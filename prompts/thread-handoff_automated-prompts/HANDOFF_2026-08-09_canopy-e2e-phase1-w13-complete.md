# HANDOFF 2026-08-09 — Canopy E2E Phase 1: W13 complete, continue at W1

Continue **Phase 1** of the juniper-canopy E2E validation arc (plan `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`, matrix `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`). LIVE-lane run `20260809T223851Z` is in flight; W13 (chrome + ancillary smoke) is COMPLETE. Next: **W1 → W2 → … → W12 → W14-last**, then DEMO lane, then matrix `status`-column consolidation.

## Completed this session

- **F-E2E-006 found + FIXED + MERGED (ml#1049)**: canopy's browser-WS allowlist defaults admit only port-8050 origins → isolated canopy 403-looped its own `/ws/training`+`/ws/control`. `canopy_up` now exports `JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS` from the real port (5 test pins, checklist §3.3 updated; 66/66 tests). Verified live post-bounce: both sockets open, console clean.
- **W13 steps 1–16 all recorded** (rowlog): workers/redis/cassandra/tutorial/about panels, welcome-modal lifecycle, dark-mode + persistence, tab restore, 15-tab console walk (0 errors), tooltips ×2, sidebar visibility+width sweep (3/9⇄2/10), badge states 0/2/5 + recovery (state 6 = N-A by GAP-WS-31 retry-forever design; states 3/4 → W14; state 1 → demo lane).
- **D-0 confirmed live** (Network Editor "No topology loaded.", server-side 404). OBS-1 version divergence (About 2.2.0 vs health 0.4.0); OBS-2 dark-mode flattens button semantics (all blue).
- Running record: `reports/e2e/20260809T223851Z/rowlog.md` (+ screenshots same dir). Evidence doc has Phase-1 env header + F-E2E-006 + PR ledger.

## Remaining work

1. **W1 cold-start training e2e** — FIRST read matrix lines 704–767 (W1+W2 scripts), 231–341 (§2.5–2.10 sidebar/controls rows), 383–551 (§3.1–3.6 tab rows). Traps: Reset→Start precondition (T-6), WS-primary verify `{command, command_id}` frame + ack on `/ws/control` (T-21 — NET-only assertion FAILs a working app), FSM badge recheck (was "FSM: Unknown" cold).
2. W2–W12 per matrix order, W14 LAST (stop/restart cascor; never restart canopy — T-2). Then DEMO lane (task #2), then consolidate matrix statuses + close task #1.
3. Retest disabled-Apply tooltip once enabled (W3); M-TUTORIAL-04 context menu; C2.2-03 third writer (W5).

## Key context / gotchas (cost real time)

- **Stack is UP** (leave it): data 8101 / cascor 8202 / recurrence **8212** / canopy 8051, pids in `/tmp/juniper-e2e/*.pid`, logs same dir. **Every** `isolated_stack.bash` call (incl. `--down`) needs `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper JUNIPER_E2E_RECURRENCE_PORT=8212` — deploy stack legitimately holds 8211 (do NOT touch docker).
- Honest gate: `curl -s http://127.0.0.1:8051/v1/health` body `demo_mode:false` + `juniper_data_available:true`.
- Worktree: `generic-wishing-sunset`, branch `arc/canopy-e2e-phase1-results` (pushed). The harness BLOCKS bash with `cd <elsewhere>`/`source`/loops — use absolute paths, direct env-bin invocations, `git -C` never needed (work in-worktree).
- Playwright MCP: post-action snapshot can exceed the 5s tool timeout on this DOM — **a timed-out click may have landed; verify state, never blind-retry toggles**. `setOffline` does NOT kill established WebSockets (close `window.cascorWS.ws` directly). Disabled bootstrap buttons are pointer-transparent (tooltip hover can't fire). Batch sweeps via `browser_run_code_unsafe` chunks (~4s each). Tabs: `page.getByRole('tab', {name: ...})`. localStorage persists in the MCP profile (`juniper_canopy_welcomed=1` is set).
- Landing protocol: arm `--auto`; green-but-BLOCKED/BEHIND → `--admin` (used for #1049). No Allow-* trailers were needed. Phase-1 itself is PR-count-0: results land at Phase 4; commit rowlog/evidence to the results branch as you go.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/generic-wishing-sunset
git status --short && git log --oneline -4   # expect handoff+W13+opening commits atop c9bd54e on arc/canopy-e2e-phase1-results
curl -s http://127.0.0.1:8051/v1/health | python3 -m json.tool | grep -E 'demo_mode|juniper_data'
ss -tlnH 'sport = :8051 or sport = :8101 or sport = :8202 or sport = :8212' | wc -l   # expect 4
```

Session tasks #1–#5 carry the phase chain (#1 in_progress). Arc memory: `project_canopy_e2e_validation_arc_2026-08-08.md`.
