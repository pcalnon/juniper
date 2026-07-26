# Release-Train Follow-Up: Treat `_version.py` as a Lockstep Artifact for Static-Version Packages

**Project**: Juniper
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**Date**: 2026-07-23
**Status**: IMPLEMENTED — Option A shipped in juniper-ml#710 (ml#701); Option B (flip all static → `dynamic = ["version"]`) remains parked

---

## 1. Incident record (two live instances of the same class)

1. **juniper-ci-tools 0.7.0 (2026-07-21).** The release-train proposal PR (juniper-ml#668) bumped
   `juniper-ci-tools/pyproject.toml` `[project].version` to `0.7.0` but left
   `juniper_ci_tools/_version.py` at `0.6.0`. The shipped 0.7.0 wheel's metadata was correct while its
   `__version__` dunder reported `0.6.0` (every `--version` surface lies). Caught only because ci-tools
   has per-consumer dunder-match drift gates (`tests/test_coverage_gap_mapper_drift.py` /
   `tests/test_env_drift_check_drift.py`, `test_version_dunder_matches_pyproject`), which went red on
   main alongside the workflow-pin drift; both were fixed by juniper-ml#684.
2. **juniper-service-core 0.5.0 (shipped 2026-07-18; discovered 2026-07-23 while writing this
   document).** The #657 release proposal bumped `juniper-service-core/pyproject.toml` to `0.5.0`;
   `juniper_service_core/_version.py` still read `0.4.0` at main `69efc9c`. The shipped 0.5.0 wheel
   carried the stale dunder. **No gate existed for service-core, so nothing went red — the drift sat
   undetected for five days.** Healed in-repo by juniper-ml#702 (repo copy); the shipped wheel heals
   at the next release.

## 2. Root cause

`util/release_train/propose.py` treated the version bump as an either/or on the registry's `version_source` (pre-#710 apply site):

- `dynamic` → edit `<path>/<import_package>/_version.py` via `set_dynamic_version`;
- `static` → edit `pyproject.toml` `[project].version` via `set_pyproject_version` **only**.

But the two mechanisms are not mutually exclusive in this codebase: **all five static-version in-repo packages also carry a `_version.py` `__version__` dunder** ("Single source of truth for the package version" — which the static release path silently falsified):

| Package | version_source | `_version.py` present | Notes |
| --- | --- | --- | --- |
| juniper-ci-tools | static | yes | healed by ml#684; now lockstep-gated |
| juniper-config-tools | static | yes | lockstep-gated |
| juniper-doc-tools | static | yes | lockstep-gated |
| juniper-observability | static | yes | lockstep-gated |
| juniper-service-core | static | yes | healed by ml#702; now lockstep-gated |
| juniper-model-core (+3 recurrence pkgs, cross-repo) | dynamic | yes | n/a (dynamic path edits the dunder) |

This is the RK-11 lockstep-artifact class (the same philosophy that moved the meta extras pin + `tests/test_pyproject_extras.py` + the AGENTS.md table together in ml#661).

## 3. Design of record (Option A — shipped)

1. **propose.py**: after the `static` branch edits `pyproject.toml`, additionally check
   `sources.read_file(entry, dunder_file_rel(entry))`; when the file exists, run
   `set_dynamic_version` on it and append the `FileEdit` — one lockstep artifact, mirroring the
   in-repo co-change pattern. No registry schema change (auto-detection by file presence avoids a new
   field that could itself drift). The proposal body / co-change checklist names the dunder edit the
   same way it names the AGENTS.md co-change. A present-but-unparseable dunder is left alone and
   flagged `REQUIRED-manual`.
2. **Tests** (`tests/test_release_train_propose.py`, hermetic): static-with-dunder bumps BOTH files;
   static-without-dunder emits no phantom `_version.py` edit; the dynamic path is unchanged;
   unparseable dunder → no edit + REQUIRED-manual checklist item; the proposal body mentions the
   dunder co-change.
3. **Generic gate** (`tests/test_release_train_registry.py::VersionDunderLockstepTest`): asserts
   `pyproject [project].version == _version.py __version__` for every in-repo package that has both —
   closes the "service-core had no gate" hole. Dynamic packages are exempt (their dunder IS the
   version source). The ci-tools-specific consumer gates remain as belt-and-braces.
4. **Out of scope (Option B, still parked)**: flipping all five static packages to
   `dynamic = ["version"]` would dissolve the class structurally, but needs
   `[tool.setuptools.dynamic]` wiring ×5, five registry `version_source` flips, and updates to the
   registry test's dynamic-set assertions. Option A ships the protection now; B remains available
   later.

## 4. Acceptance criteria

1. A release-train proposal for any static-with-dunder in-repo package produces a PR whose diff bumps `pyproject.toml` AND `_version.py` together. — **met** (hermetic propose tests in #710).
2. The hermetic propose tests cover the three shapes in §3 (+ the unparseable-manual shape) and pass. — **met**.
3. The generic dunder-lockstep gate is wired into CI (the standard unittest battery) and is green. — **met** (`VersionDunderLockstepTest` in `tests/test_release_train_registry.py`).
4. `util/release_train/` docstrings + the release-train plan doc's co-change inventory mention the dunder artifact. — **met** in #710 (plan §5.4 + `propose.py` module docstring + AGENTS.md).

## 5. Grounding / validation record

Probed 2026-07-23 at juniper-ml main `69efc9c` by the authoring session: `propose.py` apply-site and
helper line numbers; registry `version_source` values; per-package `_version.py` presence and
pyproject/dunder comparison; gate inventory (`grep` for dunder asserts — ci-tools consumer gates only
pre-#710; doc-tools' `test_cli.py` asserts its `--version` output matches its own dunder, which is
self-consistent and would NOT catch a pyproject/dunder split). The service-core live drift was
discovered during that probe and healed in juniper-ml#702.

## 6. Implementation record (juniper-ml#710)

Option A (design of record) landed in [juniper-ml#710](https://github.com/pcalnon/juniper-ml/pull/710):

| Acceptance (§4) | Where it landed |
|---|---|
| Static-with-dunder proposal bumps `pyproject.toml` **and** `_version.py` together; body names the co-change | `util/release_train/propose.py` step 3a (`dunder_file_rel` / `dunder_cochange_rel`; auto-detect by file presence, no registry field); hermetic shapes in `tests/test_release_train_propose.py` |
| Hermetic propose tests cover the §3.2 shapes (+ unparseable → REQUIRED-manual) | `tests/test_release_train_propose.py` (both-bumped / no-phantom / dynamic-unchanged / unparseable-REQUIRED-manual); edge cases in juniper-ml#712 |
| Generic pyproject==dunder gate in CI | `tests/test_release_train_registry.py` `VersionDunderLockstepTest` (always-on; hard-pins eligible count at 5; dynamic exempt; #712 adds synthetic bite-proof + path agreement with `propose.dunder_file_rel`) |
| Docs / plan inventory mention the dunder artifact | Plan §5.4 atomicity co-changes; `propose.py` module docstring; AGENTS.md; operator runbook Gate 1 review table (juniper-ml#711; re-entry nuance below) |

**Operator surface:** when reviewing a Gate 1 proposal for a static-with-dunder package, expect both
files in the diff, **or** a REQUIRED-manual checklist item if the dunder is unparseable, **or** a
pyproject-only diff with no dunder checklist when `__version__` already equals the proposed
`to_version` (partial heal / re-entry — silent success after #712). See the release-train
[operator runbook](JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.2.

### 6.1 Coverage follow-up (juniper-ml#712)

[juniper-ml#712](https://github.com/pcalnon/juniper-ml/pull/712) hardens the hermetic edge cases #710's
happy path missed and fixes one checklist correctness bug found while writing them:

| Shape / fix | Contract |
|---|---|
| Already-at-target dunder | No phantom `_version.py` edit; **no** REQUIRED-manual checklist line (pre-#712 falsely REQUIRED'd a correct dunder) |
| Unparseable dunder | Checklist REQUIRED; PR body must **not** claim a lockstep co-change landed |
| Single-quoted `__version__ = '…'` | Still bumps (quote-style skip would recreate the stale-dunder class) |
| Edit ordering | Dunder `FileEdit` is `edits[1]` before CHANGELOG so `dunder_cochange_rel` stays correct |

**Still available later (Option B, §3.4):** flipping all five static packages to `dynamic = ["version"]` would dissolve the class structurally; not required once Option A + the always-on gate are in place.
