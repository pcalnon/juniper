# Requirements — status: rejected

**Total entries**: 17

**By priority**: P0=3 | P1=5 | P2=9

**By category**: SEC=9 | DATA=2 | TRAIN=1 | API=1 | UI=1 | OBS=1 | OPS=1 | ARCH=1

**By owner**: ml=17

---

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

### JR-ML-TRAIN-017 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: VERIFIED + test added.

**Status**: rejected  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 360-378)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: VERIFIED + test added

**Notes**:

[v3 brief repaired from cited content; was: '4.1 CR-023: Whitelist Training Start Parameters']

### JR-ML-SEC-058 — Issue Remediations, Section 18.

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-A-SECURITY-CONCURRENCY-ERROR.md` (lines 463-513)

**Detail**:

#### ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client)

### JR-ML-API-007 — Issue Remediations, Section 21.

**Status**: rejected  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_V6-PARTIAL-AGENT-C-CROSSREPO-CLIENTS-API.md` (lines 692-742)

**Detail**:

#### API-01: Health `status` Value Inconsistent

### JR-ML-SEC-059 — Phase 2 was executed on branch `fix/interface-phase2-security` in cascor and.

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_2026-04-08_JUNIPER-ECOSYSTEM_CANOPY-CASCOR-INTERFACE-ROADMAP.md` (lines 336-360)

**Detail**:

`fix/interface-phase2-docs` in juniper-ml. All four issues were verified

**Notes**:

[v3 brief repaired from cited content; was: '4.0 Phase 2 Execution Results (2026-04-09)']

### JR-ML-DATA-006 — Task 2 (Dataset)

**Status**: rejected  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 374-381)

### JR-ML-SEC-118 — 2A. Validation Loss/Accuracy Overlay Traces.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_DASHBOARD-AUGMENTATION-PLAN.md` (lines 74-88)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-UI-027 — All services handle signals adequately at the application level. The gap is in the orchestration scripts that don't verify shutdown….

**Status**: rejected  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-06_JUNIPER-ECOSYSTEM_MICROSERVICES-STARTUP-CODE-REVIEW.md` (lines 453-468)

**Detail**:

All services handle signals adequately at the application level. The gap is in the orchestration scripts that don't verify shutdown completed.

**Notes**:

[v3 brief repaired from cited content; was: '7.5 Shutdown Signal Handling']

### JR-ML-OBS-060 — Gap**: During rapid cascade additions (e.g., 2+ hidden units in < 5 seconds), intermediate states may be missed. The topology will jump….

**Status**: rejected  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 93-143)

**Detail**:

**Repositories**: juniper-cascor, juniper-canopy

**Notes**:

[v3 brief repaired from cited content; was: '1.2 Network Topology Visualization Issues']

### JR-ML-DATA-009 — Generator names `"circle"`/`"moon"` don't match server's `"circles"` — no `"moon"` generator on server

**Status**: rejected  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:

- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_CODE-AUDIT.md` (lines 348-359)

**Detail**:

| DC-01 | **High**   | `constants.py`           | 91–92   | Generator names `"circle"`/`"moon"` don't match server's `"circles"` — no `"moon"` generator on server |

**Notes**:

[v4 brief repaired; was: '2.6 juniper-data-client']

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

### JR-ML-OPS-004 — Shadow traffic: rejected.

**Status**: rejected  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/JUNIPER_2026-04-12_JUNIPER-ECOSYSTEM_R3-03-LEAN-EXECUTION-DOCUMENT.md` (lines 68-68)

**Notes**:

Settled position C-31 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-188 — The `sync_multi_node_checkboxes` callback handles the bidirectional link:.

**Status**: rejected  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_2026-04-20_JUNIPER-CANOPY_META-PARAMETERS-ENHANCEMENT-PLAN.md` (lines 234-257)

**Detail**:

- Uses `ctx.triggered_id` to determine which checkbox changed

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Cross-Section Checkbox Linking']
