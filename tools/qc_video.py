#!/usr/bin/env python3
"""Quality-check a finished voice-to-manim video.

Checks (each can be skipped):
* ffprobe streams/format against the project config targets,
* full decode (any decoder error fails),
* integrated loudness + true peak (FFmpeg loudnorm measurement),
* long-silence scan (default: >3 s below -45 dB),
* optional contact sheet for visual inspection,
* optional final speech-gap audit from marks + voice_units + config.

Example:
    python qc_video.py final.mp4 \
        --config project_config.json \
        --marks-final marks_final_myvoice.json \
        --voice-units voice_units.json \
        --contact-sheet contact_sheet.jpg \
        --output qc_report.json

Exit code is 0 only when every enabled gate passes.
Requires ffmpeg/ffprobe on PATH.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def load_json(path: Path | None) -> Any:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def probe(video: Path) -> dict[str, Any]:
    result = run([
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,sample_rate,channels,duration",
        "-show_entries", "format=duration,size,bit_rate,format_name",
        "-of", "json", str(video),
    ])
    if result.returncode != 0:
        raise SystemExit(f"ffprobe failed: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    fmt = data.get("format", {}) or {}
    vstream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}) or {}
    astream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {}) or {}

    def fps_of(stream: dict[str, Any]) -> float | None:
        for key in ("avg_frame_rate", "r_frame_rate"):
            value = str(stream.get(key) or "")
            if "/" in value:
                num, den = value.split("/", 1)
                try:
                    return round(float(num) / float(den), 3) if float(den) else None
                except ValueError:
                    pass
            try:
                return round(float(value), 3)
            except ValueError:
                continue
        return None

    def as_float(value: Any) -> float | None:
        try:
            return round(float(value), 3)
        except (TypeError, ValueError):
            return None

    return {
        "format": fmt.get("format_name"),
        "duration_s": as_float(fmt.get("duration")),
        "size_bytes": int(fmt["size"]) if str(fmt.get("size", "")).isdigit() else None,
        "video": {
            "codec": vstream.get("codec_name"),
            "width": vstream.get("width"),
            "height": vstream.get("height"),
            "fps": fps_of(vstream),
        },
        "audio": {
            "codec": astream.get("codec_name"),
            "sample_rate_hz": int(astream["sample_rate"]) if str(astream.get("sample_rate", "")).isdigit() else None,
            "channels": astream.get("channels"),
        },
    }


def full_decode(video: Path) -> dict[str, Any]:
    result = run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(video), "-f", "null", "-"])
    return {"ok": result.returncode == 0 and not result.stderr.strip(),
            "returncode": result.returncode, "stderr": result.stderr.strip()[:2000]}


def measure_loudness(video: Path) -> dict[str, Any]:
    result = run([
        "ffmpeg", "-nostdin", "-i", str(video), "-vn",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-",
    ])
    match = None
    for match in re.finditer(r"\{\s*\"input_i\".*?\}", result.stderr, flags=re.DOTALL):
        pass
    if not match:
        return {"ok": False, "error": "loudnorm JSON not found", "stderr_tail": result.stderr.strip()[-1000:]}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"loudnorm JSON parse failed: {exc}"}

    def num(value: Any) -> float | None:
        try:
            result_value = float(value)
            return result_value if math.isfinite(result_value) else None
        except (TypeError, ValueError):
            return None

    return {
        "ok": True,
        "integrated_lufs": num(data.get("input_i")),
        "true_peak_dbtp": num(data.get("input_tp")),
        "lra": num(data.get("input_lra")),
        "threshold_lufs": num(data.get("input_thresh")),
    }


def scan_silence(video: Path, noise_db: float, min_duration: float) -> dict[str, Any]:
    result = run([
        "ffmpeg", "-nostdin", "-i", str(video), "-vn",
        "-af", f"silencedetect=noise={noise_db:g}dB:d={min_duration:g}",
        "-f", "null", "-",
    ])
    events = []
    current: dict[str, Any] = {}
    for line in result.stderr.splitlines():
        start = re.search(r"silence_start:\s*([0-9.]+)", line)
        end = re.search(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", line)
        if start:
            current = {"start_s": round(float(start.group(1)), 3)}
        if end:
            current["end_s"] = round(float(end.group(1)), 3)
            current["duration_s"] = round(float(end.group(2)), 3)
            events.append(current)
            current = {}
    return {"noise_db": noise_db, "min_duration_s": min_duration, "events": events, "count": len(events)}


def make_contact_sheet(video: Path, output: Path, duration: float | None, frames: int) -> dict[str, Any]:
    if not duration or duration <= 0:
        return {"ok": False, "error": "unknown duration"}
    cols = max(1, math.ceil(math.sqrt(frames)))
    rows = max(1, math.ceil(frames / cols))
    fps_expr = max(frames / duration, 0.001)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = run([
        "ffmpeg", "-y", "-v", "error", "-nostdin", "-i", str(video),
        "-vf", f"fps={fps_expr:.6f},scale=320:-1,tile={cols}x{rows}:padding=4:margin=4",
        "-frames:v", "1", str(output),
    ])
    return {"ok": result.returncode == 0 and output.is_file(), "path": str(output),
            "frames_requested": frames, "stderr": result.stderr.strip()[:1000]}


def speech_gap_audit(marks: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    units = [u for u in manifest.get("units", []) if isinstance(u, dict) and u.get("id") in marks]
    rows = []
    for current, nxt in zip(units, units[1:]):
        start = float(marks[current["id"]])
        next_start = float(marks[nxt["id"]])
        duration = float(current.get("duration_s") or 0.0)
        tail = float(current.get("tail_handle_s") or 0.0)
        lead = float(nxt.get("lead_handle_s") or 0.0)
        rows.append({
            "unit": current["id"],
            "next": nxt["id"],
            "file_gap_s": round(next_start - (start + duration), 3),
            "speech_gap_s": round((next_start + lead) - (start + duration - tail), 3),
        })
    file_gaps = [r["file_gap_s"] for r in rows]
    speech_gaps = [r["speech_gap_s"] for r in rows]
    return {
        "rows": rows,
        "min_file_gap_s": min(file_gaps) if file_gaps else None,
        "min_speech_gap_s": min(speech_gaps) if speech_gaps else None,
        "negative_file_gaps": [r for r in rows if r["file_gap_s"] < 0],
        "negative_speech_gaps": [r for r in rows if r["speech_gap_s"] < 0],
        "marks_end_s": marks.get("END"),
    }


def config_values(config: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if not config:
        return {}, {}
    output = config.get("output", {}) if isinstance(config.get("output"), dict) else {}
    targets = config.get("qc_targets", {}) if isinstance(config.get("qc_targets"), dict) else {}
    return output, targets


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, help="QC report JSON")
    parser.add_argument("--config", type=Path, help="project_config.json (output spec + QC targets)")
    parser.add_argument("--marks-final", type=Path, help="final marks JSON for the speech-gap audit")
    parser.add_argument("--voice-units", type=Path, help="voice_units.json for the speech-gap audit")
    parser.add_argument("--contact-sheet", type=Path, help="write a contact-sheet JPG/PNG here")
    parser.add_argument("--frames", type=int, default=12, help="contact-sheet frame count (default 12)")
    parser.add_argument("--silence-db", type=float, default=-45.0)
    parser.add_argument("--silence-duration", type=float, default=3.0)
    parser.add_argument("--skip-decode", action="store_true")
    parser.add_argument("--skip-loudness", action="store_true")
    parser.add_argument("--skip-silence", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.video.is_file():
        raise SystemExit(f"video not found: {args.video}")
    config = load_json(args.config)
    expected_output, targets = config_values(config if isinstance(config, dict) else None)

    report: dict[str, Any] = {"video": str(args.video), "probe": probe(args.video), "checks": {}}
    failures: list[str] = []
    info = report["probe"]

    spec_ok = True
    for key, actual_key in (("width", "width"), ("height", "height"), ("fps", "fps")):
        expected = expected_output.get(key)
        if expected is not None:
            actual = info["video"].get(actual_key)
            if key == "fps":
                if actual is None or abs(float(actual) - float(expected)) > 0.05:
                    spec_ok = False
            elif int(actual or 0) != int(expected):
                spec_ok = False
    report["checks"]["spec"] = {"ok": spec_ok, "expected": expected_output}
    if expected_output and not spec_ok:
        failures.append("spec")

    if not args.skip_decode:
        report["checks"]["decode"] = full_decode(args.video)
        if not report["checks"]["decode"]["ok"]:
            failures.append("decode")

    if not args.skip_loudness:
        loudness = measure_loudness(args.video)
        report["checks"]["loudness"] = loudness
        if not loudness.get("ok"):
            failures.append("loudness-measure")
        else:
            loud_range = targets.get("loudness_lufs_range")
            if loud_range and loudness.get("integrated_lufs") is not None:
                low, high = float(loud_range[0]), float(loud_range[1])
                if not (low <= loudness["integrated_lufs"] <= high):
                    failures.append("loudness-range")
            peak_max = targets.get("true_peak_max_dbtp")
            if peak_max is not None and loudness.get("true_peak_dbtp") is not None:
                if loudness["true_peak_dbtp"] > float(peak_max):
                    failures.append("true-peak")

    if not args.skip_silence:
        silence = scan_silence(args.video, args.silence_db, args.silence_duration)
        report["checks"]["silence"] = silence
        if silence["count"]:
            failures.append("long-silence")

    if args.contact_sheet:
        sheet = make_contact_sheet(args.video, args.contact_sheet, info.get("duration_s"), args.frames)
        report["checks"]["contact_sheet"] = sheet
        if not sheet["ok"]:
            failures.append("contact-sheet")

    if args.marks_final or args.voice_units:
        if not (args.marks_final and args.voice_units):
            failures.append("gap-audit-inputs")
            report["checks"]["speech_gaps"] = {"ok": False, "error": "--marks-final and --voice-units must be given together"}
        else:
            audit = speech_gap_audit(load_json(args.marks_final), load_json(args.voice_units))
            audit["ok"] = not audit["negative_speech_gaps"]
            report["checks"]["speech_gaps"] = audit
            if not audit["ok"]:
                failures.append("speech-gap")

    report["status"] = "PASS" if not failures else "FAIL"
    report["failures"] = failures
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("WROTE", args.output)
    loud = report["checks"].get("loudness", {})
    print(
        f"QC {report['status']}  duration={info.get('duration_s')}s  "
        f"video={info['video'].get('width')}x{info['video'].get('height')}@{info['video'].get('fps')}  "
        f"LUFS={loud.get('integrated_lufs')}  TP={loud.get('true_peak_dbtp')}  failures={failures}"
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
