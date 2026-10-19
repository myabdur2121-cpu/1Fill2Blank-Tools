#!/usr/bin/env python3
"""Build a one-line-per-project INDEX draft for a folder of projects.

Read-only: prints Markdown to stdout (or ``--output``). It follows the
owner's ``mywork`` discipline (see Tools ``docs/bn/06-ecosystem-map.md``):
one line per project, a short "what is it", a status emoji, and the main
files. Status/summary are taken from each project's ``notes.md``/``README.md``
when present; main files are guessed by simple, visible heuristics so a
human can correct the draft.

Example::

    python project_index.py path/to/year2026 > INDEX.draft.md
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from pathlib import Path

IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
STATUS_EMOJI = ["✅", "🚧", "❌"]
STATUS_LABEL = {"✅": "✅ passed", "🚧": "🚧 চলমান", "❌": "❌ বাতিল"}


def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            out.append(Path(dirpath) / name)
    return sorted(out)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def clean_cell(text: str, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", text).strip().replace("|", "\\|")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text or "—"


def find_status(project: Path, root: Path) -> str:
    docs = [read_text(project / "notes.md"), read_text(project / "README.md")]
    for text in docs:
        for line in text.splitlines():
            if "status" in line.lower() or "অবস্থা" in line:
                for emoji in STATUS_EMOJI:
                    if emoji in line:
                        return STATUS_LABEL[emoji]
    index_text = read_text(root / "INDEX.md")
    for line in index_text.splitlines():
        if project.name in line:
            for emoji in STATUS_EMOJI:
                if emoji in line:
                    return STATUS_LABEL[emoji]
    for text in docs:
        for emoji in STATUS_EMOJI:
            if emoji in text:
                return STATUS_LABEL[emoji]
    return "? অজানা"


def find_summary(project: Path) -> str:
    for name in ("notes.md", "README.md"):
        text = read_text(project / name)
        if not text:
            continue
        for line in text.splitlines():
            if "কী:" in line:
                return clean_cell(line.split("কী:", 1)[1].lstrip(" -"))
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                title = re.sub(rf"^{re.escape(project.name)}\s*[—:\-]*\s*", "", title)
                if title:
                    return clean_cell(title)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith(("`", "|", "-", "#")):
                return clean_cell(stripped)
    return "—"


def scene_class_count(text: str) -> int:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return -1  # broken file marker

    def base_name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Subscript):
            return base_name(node.value)
        return ""

    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    scenes: set[str] = set()
    changed = True
    while changed:
        changed = False
        for cls in classes:
            if cls.name in scenes:
                continue
            bases = [base_name(b) for b in cls.bases]
            if any(b.endswith("Scene") or b == "BaseScene" or b in scenes for b in bases):
                scenes.add(cls.name)
                changed = True
    return len(scenes)


def score_main_file(path: Path, project: Path) -> float:
    rel = path.relative_to(project)
    name = path.name.lower()
    text = read_text(path)
    lines = text.count("\n") + 1 if text else 0
    scenes = scene_class_count(text)
    score = 0.0
    if name in {"scene_construct.py", "main.py"} or name.endswith("_scene.py"):
        score += 5
    if name in {"common.py", "engine.py", "helpers.py"} or "_lib" in name:
        score += 3
    if re.fullmatch(r"part\d+\.py", name):
        score += 3
    if scenes > 0:
        score += min(scenes, 3) * 2
    score += min(lines / 500.0, 2.0)
    if any(token in name for token in ("test", "demo", "variant")):
        score -= 2
    if "old_versions" in rel.parts:
        score -= 3
    if scenes < 0:
        score -= 5
    return score


def project_dirs(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in IGNORE_DIRS or child.name.startswith("."):
            continue
        files = walk_files(child)
        if any(p.suffix == ".py" for p in files) or (child / "notes.md").exists():
            candidates.append(child)
    return candidates or [root]


def build_index(root: Path, max_main: int) -> str:
    projects = project_dirs(root)
    index_text = read_text(root / "INDEX.md")
    lines: list[str] = []
    lines.append(f"# Project INDEX (খসড়া) — {root.name}")
    lines.append("")
    lines.append("> `project_index.py` দিয়ে বানানো খসড়া। status/summary মিলিয়ে তবে canonical করো।")
    lines.append("")
    lines.append("| project | status | কী | ফাইল (Python) | main ফাইল (অনুমান) | টীকা |")
    lines.append("|---|---|---|---:|---|---|")
    for project in projects:
        files = walk_files(project)
        py_files = [p for p in files if p.suffix == ".py"]
        ranked = sorted(
            py_files,
            key=lambda p: (-score_main_file(p, project), str(p.relative_to(project))),
        )[:max_main]
        main_cell = "<br>".join(
            f"`{p.relative_to(project)}`" for p in ranked
        ) or "—"
        note = ""
        if index_text and project.parent == root and project.name not in index_text:
            note = "⚠️ বিদ্যমান INDEX-এ নেই"
        lines.append(
            f"| `{project.name}` | {find_status(project, root)} | {find_summary(project)} | "
            f"{len(files)} ({len(py_files)}) | {main_cell} | {note} |"
        )
    lines.append("")
    lines.append("নিয়ম: project-প্রতি এক লাইন; status বদলালে emoji বদলাও; পুরনো বছর read-only।")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Draft a one-line-per-project INDEX (read-only)."
    )
    parser.add_argument("root", type=Path, help="Folder containing project folders")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Write here instead of stdout")
    parser.add_argument("--max-main", type=int, default=4, help="Main-file guesses per project")
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    report = build_index(root, max(args.max_main, 1))
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
