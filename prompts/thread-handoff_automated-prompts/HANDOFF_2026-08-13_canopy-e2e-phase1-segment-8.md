# HANDOFF 2026-08-13 — Canopy E2E Phase 1: segment 8

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. Segment 7 closed the
Network Editor and Replay tabs and re-drove W11 behind an owner-approved training run. Work is COMMITTED
and PUSHED on branch `arc/canopy-e2e-phase1-seg7` (worktree `mighty-dancing-token`, tip `3018e7c`).
Run-id `20260811T010700Z`.

**Branch note — read first.** Seg5 (`warm-scribbling-island`) and seg6 (`encapsulated-prancing-sun`) are
both locked by other sessions; a worktree-isolated session cannot run git against them. Segment 7 branched
from the pushed seg6 tip. Do the same: branch `arc/canopy-e2e-phase1-seg8` from the pushed seg7 tip.
This is now the arc's normal mode, not an exception.

## Completed in segment 7

- **Network Editor 18/18** and **Replay 17/17** closed; W11 re-driven. TSV now **79 rows**.
- **F-CANOPY-011 proven LIVE**: with canopy's own `/api/status` reading `fsm_status: INVESTIGATING` and
  the network rehydrated to 10 units, the panel stayed idle/locked, badge `FSM: Unknown`
  (`state_machine` is literally `null`).
- **Correction to segment 6's framing**: cascor ITSELF refuses `add_hidden_unit_manual` /
  `remove_hidden_unit_manual` outside INVESTIGATING. The gate's intent is CORRECT — **fix the key
  (`state_machine.status` → `fsm_status`), do not remove the gate**. PATCH *is* allowed in STOPPED, which
  is why seg6's two landed mutations made the gate look gratuitous.
- **F-CANOPY-013 no longer latent** — captured on fully successful ops (`…index None (now None hidden
  units)`); the PATCH path is spared (it counts request-side values).
- **F-CANOPY-012 sharpened**: required shape is `(12,2)` = `(n_in+n_hidden, n_out)`, NOT `(2,12)`, while
  the placeholder says "row-major" — a naive reshape transposes, passes the shape check, and silently
  corrupts the network.
- **F-CANOPY-015 sharpened**: real values are at `data.session.*`; the backend's `range` is a **dict**
  `{start,end}` but the render does `range_value[0]/[1]` — reading one level deeper without a dict→list
  conversion turns a wrong readout into a `KeyError`.
- **F-CASCOR-002 UPGRADE P2 → P1**: optimizer loss is physical and self-propagating. Two independent
  restore→save cycles both wrote artifacts with the optimizer group ABSENT (191 nodes / 2 optimizer nodes
  / `learning_rate = np.bytes_(b'0.1')` → 0 optimizer nodes). A 2nd-generation snapshot cannot even hit
  the bug: training resumes with a fresh optimizer and NO warning.
- **F-CANOPY-016 (NEW, P1)**: the in-metrics replay control cluster **never dispatches**. With 401 rows
  loaded, `update_replay_ui` gets ZERO requests in 20 s though its store Input demonstrably changed (the
  sibling loss chart renders 401 points), and `metrics-panel-replay-state` gets ZERO on play/step clicks.
  Registered (rendered `0 / 0` at mount) then never re-fires. **Root cause NOT isolated** — that is fix-phase work.
- **F-CANOPY-002 confirmed client-side**: `_lastMetricsFrameMs: 0` (no metrics frame has EVER arrived)
  while `_lastStateFrameMs` is real and the socket is `connected/live`.

## Remaining work (priority order)

1. **W3 — parameter apply round-trip** (numeric-input wall; drive numerics via native-setter or
   `POST /api/set_params`).
2. **W6 — dataset COLD migration** (stage → restart). Segment 7 already proved the staging path:
   `POST /v1/training/dataset` `{"dataset_type":"spirals","params":{…}}` then Start. Note the sidebar
   `Apply Dataset` only stages canopy's *pending* config, and the banner's `Stop & Restart with new
   dataset` did NOT start a run — worth a row of its own.
3. Remaining global chrome (§2.x), then **W5-30 + the DEMO lane** (each demo arm must 501 and render
   `❌ Operation not supported in this mode`).
4. **W7/W8 remain BLOCKED** — the isolated recurrence leg is down (host 8211 is the juniper-deploy
   container; never record it as the pre-registered T-16 candidate).
5. Phase 1 lands as ONE evidence PR (plan §6.2); the wip commits are crash-safety only.

## Key context / gotchas

- Stack UP and supervised: data 8101 / cascor 8202 (supervised child, pid 437062 under supervisor 437053)
  / canopy 8051 (`demo_mode:false`). Supervisor log has **zero child exits** across segments 6+7.
- Restart cascor ONLY via `nohup bash util/ad-hoc/e2e_cascor_leg_supervise.bash >/dev/null 2>&1 &` — NOT
  `e2e_cascor_leg_restart.bash`. **Never reap while the stack runs.**
- Live state now: network 10/10 with segment-7 mutations (unit 0 weights `[0.11,0.22]`, `output_bias`
  `[0.75,-0.75]`, tail unit Sigmoid/bias 0.25), then a spirals training run to 401 metrics. **5 snapshots**
  on disk; `snapshot_20260811T010849Z` is the pristine V2 one, `snapshot_20260813T051936Z` is the
  pre-training insurance copy.
- **`offsetParent` is `null` for `position:fixed` elements — never use it as a modal visibility test.** Use
  `getComputedStyle` + `getBoundingClientRect().width/height > 0`. Two false "modal never opened" readings
  came from this.
- **A Dash slider commits only on a TRUSTED event.** Native-setter and synthetic pointer sequences move the
  handle with ZERO dispatches; `page.keyboard.press('ArrowRight')` on the focused thumb works. A moved
  handle is NOT evidence a value committed.
- After any reload the **welcome modal** (`#welcome-modal-close`) sits over the dashboard — dismiss first.
- Settle 1.5–2 s before clicking (a click within ~10 ms of a tab render is silently lost). Confirm-modal
  DOM does not exist while closed — poll for it to appear.
- The metrics store is **throttled**: in `full` mode only 1 poll in 15 returns data. A short window looks
  like a dead store when it is merely slow.
- Don't blame F-CANOPY-004 congestion before excluding the instrument — it is an attractive and therefore
  dangerous default explanation.
- Verdicts accumulate in the per-run TSV via `util/ad-hoc/e2e_append_statuses.py` (dup-guarded;
  `--replace` rewrites a revised verdict in place). Matrix status column still untouched — bulk-filled at close.
- Commits are unsigned (signing key times out headless); harmless, wip commits are squashed at close.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/mighty-dancing-token
git log --oneline -1                                                    # handoff commit atop 3018e7c
git status --short                                                      # clean
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8101/v1/health   # 200 (repeat 8202, 8051)
curl -sS http://127.0.0.1:8202/v1/network | head -c 80                  # 10 hidden units
curl -sS http://127.0.0.1:8051/api/v1/snapshots | python3 -c "import sys,json;print(len(json.load(sys.stdin)['snapshots']))"   # 5
tail -3 /tmp/juniper-e2e/logs/juniper-cascor-supervisor.log             # no child-exit lines
cut -f1 reports/e2e/20260811T010700Z/statuses.tsv | sed 's/-[0-9]*$//' | sort | uniq -c   # 18 NE / 17 REPLAY / 4 SNAP / 11 W11 / 29 W5
python3 -m unittest -q tests/test_isolated_stack_script.py              # 66/66 OK
pre-commit run --from-ref origin/main --to-ref HEAD                     # clean
```

All executed at segment-7 close and pass as written.

Git: branch `arc/canopy-e2e-phase1-seg7`, pushed, clean tree. No stash use.
