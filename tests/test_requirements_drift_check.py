"""Regression tests for util/requirements_drift_check.py.

Covers ``--mode quick``: structural validation of (path, line_start, line_end)
triples in a synthetic id_assignments.yaml fixture. See the tool's docstring
and notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md §7 for the spec.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml  # type: ignore[import-untyped]


def _load_drift_module():
    module_path = Path(__file__).resolve().parent.parent / "util" / "requirements_drift_check.py"
    spec = importlib.util.spec_from_file_location("requirements_drift_check", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load requirements_drift_check module")
    module = importlib.util.module_from_spec(spec)
    # Python 3.13's dataclass introspection consults sys.modules[__module__],
    # which fails unless the module is registered before exec_module runs.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drift = _load_drift_module()


def _entry(eid: str, sources: list[dict]) -> dict:
    return {
        "id": eid,
        "owner": "ml",
        "category": "DOC",
        "status": "proposed",
        "priority": "P3",
        "brief": "test entry",
        "merged_count": 1,
        "notes": None,
        "sources": sources,
    }


def _write_yaml(path: Path, entries: list[dict]) -> None:
    path.write_text(yaml.safe_dump(entries), encoding="utf-8")


class ValidateRangeTests(unittest.TestCase):
    """drift.validate_range structural checks."""

    def test_valid_range_returns_none(self):
        self.assertIsNone(drift.validate_range(1, 1))
        self.assertIsNone(drift.validate_range(10, 100))

    def test_missing_endpoints_flagged(self):
        self.assertIsNotNone(drift.validate_range(None, 5))
        self.assertIsNotNone(drift.validate_range(5, None))
        self.assertIsNotNone(drift.validate_range(None, None))

    def test_non_integer_flagged(self):
        self.assertIsNotNone(drift.validate_range("1", 10))
        self.assertIsNotNone(drift.validate_range(1, "10"))
        self.assertIsNotNone(drift.validate_range(1.5, 10))

    def test_bool_not_treated_as_int(self):
        # bool is an int subclass; we explicitly reject it to catch YAML-parser
        # quirks where 'yes'/'no' could land as bool.
        self.assertIsNotNone(drift.validate_range(True, 10))
        self.assertIsNotNone(drift.validate_range(1, False))

    def test_zero_or_negative_start_flagged(self):
        self.assertIsNotNone(drift.validate_range(0, 10))
        self.assertIsNotNone(drift.validate_range(-5, 10))

    def test_end_before_start_flagged(self):
        self.assertIsNotNone(drift.validate_range(50, 10))


class CheckQuickFixtureTests(unittest.TestCase):
    """End-to-end check_quick against a synthetic snapshot."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.existing_file = self.root / "doc.md"
        self.existing_file.write_text("line1\nline2\nline3\n", encoding="utf-8")
        self.addCleanup(self.tmp.cleanup)

    def _check(self, entries):
        return drift.check_quick(entries, ecosystem_root=None)

    def test_valid_entry_is_ok(self):
        findings = self._check(
            [
                _entry(
                    "JR-ML-DOC-001",
                    [{"path": str(self.existing_file), "line_start": 1, "line_end": 3}],
                )
            ]
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "OK")

    def test_missing_path_is_bad_path(self):
        findings = self._check(
            [
                _entry(
                    "JR-ML-DOC-002",
                    [{"path": str(self.root / "missing.md"), "line_start": 1, "line_end": 3}],
                )
            ]
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "BAD_PATH")
        self.assertIn("file not found", findings[0].detail)

    def test_empty_path_is_bad_path(self):
        findings = self._check([_entry("JR-ML-DOC-003", [{"path": "", "line_start": 1, "line_end": 3}])])
        self.assertEqual(findings[0].category, "BAD_PATH")
        self.assertIn("empty", findings[0].detail)

    def test_bad_range_short_circuits_path_check(self):
        # Even with a non-existent path, BAD_RANGE wins so the user fixes the
        # easier structural defect first.
        findings = self._check(
            [
                _entry(
                    "JR-ML-DOC-004",
                    [
                        {
                            "path": str(self.root / "missing.md"),
                            "line_start": 10,
                            "line_end": 5,
                        }
                    ],
                )
            ]
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "BAD_RANGE")

    def test_missing_line_end_is_bad_range(self):
        findings = self._check(
            [
                _entry(
                    "JR-ML-DOC-005",
                    [{"path": str(self.existing_file), "line_start": 1, "line_end": None}],
                )
            ]
        )
        self.assertEqual(findings[0].category, "BAD_RANGE")

    def test_multiple_sources_per_entry(self):
        findings = self._check(
            [
                _entry(
                    "JR-ML-DOC-006",
                    [
                        {"path": str(self.existing_file), "line_start": 1, "line_end": 3},
                        {"path": str(self.root / "ghost.md"), "line_start": 1, "line_end": 3},
                    ],
                )
            ]
        )
        cats = sorted(f.category for f in findings)
        self.assertEqual(cats, ["BAD_PATH", "OK"])

    def test_entry_without_sources_emits_no_findings(self):
        findings = self._check(
            [
                {
                    "id": "JR-ML-DOC-007",
                    "owner": "ml",
                    "category": "DOC",
                    "status": "proposed",
                    "priority": "P3",
                    "brief": "no sources",
                    "merged_count": 1,
                    "notes": None,
                    "sources": [],
                }
            ]
        )
        self.assertEqual(findings, [])


class EcosystemRootRewriteTests(unittest.TestCase):
    """--ecosystem-root translates absolute paths to a different checkout."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Create a fake juniper-ml/notes/foo.md under the override root.
        target = self.root / "juniper-ml" / "notes" / "foo.md"
        target.parent.mkdir(parents=True)
        target.write_text("body\n", encoding="utf-8")
        self.target = target
        self.addCleanup(self.tmp.cleanup)

    def test_rewrite_resolves_path_to_new_root(self):
        snapshot_path = f"{drift.SNAPSHOT_ECOSYSTEM_ROOT}/juniper-ml/notes/foo.md"
        rewritten = drift.rewrite_path(snapshot_path, self.root)
        self.assertEqual(rewritten, str(self.target))

    def test_rewrite_passes_through_unrelated_paths(self):
        unrelated = "/some/other/place/file.md"
        self.assertEqual(drift.rewrite_path(unrelated, self.root), unrelated)

    def test_rewrite_noop_when_no_root_given(self):
        path = f"{drift.SNAPSHOT_ECOSYSTEM_ROOT}/juniper-ml/notes/foo.md"
        self.assertEqual(drift.rewrite_path(path, None), path)

    def test_check_quick_honours_ecosystem_root(self):
        snapshot_path = f"{drift.SNAPSHOT_ECOSYSTEM_ROOT}/juniper-ml/notes/foo.md"
        entries = [_entry("JR-ML-DOC-008", [{"path": snapshot_path, "line_start": 1, "line_end": 1}])]
        findings = drift.check_quick(entries, ecosystem_root=self.root)
        self.assertEqual(findings[0].category, "OK")


class MainCLITests(unittest.TestCase):
    """End-to-end exit code + output behaviour."""

    def _run_main(self, argv, capture_stdout=True):
        buf = io.StringIO() if capture_stdout else None
        if buf is not None:
            with redirect_stdout(buf):
                code = drift.main(argv)
            return code, buf.getvalue()
        return drift.main(argv), ""

    def _write_fixture(self, tmpdir: Path, entries: list[dict]) -> Path:
        yaml_path = tmpdir / "id_assignments.yaml"
        _write_yaml(yaml_path, entries)
        return yaml_path

    def test_returns_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            (tmp / "real.md").write_text("x\n", encoding="utf-8")
            yaml_path = self._write_fixture(
                tmp,
                [
                    _entry(
                        "JR-ML-DOC-100",
                        [{"path": str(tmp / "real.md"), "line_start": 1, "line_end": 1}],
                    )
                ],
            )
            code, out = self._run_main(["--yaml", str(yaml_path), "--quiet"])
            self.assertEqual(code, 0)
            self.assertIn("OK:        1", out)

    def test_returns_one_when_drift_present(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            yaml_path = self._write_fixture(
                tmp,
                [
                    _entry(
                        "JR-ML-DOC-101",
                        [{"path": str(tmp / "missing.md"), "line_start": 1, "line_end": 1}],
                    )
                ],
            )
            code, out = self._run_main(["--yaml", str(yaml_path), "--quiet"])
            self.assertEqual(code, 1)
            self.assertIn("BAD_PATH:  1", out)

    def test_returns_two_when_yaml_missing(self):
        code, _ = self._run_main(["--yaml", "/nonexistent/path/id_assignments.yaml"])
        self.assertEqual(code, 2)

    def test_returns_two_for_unimplemented_mode(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            yaml_path = self._write_fixture(tmp, [])
            code, _ = self._run_main(["--yaml", str(yaml_path), "--mode", "full"])
            self.assertEqual(code, 2)

    def test_json_output_is_well_formed(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            yaml_path = self._write_fixture(
                tmp,
                [
                    _entry(
                        "JR-ML-DOC-102",
                        [{"path": str(tmp / "missing.md"), "line_start": 1, "line_end": 1}],
                    )
                ],
            )
            _, out = self._run_main(["--yaml", str(yaml_path), "--json"])
            payload = json.loads(out)
            self.assertEqual(payload["mode"], "quick")
            self.assertEqual(payload["totals"]["bad_path"], 1)
            self.assertEqual(payload["findings"][0]["category"], "BAD_PATH")


if __name__ == "__main__":
    unittest.main()
