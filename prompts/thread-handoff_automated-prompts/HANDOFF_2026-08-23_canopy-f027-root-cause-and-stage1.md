# HANDOFF 2026-08-23 — Canopy E2E Phase 2: F-CANOPY-027 root-caused and Stage 1+3 shipped

Continue the juniper-canopy E2E validation arc, **Phase 2** (plan §6.3). Successor to
[`HANDOFF_2026-08-23_canopy-e2e-phase2-defect-triage.md`](HANDOFF_2026-08-23_canopy-e2e-phase2-defect-triage.md).

**The headline: F-CANOPY-027 is root-caused and its symptom is fixed on all three panels.** It was never a
wiring defect — it was **callback starvation under dash-renderer's hard-coded 12-slot concurrency pool**.
Twenty mechanisms had been refuted across three prior sessions, all of them looking at wiring; all of the
wiring was correct.

**Read the prior handoff's *Traps* section — it is still fully valid and is not repeated here.**

## Documents

| what | path |
|---|---|
| matrix (the ledger) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| evidence note (findings ledger) | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` |
| plan (§6.3 Phase 2, merge policy `:689`) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` |
| **remediation design of record** | `notes/JUNIPER_2026-08-23_JUNIPER-CANOPY_CALLBACK-STARVATION-REMEDIATION-DESIGN.md` — **§12 is the current truth; §3/§6 are pre-implementation** |

## Verify your starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline -1 origin/main    # expect dd6721a or later
python3 util/ad-hoc/e2e_unfilled_rows.py                # expect 298 verdicted / 0 UNFILLED
python3 util/ad-hoc/e2e_finding_triage.py --open-only   # expect 38 findings / 9 fixed / 29 open
git -C ../juniper-canopy log --oneline -1               # expect 6ba0207 or later
```

Phase 2's gate is still **16 findings** (3 P0 · 3 P0/P1 · 10 P1). The 10 open P2s, 2 LEDGER entries and
1 untriaged (F-CANOPY-013 — still has no priority tag, still cheap) do **not** gate it.

## The root cause, in one paragraph

dash-renderer 4.2.0 promotes work out of `callbacks.prioritized` under a cap that is a literal in the
bundle (`dash_renderer.dev.js:2846`): `available = Math.max(0, 12 - executing.length - watched.length)`.
Separately `getReadyCallbacks` will not promote a callback while any Input of it is an output claimed by a
still-pending callback. Together: **a poller whose completion time exceeds its own trigger period is never
absent from the pending set, so every consumer of its output starves indefinitely.** Arbitration is a
deterministic base-36 priority string, so terminal render callbacks (every stat tile and figure) lose every
time — which is why it looked like broken wiring. Full derivation + clean-room reproduction with a control:
evidence note § F-CANOPY-027 → `ROOT CAUSE (2026-08-23)`.

## What shipped this session

| PR | what |
|---|---|
| juniper-ml#1286 | root-cause record + 5 forensic probes |
| juniper-ml#1289 | remediation design of record + AST poller census |
| juniper-canopy#507 | **Stage 1** — per-tab gated poll lanes, CAN-000 clamp and tab gate fused into one clientside writer, dead poller removed, redundant tab-bar rebuild suppressed |
| juniper-canopy#509 | **Stage 3** — 2 more pollers gated + the poller-budget guard *(check it merged; it was mid-CI at handoff)* |
| juniper-ml#1294 | outcome record + widened Stage 2 scope |

**Result — verified on all three panels** by A/B injection through each component's own `setProps` (the same
probe that measured **0** dispatches across 220 before):

| panel | consumer dispatches | DOM |
|---|---|---|
| Candidate Metrics | 0 → **2** each | `''` → `Inactive` / `No active candidate pool` |
| Dataset View | **3 / 3 / 4** | changed ✓ |
| Decision Boundary | **3 / 3** | `No network loaded` → `Displaying decision boundary` |

| pool metric | baseline | after #507 | after #509 | design §7.1 target |
|---|---|---|---|---|
| pool full (`available == 0`) | 83.6 % | 63.6 % | **61.4 %** | < 20 % — **NOT met** |
| `prioritized` backlog, max | 36 | 37 | **23** | < 12 — **NOT met** |
| completions / 60 s | 224 | 499 | 449 | > 500 — met at #507 |

## Remaining work, in priority order

1. **Re-drive and re-score the F-CANOPY-027 rows.** *Not done — needs a LIVE TRAINING RUN.* Mechanism-level
   verification is not a substitute, and the plan requires it. Rows: `M-CANDIDATES-07/-09/-10/-11`,
   `M-BOUNDARIES-01/-02/-03/-04`, `M-DATASET-13/-15/-16`, **plus** `M-CANDIDATES-01/-02/-03/-04/-06`, which
   still carry `PASS` recorded against the panel's *mount defaults* and are unproven. Use
   `util/ad-hoc/e2e_matrix_rescore.py` (never `e2e_matrix_fill.py --overwrite`).
2. **Stage 2** (design §12.2) — **its scope is wider than originally written.** Two levers:
   *(a)* consolidate the ~10 remaining global pollers; *(b)* **NEW — stop no-op store writes.** An unchanged
   write still fires every downstream consumer, so panel work chained off a global store re-runs on every
   tab regardless of interval gating: `update_snapshots_table` takes
   `Input("dataset-swap-events-store", "data")`, rewritten every 5 s by `poll_dataset_swap_events`; Network
   Editor and Replay share the shape. The fix pattern is already in-tree (`hydrate_model_class` returns
   `no_update` when unchanged). **Check each call site individually — in some designs a store write doubles
   as a heartbeat and a consumer keys off the write, not the value.**
3. The rest of the P1s: F-CANOPY-031 (snapshots panel never renders against the migrated corpus),
   -002/-006 (both already root-caused in the ledger), -025 (blocks W7 from the UI), then -003/-007/-009/
   -010/-011/-014, F-CASCOR-001, F-ML-001.
4. Triage **F-CANOPY-013** (no priority tag; cheap).

## Key context the next session needs

- **Use the BUILT-app census, not the AST one.** `canopy_poller_inventory.py` resolves 151 of the app's 182
  callbacks and *missed two real panel-scoped pollers* that #509 had to add. `canopy_poller_budget_probe.py`
  reads `app._callback_list` and is correct. The Stage 3 guard uses the built-app census for this reason.
- **`e2e_f027_slots.py` is the instrument for any load work** — subscribe-not-sample; reports `available`
  distribution, backlog, slot holders, and who is starving.
- **A server-side `dash.no_update` tab gate saves nothing.** The round-trip and the slot are already spent
  by the time the handler returns. Gate on the client (`dcc.Interval.disabled`).
- **Refuted, do not re-run** (beyond the prior handoff's eighteen): the consumers missing from the client's
  derived `graphs.inputMap` (they are present, and every output resolves in `paths`); and
  `visualization-tabs.active_tab`-as-an-`Input` poisoning the writer (moving it to `State` was implemented,
  verified applied in the served graph, and changed nothing — reverted).
- **`open_signed_pr.py`'s dup-guard fires BEFORE it commits**, so a correction to an open PR's branch needs
  a new branch and the old PR closed (this cost one cycle: canopy#508 → #509, a Black reformat).
- **Canopy's Black hook is line-length 512 and `files: ^src/`.** Local `black` lives at
  `/opt/miniforge3/bin/black`, not in the JuniperCanopy1 env. Run it before pushing canopy source.

## Git state at handoff

juniper-ml `origin/main` = **dd6721a**; worktree clean. juniper-canopy `origin/main` = **6ba0207** (plus
#509 if it merged). No open PRs of mine in either repo except canopy#509 if still in flight; canopy#505/#506
are dependabot. Isolated stack is **DOWN**, all isolated ports free. Matrix coverage unchanged at **298 of
298** verdicted (re-verified with `e2e_unfilled_rows.py`) — **no rows were re-scored this session**, so the
verdict distribution is exactly as the previous handoff left it. That distribution is deliberately not
restated here: a naive grep over the matrix does not reproduce it (PASS carries many rider variants such as
`PASS(post-run)` / `PASS(delayed)`), and this arc's handoffs have a history of inheriting numbers nobody
re-derived. Derive it from the matrix directly if you need it.

**`origin/main` moves several times a day — always branch from a freshly fetched `origin/main`, and
re-derive every line anchor in this document before relying on it.**
