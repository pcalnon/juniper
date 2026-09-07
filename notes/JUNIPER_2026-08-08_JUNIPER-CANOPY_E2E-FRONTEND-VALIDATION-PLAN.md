# Juniper Canopy — End-to-End Front-End-Driven Validation Plan (Design of Record)

**Project**: Juniper — juniper-canopy end-to-end, front-end-driven validation
**Repository**: pcalnon/juniper-canopy (target, v0.6.0 per `juniper-canopy/pyproject.toml:29`) · pcalnon/juniper-ml (harness / notes)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Fable 5)
**Document Type**: Design of Record / Execution Plan
**Date**: 2026-08-08
**Status**: **DRAFT — AWAITING OWNER APPROVAL**
**Companion document** (per-control click-by-click matrix + numbered workflow scripts, authored in parallel):
`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`
**Grounding audits produced against this plan**:
`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-GROUNDING-AUDIT.md`,
`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-COVERAGE-AUDIT.md`

### Validation record

This revision incorporates the corrections from the two independent audit reports:

| Report | Verdict |
|---|---|
| `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-GROUNDING-AUDIT.md` (grounding / anti-hallucination) | **GO-WITH-FIXES** — 874/890 claims exact; 9 VERIFIED-DRIFT; 7 WRONG (1 blocking) |
| `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-COVERAGE-AUDIT.md` (coverage / consistency) | **MAJOR-GAPS** — 38 findings: 3 blockers (FE-1, FE-2, CN-1), 13 major, 22 minor |

All corrections from both reports' §7 correction lists were applied to this document and the companion
matrix on **2026-08-08**, in this revision. Workflow ids now follow the matrix's `W1 … W14` namespace
(grounding C-1 / coverage CN-1). The document remains `DRAFT — AWAITING OWNER APPROVAL`.

**Citation convention.** Canopy paths are written `juniper-canopy/src/...:<line>`; juniper-ml paths are
repo-relative (`util/isolated_stack.bash:<line>`). Every `file:line` in this document was opened and read
during authoring. Where the drafting brief and the repository disagreed, the repository won and the
discrepancy is recorded in §5 (T-14 … T-17).

---

## 1. Objective & Owner Mandate

### 1.1 Mandate (reproduced faithfully)

> End-to-end validation of juniper-canopy including but not limited to: (a) all top-tab-menu pages open
> and display contents as expected; (b) all documented functionality works correctly from a user's
> front-end-driven perspective; (c) all primary user workflows/use-cases function correctly end-to-end as
> driven by front-end web interactions; (d) specific frequently-broken functionality: network topology
> graph displays; network topology graph interactions; front-page training status indicators; snapshots
> saving/loading/replaying; dataset loading, hot and cold new-dataset migration. The full application must
> be exercised click-by-click. A full test suite must be implemented to exercise the validated features.
> Headless merges of all PRs in this arc are pre-authorized, BUT all execution is gated on the owner's
> approval of this finalized planning documentation.

### 1.2 Approval gate

**No execution begins until the owner approves this document** (§14). That includes Phase 0 — the
`isolated_stack.bash` port fix (§5 T-1) is a real code change and waits with everything else. Until then
this arc produces documents only.

### 1.3 Headless-merge authorization and its limits

Headless merge is pre-authorized **for PRs in this arc**, subject to the standing guardrails, which this
plan does not and cannot relax:

| Limit | Rule |
|---|---|
| Green CI | Every canopy PR must land with canopy CI green, **including the `ui-tests` job** (`juniper-canopy/.github/workflows/ci.yml:353-415`), which the quality gate treats as `failure = error` (`:928-932`). |
| Scope | Only PRs enumerated or derived in §10. A defect discovered outside this arc's scope is filed, not silently fixed. |
| Deploy/PyPI gates | Unchanged and owner-only. This arc cuts no release and approves no `pypi` environment. |
| Test-first fixes | Every Phase-2 fix PR carries the regression test that fails before it and passes after (§6.3). |
| Doc drift | Never silently "corrected" in a code PR; batched into the Phase-4 docs-truth-up PR (§11). |

---

## 2. Scope & Non-Goals

### 2.1 In scope

1. **All 15 visualization tabs** — the roster built by `_all_visualization_tabs()`
   (`juniper-canopy/src/frontend/dashboard_manager.py:2164-2252`) and pinned in
   `juniper-canopy/notes/UI_STANDARDS.md:27-31`: open, render, and behave.
2. **Global chrome** — header/theme toggle, the unified status bar (`dashboard_manager.py:710-820`), the
   WS badge, the welcome modal (`:1859`), sidebar contextual visibility (`:2286-2308`) and per-tab widths
   (`:2315-2322`), the tutorial/context-menu JS surfaces
   (`juniper-canopy/src/frontend/assets/context_menus.js`, `tutorial_walkthrough.js`).
3. **Both run modes, each only where it is the honest lane** — LIVE (service) is primary; DEMO is used
   only for demo-only surfaces (§4.4).
4. **Both models** — `cascor` and `recurrence` (`juniper-canopy/src/model_registry.py:167-193`), with the
   recurrence lane scoped by the decision in §4.5.
5. **The five owner-named fragile areas** — §7.
6. **A durable automated UI suite** — §8.

### 2.2 Non-goals

| Excluded | Rationale |
|---|---|
| Load / performance / soak testing | Different instrumentation and budget; the CI `ui-tests` job carries a ≤5 min wall-clock commitment (`ci.yml:350-351`) this arc must not break. |
| Security penetration testing | Covered by the separate stack security audit line; this arc only *observes* auth posture as a precondition (§5 T-9). |
| Mobile / responsive / accessibility conformance | **Future work** — recommended as a follow-on arc; explicitly not validated here. |
| juniper-deploy Docker-stack validation | Different topology (container DNS names, secrets, compose profiles). This arc validates the on-host isolated stack. |
| cascor / juniper-data internal correctness | Only what the canopy UI surfaces is in scope. A wrong candidate-correlation *number* from cascor is a cascor finding; a *blank panel* is a canopy finding. |
| Numeric-value entry through `dbc.Input(type=number)` via the browser | Blocked under this arc's Playwright harness (§5 T-7); validated through the documented `set_params` doctrine instead. The `dash_duo` / Selenium `send_keys` un-xfail route both shipped xfails name was **evaluated and rejected** for this arc (rationale in T-7). |

---

## 3. Ground-Truth Inventory Summary

### 3.1 Application shape

Dash is mounted into FastAPI as a WSGI sub-app at `/dashboard`
(`juniper-canopy/src/main.py:495`), and `GET /` redirects there (`:520-527`). The layout root is
`DashboardManager._setup_layout` (`dashboard_manager.py:596-598`); the right-hand tab container is
`dbc.Tabs(..., id="visualization-tabs", active_tab="metrics")` (`:1694-1700`). Server-side Dash callbacks
call canopy's **own** API at `http://127.0.0.1:{settings.server.port}` (`:440,:443`) with
`internal_api_headers()` (`juniper-canopy/src/frontend/internal_api.py:63-79`), which always carries the
internal-request token so those self-calls bypass canopy's rate limiter.

### 3.2 The 15 tabs

| # | `tab_id` | Label | Renderer | Cascade-only? |
|---|---|---|---|---|
| 1 | `metrics` | Training Metrics | `components/metrics_panel.py` (2288 ln) | no |
| 2 | `candidates` | Candidate Metrics | `components/candidate_metrics_panel.py` | **yes** |
| 3 | `topology` | Network Topology | `components/network_visualizer.py` (1770 ln) | **yes** |
| 4 | `evolution` | Network Evolution | `components/network_evolution.py` | **yes** |
| 5 | `boundaries` | Decision Boundary | `components/decision_boundary.py` | **yes** |
| 6 | `dataset` | Dataset View | `components/dataset_plotter.py` (1355 ln) | no |
| 7 | `workers` | Workers | `components/worker_panel.py` | **yes** |
| 8 | `parameters` | Parameters | `components/parameters_panel.py` | no |
| 9 | `snapshots` | Snapshots | `components/hdf5_snapshots_panel.py` (1410 ln) | no |
| 10 | `replay` | Replay | `components/replay_player_panel.py` | no |
| 11 | `network-editor` | Network Editor | `components/network_editor_panel.py` | no |
| 12 | `redis` | Redis | `components/redis_panel.py` | no |
| 13 | `cassandra` | Cassandra | `components/cassandra_panel.py` | no |
| 14 | `tutorial` | Tutorial | `components/tutorial_panel.py` | no |
| 15 | `about` | About | `components/about_panel.py` | no |

Order and ids: `dashboard_manager.py:2176-2252`. The five cascade-only ids are
`_CASCADE_ONLY_TAB_IDS` (`:387`), filtered by `_visible_tabs` (`:2254-2268`) and applied by the
`suppress_cascade_tabs` callback (`:2353-2360`); the status-bar hidden-units segment is hidden in the same
family (`:2362-2370`).

### 3.3 Primary user workflows (validated end-to-end in Phase 1)

W1 Cold-start cascor training, end to end (first visit → welcome modal → Start → observe) · W2
Pause / Resume / Stop / Reset control matrix (incl. the Reset → Start precondition path, §5 T-6) ·
W3 Parameter apply round-trip · W4 Topology exploration (layout / 2D-3D / weight-matrix / depth /
select) · W5 Snapshot lifecycle (create → view → restore → Network Editor unlock → replay transport →
resume/retrain) · W6 Dataset COLD migration (stage → banner → restart-confirm → restart) · W7 Dataset
HOT migration (experimental flag → live-switch modal → swap) · W8 Model switch cascor ⇄ recurrence
(selection, gating, tab suppression) · W9 DEMO-lane dataset generate / upload / URL import (per §5
T-11) · W10 Metrics layout save/load/delete · W11 In-metrics replay controls · W12 Evolution +
Boundaries during a live run · W13 Ancillary tabs + chrome smoke (welcome modal, 15-tab walk, theme,
tutorial, about) · W14 Upstream-degradation induction (stop/restart cascor mid-run, §7.3).
**Workflow ids are the companion matrix's (`W1 … W14`, its §4 scripts are canonical); this list is a
summary, not a second numbering.** Per-control detail lives in the **companion matrix document**.

### 3.4 Canopy `/api/*` route surface (registered)

`GET /api/status` (status bar, 1 s tick) · `GET /api/state` · `GET /api/stream_health` (WS badge) ·
`GET /api/topology`, `/api/topology/raw` · `GET /api/dataset`, `/api/dataset/generators` ·
`POST /api/dataset/generate|import-file|import-url` · `POST /api/stage_dataset`,
`DELETE /api/cancel_pending_dataset` · `POST|DELETE /api/live_dataset_swap` ·
`GET|POST /api/admin/experimental_functions` · `GET /api/history/dataset_swaps` ·
`GET /api/snapshots/{id}/history/dataset_swaps` (per-snapshot swap history, `main.py:4032`; fetched by
`dashboard_manager.py:5686` into `loaded-snapshot-swap-events-store` for the replay swap-events graph) ·
`POST /api/model/select` · `POST /api/set_params` · `POST /api/train/{start,pause,resume,stop,reset,restart}`,
`GET /api/train/status` · `GET|POST /api/v1/snapshots`, `GET /api/v1/snapshots/{id}`,
`/api/v1/snapshots/history`, `POST /api/v1/snapshots/{id}/{restore,replay,resume,retrain}`,
`POST /api/v1/snapshots/{id}/replay/control` · `POST|DELETE /api/v1/network/hidden-units[/{idx}]` ·
`GET /api/v1/workers/{list,stats}` · `GET /api/v1/redis/*`, `/api/v1/cassandra/*` ·
`GET|POST|DELETE /api/v1/metrics/layouts[/{name}]` · `POST /api/ws_latency` (browser-originated
latency-sample sink, `main.py:4225`, POSTed by `assets/ws_latency.js:47-50` on a 60 s cadence —
expected background traffic, not console/network noise). All enumerated from the
`@app.<verb>("/api/...")` decorators in `juniper-canopy/src/main.py`. `/api/remote/*` (five routes:
`status,connect,disconnect,start_workers,stop_workers`) is **registered but has no frontend caller** —
out of scope for a UI-coverage matrix.

---

## 4. Environment & Stack Strategy

### 4.1 The isolated stack is the primary surface

`util/isolated_stack.bash` brings up a trio that never touches operator ports: juniper-data on **8101**
(dedicated `python3.14` venv), juniper-cascor on **8202** (`JuniperCascor1`), juniper-canopy on **8051**
(`JuniperCanopy1`, `JUNIPER_CANOPY_DEMO_MODE=0`) — `util/isolated_stack.bash:54-77,:241-259`. The
control-WS origin pair is set on both ends to `http://127.0.0.1:8051`
(`:229` cascor allowlist, `:255` canopy origin), the resolution of the "403 mystery" recorded in
`notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md:121-133`.

### 4.2 Phase-0 blocker: the canopy port is never applied (confirmed defect)

`util/isolated_stack.bash:252` exports `JUNIPER_CANOPY_PORT="${CANOPY_PORT}"`. Canopy's `Settings` uses
`env_prefix="JUNIPER_CANOPY_"` with `env_nested_delimiter="__"` and `extra="ignore"`
(`juniper-canopy/src/settings.py:188-195`); the port lives at `ServerSettings.port` (`:118-122`, default
**8050**) and is read as `settings.server.port` by the entrypoint (`juniper-canopy/src/main.py:4247-4248`).
`JUNIPER_CANOPY_PORT` appears **nowhere** in the canopy repository (verified by repo-wide grep), so it is
silently dropped and canopy binds **8050 — the operator port**, fails the 8051 health gate
(`util/isolated_stack.bash:259`), and `do_up` tears the partial trio down (`:294-302`). The same wrong
variable is documented in the checklist (`…ISOLATED-STACK-E2E-CHECKLIST.md:106`) and *asserted* by the
harness tests (`tests/test_isolated_stack_script.py:348-349,:609`), so the tests currently pin the bug.

Second-order consequence: `DashboardManager._api_base_url` is built from `settings.server.port`
(`dashboard_manager.py:440,:443`), so the fix also repoints every server-side self-call at the isolated
port instead of 8050.

**Phase-0 fix**: export `JUNIPER_CANOPY_SERVER__PORT` (and `JUNIPER_CANOPY_SERVER__HOST`), correct the
checklist §3.3, and invert the test assertions to the nested names. In-repo corroboration that the
nested form is correct: canopy's **own** UI conftest already uses it —
`juniper-canopy/src/tests/ui/conftest.py:40-41` sets `JUNIPER_CANOPY_SERVER__HOST` /
`JUNIPER_CANOPY_SERVER__PORT` for the Popen'd app. (For contrast, juniper-recurrence
uses a **flat** `port` field under `env_prefix="JUNIPER_RECURRENCE_"` —
`juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py:128,:152` — so
`JUNIPER_RECURRENCE_PORT` *would* work; the nesting trap is canopy-specific.)

### 4.3 Honest health-gate protocol (mandatory for every live-lane run)

HTTP 200 on `/v1/health` is **not** proof of a live stack. When cascor is unreachable at startup canopy
logs a warning and silently re-creates a demo backend (`juniper-canopy/src/main.py:322-337`), after which
`/v1/health` still returns `status: "ok"` — the truth is in the body (`:1059-1069`). The gate is:

```
GET http://127.0.0.1:8051/v1/health  →  status == "ok"
                                        AND demo_mode  == false      # main.py:1068
                                        AND juniper_data_available == true   # main.py:1069
```

Plus two preflights: (i) `juniper-cascor-client >= 0.7.0` present in `JuniperCanopy1` — the floor declared
at `juniper-canopy/pyproject.toml:162` (observed today: `juniper_cascor_client-0.7.0.dist-info` in
`/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/`) — because the topology transform
imports it (§7.1); (ii) `make check-env` in the canopy repo (`juniper-canopy/Makefile:31-32`) to assert
the env satisfies every `juniper-*` floor.

### 4.4 Two lanes

| | **LIVE lane (primary)** | **DEMO lane (narrow)** |
|---|---|---|
| Stack | isolated trio, data 8101 / cascor 8202 / canopy 8051 | single canopy process, `JUNIPER_CANOPY_DEMO_MODE=1` |
| Gate | §4.3 (`demo_mode == false`) | `demo_mode == true` |
| Covers | W1…W8, W10–W14 (plus W9's live-lane 400-mirror step), all five fragile areas, both topology sources, real snapshots, real staging/restart/live-swap | only the surfaces that are **demo-only by design**: the Dataset View **Generate** modal (`main.py:1414-1418`, 400 in service mode), **Import File** (`:1478-1482`) and **Import URL** (`:1572`) which are likewise demo-gated, the fabricated snapshot list (`:1818-1828`, `_demo_snapshots` session store `:1892-1899`), and the welcome modal / theme / static tabs where mode is irrelevant |
| Automation | new `ui_live` marker, local runner only (§8) | existing `@pytest.mark.ui` suite + CI `ui-tests` job |

Rule: **a surface is validated in the lane where it is honest.** Nothing owner-named as fragile is signed
off from the demo lane alone.

### 4.5 Model matrix — decision on recurrence

`util/isolated_stack.bash` starts **data, cascor, canopy only**; there is no juniper-recurrence leg
(verified: no `recurrence` token in the script). Canopy routes to recurrence only when
`recurrence_service_url` is configured (`juniper-canopy/src/settings.py:261`,
`src/backend/__init__.py:111-134`); with it unset, `_selection_targets_recurrence` returns False
(`main.py:3498-3510`) and the backend swap is a **silent no-op** while
`model_is_trainable("recurrence")` still returns True, because it keys only off the registry's hardcoded
`status="live"` (`model_registry.py:188`, `:232-247`) — so Start is *not* disabled and the one-shot
suppression never engages. (The docstring at `src/backend/__init__.py:116-118` asserts the picker gates an
unconfigured recurrence model out; `model_is_trainable` does not implement that — see F-CANDIDATE in §7.5.)

**Decision (owner may override at approval):**

- **Default**: Phase 0 adds an **optional fourth leg** to `isolated_stack.bash` behind `--with-recurrence`,
  launching juniper-recurrence on **8211** (`JUNIPER_RECURRENCE_PORT=8211`, flat prefix per §4.2) and
  exporting `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=http://127.0.0.1:8211` for canopy. With the leg up, W8
  is validated end-to-end (real one-shot fit, real suppression, real regression card
  `metrics_panel.py:1666-1716`). **8211 occupancy pre-check (mandatory in PR-M2)**: 8211 is precisely the
  host port a running juniper-deploy stack publishes for recurrence —
  `juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py:152` reads
  `port: int = 8210  # container port; deploy maps host 8211 -> ctr 8210` — so the fourth leg must check
  8211 for a live listener before `--up` (mirroring the §12 8050/8051 mitigation) and abort loudly on a
  collision.
- **Fallback** (if the owner declines the fourth leg): every recurrence matrix row (all of W8) is
  annotated `N-A (no recurrence service)` rather than PASS — an honest reduction the §9 vocabulary
  already supports. **The previously drafted self-URL trick is REJECTED on the record** (coverage audit
  FE-4): pointing `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` at the stack's own canopy port is not
  cosmetic — `POST /api/model/select` re-creates the **process-global backend** as a real
  `RecurrenceServiceAdapter` aimed at a service that does not implement the recurrence API
  (`src/backend/__init__.py:130-134`), and no validator rejects a self-URL
  (`_check_recurrence_service_url`, `settings.py:509-525`, only resolves a shared alias) — so
  status/metrics/topology polling would break broadly, not yield a clean "selection-UI-only" lane. If a
  drivable stand-in is ever wanted without PR-M2, the honest option is a ~40-line stub recurrence
  service under `util/ad-hoc/` answering `/v1/health/ready` + `/v1/train` + `/v1/predict`.

---

## 5. Constraints & Traps Register

| ID | Statement | Citation | Consequence for validation |
|---|---|---|---|
| **T-1** | `isolated_stack.bash` exports `JUNIPER_CANOPY_PORT`, which canopy ignores (`extra="ignore"`); canopy binds 8050. | `util/isolated_stack.bash:252`; `juniper-canopy/src/settings.py:118-122,:188-195`; `src/main.py:4247-4248` | Live lane cannot start until Phase 0. Blocks everything. |
| **T-2** | Cascor unreachable at boot → canopy silently becomes a demo backend; `/v1/health` still `"ok"`. | `src/main.py:322-337`, `:1059-1069` | Every live gate must assert `demo_mode == false`, never HTTP 200 alone. A false-live run invalidates the whole session. |
| **T-3** | Topology REST handler passes *graph-format* payloads through without importing the adapter, but the *weight-oriented* branch still does `from backend.cascor_service_adapter import CascorServiceAdapter`. That module hard-imports `juniper_cascor_client`. | `dashboard_manager.py:6447-6462` | The historical "permanently empty topology" class is fixed for demo-format payloads and **remains live for the real cascor payload** in a client-less env. Preflight the 0.7.0 floor (§4.3). |
| **T-4** | The topology WS fast path also imports the adapter unconditionally when a `ws-topology-buffer` frame arrives. | `dashboard_manager.py:3741-3754` | Same import exposure on the push path; a client-less env fails on cascade-add, not only on poll. |
| **T-5** | Every failure path in the topology/metrics handlers returns `dash.no_update` (last-known-good), never an error surface. | `dashboard_manager.py:6427-6443` | A broken panel looks *stale*, not *failed*. Validation must diff against a known-changing topology, not just "something is drawn". |
| **T-6** | `POST /api/train/start` defaults `reset=False`; START from a `COMPLETED` FSM is refused with 409. | `src/main.py:3247`, `:3272` (409); checklist §6 | Every start-based workflow needs a Reset → Start precondition, mirroring `src/tests/ui/test_train_after_reset.py`. |
| **T-7** | Playwright cannot drive `dbc.Input(type=number)` into Dash `State`; both proofs are **strict** xfails. | `src/tests/ui/test_apply_button_flow.py:62-71`; `src/tests/ui/test_l3_native_setter_poc.py:46-48` | Numeric params are validated by the `POST /api/set_params` → assert-DOM doctrine (`src/tests/ui/test_param_roundtrip_visible.py:66-92`). An XPASS is a *canary*, not a regression. **Un-xfail path, evaluated and REJECTED for this arc**: both shipped xfail reasons name a concrete route out — `dash[testing]` / `dash_duo` (Selenium `send_keys`), which needs selenium + chromedriver + multiprocess added to the env. Rejected on the record because it adds a second browser-automation stack beside Playwright, plus env weight, for one input class the doctrine already covers; Phase 3 may revisit it if the granular-MODIFY limit (T-22) is promoted to P1 — `dash_duo` is the only named route that could drive those modal-scoped fields. |
| **T-8** | Canopy's rate limiter defaults **off**; server-side self-calls are exempt regardless via the internal-request token. | `src/settings.py:317-318`; `src/frontend/internal_api.py:63-79` | The historical apply-params 429 class is only reachable when an operator enables the limiter *and* the call is browser-originated (the clientside REST fallback). Record the limiter state in every evidence header. |
| **T-9** | Browser-control auth (Origin + CSRF) on `/api/train/*` engages **only when `CANOPY_API_KEY` is configured**; with no key, `auth.enabled` is False and the surface is open. `/api/set_params` is not in the gated set. | `src/security.py:47-59`, `:261-268`, `require_browser_control_auth` acceptance rules; gated routes `src/main.py:3246,3278,3299,3320,3341,3362,3426`; `/api/set_params` `:3640` | The isolated stack sets no key, so the live browser lane is unblocked. A deploy-stack run would additionally need Origin+CSRF. Both postures must be stated in the evidence header. |
| **T-10** | Replay / resume / retrain require a live cascor; demo returns **501**. | `src/main.py:2553-2563` | Fragile-area 4 (snapshots) is a LIVE-lane-only sign-off beyond `restore`. |
| **T-11** | Dataset **Generate**, **Import File**, and **Import URL** are demo-only (400 in service mode). URL import is additionally off by default. | `src/main.py:1417-1418`, `:1478-1482`, `:1572`; `src/settings.py:396` | These three Dataset-View controls are DEMO-lane rows; in the live lane the 400 **is** the expected result (the matrix's live-lane mirror arms), so the observed 400 scores `PASS` on those rows — never FAIL. |
| **T-12** | `swap-restore-pre-btn` / `swap-restore-post-btn` are rendered with **no callback anywhere**. | `src/frontend/components/hdf5_snapshots_panel.py:709,:720` (repo-wide grep finds no other reference) | Expected-dead. Matrix automation class `DEAD-EXPECTED` (terminal status `DEAD-CONFIRMED`, §9); a Phase-2 decision is required: wire or remove (§10 PR-C6). |
| **T-13** | Sidebar sections are hidden via `{"display": "none"}`, never unmounted; all 15 tab panels exist eagerly in the DOM. | `dashboard_manager.py:2286-2308`; `:2176-2252` | Assertions must be **visibility**-based (`to_be_visible`), never presence-based; tab "opens" must assert rendered content, not element existence. |
| **T-14** | *Brief-vs-repo discrepancy.* The snapshot context-menu asset is at `src/frontend/assets/snapshot_context_menu.js` (195 ln), not `src/assets/`. `src/assets/` holds images only. | directory listings; `src/frontend/assets/snapshot_context_menu.js:6-7,:33-34,:172-182` | Cite the real path. The right-click menu maps to the same `restore/replay/...` ops. |
| **T-15** | *Brief-vs-repo discrepancy.* `docs/USER_MANUAL.md` contains **no** "C++ prototype" or `JuniperPython` text, and no Redis/Cassandra "Planned" claim. Those live elsewhere. | `docs/demo/DEMO_MODE_QUICK_START.md:65`; `docs/demo/DEMO_MODE_MANUAL.md:27,:38`; `docs/cassandra/CASSANDRA_INTEGRATION_QUICK_START.md:81,:147`; `docs/testing/TESTING_QUICK_START.md:12,:88,:92`; `docs/REFERENCE.md:170-171` | The Phase-4 docs-truth-up scope is wider than USER_MANUAL alone (§11). |
| **T-16** | *Brief-vs-repo discrepancy.* Recurrence's registry `status` is hardcoded `"live"`, so the D8 train-gate does **not** disable Start for it even with no recurrence service configured. | `src/model_registry.py:188`, `:232-247`; `dashboard_manager.py:6749-6752` | Drives the §4.5 decision; also a candidate finding (§7.5). |
| **T-17** | *Brief-vs-repo precision.* `/ws/training` idle timeout is a real setting (`120`), and the flap history is documented in-code. | `src/settings.py:166`; `src/main.py:147`, `:702`, `:719-738` | Any workflow idling >120 s on a live socket must expect a Connected→Reconnecting badge transition and not score it FAIL. |
| **T-18** | The WS badge has **two** inputs — browser-socket peek + upstream `/api/stream_health` — precisely because a green badge once masked a dead relay for 12+ hours. | `dashboard_manager.py:3477-3487`, `:3521-3528`, `:3532-3538`; `src/frontend/components/connection_indicator.py:34-48,:55-60` | Badge assertions must cover the degraded-downgrade path, not just "green". |
| **T-19** | A model swap does **not** reset `active_tab`; there are **three** `active_tab` writers (`dashboard_manager.py:3278` tutorial trigger, `:3300` layout-state restore, `hdf5_snapshots_panel.py:1230` snapshot replay). The "exactly two" text at `dashboard_manager.py:2259-2261` is a **stale docstring** — matrix DIVERGENCE D-1, doc-only. | `dashboard_manager.py:3278,:3300`; `hdf5_snapshots_panel.py:1230`; stale docstring `dashboard_manager.py:2259-2261` | Swapping to a one-shot model while a cascade-only tab is active is an orphaned-active-tab probe the matrix must include. |
| **T-20** | UI tests are excluded from the default pytest run and must run in their own process (event-loop leak). | `juniper-canopy/pyproject.toml:346-352`; `juniper-canopy/Makefile:20-26` | The new live suite must inherit the split-invocation pattern; it must not be pulled into the default `pytest` run. |
| **T-21** | The five training-control buttons default to the **`/ws/control` WebSocket transport**: `enable_ws_control_buttons` defaults **`True`** (`juniper-canopy/src/settings.py:349`), registering the clientside WS-with-REST-fallback callback (`dashboard_manager.py:4125-4149`; JS body `:110-260`). The in-code comment at `dashboard_manager.py:4122-4124` claiming the flag is "off (default)" is **stale** — a **finding-candidate for Phase 1** (comment drift). | `src/settings.py:349`; `dashboard_manager.py:4122-4124,:4125-4149`; `assets/websocket_client.js:517` | Button rows/steps must be transport-aware: primary verification is a WS frame on `/ws/control`; `POST /api/train/<cmd>` fires only as the automatic fallback (or under the non-default server-side registration). A NET-only assertion FAILs on a working app. |
| **T-22** | The restart modal's **granular-MODIFY** capability (N3b) has **no automatable drive path**: 10 of its 11 fields are `dbc.Input(type="number")` (`dashboard_manager.py:5157-5162,:5185-5190`), so the T-7 numeric wall applies, and — unlike the sidebar params — there is **no API bypass**: the fields are seeded on modal open and consumed only by the Confirm handler's diff-against-baseline (`:5058-5079`); no route writes those modal-scoped Dash `State`s. A **finding-candidate for Phase 1**. | `dashboard_manager.py:401-415` (field maps), `:5149-5174,:5176-5204` (builders), `:5058-5079` | The seeding half is testable (set params → open modal → assert seeded values); the **modify** half is MANUAL-only (human keystrokes) — recorded as a known coverage limit, per matrix §2.10 + W6. |

---

## 6. Validation Phases

### 6.1 Phase 0 — Prerequisites & stack fixes

**Entry**: owner approval of this document.
**Steps**

1. **PR-M1 (juniper-ml)** — fix `util/isolated_stack.bash:252` to export
   `JUNIPER_CANOPY_SERVER__PORT` (+ `…SERVER__HOST`); correct
   `notes/JUNIPER_2026-07-21_…ISOLATED-STACK-E2E-CHECKLIST.md:106`; invert **all three** test
   occurrences to the nested names — `tests/test_isolated_stack_script.py:348-349`, `:609`, **and**
   `:425` (the `printf 'JUNIPER_CANOPY_PORT=%s\n' "${{JUNIPER_CANOPY_PORT-}}"` line inside the
   launch-stub heredoc, which must change in the same PR or the `:609` assertion asserts against a
   variable the stub no longer prints) — and add a **negative** assertion
   that the flat `JUNIPER_CANOPY_PORT=` form is absent (so the bug cannot re-land).
2. **PR-M2 (juniper-ml, conditional on §4.5)** — `--with-recurrence` fourth leg on 8211 + canopy
   `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` wiring + the **8211 occupancy pre-check** (§4.5 — juniper-deploy
   maps host 8211 → recurrence container 8210, so a live compose stack can already hold it) + `--dry-run`
   and teardown coverage in the same test file.
3. **Env preflight** — `make check-env` in canopy (`Makefile:31-32`); confirm
   `juniper-cascor-client>=0.7.0` in `JuniperCanopy1`; confirm no operator canopy is holding 8050/8051.
4. **Bring-up rehearsal** — `util/isolated_stack.bash --dry-run --up`, then `--up`, then the §4.3 honest
   gate, then `--down` and a port re-check.

**Exit**: `--up` reaches the honest gate (`demo_mode == false`, `juniper_data_available == true`) and
`--down` releases all ports. **Deliverables**: PR-M1 (+PR-M2), a rehearsal transcript appended to the
evidence file. **PR count**: 1–2 (juniper-ml).

### 6.2 Phase 1 — Live click-by-click validation

**Entry**: Phase 0 exit met.
**Steps**: the orchestrating session drives a real browser through the **companion matrix** using the
browser MCP surface already sanctioned by the suite's Skills (`.claude/skills/service-smoke/SKILL.md` for
boot+HTTP+opt-in `--ui`, `.claude/skills/ui-test-author/SKILL.md` for authoring from live observation —
both declare `mcp__playwright`, `model: opus`, `effort: max`, and mandatory teardown). Order (matrix
numbering, chrome smoke first, the destabilizing degradation probe last): W13 → W1 → W2 → W3 → W4 →
W5 → W6 → W7 → W8 → W9 → W10 → W11 → W12 → W14.

**Evidence protocol** (per matrix row): pre-state, the exact interaction, observed DOM/network result,
status, screenshot id, and — for FAIL — the smallest reproducer. Failures are appended to the findings
ledger (§9) as they occur; validation does **not** stop at first failure unless the stack is unusable.

**Exit**: every matrix row's `status` column carries a terminal status (§9); no row left at the initial
`—`.
**Deliverables**: completed matrix, findings ledger, screenshot set. **PR count**: 0 (read-only session;
the matrix + ledger land with Phase 4).

### 6.3 Phase 2 — Defect triage & fix PRs

**Entry**: Phase 1 complete; ledger triaged into P0 (blocks a mandate-named workflow) / P1 (breaks a
documented behaviour) / P2 (cosmetic or drift).
**Steps**: one PR per defect or per tight defect cluster, each carrying (a) the fix, (b) a regression test
that fails on the parent commit, (c) a matrix-row reference. After each merge, re-run the affected matrix
rows on a fresh live stack and update the row status to `PASS (re-validated @ <sha>)`.
**Exit**: every P0 and P1 closed or explicitly deferred with owner sign-off; no matrix row left FAIL
without a linked issue. Count that mechanically with `python3 util/ad-hoc/e2e_finding_triage.py` (operator
contract: [`docs/REFERENCE.md` § Canopy E2E Finding Triage](../docs/REFERENCE.md#canopy-e2e-finding-triage));
`ACCEPTED` is owner-deferred and is **not** OPEN. **Deliverables**: fix PRs + regression tests. **PR count**: unknown a priori —
budget 3–10 (juniper-canopy), sized after Phase 1.

### 6.4 Phase 3 — Automated UI test-suite implementation

**Entry**: Phase 2 P0/P1 closed (so the suite encodes correct behaviour, not bugs).
**Steps**: implement §8 in four PRs — harness (env escape hatch + base-URL override + `ui_live` marker +
`src/tests/ui_live/` sibling directory + `make test-ui-live` runner), per-tab smoke suite, workflow
suites, fragile-area regression suites.
**Exit**: `make test-ui` (demo) and `make test-ui-live` both green; `make test-ui` and default `pytest`
byte-identical in behaviour to today (the live suite lives in the sibling `src/tests/ui_live/`, ignored
by the default addopts — §8.2); CI `ui-tests` job unchanged in scope and within its ≤5 min budget
(`ci.yml:350-351`).
**Deliverables**: `src/tests/ui_live/` suite + runner + docs. **PR count**: 4 (juniper-canopy).

### 6.5 Phase 4 — Evidence report, docs-truth-up, closeout

**Steps**: (1) publish `JUNIPER_2026-08-XX_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` in juniper-ml
`notes/` (matrix outcomes, ledger, environment header, screenshots index); (2) land the companion matrix
document; (3) one docs-truth-up PR per §11; (4) closeout note against the acceptance criteria (§13).
**Exit**: owner accepts the evidence report. **PR count**: 1 (juniper-ml notes) + 1–2 (juniper-canopy docs).

---

## 7. Fragile-Area Deep Dives

### 7.1 Network topology graph — display

**Implementation.** `NetworkVisualizer` (`src/frontend/components/network_visualizer.py`, `component_id`
default `"network-visualizer"` at `:69`) renders `dcc.Graph(id="network-visualizer-graph")` at `:246-258`
with `select2d`/`lasso2d` added to the modebar. Data arrives in
`network-visualizer-topology-store` (`:260`) from three sources: the tab-gated REST poll
(`dashboard_manager.py:3717-3724` → handler `:6427-6464`, `GET /api/topology` at `:6439`), the WS
cascade-add fast path (`:3741-3754`), and — for the heatmap — `network-visualizer-raw-topology-store` from
`GET /api/topology/raw` (`:3765-3784`), which is deliberately never WS-gated.

**Failure history.** A `ModuleNotFoundError` from the lazy `CascorServiceAdapter` import landed in a broad
`except` → `dash.no_update` → a permanently empty panel in client-less installs (the 2026-07-12…14 UI-leg
red, described in-code at `dashboard_manager.py:6447-6456`). The graph-format passthrough (`:6457-6459`) fixed
the demo shape; the weight-oriented branch (`:6462`) and the WS path (`:3742`) still import it (T-3/T-4).

**Validation approach.** LIVE lane only for the real payload. (i) Assert the panel renders ≥ the seed
topology before training; (ii) start training, wait for a cascade add, assert **node count increases** —
defeating the last-known-good masking of T-5; (iii) switch to Weight Matrix and assert the heatmap
populates from `/api/topology/raw`; (iv) repeat with `juniper-cascor-client` deliberately absent in a
throwaway env to prove the import path fails *loudly* after any Phase-2 fix — a **separate throwaway-env
drill** executed alongside matrix **W14** (W14 itself covers the stop-cascor upstream-outage induction;
the client-absent arm needs a different environment, not a stack manipulation, and is owned by this
subsection's Phase-1 execution).

**Planned regression tests.** `test_live_topology_renders_and_grows` (`ui_live`);
`test_topology_weight_matrix_populates` (`ui_live`); a non-browser unit pin that the weight-oriented branch
surfaces an error state rather than `no_update` when the client is missing (if Phase 2 changes that
behaviour).

### 7.2 Network topology graph — interactions

**Implementation.** Layout dropdown (Hierarchical / Staggered / Spring / Circular) `:110-120`; Show-Weights
checklist `:122-127`; Display mode Node Graph / Weight Matrix `:130-141`; View 2D / 3D `:144-155`;
hierarchy-depth slider + label `:169-192` (container hidden until ≥1 hidden unit); selection via
`clickData` + `selectedData` → `-selected-nodes` / `-selection-info` (`:545-562`); view-state capture from
`relayoutData` (`:292-297`).

**Known gap.** There is **no `hoverData` callback** anywhere in `network_visualizer.py` or
`dashboard_manager.py` (verified by grep) — hover is Plotly-native only. Matrix rows for hover must
therefore assert the Plotly tooltip, not a Dash-side effect.

**Validation approach.** Drive each control and assert a *figure-level* change (trace count, axis type
`scene` for 3-D, `heatmap` type for weight matrix) rather than a screenshot diff. Depth slider is exercised
only after the container un-hides (≥1 hidden unit) — before that it is `N-A`, not FAIL. Selection is
validated by asserting `-selection-info` becomes visible with the expected node ids.

**Planned regression tests.** `test_topology_layout_modes_change_figure`,
`test_topology_2d_3d_toggle`, `test_topology_depth_slider_filters`, `test_topology_click_select_info`
(all `ui_live`).

### 7.3 Front-page training status indicators

**Implementation.** One callback on the 1 s `fast-update-interval`
(`dashboard_manager.py:3087-3104`) → `_update_unified_status_bar_handler` (`:5939-5969`), a single
`GET /api/status` (`:5958`) whose measured latency colours `status-indicator` (`:714-721`) and fills
`latency-display` (`:812-819`). Segments: `top-status-display` (`:730-734`), `top-phase-display`
(`:749-753`), `top-epoch-display` labelled **"Step"** (`:766-779`; the value is `current_epoch` with a
`current_step` alias, `:6032-6037`), `top-hidden-units-display` inside `status-iteration-segment`
(`:792-810`; `installed / max`, `:6039-6042`). Non-200 is classified into an actionable label rather than a
bare "Error" (`:5963-5968`). The WS badge is separate (T-18).

**Failure history.** Mislabelled counters ("Epoch: 10000 vs 12", "Iteration: 0 / 10000") were corrected by
relabelling, with the true growth iteration moved to the Network Info panel (`:761-765`, `:784-791`,
`:6044-6049`); the badge-vs-relay divergence drove the two-input badge.

**Validation approach.** With training running: assert Status/Phase change from Stopped/Idle; assert Step
is monotonic non-decreasing across ≥3 ticks; assert Hidden Units matches the topology node count; assert
the latency dot recolours plausibly. Then a **degraded probe — executed as matrix workflow W14**
(upstream-degradation induction): stop cascor mid-run via the isolated stack's own helpers and assert the
status label becomes the classified failure label and the WS badge downgrades from green
(`WS: Upstream reconnecting` / `WS: Upstream degraded` — badge states 3/4), then restart cascor and
assert recovery **without restarting canopy** (restarting canopy while cascor is down triggers the T-2
silent demo fallback, which is its own separate assertion).

**Planned regression tests.** `test_status_bar_advances_during_training`,
`test_status_bar_classifies_backend_outage`, `test_ws_badge_downgrades_on_stream_health` (all `ui_live`);
plus a pure-unit pin on the `_counter_displays` (`dashboard_manager.py:5996-6070`) mapping if Phase 2
touches it.

### 7.4 Snapshots — saving / loading / replaying

**Implementation.** Create: `-create-button` (`hdf5_snapshots_panel.py:157`) → `_create_snapshot_handler`
(`:388`) → `POST /api/v1/snapshots` (`:407`). List: `_fetch_snapshots_handler` (`:432`) →
`GET /api/v1/snapshots` (`:463`); detail `:490`; history `:594` → `/api/v1/snapshots/history` (`:606`).
Per-row ops are a `DropdownMenu` of pattern-matched ids
`{"type": "hdf5-snapshots-panel-snapshot-op-btn", "index": <id>, "op": restore|replay|resume|retrain}`
(`:937-952`), collected by an `ALL/ALL` Input (`:1146`) into the confirm modal, then
`_invoke_snapshot_op_handler` (`:541`) → `POST /api/v1/snapshots/{id}/{op}` (`:556`). Right-click gives the
same four ops (`src/frontend/assets/snapshot_context_menu.js:33-34,:172-182`). Replay is driven by
`ReplayPlayerPanel`: play/pause/stop (`replay_player_panel.py:203,:210,:217`), scrubber `:238`, speed
`:259`, range `:284`, all through `_invoke_replay_control` (`:336`) →
`POST /api/v1/snapshots/{id}/replay/control` (`:356`); weights stream into `replay-weight-buffer` (`:124`)
drained on a 500 ms `Interval` (`:129`), with a V2-weights vs V1-metrics-only badge (`:177`).

**Traps.** Replay/resume/retrain 501 in demo (T-10); demo snapshots are fabricated + session-persistent
(`main.py:1818-1828`, `:1892-1899`); the two swap-restore buttons are dead (T-12). Restoring puts the cascor
FSM into `Investigating`, which unlocks the Network Editor — its panel polls `GET /api/status` on a 2 s
`Interval` (`network_editor_panel.py:135`, gate `:400`, poll `:486-493`), a behaviour also documented at
`docs/USER_MANUAL.md:354`.

**Validation approach.** LIVE lane: train briefly → create snapshot (named + described) → assert it appears
in the list and in history → restore → assert Network Editor unlocks within ~2 polls → replay → exercise
every transport control and assert the epoch readout and scrubber track → resume and retrain → assert
FSM/status transitions. DEMO lane covers only create/list/restore plus the expected 501s.

**Planned regression tests.** `test_snapshot_create_appears_in_list`,
`test_snapshot_restore_unlocks_network_editor`, `test_replay_controls_drive_scrubber`,
`test_replay_resume_retrain_reachable` (all `ui_live`); `test_replay_ops_501_in_demo` (existing demo lane).

### 7.5 Dataset loading — cold and hot migration

**Cold path.** Sidebar dataset section: `nn-dataset-type-dropdown` (`dashboard_manager.py:1243`, options
model-gated at `:2424-2433`), spiral typed fields plus schema-driven
`{"type": "nn-gen-param", "name": …}` inputs rendered from `GET /api/dataset/generators`
(`:2440-2448`, `:2601-2613`; the endpoint proxies juniper-data's `/v1/generators` at `main.py:1650-1662`),
then `apply-dataset-button` (`:1258`) → `POST /api/stage_dataset` (`main.py:3824`) → the
`pending-dataset-banner` (`:1554`) with `restart-with-new-dataset-button` (`:1539`) and
`cancel-pending-dataset-button` (`:1545` → `DELETE /api/cancel_pending_dataset`, `main.py:3847`). Restart
opens `restart-confirm-modal` (`:2045`, `backdrop="static"`) carrying a plan summary (`:1973`), a
start-fresh toggle (`:1975`), a granular re-stage section (`:1986-2028`) and a baseline store (`:2035`),
confirmed at `:2041` → `POST /api/train/restart` (`main.py:3426`, `reset` defaults True at `:3380/:3451`).

**Hot path.** `experimental-functions-toggle` (`:1646`), server-authoritative via
`GET|POST /api/admin/experimental_functions` (`main.py:3880`, `:3902`), gates
`live-dataset-switch-button` (`:1275`); the gate requires **both** the flag and a running training run
(`_gate_live_switch_button_handler`, `:5722-5731`). Click opens the two-step `live-switch-modal`
(`:1909`, summary built at `:5733-5749`); accept → `POST /api/live_dataset_swap` (`main.py:3937`), cancel
in-flight → `DELETE` on the same path (`:3968`). Swap history feeds `GET /api/history/dataset_swaps`
(`main.py:4006`).

**Dataset View tab.** Generate / Upload / URL modal tabs
(`dataset_plotter.py:99,:198,:204,:213-214,:233,:249,:254,:263`) — all three are demo-only server-side
(T-11), and URL import is additionally opt-in (`settings.py:396`).

**Model interaction.** `POST /api/model/select` (`main.py:3570-3585`) re-creates the backend; the picker is
the modal at `dashboard_manager.py:2112` with search `:2098` and per-row `{"type":"model-select-btn"}`
(`:2415`), mirroring the result into `model-class-store` (`:2412`). Hydration is once-per-mount from
`GET /api/train/status` on `params-init-interval` (`:2333-2351`).

**F-CANDIDATE (to be confirmed in Phase 1).** With no `recurrence_service_url`, selecting *Recurrence
(LMU)* leaves the backend on cascor (`main.py:3498-3510`; `src/backend/__init__.py:125-127`) while Start
stays enabled (`model_registry.py:232-247`) — the user is shown a successful selection of a model that is
not actually active. Ledger it; do not pre-judge the fix.

**Validation approach.** Cold: stage a *different* generator, assert the banner, open the restart modal,
assert the plan summary reflects the staged config, toggle granular fields, confirm, then assert the
Dataset View and topology input width both reflect the new dataset. Hot: enable the experimental flag,
assert the button stays disabled until training runs, start training, swap live, assert the swap appears in
`/api/history/dataset_swaps` and the metrics stream continues. Also assert the cancel paths.

**Planned regression tests.** `test_cold_dataset_stage_banner_restart`,
`test_cancel_pending_dataset_clears_banner`, `test_live_switch_gated_by_flag_and_running`,
`test_live_dataset_swap_records_history`, `test_model_select_suppresses_cascade_tabs` (all `ui_live`).

---

## 8. Test-Suite Implementation Design

### 8.1 Constraints inherited from the existing harness

The current suite is 11 files / 21 test functions under `src/tests/ui/`, **20** of them
`@pytest.mark.ui` (marker declared at `pyproject.toml:368`) —
`src/tests/ui/test_sidebar_width.py:52` `test_every_known_tab_has_a_label_mapping` carries
`@pytest.mark.regression` instead (`:51`), so it is reachable **only** through `make test-ui`
(`Makefile:23-24`, no `-m` filter): CI's `-m "ui and not slow"` selector (`ci.yml:402`) never runs it
and the default run ignores the directory — and any future CI selector built on the `ui` marker
**preserves that hole** rather than closing it. Phase-3 one-liner (fold into PR-C-H): mark that test
`ui` as well, or move it out of `src/tests/ui/`. `canopy_url` (`src/tests/ui/conftest.py:33-79`)
**Popens `src/main.py`** in demo mode on a free port and gates on `/v1/health/ready`; `dashboard_page`
(`:81-126`) pre-seeds `localStorage['juniper_canopy_welcomed']` and applies a two-stage init-race gate.
The demo pins are hard-set in the conftests (§8.2 item 1). UI tests are `--ignore`d from the default run
(`pyproject.toml:339-353`) and run via `make test-ui` (`Makefile:23-24`).

### 8.2 Live-lane architecture (four additive changes, zero behaviour change to the existing lanes)

1. **Env escape hatch for the three demo pins.** There are **three** demo-pin sites, not two:
   `conftest.py:12` (root), `src/tests/conftest.py:23` (suite — which also pins
   `JUNIPER_DATA_URL=http://localhost:8100`, the **operator** data port, at `:25`, and disables rate
   limiting at `:27`), and `src/tests/ui/conftest.py:39` (`"JUNIPER_CANOPY_DEMO_MODE": "1"` inside the
   `canopy_url` subprocess env — bypassed on the live path only because item 2 Popens nothing, an
   implicit dependency stated here explicitly). The two module-level pins move from unconditional
   assignment to an explicit opt-in guard, e.g.
   `if os.getenv("JUNIPER_CANOPY_TEST_LIVE") != "1": os.environ["JUNIPER_CANOPY_DEMO_MODE"] = "1"`.
   Default behaviour (no env var) is byte-identical to today — this is the invariant the PR must prove.
2. **Base-URL override.** `canopy_url` grows a first branch: when `JUNIPER_E2E_CANOPY_URL` is set, **yield
   it and Popen nothing** (no subprocess, no teardown kill). `dashboard_page` is unchanged and simply
   targets the external stack. The live fixture additionally performs the §4.3 honest gate and **fails the
   session loudly** if `demo_mode != false` — a live suite silently running against a demo backend is the
   single worst outcome available to this arc.
3. **New sibling directory `src/tests/ui_live/` + marker `ui_live`.** The live tests go in a **new
   sibling directory `src/tests/ui_live/`** — deliberately **not** inside `src/tests/ui/` — with (a) the
   pyproject `addopts` gaining `--ignore=src/tests/ui_live` beside the existing `--ignore=src/tests/ui`
   (`pyproject.toml:352`), so the default suite and the CI demo lane never collect it; (b) `make test-ui`
   left **untouched**; (c) the marker `ui_live` registered in `pyproject.toml` markers and carried by
   every live test, for selection hygiene. **Why the sibling, stated explicitly**: the default `pytest`
   run collects `src/tests/**` wholesale (only the `--ignore` lines keep subtrees out), so an un-ignored
   new directory would leak into `make test`; and a directory *inside* `src/tests/ui/` would leak into
   `make test-ui`, because `Makefile:24` runs `$(PYTEST) src/tests/ui --override-ini=addopts=` with **no
   `-m` filter** — pulling the live suite into the demo runner and breaking the A-6 "`make test-ui`
   unchanged" promise. The CI `ui-tests` job is additionally path-scoped to `src/tests/ui`
   (`ci.yml:403`), so no CI selector change is required; `-m "ui and not slow"` (`ci.yml:402`) stays
   as-is (see §8.1 for the pre-existing `regression`-marker hole that selector already has).
4. **Local runner.** A new `make test-ui-live` target that requires `JUNIPER_E2E_CANOPY_URL` (plus the
   live-lane env vars, e.g. `JUNIPER_CANOPY_TEST_LIVE=1`), runs
   `pytest src/tests/ui_live --override-ini=addopts= -m ui_live --junitxml=reports/junit/junit-ui-live.xml`,
   and refuses to run without the honest gate. **The live lane is deliberately NOT wired into GitHub
   Actions** — CI has no cascor and no juniper-data (checklist §6), so a CI live lane could only ever be a
   disguised demo run.

### 8.3 The `set_params` doctrine (numeric parameters)

Because of T-7, no live test may attempt to type into a numeric `dbc.Input`. The sanctioned pattern is the
one already shipped: `POST /api/set_params` with the full field set, poll `/api/state` for the value, then
assert the DOM input reflects it after the init tick — exactly
`src/tests/ui/test_param_roundtrip_visible.py:37-92`. Field-count precision (verify against code, not
lore): the dirty-tracking `comparisons` list watches **27** inputs (`dashboard_manager.py:6884-6912`);
the Apply callback gathers **28** `State`s (`:4508-4540` — the 27 plus the non-dirty-tracked
`nn-init-output-weights-dropdown`, matrix D-2), the number the shipped test's comment mirrors
(`test_param_roundtrip_visible.py:35`); and the Apply `POST /api/set_params` body it builds carries
**25** keys (`:6971-7003`) — three of the 28 are deliberately dropped: `nn_dataset_elements` and
`nn_dataset_noise` (canopy-local; they travel on `/api/stage_dataset`) and `cn_training_complete` (a
read-only status flag). The shipped test payload is its own 27-key shape (`:37-65`: the 25 POST keys
minus `nn_init_output_weights`, plus those three canopy-local keys, to satisfy `SetParamsRequest`).
Non-numeric controls (dropdowns, radios, checklists, sliders, buttons) are driven normally through the
browser.

### 8.4 Suite composition

| Suite | File(s) | Content | Lane |
|---|---|---|---|
| Per-tab smoke | `src/tests/ui_live/test_tabs_smoke.py` | 15 parametrized cases: click tab → assert its signature element **visible** (T-13) → assert no console error → assert sidebar width matches `ui_standards.TAB_SIDEBAR_WIDTH` | live |
| Workflows | `src/tests/ui_live/test_workflows_*.py` | W1/W2 control loop, W3 params, W6 cold migration, W7 hot migration, W5 snapshot lifecycle + replay, W8 model swap | live |
| Fragile-area regressions | `src/tests/ui_live/test_fragile_*.py` | the eighteen `ui_live` tests named in §7 (plus one demo-lane test, `test_replay_ops_501_in_demo`) | live |
| Demo-only | extend `src/tests/ui/` | Generate modal, import-file, import-url-disabled, 501 replay ops, welcome modal | demo |

### 8.5 Outputs

JUnit XML to `reports/junit/junit-ui-live.xml` (mirroring the CI artifact convention at `ci.yml:409-415`),
Playwright screenshots on failure into `reports/e2e/<run-id>/`, and a run header recording: canopy
`git_sha`/`build_date` from `/v1/health` (`main.py:1073-1074`), `demo_mode`, `juniper_data_available`,
**`enable_ws_control_buttons` (the training-button transport posture — T-21; default `True`, log line
`dashboard_manager.py:4149`)**, rate-limiter state, API-key posture, and the four service ports.

---

## 9. Evidence & Reporting Protocol

**Row statuses** — the single shared vocabulary, used identically by this plan and the companion matrix
(the matrix's every §2/§3 row carries a `status` column initialized `—` and filled with exactly one of
these terminal values during Phase 1):

| Status | Meaning |
|---|---|
| `PASS` | Observed behaviour matches the expectation stated in the matrix row. |
| `FAIL` | Divergence from code-derived expected behaviour → a ledger entry. A `DEAD-EXPECTED`-class row that produces a network request, DOM change, or console error is a `FAIL` (regression in the opposite direction). |
| `BLOCKED` | Could not be exercised because a prerequisite failed (record the blocker's finding id / divergence id). |
| `N-A` | Not applicable in this lane/config (e.g. recurrence rows without a recurrence service; the 429 toast arm with the limiter off). |
| `DEAD-CONFIRMED` | The terminal PASS-state of a `DEAD-EXPECTED` automation-class row (matrix §1.3): the click verifiably did nothing — no request, no DOM change, no console error. |

`DEAD-EXPECTED` remains the matrix's **automation class** (§1.3); its passing terminal status is
`DEAD-CONFIRMED`. A code-vs-doc **DIVERGENCE** (matrix D-0 …) is a ledger annotation, **not** a row
status, and is not a Phase-1 failure.

**Findings ledger.** One row per finding, id `F-CANOPY-NNN` (zero-padded, sequential from `F-CANOPY-001`),
fields: id · title · severity (P0/P1/P2) · matrix row(s) · lane · `file:line` evidence · reproducer ·
screenshot id · status (`OPEN` / `FIXED-IN <PR>` / `DEFERRED`). Findings against *other* repos are
prefixed `F-CASCOR-` / `F-DATA-` / `F-ML-` and are filed as issues in their own repo.

**Screenshots.** `reports/e2e/<run-id>/<row-id>__<step>.png`, where `<row-id>` is the matrix's
first-column row id — chrome rows `C<section>-NN` (e.g. `C2.5-03`), tab rows `M-<TAB>-NN` (e.g.
`M-TOPOLOGY-04`) — referenced by id from the matrix and the ledger; the run-id is
`<UTC yyyymmddThhmmssZ>`.

**Evidence report.** `JUNIPER_2026-08-XX_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` in juniper-ml `notes/`
(date = the day the report is published), containing the environment header (§8.5), the completed matrix
outcome table, the full ledger, the re-validation record from Phase 2, and the acceptance-criteria
scorecard (§13).

---

## 10. PR & Merge Plan

| PR | Repo | Content | Gate |
|---|---|---|---|
| **PR-M1** | juniper-ml | `isolated_stack.bash` nested-port fix + checklist §3.3 correction + inverted/negative test assertions across **all three** `JUNIPER_CANOPY_PORT` occurrences (`tests/test_isolated_stack_script.py:348-349`, `:425` launch-stub heredoc, `:609`) | juniper-ml CI green |
| **PR-M2** *(conditional, §4.5)* | juniper-ml | `--with-recurrence` fourth leg (8211) + **8211 occupancy pre-check** (juniper-deploy maps host 8211 → recurrence ctr 8210) + canopy recurrence URL wiring + tests | juniper-ml CI green |
| **PR-C1…Cn** | juniper-canopy | Phase-2 fixes, one per defect/cluster, each with its failing-first regression test | canopy CI green **incl. `ui-tests`** |
| **PR-C-H** | juniper-canopy | Live-lane harness: conftest escape hatch, `JUNIPER_E2E_CANOPY_URL` fixture branch, `src/tests/ui_live/` sibling dir + `--ignore=src/tests/ui_live` addopts line, `ui_live` marker, `make test-ui-live` target (`make test-ui` untouched), §8.1 regression-marker one-liner | canopy CI green; default `pytest` and `make test-ui` output provably unchanged |
| **PR-C-S** | juniper-canopy | Per-tab smoke suite (15 parametrized rows) | canopy CI green |
| **PR-C-W** | juniper-canopy | Workflow suites (W1…W8) | canopy CI green |
| **PR-C-F** | juniper-canopy | Fragile-area regression suites (§7) | canopy CI green |
| **PR-C6** | juniper-canopy | Decision on the dead swap-restore buttons (T-12): wire or remove, with a test either way | canopy CI green |
| **PR-C-D** | juniper-canopy | Docs-truth-up batch (§11) | canopy CI green (docs link job) |
| **PR-ML-N** | juniper-ml | This plan + companion matrix + evidence report + the two audit reports into `notes/` | juniper-ml CI green |

**Estimated total**: 2 (ml, Phase 0) + 3–10 (canopy fixes) + 4 (canopy suite) + 1 (canopy docs) + 1 (ml
notes) ≈ **11–18 PRs**.

**Merge policy restated**: headless merge is pre-authorized for this arc's PRs only, each still requires
green CI including `ui-tests`, and no PR in this arc touches release/publish machinery or a deploy gate.
Sequence: PR-M1 (+M2) → PR-C1…Cn → PR-C-H → PR-C-S → PR-C-W → PR-C-F → PR-C6 → PR-C-D → PR-ML-N.

---

## 11. Documentation-Drift Handling

**Policy.** For validation purposes, **code is truth**. A control that behaves differently from the manual
is a *documentation* finding unless the code behaviour is itself wrong. Drift is recorded in the ledger
(severity P2 unless it would mislead an operator into a destructive action) and repaired in the single
Phase-4 docs-truth-up PR — never silently edited inside a code PR.

**Known drift confirmed during grounding:**

| # | Claim | Location | Reality |
|---|---|---|---|
| D-1 | Supported dataset formats: CSV, JSON, NumPy `.npy`, HDF5 `.h5` | `docs/USER_MANUAL.md:516-521` | `POST /api/dataset/import-file` accepts **CSV only** (`main.py:1470-1492`, via `parse_csv_bytes`) and is demo-only. |
| D-2 | Config override via `CASCOR_<SECTION>_<KEY>` env vars | `docs/USER_MANUAL.md:553-570` | Prefix is `JUNIPER_CANOPY_` with `__` nesting (`settings.py:188-195`); the legacy names only survive as deprecation aliases. |
| D-3 | Max Hidden Units range "1 - 100", default 10 | `docs/USER_MANUAL.md:222-227` | `hidden_units: min=0, max=10000, default=1000` (`settings.py:113`). |
| D-4 | Only ~5 of 15 tabs documented (Metrics, Topology, Network Editor, Decision Boundary, Dataset View) | `docs/USER_MANUAL.md:236,:283,:350,:425,:491` | 15 tabs ship (`dashboard_manager.py:2176-2252`). 10 tabs are undocumented. |
| D-5 | Redis / Cassandra integration listed as "Planned" | `docs/REFERENCE.md:166-171` | Both tabs ship with panels and live endpoints (`/api/v1/redis/*`, `/api/v1/cassandra/*`). |
| D-6 | "Real CasCor C++ prototype" / "C++/Python" backend | `docs/demo/DEMO_MODE_QUICK_START.md:65`; `docs/demo/DEMO_MODE_MANUAL.md:27,:38` | The service backend is the Python juniper-cascor service. |
| D-7 | `conda activate JuniperPython` | `docs/cassandra/CASSANDRA_INTEGRATION_QUICK_START.md:81,:147`; `docs/testing/TESTING_QUICK_START.md:12,:88,:92` | That env is `JuniperPython-DEPRECATED`; canopy runs in `JuniperCanopy1`. |
| D-8 | `src/backend/__init__.py:116-118` states the picker gates an unconfigured recurrence model out | `src/backend/__init__.py:116-118` | `model_is_trainable` gates on registry `status` only (`model_registry.py:232-247`); recurrence is hardcoded `"live"` (`:188`). Docstring **or** code must change (§7.5). |

Any additional drift found in Phase 1 is appended to this table before the Phase-4 PR is opened.

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A live run silently degrades to demo (T-2) and produces meaningless PASSes | Whole session invalid | §4.3 honest gate enforced at bring-up **and** as a session-scoped fixture assertion in the live suite (§8.2 item 2) |
| Last-known-good `no_update` masking (T-5) turns a broken panel into a "stale but plausible" one | False PASS on the top fragile area | Every fragile-area assertion requires an **observed change** (node count grows, epoch advances), never a static snapshot |
| Long live workflows exceed the 120 s WS idle timeout (T-17) | Spurious badge FAILs | Bounded waits sized under 120 s; badge transitions across an idle boundary are expected, not FAIL |
| Live tests become flaky and erode trust | Suite gets disabled | Live lane is local-only (never gating CI), uses explicit `wait_for_function` gates modelled on `conftest.py:110-125`, and any test that flakes twice is quarantined with a ledger entry rather than retried blindly |
| Phase-2 defect count is unknown until Phase 1 completes | Schedule uncertainty | Phases 2/3 are budget-ranged, not fixed; the owner re-approves scope if P0 count exceeds ~5 |
| Cross-repo defect surfaces (cascor/data) | Arc scope creep | Filed as `F-CASCOR-` / `F-DATA-` issues in their own repos; this arc only records the UI-visible symptom |
| Concurrent sessions collide on the same worktree/branch space | Lost work / duplicate PRs | `gh pr list` dup-guard before opening any PR; per-agent scratchpad subdirectories; one agent owns the arc's branch namespace |
| The port fix lands but an operator canopy already holds 8050/8051 | Bring-up confusion | Phase-0 step 3 explicitly checks both ports before `--up` |

---

## 13. Acceptance Criteria

| # | Owner requirement | Measurable criterion |
|---|---|---|
| **A-1** | (a) All top-tab-menu pages open and display contents as expected | All 15 tabs in §3.2 have a `PASS` row in both the tab-open and content-render matrix columns on the LIVE lane, plus the cascade-suppression variant for a one-shot model; zero rows left at the initial `—`. |
| **A-2** | (b) All documented functionality works from the front end | Every behavioural claim in the enumerated claim set — the §11 drift table (D-1…D-8) plus any USER_MANUAL / REFERENCE claim found and appended during Phase 1 — has a matrix row (or ledger entry) with a terminal status; each divergence is either a `FIXED-IN <PR>` ledger entry or a §11 drift row. (The matrix is code-derived; §11 is the doc-claim denominator, kept current as Phase 1 finds more.) |
| **A-3** | (c) All primary workflows function end-to-end | W1 … W14 each end `PASS` on the LIVE lane (W8 per the §4.5 recurrence decision, else its rows are `N-A`; W9's three demo-only controls on the DEMO lane with its live-lane 400-mirror step on LIVE; W14's stop/restart-cascor induction steps are MANUAL stack manipulations, honestly recorded as such). |
| **A-4** | (d) The five fragile areas | Each §7 subsection's validation approach executed and `PASS`, **and** its named regression tests merged and green (≥18 new `ui_live` tests — the eighteen named in §7). |
| **A-5** | Click-by-click coverage | 100 % of the companion matrix's §2/§3 rows carry a terminal `status`-column value (keyed by row id `C<section>-NN` / `M-<TAB>-NN`); every interactive `id=` reachable from the 15 tabs + sidebar + status bar appears in the matrix or is listed with a documented exclusion reason. |
| **A-6** | A full test suite is implemented | `make test-ui-live` green against a live isolated stack; `make test-ui` and default `pytest` unchanged; canopy CI (incl. `ui-tests`) green on `main` after the last arc PR. |
| **A-7** | Evidence | `JUNIPER_2026-08-XX_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` published with environment header, full matrix outcomes, full ledger, and this scorecard filled in. |

---

## 14. Approval Gate & Amendment Protocol

1. **Gate.** The owner reviews this document together with the companion matrix and the two audit reports
   (§15). Execution — including Phase 0 — begins only on the owner's explicit approval. No agent message,
   including this one, constitutes that approval.
2. **Cross-validation before ratification.** Because this arc authorizes headless merges, two independent
   auditors re-probe every `file:line` claim here (grounding audit) and every mandate clause against
   coverage (coverage audit). Their reports are inputs to the gate, not post-hoc commentary.
3. **Amendments.** Once approved, this document is the design of record. Changes arrive as **follow-up
   PRs against this file** with a dated `## Amendment N` section stating what changed and why; the original
   text is never rewritten in place. Scope-expanding amendments (new phases, new repos, new merge
   authority) require fresh owner approval.
4. **Status transitions.** `DRAFT — AWAITING OWNER APPROVAL` → `APPROVED — IN EXECUTION` (owner edits the
   header) → `COMPLETE` (on acceptance of the evidence report) or `SUPERSEDED BY <doc>`.

---

## 15. References

**Companion / audit documents (this arc)**

- `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` — per-control matrix + numbered workflow scripts (authored in parallel)
- `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-GROUNDING-AUDIT.md` — COMPLETE (GO-WITH-FIXES; corrections applied in this revision — see Validation record)
- `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-COVERAGE-AUDIT.md` — COMPLETE (MAJOR-GAPS; corrections applied in this revision — see Validation record)
- `JUNIPER_2026-08-XX_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` — Phase-4 deliverable

**juniper-canopy — code**

- `src/main.py` — FastAPI app, Dash mount (`:495`), lifespan + demo fallback (`:322-337`), health (`:1047-1075`), dataset routes (`:1414`, `:1470`, `:1557`, `:1640`), train routes (`:3246`, `:3278`, `:3299`, `:3320`, `:3341`, `:3426`), model select (`:3570`), `set_params` (`:3640`), staging/live-swap (`:3824`-`:4006`), snapshot ops (`:2553-2563`, `/api/v1/snapshots*`), entrypoint (`:4247-4258`)
- `src/frontend/dashboard_manager.py` — layout (`:596`), status bar (`:710-820`, `:3087-3104`, `:5939`), sidebar (`:267-282`, `:284`, `:2286-2322`), tabs (`:1694-1700`, `:2164-2268`, `:2353-2370`), model selection (`:2098-2119`, `:2372-2433`), dataset controls (`:1243-1290`, `:1539-1554`, `:1646`, `:1909`, `:2045`), training buttons (`:857-890`, `:4119-4186`), params (`:4385+`, `:7028-7042`), WS/topology stores (`:3437-3538`, `:3717-3784`), handlers (`:5722-5749`, `:6427-6464`, `:6749-6752`)
- `src/settings.py` — `ServerSettings` (`:118-123`), WS (`:126-166`), model_config (`:188-195`), recurrence (`:261-270`, `:509-525`), rate limit (`:317-318`), `enable_ws_control_buttons` (`:349`), csrf/browser-control (`:366`, `:376`), URL-import gate (`:396`)
- `src/security.py` (`:44-73`, `:261-281`), `src/frontend/internal_api.py:63-79`, `src/model_registry.py:160-247`, `src/backend/__init__.py:111-134`
- Components: `network_visualizer.py`, `hdf5_snapshots_panel.py`, `replay_player_panel.py`, `dataset_plotter.py`, `network_editor_panel.py`, `metrics_panel.py`, `connection_indicator.py`
- Assets: `src/frontend/assets/{snapshot_context_menu,context_menus,tutorial_walkthrough,ws_dash_bridge,websocket_client,ws_latency}.js`

**juniper-canopy — tests, CI, docs**

- `src/tests/ui/{conftest,test_param_roundtrip_visible,test_apply_button_flow,test_l3_native_setter_poc,test_train_after_reset,test_ws_silent_poll_liveness}.py`; `conftest.py`; `src/tests/conftest.py`; `pyproject.toml:336-389`; `Makefile`
- `.github/workflows/ci.yml:347-415`, `:905-949`; `notes/UI_STANDARDS.md`; `docs/{USER_MANUAL,REFERENCE}.md`; `docs/{demo,testing,cassandra}/`

**juniper-ml** — `util/isolated_stack.bash`; `tests/test_isolated_stack_script.py`;
`notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md`;
`notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`;
`.claude/skills/{service-smoke,ui-test-author}/SKILL.md`

**juniper-recurrence** — `juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py:128,:152` (flat `JUNIPER_RECURRENCE_` prefix; container/default port 8210 — juniper-deploy maps **host 8211** → ctr 8210 per the `:152` comment, hence the §4.5/PR-M2 occupancy pre-check)

---

*End of document. Status: DRAFT — AWAITING OWNER APPROVAL.*
