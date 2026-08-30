# Requirements — status: proposed

**Total entries**: 1445

**By priority**: P0=123 | P1=524 | P2=724 | P3=74

**By category**: ARCH=275 | SEC=191 | WS=157 | OBS=151 | API=123 | TEST=106 | TRAIN=106 | UI=85 | TOOL=58 | DEP=53 | DOC=46 | DATA=40 | PERF=30 | OPS=16 | LOCK=8

**By owner**: ml=1119 | can=180 | cas=74 | dep=26 | ccl=17 | dat=14 | dcl=10 | cwk=4 | rec=1

---

### JR-ML-ARCH-001 — **Blocks**: All releases, deployments, and downstream development.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md` (lines 25-97)
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md` (lines 24-96)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 1:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md

---

[v3 brief repaired from cited content; was: 'Phase 1:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-002 — **Prerequisite**: Phase 1 (training must work for connection to matter).

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md` (lines 100-127)
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md` (lines 99-126)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 2:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md

---

[v3 brief repaired from cited content; was: 'Phase 2:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-SEC-014 — [ ] WebSocket relay normalized and consumed by dashboard — relay normalization is COMPLETE (P5-RC-14, `cascor_service_adapter.py:222`);….

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 664-714)

**Detail**:

- [x] Demo and service backends return structurally identical data — `demo_backend.apply_params()` standardized to `{ok, data}` envelope to match service backend; other methods already converged (verified 2026-04-10)

**Notes**:

[v3 brief repaired from cited content; was: '6.4 Phase 4 Success Criteria']

### JR-ML-ARCH-003 — [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase via PR #61).

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md` (lines 51-100)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 1:'] From JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md

### JR-ML-SEC-015 — `_accuracy` assumes one-hot encoded targets — broken for `output_size=1`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 803-821)

### JR-ML-SEC-016 — `ActivationWithDerivative.__setstate__` silently falls back to ReLU for unrecognized activation names.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 746-766)

### JR-DEP-OBS-001 — Add juniper_cascor_training_sessions_completed_total counter with closed-set outcome labels.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 808-827)

**Detail**:

juniper_cascor_training_sessions_completed_total does not exist as of 2026-05-03.
Cascor currently exposes only training_sessions_active (Gauge) and training_epochs_total (Counter).
Recommendation: add counter with closed-set outcome ∈ {success, error, aborted} bumped from
training-loop completion handler. ~50 lines, R5.4 PR or separate R5.5a sub-track.

### JR-ML-DATA-001 — Add missing generator constants: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 433-442)

**Detail**:

| 3 | juniper-data-client | Update `FakeDataClient._GENERATOR_CATALOG` to match server registry                           |

**Notes**:

[v4 brief repaired; was: '8.1 Critical (Fix Immediately)']

### JR-ML-SEC-017 — `add_unit` initializes new hidden unit output weights with random values instead of zero.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 718-746)

**Detail**:

Add an `init_output_weights` flag with enumerated values including, but not necessarily limited to, the following: zero and random.
    The flag should be used to determine output node initialization behavior: using `torch.zeros` for the new row(s) vs `toch.randn * 0.1`.
    The flag should have defaults defined in appropriate constants class and local config files.
    Flag default should be accessed by juniper-cascor durring all network initialization locations in the code.
    The flag value

### JR-ML-DEP-002 — Aggregate Results.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 14-28)

**Detail**:

| juniper-ml            | 0.3.0   | 88 pass          | N/A (meta) | 16/16 pass   | 1        | 4      | 3      | 8      |

### JR-ML-OBS-007 — align between docker-compose and k8s deployments; `pending_tasks`.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 260-275)

**Detail**:

**Scope**: Verify alert/dashboard/scrape configs are technically correct.

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Dimension B — PromQL + scrape correctness']

### JR-ML-SEC-018 — All WebSocket endpoints must enforce per-frame size limits: training 4 KB inbound, control 64 KB.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 145-180)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 681-703)

**Detail**:

Cascor training_stream.py: max_size=4096 on receive.
Cascor control_stream.py: maintain 64 KB cap (regression test).
Canopy /ws/training and /ws/control: audit every receive_*() call; add max_size parameter per control table.

**Notes**:

M-SEC-03 (P0). Must precede Phase B per R1-03. Phase B-pre-a (Day 5 of runbook).

### JR-CAN-SEC-001 — API key validation must use hmac.compare_digest() to prevent timing attacks.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 43-43)

**Detail**:

Issue 0.1.2: Replace string 'in' operator with constant-time comparison.
File: src/security.py

### JR-ML-ARCH-004 — Applications Affected.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 411-421)

**Notes**:

[v4 brief repaired; was: 'By Severity']

### JR-ML-TEST-001 — `batch_update_tags`: `if add_tags:` truthiness check means `add_tags=[]` (empty list) omits key from payload. Server may interpret absence d.

**Status**: proposed  **Priority**: P0  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 220-229)

**Detail**:

| ID        | Severity     | File:Line                       | Description

**Notes**:

[v4 brief repaired; was: '4.1 Bugs']

### JR-ML-ARCH-005 — **Blocks**: All downstream canopy monitoring fixes.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 10-46)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 1:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

### JR-CAN-SEC-002 — CallbackContextAdapter must be thread-safe via contextvars.ContextVar.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 50-50)

**Detail**:

Issue 0.2.1: Replace instance attributes with contextvars.ContextVar to ensure
thread isolation. File: src/frontend/callback_context.py

### JR-ML-SEC-019 — Canopy and Cascor must validate WebSocket Origin header against configurable allowlist; reject null origins and wildcards.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 100-145)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 489-550)

**Detail**:

Cascor: new src/api/websocket/origin.py with validate_origin(ws, allowlist) → bool.
Rules: case-insensitive scheme+host, exact port, strip trailing slash, reject null origin, no wildcard support.
Canopy: mirror implementation in src/backend/ws_security.py (do not cross-import).
Cascor default: [http://localhost:8201, https://localhost:8201, http://127.0.0.1:8201, https://127.0.0.1:8201]
Canopy default: [http://localhost:8050, https://localhost:8050, http://127.0.0.1:8050, https://127.0.0.1:8050]

**Notes**:

M-SEC-01 (canopy), M-SEC-01b (cascor). RISK-15 CSWSH mitigation. Env var JUNIPER_WS_ALLOWED_ORIGINS. Phase B-pre (Day 4).

### JR-ML-UI-001 — Canopy dashboard must implement WS-aware polling toggle: skip /api/metrics/history polling when connected.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 250-350)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1087-1159)

**Detail**:

Refactor _update_metrics_store_handler (dashboard_manager.py:2388-2421) to read ws-connection-status via State.
If ws_status.connected: return no_update (WS driving).
Else if (n % 10) != 0: return no_update (slow fallback to 1 Hz).
Else: call /api/metrics/history?limit=1000.
Apply same pattern to _handle_training_state_poll, _handle_candidate_progress_poll, _handle_topology_poll.

**Notes**:

GAP-WS-16, GAP-WS-25. Bandwidth elimination dependent on extendTraces. Phase B (Day 9). Acceptance criterion: <400 KB over 10s.

### JR-ML-UI-002 — Canopy dashboard must implement ws_dash_bridge.js ring buffers and drain callbacks for live WebSocket metrics.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 970-1045)

**Detail**:

New src/frontend/assets/ws_dash_bridge.js (~200 lines): module-scope closure with on(type, ...) handlers
(metrics, state, topology, cascade_add, candidate_progress) and onStatus(...).
Typed JS ring buffers: MAX_METRICS_BUFFER=1000, MAX_EVENT_BUFFER=500.
Bound-in-handler invariant: every push does splice-to-cap (load-bearing for RISK-12).
Expose ONE global: window._juniperWsDrain with drainMetrics, drainState, drainTopology, drainCascadeAdd, drainCandidateProgress, peekStatus, _introspect.
rAF coalescer scaffold disabled per R0-01 disagreement #1 (_scheduleRaf noop, commented structure).
Try-catch wrapper on every handler (FR-RISK-10).

**Notes**:

GAP-WS-04, GAP-WS-05. Bound-in-handler cap non-negotiable per R0-01 §3.2.5. rAF disabled. Phase B (Day 8).

### JR-ML-UI-003 — Canopy metrics panels must migrate from full figure replace to Plotly.extendTraces clientside callback.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 150-250)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1049-1158)

**Detail**:

Metrics panel: new dcc.Store(id='metrics-panel-figure-signal') for clientside callback.
Clientside callback: Input ws-metrics-buffer.data, State metrics-panel-figure-signal.data.
Extract epochs/losses/accs/vlosses/vaccs from buffer_data.events.
Call Plotly.extendTraces("metrics-panel-figure", update, [0,1,2,3,4], 5000).
Guard with document.getElementById('metrics-panel-figure') check (FR-RISK-02).
Wrap in try-catch (FR-RISK-10).
Mirror for candidate_metrics_panel with maxPoints=5000.
Initial figure layout must have uirevision="metrics-panel-v1" (prevents pan/zoom reset).

**Notes**:

GAP-WS-14. P0 bandwidth kill (3 MB/s→<400 KB over 10s). Dummy output pattern per R0-01 §3.3.4. Phase B (Day 9).

### JR-ML-SEC-020 — Canopy must implement cookie-session + CSRF first-frame validation before accepting WebSocket connections.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 145-230)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 604-705)

**Detail**:

Canopy src/main.py: add SessionMiddleware with secret_key from env JUNIPER_CANOPY_SESSION_SECRET.
New /api/csrf endpoint returns {"csrf_token": ...}, mints on first request, rotates hourly.
/ws/training and /ws/control: after accept, receive_json(timeout=5.0) for first frame.
First frame must be type="auth" with csrf_token matching session token (hmac.compare_digest).
On failure: close code 4001 "Authentication failed".
Frontend: inject window.__canopy_csrf in layout, send auth frame immediately in websocket_client.js onopen.

**Notes**:

M-SEC-02 (P0). CSWSH second-line defense. Env var JUNIPER_CANOPY_SESSION_SECRET. Phase B-pre (Day 5).

### JR-CAN-UI-001 — Canopy should not mutate incoming broadcast messages in websocket_manager.broadcast().

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 75-75)

**Detail**:

Issue 1.1.3: broadcast() currently mutates message dicts in-place.
Must pass immutable copy or deep clone before modification.

### JR-ML-OBS-008 — `CanopyDashboardAvailabilitySlowBurn`, `CanopyRenderLatencySlowBurn`, `CascorTrainJobSuccessSlowBurn`, `CascorTrainStepLatencySlowBurn`, `Da.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 446-456)

**Notes**:

[v4 brief repaired; was: '7.1 Rules by severity label']

### JR-ML-SEC-021 — `CascadeCorrelationNetwork._roll_sequence_number` stores all discarded values in a list.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 628-648)

### JR-ML-WS-001 — Cascor bounded 1024-entry replay buffer for lossless reconnect.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 81-131)

### JR-ML-SEC-022 — CasCor distributed training must enforce TLS encryption, worker authentication, multi-tier protection, and comprehensive data validation.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 370-393)

**Detail**:

SR-1/2/3: Protect network, workers, and primary from threats. SR-5: TLS for all in-transit data. SR-6: Worker authentication. SR-7: Data validation.

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

### JR-CAS-TRAIN-010 — Cascor must implement mini-batch training for the output-layer trainer to support larger datasets and reduced memory footprint.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md` (lines 19-54)

**Detail**:

Currently cascor trainers are full-batch end-to-end. Proposed restoration adds config knobs:
- `use_mini_batch` (default True)
- `mini_batch_size` (sane default TBD)
Candidate-unit trainer intentionally NOT mini-batched (Pearson correlation needs full-batch stats).
Estimated 3-4 PRs, Tier-2 effort.

### JR-ML-TRAIN-008 — CasCor remote workers must support dynamic joining/leaving, tolerate intermittent connections, and provide task redistribution on failure.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 329-360)

**Detail**:

FR-1: Workers connect before/after training. FR-3: Tolerate intermittent connections. FR-6: Dynamic join/leave during rounds. FR-7: Automatic task redistribution on worker failure.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

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

### JR-ML-SEC-023 — Cassandra referenced in docs but not in compose file.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 328-341)

**Notes**:

[v4 brief repaired; was: '4.3 Issues Identified']

### JR-ML-SEC-024 — Coverage tests bypass actual `fit()` method to avoid timeouts — false coverage confidence.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 969-1002)

**Detail**:

Both Option A and Option B.
    Option A will allow accurate, critical code path coverage checks with non-limiting runtimes.
    Option B will allow the more rigorous checks needed for this application critical code path.

### JR-DEP-OBS-002 — Create Grafana dashboards for CasCor training, Data throughput, and Canopy requests.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 75-119)

**Detail**:

Phase 1 (v0.2.0) observability hardening. Three new dashboards: (1) cascor-training.json
with epoch progress, loss, hidden unit additions, latency histogram; (2) data-service.json
with generation rate, request count by endpoint, response time percentiles, error rate;
(3) canopy-requests.json with HTTP rate, WS connections, response codes, page load times.
Dashboard provider already watches provisioning directory; new JSON files auto-load.

### JR-DEP-OBS-003 — Create Prometheus alerting rules for health, latency, error rate, and restart loop.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 111-119)

**Detail**:

Phase 1. Create prometheus/alerts.yml with recording and alerting rules: service health
endpoint down > 2 min, request error rate > 5%, P95 latency > 2s, container restart loop.
Wire into prometheus/prometheus.yml via rule_files directive. Add Grafana alert contact
point configuration to provisioning.

### JR-ML-SEC-025 — Critical deployment gap. The worker is the only distributed component that runs on remote machines but has zero deployment infrastructure:.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 396-414)

**Detail**:

**Critical deployment gap.** The worker is the only distributed component that runs on remote machines but has zero deployment infrastructure:

**Notes**:

[v3 brief repaired from cited content; was: '6.2 juniper-cascor-worker']

### JR-ML-TEST-002 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 48-53)

**Detail**:

**C-ML-1: Missing git tags for v0.2.1 and v0.3.0**

### JR-ML-SEC-026 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 115-131)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 287-298)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 350-355)

**Detail**:

**C-JD-1: Version mismatch across 4 files:**

*Merged from 3 extraction candidates (slices: 3c-2b).*

### JR-ML-API-002 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 176-187)

**Detail**:

**C-JDC-1: Version doesn't reflect API changes**

### JR-ML-DEP-003 — Critical startup/shutdown fixes (plant/chop scripts).

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 280-289)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 216-225)

**Notes**:

[v4 brief repaired; was: '9.1 Completed Phases']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-API-003 — Cross-Cutting Themes.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 28-41)

**Detail**:

1. **Changelog debt is universal**: Every application has significant undocumented changes. This is the single most common blocker.

### JR-ML-SEC-027 — CSWSH (Cross-Site WebSocket Hijacking) attack must be closed by Origin allowlist + CSRF first-frame.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 450-520)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 489-550)

**Detail**:

First line: M-SEC-01 (Origin allowlist) lands Day 4.
Second line: M-SEC-02 (CSRF first-frame) lands Day 5.
Combined mitigation closes RISK-15 per R0-02 §10.1.
M-SEC-01 alone blocks third-party page from initiating; M-SEC-02 blocks cross-site session hijacking.
Origin validation must happen pre-accept (fail-closed).

**Notes**:

RISK-15 (High). Mandatory close per R1-03 as page-on-call alert, not ticket. Phase B-pre (Days 4-5).

### JR-CAN-API-001 — Dataset-tab edits do not change running training data; missing dataset-swap endpoint and param-map gap prevent user control of cascor dataset.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 39-42)

**Detail**:

Phase 1 fix: add cascor dataset-swap endpoint + Cancel button for cold swap (cold-swap + Cancel button). Phase 2: live in-flight swap behind experimental-functions gate with two-step warning modal and History/Snapshots/Replay persistence.

**Notes**:

Separate detailed spec in ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md

### JR-CAN-UI-002 — Dataset-tab edits don't persist—Phase 1 cold-swap with Cancel button, Phase 2 live in-flight swap.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 38-42)

**Detail**:

Phase 1: add Cancel button, cold-swap via canopy adapter + cascor endpoint.
Phase 2 (separate doc): live dataset swap behind experimental-functions gate,
two-step warning modal, History/Snapshots/Replay persistence.

**PRs**: PR-7 (Phase 1, Issue, PR-series P2-1 to P2-7 (Phase 2 live swap, documented separately)

**Notes**:

See ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md for full Phase 2 spec.
Shares root cause with Issue #1.

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

### JR-ML-DEP-004 — **Deployment artifacts**: None (no Dockerfile, no systemd, no scripts).

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 127-152)

**Detail**:

- **Type**: Pure HTTP client library

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Per-Client/Worker Inventory']

### JR-ML-SEC-028 — Duplicate forward-pass logic in `train_output_layer` vs `forward()`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 821-841)

### JR-ML-SEC-029 — Early stopping patience state not propagated between `grow_network` iterations.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 591-628)

### JR-CAN-SEC-003 — Exception handler must suppress internal details; log full stack server-side only.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 45-45)

**Detail**:

Issue 0.1.3: Return generic message to client, preserve full exception in
server-side logs only. Prevents information disclosure.

### JR-CAS-ARCH-001 — Extract duplicated ActivationWithDerivative class to shared module to prevent divergence in ACTIVATION_MAP.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 144-157)

**Detail**:

Class defined identically in cascade_correlation.py:291 and candidate_unit.py:138.
If ACTIVATION_MAP diverges between copies, deserialized objects behave differently.
Fix: extract to shared module (e.g., src/utils/activation.py) and import from both.
Codebase validation CONFIRMED duplicate at lines 291 and 138.

### JR-ML-DATA-002 — `FakeDataClient` masks generator name bugs — accepts invalid names

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 479-488)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 387-396)

**Notes**:

[v4 brief repaired; was: '15.2 juniper-data-client']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DEP-005 — **File**: [`alertmanager/alertmanager.yml`](https://github.com/pcalnon/juniper-deploy/blob/main/alertmanager/alertmanager.yml) (cross-repo).

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 97-126)

**Detail**:

- **Status**: open — operational gap

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Alertmanager `tickets` receiver placeholder']

### JR-ML-OBS-009 — **File**: [`notes/SLO_CATALOG_2026-05-03.md`](https://github.com/pcalnon/juniper-deploy/blob/main/notes/SLO_CATALOG_2026-05-03.md)….

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 70-97)

**Detail**:

- **Status**: open (30-day soak underway)

**Notes**:

[v3 brief repaired from cited content; was: '3.1 SLO catalog target calibration against soak-window data']

### JR-CAS-TOOL-001 — Fix ./try convenience script path resolution errors in helper scripts.

**Status**: proposed  **Priority**: P0  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 201-252)

**Detail**:

Helper scripts (GET_OS_SCRIPT, GET_PROJECT_SCRIPT, DATE_FUNCTIONS_SCRIPT) are overridden as bare filenames. Fix to use absolute paths derived from BASH_SOURCE[0]. Update conf/script_util.cfg to correctly compute ROOT_PROJECT_DIR with proper project hierarchy.

### JR-CAN-API-002 — Fix /ws exception handling infinite loop in main.py.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 73-73)

**Detail**:

Issue 1.1.1: WebSocket route exception handling loop. Must exit cleanly
on expected errors (client disconnect) without retry loop.
File: src/main.py

### JR-DEP-OPS-001 — Fix critical AGENTS.md documentation errors: Grafana password, rate limiting defaults.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 9-26)

**Detail**:

Phase 1 (P0 priority, blocks other work). Step 1.1: Replace GRAFANA_ADMIN_PASSWORD
default 'admin' with GF_SECURITY_ADMIN_PASSWORD__FILE referencing Docker secret.
Step 1.2: Update JUNIPER_CASCOR_RATE_LIMIT_ENABLED and CANOPY_RATE_LIMIT_ENABLED
defaults from false to true (matches docker-compose.yml).

### JR-DCL-DOC-001 — Fix flake8 line-length command in AGENTS.md from 120 to 512.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 37-45)

**Detail**:

AGENTS.md commands section specifies --max-line-length=120, but the project standard is 512.
This discrepancy causes agents to produce false positives against actual project linting rules.
The parent CLAUDE.md explicitly states line-length 512 for all linters (ecosystem standard).
Fix: Update AGENTS.md Quick Reference > Essential Commands section.

**Notes**:

Also appears in AGENTS_MD_UPDATE_ROADMAP (Task 1.2) and AGENTS_MD_UPDATE_PLAN (Step 1.2).

### JR-CAS-ARCH-002 — Fix invalid CandidateUnit constructor parameters in fit() method - all parameters silently absorbed by kwargs.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-24.md` (lines 100-110)

**Detail**:

Lines 1154-1166: fit() passes 11 parameters with `_CandidateUnit__` prefix (wrong mangling
style) instead of `CandidateUnit__`. All absorbed by **kwargs. CandidateUnit created with
ALL default values, ignoring user's activation function, input size, output size, learning
rate, etc. WORSE than documented - affects all training in fit() path.

### JR-CAN-UI-003 — Fix metaparameter edits that silently drop 14 of 29 keys without reaching cascor backend.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 56-162)

**Detail**:

Root causes: incomplete adapter mapping, no roundtrip verification.
Three sub-parts: (C1) surface drops to user, (C2) extend cascor PATCH endpoints,
(C3) roundtrip verification. Includes candidate-pool invariants atomic validation.

**PRs**: PR-1 (Phase 6A series, Issue

**Notes**:

Blocks Issue

### JR-CAN-API-003 — Fix metrics format mismatch: flatten nested dashboard metrics contract (metrics.loss, metrics.accuracy) to match service mode output.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Dashboard reads nested metrics (metrics.loss, metrics.accuracy); service-mode adapter emits flat structure. Critical display blocker for metrics charts.

**Notes**:

P5-RC-01; critical display blocker; part of final synthesis

### JR-CAN-UI-004 — Fix network topology format mismatch: convert weight-oriented CasCor structure to graph-oriented visualizer contract.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Service-mode emits weight-oriented topology (input_size, hidden_units: [...]) while visualizer expects graph-oriented structure (input_units, connections). Critical display blocker.

**Notes**:

P5-RC-02; critical display blocker; part of final synthesis

### JR-DCL-DOC-002 — Fix __version__ in juniper_data_client/__init__.py from 0.3.1 to 0.3.2 to match pyproject.toml.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 24-32)

**Detail**:

The __init__.py __version__ string (0.3.1) is out of sync with pyproject.toml (0.3.2).
This is a code bug affecting any code or consumer that reads juniper_data_client.__version__.
Fix: Update juniper_data_client/__init__.py line 10 to __version__ = "0.3.2"

**Notes**:

Also appears in AGENTS_MD_UPDATE_ROADMAP (Task 1.1) and AGENTS_MD_UPDATE_PLAN (Step 1.1).

### JR-CAS-ARCH-003 — Fix walrus operator precedence bug in train_output_layer() that assigns boolean instead of snapshot path.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 128-141)

**Detail**:

Line 1322: `if snapshot_path := self.create_snapshot() is not None:` is parsed as
`snapshot_path := (self.create_snapshot() is not None)`. snapshot_path always assigned
True/False, not actual path. Log message prints 'True'. Fix: add parentheses
`if (snapshot_path := self.create_snapshot()) is not None:`.
Codebase validation (2026-02-18) CONFIRMED.

### JR-ML-SEC-030 — Global singleton initialization race in `get_api_key_auth()` and `get_rate_limiter()`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 330-362)

### JR-ML-WS-011 — H-JCW-2: Thread-unsafe `asyncio.Event.set()` from signal handler.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 298-306)

**Detail**:

**H-JCW-1: `worker.py` at 68.23% coverage**

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-SEC-031 — Hidden unit activation function not wrapped in `ActivationWithDerivative` after HDF5 deserialization.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 700-718)

### JR-ML-OBS-010 — Impact. The juniper-data dashboard panel "Cached Datasets".

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 787-826)

**Detail**:

**Finding.** The metric `juniper_data_datasets_cached` (Gauge, no labels)

**Notes**:

[v3 brief repaired from cited content; was: '15.1 `juniper_data_datasets_cached` is defined-and-emitted i']

### JR-ML-DATA-003 — **Impact**: `FakeDataClient` masks this — unit tests pass but real server requests fail with 400

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 324-340)

**Detail**:

**Impact**: `FakeDataClient` masks this — unit tests pass but real server requests fail with 400.

**Notes**:

[v3 brief repaired from cited content; was: '6.1 Critical: Generator Name Mismatch (XREPO-01 — confirmed ']

### JR-ML-SEC-032 — `InlineDataset` allows unbounded array sizes in training start request.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 571-591)

### JR-ML-OBS-011 — Items identified from cross-referencing WebSocket messaging architecture reviews against implementation status.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 257-280)

**Detail**:

## 9. Microservices and Infrastructure

**Notes**:

[v3 brief repaired from cited content; was: '8.3 Critical Individual Gaps (from WebSocket Architecture Re']

### JR-ML-PERF-001 — JS ring buffers must cap at bound on every push (not in drain callback) to enforce memory invariant.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 550-600)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 976-982)

**Detail**:

ws_dash_bridge.js: bound-in-handler invariant—every push does splice-to-cap (MAX_METRICS_BUFFER=1000, etc).
Load-bearing for RISK-12: DO NOT move the cap into the drain callback.
Ensures memory is bounded even if drain callback is never called or crashes.

**Notes**:

R0-01 §3.2.5 load-bearing. Non-negotiable. Phase B (Day 8). Memory safety for long-running dashboards.

### JR-ML-SEC-033 — juniper-data P0: path traversal fix in csv_import with JUNIPER_DATA_IMPORT_DIR validation.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-DEVELOPMENT-ROADMAP.md` (lines 25-40)

### JR-ML-SEC-034 — Key Categories of Missing Items.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 594-614)

**Detail**:

| Active Bugs (cascor)   | 3         | `TrainingMonitor.current_phase` never updated, uninitialized variable crash    |

### JR-ML-OBS-012 — Low Priority (Future Phases).

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 375-408)

**Detail**:

| Phase 5: Observability & Hardening | MICROSERVICES_STARTUP_CODE_REVIEW | AlertManager receivers, alert rules, health standardization                 |

### JR-CAN-API-004 — Metaparameter edits in Dashboard never reach cascor; adapter drops 14 of 29 form keys silently without verification or user feedback.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 57-120)

**Detail**:

Apply Parameters posts 29 keys but _CANOPY_TO_CASCOR_PARAM_MAP maps only 16. Silent drops: 6 candidate-pool params + 7 NN/dataset params. No roundtrip verification; user sees 'Parameters applied' lie. Recommendation: Option C (staged C1→C2→C3): surface dropped keys, extend cascor PATCH endpoints, add roundtrip verification.

**Design**:

C1: adapter warning toast + skipped list propagation. C2: cascor PATCH endpoints for candidate-pool selection. C3: roundtrip GET cascor /v1/training/params and diff against requested.

**Notes**:

Root cause: incomplete param-map gap + no roundtrip verification. Candidate-pool selection is most user-facing, making silent drop the worst residual.

### JR-ML-API-004 — No error-path tests for batch endpoints via real client (only FakeDataClient).

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 239-246)

**Detail**:

- **Critical**: FakeDataClient accepts `"circle"` and `"moon"` — masks the server mismatch. All unit tests pass but would fail against real server.

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Test Coverage Gaps']

### JR-ML-SEC-035 — `_NoOpLogger` session fixture masks logging-related bugs in production code.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1022-1040)

### JR-CAS-PERF-001 — Optimize tensor serialization overhead in parallel candidate training via shared memory blocks.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/OPT5_SHARED_MEMORY_PLAN.md` (lines 1-32)

**Detail**:

OPT-5 eliminates redundant tensor serialization by sharing training tensors via
named POSIX shared memory. Currently each of N candidates sends same tensors through
queue. ForkingPickler already sends handles (~340 bytes) but GET-side reconstruction
costs ~320us (same-process) to ~9ms (cross-process). For 16 candidates, ~100-145ms
overhead per round. Using multiprocessing.shared_memory.SharedMemory creates named
block, workers attach by name. Expected improvement: 5-20% total round time reduction.

### JR-ML-ARCH-006 — **P0: polling eliminated**.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 145-146)

### JR-ML-OBS-013 — P2 — Quality / correctness (real but lower-impact).

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 380-391)

**Detail**:

| **A.5** | juniper-cascor | `juniper_cascor_inference_*` (counter + histogram) dead → 4 dashboard panels show flat zeros | Wire `record_inference()` if cas

### JR-CAN-SEC-004 — Phase 0 Addendum—Add threading.Lock to TrainingStateMachine.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 258-260)

**Detail**:

HIGH-015: Thread-safe locking required in backend training state machine.
File: src/backend/training_state_machine.py

### JR-CAN-SEC-005 — Phase 0 Pre-Release Security Blockers (6 vulnerabilities).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 30-61)

**Detail**:

0.1.1: Fix path traversal in snapshot endpoints via regex + resolve() check.
0.1.2: Fix timing attack in API key validation via hmac.compare_digest().
0.1.3: Suppress internal exception details; log server-side, return generic message.
0.1.4: Fix rate limiter memory leak with periodic eviction + size cap (10k entries).
0.2.1: Fix thread-unsafe CallbackContextAdapter via contextvars.ContextVar.
0.2.2: Fix threading.Event replacement race with clear() instead of reassign.

### JR-CAN-API-005 — Phase 1 Release-Critical Quality (15 tasks across API, config, frontend).

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 64-101)

**Detail**:

Step 1.1 (7 tasks): Fix /ws exception loop, enforce max_connections, stop
broadcast() mutation, remove duplicate cn_patience, define set_params Pydantic model,
handle malformed Content-Length, restrict CORS.
Step 1.2 (5 tasks): Centralize version, update app_config.yaml/pyproject.toml headers,
use get_settings() in get_rate_limiter(), fix CORS YAML syntax.
Step 1.3 (3 tasks): Replace _api_url() with settings-based, fix screenshot timestamp,
deduplicate accuracy plot logic.

### JR-ML-OBS-014 — Phase 1: Critical Bug Fixes (OI-1 + OI-4) — COMPLETE.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 644-658)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-SEC-036 — Phase 1: Critical Fixes (P0) -- COMPLETED.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 714-732)

**Detail**:

**Goal**: Make existing host-mode startup/shutdown reliable.

### JR-ML-SEC-037 — Phase 1: Critical Startup/Shutdown Fixes — ✅ COMPLETE (commit `03aec86`).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 228-243)

**Detail**:

| 1.1  | `wait_for_health()` function — polls `/v1/health` with configurable timeout | ✅ Implemented |

### JR-ML-WS-012 — Phase A-server cascor prerequisites for browser WebSocket migration.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 931-1016)

### JR-ML-OPS-001 — Phase B-pre gate (after Day 6) requires 8 criteria: all M-SEC-NN landed, audit logger, 24h staging, risk sheet.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-06-OPS-PHASING-RISK.md` (lines 79-110)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 850-870)

**Detail**:

1. M-SEC-01 landed (Day 4)
2. M-SEC-01b landed (Day 4)
3. M-SEC-02 landed (Day 5)
4. M-SEC-03 landed (Day 5)
5. M-SEC-04 + M-SEC-05 + M-SEC-10 landed (Day 6)
6. Audit logger exporting counters
7. Staging deployment ≥ 24h (calendar-day gap recommended)
8. Runbook published + RISK-15 marked "in production" in risk tracking sheet

**Notes**:

All 8 must be true before Phase D PR eligible. Per R0-06 §3.2. Non-parallelizable gate.

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

### JR-ML-OPS-002 — Publish v7.0.1 hotfix to roadmap with verified fixes and shipped CAN-015g/h work.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md` (lines 232-242)

### JR-ML-DEP-006 — PyPI packages can be yanked (not deleted) if critical issues found post-release.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 394-412)

**Detail**:

- All git tags can be deleted and recreated: `git tag -d v<VERSION> && git push --delete origin v<VERSION>`

**Notes**:

[v3 brief repaired from cited content; was: 'Rollback Plan']

### JR-CAN-PERF-001 — Rate limiter must evict expired entries periodically to prevent memory leak.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 47-49)

**Detail**:

Issue 0.1.4: Add _evict_expired() method with periodic cleanup.
Emergency size cap: 10,000 entries. File: src/security.py

### JR-CAS-TRAIN-011 — Remove hardcoded absolute path from remote_client_0.py that points to obsolete prototype directory.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 176-189)

**Detail**:

Line 16: sys.path.append("/home/pcalnon/Development/python/Juniper/src/prototypes/cascor/src")
Points to old prototype location. Will fail on any other machine. Also note INT-P2-009:
inconsistent queue names between remote_client.py and remote_client_0.py.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-ARCH-004 — Remove hardcoded absolute paths in test file for cross-platform portability.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 192-205)

**Detail**:

src/tests/unit/test_candidate_training_manager.py lines 10,12 contain hardcoded paths
to prototype directories (Linux and macOS). Will cause import failures and raise
EnvironmentError on Windows. Fix: replace with dynamic path resolution using
os.path.dirname(__file__).

### JR-ML-SEC-038 — `_save_hidden_units` reads activation function name incorrectly from `ActivationWithDerivative` wrapper.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 785-803)

### JR-ML-SEC-039 — `SharedTrainingMemory` shape descriptor only supports tensors up to 2D.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 766-785)

**Detail**:

Immedidately, add validation check rejecting `ndim > 2` with a clear error message.
    - The capacity to allow `ndim > 2` should be documented as an enhancement and added to the development plan.  This feature is required for using some alternate datasets and for the hierarchical network enhancement.

### JR-DEP-OBS-004 — Ship Prometheus burn-rate alerting rules derived from SLO targets with MWMBR pattern.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 102-140)

**Detail**:

Implement Multi-Window Multi-Burn-Rate alerts for the 5 user-facing SLOs (§3).
Fast-burn (5m/1h @ 14.4×) and mid-burn (30m/6h @ 6×) page on-call.
Slow-burn (2h/24h @ 3×) and long-burn (6h/72h @ 1×) create tickets only.
Internal-supporting SLIs (§4) emit log-only-severity alerts with same MWMBR shape.

### JR-CAN-TRAIN-001 — Single-iteration auto-pause after stop+reset due to cleared _pause_event.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 42-42)

**Detail**:

cascor lifecycle manager leaves _pause_event cleared after reset().
Fix: one-line change to clear+set instead of reassign.

**PRs**: PR-5 (cascor fix, ordered first in remediation)

### JR-CAN-TRAIN-002 — Single-iteration auto-pause after stop+reset; reset() leaves _pause_event cleared, preventing pause on next iteration.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 43-43)

**Detail**:

Fix: cascor lifecycle manager (1 line). reset() must preserve _pause_event state or re-initialize it correctly.

**Notes**:

Affects training flow control.

### JR-ML-SEC-040 — Step 6: PR and Worktree Cleanup.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 162-203)

**Detail**:

| `src/frontend/dashboard_manager.py` | UI layout, callback handlers |

### JR-CAN-SEC-006 — Threading.Event replacement race must use clear() instead of reassignment.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 52-53)

**Detail**:

Issue 0.2.2: In demo_mode.py, use _stop.clear() instead of _stop = Event()
to avoid TOCTOU race. File: src/demo_mode.py

### JR-ML-SEC-041 — Three receivers, all SMTP email per OBS-ROUTE-01 (juniper-deploy#60).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 539-558)

**Detail**:

| `default` | `alerts-default@example.com` | **PLACEHOLDER** (`CHANGE_BEFORE_PRODUCTION_USE` flagged) |

**Notes**:

[v3 brief repaired from cited content; was: '9.1 Receivers']

### JR-ML-SEC-042 — Tracks PID in `STARTED_PIDS` array for failure cleanup.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 152-202)

**Detail**:

**Location**: `juniper-ml/util/juniper_plant_all.bash` (319 lines)

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Current State: `juniper_plant_all.bash`']

### JR-ML-SEC-043 — Triple random seeding in `conftest.py` creates confusing test infrastructure.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1076-1176)

### JR-ML-SEC-044 — `unit.get("activation_fn", torch.sigmoid).__name__` returns `"ActivationWithDerivative"` not the underlying function name.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 256-283)

**Detail**:

| CC-01 | **Critical** | `api/websocket/messages.py`       | 72–79   | `create_topology_message()` exists but is never called — topology changes not broadcast via WS                            |

**Notes**:

[v4 brief repaired; was: '2.1 juniper-cascor']

### JR-CCL-DOC-001 — Update AGENTS.md version from 0.1.0 to 0.3.0 to match current package state.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 20-28)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 11-13)

**Detail**:

AGENTS.md declares version 0.1.0 but actual package version is 0.3.0. Misleads agents about
codebase maturity and feature set (missing testing submodule, worker API, snapshot API, dataset API).

**Notes**:

Critical severity: marked P0 as blocking (misleads agents about codebase state)

### JR-CCL-DOC-002 — Update AGENTS.md: correct flake8 line length from 120 to 512 (blocker — agents produce incorrect output).

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 46-46)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 16-17)

**Detail**:

The AGENTS.md file incorrectly specifies flake8 --max-line-length=120, while pyproject.toml and
.pre-commit-config.yaml both specify 512 per Juniper ecosystem standard. This causes agents to
produce false-positive linting failures.

**Notes**:

Critical severity: marked P0 as blocking (agents produce incorrect output)

### JR-ML-SEC-045 — `validate_pid()` checks `/proc/<pid>` exists and logs `/proc/<pid>/cmdline`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 208-243)

**Detail**:

**Location**: `juniper-ml/util/juniper_chop_all.bash` (226 lines)

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Current State: `juniper_chop_all.bash`']

### JR-ML-SEC-046 — `validate_training` has no early stopping path when validation data is absent.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 680-700)

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

### JR-ML-SEC-047 — WebSocket control stream documents `set_params` command but does not implement it.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 227-260)

### JR-ML-SEC-048 — `WebSocketManager` `_active_connections` set lacks explicit async synchronization.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 459-490)

### JR-ML-OBS-015 — When the cascade correlation network adds a hidden unit, no WebSocket message is broadcast to connected clients. The `cascade_add` message….

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 57-93)

**Detail**:

**Repositories**: juniper-cascor, juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '1.1 WebSocket Topology Broadcast Gap']

### JR-ML-OBS-016 — Who/what closes it.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 699-721)

**Detail**:

- **CALIB-01** (P3) — recommended action: a single calibration PR

### JR-ML-OBS-017 — Wire Alertmanager default and tickets receivers (email via Gmail SMTP) to unblock SLO program close-out by 2026-06-02.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 132-142)

**Detail**:

G2 - Alertmanager receivers silently drop alerts routed to default/tickets.
Both receivers exist as no-op placeholders. Soft blocker before 2026-06-02 soak-close.
Recommend Option A: Email-via-Gmail SMTP for both (use existing SOPS-encrypted creds).

### JR-ML-SEC-049 — **Wire up topology broadcast**: Register a `topology_change` callback in `TrainingLifecycleManager._install_monitoring_hooks()` that calls `.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 523-533)

**Detail**:

1. **Wire up topology broadcast**: Register a `topology_change` callback in `TrainingLifecycleManager._install_monitoring_hooks()` that calls `create_topology_message()` and broadcasts

**Notes**:

[v4 brief repaired; was: '7.1 Immediate (Critical/High)']

### JR-ML-ARCH-007 — ├── severity=warning  → tickets  (group_by adds severity, group_wait=2m, repeat_interval=24h)  # B.1 fold-in.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 558-569)

**Detail**:

route: receiver=default, group_by=[alertname,service], group_wait=30s, group_interval=5m, repeat_interval=4h

**Notes**:

[v3 brief repaired from cited content; was: '9.2 Route tree']

### JR-ML-API-008 — /api/v1/training/status returns snapshot_seq + server_instance_id atomically.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 117-117)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-024 — /ws/control handler returns protocol-error envelopes, echoes command_id, NO seq on command_response.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 120-120)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-TRAIN-018 — 0-cascor: `git revert` P1.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 342-343)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-019 — 0-cascor: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 339-340)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-020 — 0-cascor: `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 340-341)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-021 — 0-cascor: Rolling cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 341-342)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-OBS-024 — 01: Dual metric format removed aggressively.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 375-376)

**Notes**:

[v2 ARCH→OBS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-041 — 02: Phase B clientside_callback hard to debug.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 376-377)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-042 — 03: Phase C REST+WS ordering race.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 377-378)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-043 — 04: Slow-client blocks broadcasts.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 378-379)

### JR-ML-TEST-006 — 05: Playwright misses real-cascor regression.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 379-380)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TRAIN-022 — 06: Reconnection storm after cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 380-381)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-044 — 07: 50-conn cap hit (multi-tenant).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 381-382)

### JR-ML-ARCH-045 — 08: Demo mode parity breaks.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 382-383)

### JR-ML-ARCH-046 — 09: Phase C unexpected behavior.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 383-384)

### JR-ML-ARCH-047 — 10: Browser memory exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 384-385)

### JR-ML-TRAIN-023 — 11: Silent data loss via drop-oldest.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 385-386)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-UI-010 — 12: Background tab memory spike.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 386-387)

**Notes**:

[v2 ARCH→UI re-bucket]

### JR-ML-ARCH-048 — 13: Orphaned commands after timeout.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 387-388)

### JR-ML-TRAIN-024 — 14: Cascor crash mid-broadcast.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 388-389)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-WS-025 — 15: **CSWSH attack**.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 389-390)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-049 — --: Mid-week deploys for behavior-changing flag flips only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 300-301)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-050 — --: Minimum-viable carveout ~7 days (P0 only).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 301-302)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-025 — --: Phase 0-cascor staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 295-296)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-051 — --: Phase B staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 296-297)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-052 — --: Phase B-pre-b staging soak = 48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 297-298)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-053 — --: Phase C flag-flip canary >= 7 days production data.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 299-300)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-054 — --: Phase D entry gate = B-pre-b in production >=48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 298-299)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-055 — **Prerequisite**: Phase 2 (connection must work for UI to receive data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md` (lines 130-203)
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md` (lines 129-202)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 3:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md

---

[v3 brief repaired from cited content; was: 'Phase 3:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-SEC-060 — [ ] Training Metrics: progress bars show grow iteration and candidate epoch during training.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 314-329)

**Detail**:

- [ ] Training Metrics: progress bars show grow iteration and candidate epoch during training

**Notes**:

[v3 brief repaired from cited content; was: '8.3 Visual Verification Checklist']

### JR-ML-TRAIN-026 — [x] **Status**: ✅ Fixed (2026-04-03 — branch `fix/regression-phase2-cascor`, PR #62).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md` (lines 103-153)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: 'Phase 2:'] From JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md

### JR-ML-TRAIN-027 — A-SDK: Downgrade cascor-client pin.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 343-344)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-056 — A-SDK: PyPI yank.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 344-345)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-CAN-UI-011 — Accuracy plot phase band logic must be deduplicated.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 93-93)

**Detail**:

Issue 1.3.3: Repeated phase-band visualization logic in metrics_panel.py.
Extract to shared helper. File: src/frontend/components/metrics_panel.py

### JR-CCL-DOC-005 — Add Architecture section to AGENTS.md documenting class hierarchy, API categories, exception hierarchy, design patterns.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 152-154)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 51-56)
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 112-118)

**Detail**:

Document class hierarchy (JuniperCascorClient, CascorTrainingStream, CascorControlStream),
API method categories (health, network, training, metrics, data, snapshots, workers),
exception hierarchy (7 exception classes), design patterns (context manager, callback/observer, retry, envelope).

**Notes**:

[v3 xrepo fuzzy merge: owners=ccl,dcl, n=2] High severity: agents have no guidance on codebase structure / Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.1) and AGENTS_MD_UPDATE_PLAN (Step 3.1).

### JR-ML-WS-026 — Add async set_params() method to CascorControlStream for WebSocket parameter control.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 94-150)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CAN-TEST-008 — Add browser-automation UI test sub-suite with dedicated CI lane.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 45-46)

**Detail**:

No browser automation harness exists. Create pytest sub-suite with ≤5 min
wall-clock budget via parallel jobs, caching, and slow marker. Skeleton
in Phase 4 step 1, full coverage in Phase 4 step 2.

**PRs**: PR-4.1 (skeleton with basic page loads), {'PR-4.2 (full coverage': 'param Apply, dataset swap, snapshot restore)'}

### JR-CAS-ARCH-005 — Add connection retry logic with exponential backoff for JuniperData REST client.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 313-326)

**Detail**:

Client has no retry logic, connection pooling, or circuit breaker. Transient network
error crashes entire pipeline. Fix: add retry with exponential backoff (urllib3.Retry
or tenacity).

### JR-ML-OBS-025 — Add dashboard/alert lint lane to juniper-deploy CI.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 284-290)

**Detail**:

Cross-cutting recommendation: Add CI guardrail to prevent future stale panels.
Run promtool check rules on alert_rules.yml and recording_rules.yml.
JSON-schema validate each dashboard and promtool query instant against synthetic Prometheus.

### JR-CCL-DOC-006 — Add Directory Layout section to AGENTS.md documenting complete directory tree with annotations.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 152-154)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 48-49)

**Notes**:

High severity: required by directives for agent codebase orientation

### JR-DCL-DOC-003 — Add directory structure section to AGENTS.md showing full repository layout.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-56)

**Detail**:

AGENTS.md lacks any description of the directory structure. Must document complex layout including:
juniper_data_client/, juniper_data_client/testing/, tests/, docs/, notes/, scripts/, util/,
.github/workflows/, conf/ with annotations for each directory's purpose.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.1) and AGENTS_MD_UPDATE_PLAN (Step 2.1).

### JR-ML-OBS-026 — Add `get_dataset_data()` method to `src/api/lifecycle/manager.py`:.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 151-187)

**Detail**:

result = {"train_x": self._train_x.detach().cpu().tolist(),

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Fix — Phase 2: Cross-Repo Dataset Data Endpoint']

### JR-CAN-TEST-009 — Add integration test suite for real CasCor backend code paths with mocked CascorIntegration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 191-207)

**Detail**:

conftest.py forces CASCOR_DEMO_MODE=1 for all tests; no test exercises cascor_integration paths. Would have caught INT-CRIT-001/002/003.

**Notes**:

Phase 2 high priority; must test control, topology, metrics, statistics, decision boundary, snapshots

### JR-DEP-DEP-001 — Add juniper-cascor-worker service to docker-compose.yml under full profile.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 154-180)

**Detail**:

Phase 3 (v0.4.0) worker integration. Add juniper-cascor-worker service with build context
../juniper-cascor-worker, environment variables (CASCOR_SERVICE_URL, WORKER_ID, WORKER_LOG_LEVEL).
Attach to backend bridge network (same as cascor). Add depends_on: juniper-cascor: condition: service_healthy.
Define health check endpoint or process check. Add deploy.replicas for horizontal scaling (default 1).
Add WORKER_REPLICAS env var for override. Document scaling in README.

### JR-DEP-DEP-002 — Add juniper.target and per-service systemd unit files with dependency ordering.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 89-165)

**Detail**:

juniper.target groups all services. juniper-data.service runs first (MemoryMax=2G, CPUQuota=200%).
juniper-cascor.service depends on data (MemoryMax=8G, CPUQuota=400%). juniper-canopy.service
wants cascor softly (falls back to demo mode). All use ExecStartPost wait_for_health.sh gate.
Security hardening: NoNewPrivileges=true, ProtectSystem=strict, ProtectHome=read-only.

### JR-ML-TEST-007 — Add macOS CI matrix leg to all repos for cross-platform coverage (rss_mb sampling, POSIX assumptions).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 75-125)

**Detail**:

R3.7 Resolution: Use macos-latest (ARM); run all unit tests (not integration/perf); start in continue-on-error mode for 2 weeks, then make required.

**Notes**:

macOS-13 (Intel) removed as deprecated.

### JR-CAN-WS-002 — Add missing fields to WebSocket relay state callback (current_epoch, current_step, learning_rate, max_hidden_units, max_epochs, network_name, timestamp).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 261-290)

**Detail**:

ISS-02 MODERATE. WebSocket relay state callback (cascor_service_adapter.py:218-225) only forwards status and phase to global training_state. CasCor state messages also contain current_epoch, current_step, learning_rate, max_hidden_units, max_epochs, network_name, timestamp — all discarded. TrainingState.update_state() accepts **kwargs and can handle these fields. Result: /api/state reads from training_state.get_state() with stale epoch/step data after initial sync (though status bar makes fresh REST calls, bypassing staleness).

**Notes**:

Currently latent because status bar makes fresh REST calls. Mitigating factor masks the bug in production but architectural risk remains.

### JR-CAS-API-006 — Add requests as declared dependency in pyproject.toml - currently undeclared but used by JuniperDataClient.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 229-242)

**Detail**:

JuniperDataClient imports requests but not listed in pyproject.toml or documented
in CLAUDE.md. Will fail on fresh installs. Add to dependencies and document.

### JR-DEP-SEC-001 — Add reverse proxy (Traefik or Caddy) with TLS termination to production profile.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 135-152)

**Detail**:

Phase 2. Proxy service in production profile terminates TLS; services communicate
over plaintext on internal networks. Support both self-signed certificates (dev)
and Let's Encrypt (production). Expose only ports 443 (HTTPS) and optionally 80
(redirect) on host.

### JR-ML-SEC-061 — Add security hardening to check_doc_links.py including universal bounds checking, input validation, and traversal depth limits.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-07_JUNIPER-ECOSYSTEM_CROSS-REPO-LINK-RESOLUTION-PROPOSAL.md` (lines 813-920)

**Detail**:

Existing vulnerability: filesystem existence oracle via crafted links like ../../../../etc/passwd.

Required fixes:
1. Universal bounds check - constrain resolved paths to repo/ecosystem root using Path.is_relative_to()
2. Input validation - reject null bytes and absolute paths before path construction
3. Traversal depth limit - reject links with >5 ../ segments
4. Structural validation in skip mode - ensure cross-repo links don't escape target repo

### JR-ML-SEC-062 — Add security logging remediation across Juniper services.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECURITY_LOGGING_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Audit trail and incident response capability.

### JR-ML-API-009 — Add startup health verification to Canopy**: When `CASCOR_SERVICE_URL` is set, perform an HTTP GET to the CasCor health endpoint during….

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 627-655)

**Detail**:

- cascor_service: reachable / unreachable / demo_mode

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Health Check Pattern Recommendation']

### JR-ML-TRAIN-028 — Add to `_STATE_FIELDS`:.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 491-505)

**Detail**:

**Effort**: 1 day | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '5.1 Define Progress Fields in TrainingState']

### JR-CAS-ARCH-006 — Add try/except guard around SpiralDataProvider import for graceful degradation when requests unavailable.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 297-310)

**Detail**:

Line 505: lazy import transitively imports requests. If requests not installed,
fails with ModuleNotFoundError even when JUNIPER_DATA_URL set. Add try/except
with clear error message.

### JR-ML-SEC-063 — Additional Findings from CasCor Validation.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 54-66)

**Detail**:

1. **`create_topology_message()` is dead code in juniper-cascor** — The message builder exists in `api/websocket/messages.py` (line 35) and is exported in `__init__.py`, but no production code path ever calls it. CasCor only sends `cascade_add` event messages (with event metadata, no topology data).

### JR-ML-SEC-064 — `add_units_as_layer` stores numpy copies of weights in history.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 895-913)

### JR-ML-WS-027 — Adopt WebSocket-based remote worker architecture (Approach A) with phased rollout through Phase 4.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 1496-1520)

**Detail**:

Phases: 1a security fixes, 1b WebSocket endpoint, 2 remote agent, 3 unified distributor, 4 hardening.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-TEST-008 — Align CI/pre-commit across 8 repos to common baseline: same union of workflows, hooks, pre-commit config.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-PIPELINE-ALIGNMENT-PLAN.md` (lines 28-42)

### JR-ML-DEP-013 — All items 🔴 NOT STARTED.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 235-251)

**Detail**:

| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Microservices Architecture Roadmap (Phases 5–9)']

### JR-ML-OBS-027 — All items 🔴 NOT STARTED unless otherwise noted.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 203-237)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 158-192)

**Detail**:

## 8. WebSocket Migration (R5-01 Remaining Phases)

**Notes**:

[v3 brief repaired from cited content; was: '7.1 Canopy Enhancement Backlog (CAN-000 through CAN-021)']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DEP-014 — All items 🔴 NOT STARTED unless otherwise noted.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 299-315)

**Detail**:

| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Microservices Architecture Roadmap (Phases 5–9)']

### JR-ML-OBS-028 — All services use HTTP health probes with proper intervals, timeouts, and retry counts.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 313-328)

**Detail**:

| **Dependency ordering** | `depends_on` with `condition: service_healthy` ensures proper startup sequence        |

**Notes**:

[v4 brief repaired; was: '4.2 Strengths']

### JR-ML-SEC-065 — All three tasks validated by specialized sub-agents (2026-03-29):.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 354-366)

**Detail**:

- `network_visualizer.py` — uses count-based positioning, not numeric `layer` field

**Notes**:

[v3 brief repaired from cited content; was: '9.4 Files NOT Requiring Modification']

### JR-ML-UI-011 — All WebSocket JS handlers must wrap body in try-catch to prevent single exception from breaking dashboard.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 500-550)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 981-991)

**Detail**:

ws_dash_bridge.js: every on(type, ...) handler body wrapped in try { ... } catch (e) { console.error('[ws_dash_bridge]', e); }.
Clientside callback for extendTraces: try { ... } catch (e) { return window.dash_clientside.no_update; }.
Prevents exceptions from hanging callback chain.

**Notes**:

FR-RISK-10. Phase B (Day 8-9). Defensive coding for dashboard stability.

### JR-ML-API-010 — All WebSocket message envelopes must include optional seq field and preserve backward compatibility.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-03-MAXIMALIST-COMPREHENSIVE.md` (lines 194-240)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 262-282)

**Detail**:

Message builders add optional seq: int | None = None parameter.
seq serializes as top-level field when present; omitted when None (backward compat).
Every message type (state, metrics, topology, etc.) flows through _assign_seq_and_append.
Cascade client that does not understand seq field must still function (field is optional in parsers).

**Notes**:

Phase A-server (Day 2). Backward compatibility non-negotiable. Unknown fields must be ignored per schema.

### JR-CAS-API-007 — API defaults extraction and normalization: 49 constants for API layer (network models, lifecycle, observability, security, endpoints).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/HARDCODED_VALUES_ANALYSIS.md` (lines 200-300)

**Detail**:

New cascor_constants/constants_api/ submodule with constants_api_defaults.py (43 constants). Network defaults: input_size=2, output_size=2, learning_rate=0.01, candidate_learning_rate=0.005, max_hidden_units=10, candidate_pool_size=8, correlation_threshold=0.1, patience=5, candidate_epochs=50, output_epochs=25, epochs_max=200, max_iterations=1000, init_output_weights='zero'. Lifecycle: 8 manager defaults. Observability: 4 logging/Sentry config. Service launcher: 3 timeouts. Middleware/routes: HTTP codes, resolution bounds. App URLs: JuniperData, Canopy, health checks. Validation tests required to prevent constants/settings drift.

**Notes**:

[v2 remap: SE→API]

### JR-CAN-DOC-002 — Application version must be centralized via importlib.metadata.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 83-83)

**Detail**:

Issue 1.2.1: Version string currently duplicated across health, status, and
config endpoints. Use importlib.metadata as single source of truth.
File: src/main.py

### JR-ML-ARCH-057 — Audit async route handlers; ensure all blocking I/O wrapped in asyncio.to_thread().

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-AUDIT-HOOK-MIGRATION-PLAN.md` (lines 1-50)

### JR-ML-ARCH-058 — `audit_log_enabled`: B-pre-a.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 315-316)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-059 — B-pre-a: `JUNIPER_AUDIT_LOG_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 349-350)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-060 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS='*'`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 347-348)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-061 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS=<broader>`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 346-347)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-062 — B-pre-a: `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 348-349)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-063 — B-pre-a: `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 345-346)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-064 — B-pre-b: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 351-352)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-065 — B-pre-b: `JUNIPER_WS_RATE_LIMIT_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 352-353)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-066 — B-pre-b: `JUNIPER_WS_SECURITY_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 350-351)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-067 — B: Hardcoded ring-cap reduction.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 355-356)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-068 — B: `JUNIPER_DISABLE_WS_BRIDGE=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 354-355)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-069 — B: `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 353-354)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-070 — B: URL `?ws=off` diagnostic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 356-357)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-028 — Background _recv_task started on connect; parses inbound, pops future by command_id, set_result(envelope).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 219-219)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-TEST-010 — Bandit configuration must be consolidated to single file.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 121-121)

**Detail**:

Issue 2.2.1: Multiple bandit config files (.bandit, .pre-commit hook, CI).
Consolidate to .bandit and reference from all invocation points.

### JR-CAN-TEST-011 — Bandit invocations across all CI workflows must be consistent.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 122-122)

**Detail**:

Issue 2.2.2: bandit runs in pre-commit, CI, and manual invocations with
varying flags. Standardize command and flags across all paths.

### JR-ML-SEC-066 — Binary: `[[0.0],[1.0]]` -> `[0,1]` (threshold, not argmax).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 302-314)

**Detail**:

| `test_dataset_target_conversion_binary`             | Binary: `[[0.0],[1.0]]` -> `[0,1]` (threshold, not argmax) |

**Notes**:

[v4 brief repaired; was: '8.2 New Tests Required']

### JR-DEP-OBS-008 — Bridge juniper_cascor_pending_tasks gauge from worker coordinator queue depth to Prometheus.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 510-532)

**Detail**:

R4.4 worker heartbeat SLO (§4.1) is resolved via WorkerRegistryCollector. But §4.2
(pending-task queue depth) still requires a juniper_cascor_pending_tasks gauge from the
worker coordinator. Small cascor sub-track to add to existing WorkerRegistryCollector,
populated from coordinator's pending-task queue depth.

### JR-ML-OBS-029 — broadcast_from_thread adds Task.add_done_callback(_log_exception) (GAP-WS-29).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 119-119)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

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

### JR-ML-ARCH-071 — BUG-CC-01: `create_topology_message()` Not Fully Implemented.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 536-561)

### JR-ML-ARCH-072 — BUG-CC-02: `cascade_add` Correlation Hardcoded to `0.0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 564-578)

### JR-ML-ARCH-073 — BUG-CC-03: `or` Fallback Bugs for Falsy Values in spiral_problem.py.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 581-595)

### JR-ML-ARCH-074 — BUG-CC-04: Version Strings Inconsistent Across File Headers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 598-612)

### JR-ML-ARCH-075 — BUG-CC-05: `remote_client_0.py` Hardcoded Old Monorepo Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 615-641)

### JR-ML-ARCH-076 — BUG-CC-06: 32 Test Files Have Hardcoded `sys.path.append` to Old Monorepo.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 644-658)

### JR-ML-ARCH-077 — BUG-CC-07: `TrainingMonitor.current_phase` Never Updated by State Machine.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 661-675)

### JR-ML-ARCH-078 — BUG-CC-08: Undeclared Global `shared_object_dict`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 678-692)

### JR-ML-ARCH-079 — BUG-CC-09: `validate_training_results` Uninitialized Variable When `max_epochs=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 695-709)

### JR-ML-ARCH-080 — BUG-CC-10: `validate_training` Validation Variables Not Initialized for No-Validation-Data Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 712-726)

### JR-ML-ARCH-081 — BUG-CC-11: Walrus Operator Precedence Bug in `utils.py`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 729-743)

### JR-ML-ARCH-082 — BUG-CC-12: `load_dataset` Uses `yaml.safe_load` Instead of `torch.load`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 746-779)

### JR-ML-ARCH-083 — BUG-CC-13: `RateLimiter._counters` Never Pruned — Unbounded Memory Growth.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 782-796)

### JR-ML-ARCH-084 — BUG-CC-14: `HandshakeCooldown._rejections` Never Pruned for Non-Blocked IPs.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 799-813)

### JR-ML-ARCH-085 — BUG-CC-15: `RequestBodyLimitMiddleware` Reads Full Body Before Size Check.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 816-830)

### JR-ML-ARCH-086 — BUG-CC-16: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 833-841)

### JR-ML-OBS-030 — BUG-CC-17: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 844-852)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-087 — BUG-CC-18: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 855-863)

### JR-ML-ARCH-088 — BUG-CN-01: `_stop.clear()` Race — `_perform_reset()` Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 868-882)

### JR-ML-ARCH-089 — BUG-CN-02: DashboardManager God Class (3,232 Lines).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 885-907)

### JR-ML-ARCH-090 — BUG-CN-03: 226 `hasattr` Guards in Tests Skip Test Logic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 910-924)

### JR-ML-ARCH-091 — BUG-CN-04: `_api_base_url` Hardcoded to `127.0.0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 927-941)

### JR-ML-ARCH-092 — BUG-CN-05: Service Populate Param Values with Int Defaults.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 944-958)

### JR-ML-ARCH-093 — BUG-CN-06: 1 Hz State Throttle Drops Terminal Transitions.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 961-976)

### JR-ML-ARCH-094 — BUG-CN-07: Duplicate `APP_VERSION` Assignment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 979-993)

### JR-ML-ARCH-095 — BUG-CN-08: `_demo_snapshots` List Grows Unbounded in Demo Mode.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 996-1010)

### JR-ML-ARCH-096 — BUG-CN-09: `WebSocketManager.active_connections` Not Thread Safe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1013-1027)

### JR-ML-ARCH-097 — BUG-CN-10: `message_count` Increment Not Atomic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1030-1044)

### JR-ML-ARCH-098 — BUG-CN-11: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1047-1055)

### JR-ML-ARCH-099 — BUG-CN-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1058-1066)

### JR-ML-ARCH-100 — BUG-JD-01: `batch_export` Builds Entire ZIP in Memory — OOM Risk.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1071-1093)

### JR-ML-ARCH-101 — BUG-JD-02: `delete()` TOCTOU Race Condition.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1096-1110)

### JR-ML-ARCH-102 — BUG-JD-03: `update_meta` Writes Without Temp File — Partial Data Exposure.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1113-1127)

### JR-ML-ARCH-103 — BUG-JD-04: Deterministic IDs with `seed=None` → Stale Cache Returns.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1130-1144)

### JR-ML-ARCH-104 — BUG-JD-05: `_version_lock` Is Class Variable — Won't Work Across Workers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1147-1169)

### JR-ML-ARCH-105 — BUG-JD-06: `ReadinessResponse.timestamp` Uses Naive `datetime.now()`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1172-1186)

### JR-ML-ARCH-106 — BUG-JD-07: `record_dataset_generation()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1189-1203)

### JR-ML-ARCH-107 — BUG-JD-08: `record_access()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1206-1220)

### JR-ML-OBS-031 — BUG-JD-09: High-Cardinality Prometheus Labels from Parameterized Routes.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1223-1237)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-108 — BUG-JD-10: ALL Storage Operations Block Async Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1240-1248)

### JR-ML-ARCH-109 — BUG-JD-11: `record_access` TOCTOU Race on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1251-1259)

### JR-ML-ARCH-110 — C-01: Correlation field is `command_id`, NOT `request_id` -- every repo, every test.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 228-229)

### JR-ML-WS-031 — C-02: `command_response` has NO `seq` field; `/ws/control` has no replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 229-230)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-111 — C-03: `set_params` default timeout = 1.0 s (not 5.0 s).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 230-231)

### JR-ML-ARCH-112 — C-04: SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 242-243)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-032 — C-05: Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 243-244)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-113 — C-06: `server_instance_id` = programmatic key; `server_start_time` = advisory only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 231-232)

### JR-ML-ARCH-114 — C-07: `replay_buffer_capacity` added to `connection_established`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 232-233)

### JR-ML-ARCH-115 — C-08: Two-phase registration via `_pending_connections` set.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 233-234)

### JR-ML-TRAIN-029 — C-09: Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 234-235)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-030 — C-10: Adapter->cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 256-257)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-033 — C-11: GAP-WS-19 `close_all` lock is RESOLVED on main; regression test only.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 257-258)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-031 — C-12: Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 268-269)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-116 — C-13: Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 269-270)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-117 — C-14: Phase B ships behind two flags: `enable_browser_ws_bridge` (False->True post-soak) + `disable_ws_bri.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 270-271)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-PERF-002 — C-15: Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`).

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 271-272)

**Notes**:

[v2 ARCH→PERF re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-118 — C-16: rAF coalescer scaffolded but DISABLED (`enable_raf_coalescer=False`).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 272-273)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-119 — C-17: REST fallback cadence during disconnect = 1 Hz (NOT 100 ms).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 244-245)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-034 — C-18: `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 245-246)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-120 — C-19: Ring-bound enforced in the handler (NOT the drain callback); AST lint enforces.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 246-247)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-035 — C-20: GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 273-274)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-121 — C-21: NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 274-275)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-122 — C-22: `_normalize_metric` dual-format contract preserved forever; CODEOWNERS hard gate in Phase H.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 275-276)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-123 — C-23: REST endpoints preserved FOREVER -- no deprecation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 247-248)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-124 — C-24: Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 258-259)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-125 — C-25: One-resume-per-connection rule (second resume -> close 1003).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 248-249)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-126 — C-26: Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 259-260)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-127 — C-27: **`ws_security_enabled=True` (positive sense)**, NOT `disable_ws_auth`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 260-261)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-128 — C-28: Phase C flag `use_websocket_set_params=False` default; 6 hard flip gates.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 276-277)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-129 — C-29: Debounce lives in Dash clientside callback (NOT SDK), 250 ms.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 249-250)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-130 — C-30: `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 250-251)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-131 — C-31: Shadow traffic: rejected.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 261-262)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TEST-009 — C-32: Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 282-283)

**Notes**:

[v2 ARCH→TEST re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-132 — C-33: Per-command HMAC deferred indefinitely.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 262-263)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TEST-010 — C-34: Contract-test pytest marker `contract` runs on every PR in all 3 repos.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 283-284)

**Notes**:

[v2 ARCH→TEST re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-PERF-003 — C-35: Latency tests are recording-only in CI; strict assertions local-only.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 284-285)

**Notes**:

[v2 ARCH→PERF re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-133 — C-36: Total effort: 13.5 target / 15.75 planning buffer / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 294-295)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-OBS-032 — C-37: P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 285-286)

**Notes**:

[v2 ARCH→OBS re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-134 — C-38: Observability-before-behavior rule: metrics + panels + alerts before the behavior change.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 286-287)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-135 — C-39: Kill switch MTTR <=5 min, CI-tested, staging-drilled; untested switch is not a switch.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 287-288)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-136 — C-40: Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 235-236)

### JR-ML-WS-036 — C-41: `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 236-237)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-137 — C-42: Error-budget burn-rate rule operationally binding (if 99.9% budget burns in <1 day, freeze non-relia.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 288-289)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-138 — C: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 357-358)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-139 — C: `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 358-359)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-CAN-ARCH-001 — CallbackContextAdapter must use contextvars.ContextVar for thread-safe and async-safe test mode isolation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` (lines 99-143)

**Detail**:

CRIT-002 concurrency vulnerability: instance attributes in CallbackContextAdapter not thread-safe.
Current fix (contextvars) implemented correctly; recommendation reinforced to use ContextVar pattern.

**Notes**:

CODE_REVIEW_ANALYSIS v0.4.0; fixed with contextvars.ContextVar in alignment with R5-01 philosophy.

### JR-ML-WS-037 — Caller-cancellation cleans correlation map entry in finally.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 221-221)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-API-011 — Canonical settings table: 25+ configuration variables across cascor/canopy with env vars, types, defaults, validation.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R4-01-COMPREHENSIVE-MASTER-PLAN.md` (lines 212-242)

**Detail**:

Settings with Pydantic Field(..., description=...). Cascor: ws_replay_buffer_size (int, 1024, env JUNIPER_WS_REPLAY_BUFFER_SIZE, validation >=0),
ws_send_timeout_seconds (float, 0.5, JUNIPER_WS_SEND_TIMEOUT_SECONDS, >0), ws_state_throttle_coalesce_ms (int, 1000, JUNIPER_WS_STATE_THROTTLE_COALESCE_MS, >0),
ws_resume_handshake_timeout_s (float, 5.0, JUNIPER_WS_RESUME_HANDSHAKE_TIMEOUT_S, >0), ws_pending_max_duration_s (float, 10.0, JUNIPER_WS_PENDING_MAX_DURATION_S, >0),
ws_max_connections_per_ip (int, 5, JUNIPER_WS_MAX_CONNECTIONS_PER_IP, >=1), ws_allowed_origins (list[str], [], JUNIPER_WS_ALLOWED_ORIGINS, no '*'),
ws_idle_timeout_seconds (int, 120, JUNIPER_WS_IDLE_TIMEOUT_SECONDS, >=0), ws_backpressure_policy (Literal, drop_oldest_progress_only, JUNIPER_WS_BACKPRESSURE_POLICY, enum).
Canopy: ws_security_enabled (bool, True, JUNIPER_WS_SECURITY_ENABLED, bool; CI refuses False in prod), ws_max_connections_per_ip (int, 5, JUNIPER_CANOPY_WS_MAX_CONNECTIONS_PER_IP, >=1),
ws_allowed_origins (list[str], localhost defaults, JUNIPER_CANOPY_WS_ALLOWED_ORIGINS, no '*'), ws_rate_limit_enabled (bool, True, JUNIPER_WS_RATE_LIMIT_ENABLED, bool),
ws_rate_limit_cps (int, 10, JUNIPER_WS_RATE_LIMIT_CPS, >=1), audit_log_enabled (bool, True, JUNIPER_AUDIT_LOG_ENABLED, bool),
audit_log_path (str, /var/log/canopy/audit.log, JUNIPER_AUDIT_LOG_PATH, path), audit_log_retention_days (int, 90, JUNIPER_AUDIT_LOG_RETENTION_DAYS, >=1),
disable_ws_control_endpoint (bool, False, JUNIPER_DISABLE_WS_CONTROL_ENDPOINT, bool), enable_browser_ws_bridge (bool, False→True, JUNIPER_ENABLE_BROWSER_WS_BRIDGE, bool),
disable_ws_bridge (bool, False, JUNIPER_DISABLE_WS_BRIDGE, bool), enable_raf_coalescer (bool, False, JUNIPER_ENABLE_RAF_COALESCER, bool),
enable_ws_latency_beacon (bool, True, JUNIPER_ENABLE_WS_LATENCY_BEACON, bool), use_websocket_set_params (bool, False, JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS, bool),
ws_set_params_timeout (float, 1.0, JUNIPER_WS_SET_PARAMS_TIMEOUT, >0), enable_ws_control_buttons (bool, False, JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS, bool),
disable_ws_auto_reconnect (bool, False, JUNIPER_DISABLE_WS_AUTO_RECONNECT, bool).
CI assert: every setting documented, every env var round-trips.

**Design**:

Pydantic BaseModel with Field(..., description=...) for documentation. Type-safe validation on load.
env var naming: JUNIPER_<SETTING_UPPER> for cascor, JUNIPER_CANOPY_<SETTING_UPPER> or JUNIPER_<SETTING_UPPER> for canopy (varies by context).

**Notes**:

[v2 ARCH→API re-bucket] Central to Phase execution. All settings present before merge. CI lint enforces documentation + round-trip.

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

### JR-CAN-API-010 — Canopy must enforce max_connections limit in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 74-74)

**Detail**:

Issue 1.1.2: Currently no enforcement of max_connections. Must track active
connection count and reject new clients when limit reached.

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

### JR-ML-OBS-033 — Canopy must implement JSON audit logger for WebSocket control commands with scrubbing and CRLF escaping.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 250-320)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 800-846)

**Detail**:

New src/backend/audit_log.py: canopy.audit logger with JSON formatter, TimedRotatingFileHandler(when="midnight", backupCount=90).
AUDIT_SCRUB_ALLOWLIST auto-derived from SetParamsRequest.model_fields.keys().
audit_log.ws_control(event, ...): logs session_id hash, remote_addr, origin, endpoint, command, request_id, params_keys,
params_scrubbed (before/after), result, seq per R0-02 §4.6 rules 1-11.
CRLF escape every user-controlled field at write-time.
audit_log.ws_auth(...) for auth/origin/cookie failures.
Settings: audit_log_path, audit_log_retention_days.

**Notes**:

IMPL-SEC-32..35. Configurable path and retention. Phase B-pre (Day 6). M-SEC-10 consolidation per R1-03.

### JR-CAN-API-011 — Canopy must normalize cascor ResponseEnvelope format at adapter boundary, transforming metrics, topology, and dataset responses to dashboard-compatible shapes.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 131-175)

**Detail**:

Add centralized normalization methods to CascorServiceAdapter: _unwrap_envelope(), _normalize_metric(), _normalize_metrics_history(), _normalize_topology(), _normalize_dataset(), _normalize_status(). All methods are static; normalization occurs once at adapter boundary.

**Design**:

DemoBackend is the reference implementation. ServiceBackend must produce identical response shapes. Pattern: ResponseEnvelope → unwrap → normalize → dashboard-compatible dict.

**Notes**:

Root cause of metrics display failure in service mode. Phase 1 plan addressed envelope unwrapping but did not establish dashboard-compatibility contract.

### JR-ML-SEC-067 — Canopy WebSocket handlers must enforce 120s idle timeout; close with code 1000 on expiry.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 320-360)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 813-821)

**Detail**:

Wrap receive_text() main loop in asyncio.wait_for(..., timeout=120) on both /ws/training and /ws/control.
On asyncio.TimeoutError, close with 1000 "Normal Closure".
Heartbeat from Phase F will reset timer (safe because it ships later but idle timeout defensible alone).
IMPL-SEC-30 checkpoint.

**Notes**:

IMPL-SEC-30. Idle timeout does not force disconnect during long polling; only closes on true inactivity. Phase B-pre (Day 6).

### JR-ML-OBS-034 — canopy work was already implemented in the months between the 2026-04-08.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 451-491)

**Detail**:

roadmap snapshot and Phase 3 execution. The only real gap was the demo backend,

**Notes**:

[v3 brief repaired from cited content; was: '5.0 Phase 3 Execution Results (2026-04-09)']

### JR-ML-SEC-068 — Cascor /ws/control must enforce per-connection command rate limit (leaky bucket, 10/sec).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 210-250)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 786-810)

**Detail**:

New src/api/websocket/rate_limit.py: per-connection leaky bucket, capacity 10, refill 10/sec.
control_stream_handler consumes 1 token per command frame.
On empty bucket: reply {"type": "command_response", "data": {"status": "rate_limited", "retry_after": 0.3}}.
Do NOT close on rate limit; allow client to retry.
One-resume-per-connection micro-control: in training_stream resume handler, record connection-scoped resumed_once.
Second resume frame closes with 1003.

**Notes**:

M-SEC-05 (P1), IMPL-SEC-29. Phase B-pre (Day 6).

### JR-ML-WS-040 — Cascor /ws/control protocol error responses per GAP-WS-22.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 916-928)

### JR-CAS-API-008 — CasCor backend must expose prediction method accepting arbitrary input grids for visualization.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 687-691)

**Notes**:

Required for JuniperCanopy decision boundary visualization.

### JR-ML-WS-041 — Cascor backpressure handling with 0.5s per-send timeout (quick fix).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 454-525)

### JR-ML-WS-042 — Cascor command_id echo in control responses for per-command correlation.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 821-915)

### JR-ML-API-012 — CasCor has the training tensors in memory (`_train_x`, `_train_y`) but its `/v1/dataset`.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 128-137)

**Detail**:

`ServiceBackend.get_dataset()` (service_backend.py:155-168) returns metadata only. The

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Root Cause']

### JR-ML-SEC-069 — Cascor must enforce per-IP WebSocket connection limit (default 5) to mitigate connection exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 180-210)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 774-798)

**Detail**:

WebSocketManager.__init__: self._per_ip_counts: Dict[str, int] = {}, reuse self._lock.
In connect(): before accept(), under async with self._lock: increment and check against ws_max_connections_per_ip.
Increment must happen before accept() (fail-closed).
In disconnect(): decrement in finally block to handle exceptions.
Default 5; configurable via JUNIPER_WS_MAX_CONNECTIONS_PER_IP.
Rejection: code 1013 (Try Again Later).

**Notes**:

M-SEC-04 (P1), IMPL-SEC-05..09. RISK-07 mitigation. Phase B-pre (Day 6).

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

### JR-ML-PERF-004 — CasCor remote workers must maintain zero regression in local-only throughput and limit remote overhead to < 5% of task execution.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 361-369)

**Detail**:

PR-2: Zero regression in local-only throughput. PR-3: Remote overhead < 5% task time.

### JR-CAS-API-009 — CasCor service must expose REST endpoints for snapshot save/load with full training state.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 701-705)

**Detail**:

REST endpoints must capture network weights, optimizer state, and training metadata via PyTorch state_dict() or equivalent.

### JR-ML-PERF-005 — Cascor WebSocket send must timeout at 0.5s to prevent indefinite client stalls during backpressure.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 286-292)

**Detail**:

Wrap existing await websocket.send_json(message) in asyncio.wait_for(..., timeout=self._settings.ws_send_timeout_seconds).
Default ws_send_timeout_seconds = 0.5 in Settings (range gt=0.0, le=5.0).
On asyncio.TimeoutError / WebSocketDisconnect, log INFO and return False so caller prunes.
Quick-fix mitigation for RISK-04 in Phase A-server (Day 2, commit 3).
Phase E may upgrade to full pump-task backpressure if production telemetry shows RISK-04/11 triggering.

**Notes**:

RISK-04 quick-fix. Phase E (Day 12) full backpressure deferred per R0-03 §7.2 unless production data warrants.

### JR-CAN-DATA-002 — CascorIntegration must implement save_snapshot() and load_snapshot() for persistence and recovery

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 96-115)

**Detail**:

CascorIntegration lacks snapshot serialization methods; prevents session recovery and checkpoint-based resumption.
HDF5 snapshot creation exists in main.py but only for demo mode state.

**Notes**:

[v2 ARCH→DATA re-bucket] CAN-CRIT-002; CRITICAL priority post-release item; validation confirmed not implemented.

### JR-CAN-API-012 — CascorServiceAdapter must normalize cascor's nested status structure (state_machine, monitor, training_state) to flat dashboard format (is_running, is_paused, phase, current_epoch, hidden_units).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md` (lines 1-10)

**Detail**:

Cascor returns nested objects; dashboard expects flat keys. Add _normalize_status_response() method that maps state_machine.status (title case) to boolean flags (is_running, is_paused, completed, failed) with falsy-value safety using _first_defined().

**Notes**:

Status bar works via /api/status endpoint transformation; direct backend.get_status() calls get nested format.

### JR-ML-TRAIN-032 — CCC-01: Wire-format schema evolution — strictly additive, no field rename/retype/remove; rollout state matrix.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-03-CROSS-CUTTING-CONCERNS.md` (lines 59-146)

**Detail**:

Wire format is additive-only. Every field added in Phase 0-cascor (seq, emitted_at_monotonic, replay_buffer_capacity, server_instance_id)
is present but may be ignored by older clients. No field is renamed, retyped, or removed.
Rollout state matrix documents per-phase per-endpoint compatibility: which fields are present,
which are optional, which old clients tolerate.
Acceptance criteria: rollout doc completed, PR contains state matrix, no surprises in cross-repo CI.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Cross-cutting. Applies to all phases touching wire. Dedup with R3-03.

### JR-ML-OBS-035 — CCC-02: Observability stack — metrics/logging/tracing/dashboards/alerts before behavior, load-bearing SLO binding.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-03-CROSS-CUTTING-CONCERNS.md` (lines 160-258)

**Detail**:

Principle: observability precedes behavior. Every Phase ships metrics, dashboards, alerts, runbooks **before** the feature flips.
Metrics naming convention: `{repo}_ws_{metric}` for WebSocket, `{repo}_training_{metric}` for training control.
Labels: `endpoint` (path), `event_type` (for audit), `transport` (rest/ws), `policy` (backpressure).
Dashboard panels: "WebSocket health" (latency p50/p95/p99), "Polling bandwidth" trend, "Connection state", "Rate limits",
"Audit events", "Backpressure drops".
Alerts: `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap` (ticket), `WSPendingConnectionStuck` (ticket), `WSSlowBroadcastP95` (ticket),
`CSRFFailureRate` (ticket), `AuditLogRotationFailure` (ticket).
Load-bearing SLO: P0 success metric `canopy_rest_polling_bytes_per_sec` >=90% reduction vs baseline. Binding after >=1 week production data.
Acceptance: all metrics present before PR merge, histogram test-fired in staging, gauge queries return non-zero.

**Notes**:

Cross-cutting. Principle from R1-02 principle 1. Dedup with R3-03.

### JR-ML-ARCH-140 — CCC-03: Kill-switch architecture — every phase has config-only reversal, MTTR <=5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-03-CROSS-CUTTING-CONCERNS.md` (lines 261-340)

**Detail**:

Every behavior change has a kill switch: feature flag (boolean), config enum, or env var.
MTTR (mean time to recovery) <=5 min: flip flag + restart, no code revert needed.
Every switch CI-tested: PR includes test that toggles switch, asserts behavior changes.
Every switch staging-drilled: canary in staging verifies toggle works before production deploy.
Examples: `enable_browser_ws_bridge` (5 min toggle), `use_websocket_set_params` (2 min toggle), `ws_backpressure_policy` (env var),
`ws_allowed_origins` (env list), `disable_ws_bridge` (permanent kill, always available).
Acceptance: if kill switch fails to produce expected metric delta within 60 s, migration halts for re-planning.

**Notes**:

Cross-cutting. Principle from R1-02 principle 2. Dedup with R3-03.

### JR-ML-DOC-001 — CHANGELOG.md + docs/websocket_protocol.md additive field contract section.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 121-121)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-CAN-TEST-012 — CI must upload coverage reports to Codecov.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 117-117)

**Detail**:

Issue 2.1.5: .github/workflows/ci.yml missing Codecov step. Add upload
after test run for coverage tracking and status badges.

### JR-ML-API-013 — Client Packages (PyPI).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 67-76)

**Detail**:

| `juniper-data-client`   | 0.3.0   | HTTP client for JuniperData API          |

### JR-ML-OBS-036 — _client_latency_ms private field on returned dict.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 223-223)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-UI-012 — Code review audit plan (R5-01 aligned): 34 gaps, 22 REAFFIRMED, 1 SUPERSEDED, 4 DEFERRED, 7 COORDINATED with R5-01 phases.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_AUDIT_PLAN_2026-04-12_R5-01-aligned.md` (lines 1-100)

**Detail**:

Re-evaluates 34 gaps from original audit (91 issues, 57 verified, 16 partially fixed, 18 not fixed) against R5-01 Canonical Development Plan. Dispositions: REAFFIRMED (22 gaps, original remediation applies — Cassandra/Redis, test quality, dataset/torch/training state, frontend), SUPERSEDED (1 gap, HIGH-005 sync HTTP → R5-01 Phase B), DEFERRED (4 gaps, DashboardManager extraction, ThemeColors rollout, Dockerfile decisions), COORDINATED (7 gaps with specific R5-01 phases: Phase 0-cascor, Phase B, Phase C).

**Notes**:

[v2 ARCH→UI re-bucket] 22 REAFFIRMED gaps mostly completed via PR #146. DEFERRED gaps tracked as accepted technical debt. COORDINATED gaps require synchronization with R5-01 phase owners.

### JR-CAN-OBS-002 — ColoredFormatter must not mutate LogRecord during formatting.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 151-151)

**Detail**:

Issue 3.1.1: ColoredFormatter adds ANSI codes to LogRecord.msg in-place,
affecting file output. Clone record before mutation or use format string.

### JR-DEP-SEC-002 — Complete SOPS secrets management with .env.secrets example and make targets.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 143-152)

**Detail**:

Phase 2. Create .env.secrets.example documenting all secret variables (API keys,
Grafana admin password, Sentry DSNs). Add make secrets-encrypt / make secrets-decrypt
targets wrapping sops commands. Document workflow in docs/SECRETS_GUIDE.md. Ensure CI
does not require decrypted secrets (use ${VAR:-} defaults).

### JR-ML-TEST-011 — Comprehensive testing strategy for WebSocket migration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-05-TESTING-VALIDATION.md` (lines 1-68)

### JR-ML-ARCH-141 — CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4216-4231)

### JR-ML-ARCH-142 — CONC-02: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4234-4249)

### JR-ML-OBS-037 — CONC-03: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4252-4275)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-143 — CONC-04: ALL Storage Operations Block Async Event Loop (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4278-4301)

### JR-ML-ARCH-144 — CONC-07: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4304-4319)

### JR-ML-ARCH-145 — CONC-08: `is_running` Reads/Writes Inconsistently Locked.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4322-4336)

### JR-ML-ARCH-146 — CONC-09: Fire-and-Forget `asyncio.create_task` Without Stored Reference.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4339-4353)

### JR-ML-ARCH-147 — CONC-10: Health Monitor Deregister/Assign Race Window.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4356-4370)

### JR-ML-ARCH-148 — CONC-12: `record_access` TOCTOU on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4373-4388)

### JR-CAN-DOC-003 — Configuration must have no version string mismatches (app_config.yaml, pyproject.toml).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 84-86)

**Detail**:

Issues 1.2.2, 1.2.3: Update app_config.yaml version to 0.4.0 and pyproject.toml
header version comment to match. Should be single source via importlib.metadata.

### JR-CAS-TRAIN-022 — Consolidate duplicated JuniperDataClient in Cascor and Canopy into shared package.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 214-226)

**Detail**:

Cascor and Canopy maintain separate copies. Canopy has get_preview() method not in
Cascor. Changes to one not reflected in other. Fix: consolidate into juniper_data_client
shared package installable by both applications.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-DEP-OBS-009 — Consolidate health check timings and Prometheus scrape intervals into .env variables.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 9-145)

**Detail**:

110+ hardcoded values across docker-compose.yml, Prometheus configs, alert rules, scripts.
~24 are env-configurable, ~85 remain hardcoded. Priority HIGH: health check timings (28 values)
and Prometheus config (7 values). Approach A (RECOMMENDED): Docker Compose extension fields
(x-healthcheck-defaults) + .env expansion. Create scripts/config.sh for shell script defaults.
Add ~20 new variables to .env.example: HEALTHCHECK_INTERVAL, TIMEOUT, START_PERIOD, RETRIES;
PROMETHEUS_SCRAPE_INTERVAL, EVAL_INTERVAL, SCRAPE_TIMEOUT; per-service intervals.

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

### JR-ML-ARCH-149 — Correctness: no seq gaps.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 147-148)

### JR-ML-TRAIN-033 — Correctness: no state loss.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAN-API-013 — CORS configuration YAML syntax must be valid and documented.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 87-87)

**Detail**:

Issue 1.2.5: app_config.yaml CORS section has syntax errors. Validate and
document expected format. File: conf/app_config.yaml

### JR-CAN-SEC-009 — CORS must be restricted to used methods and headers only.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 79-79)

**Detail**:

Issue 1.1.7: Currently allows all methods and headers. Restrict to
actual API usage (GET, POST, OPTIONS; only necessary headers). File: src/main.py

### JR-DEP-TOOL-001 — Create juniper-ctl CLI wrapper for systemd management (start/stop/restart/logs/health/resources).

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 256-274)

**Detail**:

Management CLI wrapping systemctl --user commands with 10+ subcommands:
start/stop/restart (single or all), status (all services), logs/follow, health (latest checks),
resources (CPU/memory/IO usage), install (symlink units + daemon-reload), enable/disable (auto-start).

### JR-CCL-ARCH-001 — Create production constants module juniper_cascor_client/constants.py with ~30 constants (URLs, timeouts, retries, status codes).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 12-22)

**Detail**:

Sections: Service Configuration (base URLs), HTTP Configuration (timeout, retries, backoff, pool size),
HTTP Status Codes (400, 404, 409, 422, 503), Decision Boundary (resolution default/min/max),
Authentication (header name).

**Design**:

Create juniper_cascor_client/constants.py with logical sections organizing ~30 production constants.
Alternative: split into constants.py (production) and testing/constants.py (test fixtures).

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-ML-OBS-038 — Create register_or_reuse and register_fresh helpers in juniper-observability to centralize idempotent prometheus_client collector construction, eliminating ~10 copy-pasted implementations across consumer repos.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md` (lines 1-50)

**Detail**:

Two helpers needed:
1. register_or_reuse(factory, name, *args, **kwargs) - adopts existing collectors
2. register_fresh(factory, name, *args, **kwargs) - unregisters and recreates

Live in juniper_observability/prometheus_helpers.py, re-exported from __init__.
~150 lines code + docstrings + unit tests. Target: juniper-data, juniper-canopy, juniper-cascor-client, juniper-cascor.

**Design**:

Constraints:
- Production path zero-overhead
- Test-isolation honesty (predictable behavior)
- Optional-dependency friendly
- No new private-API surface beyond existing inline guards
- Migration is opt-in

API signature:
def register_or_reuse(factory: Callable, name: str, *args, **kwargs) -> T
def register_fresh(factory: Callable, name: str, *args, **kwargs) -> T

**Notes**:

Part of OBS-COLLECTOR-IDEMPOTENT track. Cascor has drop+recreate; 2026-05 PRs use adopt-existing. This centralizes into single canonical form.

### JR-CAS-API-010 — Create shared protocol/interface package for data contracts between applications.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 245-257)

**Detail**:

No shared Python package defining data contracts (Pydantic models, type aliases).
Each app independently defines expectations. NPZ array keys (X_train, y_train, etc.)
documented but not enforced. Fix: create juniper_contracts package defining API schemas.

### JR-CCL-TRAIN-001 — Create testing constants module juniper_cascor_client/testing/constants.py with ~65 constants (hyperparams, scenario params, topology, worker sim).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 23-37)

**Detail**:

Sections: Fake Client Configuration (URL, version, error rate, uptime), Training Hyperparameters
(learning rate, epochs, hidden units, patience), Loss/Accuracy Curve Parameters (per scenario),
Network Topology Generation (bias, weight scales), Decision Boundary Generation, Worker Simulation Data,
Dataset Configuration.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Part of hardcoded-values refactor (HIGH priority)

### JR-ML-ARCH-150 — D-1: Correlation field name (D-02).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 118-119)

### JR-ML-TRAIN-034 — D-2: Phase 0-cascor carve-out (D-11).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 119-120)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-151 — D-3: Two-flag browser bridge (D-17 + D-18).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 120-121)

### JR-ML-ARCH-152 — D-4: REST paths preserved forever (D-21, D-54, D-56).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 121-122)

### JR-ML-SEC-070 — D-5: Positive-sense security flag (D-10).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 122-123)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-PERF-006 — D-6: Phase E backpressure default (D-19).

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 123-124)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-ARCH-153 — D-7: Phase C flag-flip criteria (D-48).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 124-125)

### JR-ML-ARCH-154 — D-8: Kill-switch MTTR tested (D-53).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 125-126)

### JR-ML-PERF-007 — D-**Browser memory leak** (RISK-10): Medium-High.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 132-133)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-TRAIN-035 — D-**Cascor crash mid-broadcast** (RISK-14): Low.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 135-136)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-155 — D-Correctness: no seq gaps: `cascor_ws_seq_gap_detected_total`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 147-148)

### JR-ML-TRAIN-036 — D-Correctness: no state loss: `cascor_ws_dropped_messages_total{type="state"}`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-OBS-039 — D-Criterion: Metric.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 143-144)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-WS-045 — D-**CSWSH attack** (RISK-15): High.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 131-132)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-OBS-040 — D-**Dual metric format breakage** (RISK-01): High.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 134-135)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-156 — D-Observability: full pipe: All canonical metrics present on `/metrics`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 149-150)

### JR-ML-ARCH-157 — D-**P0: polling eliminated**: `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 145-146)

### JR-ML-ARCH-158 — D-Recovery: kill switches work: Every switch flipped in staging.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 150-151)

### JR-ML-ARCH-159 — D-Risk: Severity.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 129-130)

### JR-ML-WS-046 — D-Security: CSWSH closed: `canopy_ws_origin_rejected_total` page alert functional.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-TRAIN-037 — D-**Silent data loss** (RISK-11): High (low likelihood).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 133-134)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-160 — D: `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 359-360)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-161 — D: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 360-361)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-CAN-OBS-003 — Dashboard MetricsPanel expects nested metric format (metrics.loss, metrics.accuracy, network_topology.hidden_units) but service backend produces flat keys.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 242-337)

**Detail**:

Nine MetricsPanel code locations read nested structure: Line 1091 network_topology.hidden_units, Line 1120-1122 metrics.loss/accuracy/network_topology.hidden_units, etc. Service backend currently returns flat keys only.

**Notes**:

Display failure affects all metric charts. Nested format required by React component state rendering.

### JR-CAN-API-014 — DashboardManager must construct API URLs via settings, not ad-hoc _api_url().

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 91-91)

**Detail**:

Issue 1.3.1: _api_url() helper is error-prone and inconsistent. Replace all
callsites with settings-based URL construction. File: src/frontend/dashboard_manager.py

### JR-DEP-OBS-010 — Decide on per-service vs. shared library approach for MetricsAuthMiddleware.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` (lines 1-60)

**Detail**:

juniper-data ships MetricsAuthMiddleware (IP allowlist on /metrics). Cascor and canopy
expose /metrics without in-process auth. Question: lift to juniper-observability shared lib
or keep per-service? Decision (locked 2026-05-02): keep per-service. Cascor/canopy are
network-isolated (ClusterIP, no ingress routing); data is exposed beyond cluster boundary.
Asymmetry is deliberate. Re-open if: cascor/canopy exposed beyond boundary, third service
needs middleware, compliance audit mandates uniform posture, or NetworkPolicy isolation breaks.

### JR-CAN-UI-013 — Decision boundary visualization must support real CasCor backend (currently demo-only endpoint).

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 74-94)

**Detail**:

/api/decision_boundary endpoint only returns demo data when CASCOR_DEMO_MODE is not set.
No implementation for real backend path; core visualization feature non-functional in production.
Design option: Add get_decision_boundary_data() to CascorIntegration that queries real backend.

**Notes**:

[v2 ARCH→UI re-bucket] CAN-CRIT-001; identified as validation-confirmed critical integration gap in post-release audit.

### JR-DEP-OBS-011 — Define and document alert rule thresholds as environment-configurable constants.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 55-66)

**Detail**:

Prometheus alert_rules.yml contains 10+ hardcoded thresholds (error rate 0.05, data P95
latency 2.0s, cascor P95 5.0s, dataset gen 30.0s, correlation 0.01, restart count 3, windows
1m/5m/10m/15m/30m). Document all values clearly in YAML comments. Consider envsubst preprocessing
for full configurability across deployment targets. Medium priority per analysis.

### JR-ML-API-014 — Define four snapshot endpoints: restore (explore), replay (watch metrics fresh), resume (continue), retrain (new training).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-SNAPSHOT-LOAD-TYPES.md` (lines 18-76)

### JR-DEP-DEP-003 — Define production Docker Compose profile with resource limits, restart policies, log rotation.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 121-152)

**Detail**:

Phase 2 (v0.3.0) production readiness. Add --profile production to docker-compose.yml
or docker-compose.production.yml override. Per-service resource limits (deploy.resources.limits
for CPU and memory), restart policies (restart: always with deploy.restart_policy),
log rotation (Docker logging driver options max-size, max-file).

### JR-CAN-API-015 — Define Pydantic model for set_params endpoint request body.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 77-77)

**Detail**:

Issue 1.1.5: set_params endpoint lacks formal request schema. Add Pydantic
model for validation. File: src/main.py. Updates OpenAPI documentation.

### JR-ML-SEC-071 — Deterministic IDs with `seed=None` → same ID for different random data → stale cache returns.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 327-348)

**Detail**:

| JD-01 | **High**   | `api/security.py`        | 59      | Non-constant-time API key comparison — timing side-channel attack vector                     |

**Notes**:

[v4 brief repaired; was: '2.5 juniper-data']

### JR-ML-ARCH-162 — `disable_ws_auto_reconnect`: F.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 317-318)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-163 — `disable_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 308-309)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-164 — `disable_ws_control_endpoint`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 313-314)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-WS-047 — disconnect() cancels recv task, drains pending with set_exception(JuniperCascorConnectionError).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 220-220)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-DEP-001 — Docker dependencies must be pinned via lockfile, not floating versions.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 128-128)

**Detail**:

Issue 2.3.2: Dockerfile uses floating versions (python:3.11, etc). Pin via
Dockerfile ARG or multi-stage from pinned base images.

### JR-CAN-DEP-002 — Docker log file handler must use append mode, not write mode.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 130-130)

**Detail**:

Issue 2.3.4: Log file handler configured with 'w' (write) instead of 'a'
(append). Causes log truncation on app restart. Use 'a' mode.

### JR-CAN-DEP-003 — Docker must have production configuration or documented env var overrides.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 129-129)

**Detail**:

Issue 2.3.1: Dockerfile currently dev-centric. Create Dockerfile.prod or
document production override env vars (API_BASE, CASCOR_HOST, etc).

### JR-CAN-DEP-004 — Docker service URLs must have correct defaults for health checks.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 129-129)

**Detail**:

Issue 2.3.3: HEALTHCHECK instruction uses http://localhost:8000/health
but app may be configured differently. Use env vars or expose-port-agnostic probe.

### JR-DCL-DOC-004 — Document complete JuniperDataClient public API (20+ methods) in AGENTS.md, replacing minimal 3-method snippet.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 79-108)

**Detail**:

Public API section currently shows only 3 methods (health_check, create_spiral_dataset, download_artifact_npz).
Client has grown to 20+ public methods across 9 categories: Health & Readiness (3), Generator Discovery (2),
Dataset Creation (2), Dataset Versioning (2), Dataset Operations (3), Artifact Download (2), Preview (1),
Batch Operations (4), Resource Management (2). Must replace snippet with full categorized reference.

**Notes**:

New API added since last AGENTS.md update (2026-02-20): batch_delete, batch_create, batch_update_tags,
batch_export, list_versions, get_latest, list_generators, get_generator_schema, get_preview, is_ready,
wait_for_ready. Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.3) and AGENTS_MD_UPDATE_PLAN (Step 2.3).

### JR-CAS-DOC-002 — Document forkserver context workaround and multiprocessing queue-based task distribution.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/setup_config_guides/forkserver_fix.md` (lines 1-20)

**Detail**:

Forkserver debugging and configuration guide. Documents BaseManager configuration
with forkserver context, queue-based task distribution patterns.

### JR-DCL-DOC-005 — Document juniper_data_client.testing submodule in AGENTS.md (FakeDataClient, generators).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-57)

**Detail**:

Testing submodule (juniper_data_client/testing/) contains FakeDataClient (715 lines) and 4 synthetic
generators (generate_spiral, generate_xor, generate_circle, generate_moon) in generators.py (284 lines).
This is a critical public API surface that ships with the library and is used by consumers (juniper-cascor,
juniper-canopy). Must add "Testing Utilities" section documenting import paths and usage patterns.

**Notes**:

The omission of this submodule from AGENTS.md means agents are unaware of this significant API.
Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.4) and AGENTS_MD_UPDATE_PLAN (Step 2.4).

### JR-ML-ARCH-165 — E: `JUNIPER_WS_BACKPRESSURE_POLICY=block`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 361-362)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-038 — Effort bounds and calendar: 15.75 expected eng days (~4.5 weeks calendar) with soak windows.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R4-01-COMPREHENSIVE-MASTER-PLAN.md` (lines 76-94)

**Detail**:

Effort table (optimistic/expected/pessimistic): Phase 0-cascor 1.5/2.0/3.0, A-SDK 0.5/1.0/1.5, B-pre-a 0.5/1.0/1.5,
B 3.0/4.0/5.0, B-pre-b 1.0/1.5/2.0, C 1.5/2.0/3.0, D 0.75/1.0/1.5, E 0.75/1.0/1.5, F 0.25/0.5/1.0,
G 0.25/0.5/0.75, H 0.5/1.0/1.5, I 0.1/0.25/0.5. Total 10.6/15.75/22.25 eng days.
Calendar translation: 15.75 days × single-dev lane = ~3 weeks one-person, or ~4.5 weeks with 48-72 h soak windows.
Minimum-viable carveout (P0 only): ~7 days (Phase A-SDK + 0-cascor + B-pre-a + B + I).
Soak windows: 0-cascor 72 h, Phase B 72 h, B-pre-b 48 h, Phase C canary >=7 days.
Phase dependency graph: A-SDK || 0-cascor || B-pre-a → B || B-pre-b → D; C parallel with B/D; E/F/G/H follow.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Risks: 0-cascor async race (+risk), A-SDK correlation map iteration (+risk), B-pre-a audit logger name collision (+risk),
B NetworkVisualizer Plotly (+1 day), B-pre-b session middleware absent (+0.5 day), C concurrent-correlation bugs (+risk),
D orphaned-command UI state (+risk), E queue tuning (+risk), F reconnect-cap lift debated.

### JR-DEP-OBS-012 — Emit X-Juniper-Readiness response header on all /v1/health/ready endpoints.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 89-94)

**Detail**:

All four services (cascor, data, canopy, cascor-worker) must emit
X-Juniper-Readiness: ready | degraded | not_ready response header on /v1/health/ready.
Header mirrors body status field byte-for-byte. Constant single-sourced in
juniper-observability (READINESS_HEADER). Cascor-worker uses same literal without import.

### JR-ML-ARCH-166 — `enable_browser_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 307-308)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-167 — `enable_raf_coalescer`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 309-310)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-168 — `enable_ws_control_buttons`: D.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 311-312)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-UI-012 — End of audit report.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 549-566)

**Detail**:

12. **Add shared memory startup sweep**: On cascor server startup, remove stale `juniper_train_*` blocks from `/dev/shm`.

**Notes**:

[v3 brief repaired from cited content; was: '7.3 Long-Term (Low/Architectural)']

### JR-ML-ARCH-169 — ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4412-4426)

### JR-ML-TRAIN-039 — ERR-02: `response.json()` Unguarded in cascor-client `_request()`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4429-4443)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-040 — ERR-06: `raise HTTPException` Without `from e` — Lost Exception Context (cascor).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4446-4460)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-170 — ERR-07: `raise HTTPException` Without `from e` — Broad Except Masks Programming Errors (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4463-4477)

### JR-ML-ARCH-171 — ERR-08: `str(e)` in Batch Create Error Response — Information Disclosure (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4480-4494)

### JR-ML-ARCH-172 — ERR-09: `remote_client_0.process_tasks()` Catches All Exceptions, Only Prints.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4497-4511)

### JR-ML-ARCH-173 — ERR-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4514-4529)

### JR-ML-ARCH-174 — ERR-13: `arc_agi` Generator Silent Fallback on Any Exception.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4532-4546)

### JR-ML-ARCH-175 — ERR-14: `CascorMetricsStream.stream()` Swallows ConnectionClosed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4549-4571)

### JR-CAS-TEST-005 — Establish automated CI/CD pipeline with pytest, coverage, type checking, and linting.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 569-599)

### JR-CAS-TEST-006 — Establish performance testing infrastructure with reproducible baselines and CI/CD integration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PERFORMANCE_TESTING_PLAN.md` (lines 28-41)

**Detail**:

5-phase performance testing plan: Phase 1 baseline profiling, Phase 2 micro-benchmarks,
Phase 3 concurrency scaling, Phase 4 end-to-end profiling, Phase 5 optimization.
Goals: establish baselines, identify bottlenecks, quantify scaling, produce
recommendations, create regression-safe CI/CD integration.

### JR-ML-OPS-003 — Every phase must have kill-switch feature flag; TTF (time to fallback) documented.

**Status**: proposed  **Priority**: P1  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-02-RISK-MINIMIZED-SAFETY-FIRST.md` (lines 29-47)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1044-1046)

**Detail**:

Phase A: no feature flag (additive SDK method, cannot be disabled).
Phase A-server: no feature flag (seq is infrastructure, not a feature).
Phase B: disable_ws_bridge=True → forces REST polling. TTF ~2 min.
Phase C: use_websocket_set_params=False (default) → falls back to REST. TTF ~2 min.
Phase D: disable_ws_control_endpoint=True → buttons force REST. TTF ~5 min.
Phase B-pre auth: ws_security_enabled=False (or JUNIPER_CANOPY_DISABLE_WS_AUTH=true per naming debate in §14 D5). TTF ~2 min. Local dev only—never set in prod.

**Notes**:

Kill switches are non-optional per R1-02 §1.2 principle #2. All documented in day rollback sections.

### JR-ML-SEC-072 — Excessive f-string tensor interpolation logging in hot paths.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 877-895)

### JR-ML-SEC-073 — Execute comprehensive security audit of Juniper ecosystem with threat modeling and vulnerability assessment.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECURITY_AUDIT_PLAN.md` (lines 1-100)

**Notes**:

Multi-phase security program.

### JR-CCL-DOC-007 — Expand AGENTS.md Key Files table with 15+ missing entries (testing submodule, py.typed, CHANGELOG.md, docs/, scripts/, notes/, CI/CD files).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 58-77)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 23-28)
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-76)

**Detail**:

Missing files include: juniper_cascor_client/testing/ (1,807 LOC), py.typed (PEP 561),
CHANGELOG.md, docs/ (4 files), scripts/ (2 files), notes/, .env.example, .pre-commit-config.yaml,
.github/workflows/ci.yml, publish.yml, CODEOWNERS, dependabot.yml, .sops.yaml, conf/, tests/conftest.py.

**Notes**:

[v3 xrepo fuzzy merge: owners=ccl,dcl, n=2] High severity: agents cannot orient themselves or find major code components / Severity: High. Testing submodule is critical public API (ships with library, used by juniper-cascor
and juniper-canopy). Agents working on this codebase are unaware of its existence when omitted from AGENTS.md.
Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.2) and AGENTS_MD_UPDATE_PLAN (Step 2.2).

### JR-ML-ARCH-176 — F: `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 362-363)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-048 — Fail-fast: no SDK retries on timeout (C-04).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 222-222)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-TEST-013 — FakeCascorClient.update_params snapshots _network_config to _training_params['params'] at init but update_params does not sync updates, causing verify-roundtrip mismatches.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 41-119)

**Detail**:

When update_params({'learning_rate': 0.005}) is called, _network_config is updated but _training_params['params'] stale snapshot is not, causing get_training_params() to return original value. Workaround: update both locations in FakeCascorClient.update_params.

**PRs**: #264

**Notes**:

Upstream fix pending in juniper-cascor-client. Test currently uses idle scenario workaround.

### JR-ML-SEC-074 — Five specialized validation agents independently cross-referenced the v2.0.0 outstanding development items document against 34 source….

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 572-588)

**Detail**:

Five specialized validation agents independently cross-referenced the v2.0.0 outstanding development items document against 34 source documents spanning all 8 Juniper ecosystem repositories. Each agent was assigned a focused subset of source documents to ensure thorough coverage:

**Notes**:

[v3 brief repaired from cited content; was: 'Process']

### JR-ML-TRAIN-041 — Fix BUG-CC-12: replace yaml.safe_load with torch.load or safetensors in cascor utils.py.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md` (lines 71-77)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-PERF-008 — Fix BUG-JD-10: wrap sync storage I/O in asyncio.to_thread in juniper-data batch_update_tags.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md` (lines 79-84)

### JR-ML-TRAIN-042 — Fix CasCor demo training error with identified root cause and remediation.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN-OLD.md` (lines 1-100)

**Notes**:

Legacy plan version; check for updates in primary plan.

### JR-CAN-API-016 — Fix CascorStateSync to read from correct response fields (data.state_machine, data.monitor).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

Sync reads data.state, data.epoch; real cascor has data.state_machine, data.monitor. Causes initial state hydration to fail.

**Notes**:

FIX-5; initial sync reads wrong keys

### JR-ML-SEC-075 — Fix critical security vulnerabilities in CasCor multiprocessing: hardcoded authkey, unpickler, queue sizing, API key comparison.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 809-850)

**Detail**:

Phase 1a: (1) Remove hardcoded PROJECT_MODEL_AUTHKEY, (2) Add RestrictedUnpickler for result queue, (3) Add queue maxsize, (4) Result bounds checking, (5) Use hmac.compare_digest for API key validation.

### JR-ML-TEST-012 — Fix cross-project regression issues with remediation plan.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CROSS_PROJECT_REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-100)

**Notes**:

Active investigation status.

### JR-CAS-TRAIN-023 — Fix epoch/iteration semantic error in grow_network() and ValidateTrainingInputs dataclass; rename for correctness.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/analysis/REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-180)

**Detail**:

Each grow_network() loop iteration performs complete Cascade Correlation growth cycle (candidate training, selection, installation), not single epoch. Rename max_epochs→max_iterations, epoch→iteration, epochs_completed→iterations_completed, log "Iteration" not "Epoch". Update ValidateTrainingInputs fields. Callers: fit() line 1445, unit tests. No breaking API changes. Backward-compatible alias pattern available (lines 1375-1379). Estimated 2-4 hours effort. Non-functional behavior change.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-ML-DEP-015 — Fix image build bugs: observability images not inheriting base image labels correctly.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_IMAGE-BUILD-BUGS.md` (lines 1-50)

### JR-ML-OBS-041 — Fix layer assignments (Task 3); add `get_dataset_data()` (Task 2 Ph2).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 329-341)

**Detail**:

| `src/backend/cascor_service_adapter.py`          | Fix layer assignments (Task 3); add `get_dataset_data()` (Task 2 Ph2) | 1, 4  |

**Notes**:

[v4 brief repaired; was: '9.1 juniper-canopy (all phases)']

### JR-ML-SEC-076 — Fix Logic Validation.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 886-895)

**Detail**:

| OI-1 | **VALID** | `dash.no_update` confirmed as correct Dash sentinel; already used 26 times in `dashboard_manager.py` |

### JR-CAS-ARCH-007 — Fix main.py passing invalid parameters to SpiralProblem constructor.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 281-295)

**Detail**:

Lines 208-210: passes _SpiralProblem__spiral_config=logging.config (the logging module,
not config object), _SpiralProblem__dataset_tensors=None, _SpiralProblem__dataset_file_info=None.
Silently absorbed by **kwargs. Fix: remove invalid parameters or implement SpiralConfig.

### JR-CAN-API-017 — Fix metrics format mismatch: _normalize_metric() produces flat keys but dashboard expects nested format.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 188-258)

**Detail**:

CRITICAL display blocker (ISS-01). Service backend _normalize_metric() produces flat dictionary {epoch, train_loss, train_accuracy, hidden_units, phase} but MetricsPanel reads nested format {epoch, metrics.loss, metrics.accuracy, network_topology.hidden_units, phase}. When dashboard executes metric.get("metrics", {}).get("loss", 0) on flat data, returns 0. Impacts loss chart, accuracy chart, hidden unit count, and phase-colored scatter plots.

**Design**:

Transform _normalize_metric() output or add adapter layer between normalized flat metrics and dashboard nested consumption. Must preserve falsy-value semantics (0, 0.0, False are valid metrics, not missing values).

**Notes**:

Unanimous finding across Phase 3 proposals v1-v7 and Phase 2. Phase 1 designed canonical internal contract (flat keys) by analyzing normalization boundary only, never validated against dashboard consumption boundary. Status bar's success with flat keys masked metrics panel failure.

### JR-CAN-API-018 — Fix network topology format mismatch: cascor returns weight-oriented structure but NetworkVisualizer expects graph-oriented.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 313-378)

**Detail**:

CRITICAL display blocker (ISS-04). CasCor /v1/network/topology returns {input_size, output_size, hidden_units: [objects with weights], output_weights, output_bias}. NetworkVisualizer expects {input_units (int), output_units (int), hidden_units (int), nodes, connections}. Six structural mismatches: input_size vs input_units, output_size vs output_units, hidden_units array vs int count, missing connections list, missing nodes list, weight data location mismatch. Validation check at network_visualizer.py:351 always triggers, rendering empty placeholder graph.

**Design**:

Add topology adapter (extract_network_topology_graph) that transforms cascor weight-oriented structure to graph-oriented format, analogous to existing get_decision_boundary() decision boundary adapter at cascor_service_adapter.py:495-543.

**Notes**:

Identified by proposals v2, v4. Regression tests (test_topology_boundary_data_contract.py) validate expected input_units/output_units keys; these pass against demo backend but would fail against real cascor data.

### JR-ML-TEST-013 — Fix regressions identified in 2026-04-03 analysis.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-100)

### JR-DEP-SEC-003 — Fix shell injection vulnerability in wait_for_services.sh and related scripts.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 264-314)

**Detail**:

check_service() interpolates environment-derived URLs directly into inline Python code.
Malicious JUNIPER_DATA_PORT value can break out and execute arbitrary code. Same pattern found
in health_check.sh (line 59-79) and test_health_enhanced.sh (line 66). Affects wait_for_services.sh,
health_check.sh, test_health_enhanced.sh. Remediation: pass URLs via sys.argv[1] instead of
interpolating into code string. Add PORT numeric validation as defense-in-depth.

### JR-ML-TRAIN-043 — Fix tensor dimension mismatch issues in CasCor batch processing pipeline.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_TENSOR_DIMENSION_MISMATCH_ANALYSIS.md` (lines 1-100)

**Notes**:

Analysis-based remediation for candidate training.

### JR-ML-TOOL-001 — Fix wake_the_claude.bash session validation failures.

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/wake_the_claude_failure_analysis.md` (lines 1-100)

**Notes**:

Development tooling issue.

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

### JR-CAN-SEC-010 — get_rate_limiter() must use get_settings() instead of direct access.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 86-86)

**Detail**:

Issue 1.2.4: Inconsistent settings access pattern. Use get_settings() function
for uniform configuration retrieval. File: src/security.py

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-CAN-TEST-014 — GitHub Actions workflow must fix lockfile extras mismatch.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 113-113)

**Detail**:

Issue 2.1.1: .github/workflows/lockfile-update.yml extras specification
conflicts with pyproject.toml. Align definitions.

### JR-CAN-TEST-015 — GitHub publish workflow must add contents:read permission.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 114-114)

**Detail**:

Issue 2.1.2: .github/workflows/publish.yml missing minimal required
permissions. Add contents:read for artifact access.

### JR-ML-API-015 — `glob("*.npz")` scans entire data directory on every health check.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 442-455)

**Detail**:

| **Sync generation**    | ⚠️ Concern | `generator.generate(params)` blocks event loop in async endpoint  |

**Notes**:

[v4 brief repaired; was: '4.3 juniper-data Performance']

### JR-ML-ARCH-177 — H: `git revert` P16.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 363-364)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-CCL-TEST-004 — Hardcoded values refactor implementation plan: Phase 1 create constants module, Phase 2 refactor source files, Phase 3 validate test suite and pre-commit, Phase 4 documentation update.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 42-44)
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-48)
- `juniper-cascor-worker/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 1-79)
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 38-41)

**Notes**:

[v2 ARCH→TEST re-bucket] [v3 xrepo fuzzy merge: owners=ccl,cwk,dcl, n=4] Part of hardcoded-values refactor (HIGH priority)

### JR-CAN-OBS-004 — Health checks must use async probes instead of blocking network calls.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 155-155)

**Detail**:

Issue 3.1.5: Health endpoints currently block on cascor connectivity checks.
Use async probes or timeout guards to prevent cascor slowness from blocking
health endpoint response.

### JR-CAN-API-019 — Helper function _first_defined() must be available for falsy-value safe field extraction across nested cascor response structures.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 1-50)

**Detail**:

Pattern: _first_defined(a, b, c) returns first non-None/non-False value. Required for extracting epoch/hidden_units from cascor's variable-structure responses where a field may be nested at different paths depending on backend state.

**Notes**:

Used across all normalization methods.

### JR-ML-ARCH-178 — I: `git revert` cache-bust commit.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 364-365)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-CAN-API-020 — Implement CascorIntegration.get_network_data() method to return network statistics.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 120-140)

**Detail**:

Method does not exist on CascorIntegration class; callers will receive AttributeError at runtime. Must return dict with keys: input_weights, hidden_weights, output_weights, hidden_biases, output_biases, threshold_function, optimizer.

**Notes**:

Network statistics tab fails when connected to real CasCor backend; blocking P1

### JR-CAN-UI-014 — Implement decision boundary visualization for real CasCor backend in Canopy dashboard.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 88-118)

**Detail**:

The /api/decision_boundary endpoint retrieves prediction function from cascor_integration but never computes the grid. Must implement grid computation mirroring demo mode logic.

**Notes**:

Dataset/Decision Boundary tab shows "No data available" when connected to real CasCor backend

### JR-CAN-API-021 — Implement real backend control for Canopy WebSocket endpoint when connected to live CasCor backend.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 55-85)

**Detail**:

The /ws/control endpoint currently rejects all commands when cascor_integration is active with a hardcoded error. Must implement command routing to CascorIntegration methods (start, stop, pause, resume, reset) and add state broadcasting after each command execution.

**Notes**:

Part of Phase 1 critical integration blockers; blocking all real-backend WebSocket control

### JR-ML-TRAIN-044 — Implement root cause fix for CasCor training stall based on proposal analysis.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md` (lines 1-100)

**Notes**:

Blocks training completion.

### JR-CAN-API-022 — Implement save_snapshot() and load_snapshot() methods on CascorIntegration class.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 146-166)

**Detail**:

Methods do not exist; code falls through to minimal HDF5 fallback that only stores metadata, not network state. Must delegate to CasCor's CascadeHDF5Serializer.

**Notes**:

Snapshot save/load in real backend mode produces incomplete snapshots

### JR-ML-UI-013 — In `_process_dataset_update()`, add metadata-only branch:.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 137-151)

**Detail**:

**File:** `src/frontend/components/dataset_plotter.py`

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Fix — Phase 1: Canopy Graceful Degradation (canopy-only)']

### JR-ML-API-016 — Include all 22 meta-parameter fields in the state response. Use `.get()` with `TrainingConstants` defaults for any missing fields to handle….

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 306-310)

**Detail**:

Include all 22 meta-parameter fields in the state response. Use `.get()` with `TrainingConstants` defaults for any missing fields to handle backward compatibility when the backend doesn't yet store all parameters.

**Notes**:

[v3 brief repaired from cited content; was: '5.2 `/api/state` Endpoint']

### JR-ML-SEC-077 — Incomplete implementation of `max_epochs` and `max_iterations` as separate training limits — broken data flow across cascor and canopy.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 60-160)

**Detail**:

Option A, executed as two coordinated PRs (cascor first, then canopy). The canopy side is primarily wiring an existing UI control to an existing param map — the UI already exists and the user already expects it to work. The cascor side is the larger change but follows established patterns for existing fields like `epochs_max`.

Both repos should be updated in the same development cycle to avoid a window where the field exists in cascor but canopy can't drive it.

### JR-ML-OBS-042 — Issue Remediations, Section 17.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-A-SECURITY-CONCURRENCY-ERROR.md` (lines 297-347)

**Detail**:

#### CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager

### JR-ML-SEC-078 — Issue Remediations, Section 19.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 607-657)

**Detail**:

#### CI-01: cascor-client CI Doesn't Test Python 3.14

### JR-ML-DEP-016 — juniper-deploy P0: define SECRETS_DIR and SECRETS_FILES variables in Makefile.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-DEVELOPMENT-ROADMAP.md` (lines 47-60)

### JR-ML-OBS-043 — `juniper_data/api/routes/health.py` (`/v1/health`, `/v1/health/live`, `/v1/health/ready`).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 51-101)

**Detail**:

| Python entry point             | `juniper_data/__main__.py`                                                                | Active                                      |

**Notes**:

[v4 brief repaired; was: '2.1 Per-Application Inventory']

### JR-ML-WS-124 — lifecycle/manager.py state coalescer; terminal transitions bypass throttle (GAP-WS-21).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 118-118)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-API-017 — `list_versions` loads all metadata then filters in Python. No database-level filtering for Postgres.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 178-187)

**Detail**:

| ID         | Severity   | File:Line                    | Description                                                                                          |

**Notes**:

[v4 brief repaired; was: '3.3 Performance']

### JR-ML-API-018 — `list_versions` loads all metadata then filters in Python. No DB-level filtering for Postgres.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 444-453)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 355-364)

**Detail**:

| JD-PERF-01 | **HIGH**   | `api/routes/datasets.py:107`        | Sync `generator.generate()` blocks async event loop. Needs `asyncio.to_thread()`.              |

**Notes**:

[v4 brief repaired; was: '14.2 Performance Issues']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-API-019 — Lock is per-process; multiple uvicorn workers each have their own lock, defeating the purpose.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 145-159)

**Detail**:

| BUG-JD-01 | **MEDIUM** | `batch_export` builds entire ZIP in memory — OOM risk           | `api/routes/datasets.py:416-434` | Large dataset exports accumulate entire ZIP in memory before sending response                 |

**Notes**:

[v4 brief repaired; was: '5.3 juniper-data']

### JR-CAN-OBS-005 — Logger wrapper instances must be cached to avoid re-wrapping overhead.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 152-152)

**Detail**:

Issue 3.1.2: Wrapper created fresh on each logger.info/debug call. Cache
wrapper per logger instance to improve performance.

### JR-ML-TEST-014 — Make sentry-sdk a hard runtime dependency and remove importorskip guards in tests.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 61-65)

**Detail**:

R3.4 Resolution (b): Move sentry-sdk to hard runtime dep across cascor/canopy/data. Drop importorskip guards so SEC-15 before_send hook tests run every CI run.

**Notes**:

Security-critical test coverage.

### JR-ML-WS-125 — manager.py gains server_instance_id, server_start_time, _next_seq, _seq_lock, _replay_buffer, _assign_seq_and_append().

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 113-113)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-SEC-079 — Medium Priority.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 364-375)

**Detail**:

| Task 2 Ph1: Metadata-only graceful handling  | DASHBOARD_AUGMENTATION_PLAN       | Dataset tab metadata-only display for service mode

### JR-CAN-API-023 — Middleware must handle malformed Content-Length header gracefully.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 78-78)

**Detail**:

Issue 1.1.6: Non-numeric or negative Content-Length can crash request parsing.
Add bounds check and return 400 Bad Request. File: src/middleware.py

### JR-ML-WS-126 — MISSING: - PARTIAL — feature is partially implemented; some paths work, others don't.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 60-61)

### JR-ML-WS-127 — MISSING: Status: server-side PRESENT (cascor accepts and handles the command); client-side MISSING.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE-1.md` (lines 729-730)

### JR-CAN-TEST-016 — MyPy strict_optional setting conflict must be resolved.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 123-123)

**Detail**:

Issue 2.2.3: MyPy configuration has conflicting strict_optional directives
in different sections. Consolidate to single authoritative setting.

### JR-CAN-API-024 — Network topology format mismatch: cascor returns weight-oriented format (input_size, hidden_units array with weights) but NetworkVisualizer expects graph-oriented format (input_units, output_units integers, nodes/connections lists).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 268-295)

**Detail**:

CasCor architecture: input_size, hidden_units [{id, weights, bias, activation}], output_weights, output_bias. Adapter must reconstruct graph format preserving cascade connections (each hidden unit connects to all inputs plus prior hidden units).

**Notes**:

Topology visualization always renders empty because validation guard topology_data.get('input_units', 0)==0 fails when key is 'input_size'.

### JR-CAN-UI-015 — Network visualizer screenshot timestamp must not be static.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 92-92)

**Detail**:

Issue 1.3.2: Screenshot PNG contains hardcoded timestamp instead of actual
capture time. Must update on every screenshot. File: src/frontend/components/network_visualizer.py

### JR-ML-DATA-007 — nn-growth-preset-epochs-input (disabled=True; convergence is default)

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 331-381)

**Detail**:

dbc.Card (className="mb-3")

**Notes**:

[v3 brief repaired from cited content; was: '6.1 Card Structure']

### JR-CAN-TEST-017 — No real UI test sub-suite; browser-automation harness does not exist; no acceptance criterion for UI correctness.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 46-46)

**Detail**:

Fix: new pytest sub-suite + CI lane. Add Selenium or Playwright-based browser automation tests covering all 6 issues. CI budget: <=5 min wall-clock with parallel job + cache + slow marker.

**Notes**:

Quality gate missing; manual testing only.

### JR-CAN-API-025 — Normalize case-sensitivity for status and phase fields: ensure consistent handling of uppercase values from backends.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 102-116)

**Detail**:

Relay path at cascor_service_adapter.py:222 lacks .lower(); sync path at state_sync.py:70 has it. Asymmetric protection. FakeCascorClient uses uppercase, triggering bug in tests. Future backends may pass uppercase.

**Notes**:

P5-RC-03; retained as HIGH latent bug; defensive measure for future backends

### JR-CAN-API-026 — Normalize ServiceTrainingMonitor to use unwrapped response format for real cascor integration.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

_ServiceTrainingMonitor reads raw JuniperCascorClient responses without calling _unwrap_response(). Must normalize via single boundary in CascorServiceAdapter. Fixes FIX-1,2,3.

**Notes**:

Systemic root cause; affects metrics, is_training flag, response shape

### JR-CAN-UI-016 — Numeric input typing vs spinner mismatch; universal debounce=True confuses Apply-button enable indicator.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 44-45)

**Detail**:

Fix: canopy frontend component refactor. Debounce logic does not properly track which fields changed relative to current backend state.

**Notes**:

UX issue; component refactor required.

### JR-ML-ARCH-179 — Observability: full pipe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 149-150)

### JR-ML-SEC-080 — Output weight connection loop — correctly handles all inputs + hidden -> each output.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 213-263)

**Detail**:

**File:** `src/backend/cascor_service_adapter.py`

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Fix']

### JR-ML-WS-128 — Phase 0-cascor: Cascor /ws/training emits monotonic seq, advertises server_instance_id+replay_buffer_capacity, supports resume, fixes state coalescer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-91)

**Notes**:

Phase 0-cascor major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-014 — Phase 1 (canopy-only) — COMPLETE.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 160-168)

**Detail**:

| Fix pre-existing test failures (5 in `test_response_normalization.py`) | ✅ Fixed       | Backlog Sprint 1 |

### JR-CAN-ARCH-002 — Phase 1 Addendum—6 backend fixes (KeyError guards, thread safety, connection leaks).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 262-270)

**Detail**:

1.4.1: Guard get_dataset against KeyError on partial data (MED-036).
1.4.2: Fix prepare_dataset_for_visualization None crash (MED-038).
1.4.3: Thread-safe locking for Cassandra singleton (MED-039).
1.4.4: Thread-safe locking for Redis singleton (MED-041).
1.4.5: Fix Redis exception aliases to use sentinel class (MED-042).
1.4.6: Fix Redis force_new=True connection leak (MED-043).

### JR-CAN-TEST-018 — Phase 2 CI/CD Infrastructure Reliability (12 tasks).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 104-138)

**Detail**:

Step 2.1 (5 CI tasks): Fix lockfile extras, add permissions, fix pip-audit,
define dev extra, add Codecov upload.
Step 2.2 (3 security tasks): Consolidate bandit config, standardize invocations,
fix mypy strict_optional conflict.
Step 2.3 (4 Docker tasks): Create prod config, pin deps via lockfile,
fix service URLs, change log handler to append mode.

### JR-ML-API-020 — Phase 2: Backend API.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 528-537)

**Detail**:

1. Update `/api/set_params` endpoint to accept new keys

### JR-CAN-ARCH-003 — Phase 3 Addendum—5 backend quality improvements (circuit breaker, lazy imports, API exposure).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 271-277)

**Detail**:

3.5.1: Cache network property or wrap in circuit breaker (MED-034).
3.5.2: Narrow relay loop exception handling (MED-035).
3.5.3: Lazy-import torch in data_adapter.py (MED-037).
3.5.4: Expose public API on CascorServiceAdapter (MED-046).
3.5.5: Don't store Cassandra credentials as plain attributes (MED-040).

### JR-CAN-DOC-004 — Phase 3 Code Quality & Observability (18 tasks).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 141-186)

**Detail**:

Step 3.1 (6 logging): Fix ColoredFormatter mutation, cache logger wrappers,
make Sentry sample rate configurable, normalize Prometheus labels, use async
health checks, set production log levels.
Step 3.2 (5 dead code): Remove unused candidate pool display, orphaned callbacks,
extract create_empty_plot(), deprecate legacy TrainingMetricsComponent.
Step 3.3 (5 frontend): Extract colors to theme_constants, fix modulo toggle,
fix doc links, remove blocking time.sleep(), split NetworkVisualizer callback.
Step 3.4 (2 perf): Reduce API timeout, begin DashboardManager extraction.

### JR-ML-TRAIN-045 — Phase 3: Layout.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 537-544)

**Detail**:

1. Replace Training Parameters card with Meta Parameters card

### JR-CAN-TEST-019 — Phase 4 Addendum—6 test quality fixes (context suppression, schema tests, coverage gaps).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 279-287)

**Detail**:

4.3.1: Remove contextlib.suppress(Exception) from assertions (HIGH-016).
4.3.2: Add pytest.fail() guards to WebSocket schema tests (HIGH-017).
4.3.3: Remove hasattr guards from unit tests (HIGH-018).
4.3.4: Rewrite performance test without exception suppression (HIGH-019).
4.3.5: Add dedicated tests for parameters_panel.py (55.3% gap).
4.3.6: Expand candidate_metrics_panel.py callback tests (65.6% gap).

### JR-ML-OBS-044 — Phase 6: Finalize.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 563-607)

**Detail**:

1. Run linters (black, isort, flake8)

### JR-ML-SEC-081 — Phase B-pre-a: Origin allowlist, per-IP cap, frame-size cap, audit logger skeleton on `/ws/training`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 334-430)

**Detail**:

Cascor side: Origin validation (M-SEC-01), empty list = fail-closed, case-insensitive host, null origin rejected.
Per-IP connection cap = 5 default, configurable. `_per_ip_counts` dict under lock.
Frame size limit: `max_size=4096` on receive_* calls. Canopy side: duplicate Origin helper (copy, not import).
`Settings.allowed_origins` with localhost/127.0.0.1 defaults. `max_size=4096` on canopy's `/ws/training`.
Audit logger skeleton: `canopy.audit` logger (new module), JSON formatter, TimedRotatingFileHandler daily rotation,
30-day retention, scrub allowlist (no raw payloads). No Prometheus counters yet (land in Phase B).
"One resume per connection" rule: `resume_consumed: bool` per connection, second resume closes 1003.
GAP-WS-19 regression test: `test_close_all_holds_lock`.
Tests: frame size limit 1009, per-IP 6th rejected 1013, origin allowlist matrix, audit log format + rotation, empty allowlist rejects all, second resume closes 1003.
Observability: `canopy_ws_origin_rejected_total{origin_hash, endpoint}` (hashed),
`canopy_ws_oversized_frame_rejected_total{endpoint}`, `canopy_ws_per_ip_cap_rejected_total{endpoint}`,
`canopy_audit_events_total{event_type}`.

**Design**:

Two-PR sequence, cascor→canopy. M-SEC-03 (frame size) + M-SEC-04 (per-IP cap) + M-SEC-07 (audit skeleton).
Origin allowlist on `/ws/training` specifically (read-path). Gates Phase B only.

**Notes**:

Parallel with Phase 0-cascor and A-SDK. Exit gate: empty allowlist = fail-closed (HALT if fail-open).
Rollback: env flags (`JUNIPER_WS_ALLOWED_ORIGINS='*'` ignored by parser; instead use high cap `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=1000`).

### JR-ML-SEC-082 — Phase B-pre-a: Origin on /ws/training, size caps, per-IP cap, idle timeout, audit-logger skeleton.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-93)

**Notes**:

Phase B-pre-a major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-083 — Phase B-pre-b: Origin on /ws/control, cookie session + CSRF first-frame, rate limit, idle timeout, adapter HMAC, audit Prom counters.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 597-699)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-95)

**Detail**:

Cookie session + CSRF (canopy): SessionMiddleware added (or reused if present).
`/api/csrf` endpoint returns CSRF token bound to session (constant-time comparable via `hmac.compare_digest`).
Dash template injects CSRF token via data attribute. `/ws/control` first frame must be `{type: "auth", csrf_token: "..."}` within 5 s;
invalid/absent/expired → close 1008. Cookie: `SameSite=Lax`, `HttpOnly`, `Secure` (prod).
M-SEC-06 opaque close: numeric codes only, no human-readable reasons.
Origin + rate limit (cascor): `/ws/control` validates Origin against `Settings.ws_allowed_origins` (same allowlist as `/ws/training`).
M-SEC-05 single-bucket rate limit: 10 cmd/s leaky bucket per-connection, 11th → close 1013.
M-SEC-10 idle timeout: >120 s idle → close 1008. Settings: `ws_idle_timeout_seconds = 120`.
Adapter auth: canopy computes `csrf_token = hmac(api_key.encode(), b"adapter-ws", sha256).hexdigest()` on connect.
First frame sent: `{type: "auth", csrf_token: <hmac>}`. Cascor derives same + compares with `hmac.compare_digest`.
Uniform code path (no `X-Juniper-Role` header special case).
M-SEC-11 adapter inbound validation: `cascor_service_adapter.py` wraps inbound with Pydantic `CascorServerFrame` (`extra="allow"`).
Malformed → log + increment `canopy_adapter_inbound_invalid_total` + continue.
M-SEC-07 extended log injection: audit logger escapes CRLF + tab in all logged strings (prevents log forgery).
Tests: CSRF required, binds to session constant-time, kill-switch works, Origin rejected, rate limit 11th cmd closes 1013,
idle timeout closes 1008, adapter sends HMAC on connect, inbound malformed logged+counted, CRLF injection escaped,
opaque close codes, session middleware exists, cascor rejects unknown params via extra="forbid".
Observability: `canopy_csrf_validation_failures_total`, `canopy_audit_events_total{event_type="csrf_failure"}`,
`cascor_ws_control_rate_limit_rejected_total`, `cascor_ws_control_idle_timeout_total`, `canopy_adapter_inbound_invalid_total`.

**Design**:

Two-PR sequence (cascor→canopy). M-SEC-01/01b (Origin) + M-SEC-02 (cookie+CSRF) + M-SEC-05 (rate limit) + M-SEC-10 (idle timeout) +
M-SEC-11 (adapter validation) + M-SEC-07 extended (log escaping). Gates Phase D (browser control buttons).
HMAC first-frame auth uniform with existing SDK auth pattern.

**Notes**:

[v3 xround merge: rounds=R2-0,R3-0, n=2] Parallel with Phase B. Entry: Phase B in main. Merge order strict: P8→P9 (P8 must land first, P9's adapter path depends on P8's handler).
Exit: all tests green, manual Origin/CSRF/rate-limit probes work, SessionMiddleware detected, adapter handshake works, 48h soak.
Rollback: `JUNIPER_DISABLE_WS_AUTH=true` (existing flag, 2 min TTF). Dedup candidate with R3-03. / Phase B-pre-b major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-015 — Phase B: Browser bridge drains /ws/training into Dash store, Plotly.extendTraces updates, polling killed, GAP-WS-24a/b latency pipe.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-94)

**Notes**:

Phase B major milestone from R3-03 Phase index (§2); orchestrates implementation effort

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

### JR-ML-ARCH-180 — Phase H: Normalize_metric audit + regression gate; CODEOWNERS hard gate; pre-commit hook.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-101)

**Notes**:

Phase H major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-016 — Phase I: Asset cache busting; bump assets_url_path / hash query param.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-102)

**Notes**:

Phase I major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-ARCH-181 — Phase: Switch (env var).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 337-338)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-CAN-TEST-020 — pip-audit in CI must scan full dependency tree, not just top-level.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 115-115)

**Detail**:

Issue 2.1.3: pip-audit command in .github/workflows/ci.yml is incomplete.
Must specify report file and scan transitive dependencies.

### JR-CAN-TOOL-001 — Post-release development roadmap: Phase 0 CRITICAL (integration gaps), Phase 1 HIGH (backend), validated complete for Phase 0-1 items.

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 1-100)

**Detail**:

Phase 0 CRITICAL: Integration Gaps (Decision Boundary, Save/Load Snapshot). Phase 1 HIGH: Backend integration (Health Check, NPZ Validation). Status: SUPERSEDED — execution tracked in juniper-ml/notes. Validated as complete for most Phase 0-1 items.

**Notes**:

Superseded by more recent development plans; cross-referenced for historical context and closure verification.

### JR-CAN-OBS-006 — Production default log levels must prevent debug spam in production.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 156-156)

**Detail**:

Issue 3.1.6: Default log level may be too verbose in production. Set
production-safe default (INFO/WARNING) independent of dev config.

### JR-CAN-OBS-007 — Prometheus endpoint labels must be normalized to prevent cardinality explosion.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 154-154)

**Detail**:

Issue 3.1.4: Endpoint labels may include query params, causing unbounded cardinality.
Normalize to path template (e.g. /api/v1/params/{id} not /api/v1/params/123).

### JR-CAN-LOCK-002 — pyproject.toml must define 'dev' extra for dependency management.

**Status**: proposed  **Priority**: P1  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 116-116)

**Detail**:

Issue 2.1.4: Missing dev extra for development dependencies. Define
[project.optional-dependencies] with 'dev' key including test/lint tools.

### JR-ML-API-021 — Reconnect protocol must handle resume frames within 5s timeout and emit resume_ok or resume_failed response.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-03-MAXIMALIST-COMPREHENSIVE.md` (lines 420-490)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 389-412)

**Detail**:

training_stream handler: await asyncio.wait_for(ws.receive_json(), timeout=5.0) for optional first frame.
If type=="resume": check server_instance_id, call replay_since(), emit resume_ok + replayed OR resume_failed.
Failure reasons: server_restarted (instance mismatch), out_of_range (seq too old), malformed_resume (missing fields).
If first frame is not resume or timeout: treat as fresh client, route through normal handler.
Promote to active only after resume handling completes.

**Notes**:

Phase A-server (Day 3). R0-03 §6.1 "initial_status race" documented in code comment. Scenarios in §8.

### JR-ML-ARCH-182 — Recovery: kill switches work.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 150-151)

### JR-CCL-ARCH-002 — Refactor testing/fake_client.py to use testing constants (~40 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 50-52)
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 54-56)
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 42-45)
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-49)

**Notes**:

[v3 xrepo fuzzy merge: owners=ccl,dcl, n=4] Part of hardcoded-values refactor (HIGH priority)

### JR-ML-DEP-017 — Release readiness checklist: pre-commit compliance, test pass, version sync across 6 applications.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 1-50)

### JR-ML-API-022 — Releases must follow the dependency graph:.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 351-364)

**Detail**:

1. juniper-data (upstream, no Juniper dependencies)

**Notes**:

[v3 brief repaired from cited content; was: '5.1 Tag & Release Order']

### JR-ML-TEST-015 — Remediate cross-project regression issues identified in 2026-04-03 analysis.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REGRESSION_REMEDIATION_PLAN_2026-04-03.md` (lines 1-100)

### JR-ML-TRAIN-046 — Remediate training stall issue with identified root cause and proposed solution.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/TRAINING_STALL_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Blocking training completion; high priority fix.

### JR-CAN-API-027 — Remove duplicate cn_patience configuration parameter.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 76-76)

**Detail**:

Issue 1.1.4: cn_patience appears twice in configuration. Consolidate to single
canonical definition. File: src/main.py

### JR-CAS-ARCH-008 — Remove or archive stale duplicate check.py file (outdated copy of spiral_problem.py).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 329-342)

**Detail**:

src/spiral_problem/check.py contains complete but outdated copy of SpiralProblem class
using old-style constructor parameters. Dead code creating confusion. Remove or archive.

### JR-CAN-TEST-021 — Replace 8 always-passing assert True tests with real assertions using pytest.raises().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 86-98)

**Detail**:

Tests in performance and integration suites use assert True in both success and exception branches. Provides false confidence; regressions undetectable.

**Notes**:

Category A: 8 critical test issues; Phase 1 critical

### JR-CAN-UI-017 — Replace debounce=True with 350ms on numeric inputs to fix perceived typing lag.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 365-499)

**Detail**:

Issue: spinner changes commit immediately but typed values require blur.
Solution: use debounce=350ms for live feedback without callback churn.
Also adds clientside blur-on-Apply and validation styling (invalid=True border).

**PRs**: PR-2 (Phase 6B, Issue

### JR-ML-WS-131 — replay_since(last_seq) + ReplayOutOfRange exception; copy-under-lock pattern.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 115-115)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-API-023 — Requires network access and many requests; mitigated by rate limiting.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 492-505)

**Notes**:

[v4 brief repaired; was: '6.1 Risks']

### JR-ML-TEST-016 — Resolve CI validation findings: categorize, root-cause, fix per priority (P0/P1/P2/P3).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-FINDINGS.md` (lines 1-50)

### JR-CCL-TEST-005 — Run full test suite validation after constants refactor to ensure scenario outputs and behaviors unchanged.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 62-71)

**Detail**:

Execute: pytest tests/ -v
Verify scenario generation for two_spiral, xor_converged, and empty scenarios.
Validate metric curves, topology, and decision boundary data match pre-refactor.

**Notes**:

Validation phase of refactor (HIGH priority)

### JR-ML-SEC-084 — SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 169-184)

### JR-ML-SEC-085 — SEC-02: Rate Limiter Memory Unbounded — DoS Vector.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 187-209)

### JR-ML-SEC-086 — SEC-03: No Per-IP WebSocket Connection Limiting (cascor).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 212-226)

### JR-ML-SEC-087 — SEC-04: Sync Dataset Generation Blocks Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 229-244)

### JR-ML-SEC-088 — SEC-05: Cross-Site WebSocket Hijacking (CSWSH) — No Origin Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 247-261)

### JR-ML-SEC-089 — SEC-06: No Auth on Canopy WS Endpoints.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 264-278)

### JR-ML-SEC-090 — SEC-07: Unvalidated `params` Dict Values in TrainingStartRequest.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 281-295)

### JR-ML-SEC-091 — SEC-10: Sentry `send_default_pii=True` (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 298-312)

### JR-ML-SEC-092 — SEC-11: `pickle.loads` HDF5 Snapshot Data Without RestrictedUnpickler.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 315-337)

### JR-ML-SEC-093 — SEC-12: `/ws` Generic Endpoint Missing Origin/Per-IP Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 340-354)

### JR-ML-SEC-094 — SEC-13: Auth Secrets Exposed via Query Params (`/api/remote/connect`).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 357-379)

### JR-ML-SEC-095 — SEC-14: Internal Exception Messages Leaked to Clients.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 382-396)

### JR-ML-SEC-096 — SEC-15: Cascor Sentry `send_default_pii=True`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 399-413)

### JR-ML-SEC-097 — SEC-16: `/metrics` Prometheus Endpoint Bypasses Auth Middleware.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 416-430)

### JR-ML-SEC-098 — SEC-17: Snapshot `snapshot_id` Path Param Unchecked for Traversal.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 433-447)

### JR-ML-SEC-099 — SEC-18: `_decode_binary_frame` No Bounds Check (cascor-worker).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 450-464)

### JR-ML-SEC-100 — Security remediation for identified vulnerability in PR#40.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PR40_SECURITY_REMEDIATION_PLAN.md` (lines 1-100)

### JR-ML-SEC-101 — Security remediation for juniper-deploy PR#14.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/JUNIPER_DEPLOY_PR14_SECURITY_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Security issue in deployment pipeline.

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

### JR-CAN-OBS-008 — Sentry sample rate must be configurable via environment variable.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 153-153)

**Detail**:

Issue 3.1.3: Sentry sample_rate hardcoded. Add SENTRY_SAMPLE_RATE env var
with sensible default (0.1 for production, 1.0 for dev).

### JR-ML-API-024 — Server must advertise server_instance_id (UUID) in connection_established and snapshot_seq in status endpoint.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-03-MAXIMALIST-COMPREHENSIVE.md` (lines 392-410)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 283-299)

**Detail**:

connection_established frame (sent via send_personal_message, bypassing replay buffer) includes server_instance_id, server_start_time, replay_buffer_capacity.
/api/v1/training/status endpoint adds atomic snapshot under _seq_lock: payload["snapshot_seq"] = manager._next_seq - 1.
Also advertise server_instance_id in status endpoint.
Client uses server_instance_id to detect server restarts and reject out-of-date resume attempts.

**Notes**:

Phase A-server (Days 2-3). Atomicity of snapshot_seq with state read is load-bearing (Day 3 commit 6).

### JR-CAS-TEST-007 — Set and enforce minimum coverage thresholds: 70% overall, 80% for core snapshots module.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 632-647)

### JR-ML-API-025 — SetParamsResponse wire model with extra=allow.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 224-224)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-API-026 — Step 3: Add Regression Tests.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 95-145)

**Detail**:

#### New file: `src/tests/unit/test_convergence_ui_regression.py`

### JR-ML-TRAIN-047 — **Strengths of B**: More explicit parsing, handles whitespace in values.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 131-171)

**Detail**:

**2.1.1 CI path fix** (`ci.yml:244`):

**Notes**:

[v3 brief repaired from cited content; was: '2.1 juniper-ml: CI & Script Fixes']

### JR-ML-OBS-045 — Swap PrometheusMiddleware and RequestIdMiddleware order in canopy main.py:312 to fix mis-labeling.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 162-168)

**Detail**:

G5 - Middleware order causes request-id ContextVar to be unset during metric labeling.
One-line fix. Add unit test asserting request-id header present in metric labels.

### JR-ML-SEC-102 — Task 1 (Metrics).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 381-404)

**Detail**:

- Card pattern: `html.Div([html.H5(), html.H2(id=...)])` with flex layout (lines 393-428)

### JR-DAT-TEST-007 — Test code quality: tests must not be excluded from flake8, mypy, or pytest checks.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 58-76)

**Detail**:

TST-002: Tests excluded from Flake8 (HIGH).
TST-003: Tests excluded from MyPy (HIGH).
TST-004: Pytest warnings suppressed (HIGH).
CFG-001: Excessive Flake8 ignores E722, F401 (HIGH).
33+ flake8 violations hidden (F401 7, F541 5, SIM117 21).

**Notes**:

P1 HIGH issues. 34 total violations currently undetected.

### JR-CWK-TEST-001 — Test import mocking fix: add patch.dict(sys.modules, {"cascade_correlation": None, ...}) to test_connect_without_cascor_raises and test_start_without_cascor_raises to force ImportError regardless of JuniperCascor environment.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/history/FIX_TEST_IMPORT_MOCKING_PLAN.md` (lines 1-50)

**Detail**:

Two tests fail when run in JuniperCascor conda environment where cascade_correlation package is installed: (1) test_connect_without_cascor_raises expects ImportError handler but import succeeds, code attempts real TCP connection to manager (127.0.0.1:50000), gets ConnectionRefusedError wrapped as WorkerConnectionError, regex match fails. (2) test_start_without_cascor_raises bypasses "Not connected" guard, import succeeds, code spawns real forkserver processes, returns normally without raising. Fix: wrap both tests' calls to worker.connect()/start() in patch.dict(sys.modules, {"cascade_correlation": None, "cascade_correlation.cascade_correlation": None}), forcing ImportError on import statement. Matches existing pattern in 6 other tests (lines 87, 115, 134, 161, 186, 307). Setting sys.modules key to None causes Python's import machinery to raise ImportError: import of <module> halted; None in sys.modules.

### JR-CAN-TEST-022 — Test Suite & CI/CD Enhancements (16 epics, 145 total hours).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 1-50)

**Detail**:

Phase 1 (21h): Eliminate false-positive tests (9 assert True), move non-test files,
fix security scan suppression.
Phase 2 (39h): Consolidate conftest.py, re-enable MyPy codes, enable linting on tests.
Phase 3 (50h): Fix weak tests, address unconditional skips, fix exception suppression,
re-enable flake8 checks, remove duplicate test classes, fix bug-documenting tests.
Phase 4 (35h): Configuration standardization, docs, future MyPy, extended suppress review.

### JR-CAS-TEST-008 — Test suite optimization: force sequential training, remove coverage from defaults, fix test collection, optimize fixtures.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_PERFORMANCE_IMPROVEMENT_PLAN.md` (lines 1-250)

**Detail**:

Phase 1 (critical): Force sequential training via conftest autouse fixture patching _calculate_optimal_process_count to return 1. Phase 2: Remove coverage from pytest.ini addopts (2-3x speedup). Phase 3: Fix test_hdf5.py import path. Phase 4: Create lightweight network_with_hidden_units fixture. Phase 5: Harden worker shutdown (bounded total timeout, CASCOR_NUM_PROCESSES env var). Phase 6 (applied): Patch Logger._log_at_level to no-op, torch warmup fixture, mock fit() in tests, reduce epochs. Results: 500+s → 12-24s (86-93% reduction), 1408 passed, 15 skipped.

**Notes**:

[v2 remap: TI→TEST]

### JR-ML-TEST-017 — testing/fake_ws_client.py: on_command(name, handler) auto-scaffold command_response reply.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 225-225)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-UI-017 — The Meta Parameters card will be 2-3x taller than the current Training Parameters card. Guardrails:.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 448-460)

**Notes**:

[v3 brief repaired from cited content; was: '7.5 UI Overflow']

### JR-ML-SEC-103 — The metaparameter update flow works through these stages:.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 146-188)

**Detail**:

**Repositories**: juniper-canopy, juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '1.3 Metaparameter Wiring Gaps']

### JR-ML-TRAIN-048 — Training Control.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 315-323)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 251-259)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-WS-134 — training_stream.py two-phase registration, resume/resume_ok/resume_failed handler with 5s timeout.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 116-116)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-TEST-018 — Unit tests for apply_params() routing and feature flag.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-05-TESTING-VALIDATION.md` (lines 252-261)

### JR-ML-TEST-019 — Unit tests for seq numbers, replay buffer, and resume protocol.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-05-TESTING-VALIDATION.md` (lines 171-207)

### JR-ML-TEST-020 — Unit tests for set_params() method and concurrent correlation.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-05-TESTING-VALIDATION.md` (lines 212-237)

### JR-ML-SEC-104 — Update TrainingState at each grow iteration boundary:.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 521-534)

**Detail**:

**Effort**: 1-2 days | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '5.3 Grow-Network State Updates']

### JR-ML-DATA-008 — `_update_topology_store_handler` returns `{}` instead of `dash.no_update` on error — **NOT FIXED** (OI-1)

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 66-82)

**Detail**:

| DATASET_DISPLAY_BUG_ANALYSIS.md               | Dataset tab blank        | RC-1 stale install, RC-2 FakeClient, CF-1..CF-3 | **FIXED** — `get_dataset_data()` added to client (6ed0fda), FakeClient (be17329), version bumped to 0.3.0 (09adb16), `hasattr` guard + broad exception in adapter (line 707)

**Notes**:

[v3 brief repaired from cited content; was: '2.1 Documents in `notes/development/`']

### JR-ML-ARCH-183 — `use_websocket_set_params`: C.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 310-311)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-SEC-105 — Validate Anthropic API key access patterns across repos; ensure keys not logged or exposed in responses.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md` (lines 1-50)

### JR-ML-TEST-021 — Validate CI pipeline: every workflow runs green, soft-fail jobs promoted per-repo to hard gates after shakedown.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-ROADMAP.md` (lines 28-51)

### JR-ML-OBS-046 — Wire 9 cascor WS metrics (resume/replay/throttle observability) via OBS-WIRE-02, behind feature flag.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 148-162)

**Detail**:

G4 - 11 dead cascor_ws_* metrics with zero production callers defined but unwired.
OBS-WIRE-02 wires 9 viable metrics. Remove cascor_ws_seq_gap_detected_total and cascor_ws_connections_active as not feasible.
Deploy behind JUNIPER_CASCOR_WS_METRICS_FULL feature flag initially.

### JR-ML-OBS-047 — Work Unit 2: Metrics Panel Table Dark Mode (MEDIUM-HIGH).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 83-129)

**Detail**:

**Issues**: 1E (lines 1759, 1819, 1904)

### JR-ML-API-027 — Work Unit 4: Service Mode Verification (LOW) — IMPLEMENTED.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 144-161)

**Detail**:

Added 5 integration tests to `test_network_stats_endpoint.py` (`TestNetworkStatsServiceMode` class) that mock the backend as service mode with realistic multi-hidden-unit weight data. Tests verify:

### JR-ML-OBS-048 — WS metrics audit A9 + integration 3.2: expose buffer occupancy, connection state, frame sizes as Prometheus gauges.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md` (lines 1-50)

### JR-ML-ARCH-184 — `ws_backpressure_policy`: E.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 316-317)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-185 — `ws_rate_limit_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 314-315)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-186 — `ws_security_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 312-313)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-DATA-010 — Phase 3 integration test: a `cascade_add` WebSocket message must trigger a topology broadcast

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 775-794)

**Detail**:

test_websocket_topology_push.py — New integration test

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 3 Tests']

[2026-08-29 brief repaired from cited content; was: '"""cascade_add WebSocket message must trigger topology broadcast."""']

### JR-ML-TRAIN-054 — Phase 2 test: the demo backend must produce hidden-to-hidden cascade connections

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 760-775)

**Detail**:

`# Setup: create network with 2+ hidden units`

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 2 Tests']

[2026-08-29 brief repaired from cited content; was: '"""Demo backend must produce hidden-to-hidden cascade connections.""".']

### JR-ML-OBS-061 — """Exception during REST poll must NOT overwrite topology store.""".

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 736-760)

**Detail**:

mock_requests.get.return_value = Mock(ok=False, status_code=503)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 1 Tests']

### JR-ML-API-032 — "cn_candidate_selection": None,  # no default; sub-group disabled when checkbox unchecked.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 267-302)

**Detail**:

"cn_candidate_selection": None,  # no default; sub-group disabled when checkbox unchecked

**Notes**:

[v3 brief repaired from cited content; was: '4.4 Applied Params Store Structure']

### JR-CAS-TOOL-005 — 10 open/remaining work items: hardcoded paths, stale files, fallback bugs, version inconsistencies, legacy directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 160-180)

**Detail**:

INT-P0-004: remote_client_0.py hardcoded path to monorepo (delete, superseded by juniper-cascor-worker). INT-P0-005: Hardcoded test paths (sys.path.append lines). INT-P1-008: check.py stale duplicate. INT-P2-005/006: or fallback bugs (clockwise, numeric params) → if x is not None pattern. INT-P2-014: Local traceback imports (use top-level, remove 9 instances). INT-P3-009: Version strings inconsistent (main.py 0.3.1, cascade_correlation.py 0.3.2, pyproject.toml 0.4.0). Legacy remote_client/ directory (remove or archive). Estimated effort 2-4 hours total.

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-DATA-011 — 2.4.1 Fix `wait_for_ready()` (`client.py:86`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 204-214)

**Detail**:

**2.4.1 Fix `wait_for_ready()`** (`client.py:86`):

**Notes**:

[v3 brief repaired from cited content; was: '2.4 juniper-cascor-client: Semantic & Coverage Fixes']

### JR-ML-OBS-062 — 2B. Training Progress Summary Cards.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 88-99)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-OBS-063 — 2C. Learning Rate Metric Card.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 99-108)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-OBS-064 — 2E. Hidden Units Progress Ratio.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 116-128)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`, `src/frontend/dashboard_manager.py`

### JR-ML-SEC-122 — 4 test files with `requires_server` skip marker — need CI integration environment.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 175-193)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 144-158)

**Detail**:

| CLN-CN-01 | **P2**   | `theme-table` CSS class not yet implemented                        | No `.theme-table` in any CSS file — conditional `is_dark` styling used instead    | S      |

**Notes**:

[v4 brief repaired; was: '6.2 juniper-canopy — Code Quality']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-OBS-065 — 5 fast/slow pairs = 10 MWMBR rules of the 16 page+ticket count;.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 456-472)

**Detail**:

| 3.1 Canopy dashboard availability | `CanopyDashboardAvailabilityFastBurn` | `CanopyDashboardAvailabilitySlowBurn` |

**Notes**:

[v3 brief repaired from cited content; was: '7.2 MWMBR burn-rate pairs']

### JR-CAN-TEST-023 — 9+ skipped/placeholder tests contain only pass or skip decorator without real test logic.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

**Detail**:

Placeholder tests with no assertions or logic do not test anything. Must implement real test logic or remove.

**Notes**:

Identified in test audit; blocks coverage.

### JR-ML-SEC-123 — [ ] All tests pass (`pytest -v` or `python3 -m unittest -v`).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 314-327)

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Pre-Release Validation Checklist']

### JR-ML-ARCH-212 — [ ] **Task 4.1.2**: Add dark mode font color toggling based on theme state.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md` (lines 206-239)
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md` (lines 205-238)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 4:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md

---

[v3 brief repaired from cited content; was: 'Phase 4:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-OBS-066 — [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) §6 — residual follow-ups….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 409-415)

**Detail**:

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) §6 — residual follow-ups (juniper-ml#192)

**Notes**:

[v3 brief repaired from cited content; was: 'Primary']

### JR-ML-OBS-067 — [x] `set_params` works via WebSocket control channel — verified and new integration tests added (2026-04-09).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 207-216)

**Detail**:

- [x] New tests added for all changes — `test_websocket_control.py` (3 tests), `test_lifecycle_manager.py` (1 test)

**Notes**:

[v3 brief repaired from cited content; was: '3.4 Phase 1 Success Criteria']

### JR-ML-ARCH-213 — [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md` (lines 156-230)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 3:'] From JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md

### JR-ML-UI-028 — A.1 Startup Scripts.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 818-831)

**Detail**:

| `util/juniper_plant_all.bash`    | juniper-ml     | Start all (host)    | Active (overhauled, commit `03aec86`) |

### JR-ML-DEP-018 — A.2 Container/Deploy Files.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 831-846)

**Detail**:

| `docker-compose.yml`                  | juniper-deploy | Primary orchestration | Active     |

### JR-ML-SEC-124 — A.3 Health Check Scripts.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 846-855)

**Detail**:

| `scripts/health_check.sh`         | juniper-deploy | Full stack health          |

### JR-ML-OBS-068 — A.4 CasCor Query Utilities.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 855-866)

**Detail**:

| `util/get_cascor_status.bash`       | juniper-ml | `/v1/training/status`           |

### JR-ML-OBS-069 — A.5 Configuration Files.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 866-880)

**Detail**:

| `.env.example`                  | juniper-deploy | Full config template    |

### JR-ML-API-033 — A.6 Application Entry Points.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 880-895)

**Detail**:

| `juniper_data/__main__.py`     | juniper-data          | `python -m juniper_data` |

### JR-CAN-UI-025 — About panel documentation links must be validated and repaired.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 170-170)

**Detail**:

Issue 3.3.3: Broken or outdated documentation links in About panel.
Audit all links and update URLs or remove invalid references.

### JR-ML-TRAIN-055 — Adam Optimizer Pathology: fix Adam optimizer pathology issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-07-ADAM-OPTIMIZER-PATHOLOGY.md` (lines 1-44)

### JR-ML-WS-139 — Adapter→cascor auth = HMAC first-frame, NOT X-Juniper-Role header.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 47-47)

**Notes**:

Settled position C-10 from R3-03 table; cross-round consensus consolidation

### JR-DCL-DOC-006 — Add CI/CD documentation section to AGENTS.md covering 3 GitHub Actions workflows.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-134)

**Detail**:

AGENTS.md has no CI/CD documentation. Agents making changes should know: ci.yml runs multi-version
tests (Python 3.12, 3.13, 3.14), pre-commit hooks, coverage checks (80% threshold), security scanning;
publish.yml handles PyPI publishing with trusted publishing (OIDC) and build attestations;
security-scan.yml runs weekly Bandit + pip-audit scanning.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.2) and AGENTS_MD_UPDATE_PLAN (Step 3.2).

### JR-CCL-DOC-008 — Add CI/CD Pipeline section to AGENTS.md documenting GitHub Actions workflow structure, quality gates, downstream dispatch.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 57-60)

**Notes**:

Medium severity: improves agent understanding of CI workflows

### JR-DEP-SEC-004 — Add container image security scanning (Trivy or Grype) to CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 197-203)

**Detail**:

Phase 4. Add security-scan job to CI using Trivy or Grype. Scan all locally-built
images after build step. Fail on critical/high CVEs; warn on medium. Cache
vulnerability database to reduce CI time.

### JR-CAS-TEST-010 — Add coverage report --fail-under gate and per-module thresholds to CI.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 501-511)

**Detail**:

CI/CD coverage gates not enforced. Add `coverage report --fail-under=80` to CI,
configure per-module thresholds, add coverage badge to README.

### JR-CCL-DOC-009 — Add Environment Variables section to AGENTS.md documenting JUNIPER_CASCOR_API_KEY and CASCOR_SERVICE_URL.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 71-73)

**Notes**:

Medium severity: documents runtime configuration

### JR-ML-DEP-019 — Add `FakeCascorClient` to the `juniper-cascor-client` package that implements the same interface as `JuniperCascorClient` with configurable….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 2870-3070)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 6:']

### JR-CAS-PERF-002 — Add GPU/CUDA support for all tensor operations and training.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 885-912)

### JR-ML-UI-029 — Add indeterminate progress animation during candidate training.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 534-543)

**Detail**:

**Effort**: 2 days | **Repo**: juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '5.4 Canopy Progress Indicators']

### JR-ML-TEST-023 — Add integration test for Canopy demo mode toggle with juniper_canopy_demo_mode_active metric.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 51-52)

**Detail**:

R3.2: Toggle demo mode; assert metric reflects within one update tick.

### JR-CAN-TEST-024 — Add integration tests for async/sync boundary with WebSocket responsiveness during training.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 168-189)

**Detail**:

No integration tests verify WebSocket responsiveness during active training; schedule_broadcast() uses run_coroutine_threadsafe but has no tests.

**Notes**:

Phase 2 high priority; training callbacks are registered but untested in integration context

### JR-CCL-DOC-010 — Add Linting & Formatting section to AGENTS.md documenting line length (512), tool versions, complexity limits, pre-commit hooks.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 62-64)

**Notes**:

Medium severity: supports local quality enforcement

### JR-ML-TEST-024 — Add live integration test for juniper-data dataset generation with metrics assertion.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 47-49)

**Detail**:

R3.1: POST /v1/datasets, scrape /metrics, assert juniper_data_dataset_generations_total counter and duration histogram.

### JR-ML-API-034 — Add near the top after configurable paths:.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 310-353)

**Detail**:

if [[ "${1:-}" == "--systemd" ]]; then

**Notes**:

[v3 brief repaired from cited content; was: '5.8 Plant/chop --systemd mode (Step 2.8)']

### JR-ML-OBS-070 — Add `on_epoch_callback` parameter to `train_output_layer()`:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 505-521)

**Detail**:

**Effort**: 1-2 days | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '5.2 Option C: Output Training Callback']

### JR-ML-OBS-071 — Add phase="input" and phase="candidate" emission sites in cascor training_step_duration_seconds.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 169-178)

**Detail**:

G6 - training_step_duration_seconds only emits phase="output" despite SLO design intent of three phases.
Add input/candidate emission sites at corresponding training stages.

### JR-ML-TRAIN-056 — Add `progress_queue` to persistent forkserver worker pool:.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 543-556)

**Detail**:

**Effort**: 3-5 days | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '5.5 Option A: Candidate Progress Queue']

### JR-CCL-DOC-011 — Add Python Version Support note to AGENTS.md documenting >=3.11, tested on 3.11-3.14.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 78-79)

**Notes**:

Medium severity: clarifies compatibility constraints

### JR-ML-TEST-025 — Add replay buffer overflow test for CasCor with eviction verification.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 57-59)

**Detail**:

R3.5: Drive API_METRICS_BUFFER_SIZE + 1 updates; assert oldest evicted, newest retained, no exception.

### JR-DEP-TEST-001 — Add scheduled weekly integration tests to detect upstream breakage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 184-195)

**Detail**:

Phase 4 (v0.5.0) CI enhancement. Add schedule: cron: '0 6 * * 1' trigger to
.github/workflows/ci.yml or dedicated workflow. Run full Docker integration suite
weekly against main to detect upstream breakage. Notify on failure via GitHub Actions.

### JR-CCL-SEC-002 — Add Security section to AGENTS.md documenting SOPS encryption, Gitleaks, Bandit, pip-audit.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 75-76)

**Notes**:

Medium severity: documents security tooling

### JR-ML-UI-030 — Add symlink `scripts/juniper-ctl` -> `juniper-canopy-ctl`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 107-128)

**Detail**:

- ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8050

**Notes**:

[v3 brief repaired from cited content; was: '5.1 juniper-canopy changes (Step 2.3)']

### JR-CCL-DOC-012 — Add Test Organization section to AGENTS.md documenting test structure, markers, fixtures, 80% coverage requirement.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 66-69)

**Notes**:

Medium severity: helps agents understand test conventions

### JR-ML-SEC-125 — Add `TestBatchOperations` and `TestVersioning` classes in `test_client.py` using `@responses.activate`. Cover:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 188-204)

**Detail**:

**2.3.1 Add PATCH to retry allowed_methods** (`client.py:101`):

**Notes**:

[v3 brief repaired from cited content; was: '2.3 juniper-data-client: Test & Retry Fixes']

### JR-ML-TRAIN-057 — Add tests for `run()` → `_message_loop()` → `_handle_task_assign()` flow, `_heartbeat_loop`, and connection loss/reconnection. Target:….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 214-243)

**Detail**:

**2.5.1 Fix signal handler thread safety** (`worker.py:121`, `cli.py:95`):

**Notes**:

[v3 brief repaired from cited content; was: '2.5 juniper-cascor-worker: Thread Safety & Coverage']

### JR-ML-API-035 — **Add topology hash based on weights**: Include a hash or generation counter for weight values in the topology hash function so the network.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 533-549)

**Detail**:

5. **Add topology hash based on weights**: Include a hash or generation counter for weight values in the topology hash function so the network visualization redraws when weights change during

**Notes**:

[v4 brief repaired; was: '7.2 Short-Term (Medium)']

### JR-ML-OBS-072 — Add warning-level logging to the exception handler:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 457-473)

**Detail**:

logger.warning("Failed to extract network topology: %s: %s", type(e).__name__, e)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix']

### JR-ML-OBS-073 — Additional Work Completed (not in original plan).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 404-418)

**Detail**:

| GIL contention test fix | 04db7e6 | Rewrote flaky training loop tests to use thread.join instead of polling |

### JR-CAS-TOOL-006 — Address 7 codebase analysis issues: logging system gaps, startup robustness, constants over-engineering, security risks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/CODEBASE_ANALYSIS_2026-03-12.md` (lines 1-100)

**Detail**:

Logging: YAML relative paths, three independent mechanisms, CWD-dependent resolution. Startup: os._exit() usage, module-level Sentry init, lru_cache on get_settings(). Architecture: dual logging systems (CLI vs API), constants over-engineering (7 sub-packages), name-mangled constructor params, sys.path manipulation, deprecated docker-compose. Code quality: exception handling breadth, global state, LogConfig Java-style getters/setters, commented-out code, walrus operator misuse. Security: CORS wildcard risk, Sentry PII collection, nosec without ticket.

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-ARCH-214 — **After deduplication**: ~85 unique items not present in v2.0.0.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 588-594)

**Detail**:

- **After deduplication**: ~85 unique items not present in v2.0.0

**Notes**:

[v3 brief repaired from cited content; was: 'Results']

### JR-ML-TRAIN-058 — After training fails or completes, `start_training()` bypasses the guard (only checks `is_started()`), but `handle_command(Command.START)`….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 154-182)

**Detail**:

**Severity**: S1 | **Effort**: Medium (1 day) | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '3.2 CR-007: Auto-Reset State Machine on Start']

### JR-CAS-WS-004 — AGENTS.md documentation drift: 7-phase plan to align with service architecture, security, observability, CI/CD.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 1-150)

**Detail**:

Phase 1: Update version 0.3.17 → 0.4.0, restructure to lead with service architecture. Phase 2: Add server commands, environment variables, key entry points (server.py, api/app.py). Phase 3: Document REST API (endpoint inventory, auth), WebSocket protocol (3 channels), lifecycle management, remote workers, middleware. Phase 4: Security (API keys, rate limiting, headers, TLS), observability (JSON logging, Prometheus, Sentry). Phase 5: CI/CD workflows, deployment (Docker, Kubernetes), configuration. Phase 6: Update existing sections (directory structure, dependencies, testing). Phase 7: New sections (service launcher, MCP). Validation criteria listed.

### JR-ML-OBS-074 — Alert rules and recording rules exist but are not mounted in Prometheus container (see DD-DC-03).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 292-300)

**Detail**:

| DD-OBS-01 | **High**   | AlertManager config exists but is never deployed (see DD-DC-02).                                  |

**Notes**:

[v4 brief repaired; was: '5.4 Observability Issues']

### JR-ML-SEC-126 — **AlertManager service missing** from docker-compose.yml but referenced by Prometheus.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 363-374)

**Detail**:

1. **AlertManager service missing** from docker-compose.yml but referenced by Prometheus

**Notes**:

[v4 brief repaired; was: '6.6 High: Docker Infrastructure Gaps (juniper-deploy)']

### JR-ML-SEC-127 — AlertManager service missing from docker-compose.yml — `prometheus.yml:34` references `alertmanager:9093` but no service defined.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 402-419)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 317-330)

**Detail**:

| DEPLOY-01 | **HIGH**   | Docker secret name/path mismatch: `juniper_data_api_key` (singular) vs app expects `juniper_data_api_keys` (plural)              | `docker-compose.yml:499-500` vs service env var

**Notes**:

[v4 brief repaired; was: '13.1 Infrastructure Bugs (Confirmed Still Present)']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-128 — `alertmanager.yml` has empty receiver stubs, no real integrations.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 289-299)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 225-235)

**Detail**:

| 5.1  | Configure AlertManager receivers (Slack/email)   | 🔴 Placeholders only | `alertmanager.yml` has empty receiver stubs, no real integrations |

**Notes**:

[v4 brief repaired; was: '9.2 Phase 5: Observability & Hardening — INCOMPLETE']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-TOOL-002 — Algorithm Enhancements.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 323-330)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 259-266)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-CAS-ARCH-009 — Align inconsistent queue method names between remote_client.py and remote_client_0.py implementations.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 471-483)

**Detail**:

Two implementations register different queue names: get_task_queue/get_result_queue vs
get_tasks_queue/get_done_queue. Old client fails to connect to current manager.
Remove remote_client_0.py or align queue names.

### JR-CAN-API-028 — All JuniperData REST API interactions must have standardized error handling with status code mapping.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 199-211)

**Detail**:

Map HTTP status codes to user-friendly error messages; implement consistent retry and timeout patterns.
Estimated scope: 2-3 files, 100-200 lines.

**Notes**:

CAN-HIGH-006; HIGH priority post-release item.

### JR-ML-OBS-075 — All major exports re-exported through `juniper_data/api/observability.py` (back-compat shim); `DependencyStatus` / `ReadinessResponse` impor.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 236-249)

**Detail**:

| Repo | Declares dep in `pyproject.toml`? | Imports `juniper_observability`? | Components imported |

**Notes**:

[v4 brief repaired; was: '4.2 Adoption matrix']

### JR-ML-SEC-129 — All service files use the same hardening pattern as the existing canopy service:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 54-67)

**Notes**:

[v3 brief repaired from cited content; was: '2.6 Security hardening']

### JR-ML-TRAIN-059 — All structural IDs exist (headers, collapses, icons).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 460-471)

**Notes**:

[v4 brief repaired; was: '8.1 Unit Tests - Layout Verification']

### JR-ML-API-036 — All three services already implement Kubernetes-compatible health probes:.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 604-616)

**Detail**:

| **JuniperData**   | `GET /v1/health/live` → `{"status": "alive"}` | `GET /v1/health/ready` → `{"status": "ready", "version": ...}`                        | `GET /v1/health` |

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Current Health Endpoints']

### JR-CAS-TEST-011 — Always-passing tests with assert True must be replaced with real test logic.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 57-62)

**Detail**:

TST-001: tests in test_training_workflow.py:186-204 always pass. Real test logic
required to validate behavior.

### JR-ML-SEC-130 — Analyze juniper-deploy public release feasibility: dependencies, security, CI/CD readiness.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-09_JUNIPER-DEPLOY_GO-PUBLIC-ANALYSIS.md` (lines 1-50)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-131 — API key in plaintext over HTTP. Default URL is `http://`. No warning when API key is set with non-HTTPS URL.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 62-69)

**Detail**:

| ID        | Severity | File:Line           | Description                                                                                                  |

**Notes**:

[v4 brief repaired; was: '1.2 Security']

### JR-ML-API-037 — **API Surface**: 42+ REST methods + 2 WebSocket stream classes.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 221-228)

**Detail**:

- **Tests**: 208 passed, 84.48% coverage

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-CAN-PERF-003 — API timeout must be reduced for fast-interval callbacks.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 176-176)

**Detail**:

Issue 3.4.1: Default API timeout too long for frequently-polled endpoints.
Set shorter timeout (2-5s) for metrics/state endpoints, keep longer (10s) for
heavy operations like dataset upload.

### JR-DAT-API-006 — API versioning strategy defines version increment, backward-incompatibility, deprecation policy (2 minor versions notice, 6 months support).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 245-265)

**Notes**:

DATA-009 complete. Documented in docs/api/JUNIPER_DATA_API.md.

### JR-ML-API-038 — API-01: Health `status` Value Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5133-5148)

### JR-ML-API-039 — API-02: Health Response Schema Diverges.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5151-5165)

### JR-ML-API-040 — API-03: Canopy FSM Lacks Auto-Reset from FAILED/COMPLETED on START.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5168-5182)

### JR-ML-API-041 — API-04: FakeClient State Constants Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5185-5189)

### JR-ML-API-042 — API-05: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5192-5207)

### JR-ML-API-043 — API-06: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5210-5214)

### JR-ML-API-044 — API-07: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5217-5221)

### JR-ML-API-045 — API-08: `set_params` Includes Extraneous `type:command` Field.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5224-5232)

### JR-ML-API-046 — API-09: HTTPException Errors Bypass ResponseEnvelope.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5235-5249)

### JR-ML-API-047 — `app = create_app()` at module level — app created at import time, coupling to env state.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 187-198)

**Detail**:

| ID       | Severity   | File:Line                           | Description                                                                               |

**Notes**:

[v4 brief repaired; was: '3.4 Code Quality']

### JR-CAN-DATA-003 — Architecture adapter must handle dataset-triggered shape changes: equal-dim (no-op), grow-only (append nodes), shrink (prepend adapter layer)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 122-126)

**Detail**:

Method: adapt_for_dataset_swap(network, before_dims, after_dims) → ArchChanges. Three cases: (1) equal I/O dims—no work, (2) grow only—append nodes to outermost input/output layer, (3) shrink—prepend new dataset-side adapter layer.

**Notes**:

[v2 ARCH→DATA re-bucket] Returns ArchChanges struct for training history persistence.

### JR-ML-WS-140 — **Architecture**: WebSocket-based async worker (default) + legacy multiprocessing mode (deprecated).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 280-287)

**Detail**:

- **Tests**: 101 passed, 80.13% coverage (barely meets threshold)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-ML-ARCH-215 — Async route audit follow-up: ensure all storage/network I/O wrapped in asyncio.to_thread().

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_FOLLOWUP-ASYNC-ROUTE-AUDIT.md` (lines 1-50)

### JR-CAN-TEST-025 — Async/sync boundary (ThreadPoolExecutor fit_async, start_training_background) must have dedicated test coverage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 157-168)

**Detail**:

No tests for concurrent start requests, executor shutdown during training, exception propagation across boundary.
Estimated scope: 1-2 test files, 200-300 lines.

**Notes**:

CAN-HIGH-003; HIGH priority post-release item.

### JR-ML-OPS-005 — Audit and update Juniper SOPS (Standard Operating Procedures) documentation.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SOPS_AUDIT_2026-03-02.md` (lines 1-100)

### JR-ML-SEC-132 — `AuditLogger` and `WorkerMetrics` counters lack thread-safety.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 523-541)

### JR-ML-ARCH-216 — Background CascorControlStream supervisor task in canopy adapter.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 447-473)

### JR-CAN-OPS-002 — Background coverage runs exceed 300s timeout, requiring CI harness tuning.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 35-35)

**Detail**:

Operational issue, not a code defect. Suggest increasing test harness timeout or optimizing coverage runner.

**Notes**:

Operational tuning only.

### JR-ML-OBS-076 — Background.** The post-METRICS-MON state report (juniper-ml#223 §15) found that `juniper_data_datasets_cached` Gauge is defined in….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 307-334)

**Detail**:

**Severity:** P2 · **Owner repo:** juniper-data · **Status:** in-flight (sister PR opened 2026-05-06)

**Notes**:

[v3 brief repaired from cited content; was: '3.11 DATA-CACHED-WIRE — `juniper_data_datasets_cached` Gauge']

### JR-ML-DEP-020 — Background.** The R5.1 SLO catalog (juniper-deploy `notes/SLO_CATALOG_2026-05-03.md`) deliberately picked conservative initial targets….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 62-97)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

**Notes**:

[v3 brief repaired from cited content; was: '3.1 CALIB-01 — T+30d SLO target calibration']

### JR-CAS-TEST-012 — Backward compatibility testing with old serialized snapshots.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

### JR-CWK-TEST-002 — Bandit B105 pre-commit false positives in test files: suppress B105 (hardcoded_password_string) in test Bandit hook, targeting known-safe test fixture credential values.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 99-106)

**Detail**:

Root cause: auth_token field matches Bandit regex (RE_WORDS includes "token") introduced in WebSocket Phase 2 refactoring after pre-commit config finalized. Original api_key didn't trigger B105 ("key" not in word list). 11 B105 false positives across 3 test files (test_cli.py:4, test_config.py:6, test_worker_agent.py:1) — all test fixtures using dummy credentials. Solution: Add B105 to --skip in .pre-commit-config.yaml test Bandit hook (line 195), maintaining numerical order (--skip=B101,B104,B105,B108,B110,B311). Source Bandit hook unaffected; detect-private-key hook catches real secrets.

### JR-ML-OBS-077 — Based on the existing Docker Compose architecture, a k8s deployment would need:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 364-385)

**Detail**:

## 6. Client & Worker Analysis

**Notes**:

[v3 brief repaired from cited content; was: '5.2 Requirements for K8s Support']

### JR-ML-SEC-133 — Both are pure client libraries. They provide:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 385-396)

**Detail**:

**No startup/shutdown/orchestration changes needed.** These libraries are consumers, not producers.

**Notes**:

[v3 brief repaired from cited content; was: '6.1 juniper-data-client / juniper-cascor-client']

### JR-CAN-ARCH-004 — Bypass state sync normalization fragility: CascorStateSync uses raw client, bypassing adapter layer (ISS-13).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 571-585)

**Detail**:

ISS-13 MODERATE. ServiceBackend.initialize() (service_backend.py:189) creates CascorStateSync with raw JuniperCascorClient instance (self._adapter._client), bypassing entire normalization layer. Means: metrics_history stored without _normalize_metric() (ISS-05); training params stored with raw cascor names without _CASCOR_TO_CANOPY_PARAM_MAP (ISS-12); training status partially normalized but with uppercase gap (ISS-06 on sync path). Structural cause underlying ISS-05, ISS-06, ISS-12. Sync module should either go through adapter or replicate normalization logic.

**Notes**:

Identified by v7. This is the architectural fragility enabling cascading issues.

### JR-ML-UI-031 — CAN-000: Periodic Updates Pause When Apply Parameters Active.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1990-1994)

### JR-ML-UI-032 — CAN-003: Retain Candidate Pool Data Per Node Addition.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2000-2004)

### JR-ML-UI-033 — CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1912-1926)

### JR-ML-UI-034 — CAN-CRIT-002: Save/Load Snapshot in Adapter — Blocked on `/v1/snapshots/*` API.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1929-1943)

### JR-ML-UI-035 — CAN-DEF-008: Advanced 3D Node Interactions.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1980-1983)

### JR-ML-UI-036 — CAN-HIGH-005: Remote Worker Status Dashboard.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1946-1960)

### JR-CAN-TRAIN-004 — Candidate pool handling on dataset swap: Option C selected—abandon all candidates and force output-training-first mode on new dataset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 128-131)

**Detail**:

After architecture adaptation, drop candidate pool. Submit new training future with mode='output_training_first' forcing immediate output training on new dataset before any new candidate-pool training.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Alternative options (keep candidates, retrain on new data) considered and rejected.

### JR-ML-TRAIN-060 — Candidate Quality Decay: address candidate quality degradation in long training runs.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-02-CANDIDATE-QUALITY-DECAY.md` (lines 1-40)

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

### JR-ML-UI-037 — Canopy dashboard must display WebSocket connection status badge (connected green, reconnecting yellow, offline red).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 350-400)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1108-1120)

**Detail**:

New src/frontend/components/connection_indicator.py: html.Div(id='ws-connection-indicator').
Clientside callback reads ws-connection-status.data → toggles class connected-green / reconnecting-yellow / offline-red / demo-gray.
CSS rules in assets/styles.css.

**Notes**:

GAP-WS-26 (P2). Also mirrors demo mode parity (RISK-08, GAP-WS-33). Phase B (Day 9).

### JR-ML-DATA-012 — Canopy metrics normalization must maintain dual-format backward compatibility (nested + flat metric keys)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1371-1382)

**Detail**:

Phase H: test test_normalize_metric_produces_dual_format before any audit PR.
test_normalize_metric_nested_topology_present, test_normalize_metric_preserves_legacy_timestamp_field.
Write consumer audit doc listing every consumer of nested vs flat keys across canopy frontend.
Explicit recommendation: do NOT remove either format without landing this test first.

**Notes**:

RISK-01. Phase H (Day 12) regression gate. Must not ship Phase B without test in place.

### JR-ML-UI-038 — Canopy must configure Dash assets_url_path with content-hash query string to bust browser cache on new JS.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 550-600)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1364-1370)

**Detail**:

Configure assets_url_path with query-string content hash so browsers pick up new JS without hard refresh.
Verify: load dashboard; view source; assets/websocket_client.js?v=<sha> visible.
Test: test_asset_url_includes_version_query_string (Playwright).
Should have shipped with Day 8 Phase B per R0-06 §3.6; if not, defer to Day 12.
Do NOT ship Phase B without Phase I in production—stale websocket_client.js will not understand seq.

**Notes**:

Phase I (Day 8 or 12). R0-01 step 30. Acceptance criterion: browsers have <5 day old code in production.

### JR-ML-OBS-078 — Canopy must observe set_params latency separately for WebSocket and REST transports.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 200-250)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1225-1230)

**Detail**:

Histogram canopy_set_params_latency_ms with labels transport="websocket"|"rest".
Buckets: {5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000} ms.
WebSocket: read _client_latency_ms from ack envelope.
REST: measure time.monotonic() delta.

**Notes**:

Per R0-04 §7. Cross-transport comparison informs Phase C feature flag decision (§5.6 ack-vs-effect).

### JR-CAN-UI-026 — Canopy must use explicit blur-on-Apply to force pending debounced values to commit.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 456-475)

**Detail**:

Clientside callback that blurs active element on Apply button click.
Removes entire class of apply-with-stale-value races where fast typists
submit before debounce commits value. ~10 lines of JS.

**Notes**:

Part of Issue

### JR-CAN-OBS-010 — Canopy must validate that JuniperData service is reachable during startup via HTTP health probe.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 122-139)

**Detail**:

Application validates JUNIPER_DATA_URL configuration but makes no actual HTTP request.
Failures only surface when user first attempts data operation.
Recommendation: Add GET to {JUNIPER_DATA_URL}/health during lifespan; non-blocking with degradation flag.

**Notes**:

CAN-HIGH-001 from post-release roadmap; marked as validated critical integration gap.

### JR-ML-OBS-079 — `CanopyDashboardAvailabilityFastBurn` (page) / `CanopyDashboardAvailabilitySlowBurn` (ticket).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 276-286)

**Detail**:

| 3.1 | Canopy dashboard availability | `99.5%` | 30d rolling | `CanopyDashboardAvailabilityFastBurn` (page) / `CanopyDashboardAvailabilitySlowBurn` (ticket) | Computable; log-only-effective dur

**Notes**:

[v4 brief repaired; was: '5.1 User-facing primary SLIs (release-blocking, 5)']

### JR-ML-ARCH-217 — Capture open issues post-V38 release: training stalls, convergence, network growth constraints.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-03_JUNIPER-CASCOR_POST-V38-OPEN-ISSUES-PLAN.md` (lines 1-50)

### JR-ML-ARCH-218 — CAS-006: Auto-Snap Best Network.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2446-2450)

### JR-CAS-API-013 — Cascor feature enhancements: CAS-001 through CAS-010 (separate epoch limits, max iterations, auto-snap, test optimization, hierarchy, population, vector DB).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 310-330)

**Detail**:

CAS-001: Extract spiral generator (✅ COMPLETE). CAS-002: Separate epoch limits for full network and candidates. CAS-003: Max train session iterations. CAS-004: Extract remote worker (✅ COMPLETE, juniper-cascor-worker). CAS-005: Extract common dependencies to modules. CAS-006: Auto-snap best network (accuracy ratchet). CAS-007: Optimize slow tests (≤5 min, 86-93% reduction via Phase 6). CAS-008: Network hierarchy management. CAS-009: Network population management. CAS-010: Snapshot vector DB storage. Status: CAS-001/004 COMPLETE, others NOT STARTED.

**Notes**:

[v2 remap: SE→API]

### JR-ML-DEP-021 — Cascor listens on container port 8200 but is mapped to host port 8201 in Docker. The client default `base_url` is `http://localhost:8200`….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 409-420)

**Detail**:

**Repositories**: juniper-cascor, juniper-deploy

**Notes**:

[v3 brief repaired from cited content; was: '3.4 Port Mapping Inconsistency']

### JR-CAS-API-014 — CasCor service API must support separate network_epochs and candidate_epochs parameters.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 562-566)

**Notes**:

Requires API contract extension; juniper-cascor-client start_training() method update.

### JR-ML-WS-143 — Cascor SetParamsRequest has extra=forbid; canopy adapter routes unclassified keys to REST.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 46-46)

**Notes**:

Settled position C-09 from R3-03 table; cross-round consensus consolidation

### JR-CAN-API-029 — Cascor swap_dataset_live endpoint pre-conditions: experimental gate enabled, training running, no swap in progress, dim change supported, shrink supported by phase set.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 93-101)

**Detail**:

Return 403 if gate disabled, 422 if not training/dim unsupported/shrink unsupported, 409 if swap already in progress.

**Notes**:

Failures between steps 4-14 trigger rollback; return 5xx with original error wrapped.

### JR-ML-SEC-134 — CasCor-Side Validation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 895-907)

**Detail**:

| `cascade_add` correlation hardcoded to 0.0 | Cosmetic — does not affect topology display |

### JR-ML-OBS-080 — `CascorControlStream.set_params()` with `command_id`.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 237-248)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 192-203)

**Detail**:

| A-SDK    | `CascorControlStream.set_params()` with `command_id` | ✅ Complete                                     |

**Notes**:

[v4 brief repaired; was: '8.1 Phases Now Complete']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-CAN-API-030 — CascorStateSync reads raw cascor responses and duplicates envelope-unwrapping logic instead of using adapter normalization methods, risking format drift.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 548-570)

**Detail**:

state_sync.py reads raw response without adapter; bypasses normalization methods. Should call adapter's _unwrap_envelope() and _first_defined() for standardization.

**Notes**:

State sync should accept adapter instead of raw client reference.

### JR-ML-OBS-081 — Categories: 5 RED panels (Request Rate, Error Rate, p95 Latency stats +.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 330-360)

**Detail**:

Categories: 5 RED panels (Request Rate, Error Rate, p95 Latency stats +

**Notes**:

[v3 brief repaired from cited content; was: '6.2 juniper-canopy.json (18 panels, version 3, title "Junipe']

### JR-ML-ARCH-219 — CC-01: `_recv_loop` Catches Bare `Exception`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3656-3670)

### JR-ML-DOC-002 — CC-04: `set_params()` Method Not Documented in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3673-3687)

**Notes**:

[v2 ARCH→DOC re-bucket]

### JR-ML-ARCH-220 — CC-05: CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3690-3698)

### JR-ML-ARCH-221 — CC-06: `command()` Never Sends `type` Field.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3701-3708)

### JR-ML-ARCH-222 — CC-07: NpzFile Resource Leak in data-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3711-3725)

### JR-ML-WS-144 — CC-08: WebSocket Auto-Reconnection Not Implemented.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3728-3742)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-223 — CC-13: `_recv_loop` Silently Drops Non-Correlated Server Messages.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3762-3776)

### JR-ML-ARCH-224 — CC-14: `_handle_response()` Calls `response.json()` Unconditionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3779-3793)

### JR-ML-SEC-135 — CC-15: No TLS/SSL Configuration Support on WS Streams.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3796-3810)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-ARCH-225 — CC-16: `FakeCascorClient.wait_for_ready()` Returns True Immediately.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3813-3827)

### JR-ML-ARCH-226 — CC-17: `FakeCascorClient.wait_for_ready()` Missing `self._lock`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3830-3844)

### JR-ML-ARCH-227 — CFG-01: `torch` Imported but Missing from canopy Dependencies.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4883-4897)

### JR-ML-ARCH-228 — CFG-02: `sentry-sdk` in Core Dependencies but Only Used Optionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4900-4914)

### JR-ML-ARCH-229 — CFG-03: `SENTRY_SDK_DSN` vs `JUNIPER_CASCOR_SENTRY_DSN` — Dual Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4917-4931)

### JR-ML-ARCH-230 — CFG-04: `JUNIPER_DATA_URL` Read via Raw `os.getenv`, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4934-4948)

### JR-ML-ARCH-231 — CFG-05: `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — Both Needed.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4951-4965)

### JR-ML-ARCH-232 — CFG-06: `CASCOR_*` Env Prefix Inconsistent with `JUNIPER_*` Convention.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4968-4982)

### JR-ML-ARCH-233 — CFG-07: Port 8200 vs 8201 Confusion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4985-4999)

### JR-ML-ARCH-234 — CFG-08: Rate Limiting Defaults Differ Across Services.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5002-5016)

### JR-ML-ARCH-235 — CFG-09: `audit_log_path` Defaults to `/var/log/` — Requires Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5019-5041)

### JR-ML-ARCH-236 — CFG-12: `setuptools>=82.0` vs `>=61.0` Elsewhere.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5044-5058)

### JR-ML-ARCH-237 — CFG-13: `python-dotenv` in canopy Core Deps but Never Imported.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5061-5075)

### JR-ML-TRAIN-061 — CFG-14: `juniper-cascor-client>=0.1.0` Allows Outdated Incompatible Versions.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5078-5092)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-238 — CFG-16: `CASCOR_DEMO_MODE` Read Directly, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5095-5109)

### JR-ML-SEC-136 — **CHANGELOG changes**: Add sections for v0.1.1, v0.3.0 covering:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 101-113)

**Detail**:

**CHANGELOG changes**: Add sections for v0.1.1, v0.3.0 covering:

**Notes**:

[v3 brief repaired from cited content; was: '1.5 juniper-cascor-worker: CHANGELOG & Tags']

### JR-ML-TEST-026 — Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 69-69)

**Notes**:

Settled position C-32 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-062 — CI-01: cascor-client CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4643-4657)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-063 — CI-02: cascor-worker CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4660-4664)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-239 — CI-03: juniper-deploy CI Runs ZERO Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4667-4681)

### JR-ML-SEC-137 — CI-04: Missing Weekly security-scan.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4684-4695)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-TRAIN-064 — CI-05: Missing lockfile-update.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4698-4709)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TEST-027 — CI-06: juniper-deploy No Coverage Configuration.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4712-4723)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-ARCH-240 — CI-07: Inconsistent GitHub Actions Versions Across Repos.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4726-4737)

### JR-ML-SEC-138 — CI-SEC-01: No Weekly Security Scan for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4838-4842)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-139 — CI-SEC-02: No Security Scanning in juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4845-4856)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-CAN-TEST-026 — CI/CD configuration disables 15+ MyPy type checking codes and excludes tests from flake8/mypy, hiding type errors.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 195-235)

**Detail**:

.pre-commit-config.yaml excludes tests from type checking. ci.yml uses || true on bandit, warnings-only on pip-audit. Must enable strict type checking for tests.

**Notes**:

Allows type errors to ship.

### JR-ML-SEC-140 — **Clean separation of concerns**: Each repository has a single, well-defined responsibility.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 455-464)

**Detail**:

1. **Clean separation of concerns**: Each repository has a single, well-defined responsibility

**Notes**:

[v4 brief repaired; was: '5.1 Strengths']

### JR-ML-TOOL-003 — CLN-CC-01: Delete Legacy `remote_client/` Directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1317-1343)

### JR-ML-TOOL-004 — CLN-CC-02: Delete Stale `check.py` Duplicate (600 Lines).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1346-1361)

### JR-ML-TOOL-005 — CLN-CC-03: Remove 9 Local `import traceback` in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1364-1378)

### JR-ML-TOOL-006 — CLN-CC-04: Enable mypy Strict Mode.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1381-1395)

### JR-ML-TOOL-007 — CLN-CC-05: Legacy Spiral Code — Trivial Getter/Setter Methods, No @deprecated.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1398-1412)

### JR-ML-TOOL-008 — CLN-CC-06: Remove "Roll" Concept in CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1415-1421)

### JR-ML-TOOL-009 — CLN-CC-07: Candidate Factory Refactor.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1424-1430)

### JR-ML-TOOL-010 — CLN-CC-08: Remove Commented-Out Code Blocks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1433-1439)

### JR-ML-TOOL-011 — CLN-CC-09: Line Length Reduction to 120 Characters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1442-1448)

### JR-ML-TOOL-012 — CLN-CC-10: `utils.py:238` — Broken `check_object_pickleability` Uses `dill` Not in Deps.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1451-1473)

### JR-ML-TOOL-013 — CLN-CC-11: `snapshot_serializer.py` — Extend Optimizer Support (In-Code TODO).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1476-1490)

### JR-ML-TOOL-014 — CLN-CC-12: `.ipynb_checkpoints` Directories Committed to Repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1493-1507)

### JR-ML-TOOL-015 — CLN-CC-13: `sys.path.append` at Module Level in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1510-1524)

### JR-ML-TOOL-016 — CLN-CC-14: Empty `# TODO :` Headers in 18+ Files.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1527-1541)

### JR-ML-TOOL-017 — CLN-CC-15: `_object_attributes_to_table` Return Type Annotation Wrong.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1544-1558)

### JR-ML-TOOL-018 — CLN-CN-01: `theme-table` CSS Class Never Implemented.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1563-1588)

### JR-ML-TOOL-019 — CLN-CN-02: NPZ Validation Only in DemoMode, Not ServiceBackend.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1591-1605)

### JR-ML-TOOL-020 — CLN-CN-03: Performance Test Suite Minimal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1608-1622)

### JR-ML-TOOL-021 — CLN-CN-04: JuniperData-Specific Error Handling Missing.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1625-1639)

### JR-ML-TOOL-022 — CLN-CN-05: DashboardManager Extraction (3,232 → Component Classes).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1642-1657)

### JR-ML-TOOL-023 — CLN-CN-06: Re-enable Remaining MyPy Disabled Codes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1660-1674)

### JR-ML-TOOL-024 — CLN-CN-07: Real Backend Path Test Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1677-1691)

### JR-ML-TOOL-025 — CLN-CN-08: Convert Skipped Integration Tests (4 Files with `requires_server`).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1694-1708)

### JR-ML-TOOL-026 — CLN-CN-09: main.py Coverage Gap (84% vs 95% Target).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1711-1725)

### JR-ML-TOOL-027 — CLN-CN-10: `main.py` Is 2,543 Lines — Second God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1728-1742)

### JR-ML-TOOL-028 — CLN-CN-11: `metrics_panel.py` Is 1,790 Lines — Third God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1745-1759)

### JR-ML-TOOL-029 — CLN-CN-12: `network_visualizer.py:1512` — Active TODO Indicating Logging Error Bug.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1762-1776)

### JR-ML-TOOL-030 — CLN-CN-13: Deprecated `_generate_spiral_dataset_local()` Still Called.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1779-1793)

### JR-ML-TOOL-031 — CLN-CN-14: `np.random.seed(42)` Sets Global Numpy Seed.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1796-1810)

### JR-ML-TOOL-032 — CLN-JD-01: `python-dotenv` Hard Dependency for Optional ARC-AGI Feature.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1815-1829)

### JR-ML-TOOL-033 — CLN-JD-02: `FakeDataClient.close()` Destroys Data.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1832-1846)

### JR-ML-TOOL-034 — CLN-JD-03: Module-Level `create_app()` at `app.py:142` — Import-Time Side Effects.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1849-1863)

### JR-DEP-SEC-005 — Close secret-leak detection bypass via Gitleaks path-based allowlisting.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 29-91)

**Detail**:

Gitleaks .gitleaks.toml blanket-allows files matching *.env.enc and *.env.secrets.enc,
creating bypass path for plaintext secrets. Root causes: (1) path-based allowlisting exempts
matching files from all rules, (2) pre-commit hook skipped in CI, (3) weak SOPS metadata validation
(only grep "^sops_" check). Remediation: replace path allowlist with content-based ciphertext regex,
remove CI skip, strengthen to multi-field SOPS validation + ciphertext line check.

### JR-ML-TRAIN-065 — `cn-training-convergence-threshold-input`.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 56-71)

**Detail**:

| 2   | Correlation Threshold     | `cn-correlation-threshold-input`          | number (float) | 0.001               | NEW         |

**Notes**:

[v4 brief repaired; was: '2.2 Candidate Nodes Subsection (10 inputs)']

### JR-ML-SEC-141 — **Code complexity in Canopy**.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 560-575)

**Detail**:

| Criterion                     | Option 1: Feature Flag | Option 2: Mock Containers | Option 3: Client Fakes | Option 4: VCR         | Option 5: Demo Profile    |

**Notes**:

[v4 brief repaired; was: '3.4 Comparative Evaluation']

### JR-CAS-TOOL-007 — Code quality & compliance improvements: coverage thresholds, strict MyPy, pre-commit hooks, lint compliance tests.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 118-130)

**Detail**:

Pre-commit compliance: All 20 hooks pass, 9 violations fixed (F401×2, F402, C401, B007, B404, B105/B110/B107). Lint compliance tests: 162 parametrized tests (test_lint_compliance.py for future detection). Coverage threshold: fail_under = 80 in pyproject.toml. CI pipeline green (pre-commit, unit tests 3.11/3.12/3.13, security, integration, build). CPU-only PyTorch in CI configured. No critical lint violations remaining.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAN-DOC-005 — Code quality, frontend, security, CI/CD audit domains: 8-domain audit with 15 gaps identified (11 NOT fixed, 4 partially, 1 documentation).

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_AUDIT_PLAN_2026-04-12.md` (lines 1-100)

**Detail**:

Comprehensive audit across 8 domains: Security, Concurrency, CI/CD, App Logic, Backend Services, Code Quality/Frontend, Observability/Logging, Test Quality. Registry of CRIT-001 through LOW-022 issues mapping to severity (Critical, High, Medium, Low), category, file, phase, claimed status. Most issues have proposed fixes ranging from straightforward (add lock, fix hardcoded value) to complex (restructure component, redesign exception handling).

### JR-ML-SEC-142 — Code Reference Validation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 880-886)

**Detail**:

Every line number, code snippet, and factual claim about the codebase was verified against the current source files. No shifted, wrong, or missing references found.

### JR-ML-OBS-082 — Complete baseline metrics and observability inventory analysis.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_ANALYSIS_2026-04-25.md` (lines 1-100)

**Notes**:

BASELINE phase of METRICS-MON program.

### JR-CAS-WS-005 — Complete documentation for spiral data generator extraction, PyPI client packages, microservices implementation, and polyrepo architecture.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/JUNIPER_CASCOR_SPIRAL_DATA_GEN_REFACTOR_PLAN.md` (lines 1-100)

**Detail**:

Comprehensive extraction plan synthesizing 3 proposals, phases 0-4 complete (76 tests passing), phase 5 deferred. Core principles: pure NumPy generator, artifact-first API (NPZ), minimal provider set, deterministic reproducibility. Methods to extract: coordinate generation, feature/label construction, ordering/partitioning. Dependency decoupling: remove torch, matplotlib, logging, multiprocessing. Constants extraction: spiral geometry (num_spirals, points_per_spiral, rotations), noise parameters. NPZ data contract specification (dataset_id hash-based, structure validation). Documentation complete with test coverage and phase-by-phase delivery schedule.

### JR-CAN-API-031 — Configure JuniperData client integration with JUNIPER_DATA_URL and docker-compose entry.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 209-232)

**Detail**:

JUNIPER_DATA_URL not in app_config.yaml; no docker-compose entry; no E2E test with live JuniperData service.

**Notes**:

Phase 2 high priority; client exists in Phase 4 deliverable but is not actively integrated

### JR-DEP-TOOL-002 — Consolidate demo dataset parameters and shell script timeouts into config.sh.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 93-117)

**Detail**:

Shell scripts have 8 hardcoded timeouts (90s service wait, 3s poll, 3s curl, 5s health,
120s demo test, 3s demo poll, 5s training start, 90s enhanced test). Demo has 7 hardcoded
parameters (n_spirals=2, n_points=200, noise=0.15, seed=42, learning_rate=0.01, 500 epochs).
Source all from scripts/config.sh. Lower priority (LOW) per analysis.

### JR-CAN-TEST-027 — Consolidate duplicate conftest.py fixtures into single configuration file.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 122-128)

**Detail**:

Two conftest.py files (445 + 224 lines) contain overlapping fixtures. Consolidate to avoid duplication and maintenance burden.

**Notes**:

Category D: Duplicate fixtures; DRY principle violation

### JR-ML-TEST-028 — Consolidated regression remediation plan.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-03_JUNIPER-ECOSYSTEM_CONSOLIDATED-REMEDIATION-PLAN.md` (lines 1-50)

### JR-ML-TEST-029 — Contract-test pytest marker contract runs on every PR, NOT nightly.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 71-71)

**Notes**:

Settled position C-34 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-039 — Contrast with service adapter (`cascor_service_adapter.py` lines 617-621):.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 361-385)

**Detail**:

**File**: `juniper-canopy/src/backend/demo_backend.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-OBS-083 — Convergence Detection checkbox (default: enabled).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 19-31)

**Detail**:

The Training Parameters card (`dashboard_manager.py` lines 417-512) contains a flat list of 6 inputs:

**Notes**:

[v3 brief repaired from cited content; was: 'Current State']

### JR-ML-TRAIN-066 — Convergence Timing: optimize convergence detection timing.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-04-CONVERGENCE-TIMING.md` (lines 1-46)

### JR-ML-WS-145 — Correlation field is command_id, NOT request_id.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 38-38)

**Notes**:

Settled position C-01 from R3-03 table; cross-round consensus consolidation

### JR-ML-TEST-030 — COV-01: Deploy Tests Exist but Zero Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4740-4744)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TEST-031 — COV-02: Canopy No Per-Module Coverage Gate.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4747-4758)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TEST-032 — COV-04: Coverage Gate Mismatch — CI Comment 95% vs Actual 80%.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4761-4772)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-DAT-OBS-004 — Coverage reporting must upload to external service (Codecov, Coveralls) for trend tracking.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 68-69)

**Notes**:

INF-002 MEDIUM (P2).

### JR-CAS-OBS-003 — Create baseline py-spy profiles for key operations to enable performance regression detection.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 850-854)

### JR-DCL-ARCH-001 — Create juniper_data_client/constants.py module to centralize ~60 hardcoded values across codebase.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 130-145)

**Detail**:

Codebase contains ~89 hardcoded values across 6 files with no centralized constants module.
Only 3 values are defined as class-level constants on JuniperDataClient (DEFAULT_TIMEOUT, DEFAULT_RETRIES,
DEFAULT_BACKOFF_FACTOR); remaining values (16 API endpoints, connection pool sizes, HTTP status codes,
generator defaults) are inline literals. Create single constants.py organized into 7 sections:
(1) HTTP Configuration, (2) API Endpoints, (3) Timeouts & Polling, (4) Authentication,
(5) Generator Defaults, (6) Generator Mathematics, (7) Data Types.

**Design**:

Recommended structure: single juniper_data_client/constants.py (~60 constants).
Maintain backward compatibility by keeping class-level constants as aliases referencing module constants.
Validate all generator outputs match current behavior with integration tests.
Keep mathematical constants clearly separated from configuration constants.

### JR-DEP-DEP-004 — Create systemd health timer and one-shot units for periodic service health checks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 185-220)

**Detail**:

Six new units (3 timers + 3 one-shots) for juniper-data, juniper-cascor, juniper-canopy.
Timers fire every 30 seconds (OnActiveSec=30, OnUnitActiveSec=30, AccuracySec=5s).
One-shot units run health_check_systemd.sh, query /v1/health/ready endpoint, parse JSON,
output structured results to journal. Non-zero exit enables OnFailure= triggers.

### JR-ML-OBS-084 — Cross-link: panels bind catalog §3.5 (`dataset_post_total`) and §4.7.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 400-424)

**Detail**:

Cross-link: panels bind catalog §3.5 (`dataset_post_total`) and §4.7.

**Notes**:

[v3 brief repaired from cited content; was: '6.4 juniper-data.json (17 panels, version 3, title "JuniperD']

### JR-ML-SEC-143 — Cross-references. Runbook §5.3, §7 · OBS-ROUTE-01 PR juniper-deploy#60 (validation evidence in PR body).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 182-207)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

**Notes**:

[v3 brief repaired from cited content; was: '3.5 AMTOOL-CI — `amtool check-config` snap-confinement gap']

### JR-ML-ARCH-241 — CW-01: `receive_json()` Doesn't Catch JSONDecodeError.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3906-3920)

### JR-ML-PERF-011 — CW-02: `requirements.lock` Includes CUDA Packages (~2-4GB Bloat).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3923-3937)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-ARCH-242 — CW-03: No Integration Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3940-3954)

### JR-ML-ARCH-243 — CW-04: Timeout Error Sends `candidate_uuid: ""` Instead of Actual UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3957-3971)

### JR-ML-ARCH-244 — CW-05: Dynamic Import `from candidate_unit.candidate_unit import CandidateUnit`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3974-3996)

### JR-ML-ARCH-245 — CW-06: `receive_json()` in Registration Path — No JSONDecodeError Catch.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3999-4006)

### JR-ML-ARCH-246 — CW-07: No Validation of `tensor_manifest` Keys Against Received Binary Frames.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4009-4023)

### JR-ML-PERF-012 — CW-08: Top-Level `import torch` — First-Task Latency.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4026-4040)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-CAN-PERF-004 — Dashboard HTTP polling ignores WebSocket relay; switch to WS for real-time metrics updates.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 293-310)

**Detail**:

ISS-03 LOW. Dashboard has WebSocket relay (cascor_service_adapter.py relay loop) but does NOT consume WebSocket messages. Relies entirely on HTTP polling via dcc.Interval: fast-update-interval 1000ms, slow-update-interval 5000ms. websocket-data div defined at dashboard_manager.py:876 but zero Input("websocket-data",...) Dash callback bindings exist. Performance/UX issue, not functional blocker (ISS-01 format mismatch applies to WebSocket data anyway, and ISS-11 unnormalized field names would become active bug if this fixed).

### JR-CAN-OBS-011 — Dashboard must not hardcode localhost:8050 URLs; MetricsPanel has 6+ instances preventing non-local deployment.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 1-50)

**Detail**:

Lines 1050, 1075, 1085, 1095, 1105, 1110 in MetricsPanel reference hardcoded localhost:8050. Must use environment variable or configuration endpoint for cascor service URL.

**Notes**:

Blocks Docker/cloud deployment.

### JR-CAN-OBS-012 — Dashboard state management must track cascor service backend availability and display connection status/errors to user.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 1-50)

**Detail**:

Currently no feedback when cascor service is unavailable; UI hangs or renders empty. Add connection-state callback and error toast on service failure.

**Notes**:

Improves debugging and user experience.

### JR-CAN-UI-027 — DashboardManager must be refactored for extract to <2000 lines.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 177-177)

**Detail**:

Issue 3.4.2: DashboardManager is monolithic. Begin extraction of sidebar,
controls, stores, and theme logic into separate modules. Post-refactor target: <2000 lines.

**Notes**:

[v2 ARCH→UI re-bucket]

### JR-CAN-UI-028 — Dataset scatter plot always empty in service mode; CasCor endpoint returns metadata only (ISS-09).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 496-512)

**Detail**:

ISS-09 MODERATE. ServiceBackend.get_dataset() (service_backend.py:155-168) returns metadata only (sample counts, feature counts); DatasetPlotter._create_scatter_plot() (dataset_plotter.py:304-305) expects raw data arrays (inputs, targets). CasCor /v1/dataset returns metadata only, not raw training data. Result: dataset tab shows metadata but no scatter plot. Documented as known limitation in Phase 1 but not re-surfaced in Phase 2 analysis.

**Design**:

Requires CasCor API extension (new endpoint returning data arrays) or direct integration with juniper-data to fetch raw training data. Architectural enhancement, not simple normalization fix.

**Notes**:

Identified by v4. Known Phase 1 limitation; architectural enhancement scope.

### JR-ML-SEC-144 — `dataset_id` concatenated into filesystem paths without sanitization. Path traversal via `../../` in user-supplied `dataset_id`. Documented.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 169-178)

**Detail**:

| ID        | Severity   | File:Line                   | Description

**Notes**:

[v4 brief repaired; was: '3.2 Security']

### JR-ML-ARCH-247 — DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles".

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3849-3853)

### JR-ML-ARCH-248 — DC-02: GENERATOR_MOON = "moon" — No Server Generator.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3856-3860)

### JR-ML-ARCH-249 — DC-03: Missing Constants for 5 Server Generators.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3863-3867)

### JR-ML-DATA-013 — DC-04: `FakeDataClient` Masks Generator Name Bugs

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3870-3884)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-DATA-014 — DC-05: `FakeDataClient` Missing Lifecycle Methods

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3887-3901)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-UI-040 — Debounce lives in Dash clientside callback, NOT SDK.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 66-66)

**Notes**:

Settled position C-29 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-145 — Decision boundary computation runs synchronously in async handler, blocking event loop.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 913-931)

### JR-ML-DEP-022 — **Decision**: Bind to `127.0.0.1:8200` (settings default).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 20-26)

**Detail**:

**Decision**: Bind to `127.0.0.1:8200` (settings default).

**Notes**:

[v3 brief repaired from cited content; was: '2.1 juniper-cascor bind address']

### JR-ML-UI-041 — **Decision**: Rename canopy's `juniper-ctl` to `juniper-canopy-ctl` for consistency.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 38-46)

**Detail**:

**Decision**: Rename canopy's `juniper-ctl` to `juniper-canopy-ctl` for consistency.

**Notes**:

[v3 brief repaired from cited content; was: '2.4 CLI naming convention']

### JR-ML-WS-146 — **Decision**: Support both `--systemd` flag and `USE_SYSTEMD=1` env var.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 32-38)

**Detail**:

**Decision**: Support both `--systemd` flag and `USE_SYSTEMD=1` env var.

**Notes**:

[v3 brief repaired from cited content; was: '2.3 Plant/chop systemd mode activation']

### JR-ML-UI-042 — **Decision**: Use `Wants=` (not `Requires=`).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 26-32)

**Detail**:

**Decision**: Use `Wants=` (not `Requires=`).

**Notes**:

[v3 brief repaired from cited content; was: '2.2 juniper-all.target: Wants= vs Requires=']

### JR-ML-TRAIN-067 — DEFAULT_CANDIDATE_CORRELATION_THRESHOLD: Final[float] = 0.001.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 149-197)

**Detail**:

DEFAULT_CANDIDATE_CORRELATION_THRESHOLD: Final[float] = 0.001

**Notes**:

[v3 brief repaired from cited content; was: '3.3 New Candidate Nodes Constants']

### JR-ML-DATA-015 — DEFAULT_MAX_ITERATIONS: Final[int] = 1000

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 114-149)

**Detail**:

MAX_MAX_ITERATIONS: Final[int] = 100000

**Notes**:

[v3 brief repaired from cited content; was: '3.2 New Neural Network Constants']

### JR-ML-TRAIN-068 — DEFAULT_TRAINING_EPOCHS: Final[int] = 1000000    # was 300.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 99-114)

**Detail**:

DEFAULT_TRAINING_EPOCHS: Final[int] = 1000000    # was 300

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Modified Existing Constants']

### JR-CAS-OBS-004 — Define performance targets for latency and throughput.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

Benchmark harness needed to measure actual performance against targets.

### JR-CAN-TRAIN-005 — Demo cascor training loss plateaus at ~0.24 after first hidden unit despite 6+ units added; root causes include vanilla SGD vs Adam and mini-batch issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 120-185)

**Detail**:

RC-9: Vanilla SGD vs Adam. RC-10: Mini-batch between cascades undoes full-batch retrain. RC-11: Un-normalized covariance vs Pearson. RC-12: Spiral complexity. Recommended fix: Adam + autograd (Option 4B).

**Notes**:

Remediation code examples provided in source document.

### JR-ML-UI-043 — Demo mode must maintain parity with live WebSocket mode (connection status, metrics updates).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 450-500)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1116-1130)

**Detail**:

In src/backend/demo_mode.py, set window.cascorWS status to {connected: true, mode: "demo"} via set_props or peek path.
Dashboard ws-connection-status reflects "demo".
Connection indicator badge shows gray "demo" state.

**Notes**:

RISK-08, GAP-WS-33. Phase B (Day 9). Demo users see same UI feedback as live users.

### JR-CAN-TRAIN-006 — Demo training performs exactly one output gradient step per epoch while reference CasCor requires convergence training (1000+ steps) as self-contained phase before cascade decisions.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md` (lines 15-67)

**Detail**:

Demo calls train_output_step() once per epoch (1 gradient step), checks convergence after 10 epochs. Reference trains output layer for _PROJECT_MODEL_OUTPUT_EPOCHS=1000 steps as phase before cascade. New hidden units get random weights requiring O(100) steps to reach optimal; with 1 step/epoch, convergence check fires prematurely. After first hidden: loss stalls, cascading failure ensues.

**Design**:

Fix: demo must implement phase-based training—output-layer convergence phase (1000 steps) before cascade decisions.

**Notes**:

Mismatch 1 of 5 identified in training stall analysis.

### JR-CAN-TRAIN-007 — Demo warm-starts output layer on cascade (copy old weights, small-random new column) while reference re-initializes all output weights and retrains 1000 epochs from scratch.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md` (lines 70-100)

**Detail**:

Demo preserves old output weights, only new column gets small-random init. Reference: random re-init all weights, retrain 1000 epochs. Warm-start strategy violates CasCor spec; interaction weights between new unit and old units require full convergence on new architecture.

**Notes**:

Mismatch 2 of 5 identified.

### JR-ML-TRAIN-069 — `demo_backend.py:get_network_topology()` only creates input-to-hidden connections. It does not create hidden-to-hidden cascade connections….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 357-361)

**Detail**:

`demo_backend.py:get_network_topology()` only creates input-to-hidden connections. It does not create hidden-to-hidden cascade connections that are the defining featur

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-UI-044 — Dependency Graph (Runtime).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 76-85)

### JR-ML-SEC-146 — DEPLOY-01: Docker Secret Name/Path Mismatch.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3335-3349)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-OBS-085 — DEPLOY-02: AlertManager Service Missing from docker-compose.yml.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3352-3366)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-250 — DEPLOY-04: K8s Canopy Missing Service URL Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3386-3397)

### JR-ML-DEP-023 — **Deployment choice**: User units (`~/.config/systemd/user/`) vs system units (`/etc/systemd/system/`).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 451-651)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 2:']

### JR-ML-DEP-024 — Deprecate JuniperCanopy's non-standard `/health` and `/api/health` routes.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 3783-3983)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 8:']

### JR-ML-API-048 — Deprecated `get_arc_agi_api()` has no `warnings.warn()` call.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 150-156)

**Detail**:

- `traces_sample_rate=1.0` sends all Sentry traces

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-UI-045 — Design and implement integrated dashboard combining Canopy and CasCor metrics.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/INTEGRATED_DASHBOARD_PLAN.md` (lines 1-100)

### JR-ML-OBS-086 — Design and implement worker heartbeat protocol for CasCor distributed training.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md` (lines 1-50)

### JR-CAS-TOOL-008 — Design decisions record: 10 items tracking ActivationWithDerivative location, CandidateUnit factory, or fallback pattern, client packages, async wrapper, large file refactoring, legacy code removal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 325-342)

**Detail**:

Decision 1 (✅ IMPLEMENTED): ActivationWithDerivative → src/utils/activation.py. Decision 2 (✅ IMPLEMENTED): CandidateUnit constructor fix (factory + remove kwargs). Decision 3 (DECIDED): or fallback → if x is not None. Decision 4 (✅ IMPLEMENTED): Client packages (PyPI). Decision 5 (✅ IMPLEMENTED): Async wrapper (ThreadPoolExecutor). Decision 6 (DECIDED, not started): Large file refactoring (mixin-based). Decision 7 (DECIDED, gated): Legacy code removal (after E2E gate). Decision 8 (DECIDED): Optimizer serialization removal. Decision 9 (🔵 DEFERRED): Multiprocessing state (partial restore). Decision 10 (✅ IMPLEMENTED): SharedMemory (Named with lightweight tasks).

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-DEP-025 — Docker Compose V2 is required because the Phase 1 Compose file uses `depends_on: condition: service_healthy`, which is V2-only syntax.….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 198-398)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 1:']

### JR-DEP-DEP-005 — Docker Python 3.14 migration plan for juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/history/DOCKER_PYTHON_314_MIGRATION_PLAN.md` (lines 1-50)

### JR-ML-OBS-087 — Document all metrics: Prometheus exposition format, cardinality limits, label guidelines.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-08_JUNIPER-ECOSYSTEM_METRICS-DOCUMENTATION.md` (lines 1-50)

### JR-DCL-DOC-007 — Document JuniperDataClient exception hierarchy with HTTP status code mapping in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 112-116)

**Detail**:

Exception hierarchy is mentioned only in Key Files, not fully documented. Must show full exception tree
(JuniperDataClientError parent with 5 specific exceptions) and HTTP status code -> exception type mapping.
Essential context for agents working on error handling and debugging.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.3) and AGENTS_MD_UPDATE_PLAN (Step 3.3).

### JR-ML-DOC-003 — Documentation audit: standardize link formats, enforce cross-repo resolution, validate all links in CI.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/DOCUMENTATION_AUDIT_AND_UPGRADE_PLAN.md` (lines 1-50)

### JR-ML-SEC-147 — Dual auth mechanisms — WebSocket endpoints lack middleware-level enforcement and rate limiting.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 294-330)

### JR-ML-DATA-016 — Duplicate pytest configuration in `pyproject.toml` and `pytest.ini`

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 390-397)

**Detail**:

- Duplicate pytest configuration in `pyproject.toml` and `pytest.ini`

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-OBS-088 — Duplicate `_success_envelope` definition (dead code).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 255-265)

**Detail**:

- `response.json()` not protected against non-JSON 200 responses

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-TRAIN-070 — During `CascorStateSync.sync()`, the topology is fetched and transformed correctly into `SyncedState.topology`. However, in `main.py` where….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 475-479)

**Detail**:

During `CascorStateSync.sync()`, the topology is fetched and transformed correctly into `SyncedState.topology`. However, in `main.py` where the synced state is applied, only training status/epoch/params are pushed to the app state — the synced topology is never written to the Das

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-API-049 — Dynamic import `from candidate_unit.candidate_unit import CandidateUnit` — fragile, no version check.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 314-327)

**Detail**:

| CW-01 | **Medium** | `worker.py`        | 225     | Timeout error sends `candidate_uuid: ""` instead of actual UUID from `candidate_data`                |

**Notes**:

[v4 brief repaired; was: '2.4 juniper-cascor-worker']

### JR-ML-UI-046 — Each radio group controls `disabled` state of associated inputs:.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 257-267)

**Detail**:

- **NN Growth Trigger**: `"preset_epochs"` enables preset-epochs-input, disables convergence-threshold-input; `"convergence"` reverses

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Radio Button Enable/Disable Pattern']

### JR-ML-OBS-089 — Effort**: 3-4 days | **Repo**: juniper-canopy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 649-657)

**Detail**:

**Effort**: 3-4 days | **Repo**: juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '6.2 P5-RC-14 + P5-RC-05: WebSocket Consumption']

### JR-ML-API-050 — Effort**: 3-5 days | **Repos**: juniper-cascor, juniper-canopy.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 657-664)

**Detail**:

**Effort**: 3-5 days | **Repos**: juniper-cascor, juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '6.3 KL-1: Dataset Data in Service Mode']

### JR-ML-OBS-090 — emitted_at_monotonic: float on every /ws/training broadcast envelope.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 78-78)

**Notes**:

Settled position C-41 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-071 — Enable Canopy to connect to external CasCor instances with connection orchestration.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_EXTERNAL_CASCOR_PLAN.md` (lines 1-100)

**Notes**:

[v2 ARCH→TRAIN re-bucket] Approved for implementation.

### JR-ML-SEC-148 — End of deep audit report.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 468-487)

**Detail**:

| 21 | All 5 repos    | Bump AGENTS.md and file header versions to match `pyproject.toml` |

**Notes**:

[v3 brief repaired from cited content; was: '8.4 Low (Backlog)']

### JR-ML-API-051 — Error parsing silently loses `{"error": "string"}` format messages — falls through to `response.text`.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 298-314)

**Detail**:

| CL-01 | **Medium** | `ws_client.py`              | 231–240  | `command()` vs `set_params()` message format inconsistency — `command()` never sends `"type"` field   |

**Notes**:

[v4 brief repaired; was: '2.3 juniper-cascor-client']

### JR-ML-OPS-006 — Error-budget burn-rate rule operationally binding.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 79-79)

**Notes**:

Settled position C-42 from R3-03 table; cross-round consensus consolidation

### JR-ML-TOOL-035 — Establish 6-type prompt classification (Handoff, Task, Template, Planning, Audit, Infrastructure) with boilerplate analysis.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` (lines 326-466)

### JR-ML-OPS-007 — Establish PyPI publish procedure: OIDC trusted publishing, semantic versioning, automated changelog.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (lines 1-50)

### JR-ML-SEC-149 — Estimated Duration**: 8-12 days (original) — **ACTUAL: ~0.5 day (verification + demo gap fix).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 434-451)

**Detail**:

## 5. Phase 3: Metrics Granularity

**Notes**:

[v3 brief repaired from cited content; was: '4.5 Phase 2 Success Criteria']

### JR-ML-OBS-091 — Execute metrics and monitoring code review across Juniper services.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md` (lines 1-100)

**Notes**:

PROPOSED phase; awaiting kickoff.

### JR-ML-API-052 — Existing Infrastructure.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 85-97)

**Detail**:

- **Docker Compose**: Partial — `JuniperCanopy/conf/docker-compose.yaml` defines `juniper-data`, `juniper_canopy`, and `redis` services; `JuniperCascor/conf/docker-compose

### JR-ML-API-053 — Expand to accept all 22 parameter keys with `nn_` and `cn_` prefixes. Map `nn_learning_rate`, `nn_max_hidden_units`, `nn_max_total_epochs`….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 302-306)

**Detail**:

Expand to accept all 22 parameter keys with `nn_` and `cn_` prefixes. Map `nn_learning_rate`, `nn_max_hidden_units`, `nn_max_total_epochs` to `TrainingState.update_state()` for backward compatibility. Forward all params to `backend.apply_params()`.

**Notes**:

[v3 brief repaired from cited content; was: '5.1 `/api/set_params` Endpoint (`main.py`)']

### JR-ML-ARCH-251 — Expand/collapse indicator.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 71-84)

**Detail**:

| NN section collapse | `nn-subsection-collapse` | dbc.Collapse wrapper      |

**Notes**:

[v4 brief repaired; was: '2.3 Structural IDs']

### JR-DEP-TEST-002 — Extend compose validation to cover observability and production profiles.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 205-211)

**Detail**:

Phase 4. validate-compose job in ci.yml already validates full, demo, dev profiles.
Extend to validate observability and production profiles as added. Add JSON schema
validation for Grafana dashboard files (Phase 1 output).

### JR-ML-ARCH-252 — Extend to accept and store all new `nn_*` and `cn_*` keyword arguments. Unknown keys should be stored and accessible but not cause errors.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 310-314)

**Detail**:

Extend to accept and store all new `nn_*` and `cn_*` keyword arguments. Unknown keys should be stored and accessible but not cause errors.

**Notes**:

[v3 brief repaired from cited content; was: '5.3 `DemoMode.apply_params()` (`demo_mode.py`)']

### JR-CAN-OBS-013 — Extract create_empty_plot() as shared utility across metric panels.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 162-162)

**Detail**:

Issue 3.2.3: create_empty_plot logic duplicated in multiple components.
Extract to plot_utils.py or equivalent shared module.

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-OBS-092 — `extract_network_topology()` catches all exceptions with a bare `except Exception` and returns `None` with no logging. Any bug in….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 433-437)

**Detail**:

`extract_network_topology()` catches all exceptions with a bare `except Exception` and returns `None` with no logging. Any bug in `_transform_topology()` (e.g., unexpected data format from CasCor) is completely invisible.

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-DATA-017 — `FakeDataClient.close()` doesn't prevent subsequent operations

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 201-209)

**Detail**:

- `FakeDataClient.close()` doesn't prevent subsequent operations

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-ARCH-253 — Feature flag use_websocket_set_params (default False) for Phase C rollout control.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 403-432)

### JR-ML-OBS-093 — **File**: `juniper-canopy/src/backend/cascor_service_adapter.py`.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 437-457)

**Detail**:

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-UI-047 — **File**: `juniper-canopy/src/backend/state_sync.py` (lines 125-135) — correctly fetches and transforms topology.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 479-485)

**Detail**:

**File**: `juniper-canopy/src/backend/state_sync.py` (lines 125-135) — correctly fetches and transforms topology.

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-TRAIN-072 — **File**: `juniper-cascor-client/constants.py:31`.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 340-345)

**Detail**:

**File**: `juniper-cascor-client/constants.py:31`

**Notes**:

[v3 brief repaired from cited content; was: '6.2 Medium: 503 Not Retried (XREPO-02 — confirmed STILL PRES']

### JR-ML-DOC-004 — Fix 17 broken markdown links in DEVELOPER_CHEATSHEET.md - 12 self-referencing and 5 missing intra-repo files.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-07_JUNIPER-ECOSYSTEM_CROSS-REPO-LINK-RESOLUTION-PROPOSAL.md` (lines 207-244)

**Detail**:

Category B (12 links): self-referencing cross-repo links should be direct relative:
- ../juniper-ml/notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md → JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md
- ../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md → SOPS_IMPLEMENTATION_PLAN.md
- ../juniper-ml/notes/SOPS_AUDIT_2026-03-02.md → SOPS_AUDIT_2026-03-02.md
- ../juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md → SECRETS_MANAGEMENT_ANALYSIS.md
- ../juniper-ml/notes/pypi-publish-procedure.md → pypi-publish-procedure.md
- ../juniper-ml/AGENTS.md → ../AGENTS.md (5 instances)

Category C (5 links): missing files never created, should be removed or redirected:
- Line 491: plan_7.5_7.6_dependency_management.md (remove)
- Line 575: STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md (remove)
- Line 720: PYPI_PUBLISH_PROCEDURE.md → pypi-publish-procedure.md (rename fix)
- Line 720: PYPI_PUBLISH_PLAN_3_PACKAGES.md (remove)
- Line 755: WORKTREE_IMPLEMENTATION_PLAN.md (remove or redirect to JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md)

### JR-DAT-TEST-008 — Fix 21 SIM117 violations (nested with statements) by combining where Python 3.11+ allows.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 247-266)

**Notes**:

RD-008 LOW priority deferred. Currently in ruff ignore list in pyproject.toml.

### JR-CAS-ARCH-010 — Fix boolean parameter initialization using "or" fallback in spiral_problem.py.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 426-438)

**Detail**:

Line 671: `self.clockwise = clockwise or self.clockwise or _SPIRAL_PROBLEM_CLOCKWISE`
never becomes False. Line 695: `noise or 0.0` fallback incorrect when 0.0 is valid.
Use explicit None checks.

### JR-ML-TOOL-036 — Fix broken check_object_pickleability function in utils.py:238 which uses dill not in dependencies.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (lines 3580-3590)

**Detail**:

CLN-CC-10: utils.py:238 imports and uses `dill` library which is not in project dependencies.
Function is broken. Fix by either adding dill to deps or refactoring to use pickle only.

### JR-CAS-TEST-013 — Fix conftest.py fast-slow mode logic - inverted semantics for JUNIPER_FAST_SLOW env var.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 441-453)

**Detail**:

Line 83: `os.environ.get("JUNIPER_FAST_SLOW") == "0"` triggers fast-slow mode when
env var is "0", semantically opposite. test_spiral_problem.py:_is_fast_mode() checks == "1".
Align condition to use consistent semantics.

### JR-ML-API-054 — Fix Docker secret name: `juniper_data_api_key` → `juniper_data_api_keys` (or vice versa).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 442-452)

**Detail**:

| 6 | juniper-deploy | Add AlertManager service to docker-compose.yml                                           |

**Notes**:

[v4 brief repaired; was: '8.2 High (Fix Soon)']

### JR-CAS-DOC-003 — Fix import alias mistake: datetime import uses pd instead of dt.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 362-366)

**Detail**:

Line 38 of cascade_correlation.py: 'import datetime as pd' should be 'import datetime as dt'. pd is conventionally pandas; using for datetime misleads developers.

### JR-CAS-ARCH-011 — Fix misleading import alias "import datetime as pd" - confuses with pandas.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 366-378)

**Detail**:

Line 38: imports datetime as pd (universally associated with pandas). Alias never used.
Line 37 already has import datetime. Remove the confusing import.

### JR-CAS-PERF-003 — Fix _roll_sequence_number memory issue in CascadeCorrelationNetwork using same optimization as CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 456-468)

**Detail**:

Line 775: list comprehension stores all discarded values. Unlike CandidateUnit version
(fixed in CASCOR-P1-008), this version still has OOM risk. Apply same fix: simple
for-loop with MAX_ROLL_COUNT cap.

### JR-ML-DOC-005 — Fix semantic error in SECURITY_AUDIT_PLAN.md line 845 - correct deep relative path to ../CLAUDE.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-07_JUNIPER-ECOSYSTEM_CROSS-REPO-LINK-RESOLUTION-PROPOSAL.md` (lines 246-264)

**Detail**:

Category D false-negative: ../../../CLAUDE.md resolves to wrong document via repo-root fallback.
Should be ../CLAUDE.md to reference repo's own CLAUDE.md (symlink to AGENTS.md) containing the same #worktree-procedures-mandatory--task-isolation section.

### JR-ML-DEP-026 — Fix the existing `juniper_plant_all.bash` and `juniper_chop_all.bash` scripts with health checks, error handling, and configurability. Add….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 504-529)

**Detail**:

Fix the existing `juniper_plant_all.bash` and `juniper_chop_all.bash` scripts with health checks, error handling, and configurability. Add missing systemd units and worker deployment config.

**Notes**:

[v3 brief repaired from cited content; was: '9.1 Approach A: Incremental Fix (Recommended)']

### JR-CAN-API-032 — Fix uppercase status normalization gap in WebSocket relay path (ISS-06 architectural fragility).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 404-448)

**Detail**:

ISS-06 HIGH (latent). CasCor TrainingStateMachine.get_state_summary() returns UPPERCASE status (.name values: "STARTED", "PAUSED", "COMPLETED", "FAILED", "STOPPED"). _normalize_status() mapping lacks uppercase entries. Sync path calls .lower() before lookup (partially protected). Relay callback path (cascor_service_adapter.py:222) passes raw status with NO .lower() call — unprotected. When cascor broadcasts "STARTED" via WebSocket, relay's _normalize_status("STARTED") falls through to default "Stopped", incorrectly updating training_state. FakeCascorClient emits uppercase, so tests using fake client against relay path trigger this bug. Architectural risk: any future CasCor change to uppercase enum .name values via WebSocket would cause incorrect status.

**Notes**:

Post-validation finding: current production WebSocket state messages use title-case (protected). But vulnerability exists in test paths and is latent architectural fragility.

### JR-CAS-TRAIN-028 — Fix validate_training_results bug - uninitialized variables in edge cases.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 381-393)

**Detail**:

Line 2750: TODO marked. Variable initialized to None, only set inside for loop. If
max_epochs=0, post-loop check references unbound epoch variable. Fix: initialize epoch
and validate_training_results before loop.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-TRAIN-029 — Fix validate_training_results None initialization bug in training loop.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 374-378)

**Detail**:

Variable initialized as None; if training loop doesn't execute (e.g. max_epochs=0), debug log crashes with AttributeError on .early_stop.

### JR-ML-TEST-033 — For each application (in dependency order):.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 364-375)

**Detail**:

1. Create git tag: `git tag -a v<VERSION> -m "Release v<VERSION>"`

**Notes**:

[v3 brief repaired from cited content; was: '5.2 Per-Application Release Steps']

### JR-ML-SEC-150 — For each application, compile changelog entries from git history:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 273-286)

**Detail**:

| juniper-ml            | Populate [Unreleased], rename to [0.4.0] | Added, Changed, Fixed, CI                                                   |

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Changelog Updates']

### JR-ML-TEST-034 — For each radio group, associated inputs are indented (`ms-3` or `ms-4`) and conditionally disabled:.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 385-414)

**Detail**:

html.P("Network Growth Triggers:", className="mb-1 fw-bold"),

**Notes**:

[v3 brief repaired from cited content; was: '6.2 Radio Button Sub-field Pattern']

### JR-ML-SEC-151 — For juniper-ml, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 327-337)

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Build & Package Validation (PyPI packages only)']

### JR-ML-SEC-152 — `force_sequential_training` autouse fixture masks all multiprocessing bugs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1002-1022)

### JR-ML-SEC-153 — Future (If Scale Demands).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 735-750)

**Detail**:

1. **Docker Compose demo profile**: Run real CasCor with auto-start training for stakeholder demos.

### JR-ML-SEC-154 — Future enhancements: CAN-000 through CAN-021 (meta param menu, training metrics UI, parameter tuning tab, snapshot capture/replay).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 168-178)
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 280-310)

**Detail**:

| Task 1A: Validation loss/accuracy overlay traces | ❌ NOT STARTED | —       |

**Notes**:

[v3 xrepo fuzzy merge: owners=cas,ml, n=2] [v2 remap: BG→TRAIN]

### JR-ML-OBS-094 — GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy /api/ws_latency + histogram).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 57-57)

**Notes**:

Settled position C-20 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-055 — `generator.generate(params)` is synchronous inside async handler. Blocks event loop for large datasets (MNIST: 60K samples).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 159-169)

**Detail**:

| ID        | Severity   | File:Line                        | Description

**Notes**:

[v4 brief repaired; was: '3.1 Bugs']

### JR-DAT-SEC-003 — GitHub Actions versions must be pinned to SHA, not floating refs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 62-63)

**Notes**:

SEC-004 MEDIUM (P2). ci.yml:70,73,84, etc.

### JR-ML-API-056 — **Guardrails**: Validate params against same whitelist as REST endpoint.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 182-207)

**Detail**:

**Severity**: S2 | **Effort**: Small (0.5 day) | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '3.3 CR-008: Implement WebSocket `set_params`']

### JR-ML-DATA-018 — H-JDC-2: PATCH excluded from retry allowed_methods (`client.py:101`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 187-195)

**Detail**:

**H-JDC-1: Real client HTTP tests missing for 6 methods**:

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-SEC-155 — H-JDP-1: Makefile `prepare-secrets` uses undefined variables (`Makefile:70-72`).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 355-373)

**Detail**:

**H-JDP-1: Makefile `prepare-secrets` uses undefined variables** (`Makefile:70-72`)

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-TEST-035 — Handler returns `dash.no_update` for the triggering component.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 423-431)

**Detail**:

The `sync_multi_node_checkboxes` callback has components as both Input and Output. This is safe because:

**Notes**:

[v3 brief repaired from cited content; was: '7.2 Circular Dependency Risk']

### JR-CAN-UI-029 — Hardcoded colors must be extracted to theme_constants.py for DRY.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 168-168)

**Detail**:

Issue 3.3.1: Color strings repeated across components. Extract to
theme_constants.py for centralized management and dark/light theme support.

### JR-CAN-DEP-005 — Hardcoded localhost:8050 URLs in MetricsPanel; breaks in Docker/reverse-proxy/non-standard host (ISS-10).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 515-538)

**Detail**:

ISS-10 MODERATE. Multiple metrics_panel.py locations use hardcoded http://localhost:8050 URLs: line 1000 (/api/network/stats), line 1021 (/api/state), line 1155-1231 (metrics layout endpoints), line 1274 (layout delete). No dynamic URL construction method (_api_url()) exists in file — all hardcoded. When canopy runs in Docker, behind reverse proxy, or non-standard host/port, requests fail silently with ConnectionError. Affected panels (network stats, training state, metrics layout management) return fallback/empty data or fail to persist customizations.

**Notes**:

Identified by v4. Validation found 4 additional hardcoded localhost URLs beyond initial 2 identified.

### JR-ML-DATA-019 — Hardcoded values refactor (~89 values → `constants.py`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 402-409)

**Detail**:

| Hardcoded values refactor (~89 values → `constants.py`) | ✅ Complete        |

**Notes**:

[v4 brief repaired; was: '7.4 juniper-data-client — Constants Refactor ✅ COMPLETE']

### JR-CWK-WS-002 — Hardcoded values refactoring: create juniper_cascor_worker/constants.py to consolidate ~50 hardcoded values (protocol messages, activation functions, training defaults, WebSocket config, validation bounds).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 1-50)

**Detail**:

~50 hardcoded values across 7 source files. Existing infrastructure: config.py WorkerConfig dataclass (8 field defaults, partial coverage). Gaps: protocol message type strings (7), activation function names (3), training hyperparameters (6 — epochs, learning rate, display frequency, value scales), WebSocket config (4), config duplicates across config.py/cli.py/env defaults (6), validation constants (2), error handling (2). Coverage summary: ~3 covered (partial), ~47 not covered. Proposed solution: create constants.py with sections for protocol types, activation functions, training defaults, WebSocket, config defaults, validation, error handling. Update config.py, cli.py, worker.py, task_executor.py, ws_connection.py to import from constants.py. Key benefit: eliminates 3-way duplication between config.py, cli.py, env var defaults.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-API-057 — have marker REMOVED (R5.1b); the 2 non-re-bucketed cascor histograms.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 305-331)

**Detail**:

**Scope**: Bucket→SLO alignment, R5.1b coverage of the 2 non-re-bucketed

**Notes**:

[v3 brief repaired from cited content; was: '4.4 Dimension D — Buckets + test coverage']

### JR-ML-API-058 — Health-check-based startup in `juniper_plant_all.bash`.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 468-489)

**Detail**:

| Health-check-based startup in `juniper_plant_all.bash` | High   | Low     | **P0**   | **Resolved** (commit `03aec86`)           |

**Notes**:

[v4 brief repaired; was: '8.1 Priority Matrix']

### JR-ML-SEC-156 — Hidden unit forward pass recomputed redundantly every output training epoch.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 841-859)

### JR-DAT-OBS-005 — Histogram R5.1 ratification decides SLO targets p95 <100ms and p99 <1s, optionally collapses low-information buckets.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 71-87)

**Notes**:

Tentative layout pending R5.1 SLO design. HELP-string marker points to rationale doc.

### JR-ML-OBS-095 — **Host-mode startup (`juniper_plant_all.bash`)** -- overhauled in commit `03aec86`. Now uses `wait_for_health()` polling, `check_port_availa.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 38-51)

**Detail**:

1. **Host-mode startup (`juniper_plant_all.bash`)** -- overhauled in commit `03aec86`. Now uses `wait_for_health()` polling, `check_port_available()`, `validate_conda_env()`, per-service Python binaries, `set -euo pipefail`, `trap clean

**Notes**:

[v4 brief repaired; was: 'Key Findings']

### JR-ML-ARCH-254 — HSK-01: 3 Broken Symlinks in canopy `notes/development/`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2881-2895)

### JR-ML-ARCH-255 — HSK-02: `src/remote_client/` Directory Still Exists.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2898-2902)

### JR-ML-ARCH-256 — HSK-03: `src/spiral_problem/check.py` — 600-Line Stale Duplicate.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2905-2909)

### JR-ML-ARCH-257 — HSK-04: 32 Test Files with Hardcoded `sys.path.append`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2912-2916)

### JR-ML-TRAIN-073 — HSK-05: cascor-client AGENTS.md Header Version 0.3.0 vs Package 0.4.0.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2919-2933)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-DOC-006 — HSK-06: juniper-data AGENTS.md Header Version 0.5.0 vs Package 0.6.0.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2936-2940)

**Notes**:

[v2 ARCH→DOC re-bucket]

### JR-ML-TRAIN-074 — HSK-07: cascor-client File Headers Show Versions 0.1.0–0.3.0.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2943-2947)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TEST-036 — HSK-08: data-client `tests/conftest.py` Version Header Says 0.3.1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2950-2954)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TRAIN-075 — HSK-09: Dead Code `_STATE_TO_FSM` and `_STATE_TO_PHASE` in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2957-2982)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TOOL-037 — HSK-10: `scripts/test.bash` Outdated/Non-Functional.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2985-3010)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-ARCH-258 — HSK-11: `wake_the_claude.bash` `DEBUG="${TRUE}"` Hardcoded ON.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3013-3028)

### JR-ML-TEST-037 — HSK-12: `NOHUP_STATUS=$?` Captures Fork Status (Always 0).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3031-3045)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-ARCH-259 — HSK-13: 169 Hardcoded ThemeColors Remain in canopy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3048-3062)

### JR-ML-ARCH-260 — HSK-14: `resume_session.bash` Contains Hardcoded Session UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3065-3087)

### JR-ML-TOOL-038 — HSK-15: `util/global_text_replace.bash` Is a No-Op.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3090-3112)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-039 — HSK-16: `util/kill_all_pythons.bash` Uses `sudo kill -9` on ALL Python Processes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3115-3129)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-040 — HSK-17: `util/worktree_new.bash` Hardcodes Branch/Repo Names.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3132-3146)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-041 — HSK-18: `util/worktree_close.bash` Hardcodes Default Identifier.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3149-3163)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-ARCH-261 — HSK-19: Stale Files in Repo Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3166-3180)

### JR-ML-ARCH-262 — HSK-20: `claude_interactive.bash:17` `DEBUG="${TRUE}"` Hardcoded.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3183-3198)

### JR-ML-ARCH-263 — HSK-21: `wake_the_claude.bash:53` Stale TODO Comment.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3201-3215)

### JR-ML-ARCH-264 — HSK-22: `wake_the_claude.bash:547` TODO — Model Parameter Never Validated.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3218-3232)

### JR-ML-TRAIN-076 — HSK-23: `scripts/juniper-all-ctl:38` Cascor Port Defaults to 8200 (Container) vs Host 8201.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3235-3249)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-077 — HSK-24: Unused Constants in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3252-3277)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-DATA-020 — Identify from git log

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 305-314)

**Detail**:

| juniper-ml            | v0.2.1, v0.3.0 | Identify from git log |

**Notes**:

[v4 brief repaired; was: '4.1 Create Missing Retroactive Tags']

### JR-ML-DEP-027 — **Image availability**: k3s uses containerd, not Docker. Images built with Docker must be imported:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 1472-1672)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 4:']

### JR-ML-API-059 — Immediate (No Infrastructure Changes).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 721-727)

**Detail**:

1. **Refactor Canopy's backend branching**: Define a `BackendProtocol` that both `DemoMode` and `CascorServiceAdapter` implement. Eliminate scattered `if demo_mode_instance:` checks in `main.py

### JR-ML-DEP-028 — Implement auto-start configuration for JuniperCascor: create network, load dataset, begin training on startup.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 3294-3494)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 7:']

### JR-DEP-DEP-006 — Implement native systemd user-unit deployment mode alongside Docker Compose.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 1-30)

**Detail**:

Phase 2 systemd implementation provides zero containerization overhead, direct GPU/CUDA access,
dependency ordering via systemd After=/Requires=, health monitoring via timer-triggered one-shot
services, per-service resource accounting via cgroups v2, and security hardening.
Coexists with Docker Compose deployment. Both methods manage the same 3 core services
(juniper-data, juniper-cascor, juniper-canopy) with independent conda environments.

**Design**:

File layout: systemd/user/*.service (10 unit files), systemd/install.sh, scripts/wait_for_health.sh,
scripts/health_check_systemd.sh, conf/juniper.env.example, scripts/juniper-ctl CLI wrapper.
Tasks 2.1–2.14 define complete implementation with resource limits, health checks, and lifecycle validation.

### JR-ML-PERF-013 — Implement performance optimizations from training analysis.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/TRAINING_PERFORMANCE_ANALYSIS_2026-03-20.md` (lines 1-100)

**Notes**:

Throughput and latency improvements.

### JR-ML-TOOL-042 — Implement phased prompt automation: Phase 1 snippets (1 day), Phase 2 discovery scripts (2 days), Phase 3 template rendering (2-3 days).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` (lines 1081-1150)

### JR-ML-SEC-157 — Implement secrets management strategy for Juniper ecosystem (analysis-driven).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECRETS_MANAGEMENT_ANALYSIS.md` (lines 1-100)

### JR-ML-TOOL-043 — Implement thread handoff procedure: context transfer, worktree state, verification commands.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-IMPLEMENTATION.md` (lines 1-50)

### JR-ML-OBS-096 — Implement unified health probe semantics and status code propagation across Juniper services.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md` (lines 1-50)

**Notes**:

R1.2 phase of METRICS-MON program.

### JR-ML-WS-147 — Implement WebSocket remote worker infrastructure: /ws/v1/workers endpoint, WorkerRegistry, WorkerCoordinator, binary protocol.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 852-890)

**Design**:

Phase 1b WebSocket endpoint with JWT auth, binary message frames, task assignment/result collection, worker heartbeat management.

### JR-ML-UI-048 — In demo mode, networks with 2+ hidden units display an **incomplete topology** — missing the signature cascade connections between hidden….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 385-389)

**Detail**:

In demo mode, networks with 2+ hidden units display an **incomplete topology** — missing the signature cascade connections between hidden units. The visualization appears as a standard feedforward network rather than a cascade correlation network.

**Notes**:

[v3 brief repaired from cited content; was: 'Consequence']

### JR-ML-API-060 — Inconsistency**: Health check endpoints differ (`/v1/health` vs `/v1/health/ready`). All should use `/v1/health` for liveness and….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 341-360)

**Detail**:

| Base image    | python:3.14-slim         | python:3.14-slim       | python:3.14-slim     |

**Notes**:

[v3 brief repaired from cited content; was: '4.4 Per-Service Dockerfile Review']

### JR-CAS-TEST-014 — Increase code coverage from ~15-78% baseline to 90% target via additional unit tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 543-589)

### JR-CAS-TRAIN-030 — Integration fixes: 9 JuniperData items (API path, deprecation warnings, auth, NPZ validation, contract tests, retry/backoff).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 138-145)

**Detail**:

CAS-INT-001 through CAS-INT-009 verified complete. Items include: API path validation, deprecation warning handling, authentication token management, NPZ format validation, data contract tests, max_retries=3 retry logic with backoff, status code normalization, error classification. All integrated with current JuniperData REST API. Async training boundary via ThreadPoolExecutor. RemoteWorkerClient integration via REST endpoints. Test suite CI/CD phases 0-4 complete (MED-014 line length deferred).

**Notes**:

[v2 remap: BG→TRAIN]

### JR-ML-DATA-021 — Integration tests (cascor `set_params` via WS)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 248-257)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 203-216)

**Notes**:

[v4 brief repaired; was: '8.2 Phases Still Incomplete']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-158 — Integration tests rely on fixed `time.sleep()` for async training synchronization.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 951-969)

### JR-CAN-TEST-028 — Integration tests use time.sleep(0.2)-based timing for synchronization across multiple files; fragile and platform-dependent.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 30-30)

**Detail**:

Three sites hardened in PR #264; more remain. Sleep-based timing should be replaced with event-driven synchronization or pytest fixtures.

**Notes**:

Audit recommended for codebase-wide cleanup.

### JR-ML-TRAIN-078 — Investigate V38 grow-network performance; characterize scaling limits and convergence behavior.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-CASCOR_V38-GROW-NETWORK-INVESTIGATION-PLAN.md` (lines 1-50)

### JR-ML-OBS-097 — `is_alive()` catches both `JuniperCascorClientError` and builtin `ConnectionError`. The latter is dead code — `requests.ConnectionError` pro.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 52-62)

**Detail**:

| ID        | Severity   | File:Line                    | Description

**Notes**:

[v4 brief repaired; was: '1.1 Bugs']

### JR-ML-SEC-159 — Issue Remediations, Section 15 — juniper-data-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 506-556)

**Detail**:

#### DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles"

### JR-ML-SEC-160 — Issue Remediations, Section 9.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 343-392)

**Detail**:

#### 5.1: AlertManager Receivers — Placeholders Only

### JR-ML-UI-049 — Issue Summary Table.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 42-54)

**Detail**:

| **OI-5** | LOW | Quality | Initial sync topology never pushed to Dash store | juniper-canopy | **FIXED** (2beea5c) — fallback in `ServiceBackend.get_network_topology()` |

### JR-ML-API-061 — Issue**: Inconsistent endpoint availability. All services should implement the full set: `/v1/health` (basic), `/v1/health/live`….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 414-424)

**Detail**:

**Issue**: Inconsistent endpoint availability. All services should implement the full set: `/v1/health` (basic), `/v1/health/live` (liveness), `/v1/health/ready

**Notes**:

[v3 brief repaired from cited content; was: '7.1 Health Check Consistency']

### JR-ML-DEP-029 — Issue**: juniper-cascor uses port 8201 in host mode and Docker published port, but 8200 internally. The `get_cascor_*.bash` scripts….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 424-434)

**Detail**:

**Issue**: juniper-cascor uses port 8201 in host mode and Docker published port, but 8200 internally. The `get_cascor_*.bash` scripts hardcode 8201. Documentati

**Notes**:

[v3 brief repaired from cited content; was: '7.2 Port Assignments']

### JR-ML-OBS-098 — Issues Previously Identified and Now Resolved.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 794-809)

**Detail**:

| RC-1: Stale editable install | DATASET_DISPLAY_BUG_ANALYSIS.md | Fixed: `get_dataset_data()` added to client, version bumped to 0.3.0 |

### JR-ML-SEC-161 — Issues Previously Identified and Still Outstanding.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 809-859)

**Detail**:

| response.ok returns bad default | DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN.md Phase 3/5 | OI-1 |

### JR-ML-DATA-022 — JD-PERF-01: Sync `generator.generate()` Blocks Event Loop

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3534-3538)

### JR-ML-DATA-023 — JD-PERF-02: `filter_datasets`/`get_stats` Load ALL Metadata

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3541-3555)

### JR-ML-DATA-024 — JD-PERF-03: `list_versions` Loads All Metadata

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3558-3569)

### JR-ML-DATA-025 — JD-PERF-04: No Connection Pooling for Postgres

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3572-3586)

### JR-ML-DATA-026 — JD-PERF-05: Readiness Probe Filesystem Glob

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3589-3593)

### JR-ML-DATA-027 — JD-SEC-01: Path Traversal via `dataset_id` in Filesystem Paths

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3485-3507)

### JR-ML-DATA-028 — JD-SEC-02: API Key Comparison Not Constant-Time (data)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3510-3518)

### JR-ML-DATA-029 — JD-SEC-03: Rate Limiter Memory Unbounded (data)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3521-3529)

### JR-ML-TRAIN-079 — `juniper-cascor-client/testing/__init__.py` exports `FakeCascorClient` and `FakeCascorTrainingStream` only. No fake for….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 345-349)

**Detail**:

`juniper-cascor-client/testing/__init__.py` exports `FakeCascorClient` and `FakeCascorTrainingStream` only. No fake for `CascorControlStream`. Consumers testing WebSocket control (e.g., `set_params`) cannot use the testing subpackage.

**Notes**:

[v3 brief repaired from cited content; was: '6.3 Medium: No FakeCascorControlStream (XREPO-03 — confirmed']

### JR-ML-OBS-099 — `juniper-deploy/grafana/provisioning/dashboards/`. All four ship at.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 286-310)

**Detail**:

| 4.1 | Worker heartbeat freshness | `< 30s` per worker | n/a (instant) | Computable post juniper-cascor#188 (`WorkerRegistryCollector` ships `juniper_cas

**Notes**:

[v3 brief repaired from cited content; was: '5.2 Internal-supporting SLIs (graphed-only, 8)']

### JR-ML-OBS-100 — JuniperCanopy implements a two-mode activation system in `src/main.py` (lines 213-247):.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 328-342)

**Detail**:

JuniperCanopy implements a two-mode activation system in `src/main.py` (lines 213-247):

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Current Implementation']

### JR-ML-DATA-030 — `juniper_data_client/__init__.py` — update `__version__` to `"0.4.0"`

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 63-73)

**Detail**:

- `pyproject.toml` — bump version to `0.4.0`

**Notes**:

[v3 brief repaired from cited content; was: '1.3 juniper-data-client: Version Alignment']

### JR-ML-SEC-162 — `juniper_observability` mounted at app construction): emits.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 68-96)

**Detail**:

| `/metrics` URL | `http://juniper-data:8100/metrics` (compose); `http://localhost:8100/metrics` (local) |

**Notes**:

[v3 brief repaired from cited content; was: '3.1 juniper-data']

### JR-ML-SEC-163 — JUNIPER_WS_ALLOWED_ORIGINS=* explicitly REFUSED by the parser.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 67-67)

**Notes**:

Settled position C-30 from R3-03 table; cross-round consensus consolidation

### JR-ML-DOC-007 — Keep AGENTS.md synchronized with project structure.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/AGENTS_MD_DRIFT_ANALYSIS_2026-04-02.md` (lines 1-100)

**Notes**:

Drift analysis identifies documentation gaps.

### JR-ML-OPS-008 — Kill switch MTTR ≤5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 76-76)

**Notes**:

Settled position C-39 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-050 — KL-1: Dataset Scatter Plot Empty in Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1963-1977)

### JR-ML-PERF-014 — Latency instrumentation hooks for set_params round-trip measurement.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 539-590)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-TEST-038 — Latency tests are recording-only in CI (latency_recording marker); strict assertions local-only.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 72-72)

**Notes**:

Settled position C-35 from R3-03 table; cross-round consensus consolidation

### JR-CAN-TRAIN-008 — Live dataset swap during training requires experimental-functions gate, pause/resume lifecycle, architecture adaptation, and snapshot/replay persistence.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 15-48)

**Detail**:

Functional requirements F2.1-F2.10: live switch without stopping, opt-in gate (env var CASCOR_EXPERIMENTAL_FUNCTIONS_ENABLED), two-step warning modal, architecture delta handling (grow/shrink), snapshot at swap point, replay support, server-side gate enforcement. Orchestration: pause → reload via _reload_dataset → architecture_adapter.adapt_for_dataset_swap → restart with mode='output_training_first' → resume.

**Design**:

Cascor lifecycle method swap_dataset_live: acquire _training_lock, validate gate + is_started(), snapshot pre-swap state (tensors, weights, dataset_cfg, dims), pause, stop training future, _reload_dataset, compute arch delta, adapt_for_dataset_swap, drop candidate pool (Option C: abandon), submit new future, resume. Rollback on failure.

**Notes**:

Requires P2-PRE-1 pause/stop audit. Original draft referenced non-existent cascor components; design review replaced with actual surface.

### JR-ML-SEC-164 — Locks in lifecycle manager; `_topology_lock` for safe reads during training.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 505-523)

**Notes**:

[v4 brief repaired; was: '6.2 Guardrails']

### JR-ML-API-062 — M-JCC-3: Handshake not validated in `CascorControlStream.connect()` (`ws_client.py:178`).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 239-255)

**Detail**:

**M-JCC-1: `wait_for_ready()` calls `is_alive()` instead of `is_ready()`** (`client.py:86`)

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-ML-TRAIN-080 — M-JCW-2: No WebSocket receive timeout (`ws_connection.py:134`).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 306-317)

**Detail**:

**M-JCW-1: No task execution timeout** (`worker.py:201`)

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-ML-OBS-101 — M-JD-1: Sentry PII enabled by default (`observability.py:139`).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 142-150)

**Detail**:

**M-JD-1: Sentry PII enabled by default** (`observability.py:139`)

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-ML-API-063 — **M-JDC-2: docs/QUICK_START.md references `FakeJuniperDataClient`** — should be `FakeDataClient`.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 195-201)

**Detail**:

**M-JDC-1: docs/REFERENCE.md stale** — version header says 0.3.1, missing batch and versioning documentation

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-ML-DATA-031 — M-ML-1: `test_worktree_cleanup.py` not run in CI (`ci.yml:109-110`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 67-78)

**Detail**:

**M-ML-1: `test_worktree_cleanup.py` not run in CI** (`ci.yml:109-110`)

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-CAN-TEST-029 — main.py test coverage must increase from 84% to 95% target for critical paths.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 234-246)

**Detail**:

Gap is primarily in real-backend code paths and error handling branches not exercised in demo mode.
Estimated scope: 1-2 test files, 200-300 lines.

**Notes**:

CAN-HIGH-008; HIGH priority post-release item.

### JR-ML-API-064 — Major features (dataset versioning CAN-DEF-005, batch endpoints CAN-DEF-006, Docker secrets, systemd support, Postgres concurrency fixes)….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 131-142)

**Detail**:

**H-JD-1: 60+ commits since v0.5.0 not in CHANGELOG**

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-DATA-032 — Methods catching only `JuniperCascorClientError` (not yet broadened)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 505-522)

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-DEP-030 — Migrate JuniperCanopy from YAML-based `ConfigManager` to Pydantic v2 `BaseSettings`.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 4251-4451)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 9:']

### JR-ML-SEC-165 — Missing `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` env vars. Canopy deployment won't wire to backend services.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 272-281)

**Detail**:

| DD-K8S-01 | **Medium** | `values.yaml:306`     | Redis `auth.enabled: false` — no authentication.

**Notes**:

[v4 brief repaired; was: '5.2 Kubernetes/Helm Issues']

### JR-CAN-UI-030 — Modulo toggle for theme switching must use Dash State, not module-level flag.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 169-169)

**Detail**:

Issue 3.3.2: Theme toggle using module-level variable instead of callback State.
Can cause race conditions in multi-user scenarios. Use dcc.Store for theme state.

### JR-CAN-TEST-030 — Move 5 non-test files (scripts, manual verifiers) out of test directory to util/.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 99-108)

**Detail**:

Files like test_yaml.py, test_dashboard_init.py are print-based scripts with no assertions. Should be moved to util/ for clarity.

**Notes**:

Category B: 5 files; Phase 1 high priority

### JR-CAS-LOCK-002 — Move dill to test-only dependencies or add proper import guard - currently undeclared runtime dep.

**Status**: proposed  **Priority**: P2  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 532-544)

**Detail**:

check_object_pickleability in src/utils/utils.py:248 imports dill (not in dependencies).
Will crash with ModuleNotFoundError if called. Move to test dependencies or add guard.

### JR-CAS-DOC-004 — Move top-level import traceback statements - currently repeated in exception handlers.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 547-559)

**Detail**:

Multiple locations in cascade_correlation.py have import traceback inside except
blocks. Move to file-level imports.

### JR-ML-WS-148 — `MSG_TYPE_TOKEN_REFRESH` defined but never referenced — dead code (forward compatibility?).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 123-132)

**Detail**:

|    ID    | Severity | File:Line               | Description                                                                                 |

**Notes**:

[v4 brief repaired; was: '2.3 Code Quality']

### JR-CAN-OBS-014 — Multiple hardcoded localhost:8050 URLs in MetricsPanel (6+ instances) prevent non-local deployment and cross-origin access.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 415-445)

**Detail**:

Lines 1050, 1075, 1085, 1095, 1105, 1110 reference hardcoded localhost:8050. Must use environment variable or configuration endpoint.

**Notes**:

Blocks deployment to non-localhost targets.

### JR-ML-TEST-039 — Multiple regression analysis documents for training defects (01-09).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-ANALYSIS-03.md` (lines 1-50)

### JR-CAN-TEST-031 — Multiple test files contain 25+ exception suppressions (try/except pass) that hide real errors and should be replaced with proper assertions.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

**Detail**:

Suppressions mask failures and prevent test failures from surfacing. Must audit and replace with proper error handling and assertions.

**Notes**:

Identified in test audit as 25+ suppression sites.

### JR-ML-OBS-102 — Must handle conda activation from Python (tricky).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 529-564)

**Detail**:

**Risk**: Medium. New code means new bugs. Conda activation from Python subprocess is notoriously fragile.

**Notes**:

[v3 brief repaired from cited content; was: '9.2 Approach B: Unified CLI Tool (juniper-ctl)']

### JR-ML-DEP-031 — Near-Term (Docker Compose Adoption).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 727-735)

**Detail**:

1. **Create ecosystem-level `docker-compose.yml`**: Define all 3 services + Redis with health-gated dependency ordering. Place at `Juniper/docker-compose.yml` (or `Juniper/juniper/docker-compose.yml`).

### JR-ML-TRAIN-081 — Neither `CascorTrainingStream` nor `CascorControlStream` implements reconnection. For training runs lasting hours, a network hiccup….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 228-239)

**Detail**:

**H-JCC-1: CHANGELOG missing v0.2.0 and v0.3.0 entries**

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-TRAIN-082 — Network Architecture.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 330-337)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 266-273)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-CAN-ARCH-005 — NetworkVisualizer callback is overloaded and must be split.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 172-172)

**Detail**:

Issue 3.3.5: Single callback handles too many inputs. Split into separate
callbacks for layout changes, theme changes, and data updates.

### JR-ML-UI-051 — NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 58-58)

**Notes**:

Settled position C-21 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-103 — Neural network training, CPU/memory intensive.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 46-54)

**Notes**:

[v4 brief repaired; was: '2.5 Resource limits']

### JR-ML-DATA-033 — NEW (replaces `convergence-enabled-checkbox`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 39-56)

**Detail**:

| 3  | Learning Rate         | `nn-learning-rate-input`                | number (float) | 0.01            | RENAMED (was `learning-rate-input`)           |

**Notes**:

[v4 brief repaired; was: '2.1 Neural Network Subsection (12 inputs)']

### JR-ML-UI-052 — **New file**: `juniper-cascor/scripts/juniper-cascor-ctl`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 253-263)

**Detail**:

**New file**: `juniper-cascor/scripts/juniper-cascor-ctl`

**Notes**:

[v3 brief repaired from cited content; was: '5.5 juniper-cascor-ctl (Step 2.5)']

### JR-ML-SEC-166 — **New file**: `juniper-cascor/scripts/juniper-cascor.service`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 195-245)

**Detail**:

**New file**: `juniper-cascor/scripts/juniper-cascor.service`

**Notes**:

[v3 brief repaired from cited content; was: '5.4 juniper-cascor.service (Step 2.2)']

### JR-ML-SEC-167 — **New file**: `juniper-data/scripts/juniper-data.service`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 128-178)

**Detail**:

**New file**: `juniper-data/scripts/juniper-data.service`

**Notes**:

[v3 brief repaired from cited content; was: '5.2 juniper-data.service (Step 2.1)']

### JR-ML-UI-053 — **New file**: `juniper-ml/scripts/juniper-all.target`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 263-298)

**Detail**:

**New file**: `juniper-ml/scripts/juniper-all.target`

**Notes**:

[v3 brief repaired from cited content; was: '5.6 juniper-all.target (Step 2.6)']

### JR-ML-SEC-168 — **No docker-integration CI job** — compose config validated but services never built/started/tested. Planned in `CONTAINER_VALIDATION_CI_PLA.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 300-311)

**Detail**:

| TST-01 | **Medium** | No Helm chart tests in CI (`helm lint` only in pre-commit, not CI).                                                                                                         |

**Notes**:

[v4 brief repaired; was: '5.5 Test Coverage Gaps']

### JR-ML-SEC-169 — No integration tests (marker defined, zero tests use it); no binary frame edge case tests.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 132-142)

**Detail**:

| `cli.py`           | 90.70%   | Second SIGINT force-exit path; post-`asyncio.run` log line                                |

**Notes**:

[v4 brief repaired; was: '2.4 Test Coverage Gaps']

### JR-ML-TRAIN-083 — No integration tests against live cascor; no `FakeCascorControlStream` (XREPO-03 confirmed); no test markers on `test_set_params.py`.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 81-89)

**Detail**:

| `client.py`    | 82.22%   | `wait_for_ready()` polling, JSON decode errors, fallback error message path                                                          |

**Notes**:

[v4 brief repaired; was: '1.4 Test Coverage Gaps']

### JR-ML-DEP-032 — No Kubernetes manifests exist anywhere in the Juniper ecosystem.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 360-364)

**Notes**:

[v3 brief repaired from cited content; was: '5.1 Current State']

### JR-ML-SEC-170 — No validation that TLS cert/key/CA paths exist on disk at startup. Confusing SSL error at connect time instead of clear config error.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 114-123)

**Detail**:

| ID        | Severity | File:Line                  | Description

**Notes**:

[v4 brief repaired; was: '2.2 Security']

### JR-ML-OBS-104 — nohup redirect to timestamped files.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 444-453)

**Notes**:

[v4 brief repaired; was: '7.4 Logging']

### JR-ML-LOCK-001 — `NOHUP_STATUS=$?` captures fork status (always 0), not process exit — error check is dead code.

**Status**: proposed  **Priority**: P2  **Category**: LOCK  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 369-381)

**Detail**:

| ML-01 | **Medium** | `scripts/wake_the_claude.bash` | 37      | `DEBUG="${TRUE}"` hardcoded ON in production — all invocations emit debug output               |

**Notes**:

[v4 brief repaired; was: '2.8 juniper-ml']

### JR-CAN-API-033 — Normalize /api/metrics current snapshot endpoint; follows same broken path as metrics history (ISS-07).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 453-465)

**Detail**:

ISS-07 MODERATE. /api/metrics endpoint (current snapshot) calls cascor_service_adapter.py:86-94 get_current_metrics() which uses _normalize_metric() producing flat keys. Conceptually subset of ISS-01 — fixing _normalize_metric() output format automatically fixes both history and current snapshot endpoints.

**Notes**:

Phase 2 focused only on /api/metrics/history; missed current endpoint.

### JR-CAN-TRAIN-009 — Normalize state sync metrics history through adapter (ISS-05 latent formatting).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 381-401)

**Detail**:

ISS-05 MODERATE. During initial state sync (state_sync.py:115-129), CascorStateSync.sync() stores raw cascor metrics directly into state.metrics_history without normalization. Raw cascor uses native field names (loss, accuracy, validation_loss, validation_accuracy, hidden_units) — different from flat canopy format (train_loss, train_accuracy) and demo nested format. Currently latent: synced.metrics_history stored but never served; polling makes fresh REST calls through normalization. Future risk: pre-populating charts from synced metrics on connect would deliver wrong format (double latent — even flat normalization wouldn't match dashboard nested consumption without ISS-01 fix).

**Notes**:

[v2 ARCH→TRAIN re-bucket] Identified by v1, v3, v5, v6, v7. Structural cause underlying ISS-05, ISS-06, ISS-12. Sync module should go through adapter or replicate normalization logic.

### JR-CAS-TOOL-009 — Not-started items: coverage gates per-module, MyPy strict mode, Spider legacy code removal, Docker end-to-end validation.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 183-198)

**Detail**:

CAS-REF-002: Coverage gates (per-module thresholds, P2, S effort). CAS-REF-003: Critical type errors MyPy strict (P2, M effort). CAS-007: Slow tests optimization (P2, M effort, 86-93% achieved Phase 6). CAS-REF-004: Legacy spiral code (16 deprecated methods, P2, M effort). INT-P3-003: Docker Compose E2E validation (P3, S effort). INT-P3-008: pytest.ini.swp and coverage files in gitignore (P3, S effort). INT-P3-010: cascor_snapshots vs snapshots directory confusion (P3, S effort). Shell scripts: 6 Oracle analysis items (P3, M effort). All 🔴 NOT STARTED or 🔵 DEFERRED.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAN-DATA-004 — NPZ dataset loading must validate dtype and shape of all arrays beyond key existence checks

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 141-154)

**Detail**:

Current implementation only verifies required keys exist; does not validate array dtypes or shapes.
Malformed data causes cryptic errors downstream during training.

**Notes**:

CAN-HIGH-002; HIGH priority post-release item; marked PARTIALLY IMPLEMENTED.

### JR-CAN-UI-031 — Numeric inputs must use validation styling (red border) for out-of-range values.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 478-499)

**Detail**:

dbc.Input invalid=True property shows red border. Add pattern-matching callback
that watches min/max bounds and sets invalid flag on value change. Provides
immediate feedback without requiring Apply-button interaction.

**Notes**:

Part of Issue

### JR-ML-OBS-105 — Observability-before-behavior rule: metrics + panels + alerts land BEFORE behavior change.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 75-75)

**Notes**:

Settled position C-38 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-106 — On dashboard startup (or reconnection), the topology tab will show blank until the first successful REST poll (up to 5 seconds) while the….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 485-489)

**Notes**:

[v3 brief repaired from cited content; was: 'Consequence']

### JR-ML-WS-149 — One-resume-per-connection rule (second resume → close 1003).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 62-62)

**Notes**:

Settled position C-25 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-171 — **Orchestration quality**.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 282-299)

**Notes**:

[v4 brief repaired; was: '2.3 Comparative Evaluation']

### JR-ML-SEC-172 — Orchestration quality**: Excellent. Declarative dependency ordering with health-gated startup (`depends_on: condition: service_healthy`)….

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 116-166)

**Detail**:

#### Option A: Docker Compose (Unified)

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Startup Orchestration Options']

### JR-ML-TRAIN-084 — Output Weight Initialization: improve output layer weight init.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-05-OUTPUT-WEIGHT-INIT.md` (lines 1-38)

### JR-ML-OBS-107 — Output("network-visualizer-topology-store", "data"),.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 215-245)

**Detail**:

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-TRAIN-085 — **Outstanding**: No version bump for unreleased constants refactor. Integration test marker defined but zero tests.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 381-392)

**Detail**:

| Hardcoded values refactor → `constants.py`                 | ✅ Complete (~70 replacements) |

**Notes**:

[v3 brief repaired from cited content; was: '7.2 juniper-cascor-worker — All Planned Work ✅ COMPLETE']

### JR-ML-OBS-108 — P0 success metric: canopy_rest_polling_bytes_per_sec reduced >90% vs baseline.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 74-74)

**Notes**:

Settled position C-37 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-109 — P1 — Operationally meaningful (alerts inert, dashboards wrong, SLI math broken).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 370-380)

**Detail**:

| **3.2** | juniper-deploy | Alertmanager `tickets` receiver is a placeholder | Open small PR wiring real notification config (webhook/email/Slack); decide

### JR-ML-OBS-110 — panels (STALE — see §15 unexpected findings; metric family removed.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 360-400)

**Detail**:

Categories: 5 RED panels, 5 training panels (sessions, hidden units,

**Notes**:

[v3 brief repaired from cited content; was: '6.3 juniper-cascor.json (22 panels, version 3, title "Junipe']

### JR-CAN-API-034 — Parameter map _CASCOR_TO_CANOPY_PARAM_MAP is asymmetric: forward maps nn_growth_convergence_threshold to patience, reverse maps patience to cn_training_convergence_threshold (different field).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 668-689)

**Detail**:

Generate reverse map programmatically: _CASCOR_TO_CANOPY_PARAM_MAP = {v: k for k, v in _CANOPY_TO_CASCOR_PARAM_MAP.items()}. Add bijectivity assertion to catch future duplicates.

**Notes**:

Causes param sync to apply updates to wrong canopy parameter.

### JR-CAN-PERF-005 — Parameter retry logic must not use blocking time.sleep().

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 171-171)

**Detail**:

Issue 3.3.4: Blocking sleep in parameter retry callback blocks event loop.
Use asyncio.sleep() or defer via callback scheduling instead.

### JR-ML-SEC-173 — Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can es.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 436-444)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 347-355)

**Detail**:

| JD-SEC-01 | **HIGH**   | `storage/local_fs.py:52-58` | Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can esc

**Notes**:

[v4 brief repaired; was: '14.1 Security Issues (Confirmed Still Present)']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-UI-054 — Per `JUNIPER_2026-03-30_JUNIPER-CANOPY_DEPENDENCY-UPDATE-WORKFLOW.md`, after adding `get_dataset_data()` to juniper-cascor-client:.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 187-200)

**Detail**:

Per `JUNIPER_2026-03-30_JUNIPER-CANOPY_DEPENDENCY-UPDATE-WORKFLOW.md`, after adding `get_dataset_data()` to juniper-cascor-client:

**Notes**:

[v3 brief repaired from cited content; was: '3.4 Dependency Update When Adding Client Method']

### JR-ML-OBS-111 — Per `juniper_observability/__init__.py`:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 222-236)

**Detail**:

- **Constants (R1.1/R1.2/R1.3 contract):**

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Public symbols']

### JR-ML-SEC-174 — Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 63-63)

**Notes**:

Settled position C-26 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-055 — Per-IP WebSocket connection limit — setting not found in cascor codebase.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 356-364)

**Detail**:

| `cascade_add` correlation           | NETWORK_TOPOLOGY_DISPLAY_ANALYSIS | Hardcoded `0.0` instead of actual best candidate correlation             |

**Notes**:

[v4 brief repaired; was: 'High Priority']

### JR-ML-OBS-112 — Per-phase entry plans.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 448-454)

**Detail**:

- [`METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`](../../legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md)

### JR-ML-OBS-113 — Per-repo histogram bucket rationale.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 740-746)

### JR-ML-PERF-015 — PERF-CC-01: Blocking `torch.save`/`torch.load` in Async-Adjacent Code Paths.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4109-4123)

### JR-ML-PERF-016 — PERF-CC-02: `replay_since` Scans Entire Replay Buffer O(n).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4126-4140)

### JR-ML-PERF-017 — PERF-CC-03: `_broadcast_training_state` Uses `hasattr` Check.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4143-4157)

### JR-ML-PERF-018 — PERF-CN-01: 33 of 50 Dash Callbacks Missing `prevent_initial_call=True`.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4075-4089)

### JR-ML-PERF-019 — PERF-CN-02: f-string Logging in Hot Paths (71 Occurrences).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4092-4106)

### JR-ML-PERF-020 — PERF-JD-01: Readiness Probe Does Filesystem Glob on Every Call.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4160-4182)

### JR-ML-PERF-021 — PERF-JD-02: High-Cardinality Prometheus Labels.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4185-4193)

### JR-ML-TRAIN-086 — Phantom Inter-Cascade Training Phase: remove 1-step/epoch phantom training phase.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-01-PHANTOM-TRAINING-PHASE.md` (lines 30-48)

### JR-ML-OBS-114 — Phase 0-cascor (seq/replay/resume) — ✅ IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 302-315)

**Detail**:

| Send timeout (0.5s, GAP-WS-07 quick-fix)                               | ✅                                              |

### JR-ML-TRAIN-087 — Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 49-49)

**Notes**:

[v2 ARCH→TRAIN re-bucket] Settled position C-12 from R3-03 table; cross-round consensus consolidation

### JR-CAN-TEST-032 — Phase 1 test coverage gap: characterization tests validate flat output, not dashboard nested consumption (ISS-19).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 686-696)

**Detail**:

ISS-19 LOW. At tests/unit/test_response_normalization.py, Phase 1 characterization tests validate normalization produces correct flat output (line 96 asserts "train_loss" in result[0] or "loss" in result[0]) but never verify compatibility with dashboard's expected nested format. Testing-level manifestation of Phase 1 plan's fundamental oversight: canonical contract validated against normalization boundary, not consumption boundary. Status bar's success with flat keys masked metrics panel's different contract.

**Design**:

Add dashboard contract tests validating that normalized flat output can be transformed to/consumed as nested format dashboard expects. Include nested access patterns (metric.get("metrics", {}).get("loss", 0)) in test assertions.

**Notes**:

Identified by v5, v7. Reflects Phase 1 boundary assumption error.

### JR-ML-UI-056 — Phase 1: Foundation (Constants + Settings).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 522-528)

**Detail**:

1. Update `canopy_constants.py` with all new and changed constants

### JR-ML-DEP-033 — Phase 2 (Near-term):  Adopt Option 3 — add FakeCascorClient and FakeDataClient to.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 575-604)

**Detail**:

**Recommended approach: Phased adoption combining Options 1, 3, and 5.**

**Notes**:

[v3 brief repaired from cited content; was: '3.5 Recommendation']

### JR-ML-UI-057 — Phase 2: Demo Backend Cascade Connections (OI-3) — COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 658-672)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-UI-058 — Phase 2: systemd & Service Management (P1) -- COMPLETED.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 732-754)

**Detail**:

**Goal**: Provide OS-native service management for all three core services.

### JR-ML-DEP-034 — Phase 2: systemd & Service Management — ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 243-258)

**Detail**:

| 2.1  | `juniper-data.service` systemd unit                          | ❌ Not in juniper-deploy scripts/ (may be in individual repos) |

### JR-ML-SEC-175 — Phase 3: Worker Deployment & Container Integration — ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 258-270)

**Detail**:

| 3.1  | `juniper-cascor-worker/Dockerfile`                            | ✅ Implemented                                           |

### JR-CAN-TEST-033 — Phase 4 Test Coverage Expansion (14 tasks).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 189-214)

**Detail**:

Step 4.1 (4 gap fills): Test discovery, observability (Prometheus/Sentry),
secrets_util (SOPS paths), middleware edge cases (malformed headers).
Step 4.2 (4 new types): Security tests (auth, injection, CORS), WebSocket load,
circuit breaker resilience, API contract validation.

### JR-CAN-DOC-006 — Phase 5 Housekeeping (19 low-priority tasks across config, logging, CI/CD).

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 218-255)

**Detail**:

5.1 (5 config): Deprecation warnings, boolean/int precedence, env var migration,
Black target-version, CPU-only conda env.
5.2 (4 logging): Capture call site, timezone-aware timestamps, replace print(),
resolve FATAL_LEVEL conflict.
5.3 (6 code): AttributeError fix, message size check, exception type narrowing,
parameter forwarding, hit_rate format verification, theme-aware colors.
5.4 (4 CI/CD): Docker health check, shellcheck severity, pre-commit autoupdate,
codecov docs.

### JR-ML-SEC-176 — Phase 5: Observability & Hardening (P2-P3) -- Medium-Term.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 804-818)

**Detail**:

| 5.1  | Configure AlertManager receivers (Slack/email)   | `juniper-deploy/alertmanager/alertmanager.yml` | Low             |

### JR-ML-SEC-177 — Phase 5: Observability & Hardening — ❌ NOT STARTED.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 285-302)

**Detail**:

| 5.1  | Configure AlertManager receivers                 | ❌      |

### JR-ML-SEC-178 — Phase 5: Quality Improvements (OI-5, OI-6) — COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 706-736)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-TRAIN-088 — Phase A-SDK — ✅ IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 315-322)

**Detail**:

| `CascorControlStream.set_params()` with `command_id` correlation | ✅ In `ws_client.py` |

### JR-ML-WS-150 — Phase B ships behind two flags: enable_browser_ws_bridge + disable_ws_bridge.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 51-51)

**Notes**:

Settled position C-14 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-265 — Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 50-50)

**Notes**:

Settled position C-13 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-179 — Phase B-pre-a (security) — ⚠️ PARTIALLY IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 322-330)

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

### JR-ML-ARCH-266 — Phase C flag use_websocket_set_params=False default; 6 hard flip gates.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 65-65)

**Notes**:

Settled position C-28 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-180 — Phase display may be incorrect — field set at init but not yet updated during training transitions.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 120-134)

**Detail**:

| BUG-CC-01 | **MEDIUM** | `create_topology_message()` not implemented — No topology changes WS   | `src/api/websocket/messages.py:72`                                                | Defined and exported, no production callers. Only used in tests

**Notes**:

[v4 brief repaired; was: '5.1 juniper-cascor']

### JR-ML-PERF-022 — Phase E: Per-client pump tasks + bounded queues + policy matrix; default drop_oldest_progress_only.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 867-921)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 52-52)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-98)

**Detail**:

Replace serial fan-out in `WebSocketManager.broadcast()` with per-client pump tasks + bounded queues.
Per-client `asyncio.Queue` bounded at 256 (configurable via `Settings.ws_per_client_queue_size`).
Per-client `_pump_task` created on connect, cancelled on disconnect.
Policy dispatch: `drop_oldest_progress_only` (default) drops oldest progress events (metrics, candidate_progress);
closes 1013 for state-bearing events (state, topology, cascade_add, connection_established).
`block` (legacy): synchronously blocks broadcast until queue drains.
`close_slow`: closes 1008 if queue full >5s.
Setting: `ws_backpressure_policy = "drop_oldest_progress_only"` (env: `JUNIPER_WS_BACKPRESSURE_POLICY`).
Tests: 5 entries. Default drops oldest for progress, block policy works when opted-in, close_slow closes stalled,
slow client doesn't block fast clients, terminal state events not dropped.
Observability: `cascor_ws_dropped_messages_total{policy, reason}`, `cascor_ws_per_client_queue_depth_histogram`.

**Design**:

Single PR (P13). Overrides source-doc default (`block`) with production-safer `drop_oldest_progress_only`.
Progress events droppable, state events flow or close (prevent silent loss).

**Notes**:

[v3 xround merge: rounds=R2-0,R3-0, n=3] Conditional phase: enters if RISK-04 (backpressure issue) observed in production. Entry: Phase 0-cascor in main.
May not ship if Phase B load testing shows slow-client impact acceptable. Exit: 5 tests green, load test (50 clients,
1 slow) → fast clients <=200ms p95, dropped counters visible. Priority P2 (default), conditional entry makes it potentially deferred. / Settled position C-15 from R3-03 table; cross-round consensus consolidation / Phase E major milestone from R3-03 Phase index (§2); orchestrates implementation effort

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

### JR-ML-TEST-040 — Phase G (integration tests): 15 cascor `/ws/control` set_params tests via FastAPI TestClient + contract lane.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 976-1029)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-100)

**Detail**:

Tests in `juniper-cascor/src/tests/integration/api/test_ws_control_set_params.py`.
15 entries: happy path, whitelist filters unknown keys, init_output_weights literal validation (rejects injection),
oversized frame 64 KB rejected (4 KB per B-pre-a), network error returns error, unknown command error,
malformed JSON closes 1003, origin rejected, unauthenticated rejected, rate limit after 10 cmds,
bad init_output_weights rejected, concurrent command correlation (2 clients, echo routing correct),
set_params during training applies on next epoch (ack vs effect), echoes command_id, command_response no seq.
Contract-lane test: `test_fake_cascor_message_schema_parity` (runs in both cascor + canopy `contract` lane).
No design sketch needed (test-only phase).

**Notes**:

[v3 xround merge: rounds=R2-0,R3-0, n=2] Entry: Phase 0-cascor + Phase B-pre-b in main. Tests via FastAPI TestClient (no SDK dependency).
Exit: all 15 pass, `pytest -m contract` lane green in cascor + canopy. Rollback: n/a (test-only).
Dedup candidate with R3-03. / Phase G major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-DOC-008 — Phase H: `_normalize_metric` dual-format regression test + consumer audit + CODEOWNERS hard gate.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 1032-1077)

**Detail**:

Phase does NOT refactor `_normalize_metric`; locks in dual-format contract (flat keys + nested keys) with regression gate.
Tests in `juniper-canopy/src/tests/unit/test_normalize_metric.py`.
Regression: `test_normalize_metric_produces_dual_format` asserts BOTH nested (`{training: {loss: 0.5}}`) AND flat (`{training.loss: 0.5}`) on output.
Additional tests: nested format unchanged since Phase H, flat format unchanged since Phase H.
Consumer audit document: `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` enumerates every consumer:
frontend MetricsPanel, CandidateMetricsPanel, Prometheus `/api/metrics`, WebSocket drain, debug logger, test fixtures.
CODEOWNERS: `juniper-canopy/src/backend/normalize_metric.py @<project-lead>` + `juniper-canopy/src/frontend/components/metrics_panel.py @<project-lead>`.
`.github/CODEOWNERS` branch protection enforces owner review.

**Design**:

Single PR (P16). Test-only phase; refactoring deferred to follow-up (gated on audit findings).

**Notes**:

Entry: Phase B in main. Exit: regression tests pass, CODEOWNERS enforced (test via PR without owner review → must block),
consumer audit reviewed + merged. Rollback: revert P16 (10 min TTF); CODEOWNERS rule disappears.
Note: Phase H is NOT a behavior-change gate; it's a documentation + regression-gate phase.

### JR-ML-OBS-115 — Phase R4: Best-practice and ergonomic improvements for observability.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md` (lines 1-50)

**Notes**:

Follows test-coverage closure (R3).

### JR-ML-OBS-116 — Phase R5: SLO/SLI catalog, scrape manifests, Grafana dashboards, and alerting.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md` (lines 1-50)

**Notes**:

Final phase of METRICS-MON program.

### JR-ML-UI-059 — Phases C–H — ❌ NOT STARTED.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 341-356)

**Detail**:

## 12. Items Not Yet Implemented

### JR-ML-SEC-181 — PID validation (check `/proc/<pid>/cmdline`).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 489-504)

**Detail**:

## 9. Development & Tooling Recommendations

**Notes**:

[v4 brief repaired; was: '8.2 Risk Assessment']

### JR-ML-TRAIN-089 — Post-Reset Desynchronization: fix desync after model reset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-10-POST-RESET-DESYNC.md` (lines 1-38)

### JR-ML-API-065 — Postgres and Redis stores not tested in CI (require live instances).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 198-206)

**Notes**:

[v3 brief repaired from cited content; was: '3.5 Test Coverage Gaps']

### JR-ML-OBS-117 — Primary catalog / program docs.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 721-728)

**Detail**:

- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (juniper-ml#195 / #194)

### JR-ML-TRAIN-090 — Priority**: SHOULD complete before release.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 113-131)

**Detail**:

**CHANGELOG changes**: Populate [Unreleased] section, then rename to [0.4.0] covering:

**Notes**:

[v3 brief repaired from cited content; was: '1.6 juniper-ml: CHANGELOG & Tags']

### JR-DAT-DOC-001 — Production startup must use create_app() factory: uvicorn juniper_data.api.app:create_app --factory or python -m juniper_data.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 239-250)

**Notes**:

D-050 MEDIUM priority. Current docs show direct app reference.

### JR-ML-SEC-182 — prometheus container's bridge-network IP must be in.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 496-513)

**Detail**:

| `prometheus` | `localhost:9090` | 15s (global default) | 10s | `/metrics` | `deployment=docker-compose`; per-job `service=prometheus`, `environment=docker` |

**Notes**:

[v3 brief repaired from cited content; was: '8.1 docker-compose (`juniper-deploy/prometheus/prometheus.ym']

### JR-ML-SEC-183 — Prometheus metrics unbounded label cardinality on `endpoint` label.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 362-395)

### JR-ML-WS-153 — PROTO-01: Canopy `/ws/control` Accepts `reset` Parameter Not in Cascor Protocol.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5252-5266)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-UI-060 — **Push vs. poll architecture**: The WebSocket infrastructure exists but key events (topology changes) still require REST polling. This creat.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 464-472)

**Detail**:

1. **Push vs. poll architecture**: The WebSocket infrastructure exists but key events (topology changes) still require REST polling. This creates unnecessary latency and server load.

**Notes**:

[v4 brief repaired; was: '5.2 Weaknesses']

### JR-ML-SEC-184 — `pyproject.toml:7` — update header comment to `Version: 0.6.0`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 30-41)

**Detail**:

- `juniper_data/__init__.py:17` — change `__version__ = "0.4.2"` to `"0.6.0"`

**Notes**:

[v3 brief repaired from cited content; was: '1.1 juniper-data: Version Synchronization']

### JR-ML-OBS-118 — pytest tests/unit/test_response_normalization.py -v       # All must pass (0 failures).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 291-302)

**Detail**:

pytest tests/unit/test_response_normalization.py -v       # All must pass (0 failures)

**Notes**:

[v3 brief repaired from cited content; was: '8.1 Automated Tests']

### JR-ML-API-066 — Radio items and checkboxes fire immediately but handler logic is O(1) comparisons.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 431-439)

**Notes**:

[v3 brief repaired from cited content; was: '7.3 Performance']

### JR-ML-UI-061 — rAF coalescer must be scaffolded but disabled by default in Phase B; revisit in Phase B+1 if frame pressure detected.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-01-FRONTEND-PERFORMANCE.md` (lines 50-120)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1475-1485)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 53-53)

**Detail**:

R0-01 §7 disagreement #1: ship scaffolded but DISABLED (wins over arch doc §5.5 which says ship enabled).
Implement _scheduleRaf = function() {} (noop) in ws_dash_bridge.js.
Leave full code structure in commented-out block for easy Phase B+1 enablement.
D1 resolution: rAF coalescer disabled.

**Notes**:

[v3 xround merge: rounds=R0-0,R1-0,R3-0, n=2] Disagreement D1 per R1-04 §14. Revisit if §5.6 instrumentation shows frame pressure. Phase B (Day 8). / Settled position C-16 from R3-03 table; cross-round consensus consolidation

### JR-CAN-TEST-034 — Re-enable MyPy error codes currently disabled (15 codes); fix underlying type issues.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 160-165)

**Detail**:

.pre-commit-config.yaml disables 15 MyPy error codes, reducing type checking effectiveness. Phase 2 work to fix underlying issues, then re-enable codes.

**Notes**:

Category H: 15 codes disabled; type safety issue

### JR-CAS-TEST-015 — Re-enable skipped critical deterministic training resume test.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 57-62)

**Detail**:

TST-004: test_comprehensive_serialization.py:41-42 has critical deterministic test
marked as skip. Remove skip decorator and enable test.

### JR-ML-API-067 — README API table (+6 methods), REFERENCE.md (version + batch/versioning), QUICK_START.md (FakeDataClient class name).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 286-294)

**Detail**:

| juniper-data-client   | README API table (+6 methods), REFERENCE.md (version + batch/versioning), QUICK_START.md (FakeDataClient class name) |

**Notes**:

[v4 brief repaired; was: '3.2 README & Documentation Updates']

### JR-CAN-TEST-035 — Real backend code paths in main.py and CascorIntegration must have integration test coverage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 170-182)

**Detail**:

All current tests run with CASCOR_DEMO_MODE=1; no integration tests for real backend.
Should gate behind CASCOR_BACKEND_AVAILABLE environment variable.
Estimated scope: 2-3 test files, 400-600 lines.

**Notes**:

CAN-HIGH-004; HIGH priority post-release item.

### JR-ML-API-068 — **Recommendation**: Add a startup sweep that removes stale `juniper_train_*` blocks from `/dev/shm`.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 188-217)

**Detail**:

#### 1.4.1 Shared Memory Block Leaks

**Notes**:

[v3 brief repaired from cited content; was: '1.4 Shared Memory and Multiprocessing Issues']

### JR-ML-DEP-035 — Recommendation**: Continue with direct URL configuration (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`). Docker Compose DNS will handle….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 616-627)

**Detail**:

**Recommendation**: Continue with direct URL configuration (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`). Docker Compose DNS will handle discovery automatically when contai

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Discovery Approach Evaluation']

### JR-ML-API-069 — Recommendation**: LOW PRIORITY — the 5-second poll will pick it up. Can be addressed as part of OI-2 (WebSocket push) which provides a more….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 489-499)

**Detail**:

**Recommendation**: LOW PRIORITY — the 5-second poll will pick it up. Can be addressed as part of OI-2 (WebSocket push) which provides a more comprehensive solution.

**Notes**:

[v3 brief repaired from cited content; was: 'Fix']

### JR-ML-TEST-041 — `reconnect_backoff_max` not validated against `reconnect_backoff_base`.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 317-324)

**Detail**:

- Sigmoid derivative evaluates `torch.sigmoid` twice per call

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-DATA-034 — `_recv_loop` catches bare `Exception` — swallows programming errors, pending futures time out

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 466-479)

**Detail**:

| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                | 🔴 Open            |

**Notes**:

[v4 brief repaired; was: '15.1 juniper-cascor-client']

### JR-ML-TRAIN-091 — `_recv_loop` catches bare `Exception` — swallows programming errors, pending futures time out.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 377-387)

**Detail**:

| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                | 🔴 Open            |

**Notes**:

[v4 brief repaired; was: '15.1 juniper-cascor-client']

### JR-ML-ARCH-267 — Refactor CascorControlStream with background recv task and correlation map.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-04-SDK-SET-PARAMS.md` (lines 254-272)

### JR-ML-OBS-119 — References `max-epochs-input`, old IDs, and `"Training Parameters"` label.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 503-522)

**Detail**:

| `test_convergence_layout.py`         | Update for removed `convergence-enabled-checkbox`, new radio group        |

**Notes**:

[v4 brief repaired; was: '8.4 Existing Tests Requiring Updates']

### JR-ML-TEST-042 — Regression analysis and remediation for model training defects.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-03_JUNIPER-ECOSYSTEM_REGRESSION-ANALYSIS.md` (lines 1-50)

### JR-ML-DEP-036 — Release Order Risks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 386-394)

### JR-ML-DATA-035 — Remediation Summary

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 95-108)

**Detail**:

1. Create retroactive git tags for v0.2.1 and v0.3.0

### JR-ML-DEP-037 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 156-169)

**Detail**:

1. Synchronize all version references to target release (0.6.0 recommended given post-0.5.0 features)

### JR-ML-API-070 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 209-221)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 265-280)

**Detail**:

1. Bump version to 0.4.0 (new public API surface)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-185 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 330-343)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 397-411)

**Detail**:

1. Write CHANGELOG v0.3.0 entry (WebSocket rewrite, auth_token rename, TLS support, etc.)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-CAN-TEST-036 — RemoteWorkerClient integration must have test coverage and verified integration path.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 184-197)

**Detail**:

RemoteWorkerClient integration referenced in architecture docs but has no test coverage or verified path.
Distributed training via remote workers is planned capability.
Estimated scope: 2-3 files, 300-500 lines; depends on RemoteWorkerClient in JuniperCascor.

**Notes**:

[v2 ARCH→TEST re-bucket] CAN-HIGH-005; HIGH priority post-release item.

### JR-ML-TOOL-044 — Remove 9 stale local import traceback statements from cascade_correlation.py by uncomenting top-level import at line 64.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (lines 3568-3580)

**Detail**:

CLN-CC-03: 9 local `import traceback` statements scattered in cascade_correlation.py
across lines 2270, 2804, 3775, 3840 and other files. Consolidate via uncommented
line 64 top-level import. Effort: 30 minutes.

### JR-CAN-DOC-007 — Remove commented-out imports across codebase.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 164-164)

**Detail**:

Issue 3.2.5: Commented imports clutter code. Remove or restore with rationale.

### JR-ML-TOOL-045 — Remove committed .ipynb_checkpoints directories from repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (lines 3590-3600)

**Detail**:

CLN-CC-12: Jupyter notebook checkpoint directories committed to repository in
src/cascade_correlation/.ipynb_checkpoints/, src/candidate_unit/, src/
These should be in .gitignore. Effort: 10 minutes.

### JR-ML-API-071 — Remove `COPY conftest.py .` — conftest.py is already inside `tests/` which is copied on line 29.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 243-273)

**Detail**:

**2.6.1 Fix Makefile variables** (`Makefile:70-72`):

**Notes**:

[v3 brief repaired from cited content; was: '2.6 juniper-deploy: Makefile & Dockerfile Fixes']

### JR-CAN-UI-032 — Remove dead _create_candidate_pool_display from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 160-160)

**Detail**:

Issue 3.2.1: Dead code left in MetricsPanel. Remove or document why retained.
File: src/frontend/components/metrics_panel.py

**Notes**:

[v2 ARCH→UI re-bucket]

### JR-CAS-ARCH-012 — Remove direct absolute path hardcoding that breaks on non-development machines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 142-146)

**Notes**:

Use relative paths or environment-relative configuration.

### JR-CAS-ARCH-013 — Remove duplicate snapshot_counter initialization in _init_network_parameters.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 396-408)

**Detail**:

Lines 530 and 548: self.snapshot_counter = 0 appears twice. Second is redundant.

### JR-ML-ARCH-268 — Remove module-level sys.path.append in cascade_correlation.py:69.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (lines 3600-3610)

**Detail**:

CLN-CC-13: sys.path manipulation at module level in cascade_correlation.py:69
is an anti-pattern. Refactor to use proper imports or package structure.

### JR-CAN-ARCH-006 — Remove or deprecate legacy TrainingMetricsComponent.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 163-163)

**Detail**:

Issue 3.2.4: TrainingMetricsComponent appears unused. Verify no references
and remove, or document deprecation plan and mark with DeprecationWarning.

### JR-CAN-TRAIN-010 — Remove orphaned candidate callbacks from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 161-161)

**Detail**:

Issue 3.2.2: Callbacks in MetricsPanel that reference removed candidate display.
Remove or reconnect to active candidate pool UI.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-ARCH-014 — Remove undeclared global variable shared_object_dict from _train_candidate_unit.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 351-363)

**Detail**:

Line 2300: global shared_object_dict declared but never defined anywhere. Accessing
raises NameError. Remnant from earlier design. Remove global declaration and related
dead code.

### JR-CAN-TEST-037 — Remove || true suppression from Bandit security scan in CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 150-155)

**Detail**:

ci.yml line 412: bandit || true suppresses security issues silently. Security should not fail silently.

**Notes**:

Category G: Security scan gap; best practices violation

### JR-ML-OBS-120 — Removed callback**: `handle_parameter_changes` - returns `dash.no_update` unconditionally, only logs. Logging can move to….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 197-214)

**Detail**:

**Removed callback**: `handle_parameter_changes` - returns `dash.no_update` unconditionally, only logs. Logging can move to `track_param_changes`.

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Callback Summary']

### JR-ML-UI-062 — Renamed to `nn-growth-convergence-threshold-input`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 84-99)

**Detail**:

## 3. Constants Changes (`canopy_constants.py`)

**Notes**:

[v4 brief repaired; was: '2.4 Removed Component IDs']

### JR-CAS-ARCH-015 — Replace "or" fallback chains with explicit None checks for falsy parameter values.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 411-423)

**Detail**:

Patterns like `learning_rate or _CONSTANT` fall through when config value is 0 or 0.0
(falsy). Incorrect for parameters where 0 is valid. Fix: use explicit
`if self.config.learning_rate is not None:` checks.

### JR-ML-OBS-121 — Replace `Dict[str, Any]` returns in `BackendProtocol` with TypedDicts or dataclasses:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 619-649)

**Detail**:

**Effort**: 3-5 days | **Repo**: juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '6.1 P5-RC-18: Typed Backend Contract']

### JR-CAS-TEST-016 — Replace hardcoded absolute paths in test files with dynamic resolution.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 57-62)

**Detail**:

TST-003: test_quick.py:9, test_final.py:9, test_cascor_fix.py:9, test_p1_fixes.py:171
contain hardcoded absolute paths. Replace with os.path.dirname(__file__) resolution.

### JR-CAS-TEST-017 — Replace mock-only tests with actual integration tests exercising real source code.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 57-62)

**Detail**:

TST-002: 67+ tests in test_log_config_coverage.py mock-only, not exercising real code.

### JR-CAS-ARCH-016 — Replace os._exit() with sys.exit() in main.py for proper cleanup handling.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 486-498)

**Detail**:

Lines 142,145: os._exit(1) bypasses cleanup handlers, finally blocks, atexit functions.
sys.exit() should be preferred.

### JR-CAS-ARCH-017 — Replace Path truthiness checks with explicit None checks.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 394-398)

**Detail**:

Path objects are always truthy even for empty strings. Use 'if x is None' instead of 'or' fallback patterns (lines 3015, 3096, 471).

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

### JR-ML-DATA-036 — **Repositories**: juniper-data, juniper-data-client

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 381-388)

**Detail**:

**Repositories**: juniper-data, juniper-data-client

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Generator Name Mismatch']

### JR-ML-SEC-186 — **Repositories**: juniper-data, juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 217-256)

**Detail**:

**Repositories**: juniper-data, juniper-deploy

**Notes**:

[v3 brief repaired from cited content; was: '1.5 Security Concerns']

### JR-ML-SEC-187 — `RequestBodyLimitMiddleware` relies solely on `Content-Length` header — bypassable with chunked encoding.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 427-459)

### JR-ML-SEC-188 — Requires CASCOR_SERVICE_URL or explicit demo mode.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 265-292)

**Detail**:

- **Strength**: Self-contained, handles env setup

**Notes**:

[v3 brief repaired from cited content; was: '3.4 Individual Application Startup Scripts']

### JR-ML-OBS-122 — Requires JuniperCascor and JuniperData to be running and healthy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 342-388)

**Detail**:

- Simulates realistic training lifecycle: idle → training → paused → complete

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Purpose and Analysis of Current Modes']

### JR-ML-TRAIN-092 — Residual Variance Collapse: address residual variance collapse in training.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-09-RESIDUAL-VARIANCE-COLLAPSE.md` (lines 1-46)

### JR-ML-OBS-123 — Resolve duplicated observability types (DependencyStatus, ReadinessResponse) across repos.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md` (lines 1-50)

**Notes**:

Establish shared observability library.

### JR-ML-UI-063 — Resolved**: Previously, `juniper_plant_all.bash` used `/opt/miniforge3/envs/JuniperCanopy/bin/python` for all services. Fixed in commit….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 434-444)

**Detail**:

**Resolved**: Previously, `juniper_plant_all.bash` used `/opt/miniforge3/envs/JuniperCanopy/bin/python` for all services. Fixed in commit `03aec86` — each service

**Notes**:

[v3 brief repaired from cited content; was: '7.3 Conda Environment Mapping']

### JR-ML-WS-156 — REST fallback cadence during disconnect = 1 Hz.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 54-54)

**Notes**:

Settled position C-17 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-124 — Retirement procedure: `git mv notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md notes/legacy/` in a doc-only PR; leave a tombstone….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 388-409)

**Detail**:

- A successor tracker (e.g. `POST_METRICS_MON_TRACKER_2026-09-01.md` for a 2026-Q3 program close) supersedes it.

**Notes**:

[v3 brief repaired from cited content; was: '4.3 When the tracker itself can be retired']

### JR-ML-UI-064 — `RETRY_ALLOWED_METHODS` includes `POST`/`DELETE` — retrying mutations can cause duplicates. Currently safe (server is idempotent) but should.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 229-239)

**Detail**:

| ID       | Severity   | File:Line             | Description

**Notes**:

[v4 brief repaired; was: '4.2 Code Quality']

### JR-ML-OBS-125 — return {}          # <-- BUG: overwrites store with empty dict.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 111-142)

**Detail**:

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-WS-157 — Ring-bound enforced in the handler, NOT the drain callback.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 56-56)

**Notes**:

Settled position C-19 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-269 — RISK: Correctness: no seq gaps.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 147-148)

### JR-ML-TRAIN-093 — RISK: Correctness: no state loss.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-270 — RISK: Criterion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 143-144)

### JR-ML-OBS-126 — **Risk**: Low-Medium. systemd is well-understood, but conda integration adds complexity.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 564-591)

**Detail**:

Standardize on systemd user services for host-mode and enhance the juniper-deploy Makefile for container mode. Remove the bash orchestration scripts.

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Approach C: systemd-First + Makefile Enhancement']

### JR-ML-ARCH-271 — RISK: Observability: full pipe.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 149-150)

### JR-ML-ARCH-272 — RISK: **P0: polling eliminated**.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 145-146)

### JR-ML-ARCH-273 — RISK: Recovery: kill switches work.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 150-151)

### JR-ML-WS-158 — RISK: Security: CSWSH closed.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-274 — ROBUST-01: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4574-4597)

### JR-ML-API-072 — Round-trip: apply -> state -> verify values match.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 492-503)

**Detail**:

| `DemoMode.apply_params()` accepts all new params  | Backend integration |

**Notes**:

[v4 brief repaired; was: '8.3 Integration Tests']

### JR-DCL-TEST-001 — Run full test suite and pre-commit hooks after constants refactor to validate no behavioral changes.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 52-69)

**Detail**:

After completing constants refactor (dcl-010 through dcl-013), must run: (1) Full test suite with
pytest tests/ -v, (2) Pre-commit hooks with pre-commit run --all-files, (3) Verify each generator
(spiral, xor, circle, moon) with default parameters to ensure outputs match pre-refactor results.

### JR-CAS-ARCH-018 — Run mypy and categorize type errors, then gradually increase strictness.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 514-529)

**Detail**:

Type errors present. Sub-tasks: run mypy, categorize errors, fix critical errors,
gradually increase strictness, remove continue-on-error from CI.

### JR-ML-UI-065 — Same color support, error handling, resource monitoring.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 184-195)

**Detail**:

**New file**: `juniper-data/scripts/juniper-data-ctl`

**Notes**:

[v3 brief repaired from cited content; was: '5.3 juniper-data-ctl (Step 2.4)']

### JR-DAT-OBS-006 — SARIF upload must fail on error, not continue-on-error.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 70-71)

**Notes**:

INF-004 MEDIUM (P2). ci.yml:320.

### JR-ML-WS-159 — SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 41-41)

**Notes**:

Settled position C-04 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-073 — **Secret name/path mismatch**: Top-level `secrets` defines `juniper_data_api_key` (singular) but service env `JUNIPER_DATA_API_KEYS_FILE` po.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 260-272)

**Detail**:

| DD-DC-01 | **High**   | **Secret name/path mismatch**: Top-level `secrets` defines `juniper_data_api_key` (singular) but service env `JUNIPER_DATA_API_KEYS_FILE` points to `/run/secrets/juniper_data_api_k

**Notes**:

[v4 brief repaired; was: '5.1 Docker Compose Issues']

### JR-ML-SEC-189 — `secrets/` directory on disk (gitignored properly).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 281-292)

**Detail**:

| DD-SEC-02 | **Medium** | Cascor port bound to 0.0.0.0 (see DD-DC-04).        |

**Notes**:

[v4 brief repaired; was: '5.3 Security']

### JR-ML-DEP-038 — Security benefit**: JuniperCanopy cannot directly reach JuniperData on the `backend` network. All data requests from Canopy go through….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 1040-1240)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 3:']

### JR-ML-SEC-190 — Security Concerns.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 89-95)

**Detail**:

- `kill_all_pythons.bash`: Dangerous — kills all Python processes system-wide with `sudo kill -9`

### JR-ML-API-074 — `self.clockwise = clockwise or self.clockwise or DEFAULT` — falsy `False`/`0` values silently overridden.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 107-118)

**Detail**:

| BUG-CC-01 | **MEDIUM** | `create_topology_message()` is dead code — topology changes never broadcast via WS | `src/api/websocket/messages.py:72`                                                | Defined and exported but zero production callers. Only used in tests

**Notes**:

[v4 brief repaired; was: '5.1 juniper-cascor']

### JR-ML-SEC-191 — Serialization & Validation (v3.0.0).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 337-348)

### JR-ML-WS-160 — server_instance_id = programmatic key; server_start_time = advisory only.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 43-43)

**Notes**:

Settled position C-06 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-192 — **Service file**: `juniper-canopy/scripts/juniper-canopy.service`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 243-265)

**Detail**:

**Service file**: `juniper-canopy/scripts/juniper-canopy.service`

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Current State: systemd (juniper-canopy only)']

### JR-ML-API-075 — Service Inventory.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 59-67)

**Detail**:

| **JuniperCascor** | 8200 | `python src/server.py`   | FastAPI + uvicorn        | Pydantic Settings (`JUNIPER_CASCOR_*` env vars)     |

### JR-ML-OBS-127 — Service mode populates parameter values with internal defaults first — UI shows incorrect values for params cascor doesn't expose.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 283-298)

**Detail**:

| CN-01 | **Medium** | `dashboard_manager.py`  | 346–349        | `_api_base_url` hardcoded to `127.0.0.1` — Dash REST callbacks break in Docker/remote deployments                                 |

**Notes**:

[v4 brief repaired; was: '2.2 juniper-canopy']

### JR-ML-OBS-128 — Service Topology.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 37-59)

**Detail**:

│   Uses:             │     REST         │    Uses:             │

### JR-ML-SEC-193 — Service-specific metric inventory (7 metrics):.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 163-193)

**Detail**:

| `/metrics` URL | `http://juniper-canopy:8050/metrics` |

**Notes**:

[v3 brief repaired from cited content; was: '3.3 juniper-canopy']

### JR-CAN-API-035 — ServiceBackend.get_status() returns nested training status but dashboard expects flat keys (is_running, is_paused, phase, current_epoch, hidden_units).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 303-328)

**Detail**:

get_status() returns nested cascor structures. Must add _normalize_status_response() that transforms state_machine.status (title case) to is_running/is_paused/completed/failed boolean flags with epoch/hidden_units extraction.

**Notes**:

Status bar works via /api/status endpoint transformation; inconsistent when backend.get_status() called directly.

### JR-ML-PERF-023 — `ServiceDown` suppresses `HighErrorRate*` / `HighLatency*` for the same.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 569-574)

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Inhibit rules']

### JR-ML-TOOL-046 — Setup MCP server for Claude integration: Slack, Gmail, Google Calendar adapters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md` (lines 1-50)

### JR-ML-DATA-037 — Several `CascorServiceAdapter` methods catch only `JuniperCascorClientError`, which would miss `AttributeError`, `TypeError`, or other…

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 501-505)

**Detail**:

Several `CascorServiceAdapter` methods catch only `JuniperCascorClientError`, which would miss `AttributeError`, `TypeError`, or other unexpected exceptions. This was the original vector for the dataset display bug (RC-2).

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-SEC-194 — Should be pinned (e.g., `redis:7.4.2-alpine`) for reproducible builds.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 373-390)

**Detail**:

**M-JDP-1: `redis:7-alpine` floating minor version tag**

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-ML-UI-066 — `--slient` typo in `wake_the_claude.bash:108` (should be `--silent`).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 78-89)

**Detail**:

- `--slient` typo in `wake_the_claude.bash:108` (should be `--silent`)

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-DAT-TEST-009 — Slow test job must be scheduled separately for integration and performance tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 69-70)

**Notes**:

INF-003 MEDIUM (P2).

### JR-CAN-SEC-011 — Snapshot endpoints must sanitize names and confine paths to prevent directory traversal attacks.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` (lines 53-95)

**Detail**:

CRIT-001 vulnerability: /api/v1/snapshots endpoints allow path traversal via ../../ and URL-encoded sequences.
Remediation: Add _sanitize_snapshot_name() with regex ^[a-zA-Z0-9_-]+$; verify resolved path stays within _snapshots_dir.

**Notes**:

CODE_REVIEW_ANALYSIS v0.4.0; path sanitization + path confinement (defense in depth) recommended.

### JR-ML-OBS-129 — Source of truth files (with current `origin/main` SHA).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 764-787)

**Detail**:

- `juniper-data/juniper_data/api/observability.py` (juniper-data `88149bf`)

### JR-ML-OBS-130 — **Source-of-truth:** `juniper-deploy/alertmanager/alertmanager.yml` (154 lines).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 513-539)

**Detail**:

Three ServiceMonitor templates: `data-servicemonitor.yaml`,

**Notes**:

[v3 brief repaired from cited content; was: '8.2 Kubernetes (`juniper-deploy/k8s/helm/juniper/templates/*']

### JR-ML-SEC-195 — **Source-of-truth:** `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 257-276)

**Detail**:

`juniper-data/juniper_data/api/observability.py:72` and is **not**

**Notes**:

[v3 brief repaired from cited content; was: '4.4 MetricsAuthMiddleware confinement']

### JR-ML-TRAIN-094 — Spiral Complexity: limit spiral depth and complexity growth.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-03-SPIRAL-COMPLEXITY.md` (lines 1-50)

### JR-ML-UI-067 — `src/conf/app_config.yaml` + `${VAR:default}` substitution.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 655-663)

**Detail**:

| **JuniperCanopy** | YAML config + env vars  | `src/conf/app_config.yaml` + `${VAR:default}` substitution |

**Notes**:

[v4 brief repaired; was: 'Current State']

### JR-ML-DOC-009 — Stabilize CI documentation link validation by implementing cross-repo link classification and worktree directory exclusion.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-07_JUNIPER-ECOSYSTEM_CROSS-REPO-LINK-RESOLUTION-PROPOSAL.md` (lines 70-175)

**Detail**:

DEVELOPER_CHEATSHEET.md has 124 broken cross-repo links in CI:
- 107 Category A: cross-repo relative links (../juniper-data/..., etc)
- 12 Category B: self-referencing cross-repo (../juniper-ml/...)
- 5 Category C: missing intra-repo files
- 1 Category D: false-negative deep link

Phase 1: Implement --cross-repo flag with skip/warn/check modes; exclude .claude/worktrees from scanning.

**Design**:

Approach 1A: Add --cross-repo flag with three modes:
- skip (default in CI): skip cross-repo links, log count
- warn: report as warnings (non-blocking)
- check: validate as normal (for local with all repos)

_ECOSYSTEM_REPOS hardcoded set with 8 known repos.
_CROSS_REPO_PATTERN regex matches patterns.

**PRs**: juniper-ml PR

**Notes**:

Recommend Phase 1: CI stabilization with --cross-repo skip.
Phase 2: ecosystem-root discovery with fallback.
Phase 3: documentation content cleanup (Approach 2A hybrid links).

### JR-ML-SEC-196 — State machine enters irrecoverable terminal state after FAILED or COMPLETED without enforced reset.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 186-227)

### JR-ML-UI-068 — Step 2: Validate Existing Fixes.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 70-95)

**Detail**:

| B-5.1 | `_apply_parameters_handler` stores `"enabled" in (conv_enabled or [])` → correct boolean. No continuous sync. |

### JR-ML-OBS-131 — Step 4: Commit Strategy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 146-154)

**Detail**:

1. **Phase 6 training improvements**: Constants, demo_mode algorithm changes, demo_backend, phase6 tests

### JR-ML-SEC-197 — Step 5: Update Plan Document.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 154-162)

**Detail**:

Add Phase 5.3 section to `notes/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` documenting:

### JR-ML-API-076 — Store starts empty; `init_params_from_backend` repopulates on each page load.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 439-448)

**Detail**:

| `/api/state` response         | Old fields missing               | Always provide defaults via `.get()` with `TrainingConstants` fallbacks      |

**Notes**:

[v4 brief repaired; was: '7.4 Backward Compatibility']

### JR-ML-SEC-198 — **Strength**: Matches documented security model; prevents container internet access on backend/data.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 73-101)

**Detail**:

**File**: `docker-compose.yml` lines 494-503

**Notes**:

[v3 brief repaired from cited content; was: '1.4 juniper-deploy: Network Isolation']

### JR-ML-SEC-199 — **Strengths of A**: Preserves functionality, standard security pattern, configurable per deployment.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 41-63)

**Detail**:

**Root cause**: `csv_import/generator.py:80-87` passes `file_path` directly to `Path()`.

**Notes**:

[v3 brief repaired from cited content; was: '1.2 juniper-data: CSV Import Path Traversal Fix']

### JR-ML-OBS-132 — **Strengths**: Comprehensive fix, prevents the same class of bug across all tabs.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 152-202)

**Detail**:

#### Approach A: Return `dash.no_update` on error (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

### JR-ML-UI-069 — **Strengths**: Fixes demo mode topology to match CasCor architecture.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 389-431)

**Detail**:

#### Approach A: Add cascade connections to demo backend (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

### JR-ML-SEC-200 — Substantial features (systemd support, worker integration, startup/shutdown scripts, worktree cleanup v2) are completely undocumented in….

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 53-67)

**Detail**:

**H-ML-1: CI dependency-docs job references wrong path** (`ci.yml:244`)

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-CAS-TRAIN-031 — Support multiple optimizer types via configuration (Adam, SGD, RMSprop, AdamW).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 749-773)

### JR-CAN-ARCH-007 — Systemic architectural issue: no canonical backend contract across demo and service modes (ISS-17).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 642-664)

**Detail**:

ISS-17 SYSTEMIC. BackendProtocol returns Dict[str, Any] for all methods with no shared type definition, TypedDict, or dataclass enforcing structurally identical output between demo and service modes. Mode-dependent schemas: metrics history (nested vs flat), current metrics (nested vs flat), topology (graph-oriented vs weight-oriented), dataset (includes data arrays vs metadata only), state sync metrics (N/A vs raw cascor). Status bar works correctly because both backends happen to produce matching flat output; all other mismatches exist because no mechanism detects/prevents them. Root cause enabling ISS-01, ISS-04, ISS-05, ISS-06, ISS-12.

**Design**:

Define shared BackendProtocol with Pydantic models or TypedDicts enforcing identical output shapes across demo/service modes. Add runtime validation layer detecting format divergence. Establish contract tests verifying both backends produce identical data shapes.

**Notes**:

Identified by v4, v6, v7. Architectural root cause hierarchy shows ISS-17 at apex with multiple child issues.

### JR-ML-DEP-039 — Tally by severity.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 412-421)

### JR-ML-TRAIN-095 — Tanh Saturation: address tanh saturation issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-06-TANH-SATURATION.md` (lines 1-38)

### JR-ML-TRAIN-096 — Task 3 (Topology).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 366-374)

**Detail**:

- Exact lines confirmed: 582 and 611 in cascor_service_adapter.py

### JR-ML-SEC-201 — `TaskDistributor` dual-path execution is serial, not concurrent.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 931-951)

### JR-CAN-TEST-038 — Test non-test files exist in test directory; test_yaml.py, test_config.py, test_dashboard_init.py, test_and_verify_button_layout.py, implementation_script.py should be moved or removed.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

**Detail**:

Five non-test files found in test directory that should either be moved to appropriate location or deleted. Cleans up test structure.

**Notes**:

Identified in test audit.

### JR-DAT-TEST-010 — Test suite CI/CD enhancement plan (Claude version).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

### JR-CAN-TEST-039 — Test suite contains 9 false-positive tests (assert True only) masking actual test failures.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 85-130)

**Detail**:

False positives in test_button_responsiveness.py (4 instances), test_button_state.py (1), test_metrics_panel_coverage.py (1), test_dashboard_manager.py (1), test_config_refactoring.py (1), test_candidate_visibility.py (1). Each contains only assert True statement.

**Notes**:

Must be replaced with real test assertions or removed.

### JR-CWK-TEST-003 — Test warning elimination: suppress DeprecationWarnings in test_worker.py (expected legacy API tests), RuntimeWarnings for unawaited CascorWorkerAgent coroutines, enforce warnings-as-errors baseline in pyproject.toml.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 107-144)

**Detail**:

DeprecationWarnings (23): CandidateTrainingWorker.__init__() emits at worker.py:326; test_worker.py exercises deprecated legacy API. Solution: module-level pytestmark filterwarnings in test_worker.py. RuntimeWarnings (3): unawaited CascorWorkerAgent.run() coroutines during mock-based test cleanup. Solution: targeted filterwarnings in pyproject.toml for coroutine pattern. Baseline: filterwarnings = ["error", ...] in pytest config treats all warnings as errors by default with explicit exceptions for known, intentional warnings. Prevents silent warning accumulation; new unexpected warnings cause test failures.

### JR-ML-SEC-202 — `test_health_enhanced.sh` uses `curl` while other scripts use python3 urllib. Inconsistent dependency.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 311-324)

**Detail**:

| DD-SCR-01 | **Low**  | `test_health_enhanced.sh` uses `curl` while other scripts use python3 urllib. Inconsistent dependency. |

**Notes**:

[v4 brief repaired; was: '5.6 Scripts/Automation']

### JR-ML-SEC-203 — Tests named for `grow_network` testing actually bypass it entirely.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1040-1058)

### JR-ML-UI-070 — **Tests**: 88 passed (60 + 11 + 17 Python) + 1 bash regression.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 41-48)

**Detail**:

- **Version**: 0.3.0 (pyproject.toml)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-DAT-TEST-011 — TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN for juniper-data.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 1-50)

### JR-ML-TRAIN-097 — The cascor state machine returns UPPERCASE state names (`"STOPPED"`, `"STARTED"`), while `TrainingState.get_state()` returns title-case….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 402-409)

**Detail**:

**Repositories**: juniper-cascor, juniper-cascor-client

**Notes**:

[v3 brief repaired from cited content; was: '3.3 State Name Inconsistency']

### JR-ML-API-077 — The constants in all three packages include explicit documentation of the alignment requirement.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 388-402)

**Detail**:

**Repositories**: juniper-cascor, juniper-cascor-client, juniper-cascor-worker

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Wire Protocol Alignment']

### JR-ML-API-078 — The core CR-006 issue has been SUBSTANTIALLY ADDRESSED since the prior analysis. Verification against the current codebase shows:.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 82-132)

**Detail**:

**Severity**: S1 (largely resolved) | **Effort**: Small (0.5-1 day) | **Repos**: juniper-cascor, juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '3.1 CR-006: Verify `max_iterations` End-to-End Implementatio']

### JR-ML-UI-071 — The current topology visualization is exclusively **node-centric** — showing nodes and their connections as a graph. A **weight-centric**….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 532-536)

**Detail**:

The current topology visualization is exclusively **node-centric** — showing nodes and their connections as a graph. A **weight-centric** view would display the raw weight arrays from CasCor, showing the actual numerical structure of the network.

**Notes**:

[v3 brief repaired from cited content; was: 'Description']

### JR-ML-UI-072 — The `get_dataset_data()` method (line 733) already demonstrates the correct pattern: `except Exception as e` with a warning log. Apply the….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 522-532)

**Detail**:

The `get_dataset_data()` method (line 733) already demonstrates the correct pattern: `except Exception as e` with a warning log. Apply the same pattern to the methods listed above that handle data transformation (especially `get_decis

**Notes**:

[v3 brief repaired from cited content; was: 'Fix']

### JR-ML-OBS-133 — The `juniper-deploy` repository provides Docker Compose orchestration with 5 profiles:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 292-313)

**Detail**:

Profile: observability (additive)

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Architecture Overview']

### JR-ML-DATA-038 — The `JuniperServiceScrapeDown` alert similarly uses `up == 0` to detect

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 483-496)

**Detail**:

| `CascorPendingTasksSaturated` (`alert_rules.yml:1050`) | `juniper_cascor_pending_tasks` | The guard was originally placed because the gauge had not yet been bridged from the cascor coordinator to Pr

**Notes**:

[v3 brief repaired from cited content; was: '7.4 `absent_over_time(...) == 0` inertness guards']

### JR-ML-DEP-040 — There is no unified multi-service startup mechanism. Each service is started independently:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 97-116)

**Detail**:

There is no unified multi-service startup mechanism. Each service is started independently:

**Notes**:

[v3 brief repaired from cited content; was: '2.1 Current State']

### JR-ML-API-079 — Thin wrapper that operates on the target and all three services:.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 298-310)

**Detail**:

**New file**: `juniper-ml/scripts/juniper-all-ctl`

**Notes**:

[v3 brief repaired from cited content; was: '5.7 juniper-all-ctl (Step 2.6)']

### JR-ML-UI-073 — This document was produced by cross-referencing 34 source documents across the Juniper ecosystem:.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 488-504)

**Detail**:

| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker      | 🔴 Open |

**Notes**:

[v3 brief repaired from cited content; was: '15.3 juniper-cascor-worker']

### JR-ML-SEC-204 — TOCTOU gap in `_check_stale_workers` between snapshot and deregistration.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 541-571)

### JR-ML-UI-074 — `_toggle_cn_multi_candidate_subgroup_handler` checkbox unchecked disables all.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 471-492)

**Notes**:

[v4 brief repaired; was: '8.2 Unit Tests - Callback Handlers']

### JR-ML-OBS-134 — Top offenders: `test_dashboard_manager.py` (17), `test_config_refactoring.py` (17), `test_decision_boundary.py` (14).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 134-145)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 118-130)

**Detail**:

| BUG-CN-01 | **HIGH**   | `_stop.clear()` race in `_perform_reset()` — outside lock      | `src/demo_mode.py:1617`             | Second call site at L1617 is outside the lock block (lock only covers L1615-1616)                                    |

**Notes**:

[v4 brief repaired; was: '5.2 juniper-canopy']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-TRAIN-098 — Topology updates after `cascade_add` are delayed by up to 5 seconds.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 245-251)

**Notes**:

[v3 brief repaired from cited content; was: 'Consequence']

### JR-ML-OPS-009 — Total effort: 13.5 expected engineering days / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 73-73)

**Notes**:

Settled position C-36 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-099 — TQ-01: 10+ Tests with No Assertions (cascor).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4775-4786)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-275 — TQ-02: 149 `time.sleep` Calls in canopy Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4789-4800)

### JR-ML-ARCH-276 — TQ-03: Worker Config Validation Tests with No Assertions.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4803-4814)

### JR-ML-TRAIN-100 — TQ-04: 139 `hasattr` Guards in cascor Tests.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4817-4821)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-277 — TQ-05: 10 Unit Tests Import httpx (Integration-Level).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4824-4835)

### JR-ML-DEP-041 — Training control (called from `/ws/control` handler and Dash callbacks):.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 2348-2548)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 5:']

### JR-CAN-OBS-015 — Training History must record dataset swap as first-class event with timestamp, before/after config, and architecture changes.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 41-42)

**Detail**:

F2.7: History shall record swap with timestamp + before/after cfg. F2.8: Snapshot captured at swap point. F2.9: Replay must handle sessions with swaps.

**Notes**:

Persistence schema TBD during review.

### JR-CAN-TRAIN-011 — TrainingStateMachine must protect all state mutations with threading.Lock to ensure thread safety.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 177-181)

**Detail**:

HIGH-015: Add threading.Lock on all state mutations AND getters (partial fix in prior audit lacked lock on getters).
Independent of R5-01; backend state management concern.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; partially remediated prior; full coverage required.

### JR-ML-OBS-135 — Trigger / due date. No fixed date — fires off CALIB-01 ratification, expected mid- to late-June 2026.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 97-124)

**Detail**:

**Severity:** P2 · **Owner repo:** juniper-cascor · **Status:** open (depends on CALIB-01)

**Notes**:

[v3 brief repaired from cited content; was: '3.2 R5.1c-BUCKETS — Cascor sub-ms bucket re-evaluation']

### JR-ML-UI-075 — Two collapsible subsections with 22 total input components, radio button groups for mutually exclusive options, conditional enable/disable….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 31-39)

**Detail**:

## 2. Component ID Registry

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: 'Target State']

### JR-ML-API-080 — Type-safe, validated configuration.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 663-713)

**Detail**:

The mixed approach (Pydantic Settings for two services, YAML for one) creates inconsistency. All three services are FastAPI-based, so Pydantic `BaseSettings` is the natural fit.

**Notes**:

[v3 brief repaired from cited content; was: 'Evaluation']

### JR-ML-UI-076 — UI Lock and Visualization: UI locking during training and visualization improvements.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CANOPY_PROPOSAL-08-UI-LOCK-AND-VISUALIZATION.md` (lines 1-45)

### JR-ML-SEC-205 — Unvalidated `params` dict in `TrainingStartRequest` passed as `kwargs` to `network.fit()`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 395-427)

### JR-CCL-DOC-013 — Update AGENTS.md and CHANGELOG.md documentation after hardcoded-values refactor completion.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 76-79)

**Notes**:

Documentation & release phase (MEDIUM priority)

### JR-DEP-OPS-002 — Update AGENTS.md with directory layout, security architecture, CI pipeline, network topology.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 29-143)

**Detail**:

Phase 2 (P1 priority) add missing major sections: directory layout, security architecture
(networks, container hardening, secrets), CI/CD pipeline (4 jobs, multi-repo checkout, pinned actions),
Docker Compose profiles (profile-to-service mapping), network architecture, Makefile targets.
Phase 3 complete existing sections: expand service ports table, key files table, dependency graph,
environment variables, essential commands. Phase 4 update metadata, add documentation index, testing architecture.

### JR-ML-API-081 — Update all broken existing tests.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 555-563)

**Detail**:

1. Update all broken existing tests

**Notes**:

[v4 brief repaired; was: 'Phase 5: Tests']

### JR-ML-TEST-043 — Update all tests; map `convergence_enabled` from `nn_growth_trigger == "convergence"`.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 414-423)

**Notes**:

[v4 brief repaired; was: '7.1 Breaking Changes']

### JR-ML-DEP-042 — Update juniper-ml extras version requirements to match released versions.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 375-386)

**Detail**:

- Update parent CLAUDE.md with new version numbers

**Notes**:

[v3 brief repaired from cited content; was: '5.3 Post-Release']

### JR-ML-DEP-043 — Update `org.opencontainers.image.version` to match release version.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 171-188)

**Detail**:

**2.2.1 n_spirals fallback** (`datasets.py:114`):

**Notes**:

[v3 brief repaired from cited content; was: '2.2 juniper-data: Code Fixes']

### JR-ML-OBS-136 — `_update_topology_store_handler()` in `dashboard_manager.py` returns `{}` when the REST poll fails, instead of `dash.no_update`. This empty….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 107-111)

**Detail**:

`_update_topology_store_handler()` in `dashboard_manager.py` returns `{}` when the REST poll fails, instead of `dash.no_update`. This empty dict flows into the NetworkVisualizer callback where the guard `topology_data.get("input_units", 0) == 0` evaluates to `True`, rendering an empty graph.

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-UI-077 — v1.0.0–v2.0.0 Primary Sources.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 504-513)

**Detail**:

| 1 | `JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md`  | `juniper-ml/notes/development/`     | 2026-04-17 | 91+ items from 16 source documents      |

### JR-ML-SEC-206 — V17/V18 cross-repo dispatch token setup: enable inter-repo CI workflows with OIDC trust.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_V17-V18-CROSS-REPO-DISPATCH-TOKEN-SETUP.md` (lines 1-50)

### JR-CAS-OBS-005 — Verify WebSocket responsiveness under load when training runs via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 870-874)

### JR-ML-SEC-207 — **Version**: 0.2.0 (documented in AGENTS.md; no formal release).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 343-350)

**Detail**:

- **Version**: 0.2.0 (documented in AGENTS.md; no formal release)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-ML-SEC-208 — **Version**: 0.2.1 | **Stack**: Docker Compose + Helm + Prometheus + Grafana + AlertManager.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 246-260)

**Detail**:

| DC-CI-01 | **Low**  | Security scan installs `.[dev]` (full dev deps) instead of minimal runtime. |

**Notes**:

[v3 brief repaired from cited content; was: '4.4 CI/CD']

### JR-ML-API-082 — **Version**: 0.3.2 (code) — but no git tag exists for v0.3.2.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 169-176)

**Detail**:

- **Version**: 0.3.2 (code) — but no git tag exists for v0.3.2

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-ML-DATA-039 — **Version**: 0.4.0 | **Python**: ≥3.12 | **Dependencies**: numpy≥1.24, requests≥2.28, urllib3≥2.0

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 206-220)

**Detail**:

| JD-CI-03 | **Low**    | CI workflow and `.pre-commit-config.yaml` headers say version `0.4.0` — stale. |

**Notes**:

[v3 brief repaired from cited content; was: '3.6 CI/CD']

### JR-ML-API-083 — **Version**: 0.5.0 (pyproject.toml) / 0.4.2 (**init**.py) / 0.4.0 (Dockerfile).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 108-115)

**Detail**:

- **Version**: 0.5.0 (pyproject.toml) / 0.4.2 (**init**.py) / 0.4.0 (Dockerfile)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-ML-SEC-209 — **Version**: 0.6.0 (unreleased hardcoded-values refactor on main) | **Python**: ≥3.12.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 142-159)

**Detail**:

| CW-CI-01   | **Low**    | CI tests 3.11-3.13, not 3.14 (Dockerfile uses python:3.14-slim).                                                 |

**Notes**:

[v3 brief repaired from cited content; was: '2.5 CI/CD & Dockerfile']

### JR-ML-OBS-137 — **Weaknesses**: Additional REST call for raw format, two stores to maintain.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 555-605)

**Detail**:

#### Approach A: Dual-store architecture (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

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

### JR-CAN-API-036 — WebSocket /ws/training connect-time message ordering is not atomic; initial_status/state messages can be preempted by background demo broadcasts.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 122-150)

**Detail**:

Handler sends connection_established, initial_status, state with await boundaries; client added to active_connections before all sends complete, allowing broadcast loop to inject metrics/state messages between. Enforce send ordering before client becomes visible to broadcasts.

**Notes**:

Currently mitigated on test side only; product-side ordering not enforced.

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

### JR-CAN-TEST-040 — WebSocket tests marked with requires_server must be converted to work with TestClient interface.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 213-232)

**Detail**:

Four WebSocket test groups currently skipped: test_websocket_training.py, test_websocket_control.py,
test_main_ws.py (subset), test_websocket_state.py (subset).
Convert to TestClient WebSocket interface for CI compatibility.
Estimated scope: 4 files, 200-300 lines modified.

**Notes**:

CAN-HIGH-007; HIGH priority post-release item; identified in TEST_SUITE_AUDIT.

### JR-ML-DOC-010 — When an item closes:.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 370-378)

**Detail**:

1. Remove its row from §2 (or flip the `Status` column to `closed (PR #N)` if you prefer to keep historical visibility).

**Notes**:

[v3 brief repaired from cited content; was: '4.1 How this tracker is updated as items close']

### JR-ML-OBS-138 — When `cascade_add` is received via WebSocket from CasCor, the Canopy adapter in `start_metrics_relay()` reacts by making a REST call to….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 207-215)

**Detail**:

When `cascade_add` is received via WebSocket from CasCor, the Canopy adapter in `start_metrics_relay()` reacts by making a REST call to CasCor's `/v1/network/topology` endpoint, transforms the result via `_transform_topology()`, and broadcasts it via Canopy's internal `websocket_manager.broadcast()`

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-ARCH-278 — When `cn-multi-candidate-checkbox` is unchecked (default), the entire sub-group must be disabled:.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 214-234)

**Detail**:

Note: Callback #9 (`toggle_cn_selection_inputs`) should also check the checkbox state and keep inputs disabled when the checkbox is unchecked, regardless o

**Notes**:

[v3 brief repaired from cited content; was: '4.5 Multi Candidate Sub-Group Enable/Disable']

### JR-ML-OBS-139 — Why This Causes the Blank After Hidden Unit Addition.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 142-152)

**Detail**:

When CasCor adds a hidden unit via `grow_network()`, there is a brief transient window where the network state is being reorganized (output weights resized, new unit installed). If the Canopy REST poll hits `/api/topology` during this window and receives a 503 (or timeout), the handler returns `{}`,

### JR-ML-API-084 — Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 77-77)

**Notes**:

Settled position C-40 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-078 — Work Unit 1: Worktree Developer Experience (HIGH).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 41-83)

**Detail**:

**Impact**: Unblocks all worktree-based development workflows

### JR-ML-API-085 — Work Unit 3: Pre-Existing Test Failures (MEDIUM) — IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 129-144)

**Detail**:

**Issues**: 3A (9 failing tests in `test_api_state_endpoint.py`)

### JR-ML-OBS-140 — Work Unit 5: Code Cleanup — Remove Redundant Inline Styles (LOW) — IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 161-201)

**Detail**:

Removed all 13 `style={"backgroundColor": "#f8f9fa"}` attributes from `dbc.CardHeader` instances across 4 files. The CSS rule `.card-header { background-color: var(--bg-secondary) !important;

### JR-ML-TRAIN-101 — Worker protocol constants (`MSG_TYPE_*`, `BINARY_FRAME_*`) must remain bit-identical to cascor's `MessageType(StrEnum)` in `protocol.py`.….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 349-353)

**Detail**:

Worker protocol constants (`MSG_TYPE_*`, `BINARY_FRAME_*`) must remain bit-identical to cascor's `MessageType(StrEnum)` in `protocol.py`. Wave 5 verified alignment, but **no automated CI check exists**. A cascor protocol change could silently break worker connectivity.

**Notes**:

[v3 brief repaired from cited content; was: '6.4 Medium: Protocol Constants Alignment is Manual']

### JR-ML-SEC-210 — Worker `worker_id` is client-supplied with no server-side validation or uniqueness enforcement.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 490-523)

### JR-ML-API-086 — Wrap `generator.generate()` in `asyncio.to_thread()` (PERF-01).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 452-468)

**Detail**:

| 10 | juniper-data          | Use `hmac.compare_digest()` for API key comparison (SEC-01)    |

**Notes**:

[v4 brief repaired; was: '8.3 Medium (Address in Next Sprint)']

### JR-ML-OBS-141 — ws-metrics-buffer store shape = {events, gen, last_drain_ms}.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 55-55)

**Notes**:

Settled position C-18 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-211 — ws_security_enabled=True (positive sense), NOT disable_ws_auth.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 64-64)

**Notes**:

Settled position C-27 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-279 — XREPO-01: Generator Name `"circle"` vs Server's `"circles"`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2509-2524)

### JR-ML-ARCH-280 — XREPO-02: 503 Not in `RETRYABLE_STATUS_CODES`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2571-2586)

### JR-ML-ARCH-281 — XREPO-03: No `FakeCascorControlStream` — Testing Gap for WS Control.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2589-2604)

### JR-ML-ARCH-282 — XREPO-04: Protocol Constants Alignment Is Manual.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2607-2629)

### JR-ML-ARCH-283 — XREPO-05: State Name Inconsistency — UPPERCASE vs Title-Case vs FSM Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2632-2646)

### JR-ML-ARCH-284 — XREPO-06: `epochs_max` Default Discrepancy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2649-2663)

### JR-ML-ARCH-285 — XREPO-07: `command()` vs `set_params()` Message Format Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2666-2681)

### JR-ML-ARCH-286 — XREPO-08: Three Distinct WS Message Formats.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2684-2692)

### JR-ML-ARCH-287 — XREPO-09: Client `create_dataset()` Missing `tags` and `ttl_seconds`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2695-2709)

### JR-ML-DATA-040 — XREPO-10: `FakeDataClient` Metadata Schema Diverges from Real Server

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2712-2726)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-ARCH-288 — XREPO-11: Client Retries Non-Idempotent Mutations (POST, DELETE).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2729-2743)

### JR-ML-ARCH-289 — XREPO-12: `y` Tensor Received but Never Used in Worker.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2746-2760)

### JR-ML-ARCH-290 — XREPO-13: Health Endpoint `status` Value Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2763-2771)

### JR-ML-ARCH-291 — XREPO-14: FakeClient State Constants Use Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2774-2789)

### JR-ML-ARCH-292 — XREPO-15: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2792-2800)

### JR-ML-ARCH-293 — XREPO-16: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2803-2818)

### JR-ML-ARCH-294 — XREPO-17: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2821-2836)

### JR-ML-DEP-044 — | Repo           | `pyproject.toml` | `AGENTS.md` header | File headers   |.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 353-363)

**Detail**:

| Repo           | `pyproject.toml` | `AGENTS.md` header | File headers   |

**Notes**:

[v4 brief repaired; was: '6.5 Low: Version Header Drift (Multiple Repos)']

### JR-ML-OBS-142 — │   cascade_add ───┼── broadcast ─┤── topology hint   │  ← count only, not full topology.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 472-492)

**Detail**:

## 6. Risk Assessment and Guardrails

**Notes**:

[v3 brief repaired from cited content; was: '5.3 Architecture Diagram: WebSocket Message Flow']

### JR-ML-TRAIN-102 — ✅ Complete (header version needs bump 0.3.0 → 0.4.0).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 374-381)

**Detail**:

| Hardcoded values refactor → `constants.py` | ✅ Complete (126 lines, 330 test constants)           |

**Notes**:

[v4 brief repaired; was: '7.1 juniper-cascor-client — All Planned Work ✅ COMPLETE']

### JR-ML-SEC-218 — [ ] `docker compose config` validates for all profiles.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 337-351)

**Detail**:

**Sequence**: After Phase 4 validation

**Notes**:

[v3 brief repaired from cited content; was: '4.4 Docker Validation (juniper-deploy)']

### JR-ML-ARCH-295 — [ ] **Task 5.1.1**: Remove misleading `import datetime as pd`.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md` (lines 242-263)
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md` (lines 241-262)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 5:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-06.md

---

[v3 brief repaired from cited content; was: 'Phase 5:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-02.md

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-TRAIN-105 — [ ] **Task 6.2.2**: Verify training starts and completes epoch 1+.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 190-220)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: 'Phase 6:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

### JR-ML-ARCH-296 — [x] **Status**: ✅ Fixed (verified 2026-04-03 — already removed).

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md` (lines 233-265)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 4:'] From JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md

### JR-CAN-DOC-008 — Add deprecation warnings to remaining legacy env validators.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 227-227)

**Detail**:

Issue 5.1.1: Legacy env var validators need deprecation warnings.
Use warnings.warn() to alert users of upcoming removal.

### JR-ML-API-089 — Add `GET /v1/dataset/data` endpoint.

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 341-348)

**Detail**:

| `src/api/lifecycle/manager.py` | Add `get_dataset_data()` method     |

**Notes**:

[v4 brief repaired; was: '9.2 juniper-cascor (Phase 4 only)']

### JR-DAT-DOC-002 — AGENTS.md must document current project structure, components, security, dependencies (15+ entries for components).

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 45-64)

**Notes**:

D-001 through D-050 catalogued. 5 CRITICAL issues (version, security, line length, directory, middleware).

### JR-CAN-OBS-016 — All print() statements must be replaced with logger.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 237-237)

**Detail**:

Issue 5.2.3: print() bypasses logging config. Replace with appropriate
logger.info/debug/warning calls throughout codebase.

### JR-CAN-TEST-041 — apply_params verify-roundtrip has no retry mechanism on stale reads, could surface as spurious user-facing errors.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 33-33)

**Detail**:

Verify logic does not retry stale reads; timing-sensitive assertion could fail intermittently. Add exponential backoff retry with max attempts.

**Notes**:

Risk of spurious test failures and user-facing errors.

### JR-CAN-WS-005 — Architectural fragility: WebSocket relay broadcasts unnormalized metric field names (ISS-11).

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 541-553)

**Detail**:

ISS-11 LOW. WebSocket relay loop (cascor_service_adapter.py:203-206) broadcasts cascor raw metrics messages without applying _normalize_metric(). CasCor sends loss/accuracy/validation_loss/validation_accuracy; REST path normalizes to train_loss/train_accuracy/val_loss/val_accuracy. Currently non-functional (dashboard doesn't consume WebSocket — ISS-03). Becomes active bug if ISS-03 addressed — REST and WebSocket paths would deliver metrics with different field names.

**Notes**:

[v2 ARCH→WS re-bucket] Identified by v4, v7. Latent until ISS-03 fixed.

### JR-CAN-LOCK-003 — Black code formatter must have py314 in target-version.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 230-230)

**Detail**:

Issue 5.1.4: pyproject.toml Black config needs py314 for Python 3.14 compatibility.
Add to target-version list.

### JR-CAN-API-037 — candidate_learning_rate parameter unmapped in canopy (accessible via cascor API but not UI) (ISS-16).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 627-639)

**Detail**:

ISS-16 LOW. CasCor TrainingParamUpdateRequest accepts candidate_learning_rate as updatable field, but no canopy parameter maps to it in _CANOPY_TO_CASCOR_PARAM_MAP. Users cannot view or modify candidate learning rate from dashboard; parameter accessible via direct cascor API calls only.

**Notes**:

Identified by v4 (unique finding).

### JR-CAS-TRAIN-033 — CasCor juniper-cascor bug: TrainingMonitor.current_phase never updated during training (ISS-08).

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 468-493)

**Detail**:

ISS-08 MODERATE (cross-repo). TrainingMonitor.current_phase initialized to "output" at juniper-cascor/lifecycle/monitor.py:111, never updated during training. When training enters candidate phase, TrainingLifecycleManager updates training_state and state_machine (manager.py:270) but NOT monitor.current_phase. Since metrics recorded via monitor.on_epoch_end() reads self.current_phase, all metrics history entries have phase="output" regardless of actual training phase. Result: phase-colored scatter plots show all data as "Output Training" (never "Candidate Training"); substring matching prevents candidate-phase color-coding.

**Design**:

Fix in juniper-cascor repository: update monitor.current_phase when LifecycleManager transitions phases.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Identified by v5 (unique finding). This is a juniper-cascor bug, not juniper-canopy bug. Fix must be applied in cascor repository.

### JR-CAN-LOCK-004 — CASCOR_SNAPSHOT_DIR env var must be migrated to JUNIPER_CANOPY_SNAPSHOT_DIR.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 229-229)

**Detail**:

Issue 5.1.3: Old env var still referenced. Support both for compatibility
but document migration path and plan removal date.

### JR-CAS-TRAIN-034 — Code cleanup deferred items: Roll concept removal, candidate factory refactor, 120-char line length, LogConfig params, logger TODOs, commented code.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 263-282)

**Detail**:

CASCOR-P1-008: Remove Roll concept in CandidateUnit. P3-001: Candidate factory refactor (_create_candidate_unit()). MED-014: Line length 120 characters. INT-P4-012: LogConfig.__init__ parameter naming. INT-P4-013: Logger TODO cleanup. INT-P4-014: Remove commented-out code blocks. INT-P4-015: Clean up "Original corrupted line" comments. INT-P4-016: Remove uuid import alias redundancy. ENH-009: Per-instance queue management. ENH-010: Process-based plotting. INT-P4-010/011: Multiprocessing metrics and fallback testing. All status: 🔵 DEFERRED for post-release.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CAN-TEST-042 — Codebase contains 60+ skipped tests using 'Method _X not exposed as public API' rationale, papering over real coverage gaps.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 34-34)

**Detail**:

60+ skips across h5py-related tests and internal-method probes. Indicates either test suite design issue or missing public API test coverage. Audit to determine if skips are justified or represent untested paths.

**Notes**:

Coverage gaps in h5py and internal method testing.

### JR-CAN-DOC-009 — Codecov build count assumption must be documented.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 254-254)

**Detail**:

Issue 5.4.4: Codecov configuration makes implicit assumptions about build
frequency. Document in README or config comments what build count limit is
set to and why.

### JR-CAN-LOCK-005 — CPU-only conda environment must be created for deployment without CUDA.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 231-231)

**Detail**:

Issue 5.1.5: Current environment assumes CUDA. Create environment-cpu.yml
with PyTorch CPU variant and document usage.

### JR-CAS-TEST-018 — Create end-to-end integration tests spinning up JuniperData and full pipeline.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 581-591)

**Detail**:

No automated integration tests spin up JuniperData and verify full pipeline (Cascor →
JuniperData → artifact → tensor conversion → training). All current tests use mocks.

### JR-CAN-API-038 — Dead parameter mapping: cn_training_iterations → candidate_epochs (unmapped by cascor) (ISS-15).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 608-624)

**Detail**:

ISS-15 LOW. Forward map at cascor_service_adapter.py:364 maps cn_training_iterations to candidate_epochs, but cascor API neither returns nor accepts candidate_epochs. CasCor get_training_params() returns 6 keys (none being candidate_epochs), TrainingParamUpdateRequest accepts 7 fields (none being candidate_epochs). Result: cn_training_iterations always shows default/stale value; parameter writes silently dropped.

**Design**:

Sub-issue ISS-15b: patience → nn_growth_convergence_threshold has semantic mismatch. patience is integer count (epochs to wait) but threshold implies float value (e.g., 0.001). Parameter panel displays integer patience under "Growth Convergence Threshold" label.

**Notes**:

Identified by v2, v4. Misleading UI label and dead parameter slot in mapping.

### JR-CAN-TRAIN-012 — Defer true IPC architecture (Cascor-Canopy process separation) to future when triggering conditions are met.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 407-433)

**Detail**:

Current architecture embeds CasCor within Canopy process. Deferral justified by RemoteWorkerClient and async training providing sufficient capability. Revisit if hard cancellation, multiple concurrent jobs, or remote clusters needed.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Phase 4 deferred; has explicit trigger conditions

### JR-ML-DOC-011 — Define issue tracking template: structured fields for requirements, test cases, verification.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/templates/TEMPLATE_ISSUE_TRACKING.md` (lines 1-50)

### JR-CAN-OPS-003 — Demo backend logs 'Invalid STOP command in current state' error on every teardown, creating noisy logs.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 32-32)

**Detail**:

Cosmetic issue; does not affect functionality. Fix by handling terminal state transitions more gracefully.

**Notes**:

Low priority; noise reduction only.

### JR-CAN-DEP-006 — Docker health check should consider curl-based approach.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 251-251)

**Detail**:

Issue 5.4.1: Current health check may not be reliable. Consider switch to
curl-based probe (add curl to base image) for more flexible checks.

### JR-ML-OPS-010 — Document and automate manual PyPI setup procedures.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PYPI_MANUAL_SETUP_STEPS.md` (lines 1-100)

**Notes**:

Manual steps should be automated in publishing pipeline.

### JR-CAS-WS-006 — Documentation generation: CLI setup guide (Claude Code + Serena MCP configuration, auto-start, troubleshooting).

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/setup_config_guides/claude-code-serena-setup-guide.md` (lines 1-100)

**Detail**:

Native installer for Claude Code (no Node.js required), uvx for Serena (from GitHub), global MCP server configuration with --project-from-cwd auto-detection, validation procedures (claude doctor, /mcp status check), troubleshooting (uvx path, Serena startup, port 24282, PATH resolution). File locations: ~/.local/bin/claude, ~/.claude/settings.json, ~/.claude.json. Per-project configuration alternative. Documentation complete with 8 sections and reference tables.

### JR-CAN-OPS-004 — Double initialization on fallback-to-demo path: backend.initialize() called twice (ISS-18).

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 667-683)

**Detail**:

ISS-18 LOW. In main.py:165-180, when CasCor probe fails and backend falls back to demo mode, backend.initialize() called once inside fallback block (line 177) and again unconditionally (line 180). For DemoBackend, initialize() calls self._demo.start() starting training simulation thread. Could start two threads or produce unexpected state. In practice, DemoBackend.initialize() appears idempotent, so code smell rather than active bug. Only affects fallback-to-demo path (cascor unreachable).

**Notes**:

Identified by v6. v5 confirmed asynccontextmanager runs sequentially so demo state sync executes correctly after fallback.

### JR-ML-SEC-219 — Draft release descriptions for each application (templates provided in the code review document). These should be refined and used as….

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 294-305)

**Detail**:

Draft release descriptions for each application (templates provided in the code review document). These should be refined and used as GitHub release notes.

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Release Description Documents']

### JR-CAN-OPS-005 — Dual status normalization paths produce inconsistent representations (ISS-14 cosmetic inconsistency).

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 588-605)

**Detail**:

ISS-14 INFO. Two independent normalization paths exist: Path A (ServiceBackend.get_status()) uses .upper() comparison returning boolean flags (is_running, is_paused) plus raw fsm_status; Path B (relay callback _normalize_status()) returns title-case strings ("Training", "Paused"). Result: training_state may hold status="Started" while /api/status returns is_running=True and fsm_status="STARTED". Cosmetic inconsistency only, not functional blocker, but could confuse code comparing status strings from different sources.

**Notes**:

Identified by v4. Cross-source status comparison risk.

### JR-CAN-ARCH-008 — Environment variable parsing must fix boolean/integer precedence bug.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 228-228)

**Detail**:

Issue 5.1.2: _convert_type checks boolean before integer, causing "0"
to parse as False instead of 0. Reorder checks: int/float before bool.

### JR-CAN-SEC-012 — Exception handling in callback_context must narrow exception types.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 244-244)

**Detail**:

Issue 5.3.3: Bare except: clause catches SystemExit/KeyboardInterrupt.
Narrow to (ValueError, AttributeError, ...); let system signals propagate.

### JR-CAN-OBS-017 — FATAL_LEVEL constant conflict must be resolved.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 238-238)

**Detail**:

Issue 5.2.4: FATAL_LEVEL defined in multiple modules with different values.
Consolidate to single definition in logging module.

### JR-ML-ARCH-297 — Future: Implement free-threading local tier when PyTorch supports free-threaded Python (Python 3.14+).

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 914-932)

### JR-ML-TRAIN-106 — **Goal**: Ensure cascor exposes all required fields for canopy consumption.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 49-65)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: 'Phase 2:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

### JR-ML-ARCH-298 — **Goal**: Fix all dark mode styling issues and UI layout problems.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 107-162)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 4:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

### JR-ML-ARCH-299 — **Goal**: Fix parameter initialization and value mapping issues.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 68-104)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 3:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

### JR-ML-ARCH-300 — **Goal**: Implement new features requested in the regression report.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 165-187)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 5:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

### JR-CAN-UI-033 — Header title color must be theme-aware (not hardcoded).

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 247-247)

**Detail**:

Issue 5.3.6: Header title color hardcoded to light theme. Use theme-aware
color from theme_constants.py for dark/light mode support.

### JR-CAN-UI-034 — Hit rate formatter must verify percentage contract (0.0-1.0 range).

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 246-246)

**Detail**:

Issue 5.3.5: _format_hit_rate may receive values outside [0, 1]. Add bounds
check and either clamp or raise error depending on usage context.

### JR-ML-TOOL-047 — Implement V2 worktree cleanup procedure.

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/WORKTREE_CLEANUP_V2_PLAN.md` (lines 1-100)

**Notes**:

Development workflow optimization.

### JR-CAS-PERF-005 — Infrastructure enhancements: GPU/CUDA support, continuous profiling (Grafana Pyroscope), large file refactoring, auto-generated API docs.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 253-267)

**Detail**:

P3-NEW-003: GPU/CUDA support (XL, 2-4 weeks, 🔴 NOT STARTED). P3-NEW-004: Continuous profiling with Grafana Pyroscope (🔵 DEFERRED, L effort). Large file refactoring (no file > 2000 lines, 🔴 NOT STARTED, L effort). Auto-generated API docs (MkDocs/Sphinx, 🔴 NOT STARTED, M effort). Documentation link checking in CI (🔴 NOT STARTED, S effort). Documentation search functionality (🔴 NOT STARTED, M effort). All marked future work or deferred.

**Notes**:

[v2 ARCH→PERF re-bucket] [v2 remap: AR→ARCH]

### JR-ML-ARCH-301 — juniper-canopy: **3066 passed**, 100 skipped, 12 pre-existing failures (state sync + topology handler), 3 collection errors (missing….

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md` (lines 268-323)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 5:'] From JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md

### JR-ML-DATA-041 — juniper-cascor-client (Phase 4): add `get_dataset_data()` to `juniper_cascor_client/client.py`

**Status**: proposed  **Priority**: P3  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 348-354)

**Detail**:

| `juniper_cascor_client/client.py` | Add `get_dataset_data()` method |

**Notes**:

[v4 brief repaired; was: '9.3 juniper-cascor-client (Phase 4 only)']

[2026-08-29 brief repaired from cited content; was: '`juniper_cascor_client/client.py`']

### JR-CAN-ARCH-009 — Layout type sprint must forward positional/keyword parameters correctly.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 245-245)

**Detail**:

Issue 5.3.4: _layout_type_sprint helper loses parameters. Use *args, **kwargs
or explicit forwarding to preserve full signature.

### JR-CAN-UI-035 — Left sidebar too wide on Training Metrics tab; hardcoded dbc.Col(width=3) applies to all tabs.

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 47-47)

**Detail**:

Fix: per-tab width via ui_standards.py + seed notes/UI_STANDARDS.md with design constants and sidebar width table.

**Notes**:

Cosmetic; low priority. Enables UI design documentation.

### JR-CAN-UI-036 — Left sidebar too wide on Training Metrics tab—use per-tab width from ui_standards.

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 46-46)

**Detail**:

Hardcoded dbc.Col(width=3) for all tabs. Move to per-tab config via
ui_standards.py. Seeds UI_STANDARDS.md documentation.

**PRs**: PR-6 (cosmetic sidebar width), PR-6.5 (UI_STANDARDS doc + Training-Metrics narrowing experiment)

### JR-CAN-OBS-018 — Log timestamps must be timezone-aware (UTC).

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 236-236)

**Detail**:

Issue 5.2.2: Naive timestamps can cause ambiguity in distributed logs.
Use datetime.now(timezone.utc) or equivalent.

### JR-CAN-OBS-019 — Logger must capture real call site instead of logger.py:line-N.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 235-235)

**Detail**:

Issue 5.2.1: _log_with_context wrapper causes all logs to appear from
logger.py instead of actual call site. Use inspect.stack() to get caller.

### JR-ML-DOC-012 — Maintain cheatsheet mapping AGENTS.md sections to project/repo; enable rapid reference.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-15_JUNIPER-ECOSYSTEM_CHEATSHEET-SECTION-TO-PROJECT-MAPPING.md` (lines 1-50)

### JR-ML-DOC-013 — Maintain developer cheatsheet with current tooling and workflow procedures.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md` (lines 1-100)

**Notes**:

Living documentation; should be kept current.

### JR-CAN-API-039 — Normalize parameter mapping: state sync params use raw cascor names instead of nn_*/cn_* namespace (ISS-12).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 556-568)

**Detail**:

ISS-12 MODERATE. During initial state sync (state_sync.py:98-103), training parameters stored using raw cascor parameter names (learning_rate, max_hidden_units, epochs_max) rather than mapped through _CASCOR_TO_CANOPY_PARAM_MAP to canopy namespace (nn_*/cn_*). When main.py:189-202 applies synced.params to parameter panel, dashboard receives cascor parameter names. Parameter panel labels may not match values, or values may not populate correctly.

**Notes**:

Identified by v7 (unique finding). Caused by ISS-13 (state sync bypasses adapter).

### JR-CAS-TRAIN-035 — Per-instance queue management to avoid cross-instance interference.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Complex refactor; deferred to later phase.

### JR-ML-API-090 — Phase 4 (cross-repo dataset endpoint).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 178-184)

**Detail**:

| Task 2 Phase 2: `GET /v1/dataset/data` endpoint in cascor | ❌ NOT STARTED |

### JR-ML-DEP-048 — Phase 4 (Intermediate):  Kubernetes via k3s when multi-machine or production scale is required.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 299-328)

**Detail**:

**Recommended approach: Layered strategy with Docker Compose as the primary orchestrator.**

**Notes**:

[v3 brief repaired from cited content; was: '2.4 Recommendation']

### JR-ML-ARCH-302 — Phase 4: Callbacks.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 544-555)

**Detail**:

1. Add collapsible toggle callbacks (NN + CN sections)

### JR-ML-DEP-049 — Phase 4: Kubernetes Helm Chart — ✅ COMPLETE.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 270-285)

**Detail**:

| 4.1  | Chart scaffolding (`Chart.yaml`, `_helpers.tpl`) | ✅ Implemented |

### JR-ML-DEP-050 — Phase 4: Kubernetes Support (P2) -- DONE.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 785-804)

**Detail**:

**Goal**: Enable k8s deployment of the full stack.

### JR-ML-TOOL-048 — Phase I (folded into Phase B): Asset cache busting for `websocket_client.js` + `ws_dash_bridge.js`.

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 1080-1099)

**Detail**:

Bump `assets_folder_snapshot` or equivalent query param in Dash config so browsers pick up new JS without hard refresh.
Included as deliverable MVS-FE-16 in Phase B (§6.3), not a standalone phase.
Verify via browser devtools that JS URL includes cache-bust query parameter changing on deploy.

**Design**:

Part of Phase B PR (P6). Ensures stale JS in browser cache doesn't cause mismatches with new protocol.

**Notes**:

Folded into Phase B per R1-05 §6.2. No independent gate. Rollback: revert cache-bust config (5 min TTF).
Priority P3 (folded, low-visibility change).

### JR-ML-OBS-149 — Plan post-R5 observability program enhancements.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md` (lines 1-100)

**Notes**:

After R5 completion; scope TBD.

### JR-CAN-LOCK-006 — Pre-commit hook suite must be auto-updated.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 253-253)

**Detail**:

Issue 5.4.3: pre-commit hooks may be outdated. Run `pre-commit autoupdate`
to refresh all hook versions and update .pre-commit-config.yaml.

### JR-DAT-TEST-012 — Pre-commit hooks should include pyupgrade for syntax modernization.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 72-73)

**Notes**:

L-01 LOW (P3).

### JR-DAT-TEST-013 — Pre-commit hooks should include shellcheck for shell script validation.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 73-74)

**Notes**:

L-02 LOW (P3).

### JR-CAS-PERF-006 — Process-based async plotting to avoid blocking training.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Depends on BUG-002 verification.

### JR-CAN-TEST-043 — Pytest tests use CWD-relative paths instead of fixture-based or absolute paths, causing Docker-environment failures.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 31-31)

**Detail**:

One file fixed; codebase-wide audit not done. CWD-relative paths fail in container contexts where CWD differs.

**Notes**:

One file fixed; more audit needed.

### JR-CAS-LOCK-003 — Reconcile version across pyproject.toml, file headers, and API response metadata.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 820-824)

**Detail**:

Consider using single-source-of-truth version via importlib.metadata.version() instead of file header strings.

### JR-CAS-TOOL-010 — Remove legacy stale duplicate file check.py (duplicate of spiral_problem.py).

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 275-279)

### JR-CAN-ARCH-010 — Settings access must guard against KeyError or use default.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 242-242)

**Detail**:

Issue 5.3.1: config.key access can raise AttributeError. Use get() or
try/except to provide sensible defaults.

### JR-CAN-TEST-044 — Shellcheck severity level should align with ecosystem convention.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 252-252)

**Detail**:

Issue 5.4.2: Current shellcheck invocation uses non-standard severity flag.
Align to standard shellcheck options.

### JR-CAS-TEST-019 — Test WebSocket responsiveness during training under load via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 622-632)

**Detail**:

When Cascor training runs via asyncio.run_in_executor() in FastAPI, WebSocket
responsiveness should be verified under load.

### JR-CAN-WS-006 — Training WebSocket must validate message size to prevent DoS.

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 243-243)

**Detail**:

Issue 5.3.2: WebSocket message handler does not check message size.
Add check: reject messages > 1MB with log and graceful disconnect.

### JR-ML-OPS-011 — Transfer all Juniper repositories and PyPI packages from pcalnon to OvertoadResearch GitHub organization.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PYPI_DEPLOYMENT_PLAN.md` (lines 339-400)

**Detail**:

Phase 5: Create OvertoadResearch org on GitHub/PyPI, transfer repos with URL redirects, update git remotes/SSH, add org as PyPI maintainer, update OIDC configs.

### JR-CAN-DOC-010 — UI_STANDARDS.md document must be created to codify design constants (sidebar widths, spacing, color scheme) across dashboard components.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 1-50)

**Detail**:

Currently no centralized design standards; sidebar width hardcoded to dbc.Col(width=3) for all tabs. Create ui_standards.py module and notes/UI_STANDARDS.md documenting spacing, colors, responsive breakpoints.

**Notes**:

Enables consistent design across application.

### JR-DCL-DOC-008 — Update AGENTS.md Last Updated date and document utility scripts.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 160-163)

**Detail**:

Low-priority metadata and polish tasks: (1) Update header Last Updated from 2026-02-20 to current date,
(2) Document utility scripts (scripts/check_doc_links.py, scripts/generate_dep_docs.sh, util/run_all_tests.bash),
(3) Add environment variables section documenting JUNIPER_DATA_API_KEY, JUNIPER_DATA_URL, .env.example reference.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Tasks 4.1, 4.2, 4.3) and AGENTS_MD_UPDATE_PLAN (Steps 4.1, 4.2, 4.3).

### JR-CAS-DEP-001 — Validate docker-compose configuration for 3-service deployment end-to-end.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 594-603)

**Detail**:

docker-compose config for 3-service deployment not tested end-to-end.

### JR-REC-TEST-002 — Service-vs-bench parity as a regression criterion

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md` (lines 1-13)

**Detail**:

A service-mode run with bench-primary-matched params must land inside the same OQ-14 bands as the offline bench; divergence is a service-path defect. Candidate for a periodic (release-gate or scheduled) automated check once `run_suite.py` (Wave 7.1) exists.
