#!/usr/bin/env python3
"""Structural gate for in-repo shared-package ``ci-*.yml`` workflows.

The six subdirectory packages (juniper-ci-tools / config-tools / doc-tools /
model-core / observability / service-core) each ship an independent CI workflow
under ``.github/workflows/ci-<suffix>.yml``. These are distinct from the meta
``ci.yml`` and from the ``publish-*.yml`` publishers. Contracts that matter in
practice:

  * **Path filters** — push/PR must scope to ``<subdir>/**`` *and* the workflow
    file itself so a workflow edit still runs CI; dropping the self-path lets a
    broken gate land without a red check.
  * **Python matrix floors** — each package's declared ``requires-python`` /
    historical floor must stay in the matrix (dropping 3.12 silently narrows
    coverage; widening past classifiers is noise).
  * **working-directory** — five packages run pytest from the package subdir;
    service-core intentionally installs from the monorepo root (sibling
    editable ``juniper-model-core``) and must keep that install order.
  * **Coverage gates** — ``--cov-fail-under`` plus a blocking
    ``juniper-coverage-gap-map --enforce`` step (per-file rollout C-2/C-3/C-4).
    Losing ``--enforce`` turns the gap-map into a no-op and ships green on a
    gutted module.
  * **Build after test** — ``build.needs: test`` so a red matrix cannot publish
    a wheel smoke / twine check as success.

Neither the workflow YAML nor ``util/`` is pre-commit-lint-gated for these
properties, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_subpackage_ci_workflows.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

import yaml

# (workflow suffix, package subdir, import/cov name, min python versions,
#  cov-fail-under floor, test uses working-directory defaults).
#
# Matrix floors are *minimums* each workflow must include (extras OK).
# Keep in lockstep with the six ci-*.yml files under .github/workflows/.
SHARED_CI: tuple[tuple[str, str, str, tuple[str, ...], int, bool], ...] = (
    ("ci-tools", "juniper-ci-tools", "juniper_ci_tools", ("3.11", "3.12", "3.13", "3.14"), 85, True),
    ("config-tools", "juniper-config-tools", "juniper_config_tools", ("3.11", "3.12", "3.13", "3.14"), 85, True),
    ("doc-tools", "juniper-doc-tools", "juniper_doc_tools", ("3.12", "3.13", "3.14"), 85, True),
    ("model-core", "juniper-model-core", "juniper_model_core", ("3.12", "3.13", "3.14"), 95, True),
    ("observability", "juniper-observability", "juniper_observability", ("3.12", "3.13"), 90, True),
    ("service-core", "juniper-service-core", "juniper_service_core", ("3.12", "3.13"), 80, False),
)

# Console / module smokes expected in the build job (observability + service-core
# currently have no wheel smoke — pin the packages that do).
SMOKE_MARKERS: dict[str, tuple[str, ...]] = {
    "juniper-ci-tools": (
        "juniper-generate-dep-docs --version",
        "juniper-env-drift-check --version",
        "juniper-coverage-gap-map --version",
    ),
    "juniper-doc-tools": (
        "juniper-check-doc-links --version",
        "python -m juniper_doc_tools --version",
    ),
    "juniper-config-tools": ("python -m juniper_config_tools --version",),
    "juniper-model-core": ("import juniper_model_core",),
}


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


def _step_runs(job: dict) -> list[str]:
    return [str(s.get("run") or "") for s in (job.get("steps") or []) if "run" in s]


def _needs_list(job: dict) -> list[str]:
    needs = job.get("needs")
    if needs is None:
        return []
    if isinstance(needs, str):
        return [needs]
    return list(needs)


class SubpackageCiStructuralTest(unittest.TestCase):
    """Pin shared-package ci-*.yml contracts that keep subdirectory CI honest."""

    repo_root: Path
    workflows_dir: Path
    loaded: dict[str, dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflows_dir = cls.repo_root / ".github" / "workflows"
        cls.loaded = {}
        for suffix, subdir, cov_name, matrix, cov_floor, uses_wd in SHARED_CI:
            path = cls.workflows_dir / f"ci-{suffix}.yml"
            if not path.is_file():
                raise unittest.SkipTest(f"missing {path.name}")
            raw = path.read_text(encoding="utf-8")
            cls.loaded[subdir] = {
                "path": path,
                "raw": raw,
                "doc": yaml.safe_load(raw),
                "suffix": suffix,
                "cov_name": cov_name,
                "matrix_min": matrix,
                "cov_floor": cov_floor,
                "uses_wd": uses_wd,
            }

    def test_exactly_the_six_shared_ci_workflows_exist(self) -> None:
        found = sorted(p.name for p in self.workflows_dir.glob("ci-*.yml") if p.name != "ci.yml" and not p.name.startswith("ci.yml"))
        # Only the six package workflows use the ci-<pkg>.yml naming; meta is ci.yml.
        expected = sorted(f"ci-{suffix}.yml" for suffix, *_ in SHARED_CI)
        self.assertEqual(
            found,
            expected,
            "shared ci-* set drifted — update SHARED_CI + this gate together",
        )

    def test_permissions_are_contents_read_only(self) -> None:
        for subdir, info in self.loaded.items():
            with self.subTest(pkg=subdir):
                self.assertEqual(info["doc"].get("permissions"), {"contents": "read"})

    def test_triggers_include_push_pr_dispatch_with_path_filters(self) -> None:
        for subdir, info in self.loaded.items():
            on = _workflow_on(info["doc"])
            wf_self = f".github/workflows/ci-{info['suffix']}.yml"
            with self.subTest(pkg=subdir):
                self.assertIn("workflow_dispatch", on)
                for event in ("push", "pull_request"):
                    self.assertIn(event, on, f"{subdir}: missing {event} trigger")
                    paths = (on.get(event) or {}).get("paths") or []
                    self.assertIn(f"{subdir}/**", paths)
                    self.assertIn(
                        wf_self,
                        paths,
                        f"{subdir}: {event} must include self-path {wf_self} " "so workflow edits still run CI",
                    )
                    branches = (on.get(event) or {}).get("branches") or []
                    self.assertIn("main", branches)

    def test_python_matrix_includes_declared_floors(self) -> None:
        for subdir, info in self.loaded.items():
            test_job = (info["doc"].get("jobs") or {}).get("test") or {}
            matrix = ((test_job.get("strategy") or {}).get("matrix") or {}).get("python-version") or []
            matrix_s = {str(v) for v in matrix}
            with self.subTest(pkg=subdir):
                missing = set(info["matrix_min"]) - matrix_s
                self.assertFalse(
                    missing,
                    f"{subdir}: matrix {sorted(matrix_s)} missing required floors {sorted(missing)}",
                )
                self.assertIs((test_job.get("strategy") or {}).get("fail-fast"), False)

    def test_test_job_working_directory_and_service_core_sibling_install(self) -> None:
        for subdir, info in self.loaded.items():
            test_job = (info["doc"].get("jobs") or {}).get("test") or {}
            wd = ((test_job.get("defaults") or {}).get("run") or {}).get("working-directory")
            runs = "\n".join(_step_runs(test_job))
            with self.subTest(pkg=subdir):
                if info["uses_wd"]:
                    self.assertEqual(wd, subdir)
                else:
                    # service-core: monorepo-root install of sibling model-core first.
                    self.assertIsNone(wd)
                    self.assertIn("pip install -e juniper-model-core", runs)
                    self.assertIn('pip install -e "juniper-service-core/.[test]"', runs)
                    # Sibling must precede service-core install (publish-first ordering).
                    self.assertLess(
                        runs.index("pip install -e juniper-model-core"),
                        runs.index('pip install -e "juniper-service-core/.[test]"'),
                    )

    def test_coverage_fail_under_and_blocking_gap_map_enforce(self) -> None:
        for subdir, info in self.loaded.items():
            test_job = (info["doc"].get("jobs") or {}).get("test") or {}
            runs = _step_runs(test_job)
            joined = "\n".join(runs)
            with self.subTest(pkg=subdir):
                self.assertIn(f"--cov={info['cov_name']}", joined)
                self.assertIn(f"--cov-fail-under={info['cov_floor']}", joined)
                self.assertIn("coverage.json", joined)
                enforce_steps = [r for r in runs if "juniper-coverage-gap-map" in r]
                self.assertTrue(enforce_steps, f"{subdir}: missing coverage-gap-map step")
                for step in enforce_steps:
                    self.assertIn("--enforce", step)
                    self.assertIn("coverage.json", step)
                if subdir == "juniper-ci-tools":
                    # C-2: __main__.py shim omitted from the enforcing gate.
                    self.assertTrue(any("--omit" in s and "__main__.py" in s for s in enforce_steps))
                else:
                    # Other packages must not silently adopt a broad omit.
                    self.assertFalse(
                        any("--omit" in s for s in enforce_steps),
                        f"{subdir}: unexpected --omit on enforcing gap-map",
                    )

    def test_build_needs_test_and_uses_package_working_directory(self) -> None:
        for subdir, info in self.loaded.items():
            jobs = info["doc"].get("jobs") or {}
            build = jobs.get("build") or {}
            wd = ((build.get("defaults") or {}).get("run") or {}).get("working-directory")
            runs = "\n".join(_step_runs(build))
            with self.subTest(pkg=subdir):
                self.assertIn("test", jobs)
                self.assertIn("build", jobs)
                self.assertIn("test", _needs_list(build))
                self.assertEqual(wd, subdir)
                self.assertIn("python -m build", runs)
                self.assertIn("twine check", runs)

    def test_wheel_smoke_entry_points_where_declared(self) -> None:
        for subdir, markers in SMOKE_MARKERS.items():
            info = self.loaded[subdir]
            build = (info["doc"].get("jobs") or {}).get("build") or {}
            smoke = next(
                (s for s in (build.get("steps") or []) if "Smoke" in str(s.get("name") or "")),
                None,
            )
            with self.subTest(pkg=subdir):
                self.assertIsNotNone(smoke, f"{subdir}: expected Smoke-test step")
                run = str(smoke.get("run") or "")
                self.assertIn("python -m venv", run)
                self.assertIn(".whl", run)
                for marker in markers:
                    self.assertIn(marker, run)

    def test_packages_without_wheel_smoke_still_twine_check(self) -> None:
        for subdir in ("juniper-observability", "juniper-service-core"):
            build = (self.loaded[subdir]["doc"].get("jobs") or {}).get("build") or {}
            names = [str(s.get("name") or "") for s in (build.get("steps") or [])]
            with self.subTest(pkg=subdir):
                self.assertFalse(any("Smoke" in n for n in names))
                self.assertTrue(any("twine check" in str(s.get("run") or "") for s in build.get("steps") or []))


if __name__ == "__main__":
    unittest.main()
