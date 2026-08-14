# HANDOFF 2026-08-10 — Canopy E2E Phase 1: segment 5 (W5 continuation)

Continue **Phase 1 live click-by-click validation** of the juniper-canopy E2E arc. Segment 4 is
COMMITTED and PUSHED on branch `arc/canopy-e2e-phase1-seg4` (worktree `cached-roaming-hamster`;
commits `c3b816d` + `951f80b`). Run-id `20260811T010700Z`.

## Completed in segment 4

- **Handoff reconciliation.** The prior handoff was stale in four ways: its worktree
  (`joyful-popping-castle`) no longer exists; the evidence doc was already committed (nothing lost);
  Phase 1 was already ~1/3 driven by two earlier sessions; and two divergent arc branches existed.
  `arc/canopy-e2e-phase1-results` held ~22 verdicts the later run never re-covered — preserved at
  `reports/e2e/20260809T223851Z/rowlog.md` and folded in (incl. **D-0 already confirmed live**).
- **Stack-topology correction.** Host **8211 is the juniper-deploy CONTAINER** (host 8211 → ctr 8210,
  up 30h; `.dockerenv` + docker cgroup + `docker ps`), NOT an E2E leg. The isolated recurrence leg is
  **DOWN**; canopy pointed at unserved 8212. W7/W8 stay BLOCKED — driven as-is they present exactly as
  the pre-registered **T-16** candidate for a purely environmental reason.
- **Two findings opened, root-caused to file:line** (full write-ups in the evidence doc):
  - **F-CANOPY-007 (P1)** — canopy CREATES snapshots via the cascor backend but LISTS them off a LOCAL
    path (`main.py:1713-1726`); silent empty list on any split filesystem. Blocks all of FA-4.
    **Confirmed by remediation.**
  - **F-CANOPY-008 (P0/P1)** — `/ws/control` CSRF gate leaks a per-IP slot on all five reject paths
    (no `release_connection_limits()`); 5 rejections permanently lock the control plane until canopy
    restarts. Shared across all clients behind NAT. Reachable with zero malice.
- **Harness**: `isolated_stack.bash` canopy leg now exports `JUNIPER_CANOPY_SNAPSHOT_DIR`; new
  `util/ad-hoc/e2e_canopy_leg_restart.bash` (verifies uid+cmdline before signalling; **health-gates**
  the recurrence hand-off). New `util/ad-hoc/e2e_row_coverage.py` mapper.
- Coverage: **298 matrix rows / 109 verdicted / 189 remaining.**

## Remaining work (priority order)

1. **Resume W5 at step 4** — preconditions still met and the snapshot list now works. Steps 4-7
   (view detail → restore modal → cancel → confirm), 8-10 (FSM `Investigating`, D-0 readout), 11-15
   (patch/append/remove; **I=2, H=10 → append vector is 12 floats**, sourced from `/api/topology`
   since the topology DOM is dead per F-CANOPY-006), 16-29 (replay lifecycle, resume/retrain, history,
   DEAD-EXPECTED probes).
2. Tasks #4-#10 in the session task list: Network Editor + Replay + W11 → W3 params → W6 → W7/W8
   (needs the recurrence leg) → remaining chrome → DEMO lane → Phase-1 close.
3. Phase 1 lands as ONE evidence PR (plan §6.2); the wip commits are crash-safety.

## Key context / gotchas

- **Stack UP and honest**: data 8101 / cascor 8202 / canopy 8051 (`demo_mode:false`,
  `juniper_data_available:true`). cascor holds a trained **10-unit** network, STOPPED, and now **one**
  snapshot (`snapshot_20260811T010849Z`). Recurrence leg DOWN.
- **Restarting canopy invalidates the browser's CSRF token** → `/ws/control` 403-loops and, via
  F-CANOPY-008, burns all 5 per-IP slots in ~10 s. **Always** park the browser at `about:blank`, restart,
  then `clearCookies()` + clear storage before reattaching (re-set `juniper_canopy_welcomed=1`).
- Carry forward: F-CANOPY-002/003/004/005/006 (button wedge, during-run DOM lag, REST double-fire,
  dead topology) — assert API first, DOM patiently.
- **NEVER `reap_pytest_orphans.bash` while the stack runs** (F-ML-001).
- Playwright: 5 s tool timeouts trip on this page — use `browser_run_code_unsafe` with generous waits.
- Matrix `status` column still untouched; verdicts accumulate in the per-run TSVs, bulk-filled at close.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-roaming-hamster
git log --oneline -2          # expect 951f80b, c3b816d
git status --short            # expect clean
curl -sS http://127.0.0.1:8051/v1/health | grep -o 'demo_mode":[a-z]*'      # false
curl -sS http://127.0.0.1:8051/api/v1/snapshots | head -c 120               # 1 snapshot
curl -sS http://127.0.0.1:8202/v1/network | grep -o 'hidden_units":[0-9]*'  # 10
python3 util/ad-hoc/e2e_row_coverage.py --repo-root .                       # 109 / 189
```

Git: branch `arc/canopy-e2e-phase1-seg4`, pushed, clean tree. No stash use.
