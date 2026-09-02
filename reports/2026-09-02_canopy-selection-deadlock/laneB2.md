# Lane B2 — Adversarial review by AMPUTATION / BLIND SPOTS

Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane B.
Lens: what did four proposers and three verifiers all fail to see?
Date: 2026-09-02. Repos read-only; nothing edited.

## Artifacts

Two runnable probes (scratchpad, not repo — the brief forbids repo edits):

- `probe_tabs.py` — renders `DashboardManager._visible_tabs("live"/"one_shot")` and reports which
  `_GATED_POLL_INTERVALS` output ids survive the one-shot rebuild.
- `probe_gate.py` — three claims: C1 registry reachability property, C2 availability-gate no-snap,
  C3 one-shot generator-name alias gap. Output transcribed inline below.

Run: `cd juniper-canopy/src && conda run -n JuniperCanopy1 python <path>/probe_gate.py`

---

## NEW FINDINGS

### B2-1 (CRITICAL — the recommended fix does not work in the deployed stack)

**The availability gate disables `equities_seq` in the shipped docker image, and the snap the fix
relies on then declines to fire.**

Chain:

1. `juniper-data/requirements.lock` does **not** contain `yfinance`, and `juniper-data/Dockerfile:26,31`
   builds the image as `pip install -r requirements.lock` then `pip install --no-deps .` — extras are
   never installed. So `EQUITIES_DEPS_AVAILABLE = False`
   (`juniper-data/juniper_data/generators/equities/generator.py:59-65`).
2. `equities_seq.is_available()` mirrors it
   (`juniper-data/juniper_data/generators/equities_seq/generator.py:74`), so `GET /v1/generators`
   reports `equities_seq: available=false` (`juniper-data/juniper_data/api/routes/generators.py:177-198`).
3. `juniper-canopy/src/frontend/dashboard_manager.py:2702` composes
   `apply_availability_gate(gated_dataset_options(model_key), self._fetch_generators())`. The
   availability gate (`juniper-canopy/src/dataset_schema.py:268-285`) disables `equities_seq`.
4. `_gate_dataset_options_handler` (`dashboard_manager.py:2703-2706`):

   ```python
   enabled = [option["value"] for option in options if not option.get("disabled")]
   if current_value in enabled or not enabled:
       return options, dash.no_update      # <-- `not enabled` branch: NO SNAP
   ```

Measured (`probe_gate.py` C2, model=`recurrence`, current=`spirals`, equities_seq unavailable):

```
spirals        disabled=True  'Spirals — needs a 2-D model'
xor            disabled=True  'XOR — needs a 2-D model'
mnist          disabled=True  'MNIST — needs a 2-D model'
circles        disabled=True  'Circles — needs a 2-D model'
moons          disabled=True  'Moons — needs a 2-D model'
equities_seq   disabled=True  'Equities (sequence) — unavailable in this deployment'
enabled set          : []
returned dropdown val: dash.no_update      <-- NO SNAP
```

**Why it matters.** The round's fix rests on "the existing dead-dataset snap at `:2702-2706` repairs
the dataset". That premise is false whenever the only compatible dataset is unavailable — which is the
default in the container that juniper-deploy actually runs. Post-fix the user selects Recurrence and
lands on `(recurrence, spirals)` with a **100 %-disabled dropdown still displaying `spirals`**. That is
strictly worse than today, where the recurrence row is at least honestly disabled. Then B2-3 fires.

**Must be added to the fix.** The `not enabled` branch must not be silent: either keep the model
un-selectable when its compatible∩available set is empty, or snap + surface a blocking notice naming
the missing extra. Neither is in the proposal.

### B2-2 (HIGH — the proposed guardrail is vacuous, three ways)

The guardrail is "a reachability-closure property test asserting every `compatible()` pair is
reachable, run over synthetic registries with ≥3 partition components".

**(a) It passes on the shipped registry today, with the deadlock intact.** Measured (`probe_gate.py` C1):

```
model=cascor      enabled=['circles','mnist','moons','spirals','xor']  compatible=[same]  match=True
model=recurrence  enabled=['equities_seq']                             compatible=[same]  match=True
--> property holds on shipped registry: True
```

`model_registry.gated_dataset_options("recurrence")` already returns `equities_seq` **enabled**. The
deadlock is not in the registry — it is in `_build_model_selection_table`
(`dashboard_manager.py:3050`, `disabled=not is_compatible`) and in the `_gate_dataset_options_handler`
snap. A property stated over `model_registry` functions cannot see either.

**(b) A synthetic registry structurally cannot drive the gate.** Injectability is inconsistent:
`compatible_models` (`model_registry.py:321`), `compatible_datasets` (`:329`), `model_options` (`:222`),
`model_is_trainable` (`:232`) and `dataset_model_hint` (`:382`) take injectable tuples — but
`get_model_spec` (`:264`), `get_dataset_spec` (`:276`), `dataset_type_options` (`:200`),
`dataset_default_params` (`:209`) and **`gated_dataset_options` (`:408`)** do not; they read the module
globals `MODELS` / `DATASET_TYPES`. The guardrail as specified must monkeypatch module state or it
tests a different code path from the one that ships.

**(c) It cannot observe B2-1.** `_gate_dataset_options_handler` calls `self._fetch_generators()`
(`dashboard_manager.py:2712-2733`), a live HTTP GET. Under test that raises → `generators = []` →
`availability_map([])` → `{}` → `is_generator_available` returns `.get(name, True)` → **True**. The
fail-open fallback means the guardrail always runs with every generator available, so the `not enabled`
branch that fires in production is unreachable from the test.

**Must be added.** The property has to be asserted over the *pair of callback handlers* with an
injected generator list, including at least one all-unavailable case, and `gated_dataset_options` needs
the same `dataset_types=` / `models=` injectability its siblings already have.

### B2-3 (HIGH — the one-shot Start body skips the generator-name alias map)

`DashboardManager._resolve_oneshot_start_body_handler` (`dashboard_manager.py:2668-2685`):

```python
dataset_ref: dict[str, object] = {"generator": dataset_generator}   # RAW dropdown value
```

Its two sibling handlers both alias: `_render_dataset_params_handler` (`:2769`) and
`_apply_dataset_handler` (`:2836`) call `generator_name_for_type()`. This one does not.
`GENERATOR_NAME_ALIASES = {"spirals": "spiral", "moons": "moon"}` (`dataset_schema.py:97-100`), and
juniper-data has **no** alias layer — `datasets.py:99` rejects anything not a `GENERATOR_REGISTRY` key,
and the keys are `spiral` / `moon`. juniper-recurrence forwards the name verbatim
(`juniper-recurrence/juniper_recurrence/data.py:45`).

Measured (`probe_gate.py` C3):

```
dropdown=spirals      -> sent generator='spirals'      valid_juniper_data_key=False
dropdown=moons        -> sent generator='moons'        valid_juniper_data_key=False
dropdown=equities_seq -> sent generator='equities_seq' valid_juniper_data_key=True
```

Masked today only because `equities_seq` (identity) is the sole one-shot-reachable value. Reachable
after the fix via **B2-1** (dropdown retains `spirals` on a recurrence backend) and **B2-4** (split-brain
offers `spirals` while the class store says `one_shot`). Failure mode is an upstream 400
"Unknown generator 'spirals'", not the shape error a developer would expect.

### B2-4 (HIGH — page reload split-brains the two selection stores)

`model-selection-store` is `storage_type="memory"` seeded to `DEFAULT_MODEL_KEY`
(`dashboard_manager.py:1842`); `model-class-store` is memory-seeded `"live"` (`:1839`) but is hydrated
from the server by `hydrate_model_class` → `_resolve_model_class` → `GET /api/train/status.execution`
(`:2275-2296`, `:2515-2531`). Nothing hydrates the selection store — FR15 (already flagged as
"unimplemented"). The **consequence** was not reported:

On a browser refresh while the live backend is recurrence:

| store | value after mount | source |
| --- | --- | --- |
| `model-selection-store` | `"cascor"` | memory seed |
| `model-class-store` | `"one_shot"` | live `/api/train/status` |

- `gate_dataset_options` keys off the **selection** store (`:2607`) → offers the five 2-D datasets, keeps `spirals`.
- `resolve_oneshot_start_body` keys off the **class** store (`:2636`) → builds `{"dataset": {"generator": "spirals"}}`.
- `nn-model-summary` is seeded `_initial_model_summary()` (`:1221`) → the sidebar reads **"Active: CasCor"** against a live LMU backend.
- Cascade tabs are suppressed (class store is right) while the sidebar/model table are wrong.

Start then POSTs a rank-2 generator ref to the LMU service. With B2-3 it fails as an unknown-generator 400.

### B2-5 (HIGH — selecting Recurrence is a silent no-op when the service URL is unset, and the UI still re-gates)

`settings.recurrence_service_url` defaults to `None` (`juniper-canopy/src/settings.py:261`).
`_selection_targets_recurrence` requires it (`main.py:3659-3672`), so `_swap_backend` takes its no-op
branch (`main.py:3705-3708`) and returns `swapped: False`, `backend: "demo"|"service"`,
`execution: "live"`.

`_select_model_handler` (`dashboard_manager.py:2884-2897`) reads only `nn_model`, `execution` and
`status`; `_model_summary_text` (`:2932-2938`) reads `nn_model` + the **registry** `status` (always
`"live"` for recurrence). **Neither reads `swapped` or `backend`.** Result:

- sidebar: "Active: Recurrence (LMU)"
- `model-selection-store` = `"recurrence"` → dataset gate forces `equities_seq` (or B2-1's dead dropdown)
- `model-class-store` = `"live"` → all cascade tabs stay, `oneshot-start-params-store` stays `None`
- live backend: still cascor/demo, training a cascade on spirals

Today this is unreachable (the fix's whole point). After the fix, any deployment without
`RECURRENCE_SERVICE_URL` — the default, including plain `python -m juniper_canopy` and the demo
fallback — reaches it on the first click. Answers Direction 2: demo mode has no separate model
registry, so this *is* the demo-mode failure.

### B2-6 (MEDIUM-HIGH — eight missing backend methods, not one; `BackendProtocol` under-declares)

The round flagged `stage_dataset`. The real list of methods `main.py` calls **unguarded** that
`RecurrenceBackend` (`juniper-canopy/src/backend/recurrence_backend.py`) does not implement:

| method | call site | route |
| --- | --- | --- |
| `stage_dataset` | `main.py:3995` | `POST /api/stage_dataset` (flagged) |
| `cancel_pending_dataset` | `main.py:4012` | `DELETE /api/cancel_pending_dataset` |
| `get_experimental_functions` | `main.py:4051` | `GET /api/admin/experimental_functions` |
| `set_experimental_functions` | `main.py:4073` | `POST /api/admin/experimental_functions` |
| `swap_dataset_live` | `main.py:4117` | `POST /api/live_dataset_swap` |
| `cancel_swap_dataset_live` | `main.py:4143` | `DELETE /api/live_dataset_swap` |
| `get_dataset_swap_events` | `main.py:4180` | dataset-swap events |
| `get_snapshot_dataset_swaps` | `main.py:4209` | snapshot swap list |

`DemoBackend` stubs **all eight** (`backend/demo_backend.py:347-383`). `backend/protocol.py:231-327`
declares only 20 methods and none of these, so no type check catches the gap. Every one of these
routes wraps in `except Exception` → 500 + `error_id` + a full traceback at ERROR level.

Highest-impact of the set: `GET /api/admin/experimental_functions` is called on **every page mount** by
`load_reconcile_experimental_functions` (`dashboard_manager.py:4998-5040`). On a recurrence backend that
is a 500 + logged traceback per page load, and the user is shown
**"Could not reach backend; experimental functions disabled."** — a false diagnosis; the backend is
reachable, the method does not exist.

Contrast: `regenerate_dataset` / `regenerate_dataset_from_generator` / `import_dataset` **are**
`hasattr`-guarded and 501 cleanly (`main.py:1461, 1486, 1524, 1618`) — the guard idiom exists, it just
was not applied to the eight above.

Also (Direction 4): `_gate_live_switch_button_handler` (`dashboard_manager.py:5987-5994`) gates the
Live Dataset Switch on `experimental_functions AND is_running` only — **nothing about model class or
backend type**. It is kept disabled today only as a side effect of the experimental-functions read
500-ing, i.e. by accident.

### B2-7 (MEDIUM-HIGH — vacuous snapshot save/restore on the recurrence path)

`POST` snapshot save gates cascor's adapter on `backend_type == "service"` (`main.py:2345`), so
recurrence falls to the h5py fallback (`main.py:2372-2415`), which writes:

- `training_state` scalar attrs, and
- `_extract_meta_params()` — **cascor** `nn_*` / `cn_*` meta-params (learning rate, max hidden units,
  candidate pool size…),

and **no LMU state at all**: no readout weights, no `d`/`theta`/`ridge`, no dataset reference. It then
returns `"message": "Snapshot created successfully"` and logs `_log_snapshot_activity(... "mode": "real")`
(`main.py:2427-2437`).

Restore (`main.py:2589-2660`) reads them back, calls `training_state.update_state(**restored_attrs)`
and `backend.apply_params(**meta_params)`. `RecurrenceBackend.apply_params`
(`recurrence_backend.py:285-299`) recognises only `d`/`theta`/`ridge` and **silently ignores the rest**,
returning `{"ok": True, "data": {}}` — which the route never inspects. It returns
`{"status": "success", "mode": "real"}` and broadcasts a `snapshot_restored` WebSocket event.

Net: a green save, a green restore, a WS broadcast, restored-looking epoch/phase in the status bar —
and zero model state recovered. Textbook vacuous-pass, in the same class as the cascor snapshot-integrity
work. The Snapshots tab is **not** in `_CASCADE_ONLY_TAB_IDS` (`dashboard_manager.py:427`), so it is
fully visible for a one-shot model.

Related, minor: the service-only guards return "Demo mode is not supported" / "Not available in demo
mode" (`main.py:2721`, `4263`, `4292`, `4314`) — misattributed on the recurrence path.

### B2-8 (MEDIUM — the model swap strands `active_tab` on a deleted tab)

`_visible_tabs` (`dashboard_manager.py:2435-2449`) drops the five cascade-only tabs for `one_shot` and
its docstring says it "deliberately does NOT touch `active_tab` … (Resetting a hidden active tab on a
*runtime* model swap belongs with A1-iv's model-switch flow.)" — A1-iv shipped the runtime swap without it.

There are exactly three `visualization-tabs.active_tab` writers (`dashboard_manager.py:3492`, `:3514`,
`frontend/components/hdf5_snapshots_panel.py:1270`); none keys on model class.

dbc 2.0.4's `Tabs` self-heal is
`useEffect(() => { setProps && active_tab === undefined && setProps({active_tab: children[0].tab_id}) }, [])`
— **empty dependency array**, and it only fires when `active_tab` is `undefined`. A stale value naming a
removed tab is never corrected; `Tab.Container activeKey` then matches no pane → blank content area.

Reachability: `TAB_SIDEBAR_CONFIG` (`dashboard_manager.py:324-410`) makes `sidebar-nn-section` — which
contains the model picker `sidebar-nn-model` (`:1244`) — visible on **metrics, topology, dataset**. So a
user can select Recurrence *from the Topology tab*, whereupon Topology is deleted and `active_tab` stays
`"topology"`: empty right panel, and `update_sidebar_visibility` (`:2470-2484`, `prevent_initial_call=True`,
Input `active_tab`) never re-fires, so the sidebar keeps the topology layout.

Persistence (Direction 3): `layout-state-store` is `storage_type="local"` and the restore clientside
callback (`:3501-3518`) writes the persisted tab back with **no validation against the rendered tab
set**, so the dead-tab state is re-entered on every reload.

Note the dataset-type dropdown lives in `sidebar-nn-spiral-dataset`, which `TAB_SIDEBAR_CONFIG` shows on
the **`dataset` tab only** — so on metrics/topology the snap the fix relies on happens entirely
off-screen.

### B2-9 (MEDIUM — the generators proxy is unauthenticated; its fallback list has no `equities_seq` and no schemas)

`main.py:1697` fetches `f"{data_url}/v1/generators"` with **no `X-API-Key`**, and `/v1/generators` is
**not** in juniper-data's `EXEMPT_PATHS` (`juniper-data/juniper_data/api/constants.py:72-80`).
`SecurityMiddleware` authenticates it whenever a key is configured
(`juniper-data/juniper_data/api/middleware.py:190-212`). On 401 the route falls back to a hardcoded
four-entry list (`main.py:1709-1716`): `spiral, xor, circles, moon` — **no `equities_seq`, no `mnist`,
and no `schema` key on any entry**.

Consequences on the newly-reachable path:

- `is_generator_available("equities_seq", …)` → name absent → fail-open `True`. Availability gate becomes a no-op.
- `_generator_schema("equities_seq", …)` → `{}` → `parse_schema_fields` → `[]` →
  `_build_schema_param_inputs` renders **"No adjustable parameters — sensible generator defaults are used."**
  (`dashboard_manager.py:2789-2791`) for the LMU's *only* dataset, which in fact has ~15 parameters
  (`EquitiesSeqParams` extends `EquitiesParams`).

Second-order: juniper-data's failed-auth throttle is 10 failures / 60 s
(`juniper-data/juniper_data/api/constants.py:125-126`); `_fetch_generators` re-fetches every 30 s per
DashboardManager (`_GENERATORS_CACHE_TTL_S = 30.0`, `dashboard_manager.py:2710`), so canopy can throttle
itself out of the endpoint.

### B2-10 (MEDIUM — user-entered generator params are silently discarded on the one-shot path)

`_resolve_oneshot_start_body_handler` (`dashboard_manager.py:2668-2685`) builds `params` **only** from
`dataset_default_params(dataset_generator)` — the frozen registry seed
`{"max_symbols": 5, "regression_target": "return"}` (`model_registry.py:148`). The schema-driven
`{"type": "nn-gen-param", …}` inputs are read only by `_apply_dataset_handler`
(`dashboard_manager.py:2827-2860`), which POSTs `/api/stage_dataset` → `backend.stage_dataset` →
AttributeError → 500 on recurrence.

So on `(recurrence, equities_seq)` **every** sidebar parameter input (lookback, start/end date,
train_ratio, symbols, …) is decorative: editing it changes nothing, and the only path that would have
consumed it 500s.

### B2-11 (LOW-MEDIUM — the recurrence control explanations never reach the user)

`RecurrenceBackend.stop_training` / `pause_training` / `resume_training`
(`recurrence_backend.py:179-187`) return `ControlResult(ok=False, message="a recurrence fit is a
non-interruptible one-shot solve and cannot be stopped")` — the reason is in **`message`**.
`_control_result_failure` (`main.py:3378-3390`) reads `result.get("error") or "command failed"`. So all
three carefully-written explanations are discarded and the user gets
**"Training could not be stopped: command failed"** (409) during a 300 s blocking LMU fit.

### B2-12 (LOW-MEDIUM — the restart modal displays a disabled option as its selected value)

`restart-ds-type`'s options are frozen at layout build as `gated_dataset_options(DEFAULT_MODEL_KEY)`
(`dashboard_manager.py:5422`) — cascor's gating, in which `equities_seq` is
`{"disabled": True, "label": "Equities (sequence) — needs a 3-D model"}`. `open_restart_confirm_modal`
(`:5260-5294`) writes `restart-ds-type.value` from the sidebar dropdown, i.e. `"equities_seq"`. The
operator sees a dropdown whose current value is a greyed option whose reason contradicts the active
model, and can only re-select a 2-D dataset. `RESTART_MODAL_DATASET_FIELDS` (`:488-494`) also carries
spiral-only `rotations` / `n_spirals`, and the confirm path routes through `/api/stage_dataset` (B2-6).

### B2-13 (Direction 7 — the fix scales, but two unguarded hazards ride with the 5 hidden generators)

Adding `multi_sine` / `mackey_glass` / `ar_p` / `irregular_sine` / `delay_product` keeps the graph at
two components (all rank-3 regression; `temporal_ok` only constrains `irregular`), so the unary-predicate
fix is sufficient for the deadlock. Two things are not:

1. **`dataset_default_params` is a hand-maintained per-dataset bound with no gate.** Its seed exists
   because juniper-data's default universe "would blow the 300 s train timeout" (`model_registry.py:144-148`);
   `_resolve_oneshot_start_body_handler` omits `params` entirely for any dataset without a seed
   (`dataset_default_params` → `{}`, `model_registry.py:216-219`). Adding a rank-3 generator without a
   seed silently reintroduces the timeout class against `_DEFAULT_TRAIN_READ_TIMEOUT = 300.0`
   (`backend/recurrence_service_adapter.py`).
2. **There is no drift test between canopy's `DATASET_TYPES` and juniper-data's `GENERATOR_REGISTRY`.**
   Grep of `juniper-canopy/src/tests` finds none. The two already disagree on `equities_seq`
   (`task_type` `regression` in `model_registry.py:141` vs `classification` in
   `juniper-data/juniper_data/api/routes/generators.py:113-119`), and each new generator hand-copies
   `ndim` / `task_type` / `temporal` with nothing checking them. Also, per the standing ecosystem note,
   `mackey_glass` accepts a seed and ignores it — exposing it would ship a non-reproducible dataset with
   no warning.

---

## REFUTED HYPOTHESES (what I searched and found nothing)

Recorded so the round does not re-spend effort here.

- **R1 — "`regression_target="return"` is inert because equities_seq's `y_*` is one-hot."** FALSE.
  `sequence_data_from_arrays` prefers `y_reg_{split}` over `y_{split}`
  (`juniper-recurrence/juniper-recurrence-model/juniper_recurrence_model/data.py:75-81`). The seed is effective.
  (Residual nit: `DatasetDescriptor.output_dim` is then `y_reg.shape[1]` = 1, which
  `RecurrenceBackend.get_dataset` maps to `"num_classes": 1` — a nonsense label on the dataset readout.)
- **R2 — "the one-shot tab rebuild deletes a poll-gate Output id and kills the whole gate callback."**
  Deletion confirmed (`probe_tabs.py`: `candidate-metrics-panel-update-interval` is present for `live`
  and absent for `one_shot`), but harmless: dash-renderer's `applyProps` does
  `var itempath = getPath(paths, id); if (!itempath) { return false; }` — it **skips** the missing output
  and applies the rest. The other 11 outputs still land. Not a defect.
- **R3 — "demo mode is a one-way door once you pick a model."** FALSE. `create_backend` re-resolves
  `force_demo` from settings on every call (`backend/__init__.py:75-85`), so selecting cascor rebuilds
  `DemoBackend`.
- **R4 — "`regenerate_dataset` / `import_dataset` AttributeError on recurrence."** FALSE — both are
  `hasattr`-guarded and return 501 (`main.py:1461, 1486, 1524, 1618`).
- **R5 — "the metrics panel breaks on regression-only metrics / a 1-point history."** FALSE — A1-iii-b2
  ships a dedicated one-shot regression card (`frontend/components/metrics_panel.py:480, 768`).
- **R6 — "`EquitiesSeqParams` rejects `regression_target` / `max_symbols`."** FALSE — both are inherited
  from `EquitiesParams` (`juniper-data/juniper_data/generators/equities/params.py:79, 93`).
- **R7 — "the 5s `shutdown()` join leaks a fit thread across a swap."** Not reachable:
  `_swap_backend` refuses with 409 while `is_training_active()` (`main.py:3710-3715`).

---

## VERDICT

**The recommended fix is necessary but not sufficient, and the guardrail as specified is vacuous.**

- The fix makes the recurrence row *selectable*. In the shipped docker stack it does **not** make
  `(recurrence, equities_seq)` *reachable* (B2-1), and it opens five new failure paths that are
  unreachable today precisely because the pair is unreachable: B2-3, B2-4, B2-5, B2-7, B2-10.
- The guardrail would go green on the current, deadlocked codebase (B2-2a), cannot be driven with a
  synthetic registry through the real gate (B2-2b), and structurally cannot see the branch that breaks
  in production (B2-2c).

**Minimum additions before this fix ships:**

1. Handle the empty compatible∩available set explicitly (B2-1) — never leave a silently-retained
   incompatible pair behind a fully-disabled dropdown.
2. Apply `generator_name_for_type` in `_resolve_oneshot_start_body_handler` (B2-3). One line.
3. Reconcile `model-selection-store` with the server (the flagged FR15) **before** the pair becomes
   reachable, or the reload path silently sends rank-2 data to the LMU (B2-4).
4. Surface `swapped: False` from `/api/model/select` in the UI (B2-5).
5. `hasattr`-guard the remaining seven backend methods, or declare them on `BackendProtocol` (B2-6).
6. Rewrite the guardrail as a handler-level property test with an injected generator list covering the
   all-unavailable case, and give `gated_dataset_options` the injectability its siblings already have
   (B2-2).

**Should be filed as separate defects:** B2-7 (vacuous snapshot cycle), B2-8 (stranded `active_tab` +
unvalidated local-storage restore), B2-9 (unauthenticated generators proxy + schema-less fallback),
B2-11, B2-12, B2-13.
