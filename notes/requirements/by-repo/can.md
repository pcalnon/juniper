# Requirements — juniper-canopy (can)

**Total entries**: 215

**By status**: proposed=180 | designed=1 | shipped=34

**By priority**: P0=19 | P1=89 | P2=74 | P3=33

**By category**: TEST=44 | API=39 | UI=36 | OBS=19 | SEC=12 | TRAIN=12 | DOC=10 | ARCH=10 | LOCK=6 | WS=6 | DEP=6 | PERF=5 | OPS=5 | DATA=4 | TOOL=1

---

### JR-CAN-OBS-001 — Prometheus histogram bucket rationale: canopy_ws_browser_latency_ms with SLO candidates (p95<25ms, p99<100ms).

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-95)

**Detail**:

WebSocket browser latency metric with 10 buckets [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000] ms mapping to UX thresholds: 5ms (sub-frame 200Hz), 10ms (100Hz frame), 25ms (60Hz display jitter boundary), 50ms (perceived instant threshold), 100ms (noticeable lag, Nielsen), 250ms-5s (degradation signals). SLO candidates: p95 training-WS RTT<25ms, p99 control-WS RTT<100ms. Status: tentative pending R5.1 ratification.

**Notes**:

METRICS-MON sub-track R4.1. May reshape upper buckets (2.5s, 5s) post-R5.1.

### JR-CAN-SEC-001 — API key validation must use hmac.compare_digest() to prevent timing attacks.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 43-43)

**Detail**:

Issue 0.1.2: Replace string 'in' operator with constant-time comparison.
File: src/security.py

### JR-CAN-SEC-002 — CallbackContextAdapter must be thread-safe via contextvars.ContextVar.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 50-50)

**Detail**:

Issue 0.2.1: Replace instance attributes with contextvars.ContextVar to ensure
thread isolation. File: src/frontend/callback_context.py

### JR-CAN-UI-001 — Canopy should not mutate incoming broadcast messages in websocket_manager.broadcast().

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 75-75)

**Detail**:

Issue 1.1.3: broadcast() currently mutates message dicts in-place.
Must pass immutable copy or deep clone before modification.

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

### JR-CAN-SEC-003 — Exception handler must suppress internal details; log full stack server-side only.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 45-45)

**Detail**:

Issue 0.1.3: Return generic message to client, preserve full exception in
server-side logs only. Prevents information disclosure.

### JR-CAN-API-002 — Fix /ws exception handling infinite loop in main.py.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 73-73)

**Detail**:

Issue 1.1.1: WebSocket route exception handling loop. Must exit cleanly
on expected errors (client disconnect) without retry loop.
File: src/main.py

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

### JR-CAN-PERF-001 — Rate limiter must evict expired entries periodically to prevent memory leak.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 47-49)

**Detail**:

Issue 0.1.4: Add _evict_expired() method with periodic cleanup.
Emergency size cap: 10,000 entries. File: src/security.py

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

### JR-CAN-SEC-006 — Threading.Event replacement race must use clear() instead of reassignment.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 52-53)

**Detail**:

Issue 0.2.2: In demo_mode.py, use _stop.clear() instead of _stop = Event()
to avoid TOCTOU race. File: src/demo_mode.py

### JR-CAN-SEC-007 — API key timing attack must use hmac.compare_digest() for constant-time comparison.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 79-83)

**Detail**:

HIGH-001: Replace simple set membership check with hmac.compare_digest() in both browser CSRF auth and adapter HMAC auth.
R5-01 Section 4.1 mandates this pattern; remediation already correct per analysis.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; reinforced by R5-01 canonical pattern.

### JR-CAN-UI-005 — Candidate info section must display and be collapsible with historical pool tracking.

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase1/README.md` (lines 27-93)

**Detail**:

P1-1 feature: always-visible section with toggle icon, historical pools rendered as collapsed cards, top 10 pools maintained.
Implemented in metrics_panel.py with dbc.Collapse wrapper and callback handlers.

**Notes**:

Phase 1 complete feature; shipped status verified from implementation notes.

### JR-CAN-SEC-008 — Exception handler must use opaque error messages and add CRLF escaping in audit logs.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 84-88)

**Detail**:

HIGH-002: Generic error messages + server-side logging per R5-01 Section 4.3 (M-SEC-06).
Add CRLF escaping in audit logs per M-SEC-07 when logs echo client input.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; shipped with opaque messages pattern.

### JR-CAN-TRAIN-003 — External CasCor development plan phases 0-7: characterization, adapter normalization, backend sync, parameter mapping, dataset/topology adapters, integration validation.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_1/5b_DEVELOPMENT_PLAN_EXTERNAL_CASCOR_FIX.md` (lines 100-200)

**Detail**:

Comprehensive 7-phase plan validating RC-1 through RC-5 root causes and implementing systematic fixes. Phase 0: characterization tests validating root causes. Phase 1: adapter normalization layer. Phase 2: ServiceBackend status normalization. Phase 3: CascorStateSync structure navigation. Phase 4: parameter mapping cleanup. Phase 5: metric history normalization. Phase 6: dataset and topology adapters. Phase 7: integration validation.

**PRs**: #146

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAN-DOC-001 — Four standardized documentation templates must be provided for roadmaps, issue tracking, PRs, and release notes.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_DESCRIPTION_POST_REFACTOR_v0.24.0_2026-01-11.md` (lines 20-31)

**Detail**:

TEMPLATE_DEVELOPMENT_ROADMAP.md, TEMPLATE_ISSUE_TRACKING.md, TEMPLATE_PULL_REQUEST_DESCRIPTION.md, TEMPLATE_RELEASE_NOTES.md.
All with placeholders, consistency enforcement for future documentation.

**Notes**:

Shipped in v0.24.0; verified as part of POST_REFACTOR_VERIFICATION report.

### JR-CAN-API-006 — Implement cascor_service_adapter normalization adapters (ResponseEnvelope, metrics, status, parameters).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_1/5b_DEVELOPMENT_PLAN_EXTERNAL_CASCOR_FIX.md` (lines 1-150)

**Detail**:

7-phase development plan Phase 1: Adapter normalization (_unwrap_envelope, _normalize_metric, _normalize_metrics_history). Phase 2: ServiceBackend status normalization (flat dict builder). Phase 3: CascorStateSync fix (navigate real cascor nested structure). Phase 4: Parameter map cleanup (generate reverse map).

**PRs**: #146

### JR-CAN-TEST-001 — Integration and enhancements PR v0.31.0+: CasCor backend, JuniperData, 4-phase test suite, CI/CD parity (80 commits, 28,855 LOC).

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_DESCRIPTION_INTEGRATION_AND_ENHANCEMENTS_2026-02-18.md` (lines 1-100)

**Detail**:

Consolidates 80 commits delivering: CasCor backend (async training, remote workers), JuniperData (REST client, Docker Compose), 4-phase test suite (42+ integration, 20+ unit, 13+ regression), CI/CD parity. 182 files changed, 28,855 net LOC additions.

**PRs**: #146

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-CAN-DATA-001 — JuniperCanopy ↔ JuniperData integration: replace local client with shared package, mandatory JUNIPER_DATA_URL, schema mismatch fixes

**Status**: shipped  **Priority**: P1  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/history/CANOPY_JUNIPER_DATA_INTEGRATION_PLAN.md` (lines 1-100)

**Detail**:

Critical integration plan Phase 0 (CRITICAL): Replace local client with shared package, make JUNIPER_DATA_URL mandatory, fix schema mismatch. Phase 1 (HIGH): Add to app_config.yaml, API key auth, retry/backoff, NPZ validation. Phase 2 (MEDIUM): Docker compose, constants, health check. Phase 3 (MEDIUM): Dataset selector, management API, multiple generators. Status: Phase 0+1 COMPLETE, 71 new tests, 3,276 passed.

**PRs**: #146

### JR-CAN-LOCK-001 — Lockfile must include --extra observability to prevent Dependabot PR failures in CI.

**Status**: shipped  **Priority**: P1  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` (lines 145-155)

**Detail**:

CRIT-003: .github/workflows/lockfile-update.yml does not pass --extra observability to pip-compile;
causes CI failures when Dependabot updates dependencies.
Fix: Add --extra observability flag to lockfile-update workflow.

**Notes**:

CODE_REVIEW_ANALYSIS v0.4.0; critical CI/CD blocker for regular dependency updates.

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

### JR-CAN-UI-006 — Network topology visualization must support staggered hidden node layout with wave pattern positioning.

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase1/README.md` (lines 175-244)

**Detail**:

P1-3 feature: staggered layout option in dropdown; first node at center, alternating outward left/right.
Dynamic spread increases with node count (up to 3.0 max). Centered between input/output columns.
Implemented via _compute_staggered_positions() method in network_visualizer.py.

**Notes**:

Phase 1 complete feature; shipped status verified.

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

### JR-CAN-TEST-002 — Phase 1 Complete—Eliminated 9 false-positive assert True tests.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 18-24)

**Detail**:

Epic 1.1: Removed all assert True patterns from test_button_responsiveness.py,
test_button_state.py, and others. Epic 1.2: Moved 5 non-test files (test_yaml.py,
test_dashboard_init.py, etc.) to util/verify_*.py. Epic 1.3: Fixed security scan
suppression (removed || true from bandit, updated pip-audit to strict mode).

### JR-CAN-TEST-003 — Phase 2 Complete—Consolidated fixtures and enabled MyPy/linting on tests.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 25-30)

**Detail**:

Epic 2.1: Single source of truth for test fixtures. Epic 2.2: Re-enabled critical
MyPy error codes (arg-type, return-value, assignment). Epic 2.3: Enabled flake8
linting on test files with relaxed configuration.

### JR-CAN-UI-007 — Phase 2 polish features: visual indicators, image downloads, HDF5 snapshots, About tab (70 tests, 2247 passed).

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase2/README.md` (lines 1-100)

**Detail**:

P2-1: Visual indicator for most recently added node (pulsing glow, edge highlighting). P2-2: Unique name suggestion for image downloads (timestamp-based filename). P2-3: About Tab for Juniper Cascor Backend (version, license, credits, docs links). P2-4: HDF5 Snapshot Tab - List Available Snapshots (sortable table, auto-refresh). P2-5: HDF5 Tab - Show Snapshot Details (metadata, attributes, error handling). Status: all COMPLETE, 70 new tests, 2247 total passed, 95%+ coverage.

**PRs**: #204

### JR-CAN-TEST-004 — Phase 3 Complete—Fixed weak tests, unconditional skips, exception suppression.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 31-39)

**Detail**:

Epic 3.1: Reduced in [200, 503] permissive patterns from 21 to 5. Epic 3.2: Converted
9 unconditional skips to conditional with documentation (ADR-001). Epic 3.3: Fixed
5 exception suppression patterns. Epic 3.4: Re-enabled B905, F401, B008. Epic 3.5:
Removed duplicate test classes. Epic 3.6: Converted bug-documenting tests to xfail.

### JR-CAN-UI-008 — Phase 3 Wave 1 HDF5 snapshot capabilities: create, restore, history with validation (102 tests, 2413 passed).

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_DESCRIPTION_PHASE3-WAVE-1_2026-01-09.md` (lines 1-100)

**Detail**:

P3-1: Create New Snapshot with name/description inputs and success feedback. P3-2: Restore from Existing Snapshot with validation and confirmation modal. P3-3: Snapshot History with create/restore/delete action logging. New endpoints: POST /api/v1/snapshots, POST /api/v1/snapshots/{id}/restore, GET /api/v1/snapshots/history. 102 new tests, 2413 passed, 93% coverage.

**PRs**: #215

**Notes**:

[v2 ARCH→UI re-bucket]

### JR-CAN-TEST-005 — Phase 4 Complete—Config standardization, docs, MyPy improvements, suppress review.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 40-45)

**Detail**:

Epic 4.1: Standardized coverage fail_under to 80%, re-enabled pytest warnings.
Epic 4.2: Enabled markdown linting, created TEST_DIRECTORY_STRUCTURE.md, fixed
docstrings. Epic 4.3: Re-enabled 9 MyPy codes (call-arg, override, no-redef, etc),
reduced disabled codes from 15 to 7. Epic 4.4: Reviewed contextlib.suppress patterns,
added clarifying comments.

### JR-CAN-WS-001 — R5-01 Canonical Development Plan integration: 11 phases of WebSocket, security, architectural work aligned with code audit gaps.

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-12_R5-01-aligned.md` (lines 1-100)

**Detail**:

Reorganizes remediation timeline to coordinate with R5-01 Canonical Development Plan. 4 tracks: PRE (complete via PR #146), PAR (parallel with R5-01), EMB (R5-01 phase-embedded), POST (deferred). 11 R5-01 phases including WebSocket bridge, security hardening, frontend wiring, parameter adapter. Tracks dependencies, timelines (Weeks 1-12+), resource allocation, metrics.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CAN-PERF-002 — Rate limiter memory leak must be fixed with periodic eviction of expired counters.

**Status**: shipped  **Priority**: P1  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 89-93)

**Detail**:

HIGH-003 HTTP-level rate limiter: Add periodic eviction to prevent unbounded memory growth.
Note: R5-01 Phase B adds separate WS-level single-bucket rate limiter (10 tokens, 10 cmd/sec) - do not delete HTTP limiter.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; shipped with HTTP rate limiter; WS limiter in Phase B.

### JR-CAN-UI-009 — Replay controls must support playback at variable speeds (1x, 2x, 4x) with progress slider.

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase1/README.md` (lines 95-172)

**Detail**:

P1-2 feature: ⏮ go-to-start, ◀ step-back, ▶ play/pause, ⏩ step-forward, ⏭ go-to-end, speed selector.
Replay state machine: stopped → playing → paused → stopped. Visibility controlled by training state.
Implemented with dcc.Store for replay-state and interval timer.

**Notes**:

Phase 1 complete feature; shipped status verified.

### JR-CAN-OPS-001 — Startup regression analysis and fixes: JuniperData lifecycle, env var expansion, namespace collision, config convention mismatches.

**Status**: shipped  **Priority**: P1  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/REGRESSION_ANALYSIS_STARTUP_FAILURE_2026-02-09.md` (lines 1-100)

**Detail**:

Root causes: RC-1 missing JuniperData service lifecycle management, RC-2 ${VAR:default} syntax unsupported by os.path.expandvars, RC-3 shell-to-Python environment namespace collision, RC-4 CASCOR_DEMO_MODE value convention mismatch. Fixes: script-level service management, custom config expansion, shell variable filtering, startup validation.

**PRs**: #146

### JR-CAN-TEST-006 — Test suite must achieve 2908 tests passing with 99% pass rate and 93%+ coverage across all components.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_DESCRIPTION_POST_REFACTOR_v0.24.0_2026-01-11.md` (lines 50-80)

**Detail**:

34 roadmap items (Phases 0-3) verified complete with 2908 tests passed, 34 skipped, 0 failed.
Coverage by component: redis_panel 100%, redis_client 97%, cassandra_client 97%, cassandra_panel 99%,
websocket_manager 100%, statistics 100%, dashboard_manager 95%, training_monitor 95%,
training_state_machine 96%, hdf5_snapshots_panel 95%, about_panel 100%, main.py 84%.

**Notes**:

v0.24.0 shipped; main.py gap noted as requiring real CasCor backend or uvicorn runtime.

### JR-CAN-TEST-007 — Test suite remediation: fix 67 non-passing tests (54 ERROR, 10 FAILED, 3 XFAIL) → 3,215 passed, 37 skipped.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/FIX_FAILING_TESTS.md` (lines 1-100)

**Detail**:

Comprehensive test remediation addressing 54 ERROR tests (missing pytest-mock), 10 FAILED tests (snapshot attributes, race conditions, server-dependent), 3 XFAIL tests (logger VERBOSE, empty YAML). Result: 3,215 passed, 0 failed, 37 skipped. Includes race condition fixes in test_polling_interval, test_websocket_connect, test_snapshot_restore.

**PRs**: #146

### JR-CAN-UI-010 — Meta Parameters enhancement: rename Training Parameters to Meta Parameters with NN and Candidate Nodes subsections (22 components).

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 1-100)

**Detail**:

Restructure parameters card into two collapsible subsections: Neural Network (12 inputs: max iterations, learning rate, hidden units, growth trigger, convergence threshold, spiral params, dataset elements/noise) and Candidate Nodes (10 inputs: pool size, correlation threshold, selected candidates, training radio, iterations, convergence threshold, multi-candidate selection, candidate selection radio, top/random candidates count). Single shared Apply Parameters button. Cross-section checkbox linking (Multi-Node Layers ↔ Multi Candidate Selection).

**Design**:

Collapsible card structure with 22 component IDs, 10 Dash callbacks for toggles/radio/checkbox sync, theme constants (NEW/CHANGED/REMOVED tracking). Test plan includes unit and integration tests.

### JR-CAN-UI-011 — Accuracy plot phase band logic must be deduplicated.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 93-93)

**Detail**:

Issue 1.3.3: Repeated phase-band visualization logic in metrics_panel.py.
Extract to shared helper. File: src/frontend/components/metrics_panel.py

### JR-CAN-TEST-008 — Add browser-automation UI test sub-suite with dedicated CI lane.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 45-46)

**Detail**:

No browser automation harness exists. Create pytest sub-suite with ≤5 min
wall-clock budget via parallel jobs, caching, and slow marker. Skeleton
in Phase 4 step 1, full coverage in Phase 4 step 2.

**PRs**: PR-4.1 (skeleton with basic page loads), {'PR-4.2 (full coverage': 'param Apply, dataset swap, snapshot restore)'}

### JR-CAN-TEST-009 — Add integration test suite for real CasCor backend code paths with mocked CascorIntegration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 191-207)

**Detail**:

conftest.py forces CASCOR_DEMO_MODE=1 for all tests; no test exercises cascor_integration paths. Would have caught INT-CRIT-001/002/003.

**Notes**:

Phase 2 high priority; must test control, topology, metrics, statistics, decision boundary, snapshots

### JR-CAN-WS-002 — Add missing fields to WebSocket relay state callback (current_epoch, current_step, learning_rate, max_hidden_units, max_epochs, network_name, timestamp).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 261-290)

**Detail**:

ISS-02 MODERATE. WebSocket relay state callback (cascor_service_adapter.py:218-225) only forwards status and phase to global training_state. CasCor state messages also contain current_epoch, current_step, learning_rate, max_hidden_units, max_epochs, network_name, timestamp — all discarded. TrainingState.update_state() accepts **kwargs and can handle these fields. Result: /api/state reads from training_state.get_state() with stale epoch/step data after initial sync (though status bar makes fresh REST calls, bypassing staleness).

**Notes**:

Currently latent because status bar makes fresh REST calls. Mitigating factor masks the bug in production but architectural risk remains.

### JR-CAN-DOC-002 — Application version must be centralized via importlib.metadata.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 83-83)

**Detail**:

Issue 1.2.1: Version string currently duplicated across health, status, and
config endpoints. Use importlib.metadata as single source of truth.
File: src/main.py

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

### JR-CAN-ARCH-001 — CallbackContextAdapter must use contextvars.ContextVar for thread-safe and async-safe test mode isolation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` (lines 99-143)

**Detail**:

CRIT-002 concurrency vulnerability: instance attributes in CallbackContextAdapter not thread-safe.
Current fix (contextvars) implemented correctly; recommendation reinforced to use ContextVar pattern.

**Notes**:

CODE_REVIEW_ANALYSIS v0.4.0; fixed with contextvars.ContextVar in alignment with R5-01 philosophy.

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

### JR-CAN-TEST-012 — CI must upload coverage reports to Codecov.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 117-117)

**Detail**:

Issue 2.1.5: .github/workflows/ci.yml missing Codecov step. Add upload
after test run for coverage tracking and status badges.

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

### JR-CAN-DOC-003 — Configuration must have no version string mismatches (app_config.yaml, pyproject.toml).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 84-86)

**Detail**:

Issues 1.2.2, 1.2.3: Update app_config.yaml version to 0.4.0 and pyproject.toml
header version comment to match. Should be single source via importlib.metadata.

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

### JR-CAN-API-015 — Define Pydantic model for set_params endpoint request body.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 77-77)

**Detail**:

Issue 1.1.5: set_params endpoint lacks formal request schema. Add Pydantic
model for validation. File: src/main.py. Updates OpenAPI documentation.

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

### JR-CAN-TEST-013 — FakeCascorClient.update_params snapshots _network_config to _training_params['params'] at init but update_params does not sync updates, causing verify-roundtrip mismatches.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 41-119)

**Detail**:

When update_params({'learning_rate': 0.005}) is called, _network_config is updated but _training_params['params'] stale snapshot is not, causing get_training_params() to return original value. Workaround: update both locations in FakeCascorClient.update_params.

**PRs**: #264

**Notes**:

Upstream fix pending in juniper-cascor-client. Test currently uses idle scenario workaround.

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

### JR-CAN-API-022 — Implement save_snapshot() and load_snapshot() methods on CascorIntegration class.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 146-166)

**Detail**:

Methods do not exist; code falls through to minimal HDF5 fallback that only stores metadata, not network state. Must delegate to CasCor's CascadeHDF5Serializer.

**Notes**:

Snapshot save/load in real backend mode produces incomplete snapshots

### JR-CAN-OBS-005 — Logger wrapper instances must be cached to avoid re-wrapping overhead.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 152-152)

**Detail**:

Issue 3.1.2: Wrapper created fresh on each logger.info/debug call. Cache
wrapper per logger instance to improve performance.

### JR-CAN-API-023 — Middleware must handle malformed Content-Length header gracefully.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 78-78)

**Detail**:

Issue 1.1.6: Non-numeric or negative Content-Length can crash request parsing.
Add bounds check and return 400 Bad Request. File: src/middleware.py

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

### JR-CAN-API-027 — Remove duplicate cn_patience configuration parameter.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 76-76)

**Detail**:

Issue 1.1.4: cn_patience appears twice in configuration. Consolidate to single
canonical definition. File: src/main.py

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

### JR-CAN-OBS-008 — Sentry sample rate must be configurable via environment variable.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 153-153)

**Detail**:

Issue 3.1.3: Sentry sample_rate hardcoded. Add SENTRY_SAMPLE_RATE env var
with sensible default (0.1 for production, 1.0 for dev).

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

### JR-CAN-UI-018 — About tab must display version, license, credits, documentation links, and collapsible system information.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_PHASE2_PARTIAL_2026-01-07.md` (lines 74-100)

**Detail**:

P2-3 feature: new about_panel.py component showing version 2.2.0, MIT License, author/algorithm/tech credits,
links to docs/API/environment setup, GitHub contact, Python/platform/arch in collapsible section.
Integrated into dashboard_manager as fifth tab.

**Notes**:

Phase 2 feature; shipped with 27 tests, 95%+ coverage maintained.

### JR-CAN-UI-019 — Image download from Network Topology must use timestamp-based filename (juniper_topology_YYYYMMDD_HHMMSS.png).

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_PHASE2_PARTIAL_2026-01-07.md` (lines 55-72)

**Detail**:

P2-2 feature: replaces Plotly default "newplot" with unique timestamped name.
High resolution 2x scale for crisp PNG exports.
Implemented via toImageButtonOptions in dcc.Graph config.

**Notes**:

Phase 2 feature; shipped with 4 tests.

### JR-CAN-UI-020 — Must support zero-copy metadata parameter updates between Canopy and Cascor.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 56-162)

**Detail**:

Candidate-pool invariants form a constrained triple (selected_candidates,
top_candidates, random_candidates) that must be validated atomically in cascor.
Post-merge validation required for multi-key PATCH (e.g. {S: 6, T: 4, R: 2}).
Validation helper _validate_candidate_pool_triple() enforces 6 invariants.

**Notes**:

Shipped as part of Phase 6A remediation (Issue #1 / can-001 implementation).
Candidate-pool semantics confirmed 2026-05-09.

### JR-CAN-UI-021 — New node visual indicator must show pulsing glow (cyan #17a2b8, 1s period) and edge highlighting (50% opacity).

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_PHASE2_PARTIAL_2026-01-07.md` (lines 24-50)

**Detail**:

P2-1 feature: animated glow on new hidden node addition; state machine (none → active → fading → none).
Highlight persists until different node selected; 2-second linear fade when triggered.
Implemented via new-node-highlight dcc.Store and interval-based callback.

**Notes**:

Phase 2 feature; shipped with 17 tests, visual regression verification recommended.

### JR-CAN-UI-022 — Phase 3 Wave 1—HDF5 snapshot capabilities (create, restore, history).

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 75-211)

**Detail**:

P3-1: Create new snapshot endpoint (POST /api/v1/snapshots) with auto-generated
timestamp names and demo mode support. P3-2: Restore endpoint with training state
validation and WebSocket broadcast. P3-3: History tracking (append-only JSONL log).
Status: all complete as of 2026-01-10.

### JR-CAN-UI-023 — Phase 3 Wave 2—Training Metrics Save/Load layouts and 3D topology visualization.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 402-599)

**Detail**:

P3-4: Save/load metric panel configuration as named presets (GET/POST/DELETE
/api/v1/metrics/layouts endpoints). P3-5: Toggle 2D/3D network topology view
with layer-based z-axis, circular layout for >4 hidden nodes, weight-based edge coloring.

**PRs**: {'PR-series': 'Wave 2 (37 new tests, coverage maintained 93%+)'}

### JR-CAN-OBS-009 — Phase 3 Wave 3—Redis and Cassandra cluster monitoring tabs.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 604-897)

**Detail**:

P3-6: Redis monitoring (health badge, memory/ops/hit-rate metrics, auto-refresh).
P3-7: Cassandra cluster overview (contact points, hosts table, keyspace/table metrics).
Both integrate new backend clients (redis_client.py, cassandra_client.py),
optional integration with soft-fail on missing libraries.

**PRs**: {'PR-series': 'Wave 3 (93 new tests, 640+ total for Phase 3)'}

### JR-CAN-UI-024 — Redefine pool training metrics around correlation statistics instead of loss/accuracy.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 396-440)

**Detail**:

CasCor trains on correlation, not loss/accuracy; these metrics do not exist for candidate pool. Replace with avg_correlation, max_correlation, min_correlation, std_correlation, success_rate.

**Notes**:

Phase 3 P2 fix; doc status COMPLETE; requires UI schema change

### JR-CAN-TEST-023 — 9+ skipped/placeholder tests contain only pass or skip decorator without real test logic.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

**Detail**:

Placeholder tests with no assertions or logic do not test anything. Must implement real test logic or remove.

**Notes**:

Identified in test audit; blocks coverage.

### JR-CAN-UI-025 — About panel documentation links must be validated and repaired.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 170-170)

**Detail**:

Issue 3.3.3: Broken or outdated documentation links in About panel.
Audit all links and update URLs or remove invalid references.

### JR-CAN-TEST-024 — Add integration tests for async/sync boundary with WebSocket responsiveness during training.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 168-189)

**Detail**:

No integration tests verify WebSocket responsiveness during active training; schedule_broadcast() uses run_coroutine_threadsafe but has no tests.

**Notes**:

Phase 2 high priority; training callbacks are registered but untested in integration context

### JR-CAN-API-028 — All JuniperData REST API interactions must have standardized error handling with status code mapping.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 199-211)

**Detail**:

Map HTTP status codes to user-friendly error messages; implement consistent retry and timeout patterns.
Estimated scope: 2-3 files, 100-200 lines.

**Notes**:

CAN-HIGH-006; HIGH priority post-release item.

### JR-CAN-PERF-003 — API timeout must be reduced for fast-interval callbacks.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 176-176)

**Detail**:

Issue 3.4.1: Default API timeout too long for frequently-polled endpoints.
Set shorter timeout (2-5s) for metrics/state endpoints, keep longer (10s) for
heavy operations like dataset upload.

### JR-CAN-DATA-003 — Architecture adapter must handle dataset-triggered shape changes: equal-dim (no-op), grow-only (append nodes), shrink (prepend adapter layer)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 122-126)

**Detail**:

Method: adapt_for_dataset_swap(network, before_dims, after_dims) → ArchChanges. Three cases: (1) equal I/O dims—no work, (2) grow only—append nodes to outermost input/output layer, (3) shrink—prepend new dataset-side adapter layer.

**Notes**:

[v2 ARCH→DATA re-bucket] Returns ArchChanges struct for training history persistence.

### JR-CAN-TEST-025 — Async/sync boundary (ThreadPoolExecutor fit_async, start_training_background) must have dedicated test coverage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 157-168)

**Detail**:

No tests for concurrent start requests, executor shutdown during training, exception propagation across boundary.
Estimated scope: 1-2 test files, 200-300 lines.

**Notes**:

CAN-HIGH-003; HIGH priority post-release item.

### JR-CAN-OPS-002 — Background coverage runs exceed 300s timeout, requiring CI harness tuning.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 35-35)

**Detail**:

Operational issue, not a code defect. Suggest increasing test harness timeout or optimizing coverage runner.

**Notes**:

Operational tuning only.

### JR-CAN-ARCH-004 — Bypass state sync normalization fragility: CascorStateSync uses raw client, bypassing adapter layer (ISS-13).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 571-585)

**Detail**:

ISS-13 MODERATE. ServiceBackend.initialize() (service_backend.py:189) creates CascorStateSync with raw JuniperCascorClient instance (self._adapter._client), bypassing entire normalization layer. Means: metrics_history stored without _normalize_metric() (ISS-05); training params stored with raw cascor names without _CASCOR_TO_CANOPY_PARAM_MAP (ISS-12); training status partially normalized but with uppercase gap (ISS-06 on sync path). Structural cause underlying ISS-05, ISS-06, ISS-12. Sync module should either go through adapter or replicate normalization logic.

**Notes**:

Identified by v7. This is the architectural fragility enabling cascading issues.

### JR-CAN-TRAIN-004 — Candidate pool handling on dataset swap: Option C selected—abandon all candidates and force output-training-first mode on new dataset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 128-131)

**Detail**:

After architecture adaptation, drop candidate pool. Submit new training future with mode='output_training_first' forcing immediate output training on new dataset before any new candidate-pool training.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Alternative options (keep candidates, retrain on new data) considered and rejected.

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

### JR-CAN-TEST-026 — CI/CD configuration disables 15+ MyPy type checking codes and excludes tests from flake8/mypy, hiding type errors.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 195-235)

**Detail**:

.pre-commit-config.yaml excludes tests from type checking. ci.yml uses || true on bandit, warnings-only on pip-audit. Must enable strict type checking for tests.

**Notes**:

Allows type errors to ship.

### JR-CAN-DOC-005 — Code quality, frontend, security, CI/CD audit domains: 8-domain audit with 15 gaps identified (11 NOT fixed, 4 partially, 1 documentation).

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_AUDIT_PLAN_2026-04-12.md` (lines 1-100)

**Detail**:

Comprehensive audit across 8 domains: Security, Concurrency, CI/CD, App Logic, Backend Services, Code Quality/Frontend, Observability/Logging, Test Quality. Registry of CRIT-001 through LOW-022 issues mapping to severity (Critical, High, Medium, Low), category, file, phase, claimed status. Most issues have proposed fixes ranging from straightforward (add lock, fix hardcoded value) to complex (restructure component, redesign exception handling).

### JR-CAN-API-031 — Configure JuniperData client integration with JUNIPER_DATA_URL and docker-compose entry.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 209-232)

**Detail**:

JUNIPER_DATA_URL not in app_config.yaml; no docker-compose entry; no E2E test with live JuniperData service.

**Notes**:

Phase 2 high priority; client exists in Phase 4 deliverable but is not actively integrated

### JR-CAN-TEST-027 — Consolidate duplicate conftest.py fixtures into single configuration file.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 122-128)

**Detail**:

Two conftest.py files (445 + 224 lines) contain overlapping fixtures. Consolidate to avoid duplication and maintenance burden.

**Notes**:

Category D: Duplicate fixtures; DRY principle violation

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

### JR-CAN-TRAIN-005 — Demo cascor training loss plateaus at ~0.24 after first hidden unit despite 6+ units added; root causes include vanilla SGD vs Adam and mini-batch issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 120-185)

**Detail**:

RC-9: Vanilla SGD vs Adam. RC-10: Mini-batch between cascades undoes full-batch retrain. RC-11: Un-normalized covariance vs Pearson. RC-12: Spiral complexity. Recommended fix: Adam + autograd (Option 4B).

**Notes**:

Remediation code examples provided in source document.

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

### JR-CAN-OBS-013 — Extract create_empty_plot() as shared utility across metric panels.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 162-162)

**Detail**:

Issue 3.2.3: create_empty_plot logic duplicated in multiple components.
Extract to plot_utils.py or equivalent shared module.

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-CAN-API-032 — Fix uppercase status normalization gap in WebSocket relay path (ISS-06 architectural fragility).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 404-448)

**Detail**:

ISS-06 HIGH (latent). CasCor TrainingStateMachine.get_state_summary() returns UPPERCASE status (.name values: "STARTED", "PAUSED", "COMPLETED", "FAILED", "STOPPED"). _normalize_status() mapping lacks uppercase entries. Sync path calls .lower() before lookup (partially protected). Relay callback path (cascor_service_adapter.py:222) passes raw status with NO .lower() call — unprotected. When cascor broadcasts "STARTED" via WebSocket, relay's _normalize_status("STARTED") falls through to default "Stopped", incorrectly updating training_state. FakeCascorClient emits uppercase, so tests using fake client against relay path trigger this bug. Architectural risk: any future CasCor change to uppercase enum .name values via WebSocket would cause incorrect status.

**Notes**:

Post-validation finding: current production WebSocket state messages use title-case (protected). But vulnerability exists in test paths and is latent architectural fragility.

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

### JR-CAN-TEST-028 — Integration tests use time.sleep(0.2)-based timing for synchronization across multiple files; fragile and platform-dependent.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 30-30)

**Detail**:

Three sites hardened in PR #264; more remain. Sleep-based timing should be replaced with event-driven synchronization or pytest fixtures.

**Notes**:

Audit recommended for codebase-wide cleanup.

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

### JR-CAN-TEST-029 — main.py test coverage must increase from 84% to 95% target for critical paths.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 234-246)

**Detail**:

Gap is primarily in real-backend code paths and error handling branches not exercised in demo mode.
Estimated scope: 1-2 test files, 200-300 lines.

**Notes**:

CAN-HIGH-008; HIGH priority post-release item.

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

### JR-CAN-OBS-014 — Multiple hardcoded localhost:8050 URLs in MetricsPanel (6+ instances) prevent non-local deployment and cross-origin access.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 415-445)

**Detail**:

Lines 1050, 1075, 1085, 1095, 1105, 1110 reference hardcoded localhost:8050. Must use environment variable or configuration endpoint.

**Notes**:

Blocks deployment to non-localhost targets.

### JR-CAN-TEST-031 — Multiple test files contain 25+ exception suppressions (try/except pass) that hide real errors and should be replaced with proper assertions.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

**Detail**:

Suppressions mask failures and prevent test failures from surfacing. Must audit and replace with proper error handling and assertions.

**Notes**:

Identified in test audit as 25+ suppression sites.

### JR-CAN-ARCH-005 — NetworkVisualizer callback is overloaded and must be split.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 172-172)

**Detail**:

Issue 3.3.5: Single callback handles too many inputs. Split into separate
callbacks for layout changes, theme changes, and data updates.

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

### JR-CAN-TEST-034 — Re-enable MyPy error codes currently disabled (15 codes); fix underlying type issues.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 160-165)

**Detail**:

.pre-commit-config.yaml disables 15 MyPy error codes, reducing type checking effectiveness. Phase 2 work to fix underlying issues, then re-enable codes.

**Notes**:

Category H: 15 codes disabled; type safety issue

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

### JR-CAN-DOC-007 — Remove commented-out imports across codebase.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 164-164)

**Detail**:

Issue 3.2.5: Commented imports clutter code. Remove or restore with rationale.

### JR-CAN-UI-032 — Remove dead _create_candidate_pool_display from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 160-160)

**Detail**:

Issue 3.2.1: Dead code left in MetricsPanel. Remove or document why retained.
File: src/frontend/components/metrics_panel.py

**Notes**:

[v2 ARCH→UI re-bucket]

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

### JR-CAN-TEST-037 — Remove || true suppression from Bandit security scan in CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 150-155)

**Detail**:

ci.yml line 412: bandit || true suppresses security issues silently. Security should not fail silently.

**Notes**:

Category G: Security scan gap; best practices violation

### JR-CAN-API-035 — ServiceBackend.get_status() returns nested training status but dashboard expects flat keys (is_running, is_paused, phase, current_epoch, hidden_units).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_MERGED_EXTERNAL_CASCOR_DEV_PLAN_v1.md` (lines 303-328)

**Detail**:

get_status() returns nested cascor structures. Must add _normalize_status_response() that transforms state_machine.status (title case) to is_running/is_paused/completed/failed boolean flags with epoch/hidden_units extraction.

**Notes**:

Status bar works via /api/status endpoint transformation; inconsistent when backend.get_status() called directly.

### JR-CAN-SEC-011 — Snapshot endpoints must sanitize names and confine paths to prevent directory traversal attacks.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` (lines 53-95)

**Detail**:

CRIT-001 vulnerability: /api/v1/snapshots endpoints allow path traversal via ../../ and URL-encoded sequences.
Remediation: Add _sanitize_snapshot_name() with regex ^[a-zA-Z0-9_-]+$; verify resolved path stays within _snapshots_dir.

**Notes**:

CODE_REVIEW_ANALYSIS v0.4.0; path sanitization + path confinement (defense in depth) recommended.

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

### JR-CAN-TEST-038 — Test non-test files exist in test directory; test_yaml.py, test_config.py, test_dashboard_init.py, test_and_verify_button_layout.py, implementation_script.py should be moved or removed.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

**Detail**:

Five non-test files found in test directory that should either be moved to appropriate location or deleted. Cleans up test structure.

**Notes**:

Identified in test audit.

### JR-CAN-TEST-039 — Test suite contains 9 false-positive tests (assert True only) masking actual test failures.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 85-130)

**Detail**:

False positives in test_button_responsiveness.py (4 instances), test_button_state.py (1), test_metrics_panel_coverage.py (1), test_dashboard_manager.py (1), test_config_refactoring.py (1), test_candidate_visibility.py (1). Each contains only assert True statement.

**Notes**:

Must be replaced with real test assertions or removed.

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

### JR-CAN-DOC-008 — Add deprecation warnings to remaining legacy env validators.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 227-227)

**Detail**:

Issue 5.1.1: Legacy env var validators need deprecation warnings.
Use warnings.warn() to alert users of upcoming removal.

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

### JR-CAN-LOCK-004 — CASCOR_SNAPSHOT_DIR env var must be migrated to JUNIPER_CANOPY_SNAPSHOT_DIR.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 229-229)

**Detail**:

Issue 5.1.3: Old env var still referenced. Support both for compatibility
but document migration path and plan removal date.

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

### JR-CAN-OPS-004 — Double initialization on fallback-to-demo path: backend.initialize() called twice (ISS-18).

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 667-683)

**Detail**:

ISS-18 LOW. In main.py:165-180, when CasCor probe fails and backend falls back to demo mode, backend.initialize() called once inside fallback block (line 177) and again unconditionally (line 180). For DemoBackend, initialize() calls self._demo.start() starting training simulation thread. Could start two threads or produce unexpected state. In practice, DemoBackend.initialize() appears idempotent, so code smell rather than active bug. Only affects fallback-to-demo path (cascor unreachable).

**Notes**:

Identified by v6. v5 confirmed asynccontextmanager runs sequentially so demo state sync executes correctly after fallback.

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

### JR-CAN-API-039 — Normalize parameter mapping: state sync params use raw cascor names instead of nn_*/cn_* namespace (ISS-12).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 556-568)

**Detail**:

ISS-12 MODERATE. During initial state sync (state_sync.py:98-103), training parameters stored using raw cascor parameter names (learning_rate, max_hidden_units, epochs_max) rather than mapped through _CASCOR_TO_CANOPY_PARAM_MAP to canopy namespace (nn_*/cn_*). When main.py:189-202 applies synced.params to parameter panel, dashboard receives cascor parameter names. Parameter panel labels may not match values, or values may not populate correctly.

**Notes**:

Identified by v7 (unique finding). Caused by ISS-13 (state sync bypasses adapter).

### JR-CAN-LOCK-006 — Pre-commit hook suite must be auto-updated.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 253-253)

**Detail**:

Issue 5.4.3: pre-commit hooks may be outdated. Run `pre-commit autoupdate`
to refresh all hook versions and update .pre-commit-config.yaml.

### JR-CAN-TEST-043 — Pytest tests use CWD-relative paths instead of fixture-based or absolute paths, causing Docker-environment failures.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 31-31)

**Detail**:

One file fixed; codebase-wide audit not done. CWD-relative paths fail in container contexts where CWD differs.

**Notes**:

One file fixed; more audit needed.

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

### JR-CAN-WS-006 — Training WebSocket must validate message size to prevent DoS.

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 243-243)

**Detail**:

Issue 5.3.2: WebSocket message handler does not check message size.
Add check: reject messages > 1MB with log and graceful disconnect.

### JR-CAN-DOC-010 — UI_STANDARDS.md document must be created to codify design constants (sidebar widths, spacing, color scheme) across dashboard components.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 1-50)

**Detail**:

Currently no centralized design standards; sidebar width hardcoded to dbc.Col(width=3) for all tabs. Create ui_standards.py module and notes/UI_STANDARDS.md documenting spacing, colors, responsive breakpoints.

**Notes**:

Enables consistent design across application.
