# Requirements — DATA

**Area**: data-pipeline — dataset generation, NPZ contracts, ingestion

**Total entries**: 53

**By status**: proposed=40 | shipped=9 | deferred=2 | rejected=2

**By priority**: P0=8 | P1=10 | P2=34 | P3=1

**By owner**: ml=41 | dat=7 | can=4 | rec=1

---

## Requirements from Area: Data, List

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

### JR-ML-DATA-001 — Add missing generator constants: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 433-442)

**Detail**:

| 3 | juniper-data-client | Update `FakeDataClient._GENERATOR_CATALOG` to match server registry                           |

**Notes**:

[v4 brief repaired; was: '8.1 Critical (Fix Immediately)']

### JR-ML-DATA-002 — `FakeDataClient` masks generator name bugs — accepts invalid names

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 479-488)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 387-396)

**Notes**:

[v4 brief repaired; was: '15.2 juniper-data-client']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DATA-003 — **Impact**: `FakeDataClient` masks this — unit tests pass but real server requests fail with 400

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 324-340)

**Detail**:

**Impact**: `FakeDataClient` masks this — unit tests pass but real server requests fail with 400.

**Notes**:

[v3 brief repaired from cited content; was: '6.1 Critical: Generator Name Mismatch (XREPO-01 — confirmed ']

### JR-CAN-DATA-001 — JuniperCanopy ↔ JuniperData integration: replace local client with shared package, mandatory JUNIPER_DATA_URL, schema mismatch fixes

**Status**: shipped  **Priority**: P1  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/history/CANOPY_JUNIPER_DATA_INTEGRATION_PLAN.md` (lines 1-100)

**Detail**:

Critical integration plan Phase 0 (CRITICAL): Replace local client with shared package, make JUNIPER_DATA_URL mandatory, fix schema mismatch. Phase 1 (HIGH): Add to app_config.yaml, API key auth, retry/backoff, NPZ validation. Phase 2 (MEDIUM): Docker compose, constants, health check. Phase 3 (MEDIUM): Dataset selector, management API, multiple generators. Status: Phase 0+1 COMPLETE, 71 new tests, 3,276 passed.

**PRs**: #146

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

### JR-ML-DATA-004 — **Deferred items**: RD-008 (SIM117 test fixes), RD-015 (IPC/ZeroMQ), RD-016 (GPU), RD-017 (continuous profiling)

**Status**: deferred  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 392-402)

**Detail**:

| HTTP status codes → `starlette.status`                            | ✅ Complete                              |

**Notes**:

[v3 brief repaired from cited content; was: '7.3 juniper-data — Constants Refactor ✅; Roadmap Items Defer']

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

### JR-ML-DATA-006 — Task 2 (Dataset)

**Status**: rejected  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 374-381)

### JR-CAN-DATA-002 — CascorIntegration must implement save_snapshot() and load_snapshot() for persistence and recovery

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 96-115)

**Detail**:

CascorIntegration lacks snapshot serialization methods; prevents session recovery and checkpoint-based resumption.
HDF5 snapshot creation exists in main.py but only for demo mode state.

**Notes**:

[v2 ARCH→DATA re-bucket] CAN-CRIT-002; CRITICAL priority post-release item; validation confirmed not implemented.

### JR-ML-DATA-007 — nn-growth-preset-epochs-input (disabled=True; convergence is default)

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 331-381)

**Detail**:

dbc.Card (className="mb-3")

**Notes**:

[v3 brief repaired from cited content; was: '6.1 Card Structure']

### JR-ML-DATA-008 — `_update_topology_store_handler` returns `{}` instead of `dash.no_update` on error — **NOT FIXED** (OI-1)

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 66-82)

**Detail**:

| DATASET_DISPLAY_BUG_ANALYSIS.md               | Dataset tab blank        | RC-1 stale install, RC-2 FakeClient, CF-1..CF-3 | **FIXED** — `get_dataset_data()` added to client (6ed0fda), FakeClient (be17329), version bumped to 0.3.0 (09adb16), `hasattr` guard + broad exception in adapter (line 707)

**Notes**:

[v3 brief repaired from cited content; was: '2.1 Documents in `notes/development/`']

### JR-ML-DATA-009 — Generator names `"circle"`/`"moon"` don't match server's `"circles"` — no `"moon"` generator on server

**Status**: rejected  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 348-359)

**Detail**:

| DC-01 | **High**   | `constants.py`           | 91–92   | Generator names `"circle"`/`"moon"` don't match server's `"circles"` — no `"moon"` generator on server |

**Notes**:

[v4 brief repaired; was: '2.6 juniper-data-client']

### JR-ML-DATA-010 — Phase 3 integration test: a `cascade_add` WebSocket message must trigger a topology broadcast

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 775-794)

**Detail**:

test_websocket_topology_push.py — New integration test

**Notes**:

[v3 brief repaired from cited content; was: 'Phase 3 Tests']

[2026-08-29 brief repaired from cited content; was: '"""cascade_add WebSocket message must trigger topology broadcast."""']

### JR-ML-DATA-011 — 2.4.1 Fix `wait_for_ready()` (`client.py:86`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 204-214)

**Detail**:

**2.4.1 Fix `wait_for_ready()`** (`client.py:86`):

**Notes**:

[v3 brief repaired from cited content; was: '2.4 juniper-cascor-client: Semantic & Coverage Fixes']

### JR-CAN-DATA-003 — Architecture adapter must handle dataset-triggered shape changes: equal-dim (no-op), grow-only (append nodes), shrink (prepend adapter layer)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` (lines 122-126)

**Detail**:

Method: adapt_for_dataset_swap(network, before_dims, after_dims) → ArchChanges. Three cases: (1) equal I/O dims—no work, (2) grow only—append nodes to outermost input/output layer, (3) shrink—prepend new dataset-side adapter layer.

**Notes**:

[v2 ARCH→DATA re-bucket] Returns ArchChanges struct for training history persistence.

### JR-ML-DATA-012 — Canopy metrics normalization must maintain dual-format backward compatibility (nested + flat metric keys)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 1371-1382)

**Detail**:

Phase H: test test_normalize_metric_produces_dual_format before any audit PR.
test_normalize_metric_nested_topology_present, test_normalize_metric_preserves_legacy_timestamp_field.
Write consumer audit doc listing every consumer of nested vs flat keys across canopy frontend.
Explicit recommendation: do NOT remove either format without landing this test first.

**Notes**:

RISK-01. Phase H (Day 12) regression gate. Must not ship Phase B without test in place.

### JR-ML-DATA-013 — DC-04: `FakeDataClient` Masks Generator Name Bugs

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3870-3884)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-DATA-014 — DC-05: `FakeDataClient` Missing Lifecycle Methods

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3887-3901)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-DATA-015 — DEFAULT_MAX_ITERATIONS: Final[int] = 1000

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 114-149)

**Detail**:

MAX_MAX_ITERATIONS: Final[int] = 100000

**Notes**:

[v3 brief repaired from cited content; was: '3.2 New Neural Network Constants']

### JR-ML-DATA-016 — Duplicate pytest configuration in `pyproject.toml` and `pytest.ini`

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 390-397)

**Detail**:

- Duplicate pytest configuration in `pyproject.toml` and `pytest.ini`

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-DATA-017 — `FakeDataClient.close()` doesn't prevent subsequent operations

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 201-209)

**Detail**:

- `FakeDataClient.close()` doesn't prevent subsequent operations

**Notes**:

[v3 brief repaired from cited content; was: 'Low Issues']

### JR-ML-DATA-018 — H-JDC-2: PATCH excluded from retry allowed_methods (`client.py:101`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 187-195)

**Detail**:

**H-JDC-1: Real client HTTP tests missing for 6 methods**:

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-DATA-019 — Hardcoded values refactor (~89 values → `constants.py`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 402-409)

**Detail**:

| Hardcoded values refactor (~89 values → `constants.py`) | ✅ Complete        |

**Notes**:

[v4 brief repaired; was: '7.4 juniper-data-client — Constants Refactor ✅ COMPLETE']

### JR-ML-DATA-020 — Identify from git log

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 305-314)

**Detail**:

| juniper-ml            | v0.2.1, v0.3.0 | Identify from git log |

**Notes**:

[v4 brief repaired; was: '4.1 Create Missing Retroactive Tags']

### JR-ML-DATA-021 — Integration tests (cascor `set_params` via WS)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 248-257)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 203-216)

**Notes**:

[v4 brief repaired; was: '8.2 Phases Still Incomplete']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DATA-022 — JD-PERF-01: Sync `generator.generate()` Blocks Event Loop

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3534-3538)

### JR-ML-DATA-023 — JD-PERF-02: `filter_datasets`/`get_stats` Load ALL Metadata

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3541-3555)

### JR-ML-DATA-024 — JD-PERF-03: `list_versions` Loads All Metadata

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3558-3569)

### JR-ML-DATA-025 — JD-PERF-04: No Connection Pooling for Postgres

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3572-3586)

### JR-ML-DATA-026 — JD-PERF-05: Readiness Probe Filesystem Glob

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3589-3593)

### JR-ML-DATA-027 — JD-SEC-01: Path Traversal via `dataset_id` in Filesystem Paths

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3485-3507)

### JR-ML-DATA-028 — JD-SEC-02: API Key Comparison Not Constant-Time (data)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3510-3518)

### JR-ML-DATA-029 — JD-SEC-03: Rate Limiter Memory Unbounded (data)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3521-3529)

### JR-ML-DATA-030 — `juniper_data_client/__init__.py` — update `__version__` to `"0.4.0"`

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 63-73)

**Detail**:

- `pyproject.toml` — bump version to `0.4.0`

**Notes**:

[v3 brief repaired from cited content; was: '1.3 juniper-data-client: Version Alignment']

### JR-ML-DATA-031 — M-ML-1: `test_worktree_cleanup.py` not run in CI (`ci.yml:109-110`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 67-78)

**Detail**:

**M-ML-1: `test_worktree_cleanup.py` not run in CI** (`ci.yml:109-110`)

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-ML-DATA-032 — Methods catching only `JuniperCascorClientError` (not yet broadened)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 505-522)

**Notes**:

[v3 brief repaired from cited content; was: 'Evidence']

### JR-ML-DATA-033 — NEW (replaces `convergence-enabled-checkbox`)

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 39-56)

**Detail**:

| 3  | Learning Rate         | `nn-learning-rate-input`                | number (float) | 0.01            | RENAMED (was `learning-rate-input`)           |

**Notes**:

[v4 brief repaired; was: '2.1 Neural Network Subsection (12 inputs)']

### JR-CAN-DATA-004 — NPZ dataset loading must validate dtype and shape of all arrays beyond key existence checks

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: can

**Sources**:

- `juniper-canopy/notes/history/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-25.md` (lines 141-154)

**Detail**:

Current implementation only verifies required keys exist; does not validate array dtypes or shapes.
Malformed data causes cryptic errors downstream during training.

**Notes**:

CAN-HIGH-002; HIGH priority post-release item; marked PARTIALLY IMPLEMENTED.

### JR-ML-DATA-034 — `_recv_loop` catches bare `Exception` — swallows programming errors, pending futures time out

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 466-479)

**Detail**:

| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                | 🔴 Open            |

**Notes**:

[v4 brief repaired; was: '15.1 juniper-cascor-client']

### JR-ML-DATA-035 — Remediation Summary

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 95-108)

**Detail**:

1. Create retroactive git tags for v0.2.1 and v0.3.0

### JR-ML-DATA-036 — **Repositories**: juniper-data, juniper-data-client

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 381-388)

**Detail**:

**Repositories**: juniper-data, juniper-data-client

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Generator Name Mismatch']

### JR-ML-DATA-037 — Several `CascorServiceAdapter` methods catch only `JuniperCascorClientError`, which would miss `AttributeError`, `TypeError`, or other…

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 501-505)

**Detail**:

Several `CascorServiceAdapter` methods catch only `JuniperCascorClientError`, which would miss `AttributeError`, `TypeError`, or other unexpected exceptions. This was the original vector for the dataset display bug (RC-2).

**Notes**:

[v3 brief repaired from cited content; was: 'Root Cause']

### JR-ML-DATA-038 — The `JuniperServiceScrapeDown` alert similarly uses `up == 0` to detect

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 483-496)

**Detail**:

| `CascorPendingTasksSaturated` (`alert_rules.yml:1050`) | `juniper_cascor_pending_tasks` | The guard was originally placed because the gauge had not yet been bridged from the cascor coordinator to Pr

**Notes**:

[v3 brief repaired from cited content; was: '7.4 `absent_over_time(...) == 0` inertness guards']

### JR-ML-DATA-039 — **Version**: 0.4.0 | **Python**: ≥3.12 | **Dependencies**: numpy≥1.24, requests≥2.28, urllib3≥2.0

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 206-220)

**Detail**:

| JD-CI-03 | **Low**    | CI workflow and `.pre-commit-config.yaml` headers say version `0.4.0` — stale. |

**Notes**:

[v3 brief repaired from cited content; was: '3.6 CI/CD']

### JR-ML-DATA-040 — XREPO-10: `FakeDataClient` Metadata Schema Diverges from Real Server

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 2712-2726)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-DATA-041 — juniper-cascor-client (Phase 4): add `get_dataset_data()` to `juniper_cascor_client/client.py`

**Status**: proposed  **Priority**: P3  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 348-354)

**Detail**:

| `juniper_cascor_client/client.py` | Add `get_dataset_data()` method |

**Notes**:

[v4 brief repaired; was: '9.3 juniper-cascor-client (Phase 4 only)']

[2026-08-29 brief repaired from cited content; was: '`juniper_cascor_client/client.py`']

### JR-REC-DATA-001 — 3-D irregular-Δt NPZ sequence contract consumption

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md` (lines 1-13)
- `juniper-data-client/juniper_data_client/contract.py` (lines 41-53)

**Detail**:

Consume `{X,y,dt,target_dt,observed_mask}_{train,test,full}` with `dt[:,0]==0`; equities sequences use the stationary `y_reg_*` log-return target (the r²≈−50 raw-price artifact class), never the one-hot direction label.
