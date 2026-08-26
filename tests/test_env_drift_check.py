"""Dogfood test for the shared ``juniper-env-drift-check`` console script
(``juniper-ci-tools/juniper_ci_tools/cli_env_drift_check.py``; test-suite audit
plan §10.1).

This is the integration gate for that tool inside juniper-ml: ``juniper-ci-tools/``
is a sub-module outside this repo's flake8 / pre-commit scope, so a wired unittest
is what actually gates it on every PR (the same discipline as
``tests/test_ci_tools_drift.py`` and ``tests/test_env_floor_drift_check.py``).

It exercises the **shipped** module end-to-end as a subprocess
(``python -m juniper_ci_tools.cli_env_drift_check``, with the ci-tools package on
``PYTHONPATH``) against synthetic fixtures — a ``pyproject.toml`` with juniper-*
floors, a synthetic ``site-packages`` populated with ``*.dist-info/METADATA``, and
a ``requirements.lock`` — so no real pip / conda is touched. It asserts:

* exit 0 when the scanned env satisfies the floors;
* exit 1 (drift) when an installed juniper-* wheel is below its floor, and that
  the offending dist is named;
* a **plain wheel** below its floor is flagged identically to an editable install
  (the gap ``util/editable_install_drift_check.py`` misses — the 2026-06-26
  canopy incident class);
* ``--check-lock`` exits 1 when a lock pin is below a floor, 0 when consistent;
* exit 2 on usage errors (no pyproject / no juniper floors);
* the ``--json`` payload shape.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.redacted_env import RedactedEnv


def _ci_tools_pkg_root(juniper_ml_root: Path) -> Path | None:
    """Directory to put on PYTHONPATH so ``juniper_ci_tools`` imports (the
    ``juniper-ci-tools/`` sub-package dir). None if not present in this checkout.
    """
    candidate = juniper_ml_root / "juniper-ci-tools"
    if (candidate / "juniper_ci_tools" / "cli_env_drift_check.py").is_file():
        return candidate
    return None


def _make_dist_info(site_dir: Path, name: str, version: str, *, editable: bool = False) -> None:
    dist_info = site_dir / f"{name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n", encoding="utf-8")
    if editable:
        (dist_info / "direct_url.json").write_text(json.dumps({"url": "file:///src/" + name, "dir_info": {"editable": True}}), encoding="utf-8")


def _write_pyproject(repo: Path, deps: list[str]) -> None:
    body = '[project]\nname = "synthetic-repo"\nversion = "1.0.0"\ndependencies = [\n'
    body += "".join(f'    "{d}",\n' for d in deps)
    body += "]\n"
    (repo / "pyproject.toml").write_text(body, encoding="utf-8")


class EnvDriftCheckDogfoodTest(unittest.TestCase):
    # Declared at class scope so mypy sees the attributes set in setUpClass
    # (the typed _run method below reads them).
    juniper_ml_root: Path
    pkg_root: Path | None
    have_packaging: bool

    @classmethod
    def setUpClass(cls):
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.pkg_root = _ci_tools_pkg_root(cls.juniper_ml_root)
        cls.have_packaging = importlib.util.find_spec("packaging") is not None

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:
        if self.pkg_root is None:
            self.skipTest("juniper-ci-tools/ not present in this checkout")
        if not self.have_packaging:
            self.skipTest("packaging not importable in the test interpreter")
        env = RedactedEnv(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(self.pkg_root), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        return subprocess.run(
            [sys.executable, "-m", "juniper_ci_tools.cli_env_drift_check", *args],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_help_exits_zero(self):
        proc = self._run(["--help"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("juniper-env-drift-check", proc.stdout)

    def test_satisfying_env_exits_zero(self):
        with TemporaryDirectory() as repo, TemporaryDirectory() as sp:
            _write_pyproject(Path(repo), ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")
            proc = self._run(["--repo-root", repo, "--site-packages", sp])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("RESULT: OK", proc.stdout)

    def test_below_floor_exits_one_and_names_dist(self):
        with TemporaryDirectory() as repo, TemporaryDirectory() as sp:
            _write_pyproject(Path(repo), ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.0")
            proc = self._run(["--repo-root", repo, "--site-packages", sp])
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertIn("juniper-data-client", proc.stdout)
            self.assertIn("0.4.0", proc.stdout)
            self.assertIn("BELOW_FLOOR", proc.stdout)

    def test_plain_wheel_treated_identically_to_editable(self):
        # The closed gap: a plain wheel below its floor is flagged exactly as an
        # editable install would be (importlib.metadata is install-type-agnostic).
        results = {}
        for editable in (False, True):
            with TemporaryDirectory() as repo, TemporaryDirectory() as sp:
                _write_pyproject(Path(repo), ["juniper-cascor-client>=0.5.0"])
                _make_dist_info(Path(sp), "juniper-cascor-client", "0.3.0", editable=editable)
                proc = self._run(["--repo-root", repo, "--site-packages", sp])
                results[editable] = proc.returncode
        self.assertEqual(results, {False: 1, True: 1})

    def test_check_lock_below_exits_one_consistent_zero(self):
        # Lock pin below floor -> exit 1.
        with TemporaryDirectory() as repo, TemporaryDirectory() as sp:
            _write_pyproject(Path(repo), ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")  # env OK
            (Path(repo) / "requirements.lock").write_text("juniper-data-client==0.4.0\n", encoding="utf-8")
            proc = self._run(["--repo-root", repo, "--site-packages", sp, "--check-lock"])
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertIn("requirements.lock", proc.stdout)
        # Consistent lock -> exit 0.
        with TemporaryDirectory() as repo, TemporaryDirectory() as sp:
            _write_pyproject(Path(repo), ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")
            (Path(repo) / "requirements.lock").write_text("juniper-data-client==0.4.1\n", encoding="utf-8")
            proc = self._run(["--repo-root", repo, "--site-packages", sp, "--check-lock"])
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_json_payload_shape(self):
        with TemporaryDirectory() as repo, TemporaryDirectory() as sp:
            _write_pyproject(Path(repo), ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.0")
            proc = self._run(["--repo-root", repo, "--site-packages", sp, "--json"])
            self.assertEqual(proc.returncode, 1, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["findings"][0]["name"], "juniper-data-client")
            self.assertEqual(payload["findings"][0]["status"], "BELOW_FLOOR")
            self.assertIn("summary", payload)

    def test_usage_error_no_pyproject_exits_two(self):
        with TemporaryDirectory() as repo:
            proc = self._run(["--repo-root", repo])
            self.assertEqual(proc.returncode, 2)
            self.assertIn("pyproject.toml", proc.stderr)

    def test_usage_error_no_juniper_floors_exits_two(self):
        with TemporaryDirectory() as repo:
            _write_pyproject(Path(repo), ["requests>=2.0"])
            proc = self._run(["--repo-root", repo])
            self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
