# Requirements — SEC

**Area**: security — authn, authz, secrets, CVEs, hardening

**Total entries**: 246

**By status**: proposed=191 | designed=12 | in-progress=1 | shipped=20 | deferred=13 | rejected=9

**By priority**: P0=58 | P1=67 | P2=111 | P3=10

**By owner**: ml=219 | can=12 | dep=5 | cwk=4 | dat=3 | ccl=2 | dcl=1

---

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

### JR-ML-SEC-002 — missed, (b) part of a not-yet-implemented WebSocket consumption pathway that.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 216-266)

**Detail**:

> - 2026-04-10 second revision: NEW-01 and canopy-set_params markings reverted as

**Notes**:

[v3 brief repaired from cited content; was: '3.5 Phase 1 Deferred Items — STATUS UPDATE (2026-04-10, REVI']

### JR-CWK-SEC-001 — v0.2.0 breaking change: remove hardcoded default auth key ("juniper"), make WORKER_AUTH_KEY environment variable required at worker startup with clear error message if not set.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 27-50)

**Detail**:

Breaking change for 0.1.0→0.2.0 (SemVer minor allowed pre-1.0). Rationale: hardcoded default allowed any network-accessible actor to register workers. Removed the 'juniper' default. WORKER_AUTH_KEY now REQUIRED with validation at startup (clear error if not set). Migration: set WORKER_AUTH_KEY environment variable explicitly before worker startup. For production: source from secret store (Docker secrets, K8s secrets, Vault, SOPS-encrypted env file) rather than plaintext export.

**Notes**:

Related: v0.3.0 renamed WORKER_AUTH_KEY to CASCOR_AUTH_TOKEN and the CLI flag from --api-key to --auth-token. Operators upgrading directly from v0.1.x to v0.3.0 should consult v0.3.0 release notes for mapping.

### JR-ML-SEC-003 — Issue Remediations, Section 4.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-A-SECURITY-CONCURRENCY-ERROR.md` (lines 9-59)

**Detail**:

#### SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel

### JR-ML-SEC-004 — Issue Remediations, Section 7.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 9-59)

**Detail**:

#### CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode

### JR-ML-SEC-005 — Issue Remediations, Section 8.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 127-177)

**Detail**:

#### Phase E: Backpressure Pump Tasks

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

### JR-ML-SEC-011 — `_create_optimizer` references undefined `OptimizerConfig` attributes — crashes on non-default optimizer types.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 648-680)

### JR-ML-SEC-012 — Enhancement**: Instead of scattered `if demo_mode_instance:` checks, use a common backend interface. Both `DemoMode` and….

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 388-438)

**Detail**:

#### Option 1: Runtime Feature Flag (Current Approach, Enhanced)

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Operating Mode Options for Microservices']

### JR-ML-SEC-013 — Floating tags, undefined vars, broken Dockerfiles.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 421-436)

**Notes**:

[v4 brief repaired; was: 'By Category']

### JR-ML-SEC-014 — [ ] WebSocket relay normalized and consumed by dashboard — relay normalization is COMPLETE (P5-RC-14, `cascor_service_adapter.py:222`);….

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 664-714)

**Detail**:

- [x] Demo and service backends return structurally identical data — `demo_backend.apply_params()` standardized to `{ok, data}` envelope to match service backend; other methods already converged (verified 2026-04-10)

**Notes**:

[v3 brief repaired from cited content; was: '6.4 Phase 4 Success Criteria']

### JR-ML-SEC-015 — `_accuracy` assumes one-hot encoded targets — broken for `output_size=1`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 803-821)

### JR-ML-SEC-016 — `ActivationWithDerivative.__setstate__` silently falls back to ReLU for unrecognized activation names.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 746-766)

### JR-ML-SEC-017 — `add_unit` initializes new hidden unit output weights with random values instead of zero.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 718-746)

**Detail**:

Add an `init_output_weights` flag with enumerated values including, but not necessarily limited to, the following: zero and random.
    The flag should be used to determine output node initialization behavior: using `torch.zeros` for the new row(s) vs `toch.randn * 0.1`.
    The flag should have defaults defined in appropriate constants class and local config files.
    Flag default should be accessed by juniper-cascor durring all network initialization locations in the code.
    The flag value

### JR-ML-SEC-018 — All WebSocket endpoints must enforce per-frame size limits: training 4 KB inbound, control 64 KB.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 145-180)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 681-703)

**Detail**:

Cascor training_stream.py: max_size=4096 on receive.
Cascor control_stream.py: maintain 64 KB cap (regression test).
Canopy /ws/training and /ws/control: audit every receive_*() call; add max_size parameter per control table.

**Notes**:

M-SEC-03 (P0). Must precede Phase B per R1-03. Phase B-pre-a (Day 5 of runbook).

### JR-CAN-SEC-001 — API key validation must use hmac.compare_digest() to prevent timing attacks.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 43-43)

**Detail**:

Issue 0.1.2: Replace string 'in' operator with constant-time comparison.
File: src/security.py

### JR-CAN-SEC-002 — CallbackContextAdapter must be thread-safe via contextvars.ContextVar.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 50-50)

**Detail**:

Issue 0.2.1: Replace instance attributes with contextvars.ContextVar to ensure
thread isolation. File: src/frontend/callback_context.py

### JR-ML-SEC-019 — Canopy and Cascor must validate WebSocket Origin header against configurable allowlist; reject null origins and wildcards.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 100-145)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 489-550)

**Detail**:

Cascor: new src/api/websocket/origin.py with validate_origin(ws, allowlist) → bool.
Rules: case-insensitive scheme+host, exact port, strip trailing slash, reject null origin, no wildcard support.
Canopy: mirror implementation in src/backend/ws_security.py (do not cross-import).
Cascor default: [http://localhost:8201, https://localhost:8201, http://127.0.0.1:8201, https://127.0.0.1:8201]
Canopy default: [http://localhost:8050, https://localhost:8050, http://127.0.0.1:8050, https://127.0.0.1:8050]

**Notes**:

M-SEC-01 (canopy), M-SEC-01b (cascor). RISK-15 CSWSH mitigation. Env var JUNIPER_WS_ALLOWED_ORIGINS. Phase B-pre (Day 4).

### JR-ML-SEC-020 — Canopy must implement cookie-session + CSRF first-frame validation before accepting WebSocket connections.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 145-230)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 604-705)

**Detail**:

Canopy src/main.py: add SessionMiddleware with secret_key from env JUNIPER_CANOPY_SESSION_SECRET.
New /api/csrf endpoint returns {"csrf_token": ...}, mints on first request, rotates hourly.
/ws/training and /ws/control: after accept, receive_json(timeout=5.0) for first frame.
First frame must be type="auth" with csrf_token matching session token (hmac.compare_digest).
On failure: close code 4001 "Authentication failed".
Frontend: inject window.__canopy_csrf in layout, send auth frame immediately in websocket_client.js onopen.

**Notes**:

M-SEC-02 (P0). CSWSH second-line defense. Env var JUNIPER_CANOPY_SESSION_SECRET. Phase B-pre (Day 5).

### JR-ML-SEC-021 — `CascadeCorrelationNetwork._roll_sequence_number` stores all discarded values in a list.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 628-648)

### JR-ML-SEC-022 — CasCor distributed training must enforce TLS encryption, worker authentication, multi-tier protection, and comprehensive data validation.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 370-393)

**Detail**:

SR-1/2/3: Protect network, workers, and primary from threats. SR-5: TLS for all in-transit data. SR-6: Worker authentication. SR-7: Data validation.

### JR-ML-SEC-023 — Cassandra referenced in docs but not in compose file.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 328-341)

**Notes**:

[v4 brief repaired; was: '4.3 Issues Identified']

### JR-ML-SEC-024 — Coverage tests bypass actual `fit()` method to avoid timeouts — false coverage confidence.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 969-1002)

**Detail**:

Both Option A and Option B.
    Option A will allow accurate, critical code path coverage checks with non-limiting runtimes.
    Option B will allow the more rigorous checks needed for this application critical code path.

### JR-ML-SEC-025 — Critical deployment gap. The worker is the only distributed component that runs on remote machines but has zero deployment infrastructure:.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 396-414)

**Detail**:

**Critical deployment gap.** The worker is the only distributed component that runs on remote machines but has zero deployment infrastructure:

**Notes**:

[v3 brief repaired from cited content; was: '6.2 juniper-cascor-worker']

### JR-ML-SEC-026 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 115-131)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 287-298)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 350-355)

**Detail**:

**C-JD-1: Version mismatch across 4 files:**

*Merged from 3 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-027 — CSWSH (Cross-Site WebSocket Hijacking) attack must be closed by Origin allowlist + CSRF first-frame.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 450-520)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 489-550)

**Detail**:

First line: M-SEC-01 (Origin allowlist) lands Day 4.
Second line: M-SEC-02 (CSRF first-frame) lands Day 5.
Combined mitigation closes RISK-15 per R0-02 §10.1.
M-SEC-01 alone blocks third-party page from initiating; M-SEC-02 blocks cross-site session hijacking.
Origin validation must happen pre-accept (fail-closed).

**Notes**:

RISK-15 (High). Mandatory close per R1-03 as page-on-call alert, not ticket. Phase B-pre (Days 4-5).

### JR-ML-SEC-028 — Duplicate forward-pass logic in `train_output_layer` vs `forward()`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 821-841)

### JR-ML-SEC-029 — Early stopping patience state not propagated between `grow_network` iterations.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 591-628)

### JR-CAN-SEC-003 — Exception handler must suppress internal details; log full stack server-side only.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 45-45)

**Detail**:

Issue 0.1.3: Return generic message to client, preserve full exception in
server-side logs only. Prevents information disclosure.

### JR-ML-SEC-030 — Global singleton initialization race in `get_api_key_auth()` and `get_rate_limiter()`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 330-362)

### JR-ML-SEC-031 — Hidden unit activation function not wrapped in `ActivationWithDerivative` after HDF5 deserialization.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 700-718)

### JR-ML-SEC-032 — `InlineDataset` allows unbounded array sizes in training start request.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 571-591)

### JR-ML-SEC-033 — juniper-data P0: path traversal fix in csv_import with JUNIPER_DATA_IMPORT_DIR validation.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-DEVELOPMENT-ROADMAP.md` (lines 25-40)

### JR-ML-SEC-034 — Key Categories of Missing Items.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 594-614)

**Detail**:

| Active Bugs (cascor)   | 3         | `TrainingMonitor.current_phase` never updated, uninitialized variable crash    |

### JR-ML-SEC-035 — `_NoOpLogger` session fixture masks logging-related bugs in production code.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1022-1040)

### JR-CAN-SEC-004 — Phase 0 Addendum—Add threading.Lock to TrainingStateMachine.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 258-260)

**Detail**:

HIGH-015: Thread-safe locking required in backend training state machine.
File: src/backend/training_state_machine.py

### JR-CAN-SEC-005 — Phase 0 Pre-Release Security Blockers (6 vulnerabilities).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 30-61)

**Detail**:

0.1.1: Fix path traversal in snapshot endpoints via regex + resolve() check.
0.1.2: Fix timing attack in API key validation via hmac.compare_digest().
0.1.3: Suppress internal exception details; log server-side, return generic message.
0.1.4: Fix rate limiter memory leak with periodic eviction + size cap (10k entries).
0.2.1: Fix thread-unsafe CallbackContextAdapter via contextvars.ContextVar.
0.2.2: Fix threading.Event replacement race with clear() instead of reassign.

### JR-ML-SEC-036 — Phase 1: Critical Fixes (P0) -- COMPLETED.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 714-732)

**Detail**:

**Goal**: Make existing host-mode startup/shutdown reliable.

### JR-ML-SEC-037 — Phase 1: Critical Startup/Shutdown Fixes — ✅ COMPLETE (commit `03aec86`).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 228-243)

**Detail**:

| 1.1  | `wait_for_health()` function — polls `/v1/health` with configurable timeout | ✅ Implemented |

### JR-ML-SEC-038 — `_save_hidden_units` reads activation function name incorrectly from `ActivationWithDerivative` wrapper.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 785-803)

### JR-ML-SEC-039 — `SharedTrainingMemory` shape descriptor only supports tensors up to 2D.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 766-785)

**Detail**:

Immedidately, add validation check rejecting `ndim > 2` with a clear error message.
    - The capacity to allow `ndim > 2` should be documented as an enhancement and added to the development plan.  This feature is required for using some alternate datasets and for the hierarchical network enhancement.

### JR-ML-SEC-040 — Step 6: PR and Worktree Cleanup.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 162-203)

**Detail**:

| `src/frontend/dashboard_manager.py` | UI layout, callback handlers |

### JR-CAN-SEC-006 — Threading.Event replacement race must use clear() instead of reassignment.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 52-53)

**Detail**:

Issue 0.2.2: In demo_mode.py, use _stop.clear() instead of _stop = Event()
to avoid TOCTOU race. File: src/demo_mode.py

### JR-ML-SEC-041 — Three receivers, all SMTP email per OBS-ROUTE-01 (juniper-deploy#60).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 539-558)

**Detail**:

| `default` | `alerts-default@example.com` | **PLACEHOLDER** (`CHANGE_BEFORE_PRODUCTION_USE` flagged) |

**Notes**:

[v3 brief repaired from cited content; was: '9.1 Receivers']

### JR-ML-SEC-042 — Tracks PID in `STARTED_PIDS` array for failure cleanup.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 152-202)

**Detail**:

**Location**: `juniper-ml/util/juniper_plant_all.bash` (319 lines)

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Current State: `juniper_plant_all.bash`']

### JR-ML-SEC-043 — Triple random seeding in `conftest.py` creates confusing test infrastructure.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1076-1176)

### JR-ML-SEC-044 — `unit.get("activation_fn", torch.sigmoid).__name__` returns `"ActivationWithDerivative"` not the underlying function name.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 256-283)

**Detail**:

| CC-01 | **Critical** | `api/websocket/messages.py`       | 72–79   | `create_topology_message()` exists but is never called — topology changes not broadcast via WS                            |

**Notes**:

[v4 brief repaired; was: '2.1 juniper-cascor']

### JR-ML-SEC-045 — `validate_pid()` checks `/proc/<pid>` exists and logs `/proc/<pid>/cmdline`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 208-243)

**Detail**:

**Location**: `juniper-ml/util/juniper_chop_all.bash` (226 lines)

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Current State: `juniper_chop_all.bash`']

### JR-ML-SEC-046 — `validate_training` has no early stopping path when validation data is absent.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 680-700)

### JR-ML-SEC-047 — WebSocket control stream documents `set_params` command but does not implement it.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 227-260)

### JR-ML-SEC-048 — `WebSocketManager` `_active_connections` set lacks explicit async synchronization.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 459-490)

### JR-ML-SEC-049 — **Wire up topology broadcast**: Register a `topology_change` callback in `TrainingLifecycleManager._install_monitoring_hooks()` that calls `.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 523-533)

**Detail**:

1. **Wire up topology broadcast**: Register a `topology_change` callback in `TrainingLifecycleManager._install_monitoring_hooks()` that calls `create_topology_message()` and broadcasts

**Notes**:

[v4 brief repaired; was: '7.1 Immediate (Critical/High)']

### JR-CAN-SEC-007 — API key timing attack must use hmac.compare_digest() for constant-time comparison.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 79-83)

**Detail**:

HIGH-001: Replace simple set membership check with hmac.compare_digest() in both browser CSRF auth and adapter HMAC auth.
R5-01 Section 4.1 mandates this pattern; remediation already correct per analysis.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; reinforced by R5-01 canonical pattern.

### JR-CAN-SEC-008 — Exception handler must use opaque error messages and add CRLF escaping in audit logs.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-12_R5-01-aligned.md` (lines 84-88)

**Detail**:

HIGH-002: Generic error messages + server-side logging per R5-01 Section 4.3 (M-SEC-06).
Add CRLF escaping in audit logs per M-SEC-07 when logs echo client input.

**Notes**:

CODE_REVIEW_ANALYSIS (R5-01 aligned) v0.4.0; shipped with opaque messages pattern.

### JR-CCL-SEC-001 — Implement SOPS configuration (.sops.yaml) and .env.example for secrets management.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-DAT-SEC-002 — Security hardening includes SecurityHeadersMiddleware, RequestBodyLimitMiddleware, CORS, rate limiting, metrics auth, API docs hiding.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 80-85)

**Notes**:

v0.5.0 released as security hardening. Requires explicit CORS_ORIGINS env var for existing deployments.

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

### JR-ML-SEC-052 — [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](../../legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md) — full program tracker (CLOSED 2026-05-03).

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 439-448)

**Detail**:

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — program-close note (PR juniper-ml#192)

**Notes**:

[v3 brief repaired from cited content; was: 'Primary']

### JR-ML-SEC-053 — Issue Remediations, Section 11.

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 9-59)

**Detail**:

#### XREPO-01: Generator Name `"circle"` vs Server's `"circles"`

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

### JR-ML-SEC-058 — Issue Remediations, Section 18.

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-A-SECURITY-CONCURRENCY-ERROR.md` (lines 463-513)

**Detail**:

#### ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client)

### JR-ML-SEC-059 — Phase 2 was executed on branch `fix/interface-phase2-security` in cascor and.

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 336-360)

**Detail**:

`fix/interface-phase2-docs` in juniper-ml. All four issues were verified

**Notes**:

[v3 brief repaired from cited content; was: '4.0 Phase 2 Execution Results (2026-04-09)']

### JR-ML-SEC-060 — [ ] Training Metrics: progress bars show grow iteration and candidate epoch during training.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 314-329)

**Detail**:

- [ ] Training Metrics: progress bars show grow iteration and candidate epoch during training

**Notes**:

[v3 brief repaired from cited content; was: '8.3 Visual Verification Checklist']

### JR-DEP-SEC-001 — Add reverse proxy (Traefik or Caddy) with TLS termination to production profile.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 135-152)

**Detail**:

Phase 2. Proxy service in production profile terminates TLS; services communicate
over plaintext on internal networks. Support both self-signed certificates (dev)
and Let's Encrypt (production). Expose only ports 443 (HTTPS) and optionally 80
(redirect) on host.

### JR-ML-SEC-061 — Add security hardening to check_doc_links.py including universal bounds checking, input validation, and traversal depth limits.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-03-07_JUNIPER-ECOSYSTEM_CROSS-REPO-LINK-RESOLUTION-PROPOSAL.md` (lines 813-920)

**Detail**:

Existing vulnerability: filesystem existence oracle via crafted links like ../../../../etc/passwd.

Required fixes:
1. Universal bounds check - constrain resolved paths to repo/ecosystem root using Path.is_relative_to()
2. Input validation - reject null bytes and absolute paths before path construction
3. Traversal depth limit - reject links with >5 ../ segments
4. Structural validation in skip mode - ensure cross-repo links don't escape target repo

### JR-ML-SEC-062 — Add security logging remediation across Juniper services.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECURITY_LOGGING_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Audit trail and incident response capability.

### JR-ML-SEC-063 — Additional Findings from CasCor Validation.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 54-66)

**Detail**:

1. **`create_topology_message()` is dead code in juniper-cascor** — The message builder exists in `api/websocket/messages.py` (line 35) and is exported in `__init__.py`, but no production code path ever calls it. CasCor only sends `cascade_add` event messages (with event metadata, no topology data).

### JR-ML-SEC-064 — `add_units_as_layer` stores numpy copies of weights in history.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 895-913)

### JR-ML-SEC-065 — All three tasks validated by specialized sub-agents (2026-03-29):.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 354-366)

**Detail**:

- `network_visualizer.py` — uses count-based positioning, not numeric `layer` field

**Notes**:

[v3 brief repaired from cited content; was: '9.4 Files NOT Requiring Modification']

### JR-ML-SEC-066 — Binary: `[[0.0],[1.0]]` -> `[0,1]` (threshold, not argmax).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 302-314)

**Detail**:

| `test_dataset_target_conversion_binary`             | Binary: `[[0.0],[1.0]]` -> `[0,1]` (threshold, not argmax) |

**Notes**:

[v4 brief repaired; was: '8.2 New Tests Required']

### JR-ML-SEC-067 — Canopy WebSocket handlers must enforce 120s idle timeout; close with code 1000 on expiry.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 320-360)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 813-821)

**Detail**:

Wrap receive_text() main loop in asyncio.wait_for(..., timeout=120) on both /ws/training and /ws/control.
On asyncio.TimeoutError, close with 1000 "Normal Closure".
Heartbeat from Phase F will reset timer (safe because it ships later but idle timeout defensible alone).
IMPL-SEC-30 checkpoint.

**Notes**:

IMPL-SEC-30. Idle timeout does not force disconnect during long polling; only closes on true inactivity. Phase B-pre (Day 6).

### JR-ML-SEC-068 — Cascor /ws/control must enforce per-connection command rate limit (leaky bucket, 10/sec).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 210-250)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 786-810)

**Detail**:

New src/api/websocket/rate_limit.py: per-connection leaky bucket, capacity 10, refill 10/sec.
control_stream_handler consumes 1 token per command frame.
On empty bucket: reply {"type": "command_response", "data": {"status": "rate_limited", "retry_after": 0.3}}.
Do NOT close on rate limit; allow client to retry.
One-resume-per-connection micro-control: in training_stream resume handler, record connection-scoped resumed_once.
Second resume frame closes with 1003.

**Notes**:

M-SEC-05 (P1), IMPL-SEC-29. Phase B-pre (Day 6).

### JR-ML-SEC-069 — Cascor must enforce per-IP WebSocket connection limit (default 5) to mitigate connection exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R0-02-SECURITY-HARDENING.md` (lines 180-210)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R1-04-OPERATIONAL-RUNBOOK.md` (lines 774-798)

**Detail**:

WebSocketManager.__init__: self._per_ip_counts: Dict[str, int] = {}, reuse self._lock.
In connect(): before accept(), under async with self._lock: increment and check against ws_max_connections_per_ip.
Increment must happen before accept() (fail-closed).
In disconnect(): decrement in finally block to handle exceptions.
Default 5; configurable via JUNIPER_WS_MAX_CONNECTIONS_PER_IP.
Rejection: code 1013 (Try Again Later).

**Notes**:

M-SEC-04 (P1), IMPL-SEC-05..09. RISK-07 mitigation. Phase B-pre (Day 6).

### JR-DEP-SEC-002 — Complete SOPS secrets management with .env.secrets example and make targets.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 143-152)

**Detail**:

Phase 2. Create .env.secrets.example documenting all secret variables (API keys,
Grafana admin password, Sentry DSNs). Add make secrets-encrypt / make secrets-decrypt
targets wrapping sops commands. Document workflow in docs/SECRETS_GUIDE.md. Ensure CI
does not require decrypted secrets (use ${VAR:-} defaults).

### JR-CAN-SEC-009 — CORS must be restricted to used methods and headers only.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 79-79)

**Detail**:

Issue 1.1.7: Currently allows all methods and headers. Restrict to
actual API usage (GET, POST, OPTIONS; only necessary headers). File: src/main.py

### JR-ML-SEC-070 — D-5: Positive-sense security flag (D-10).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md` (lines 122-123)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-071 — Deterministic IDs with `seed=None` → same ID for different random data → stale cache returns.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 327-348)

**Detail**:

| JD-01 | **High**   | `api/security.py`        | 59      | Non-constant-time API key comparison — timing side-channel attack vector                     |

**Notes**:

[v4 brief repaired; was: '2.5 juniper-data']

### JR-ML-SEC-072 — Excessive f-string tensor interpolation logging in hot paths.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 877-895)

### JR-ML-SEC-073 — Execute comprehensive security audit of Juniper ecosystem with threat modeling and vulnerability assessment.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECURITY_AUDIT_PLAN.md` (lines 1-100)

**Notes**:

Multi-phase security program.

### JR-ML-SEC-074 — Five specialized validation agents independently cross-referenced the v2.0.0 outstanding development items document against 34 source….

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 572-588)

**Detail**:

Five specialized validation agents independently cross-referenced the v2.0.0 outstanding development items document against 34 source documents spanning all 8 Juniper ecosystem repositories. Each agent was assigned a focused subset of source documents to ensure thorough coverage:

**Notes**:

[v3 brief repaired from cited content; was: 'Process']

### JR-ML-SEC-075 — Fix critical security vulnerabilities in CasCor multiprocessing: hardcoded authkey, unpickler, queue sizing, API key comparison.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 809-850)

**Detail**:

Phase 1a: (1) Remove hardcoded PROJECT_MODEL_AUTHKEY, (2) Add RestrictedUnpickler for result queue, (3) Add queue maxsize, (4) Result bounds checking, (5) Use hmac.compare_digest for API key validation.

### JR-ML-SEC-076 — Fix Logic Validation.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 886-895)

**Detail**:

| OI-1 | **VALID** | `dash.no_update` confirmed as correct Dash sentinel; already used 26 times in `dashboard_manager.py` |

### JR-DEP-SEC-003 — Fix shell injection vulnerability in wait_for_services.sh and related scripts.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 264-314)

**Detail**:

check_service() interpolates environment-derived URLs directly into inline Python code.
Malicious JUNIPER_DATA_PORT value can break out and execute arbitrary code. Same pattern found
in health_check.sh (line 59-79) and test_health_enhanced.sh (line 66). Affects wait_for_services.sh,
health_check.sh, test_health_enhanced.sh. Remediation: pass URLs via sys.argv[1] instead of
interpolating into code string. Add PORT numeric validation as defense-in-depth.

### JR-CAN-SEC-010 — get_rate_limiter() must use get_settings() instead of direct access.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 86-86)

**Detail**:

Issue 1.2.4: Inconsistent settings access pattern. Use get_settings() function
for uniform configuration retrieval. File: src/security.py

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-077 — Incomplete implementation of `max_epochs` and `max_iterations` as separate training limits — broken data flow across cascor and canopy.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 60-160)

**Detail**:

Option A, executed as two coordinated PRs (cascor first, then canopy). The canopy side is primarily wiring an existing UI control to an existing param map — the UI already exists and the user already expects it to work. The cascor side is the larger change but follows established patterns for existing fields like `epochs_max`.

Both repos should be updated in the same development cycle to avoid a window where the field exists in cascor but canopy can't drive it.

### JR-ML-SEC-078 — Issue Remediations, Section 19.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 607-657)

**Detail**:

#### CI-01: cascor-client CI Doesn't Test Python 3.14

### JR-ML-SEC-079 — Medium Priority.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 364-375)

**Detail**:

| Task 2 Ph1: Metadata-only graceful handling  | DASHBOARD_AUGMENTATION_PLAN       | Dataset tab metadata-only display for service mode

### JR-ML-SEC-080 — Output weight connection loop — correctly handles all inputs + hidden -> each output.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 213-263)

**Detail**:

**File:** `src/backend/cascor_service_adapter.py`

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Fix']

### JR-ML-SEC-081 — Phase B-pre-a: Origin allowlist, per-IP cap, frame-size cap, audit logger skeleton on `/ws/training`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 334-430)

**Detail**:

Cascor side: Origin validation (M-SEC-01), empty list = fail-closed, case-insensitive host, null origin rejected.
Per-IP connection cap = 5 default, configurable. `_per_ip_counts` dict under lock.
Frame size limit: `max_size=4096` on receive_* calls. Canopy side: duplicate Origin helper (copy, not import).
`Settings.allowed_origins` with localhost/127.0.0.1 defaults. `max_size=4096` on canopy's `/ws/training`.
Audit logger skeleton: `canopy.audit` logger (new module), JSON formatter, TimedRotatingFileHandler daily rotation,
30-day retention, scrub allowlist (no raw payloads). No Prometheus counters yet (land in Phase B).
"One resume per connection" rule: `resume_consumed: bool` per connection, second resume closes 1003.
GAP-WS-19 regression test: `test_close_all_holds_lock`.
Tests: frame size limit 1009, per-IP 6th rejected 1013, origin allowlist matrix, audit log format + rotation, empty allowlist rejects all, second resume closes 1003.
Observability: `canopy_ws_origin_rejected_total{origin_hash, endpoint}` (hashed),
`canopy_ws_oversized_frame_rejected_total{endpoint}`, `canopy_ws_per_ip_cap_rejected_total{endpoint}`,
`canopy_audit_events_total{event_type}`.

**Design**:

Two-PR sequence, cascor→canopy. M-SEC-03 (frame size) + M-SEC-04 (per-IP cap) + M-SEC-07 (audit skeleton).
Origin allowlist on `/ws/training` specifically (read-path). Gates Phase B only.

**Notes**:

Parallel with Phase 0-cascor and A-SDK. Exit gate: empty allowlist = fail-closed (HALT if fail-open).
Rollback: env flags (`JUNIPER_WS_ALLOWED_ORIGINS='*'` ignored by parser; instead use high cap `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=1000`).

### JR-ML-SEC-082 — Phase B-pre-a: Origin on /ws/training, size caps, per-IP cap, idle timeout, audit-logger skeleton.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-93)

**Notes**:

Phase B-pre-a major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-083 — Phase B-pre-b: Origin on /ws/control, cookie session + CSRF first-frame, rate limit, idle timeout, adapter HMAC, audit Prom counters.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R2-02-PHASE-EXECUTION-CONTRACTS.md` (lines 597-699)
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 89-95)

**Detail**:

Cookie session + CSRF (canopy): SessionMiddleware added (or reused if present).
`/api/csrf` endpoint returns CSRF token bound to session (constant-time comparable via `hmac.compare_digest`).
Dash template injects CSRF token via data attribute. `/ws/control` first frame must be `{type: "auth", csrf_token: "..."}` within 5 s;
invalid/absent/expired → close 1008. Cookie: `SameSite=Lax`, `HttpOnly`, `Secure` (prod).
M-SEC-06 opaque close: numeric codes only, no human-readable reasons.
Origin + rate limit (cascor): `/ws/control` validates Origin against `Settings.ws_allowed_origins` (same allowlist as `/ws/training`).
M-SEC-05 single-bucket rate limit: 10 cmd/s leaky bucket per-connection, 11th → close 1013.
M-SEC-10 idle timeout: >120 s idle → close 1008. Settings: `ws_idle_timeout_seconds = 120`.
Adapter auth: canopy computes `csrf_token = hmac(api_key.encode(), b"adapter-ws", sha256).hexdigest()` on connect.
First frame sent: `{type: "auth", csrf_token: <hmac>}`. Cascor derives same + compares with `hmac.compare_digest`.
Uniform code path (no `X-Juniper-Role` header special case).
M-SEC-11 adapter inbound validation: `cascor_service_adapter.py` wraps inbound with Pydantic `CascorServerFrame` (`extra="allow"`).
Malformed → log + increment `canopy_adapter_inbound_invalid_total` + continue.
M-SEC-07 extended log injection: audit logger escapes CRLF + tab in all logged strings (prevents log forgery).
Tests: CSRF required, binds to session constant-time, kill-switch works, Origin rejected, rate limit 11th cmd closes 1013,
idle timeout closes 1008, adapter sends HMAC on connect, inbound malformed logged+counted, CRLF injection escaped,
opaque close codes, session middleware exists, cascor rejects unknown params via extra="forbid".
Observability: `canopy_csrf_validation_failures_total`, `canopy_audit_events_total{event_type="csrf_failure"}`,
`cascor_ws_control_rate_limit_rejected_total`, `cascor_ws_control_idle_timeout_total`, `canopy_adapter_inbound_invalid_total`.

**Design**:

Two-PR sequence (cascor→canopy). M-SEC-01/01b (Origin) + M-SEC-02 (cookie+CSRF) + M-SEC-05 (rate limit) + M-SEC-10 (idle timeout) +
M-SEC-11 (adapter validation) + M-SEC-07 extended (log escaping). Gates Phase D (browser control buttons).
HMAC first-frame auth uniform with existing SDK auth pattern.

**Notes**:

[v3 xround merge: rounds=R2-0,R3-0, n=2] Parallel with Phase B. Entry: Phase B in main. Merge order strict: P8→P9 (P8 must land first, P9's adapter path depends on P8's handler).
Exit: all tests green, manual Origin/CSRF/rate-limit probes work, SessionMiddleware detected, adapter handshake works, 48h soak.
Rollback: `JUNIPER_DISABLE_WS_AUTH=true` (existing flag, 2 min TTF). Dedup candidate with R3-03. / Phase B-pre-b major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-084 — SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 169-184)

### JR-ML-SEC-085 — SEC-02: Rate Limiter Memory Unbounded — DoS Vector.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 187-209)

### JR-ML-SEC-086 — SEC-03: No Per-IP WebSocket Connection Limiting (cascor).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 212-226)

### JR-ML-SEC-087 — SEC-04: Sync Dataset Generation Blocks Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 229-244)

### JR-ML-SEC-088 — SEC-05: Cross-Site WebSocket Hijacking (CSWSH) — No Origin Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 247-261)

### JR-ML-SEC-089 — SEC-06: No Auth on Canopy WS Endpoints.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 264-278)

### JR-ML-SEC-090 — SEC-07: Unvalidated `params` Dict Values in TrainingStartRequest.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 281-295)

### JR-ML-SEC-091 — SEC-10: Sentry `send_default_pii=True` (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 298-312)

### JR-ML-SEC-092 — SEC-11: `pickle.loads` HDF5 Snapshot Data Without RestrictedUnpickler.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 315-337)

### JR-ML-SEC-093 — SEC-12: `/ws` Generic Endpoint Missing Origin/Per-IP Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 340-354)

### JR-ML-SEC-094 — SEC-13: Auth Secrets Exposed via Query Params (`/api/remote/connect`).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 357-379)

### JR-ML-SEC-095 — SEC-14: Internal Exception Messages Leaked to Clients.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 382-396)

### JR-ML-SEC-096 — SEC-15: Cascor Sentry `send_default_pii=True`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 399-413)

### JR-ML-SEC-097 — SEC-16: `/metrics` Prometheus Endpoint Bypasses Auth Middleware.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 416-430)

### JR-ML-SEC-098 — SEC-17: Snapshot `snapshot_id` Path Param Unchecked for Traversal.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 433-447)

### JR-ML-SEC-099 — SEC-18: `_decode_binary_frame` No Bounds Check (cascor-worker).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 450-464)

### JR-ML-SEC-100 — Security remediation for identified vulnerability in PR#40.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PR40_SECURITY_REMEDIATION_PLAN.md` (lines 1-100)

### JR-ML-SEC-101 — Security remediation for juniper-deploy PR#14.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/JUNIPER_DEPLOY_PR14_SECURITY_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Security issue in deployment pipeline.

### JR-ML-SEC-102 — Task 1 (Metrics).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 381-404)

**Detail**:

- Card pattern: `html.Div([html.H5(), html.H2(id=...)])` with flex layout (lines 393-428)

### JR-ML-SEC-103 — The metaparameter update flow works through these stages:.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 146-188)

**Detail**:

**Repositories**: juniper-canopy, juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '1.3 Metaparameter Wiring Gaps']

### JR-ML-SEC-104 — Update TrainingState at each grow iteration boundary:.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 521-534)

**Detail**:

**Effort**: 1-2 days | **Repo**: juniper-cascor

**Notes**:

[v3 brief repaired from cited content; was: '5.3 Grow-Network State Updates']

### JR-ML-SEC-105 — Validate Anthropic API key access patterns across repos; ensure keys not logged or exposed in responses.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md` (lines 1-50)

### JR-ML-SEC-106 — bound 2 user-supporting SLIs (§4.3, §4.4) to 2 of them. Result: ≥8 dashboard.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 176-226)

**Detail**:

**Scope**: Verify all metrics referenced in the R5.1 SLO catalog, `alert_rules.yml`,

**Notes**:

[v3 brief repaired from cited content; was: '4.1 Dimension A — Metrics surface integrity']

### JR-ML-SEC-107 — Background.** The post-METRICS-MON state report (juniper-ml#223 §15) found two clusters of stale panels in….

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 334-370)

**Detail**:

**Severity:** P1 (operational — dashboards mislead operators) · **Owner repo:** juniper-deploy · **Status:** in-flight (sister PR opened 2026-05-06)

**Notes**:

[v3 brief repaired from cited content; was: '3.12 DASHBOARD-STALE-PANELS — 7 stale Grafana panels post au']

### JR-ML-SEC-108 — emits per-worker gauges. `juniper-cascor-worker` itself does not.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 96-146)

**Detail**:

| `/metrics` URL | `http://juniper-cascor:8200/metrics` (compose) |

**Notes**:

[v3 brief repaired from cited content; was: '3.2 juniper-cascor']

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

### JR-ML-SEC-111 — Step 1: Workspace Setup.

**Status**: in-progress  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 48-70)

**Detail**:

- Branch: `main` with committed Phase 5.1/5.2 fixes

### JR-ML-SEC-112 — juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 415-423)

**Detail**:

- juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline

**Notes**:

[v3 brief repaired from cited content; was: 'Cross-repo']

### JR-ML-SEC-113 — Optimizer and `nn.Linear` recreated on every `train_output_layer` call.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 859-877)

### JR-ML-SEC-114 — Per-phase entry / design docs.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 728-740)

**Detail**:

- `juniper-ml/notes/code-review/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`

### JR-ML-SEC-115 — Performance test baselines record data but never assert against regression thresholds.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1058-1076)

### JR-ML-SEC-116 — **R4.6 request-id propagation**: Correctly implemented and well-tested in.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 275-305)

**Detail**:

**Scope**: Verify R2.1 lib adoption, R2.2 WS schema alignment, R4.6

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Dimension C — Shared lib + WS schema + middleware']

### JR-ML-SEC-117 — Per-command HMAC deferred indefinitely.

**Status**: deferred  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 70-70)

**Notes**:

Settled position C-33 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-118 — 2A. Validation Loss/Accuracy Overlay Traces.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 74-88)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-SEC-119 — Issue Remediations, Section 15 — juniper-cascor-client.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 323-373)

**Detail**:

#### CC-01: `_recv_loop` Catches Bare `Exception`

### JR-ML-SEC-120 — Issue Remediations, Section 15 — juniper-cascor-worker.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 561-611)

**Detail**:

#### CW-01: `receive_json()` Doesn't Catch JSONDecodeError

### JR-ML-SEC-121 — Secret name `juniper_data_api_key` (singular) vs env var `juniper_data_api_keys` (plural) — naming inconsistency.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 359-369)

**Detail**:

| DD-01 | **High** | `docker-compose.yml`           | 129, 298, 349, 386 | Cascor and canopy ports bound to `0.0.0.0` — exposed to network (data correctly uses `127.0.0.1`)                |

**Notes**:

[v4 brief repaired; was: '2.7 juniper-deploy']

### JR-ML-SEC-122 — 4 test files with `requires_server` skip marker — need CI integration environment.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 175-193)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 144-158)

**Detail**:

| CLN-CN-01 | **P2**   | `theme-table` CSS class not yet implemented                        | No `.theme-table` in any CSS file — conditional `is_dark` styling used instead    | S      |

**Notes**:

[v4 brief repaired; was: '6.2 juniper-canopy — Code Quality']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-123 — [ ] All tests pass (`pytest -v` or `python3 -m unittest -v`).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 314-327)

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Pre-Release Validation Checklist']

### JR-ML-SEC-124 — A.3 Health Check Scripts.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 846-855)

**Detail**:

| `scripts/health_check.sh`         | juniper-deploy | Full stack health          |

### JR-DEP-SEC-004 — Add container image security scanning (Trivy or Grype) to CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 197-203)

**Detail**:

Phase 4. Add security-scan job to CI using Trivy or Grype. Scan all locally-built
images after build step. Fail on critical/high CVEs; warn on medium. Cache
vulnerability database to reduce CI time.

### JR-CCL-SEC-002 — Add Security section to AGENTS.md documenting SOPS encryption, Gitleaks, Bandit, pip-audit.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 75-76)

**Notes**:

Medium severity: documents security tooling

### JR-ML-SEC-125 — Add `TestBatchOperations` and `TestVersioning` classes in `test_client.py` using `@responses.activate`. Cover:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 188-204)

**Detail**:

**2.3.1 Add PATCH to retry allowed_methods** (`client.py:101`):

**Notes**:

[v3 brief repaired from cited content; was: '2.3 juniper-data-client: Test & Retry Fixes']

### JR-ML-SEC-126 — **AlertManager service missing** from docker-compose.yml but referenced by Prometheus.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 363-374)

**Detail**:

1. **AlertManager service missing** from docker-compose.yml but referenced by Prometheus

**Notes**:

[v4 brief repaired; was: '6.6 High: Docker Infrastructure Gaps (juniper-deploy)']

### JR-ML-SEC-127 — AlertManager service missing from docker-compose.yml — `prometheus.yml:34` references `alertmanager:9093` but no service defined.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 402-419)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 317-330)

**Detail**:

| DEPLOY-01 | **HIGH**   | Docker secret name/path mismatch: `juniper_data_api_key` (singular) vs app expects `juniper_data_api_keys` (plural)              | `docker-compose.yml:499-500` vs service env var

**Notes**:

[v4 brief repaired; was: '13.1 Infrastructure Bugs (Confirmed Still Present)']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-128 — `alertmanager.yml` has empty receiver stubs, no real integrations.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 289-299)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 225-235)

**Detail**:

| 5.1  | Configure AlertManager receivers (Slack/email)   | 🔴 Placeholders only | `alertmanager.yml` has empty receiver stubs, no real integrations |

**Notes**:

[v4 brief repaired; was: '9.2 Phase 5: Observability & Hardening — INCOMPLETE']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-129 — All service files use the same hardening pattern as the existing canopy service:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 54-67)

**Notes**:

[v3 brief repaired from cited content; was: '2.6 Security hardening']

### JR-ML-SEC-130 — Analyze juniper-deploy public release feasibility: dependencies, security, CI/CD readiness.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-09_JUNIPER-DEPLOY_GO-PUBLIC-ANALYSIS.md` (lines 1-50)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-131 — API key in plaintext over HTTP. Default URL is `http://`. No warning when API key is set with non-HTTPS URL.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 62-69)

**Detail**:

| ID        | Severity | File:Line           | Description                                                                                                  |

**Notes**:

[v4 brief repaired; was: '1.2 Security']

### JR-ML-SEC-132 — `AuditLogger` and `WorkerMetrics` counters lack thread-safety.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 523-541)

### JR-ML-SEC-133 — Both are pure client libraries. They provide:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 385-396)

**Detail**:

**No startup/shutdown/orchestration changes needed.** These libraries are consumers, not producers.

**Notes**:

[v3 brief repaired from cited content; was: '6.1 juniper-data-client / juniper-cascor-client']

### JR-ML-SEC-134 — CasCor-Side Validation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 895-907)

**Detail**:

| `cascade_add` correlation hardcoded to 0.0 | Cosmetic — does not affect topology display |

### JR-ML-SEC-135 — CC-15: No TLS/SSL Configuration Support on WS Streams.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3796-3810)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-136 — **CHANGELOG changes**: Add sections for v0.1.1, v0.3.0 covering:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 101-113)

**Detail**:

**CHANGELOG changes**: Add sections for v0.1.1, v0.3.0 covering:

**Notes**:

[v3 brief repaired from cited content; was: '1.5 juniper-cascor-worker: CHANGELOG & Tags']

### JR-ML-SEC-137 — CI-04: Missing Weekly security-scan.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4684-4695)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-138 — CI-SEC-01: No Weekly Security Scan for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4838-4842)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-139 — CI-SEC-02: No Security Scanning in juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 4845-4856)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-140 — **Clean separation of concerns**: Each repository has a single, well-defined responsibility.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 455-464)

**Detail**:

1. **Clean separation of concerns**: Each repository has a single, well-defined responsibility

**Notes**:

[v4 brief repaired; was: '5.1 Strengths']

### JR-DEP-SEC-005 — Close secret-leak detection bypass via Gitleaks path-based allowlisting.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 29-91)

**Detail**:

Gitleaks .gitleaks.toml blanket-allows files matching *.env.enc and *.env.secrets.enc,
creating bypass path for plaintext secrets. Root causes: (1) path-based allowlisting exempts
matching files from all rules, (2) pre-commit hook skipped in CI, (3) weak SOPS metadata validation
(only grep "^sops_" check). Remediation: replace path allowlist with content-based ciphertext regex,
remove CI skip, strengthen to multi-field SOPS validation + ciphertext line check.

### JR-ML-SEC-141 — **Code complexity in Canopy**.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 560-575)

**Detail**:

| Criterion                     | Option 1: Feature Flag | Option 2: Mock Containers | Option 3: Client Fakes | Option 4: VCR         | Option 5: Demo Profile    |

**Notes**:

[v4 brief repaired; was: '3.4 Comparative Evaluation']

### JR-ML-SEC-142 — Code Reference Validation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 880-886)

**Detail**:

Every line number, code snippet, and factual claim about the codebase was verified against the current source files. No shifted, wrong, or missing references found.

### JR-ML-SEC-143 — Cross-references. Runbook §5.3, §7 · OBS-ROUTE-01 PR juniper-deploy#60 (validation evidence in PR body).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (lines 182-207)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

**Notes**:

[v3 brief repaired from cited content; was: '3.5 AMTOOL-CI — `amtool check-config` snap-confinement gap']

### JR-ML-SEC-144 — `dataset_id` concatenated into filesystem paths without sanitization. Path traversal via `../../` in user-supplied `dataset_id`. Documented.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 169-178)

**Detail**:

| ID        | Severity   | File:Line                   | Description

**Notes**:

[v4 brief repaired; was: '3.2 Security']

### JR-ML-SEC-145 — Decision boundary computation runs synchronously in async handler, blocking event loop.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 913-931)

### JR-ML-SEC-146 — DEPLOY-01: Docker Secret Name/Path Mismatch.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md` (lines 3335-3349)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-147 — Dual auth mechanisms — WebSocket endpoints lack middleware-level enforcement and rate limiting.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 294-330)

### JR-ML-SEC-148 — End of deep audit report.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 468-487)

**Detail**:

| 21 | All 5 repos    | Bump AGENTS.md and file header versions to match `pyproject.toml` |

**Notes**:

[v3 brief repaired from cited content; was: '8.4 Low (Backlog)']

### JR-ML-SEC-149 — Estimated Duration**: 8-12 days (original) — **ACTUAL: ~0.5 day (verification + demo gap fix).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 434-451)

**Detail**:

## 5. Phase 3: Metrics Granularity

**Notes**:

[v3 brief repaired from cited content; was: '4.5 Phase 2 Success Criteria']

### JR-ML-SEC-150 — For each application, compile changelog entries from git history:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 273-286)

**Detail**:

| juniper-ml            | Populate [Unreleased], rename to [0.4.0] | Added, Changed, Fixed, CI                                                   |

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Changelog Updates']

### JR-ML-SEC-151 — For juniper-ml, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker:.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 327-337)

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Build & Package Validation (PyPI packages only)']

### JR-ML-SEC-152 — `force_sequential_training` autouse fixture masks all multiprocessing bugs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1002-1022)

### JR-ML-SEC-153 — Future (If Scale Demands).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 735-750)

**Detail**:

1. **Docker Compose demo profile**: Run real CasCor with auto-start training for stakeholder demos.

### JR-ML-SEC-154 — Future enhancements: CAN-000 through CAN-021 (meta param menu, training metrics UI, parameter tuning tab, snapshot capture/replay).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 168-178)
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 280-310)

**Detail**:

| Task 1A: Validation loss/accuracy overlay traces | ❌ NOT STARTED | —       |

**Notes**:

[v3 xrepo fuzzy merge: owners=cas,ml, n=2] [v2 remap: BG→TRAIN]

### JR-DAT-SEC-003 — GitHub Actions versions must be pinned to SHA, not floating refs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 62-63)

**Notes**:

SEC-004 MEDIUM (P2). ci.yml:70,73,84, etc.

### JR-ML-SEC-155 — H-JDP-1: Makefile `prepare-secrets` uses undefined variables (`Makefile:70-72`).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 355-373)

**Detail**:

**H-JDP-1: Makefile `prepare-secrets` uses undefined variables** (`Makefile:70-72`)

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-SEC-156 — Hidden unit forward pass recomputed redundantly every output training epoch.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 841-859)

### JR-ML-SEC-157 — Implement secrets management strategy for Juniper ecosystem (analysis-driven).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECRETS_MANAGEMENT_ANALYSIS.md` (lines 1-100)

### JR-ML-SEC-158 — Integration tests rely on fixed `time.sleep()` for async training synchronization.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 951-969)

### JR-ML-SEC-159 — Issue Remediations, Section 15 — juniper-data-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 506-556)

**Detail**:

#### DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles"

### JR-ML-SEC-160 — Issue Remediations, Section 9.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 343-392)

**Detail**:

#### 5.1: AlertManager Receivers — Placeholders Only

### JR-ML-SEC-161 — Issues Previously Identified and Still Outstanding.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 809-859)

**Detail**:

| response.ok returns bad default | DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN.md Phase 3/5 | OI-1 |

### JR-ML-SEC-162 — `juniper_observability` mounted at app construction): emits.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 68-96)

**Detail**:

| `/metrics` URL | `http://juniper-data:8100/metrics` (compose); `http://localhost:8100/metrics` (local) |

**Notes**:

[v3 brief repaired from cited content; was: '3.1 juniper-data']

### JR-ML-SEC-163 — JUNIPER_WS_ALLOWED_ORIGINS=* explicitly REFUSED by the parser.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 67-67)

**Notes**:

Settled position C-30 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-164 — Locks in lifecycle manager; `_topology_lock` for safe reads during training.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 505-523)

**Notes**:

[v4 brief repaired; was: '6.2 Guardrails']

### JR-ML-SEC-165 — Missing `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` env vars. Canopy deployment won't wire to backend services.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 272-281)

**Detail**:

| DD-K8S-01 | **Medium** | `values.yaml:306`     | Redis `auth.enabled: false` — no authentication.

**Notes**:

[v4 brief repaired; was: '5.2 Kubernetes/Helm Issues']

### JR-ML-SEC-166 — **New file**: `juniper-cascor/scripts/juniper-cascor.service`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 195-245)

**Detail**:

**New file**: `juniper-cascor/scripts/juniper-cascor.service`

**Notes**:

[v3 brief repaired from cited content; was: '5.4 juniper-cascor.service (Step 2.2)']

### JR-ML-SEC-167 — **New file**: `juniper-data/scripts/juniper-data.service`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-SYSTEMD-PHASE2-PLAN.md` (lines 128-178)

**Detail**:

**New file**: `juniper-data/scripts/juniper-data.service`

**Notes**:

[v3 brief repaired from cited content; was: '5.2 juniper-data.service (Step 2.1)']

### JR-ML-SEC-168 — **No docker-integration CI job** — compose config validated but services never built/started/tested. Planned in `CONTAINER_VALIDATION_CI_PLA.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 300-311)

**Detail**:

| TST-01 | **Medium** | No Helm chart tests in CI (`helm lint` only in pre-commit, not CI).                                                                                                         |

**Notes**:

[v4 brief repaired; was: '5.5 Test Coverage Gaps']

### JR-ML-SEC-169 — No integration tests (marker defined, zero tests use it); no binary frame edge case tests.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 132-142)

**Detail**:

| `cli.py`           | 90.70%   | Second SIGINT force-exit path; post-`asyncio.run` log line                                |

**Notes**:

[v4 brief repaired; was: '2.4 Test Coverage Gaps']

### JR-ML-SEC-170 — No validation that TLS cert/key/CA paths exist on disk at startup. Confusing SSL error at connect time instead of clear config error.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 114-123)

**Detail**:

| ID        | Severity | File:Line                  | Description

**Notes**:

[v4 brief repaired; was: '2.2 Security']

### JR-ML-SEC-171 — **Orchestration quality**.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 282-299)

**Notes**:

[v4 brief repaired; was: '2.3 Comparative Evaluation']

### JR-ML-SEC-172 — Orchestration quality**: Excellent. Declarative dependency ordering with health-gated startup (`depends_on: condition: service_healthy`)….

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_MICROSERVICES-ARCHITECTURE-ANALYSIS.md` (lines 116-166)

**Detail**:

#### Option A: Docker Compose (Unified)

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Startup Orchestration Options']

### JR-ML-SEC-173 — Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can es.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 436-444)
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS.md` (lines 347-355)

**Detail**:

| JD-SEC-01 | **HIGH**   | `storage/local_fs.py:52-58` | Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can esc

**Notes**:

[v4 brief repaired; was: '14.1 Security Issues (Confirmed Still Present)']

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-174 — Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 63-63)

**Notes**:

Settled position C-26 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-175 — Phase 3: Worker Deployment & Container Integration — ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 258-270)

**Detail**:

| 3.1  | `juniper-cascor-worker/Dockerfile`                            | ✅ Implemented                                           |

### JR-ML-SEC-176 — Phase 5: Observability & Hardening (P2-P3) -- Medium-Term.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 804-818)

**Detail**:

| 5.1  | Configure AlertManager receivers (Slack/email)   | `juniper-deploy/alertmanager/alertmanager.yml` | Low             |

### JR-ML-SEC-177 — Phase 5: Observability & Hardening — ❌ NOT STARTED.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 285-302)

**Detail**:

| 5.1  | Configure AlertManager receivers                 | ❌      |

### JR-ML-SEC-178 — Phase 5: Quality Improvements (OI-5, OI-6) — COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_NETWORK-TOPOLOGY-DISPLAY-ANALYSIS-AND-FIXES.md` (lines 706-736)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-SEC-179 — Phase B-pre-a (security) — ⚠️ PARTIALLY IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-RECORD.md` (lines 322-330)

### JR-ML-SEC-180 — Phase display may be incorrect — field set at init but not yet updated during training transitions.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 120-134)

**Detail**:

| BUG-CC-01 | **MEDIUM** | `create_topology_message()` not implemented — No topology changes WS   | `src/api/websocket/messages.py:72`                                                | Defined and exported, no production callers. Only used in tests

**Notes**:

[v4 brief repaired; was: '5.1 juniper-cascor']

### JR-ML-SEC-181 — PID validation (check `/proc/<pid>/cmdline`).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 489-504)

**Detail**:

## 9. Development & Tooling Recommendations

**Notes**:

[v4 brief repaired; was: '8.2 Risk Assessment']

### JR-ML-SEC-182 — prometheus container's bridge-network IP must be in.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 496-513)

**Detail**:

| `prometheus` | `localhost:9090` | 15s (global default) | 10s | `/metrics` | `deployment=docker-compose`; per-job `service=prometheus`, `environment=docker` |

**Notes**:

[v3 brief repaired from cited content; was: '8.1 docker-compose (`juniper-deploy/prometheus/prometheus.ym']

### JR-ML-SEC-183 — Prometheus metrics unbounded label cardinality on `endpoint` label.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 362-395)

### JR-ML-SEC-184 — `pyproject.toml:7` — update header comment to `Version: 0.6.0`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 30-41)

**Detail**:

- `juniper_data/__init__.py:17` — change `__version__ = "0.4.2"` to `"0.6.0"`

**Notes**:

[v3 brief repaired from cited content; was: '1.1 juniper-data: Version Synchronization']

### JR-ML-SEC-185 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 330-343)
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 397-411)

**Detail**:

1. Write CHANGELOG v0.3.0 entry (WebSocket rewrite, auth_token rename, TLS support, etc.)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-186 — **Repositories**: juniper-data, juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 217-256)

**Detail**:

**Repositories**: juniper-data, juniper-deploy

**Notes**:

[v3 brief repaired from cited content; was: '1.5 Security Concerns']

### JR-ML-SEC-187 — `RequestBodyLimitMiddleware` relies solely on `Content-Length` header — bypassable with chunked encoding.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 427-459)

### JR-ML-SEC-188 — Requires CASCOR_SERVICE_URL or explicit demo mode.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 265-292)

**Detail**:

- **Strength**: Self-contained, handles env setup

**Notes**:

[v3 brief repaired from cited content; was: '3.4 Individual Application Startup Scripts']

### JR-ML-SEC-189 — `secrets/` directory on disk (gitignored properly).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 281-292)

**Detail**:

| DD-SEC-02 | **Medium** | Cascor port bound to 0.0.0.0 (see DD-DC-04).        |

**Notes**:

[v4 brief repaired; was: '5.3 Security']

### JR-ML-SEC-190 — Security Concerns.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 89-95)

**Detail**:

- `kill_all_pythons.bash`: Dangerous — kills all Python processes system-wide with `sudo kill -9`

### JR-ML-SEC-191 — Serialization & Validation (v3.0.0).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V3-VALIDATED.md` (lines 337-348)

### JR-ML-SEC-192 — **Service file**: `juniper-canopy/scripts/juniper-canopy.service`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 243-265)

**Detail**:

**Service file**: `juniper-canopy/scripts/juniper-canopy.service`

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Current State: systemd (juniper-canopy only)']

### JR-ML-SEC-193 — Service-specific metric inventory (7 metrics):.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 163-193)

**Detail**:

| `/metrics` URL | `http://juniper-canopy:8050/metrics` |

**Notes**:

[v3 brief repaired from cited content; was: '3.3 juniper-canopy']

### JR-ML-SEC-194 — Should be pinned (e.g., `redis:7.4.2-alpine`) for reproducible builds.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 373-390)

**Detail**:

**M-JDP-1: `redis:7-alpine` floating minor version tag**

**Notes**:

[v3 brief repaired from cited content; was: 'Medium Issues']

### JR-CAN-SEC-011 — Snapshot endpoints must sanitize names and confine paths to prevent directory traversal attacks.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` (lines 53-95)

**Detail**:

CRIT-001 vulnerability: /api/v1/snapshots endpoints allow path traversal via ../../ and URL-encoded sequences.
Remediation: Add _sanitize_snapshot_name() with regex ^[a-zA-Z0-9_-]+$; verify resolved path stays within _snapshots_dir.

**Notes**:

CODE_REVIEW_ANALYSIS v0.4.0; path sanitization + path confinement (defense in depth) recommended.

### JR-ML-SEC-195 — **Source-of-truth:** `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_METRICS-STATE-REPORT.md` (lines 257-276)

**Detail**:

`juniper-data/juniper_data/api/observability.py:72` and is **not**

**Notes**:

[v3 brief repaired from cited content; was: '4.4 MetricsAuthMiddleware confinement']

### JR-ML-SEC-196 — State machine enters irrecoverable terminal state after FAILED or COMPLETED without enforced reset.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 186-227)

### JR-ML-SEC-197 — Step 5: Update Plan Document.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CONVERGENCE_UI_FIX_PLAN.md` (lines 154-162)

**Detail**:

Add Phase 5.3 section to `notes/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` documenting:

### JR-ML-SEC-198 — **Strength**: Matches documented security model; prevents container internet access on backend/data.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 73-101)

**Detail**:

**File**: `docker-compose.yml` lines 494-503

**Notes**:

[v3 brief repaired from cited content; was: '1.4 juniper-deploy: Network Isolation']

### JR-ML-SEC-199 — **Strengths of A**: Preserves functionality, standard security pattern, configurable per deployment.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 41-63)

**Detail**:

**Root cause**: `csv_import/generator.py:80-87` passes `file_path` directly to `Path()`.

**Notes**:

[v3 brief repaired from cited content; was: '1.2 juniper-data: CSV Import Path Traversal Fix']

### JR-ML-SEC-200 — Substantial features (systemd support, worker integration, startup/shutdown scripts, worktree cleanup v2) are completely undocumented in….

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 53-67)

**Detail**:

**H-ML-1: CI dependency-docs job references wrong path** (`ci.yml:244`)

**Notes**:

[v3 brief repaired from cited content; was: 'High Issues']

### JR-ML-SEC-201 — `TaskDistributor` dual-path execution is serial, not concurrent.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 931-951)

### JR-ML-SEC-202 — `test_health_enhanced.sh` uses `curl` while other scripts use python3 urllib. Inconsistent dependency.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 311-324)

**Detail**:

| DD-SCR-01 | **Low**  | `test_health_enhanced.sh` uses `curl` while other scripts use python3 urllib. Inconsistent dependency. |

**Notes**:

[v4 brief repaired; was: '5.6 Scripts/Automation']

### JR-ML-SEC-203 — Tests named for `grow_network` testing actually bypass it entirely.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 1040-1058)

### JR-ML-SEC-204 — TOCTOU gap in `_check_stale_workers` between snapshot and deregistration.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 541-571)

### JR-ML-SEC-205 — Unvalidated `params` dict in `TrainingStartRequest` passed as `kwargs` to `network.fit()`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 395-427)

### JR-ML-SEC-206 — V17/V18 cross-repo dispatch token setup: enable inter-repo CI workflows with OIDC trust.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_V17-V18-CROSS-REPO-DISPATCH-TOKEN-SETUP.md` (lines 1-50)

### JR-ML-SEC-207 — **Version**: 0.2.0 (documented in AGENTS.md; no formal release).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CROSS-PROJECT-CODE-REVIEW.md` (lines 343-350)

**Detail**:

- **Version**: 0.2.0 (documented in AGENTS.md; no formal release)

**Notes**:

[v3 brief repaired from cited content; was: 'Overview']

### JR-ML-SEC-208 — **Version**: 0.2.1 | **Stack**: Docker Compose + Helm + Prometheus + Grafana + AlertManager.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 246-260)

**Detail**:

| DC-CI-01 | **Low**  | Security scan installs `.[dev]` (full dev deps) instead of minimal runtime. |

**Notes**:

[v3 brief repaired from cited content; was: '4.4 CI/CD']

### JR-ML-SEC-209 — **Version**: 0.6.0 (unreleased hardcoded-values refactor on main) | **Python**: ≥3.12.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-19_JUNIPER-ECOSYSTEM_DEEP-AUDIT-FIVE-REPOS.md` (lines 142-159)

**Detail**:

| CW-CI-01   | **Low**    | CI tests 3.11-3.13, not 3.14 (Dockerfile uses python:3.14-slim).                                                 |

**Notes**:

[v3 brief repaired from cited content; was: '2.5 CI/CD & Dockerfile']

### JR-ML-SEC-210 — Worker `worker_id` is client-supplied with no server-side validation or uniqueness enforcement.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 490-523)

### JR-ML-SEC-211 — ws_security_enabled=True (positive sense), NOT disable_ws_auth.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 64-64)

**Notes**:

Settled position C-27 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-212 — P3 — Hygiene / future / aspirational.

**Status**: shipped  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_OBSERVABILITY-AUDIT-AND-OUTSTANDING-ISSUES.md` (lines 391-412)

**Detail**:

| **3.1** | juniper-deploy | SLO catalog calibration vs soak-window data | Schedule T+30d agent for 2026-06-02; open calibration PR if observed data warrant

### JR-CWK-SEC-004 — v0.3.0 deprecations: CandidateTrainingWorker (legacy), --api-key CLI flag, CASCOR_API_KEY env var; migrate to CascorWorkerAgent and --auth-token before next major release.

**Status**: shipped  **Priority**: P3  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 113-122)

**Detail**:

CandidateTrainingWorker (legacy): use --legacy to opt in; emits DeprecationWarning. --api-key CLI flag (old flag still parsed, deprecated). CASCOR_API_KEY env var (old var still read as fallback, deprecated). Plan migration to CascorWorkerAgent and --auth-token before next major release.

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-213 — Effort**: 1 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 378-402)

**Detail**:

**Effort**: 1 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.2 CR-026: Server-Assigned Worker IDs']

### JR-ML-SEC-214 — Issue Remediations, Section 10.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-E-DASHBOARD-WS-INFRA-DEPLOY-TESTING.md` (lines 392-428)

**Detail**:

All CasCor enhancement items are feature requests. Brief remediation approaches:

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

### JR-ML-SEC-217 — Worker security modules (mTLS, anomaly detection, rate limiting, audit) are not integrated into runtime.

**Status**: deferred  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (lines 260-294)

### JR-ML-SEC-218 — [ ] `docker compose config` validates for all profiles.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 337-351)

**Detail**:

**Sequence**: After Phase 4 validation

**Notes**:

[v3 brief repaired from cited content; was: '4.4 Docker Validation (juniper-deploy)']

### JR-ML-SEC-219 — Draft release descriptions for each application (templates provided in the code review document). These should be refined and used as….

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_RELEASE-PREPARATION-PLAN.md` (lines 294-305)

**Detail**:

Draft release descriptions for each application (templates provided in the code review document). These should be refined and used as GitHub release notes.

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Release Description Documents']

### JR-CAN-SEC-012 — Exception handling in callback_context must narrow exception types.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 244-244)

**Detail**:

Issue 5.3.3: Bare except: clause catches SystemExit/KeyboardInterrupt.
Narrow to (ValueError, AttributeError, ...); let system signals propagate.
