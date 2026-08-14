# HANDOFF 2026-08-14 — Canopy E2E Phase 1: segment 10

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. Segment 9 **drove the W6
restart-confirm owner gate** that the previous three segments deferred, and **resolved F-CANOPY-019's open
question**. Run-id `20260811T010700Z`; per-run TSV `reports/e2e/20260811T010700Z/statuses.tsv`, **119 rows**.

**Branch.** Segment 9 rides `arc/canopy-e2e-phase1-seg9` (signed tip `fc2993b`), open as **evidence PR
juniper-ml#1106**. Branch segment 10 from `origin/main` **once #1106 merges**; if it is still open, branch
from its tip. The per-segment evidence-PR cadence (changed at segment-8 close) continues: one PR per segment,
not an accumulating chain.

**Browser MCP WAS available in segment 9** — `mcp__playwright__*` tools entered the session index for the
first time in the arc, so the `util/ad-hoc/` script drivers were not needed. Try the MCP first; the drivers
(`e2e_w3_params_driver.py`, `e2e_w6_dataset_driver.py`, run under
`/opt/miniforge3/envs/JuniperCanopy1/bin/python`) remain the fallback.

## Completed in segment 9

- **W6-16..20 DRIVEN.** W6-16 PASS (progress alert ≈1.8 s, orchestration ran), W6-17 PASS(truthful) /
  FAIL(message composition), W6-18 PASS, W6-19 + W6-20 FAIL(display only — pre-existing findings).
- **F-CANOPY-019 RESOLVED: the STAGED dataset wins at restart; the modal describes the SIDEBAR.** Staged
  `spirals/200/0.1`, set the sidebar back to `1000/0.25` *without* applying, confirmed → juniper-data produced
  `spiral-1.0.0-6514b5ab7f063c31` (`n_samples 200, noise 0.1`). The user reads "Samples: 1000" and gets 200.
  Not a cosmetic summary bug — the confirm dialog **misdescribes the action it performs**.
- **Two handoff worries disproven.** `reset: True` is hard-coded at **`:5453`** (not `:5447`), but with
  start-fresh OFF the network **survived** (`hidden_units` stayed 1; `current_epoch` reset 1→0) — it resets
  counters, not the model. The outcome alert is substantively truthful but ungrammatical
  (`"Started continued the current model."`, `:5504`).
- **A drafted P1 was withdrawn as a duplicate** — see "Do not re-file" below.
- §2.x partial: C2.1-03, C2.1-04, C2.2-02, C2.4-03 PASS, plus a new C2.5-TRANSPORT row confirming FE-1
  (control clicks travel as `/ws/control` frames; **zero** `/api/train/*` browser POSTs).
- Added `util/ad-hoc/e2e_poll_status.py` (status poller; the session sandbox refuses multi-command bash loops).

## Remaining work (priority order)

1. **The F-CANOPY-019 second-order arm — highest value, cheap, not yet driven.** `_execute_restart_handler`
   Phase 1 re-stages only when `_restart_dataset_changed(dataset_vals, baseline.dataset)` is true, and **both
   sides are seeded from the sidebar**. So editing **any** granular dataset field should flip the outcome —
   re-staging the sidebar values over the staged ones and silently discarding the pending change. That would
   make the dialog's effect depend on whether the user opened "Verify / modify what will happen" at all.
   Reproduce exactly as segment 9 did, but touch one granular field before confirming.
2. **Matrix status-column bulk-fill — still completely untouched** across all segments. 119 TSV rows are ready
   to map back into `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`.
   `util/ad-hoc/e2e_row_coverage.py` is the mapper.
3. **Remaining global chrome (§2.x)** — §2.3 top status bar, §2.6-§2.10 sidebar sections and global modals.
   Note §2.3's rows are only assertable on a page loaded **before** training starts (see below).
4. **W5-30 + the DEMO lane** (each demo arm must 501 and render `❌ Operation not supported in this mode`).
   The live stack runs `demo_mode:false`, so this needs its own approach.
5. **W6-21** (staging-failure arm) needs the shared juniper-data leg stopped — MANUAL, not attempted.
6. **W7/W8 remain BLOCKED** — the isolated recurrence leg is down (host 8211 is the juniper-deploy container;
   never record it as the pre-registered T-16 candidate).

## Do not re-file: the withdrawn finding

A live, reproducible observation — **a page loaded while training is already running shows
`Stopped / Idle / 0 hidden units` with `#latency-display` EMPTY, permanently**, across reloads, a new tab, and
a full canopy restart, while the backend was at 3 units / epoch 4 — was drafted as a new P1 and **withdrawn**.
It is the blast radius of two OPEN findings: **F-CANOPY-006** (topology counts "never update from any source";
segment 4 already recorded the identical 0/0/0-vs-correct-`/api/topology` reading) and **F-CANOPY-004**
(starved server-side callbacks leaving an element "empty 6+ min later"). Check the ledger before filing.

It is kept on the `F-CANOPY-020` TSV row for what it *does* add: the affected surface is the **top status bar
itself** (`update_unified_status_bar`, `:3087-3104`, on the same 1 s `fast-update-interval` F-CANOPY-006
fingers as the supersession driver); the failure is **permanent**, not the documented 30 s–minutes lag; an
**empty** rather than stale latency field discriminates "never produced a value" from "produced a late one";
and it correlates with **when the page was loaded** — the only live status bar all session was on a page
loaded *before* training started, which then tracked correctly including candidate progress `400/400`.
Ruled out already: interval throttling, a dead callback loop (62 callbacks/12 s, all 200), JS errors, server
errors, and init/localStorage state.

**Practical consequence for segment 10: load the dashboard BEFORE starting training** if any row depends on
the status bar or topology counters.

## Key context / gotchas

- **Stack UP and supervised**: data 8101 / cascor 8202 / canopy 8051 (`demo_mode:false`). Canopy was restarted
  onto `d11bfcd` in segment 9. **Training was left RUNNING** (3+ hidden units and growing, spirals/200/0.1).
- **The cascor leg pins `#513`.** Supervisor **2830431** / child **2830469**, booted `2026-08-14 03:52:46` —
  while cascor **#514** ("thread candidate patience and convergence to the pool") merged `04:57:03` and
  **#516** at `15:37:23`. Both are absent from the running leg. `ps -o lstart -p <pid>` vs `git log` before
  attributing ANY observed behaviour.
- **OPEN QUESTION (F-CASCOR-003b): the candidate pool was still resident after a clean stop** — forkserver +
  15 × 116 MiB at +90 s with `fsm_status` STOPPED, ancestry walked to this arc's own cascor child. **Not**
  recordable against current cascor main for the version reason above. **To settle: restart the cascor leg
  onto `fadfe80` and repeat start → stop → observe.** Worth doing early, since the network is disposable.
- Restart cascor ONLY via `nohup bash util/ad-hoc/e2e_cascor_leg_supervise.bash >/dev/null 2>&1 &` — NOT
  `e2e_cascor_leg_restart.bash`. Stop first with `kill -TERM <supervisor-pid>`. **Never reap while the stack
  runs.**
- **The card is SHARED** — another session runs cascor on the experiment_stack range (8230-8259). Walk the
  parent chain to a pid you own before attributing GPU load, and prove descent from *your* leg before killing
  anything.
- `/api/set_params`, `/api/stage_dataset`, `/api/cancel_pending_dataset` are POSTed **server-side** from Dash
  callbacks — **0 browser requests is EXPECTED**. Prove them on the canopy log (read by byte offset; it is
  >119 MB) plus `_dash-update-component`.

## Browser-driving techniques that work (segment 9)

- **Verify clicks by EFFECT, never by the tool's return.** `locator.click()` — even `force: true` — exceeds
  the tool budget after "done scrolling" while the element is provably stable and topmost.
  `page.mouse.click(x, y)` fired **without awaiting** does land (console showed
  `[Phase D] WS command success: stop <uuid>`). Compute coordinates and dispatch immediately; a layout shift
  in between silently misses.
- **Numeric inputs**: `element.focus()` via `page.evaluate`, then real trusted keystrokes
  (`Control+A` / `Delete` / `keyboard.type`). Post-#489 both `#nn-dataset-elements-input` (`step=1`) and
  `#nn-dataset-noise-input` (`step="any"`) commit cleanly.
- **`performance.getEntriesByType('resource')` caps at 250 entries** — a full buffer reads *exactly* like zero
  traffic and produced a wrong "the callback loop is dead" conclusion. `clearResourceTimings()` +
  `setResourceTimingBufferSize()` before counting. Also: never call `browser_network_requests` unfiltered on
  this page — the Dash callback volume floods the context.
- **Read a panel's counters only with its own tab ACTIVE** — panels are hidden, not unmounted, so a hidden
  never-hydrated panel returns `0` and looks exactly like a real failure.
- **`#welcome-modal` IS the `.modal-dialog`** — `#welcome-modal .modal-dialog` returns null and reads like a
  closed modal.
- **Scope `[role=option]` by the trigger's `aria-controls`** (a global query returned six options from other
  open dropdowns). Radix selects drive reliably by keyboard (focus → `Enter` → arrows) when a click won't take.
- **`window.cascorControlWS` is NOT the socket handle** — the bridge registers on `window.cascorWS`.
- **Settle before judging**, again: the W6-14 summary re-render read as a wall at 2.5 s and had updated by the
  next 1.5 s sample.

## Verification (run first)

```bash
cd <segment-10 worktree>
git log --oneline -1                                                    # segment-9 tip or main
git status --short                                                      # clean
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8101/v1/health   # 200 (repeat 8202, 8051)
python3 util/ad-hoc/e2e_poll_status.py                                  # one-shot status line
curl -sS http://127.0.0.1:8202/v1/network | head -c 120                 # live network, non-404
curl -sS http://127.0.0.1:8051/api/v1/snapshots | python3 -c "import sys,json;print(len(json.load(sys.stdin)['snapshots']))"   # 4
cut -f1 reports/e2e/20260811T010700Z/statuses.tsv | sed 's/-[0-9]*$//' | sort | uniq -c   # 119 data rows + header
ps -o pid,lstart= -p 2830469                                            # Fri Aug 14 03:52:46 — the #513-pinned leg
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
python3 -m unittest -q tests/test_isolated_stack_script.py              # 66/66 OK
gh pr view 1106 --repo pcalnon/juniper-ml --json state,mergeStateStatus  # segment-9 evidence PR
```

## Git state

Branch `arc/canopy-e2e-phase1-seg9`, signed tip `fc2993b`, pushed and rebased onto `main`; **PR
juniper-ml#1106 OPEN** (evidence doc + TSV 119 rows + `e2e_poll_status.py`). No stash use. No uncommitted work
beyond this handoff file. juniper-ml `main` carries `required_signatures` — commit with `-S`; if checks are
green and only signatures block, the **REST squash endpoint**
(`gh api -X PUT repos/<r>/pulls/N/merge -f merge_method=squash`) merges where `gh pr merge --squash` stalls.
