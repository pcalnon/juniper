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

## Resident-hazard gap triage (operational)

Three complementary scanners — keep all three; the first alone cannot find a directive that was never in `AGENTS.md`:

| Script | Question |
|--------|----------|
| `2026-08-28_hazard_triage.py` | Which *already-resident* `AGENTS.md` blocks look like hazards? (`gh api` on GitHub `main`; default `--min-score 2`) |
| `2026-08-28_resident_gap_scan.py` | Which source comments are hazard-shaped and resident nowhere? (local, read-only; ranks by identifier count) |
| `2026-08-31_resident_gap_triage.py` | Gap finding scored with four severity signals on the **block** (default `--min-score 3`; `--json` writes every scored row; `--self-check` pins cascor `cascade_correlation.py:1927`) |

The scored **total is not a health metric**. Relocation removes resident identifiers, so the gap predicate starts matching them — cutting widens the gap by construction. Read the score ≥ 3 count (and whether anything *new* appears there). `SKIP_DIRS` excludes in-repo worktrees (#1519).

Operator contract: [`docs/REFERENCE.md` § Resident-Hazard Gap Triage](../../docs/REFERENCE.md#resident-hazard-gap-triage). Fleet record: [`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md`](../../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md).

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

## Topology step order and blast-radius IDs (operational)

`e2e_seg17_topology_driver.py` `--step` is order-preserving on one page. `topo` fills the raw-topology store (M-03 Weight Matrix); a later `topostate` then scores M-18 `INDETERMINATE`. Re-drive `--step topostate` **alone**. Scorer predicates stay with in-flight docs #1675.

The copied blast-radius sentence *W4-01..17 and W1-12..14 stay BLOCKED* names 20 IDs that **are all defined** — matrix §4's `### W4` is 17 numbered steps and `### W1` is 19. They are written as ordinals under a heading, so a grep for `W4-09` finds nothing; that is a fact about the spelling, not the definition. The plan's zero matches are by design (it delegates workflow ids to the matrix).
**The module docstring is correct — leave it.** What is thin is coverage: only `W4-02` was ever driven. juniper-ml#1695 filed this as F-E2E-007 and **withdrew it the same day**.

`e2e_finding_triage.py` `pri_of` takes the **first** severity token anywhere in the bolded header body. Do not name another severity in header prose. Dispositions stay with in-flight docs #1646.

Operator contract: [`docs/REFERENCE.md` § Canopy E2E Topology Step Order and Blast-Radius IDs](../../docs/REFERENCE.md#canopy-e2e-topology-step-order-and-blast-radius-ids).

---

## Memory-budget slack (operational)

`2026-08-25_p5_port_memory_budget.py measure-growth`, `2026-08-26_p5_fleet_state.py`,
`2026-08-26_p5_promote_ready.py`, and `2026-08-28_p5_cut.py` size a ceiling's working room.
They are **not** the `Memory Budget` CI gate (`util/memory_budget_check.py`).

- **Headroom is not slack.** The checker prints `headroom = ceiling_chars - chars` and fails only
  on over-ceiling growth or an undeclared ceiling raise. It never reads `measure-growth`.
- **`measure-growth` prints `median` / nearest-rank `p90` / `max`.** There is no required-slack
  field and no exclusion flag. Planning slack is `max(max, 2000)` in the cut / promote helpers.
  Size from `max`, never from p90. Default `--ref` is `HEAD` — pass `origin/main` after a fetch.
- **`--ratchet` seeds, it does not leave working room.** After a cut, hand-edit slack.
- **`p5_fleet_state.py` counts chars** (`len()` of UTF-8 text from the GitHub API). The API
  `size` field is bytes.

Operator contract: [`docs/REFERENCE.md` § Memory-Budget Slack (Planning)](../../docs/REFERENCE.md#memory-budget-slack-planning).

## F-039 store probe (operational)

`e2e_f039_topoprobe_instrument.py` (`apply` / `report` / `revert`), `e2e_f039_metrics_store_soak.py`, and `e2e_f039_duplicate_store_probe.py` are the revertible server-side instrument that root-caused F-CANOPY-039 (FIXED in juniper-canopy#549). They are **not CI**.

- **Read the whole `report` series**, not its head. Topology's measured healthy shape is `eq=False` ×4 then `eq=True` ×11. A head-only reading of that same log produced the retracted "permanently empty" claim.
- **`--target topology` refuses** on current canopy: `_update_topology_store_handler` no longer receives the client's store copy. Use `--target metrics`, or add the `State` first.
- **Backup lives in the git dir** (`f039-topoprobe.f039bak`), never beside `dashboard_manager.py`. A work-tree bak is swept by `git add -A`.
- **`curl` cannot tick a Dash interval.** Hold a live browser session with the soak script.
- **`e2e_f039_duplicate_store_probe.py` exit 1 is not a verdict** — the probe could not run. `dcc.Store` has no DOM; `paths.strs` hides duplicates.
- **That `paths.strs` blindness now has a lift: `2026-09-05_dash_layout_id_census.py`.** Dash serves the layout tree as JSON from the *server* at `/<prefix>_dash-layout`, before dash-renderer indexes
  anything, so a duplicate id appears there as two nodes carrying one id — which `paths.strs`, a one-id-to-one-path map, cannot represent at all. Use it before reaching for the duplicate probe. It
  settled the question for `metrics-panel-metrics-store` on 2026-09-05 (465 id-bearing nodes, 465 distinct, zero duplicates anywhere) and a clean census is a **refutation**, not an absence of evidence.
  It reads the layout **as served**, so a component a callback adds later would not appear; every canopy panel declares its stores statically, but that bound is real.
- **A response census must detach its listener.** `2026-09-04_f035_candidate_loss_redrive.py` attached `page.on("response", …)`, never removed it, and returned the dict the handler keeps mutating —
  so its log printed an honest 30 s window while the JSON, dumped 48 s later at end of run, reported the whole listening lifetime. One run, two archived artifacts, 17 writes vs 46. Both censuses now
  `remove_listener`, return a copy, and record `window_s` in the artifact. If a census does not stop counting when its window closes, it is not a census — and the two artifacts will disagree silently.
- **`2026-09-05_f035_store_write_latency_probe.py`** times each store-writing round trip against the interval that re-requests it, because dash-renderer retires an in-flight call on re-request. Read its
  `overlap_fraction` as the retirement **precondition**, never as retirement: on 2026-09-05 it read 0.69 while the store was constant-empty across 130 server-side comparisons, so nine unopposed
  responses also failed to land. A number that explains most of a result is not the cause of it.

Always `revert` before committing anything from the instrumented checkout.

Operator contract: [`docs/REFERENCE.md` § F-039 Store Probe](../../docs/REFERENCE.md#f-039-store-probe).

## Ruleset context audit (operational)

`2026-08-10_ruleset_context_audit.py` classifies each publishing repo's `required_status_checks` as BLOCKING / MATCHED / Tier 1 / path-gated / advisory. Read-only (`gh api` + `gh pr list`). It does **not** add or remove contexts — that is `2026-08-20_require_context_safely.py`.

A required name that never reports leaves `main` unmergeable with every visible check green (the 2026-08-10 fleet-union class). Re-run the auditor; do not quote the incident note's §1 counts. Human-mode exit 0 can still print `ERROR:` rows; `--json` fails closed on probe errors.

Operator contract: [`docs/REFERENCE.md` § Ruleset Context Audit](../../docs/REFERENCE.md#ruleset-context-audit).

## Worktree in-use probe (operational)

`2026-09-02_worktree_inuse_probe.py` is an independent second opinion for a worktree sweep. The cwd-only liveness probe (`2026-08-20_worktree_liveness_probe.py`) and the P5 cleaner's `occupied()` gate miss an editor or a long `pytest` whose cwd is elsewhere while a file inside the tree is still open.

- STRONG (cwd or an open fd inside the tree) → `IN USE`, exit 1 `REFUSE`.
- WEAK (cmdline substring) → `review` / `CAUTION`, exit stays 0. The first run reported every tree in use because the probe named the paths as arguments; self and parent pids are excluded from WEAK by pid.
- Empty argv exits 2 (the cwd-only probe exits 0 on that misuse).
- Read-only. Sibling `foo-extra` is not inside `foo`. Unreadable `/proc` (other users) is counted, not treated as in-use.

```bash
python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py <worktree-dir> [<worktree-dir> ...]
```

Operator contract: [`docs/REFERENCE.md` § Worktree Divergence](../../docs/REFERENCE.md#worktree-divergence-is-a-memory-cost).

## Canopy E2E finding triage (operational)

`e2e_finding_triage.py` is the mechanical P0/P1 open-count for Phase 2's exit criterion. It reads only line-starting `**F-<AREA>-<NNN> — …**` headers in the evidence ledger.

- `FIXED` / `HEALED` in the last 170 characters of the header → closed.
- `ACCEPTED` in that same tail, and not also FIXED → owner-deferred. Third disposition: not FIXED, not OPEN.
- `--open-only` hides closed rows; the totals block still counts every finding.
- Always exits 0. A green shell is not "no open P0/P1".

```bash
python3 util/ad-hoc/e2e_finding_triage.py
python3 util/ad-hoc/e2e_finding_triage.py --open-only
```

Operator contract: [`docs/REFERENCE.md` § Canopy E2E Finding Triage](../../docs/REFERENCE.md#canopy-e2e-finding-triage).

## F-CANOPY-037 render census (operational)

`e2e_f037_render_census.py` re-drives the topology-graph paint that F-CANOPY-037 measured in 2 of 11 sessions. Default `--sessions` is 11; a single session is not a comparable claim. Exit 0 means every session produced PASS or FAIL (even if painted==0); exit 2 means the census failed to measure. All-zero `hidden_units` is INVALID (nothing to draw), not a render FAIL. Idle populated is VALID.

The census does **not** start canopy. Bring up the isolated trio first (`util/isolated_stack.bash --up`), train a network, then:

```bash
python3 util/ad-hoc/e2e_f037_render_census.py
```

No `--base-url`; inherit `JUNIPER_E2E_CANOPY_URL` (default `http://127.0.0.1:8051`). A/B a pre-merge checkout on `:8052` with `e2e_f037_ab_premerge_leg.bash`. `_find_juniper_root` must see **both** `juniper-canopy` and `juniper-cascor`; three hops from a nested worktree recorded `sha=None`.

Operator contract: [`docs/REFERENCE.md` § F-CANOPY-037 Render Census](../../docs/REFERENCE.md#f-canopy-037-render-census).

---

## What does NOT belong here

- Scripts that are part of a documented build / test / release flow → `util/` proper or `scripts/`.
- Scripts called by CI workflows → `util/` proper (CI should never invoke `util/ad-hoc/`).
- Tests → `tests/`.
- Generated artifacts (lockfiles, dep docs, build output) → wherever the build tooling expects.
