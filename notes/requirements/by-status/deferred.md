# Requirements — status: deferred

**Total entries**: 40

**By priority**: P0=8 | P1=9 | P2=7 | P3=16

**By category**: SEC=13 | OBS=9 | API=4 | DATA=2 | TRAIN=2 | WS=2 | ARCH=2 | PERF=2 | DEP=2 | UI=1 | TEST=1

**By owner**: ml=31 | cas=4 | dat=3 | dep=1 | rec=1

---

### JR-ML-OBS-005 — Additional completed work (not in original plan).

**Status**: deferred  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 184-228)

**Detail**:

## 8. Critical Bug Fixes (Phase 1)

### JR-ML-SEC-006 — carry-forward tracker — recommended container-form alternative is.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 574-624)

**Detail**:

arbitrary file paths). Tracked as **AMTOOL-CI** (P3) on the

**Notes**:

[v3 brief repaired from cited content; was: '9.4 Validation status']

### JR-ML-SEC-007 — Issue Remediations, Section 13.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 428-478)

**Detail**:

#### DEPLOY-01: Docker Secret Name/Path Mismatch

### JR-ML-SEC-008 — juniper-deploy: 3 high infrastructure bugs (AlertManager missing, rules not mounted, secret mismatch), 8 unimplemented roadmap items.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 396-434)

**Detail**:

| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker | 🔴 Open |

**Notes**:

[v3 brief repaired from cited content; was: '15.3 juniper-cascor-worker']

### JR-ML-OBS-006 — Save/Load snapshot in adapter — prevents training session recovery in service mode.

**Status**: deferred  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 193-203)

**Notes**:

[v4 brief repaired; was: '7.0 Critical and High-Priority Enhancements (v3.0.0)']

### JR-ML-API-001 — Storage & Infrastructure.

**Status**: deferred  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 348-398)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 273-317)

**Detail**:

## 11. Cross-Repository Alignment Issues

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-009 — The remaining open items are all P3 / soft-blocker items tracked in.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 648-676)

**Detail**:

| **A.1 / A.2a–e (cascor training metrics dead-defined)** | juniper-cascor#204 (OBS-WIRE-01) — wired 5 emission sites |

**Notes**:

[v3 brief repaired from cited content; was: 'Closing PRs']

### JR-ML-SEC-010 — v3.0.0 Cross-Referenced Source Documents (34 total).

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 513-563)

**Detail**:

| 1  | `notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md`                              | juniper-ml     |

### JR-ML-API-006 — CAN-015g/h snapshot-loading endpoints: restore, replay, resume, retrain with FSM state transitions.

**Status**: deferred  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md` (lines 1-100)

### JR-ML-DATA-004 — **Deferred items**: RD-008 (SIM117 test fixes), RD-015 (IPC/ZeroMQ), RD-016 (GPU), RD-017 (continuous profiling)

**Status**: deferred  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 392-402)

**Detail**:

| HTTP status codes → `starlette.status`                            | ✅ Complete                              |

**Notes**:

[v3 brief repaired from cited content; was: '7.3 juniper-data — Constants Refactor ✅; Roadmap Items Defer']

### JR-CAS-TRAIN-021 — Implement full IPC architecture to separate Cascor from Canopy process for production deployment.

**Status**: deferred  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 260-279)

**Detail**:

Currently Cascor embedded in Canopy via sys.path import. Production deployment requires
separate processes communicating via sockets/REST. Sub-tasks: design protocol spec,
implement Cascor server mode, update Canopy to connect externally, add connection
management and health checks.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-DATA-005 — IPC Architecture (ZeroMQ/shared-memory)

**Status**: deferred  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 453-466)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 364-377)

**Detail**:

## 15. Client Library Outstanding Items

**Notes**:

[v4 brief repaired; was: '14.3 Deferred Roadmap Items']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-054 — Issue Remediations, Section 14 — Performance and Roadmap.

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 540-590)

**Detail**:

#### JD-PERF-01: Sync `generator.generate()` Blocks Event Loop

### JR-ML-SEC-055 — Phase 1 was executed on branch `fix/interface-phase1-verification`. All three Tier 0.

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 53-82)

**Detail**:

| CR-006 deconflation (fit())                                            | VERIFIED             | `cascade_correlation.py:1450` routes `max_epochs` to `train_output_layer()`; `cascade_correlation.py:1476-1488` routes `max_iterations` to `grow_network()`           |

**Notes**:

[v3 brief repaired from cited content; was: '3.0 Phase 1 Execution Results (2026-04-09)']

### JR-DEP-OBS-007 — Replace log-only burn-rate alert severity with paging severity after 30-day soak period.

**Status**: deferred  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 918-932)

**Detail**:

All numeric SLO targets in §3 are initial and provisional. R5.4 ships burn-rate alerts in
log-only severity. After 30-day production soak window (target 2026-06-15), compare actual
burn rates against targets, tighten or relax as needed, and lift log-only severity to paging
for §3.1, §3.2, §3.5 (which have all pre-conditions met today).

### JR-ML-SEC-056 — ❌ Planned in `CONTAINER_VALIDATION_CI_PLAN.md` but absent from `ci.yml`.

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 409-433)

**Detail**:

| Post-release roadmap: Grafana dashboards, Prometheus alerting | ✅ Done (v0.2.0)                                                         |

**Notes**:

[v4 brief repaired; was: '7.5 juniper-deploy — Multiple Plans Partially Complete']

### JR-ML-SEC-057 — 🔴 Planned in `CONTAINER_VALIDATION_CI_PLAN.md` but absent from CI.

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 419-436)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 330-347)

**Detail**:

| DEPLOY-RD-01 | 0.3.0           | Production compose profile with resource limits          | 🔴 NOT DONE                                                        |

**Notes**:

[v4 brief repaired; was: '13.2 Unimplemented Roadmap Items']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-OBS-058 — Address residual follow-ups from METRICS-MON program close.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md` (lines 1-100)

**Notes**:

Captured in POST_METRICS_MON_TRACKER; deferred after program closure.

### JR-ML-UI-026 — Canopy dashboard self-call refactor: defer weight display, implement metrics playback, option C trigger conditions.

**Status**: deferred  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md` (lines 1-50)

### JR-CAS-TEST-009 — Defer test optimization: reduce 45-minute test suite to ≤5 minutes.

**Status**: deferred  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 37-39)

**Detail**:

Test suite runs in 45+ minutes; target ≤5 minutes. This is a deferred medium-priority optimization (MED-014) per document status.

**Notes**:

Deferred optimization; developer productivity; noted in doc status

### JR-ML-SEC-117 — Per-command HMAC deferred indefinitely.

**Status**: deferred  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 70-70)

**Notes**:

Settled position C-33 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-137 — Phase E-server deferred perper-client queue and backpressure policy matrix.

**Status**: deferred  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-03-CASCOR-BACKEND.md` (lines 1017-1029)

### JR-ML-OBS-059 — Re-bucket cascor_ws_command_handler_seconds for better SLO breach-detection precision post-soak.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 173-182)

**Detail**:

G7 - 50 ms SLO target sits one bucket below 100 ms +inf cap, limiting breach-detection precision.
Deferred to R5.1c post-soak calibration per juniper-cascor/notes/HISTOGRAM_BUCKETS_RATIONALE.md.

### JR-ML-ARCH-187 — Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: deferred  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 61-61)

**Notes**:

Settled position C-24 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-146 — Concrete actions.** ≤ 10-line PR replacing the two literals with shared-lib imports. Update worker tests to import from the shared lib….

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 264-280)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor-worker · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.9 R2-WORKER-DEDUP — juniper-cascor-worker contract-constan']

### JR-DAT-OBS-007 — Continuous profiling (Grafana Pyroscope, Prometheus, OpenTelemetry) deferred until production deployment.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 493-516)

**Notes**:

RD-017 (DATA-020). Deferred. Partially addressed with Prometheus + Sentry in commit 830a0ef.

### JR-CAS-PERF-004 — Create baseline performance profiles using py-spy for regression detection.

**Status**: deferred  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 635-645)

**Detail**:

Baseline py-spy profiles for key operations enable performance regression detection.

### JR-ML-OBS-147 — Defer full worker migration; adopt only R1.2 probe contract constants.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md` (lines 1-100)

**Notes**:

Decided: no full migration now. Use contract constants only.

### JR-ML-API-087 — Ecosystem-Wide Patterns.

**Status**: deferred  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 436-445)

**Detail**:

1. **No application has all git tags**: This is a systemic process gap. Releases are documented in changelogs but tags are not created, meaning GitHub releases and PyPI publishes may not ha

### JR-DAT-PERF-001 — GPU acceleration (CuPy, JAX, PyTorch) deferred until >1M points or >30s generation time.

**Status**: deferred  **Priority**: P3  **Category**: PERF  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 468-490)

**Notes**:

RD-016 (DATA-019). Deferred. PyTorch no longer a dependency. CUDA not in CI.

### JR-DAT-WS-001 — IPC architecture (gRPC, message queue, shared memory, WebSocket) deferred until REST bottleneck or >100MB datasets.

**Status**: deferred  **Priority**: P3  **Category**: WS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 438-465)

**Notes**:

[v2 ARCH→WS re-bucket] RD-015 (DATA-018). Deferred. REST migration success reduced urgency.

### JR-ML-SEC-215 — Phase 3: WebSocket Topology Push (OI-2) — COMPLETE.

**Status**: deferred  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 672-688)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-SEC-216 — Phase 4: Weight-Centric Topology Toggle (OF-1) — COMPLETE.

**Status**: deferred  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 688-706)

**Detail**:

**Repos**: juniper-canopy only (CasCor already returns raw weight-oriented format)

### JR-ML-DEP-047 — **Primary: Approach A (Incremental Fix)** with elements of Approach C for systemd units.

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 591-603)

**Detail**:

**Primary: Approach A (Incremental Fix)** with elements of Approach C for systemd units.

**Notes**:

[v4 brief repaired; was: '9.4 Recommended Approach']

### JR-ML-API-088 — R5.6-THROTTLE (P3, deferred) on the carry-forward tracker.

**Status**: deferred  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 472-483)

**Detail**:

annotation `description` blocks (`alert_rules.yml:751`, `:819`). The

**Notes**:

[v3 brief repaired from cited content; was: '7.3 The 25-epoch throttle caveat']

### JR-ML-TRAIN-104 — Remove 9 local `import traceback` in cascade_correlation.py — uncomment line 64 top-level import.

**Status**: deferred  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 159-175)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 130-144)

**Detail**:

| CLN-CC-02 | **P2**   | Delete stale `check.py` duplicate (600 lines) — copy of spiral_problem.py                        | `src/spiral_problem/check.py`                                                            | 10 min      |

**Notes**:

[v4 brief repaired; was: '6.1 juniper-cascor — Stale Code Removal']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-CAS-ARCH-019 — Remove legacy spiral generator code once JuniperData is stable and proven.

**Status**: deferred  **Priority**: P3  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 568-578)

**Detail**:

Dual-path (legacy + JuniperData) creates maintenance burden. Once JuniperData stable,
remove legacy spiral generator from spiral_problem.py.

### JR-ML-OBS-148 — The following issues were identified through cross-referencing all prior documents against the current codebase. Issues are ordered by….

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 82-105)

**Detail**:

| CANOPY_DASHBOARD_DISPLAY_FIXES.md          | 3 display issues (metrics, dataset, topology) | Issue 3 (output weights transposition): **FIXED** (committed in adapter). Issues 1-2: **FIXED** per CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md |

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Documents in `notes/`']

### JR-ML-SEC-217 — Worker security modules (mTLS, anomaly detection, rate limiting, audit) are not integrated into runtime.

**Status**: deferred  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 260-294)

### JR-REC-DEP-001 — Dedicated conda environment decision (Q-10)

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 1262-1274)

**Detail**:

Recurrence currently rides `JuniperCascor1` (works today; editable install + console script live there). A dedicated lighter env is probably right for hygiene — explicitly an owner call; nothing blocks on it.
