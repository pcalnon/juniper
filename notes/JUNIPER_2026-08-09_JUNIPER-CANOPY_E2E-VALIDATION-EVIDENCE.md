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
