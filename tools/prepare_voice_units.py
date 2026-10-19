#!/usr/bin/env python3
"""Prepare cleaned voice micro-units from explicit editorial decisions.

The editorial work (which take, where to split, what gap) belongs in a
decisions JSON — never inside this tool. The tool only executes it:

* sustained-speech detection (ignores isolated recorder clicks),
* small lead/tail handles so onsets are not clipped,
* light cleanup (high-pass + micro fades; optional gentle denoise),
* one ``Mxx.wav`` per unit + a portable ``voice_units.json`` manifest.

Decisions JSON shape (see ``templates/voice_unit_decisions.example.json``)::

    {
      "purpose": "...",
      "source_root": "path/to/voice/folder",
      "defaults": {"lead_handle_s": 0.08, "tail_handle_s": 0.10,
                   "sample_rate_hz": 48000, "cleanup": "standard"},
      "excluded_alternate_takes": [{"file": "...", "reason": "..."}],
      "units": [
        {"id": "M01", "source": "enhanced/clip_1.wav",
         "text_bn_corrected": "...", "visual": "...",
         "gap_after_speech_s": 0.45},
        {"id": "M05", "source": "enhanced/clip_4.wav",
         "trim_start_s": 14.63, "gap_after_speech_s": 0.35, ...}
      ]
    }

A finished ``voice_units.json`` (same field names) can also be used as the
decisions file to re-render the clips; ``speech_start_s``/``speech_end_s``
are honoured when present, and a missing absolute ``source`` path is
resolved through ``source_name`` under ``--source-root``.

Requires ffmpeg/ffprobe on PATH and numpy. Designed for short clips
(speech detection decodes the searched window).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".aif", ".aiff")


def natural_key(path: Path) -> tuple:
    parts = re.split(r"(\d+)", path.name)
    return tuple((1, int(p), "") if p.isdigit() else (0, 0, p.lower()) for p in parts)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        text=True,
    )
    return float(json.loads(out)["format"]["duration"])


def decode_mono(path: Path, sr: int):
    import numpy as np

    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-nostdin", "-i", str(path),
        "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "1", "-ar", str(sr), "-",
    ])
    return np.frombuffer(raw, dtype=np.float32).copy()


def detect_speech_bounds(audio, sr: int, search_start: float, search_end: float,
                         threshold_db: float = -45.0, soft_db: float = -55.0,
                         frame_s: float = 0.01, sustain_s: float = 0.05,
                         backtrack_s: float = 0.12, forward_s: float = 0.15) -> tuple[float, float]:
    """Find sustained speech inside [search_start, search_end] (absolute seconds).

    Isolated clicks are ignored: speech must stay above ``threshold_db``
    for ``sustain_s``. A softer threshold then backtracks/forwards a
    little so quiet onsets and tails are kept.
    """
    import numpy as np

    start_sample = max(0, int(search_start * sr))
    end_sample = min(len(audio), int(round(search_end * sr)))
    window = audio[start_sample:end_sample]
    frame = max(1, int(frame_s * sr))
    if len(window) < frame:
        raise RuntimeError("search window is shorter than one analysis frame")
    rms = np.array([
        np.sqrt(np.mean(window[i:i + frame] ** 2) + 1e-12)
        for i in range(0, len(window) - frame + 1, frame)
    ])
    db = 20 * np.log10(rms + 1e-12)
    sustain = max(1, int(round(sustain_s / frame_s)))
    above = db > threshold_db
    if len(db) < sustain:
        raise RuntimeError("search window too short for sustained-speech detection")
    sustained = np.convolve(above.astype(int), np.ones(sustain, dtype=int), mode="valid")
    starts = np.where(sustained == sustain)[0]
    if len(starts) == 0:
        raise RuntimeError("no sustained speech found in search window")
    first_core = int(starts[0])
    last_core_start = int(starts[-1])
    back_frames = int(round(backtrack_s / frame_s))
    back_from = max(0, first_core - back_frames)
    back = np.where(db[back_from:first_core + 1] > soft_db)[0]
    first = back_from + int(back[0]) if len(back) else first_core
    last_core_end = last_core_start + sustain
    fwd_frames = int(round(forward_s / frame_s))
    forward_end = min(len(db), last_core_end + fwd_frames)
    fwd = np.where(db[last_core_end:forward_end] > soft_db)[0]
    last = last_core_end + int(fwd[-1] + 1) if len(fwd) else last_core_end
    offset = start_sample / sr
    return offset + first * frame_s, offset + last * frame_s


class SourceResolver:
    def __init__(self, source_root: Path | None, decisions_dir: Path):
        self.source_root = source_root
        self.decisions_dir = decisions_dir
        self._by_name: dict[str, Path] | None = None

    def _index(self) -> dict[str, Path]:
        if self._by_name is None:
            self._by_name = {}
            if self.source_root and self.source_root.is_dir():
                for path in sorted(self.source_root.rglob("*"), key=natural_key):
                    if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                        self._by_name.setdefault(path.name, path.resolve())
        return self._by_name

    def resolve(self, unit: dict[str, Any]) -> Path:
        candidates: list[Path] = []
        source = unit.get("source") or unit.get("source_file")
        if source:
            raw = Path(str(source)).expanduser()
            candidates.append(raw)
            if not raw.is_absolute():
                if self.source_root:
                    candidates.append(self.source_root / raw)
                candidates.append(self.decisions_dir / raw)
        source_name = unit.get("source_name") or (Path(str(source)).name if source else None)
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        if source_name:
            found = self._index().get(str(source_name))
            if found:
                return found
        raise SystemExit(f"source audio not found for unit {unit.get('id')}: source={source!r} source_name={source_name!r}")

    def portable_source(self, resolved: Path, unit: dict[str, Any]) -> str:
        if self.source_root:
            try:
                return str(resolved.relative_to(self.source_root.resolve()))
            except ValueError:
                pass
        source = unit.get("source")
        if source and not Path(str(source)).is_absolute():
            return str(source)
        return resolved.name


def optional_float(unit: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = unit.get(key)
        if value is not None:
            return float(value)
    return None


def build_filters(cleanup: str, start: float, end: float, highpass_hz: float,
                  fade_in_s: float, fade_out_s: float, sample_rate: int) -> list[str]:
    duration = end - start
    filters = [f"atrim=start={start:.3f}:end={end:.3f}", "asetpts=N/SR/TB"]
    if cleanup in {"standard", "raw_phone"}:
        filters.append(f"highpass=f={highpass_hz:g}")
    if cleanup == "raw_phone":
        filters += ["afftdn=nr=5:nf=-30", "lowpass=f=12500"]
    if cleanup in {"standard", "raw_phone"}:
        filters.append(f"afade=t=in:st=0:d={fade_in_s:.3f}")
        filters.append(f"afade=t=out:st={max(0.0, duration - fade_out_s):.3f}:d={fade_out_s:.3f}")
    filters.append(f"aresample={sample_rate}")
    return filters


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--decisions", type=Path, required=True, help="decisions JSON (or an existing voice_units.json)")
    parser.add_argument("--source-root", type=Path, help="folder containing source clips (overrides decisions source_root)")
    parser.add_argument("--out-dir", type=Path, required=True, help="folder for Mxx.wav files")
    parser.add_argument("--out-manifest", type=Path, required=True, help="voice_units.json to write")
    parser.add_argument("--sample-rate", type=int, default=None, help="default: decisions or 48000")
    parser.add_argument("--lead-handle", type=float, default=None, help="default: decisions or 0.08")
    parser.add_argument("--tail-handle", type=float, default=None, help="default: decisions or 0.10")
    parser.add_argument("--cleanup", choices=["standard", "raw_phone", "none"], default=None,
                        help="default cleanup for units that do not specify one")
    parser.add_argument("--explicit-handle-mode", choices=["configured", "actual"], default="configured",
                        help="for an explicitly trimmed side, record the configured handle (matches the "
                             "reference production) or the measured one")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing existing output wavs")
    parser.add_argument("--dry-run", action="store_true", help="detect bounds and write the manifest, but create no wav files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.decisions.is_file():
        raise SystemExit(f"decisions file not found: {args.decisions}")
    raw = json.loads(args.decisions.read_text(encoding="utf-8"))
    root: dict[str, Any] = raw if isinstance(raw, dict) else {"units": raw}
    units_in = root.get("units")
    if not isinstance(units_in, list) or not units_in:
        raise SystemExit("decisions must contain a non-empty 'units' list")

    defaults: dict[str, Any] = root.get("defaults", {}) if isinstance(root.get("defaults"), dict) else {}
    sample_rate = int(args.sample_rate or defaults.get("sample_rate_hz") or root.get("sample_rate_hz") or 48000)
    lead_handle = float(args.lead_handle if args.lead_handle is not None else defaults.get("lead_handle_s", 0.08))
    tail_handle = float(args.tail_handle if args.tail_handle is not None else defaults.get("tail_handle_s", 0.10))
    highpass_hz = float(defaults.get("highpass_hz", 65))
    fade_in_s = float(defaults.get("fade_in_s", 0.008))
    fade_out_s = float(defaults.get("fade_out_s", 0.012))
    default_cleanup = str(args.cleanup or defaults.get("cleanup") or "standard")

    source_root_value = args.source_root or (Path(str(root["source_root"])).expanduser() if root.get("source_root") else None)
    if source_root_value and not source_root_value.is_absolute():
        source_root_value = (args.decisions.resolve().parent / source_root_value)
    resolver = SourceResolver(source_root_value.resolve() if source_root_value else None,
                                args.decisions.resolve().parent)

    seen_ids: set[str] = set()
    rows: list[dict[str, Any]] = []
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for unit in units_in:
        if not isinstance(unit, dict):
            raise SystemExit("every unit must be a JSON object")
        uid = str(unit.get("id") or "").strip()
        if not uid:
            raise SystemExit("every unit needs an id")
        if uid in seen_ids:
            raise SystemExit(f"duplicate unit id: {uid}")
        seen_ids.add(uid)

        src = resolver.resolve(unit)
        src_duration = ffprobe_duration(src)

        trim_pair = unit.get("trim") if isinstance(unit.get("trim"), (list, tuple)) else None
        explicit_start = optional_float(unit, "trim_start_s")
        explicit_end = optional_float(unit, "trim_end_s")
        if trim_pair is not None:
            if explicit_start is None and trim_pair[0] is not None:
                explicit_start = float(trim_pair[0])
            if explicit_end is None and trim_pair[1] is not None:
                explicit_end = float(trim_pair[1])

        speech_start = optional_float(unit, "speech_start_s")
        speech_end = optional_float(unit, "speech_end_s")
        if speech_start is None or speech_end is None:
            audio = decode_mono(src, sample_rate)
            detected_start, detected_end = detect_speech_bounds(
                audio, sample_rate,
                explicit_start if explicit_start is not None else 0.0,
                explicit_end if explicit_end is not None else src_duration,
            )
            speech_start = detected_start if speech_start is None else speech_start
            speech_end = detected_end if speech_end is None else speech_end

        start = explicit_start if explicit_start is not None else max(0.0, speech_start - lead_handle)
        end = explicit_end if explicit_end is not None else min(src_duration, speech_end + tail_handle)
        if not (0.0 <= start < end <= src_duration + 0.05):
            raise SystemExit(f"{uid}: invalid trim {start:.3f}..{end:.3f} for source duration {src_duration:.3f}")
        end = min(end, src_duration)

        if args.explicit_handle_mode == "configured" and explicit_start is not None:
            lead = lead_handle
        else:
            lead = max(0.0, speech_start - start)
        if args.explicit_handle_mode == "configured" and explicit_end is not None:
            tail = tail_handle
        else:
            tail = max(0.0, end - speech_end)
        if unit.get("lead_handle_s") is not None and explicit_start is not None and "speech_start_s" in unit:
            lead = float(unit["lead_handle_s"])
        if unit.get("tail_handle_s") is not None and explicit_end is not None and "speech_end_s" in unit:
            tail = float(unit["tail_handle_s"])

        cleanup = str(unit.get("cleanup") or default_cleanup)
        if cleanup == "auto":
            cleanup = "raw_phone" if unit.get("unenhanced") else "standard"
        if cleanup not in {"standard", "raw_phone", "none"}:
            raise SystemExit(f"{uid}: unknown cleanup {cleanup!r}")

        out_path = args.out_dir / f"{uid}.wav"
        if args.dry_run:
            actual = end - start
        else:
            if out_path.exists() and not args.overwrite:
                raise SystemExit(f"output exists (use --overwrite to replace): {out_path}")
            filters = build_filters(cleanup, start, end, highpass_hz, fade_in_s, fade_out_s, sample_rate)
            cmd = [
                "ffmpeg", "-y" if args.overwrite else "-n", "-hide_banner", "-loglevel", "error",
                "-nostdin", "-i", str(src), "-af", ",".join(filters),
                "-ac", "1", "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(out_path),
            ]
            subprocess.run(cmd, check=True)
            actual = ffprobe_duration(out_path)

        gap = unit.get("gap_after_speech_s", unit.get("gap_after_s"))
        row = {
            "id": uid,
            "source": resolver.portable_source(src, unit),
            "source_name": src.name,
            "trim_start_s": round(start, 3),
            "trim_end_s": round(end, 3),
            "speech_start_s": round(speech_start, 3),
            "speech_end_s": round(speech_end, 3),
            "duration_s": round(actual, 3),
            "lead_handle_s": round(lead, 3),
            "tail_handle_s": round(tail, 3),
            "gap_after_speech_s": None if gap is None else float(gap),
            "text_bn_corrected": str(unit.get("text_bn_corrected") or unit.get("text_bn") or unit.get("text") or ""),
            "visual": str(unit.get("visual") or ""),
            "file": out_path.name,
        }
        rows.append(row)
        print(f"{uid} {actual:5.2f}s  {src.name} [{start:.2f}-{end:.2f}] cleanup={cleanup}")

    excluded = root.get("excluded_alternate_takes") or root.get("excluded") or []
    manifest = {
        "purpose": str(root.get("purpose") or "Own voice, micro-segmented for ManimCE sync"),
        "excluded_alternate_takes": [
            {"file": str(item.get("file") or item.get("source_name") or ""), "reason": str(item.get("reason") or "")}
            for item in excluded if isinstance(item, dict)
        ],
        "units": rows,
        "total_clean_duration_s": round(sum(r["duration_s"] for r in rows), 3),
    }
    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"TOTAL clean audio: {manifest['total_clean_duration_s']:.2f}s")
    print("WROTE", args.out_manifest)
    if args.dry_run:
        print("DRY RUN: no wav files were written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
