#!/usr/bin/env python3
"""Transcribe voice clips one by one (generic, low-RAM friendly).

Each file is transcribed independently so clips can be audited, mapped to
script lines and checked for duplicate takes. Audio is decoded with the
system FFmpeg to 16 kHz mono float32 and passed to faster-whisper as an
array (this avoids PyAV version mismatches).

Low-RAM note: in ~2 GB sandboxes use the default ``small`` model on CPU
int8; ``medium`` is known to be OOM-killed there.

Examples:
    python transcribe_clips.py voice_folder --output transcripts.json
    python transcribe_clips.py a.wav b.m4a --language bn --output out.json
    python transcribe_clips.py voice_folder --dry-run

Requires: ffmpeg on PATH; Python packages numpy + faster-whisper
(imported lazily, so ``--help`` and ``--dry-run`` work without them).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".aif", ".aiff")


def natural_key(path: Path) -> tuple:
    parts = re.split(r"(\d+)", path.name)
    key = []
    for part in parts:
        key.append((1, int(part), "") if part.isdigit() else (0, 0, part.lower()))
    return tuple(key)


def collect(inputs: list[Path], recursive: bool) -> list[Path]:
    found: dict[Path, None] = {}
    for item in inputs:
        item = item.expanduser()
        if item.is_file():
            found[item.resolve()] = None
        elif item.is_dir():
            iterator = item.rglob("*") if recursive else item.glob("*")
            for path in iterator:
                if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                    found[path.resolve()] = None
        else:
            raise SystemExit(f"input not found: {item}")
    return sorted(found, key=natural_key)


def decode_16k_mono(path: Path):
    import numpy as np  # lazy: --help/--dry-run must work without numpy

    cmd = [
        "ffmpeg", "-v", "error", "-nostdin", "-i", str(path),
        "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "1", "-ar", "16000", "-",
    ]
    raw = subprocess.check_output(cmd)
    return np.frombuffer(raw, dtype=np.float32).copy()


def trim_for_asr(audio, sr: int = 16000, threshold_db: float = -45.0, handle_s: float = 0.25):
    """Remove start/stop silence before ASR, keeping a small handle."""
    import numpy as np

    frame = int(0.02 * sr)
    if len(audio) <= frame:
        return audio, 0.0, len(audio) / sr
    rms = np.array([
        np.sqrt(np.mean(audio[i:i + frame] ** 2) + 1e-12)
        for i in range(0, len(audio) - frame + 1, frame)
    ])
    db = 20 * np.log10(rms + 1e-12)
    idx = np.where(db > threshold_db)[0]
    if len(idx) == 0:
        return audio, 0.0, len(audio) / sr
    start = max(0, int(idx[0] * frame - handle_s * sr))
    end = min(len(audio), int((idx[-1] + 1) * frame + handle_s * sr))
    return audio[start:end], start / sr, end / sr


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", type=Path, help="audio files and/or folders")
    parser.add_argument("--output", type=Path, help="transcripts JSON (required unless --dry-run)")
    parser.add_argument("--model", default="small", help="faster-whisper model (default: small)")
    parser.add_argument("--model-dir", type=Path, help="model download/cache folder (optional)")
    parser.add_argument("--language", default="bn",
                        help="ISO code forced for ASR, or 'auto' to detect (default: bn)")
    parser.add_argument("--initial-prompt", default=None,
                        help="optional vocabulary prompt; default none (the skill's audited default)")
    parser.add_argument("--beam", type=int, default=5)
    parser.add_argument("--word-timestamps", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--cpu-threads", type=int, default=2)
    parser.add_argument("--no-trim", action="store_true", help="do not trim silence before ASR")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dry-run", action="store_true", help="list files that would be transcribed, then stop")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    files = collect(args.inputs, args.recursive)
    if not files:
        raise SystemExit("no audio files found")
    if args.dry_run:
        for path in files:
            print(path)
        print(f"DRY RUN: {len(files)} file(s); model={args.model} language={args.language}")
        return 0
    if args.output is None:
        raise SystemExit("--output is required (or use --dry-run)")

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("faster-whisper is not installed in this environment") from exc

    language = None if str(args.language).lower() in {"auto", "", "none"} else args.language
    started = time.time()
    print(f"Loading faster-whisper model={args.model!r} ({args.device} {args.compute_type})...", flush=True)
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        cpu_threads=args.cpu_threads,
        num_workers=1,
        download_root=str(args.model_dir) if args.model_dir else None,
    )
    print(f"Model ready in {time.time() - started:.1f}s; files={len(files)}", flush=True)

    results: list[dict[str, Any]] = []
    for index, path in enumerate(files, 1):
        t0 = time.time()
        audio = decode_16k_mono(path)
        if args.no_trim:
            trim_start, trim_end = 0.0, len(audio) / 16000
        else:
            audio, trim_start, trim_end = trim_for_asr(audio)
        segments, info = model.transcribe(
            audio,
            language=language,
            task="transcribe",
            beam_size=args.beam,
            best_of=5,
            patience=1.0,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.45,
            condition_on_previous_text=False,
            initial_prompt=args.initial_prompt,
            vad_filter=False,
            word_timestamps=args.word_timestamps,
            repetition_penalty=1.08,
            no_repeat_ngram_size=3,
        )
        segment_list = []
        for seg in segments:
            segment_list.append({
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": seg.text.strip(),
                "avg_logprob": round(float(seg.avg_logprob), 4),
                "no_speech_prob": round(float(seg.no_speech_prob), 4),
                "words": [
                    {
                        "start": round(float(w.start), 3),
                        "end": round(float(w.end), 3),
                        "word": w.word,
                        "probability": round(float(w.probability), 4),
                    }
                    for w in (seg.words or [])
                ],
            })
        text = " ".join(s["text"] for s in segment_list).strip()
        results.append({
            "index": index,
            "file": str(path),
            "name": path.name,
            "duration_asr": round(float(info.duration), 3),
            "trim_start_s": round(float(trim_start), 3),
            "trim_end_s": round(float(trim_end), 3),
            "language": info.language,
            "language_probability": round(float(info.language_probability), 4),
            "text": text,
            "segments": segment_list,
            "elapsed_s": round(time.time() - t0, 2),
        })
        print(f"[{index:02d}/{len(files)}] {path.name} :: {text}", flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"DONE {len(results)} files in {time.time() - started:.1f}s -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
