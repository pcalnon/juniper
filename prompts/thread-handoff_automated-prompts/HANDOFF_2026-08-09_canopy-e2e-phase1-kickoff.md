# HANDOFF 2026-08-09 — Canopy E2E validation arc: Phase 1 kickoff

Continue the juniper-canopy E2E front-end validation arc (session "canopy functionality testing"). Phase 0 is COMPLETE; begin **Phase 1: live click-by-click browser validation**.

## Completed so far

- Plan of record MERGED + owner-approved: `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` (ml#1036; phases 0-4, traps T-1..T-22). Execution script: `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` (298 row-ID'd rows, workflows W1-W14). Both survived dual independent audits (890 claims re-probed).
- Phase 0 MERGED: ml#1037 (canopy leg nested `JUNIPER_CANOPY_SERVER__PORT`), ml#1042 (`--with-recurrence` leg on 8211 + conditional `PYTHON_GIL` probe + teardown glob `.h5`-only), cascor#501 (restored 5 snapshot modules Paul's `4081f5b` direct push over-deleted; cascor main was import-dead — healed, primary ff'd).
- Rehearsal PASSED: quad up (data 8101 / cascor 8202 / recurrence 8211 / canopy 8051), honest gate green, teardown clean.
- Owner authorizations in force: headless merges for all arc PRs; §4.5 recurrence-leg default ratified.

## Remaining work

1. **Phase 1** (task #6): bring the quad up, drive the FULL matrix — all 298 rows + W1-W14 — with the Playwright browser MCP; fill the matrix `status` column (PASS/FAIL/BLOCKED/N-A/DEAD-CONFIRMED); capture `<row-id>__<step>.png` screenshots; findings ledger F-CANOPY-NNN in the evidence doc. DEMO lane afterward for demo-only rows (T-11 surfaces).
2. Phase 2 (task #7): triage findings → canopy fix PRs each with a regression test; re-validate.
3. Phase 3 (task #8): `src/tests/ui_live/` suite per plan §8 (sibling dir + addopts `--ignore` + `make test-ui-live`; numeric params ONLY via `POST /api/set_params` — T-7 wall).
4. Phase 4 (task #9): finish evidence doc, docs truth-up PR batch, closeout.
5. Merge the in-flight experiment_stack GIL follow-up PR when green (delegated pre-handoff; check `gh pr list --author @me` on juniper-ml).

## Key context

- Bring-up: `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper util/isolated_stack.bash --up --with-recurrence` (override REQUIRED from a session worktree — T-1-adjacent path gotcha). Gate on `/v1/health` BODY: `demo_mode:false` AND `juniper_data_available:true` (T-2 silent demo fallback), never HTTP 200.
- Dash at `http://127.0.0.1:8051/dashboard/`; suppress welcome modal via `localStorage juniper_canopy_welcomed=1`; wait out the params-init race (matrix §0 preconditions).
- Training buttons are WS-primary (T-21): verify `/ws/control` frames, NOT `POST /api/train/*` (fires only as fallback). Reset→Start after COMPLETED (T-6). Sidebar sections hidden-not-unmounted → assert visibility (T-13). No hoverData on topology (Plotly-native only). Pre-registered defect candidates to confirm as findings: unregistered `GET /api/network/topology` (Network Editor 404, matrix D-0), recurrence silent no-op swap w/ Start enabled (T-16), stale `enable_ws_control_buttons` comment (T-21), plant_all probe-only port var (F-E2E-004).
- Evidence doc STARTED, UNCOMMITTED in worktree joyful-popping-castle: `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (Phase-0 section done) + this handoff file — commit both with Phase 1's first PR.
- Landing protocol on ml (main churns): arm `--auto`; if checks green but BLOCKED/BEHIND, `--admin` (per arc authorization). cascor: no auto-merge; `--admin` after green.
- Session task list carries the gated chain (tasks 6-9 pending). Arc memory: `project_canopy_e2e_validation_arc_2026-08-08.md` (updated through Phase 0).

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/joyful-popping-castle
git status --short   # expect: ?? notes/...EVIDENCE.md + ?? prompts/.../HANDOFF_2026-08-09_... only
git log --oneline -2 # expect #1042 then #1037 squashes at/near tip
grep -c 'SERVER__PORT' util/isolated_stack.bash   # expect >=2
ss -tlnH 'sport = :8051 or sport = :8101 or sport = :8202 or sport = :8211'   # expect empty
```

Git: branch `arc/canopy-e2e-phase1-staging` tracking origin/main, clean but for the two untracked notes/prompts files above. No stash use.
