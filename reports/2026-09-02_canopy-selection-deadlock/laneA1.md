# Lane A verifier A1 — measurement re-creation

**Claim under test:** In the juniper-canopy dashboard, the pair `(model=recurrence, dataset=equities_seq)`
is UNREACHABLE from the default state `(model=cascor, dataset=spirals)` through the sidebar dataset
dropdown and the model-selection modal, because each side's control hard-disables every option
incompatible with the peer side's CURRENT value, and neither side can be unset.

**Verdict: CONFIRMED** — by executed code, not by reading.

**Repo:** `/home/pcalnon/Development/python/Juniper/juniper-canopy` @ `30e15b7` (clean tree, read-only; nothing edited).
**Date:** 2026-09-02.

---

## 0. Instrument (NO downgrade — the code was executed)

```
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
PYTHONPATH=src /opt/miniforge3/envs/JuniperCanopy1/bin/python <probe>
# python 3.13.13 | conda-forge | dash 4.2.0
```

`conda run -n JuniperCanopy1 python` is the equivalent invocation; I used the env's interpreter
directly with `PYTHONPATH=src` (canopy's own `[tool.pytest.ini_options] pythonpath = ["src"]`, so
flat imports `model_registry`, `frontend.dashboard_manager` resolve). `JuniperCanopy` (no suffix)
is marked `-DEPRECATED` on this box; I did not use it. **Every number below is executed output.**

Three probes, all in
`/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2b5fe8ef-.../scratchpad/`:

| Probe | Entry point | What it measures |
|---|---|---|
| `probe_reachability.py` | `model_registry.gated_dataset_options` + `DashboardManager._build_model_selection_table` | per-option / per-button `disabled`; the transition graph; BFS |
| `probe_writers.py` | `DashboardManager({}).app.callback_map` (**175 callbacks, real app built**) | every registered writer of either id, server-side AND clientside |
| `probe_addendum.py` | `to_plotly_json()`, `apply_availability_gate`, `_gate_dataset_options_handler` | what the browser actually receives; deployment-state sensitivity; snap asymmetry |

The one thing I could **not** execute: a live browser check that a `disabled` react-select option /
`<button disabled>` really refuses the click. Canopy is listening on `127.0.0.1:8050` but does not
answer (`curl --max-time 15` → exit 28, 0 bytes; same for `/v1/health` and `/dashboard/`). That
sub-step is **NO ARTIFACT**; §A below gives the wire-level serialization instead, which is the
closest artifact short of a browser.

---

## 1. Registry seeds (executed, unmocked)

```
model 'cascor'      ndim=[2]  tasks=[classification, regression]  requires_dt=False  status=live
model 'recurrence'  ndim=[3]  tasks=[regression]                  requires_dt=True   status=live
dataset spirals/xor/mnist/circles/moons   ndim=2  task=classification  temporal='none'
dataset equities_seq                      ndim=3  task=regression      temporal='irregular'
DEFAULT_MODEL_KEY='cascor'   DEFAULT_DATASET_TYPE='spirals'
```

There is **no** dataset that both models accept and **no** model that accepts both dataset ranks.
The compatibility relation is a perfect 2-block partition — that is the structural precondition for
the deadlock.

## 2. `gated_dataset_options(model_key)` — executed

| model_key | spirals | xor | mnist | circles | moons | equities_seq |
|---|---|---|---|---|---|---|
| `cascor` | — | — | — | — | — | **disabled** (`"Equities (sequence) — needs a 3-D model"`) |
| `recurrence` | **disabled** | **disabled** | **disabled** | **disabled** | **disabled** | — |
| `__unknown_model__` (control) | — | — | — | — | — | — (all 6 enabled) |

`src/model_registry.py:408`. The unknown-key row is the ungated fallback and is my first
harness-adequacy control (§5).

## 3. `_build_model_selection_table(dataset_value, selected_model)` — executed

`src/frontend/dashboard_manager.py:3000` (`@staticmethod`, called unbound).

| dataset_value | cascor Select | recurrence Select |
|---|---|---|
| spirals / xor / mnist / circles / moons | enabled | **disabled** (`title="needs 3-D data"`) |
| equities_seq | **disabled** (`title="needs 2-D data"`) | enabled |
| `None` (control) | enabled | enabled |

Asserted inside the probe: the enabled set does **not** depend on `selected_model` (only the button
label/colour does) — so there is no "you can always re-pick your current model" escape.

## 4. Directed transition graph and reachability — executed

Edges: (a) dataset dropdown — from `(m,d)` to `(m,d')` for every `d'` **enabled** under `m`;
(b) model modal — from `(m,d)` to `(m', snap(m',d))` for every `m'` whose Select button is **enabled**
under `d`, where `snap` replays `_gate_dataset_options_handler`'s auto-snap.

```
START = ('cascor','spirals')      |STATES| = 12      |REACHABLE| = 5

REACHABLE:   (cascor,spirals) (cascor,xor) (cascor,mnist) (cascor,circles) (cascor,moons)
UNREACHABLE: (cascor,equities_seq)
             (recurrence,spirals) (recurrence,xor) (recurrence,mnist)
             (recurrence,circles) (recurrence,moons)
             (recurrence,equities_seq)   <-- the target

TARGET reachable from default? False
```

Two further executed facts worth keeping:

- **`(recurrence,equities_seq)` is an absorbing state with ZERO out-edges.** If you ever got there,
  the dropdown offers only `equities_seq` and the table enables only `recurrence` — you could never
  get back to cascor either. The lock is symmetric, not one-way.
- **Reverse reachability:** the only states that can reach the target are
  `(cascor,equities_seq)` and all five `(recurrence, <2-D>)` states — every one of which is itself
  unreachable. The target sits in a component disjoint from the start component.

## 5. REQUIRED CRITICAL CHECK — could this procedure have said "reachable"?

Yes. Four positive controls, all executed:

1. `gated_dataset_options('cascor')` returns **5 of 6 enabled** — the probe reads `disabled` correctly
   and reports absence-of-disabled as enabled.
2. `gated_dataset_options('__unknown_model__')` → **6 of 6 enabled** (ungated fallback path).
3. `_build_model_selection_table(None, 'cascor')` → **both** models' Select buttons enabled — the
   button walker can and does emit `enabled`.
4. Synthetic positive control: a `ModelSpec(input_ndim={3}, tasks={regression}, requires_dt=True)`
   injected via the `models=` kwarg yields `compatible_datasets → ['equities_seq']` and a table whose
   Select button is `{'disabled': False, 'title': 'Select this model'}`.

So a uniformly-disabled reading is not an artifact of the harness; the harness reports `enabled`
wherever `enabled` exists. Additionally the graph builder produced **5** reachable states, not 1 —
it is capable of emitting edges.

Deployment-state sensitivity (also executed, `probe_addendum.py` §B): the reachable set is
`{cascor}x{5 2-D datasets}` under *all-available*, *all-generators-declared-available*, and
*equities-unavailable*, and collapses to `{(cascor,spirals)}` under *only-equities-available*.
`apply_availability_gate` (`src/dataset_schema.py:268`) can only ever **add** `disabled` — it skips
options already disabled and never clears the flag — so no deployment state can make the target
reachable. The deadlock is monotone in availability.

---

## 6. The four required sub-reports

### (a) Is `nn-dataset-type-dropdown` non-clearable? — **CONFIRMED**

`src/frontend/dashboard_manager.py:1330-1334`:

```python
dcc.Dropdown(
    id="nn-dataset-type-dropdown",                      # :1331
    options=gated_dataset_options(DEFAULT_MODEL_KEY),   # :1332
    value=DEFAULT_DATASET_TYPE,                         # :1333
    clearable=False,                                    # :1334  <-- anchor confirmed
```

Confirmed at the wire level too: the realized layout component serializes as
`{"clearable": false, "value": "spirals", ...}`. The dataset side can never be unset.

### (b) Is `model-selection-store` seeded with a non-empty default? — **CONFIRMED**

`src/frontend/dashboard_manager.py:1842`:

```python
dcc.Store(id="model-selection-store", storage_type="memory", data=DEFAULT_MODEL_KEY)
```

Executed from the built app's layout: `data='cascor'`, `storage_type='memory'`. Non-empty at first
paint, and — because it is `memory`, not `local`/`session` — it **resets to `'cascor'` on every page
reload**, so a reload is not an escape either. The model side can never be unset:
`_gate_dataset_options_handler` returns `(no_update, no_update)` on a falsy `model_key`, and nothing
ever writes a falsy value (see (c)).

### (c) Any OTHER writer of either value? — **REFUTED that any exists** (i.e. no other writer found)

This is the load-bearing part. I enumerated writers from `app.callback_map` on the **real built app**
(175 registered callbacks), not by grep, so a callback whose id is built from a variable cannot hide.

**`nn-dataset-type-dropdown.value` — exactly ONE writer:**

```
output_key = ..nn-dataset-type-dropdown.options...nn-dataset-type-dropdown.value..
clientside  = False
inputs      = [('model-selection-store','data'), ('params-init-interval','n_intervals')]
state       = [('nn-dataset-type-dropdown','value')]
```
→ `gate_dataset_options` at `dashboard_manager.py:2604-2613` → `_gate_dataset_options_handler` (:2687).
It is also the sole writer of `.options`.

**`model-selection-store.data` — exactly ONE writer:**

```
output_key = ..model-selection-store.data...model-class-store.data@<hash>...
             nn-model-summary.children...model-selection-modal.is_open@<hash>..
clientside  = False
inputs      = [('{"index":["ALL"],"type":"model-select-btn"}','n_clicks')]
state       = []
```
→ `select_model` at `dashboard_manager.py:2590-2599` → `_select_model_from_table_handler` (:2914).
Its only trigger is the per-row Select button, which §3 shows is `disabled` for the incompatible model.

Every other candidate route, checked and cleared:

| Candidate route | Result | Evidence |
|---|---|---|
| **URL / query params** | **NO ARTIFACT** | Walked the realized layout: **no `dcc.Location` and no `dcc.Link` anywhere** (464 id-bearing components). There is no URL-driven state at all. |
| **Clientside callbacks** | **REFUTED** | `callback_map` marks both writers `clientside = False`; no clientside callback outputs either id. |
| **`dash_clientside.set_props`** (bypasses `callback_map`) | **REFUTED** | All 5 call sites in the repo enumerated, all literal ids: `training-control-action` (x2, `dashboard_manager.py:156,175`), `button-states` (:180), `walkthrough-state-store` (`assets/tutorial_walkthrough.js:239`), `context-menu-tutorial-trigger` (`assets/context_menus.js:116`), and `STORE_ID = "hdf5-snapshots-panel-context-menu-trigger"` (`assets/snapshot_context_menu.js:28,131`). None targets either id. |
| **Direct DOM manipulation in assets JS** | **REFUTED** | `grep 'dataset-type\|model-selection\|model-select-btn\|nn-model'` over all 6 `src/frontend/assets/*.js` → **zero hits**. |
| **REST `POST /api/model/select`** (`src/main.py:3731`) | **CONFIRMED it exists; REFUTED as a UI route** | It validates the key against the registry and swaps the *process-global backend* (`_swap_backend`). Nothing reads its result back into `model-selection-store` — that store has one writer and its only input is the Select buttons. A direct POST would desync the server from the dashboard, not unlock the UI. |
| **REST `POST /api/stage_dataset`** (`src/main.py:3985`) | **CONFIRMED it exists; REFUTED as a UI route** | Staged server-side by `apply_dataset`, which reads the dropdown as `State`. No writer back to the dropdown. |
| **REST `GET /api/dataset`, `POST /api/dataset/generate|import-file|import-url`, `GET /api/dataset/generators`** (`main.py:1442,1455,1511,1598,1681`) | **REFUTED** | Plotter/import surfaces. `/api/dataset/generators` feeds `_fetch_generators()` → `apply_availability_gate`, which as shown can only *add* `disabled`. |
| **Demo mode** (`src/demo_mode.py`) | **REFUTED** | `grep -c model src/demo_mode.py` → **0**. Demo mode has no concept of model selection. |
| **Snapshots / session restore** | **REFUTED** | `src/snapshots/` holds only `snapshot_history.jsonl` (data). `hdf5_snapshots_panel.py` *displays* `dataset_type` (:709-710) read-only; no restore-into-control path. |
| **Browser persistence** | **REFUTED** | `persistence=True` appears **once** in the whole dashboard, on `experimental-functions-toggle` (:1742-1743). `model-selection-store` is `storage_type="memory"`. No `local`/`session` store carries either value. |
| **WebSocket push** | **REFUTED** | `grep 'model_key\|nn_model\|model_selection' src/communication/` → zero hits. |
| **Pattern-matching output collision** | **REFUTED** | Both ids are plain strings; Dash pattern-matching outputs are dict ids and cannot match a string id. |

**Near-misses worth flagging (they do not refute the claim, they reinforce it):**

1. **`restart-ds-type` (`dashboard_manager.py:5422`) is a SECOND dataset-type dropdown whose gate is
   frozen at build time.** It is constructed as
   `dcc.Dropdown(id="restart-ds-type", options=gated_dataset_options(DEFAULT_MODEL_KEY), ...)` and the
   **only** output on it in the whole app is `restart-ds-type.value` (:5268) — **never `.options`**.
   So it is permanently gated against `cascor` and shows `equities_seq` disabled even if the active
   model were `recurrence`. Independent latent defect; same direction as the deadlock.
2. **`model-class-store` hydrates from the server but `model-selection-store` does not.**
   `hydrate_model_class` (:2514-2531) reads `GET /api/train/status` for the *execution paradigm* only.
   So a backend swapped to recurrence via REST makes `model-class-store == "one_shot"` while
   `model-selection-store` stays `"cascor"` and the dropdown stays gated to 2-D — the dashboard would
   ask for a one-shot Start against a 2-D generator. Divergence, not an unlock.
3. `dataset-plotter-dataset-selector` is a viz-only generator picker (`POST /api/dataset/generate`);
   it never writes the sidebar dropdown.

### (d) Does `_gate_dataset_options_handler` auto-snap, and is there a model-side equivalent? — **CONFIRMED (dataset side) / REFUTED, none exists (model side)**

`dashboard_manager.py:2687`, body at :2702-2706:

```python
options = apply_availability_gate(gated_dataset_options(model_key), self._fetch_generators())
enabled = [option["value"] for option in options if not option.get("disabled")]
if current_value in enabled or not enabled:
    return options, dash.no_update
return options, enabled[0]                     # <-- the auto-snap
```

Executed over the full 2x6 grid (stub `_fetch_generators → []`):

```
(cascor,      equities_seq) -> snaps to 'spirals'
(recurrence,  spirals|xor|mnist|circles|moons) -> snaps to 'equities_seq'
all other (model,dataset) pairs -> no_update
```

So the **dataset follows the model automatically**. There is **no** model-side counterpart:
`model-selection-store.data` has one writer whose sole input is the Select buttons, and
`dir(DashboardManager)` contains no member matching `model` + `snap`/`gate`. The model never follows
the dataset. That asymmetry is precisely why the graph has an unreachable component: the only edge
type that could cross the 2-D/3-D partition — "dataset changed, therefore snap the model" — does not
exist, and the edge that does exist ("model changed, therefore snap the dataset") can never fire
because the model change is itself blocked by the current dataset.

---

## 7. What the browser actually receives (closest artifact to a live check)

```json
Dropdown: {"options": [... {"label": "Equities (sequence) — needs a 3-D model",
                            "value": "equities_seq", "disabled": true}],
           "value": "spirals", "clearable": false, "id": "nn-dataset-type-dropdown"}

Button:   {"children": "Select", "id": {"type": "model-select-btn", "index": "recurrence"},
           "disabled": true, "title": "needs 3-D data"}
```

`disabled: true` reaches the wire on both controls. The remaining assumption — that dash-core-components'
react-select refuses a `disabled` option and that `<button disabled>` fires no `n_clicks` — is standard
component semantics but is **NO ARTIFACT** here, since the local canopy on `:8050` accepts TCP and never
responds. If a browser lane is available, that is the one step left to close.

---

## 8. Bottom line

The claim is **CONFIRMED**, and the mechanism is exactly as stated: each side hard-disables every
option incompatible with the peer's current value, neither side can be unset (`clearable=False`;
`memory` store seeded non-empty and reset to `cascor` on reload), and the dataset-side auto-snap has
no model-side twin. Reachable set from `(cascor, spirals)` = **5 of 12** states, all `model=cascor`.
`(recurrence, equities_seq)` is in a disjoint strongly-connected component of size 1 with no
in-edges from the start component and no out-edges at all. No second writer of either value exists
anywhere in the 175-callback app, the 6 asset JS files, the REST surface, demo mode, snapshots, or
browser persistence.
