# `util/ad-hoc/` — Single-use, temporary, and unfinished scripts

This directory is the home for scripts that:

- Will run once (or a handful of times) and then be **retained as provenance** of the work they produced (retention policy, owner decision 2026-08-25 — see Lifecycle below).
- Are work-in-progress and not yet ready for promotion to `util/` proper.
- Support a one-off investigation, migration, or analysis tied to a specific PR / incident.

It exists because the alternative — authoring such scripts in `/tmp/` — caused real, irrecoverable loss in the v1–v4 requirements-snapshot effort (`phase4_consolidate.py`, `v2_citation_validate.py`). See [`../../notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §7](../../notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection) and [plan-doc §12](../../notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md#12-open-issues--questions-discovered-during-execution).

The repo-level rule lives in [`../../AGENTS.md`](../../AGENTS.md#script-placement-mandatory); the ecosystem-level restatement lives in the parent `Juniper/AGENTS.md` "Cross-Project Conventions" section (one directory above this repo, outside the juniper-ml git tree).

---

## Conventions

### File header (Python)

Every Python script in this directory should declare its scope and lifecycle inline:

```python
"""
<one-line purpose>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: <name>
Created: YYYY-MM-DD
Status: ad-hoc — <intent: one-off | wip | migration | investigation>
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: <PR #, incident, or notes/ doc>
"""
```

### File header (bash)

```bash
#!/usr/bin/env bash
# <one-line purpose>
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     <name>
# Created:    YYYY-MM-DD
# Status:     ad-hoc — <one-off | wip | migration | investigation>
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    <PR #, incident, notes/ doc>
set -euo pipefail
```

### Naming

- Date-prefix optional but useful: `YYYY-MM-DD_<short-purpose>.{py,bash}`.
- Use kebab-case or snake_case consistently — match existing siblings.

---

## Lifecycle

| Stage                                 | Action                                                                                                            |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Created**                           | Place here. Include the header above; under the retention policy the `Retire when:` field reads `RETAINED`.       |
| **Used for its purpose**              | Commit any non-trivial output / log alongside the script (e.g., in `notes/`) so the artifact survives the script. |
| **Graduates to permanent utility**    | Move to `util/<name>` (drop `ad-hoc` from the header `Status:`). Update any docs that referenced the old path.    |
| **Retained (the default)**            | **Owner decision 2026-08-25: ad-hoc scripts carry no retirement deadline.** They are kept in place as the provenance of how evidence, migrations, and one-off analyses were produced, even after their purpose completes. Pre-policy `Retire when:` conditions were rewritten to `RETAINED (…) Previously: <condition>` so the historical trigger stays readable. |
| **Retired (exceptional, owner-directed only)** | Only on an explicit owner decision — never as routine cleanup. Move to `util/ad-hoc/retired/` with the retirement date in the filename; do not plain-delete. |

**Example (juniper-ml#928):** the seven `2026-07-28_flood_census_*` / `docs_census_*` / `fp_transition_c2` investigation scripts were moved to `util/ad-hoc/retired/` with a `_RETIRED-2026-08-05` suffix once the flood-remediation analysis landed and `util/sequence_safety/` + `util/fleet_triage/predict_merge.py` became the live screens. Keeping the retired files in-repo preserves notes/ appendix and provenance comments that still name the old paths.

---

## Snapshot sidecar chain (operational)

`2026-08-24_regenerate_sidecar_chain.bash` (lands with juniper-ml#1333) regenerates index → classify → attribute → backfill in order. It is ad-hoc until a supported `util/` entry point exists.

Do **not** export `JUNIPER_CASCOR_SNAPSHOTS_DIR` for this script. That variable is both cascor's snapshot write directory and `snapshot_index.default_root()`; redirecting it (as the probe scripts in this directory do, so they cannot grow the archive) would point every stage at the scratch dir. Pass `--root` instead. `--backup DIR` is required and must already hold all four `snapshots_*.jsonl` files.

Operator contract: [`docs/REFERENCE.md` § Snapshot Attribution Dataset Pin](../../docs/REFERENCE.md#snapshot-attribution-dataset-pin).

---

## Canopy E2E topology driver (operational)

`e2e_seg17_topology_driver.py` scores Topology-tab matrix rows against a live isolated canopy (`JUNIPER_E2E_CANOPY_URL`, default `:8051`). `--step` names must be in the `STEPS` dict (exit `2` otherwise). After [juniper-ml#1672](https://github.com/pcalnon/juniper-ml/pull/1672), M-TOPOLOGY-06 requires **both** the depth label and the hidden count, M-07 asserts the label `"all"`, and M-12 scores the Clear selection button (an empty-space click is recorded, not scored).

Do not treat the module docstring's "NOT IMPLEMENTED" list as the registry — `topostate` and `topoexport` exist. Do not invent clicks with `gd.emit`.

`2026-09-04_canopy_verify_instance.bash` brings up a second canopy from a worktree (default `:8052`) beside the shared isolated stack. It does not restart `:8051` and does not `POST /v1/network`. `down` kills by pid, never by port. Leave the pidfile under `CANOPY_VERIFY_RUN_DIR` in place so `reap_pytest_orphans.bash` will not treat the instance as an orphan.

Operator contract: [`docs/REFERENCE.md` § Canopy E2E Topology Driver](../../docs/REFERENCE.md#canopy-e2e-topology-driver).

---

## What does NOT belong here

- Scripts that are part of a documented build / test / release flow → `util/` proper or `scripts/`.
- Scripts called by CI workflows → `util/` proper (CI should never invoke `util/ad-hoc/`).
- Tests → `tests/`.
- Generated artifacts (lockfiles, dep docs, build output) → wherever the build tooling expects.
