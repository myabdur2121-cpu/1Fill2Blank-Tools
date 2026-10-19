#!/usr/bin/env python3
"""Compute per-segment holds ("pads") from a no-pad timing render.

Inputs are:
* ``marks.json`` from pass 1 (Manim scene times, no pads applied);
* one voice clip per voice segment, e.g. ``S01.mp3``;
* a project plan saying which marks occur in which order.

For every voice segment::

    pad = max(0, voice_duration + safety_gap - animation_duration)

With ``--voice-units`` the calculation becomes handle-aware (the
own-voice production mode): the desired gap is measured between actual
speech, so the current clip's tail handle and the next clip's lead
handle are subtracted::

    required = duration - tail_handle + desired_speech_gap - next_lead
    pad = max(0, required - animation_duration)

The second render inserts that many extra seconds while the finished
visual for the segment stays on screen, so speech finishes before the
next visual segment begins.

Example (Factorial project)::

    python compute_pads.py marks_pass1.json audio/ pad.json \
        --plan project_plan.json --durations-out voice_durations.json

FFmpeg's ``ffprobe`` must be on PATH.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac", ".aac")


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
    # project_config.json keeps these under an "audio" object.
    audio = plan.get("audio")
    if isinstance(audio, dict):
        for key in keys:
            value = audio.get(key)
            if isinstance(value, list) and value:
                return [str(item) for item in value]
    return None


def _plan_pattern(plan: dict[str, Any]) -> str | None:
    value = plan.get("audio_pattern")
    if value:
        return str(value)
    audio = plan.get("audio")
    if isinstance(audio, dict) and audio.get("audio_pattern"):
        return str(audio["audio_pattern"])
    return None


def _load_voice_units(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    if not path.is_file():
        raise SystemExit(f"voice units file not found: {path}")
    data = _load_json(path)
    units = data.get("units") if isinstance(data, dict) else None
    if not isinstance(units, list) or not units:
        raise SystemExit("voice units file must contain a non-empty 'units' list")
    result: dict[str, dict[str, Any]] = {}
    for unit in units:
        if not isinstance(unit, dict) or not unit.get("id"):
            raise SystemExit("every voice unit needs an id")
        result[str(unit["id"])] = unit
    return result


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
    parser.add_argument("marks", type=Path, help="pass-1 marks JSON")
    parser.add_argument("audio_dir", type=Path, help="folder containing voice clips")
    parser.add_argument("output", type=Path, help="pad JSON to write")
    parser.add_argument("--plan", type=Path, help="project plan JSON (order/voice_segments/gap)")
    parser.add_argument("--order", help="comma-separated mark order; overrides plan")
    parser.add_argument("--voice", help="comma-separated voice segment IDs; overrides plan")
    parser.add_argument("--gap", type=float, default=None, help="safety gap seconds (default: plan or 0.45)")
    parser.add_argument("--pattern", help="clip name pattern, default: plan or {segment}.mp3")
    parser.add_argument("--durations-out", type=Path, help="voice durations JSON (default beside output)")
    parser.add_argument("--voice-units", type=Path,
                        help="voice_units.json: enables handle-aware mode using per-unit "
                             "duration_s / lead_handle_s / tail_handle_s / gap_after_speech_s")
    parser.add_argument("--report", type=Path, help="detailed pad report JSON (handle-aware mode)")
    parser.add_argument("--nonvoice-gap", type=float, default=0.65,
                        help="desired beat before a non-voice mark such as LOGO_MID/OUTRO "
                             "in handle-aware mode (default: 0.65)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.marks.is_file():
        raise SystemExit(f"marks file not found: {args.marks}")
    if not args.audio_dir.is_dir():
        raise SystemExit(f"audio folder not found: {args.audio_dir}")

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
    all_starts = {str(key): float(value) for key, value in loaded_marks.items()}

    order = _csv(args.order) or _plan_list(plan, ("order", "sequence"))
    if not order:
        # Fall back to time order, preserving JSON order for identical times.
        indexed = list(enumerate(all_starts.items()))
        order = [key for _, (key, _) in sorted(indexed, key=lambda pair: (pair[1][1], pair[0]))]

    missing_marks = [key for key in order if key not in all_starts]
    if missing_marks:
        raise SystemExit(f"MISSING MARKS: {missing_marks} (got {list(all_starts)})")
    starts = {key: all_starts[key] for key in order}
    if any(starts[order[i + 1]] < starts[order[i]] - 1e-6 for i in range(len(order) - 1)):
        raise SystemExit(f"MARKS NOT MONOTONIC: {starts}")

    pattern = args.pattern or _plan_pattern(plan) or "{segment}.mp3"
    unit_map = _load_voice_units(args.voice_units)
    voice = _csv(args.voice) or _plan_list(plan, ("voice_segments", "voice", "segments"))
    if not voice and unit_map:
        voice = [key for key in order if key in unit_map]
    if not voice:
        voice = [key for key in order if find_audio(args.audio_dir, key, pattern).exists()]
    if not voice:
        raise SystemExit("no voice segments supplied or discovered")

    last_voice = voice[-1]
    if order.index(last_voice) >= len(order) - 1:
        raise SystemExit(
            f"voice segment {last_voice} needs a following mark (for example OUTRO or END) "
            "so its available animation time can be measured"
        )

    gap_value = plan.get("gap_seconds", plan.get("gap", 0.45))
    gap = float(args.gap if args.gap is not None else gap_value)
    if gap < 0:
        raise SystemExit("gap cannot be negative")

    voice_durations: dict[str, float] = {}
    for segment in voice:
        if unit_map:
            unit = unit_map.get(segment)
            if unit is None:
                raise SystemExit(f"voice segment {segment} is missing from voice units file")
            if unit.get("duration_s") is None:
                raise SystemExit(f"voice unit {segment} has no duration_s")
            voice_durations[segment] = float(unit["duration_s"])
            continue
        clip = find_audio(args.audio_dir, segment, pattern)
        if not clip.exists():
            raise SystemExit(f"MISSING AUDIO {clip}")
        voice_durations[segment] = media_duration(clip)

    pads: dict[str, float] = {}
    report: list[dict[str, Any]] = []
    if unit_map:
        print(f"{'seg':9s} {'start':>8s} {'anim_len':>9s} {'voice':>7s} {'need':>7s} {'pad':>7s} {'gap*':>7s}")
    else:
        print(f"{'seg':9s} {'start':>8s} {'anim_len':>9s} {'voice':>7s} {'pad':>7s}")
    for index, key in enumerate(order[:-1]):
        next_key = order[index + 1]
        animation_len = starts[next_key] - starts[key]
        voice_len = voice_durations.get(key, 0.0)
        if unit_map and key in unit_map:
            unit = unit_map[key]
            tail = float(unit.get("tail_handle_s") or 0.0)
            if next_key in unit_map:
                raw_gap = unit.get("gap_after_speech_s")
                desired = float(raw_gap) if raw_gap is not None else gap
                next_lead = float(unit_map[next_key].get("lead_handle_s") or 0.0)
            else:
                desired = float(args.nonvoice_gap)
                next_lead = 0.0
            required = voice_len - tail + desired - next_lead
            pad = max(0.0, required - animation_len)
            pads[key] = round(pad, 3)
            predicted_gap = (animation_len + pad) - voice_len + tail + next_lead
            report.append({
                "unit": key,
                "next": next_key,
                "natural_s": round(animation_len, 3),
                "voice_duration_s": voice_len,
                "required_interval_s": round(required, 3),
                "pad_s": round(pad, 3),
                "desired_speech_gap_s": desired,
                "predicted_speech_gap_s": round(predicted_gap, 3),
                "text": unit.get("text_bn_corrected") or unit.get("text") or "",
            })
            print(
                f"{key:9s} {starts[key]:8.2f} {animation_len:9.2f} {voice_len:7.2f} "
                f"{required:7.2f} {pad:7.2f} {predicted_gap:7.2f}"
            )
            continue
        pad = max(0.0, voice_len + gap - animation_len) if key in voice_durations else 0.0
        if key in voice_durations:
            pads[key] = round(pad, 3)
        if unit_map:
            report.append({"unit": key, "next": next_key, "natural_s": round(animation_len, 3), "pad_s": round(pad, 3)})
            print(f"{key:9s} {starts[key]:8.2f} {animation_len:9.2f} {voice_len:7.2f} {'--':>7s} {pad:7.2f} {'--':>7s}")
        else:
            print(f"{key:9s} {starts[key]:8.2f} {animation_len:9.2f} {voice_len:7.2f} {pad:7.2f}")

    timeline_end = starts[order[-1]]
    print(f"{order[-1]:9s} {timeline_end:8.2f}")
    print(
        f"voice total: {sum(voice_durations.values()):.2f}s   "
        f"pads total: {sum(pads.values()):.2f}s   "
        f"expected final: {timeline_end + sum(pads.values()):.2f}s"
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pads, indent=2), encoding="utf-8")
    durations_out = args.durations_out or (args.output.parent / "voice_durations.json")
    durations_out.parent.mkdir(parents=True, exist_ok=True)
    durations_out.write_text(json.dumps(voice_durations, indent=2), encoding="utf-8")
    print("WROTE", args.output)
    print("WROTE", durations_out)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("WROTE", args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
