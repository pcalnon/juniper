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
| Stack | data 8101 (v0.11.0) · cascor 8202 (v0.6.0) · recurrence **8212** (8211 held by the operator Docker stack at bring-up; the #1042 occupancy pre-check relocated the leg — canopy env `JUNIPER_E2E_RECURRENCE_PORT=8212` confirms) · canopy 8051 (v0.4.0). **Superseded 2026-08-10 (segment 4): the isolated recurrence leg is DOWN — see §"Stack-topology correction" below. The trio (data/cascor/canopy) is unaffected and still honest.** |
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

**F-CANOPY-006 — the topology graph NEVER renders in the live lane: a provably-correct server render is silently never applied client-side (P0, OPEN; server side exonerated live).**
End-to-end isolation, all captured live on run 2's completed 10-unit network: (1) data layer perfect — `GET /api/topology` serves `input_units:2, output_units:2, hidden_units:10`, 14 nodes, 89 weighted connections; (2) the rebuild callback's own request body (intercepted) carries that full topology + `depth-slider.value: 10`; (3) the server's response (intercepted) is **HTTP 200, 39 KB, a 181-trace figure, counts `2/10/2/89`** — the rebuild (`network_visualizer.py:365-…`) computes correctly; (4) the DOM never changes: counts remain the layout-default `"0"`s and the applied Plotly figure stays `data:[]` — across the whole run, post-run quiet queue, a direct store injection, AND a fresh page reload (clean renderer). Zero console errors, zero server-side callback errors. Two compounding shipped facts: the depth slider ships `value=0, max=0` (`network_visualizer.py:180-183`), so every fresh session's rebuild input is a hierarchy filter of **zero** cascade units (label renders `"0 of N"` — the "user-picked" value nobody picked); and the rebuild's 12-Input set includes the 1 s `fast-update-interval` while its own server time measures 1.5–5 s (F-CANOPY-004), keeping the same-output callback perpetually re-queued — the prime Phase-2 suspect for the renderer never painting a response (supersession/serialization), to be confirmed at fix time. Blast radius: M-TOPOLOGY-01..18 and W4 BLOCKED (graph-dependent rows); W1 steps 12–14 blocked at the DOM (cascade growth itself proven server-side and via the Evolution tab's cards). The mandate's flagship visualization is non-functional in the live lane.

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

---

## Phase 1 — segment 4 (2026-08-10): state reconciliation

Segment 4 opened against a stale handoff. Reconciling it against the live host produced three
corrections and one evidence recovery, all recorded here before any new row was driven.

### Stack-topology correction — the isolated recurrence leg is DOWN

The segment-3 handoff (and the run header above) assert a live recurrence leg on **8212**. Re-probed at
segment-4 open: **false**.

| Probe | Result |
|---|---|
| `curl :8212/v1/health/ready` | `Failed to connect … Could not connect to server` — **nothing is serving 8212** |
| `curl :8211/v1/health/ready` | `{"status":"ready"}` — but **not an E2E leg** (below) |
| `ss -tlnpH "sport = :8211"` | listener with no owning host pid visible to this user |
| `pgrep -af juniper-recurrence` | pid 1169615 `/usr/local/bin/python3.13 … serve` — **no `--port` flag**, container-style prefix |
| `/proc/1169615/root/.dockerenv` | **present** |
| `/proc/1169615/cgroup` | `…/docker-106a7b2f….scope` |
| `docker ps` | `juniper-recurrence  127.0.0.1:8211->8210/tcp  Up 30 hours (healthy)` |

**Conclusion**: host 8211 is the operator's **juniper-deploy container** (host 8211 → ctr 8210), exactly the
collider `isolated_stack.bash:26-27,164-165,291-295` warns about; the canonical E2E default is
8211 (`isolated_stack.bash:83`), which is why the earlier session relocated the leg to 8212. That relocated
leg has since exited (canopy, started 2026-08-09 17:46, has survived it). Canopy still points at the dead
port: live process env carries `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=http://127.0.0.1:8212` and
`JUNIPER_E2E_RECURRENCE_PORT=8212`.

**Consequence (recorded to prevent a false finding)**: **W7 / W8 and every recurrence-dependent row are
BLOCKED until the isolated leg is restored on 8212.** Driven as-is they would fail for a purely
environmental reason while presenting exactly as the pre-registered **T-16** candidate (recurrence silent
no-op swap with Start still enabled). T-16 may only be adjudicated against a live leg. The deploy stack is
the operator's and is **not** to be stopped to free 8211 — the documented `JUNIPER_E2E_RECURRENCE_PORT`
override is the sanctioned path.

The trio is unaffected: data 8101 and cascor 8202 are host processes (`python` pid 1755429, `uvicorn`
pid 3325500 — the latter the documented mid-session cascor restart), and the honest gate re-passed at
segment-4 open (`demo_mode:false`, `juniper_data_available:true`).

### W5 preconditions re-verified live

`GET :8202/v1/training/status` → `state_machine.status STOPPED`, `phase IDLE`,
`monitor.current_hidden_units 10`, `is_training false`; `GET :8202/v1/snapshots` → `data: []`.
The trained 10-unit network and the empty snapshot baseline both survived the 26 h idle — W5 may proceed.

### Evidence recovery — the superseded `-results` run

Phase 1 was driven twice, on two branches, by two sessions:

| Branch | Run-id | Record | Fate |
|---|---|---|---|
| `arc/canopy-e2e-phase1-results` | `20260809T223851Z` | `rowlog.md` (91 lines) | superseded; its F-E2E-006 fix landed as ml#1049 |
| `arc/canopy-e2e-phase1` | `20260810T002233Z` | `statuses.tsv` (92 rows) | carried forward |

The later run re-covered most of the earlier one, but **~22 verdicts exist only in the earlier rowlog**.
It is preserved verbatim at `reports/e2e/20260809T223851Z/rowlog.md` rather than discarded, and its unique
rows are inherited with run-id attribution: **C2.2-02/04/05/06**, **M-WORKERS-06**, **M-REDIS-01/04**,
**M-CASSANDRA-01/04**, **M-TUTORIAL-01/02**, **M-ABOUT-03**, **M-PARAMETERS-01/02/03**, **M-REPLAY-01**,
**M-NETWORK-EDITOR-02/03/05/10**, and the **W13 step ledger 1–16**.

Most consequential: **M-NETWORK-EDITOR-05 already confirms divergence D-0 live** — readout
"No topology loaded.", server-side 404, *no browser-side request* — which the segment-3 handoff still
listed as outstanding work.

### Cross-run verdict reconciliation — C2.4-07

The two runs disagree, and the disagreement is itself evidence: the earlier run recorded **N-A
(annotated)** — "WS: Offline" judged unreachable, because the retry-forever client collapses
`closed`→`reconnecting` in a single status update (GAP-WS-31) and a MutationObserver over a fresh socket
close saw no intermediate state. The later run recorded **PASS**, catching the red `#dc3545` state in the
*pre-connect* window (t≈+806 ms after reload) rather than via socket loss. **PASS stands**; the earlier
note is retained as the methodology reason the state is invisible on the socket-loss path.

### Coverage baseline

`util/ad-hoc/e2e_row_coverage.py` (added this segment) diffs the matrix row inventory against every
accumulated verdict record, expanding the compressed range notation the run records use
(`M-TOPOLOGY-01..06,09..18`). At segment-4 open:

**298 matrix rows · 104 verdicted · 194 remaining.** The mapper only credits a row when its id is the
verdict record's *subject* (first TSV field / first table cell), so rows recorded in the earlier rowlog's
prose bullets (`M-PARAMETERS-02/03`, `M-NETWORK-EDITOR-03/05/10`) read as remaining and will be
re-confirmed live rather than assumed — a deliberately conservative bias.

### Observation candidates promoted from the `-results` sweep

- **OBS-1 → docs-truth-up (Phase 4)**: About panel "App Version: 2.2.0" vs `/v1/health` `version: 0.4.0` —
  two disagreeing version sources (about-panel local `self.version` vs the health handler). Corroborated
  independently by the later run (TSV `M-ABOUT-02`).
- **OBS-2 → UX candidate (Phase 2 triage)**: dark mode flattens all five training-control buttons to a
  uniform blue, losing the light-mode semantics (Start green / Pause yellow / Stop red). Legible, but
  semantics-destroying. Evidence: `W13-13__dark-metrics-top.png` vs the light walkthrough capture.
- **OBS-3 → not a finding**: metrics-tab sidebar header "Network Parameters" vs tutorial-tab "Training
  Controls" is `TAB_HEADER_MAP` behaving as designed (C2.2-04 corroboration).

### Findings opened in segment 4

**F-CANOPY-007 — canopy CREATES snapshots through the cascor backend but LISTS them off a LOCAL
filesystem path; on any split-filesystem deployment the list is silently empty (P1, OPEN).**

Found driving W5 step 3. The create succeeded end-to-end — panel reported
`✅ Snapshot created successfully: snapshot_20260811T010849Z`, both inputs cleared — yet the table stayed
on its empty state and `#hdf5-snapshots-panel-status` still read "No snapshots available". The UI was
faithful; its own API was wrong:

| Probe | Result |
|---|---|
| `GET :8202/v1/snapshots` (cascor) | `{"status":"success","data":[{"id":"snapshot_20260811T010849Z","size_bytes":296701,"path":".../juniper-cascor/src/snapshots/…h5"}]}` |
| `GET :8051/api/v1/snapshots` (canopy) | `{"snapshots": [], "message": "No snapshots available"}` |

Mechanism: `get_snapshots` (`juniper-canopy/src/main.py:1874-1909`) serves `_list_snapshot_files()`
(`:1838`), which reads `_snapshots_dir` — `JUNIPER_CANOPY_SNAPSHOT_DIR`, else the deprecated
`CASCOR_SNAPSHOT_DIR`, else **`"./snapshots"` relative to canopy's CWD** (`:1713-1726`). The detail and
op paths resolve through the same root (`_find_snapshot_file`, `:1764-1806`, used at `:2000`). Creation,
by contrast, is proxied to the cascor backend, which writes under **its own** `src/snapshots`. Live: the
env var was unset, canopy's CWD was `juniper-canopy/src`, and `juniper-canopy/src/snapshots/` held only
`snapshot_history.jsonl` — no `.h5` at all.

Why it has never been seen: the shipped compose topology co-mounts ONE volume
(`juniper-cascor-snapshots:/app/data`, `juniper-deploy/docker-compose.yml:265` and `:434`) into both
services, so the local read resolves to cascor's directory. Two host processes with different CWDs — the
isolated stack, or any split-host deployment — do not share it. The failure is **silent**: no error, no
warning, no degraded-mode signal; `snapshot_history.jsonl` is still written locally, so history and list
actively disagree.

Blast radius: the entire FA-4 surface (list / detail / restore / replay / resume / retrain), i.e. W5
steps 4-7 and 16-27, because every one of them needs a table row that can never appear.

**Confirmed by remediation** — the strongest available proof. After exporting
`JUNIPER_CANOPY_SNAPSHOT_DIR` at cascor's real snapshot dir and bouncing the canopy leg, the same probe
returned the snapshot with its true path, and the panel rendered `1 snapshot(s) found`, empty state
`display:none`, one row (289.7 KB), 1 View button + 4 op buttons.

Fix direction (Phase 2): canopy should resolve snapshots through the backend it created them with rather
than assuming a shared filesystem — or, at minimum, detect that the configured dir is not the backend's
and surface a degraded-mode banner instead of an empty list.

**F-CANOPY-008 — the `/ws/control` CSRF gate leaks a per-IP connection slot on every rejection;
five rejections permanently lock the control plane out until canopy restarts (P0/P1, OPEN).**

Found immediately after the canopy bounce above. `/ws/training` reconnected normally; `/ws/control`
403-looped, and the audit log named the reason:
`{"event":"ws_csrf_rejected","endpoint":"/ws/control","reason":"invalid_token"}` × 5 — the browser was
still presenting a token minted by the *previous* canopy process. That part is expected. What is **not**
expected is what those five rejections left behind: `Per-IP limit reached for 127.0.0.1 (5/5)`, which then
survived a full page close, `clearCookies()`, `localStorage`/`sessionStorage` clear, and a 20 s idle
window. The counter never came back.

Mechanism, read out of the handler (`juniper-canopy/src/main.py`, `/ws/control`):

| Step | Path | Slot handling |
|---|---|---|
| Origin validation | `close(4003); return` | correct — returns *before* any reservation |
| `check_connection_limits(...)` | reserves a per-IP + per-session slot | its own per-session failure arm decrements (`websocket_manager.py:544`) |
| `connect(...)` | `except: release_connection_limits(); raise` / `if not connected: release_connection_limits()` | **correct on both arms** |
| **CSRF first-frame auth** | `missing_or_invalid_frame`, `invalid_token`, `auth_timeout`, `malformed_auth`, generic `Exception` | **all five do `log…(); close(1008); return` — none calls `release_connection_limits()` or `disconnect()`** |

The reservation taken before `connect()` is therefore never rolled back when the CSRF gate rejects.
`websocket_manager.release_connection_limits` (`:549-559`) exists for precisely this rollback and its
docstring describes the window; the surrounding `connect()` call was written with that discipline and the
CSRF block that follows was not. Since `connect()` had already *succeeded*, the socket is also still
registered in `active_connections` — so the leak plausibly extends to the registration and to
`juniper_canopy_websocket_connections_active{channel="control"}`. (The counter leak is proven live; the
registration/metric leak is a code-reading inference to confirm during Phase 2 triage.)

Why this matters well beyond the test rig, with `max_connections_per_ip: int = 5` (`settings.py:156`):

- It is reachable with **zero malice** — restart canopy, or simply let a token go stale, with a dashboard
  tab open. The client's own auto-reconnect burns all five slots in about ten seconds. That is exactly how
  it was hit here.
- Recovery requires **restarting canopy**. Nothing the operator does in the browser releases the slots.
- The cap is **shared across all clients behind NAT** — the method's own docstring states that inside
  Docker every client presents as the bridge-gateway IP. So five CSRF failures from *one* user lock the
  control plane for *every* user of that deployment.
- Because the training buttons are WS-primary (T-21), the visible symptom is "the training controls stopped
  working", with only a console 403 to go on.

Fix direction (Phase 2): release the reservation on every CSRF reject path — cleanest as a `try/finally`
(or a small context manager) around the post-reservation block so no future gate inserted after
`check_connection_limits` can reintroduce the leak. Regression test: drive N+1 rejected handshakes from
one IP, then assert a *valid* handshake still connects.

Note this is the "audit every call site when extending a shared helper" class: the helper was correct and
correctly used at the call site it shipped with; the later-added gate simply did not adopt it.

---

## Phase 1 — segment 5 (2026-08-11): W5 steps 4-7

### Stack state on entry — the cascor leg had died

Segment 4 handed off "stack UP and honest: data 8101 / cascor 8202 / canopy 8051". On entry to segment 5
the cascor leg was **DOWN and had been for ~7.6 h**:

| Probe | Result |
|---|---|
| `isolated_stack.bash --status` | data `health=200 pid=1755429` · cascor **`health=000 pid=none`** · canopy `health=200 pid=2375744` |
| `/tmp/juniper-e2e/logs/juniper-cascor.log` | last write `2026-08-10 20:36` local (= `2026-08-11T01:36Z`); ends **mid-poll** on a `GET /v1/training/status 200 OK` |
| uvicorn shutdown lines | none — no `Shutting down`, no traceback, no exit code |
| `syslog` OOM in the window | none (`grep -iE 'oom|killed process'`, `Aug 10 19:00–21:59` → no hits) |

An abrupt end mid-request with no graceful shutdown and no OOM is a **hard external kill**. This is the
second occurrence of the **F-ML-001** class already in this ledger — and the sibling helper
`util/ad-hoc/e2e_cascor_leg_restart.bash` was written during the *first* occurrence, its header recording
"after an orphan-reaper pass took down the nohup-detached cascor service". A concurrent experiment
campaign was active across the window (run dirs `20260811T022342Z` … `20260811T042344Z` under
`~/.local/state/juniper-experiments`), and orphaned `JuniperCascor1` forkserver children from a dead
experiment_stack cascor (port 8230, ~4.8 h old) were still resident. F-ML-001 therefore stands **unfixed
and demonstrably recurrent**: the isolated stack's nohup-detached services remain reapable by any
concurrent session's cleanup pass. The pidfile-exclusion / listener-port KEEP gate proposed in F-ML-001 is
what would have prevented both occurrences.

Recovery: `bash util/ad-hoc/e2e_cascor_leg_restart.bash` → `cascor healthy on 8202`. Canopy was **not**
touched, so the browser CSRF context stayed valid and no F-CANOPY-008 slot was burned.

**Canopy reconnect — an unprompted resilience positive.** Canopy rode the entire 7.6 h outage and healed
itself with no intervention: `Control stream supervisor connected to ws://127.0.0.1:8202` at `04:14:04`
and `Cascor metrics stream connected` at `04:14:19`, with the next relay summary reading
`status=healthy; reconnects=1`. The supervisor's fixed 30 s control-stream backoff and the metrics
stream's escalating backoff both behaved as designed across a multi-hour outage. Relevant to the W14
outage-recovery rows.

### Precondition change — restore now targets an EMPTY cascor

The restarted cascor came back with no in-memory model: `GET :8202/v1/network` → `404 "No network created"`,
FSM `STOPPED/IDLE`, `current_hidden_units: 0`. The trained 10-unit network segment 4 handed forward is
**gone**; the snapshot file survived on disk (`snapshot_20260811T010849Z.h5`, 296 701 bytes).

This *strengthens* W5 steps 4-7 rather than weakening them: the restore is now exercised into a genuinely
empty backend, which is the honest test of the restore path, and its success becomes the precondition for
steps 8+ instead of being masked by a network that was already resident. Recorded here because any later
row that assumes "10 units were already loaded" must read this note first.

### Findings opened in segment 5

**F-CANOPY-009 — the snapshot detail panel is wiped by the table's own 10 s refresh: every selection
self-destructs within one tick (P1, OPEN; root-caused live).**

Found driving W5 step 4. The row's `View Details` button *does* work — the panel fills correctly — and then
the panel clears itself with no user action. Measured live, single click, 500 ms polling of
`#hdf5-snapshots-panel-detail-panel`:

| t (ms from probe start) | Panel content |
|---|---|
| 10 527 | `Select a snapshot from the table above to view its details.` (placeholder) |
| **14 308** | **`ID: snapshot_20260811T010849Z  Name: snapshot_20260811T010849Z.h5  Times…`** (filled) |
| **21 320** | `Select a snapshot from the table above to view its details.` (**wiped**) |

Visible lifetime ≈ **7 s**, bounded above by the panel's 10 s refresh tick. The first three attempts of this
row were recorded as "button does nothing" purely because each post-click read at +7–10 s sampled *after*
the wipe — the defect masquerades as a dead button.

Mechanism, captured from the wire (`_dash-update-component` request/response pairs):

1. `select_snapshot` (`juniper-canopy/src/frontend/components/hdf5_snapshots_panel.py:995`) fires with
   `changedPropIds` naming the row button's `n_clicks` and `state` carrying the correct
   `{"type":"hdf5-snapshots-panel-view-btn","index":"snapshot_20260811T010849Z"}` — and returns
   `{"hdf5-snapshots-panel-selected-id":{"data":null}}`. The serialized `inputs` entry carries **no
   `value` key**, i.e. `n_clicks` arrives falsy.
2. `update_detail_panel` (`:1038`) then fires with `selected-id.data = null` and returns the placeholder
   `P` element — captured verbatim in the same trace.

Why `n_clicks` is falsy on that second firing: `update_snapshots_table` (`:868`) is driven by
`Input(f"{component_id}-refresh-interval", "n_intervals")` (`:862`) on a **10 s** interval
(`DEFAULT_REFRESH_INTERVAL_MS = 10000`, `:53`; wired `:361-364`) and rebuilds **every row from scratch**
each tick. The rebuilt `View Details` button (`:920-927`) is constructed **without `n_clicks=0`** — unlike
all four sibling op-buttons (`:936-954`), which each pass it explicitly. Its counter therefore returns as
`None`, the pattern-matching `Input(..., ALL)` sees the input list change, and `select_snapshot` re-fires
with `n_clicks_list = [None]`. It hits its own guard at `:997-998`:

```python
if not n_clicks_list or not any(n_clicks_list):
    return None
```

`any([None])` is `False`, so the callback **clears** the store rather than leaving it alone — and the
detail panel follows it down.

Two structural notes that matter at fix time:

- All four early-outs in this callback (`:998`, `:1002`, `:1007`, `:1012`) `return None`. Every one of them
  means "nothing meaningful triggered me", yet each **destroys** existing selection state. `dash.no_update`
  is the correct return for all four and `dash` is already imported at `:41` — the fix is a one-token change
  per site, not a refactor.
- The author's own fallback at `:1022-1030` ("find the button with highest `n_clicks`") is **dead code**: it
  sits in the `except json.JSONDecodeError` arm, which is only reachable *after* passing the `:997` guard
  that already rejected this exact state. Someone anticipated this failure mode and the guard above it
  prevents the remedy from ever running.

Blast radius: W5 step 4, and every downstream row that needs a *stable* selection — the detail panel is the
only surface exposing a snapshot's HDF5 attributes (`format_version`, `serializer_version`,
`juniper_version`), so the V1/V2 determination behind W5 step 18 cannot be made from the UI. Any operator
reading a snapshot's provenance has a ≈7 s window per click.

Note the contrast with **F-CANOPY-007**: that one made the list unreachable on a split filesystem; this one
makes the *detail* unreadable even when the list is correct. They are independent defects on the same
panel, and 007's fix is what made 009 observable at all.

Fix direction (Phase 2): return `dash.no_update` from all four early-outs in `select_snapshot`, and
construct the `View Details` button with `n_clicks=0` to match its siblings so the rebuild stops
re-triggering the callback at all. Regression test: select a snapshot, hold past two refresh ticks
(> 20 s), assert the detail panel still renders the selected id.

**F-CANOPY-010 — the snapshot-operation CONFIRMATION MODAL closes itself ~3.6 s after opening; the
operator has under four seconds to read and confirm a state-changing action (P1, OPEN; root-caused live).**

Same class as F-CANOPY-009, different callback, worse consequence — recorded separately because it needs
its own fix and its own regression test. Found driving W5 step 5.

The modal opens **correctly**. Body captured live, matching the matrix expectation on both halves:

> `Confirm Restore of snapshot: snapshot_20260811T010849Z` · `Load this snapshot for inspection and
> modification. Training is NOT started — invoke Retrain or Resume to begin a training run.` · `⚠️ Training
> must …`

Then it decays, in two stages, with no user action:

| t (ms from click) | State |
|---|---|
| 2 256 | modal open, body correct |
| 4 765 | modal still open, **body emptied** (`""`) |
| 5 887 | **modal gone** |

≈ **3.6 s** of usable life. Mechanism: `open_snapshot_op_modal`
(`hdf5_snapshots_panel.py:1151`) is fed by `Input({"type": …-snapshot-op-btn, "index": ALL, "op": ALL},
"n_clicks")` (`:1146`). The same 10 s `update_snapshots_table` rebuild that drives F-CANOPY-009 reconstructs
the dropdown items, re-firing this callback with a falsy `n_clicks`; it takes one of its four early-outs
(`:1167`, `:1171`, `:1175`, `:1198`), each of which returns the triple

```python
return False, "", None      # is_open=False, modal_body="", pending_id=None
```

— i.e. it *actively slams the dialog shut, blanks its body, and discards the pending operation id*. The
two-stage decay above is exactly those three Outputs landing across ticks. Note the op-buttons **do** carry
`n_clicks=0` (`:936-954`), so unlike F-CANOPY-009 this is not a missing-default bug — the guard at `:1170`
rejects the rebuilt `0` as falsy just the same. The fix is the same one-token change (`dash.no_update`,
already imported at `:41`) at all four sites.

Severity above F-CANOPY-009: this is the **confirmation gate for restore / replay / resume / retrain** — the
operations that mutate live training state. A confirmation dialog that revokes itself in 3.6 s either
trains the operator to click without reading, or silently drops the action. It also discards
`-restore-pending-id`, so the pending operation is gone even if the button were still reachable.

Reproduction is deterministic and needs no special timing: open any row's op menu, pick any operation,
wait four seconds.

### W5 steps 5-7 — results

- **Step 5 PASS.** Modal opens with the correct title and the ⚠️ training-state warning (body quoted above).
  The self-close is filed as F-CANOPY-010, not as a step-5 failure — the step's stated expectation is met.
- **Step 6 PASS**, and proven on the wire rather than by timing. Cancel produced exactly one
  `_dash-update-component` carrying `restore-cancel`, answered
  `{"hdf5-snapshots-panel-restore-modal":{"is_open":false}}` — the dedicated cancel callback (`:1209-1210`)
  — with **zero `/api/` requests** in the window, satisfying "modal closes, no request". Timing confirms the
  close was the click and not the F-CANOPY-010 decay: modal open t=3383 ms, cancel clicked t=3390 ms, closed
  t=6172 ms.
- **Step 7 INCONCLUSIVE — re-run required.** Confirm fired and the panel rendered
  `❌ Failed (restore): Failed to restore snapshot`, but **the cascor leg was already dead when it landed**,
  so this is environmental and *not* a canopy verdict. A direct probe taken while cascor was down returned
  the identical `HTTP 500 {"detail":"Failed to restore snapshot"}` from
  `POST :8051/api/v1/snapshots/{id}/restore` — canopy's message is faithful to an unreachable backend.
  Recorded as INCONCLUSIVE rather than FAIL. One honest-label observation does survive: the surface reports
  failure correctly but carries **no diagnostic** distinguishing "backend unreachable" from "restore
  rejected" — the operator cannot tell these apart from the UI.

### F-ML-001 UPGRADE — three confirmed kills in one session; the trigger is now pinned

F-ML-001 was filed as "the reaper can kill nohup-detached isolated-stack services". This segment escalates
it from a hazard to a **demonstrated, repeating, arc-blocking failure**, and pins both the trigger and the
selectivity.

Three kills of the isolated cascor leg (8202) inside ~1 hour, each within ~2 s of a concurrent
experiment-campaign run directory being created:

| # | cascor log last write | Concurrent run dir created | Δ |
|---|---|---|---|
| 1 | `2026-08-11 01:36` (local 20:36 Aug 10) | campaign active across the window | — |
| 2 | `04:34:01.118` | `20260811T093401Z-3b2b` → 04:34:01 | **~0 s** |
| 3 | `04:36:45.999` | `20260811T093647Z-dae2` → 04:36:47 | **~2 s** |

Every kill is abrupt: last line is a served request, no uvicorn `Shutting down`, no traceback, and no OOM
in `syslog` for any window. Kill #3 landed *mid-gesture*, between the restore-confirm click and its
response — which is what produced the INCONCLUSIVE W5-07 above.

**Why cascor and not the other two legs** — the reaper's predicate explains the selectivity exactly, and
all three legs behave as predicted:

| Leg | cmdline | Matches `JuniperC[a-z0-9]+` gate? | Parentless? | Outcome |
|---|---|---|---|---|
| cascor 8202 | `/opt/miniforge3/envs/**JuniperCascor1**/bin/python3.13 …/uvicorn api.app:create_app` | **yes** | yes (ppid 1/systemd — nohup by design) | **killed, 3×** |
| data 8101 | `/tmp/juniper-e2e/.venv-data/…/python -m juniper_data` | no (venv path) | yes | survived |
| canopy 8051 | `python main.py` (bare argv; env path not in cmdline) | no | yes | survived |

So the leg that dies is precisely the one whose **conda env name appears in its cmdline**. Data and canopy
survive by accident of how they are invoked, not by any protection — F-ML-001's original note that canopy
"is equally exposed" is confirmed as *conditionally* true: it escapes only because `python main.py` hides
`JuniperCanopy1`.

**The trigger is an operator action, not the campaign scripts.** `util/experiments/**` and
`util/experiment_stack.bash` contain no `reap_pytest_orphans` / `kill_all_pythons` / `pkill` / `killall`
invocation (greps clean). The kills therefore come from the concurrent session's *manual pre-run reap* —
the standing practice of clearing orphaned `JuniperCascor1` forkserver children before each campaign run
(the known GPU-leak class). Corroborating: the ~4.8 h-old orphaned forkserver children from a dead
experiment cascor on port 8230 that were resident at segment start were gone after kill #2.

Consequence for this arc: **the isolated cascor leg cannot be kept alive while the campaign runs**, and
189 matrix rows remain, most of which need it. This is a coordination/tooling blocker, not a canopy defect
— escalated to the session owner rather than worked around, because every available workaround either
deviates from the byte-matched launch recipe the E2E evidence depends on, or edits a shared tool another
running session is actively using.

#### Remedy adopted (owner-selected): supervise the leg under a live parent

`util/ad-hoc/e2e_cascor_leg_supervise.bash` (new) launches the cascor leg as a **direct child of a resident
supervisor** instead of via `( … nohup … & )`. It targets the reaper's *orphan* predicate only — the
uvicorn argv, the §6.1 env set, the port, the CWD, and the log destination stay byte-identical to
`cascor_up` / `e2e_cascor_leg_restart.bash`, so nothing the E2E evidence observes about canopy↔cascor
behaviour changes. The supervisor's own argv (`bash util/ad-hoc/e2e_cascor_leg_supervise.bash`) does not
match the `JuniperC[a-z0-9]+` candidate gate, so the supervisor is never itself a reap candidate and the
child can never re-classify to orphan.

**Verified with the reaper itself** — `util/reap_pytest_orphans.bash --dry-run --verbose` against the
running supervised stack:

```text
KEEP       pid=437062 ppid=437053 (live parent) cmd=…/JuniperCascor1/bin/python3.13 …/uvicorn api.app:create_app --
WOULD REAP pid=3695742 ppid=25920 cmd=…/JuniperCascor1/bin/python3.13 -c … multiprocessing.forkserver …
…
Dry-run summary: 5 would be reaped, 4 kept (live parent), 0 skipped.
```

The E2E leg is classified **KEEP (live parent)** by the very tool that killed it three times, while the
stale campaign forkserver orphans are still correctly flagged for reaping. The F-ML-001 dry-run/live delta
caveat (children of reaped orphans re-classify mid-pass) does not reach this leg: its parent is not a
candidate in any pass.

Two limits worth stating plainly:

- This defends against the **orphan reaper only**. A blanket killer (`kill_all_pythons.bash` and friends)
  kills regardless of parentage and would still take the leg down.
- cascor's own multiprocessing **forkserver children** remain orphan-classified candidates. Reaping those
  does not kill the service (its parent is the supervisor) but can disrupt an in-flight training run — so a
  reap during a live W1/W2 run is still not safe.

Auto-restart is deliberately **opt-in** (`--restart`, default off) so a genuine cascor crash stays visible
instead of being silently papered over mid-run; every child exit is timestamped to
`${LOG_DIR}/juniper-cascor-supervisor.log` either way, so a row verdict can always be checked against
whether the backend restarted underneath it.

F-6 note: because uvicorn is a *direct* child here, `$!` genuinely is the server pid, so the pidfile this
script writes is honest — unlike the subshell form, where `$!` is the subshell.

---

## Phase 1 — segment 6 (2026-08-12): W5 steps 7-10

### Stack state on entry — the supervision remedy held

All four legs healthy on arrival; **the cascor leg had been up 10.6 h uninterrupted** under
`util/ad-hoc/e2e_cascor_leg_supervise.bash` (supervisor pid 437053, child pid 437062, started
`2026-08-12 09:44:52-0500`). `${LOG_DIR}/juniper-cascor-supervisor.log` records **zero child exits** across
the whole segment, so every verdict below is a genuine canopy verdict rather than an environmental
artifact — the exact confound that made W5-07 inconclusive in segment 5. `reap_pytest_orphans.bash
--dry-run` still reports `KEEP pid=437062 ppid=437053 (live parent)`. The F-ML-001 remedy is holding.

Restore precondition was as segment 5 left it: cascor network **empty** (`GET :8202/v1/network` →
`"No network created"`), snapshot `snapshot_20260811T010849Z` intact on disk (296701 bytes). Clean
restore-into-empty.

### W5-07 — RE-RUN: PASS (was INCONCLUSIVE)

Driven as one `page.evaluate` gesture per the segment-5 technique (CDP round-trips are far too slow for
F-CANOPY-010's ~3.6 s modal window). Timings from inside the page: restore op-btn clicked `t=9 ms`,
confirm button visible `t=1837 ms`, **restore-confirm clicked `t=1844 ms`** (comfortably inside the decay
window), status settled `t=4282 ms`.

- **UI**: `#hdf5-snapshots-panel-restore-status` → `✅ Restored from snapshot 'snapshot_20260811T010849Z'`.
- **Modal body** (re-confirming W5-05): `Confirm Restore of snapshot: snapshot_20260811T010849Z / Load this
  snapshot for inspection and modification. Training is NOT started — invoke Retrain or Resume to begin a
  training run. / ⚠️ Training must be paused or stopped before any snaps…`
- **Wire** (server-side, per the §methodology note — the browser log carries only
  `_dash-update-component`; a filtered capture of 1978 requests contained **zero** `/api/v1/snapshots`
  entries, confirming the call is canopy→cascor): cascor log shows
  `POST /v1/snapshots/snapshot_20260811T010849Z/restore HTTP/1.1" 200 OK` and
  `api.lifecycle.manager - INFO - Snapshot restored: snapshot_20260811T010849Z (FSM=Investigating)`
  at `2026-08-12 20:24:03,610`.
- **Backend truth** (the half that was missing): `GET :8202/v1/network` → `input_size:2, output_size:2,
  hidden_units:10, max_hidden_units:10, uuid d5827628-4843-4910-a9ba-aec16f0de3ee`;
  `/v1/network/topology` returns all 10 units with the correct CasCor cascade fan-in (unit 0 → 2 weights,
  unit 1 → 3, unit 2 → 4, …). Empty → 10 units, correlated to the click, on a leg proven not to have
  restarted.

The segment-5 honest-label note stands and is now sharper: canopy's failure copy was faithful to a dead
backend, and its success copy is faithful to a live one — but **neither carries a diagnostic
distinguishing the two**, which is precisely why the row needed a supervised leg to adjudicate.

### W5-08 — PASS

`GET :8051/api/status` → `fsm_status = 'INVESTIGATING'`, corroborated at the source by cascor's
`/v1/training/status` → `state_machine.status = "INVESTIGATING"`, `phase = "IDLE"`. Restore did **not**
start training (`training_state.status "Stopped"`, `is_training false`) — matching the modal's own copy.

### W5-09 — FAIL (F-CANOPY-011)

Expected: idle block hides, active block shows, `#network-editor-panel-idle-fsm-badge` reads
`FSM: Investigating`. Observed, **stable across 6 samples spanning 12.5 s** (not a transient):

| element | expected | observed |
|---|---|---|
| `#network-editor-panel-idle-fsm-badge` | `FSM: Investigating` | `FSM: Unknown` |
| `#network-editor-panel-idle` | hidden | `display: block` (visible) |
| `#network-editor-panel-active` | shown | `display: none` (hidden) |

The panel never leaves its idle state, so the entire active editing surface — add-unit, remove-unit,
patch-weights — is unreachable through the UI while the FSM is genuinely `INVESTIGATING`.

### W5-10 — PASS (expected divergence D-0), but the cause is now known to be doubled

`#network-editor-panel-topology-readout` → `No topology loaded.` and `#network-editor-panel-remove-idx`
options `[""]` (empty) — exactly the matrix's "expected today" text, so the row passes as written.

The new information is *why*. There are **two stacked defects**, and the first masks the second:

1. **F-CANOPY-011** short-circuits at `network_editor_panel.py:505` before the topology fetch is ever
   attempted, returning `topology-store = None` → `render_topology` renders the placeholder.
2. **D-0** — the fetch at `:517` targets `/api/network/topology`, which is **404** (verified live); the
   working route is `/api/topology` (**200**, serving `input_units:2, output_units:2, hidden_units:10`,
   14 nodes, 89 connections).

**Operational consequence: fixing D-0's route alone will NOT revive the Network Editor.** Both the FSM key
and the route must be corrected, or the panel stays idle and the readout stays on the placeholder.

### Findings opened in segment 6

**F-CANOPY-011 — the Network Editor reads the FSM from a key shape canopy's `/api/status` never returns,
so the panel is permanently inert (P1, OPEN; root-caused, deterministic).**
`network_editor_panel.py:400-412` (`_is_investigating`) and the badge line `:501` both read
`status["state_machine"]["status"]`, falling back to a top-level `status["status"]`. Canopy's `/api/status`
returns **neither**: it is a flat dict whose FSM field is `fsm_status`. Verified live against the running
service — `'state_machine' in payload → False`, `'status' in payload → False`,
`payload['fsm_status'] → 'INVESTIGATING'`. `state_machine` is *cascor's* `/v1/training/status` schema, not
canopy's; the panel was written against the upstream shape but points at the canopy proxy. The docstring at
`:403-406` asserts the wrong contract in prose ("nests the FSM summary under `state_machine`"), which is
why it reads as correct on inspection. Consequently `_is_investigating` returns `False` unconditionally,
`:505` always takes the not-investigating branch (`idle: block`, `active: none`), and `:501` renders
`"Unknown".title()` → `FSM: Unknown`. This is a complete feature blackout of a shipped panel, independent
of actual FSM state, and it masks D-0 (`:517` → `/api/network/topology`, 404; the live route is
`/api/topology`). Blast radius: W5-09 FAIL; W5-12/13/14 have **no UI path** and must be driven at the API
to prove the routes; M-NETWORK-EDITOR rows that assert the active surface. Fix is two contract
corrections (read `fsm_status`; fetch `/api/topology`) plus a test that pins the panel against a real
`/api/status` payload rather than a hand-built one.

**F-CASCOR-002 — snapshot restore ALWAYS drops optimizer state: `learning_rate` is written as a string and
read back undecoded, so the Adam constructor raises and the optimizer is silently set to `None` (P2, cascor
repo, OPEN; root-caused and reproduced).**
Save/load asymmetry in `src/snapshots/snapshot_serializer.py`. `:448` writes
`write_str_attr(opt_group, "learning_rate", network.learning_rate)` — a **string** attribute. `:1037` reads
it back with a raw `opt_group.attrs.get("learning_rate", …)` — **no decode** — while its sibling one line
up (`:1036`, `optimizer_type`, written by the same `write_str_attr`) *is* decoded via `read_str_attr`.
Direct probe of the live artifact confirms the on-disk types: `params/output_layer/optimizer` attrs are
`learning_rate = np.bytes_(b'0.1')`, `optimizer_type = np.bytes_(b'Adam')`. The undecoded value flows to
`:1050` `optim.Adam(output_layer.parameters(), lr=learning_rate)`, where torch's range check
(`0.0 <= lr`) raises — reproduced verbatim in the JuniperCascor1 env:
`TypeError: '<=' not supported between instances of 'float' and 'numpy.bytes_'`. `:1026-1028` catches it,
logs `Could not restore optimizer: …` at **WARNING**, and sets `network.output_optimizer = None`. This is
deterministic, not intermittent: every restore of every snapshot loses optimizer state. Observed live in
this segment's restore. The codebase is internally inconsistent about the same field — `:336` writes
`config_group.attrs["learning_rate"]` as a native float. Severity is P2 because the weights restore
correctly and the network is usable for inspection; the **consequence for resume/retrain (W5-27) is
verified at that row**, since `output_optimizer = None` may either be lazily rebuilt or fault. Surface
honesty gap: canopy reports an unqualified `✅ Restored` while the backend has degraded the restore, and
the warning exists only in the cascor log. **Scope widened later in the segment:** the same warning fires
on the **replay** load path too (cascor log, `20:45:31` and `20:51:19`, both `POST …/replay` starts), so
this is not restore-specific — it is every snapshot load path that reaches
`_load_optimizer_state_from_hdf5_helper`.

### Observations (segment 6, non-finding)

- **`/api/status.hidden_units` is stale after a restore.** For the same restored network, canopy's
  `/api/status` reports `hidden_units: 0` while `/api/topology` reports `10` and cascor's `/v1/network`
  reports `10`. The source is cascor's `/v1/training/status` **`monitor`** block
  (`monitor.current_hidden_units: 0`) — training telemetry, which is legitimately zero because no training
  has run since the restore. Recorded as a finding-*candidate* rather than a finding: no consumer has yet
  been shown to render network size from this field. Any that does would show a restored 10-unit network
  as empty. `input_size`/`output_size` on the same payload are correct (2/2).
- **Topology tab reads 0/0/0 for the restored network** (`#network-visualizer-{input,hidden,output}-count`)
  while `/api/topology` serves 2/10/2. This **corroborates F-CANOPY-006** (counts stay at the layout-default
  `"0"`s and the DOM never updates) rather than being new, and it is *not* attributable to the stale
  `/api/status.hidden_units` above — under F-CANOPY-006 those counts never update from any source.
- **Step-11 inputs resolved.** `I = 2`, `H = 10` taken from `/api/topology` (the topology DOM being dead
  per F-CANOPY-006), confirming the handoff's pre-computed **append weight-vector length of `I + H` = 12
  floats** for W5-13.

### W5 steps 11-15 — the editor works; only its gate is broken

**The load-bearing result of this segment.** Every Network Editor control is `present: true,
disabled: false, visible: false` — enabled, in the DOM, inside the block F-CANOPY-011 keeps hidden.
Driving them by raw JS (which Dash honours regardless of CSS visibility) exercised the full callback →
canopy route → adapter → cascor path **successfully**, including two real mutations that landed in cascor.

**Therefore F-CANOPY-011 is a visibility/gating defect ONLY.** The editor's callbacks, canopy's three
proxy routes, and cascor's validation are all sound. This bounds the fix to the two contract corrections
and is why F-CANOPY-011 is filed P1-unreachable rather than P0-broken.

Control types (relevant because the T-7 numeric wall does *not* obstruct this panel): `patch-values` and
`add-weights` are `<textarea>`; `patch-target`, `add-activation`, `remove-idx` are `<select>`; only
`patch-idx` and `add-bias` are `input[type=number]`, and both ship at usable defaults (`0` / `Tanh`), so
no numeric field had to be driven.

| step | verdict | evidence |
|---|---|---|
| W5-11 | PASS | `I=2`, `H=10` from `/api/topology`; `output_weights` is 12 × 2, cascade fan-in 2,3,4,…,11 |
| W5-12 | PASS (both arms) | shape violation rejected **without mutating**; valid 1-D patch landed |
| W5-13 | PASS (after cap reorder) | cap-refused at H=10; appended after the step-15 delete |
| W5-14 | PASS | count 9 → 10, verified at the API (DOM oracle dead per F-CANOPY-006) |
| W5-15 | PASS | `DELETE …/hidden-units/9` → 200; UI path blocked, twice over |

**W5-12 — negative arm (the matrix's explicit requirement).** Target `output_weights`, 24 flat floats
(`0.01 … 0.24`, row-major for the 12 × 2 shape) →
`Patch failed: patch_weights failed: shape mismatch: output_weights expects (12, 2), got (24,)`.
Re-reading `/v1/network/topology` immediately after shows `output_weights` **byte-identical** to the
pre-state (`[[0.08172,-0.08172],[0.32116,-0.32093],[0.64142,-0.64161]]`) — the matrix's "must be rejected
without mutating state" is satisfied, and the error text is precise and actionable.

**W5-12 — positive arm.** Target `output_bias`, values `0.25, -0.25` → `Patched output.bias (2 values).`;
`/v1/network/topology` then reports `output_bias = [0.25, -0.25]`. The write path is proven end-to-end.

**W5-13 — as specified, then reordered.** With H=10 the append was refused:
`Add failed: add_hidden_unit failed: network is at max_hidden_units cap (10)` — an honest business-rule
refusal (the restored snapshot is a fully-grown network at `max_hidden_units: 10`), not a defect; state
unmutated. The success path therefore required freeing a slot, so **step 15 was executed before step 13**
and the append vector recomputed at the new H: `I + H = 2 + 9 = 11` floats. Result:
`hidden_units 9 → 10`, tail unit id 9 carrying **exactly** the sent ramp
`[0.31,0.32,…,0.41]` (11 weights), `bias 0.0`, `activation Tanh` — the shipped defaults, uncoerced.

**W5-15 — route proven, UI path blocked twice.** `DELETE :8051/api/v1/network/hidden-units/9` (canopy's
proxy, `main.py:2745-2755`) → **HTTP 200**, body `removed_index: 9`, `num_hidden_units: 9`,
`fsm_state: "INVESTIGATING"`; count 10 → 9. The UI path is unreachable for **two independent reasons**:
`#network-editor-panel-remove-idx` has options `[""]` (D-0 — the topology that would populate it never
loads) *and* the whole active block is hidden (F-CANOPY-011).

Final network state left for the replay rows: `input 2 / hidden 10 / output 2`, `output_bias [0.25,-0.25]`,
tail unit = the synthetic ramp. The snapshot `.h5` on disk is **untouched** by all of this, so W5-16/27
still replay and resume from the pristine artifact.

### Findings opened in segment 6 (continued)

**F-CANOPY-012 — `output_weights`, the Network Editor's DEFAULT patch target, is structurally impossible
to patch from the UI: the panel parses a flat 1-D list while the route requires 2-D (P2, OPEN;
root-caused).**
`_parse_float_list` (`network_editor_panel.py:415-431`) returns a **flat** `List[float]`, and
`on_patch_weights` (`:721-760`) forwards it verbatim as `body["values"]` — there is **no reshape anywhere**
in the callback, and none is possible today because the topology needed to infer the shape is exactly what
D-0/F-CANOPY-011 withhold. cascor requires `output_weights` as `(I+H, output_size)` = `(12, 2)`, so any
input a user can type is rejected: `shape mismatch: output_weights expects (12, 2), got (24,)`. Of the
four dropdown options, only this one is 2-D — `output_bias` (1-D), `hidden_unit_weights` (1-D per unit),
and `hidden_unit_bias` (scalar) all round-trip fine, and `output_bias` was proven to land live. The broken
option is the dropdown's **first and default** value, so it is the first thing any operator tries.
Mitigating: the failure is loud, precise, and non-mutating. Fix options are a 2-D-aware parse (accept
nested `[[…],[…]]`) or a reshape using `(I+H, output_size)` once the topology is available — which makes
this dependent on the D-0 route fix.

**F-CANOPY-013 — Network Editor success messages read payload keys off the response ENVELOPE, so a
successful append reports `index None (now None hidden units)` (P3, OPEN; root-caused, one latent second
instance).**
`_post_json` (`:433-465`) returns `{"success": True, "data": resp.json()}` — i.e. `result["data"]` is the
**entire** cascor envelope `{"status":…, "data": {…}, "meta":…}`, as confirmed live by the DELETE response
body. But `on_add_unit` (`:608-611`) does `data = result["data"]; idx = data.get("unit_index"); total =
data.get("num_hidden_units")`, reading both keys off the envelope root where they do not exist; they live
one level deeper at `result["data"]["data"]`. Both resolve to `None`, producing the observed
`Appended unit at index None (now None hidden units).` on an append that in fact **fully succeeded**. The
key *names* are correct — cascor documents the add payload as carrying `unit_index`, `num_hidden_units`,
`operation` (`juniper-cascor src/api/routes/network.py:135`) — so this is purely a nesting-level error,
fixable in one line. Cosmetic only (no state is harmed, and the operation itself is correct), but it
degrades the one surface an operator has for confirming a blind mutation, and it does so on the *success*
path where nobody is looking for a bug. **Second, latent instance:** `on_remove_unit` (`:705-707`) repeats
the pattern verbatim and would render `Removed unit N (now None hidden units).` — unreachable today only
because the remove dropdown is empty, so it will surface the moment F-CANOPY-011 and D-0 are fixed. Fix
both call sites together.

### W5 steps 16-26 — replay starts perfectly, then cannot be controlled at all

**W5-16 PASS.** Replay op → modal body `Confirm Replay of snapshot: snapshot_20260811T010849Z / Start a
read-only playback session of this snapshot's training history. Use the replay player controls to scrub
through metric and topology evolution. / ⚠️ Training must b…` → confirm → **the active tab auto-switched
to `Replay`** (t=6125 ms) and the panel reported `✅ Snapshot replay started`. Both halves of the
expectation met.

**W5-17 PASS.** `#replay-player-panel-idle` is `display: none` (placeholder gone),
`#replay-player-panel-active` is `display: block`, `#replay-player-panel-snapshot-id` =
`snapshot_20260811T010849Z`, `#replay-player-panel-fsm-badge` = `REPLAYING`. All three halves met.

**W5-18 FAIL (F-CANOPY-015).** `#replay-player-panel-weights-badge` renders **`V1 (metrics only)`** in the
grey style. The snapshot is provably **V2 with weight history**: the artifact's own root attrs are
`format_version = b'2'`, `serializer_version = b'2.0.0'`, and `history/weights/` holds `output_weights`
and `output_bias` (3 samples each) plus `hidden_units` and `sample_indices`; cascor's own replay-start
response reports `session.weights_available = True` with
`weight_sampling {strategy: adaptive, interval: 50, num_samples: 3}`. The badge is reporting the opposite
of the truth, which per the matrix is the row's entire purpose ("Record which").

**W5-19 FAIL / W5-26 FAIL / W5-21, W5-22, W5-23 BLOCKED (all F-CANOPY-014).** Clicking
`#replay-player-panel-play-btn` (visible, enabled) leaves the status block on
`❌ Invalid URL '/api/v1/snapshots/snapshot_20260811T010849Z/replay/control': No scheme supplied. Perhaps
you meant https:///api/v1/…` and `#replay-player-panel-epoch-readout` frozen at `0 / 12` — playback never
advances. `#replay-player-panel-stop-btn` produces the **identical** error, proving the failure is
**action-independent**: every control action funnels through the one malformed URL at
`replay_player_panel.py:356`. The slider rows (seek / speed / range) are therefore recorded BLOCKED rather
than driven — the submit path is provably dead for every action, so dragging them could only re-observe
the same error.
**Backend exonerated on the wire**: a direct `POST :8051/api/v1/snapshots/{id}/replay/control
{"action":"play"}` returns **HTTP 200** with a full result block (`length: 12, time_index: 0, speed: 1.0,
paused: false, range {0,12}, weights_available: true`). canopy's route and cascor are both healthy; only
the panel's URL construction is broken.

**W5-20, W5-24, W5-25 BLOCKED (consequential).** The V2 last-sample drain, the Evolution weight-norms
un-hide, and the Decision-Boundary redraw all require playback to advance, which F-CANOPY-014 prevents.
W5-20 is doubly blocked — the panel also believes the session is V1 (F-CANOPY-015).

### Findings opened in segment 6 (continued)

**F-CANOPY-014 — the replay player builds every control URL with an EMPTY base, so the entire replay
control surface is dead: play / pause / seek / speed / range / stop all fail with `No scheme supplied`
(P1, OPEN; root-caused, backend exonerated).**
`replay_player_panel.py:80` initialises `self._api_base_url = config.get("api_base_url", "")` — an
**empty-string** fallback. The runtime config does not supply `api_base_url`, so the base is `""` and
`:356` builds `f"{self._api_base_url}/api/v1/snapshots/{snapshot_id}/replay/control"` =
`"/api/v1/snapshots/…/replay/control"`, a schemeless relative path. `requests` rejects it verbatim:
`Invalid URL …: No scheme supplied.` The panel surfaces this honestly in its status block, but every
control is inert. A three-way comparison across the sibling panels isolates the defect precisely — this is
the **only** one of the three with an empty fallback:

| panel | line | base-URL expression | outcome |
|---|---|---|---|
| `hdf5_snapshots_panel.py` | `:79` | `f"http://127.0.0.1:{_settings.server.port}"` (unconditional) | works — create/restore/replay all landed |
| `network_editor_panel.py` | `:99` | `config.get("api_base_url", f"http://127.0.0.1:{_settings.server.port}")` | works — patch/add/delete all landed |
| `replay_player_panel.py` | `:80` | `config.get("api_base_url", "")` | **broken** |

Blast radius: W5-19/26 FAIL and W5-20/21/22/23/24/25 BLOCKED — the whole M-REPLAY control surface. Fix is
one line (adopt either sibling's fallback); the deeper question of why the config omits `api_base_url` is
worth answering so the two working panels aren't relying on defaults either.

**F-CANOPY-015 — the replay player reads three session fields one nesting level too shallow; the weights
badge therefore reports V1 for a V2 snapshot while two sibling misreads are silently masked by
coincidence (P2, OPEN; root-caused, empirically confirmed).**
cascor's replay-start payload nests the live session summary under a `session` key. Measured directly off
the running service, the `data` block's keys are
`['fsm_state', 'operation', 'session', 'snapshot_id', 'status', 'time_index', 'training_params']` while
`data.session` carries `['length', 'paused', 'range', 'snapshot_id', 'speed', 'time_index',
'weight_sampling', 'weights_available']`. canopy's `confirm_snapshot_op`
(`hdf5_snapshots_panel.py:1281-1287`) stores the **data block** as the session store — correct as far as it
goes — but `replay_player_panel.py:468-471` then reads `range`, `speed`, and `weights_available` off that
block's top level, where **none of the three exist**. The panel is inconsistent with itself: its own
`_session_window` (`:383-397`) and the `fsm_state` read (`:470`) *are* written against the unified
data-block shape and work correctly, which is why the epoch readout and FSM badge are right.
Observed consequences, exactly as the shapes predict:

| read | line | actual value | rendered | masked? |
|---|---|---|---|---|
| `weights_available` | `:471` | `True` (nested) | `V1 (metrics only)` | **no — visibly wrong** |
| `speed` | `:469` | `1.0` (nested) | `1×` via `SPEED_DEFAULT` | yes, by coincidence |
| `range` | `:468` | `{0, 12}` (nested) | `[0, 12]` via `[start, end]` | yes, by coincidence |

The two masked reads are latent: they render correctly **only** while the real session values happen to
equal the fallbacks, so a resumed session at a non-default speed or a user-narrowed range would display
stale defaults with no error. Same defect class as F-CANOPY-013 (a payload key read one level too
shallow), different file and different pair of keys — worth fixing as one sweep with a helper that
unwraps `session.session` once.

### W5 steps 27-29 — the tail rows

**W5-27 PASS — both operations 200 in the LIVE lane.** The row asks for "200 vs 409 vs 501 for each":

| op | code | resulting FSM | notes |
|---|---|---|---|
| `POST …/{id}/resume` | **200** | `RESUME_READY` | prepares a resume point; does **not** start training. `time_index.default = "end"`, window `{0, 12}` |
| `POST …/{id}/retrain` | **200** | `STOPPED` | resets to a fresh-run-ready state, window reset to `{0, 0}` |

Both were driven at the API after the UI modal gesture failed to open twice under page congestion (see the
methodology note below); the surrounding modal machinery is already proven by W5-05 and W5-16. The **409**
arm was not induced — it requires an active training run, which is out of this row's scope and would have
left the stack mid-run against the W5 cleanup contract. The **501** arm belongs to the DEMO-lane row
W5-30, not here. Both ops are recorded by the backend history surface, which is how W5-28 cross-validates.

**W5-28 PASS.** `#hdf5-snapshots-panel-history-toggle` flipped
`#hdf5-snapshots-panel-history-collapse` from `visible:false / .collapse` to `visible:true / .collapsing`,
and `#…-history-content` went from its `Loading history…` placeholder to real entries within 3.2 s:
`• RETRAIN snapshot_20260811T010849Z 2026-08-13 01:57:41 … • RESUME … 01:57:32 … • REPLAY_STOPPED …
01:54:41 …`. A satisfying cross-check: the history faithfully lists exactly the operations this segment
drove, in order. `GET /api/v1/snapshots/history` independently returns 200 with the same records.

**W5-29 PASS (dead-expected, proven statically).** Stronger than the row asks. The two ids
`{"type": "hdf5-snapshots-panel-swap-restore-pre-btn"…}` / `…-post-btn` occur in the entire panel **only**
at their construction sites (`hdf5_snapshots_panel.py:709` and `:720`) — there is **no `Input(...)`
anywhere referencing either**, so no callback can fire and the buttons are inert *by construction*, not
merely inert-on-the-day. Live confirmation: this session renders **zero** such buttons
(`swapBtnCount: 0`) because there are no dataset-swap events to build paired-diff cards from
(`#hdf5-snapshots-panel-dataset-swaps-content` is present but empty). The row's expectation — nothing
happens, no request, no console error — therefore holds vacuously and provably. Not click-driven: there
was nothing to click, and manufacturing a swap event to reach a button already proven callback-less would
add no evidence.

### Methodology notes (segment 6)

- **A click issued within ~10 ms of a tab render is silently lost.** The first W5-16 attempt clicked the
  replay op 7 ms after the Snapshots tab rendered and nothing happened — Dash had not yet wired the
  freshly-rebuilt pattern-matched Input. A **1.5-2 s settle before clicking** made it reliable. This is
  distinct from F-CANOPY-010 (which closes an *already-open* modal) and worth carrying forward: a lost
  click looks exactly like a broken control.
- **The confirm modal's DOM does not exist while closed.** `[id*="modal"]` returns `[]` on a settled
  Snapshots tab; the modal and its confirm button enter the DOM only on open. So "confirm button absent"
  is the normal closed state, not evidence of a defect — poll for the element to *appear*.
- **Page congestion is real and measurable.** Two `page.evaluate` gestures with ~43 s internal budgets
  exceeded 120 s of wall clock while the same operations succeeded instantly at the API. This is
  F-CANOPY-004 territory and it makes long in-page polling loops an unreliable instrument; where a row's
  assertion is about the *backend outcome* rather than the *UI gesture*, driving the API is both faster
  and more trustworthy.
- **Supervisor log clean for the whole segment.** `${LOG_DIR}/juniper-cascor-supervisor.log` still shows
  only the single `09:44:52` start and the `09:44:56` healthy line — **zero child exits** across every row
  above, so no verdict in this segment can be an environmental artifact.

---

## Phase 1 — segment 7 (2026-08-13): the Network Editor tab, 18/18

Branch `arc/canopy-e2e-phase1-seg7`, cut from the pushed seg6 tip `3562bff`; the seg6 worktree
`encapsulated-prancing-sun` is locked by another session, so this segment follows the arc's
one-worktree-per-segment pattern for the third time. Run id unchanged: `20260811T010700Z`.

### Stack state on entry

`data 8101 / cascor 8202 / canopy 8051` all `200`; cascor at **10/10** hidden units; 1 snapshot;
supervisor log still showing only the `09:44:52` start and `09:44:56` healthy lines — **zero child
exits**, now across two segments and ~19 h of uptime. The F-ML-001 supervision remedy continues to hold,
so nothing below is environmental.

### The headline: F-CANOPY-011 is now proven live, not inferred

Segment 6 established the defect by reading the code. This segment put it in front of the panel and
watched it fail, which is a materially stronger claim.

`POST /api/v1/snapshots/snapshot_20260811T010849Z/restore` → `200`, and canopy's **own** `/api/status`
then reported:

```json
{"fsm_status": "INVESTIGATING", "phase": "idle", "state_machine": null, ...}
```

That is the exact state the editor exists to unlock in. After waiting 5 s — more than two of the panel's
own 2 s poll cycles, so staleness is excluded — the panel was **unchanged**:

| element | observed | expected if the gate worked |
|---|---|---|
| `-idle` | `display:block`, `offsetParent` set | hidden |
| `-active` | `display:none`, `offsetParent` null | **visible** |
| `-idle-fsm-badge` | `FSM: Unknown` | `FSM: Investigating` |
| `-topology-readout` | `No topology loaded.` | the live topology |

The mechanism is visible in that JSON: `state_machine` is literally `null` and the field is `fsm_status`,
so `_is_investigating` (`:410-412`) evaluates `("" or "").upper() == "INVESTIGATING"` → `False`
**unconditionally**, and the badge falls all the way to its last-resort `Unknown`.

### The correction: the gate's *intent* is right — cascor enforces the same precondition

This is the segment's most consequential finding, and it revises segment 6's framing. Driving the append
and remove submits while the FSM was `STOPPED` produced, from **cascor**, not canopy:

```text
Add failed:    add_hidden_unit failed:    add_hidden_unit_manual requires INVESTIGATING state (currently STOPPED)
Remove failed: remove_hidden_unit failed: remove_hidden_unit_manual requires INVESTIGATING state (currently STOPPED)
```

So the editor is **not** gated for no reason: manual structural edits have a real backend precondition,
and canopy's gate is a faithful mirror of it that happens to read the wrong key. Segment 6 saw only the
two `PATCH` mutations land — and `PATCH` is genuinely permitted in `STOPPED`, which is why the gate looked
gratuitous from that evidence alone.

The practical consequence for the fix: **do not remove the gate**, correct it
(`state_machine.status` → `fsm_status`). And the corrected gate does work — with the FSM actually at
`INVESTIGATING`, the same two ops succeeded end-to-end (`hidden_units` 10 → 9 → 10, tail unit carrying the
sent 11-weight vector, `bias 0.25`, `activation Sigmoid`, all read back from cascor).

### F-CANOPY-013 is no longer latent — it is observed on successful operations

Both success messages were captured on ops that **fully succeeded** at the backend:

```text
Snapshot taken; Removed unit 9 (now None hidden units).      [alert-success]
Appended unit at index None (now None hidden units).         [alert-success]
```

`_post_json` (`:458`) returns the whole `{status, data, meta}` envelope as `result["data"]`, so `:609-610`
and the remove callback read `unit_index` / `num_hidden_units` off the **envelope root** and get `None`.
The patch path is *spared* — its messages count request-side values via `len(values)` — which usefully
bounds the fix to callbacks that read a response.

### F-CANOPY-012 confirmed and sharpened — a naive reshape would still be wrong

```text
Patch failed: patch_weights failed: shape mismatch: output_weights expects (12, 2), got (24,)
```

The panel sends flat `(24,)`; cascor wants 2-D. But the required shape is
`(n_in + n_hidden, n_out) = (12, 2)` — **not** `(n_out, n_in + n_hidden) = (2, 12)` — while the field's own
placeholder instructs the user to type "CSV **row-major**". A reshape that trusts the placeholder would
produce a transposed weight matrix that *passes* the shape check and silently corrupts the network. The
fix must reshape to `(12, 2)` and the placeholder must be corrected in the same change.

### F-CASCOR-002 UPGRADE — the loss is physical, self-propagating, and reproducible on demand

Segment 6 proved the `TypeError` and the swallowed WARNING. Segment 7 found what that costs on disk.
Re-snapshotting a network that was itself restored from a snapshot yields an artifact with the optimizer
group **entirely absent** — verified with `util/ad-hoc/e2e_snapshot_h5_compare.py` (added this segment):

| snapshot | provenance | nodes | optimizer nodes |
|---|---|---|---|
| `snapshot_20260811T010849Z.h5` (296,701 B) | original training | 191 | **2** — `params/output_layer/optimizer[/state_dict]` |
| `snapshot_20260813T043121Z.h5` (285,187 B) | taken after an earlier restore | 185 | **0 — ABSENT** |
| `snapshot_20260813T043711Z.h5` (295,308 B) | taken after a *fresh* restore | 189 | **0 — ABSENT** |

The third row is a deliberate control: an independent restore→save cycle, run minutes after the second,
reproducing the loss exactly. And the smoking gun sits in the pristine file where the finding said it
would:

```text
params/output_layer/optimizer.attrs['learning_rate'] = np.bytes_(b'0.1')   (python type bytes_)
config.attrs['learning_rate']                        = np.float64(0.1)     (python type float64)
```

— the same attribute written as a **string** in one place and a float in the other, which is precisely the
`np.bytes_` that trips torch's range check at `:1037`.

This warrants a **severity upgrade, P2 → P1**. The original finding describes a load-time warning; what is
actually happening is that one restore→save cycle **permanently destroys the optimizer state in the
artifact lineage**. A consumer of the second-generation snapshot cannot even encounter the bug — there is
nothing left to fail on — so training resumed from it silently restarts the optimizer from scratch, with
no warning at all. The failure is loudest at its least harmful moment and silent thereafter.

### Row-by-row results (all 18)

`M-NETWORK-EDITOR-05` was already recorded in segment 6 (D-0 re-confirmed); the other 17 are new.
Full per-row detail is in `reports/e2e/20260811T010700Z/statuses.tsv` — the summary:

| verdict | rows |
|---|---|
| **PASS** | 01, 02, 05, 06, 07, 08, 10, 12, 14, 15, 16, 18 |
| **PASS**, reachable only by injection | 11 |
| **PASS** on path/effect, **FAIL** on status message (F-CANOPY-013) | 09, 13 |
| **PASS** on 2 of 4 targets, **FAIL** on the default (F-CANOPY-012) | 17 |
| **FAIL** (F-CANOPY-011) | 03, 04 |

Three rows earned more than a bare verdict:

- **M-NETWORK-EDITOR-01** — `dcc.Interval` renders **no DOM node**, and canopy's log is application-level
  with no access lines, so neither the usual DOM nor log oracle applies. Verified instead by instrumenting
  `window.fetch` and timing the Dash callback POSTs carrying the `fsm-poll` input: **6 fires in 11 s,
  median inter-arrival 1957 ms** against the 2000 ms nominal. The 1045–3025 ms spread is congestion, not
  drift — the same window carried **140** other Dash callbacks, which is the hardest number this arc has
  yet put on F-CANOPY-004.
- **M-NETWORK-EDITOR-11** — the validation arm needs no trickery and is the more useful evidence: clicking
  Delete with an empty index returns `Pick a unit to delete.` and correctly does **not** open the modal,
  proving the callback is wired and fires from a `display:none` control. Reaching the modal itself
  required injecting the `<option value="9">` that D-0 prevents from ever existing.
- **M-NETWORK-EDITOR-13** — the `STOPPED` arm proves the *ordering* independently of the outcome: the
  snapshot-first `POST` succeeded (count 1 → 2) and only then was the `DELETE` refused. Had the order been
  reversed or the snapshot skipped, the counts could not look like that.

### Observations (segment 7, non-finding)

- **The snapshot-first pre-step is not transactional.** A refused `DELETE` leaves its safety snapshot
  behind (count 1 → 2 with the network untouched at 10 units). Defensible — a pre-op snapshot is a safety
  artifact and keeping it costs only disk — but undocumented, and repeated failed attempts accumulate
  orphans.
- **The T-7 numeric wall is narrower than recorded.** `-add-bias` and `-patch-idx` are both
  `type="number"`, yet both were driven successfully with a native-setter + `input`/`change` gesture, and
  the values reached cascor (`bias 0.25` on the appended unit; `[0.11, 0.22]` on unit 0). T-7 is a
  Playwright `fill()` limitation, **not** a DOM one — so `AUTO` via raw JS is sufficient where the matrix
  currently prescribes `AUTO-API`.
- **The remove picker has two independent reasons to stay empty**, so fixing either alone is insufficient:
  the gate returns before the topology fetch is ever reached (`:505`), *and* that fetch targets the 404
  route `/api/network/topology` (D-0).

### The Replay tab, 17/17

A replay session was started **through the UI** (Snapshots → `▶️ Replay` → Confirm) on the pristine
`snapshot_20260811T010849Z`. That detail matters: a session started by direct API call does **not** light
the panel up, because `replay-player-session` is written by the *snapshots* panel after its own POST — the
player is store-driven, not backend-polled. The panel went active 4643 ms after Confirm and the tab
**auto-switched to Replay**, corroborating segment 6.

**The whole transport surface is dead, and now provably all of it.** Segment 6 established
action-independence from play + stop. This segment drove all six controls:

| control | driven how | dispatched? | result |
|---|---|---|---|
| `-play-btn` / `-pause-btn` / `-stop-btn` | `.click()` | yes | **byte-identical** `No scheme supplied` |
| `-scrubber` | trusted `ArrowRight` | 2 callbacks | same error; handle 6 → 7 |
| `-speed` | trusted `ArrowRight` | 2 callbacks | same error; handle 5.0 → 5.1 |
| `-range` | trusted `ArrowRight` | 2 callbacks | same error; handles → `[3, 12]` |

The error text carries its own diagnosis — `Perhaps you meant **https:///**/api/v1/…` — three slashes,
the empty base URL concatenated straight onto the path. The sliders' readouts (`0 / 12`, `1×`, `[0, 12]`)
correctly do **not** advance, because they re-render only from a *successful* control response; that is
right behaviour downstream of a dead request, not a second defect.

The backend was exonerated once more en passant: a direct `POST {"action":"stop"}` to the same route
returned `200` with `fsm_state: STOPPED`.

**F-CANOPY-015 measured against the payload.** `POST /replay` returns, nested at `data.session`:

```json
{"length": 12, "time_index": 0, "speed": 1.0, "paused": true,
 "range": {"start": 0, "end": 12}, "weights_available": true,
 "weight_sampling": {"strategy": "adaptive", "num_samples": 3, "sample_epochs": [10000, 10, 11]}}
```

`weights_available` is **true** — this is provably a V2 snapshot — and the badge nonetheless renders
**`V1 (metrics only)`** in grey. The two masked siblings behave exactly as the finding predicted: `speed`
`1.0` equals `SPEED_DEFAULT`, and `range` renders `[0, 12]` because the fallback `[start, end]` from
`_session_window` coincides with the real window.

That second one hides a trap worth stating plainly, because it is the same shape as the F-CANOPY-012
transpose: the backend's `range` is a **dict** `{start, end}`, while the render does
`f"[{range_value[0]}, {range_value[1]}]"`. **Reading one level deeper without converting dict → list turns
a silently-wrong readout into a `KeyError`.** The obvious one-line fix crashes the panel.

One more stale line in the matrix: row 05 says the badge "ships `display:none`", but the callback's
`badge_style` sets `display:inline-block`, so it is *shown* — shown and wrong, which is worse than hidden.

**What still works.** `-status` faithfully rendered the error for all six attempts (it is doing its job —
what it reports is F-CANOPY-014). The weight-drain plumbing is intact: `window._juniperWsDrain` exposes
`_replayWeightBuffer` beside its six sibling channel buffers and `drainReplayWeights()` returns
`array(0)` — idle, not broken, which is precisely the distinction worth drawing when the observable
payoff is blocked upstream. The swap-events graph renders its empty state correctly, and
`GET /api/snapshots/{id}/history/dataset_swaps` returns `200` with `{"events": []}` — a live route, not
another D-0. Graph, count (`0 events`) and backend all agree, so the count is genuinely wired.

| verdict | rows |
|---|---|
| **PASS** | 01, 02, 03, 04, 06, 13, 14, 15, 16, 17 |
| **FAIL** (F-CANOPY-014) | 07, 08, 09, 10, 11, 12 |
| **FAIL** (F-CANOPY-015) | 05 |

### Methodology corrections (segment 7)

Two of my own instrument errors, recorded because each cost real time and each would recur:

- **`offsetParent` is `null` for `position:fixed` elements — so it is not a visibility test for modals.**
  Two replay-start attempts were scored as "modal never opened (20 s)" and provisionally blamed on
  F-CANOPY-004 congestion. Both were wrong: the modal *was* opening and my filter could not see it. Use
  `getComputedStyle` + `getBoundingClientRect().width/height > 0`. This sits directly beside segment 6's
  note that the modal DOM does not exist while closed — together they say: poll for the element to
  appear, then test visibility by geometry.
- **A Dash slider commits only on a TRUSTED event.** Setting the paired `<input type="number">` via the
  React native-setter moves the visual handle but produces **zero** callback dispatches and no readout
  change; so does a full synthetic `pointerdown`/`pointermove`/`pointerup` sequence. A real
  `page.keyboard.press('ArrowRight')` on the focused thumb dispatches immediately. Under
  `updatemode="mouseup"`, a moved handle is **not** evidence that a value committed — the two must be
  checked separately, or a dead control looks driven.
- **Do not blame congestion before excluding the instrument.** Both corrections above initially presented
  as F-CANOPY-004. Congestion is real and measured (140 callbacks / 11 s), which makes it an attractive
  and therefore dangerous default explanation.

### A first-load overlay stands between a fresh page and every gesture

After any reload the **welcome modal** (`welcome-modal`, matrix §2.1) is open over the dashboard and must
be dismissed via `#welcome-modal-close` before driving anything. Sessions that keep one long-lived page
never see it, so it is easy to omit from a recipe and then lose time to it after the first reload.

### W11 — in-metrics replay: 2 driven, 9 blocked on an unmet precondition

W11's stated precondition is "training **stopped** with accumulated history". The second half is not met
in this run: `GET /api/metrics/history?count=100` returns `history: []`, and `monitor.total_metrics` is
`0` — no training has run in this cascor process since the `09:44:52` start. Two rows are still
answerable, and one of the two is a matrix-precision correction worth having.

**W11-01 passes through a branch the row does not describe.** The controls are visible — but
`toggle_replay_visibility` (`metrics_panel.py:946-947`) returns `display:block` *unconditionally* when the
training-state store is falsy, and only then falls through to the
`status ∈ [STOPPED, PAUSED, COMPLETED, FAILED]` test the row names. The store is empty here, so the
status branch was never evaluated. This matters because canopy's `/api/status` currently reports
`fsm_status: REPLAYING`, which is **not** in that set — anyone checking the row against live status would
record a divergence that is not real.

**W11-02 passes in its degenerate form.** The readout is `0 / 0`. The row's `N = history length − 1` holds
for non-empty history; `update_replay_ui` (`:1082`) is `len(metrics_data) - 1 if metrics_data else 0`, so
empty history clamps `N` to `0`, not `−1`.

**D-3 is confirmed at the cited site**, which is W11-05's real payload: `metrics_panel.py:1034` reads
`base_interval = 1000`, and `:1035` divides by speed — so 1x = 1000 ms, 2x = 500 ms, 4x = 250 ms. The
documented divergence (base is 1000 ms, **not** 500 ms) holds exactly, and step 4's expected 250 ms at 4x
follows.

**The remaining nine rows were driven anyway, and the results are artifacts rather than verdicts** — which
is the point of recording them explicitly. With `max_index = 0`, `replay_tick` (`:1053-1060`) computes
`new_index 1 > end_index 0` and sets `mode = "stopped"` on the *first* tick, so:

- the play icon never durably shows ⏸ (there is no empty-history guard on the play branch — `:1010-1011`
  flips `mode` unconditionally — the state is simply overtaken by its own auto-stop);
- both step buttons pin to 0 through their own clamps (`max(0, i-1)` / `min(max_index, i+1)`);
- both jumps are no-ops because `start_index` and `end_index` coincide at 0;
- the slider is explicitly short-circuited (`:1031` computes the index only `if max_index > 0`).

None of that distinguishes a correct control from a dead one, so none of it is reported as a defect.

**Unblocking W11 needs a decision, not just more driving.** It requires a short cascor training run to
accumulate metrics history — that is W1 — which is a live state change: it would overwrite the
deliberately mutated network built by W5-12/13/15 and this segment's editor rows, and the standing
guidance is not to disturb a live cascor training state casually. Flagged for the owner rather than taken
unilaterally.
