#!/usr/bin/env python3
"""Place voice clips at scene marks, duck music under speech, mux an MP4.

This is the reusable version of the Factorial project's ``mix_final.py``.
Defaults preserve the settings that were measured and checked there:

* voice high-pass at 70 Hz;
* unducked music mean targeted 11 dB below voice-track mean;
* FFmpeg sidechain compression (threshold 0.02, ratio 6,
  attack 150 ms, release 850 ms) so music falls while speech is present
  and returns smoothly during logo/silence sections;
* one-pass loudnorm to -15 LUFS, -1.5 dBTP, LRA 11;
* H.264 video stream copied, AAC 192 kbit/s stereo at 48 kHz.

Example::

    python mix_voice_music.py \
        --video silent_1080p.mp4 \
        --marks marks_final.json \
        --audio-dir audio \
        --music music/background.wav \
        --output final.mp4 \
        --plan project_plan.json

FFmpeg and ffprobe must be on PATH.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac", ".aac")


def run(command: list[str]) -> None:
    print("+", " ".join(command)[:400])
    subprocess.run(command, check=True)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _plan_list(plan: dict[str, Any], keys: tuple[str, ...]) -> list[str] | None:
    for key in keys:
        value = plan.get(key)
        if isinstance(value, list) and value:
            return [str(item) for item in value]
    return None


def media_duration(path: Path) -> float:
    result = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    return float(json.loads(result)["format"]["duration"])


def mean_volume_db(path: Path) -> float:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"mean_volume:\s*(-?(?:inf|[\d.]+)) dB", result.stderr)
    if not match:
        raise SystemExit(f"volumedetect failed for {path}")
    value = match.group(1)
    if value in {"inf", "-inf"}:
        raise SystemExit(f"audio appears silent: {path}")
    return float(value)


def find_audio(audio_dir: Path, segment: str, pattern: str) -> Path:
    if "{segment}" not in pattern:
        raise SystemExit("audio pattern must contain {segment}, e.g. '{segment}.mp3'")
    preferred = audio_dir / pattern.format(segment=segment)
    if preferred.exists():
        return preferred
    for extension in AUDIO_EXTENSIONS:
        candidate = audio_dir / f"{segment}{extension}"
        if candidate.exists():
            return candidate
    return preferred


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", type=Path, required=True, help="silent rendered video")
    parser.add_argument("--marks", type=Path, required=True, help="final-render marks JSON")
    parser.add_argument("--audio-dir", type=Path, required=True, help="folder with one clip per segment")
    parser.add_argument("--music", type=Path, required=True, help="background music WAV/MP3")
    parser.add_argument("--output", type=Path, required=True, help="final MP4")
    parser.add_argument("--plan", type=Path, help="project plan JSON")
    parser.add_argument("--sequence", help="comma-separated full mark order; overrides plan")
    parser.add_argument("--segments", help="comma-separated voice segment IDs; overrides plan")
    parser.add_argument("--pattern", help="clip name pattern, default: plan or {segment}.mp3")
    parser.add_argument("--voice-track", type=Path, help="intermediate WAV (default beside output)")
    parser.add_argument("--sync-plan", type=Path, help="sync report JSON (default beside output)")
    parser.add_argument("--music-below-voice-db", type=float, default=None,
                        help="unducked music mean below voice mean (default: plan or 11)")
    parser.add_argument("--music-gain-db", type=float, default=None,
                        help="manual gain in dB instead of automatic mean matching")
    parser.add_argument("--duck-threshold", type=float, default=0.02)
    parser.add_argument("--duck-ratio", type=float, default=6.0)
    parser.add_argument("--duck-attack", type=float, default=150.0, help="milliseconds")
    parser.add_argument("--duck-release", type=float, default=850.0, help="milliseconds")
    parser.add_argument("--loudness", type=float, default=-15.0, help="integrated LUFS target")
    parser.add_argument("--true-peak", type=float, default=-1.5)
    parser.add_argument("--lra", type=float, default=11.0)
    parser.add_argument("--no-loudnorm", action="store_true")
    parser.add_argument("--audio-bitrate", default="192k")
    parser.add_argument("--loop-music", action="store_true", help="loop a short music file")
    parser.add_argument("--remove-voice-track", action="store_true")
    parser.add_argument("--overlap-tolerance", type=float, default=0.05)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    for label, path in [
        ("video", args.video),
        ("marks", args.marks),
        ("music", args.music),
    ]:
        if not path.is_file():
            raise SystemExit(f"{label} file not found: {path}")
    if not args.audio_dir.is_dir():
        raise SystemExit(f"audio folder not found: {args.audio_dir}")
    if args.output.resolve() == args.video.resolve():
        raise SystemExit("output must not overwrite the input video")

    plan: dict[str, Any] = {}
    if args.plan:
        if not args.plan.is_file():
            raise SystemExit(f"plan file not found: {args.plan}")
        loaded = _load_json(args.plan)
        if not isinstance(loaded, dict):
            raise SystemExit("project plan must be a JSON object")
        plan = loaded

    loaded_marks = _load_json(args.marks)
    if not isinstance(loaded_marks, dict) or not loaded_marks:
        raise SystemExit("marks file must be a non-empty JSON object")
    marks = {str(key): float(value) for key, value in loaded_marks.items()}

    sequence = _csv(args.sequence) or _plan_list(plan, ("order", "sequence"))
    if not sequence:
        indexed = list(enumerate(marks.items()))
        sequence = [key for _, (key, _) in sorted(indexed, key=lambda pair: (pair[1][1], pair[0]))]
    missing = [key for key in sequence if key not in marks]
    if missing:
        raise SystemExit(f"marks missing sequence entries: {missing}")

    pattern = args.pattern or str(plan.get("audio_pattern") or "{segment}.mp3")
    segments = _csv(args.segments) or _plan_list(plan, ("voice_segments", "voice", "segments"))
    if not segments:
        segments = [key for key in sequence if find_audio(args.audio_dir, key, pattern).exists()]
    if not segments:
        raise SystemExit("no voice segments supplied or discovered")

    output_parent = args.output.parent if str(args.output.parent) else Path(".")
    output_parent.mkdir(parents=True, exist_ok=True)
    voice_track = args.voice_track or (output_parent / "voice_track.wav")
    voice_track.parent.mkdir(parents=True, exist_ok=True)
    sync_plan_path = args.sync_plan or (output_parent / "sync_plan.json")
    sync_plan_path.parent.mkdir(parents=True, exist_ok=True)

    video_duration = media_duration(args.video)
    clips: dict[str, Path] = {}
    durations: dict[str, float] = {}
    for segment in segments:
        clip = find_audio(args.audio_dir, segment, pattern)
        if not clip.exists():
            raise SystemExit(f"voice clip not found: {clip}")
        clips[segment] = clip
        durations[segment] = media_duration(clip)

    # Sync sanity check before doing any expensive audio work.
    report: list[dict[str, float | str]] = []
    print(f"{'seg':9s} {'start':>8s} {'end':>8s} {'next':>8s} {'gap':>6s}")
    for segment in segments:
        if segment not in marks:
            raise SystemExit(f"voice segment has no mark: {segment}")
        start = marks[segment]
        end = start + durations[segment]
        if segment in sequence and sequence.index(segment) + 1 < len(sequence):
            next_start = marks[sequence[sequence.index(segment) + 1]]
            next_name = sequence[sequence.index(segment) + 1]
        else:
            next_start = video_duration
            next_name = "VIDEO_END"
        gap = next_start - end
        report.append(
            {
                "seg": segment,
                "voice_start_s": round(start, 3),
                "voice_end_s": round(end, 3),
                "next_segment": next_name,
                "next_segment_start_s": round(next_start, 3),
                "gap_s": round(gap, 3),
            }
        )
        print(f"{segment:9s} {start:8.2f} {end:8.2f} {next_start:8.2f} {gap:6.2f}")
        if end > next_start + args.overlap_tolerance:
            raise SystemExit(
                f"OVERLAP: {segment} ends at {end:.2f}s, after next segment at {next_start:.2f}s"
            )
    sync_plan_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # 1) Build one voice track by delaying every clip to its scene mark.
    voice_cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for segment in segments:
        voice_cmd += ["-i", str(clips[segment])]
    filters: list[str] = []
    labels: list[str] = []
    for index, segment in enumerate(segments):
        delay_ms = int(round(marks[segment] * 1000))
        filters.append(
            f"[{index}:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"highpass=f=70,adelay={delay_ms}|{delay_ms}[v{index}]"
        )
        labels.append(f"[v{index}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(segments)}:duration=longest:dropout_transition=0:normalize=0[mix]"
    )
    filters.append(f"[mix]apad=whole_dur={video_duration:.3f},atrim=0:{video_duration:.3f}[vout]")
    voice_cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
        "-c:a",
        "pcm_s16le",
        str(voice_track),
    ]
    run(voice_cmd)

    # 2) Match the unducked music level to the measured voice track.
    voice_mean = mean_volume_db(voice_track)
    music_mean = mean_volume_db(args.music)
    if args.music_gain_db is not None:
        gain = 10.0 ** (args.music_gain_db / 20.0)
        gain_description = f"manual {args.music_gain_db:+.1f} dB"
    else:
        below_raw = plan.get("music_below_voice_db", 11.0)
        below = float(args.music_below_voice_db if args.music_below_voice_db is not None else below_raw)
        gain_db = (voice_mean - below) - music_mean
        gain = min(1.0, max(0.05, 10.0 ** (gain_db / 20.0)))
        gain_description = f"music mean targeted {below:g} dB below voice mean"
    print(
        f"voice mean {voice_mean:.1f} dB | music mean {music_mean:.1f} dB | "
        f"music gain {gain:.4f} ({20 * math.log10(gain):+.1f} dB; {gain_description})"
    )

    # 3) Duck, mix and mux.  The video stream is copied without re-encoding.
    loudnorm = (
        ""
        if args.no_loudnorm
        else f"loudnorm=I={args.loudness:g}:TP={args.true_peak:g}:LRA={args.lra:g},"
    )
    filter_complex = (
        "[1:a]asplit=2[vm][vsc];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain:.4f}[mus];"
        "[mus][vsc]sidechaincompress="
        f"threshold={args.duck_threshold:g}:ratio={args.duck_ratio:g}:"
        f"attack={args.duck_attack:g}:release={args.duck_release:g}:makeup=1[duck];"
        "[vm][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        f"{loudnorm}aresample=48000[aout]"
    )

    final_cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(args.video), "-i", str(voice_track)]
    if args.loop_music:
        final_cmd += ["-stream_loop", "-1"]
    final_cmd += [
        "-i",
        str(args.music),
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        args.audio_bitrate,
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        "-t",
        f"{video_duration:.3f}",
        str(args.output),
    ]
    run(final_cmd)

    if args.remove_voice_track:
        voice_track.unlink(missing_ok=True)
    print("WROTE", args.output)
    print("SYNC PLAN", sync_plan_path)
    print("VOICE TRACK", voice_track if not args.remove_voice_track else "(removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
