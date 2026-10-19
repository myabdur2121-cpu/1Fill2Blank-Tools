#!/usr/bin/env python3
"""Report disposable-cache candidates without deleting anything.

This tool never removes, moves, or renames files. It only measures and
classifies, so the owner can approve any cleanup later.

Categories:

* ``strong`` — very likely disposable: Manim ``partial_movie_files``,
  ``__pycache__``/``.pyc``, ``*.log``, LaTeX auxiliary files.
* ``review`` — generated-looking media/temp files under ``media/``,
  ``cache/``, ``tmp/`` ... look before deciding.
* ``archive_like`` — code/docs/config found *inside* a ``cache`` folder.
  These are NOT disposable just because of the folder name (the old
  workspace snapshot kept a whole project archive under ``cache/mywork``).

Example::

    python cache_report.py /path/to/workspace > cache_report.md
    python cache_report.py /path/to/workspace --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

IGNORE_DIRS = {".git"}
CANDIDATE_DIR_NAMES = {"cache", "media", "partial_movie_files", "__pycache__", "logs", "log", "tmp", "temp"}
AUX_SUFFIXES = {".aux", ".fls", ".fdb_latexmk"}
ARCHIVE_SUFFIXES = {".py", ".md", ".json", ".txt", ".sh", ".toml", ".yml", ".yaml", ".html"}
REVIEW_SUFFIXES = {".mp4", ".mov", ".mkv", ".wav", ".mp3", ".m4a", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".xdv", ".dvi"}


def human_size(n: int) -> str:
    size = float(n)
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if size < 1024 or unit == "GiB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GiB"


def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            out.append(Path(dirpath) / name)
    return out


def classify(rel: Path) -> tuple[str, str]:
    """Return (category, reason). Categories: strong/review/archive_like/other."""
    parts = rel.parts
    suffixes = "".join(rel.suffixes[-2:]).lower() if len(rel.suffixes) >= 2 else rel.suffix.lower()
    suffix = rel.suffix.lower()
    if "partial_movie_files" in parts:
        return "strong", "Manim partial render"
    if "__pycache__" in parts or suffix == ".pyc":
        return "strong", "Python bytecode cache"
    if suffix == ".log" or "logs" in parts or "log" in parts:
        return "strong", "log file"
    if suffix in AUX_SUFFIXES or suffixes == ".synctex.gz":
        return "strong", "LaTeX auxiliary"
    under_cache = "cache" in parts[:-1]
    if under_cache and (suffix in ARCHIVE_SUFFIXES or "mywork" in parts):
        return "archive_like", "cache-এর ভেতরে কোড/ডক/config—আর্কাইভ হতে পারে"
    generated_zone = any(p in {"media", "cache", "tmp", "temp"} for p in parts[:-1])
    if generated_zone and suffix in REVIEW_SUFFIXES:
        return "review", "media/cache/tmp অঞ্চলে generated-দেখতে মিডিয়া"
    if generated_zone:
        return "review", "media/cache/tmp অঞ্চলের অন্য ফাইল"
    return "other", ""


def build_data(root: Path, limit: int) -> dict:
    files = walk_files(root)
    records = []
    totals = Counter()
    counts = Counter()
    reasons = Counter()
    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        rel = path.relative_to(root)
        category, reason = classify(rel)
        records.append(
            {"rel": str(rel), "size": size, "category": category, "reason": reason}
        )
        if category != "other":
            totals[category] += size
            counts[category] += 1
            if reason:
                reasons[(category, reason)] += 1

    # Shallowest candidate directories only (avoid double-counting nested ones).
    prefixes: set[Path] = set()
    for record in records:
        parts = Path(record["rel"]).parts
        for i in range(1, len(parts)):
            prefix = Path(*parts[:i])
            if prefix.name in CANDIDATE_DIR_NAMES:
                prefixes.add(prefix)
    candidate_dirs: list[Path] = []
    for rel_d in sorted(prefixes, key=lambda p: (len(p.parts), str(p))):
        if any(parent == rel_d or parent in rel_d.parents for parent in candidate_dirs):
            continue
        candidate_dirs.append(rel_d)

    dir_rows = []
    for rel_d in candidate_dirs:
        inside = [
            r for r in records
            if Path(r["rel"]) == rel_d or rel_d in Path(r["rel"]).parents
        ]
        by_cat = Counter()
        by_cat_size = Counter()
        for r in inside:
            by_cat[r["category"]] += 1
            by_cat_size[r["category"]] += r["size"]
        dir_rows.append(
            {
                "dir": str(rel_d),
                "files": len(inside),
                "size": sum(r["size"] for r in inside),
                "strong": by_cat_size.get("strong", 0),
                "review": by_cat_size.get("review", 0),
                "archive_like": by_cat_size.get("archive_like", 0),
            }
        )

    biggest = sorted(
        [r for r in records if r["category"] in {"strong", "review"}],
        key=lambda r: r["size"],
        reverse=True,
    )[:limit]
    archive_examples = sorted(
        [r for r in records if r["category"] == "archive_like"],
        key=lambda r: r["rel"],
    )[:limit]

    return {
        "root": str(root),
        "total_files": len(records),
        "total_bytes": sum(r["size"] for r in records),
        "counts": dict(counts),
        "category_bytes": dict(totals),
        "candidate_dirs": dir_rows,
        "largest_candidates": biggest,
        "archive_like_examples": archive_examples,
        "notes": [
            "This report never deletes anything.",
            "Folder name alone is not a delete decision; review archive_like first.",
        ],
    }


def to_markdown(data: dict) -> str:
    counts = data["counts"]
    sizes = data["category_bytes"]
    lines: list[str] = []
    lines.append("# Cache রিপোর্ট (dry-run — কিছু মোছা হয়নি)")
    lines.append("")
    lines.append(f"- Root: `{data['root']}`")
    lines.append(f"- মোট ফাইল: {data['total_files']} ({human_size(data['total_bytes'])})")
    lines.append(
        f"- Strong candidate: {counts.get('strong', 0)} ফাইল, {human_size(sizes.get('strong', 0))}"
    )
    lines.append(
        f"- Review দরকার: {counts.get('review', 0)} ফাইল, {human_size(sizes.get('review', 0))}"
    )
    lines.append(
        f"- ⚠️ Archive-like (cache-এর ভেতরে কোড/ডক): {counts.get('archive_like', 0)} ফাইল, "
        f"{human_size(sizes.get('archive_like', 0))} — **এগুলো disposable ধরা যাবে না**"
    )
    lines.append("")
    if data["candidate_dirs"]:
        lines.append("## Candidate ফোল্ডার")
        lines.append("| ফোল্ডার | ফাইল | আকার | strong | review | archive-like |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for row in data["candidate_dirs"]:
            lines.append(
                f"| `{row['dir']}` | {row['files']} | {human_size(row['size'])} | "
                f"{human_size(row['strong'])} | {human_size(row['review'])} | "
                f"{human_size(row['archive_like'])} |"
            )
        lines.append("")
    if data["largest_candidates"]:
        lines.append("## সবচেয়ে বড় strong/review ফাইল")
        for r in data["largest_candidates"]:
            lines.append(
                f"- `{r['rel']}` — {human_size(r['size'])} ({r['category']}: {r['reason']})"
            )
        lines.append("")
    if data["archive_like_examples"]:
        lines.append("## Archive-like উদাহরণ (আগে যাচাই করো)")
        for r in data["archive_like_examples"]:
            lines.append(f"- `{r['rel']}` — {human_size(r['size'])}")
        lines.append("")
    lines.append("পরের ধাপ: মালিক তালিকা দেখে অনুমতি দিলেই শুধু cleanup হবে।")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run cache report (never deletes anything)."
    )
    parser.add_argument("root", type=Path, help="Workspace/project folder to inspect")
    parser.add_argument("--limit", type=int, default=20, help="How many examples to list")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    data = build_data(root, max(args.limit, 1))
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
