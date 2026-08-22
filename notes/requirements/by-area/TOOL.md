# Requirements — TOOL

**Area**: dev tooling / scripts / workflow — worktree procs, claude-code launchers

**Total entries**: 68

**By status**: proposed=58 | designed=1 | shipped=9

**By priority**: P0=1 | P1=9 | P2=55 | P3=3

**By owner**: ml=48 | cas=10 | cwk=3 | dat=2 | dep=2 | rec=2 | can=1

---

### JR-CAS-TOOL-001 — Fix ./try convenience script path resolution errors in helper scripts.

**Status**: proposed  **Priority**: P0  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 201-252)

**Detail**:

Helper scripts (GET_OS_SCRIPT, GET_PROJECT_SCRIPT, DATE_FUNCTIONS_SCRIPT) are overridden as bare filenames. Fix to use absolute paths derived from BASH_SOURCE[0]. Update conf/script_util.cfg to correctly compute ROOT_PROJECT_DIR with proper project hierarchy.

### JR-CAS-TOOL-002 — Complete CI/CD infrastructure: pre-commit 21 hooks, coverage 80%, GitHub Actions matrix (3.11/3.12/3.13), security scanning.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/pull_requests/PR_full_branch_spiral_gen_extract_pre_deploy.md` (lines 1-100)

**Detail**:

91% test coverage achieved (from ~15%), 1333+ tests. CI pipeline: GitHub Actions matrix (3.11/3.12/3.13), scheduled nightly tests, pre-commit hooks (21 total), coverage enforcement (80%), security scanning (Bandit, Gitleaks, pip-audit). 28 version increments (0.0.1 → 0.7.0). Critical fixes: multiprocessing completion logic, undefined queue_timeout, test timeouts, snapshot serializer TypeError, candidate training result parsing, task parameter wiring, best_candidate_id selection, NaN input handling.

**Notes**:

[v2 remap: CL→TOOL]

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

### JR-CWK-TOOL-001 — Worktree cleanup procedure with CWD continuity: create new worktree before removing old one to avoid trapping Claude Code sessions in invalid paths.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (lines 1-15)

**Detail**:

The V1 procedure (see notes/history/WORKTREE_CLEANUP_PROCEDURE_V1.md) removed the worktree directory without first creating a replacement, leaving the session trapped. V2 creates a new worktree and switches CWD before removing the old one (Phase 2 must complete before Phase 4). Phases: 1 Save & Push, 2 Create New Worktree (session continuity gate), 3 Merge & Pull Request, 4 Remove Old Worktree (prerequisite: new CWD verified), 5 Verify.

**Design**:

Phase 2 is the critical gate: CWD must move to the new worktree (Step 5) before the old one is removed (Phase 4, Step 9). The procedure enforces this with explicit verification gates in Step 6.

### JR-CAS-TOOL-003 — Hardcoded values extraction into constants module; 56 hardcoded values across API layer, lifecycle manager, observability require extraction.

**Status**: designed  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/HARDCODED_VALUES_ANALYSIS.md` (lines 1-100)

**Detail**:

New module cascor_constants/constants_api/constants_api_defaults.py with 43 constants. Target location: cascor_constants/ hierarchy extended. Approach A recommended: extend existing cascor_constants/ pattern (vs. Approach B: centralize in settings.py, Approach C: hybrid). Files requiring modification: 16 (models, lifecycle, observability, routes, service_launcher, middleware, app, workers, candidate_unit, spiral_problem, snapshots, profiling).

**Notes**:

[v2 remap: CL→TOOL]

### JR-DEP-TOOL-001 — Create juniper-ctl CLI wrapper for systemd management (start/stop/restart/logs/health/resources).

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 256-274)

**Detail**:

Management CLI wrapping systemctl --user commands with 10+ subcommands:
start/stop/restart (single or all), status (all services), logs/follow, health (latest checks),
resources (CPU/memory/IO usage), install (symlink units + daemon-reload), enable/disable (auto-start).

### JR-ML-TOOL-001 — Fix wake_the_claude.bash session validation failures.

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/wake_the_claude_failure_analysis.md` (lines 1-100)

**Notes**:

Development tooling issue.

### JR-CAN-TOOL-001 — Post-release development roadmap: Phase 0 CRITICAL (integration gaps), Phase 1 HIGH (backend), validated complete for Phase 0-1 items.

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 1-100)

**Detail**:

Phase 0 CRITICAL: Integration Gaps (Decision Boundary, Save/Load Snapshot). Phase 1 HIGH: Backend integration (Health Check, NPZ Validation). Status: SUPERSEDED — execution tracked in juniper-ml/notes. Validated as complete for most Phase 0-1 items.

**Notes**:

Superseded by more recent development plans; cross-referenced for historical context and closure verification.

### JR-CAS-TOOL-004 — Session status and validation: 18 integration tests, 11/12 MVP criteria met, ready for testing phase.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/SESSION_STATUS.md` (lines 1-150)

**Detail**:

Part 1 completed (analysis + critical fixes). Part 2 completed (validation + testing). Hidden units checksums (MD5, non-breaking), shape validation (cascade constraints), format validation (version compatibility). Test suite: 18 integration tests across 8 test classes. Metrics: 2 files modified (snapshot_serializer.py, AGENTS.md), 4 created, ~700 lines added, 2 functions. Coverage estimate 95% serialization paths, 100% validation. Status: 11/12 MVP criteria met (92%). Ready for MVP testing with test execution pending.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CWK-TOOL-002 — Thread handoff procedure: preserve context fidelity when thread compaction degrades output by proactively handing off to fresh thread before context saturation.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/THREAD_HANDOFF_PROCEDURE.md` (lines 1-35)

**Detail**:

Thread compaction introduces information loss (subtle decisions, edge cases, partial progress, reasoning get dropped). Triggers: (1) context saturation after 15+ tool calls or 5+ file edits, (2) phase boundary completion, (3) degraded recall (re-reading files), (4) multi-module transitions, (5) user request. Do NOT handoff when task is nearly complete (<2 steps) or thread is still sharp. Handoff goal structure: original task, completed items, remaining work, key discoveries, file paths.

**Design**:

Handoff protocol: (1) Checkpoint current state (task, completed, remaining, discovered, files in play), (2) Compose concise actionable goal (be specific, include paths, state decisions, mention test status, keep <500 words), (3) Present to user via handoff() tool if available (follow=true for current thread stop, follow=false rare).

### JR-CWK-TOOL-003 — Worktree setup procedure: standardized protocol for creating git worktrees when beginning a new task, centralizing worktrees in /home/pcalnon/Development/python/Juniper/worktrees/.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_SETUP_PROCEDURE.md` (lines 1-30)

**Detail**:

Prerequisites: must be in primary directory (not already in worktree), working tree clean, target branch not already checked out elsewhere. Protocol: (1) Ensure clean state, (2) Fetch and update parent branch (typically main), (3) Create working branch, (4) Compute worktree directory name using format <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>, (5) Create worktree, (6) Verify and begin work.

**Design**:

Naming convention: <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>. All worktrees in /home/pcalnon/Development/python/Juniper/worktrees/. Example: juniper-cascor-worker--feature--add-gpu-support--20260225-1430--047c3f61.

### JR-CAS-TOOL-005 — 10 open/remaining work items: hardcoded paths, stale files, fallback bugs, version inconsistencies, legacy directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 160-180)

**Detail**:

INT-P0-004: remote_client_0.py hardcoded path to monorepo (delete, superseded by juniper-cascor-worker). INT-P0-005: Hardcoded test paths (sys.path.append lines). INT-P1-008: check.py stale duplicate. INT-P2-005/006: or fallback bugs (clockwise, numeric params) → if x is not None pattern. INT-P2-014: Local traceback imports (use top-level, remove 9 instances). INT-P3-009: Version strings inconsistent (main.py 0.3.1, cascade_correlation.py 0.3.2, pyproject.toml 0.4.0). Legacy remote_client/ directory (remove or archive). Estimated effort 2-4 hours total.

**Notes**:

[v2 remap: CL→TOOL]

### JR-CAS-TOOL-006 — Address 7 codebase analysis issues: logging system gaps, startup robustness, constants over-engineering, security risks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/CODEBASE_ANALYSIS_2026-03-12.md` (lines 1-100)

**Detail**:

Logging: YAML relative paths, three independent mechanisms, CWD-dependent resolution. Startup: os._exit() usage, module-level Sentry init, lru_cache on get_settings(). Architecture: dual logging systems (CLI vs API), constants over-engineering (7 sub-packages), name-mangled constructor params, sys.path manipulation, deprecated docker-compose. Code quality: exception handling breadth, global state, LogConfig Java-style getters/setters, commented-out code, walrus operator misuse. Security: CORS wildcard risk, Sentry PII collection, nosec without ticket.

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-TOOL-002 — Algorithm Enhancements.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 323-330)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 259-266)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-TOOL-003 — CLN-CC-01: Delete Legacy `remote_client/` Directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1317-1343)

### JR-ML-TOOL-004 — CLN-CC-02: Delete Stale `check.py` Duplicate (600 Lines).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1346-1361)

### JR-ML-TOOL-005 — CLN-CC-03: Remove 9 Local `import traceback` in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1364-1378)

### JR-ML-TOOL-006 — CLN-CC-04: Enable mypy Strict Mode.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1381-1395)

### JR-ML-TOOL-007 — CLN-CC-05: Legacy Spiral Code — Trivial Getter/Setter Methods, No @deprecated.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1398-1412)

### JR-ML-TOOL-008 — CLN-CC-06: Remove "Roll" Concept in CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1415-1421)

### JR-ML-TOOL-009 — CLN-CC-07: Candidate Factory Refactor.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1424-1430)

### JR-ML-TOOL-010 — CLN-CC-08: Remove Commented-Out Code Blocks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1433-1439)

### JR-ML-TOOL-011 — CLN-CC-09: Line Length Reduction to 120 Characters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1442-1448)

### JR-ML-TOOL-012 — CLN-CC-10: `utils.py:238` — Broken `check_object_pickleability` Uses `dill` Not in Deps.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1451-1473)

### JR-ML-TOOL-013 — CLN-CC-11: `snapshot_serializer.py` — Extend Optimizer Support (In-Code TODO).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1476-1490)

### JR-ML-TOOL-014 — CLN-CC-12: `.ipynb_checkpoints` Directories Committed to Repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1493-1507)

### JR-ML-TOOL-015 — CLN-CC-13: `sys.path.append` at Module Level in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1510-1524)

### JR-ML-TOOL-016 — CLN-CC-14: Empty `# TODO :` Headers in 18+ Files.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1527-1541)

### JR-ML-TOOL-017 — CLN-CC-15: `_object_attributes_to_table` Return Type Annotation Wrong.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1544-1558)

### JR-ML-TOOL-018 — CLN-CN-01: `theme-table` CSS Class Never Implemented.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1563-1588)

### JR-ML-TOOL-019 — CLN-CN-02: NPZ Validation Only in DemoMode, Not ServiceBackend.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1591-1605)

### JR-ML-TOOL-020 — CLN-CN-03: Performance Test Suite Minimal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1608-1622)

### JR-ML-TOOL-021 — CLN-CN-04: JuniperData-Specific Error Handling Missing.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1625-1639)

### JR-ML-TOOL-022 — CLN-CN-05: DashboardManager Extraction (3,232 → Component Classes).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1642-1657)

### JR-ML-TOOL-023 — CLN-CN-06: Re-enable Remaining MyPy Disabled Codes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1660-1674)

### JR-ML-TOOL-024 — CLN-CN-07: Real Backend Path Test Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1677-1691)

### JR-ML-TOOL-025 — CLN-CN-08: Convert Skipped Integration Tests (4 Files with `requires_server`).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1694-1708)

### JR-ML-TOOL-026 — CLN-CN-09: main.py Coverage Gap (84% vs 95% Target).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1711-1725)

### JR-ML-TOOL-027 — CLN-CN-10: `main.py` Is 2,543 Lines — Second God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1728-1742)

### JR-ML-TOOL-028 — CLN-CN-11: `metrics_panel.py` Is 1,790 Lines — Third God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1745-1759)

### JR-ML-TOOL-029 — CLN-CN-12: `network_visualizer.py:1512` — Active TODO Indicating Logging Error Bug.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1762-1776)

### JR-ML-TOOL-030 — CLN-CN-13: Deprecated `_generate_spiral_dataset_local()` Still Called.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1779-1793)

### JR-ML-TOOL-031 — CLN-CN-14: `np.random.seed(42)` Sets Global Numpy Seed.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1796-1810)

### JR-ML-TOOL-032 — CLN-JD-01: `python-dotenv` Hard Dependency for Optional ARC-AGI Feature.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1815-1829)

### JR-ML-TOOL-033 — CLN-JD-02: `FakeDataClient.close()` Destroys Data.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1832-1846)

### JR-ML-TOOL-034 — CLN-JD-03: Module-Level `create_app()` at `app.py:142` — Import-Time Side Effects.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 1849-1863)

### JR-CAS-TOOL-007 — Code quality & compliance improvements: coverage thresholds, strict MyPy, pre-commit hooks, lint compliance tests.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 118-130)

**Detail**:

Pre-commit compliance: All 20 hooks pass, 9 violations fixed (F401×2, F402, C401, B007, B404, B105/B110/B107). Lint compliance tests: 162 parametrized tests (test_lint_compliance.py for future detection). Coverage threshold: fail_under = 80 in pyproject.toml. CI pipeline green (pre-commit, unit tests 3.11/3.12/3.13, security, integration, build). CPU-only PyTorch in CI configured. No critical lint violations remaining.

**Notes**:

[v2 remap: CL→TOOL]

### JR-DEP-TOOL-002 — Consolidate demo dataset parameters and shell script timeouts into config.sh.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 93-117)

**Detail**:

Shell scripts have 8 hardcoded timeouts (90s service wait, 3s poll, 3s curl, 5s health,
120s demo test, 3s demo poll, 5s training start, 90s enhanced test). Demo has 7 hardcoded
parameters (n_spirals=2, n_points=200, noise=0.15, seed=42, learning_rate=0.01, 500 epochs).
Source all from scripts/config.sh. Lower priority (LOW) per analysis.

### JR-CAS-TOOL-008 — Design decisions record: 10 items tracking ActivationWithDerivative location, CandidateUnit factory, or fallback pattern, client packages, async wrapper, large file refactoring, legacy code removal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 325-342)

**Detail**:

Decision 1 (✅ IMPLEMENTED): ActivationWithDerivative → src/utils/activation.py. Decision 2 (✅ IMPLEMENTED): CandidateUnit constructor fix (factory + remove kwargs). Decision 3 (DECIDED): or fallback → if x is not None. Decision 4 (✅ IMPLEMENTED): Client packages (PyPI). Decision 5 (✅ IMPLEMENTED): Async wrapper (ThreadPoolExecutor). Decision 6 (DECIDED, not started): Large file refactoring (mixin-based). Decision 7 (DECIDED, gated): Legacy code removal (after E2E gate). Decision 8 (DECIDED): Optimizer serialization removal. Decision 9 (🔵 DEFERRED): Multiprocessing state (partial restore). Decision 10 (✅ IMPLEMENTED): SharedMemory (Named with lightweight tasks).

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-TOOL-035 — Establish 6-type prompt classification (Handoff, Task, Template, Planning, Audit, Infrastructure) with boilerplate analysis.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` (lines 326-466)

### JR-ML-TOOL-036 — Fix broken check_object_pickleability function in utils.py:238 which uses dill not in dependencies.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (lines 3580-3590)

**Detail**:

CLN-CC-10: utils.py:238 imports and uses `dill` library which is not in project dependencies.
Function is broken. Fix by either adding dill to deps or refactoring to use pickle only.

### JR-ML-TOOL-037 — HSK-10: `scripts/test.bash` Outdated/Non-Functional.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2985-3010)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-038 — HSK-15: `util/global_text_replace.bash` Is a No-Op.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3090-3112)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-039 — HSK-16: `util/kill_all_pythons.bash` Uses `sudo kill -9` on ALL Python Processes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3115-3129)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-040 — HSK-17: `util/worktree_new.bash` Hardcodes Branch/Repo Names.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3132-3146)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-041 — HSK-18: `util/worktree_close.bash` Hardcodes Default Identifier.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3149-3163)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-042 — Implement phased prompt automation: Phase 1 snippets (1 day), Phase 2 discovery scripts (2 days), Phase 3 template rendering (2-3 days).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` (lines 1081-1150)

### JR-ML-TOOL-043 — Implement thread handoff procedure: context transfer, worktree state, verification commands.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-IMPLEMENTATION.md` (lines 1-50)

### JR-CAS-TOOL-009 — Not-started items: coverage gates per-module, MyPy strict mode, Spider legacy code removal, Docker end-to-end validation.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 183-198)

**Detail**:

CAS-REF-002: Coverage gates (per-module thresholds, P2, S effort). CAS-REF-003: Critical type errors MyPy strict (P2, M effort). CAS-007: Slow tests optimization (P2, M effort, 86-93% achieved Phase 6). CAS-REF-004: Legacy spiral code (16 deprecated methods, P2, M effort). INT-P3-003: Docker Compose E2E validation (P3, S effort). INT-P3-008: pytest.ini.swp and coverage files in gitignore (P3, S effort). INT-P3-010: cascor_snapshots vs snapshots directory confusion (P3, S effort). Shell scripts: 6 Oracle analysis items (P3, M effort). All 🔴 NOT STARTED or 🔵 DEFERRED.

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-TOOL-044 — Remove 9 stale local import traceback statements from cascade_correlation.py by uncomenting top-level import at line 64.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (lines 3568-3580)

**Detail**:

CLN-CC-03: 9 local `import traceback` statements scattered in cascade_correlation.py
across lines 2270, 2804, 3775, 3840 and other files. Consolidate via uncommented
line 64 top-level import. Effort: 30 minutes.

### JR-ML-TOOL-045 — Remove committed .ipynb_checkpoints directories from repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md` (lines 3590-3600)

**Detail**:

CLN-CC-12: Jupyter notebook checkpoint directories committed to repository in
src/cascade_correlation/.ipynb_checkpoints/, src/candidate_unit/, src/
These should be in .gitignore. Effort: 10 minutes.

### JR-ML-TOOL-046 — Setup MCP server for Claude integration: Slack, Gmail, Google Calendar adapters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md` (lines 1-50)

### JR-ML-TOOL-047 — Implement V2 worktree cleanup procedure.

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/WORKTREE_CLEANUP_V2_PLAN.md` (lines 1-100)

**Notes**:

Development workflow optimization.

### JR-ML-TOOL-048 — Phase I (folded into Phase B): Asset cache busting for `websocket_client.js` + `ws_dash_bridge.js`.

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 1080-1099)

**Detail**:

Bump `assets_folder_snapshot` or equivalent query param in Dash config so browsers pick up new JS without hard refresh.
Included as deliverable MVS-FE-16 in Phase B (§6.3), not a standalone phase.
Verify via browser devtools that JS URL includes cache-bust query parameter changing on deploy.

**Design**:

Part of Phase B PR (P6). Ensures stale JS in browser cache doesn't cause mismatches with new protocol.

**Notes**:

Folded into Phase B per R1-05 §6.2. No independent gate. Rollback: revert cache-bust config (5 min TTF).
Priority P3 (folded, low-visibility change).

### JR-CAS-TOOL-010 — Remove legacy stale duplicate file check.py (duplicate of spiral_problem.py).

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 275-279)

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
