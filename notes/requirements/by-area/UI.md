# Requirements — UI

**Area**: ui-frontend — Canopy/Dash, UX, visualizations

**Total entries**: 114

**By status**: proposed=85 | designed=9 | in-progress=4 | shipped=14 | deferred=1 | rejected=1

**By priority**: P0=7 | P1=27 | P2=76 | P3=4

**By owner**: ml=78 | can=36

---

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

### JR-CAN-UI-001 — Canopy should not mutate incoming broadcast messages in websocket_manager.broadcast().

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 75-75)

**Detail**:

Issue 1.1.3: broadcast() currently mutates message dicts in-place.
Must pass immutable copy or deep clone before modification.

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

### JR-CAN-UI-004 — Fix network topology format mismatch: convert weight-oriented CasCor structure to graph-oriented visualizer contract.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Service-mode emits weight-oriented topology (input_size, hidden_units: [...]) while visualizer expects graph-oriented structure (input_units, connections). Critical display blocker.

**Notes**:

P5-RC-02; critical display blocker; part of final synthesis

### JR-CAN-UI-005 — Candidate info section must display and be collapsible with historical pool tracking.

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase1/README.md` (lines 27-93)

**Detail**:

P1-1 feature: always-visible section with toggle icon, historical pools rendered as collapsed cards, top 10 pools maintained.
Implemented in metrics_panel.py with dbc.Collapse wrapper and callback handlers.

**Notes**:

Phase 1 complete feature; shipped status verified from implementation notes.

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

### JR-CAN-UI-007 — Phase 2 polish features: visual indicators, image downloads, HDF5 snapshots, About tab (70 tests, 2247 passed).

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase2/README.md` (lines 1-100)

**Detail**:

P2-1: Visual indicator for most recently added node (pulsing glow, edge highlighting). P2-2: Unique name suggestion for image downloads (timestamp-based filename). P2-3: About Tab for Juniper Cascor Backend (version, license, credits, docs links). P2-4: HDF5 Snapshot Tab - List Available Snapshots (sortable table, auto-refresh). P2-5: HDF5 Tab - Show Snapshot Details (metadata, attributes, error handling). Status: all COMPLETE, 70 new tests, 2247 total passed, 95%+ coverage.

**PRs**: #204

### JR-CAN-UI-008 — Phase 3 Wave 1 HDF5 snapshot capabilities: create, restore, history with validation (102 tests, 2413 passed).

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_DESCRIPTION_PHASE3-WAVE-1_2026-01-09.md` (lines 1-100)

**Detail**:

P3-1: Create New Snapshot with name/description inputs and success feedback. P3-2: Restore from Existing Snapshot with validation and confirmation modal. P3-3: Snapshot History with create/restore/delete action logging. New endpoints: POST /api/v1/snapshots, POST /api/v1/snapshots/{id}/restore, GET /api/v1/snapshots/history. 102 new tests, 2413 passed, 93% coverage.

**PRs**: #215

**Notes**:

[v2 ARCH→UI re-bucket]

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

### JR-ML-UI-004 — Fix dataset display bug with comprehensive development plan.

**Status**: in-progress  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN-FINAL.md` (lines 1-100)

**Notes**:

FINAL revision; check for duplicate with DEVELOPMENT_PLAN.md

### JR-ML-UI-005 — Fix decision boundary visualization in Canopy UI with implementation approach addressing NaN propagation and numerical instability.

**Status**: in-progress  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_DECISION_BOUNDARY_FIX_PLAN_V2.md` (lines 1-100)

**Notes**:

V2 revision addressing issues from initial plan.

### JR-ML-UI-006 — [ ] Dashboard works when served from non-`localhost:8050` deployment path.

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1594-1615)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '14.4 Visual Verification Checklist']

### JR-ML-UI-007 — Final resolution**: **CRITICAL**. The network topology visualization is completely non-functional in service mode — the validation guard….

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1110-1118)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '7.2 Topology Severity: CRITICAL vs MODERATE']

### JR-CAN-UI-010 — Meta Parameters enhancement: rename Training Parameters to Meta Parameters with NN and Candidate Nodes subsections (22 components).

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 1-100)

**Detail**:

Restructure parameters card into two collapsible subsections: Neural Network (12 inputs: max iterations, learning rate, hidden units, growth trigger, convergence threshold, spiral params, dataset elements/noise) and Candidate Nodes (10 inputs: pool size, correlation threshold, selected candidates, training radio, iterations, convergence threshold, multi-candidate selection, candidate selection radio, top/random candidates count). Single shared Apply Parameters button. Cross-section checkbox linking (Multi-Node Layers ↔ Multi Candidate Selection).

**Design**:

Collapsible card structure with 22 component IDs, 10 Dash callbacks for toggles/radio/checkbox sync, theme constants (NEW/CHANGED/REMOVED tracking). Test plan includes unit and integration tests.

### JR-ML-UI-008 — Requires=juniper-data.service.

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 630-669)

**Detail**:

After=network-online.target juniper-data.service

**Notes**:

[v3 brief repaired from cited content; was: '9.7 Detailed Design: systemd Units']

### JR-ML-UI-009 — The Juniper Canopy system has **multiple distinct ingress paths** for data into the dashboard, each independently determining its output….

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1191-1205)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '8.1 The Fundamental Problem (Consensus Across All Proposals)']

### JR-ML-UI-010 — 12: Background tab memory spike.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 386-387)

**Notes**:

[v2 ARCH→UI re-bucket]

### JR-CAN-UI-011 — Accuracy plot phase band logic must be deduplicated.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 93-93)

**Detail**:

Issue 1.3.3: Repeated phase-band visualization logic in metrics_panel.py.
Extract to shared helper. File: src/frontend/components/metrics_panel.py

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

### JR-CAN-UI-012 — Code review audit plan (R5-01 aligned): 34 gaps, 22 REAFFIRMED, 1 SUPERSEDED, 4 DEFERRED, 7 COORDINATED with R5-01 phases.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_AUDIT_PLAN_2026-04-12_R5-01-aligned.md` (lines 1-100)

**Detail**:

Re-evaluates 34 gaps from original audit (91 issues, 57 verified, 16 partially fixed, 18 not fixed) against R5-01 Canonical Development Plan. Dispositions: REAFFIRMED (22 gaps, original remediation applies — Cassandra/Redis, test quality, dataset/torch/training state, frontend), SUPERSEDED (1 gap, HIGH-005 sync HTTP → R5-01 Phase B), DEFERRED (4 gaps, DashboardManager extraction, ThemeColors rollout, Dockerfile decisions), COORDINATED (7 gaps with specific R5-01 phases: Phase 0-cascor, Phase B, Phase C).

**Notes**:

[v2 ARCH→UI re-bucket] 22 REAFFIRMED gaps mostly completed via PR #146. DEFERRED gaps tracked as accepted technical debt. COORDINATED gaps require synchronization with R5-01 phase owners.

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

### JR-ML-UI-012 — End of audit report.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 549-566)

**Detail**:

12. **Add shared memory startup sweep**: On cascor server startup, remove stale `juniper_train_*` blocks from `/dev/shm`.

**Notes**:

[v3 brief repaired from cited content; was: '7.3 Long-Term (Low/Architectural)']

### JR-CAN-UI-014 — Implement decision boundary visualization for real CasCor backend in Canopy dashboard.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 88-118)

**Detail**:

The /api/decision_boundary endpoint retrieves prediction function from cascor_integration but never computes the grid. Must implement grid computation mirroring demo mode logic.

**Notes**:

Dataset/Decision Boundary tab shows "No data available" when connected to real CasCor backend

### JR-ML-UI-013 — In `_process_dataset_update()`, add metadata-only branch:.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 137-151)

**Detail**:

**File:** `src/frontend/components/dataset_plotter.py`

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Fix — Phase 1: Canopy Graceful Degradation (canopy-only)']

### JR-CAN-UI-015 — Network visualizer screenshot timestamp must not be static.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 92-92)

**Detail**:

Issue 1.3.2: Screenshot PNG contains hardcoded timestamp instead of actual
capture time. Must update on every screenshot. File: src/frontend/components/network_visualizer.py

### JR-CAN-UI-016 — Numeric input typing vs spinner mismatch; universal debounce=True confuses Apply-button enable indicator.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 44-45)

**Detail**:

Fix: canopy frontend component refactor. Debounce logic does not properly track which fields changed relative to current backend state.

**Notes**:

UX issue; component refactor required.

### JR-ML-UI-014 — Phase 1 (canopy-only) — COMPLETE.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 160-168)

**Detail**:

| Fix pre-existing test failures (5 in `test_response_normalization.py`) | ✅ Fixed       | Backlog Sprint 1 |

### JR-ML-UI-015 — Phase B: Browser bridge drains /ws/training into Dash store, Plotly.extendTraces updates, polling killed, GAP-WS-24a/b latency pipe.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-94)

**Notes**:

Phase B major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-016 — Phase I: Asset cache busting; bump assets_url_path / hash query param.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-102)

**Notes**:

Phase I major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-CAN-UI-017 — Replace debounce=True with 350ms on numeric inputs to fix perceived typing lag.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 365-499)

**Detail**:

Issue: spinner changes commit immediately but typed values require blur.
Solution: use debounce=350ms for live feedback without callback churn.
Also adds clientside blur-on-Apply and validation styling (invalid=True border).

**PRs**: PR-2 (Phase 6B, Issue

### JR-ML-UI-017 — The Meta Parameters card will be 2-3x taller than the current Training Parameters card. Guardrails:.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 448-460)

**Notes**:

[v3 brief repaired from cited content; was: '7.5 UI Overflow']

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

### JR-ML-UI-018 — Paths in `juniper_plant_all.bash` and `juniper_chop_all.bash` are already configurable via environment variables from Phase 1. No….

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 67-107)

**Detail**:

Paths in `juniper_plant_all.bash` and `juniper_chop_all.bash` are already configurable via environment variables from Phase 1. No additional work needed.

**Notes**:

[v3 brief repaired from cited content; was: '2.7 Step 2.7 (configurable paths) -- already done']

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

### JR-CAN-UI-024 — Redefine pool training metrics around correlation statistics instead of loss/accuracy.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 396-440)

**Detail**:

CasCor trains on correlation, not loss/accuracy; these metrics do not exist for candidate pool. Replace with avg_correlation, max_correlation, min_correlation, std_correlation, success_rate.

**Notes**:

Phase 3 P2 fix; doc status COMPLETE; requires UI schema change

### JR-ML-UI-019 — **stale label** — bridge SHIPPED via juniper-cascor#188 (`heartbeat_age_seconds`) and gpu via the same collector; this placeholder panel pre.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 310-330)

**Detail**:

| Request Latency — p50 / p95 / p99 | timeseries | `histogram_quantile(...)` against the shared HTTP duration histogram | |

**Notes**:

[v4 brief repaired; was: '6.1 juniper-overview.json (14 panels, version 3, title "Juni']

### JR-ML-UI-020 — Fix candidate training display rendering issues in Canopy.

**Status**: in-progress  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md` (lines 1-100)

### JR-ML-UI-021 — Fix Canopy dashboard display issues with layout and rendering.

**Status**: in-progress  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_DASHBOARD_DISPLAY_FIXES.md` (lines 1-100)

### JR-ML-UI-022 — Add a `dbc.RadioItems` or `dbc.ButtonGroup` toggle to the NetworkVisualizer's control panel:.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 536-555)

**Detail**:

Add a `dbc.RadioItems` or `dbc.ButtonGroup` toggle to the NetworkVisualizer's control panel:

**Notes**:

[v3 brief repaired from cited content; was: 'Design']

### JR-ML-UI-023 — Closed by **OBS-WIRE-01 / juniper-canopy#234** which swapped the add.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 249-257)

**Detail**:

Per audit finding C.1 (juniper-canopy): canopy's `RequestIdMiddleware`

**Notes**:

[v3 brief repaired from cited content; was: '4.3 RequestIdMiddleware boundary placement']

### JR-ML-UI-024 — Implement contextual menu and candidate tab design for Canopy UI.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CONTEXTUAL_MENU_AND_CANDIDATE_TAB_DESIGN.md` (lines 1-100)

### JR-ML-UI-025 — `task_timeout` env override logic: if user explicitly passes `--task-timeout 3600` (the default value), code falls through to env var. Can't.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 105-114)

**Detail**:

| ID        | Severity   | File:Line              | Description

**Notes**:

[v4 brief repaired; was: '2.1 Bugs']

### JR-ML-UI-026 — Canopy dashboard self-call refactor: defer weight display, implement metrics playback, option C trigger conditions.

**Status**: deferred  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md` (lines 1-50)

### JR-ML-UI-027 — All services handle signals adequately at the application level. The gap is in the orchestration scripts that don't verify shutdown….

**Status**: rejected  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 453-468)

**Detail**:

All services handle signals adequately at the application level. The gap is in the orchestration scripts that don't verify shutdown completed.

**Notes**:

[v3 brief repaired from cited content; was: '7.5 Shutdown Signal Handling']

### JR-ML-UI-028 — A.1 Startup Scripts.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 818-831)

**Detail**:

| `util/juniper_plant_all.bash`    | juniper-ml     | Start all (host)    | Active (overhauled, commit `03aec86`) |

### JR-CAN-UI-025 — About panel documentation links must be validated and repaired.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 170-170)

**Detail**:

Issue 3.3.3: Broken or outdated documentation links in About panel.
Audit all links and update URLs or remove invalid references.

### JR-ML-UI-029 — Add indeterminate progress animation during candidate training.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 534-543)

**Detail**:

**Effort**: 2 days | **Repo**: juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '5.4 Canopy Progress Indicators']

### JR-ML-UI-030 — Add symlink `scripts/juniper-ctl` -> `juniper-canopy-ctl`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 107-128)

**Detail**:

- ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8050

**Notes**:

[v3 brief repaired from cited content; was: '5.1 juniper-canopy changes (Step 2.3)']

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

### JR-ML-UI-039 — Contrast with service adapter (`cascor_service_adapter.py` lines 617-621):.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 361-385)

**Detail**:

**File**: `juniper-canopy/src/backend/demo_backend.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

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

### JR-ML-UI-040 — Debounce lives in Dash clientside callback, NOT SDK.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 66-66)

**Notes**:

Settled position C-29 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-041 — **Decision**: Rename canopy's `juniper-ctl` to `juniper-canopy-ctl` for consistency.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 38-46)

**Detail**:

**Decision**: Rename canopy's `juniper-ctl` to `juniper-canopy-ctl` for consistency.

**Notes**:

[v3 brief repaired from cited content; was: '2.4 CLI naming convention']

### JR-ML-UI-042 — **Decision**: Use `Wants=` (not `Requires=`).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 26-32)

**Detail**:

**Decision**: Use `Wants=` (not `Requires=`).

**Notes**:

[v3 brief repaired from cited content; was: '2.2 juniper-all.target: Wants= vs Requires=']

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

### JR-ML-UI-044 — Dependency Graph (Runtime).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 76-85)

### JR-ML-UI-045 — Design and implement integrated dashboard combining Canopy and CasCor metrics.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/INTEGRATED_DASHBOARD_PLAN.md` (lines 1-100)

### JR-ML-UI-046 — Each radio group controls `disabled` state of associated inputs:.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 257-267)

**Detail**:

- **NN Growth Trigger**: `"preset_epochs"` enables preset-epochs-input, disables convergence-threshold-input; `"convergence"` reverses

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Radio Button Enable/Disable Pattern']

### JR-ML-UI-047 — **File**: `juniper-canopy/src/backend/state_sync.py` (lines 125-135) — correctly fetches and transforms topology.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 479-485)

**Detail**:

**File**: `juniper-canopy/src/backend/state_sync.py` (lines 125-135) — correctly fetches and transforms topology.

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-CAN-UI-029 — Hardcoded colors must be extracted to theme_constants.py for DRY.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 168-168)

**Detail**:

Issue 3.3.1: Color strings repeated across components. Extract to
theme_constants.py for centralized management and dark/light theme support.

### JR-ML-UI-048 — In demo mode, networks with 2+ hidden units display an **incomplete topology** — missing the signature cascade connections between hidden….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 385-389)

**Detail**:

In demo mode, networks with 2+ hidden units display an **incomplete topology** — missing the signature cascade connections between hidden units. The visualization appears as a standard feedforward network rather than a cascade correlation network.

**Notes**:

[v3 brief repaired from cited content; was: 'Consequence']

### JR-ML-UI-049 — Issue Summary Table.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 42-54)

**Detail**:

| **OI-5** | LOW | Quality | Initial sync topology never pushed to Dash store | juniper-canopy | **FIXED** (2beea5c) — fallback in `ServiceBackend.get_network_topology()` |

### JR-ML-UI-050 — KL-1: Dataset Scatter Plot Empty in Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1963-1977)

### JR-CAN-UI-030 — Modulo toggle for theme switching must use Dash State, not module-level flag.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 169-169)

**Detail**:

Issue 3.3.2: Theme toggle using module-level variable instead of callback State.
Can cause race conditions in multi-user scenarios. Use dcc.Store for theme state.

### JR-ML-UI-051 — NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 58-58)

**Notes**:

Settled position C-21 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-052 — **New file**: `juniper-cascor/scripts/juniper-cascor-ctl`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 253-263)

**Detail**:

**New file**: `juniper-cascor/scripts/juniper-cascor-ctl`

**Notes**:

[v3 brief repaired from cited content; was: '5.5 juniper-cascor-ctl (Step 2.5)']

### JR-ML-UI-053 — **New file**: `juniper-ml/scripts/juniper-all.target`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 263-298)

**Detail**:

**New file**: `juniper-ml/scripts/juniper-all.target`

**Notes**:

[v3 brief repaired from cited content; was: '5.6 juniper-all.target (Step 2.6)']

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

### JR-ML-UI-054 — Per `JUNIPER_2026-03-30_JUNIPER-CANOPY_DEPENDENCY-UPDATE-WORKFLOW.md`, after adding `get_dataset_data()` to juniper-cascor-client:.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 187-200)

**Detail**:

Per `JUNIPER_2026-03-30_JUNIPER-CANOPY_DEPENDENCY-UPDATE-WORKFLOW.md`, after adding `get_dataset_data()` to juniper-cascor-client:

**Notes**:

[v3 brief repaired from cited content; was: '3.4 Dependency Update When Adding Client Method']

### JR-ML-UI-055 — Per-IP WebSocket connection limit — setting not found in cascor codebase.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 356-364)

**Detail**:

| `cascade_add` correlation           | NETWORK_TOPOLOGY_DISPLAY_ANALYSIS | Hardcoded `0.0` instead of actual best candidate correlation             |

**Notes**:

[v4 brief repaired; was: 'High Priority']

### JR-ML-UI-056 — Phase 1: Foundation (Constants + Settings).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 522-528)

**Detail**:

1. Update `canopy_constants.py` with all new and changed constants

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

### JR-ML-UI-059 — Phases C–H — ❌ NOT STARTED.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 341-356)

**Detail**:

## 12. Items Not Yet Implemented

### JR-ML-UI-060 — **Push vs. poll architecture**: The WebSocket infrastructure exists but key events (topology changes) still require REST polling. This creat.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 464-472)

**Detail**:

1. **Push vs. poll architecture**: The WebSocket infrastructure exists but key events (topology changes) still require REST polling. This creates unnecessary latency and server load.

**Notes**:

[v4 brief repaired; was: '5.2 Weaknesses']

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

### JR-CAN-UI-032 — Remove dead _create_candidate_pool_display from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 160-160)

**Detail**:

Issue 3.2.1: Dead code left in MetricsPanel. Remove or document why retained.
File: src/frontend/components/metrics_panel.py

**Notes**:

[v2 ARCH→UI re-bucket]

### JR-ML-UI-062 — Renamed to `nn-growth-convergence-threshold-input`.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 84-99)

**Detail**:

## 3. Constants Changes (`canopy_constants.py`)

**Notes**:

[v4 brief repaired; was: '2.4 Removed Component IDs']

### JR-ML-UI-063 — Resolved**: Previously, `juniper_plant_all.bash` used `/opt/miniforge3/envs/JuniperCanopy/bin/python` for all services. Fixed in commit….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 434-444)

**Detail**:

**Resolved**: Previously, `juniper_plant_all.bash` used `/opt/miniforge3/envs/JuniperCanopy/bin/python` for all services. Fixed in commit `03aec86` — each service

**Notes**:

[v3 brief repaired from cited content; was: '7.3 Conda Environment Mapping']

### JR-ML-UI-064 — `RETRY_ALLOWED_METHODS` includes `POST`/`DELETE` — retrying mutations can cause duplicates. Currently safe (server is idempotent) but should.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 229-239)

**Detail**:

| ID       | Severity   | File:Line             | Description

**Notes**:

[v4 brief repaired; was: '4.2 Code Quality']

### JR-ML-UI-065 — Same color support, error handling, resource monitoring.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 184-195)

**Detail**:

**New file**: `juniper-data/scripts/juniper-data-ctl`

**Notes**:

[v3 brief repaired from cited content; was: '5.3 juniper-data-ctl (Step 2.4)']

### JR-ML-UI-066 — `--slient` typo in `wake_the_claude.bash:108` (should be `--silent`).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 78-89)

**Detail**:

- `--slient` typo in `wake_the_claude.bash:108` (should be `--silent`)

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-UI-067 — `src/conf/app_config.yaml` + `${VAR:default}` substitution.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 655-663)

**Detail**:

| **JuniperCanopy** | YAML config + env vars  | `src/conf/app_config.yaml` + `${VAR:default}` substitution |

**Notes**:

[v4 brief repaired; was: 'Current State']

### JR-ML-UI-068 — Step 2: Validate Existing Fixes.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 70-95)

**Detail**:

| B-5.1 | `_apply_parameters_handler` stores `"enabled" in (conv_enabled or [])` → correct boolean. No continuous sync. |

### JR-ML-UI-069 — **Strengths**: Fixes demo mode topology to match CasCor architecture.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 389-431)

**Detail**:

#### Approach A: Add cascade connections to demo backend (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

### JR-ML-UI-070 — **Tests**: 88 passed (60 + 11 + 17 Python) + 1 bash regression.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 41-48)

**Detail**:

- **Version**: 0.3.0 (pyproject.toml)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

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

### JR-ML-UI-073 — This document was produced by cross-referencing 34 source documents across the Juniper ecosystem:.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 488-504)

**Detail**:

| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker      | 🔴 Open |

**Notes**:

[v3 brief repaired from cited content; was: '15.3 juniper-cascor-worker']

### JR-ML-UI-074 — `_toggle_cn_multi_candidate_subgroup_handler` checkbox unchecked disables all.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 471-492)

**Notes**:

[v4 brief repaired; was: '8.2 Unit Tests - Callback Handlers']

### JR-ML-UI-075 — Two collapsible subsections with 22 total input components, radio button groups for mutually exclusive options, conditional enable/disable….

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 31-39)

**Detail**:

## 2. Component ID Registry

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: 'Target State']

### JR-ML-UI-076 — UI Lock and Visualization: UI locking during training and visualization improvements.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CANOPY_PROPOSAL-08-UI-LOCK-AND-VISUALIZATION.md` (lines 1-45)

### JR-ML-UI-077 — v1.0.0–v2.0.0 Primary Sources.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 504-513)

**Detail**:

| 1 | `JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md`  | `juniper-ml/notes/development/`     | 2026-04-17 | 91+ items from 16 source documents      |

### JR-ML-UI-078 — Work Unit 1: Worktree Developer Experience (HIGH).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 41-83)

**Detail**:

**Impact**: Unblocks all worktree-based development workflows

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
