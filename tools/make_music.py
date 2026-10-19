#!/usr/bin/env python3
"""Generate original, contemplative educational background music.

The Factorial video used this same musical system: a slow piano-like
arpeggio, a soft pad, a quiet bass and a sparse melody, all synthesised
note by note with NumPy.  It copies the *style* of calm maths-explainer
music, not any existing recording or melody.

Examples
--------
Background, exactly 221.633 seconds:
    python make_music.py 221.633 background.wav

Short intro / outro assets:
    python make_music.py 8  intro.wav  --preset intro
    python make_music.py 12 outro.wav  --preset outro

Individual stems (run once for each kind; keep the mixer balance):
    python make_music.py 60 piano.wav --only piano --peak 0
    python make_music.py 60 pad.wav   --only pad   --peak 0
    python make_music.py 60 bass.wav  --only bass  --peak 0

Only Python + NumPy are needed.  Use FFmpeg afterwards if MP3 is wanted:
    ffmpeg -i background.wav -codec:a libmp3lame -b:a 256k background.mp3
"""

from __future__ import annotations

import argparse
import math
import random
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SR = 44_100


@dataclass(frozen=True)
class Preset:
    fade_in_s: float
    fade_out_s: float
    arpeggio_start_s: float
    arpeggio_tail_guard_s: float
    melody_start_bar: int
    melody_tail_guard_s: float


PRESETS: dict[str, Preset] = {
    # Defaults preserve the behaviour used for the Factorial video.
    "background": Preset(2.5, 5.0, 1.0, 3.0, 2, 8.0),
    "intro": Preset(0.7, 1.4, 0.15, 1.0, 1, 1.0),
    "outro": Preset(0.4, 4.0, 0.10, 2.5, 0, 5.0),
}

# (bass MIDI note, chord tones from low to high)
PROGRESSION = [
    (45, [57, 59, 60, 64, 69]),  # Am(add9)
    (41, [53, 57, 60, 64, 69]),  # Fmaj7
    (36, [55, 59, 60, 64, 67]),  # Cmaj7
    (43, [55, 59, 62, 64, 67]),  # G6
    (45, [57, 59, 60, 64, 69]),  # Am(add9)
    (41, [53, 57, 60, 65, 69]),  # Fmaj9-ish
    (40, [52, 55, 59, 62, 64]),  # Em7
    (43, [55, 59, 62, 67, 71]),  # G
]
MELODY_POOL = [69, 72, 76, 74, 72, 69, 67, 64, 67, 72, 71, 69, 67, 64, 62, 64]


def midi_freq(midi: float) -> float:
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


def add_tone(
    buf: np.ndarray,
    start_s: float,
    midi: float,
    duration_s: float,
    velocity: float,
    *,
    pan: float = 0.0,
    kind: str = "piano",
    only: str = "all",
) -> None:
    """Add one synthesised note to a stereo (2, samples) float buffer."""
    if only != "all" and kind != only:
        return

    start = int(start_s * SR)
    count = int(duration_s * SR)
    if start >= buf.shape[1] or count <= 0:
        return
    count = min(count, buf.shape[1] - start)
    if count <= 0:
        return

    t = np.arange(count, dtype=np.float32) / SR
    freq = midi_freq(midi)

    if kind == "piano":
        signal = np.zeros(count, dtype=np.float32)
        # A fundamental plus progressively quieter/faster-decaying harmonics
        # gives a simple piano-string character instead of a pure sine beep.
        for harmonic, amp in enumerate([1.0, 0.48, 0.23, 0.11, 0.05, 0.02], start=1):
            signal += (
                amp
                * np.sin(2 * np.pi * freq * harmonic * t, dtype=np.float32)
                * np.exp(-t * (1.6 + 0.8 * harmonic))
            )
        signal *= (1.0 - np.exp(-t * 250.0)) * velocity
    elif kind == "pad":
        envelope = np.minimum(
            1.0,
            np.minimum(t / 1.2, np.maximum(0.0, (duration_s - t) / 1.2)),
        )
        tremolo = 0.92 + 0.08 * np.sin(2 * np.pi * 0.07 * t + midi)
        signal = (
            np.sin(2 * np.pi * freq * t)
            + 0.30 * np.sin(2 * np.pi * freq * 2 * t)
        ) * envelope * tremolo * velocity
    elif kind == "bass":
        envelope = np.minimum(
            1.0,
            np.minimum(t / 0.08, np.maximum(0.0, (duration_s - t) / 0.4)),
        )
        signal = (
            np.sin(2 * np.pi * freq * t)
            + 0.18 * np.sin(2 * np.pi * freq * 2 * t)
        ) * envelope * np.exp(-t * 0.25) * velocity
    else:  # pragma: no cover - protected by argparse choices
        raise ValueError(f"unknown tone kind: {kind}")

    left = math.cos((pan + 1.0) * math.pi / 4.0)
    right = math.sin((pan + 1.0) * math.pi / 4.0)
    buf[0, start : start + count] += signal * left
    buf[1, start : start + count] += signal * right


def _apply_fade(buf: np.ndarray, seconds: float, *, fade_in: bool) -> None:
    if seconds <= 0:
        return
    count = min(buf.shape[1], int(round(seconds * SR)))
    if count <= 1:
        return
    if fade_in:
        buf[:, :count] *= np.linspace(0.0, 1.0, count, dtype=np.float32)
    else:
        buf[:, -count:] *= np.linspace(1.0, 0.0, count, dtype=np.float32) ** 1.5


def render(
    duration_s: float,
    *,
    preset_name: str = "background",
    bpm: float = 72.0,
    seed: int = 7,
    only: str = "all",
    target_peak: float = 0.62,
    fade_in_s: float | None = None,
    fade_out_s: float | None = None,
) -> tuple[np.ndarray, float]:
    if duration_s <= 0:
        raise ValueError("duration must be positive")
    if bpm <= 0:
        raise ValueError("bpm must be positive")
    if not 0.0 <= target_peak <= 1.0:
        raise ValueError("peak must be between 0 and 1; use 0 to disable normalising")

    preset = PRESETS[preset_name]
    rng = random.Random(seed)
    total = int(round(duration_s * SR))
    buf = np.zeros((2, total), dtype=np.float32)

    beat = 60.0 / bpm
    bar = 4.0 * beat
    bar_count = int(math.ceil(duration_s / bar))
    melody_index = 0

    for bar_index in range(bar_count):
        bar_start = bar_index * bar

        if preset_name == "intro":
            bass, tones = PROGRESSION[bar_index % 4]
        elif preset_name == "outro" and bar_index == bar_count - 1:
            bass, tones = PROGRESSION[2]  # resolve on Cmaj7 in the final bar
        else:
            bass, tones = PROGRESSION[bar_index % len(PROGRESSION)]

        add_tone(buf, bar_start, bass, bar * 1.05, 0.16, kind="bass", only=only)
        for j, midi in enumerate(tones[:4]):
            add_tone(
                buf,
                bar_start,
                midi,
                bar * 1.05,
                0.038,
                pan=-0.25 + 0.16 * j,
                kind="pad",
                only=only,
            )

        # Gentle eighth-note arpeggio with small human timing/velocity changes.
        for step in range(8):
            when = bar_start + step * (beat / 2.0) + rng.uniform(-0.02, 0.02)
            if when < preset.arpeggio_start_s:
                continue
            if when > duration_s - preset.arpeggio_tail_guard_s:
                continue
            midi = tones[(step * 2 + bar_index) % len(tones)]
            add_tone(
                buf,
                when,
                midi + 12,
                2.4,
                0.055 * rng.uniform(0.8, 1.15),
                pan=rng.uniform(-0.3, 0.3),
                kind="piano",
                only=only,
            )

        # Sparse melody, approximately every second bar.
        if (
            bar_index >= preset.melody_start_bar
            and bar_index % 2 == 0
            and bar_start < duration_s - preset.melody_tail_guard_s
        ):
            for melody_beat in (0, 2):
                midi = MELODY_POOL[melody_index % len(MELODY_POOL)]
                melody_index += 1
                add_tone(
                    buf,
                    bar_start + melody_beat * beat + rng.uniform(0.0, 0.05),
                    midi + 12,
                    3.2,
                    0.075,
                    pan=rng.uniform(-0.15, 0.15),
                    kind="piano",
                    only=only,
                )

    # Small-room impression from a few progressively quieter echoes.
    wet = buf.copy()
    for delay_s, gain in [(0.11, 0.22), (0.23, 0.14), (0.39, 0.08), (0.57, 0.05)]:
        delay = int(delay_s * SR)
        if 0 < delay < buf.shape[1]:
            wet[:, delay:] += buf[:, :-delay] * gain
    buf = wet

    _apply_fade(buf, preset.fade_in_s if fade_in_s is None else fade_in_s, fade_in=True)
    _apply_fade(buf, preset.fade_out_s if fade_out_s is None else fade_out_s, fade_in=False)

    peak_in = float(np.max(np.abs(buf))) if buf.size else 0.0
    if target_peak > 0 and peak_in > 0:
        buf *= target_peak / peak_in
    return buf, peak_in


def write_wav(path: Path, buf: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(buf, -1.0, 1.0) * 32767).astype(np.int16).T
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("duration", type=float, help="length in seconds, e.g. 221.633")
    parser.add_argument("output", type=Path, help="output WAV path")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="background")
    parser.add_argument("--bpm", type=float, default=72.0)
    parser.add_argument("--seed", type=int, default=7, help="same seed = same humanisation")
    parser.add_argument("--peak", type=float, default=0.62, help="target peak 0..1; 0 disables normalising")
    parser.add_argument("--fade-in", type=float, default=None, help="override preset fade-in seconds")
    parser.add_argument("--fade-out", type=float, default=None, help="override preset fade-out seconds")
    parser.add_argument("--only", choices=["all", "piano", "pad", "bass"], default="all", help="render one stem")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    buffer, peak_in = render(
        args.duration,
        preset_name=args.preset,
        bpm=args.bpm,
        seed=args.seed,
        only=args.only,
        target_peak=args.peak,
        fade_in_s=args.fade_in,
        fade_out_s=args.fade_out,
    )
    write_wav(args.output, buffer)
    print(
        f"WROTE {args.output}  {args.duration:.3f}s  preset={args.preset}  "
        f"only={args.only}  peak_before_normalise={peak_in:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
