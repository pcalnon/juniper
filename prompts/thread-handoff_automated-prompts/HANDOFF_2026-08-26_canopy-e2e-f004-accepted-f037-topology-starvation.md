# HANDOFF 2026-08-26 — Canopy E2E: F-CANOPY-004 ACCEPTED; F-CANOPY-037 is the new sole open P0/P1

Continue the juniper-canopy E2E validation arc. **Headline: the owner's four decisions were taken and
executed, F-CANOPY-004 is now ACCEPTED under a documented freshness contract, and a NEW P0/P1 —
F-CANOPY-037 — replaces it as the gate on the topology row block. Ledger: 41 findings / 25 fixed /
1 accepted / 15 open (1 P0/P1 · 2 P1 · 12 P2). Matrix 298/298, 0 unfilled.** Predecessor:
`HANDOFF_2026-08-26_canopy-e2e-phase2-p1-fix-wave.md`. This session's PR is **ml#1416, MERGED**
(`99fb1f9b`, all 7 files verified in the merge commit).

## Verify your starting state

```bash
cd <fresh worktree of juniper-ml main>        # fetch first; main moves several times an hour
python3 util/ad-hoc/e2e_finding_triage.py     # expect 41 / 25 fixed / 1 accepted / 15 open
python3 util/ad-hoc/e2e_unfilled_rows.py      # expect 298 verdicted / 0 UNFILLED
cat reports/e2e/CURRENT_RUN_ID                # 20260826T215010Z
```

Stack is **DOWN**, E2E ports 8101/8202/8051 free, deploy containers on 8050/8201/8211 untouched and
healthy (**never touch them**). cascor primary is now **`c6cd2f0`**, not the old `67d7ea3` pin — a peer
advanced it; the delta is only the forkserver preload (cascor#592) + a CI gate.

## Owner decisions taken (all four, this session)

1. **F-CANOPY-004 → ACCEPTED**, contract now **and** migration scheduled. Contract: clientside immediate ·
   interaction render **≤16 s** · fresh-session population **≤40 s** · during-run steady-state best-effort.
   **JR-CAN-PERF-004** (WS migration) is the scheduled workstream. F-004 no longer gates Phase 3.
2. Run the **full** §6.3 re-drive block live — done, and it surfaced F-037.
3. **Fix all 11 canopy P2s** (F-CASCOR-002 upstream) — **NOT STARTED**.
4. **Enable a live 3-D posture** for M-DATASET-17..26 — **NOT STARTED**.

## F-CANOPY-037 (new, P0/P1, OPEN) — read before touching the topology rows

The rebuild is chained off `metrics-panel-metrics-store`, which rewrites **141,460 B of byte-identical
data 0.57/s even on a COMPLETED run** (34 writes/60 s, **33 identical**, 0 `no_update`), so
`update_network_graph`'s Input is re-claimed faster than its own 1.5–5 s server time. **Rendered in only
2 of 11 live sessions.** When it does render it is correct and fast (39,319 B, 206 traces, stats bar
`2/10/2/89`). **Not F-006** (fixed — the DOM applies the render when it runs) and **not F-004** (does not
resolve at any budget). Ruled out by measurement: tab inactive, server wrong, empty store, callback error,
polling interference, fresh canopy leg, run-vs-idle, the depth filter, and driving the callback's own
Inputs. **Fix candidates:** suppress no-op writes on that feeder (the Stage 2 lever, never applied to this
producer), or drop the store from the rebuild's Input list (smaller diff, removes the coupling).

## Remaining work, in priority order

1. **Fix F-CANOPY-037** — it blocks M-TOPOLOGY-01..18, W4-01..17, W1-12..14 and is the only P0/P1.
2. **The all-11 P2 fix wave** (decision 3): -001, -012, -013, -015, -018, -026, -028, -032, -033, -034,
   -036; F-CASCOR-002 filed upstream.
3. **The JR-CAN-PERF-004 plan document** (decision 1's scheduled half — not yet written).
4. **The live 3-D posture** (decision 4): `POST /api/dataset/generate` is demo-gated 400 and both
   `equities` / `equities_seq` report `available:false` in the live lane.
5. **W5-21 / W5-23** on a **V2 snapshot with a non-empty history** — they are blocked by an empty V1
   replay (`epoch 0/0`, `range [0,0]` ⇒ `min==max==0`), **not** by a drag idiom. W5-22 now drives.
6. **C2.10-03, M-SNAPSHOTS-20/-21** — still owed; never reached this session.

## Key context / traps added this session

- **Dash 3.x, not Dash 2.** Sliders are **Radix** (`[role=slider]` + `input[type=number]`) — **there is no
  `.rc-slider-handle` in the tree**, so a Dash-2 selector returns `False` *without erroring* and reads as
  "the control is broken". This is why the previous handoff's "W5-21..23 need the rc-slider drag idiom" was
  wrong. `dcc.Dropdown` is a native `<button class="dash-dropdown">`. See memory `reference_dash3_widget_idioms`.
- **A probe that reports zero is not evidence until a second instrument agrees.** My first rebuild probe read
  `resp.request.post_data` inside the response handler, silently got nothing, and reported "the callback never
  fires" while a wire census counted 12/60 s. Stash the POST body on the **request** event and join on the response.
- **`f031` now exists as a script step** and also cleared F-031's flagged second defect —
  `data-snapshot-row`/`data-snapshot-id` are on **200/200** rows (the finding recorded ZERO).
- **New driver:** `util/ad-hoc/e2e_seg17_topology_driver.py` — `probe` (pins real widget markup before any row
  is scored), `topodiag`, `rebuildprobe`, `wirecensus`, `quietread`, `storestorm`, `topo`, `f031`, `theme`.
- `e2e_finding_triage.py` now has a third disposition, **ACCEPTED** (token in the header's last 170 chars,
  same convention as FIXED).

## Git state at handoff

juniper-ml: **ml#1416 MERGED** (`99fb1f9b`); branch `docs/canopy-e2e-f037-topology-starvation` can be deleted.
juniper-canopy: untouched this session (main `9f6fac9`). cascor: untouched, now `c6cd2f0`.
`origin/main` moves several times an hour — branch from a fresh fetch and re-derive every line anchor.
