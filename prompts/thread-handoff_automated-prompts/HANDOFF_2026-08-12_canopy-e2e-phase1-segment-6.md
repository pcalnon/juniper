# HANDOFF 2026-08-12 — Canopy E2E Phase 1: segment 6 (W5 continuation)

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. Segment 5 is COMMITTED
and PUSHED on branch `arc/canopy-e2e-phase1-seg5` (worktree `warm-scribbling-island`; commits `9b96873`
+ `b62c48b`). Run-id `20260811T010700Z`.

**Start here: the browser MCP must be reconnected.** Segment 5 ended when the Playwright MCP server
disconnected. Every remaining W5 row needs it. Verify `mcp__playwright__*` tools are available before
planning any UI work.

## Completed in segment 5

- **Recovered the stack twice.** cascor 8202 was down ~7.6 h on entry and died twice more mid-session.
- **W5 steps 4-7 driven.** W5-04 FAIL · W5-05 PASS · W5-06 PASS · W5-07 INCONCLUSIVE (re-run needed).
- **Two findings opened, both root-caused to file:line** (full write-ups in the evidence doc):
  - **F-CANOPY-009 (P1)** — the snapshot detail panel fills correctly, then is **wiped ~7 s later** by the
    panel's own 10 s refresh rebuild. `View Details` is built without `n_clicks=0` (unlike its 4 op-btn
    siblings at `hdf5_snapshots_panel.py:936-954`), so the rebuild re-fires `select_snapshot` with a falsy
    `n_clicks` and the `:997-998` guard returns `None` instead of `dash.no_update`, clearing the store.
    The author's own fallback at `:1022-1030` is dead code behind that guard.
  - **F-CANOPY-010 (P1)** — the snapshot-operation **confirmation modal closes itself ~3.6 s** after
    opening. Same class, worse consequence: every early-out in `open_snapshot_op_modal` returns
    `(False, "", None)`, slamming the dialog shut and discarding the pending operation id. This is the
    confirmation gate for restore / replay / resume / retrain.
- **F-ML-001 upgraded** from hazard to arc-blocker and then **remedied**. Three kills of the cascor leg in
  ~1 h, each within ~2 s of a concurrent experiment-campaign run dir being created. Selectivity pinned:
  only the leg whose conda env name appears in its cmdline (`JuniperCascor1`) matches the reaper's
  candidate gate; data escapes via its venv path, canopy escapes because its argv is a bare
  `python main.py`.
- **Remedy shipped** (owner-selected): `util/ad-hoc/e2e_cascor_leg_supervise.bash` runs cascor as a direct
  child of a resident supervisor. Launch recipe is byte-identical to `cascor_up`; only the parent changes.
  **Verified with the reaper itself** — `reap_pytest_orphans.bash --dry-run` now reports
  `KEEP pid=… (live parent)` for the leg while still flagging the stale campaign orphans.

## Remaining work (priority order)

1. **RE-RUN W5-07** (task #11). The leg is supervised, healthy, and has an **empty** network; the snapshot
   is intact on disk — so this is a clean restore-into-empty. Drive the op menu → Restore → Confirm and
   assert the ✅ path plus `GET :8202/v1/network` showing the 10-unit network restored.
2. W5 steps 8-10 (FSM Investigating, D-0 readout), 11-15 (patch/append/remove; **I=2, H=10 → append
   vector is 12 floats**, sourced from `/api/topology` since the topology DOM is dead per F-CANOPY-006),
   16-29 (replay lifecycle, resume/retrain, history, DEAD-EXPECTED probes).
3. Tasks #6-#10: Network Editor + Replay + W11 → W3 params → W6 → W7/W8 (still needs the isolated
   recurrence leg) → remaining chrome → DEMO lane → Phase-1 close.
4. Phase 1 lands as **ONE evidence PR** (plan §6.2); the wip commits are crash-safety only.

## Key context / gotchas

- **Stack is UP and supervised**: data 8101 / cascor 8202 (supervised child) / canopy 8051
  (`demo_mode:false`). Recurrence leg still DOWN — host 8211 is the juniper-deploy container, so W7/W8
  stay BLOCKED and must never be recorded as the pre-registered T-16 candidate.
- **If cascor needs restarting**, use `nohup bash util/ad-hoc/e2e_cascor_leg_supervise.bash >/dev/null 2>&1 &`
  — NOT the older `e2e_cascor_leg_restart.bash`, which recreates the orphan the reaper kills.
- Check `${LOG_DIR}/juniper-cascor-supervisor.log` before crediting any row — it timestamps every child
  exit, so a silent backend restart can never be mistaken for an uninterrupted run.
- **The 10 s snapshot-table rebuild breaks Playwright's actionability wait.** Locator `click()` times out
  ("element is not attached" / not stable). What works: do the whole gesture **inside one
  `page.evaluate`** with 50 ms polling — CDP round-trips cost ~800 ms each on this page, far too slow for
  the ≤3.6 s modal window. Raw JS `.click()` does drive Dash callbacks correctly (verified).
- Prove causation on the wire, not by timing: filter `_dash-update-component` request bodies by the
  control id and read the response. That is how W5-06 was credited.
- **Commits are unsigned** — the signing key timed out headless. Harmless (wip commits are squashed at
  close), but re-sign if that changes.
- Carry forward: F-CANOPY-002/003/004/005/006 — assert API first, DOM patiently.
- **NEVER reap while the stack runs** — cascor's forkserver children are still reapable, which disrupts an
  in-flight run even though the service now survives.
- Matrix status column still untouched; verdicts accumulate in the per-run TSVs, bulk-filled at close.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/warm-scribbling-island
git log --oneline -2          # expect b62c48b, 9b96873
git status --short            # expect clean
bash util/isolated_stack.bash --status                                      # data/cascor/canopy all 200
curl -sS http://127.0.0.1:8202/v1/network | head -c 80                      # "No network created" (empty)
curl -sS http://127.0.0.1:8051/api/v1/snapshots | head -c 120               # 1 snapshot
bash util/reap_pytest_orphans.bash --dry-run --verbose | grep 8202 -B2      # leg shows KEEP (live parent)
python3 util/ad-hoc/e2e_row_coverage.py --repo-root .                       # 109 / 189
```

Git: branch `arc/canopy-e2e-phase1-seg5`, pushed, clean tree. No stash use.
