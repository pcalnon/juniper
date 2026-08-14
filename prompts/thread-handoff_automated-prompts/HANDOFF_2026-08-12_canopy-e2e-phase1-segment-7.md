# HANDOFF 2026-08-12 — Canopy E2E Phase 1: segment 7 (W5 LIVE lane CLOSED)

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. **W5 steps 1-29 are now
complete** — segment 6 closed the entire W5 LIVE lane. Work is COMMITTED and PUSHED on branch
`arc/canopy-e2e-phase1-seg6` (worktree `encapsulated-prancing-sun`, tip `8632acd`). Run-id
`20260811T010700Z`.

**Branch note — read first.** Segment 5 lived on `arc/canopy-e2e-phase1-seg5` in worktree
`warm-scribbling-island`, which is **locked** by another session; a worktree-isolated session cannot run
git against it. Segment 6 therefore branched `arc/canopy-e2e-phase1-seg6` from the pushed seg5 tip
(`d123cd2`) — the arc's established one-worktree-per-segment pattern. Continue from **seg6**, not seg5.

## Completed in segment 6

- **W5-07 re-run: PASS** (was INCONCLUSIVE). On a supervised leg with 10.6 h uptime and **zero child
  exits**, restore-confirm landed inside the F-CANOPY-010 window, cascor logged
  `POST …/restore -> 200 OK`, and the network went from empty to the full 10-unit cascade. The F-ML-001
  supervision remedy held all segment — no verdict here is environmental.
- **W5-08..29 all driven.** Verdicts: PASS 08, FAIL 09, PASS 10, PASS 11-17, FAIL 18, FAIL 19,
  BLOCKED 20-25, FAIL 26, PASS 27-29. All 29 W5 rows now carry verdicts in the run TSV.
- **Six findings opened, every one root-caused to file:line** (full write-ups in the evidence doc):
  - **F-CANOPY-011 (P1)** — the Network Editor reads the FSM from `state_machine.status`, a shape canopy's
    `/api/status` never returns (its field is `fsm_status`), so the gate is `False` unconditionally and the
    whole active editing surface is unreachable. It also **masks D-0**: the topology fetch targets the 404
    route `/api/network/topology` while `/api/topology` serves 200. **Fixing the route alone will not
    revive the panel.**
  - **F-CANOPY-012 (P2)** — `output_weights`, the default patch target, is structurally un-patchable from
    the UI: the panel parses a flat 1-D list, the route needs 2-D, and no reshape exists.
  - **F-CANOPY-013 (P3)** — success messages read payload keys off the envelope root instead of
    `envelope["data"]`, so a fully successful append reports `index None (now None hidden units)`. The
    remove callback repeats it latently.
  - **F-CANOPY-014 (P1)** — `replay_player_panel.py:80` defaults `_api_base_url` to `""`, so every replay
    control dies with `No scheme supplied`. Action-independent (play and stop identical); backend
    exonerated (direct POST → 200). It is the only one of three sibling panels with an empty fallback.
  - **F-CANOPY-015 (P2)** — the player reads `range`, `speed`, `weights_available` one nesting level too
    shallow; the badge reports `V1 (metrics only)` for a provably V2 snapshot. The other two misreads are
    masked only because the real values coincide with the fallbacks.
  - **F-CASCOR-002 (P2)** — snapshot load always drops optimizer state: `:448` writes `learning_rate` as a
    string, `:1037` reads it undecoded, torch's range check raises on `np.bytes_`, and it is swallowed to a
    WARNING with `output_optimizer=None`. Reproduced verbatim. Fires on **restore and replay** alike.
- **Key cross-cutting result**: driving the Network Editor's hidden-but-enabled controls by raw JS
  exercised the full callback → route → cascor path **successfully**, with two mutations that landed. That
  bounds F-CANOPY-011 to a gating defect — the editor itself is sound.
- Branch green: 66/66 `test_isolated_stack_script.py`, `pre-commit` clean over the whole branch diff.

## Remaining work (priority order)

1. **W5-30** — the DEMO-lane arm (repeat steps 16/27 in demo mode; each must return **501** and render as
   `❌ Operation not supported in this mode`). Needs the demo lane, so it belongs with the DEMO sweep.
2. Network Editor + Replay + W11 → W3 params → W6 → W7/W8 → remaining chrome → DEMO lane → Phase-1 close.
   **Note W7/W8 remain BLOCKED** — the isolated recurrence leg is still down (host 8211 is the
   juniper-deploy container; never record it as the pre-registered T-16 candidate).
3. Phase 1 lands as **ONE evidence PR** (plan §6.2); the wip commits are crash-safety only.

## Key context / gotchas

- **Stack is UP and supervised**: data 8101 / cascor 8202 (supervised child, pid 437062 under supervisor
  437053) / canopy 8051 (`demo_mode:false`).
- **If cascor needs restarting**, use `nohup bash util/ad-hoc/e2e_cascor_leg_supervise.bash >/dev/null 2>&1 &`
  — NOT `e2e_cascor_leg_restart.bash`, which recreates the orphan the reaper kills. Check
  `/tmp/juniper-e2e/logs/juniper-cascor-supervisor.log` before crediting any row; it timestamps every
  child exit.
- **Live network is deliberately mutated** by W5-12/13/15: `output_bias = [0.25,-0.25]`, tail unit is a
  synthetic ramp, still 10/10 at cap. The snapshot `.h5` on disk is **untouched**, so replay/resume/retrain
  still work from the pristine artifact.
- **A click within ~10 ms of a tab render is silently lost** (Dash hasn't wired the rebuilt
  pattern-matched Input). Settle 1.5-2 s before clicking. A lost click looks exactly like a broken control.
- **The confirm modal's DOM does not exist while closed** — poll for the element to *appear*; absence is
  the normal closed state, not a defect.
- **Page congestion is real**: two `page.evaluate` gestures with ~43 s budgets exceeded 120 s while the
  same ops succeeded instantly at the API (F-CANOPY-004). Where a row asserts a *backend outcome*, drive
  the API; reload the page when callbacks stall.
- Still do the whole modal gesture **inside one `page.evaluate`** with tight polling — CDP round-trips
  (~800 ms) cannot beat the ~3.6 s F-CANOPY-010 decay.
- **NEVER reap while the stack runs** — cascor's forkserver children are still reapable and disrupt
  in-flight runs even though the service now survives.
- Carry forward: F-CANOPY-002/003/004/005/006 — assert API first, DOM patiently. The topology DOM reads
  0/0/0 regardless of state (F-CANOPY-006), so take `I`/`H` from `/api/topology`.
- Matrix status column still untouched; verdicts accumulate in the per-run TSVs, bulk-filled at close.
- Commits are unsigned (signing key times out headless); harmless since wip commits are squashed at close.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/encapsulated-prancing-sun
git log --oneline -1          # expect the handoff commit atop 8632acd
git status --short            # expect clean
bash util/isolated_stack.bash --status                                        # data/cascor/canopy 200
curl -sS http://127.0.0.1:8202/v1/network | head -c 80                        # 10 hidden units
curl -sS http://127.0.0.1:8051/api/v1/snapshots | head -c 120                 # 1 snapshot
tail -3 /tmp/juniper-e2e/logs/juniper-cascor-supervisor.log                   # no child-exit lines
grep -c '^W5-' reports/e2e/20260811T010700Z/statuses.tsv                      # 29
python3 -m unittest -q tests/test_isolated_stack_script.py                    # 66/66 OK
```

All were executed against the live host at segment-6 close and pass as written. Two notes carried forward,
because both cost time when they were wrong:

- The reaper KEEP check must key on `KEEP.*uvicorn`, **not** on the port — `--verbose` truncates the
  cmdline before `--port 8202`, so a `grep 8202` returns nothing and looks like supervision failed.
- `git log` is deliberately not pinned to an exact pair; the handoff commit lands on top after this file is
  written, so hard-coded SHAs go stale immediately.

Git: branch `arc/canopy-e2e-phase1-seg6`, pushed, clean tree. No stash use.
