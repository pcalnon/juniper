# Requirements — OBS

**Area**: observability — metrics, logging, tracing, dashboards, alerting

**Total entries**: 193

**By status**: proposed=151 | designed=12 | in-progress=3 | shipped=17 | deferred=9 | rejected=1

**By priority**: P0=23 | P1=49 | P2=109 | P3=12

**By owner**: ml=149 | can=19 | dep=12 | dat=7 | cas=5 | rec=1

---

### JR-ML-OBS-001 — A.5 was tracked but its dashboard half was not explicitly carried.

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 826-876)

**Detail**:

**Finding.** Four dashboard text / inference panels are stale relative

**Notes**:

[v3 brief repaired from cited content; was: '15.2 4 stale dashboard panels post audit-PR closes']

### JR-CAN-OBS-001 — Prometheus histogram bucket rationale: canopy_ws_browser_latency_ms with SLO candidates (p95<25ms, p99<100ms).

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-95)

**Detail**:

WebSocket browser latency metric with 10 buckets [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000] ms mapping to UX thresholds: 5ms (sub-frame 200Hz), 10ms (100Hz frame), 25ms (60Hz display jitter boundary), 50ms (perceived instant threshold), 100ms (noticeable lag, Nielsen), 250ms-5s (degradation signals). SLO candidates: p95 training-WS RTT<25ms, p99 control-WS RTT<100ms. Status: tentative pending R5.1 ratification.

**Notes**:

METRICS-MON sub-track R4.1. May reshape upper buckets (2.5s, 5s) post-R5.1.

### JR-DAT-OBS-001 — Security scanning (Bandit and pip-audit) must fail on vulnerabilities, not suppress with || true or || echo.

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 170-238)

**Notes**:

SEC-001 and SEC-002 CRITICAL. Status shipped per 2026-02-24 migration.

### JR-ML-OBS-002 — Fix 7 stale Grafana dashboard panels in juniper-cascor.json and juniper-overview.json - 3 inference panels and 4 placeholder texts.

**Status**: in-progress  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 125-135)

**Detail**:

G1 - Stale panels:
- 3 cascor inference panels query removed juniper_cascor_inference_* metrics
- 4 worker-bridge placeholder text panels never replaced with real PromQL
In-flight branch audit-fixup/stale-dashboard-panels exists as of 2026-05-06.

**Notes**:

Operational blocker. Recommend Option A - land in-flight PR + add dashboard-lint CI guardrail.

### JR-ML-OBS-003 — P5-RC-05 (frontend WebSocket consumption) is STILL OPEN, not deferred — high-volume / low-latency metrics and the bidirectional `set_params` control channel depend on it

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 574-619)

**Detail**:

> - 2026-04-10 first pass: typed contract landed (PR #140); P5-RC-05 marked DEFERRED

**Notes**:

[v3 brief repaired from cited content; was: '6.0 Phase 4 Execution Results (2026-04-10, REVISED)']

[2026-08-29 brief repaired from cited content; was: '>   per the canopy requirements (high-volume / low-latency metrics and the.']

### JR-ML-OBS-004 — Status**: **PARTIAL (2026-04-10)** — typed contract done; WebSocket consumption still open. See….

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 556-574)

**Detail**:

- [x] Dashboard shows per-epoch loss during output training phases — `train_output_layer` callback wired in cascor `manager.py:237-248`; demo mode emits via `_emit_training_metrics()` (verified 2026-04-09)

**Notes**:

[v3 brief repaired from cited content; was: '5.6 Phase 3 Success Criteria']

### JR-ML-OBS-005 — Additional completed work (not in original plan).

**Status**: deferred  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 184-228)

**Detail**:

## 8. Critical Bug Fixes (Phase 1)

### JR-ML-OBS-006 — Save/Load snapshot in adapter — prevents training session recovery in service mode.

**Status**: deferred  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 193-203)

**Notes**:

[v4 brief repaired; was: '7.0 Critical and High-Priority Enhancements (v3.0.0)']

### JR-DEP-OBS-001 — Add juniper_cascor_training_sessions_completed_total counter with closed-set outcome labels.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 808-827)

**Detail**:

juniper_cascor_training_sessions_completed_total does not exist as of 2026-05-03.
Cascor currently exposes only training_sessions_active (Gauge) and training_epochs_total (Counter).
Recommendation: add counter with closed-set outcome ∈ {success, error, aborted} bumped from
training-loop completion handler. ~50 lines, R5.4 PR or separate R5.5a sub-track.

### JR-ML-OBS-007 — align between docker-compose and k8s deployments; `pending_tasks`.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 260-275)

**Detail**:

**Scope**: Verify alert/dashboard/scrape configs are technically correct.

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Dimension B — PromQL + scrape correctness']

### JR-ML-OBS-008 — `CanopyDashboardAvailabilitySlowBurn`, `CanopyRenderLatencySlowBurn`, `CascorTrainJobSuccessSlowBurn`, `CascorTrainStepLatencySlowBurn`, `Da.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 446-456)

**Notes**:

[v4 brief repaired; was: '7.1 Rules by severity label']

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

### JR-ML-OBS-009 — **File**: [`notes/SLO_CATALOG_2026-05-03.md`](https://github.com/pcalnon/juniper-deploy/blob/main/notes/SLO_CATALOG_2026-05-03.md)….

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 70-97)

**Detail**:

- **Status**: open (30-day soak underway)

**Notes**:

[v3 brief repaired from cited content; was: '3.1 SLO catalog target calibration against soak-window data']

### JR-ML-OBS-010 — Impact. The juniper-data dashboard panel "Cached Datasets".

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 787-826)

**Detail**:

**Finding.** The metric `juniper_data_datasets_cached` (Gauge, no labels)

**Notes**:

[v3 brief repaired from cited content; was: '15.1 `juniper_data_datasets_cached` is defined-and-emitted i']

### JR-ML-OBS-011 — Items identified from cross-referencing WebSocket messaging architecture reviews against implementation status.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 257-280)

**Detail**:

## 9. Microservices and Infrastructure

**Notes**:

[v3 brief repaired from cited content; was: '8.3 Critical Individual Gaps (from WebSocket Architecture Re']

### JR-ML-OBS-012 — Low Priority (Future Phases).

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 375-408)

**Detail**:

| Phase 5: Observability & Hardening | MICROSERVICES_STARTUP_CODE_REVIEW | AlertManager receivers, alert rules, health standardization                 |

### JR-ML-OBS-013 — P2 — Quality / correctness (real but lower-impact).

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 380-391)

**Detail**:

| **A.5** | juniper-cascor | `juniper_cascor_inference_*` (counter + histogram) dead → 4 dashboard panels show flat zeros | Wire `record_inference()` if cas

### JR-ML-OBS-014 — Phase 1: Critical Bug Fixes (OI-1 + OI-4) — COMPLETE.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 644-658)

**Detail**:

**Repos**: juniper-canopy only

### JR-DEP-OBS-004 — Ship Prometheus burn-rate alerting rules derived from SLO targets with MWMBR pattern.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 102-140)

**Detail**:

Implement Multi-Window Multi-Burn-Rate alerts for the 5 user-facing SLOs (§3).
Fast-burn (5m/1h @ 14.4×) and mid-burn (30m/6h @ 6×) page on-call.
Slow-burn (2h/24h @ 3×) and long-burn (6h/72h @ 1×) create tickets only.
Internal-supporting SLIs (§4) emit log-only-severity alerts with same MWMBR shape.

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

### JR-CAS-OBS-001 — Add thread safety locks to monitoring loop metrics extraction (CascorIntegration._extract_current_metrics).

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 715-743)

### JR-DEP-OBS-005 — Define and catalogue 5 user-facing and 8 internal-supporting SLO/SLI targets for the Juniper observability stack.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 1-50)

**Detail**:

The SLO catalog is the single source of truth for Juniper SLOs. User-facing SLIs
(canopy availability, canopy render latency, cascor train-job success, cascor train-epoch p95,
data POST availability) are release-blocking with tight SLO targets. Internal-supporting SLIs
(worker heartbeat freshness, cascor pending-task queue, broadcast fan-out p95, command-handler
p95, data-client request latency, data-client error rate, dataset cache-hit ratio, http 5xx rate)
are graphed but not paging.

**Notes**:

SLO targets are provisional pending 30-day soak (§2.6). Burn-rate alerting uses
Multi-Window Multi-Burn-Rate pattern. Several forward-references to R5.3/R5.4 designs.

### JR-DEP-OBS-006 — Maintain health-readiness probe topology as a DAG with asymmetric severity policies.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 1-87)

**Detail**:

Canopy probes both cascor and data, returns 200 degraded (dashboard stays visible).
Cascor probes data (when URL set), returns 503 not_ready (gates traffic). Data probes
storage only, returns 503 not_ready. Worker probes nothing externally. Topology is
intentionally a DAG to avoid cascading false-503s. Regression tests pin both policies.
Document in repo readiness handlers.

**Notes**:

Closes METRICS-MON R2.3 seed-15. Operator runbook in §6.

### JR-DAT-OBS-002 — Prometheus histogram juniper_data_dataset_generation_duration_seconds buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, +inf.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 25-43)

**Notes**:

Tentative pending R5.1 SLO design. Bucket rationale documented for each boundary.

### JR-DAT-OBS-003 — Release notes document known issues, resolved issues, and What's Next with accurate status.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 89-103)

**Notes**:

RD-001 complete 2026-02-24. Only B008 warnings remain. v0.5.0 scope updated.

### JR-ML-OBS-018 — **Strengths**: Near-real-time topology updates, no additional REST calls, leverages existing WebSocket infrastructure.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 251-301)

**Detail**:

#### Approach A: Add WebSocket-to-Store bridge via clientside callback (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

### JR-ML-OBS-019 — Wire juniper_data_datasets_cached Gauge at every cache mutation site in juniper-data.

**Status**: in-progress  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 142-150)

**Detail**:

G3 - Dead Gauge with no production caller. Defined but never emitted.
In-flight sister PR exists. Add unit test asserting Gauge.value == len(cache) after each operation.

### JR-ML-OBS-020 — 20+ log calls per `CandidateUnit.__init__` × pool_size = 160+ per grow iteration.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 420-433)

**Detail**:

| **Forward pass**        | ✅ Optimized     | Pre-allocated buffer (OPT-1) eliminates N `torch.cat()` calls                    |

**Notes**:

[v4 brief repaired; was: '4.1 juniper-cascor Performance']

### JR-ML-OBS-021 — duplicated rather than imported from the shared lib — tracked as.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 193-222)

**Detail**:

| Source-of-truth file | `juniper_cascor_worker/http_health.py` (heartbeat HTTP/1.1 server, hand-rolled on `asyncio.start_server`) |

**Notes**:

[v3 brief repaired from cited content; was: '3.4 juniper-cascor-worker']

### JR-ML-OBS-022 — Fixing **P5-RC-01** alone restores metrics charts and current metric displays.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 83-95)

**Notes**:

[v2 ARCH→OBS re-bucket] [v3 brief repaired from cited content; was: '1.3 Two Critical Display Blockers']

### JR-ML-OBS-023 — Hash ignores weights — prevents unnecessary redraws but masks weight changes.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 433-442)

**Notes**:

[v4 brief repaired; was: '4.2 juniper-canopy Performance']

### JR-DEP-OBS-007 — Replace log-only burn-rate alert severity with paging severity after 30-day soak period.

**Status**: deferred  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 918-932)

**Detail**:

All numeric SLO targets in §3 are initial and provisional. R5.4 ships burn-rate alerts in
log-only severity. After 30-day production soak window (target 2026-06-15), compare actual
burn rates against targets, tighten or relax as needed, and lift log-only severity to paging
for §3.1, §3.2, §3.5 (which have all pre-conditions met today).

### JR-ML-OBS-024 — 01: Dual metric format removed aggressively.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 375-376)

**Notes**:

[v2 ARCH→OBS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-OBS-025 — Add dashboard/alert lint lane to juniper-deploy CI.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 284-290)

**Detail**:

Cross-cutting recommendation: Add CI guardrail to prevent future stale panels.
Run promtool check rules on alert_rules.yml and recording_rules.yml.
JSON-schema validate each dashboard and promtool query instant against synthetic Prometheus.

### JR-ML-OBS-026 — Add `get_dataset_data()` method to `src/api/lifecycle/manager.py`:.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 151-187)

**Detail**:

result = {"train_x": self._train_x.detach().cpu().tolist(),

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Fix — Phase 2: Cross-Repo Dataset Data Endpoint']

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

### JR-ML-OBS-028 — All services use HTTP health probes with proper intervals, timeouts, and retry counts.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 313-328)

**Detail**:

| **Dependency ordering** | `depends_on` with `condition: service_healthy` ensures proper startup sequence        |

**Notes**:

[v4 brief repaired; was: '4.2 Strengths']

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

### JR-ML-OBS-030 — BUG-CC-17: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 844-852)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-OBS-031 — BUG-JD-09: High-Cardinality Prometheus Labels from Parameterized Routes.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1223-1237)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-OBS-032 — C-37: P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 285-286)

**Notes**:

[v2 ARCH→OBS re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

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

### JR-ML-OBS-034 — canopy work was already implemented in the months between the 2026-04-08.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 451-491)

**Detail**:

roadmap snapshot and Phase 3 execution. The only real gap was the demo backend,

**Notes**:

[v3 brief repaired from cited content; was: '5.0 Phase 3 Execution Results (2026-04-09)']

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

### JR-ML-OBS-036 — _client_latency_ms private field on returned dict.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 223-223)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-OBS-002 — ColoredFormatter must not mutate LogRecord during formatting.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 151-151)

**Detail**:

Issue 3.1.1: ColoredFormatter adds ANSI codes to LogRecord.msg in-place,
affecting file output. Clone record before mutation or use format string.

### JR-ML-OBS-037 — CONC-03: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4252-4275)

**Notes**:

[v2 ARCH→OBS re-bucket]

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

### JR-ML-OBS-039 — D-Criterion: Metric.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 143-144)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-OBS-040 — D-**Dual metric format breakage** (RISK-01): High.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 134-135)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-CAN-OBS-003 — Dashboard MetricsPanel expects nested metric format (metrics.loss, metrics.accuracy, network_topology.hidden_units) but service backend produces flat keys.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 242-337)

**Detail**:

Nine MetricsPanel code locations read nested structure: Line 1091 network_topology.hidden_units, Line 1120-1122 metrics.loss/accuracy/network_topology.hidden_units, etc. Service backend currently returns flat keys only.

**Notes**:

Display failure affects all metric charts. Nested format required by React component state rendering.

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

### JR-DEP-OBS-011 — Define and document alert rule thresholds as environment-configurable constants.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 55-66)

**Detail**:

Prometheus alert_rules.yml contains 10+ hardcoded thresholds (error rate 0.05, data P95
latency 2.0s, cascor P95 5.0s, dataset gen 30.0s, correlation 0.01, restart count 3, windows
1m/5m/10m/15m/30m). Document all values clearly in YAML comments. Consider envsubst preprocessing
for full configurability across deployment targets. Medium priority per analysis.

### JR-DEP-OBS-012 — Emit X-Juniper-Readiness response header on all /v1/health/ready endpoints.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 89-94)

**Detail**:

All four services (cascor, data, canopy, cascor-worker) must emit
X-Juniper-Readiness: ready | degraded | not_ready response header on /v1/health/ready.
Header mirrors body status field byte-for-byte. Constant single-sourced in
juniper-observability (READINESS_HEADER). Cascor-worker uses same literal without import.

### JR-ML-OBS-041 — Fix layer assignments (Task 3); add `get_dataset_data()` (Task 2 Ph2).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 329-341)

**Detail**:

| `src/backend/cascor_service_adapter.py`          | Fix layer assignments (Task 3); add `get_dataset_data()` (Task 2 Ph2) | 1, 4  |

**Notes**:

[v4 brief repaired; was: '9.1 juniper-canopy (all phases)']

### JR-CAN-OBS-004 — Health checks must use async probes instead of blocking network calls.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 155-155)

**Detail**:

Issue 3.1.5: Health endpoints currently block on cascor connectivity checks.
Use async probes or timeout guards to prevent cascor slowness from blocking
health endpoint response.

### JR-ML-OBS-042 — Issue Remediations, Section 17.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-A-SECURITY-CONCURRENCY-ERROR.md` (lines 297-347)

**Detail**:

#### CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager

### JR-ML-OBS-043 — `juniper_data/api/routes/health.py` (`/v1/health`, `/v1/health/live`, `/v1/health/ready`).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 51-101)

**Detail**:

| Python entry point             | `juniper_data/__main__.py`                                                                | Active                                      |

**Notes**:

[v4 brief repaired; was: '2.1 Per-Application Inventory']

### JR-CAN-OBS-005 — Logger wrapper instances must be cached to avoid re-wrapping overhead.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 152-152)

**Detail**:

Issue 3.1.2: Wrapper created fresh on each logger.info/debug call. Cache
wrapper per logger instance to improve performance.

### JR-ML-OBS-044 — Phase 6: Finalize.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 563-607)

**Detail**:

1. Run linters (black, isort, flake8)

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

### JR-CAN-OBS-008 — Sentry sample rate must be configurable via environment variable.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 153-153)

**Detail**:

Issue 3.1.3: Sentry sample_rate hardcoded. Add SENTRY_SAMPLE_RATE env var
with sensible default (0.1 for production, 1.0 for dev).

### JR-ML-OBS-045 — Swap PrometheusMiddleware and RequestIdMiddleware order in canopy main.py:312 to fix mis-labeling.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 162-168)

**Detail**:

G5 - Middleware order causes request-id ContextVar to be unset during metric labeling.
One-line fix. Add unit test asserting request-id header present in metric labels.

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

### JR-ML-OBS-048 — WS metrics audit A9 + integration 3.2: expose buffer occupancy, connection state, frame sizes as Prometheus gauges.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md` (lines 1-50)

### JR-ML-OBS-049 — Closing PRs that motivated this tracker (reference only).

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 423-433)

**Detail**:

- juniper-cascor#221 — Final E.6 audit follow-up: WorkerRegistry size cap + WS handshake rejection plumbing (MERGED 2026-05-05)

### JR-CAS-OBS-002 — Define Prometheus histogram buckets for latency metrics per observability requirements.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-50)

**Notes**:

See histogram_rationale file for bucket selection rationale.

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

### JR-ML-OBS-050 — Severity-1 cluster headline.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 421-439)

**Detail**:

cause: the pre-METRICS-MON observability scaffolding in

### JR-ML-OBS-051 — **Source-of-truth:** `juniper-deploy/prometheus/alert_rules.yml` (1146 lines).

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 424-446)

**Detail**:

| juniper-cascor.json | Worker `last_task_duration_seconds` (JSON-only — Prometheus bridge pending) | **STALE** — bridge shipped via juniper-cascor#188 (`WorkerRegistr

**Notes**:

[v3 brief repaired from cited content; was: '6.5 Placeholder text panels (intentional gaps — OBS-WIRE-01)']

### JR-ML-OBS-052 — What needs to happen.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 676-699)

**Detail**:

1. **Pull p50 / p95 / p99 from Prometheus** for every SLI in catalog §3

### JR-ML-OBS-053 — 2D. Phase Duration Display.

**Status**: in-progress  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 108-116)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-OBS-054 — Design mini-batch instrumentation for CasCor training observability.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md` (lines 1-100)

**Notes**:

Batch-level metrics collection.

### JR-ML-OBS-055 — End of seed. Audit findings appended in subsequent commits on the same branch.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 454-465)

**Detail**:

- [`METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`](../../legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md)

**Notes**:

[v3 brief repaired from cited content; was: 'Design docs']

### JR-ML-OBS-056 — Phase B (polling elimination — P0 WIN) — ✅ IMPLEMENTED.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 330-341)

**Detail**:

| Two-flag design: `enable_browser_ws_bridge` + `disable_ws_bridge`   | ✅ In `settings.py`                        |

### JR-ML-OBS-057 — This tracker accepts new items in three cases:.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 378-388)

**Detail**:

- **Audit follow-ups** — if a new audit (e.g. a 2026-Q3 observability re-audit) surfaces findings whose action sits beyond a single PR, add them here with a fresh ID.

**Notes**:

[v3 brief repaired from cited content; was: '4.2 When new items are added']

### JR-ML-OBS-058 — Address residual follow-ups from METRICS-MON program close.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md` (lines 1-100)

**Notes**:

Captured in POST_METRICS_MON_TRACKER; deferred after program closure.

### JR-ML-OBS-059 — Re-bucket cascor_ws_command_handler_seconds for better SLO breach-detection precision post-soak.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md` (lines 173-182)

**Detail**:

G7 - 50 ms SLO target sits one bucket below 100 ms +inf cap, limiting breach-detection precision.
Deferred to R5.1c post-soak calibration per juniper-cascor/notes/HISTOGRAM_BUCKETS_RATIONALE.md.

### JR-ML-OBS-060 — Gap**: During rapid cascade additions (e.g., 2+ hidden units in < 5 seconds), intermediate states may be missed. The topology will jump….

**Status**: rejected  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 93-143)

**Detail**:

**Repositories**: juniper-cascor, juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '1.2 Network Topology Visualization Issues']

### JR-ML-OBS-061 — """Exception during REST poll must NOT overwrite topology store.""".

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 736-760)

**Detail**:

mock_requests.get.return_value = Mock(ok=False, status_code=503)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 1 Tests']

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

### JR-ML-OBS-065 — 5 fast/slow pairs = 10 MWMBR rules of the 16 page+ticket count;.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 456-472)

**Detail**:

| 3.1 Canopy dashboard availability | `CanopyDashboardAvailabilityFastBurn` | `CanopyDashboardAvailabilitySlowBurn` |

**Notes**:

[v3 brief repaired from cited content; was: '7.2 MWMBR burn-rate pairs']

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

### JR-ML-OBS-074 — Alert rules and recording rules exist but are not mounted in Prometheus container (see DD-DC-03).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 292-300)

**Detail**:

| DD-OBS-01 | **High**   | AlertManager config exists but is never deployed (see DD-DC-02).                                  |

**Notes**:

[v4 brief repaired; was: '5.4 Observability Issues']

### JR-ML-OBS-075 — All major exports re-exported through `juniper_data/api/observability.py` (back-compat shim); `DependencyStatus` / `ReadinessResponse` impor.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 236-249)

**Detail**:

| Repo | Declares dep in `pyproject.toml`? | Imports `juniper_observability`? | Components imported |

**Notes**:

[v4 brief repaired; was: '4.2 Adoption matrix']

### JR-ML-OBS-076 — Background.** The post-METRICS-MON state report (juniper-ml#223 §15) found that `juniper_data_datasets_cached` Gauge is defined in….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 307-334)

**Detail**:

**Severity:** P2 · **Owner repo:** juniper-data · **Status:** in-flight (sister PR opened 2026-05-06)

**Notes**:

[v3 brief repaired from cited content; was: '3.11 DATA-CACHED-WIRE — `juniper_data_datasets_cached` Gauge']

### JR-ML-OBS-077 — Based on the existing Docker Compose architecture, a k8s deployment would need:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 364-385)

**Detail**:

## 6. Client & Worker Analysis

**Notes**:

[v3 brief repaired from cited content; was: '5.2 Requirements for K8s Support']

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

### JR-ML-OBS-081 — Categories: 5 RED panels (Request Rate, Error Rate, p95 Latency stats +.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 330-360)

**Detail**:

Categories: 5 RED panels (Request Rate, Error Rate, p95 Latency stats +

**Notes**:

[v3 brief repaired from cited content; was: '6.2 juniper-canopy.json (18 panels, version 3, title "Junipe']

### JR-ML-OBS-082 — Complete baseline metrics and observability inventory analysis.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_ANALYSIS_2026-04-25.md` (lines 1-100)

**Notes**:

BASELINE phase of METRICS-MON program.

### JR-ML-OBS-083 — Convergence Detection checkbox (default: enabled).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 19-31)

**Detail**:

The Training Parameters card (`dashboard_manager.py` lines 417-512) contains a flat list of 6 inputs:

**Notes**:

[v3 brief repaired from cited content; was: 'Current State']

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

### JR-ML-OBS-084 — Cross-link: panels bind catalog §3.5 (`dataset_post_total`) and §4.7.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 400-424)

**Detail**:

Cross-link: panels bind catalog §3.5 (`dataset_post_total`) and §4.7.

**Notes**:

[v3 brief repaired from cited content; was: '6.4 juniper-data.json (17 panels, version 3, title "JuniperD']

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

### JR-CAS-OBS-004 — Define performance targets for latency and throughput.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

Benchmark harness needed to measure actual performance against targets.

### JR-ML-OBS-085 — DEPLOY-02: AlertManager Service Missing from docker-compose.yml.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3352-3366)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-OBS-086 — Design and implement worker heartbeat protocol for CasCor distributed training.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md` (lines 1-50)

### JR-ML-OBS-087 — Document all metrics: Prometheus exposition format, cardinality limits, label guidelines.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-08_JUNIPER-ECOSYSTEM_METRICS-DOCUMENTATION.md` (lines 1-50)

### JR-ML-OBS-088 — Duplicate `_success_envelope` definition (dead code).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 255-265)

**Detail**:

- `response.json()` not protected against non-JSON 200 responses

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-OBS-089 — Effort**: 3-4 days | **Repo**: juniper-canopy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 649-657)

**Detail**:

**Effort**: 3-4 days | **Repo**: juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '6.2 P5-RC-14 + P5-RC-05: WebSocket Consumption']

### JR-ML-OBS-090 — emitted_at_monotonic: float on every /ws/training broadcast envelope.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 78-78)

**Notes**:

Settled position C-41 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-091 — Execute metrics and monitoring code review across Juniper services.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md` (lines 1-100)

**Notes**:

PROPOSED phase; awaiting kickoff.

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

### JR-ML-OBS-093 — **File**: `juniper-canopy/src/backend/cascor_service_adapter.py`.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 437-457)

**Detail**:

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-OBS-094 — GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy /api/ws_latency + histogram).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 57-57)

**Notes**:

Settled position C-20 from R3-03 table; cross-round consensus consolidation

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

### JR-ML-OBS-096 — Implement unified health probe semantics and status code propagation across Juniper services.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md` (lines 1-50)

**Notes**:

R1.2 phase of METRICS-MON program.

### JR-ML-OBS-097 — `is_alive()` catches both `JuniperCascorClientError` and builtin `ConnectionError`. The latter is dead code — `requests.ConnectionError` pro.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 52-62)

**Detail**:

| ID        | Severity   | File:Line                    | Description

**Notes**:

[v4 brief repaired; was: '1.1 Bugs']

### JR-ML-OBS-098 — Issues Previously Identified and Now Resolved.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 794-809)

**Detail**:

| RC-1: Stale editable install | DATASET_DISPLAY_BUG_ANALYSIS.md | Fixed: `get_dataset_data()` added to client, version bumped to 0.3.0 |

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

### JR-ML-OBS-101 — M-JD-1: Sentry PII enabled by default (`observability.py:139`).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 142-150)

**Detail**:

**M-JD-1: Sentry PII enabled by default** (`observability.py:139`)

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-CAN-OBS-014 — Multiple hardcoded localhost:8050 URLs in MetricsPanel (6+ instances) prevent non-local deployment and cross-origin access.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_5/PHASE_5_CANOPY_CASCOR_CONNECTION_ANALYSIS_8b7d1ee8-a24d-4e2a-bfd6-8df44d7ed326.md` (lines 415-445)

**Detail**:

Lines 1050, 1075, 1085, 1095, 1105, 1110 reference hardcoded localhost:8050. Must use environment variable or configuration endpoint.

**Notes**:

Blocks deployment to non-localhost targets.

### JR-ML-OBS-102 — Must handle conda activation from Python (tricky).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 529-564)

**Detail**:

**Risk**: Medium. New code means new bugs. Conda activation from Python subprocess is notoriously fragile.

**Notes**:

[v3 brief repaired from cited content; was: '9.2 Approach B: Unified CLI Tool (juniper-ctl)']

### JR-ML-OBS-103 — Neural network training, CPU/memory intensive.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 46-54)

**Notes**:

[v4 brief repaired; was: '2.5 Resource limits']

### JR-ML-OBS-104 — nohup redirect to timestamped files.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 444-453)

**Notes**:

[v4 brief repaired; was: '7.4 Logging']

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

### JR-ML-OBS-107 — Output("network-visualizer-topology-store", "data"),.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 215-245)

**Detail**:

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

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

### JR-ML-OBS-111 — Per `juniper_observability/__init__.py`:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 222-236)

**Detail**:

- **Constants (R1.1/R1.2/R1.3 contract):**

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Public symbols']

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

### JR-ML-OBS-114 — Phase 0-cascor (seq/replay/resume) — ✅ IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 302-315)

**Detail**:

| Send timeout (0.5s, GAP-WS-07 quick-fix)                               | ✅                                              |

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

### JR-ML-OBS-117 — Primary catalog / program docs.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 721-728)

**Detail**:

- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (juniper-ml#195 / #194)

### JR-ML-OBS-118 — pytest tests/unit/test_response_normalization.py -v       # All must pass (0 failures).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 291-302)

**Detail**:

pytest tests/unit/test_response_normalization.py -v       # All must pass (0 failures)

**Notes**:

[v3 brief repaired from cited content; was: '8.1 Automated Tests']

### JR-ML-OBS-119 — References `max-epochs-input`, old IDs, and `"Training Parameters"` label.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 503-522)

**Detail**:

| `test_convergence_layout.py`         | Update for removed `convergence-enabled-checkbox`, new radio group        |

**Notes**:

[v4 brief repaired; was: '8.4 Existing Tests Requiring Updates']

### JR-ML-OBS-120 — Removed callback**: `handle_parameter_changes` - returns `dash.no_update` unconditionally, only logs. Logging can move to….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 197-214)

**Detail**:

**Removed callback**: `handle_parameter_changes` - returns `dash.no_update` unconditionally, only logs. Logging can move to `track_param_changes`.

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Callback Summary']

### JR-ML-OBS-121 — Replace `Dict[str, Any]` returns in `BackendProtocol` with TypedDicts or dataclasses:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 619-649)

**Detail**:

**Effort**: 3-5 days | **Repo**: juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '6.1 P5-RC-18: Typed Backend Contract']

### JR-ML-OBS-122 — Requires JuniperCascor and JuniperData to be running and healthy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 342-388)

**Detail**:

- Simulates realistic training lifecycle: idle → training → paused → complete

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Purpose and Analysis of Current Modes']

### JR-ML-OBS-123 — Resolve duplicated observability types (DependencyStatus, ReadinessResponse) across repos.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md` (lines 1-50)

**Notes**:

Establish shared observability library.

### JR-ML-OBS-124 — Retirement procedure: `git mv notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md notes/legacy/` in a doc-only PR; leave a tombstone….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 388-409)

**Detail**:

- A successor tracker (e.g. `POST_METRICS_MON_TRACKER_2026-09-01.md` for a 2026-Q3 program close) supersedes it.

**Notes**:

[v3 brief repaired from cited content; was: '4.3 When the tracker itself can be retired']

### JR-ML-OBS-125 — return {}          # <-- BUG: overwrites store with empty dict.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 111-142)

**Detail**:

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-OBS-126 — **Risk**: Low-Medium. systemd is well-understood, but conda integration adds complexity.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 564-591)

**Detail**:

Standardize on systemd user services for host-mode and enhance the juniper-deploy Makefile for container mode. Remove the bash orchestration scripts.

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Approach C: systemd-First + Makefile Enhancement']

### JR-DAT-OBS-006 — SARIF upload must fail on error, not continue-on-error.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 70-71)

**Notes**:

INF-004 MEDIUM (P2). ci.yml:320.

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

### JR-ML-OBS-131 — Step 4: Commit Strategy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 146-154)

**Detail**:

1. **Phase 6 training improvements**: Constants, demo_mode algorithm changes, demo_backend, phase6 tests

### JR-ML-OBS-132 — **Strengths**: Comprehensive fix, prevents the same class of bug across all tabs.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 152-202)

**Detail**:

#### Approach A: Return `dash.no_update` on error (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

### JR-ML-OBS-133 — The `juniper-deploy` repository provides Docker Compose orchestration with 5 profiles:.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 292-313)

**Detail**:

Profile: observability (additive)

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Architecture Overview']

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

### JR-CAN-OBS-015 — Training History must record dataset swap as first-class event with timestamp, before/after config, and architecture changes.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 41-42)

**Detail**:

F2.7: History shall record swap with timestamp + before/after cfg. F2.8: Snapshot captured at swap point. F2.9: Replay must handle sessions with swaps.

**Notes**:

Persistence schema TBD during review.

### JR-ML-OBS-135 — Trigger / due date. No fixed date — fires off CALIB-01 ratification, expected mid- to late-June 2026.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 97-124)

**Detail**:

**Severity:** P2 · **Owner repo:** juniper-cascor · **Status:** open (depends on CALIB-01)

**Notes**:

[v3 brief repaired from cited content; was: '3.2 R5.1c-BUCKETS — Cascor sub-ms bucket re-evaluation']

### JR-ML-OBS-136 — `_update_topology_store_handler()` in `dashboard_manager.py` returns `{}` when the REST poll fails, instead of `dash.no_update`. This empty….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 107-111)

**Detail**:

`_update_topology_store_handler()` in `dashboard_manager.py` returns `{}` when the REST poll fails, instead of `dash.no_update`. This empty dict flows into the NetworkVisualizer callback where the guard `topology_data.get("input_units", 0) == 0` evaluates to `True`, rendering an empty graph.

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-CAS-OBS-005 — Verify WebSocket responsiveness under load when training runs via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 870-874)

### JR-ML-OBS-137 — **Weaknesses**: Additional REST call for raw format, two stores to maintain.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 555-605)

**Detail**:

#### Approach A: Dual-store architecture (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

### JR-ML-OBS-138 — When `cascade_add` is received via WebSocket from CasCor, the Canopy adapter in `start_metrics_relay()` reacts by making a REST call to….

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 207-215)

**Detail**:

When `cascade_add` is received via WebSocket from CasCor, the Canopy adapter in `start_metrics_relay()` reacts by making a REST call to CasCor's `/v1/network/topology` endpoint, transforms the result via `_transform_topology()`, and broadcasts it via Canopy's internal `websocket_manager.broadcast()`

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-OBS-139 — Why This Causes the Blank After Hidden Unit Addition.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 142-152)

**Detail**:

When CasCor adds a hidden unit via `grow_network()`, there is a brief transient window where the network state is being reorganized (output weights resized, new unit installed). If the Canopy REST poll hits `/api/topology` during this window and receives a 503 (or timeout), the handler returns `{}`,

### JR-ML-OBS-140 — Work Unit 5: Code Cleanup — Remove Redundant Inline Styles (LOW) — IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 161-201)

**Detail**:

Removed all 13 `style={"backgroundColor": "#f8f9fa"}` attributes from `dbc.CardHeader` instances across 4 files. The CSS rule `.card-header { background-color: var(--bg-secondary) !important;

### JR-ML-OBS-141 — ws-metrics-buffer store shape = {events, gen, last_drain_ms}.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 55-55)

**Notes**:

Settled position C-18 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-142 — │   cascade_add ───┼── broadcast ─┤── topology hint   │  ← count only, not full topology.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 472-492)

**Detail**:

## 6. Risk Assessment and Guardrails

**Notes**:

[v3 brief repaired from cited content; was: '5.3 Architecture Diagram: WebSocket Message Flow']

### JR-ML-OBS-143 — The design doc `juniper-cascor` PR #194 (`notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md`, merged 2026-05-03) captures two key….

**Status**: shipped  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 207-227)

**Detail**:

**Severity:** P3 (user-discretion) · **Owner repo:** juniper-cascor · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.6 TRAIN-ARCH-01 — Cascor mini-batch restoration']

### JR-ML-OBS-144 — Closing PRs (commit hashes verified against current `origin/main`).

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 746-764)

**Detail**:

| juniper-cascor | #204 | obs-wire-01: wire 5 cascor metric emission sites + lazy-init race fix |

### JR-ML-OBS-145 — **The work** (when un-deferred): A 3-4 PR sub-track (constants → config → output.

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 126-176)

**Detail**:

- **Status**: deferred (user explicitly paused at design-doc stage)

**Notes**:

[v3 brief repaired from cited content; was: '3.3 TRAIN-ARCH-01 cascor mini-batch restoration']

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

### JR-ML-OBS-147 — Defer full worker migration; adopt only R1.2 probe contract constants.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md` (lines 1-100)

**Notes**:

Decided: no full migration now. Use contract constants only.

### JR-ML-OBS-148 — The following issues were identified through cross-referencing all prior documents against the current codebase. Issues are ordered by….

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 82-105)

**Detail**:

| CANOPY_DASHBOARD_DISPLAY_FIXES.md          | 3 display issues (metrics, dataset, topology) | Issue 3 (output weights transposition): **FIXED** (committed in adapter). Issues 1-2: **FIXED** per CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md |

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Documents in `notes/`']

### JR-CAN-OBS-016 — All print() statements must be replaced with logger.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 237-237)

**Detail**:

Issue 5.2.3: print() bypasses logging config. Replace with appropriate
logger.info/debug/warning calls throughout codebase.

### JR-CAN-OBS-017 — FATAL_LEVEL constant conflict must be resolved.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 238-238)

**Detail**:

Issue 5.2.4: FATAL_LEVEL defined in multiple modules with different values.
Consolidate to single definition in logging module.

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

### JR-ML-OBS-149 — Plan post-R5 observability program enhancements.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md` (lines 1-100)

**Notes**:

After R5 completion; scope TBD.

### JR-REC-OBS-001 — Experiment-lane observability toggles

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 444-456)
- `juniper-ml/util/experiment_stack.bash` (lines 7-19)

**Detail**:

Metrics exposition on + rate-limit off for per-run scrape lanes; targets labeled `service`/`environment=host-experiment`/`run_id`/`experiment` via the launcher's file_sd bridge.
