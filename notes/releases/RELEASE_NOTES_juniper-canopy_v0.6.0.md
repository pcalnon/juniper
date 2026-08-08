# juniper-canopy v0.6.0 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-07-29
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-canopy

---

This is a security-bearing release of `juniper-canopy` v0.6.0. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-canopy` |
| **Fixed in** | 0.6.0 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.6.0

### Added

- **3-D (time-series) dataset display — Phase 1 (#368)**: canopy can now load and
  visualize 3-D sequence / irregular-Δt datasets. `DemoMode`'s dataset-load path is
  `ndim`-aware (`src/demo_mode.py`): a 3-D artifact routes to a new **display-only**
  `_install_sequence_dataset` (window-0 feature view stored as JSON into `self.dataset`;
  **not** wired into the demo trainer — the cascor-like simulator can't ingest 3-D, OQ-4),
  while 2-D keeps the existing classification path. The dataset-plotter
  (`src/frontend/components/dataset_plotter.py`) gains a sequence render branch
  (dispatched on `dataset_kind == "sequence"` before any 2-D logic): feature
  **small-multiples over real (cumulative-Δt) time** + a **Δt strip** (≈ design mockup
  R4). The dispatch inspects `X_full`/`X_train` rank directly because the installed
  `juniper-data-client` (0.4.x) does not export `validate_npz_contract`. Design-of-record:
  juniper-ml `notes/JUNIPER_CANOPY_3D_DATASET_VISUALIZATION_DESIGN_2026-06-19.md`. Tests:
  `src/tests/unit/test_sequence_dataset_viz.py` (fixture-tested; live juniper-data 3-D
  end-to-end verification to follow). The control surface (signal/window selectors,
  small-multiple⇄overlay, target toggle) is Phase 2.
- **3-D dataset viewer — compare-signals controls (Phase 2a, #368)**: the sequence
  (3-D) dataset view gains its first interactive controls
  (`src/frontend/components/dataset_plotter.py`). A **signal multi-select** chooses which
  signals to plot (default: all) and a **Small multiples ⇄ Overlay** segmented toggle
  switches arrangement — small-multiples keeps each signal per-normalized and vertically
  offset (the honest default for mixed-scale sets, e.g. OHLCV), overlay shares one
  normalized axis for direct cross-signal comparison (design R2). Both controls render
  only for sequence datasets (a new visibility callback) and stay hidden for 2-D tabular;
  the signal selector self-populates from the loaded dataset's feature labels. Window-0
  only — **no backend change** (multi-window comparison + the target / characterization
  companions are Phase 2b/2c). The render path guards stale / out-of-range signal
  selections (falls back to all). Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_3D_DATASET_VISUALIZATION_DESIGN_2026-06-19.md` §3.1 / §5. Tests:
  `src/tests/unit/test_sequence_dataset_viz.py` (5 new cases).
- **3-D dataset viewer — compare-windows mode + multi-window backend (Phase 2b, #368)**:
  the sequence view gains a **`Compare: [Signals | Windows]`** segmented mode toggle (M1).
  *Compare-windows* plots one selected signal across multiple selected windows; *compare-
  signals* (default) keeps the multi-signal view but now within a **selectable window**.
  Each mode reuses the Small multiples ⇄ Overlay arrangement; only the active mode's
  controls are shown. Backend (`src/demo_mode.py`): `_install_sequence_dataset` now stores
  a **capped set of windows** (`windows_X` / `windows_dt`, cap 50; `n_windows_stored`
  records the cap, the true `n_windows` is preserved) so window-switching needs no
  re-fetch — still **display-only** (OQ-4, not wired into the trainer). Per-window Δt is
  honoured (each window keeps its own irregular cumulative-time axis). The plotter
  refactors the render path onto a shared `_plot_normalized_series` helper +
  `_window_arrays` (which falls back to the window-0 view for legacy dicts), so the Phase-1
  / 2a single-window behavior is preserved. Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_3D_DATASET_VISUALIZATION_DESIGN_2026-06-19.md` §3.1 / §5. Tests:
  `src/tests/unit/test_sequence_dataset_viz.py` (8 new cases: window cap, multi-window
  store, compare-windows render + defaults, window selection, fallback, control options).
- **3-D dataset viewer — target + characterization companions (Phase 2c, #368)**: the
  final Phase-2 slice completes the two-mode viewer. An optional **regression-target**
  graph (a `Show target` switch in the control bar) renders the primary window's target;
  a **collapsible characterization side companion** (on by default) shows whole-dataset
  **Δt** and **target** histograms plus a **W / L / F** stats block beside the main plots
  — the viz area is now a flex row whose companion hides for 2-D tabular so the main
  column expands. Backend (`src/demo_mode.py`): `_install_sequence_dataset` additionally
  stores the per-window regression target (`windows_y`, capped) and precomputes bounded
  whole-dataset `dt_hist` / `target_hist` (~30 bins each) — still **display-only** (OQ-4).
  The companions are wired as **separate callbacks**, so the core `update_dataset_plots`
  (and its tests) are unchanged. Resolves design OQ-A (target = a separate companion
  strip) and OQ-C (characterization = whole-dataset summary + the always-on selected-window
  Δt strip). Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_3D_DATASET_VISUALIZATION_DESIGN_2026-06-19.md` §3.3 / §5. Tests:
  `src/tests/unit/test_sequence_dataset_viz.py` (6 new cases). With 2a/2b this completes
  the Phase-2 control surface; the advanced full-cross grid remains Phase 3.
- **3-D dataset viewer — advanced full-cross grid (Phase 3, M4, #368)**: an opt-in
  **`Advanced: full-cross grid`** switch reveals a scrollable faceted grid of **every
  signal (columns) × window (rows)**, each cell a normalized line over cumulative-Δt time
  — the expert view the default two-mode viewer deliberately avoids. Hidden by default and
  **sequence-only**; **capped at 100 cells** (the window rows are trimmed so
  `rows × cols ≤ 100`, the title noting e.g. "first 20 of 30 windows"), inside a
  vertically-scrolling container with per-cell modebar zoom. No backend change (reuses the
  capped multi-window store from Phase 2b); wired as a **separate callback**
  (`update_sequence_grid`) so the core callbacks are untouched. Resolves design OQ-B (grid
  mechanics: row-trim cap + scroll + modebar zoom). **Completes the 3-D dataset
  visualization design** (Phases 1–3). Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_3D_DATASET_VISUALIZATION_DESIGN_2026-06-19.md` §3.4 / §5. Tests:
  `src/tests/unit/test_sequence_dataset_viz.py` (4 new cases: hidden-off, hidden-tabular,
  full-cross render, 100-cell cap).
- **Harness L2 — enroll the three #366-wired controls in the behavioral manifest
  (#369)**: `restart-with-new-dataset-button`, `nn-init-output-weights-dropdown`, and
  `dataset-plotter-dataset-selector` were L1-guarded (wired) but not yet behaviorally
  proven. Adds three `ControlContract` rows to `src/tests/ui_contract/control_manifest.py`
  (restart → `POST /api/train/start?reset=true`; init-output-weights → `POST
  /api/set_params` + `/api/state` roundtrip on the non-default `random`; dataset-plotter
  selector → `POST /api/dataset/generate {"generator": "spiral"}`), exercised in-process
  by the existing L2 driver. L2 grows 8 → 11 rows; closes the wired-vs-proven gap for the
  controls completed in #366.
- **Model + dataset-type registry (`src/model_registry.py`) — model-selection
  groundwork (A0, #368)**: a single source of truth for NN-model (`ModelSpec`) and
  dataset-type (`DatasetTypeSpec`) specifications. The dashboard's
  `nn-dataset-type-dropdown` now sources its options and default from
  `dataset_type_options()` / `DEFAULT_DATASET_TYPE` instead of a hardcoded inline list
  — **behavior-preserving** (identical labels / values / order / `spirals` default).
  Seeds the current `cascor` (live, 2-D) and `recurrence`/LMU (coming-soon, 3-D,
  `requires_dt`) models plus the five 2-D classification dataset types, with a
  future-proofed spec shape (`status` lifecycle; `version` / `benchmark_id` / `family`
  / `variant` / `tags`). `task_type` uses juniper-data's vocabulary
  (`classification` / `regression`); a model's 3-D / irregular-Δt nature is carried by
  `ndim` + `requires_dt`, not a task-type label. The compatibility resolvers, the
  dedicated selection surface, and the `nn_model` backend mirror are deferred to A1.
  Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`. Regression
  coverage: `src/tests/unit/test_model_registry.py`.
- **Recurrence (LMU) service adapter + outbound settings — model-selection A1 enabler
  (A1-i, #368)**: the first build slice of A1 (making `recurrence` genuinely *trainable*
  from canopy, not just a coming-soon registry entry). Adds `RecurrenceServiceAdapter`
  (`src/backend/recurrence_service_adapter.py`) — a thin **synchronous** `httpx` REST
  client for the juniper-recurrence model service: a blocking `POST /v1/train` (the LMU is
  a one-shot ridge/lstsq fit — no epochs to stream, hence no WebSocket) plus the instant
  `GET /v1/training/status`. It sends the outbound `X-API-Key`, applies a **generous
  read-timeout** to the blocking train, and maps failures onto a typed error hierarchy
  (`RecurrenceTrainInProgressError` 409 / `RecurrenceServiceAuthError` 401·403 /
  `RecurrenceServiceTimeoutError` / `RecurrenceServiceUnavailableError` / base
  `RecurrenceServiceError`) so the one-shot UI path (D1-A, A1-iii) can surface each
  distinctly. New `Settings.recurrence_service_url` + `recurrence_api_key`
  (`src/settings.py`) mirror the juniper-data outbound-key pattern: the prefixed
  `JUNIPER_CANOPY_*` var wins over the shared cross-service var (`RECURRENCE_SERVICE_URL` /
  `JUNIPER_RECURRENCE_API_KEY`), and the key honours `_FILE` secret indirection.
  **Adapter + settings only — no routing or UI yet**: `create_backend` provider routing is
  A1-ii; the one-shot execution path + cascade-panel suppression A1-iii. Scope is `train` +
  `status` (predict / crossval deferred — enabler OQ-2). Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md` (D3) /
  `..._MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`. Tests:
  `src/tests/unit/test_recurrence_service_adapter.py` (24 cases, mocked via
  `httpx.MockTransport`) + `src/tests/unit/test_recurrence_settings.py` (11 cases).
- **Recurrence backend + provider routing — model-selection A1 enabler (A1-ii, #368)**:
  the second build slice, making the recurrence model *routable* through canopy's backend
  factory. Adds `RecurrenceBackend` (`src/backend/recurrence_backend.py`) — a
  `BackendProtocol` wrapper over the A1-i `RecurrenceServiceAdapter` that bridges the
  execution-paradigm mismatch (D1-A): the recurrence `POST /v1/train` is a **synchronous
  one-shot fit**, so `start_training` backgrounds it on a daemon thread and the backend
  reports a **binary** `idle → training → trained|failed` status via `get_status` /
  `is_training_active` (no fabricated per-epoch progress). The cascade-only protocol
  surface is honestly stubbed — `get_network_topology` / `get_raw_topology` /
  `get_decision_boundary` return `None` (LMU has no growing topology or 2-D decision
  boundary, D6) — and `get_metrics` carries the **regression** metric set (mse / rmse / mae
  / r2 / loss, never accuracy); `apply_params` stages `d` / `theta` / `ridge` for the next
  fit; failures surface via the existing `completion_reason` field. `create_backend()`
  (`src/backend/__init__.py`) gains an `nn_model` axis (D5): a recurrence-provider model
  (resolved via the new `model_registry.get_model_spec()` + `RECURRENCE_PROVIDER` constant)
  with `recurrence_service_url` configured routes to `RecurrenceBackend`; **every other
  case — non-recurrence model, unconfigured URL, or the `nn_model=None` startup default —
  leaves the demo/cascor selection byte-for-byte unchanged**. **Routing + backend only**:
  wiring `backend_type == "recurrence"` through `main.py`'s route branches and the one-shot
  result view / panel suppression are A1-iii. Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md` (D1-A / D5 / D6).
  Tests: `src/tests/unit/backend/test_recurrence_backend.py` (24 cases — backgrounding,
  binary status, stubs, failure handling, controllable fake adapter) +
  `src/tests/unit/test_recurrence_routing.py` (9 cases — routing precedence + `get_model_spec`).
- **Recurrence route correctness + dataset-ref plumbing — model-selection A1 enabler
  (A1-iii-a, #368)**: makes a recurrence (one-shot) backend behave correctly in `main.py`'s
  route layer and lets a recurrence fit actually run. **Route fixes** (`src/main.py`): the
  `/api/v1/snapshots` mock-snapshot path is gated on `== "demo"` (was `!= "service"`, which
  made recurrence serve fabricated demo snapshots); the snapshot create/restore adapter calls
  are gated on `== "service"` (recurrence's `_adapter` is a different type — it must use the
  h5py fallback, not cascor's `save_snapshot`/`load_snapshot`); `/api/v1/workers/stats` +
  `/workers/list` return an **empty** pool for recurrence instead of the synthetic demo-worker
  fixtures; and the lifespan seeds `training_state` from `get_status()` for recurrence (it has
  no live stream / `set_state_update_callback`). The cascade-only routes were already correctly
  fenced by `== "service"` guards (clean 501/503), and `RecurrenceBackend` already returns
  `None` for topology / decision-boundary (a regression test now locks in the clean 503).
  **Dataset-ref plumbing**: `/api/train/start` gains an optional body (`dataset` ref +
  `d`/`theta`/`ridge`) and the `/ws/control` `start` command forwards its `params`, both via a
  shared `_recurrence_start_kwargs` helper — for **recurrence only**, so cascor/demo keep their
  bare `start_training(reset=…)` call **byte-for-byte unchanged** (extra kwargs would break
  them). **No UI** — the model picker + the one-shot result view / panel suppression are
  A1-iii-b / A1-iv. Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_A1_III_DASHBOARD_INTEGRATION_SCOPE_2026-06-23.md`. Tests:
  `src/tests/regression/test_recurrence_routes.py` (11 cases — route mis-bucket guards,
  topology/boundary 503, dataset-ref forwarding, cascor-unaffected, the helper).
- **One-shot cascade-panel suppression — model-selection A1 enabler (A1-iii-b1, #368)**:
  the dashboard now hides the cascade-network-only panels for a one-shot (recurrence / LMU)
  model. Adds an **execution paradigm** axis: `ModelSpec.execution` (`"live" | "one_shot"`,
  `model_registry.py`) + an `execution` property on `BackendProtocol` and all three backends
  (`demo`/`service` → `"live"`, `recurrence` → `"one_shot"`), surfaced to the frontend via a
  new `"execution"` field on `GET /api/train/status`. A new `model-class-store` (`dcc.Store`)
  is hydrated from that route on mount; when it reads `"one_shot"`, three callbacks
  (`_setup_model_class_callbacks`) **suppress** the cascade-only surface — the 5 viz tabs
  (Candidate Metrics / Network Topology / Network Evolution / Decision Boundary / Workers,
  rebuilt via a new `_all_visualization_tabs()` + `_visible_tabs()` so a now-hidden active
  tab falls back to *Training Metrics*) and the status-bar **Iteration** (hidden-units)
  segment. An LMU has no growing topology, decision boundary, candidate units, or worker pool,
  so these are meaningless for it; the route layer already refuses to serve them (A1-iii-a).
  **Suppression only** — the metrics accuracy→regression switch + the one-shot result view are
  A1-iii-b2. Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_A1_III_DASHBOARD_INTEGRATION_SCOPE_2026-06-23.md`. Tests:
  `src/tests/unit/test_recurrence_ui_suppression.py` (8 cases — execution flag across the
  backends + registry, and `_visible_tabs` drop/keep behavior) + a `/api/train/status`
  execution assertion in `test_recurrence_routes.py`.
- **One-shot regression result view — model-selection A1 enabler (A1-iii-b2, #368)**: the
  final A1-iii slice — a one-shot (recurrence / LMU) model now renders its **regression**
  result instead of a broken classification view. The metrics panel
  (`src/frontend/components/metrics_panel.py`) gains a `model-class-store`-driven callback
  (`render_model_class_metrics`) that, when the active model is `one_shot`, **hides the
  classification surface** (the accuracy / hidden-units / learning-rate cards row +
  both per-epoch loss/accuracy plots — meaningless for a single regression fit) and **shows a
  regression result card** (`_build_oneshot_result`): R² / RMSE / MSE / MAE / Loss formatted as
  plain floats (never a percentage), with a spinner placeholder while the fit runs. The
  `MetricsResult` TypedDict (`backend/protocol.py`) gains the regression keys (`r2` / `mse` /
  `rmse` / `mae`) so `RecurrenceBackend.get_metrics` is type-honest. **Design choice:** a
  dedicated result card (per design D-iii-3 "a regression-metrics card") rather than retrofitting
  the classification cards in-place — which also sidesteps the cascor nested-vs-flat metrics-
  envelope mismatch (the hidden classification cards never read recurrence data). Design-of-
  record: juniper-ml `notes/JUNIPER_CANOPY_A1_III_DASHBOARD_INTEGRATION_SCOPE_2026-06-23.md`.
  Tests: `src/tests/unit/test_recurrence_oneshot_result.py` (7 cases — surface toggle +
  regression card / spinner) + regenerated `snapshots/metrics_panel.txt`; UI sub-suite run
  locally.
- **Dedicated model-selection surface (A1b-1, #368)**: model selection moves from the sidebar
  `nn-model-dropdown` (A1-iv-3a) to a dedicated **`dbc.Modal`** (`size="xl"`, scrollable) holding a
  custom **`dbc.Table`** of models, opened by a compact sidebar **"Model: … ▸ change"** summary +
  button (`src/frontend/dashboard_manager.py`). Each row shows the model label / description,
  category, a lifecycle **status badge** (D8), a **compatibility cell**, and a per-row **Select**
  button (pattern-matching `{"type": "model-select-btn", "index": <key>}`) disabled only for
  *incompatible* models — per ratified **option (a)** a `coming_soon` model stays selectable (D8
  Train-gating deferred to iv-5). The compatibility cell is driven by a new registry
  **`model_reason()`** — the model-perspective inverse of `dataset_reason()` (e.g. "needs 3-D data"
  against a 2-D dataset). Selecting reuses the unchanged `_select_model_handler`
  (`POST /api/model/select` + store mirror) and closes the modal; the downstream dataset gate
  (A1-iv-3b) and one-shot start-body resolver (A1-iv-3c) are **untouched** — they key off the
  stores, not the dropdown, so only the input side moved. A modal was chosen over a Models tab
  because the tab bar caps `active_tab` writers at two and is rebuilt by the one-shot suppression —
  a modal's `is_open` toggle sidesteps both (OQ-1); a custom `dbc.Table` over `dash_table.DataTable`
  because the cells are rich components with no virtualization payoff at this row count (OQ-4). New
  registry helpers: `model_reason()` + `get_dataset_spec()`. Design-of-record: juniper-ml
  `notes/JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md` (D7 / §5.2 / §5.3). Tests:
  `src/tests/regression/test_model_table.py` (15 cases — table builder, status badge, open/close,
  Select → apply + close) + `src/tests/unit/test_model_registry.py` (`model_reason` / `get_dataset_spec`).
  The reactive reverse dataset→model gate, degenerate states, and the search box are A1b-2.
- **Reactive reverse gate + degenerate states (A1b-2, #368)**: completes the bidirectional gate
  (§5.3) on the sidebar side. A new **reverse-gate annotation** under the model summary
  (`nn-model-dataset-hint`) names the model constraint the *currently-selected dataset* imposes —
  e.g. *"3-D Δt-aware models only"* for `equities_seq`, *"2-D models only"* for the 2-D types — the
  dataset-side mirror of the table's per-row `model_reason` greying. It updates on every dataset
  change (a user pick **or** the forward-gate snap from `gate_dataset_options`) via a new registry
  `dataset_model_hint()` helper. The model **table** also now renders a clear **recovery message**
  (§5.8) when a dataset has *no* compatible model (degenerate empty-compatible-set state) instead of
  a silently-unusable all-greyed list — defensive under option (a) (every current seed dataset has a
  compatible model), exercised via an injectable `models=` param. The **optional search box (§5.2)
  is deferred** — it is a FR12 scale affordance with no value at the current two-model population.
  Design-of-record: juniper-ml
  [`notes/JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
  (§5.3 / §5.8). Tests: `src/tests/unit/test_model_registry.py` (`dataset_model_hint`) +
  `src/tests/regression/test_model_table.py` (degenerate recovery, hint handler/seed, callback wiring).
- **Recurrence model goes live + D8 Train-gating (A1-iv-5, #368)**: the `recurrence` (LMU) model is
  flipped from `coming_soon` → **`live`** now that the canopy-routable service is deployed and wired
  in-stack (juniper-deploy #132 sets `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` → `http://juniper-recurrence:8210`),
  so it is now a fully selectable, trainable model. Alongside it lands the **D8 Train-gate** (design
  §5.7): a registry `model_is_trainable()` predicate (status == `live`; unknown → trainable so a
  desync never strands Start, FR9), the Start button **force-disabled** for any non-live model
  (folded into `update_button_appearance` via a new `model-selection-store` Input — a single-point
  combination of training-state + model-status, not a racy second writer), and a `train-gate-notice`
  status reason near the training controls explaining why Start is disabled. A non-live model stays
  *selectable* for inspection (option (a)) but is not trainable. With every shipped model now live the
  gate is exercised via synthetic non-live models (`model_options()` gained a `models=` injectable).
  Tests: `model_is_trainable` + the flipped/repurposed registry assertions
  (`test_model_registry.py`), the Start force-disable + notice handlers + wiring
  (`test_model_table.py`), and the live-status route assertion (`test_model_select.py`).
- **Model-table search box (A1b, #368)**: the model-selection modal gains a **free-text search**
  (`model-search-input`, a `type="search"` box with a native clear) above the table. It filters the
  model rows by **label + family + category + tags** (not label-only, §8) via a new registry
  `model_matches_search()` predicate; a blank query shows everything and a non-empty query that
  matches nothing renders a clear "no models match" message. Search is **folded into the existing
  modal toggle callback** (the one that owns the table container) — typing rebuilds the table
  filtered while the modal stays open, with no racy second writer; `_build_model_selection_table`
  gains a `search=` parameter. This is the §5.2 scale affordance (browse-and-compare at
  dozens-to-hundreds of model variants); it has no functional effect at today's two models but
  completes the surface. Design-of-record: juniper-ml
  [`notes/JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
  (§5.2). Tests: `model_matches_search` (`test_model_registry.py`) + search filtering / no-match
  message / open-honours-search + search-rebuilds-keeping-open (`test_model_table.py`). **This
  completes the A1 model-selection feature end-to-end.**
- **Build provenance on `/v1/health` + `/v1/health/ready`.** The dashboard now
  reports the source `git_sha` and ISO-8601 `build_date` baked into its image
  at build time. New `GIT_SHA` / `BUILD_DATE` / `APP_VERSION` Dockerfile
  build-args become OCI labels (`org.opencontainers.image.revision` /
  `.created` / `.version` — the image previously carried no `revision` /
  `created` / `version` labels at all) plus `JUNIPER_CANOPY_GIT_SHA` /
  `_BUILD_DATE` env vars; a new `provenance` accessor (`src/provenance.py`)
  reads them back (both `null` outside a provenance-stamped image — local dev /
  a bare `docker build`). The values are also passed into `set_build_info(...)`
  (Prometheus `juniper_canopy_build` Info metric) and the shared
  `ReadinessResponse`. Foundation for the ecosystem stale-image-detection
  effort — see juniper-ml
  [`notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md).
  Requires `juniper-observability>=0.4.0`.
- **STATUS BAR — show cascor `completion_reason` (converged vs stalled) on a completed run (Issue #3 diagnosability follow-up, consumes cascor #320)**: a finished training run rendered a bare "Completed" regardless of *why* growth stopped, so a genuine convergence was indistinguishable from a 0-unit stall. cascor #320 now emits a `completion_reason` on `/v1/training/status`; this wires it through canopy end-to-end. `ServiceBackend.get_status` (`src/backend/service_backend.py`) carries the top-level `completion_reason` into the flat `StatusResult` (mirroring the existing `pending_dataset` pass-through; `StatusResult` in `src/backend/protocol.py` gains the field), and `_build_unified_status_bar_content` (`src/frontend/dashboard_manager.py`) appends a short label to the status when `status == "Completed"` via a new `_completion_reason_label` helper: `residual_collapsed`/`below_threshold` → **"Completed — converged"**, `no_candidate` → **"Completed — stalled (0 new units)"**, `early_stopped` → **"Completed — early stopped"**, `max_iterations` → **"Completed — max iterations"**. Display-only (the status color still keys off the base "Completed"); an unknown or missing reason yields a plain "Completed", so a canopy talking to a cascor that predates #320 degrades gracefully. Regression coverage: `src/tests/unit/frontend/test_completion_reason_status_bar.py` (label mapping + the five completed-run suffixes + not-completed / unknown / missing cases) and two `test_service_backend.py` cases (carry-through + `None` when absent).
- **SEC-16 parity — `/metrics` IP allowlist via
  `juniper_observability.MetricsAuthMiddleware`**: canopy now wraps its
  Prometheus `/metrics` ASGI mount in the shared
  `MetricsAuthMiddleware` (promoted from juniper-data #157 and
  juniper-cascor #313 to `juniper-observability` 0.3.0 — see
  juniper-ml #335). The middleware enforces a configurable bare-IP /
  CIDR allowlist with IPv6 zone-id strip and IPv4-mapped IPv6 unwrap,
  so a Docker container appearing as `::ffff:172.18.0.5` matches an
  IPv4 `172.18.0.0/16` allowlist entry; unparseable allowlist entries
  raise a `ValueError` at `Settings()` construction (fail-loud).
  Concrete changes: `src/settings.py` adds
  `Settings.metrics_trusted_ips: list[str] = ["127.0.0.1", "::1"]`
  with a `_validate_metrics_trusted_ips` field validator that
  delegates to `juniper_observability.parse_trusted_networks`;
  `src/main.py` rewraps the existing
  `app.mount("/metrics", get_prometheus_app())` as
  `app.mount("/metrics", MetricsAuthMiddleware(get_prometheus_app(), settings.metrics_trusted_ips))`;
  `pyproject.toml` bumps `juniper-observability>=0.2.0` to `>=0.3.0`
  (first release that exports the middleware). No `EXEMPT_PATHS`
  change required because `SecurityConstants.EXEMPT_PATH_PREFIXES`
  already contained `"/metrics"`, so canopy's `SecurityMiddleware`
  was already letting the path through — the IP allowlist is the
  only gate now. New regression test
  `src/tests/unit/test_metrics_auth_settings_integration.py` (8 cases)
  pins the canopy-side wiring: default loopback, env-var JSON-list
  widening to CIDR, bare IPv6 CIDR, fail-loud on `172.18.0.0/164`
  typos, fail-loud on `"not-an-ip"`, valid mixed CIDR + bare IP
  accepted, shared `parse_trusted_networks` delegation contract, and
  the `/metrics in EXEMPT_PATH_PREFIXES` invariant. Middleware
  behaviour itself is covered by juniper-observability's
  `tests/test_metrics_auth_middleware.py` (22 cases). Closes the
  third trigger-conditioned deferred follow-up in
  juniper-deploy/notes/poc/POC_REMEDIATION_PLAN_2026-05-27.md §6
  ("Add `MetricsAuthMiddleware` to juniper-canopy"). Companion
  juniper-deploy PR (wiring `JUNIPER_CANOPY_METRICS_TRUSTED_IPS`
  into canopy's compose env block + `.env.observability` default)
  is queued separately.
- **Outbound `X-API-Key` for juniper-data calls**: new
  `Settings.juniper_data_api_key` field plus `_check_juniper_data_api_key`
  field validator that resolves the value via `secrets_util.get_secret`
  (Docker-secrets `<NAME>_FILE` indirection). Resolution order:
  `JUNIPER_CANOPY_JUNIPER_DATA_API_KEY_FILE` → direct prefixed env →
  `JUNIPER_DATA_API_KEY_FILE` (shared cross-service) → direct shared
  env → `None`. The resolved value is plumbed through
  `_generate_spiral_dataset_from_juniper_data` and passed as
  `JuniperDataClient(api_key=…)` so every outbound juniper-data call
  carries `X-API-Key`. Closes the gap where canopy never sent an
  outbound key and silently 401'd against juniper-data once
  juniper-deploy#100 enabled juniper-data auth (canopy's own
  `/v1/health` had remained misleading because juniper-data's
  `/v1/health` is auth-exempt). When both prefixed and shared env vars
  are unset the field defaults to `None` and `JuniperDataClient` omits
  the header — preserving the pre-this-PR behaviour for stacks where
  juniper-data auth is disabled. New regression suite at
  `src/tests/unit/test_juniper_data_api_key_resolution.py` (8 cases)
  pins prefixed direct, prefixed `_FILE`, prefixed `_FILE` precedence
  over direct, prefixed `_FILE` missing-file fallthrough to shared,
  shared direct, shared `_FILE`, prefixed-wins-over-shared, and the
  no-env-vars `None` default.
- **CFG-01** (v7 roadmap §13439): new `[demo]` optional-dependencies extra declaring `torch>=2.0.0`. Closes the missing-declaration where `src/demo_mode.py:63` and `src/backend/demo_backend.py:45` `import torch` unconditionally at module level but `pyproject.toml` had no `torch` entry — `pip install juniper-canopy` (no extra) silently produced a wheel that crashed on demo import. Kept out of `[project] dependencies` per the roadmap recommendation to avoid the ~2GB install footprint on production deployments that drive a remote cascor service via `[juniper-cascor]` and never load demo mode (matches the lazy-import convention in `src/backend/data_adapter.py:363,406` whose existing `noqa: F811` comments call out the size cost explicitly). The standalone demo runner `util/juniper_canopy-demo.bash` continues to install torch via `conf/requirements.txt` + the PyTorch CPU index URL for size-optimised bash-script installs; this extra is the canonical path for `pip install juniper-canopy[demo]`. `[dev]` aggregator updated to include `[demo]` so the test suite (`src/tests/unit/test_demo_mode_comprehensive.py:22` etc. import torch unconditionally) resolves under `pip install juniper-canopy[dev]`. No code changes — declaration only.

### Changed

- **SEC-F22 / D2 — two-flag bind attestation (supersedes the unreleased single-flag attestation)**: the startup loopback bind-guard's single operator attestation is replaced by **two** independent booleans (both default `False`), so the guard names the *reason* a non-loopback bind is permitted instead of collapsing two distinct perimeters into one flag: `settings.loopback_publish_attested` (`JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED`) — canopy is reachable only via a loopback-only host publish (the containerized default; verifiable by the juniper-deploy preflight) — and `settings.auth_proxy_attested` (`JUNIPER_CANOPY_AUTH_PROXY_ATTESTED`) — a fronting authenticating reverse proxy terminates access (Phase 4; attestation only). `security.enforce_loopback_bind_guard()` (`src/security.py`, called from `main.lifespan`) now allows a non-loopback bind iff **at least one** attestation is `True` and logs which one permitted it; a non-loopback bind with **neither** still hard-fails uniformly (CRITICAL log + `NonLoopbackBindError`; there is no warning-only mode). Loopback binds (the default) start normally — zero-UX for the shipped posture. **(c) consistency fix:** the root `Dockerfile` default bind host changes from `0.0.0.0` to `127.0.0.1` so a bare `docker run -p 8050:8050` is safe-by-default (matches juniper-cascor); the juniper-deploy compose already sets `SERVER__HOST=0.0.0.0` explicitly and will add the explicit attestation. The `docker-build` smoke step (`.github/workflows/ci.yml`) now runs the container with `-e JUNIPER_CANOPY_SERVER__HOST=0.0.0.0 -e JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED=true` so the image still boots past the guard for the `/v1/health` probe. Regression coverage: `src/tests/unit/test_bind_guard.py` (neither / either / both attest; loopback-safe default; which-attestation-permitted logging) and `src/tests/regression/test_docker_bind_default.py` (loopback-safe Dockerfile default; no baked attestation). **This is one of a three-PR set** — the identical two-flag scheme lands in juniper-cascor and juniper-deploy; the deployed stack needs all three consistent, and this is owner-gated (not auto-merged). Design-of-record: juniper-ml [`notes/JUNIPER_CANOPY_CONTROL_SURFACE_AUTH_AND_NAT_DESIGN_2026-07-03.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_CANOPY_CONTROL_SURFACE_AUTH_AND_NAT_DESIGN_2026-07-03.md) §4 / §8 (D2).
- **CFG-09** (v7 roadmap §13896): `Settings.audit_log_path` default changed from `/var/log/canopy/audit.log` (root-only) to `logs/audit.log` (CWD-relative user-space). Closes the failure class where a fresh non-root install of juniper-canopy crashed at startup inside `src/audit_log.py:51` (parent-directory `mkdir`) or `:53-58` (`TimedRotatingFileHandler` open) because the bake-in default required root privileges to create `/var/log/canopy`. The matching parameter default of `configure_audit_logger(log_path=...)` in `src/audit_log.py:27` was changed in lockstep so direct callers (i.e. anyone invoking the function without passing `settings.audit_log_path`) also get the user-space default. **Not breaking for production**: deployments override via `JUNIPER_CANOPY_AUDIT_LOG_PATH` (pydantic auto-derives from `env_prefix='JUNIPER_CANOPY_'`); the env-var path is unchanged and continues to resolve. No `Settings` model_validator was added — `audit_log.py:51` already does `Path(log_path).parent.mkdir(parents=True, exist_ok=True)`, so adding one in Settings would be duplicate. Switching the default to the canonical XDG state location (`$XDG_STATE_HOME/canopy/audit.log`, default `~/.local/state/canopy/audit.log`) is a deferred follow-up — would require introducing an XDG helper to canopy, which is out of CFG-09's scope. Pinned by new 5-case source-level regression suite at `src/tests/regression/test_cfg_09_audit_log_default.py` (Settings default value, function-parameter default value, no-old-default-in-settings-source, no-old-default-in-audit_log-source, env-var-override-still-resolves).
- Refreshed developer and API documentation for the SEC-F22/SEC-F19 control-surface hardening: `docs/QUICK_START.md`, `docs/ENVIRONMENT_SETUP.md`, `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET.md`, and `docs/api/API_REFERENCE.md` now document the fail-closed loopback bind guard, the two bind attestations `JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED` / `JUNIPER_CANOPY_AUTH_PROXY_ATTESTED`, canonical `JUNIPER_CANOPY_*` settings, and global/per-IP/per-session WebSocket caps.

### Fixed

- **CI DOCKER SMOKE — the smoke container is attested past the bind-guard so the image can boot** (updated for the two-flag migration above): the startup loopback bind-guard (SEC-F22 / D2) refuses to serve on a non-loopback interface without a perimeter attestation, so canopy's `docker-build` "Verify Container Starts" smoke step (`.github/workflows/ci.yml`) — which must reach the container through the published port — would otherwise abort at startup (`NonLoopbackBindError`, raised in `main.lifespan`) and never reach `healthy`. The smoke step now runs `docker run` with `-e JUNIPER_CANOPY_SERVER__HOST=0.0.0.0 -e JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED=true` — scoped to that ephemeral CI container only (no fronting proxy is present; the container just needs to boot for the `/v1/health` probe). Supersedes the interim single-flag smoke attestation (never released). Independent security review of #420, §9.
- **SEC-F19 / D4 WS cap rollback — globally rejected sockets no longer leak reserved per-IP/per-session slots**: the endpoints reserve the per-IP/session counters before awaiting `WebSocketManager.connect()`, but the new stack-absolute global cap can reject later inside `connect()` when `max_connections` is already full. That rejection path closes the socket before it enters `active_connections`, so the endpoint's normal `disconnect()` cleanup no-ops and the reserved counters stayed inflated, letting repeated over-global attempts strand a browser session/IP at its cap until process restart. `connect()` now returns whether it actually registered the socket, and all WS endpoints release the reserved cap slots when registration is rejected or fails before activation. Regression coverage: `src/tests/unit/test_ws_connection_caps.py::TestGlobalConnectionCap::test_global_cap_rejection_releases_reserved_session_slots`.
- **STALE-VERSION SHADOW — `.dockerignore` now excludes *nested* `**/*.egg-info/` so the image stops reporting a stale package version**: `importlib.metadata.version("juniper-canopy")` (the source of `APP_VERSION` → `/v1/health` `version`, the Prometheus `juniper_canopy_build` metric, and the Sentry release) resolved to **0.4.0** while `pyproject.toml` was **0.5.0**. Root cause: a stale, git-untracked `src/juniper_canopy.egg-info` build artifact was COPYed into the image by the Dockerfile's `COPY src/ ./src/`; with `ENV PYTHONPATH=/app/src` ahead of site-packages, `importlib.metadata` resolved that egg-info's `PKG-INFO` (0.4.0) instead of the freshly-installed `juniper_canopy-0.5.0.dist-info`. The existing `.dockerignore` carried `*.egg-info/`, but that pattern only matches the **context root** and silently missed the nested `src/*.egg-info`. Fix: add the `**/`-prefixed `**/*.egg-info/` and `**/*.dist-info/` forms so nested build-metadata dirs are excluded from the build context at any depth (verified against a context containing `src/X.egg-info` — excluded, while real source is kept). Surfaced by the build-provenance `make doctor` work (juniper-ml [`notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md)): doctor correctly reported the image **FRESH** (`git_sha` == source HEAD) while the version string lied — exactly why `git_sha` is the reliable staleness signal. Takes effect on the next canopy image rebuild. Regression coverage: `src/tests/regression/test_dockerignore_egg_info.py` pins the nested-exclusion patterns.
- **TRAINING-CONTROL ERROR SURFACING — a rejected Start/Pause/Stop/Resume/Reset now shows a danger alert instead of silently bouncing the button (the "dead button" class)**: clicking a training-control button that the backend then rejected produced **no** user-visible feedback — the button flipped to its optimistic "pending" state and silently re-enabled, with the failure (and its reason) reaching only a server log or the browser console. This was the canopy half of the cascor dual-path #319 incident: a 401/502 live dataset swap (cascor#331) and an FSM-rejected Start (409) were both invisible from the dashboard. Two transports were silent: (1) the **production-default clientside WS path** (`PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS`, gated `enable_ws_control_buttons=True`) returned `success: true` *synchronously* and resolved the real WS/REST outcome only to `console.warn`; (2) the server-side handler (`_handle_training_buttons_handler`) computed `success: False` into `training-control-action` but **nothing consumed it** and the response body (the reason) was discarded. Fix — one shared outcome surface fed by both transports: a new fixed-position `training-control-outcome-alert` div (offset below `live-switch-outcome-alert`) is filled by a single unconditionally-registered render callback (`_surface_training_control_outcome_handler`) that renders a dismissable `dbc.Alert(color="danger", duration=8000)` naming the command and the reason on failure, and clears on success. The server-side handler now captures the rejection detail via a new `_extract_training_error_detail` helper (prefers cascor's structured `{"error": {"message": …}}` body — which cascor#332 made specific, e.g. "Training cannot be started: Training data not provided" — then raw text, then the exception string; never raises) and stores `{success, command, detail}`. The clientside JS pushes the **real** async outcome into the same store via `dash_clientside.set_props('training-control-action', …)` (the established Phase D §S10 pattern) from the REST-fallback failure branches, so WS rejections, WS-down→REST, and pure-REST failures all surface. All edits are additive on failure branches that previously dead-ended in the console; the success path, optimistic button state, debounce, and timeout sweeper are untouched. Design + root cause: [`notes/CANOPY_TRAINING_CONTROL_ERROR_SURFACING_DESIGN_2026-06-14.md`](https://github.com/pcalnon/juniper-canopy/blob/v0.6.0/notes/CANOPY_TRAINING_CONTROL_ERROR_SURFACING_DESIGN_2026-06-14.md). Regression coverage: `test_dashboard_manager.py` (handler failure now carries `command`+`detail`; `_extract_training_error_detail` JSON / text / bare-exception / never-raises; `_surface_training_control_outcome_handler` clear-on-success / render-danger-on-failure / fallback-detail) and `test_phase_d_button_clientside.py` (JS contains the `set_props` reporting wired into the REST fallback; render callback registered under both transport flags). **Live-verification gate:** the `set_props`→render round-trip is not Python-unit-testable, so this must be confirmed on the deployed stack (force a Start the FSM will reject; confirm the red alert appears with the cascor reason) before merge. **Deferred (noted in the design doc):** short-circuiting the REST double-send on a *definitive* WS command rejection, and an optional green success confirmation.
- **WS-CONTROL PONG — `/ws/control` accepts an inbound heartbeat pong instead of erroring (closes the WS-KEEPALIVE latent note)**: the `/ws/control` receive loop (`src/main.py`) handled inbound `{"type": "ping"}` (replies with a pong) but had no branch for `{"type": "pong"}`. A pong frame carries no `command` key, so it fell through to the command dispatch as `command == ""` and the endpoint replied `Unknown command: ` (`code="unknown_command"`). Dormant today — the server Phase-F heartbeat only pings `/ws/training`, never `/ws/control` (the WS-KEEPALIVE entry below scoped it to `channel="training"` *specifically* to avoid this misfire) — but it would trip the moment the heartbeat is extended to the control channel, or any client sends an unsolicited pong. The loop now treats `{"type": "pong"}` as a silent no-op (debug-logged), mirroring `/ws/training`, which already ignores non-ping frames. Removes the blocker noted in WS-KEEPALIVE so a future control-channel heartbeat is safe. Regression coverage in `test_websocket_control.py::TestWebSocketControlIntegration::test_control_pong_is_noop_not_unknown_command` (send a pong then a valid `start`; the next command response is the `start` success — proving the pong produced no `ok: False` error).
- **#2a APPLY-PARAMS RETRY-AFTER BACKOFF — a 429 now backs off and retries instead of failing the click (completes the half #345 deferred)**: `_apply_parameters_handler` (`src/frontend/dashboard_manager.py`) wraps its `/api/set_params` POST in a 3-attempt retry loop (`DashboardConstants.DASHBOARD_SET_PARAMS_MAX_RETRIES`), but the `429` branch **returned immediately** — it never consumed the retry budget and ignored the `Retry-After` header the limiter faithfully sets (`src/security.py`; `Retry-After: <reset_in>` seconds). After #345 exempted canopy's own self-calls a 429 here is the rarer genuine downstream/cascor-side limit, but a single transient one still failed the user's "Apply Parameters" click outright. The 429 branch now **backs off and `continue`s within the existing loop**: it sleeps `min(Retry-After, DASHBOARD_RETRY_AFTER_MAX_SLEEP_S)` and retries, returning the "Rate limited — please try again in a few seconds" message only *after* the retry budget is exhausted (not on the first 429). The sleep is **bounded** — this runs on a Dash callback thread and the advertised `Retry-After` can be the limiter's full window (tens of seconds), so it is capped at a new `DashboardConstants.DASHBOARD_RETRY_AFTER_MAX_SLEEP_S = 2.0`; a missing/non-numeric header (e.g. the rare RFC 9110 HTTP-date form, which our own limiter never emits) falls back to `DASHBOARD_RETRY_AFTER_FALLBACK_S = 0.5` via a new `_parse_retry_after` helper. **Both constants are provisional first-cut tuning and are flagged in `canopy_constants.py` for revisiting once there is real 429-frequency data from the deployed stack.** Regression coverage in `test_dashboard_manager_handlers.py` (429-then-200 retries and succeeds with the sleep capped at 2.0s even when `Retry-After: 60`; persistent 429 consumes the full retry budget and returns the message only after exhausting — not immediately; a missing header backs off by the 0.5s fallback).
- **#2a RATE LIMIT — exempt canopy's own self-calls (the dashboard was 429-ing itself)**: canopy's `RateLimiter` keys by API-key (falling back to per-IP), but the dashboard's high-frequency `/api/*` polling **and** a user's actions are *all* server-side self-calls from the canopy process carrying the same `X-API-Key` — so they shared one bucket, the polling drained it, and a click (e.g. "Apply Parameters") landing in a drained window got HTTP 429 ("Rate limited"), which also surfaced as the #3 "Error" status. `frontend.internal_api.internal_api_headers()` now attaches a **per-process unforgeable token** (`INTERNAL_REQUEST_HEADER`, a fresh `secrets.token_urlsafe(32)` generated at process start) to every self-call, and `RateLimiter.__call__` (`src/security.py`) **exempts** requests bearing it (constant-time `hmac.compare_digest`). External clients can't forge the token, so they stay rate-limited. Regression coverage in `test_security.py::TestInternalRequestRateLimitExemption` (valid token → exempt across many calls; forged token → limited; missing → limited; round-trip that `internal_api_headers()` carries the exact exempt token). **Deferred:** a `Retry-After`-aware backoff in the apply handler — the exempt removes canopy's own 429 (the dominant source), leaving only the rarer cascor-side case, so it's a small optional follow-up.
- **#2b APPLY-PARAMS HONESTY — stop reporting canopy-local params as "not supported"**: the "Apply Parameters" toast read "Applied 19 of 27 … 8 not yet supported by the backend", listing 8 params the code *already knew* were canopy-only. `CascorServiceAdapter.apply_params` (`src/backend/cascor_service_adapter.py`) built its `skipped` list from every key absent from `_CANOPY_TO_CASCOR_PARAM_MAP`, **including** the keys in `_CANOPY_LOCAL_PARAMS` — which the code's own comment says "should never be reported as skipped". Now `skipped` also excludes `_CANOPY_LOCAL_PARAMS`, so it surfaces only *genuinely* unsupported keys; with an empty `skipped`, the dashboard's honesty toast (`dashboard_manager.py`) simply doesn't fire and the clean "applied" message shows. Reworked `test_apply_params_skipped_surfaced.py::TestAdapterSurfacesSkipped` (which previously asserted the buggy contract — that canopy-local keys appear in `skipped`) to the corrected contract: canopy-local keys are not surfaced, a genuinely-unknown key still is. **Fast-follow (separate PR):** the structural param-surface cleanup — wiring the 3 silently-dropped `SetParamsRequest` params (`nn_output_epochs`/`nn_optimizer_type`/`nn_activation_function_name`), dropping the read-only `cn_training_complete`, and relocating `nn_dataset_*` off the 27-key dict onto `/api/stage_dataset`.
- **#3 STATUS-BAR DIAGNOSABILITY — specific labels instead of a bare "Error"**: a failed `/api/status` poll rendered a generic `"Error"` in the unified status bar regardless of cause, so the dominant case on the deployed stack — a transient **429** from canopy's own rate limiter (see #2a) — was indistinguishable from a real backend outage. `_update_unified_status_bar_handler` (`src/frontend/dashboard_manager.py`) now maps the failure to a specific label via a new `_status_bar_error_tuple` helper: **429 → "Rate Limited"**, **401/403 → "Unauthorized"**, **5xx → "Backend Error"**, other non-200 → "Backend Unavailable", `requests.Timeout` → "Backend Timeout", `requests.ConnectionError` → "Unreachable", anything else → "Error". Regression coverage in `test_dashboard_manager.py::TestStatusBarErrorDiagnosability` (10 cases across status codes + exception types + the unchanged 200 happy path). **Deferred follow-up:** rendering the circuit-breaker-open state as "Unreachable" rather than "Stopped" needs an `error`/unreachable signal plumbed through the `StatusResult` schema (`backend/protocol.py` + `service_backend.get_status`), so it's a separate PR rather than bundled here.
- **#4 DATASET-APPLY — numeric inputs now reach `/api/stage_dataset` (a modified dataset trains)**: editing a dataset's element count / noise and clicking **Apply Dataset** never changed the trained dataset on the real backend — only a dropdown `dataset_type` change took effect. Two coupled causes in `src/frontend/dashboard_manager.py`: (1) **Apply-Dataset had no force-blur**, so a numeric value typed and then committed by *clicking* the button (without tabbing out) was still the Dash/React `null` at `State()`-read time — the same gap fixed for Apply-Parameters in Issue #2; (2) `apply_dataset` then ran a blanket `{k: v for ... if v is not None}` drop that silently discarded those `null` numerics, leaving only `dataset_type`. Fix: the existing force-blur clientside callback now fires on **both** `apply-params-button` and `apply-dataset-button`, and `apply_dataset` seeds the payload with `nn_dataset_type` unconditionally (cascor `_reload_dataset` requires it) while including the optional numeric / spiral fields only when present. Regression coverage in `test_dashboard_manager.py::TestDatasetApplyNumericCommit` (force-blur wired to both buttons; payload always sends `dataset_type`; blanket None-drop removed) plus an updated input assertion in `tests/ui/test_apply_blur_clientside.py`. The companion relocation of `nn_dataset_*` off `/api/set_params` is the #2b change.
- **WS-KEEPALIVE — server-side Phase F heartbeat (completes the #3 "WS: Reconnecting" idle-timeout fix)**: the browser client already replied to server `{"type": "ping"}` frames with a pong (`src/frontend/assets/websocket_client.js`), but nothing on the server ever *sent* those pings, so the `/ws/training` receive loop (`src/main.py` — `asyncio.wait_for(websocket.receive_text(), timeout=idle_timeout_seconds)`, default 120s) idled out on any quiet-but-healthy training stream and the client flapped Connected→Reconnecting. `src/main.py` now starts a `_websocket_keepalive_loop` task in the application lifespan that calls `websocket_manager.broadcast_ping(channel="training")` every `websocket.heartbeat_interval` seconds (the previously-dormant 30s setting, well under the 120s idle timeout) and cancels it on shutdown; the client's existing pong resets the server idle timer. `WebSocketManager.broadcast()` / `broadcast_ping()` gain an optional `channel` filter so the heartbeat is scoped to the training channel only — `/ws/control` has no idle timeout and would mis-handle the resulting pong as an unknown command. Regression coverage: `test_main_import_and_lifespan.py::TestWebSocketKeepalive` (loop pings the training channel periodically and survives a transient broadcast error) and `test_websocket_comprehensive.py::TestHeartbeatFunctionality` (channel-scoped ping reaches training but not control; no-channel still pings all). Latent adjacent issue noted for a separate PR: the `/ws/control` endpoint treats an inbound `{"type": "pong"}` as an unknown command — dormant today because the heartbeat never pings control.
- **#1 TAB-FEEDBACK-LOOP — collapse to one tab-persistence system + equality-guard the restore callback**: clicking one tab then another re-opened the previous tab (deterministic Snapshots→Dataset). Two compounding causes in `src/frontend/dashboard_manager.py`: (1) the clientside callback that restores `visualization-tabs.active_tab` from `layout-state-store` (Input on the Store's `data`) re-asserted the tab on *every* Store change — including the echo from the write callback that stamps the Store on each tab change — re-triggering every `Input("visualization-tabs", "active_tab")` callback and racing the `allow_duplicate` active_tab outputs; (2) a redundant *second* persistence system (hand-rolled `localStorage['juniper_canopy_active_tab']` with an `active_tab`→`active_tab` self-edge writer plus a `params-init-interval` mount restore) raced the Store restore at mount. Fix: the restore callback now takes the current tab as `State("visualization-tabs", "active_tab")` and returns `no_update` when `state.active_tab === currentTab` (mirrors the write callback's existing `prev.active_tab === activeTab` guard), and the legacy localStorage pair is deleted so `layout-state-store` (`storage_type="local"`) is the single source of truth. Net: `visualization-tabs.active_tab` now has exactly two writers (Store restore + tutorial-link trigger) and a single mount-time restore. Regression coverage in `test_dashboard_manager.py::TestLayoutStatePersistence`: legacy key fully removed, restore callback equality-guarded, exactly two active_tab outputs.

### Tests

- **Lifted whole-`src` per-file coverage to satisfy the new gate — no production-code change.** The unit
  lane's overall pooled statement coverage rose **87.5% → 98.5%** (coverage.py total **85.8% → 97.5%**),
  bringing every source file to **≥90% statement** and every sub-module to **≥95% pooled**. ~520 new
  deterministic, offline unit tests were added for the previously under-covered files:
  `main.py` (76.6 → 99.3%; FastAPI routes / WebSocket handlers / lifespan via `TestClient`),
  `frontend/dashboard_manager.py` (77.2 → 99.9%; Dash inner-callback bodies invoked directly),
  `demo_mode.py` (88.2 → 99.3%),
  `backend/{cascor_service_adapter,training_monitor,demo_backend,service_backend}.py` (→ 100%),
  `frontend/components/{parameters_panel,candidate_metrics_panel,network_evolution,decision_boundary,network_editor_panel,replay_player_panel,dataset_plotter}.py`
  (→ 100%), plus the WebSocket-audit helpers in `audit_log.py` and the API-key branch of
  `frontend/internal_api.py`. UI (`src/tests/ui/`, Playwright) tests remain out of the coverage lane by
  design (session-fixture event-loop leak); no `get_layout()` / panel layout was touched.

### Security

- **SEC-F19 log hygiene — hash the `canopy_session` cookie before logging (never log the raw value)**: `WebSocketManager.check_per_session_limit` (`src/communication/websocket_manager.py`) logged a raw 8-char prefix of the anonymous `canopy_session` cookie (`session_key[:8]`) when the per-session cap tripped. That cookie is a signed Starlette session token, so even a prefix in a log line is an avoidable session-identifier leak. A new `_hash_session_key_for_log` helper now emits a short, non-reversible tag instead — keyed HMAC-SHA256 over the raw cookie with a per-process random secret (`_LOG_HASH_KEY`), truncated to 12 hex chars — so the logged digest is not an offline-computable function of the cookie and does not correlate across process restarts, mirroring the cascor sibling that hashes its identity before logging (`juniper-cascor src/api/workers/security.py`). Regression coverage: `src/tests/unit/test_ws_connection_caps.py::TestPerSessionLogHygiene`. Independent security review of #420, §9.
- **SEC-F22 / D2 — startup loopback bind-guard (the loopback bind is now an enforced invariant)**: canopy's browser training-control gate (`/api/train/*`, `/ws/control`) authenticates the same-origin browser by `Origin` + CSRF, both of which are forgeable by an in-network **non-browser** client (spoofable `Origin`, anonymously-mintable CSRF token — audit HO-6), so the **only** effective control is the loopback bind. That bind was an implicit default, not an enforced invariant — flipping `BIND_HOST=0.0.0.0` silently made the control surface in-network- (or internet-) reachable. A new startup guard (`src/security.py`: `is_loopback_host` / `enforce_loopback_bind_guard` / `NonLoopbackBindError`, called from `main.lifespan`, mirroring the E-8 `enforce_dependency_floors` fail-loud idiom) now **refuses to start** (CRITICAL log + raise; fail-closed) when `settings.server.host` (`JUNIPER_CANOPY_SERVER__HOST`) is a non-loopback interface (anything not in `127.0.0.0/8`, `::1`, or `localhost`) **unless** at least one of two operator attestations (both default `False`) is `True` — `settings.loopback_publish_attested` (`JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED`, reachable only via a loopback-only host publish) or `settings.auth_proxy_attested` (`JUNIPER_CANOPY_AUTH_PROXY_ATTESTED`, a fronting authenticating proxy terminates access); the attested non-loopback path logs a loud WARNING naming which attestation permitted it. Loopback binds (the default) start normally, so this is zero-UX for the shipped posture. Implemented **inline in canopy** (no new dependency). Regression coverage: `src/tests/unit/test_bind_guard.py`. Design-of-record: juniper-ml [`notes/JUNIPER_CANOPY_CONTROL_SURFACE_AUTH_AND_NAT_DESIGN_2026-07-03.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_CANOPY_CONTROL_SURFACE_AUTH_AND_NAT_DESIGN_2026-07-03.md) §4 / §8 (D2); implementation note: [`notes/JUNIPER_CANOPY_CONTROL-SURFACE-HARDENING_SEC-F22-F19_NOTE_2026-07-04.md`](https://github.com/pcalnon/juniper-canopy/blob/v0.6.0/notes/JUNIPER_CANOPY_CONTROL-SURFACE-HARDENING_SEC-F22-F19_NOTE_2026-07-04.md).
- **SEC-F19 / D4 — global + per-session WebSocket connection caps (kills the shared-NAT self-DoS)**: Docker NAT collapses every WS client to the bridge-gateway IP (audit HO-3), so the existing per-IP cap (`max_connections_per_ip=5`) is shared across all users behind the gateway — one client's five sockets exhaust the cap for everyone (a live self-DoS). `src/communication/websocket_manager.py` now adds, alongside the per-IP cap: (a) the stack-absolute **global** cap `max_connections` (=50) enforced in `connect()` — the single admission choke point shared by `/ws/training`, `/ws/control`, `/ws` — rejecting the N+1th connection stack-wide with close code `1013`; and (b) a **per-session** cap `max_connections_per_session` (=5, new `WebSocketSettings` field) keyed on the anonymous `canopy_session` cookie read from the WS handshake, restoring per-client fairness where the per-IP cap is inert (one session can no longer starve another behind the same gateway). A cookieless first connection is allowed and left to the global cap as the backstop. The three endpoints call a new `check_connection_limits()` (per-IP then per-session, rolling back the per-IP slot on a per-session rejection so a rejected attempt can't leak the per-IP counter); each endpoint keeps its existing close-reason (`/ws/control` stays opaque per M-SEC-06). The per-IP cap is retained but re-scoped honestly (a code comment + this note): it is **inert behind NAT** — DoS-dampening, **not** authentication. Regression coverage: `src/tests/unit/test_ws_connection_caps.py`. Design-of-record §5 / §8 (D4). **Deferred (Phase 4, owner-gated, NOT in this PR):** X-Forwarded-For-from-trusted-proxy (D6) and a real dashboard login / fronting proxy (D7) — the only mechanisms that restore genuine per-client identity / close SEC-F22 for the remote/multi-user case.

---

## References

- [CHANGELOG.md](../../CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-canopy_v0.6.0.md`

<!-- Auto-generated release-train DRAFT (util/release_train/notes_render.py).
     Source template: notes/templates/TEMPLATE_SECURITY_RELEASE_NOTES.md.
     Complete or delete these template sections before the release ceremony:
       - Affected Versions
       - Remediation / Upgrade Instructions
       - Testing & Quality
       - Upgrade Recommendation
-->
