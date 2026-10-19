#!/usr/bin/env python3
"""Analyse a Manim project folder and draft a CODE_ANATOMY report.

The tool is read-only: it parses Python files with ``ast`` (never imports or
runs project code), tolerates broken draft files, and prints a Markdown
report to stdout (or to ``--output`` when asked).

It recognises the owner's three composition patterns (see
``docs/bn/07-code-anatomy.md``):

* A — Builder + Director ``construct()`` (hooks build ``self.*`` state,
  ``construct`` plays the whole story).
* B — Segment methods (``s01`` ...) driven by a small construct loop,
  usually synced to narration via ``clip``/``at``/``upto``.
* C — Engine/BaseScene + ``body()`` content subclasses.

Example::

    python analyze_manim_project.py path/to/project > CODE_ANATOMY.draft.md
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache"}
SCENE_BASE_HINTS = {
    "Scene",
    "MovingCameraScene",
    "ThreeDScene",
    "ZoomedScene",
    "VectorScene",
    "BaseScene",
}
GENERATED_MARKERS = ("generated", "do not edit", "do-not-edit", "হাতে সম্পাদনা")
SEGMENT_RE = re.compile(r"^(s\d+|segment_\d+)$")
DATA_EXTS = {
    ".aac", ".flac", ".html", ".jpg", ".jpeg", ".json", ".m4a", ".md", ".mp3",
    ".mp4", ".ogg", ".opus", ".otf", ".pdf", ".png", ".svg", ".tex", ".ttf",
    ".txt", ".wav", ".woff2",
}
ASSET_DIR_NAMES = {"audio", "narration", "assets", "music", "fonts", "images"}


def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            out.append(Path(dirpath) / name)
    return sorted(out)


def base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return base_name(node.value)
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - very old Python fallback
        return type(node).__name__


def call_label(func: ast.expr) -> str:
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name) and func.value.id == "self":
            return f"self.{func.attr}"
        return f".{func.attr}"
    if isinstance(func, ast.Name):
        return func.id
    return type(func).__name__


@dataclass
class MethodInfo:
    name: str
    lineno: int
    end_lineno: int
    play: int = 0
    wait: int = 0
    add_sound: int = 0
    self_calls: Counter = field(default_factory=Counter)
    name_calls: Counter = field(default_factory=Counter)
    sets_self: list[str] = field(default_factory=list)
    has_return: bool = False
    direct_sequence: list[str] = field(default_factory=list)
    clip_names: list[str] = field(default_factory=list)
    at_times: list[float] = field(default_factory=list)
    has_segment_loop: bool = False

    @property
    def role(self) -> str:
        if self.name == "construct":
            return "director/construct"
        if self.name == "body":
            return "content body"
        if self.play or self.wait or self.add_sound:
            return "micro-action/timeline"
        if self.sets_self:
            return "builder (state)"
        if self.has_return:
            return "factory/helper"
        return "helper"


@dataclass
class ClassInfo:
    name: str
    bases: list[str]
    lineno: int
    is_scene: bool
    methods: dict[str, MethodInfo]
    pattern: str = "-"
    pattern_reason: str = ""


@dataclass
class FileInfo:
    rel: str
    lines: int
    parse_error: str | None
    generated: bool
    imports: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)


def _direct_sequence(fn: ast.FunctionDef) -> list[str]:
    seq: list[str] = []
    for stmt in fn.body:
        node = None
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            node = stmt.value
        elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
            node = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.value, ast.Call):
            node = stmt.value
        if node is not None:
            seq.append(call_label(node.func))
        elif isinstance(stmt, (ast.For, ast.While)):
            seq.append("<loop>")
        elif isinstance(stmt, ast.If):
            seq.append("<if>")
    compressed: list[str] = []
    for item in seq:
        if not compressed or compressed[-1] != item:
            compressed.append(item)
    return compressed


def _has_segment_loop(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.For):
            for sub in ast.walk(node):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "getattr"
                    and sub.args
                    and isinstance(sub.args[0], ast.Name)
                    and sub.args[0].id == "self"
                ):
                    return True
    return False


def method_info(fn: ast.FunctionDef) -> MethodInfo:
    info = MethodInfo(
        name=fn.name,
        lineno=fn.lineno,
        end_lineno=fn.end_lineno or fn.lineno,
        direct_sequence=_direct_sequence(fn),
        has_segment_loop=_has_segment_loop(fn),
    )
    sets: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
            ):
                attr = node.func.attr
                info.self_calls[attr] += 1
                if attr == "play":
                    info.play += 1
                elif attr == "wait":
                    info.wait += 1
                elif attr == "add_sound":
                    info.add_sound += 1
                elif attr == "clip" and node.args and isinstance(node.args[0], ast.Constant):
                    if isinstance(node.args[0].value, str):
                        info.clip_names.append(node.args[0].value)
                elif attr in {"at", "playto", "upto"} and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)):
                        info.at_times.append(float(arg.value))
            elif isinstance(node.func, ast.Name):
                info.name_calls[node.func.id] += 1
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    sets.add(target.attr)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            target = node.target
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                sets.add(target.attr)
        elif isinstance(node, ast.Return) and node.value is not None:
            info.has_return = True
    info.sets_self = sorted(sets)
    return info


def classify_pattern(cls: ClassInfo) -> tuple[str, str]:
    methods = cls.methods
    construct = methods.get("construct")
    body = methods.get("body")
    segments = [name for name in methods if SEGMENT_RE.match(name)]
    builders = [
        mi.name
        for name, mi in methods.items()
        if name != "construct" and mi.role in {"builder (state)", "factory/helper"}
    ]
    if construct and len(segments) >= 3:
        explicit_segment_calls = [
            c for c in construct.self_calls if SEGMENT_RE.match(c)
        ]
        if construct.has_segment_loop or len(explicit_segment_calls) >= 3:
            return "B", "construct segment loop/getattr বা বহু segment কল চালায়"
    if construct and "body" in construct.self_calls:
        return "C-base", "construct নিজে lifecycle চালিয়ে body() ডাকে"
    if body and not construct:
        return "C-content", "শুধু body() override করা content subclass"
    if construct:
        called_builders = [
            item[5:]
            for item in construct.direct_sequence
            if item.startswith("self.") and item[5:] in builders
        ]
        if construct.play >= 10 and len(builders) >= 3 and len(called_builders) >= 2:
            return "A", "builder গুলো state সাজায়, construct পুরো গল্প play করে"
        return "Direct", "construct নিজেই সরাসরি টাইমলাইন"
    return "-", "scene timeline পাওয়া যায়নি"


def analyze_file(path: Path, root: Path) -> FileInfo:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(root))
    head = "\n".join(text.splitlines()[:40]).lower()
    info = FileInfo(
        rel=rel,
        lines=text.count("\n") + 1,
        parse_error=None,
        generated=any(marker in head for marker in GENERATED_MARKERS),
    )
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        info.parse_error = f"line {exc.lineno}: {exc.msg}"
        return info

    for node in tree.body:
        if isinstance(node, ast.Import):
            info.imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            info.imports.append(node.module or ".")
        elif isinstance(node, ast.FunctionDef):
            info.functions.append(node.name)

    raw_classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    # Resolve local scene inheritance (e.g. P1S01(P1) where P1(Scene)).
    scene_names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for cls_node in raw_classes:
            if cls_node.name in scene_names:
                continue
            bases = [base_name(b) for b in cls_node.bases]
            if any(
                b in SCENE_BASE_HINTS or b.endswith("Scene") or b in scene_names
                for b in bases
            ):
                scene_names.add(cls_node.name)
                changed = True

    for cls_node in raw_classes:
        methods = {
            node.name: method_info(node)
            for node in cls_node.body
            if isinstance(node, ast.FunctionDef)
        }
        cls_info = ClassInfo(
            name=cls_node.name,
            bases=[base_name(b) for b in cls_node.bases],
            lineno=cls_node.lineno,
            is_scene=cls_node.name in scene_names,
            methods=methods,
        )
        if cls_info.is_scene:
            cls_info.pattern, cls_info.pattern_reason = classify_pattern(cls_info)
        info.classes.append(cls_info)
    return info


def _short(items: list[str], limit: int) -> str:
    if not items:
        return "—"
    shown = items[:limit]
    suffix = f" …(+{len(items) - limit})" if len(items) > limit else ""
    return ", ".join(f"`{item}`" for item in shown) + suffix


def build_report(root: Path) -> str:
    all_files = walk_files(root)
    py_files = [p for p in all_files if p.suffix == ".py"]
    infos = [analyze_file(p, root) for p in py_files]
    scene_classes: list[tuple[FileInfo, ClassInfo]] = [
        (fi, ci) for fi in infos for ci in fi.classes if ci.is_scene
    ]
    broken = [fi for fi in infos if fi.parse_error]
    generated = [fi for fi in infos if fi.generated]
    pattern_counts = Counter(ci.pattern for _, ci in scene_classes)
    ext_counts = Counter(
        p.suffix.lower()
        for p in all_files
        if p.suffix.lower() in DATA_EXTS and p.suffix.lower() != ".py"
    )

    lines: list[str] = []
    lines.append(f"# CODE ANATOMY (খসড়া) — {root.name}")
    lines.append("")
    lines.append(
        "> এই খসড়াটা `analyze_manim_project.py` বানিয়েছে। canonical ধরার আগে "
        "মানুষ/AI দিয়ে মিলিয়ে নাও। প্যাটার্নের ব্যাখ্যা: "
        "Tools repo-র `docs/bn/07-code-anatomy.md`।"
    )
    lines.append("")
    lines.append("## এক নজরে")
    lines.append(f"- Python ফাইল: {len(infos)} (মোট লাইন ~{sum(fi.lines for fi in infos)})")
    lines.append(f"- Scene class: {len(scene_classes)}")
    if pattern_counts:
        pretty = ", ".join(f"{k}: {v}" for k, v in sorted(pattern_counts.items()))
        lines.append(f"- প্যাটার্ন বণ্টন: {pretty}")
    lines.append(f"- ভাঙা (syntax error) ফাইল: {len(broken)}")
    lines.append(f"- Generated চিহ্নিত ফাইল: {len(generated)}")
    if ext_counts:
        top = ", ".join(f"{ext or '(none)'}×{n}" for ext, n in ext_counts.most_common(12))
        lines.append(f"- ডেটা/asset ধরন: {top}")
    lines.append("")

    lines.append("## ফাইল তালিকা")
    lines.append("| ফাইল | লাইন | class | scene | মন্তব্য |")
    lines.append("|---|---:|---|---|---|")
    for fi in infos:
        class_names = [c.name for c in fi.classes]
        scenes = [c.name for c in fi.classes if c.is_scene]
        notes: list[str] = []
        if fi.parse_error:
            notes.append(f"⚠️ {fi.parse_error}")
        if fi.generated:
            notes.append("generated?")
        if fi.functions and not scenes:
            notes.append(f"helpers: {_short(fi.functions, 6)}")
        if len(scenes) >= 4:
            notes.append("বহু variant (lab হতে পারে)")
        lines.append(
            f"| `{fi.rel}` | {fi.lines} | {_short(class_names, 5)} | "
            f"{_short(scenes, 5)} | {'<br>'.join(notes)} |"
        )
    lines.append("")

    by_pattern: dict[str, list[tuple[FileInfo, ClassInfo]]] = defaultdict(list)
    for fi, ci in scene_classes:
        by_pattern[ci.pattern].append((fi, ci))
    lines.append("## প্যাটার্ন অনুযায়ী scene class")
    for pattern in ["A", "B", "C-base", "C-content", "Direct", "-"]:
        group = by_pattern.get(pattern, [])
        if not group:
            continue
        lines.append(f"### {pattern} ({len(group)})")
        for fi, ci in group[:60]:
            lines.append(
                f"- `{fi.rel}::{ci.name}` — {ci.pattern_reason}"
            )
        if len(group) > 60:
            lines.append(f"- …আরও {len(group) - 60}টা (খসড়ায় সংক্ষেপিত)")
    lines.append("")

    lines.append("## বিস্তারিত scene মানচিত্র")
    for fi, ci in scene_classes:
        construct = ci.methods.get("construct")
        lines.append(f"### `{fi.rel}::{ci.name}` — প্যাটার্ন {ci.pattern}")
        lines.append(
            f"- Bases: {_short(ci.bases, 5)}; methods: {len(ci.methods)}"
        )
        if construct:
            seq = " -> ".join(construct.direct_sequence[:40])
            lines.append(
                f"- construct: {construct.end_lineno - construct.lineno + 1} লাইন, "
                f"play×{construct.play}, wait×{construct.wait}"
            )
            if seq:
                lines.append(f"- construct-এর সরাসরি ক্রম (সংক্ষেপে): `{seq}`")
        if ci.pattern == "A":
            lines.append("| builder/action | ভূমিকা | বসানো state |")
            lines.append("|---|---|---|")
            for name, mi in ci.methods.items():
                if name == "construct":
                    continue
                lines.append(
                    f"| `{name}` | {mi.role} (play×{mi.play}) | {_short(mi.sets_self, 8)} |"
                )
        elif ci.pattern == "B":
            lines.append("| segment | narration clip | সময়-ইঙ্গিত |")
            lines.append("|---|---|---|")
            for name in sorted(
                [n for n in ci.methods if SEGMENT_RE.match(n)],
                key=lambda s: int(re.sub(r"\D", "", s) or 0),
            ):
                mi = ci.methods[name]
                times = "—"
                if mi.at_times:
                    times = f"{min(mi.at_times):g}–{max(mi.at_times):g}s ({len(mi.at_times)}টা)"
                lines.append(
                    f"| `{name}` | {_short(mi.clip_names, 3)} | {times} |"
                )
        elif ci.pattern in {"C-base", "C-content"}:
            body = ci.methods.get("body")
            if body:
                top_calls = [
                    name for name, _ in body.name_calls.most_common(10)
                ]
                lines.append(f"- body() প্রধান helper কল: {_short(top_calls, 10)}")
        lines.append("")

    helper_files = [
        fi
        for fi in infos
        if not any(c.is_scene for c in fi.classes)
        and (len(fi.functions) >= 3 or Path(fi.rel).name in {"common.py", "engine.py", "helpers.py"})
    ]
    if helper_files:
        lines.append("## Shared helper/engine মডিউল (প্রার্থী)")
        lines.append("| ফাইল | top-level function | import |")
        lines.append("|---|---|---|")
        for fi in helper_files:
            lines.append(
                f"| `{fi.rel}` | {_short(fi.functions, 10)} | {_short(fi.imports, 6)} |"
            )
        lines.append("")

    asset_dirs: Counter = Counter()
    for p in all_files:
        for part in p.relative_to(root).parts[:-1]:
            if part in ASSET_DIR_NAMES:
                asset_dirs[part] += 1
    if asset_dirs:
        lines.append("## ডেটা/asset ফোল্ডার")
        for name, count in sorted(asset_dirs.items()):
            lines.append(f"- `{name}/` — {count} ফাইল")
        lines.append("")

    if broken:
        lines.append("## ভাঙা ফাইল (নিজে থেকে ঠিক কোরো না)")
        for fi in broken:
            lines.append(f"- `{fi.rel}` — {fi.parse_error}")
        lines.append("")
    if generated:
        lines.append("## Generated হতে পারে (উৎস খোঁজো)")
        for fi in generated:
            lines.append(f"- `{fi.rel}`")
        lines.append("")

    lines.append("## নিরাপদ সম্পাদনার সাধারণ নিয়ম")
    lines.append("- Pattern A: চেহারা builder-এ, ক্রম/সময় construct-এ।")
    lines.append("- Pattern B: সংশ্লিষ্ট segment method আর narration ম্যাপে কাজ করো।")
    lines.append("- Pattern C: content body/ডেটায়; আচরণ ইঞ্জিনে (সব পর্বে প্রভাব পড়ে)।")
    lines.append("- Generated ফাইল হাতে সম্পাদনা নয়; ভাঙা ফাইল অনুমতি ছাড়া \"ঠিক\" নয়।")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Draft a CODE_ANATOMY report for a Manim project folder (read-only)."
    )
    parser.add_argument("root", type=Path, help="Project folder to analyse")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Write the report to this file instead of stdout",
    )
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    report = build_report(root)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
