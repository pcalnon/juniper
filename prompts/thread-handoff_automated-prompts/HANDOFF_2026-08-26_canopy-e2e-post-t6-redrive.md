# HANDOFF 2026-08-26 — Canopy E2E: the post-T6 live re-drive is DONE; 8 P0/P1 verified, F-004 is the last gate

Continue the juniper-canopy E2E validation arc. **The headline: the post-T6 live re-drive (run
`20260826T174225Z`) verified all eight merged P0/P1 fixes live and flipped them to FIXED — the ledger is
now 40 / 25 fixed / 15 open (0 P0 · 1 P0/P1 · 2 P1 · 12 P2). F-CANOPY-004 is the SOLE open P0/P1 and it
GATES every remaining live render.** Predecessor: `HANDOFF_2026-08-26_canopy-e2e-phase2-p1-fix-wave.md`;
its Traps / Landing / Tooling sections remain valid. This session's records PR is **ml#1399** (open at
handoff), and the Phase-4 truth-up is **canopy#528 (docs)** + **canopy#530 (code)**, both MERGED.

## Documents

The usual four (matrix, evidence note, plan, callback-starvation design). The evidence note's last section
is *"Phase 2 — the post-T6 live re-drive (2026-08-26)"* and carries every verdict, mechanism and screenshot
name. The 8 verified findings' headers now read FIXED with live-verification riders; F-035 carries a
LIVE-INCONCLUSIVE note.

## Verify your starting state

```bash
cd <fresh worktree of juniper-ml main>        # fetch first; main moves several times an hour
python3 util/ad-hoc/e2e_finding_triage.py --open-only   # expect 40 / 25 fixed / 15 open (0 P0 · 1 P0/P1 · 2 P1 · 12 P2)
python3 util/ad-hoc/e2e_unfilled_rows.py               # expect 298 verdicted / 0 UNFILLED
cat reports/e2e/CURRENT_RUN_ID                        # 20260826T174225Z
gh pr view 1399 -R pcalnon/juniper-ml --json state    # merge if green (arc approval standing); REST squash
```

The isolated stack is **DOWN**, all E2E ports free, 8211 = the live deploy container (never touch), cascor
primary pinned `67d7ea3` (T6 freeze lifted, but nobody advanced it — keep it). No arc worktrees linger (the
docs + code canopy worktrees were removed this session).

## What is DONE (do not redo)

- **Verified live → FIXED:** F-CANOPY-003 (button re-enable 0.82–3.59 s), -005 (0 browser train POSTs / 0
  409s / business-rejection alert), -007 (empty local dir → cascor list 28029), -008 (5 CSRF rejects, 0
  per-IP lock, plane recovered), -009 (detail held), -010 (modal survived 65.8 s), -011+D-0 (active
  surface, FSM Investigating, topology 2/9/2, populated remove dropdown; restore+remove live 10→9), -014
  buttons (play/pause/stop POST absolute URLs, no scheme errors). OBS-1 + depth-label PASS.
- **F-CANOPY-035 → INCONCLUSIVE (stays OPEN, NOT a regression).** Its adapter is provably correct
  (`/api/metrics/history` had 3216 candidate entries; a sim of `_candidate_series_from_history` kept
  99/99), but the shared `metrics-panel-metrics-store` was **empty on both tabs** post-run (both loss
  plots blank) — the F-CANOPY-004 store-population/staleness condition, not F-035. **Do not file "F-035
  broken."** Re-drive it only after F-004 has an answer.
- Matrix rescored (C2.5-09, M-NETWORK-EDITOR-03/-04 → PASS); TSV + CURRENT_RUN_ID recorded; arc memory +
  MEMORY.md updated; canopy#528/#530 merged.

## Remaining work, in priority order

1. **F-CANOPY-004 is the whole game now.** It is the sole open P0/P1 and it gated the live render of F-035
   (empty store) and F-011 (~65 s editor lag) this session. The **owner decision** is drafted in the
   evidence note: accept-and-document a freshness contract (post-Stage-2: 3–16 s interaction renders,
   20–40 s fresh-session population) **versus** open the JR-CAN-PERF-004 WS-migration workstream. Put it to
   Paul; recommendation is the contract now + migration as a planned workstream. Until F-004 is decided,
   the remaining live renders cannot be shown snappy.
2. **The fix-independent §6.3 re-drives** (runnable on a fresh bring-up, no fix needed): M-TOPOLOGY-01..18
   + W4 + W1-12..14 (F-006's blocker gone), C2.10-03, M-SNAPSHOTS-20/-21 via a real dataset swap through
   the restored Live Switch, M-DATASET-14 (theme flip), the F-CANOPY-004 latency-class rows. **M-DATASET-17..26
   still await the owner's DEMO-lane / 3-D-posture scoping decision** — surface it, do not drive around it.
3. **F-CANOPY-014's three slider rows (W5-21..23)** — the driver's rc-slider handle drag did not land
   (`driven=False`, not errored); the fix is verified via the three button controls (same URL path). Needs
   the native rc-slider drag idiom (mouse down on `.rc-slider-handle`, move, up — my `drag_handle` in
   `e2e_p1wave_redrive.py` found the handle box but the value did not commit).
4. **The `f031` driver step** is still owed at a stack window (its probes were lost to `/tmp`).
5. **Matrix EXPECTED-text truth-up for M-NETWORK-EDITOR-05 / -10** — D-0 is fixed, so their "Currently
   always 'No topology loaded.'" / "empty dropdown today" expected-result text is now stale; the rows read
   PASS but the *content* needs updating to the real topology/populated-dropdown behaviour. (A matrix
   content edit, not a rescore.)
6. **The open-P2 owner decision** (fixed-vs-deferred): -001, -012, -013, -015, -018, -026, -028, -032,
   -033, -034, -036, F-CASCOR-002. Suggested fix-now: -013/-015/-018/-026/-028/-032/-034/-036; defer
   -001/-033; -012 rides an editor follow-up; F-CASCOR-002 → file upstream.
7. **Phase 3** (plan §6.4, the `ui_live` suite) — entry condition is reachable once F-004's disposition
   lands (it is the only P0/P1 gate now).

## Key context (this session's additions to the standing traps)

- **F-CANOPY-004 masquerades as a per-fix regression.** A fix's live render lagging or blanking during a
  congested run is F-004, not the fix — verify the MECHANISM (API/state correct, adapter simulation, the
  quiescent re-read) before writing "broken". This session nearly mis-filed F-035 and F-011 that way; the
  `f011check` / `f035probe` / `storeprobe` steps in `e2e_p1wave_redrive.py` are the disambiguators.
- **The metrics store is empty post-run under congestion** (both loss plots blank) even though
  `/api/metrics/history` has the data — the liveness-gated fast-interval poll demotes to `no_update` when
  the WS-liveness flag is stuck live, and the WS append path does not fire post-run. This is the F-035
  blocker and a general F-004 manifestation; a fresh, lighter-load run may populate it.
- **The finding-triage parser reads only the HEADER's bold text** (`**F-… — …**`, non-greedy to the first
  `**`), so to flip a finding's count you edit the HEADER status token (put FIXED in its last 170 chars),
  not a trailer in the block body. (Cost me a wasted pass this session.)
- **`e2e_p1wave_redrive.py`** carries every step: obs1, depth, start, f035(+f035probe,storeprobe), f005,
  f008, f007, f009, f010, f014, f011(+f011check). Run under `LD_LIBRARY_PATH= /opt/miniforge3/envs/
  JuniperCanopy1/bin/python`. f008 restarts the canopy leg onto an EMPTY snapshot dir (the F-007 posture)
  via `e2e_canopy_leg_restart.bash`.
- **`e2e_fcandidate_model_select_probe.py`** reproduces D-8 unit-level (no stack): `POST /api/model/select
  {"nn_model":"recurrence"}` → 200, backend unchanged, with no recurrence URL.

## Git state at handoff

juniper-canopy: #528 (`9b88ba10`) + #530 (`3ce7bbcf`) merged, both branches deleted, main-verify green.
juniper-ml: **ml#1399 open** (`docs/canopy-e2e-post-t6-redrive`, records) — merge when green. This handoff
rides a separate docs PR that archives it. cascor: untouched, pinned `67d7ea3`. Stack DOWN, all ports free.
**`origin/main` moves several times an hour in every repo — branch from a fresh fetch and re-derive every
line anchor.**
