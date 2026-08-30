# Requirements — status: designed

**Total entries**: 97

**By priority**: P0=5 | P1=67 | P2=18 | P3=7

**By category**: ARCH=33 | OBS=12 | SEC=12 | WS=11 | TRAIN=10 | UI=9 | DEP=6 | TEST=2 | API=1 | TOOL=1

**By owner**: ml=93 | cas=3 | can=1

---

## Requirements with Status: Designed, List

### JR-ML-OBS-003 — P5-RC-05 (frontend WebSocket consumption) is STILL OPEN, not deferred — high-volume / low-latency metrics and the bidirectional `set_params` control channel depend on it

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 574-619)

**Detail**:

> - 2026-04-10 first pass: typed contract landed (PR #140); P5-RC-05 marked DEFERRED

**Notes**:

[v3 brief repaired from cited content; was: '6.0 Phase 4 Execution Results (2026-04-10, REVISED)']

[2026-08-29 brief repaired from cited content; was: '>   per the canopy requirements (high-volume / low-latency metrics and the.']

### JR-ML-SEC-003 — Issue Remediations, Section 4.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-A-SECURITY-CONCURRENCY-ERROR.md` (lines 9-59)

**Detail**:

#### SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel

### JR-ML-SEC-004 — Issue Remediations, Section 7.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 9-59)

**Detail**:

#### CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode

### JR-ML-SEC-005 — Issue Remediations, Section 8.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 127-177)

**Detail**:

#### Phase E: Backpressure Pump Tasks

### JR-ML-OBS-004 — Status**: **PARTIAL (2026-04-10)** — typed contract done; WebSocket consumption still open. See….

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 556-574)

**Detail**:

- [x] Dashboard shows per-epoch loss during output training phases — `train_output_layer` callback wired in cascor `manager.py:237-248`; demo mode emits via `_emit_training_metrics()` (verified 2026-04-09)

**Notes**:

[v3 brief repaired from cited content; was: '5.6 Phase 3 Success Criteria']

### JR-ML-ARCH-008 — """Service current metrics must use same nested format as demo mode.""".

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1505-1554)

**Notes**:

[v3 brief repaired from cited content; was: '14.2 New Contract Tests (FIX-K)']

### JR-ML-OBS-020 — 20+ log calls per `CandidateUnit.__init__` × pool_size = 160+ per grow iteration.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 420-433)

**Detail**:

| **Forward pass**        | ✅ Optimized     | Pre-allocated buffer (OPT-1) eliminates N `torch.cat()` calls                    |

**Notes**:

[v4 brief repaired; was: '4.1 juniper-cascor Performance']

### JR-ML-UI-006 — [ ] Dashboard works when served from non-`localhost:8050` deployment path.

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1594-1615)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '14.4 Visual Verification Checklist']

### JR-ML-SEC-052 — [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](../../legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md) — full program tracker (CLOSED 2026-05-03).

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 439-448)

**Detail**:

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — program-close note (PR juniper-ml#192)

**Notes**:

[v3 brief repaired from cited content; was: 'Primary']

### JR-ML-WS-015 — [§2.9 Security Model (REQUIRED)](../../code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md#29-security-model-required-before-phase-d).

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 21-45)

**Notes**:

[v3 brief repaired from cited content; was: '0.2 Table of Contents'] WebSocket/messaging architecture gap or design

### JR-ML-ARCH-009 — Add `set_phase()` method or support `current_phase` updates.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1629-1635)

**Notes**:

[v4 brief repaired; was: '15.2 juniper-cascor — Required (cross-repo)']

### JR-ML-ARCH-010 — Add `_to_dashboard_metric()` as described in P5-RC-01 detail. Apply in both:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1307-1357)

**Notes**:

[v3 brief repaired from cited content; was: '11. Consolidated Fix Recommendations']

### JR-ML-ARCH-011 — Add `_to_dashboard_metric()` in `get_recent_metrics()`, `get_current_metrics()`; add `_transform_topology()` in `extract_network_topology()`.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1618-1628)

**Notes**:

[v4 brief repaired; was: '15.1 juniper-canopy — Required']

### JR-ML-TRAIN-012 — Align fake responses/status values with real CasCor once contract tests exist.

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1636-1642)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v4 brief repaired; was: '15.3 Optional / Recommended Cleanup']

### JR-ML-ARCH-012 — All line numbers and code patterns in this document were independently verified against the current codebase HEAD:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1656-1673)

**Notes**:

[v3 brief repaired from cited content; was: '16.1 Code Validation Results']

### JR-ML-ARCH-013 — Analysis**: 7/7 consensus on P5-RC-01, P5-RC-04, P5-RC-05 (the original Phase 2 findings). 12 issues found by only 1-2 of the 7 proposals,….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1068-1096)

**Notes**:

[v3 brief repaired from cited content; was: '6.3 Phase 3 Proposal Agreement Matrix']

### JR-ML-ARCH-014 — Improved `juniper_plant_all.bash` / `juniper_chop_all.bash`: health polling, port and conda-env validation, /proc-based PID checks, graceful SIGTERM→SIGKILL

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 603-617)
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 617-630)

**Detail**:

`# 1. wait_for_health() function that polls /v1/health with configurable timeout`

**Notes**:

[v3 thin-brief flagged] [v4 brief repaired; was: '9.5 Detailed Design: Improved `juniper_plant_all.bash`']

---

[v3 thin-brief flagged] [v4 brief repaired; was: '9.6 Detailed Design: Improved `juniper_chop_all.bash`']

*Merged from 2 extraction candidates (slices: 3c-2b).*

[2026-08-29 brief repaired from cited content; was: '```bash ```.']

### JR-ML-ARCH-015 — Both Phase 5 proposals unanimously agree, and this final document adopts without change:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 208-221)

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Unanimous Findings Preserved in Final Document']

### JR-ML-DEP-008 — CASCOR_SERVER_URL: ws://juniper-cascor:8200/ws/v1/workers.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 689-714)

**Detail**:

context: ../juniper-cascor-worker

**Notes**:

[v3 brief repaired from cited content; was: '9.9 Detailed Design: Worker in Docker Compose']

### JR-ML-ARCH-016 — `cascor_service_adapter.py`, `service_backend.py`, `state_sync.py`, `main.py`, `metrics_panel.py`, `network_visualizer.py`, `dashboard_manag.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 156-165)

**Notes**:

[v4 brief repaired; was: '2.4 Repositories Examined']

### JR-ML-ARCH-017 — `cn_training_iterations` → `candidate_epochs` mapping is non-functional at runtime.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 224-248)

**Notes**:

[v4 brief repaired; was: '4.1 Final Registry']

### JR-ML-ARCH-018 — **Divergence**: Whether the uppercase status normalization gap should be removed (Proposal A) or retained as a latent bug (Proposal B).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 96-118)

**Notes**:

[v3 brief repaired from cited content; was: '1.4 Final Resolution of the Main Divergence']

### JR-ML-OBS-021 — duplicated rather than imported from the shared lib — tracked as.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 193-222)

**Detail**:

| Source-of-truth file | `juniper_cascor_worker/http_health.py` (heartbeat HTTP/1.1 server, hand-rolled on `asyncio.start_server`) |

**Notes**:

[v3 brief repaired from cited content; was: '3.4 juniper-cascor-worker']

### JR-ML-WS-016 — Each item below has: a unique ID, severity (P0-P3), location, current state, target state, and a remediation hook.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 1128-1131)

**Notes**:

[v3 brief repaired from cited content; was: '7. Missing / Broken Pieces (Enumerated)'] WebSocket/messaging architecture gap or design

### JR-ML-API-005 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 402-419)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.3 CR-024: Chunked Encoding Body Limit']

### JR-ML-ARCH-019 — **Final resolution**: **6 confirmed** at lines 1000, 1021, 1155, 1187, 1231, 1274.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1129-1137)

**Notes**:

[v3 brief repaired from cited content; was: '7.4 Hardcoded URL Count: 2 vs 6']

### JR-ML-UI-007 — Final resolution**: **CRITICAL**. The network topology visualization is completely non-functional in service mode — the validation guard….

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1110-1118)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '7.2 Topology Severity: CRITICAL vs MODERATE']

### JR-ML-TRAIN-013 — Final resolution**: **Known limitation**. This is not a bug — it is an architectural limitation of CasCor's API. Requires CasCor API….

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1156-1164)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '7.7 Dataset Scatter: Active Bug vs Known Limitation']

### JR-ML-ARCH-020 — Final resolution**: Listed separately as `P5-RC-09` to ensure both code paths are addressed during implementation, but recognized as same….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1147-1155)

**Notes**:

[v3 brief repaired from cited content; was: '7.6 `/api/metrics` Snapshot: Separate Issue vs Subsumed']

### JR-ML-WS-017 — Final resolution**: **LOW (latent)**. The bug is currently inactive because the dashboard doesn't consume WebSocket data (P5-RC-05). The….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1174-1182)

**Notes**:

[v2 ARCH→WS re-bucket] [v3 brief repaired from cited content; was: '7.9 Relay Raw Metrics Severity: MODERATE vs LOW']

### JR-ML-ARCH-021 — Final resolution**: MODERATE structural issue with low current impact. Proposal A correctly lowered current practical impact (no downstream….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1183-1188)

**Notes**:

[v3 brief repaired from cited content; was: '7.10 State Sync Metrics Severity']

### JR-ML-ARCH-022 — Final resolution**: **MODERATE**. This is a real cross-repo bug confirmed by validation (only one assignment to `current_phase` exists). It….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1119-1128)

**Notes**:

[v3 brief repaired from cited content; was: '7.3 CasCor Phase Bug Severity']

### JR-ML-DEP-009 — Final resolution**: **MODERATE**. This issue affects deployment portability in Docker, reverse proxy, and non-standard port scenarios — all….

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1138-1146)

**Notes**:

[v2 ARCH→DEP re-bucket] [v3 brief repaired from cited content; was: '7.5 Hardcoded URLs Severity: MODERATE vs LOW']

### JR-ML-ARCH-023 — Final resolution**: **Non-functional runtime mapping**. Not dead code — the mapping executes successfully — but `candidate_epochs` is not….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1165-1173)

**Notes**:

[v3 brief repaired from cited content; was: '7.8 `candidate_epochs` Mapping Classification']

### JR-ML-ARCH-024 — FIX-A and FIX-B can be implemented in parallel. FIX-A alone will restore metrics charts.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1409-1464)

**Notes**:

[v3 brief repaired from cited content; was: '12. Implementation Priority and Ordering']

### JR-ML-OBS-022 — Fixing **P5-RC-01** alone restores metrics charts and current metric displays.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 83-95)

**Notes**:

[v2 ARCH→OBS re-bucket] [v3 brief repaired from cited content; was: '1.3 Two Critical Display Blockers']

### JR-ML-ARCH-025 — Given the depth of analysis (7 Phase 3 proposals → 4 Phase 4 proposals → 2 Phase 5 proposals → this final synthesis with code….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1683-1733)

**Notes**:

[v3 brief repaired from cited content; was: '16.3 Completeness Assessment']

### JR-ML-WS-018 — Given the latency tolerance matrix, here is the recommended transport for every operation in scope.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 974-977)

**Notes**:

[v3 brief repaired from cited content; was: '6. Transport Split Design'] WebSocket/messaging architecture gap or design

### JR-CAS-TOOL-003 — Hardcoded values extraction into constants module; 56 hardcoded values across API layer, lifecycle manager, observability require extraction.

**Status**: designed  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/HARDCODED_VALUES_ANALYSIS.md` (lines 1-100)

**Detail**:

New module cascor_constants/constants_api/constants_api_defaults.py with 43 constants. Target location: cascor_constants/ hierarchy extended. Approach A recommended: extend existing cascor_constants/ pattern (vs. Approach B: centralize in settings.py, Approach C: hybrid). Files requiring modification: 16 (models, lifecycle, observability, routes, service_launcher, middleware, app, workers, candidate_unit, spiral_problem, snapshots, profiling).

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-OBS-023 — Hash ignores weights — prevents unnecessary redraws but masks weight changes.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 433-442)

**Notes**:

[v4 brief repaired; was: '4.2 juniper-canopy Performance']

### JR-ML-ARCH-026 — In tables throughout this document:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 142-155)

**Notes**:

[v3 brief repaired from cited content; was: '2.3 Proposal Attribution Legend']

### JR-ML-SEC-053 — Issue Remediations, Section 11.

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 9-59)

**Detail**:

#### XREPO-01: Generator Name `"circle"` vs Server's `"circles"`

### JR-ML-TEST-004 — **Keeps Proposal B's issue coverage** where it prevents omissions (P5-RC-08, P5-RC-09, P5-RC-10, P5-RC-12b).

**Status**: designed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1674-1682)

**Notes**:

[v2 ARCH→TEST re-bucket] [v3 brief repaired from cited content; was: '16.2 Key Reconciliation Decisions']

### JR-ML-WS-019 — **Latency budgets**: see §5 — distinguishes *control feedback latency* (slider→DOM, must be <16 ms, achieved by Dash clientside), *ack….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 46-77)

**Notes**:

[v3 brief repaired from cited content; was: '0. Document Conventions'] WebSocket/messaging architecture gap or design

### JR-CAN-UI-010 — Meta Parameters enhancement: rename Training Parameters to Meta Parameters with NN and Candidate Nodes subsections (22 components).

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 1-100)

**Detail**:

Restructure parameters card into two collapsible subsections: Neural Network (12 inputs: max iterations, learning rate, hidden units, growth trigger, convergence threshold, spiral params, dataset elements/noise) and Candidate Nodes (10 inputs: pool size, correlation threshold, selected candidates, training radio, iterations, convergence threshold, multi-candidate selection, candidate selection radio, top/random candidates count). Single shared Apply Parameters button. Cross-section checkbox linking (Multi-Node Layers ↔ Multi Candidate Selection).

**Design**:

Collapsible card structure with 22 component IDs, 10 Dash callbacks for toggles/radio/checkbox sync, theme constants (NEW/CHANGED/REMOVED tracking). Test plan includes unit and integration tests.

### JR-ML-ARCH-027 — `metrics_panel.py` (for P5-RC-01) — fix is in backend, not the panel's access patterns.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1643-1653)

**Notes**:

[v3 brief repaired from cited content; was: '15.4 Files NOT Requiring Modification']

### JR-ML-ARCH-028 — `P5-RC-09` remains listed separately to avoid missing the `/api/metrics` snapshot path during implementation, even though it shares root….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 249-257)

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Final Classification Notes']

### JR-ML-TRAIN-014 — **Phase 1** defined normalization targeting flat keys (correct for CasCor → Canopy boundary).

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1210-1219)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v4 brief repaired; was: '8.3 How the Problem Compounds (Best Articulated by P4-D)']

### JR-ML-DEP-010 — Phase 2 gaps**: Did not examine topology path, parameter mapping, state sync normalization, deployment portability, cross-repo bugs, or….

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 196-207)

**Notes**:

[v2 ARCH→DEP re-bucket] [v3 brief repaired from cited content; was: '3.2 Phase 2: Correct but Too Narrow']

### JR-ML-WS-020 — Playwright trace viewer + dash_duo store assertions + the verification matrix in §8.8; the §1.3 architectural correction (Option B Interval.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 1875-1897)

**Notes**:

[v4 brief repaired; was: '10. Risk Register'] WebSocket/messaging architecture gap or design

### JR-ML-TEST-005 — pytest tests/integration/ -v -m "not requires_cascor".

**Status**: designed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1486-1504)

**Notes**:

[v2 ARCH→TEST re-bucket] [v3 brief repaired from cited content; was: '14.1 Automated Tests']

### JR-ML-ARCH-029 — PYTHON_GIL=0 uvicorn juniper_data.api.app:app --host 0.0.0.0 --port 8100.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1555-1593)

**Notes**:

[v3 brief repaired from cited content; was: '14.3 Manual Integration Test']

### JR-ML-TRAIN-015 — Rationale**: Proposal A's evidence is valid and preserved (current CasCor sends title-case). Proposal B's classification better matches….

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1099-1109)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '7.1 Uppercase Status Gap: Removed vs Retained']

### JR-ML-UI-008 — Requires=juniper-data.service.

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 630-669)

**Detail**:

After=network-online.target juniper-data.service

**Notes**:

[v3 brief repaired from cited content; was: '9.7 Detailed Design: systemd Units']

### JR-ML-ARCH-030 — Retained per directive; A's evidence preserved.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1018-1042)

**Notes**:

[v4 brief repaired; was: '6.1 Phase 5 Proposal Agreement Matrix']

### JR-ML-DEP-011 — RUN pip install --no-cache-dir -r requirements.lock.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 669-689)

**Detail**:

FROM python:3.14-slim AS builder

**Notes**:

[v3 brief repaired from cited content; was: '9.8 Detailed Design: Worker Dockerfile']

### JR-ML-ARCH-031 — Service mode emits **flat metrics** (`train_loss`, `train_accuracy`) and **weight-oriented topology passthrough** (`input_size`,….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 51-60)

**Notes**:

[v3 brief repaired from cited content; was: '1.1 Primary Finding']

### JR-ML-ARCH-032 — Step 7: dashboard_manager → stores flat list in metrics-panel-metrics-store.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 258-308)

**Notes**:

[v3 brief repaired from cited content; was: '5. Detailed Issue Analysis']

### JR-ML-ARCH-033 — The final document uses Proposal B's numbering:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 134-141)

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Canonical Numbering']

### JR-ML-ARCH-034 — The following subsystems function correctly in service mode (confirmed by all proposals):.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1290-1306)

**Notes**:

[v3 brief repaired from cited content; was: '10. Verified Working Paths']

### JR-ML-UI-009 — The Juniper Canopy system has **multiple distinct ingress paths** for data into the dashboard, each independently determining its output….

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1191-1205)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '8.1 The Fundamental Problem (Consensus Across All Proposals)']

### JR-ML-WS-021 — The original draft had 8 open questions; several have been resolved into recommendations during integration. Remaining genuinely-open….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-10_JUNIPER-ECOSYSTEM_WEBSOCKET-MESSAGING-ARCHITECTURE.md` (lines 1898-1915)

**Notes**:

[v3 brief repaired from cited content; was: '11. Open Questions for Human Review'] WebSocket/messaging architecture gap or design

### JR-ML-TRAIN-016 — The Phase 1 "Canonical Internal Contract" (Section 6.2) defined flat keys by analyzing the normalization boundary (CasCor → canopy….

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 168-195)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '3.1 Phase 1: Correctly Implemented but Incompletely Validate']

### JR-ML-ARCH-035 — The status bar path is the exception that proves the rule. `ServiceBackend.get_status()` was specifically designed to produce flat keys….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1206-1209)

**Notes**:

[v3 brief repaired from cited content; was: '8.2 Why the Status Bar Works (All Proposals Agree)']

### JR-ML-ARCH-036 — This document merges both Phase 5 proposals using these rules:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 121-133)

**Notes**:

[v3 brief repaired from cited content; was: '2.1 Methodology']

### JR-ML-ARCH-037 — This final synthesis tracks **20 entries total**:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 61-82)

**Notes**:

[v3 brief repaired from cited content; was: '1.2 Final Synthesis Outcome']

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

### JR-ML-ARCH-038 — Topology weight ordering assumption incorrect for cascade architecture.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1465-1483)

**Notes**:

[v4 brief repaired; was: '13. Risk Assessment']

### JR-ML-ARCH-039 — **Treatment**: Listed separately as P5-RC-09 for implementation tracking.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1259-1289)

**Notes**:

[v3 brief repaired from cited content; was: '9. False Positives and Retractions']

### JR-ML-ARCH-040 — | Final Issue | P4-A (002192f3) | P4-B (66a019dc) | P4-C (cd8254d3)  | P4-D (d7dcbd5a) | Agreement        |.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1043-1067)

**Notes**:

[v4 brief repaired; was: '6.2 Phase 4 Proposal Agreement Matrix']

### JR-ML-DEP-012 — ├── P5-RC-11  MODERATE: Hardcoded deployment URLs.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1220-1258)

**Notes**:

[v2 ARCH→DEP re-bucket] [v3 brief repaired from cited content; was: '8.4 Root Cause Dependency Graph']

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

### JR-ML-TRAIN-049 — Concurrency Assessment.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 324-330)

**Detail**:

**WebSocket Mode**: Well-designed single-threaded asyncio with `asyncio.to_thread` for CPU-bound training. No shared mutable state between async loop and training thread

### JR-ML-OBS-054 — Design mini-batch instrumentation for CasCor training observability.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md` (lines 1-100)

**Notes**:

Batch-level metrics collection.

### JR-ML-TRAIN-050 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 419-434)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.4 CR-025: WebSocket Async Lock']

### JR-ML-OBS-055 — End of seed. Audit findings appended in subsequent commits on the same branch.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 454-465)

**Detail**:

- [`METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`](../../legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md)

**Notes**:

[v3 brief repaired from cited content; was: 'Design docs']

### JR-ML-UI-024 — Implement contextual menu and candidate tab design for Canopy UI.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CONTEXTUAL_MENU_AND_CANDIDATE_TAB_DESIGN.md` (lines 1-100)

### JR-ML-SEC-112 — juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 415-423)

**Detail**:

- juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline

**Notes**:

[v3 brief repaired from cited content; was: 'Cross-repo']

### JR-ML-SEC-113 — Optimizer and `nn.Linear` recreated on every `train_output_layer` call.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 859-877)

### JR-ML-SEC-114 — Per-phase entry / design docs.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 728-740)

**Detail**:

- `juniper-ml/notes/code-review/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`

### JR-ML-SEC-115 — Performance test baselines record data but never assert against regression thresholds.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1058-1076)

### JR-ML-OBS-056 — Phase B (polling elimination — P0 WIN) — ✅ IMPLEMENTED.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 330-341)

**Detail**:

| Two-flag design: `enable_browser_ws_bridge` + `disable_ws_bridge`   | ✅ In `settings.py`                        |

### JR-ML-SEC-116 — **R4.6 request-id propagation**: Correctly implemented and well-tested in.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 275-305)

**Detail**:

**Scope**: Verify R2.1 lib adoption, R2.2 WS schema alignment, R4.6

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Dimension C — Shared lib + WS schema + middleware']

### JR-ML-WS-136 — Standardize WebSocket frame schema for Canopy↔CasCor training streaming.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md` (lines 1-50)

### JR-ML-UI-025 — `task_timeout` env override logic: if user explicitly passes `--task-timeout 3600` (the default value), code falls through to env var. Can't.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 105-114)

**Detail**:

| ID        | Severity   | File:Line              | Description

**Notes**:

[v4 brief repaired; was: '2.1 Bugs']

### JR-ML-OBS-057 — This tracker accepts new items in three cases:.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 378-388)

**Detail**:

- **Audit follow-ups** — if a new audit (e.g. a 2026-Q3 observability re-audit) surfaces findings whose action sits beyond a single PR, add them here with a fresh ID.

**Notes**:

[v3 brief repaired from cited content; was: '4.2 When new items are added']

### JR-CAS-WS-003 — Thread handoff procedure replaces default compaction; preserves context at 95-99% utilization threshold.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/THREAD_HANDOFF_IMPLEMENTATION.md` (lines 1-100)

**Detail**:

Two-layer implementation: global ~/.claude/CLAUDE.md + project CLAUDE.md. Trigger: 95-99% context utilization (within 1-5% of compaction threshold). Additional triggers: 15+ tool calls, phase boundary, degraded recall, module transition, user request. 5-step execution protocol: checkpoint, compose goal, present, verify, git status. Exclusions: nearly complete task, sharp thread, tightly coupled work.

### JR-ML-TRAIN-051 — Update `TrainingSettings` model to include new `TrainingParamConfig` entries:.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 314-331)

**Detail**:

epochs: TrainingParamConfig = TrainingParamConfig(min=10, max=10000000, default=1000000)

**Notes**:

[v3 brief repaired from cited content; was: '5.4 `settings.py`']

### JR-ML-OBS-144 — Closing PRs (commit hashes verified against current `origin/main`).

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 746-764)

**Detail**:

| juniper-cascor | #204 | obs-wire-01: wire 5 cascor metric emission sites + lazy-init race fix |

### JR-CAS-TRAIN-032 — Document workaround for sys.path mutation pattern - long-term fix via IPC.

**Status**: designed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 607-619)

**Detail**:

Canopy uses sys.path.insert(0, cascor_src) to import Cascor directly. Fragile,
creates import order dependencies. Module naming collision resolved (cascor_constants/),
but sys.path mutation remains. Long-term: IPC or make Cascor installable package.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-SEC-213 — Effort**: 1 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 378-402)

**Detail**:

**Effort**: 1 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.2 CR-026: Server-Assigned Worker IDs']

### JR-ML-SEC-214 — Issue Remediations, Section 10.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 392-428)

**Detail**:

All CasCor enhancement items are feature requests. Brief remediation approaches:

### JR-ML-DEP-046 — Phase 3: Worker Deployment & Container Integration (P1) -- Short-Term ✅ COMPLETED.

**Status**: designed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 754-785)

**Detail**:

**Goal**: Enable containerized deployment of the distributed worker.

### JR-ML-OBS-145 — **The work** (when un-deferred): A 3-4 PR sub-track (constants → config → output.

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 126-176)

**Detail**:

- **Status**: deferred (user explicitly paused at design-doc stage)

**Notes**:

[v3 brief repaired from cited content; was: '3.3 TRAIN-ARCH-01 cascor mini-batch restoration']

### JR-ML-TRAIN-103 — Trigger / due date.** None — opportunistic. May get pulled in if TRAIN-ARCH-01 unblocks (Q4 of that design doc covers the per-step vs….

**Status**: designed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 227-243)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.7 R5.6-THROTTLE — Cascor 25-epoch emit throttle removal']
