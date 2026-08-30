# Requirements — juniper-cascor (cas)

**Total entries**: 122

**By status**: proposed=74 | designed=3 | shipped=41 | deferred=4

**By priority**: P0=21 | P1=38 | P2=49 | P3=14

**By category**: TRAIN=35 | TEST=19 | ARCH=19 | API=14 | TOOL=10 | PERF=6 | WS=6 | OBS=5 | DOC=4 | LOCK=3 | DEP=1

---

### JR-CAS-LOCK-001 — Add missing PyYAML, h5py, pytest-cov, psutil dependencies to conda environment.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 256-306)

### JR-CAS-DOC-001 — Document that CascadeCorrelationNetwork is not thread-safe.

**Status**: shipped  **Priority**: P0  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 183-198)

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

### JR-CAS-TRAIN-005 — Fix logger pickling error in multiprocessing (BUG-002).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 28-36)

**Detail**:

Enhance CascadeCorrelationNetwork and CascadeCorrelationPlotter __getstate__/__setstate__ methods for pickle support; verify CandidateUnit has pickling support.

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

### JR-CAS-TEST-001 — Increase serialization test coverage to ≥80% for snapshot_serializer.py.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 102-147)

### JR-CAS-TRAIN-010 — Cascor must implement mini-batch training for the output-layer trainer to support larger datasets and reduced memory footprint.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md` (lines 19-54)

**Detail**:

Currently cascor trainers are full-batch end-to-end. Proposed restoration adds config knobs:
- `use_mini_batch` (default True)
- `mini_batch_size` (sane default TBD)
Candidate-unit trainer intentionally NOT mini-batched (Pearson correlation needs full-batch stats).
Estimated 3-4 PRs, Tier-2 effort.

### JR-CAS-ARCH-001 — Extract duplicated ActivationWithDerivative class to shared module to prevent divergence in ACTIVATION_MAP.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 144-157)

**Detail**:

Class defined identically in cascade_correlation.py:291 and candidate_unit.py:138.
If ACTIVATION_MAP diverges between copies, deserialized objects behave differently.
Fix: extract to shared module (e.g., src/utils/activation.py) and import from both.
Codebase validation CONFIRMED duplicate at lines 291 and 138.

### JR-CAS-TOOL-001 — Fix ./try convenience script path resolution errors in helper scripts.

**Status**: proposed  **Priority**: P0  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 201-252)

**Detail**:

Helper scripts (GET_OS_SCRIPT, GET_PROJECT_SCRIPT, DATE_FUNCTIONS_SCRIPT) are overridden as bare filenames. Fix to use absolute paths derived from BASH_SOURCE[0]. Update conf/script_util.cfg to correctly compute ROOT_PROJECT_DIR with proper project hierarchy.

### JR-CAS-ARCH-002 — Fix invalid CandidateUnit constructor parameters in fit() method - all parameters silently absorbed by kwargs.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-24.md` (lines 100-110)

**Detail**:

Lines 1154-1166: fit() passes 11 parameters with `_CandidateUnit__` prefix (wrong mangling
style) instead of `CandidateUnit__`. All absorbed by **kwargs. CandidateUnit created with
ALL default values, ignoring user's activation function, input size, output size, learning
rate, etc. WORSE than documented - affects all training in fit() path.

### JR-CAS-ARCH-003 — Fix walrus operator precedence bug in train_output_layer() that assigns boolean instead of snapshot path.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 128-141)

**Detail**:

Line 1322: `if snapshot_path := self.create_snapshot() is not None:` is parsed as
`snapshot_path := (self.create_snapshot() is not None)`. snapshot_path always assigned
True/False, not actual path. Log message prints 'True'. Fix: add parentheses
`if (snapshot_path := self.create_snapshot()) is not None:`.
Codebase validation (2026-02-18) CONFIRMED.

### JR-CAS-PERF-001 — Optimize tensor serialization overhead in parallel candidate training via shared memory blocks.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/OPT5_SHARED_MEMORY_PLAN.md` (lines 1-32)

**Detail**:

OPT-5 eliminates redundant tensor serialization by sharing training tensors via
named POSIX shared memory. Currently each of N candidates sends same tensors through
queue. ForkingPickler already sends handles (~340 bytes) but GET-side reconstruction
costs ~320us (same-process) to ~9ms (cross-process). For 16 candidates, ~100-145ms
overhead per round. Using multiprocessing.shared_memory.SharedMemory creates named
block, workers attach by name. Expected improvement: 5-20% total round time reduction.

### JR-CAS-TRAIN-011 — Remove hardcoded absolute path from remote_client_0.py that points to obsolete prototype directory.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 176-189)

**Detail**:

Line 16: sys.path.append("/home/pcalnon/Development/python/Juniper/src/prototypes/cascor/src")
Points to old prototype location. Will fail on any other machine. Also note INT-P2-009:
inconsistent queue names between remote_client.py and remote_client_0.py.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-ARCH-004 — Remove hardcoded absolute paths in test file for cross-platform portability.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 192-205)

**Detail**:

src/tests/unit/test_candidate_training_manager.py lines 10,12 contain hardcoded paths
to prototype directories (Linux and macOS). Will cause import failures and raise
EnvironmentError on Windows. Fix: replace with dynamic path resolution using
os.path.dirname(__file__).

### JR-CAS-TRAIN-012 — 18 verified bug fixes across architecture, training logic, serialization, runtime; 15 critical/high items addressed.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 60-90)

**Detail**:

INT-P0 items: walrus operator precedence, ActivationWithDerivative duplication, CandidateUnit constructor params (name-mangled), datetime alias misleading, global declaration, validation logic. INT-P2 items: conftest fast-slow inversion, roll_sequence memory, os._exit usage, traceback imports. INT-P1 items: requests undeclared dependency, JuniperData retry logic, dill dependency. BUG-001/002: random state restoration, logger pickling multiprocessing. Convergence threshold fix. Leaf tensor autograd RuntimeError. Module naming collision (constants→cascor_constants). Polyrepo Phase 1 duplicate elimination. All 18 fixed with codebase validation.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CAS-OBS-001 — Add thread safety locks to monitoring loop metrics extraction (CascorIntegration._extract_current_metrics).

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 715-743)

### JR-CAS-TRAIN-013 — All Phase 1 enhancements from CASCOR_ENHANCEMENTS_ROADMAP implemented and tested.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PHASE1_COMPLETE.md` (lines 9-17)

**Detail**:

Status complete 2025-10-28. BUG-001 (test random state restoration), BUG-002 (logger
pickling error) fixed. ENH-001 through ENH-008 implemented. MVP code-complete and
ready for testing phase. Zero breaking changes. All P0 and P1 work done.

### JR-CAS-API-002 — Build FastAPI service layer for CasCor with REST endpoints and WebSocket streaming.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 728-735)

**Detail**:

Add 19 REST endpoints across 6 route files; WebSocket endpoints for real-time training streaming (/ws/training, /ws/control); TrainingLifecycleManager with thread-safe state machine and ThreadPoolExecutor; service entry point (server.py) alongside existing CLI (main.py).

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

### JR-CAS-TOOL-002 — Complete CI/CD infrastructure: pre-commit 21 hooks, coverage 80%, GitHub Actions matrix (3.11/3.12/3.13), security scanning.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/pull_requests/PR_full_branch_spiral_gen_extract_pre_deploy.md` (lines 1-100)

**Detail**:

91% test coverage achieved (from ~15%), 1333+ tests. CI pipeline: GitHub Actions matrix (3.11/3.12/3.13), scheduled nightly tests, pre-commit hooks (21 total), coverage enforcement (80%), security scanning (Bandit, Gitleaks, pip-audit). 28 version increments (0.0.1 → 0.7.0). Critical fixes: multiprocessing completion logic, undefined queue_timeout, test timeouts, snapshot serializer TypeError, candidate training result parsing, task parameter wiring, best_candidate_id selection, NaN input handling.

**Notes**:

[v2 remap: CL→TOOL]

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

### JR-CAS-TRAIN-016 — Decouple Canopy from CasCor via service client; remove direct imports and sys.path manipulation.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1208-1220)

**Detail**:

Implement CascorServiceAdapter for two-mode activation (demo/service); remove legacy CascorIntegration (~1,601 lines); remove sys.path manipulation; update configuration to use CASCOR_SERVICE_URL (port 8200).

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-TRAIN-017 — Expand format validation for HDF5 snapshot files.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 73-83)

**Detail**:

Check format name/version; validate required groups and datasets; verify hidden units consistency.

### JR-CAS-TRAIN-018 — Implement hidden units checksums for integrity verification.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 53-61)

### JR-CAS-TRAIN-019 — Implement shape validation for serialized network structure.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 63-71)

**Detail**:

Implement _validate_shapes() method; validate output layer and hidden units; call from load_network().

### JR-CAS-TEST-004 — Migrate scheduled-tests.yml from conda to pip; complete Phase 1 CI pipeline enhancement.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/CI_PIPELINE_DEVELOPMENT_PLAN.md` (lines 1-100)

**Detail**:

Phase 1 complete (2026-02-22): conda environments → pip requirements. Phases 2-3: remove pytest-asyncio duplicates, expand MyPy coverage to api/, cascor_constants/, remote_client/ modules. Gap analysis identified 5 issues: scheduled-tests conda, pre-commit version mismatch, MyPy pattern expansion, conftest CLI flag audit.

**Notes**:

[v2 remap: CI→TEST]

### JR-CAS-TRAIN-020 — Performance optimizations: thread pinning (5-15x), direct queues (3-10x), shared training data, persistent workers (20-50%), cached forward pass (22-1607x isolated).

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 90-120)

**Detail**:

RC-1: torch.set_num_threads(1) + BLAS env vars → 5-15x improvement. RC-2: Direct mp.Queue vs BaseManager → 3-10x additional. RC-3: Shared training data reduces N-fold serialization. RC-4: Persistent worker pool 20-50% latency reduction. OPT-1: Pre-allocated forward buffer eliminates N+1 torch.cat. OPT-2: Batch correlation (torch.dot + linalg.norm) → 5-10%. OPT-4: Cached forward pass 22-1607x isolated, 5-15% total. OPT-5: SharedMemory training tensors 5-20% reduction. OPT-6: Single-output correlation fix 37x speedup (18.24ms → 0.49ms). Forward pass sub-linear (0→50 units = 1.86x). Convergence threshold in patience.

**Notes**:

[v2 remap: BG→TRAIN]

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

### JR-CAS-TOOL-003 — Hardcoded values extraction into constants module; 56 hardcoded values across API layer, lifecycle manager, observability require extraction.

**Status**: designed  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/HARDCODED_VALUES_ANALYSIS.md` (lines 1-100)

**Detail**:

New module cascor_constants/constants_api/constants_api_defaults.py with 43 constants. Target location: cascor_constants/ hierarchy extended. Approach A recommended: extend existing cascor_constants/ pattern (vs. Approach B: centralize in settings.py, Approach C: hybrid). Files requiring modification: 16 (models, lifecycle, observability, routes, service_launcher, middleware, app, workers, candidate_unit, spiral_problem, snapshots, profiling).

**Notes**:

[v2 remap: CL→TOOL]

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

### JR-CAS-ARCH-005 — Add connection retry logic with exponential backoff for JuniperData REST client.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 313-326)

**Detail**:

Client has no retry logic, connection pooling, or circuit breaker. Transient network
error crashes entire pipeline. Fix: add retry with exponential backoff (urllib3.Retry
or tenacity).

### JR-CAS-API-006 — Add requests as declared dependency in pyproject.toml - currently undeclared but used by JuniperDataClient.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 229-242)

**Detail**:

JuniperDataClient imports requests but not listed in pyproject.toml or documented
in CLAUDE.md. Will fail on fresh installs. Add to dependencies and document.

### JR-CAS-ARCH-006 — Add try/except guard around SpiralDataProvider import for graceful degradation when requests unavailable.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 297-310)

**Detail**:

Line 505: lazy import transitively imports requests. If requests not installed,
fails with ModuleNotFoundError even when JUNIPER_DATA_URL set. Add try/except
with clear error message.

### JR-CAS-API-007 — API defaults extraction and normalization: 49 constants for API layer (network models, lifecycle, observability, security, endpoints).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/HARDCODED_VALUES_ANALYSIS.md` (lines 200-300)

**Detail**:

New cascor_constants/constants_api/ submodule with constants_api_defaults.py (43 constants). Network defaults: input_size=2, output_size=2, learning_rate=0.01, candidate_learning_rate=0.005, max_hidden_units=10, candidate_pool_size=8, correlation_threshold=0.1, patience=5, candidate_epochs=50, output_epochs=25, epochs_max=200, max_iterations=1000, init_output_weights='zero'. Lifecycle: 8 manager defaults. Observability: 4 logging/Sentry config. Service launcher: 3 timeouts. Middleware/routes: HTTP codes, resolution bounds. App URLs: JuniperData, Canopy, health checks. Validation tests required to prevent constants/settings drift.

**Notes**:

[v2 remap: SE→API]

### JR-CAS-API-008 — CasCor backend must expose prediction method accepting arbitrary input grids for visualization.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 687-691)

**Notes**:

Required for JuniperCanopy decision boundary visualization.

### JR-CAS-API-009 — CasCor service must expose REST endpoints for snapshot save/load with full training state.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 701-705)

**Detail**:

REST endpoints must capture network weights, optimizer state, and training metadata via PyTorch state_dict() or equivalent.

### JR-CAS-TRAIN-022 — Consolidate duplicated JuniperDataClient in Cascor and Canopy into shared package.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 214-226)

**Detail**:

Cascor and Canopy maintain separate copies. Canopy has get_preview() method not in
Cascor. Changes to one not reflected in other. Fix: consolidate into juniper_data_client
shared package installable by both applications.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-API-010 — Create shared protocol/interface package for data contracts between applications.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 245-257)

**Detail**:

No shared Python package defining data contracts (Pydantic models, type aliases).
Each app independently defines expectations. NPZ array keys (X_train, y_train, etc.)
documented but not enforced. Fix: create juniper_contracts package defining API schemas.

### JR-CAS-DOC-002 — Document forkserver context workaround and multiprocessing queue-based task distribution.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/setup_config_guides/forkserver_fix.md` (lines 1-20)

**Detail**:

Forkserver debugging and configuration guide. Documents BaseManager configuration
with forkserver context, queue-based task distribution patterns.

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

### JR-CAS-TRAIN-023 — Fix epoch/iteration semantic error in grow_network() and ValidateTrainingInputs dataclass; rename for correctness.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/analysis/REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-180)

**Detail**:

Each grow_network() loop iteration performs complete Cascade Correlation growth cycle (candidate training, selection, installation), not single epoch. Rename max_epochs→max_iterations, epoch→iteration, epochs_completed→iterations_completed, log "Iteration" not "Epoch". Update ValidateTrainingInputs fields. Callers: fit() line 1445, unit tests. No breaking API changes. Backward-compatible alias pattern available (lines 1375-1379). Estimated 2-4 hours effort. Non-functional behavior change.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CAS-ARCH-007 — Fix main.py passing invalid parameters to SpiralProblem constructor.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 281-295)

**Detail**:

Lines 208-210: passes _SpiralProblem__spiral_config=logging.config (the logging module,
not config object), _SpiralProblem__dataset_tensors=None, _SpiralProblem__dataset_file_info=None.
Silently absorbed by **kwargs. Fix: remove invalid parameters or implement SpiralConfig.

### JR-CAS-ARCH-008 — Remove or archive stale duplicate check.py file (outdated copy of spiral_problem.py).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 329-342)

**Detail**:

src/spiral_problem/check.py contains complete but outdated copy of SpiralProblem class
using old-style constructor parameters. Dead code creating confusion. Remove or archive.

### JR-CAS-TEST-007 — Set and enforce minimum coverage thresholds: 70% overall, 80% for core snapshots module.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 632-647)

### JR-CAS-TEST-008 — Test suite optimization: force sequential training, remove coverage from defaults, fix test collection, optimize fixtures.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_PERFORMANCE_IMPROVEMENT_PLAN.md` (lines 1-250)

**Detail**:

Phase 1 (critical): Force sequential training via conftest autouse fixture patching _calculate_optimal_process_count to return 1. Phase 2: Remove coverage from pytest.ini addopts (2-3x speedup). Phase 3: Fix test_hdf5.py import path. Phase 4: Create lightweight network_with_hidden_units fixture. Phase 5: Harden worker shutdown (bounded total timeout, CASCOR_NUM_PROCESSES env var). Phase 6 (applied): Patch Logger._log_at_level to no-op, torch warmup fixture, mock fit() in tests, reduce epochs. Results: 500+s → 12-24s (86-93% reduction), 1408 passed, 15 skipped.

**Notes**:

[v2 remap: TI→TEST]

### JR-CAS-TRAIN-024 — 30+ critical issues identified and remediated; system transformed from non-functional to production-ready.

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/README_FIXES.md` (lines 1-100)

**Detail**:

P0 critical (10 fixed): type mismatches, field consistency, gradient descent, matrix operations, worker types. P1 high (5 fixed): serialization, counters, timeouts, early stopping, NumPy compatibility. Test validation: 10/10 passing (100%). Training efficiency: 73% reduction in candidate training time via early stopping. Multiprocessing: parallel functional with proper result collection. Robustness: graceful error handling, queue timeouts. NumPy 2.0 compatible. 100% test validation coverage.

**Notes**:

[v2 remap: BG→TRAIN]

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

### JR-CAS-API-012 — Network serialization architecture decisions: HDF5 format specification, version migration strategy, backward compatibility.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/NEXT_STEPS.md` (lines 200-250)

**Detail**:

HDF5 groups: meta, config, params, arch, random, hidden_units. Backward compatibility: old snapshots without Python random state load successfully (state not restored). Old snapshots with val_* keys load via fallback. Old corrupted config JSON falls back to attribute-based loading. No breaking changes. Schema versioning support planned (future). Compression optimization deferred. Incremental snapshots for large networks (future). Remote storage support (S3/Azure/GCS, future).

**Notes**:

[v2 remap: SE→API]

### JR-CAS-TOOL-004 — Session status and validation: 18 integration tests, 11/12 MVP criteria met, ready for testing phase.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/SESSION_STATUS.md` (lines 1-150)

**Detail**:

Part 1 completed (analysis + critical fixes). Part 2 completed (validation + testing). Hidden units checksums (MD5, non-breaking), shape validation (cascade constraints), format validation (version compatibility). Test suite: 18 integration tests across 8 test classes. Metrics: 2 files modified (snapshot_serializer.py, AGENTS.md), 4 created, ~700 lines added, 2 functions. Coverage estimate 95% serialization paths, 100% validation. Status: 11/12 MVP criteria met (92%). Ready for MVP testing with test execution pending.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAS-WS-003 — Thread handoff procedure replaces default compaction; preserves context at 95-99% utilization threshold.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/THREAD_HANDOFF_IMPLEMENTATION.md` (lines 1-100)

**Detail**:

Two-layer implementation: global ~/.claude/CLAUDE.md + project CLAUDE.md. Trigger: 95-99% context utilization (within 1-5% of compaction threshold). Additional triggers: 15+ tool calls, phase boundary, degraded recall, module transition, user request. 5-step execution protocol: checkpoint, compose goal, present, verify, git status. Exclusions: nearly complete task, sharp thread, tightly coupled work.

### JR-CAS-TEST-009 — Defer test optimization: reduce 45-minute test suite to ≤5 minutes.

**Status**: deferred  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 37-39)

**Detail**:

Test suite runs in 45+ minutes; target ≤5 minutes. This is a deferred medium-priority optimization (MED-014) per document status.

**Notes**:

Deferred optimization; developer productivity; noted in doc status

### JR-CAS-TOOL-005 — 10 open/remaining work items: hardcoded paths, stale files, fallback bugs, version inconsistencies, legacy directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 160-180)

**Detail**:

INT-P0-004: remote_client_0.py hardcoded path to monorepo (delete, superseded by juniper-cascor-worker). INT-P0-005: Hardcoded test paths (sys.path.append lines). INT-P1-008: check.py stale duplicate. INT-P2-005/006: or fallback bugs (clockwise, numeric params) → if x is not None pattern. INT-P2-014: Local traceback imports (use top-level, remove 9 instances). INT-P3-009: Version strings inconsistent (main.py 0.3.1, cascade_correlation.py 0.3.2, pyproject.toml 0.4.0). Legacy remote_client/ directory (remove or archive). Estimated effort 2-4 hours total.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAS-TEST-010 — Add coverage report --fail-under gate and per-module thresholds to CI.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 501-511)

**Detail**:

CI/CD coverage gates not enforced. Add `coverage report --fail-under=80` to CI,
configure per-module thresholds, add coverage badge to README.

### JR-CAS-PERF-002 — Add GPU/CUDA support for all tensor operations and training.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 885-912)

### JR-CAS-TOOL-006 — Address 7 codebase analysis issues: logging system gaps, startup robustness, constants over-engineering, security risks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/CODEBASE_ANALYSIS_2026-03-12.md` (lines 1-100)

**Detail**:

Logging: YAML relative paths, three independent mechanisms, CWD-dependent resolution. Startup: os._exit() usage, module-level Sentry init, lru_cache on get_settings(). Architecture: dual logging systems (CLI vs API), constants over-engineering (7 sub-packages), name-mangled constructor params, sys.path manipulation, deprecated docker-compose. Code quality: exception handling breadth, global state, LogConfig Java-style getters/setters, commented-out code, walrus operator misuse. Security: CORS wildcard risk, Sentry PII collection, nosec without ticket.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAS-WS-004 — AGENTS.md documentation drift: 7-phase plan to align with service architecture, security, observability, CI/CD.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 1-150)

**Detail**:

Phase 1: Update version 0.3.17 → 0.4.0, restructure to lead with service architecture. Phase 2: Add server commands, environment variables, key entry points (server.py, api/app.py). Phase 3: Document REST API (endpoint inventory, auth), WebSocket protocol (3 channels), lifecycle management, remote workers, middleware. Phase 4: Security (API keys, rate limiting, headers, TLS), observability (JSON logging, Prometheus, Sentry). Phase 5: CI/CD workflows, deployment (Docker, Kubernetes), configuration. Phase 6: Update existing sections (directory structure, dependencies, testing). Phase 7: New sections (service launcher, MCP). Validation criteria listed.

### JR-CAS-ARCH-009 — Align inconsistent queue method names between remote_client.py and remote_client_0.py implementations.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 471-483)

**Detail**:

Two implementations register different queue names: get_task_queue/get_result_queue vs
get_tasks_queue/get_done_queue. Old client fails to connect to current manager.
Remove remote_client_0.py or align queue names.

### JR-CAS-TEST-011 — Always-passing tests with assert True must be replaced with real test logic.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 57-62)

**Detail**:

TST-001: tests in test_training_workflow.py:186-204 always pass. Real test logic
required to validate behavior.

### JR-CAS-TEST-012 — Backward compatibility testing with old serialized snapshots.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

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

### JR-CAS-TOOL-007 — Code quality & compliance improvements: coverage thresholds, strict MyPy, pre-commit hooks, lint compliance tests.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 118-130)

**Detail**:

Pre-commit compliance: All 20 hooks pass, 9 violations fixed (F401×2, F402, C401, B007, B404, B105/B110/B107). Lint compliance tests: 162 parametrized tests (test_lint_compliance.py for future detection). Coverage threshold: fail_under = 80 in pyproject.toml. CI pipeline green (pre-commit, unit tests 3.11/3.12/3.13, security, integration, build). CPU-only PyTorch in CI configured. No critical lint violations remaining.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAS-WS-005 — Complete documentation for spiral data generator extraction, PyPI client packages, microservices implementation, and polyrepo architecture.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/JUNIPER_CASCOR_SPIRAL_DATA_GEN_REFACTOR_PLAN.md` (lines 1-100)

**Detail**:

Comprehensive extraction plan synthesizing 3 proposals, phases 0-4 complete (76 tests passing), phase 5 deferred. Core principles: pure NumPy generator, artifact-first API (NPZ), minimal provider set, deterministic reproducibility. Methods to extract: coordinate generation, feature/label construction, ordering/partitioning. Dependency decoupling: remove torch, matplotlib, logging, multiprocessing. Constants extraction: spiral geometry (num_spirals, points_per_spiral, rotations), noise parameters. NPZ data contract specification (dataset_id hash-based, structure validation). Documentation complete with test coverage and phase-by-phase delivery schedule.

### JR-CAS-OBS-003 — Create baseline py-spy profiles for key operations to enable performance regression detection.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 850-854)

### JR-CAS-OBS-004 — Define performance targets for latency and throughput.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

Benchmark harness needed to measure actual performance against targets.

### JR-CAS-TOOL-008 — Design decisions record: 10 items tracking ActivationWithDerivative location, CandidateUnit factory, or fallback pattern, client packages, async wrapper, large file refactoring, legacy code removal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 325-342)

**Detail**:

Decision 1 (✅ IMPLEMENTED): ActivationWithDerivative → src/utils/activation.py. Decision 2 (✅ IMPLEMENTED): CandidateUnit constructor fix (factory + remove kwargs). Decision 3 (DECIDED): or fallback → if x is not None. Decision 4 (✅ IMPLEMENTED): Client packages (PyPI). Decision 5 (✅ IMPLEMENTED): Async wrapper (ThreadPoolExecutor). Decision 6 (DECIDED, not started): Large file refactoring (mixin-based). Decision 7 (DECIDED, gated): Legacy code removal (after E2E gate). Decision 8 (DECIDED): Optimizer serialization removal. Decision 9 (🔵 DEFERRED): Multiprocessing state (partial restore). Decision 10 (✅ IMPLEMENTED): SharedMemory (Named with lightweight tasks).

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAS-ARCH-010 — Fix boolean parameter initialization using "or" fallback in spiral_problem.py.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 426-438)

**Detail**:

Line 671: `self.clockwise = clockwise or self.clockwise or _SPIRAL_PROBLEM_CLOCKWISE`
never becomes False. Line 695: `noise or 0.0` fallback incorrect when 0.0 is valid.
Use explicit None checks.

### JR-CAS-TEST-013 — Fix conftest.py fast-slow mode logic - inverted semantics for JUNIPER_FAST_SLOW env var.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 441-453)

**Detail**:

Line 83: `os.environ.get("JUNIPER_FAST_SLOW") == "0"` triggers fast-slow mode when
env var is "0", semantically opposite. test_spiral_problem.py:_is_fast_mode() checks == "1".
Align condition to use consistent semantics.

### JR-CAS-DOC-003 — Fix import alias mistake: datetime import uses pd instead of dt.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 362-366)

**Detail**:

Line 38 of cascade_correlation.py: 'import datetime as pd' should be 'import datetime as dt'. pd is conventionally pandas; using for datetime misleads developers.

### JR-CAS-ARCH-011 — Fix misleading import alias "import datetime as pd" - confuses with pandas.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 366-378)

**Detail**:

Line 38: imports datetime as pd (universally associated with pandas). Alias never used.
Line 37 already has import datetime. Remove the confusing import.

### JR-CAS-PERF-003 — Fix _roll_sequence_number memory issue in CascadeCorrelationNetwork using same optimization as CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 456-468)

**Detail**:

Line 775: list comprehension stores all discarded values. Unlike CandidateUnit version
(fixed in CASCOR-P1-008), this version still has OOM risk. Apply same fix: simple
for-loop with MAX_ROLL_COUNT cap.

### JR-CAS-TRAIN-028 — Fix validate_training_results bug - uninitialized variables in edge cases.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 381-393)

**Detail**:

Line 2750: TODO marked. Variable initialized to None, only set inside for loop. If
max_epochs=0, post-loop check references unbound epoch variable. Fix: initialize epoch
and validate_training_results before loop.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-TRAIN-029 — Fix validate_training_results None initialization bug in training loop.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 374-378)

**Detail**:

Variable initialized as None; if training loop doesn't execute (e.g. max_epochs=0), debug log crashes with AttributeError on .early_stop.

### JR-CAS-TEST-014 — Increase code coverage from ~15-78% baseline to 90% target via additional unit tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 543-589)

### JR-CAS-TRAIN-030 — Integration fixes: 9 JuniperData items (API path, deprecation warnings, auth, NPZ validation, contract tests, retry/backoff).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 138-145)

**Detail**:

CAS-INT-001 through CAS-INT-009 verified complete. Items include: API path validation, deprecation warning handling, authentication token management, NPZ format validation, data contract tests, max_retries=3 retry logic with backoff, status code normalization, error classification. All integrated with current JuniperData REST API. Async training boundary via ThreadPoolExecutor. RemoteWorkerClient integration via REST endpoints. Test suite CI/CD phases 0-4 complete (MED-014 line length deferred).

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CAS-LOCK-002 — Move dill to test-only dependencies or add proper import guard - currently undeclared runtime dep.

**Status**: proposed  **Priority**: P2  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 532-544)

**Detail**:

check_object_pickleability in src/utils/utils.py:248 imports dill (not in dependencies).
Will crash with ModuleNotFoundError if called. Move to test dependencies or add guard.

### JR-CAS-DOC-004 — Move top-level import traceback statements - currently repeated in exception handlers.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 547-559)

**Detail**:

Multiple locations in cascade_correlation.py have import traceback inside except
blocks. Move to file-level imports.

### JR-CAS-TOOL-009 — Not-started items: coverage gates per-module, MyPy strict mode, Spider legacy code removal, Docker end-to-end validation.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 183-198)

**Detail**:

CAS-REF-002: Coverage gates (per-module thresholds, P2, S effort). CAS-REF-003: Critical type errors MyPy strict (P2, M effort). CAS-007: Slow tests optimization (P2, M effort, 86-93% achieved Phase 6). CAS-REF-004: Legacy spiral code (16 deprecated methods, P2, M effort). INT-P3-003: Docker Compose E2E validation (P3, S effort). INT-P3-008: pytest.ini.swp and coverage files in gitignore (P3, S effort). INT-P3-010: cascor_snapshots vs snapshots directory confusion (P3, S effort). Shell scripts: 6 Oracle analysis items (P3, M effort). All 🔴 NOT STARTED or 🔵 DEFERRED.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAS-TEST-015 — Re-enable skipped critical deterministic training resume test.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 57-62)

**Detail**:

TST-004: test_comprehensive_serialization.py:41-42 has critical deterministic test
marked as skip. Remove skip decorator and enable test.

### JR-CAS-ARCH-012 — Remove direct absolute path hardcoding that breaks on non-development machines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 142-146)

**Notes**:

Use relative paths or environment-relative configuration.

### JR-CAS-ARCH-013 — Remove duplicate snapshot_counter initialization in _init_network_parameters.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 396-408)

**Detail**:

Lines 530 and 548: self.snapshot_counter = 0 appears twice. Second is redundant.

### JR-CAS-ARCH-014 — Remove undeclared global variable shared_object_dict from _train_candidate_unit.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 351-363)

**Detail**:

Line 2300: global shared_object_dict declared but never defined anywhere. Accessing
raises NameError. Remnant from earlier design. Remove global declaration and related
dead code.

### JR-CAS-ARCH-015 — Replace "or" fallback chains with explicit None checks for falsy parameter values.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 411-423)

**Detail**:

Patterns like `learning_rate or _CONSTANT` fall through when config value is 0 or 0.0
(falsy). Incorrect for parameters where 0 is valid. Fix: use explicit
`if self.config.learning_rate is not None:` checks.

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

### JR-CAS-ARCH-016 — Replace os._exit() with sys.exit() in main.py for proper cleanup handling.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 486-498)

**Detail**:

Lines 142,145: os._exit(1) bypasses cleanup handlers, finally blocks, atexit functions.
sys.exit() should be preferred.

### JR-CAS-ARCH-017 — Replace Path truthiness checks with explicit None checks.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 394-398)

**Detail**:

Path objects are always truthy even for empty strings. Use 'if x is None' instead of 'or' fallback patterns (lines 3015, 3096, 471).

### JR-CAS-ARCH-018 — Run mypy and categorize type errors, then gradually increase strictness.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 514-529)

**Detail**:

Type errors present. Sub-tasks: run mypy, categorize errors, fix critical errors,
gradually increase strictness, remove continue-on-error from CI.

### JR-CAS-TRAIN-031 — Support multiple optimizer types via configuration (Adam, SGD, RMSprop, AdamW).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 749-773)

### JR-CAS-OBS-005 — Verify WebSocket responsiveness under load when training runs via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 870-874)

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

### JR-CAS-PERF-004 — Create baseline performance profiles using py-spy for regression detection.

**Status**: deferred  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 635-645)

**Detail**:

Baseline py-spy profiles for key operations enable performance regression detection.

### JR-CAS-ARCH-019 — Remove legacy spiral generator code once JuniperData is stable and proven.

**Status**: deferred  **Priority**: P3  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 568-578)

**Detail**:

Dual-path (legacy + JuniperData) creates maintenance burden. Once JuniperData stable,
remove legacy spiral generator from spiral_problem.py.

### JR-CAS-TRAIN-033 — CasCor juniper-cascor bug: TrainingMonitor.current_phase never updated during training (ISS-08).

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 468-493)

**Detail**:

ISS-08 MODERATE (cross-repo). TrainingMonitor.current_phase initialized to "output" at juniper-cascor/lifecycle/monitor.py:111, never updated during training. When training enters candidate phase, TrainingLifecycleManager updates training_state and state_machine (manager.py:270) but NOT monitor.current_phase. Since metrics recorded via monitor.on_epoch_end() reads self.current_phase, all metrics history entries have phase="output" regardless of actual training phase. Result: phase-colored scatter plots show all data as "Output Training" (never "Candidate Training"); substring matching prevents candidate-phase color-coding.

**Design**:

Fix in juniper-cascor repository: update monitor.current_phase when LifecycleManager transitions phases.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Identified by v5 (unique finding). This is a juniper-cascor bug, not juniper-canopy bug. Fix must be applied in cascor repository.

### JR-CAS-TRAIN-034 — Code cleanup deferred items: Roll concept removal, candidate factory refactor, 120-char line length, LogConfig params, logger TODOs, commented code.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 263-282)

**Detail**:

CASCOR-P1-008: Remove Roll concept in CandidateUnit. P3-001: Candidate factory refactor (_create_candidate_unit()). MED-014: Line length 120 characters. INT-P4-012: LogConfig.__init__ parameter naming. INT-P4-013: Logger TODO cleanup. INT-P4-014: Remove commented-out code blocks. INT-P4-015: Clean up "Original corrupted line" comments. INT-P4-016: Remove uuid import alias redundancy. ENH-009: Per-instance queue management. ENH-010: Process-based plotting. INT-P4-010/011: Multiprocessing metrics and fallback testing. All status: 🔵 DEFERRED for post-release.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CAS-TEST-018 — Create end-to-end integration tests spinning up JuniperData and full pipeline.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 581-591)

**Detail**:

No automated integration tests spin up JuniperData and verify full pipeline (Cascor →
JuniperData → artifact → tensor conversion → training). All current tests use mocks.

### JR-CAS-WS-006 — Documentation generation: CLI setup guide (Claude Code + Serena MCP configuration, auto-start, troubleshooting).

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/setup_config_guides/claude-code-serena-setup-guide.md` (lines 1-100)

**Detail**:

Native installer for Claude Code (no Node.js required), uvx for Serena (from GitHub), global MCP server configuration with --project-from-cwd auto-detection, validation procedures (claude doctor, /mcp status check), troubleshooting (uvx path, Serena startup, port 24282, PATH resolution). File locations: ~/.local/bin/claude, ~/.claude/settings.json, ~/.claude.json. Per-project configuration alternative. Documentation complete with 8 sections and reference tables.

### JR-CAS-PERF-005 — Infrastructure enhancements: GPU/CUDA support, continuous profiling (Grafana Pyroscope), large file refactoring, auto-generated API docs.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 253-267)

**Detail**:

P3-NEW-003: GPU/CUDA support (XL, 2-4 weeks, 🔴 NOT STARTED). P3-NEW-004: Continuous profiling with Grafana Pyroscope (🔵 DEFERRED, L effort). Large file refactoring (no file > 2000 lines, 🔴 NOT STARTED, L effort). Auto-generated API docs (MkDocs/Sphinx, 🔴 NOT STARTED, M effort). Documentation link checking in CI (🔴 NOT STARTED, S effort). Documentation search functionality (🔴 NOT STARTED, M effort). All marked future work or deferred.

**Notes**:

[v2 ARCH→PERF re-bucket] [v2 remap: AR→ARCH]

### JR-CAS-TRAIN-035 — Per-instance queue management to avoid cross-instance interference.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Complex refactor; deferred to later phase.

### JR-CAS-PERF-006 — Process-based async plotting to avoid blocking training.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Depends on BUG-002 verification.

### JR-CAS-LOCK-003 — Reconcile version across pyproject.toml, file headers, and API response metadata.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 820-824)

**Detail**:

Consider using single-source-of-truth version via importlib.metadata.version() instead of file header strings.

### JR-CAS-TOOL-010 — Remove legacy stale duplicate file check.py (duplicate of spiral_problem.py).

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 275-279)

### JR-CAS-TEST-019 — Test WebSocket responsiveness during training under load via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 622-632)

**Detail**:

When Cascor training runs via asyncio.run_in_executor() in FastAPI, WebSocket
responsiveness should be verified under load.

### JR-CAS-DEP-001 — Validate docker-compose configuration for 3-service deployment end-to-end.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 594-603)

**Detail**:

docker-compose config for 3-service deployment not tested end-to-end.
