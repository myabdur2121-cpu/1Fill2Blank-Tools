#!/usr/bin/env python3
"""Lightweight smoke tests for the ecosystem tools.

Run from the repository root:

    python3 -m unittest discover -s tests -v

These tests use only the standard library and small synthetic fixtures:
no downloads, no Manim render, no ASR model, no external snapshots.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"


def load_tool(name: str):
    path = TOOLS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"tool_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


analyzer = load_tool("analyze_manim_project")
cache_report = load_tool("cache_report")
project_index = load_tool("project_index")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class AnalyzerPatternsTest(unittest.TestCase):
    def test_patterns_and_broken_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plays = "\n".join("        self.play(FadeIn(self.one))" for _ in range(10))
            write(
                root / "pattern_a.py",
                "from manim import *\n\n"
                "class AScene(MovingCameraScene):\n"
                "    def build_one(self):\n"
                "        self.one = Square()\n\n"
                "    def build_two(self):\n"
                "        self.two = Circle()\n\n"
                "    def make_three(self):\n"
                "        return VGroup()\n\n"
                "    def construct(self):\n"
                "        self.build_one()\n"
                "        self.build_two()\n"
                "        thing = self.make_three()\n"
                f"{plays}\n"
                "        self.wait(1)\n",
            )
            write(
                root / "pattern_b.py",
                "from manim import *\n\n"
                "class Narrated:\n"
                "    pass\n\n"
                "class BScene(Narrated, MovingCameraScene):\n"
                "    def construct(self):\n"
                "        for i in range(1, 4):\n"
                "            getattr(self, f\"s{i:02d}\")()\n\n"
                "    def s01(self):\n"
                "        self.clip(\"p2_01\")\n"
                "        self.at(1.0, FadeIn(Square()))\n\n"
                "    def s02(self):\n"
                "        self.clip(\"p2_02\")\n"
                "        self.at(2.0, FadeIn(Circle()))\n\n"
                "    def s03(self):\n"
                "        self.clip(\"p2_03\")\n"
                "        self.at(3.0, FadeIn(Triangle()))\n",
            )
            write(
                root / "pattern_c.py",
                "from manim import *\n\n"
                "def qpanel(items):\n"
                "    return VGroup()\n\n"
                "class Base(Scene):\n"
                "    def construct(self):\n"
                "        self.body()\n\n"
                "class Child(Base):\n"
                "    def body(self):\n"
                "        panel = qpanel([])\n"
                "        self.add(panel)\n",
            )
            write(root / "broken.py", "def broken(:\n    pass\n")

            report = analyzer.build_report(root)
            self.assertIn("AScene", report)
            self.assertIn("প্যাটার্ন A", report)
            self.assertIn("BScene", report)
            self.assertIn("প্যাটার্ন B", report)
            self.assertIn("p2_01", report)
            self.assertIn("C-base", report)
            self.assertIn("C-content", report)
            self.assertIn("broken.py", report)


class CacheReportTest(unittest.TestCase):
    def test_categories_and_archive_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "media/videos/x/partial_movie_files/a.mp4", "x" * 16)
            write(root / "pkg/__pycache__/m.pyc", "x" * 8)
            write(root / "cache/mywork/proj/code.py", "print('archive, do not delete')\n")
            write(root / "cache/voice/big.wav", "x" * 32)

            data = cache_report.build_data(root, limit=10)
            self.assertGreaterEqual(data["counts"].get("strong", 0), 2)
            self.assertGreaterEqual(data["counts"].get("review", 0), 1)
            self.assertGreaterEqual(data["counts"].get("archive_like", 0), 1)
            dirs = {row["dir"] for row in data["candidate_dirs"]}
            self.assertIn("cache", dirs)
            self.assertIn("media", dirs)


class ProjectIndexTest(unittest.TestCase):
    def test_status_summary_and_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "alpha/notes.md",
                "# alpha — টেস্ট\n\n- কী: আলফা প্রজেক্ট\n- Status: ✅\n",
            )
            write(
                root / "alpha/scene.py",
                "from manim import *\n\n"
                "class AlphaScene(Scene):\n"
                "    def construct(self):\n"
                "        self.wait(1)\n",
            )
            write(
                root / "beta/notes.md",
                "# beta\n\n- কী: বিটা প্রজেক্ট\n- Status: 🚧\n",
            )
            write(
                root / "beta/part1.py",
                "from manim import *\n\n"
                "class BetaScene(Scene):\n"
                "    def construct(self):\n"
                "        self.wait(1)\n",
            )

            report = project_index.build_index(root, max_main=2)
            self.assertIn("`alpha`", report)
            self.assertIn("✅ passed", report)
            self.assertIn("আলফা প্রজেক্ট", report)
            self.assertIn("`beta`", report)
            self.assertIn("🚧 চলমান", report)


class RepoHygieneTest(unittest.TestCase):
    def test_all_tools_parse(self) -> None:
        for path in sorted(TOOLS.glob("*.py")):
            with self.subTest(tool=path.name):
                ast.parse(path.read_text(encoding="utf-8"))

    def test_templates_are_valid_json(self) -> None:
        for path in sorted((REPO_ROOT / "templates").glob("*.json")):
            with self.subTest(template=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    def test_entry_links_resolve(self) -> None:
        checked = [REPO_ROOT / "START_HERE.md", REPO_ROOT / "docs/bn/README.md"]
        for md in checked:
            text = md.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                rel = target.strip().split("#")[0]
                if not rel or rel.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(file=str(md.relative_to(REPO_ROOT)), link=target):
                    self.assertTrue((md.parent / rel).resolve().exists())


if __name__ == "__main__":
    unittest.main()
