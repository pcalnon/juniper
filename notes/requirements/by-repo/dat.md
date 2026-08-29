# Requirements — juniper-data (dat)

**Total entries**: 44

**By status**: proposed=14 | shipped=27 | deferred=3

**By priority**: P0=10 | P1=18 | P2=10 | P3=6

**By category**: TEST=13 | DATA=7 | OBS=7 | API=6 | SEC=3 | TOOL=2 | DOC=2 | LOCK=1 | DEP=1 | PERF=1 | WS=1

---

### JR-DAT-DATA-001 — All 7 storage backends implemented and tested: memory, localfs, cached, redis, hf, postgres, kaggle

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-015 complete. All implementations present.

### JR-DAT-DATA-002 — All 8 generators registered in GENERATOR_REGISTRY: spiral, xor, gaussian, circles, checkerboard, csv_import, mnist, arc_agi

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-17.md` (lines 29-32)

**Notes**:

Status verified as shipped. All 8 confirmed in api/routes/generators.py. RD-001.

### JR-DAT-SEC-001 — API security includes APIKeyAuth authentication and RateLimiter middleware as default behaviors.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-017 complete. security.py confirmed.

### JR-DAT-TEST-001 — Code coverage 99.40% aggregate with 85% per-module minimum enforced in CI.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 165-173)

**Notes**:

RD-005 and RD-007 complete 2026-02-24. 659 tests, 51 modules all >=85%. Reverted to 80% per 2026-03-15 audit.

### JR-DAT-LOCK-001 — Dependabot configuration at .github/dependabot.yml with weekly schedule, grouped updates, PR limits.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 242-323)

**Notes**:

RD-002 complete during migration 2026-02-21. File present, 3 dependabot PRs open.

### JR-DAT-DATA-003 — Lifecycle management supports tagging, TTL, expiration via DatasetMeta (tags, ttl_seconds, expires_at)

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-016 complete.

### JR-DAT-DATA-004 — NPZ contract guarantees 6 array keys with float32 dtype and one-hot label encoding

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 274-292)

**Notes**:

Foundational data contract enforced by E2E tests.

### JR-DAT-TEST-002 — Security boundary test suite includes path traversal, CSV import, input bounds, resource exhaustion, API boundaries.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 201-223)

**Notes**:

RD-006 complete 2026-02-24. 41 tests across 5 classes. Documents path traversal risks in LocalFSDatasetStore and CsvImportGenerator.

### JR-DAT-OBS-001 — Security scanning (Bandit and pip-audit) must fail on vulnerabilities, not suppress with || true or || echo.

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 170-238)

**Notes**:

SEC-001 and SEC-002 CRITICAL. Status shipped per 2026-02-24 migration.

### JR-DAT-TEST-003 — TST-001: test_main.py ImportError handling must assert/skip instead of silent pass.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 329-400)

**Notes**:

TST-001 CRITICAL (P0). Status shipped per migration. Fixes provided in section 3.1.

### JR-DAT-API-001 — All consumers (juniper-cascor, JuniperCanopy) reference juniper-data-client from PyPI (>=0.3.0), not vendored copies.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 333-349)

**Notes**:

RD-011 complete 2026-02-21. Vendored copies removed from all consumers.

### JR-DAT-API-002 — Client package juniper-data-client published to PyPI (>=0.3.0) with Trusted Publishing OIDC.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 313-330)

**Notes**:

RD-010 complete 2026-02-20. Standalone repo pcalnon/juniper-data-client. 41 tests, 96% coverage.

### JR-DAT-DEP-001 — Dockerfile implements multi-stage build, python:3.11-slim, non-root UID 1000, port 8100, HEALTHCHECK.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 154-181)

**Notes**:

DATA-006 complete. .dockerignore excludes development artifacts.

### JR-DAT-TEST-004 — Documentation build step validates internal markdown links in CI, fails on broken links.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 411-430)

**Notes**:

RD-014 complete 2026-02-25. scripts/check_doc_links.py in quality gate. 22 files pass validation.

### JR-DAT-TEST-005 — End-to-end integration tests verify dataset creation, NPZ download, deterministic output, and both algorithm modes.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 210-241)

**Notes**:

DATA-008 complete. 14 E2E tests in test_e2e_workflow.py marked @pytest.mark.integration @pytest.mark.slow.

### JR-DAT-API-003 — Health check endpoints distinguish liveness (/v1/health/live) and readiness (/v1/health/ready).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 186-207)

**Notes**:

DATA-007 complete. 4 integration tests added.

### JR-DAT-TOOL-001 — Line length normalized to 120 characters in [tool.ruff] as single source of truth.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 390-408)

**Notes**:

RD-013 complete 2026-02-25. 24 files reformatted. Current value 320 per 2026-03-15 audit.

### JR-DAT-TOOL-002 — Linter migrated from flake8+isort+black+pyupgrade to ruff v0.15.2.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 359-388)

**Notes**:

RD-012 complete 2026-02-25. 2 ruff hooks replace 5 pre-commit hooks. All 700 tests pass.

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

### JR-DAT-TEST-006 — Performance test infrastructure via pytest-benchmark: 41 baselines for generators and storage.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 269-305)

**Notes**:

RD-009 complete 2026-02-25. tests/performance/ with 21+20 benchmarks. --benchmark-disable default.

### JR-DAT-DATA-005 — Phase 2 partial refactor PR for juniper-data

**Status**: shipped  **Priority**: P1  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/pull_requests/PR_PHASE2_PARTIAL_2026-01-07.md` (lines 1-50)

### JR-DAT-DATA-006 — Phase 3 Wave 1 PR for juniper-data enhancements

**Status**: shipped  **Priority**: P1  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/pull_requests/PR_DESCRIPTION_PHASE3-WAVE-1_2026-01-09.md` (lines 1-50)

### JR-DAT-DATA-007 — Post-refactor v0.24.0 PR for juniper-data

**Status**: shipped  **Priority**: P1  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/pull_requests/PR_DESCRIPTION_POST_REFACTOR_v0.24.0_2026-01-11.md` (lines 1-50)

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

### JR-DAT-SEC-002 — Security hardening includes SecurityHeadersMiddleware, RequestBodyLimitMiddleware, CORS, rate limiting, metrics auth, API docs hiding.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 80-85)

**Notes**:

v0.5.0 released as security hardening. Requires explicit CORS_ORIGINS env var for existing deployments.

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

### JR-DAT-API-006 — API versioning strategy defines version increment, backward-incompatibility, deprecation policy (2 minor versions notice, 6 months support).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 245-265)

**Notes**:

DATA-009 complete. Documented in docs/api/JUNIPER_DATA_API.md.

### JR-DAT-OBS-004 — Coverage reporting must upload to external service (Codecov, Coveralls) for trend tracking.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 68-69)

**Notes**:

INF-002 MEDIUM (P2).

### JR-DAT-TEST-008 — Fix 21 SIM117 violations (nested with statements) by combining where Python 3.11+ allows.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 247-266)

**Notes**:

RD-008 LOW priority deferred. Currently in ruff ignore list in pyproject.toml.

### JR-DAT-SEC-003 — GitHub Actions versions must be pinned to SHA, not floating refs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 62-63)

**Notes**:

SEC-004 MEDIUM (P2). ci.yml:70,73,84, etc.

### JR-DAT-OBS-005 — Histogram R5.1 ratification decides SLO targets p95 <100ms and p99 <1s, optionally collapses low-information buckets.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 71-87)

**Notes**:

Tentative layout pending R5.1 SLO design. HELP-string marker points to rationale doc.

### JR-DAT-DOC-001 — Production startup must use create_app() factory: uvicorn juniper_data.api.app:create_app --factory or python -m juniper_data.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 239-250)

**Notes**:

D-050 MEDIUM priority. Current docs show direct app reference.

### JR-DAT-OBS-006 — SARIF upload must fail on error, not continue-on-error.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 70-71)

**Notes**:

INF-004 MEDIUM (P2). ci.yml:320.

### JR-DAT-TEST-009 — Slow test job must be scheduled separately for integration and performance tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 69-70)

**Notes**:

INF-003 MEDIUM (P2).

### JR-DAT-TEST-010 — Test suite CI/CD enhancement plan (Claude version).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

### JR-DAT-TEST-011 — TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN for juniper-data.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 1-50)

### JR-DAT-OBS-007 — Continuous profiling (Grafana Pyroscope, Prometheus, OpenTelemetry) deferred until production deployment.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 493-516)

**Notes**:

RD-017 (DATA-020). Deferred. Partially addressed with Prometheus + Sentry in commit 830a0ef.

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

### JR-DAT-DOC-002 — AGENTS.md must document current project structure, components, security, dependencies (15+ entries for components).

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 45-64)

**Notes**:

D-001 through D-050 catalogued. 5 CRITICAL issues (version, security, line length, directory, middleware).

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
