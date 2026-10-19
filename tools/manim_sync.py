#!/usr/bin/env python3
"""Reusable ManimCE scene-time helpers for voice synchronisation.

Typical use in a scene file::

    from manim import *
    from manim_sync import VoiceSyncMixin

    class MyScene(VoiceSyncMixin, MovingCameraScene):
        def construct(self):
            # Build mobjects first (this takes wall-clock time, not scene time).
            ...

            self.sync_start("S01")
            ... animations for segment S01 ...
            self.pad("S01")        # extra hold from pad.json, if needed
            self.mark("S02")       # write the exact scene time to marks.json
            ... animations for segment S02 ...

File locations can be supplied in three ways, in this order:
1. ``pad_file`` / ``marks_file`` class attributes on the scene;
2. ``VOICE_PAD_FILE`` / ``SCENE_MARKS_FILE`` environment variables;
3. ``pad.json`` / ``marks.json`` in the current working directory.

The mixin intentionally does not import Manim.  It only needs the host
scene to provide ``wait()`` and, optionally, ``next_section()`` plus a
renderer/scene time.  This keeps the helper unit-testable.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _path_from(value: str | Path | None, env_name: str, default: str) -> Path | None:
    if value is not None:
        text = str(value).strip()
        return Path(text).expanduser() if text else None
    env_value = os.environ.get(env_name, "").strip()
    return Path(env_value).expanduser() if env_value else Path(default)


def _read_json_object(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_pads(path: str | Path | None = None) -> dict[str, float]:
    """Load ``{"S01": 1.25, ...}``; missing/invalid data becomes no pads."""
    pad_path = _path_from(path, "VOICE_PAD_FILE", "pad.json")
    raw = _read_json_object(pad_path)
    pads: dict[str, float] = {}
    for key, value in raw.items():
        try:
            pads[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return pads


class VoiceSyncMixin:
    """Add ``sync_start()``, ``mark()`` and ``pad()`` to a Manim scene."""

    pad_file: str | Path | None = None
    marks_file: str | Path | None = None
    voice_pads: dict[str, float] | None = None

    def _pad_path(self) -> Path | None:
        return _path_from(self.pad_file, "VOICE_PAD_FILE", "pad.json")

    def _marks_path(self) -> Path | None:
        return _path_from(self.marks_file, "SCENE_MARKS_FILE", "marks.json")

    def sync_start(self, first_mark: str | None = "S01", *, clear_marks: bool = True) -> None:
        """Reload pads, optionally clear old marks, then record the first mark."""
        self.voice_pads = load_pads(self._pad_path())
        marks_path = self._marks_path()
        if clear_marks and marks_path is not None:
            try:
                marks_path.unlink(missing_ok=True)
            except Exception:
                pass
        if first_mark:
            self.mark(first_mark)

    def _scene_time(self) -> float:
        """Return Manim's scene time, tolerating ManimCE API differences."""
        try:
            value = getattr(getattr(self, "renderer", None), "time", None)
            if value is not None:
                return float(value() if callable(value) else value)
        except Exception:
            pass
        try:
            value = getattr(self, "time", None)
            return float(value() if callable(value) else value)
        except Exception:
            return 0.0

    def mark(self, name: str) -> float:
        """Record the current scene time under ``name`` and return it."""
        current = self._scene_time()
        path = self._marks_path()
        if path is not None:
            data = _read_json_object(path)
            data[str(name)] = current
            try:
                if str(path.parent):
                    path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                pass

        print(f"[MARK] {name} @ {current:.3f}")
        next_section = getattr(self, "next_section", None)
        if callable(next_section):
            try:
                next_section(str(name))
            except Exception:
                pass
        return current

    def pad(self, key: str) -> float:
        """Wait for this segment's precomputed extra hold, if it has one."""
        if self.voice_pads is None:
            self.voice_pads = load_pads(self._pad_path())
        try:
            seconds = float(self.voice_pads.get(str(key), 0.0))
        except (TypeError, ValueError):
            seconds = 0.0
        if seconds > 0.02:
            self.wait(seconds)  # supplied by the Manim scene
        return seconds
