# Lane A / agent A2 — canopy model+dataset selection reachability

**Subject**: `/home/pcalnon/Development/python/Juniper/juniper-canopy` @ `main`, HEAD `fc62175`
(`chore(deps): pin the cascor-client floor to 0.8.0, now that it is published (#591)`), working tree clean.
**Date**: 2026-09-05
**Entry point**: the code, cold. No prose analysis of this problem was read (juniper-ml `notes/` and
`reports/` were not opened).
**Interpreter**: `conda run -n JuniperCanopy1 python` → CPython 3.13.13, dash 4.2.0, dash-bootstrap-components 2.0.4.
**Posture**: read-only on every repo. No service started or stopped; no network call to a live service;
the operator stack on :8050 was not touched. All execution was in-process against the modules on disk.

Scripts used (kept in the session scratchpad; verbatim commands in § Appendix so every number is reproducible):
`q1_registry.py`, `q2_callbacks.py`, `q2_reachability.py`, `q2_census.py`, `q2_restart.py`, `q7_generators.py`.

---

## Q1. The model/dataset compatibility relation

The registry is `/home/pcalnon/Development/python/Juniper/juniper-canopy/src/model_registry.py`
(not `src/frontend/model_registry.py` — that path does not exist; `find` over the repo returns exactly
one `model_registry.py`).

**Executed**, not read off a table: `q1_registry.py` imports the module and calls
`compatible()` over the full cross product.

### Models — `src/model_registry.py:167-193`

| key | label | category | `input_ndim` | `supported_task_types` | `requires_dt` | `status` | `execution` | `provider` |
|---|---|---|---|---|---|---|---|---|
| `cascor` | CasCor (Cascade-Correlation) | feedforward | `{2}` | classification, regression | False | live | live | `in-process` |
| `recurrence` | Recurrence (LMU) | ts_established | `{3}` | regression | True | live | one_shot | `juniper-recurrence` |

`DEFAULT_MODEL_KEY = "cascor"` (`src/model_registry.py:197`). Neither spec has aliases.

### Dataset types — `src/model_registry.py:132-150`

| value | label | `task_type` | `ndim` | `temporal` | `default_params` |
|---|---|---|---|---|---|
| `spirals` | Spirals | classification | 2 | none | `{}` |
| `xor` | XOR | classification | 2 | none | `{}` |
| `mnist` | MNIST | classification | 2 | none | `{}` |
| `circles` | Circles | classification | 2 | none | `{}` |
| `moons` | Moons | classification | 2 | none | `{}` |
| `equities_seq` | Equities (sequence) | regression | 3 | irregular | `{"max_symbols": 5, "regression_target": "return"}` |

`DEFAULT_DATASET_TYPE = "spirals"` (`src/model_registry.py:153`).

### The predicate — `src/model_registry.py:311-318`

```
dataset.ndim in model.input_ndim  AND  dataset.task_type in model.supported_task_types  AND  temporal_ok(...)
```

### COMPATIBLE PAIRS — 6 of 12 (executed)

```
('cascor',     'spirals')
('cascor',     'xor')
('cascor',     'mnist')
('cascor',     'circles')
('cascor',     'moons')
('recurrence', 'equities_seq')
```

**The relation is a disjoint bipartite partition.** `compatible_models()` returns exactly one model for
every dataset, and `compatible_datasets()` returns disjoint dataset sets for the two models:

```
spirals/xor/mnist/circles/moons -> ['cascor']      equities_seq -> ['recurrence']
cascor -> ['spirals','xor','mnist','circles','moons']   recurrence -> ['equities_seq']
```

No dataset is compatible with both models; no model is compatible with any dataset the other accepts.
`ndim` alone decides every cell (`task_type` and `temporal` never become the *first* failing axis for
these seeds — `dataset_reason` returned only "needs a N-D model" across all 6 incompatible cells).

*Could my method have produced a different answer?* Yes — if `MODELS`/`DATASET_TYPES` were assembled at
import time from an env var, a plugin scan, or a service call, executing in this environment could have
seeded a different population than a deployed canopy. It does not: both are module-level literal tuples
with no conditional construction (`src/model_registry.py:132`, `:167`), and `compatible()` is pure
(`:311-318`, no I/O). The executed output is therefore environment-independent.

---

## Q2. The actual UI transition relation

### Method

Rather than grep, I constructed the real app (`DashboardManager({})`, demo mode, as canopy's own
`conftest.py:12` does) and enumerated `app.callback_map` — **176 registered callbacks** — filtering for
outputs on the state carriers. I then walked the real `app.layout` (1163 nodes) for the control props.
This caught one surface (`restart-ds-type`, below) that a grep for `nn-dataset-type-dropdown` misses entirely.

Sanity check on the method: canopy's own suites for this surface pass under the same constructed manager —
`src/tests/regression/test_model_table.py`, `src/tests/regression/test_model_picker.py`,
`src/tests/unit/test_model_registry.py` → **76 passed**.

### Mount state (read off the executed layout, not the source)

| carrier | mount value | file:line |
|---|---|---|
| `model-selection-store.data` | `'cascor'` | `src/frontend/dashboard_manager.py:1842` (`dcc.Store(..., storage_type="memory", data=DEFAULT_MODEL_KEY)`) |
| `nn-dataset-type-dropdown.value` | `'spirals'` | `src/frontend/dashboard_manager.py:1333` |
| `nn-dataset-type-dropdown.options` | `gated_dataset_options("cascor")` → `equities_seq` carries `disabled: True` | `src/frontend/dashboard_manager.py:1332` |
| `nn-dataset-type-dropdown.clearable` | **`False`** | `src/frontend/dashboard_manager.py:1334` |
| `nn-model-summary.children` | `'Active: CasCor (Cascade-Correlation)'` | `src/frontend/dashboard_manager.py:1219-1223` → `_initial_model_summary()` `:2940-2949` |
| `model-class-store.data` | `'live'` | `src/frontend/dashboard_manager.py:1839` |

Both selection stores are `storage_type="memory"`, so **a page reload re-enters exactly this state**.

Layout census: `nn-dataset-type-dropdown`, `model-selection-store`, `model-class-store`,
`nn-model-summary`, `nn-model-change-button`, `model-selection-modal` each occur **exactly once**;
the layout has **zero duplicate ids**. There is one Dash app, one `app.layout`
(`src/frontend/dashboard_manager.py:545`, `:686`), no `use_pages`, no `dcc.Location` routing.

### Every callback that can change the selected model or dataset

**(T1) `select_model` — the only writer of `model-selection-store.data`**
`src/frontend/dashboard_manager.py:2590-2599`, handler `_select_model_from_table_handler` at `:2914-2929`.

```python
@self.app.callback(
    Output("model-selection-store", "data"),
    Output("model-class-store", "data", allow_duplicate=True),
    Output("nn-model-summary", "children"),
    Output("model-selection-modal", "is_open", allow_duplicate=True),
    Input({"type": "model-select-btn", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
```

No `State`. The clicked key comes from `ctx.triggered_id["index"]`. Guard at `:2925` —
`if not isinstance(triggered_id, dict) or not any(n_clicks_list or []): return no_update × 4` —
swallows the fire that the pattern-matching callback makes when the table is first inserted.
Applies via `_select_model_handler` (`:2876-2897`), which POSTs `/api/model/select` and returns
`no_update × 3` on any failure (`:2897`), leaving the UI on the prior model.

**(T2) `gate_dataset_options` — the only writer of `nn-dataset-type-dropdown.value` / `.options`**
`src/frontend/dashboard_manager.py:2604-2613`, handler `_gate_dataset_options_handler` at `:2687-2706`.

```python
@self.app.callback(
    Output("nn-dataset-type-dropdown", "options"),
    Output("nn-dataset-type-dropdown", "value"),
    Input("model-selection-store", "data"),
    Input("params-init-interval", "n_intervals"),
    State("nn-dataset-type-dropdown", "value"),
    prevent_initial_call=True,
)
```

Body (`:2700-2706`):

```python
if not model_key:
    return dash.no_update, dash.no_update            # :2701
options = apply_availability_gate(gated_dataset_options(model_key), self._fetch_generators())  # :2702
enabled = [option["value"] for option in options if not option.get("disabled")]                # :2703
if current_value in enabled or not enabled:
    return options, dash.no_update                    # :2705
return options, enabled[0]                            # :2706  (the "snap")
```

**(T3) `toggle_model_modal` — builds the table the Select buttons live in (does not itself change state)**
`src/frontend/dashboard_manager.py:2570-2581`, handler `_toggle_model_modal_handler` at `:2899-2912`.
Inputs `nn-model-change-button.n_clicks`, `model-selection-modal-close.n_clicks`,
`model-search-input.value`; **States** `nn-dataset-type-dropdown.value`, `model-selection-store.data`.
Table built by `_build_model_selection_table` at `:3000-3079`.

**No other writer exists.** Exhaustive `callback_map` scan:

- `nn-dataset-type-dropdown.options` / `.value` → **one** callback (T2).
- `model-selection-store.data` → **one** callback (T1).
- `nn-model-summary.children` → **one** callback (T1).
- `model-class-store.data` → T1 (`allow_duplicate`) plus `hydrate_model_class` (`:2514-2531`), which
  carries the *execution paradigm*, not the model identity.

Nothing else can move them: no `dash_clientside.set_props` touches either carrier (the only `set_props`
calls in the repo target `training-control-action` and `button-states`, `src/frontend/dashboard_manager.py:156,175,180`),
and no asset JS references either id (`src/frontend/assets/*.js` grep for `dataset-type` / `model-select` → 0 hits).

### The second, hidden dataset selector — `restart-ds-type`

Found by the layout census, not by grep. `src/frontend/dashboard_manager.py:5435`:

```python
dcc.Dropdown(id="restart-ds-type", options=gated_dataset_options(DEFAULT_MODEL_KEY),
             value=DEFAULT_DATASET_TYPE, clearable=False, className="mb-2")
```

`callback_map` shows **`restart-ds-type.options` is never an Output** — only `.value`
(`src/frontend/dashboard_manager.py:5281`, prefilled from `nn-dataset-type-dropdown.value` State at `:5298`
when `restart-with-new-dataset-button` is clicked). So its options are **frozen at
`gated_dataset_options("cascor")` for the life of the process**: `equities_seq` is `disabled` there
permanently, regardless of the selected model. It re-stages via `_restage_dataset` → `/api/stage_dataset`
and never writes back to `nn-dataset-type-dropdown.value` (see Q4).

### Admissibility tables (executed against the real handlers)

Dataset options per model — `_gate_dataset_options_handler`, availability fail-open:

| model | enabled | disabled | snap from `spirals` |
|---|---|---|---|
| `cascor` | spirals, xor, mnist, circles, moons | **equities_seq** | spirals (no snap) |
| `recurrence` | equities_seq | spirals, xor, mnist, circles, moons | **equities_seq** |

Model Select-button enablement per dataset — walked out of the real `_build_model_selection_table` output:

| dataset | cascor | recurrence |
|---|---|---|
| spirals / xor / mnist / circles / moons | enabled | **DISABLED** |
| equities_seq | DISABLED | enabled |
| *(None)* | enabled | enabled |

Search terms cannot flip `disabled` — it only filters rows:
`''→[cascor:enabled, recurrence:DISABLED]`, `'lmu'→[recurrence:DISABLED]`,
`'recurrence'→[recurrence:DISABLED]`, `'ts_established'→[recurrence:DISABLED]`, `'zzz'→[]`.

### Graph search

Gestures admitted (`q2_reachability.py`):
**A** pick a non-`disabled` dataset option (`clearable=False` forbids `None`);
**B** open the modal → click a non-`disabled` Select button → T1 → T2 fires on the store write and may snap;
**C** reload → mount state.
Gesture B assumed `POST /api/model/select` **succeeds** — the most permissive assumption; a failure is a
self-loop (`:2897`). Availability was fail-open (empty generator list), also the most permissive: the gate
at `src/dataset_schema.py:281` only ever *adds* `disabled` and can only shrink the set.

**REACHABLE STATES — 5:**

```
('cascor', 'spirals')   ('cascor', 'xor')   ('cascor', 'mnist')   ('cascor', 'circles')   ('cascor', 'moons')
```

*Could my method have produced a different answer?* Three assumptions could each flip it, and I checked each:
(i) **that `dcc.Dropdown` refuses a `disabled` option and `dbc.Button(disabled=True)` fires no click.**
This is the one claim I did **not** verify in a browser (constraint: do not disturb the live stack), so it is
asserted from the props, not observed. It is the load-bearing assumption — see Q3.
(ii) **that a select POST failure could open a path** — it cannot; failure is `no_update × 3`.
(iii) **that a real `/v1/generators` availability list could enable something** — it cannot;
`apply_availability_gate` (`src/dataset_schema.py:277-286`) only sets `disabled`, never clears it, and
`availability_map` defaults an absent generator to available (`src/dataset_schema.py:244,259`).

---

## Q3. Is every compatible-and-available pair reachable? **NO.**

```
compatible \ reachable  =  [ ('recurrence', 'equities_seq') ]
```

One compatible pair — and the *only* pair that uses the recurrence model at all — is unreachable from the
mount state. The recurrence backend is, through the UI, entirely unusable.

### Mechanism: a mutual gate between two controls that each read the other's current value

Both gates are individually correct. Composed, they close.

**Gate 1 — the dataset dropdown is gated on the current model.**
`gated_dataset_options` (`src/model_registry.py:408-424`) marks every dataset incompatible with the
selected model `disabled: True` (`:423`). It is applied at first paint at
`src/frontend/dashboard_manager.py:1332` and at runtime at `:2702`. With `model = "cascor"`,
`equities_seq` is `disabled`.
`clearable=False` (`src/frontend/dashboard_manager.py:1334`) removes the only other way for the value to
become something outside the enabled set.

**Gate 2 — the model table's Select button is gated on the current dataset.**
`_build_model_selection_table` (`src/frontend/dashboard_manager.py:3000-3079`):

```python
dataset = get_dataset_spec(dataset_value) if dataset_value else None   # :3018
...
reason = model_reason(model, dataset) if dataset is not None else None # :3033
is_compatible = reason is None                                          # :3034
...
select_button = dbc.Button(..., disabled=not is_compatible, ...)        # :3050  <-- the closing line
```

The `dataset_value` it reads is a `State` on the sidebar dropdown (`:2576`). With
`dataset = "spirals"` (2-D), `model_reason(recurrence, spirals)` = `"needs 3-D data"` → `is_compatible = False`
→ **`disabled=True`** on the recurrence row's Select button.

**The cycle.** From `('cascor','spirals')`:
to reach `equities_seq` you must first be on `recurrence` (Gate 1, `src/frontend/dashboard_manager.py:2702`
via `src/model_registry.py:423`); to reach `recurrence` you must first be on `equities_seq`
(Gate 2, `src/frontend/dashboard_manager.py:3050`). Because the compatibility relation is a **disjoint
partition** (Q1), there is no dataset from which both models are selectable and no model from which both
dataset groups are enabled — so no intermediate state breaks the cycle. The snap at
`src/frontend/dashboard_manager.py:2706` would carry the dataset across (`_gate_dataset_options_handler("recurrence", d)`
→ `equities_seq` for **every** `d`), but it fires only on a `model-selection-store` write that can never happen.

The only line that would break it is `src/frontend/dashboard_manager.py:3018` — the `if dataset_value else None`
branch. With `dataset_value = None`, `reason` is forced `None`, every Select button is enabled, and
`recurrence` becomes selectable; `_gate_dataset_options_handler("recurrence", None)` then snaps the dataset
to `equities_seq` and the pair is reached. **Executed counterfactual:**

```
Select buttons with dataset=None: [('cascor', False), ('recurrence', False)]   # False = not disabled
options_for('recurrence', None) -> snapped value = 'equities_seq'
```

That branch is unreachable because `clearable=False` at `src/frontend/dashboard_manager.py:1334` and
because the sole writer of `.value` never returns `None` (`:2701` returns `no_update`, `:2705` `no_update`,
`:2706` an `enabled[0]` string). So the escape hatch exists in the handler and is walled off by the layout.

**Scope of the claim.** This is a proof over the callback graph and the rendered `disabled`/`clearable`
props, not a browser observation. It holds unless a client can defeat a `disabled` `dcc.Dropdown` option
*and* a `disabled` `dbc.Button` — i.e. not a gesture the UI exposes. I did not drive a browser (live stack
on :8050 must not be disturbed), so I mark that single step **asserted from props, not observed**.

---

## Q4. Is every reachable pair compatible? **YES for the 5 BFS states — but three divergences sit outside that tuple.**

```
reachable \ compatible  =  []
```

All 5 reachable `(model, dataset)` selection states are compatible. However, the BFS tuple tracks the
*UI's selection state*, and three reachable conditions make that tuple stop describing the system:

**(a) The restart modal can desync the sidebar from the staged backend dataset.**
`restart-ds-type` (`src/frontend/dashboard_manager.py:5435`) is prefilled from
`nn-dataset-type-dropdown.value` on open (`:5298`), can then be edited to any other enabled type, and
`_restage_dataset` POSTs it to `/api/stage_dataset` (`:5697-5702`) before the restart orchestration
(`:5715-5722`). Nothing writes the new value back to `nn-dataset-type-dropdown.value` — `callback_map`
confirms that prop has exactly one writer, `gate_dataset_options`, whose Inputs are the model store and
the init interval. **Result**: the sidebar keeps showing the old type while the backend trains the new one.
Additionally, `restart-ds-type.options` is never regated (no `.options` Output at all), so it is pinned to
`gated_dataset_options("cascor")` forever — the restart path can never stage `equities_seq` even in a world
where Q3 were fixed.

**(b) A 2-D generator can be POSTed to the one-shot LMU backend.**
`_resolve_oneshot_start_body_handler` (`src/frontend/dashboard_manager.py:2668-2685`) keys off
`model-class-store` (the *live backend's* execution paradigm) and the dataset dropdown, and applies **no
compatibility check**. Executed:

```
model_class='one_shot' dataset='spirals'      -> {'dataset': {'generator': 'spirals'}}
model_class='one_shot' dataset='equities_seq' -> {'dataset': {'generator': 'equities_seq', 'params': {...}}}
```

`model-class-store` is written by `hydrate_model_class` (`:2514-2531`) from `GET /api/train/status`'s
`execution` field (`src/main.py:3716`), i.e. from the **process-global** `backend`. That global survives
page reloads and is swapped by `POST /api/model/select` (`src/main.py:3909`). So: if any client has swapped
the process backend to recurrence, a *freshly mounted* page — whose memory stores reset to
`('cascor','spirals')` — hydrates `model-class-store` to `"one_shot"` and resolves a Start body of
`{"dataset": {"generator": "spirals"}}`: a 2-D spiral generator aimed at the LMU. Incompatible, and the
sidebar reads "Active: CasCor (Cascade-Correlation)" throughout.

**(c) Cross-repo `task_type` disagreement on the one pair that matters.**
canopy declares `equities_seq` `task_type="regression"` (`src/model_registry.py:141`); juniper-data declares
the same generator `"task_type": "classification"`
(`/home/pcalnon/Development/python/Juniper/juniper-data/juniper_data/api/routes/generators.py:117`).
`GeneratorInfo` (`/home/pcalnon/Development/python/Juniper/juniper-data/juniper_data/core/models.py:143-162`)
does not carry `task_type` on the wire, so the disagreement is undetectable at runtime. It is load-bearing:
recurrence supports only `{"regression"}`, so had canopy used juniper-data's declared value,
`compatible(equities_seq, recurrence)` would be **False** and recurrence would have **no** compatible
dataset at all — compatible set 5, not 6.

*Could my method have produced a different answer?* The `[]` result is a set difference over the executed
BFS, so it is exact for that state space. It could look different only if the state space were the wrong
one — which is precisely what (a)/(b) show: the pair `(selected model, selected dataset)` is not a complete
description of what gets trained.

---

## Q5. What does the UI report as the active model, and where does that string come from?

### DOM → data source

`<span id="nn-model-summary" class="small text-muted">` — `src/frontend/dashboard_manager.py:1219-1223`.
Executed layout value at mount: **`'Active: CasCor (Cascade-Correlation)'`**.

Two producers, and only two:

1. **At rest / at mount**: `_initial_model_summary()` (`src/frontend/dashboard_manager.py:2940-2949`) →
   `self._model_summary_text({"nn_model": DEFAULT_MODEL_KEY, "status": spec.status})`. This is a **layout
   constant derived from the registry**. It makes **no backend call whatsoever**.
2. **After a Select click**: `select_model` (`:2593`) → `_select_model_handler` (`:2876-2897`) →
   at `:2893` `return data.get("nn_model", model_key), data.get("execution","live"), self._model_summary_text(data)`.
   `_model_summary_text` (`:2931-2938`) reads **`data["nn_model"]`** and `data["status"]` — it never reads
   `data["backend"]`.

`callback_map` confirms `nn-model-summary.children` has exactly one callback writer (T1). **There is no
callback that refreshes the summary from the backend on mount or on any interval.**

### What the backend reports

Model routes in `src/main.py`: **`POST /api/model/select` only** (`src/main.py:3921-3936`). There is **no
`GET /api/model/...` route** — grepped `@app.get("/api/model` → zero hits. So the UI has no way to *ask*
which model is live.

Response model — `_model_state_response`, `src/main.py:3860-3871`:

```python
return {
    "nn_model":  nn_model,               # :3866  the REQUESTED key, echoed back
    "backend":   backend.backend_type,   # :3867  the ACTUAL live backend
    "execution": backend.execution,      # :3868  the ACTUAL paradigm
    "status":    spec.status ...,        # :3869  from the registry
    "swapped":   swapped,                # :3870
}
```

The payload **does** carry the truth in `backend`. The UI reads `nn_model` and discards `backend`
(`src/frontend/dashboard_manager.py:2893`, `:2934`).

### Does the displayed identity provably match the live backend? **No — and here is the divergence path.**

`settings.recurrence_service_url` defaults to **`None`** (`src/settings.py:261`); it is only set by
`JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` / `RECURRENCE_SERVICE_URL`. With it unset:

1. `_selection_targets_recurrence("recurrence")` (`src/main.py:3845-3857`) =
   `spec.provider == RECURRENCE_PROVIDER and bool(settings.recurrence_service_url)` → **`False`**.
2. `_swap_backend` (`src/main.py:3891`): `if _selection_targets_recurrence(nn_model) == (backend.backend_type == "recurrence")`
   → `False == False` → **True** → takes the **no-op branch**: `current_nn_model = "recurrence"`;
   returns `_model_state_response("recurrence", swapped=False)`. **HTTP 200. No swap.**
3. The response is `{"nn_model": "recurrence", "backend": "demo"|"service", "execution": "live", "status": "live", "swapped": false}`.
4. `_select_model_handler` (`:2893`) takes `data["nn_model"]` = `"recurrence"` →
   `_model_summary_text` renders **`"Active: Recurrence (LMU)"`** while the live backend is cascor/demo.

The code says this is a known, deliberate normal path — `src/backend/__init__.py:111-136`,
`_try_create_recurrence_backend`, returns `None` when the URL is unset (`:134-136`, logged as a warning),
and its docstring at `:118-127` states outright: *"the unset-URL branch is a REACHABLE normal path… the user
is shown a successful selection of a model that is not actually active."*

**A weaker but always-on form of the same divergence needs no gesture at all**: because the summary at rest
is the layout constant `"Active: CasCor (Cascade-Correlation)"` (`:2947-2949`) and nothing re-reads the
backend, the sidebar asserts CasCor even when the process-global `backend` is a `DemoBackend`
(the default when no `cascor_service_url` is configured — `src/backend/__init__.py:107-108`) or has been
swapped to `RecurrenceBackend` by another client. `_model_state_response` would have said
`"backend": "demo"`; the UI never asks.

One visible tell of the split: `model-class-store` receives `data["execution"]` — the **actual** backend's
paradigm (`:2893`) — so the cascade panels follow the real backend while the summary follows the requested
key. The two can disagree on screen simultaneously.

**Caveat, stated plainly**: given Q3, the `select_model` path is currently unreachable *for recurrence*
through the UI. The divergence in `_select_model_handler` is therefore latent behind the deadlock — but it
is reachable today by any direct `POST /api/model/select` (the route has no UI-only guard), and the at-rest
constant-summary form is reachable with zero gestures.

*Could my method have produced a different answer?* If a `GET /api/model/...` route existed, or a second
`nn-model-summary` writer existed, the summary could be backend-derived. I checked both mechanically:
`grep '@app.get("/api/model'` → 0 hits; `callback_map` → exactly one writer. Both are exhaustive over the
constructed app, not a sample.

---

## Q6. Can training start with no dataset selected?

### The Start gate — exact signature and gate expression

Callback: `src/frontend/dashboard_manager.py:4471-4497`.

```python
@self.app.callback(
    [Output("start-button","disabled"), Output("start-button","children"),
     Output("pause-button","disabled"),  Output("pause-button","children"),
     Output("stop-button","disabled"),   Output("stop-button","children"),
     Output("resume-button","disabled"), Output("resume-button","children"),
     Output("reset-button","disabled"),  Output("reset-button","children")],
    [Input("button-states","data"),
     Input("model-selection-store","data")],
    prevent_initial_call=False,
)
def update_button_appearance(button_states, model_key): ...
```

Handler `_update_button_appearance_handler(button_states=None, model_key=None)` —
`src/frontend/dashboard_manager.py:7250-7287`. The **entire** gate expression is:

```python
start_disabled, start_text = get_button_props("start", "Start Training", "▶")   # :7267
if not model_is_trainable(model_key):                                            # :7269
    start_disabled = True                                                        # :7270
```

**The dataset value is not an argument to this callback and appears nowhere in the handler.** There is no
dataset term in the Start gate at all.

Executed:

| `model_key` | `start_disabled` | label |
|---|---|---|
| `'cascor'` | False | `▶ Start Training` |
| `'recurrence'` | False | `▶ Start Training` |
| `None` | False | `▶ Start Training` |
| `''` | False | `▶ Start Training` |

`model_is_trainable` (`src/model_registry.py:232-247`) returns `True` for an empty key (`:242-243`) and
`True` for an unknown key (`:247`, fail-open by design), and both shipped models are `status="live"` — so
this gate **never fires** for the current population. Start is always enabled.

Whether "no dataset selected" is reachable at all: `clearable=False` (`:1334`) plus a single `.value` writer
that never emits `None` (`:2701`/`:2705` `no_update`, `:2706` a string) means the dropdown always holds a
value. **So the answer is: the Start control does not gate on the dataset, but the dataset can never be
empty either — the gap is unexploitable through the sidebar today, and would open the moment the dropdown
became clearable or a `None` value reached it.**

### What Start actually POSTs

Both transports read `oneshot-start-params-store` as a `State`
(clientside `src/frontend/dashboard_manager.py:4380-4400`, server-side `:4405-4437`), resolved by
`_resolve_oneshot_start_body_handler` (`:2668-2685`):

```python
if model_class != "one_shot" or not dataset_generator:
    return None                                            # :2679-2680
dataset_ref = {"generator": dataset_generator}             # :2681
params = dataset_default_params(dataset_generator)         # :2682
if params: dataset_ref["params"] = params                  # :2683-2684
return {"dataset": dataset_ref}                            # :2685
```

Executed (all four dataset values × both classes) — `None` for every `live` case, `None` for `one_shot` with
`dataset in (None, "")`, and a `{"dataset": {...}}` body otherwise.

POST site: `_handle_training_buttons_handler` `:7158-7165` —
`post_kwargs["json"] = oneshot_start_body` only `if command == "start" and oneshot_start_body`; otherwise a
bare `POST /api/train/{command}` with no body.

### What the backend does with a missing/None dataset

`POST /api/train/start` — `src/main.py:3592-3621`:

```python
start_kwargs = _recurrence_start_kwargs(body.model_dump()) if (backend.backend_type == "recurrence" and body is not None) else {}   # :3612
result = await offload(backend.start_training, reset=reset, **start_kwargs)                                                          # :3613
```

- **cascor / demo**: body is `None` by construction (`:2679`). `start_training(reset=...)` — the backend
  trains whatever is already staged. A missing dataset is simply not a concept on this path; there is no
  refusal and no check.
- **recurrence with no dataset ref**: `start_kwargs = {}` → `RecurrenceBackend.start_training`
  (`src/backend/recurrence_backend.py:130-156`) at `:138-140`:
  ```python
  dataset_ref = {k: kwargs[k] for k in _DATASET_REF_KEYS if kwargs.get(k) is not None}
  if not any(dataset_ref.get(k) for k in ("dataset_id","name","generator")):
      return ControlResult(ok=False, error="no dataset reference (need one of dataset_id / name / generator)")
  ```
  → `_control_result_failure` → **HTTP 409** (`src/main.py:3615-3618`). It fails closed, loudly, at the
  backend — never at the button.

**Answer**: Yes, the Start button is enabled with no dataset term in its gate; the refusal lives entirely in
`RecurrenceBackend`, one full round-trip away, and only on the recurrence path.

*Could my method have produced a different answer?* Only if a second writer of `start-button.disabled`
existed. `callback_map` shows one, and the source comments at `:4486-4491` say the fusion into a single
writer is deliberate. The executed table is the real handler's return, not a reading of it.

---

## Q7. Datasets offered vs datasets available

Executed juniper-data's registry directly:
`/home/pcalnon/Development/python/Juniper/juniper-data/juniper_data/api/routes/generators.py:44`
(`GENERATOR_REGISTRY`), served by `list_generators` at `:234-254`.

**juniper-data registers 16 generators. canopy offers 6.**

canopy's 6 (`src/model_registry.py:132-150`) map onto juniper-data names via
`GENERATOR_NAME_ALIASES = {"spirals": "spiral", "moons": "moon"}` (`src/dataset_schema.py:97-100`) →
`{spiral, xor, mnist, circles, moon, equities_seq}`. All 6 exist upstream: **canopy offers nothing
juniper-data does not register (0 phantom entries).**

### The 10 generators canopy does not offer

| generator | juniper-data `task_type` | note |
|---|---|---|
| `gaussian` | classification | 2-D synthetic — would be cascor-compatible |
| `checkerboard` | classification | 2-D synthetic — would be cascor-compatible |
| `csv_import` | classification | user data import |
| `arc_agi` | classification | needs an optional extra |
| `equities` | classification | 2-D (non-windowed) equities variant |
| `multi_sine` | **regression** | (W, L, 1) sequences, regular Δt |
| `mackey_glass` | **regression** | (W, L, 1) sequences, regular Δt |
| `ar_p` | **regression** | (W, L, 1) sequences, regular Δt |
| `irregular_sine` | **regression** | (W, L, 1), genuinely **non-uniform Δt** |
| `delay_product` | **regression** | (W, L, 1), non-uniform Δt |

Five of the ten are 3-D regression sequence generators — including two with genuinely irregular Δt
(`irregular_sine`, `delay_product`). By canopy's own predicate these would be `ndim=3`,
`task_type="regression"`, `temporal="irregular"` and therefore compatible with `recurrence`. **The single
model that the UI cannot reach is also the model whose five best-matched upstream datasets canopy does not
offer at all** — so the deadlock cannot be worked around by picking a different sequence dataset either.

Side note on the availability channel: canopy's proxy `GET /api/dataset/generators`
(`src/main.py:1838-1876`) falls back to a hardcoded 4-entry list (`:1866-1874`:
spiral, xor, circles, moon) when juniper-data is unreachable. That list omits `mnist` and `equities_seq`,
but `availability_map` defaults an absent name to available (`src/dataset_schema.py:244`, `:259`), so the
fallback greys nothing. This confirms the fail-open assumption used in the Q2 BFS.

*Could my method have produced a different answer?* `GENERATOR_REGISTRY` is a module-level literal dict
built from static imports (`generators.py:44`), so executing it here yields the same 16 a running service
would register. What executing here **cannot** tell me is which of the 16 report `available: false` in a
given deployment — `generator_available(info)` (`:248`) is evaluated per-deployment, and I made no network
call. That affects only the *availability* half; the *offered* half (6) and the *registered* half (16) are
both static and exact.

---

## Summary of findings

| # | Finding | Evidence |
|---|---|---|
| A2-1 | `('recurrence','equities_seq')` — the only compatible pair using the recurrence model — is unreachable from the mount state. Mutual gate: dataset options gated on model (`dashboard_manager.py:2702` / `model_registry.py:423`) × model Select gated on dataset (`dashboard_manager.py:3050`), over a compatibility relation that is a disjoint partition. | Executed BFS: reachable 5, compatible 6 |
| A2-2 | `clearable=False` (`dashboard_manager.py:1334`) is load-bearing: with `dataset_value=None` the `if dataset_value else None` branch at `:3018` forces every Select button enabled and the pair becomes reachable. | Executed counterfactual |
| A2-3 | The sidebar's active-model string is a layout constant (`_initial_model_summary`, `:2940-2949`) and, after a Select, the **echoed request key** (`:2893`, `:2934`) — never `backend.backend_type`, which the same payload carries (`main.py:3867`). No `GET /api/model/*` route exists. | `callback_map` (1 writer), route grep (0 hits) |
| A2-4 | With `recurrence_service_url` unset (**the default**, `settings.py:261`), selecting recurrence returns **HTTP 200 with no swap** (`main.py:3891` no-op branch) and the UI displays "Active: Recurrence (LMU)" over a cascor/demo backend. Documented as intended at `backend/__init__.py:118-127`. | Code path traced |
| A2-5 | The Start gate (`:7250-7287`) has **no dataset term**; refusal lives in `RecurrenceBackend.start_training` (`recurrence_backend.py:140`) → HTTP 409, one round-trip away. `model_is_trainable` never fires for the current population. | Executed handler |
| A2-6 | `restart-ds-type` (`:5435`) is a second dataset selector whose `.options` are **never regated** (no `.options` Output in `callback_map`) — pinned to `gated_dataset_options("cascor")` for the process lifetime — and which re-stages the backend dataset without writing back to the sidebar dropdown. | Layout census + `callback_map` |
| A2-7 | `_resolve_oneshot_start_body_handler` (`:2668-2685`) applies **no** compatibility check: with `model-class-store="one_shot"` (hydrated from the process-global backend, `:2530`/`main.py:3716`) and the mount dataset, it emits `{"dataset":{"generator":"spirals"}}` — a 2-D generator aimed at the LMU. | Executed |
| A2-8 | Cross-repo `task_type` disagreement on `equities_seq`: canopy `"regression"` (`model_registry.py:141`) vs juniper-data `"classification"` (`generators.py:117`). `GeneratorInfo` omits `task_type` from the wire (`core/models.py:143-162`) so it is undetectable at runtime. Had canopy used the upstream value, recurrence would have **zero** compatible datasets. | Executed both registries |
| A2-9 | juniper-data registers 16 generators; canopy offers 6. Of the 10 missing, five are 3-D regression sequence generators (two with irregular Δt) — exactly the recurrence-compatible family. | Executed both registries |

## What I could not determine

- **Browser-level confirmation** that `dcc.Dropdown` refuses a `disabled` option and `dbc.Button(disabled=True)`
  fires no `n_clicks`. Not attempted: the operator stack on :8050 must not be disturbed. The Q3 claim rests on
  the rendered props (`disabled: True` / `clearable: False`), which I did verify by executing the layout.
- **Which generators report `available: false` in the running deployment.** `generator_available(info)`
  (`generators.py:248`) is per-deployment and I made no network call. Fail-open means this can only shrink
  the reachable set, never grow it.
- **Whether `POST /api/model/select` has ever been called against the live process** (which would make the
  A2-7 hydration path active right now). Determining that needs a live `GET /api/train/status`, which I did
  not issue.

## Appendix — reproduction

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
conda run -n JuniperCanopy1 python <script>.py     # q1_registry, q2_callbacks, q2_reachability, q2_census, q2_restart
cd /home/pcalnon/Development/python/Juniper/juniper-data
conda run -n JuniperData    python q7_generators.py
# method sanity check (76 passed):
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
conda run -n JuniperCanopy1 python -m pytest src/tests/regression/test_model_table.py \
    src/tests/regression/test_model_picker.py src/tests/unit/test_model_registry.py -q
```

Every script inserts `juniper-canopy/src` on `sys.path` and sets `JUNIPER_CANOPY_DEMO_MODE=1`, mirroring
`juniper-canopy/conftest.py:1-12`. `DashboardManager({})` is constructed exactly as
`src/tests/regression/test_model_table.py:51-53` does.

**Note on the interpreter**: `/opt/miniforge3/envs/JuniperCanopy` does not exist (it is
`JuniperCanopy-DEPRECATED`); the live env is `JuniperCanopy1`. All results above were produced under
`conda run -n JuniperCanopy1`, which fires the env's activate hooks. The Q1 numbers were additionally
produced under a direct interpreter call and were byte-identical (the registry is pure stdlib, no torch).
