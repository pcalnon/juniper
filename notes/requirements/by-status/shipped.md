# Requirements — status: shipped

**Total entries**: 177

**By priority**: P0=39 | P1=94 | P2=40 | P3=4

**By category**: TRAIN=35 | API=25 | TEST=22 | SEC=20 | OBS=17 | UI=14 | DATA=9 | TOOL=9 | DOC=7 | LOCK=5 | DEP=5 | WS=5 | OPS=3 | PERF=1

**By owner**: cas=41 | ml=37 | can=34 | dat=27 | ccl=14 | cwk=12 | rec=9 | dep=2 | dcl=1

---

### JR-ML-OBS-001 — A.5 was tracked but its dashboard half was not explicitly carried.

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 826-876)

**Detail**:

**Finding.** Four dashboard text / inference panels are stale relative

**Notes**:

[v3 brief repaired from cited content; was: '15.2 4 stale dashboard panels post audit-PR closes']

### JR-CAS-LOCK-001 — Add missing PyYAML, h5py, pytest-cov, psutil dependencies to conda environment.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 256-306)

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

### JR-ML-SEC-001 — Background.** OBS-ROUTE-01 (juniper-deploy#60, merged 2026-05-05) closed audit findings 3.2 (P1) and B.1 (P3) by wiring the alertmanager….

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 124-156)

**Detail**:

**Severity:** P1 (soft-blocker) · **Owner repo:** juniper-deploy · **Status:** open

**Notes**:

[v3 brief repaired from cited content; was: '3.3 OBS-ROUTE-CRED — Alertmanager `tickets` receiver real-cr']

### JR-ML-DEP-001 — Background.** Per `SLO_CATALOG_2026-05-03.md` §2.6 ("Provisional-targets caveat"), every R5.4 burn-rate alert ships in *log-only severity*….

**Status**: shipped  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 156-182)

**Detail**:

**Severity:** P1 · **Owner repo:** juniper-deploy · **Status:** blocked (gated on CALIB-01 + OBS-ROUTE-CRED)

**Notes**:

[v3 brief repaired from cited content; was: '3.4 LIFT-01 — R5.4 alert log-only-severity gate lift']

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

### JR-CAS-DOC-001 — Document that CascadeCorrelationNetwork is not thread-safe.

**Status**: shipped  **Priority**: P0  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 183-198)

### JR-DCL-SEC-001 — Enable PyPI build attestations and add scheduled security scanning (Bandit + pip-audit).

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 1-33)

**Detail**:

Supply chain security improvements: enabled build attestations in publish workflow, added
.github/workflows/security-scan.yml for weekly Bandit and pip-audit scanning. Version bump: 0.3.1 → 0.3.2.
All tests passing (88 unit tests, 0 failures).

**Notes**:

Status inferred from PR marked READY_FOR_MERGE with test results. SemVer impact: PATCH (0.3.1 → 0.3.2).
No breaking changes. Medium security/privacy impact (supply chain verification via attestations).

### JR-CAS-TRAIN-001 — Extract spiral data generator to separate provider service; decouple from CasCor training. Completed Phase 5 of spiral data generation refactor.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/JUNIPER_CASCOR_SPIRAL_DATA_GEN_REFACTOR-002.md` (lines 1-50)

**Detail**:

Pure NumPy generator with artifact-first API (NPZ format). Remove torch, matplotlib, logging, multiprocessing from generator. Methods to extract: coordinate generation, feature/label construction, ordering/partitioning. Methods to keep: training-specific logic.

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v2 remap: AR→ARCH]

### JR-CAS-TRAIN-002 — Fix 19 critical issues: type mismatches, gradient descent direction, field names, serialization gaps, multiprocessing errors.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/COMPLETE_FIX_SUMMARY.md` (lines 1-100)

**Detail**:

P0 critical (10): train_candidates type mismatch, candidate_index→candidate_id, best_correlation→correlation, missing candidate field, gradient ascent fix, matrix dimension error, dict access bug, worker return type, snapshot_counter init, 1D/2D tensor indexing. P1 high (5): optimizer serialization, training counter persistence, queue timeouts, early stopping, NumPy 2.0 compatibility. P2 runtime (4): method name collision, dummy results format, trailing comma, validation logic. 35+ modifications across 6 files. 10/10 tests passing (100%).

**Notes**:

[v2 remap: BG→TRAIN]

### JR-ML-TRAIN-001 — Fix activation function mismatch: use tanh instead of sigmoid in demo mode.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 87-103)

**Detail**:

Tanh critical for CasCor algorithm: outputs ∈ {-1,+1} create binary partitions; sigmoid ∈ {0,1} can produce constant features with zero gradient. Sigmoid mean-shift also biases output layer.

**Notes**:

Root cause RC-1; doc status indicates implementation complete

### JR-CAS-TRAIN-003 — Fix candidate task parameter wiring: use correct dictionary keys (candidate_seed, candidate_epochs, candidate_learning_rate).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 235-273)

### JR-CAS-TRAIN-004 — Fix candidate training runtime errors (method name mismatch, pickling, parameter handling).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 94-122)

**Detail**:

Fix _train_candidate_worker → _train_candidate_unit method call mismatch; add __getstate__/__setstate__ to LogConfig and CascadeCorrelationConfig for multiprocessing pickling support; update CascadeCorrelationNetwork.__getstate__ to exclude log_config.

### JR-ML-TRAIN-002 — Fix drain thread race condition in cascor lifecycle manager for candidate progress monitoring.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 121-142)

**Detail**:

Progress queue drain thread checks for queue before it exists in grow_network(). Fix: deferred queue discovery in drain thread or pre-create queue before original_grow().

**Notes**:

Status marked COMPLETE (Section 1, line 7-8); Phase 1 critical fix

### JR-ML-TRAIN-003 — Fix grow progress bar denominator to use max_hidden_units instead of max_epochs.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 104-118)

**Detail**:

Demo mode passes max_epochs (10000) as progress denominator instead of max_hidden_units (10), causing 0.12% → 0% display. Fix: use max_hidden_units in Canopy progress handler, cap at 100%.

**Notes**:

Phase 1 critical fix; doc status COMPLETE

### JR-CAS-TRAIN-005 — Fix logger pickling error in multiprocessing (BUG-002).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 28-36)

**Detail**:

Enhance CascadeCorrelationNetwork and CascadeCorrelationPlotter __getstate__/__setstate__ methods for pickle support; verify CandidateUnit has pickling support.

### JR-ML-TRAIN-004 — Fix loss function: use MSE on raw output instead of BCE with sigmoid.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 104-117)

**Detail**:

BCE residuals bounded [-1,1]; MSE residuals unbounded. MSE gradient stronger; residual magnitude larger. CasCor candidate training mathematically designed around MSE residuals.

**Notes**:

Root cause RC-2; doc status indicates implementation complete

### JR-CAS-TRAIN-006 — Fix multiprocessing completion logic that can hang indefinitely due to unreliable empty()/qsize() usage.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 59-99)

**Detail**:

Replace unreliable busy-wait loop using Manager queue empty()/qsize() with bounded timeout loop. Add worker liveness checks to detect crashed workers early. Exit immediately when all workers complete.

### JR-CAS-TRAIN-007 — Fix plotting subprocess to use spawn context instead of forkserver for reliable module import in child processes.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 342-386)

### JR-CAS-TRAIN-008 — Fix save_object() method TypeError due to argument count mismatch with _save_root_attributes().

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 200-232)

### JR-CAS-TRAIN-009 — Fix test random state restoration failures (BUG-001).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 18-26)

### JR-CAS-API-001 — HDF5 serialization system with UUID persistence, RNG state preservation, and complete state restoration for training resume.

**Status**: shipped  **Priority**: P0  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/FINAL_STATUS.md` (lines 1-100)

**Detail**:

Session 1 (5 items): UUID persistence, Python RNG state, config JSON serialization, history key alignment (value_loss/value_accuracy), activation function restoration. Session 2 (8 items): hidden units checksums, shape validation, format validation, test suite, Python random state fix, config sanitization, plotting regression fix. 18 integration tests (15 passing, 3 timeout). No fabricated commit SHAs or dates.

**Notes**:

[v2 remap: SE→API]

### JR-ML-TRAIN-005 — Increase output retraining from 50 mini-batch steps to full-batch training after hidden unit installation.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 118-131)

**Detail**:

Demo: ~1,600 sample evaluations; CasCor: ~2,000,000 (1,250× difference). New hidden unit weight initialized ~0.1; needs ample optimization time. Current 50 steps insufficient (~0.125 total change).

**Notes**:

Root cause RC-3; doc status indicates implementation complete

### JR-CAS-TEST-001 — Increase serialization test coverage to ≥80% for snapshot_serializer.py.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 102-147)

### JR-DAT-DATA-003 — Lifecycle management supports tagging, TTL, expiration via DatasetMeta (tags, ttl_seconds, expires_at)

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-016 complete.

### JR-ML-SEC-002 — missed, (b) part of a not-yet-implemented WebSocket consumption pathway that.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 216-266)

**Detail**:

> - 2026-04-10 second revision: NEW-01 and canopy-set_params markings reverted as

**Notes**:

[v3 brief repaired from cited content; was: '3.5 Phase 1 Deferred Items — STATUS UPDATE (2026-04-10, REVI']

### JR-DAT-DATA-004 — NPZ contract guarantees 6 array keys with float32 dtype and one-hot label encoding

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 274-292)

**Notes**:

Foundational data contract enforced by E2E tests.

### JR-CAN-OBS-001 — Prometheus histogram bucket rationale: canopy_ws_browser_latency_ms with SLO candidates (p95<25ms, p99<100ms).

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-95)

**Detail**:

WebSocket browser latency metric with 10 buckets [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000] ms mapping to UX thresholds: 5ms (sub-frame 200Hz), 10ms (100Hz frame), 25ms (60Hz display jitter boundary), 50ms (perceived instant threshold), 100ms (noticeable lag, Nielsen), 250ms-5s (degradation signals). SLO candidates: p95 training-WS RTT<25ms, p99 control-WS RTT<100ms. Status: tentative pending R5.1 ratification.

**Notes**:

METRICS-MON sub-track R4.1. May reshape upper buckets (2.5s, 5s) post-R5.1.

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

### JR-ML-TRAIN-006 — Use Adam optimizer instead of vanilla SGD for output training.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 225-242)

**Detail**:

Adam adapts per-parameter effective learning rates using first/second moment estimates. Vanilla SGD shares same lr across all params; new hidden unit columns converge poorly.

**Notes**:

Root cause RC-9; Phase 3 investigation finding; doc status indicates implementation complete

### JR-ML-TRAIN-007 — Use full-batch training between cascade additions instead of mini-batch.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 243-258)

**Detail**:

Mini-batch between cascades (960 evals) undoes full-batch retrain (40,000 evals). High gradient variance causes random walk of carefully retrained weights. Fix: full-batch for 30 epochs instead of mini-batch.

**Notes**:

Root cause RC-10; Phase 3 finding; ~40× weaker training; doc status indicates implementation complete

### JR-CWK-SEC-001 — v0.2.0 breaking change: remove hardcoded default auth key ("juniper"), make WORKER_AUTH_KEY environment variable required at worker startup with clear error message if not set.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 27-50)

**Detail**:

Breaking change for 0.1.0→0.2.0 (SemVer minor allowed pre-1.0). Rationale: hardcoded default allowed any network-accessible actor to register workers. Removed the 'juniper' default. WORKER_AUTH_KEY now REQUIRED with validation at startup (clear error if not set). Migration: set WORKER_AUTH_KEY environment variable explicitly before worker startup. For production: source from secret store (Docker secrets, K8s secrets, Vault, SOPS-encrypted env file) rather than plaintext export.

**Notes**:

Related: v0.3.0 renamed WORKER_AUTH_KEY to CASCOR_AUTH_TOKEN and the CLI flag from --api-key to --auth-token. Operators upgrading directly from v0.1.x to v0.3.0 should consult v0.3.0 release notes for mapping.

### JR-CAS-TRAIN-012 — 18 verified bug fixes across architecture, training logic, serialization, runtime; 15 critical/high items addressed.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 60-90)

**Detail**:

INT-P0 items: walrus operator precedence, ActivationWithDerivative duplication, CandidateUnit constructor params (name-mangled), datetime alias misleading, global declaration, validation logic. INT-P2 items: conftest fast-slow inversion, roll_sequence memory, os._exit usage, traceback imports. INT-P1 items: requests undeclared dependency, JuniperData retry logic, dill dependency. BUG-001/002: random state restoration, logger pickling multiprocessing. Convergence threshold fix. Leaf tensor autograd RuntimeError. Module naming collision (constants→cascor_constants). Polyrepo Phase 1 duplicate elimination. All 18 fixed with codebase validation.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CCL-LOCK-001 — Add JUNIPER_CASCOR_API_KEY environment variable fallback for API key authentication.

**Status**: shipped  **Priority**: P1  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAS-OBS-001 — Add thread safety locks to monitoring loop metrics extraction (CascorIntegration._extract_current_metrics).

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 715-743)

### JR-CWK-DOC-001 — AGENTS.md critical fixes: update version metadata (0.1.0→0.3.0), CLI command flags, env vars defaults, and flake8 line-length to match current codebase.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 9-36)

**Detail**:

Phase 1 critical corrections (blocking): (1.1) Update header version from 0.1.0 to 0.3.0, date to 2026-04-02. (1.2) Replace legacy --host/--port command with WebSocket-mode --server-url/--auth-token as default, add --legacy mode. (1.3) Remove incorrect 'juniper' default for CASCOR_AUTHKEY, add all WebSocket env vars (CASCOR_SERVER_URL, CASCOR_AUTH_TOKEN, CASCOR_HEARTBEAT_INTERVAL, etc.), label legacy-only variables. (1.4) Change flake8 --max-line-length from 120 to 512.

### JR-CWK-DOC-002 — AGENTS.md missing core architecture sections: WebSocket mode, binary tensor protocol, TLS/mTLS support, task executor, exception hierarchy, and deprecation status.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 37-79)

**Detail**:

Phase 2 missing core architecture (high priority): (2.1) Application Architecture section (two-mode WebSocket/legacy, communication flow, worker lifecycle, module dependency graph). (2.2) WebSocket mode docs (CascorWorkerAgent async event loop, WorkerConnection class, binary tensor protocol JSON+struct, TLS/mTLS config). (2.3) Task execution pipeline (execute_training_task, CandidateUnit dynamic import from cascor, --cascor-path flag). (2.4) Public API section (all __init__.py exports, CascorWorkerAgent/CandidateTrainingWorker interfaces, WorkerConfig dataclass, exception hierarchy). (2.5) Complete CLI reference (all flags with WebSocket/Legacy/Shared labels, signal handling, --cascor-path).

### JR-CCL-TEST-001 — Align FakeCascorClient response format with real cascor ResponseEnvelope structure for consumer parity.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 65-76)

**Detail**:

Wrap all FakeCascorClient responses in _success_envelope() matching real cascor envelope format.
Ensures consumer code working against fake also works against real backend.

**Notes**:

Shipped in v0.3.0 (2026-03-30); bug fix

### JR-DAT-API-001 — All consumers (juniper-cascor, JuniperCanopy) reference juniper-data-client from PyPI (>=0.3.0), not vendored copies.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 333-349)

**Notes**:

RD-011 complete 2026-02-21. Vendored copies removed from all consumers.

### JR-CAS-TRAIN-013 — All Phase 1 enhancements from CASCOR_ENHANCEMENTS_ROADMAP implemented and tested.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PHASE1_COMPLETE.md` (lines 9-17)

**Detail**:

Status complete 2025-10-28. BUG-001 (test random state restoration), BUG-002 (logger
pickling error) fixed. ENH-001 through ENH-008 implemented. MVP code-complete and
ready for testing phase. Zero breaking changes. All P0 and P1 work done.

### JR-CAN-SEC-007 — API key timing attack must use hmac.compare_digest() for constant-time comparison.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 79-83)

**Detail**:

HIGH-001: Replace simple set membership check with hmac.compare_digest() in both browser CSRF auth and adapter HMAC auth.
R5-01 Section 4.1 mandates this pattern; remediation already correct per analysis.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; reinforced by R5-01 canonical pattern.

### JR-CAS-API-002 — Build FastAPI service layer for CasCor with REST endpoints and WebSocket streaming.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 728-735)

**Detail**:

Add 19 REST endpoints across 6 route files; WebSocket endpoints for real-time training streaming (/ws/training, /ws/control); TrainingLifecycleManager with thread-safe state machine and ThreadPoolExecutor; service entry point (server.py) alongside existing CLI (main.py).

### JR-CAN-UI-005 — Candidate info section must display and be collapsible with historical pool tracking.

**Status**: shipped  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase1/README.md` (lines 27-93)

**Detail**:

P1-1 feature: always-visible section with toggle icon, historical pools rendered as collapsed cards, top 10 pools maintained.
Implemented in metrics_panel.py with dbc.Collapse wrapper and callback handlers.

**Notes**:

Phase 1 complete feature; shipped status verified from implementation notes.

### JR-CAS-WS-001 — CasCor must expose REST API for training lifecycle operations (19 endpoints).

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-735)

**Detail**:

FastAPI service layer with REST endpoints for all training lifecycle operations; WebSocket endpoints for real-time streaming (/ws/training, /ws/control); ThreadPoolExecutor for blocking training.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-CAS-TRAIN-014 — CasCor service API must serialize training access via lock or dedicated thread.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-674)

**Detail**:

CascadeCorrelationNetwork is NOT thread-safe. API layer must serialize access via a lock or run training in dedicated thread with message-passing interface.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-WS-002 — CascorIntegration → CascorServiceAdapter migration (Phase 4) replacing in-process integration with REST/WebSocket client.

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DECOUPLE_CANOPY_FROM_CASCOR_PLAN.md` (lines 1-100)

**Detail**:

Three-mode activation: demo (CASCOR_DEMO_MODE=1), legacy (CASCOR_BACKEND_PATH), service (CASCOR_SERVICE_URL, new). Adapter constructor: (service_url, api_key). WebSocket relay: CasCor service → adapter → Canopy frontend. Backward-compatible method mapping. 306 lines, 52 tests. Deprecated CascorIntegration 1,601 lines.

**Notes**:

[v2 ARCH→WS re-bucket] [v2 remap: AR→ARCH]

### JR-DAT-API-002 — Client package juniper-data-client published to PyPI (>=0.3.0) with Trusted Publishing OIDC.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 313-330)

**Notes**:

RD-010 complete 2026-02-20. Standalone repo pcalnon/juniper-data-client. 41 tests, 96% coverage.

### JR-CAS-TOOL-002 — Complete CI/CD infrastructure: pre-commit 21 hooks, coverage 80%, GitHub Actions matrix (3.11/3.12/3.13), security scanning.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/pull_requests/PR_full_branch_spiral_gen_extract_pre_deploy.md` (lines 1-100)

**Detail**:

91% test coverage achieved (from ~15%), 1333+ tests. CI pipeline: GitHub Actions matrix (3.11/3.12/3.13), scheduled nightly tests, pre-commit hooks (21 total), coverage enforcement (80%), security scanning (Bandit, Gitleaks, pip-audit). 28 version increments (0.0.1 → 0.7.0). Critical fixes: multiprocessing completion logic, undefined queue_timeout, test timeouts, snapshot serializer TypeError, candidate training result parsing, task parameter wiring, best_candidate_id selection, NaN input handling.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CCL-OPS-001 — Configure Dependabot for automated weekly dependency updates.

**Status**: shipped  **Priority**: P1  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-TEST-002 — Configure pre-commit hooks for markdownlint, shellcheck, flake8, bandit, yamllint quality gates.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-DOC-003 — Create CODEOWNERS file for PR review routing.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-DOC-004 — Create comprehensive documentation suite including DOCUMENTATION_OVERVIEW.md, QUICK_START.md, REFERENCE.md, DEVELOPER_CHEATSHEET.md.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 48-57)

**Detail**:

DOCUMENTATION_OVERVIEW.md (navigation index), QUICK_START.md (installation and first-call walkthrough),
REFERENCE.md (full method and configuration reference), docs/DEVELOPER_CHEATSHEET.md (quick-reference card),
AGENTS.md (thread handoff and worktree procedures), ecosystem compatibility matrix in README, CHANGELOG.md.

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

### JR-CAS-TRAIN-015 — Create juniper-cascor-client and juniper-cascor-worker installable packages with PyPI publishing.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1034-1047)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CCL-TEST-003 — Create juniper_cascor_client.testing submodule with FakeCascorClient and FakeCascorTrainingStream for consumer testing.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 34-42)

**Detail**:

Provide in-process fake client matching real client interface. Support update_params() with scenario-aware state updates.
Consumers can switch between real and fake by importing from one or the other.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAS-TRAIN-016 — Decouple Canopy from CasCor via service client; remove direct imports and sys.path manipulation.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1208-1220)

**Detail**:

Implement CascorServiceAdapter for two-mode activation (demo/service); remove legacy CascorIntegration (~1,601 lines); remove sys.path manipulation; update configuration to use CASCOR_SERVICE_URL (port 8200).

**Notes**:

[v2 ARCH→TRAIN re-bucket]

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

### JR-ML-TRAIN-009 — Derive candidate_pool_phase from phase_detail in Canopy adapter.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 686-709)

**Detail**:

Adapter derives candidate_pool_status but not candidate_pool_phase. One-line fix: map phase_detail to pool phase (Training/Selecting/Idle).

**Notes**:

Phase 2 P1 fix; doc status COMPLETE; simple derivation gap

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

### JR-ML-TRAIN-010 — Enhance grow iteration callback with top 2 candidate ID and correlation data.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 148-167)

**Detail**:

Top candidate info never forwarded from CasCor to Canopy; TrainingResults dataclass contains data but callback does not pass it. Fix: add best_candidate_id, best_candidate_uuid, second_candidate fields to callback signature.

**Notes**:

Phase 2 P1 fix; data already available in TrainingResults; doc status COMPLETE

### JR-CAN-SEC-008 — Exception handler must use opaque error messages and add CRLF escaping in audit logs.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 84-88)

**Detail**:

HIGH-002: Generic error messages + server-side logging per R5-01 Section 4.3 (M-SEC-06).
Add CRLF escaping in audit logs per M-SEC-07 when logs echo client input.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; shipped with opaque messages pattern.

### JR-CAS-TRAIN-017 — Expand format validation for HDF5 snapshot files.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 73-83)

**Detail**:

Check format name/version; validate required groups and datasets; verify hidden units consistency.

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

### JR-CAS-TRAIN-018 — Implement hidden units checksums for integrity verification.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 53-61)

### JR-CCL-API-002 — Implement remote worker monitoring methods: list_workers(), get_worker(worker_id), get_worker_stats().

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 28-35)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CAS-TRAIN-019 — Implement shape validation for serialized network structure.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 63-71)

**Detail**:

Implement _validate_shapes() method; validate output layer and hidden units; call from load_network().

### JR-CCL-API-003 — Implement snapshot management methods: list_snapshots(), get_snapshot(snapshot_id), save_snapshot(), load_snapshot(snapshot_id).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 36-44)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-SEC-001 — Implement SOPS configuration (.sops.yaml) and .env.example for secrets management.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-API-004 — Implement update_params() client method for runtime training parameter updates via PATCH /v1/training/params.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 28-33)

**Detail**:

Add update_params() method to JuniperCascorClient with supporting _patch() helper and PATCH method in ALLOWED_METHODS.
Tests required for both real client (responses mock) and fake client.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

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

### JR-CAS-TEST-004 — Migrate scheduled-tests.yml from conda to pip; complete Phase 1 CI pipeline enhancement.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/CI_PIPELINE_DEVELOPMENT_PLAN.md` (lines 1-100)

**Detail**:

Phase 1 complete (2026-02-22): conda environments → pip requirements. Phases 2-3: remove pytest-asyncio duplicates, expand MyPy coverage to api/, cascor_constants/, remote_client/ modules. Gap analysis identified 5 issues: scheduled-tests conda, pre-commit version mismatch, MyPy pattern expansion, conftest CLI flag audit.

**Notes**:

[v2 remap: CI→TEST]

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

### JR-CAS-TRAIN-020 — Performance optimizations: thread pinning (5-15x), direct queues (3-10x), shared training data, persistent workers (20-50%), cached forward pass (22-1607x isolated).

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 90-120)

**Detail**:

RC-1: torch.set_num_threads(1) + BLAS env vars → 5-15x improvement. RC-2: Direct mp.Queue vs BaseManager → 3-10x additional. RC-3: Shared training data reduces N-fold serialization. RC-4: Persistent worker pool 20-50% latency reduction. OPT-1: Pre-allocated forward buffer eliminates N+1 torch.cat. OPT-2: Batch correlation (torch.dot + linalg.norm) → 5-10%. OPT-4: Cached forward pass 22-1607x isolated, 5-15% total. OPT-5: SharedMemory training tensors 5-20% reduction. OPT-6: Single-output correlation fix 37x speedup (18.24ms → 0.49ms). Forward pass sub-linear (0→50 units = 1.86x). Convergence threshold in patience.

**Notes**:

[v2 remap: BG→TRAIN]

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

### JR-DAT-DATA-005 — Phase 2 partial refactor PR for juniper-data

**Status**: shipped  **Priority**: P1  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/pull_requests/PR_PHASE2_PARTIAL_2026-01-07.md` (lines 1-50)

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

### JR-DAT-DATA-006 — Phase 3 Wave 1 PR for juniper-data enhancements

**Status**: shipped  **Priority**: P1  **Category**: DATA  **Owner**: dat

**Sources**:

- `juniper-data/notes/history/pull_requests/PR_DESCRIPTION_PHASE3-WAVE-1_2026-01-09.md` (lines 1-50)

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

### JR-CAS-API-003 — Polyrepo migration complete: 7 phases, 8 repos, microservices architecture, health checks, version matrix.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 1-100)

**Detail**:

All 7 phases complete (2026-03-02). Phase 0: Stabilize baseline. Phase 1: Extract/publish client packages (juniper-data-client v0.3.1 PyPI). Phase 2: Build CasCor Service API (FastAPI, 19 REST + 2 WS endpoints). Phase 3: Create cascor-client + worker (PyPI v0.1.0 2026-02-24). Phase 4: Decouple Canopy (CascorServiceAdapter 306 lines, CascorIntegration 1,601 deleted, 2026-02-25). Phase 5: Split repos (8 repos, SSH keys, 2026-02-25). Phase 6: Hardening (Docker Compose, health check standardization, 2026-02-25). Phase 7: Production readiness (2026-03-02). Ecosystem compatibility matrix verified.

**Notes**:

[v2 ARCH→API re-bucket] [v2 remap: AR→ARCH]

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

### JR-ML-DEP-007 — Release juniper-ml v0.4.1 + juniper-observability v0.1.1a: document release steps, validation, tag/publish.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md` (lines 1-50)

### JR-DAT-OBS-003 — Release notes document known issues, resolved issues, and What's Next with accurate status.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 89-103)

**Notes**:

RD-001 complete 2026-02-24. Only B008 warnings remain. v0.5.0 scope updated.

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

### JR-CAS-API-004 — REST API and WebSocket architecture: 19 REST endpoints, 2 WS channels, Pydantic models, lifecycle management, remote workers.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 148-165)

**Detail**:

CasCor Service API complete (Phase 2). FastAPI server with 19 REST endpoints, 2 WS channels, full lifecycle management. Training lifecycle: TrainingLifecycleManager, TrainingStateMachine, TrainingMonitor. API security: auth (X-API-Key header, HMAC comparison), rate limiting (fixed-window per IP). WebSocket channels: control, training, workers. Remote worker system: registry, coordinator, binary protocol, security, audit. Decision boundary visualization. Snapshot management routes. Output weight initialization option. Convergence threshold runtime-updateable via PATCH. Pydantic BaseSettings configuration.

**Notes**:

[v2 remap: SE→API]

### JR-DAT-SEC-002 — Security hardening includes SecurityHeadersMiddleware, RequestBodyLimitMiddleware, CORS, rate limiting, metrics auth, API docs hiding.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 80-85)

**Notes**:

v0.5.0 released as security hardening. Requires explicit CORS_ORIGINS env var for existing deployments.

### JR-CAS-API-005 — Serialization critical fixes: UUID persistence, Python RNG state, config JSON serialization, history key alignment, activation function restoration.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/SERIALIZATION_FIXES_SUMMARY.md` (lines 1-100)

**Detail**:

UUID: Inject from meta/uuid via config dict. Python RNG: random.getstate() → pickle → HDF5. Config JSON: Exclude non-serializable (activation_functions_dict, log_config, logger). History keys: Accept both val_* (old) and value_* (new) with fallback. Activation: Call _init_activation_function() after load. Backward compatibility maintained for old snapshots. Test recommendations provided (5 unit tests). Hidden units checksums in progress. Shape validation deferred. Multiprocessing state restoration incomplete. Optimizer state decision needed (recommend removal).

**Notes**:

[v2 remap: SE→API]

### JR-CAN-OPS-001 — Startup regression analysis and fixes: JuniperData lifecycle, env var expansion, namespace collision, config convention mismatches.

**Status**: shipped  **Priority**: P1  **Category**: OPS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/REGRESSION_ANALYSIS_STARTUP_FAILURE_2026-02-09.md` (lines 1-100)

**Detail**:

Root causes: RC-1 missing JuniperData service lifecycle management, RC-2 ${VAR:default} syntax unsupported by os.path.expandvars, RC-3 shell-to-Python environment namespace collision, RC-4 CASCOR_DEMO_MODE value convention mismatch. Fixes: script-level service management, custom config expansion, shell variable filtering, startup validation.

**PRs**: #146

### JR-ML-OBS-018 — **Strengths**: Near-real-time topology updates, no additional REST calls, leverages existing WebSocket infrastructure.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 251-301)

**Detail**:

#### Approach A: Add WebSocket-to-Store bridge via clientside callback (RECOMMENDED)

**Notes**:

[v3 brief repaired from cited content; was: 'Fix Approaches']

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

### JR-ML-SEC-050 — The Appendix G work (now merged) completed:.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 54-74)

**Detail**:

- **Cascor side (DONE)**: TrainingState fields populated via `_grow_iteration_callback` and

**Notes**:

[v3 brief repaired from cited content; was: '2.1 Current State (Post-Appendix G)']

### JR-ML-SEC-051 — Trigger / due date.** None — independent small sub-track. Useful at any time; pairs naturally with WS metric wire-ups already shipped via….

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 280-307)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** ✅ **CLOSED 2026-05-04 via juniper-cascor#218**

**Notes**:

[v3 brief repaired from cited content; was: '3.10 WORKER-PENDING-TASKS — `juniper_cascor_pending_tasks` w']

### JR-ML-TRAIN-011 — Use Pearson correlation (normalized) instead of raw covariance in candidate training.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 259-283)

**Detail**:

Raw covariance scales with residual magnitude; after first hidden unit, residuals shrink, candidate training gradients weaken (~8× decay observed). Pearson normalized by stddev, scale-invariant.

**Notes**:

Root cause RC-11; Phase 3 finding; doc status indicates implementation complete

### JR-CWK-SEC-002 — v0.2.0 security infrastructure: add .github/workflows/security-scan.yml for weekly scheduled Bandit and pip-audit scanning, Dependabot configuration, SOPS config, and SHA-pinned GitHub Actions.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 51-77)

**Detail**:

Added .github/workflows/security-scan.yml for weekly Bandit (static security) and pip-audit (dependency CVE scanning). Added SOPS configuration (.sops.yaml) and .env.example for secrets management. Updated .gitignore to cover all .env variants. SHA-pinned all GitHub Actions to immutable commit hashes. Added cross-repo CI dispatch to juniper-cascor on push to main. Added Dependabot configuration for weekly automated dependency updates. Added CODEOWNERS file for PR review routing.

### JR-CWK-SEC-003 — v0.3.0 CVE fix: bump setuptools minimum version to >=82.0 in pyproject.toml build-system requirements to remediate source distribution CVE.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 95-109)

**Detail**:

setuptools CVE affecting source distribution handling; bumped to >=82.0. Bandit pre-commit hook tuned to avoid false positives on known-safe test fixtures (B105: hardcoded_password_string suppressed for test auth_token fields). pip-audit dependency scanning runs in CI; torch +cpu local version handling fixed to enable reliable scanning of worker dependency tree.

### JR-CWK-DEP-001 — v0.3.0 deployment infrastructure: multi-stage Docker with CPU-only PyTorch, non-root user, reproducible uv pip compile lockfiles; systemd user service and management CLI.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 53-66)

**Detail**:

Docker: multi-stage Dockerfile, CPU-only PyTorch, non-root user, requirements.lock via `uv pip compile` for reproducible builds, .dockerignore. Systemd: scripts/juniper-cascor-worker.service user service unit, scripts/juniper-cascor-worker-ctl management CLI for host-level deployment.

### JR-CWK-WS-001 — v0.3.0 major rewrite: WebSocket-based CascorWorkerAgent replaces BaseManager-based CandidateTrainingWorker as default, with TLS/mTLS support and async event loop.

**Status**: shipped  **Priority**: P1  **Category**: WS  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 10-39)

**Detail**:

v0.3.0 (2026-04-08): WebSocket worker agent (new default) with long-lived WebSocket, work units pushed from cascor backend, binary tensor frames (struct-encoded shape/dtype/numpy data), worker capability reporting (CPU cores, GPU, versions on connect), heartbeat keepalive loop. New classes: CascorWorkerAgent (async event loop), WorkerConnection (WebSocket transport with TLS/mTLS and exponential backoff reconnection). New modules: ws_connection.py, task_executor.py (isolated training pipeline). New CLI flags: --tls-cert, --tls-key, --tls-ca for mTLS. Legacy mode (CandidateTrainingWorker) preserved behind --legacy flag with DeprecationWarning, will be removed in next major. Auth token rename: --api-key/CASCOR_API_KEY → --auth-token/CASCOR_AUTH_TOKEN (old names retained as deprecated fallbacks).

**Notes**:

[v2 ARCH→WS re-bucket] Backward-compatible at deployment level via --legacy. Operators may continue legacy mode during migration window. Default mode changed; no fallback default.

### JR-CWK-TOOL-001 — Worktree cleanup procedure with CWD continuity: create new worktree before removing old one to avoid trapping Claude Code sessions in invalid paths.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (lines 1-15)

**Detail**:

The V1 procedure (see notes/history/WORKTREE_CLEANUP_PROCEDURE_V1.md) removed the worktree directory without first creating a replacement, leaving the session trapped. V2 creates a new worktree and switches CWD before removing the old one (Phase 2 must complete before Phase 4). Phases: 1 Save & Push, 2 Create New Worktree (session continuity gate), 3 Merge & Pull Request, 4 Remove Old Worktree (prerequisite: new CWD verified), 5 Verify.

**Design**:

Phase 2 is the critical gate: CWD must move to the new worktree (Step 5) before the old one is removed (Phase 4, Step 9). The procedure enforces this with explicit verification gates in Step 6.

### JR-CAS-TRAIN-024 — 30+ critical issues identified and remediated; system transformed from non-functional to production-ready.

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/README_FIXES.md` (lines 1-100)

**Detail**:

P0 critical (10 fixed): type mismatches, field consistency, gradient descent, matrix operations, worker types. P1 high (5 fixed): serialization, counters, timeouts, early stopping, NumPy compatibility. Test validation: 10/10 passing (100%). Training efficiency: 73% reduction in candidate training time via early stopping. Multiprocessing: parallel functional with proper result collection. Robustness: graceful error handling, queue timeouts. NumPy 2.0 compatible. 100% test validation coverage.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-ML-SEC-106 — bound 2 user-supporting SLIs (§4.3, §4.4) to 2 of them. Result: ≥8 dashboard.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 176-226)

**Detail**:

**Scope**: Verify all metrics referenced in the R5.1 SLO catalog, `alert_rules.yml`,

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Dimension A — Metrics surface integrity']

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

### JR-CWK-DOC-003 — AGENTS.md missing supplementary content: directory layout, expanded key files, test details, CI/CD, pre-commit hooks, scripts, Python version requirements, and resource location guide.

**Status**: shipped  **Priority**: P2  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 80-160)

**Detail**:

Phase 3 supplementary content (medium priority): (3.1) Expand Key Files table (all Python modules, docs/, scripts/, .github/workflows/, config files). (3.2) Add directory layout tree. (3.3) Update dependencies (add websockets>=11.0). (3.4) Add CI/CD section (6-job pipeline, weekly security scan, PyPI publish, Dependabot). (3.5) Add pre-commit hooks (black, isort, flake8, mypy, bandit, shellcheck, yamllint, markdownlint, SOPS). (3.6) Add test details (6 test files, ~83 tests, fixtures, 80% coverage threshold). (3.7) Add Python version requirements (>=3.11, supported 3.11-3.14, PEP 561 py.typed). (3.8) Add docs/ section. (3.9) Add scripts/ section. Phase 4 cleanup: remove stale conf/ references, update ecosystem compatibility version. Phase 5 validation: run link checker, cross-reference CLI/env vars, test suite.

### JR-ML-SEC-107 — Background.** The post-METRICS-MON state report (juniper-ml#223 §15) found two clusters of stale panels in….

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 334-370)

**Detail**:

**Severity:** P1 (operational — dashboards mislead operators) · **Owner repo:** juniper-deploy · **Status:** in-flight (sister PR opened 2026-05-06)

**Notes**:

[v3 brief repaired from cited content; was: '3.12 DASHBOARD-STALE-PANELS — 7 stale Grafana panels post au']

### JR-ML-OBS-049 — Closing PRs that motivated this tracker (reference only).

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 423-433)

**Detail**:

- juniper-cascor#221 — Final E.6 audit follow-up: WorkerRegistry size cap + WS handshake rejection plumbing (MERGED 2026-05-05)

### JR-CAS-TRAIN-025 — Complete MVP with serialization state restoration: UUID persistence, RNG restoration, config roundtrip, history preservation, activation functions.

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/NEXT_STEPS.md` (lines 1-100)

**Detail**:

Completed: UUID persistence, Python/NumPy/PyTorch RNG state, config JSON serialization, history key alignment (value_loss/value_accuracy), activation function restoration. In-progress: hidden units checksums, shape validation, format validation, multiprocessing state restoration. Deferred: optimizer state decision (remove or fix), backward compatibility, schema versioning. 6 new integration tests covering deterministic training resume.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CAS-OBS-002 — Define Prometheus histogram buckets for latency metrics per observability requirements.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-50)

**Notes**:

See histogram_rationale file for bucket selection rationale.

### JR-ML-SEC-108 — emits per-worker gauges. `juniper-cascor-worker` itself does not.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 96-146)

**Detail**:

| `/metrics` URL | `http://juniper-cascor:8200/metrics` (compose) |

**Notes**:

[v3 brief repaired from cited content; was: '3.2 juniper-cascor']

### JR-ML-WS-135 — GAP-WS-19 close_all lock is RESOLVED on main.

**Status**: shipped  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 48-48)

**Notes**:

Settled position C-11 from R3-03 table; cross-round consensus consolidation

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

### JR-CAS-TRAIN-026 — Implement flexible optimizer system supporting Adam, SGD, RMSprop, AdamW.

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

OptimizerConfig dataclass and _create_optimizer() method already exist in codebase.

### JR-CAS-TRAIN-027 — Implement N-best candidate selection (candidates_per_layer configuration).

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

_select_best_candidates() and add_units_as_layer() methods already exist.

### JR-CAS-API-011 — Infrastructure & profiling suite: cProfile, memory profiling, py-spy, hot-path logging, micro-benchmarks, test harness.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 129-145)

**Detail**:

cProfile integration: ProfileContext, profile_function decorator (src/profiling/deterministic.py). Memory profiling: MemoryTracker, --profile-memory CLI flag (src/profiling/memory.py). py-spy: SVG flame graphs, Speedscope JSON (util/profile_training.bash). Hot-path logging: SampledLogger, BatchLogger, log_if_enabled, LogFrequencyTracker. Micro-benchmarks: forward pass, autograd, correlation, candidate training, output training, concurrency, shared memory, end-to-end. Benchmark harness: src/tests/scripts/run_benchmarks.bash + pytest-benchmark. All complete and verified.

**Notes**:

[v2 remap: SE→API]

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

### JR-CAS-API-012 — Network serialization architecture decisions: HDF5 format specification, version migration strategy, backward compatibility.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/NEXT_STEPS.md` (lines 200-250)

**Detail**:

HDF5 groups: meta, config, params, arch, random, hidden_units. Backward compatibility: old snapshots without Python random state load successfully (state not restored). Old snapshots with val_* keys load via fallback. Old corrupted config JSON falls back to attribute-based loading. No breaking changes. Schema versioning support planned (future). Compression optimization deferred. Incremental snapshots for large networks (future). Remote storage support (S3/Azure/GCS, future).

**Notes**:

[v2 remap: SE→API]

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

### JR-CCL-LOCK-002 — Propagate V2 worktree cleanup procedure (CWD-trap bug fix) to juniper-cascor-client.

**Status**: shipped  **Priority**: P2  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAN-UI-024 — Redefine pool training metrics around correlation statistics instead of loss/accuracy.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 396-440)

**Detail**:

CasCor trains on correlation, not loss/accuracy; these metrics do not exist for candidate pool. Replace with avg_correlation, max_correlation, min_correlation, std_correlation, success_rate.

**Notes**:

Phase 3 P2 fix; doc status COMPLETE; requires UI schema change

### JR-ML-API-030 — REST endpoints preserved FOREVER: /api/metrics/history, /api/train/*, /api/v1/training/params, /api/topology.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 60-60)

**Notes**:

Settled position C-23 from R3-03 table; cross-round consensus consolidation

### JR-CAS-TOOL-004 — Session status and validation: 18 integration tests, 11/12 MVP criteria met, ready for testing phase.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/SESSION_STATUS.md` (lines 1-150)

**Detail**:

Part 1 completed (analysis + critical fixes). Part 2 completed (validation + testing). Hidden units checksums (MD5, non-breaking), shape validation (cascade constraints), format validation (version compatibility). Test suite: 18 integration tests across 8 test classes. Metrics: 2 files modified (snapshot_serializer.py, AGENTS.md), 4 created, ~700 lines added, 2 functions. Coverage estimate 95% serialization paths, 100% validation. Status: 11/12 MVP criteria met (92%). Ready for MVP testing with test execution pending.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CCL-OPS-002 — Set line length to 512 for all linters (black, isort, flake8) per Juniper ecosystem standard.

**Status**: shipped  **Priority**: P2  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21); ecosystem standard convention

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

### JR-ML-UI-019 — **stale label** — bridge SHIPPED via juniper-cascor#188 (`heartbeat_age_seconds`) and gpu via the same collector; this placeholder panel pre.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 310-330)

**Detail**:

| Request Latency — p50 / p95 / p99 | timeseries | `histogram_quantile(...)` against the shared HTTP duration histogram | |

**Notes**:

[v4 brief repaired; was: '6.1 juniper-overview.json (14 panels, version 3, title "Juni']

### JR-ML-API-031 — `_STATE_TO_FSM` and `_STATE_TO_PHASE` class attributes are dead code. `get_training_status()` uses a local `status_map` dict instead.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 69-81)

**Detail**:

| ID       | Severity   | File:Line                         | Description

**Notes**:

[v4 brief repaired; was: '1.3 Code Quality']

### JR-CWK-TOOL-002 — Thread handoff procedure: preserve context fidelity when thread compaction degrades output by proactively handing off to fresh thread before context saturation.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/THREAD_HANDOFF_PROCEDURE.md` (lines 1-35)

**Detail**:

Thread compaction introduces information loss (subtle decisions, edge cases, partial progress, reasoning get dropped). Triggers: (1) context saturation after 15+ tool calls or 5+ file edits, (2) phase boundary completion, (3) degraded recall (re-reading files), (4) multi-module transitions, (5) user request. Do NOT handoff when task is nearly complete (<2 steps) or thread is still sharp. Handoff goal structure: original task, completed items, remaining work, key discoveries, file paths.

**Design**:

Handoff protocol: (1) Checkpoint current state (task, completed, remaining, discovered, files in play), (2) Compose concise actionable goal (be specific, include paths, state decisions, mention test status, keep <500 words), (3) Present to user via handoff() tool if available (follow=true for current thread stop, follow=false rare).

### JR-ML-SEC-109 — **TODO/FIXME/HACK**: 3 empty `# TODO :` banner placeholders in canopy frontend.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 331-370)

**Detail**:

**Scope**: Find hidden throttles beyond the known `cascade_correlation.py:1655`,

**Notes**:

[v3 brief repaired from cited content; was: '4.5 Dimension E — Throttles + tech debt + race conditions']

### JR-ML-SEC-110 — **Version**: 0.3.0 (unreleased constants refactor on main) | **Python**: ≥3.11 | **Coverage**: 91.47%.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 89-105)

**Detail**:

| CC-CI-01 | **Low**  | CI tests Python 3.11-3.13 but `pyproject.toml` classifies 3.14.                                                   |

**Notes**:

[v3 brief repaired from cited content; was: '1.5 CI/CD']

### JR-ML-OBS-052 — What needs to happen.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 676-699)

**Detail**:

1. **Pull p50 / p95 / p99 from Prometheus** for every SLI in catalog §3

### JR-CWK-TOOL-003 — Worktree setup procedure: standardized protocol for creating git worktrees when beginning a new task, centralizing worktrees in /home/pcalnon/Development/python/Juniper/worktrees/.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_SETUP_PROCEDURE.md` (lines 1-30)

**Detail**:

Prerequisites: must be in primary directory (not already in worktree), working tree clean, target branch not already checked out elsewhere. Protocol: (1) Ensure clean state, (2) Fetch and update parent branch (typically main), (3) Create working branch, (4) Compute worktree directory name using format <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>, (5) Create worktree, (6) Verify and begin work.

**Design**:

Naming convention: <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>. All worktrees in /home/pcalnon/Development/python/Juniper/worktrees/. Example: juniper-cascor-worker--feature--add-gpu-support--20260225-1430--047c3f61.

### JR-ML-DEP-045 — Background.** Carried forward from R1; never closed (deferred for burn-in). The healthcheck implementation shipped in worker image ≥ 0.4.0;….

**Status**: shipped  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 243-264)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.8 R1.3.4-FLAG — Helm chart `worker.healthcheck.enabled` de']

### JR-ML-SEC-212 — P3 — Hygiene / future / aspirational.

**Status**: shipped  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 391-412)

**Detail**:

| **3.1** | juniper-deploy | SLO catalog calibration vs soak-window data | Schedule T+30d agent for 2026-06-02; open calibration PR if observed data warrant

### JR-ML-OBS-143 — The design doc `juniper-cascor` PR #194 (`notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md`, merged 2026-05-03) captures two key….

**Status**: shipped  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 207-227)

**Detail**:

**Severity:** P3 (user-discretion) · **Owner repo:** juniper-cascor · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.6 TRAIN-ARCH-01 — Cascor mini-batch restoration']

### JR-CWK-SEC-004 — v0.3.0 deprecations: CandidateTrainingWorker (legacy), --api-key CLI flag, CASCOR_API_KEY env var; migrate to CascorWorkerAgent and --auth-token before next major release.

**Status**: shipped  **Priority**: P3  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 113-122)

**Detail**:

CandidateTrainingWorker (legacy): use --legacy to opt in; emits DeprecationWarning. --api-key CLI flag (old flag still parsed, deprecated). CASCOR_API_KEY env var (old var still read as fallback, deprecated). Plan migration to CascorWorkerAgent and --auth-token before next major release.

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-REC-TRAIN-001 — Δt-native LMU sequence regressor with ratified acceptance bands

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-DESIGN.md` (lines 97-109)
- `juniper-recurrence/bench/run_benchmark.py` (lines 137-149)

**Detail**:

The variable-Δt LMU must (band 1) cut RMSE ≥ 25% vs the fixed-Δt control on irregular-Δt data, (band 2) beat naive persistence and match/beat the linear ridge baseline on every primary dataset, and (band 3) tie fixed-Δt on regular grids. The pre-registered `PRIMARY_DATASETS` + `evaluate_bands` are the sole scoring authority (DP-5 guardrail).

### JR-REC-TRAIN-002 — Readout spectrum (linear / RFF / MLP) with a capacity instrument

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md` (lines 31-43)
- `juniper-recurrence/bench/datasets.py` (lines 15-27)

**Detail**:

Nonlinear readouts must demonstrate capacity the linear readout provably lacks on the bilinear `delay_product` target (measured gaps: RFF +0.83, MLP +0.87 r²) while merely tying linear on near-linear synthetics. A miss is a finding to record, never a threshold to tune.

### JR-REC-DATA-001 — 3-D irregular-Δt NPZ sequence contract consumption

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md` (lines 1-13)
- `juniper-data-client/juniper_data_client/contract.py` (lines 41-53)

**Detail**:

Consume `{X,y,dt,target_dt,observed_mask}_{train,test,full}` with `dt[:,0]==0`; equities sequences use the stationary `y_reg_*` log-return target (the r²≈−50 raw-price artifact class), never the one-hot direction label.

### JR-REC-API-001 — Service train/predict/crossval referencing content-addressed datasets

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 363-375)
- `juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/training.py` (lines 37-49)

**Detail**:

Synchronous `POST /v1/train` (response = completion); `predict`/`crossval` reference `dataset_id` only (never bare `name`); crossval reuses the train hyperparameters for bench comparability. Raw pydantic response bodies (no envelope) — a deliberate contrast with cascor's `{status,data,meta}`.

### JR-REC-TEST-001 — Bench harness with pre-registered scope as scoring authority

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-recurrence/bench/run_benchmark.py` (lines 137-149)
- `juniper-recurrence/bench/datasets.py` (lines 262-274)
- `juniper-recurrence/bench/test_bench_smoke.py` (lines 1-13)

**Detail**:

Primary bands scored only on the pre-registered set; extensions (noise sweep, `ar_p` linear floor, `delay_product` capacity, `equities_seq` real data) are informational. Committed `bench/results/` baselines are reproducible from seeds.

### JR-REC-TOOL-001 — Experiment YAML config layer (`service:` projection)

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 264-276)
- `juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py` (lines 60-72)

**Detail**:

`JUNIPER_RECURRENCE_CONFIG_FILE` activates a `service:`-block-only projection with precedence CLI/init > YAML > env > defaults; forbidden infra keys (`host`/`port`/`juniper_data_url`) fail loud; deliberately **no** `.env` tier (env-file-leak doctrine).

### JR-REC-TOOL-002 — Direct-CLI `train:` block seeding (W-11)

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: rec

**Sources**:
- `juniper-recurrence/juniper-recurrence/juniper_recurrence/main.py` (lines 96-108)

**Detail**:

The `train` subcommand seeds unset argparse flags from the experiment YAML's `train:` block; explicit CLI flags win; unmodeled keys warn and are never silently applied.

### JR-REC-TEST-003 — Concurrent bench runs (per-run results dir)

**Status**: shipped  **Priority**: P2  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-recurrence/bench/run_benchmark.py` (lines 4-16)

**Detail**:

`python -m bench.run_benchmark --results-dir DIR` routes per-dataset JSON + REPORT.md; the default stays the committed `bench/results/` byte-identically.

### JR-REC-OBS-001 — Experiment-lane observability toggles

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 444-456)
- `juniper-ml/util/experiment_stack.bash` (lines 7-19)

**Detail**:

Metrics exposition on + rate-limit off for per-run scrape lanes; targets labeled `service`/`environment=host-experiment`/`run_id`/`experiment` via the launcher's file_sd bridge.
