# Requirements — API

**Area**: API contracts — schemas, versioning, compatibility, migrations

**Total entries**: 154

**By status**: proposed=123 | designed=1 | shipped=25 | deferred=4 | rejected=1

**By priority**: P0=10 | P1=64 | P2=73 | P3=7

**By owner**: ml=90 | can=39 | cas=14 | dat=6 | ccl=4 | rec=1

---

### JR-CAS-API-001 — HDF5 serialization system with UUID persistence, RNG state preservation, and complete state restoration for training resume.

**Status**: shipped  **Priority**: P0  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/FINAL_STATUS.md` (lines 1-100)

**Detail**:

Session 1 (5 items): UUID persistence, Python RNG state, config JSON serialization, history key alignment (value_loss/value_accuracy), activation function restoration. Session 2 (8 items): hidden units checksums, shape validation, format validation, test suite, Python random state fix, config sanitization, plotting regression fix. 18 integration tests (15 passing, 3 timeout). No fabricated commit SHAs or dates.

**Notes**:

[v2 remap: SE→API]

### JR-ML-API-001 — Storage & Infrastructure.

**Status**: deferred  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 348-398)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 273-317)

**Detail**:

## 11. Cross-Repository Alignment Issues

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-API-002 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 176-187)

**Detail**:

**C-JDC-1: Version doesn't reflect API changes**

### JR-ML-API-003 — Cross-Cutting Themes.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 28-41)

**Detail**:

1. **Changelog debt is universal**: Every application has significant undocumented changes. This is the single most common blocker.

### JR-CAN-API-001 — Dataset-tab edits do not change running training data; missing dataset-swap endpoint and param-map gap prevent user control of cascor dataset.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 39-42)

**Detail**:

Phase 1 fix: add cascor dataset-swap endpoint + Cancel button for cold swap (cold-swap + Cancel button). Phase 2: live in-flight swap behind experimental-functions gate with two-step warning modal and History/Snapshots/Replay persistence.

**Notes**:

Separate detailed spec in ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md

### JR-CAN-API-002 — Fix /ws exception handling infinite loop in main.py.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 73-73)

**Detail**:

Issue 1.1.1: WebSocket route exception handling loop. Must exit cleanly
on expected errors (client disconnect) without retry loop.
File: src/main.py

### JR-CAN-API-003 — Fix metrics format mismatch: flatten nested dashboard metrics contract (metrics.loss, metrics.accuracy) to match service mode output.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Dashboard reads nested metrics (metrics.loss, metrics.accuracy); service-mode adapter emits flat structure. Critical display blocker for metrics charts.

**Notes**:

P5-RC-01; critical display blocker; part of final synthesis

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

### JR-DAT-API-001 — All consumers (juniper-cascor, JuniperCanopy) reference juniper-data-client from PyPI (>=0.3.0), not vendored copies.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 333-349)

**Notes**:

RD-011 complete 2026-02-21. Vendored copies removed from all consumers.

### JR-CAS-API-002 — Build FastAPI service layer for CasCor with REST endpoints and WebSocket streaming.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 728-735)

**Detail**:

Add 19 REST endpoints across 6 route files; WebSocket endpoints for real-time training streaming (/ws/training, /ws/control); TrainingLifecycleManager with thread-safe state machine and ThreadPoolExecutor; service entry point (server.py) alongside existing CLI (main.py).

### JR-DAT-API-002 — Client package juniper-data-client published to PyPI (>=0.3.0) with Trusted Publishing OIDC.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 313-330)

**Notes**:

RD-010 complete 2026-02-20. Standalone repo pcalnon/juniper-data-client. 41 tests, 96% coverage.

### JR-DAT-API-003 — Health check endpoints distinguish liveness (/v1/health/live) and readiness (/v1/health/ready).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 186-207)

**Notes**:

DATA-007 complete. 4 integration tests added.

### JR-CAN-API-006 — Implement cascor_service_adapter normalization adapters (ResponseEnvelope, metrics, status, parameters).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_1/5b_DEVELOPMENT_PLAN_EXTERNAL_CASCOR_FIX.md` (lines 1-150)

**Detail**:

7-phase development plan Phase 1: Adapter normalization (_unwrap_envelope, _normalize_metric, _normalize_metrics_history). Phase 2: ServiceBackend status normalization (flat dict builder). Phase 3: CascorStateSync fix (navigate real cascor nested structure). Phase 4: Parameter map cleanup (generate reverse map).

**PRs**: #146

### JR-CCL-API-001 — Implement dataset retrieval method: get_dataset_data() via GET /v1/dataset/data.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 45-48)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-API-002 — Implement remote worker monitoring methods: list_workers(), get_worker(worker_id), get_worker_stats().

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 28-35)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-API-003 — Implement snapshot management methods: list_snapshots(), get_snapshot(snapshot_id), save_snapshot(), load_snapshot(snapshot_id).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 36-44)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-API-004 — Implement update_params() client method for runtime training parameter updates via PATCH /v1/training/params.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 28-33)

**Detail**:

Add update_params() method to JuniperCascorClient with supporting _patch() helper and PATCH method in ALLOWED_METHODS.
Tests required for both real client (responses mock) and fake client.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAN-API-007 — MetricsPanel must transform flat-keyed metrics to nested format for dashboard consumption (RC-1 fix from Phase 4 analysis).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_66a019dc-94ba-47fb-8042-7ce8f974d071.md` (lines 123-226)

**Detail**:

Service backend's _normalize_metric() produces flat keys (train_loss, train_accuracy, hidden_units),
but dashboard MetricsPanel reads nested keys (metrics.loss, metrics.accuracy, network_topology.hidden_units).
Fix: Add _to_dashboard_metric() transformation layer after _normalize_metric() in _ServiceTrainingMonitor.get_recent_metrics().

**Design**:

@staticmethod
def _to_dashboard_metric(flat: dict) -> dict:
  return {
    "epoch": flat.get("epoch", 0),
    "metrics": {
      "loss": flat.get("train_loss"),
      "accuracy": flat.get("train_accuracy"),
      "val_loss": flat.get("val_loss"),
      "val_accuracy": flat.get("val_accuracy"),
    },
    "network_topology": {
      "hidden_units": flat.get("hidden_units", 0),
    },
    "phase": flat.get("phase"),
    "timestamp": flat.get("timestamp"),
  }

**Notes**:

Primary blocker identified by all 7 Phase 3 proposals (v1-v7) and 4 Phase 4 proposals. Verified at cascor_service_adapter.py:430-460 and metrics_panel.py lines 1091,1120-1122,1330,1449-1450,1499,1561-1562.

### JR-CAN-API-008 — NetworkVisualizer must accept weight-oriented topology format from CasCor and transform to graph-oriented format (RC-2 from Phase 4).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_66a019dc-94ba-47fb-8042-7ce8f974d071.md` (lines 232-310)

**Detail**:

CasCor returns topology with input_size/output_size keys and hidden_units as weight array;
NetworkVisualizer expects input_units/output_units as integers and a graph connections structure.
extract_network_topology() returns raw CasCor response without transformation.

**Notes**:

Identified by v2 and v4 Phase 3 proposals. Secondary display blocker.

### JR-CAN-API-009 — Normalize external CasCor response envelope format (FIX-1 through FIX-14 decision blocks).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_1/5a_EXTERNAL_CASCOR_INTEGRATION_DEV_PLAN.md` (lines 1-100)

**Detail**:

Phase 1 comprehensive plan addressing ResponseEnvelope unwrapping, field name normalization, falsy-value preservation across FIX-1 through FIX-SYS decision blocks. Implementation verified in Phase 4 analysis — all 14 fixes correctly implemented. Includes _unwrap_response(), _normalize_metric(), _first_defined(), expanded _normalize_status(), ServiceBackend.get_status() flat dict production, and FakeCascorClient alignment.

**PRs**: #146

### JR-DAT-API-004 — NPZ artifact schema documented with 6 keys (X_train, y_train, X_test, y_test, X_full, y_full) as float32 one-hot.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 274-292)

**Notes**:

DATA-010 complete. Documented in docs/api/JUNIPER_DATA_API.md.

### JR-DAT-API-005 — Parameter validation parity with consumer projects via AliasChoices and Pydantic.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 295-300)

**Notes**:

DATA-011 complete.

### JR-CAS-API-003 — Polyrepo migration complete: 7 phases, 8 repos, microservices architecture, health checks, version matrix.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 1-100)

**Detail**:

All 7 phases complete (2026-03-02). Phase 0: Stabilize baseline. Phase 1: Extract/publish client packages (juniper-data-client v0.3.1 PyPI). Phase 2: Build CasCor Service API (FastAPI, 19 REST + 2 WS endpoints). Phase 3: Create cascor-client + worker (PyPI v0.1.0 2026-02-24). Phase 4: Decouple Canopy (CascorServiceAdapter 306 lines, CascorIntegration 1,601 deleted, 2026-02-25). Phase 5: Split repos (8 repos, SSH keys, 2026-02-25). Phase 6: Hardening (Docker Compose, health check standardization, 2026-02-25). Phase 7: Production readiness (2026-03-02). Ecosystem compatibility matrix verified.

**Notes**:

[v2 ARCH→API re-bucket] [v2 remap: AR→ARCH]

### JR-CAS-API-004 — REST API and WebSocket architecture: 19 REST endpoints, 2 WS channels, Pydantic models, lifecycle management, remote workers.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 148-165)

**Detail**:

CasCor Service API complete (Phase 2). FastAPI server with 19 REST endpoints, 2 WS channels, full lifecycle management. Training lifecycle: TrainingLifecycleManager, TrainingStateMachine, TrainingMonitor. API security: auth (X-API-Key header, HMAC comparison), rate limiting (fixed-window per IP). WebSocket channels: control, training, workers. Remote worker system: registry, coordinator, binary protocol, security, audit. Decision boundary visualization. Snapshot management routes. Output weight initialization option. Convergence threshold runtime-updateable via PATCH. Pydantic BaseSettings configuration.

**Notes**:

[v2 remap: SE→API]

### JR-CAS-API-005 — Serialization critical fixes: UUID persistence, Python RNG state, config JSON serialization, history key alignment, activation function restoration.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/SERIALIZATION_FIXES_SUMMARY.md` (lines 1-100)

**Detail**:

UUID: Inject from meta/uuid via config dict. Python RNG: random.getstate() → pickle → HDF5. Config JSON: Exclude non-serializable (activation_functions_dict, log_config, logger). History keys: Accept both val_* (old) and value_* (new) with fallback. Activation: Call _init_activation_function() after load. Backward compatibility maintained for old snapshots. Test recommendations provided (5 unit tests). Hidden units checksums in progress. Shape validation deferred. Multiprocessing state restoration incomplete. Optimizer state decision needed (recommend removal).

**Notes**:

[v2 remap: SE→API]

### JR-ML-API-005 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 402-419)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.3 CR-024: Chunked Encoding Body Limit']

### JR-ML-API-006 — CAN-015g/h snapshot-loading endpoints: restore, replay, resume, retrain with FSM state transitions.

**Status**: deferred  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md` (lines 1-100)

### JR-ML-API-007 — Issue Remediations, Section 21.

**Status**: rejected  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 692-742)

**Detail**:

#### API-01: Health `status` Value Inconsistent

### JR-ML-API-008 — /api/v1/training/status returns snapshot_seq + server_instance_id atomically.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 117-117)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-CAS-API-006 — Add requests as declared dependency in pyproject.toml - currently undeclared but used by JuniperDataClient.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 229-242)

**Detail**:

JuniperDataClient imports requests but not listed in pyproject.toml or documented
in CLAUDE.md. Will fail on fresh installs. Add to dependencies and document.

### JR-ML-API-009 — Add startup health verification to Canopy**: When `CASCOR_SERVICE_URL` is set, perform an HTTP GET to the CasCor health endpoint during….

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 627-655)

**Detail**:

- cascor_service: reachable / unreachable / demo_mode

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Health Check Pattern Recommendation']

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

### JR-CAN-API-010 — Canopy must enforce max_connections limit in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 74-74)

**Detail**:

Issue 1.1.2: Currently no enforcement of max_connections. Must track active
connection count and reject new clients when limit reached.

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

### JR-CAS-API-008 — CasCor backend must expose prediction method accepting arbitrary input grids for visualization.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 687-691)

**Notes**:

Required for JuniperCanopy decision boundary visualization.

### JR-ML-API-012 — CasCor has the training tensors in memory (`_train_x`, `_train_y`) but its `/v1/dataset`.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 128-137)

**Detail**:

`ServiceBackend.get_dataset()` (service_backend.py:155-168) returns metadata only. The

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Root Cause']

### JR-CAS-API-009 — CasCor service must expose REST endpoints for snapshot save/load with full training state.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 701-705)

**Detail**:

REST endpoints must capture network weights, optimizer state, and training metadata via PyTorch state_dict() or equivalent.

### JR-CAN-API-012 — CascorServiceAdapter must normalize cascor's nested status structure (state_machine, monitor, training_state) to flat dashboard format (is_running, is_paused, phase, current_epoch, hidden_units).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md` (lines 1-10)

**Detail**:

Cascor returns nested objects; dashboard expects flat keys. Add _normalize_status_response() method that maps state_machine.status (title case) to boolean flags (is_running, is_paused, completed, failed) with falsy-value safety using _first_defined().

**Notes**:

Status bar works via /api/status endpoint transformation; direct backend.get_status() calls get nested format.

### JR-ML-API-013 — Client Packages (PyPI).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 67-76)

**Detail**:

| `juniper-data-client`   | 0.3.0   | HTTP client for JuniperData API          |

### JR-CAN-API-013 — CORS configuration YAML syntax must be valid and documented.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 87-87)

**Detail**:

Issue 1.2.5: app_config.yaml CORS section has syntax errors. Validate and
document expected format. File: conf/app_config.yaml

### JR-CAS-API-010 — Create shared protocol/interface package for data contracts between applications.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 245-257)

**Detail**:

No shared Python package defining data contracts (Pydantic models, type aliases).
Each app independently defines expectations. NPZ array keys (X_train, y_train, etc.)
documented but not enforced. Fix: create juniper_contracts package defining API schemas.

### JR-CAN-API-014 — DashboardManager must construct API URLs via settings, not ad-hoc _api_url().

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 91-91)

**Detail**:

Issue 1.3.1: _api_url() helper is error-prone and inconsistent. Replace all
callsites with settings-based URL construction. File: src/frontend/dashboard_manager.py

### JR-ML-API-014 — Define four snapshot endpoints: restore (explore), replay (watch metrics fresh), resume (continue), retrain (new training).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-SNAPSHOT-LOAD-TYPES.md` (lines 18-76)

### JR-CAN-API-015 — Define Pydantic model for set_params endpoint request body.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 77-77)

**Detail**:

Issue 1.1.5: set_params endpoint lacks formal request schema. Add Pydantic
model for validation. File: src/main.py. Updates OpenAPI documentation.

### JR-CAN-API-016 — Fix CascorStateSync to read from correct response fields (data.state_machine, data.monitor).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

Sync reads data.state, data.epoch; real cascor has data.state_machine, data.monitor. Causes initial state hydration to fail.

**Notes**:

FIX-5; initial sync reads wrong keys

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

### JR-ML-API-015 — `glob("*.npz")` scans entire data directory on every health check.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 442-455)

**Detail**:

| **Sync generation**    | ⚠️ Concern | `generator.generate(params)` blocks event loop in async endpoint  |

**Notes**:

[v4 brief repaired; was: '4.3 juniper-data Performance']

### JR-CAN-API-019 — Helper function _first_defined() must be available for falsy-value safe field extraction across nested cascor response structures.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 1-50)

**Detail**:

Pattern: _first_defined(a, b, c) returns first non-None/non-False value. Required for extracting epoch/hidden_units from cascor's variable-structure responses where a field may be nested at different paths depending on backend state.

**Notes**:

Used across all normalization methods.

### JR-CAN-API-020 — Implement CascorIntegration.get_network_data() method to return network statistics.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 120-140)

**Detail**:

Method does not exist on CascorIntegration class; callers will receive AttributeError at runtime. Must return dict with keys: input_weights, hidden_weights, output_weights, hidden_biases, output_biases, threshold_function, optimizer.

**Notes**:

Network statistics tab fails when connected to real CasCor backend; blocking P1

### JR-CAN-API-021 — Implement real backend control for Canopy WebSocket endpoint when connected to live CasCor backend.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 55-85)

**Detail**:

The /ws/control endpoint currently rejects all commands when cascor_integration is active with a hardcoded error. Must implement command routing to CascorIntegration methods (start, stop, pause, resume, reset) and add state broadcasting after each command execution.

**Notes**:

Part of Phase 1 critical integration blockers; blocking all real-backend WebSocket control

### JR-CAN-API-022 — Implement save_snapshot() and load_snapshot() methods on CascorIntegration class.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 146-166)

**Detail**:

Methods do not exist; code falls through to minimal HDF5 fallback that only stores metadata, not network state. Must delegate to CasCor's CascadeHDF5Serializer.

**Notes**:

Snapshot save/load in real backend mode produces incomplete snapshots

### JR-ML-API-016 — Include all 22 meta-parameter fields in the state response. Use `.get()` with `TrainingConstants` defaults for any missing fields to handle….

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 306-310)

**Detail**:

Include all 22 meta-parameter fields in the state response. Use `.get()` with `TrainingConstants` defaults for any missing fields to handle backward compatibility when the backend doesn't yet store all parameters.

**Notes**:

[v3 brief repaired from cited content; was: '5.2 `/api/state` Endpoint']

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

### JR-CAN-API-023 — Middleware must handle malformed Content-Length header gracefully.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 78-78)

**Detail**:

Issue 1.1.6: Non-numeric or negative Content-Length can crash request parsing.
Add bounds check and return 400 Bad Request. File: src/middleware.py

### JR-CAN-API-024 — Network topology format mismatch: cascor returns weight-oriented format (input_size, hidden_units array with weights) but NetworkVisualizer expects graph-oriented format (input_units, output_units integers, nodes/connections lists).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 268-295)

**Detail**:

CasCor architecture: input_size, hidden_units [{id, weights, bias, activation}], output_weights, output_bias. Adapter must reconstruct graph format preserving cascade connections (each hidden unit connects to all inputs plus prior hidden units).

**Notes**:

Topology visualization always renders empty because validation guard topology_data.get('input_units', 0)==0 fails when key is 'input_size'.

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

### JR-ML-API-020 — Phase 2: Backend API.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 528-537)

**Detail**:

1. Update `/api/set_params` endpoint to accept new keys

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

### JR-ML-API-022 — Releases must follow the dependency graph:.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 351-364)

**Detail**:

1. juniper-data (upstream, no Juniper dependencies)

**Notes**:

[v3 brief repaired from cited content; was: '5.1 Tag & Release Order']

### JR-CAN-API-027 — Remove duplicate cn_patience configuration parameter.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 76-76)

**Detail**:

Issue 1.1.4: cn_patience appears twice in configuration. Consolidate to single
canonical definition. File: src/main.py

### JR-ML-API-023 — Requires network access and many requests; mitigated by rate limiting.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 492-505)

**Notes**:

[v4 brief repaired; was: '6.1 Risks']

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

### JR-ML-API-027 — Work Unit 4: Service Mode Verification (LOW) — IMPLEMENTED.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 144-161)

**Detail**:

Added 5 integration tests to `test_network_stats_endpoint.py` (`TestNetworkStatsServiceMode` class) that mock the backend as service mode with realistic multi-hidden-unit weight data. Tests verify:

### JR-CAS-API-011 — Infrastructure & profiling suite: cProfile, memory profiling, py-spy, hot-path logging, micro-benchmarks, test harness.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 129-145)

**Detail**:

cProfile integration: ProfileContext, profile_function decorator (src/profiling/deterministic.py). Memory profiling: MemoryTracker, --profile-memory CLI flag (src/profiling/memory.py). py-spy: SVG flame graphs, Speedscope JSON (util/profile_training.bash). Hot-path logging: SampledLogger, BatchLogger, log_if_enabled, LogFrequencyTracker. Micro-benchmarks: forward pass, autograd, correlation, candidate training, output training, concurrency, shared memory, end-to-end. Benchmark harness: src/tests/scripts/run_benchmarks.bash + pytest-benchmark. All complete and verified.

**Notes**:

[v2 remap: SE→API]

### JR-CAS-API-012 — Network serialization architecture decisions: HDF5 format specification, version migration strategy, backward compatibility.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/NEXT_STEPS.md` (lines 200-250)

**Detail**:

HDF5 groups: meta, config, params, arch, random, hidden_units. Backward compatibility: old snapshots without Python random state load successfully (state not restored). Old snapshots with val_* keys load via fallback. Old corrupted config JSON falls back to attribute-based loading. No breaking changes. Schema versioning support planned (future). Compression optimization deferred. Incremental snapshots for large networks (future). Remote storage support (S3/Azure/GCS, future).

**Notes**:

[v2 remap: SE→API]

### JR-ML-API-028 — _normalize_metric dual-format contract (flat + nested) preserved forever.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 59-59)

**Notes**:

Settled position C-22 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-029 — **Output weights transposition bug**: ALREADY FIXED (merged). `_transform_topology()` now.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 200-213)

**Detail**:

**Output weights transposition bug**: ALREADY FIXED (merged). `_transform_topology()` now

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Root Cause']

### JR-ML-API-030 — REST endpoints preserved FOREVER: /api/metrics/history, /api/train/*, /api/v1/training/params, /api/topology.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 60-60)

**Notes**:

Settled position C-23 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-031 — `_STATE_TO_FSM` and `_STATE_TO_PHASE` class attributes are dead code. `get_training_status()` uses a local `status_map` dict instead.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 69-81)

**Detail**:

| ID       | Severity   | File:Line                         | Description

**Notes**:

[v4 brief repaired; was: '1.3 Code Quality']

### JR-ML-API-032 — "cn_candidate_selection": None,  # no default; sub-group disabled when checkbox unchecked.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 267-302)

**Detail**:

"cn_candidate_selection": None,  # no default; sub-group disabled when checkbox unchecked

**Notes**:

[v3 brief repaired from cited content; was: '4.4 Applied Params Store Structure']

### JR-ML-API-033 — A.6 Application Entry Points.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 880-895)

**Detail**:

| `juniper_data/__main__.py`     | juniper-data          | `python -m juniper_data` |

### JR-ML-API-034 — Add near the top after configurable paths:.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 310-353)

**Detail**:

if [[ "${1:-}" == "--systemd" ]]; then

**Notes**:

[v3 brief repaired from cited content; was: '5.8 Plant/chop --systemd mode (Step 2.8)']

### JR-ML-API-035 — **Add topology hash based on weights**: Include a hash or generation counter for weight values in the topology hash function so the network.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 533-549)

**Detail**:

5. **Add topology hash based on weights**: Include a hash or generation counter for weight values in the topology hash function so the network visualization redraws when weights change during

**Notes**:

[v4 brief repaired; was: '7.2 Short-Term (Medium)']

### JR-CAN-API-028 — All JuniperData REST API interactions must have standardized error handling with status code mapping.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 199-211)

**Detail**:

Map HTTP status codes to user-friendly error messages; implement consistent retry and timeout patterns.
Estimated scope: 2-3 files, 100-200 lines.

**Notes**:

CAN-HIGH-006; HIGH priority post-release item.

### JR-ML-API-036 — All three services already implement Kubernetes-compatible health probes:.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 604-616)

**Detail**:

| **JuniperData**   | `GET /v1/health/live` → `{"status": "alive"}` | `GET /v1/health/ready` → `{"status": "ready", "version": ...}`                        | `GET /v1/health` |

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Current Health Endpoints']

### JR-ML-API-037 — **API Surface**: 42+ REST methods + 2 WebSocket stream classes.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 221-228)

**Detail**:

- **Tests**: 208 passed, 84.48% coverage

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

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

### JR-CAS-API-013 — Cascor feature enhancements: CAS-001 through CAS-010 (separate epoch limits, max iterations, auto-snap, test optimization, hierarchy, population, vector DB).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 310-330)

**Detail**:

CAS-001: Extract spiral generator (✅ COMPLETE). CAS-002: Separate epoch limits for full network and candidates. CAS-003: Max train session iterations. CAS-004: Extract remote worker (✅ COMPLETE, juniper-cascor-worker). CAS-005: Extract common dependencies to modules. CAS-006: Auto-snap best network (accuracy ratchet). CAS-007: Optimize slow tests (≤5 min, 86-93% reduction via Phase 6). CAS-008: Network hierarchy management. CAS-009: Network population management. CAS-010: Snapshot vector DB storage. Status: CAS-001/004 COMPLETE, others NOT STARTED.

**Notes**:

[v2 remap: SE→API]

### JR-CAS-API-014 — CasCor service API must support separate network_epochs and candidate_epochs parameters.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 562-566)

**Notes**:

Requires API contract extension; juniper-cascor-client start_training() method update.

### JR-CAN-API-029 — Cascor swap_dataset_live endpoint pre-conditions: experimental gate enabled, training running, no swap in progress, dim change supported, shrink supported by phase set.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 93-101)

**Detail**:

Return 403 if gate disabled, 422 if not training/dim unsupported/shrink unsupported, 409 if swap already in progress.

**Notes**:

Failures between steps 4-14 trigger rollback; return 5xx with original error wrapped.

### JR-CAN-API-030 — CascorStateSync reads raw cascor responses and duplicates envelope-unwrapping logic instead of using adapter normalization methods, risking format drift.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 548-570)

**Detail**:

state_sync.py reads raw response without adapter; bypasses normalization methods. Should call adapter's _unwrap_envelope() and _first_defined() for standardization.

**Notes**:

State sync should accept adapter instead of raw client reference.

### JR-CAN-API-031 — Configure JuniperData client integration with JUNIPER_DATA_URL and docker-compose entry.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 209-232)

**Detail**:

JUNIPER_DATA_URL not in app_config.yaml; no docker-compose entry; no E2E test with live JuniperData service.

**Notes**:

Phase 2 high priority; client exists in Phase 4 deliverable but is not actively integrated

### JR-ML-API-048 — Deprecated `get_arc_agi_api()` has no `warnings.warn()` call.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 150-156)

**Detail**:

- `traces_sample_rate=1.0` sends all Sentry traces

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-API-049 — Dynamic import `from candidate_unit.candidate_unit import CandidateUnit` — fragile, no version check.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 314-327)

**Detail**:

| CW-01 | **Medium** | `worker.py`        | 225     | Timeout error sends `candidate_uuid: ""` instead of actual UUID from `candidate_data`                |

**Notes**:

[v4 brief repaired; was: '2.4 juniper-cascor-worker']

### JR-ML-API-050 — Effort**: 3-5 days | **Repos**: juniper-cascor, juniper-canopy.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 657-664)

**Detail**:

**Effort**: 3-5 days | **Repos**: juniper-cascor, juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '6.3 KL-1: Dataset Data in Service Mode']

### JR-ML-API-051 — Error parsing silently loses `{"error": "string"}` format messages — falls through to `response.text`.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 298-314)

**Detail**:

| CL-01 | **Medium** | `ws_client.py`              | 231–240  | `command()` vs `set_params()` message format inconsistency — `command()` never sends `"type"` field   |

**Notes**:

[v4 brief repaired; was: '2.3 juniper-cascor-client']

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

### JR-ML-API-054 — Fix Docker secret name: `juniper_data_api_key` → `juniper_data_api_keys` (or vice versa).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 442-452)

**Detail**:

| 6 | juniper-deploy | Add AlertManager service to docker-compose.yml                                           |

**Notes**:

[v4 brief repaired; was: '8.2 High (Fix Soon)']

### JR-CAN-API-032 — Fix uppercase status normalization gap in WebSocket relay path (ISS-06 architectural fragility).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 404-448)

**Detail**:

ISS-06 HIGH (latent). CasCor TrainingStateMachine.get_state_summary() returns UPPERCASE status (.name values: "STARTED", "PAUSED", "COMPLETED", "FAILED", "STOPPED"). _normalize_status() mapping lacks uppercase entries. Sync path calls .lower() before lookup (partially protected). Relay callback path (cascor_service_adapter.py:222) passes raw status with NO .lower() call — unprotected. When cascor broadcasts "STARTED" via WebSocket, relay's _normalize_status("STARTED") falls through to default "Stopped", incorrectly updating training_state. FakeCascorClient emits uppercase, so tests using fake client against relay path trigger this bug. Architectural risk: any future CasCor change to uppercase enum .name values via WebSocket would cause incorrect status.

**Notes**:

Post-validation finding: current production WebSocket state messages use title-case (protected). But vulnerability exists in test paths and is latent architectural fragility.

### JR-ML-API-055 — `generator.generate(params)` is synchronous inside async handler. Blocks event loop for large datasets (MNIST: 60K samples).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 159-169)

**Detail**:

| ID        | Severity   | File:Line                        | Description

**Notes**:

[v4 brief repaired; was: '3.1 Bugs']

### JR-ML-API-056 — **Guardrails**: Validate params against same whitelist as REST endpoint.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 182-207)

**Detail**:

**Severity**: S2 | **Effort**: Small (0.5 day) | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '3.3 CR-008: Implement WebSocket `set_params`']

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

### JR-ML-API-059 — Immediate (No Infrastructure Changes).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 721-727)

**Detail**:

1. **Refactor Canopy's backend branching**: Define a `BackendProtocol` that both `DemoMode` and `CascorServiceAdapter` implement. Eliminate scattered `if demo_mode_instance:` checks in `main.py

### JR-ML-API-060 — Inconsistency**: Health check endpoints differ (`/v1/health` vs `/v1/health/ready`). All should use `/v1/health` for liveness and….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 341-360)

**Detail**:

| Base image    | python:3.14-slim         | python:3.14-slim       | python:3.14-slim     |

**Notes**:

[v3 brief repaired from cited content; was: '4.4 Per-Service Dockerfile Review']

### JR-ML-API-061 — Issue**: Inconsistent endpoint availability. All services should implement the full set: `/v1/health` (basic), `/v1/health/live`….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 414-424)

**Detail**:

**Issue**: Inconsistent endpoint availability. All services should implement the full set: `/v1/health` (basic), `/v1/health/live` (liveness), `/v1/health/ready

**Notes**:

[v3 brief repaired from cited content; was: '7.1 Health Check Consistency']

### JR-ML-API-062 — M-JCC-3: Handshake not validated in `CascorControlStream.connect()` (`ws_client.py:178`).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 239-255)

**Detail**:

**M-JCC-1: `wait_for_ready()` calls `is_alive()` instead of `is_ready()`** (`client.py:86`)

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

### JR-ML-API-064 — Major features (dataset versioning CAN-DEF-005, batch endpoints CAN-DEF-006, Docker secrets, systemd support, Postgres concurrency fixes)….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 131-142)

**Detail**:

**H-JD-1: 60+ commits since v0.5.0 not in CHANGELOG**

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-CAN-API-033 — Normalize /api/metrics current snapshot endpoint; follows same broken path as metrics history (ISS-07).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 453-465)

**Detail**:

ISS-07 MODERATE. /api/metrics endpoint (current snapshot) calls cascor_service_adapter.py:86-94 get_current_metrics() which uses _normalize_metric() producing flat keys. Conceptually subset of ISS-01 — fixing _normalize_metric() output format automatically fixes both history and current snapshot endpoints.

**Notes**:

Phase 2 focused only on /api/metrics/history; missed current endpoint.

### JR-CAN-API-034 — Parameter map _CASCOR_TO_CANOPY_PARAM_MAP is asymmetric: forward maps nn_growth_convergence_threshold to patience, reverse maps patience to cn_training_convergence_threshold (different field).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 668-689)

**Detail**:

Generate reverse map programmatically: _CASCOR_TO_CANOPY_PARAM_MAP = {v: k for k, v in _CANOPY_TO_CASCOR_PARAM_MAP.items()}. Add bijectivity assertion to catch future duplicates.

**Notes**:

Causes param sync to apply updates to wrong canopy parameter.

### JR-ML-API-065 — Postgres and Redis stores not tested in CI (require live instances).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 198-206)

**Notes**:

[v3 brief repaired from cited content; was: '3.5 Test Coverage Gaps']

### JR-ML-API-066 — Radio items and checkboxes fire immediately but handler logic is O(1) comparisons.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 431-439)

**Notes**:

[v3 brief repaired from cited content; was: '7.3 Performance']

### JR-ML-API-067 — README API table (+6 methods), REFERENCE.md (version + batch/versioning), QUICK_START.md (FakeDataClient class name).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 286-294)

**Detail**:

| juniper-data-client   | README API table (+6 methods), REFERENCE.md (version + batch/versioning), QUICK_START.md (FakeDataClient class name) |

**Notes**:

[v4 brief repaired; was: '3.2 README & Documentation Updates']

### JR-ML-API-068 — **Recommendation**: Add a startup sweep that removes stale `juniper_train_*` blocks from `/dev/shm`.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 188-217)

**Detail**:

#### 1.4.1 Shared Memory Block Leaks

**Notes**:

[v3 brief repaired from cited content; was: '1.4 Shared Memory and Multiprocessing Issues']

### JR-ML-API-069 — Recommendation**: LOW PRIORITY — the 5-second poll will pick it up. Can be addressed as part of OI-2 (WebSocket push) which provides a more….

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 489-499)

**Detail**:

**Recommendation**: LOW PRIORITY — the 5-second poll will pick it up. Can be addressed as part of OI-2 (WebSocket push) which provides a more comprehensive solution.

**Notes**:

[v3 brief repaired from cited content; was: 'Fix']

### JR-ML-API-070 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 209-221)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 265-280)

**Detail**:

1. Bump version to 0.4.0 (new public API surface)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-API-071 — Remove `COPY conftest.py .` — conftest.py is already inside `tests/` which is copied on line 29.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 243-273)

**Detail**:

**2.6.1 Fix Makefile variables** (`Makefile:70-72`):

**Notes**:

[v3 brief repaired from cited content; was: '2.6 juniper-deploy: Makefile & Dockerfile Fixes']

### JR-ML-API-072 — Round-trip: apply -> state -> verify values match.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 492-503)

**Detail**:

| `DemoMode.apply_params()` accepts all new params  | Backend integration |

**Notes**:

[v4 brief repaired; was: '8.3 Integration Tests']

### JR-ML-API-073 — **Secret name/path mismatch**: Top-level `secrets` defines `juniper_data_api_key` (singular) but service env `JUNIPER_DATA_API_KEYS_FILE` po.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 260-272)

**Detail**:

| DD-DC-01 | **High**   | **Secret name/path mismatch**: Top-level `secrets` defines `juniper_data_api_key` (singular) but service env `JUNIPER_DATA_API_KEYS_FILE` points to `/run/secrets/juniper_data_api_k

**Notes**:

[v4 brief repaired; was: '5.1 Docker Compose Issues']

### JR-ML-API-074 — `self.clockwise = clockwise or self.clockwise or DEFAULT` — falsy `False`/`0` values silently overridden.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 107-118)

**Detail**:

| BUG-CC-01 | **MEDIUM** | `create_topology_message()` is dead code — topology changes never broadcast via WS | `src/api/websocket/messages.py:72`                                                | Defined and exported but zero production callers. Only used in tests

**Notes**:

[v4 brief repaired; was: '5.1 juniper-cascor']

### JR-ML-API-075 — Service Inventory.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 59-67)

**Detail**:

| **JuniperCascor** | 8200 | `python src/server.py`   | FastAPI + uvicorn        | Pydantic Settings (`JUNIPER_CASCOR_*` env vars)     |

### JR-CAN-API-035 — ServiceBackend.get_status() returns nested training status but dashboard expects flat keys (is_running, is_paused, phase, current_epoch, hidden_units).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 303-328)

**Detail**:

get_status() returns nested cascor structures. Must add _normalize_status_response() that transforms state_machine.status (title case) to is_running/is_paused/completed/failed boolean flags with epoch/hidden_units extraction.

**Notes**:

Status bar works via /api/status endpoint transformation; inconsistent when backend.get_status() called directly.

### JR-ML-API-076 — Store starts empty; `init_params_from_backend` repopulates on each page load.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 439-448)

**Detail**:

| `/api/state` response         | Old fields missing               | Always provide defaults via `.get()` with `TrainingConstants` fallbacks      |

**Notes**:

[v4 brief repaired; was: '7.4 Backward Compatibility']

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

### JR-ML-API-079 — Thin wrapper that operates on the target and all three services:.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 298-310)

**Detail**:

**New file**: `juniper-ml/scripts/juniper-all-ctl`

**Notes**:

[v3 brief repaired from cited content; was: '5.7 juniper-all-ctl (Step 2.6)']

### JR-ML-API-080 — Type-safe, validated configuration.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 663-713)

**Detail**:

The mixed approach (Pydantic Settings for two services, YAML for one) creates inconsistency. All three services are FastAPI-based, so Pydantic `BaseSettings` is the natural fit.

**Notes**:

[v3 brief repaired from cited content; was: 'Evaluation']

### JR-ML-API-081 — Update all broken existing tests.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 555-563)

**Detail**:

1. Update all broken existing tests

**Notes**:

[v4 brief repaired; was: 'Phase 5: Tests']

### JR-ML-API-082 — **Version**: 0.3.2 (code) — but no git tag exists for v0.3.2.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 169-176)

**Detail**:

- **Version**: 0.3.2 (code) — but no git tag exists for v0.3.2

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-ML-API-083 — **Version**: 0.5.0 (pyproject.toml) / 0.4.2 (**init**.py) / 0.4.0 (Dockerfile).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 108-115)

**Detail**:

- **Version**: 0.5.0 (pyproject.toml) / 0.4.2 (**init**.py) / 0.4.0 (Dockerfile)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-CAN-API-036 — WebSocket /ws/training connect-time message ordering is not atomic; initial_status/state messages can be preempted by background demo broadcasts.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 122-150)

**Detail**:

Handler sends connection_established, initial_status, state with await boundaries; client added to active_connections before all sends complete, allowing broadcast loop to inject metrics/state messages between. Enforce send ordering before client becomes visible to broadcasts.

**Notes**:

Currently mitigated on test side only; product-side ordering not enforced.

### JR-ML-API-084 — Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 77-77)

**Notes**:

Settled position C-40 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-085 — Work Unit 3: Pre-Existing Test Failures (MEDIUM) — IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 129-144)

**Detail**:

**Issues**: 3A (9 failing tests in `test_api_state_endpoint.py`)

### JR-ML-API-086 — Wrap `generator.generate()` in `asyncio.to_thread()` (PERF-01).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 452-468)

**Detail**:

| 10 | juniper-data          | Use `hmac.compare_digest()` for API key comparison (SEC-01)    |

**Notes**:

[v4 brief repaired; was: '8.3 Medium (Address in Next Sprint)']

### JR-ML-API-087 — Ecosystem-Wide Patterns.

**Status**: deferred  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 436-445)

**Detail**:

1. **No application has all git tags**: This is a systemic process gap. Releases are documented in changelogs but tags are not created, meaning GitHub releases and PyPI publishes may not ha

### JR-ML-API-088 — R5.6-THROTTLE (P3, deferred) on the carry-forward tracker.

**Status**: deferred  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 472-483)

**Detail**:

annotation `description` blocks (`alert_rules.yml:751`, `:819`). The

**Notes**:

[v3 brief repaired from cited content; was: '7.3 The 25-epoch throttle caveat']

### JR-ML-API-089 — Add `GET /v1/dataset/data` endpoint.

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 341-348)

**Detail**:

| `src/api/lifecycle/manager.py` | Add `get_dataset_data()` method     |

**Notes**:

[v4 brief repaired; was: '9.2 juniper-cascor (Phase 4 only)']

### JR-CAN-API-037 — candidate_learning_rate parameter unmapped in canopy (accessible via cascor API but not UI) (ISS-16).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 627-639)

**Detail**:

ISS-16 LOW. CasCor TrainingParamUpdateRequest accepts candidate_learning_rate as updatable field, but no canopy parameter maps to it in _CANOPY_TO_CASCOR_PARAM_MAP. Users cannot view or modify candidate learning rate from dashboard; parameter accessible via direct cascor API calls only.

**Notes**:

Identified by v4 (unique finding).

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

### JR-CAN-API-039 — Normalize parameter mapping: state sync params use raw cascor names instead of nn_*/cn_* namespace (ISS-12).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 556-568)

**Detail**:

ISS-12 MODERATE. During initial state sync (state_sync.py:98-103), training parameters stored using raw cascor parameter names (learning_rate, max_hidden_units, epochs_max) rather than mapped through _CASCOR_TO_CANOPY_PARAM_MAP to canopy namespace (nn_*/cn_*). When main.py:189-202 applies synced.params to parameter panel, dashboard receives cascor parameter names. Parameter panel labels may not match values, or values may not populate correctly.

**Notes**:

Identified by v7 (unique finding). Caused by ISS-13 (state sync bypasses adapter).

### JR-ML-API-090 — Phase 4 (cross-repo dataset endpoint).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 178-184)

**Detail**:

| Task 2 Phase 2: `GET /v1/dataset/data` endpoint in cascor | ❌ NOT STARTED |

### JR-REC-API-001 — Service train/predict/crossval referencing content-addressed datasets

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 363-375)
- `juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/training.py` (lines 37-49)

**Detail**:

Synchronous `POST /v1/train` (response = completion); `predict`/`crossval` reference `dataset_id` only (never bare `name`); crossval reuses the train hyperparameters for bench comparability. Raw pydantic response bodies (no envelope) — a deliberate contrast with cascor's `{status,data,meta}`.
