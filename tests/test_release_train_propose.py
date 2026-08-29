#!/usr/bin/env python3
"""Hermetic regression tests for util/release_train/propose.py + notes_render.py (plan S5.4/S6/S10.1, Phase 2.1).

NO network, NO real gh, NO real pip, NO repo writes. The dup-guard ``gh pr list`` and every
file read run through an injected ``ProposeSources`` seam; version / CHANGELOG / AGENTS.md reads
run against a synthetic on-disk repo built per test (the ``test_release_train_detect.py`` idiom).
The release-notes template is copied into each synthetic tree so rendering is offline and the
"dry-run writes nothing" snapshot is self-contained.

Covers (task acceptance list):
  * a well-formed dry-run proposal for a STATIC-version package and a DYNAMIC-version package
  * CHANGELOG [Unreleased] -> [version] move correctness (fresh empty Unreleased; order preserved)
  * notes render matches the template skeleton + the archive_name convention
    (RELEASE_NOTES_<pkg>_v<version>.md, central home notes/releases/)
  * dup-guard suppression (open release PR already exists) + the -v delimiter disambiguation
  * changelog_conflict refusal path (the detector flagged an inconsistency)
  * dry-run writes NOTHING to the repo (tmpdir tree byte-identical before/after)
  * version-file editors (static pyproject / dynamic _version.py / meta AGENTS.md), propagation
    edges (MINOR escapes ceilings; PATCH does not), and CLI exit codes 0 / 2
  * in-repo meta consumer-pin co-changes (plan S5.4; closes the ml#657 RK-11 gap): an escaping MINOR
    bump emits all three lockstep edits (root pyproject.toml + tests/test_pyproject_extras.py + the
    AGENTS.md extras table) with correct raised ceilings; a non-escaping PATCH bump and a package
    absent from the extras emit ZERO co-changes + the explicit "none needed" body line; the pyproject
    edit round-trips byte-identically (only the ceiling moves); the AGENTS true-up is scoped to the
    extras table (prose / minimum-pin mentions never move) and fixes a drifted row; the meta itself
    yields no self-pin co-change; dry-run with a co-change scenario still writes nothing

``util/`` is not pre-commit-lint-gated, so this unittest IS the gate (the ``env_floor_drift_check``
precedent, shared with ``detect.py``). Imported via the house ``sys.path.insert`` idiom.

Run: python3 -m unittest -v tests/test_release_train_propose.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-07-14
"""

from __future__ import annotations

import difflib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import textwrap
import tomllib
import unittest
from collections import OrderedDict
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UTIL_DIR = REPO_ROOT / "util" / "release_train"
sys.path.insert(0, str(UTIL_DIR))

import detect as d  # noqa: E402
import notes_render as nr  # noqa: E402
import propose as pr  # noqa: E402

REAL_TEMPLATE = REPO_ROOT / "notes" / "templates" / "TEMPLATE_RELEASE_NOTES.md"
REAL_SECURITY_TEMPLATE = REPO_ROOT / "notes" / "templates" / "TEMPLATE_SECURITY_RELEASE_NOTES.md"


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


def _manifest_pkg(**over) -> dict:
    base = {
        "pypi_name": "juniper-thing",
        "repo": "juniper-ml",
        "released_version": "0.4.0",
        "declared_version": "0.4.0",
        "classification": "UNRELEASED_CHANGES",
        "proposed_bump": "minor",
        "proposed_version": "0.5.0",
        "ship_evidence": [{"file": "juniper-thing/juniper_thing/mod.py", "reason": "substantive code hunk"}],
        "changelog_unreleased_categories": ["added"],
        "changelog_conflict": None,
        "propagation_edges": [],
    }
    base.update(over)
    return base


def _write_pkg(repo_root: Path, path: str, *, name: str, version: str, changelog: str = "", dynamic: bool = False, import_pkg: str = "", dunder: bool = False) -> None:
    pkg_dir = repo_root if path == "." else repo_root / path.rstrip("/")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    if dynamic:
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{name}"\ndynamic = ["version"]\n')
        ip = import_pkg or name.replace("-", "_")
        (pkg_dir / ip).mkdir(parents=True, exist_ok=True)
        (pkg_dir / ip / "_version.py").write_text(f'"""Version."""\n__version__ = "{version}"\n')
    else:
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{name}"\nversion = "{version}"\ndescription = "x"\n')
        if dunder:
            # the ml#701 static-with-dunder shape: all five in-repo static packages also ship one.
            ip = import_pkg or name.replace("-", "_")
            (pkg_dir / ip).mkdir(parents=True, exist_ok=True)
            (pkg_dir / ip / "_version.py").write_text(f'"""Version."""\n__version__ = "{version}"\n')
    if changelog:
        (pkg_dir / "CHANGELOG.md").write_text(changelog)


def _install_templates(repo_root: Path) -> None:
    dest = repo_root / "notes" / "templates"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_TEMPLATE, dest / "TEMPLATE_RELEASE_NOTES.md")
    shutil.copy(REAL_SECURITY_TEMPLATE, dest / "TEMPLATE_SECURITY_RELEASE_NOTES.md")


# The meta-package's consumer surface the in-repo pin co-change reads + edits (root pyproject.toml,
# the tests/test_pyproject_extras.py membership contract, and the AGENTS.md "Dependency extras
# reference" table). Exercises: a single-extra ceiling pin (service-core <0.5.0), a floorless pin
# (observability, no ceiling), and a package in TWO extras (doc-tools in [tools] AND [doc-tools]).
_META_PYPROJECT = textwrap.dedent("""\
    [build-system]
    requires = ["setuptools>=61.0", "wheel"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "juniper-ml"
    version = "0.6.0"
    dependencies = []

    [project.optional-dependencies]
    tools = [
        "juniper-service-core>=0.2.0,<0.5.0",
        "juniper-model-core>=0.1.0,<0.4.0",
        "juniper-observability>=0.2.0",
        "juniper-doc-tools>=0.1.0,<0.2.0",
    ]
    doc-tools = [
        "juniper-doc-tools>=0.1.0,<0.2.0",
    ]
    all = [
        "juniper-ml[tools,doc-tools]",
    ]
    """)

_META_TEST_EXTRAS = textwrap.dedent('''\
    """Lint contract mirror (exact-string membership)."""
    EXPECTED_EXTRAS = {
        "tools": {
            "juniper-service-core>=0.2.0,<0.5.0",
            "juniper-model-core>=0.1.0,<0.4.0",
            "juniper-observability>=0.2.0",
            "juniper-doc-tools>=0.1.0,<0.2.0",
        },
        "doc-tools": {
            "juniper-doc-tools>=0.1.0,<0.2.0",
        },
        "all": {
            "juniper-ml[tools,doc-tools]",
        },
    }
    ''')

# The AGENTS table row for `tools` plus a `doc-tools` row (doc-tools in two rows) AND a prose pin
# OUTSIDE the table that must never move (the ml#657 scoping hazard: a `juniper-observability>=0.2.0`
# minimum-pin note and a `juniper-service-core` bare mention live elsewhere in the real AGENTS.md).
_META_AGENTS = textwrap.dedent("""\
    # AGENTS

    **Version**: 0.6.0

    ## Shared Observability Helpers

    Minimum pin: `juniper-observability>=0.2.0`. Do not move this prose mention.

    ### Dependency extras reference

    | Extra       | Packages                                                                                                                                              |
    |-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `tools`     | `juniper-service-core>=0.2.0,<0.5.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`            |
    | `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)                                                              |

    ## Conventions

    A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.
    """)


# A TABLE-BEARING sibling repo's AGENTS.md (ml#851) -- the real juniper-recurrence shape, trimmed:
# a per-sub-package version table (the live rows are AGENTS.md:22-24) whose cells the repo-local
# `version-drift` hook (`scripts/check_version_drift.py`, `_agents_table_version`) pins against each
# package's `_version.py`, so a proposal that moves only the **Version** header ships red there
# (juniper-recurrence#92 / #93). Also carries: the primary-tracking header (0.3.0 = the app), a
# directory cell (`juniper-recurrence/`) that must NOT read as a package mention, a same-prefix
# sibling row (`juniper-recurrence-model`) the app's needle must not match, and the prose mention
# (live AGENTS.md:118) the drift hook does NOT check and the co-change deliberately leaves alone.
_SIBLING_TABLE_AGENTS = textwrap.dedent("""\
    # AGENTS.md

    **Project**: juniper-recurrence — Recurrent / Continuous-Time Neural-Network Application
    **Repository**: pcalnon/juniper-recurrence
    **Version**: 0.3.0
    **Last Updated**: 2026-06-25

    ---

    | Sub-project | Directory | PyPI package | Version |
    |---|---|---|---|
    | Application (FastAPI + CLI service) | `juniper-recurrence/` | `juniper-recurrence` | 0.3.0 |
    | Model core (Δt-native LMU) | `juniper-recurrence-model/` | `juniper-recurrence-model` | 0.2.0 |
    | HTTP client | `juniper-recurrence-client/` | `juniper-recurrence-client` | 0.2.0 |
    | Benchmark / evaluation harness | `bench/` | _(not a package)_ | n/a |

    ## Status

    Live monorepo: the application (`juniper-recurrence` 0.3.0), the model core
    (`juniper-recurrence-model` 0.2.0), and the HTTP client (`juniper-recurrence-client` 0.2.0) are all
    published to PyPI.
    """)


def _write_meta_surface(repo_root: Path) -> None:
    """Write the meta-package's root pyproject.toml + tests/test_pyproject_extras.py + AGENTS.md so
    build_proposal's in-repo consumer-pin co-change (step 5b) can read + edit the real three files."""
    (repo_root / "pyproject.toml").write_text(_META_PYPROJECT)
    (repo_root / "tests").mkdir(parents=True, exist_ok=True)
    (repo_root / "tests" / "test_pyproject_extras.py").write_text(_META_TEST_EXTRAS)
    (repo_root / "AGENTS.md").write_text(_META_AGENTS)


_CHANGELOG = textwrap.dedent("""\
    # Changelog

    ## [Unreleased]

    ### Added

    - new validation module for the thing

    ### Fixed

    - a latent off-by-one in the parser

    ## [0.4.0] - 2026-06-01

    ### Added

    - initial release
    """)


class _FakeSources:
    """Assemble a ProposeSources with a disk-backed read_file over the synthetic tree and an
    in-memory open-PR list for the dup-guard. write/git/pr are None (dry-run/tests never mutate)."""

    def __init__(self, repo_root: Path, ecosystem_root: Path):
        self.repo_root = repo_root
        self.ecosystem_root = ecosystem_root
        self.open_prs: dict = {}

    def read_file(self, entry, filename):
        base = d.base_dir_for(entry, self.repo_root, self.ecosystem_root)
        try:
            return (base / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    def build(self) -> pr.ProposeSources:
        return pr.ProposeSources(read_file=self.read_file, list_open_prs=lambda repo: list(self.open_prs.get(repo, [])))


def _sha_tree(root: Path) -> dict:
    """relpath -> sha256 for every file under root (the writes-nothing snapshot)."""
    out: dict = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# ── notes_render ─────────────────────────────────────────────────────────────


class NotesRenderTest(unittest.TestCase):
    def test_archive_name_convention(self):
        self.assertEqual(nr.archive_name("juniper-observability", "0.4.1"), "RELEASE_NOTES_juniper-observability_v0.4.1.md")
        self.assertEqual(nr.archive_name("juniper-ml", "0.7.0"), "RELEASE_NOTES_v0.7.0.md")  # meta special-case
        self.assertEqual(nr.archive_relpath("juniper-observability", "0.4.1"), "notes/releases/RELEASE_NOTES_juniper-observability_v0.4.1.md")

    def test_parse_unreleased_groups_bullets_by_category(self):
        sections = nr.parse_unreleased(_CHANGELOG)
        self.assertEqual(list(sections), ["Added", "Fixed"])  # order + casing preserved; released 0.4.0 not included
        self.assertIn("new validation module for the thing", sections["Added"][0])
        self.assertIn("off-by-one", sections["Fixed"][0])

    def test_render_matches_template_skeleton_and_names(self):
        sections = nr.parse_unreleased(_CHANGELOG)
        text = nr.render_notes("juniper-thing", "0.5.0", bump="minor", release_date="2026-07-14", sections=sections, repo_root=REPO_ROOT)
        # metadata block + core template sections present
        self.assertIn("# juniper-thing v0.5.0 Release Notes", text)
        self.assertIn("**Release Date:** 2026-07-14", text)
        self.assertIn("**Version:** 0.5.0", text)
        self.assertIn("**Release Type:** MINOR", text)
        for heading in ("## Overview", "## Release Summary", "## What's New", "### Added", "### Fixed"):
            self.assertIn(heading, text)
        self.assertIn("new validation module for the thing", text)
        self.assertIn("notes/releases/RELEASE_NOTES_juniper-thing_v0.5.0.md", text)  # archive target named
        # skeleton conformance: every filled section is drawn from the live template's titles
        titles = nr.template_section_titles(REAL_TEMPLATE.read_text(encoding="utf-8"))
        for key in nr.STANDARD_FILLED_SECTIONS:
            self.assertTrue(any(t.startswith(key) for t in titles), f"filled section {key!r} not in template titles {titles}")

    def test_rewrite_relative_links_shapes(self):
        base = "https://github.com/pcalnon/juniper-canopy/blob/v0.6.0"
        fn = nr.rewrite_relative_links
        # plain relative + ./-normalized + anchor-on-path preserved + markdown title kept
        self.assertEqual(fn("[a](notes/X.md)", base), f"[a]({base}/notes/X.md)")
        self.assertEqual(fn("[a](./notes/X.md#sec)", base), f"[a]({base}/notes/X.md#sec)")
        self.assertEqual(fn('[a](docs/Y.md "Title")', base), f'[a]({base}/docs/Y.md "Title")')
        # untouched classes: absolute, mailto, bare anchor, protocol-relative
        for text in ("[a](https://x.invalid/p)", "[a](mailto:x@y.z)", "[a](#local)", "[a](//cdn.invalid/p)"):
            self.assertEqual(fn(text, base), text)

    def test_render_notes_link_base_rewrites_bullets_only_when_given(self):
        sections = OrderedDict([("Fixed", ["a bug ([design](notes/D.md); see [abs](https://x.invalid))"])])
        base = "https://github.com/pcalnon/juniper-canopy/blob/v0.6.0"
        with_base = nr.render_notes("juniper-canopy", "0.6.0", bump="minor", release_date="2026-07-30", sections=sections, repo_root=REPO_ROOT, link_base=base)
        self.assertIn(f"[design]({base}/notes/D.md)", with_base)
        self.assertIn("[abs](https://x.invalid)", with_base)
        without = nr.render_notes("juniper-canopy", "0.6.0", bump="minor", release_date="2026-07-30", sections=sections, repo_root=REPO_ROOT)
        self.assertIn("[design](notes/D.md)", without)  # back-compat: no link_base, no rewrite

    def test_security_release_uses_security_template(self):
        sections = OrderedDict([("Security", ["patched a transitive CVE"]), ("Fixed", ["a bug"])])
        self.assertTrue(nr.is_security_release(sections))
        text = nr.render_notes("juniper-thing", "0.4.1", bump="patch", release_date="2026-07-14", sections=sections, repo_root=REPO_ROOT)
        self.assertIn(":lock: SECURITY PATCH RELEASE", text)
        self.assertIn("## Security Impact", text)
        self.assertIn("## Changes in v0.4.1", text)
        self.assertIn("patched a transitive CVE", text)
        sec_titles = nr.template_section_titles(REAL_SECURITY_TEMPLATE.read_text(encoding="utf-8"))
        for key in nr.SECURITY_FILLED_SECTIONS:
            self.assertTrue(any(t.startswith(key) for t in sec_titles), f"security filled section {key!r} not in {sec_titles}")

    def test_render_wellformed_without_changelog(self):
        text = nr.render_notes("juniper-thing", "0.5.0", release_date="2026-07-14", sections=OrderedDict(), repo_root=REPO_ROOT)
        self.assertIn("# juniper-thing v0.5.0 Release Notes", text)
        self.assertIn("## What's New", text)  # still well-formed with a placeholder body

    def test_cli_print_archive_name(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = nr.main(["--package", "juniper-thing", "--version", "0.5.0", "--print-archive-name"])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "notes/releases/RELEASE_NOTES_juniper-thing_v0.5.0.md")

    def test_display_name_meta_is_juniper_ml(self):
        # Meta-package title stem is humanized; every other dist name passes through.
        self.assertEqual(nr.display_name("juniper-ml"), "Juniper ML")
        self.assertEqual(nr.display_name("juniper-thing"), "juniper-thing")

    def test_release_type_major_and_unknown_default(self):
        self.assertEqual(nr.release_type("major"), "MAJOR")
        self.assertEqual(nr.release_type("minor"), "MINOR")
        self.assertEqual(nr.release_type("patch"), "PATCH")
        self.assertEqual(nr.release_type("none"), "PATCH")
        self.assertEqual(nr.release_type("unexpected"), "PATCH")  # defensive default

    def test_render_meta_major_marks_breaking_on_removed(self):
        # MAJOR + Removed => title uses "Juniper ML", Release Type MAJOR, Breaking YES.
        sections = OrderedDict([("Removed", ["dropped the legacy CLI entrypoint"]), ("Fixed", ["typo in help text"])])
        text = nr.render_notes(
            "juniper-ml",
            "1.0.0",
            bump="major",
            release_date="2026-07-26",
            sections=sections,
            repo_root=REPO_ROOT,
        )
        self.assertIn("# Juniper ML v1.0.0 Release Notes", text)
        self.assertIn("**Release Type:** MAJOR", text)
        self.assertIn("**Breaking changes:** YES", text)
        self.assertIn("dropped the legacy CLI entrypoint", text)
        # Without a Removed category the Breaking flag stays NO (regression guard for the
        # case-insensitive membership check over section keys).
        no_break = nr.render_notes(
            "juniper-thing",
            "0.5.0",
            bump="minor",
            release_date="2026-07-26",
            sections=OrderedDict([("Added", ["a feature"])]),
            repo_root=REPO_ROOT,
        )
        self.assertIn("**Breaking changes:** NO", no_break)

    def test_split_bullets_star_markers_and_continuations(self):
        # Keep-a-Changelog allows ``*`` as well as ``-``; continuations fold into the
        # current bullet, and stray prose before any marker is ignored.
        body = [
            "stray prose before markers is ignored",
            "* first star bullet",
            "  continuation of first",
            "* second star",
            "- dash bullet",
            "    indented continuation",
            "bare prose joins current",
        ]
        bullets = nr._split_bullets(body)
        self.assertEqual(len(bullets), 3)
        self.assertIn("first star bullet", bullets[0])
        self.assertIn("continuation of first", bullets[0])
        self.assertEqual(bullets[1], "second star")
        self.assertIn("dash bullet", bullets[2])
        self.assertIn("indented continuation", bullets[2])
        self.assertIn("bare prose joins current", bullets[2])
        # End-to-end: parse_unreleased must accept ``*`` markers and fold continuations.
        changelog = textwrap.dedent("""\
            ## [Unreleased]

            ### Added

            * star item
              folded line

            * another

            ## [0.1.0] - 2026-01-01
            """)
        sections = nr.parse_unreleased(changelog)
        self.assertEqual(list(sections), ["Added"])
        self.assertEqual(len(sections["Added"]), 2)
        self.assertIn("star item", sections["Added"][0])
        self.assertIn("folded line", sections["Added"][0])
        self.assertEqual(sections["Added"][1], "another")


# ── CHANGELOG move ───────────────────────────────────────────────────────────


class ChangelogMoveTest(unittest.TestCase):
    def test_move_unreleased_correctness(self):
        new_text, reason = pr.move_unreleased(_CHANGELOG, "0.5.0", "2026-07-14")
        self.assertIsNone(reason)
        self.assertIsNotNone(new_text)
        # a fresh empty [Unreleased] remains, a new dated version section is inserted below it
        self.assertIn("## [Unreleased]", new_text)
        self.assertIn("## [0.5.0] - 2026-07-14", new_text)
        # ordering: Unreleased header < new version header < moved bullet < prior 0.4.0 section
        i_unrel = new_text.index("## [Unreleased]")
        i_new = new_text.index("## [0.5.0] - 2026-07-14")
        i_bullet = new_text.index("new validation module for the thing")
        i_old = new_text.index("## [0.4.0] - 2026-06-01")
        self.assertLess(i_unrel, i_new)
        self.assertLess(i_new, i_bullet)
        self.assertLess(i_bullet, i_old)
        # the moved bullet no longer sits inside the (now empty) [Unreleased] block
        unreleased_block = new_text[i_unrel:i_new]
        self.assertNotIn("new validation module", unreleased_block)

    def test_move_refuses_without_unreleased_heading(self):
        _, reason = pr.move_unreleased("# Changelog\n\n## [0.4.0] - 2026-06-01\n- x\n", "0.5.0", "2026-07-14")
        self.assertIsNotNone(reason)

    def test_move_refuses_empty_unreleased(self):
        _, reason = pr.move_unreleased("# Changelog\n\n## [Unreleased]\n\n## [0.4.0] - 2026-06-01\n- x\n", "0.5.0", "2026-07-14")
        self.assertIsNotNone(reason)


# ── version-file editors ─────────────────────────────────────────────────────


class VersionEditTest(unittest.TestCase):
    def test_dunder_file_rel_joins_path_and_import_package(self):
        entry = _entry(path="juniper-ci-tools/", pypi_name="juniper-ci-tools", ship_paths=["juniper-ci-tools/juniper_ci_tools/"])
        self.assertEqual(pr.dunder_file_rel(entry), "juniper-ci-tools/juniper_ci_tools/_version.py")
        # path="." must not leave a leading "./" that would desync from sources.read_file keys
        meta = _entry(pypi_name="juniper-ml", path=".", ship_paths=[])
        self.assertEqual(pr.dunder_file_rel(meta), "juniper_ml/_version.py")

    def test_dunder_cochange_rel_ignores_dynamic_edits0_and_finds_later(self):
        # dynamic: edits[0] IS the _version.py bump -- never a "co-change"
        dyn = pr.Proposal(pypi_name="juniper-model-core", repo="juniper-ml", from_version="0.3.0", to_version="0.4.0", bump="minor")
        dyn.edits = [pr.FileEdit(path="juniper-model-core/juniper_model_core/_version.py", old_text="a", new_text="b")]
        self.assertIsNone(pr.dunder_cochange_rel(dyn))
        # static-with-dunder: the lockstep edit is later than edits[0]
        static = pr.Proposal(pypi_name="juniper-thing", repo="juniper-ml", from_version="0.4.0", to_version="0.5.0", bump="minor")
        static.edits = [
            pr.FileEdit(path="juniper-thing/pyproject.toml", old_text="a", new_text="b"),
            pr.FileEdit(path="juniper-thing/juniper_thing/_version.py", old_text="c", new_text="d"),
            pr.FileEdit(path="juniper-thing/CHANGELOG.md", old_text="e", new_text="f"),
        ]
        self.assertEqual(pr.dunder_cochange_rel(static), "juniper-thing/juniper_thing/_version.py")
        # no later _version.py -> None (static-without-dunder)
        bare = pr.Proposal(pypi_name="juniper-thing", repo="juniper-ml", from_version="0.4.0", to_version="0.5.0", bump="minor")
        bare.edits = [
            pr.FileEdit(path="juniper-thing/pyproject.toml", old_text="a", new_text="b"),
            pr.FileEdit(path="juniper-thing/CHANGELOG.md", old_text="e", new_text="f"),
        ]
        self.assertIsNone(pr.dunder_cochange_rel(bare))

    def test_co_change_checklist_dunder_states(self):
        entry = _entry()
        included = pr._co_change_checklist(entry, "minor", [], False, [], dunder_rel="pkg/_version.py", dunder_edited=True)
        self.assertTrue(any("included in this PR" in item and "_version.py" in item for item in included))
        required = pr._co_change_checklist(entry, "minor", [], False, [], dunder_rel="pkg/_version.py", dunder_edited=False)
        self.assertTrue(any("REQUIRED" in item and "_version.py" in item for item in required))
        absent = pr._co_change_checklist(entry, "minor", [], False, [])
        self.assertFalse(any("_version.py" in item for item in absent))

    def test_set_pyproject_version(self):
        text = '[build-system]\nrequires = ["setuptools"]\n\n[project]\nname = "x"\nversion = "0.4.0"\n'
        new_text, old = pr.set_pyproject_version(text, "0.5.0")
        self.assertEqual(old, "0.4.0")
        self.assertIn('version = "0.5.0"', new_text)
        self.assertNotIn('version = "0.4.0"', new_text)

    def test_set_pyproject_version_ignores_other_tables(self):
        # a [tool.poetry] version must not be the one edited; only [project].
        text = '[project]\nname = "x"\nversion = "0.4.0"\n\n[tool.black]\nversion = "should-not-touch"\n'
        new_text, old = pr.set_pyproject_version(text, "0.5.0")
        self.assertEqual(old, "0.4.0")
        self.assertIn('version = "should-not-touch"', new_text)

    def test_set_dynamic_version(self):
        text = '"""m."""\n__version__ = "0.3.0"\n'
        new_text, old = pr.set_dynamic_version(text, "0.4.0")
        self.assertEqual(old, "0.3.0")
        self.assertIn('__version__ = "0.4.0"', new_text)

    def test_set_agents_version(self):
        text = "# AGENTS\n\n**Version**: 0.6.0\n**Author**: x\n"
        new_text, old = pr.set_agents_version(text, "0.7.0")
        self.assertEqual(old, "0.6.0")
        self.assertIn("**Version**: 0.7.0", new_text)

    def test_editors_return_none_when_absent(self):
        self.assertIsNone(pr.set_pyproject_version('[project]\nname = "x"\n', "0.5.0")[1])
        self.assertIsNone(pr.set_dynamic_version("x = 1\n", "0.5.0")[1])
        self.assertIsNone(pr.set_agents_version("no header\n", "0.5.0")[1])


# ── dup-guard + propagation ──────────────────────────────────────────────────


class DupGuardAndPropagationTest(unittest.TestCase):
    def test_find_existing_release_pr_matches_package_branch(self):
        prs = [{"number": 7, "headRefName": "release/juniper-thing-v0.9.0", "title": "release: thing"}]
        self.assertIsNotNone(pr.find_existing_release_pr(prs, "juniper-thing"))

    def test_dup_guard_delimiter_disambiguates_siblings(self):
        # an open cascor release PR must NOT dup-guard cascor-model (the -v delimiter).
        prs = [{"number": 8, "headRefName": "release/juniper-cascor-v0.5.1"}]
        self.assertIsNone(pr.find_existing_release_pr(prs, "juniper-cascor-model"))
        self.assertIsNotNone(pr.find_existing_release_pr(prs, "juniper-cascor"))

    def test_propagation_minor_lists_consumers_patch_does_not(self):
        entries = [
            _entry(pypi_name="juniper-model-core", path="juniper-model-core/"),
            _entry(pypi_name="juniper-service-core", path="juniper-service-core/", depends_on=["juniper-model-core"]),
            _entry(pypi_name="juniper-recurrence-model", path="rm/", depends_on=["juniper-model-core"]),
        ]
        mc = entries[0]
        minor = pr.propagation_edges(entries, mc, "minor")
        self.assertEqual({e["consumer"] for e in minor}, {"juniper-service-core", "juniper-recurrence-model"})
        self.assertEqual(pr.propagation_edges(entries, mc, "patch"), [])  # PATCH stays within ceilings


# ── build_proposal: static / dynamic dry-run + refusals ──────────────────────


class BuildProposalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        self.eco = self.root
        self.fake = _FakeSources(self.repo_root, self.eco)

    def tearDown(self):
        self._tmp.cleanup()

    def test_static_package_dry_run_is_wellformed(self):
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.branch, "release/juniper-thing-v0.5.0")
        self.assertEqual(prop.pr_title, "release: juniper-thing v0.5.0 (proposal)")
        self.assertIn("chore(release): juniper-thing v0.5.0", prop.commit_message)
        paths = {e.path for e in prop.edits}
        self.assertIn("juniper-thing/pyproject.toml", paths)
        self.assertIn("juniper-thing/CHANGELOG.md", paths)
        vedit = next(e for e in prop.edits if e.path == "juniper-thing/pyproject.toml")
        self.assertIn('version = "0.5.0"', vedit.new_text)
        self.assertIn('version = "0.4.0"', vedit.old_text)
        self.assertEqual(prop.notes_relpath, "notes/releases/RELEASE_NOTES_juniper-thing_v0.5.0.md")
        self.assertIn("# juniper-thing v0.5.0 Release Notes", prop.notes_draft or "")
        self.assertIn("Release proposal", prop.pr_body or "")
        # the drafted notes are NOT presented as a repo edit (archival is the later exempt step)
        self.assertNotIn(prop.notes_relpath, paths)

    def test_notes_draft_rewrites_relative_links_onto_owning_repo_blob_main(self):
        # Gate-1 / central-archive correctness (canopy v0.6.0 class; juniper-ml#877): propose must
        # rewrite CHANGELOG-sourced relative links onto the owning repo's blob/main URL so a draft
        # reviewed outside that repo (or later archived under juniper-ml notes/releases/) does not
        # 404. Ceremony pins the tag-blob form separately; this pins the propose call-site default.
        clog = textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Fixed

            - a latent off-by-one ([design](notes/DESIGN.md), [ext](https://example.invalid/x)).

            ## [0.4.0] - 2026-06-01

            ### Added

            - initial release
            """)
        # Sibling primary package: entry.repo must appear in the rewritten base (not hardcoded ml).
        sib_root = self.eco / "juniper-canopy"
        _write_pkg(sib_root, ".", name="juniper-canopy", version="0.4.0", changelog=clog)
        entry = _entry(
            pypi_name="juniper-canopy",
            repo="juniper-canopy",
            path=".",
            tag_pattern="juniper-canopy-v*",
            archive_name="RELEASE_NOTES_juniper-canopy_v{version}.md",
            ship_paths=["juniper_canopy/"],
        )
        pkg = _manifest_pkg(
            pypi_name="juniper-canopy",
            repo="juniper-canopy",
            released_version="0.4.0",
            declared_version="0.4.0",
            proposed_version="0.5.0",
        )
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        draft = prop.notes_draft or ""
        base = f"https://github.com/{pr.DEFAULT_OWNER}/juniper-canopy/blob/main"
        self.assertIn(f"[design]({base}/notes/DESIGN.md)", draft)
        self.assertNotIn("](notes/DESIGN.md)", draft)
        self.assertIn("[ext](https://example.invalid/x)", draft)  # absolute untouched
        # Propose must NOT use the ceremony tag-pinned form.
        self.assertNotIn("/blob/juniper-canopy-v0.5.0/", draft)

    def test_in_repo_notes_draft_uses_meta_repo_blob_main(self):
        # In-repo sub-package: owning checkout is juniper-ml, so link_base must be ml's blob/main
        # (not the pypi_name, and not a phantom sibling URL).
        clog = textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Added

            - new helper ([design](./notes/HELPER.md#api)).

            ## [0.4.0] - 2026-06-01

            ### Added

            - initial release
            """)
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=clog)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        draft = prop.notes_draft or ""
        base = f"https://github.com/{pr.DEFAULT_OWNER}/juniper-ml/blob/main"
        self.assertIn(f"[design]({base}/notes/HELPER.md#api)", draft)
        self.assertNotIn("](./notes/HELPER.md", draft)

    def test_dynamic_package_edits_version_file(self):
        _write_pkg(self.repo_root, "juniper-model-core/", name="juniper-model-core", version="0.3.0", changelog=_CHANGELOG, dynamic=True, import_pkg="juniper_model_core")
        entry = _entry(pypi_name="juniper-model-core", path="juniper-model-core/", version_source="dynamic", tag_pattern="juniper-model-core-v*", archive_name="RELEASE_NOTES_juniper-model-core_v{version}.md", ship_paths=["juniper-model-core/juniper_model_core/"])
        pkg = _manifest_pkg(pypi_name="juniper-model-core", released_version="0.3.0", declared_version="0.3.0", proposed_version="0.4.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        vpath = "juniper-model-core/juniper_model_core/_version.py"
        vedit = next(e for e in prop.edits if e.path == vpath)
        self.assertIn('__version__ = "0.4.0"', vedit.new_text)
        self.assertNotIn('__version__ = "0.3.0"', vedit.new_text)

    def test_static_with_dunder_bumps_both_files_in_lockstep(self):
        # ml#701: a static-version package that ALSO ships a _version.py dunder must have BOTH files
        # bumped in ONE proposal -- the ci-tools 0.7.0 / service-core 0.5.0 stale-dunder class (the
        # shipped wheel's metadata was right while its __version__ lied).
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG, dunder=True)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        paths = {e.path for e in prop.edits}
        self.assertIn("juniper-thing/pyproject.toml", paths)
        self.assertIn("juniper-thing/juniper_thing/_version.py", paths)
        vedit = next(e for e in prop.edits if e.path == "juniper-thing/pyproject.toml")
        self.assertIn('version = "0.5.0"', vedit.new_text)
        dedit = next(e for e in prop.edits if e.path == "juniper-thing/juniper_thing/_version.py")
        self.assertIn('__version__ = "0.5.0"', dedit.new_text)
        self.assertNotIn('__version__ = "0.4.0"', dedit.new_text)
        # the co-change is NAMED in the proposal body and the S5.4 checklist (like the AGENTS.md one)
        self.assertIn("juniper-thing/juniper_thing/_version.py", prop.pr_body or "")
        self.assertIn("Lockstep `__version__` dunder co-change", prop.pr_body or "")
        self.assertTrue(any("_version.py" in item and "included in this PR" in item for item in prop.co_change_checklist))

    def test_static_without_dunder_emits_no_phantom_version_py_edit(self):
        # a static package with NO _version.py gets exactly the pyproject bump -- no phantom edit,
        # no dunder checklist item, no body mention.
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual([e.path for e in prop.edits if e.path.endswith("_version.py")], [])
        self.assertFalse(any("_version.py" in item for item in prop.co_change_checklist))
        self.assertNotIn("Lockstep `__version__` dunder co-change", prop.pr_body or "")

    def test_dynamic_package_version_py_path_is_unchanged_by_lockstep(self):
        # the dynamic path is UNTOUCHED by ml#701: exactly one _version.py edit (the bump itself),
        # no pyproject edit, and no dunder co-change surfacing.
        _write_pkg(self.repo_root, "juniper-model-core/", name="juniper-model-core", version="0.3.0", changelog=_CHANGELOG, dynamic=True, import_pkg="juniper_model_core")
        entry = _entry(pypi_name="juniper-model-core", path="juniper-model-core/", version_source="dynamic", tag_pattern="juniper-model-core-v*", archive_name="RELEASE_NOTES_juniper-model-core_v{version}.md", ship_paths=["juniper-model-core/juniper_model_core/"])
        pkg = _manifest_pkg(pypi_name="juniper-model-core", released_version="0.3.0", declared_version="0.3.0", proposed_version="0.4.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        version_py_edits = [e.path for e in prop.edits if e.path.endswith("_version.py")]
        self.assertEqual(version_py_edits, ["juniper-model-core/juniper_model_core/_version.py"])
        self.assertNotIn("juniper-model-core/pyproject.toml", {e.path for e in prop.edits})
        self.assertFalse(any("_version.py" in item for item in prop.co_change_checklist))
        self.assertNotIn("Lockstep `__version__` dunder co-change", prop.pr_body or "")

    def test_static_with_unparseable_dunder_flags_required_manual(self):
        # a present-but-unparseable dunder is never guessed at: no edit, checklist REQUIRED-manual
        # (the sibling-AGENTS.md unexpected-header precedent).
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG, dunder=True)
        (self.repo_root / "juniper-thing" / "juniper_thing" / "_version.py").write_text('"""No dunder assignment here."""\nVERSION = (0, 4, 0)\n')
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual([e.path for e in prop.edits if e.path.endswith("_version.py")], [])
        self.assertTrue(any("_version.py" in item and "REQUIRED" in item for item in prop.co_change_checklist))
        # body must NOT claim a lockstep co-change was performed when no edit landed
        self.assertNotIn("Lockstep `__version__` dunder co-change", prop.pr_body or "")

    def test_static_dunder_already_at_target_is_silent_success(self):
        # if the dunder is already at the proposed version (partial heal / re-entry), do NOT emit a
        # phantom edit and do NOT flag REQUIRED-manual -- that false alarm is worse than silence.
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG, dunder=True)
        (self.repo_root / "juniper-thing" / "juniper_thing" / "_version.py").write_text('"""Version."""\n__version__ = "0.5.0"\n')
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual([e.path for e in prop.edits if e.path.endswith("_version.py")], [])
        self.assertFalse(any("_version.py" in item and "REQUIRED" in item for item in prop.co_change_checklist))
        self.assertNotIn("Lockstep `__version__` dunder co-change", prop.pr_body or "")

    def test_static_with_single_quoted_dunder_bumps_in_lockstep(self):
        # set_dynamic_version accepts either quote style; the lockstep path must not silently skip
        # a single-quoted assignment (would re-create the stale-dunder class for that shape).
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG, dunder=True)
        (self.repo_root / "juniper-thing" / "juniper_thing" / "_version.py").write_text("'''Version.'''\n__version__ = '0.4.0'\n")
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        dedit = next(e for e in prop.edits if e.path.endswith("_version.py"))
        self.assertIn("__version__ = '0.5.0'", dedit.new_text)
        self.assertNotIn("__version__ = '0.4.0'", dedit.new_text)

    def test_static_dunder_edit_precedes_changelog_in_edits(self):
        # dunder_cochange_rel scans edits[1:] for the first *_version.py; the lockstep FileEdit must
        # land immediately after the pyproject bump (edits[0]) and before CHANGELOG / other co-changes.
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG, dunder=True)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertGreaterEqual(len(prop.edits), 3)
        self.assertEqual(prop.edits[0].path, "juniper-thing/pyproject.toml")
        self.assertEqual(prop.edits[1].path, "juniper-thing/juniper_thing/_version.py")
        self.assertEqual(prop.edits[2].path, "juniper-thing/CHANGELOG.md")
        self.assertEqual(pr.dunder_cochange_rel(prop), "juniper-thing/juniper_thing/_version.py")

    def test_meta_package_co_changes_agents_md(self):
        _write_pkg(self.repo_root, ".", name="juniper-ml", version="0.6.0", changelog=_CHANGELOG)
        (self.repo_root / "AGENTS.md").write_text("# AGENTS\n\n**Version**: 0.6.0\n**Author**: Paul\n")
        entry = _entry(pypi_name="juniper-ml", path=".", tag_pattern="v*", archive_name="RELEASE_NOTES_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-ml", released_version="0.6.0", declared_version="0.6.0", proposed_version="0.7.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        agents = next((e for e in prop.edits if e.path == "AGENTS.md"), None)
        self.assertIsNotNone(agents, "meta bump must co-change AGENTS.md **Version**")
        self.assertIn("**Version**: 0.7.0", agents.new_text)
        self.assertTrue(any("AGENTS.md" in item for item in prop.co_change_checklist))

    def test_sibling_primary_package_co_changes_agents_md(self):
        # worker#140 pilot failure class: a sibling repo's AGENTS.md **Version** header tracks that
        # repo's PRIMARY package (pypi_name == repo), and the portable version-drift lint fails the
        # proposal PR unless the header moves in the same PR.
        sib_root = self.eco / "juniper-worker"
        _write_pkg(sib_root, ".", name="juniper-worker", version="0.4.0", changelog=_CHANGELOG)
        (sib_root / "AGENTS.md").write_text("# AGENTS\n\n**Version**: 0.4.0\n**Author**: Paul\n")
        entry = _entry(pypi_name="juniper-worker", repo="juniper-worker", path=".", tag_pattern="juniper-worker-v*", archive_name="RELEASE_NOTES_juniper-worker_v{version}.md", ship_paths=["juniper_worker/"])
        pkg = _manifest_pkg(pypi_name="juniper-worker", released_version="0.4.0", declared_version="0.4.0", proposed_version="0.5.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        agents = next((e for e in prop.edits if e.path == "AGENTS.md"), None)
        self.assertIsNotNone(agents, "sibling primary-package bump must co-change its AGENTS.md **Version**")
        self.assertIn("**Version**: 0.5.0", agents.new_text)
        self.assertTrue(any("Sibling AGENTS.md" in item and "included in this PR" in item for item in prop.co_change_checklist))

    def test_sibling_subpackage_never_touches_host_agents_md(self):
        # A sub-package hosted in a sibling repo (pypi_name != repo) must NOT edit the host repo's
        # AGENTS.md header -- it tracks the primary package, not the sub-package.
        sib_root = self.eco / "juniper-host"
        _write_pkg(sib_root, "juniper-host-model/", name="juniper-host-model", version="0.1.0", changelog=_CHANGELOG)
        (sib_root / "AGENTS.md").write_text("# AGENTS\n\n**Version**: 3.3.3\n")
        entry = _entry(pypi_name="juniper-host-model", repo="juniper-host", path="juniper-host-model/", tag_pattern="juniper-host-model-v*", archive_name="RELEASE_NOTES_juniper-host-model_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-host-model", released_version="0.1.0", declared_version="0.1.0", proposed_version="0.2.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertNotIn("AGENTS.md", {e.path for e in prop.edits})
        self.assertFalse(any("Sibling AGENTS.md" in item for item in prop.co_change_checklist))

    def test_sibling_agents_md_unexpected_header_left_untouched(self):
        # A header NOT at the expected from-version is never clobbered; the checklist flags it
        # REQUIRED-manual instead.
        sib_root = self.eco / "juniper-worker"
        _write_pkg(sib_root, ".", name="juniper-worker", version="0.4.0", changelog=_CHANGELOG)
        (sib_root / "AGENTS.md").write_text("# AGENTS\n\n**Version**: 9.9.9\n")
        entry = _entry(pypi_name="juniper-worker", repo="juniper-worker", path=".", tag_pattern="juniper-worker-v*", archive_name="RELEASE_NOTES_juniper-worker_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-worker", released_version="0.4.0", declared_version="0.4.0", proposed_version="0.5.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertNotIn("AGENTS.md", {e.path for e in prop.edits})
        self.assertTrue(any("Sibling AGENTS.md" in item and "REQUIRED" in item for item in prop.co_change_checklist))

    def test_sibling_agents_md_absent_flags_required_manual(self):
        # Missing AGENTS.md must not crash the proposal; surface REQUIRED so the owner notices
        # before the portable version-drift lint fails the opened PR (worker#140 class).
        sib_root = self.eco / "juniper-worker"
        _write_pkg(sib_root, ".", name="juniper-worker", version="0.4.0", changelog=_CHANGELOG)
        self.assertFalse((sib_root / "AGENTS.md").exists())
        entry = _entry(pypi_name="juniper-worker", repo="juniper-worker", path=".", tag_pattern="juniper-worker-v*", archive_name="RELEASE_NOTES_juniper-worker_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-worker", released_version="0.4.0", declared_version="0.4.0", proposed_version="0.5.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertNotIn("AGENTS.md", {e.path for e in prop.edits})
        self.assertTrue(any("Sibling AGENTS.md" in item and "REQUIRED" in item for item in prop.co_change_checklist))

    def test_sibling_agents_md_already_at_target_is_silent_success(self):
        # Header already at to_version (partial heal / re-entry) must not false-flag REQUIRED —
        # the portable lint is already satisfied; same silent-success class as the ml#701 dunder fix.
        sib_root = self.eco / "juniper-worker"
        _write_pkg(sib_root, ".", name="juniper-worker", version="0.4.0", changelog=_CHANGELOG)
        (sib_root / "AGENTS.md").write_text("# AGENTS\n\n**Version**: 0.5.0\n**Author**: Paul\n")
        entry = _entry(pypi_name="juniper-worker", repo="juniper-worker", path=".", tag_pattern="juniper-worker-v*", archive_name="RELEASE_NOTES_juniper-worker_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-worker", released_version="0.4.0", declared_version="0.4.0", proposed_version="0.5.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertNotIn("AGENTS.md", {e.path for e in prop.edits})
        self.assertFalse(any("Sibling AGENTS.md" in item and "REQUIRED" in item for item in prop.co_change_checklist))
        self.assertFalse(any("Sibling AGENTS.md" in item for item in prop.co_change_checklist))

    def test_sibling_agents_md_missing_version_header_flags_required(self):
        # AGENTS.md present but without a **Version** line: never invent a header; REQUIRED-manual.
        sib_root = self.eco / "juniper-worker"
        _write_pkg(sib_root, ".", name="juniper-worker", version="0.4.0", changelog=_CHANGELOG)
        (sib_root / "AGENTS.md").write_text("# AGENTS\n\n**Author**: Paul\n")
        entry = _entry(pypi_name="juniper-worker", repo="juniper-worker", path=".", tag_pattern="juniper-worker-v*", archive_name="RELEASE_NOTES_juniper-worker_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-worker", released_version="0.4.0", declared_version="0.4.0", proposed_version="0.5.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertNotIn("AGENTS.md", {e.path for e in prop.edits})
        self.assertTrue(any("Sibling AGENTS.md" in item and "REQUIRED" in item for item in prop.co_change_checklist))

    def test_meta_agents_md_already_at_target_is_silent_success(self):
        # Meta AGENTS.md already at to_version must not false-REQUIRED (partial heal / re-entry).
        _write_pkg(self.repo_root, ".", name="juniper-ml", version="0.6.0", changelog=_CHANGELOG)
        (self.repo_root / "AGENTS.md").write_text("# AGENTS\n\n**Version**: 0.7.0\n**Author**: Paul\n")
        entry = _entry(pypi_name="juniper-ml", path=".", tag_pattern="v*", archive_name="RELEASE_NOTES_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-ml", released_version="0.6.0", declared_version="0.6.0", proposed_version="0.7.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertNotIn("AGENTS.md", {e.path for e in prop.edits})
        self.assertFalse(any("AGENTS.md **Version**" in item and "REQUIRED" in item for item in prop.co_change_checklist))
        self.assertFalse(any("AGENTS.md **Version** header bump" in item for item in prop.co_change_checklist))

    def test_meta_agents_md_absent_flags_required_manual(self):
        # Meta bump with no AGENTS.md: proposal proceeds, checklist REQUIRED (drift lint would fail).
        _write_pkg(self.repo_root, ".", name="juniper-ml", version="0.6.0", changelog=_CHANGELOG)
        self.assertFalse((self.repo_root / "AGENTS.md").exists())
        entry = _entry(pypi_name="juniper-ml", path=".", tag_pattern="v*", archive_name="RELEASE_NOTES_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-ml", released_version="0.6.0", declared_version="0.6.0", proposed_version="0.7.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertNotIn("AGENTS.md", {e.path for e in prop.edits})
        self.assertTrue(any("AGENTS.md **Version**" in item and "REQUIRED" in item for item in prop.co_change_checklist))

    def test_minor_bump_emits_propagation_checklist_item(self):
        _write_pkg(self.repo_root, "juniper-model-core/", name="juniper-model-core", version="0.3.0", changelog=_CHANGELOG, dynamic=True, import_pkg="juniper_model_core")
        mc = _entry(pypi_name="juniper-model-core", path="juniper-model-core/", version_source="dynamic")
        consumer = _entry(pypi_name="juniper-service-core", path="juniper-service-core/", depends_on=["juniper-model-core"])
        pkg = _manifest_pkg(pypi_name="juniper-model-core", released_version="0.3.0", declared_version="0.3.0", proposed_version="0.4.0")
        prop = pr.build_proposal(mc, pkg, self.fake.build(), self.repo_root, self.eco, [mc, consumer], "2026-07-14")
        self.assertEqual({e["consumer"] for e in prop.propagation_edges}, {"juniper-service-core"})
        self.assertTrue(any("propagation" in item.lower() for item in prop.co_change_checklist))

    def test_dup_guard_suppresses_proposal(self):
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        self.fake.open_prs["juniper-ml"] = [{"number": 42, "headRefName": "release/juniper-thing-v0.5.0", "title": "release: thing"}]
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("dup-guard", prop.skipped_reason)
        self.assertEqual(prop.edits, [])  # nothing computed once suppressed
        self.assertIsNotNone(prop.existing_pr)

    def test_changelog_conflict_is_refused(self):
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        entry = _entry()
        pkg = _manifest_pkg(changelog_conflict="UNRELEASED_CHANGES but CHANGELOG [Unreleased] has no feature/fix bullets")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("changelog conflict", prop.skipped_reason)
        self.assertEqual(prop.edits, [])

    def test_changelog_move_refused_clears_staged_edits(self):
        """``move_unreleased`` refusal (empty [Unreleased]) must clear any version
        bump staged before the move — open #749 pins the skip/reason; this pins
        the clear-on-refuse stub shape (edits=[], no branch) so JSON/operators
        never see a half-proposal."""
        empty_unreleased = textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ## [0.4.0] - 2026-06-01

            ### Added

            - initial release
            """)
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=empty_unreleased)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("CHANGELOG move refused", prop.skipped_reason)
        self.assertIn("[Unreleased] section has no content to move", prop.skipped_reason)
        self.assertEqual(prop.edits, [])
        self.assertIsNone(prop.branch)

    def test_bump_none_is_refused(self):
        """No proposable SemVer bump must refuse before any edit is computed (plan S5.4)."""
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        entry = _entry()
        pkg = _manifest_pkg(proposed_bump="none", proposed_version=None)
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("no proposable version", prop.skipped_reason)
        self.assertIn("bump=none", prop.skipped_reason)
        self.assertEqual(prop.edits, [])

    def test_unreadable_version_file_is_refused(self):
        """Missing pyproject / _version.py must refuse (cannot invent a bump target)."""
        # CHANGELOG alone -- version file absent so read_file returns None.
        pkg_dir = self.repo_root / "juniper-thing"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "CHANGELOG.md").write_text(_CHANGELOG)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("could not read the version file", prop.skipped_reason)
        self.assertEqual(prop.edits, [])

    def test_unparseable_version_assignment_is_refused(self):
        """A present version file without a locatable assignment must refuse (not invent a rewrite)."""
        pkg_dir = self.repo_root / "juniper-thing"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text('[project]\nname = "juniper-thing"\ndescription = "no version key"\n')
        (pkg_dir / "CHANGELOG.md").write_text(_CHANGELOG)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("could not locate the version assignment", prop.skipped_reason)
        self.assertEqual(prop.edits, [])

    def test_empty_unreleased_changelog_move_is_refused(self):
        """Empty [Unreleased] must refuse the move (Keep-a-Changelog; no phantom section).

        With ``prop.edits.clear()`` on refuse (#751), the stub is edits=[] + no branch
        (same shape as dup-guard / bump=none). Never invent an empty section.
        """
        empty_unreleased = textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ## [0.4.0] - 2026-06-01

            ### Added

            - initial release
            """)
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=empty_unreleased)
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("CHANGELOG move refused", prop.skipped_reason)
        self.assertIn("[Unreleased] section has no content to move", prop.skipped_reason)
        self.assertEqual(prop.edits, [])
        self.assertIsNone(prop.branch)

    def test_unreadable_changelog_clears_staged_edits(self):
        """Missing CHANGELOG after the version bump is staged must refuse with an
        empty edits list (same clear-on-refuse contract as move_unreleased)."""
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog="")
        # _write_pkg only writes CHANGELOG when truthy; ensure the version file exists
        # but CHANGELOG.md does not.
        clog = self.repo_root / "juniper-thing" / "CHANGELOG.md"
        if clog.exists():
            clog.unlink()
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("could not read", prop.skipped_reason)
        self.assertIn("CHANGELOG.md", prop.skipped_reason)
        self.assertEqual(prop.edits, [])
        self.assertIsNone(prop.branch)

    def test_missing_changelog_is_refused(self):
        """Absent CHANGELOG.md must refuse (notes + Keep-a-Changelog move have no source)."""
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog="")
        entry = _entry()
        prop = pr.build_proposal(entry, _manifest_pkg(), self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-14")
        self.assertTrue(prop.skipped)
        self.assertIn("could not read", prop.skipped_reason)
        self.assertIn("CHANGELOG.md", prop.skipped_reason)
        self.assertEqual(prop.edits, [])
        self.assertIsNone(prop.branch)
        self.assertFalse(any(e.path.endswith("CHANGELOG.md") for e in prop.edits))


# ── AGENTS.md per-package version TABLE co-change (ml#851; worker#140 class, table variant) ──


class AgentsTableVersionHelperTest(unittest.TestCase):
    """``set_agents_table_version`` in isolation: what counts as a version row, and the four statuses."""

    def test_rewrites_only_the_named_row_preserving_shape(self):
        new_text, status = pr.set_agents_table_version(_SIBLING_TABLE_AGENTS, "juniper-recurrence", "0.3.0", "0.4.0")
        self.assertEqual(status, "edited")
        self.assertIn("| `juniper-recurrence` | 0.4.0 |", new_text)
        # same-prefix sibling rows are NOT collateral (the backtick-delimited needle, mirroring the
        # target repo's own `_agents_table_version`)
        self.assertIn("| `juniper-recurrence-model` | 0.2.0 |", new_text)
        self.assertIn("| `juniper-recurrence-client` | 0.2.0 |", new_text)
        # the header is step 5's business, not the table's; the prose mention is nobody's (see below)
        self.assertIn("**Version**: 0.3.0", new_text)
        self.assertIn("the application (`juniper-recurrence` 0.3.0)", new_text)
        # row shape preserved byte-for-byte apart from the cell (pipe count, padding, line count)
        self.assertEqual(new_text.count("|"), _SIBLING_TABLE_AGENTS.count("|"))
        self.assertEqual(len(new_text.splitlines()), len(_SIBLING_TABLE_AGENTS.splitlines()))

    def test_backticked_version_cell_keeps_its_backticks(self):
        text = "| `juniper-thing` |   `0.4.0`   |\n"
        new_text, status = pr.set_agents_table_version(text, "juniper-thing", "0.4.0", "0.5.0")
        self.assertEqual(status, "edited")
        self.assertEqual(new_text, "| `juniper-thing` |   `0.5.0`   |\n")

    def test_already_at_target_is_current_not_an_edit(self):
        new_text, status = pr.set_agents_table_version(_SIBLING_TABLE_AGENTS, "juniper-recurrence-model", "0.2.0", "0.2.0")
        self.assertEqual(status, "current")
        self.assertEqual(new_text, _SIBLING_TABLE_AGENTS)

    def test_no_row_is_absent(self):
        new_text, status = pr.set_agents_table_version(_SIBLING_TABLE_AGENTS, "juniper-elsewhere", "0.1.0", "0.2.0")
        self.assertEqual(status, "absent")
        self.assertEqual(new_text, _SIBLING_TABLE_AGENTS)

    def test_descriptive_row_without_a_version_cell_is_absent_not_unexpected(self):
        # a package named in a plain descriptive table must not produce checklist noise
        text = "| Client | `juniper-thing` | the HTTP client |\n"
        new_text, status = pr.set_agents_table_version(text, "juniper-thing", "0.4.0", "0.5.0")
        self.assertEqual(status, "absent")
        self.assertEqual(new_text, text)

    def test_extras_reference_row_is_not_a_version_row(self):
        # the meta AGENTS.md scoping hazard: requirement cells are not standalone version cells, so the
        # ml#657 extras table stays exclusively `apply_pin_edits_agents_table`'s business
        new_text, status = pr.set_agents_table_version(_META_AGENTS, "juniper-service-core", "0.4.0", "0.5.0")
        self.assertEqual(status, "absent")
        self.assertEqual(new_text, _META_AGENTS)

    def test_unexpected_cell_is_untouched(self):
        text = "| `juniper-thing` | 9.9.9 |\n"
        new_text, status = pr.set_agents_table_version(text, "juniper-thing", "0.4.0", "0.5.0")
        self.assertEqual(status, "unexpected")
        self.assertEqual(new_text, text)

    def test_ambiguous_two_version_row_is_unexpected(self):
        # never guess WHICH cell is the version cell
        text = "| `juniper-thing` | 0.4.0 | 0.4.0 |\n"
        new_text, status = pr.set_agents_table_version(text, "juniper-thing", "0.4.0", "0.5.0")
        self.assertEqual(status, "unexpected")
        self.assertEqual(new_text, text)

    def test_mixed_rows_are_unexpected_with_no_partial_edit(self):
        text = "| `juniper-thing` | 0.4.0 |\n| `juniper-thing` | 9.9.9 |\n"
        new_text, status = pr.set_agents_table_version(text, "juniper-thing", "0.4.0", "0.5.0")
        self.assertEqual(status, "unexpected")
        self.assertEqual(new_text, text)

    def test_unknown_from_version_never_invents_an_edit(self):
        text = "| `juniper-thing` | 0.4.0 |\n"
        new_text, status = pr.set_agents_table_version(text, "juniper-thing", None, "0.5.0")
        self.assertEqual(status, "unexpected")
        self.assertEqual(new_text, text)


class BuildProposalAgentsTableTest(unittest.TestCase):
    """ml#851 through ``build_proposal``: a table-bearing sibling repo (the juniper-recurrence shape).

    The train's ``**Version**`` header co-change (ml#706 / worker#140) knew nothing about the
    per-package version table juniper-recurrence's ``version-drift`` hook pins against ``_version.py``,
    so every recurrence proposal shipped red (recurrence#92 / #93, healed by hand). These pin the
    generic table heuristic (issue option 2) and its honesty rules."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        self.eco = self.root
        self.sib_root = self.eco / "juniper-recurrence"
        self.fake = _FakeSources(self.repo_root, self.eco)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_sibling(self, *, pkg_path: str, name: str, version: str, import_pkg: str, agents: "str | None" = _SIBLING_TABLE_AGENTS) -> None:
        _write_pkg(self.sib_root, pkg_path, name=name, version=version, changelog=_CHANGELOG, dynamic=True, import_pkg=import_pkg)
        if agents is not None:
            (self.sib_root / "AGENTS.md").write_text(agents)

    def _propose(self, *, name: str, pkg_path: str, from_version: str, to_version: str) -> "pr.Proposal":
        entry = _entry(pypi_name=name, repo="juniper-recurrence", path=pkg_path, version_source="dynamic", tag_pattern=f"{name}-v*", archive_name=f"RELEASE_NOTES_{name}_v{{version}}.md", ship_paths=[f"{pkg_path}{name.replace('-', '_')}/"])
        pkg = _manifest_pkg(pypi_name=name, repo="juniper-recurrence", released_version=from_version, declared_version=from_version, proposed_version=to_version)
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-08-07")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        return prop

    def _agents_edits(self, prop) -> list:
        return [e for e in prop.edits if e.path == "AGENTS.md"]

    def test_sibling_primary_bump_moves_header_and_row_in_one_edit(self):
        self._write_sibling(pkg_path="juniper-recurrence/", name="juniper-recurrence", version="0.3.0", import_pkg="juniper_recurrence")
        prop = self._propose(name="juniper-recurrence", pkg_path="juniper-recurrence/", from_version="0.3.0", to_version="0.4.0")
        agents = self._agents_edits(prop)
        # ONE AGENTS.md edit: the executor writes each edit's full new_text in order, so a second edit
        # on the same path would silently drop the first (header co-change lost).
        self.assertEqual(len(agents), 1, "AGENTS.md must carry exactly one composed FileEdit")
        self.assertIn("**Version**: 0.4.0", agents[0].new_text)
        self.assertIn("| `juniper-recurrence` | 0.4.0 |", agents[0].new_text)
        # the two sibling package rows are NOT collateral damage
        self.assertIn("| `juniper-recurrence-model` | 0.2.0 |", agents[0].new_text)
        self.assertIn("| `juniper-recurrence-client` | 0.2.0 |", agents[0].new_text)
        self.assertTrue(any("version-table row" in item and "juniper-recurrence" in item and "included in this PR" in item for item in prop.co_change_checklist))
        self.assertTrue(any("Sibling AGENTS.md" in item and "included in this PR" in item for item in prop.co_change_checklist))

    def test_sibling_subpackage_bumps_its_row_and_never_the_host_header(self):
        # the recurrence#92 case: the table is per-PACKAGE where the header is per-REPO, so a
        # sub-package must move its own row while leaving the primary-tracking header alone.
        self._write_sibling(pkg_path="juniper-recurrence-model/", name="juniper-recurrence-model", version="0.2.0", import_pkg="juniper_recurrence_model")
        prop = self._propose(name="juniper-recurrence-model", pkg_path="juniper-recurrence-model/", from_version="0.2.0", to_version="0.3.0")
        agents = self._agents_edits(prop)
        self.assertEqual(len(agents), 1)
        self.assertIn("| `juniper-recurrence-model` | 0.3.0 |", agents[0].new_text)
        self.assertIn("**Version**: 0.3.0", agents[0].new_text)  # untouched: still the app's version
        self.assertIn("| `juniper-recurrence` | 0.3.0 |", agents[0].new_text)  # app row untouched
        self.assertIn("| `juniper-recurrence-client` | 0.2.0 |", agents[0].new_text)
        self.assertTrue(any("version-table row" in item and "included in this PR" in item for item in prop.co_change_checklist))
        self.assertFalse(any("Sibling AGENTS.md **Version**" in item for item in prop.co_change_checklist))

    def test_row_for_a_different_package_is_untouched(self):
        # bumping the client must move ONLY the client row (the app + model rows byte-identical)
        self._write_sibling(pkg_path="juniper-recurrence-client/", name="juniper-recurrence-client", version="0.2.0", import_pkg="juniper_recurrence_client")
        prop = self._propose(name="juniper-recurrence-client", pkg_path="juniper-recurrence-client/", from_version="0.2.0", to_version="0.2.1")
        agents = self._agents_edits(prop)
        self.assertEqual(len(agents), 1)
        moved = set(agents[0].new_text.splitlines()) - set(agents[0].old_text.splitlines())
        # Exactly two lines move: the client's own table row, and the step-5c ``**Last Updated**``
        # true-up that pre-empts the agents-md-touch-up workflow (its ``[skip ci]`` commit would
        # otherwise become the PR head and orphan every required check -- the cascor#515 class).
        # The app and model rows stay byte-identical, which is what this test exists to pin.
        self.assertEqual(
            moved,
            {
                "| HTTP client | `juniper-recurrence-client/` | `juniper-recurrence-client` | 0.2.1 |",
                "**Last Updated**: 2026-08-07",
            },
        )

    def test_package_without_a_row_emits_no_phantom_agents_edit(self):
        # a table-bearing repo can still host a package the table does not list (the bench harness
        # graduating to a package): absent row => no edit and no checklist noise.
        self._write_sibling(pkg_path="juniper-recurrence-bench/", name="juniper-recurrence-bench", version="0.1.0", import_pkg="juniper_recurrence_bench")
        prop = self._propose(name="juniper-recurrence-bench", pkg_path="juniper-recurrence-bench/", from_version="0.1.0", to_version="0.2.0")
        self.assertEqual(self._agents_edits(prop), [])
        self.assertFalse(any("version-table row" in item for item in prop.co_change_checklist))

    def test_repo_without_a_table_emits_no_phantom_agents_edit(self):
        # the common shape (7 of 8 repos): AGENTS.md has a header but no per-package version table.
        self._write_sibling(pkg_path="juniper-recurrence-model/", name="juniper-recurrence-model", version="0.2.0", import_pkg="juniper_recurrence_model", agents="# AGENTS.md\n\n**Version**: 0.3.0\n**Author**: Paul\n")
        prop = self._propose(name="juniper-recurrence-model", pkg_path="juniper-recurrence-model/", from_version="0.2.0", to_version="0.3.0")
        self.assertEqual(self._agents_edits(prop), [])
        self.assertFalse(any("version-table row" in item for item in prop.co_change_checklist))

    def test_row_already_at_target_is_silent_success(self):
        # partial heal / re-entry: the row already satisfies the target repo's drift hook, so no edit
        # AND no REQUIRED (the ml#701 dunder / ml#720 header silent-success class).
        healed = _SIBLING_TABLE_AGENTS.replace("| `juniper-recurrence-model` | 0.2.0 |", "| `juniper-recurrence-model` | 0.3.0 |")
        self._write_sibling(pkg_path="juniper-recurrence-model/", name="juniper-recurrence-model", version="0.2.0", import_pkg="juniper_recurrence_model", agents=healed)
        prop = self._propose(name="juniper-recurrence-model", pkg_path="juniper-recurrence-model/", from_version="0.2.0", to_version="0.3.0")
        self.assertEqual(self._agents_edits(prop), [])
        self.assertFalse(any("version-table row" in item for item in prop.co_change_checklist))

    def test_unexpected_row_is_left_untouched_and_flagged_required(self):
        drifted = _SIBLING_TABLE_AGENTS.replace("| `juniper-recurrence-model` | 0.2.0 |", "| `juniper-recurrence-model` | 9.9.9 |")
        self._write_sibling(pkg_path="juniper-recurrence-model/", name="juniper-recurrence-model", version="0.2.0", import_pkg="juniper_recurrence_model", agents=drifted)
        prop = self._propose(name="juniper-recurrence-model", pkg_path="juniper-recurrence-model/", from_version="0.2.0", to_version="0.3.0")
        self.assertEqual(self._agents_edits(prop), [])
        self.assertTrue(any("version-table row" in item and "REQUIRED" in item for item in prop.co_change_checklist))

    def test_prose_mention_is_deliberately_left_alone(self):
        # AGENTS.md:118 in the live repo. The target repo's drift hook checks the header + the table
        # cells ONLY (scripts/check_version_drift.py invariants 1-3), so rewriting free prose would be
        # an invented edit with no gate behind it -- raised as an open question on the PR instead.
        self._write_sibling(pkg_path="juniper-recurrence/", name="juniper-recurrence", version="0.3.0", import_pkg="juniper_recurrence")
        prop = self._propose(name="juniper-recurrence", pkg_path="juniper-recurrence/", from_version="0.3.0", to_version="0.4.0")
        agents = self._agents_edits(prop)
        self.assertIn("the application (`juniper-recurrence` 0.3.0)", agents[0].new_text)


# ── in-repo meta consumer-pin co-changes: pure helpers (plan S5.4; ml#657 RK-11 gap) ─────


class ConsumerPinHelperTest(unittest.TestCase):
    def test_requirement_names_package(self):
        self.assertTrue(pr.requirement_names_package("juniper-service-core>=0.2.0,<0.5.0", "juniper-service-core"))
        self.assertTrue(pr.requirement_names_package("juniper-observability>=0.2.0", "juniper-observability"))  # floorless still names it
        # the [all] recursive self-ref names extras, not a versioned package
        self.assertFalse(pr.requirement_names_package("juniper-ml[clients,worker,tools]", "juniper-ml"))
        # a longer package name must not match its prefix
        self.assertFalse(pr.requirement_names_package("juniper-cascor-worker>=0.4.0", "juniper-cascor"))

    def test_next_minor_ceiling(self):
        self.assertEqual(pr.next_minor_ceiling("0.5.0"), "<0.6.0")
        self.assertEqual(pr.next_minor_ceiling("0.5.3"), "<0.6.0")  # patch of a minor still caps at the next minor
        self.assertEqual(pr.next_minor_ceiling("0.9.0"), "<0.10.0")  # multi-digit minor

    def test_raise_requirement_ceiling(self):
        # escaping: 0.5.0 is NOT < 0.5.0 -> raise to <0.6.0
        self.assertEqual(pr.raise_requirement_ceiling("juniper-service-core>=0.2.0,<0.5.0", "0.5.0"), "juniper-service-core>=0.2.0,<0.6.0")
        # non-escaping patch under the ceiling -> no change
        self.assertIsNone(pr.raise_requirement_ceiling("juniper-service-core>=0.2.0,<0.5.0", "0.4.1"))
        # no upper bound -> any higher version still satisfies >=floor
        self.assertIsNone(pr.raise_requirement_ceiling("juniper-ci-tools>=0.1.0", "0.9.0"))
        # a <= ceiling: 0.5.0 <= 0.5.0 satisfies -> no change; 0.5.1 escapes -> raise
        self.assertIsNone(pr.raise_requirement_ceiling("juniper-x>=0.2.0,<=0.5.0", "0.5.0"))
        self.assertEqual(pr.raise_requirement_ceiling("juniper-x>=0.2.0,<=0.5.0", "0.5.1"), "juniper-x>=0.2.0,<0.6.0")

    def test_compute_multi_extra_and_absent_and_meta_self(self):
        # doc-tools is pinned in BOTH [tools] and [doc-tools] -> one co-change per extra
        cc = pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-doc-tools", "0.2.0")
        self.assertEqual({c.extra for c in cc}, {"tools", "doc-tools"})
        self.assertTrue(all(c.new_req == "juniper-doc-tools>=0.1.0,<0.3.0" for c in cc))
        # a package not named in any extra -> zero
        self.assertEqual(pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-config-tools", "0.9.0"), [])
        # the meta-package does not pin ITSELF with a version (only the [all] recursive ref) -> zero
        self.assertEqual(pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-ml", "0.7.0"), [])
        # a floorless pin (observability) escapes no ceiling -> zero
        self.assertEqual(pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-observability", "0.9.0"), [])

    def test_pyproject_edit_round_trips_byte_identical(self):
        cc = pr.compute_consumer_pin_cochanges(_META_PYPROJECT, "juniper-service-core", "0.5.0")
        self.assertEqual(len(cc), 1)
        new_text = pr.apply_pin_edits_exact(_META_PYPROJECT, cc)
        # re-parse: the target ceiling is raised, the floor is intact
        after = tomllib.loads(new_text)["project"]["optional-dependencies"]
        self.assertIn("juniper-service-core>=0.2.0,<0.6.0", after["tools"])
        self.assertNotIn("juniper-service-core>=0.2.0,<0.5.0", after["tools"])
        # every OTHER extras entry is byte-identical (floors + siblings untouched)
        before = tomllib.loads(_META_PYPROJECT)["project"]["optional-dependencies"]
        for extra in before:
            unchanged_before = {r for r in before[extra] if "juniper-service-core" not in r}
            unchanged_after = {r for r in after[extra] if "juniper-service-core" not in r}
            self.assertEqual(unchanged_before, unchanged_after, f"[{extra}] sibling entries drifted")
        # exactly ONE textual line differs, and single-digit-minor keeps the byte length
        diff = [ln for ln in difflib.unified_diff(_META_PYPROJECT.splitlines(), new_text.splitlines()) if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
        self.assertEqual(diff, ['-    "juniper-service-core>=0.2.0,<0.5.0",', '+    "juniper-service-core>=0.2.0,<0.6.0",'])
        self.assertEqual(len(new_text), len(_META_PYPROJECT))

    def test_agents_table_true_up_is_scoped(self):
        new_req = "juniper-service-core>=0.2.0,<0.6.0"
        out = pr.apply_pin_edits_agents_table(_META_AGENTS, "juniper-service-core", new_req)
        # the [tools] table row is trued up ...
        self.assertIn("`juniper-service-core>=0.2.0,<0.6.0`", out)
        # ... but the prose pin in the ## Conventions section is NOT moved
        self.assertIn("A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.", out)
        # the observability minimum-pin prose note is untouched too
        self.assertIn("Minimum pin: `juniper-observability>=0.2.0`.", out)
        # doc-tools sits in TWO table rows -> both are trued up, none outside the table
        dt = pr.apply_pin_edits_agents_table(_META_AGENTS, "juniper-doc-tools", "juniper-doc-tools>=0.1.0,<0.3.0")
        self.assertEqual(dt.count("`juniper-doc-tools>=0.1.0,<0.3.0`"), 2)
        self.assertNotIn("`juniper-doc-tools>=0.1.0,<0.2.0`", dt)

    def test_agents_table_true_up_fixes_a_drifted_row(self):
        # the ml#657 class: the table row lags pyproject at <0.4.0; the name-anchored true-up corrects it
        stale = _META_AGENTS.replace("`juniper-service-core>=0.2.0,<0.5.0`, `juniper-model-core", "`juniper-service-core>=0.2.0,<0.4.0`, `juniper-model-core")
        fixed = pr.apply_pin_edits_agents_table(stale, "juniper-service-core", "juniper-service-core>=0.2.0,<0.6.0")
        self.assertIn("`juniper-service-core>=0.2.0,<0.6.0`", fixed)
        # only the table row is affected; the model-core sibling and the prose pins are intact
        self.assertIn("`juniper-model-core>=0.1.0,<0.4.0`", fixed)
        self.assertIn("A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.", fixed)


class ApplyPinPairsExactTest(unittest.TestCase):
    """Direct pins for ``apply_pin_pairs_exact`` — shared by meta co-change + D6 follow-on edits.

    The helper is bare ``str.replace`` over exact ``old_req`` strings parsed from the same file.
    A regression that switches to regex / partial-token replace, drops de-dup, or stops replacing
    every occurrence would corrupt consumer pyprojects across the release-train write path.
    """

    def test_empty_pairs_is_noop(self):
        text = 'dependencies = ["juniper-up>=0.2.0,<0.4.0"]\n'
        self.assertEqual(pr.apply_pin_pairs_exact(text, []), text)

    def test_replaces_every_occurrence_of_exact_old_req(self):
        # Multi-extra / duplicate pin strings must all move (doc-tools sits in tools + doc-tools).
        text = 'a = ["juniper-doc-tools>=0.1.0,<0.2.0"]\nb = ["juniper-doc-tools>=0.1.0,<0.2.0"]\n'
        out = pr.apply_pin_pairs_exact(text, [("juniper-doc-tools>=0.1.0,<0.2.0", "juniper-doc-tools>=0.1.0,<0.3.0")])
        self.assertEqual(out.count("juniper-doc-tools>=0.1.0,<0.3.0"), 2)
        self.assertNotIn("juniper-doc-tools>=0.1.0,<0.2.0", out)

    def test_dedups_identical_pairs_without_double_replace(self):
        # Identical (old, new) pairs must apply once — a second pass would no-op only when
        # old != new; if a future change made new contain old as a substring, re-applying
        # would corrupt. De-dup is the safety valve both call sites rely on.
        text = 'req = "juniper-up>=0.2.0,<0.4.0"\n'
        pairs = [
            ("juniper-up>=0.2.0,<0.4.0", "juniper-up>=0.2.0,<0.5.0"),
            ("juniper-up>=0.2.0,<0.4.0", "juniper-up>=0.2.0,<0.5.0"),
        ]
        out = pr.apply_pin_pairs_exact(text, pairs)
        self.assertEqual(out, 'req = "juniper-up>=0.2.0,<0.5.0"\n')
        self.assertEqual(out.count("juniper-up>=0.2.0,<0.5.0"), 1)

    def test_applies_distinct_pairs_in_order(self):
        text = 'deps = ["juniper-a>=1.0.0,<2.0.0", "juniper-b>=1.0.0,<2.0.0"]\n'
        out = pr.apply_pin_pairs_exact(
            text,
            [
                ("juniper-a>=1.0.0,<2.0.0", "juniper-a>=1.0.0,<3.0.0"),
                ("juniper-b>=1.0.0,<2.0.0", "juniper-b>=1.0.0,<3.0.0"),
            ],
        )
        self.assertIn("juniper-a>=1.0.0,<3.0.0", out)
        self.assertIn("juniper-b>=1.0.0,<3.0.0", out)
        self.assertNotIn("<2.0.0", out)

    def test_leaves_non_exact_sibling_pins_untouched(self):
        # Prefix / longer-name siblings must not move when the exact old_req is absent as a
        # full string (bare replace is exact-token, not package-name anchored).
        text = 'deps = ["juniper-cascor>=0.5.0,<0.6.0", "juniper-cascor-worker>=0.4.0", ' '"juniper-cascor-client>=0.5.0"]\n'
        out = pr.apply_pin_pairs_exact(text, [("juniper-cascor>=0.5.0,<0.6.0", "juniper-cascor>=0.5.0,<0.7.0")])
        self.assertIn("juniper-cascor>=0.5.0,<0.7.0", out)
        self.assertIn("juniper-cascor-worker>=0.4.0", out)
        self.assertIn("juniper-cascor-client>=0.5.0", out)
        self.assertNotIn("juniper-cascor>=0.5.0,<0.6.0", out)

    def test_apply_pin_edits_exact_delegates_pair_list(self):
        cc = [
            pr.ConsumerPinCoChange(extra="tools", old_req="juniper-x>=0.1.0,<0.2.0", new_req="juniper-x>=0.1.0,<0.3.0"),
            pr.ConsumerPinCoChange(extra="doc-tools", old_req="juniper-x>=0.1.0,<0.2.0", new_req="juniper-x>=0.1.0,<0.3.0"),
        ]
        text = 'tools = ["juniper-x>=0.1.0,<0.2.0"]\ndoc = ["juniper-x>=0.1.0,<0.2.0"]\n'
        self.assertEqual(pr.apply_pin_edits_exact(text, cc), pr.apply_pin_pairs_exact(text, [("juniper-x>=0.1.0,<0.2.0", "juniper-x>=0.1.0,<0.3.0")]))


# ── in-repo meta consumer-pin co-changes: build_proposal integration ─────────────────────


class BuildProposalConsumerPinTest(unittest.TestCase):
    """The escaping / non-escaping / absent / multi-extra / meta-self cases through build_proposal,
    against a synthetic repo carrying the real three-file meta surface. Fully offline (no writes)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        _write_meta_surface(self.repo_root)
        self.eco = self.root
        self.fake = _FakeSources(self.repo_root, self.eco)

    def tearDown(self):
        self._tmp.cleanup()

    def _subpkg_entry(self, name: str, path: str) -> "d.PackageEntry":
        return _entry(pypi_name=name, path=path, tag_pattern=f"{name}-v*", archive_name=f"RELEASE_NOTES_{name}_v{{version}}.md", ship_paths=[f"{path}{name.replace('-', '_')}/"])

    def _edit(self, prop, path):
        return next((e for e in prop.edits if e.path == path), None)

    def test_escaping_minor_bump_emits_all_three_cochanges(self):
        _write_pkg(self.repo_root, "juniper-service-core/", name="juniper-service-core", version="0.4.0", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-service-core", "juniper-service-core/")
        pkg = _manifest_pkg(pypi_name="juniper-service-core", released_version="0.4.0", declared_version="0.4.0", proposed_version="0.5.0")
        before = _sha_tree(self.repo_root)
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        # build_proposal itself writes NOTHING (dry-run purity)
        self.assertEqual(before, _sha_tree(self.repo_root))
        # the version-file edit stays edits[0] (root pyproject is an ADDITIONAL edit, not the version bump)
        self.assertEqual(prop.edits[0].path, "juniper-service-core/pyproject.toml")
        # co-change record + all three lockstep edits present with the raised ceiling
        self.assertEqual([(c.extra, c.old_req, c.new_req) for c in prop.consumer_pin_cochanges], [("tools", "juniper-service-core>=0.2.0,<0.5.0", "juniper-service-core>=0.2.0,<0.6.0")])
        root = self._edit(prop, "pyproject.toml")
        self.assertIsNotNone(root, "root pyproject.toml pin co-change missing")
        self.assertIn("juniper-service-core>=0.2.0,<0.6.0", root.new_text)
        self.assertNotIn("juniper-service-core>=0.2.0,<0.5.0", tomllib.loads(root.new_text)["project"]["optional-dependencies"]["tools"])
        test_edit = self._edit(prop, "tests/test_pyproject_extras.py")
        self.assertIsNotNone(test_edit, "test_pyproject_extras.py lockstep edit missing")
        self.assertIn("juniper-service-core>=0.2.0,<0.6.0", test_edit.new_text)
        agents = self._edit(prop, "AGENTS.md")
        self.assertIsNotNone(agents, "AGENTS.md extras-table co-change missing")
        self.assertIn("`juniper-service-core>=0.2.0,<0.6.0`", agents.new_text)
        # scoping: the AGENTS prose pin is NOT moved by the table true-up
        self.assertIn("A prose pin that must NOT be edited: `juniper-service-core>=0.2.0,<0.5.0`.", agents.new_text)
        # the PR body carries the Consumer-pin co-changes section listing the edit
        self.assertIn("Consumer-pin co-changes", prop.pr_body or "")
        self.assertIn("`[tools]`: `juniper-service-core>=0.2.0,<0.5.0` -> `juniper-service-core>=0.2.0,<0.6.0`", prop.pr_body or "")
        self.assertTrue(any("In-repo meta consumer pin" in item for item in prop.co_change_checklist))

    def test_doc_tools_bump_updates_both_extras(self):
        _write_pkg(self.repo_root, "juniper-doc-tools/", name="juniper-doc-tools", version="0.1.5", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-doc-tools", "juniper-doc-tools/")
        pkg = _manifest_pkg(pypi_name="juniper-doc-tools", released_version="0.1.5", declared_version="0.1.5", proposed_version="0.2.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual({c.extra for c in prop.consumer_pin_cochanges}, {"tools", "doc-tools"})
        root = self._edit(prop, "pyproject.toml")
        extras = tomllib.loads(root.new_text)["project"]["optional-dependencies"]
        self.assertIn("juniper-doc-tools>=0.1.0,<0.3.0", extras["tools"])
        self.assertIn("juniper-doc-tools>=0.1.0,<0.3.0", extras["doc-tools"])
        agents = self._edit(prop, "AGENTS.md")
        self.assertEqual(agents.new_text.count("`juniper-doc-tools>=0.1.0,<0.3.0`"), 2)

    def test_non_escaping_patch_bump_emits_none_needed(self):
        _write_pkg(self.repo_root, "juniper-service-core/", name="juniper-service-core", version="0.4.0", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-service-core", "juniper-service-core/")
        pkg = _manifest_pkg(pypi_name="juniper-service-core", released_version="0.4.0", declared_version="0.4.0", proposed_bump="patch", proposed_version="0.4.1")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.consumer_pin_cochanges, [])
        # NO root pyproject / test / AGENTS edits (only the sub-package version bump + its CHANGELOG)
        self.assertEqual({e.path for e in prop.edits}, {"juniper-service-core/pyproject.toml", "juniper-service-core/CHANGELOG.md"})
        self.assertIn("none needed -- new version within existing ceilings", prop.pr_body or "")

    def test_package_absent_from_extras_emits_zero(self):
        # juniper-config-tools is in-repo but NOT named in the fixture's extras -> zero co-changes
        _write_pkg(self.repo_root, "juniper-config-tools/", name="juniper-config-tools", version="0.1.0", changelog=_CHANGELOG)
        entry = self._subpkg_entry("juniper-config-tools", "juniper-config-tools/")
        pkg = _manifest_pkg(pypi_name="juniper-config-tools", released_version="0.1.0", declared_version="0.1.0", proposed_version="0.2.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.consumer_pin_cochanges, [])
        self.assertIsNone(self._edit(prop, "pyproject.toml"))
        self.assertIsNone(self._edit(prop, "AGENTS.md"))
        self.assertIn("none needed", prop.pr_body or "")

    def test_meta_self_bump_has_no_pin_cochange_only_version_header(self):
        # the meta-package bumping itself: AGENTS **Version** co-change, but NO extras-table pin change.
        # _write_meta_surface already laid down the extras pyproject + AGENTS; add the meta CHANGELOG.
        (self.repo_root / "CHANGELOG.md").write_text(_CHANGELOG)
        entry = _entry(pypi_name="juniper-ml", path=".", tag_pattern="v*", archive_name="RELEASE_NOTES_v{version}.md", ship_paths=[])
        pkg = _manifest_pkg(pypi_name="juniper-ml", released_version="0.6.0", declared_version="0.6.0", proposed_version="0.7.0")
        prop = pr.build_proposal(entry, pkg, self.fake.build(), self.repo_root, self.eco, [entry], "2026-07-17")
        self.assertFalse(prop.skipped, prop.skipped_reason)
        self.assertEqual(prop.consumer_pin_cochanges, [])
        agents = self._edit(prop, "AGENTS.md")
        self.assertIsNotNone(agents)
        self.assertIn("**Version**: 0.7.0", agents.new_text)  # the version header co-change (step 5)
        self.assertIn("`juniper-service-core>=0.2.0,<0.5.0`", agents.new_text)  # extras table NOT touched
        self.assertIn("none needed", prop.pr_body or "")

    def test_meta_consumer_excluded_from_propagation_when_in_repo(self):
        # a sub-package MINOR bump: the meta (in-repo) is folded into THIS PR, so it is NOT also a
        # cross-repo propagation follow-on; a genuine sibling consumer still is.
        mc = self._subpkg_entry("juniper-model-core", "juniper-model-core/")
        meta = _entry(pypi_name="juniper-ml", repo="juniper-ml", path=".", depends_on=["juniper-model-core"])
        sibling = _entry(pypi_name="juniper-recurrence", repo="juniper-recurrence", path=".", depends_on=["juniper-model-core"])
        edges = pr.propagation_edges([mc, meta, sibling], mc, "minor")
        consumers = {e["consumer"] for e in edges}
        self.assertNotIn("juniper-ml", consumers)  # folded into the same PR
        self.assertIn("juniper-recurrence", consumers)  # cross-repo follow-on remains


# ── CLI: dry-run report / json / writes-nothing / exit codes ─────────────────


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


class CliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        self.registry = self.root / "registry.yaml"
        self.registry.write_text(_MINI_REGISTRY)
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({"schema": "juniper-release-train/manifest/v1", "packages": [_manifest_pkg()]}))
        self.fake = _FakeSources(self.repo_root, self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, *extra) -> "tuple[int, str]":
        buf = io.StringIO()
        argv = ["--manifest", str(self.manifest), "--repo-root", str(self.repo_root), "--ecosystem-root", str(self.root), "--registry", str(self.registry), "--release-date", "2026-07-14", *extra]
        with redirect_stdout(buf):
            code = pr.main(argv, sources=self.fake.build())
        return code, buf.getvalue()

    def test_dry_run_report_is_default_and_wellformed(self):
        code, out = self._run()  # no --dry-run flag: dry-run is the default
        self.assertEqual(code, 0)
        self.assertIn("DRY-RUN", out)
        self.assertIn("PROPOSE  juniper-thing", out)
        self.assertIn("release/juniper-thing-v0.5.0", out)
        self.assertIn('version = "0.5.0"', out)

    def test_json_mode(self):
        code, out = self._run("--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["schema"], "juniper-release-train/proposals/v1")
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["summary"]["proposed"], 1)
        self.assertEqual(payload["proposals"][0]["branch"], "release/juniper-thing-v0.5.0")

    def test_dry_run_writes_nothing(self):
        before = _sha_tree(self.repo_root)
        code, _ = self._run()
        self.assertEqual(code, 0)
        after = _sha_tree(self.repo_root)
        self.assertEqual(before, after, "dry-run must not create/modify/delete any repo file")

    def test_package_filter_and_skip_non_unreleased(self):
        # a manifest with an UP_TO_DATE package produces no proposal (only UNRELEASED_CHANGES proposed)
        self.manifest.write_text(json.dumps({"packages": [_manifest_pkg(classification="UP_TO_DATE")]}))
        code, out = self._run()
        self.assertEqual(code, 0)
        self.assertIn("nothing to propose", out)

    def test_exit_two_bad_manifest(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pr.main(["--manifest", str(self.root / "nope.json"), "--repo-root", str(self.repo_root), "--registry", str(self.registry)], sources=self.fake.build())
        self.assertEqual(code, 2)

    def test_exit_two_unknown_package(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pr.main(["--manifest", str(self.manifest), "--repo-root", str(self.repo_root), "--registry", str(self.registry), "--package", "juniper-nope"], sources=self.fake.build())
        self.assertEqual(code, 2)

    def test_dry_run_overrides_execute_flag(self):
        # even with --execute, --dry-run wins (safety); nothing is written.
        before = _sha_tree(self.repo_root)
        code, out = self._run("--execute", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("DRY-RUN", out)
        self.assertEqual(before, _sha_tree(self.repo_root))

    def test_manifest_package_absent_from_registry_is_skipped(self):
        """A proposable manifest package missing from registry.yaml must skip, not crash.

        Orthogonal to ``--package`` unknown (exit 2 before the loop) and to
        ``build_proposal`` refusals (#749): this is the CLI ``main()`` path that
        never calls ``build_proposal`` when the registry lookup misses.
        """
        self.manifest.write_text(
            json.dumps(
                {
                    "packages": [
                        _manifest_pkg(),
                        _manifest_pkg(pypi_name="juniper-ghost", repo="juniper-ghost"),
                    ]
                }
            )
        )
        code, out = self._run("--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        by_name = {p["pypi_name"]: p for p in payload["proposals"]}
        self.assertIn("juniper-thing", by_name)
        self.assertIsNone(by_name["juniper-thing"].get("skipped_reason"))
        self.assertEqual(by_name["juniper-ghost"]["skipped_reason"], "package not in registry.yaml")
        self.assertEqual(payload["summary"]["proposed"], 1)
        self.assertEqual(payload["summary"]["skipped"], 1)


# ── execute path: cross-repo guard + headless-commit gpgsign landmine (Phase 2.2) ────


_TWO_PKG_REGISTRY = textwrap.dedent("""\
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
      - pypi_name: juniper-sibling
        repo: juniper-sibling
        path: "."
        version_source: static
        tag_pattern: "v*"
        archive_name: "RELEASE_NOTES_juniper-sibling_v{version}.md"
        trigger: {now: release, target: release}
        verify: {now: strict, target: strict}
        depends_on: []
        ship_paths: ["juniper_sibling/"]
        exclude_paths: ["juniper_sibling/tests/"]
    """)


class ExecuteCrossRepoGuardTest(unittest.TestCase):
    """--execute capability boundary (Phase 4.1, plan S9.2 / S12 step 4.1). The DEGRADED single-repo
    ``GITHUB_TOKEN`` path (no --cross-repo) opens PRs ONLY for juniper-ml and SKIPS sibling-repo packages
    with the same clear reason as before; the CROSS-REPO-capable path (--cross-repo, an on-disk sibling
    checkout) additionally opens a sibling's PR in ITS OWN repo -- branched from that repo's origin/main,
    written into that repo's checkout, never touching the meta from the sibling context. Also pins the
    headless-commit gpgsign landmine fix. Fully hermetic: every repo-aware write / git / pr effect is a
    recording spy (no real repo writes, no gh, no git)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        # An in-repo (writable) package AND a cross-repo sibling, BOTH readable on disk -- so the
        # ONLY thing that skips the sibling under --execute is the cross-repo guard, not a failed
        # file read (proving the guard, not an incidental read failure, is the gate).
        _write_pkg(self.repo_root, "juniper-thing/", name="juniper-thing", version="0.4.0", changelog=_CHANGELOG)
        sibling = self.root / "juniper-sibling"
        sibling.mkdir()
        _write_pkg(sibling, ".", name="juniper-sibling", version="0.4.0", changelog=_CHANGELOG)
        self.registry = self.root / "registry.yaml"
        self.registry.write_text(_TWO_PKG_REGISTRY)
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(
            json.dumps(
                {
                    "packages": [
                        _manifest_pkg(pypi_name="juniper-thing", repo="juniper-ml"),
                        _manifest_pkg(pypi_name="juniper-sibling", repo="juniper-sibling"),
                    ]
                }
            )
        )
        self.calls = {"write": [], "branch": [], "commit": [], "pr": []}

    def tearDown(self):
        self._tmp.cleanup()

    def _read_file(self, entry, filename):
        base = d.base_dir_for(entry, self.repo_root, self.root)
        try:
            return (base / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    def _sources(self) -> pr.ProposeSources:
        # Repo-aware recording seam (Phase 4.1): every write member carries the target repo, so the
        # test can prove a sibling's branch/commit lands in the SIBLING repo, never the juniper-ml one.
        def open_pr(repo, base, head, title, body):
            self.calls["pr"].append((repo, base, head))
            return f"https://github.com/pcalnon/{repo}/pull/1"

        def create_signed_commit(repo, branch, message, additions, expected_head_oid):
            # record the decoded paths so the assertions read like the old write_file recording
            self.calls["write"].extend((repo, path) for path, _contents in additions)
            self.calls["commit"].append((repo, branch, message, expected_head_oid))
            return "c0ffee"

        return pr.ProposeSources(
            read_file=self._read_file,
            list_open_prs=lambda repo: [],
            resolve_ref_sha=lambda repo, ref: f"sha-{repo}-{ref}",
            create_branch=lambda repo, branch, sha: self.calls["branch"].append((repo, branch, sha)),
            create_signed_commit=create_signed_commit,
            open_pr=open_pr,
        )

    def _run_execute(self, *extra) -> "tuple[int, str]":
        buf = io.StringIO()
        argv = ["--manifest", str(self.manifest), "--repo-root", str(self.repo_root), "--ecosystem-root", str(self.root), "--registry", str(self.registry), "--release-date", "2026-07-14", "--execute", *extra]
        with redirect_stdout(buf):
            code = pr.main(argv, sources=self._sources())
        return code, buf.getvalue()

    # ── capability helper (degraded vs cross-repo-capable) ───────────────────────────────────
    def test_cross_repo_skip_reason_capability(self):
        # in-repo is always writable (both paths)
        self.assertIsNone(pr.cross_repo_skip_reason("juniper-ml"))
        # sibling on the DEGRADED path (no capability) -> the SAME clear reason as before (preserved)
        degraded = pr.cross_repo_skip_reason("juniper-cascor")
        self.assertIsNotNone(degraded)
        self.assertIn("cross-repo", degraded)
        self.assertIn("juniper-cascor", degraded)
        self.assertIn("single-repo GITHUB_TOKEN", degraded)  # today's degraded-path wording
        # capable but the checkout is absent under the ecosystem root -> a distinct reason
        absent = pr.cross_repo_skip_reason("juniper-cascor", cross_repo_capable=True, ecosystem_root=self.root)
        self.assertIsNotNone(absent)
        self.assertIn("checkout is not present", absent)
        # capable AND the sibling checkout is on disk (setUp created self.root/juniper-sibling) -> writable
        self.assertIsNone(pr.cross_repo_skip_reason("juniper-sibling", cross_repo_capable=True, ecosystem_root=self.root))
        # the writable repo is still overridable (env / future multi-repo identity)
        self.assertIsNone(pr.cross_repo_skip_reason("juniper-cascor", writable_repo="juniper-cascor"))

    # ── DEGRADED path (no --cross-repo): in-repo only, sibling skipped (preserved) ───────────
    def test_degraded_path_opens_in_repo_and_skips_cross_repo(self):
        code, out = self._run_execute()  # NO --cross-repo
        self.assertEqual(code, 0, out)
        # exactly one PR opened, and it is the juniper-ml package (never the sibling); base 'main'
        self.assertEqual(self.calls["pr"], [("juniper-ml", "main", "release/juniper-thing-v0.5.0")])
        self.assertIn("opened: juniper-thing", out)
        self.assertIn("skip: juniper-sibling", out)
        self.assertIn("cross-repo", out)
        self.assertIn("single-repo GITHUB_TOKEN", out)  # the degraded-path skip reason, preserved
        # every write targeted the juniper-ml checkout for the in-repo package; nothing for the sibling
        for repo, path in self.calls["write"]:
            self.assertEqual(repo, "juniper-ml")
            self.assertTrue(path.startswith("juniper-thing/"), f"unexpected write to {path!r} -- sibling clobber?")

    # ── CROSS-REPO-capable path (--cross-repo): sibling opens in its OWN repo ────────────────
    def test_cross_repo_opens_sibling_in_its_repo_with_correct_branch_and_base(self):
        code, out = self._run_execute("--cross-repo")
        self.assertEqual(code, 0, out)
        # BOTH open now, each in its OWN repo; the PR --base is 'main' in both cases. Order is the
        # Phase-4.2 deterministic topological sort of the registry depends_on DAG: both packages are
        # dependency-free, so the lexicographic pypi_name tie-break puts 'juniper-sibling' before
        # 'juniper-thing' (independent of the manifest's listing order).
        self.assertEqual(
            self.calls["pr"],
            [
                ("juniper-sibling", "main", "release/juniper-sibling-v0.5.0"),
                ("juniper-ml", "main", "release/juniper-thing-v0.5.0"),
            ],
        )
        self.assertIn("opened: juniper-thing", out)
        self.assertIn("opened: juniper-sibling", out)
        # Both branch from the API-resolved tip of `main` in their OWN repo. The old local-git path
        # needed an in-repo `main` vs sibling `origin/main` split (working tree vs fresh clone); the
        # API path has no working tree, so one ref name is correct for both.
        self.assertIn(("juniper-sibling", "release/juniper-sibling-v0.5.0", "sha-juniper-sibling-main"), self.calls["branch"])
        self.assertIn(("juniper-ml", "release/juniper-thing-v0.5.0", "sha-juniper-ml-main"), self.calls["branch"])

    def test_cross_repo_sibling_edits_target_sibling_checkout_never_the_meta(self):
        self._run_execute("--cross-repo")
        sib_writes = [path for repo, path in self.calls["write"] if repo == "juniper-sibling"]
        # the sibling proposal edited only its OWN files (version bump + CHANGELOG at path '.')
        self.assertEqual(set(sib_writes), {"pyproject.toml", "CHANGELOG.md"})
        # NO sibling-shaped edit landed in the juniper-ml checkout (the clobber the guard prevents) ...
        self.assertNotIn(("juniper-ml", "pyproject.toml"), self.calls["write"])
        # ... and the sibling proposal NEVER edited the meta's consumer-pin lockstep files (#661 is
        # in-repo only; a sibling emits the S13 propagation edge instead)
        for repo, path in self.calls["write"]:
            if repo == "juniper-sibling":
                self.assertNotIn(path, {"tests/test_pyproject_extras.py", "AGENTS.md"})
        # every juniper-ml write is for the in-repo package's own subtree
        for repo, path in self.calls["write"]:
            if repo == "juniper-ml":
                self.assertTrue(path.startswith("juniper-thing/"), f"unexpected juniper-ml write {path!r}")

    def test_execute_commit_is_a_github_signed_api_commit(self):
        # Replaces the old `test_execute_commit_disables_gpg_signing`, which pinned the exact defect:
        # `-c commit.gpgsign=false` produced an UNSIGNED commit, and once the 2026-08-12 ruleset
        # normalization added `required_signatures` fleet-wide, every proposal PR became unmergeable
        # (cascor#515). A commit authored through GitHub's API is GitHub-signed / Verified.
        self._run_execute("--cross-repo")  # exercise BOTH repos' commits
        self.assertTrue(self.calls["commit"], "expected a signed-commit call in the --execute path")
        self.assertEqual({repo for repo, _b, _m, _o in self.calls["commit"]}, {"juniper-ml", "juniper-sibling"})
        for _repo, _branch, message, expected_head_oid in self.calls["commit"]:
            self.assertTrue(message, "commit must carry a headline")
            # optimistic concurrency: pinned to the tip we branched from, never blank
            self.assertTrue(expected_head_oid)
        # every edit rides in ONE commit per repo -- not one commit per file
        self.assertEqual(len(self.calls["commit"]), 2)

    def test_execute_path_makes_no_local_git_commit(self):
        # Anti-resurrection: the module must expose no local-git helper for the write path, or the
        # unsigned commit can grow back the next time someone needs a working tree. Targets the
        # executable forms only -- the ProposeSources docstring still NAMES the old flag when
        # explaining why it was removed, and that prose must stay readable.
        self.assertFalse(hasattr(pr, "_git"), "propose.py must not carry a local-git helper")
        src = Path(pr.__file__).read_text(encoding="utf-8")
        self.assertNotIn('"commit.gpgsign=false"', src)  # the argv-token literal
        self.assertNotIn('"git"', src)  # a subprocess argv naming the git binary
        self.assertNotIn('subprocess.run(["git"', src)

    def test_execute_proposal_direct_refuses_cross_repo_without_capability(self):
        # belt-and-suspenders: called directly WITHOUT capability, execute_proposal must never write a
        # sibling-repo proposal's edits into a checkout or open its PR.
        prop = pr.Proposal(pypi_name="juniper-sibling", repo="juniper-sibling", from_version="0.4.0", to_version="0.5.0", bump="minor", branch="release/juniper-sibling-v0.5.0")
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        url = pr.execute_proposal(prop, self._sources(), "main")  # cross_repo defaults False
        self.assertEqual(url, "")
        self.assertEqual(self.calls["write"], [])
        self.assertEqual(self.calls["branch"], [])
        self.assertEqual(self.calls["commit"], [])
        self.assertEqual(self.calls["pr"], [])

    def test_execute_proposal_direct_opens_sibling_when_capable(self):
        # the direct path is capability-aware too: --cross-repo + an on-disk sibling checkout opens it.
        prop = pr.Proposal(pypi_name="juniper-sibling", repo="juniper-sibling", from_version="0.4.0", to_version="0.5.0", bump="minor", branch="release/juniper-sibling-v0.5.0", pr_title="t", pr_body="b", commit_message="chore(release): juniper-sibling v0.5.0")
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        url = pr.execute_proposal(prop, self._sources(), "main", cross_repo=True, ecosystem_root=self.root)
        self.assertTrue(url)
        self.assertEqual(self.calls["pr"], [("juniper-sibling", "main", "release/juniper-sibling-v0.5.0")])
        self.assertIn(("juniper-sibling", "release/juniper-sibling-v0.5.0", "sha-juniper-sibling-main"), self.calls["branch"])
        self.assertIn(("juniper-sibling", "pyproject.toml"), self.calls["write"])


# ── Phase 4.2: dependency-aware ordering (topological sort + cycle detection) ──


def _reg_entry(name: str, deps=None, repo: str = "juniper-ml") -> "d.PackageEntry":
    return _entry(pypi_name=name, repo=repo, path=f"{name}/", depends_on=list(deps or []), tag_pattern=f"{name}-v*", archive_name=f"RELEASE_NOTES_{name}_v{{version}}.md", ship_paths=[f"{name}/{name.replace('-', '_')}/"])


class TopologicalOrderTest(unittest.TestCase):
    def test_real_registry_is_upstream_first_and_deterministic(self):
        # the real 18-package registry: every depends_on edge points strictly backwards, and the tier
        # spot-checks from plan S13 / the task hold; meta last, deterministic lexicographic root first.
        entries = d.load_registry(REPO_ROOT / "util" / "release_train" / "registry.yaml")
        order = pr.topological_order(entries)
        idx = {n: i for i, n in enumerate(order)}
        by_name = {e.pypi_name: e for e in entries}
        self.assertEqual(sorted(order), sorted(by_name), "topo order must be a permutation of every registered package")
        for e in entries:
            for dep in e.depends_on:
                if dep in by_name:
                    self.assertLess(idx[dep], idx[e.pypi_name], f"{dep} must precede its consumer {e.pypi_name}")
        for up, down in (("juniper-observability", "juniper-canopy"), ("juniper-service-core", "juniper-canopy"), ("juniper-observability", "juniper-cascor"), ("juniper-model-core", "juniper-cascor")):
            self.assertLess(idx[up], idx[down], f"{up} must precede {down}")
        self.assertEqual(order[-1], "juniper-ml", "the meta depends on all -> processed last")
        self.assertEqual(order[0], "juniper-cascor-model", "lexicographic tie-break among the dependency-free roots")

    def test_synthetic_diamond_tie_break_is_lexicographic(self):
        # a -> {b, c}; d -> {b, c}. b and c are both ready after a; the pypi_name tie-break orders b<c.
        entries = [_reg_entry("juniper-a"), _reg_entry("juniper-b", ["juniper-a"]), _reg_entry("juniper-c", ["juniper-a"]), _reg_entry("juniper-d", ["juniper-b", "juniper-c"])]
        self.assertEqual(pr.topological_order(entries), ["juniper-a", "juniper-b", "juniper-c", "juniper-d"])

    def test_order_independent_of_registry_file_order(self):
        forward = [_reg_entry("juniper-a"), _reg_entry("juniper-b", ["juniper-a"])]
        reversed_ = [_reg_entry("juniper-b", ["juniper-a"]), _reg_entry("juniper-a")]
        self.assertEqual(pr.topological_order(forward), pr.topological_order(reversed_))

    def test_non_registry_dependency_is_ignored(self):
        # a depends_on naming a package NOT in the registry does not constrain (or break) the ordering
        entries = [_reg_entry("juniper-a", ["juniper-not-registered"]), _reg_entry("juniper-b", ["juniper-a"])]
        self.assertEqual(pr.topological_order(entries), ["juniper-a", "juniper-b"])

    def test_cycle_raises_naming_the_cycle(self):
        entries = [_reg_entry("juniper-x", ["juniper-y"]), _reg_entry("juniper-y", ["juniper-z"]), _reg_entry("juniper-z", ["juniper-x"])]
        with self.assertRaises(pr.CycleError) as ctx:
            pr.topological_order(entries)
        msg = str(ctx.exception)
        for n in ("juniper-x", "juniper-y", "juniper-z"):
            self.assertIn(n, msg)


# ── Phase 4.2: consumer ceiling-bump follow-on PRs (D6) -- pure helpers ───────


class FollowOnHelperTest(unittest.TestCase):
    def test_requirement_names_package_tolerates_extras_marker(self):
        self.assertTrue(pr.requirement_names_package("juniper-model-core[crossval]>=0.2.0,<0.4.0", "juniper-model-core"))
        self.assertTrue(pr.requirement_names_package("juniper-model-core[a,b] >= 0.2.0", "juniper-model-core"))
        self.assertTrue(pr.requirement_names_package("juniper-service-core>=0.2.0,<0.5.0", "juniper-service-core"))  # plain form still matches
        self.assertFalse(pr.requirement_names_package("juniper-ml[tools,doc-tools]", "juniper-ml"))  # extras ref, NO version -> not a versioned pin
        self.assertFalse(pr.requirement_names_package("juniper-cascor-worker>=0.4.0", "juniper-cascor"))  # a longer package name never matches

    def test_consumer_pin_requirements_across_deps_and_extras(self):
        text = '[project]\nname = "c"\nversion = "0.1.0"\ndependencies = ["juniper-up>=0.2.0,<0.4.0", "other>=1"]\n\n[project.optional-dependencies]\ntest = ["juniper-up[conformance]>=0.2.0,<0.4.0"]\n'
        self.assertEqual(pr.consumer_pin_requirements(text, "juniper-up"), [("dependencies", "juniper-up>=0.2.0,<0.4.0"), ("[test]", "juniper-up[conformance]>=0.2.0,<0.4.0")])
        self.assertEqual(pr.consumer_pin_requirements("not valid toml [[", "juniper-up"), [])  # unparseable -> empty, never raises

    def test_escaped_pin_edits_raises_only_the_ceiling(self):
        pins = [("dependencies", "juniper-up>=0.2.0,<0.4.0"), ("[t]", "juniper-up[x]>=0.2.0,<0.4.0")]
        self.assertEqual(pr.escaped_pin_edits(pins, "0.4.0"), [("dependencies", "juniper-up>=0.2.0,<0.4.0", "juniper-up>=0.2.0,<0.5.0"), ("[t]", "juniper-up[x]>=0.2.0,<0.4.0", "juniper-up[x]>=0.2.0,<0.5.0")])
        self.assertEqual(pr.escaped_pin_edits([("dependencies", "juniper-up>=0.2.0,<0.9.0")], "0.4.0"), [])  # within range
        self.assertEqual(pr.escaped_pin_edits([("dependencies", "juniper-up>=0.2.0")], "0.4.0"), [])  # floor-only

    def test_follow_on_branch_and_dup_guard_delimiter(self):
        self.assertEqual(pr.follow_on_branch("juniper-model-core", "0.4.0"), "deps/juniper-model-core-ceiling-0.5.0")
        self.assertEqual(pr.follow_on_branch("juniper-x", "0.9.0"), "deps/juniper-x-ceiling-0.10.0")
        self.assertIsNotNone(pr.find_existing_follow_on_pr([{"number": 5, "headRefName": "deps/juniper-model-core-ceiling-0.5.0"}], "juniper-model-core"))
        # the -ceiling- delimiter keeps a shorter upstream from matching a longer one's branch
        self.assertIsNone(pr.find_existing_follow_on_pr([{"headRefName": "deps/juniper-cascor-model-ceiling-0.2.0"}], "juniper-cascor"))


# ── Phase 4.2: follow-on generation through build_proposal (the S12-4.2 verify) ──


def _write_consumer_pyproject(base_dir: Path, name: str, deps: list, opt_deps: "dict | None" = None, version: str = "0.1.0") -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    lines = ["[project]", f'name = "{name}"', f'version = "{version}"', "dependencies = ["]
    lines += [f'    "{dep}",' for dep in deps]
    lines.append("]")
    if opt_deps:
        lines += ["", "[project.optional-dependencies]"]
        for extra, reqs in opt_deps.items():
            lines.append(f"{extra} = [")
            lines += [f'    "{r}",' for r in reqs]
            lines.append("]")
    (base_dir / "pyproject.toml").write_text("\n".join(lines) + "\n")


class FollowOnBuildProposalTest(unittest.TestCase):
    """A simulated in-repo upstream MINOR bump with four sibling consumers (escaped ceiling / within
    range / floor-only / extras-form ceiling). Offline: consumer pyprojects live under the ecosystem
    root; build_proposal reads them and never writes."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        _write_pkg(self.repo_root, "juniper-up/", name="juniper-up", version="0.3.0", changelog=_CHANGELOG)  # upstream, in-repo
        self.eco = self.root
        _write_consumer_pyproject(self.eco / "juniper-cons-escaped", "juniper-cons-escaped", ["juniper-up>=0.2.0,<0.4.0"])
        _write_consumer_pyproject(self.eco / "juniper-cons-within", "juniper-cons-within", ["juniper-up>=0.2.0,<0.9.0"])
        _write_consumer_pyproject(self.eco / "juniper-cons-floor", "juniper-cons-floor", ["juniper-up>=0.2.0"])
        _write_consumer_pyproject(self.eco / "juniper-cons-extras", "juniper-cons-extras", ["numpy>=1"], opt_deps={"test": ["juniper-up[conformance]>=0.2.0,<0.4.0"]})
        self.fake = _FakeSources(self.repo_root, self.eco)
        self.up = _entry(pypi_name="juniper-up", path="juniper-up/")
        self.entries = [
            self.up,
            _entry(pypi_name="juniper-cons-escaped", repo="juniper-cons-escaped", path=".", depends_on=["juniper-up"]),
            _entry(pypi_name="juniper-cons-within", repo="juniper-cons-within", path=".", depends_on=["juniper-up"]),
            _entry(pypi_name="juniper-cons-floor", repo="juniper-cons-floor", path=".", depends_on=["juniper-up"]),
            _entry(pypi_name="juniper-cons-extras", repo="juniper-cons-extras", path=".", depends_on=["juniper-up"]),
        ]

    def tearDown(self):
        self._tmp.cleanup()

    def _pkg(self, **over):
        base = {"pypi_name": "juniper-up", "released_version": "0.3.0", "declared_version": "0.3.0", "proposed_version": "0.4.0"}
        base.update(over)
        return _manifest_pkg(**base)

    def _prop(self, cross_repo=True, pkg=None):
        before = _sha_tree(self.repo_root)
        prop = pr.build_proposal(self.up, pkg or self._pkg(), self.fake.build(), self.repo_root, self.eco, self.entries, "2026-07-22", cross_repo=cross_repo)
        self.assertEqual(before, _sha_tree(self.repo_root), "build_proposal must write nothing (dry-run purity), even with follow-ons")
        return prop

    def test_verify_step_4_2_expected_edges_and_follow_on_content(self):
        # PLAN S12 step 4.2 verify: a simulated upstream MINOR bump produces the expected downstream
        # propagation edges -- plus (Phase 4.2) the ceiling-bump follow-on content per escaped consumer.
        prop = self._prop(cross_repo=True)
        states = {e["consumer"]: e["consumer_pin_state"] for e in prop.propagation_edges}
        self.assertEqual(states["juniper-cons-escaped"], pr.PIN_ESCAPED_FOLLOWON)
        self.assertEqual(states["juniper-cons-extras"], pr.PIN_ESCAPED_FOLLOWON)
        self.assertEqual(states["juniper-cons-within"], pr.PIN_WITHIN_RANGE)
        self.assertEqual(states["juniper-cons-floor"], pr.PIN_FLOOR_ONLY)
        fos = {f.consumer: f for f in prop.follow_on_prs}
        self.assertEqual(set(fos), {"juniper-cons-escaped", "juniper-cons-extras"}, "follow-ons ONLY for escaped ceilings")
        esc = fos["juniper-cons-escaped"]
        self.assertEqual(esc.repo, "juniper-cons-escaped")  # opens in the CONSUMER's repo
        self.assertEqual(esc.branch, "deps/juniper-up-ceiling-0.5.0")
        self.assertFalse(esc.skipped)
        self.assertEqual(esc.pin_changes, [("dependencies", "juniper-up>=0.2.0,<0.4.0", "juniper-up>=0.2.0,<0.5.0")])
        self.assertEqual([e.path for e in esc.edits], ["pyproject.toml"])
        self.assertIn("juniper-up>=0.2.0,<0.5.0", esc.edits[0].new_text)  # ceiling raised
        self.assertIn("juniper-up>=0.2.0", esc.edits[0].new_text)  # floor preserved
        self.assertNotIn("<0.4.0", esc.edits[0].new_text)
        # the extras-form pin is edited in place (floor + [extra] preserved, only ceiling raised)
        ext = fos["juniper-cons-extras"]
        self.assertEqual(ext.pin_changes, [("[test]", "juniper-up[conformance]>=0.2.0,<0.4.0", "juniper-up[conformance]>=0.2.0,<0.5.0")])
        self.assertIn("juniper-up[conformance]>=0.2.0,<0.5.0", ext.edits[0].new_text)
        # body cites S13, the triggering release proposal, and the 2026-07-06 incident precedent
        self.assertIn("S13", esc.pr_body or "")
        self.assertIn("release/juniper-up-v0.4.0", esc.pr_body or "")
        self.assertIn("2026-07-06 ci-tools incident", esc.pr_body or "")
        # title/commit name the raised ceiling + the consumer
        self.assertIn("<0.5.0", esc.pr_title or "")
        self.assertIn("juniper-cons-escaped", esc.pr_title or "")
        # the proposal PR body surfaces every edge's pin state + a follow-on section
        self.assertIn("escaped -> follow-on", prop.pr_body or "")
        self.assertIn("deps/juniper-up-ceiling-0.5.0", prop.pr_body or "")

    def test_degraded_mode_skips_siblings_with_reason_but_keeps_content(self):
        prop = self._prop(cross_repo=False)
        esc_edge = next(e for e in prop.propagation_edges if e["consumer"] == "juniper-cons-escaped")
        self.assertTrue(esc_edge["consumer_pin_state"].startswith("escaped -> skipped("))
        self.assertIn("single-repo GITHUB_TOKEN", esc_edge["consumer_pin_state"])
        fo = next(f for f in prop.follow_on_prs if f.consumer == "juniper-cons-escaped")
        self.assertTrue(fo.skipped)
        self.assertTrue(fo.edits, "content is still computed for the dry-run preview even when skipped")
        self.assertEqual(fo.pin_changes, [("dependencies", "juniper-up>=0.2.0,<0.4.0", "juniper-up>=0.2.0,<0.5.0")])

    def test_dup_guard_suppresses_follow_on_per_consumer_repo(self):
        self.fake.open_prs["juniper-cons-escaped"] = [{"number": 9, "headRefName": "deps/juniper-up-ceiling-0.5.0"}]
        prop = self._prop(cross_repo=True)
        esc_edge = next(e for e in prop.propagation_edges if e["consumer"] == "juniper-cons-escaped")
        self.assertIn("dup-guard", esc_edge["consumer_pin_state"])
        fo = next(f for f in prop.follow_on_prs if f.consumer == "juniper-cons-escaped")
        self.assertTrue(fo.skipped)
        self.assertIn("#9", fo.skipped_reason or "")
        # a DIFFERENT consumer with no open dup is unaffected -> still a live follow-on
        self.assertEqual(next(f for f in prop.follow_on_prs if f.consumer == "juniper-cons-extras").consumer_pin_state, pr.PIN_ESCAPED_FOLLOWON)

    def test_patch_bump_produces_no_edges_and_no_follow_ons(self):
        prop = self._prop(cross_repo=True, pkg=self._pkg(proposed_bump="patch", proposed_version="0.3.1"))
        self.assertEqual(prop.propagation_edges, [])
        self.assertEqual(prop.follow_on_prs, [])

    def test_unreadable_consumer_pyproject_is_unknown_not_a_follow_on(self):
        # a registry consumer whose checkout is absent -> honest "unknown", never a follow-on
        entries = [self.up, _entry(pypi_name="juniper-cons-absent", repo="juniper-cons-absent", path=".", depends_on=["juniper-up"])]
        prop = pr.build_proposal(self.up, self._pkg(), self.fake.build(), self.repo_root, self.eco, entries, "2026-07-22", cross_repo=True)
        edge = next(e for e in prop.propagation_edges if e["consumer"] == "juniper-cons-absent")
        self.assertIn("unknown", edge["consumer_pin_state"])
        self.assertEqual(prop.follow_on_prs, [])

    def test_meta_consumer_deferred_never_a_follow_on_on_sibling_upstream(self):
        # a SIBLING upstream with the meta as a ceiling-pinning consumer: meta is deferred (Q-META), no PR
        up_sib = _entry(pypi_name="juniper-sib-up", repo="juniper-sib-up", path=".")
        _write_consumer_pyproject(self.eco / "juniper-sib-up", "juniper-sib-up", ["numpy>=1"], version="0.3.0")
        (self.eco / "juniper-sib-up" / "CHANGELOG.md").write_text(_CHANGELOG)
        (self.repo_root / "pyproject.toml").write_text('[project]\nname = "juniper-ml"\nversion = "0.6.0"\ndependencies = []\n\n[project.optional-dependencies]\nservers = ["juniper-sib-up>=0.2.0,<0.4.0"]\n')
        meta = _entry(pypi_name="juniper-ml", repo="juniper-ml", path=".", depends_on=["juniper-sib-up"])
        pkg = _manifest_pkg(pypi_name="juniper-sib-up", repo="juniper-sib-up", released_version="0.3.0", declared_version="0.3.0", proposed_version="0.4.0")
        prop = pr.build_proposal(up_sib, pkg, self.fake.build(), self.repo_root, self.eco, [up_sib, meta], "2026-07-22", cross_repo=True)
        meta_edge = next(e for e in prop.propagation_edges if e["consumer"] == "juniper-ml")
        self.assertIn("deferred", meta_edge["consumer_pin_state"])
        self.assertNotIn("juniper-ml", {f.consumer for f in prop.follow_on_prs})


# ── Phase 4.2: execute_follow_on (hermetic spies) + CLI ordering / cycle ─────


class ExecuteFollowOnTest(unittest.TestCase):
    def setUp(self):
        self.calls = {"write": [], "branch": [], "commit": [], "pr": []}
        self._tmp = tempfile.TemporaryDirectory()
        self.eco = Path(self._tmp.name)
        (self.eco / "juniper-cascor").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def _sources(self) -> pr.ProposeSources:
        def open_pr(repo, base, head, title, body):
            self.calls["pr"].append((repo, base, head))
            return f"https://github.com/pcalnon/{repo}/pull/2"

        def create_signed_commit(repo, branch, message, additions, expected_head_oid):
            self.calls["write"].extend((repo, path) for path, _contents in additions)
            self.calls["commit"].append((repo, branch, message, expected_head_oid))
            return "c0ffee"

        return pr.ProposeSources(
            read_file=lambda e, f: None,
            list_open_prs=lambda repo: [],
            resolve_ref_sha=lambda repo, ref: f"sha-{repo}-{ref}",
            create_branch=lambda repo, branch, sha: self.calls["branch"].append((repo, branch, sha)),
            create_signed_commit=create_signed_commit,
            open_pr=open_pr,
        )

    def _fo(self, skipped=None) -> pr.FollowOnPR:
        fo = pr.FollowOnPR(consumer="juniper-cascor", repo="juniper-cascor", upstream="juniper-model-core", upstream_version="0.4.0", pin_file="pyproject.toml", pin_changes=[("dependencies", "juniper-model-core>=0.2.0,<0.4.0", "juniper-model-core>=0.2.0,<0.5.0")], branch="deps/juniper-model-core-ceiling-0.5.0", consumer_pin_state=pr.PIN_ESCAPED_FOLLOWON, commit_message="chore(deps): raise juniper-model-core ceiling to <0.5.0 for its v0.4.0 release", pr_title="t", pr_body="b")
        fo.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        if skipped:
            fo.skipped_reason = skipped
        return fo

    def test_opens_in_consumer_repo_with_a_signed_commit_when_capable(self):
        # The follow-on lane carries the SAME unsigned-commit defect as the proposal lane and is fixed
        # by the same shared helper -- fixing only one would leave consumer-pin PRs unmergeable.
        url = pr.execute_follow_on(self._fo(), self._sources(), "main", cross_repo=True, ecosystem_root=self.eco)
        self.assertTrue(url)
        self.assertEqual(self.calls["pr"], [("juniper-cascor", "main", "deps/juniper-model-core-ceiling-0.5.0")])
        self.assertIn(("juniper-cascor", "deps/juniper-model-core-ceiling-0.5.0", "sha-juniper-cascor-main"), self.calls["branch"])
        self.assertIn(("juniper-cascor", "pyproject.toml"), self.calls["write"])
        self.assertEqual(len(self.calls["commit"]), 1)
        repo, branch, message, expected_head_oid = self.calls["commit"][0]
        self.assertEqual(repo, "juniper-cascor")
        self.assertEqual(branch, "deps/juniper-model-core-ceiling-0.5.0")
        self.assertIn("juniper-model-core", message)
        self.assertEqual(expected_head_oid, "sha-juniper-cascor-main")

    def test_refuses_without_cross_repo_capability(self):
        url = pr.execute_follow_on(self._fo(), self._sources(), "main")  # cross_repo defaults False
        self.assertEqual(url, "")
        self.assertEqual(self.calls, {"write": [], "branch": [], "commit": [], "pr": []})

    def test_refuses_a_skipped_follow_on(self):
        url = pr.execute_follow_on(self._fo(skipped="dup-guard: open ceiling-bump PR"), self._sources(), "main", cross_repo=True, ecosystem_root=self.eco)
        self.assertEqual(url, "")
        self.assertEqual(self.calls["pr"], [])


class CliOrderingAndCycleTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo_root = self.root / "juniper-ml"
        self.repo_root.mkdir()
        _install_templates(self.repo_root)
        self.fake = _FakeSources(self.repo_root, self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _reg(self, name, deps):
        deps_str = "[" + ", ".join(deps) + "]"
        return f'  - {{pypi_name: {name}, repo: juniper-ml, path: "{name}/", version_source: static, tag_pattern: "{name}-v*", archive_name: "RELEASE_NOTES_{name}_v{{version}}.md", trigger: {{now: release, target: release}}, verify: {{now: strict, target: strict}}, depends_on: {deps_str}, ship_paths: ["{name}/{name}/"], exclude_paths: []}}'

    def test_cyclic_registry_exits_two(self):
        registry = self.root / "registry.yaml"
        registry.write_text("packages:\n" + self._reg("juniper-x", ["juniper-y"]) + "\n" + self._reg("juniper-y", ["juniper-x"]) + "\n")
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"packages": [_manifest_pkg(pypi_name="juniper-x")]}))
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pr.main(["--manifest", str(manifest), "--repo-root", str(self.repo_root), "--registry", str(registry)], sources=self.fake.build())
        self.assertEqual(code, 2)

    def test_eligible_packages_processed_upstream_first(self):
        # the manifest lists the DOWNSTREAM first; the topo sort must reorder to upstream-first.
        registry = self.root / "registry.yaml"
        registry.write_text("packages:\n" + self._reg("juniper-down", ["juniper-upp"]) + "\n" + self._reg("juniper-upp", []) + "\n")
        _write_pkg(self.repo_root, "juniper-down/", name="juniper-down", version="0.4.0", changelog=_CHANGELOG)
        _write_pkg(self.repo_root, "juniper-upp/", name="juniper-upp", version="0.4.0", changelog=_CHANGELOG)
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"packages": [_manifest_pkg(pypi_name="juniper-down"), _manifest_pkg(pypi_name="juniper-upp")]}))
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pr.main(["--manifest", str(manifest), "--repo-root", str(self.repo_root), "--ecosystem-root", str(self.root), "--registry", str(registry), "--release-date", "2026-07-22", "--json"], sources=self.fake.build())
        self.assertEqual(code, 0, buf.getvalue())
        order = [p["pypi_name"] for p in json.loads(buf.getvalue())["proposals"]]
        self.assertEqual(order, ["juniper-upp", "juniper-down"], "upstream juniper-upp must be proposed before its consumer despite manifest order")


class ExecuteProposalSeamTest(unittest.TestCase):
    """Direct ``execute_proposal`` gates: missing write seam + skipped/branchless no-ops.

    Open #749 covers ``build_proposal`` refusal stubs; #730 covers ceremony archive
    execute + the propose *step-summary* rehearsal. These pin the function's own
    early exits so ``--execute`` never partial-writes on a miswired seam and never
    opens a PR for a skipped/branchless stub.
    """

    def _recording_sources(self) -> "tuple[pr.ProposeSources, dict]":
        calls: dict = {"write": [], "branch": [], "commit": [], "pr": []}

        def open_pr(repo, base, head, title, body):
            calls["pr"].append((repo, base, head))
            return f"https://example.invalid/{repo}/pull/1"

        def create_signed_commit(repo, branch, message, additions, expected_head_oid):
            calls["write"].extend((repo, path) for path, _contents in additions)
            calls["commit"].append((repo, branch, message, expected_head_oid))
            return "c0ffee"

        sources = pr.ProposeSources(
            read_file=lambda _entry, _filename: None,
            list_open_prs=lambda _repo: [],
            resolve_ref_sha=lambda repo, ref: f"sha-{repo}-{ref}",
            create_branch=lambda repo, branch, sha: calls["branch"].append((repo, branch, sha)),
            create_signed_commit=create_signed_commit,
            open_pr=open_pr,
        )
        return sources, calls

    def test_execute_proposal_raises_when_write_seam_missing(self):
        prop = pr.Proposal(
            pypi_name="juniper-thing",
            repo="juniper-ml",
            from_version="0.4.0",
            to_version="0.5.0",
            bump="minor",
            branch="release/juniper-thing-v0.5.0",
        )
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        dry_sources = pr.ProposeSources(
            read_file=lambda _entry, _filename: None,
            list_open_prs=lambda _repo: [],
        )
        with self.assertRaises(pr.SourceError) as ctx:
            pr.execute_proposal(prop, dry_sources, "main")
        self.assertIn("execute mode needs", str(ctx.exception))

    def test_execute_proposal_skipped_returns_empty_without_writes(self):
        sources, calls = self._recording_sources()
        prop = pr.Proposal(
            pypi_name="juniper-thing",
            repo="juniper-ml",
            from_version="0.4.0",
            to_version="0.5.0",
            bump="minor",
            branch="release/juniper-thing-v0.5.0",
            skipped_reason="dup-guard: open release PR already exists (#9 release/juniper-thing-v0.5.0)",
        )
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        self.assertEqual(pr.execute_proposal(prop, sources, "main"), "")
        self.assertEqual(calls["write"], [])
        self.assertEqual(calls["branch"], [])
        self.assertEqual(calls["commit"], [])
        self.assertEqual(calls["pr"], [])

    def test_execute_proposal_missing_branch_returns_empty_without_writes(self):
        sources, calls = self._recording_sources()
        prop = pr.Proposal(
            pypi_name="juniper-thing",
            repo="juniper-ml",
            from_version="0.4.0",
            to_version="0.5.0",
            bump="minor",
            branch=None,
        )
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        self.assertEqual(pr.execute_proposal(prop, sources, "main"), "")
        self.assertEqual(calls["write"], [])
        self.assertEqual(calls["branch"], [])
        self.assertEqual(calls["commit"], [])
        self.assertEqual(calls["pr"], [])


if __name__ == "__main__":
    unittest.main()
