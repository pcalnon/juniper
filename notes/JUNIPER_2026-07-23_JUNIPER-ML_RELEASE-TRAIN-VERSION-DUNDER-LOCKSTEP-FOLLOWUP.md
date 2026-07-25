# Release-Train Follow-Up: Treat `_version.py` as a Lockstep Artifact for Static-Version Packages

**Project**: Juniper
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**Date**: 2026-07-23
**Status**: IMPLEMENTED — Option A shipped in [juniper-ml#710](https://github.com/pcalnon/juniper-ml/pull/710) (2026-07-25)

---

## 1. Incident record (two live instances of the same class)

1. **juniper-ci-tools 0.7.0 (2026-07-21).** The release-train proposal PR (juniper-ml#668) bumped `juniper-ci-tools/pyproject.toml` `[project].version` to `0.7.0` but left `juniper_ci_tools/_version.py` at `0.6.0`. The shipped 0.7.0 wheel's metadata was correct while its `__version__` dunder reported `0.6.0` (every `--version` surface lies). Caught only because ci-tools happens to have per-consumer dunder-match drift gates (`tests/test_coverage_gap_mapper_drift.py` / `tests/test_env_drift_check_drift.py`, `test_version_dunder_matches_pyproject`), which went red on main alongside the workflow-pin drift; both were fixed by juniper-ml#684.
2. **juniper-service-core 0.5.0 (shipped 2026-07-18; discovered 2026-07-23 while writing this document).** The #657 release proposal bumped `juniper-service-core/pyproject.toml` to `0.5.0`; `juniper_service_core/_version.py` still reads `0.4.0` at main `69efc9c`. The shipped 0.5.0 wheel carries the stale dunder. **No gate exists for service-core, so nothing went red — the drift sat undetected for five days.** A companion one-line fix PR repoints the repo copy (the shipped wheel heals at the next release); see the PR referencing this document.

## 2. Root cause

`util/release_train/propose.py` treats the version bump as an either/or on the registry's `version_source` (apply site at `propose.py:1033-1035` @ `69efc9c`):

- `dynamic` → edit `<path>/<import_package>/_version.py` via `set_dynamic_version` (`:308`), path from `_version_py_relpath(entry)` (`:285`);
- `static` → edit `pyproject.toml` `[project].version` via `set_pyproject_version` (`:289`) **only**.

But the two mechanisms are not mutually exclusive in this codebase: **all five static-version in-repo packages also carry a `_version.py` `__version__` dunder** ("Single source of truth for the package version" — which the static release path silently falsifies):

| Package | version_source | `_version.py` present | pyproject vs dunder @ 69efc9c |
| --- | --- | --- | --- |
| juniper-ci-tools | static | yes | 0.7.0 = 0.7.0 (healed by ml#684) |
| juniper-config-tools | static | yes | 0.1.0 = 0.1.0 |
| juniper-doc-tools | static | yes | 0.1.1 = 0.1.1 |
| juniper-observability | static | yes | 0.4.0 = 0.4.0 |
| juniper-service-core | static | yes | **0.5.0 ≠ 0.4.0 — live drift** |
| juniper-model-core (+3 recurrence pkgs, cross-repo) | dynamic | yes | n/a (dynamic path edits the dunder) |

Every future static-package release re-creates the drift until propose.py changes. This is the RK-11 lockstep-artifact class (the same philosophy that moved the meta extras pin + `tests/test_pyproject_extras.py` + the AGENTS.md table together in ml#661).

## 3. Proposed design (for the implementing session)

1. **propose.py**: in the version-bump application block (`:1033-1035` region), after the `static` branch edits `pyproject.toml`, additionally check `sources.read_file(entry, _version_py_relpath(entry))`; when the file exists, run `set_dynamic_version` on it and append the `FileEdit` — one lockstep artifact, mirroring the in-repo co-change pattern. No registry schema change needed (auto-detection by file presence avoids a new field that could itself drift). The proposal body / co-change checklist should name the dunder edit the same way it names the AGENTS.md co-change.
2. **Tests** (`tests/test_release_train_propose.py`, hermetic): a static-with-dunder package bumps BOTH files; a static package without `_version.py` is untouched beyond pyproject (no phantom edit); the dynamic path is unchanged; the proposal body mentions the dunder co-change.
3. **Generic gate** (so the class can never ship silently again, train or no train): a lint asserting `pyproject [project].version == _version.py __version__` for every in-repo package that has both — natural homes: extend `tests/test_release_train_registry.py` (it already resolves all in-repo package versions) or a small standalone `tests/test_version_dunder_lockstep.py`. This closes the "service-core had no gate" hole that let instance #2 sit undetected; the ci-tools-specific gates remain as consumer-side belt-and-braces.
4. **Out of scope**: retro-fixing shipped wheels (impossible); cross-repo packages (all four dynamic — already handled); changing any package to `dynamic = ["version"]` (a larger convention decision the owner may prefer instead — if every static package flipped to dynamic, the class disappears structurally; worth a line in the implementation PR for the owner to weigh).

## 4. Acceptance criteria

1. A release-train proposal for any static-with-dunder in-repo package produces a PR whose diff bumps `pyproject.toml` AND `_version.py` together.
2. The hermetic propose tests cover the three shapes in §3.2 and pass.
3. The generic dunder-lockstep gate is wired into CI (the standard unittest battery) and is green at the implementing HEAD — which requires the service-core drift already healed (companion fix PR to this document).
4. `util/release_train/` docs strings + the release-train plan doc's co-change inventory mention the dunder artifact.

## 5. Grounding / validation record

Probed 2026-07-23 at juniper-ml main `69efc9c` by the authoring session: `propose.py` apply-site and helper line numbers; registry `version_source` values; per-package `_version.py` presence and pyproject/dunder comparison (table above); gate inventory (`grep` for dunder asserts — ci-tools consumer gates only; doc-tools' `test_cli.py` asserts its `--version` output matches its own dunder, which is self-consistent and would NOT catch a pyproject/dunder split). The service-core live drift was discovered during this probe and is being fixed in a companion PR alongside this document's PR.

## 6. Implementation record (juniper-ml#710)

Option A (design of record) landed in [juniper-ml#710](https://github.com/pcalnon/juniper-ml/pull/710):

| Acceptance (§4) | Where it landed |
|---|---|
| Static-with-dunder proposal bumps `pyproject.toml` **and** `_version.py` together; body names the co-change | `util/release_train/propose.py` step 3a (`dunder_file_rel` / `dunder_cochange_rel`; auto-detect by file presence, no registry field); hermetic shapes in `tests/test_release_train_propose.py` |
| Hermetic propose tests cover the §3.2 shapes (+ unparseable → REQUIRED-manual) | `tests/test_release_train_propose.py` (both-bumped / no-phantom / dynamic-unchanged / unparseable-REQUIRED-manual) |
| Generic pyproject==dunder gate in CI | `tests/test_release_train_registry.py` `VersionDunderLockstepTest` (always-on; hard-pins eligible count at 5; dynamic exempt) |
| Docs / plan inventory mention the dunder artifact | Plan §5.4 atomicity co-changes; `propose.py` module docstring; AGENTS.md; operator runbook Gate 1 review table |

**Operator surface:** when reviewing a Gate 1 proposal for a static-with-dunder package, expect both files in the diff (or a REQUIRED-manual checklist item if the dunder is unparseable). See the release-train
[operator runbook](JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.2.

**Still available later (Option B, §3.4):** flipping all five static packages to `dynamic = ["version"]` would dissolve the class structurally; not required once Option A + the always-on gate are in place.
