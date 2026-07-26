#!/usr/bin/env python3
"""Hermetic regression tests for util/release_train/detect.py (plan S4.2/S4.3, Phase 1.2).

NO network, NO real gh, NO real pip. Every external data source (PyPI JSON, gh tags /
releases / compare, filesystem source reads) is injected through a fake ``Sources``
object; version / CHANGELOG reads run against a synthetic on-disk repo built per test.

Covers (task acceptance list):
  * each classification -- UP_TO_DATE, UNRELEASED_CHANGES, BUMPED_NOT_RELEASED,
    NEVER_RELEASED, SHIP_UNCERTAIN, ANOMALY
  * static vs dynamic (``_version.py``) declared-version reading
  * diff-base tag resolution preferring the tag equal to the released version
  * the substantive-hunk filter -- discount a comment-only and a docstring/link-only
    ``.py`` edit; catch a real code hunk
  * path-scoping -- subdir package vs the cascor "repo minus the two subpkg dirs" app
  * CHANGELOG [Unreleased] corroboration-conflict surfacing
  * SemVer proposal derivation (pre-1.0: breaking/feature => MINOR, fix => PATCH)
  * release-manifest JSON shape
  * CLI exit codes 0 / 1 / 2

``util/`` is not pre-commit-lint-gated, so this unittest IS the gate (the
``env_floor_drift_check`` precedent). Imported via the house ``sys.path.insert`` idiom.

Run: python3 -m unittest -v tests/test_release_train_detect.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-07-11
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

UTIL_DIR = Path(__file__).resolve().parents[1] / "util" / "release_train"
sys.path.insert(0, str(UTIL_DIR))

import detect as d  # noqa: E402

# ── helpers ──────────────────────────────────────────────────────────────────


def _entry(**over) -> d.PackageEntry:
    base = {
        "pypi_name": "juniper-thing",
        "repo": "juniper-ml",
        "path": "juniper-thing/",
        "version_source": "static",
        "tag_pattern": "juniper-thing-v*",
        "archive_name": "RELEASE_NOTES_juniper-thing_v{version}.md",
        "trigger": {"now": "release", "target": "release"},
        "verify": {"now": "strict", "target": "strict"},
        "depends_on": [],
        "ship_paths": ["juniper-thing/juniper_thing/"],
        "exclude_paths": [],
    }
    base.update(over)
    return d.PackageEntry(**base)


def _pypi(version: "str | None", upload: str = "2026-06-01T00:00:00Z") -> "dict | None":
    if version is None:
        return None
    return {"info": {"version": version}, "releases": {version: [{"upload_time_iso_8601": upload}]}}


class _FakeSources:
    """Assemble an injectable Sources with in-memory pypi/tags/releases/compare and a
    disk-backed read_file over the synthetic repo tree."""

    def __init__(self, repo_root: Path, ecosystem_root: Path):
        self.repo_root = repo_root
        self.ecosystem_root = ecosystem_root
        self.pypi: dict = {}
        self.tags: dict = {}
        self.releases: dict = {}
        self.compares: dict = {}

    def read_file(self, entry, filename):
        base = d.base_dir_for(entry, self.repo_root, self.ecosystem_root)
        try:
            return (base / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    def build(self) -> d.Sources:
        return d.Sources(
            pypi_json=lambda name: self.pypi.get(name),
            list_tags=lambda repo: list(self.tags.get(repo, [])),
            list_releases=lambda repo: set(self.releases.get(repo, set())),
            compare=lambda entry, base, head: self.compares.get((entry.repo, base, head), d.CompareResult(files=[], commits=[], ok=False, error="no compare")),
            read_file=self.read_file,
        )


def _write_pkg(repo_root: Path, path: str, *, name: str, version: str, changelog: str = "", dynamic: bool = False, import_pkg: str = "") -> None:
    """Create a synthetic package tree with pyproject (+ _version.py if dynamic) + CHANGELOG."""
    pkg_dir = repo_root if path == "." else repo_root / path.rstrip("/")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    if dynamic:
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{name}"\ndynamic = ["version"]\n')
        ip = import_pkg or name.replace("-", "_")
        (pkg_dir / ip).mkdir(parents=True, exist_ok=True)
        (pkg_dir / ip / "_version.py").write_text(f'__version__ = "{version}"\n')
    else:
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{name}"\nversion = "{version}"\n')
    if changelog:
        (pkg_dir / "CHANGELOG.md").write_text(changelog)


def _fc(filename: str, patch: "str | None", status: str = "modified") -> d.FileChange:
    return d.FileChange(filename=filename, status=status, patch=patch)


# realistic patch fixtures (aligned line numbers so the tokenize path is exercised)
_COMMENT_ONLY_PATCH = "@@ -84,3 +84,3 @@\n # aligned comment context\n-# see notes/OLD.md\n+# see notes/NEW.md"
_DOCSTRING_PATCH = "@@ -12,3 +12,3 @@\n prose line\n-Reference: OLD_NOTE.md section 6.\n+Reference: NEW_NOTE.md section 6.\n more prose"
_REAL_CODE_PATCH = "@@ -10,2 +10,2 @@\n def handler():\n-    return old()\n+    return new_validation()"


# ── pure-function unit tests ─────────────────────────────────────────────────


class VersionAndBumpTest(unittest.TestCase):
    def test_version_cmp(self):
        self.assertEqual(d.version_cmp("0.4.0", "0.4.0"), 0)
        self.assertEqual(d.version_cmp("0.5.0", "0.4.0"), 1)
        self.assertEqual(d.version_cmp("0.4.0", "0.5.0"), -1)
        self.assertEqual(d.version_cmp("0.10.0", "0.9.0"), 1)  # numeric, not lexical

    def test_bump_version_pre_1_0(self):
        self.assertEqual(d.bump_version("0.4.0", "minor"), "0.5.0")
        self.assertEqual(d.bump_version("0.4.1", "patch"), "0.4.2")
        self.assertIsNone(d.bump_version("0.4.0", "none"))


class TagResolutionTest(unittest.TestCase):
    def test_prefers_tag_equal_to_released_version(self):
        tags = ["v0.3.0", "v0.5.0", "v0.4.0"]
        self.assertEqual(d.resolve_diff_base_tag(tags, "v*", "0.4.0"), "v0.4.0")

    def test_falls_back_to_newest_when_no_exact(self):
        self.assertEqual(d.resolve_diff_base_tag(["v0.3.0", "v0.4.0"], "v*", "0.9.0"), "v0.4.0")

    def test_prefix_disambiguates_sibling_subpackage_tags(self):
        # "v*" must not match "juniper-ci-tools-v*"; recurrence app must not match client/model tags.
        self.assertIsNone(d.tag_version("juniper-ci-tools-v0.6.0", "v*"))
        self.assertIsNone(d.tag_version("juniper-recurrence-client-v0.2.0", "juniper-recurrence-v*"))
        self.assertEqual(d.tag_version("juniper-recurrence-v0.2.0", "juniper-recurrence-v*"), "0.2.0")

    def test_no_matching_tag_returns_none(self):
        self.assertIsNone(d.resolve_diff_base_tag(["other-v1.0.0"], "v*", "0.4.0"))


class SubstantiveHunkTest(unittest.TestCase):
    def test_comment_only_edit_is_discounted(self):
        self.assertIs(d.has_substantive_hunk(_COMMENT_ONLY_PATCH, None), False)

    def test_docstring_link_edit_is_discounted_with_file(self):
        # New-side line 13 (the '+' line) lands inside a module docstring -> not a code line.
        file_text = "\n".join(['"""', "prose line", "prose line", "Reference: NEW_NOTE.md section 6.", "more prose", '"""', "import os"] + ["x = 1"] * 6) + "\n"
        # rebuild so the changed '+' line is at line 13 to match the @@ header
        file_text = "\n".join(["header"] * 11 + ['"""docstring', "Reference: NEW_NOTE.md section 6.", 'end"""']) + "\n"
        patch = "@@ -12,1 +12,1 @@\n-Reference: OLD_NOTE.md section 6.\n+Reference: NEW_NOTE.md section 6."
        self.assertIs(d.has_substantive_hunk(patch, file_text), False)

    def test_real_code_hunk_is_substantive_with_file(self):
        file_text = "\n".join(["header"] * 9 + ["def handler():", "    return new_validation()"]) + "\n"
        self.assertIs(d.has_substantive_hunk(_REAL_CODE_PATCH, file_text), True)

    def test_real_code_hunk_substantive_without_file(self):
        self.assertIs(d.has_substantive_hunk(_REAL_CODE_PATCH, None), True)

    def test_patch_unavailable_is_uncertain(self):
        self.assertIsNone(d.has_substantive_hunk(None, None))


class SubstantiveBetweenTest(unittest.TestCase):
    """The alignment-free base-vs-head code-line test used by the path-scoped fallback."""

    def test_docstring_link_edit_leaves_code_lines_unchanged(self):
        base = '"""Module.\n\nSee ``notes/JUNIPER_OLD_NAME_2026-05-22.md`` for details.\n"""\nimport os\n\n\ndef f():\n    return os.getpid()\n'
        head = '"""Module.\n\nSee ``notes/JUNIPER_2026-05-22_NEW-NAME.md`` for details.\n"""\nimport os\n\n\ndef f():\n    return os.getpid()\n'
        self.assertIs(d.substantive_between(base, head), False)  # only the docstring changed

    def test_comment_edit_leaves_code_lines_unchanged(self):
        base = "x = 1  # see notes/OLD.md\n"
        head = "x = 1  # see notes/NEW.md\n"
        self.assertIs(d.substantive_between(base, head), False)

    def test_default_argument_value_change_is_substantive(self):
        # ci-tools class: a notes-rename that edits a default= string ON A CODE LINE.
        base = 'def build():\n    p.add_argument("--h", default="OLD_HEADER.md")\n'
        head = 'def build():\n    p.add_argument("--h", default="NEW_HEADER.md")\n'
        self.assertIs(d.substantive_between(base, head), True)

    def test_ruff_reformat_is_substantive(self):
        base = "def f(s):\n    return zip(s, s[1:])\n"
        head = "def f(s):\n    return zip(s, s[1:], strict=False)\n"
        self.assertIs(d.substantive_between(base, head), True)

    def test_unreadable_is_uncertain(self):
        self.assertIsNone(d.substantive_between(None, "x = 1\n"))

    def test_classify_change_honours_precomputed_substantive(self):
        e = _entry()
        ship = d.classify_change(_fc("juniper-thing/juniper_thing/m.py", None, status="modified"), e, None)
        self.assertEqual(ship[0], "uncertain")  # no patch, no override -> uncertain
        fc_true = d.FileChange("juniper-thing/juniper_thing/m.py", "modified", None, cumulative=False, substantive=True)
        fc_false = d.FileChange("juniper-thing/juniper_thing/m.py", "modified", None, cumulative=False, substantive=False)
        self.assertEqual(d.classify_change(fc_true, e, None)[0], "ship")
        self.assertEqual(d.classify_change(fc_false, e, None)[0], "nonship")


class PyprojectClassifierTest(unittest.TestCase):
    def test_runtime_extra_change_is_ship(self):
        patch = '@@ -50,2 +50,4 @@\n [project.optional-dependencies]\n clients = ["juniper-data-client>=0.4.1"]\n+recurrence = [\n+  "juniper-recurrence>=0.2.0,<0.3.0",\n+]'
        self.assertEqual(d.classify_pyproject_patch(patch)[0], "ship")

    def test_version_bump_is_ship(self):
        patch = '@@ -2,1 +2,1 @@\n [project]\n-version = "0.4.0"\n+version = "0.5.0"'
        self.assertEqual(d.classify_pyproject_patch(patch)[0], "ship")

    def test_pytest_config_is_nonship(self):
        patch = '@@ -80,2 +80,3 @@\n [tool.pytest.ini_options]\n minversion = "8.0"\n+addopts = "--strict-config"'
        self.assertEqual(d.classify_pyproject_patch(patch)[0], "nonship")

    def test_test_extra_is_nonship(self):
        patch = '@@ -55,3 +55,3 @@\n [project.optional-dependencies]\n test = [\n-  "pytest",\n+  "pytest", "juniper-observability>=0.3.1",\n ]'
        self.assertEqual(d.classify_pyproject_patch(patch)[0], "nonship")

    def test_patch_unavailable_is_uncertain(self):
        self.assertEqual(d.classify_pyproject_patch(None)[0], "uncertain")


class PathScopingTest(unittest.TestCase):
    def test_subdir_package_scope(self):
        e = _entry(pypi_name="juniper-ci-tools", path="juniper-ci-tools/", ship_paths=["juniper-ci-tools/juniper_ci_tools/"], tag_pattern="juniper-ci-tools-v*")
        self.assertTrue(d.in_scope("juniper-ci-tools/juniper_ci_tools/cli.py", e))
        self.assertTrue(d.in_scope("juniper-ci-tools/pyproject.toml", e))
        self.assertFalse(d.in_scope("juniper-ci-tools/tests/test_cli.py", e))
        self.assertFalse(d.in_scope("juniper-service-core/juniper_service_core/x.py", e))
        self.assertFalse(d.in_scope("notes/x.md", e))

    def test_cascor_app_is_repo_minus_subpackages(self):
        e = _entry(
            pypi_name="juniper-cascor",
            repo="juniper-cascor",
            path=".",
            ship_paths=["src/", "juniper_cascor/"],
            exclude_paths=["src/tests/", "src/backups/", "juniper-cascor-model/", "juniper-cascor-protocol/"],
            tag_pattern="v*",
        )
        self.assertTrue(d.in_scope("src/api/routes.py", e))
        self.assertTrue(d.in_scope("juniper_cascor/main.py", e))
        self.assertTrue(d.in_scope("pyproject.toml", e))
        self.assertFalse(d.in_scope("src/tests/test_x.py", e))  # excluded
        self.assertFalse(d.in_scope("juniper-cascor-model/juniper_cascor_model/m.py", e))  # sub-package
        self.assertFalse(d.in_scope("juniper-cascor-protocol/juniper_cascor_protocol/p.py", e))
        self.assertFalse(d.in_scope("notes/x.md", e))


class SemVerAndChangelogTest(unittest.TestCase):
    def test_semver_feature_is_minor(self):
        bump, ver = d.propose_semver("0.4.0", ["Added"], set())
        self.assertEqual((bump, ver), ("minor", "0.5.0"))

    def test_semver_fix_is_patch(self):
        self.assertEqual(d.propose_semver("0.4.1", ["Fixed"], set())[0], "patch")

    def test_semver_breaking_is_minor_pre_1_0(self):
        self.assertEqual(d.propose_semver("0.4.0", ["Removed"], set())[0], "minor")

    def test_semver_commit_class_feat(self):
        self.assertEqual(d.propose_semver("0.4.0", [], {"feat"})[0], "minor")

    def test_semver_none_when_empty(self):
        self.assertEqual(d.propose_semver("0.4.0", [], set()), ("none", None))

    def test_changelog_conflict_up_to_date_but_added(self):
        msg = d.changelog_conflict(d.UP_TO_DATE, ["Added"])
        self.assertIsNotNone(msg)
        self.assertIn("added", (msg or "").lower())

    def test_changelog_conflict_unreleased_but_empty(self):
        self.assertIsNotNone(d.changelog_conflict(d.UNRELEASED_CHANGES, []))

    def test_no_conflict_when_aligned(self):
        self.assertIsNone(d.changelog_conflict(d.UNRELEASED_CHANGES, ["Added"]))
        self.assertIsNone(d.changelog_conflict(d.UP_TO_DATE, []))


class ChangelogReaderTest(unittest.TestCase):
    def test_reads_unreleased_categories_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changelog = textwrap.dedent("""\
                # Changelog

                ## [Unreleased]

                ### Added
                - a new thing

                ### Tests
                - a test only

                ## [0.4.0] - 2026-06-01
                ### Fixed
                - old
                """)
            _write_pkg(root, ".", name="juniper-thing", version="0.4.0", changelog=changelog)
            e = _entry(repo="juniper-ml", path=".")
            fake = _FakeSources(root, root.parent)
            cats = d.read_changelog_unreleased(e, root, root.parent, fake.read_file)
            self.assertIn("added", cats)
            self.assertIn("tests", cats)
            self.assertNotIn("fixed", cats)  # that bullet is under the released 0.4.0 section


class DeclaredVersionTest(unittest.TestCase):
    def test_static_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "sub/", name="juniper-thing", version="0.4.0")
            e = _entry(repo="juniper-ml", path="sub/", version_source="static")
            self.assertEqual(d.read_declared_version(e, root, root.parent), "0.4.0")

    def test_dynamic_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_pkg(root, "sub/", name="juniper-model-core", version="0.3.0", dynamic=True, import_pkg="juniper_model_core")
            e = _entry(pypi_name="juniper-model-core", repo="juniper-ml", path="sub/", version_source="dynamic")
            self.assertEqual(d.read_declared_version(e, root, root.parent), "0.3.0")


# ── classification integration tests (fake sources + synthetic repo) ─────────


class ClassificationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        self.eco = self.root
        self.fake = _FakeSources(self.repo_root, self.eco)

    def tearDown(self):
        self._tmp.cleanup()

    def _pkg(self, version: str, changelog: str = "") -> d.PackageEntry:
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version=version, changelog=changelog)
        return _entry(repo="juniper-ml", path="juniper-thing/")

    def _classify(self, entry) -> d.PackageRecord:
        return d.classify_package(entry, self.fake.build(), self.repo_root, self.eco)

    def test_never_released(self):
        e = self._pkg("0.1.0")
        self.fake.pypi["juniper-thing"] = None
        self.assertEqual(self._classify(e).classification, d.NEVER_RELEASED)

    def test_bumped_not_released(self):
        e = self._pkg("0.5.0")
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.assertEqual(self._classify(e).classification, d.BUMPED_NOT_RELEASED)

    def test_anomaly_declared_below_released(self):
        e = self._pkg("0.1.0")
        self.fake.pypi["juniper-thing"] = _pypi("0.2.0")
        self.assertEqual(self._classify(e).classification, d.ANOMALY)

    def test_up_to_date_only_nonship_changes(self):
        e = self._pkg("0.4.0")
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.fake.tags["juniper-ml"] = ["juniper-thing-v0.4.0"]
        self.fake.compares[("juniper-ml", "juniper-thing-v0.4.0", "main")] = d.CompareResult(
            files=[_fc("juniper-thing/juniper_thing/mod.py", _COMMENT_ONLY_PATCH), _fc("juniper-thing/tests/test_mod.py", _REAL_CODE_PATCH), _fc("juniper-thing/README.md", "@@ -1 +1 @@\n-old\n+new")],
            commits=["docs: rename notes"],
        )
        rec = self._classify(e)
        self.assertEqual(rec.classification, d.UP_TO_DATE)
        self.assertEqual(rec.ship_evidence, [])

    def test_unreleased_changes_on_substantive_ship_hunk(self):
        e = self._pkg("0.4.0", changelog="## [Unreleased]\n### Added\n- new module\n")
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.fake.tags["juniper-ml"] = ["juniper-thing-v0.4.0"]
        # a real code hunk in a shipping .py; file_text on disk aligns with the patch line numbers
        (self.repo_root / "juniper-thing" / "juniper_thing").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "juniper-thing" / "juniper_thing" / "mod.py").write_text("\n".join(["h"] * 9 + ["def handler():", "    return new_validation()"]) + "\n")
        self.fake.compares[("juniper-ml", "juniper-thing-v0.4.0", "main")] = d.CompareResult(
            files=[_fc("juniper-thing/juniper_thing/mod.py", _REAL_CODE_PATCH)],
            commits=["feat: add validation"],
        )
        rec = self._classify(e)
        self.assertEqual(rec.classification, d.UNRELEASED_CHANGES)
        self.assertEqual(len(rec.ship_evidence), 1)
        self.assertEqual(rec.proposed_bump, "minor")
        self.assertEqual(rec.proposed_version, "0.5.0")

    def test_ship_uncertain_on_patch_unavailable(self):
        e = self._pkg("0.4.0")
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.fake.tags["juniper-ml"] = ["juniper-thing-v0.4.0"]
        self.fake.compares[("juniper-ml", "juniper-thing-v0.4.0", "main")] = d.CompareResult(
            files=[_fc("juniper-thing/juniper_thing/mod.py", None)],  # over-large diff: no patch
            commits=[],
        )
        rec = self._classify(e)
        self.assertEqual(rec.classification, d.SHIP_UNCERTAIN)
        self.assertEqual(len(rec.ship_uncertain), 1)

    def test_ship_uncertain_when_no_matching_tag(self):
        e = self._pkg("0.4.0")
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.fake.tags["juniper-ml"] = ["v9.9.9"]  # nothing under juniper-thing-v*
        self.assertEqual(self._classify(e).classification, d.SHIP_UNCERTAIN)

    def test_changelog_conflict_is_surfaced(self):
        # UP_TO_DATE (comment-only ship edit) but CHANGELOG advertises a feature -> conflict noted.
        e = self._pkg("0.4.0", changelog="## [Unreleased]\n### Added\n- undocumented-in-diff feature\n")
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.fake.tags["juniper-ml"] = ["juniper-thing-v0.4.0"]
        self.fake.compares[("juniper-ml", "juniper-thing-v0.4.0", "main")] = d.CompareResult(
            files=[_fc("juniper-thing/juniper_thing/mod.py", _COMMENT_ONLY_PATCH)],
            commits=["docs: tidy"],
        )
        rec = self._classify(e)
        self.assertEqual(rec.classification, d.UP_TO_DATE)
        self.assertIsNotNone(rec.changelog_conflict)

    def test_hygiene_flags(self):
        e = self._pkg("0.4.0")
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.fake.tags["juniper-ml"] = ["juniper-thing-v0.4.0"]
        self.fake.releases["juniper-ml"] = set()  # no GitHub Release for the tag -> TAG_ONLY
        self.fake.compares[("juniper-ml", "juniper-thing-v0.4.0", "main")] = d.CompareResult(files=[], commits=[])
        rec = self._classify(e)
        self.assertTrue(rec.hygiene["tag_only"])
        self.assertTrue(rec.hygiene["notes_missing"])  # no notes/releases/ archive on the synthetic tree


class ManifestShapeTest(unittest.TestCase):
    def test_manifest_json_shape(self):
        rec = d.PackageRecord(entry=_entry(), released_version="0.4.0", declared_version="0.4.0", classification=d.UP_TO_DATE)
        manifest = d.build_manifest([rec])
        self.assertEqual(set(manifest), {"schema", "generated_by", "summary", "packages"})
        self.assertEqual(manifest["summary"]["total"], 1)
        self.assertIn(d.UP_TO_DATE, manifest["summary"]["by_classification"])
        pkg = manifest["packages"][0]
        for key in ("pypi_name", "repo", "released_version", "declared_version", "diff_base_tag", "classification", "proposed_bump", "proposed_version", "ship_evidence", "nonship_discounted", "changelog_unreleased_categories", "hygiene", "propagation_edges"):
            self.assertIn(key, pkg, f"manifest package record missing '{key}'")
        # round-trips through JSON
        json.loads(json.dumps(manifest))


# ── CLI exit-code tests (synthetic registry + fake sources) ──────────────────


_MINI_REGISTRY = textwrap.dedent("""\
    packages:
      - pypi_name: juniper-thing
        repo: juniper-ml
        path: "juniper-thing/"
        version_source: static
        tag_pattern: "juniper-thing-v*"
        archive_name: "RELEASE_NOTES_juniper-thing_v{version}.md"
        trigger: {now: release, target: release}
        verify: {now: strict, target: strict}
        depends_on: []
        ship_paths: ["juniper-thing/juniper_thing/"]
        exclude_paths: []
    """)


class CliExitCodeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0")
        self.registry = self.root / "registry.yaml"
        self.registry.write_text(_MINI_REGISTRY)
        self.fake = _FakeSources(self.repo_root, self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, sources, *extra) -> "tuple[int, str]":
        buf = io.StringIO()
        argv = ["--repo-root", str(self.repo_root), "--ecosystem-root", str(self.root), "--registry", str(self.registry), *extra]
        with redirect_stdout(buf):
            code = d.main(argv, sources=sources)
        return code, buf.getvalue()

    def _wire_up_to_date(self):
        self.fake.pypi["juniper-thing"] = _pypi("0.4.0")
        self.fake.tags["juniper-ml"] = ["juniper-thing-v0.4.0"]
        self.fake.compares[("juniper-ml", "juniper-thing-v0.4.0", "main")] = d.CompareResult(files=[_fc("juniper-thing/README.md", "@@ -1 +1 @@\n-a\n+b")], commits=[])

    def test_exit_zero_all_up_to_date(self):
        self._wire_up_to_date()
        code, out = self._run(self.fake.build())
        self.assertEqual(code, 0)
        self.assertIn(d.UP_TO_DATE, out)

    def test_exit_zero_json_mode(self):
        self._wire_up_to_date()
        code, out = self._run(self.fake.build(), "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["summary"]["by_classification"].get(d.UP_TO_DATE), 1)

    def test_exit_one_needs_action(self):
        self.fake.pypi["juniper-thing"] = _pypi("0.5.0")  # released 0.5.0 but declared 0.4.0 -> ANOMALY (action)
        code, _ = self._run(self.fake.build())
        self.assertEqual(code, 1)

    def test_exit_two_source_error(self):
        def boom(_name):
            raise d.SourceError("network down")

        broken = d.Sources(pypi_json=boom, list_tags=lambda r: [], list_releases=lambda r: set(), compare=lambda e, b, h: d.CompareResult([], [], ok=False), read_file=self.fake.read_file)
        code, _ = self._run(broken)
        self.assertEqual(code, 2)

    def test_exit_two_empty_registry(self):
        empty = self.root / "empty.yaml"
        empty.write_text("packages: []\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = d.main(["--repo-root", str(self.repo_root), "--registry", str(empty)], sources=self.fake.build())
        self.assertEqual(code, 2)

    def test_exit_two_unknown_package(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = d.main(["--repo-root", str(self.repo_root), "--registry", str(self.registry), "--package", "nope"], sources=self.fake.build())
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
