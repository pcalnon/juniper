# Requirements — TRAIN

**Area**: training — cascor algorithm, candidates, convergence, model state

**Total entries**: 156

**By status**: proposed=106 | designed=10 | shipped=35 | deferred=2 | rejected=1 | superseded=2

**By priority**: P0=22 | P1=55 | P2=70 | P3=9

**By owner**: ml=106 | cas=35 | can=12 | rec=2 | ccl=1

---

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

### JR-ML-TRAIN-005 — Increase output retraining from 50 mini-batch steps to full-batch training after hidden unit installation.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 118-131)

**Detail**:

Demo: ~1,600 sample evaluations; CasCor: ~2,000,000 (1,250× difference). New hidden unit weight initialized ~0.1; needs ample optimization time. Current 50 steps insufficient (~0.125 total change).

**Notes**:

Root cause RC-3; doc status indicates implementation complete

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

### JR-ML-TRAIN-008 — CasCor remote workers must support dynamic joining/leaving, tolerate intermittent connections, and provide task redistribution on failure.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 329-360)

**Detail**:

FR-1: Workers connect before/after training. FR-3: Tolerate intermittent connections. FR-6: Dynamic join/leave during rounds. FR-7: Automatic task redistribution on worker failure.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

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

### JR-CAS-TRAIN-012 — 18 verified bug fixes across architecture, training logic, serialization, runtime; 15 critical/high items addressed.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 60-90)

**Detail**:

INT-P0 items: walrus operator precedence, ActivationWithDerivative duplication, CandidateUnit constructor params (name-mangled), datetime alias misleading, global declaration, validation logic. INT-P2 items: conftest fast-slow inversion, roll_sequence memory, os._exit usage, traceback imports. INT-P1 items: requests undeclared dependency, JuniperData retry logic, dill dependency. BUG-001/002: random state restoration, logger pickling multiprocessing. Convergence threshold fix. Leaf tensor autograd RuntimeError. Module naming collision (constants→cascor_constants). Polyrepo Phase 1 duplicate elimination. All 18 fixed with codebase validation.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-CAS-TRAIN-013 — All Phase 1 enhancements from CASCOR_ENHANCEMENTS_ROADMAP implemented and tested.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PHASE1_COMPLETE.md` (lines 9-17)

**Detail**:

Status complete 2025-10-28. BUG-001 (test random state restoration), BUG-002 (logger
pickling error) fixed. ENH-001 through ENH-008 implemented. MVP code-complete and
ready for testing phase. Zero breaking changes. All P0 and P1 work done.

### JR-CAS-TRAIN-014 — CasCor service API must serialize training access via lock or dedicated thread.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-674)

**Detail**:

CascadeCorrelationNetwork is NOT thread-safe. API layer must serialize access via a lock or run training in dedicated thread with message-passing interface.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

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

### JR-ML-TRAIN-009 — Derive candidate_pool_phase from phase_detail in Canopy adapter.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 686-709)

**Detail**:

Adapter derives candidate_pool_status but not candidate_pool_phase. One-line fix: map phase_detail to pool phase (Training/Selecting/Idle).

**Notes**:

Phase 2 P1 fix; doc status COMPLETE; simple derivation gap

### JR-ML-TRAIN-010 — Enhance grow iteration callback with top 2 candidate ID and correlation data.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 148-167)

**Detail**:

Top candidate info never forwarded from CasCor to Canopy; TrainingResults dataclass contains data but callback does not pass it. Fix: add best_candidate_id, best_candidate_uuid, second_candidate fields to callback signature.

**Notes**:

Phase 2 P1 fix; data already available in TrainingResults; doc status COMPLETE

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

### JR-CAS-TRAIN-020 — Performance optimizations: thread pinning (5-15x), direct queues (3-10x), shared training data, persistent workers (20-50%), cached forward pass (22-1607x isolated).

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 90-120)

**Detail**:

RC-1: torch.set_num_threads(1) + BLAS env vars → 5-15x improvement. RC-2: Direct mp.Queue vs BaseManager → 3-10x additional. RC-3: Shared training data reduces N-fold serialization. RC-4: Persistent worker pool 20-50% latency reduction. OPT-1: Pre-allocated forward buffer eliminates N+1 torch.cat. OPT-2: Batch correlation (torch.dot + linalg.norm) → 5-10%. OPT-4: Cached forward pass 22-1607x isolated, 5-15% total. OPT-5: SharedMemory training tensors 5-20% reduction. OPT-6: Single-output correlation fix 37x speedup (18.24ms → 0.49ms). Forward pass sub-linear (0→50 units = 1.86x). Convergence threshold in patience.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-ML-TRAIN-011 — Use Pearson correlation (normalized) instead of raw covariance in candidate training.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 259-283)

**Detail**:

Raw covariance scales with residual magnitude; after first hidden unit, residuals shrink, candidate training gradients weaken (~8× decay observed). Pearson normalized by stddev, scale-invariant.

**Notes**:

Root cause RC-11; Phase 3 finding; doc status indicates implementation complete

### JR-ML-TRAIN-012 — Align fake responses/status values with real CasCor once contract tests exist.

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1636-1642)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v4 brief repaired; was: '15.3 Optional / Recommended Cleanup']

### JR-ML-TRAIN-013 — Final resolution**: **Known limitation**. This is not a bug — it is an architectural limitation of CasCor's API. Requires CasCor API….

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1156-1164)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '7.7 Dataset Scatter: Active Bug vs Known Limitation']

### JR-ML-TRAIN-014 — **Phase 1** defined normalization targeting flat keys (correct for CasCor → Canopy boundary).

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1210-1219)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v4 brief repaired; was: '8.3 How the Problem Compounds (Best Articulated by P4-D)']

### JR-ML-TRAIN-015 — Rationale**: Proposal A's evidence is valid and preserved (current CasCor sends title-case). Proposal B's classification better matches….

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 1099-1109)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '7.1 Uppercase Status Gap: Removed vs Retained']

### JR-ML-TRAIN-016 — The Phase 1 "Canonical Internal Contract" (Section 6.2) defined flat keys by analyzing the normalization boundary (CasCor → canopy….

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (lines 168-195)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '3.1 Phase 1: Correctly Implemented but Incompletely Validate']

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

### JR-ML-TRAIN-017 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: VERIFIED + test added.

**Status**: rejected  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 360-378)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: VERIFIED + test added

**Notes**:

[v3 brief repaired from cited content; was: '4.1 CR-023: Whitelist Training Start Parameters']

### JR-ML-TRAIN-018 — 0-cascor: `git revert` P1.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 342-343)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-019 — 0-cascor: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 339-340)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-020 — 0-cascor: `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 340-341)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-021 — 0-cascor: Rolling cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 341-342)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-022 — 06: Reconnection storm after cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 380-381)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-023 — 11: Silent data loss via drop-oldest.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 385-386)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-024 — 14: Cascor crash mid-broadcast.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 388-389)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-025 — --: Phase 0-cascor staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 295-296)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-026 — [x] **Status**: ✅ Fixed (2026-04-03 — branch `fix/regression-phase2-cascor`, PR #62).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md` (lines 103-153)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: 'Phase 2:'] From JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-ROADMAP.md

### JR-ML-TRAIN-027 — A-SDK: Downgrade cascor-client pin.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 343-344)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-028 — Add to `_STATE_FIELDS`:.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 491-505)

**Detail**:

**Effort**: 1 day | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '5.1 Define Progress Fields in TrainingState']

### JR-ML-TRAIN-029 — C-09: Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 234-235)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-030 — C-10: Adapter->cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 256-257)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-031 — C-12: Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 268-269)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-032 — CCC-01: Wire-format schema evolution — strictly additive, no field rename/retype/remove; rollout state matrix.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-03-CROSS-CUTTING-CONCERNS.md` (lines 59-146)

**Detail**:

Wire format is additive-only. Every field added in Phase 0-cascor (seq, emitted_at_monotonic, replay_buffer_capacity, server_instance_id)
is present but may be ignored by older clients. No field is renamed, retyped, or removed.
Rollout state matrix documents per-phase per-endpoint compatibility: which fields are present,
which are optional, which old clients tolerate.
Acceptance criteria: rollout doc completed, PR contains state matrix, no surprises in cross-repo CI.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Cross-cutting. Applies to all phases touching wire. Dedup with R3-03.

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

### JR-ML-TRAIN-033 — Correctness: no state loss.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CCL-TRAIN-001 — Create testing constants module juniper_cascor_client/testing/constants.py with ~65 constants (hyperparams, scenario params, topology, worker sim).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 23-37)

**Detail**:

Sections: Fake Client Configuration (URL, version, error rate, uptime), Training Hyperparameters
(learning rate, epochs, hidden units, patience), Loss/Accuracy Curve Parameters (per scenario),
Network Topology Generation (bias, weight scales), Decision Boundary Generation, Worker Simulation Data,
Dataset Configuration.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Part of hardcoded-values refactor (HIGH priority)

### JR-ML-TRAIN-034 — D-2: Phase 0-cascor carve-out (D-11).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 119-120)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-035 — D-**Cascor crash mid-broadcast** (RISK-14): Low.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 135-136)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-036 — D-Correctness: no state loss: `cascor_ws_dropped_messages_total{type="state"}`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-037 — D-**Silent data loss** (RISK-11): High (low likelihood).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 133-134)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-038 — Effort bounds and calendar: 15.75 expected eng days (~4.5 weeks calendar) with soak windows.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R4-01-COMPREHENSIVE-MASTER-PLAN.md` (lines 76-94)

**Detail**:

Effort table (optimistic/expected/pessimistic): Phase 0-cascor 1.5/2.0/3.0, A-SDK 0.5/1.0/1.5, B-pre-a 0.5/1.0/1.5,
B 3.0/4.0/5.0, B-pre-b 1.0/1.5/2.0, C 1.5/2.0/3.0, D 0.75/1.0/1.5, E 0.75/1.0/1.5, F 0.25/0.5/1.0,
G 0.25/0.5/0.75, H 0.5/1.0/1.5, I 0.1/0.25/0.5. Total 10.6/15.75/22.25 eng days.
Calendar translation: 15.75 days × single-dev lane = ~3 weeks one-person, or ~4.5 weeks with 48-72 h soak windows.
Minimum-viable carveout (P0 only): ~7 days (Phase A-SDK + 0-cascor + B-pre-a + B + I).
Soak windows: 0-cascor 72 h, Phase B 72 h, B-pre-b 48 h, Phase C canary >=7 days.
Phase dependency graph: A-SDK || 0-cascor || B-pre-a → B || B-pre-b → D; C parallel with B/D; E/F/G/H follow.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Risks: 0-cascor async race (+risk), A-SDK correlation map iteration (+risk), B-pre-a audit logger name collision (+risk),
B NetworkVisualizer Plotly (+1 day), B-pre-b session middleware absent (+0.5 day), C concurrent-correlation bugs (+risk),
D orphaned-command UI state (+risk), E queue tuning (+risk), F reconnect-cap lift debated.

### JR-ML-TRAIN-039 — ERR-02: `response.json()` Unguarded in cascor-client `_request()`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4429-4443)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-040 — ERR-06: `raise HTTPException` Without `from e` — Lost Exception Context (cascor).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4446-4460)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-041 — Fix BUG-CC-12: replace yaml.safe_load with torch.load or safetensors in cascor utils.py.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md` (lines 71-77)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-042 — Fix CasCor demo training error with identified root cause and remediation.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN-OLD.md` (lines 1-100)

**Notes**:

Legacy plan version; check for updates in primary plan.

### JR-CAS-TRAIN-023 — Fix epoch/iteration semantic error in grow_network() and ValidateTrainingInputs dataclass; rename for correctness.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/analysis/REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-180)

**Detail**:

Each grow_network() loop iteration performs complete Cascade Correlation growth cycle (candidate training, selection, installation), not single epoch. Rename max_epochs→max_iterations, epoch→iteration, epochs_completed→iterations_completed, log "Iteration" not "Epoch". Update ValidateTrainingInputs fields. Callers: fit() line 1445, unit tests. No breaking API changes. Backward-compatible alias pattern available (lines 1375-1379). Estimated 2-4 hours effort. Non-functional behavior change.

**Notes**:

[v2 remap: BG→TRAIN]

### JR-ML-TRAIN-043 — Fix tensor dimension mismatch issues in CasCor batch processing pipeline.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_TENSOR_DIMENSION_MISMATCH_ANALYSIS.md` (lines 1-100)

**Notes**:

Analysis-based remediation for candidate training.

### JR-ML-TRAIN-044 — Implement root cause fix for CasCor training stall based on proposal analysis.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md` (lines 1-100)

**Notes**:

Blocks training completion.

### JR-ML-TRAIN-045 — Phase 3: Layout.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 537-544)

**Detail**:

1. Replace Training Parameters card with Meta Parameters card

### JR-ML-TRAIN-046 — Remediate training stall issue with identified root cause and proposed solution.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/TRAINING_STALL_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Blocking training completion; high priority fix.

### JR-ML-TRAIN-047 — **Strengths of B**: More explicit parsing, handles whitespace in values.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 131-171)

**Detail**:

**2.1.1 CI path fix** (`ci.yml:244`):

**Notes**:

[v3 brief repaired from cited content; was: '2.1 juniper-ml: CI & Script Fixes']

### JR-ML-TRAIN-048 — Training Control.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 315-323)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 251-259)

*Merged from 2 extraction candidates (slices: 3c-2b).*

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

### JR-ML-TRAIN-049 — Concurrency Assessment.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 324-330)

**Detail**:

**WebSocket Mode**: Well-designed single-threaded asyncio with `asyncio.to_thread` for CPU-bound training. No shared mutable state between async loop and training thread

### JR-ML-TRAIN-050 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 419-434)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.4 CR-025: WebSocket Async Lock']

### JR-ML-TRAIN-051 — Update `TrainingSettings` model to include new `TrainingParamConfig` entries:.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 314-331)

**Detail**:

epochs: TrainingParamConfig = TrainingParamConfig(min=10, max=10000000, default=1000000)

**Notes**:

[v3 brief repaired from cited content; was: '5.4 `settings.py`']

### JR-ML-TRAIN-052 — (Unchanged from v3 — Phases 0-cascor, A-SDK, B-pre-a, B, C, D all ✅ Complete.).

**Status**: superseded  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-21_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V4-VALIDATED.md` (lines 289-324)
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V5-VALIDATED.md` (lines 323-360)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '8. WebSocket Migration (R5-01 Remaining Phases)'] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

[v3 brief repaired from cited content; was: '8. WebSocket Migration (R5-01 Remaining Phases)'] Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-TRAIN-053 — V6 Partial — Agent B: Active Bugs (CasCor, Canopy, Data).

**Status**: superseded  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-B-ACTIVE-BUGS.md` (lines 1-100)

**Notes**:

[v2 ARCH→TRAIN re-bucket] v6 partial agent output; pre-dates V6_REMEDIATION_ANALYSIS — likely subsumed by V6/V7 entries already captured by ml-C

### JR-ML-TRAIN-054 — Phase 2 test: the demo backend must produce hidden-to-hidden cascade connections

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 760-775)

**Detail**:

`# Setup: create network with 2+ hidden units`

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 2 Tests']

[2026-08-29 brief repaired from cited content; was: '"""Demo backend must produce hidden-to-hidden cascade connections.""".']

### JR-ML-TRAIN-055 — Adam Optimizer Pathology: fix Adam optimizer pathology issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-07-ADAM-OPTIMIZER-PATHOLOGY.md` (lines 1-44)

### JR-ML-TRAIN-056 — Add `progress_queue` to persistent forkserver worker pool:.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 543-556)

**Detail**:

**Effort**: 3-5 days | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '5.5 Option A: Candidate Progress Queue']

### JR-ML-TRAIN-057 — Add tests for `run()` → `_message_loop()` → `_handle_task_assign()` flow, `_heartbeat_loop`, and connection loss/reconnection. Target:….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 214-243)

**Detail**:

**2.5.1 Fix signal handler thread safety** (`worker.py:121`, `cli.py:95`):

**Notes**:

[v3 brief repaired from cited content; was: '2.5 juniper-cascor-worker: Thread Safety & Coverage']

### JR-ML-TRAIN-058 — After training fails or completes, `start_training()` bypasses the guard (only checks `is_started()`), but `handle_command(Command.START)`….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 154-182)

**Detail**:

**Severity**: S1 | **Effort**: Medium (1 day) | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '3.2 CR-007: Auto-Reset State Machine on Start']

### JR-ML-TRAIN-059 — All structural IDs exist (headers, collapses, icons).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 460-471)

**Notes**:

[v4 brief repaired; was: '8.1 Unit Tests - Layout Verification']

### JR-CAN-TRAIN-004 — Candidate pool handling on dataset swap: Option C selected—abandon all candidates and force output-training-first mode on new dataset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 128-131)

**Detail**:

After architecture adaptation, drop candidate pool. Submit new training future with mode='output_training_first' forcing immediate output training on new dataset before any new candidate-pool training.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Alternative options (keep candidates, retrain on new data) considered and rejected.

### JR-ML-TRAIN-060 — Candidate Quality Decay: address candidate quality degradation in long training runs.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-02-CANDIDATE-QUALITY-DECAY.md` (lines 1-40)

### JR-ML-TRAIN-061 — CFG-14: `juniper-cascor-client>=0.1.0` Allows Outdated Incompatible Versions.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 5078-5092)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-062 — CI-01: cascor-client CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4643-4657)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-063 — CI-02: cascor-worker CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4660-4664)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-064 — CI-05: Missing lockfile-update.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4698-4709)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-065 — `cn-training-convergence-threshold-input`.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 56-71)

**Detail**:

| 2   | Correlation Threshold     | `cn-correlation-threshold-input`          | number (float) | 0.001               | NEW         |

**Notes**:

[v4 brief repaired; was: '2.2 Candidate Nodes Subsection (10 inputs)']

### JR-ML-TRAIN-066 — Convergence Timing: optimize convergence detection timing.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-04-CONVERGENCE-TIMING.md` (lines 1-46)

### JR-ML-TRAIN-067 — DEFAULT_CANDIDATE_CORRELATION_THRESHOLD: Final[float] = 0.001.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 149-197)

**Detail**:

DEFAULT_CANDIDATE_CORRELATION_THRESHOLD: Final[float] = 0.001

**Notes**:

[v3 brief repaired from cited content; was: '3.3 New Candidate Nodes Constants']

### JR-ML-TRAIN-068 — DEFAULT_TRAINING_EPOCHS: Final[int] = 1000000    # was 300.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 99-114)

**Detail**:

DEFAULT_TRAINING_EPOCHS: Final[int] = 1000000    # was 300

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Modified Existing Constants']

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

### JR-ML-TRAIN-069 — `demo_backend.py:get_network_topology()` only creates input-to-hidden connections. It does not create hidden-to-hidden cascade connections….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 357-361)

**Detail**:

`demo_backend.py:get_network_topology()` only creates input-to-hidden connections. It does not create hidden-to-hidden cascade connections that are the defining featur

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-TRAIN-070 — During `CascorStateSync.sync()`, the topology is fetched and transformed correctly into `SyncedState.topology`. However, in `main.py` where….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 475-479)

**Detail**:

During `CascorStateSync.sync()`, the topology is fetched and transformed correctly into `SyncedState.topology`. However, in `main.py` where the synced state is applied, only training status/epoch/params are pushed to the app state — the synced topology is never written to the Das

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-TRAIN-071 — Enable Canopy to connect to external CasCor instances with connection orchestration.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_EXTERNAL_CASCOR_PLAN.md` (lines 1-100)

**Notes**:

[v2 ARCH→TRAIN re-bucket] Approved for implementation.

### JR-ML-TRAIN-072 — **File**: `juniper-cascor-client/constants.py:31`.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 340-345)

**Detail**:

**File**: `juniper-cascor-client/constants.py:31`

**Notes**:

[v3 brief repaired from cited content; was: '6.2 Medium: 503 Not Retried (XREPO-02 — confirmed STILL PRES']

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

### JR-ML-TRAIN-073 — HSK-05: cascor-client AGENTS.md Header Version 0.3.0 vs Package 0.4.0.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2919-2933)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-074 — HSK-07: cascor-client File Headers Show Versions 0.1.0–0.3.0.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2943-2947)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-075 — HSK-09: Dead Code `_STATE_TO_FSM` and `_STATE_TO_PHASE` in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2957-2982)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-076 — HSK-23: `scripts/juniper-all-ctl:38` Cascor Port Defaults to 8200 (Container) vs Host 8201.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3235-3249)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-077 — HSK-24: Unused Constants in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3252-3277)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAS-TRAIN-030 — Integration fixes: 9 JuniperData items (API path, deprecation warnings, auth, NPZ validation, contract tests, retry/backoff).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 138-145)

**Detail**:

CAS-INT-001 through CAS-INT-009 verified complete. Items include: API path validation, deprecation warning handling, authentication token management, NPZ format validation, data contract tests, max_retries=3 retry logic with backoff, status code normalization, error classification. All integrated with current JuniperData REST API. Async training boundary via ThreadPoolExecutor. RemoteWorkerClient integration via REST endpoints. Test suite CI/CD phases 0-4 complete (MED-014 line length deferred).

**Notes**:

[v2 remap: BG→TRAIN]

### JR-ML-TRAIN-078 — Investigate V38 grow-network performance; characterize scaling limits and convergence behavior.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-CASCOR_V38-GROW-NETWORK-INVESTIGATION-PLAN.md` (lines 1-50)

### JR-ML-TRAIN-079 — `juniper-cascor-client/testing/__init__.py` exports `FakeCascorClient` and `FakeCascorTrainingStream` only. No fake for….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 345-349)

**Detail**:

`juniper-cascor-client/testing/__init__.py` exports `FakeCascorClient` and `FakeCascorTrainingStream` only. No fake for `CascorControlStream`. Consumers testing WebSocket control (e.g., `set_params`) cannot use the testing subpackage.

**Notes**:

[v3 brief repaired from cited content; was: '6.3 Medium: No FakeCascorControlStream (XREPO-03 — confirmed']

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

### JR-ML-TRAIN-080 — M-JCW-2: No WebSocket receive timeout (`ws_connection.py:134`).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 306-317)

**Detail**:

**M-JCW-1: No task execution timeout** (`worker.py:201`)

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-ML-TRAIN-081 — Neither `CascorTrainingStream` nor `CascorControlStream` implements reconnection. For training runs lasting hours, a network hiccup….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 228-239)

**Detail**:

**H-JCC-1: CHANGELOG missing v0.2.0 and v0.3.0 entries**

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-TRAIN-082 — Network Architecture.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 330-337)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 266-273)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-TRAIN-083 — No integration tests against live cascor; no `FakeCascorControlStream` (XREPO-03 confirmed); no test markers on `test_set_params.py`.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 81-89)

**Detail**:

| `client.py`    | 82.22%   | `wait_for_ready()` polling, JSON decode errors, fallback error message path                                                          |

**Notes**:

[v4 brief repaired; was: '1.4 Test Coverage Gaps']

### JR-CAN-TRAIN-009 — Normalize state sync metrics history through adapter (ISS-05 latent formatting).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 381-401)

**Detail**:

ISS-05 MODERATE. During initial state sync (state_sync.py:115-129), CascorStateSync.sync() stores raw cascor metrics directly into state.metrics_history without normalization. Raw cascor uses native field names (loss, accuracy, validation_loss, validation_accuracy, hidden_units) — different from flat canopy format (train_loss, train_accuracy) and demo nested format. Currently latent: synced.metrics_history stored but never served; polling makes fresh REST calls through normalization. Future risk: pre-populating charts from synced metrics on connect would deliver wrong format (double latent — even flat normalization wouldn't match dashboard nested consumption without ISS-01 fix).

**Notes**:

[v2 ARCH→TRAIN re-bucket] Identified by v1, v3, v5, v6, v7. Structural cause underlying ISS-05, ISS-06, ISS-12. Sync module should go through adapter or replicate normalization logic.

### JR-ML-TRAIN-084 — Output Weight Initialization: improve output layer weight init.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-05-OUTPUT-WEIGHT-INIT.md` (lines 1-38)

### JR-ML-TRAIN-085 — **Outstanding**: No version bump for unreleased constants refactor. Integration test marker defined but zero tests.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 381-392)

**Detail**:

| Hardcoded values refactor → `constants.py`                 | ✅ Complete (~70 replacements) |

**Notes**:

[v3 brief repaired from cited content; was: '7.2 juniper-cascor-worker — All Planned Work ✅ COMPLETE']

### JR-ML-TRAIN-086 — Phantom Inter-Cascade Training Phase: remove 1-step/epoch phantom training phase.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-01-PHANTOM-TRAINING-PHASE.md` (lines 30-48)

### JR-ML-TRAIN-087 — Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 49-49)

**Notes**:

[v2 ARCH→TRAIN re-bucket] Settled position C-12 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-088 — Phase A-SDK — ✅ IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 315-322)

**Detail**:

| `CascorControlStream.set_params()` with `command_id` correlation | ✅ In `ws_client.py` |

### JR-ML-TRAIN-089 — Post-Reset Desynchronization: fix desync after model reset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-10-POST-RESET-DESYNC.md` (lines 1-38)

### JR-ML-TRAIN-090 — Priority**: SHOULD complete before release.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 113-131)

**Detail**:

**CHANGELOG changes**: Populate [Unreleased] section, then rename to [0.4.0] covering:

**Notes**:

[v3 brief repaired from cited content; was: '1.6 juniper-ml: CHANGELOG & Tags']

### JR-ML-TRAIN-091 — `_recv_loop` catches bare `Exception` — swallows programming errors, pending futures time out.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 377-387)

**Detail**:

| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                | 🔴 Open            |

**Notes**:

[v4 brief repaired; was: '15.1 juniper-cascor-client']

### JR-CAN-TRAIN-010 — Remove orphaned candidate callbacks from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 161-161)

**Detail**:

Issue 3.2.2: Callbacks in MetricsPanel that reference removed candidate display.
Remove or reconnect to active candidate pool UI.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-092 — Residual Variance Collapse: address residual variance collapse in training.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-09-RESIDUAL-VARIANCE-COLLAPSE.md` (lines 1-46)

### JR-ML-TRAIN-093 — RISK: Correctness: no state loss.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-094 — Spiral Complexity: limit spiral depth and complexity growth.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-03-SPIRAL-COMPLEXITY.md` (lines 1-50)

### JR-CAS-TRAIN-031 — Support multiple optimizer types via configuration (Adam, SGD, RMSprop, AdamW).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 749-773)

### JR-ML-TRAIN-095 — Tanh Saturation: address tanh saturation issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/JUNIPER_2026-03-19_JUNIPER-CASCOR_PROPOSAL-06-TANH-SATURATION.md` (lines 1-38)

### JR-ML-TRAIN-096 — Task 3 (Topology).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 366-374)

**Detail**:

- Exact lines confirmed: 582 and 611 in cascor_service_adapter.py

### JR-ML-TRAIN-097 — The cascor state machine returns UPPERCASE state names (`"STOPPED"`, `"STARTED"`), while `TrainingState.get_state()` returns title-case….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 402-409)

**Detail**:

**Repositories**: juniper-cascor, juniper-cascor-client

**Notes**:

[v3 brief repaired from cited content; was: '3.3 State Name Inconsistency']

### JR-ML-TRAIN-098 — Topology updates after `cascade_add` are delayed by up to 5 seconds.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 245-251)

**Notes**:

[v3 brief repaired from cited content; was: 'Consequence']

### JR-ML-TRAIN-099 — TQ-01: 10+ Tests with No Assertions (cascor).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4775-4786)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-100 — TQ-04: 139 `hasattr` Guards in cascor Tests.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4817-4821)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-CAN-TRAIN-011 — TrainingStateMachine must protect all state mutations with threading.Lock to ensure thread safety.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 177-181)

**Detail**:

HIGH-015: Add threading.Lock on all state mutations AND getters (partial fix in prior audit lacked lock on getters).
Independent of R5-01; backend state management concern.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; partially remediated prior; full coverage required.

### JR-ML-TRAIN-101 — Worker protocol constants (`MSG_TYPE_*`, `BINARY_FRAME_*`) must remain bit-identical to cascor's `MessageType(StrEnum)` in `protocol.py`.….

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 349-353)

**Detail**:

Worker protocol constants (`MSG_TYPE_*`, `BINARY_FRAME_*`) must remain bit-identical to cascor's `MessageType(StrEnum)` in `protocol.py`. Wave 5 verified alignment, but **no automated CI check exists**. A cascor protocol change could silently break worker connectivity.

**Notes**:

[v3 brief repaired from cited content; was: '6.4 Medium: Protocol Constants Alignment is Manual']

### JR-ML-TRAIN-102 — ✅ Complete (header version needs bump 0.3.0 → 0.4.0).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 374-381)

**Detail**:

| Hardcoded values refactor → `constants.py` | ✅ Complete (126 lines, 330 test constants)           |

**Notes**:

[v4 brief repaired; was: '7.1 juniper-cascor-client — All Planned Work ✅ COMPLETE']

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

### JR-ML-TRAIN-103 — Trigger / due date.** None — opportunistic. May get pulled in if TRAIN-ARCH-01 unblocks (Q4 of that design doc covers the per-step vs….

**Status**: designed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 227-243)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.7 R5.6-THROTTLE — Cascor 25-epoch emit throttle removal']

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

### JR-ML-TRAIN-105 — [ ] **Task 6.2.2**: Verify training starts and completes epoch 1+.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 190-220)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: 'Phase 6:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

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

### JR-CAN-TRAIN-012 — Defer true IPC architecture (Cascor-Canopy process separation) to future when triggering conditions are met.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 407-433)

**Detail**:

Current architecture embeds CasCor within Canopy process. Deferral justified by RemoteWorkerClient and async training providing sufficient capability. Revisit if hard cancellation, multiple concurrent jobs, or remote clusters needed.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Phase 4 deferred; has explicit trigger conditions

### JR-ML-TRAIN-106 — **Goal**: Ensure cascor exposes all required fields for canopy consumption.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md` (lines 49-65)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: 'Phase 2:'] From JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-DEVELOPMENT-ROADMAP-04.md

### JR-CAS-TRAIN-035 — Per-instance queue management to avoid cross-instance interference.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Complex refactor; deferred to later phase.

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
