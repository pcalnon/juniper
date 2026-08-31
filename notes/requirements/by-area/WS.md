# Requirements — WS

**Area**: websocket / messaging — Canopy↔Cascor streaming, replay, control plane

**Total entries**: 176

**By status**: proposed=157 | designed=11 | shipped=5 | deferred=2 | superseded=1

**By priority**: P0=14 | P1=125 | P2=33 | P3=4

**By owner**: ml=161 | cas=6 | can=6 | cwk=2 | dat=1

---

### JR-ML-WS-001 — Cascor bounded 1024-entry replay buffer for lossless reconnect.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 81-131)

### JR-ML-WS-002 — Cascor must add optional seq field to all WebSocket messages and implement replay buffer with ReplayOutOfRange exception.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 233-299)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-03-MAXIMALIST-COMPREHENSIVE.md` (lines 352-420)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 39-39)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 112-112)

**Detail**:

4 commits: (1) optional seq parameter to message builders; (2) WebSocketManager replay buffer with server_instance_id
and _assign_seq_and_append under lock; (3) 0.5s send timeout on _send_json; (4) replay_since() method.
Replay buffer bounded to configurable size (default 1024, range 256-16384).
ReplayOutOfRange raised when last_seq < oldest_available - 1.

**Design**:

- self._seq_lock = asyncio.Lock(), self._next_seq: int = 0
- self._replay_buffer: deque[tuple[int, dict]] = deque(maxlen=replay_buffer_size)
- server_instance_id: str = str(uuid.uuid4())
- async _assign_seq_and_append(message) holds lock, assigns seq, appends to deque
- broadcast() and broadcast_from_thread() routed through _assign_seq_and_append before iteration
- async replay_since(last_seq) returns list[dict] under copy-under-lock pattern

**Notes**:

[v3 xround merge: rounds=R1-0,R3-0, n=3] GAP-WS-13. Carved out from Phase B per R0-03. Phase A-server (Days 2-3 of runbook). Request_id field is additive per R0-04 §12.2. / Settled position C-02 from R3-03 table; cross-round consensus consolidation / Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-003 — Cascor replay_since() method for lossless reconnect protocol.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 200-243)

### JR-ML-WS-004 — Cascor server_instance_id UUID generation and advertisement.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 281-333)

### JR-ML-WS-005 — Cascor snapshot_seq in status endpoint under same lock as seq counter.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 787-820)

### JR-ML-WS-006 — Cascor training_stream must implement two-phase registration, resume frame handler with replay, and 1 Hz state throttle coalescer.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 363-450)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-03-MAXIMALIST-COMPREHENSIVE.md` (lines 416-475)

**Detail**:

5 commits: (5) async connect_pending(), promote_to_active() with atomic move under _seq_lock;
(6) training_stream resume handler with 5s timeout for optional resume frame, server_instance_id check, replay_since() call;
(7) snapshot_seq endpoint on /api/v1/training/status; (8) state coalescer replaces 1 Hz drop filter;
(9) protocol error responses on /ws/control with JSON decode error handling.

**Design**:

- Two-phase registration: connect_pending(ws) sends connection_established, adds to _pending_connections
- promote_to_active(ws) atomically moves pending→active under _seq_lock
- Resume handler: await asyncio.wait_for(ws.receive_json(), timeout=5.0), branch on first_frame.type
- Emit resume_ok + replayed messages OR resume_failed with reason (server_restarted/out_of_range/malformed)
- State coalescer: buffer latest pending, flush max 1/sec, bypass throttle for terminal transitions
- Atomic snapshot_seq in status endpoint under _seq_lock

**Notes**:

GAP-WS-13, GAP-WS-21, GAP-WS-22, GAP-WS-29. R0-03 §8 scenario handling. Phase A-server (Days 2-3).

### JR-ML-WS-007 — Cascor two-phase connection registration with pending set.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 407-453)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 45-45)

**Notes**:

[v3 xround merge: rounds=R0-0,R3-0, n=2] Settled position C-08 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-008 — Cascor WebSocketManager emit monotonic sequence numbers on every message.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 133-200)

### JR-ML-WS-009 — CascorControlStream must expose async set_params(params, timeout=1.0) method for WebSocket parameter updates.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 98-103)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-03-MAXIMALIST-COMPREHENSIVE.md` (lines 159-170)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 1-50)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1482-1492)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 243-331)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 40-40)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-92)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 114-114)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 217-217)

**Detail**:

Adds async set_params(params, *, timeout=1.0, request_id=None) to CascorControlStream in juniper-cascor-client.
Implements per-request correlation map with background recv task for concurrent callers.
Preserves existing command() API. Includes latency instrumentation via _client_latency_ms field.

**Design**:

- Background recv task (_recv_loop) parses JSON responses and maps via request_id
- _pending: Dict[str, asyncio.Future[Dict]]for correlation
- Default 1.0s timeout; raises JuniperCascorTimeoutError on timeout
- Latency measurement: envelope["_client_latency_ms"] = (t_acked - t_sent) * 1000

**Notes**:

[v3 xround merge: rounds=R0-0,R1-0,R2-0,R3-0, n=7] GAP-WS-01. Cross-round dup with ml-B/R3-03 which would have surfaced this. Phase A (Day 1 of runbook). / Disagreement D2 per R1-04 §14. Rationale: user experience during parameter adjustment. / Parallel with Phase 0-cascor. Loose entry gate (SDK ships independent of cascor). Gated by
`test_set_params_caller_cancellation_cleans_correlation_map` passing. Rollback: PyPI yank or flag-off. / Settled position C-03 from R3-03 table; cross-round consensus consolidation / Phase A-SDK major milestone from R3-03 Phase index (§2); orchestrates implementation effort / Phase 0-cascor checklist item from R3-03 §3.1 deliverables / Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-010 — Day-1 verification procedure: 5 greps + baseline measurement before any Phase B deploy.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R4-02-EXECUTIVE-READY-DELIVERABLE.md` (lines 28-66)

**Detail**:

Pre-flight checks (must complete before Phase B PR): (1) Confirm ecosystem clean across 3 repos (git status);
(2) Verify GAP-WS-19 resolved at manager.py:138-156; (3) Record 5 scope-determining greps:
  - SessionMiddleware presence (B-pre-b budget);
  - NetworkVisualizer render tech (cytoscape vs Plotly, Phase B scope);
  - Dash version floor;
  - run_coroutine_threadsafe usage (Phase C supervisor);
  - command_id vs request_id in cascor control (Phase G contract).
(4) Measure 1-hour baseline canopy_rest_polling_bytes_per_sec in staging (denominator for >90% reduction acceptance gate).
(5) Create worktrees per Juniper convention (/home/pcalnon/Development/python/Juniper/worktrees/ format <repo>--<branch>--<YYYYMMDD-HHMM>--<shorthash>).
(6) Open Phase 0-cascor + A-SDK worktrees in parallel (no cross-repo dep until Phase G).
(7) Begin with PR-1 (phase-a-sdk-set-params on cascor-client).

**Notes**:

[v2 ARCH→WS re-bucket] Gate on Phase B entry. Dedup with R4-02, R3-03.

### JR-ML-WS-011 — H-JCW-2: Thread-unsafe `asyncio.Event.set()` from signal handler.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 298-306)

**Detail**:

**H-JCW-1: `worker.py` at 68.23% coverage**

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-WS-012 — Phase A-server cascor prerequisites for browser WebSocket migration.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 931-1016)

### JR-ML-WS-013 — Phase B: browser ws_dash_bridge drain, Plotly.extendTraces, connection-status store, polling kill.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 433-594)

**Detail**:

Frontend JS: new `ws_dash_bridge.js` (~200 LOC). Module-scope `window._juniperWsDrain`. Five handlers: metrics, state, topology,
cascade_add, candidate_progress. Per-handler bounded ring buffers. Drain methods: drainMetrics(), drainState(), drainTopology(),
drainCascadeAdd(), drainCandidateProgress(), peekStatus(). Ring bound enforced in handler (not drain callback).
Edit `websocket_client.js`: add `onStatus()` enrichment (connected/reason/reconnectAttempt/ts), jitter to reconnect
(delay = Math.random() * Math.min(CAP, BASE * 2**attempt) with BASE=500ms, CAP=30s), capture `server_instance_id`,
track `seq` (monotonic check + warn gap), emit `resume` frame first on reconnect, fall back to REST snapshot on `resume_failed`.
Delete raw-WS callback in `dashboard_manager.py`.
New `ws_latency.js` (~50 LOC): browser-side latency beacon, records `received_at_ms - emitted_at_monotonic`, POSTs to `/api/ws_latency` every 60 s.
rAF scaffold: `_scheduleRaf` gated function, default disabled per D-03.
Python-side: add `dcc.Store(id='ws-metrics-buffer')` with drain callback on fast-update-interval. Callback reads
`window._juniperWsDrain.drainMetrics()`, writes `{events: [...], gen: int, last_drain_ms: float}`.
Update existing `ws-topology-buffer` + `ws-state-buffer` drain callbacks to read from `window._juniperWsDrain`.
Add `dcc.Store(id='ws-connection-status')` with drain callback that peeks `window._juniperWsDrain.peekStatus()`, emits on change.
Refactor `_update_metrics_store_handler`: read ws-connection-status via State, return no_update when connected, 1 Hz fallback (n % 10 == 0).
Rewrite `MetricsPanel.update_metrics_display()` as clientside_callback calling `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`.
Add `uirevision: "metrics-panel-v1"` to layout, hidden `metrics-panel-figure-signal` dummy Store.
Migrate `CandidateMetricsPanel.py` likewise. Apply polling toggle to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`.
**KEEP REST paths** (kill switch + fallback).
NetworkVisualizer minimum wire: wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to cytoscape callback. **If Plotly, convert to extendTraces (+1 day per D-06).**
Connection indicator badge (GAP-WS-26): `html.Div` with clientside_callback reading ws-connection-status, CSS class toggle.
States: connected/reconnecting/offline/demo.
Demo mode (`demo_mode.py`): sets ws-connection-status to `{connected: true, mode: "demo"}` so polling returns no_update, badge shows "demo".
`/api/ws_latency` POST endpoint in `main.py`: increments `canopy_ws_delivery_latency_ms_bucket` histogram AND `canopy_rest_polling_bytes_per_sec` gauge.
Asset cache bust: bump `assets_folder_snapshot` or equivalent so browsers pick up new JS without hard refresh.
Two-flag runtime check: `enabled = Settings.enable_browser_ws_bridge AND NOT Settings.disable_ws_bridge`.
Default `enable_browser_ws_bridge=False` during PR cycle (flip-to-True is separate one-line follow-up P7, not Phase B gate).
Cascor-side residual: None at code level (all cascor work in Phase 0-cascor). Phase B adds Prometheus counters for audit events
deferred from B-pre-a.
Observability: `canopy_rest_polling_bytes_per_sec`, `canopy_ws_delivery_latency_ms_bucket`, `canopy_ws_active_connections`,
`canopy_audit_events_total{event_type}`, `canopy_ws_drain_callback_error_rate`.
Dashboard panels: "WebSocket health" (p50/p95/p99 delivery latency), "Polling bandwidth" (trend).
Tests: 27 total. Unit: `test_ws_dash_bridge.py` (update handlers return no_update when WS connected, fallback REST when disconnected,
connection status reflects cascor WS, metrics buffer bounded). Integration: `test_cascor_adapter_ws.py` (adapter subscribes+forwards,
reconnects, resume_failed handling, demo parity), `test_ws_reconnect_replay.py` (replays 10 missed, stale instance_id triggers snapshot,
no gap, old cascor fallback). Dash_duo e2e: `test_browser_receives_metrics.py` (browser receives event, chart updates per event, no polling
when WS, polling fallback on disconnect, demo parity, buffer bounded, badge reflects state). Playwright e2e: `test_websocket_wire.py`
(frames have seq, resume replays, seq resets on restart, extendTraces used). Phase H regression gate: `test_metrics_dual_format` (BOTH nested
and flat keys present). P0 proof: `test_polling_elimination` (zero `/api/metrics/history` requests after initial load over 60s).
Frame budget: `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` (rAF scaffolded disabled, retargeted to drain callback, marked `latency_recording`).
Fallback 1 Hz: `test_fallback_polling_at_1hz_when_disconnected`. NetworkVisualizer: `test_network_visualizer_updates_on_ws_cascade_add`.
Latency API: `test_canopy_latency_api_aggregates_submissions_into_prom_histogram`. Two-flag interaction: `test_both_flags_interact_correctly`.
Audit Prometheus: `test_audit_log_prometheus_counters` (deferred from B-pre-a).
Runbook: `juniper-canopy/notes/runbooks/ws-bridge-kill.md` (flip `disable_ws_bridge=True`, 5 min TTF).

**Design**:

Drain-based architecture: bounded ring buffers per event type, drain callbacks on fast interval coalesce updates.
Clientside callbacks for Plotly.extendTraces (high-freq updates). Status store drives toggle logic.
Two-flag design: feature gate + permanent kill switch. Default disabled until 72h staging soak validates memory (p95 <=500 MB).

**Notes**:

P0 win. Three-PR sequence: P5 (cascor audit Prom), P6 (canopy drain wiring, flag off), P7 (flag flip post-soak, NOT a gate).
Exit: >90% bandwidth reduction sustained 1 hour, delivery latency histogram live, dashboard panels green, memory p95 <=500 MB after 24h.
Two-flag logic: `enabled = enable_browser_ws_bridge AND NOT disable_ws_bridge`. Rollback: `disable_ws_bridge=true` (2 min TTF).

### JR-ML-WS-014 — WebSocket bridge replaces ~3 MB/s REST polling for metrics; achieves >=90% bandwidth reduction.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R4-01-COMPREHENSIVE-MASTER-PLAN.md` (lines 33-40)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 130-135)

**Detail**:

Cascor's `/ws/training` broadcast stream emits monotonically-increasing `seq` on every outbound envelope,
advertises `server_instance_id` + `replay_buffer_capacity` on `connection_established`, supports a 1024-entry
replay buffer with `resume` handler, exposes `snapshot_seq` atomically on REST. Browser drains `/ws/training`
into bounded Dash store, renders via Plotly.extendTraces, **stops polling `/api/metrics/history`** when healthy.
Polling kept forever as fallback kill-switch.

**Design**:

Two-phase WebSocket pipeline: Phase 0-cascor (cascor server prerequisites) + Phase B (browser bridge drain).
Phase 0-cascor: sequence numbers, replay buffer, resume protocol, state coalescer fix.
Phase B: ws_dash_bridge.js drain module, Plotly extendTraces for metrics panel, connection-status store,
fallback toggle via `enable_browser_ws_bridge` (default False until staging soak) + `disable_ws_bridge` (permanent kill switch).

**Notes**:

[v2 ARCH→WS re-bucket] P0 motivator. Metric: `canopy_rest_polling_bytes_per_sec` >=90% reduction vs baseline. Dedup candidate with R3-03.

### JR-CAS-WS-001 — CasCor must expose REST API for training lifecycle operations (19 endpoints).

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-735)

**Detail**:

FastAPI service layer with REST endpoints for all training lifecycle operations; WebSocket endpoints for real-time streaming (/ws/training, /ws/control); ThreadPoolExecutor for blocking training.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CAS-WS-002 — CascorIntegration → CascorServiceAdapter migration (Phase 4) replacing in-process integration with REST/WebSocket client.

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DECOUPLE_CANOPY_FROM_CASCOR_PLAN.md` (lines 1-100)

**Detail**:

Three-mode activation: demo (CASCOR_DEMO_MODE=1), legacy (CASCOR_BACKEND_PATH), service (CASCOR_SERVICE_URL, new). Adapter constructor: (service_url, api_key). WebSocket relay: CasCor service → adapter → Canopy frontend. Backward-compatible method mapping. 306 lines, 52 tests. Deprecated CascorIntegration 1,601 lines.

**Notes**:

[v2 ARCH→WS re-bucket] [v2 remap: AR→ARCH]

### JR-CAN-WS-001 — R5-01 Canonical Development Plan integration: 11 phases of WebSocket, security, architectural work aligned with code audit gaps.

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-12_R5-01-aligned.md` (lines 1-100)

**Detail**:

Reorganizes remediation timeline to coordinate with R5-01 Canonical Development Plan. 4 tracks: PRE (complete via PR #146), PAR (parallel with R5-01), EMB (R5-01 phase-embedded), POST (deferred). 11 R5-01 phases including WebSocket bridge, security hardening, frontend wiring, parameter adapter. Tracks dependencies, timelines (Weeks 1-12+), resource allocation, metrics.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CWK-WS-001 — v0.3.0 major rewrite: WebSocket-based CascorWorkerAgent replaces BaseManager-based CandidateTrainingWorker as default, with TLS/mTLS support and async event loop.

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 10-39)

**Detail**:

v0.3.0 (2026-04-08): WebSocket worker agent (new default) with long-lived WebSocket, work units pushed from cascor backend, binary tensor frames (struct-encoded shape/dtype/numpy data), worker capability reporting (CPU cores, GPU, versions on connect), heartbeat keepalive loop. New classes: CascorWorkerAgent (async event loop), WorkerConnection (WebSocket transport with TLS/mTLS and exponential backoff reconnection). New modules: ws_connection.py, task_executor.py (isolated training pipeline). New CLI flags: --tls-cert, --tls-key, --tls-ca for mTLS. Legacy mode (CandidateTrainingWorker) preserved behind --legacy flag with DeprecationWarning, will be removed in next major. Auth token rename: --api-key/CASCOR_API_KEY → --auth-token/CASCOR_AUTH_TOKEN (old names retained as deprecated fallbacks).

**Notes**:

[v2 ARCH→WS re-bucket] Backward-compatible at deployment level via --legacy. Operators may continue legacy mode during migration window. Default mode changed; no fallback default.

### JR-ML-WS-015 — [§2.9 Security Model (REQUIRED)](../../code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md#29-security-model-required-before-phase-d).

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 21-45)

**Notes**:

[v3 brief repaired from cited content; was: '0.2 Table of Contents'] WebSocket/messaging architecture gap or design

### JR-ML-WS-016 — Each item below has: a unique ID, severity (P0-P3), location, current state, target state, and a remediation hook.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 1128-1131)

**Notes**:

[v3 brief repaired from cited content; was: '7. Missing / Broken Pieces (Enumerated)'] WebSocket/messaging architecture gap or design

### JR-ML-WS-017 — Final resolution**: **LOW (latent)**. The bug is currently inactive because the dashboard doesn't consume WebSocket data (P5-RC-05). The….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1174-1182)

**Notes**:

[v2 ARCH→WS re-bucket] [v3 brief repaired from cited content; was: '7.9 Relay Raw Metrics Severity: MODERATE vs LOW']

### JR-ML-WS-018 — Given the latency tolerance matrix, here is the recommended transport for every operation in scope.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 974-977)

**Notes**:

[v3 brief repaired from cited content; was: '6. Transport Split Design'] WebSocket/messaging architecture gap or design

### JR-ML-WS-019 — **Latency budgets**: see §5 — distinguishes *control feedback latency* (slider→DOM, must be <16 ms, achieved by Dash clientside), *ack….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 46-77)

**Notes**:

[v3 brief repaired from cited content; was: '0. Document Conventions'] WebSocket/messaging architecture gap or design

### JR-ML-WS-020 — Playwright trace viewer + dash_duo store assertions + the verification matrix in §8.8; the §1.3 architectural correction (Option B Interval.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 1875-1897)

**Notes**:

[v4 brief repaired; was: '10. Risk Register'] WebSocket/messaging architecture gap or design

### JR-ML-WS-021 — The original draft had 8 open questions; several have been resolved into recommendations during integration. Remaining genuinely-open….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 1898-1915)

**Notes**:

[v3 brief repaired from cited content; was: '11. Open Questions for Human Review'] WebSocket/messaging architecture gap or design

### JR-ML-WS-022 — This section documents every message type that crosses each repo boundary. **Asterisks (*) mark fields that are required**; all others are….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 437-440)

**Notes**:

[v3 brief repaired from cited content; was: '3. Bidirectional Message Contract'] WebSocket/messaging architecture gap or design

### JR-ML-WS-023 — This section tabulates every editable canopy UI element with its latency requirements and the recommended transport.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 815-823)

**Notes**:

[v3 brief repaired from cited content; was: '5. Latency Tolerance Matrix'] WebSocket/messaging architecture gap or design

### JR-ML-WS-024 — /ws/control handler returns protocol-error envelopes, echoes command_id, NO seq on command_response.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 120-120)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-025 — 15: **CSWSH attack**.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 389-390)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-026 — Add async set_params() method to CascorControlStream for WebSocket parameter control.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 94-150)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CAN-WS-002 — Add missing fields to WebSocket relay state callback (current_epoch, current_step, learning_rate, max_hidden_units, max_epochs, network_name, timestamp).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 261-290)

**Detail**:

ISS-02 MODERATE. WebSocket relay state callback (cascor_service_adapter.py:218-225) only forwards status and phase to global training_state. CasCor state messages also contain current_epoch, current_step, learning_rate, max_hidden_units, max_epochs, network_name, timestamp — all discarded. TrainingState.update_state() accepts **kwargs and can handle these fields. Result: /api/state reads from training_state.get_state() with stale epoch/step data after initial sync (though status bar makes fresh REST calls, bypassing staleness).

**Notes**:

Currently latent because status bar makes fresh REST calls. Mitigating factor masks the bug in production but architectural risk remains.

### JR-ML-WS-027 — Adopt WebSocket-based remote worker architecture (Approach A) with phased rollout through Phase 4.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 1496-1520)

**Detail**:

Phases: 1a security fixes, 1b WebSocket endpoint, 2 remote agent, 3 unified distributor, 4 hardening.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-028 — Background _recv_task started on connect; parses inbound, pops future by command_id, set_result(envelope).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 219-219)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-029 — BROKEN: - MISSING — feature does not exist.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 61-62)

### JR-ML-WS-030 — Browser must send ping frame every 30s; expect pong within 5s; close and reconnect on timeout.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 400-450)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1313-1318)

**Detail**:

assets/websocket_client.js: send {"type": "ping"} every 30s; expect {"type": "pong"} within 5s.
Close + reconnect on timeout (true heartbeat loss indicates network issue).
Cascor training_stream_handler inbound dispatcher already handles ping → pong (Day 3 handle_training_inbound).

**Notes**:

GAP-WS-12. Phase F (Day 11). Does not bypass auth (heartbeat inside authenticated session).

### JR-ML-WS-031 — C-02: `command_response` has NO `seq` field; `/ws/control` has no replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 229-230)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-032 — C-05: Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 243-244)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-033 — C-11: GAP-WS-19 `close_all` lock is RESOLVED on main; regression test only.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 257-258)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-034 — C-18: `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 245-246)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-035 — C-20: GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 273-274)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-WS-036 — C-41: `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 236-237)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-037 — Caller-cancellation cleans correlation map entry in finally.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 221-221)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-038 — Canopy adapter must split apply_params into hot (WebSocket) and cold (REST) paths; route hot params via CascorControlStream.set_params.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1161-1276)

**Detail**:

Canopy src/config/settings.py: add use_websocket_set_params: bool = Field(default=False, ...).
Env var JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS.
Class constants _HOT_CASCOR_PARAMS and _COLD_CASCOR_PARAMS (enumeration from R0-04 §5.1).
Refactor apply_params(**params): if flag False → _apply_params_cold; if True → split hot/cold, unclassified keys REST+WARNING.
Run hot FIRST, then cold (per R0-04 §5.1 ordering guarantee with lifecycle._training_lock serialization).
_apply_params_hot: check control_stream connected; asyncio.run_coroutine_threadsafe(..., self._event_loop).result(timeout=2.0).
Fall back to REST on JuniperCascorTimeoutError, JuniperCascorConnectionError.
Surface server error (do NOT fall back) on JuniperCascorClientError.

**Notes**:

Phase C (Day 10). Feature flag default False per R0-04 §5.6 ack-vs-effect analysis. Flag remains False in Phase C release.

### JR-ML-WS-039 — Canopy must implement _control_stream_supervisor task that maintains persistent WebSocket connection to cascor.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 100-200)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1217-1260)

**Detail**:

Background task: loop while not shutdown.is_set(): connect → wait_closed() → backoff [1, 2, 5, 10, 30] seconds.
Launched alongside _metrics_relay_task in start_metrics_relay().
Cancelled in stop_metrics_relay().
self._control_stream = None when not connected (used by _apply_params_hot gate).
Latency instrumentation: read envelope["_client_latency_ms"] from set_params ack, observe SET_PARAMS_LATENCY_MS.labels(transport="websocket").

**Notes**:

Enables Phase C and Phase D. Separate from metrics relay (Day 7). Histogram buckets per R0-04 §7.

### JR-ML-WS-040 — Cascor /ws/control protocol error responses per GAP-WS-22.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 916-928)

### JR-ML-WS-041 — Cascor backpressure handling with 0.5s per-send timeout (quick fix).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 454-525)

### JR-ML-WS-042 — Cascor command_id echo in control responses for per-command correlation.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 821-915)

### JR-ML-WS-043 — Cascor Phase 0-cascor: sequence numbers, replay buffer, resume protocol, state coalescer fix.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 128-240)

**Detail**:

10 commits: `messages.py` adds optional `seq: Optional[int]` on every envelope builder.
`manager.py` adds: `server_instance_id: str = uuid4()`, `server_start_time: float`, `_next_seq: int`,
`_seq_lock: asyncio.Lock`, `_replay_buffer: deque` with `maxlen=Settings.ws_replay_buffer_size` (default 1024).
`connect()` sends `connection_established` with `server_instance_id`, `server_start_time`, `replay_buffer_capacity`.
`_send_json()` wraps in `asyncio.wait_for(..., timeout=0.5)` (GAP-WS-07 quick-fix).
`replay_since(last_seq)` helper + `ReplayOutOfRange` exception.
`training_stream.py` adds `_pending_connections: set`, two-phase registration, `promote_to_active()`.
`/ws/training` handles `resume` frame (5 s timeout) → `resume_ok` or `resume_failed`.
Server restart detected via `server_instance_id` mismatch. One-resume-per-connection rule enforced (second → close 1003).
`/api/v1/training/status` REST returns `snapshot_seq` + `server_instance_id` atomically under `_seq_lock`.
Lifecycle manager: replace throttle with debounced coalescer; terminal transitions bypass throttle (GAP-WS-21 fix).
`broadcast_from_thread` adds `Task.add_done_callback(_log_exception)` (GAP-WS-29 fix).
`/ws/control` returns protocol-error envelopes; echoes `command_id`; **NO seq** (D-03).
CHANGELOG + `docs/websocket_protocol.md` update.

**Design**:

Additive-field design. Existing clients ignoring seq keep working. Resume handler with 5 s timeout;
one-resume guard prevents replay amplification. Atomic snapshot_seq under seq_lock prevents torn reads.

**Notes**:

Parallel with Phase A-SDK. Entry: cascor main clean, GAP-WS-19 verified. Exit: 20 tests pass,
seq monotonic in staging, 24h soak zero gaps. Rollback: git revert (15 min TTF).

### JR-ML-WS-044 — Constitution: 42+ settled positions on wire format, protocol behavior, security, phase order, observability, effort.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R4-01-COMPREHENSIVE-MASTER-PLAN.md` (lines 112-242)

**Detail**:

C-01: Correlation field `command_id`, NOT `request_id`. C-02: `command_response` NO seq; `/ws/control` no replay buffer.
C-03: `set_params` default timeout 1.0 s (not 5.0 s). C-04: SDK fails fast on disconnect, no reconnect queue, no retries.
C-05: Replay buffer 1024 entries, env-configurable. C-06: `server_instance_id` programmatic key, `server_start_time` advisory.
C-07: `replay_buffer_capacity` on `connection_established`. C-08: Two-phase registration via `_pending_connections`.
C-09: Cascor `SetParamsRequest` `extra="forbid"`; canopy routes unclassified keys to REST with WARN.
C-10: Adapter→cascor HMAC first-frame (NOT `X-Juniper-Role` header). C-11: GAP-WS-19 resolved on main, regression test only.
C-12/C-13: Phase 0-cascor carve-out from Phase B; Phase B-pre splits 0-cascor + B-pre-b.
C-14: Phase B two-flag design (`enable_browser_ws_bridge` + `disable_ws_bridge`). C-15: Phase E default `drop_oldest_progress_only`.
C-16: rAF coalescer scaffolded disabled. C-17: REST fallback 1 Hz during disconnect. C-18: `ws-metrics-buffer` = `{events, gen, last_drain_ms}`.
C-19: Ring bound in handler, not drain callback. C-20: GAP-WS-24 splits 24a (browser) + 24b (canopy endpoint).
C-21: NetworkVisualizer minimum wire Phase B, deep deferred if cytoscape. C-22: `_normalize_metric` dual format preserved, CODEOWNERS Phase H.
C-23: REST endpoints preserved FOREVER, no deprecation. C-24: Per-IP cap 5, single-bucket rate limit 10 cmd/s.
C-25: One-resume-per-connection rule. C-26: Per-command HMAC deferred. C-27: `ws_security_enabled=True` (positive sense).
C-28: Phase C flag `use_websocket_set_params=False` default, 6 hard flip gates.
C-29: Debounce in Dash callback (250 ms), not SDK. C-30: `JUNIPER_WS_ALLOWED_ORIGINS='*'` REFUSED (non-switch).
C-31: Multi-tenant isolation deferred. C-32: Chromium-only Playwright v1. C-33: Per-command HMAC deferred.
C-34: Contract-test pytest marker. C-35: Latency tests recording-only CI, strict local-only. C-36: Total 15.75 eng days / ~4.5 weeks.
C-37: P0 metric = canopy_rest_polling_bytes_per_sec >=90% reduction. C-38: Observability-before-behavior. C-39: Kill-switch MTTR <=5 min, CI-tested.
C-40: Wire format strictly additive. C-41: `emitted_at_monotonic` on every `/ws/training` broadcast.
C-42: Error-budget burn-rate operationally binding.
Plus D-NN decision mapping, effort table, feature flag inventory.

**Notes**:

[v2 ARCH→WS re-bucket] Source of truth. All items settled; re-litigation via formal decision change only. Used by Phase 0-cascor through Phase I.

### JR-ML-WS-045 — D-**CSWSH attack** (RISK-15): High.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 131-132)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-046 — D-Security: CSWSH closed: `canopy_ws_origin_rejected_total` page alert functional.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-047 — disconnect() cancels recv task, drains pending with set_exception(JuniperCascorConnectionError).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 220-220)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-048 — Fail-fast: no SDK retries on timeout (C-04).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 222-222)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-049 — GAP-WS-01: and the subsequent canopy-side adapter refactor.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1338-1342)

### JR-ML-WS-050 — GAP-WS-01: through GAP-WS-33), ranging from P0 (security, auth, replay protocol, REST polling bandwid.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 149-153)

### JR-ML-WS-051 — GAP-WS-01: — `juniper-cascor-client` lacks WebSocket `set_params`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1236-1240)

### JR-ML-WS-052 — GAP-WS-02: through GAP-WS-05) | Playwright e2e: `test_browser_receives_metrics_event`, `test_chart_up.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1784-1788)

### JR-ML-WS-053 — GAP-WS-02: — Browser-side `cascorWS` / `cascorControlWS` are dead code.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1249-1253)

### JR-ML-WS-054 — GAP-WS-03: — Parallel raw-WebSocket clientside callback at `dashboard_manager.py:1490`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1257-1261)

### JR-ML-WS-055 — GAP-WS-04: note about background tab throttling.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 2003-2007)

### JR-ML-WS-056 — GAP-WS-04: — `ws-metrics-buffer` store never populated.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1265-1269)

### JR-ML-WS-057 — GAP-WS-05: — No clientside callback drains WS stores into chart inputs.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1273-1277)

### JR-ML-WS-058 — GAP-WS-06: — Training control buttons use REST POST instead of WebSocket.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1289-1293)

### JR-ML-WS-059 — GAP-WS-07: (backpressure) sooner. **Decision needed before Phase E.**.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 2015-2019)

### JR-ML-WS-060 — GAP-WS-07: backpressure with per-send timeout) lands before or together with Phase B (GAP-WS-13 seque.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1170-1174)

### JR-ML-WS-061 — GAP-WS-07: — No backpressure / slow client handling in cascor `WebSocketManager`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1297-1301)

### JR-ML-WS-062 — GAP-WS-08: — No end-to-end browser test for the WebSocket path.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1307-1311)

### JR-ML-WS-063 — GAP-WS-09: integration tests that exercise the failure modes.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1437-1441)

### JR-ML-WS-064 — GAP-WS-09: — No cascor-side integration test for `set_params` on `/ws/control`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1320-1324)

### JR-ML-WS-065 — GAP-WS-10: + the canopy adapter refactor + GAP-WS-32 (per-command timeouts).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1855-1859)

### JR-ML-WS-066 — GAP-WS-10: — No canopy-side integration test for `set_params` round-trip.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1332-1336)

### JR-ML-WS-067 — GAP-WS-11: + §4.4 phased plan.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1923-1927)

### JR-ML-WS-068 — GAP-WS-11: Phase H).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1532-1536)

### JR-ML-WS-069 — GAP-WS-11: — Canopy `_normalize_metric` dual format is undocumented for external consumers.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1340-1344)

### JR-ML-WS-070 — GAP-WS-12: — No WebSocket heartbeat / ping-pong reciprocity.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1348-1352)

### JR-ML-WS-071 — GAP-WS-13: (P1) — Lossless reconnect via sequence numbers and replay buffer. Required components:.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1142-1146)

### JR-ML-WS-072 — GAP-WS-13: (sequence numbers + replay), GAP-WS-14 (Plotly extendTraces), GAP-WS-15 (rAF coalescing),.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1829-1833)

### JR-ML-WS-073 — GAP-WS-13: a server that doesn't recognize the `resume` command will respond with `command_response`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1214-1218)

### JR-ML-WS-074 — GAP-WS-13: Lossless Reconnect via Sequence Numbers and Replay Buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2177-2188)

### JR-ML-WS-075 — GAP-WS-13: reconnect+replay protocol — `server_start_time` change forces all clients to do a full RES.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 2005-2009)

### JR-ML-WS-076 — GAP-WS-13: sequence numbers land). Currently there is no mechanism to reject an outdated client. De.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 2023-2027)

### JR-ML-WS-077 — GAP-WS-13: — Lossless reconnect via sequence numbers and replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1356-1360)

### JR-ML-WS-078 — GAP-WS-14: (`extendTraces`), this keeps the per-frame cost under 17 ms.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1377-1381)

### JR-ML-WS-079 — GAP-WS-14: above. Kept here for reference link integrity.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1442-1446)

### JR-ML-WS-080 — GAP-WS-14: mandates `Plotly.extendTraces(maxPoints=5000)`; ring buffer in `ws-metrics-buffer` (last 1.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 2001-2005)

### JR-ML-WS-081 — GAP-WS-14: Plotly `extendTraces` with `maxPoints` Limit.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2146-2160)

### JR-ML-WS-082 — GAP-WS-14: — Plotly chart updates must use `extendTraces` with `maxPoints`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1364-1368)

### JR-ML-WS-083 — GAP-WS-15: Browser-Side rAF Coalescing for 50Hz Candidate Events.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2163-2174)

### JR-ML-WS-084 — GAP-WS-15: — Browser-side rAF coalescing for high-frequency events.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1372-1376)

### JR-ML-WS-085 — GAP-WS-16: `/api/metrics/history` Polling Bandwidth Bomb (~3 MB/s).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2129-2143)

### JR-ML-WS-086 — GAP-WS-16: — `/api/metrics/history` polling is the bandwidth bomb (P0 motivator).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1380-1384)

### JR-ML-WS-087 — GAP-WS-17: — `permessage-deflate` compression not configured.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1388-1392)

### JR-ML-WS-088 — GAP-WS-18: chunking or REST fallback; document the threshold; add a server-side size guard.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 2007-2011)

### JR-ML-WS-089 — GAP-WS-18: Topology Message >64KB Causes Connection Teardown.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2219-2238)

### JR-ML-WS-090 — GAP-WS-18: — Topology message can exceed 64 KB silently.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1396-1400)

### JR-ML-WS-091 — GAP-WS-19: in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 229-233)

### JR-ML-WS-092 — GAP-WS-19: — `close_all()` does not hold `_lock` (CR-025 partial).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1404-1408)

### JR-ML-WS-093 — **GAP-WS-20: (P3)**: normalize bidirectional envelope to use `{type, timestamp, data}` everywhere. Trac.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 482-486)

### JR-ML-WS-094 — GAP-WS-20: — Bidirectional envelope asymmetry.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1412-1416)

### JR-ML-WS-095 — GAP-WS-21: (P1) in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 555-559)

### JR-ML-WS-096 — GAP-WS-21: 1 Hz State Throttle Drops Terminal Transitions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2241-2246)

### JR-ML-WS-097 — GAP-WS-21: debouncer rewrite) AND state event rate goes >5 Hz.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1528-1532)

### JR-ML-WS-098 — GAP-WS-21: — 1 Hz state throttle drops terminal transitions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1420-1424)

### JR-ML-WS-099 — GAP-WS-22: (P2) in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 745-749)

### JR-ML-WS-100 — GAP-WS-22: (protocol error responses).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1908-1912)

### JR-ML-WS-101 — GAP-WS-22: — Protocol error responses not specified.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1431-1435)

### JR-ML-WS-102 — GAP-WS-23: (P1) in §7: clientside chart updates must use `Plotly.extendTraces()` with `maxPoints` p.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1022-1026)

### JR-ML-WS-103 — GAP-WS-23: — `Plotly.extendTraces` with `maxPoints` (alias of GAP-WS-14).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1439-1443)

### JR-ML-WS-104 — GAP-WS-24: (P2) in §7. Phase B includes the instrumentation; Phase C+ uses the data to validate (or.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1037-1041)

### JR-ML-WS-105 — GAP-WS-24: — Production WebSocket latency instrumentation.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1444-1448)

### JR-ML-WS-106 — GAP-WS-25: (polling toggle).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1385-1389)

### JR-ML-WS-107 — GAP-WS-25: polling toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1386-1390)

### JR-ML-WS-108 — GAP-WS-25: WebSocket-Health-Aware Polling Toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2191-2202)

### JR-ML-WS-109 — GAP-WS-25: — WebSocket-health-aware polling toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1452-1456)

### JR-ML-WS-110 — GAP-WS-26: Visible Connection Status Indicator.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2205-2216)

### JR-ML-WS-111 — GAP-WS-26: — Visible connection status indicator.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1460-1464)

### JR-ML-WS-112 — GAP-WS-27: — Per-IP connection caps and DoS protection.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1468-1472)

### JR-ML-WS-113 — GAP-WS-28: Multi-Key `update_params` Torn-Write Race.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2249-2260)

### JR-ML-WS-114 — GAP-WS-28: — Multi-key `update_params` torn-write race.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1476-1480)

### JR-ML-WS-115 — GAP-WS-29: for the exception-handling path.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1180-1184)

### JR-ML-WS-116 — GAP-WS-29: — `broadcast_from_thread` discards future exceptions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1484-1488)

### JR-ML-WS-117 — GAP-WS-30: — Reconnect backoff has no jitter (thundering herd risk).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1492-1496)

### JR-ML-WS-118 — GAP-WS-31: Unbounded Reconnect Cap — Stops After 10.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2263-2274)

### JR-ML-WS-119 — GAP-WS-31: — Unbounded reconnect attempts cap (currently capped at 10).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1500-1504)

### JR-ML-WS-120 — GAP-WS-32: per-command correlation IDs + `pending verification` state pending matching `command_respo.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 2004-2008)

### JR-ML-WS-121 — GAP-WS-32: Per-Command Timeouts and Orphaned-Command Resolution.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2277-2288)

### JR-ML-WS-122 — GAP-WS-32: — Per-command timeouts and orphaned-command resolution.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1508-1512)

### JR-ML-WS-123 — GAP-WS-33: — Demo mode failure visibility.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 1516-1520)

### JR-ML-WS-124 — lifecycle/manager.py state coalescer; terminal transitions bypass throttle (GAP-WS-21).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 118-118)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-125 — manager.py gains server_instance_id, server_start_time, _next_seq, _seq_lock, _replay_buffer, _assign_seq_and_append().

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 113-113)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-126 — MISSING: - PARTIAL — feature is partially implemented; some paths work, others don't.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 60-61)

### JR-ML-WS-127 — MISSING: Status: server-side PRESENT (cascor accepts and handles the command); client-side MISSING.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 729-730)

### JR-ML-WS-128 — Phase 0-cascor: Cascor /ws/training emits monotonic seq, advertises server_instance_id+replay_buffer_capacity, supports resume, fixes state coalescer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-91)

**Notes**:

Phase 0-cascor major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-129 — Phase D: Browser start/stop/pause/resume/reset routed via /ws/control with REST fallback; per-command timeouts.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 250-350)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1278-1355)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 792-864)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-97)

**Detail**:

Replace REST POST callback body with clientside callback calling window.cascorControlWS.send({command, command_id: uuidv4()}).
Fallback: if window.cascorControlWS not connected, POST to /api/train/{command}.
Add command_id generation in ws_dash_bridge.js.
Track pending commands in JS map; mark button "pending verification" until command_response or matching state event.
Cascor: accept optional command_id in inbound frames; echo in command_response (pass-through string, no validation).

**Notes**:

[v3 xround merge: rounds=R0-0,R1-0,R2-0,R3-0, n=3] GAP-WS-32, RISK-13. Cascor Day 3 verify command_id echo. Phase D (Day 11). BLOCKED on Phase B-pre in production ≥24h. / Entry: Phase B in main + Phase B-pre-b in production >=48h (strict). Phase D gated on production because directly exposes control plane.
Exit: 9 tests pass, manual button clicks work via WS + fallback, CSRF enforced, 24h zero orphaned commands.
Rollback: `JUNIPER_CANOPY_BUTTONS_USE_WS=false` (instant) or revert P12→P11. Dedup candidate with R3-03. / Phase D major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-130 — Phase F: Application ping/pong at 30s; 10s dead-conn threshold; uncap reconnect; jitter formula.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-99)

**Notes**:

Phase F major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-131 — replay_since(last_seq) + ReplayOutOfRange exception; copy-under-lock pattern.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 115-115)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-132 — Security: CSWSH closed.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-133 — self._pending: Dict[str, asyncio.Future] correlation map, bounded at 256 with JuniperCascorOverloadError on overflow.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 218-218)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-134 — training_stream.py two-phase registration, resume/resume_ok/resume_failed handler with 5s timeout.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 116-116)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-135 — GAP-WS-19 close_all lock is RESOLVED on main.

**Status**: shipped  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 48-48)

**Notes**:

Settled position C-11 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-136 — Standardize WebSocket frame schema for Canopy↔CasCor training streaming.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md` (lines 1-50)

### JR-CAS-WS-003 — Thread handoff procedure replaces default compaction; preserves context at 95-99% utilization threshold.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/THREAD_HANDOFF_IMPLEMENTATION.md` (lines 1-100)

**Detail**:

Two-layer implementation: global ~/.claude/CLAUDE.md + project CLAUDE.md. Trigger: 95-99% context utilization (within 1-5% of compaction threshold). Additional triggers: 15+ tool calls, phase boundary, degraded recall, module transition, user request. 5-step execution protocol: checkpoint, compose goal, present, verify, git status. Exclusions: nearly complete task, sharp thread, tightly coupled work.

### JR-ML-WS-137 — Phase E-server deferred perper-client queue and backpressure policy matrix.

**Status**: deferred  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 1017-1029)

### JR-ML-WS-138 — `src/api/websocket/worker_stream.py:159-164` — server generates `worker_id = f"worker-{uuid.uuid4().hex[:12]}"`. Client-supplied value is st.

**Status**: superseded  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-21_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V4-VALIDATED.md` (lines 76-100)
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V5-VALIDATED.md` (lines 93-119)

**Notes**:

[v2 ARCH→WS re-bucket] [v4 brief repaired; was: '3. Items Previously Incomplete — Now Fixed'] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

[v4 brief repaired; was: '3. Items Previously Incomplete — Now Fixed'] Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-WS-139 — Adapter→cascor auth = HMAC first-frame, NOT X-Juniper-Role header.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 47-47)

**Notes**:

Settled position C-10 from R3-03 table; cross-round consensus consolidation

### JR-CAS-WS-004 — AGENTS.md documentation drift: 7-phase plan to align with service architecture, security, observability, CI/CD.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 1-150)

**Detail**:

Phase 1: Update version 0.3.17 → 0.4.0, restructure to lead with service architecture. Phase 2: Add server commands, environment variables, key entry points (server.py, api/app.py). Phase 3: Document REST API (endpoint inventory, auth), WebSocket protocol (3 channels), lifecycle management, remote workers, middleware. Phase 4: Security (API keys, rate limiting, headers, TLS), observability (JSON logging, Prometheus, Sentry). Phase 5: CI/CD workflows, deployment (Docker, Kubernetes), configuration. Phase 6: Update existing sections (directory structure, dependencies, testing). Phase 7: New sections (service launcher, MCP). Validation criteria listed.

### JR-ML-WS-140 — **Architecture**: WebSocket-based async worker (default) + legacy multiprocessing mode (deprecated).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 280-287)

**Detail**:

- **Tests**: 101 passed, 80.13% coverage (barely meets threshold)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-ML-WS-141 — Canopy adapter hot/cold parameter splitting (WebSocket vs REST).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 293-352)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-142 — Canopy control buttons must resolve orphaned commands via state event arrival (fallback to explicit timeout).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 350-400)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1307-1340)

**Detail**:

Track pending commands in JS map by command_id.
Button marked "pending verification" until command_response arrives OR a matching state event lands.
If orphaned (no response after explicit timeout, ~5s), resolve as success-assumed per RISK-13 mitigation.
Prevents UI deadlock if server handles command but response WS frame is dropped.

**Notes**:

RISK-13. Phase D (Day 11). Playwright test: test_orphaned_command_resolves_via_state_event.

### JR-ML-WS-143 — Cascor SetParamsRequest has extra=forbid; canopy adapter routes unclassified keys to REST.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 46-46)

**Notes**:

Settled position C-09 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-144 — CC-08: WebSocket Auto-Reconnection Not Implemented.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3728-3742)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CAS-WS-005 — Complete documentation for spiral data generator extraction, PyPI client packages, microservices implementation, and polyrepo architecture.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/JUNIPER_CASCOR_SPIRAL_DATA_GEN_REFACTOR_PLAN.md` (lines 1-100)

**Detail**:

Comprehensive extraction plan synthesizing 3 proposals, phases 0-4 complete (76 tests passing), phase 5 deferred. Core principles: pure NumPy generator, artifact-first API (NPZ), minimal provider set, deterministic reproducibility. Methods to extract: coordinate generation, feature/label construction, ordering/partitioning. Dependency decoupling: remove torch, matplotlib, logging, multiprocessing. Constants extraction: spiral geometry (num_spirals, points_per_spiral, rotations), noise parameters. NPZ data contract specification (dataset_id hash-based, structure validation). Documentation complete with test coverage and phase-by-phase delivery schedule.

### JR-ML-WS-145 — Correlation field is command_id, NOT request_id.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 38-38)

**Notes**:

Settled position C-01 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-146 — **Decision**: Support both `--systemd` flag and `USE_SYSTEMD=1` env var.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 32-38)

**Detail**:

**Decision**: Support both `--systemd` flag and `USE_SYSTEMD=1` env var.

**Notes**:

[v3 brief repaired from cited content; was: '2.3 Plant/chop systemd mode activation']

### JR-CWK-WS-002 — Hardcoded values refactoring: create juniper_cascor_worker/constants.py to consolidate ~50 hardcoded values (protocol messages, activation functions, training defaults, WebSocket config, validation bounds).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 1-50)

**Detail**:

~50 hardcoded values across 7 source files. Existing infrastructure: config.py WorkerConfig dataclass (8 field defaults, partial coverage). Gaps: protocol message type strings (7), activation function names (3), training hyperparameters (6 — epochs, learning rate, display frequency, value scales), WebSocket config (4), config duplicates across config.py/cli.py/env defaults (6), validation constants (2), error handling (2). Coverage summary: ~3 covered (partial), ~47 not covered. Proposed solution: create constants.py with sections for protocol types, activation functions, training defaults, WebSocket, config defaults, validation, error handling. Update config.py, cli.py, worker.py, task_executor.py, ws_connection.py to import from constants.py. Key benefit: eliminates 3-way duplication between config.py, cli.py, env var defaults.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-147 — Implement WebSocket remote worker infrastructure: /ws/v1/workers endpoint, WorkerRegistry, WorkerCoordinator, binary protocol.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 852-890)

**Design**:

Phase 1b WebSocket endpoint with JWT auth, binary message frames, task assignment/result collection, worker heartbeat management.

### JR-ML-WS-148 — `MSG_TYPE_TOKEN_REFRESH` defined but never referenced — dead code (forward compatibility?).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 123-132)

**Detail**:

|    ID    | Severity | File:Line               | Description                                                                                 |

**Notes**:

[v4 brief repaired; was: '2.3 Code Quality']

### JR-ML-WS-149 — One-resume-per-connection rule (second resume → close 1003).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 62-62)

**Notes**:

Settled position C-25 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-150 — Phase B ships behind two flags: enable_browser_ws_bridge + disable_ws_bridge.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 51-51)

**Notes**:

Settled position C-14 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-151 — Phase C (P2 priority): Canopy adapter hot/cold param split; hot→WS via `command_id`; REST fallback; flag-off default.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 706-789)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-96)

**Detail**:

Canopy adapter (`cascor_service_adapter.py`) splits params: hot set (learning_rate, candidate_learning_rate, correlation_threshold,
candidate_pool_size, max_hidden_units) → `/ws/control` via `set_params` (1.0 s timeout); cold set → REST PATCH (permanent, never deprecated).
`_HOT_CASCOR_PARAMS` + `_COLD_CASCOR_PARAMS` frozensets. `apply_params(**params)` dispatcher calls `_apply_params_hot()` (WS) or `_apply_params_cold()` (REST).
`_apply_params_hot()` uses `CascorControlStream.set_params(params, timeout=1.0)`. On timeout/error: **unconditional fallback to REST PATCH** (no retries).
Unclassified keys (not in `_HOT` or `_COLD`) → REST with WARNING log.
`_control_stream_supervisor`: background task maintaining `/ws/control` connection, reconnects on disconnect,
sends HMAC first-frame (wired in B-pre-b, confirmed here).
Settings: `use_websocket_set_params: bool = False` (default), `ws_set_params_timeout: float = 1.0`.
Debounce (250 ms) lives in Dash clientside slider callback, not SDK.
Latency instrumentation: `canopy_set_params_latency_ms{transport, param_name}` histogram (labels: `rest`, `ws`).
Tests: 14+ entries. Routes hot to WS when flag on, to REST when off. Routes cold to REST always.
Falls back to REST on WS timeout + connection error. Defaults unclassified to REST with warning. Slider debounce 250 ms.
Set_params latency histogram exported for both transports. Slider drag routes correct per flag. Control stream supervisor
reconnects + sends HMAC. Concurrent correlation test passes.
Documenation: `juniper-canopy/notes/runbooks/ws-set-params-flip.md` (how to flip, monitor, revert).

**Design**:

Single PR (P10). No cascor-side change (Phase 0-cascor's `command_id` echo handles it).
Adapter refactor centralizes param routing logic. REST fallback unconditional (no retries per R1-05 §4.22).

**Notes**:

[v3 xround merge: rounds=R2-0,R3-0, n=2] Entry: Phase A-SDK on PyPI, Phase B in main + staging. Optional: Phase C can skip until Phase D if timeline tight
(Phase D is gated on B-pre-b, not C). Exit: 14+ tests pass, latency histogram has both transport labels,
flag-off by default (regression check), manual drag test works. Rollback: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`.
Canary: 7 days production >=0 orphaned commands before flag flip PR. / Phase C major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-152 — Phase F (optional): Application-level `ping`/`pong` heartbeat, dead-connection detection, uncapped reconnect.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 924-973)

**Detail**:

Cascor `/ws/training` + `/ws/control` emit `ping` every 30 s (JSON `{type: "ping", ts: float}`).
JS replies `pong` within 5 s. Dead-connection detection: no `pong` within 10 s of `ping` → close 1006.
GAP-WS-31: lift 10-attempt reconnect cap to unlimited, max interval 60 s once cap reached.
Jitter formula: `delay = Math.random() * Math.min(60000, 500 * 2 ** Math.min(attempt, 7))` (explicit, prevents NaN).
Tests: 4 entries. Heartbeat reciprocity, dead-connection detection, uncapped attempts, jitter formula no NaN.

**Design**:

Single PR (P14) across cascor + canopy. Application-level vs framework-level (uvicorn) detects TCP half-open faster.

**Notes**:

Entry: Phase B in main. Priority P2 (default), small phase (0.25-1.0 day). Exit: 4 tests pass,
manual firewall drop → dead conn within 40 s, 48h soak no NaN delays. Rollback: revert P14 (10 min TTF).

### JR-ML-WS-153 — PROTO-01: Canopy `/ws/control` Accepts `reset` Parameter Not in Cascor Protocol.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5252-5266)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-154 — Replay buffer = 1024 entries, env-configurable via JUNIPER_WS_REPLAY_BUFFER_SIZE.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 42-42)

**Notes**:

Settled position C-05 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-155 — replay_buffer_capacity added to connection_established.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 44-44)

**Notes**:

Settled position C-07 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-156 — REST fallback cadence during disconnect = 1 Hz.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 54-54)

**Notes**:

Settled position C-17 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-157 — Ring-bound enforced in the handler, NOT the drain callback.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 56-56)

**Notes**:

Settled position C-19 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-158 — RISK: Security: CSWSH closed.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-159 — SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 41-41)

**Notes**:

Settled position C-04 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-160 — server_instance_id = programmatic key; server_start_time = advisory only.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 43-43)

**Notes**:

Settled position C-06 from R3-03 table; cross-round consensus consolidation

### JR-CAN-WS-003 — WebSocket /ws endpoint exception handling must be complete with proper cleanup in finally block.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 130-144)

**Detail**:

HIGH-010: Endpoint will be substantially rewritten in R5-01 Phase 0-cascor + Phase B-pre-a/b.
Current finally block is minimal stopgap; acceptable interim but do NOT over-invest in hardening.
Will implement two-phase registration, frame size caps, per-IP caps, origin validation, CSRF auth, rate limiting.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; deferred until R5-01 phases complete.

### JR-ML-WS-161 — WebSocket fallback to REST for set_params on connection/timeout errors.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 354-382)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CAN-WS-004 — WebSocket relay state callback must include current_epoch and other training fields in broadcast.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_66a019dc-94ba-47fb-8042-7ce8f974d071.md` (lines 311-380)

**Detail**:

Relay only sends status and phase; omits current_epoch, metrics_history, parameters.
Causes stale state data in /api/state endpoint and incomplete WebSocket state updates.

**Notes**:

Identified by all 7 Phase 3 proposals. MODERATE severity, not a display blocker.

### JR-DAT-WS-001 — IPC architecture (gRPC, message queue, shared memory, WebSocket) deferred until REST bottleneck or >100MB datasets.

**Status**: deferred  **Priority**: P3  **Category**: WS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 438-465)

**Notes**:

[v2 ARCH→WS re-bucket] RD-015 (DATA-018). Deferred. REST migration success reduced urgency.

### JR-CAN-WS-005 — Architectural fragility: WebSocket relay broadcasts unnormalized metric field names (ISS-11).

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 541-553)

**Detail**:

ISS-11 LOW. WebSocket relay loop (cascor_service_adapter.py:203-206) broadcasts cascor raw metrics messages without applying _normalize_metric(). CasCor sends loss/accuracy/validation_loss/validation_accuracy; REST path normalizes to train_loss/train_accuracy/val_loss/val_accuracy. Currently non-functional (dashboard doesn't consume WebSocket — ISS-03). Becomes active bug if ISS-03 addressed — REST and WebSocket paths would deliver metrics with different field names.

**Notes**:

[v2 ARCH→WS re-bucket] Identified by v4, v7. Latent until ISS-03 fixed.

### JR-CAS-WS-006 — Documentation generation: CLI setup guide (Claude Code + Serena MCP configuration, auto-start, troubleshooting).

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/setup_config_guides/claude-code-serena-setup-guide.md` (lines 1-100)

**Detail**:

Native installer for Claude Code (no Node.js required), uvx for Serena (from GitHub), global MCP server configuration with --project-from-cwd auto-detection, validation procedures (claude doctor, /mcp status check), troubleshooting (uvx path, Serena startup, port 24282, PATH resolution). File locations: ~/.local/bin/claude, ~/.claude/settings.json, ~/.claude.json. Per-project configuration alternative. Documentation complete with 8 sections and reference tables.

### JR-CAN-WS-006 — Training WebSocket must validate message size to prevent DoS.

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 243-243)

**Detail**:

Issue 5.3.2: WebSocket message handler does not check message size.
Add check: reject messages > 1MB with log and graceful disconnect.
