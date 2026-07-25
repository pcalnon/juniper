#!/usr/bin/env python3
"""Structural lint + registry<->pyproject drift gate for the release-train registry
(util/release_train/registry.yaml, plan S4.1).

Two tiers:

1. **Structural lint (ALWAYS runs)** -- all 18 packages present; every required field
   present with a valid enum; exactly 8 owning repos including juniper-recurrence;
   tag_pattern / archive_name well-formed; depends_on references known packages. This
   is the always-on gate so a newly-added or malformed package cannot silently escape.

2. **Registry<->pyproject resolution** -- every registry entry must resolve to a real
   ``pyproject.toml`` and every ecosystem ``pyproject.toml`` with a ``[project]`` table
   must appear in the registry (plan S4.1: "a newly-added package cannot silently escape
   the train"). The 7 in-repo juniper-ml packages are validated UNCONDITIONALLY; the 11
   cross-repo entries use the ``test_doc_tools_drift.py`` sibling-on-disk auto-skip
   semantics (skip when siblings are absent; skip local runs unless
   ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``) because local sibling trees can lag origin/main.

3. **Static-package version==dunder lockstep gate (ALWAYS runs)** -- every in-repo package
   with BOTH a static ``[project].version`` and a ``_version.py`` ``__version__`` must keep
   them equal, train or no train (the ml#701 stale-dunder class: ci-tools 0.7.0 / service-core
   0.5.0 shipped wheels whose ``__version__`` lied; service-core sat undetected for five days
   because no generic gate existed). Dynamic packages are exempt -- their dunder IS the source.

``prompts/**`` / ``util/**`` are not pre-commit-lint-gated, so this unittest is the gate.

Run: python3 -m unittest -v tests/test_release_train_registry.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-07-11
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import tomllib  # Python >= 3.11 (juniper-ml requires >= 3.12)
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "util" / "release_train" / "registry.yaml"

# The 8 publishing repos (audit S1 / plan Appendix B). juniper-deploy + juniper-slacker
# are NOT packages (audit S2) and must never appear.
PUBLISHING_REPOS = frozenset(
    {
        "juniper-ml",
        "juniper-cascor",
        "juniper-canopy",
        "juniper-cascor-client",
        "juniper-cascor-worker",
        "juniper-data",
        "juniper-data-client",
        "juniper-recurrence",
    }
)

# Dynamic-version packages (audit S2): model-core + the 3 recurrence packages.
DYNAMIC_PACKAGES = frozenset({"juniper-model-core", "juniper-recurrence", "juniper-recurrence-client", "juniper-recurrence-model"})

REQUIRED_FIELDS = ("pypi_name", "repo", "path", "version_source", "tag_pattern", "archive_name", "trigger", "verify", "depends_on", "ship_paths", "exclude_paths")

# Sibling repos used by the ecosystem-root heuristic (mirrors test_doc_tools_drift.py).
_KNOWN_SIBLINGS = ("juniper-cascor", "juniper-canopy", "juniper-data", "juniper-data-client", "juniper-cascor-client", "juniper-recurrence")


def _load_raw() -> list:
    import yaml  # noqa: PLC0415

    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    return data.get("packages", []) or []


def _project_name(pyproject: Path) -> "str | None":
    if tomllib is not None:
        try:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
            name = data.get("project", {}).get("name")
            return name if isinstance(name, str) else None
        except (OSError, ValueError):
            return None
    for line in pyproject.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'^\s*name\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    return None


def _project_version(pyproject: Path) -> "str | None":
    if tomllib is not None:
        try:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
            version = data.get("project", {}).get("version")
            return version if isinstance(version, str) else None
        except (OSError, ValueError):
            return None
    for line in pyproject.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'^\s*version\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    return None


def _dunder_version(text: str) -> "str | None":
    """Extract ``__version__`` from a ``_version.py`` body (same regex the live gate uses)."""
    m = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    return m.group(1) if m else None


def _versions_in_lockstep(pyver: "str | None", dunder_text: str) -> bool:
    """True when a static ``[project].version`` equals the dunder (the ml#701 comparator)."""
    dver = _dunder_version(dunder_text)
    return pyver is not None and dver is not None and pyver == dver


def _has_project_table(pyproject: Path) -> bool:
    try:
        text = pyproject.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(re.search(r"^\[project\]\s*$", text, re.MULTILINE))


def _in_repo_pyprojects(ml_root: Path) -> list:
    """Tracked juniper-ml pyproject.toml files with a [project] table (meta + 6 subs).
    Excludes build/dist/egg-info/node_modules and nested .claude worktree checkouts."""
    skip_parts = {".claude", "build", "dist", "node_modules", ".git", ".tox", ".venv"}
    out = []
    for pp in ml_root.rglob("pyproject.toml"):
        rel_parts = pp.relative_to(ml_root).parts
        if any(part in skip_parts or part.endswith(".egg-info") for part in rel_parts):
            continue
        if _has_project_table(pp):
            out.append(pp)
    return out


def _find_ecosystem_root(ml_root: Path) -> "Path | None":
    known = set(_KNOWN_SIBLINGS)
    for candidate in (ml_root.parent, ml_root.parent.parent):
        try:
            found = sum(1 for repo in known if (candidate / repo).is_dir())
        except OSError:
            continue
        if found >= 3:
            return candidate
    return None


class RegistryStructuralTest(unittest.TestCase):
    """Always-on structural lint over registry.yaml."""

    @classmethod
    def setUpClass(cls):
        cls.packages = _load_raw()
        cls.names = [p.get("pypi_name") for p in cls.packages]

    def test_registry_file_exists(self):
        self.assertTrue(REGISTRY_PATH.is_file(), f"missing {REGISTRY_PATH}")

    def test_exactly_18_packages(self):
        self.assertEqual(len(self.packages), 18, f"expected 18 packages, got {len(self.packages)}")
        self.assertEqual(len(set(self.names)), 18, "duplicate pypi_name in registry")

    def test_every_pypi_name_is_juniper_prefixed(self):
        for name in self.names:
            self.assertTrue(isinstance(name, str) and name.startswith("juniper-"), f"bad pypi_name: {name!r}")

    def test_exactly_8_repos_including_recurrence(self):
        repos = {p.get("repo") for p in self.packages}
        self.assertEqual(repos, PUBLISHING_REPOS, f"registry repos {sorted(repos)} != the 8 publishing repos")
        self.assertIn("juniper-recurrence", repos, "juniper-recurrence must be present (the ecosystem.yaml/docs-full-check omission this registry fixes)")

    def test_required_fields_present(self):
        for pkg in self.packages:
            for field in REQUIRED_FIELDS:
                self.assertIn(field, pkg, f"{pkg.get('pypi_name')}: missing required field '{field}'")
            self.assertEqual(set(pkg["trigger"]), {"now", "target"}, f"{pkg['pypi_name']}: trigger needs now+target")
            self.assertEqual(set(pkg["verify"]), {"now", "target"}, f"{pkg['pypi_name']}: verify needs now+target")

    def test_valid_enums(self):
        for pkg in self.packages:
            name = pkg["pypi_name"]
            self.assertIn(pkg["version_source"], ("static", "dynamic"), f"{name}: bad version_source")
            self.assertIn(pkg["trigger"]["now"], ("release", "tag"), f"{name}: bad trigger.now")
            self.assertEqual(pkg["trigger"]["target"], "release", f"{name}: trigger.target must normalize to release (F-4)")
            self.assertIn(pkg["verify"]["now"], ("strict", "fallback"), f"{name}: bad verify.now")
            self.assertIn(pkg["verify"]["target"], ("strict", "fallback"), f"{name}: bad verify.target")
            self.assertIsInstance(pkg["ship_paths"], list, f"{name}: ship_paths must be a list")
            self.assertIsInstance(pkg["exclude_paths"], list, f"{name}: exclude_paths must be a list")
            self.assertIsInstance(pkg["depends_on"], list, f"{name}: depends_on must be a list")

    def test_dynamic_packages_are_exactly_the_four(self):
        dynamic = {p["pypi_name"] for p in self.packages if p["version_source"] == "dynamic"}
        self.assertEqual(dynamic, set(DYNAMIC_PACKAGES), f"dynamic-version set drifted: {sorted(dynamic)}")

    def test_tag_pattern_wellformed(self):
        for pkg in self.packages:
            self.assertTrue(pkg["tag_pattern"].endswith("*"), f"{pkg['pypi_name']}: tag_pattern must be a glob ending in '*'")

    def test_archive_name_follows_convention(self):
        for pkg in self.packages:
            name = pkg["pypi_name"]
            archive = pkg["archive_name"]
            self.assertIn("{version}", archive, f"{name}: archive_name needs a {{version}} slot")
            expected = "RELEASE_NOTES_v{version}.md" if name == "juniper-ml" else f"RELEASE_NOTES_{name}_v{{version}}.md"
            self.assertEqual(archive, expected, f"{name}: archive_name '{archive}' != convention '{expected}'")

    def test_depends_on_references_known_packages(self):
        known = set(self.names)
        for pkg in self.packages:
            for dep in pkg["depends_on"]:
                self.assertIn(dep, known, f"{pkg['pypi_name']}: depends_on '{dep}' is not a registered package")
            self.assertNotIn(pkg["pypi_name"], pkg["depends_on"], f"{pkg['pypi_name']}: self-dependency")

    def test_meta_depends_on_the_widest_set(self):
        meta = next(p for p in self.packages if p["pypi_name"] == "juniper-ml")
        # the meta aggregates every extra; it must depend on many packages and never be a leaf.
        self.assertGreaterEqual(len(meta["depends_on"]), 15, "meta should depend on its full extras surface")

    def test_cascor_app_excludes_its_two_subpackages(self):
        cascor = next(p for p in self.packages if p["pypi_name"] == "juniper-cascor")
        excludes = " ".join(cascor["exclude_paths"])
        self.assertIn("juniper-cascor-model/", excludes, "cascor app scope must exclude the model sub-package dir")
        self.assertIn("juniper-cascor-protocol/", excludes, "cascor app scope must exclude the protocol sub-package dir")


class RegistryInRepoResolutionTest(unittest.TestCase):
    """Unconditional: the 7 in-repo juniper-ml entries <-> the 7 tracked pyprojects."""

    @classmethod
    def setUpClass(cls):
        cls.packages = _load_raw()

    def test_every_in_repo_entry_resolves_to_a_real_pyproject(self):
        for pkg in self.packages:
            if pkg["repo"] != "juniper-ml":
                continue
            with self.subTest(pkg=pkg["pypi_name"]):
                pyproject = (REPO_ROOT / pkg["path"] / "pyproject.toml") if pkg["path"] != "." else (REPO_ROOT / "pyproject.toml")
                self.assertTrue(pyproject.is_file(), f"{pkg['pypi_name']}: no pyproject at {pyproject}")
                name = _project_name(pyproject)
                self.assertEqual(name, pkg["pypi_name"], f"{pyproject}: [project].name '{name}' != registry '{pkg['pypi_name']}'")

    def test_every_in_repo_pyproject_is_registered(self):
        registered = {p["pypi_name"] for p in self.packages}
        for pyproject in _in_repo_pyprojects(REPO_ROOT):
            name = _project_name(pyproject)
            self.assertIsNotNone(name, f"{pyproject}: no [project].name")
            with self.subTest(pyproject=str(pyproject.relative_to(REPO_ROOT))):
                self.assertIn(name, registered, f"{pyproject}: package '{name}' has a [project] table but is not in the release-train registry")

    def test_finds_exactly_seven_in_repo_packages(self):
        # meta + 6 sub-packages; a portable sanity check that the reverse scan is scoped right.
        found = {_project_name(pp) for pp in _in_repo_pyprojects(REPO_ROOT)}
        in_repo_registered = {p["pypi_name"] for p in self.packages if p["repo"] == "juniper-ml"}
        self.assertEqual(found, in_repo_registered, f"in-repo pyprojects {sorted(found)} != registered juniper-ml packages {sorted(in_repo_registered)}")


class VersionDunderLockstepTest(unittest.TestCase):
    """The generic pyproject==dunder lockstep gate (ml#701 design S3.3) -- always-on, train or no train.

    Every in-repo package with BOTH a static ``[project].version`` and a ``_version.py``
    ``__version__`` must keep the two equal: the static release path used to bump only pyproject,
    shipping wheels whose dunder lied (ci-tools 0.7.0, caught only by its own consumer gates;
    service-core 0.5.0, silent for five days because no gate existed -- the hole this class closes).
    Dynamic packages are exempt (their dunder IS the version source). The ci-tools consumer-side
    gates (test_coverage_gap_mapper_drift / test_env_drift_check_drift) stay as belt-and-braces."""

    @classmethod
    def setUpClass(cls):
        cls.packages = _load_raw()

    def test_project_version_reads_static_assignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            pp = Path(tmp) / "pyproject.toml"
            pp.write_text('[project]\nname = "juniper-x"\nversion = "0.5.0"\ndescription = "x"\n', encoding="utf-8")
            self.assertEqual(_project_version(pp), "0.5.0")
            dyn = Path(tmp) / "dynamic.toml"
            dyn.write_text('[project]\nname = "juniper-x"\ndynamic = ["version"]\n', encoding="utf-8")
            self.assertIsNone(_project_version(dyn))

    def test_lockstep_comparator_bites_on_synthetic_drift(self):
        # Synthetic negative (service-core 0.5.0 class): pyproject ahead of dunder must NOT lockstep.
        self.assertFalse(_versions_in_lockstep("0.5.0", '"""v."""\n__version__ = "0.4.0"\n'))
        self.assertTrue(_versions_in_lockstep("0.5.0", '"""v."""\n__version__ = "0.5.0"\n'))
        self.assertFalse(_versions_in_lockstep("0.5.0", '"""No dunder."""\nVERSION = (0, 5, 0)\n'))
        self.assertFalse(_versions_in_lockstep(None, '__version__ = "0.5.0"\n'))
        # single quotes are accepted (same regex as the live gate)
        self.assertTrue(_versions_in_lockstep("0.1.1", "__version__ = '0.1.1'\n"))

    def test_static_in_repo_pyproject_version_equals_dunder(self):
        eligible = 0
        for pkg in self.packages:
            if pkg["repo"] != "juniper-ml" or pkg["version_source"] != "static":
                continue
            base = REPO_ROOT if pkg["path"] == "." else REPO_ROOT / pkg["path"]
            dunder = base / pkg["pypi_name"].replace("-", "_") / "_version.py"
            if not dunder.is_file():
                continue  # static-without-dunder (the meta-package itself): nothing to lock
            eligible += 1
            with self.subTest(pkg=pkg["pypi_name"]):
                pyver = _project_version(base / "pyproject.toml")
                self.assertIsNotNone(pyver, f"{pkg['pypi_name']}: no static [project].version in {base / 'pyproject.toml'}")
                dtext = dunder.read_text(encoding="utf-8")
                self.assertTrue(
                    _versions_in_lockstep(pyver, dtext),
                    f"{pkg['pypi_name']}: pyproject [project].version {pyver!r} != {dunder.relative_to(REPO_ROOT)} __version__ {_dunder_version(dtext)!r} -- the ml#701 stale-dunder class; bump both in lockstep (propose.py does this automatically since ml#701's implementation)",
                )
        self.assertEqual(eligible, 5, f"expected exactly the 5 static-with-dunder in-repo packages (ci-tools, config-tools, doc-tools, observability, service-core), found {eligible} -- registry or tree drifted; update this count deliberately")

    def test_gate_dunder_path_matches_propose_dunder_file_rel(self):
        # the gate derives the dunder path from pypi_name; propose.py uses PackageEntry.import_package
        # (also pypi_name with '-' -> '_'). Keep them identical so a rename cannot split the two.
        sys.path.insert(0, str(REPO_ROOT / "util" / "release_train"))
        import detect as detect_mod  # noqa: PLC0415
        import propose as propose_mod  # noqa: PLC0415

        entries = {e.pypi_name: e for e in detect_mod.load_registry()}
        checked = 0
        for pkg in self.packages:
            if pkg["repo"] != "juniper-ml" or pkg["version_source"] != "static":
                continue
            base = REPO_ROOT if pkg["path"] == "." else REPO_ROOT / pkg["path"]
            gate_path = base / pkg["pypi_name"].replace("-", "_") / "_version.py"
            if not gate_path.is_file():
                continue
            entry = entries[pkg["pypi_name"]]
            propose_rel = propose_mod.dunder_file_rel(entry)
            self.assertEqual(
                (REPO_ROOT / propose_rel).resolve(),
                gate_path.resolve(),
                f"{pkg['pypi_name']}: gate path {gate_path} != propose dunder_file_rel {propose_rel}",
            )
            checked += 1
        self.assertEqual(checked, 5)


class RegistryCrossRepoResolutionTest(unittest.TestCase):
    """Cross-repo entries -- sibling-on-disk auto-skip semantics (test_doc_tools_drift.py)."""

    @classmethod
    def setUpClass(cls):
        cls.packages = _load_raw()
        cls.ecosystem_root = _find_ecosystem_root(REPO_ROOT)

    def test_environment_is_either_ecosystem_or_skipped(self):
        if self.ecosystem_root is None:
            print("INFO: ecosystem siblings not on disk -- cross-repo registry resolution skipping (per-PR mode).")
        else:
            print(f"INFO: ecosystem root = {self.ecosystem_root}")

    def test_cross_repo_entries_resolve_to_real_pyprojects(self):
        if self.ecosystem_root is None:
            self.skipTest("ecosystem siblings not on disk")
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            self.skipTest("skipping local cross-repo resolution (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override; siblings must be pulled to origin/main first)")
        for pkg in self.packages:
            if pkg["repo"] == "juniper-ml":
                continue
            with self.subTest(pkg=pkg["pypi_name"]):
                base = self.ecosystem_root / pkg["repo"]
                if not base.is_dir():
                    print(f"WARN: {pkg['repo']} not present (clone failure?) -- skipping {pkg['pypi_name']}")
                    continue
                pyproject = (base / pkg["path"] / "pyproject.toml") if pkg["path"] != "." else (base / "pyproject.toml")
                self.assertTrue(pyproject.is_file(), f"{pkg['pypi_name']}: no pyproject at {pyproject}")
                name = _project_name(pyproject)
                self.assertEqual(name, pkg["pypi_name"], f"{pyproject}: [project].name '{name}' != registry '{pkg['pypi_name']}'")


if __name__ == "__main__":
    unittest.main()
