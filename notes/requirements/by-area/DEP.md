# Requirements — DEP

**Area**: deployment-config — Docker, Compose, K8s, Helm, image build

**Total entries**: 66

**By status**: proposed=53 | designed=6 | shipped=5 | deferred=2

**By priority**: P0=6 | P1=20 | P2=31 | P3=9

**By owner**: ml=50 | dep=6 | can=6 | dat=1 | cwk=1 | cas=1 | rec=1

---

### JR-ML-DEP-001 — Background.** Per `SLO_CATALOG_2026-05-03.md` §2.6 ("Provisional-targets caveat"), every R5.4 burn-rate alert ships in *log-only severity*….

**Status**: shipped  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 156-182)

**Detail**:

**Severity:** P1 · **Owner repo:** juniper-deploy · **Status:** blocked (gated on CALIB-01 + OBS-ROUTE-CRED)

**Notes**:

[v3 brief repaired from cited content; was: '3.4 LIFT-01 — R5.4 alert log-only-severity gate lift']

### JR-ML-DEP-002 — Aggregate Results.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 14-28)

**Detail**:

| juniper-ml            | 0.3.0   | 88 pass          | N/A (meta) | 16/16 pass   | 1        | 4      | 3      | 8      |

### JR-ML-DEP-003 — Critical startup/shutdown fixes (plant/chop scripts).

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 280-289)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 216-225)

**Notes**:

[v4 brief repaired; was: '9.1 Completed Phases']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DEP-004 — **Deployment artifacts**: None (no Dockerfile, no systemd, no scripts).

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 127-152)

**Detail**:

- **Type**: Pure HTTP client library

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Per-Client/Worker Inventory']

### JR-ML-DEP-005 — **File**: [`alertmanager/alertmanager.yml`](https://github.com/pcalnon/juniper-deploy/blob/main/alertmanager/alertmanager.yml) (cross-repo).

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 97-126)

**Detail**:

- **Status**: open — operational gap

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Alertmanager `tickets` receiver placeholder']

### JR-ML-DEP-006 — PyPI packages can be yanked (not deleted) if critical issues found post-release.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 394-412)

**Detail**:

- All git tags can be deleted and recreated: `git tag -d v<VERSION> && git push --delete origin v<VERSION>`

**Notes**:

[v3 brief repaired from cited content; was: 'Rollback Plan']

### JR-DAT-DEP-001 — Dockerfile implements multi-stage build, python:3.11-slim, non-root UID 1000, port 8100, HEALTHCHECK.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 154-181)

**Notes**:

DATA-006 complete. .dockerignore excludes development artifacts.

### JR-ML-DEP-007 — Release juniper-ml v0.4.1 + juniper-observability v0.1.1a: document release steps, validation, tag/publish.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md` (lines 1-50)

### JR-CWK-DEP-001 — v0.3.0 deployment infrastructure: multi-stage Docker with CPU-only PyTorch, non-root user, reproducible uv pip compile lockfiles; systemd user service and management CLI.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 53-66)

**Detail**:

Docker: multi-stage Dockerfile, CPU-only PyTorch, non-root user, requirements.lock via `uv pip compile` for reproducible builds, .dockerignore. Systemd: scripts/juniper-cascor-worker.service user service unit, scripts/juniper-cascor-worker-ctl management CLI for host-level deployment.

### JR-ML-DEP-008 — CASCOR_SERVER_URL: ws://juniper-cascor:8200/ws/v1/workers.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 689-714)

**Detail**:

context: ../juniper-cascor-worker

**Notes**:

[v3 brief repaired from cited content; was: '9.9 Detailed Design: Worker in Docker Compose']

### JR-ML-DEP-009 — Final resolution**: **MODERATE**. This issue affects deployment portability in Docker, reverse proxy, and non-standard port scenarios — all….

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1138-1146)

**Notes**:

[v2 ARCH→DEP re-bucket] [v3 brief repaired from cited content; was: '7.5 Hardcoded URLs Severity: MODERATE vs LOW']

### JR-ML-DEP-010 — Phase 2 gaps**: Did not examine topology path, parameter mapping, state sync normalization, deployment portability, cross-repo bugs, or….

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 196-207)

**Notes**:

[v2 ARCH→DEP re-bucket] [v3 brief repaired from cited content; was: '3.2 Phase 2: Correct but Too Narrow']

### JR-ML-DEP-011 — RUN pip install --no-cache-dir -r requirements.lock.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 669-689)

**Detail**:

FROM python:3.14-slim AS builder

**Notes**:

[v3 brief repaired from cited content; was: '9.8 Detailed Design: Worker Dockerfile']

### JR-ML-DEP-012 — ├── P5-RC-11  MODERATE: Hardcoded deployment URLs.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1220-1258)

**Notes**:

[v2 ARCH→DEP re-bucket] [v3 brief repaired from cited content; was: '8.4 Root Cause Dependency Graph']

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

### JR-ML-DEP-013 — All items 🔴 NOT STARTED.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 235-251)

**Detail**:

| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Microservices Architecture Roadmap (Phases 5–9)']

### JR-ML-DEP-014 — All items 🔴 NOT STARTED unless otherwise noted.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 299-315)

**Detail**:

| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Microservices Architecture Roadmap (Phases 5–9)']

### JR-DEP-DEP-003 — Define production Docker Compose profile with resource limits, restart policies, log rotation.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 121-152)

**Detail**:

Phase 2 (v0.3.0) production readiness. Add --profile production to docker-compose.yml
or docker-compose.production.yml override. Per-service resource limits (deploy.resources.limits
for CPU and memory), restart policies (restart: always with deploy.restart_policy),
log rotation (Docker logging driver options max-size, max-file).

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

### JR-ML-DEP-015 — Fix image build bugs: observability images not inheriting base image labels correctly.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_IMAGE-BUILD-BUGS.md` (lines 1-50)

### JR-ML-DEP-016 — juniper-deploy P0: define SECRETS_DIR and SECRETS_FILES variables in Makefile.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-DEVELOPMENT-ROADMAP.md` (lines 47-60)

### JR-ML-DEP-017 — Release readiness checklist: pre-commit compliance, test pass, version sync across 6 applications.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 1-50)

### JR-ML-DEP-018 — A.2 Container/Deploy Files.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 831-846)

**Detail**:

| `docker-compose.yml`                  | juniper-deploy | Primary orchestration | Active     |

### JR-ML-DEP-019 — Add `FakeCascorClient` to the `juniper-cascor-client` package that implements the same interface as `JuniperCascorClient` with configurable….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 2870-3070)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 6:']

### JR-ML-DEP-020 — Background.** The R5.1 SLO catalog (juniper-deploy `notes/SLO_CATALOG_2026-05-03.md`) deliberately picked conservative initial targets….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 62-97)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

**Notes**:

[v3 brief repaired from cited content; was: '3.1 CALIB-01 — T+30d SLO target calibration']

### JR-ML-DEP-021 — Cascor listens on container port 8200 but is mapped to host port 8201 in Docker. The client default `base_url` is `http://localhost:8200`….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 409-420)

**Detail**:

**Repositories**: juniper-cascor, juniper-deploy

**Notes**:

[v3 brief repaired from cited content; was: '3.4 Port Mapping Inconsistency']

### JR-DEP-DEP-004 — Create systemd health timer and one-shot units for periodic service health checks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 185-220)

**Detail**:

Six new units (3 timers + 3 one-shots) for juniper-data, juniper-cascor, juniper-canopy.
Timers fire every 30 seconds (OnActiveSec=30, OnUnitActiveSec=30, AccuracySec=5s).
One-shot units run health_check_systemd.sh, query /v1/health/ready endpoint, parse JSON,
output structured results to journal. Non-zero exit enables OnFailure= triggers.

### JR-ML-DEP-022 — **Decision**: Bind to `127.0.0.1:8200` (settings default).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 20-26)

**Detail**:

**Decision**: Bind to `127.0.0.1:8200` (settings default).

**Notes**:

[v3 brief repaired from cited content; was: '2.1 juniper-cascor bind address']

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

### JR-ML-DEP-026 — Fix the existing `juniper_plant_all.bash` and `juniper_chop_all.bash` scripts with health checks, error handling, and configurability. Add….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 504-529)

**Detail**:

Fix the existing `juniper_plant_all.bash` and `juniper_chop_all.bash` scripts with health checks, error handling, and configurability. Add missing systemd units and worker deployment config.

**Notes**:

[v3 brief repaired from cited content; was: '9.1 Approach A: Incremental Fix (Recommended)']

### JR-CAN-DEP-005 — Hardcoded localhost:8050 URLs in MetricsPanel; breaks in Docker/reverse-proxy/non-standard host (ISS-10).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 515-538)

**Detail**:

ISS-10 MODERATE. Multiple metrics_panel.py locations use hardcoded http://localhost:8050 URLs: line 1000 (/api/network/stats), line 1021 (/api/state), line 1155-1231 (metrics layout endpoints), line 1274 (layout delete). No dynamic URL construction method (_api_url()) exists in file — all hardcoded. When canopy runs in Docker, behind reverse proxy, or non-standard host/port, requests fail silently with ConnectionError. Affected panels (network stats, training state, metrics layout management) return fallback/empty data or fail to persist customizations.

**Notes**:

Identified by v4. Validation found 4 additional hardcoded localhost URLs beyond initial 2 identified.

### JR-ML-DEP-027 — **Image availability**: k3s uses containerd, not Docker. Images built with Docker must be imported:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 1472-1672)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 4:']

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

### JR-ML-DEP-029 — Issue**: juniper-cascor uses port 8201 in host mode and Docker published port, but 8200 internally. The `get_cascor_*.bash` scripts….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 424-434)

**Detail**:

**Issue**: juniper-cascor uses port 8201 in host mode and Docker published port, but 8200 internally. The `get_cascor_*.bash` scripts hardcode 8201. Documentati

**Notes**:

[v3 brief repaired from cited content; was: '7.2 Port Assignments']

### JR-ML-DEP-030 — Migrate JuniperCanopy from YAML-based `ConfigManager` to Pydantic v2 `BaseSettings`.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 4251-4451)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 9:']

### JR-ML-DEP-031 — Near-Term (Docker Compose Adoption).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 727-735)

**Detail**:

1. **Create ecosystem-level `docker-compose.yml`**: Define all 3 services + Redis with health-gated dependency ordering. Place at `Juniper/docker-compose.yml` (or `Juniper/juniper/docker-compose.yml`).

### JR-ML-DEP-032 — No Kubernetes manifests exist anywhere in the Juniper ecosystem.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 360-364)

**Notes**:

[v3 brief repaired from cited content; was: '5.1 Current State']

### JR-ML-DEP-033 — Phase 2 (Near-term):  Adopt Option 3 — add FakeCascorClient and FakeDataClient to.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 575-604)

**Detail**:

**Recommended approach: Phased adoption combining Options 1, 3, and 5.**

**Notes**:

[v3 brief repaired from cited content; was: '3.5 Recommendation']

### JR-ML-DEP-034 — Phase 2: systemd & Service Management — ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 243-258)

**Detail**:

| 2.1  | `juniper-data.service` systemd unit                          | ❌ Not in juniper-deploy scripts/ (may be in individual repos) |

### JR-ML-DEP-035 — Recommendation**: Continue with direct URL configuration (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`). Docker Compose DNS will handle….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 616-627)

**Detail**:

**Recommendation**: Continue with direct URL configuration (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`). Docker Compose DNS will handle discovery automatically when contai

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Discovery Approach Evaluation']

### JR-ML-DEP-036 — Release Order Risks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 386-394)

### JR-ML-DEP-037 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 156-169)

**Detail**:

1. Synchronize all version references to target release (0.6.0 recommended given post-0.5.0 features)

### JR-ML-DEP-038 — Security benefit**: JuniperCanopy cannot directly reach JuniperData on the `backend` network. All data requests from Canopy go through….

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 1040-1240)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 3:']

### JR-ML-DEP-039 — Tally by severity.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 412-421)

### JR-ML-DEP-040 — There is no unified multi-service startup mechanism. Each service is started independently:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 97-116)

**Detail**:

There is no unified multi-service startup mechanism. Each service is started independently:

**Notes**:

[v3 brief repaired from cited content; was: '2.1 Current State']

### JR-ML-DEP-041 — Training control (called from `/ws/control` handler and Dash callbacks):.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-DEVELOPMENT-ROADMAP.md` (lines 2348-2548)

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 5:']

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

### JR-ML-DEP-044 — | Repo           | `pyproject.toml` | `AGENTS.md` header | File headers   |.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 353-363)

**Detail**:

| Repo           | `pyproject.toml` | `AGENTS.md` header | File headers   |

**Notes**:

[v4 brief repaired; was: '6.5 Low: Version Header Drift (Multiple Repos)']

### JR-ML-DEP-045 — Background.** Carried forward from R1; never closed (deferred for burn-in). The healthcheck implementation shipped in worker image ≥ 0.4.0;….

**Status**: shipped  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 243-264)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.8 R1.3.4-FLAG — Helm chart `worker.healthcheck.enabled` de']

### JR-ML-DEP-046 — Phase 3: Worker Deployment & Container Integration (P1) -- Short-Term ✅ COMPLETED.

**Status**: designed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 754-785)

**Detail**:

**Goal**: Enable containerized deployment of the distributed worker.

### JR-ML-DEP-047 — **Primary: Approach A (Incremental Fix)** with elements of Approach C for systemd units.

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 591-603)

**Detail**:

**Primary: Approach A (Incremental Fix)** with elements of Approach C for systemd units.

**Notes**:

[v4 brief repaired; was: '9.4 Recommended Approach']

### JR-CAN-DEP-006 — Docker health check should consider curl-based approach.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 251-251)

**Detail**:

Issue 5.4.1: Current health check may not be reliable. Consider switch to
curl-based probe (add curl to base image) for more flexible checks.

### JR-ML-DEP-048 — Phase 4 (Intermediate):  Kubernetes via k3s when multi-machine or production scale is required.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 299-328)

**Detail**:

**Recommended approach: Layered strategy with Docker Compose as the primary orchestrator.**

**Notes**:

[v3 brief repaired from cited content; was: '2.4 Recommendation']

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

### JR-CAS-DEP-001 — Validate docker-compose configuration for 3-service deployment end-to-end.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 594-603)

**Detail**:

docker-compose config for 3-service deployment not tested end-to-end.

### JR-REC-DEP-001 — Dedicated conda environment decision (Q-10)

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 1262-1274)

**Detail**:

Recurrence currently rides `JuniperCascor1` (works today; editable install + console script live there). A dedicated lighter env is probably right for hygiene — explicitly an owner call; nothing blocks on it.
