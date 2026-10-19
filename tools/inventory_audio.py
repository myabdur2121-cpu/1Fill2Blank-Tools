#!/usr/bin/env python3
"""Inventory audio clips with ffprobe.

Step 1 of the voice-to-manim skill is: trust nothing about filenames.
This tool records duration / sample-rate / channels / codec for every clip
so take-mapping decisions start from evidence.

Examples:
    python inventory_audio.py voice_folder --output inventory.json
    python inventory_audio.py clip1.wav clip2.m4a        # JSON to stdout
    python inventory_audio.py voice_folder --no-recursive --output inventory.json

Requires ffprobe on PATH.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_EXTENSIONS = (".wav", ".mp3", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".aif", ".aiff")


def natural_key(path: Path) -> tuple:
    """Sort key where embedded numbers compare numerically (2 before 10)."""
    parts = re.split(r"(\d+)", path.name)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((1, int(part), ""))
        else:
            key.append((0, 0, part.lower()))
    return tuple(key)


def collect(inputs: list[Path], extensions: tuple[str, ...], recursive: bool) -> list[Path]:
    found: dict[Path, None] = {}
    for item in inputs:
        item = item.expanduser()
        if item.is_file():
            found[item.resolve()] = None
        elif item.is_dir():
            iterator = item.rglob("*") if recursive else item.glob("*")
            for path in iterator:
                if path.is_file() and path.suffix.lower() in extensions:
                    found[path.resolve()] = None
        else:
            raise SystemExit(f"input not found: {item}")
    return sorted(found, key=natural_key)


def probe(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,codec_name,sample_rate,channels,channel_layout,bit_rate,duration",
        "-show_entries", "format=duration,size,bit_rate,format_name",
        "-of", "json", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ffprobe failed for {path}")
    data = json.loads(result.stdout)
    fmt = data.get("format", {}) or {}
    stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {}) or {}

    def as_float(value: Any) -> float | None:
        try:
            return round(float(value), 3)
        except (TypeError, ValueError):
            return None

    def as_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return {
        "path": str(path),
        "name": path.name,
        "size_bytes": as_int(fmt.get("size")) or path.stat().st_size,
        "duration_s": as_float(fmt.get("duration")) if fmt.get("duration") is not None else as_float(stream.get("duration")),
        "format": fmt.get("format_name"),
        "codec": stream.get("codec_name"),
        "sample_rate_hz": as_int(stream.get("sample_rate")),
        "channels": as_int(stream.get("channels")),
        "channel_layout": stream.get("channel_layout"),
        "bit_rate": as_int(stream.get("bit_rate")) or as_int(fmt.get("bit_rate")),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", type=Path, help="audio files and/or folders")
    parser.add_argument("--output", type=Path, help="inventory JSON to write (default: stdout)")
    parser.add_argument("--extensions", help="comma list, e.g. .wav,.m4a (default: common audio types)")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True,
                        help="search folders recursively (default: true)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    extensions = DEFAULT_EXTENSIONS
    if args.extensions:
        extensions = tuple(e.strip().lower() if e.strip().startswith(".") else "." + e.strip().lower()
                             for e in args.extensions.split(",") if e.strip())
    files = collect(args.inputs, extensions, args.recursive)
    if not files:
        raise SystemExit("no audio files found")

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in files:
        try:
            rows.append(probe(path))
        except Exception as exc:  # keep going so one bad file does not hide the rest
            errors.append({"path": str(path), "error": str(exc)})

    total = round(sum(r["duration_s"] or 0.0 for r in rows), 3)
    payload = {
        "generated_by": "1Fill2Blank-Tools inventory_audio.py",
        "count": len(rows),
        "total_duration_s": total,
        "files": rows,
        "errors": errors,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"WROTE {args.output}  files={len(rows)}  total={total:.2f}s  errors={len(errors)}")
    else:
        print(text)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
