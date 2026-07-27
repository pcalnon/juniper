#!/usr/bin/env python3
"""Regression tests for util/editable_install_drift_check.py.

Builds a synthetic conda directory (envs/<E>/lib/pythonX/site-packages with
``*.dist-info/direct_url.json`` files) plus a synthetic ecosystem root, then
asserts classification, environment selection, exit codes, JSON output, and the
``--fix`` plan. ``--dry-run`` covers the plan shape; live ``run_fix`` is
exercised with a mocked ``subprocess.run`` so no real ``pip`` is invoked.

Run: python3 -m unittest -v tests/test_editable_install_drift_check.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-06-16
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

UTIL_DIR = Path(__file__).resolve().parents[1] / "util"
sys.path.insert(0, str(UTIL_DIR))

import editable_install_drift_check as mod  # noqa: E402


def write_editable(site_pkgs: Path, dist_name: str, target: str, *, version: str = "1.0.0", editable: bool = True) -> None:
    """Create a <dist>-<ver>.dist-info with a direct_url.json in site_pkgs."""
    dist_info = site_pkgs / f"{dist_name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {dist_name}\nVersion: {version}\n\nbody\n")
    (dist_info / "direct_url.json").write_text(
        json.dumps(
            {
                "url": f"file://{target}",
                "dir_info": {"editable": editable},
            }
        )
    )


class DriftCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.conda = self.root / "conda"
        self.eco = self.root / "Juniper"

        # Canonical (non-worktree) source repo that EXISTS.
        self.canonical = self.eco / "juniper-data"
        self.canonical.mkdir(parents=True)
        (self.canonical / "pyproject.toml").write_text('[project]\nname = "juniper-data"\nversion = "0.6.0"\n')
        # A worktree dir that EXISTS -> WORKTREE_PINNED.
        self.worktree_live = self.eco / "worktrees" / "wt-a" / "juniper-cascor-client"
        self.worktree_live.mkdir(parents=True)
        # Paths that DO NOT exist -> ORPHANED.
        self.gone_worktree = self.eco / "worktrees" / "gone" / "juniper-canopy"
        self.gone_plain = self.eco / "deleted-juniper-data-client"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def site_packages(self, env: str, py: str = "python3.13") -> Path:
        sp = self.conda / "envs" / env / "lib" / py / "site-packages"
        sp.mkdir(parents=True, exist_ok=True)
        return sp

    def run_main(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = mod.main(["--conda-dir", str(self.conda), "--ecosystem-root", str(self.eco), *argv])
        return code, buf.getvalue()

    # ── classify ────────────────────────────────────────────────────────────

    def test_classify_fresh_pinned_orphaned(self) -> None:
        self.assertEqual(mod.classify(str(self.canonical))[0], mod.STATUS_FRESH)
        self.assertEqual(mod.classify(str(self.worktree_live))[0], mod.STATUS_WORKTREE)
        self.assertEqual(mod.classify(str(self.gone_plain))[0], mod.STATUS_ORPHANED)
        # A missing path that lives under a worktree is ORPHANED, not pinned.
        self.assertEqual(mod.classify(str(self.gone_worktree))[0], mod.STATUS_ORPHANED)

    # ── collect ─────────────────────────────────────────────────────────────

    def test_collect_classifies_each_install(self) -> None:
        sp = self.site_packages("JuniperX")
        write_editable(sp, "juniper-data", str(self.canonical))
        write_editable(sp, "juniper-cascor-client", str(self.worktree_live))
        write_editable(sp, "juniper-canopy", str(self.gone_worktree))
        write_editable(sp, "juniper-data-client", str(self.gone_plain))

        findings = mod.collect(self.conda, None)
        by_pkg = {f.package: f.status for f in findings}
        self.assertEqual(
            by_pkg,
            {
                "juniper-data": mod.STATUS_FRESH,
                "juniper-cascor-client": mod.STATUS_WORKTREE,
                "juniper-canopy": mod.STATUS_ORPHANED,
                "juniper-data-client": mod.STATUS_ORPHANED,
            },
        )

    def test_non_juniper_and_non_editable_ignored(self) -> None:
        sp = self.site_packages("JuniperX")
        write_editable(sp, "requests", str(self.canonical))  # not juniper
        write_editable(sp, "juniper-data", str(self.canonical), editable=False)  # wheel
        self.assertEqual(mod.collect(self.conda, None), [])

    def test_dedup_across_site_packages(self) -> None:
        # Same package editable in two interpreter trees -> reported once.
        write_editable(self.site_packages("JuniperX", "python3.13"), "juniper-data", str(self.canonical))
        write_editable(self.site_packages("JuniperX", "python3.14t"), "juniper-data", str(self.canonical))
        findings = [f for f in mod.collect(self.conda, None) if f.env == "JuniperX"]
        self.assertEqual(len(findings), 1)

    # ── environment selection ────────────────────────────────────────────────

    def test_deprecated_excluded_by_default_included_with_flag(self) -> None:
        write_editable(self.site_packages("JuniperLive"), "juniper-data", str(self.canonical))
        write_editable(self.site_packages("JuniperOld-DEPRECATED"), "juniper-canopy", str(self.gone_plain))
        default_envs = {f.env for f in mod.collect(self.conda, None)}
        self.assertEqual(default_envs, {"JuniperLive"})
        all_envs = {f.env for f in mod.collect(self.conda, None, include_deprecated=True)}
        self.assertEqual(all_envs, {"JuniperLive", "JuniperOld-DEPRECATED"})

    def test_env_filter_overrides_glob_and_deprecation(self) -> None:
        write_editable(self.site_packages("JuniperOld-DEPRECATED"), "juniper-data", str(self.canonical))
        # Explicit --env selects it even though it is deprecated.
        findings = mod.collect(self.conda, ["JuniperOld-DEPRECATED"])
        self.assertEqual([f.env for f in findings], ["JuniperOld-DEPRECATED"])

    # ── exit codes + JSON ─────────────────────────────────────────────────────

    def test_exit_zero_when_only_fresh_and_pinned(self) -> None:
        sp = self.site_packages("JuniperX")
        write_editable(sp, "juniper-data", str(self.canonical))
        write_editable(sp, "juniper-cascor-client", str(self.worktree_live))
        code, _ = self.run_main()
        self.assertEqual(code, 0)

    def test_strict_fails_on_worktree_pinned(self) -> None:
        write_editable(self.site_packages("JuniperX"), "juniper-cascor-client", str(self.worktree_live))
        self.assertEqual(self.run_main()[0], 0)
        self.assertEqual(self.run_main("--strict")[0], 1)

    def test_exit_one_on_orphaned(self) -> None:
        write_editable(self.site_packages("JuniperX"), "juniper-canopy", str(self.gone_plain))
        self.assertEqual(self.run_main()[0], 1)

    def test_exit_two_when_no_envs(self) -> None:
        # Fresh conda dir with no envs/ at all.
        code, _ = self.run_main()
        self.assertEqual(code, 2)

    def test_json_output_shape(self) -> None:
        write_editable(self.site_packages("JuniperX"), "juniper-data", str(self.canonical))
        code, out = self.run_main("--json")
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(payload["findings"][0]["package"], "juniper-data")
        self.assertEqual(payload["findings"][0]["status"], mod.STATUS_FRESH)

    # ── canonical discovery + fix plan ────────────────────────────────────────

    def test_discover_canonical_unique(self) -> None:
        found, candidates = mod.discover_canonical("juniper-data", self.eco)
        self.assertEqual(found, self.canonical)
        self.assertEqual(candidates, [self.canonical])

    def test_discover_canonical_skips_worktrees(self) -> None:
        # A worktree copy with a matching pyproject must NOT be treated as canonical.
        wt_pkg = self.eco / "worktrees" / "wt-b" / "juniper-thing"
        wt_pkg.mkdir(parents=True)
        (wt_pkg / "pyproject.toml").write_text('[project]\nname = "juniper-thing"\n')
        found, candidates = mod.discover_canonical("juniper-thing", self.eco)
        self.assertIsNone(found)
        self.assertEqual(candidates, [])

    def test_fix_dry_run_resolves_orphan_to_canonical(self) -> None:
        write_editable(self.site_packages("JuniperX"), "juniper-data", str(self.gone_plain))
        code, out = self.run_main("--fix", "--dry-run", "--json")
        payload = json.loads(out)
        fix = payload["fix"]
        self.assertEqual(len(fix), 1)
        self.assertEqual(fix[0]["action"], "DRY_RUN")
        self.assertEqual(fix[0]["canonical"], str(self.canonical))
        self.assertIn("--force-reinstall", fix[0]["cmd"])
        # dry-run never repairs, so the orphan remains -> exit 1.
        self.assertEqual(code, 1)

    def test_fix_skips_when_canonical_unresolvable(self) -> None:
        # juniper-canopy has no pyproject under the ecosystem root here.
        write_editable(self.site_packages("JuniperX"), "juniper-canopy", str(self.gone_plain))
        _, out = self.run_main("--fix", "--dry-run", "--json")
        fix = json.loads(out)["fix"]
        self.assertEqual(fix[0]["action"], "SKIP")
        self.assertFalse(fix[0]["resolvable"])

    # ── run_fix live (non-dry) execution — mocked pip only ──────────────────

    def _resolvable_plan(self) -> list[dict]:
        return [
            {
                "env": "JuniperX",
                "package": "juniper-data",
                "from": str(self.gone_plain),
                "canonical": str(self.canonical),
                "candidates": [str(self.canonical)],
                "resolvable": True,
            }
        ]

    def test_run_fix_executes_and_reports_fixed(self) -> None:
        """Non-dry run_fix must invoke pip and mark FIXED on success.

        Prior suite only covered --fix --dry-run (DRY_RUN / SKIP). The live
        mutation path is the only branch that re-points orphaned editables.
        """
        plan = self._resolvable_plan()
        with mock.patch.object(mod.subprocess, "run", return_value=mock.Mock()) as run:
            results = mod.run_fix(plan, self.conda, dry_run=False)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["action"], "FIXED")
        self.assertNotIn("error", results[0])
        run.assert_called_once()
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[0], str(mod.env_python(self.conda, "JuniperX")))
        self.assertEqual(cmd[1:5], ["-m", "pip", "install", "-e"])
        self.assertEqual(cmd[5], str(self.canonical))
        self.assertIn("--force-reinstall", cmd)
        self.assertTrue(run.call_args.kwargs.get("check"))

    def test_run_fix_reports_called_process_error(self) -> None:
        """pip failure must become action=ERROR with truncated stderr, not raise."""
        plan = self._resolvable_plan()
        exc = subprocess.CalledProcessError(1, ["pip"], stderr="Could not find a version that satisfies the requirement\n")
        with mock.patch.object(mod.subprocess, "run", side_effect=exc):
            results = mod.run_fix(plan, self.conda, dry_run=False)

        self.assertEqual(results[0]["action"], "ERROR")
        self.assertIn("Could not find a version", results[0]["error"])
        self.assertEqual(results[0]["canonical"], str(self.canonical))

    def test_run_fix_reports_oserror(self) -> None:
        """Missing env python (OSError) must become ERROR, not abort the plan."""
        plan = self._resolvable_plan() + [
            {
                "env": "JuniperY",
                "package": "juniper-data",
                "from": str(self.gone_plain),
                "canonical": str(self.canonical),
                "candidates": [str(self.canonical)],
                "resolvable": True,
            }
        ]
        with mock.patch.object(
            mod.subprocess,
            "run",
            side_effect=[FileNotFoundError("python missing"), mock.Mock()],
        ):
            results = mod.run_fix(plan, self.conda, dry_run=False)

        self.assertEqual([r["action"] for r in results], ["ERROR", "FIXED"])
        self.assertIn("python missing", results[0]["error"])


if __name__ == "__main__":
    unittest.main()
