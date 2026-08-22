# Requirements — TEST

**Area**: testing-and-ci — pytest, fixtures, CI workflows, regression analysis

**Total entries**: 133

**By status**: proposed=106 | designed=2 | in-progress=1 | shipped=22 | deferred=1 | superseded=1

**By priority**: P0=6 | P1=59 | P2=60 | P3=8

**By owner**: can=44 | ml=43 | cas=19 | dat=13 | ccl=5 | cwk=3 | rec=3 | dep=2 | dcl=1

---

### JR-DAT-TEST-001 — Code coverage 99.40% aggregate with 85% per-module minimum enforced in CI.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 165-173)

**Notes**:

RD-005 and RD-007 complete 2026-02-24. 659 tests, 51 modules all >=85%. Reverted to 80% per 2026-03-15 audit.

### JR-CAS-TEST-001 — Increase serialization test coverage to ≥80% for snapshot_serializer.py.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 102-147)

### JR-DAT-TEST-002 — Security boundary test suite includes path traversal, CSV import, input bounds, resource exhaustion, API boundaries.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 201-223)

**Notes**:

RD-006 complete 2026-02-24. 41 tests across 5 classes. Documents path traversal risks in LocalFSDatasetStore and CsvImportGenerator.

### JR-DAT-TEST-003 — TST-001: test_main.py ImportError handling must assert/skip instead of silent pass.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 329-400)

**Notes**:

TST-001 CRITICAL (P0). Status shipped per migration. Fixes provided in section 3.1.

### JR-ML-TEST-001 — `batch_update_tags`: `if add_tags:` truthiness check means `add_tags=[]` (empty list) omits key from payload. Server may interpret absence d.

**Status**: proposed  **Priority**: P0  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 220-229)

**Detail**:

| ID        | Severity     | File:Line                       | Description

**Notes**:

[v4 brief repaired; was: '4.1 Bugs']

### JR-ML-TEST-002 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 48-53)

**Detail**:

**C-ML-1: Missing git tags for v0.2.1 and v0.3.0**

### JR-CCL-TEST-001 — Align FakeCascorClient response format with real cascor ResponseEnvelope structure for consumer parity.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 65-76)

**Detail**:

Wrap all FakeCascorClient responses in _success_envelope() matching real cascor envelope format.
Ensures consumer code working against fake also works against real backend.

**Notes**:

Shipped in v0.3.0 (2026-03-30); bug fix

### JR-CCL-TEST-002 — Configure pre-commit hooks for markdownlint, shellcheck, flake8, bandit, yamllint quality gates.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAS-TEST-002 — Create comprehensive test suite for serialization with 6+ test cases.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 38-51)

**Detail**:

Implement test_deterministic_training_resume, test_hidden_units_preservation, test_config_roundtrip, test_activation_function_restoration, test_torch_random_state_restoration, test_history_preservation.

### JR-CAS-TEST-003 — Create GitHub Actions CI/CD workflow with pytest, coverage, mypy, and linting.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 467-507)

### JR-CCL-TEST-003 — Create juniper_cascor_client.testing submodule with FakeCascorClient and FakeCascorTrainingStream for consumer testing.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 34-42)

**Detail**:

Provide in-process fake client matching real client interface. Support update_params() with scenario-aware state updates.
Consumers can switch between real and fake by importing from one or the other.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

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

### JR-CAN-TEST-001 — Integration and enhancements PR v0.31.0+: CasCor backend, JuniperData, 4-phase test suite, CI/CD parity (80 commits, 28,855 LOC).

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/pull_requests/PR_DESCRIPTION_INTEGRATION_AND_ENHANCEMENTS_2026-02-18.md` (lines 1-100)

**Detail**:

Consolidates 80 commits delivering: CasCor backend (async training, remote workers), JuniperData (REST client, Docker Compose), 4-phase test suite (42+ integration, 20+ unit, 13+ regression), CI/CD parity. 182 files changed, 28,855 net LOC additions.

**PRs**: #146

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-CAS-TEST-004 — Migrate scheduled-tests.yml from conda to pip; complete Phase 1 CI pipeline enhancement.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/CI_PIPELINE_DEVELOPMENT_PLAN.md` (lines 1-100)

**Detail**:

Phase 1 complete (2026-02-22): conda environments → pip requirements. Phases 2-3: remove pytest-asyncio duplicates, expand MyPy coverage to api/, cascor_constants/, remote_client/ modules. Gap analysis identified 5 issues: scheduled-tests conda, pre-commit version mismatch, MyPy pattern expansion, conftest CLI flag audit.

**Notes**:

[v2 remap: CI→TEST]

### JR-DAT-TEST-006 — Performance test infrastructure via pytest-benchmark: 41 baselines for generators and storage.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 269-305)

**Notes**:

RD-009 complete 2026-02-25. tests/performance/ with 21+20 benchmarks. --benchmark-disable default.

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

### JR-CAN-TEST-004 — Phase 3 Complete—Fixed weak tests, unconditional skips, exception suppression.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 31-39)

**Detail**:

Epic 3.1: Reduced in [200, 503] permissive patterns from 21 to 5. Epic 3.2: Converted
9 unconditional skips to conditional with documentation (ADR-001). Epic 3.3: Fixed
5 exception suppression patterns. Epic 3.4: Re-enabled B905, F401, B008. Epic 3.5:
Removed duplicate test classes. Epic 3.6: Converted bug-documenting tests to xfail.

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

### JR-ML-TEST-003 — Complete comprehensive requirements audit and test plan for juniper-canopy with 16 action items.

**Status**: in-progress  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_REQUIREMENTS_AUDIT_AND_TEST_PLAN.md` (lines 1-100)

**Notes**:

Prerequisite for other canopy development items.

### JR-ML-TEST-004 — **Keeps Proposal B's issue coverage** where it prevents omissions (P5-RC-08, P5-RC-09, P5-RC-10, P5-RC-12b).

**Status**: designed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1674-1682)

**Notes**:

[v2 ARCH→TEST re-bucket] [v3 brief repaired from cited content; was: '16.2 Key Reconciliation Decisions']

### JR-ML-TEST-005 — pytest tests/integration/ -v -m "not requires_cascor".

**Status**: designed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1486-1504)

**Notes**:

[v2 ARCH→TEST re-bucket] [v3 brief repaired from cited content; was: '14.1 Automated Tests']

### JR-ML-TEST-006 — 05: Playwright misses real-cascor regression.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 379-380)

**Notes**:

[v2 ARCH→TEST re-bucket]

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

### JR-ML-TEST-007 — Add macOS CI matrix leg to all repos for cross-platform coverage (rss_mb sampling, POSIX assumptions).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 75-125)

**Detail**:

R3.7 Resolution: Use macos-latest (ARM); run all unit tests (not integration/perf); start in continue-on-error mode for 2 weeks, then make required.

**Notes**:

macOS-13 (Intel) removed as deprecated.

### JR-ML-TEST-008 — Align CI/pre-commit across 8 repos to common baseline: same union of workflows, hooks, pre-commit config.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-PIPELINE-ALIGNMENT-PLAN.md` (lines 28-42)

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

### JR-ML-TEST-009 — C-32: Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 282-283)

**Notes**:

[v2 ARCH→TEST re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-TEST-010 — C-34: Contract-test pytest marker `contract` runs on every PR in all 3 repos.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 283-284)

**Notes**:

[v2 ARCH→TEST re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-CAN-TEST-012 — CI must upload coverage reports to Codecov.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 117-117)

**Detail**:

Issue 2.1.5: .github/workflows/ci.yml missing Codecov step. Add upload
after test run for coverage tracking and status badges.

### JR-ML-TEST-011 — Comprehensive testing strategy for WebSocket migration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-05-TESTING-VALIDATION.md` (lines 1-68)

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

### JR-CAN-TEST-013 — FakeCascorClient.update_params snapshots _network_config to _training_params['params'] at init but update_params does not sync updates, causing verify-roundtrip mismatches.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 41-119)

**Detail**:

When update_params({'learning_rate': 0.005}) is called, _network_config is updated but _training_params['params'] stale snapshot is not, causing get_training_params() to return original value. Workaround: update both locations in FakeCascorClient.update_params.

**PRs**: #264

**Notes**:

Upstream fix pending in juniper-cascor-client. Test currently uses idle scenario workaround.

### JR-ML-TEST-012 — Fix cross-project regression issues with remediation plan.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CROSS_PROJECT_REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-100)

**Notes**:

Active investigation status.

### JR-ML-TEST-013 — Fix regressions identified in 2026-04-03 analysis.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-100)

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

### JR-CCL-TEST-004 — Hardcoded values refactor implementation plan: Phase 1 create constants module, Phase 2 refactor source files, Phase 3 validate test suite and pre-commit, Phase 4 documentation update.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 42-44)
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-48)
- `juniper-cascor-worker/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 1-79)
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 38-41)

**Notes**:

[v2 ARCH→TEST re-bucket] [v3 xrepo fuzzy merge: owners=ccl,cwk,dcl, n=4] Part of hardcoded-values refactor (HIGH priority)

### JR-ML-TEST-014 — Make sentry-sdk a hard runtime dependency and remove importorskip guards in tests.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 61-65)

**Detail**:

R3.4 Resolution (b): Move sentry-sdk to hard runtime dep across cascor/canopy/data. Drop importorskip guards so SEC-15 before_send hook tests run every CI run.

**Notes**:

Security-critical test coverage.

### JR-CAN-TEST-016 — MyPy strict_optional setting conflict must be resolved.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 123-123)

**Detail**:

Issue 2.2.3: MyPy configuration has conflicting strict_optional directives
in different sections. Consolidate to single authoritative setting.

### JR-CAN-TEST-017 — No real UI test sub-suite; browser-automation harness does not exist; no acceptance criterion for UI correctness.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 46-46)

**Detail**:

Fix: new pytest sub-suite + CI lane. Add Selenium or Playwright-based browser automation tests covering all 6 issues. CI budget: <=5 min wall-clock with parallel job + cache + slow marker.

**Notes**:

Quality gate missing; manual testing only.

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

### JR-ML-TEST-015 — Remediate cross-project regression issues identified in 2026-04-03 analysis.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REGRESSION_REMEDIATION_PLAN_2026-04-03.md` (lines 1-100)

### JR-CAN-TEST-021 — Replace 8 always-passing assert True tests with real assertions using pytest.raises().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 86-98)

**Detail**:

Tests in performance and integration suites use assert True in both success and exception branches. Provides false confidence; regressions undetectable.

**Notes**:

Category A: 8 critical test issues; Phase 1 critical

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

### JR-CAS-TEST-007 — Set and enforce minimum coverage thresholds: 70% overall, 80% for core snapshots module.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 632-647)

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

### JR-ML-TEST-021 — Validate CI pipeline: every workflow runs green, soft-fail jobs promoted per-repo to hard gates after shakedown.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-ROADMAP.md` (lines 28-51)

### JR-CAS-TEST-009 — Defer test optimization: reduce 45-minute test suite to ≤5 minutes.

**Status**: deferred  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 37-39)

**Detail**:

Test suite runs in 45+ minutes; target ≤5 minutes. This is a deferred medium-priority optimization (MED-014) per document status.

**Notes**:

Deferred optimization; developer productivity; noted in doc status

### JR-ML-TEST-022 — Issues identified through cross-cutting test coverage and CI analysis across all repositories.

**Status**: superseded  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V5-VALIDATED.md` (lines 738-780)

**Notes**:

[v2 ARCH→TEST re-bucket] [v3 brief repaired from cited content; was: '19. Testing and CI/CD Gaps (v5 new)'] Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-CAN-TEST-023 — 9+ skipped/placeholder tests contain only pass or skip decorator without real test logic.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 1-50)

**Detail**:

Placeholder tests with no assertions or logic do not test anything. Must implement real test logic or remove.

**Notes**:

Identified in test audit; blocks coverage.

### JR-CAS-TEST-010 — Add coverage report --fail-under gate and per-module thresholds to CI.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 501-511)

**Detail**:

CI/CD coverage gates not enforced. Add `coverage report --fail-under=80` to CI,
configure per-module thresholds, add coverage badge to README.

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

### JR-ML-TEST-024 — Add live integration test for juniper-data dataset generation with metrics assertion.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 47-49)

**Detail**:

R3.1: POST /v1/datasets, scrape /metrics, assert juniper_data_dataset_generations_total counter and duration histogram.

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

### JR-CAS-TEST-011 — Always-passing tests with assert True must be replaced with real test logic.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 57-62)

**Detail**:

TST-001: tests in test_training_workflow.py:186-204 always pass. Real test logic
required to validate behavior.

### JR-CAN-TEST-025 — Async/sync boundary (ThreadPoolExecutor fit_async, start_training_background) must have dedicated test coverage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 157-168)

**Detail**:

No tests for concurrent start requests, executor shutdown during training, exception propagation across boundary.
Estimated scope: 1-2 test files, 200-300 lines.

**Notes**:

CAN-HIGH-003; HIGH priority post-release item.

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

### JR-ML-TEST-026 — Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 69-69)

**Notes**:

Settled position C-32 from R3-03 table; cross-round consensus consolidation

### JR-ML-TEST-027 — CI-06: juniper-deploy No Coverage Configuration.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4712-4723)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-CAN-TEST-026 — CI/CD configuration disables 15+ MyPy type checking codes and excludes tests from flake8/mypy, hiding type errors.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_CLAUDE.md` (lines 195-235)

**Detail**:

.pre-commit-config.yaml excludes tests from type checking. ci.yml uses || true on bandit, warnings-only on pip-audit. Must enable strict type checking for tests.

**Notes**:

Allows type errors to ship.

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

### JR-DEP-TEST-002 — Extend compose validation to cover observability and production profiles.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 205-211)

**Detail**:

Phase 4. validate-compose job in ci.yml already validates full, demo, dev profiles.
Extend to validate observability and production profiles as added. Add JSON schema
validation for Grafana dashboard files (Phase 1 output).

### JR-DAT-TEST-008 — Fix 21 SIM117 violations (nested with statements) by combining where Python 3.11+ allows.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 247-266)

**Notes**:

RD-008 LOW priority deferred. Currently in ruff ignore list in pyproject.toml.

### JR-CAS-TEST-013 — Fix conftest.py fast-slow mode logic - inverted semantics for JUNIPER_FAST_SLOW env var.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 441-453)

**Detail**:

Line 83: `os.environ.get("JUNIPER_FAST_SLOW") == "0"` triggers fast-slow mode when
env var is "0", semantically opposite. test_spiral_problem.py:_is_fast_mode() checks == "1".
Align condition to use consistent semantics.

### JR-ML-TEST-033 — For each application (in dependency order):.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 364-375)

**Detail**:

1. Create git tag: `git tag -a v<VERSION> -m "Release v<VERSION>"`

**Notes**:

[v3 brief repaired from cited content; was: '5.2 Per-Application Release Steps']

### JR-ML-TEST-034 — For each radio group, associated inputs are indented (`ms-3` or `ms-4`) and conditionally disabled:.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 385-414)

**Detail**:

html.P("Network Growth Triggers:", className="mb-1 fw-bold"),

**Notes**:

[v3 brief repaired from cited content; was: '6.2 Radio Button Sub-field Pattern']

### JR-ML-TEST-035 — Handler returns `dash.no_update` for the triggering component.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 423-431)

**Detail**:

The `sync_multi_node_checkboxes` callback has components as both Input and Output. This is safe because:

**Notes**:

[v3 brief repaired from cited content; was: '7.2 Circular Dependency Risk']

### JR-ML-TEST-036 — HSK-08: data-client `tests/conftest.py` Version Header Says 0.3.1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2950-2954)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TEST-037 — HSK-12: `NOHUP_STATUS=$?` Captures Fork Status (Always 0).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3031-3045)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-CAS-TEST-014 — Increase code coverage from ~15-78% baseline to 90% target via additional unit tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 543-589)

### JR-CAN-TEST-028 — Integration tests use time.sleep(0.2)-based timing for synchronization across multiple files; fragile and platform-dependent.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 30-30)

**Detail**:

Three sites hardened in PR #264; more remain. Sleep-based timing should be replaced with event-driven synchronization or pytest fixtures.

**Notes**:

Audit recommended for codebase-wide cleanup.

### JR-ML-TEST-038 — Latency tests are recording-only in CI (latency_recording marker); strict assertions local-only.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 72-72)

**Notes**:

Settled position C-35 from R3-03 table; cross-round consensus consolidation

### JR-CAN-TEST-029 — main.py test coverage must increase from 84% to 95% target for critical paths.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 234-246)

**Detail**:

Gap is primarily in real-backend code paths and error handling branches not exercised in demo mode.
Estimated scope: 1-2 test files, 200-300 lines.

**Notes**:

CAN-HIGH-008; HIGH priority post-release item.

### JR-CAN-TEST-030 — Move 5 non-test files (scripts, manual verifiers) out of test directory to util/.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 99-108)

**Detail**:

Files like test_yaml.py, test_dashboard_init.py are print-based scripts with no assertions. Should be moved to util/ for clarity.

**Notes**:

Category B: 5 files; Phase 1 high priority

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

### JR-ML-TEST-041 — `reconnect_backoff_max` not validated against `reconnect_backoff_base`.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 317-324)

**Detail**:

- Sigmoid derivative evaluates `torch.sigmoid` twice per call

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-TEST-042 — Regression analysis and remediation for model training defects.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-03_JUNIPER-ECOSYSTEM_REGRESSION-ANALYSIS.md` (lines 1-50)

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

### JR-CAN-TEST-037 — Remove || true suppression from Bandit security scan in CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 150-155)

**Detail**:

ci.yml line 412: bandit || true suppresses security issues silently. Security should not fail silently.

**Notes**:

Category G: Security scan gap; best practices violation

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

### JR-DCL-TEST-001 — Run full test suite and pre-commit hooks after constants refactor to validate no behavioral changes.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 52-69)

**Detail**:

After completing constants refactor (dcl-010 through dcl-013), must run: (1) Full test suite with
pytest tests/ -v, (2) Pre-commit hooks with pre-commit run --all-files, (3) Verify each generator
(spiral, xor, circle, moon) with default parameters to ensure outputs match pre-refactor results.

### JR-DAT-TEST-009 — Slow test job must be scheduled separately for integration and performance tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 69-70)

**Notes**:

INF-003 MEDIUM (P2).

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

### JR-DAT-TEST-011 — TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN for juniper-data.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 1-50)

### JR-ML-TEST-043 — Update all tests; map `convergence_enabled` from `nn_growth_trigger == "convergence"`.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 414-423)

**Notes**:

[v4 brief repaired; was: '7.1 Breaking Changes']

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

### JR-CAN-TEST-041 — apply_params verify-roundtrip has no retry mechanism on stale reads, could surface as spurious user-facing errors.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 33-33)

**Detail**:

Verify logic does not retry stale reads; timing-sensitive assertion could fail intermittently. Add exponential backoff retry with max attempts.

**Notes**:

Risk of spurious test failures and user-facing errors.

### JR-CAN-TEST-042 — Codebase contains 60+ skipped tests using 'Method _X not exposed as public API' rationale, papering over real coverage gaps.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 34-34)

**Detail**:

60+ skips across h5py-related tests and internal-method probes. Indicates either test suite design issue or missing public API test coverage. Audit to determine if skips are justified or represent untested paths.

**Notes**:

Coverage gaps in h5py and internal method testing.

### JR-CAS-TEST-018 — Create end-to-end integration tests spinning up JuniperData and full pipeline.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 581-591)

**Detail**:

No automated integration tests spin up JuniperData and verify full pipeline (Cascor →
JuniperData → artifact → tensor conversion → training). All current tests use mocks.

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

### JR-CAN-TEST-043 — Pytest tests use CWD-relative paths instead of fixture-based or absolute paths, causing Docker-environment failures.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/OUTSTANDING_TEST_ISSUES_2026-05-10.md` (lines 31-31)

**Detail**:

One file fixed; codebase-wide audit not done. CWD-relative paths fail in container contexts where CWD differs.

**Notes**:

One file fixed; more audit needed.

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

### JR-REC-TEST-001 — Bench harness with pre-registered scope as scoring authority

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-recurrence/bench/run_benchmark.py` (lines 137-149)
- `juniper-recurrence/bench/datasets.py` (lines 262-274)
- `juniper-recurrence/bench/test_bench_smoke.py` (lines 1-13)

**Detail**:

Primary bands scored only on the pre-registered set; extensions (noise sweep, `ar_p` linear floor, `delay_product` capacity, `equities_seq` real data) are informational. Committed `bench/results/` baselines are reproducible from seeds.

### JR-REC-TEST-002 — Service-vs-bench parity as a regression criterion

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md` (lines 1-13)

**Detail**:

A service-mode run with bench-primary-matched params must land inside the same OQ-14 bands as the offline bench; divergence is a service-path defect. Candidate for a periodic (release-gate or scheduled) automated check once `run_suite.py` (Wave 7.1) exists.

### JR-REC-TEST-003 — Concurrent bench runs (per-run results dir)

**Status**: shipped  **Priority**: P2  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-recurrence/bench/run_benchmark.py` (lines 4-16)

**Detail**:

`python -m bench.run_benchmark --results-dir DIR` routes per-dataset JSON + REPORT.md; the default stays the committed `bench/results/` byte-identically.
