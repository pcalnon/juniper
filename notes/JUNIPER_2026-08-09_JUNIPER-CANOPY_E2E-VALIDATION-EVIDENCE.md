# Juniper Canopy — E2E Front-End Validation: Evidence Record

**Project**: juniper-canopy end-to-end front-end validation (execution arc)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Fable 5), session "canopy functionality testing"
**Started**: 2026-08-09
**Status**: PHASE 0 COMPLETE — PHASE 1 IN PROGRESS (run `20260810T002233Z`)
**Plan of record**: [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`](JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md) (merged juniper-ml#1036, approved by owner 2026-08-09)
**Execution script**: [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md)

This file accumulates the arc's execution evidence phase by phase (plan §9). Matrix row statuses live in the matrix's own `status` column at Phase-1 close; this file holds transcripts, findings, and the PR ledger.

---

## Phase 0 — Prerequisites & stack fixes (2026-08-09) — COMPLETE

### Exit criteria (plan §6.1)

| Criterion | Result |
|---|---|
| `--up` reaches the honest gate (`demo_mode == false`, `juniper_data_available == true`) | **PASS** (rehearsal 4, ~08:40Z) |
| `--down` releases all ports | **PASS** (8051/8101/8202/8211 all free post-teardown) |
| Env preflight | **PASS** (see below) |
| PR-M1 | **MERGED** — juniper-ml#1037 |
| PR-M2 (§4.5 default, owner-ratified) | juniper-ml#1042 (auto-merge armed at time of writing) |

### Env preflight (plan §6.1 step 3)

- Ports 8050/8051/8101/8202/8211: no listeners at preflight.
- `python3.14`: present at `/usr/bin/python3.14` — **stock GIL build** (`Py_GIL_DISABLED = 0`; no `python3.14t` exists) → drove fix (2) below.
- `juniper-cascor-client` in JuniperCanopy1: `0.7.0` — meets the `>=0.7.0` floor (T-3/T-4 preflight).
- `juniper-recurrence` console script: present in JuniperCascor1 (no dedicated recurrence env; experiment_stack parity).
- Canopy `make check-env` equivalent (`juniper-env-drift-check --repo-root juniper-canopy --check-lock`): **RESULT: OK** (5 lock pins OK).

### Bring-up rehearsal ledger

| # | Command | Result | Cause / action |
|---|---|---|---|
| 1 | `--up --with-recurrence` (defaults) | FAIL (data leg) | Session-worktree gotcha: `PROJECT_DIR` derives two-up from the script → resolved to `.claude/worktrees/`; `pip install -e .../worktrees/juniper-data[api]` invalid. Action: use `JUNIPER_E2E_PROJECT_DIR` (documented override); partial-failure teardown behaved correctly. |
| 2 | + `JUNIPER_E2E_PROJECT_DIR=<ecosystem root>` | FAIL (data leg, 60s gate burn) | `PYTHON_GIL=0` fatal on the now-stock host python3.14: `Fatal Python error: config_read_gil: Disabling the GIL is not supported by this build`. Action: fix (2). |
| 3 | + GIL-probe fix | FAIL (cascor leg) | **cascor main broken at HEAD** — see Finding F-E2E-001. Action: restore PR cascor#501; rehearsal re-pointed via symlink e2e-root at the restore worktree. |
| 4 | + restored cascor | **PASS — exit 0** | data healthy 2s → cascor 2s → recurrence 2s → canopy 6s. |

**Honest gate (rehearsal 4)** — `GET http://127.0.0.1:8051/v1/health`: `status: "ok"`, **`demo_mode: false`**, **`juniper_data_available: true`**, `version: 0.4.0`; `GET /v1/health/ready`: `overall: ready`, `juniper_data: healthy`, `juniper_cascor: healthy`; recurrence `GET :8211/v1/health/ready`: HTTP 200. Teardown: all four services stopped by port; `ss` re-check empty. Full transcripts: session scratchpad `rehearsal_up{,2,3,4}.log` (summarized here; scratchpad is transient by design).

### Findings (Phase 0)

**F-E2E-001 — cascor main broken by direct-push over-deletion (CRITICAL, HEALED).**
cascor commit `4081f5b` ("removing old snapshots", 2026-08-09 03:16 CDT, direct push) deleted the stale `src/snapshots/snapshot_*.h5` artifacts **and five live source modules** (`snapshot_cli.py`, `snapshot_common.py`, `snapshot_errors.py`, `snapshot_serializer.py`, `snapshot_utils.py`; 2,635 lines). `api/routes/snapshots.py:11` and `cascade_correlation.py` still import them → `create_app` import-dies; cascor Post-Merge Main Verification and Golden Regression (WS-6 Gate) went RED on main. Landing as a direct push bypassed the per-PR sequence-safety `juniper-symbol-loss-check` screen (which exists for precisely this class). **Heal**: cascor#501 restored the five modules byte-for-byte from `4081f5b^` (`.h5` deletions honored), merged 2026-08-09T08:47:50Z; primary cascor checkout fast-forwarded.

**F-E2E-002 — isolated_stack teardown glob reproduced the same over-deletion class (FIXED in #1042).**
`do_down`'s `snapshots/snapshot_*` glob matched the **source modules** (`src/snapshots/` is a Python package), reproduced live against a fresh cascor worktree. Root-cause rhyme for F-E2E-001's sweep pattern. Glob tightened to `snapshot_*.h5` + a `snapshot_cli.py` survival guard in tests.

**F-E2E-003 — host python3.14 regressed to a stock GIL build (FIXED for isolated_stack in #1042; experiment_stack follow-up PR in flight).**
`PYTHON_GIL=0` is fatal on stock CPython (`config_read_gil`). isolated_stack's data leg now probes `sysconfig Py_GIL_DISABLED` and passes the toggle conditionally. `util/experiment_stack.bash` carries the same latent class (3 sites) — follow-up PR delegated.

**F-E2E-004 — `juniper_plant_all.bash` flat `JUNIPER_CANOPY_PORT` is probe-only (LEDGER; operator path).**
The plant script's `JUNIPER_CANOPY_PORT` (default 8050) moves only its health-probe URL/origin derivation and is never exported into canopy's process — an operator override probes a port canopy never binds. Latent T-1 variant; works at defaults by coincidence. Triage in Phase 2/4.

**F-E2E-005 — `tests/test_experiment_stack_script.py` pre-existing `assertIn(..., env_text)` sites render ambient secrets on failure (LEDGER; test hygiene).**
Found by the #1044 executor while mutation-testing: the live-up stubs capture `env | grep -E '^(...|JUNIPER_)'` into `env_text`, and an assertion failure renders the whole blob — including live `JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI` tokens — the exact class `tests/redacted_env.py` exists to prevent. #1044's new assertions compare filtered line lists; the pre-existing sites remain. Follow-up: sweep that file (and siblings) for the shape. Severity: leaks only on local failure output, but real.

**F-E2E-003 scope precision (from the #1044 executor)**: the JuniperData *conda* env python (3.14.2) is still free-threaded (`Py_GIL_DISABLED=1`); only the *system* `/usr/bin/python3.14` (3.14.0) is stock. isolated_stack builds its venv from the system interpreter (live break, fixed in #1042); experiment_stack launches from the conda env (latent, hardened in #1044).

### PR ledger (Phase 0)

| PR | Repo | Content | State |
|---|---|---|---|
| #1036 | juniper-ml | Planning docs (plan + matrix + dual audits) | MERGED (owner) |
| #1037 | juniper-ml | PR-M1: canopy leg nested `JUNIPER_CANOPY_SERVER__PORT`/`__HOST` + checklist §3.3 + 3 test-site inversion + negative guards | MERGED |
| cascor#501 | juniper-cascor | Restore 5 snapshot modules (F-E2E-001 heal) | MERGED |
| #1042 | juniper-ml | PR-M2: `--with-recurrence` leg (8211, occupancy pre-check, canopy URL hand-off) + GIL probe + teardown glob `.h5`-only | auto-merge armed |
| #1044 | juniper-ml | experiment_stack GIL probe (F-E2E-003 tail; latent hardening — conda-env python still free-threaded) | MERGED |

### Notes for Phase 1

- Bring-up: `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper util/isolated_stack.bash --up --with-recurrence` (post-#1042 script; cascor primary is healed so no symlink root needed).
- Gate every live check on the §4.3 body assertions, never HTTP 200.
- Evidence: matrix row statuses + screenshots per plan §9 (`<row-id>__<step>.png`).

---

## Phase 1 — Live click-by-click validation (2026-08-10) — IN PROGRESS

### Run header (plan §9 / §8.5)

| Field | Value |
|---|---|
| Run-id | `20260810T002233Z` — screenshots `reports/e2e/20260810T002233Z/`, running row record `statuses.tsv` there; matrix `status` column filled in bulk at Phase-1 close |
| Stack | data 8101 (v0.11.0) · cascor 8202 (v0.6.0) · recurrence **8212** (8211 held by the operator Docker stack at bring-up; the #1042 occupancy pre-check relocated the leg — canopy env `JUNIPER_E2E_RECURRENCE_PORT=8212` confirms) · canopy 8051 (v0.4.0) |
| Honest gate (§4.3) | `GET :8051/v1/health`: `status:"ok"`, **`demo_mode:false`**, **`juniper_data_available:true`**; `GET /v1/health/ready`: `ready`, deps healthy (data 20.5 ms, cascor 15.7 ms), `details.mode:"service"` |
| Canopy env (live process) | `JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS=["http://127.0.0.1:8051","http://localhost:8051"]` present (F-E2E-006 fix live); `DEMO_MODE=0`; nested `SERVER__PORT=8051` |
| Transport | WS-primary confirmed: `/ws/training` + `/ws/control` both OPEN; control handshake observed in console (`CSRF token acquired` → `Sending CSRF auth frame` → `Control WS Status: open`) — plan T-21 posture as shipped |
| Browser | Playwright MCP Chromium, fresh profile (clean localStorage) |

### Findings ledger (Phase 1)

**F-E2E-006 — isolated_stack canopy leg lacked the browser-WS origin allowlist (stack harness; FIXED ml#1049).**
Found at first live browser attach (prior session, 2026-08-09): with `JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS` unset, canopy's browser-facing sockets rejected the dashboard's own origin. Fix: `util/isolated_stack.bash` canopy leg now exports the canopy-origin allowlist pair (`isolated_stack.bash:363-364`); merged as ml#1049. Verified live this run: both sockets OPEN with the allowlist in the process env.

**F-CANOPY-001 — dark-mode toggle glyph not synced from the persisted store on mount (P2, OPEN).**
Reproducer: toggle dark (glyph 🌙→☀️, `<html>` gains `dark-mode`) → reload → theme restores dark but the button renders the layout-default 🌙; the next click still behaves correctly (store true→false → light), so only the glyph is stale.
Evidence: `toggle_dark_mode` (`juniper-canopy/src/frontend/dashboard_manager.py:2905-2916`) is the **sole writer** of `dark-mode-toggle.children` and is `prevent_initial_call=True`; the PERF-CN-01 mount-time propagation (`:2921-2928`, `prevent_initial_call=False`) exists only for `theme-state` — the glyph Output is omitted from any mount path. Screenshots: `C2.1-01__dark.png` (correct ☀️ pre-reload), `C2.1-02__reload-glyph-desync.png` (dark theme + 🌙). Matrix rows C2.1-01/02 — both PASS on their stated expectations; this is a ledger finding, not a row FAIL.

**F-CANOPY-002 — `ws_latency.js` beacon CLOBBERS the WS bridge's `metrics` handler: the metrics fast path is dead in every live run and the panel starves (P0, OPEN; root-caused).**
Mechanism, proven live across two runs: `CascorWebSocket.on(type, handler)` is a **single-slot registry** — `this.handlers[type] = handler` silently replaces (`websocket_client.js:179-180`; dispatch `:258-260`). `ws_dash_bridge.js:217` registers the real `metrics` intake (feeding `_juniperWsDrain._metricsBuffer` → `ws-metrics-buffer` → `append_ws_metrics_store`, `dashboard_manager.py:3703-3712`); `ws_latency.js:75` then registers its latency-sampling `metrics` handler on the same socket — alphabetical asset load order guarantees the beacon loads after the bridge (console: "[WS Bridge] Handlers registered" precedes "[WS Latency] Beacon initialized") — and **replaces the bridge's**. Result: metrics frames arrive on `/ws/training` (run 2 raw-socket instrumentation: 401 `metrics` frames during the output phase) but dispatch ONLY into the latency sampler; the drain's metrics intake never fires (`_metricsReceived: false` / stale, buffer 0) while `state` / `candidate_progress` / `cascade_add` — types the beacon does not touch — flow normally on the same socket, and `initial_metrics` (its own un-clobbered slot) stamps the drain at reconnects. Live-run dispatch snapshot: `handlers['metrics'].toString()` = the beacon's `_recordLatency` body. Panel impact: KPI tiles / status pill / both plots / progress-detail sat frozen through both runs, catching up minutes later via the congested REST poll (M-METRICS-31 — `ws_live` correctly reads false, so the 1 Hz poll runs but lands ~30-90 s late under the F-CANOPY-003 congestion). Matrix: M-METRICS-31 FAIL (during-run), M-METRICS-32 FAIL. Fix direction (Phase 2): per-type handler LIST (registry append + dispatch fan-out), or route the beacon through the bridge. Note `off()` (`websocket_client.js:493-494`) already guards identity — only `on()` clobbers.

**F-CANOPY-003 — control-button loading state: success ack never re-enables; the 2 s timeout sweep lands at 30 s–minutes under callback congestion (P1, OPEN).**
Measured: Reset click → WS frame sent + success ack in ~1 s → optimistic ⏳ rendered at +4 s → button re-enabled at **+32 s**. Start's stuck window after its successful ack ran **minutes** (cleared only when the next control action fired the sweep's other Input). Evidence: the Phase-D clientside success path only `console.log`s — no button-states write and no `training-control-action` write on success (`dashboard_manager.py:233-236`); the sweep `handle_button_timeout_and_acks` (`:4246-4257`, handler `:6771-6796`) is the SOLE recovery and compares against `DASHBOARD_TIMEOUT_THRESHOLD = 2.0` s (`canopy_constants.py:384`) — the registration comment "Re-enable buttons after timeout (5s) or on control acknowledgment" is doubly stale (no ack path exists; threshold is 2 s). The 30 s+ real-world latency tracks the same server-side callback congestion that delayed every render during the run (12 Dash POSTs/s observed; `fast-update-interval` fired 26×/6 s). Matrix row C2.5-09 **FAIL**; C2.5-02's optimistic-disable half PASS.

**F-CANOPY-004 — server-side Dash callbacks lag 30 s–minutes behind reality during a live run; clientside callbacks are instant (P0/P1 systemic, OPEN).**
Measured, run 2 (topology tab, 1 Hz sampling for 60 s): canopy `/api/status` steady at `phase:candidate, hidden_units:1, epoch:1` for the full minute while the top status bar rendered `Output Training / Step 0 / Hidden Units 0/10` and the topology counts rendered `0/0/0/0` THROUGHOUT — yet the **clientside** depth-slider reveal (same underlying store) flipped `display:block` instantly. Same pattern everywhere: optimistic button ⏳ rendered +4 s after a clientside write; the 2 s button sweep landed +32 s (F-CANOPY-003); run-1 tiles caught up minutes post-run. Dash POST volume observed: ~12/s during a run (`fast-update-interval` alone fired 26×/6 s). Architecture note for Phase 2: every interval-driven server callback does a synchronous self-call `requests.get(self._api_url(...))` back into the same canopy server (e.g. `dashboard_manager.py:6376`), so callbacks queue behind their own server's request backlog; the WS drain pump (500 ms) multiplies POSTs during runs. Impact: during training — the only time the dashboard matters — every REST-fed surface is 30 s–minutes stale; only WS-clientside surfaces (badge) and the (currently clobbered, F-CANOPY-002) WS fast path can be truthful in real time. FA-3 rows C2.3-01..07 pass *eventually* but fail any reasonable freshness expectation; recorded here rather than as per-row FAILs since no row states a latency contract.

**F-CANOPY-005 — WS command send-promise races its own 3 s timeout under congestion: the REST fallback double-fires state-changing commands AFTER WS success (P0, OPEN; root-caused live).**
Captured on a W2 resume: the `{command:"resume"}` frame was acked on the wire **+18 ms** after send (`command_response`, matching `command_id`), yet the send-promise rejected `"Command timeout (no command_response for 81c7f1a1-…)"` and the Phase-D fallback then POSTed `/api/train/resume` — which the (already-resumed) backend refused **409**. Mechanism: `send()` arms a per-command `setTimeout` ceiling — start 11 s, set_params 2 s, **everything else 3 s** (`websocket_client.js:396-403,410-413`) — while ack matching happens in `_handleMessage → _resolvePendingCommand` on the browser main thread (`:210-211`, `:436-447`); during a run the main thread is blocked by the F-CANOPY-004 render queue, so the expired timer task can beat the queued WS `message` task and reject a command whose ack already arrived. Consequences: (a) duplicate **state-changing** POSTs (a lost race on `start` would re-POST start; observed on resume as a 409); (b) the operator sees a failure signal for a command that succeeded — `reportFailure` fed `training-control-action` with `success:false` (console: `[Phase D] REST fallback (resume): WS rejected: Command timeout…` then `…returned 409`), though the danger alert itself ALSO never rendered (its server-side callback starved — same congestion; alert element still empty 6+ min later). Composed with F-CANOPY-003: after this sequence THREE buttons (start/pause/resume) sat stuck ⏳ disabled >8 min — during a run the interval-driven sweep pass effectively never lands (quiet-page clear ≈ +32 s), so a rejected/raced command wedges its button for the rest of the run. W2 step 2's pause-pause rejection arm is **BLOCKED** by exactly this wedge: the second pause click hits a still-disabled button, so no frame is ever sent and C2.5-10's alert is unreachable via that route.

**F-CASCOR-001 — CUDA OOM in candidate seeding is classified "Completed — stalled (0 new units)" instead of an error state (P1, cascor repo, OPEN).**
W1 run 1: every `CandidateUnit` construction raised `torch.AcceleratorError: CUDA error: out of memory` at `candidate_unit.py:333`/`:392` (`torch.rand(1, device="cuda")` seed-roll) via `train_candidate_worker` (`cascade_correlation.py:3270`) — repeated per candidate — and the run transitioned `Started -> Completed` with the stall label. The UI surfaced cascor's classification faithfully (`Status: Completed — stalled (0 new units)` — honest-label plumbing WORKS, plan §7.3), but a hard environmental failure is indistinguishable from a legitimate correlation stall at every surface. Host cause: 7563/8192 MiB VRAM pinned by ~50 orphaned `JuniperCascor1` forkserver workers (the known orphan class). To file as a cascor issue.

**F-ML-001 — `util/reap_pytest_orphans.bash` kills nohup-detached isolated-stack services (P1, juniper-ml repo, OPEN).**
Freeing the VRAM via the repo's own reaper took down the live cascor service leg: isolated-stack services are launched `( cd … && nohup … & )`, so after the subshell exits they are parentless BY DESIGN — exactly the reaper's orphan predicate (candidate gate: JuniperC-env python; orphan: parent gone/init/systemd). Dry-run listed only forkserver/resource-tracker rows, but the live pass cascaded 145 kills including the service (`52 would be reaped` → `145 reaped`; the dry-run/live delta is itself a gap — children of reaped orphans re-classify mid-pass). The data leg survived only because its venv python path escapes the `JuniperC[a-z0-9]+` gate; canopy (JuniperCanopy1 — gate-matching) survived this pass but is equally exposed. Needs a service-pidfile exclusion (read `${RUN_DIR}/juniper-*.pid`) or a listener-port KEEP gate.

### Observations (non-finding)

- **Badge render lag**: `ws-connection-indicator` trails the client state machine by ~1–2 s in both directions (client `closed/reconnecting` at +0.8 s rendered amber at +2.8 s; client re-`open` rendered green ~2 s later). No latency contract exists in the matrix; recorded as §7.3 context.
- **Load sequence**: badge renders `WS: Offline` (red) during pre-first-connect hydration (observed +0.8 s → ~11 s on a cold reload) before settling `WS: Connected`; the server-rendered initial layout is `WS: --` grey `#6c757d` (verified from `/dashboard/_dash-layout` JSON — C2.4-01's authoritative source).
- **Rejected induction, documented for console-log honesty**: a `context.setOffline(true)` probe does NOT drop established localhost WebSockets (Chromium blocks only new connections) — the badge rightly stayed green while every HTTP poll failed, spraying **187 fetch errors** into the console (`console-2026-08-10T00-27-03-702Z.log`, all within the offline window, cleared by the next reload). Those errors are excluded from CON assertions; the working induction for badge states 6/7 is a client-side `ws.close()` under a temporarily raised `baseReconnectDelay`.
- Reconnect timing: a bare `ws.close()` on localhost recovers in ~121 ms (attempt 1) — too fast for the badge to repaint; the raised-delay induction is what makes states 6/7 renderable.
- **Doc divergences for the truth-up batch (D-ledger additions)**: (i) `stream_health.overall` recovery value is `"healthy"`, not the matrix's claimed `"ok"` (W14 steps 3/9, `main.py:1279` route); (ii) the About panel renders **"App Version: 2.2.0"** while `/v1/health` serves `version: 0.4.0` — the About `self.version` source is stale/mis-wired (`about_panel.py:323-345` block); (iii) depth-slider label read `"0 of 3"` while the slider had never been touched — the initial slider `value` seeds 0 rather than max, so the "user-picked value" semantics start from a filter that would draw zero cascade units (matrix M-TOPOLOGY-06/07 context; Phase-2 look).
- W1 run 2 (post-VRAM-heal): output phase streamed ~400 metrics frames on `/ws/training` (raw-socket capture), then candidate phases with steady `candidate_progress` (~35/30 s) and `state` frames; cascade growth 1→6+ units observed server-side; Evolution tab captured a growth card per add via the clientside WS path — confirming every WS type EXCEPT the clobbered `metrics` reaches Dash.
- Console-error ledger for the CON sweeps: zero uncaught errors across all tab walks; the only entries are (a) the deliberately-excluded offline-window fetch spam, (b) F-CANOPY-005's `409` + its two `[Phase D]` warnings.

### Phase-1 methodology notes

- **"NET" verifies for `/api/*` polls are server-side.** Canopy's interval callbacks fetch its own REST routes from INSIDE the Dash callback (`requests.get(self._api_url(...))`), so the browser network log shows only `_dash-update-component` POSTs — the matrix's NET expectations for poll rows are verified via the canopy log / direct endpoint probes, not browser DevTools. Browser-originated NET remains observable for the explicitly clientside paths (`/api/csrf`, `/api/ws_latency`, the Phase-D REST fallback, snapshot/replay panel fetches).
- **During-run DOM reads carry the F-CANOPY-004 lag** (renders land 30 s–minutes late). Rows whose *expected result* is a DOM state were credited only after the state actually rendered; rows starved past the run's end were re-read post-run when the callback queue drains. Direct endpoint probes were used to separate "backend wrong" from "render late" in every ambiguous case.
- **Multi-writer store races**: sub-second synthetic batch gestures (e.g. clicking all 5 accordion headers in one JS task) can race Dash's store round-trips; paced re-probes (600–900 ms gaps) were used before recording any FAIL.

### Row statuses (running)

`reports/e2e/20260810T002233Z/statuses.tsv` is the per-row record as rows execute. Verdicts so far: **C2.1-01..04 PASS** · **C2.4-01 PASS** · **C2.4-03 PASS** · **C2.4-06 PASS** · **C2.4-07 PASS** (C2.4-02 → DEMO lane; C2.4-04/05 → W14 induction).
