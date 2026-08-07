#!/usr/bin/env python3
"""Structural + hermetic YAML-extraction gate for shared-package publish-*.yml workflows.

The six in-repo shared packages each ship via ``.github/workflows/publish-<pkg>.yml``
(juniper-ci-tools / config-tools / doc-tools / model-core / observability /
service-core). These are distinct from the meta-package ``publish.yml`` (covered by
``tests/test_publish_testpypi_verify.py`` once that lands) and carry contracts that
have already bitten in production:

  * **#555 double-publish race** — subscribing to both ``release: published`` and
    ``push: tags`` fired two concurrent runs that raced the immutable TestPyPI
    upload. Sibling workflows must stay release-only (+ ``workflow_dispatch``).
  * **Wrong-package Release fire** — a ``release: published`` for any package fires
    every release-triggered workflow; the build job's tag-prefix ``if`` must keep
    other packages' Releases from publishing this one.
  * **--no-deps + PyPI fallback squatting** — with ``--no-deps``, an
    ``--extra-index-url https://pypi.org/simple/`` only risks resolving a squatted
    *target* package on production PyPI during TestPyPI index lag. Sibling verify
    steps must install from TestPyPI only (companion to
    ``tests/test_workflow_script_paths.py``'s no-deps+extra-index lint).
  * **skip-existing** — residual overlap (manual dispatch during a release) must
    be a no-op, not an immutable-upload 400.
  * **subdirectory build** — ``working-directory`` + artifact path under the
    package dir so a root-level build cannot ship the wrong package.

This unittest:
  1. Structurally pins the shared contracts across all six ``publish-*.yml`` files.
  2. Extracts each Verify-install shell and runs it hermetically with PATH stubs
     for ``sleep`` / ``pip`` / ``python`` (+ console-script stubs where needed) so
     a rewrite that drops ``--no-deps``, adds a PyPI fallback, or stops installing
     the package==version fails in CI without hitting the network.

Neither the workflow YAML nor ``util/`` is pre-commit-lint-gated for these
properties, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_publish_subpackage_workflows.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import re
import stat
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

TESTPYPI_INDEX = "https://test.pypi.org/simple/"
PYPI_EXTRA_INDEX = "https://pypi.org/simple/"

# (workflow stem suffix, pypi/package name, subdirectory). Keep in lockstep with
# the six publish-*.yml files under .github/workflows/.
SHARED_PACKAGES: tuple[tuple[str, str, str], ...] = (
    ("ci-tools", "juniper-ci-tools", "juniper-ci-tools"),
    ("config-tools", "juniper-config-tools", "juniper-config-tools"),
    ("doc-tools", "juniper-doc-tools", "juniper-doc-tools"),
    ("model-core", "juniper-model-core", "juniper-model-core"),
    ("observability", "juniper-observability", "juniper-observability"),
    ("service-core", "juniper-service-core", "juniper-service-core"),
)


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _workflow_on(doc: dict) -> dict:
    """PyYAML may parse the ``on:`` key as boolean ``True``."""
    if "on" in doc:
        return doc["on"] or {}
    if True in doc:
        return doc[True] or {}
    return {}


def _verify_step_run(doc: dict) -> tuple[str, str]:
    steps = (doc.get("jobs") or {}).get("publish-testpypi", {}).get("steps") or []
    step = next((s for s in steps if "Verify" in str(s.get("name") or "") and "run" in s), None)
    if step is None:
        raise unittest.SkipTest("could not locate Verify install step in publish-testpypi")
    return str(step["name"]), step["run"]


def _pypi_publish_steps(job: dict) -> list[dict]:
    out = []
    for step in job.get("steps") or []:
        uses = str(step.get("uses") or "")
        if "gh-action-pypi-publish" in uses:
            out.append(step)
    return out


class PublishSubpackageStructuralTest(unittest.TestCase):
    """Pin shared-package publish-*.yml contracts that already failed in the wild."""

    repo_root: Path
    workflows_dir: Path
    loaded: dict[str, dict]

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflows_dir = cls.repo_root / ".github" / "workflows"
        cls.loaded = {}
        for suffix, pkg, _subdir in SHARED_PACKAGES:
            path = cls.workflows_dir / f"publish-{suffix}.yml"
            if not path.is_file():
                raise unittest.SkipTest(f"missing {path.name}")
            cls.loaded[pkg] = {
                "path": path,
                "raw": path.read_text(encoding="utf-8"),
                "doc": yaml.safe_load(path.read_text(encoding="utf-8")),
                "suffix": suffix,
            }

    def test_exactly_the_six_shared_publish_workflows_exist(self) -> None:
        found = sorted(p.name for p in self.workflows_dir.glob("publish-*.yml"))
        expected = sorted(f"publish-{suffix}.yml" for suffix, _, _ in SHARED_PACKAGES)
        self.assertEqual(found, expected, "shared publish-* set drifted — update SHARED_PACKAGES + this gate together")

    def test_no_push_tags_trigger(self) -> None:
        # #555: release+push:tags double-fired concurrent publishes.
        for pkg, info in self.loaded.items():
            on = _workflow_on(info["doc"])
            with self.subTest(pkg=pkg):
                self.assertIn("release", on)
                self.assertIn("workflow_dispatch", on)
                self.assertNotIn("push", on, f"{pkg}: must not subscribe to push:tags (ml#555 race)")

    def test_permissions_are_oidc_plus_contents_read(self) -> None:
        for pkg, info in self.loaded.items():
            with self.subTest(pkg=pkg):
                self.assertEqual(
                    info["doc"].get("permissions"),
                    {"id-token": "write", "contents": "read"},
                )

    def test_concurrency_serializes_per_ref_without_cancel(self) -> None:
        for pkg, info in self.loaded.items():
            conc = info["doc"].get("concurrency") or {}
            with self.subTest(pkg=pkg):
                self.assertIn(f"publish-{info['suffix']}-", str(conc.get("group") or ""))
                self.assertIs(conc.get("cancel-in-progress"), False)

    def test_build_tag_prefix_guard_matches_package(self) -> None:
        for suffix, pkg, subdir in SHARED_PACKAGES:
            doc = self.loaded[pkg]["doc"]
            build = (doc.get("jobs") or {}).get("build") or {}
            build_if = str(build.get("if") or "")
            with self.subTest(pkg=pkg):
                self.assertIn("workflow_dispatch", build_if + str(_workflow_on(doc)))
                expected = f"startsWith(github.event.release.tag_name, '{pkg}-v')"
                self.assertIn(expected, build_if)
                # working-directory must be the package subdirectory
                wd = ((build.get("defaults") or {}).get("run") or {}).get("working-directory")
                self.assertEqual(wd, subdir)

    def test_artifact_path_under_subdirectory(self) -> None:
        for suffix, pkg, subdir in SHARED_PACKAGES:
            doc = self.loaded[pkg]["doc"]
            steps = ((doc.get("jobs") or {}).get("build") or {}).get("steps") or []
            upload = next((s for s in steps if "upload-artifact" in str(s.get("uses") or "")), None)
            with self.subTest(pkg=pkg):
                self.assertIsNotNone(upload)
                with_ = upload.get("with") or {}
                self.assertEqual(with_.get("name"), f"{pkg}-dist")
                self.assertEqual(with_.get("path"), f"{subdir}/dist/")
                self.assertEqual(with_.get("if-no-files-found"), "error")

    def test_publish_chain_and_environments(self) -> None:
        for pkg, info in self.loaded.items():
            jobs = info["doc"].get("jobs") or {}
            with self.subTest(pkg=pkg):
                self.assertIn("build", jobs)
                self.assertIn("publish-testpypi", jobs)
                self.assertIn("publish-pypi", jobs)
                tp = jobs["publish-testpypi"]
                py = jobs["publish-pypi"]
                needs_tp = tp.get("needs")
                needs_tp = [needs_tp] if isinstance(needs_tp, str) else (needs_tp or [])
                needs_py = py.get("needs")
                needs_py = [needs_py] if isinstance(needs_py, str) else (needs_py or [])
                self.assertIn("build", needs_tp)
                self.assertIn("publish-testpypi", needs_py)
                tp_env = tp.get("environment")
                py_env = py.get("environment")
                # environment may be a string or {name, url}
                tp_name = tp_env if isinstance(tp_env, str) else (tp_env or {}).get("name")
                py_name = py_env if isinstance(py_env, str) else (py_env or {}).get("name")
                self.assertEqual(tp_name, "testpypi")
                self.assertEqual(py_name, "pypi")

    def test_skip_existing_on_both_publish_steps(self) -> None:
        for pkg, info in self.loaded.items():
            jobs = info["doc"].get("jobs") or {}
            with self.subTest(pkg=pkg):
                for job_name in ("publish-testpypi", "publish-pypi"):
                    pubs = _pypi_publish_steps(jobs[job_name])
                    self.assertEqual(len(pubs), 1, f"{pkg}/{job_name}: expected one pypi-publish action")
                    with_ = pubs[0].get("with") or {}
                    self.assertIs(with_.get("skip-existing"), True, f"{pkg}/{job_name}: skip-existing required (#555 residual)")

    def test_testpypi_publish_targets_testpypi_legacy(self) -> None:
        for pkg, info in self.loaded.items():
            pubs = _pypi_publish_steps(info["doc"]["jobs"]["publish-testpypi"])
            with self.subTest(pkg=pkg):
                with_ = pubs[0].get("with") or {}
                self.assertEqual(with_.get("repository-url"), "https://test.pypi.org/legacy/")
                self.assertEqual(with_.get("packages-dir"), "dist/")

    def test_verify_uses_no_deps_testpypi_only(self) -> None:
        for pkg, info in self.loaded.items():
            _name, script = _verify_step_run(info["doc"])
            with self.subTest(pkg=pkg):
                self.assertIn("--no-deps", script)
                self.assertIn(f"--index-url {TESTPYPI_INDEX}", script)
                self.assertIn(f'"{pkg}==${{version}}"', script)
                # Security: no production-PyPI fallback when --no-deps is set.
                self.assertNotIn("--extra-index-url", script)
                self.assertNotIn(PYPI_EXTRA_INDEX, script)
                self.assertIsNotNone(re.search(r"for attempt in 1 2 3 4 5", script))

    def test_verify_version_source_and_post_install_check(self) -> None:
        """Each package pins a version source + a post-install proof (import or METADATA)."""
        for pkg, info in self.loaded.items():
            _name, script = _verify_step_run(info["doc"])
            with self.subTest(pkg=pkg):
                if pkg == "juniper-model-core":
                    self.assertIn("juniper-model-core/juniper_model_core/_version.py", script)
                    self.assertIn("__version__", script)
                else:
                    self.assertIn(f"{pkg}/pyproject.toml", script)
                    self.assertIn("grep '^version'", script)
                # Post-install must prove the package landed — either importlib.metadata
                # (deps-heavy packages that cannot import under --no-deps) or a direct import.
                has_metadata = "importlib.metadata" in script and f"m.version('{pkg}')" in script
                has_import = f"import {pkg.replace('-', '_')}" in script
                self.assertTrue(
                    has_metadata or has_import,
                    f"{pkg}: verify must prove install via importlib.metadata or package import",
                )


class PublishSubpackageVerifyRehearsalTest(unittest.TestCase):
    """Run each extracted verify shell with PATH stubs — prove --no-deps + TestPyPI install fires."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.scripts: dict[str, str] = {}
        for suffix, pkg, _subdir in SHARED_PACKAGES:
            path = cls.repo_root / ".github" / "workflows" / f"publish-{suffix}.yml"
            if not path.is_file():
                raise unittest.SkipTest(f"missing {path.name}")
            _name, script = _verify_step_run(yaml.safe_load(path.read_text(encoding="utf-8")))
            cls.scripts[pkg] = script

    def _stage_version_tree(self, root: Path, pkg: str, version: str = "9.9.9") -> None:
        if pkg == "juniper-model-core":
            ver_dir = root / "juniper-model-core" / "juniper_model_core"
            ver_dir.mkdir(parents=True, exist_ok=True)
            (ver_dir / "_version.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
        else:
            pkg_dir = root / pkg
            pkg_dir.mkdir(parents=True, exist_ok=True)
            (pkg_dir / "pyproject.toml").write_text(
                f'[project]\nname = "{pkg}"\nversion = "{version}"\n',
                encoding="utf-8",
            )

    def _write_stubs(self, bindir: Path, pip_log: Path, version: str = "9.9.9") -> None:
        sleep = bindir / "sleep"
        sleep.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        sleep.chmod(sleep.stat().st_mode | stat.S_IXUSR)

        pip = bindir / "pip"
        pip.write_text(
            "#!/bin/bash\n" f'printf "%s\\n" "$*" >> "{pip_log}"\n' "exit 0\n",
            encoding="utf-8",
        )
        pip.chmod(pip.stat().st_mode | stat.S_IXUSR)

        # python stub: -c importlib.metadata / import / -m <pkg> --version all succeed.
        python = bindir / "python"
        python.write_text(
            "#!/bin/bash\n" 'args="$*"\n' 'if [[ "$args" == *importlib.metadata* ]]; then\n' f'  echo "TestPyPI install OK {version}"\n' "  exit 0\n" "fi\n" 'if [[ "$args" == *-m* ]]; then\n' f'  echo "{version}"\n' "  exit 0\n" "fi\n" f'echo "TestPyPI install OK {version}"\n' "exit 0\n",
            encoding="utf-8",
        )
        python.chmod(python.stat().st_mode | stat.S_IXUSR)

        # doc-tools verify invokes the console script directly.
        console = bindir / "juniper-check-doc-links"
        console.write_text("#!/bin/bash\necho ok\nexit 0\n", encoding="utf-8")
        console.chmod(console.stat().st_mode | stat.S_IXUSR)

    def _run_verify(self, pkg: str) -> list[str]:
        script = self.scripts[pkg]
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            bindir = tdp / "bin"
            bindir.mkdir()
            pip_log = tdp / "pip.log"
            pip_log.write_text("", encoding="utf-8")
            self._stage_version_tree(tdp, pkg, version="9.9.9")
            self._write_stubs(bindir, pip_log, version="9.9.9")
            script_path = tdp / "verify.sh"
            script_path.write_text(script, encoding="utf-8")
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            proc = subprocess.run(  # nosec B603,B607 - workflow's own shell, fixed argv
                ["bash", str(script_path)],
                cwd=str(tdp),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"{pkg}: verify shell exited {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )
            return [ln for ln in pip_log.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def test_each_verify_fires_exactly_one_no_deps_testpypi_install(self) -> None:
        for pkg in self.scripts:
            with self.subTest(pkg=pkg):
                lines = self._run_verify(pkg)
                self.assertEqual(len(lines), 1, f"{pkg}: expected 1 pip install, got {lines}")
                line = lines[0]
                self.assertIn("install", line)
                self.assertIn("--no-deps", line)
                self.assertIn(f"--index-url {TESTPYPI_INDEX}", line)
                self.assertIn(f"{pkg}==9.9.9", line)
                self.assertNotIn("--extra-index-url", line)
                self.assertNotIn(PYPI_EXTRA_INDEX, line)


if __name__ == "__main__":
    unittest.main()
