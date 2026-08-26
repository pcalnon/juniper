#!/usr/bin/env python3
"""Every `tests/test_*.py` must be INVOKED by ci.yml's regression job.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

juniper-ml's CI runs an explicit hand-written list of suites -- there is no discovery --
so a new `tests/test_*.py` is not gated merely by existing. The list and the directory
drift silently, and a suite that never runs is indistinguishable from one that passes.

Observed twice in two days:

- ml#1254: `test_snapshot_index.py` shipped in ml#1238 unwired (60 tests, zero enforcement).
- ml#1259: three more found by sweep -- `test_safe_merge.py` (72 tests, guarding
  `util/safe_merge.py`, the ONLY sanctioned path to `main`), `test_subpackage_py_typed.py`
  (the gate for the ml#1237 py.typed fix), and `test_requirements_consolidate.py`. All
  passed unmodified; they had simply never run.

Both were fixed instance-by-instance. This closes the class.

**Why a substring search is not enough -- and is itself the bug.** The regression step is a
single `run: |` block scalar, so its `#` lines are literal string content, not YAML comments.
A naive `"test_foo.py" in ci_yaml` therefore matches a suite that is only *mentioned* in an
explanatory comment and never invoked -- reporting a wired suite when nothing runs. That is
the exact vacuous-pass shape this file exists to prevent, so the extractor skips comment
lines and requires a real `-m unittest` invocation. Two negative controls pin it.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

# `python3 -m unittest -v tests/test_foo.py` -- capture the suite's basename.
_TEST_PATH = re.compile(r"(?<![A-Za-z0-9_./-])tests/(test_[A-Za-z0-9_]+\.py)\b")

_JOB = "tests"
_STEP = "Run Python regression tests"


def _repo_root() -> Path:
    """Walk up to the directory containing .github/workflows/ (location-agnostic)."""
    for candidate in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if (candidate / ".github" / "workflows").is_dir():
            return candidate
    raise AssertionError("could not locate repo root (no .github/workflows/ in any ancestor)")


def _regression_run_script(ci_yaml_text: str) -> str:
    """The regression step's shell script.

    Raises rather than returning "" on a rename: an empty script would make every suite
    look unwired, which is loud -- but a rename should name itself, not present as 96
    simultaneous drift failures.
    """
    parsed = yaml.safe_load(ci_yaml_text)
    jobs = parsed.get("jobs") or {}
    if _JOB not in jobs:
        raise AssertionError(f"ci.yml has no {_JOB!r} job (renamed?); this gate needs updating")
    for step in jobs[_JOB].get("steps") or []:
        if step.get("name") == _STEP:
            return step.get("run") or ""
    raise AssertionError(f"ci.yml {_JOB!r} job has no {_STEP!r} step (renamed?)")


def _invoked_suites(run_script: str) -> list[str]:
    """Suites ACTUALLY INVOKED. Comment lines do not count; duplicates are preserved."""
    found: list[str] = []
    for raw in run_script.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Drop any trailing shell comment so a path named there cannot smuggle a suite in.
        line = re.split(r"\s#", line, maxsplit=1)[0]
        if "-m unittest" not in line:
            continue
        found.extend(_TEST_PATH.findall(line))
    return found


class CiTestWiringDriftTest(unittest.TestCase):
    """The gate: tests/ and ci.yml's invocation list must agree exactly."""

    @classmethod
    def setUpClass(cls):
        cls.root = _repo_root()
        cls.ci = (cls.root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        cls.script = _regression_run_script(cls.ci)
        cls.invoked = _invoked_suites(cls.script)
        cls.on_disk = sorted(p.name for p in (cls.root / "tests").glob("test_*.py"))

    def test_the_extraction_found_something(self):
        """Guard the guard: 0 invocations would make every other assertion meaningless."""
        self.assertGreater(len(self.invoked), 50, "extracted almost no invocations -- the extractor is broken, " "not the wiring. Every other assertion in this file would be vacuous.")

    def test_every_suite_on_disk_is_invoked_by_ci(self):
        missing = sorted(set(self.on_disk) - set(self.invoked))
        self.assertEqual(
            missing,
            [],
            "test suites exist in tests/ but are NEVER RUN by ci.yml:\n" + "\n".join(f"  {m}" for m in missing) + "\n\nA suite that never runs is indistinguishable from one that passes " "(ml#1254, ml#1259). Add `python3 -m unittest -v tests/<name>` to the " f"{_STEP!r} step -- and any third-party import to 'Install test dependencies', " "which installs an explicit short list and fails at collection otherwise.",
        )

    def test_ci_does_not_invoke_a_suite_that_does_not_exist(self):
        phantom = sorted(set(self.invoked) - set(self.on_disk))
        self.assertEqual(
            phantom,
            [],
            "ci.yml invokes test suites that do not exist:\n" + "\n".join(f"  {p}" for p in phantom) + "\n\nEither restore the file or drop the invocation.",
        )

    def test_no_suite_is_invoked_twice(self):
        dupes = sorted({s for s in self.invoked if self.invoked.count(s) > 1})
        self.assertEqual(dupes, [], f"invoked more than once (wasted CI time; often a bad merge): {dupes}")


class ExtractorTest(unittest.TestCase):
    """Negative controls. A gate that cannot fail is not a gate."""

    def test_recognises_the_repo_invocation_form(self):
        self.assertEqual(
            _invoked_suites("          python3 -m unittest -v tests/test_foo.py\n"),
            ["test_foo.py"],
        )

    def test_a_comment_only_mention_is_NOT_counted_as_wired(self):
        """The failure this whole file guards: `#` lines are string content, not YAML comments."""
        script = "          # tests/test_ghost.py: pins the widget contract, see ml#1\n" "          python3 -m unittest -v tests/test_real.py\n"
        found = _invoked_suites(script)
        self.assertEqual(found, ["test_real.py"])
        self.assertNotIn("test_ghost.py", found, "a comment is not an invocation")

    def test_a_trailing_comment_cannot_smuggle_a_suite(self):
        script = "          python3 -m unittest -v tests/test_real.py  # also tests/test_ghost.py\n"
        self.assertEqual(_invoked_suites(script), ["test_real.py"])

    def test_a_bare_path_without_unittest_is_not_an_invocation(self):
        self.assertEqual(_invoked_suites("          cp tests/test_foo.py /tmp/\n"), [])

    def test_duplicates_are_preserved_for_the_duplicate_check(self):
        script = "          python3 -m unittest -v tests/test_a.py\n" "          python3 -m unittest -v tests/test_a.py\n"
        self.assertEqual(_invoked_suites(script), ["test_a.py", "test_a.py"])


class WorkflowShapeTest(unittest.TestCase):
    """A rename must name itself rather than surface as 96 drift failures."""

    def test_missing_job_raises_a_named_error(self):
        with self.assertRaises(AssertionError) as ctx:
            _regression_run_script("jobs:\n  other:\n    steps: []\n")
        self.assertIn(_JOB, str(ctx.exception))

    def test_missing_step_raises_a_named_error(self):
        with self.assertRaises(AssertionError) as ctx:
            _regression_run_script(f"jobs:\n  {_JOB}:\n    steps:\n      - name: Something Else\n")
        self.assertIn(_STEP, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
