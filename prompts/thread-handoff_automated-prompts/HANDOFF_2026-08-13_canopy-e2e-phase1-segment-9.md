# HANDOFF 2026-08-13 — Canopy E2E Phase 1: segment 9

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. Segment 8 closed W3,
drove W6 through step 15, and shipped the first fix PR of the arc. Work is COMMITTED and PUSHED on
branch `arc/canopy-e2e-phase1-seg8` (worktree `piped-cuddling-squirrel`). Run-id `20260811T010700Z`.

**Branch note.** Branch `arc/canopy-e2e-phase1-seg9` from the pushed seg8 tip. Prior segments' worktrees
are locked by other sessions; a worktree-isolated session cannot run git against them. This is the arc's
normal mode, not an exception — it has now repeated four segments running.

**Browser MCP was unavailable in segment 8.** `claude mcp list` reported playwright and chrome-devtools
connected, but their tools never entered the session tool index and ToolSearch could not find them. The
fallback — now proven and preferred for causal work — is to drive Playwright from a script under
`util/ad-hoc/` with `/opt/miniforge3/envs/JuniperCanopy1/bin/python` (the only env with playwright;
chromium 147 launches fine). Two drivers exist: `e2e_w3_params_driver.py` (shared browser/log helpers,
`--steps` selector) and `e2e_w6_dataset_driver.py` (imports them via importlib). Try the MCP first; if
its tools are absent, use the drivers.

## Completed in segment 8

- **W3 CLOSED** (01-08 + 16) and **W6 driven 01-15**, all PASS. TSV 79 → **111 rows**.
- **F-CANOPY-017 (P1)** — editing a step-invalid numeric param silently applies a hardcoded default.
  HTML5 bases the step grid at `min`, so `#nn-learning-rate-input` (`min=0.0001, step=0.001`) rejected
  every plausible learning rate; the edit yields Dash State `None` and `dashboard_manager.py:6975`
  substituted `DEFAULT_LEARNING_RATE=0.01`. Live: 0.0789 → typed 0.0733 → applied 0.01. 7 of 22 sidebar
  number inputs were off their own grid. **FIX PR OPEN: juniper-canopy#489** (not merged — your review).
- **F-CANOPY-018 (P2)** — `params-status` has two writers; the dirty tracker re-fires on
  `applied-params-store` and overwrites the apply toast, so "Unsaved changes" shows after every
  successful apply and the applied/skipped/clamped detail is never seen. **Not yet fixed.**
- **F-CANOPY-019 (P2)** — the restart-confirm modal's "Restart plan" describes the SIDEBAR config, not
  the STAGED pending dataset (staged moons/200/0.1 vs summary "spirals / 1000 / 0.25"). **Not yet fixed.**
- Corrected the matrix's W3-02 framing: the wall is **step-grid validity**, not synthetic-vs-trusted
  events — real keystrokes behave identically and a step-valid field commits a typed value fine.
- Handoff correction: there are **4** snapshots, not 5 (history shows 3 creates + the pristine one, no
  deletes). Nothing was lost.

## Remaining work (priority order)

1. **Remaining global chrome (§2.x)**, then **W5-30 + the DEMO lane** (each demo arm must 501 and render
   `❌ Operation not supported in this mode`).
2. **W6-16..20 — OWNER GATE.** `#restart-confirm-button` POSTs `/api/train/restart` with `reset`
   **hard-coded True** (`dashboard_manager.py:5447`) regardless of the start-fresh switch, so confirming
   wipes the live 10-unit segment-6/7 network. Insurance snapshot `snapshot_20260813T051936Z` is on disk.
   Driving it also settles the open F-CANOPY-019 question of whether the staged dataset or the modal's
   summary actually wins at restart.
3. **W6-21** (staging-failure arm) needs the shared juniper-data leg stopped — MANUAL, not attempted.
4. **W7/W8 remain BLOCKED** — the isolated recurrence leg is down (host 8211 is the juniper-deploy
   container; never record it as the pre-registered T-16 candidate).
5. Matrix bulk-fill, then Phase 1 lands as ONE evidence PR (plan §6.2); the wip commits are crash-safety
   only and squash at close.

## Key context / gotchas

- Stack UP and supervised: data 8101 / cascor 8202 (supervised child, pid 437062 under supervisor
  437053) / canopy 8051 (`demo_mode:false`). Supervisor log has **zero child exits** across segments
  6+7+8 (~24 h).
- Restart cascor ONLY via `nohup bash util/ad-hoc/e2e_cascor_leg_supervise.bash >/dev/null 2>&1 &` — NOT
  `e2e_cascor_leg_restart.bash`. **Never reap while the stack runs.**
- Stack left at baseline: params restored (LR 0.1 / Adam / Tanh), pending dataset cancelled to None, FSM
  STOPPED, network still 10 units with the segment-7 mutations, **4** snapshots on disk.
- **`/api/set_params`, `/api/stage_dataset` and `/api/cancel_pending_dataset` are POSTed SERVER-SIDE from
  Dash callbacks — 0 browser requests is EXPECTED, never score it a failure.** Prove them on the canopy
  server log (read by byte offset; the log is >100 MB) plus the browser's `_dash-update-component`.
- **`dcc.Dropdown` renders as a Dash 3.x Radix select** — a `<button aria-haspopup="listbox">` with
  options portalled to body as `[role=option]`, NOT react-select (`.Select-control` does not exist).
  Match option names **exactly** or "Adam" also matches AdamW/NAdam/RAdam/Adamax. A global
  `[role=option]` query also picks up other open dropdowns' options.
- **Presence of a component id in a `_dash-update-component` body proves nothing** — every fire of a
  27-Input callback names all 27. Only the carried **value** is evidence. This nearly produced a wrong
  conclusion in segment 8.
- **An under-settled page silently drops the callback and reads exactly like a wall.** An early 5-rung
  input ladder "confirmed" the numeric wall and was wrong. Settle ~4 s after reload before judging.
- Running canopy tests via the env's python directly bypasses conda's LIBTORCH strip hooks — prefix with
  `LD_LIBRARY_PATH=` or you get a spurious `torch._C` ImportError.
- Three `src/tests/integration/test_demo_mode_gauge.py` failures are **pre-existing on clean canopy main**
  (verified as a control) — do not attribute them to a change.
- `offsetParent` is `null` for `position:fixed`; use `getComputedStyle` + `getBoundingClientRect`. A Dash
  slider commits only on a TRUSTED event. The welcome modal (`#welcome-modal-close`) sits over the
  dashboard after a fresh load. Confirm-modal DOM does not exist while closed — poll for it to appear.
- Verdicts accumulate in the per-run TSV via `util/ad-hoc/e2e_append_statuses.py` (dup-guarded;
  `--replace` rewrites a revised verdict in place). Matrix status column still untouched — bulk-filled at close.
- Commits are unsigned (signing key times out headless); harmless, wip commits squash at close.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/piped-cuddling-squirrel
git log --oneline -1                                                    # handoff commit atop 660c16d
git status --short                                                      # clean
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8101/v1/health   # 200 (repeat 8202, 8051)
curl -sS http://127.0.0.1:8202/v1/network | head -c 80                  # 10 hidden units
curl -sS http://127.0.0.1:8051/api/v1/snapshots | python3 -c "import sys,json;print(len(json.load(sys.stdin)['snapshots']))"   # 4
curl -sS http://127.0.0.1:8051/api/status | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['fsm_status'], d['pending_dataset'])"  # STOPPED None
tail -3 /tmp/juniper-e2e/logs/juniper-cascor-supervisor.log             # no child-exit lines
cut -f1 reports/e2e/20260811T010700Z/statuses.tsv | sed 's/-[0-9]*$//' | sort | uniq -c   # 29 W5 / 21 W6 / 18 NE / 17 REPLAY / 11 W11 / 9 W3 / 4 SNAP
python3 -m unittest -q tests/test_isolated_stack_script.py              # 66/66 OK
pre-commit run --from-ref origin/main --to-ref HEAD                     # clean
gh pr view 489 --repo pcalnon/juniper-canopy --json state,title         # the F-CANOPY-017 fix, open
```

All executed at segment-8 close and pass as written.

Git: branch `arc/canopy-e2e-phase1-seg8`, pushed, clean tree. No stash use. Canopy fix rides its own
branch `fix/params-step-grid-silent-default` (worktree
`worktrees/juniper-canopy--fix--params-step-grid--20260813-1030--2fdd2a0`) — clean up after #489 merges.
