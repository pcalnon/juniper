# Lane B agent B1 — adversarial review, lens: CORRECTNESS

**Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) §2 Lane B
**Target of attack**: [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](../../../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) (design of record) and juniper-canopy PR #592
**Subject repo**: `/home/pcalnon/Development/python/Juniper/juniper-canopy`, branch `main`, HEAD `fc62175`
**Date**: 2026-09-05
**Brief**: refute. A finding that the reasoning is sound is worth nothing.

---

## 0. Instrument, and whether it could have produced a different answer

| | |
|---|---|
| **Instrument** | Direct execution of canopy's shipped registry and handler code under `conda run -n JuniperCanopy1 python` (dash 4.2.0, dbc 2.0.4, py 3.13.13), with `dashboard_manager.requests` replaced by a recording stub so commit paths are observed without a network call. Plus extraction of the **original TypeScript** for `dcc.Dropdown` from dash's shipped source map `async-dropdown.js.map`. |
| **Could it produce a different answer?** | Yes, and it did — three times. My first availability probe marked the wrong upstream generator (`equities` instead of `equities_seq`) and produced a false "the availability gate can never grey equities_seq" result, which I then refuted against `juniper-data/juniper_data/api/routes/generators.py:113`. My hypothesis that `equities_seq` was not a juniper-data generator at all was **REFUTED** the same way. The four-scenario availability probe produces four *different* verdicts, so it is not a constant function. |
| **Sample size** | Handler-level: the full 6-dataset × 2-model grid (12 pairs), 4 availability scenarios, 2 null encodings (`None`, `''`), 9 dropdown consumers, 3 backend types. |
| **What was NOT done** | No browser DOM run (the operator's stack on :8050 was not disturbed, per constraint). No live service call. No `equities_seq` artifact was generated (needs `yfinance` + network). No PR-592 branch checkout. |
| **Scratch probes** | `p1_snap.py`, `p3_nulls.py`, `p4_avail.py`, `p5_counterfactual.py`, `p6_consumers.py` under the session scratchpad. Their material outputs are inlined below so the findings stand without them. |

---

## FATAL

### F1 — `⊥`-at-mount (§4.10 / OQ-N2, an ACCEPTED and dispositioned decision) is destroyed one second after page load, by the very callback the design relies on

`params-init-interval` is `dcc.Interval(..., interval=1000, max_intervals=1)` at `src/frontend/dashboard_manager.py:1871`, and it is an **Input** of `gate_dataset_options` (`:2608`) precisely so the availability gate runs at first paint (the comment at `:2601-2603` says so). At `t≈1 s` that pass calls the snap with `current_value = None`:

```python
# src/frontend/dashboard_manager.py:2702-2706
if current_value in enabled or not enabled:
    return options, dash.no_update
return options, enabled[0]
```

`None in ['spirals', 'xor', 'mnist', 'circles', 'moons']` is `False`, and `enabled` is non-empty, so it returns `enabled[0]`. MEASURED, all four availability scenarios:

```
### A. juniper-data UP, equities extra ABSENT       cascor gate(bottom) -> 'spirals'
### B. juniper-data DOWN -> canopy 4-entry fallback cascor gate(bottom) -> 'spirals'
### C. proxy raised -> empty list                   cascor gate(bottom) -> 'spirals'
### D. everything available                        cascor gate(bottom) -> 'spirals'
```

**No change in the specified set preserves `⊥` here.** §4.7 changes only the `not enabled` arm. §4.1 states the opposite behaviour as *correct*: "the snap behaves identically whether the current value is `None` or `'spirals'`". §4.1 and §4.10 are therefore mutually contradictory: §4.1 relies on the snap moving `None`, §4.10 requires it not to.

**Second-order, and worse.** §4.10's hydration must write `Output("nn-dataset-type-dropdown", "value")` — an Output **solely owned** by `gate_dataset_options` at `:2606` with no `allow_duplicate`. A second writer requires `allow_duplicate=True`, and the natural mount trigger for hydration is the same `params-init-interval`: two writers on one Output fired by one Input, resolution order undefined. §4.10 says "ordering is not negotiable" about PR sequencing and says nothing about this ordering.

**Why FATAL rather than SERIOUS**: OQ-N2 is not an open question — it is dispositioned ACCEPTED with a named prerequisite (N10), and PR 2 exists to satisfy it. The specified work cannot deliver the decision it was scoped from.

### F2 — §4.11's "clear model" affordance ships a Start button with no model selected and no gate

The design introduces a **second null** — a cleared model — in N11/§4.11, and never extends `⊥`'s formal treatment (§2), `I-safe`, `I-cover`, or the G1b assertion to cover it. G1b as written is `Reach ⊆ compatible ∪ {(m, ⊥)}`; once the model axis is clearable, `(⊥_model, spirals)` is reachable and belongs to neither term, so **the design's own G1b fails against the design's own §4.11**.

That is a test-plan defect. The runtime defect is worse. MEASURED:

```
model_is_trainable(None)                                     -> True
model_is_trainable('')                                       -> True
_update_button_appearance_handler(button_states={}, model_key=None)[0]  -> False   # Start ENABLED
_train_gate_notice_handler(None)                             -> None              # no notice rendered
```

Source: `src/model_registry.py:245-246`

```python
if not model_key:
    return True
```

The docstring justifies this fail-open for "a transient desync" — a *reason to guess* — but §4.11 turns it into the response to a **deliberate** clear. Both consumers of `model-selection-store.data` that gate training read through it: `update_button_appearance` (`:4491`, sole writer of `start-button.disabled` at `:4473`) and `annotate_train_gate` (`:2661`). So after §4.11 ships:

- Start is **enabled** at `(⊥_model, d)`;
- no train-gate notice explains anything;
- the POST reaches the backend, which still holds the previously-selected model, and trains it while the sidebar shows no model.

That is the X1 silent-misattribution class that PR 1 exists to close, reintroduced by PR 3 — the exact failure mode the design names in §4.11 for the *dataset* axis ("the mutual-gate trap again, on the model axis — a defect this design exists to prevent, shipped by the affordance meant to relieve it") and does not notice on the training-control axis. §4.8 (X5) gates Start on the dataset value only.

### F3 — the §4.2 null-dataset guard is specified at one of **three** commit paths; the other two are unguarded, one is destructive, and the function §4.2 names as "the correct idiom" is itself one of the unguarded two

MEASURED with `requests` stubbed (each line is the recorded outbound call):

| handler | call at `dataset=None` | returned to the UI |
|---|---|---|
| `_apply_dataset_handler` (`:2831`) | `POST /api/stage_dataset {'nn_dataset_type': None}` | `(True, None)` → **pending-dataset banner opens** |
| `_accept_live_switch_handler` (`:6046`) | `POST /api/live_dataset_swap {}` | `Alert("Live dataset swap complete. …", color="success")` |
| `_restage_dataset` (`:5631`) | `POST /api/stage_dataset {}` | `(True, '')` — success |

**(a) X4 is destructive, not vacuous.** §4.2 says the `None` "strips into a vacuous 200 plus a false pending-banner". Trace it through: canopy `main.py:4190` does `body.model_dump(exclude_none=True)` → `{}` → `backend.stage_dataset()` → cascor `POST /v1/training/dataset`, whose route docstring is explicit (`juniper-cascor/src/api/routes/training.py:276-277`):

> *"An empty body clears any prior staging (idempotent with DELETE for that case)."*

So Apply Dataset at `⊥` **discards the operator's staged dataset change** and canopy then opens the banner claiming one is staged. The guard is more necessary than the design argues, and the design's severity statement is wrong.

**(b) The live-swap path is not mentioned anywhere in the design.** `dashboard_manager.py:6068` strips `None` client-side (`payload = {k: v for k, v in payload.items() if v is not None}`), and `main.py:4315` strips again. `SwapDatasetLiveRequest` inherits every field optional (`juniper-cascor/src/api/models/training.py:253`), so `lifecycle.swap_dataset_live()` runs with no config: per its own docstring (`juniper-cascor/src/api/lifecycle/manager.py:3038-3041`) it snapshots pre-swap state, signals stop on the training future, awaits its exit, and discards the in-flight candidate pool. **A `⊥`-state Accept interrupts a running training and canopy renders "Live dataset swap complete."** Reachability is narrower than Apply Dataset — `_gate_live_switch_button_handler` (`:6000-6009`) requires `experimental_functions AND is_running` — but the consequence is larger, because it lands on a live experiment.

Ahead of that, `_open_live_switch_modal_handler` (`:6011`) skips any `None` row, so at `⊥` the confirmation modal renders `"No dataset config selected in the sidebar."` and the Accept button remains live. MEASURED.

**(c) The cited exemplar is not a guard.** §4.2 says *"The correct idiom already exists at `_restage_dataset:5629-5631`."* That code omits the key when `dtype is None` — which produces the **same empty body**, and therefore the same cascor unstaging. Omitting a key and sending `None` are the same thing downstream of `exclude_none=True`. The only actual guard in §4.2 is the second half ("disable Apply Dataset at `⊥`"), and an implementer following the named exemplar will ship the weaker one.

---

## SERIOUS

### S1 — PR #592's `_selection_is_live` reports "Active: Recurrence (LMU)" over a recurrence service that has never connected

`RecurrenceBackend.initialize()` (`src/backend/recurrence_backend.py:301-304`):

```python
async def initialize(self) -> bool:
    """No eager connection — the adapter surfaces connection errors at fit time."""
    logger.info("RecurrenceBackend ready (lazy connect) for %s", self._adapter.service_url)
    return True
```

It cannot fail, so the 502 branch in `_swap_backend` (`src/main.py:3905-3907`, `if not await new_backend.initialize(): … 502`) is **unreachable for recurrence**. The backend is installed (`main.py:3909`) and the response is `{"backend": "recurrence", "swapped": True}` whether or not the service exists. PR 592's predicate compares backend **type**, never **health**:

```python
backend_type = data.get("backend")
if not backend_type:
    return None
spec = get_model_spec(data.get("nn_model", ""))
selection_needs_recurrence = spec is not None and spec.provider == RECURRENCE_PROVIDER
return selection_needs_recurrence == (backend_type == DashboardManager.RECURRENCE_BACKEND_TYPE)
```

→ `True == True` → `True` → *"Active: Recurrence (LMU)"* while nothing can train.

**In fairness to the departure**: the design's §4.4 predicate (`swapped is False`) is equally blind here — `swapped` is `True` on this path. This is a gap in **both** predicates, not a regression introduced by the departure. It is SERIOUS because the PR's stated purpose is "a model whose displayed identity differs from the live backend is a defect" (N5), and this state satisfies exactly that description while the new code declares it healthy.

### S2 — PR #592 renders a DemoBackend synthetic simulation as *"Active: CasCor (Cascade-Correlation)"*, and its own test asserts that as correct

`create_backend` falls back to `DemoBackend` when no cascor URL is configured (`src/backend/__init__.py:107-108`, *"No CasCor service URL configured — falling back to demo mode"*), and `DemoBackend.initialize()` auto-starts a simulation. `backend_type == "demo"` (`src/backend/demo_backend.py:70-71`). The predicate partitions the domain into `{recurrence}` vs everything else, so `demo` agrees with a `cascor` selection:

```
nn_model=cascor  backend=demo  -> _selection_is_live = True   -> "Active: CasCor (Cascade-Correlation)"
```

`test_cascor_selected_over_a_cascor_family_backend_is_live` parametrizes `["cascor", "demo"]` and **asserts** `True`. A benchmark run filed under "CasCor" while a synthetic demo simulation trains is the misattribution class the PR exists to close; the chosen predicate cannot separate real cascor from simulated cascor **by construction**, and the PR ratifies that.

Compounding it (MEASURED, unchanged by PR 592): `nn-model-summary` has exactly one callback writer (`:2593`, fired only by a `model-select-btn` click) plus the layout seed `_initial_model_summary` (`:1220`), which calls `_model_summary_text({"nn_model": DEFAULT_MODEL_KEY, "status": …})` with **no `backend` key**. `_selection_is_live` returns `None` on a missing key, so at first paint — in every configuration including demo mode and a dead cascor — the sidebar reads *"Active: CasCor (Cascade-Correlation)"*. A user who never opens the model modal never sees the new string.

### S3 — PR #592's load-bearing test pins a `backend_type` value that does not exist

The domain is exactly three literals, and the protocol says so:

| value | site |
|---|---|
| `"service"` | `src/backend/service_backend.py:83-84` |
| `"recurrence"` | `src/backend/recurrence_backend.py:118-121` |
| `"demo"` | `src/backend/demo_backend.py:70-71` |
| *(docstring)* | `src/backend/protocol.py:323` — `"""Return 'demo', 'service', or 'recurrence' for logging/status."""` |

`"cascor"` is never a `backend_type`. PR 592's class-attribute comment says *`The other values ("cascor", "demo") both serve cascor-family models`*, and **`test_noop_reselect_of_the_live_model_still_reads_active`** — the test the PR body names as its whole justification for departing from §4.4's `swapped is False` — asserts against `{"nn_model": "cascor", "backend": "cascor", …}`, a payload `_model_state_response` (`main.py:3860-3871`) can never emit; the real value for that scenario is `"service"`.

Re-derived: substituting `"service"` the predicate still returns `True`, so the **logic survives and the departure from §4.4 is defensible on its merits** — `swapped is False` genuinely is also the healthy no-op re-select (`main.py:3891`, five enumerated paths, two of them healthy). What does not survive is the *evidence*: the guard against the naive predicate is demonstrated on an unreachable payload. Related: the rendered message `f"… NOT ACTIVE — the {data.get('backend')} backend is running"` will read *"the service backend is running"* in production, a string no test covers.

### S4 — §9's "the LMU has zero available datasets in the container", and with it §4.7 / G1d's premise, does not hold through canopy's gate in the likeliest deployment

Two fail-open layers sit between juniper-data and the gate:

1. `is_generator_available` (`src/dataset_schema.py:255-258`) ends `return availability_map(generators).get(name, True)` — a generator **absent** from the list is available.
2. canopy's own proxy falls back to a **4-entry list with no `available` key and no equities entry** when juniper-data is unreachable (`src/main.py:1865-1874`: `spiral`, `xor`, `circles`, `moon`).

MEASURED across four scenarios:

```
A. juniper-data UP, equities extra ABSENT   recurrence enabled=[]                gate(bottom) -> no_update (stays at bottom)
B. juniper-data DOWN -> 4-entry fallback    recurrence enabled=['equities_seq']  gate(bottom) -> 'equities_seq'
C. proxy raised -> empty list               recurrence enabled=['equities_seq']  gate(bottom) -> 'equities_seq'
D. everything available                     recurrence enabled=['equities_seq']  gate(bottom) -> 'equities_seq'
```

Only scenario A reaches §4.7's recovery state. In B and C the UI says the dataset is available and the failure surfaces later as a 501 at generate time. `yfinance` is genuinely absent from `juniper-data/requirements.lock` (181 lines, zero matches for `yfinance` or `equities`; it is declared only in `pyproject.toml:51`), so §9's *packaging* claim is correct — but §4.7 is scoped to "the gate says unavailable", and the deployed failure mode is "the gate says available and it fails later". Those are different sets, and G1d ("injected all-unavailable generator list") tests only the first.

### S5 — the `equities_seq` `task_type` disagreement is real, and "fixing it" in the obvious direction deletes the reachability target

MEASURED, both declarations:

- canopy: `task_type="regression"` — `src/model_registry.py:141` (spec at `:138-149`, `ndim=3`, `temporal="irregular"`)
- juniper-data: `"task_type": "classification"` — `juniper_data/api/routes/generators.py:117`

Executed counterfactual against the live registry:

```
as shipped (regression)                -> compatible_models(equities_seq) = ['recurrence']
aligned to upstream (classification)   -> compatible_models(equities_seq) = []      reason='needs regression data'
```

So aligning canopy to upstream gives recurrence **zero** compatible datasets and deletes `(recurrence, equities_seq)` — the pair §4.1's traversal exists to reach. **The design's §12 nowhere states that upstream `task_type` is not authoritative for canopy's seeds**, and §12's ten new seeds are precisely where an implementer would copy it.

**The third possibility both registries get wrong, and it is the real answer.** The generator is **dual-target**:

- `_WINDOW_KEYS = ("X", "y", "y_reg", "date", "dt", …)` — `juniper_data/generators/equities_seq/generator.py:56`
- `y_dir = EquitiesGenerator._direction_onehot(frame)` and `y_reg = EquitiesGenerator._regression_target(frame, params.regression_target)` — same file, `:174-175`
- `_regression_target` returns `(n, 1)` float32 continuous (`return`, `log_return`, `next_close`) — `juniper_data/generators/equities/generator.py:988-1008`

and the LMU reads the regression array preferentially:

- `if f"y_reg_{split}" in arrays: y = …` else fall back to `y_{split}` — `juniper-recurrence/juniper-recurrence-model/juniper_recurrence_model/data.py:147-153`
- `self.task_type: TaskType = "regression"` hardcoded on `LMURegressor` — same package, `model.py:92`

juniper-data's label describes the canonical `y_*` array (it drives `n_classes` / `class_distribution` metadata); canopy's describes the task the selected model performs. **Both are locally correct; neither vocabulary has a "both" value.** juniper-data's `task_type` is a per-generator constant read at `juniper_data/api/routes/datasets.py:306` with no param input, so `regression_target` cannot move it.

Two further measurements that bound the finding:

- **The drift is inert across the wire.** `GeneratorInfo` (`juniper_data/core/models.py:143-162`) has fields `name, version, description, available, install_hint, params_schema` — **no `task_type`**. Nothing propagates to canopy, and canopy reads `task_type` only from its own registry.
- **The `task_type` clause is inert inside canopy today.** Executed: dropping it from `compatible()` changes **0 of 12** verdicts across the seed grid — `ndim` + `temporal` already partition cascor from recurrence. It becomes load-bearing the moment a second 3-D Δt model or a 2-D regression dataset is seeded, i.e. exactly at §12.

### S6 — §4.3's Y9 fix collides with a shipped test, because `⊥` and "unknown value" are the same state today

`_build_model_selection_table` (`:3018`) does `dataset = get_dataset_spec(dataset_value) if dataset_value else None`, and `get_dataset_spec('does-not-exist')` also returns `None`. Two shipped tests pin both collapses to the same behaviour:

- `test_table_without_a_dataset_treats_all_models_as_compatible` — `src/tests/regression/test_model_table.py:169-173` (the test §4.1 cites; the cite is accurate)
- `test_table_unknown_dataset_value_treats_all_models_as_compatible` — `:175-179`

Y9 is real (MEASURED: at `dataset=None`, `reason is None` for every model at `:3033-3041`, so every row renders `"✓ compatible"`). But §4.3's "render what the row would require" needs `⊥` distinguished from a stale value, which the current signature cannot express. The change either breaks `:175-179` or requires a new argument the design does not scope.

---

## MINOR

| id | finding | evidence |
|---|---|---|
| **M1** | The design's "All **ten** Python consumers of `nn-dataset-type-dropdown.value`" is not reproducible. The dependency graph has **nine**: `:2576`, `:2609`, `:2624`, `:2637`, `:2649`, `:4935`, `:5166`, `:5223`, `:5298` — plus two Outputs (`:2605`, `:2606`) and the layout declaration (`:1331`). | exhaustive grep of `src/`, `juniper_canopy/` (which contains only `__init__.py`), and `util/` |
| **M2** | "there are **zero** JS consumers" is true of the dependency graph but not of the data flow: `PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS` reads `oneshot-start-params-store` (`:4398`), computed from the dropdown value at `:2635-2640`. It **is** null-safe (`if (command === 'start' && oneshot_start_body)`), so the conclusion holds; the framing does not. | `dashboard_manager.py:111-240`, `:2631-2640` |
| **M3** | Line references in §4 have drifted 3–63 lines against HEAD `fc62175`: `_update_button_appearance_handler` is `:7250` not `:7187`; `_apply_dataset_handler` `:2831` not `:2845`; `_restage_dataset` `:5631` not `:5629`; cascor's `Literal` `:234` not `:235`. §4.4's citation of the `ok=True`-then-fail pattern at `recurrence_backend.py:154-156` points at `start_training`, not `initialize()` (which is `:301-304` and starts no thread) — so §4.4's evidence for N6 is misattributed even though N6's point stands. | direct reads |
| **M4** | A clear performed in the first ~1 s after load is undone by the interval-driven gate pass (F1's mechanism, in the transit case). Narrow, but it makes §4.1's traversal non-deterministic for a fast operator. | `:1871` `interval=1000` |
| **M5** | `''` and `None` diverge downstream: `_apply_dataset_handler('')` sends `{'nn_dataset_type': ''}` **un-stripped** by `exclude_none=True`, so it reaches cascor's `Literal[…]` and 422s/502s rather than clearing staging. Moot for the ✕ (see below), but any guard written as `if not dataset_type` vs `if dataset_type is None` will behave differently. | MEASURED, probe 6 |

---

## NOT A DEFECT — where I attacked and found nothing

Recorded plainly, per §6 of the procedure ("a round that changes nothing must be recorded as such").

**N-A. The ✕ emits `null`, not `''` — attack surface 2 is REFUTED.** I did not read docs. I extracted the original TypeScript from the shipped source map at `/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/dash/dcc/async-dropdown.js.map` (`webpack:///./src/fragments/Dropdown.tsx`):

```tsx
const handleClear = useCallback(() => {
    const finalValue: DropdownProps['value'] = multi ? [] : null;
    handleSetProps(finalValue);
}, [multi, handleSetProps]);                                   // :214-217
```

and, for the keyboard/deselect route, `updateSelection` single-select empty → `if (clearable) { handleSetProps(null); }` (`:136-141`). `handleSetProps` calls `setProps({value: newValue})` (`:99-110`); the `debounce && isOpen` local-only branch does not apply, because the ✕ is on the trigger and `e.preventDefault()`s (`:516-522`), and canopy sets no `debounce`. Every `is None` / `if not x` check in the design behaves as intended. The ✕ is also correctly gated: `canClearValues = clearable && !disabled && !!sanitizedValues.length` (`:421`).

**N-B. The traversal does terminate at the target — attack surface 1's core claim survives.** MEASURED: `enabled[0]` **is** `equities_seq` in scenarios B/C/D, for a structural reason, not a coincidence — recurrence has exactly one compatible dataset (`compatible_datasets(recurrence) == ['equities_seq']`, executed), and `apply_availability_gate` (`src/dataset_schema.py:268-286`) maps over the option list without reordering or removing entries, so registry order is preserved. In scenario A (`enabled == []`) the snap returns `no_update` and the value stays at `⊥` — incomplete, not invalid. **The catch-22 itself is resolved by the `⊥` cut vertex.**

**N-C. No `⊥` reaches persistent storage — attack surface 4 finds nothing on that route.** `nn-dataset-type-dropdown` (`:1330-1337`) declares no `persistence` / `persistence_type`; `model-selection-store` (`:1842`) and `model-class-store` (`:1839`) are `storage_type="memory"`; `oneshot-start-params-store` (`:1848`) is `"memory"`. The only nearby persisted widget is `experimental-functions-toggle` (`:1742-1743`). Nothing `⊥` survives a reload or reaches `layout-state-store`. The commit paths in F3 are the real "committed `⊥`" answer, not storage.

**N-D. The empty-set state does not strand the user — attack surface 7's stranding hypothesis is REFUTED.** At `(recurrence, ⊥)` with nothing available, both Select buttons in the model table are enabled (`_build_model_selection_table(None, …)` → all `disabled=False`, pinned by `test_model_table.py:169-173`), so re-selecting cascor re-fires the gate and snaps to `spirals`. The recovery state recovers. What §4.7 *does* miss is scenario coverage, not escapability — see S4.

**N-E. The Start gate is enforceable where §4.8 puts it.** `Output("start-button", "disabled")` has exactly one writer (`:4473`, and the comment at `:4489-4492` says so deliberately — "no racy second writer"), and **both** Start transports key off `Input("start-button", "n_clicks")` (clientside `:4394`, server-side `:4419`), which a native disabled `dbc.Button` cannot emit. Adding the dataset to `_update_button_appearance_handler` is a sound place to gate — on the **dataset** axis. See F2 for the model axis.

**N-F. `equities_seq` is a real juniper-data generator.** I hypothesised that canopy's `generator_name_for_type('equities_seq') → 'equities_seq'` pointed at a non-existent upstream name (§12.1 lists `equities` among the unseeded ten), which would have made the whole reachability target a dead pair. **REFUTED** at `juniper_data/api/routes/generators.py:113` — `equities` and `equities_seq` are two distinct registered generators. Recorded because it is exactly the confident-wrongness the procedure's §5.2 exists to catch, and it was caught by re-deriving rather than by reasoning.

**N-G. §4.9's staging analysis is correct.** cascor's `StageDatasetRequest.dataset_type` is `Literal["spirals","xor","mnist","circles","moons","equities","gaussian","checkerboard"]` (`juniper-cascor/src/api/models/training.py:234`) — **no `equities_seq`**, so Apply Dataset at `(recurrence, equities_seq)` against a cascor backend does fail as the design says.

---

## Verdict

**The `⊥` cut vertex resolves the stated catch-22.** MEASURED at handler level, in three of four availability scenarios, the traversal `(cascor, spirals) → clear → (cascor, ⊥) → Select Recurrence → (recurrence, equities_seq)` completes, and in the fourth it parks at `⊥` without becoming invalid. `clearable=True` emits `None`, every one of the nine Python consumers survives it without raising, and nothing persists.

**But the specified change set, taken as written, does not ship correctly.** Three defects are fatal to the specification rather than to the mechanism: it cannot deliver the accepted `⊥`-at-mount decision (F1); the new model-side null it introduces in §4.11 ships an ungated Start and reintroduces the misattribution class PR 1 exists to close (F2); and the null-dataset guard covers one of three commit paths while naming as "the correct idiom" a function that is itself one of the unguarded two (F3). PR #592's departure from §4.4 is defensible on its logic and undemonstrated by its evidence (S1–S3).

**What this evidence cannot support.** No DOM was driven, so `⊥` has still never been observed in a browser — OQ-N5's re-run remains the only thing that can confirm the Radix dropdown renders and clears as the source says it does. No `equities_seq` artifact was generated, so "the LMU trains on it end-to-end" is INFERRED from the code path (S5), not measured. And the deployed container's actual `available` flag for `equities_seq` was not read — S4's four scenarios bound the behaviour, they do not tell you which one is live.
