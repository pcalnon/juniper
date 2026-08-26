#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/2026-08-25_p5_port_memory_budget.py`` -- the P5 porting helper.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the gate.
Hermetic: git history is built in a TemporaryDirectory; nothing reads a sibling repo.

What it pins, and why each mattered:

- ``p90`` is nearest-rank. The floor form ``int(n * 0.9) - 1`` returned the SMALLEST growth
  at n == 2 -- the 2026-08-25 fleet measurement printed p90 < median for four repos. Slack
  sized from that number is under-sized in exactly the direction a ceiling cannot tolerate.
- Growth is measured in CHARACTERS, the unit the ceiling uses, not bytes.
- The rendered job, standalone workflow and budget config parse and carry the figures that
  were MEASURED in the repo, so a port never re-types a number from a note (the first two
  ports found every transcribed figure stale).
- ``insert-job`` lands the block BEFORE ``required-checks`` and outside its ``needs:``
  (plan correction C9), ahead of the anchor job's banner comment.
- ``adapt-test`` rewrites the repo-root depth and adds SPACE-separated ``# nosec`` codes;
  the comma form under-suppresses on bandit 1.9.4 and reads as applied.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "util" / "ad-hoc" / "2026-08-25_p5_port_memory_budget.py"


def _load():
    spec = importlib.util.spec_from_file_location("p5_port_helper", HELPER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


helper = _load()


def _git(repo: Path, *args: str) -> None:
    # A throwaway identity and NO signing: the developer's global commit.gpgsign=true would
    # otherwise reach for a hardware token from inside a unit test.
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _seed_repo(root: Path, contents: list[str]) -> None:
    _git(root, "init", "-q", "-b", "main")
    for i, text in enumerate(contents):
        (root / "AGENTS.md").write_text(text, encoding="utf-8")
        _git(root, "add", "AGENTS.md")
        _git(root, "commit", "-q", "-m", f"c{i}")


_STATS = {
    "repo": "juniper-foo",
    "days": 30,
    "commits": 4,
    "start": 30000,
    "end": 34695,
    "net": 4695,
    "rate": 156.5,
    "grew": 3,
    "shrank": 0,
    "median": 1982,
    "p90": 2582,
    "max": 2582,
}


class StatsTest(unittest.TestCase):
    def test_p90_is_nearest_rank_not_floor(self):
        # n == 2: the floor form returned index 0, the SMALLEST growth.
        st = helper.stats_from_sizes([0, 200, 2000], 30)
        self.assertEqual(st["p90"], 1800)
        self.assertEqual(st["max"], 1800)
        self.assertGreaterEqual(st["p90"], st["median"])
        # n == 3 -> ceil(2.7) = 3rd value.
        st = helper.stats_from_sizes([0, 1, 3, 6], 30)
        self.assertEqual(st["p90"], 3)
        # n == 20 -> ceil(18.0) = 18th value, not the 20th and not the 17th.
        sizes = [0]
        for g in range(1, 21):
            sizes.append(sizes[-1] + g)
        st = helper.stats_from_sizes(sizes, 30)
        self.assertEqual(st["p90"], 18)
        self.assertEqual(st["max"], 20)

    def test_p90_never_below_median_nor_above_max(self):
        for n in range(1, 30):
            sizes = [0]
            for g in range(1, n + 1):
                sizes.append(sizes[-1] + g * 7)
            st = helper.stats_from_sizes(sizes, 30)
            self.assertGreaterEqual(st["p90"], st["median"], n)
            self.assertLessEqual(st["p90"], st["max"], n)

    def test_rate_net_and_counts(self):
        st = helper.stats_from_sizes([100, 50, 250], 30, repo_name="r")
        self.assertEqual(st["net"], 150)
        self.assertAlmostEqual(st["rate"], 5.0)
        self.assertEqual((st["grew"], st["shrank"], st["max"], st["commits"]), (1, 1, 200, 3))
        self.assertEqual(st["repo"], "r")

    def test_no_growing_commits_reports_none_not_zero(self):
        st = helper.stats_from_sizes([300, 200], 30)
        self.assertIsNone(st["max"])
        self.assertIsNone(st["p90"])
        self.assertEqual(st["shrank"], 1)


class GrowthFromGitTest(unittest.TestCase):
    def test_measures_characters_not_bytes(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _seed_repo(root, ["é" * 100, "é" * 300])  # 2 bytes per char in UTF-8
            st = helper.growth_stats(root, 30)
        self.assertIsNotNone(st)
        self.assertEqual((st["start"], st["end"], st["net"]), (100, 300, 200))

    def test_measured_ceiling_is_working_tree_char_count(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("é" * 50 + "x" * 25, encoding="utf-8")
            self.assertEqual(helper.measured_ceiling(root), 75)

    def test_too_few_commits_returns_none(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _seed_repo(root, ["only one"])
            self.assertIsNone(helper.growth_stats(root, 30))

    def test_git_failure_raises_rather_than_reporting_no_growth(self):
        with TemporaryDirectory() as td:
            with self.assertRaises(helper.GrowthError):
                helper.growth_stats(Path(td) / "not-a-repo", 30)


class RenderTest(unittest.TestCase):
    def test_job_block_parses_and_carries_measured_figures(self):
        block = helper.render_job("juniper-foo", "PYTHON_TEST_VERSION", _STATS, ceiling=34695, today="2026-08-25")
        job = yaml.safe_load("jobs:\n" + block)["jobs"]["memory-budget"]
        self.assertEqual(job["name"], "Memory Budget")
        self.assertNotIn("needs", job)
        run = job["steps"][-1]["run"]
        self.assertIn("--advisory", run)
        self.assertIn("--trailers-file memory-budget-trailers.txt", run)
        self.assertIn("--base-ref FETCH_HEAD", run)
        self.assertIn("${{ env.PYTHON_TEST_VERSION }}", job["steps"][1]["with"]["python-version"])
        for figure in ("34,695", "2,582", "1,982", "+4,695", "2026-08-25", "juniper-foo"):
            self.assertIn(figure, block, figure)
        self.assertNotIn("@@", block)
        banner = [ln for ln in block.splitlines() if "Memory File Size Budget (ADVISORY)" in ln and "echo" in ln][0]
        self.assertEqual(len(banner.split('"')[1]), 62)  # 60 inner chars + the two box edges

    def test_job_block_uses_the_targets_own_pins(self):
        with TemporaryDirectory() as td:
            wf = Path(td) / "ci.yml"
            wf.write_text(
                "jobs:\n  x:\n    steps:\n      - uses: actions/checkout@aaaa  # v9.9.9\n      - uses: actions/setup-python@bbbb  # v8.8.8\n",
                encoding="utf-8",
            )
            pins = helper.pins_from(wf)
        self.assertEqual(pins, ("actions/checkout@aaaa  # v9.9.9", "actions/setup-python@bbbb  # v8.8.8"))
        block = helper.render_job("juniper-foo", "PYTHON_VERSION", _STATS, ceiling=1, pins=pins, today="2026-08-25")
        self.assertIn("uses: actions/checkout@aaaa  # v9.9.9", block)
        self.assertIn("uses: actions/setup-python@bbbb  # v8.8.8", block)
        self.assertEqual(helper.pins_from(None), (helper.DEFAULT_CHECKOUT, helper.DEFAULT_SETUP_PYTHON))

    def test_insert_job_lands_before_required_checks_banner_and_outside_needs(self):
        block = helper.render_job("juniper-foo", "PYTHON_TEST_VERSION", _STATS, ceiling=34695, today="2026-08-25")
        with TemporaryDirectory() as td:
            wf = Path(td) / "ci.yml"
            wf.write_text(
                "name: CI\non: [pull_request]\njobs:\n  unit-tests:\n    runs-on: ubuntu-latest\n    steps: []\n\n" "  # ═══════════════\n  # Required Checks Aggregator: Final quality gate\n  # ═══════════════\n" "  required-checks:\n    name: Quality Gate\n    runs-on: ubuntu-latest\n    needs: [unit-tests]\n    steps: []\n",
                encoding="utf-8",
            )
            job_file = Path(td) / "job.yml"
            job_file.write_text(block, encoding="utf-8")
            self.assertEqual(helper.insert_job(wf, job_file, "required-checks"), 0)
            text = wf.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        self.assertEqual(list(data["jobs"]), ["unit-tests", "memory-budget", "required-checks"])
        self.assertEqual(data["jobs"]["required-checks"]["needs"], ["unit-tests"])
        self.assertLess(text.index("memory-budget:"), text.index("# Required Checks Aggregator"))
        self.assertLess(text.index("# Required Checks Aggregator"), text.index("required-checks:"))

    def test_standalone_workflow_parses(self):
        wf = helper.render_workflow("juniper-recurrence", "PYTHON_TEST_VERSION", "3.14", _STATS, ceiling=11578, today="2026-08-25")
        data = yaml.safe_load(wf)
        self.assertEqual(data["name"], "Memory Budget")
        trigger = data.get("on", data.get(True))  # PyYAML reads a bare `on:` key as boolean True
        self.assertIn("pull_request", trigger)
        self.assertEqual(data["env"]["PYTHON_TEST_VERSION"], "3.14")
        self.assertEqual(list(data["jobs"]), ["memory-budget"])
        self.assertEqual(data["jobs"]["memory-budget"]["name"], "Memory Budget")
        self.assertEqual(data["permissions"], {"contents": "read"})
        self.assertIn("11,578", wf)

    def test_config_ceiling_is_the_measured_figure_and_notes_the_destination(self):
        without = json.loads(helper.render_config("juniper-recurrence", _STATS, ceiling=11578, has_reference=False, today="2026-08-25"))
        self.assertEqual(without["files"]["AGENTS.md"]["ceiling_chars"], 11578)
        self.assertIn("NO docs/REFERENCE.md", "\n".join(without["_README"]))
        self.assertIn("2,582", without["files"]["AGENTS.md"]["_note"])
        with_ref = json.loads(helper.render_config("juniper-data", _STATS, ceiling=43493, has_reference=True, today="2026-08-25"))
        self.assertEqual(with_ref["files"]["AGENTS.md"]["ceiling_chars"], 43493)
        self.assertIn("deliberately NOT governed", "\n".join(with_ref["_README"]))
        # Every figure in the README is the measured one, thousands-separated.
        readme = "\n".join(with_ref["_README"])
        for figure in ("30,000 -> 34,695", "+4,695", "~156/day", "largest 2,582", "p90 2,582"):
            self.assertIn(figure, readme, figure)

    def test_render_cli_refuses_a_repo_with_no_agents_md(self):
        with TemporaryDirectory() as td:
            p = subprocess.run(
                [sys.executable, str(HELPER), "render-config", td],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(p.returncode, 2)
        self.assertIn("no AGENTS.md", p.stderr)


class AdaptTest(unittest.TestCase):
    _FIXTURE = "import subprocess\n" "\n" "REPO_ROOT = Path(__file__).resolve().parents[1]\n" "\n" "def _git(repo, *args):\n" "    return subprocess.run(\n" '        ["git", "-C", str(repo), *args],\n' "        check=True,\n" "    )\n" "\n" "def _run(root, budget, *extra):\n" "    return subprocess.run(\n" '        [sys.executable, str(MODULE_PATH), "--repo-root", str(root), "--budget", str(budget), "--base-ref", "HEAD", *extra],\n' "        capture_output=True,\n" "    )\n"

    def test_depth_rewritten_and_nosec_codes_space_separated(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "test_x.py"
            path.write_text(self._FIXTURE, encoding="utf-8")
            self.assertEqual(helper.adapt_test(path, 3), 0)
            text = path.read_text(encoding="utf-8")
        self.assertIn("REPO_ROOT = Path(__file__).resolve().parents[3]", text)
        self.assertNotIn("REPO_ROOT = Path(__file__).resolve().parents[1]", text)
        self.assertIn("one level deeper", text)  # the explanatory note lands with the rewrite
        self.assertIn("subprocess.run(  # nosec B603 B607 - fixed git argv", text)
        self.assertIn("subprocess.run(  # nosec B603 - sys.executable", text)
        self.assertIn("import subprocess  # nosec B404 - subprocess IS the interface under test", text)
        self.assertNotIn("B603,B607", text)
        self.assertEqual(text.count("# nosec"), 3)
        # Idempotent: a second pass adds nothing.
        with TemporaryDirectory() as td:
            path = Path(td) / "test_x.py"
            path.write_text(text, encoding="utf-8")
            self.assertEqual(helper.adapt_test(path, 3), 0)
            self.assertEqual(path.read_text(encoding="utf-8").count("# nosec"), 3)

    def test_same_depth_is_a_no_op_for_the_root_line(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "test_x.py"
            path.write_text(self._FIXTURE, encoding="utf-8")
            self.assertEqual(helper.adapt_test(path, 1), 0)
            text = path.read_text(encoding="utf-8")
        self.assertIn("REPO_ROOT = Path(__file__).resolve().parents[1]", text)
        self.assertNotIn("one level deeper", text)

    def test_missing_root_line_is_an_error(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "test_x.py"
            path.write_text("print('no root line')\n", encoding="utf-8")
            self.assertEqual(helper.adapt_test(path, 2), 2)


class AdaptFlagsTest(unittest.TestCase):
    _HEADER_FIXTURE = '"""\n' "Project:     Juniper\n" "Sub-Project: juniper-ml\n" "Application: tests\n" "Version:     0.1.0\n" "License:     MIT License\n" '"""\n' "\n" "import subprocess\n" "from pathlib import Path\n" "from tempfile import TemporaryDirectory\n" "\n" "REPO_ROOT = Path(__file__).resolve().parents[1]\n"

    def _adapt(self, **kwargs) -> str:
        with TemporaryDirectory() as td:
            path = Path(td) / "test_x.py"
            path.write_text(self._HEADER_FIXTURE, encoding="utf-8")
            self.assertEqual(helper.adapt_test(path, 1, **kwargs), 0)
            return path.read_text(encoding="utf-8")

    def test_sub_project_and_header_version_rewritten(self):
        text = self._adapt(sub_project="juniper-data-client", header_version="0.4.2")
        self.assertIn("Sub-Project: juniper-data-client\n", text)
        self.assertNotIn("juniper-ml", text)
        self.assertIn("Version:     0.4.2\n", text)  # column alignment preserved
        self.assertNotIn("0.1.0", text)

    def test_header_version_none_drops_the_line(self):
        # cascor forbids `Version:` lines repo-wide (BUG-CC-04) -- a test in a DIFFERENT file.
        text = self._adapt(header_version="none")
        self.assertNotIn("Version:", text)
        self.assertIn("Application: tests\nLicense:     MIT License\n", text)

    def test_pytest_marker_inserted_after_stdlib_imports_before_root(self):
        text = self._adapt(pytest_marker="unit")
        self.assertIn("from tempfile import TemporaryDirectory\n\nimport pytest\n", text)
        self.assertIn("pytestmark = pytest.mark.unit\n", text)
        self.assertLess(text.index("pytestmark"), text.index("REPO_ROOT ="))
        self.assertIn("DESELECTED", text)
        # Idempotent: a second pass does not add a second marker.
        with TemporaryDirectory() as td:
            path = Path(td) / "test_x.py"
            path.write_text(text, encoding="utf-8")
            self.assertEqual(helper.adapt_test(path, 1, pytest_marker="unit"), 0)
            self.assertEqual(path.read_text(encoding="utf-8").count("pytestmark"), 1)

    def test_import_nosec_b404_added_once(self):
        text = self._adapt()
        self.assertIn("import subprocess  # nosec B404", text)
        self.assertEqual(text.count("nosec B404"), 1)


class InsertJobGuardTest(unittest.TestCase):
    def test_second_insert_of_the_same_job_is_refused_and_leaves_the_file_unchanged(self):
        block = helper.render_job("juniper-foo", "PYTHON_TEST_VERSION", _STATS, ceiling=1, today="2026-08-25")
        with TemporaryDirectory() as td:
            wf = Path(td) / "ci.yml"
            wf.write_text("jobs:\n  a:\n    steps: []\n\n  required-checks:\n    needs: [a]\n    steps: []\n", encoding="utf-8")
            job_file = Path(td) / "job.yml"
            job_file.write_text(block, encoding="utf-8")
            self.assertEqual(helper.insert_job(wf, job_file, "required-checks"), 0)
            once = wf.read_text(encoding="utf-8")
            self.assertEqual(helper.insert_job(wf, job_file, "required-checks"), 2)
            self.assertEqual(wf.read_text(encoding="utf-8"), once)
        self.assertEqual(once.count("  memory-budget:\n"), 1)


class RepoNameTest(unittest.TestCase):
    def test_name_comes_from_origin_url_not_the_worktree_directory(self):
        with TemporaryDirectory() as td:
            root = Path(td) / "juniper-foo--feat--memory-budget-gate--20260825-1852--deadbeef"
            root.mkdir()
            _git(root, "init", "-q", "-b", "main")
            self.assertEqual(helper.repo_name(root), root.name)  # no remote: directory name
            _git(root, "remote", "add", "origin", "https://github.com/pcalnon/juniper-foo.git")
            self.assertEqual(helper.repo_name(root), "juniper-foo")
            _git(root, "remote", "set-url", "origin", "git@github.com:pcalnon/juniper-bar.git")
            self.assertEqual(helper.repo_name(root), "juniper-bar")


if __name__ == "__main__":
    unittest.main()
