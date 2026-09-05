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

## X7 off-loop census (operational)

`2026-09-04_x7_offload_census.py` (v1) and `2026-09-04_x7_offload_census_v2.py` (v2, v0.3.0) land with juniper-ml#1631. They are **not** CI and **not** the slice-1a authority — that is `juniper-canopy/src/tests/regression/test_x7_off_loop_discipline.py`.

- **v1 is retained unfixed as the negative example.** It matches receiver *names*. The bare name `client` is bound in canopy `main.py` to cascor, redis, cassandra, **and** an `httpx.AsyncClient`, so it reports an awaited async call as blocking. That is the same flaw that makes `ruff --select ASYNC` report "All checks passed!" against these sites.
- **v2 resolves assignment provenance** and reports an `UNRESOLVED` bucket rather than guessing. Use it to explore; use the canopy gate to decide when slice 1a is done.
- **Exemption must be site-local.** A module-global expression match ("this call text was handed to `to_thread` somewhere in the file") hides every twin of an offloaded call — including the three health endpoints X7 is defined by — and the miss grows as work proceeds. v2 v0.3.0 and the canopy gate at `d33ab0a` are site-local only. Do not reintroduce cross-site matching.
- Both read `main.py` only. Design §5.2 also puts the metrics relay's `extract_network_topology()` in slice 1a; a receiver-based scan cannot see a `self`-method with internal I/O.
- Both hardcode `CANOPY_MAIN` to `/home/pcalnon/Development/python/Juniper/juniper-canopy/src/main.py`. Retarget before running on any other host.

Operator contract: [`docs/REFERENCE.md` § X7 Off-Loop Census](../../docs/REFERENCE.md#x7-off-loop-census).

---

## Canopy E2E unfilled-rows ledger (operational)

`e2e_unfilled_rows.py` is the **ledger** reader for the click-by-click matrix. It lists `C2.` / `M-` rows whose `status` cell is still a placeholder (`""`, `—`, `-`, `--`, `TBD`, `n/a`), grouped by `###` section. It reuses `e2e_matrix_fill.py`'s escaped-pipe split and placeholder set so the answer cannot drift from what the filler will write. Exit 0 always.

`e2e_row_coverage.py` is an **estimator**: it diffs matrix row ids against `reports/e2e/*/statuses.tsv` and `rowlog.md`. It can list already-`PASS` rows as remaining (observed on `origin/main` `8da1f87e`: ledger `UNFILLED: 0`, estimator still names `M-PARAMETERS-02` / `03`) and can over-credit a compressed range or a `pending …` record. Plan re-drives from the ledger.

W-series tokens in verdict files are not ledger rows. `--repo-root` / `--matrix` override the default path.

Operator contract: [`docs/REFERENCE.md` § Canopy E2E Unfilled-Rows Ledger](../../docs/REFERENCE.md#canopy-e2e-unfilled-rows-ledger).

---

## What does NOT belong here

- Scripts that are part of a documented build / test / release flow → `util/` proper or `scripts/`.
- Scripts called by CI workflows → `util/` proper (CI should never invoke `util/ad-hoc/`).
- Tests → `tests/`.
- Generated artifacts (lockfiles, dep docs, build output) → wherever the build tooling expects.
