# Lane B1 — Adversarial review: the model-Select un-gate fix is the wrong fix

**Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane B
**Brief argued**: ship D4 / §5.5 (inline ✕ / `clearable=True`), not the unary `:3050` predicate.
**Date**: 2026-09-02
**Evidence standard**: every claim below is backed by a `file:line` or by executed code
(`probe.py`, `probe2.py`, `probe3.py`, `probe4.py` in this scratchpad, run under
`conda run -n JuniperCanopy1`). Docstrings are marked as CLAIMS where that is all that exists.

> **Script-placement note.** The four probes analyse repository content and by
> `juniper-ml/CLAUDE.md` § Script placement they belong in `util/ad-hoc/`. This review was
> commissioned read-only ("DO NOT EDIT" both repos), so they were written to the session
> scratchpad instead and **will be lost when the session is reaped**. If any of the executed
> evidence below is to be re-derivable, copy `probe.py` and `probe2.py` into
> `juniper-canopy/util/ad-hoc/` (or `juniper-ml/util/ad-hoc/`) before this session ends —
> `probe.py` reproduces the R1 parking result and `probe2.py` the R2 table result.

---

## 0. Scoreboard

| # | Refutation | Strength | Evidence |
|---|---|---|---|
| R1 | The unary fix **parks the UI on an invalid pair and fails OPEN** — in exactly the configuration it exists to enable | **fatal** | executed |
| R2 | The D4 mechanism is **already fully implemented, tested and passing today**; only `clearable=False` gates it | **fatal to "resurrects existing code"** | executed + `test_model_table.py:170-173` |
| R3 | The snap **substitutes** where §5.6 says **clear**; the code calls it "dataset-primary" and it is not | strong | `:2695` |
| R4 | `clearable=False` **predates the design by 5 weeks** — D4 was never rejected, it was skipped | strong | `git log -L` |
| R5 | The snap **destroys the user's dataset choice and their staged generator params** on a round trip | strong | executed |
| R6 | Start is **never gated on the dataset**, so canopy has no last line of defence | strong | executed |
| R7 | The unary fix's parked state emits a generator name **juniper-data does not have** | moderate | executed |
| R8 | FR9's fail-closed **never reaches the operator** — canopy reports "Training started successfully" for a run that never started, so the fix's safety net is invisible exactly where it is needed | **amplifies R1 to fatal** | `recurrence_backend.py:156`, `dashboard_manager.py:6308-6324` |
| R9 | `clearable=False` makes **either** §5.6 policy unimplementable — substitution is not a choice, it is the only option left | strong | `:1334` vs design `:165-166` |
| R10 | The ✕ state is **already pinned by a passing regression test** whose comment says *"(e.g. cleared)"* — the fix's own "existing tested code" phrase describes the alternative | **fatal to claim 2** | `test_model_table.py:170-173` |
| R11 | A narrowly-scoped unary `:3050` makes each row **self-contradictory** — "needs 3-D data" beside an enabled Select, and the §5.8 "No compatible model" alert above an all-enabled table | strong | `:3033-3035`, `:3070-3079` |

Self-test of my own brief: **SURVIVED**, with one honest defect found and reported (§7, D-W1).

**One-sentence version.** The recommended fix reproduces the very parking bug it was designed
to avoid — in the deployment shape it exists to serve — behind an enabled Start button and a
green "Training started successfully"; while the alternative it displaces is already
implemented, already correct, fails closed, and costs one token.

---

## 1. R1 — the unary fix is unsound in the exact case it is built for (FATAL)

The rebuttal to a naive `disabled=False` is that `_gate_dataset_options_handler`'s
`if current_value in enabled or not enabled: return options, dash.no_update`
(`dashboard_manager.py:2704-2705`) parks the UI when a model has no compatible dataset.
The recommended fix answers this by making the predicate unary on
`compatible_datasets(model)` — "a model with no compatible dataset stays disabled, so
`enabled` is never empty."

**That reasoning is wrong, and I verified it by execution.** The unary predicate reads
`model_registry.compatible_datasets()` — a **pure compatibility** resolver
(`model_registry.py:329-334`, docstring: *"Pure compatibility — no status filtering"*).
The runtime `enabled` list is computed from a **different, strictly narrower** set:

```python
# dashboard_manager.py:2702-2703
options = apply_availability_gate(gated_dataset_options(model_key), self._fetch_generators())
enabled = [option["value"] for option in options if not option.get("disabled")]
```

`apply_availability_gate` (`dataset_schema.py:268-286`) additionally disables any dataset
whose juniper-data generator reports `available: False`. So:

> **`compatible_datasets(model)` non-empty does NOT imply `enabled` non-empty.**

And this is not hypothetical. `equities_seq` — the *only* dataset compatible with
`recurrence` — is gated behind juniper-data's optional `equities` extra:
`juniper-data/juniper_data/tests/unit/test_api_routes.py:414` asserts
`by_name["equities_seq"]["available"] is EQUITIES_DEPS_AVAILABLE`, and
`juniper_data/api/routes/generators.py:178-200` derives `available` from the generator's
`is_available()` hook.

Executed (`probe.py`, deployment **without** the equities extra):

```
[NO equities extra] model=recurrence cur=spirals enabled=[] -> value=NO_UPDATE(park)

== THE PARKING TEST: unary fix, deployment WITHOUT the equities extra ==
  user selects recurrence from (cascor, spirals); gate returns value = NO_UPDATE(park)
  dropdown options now: [('spirals', True), ('xor', True), ('mnist', True),
                         ('circles', True), ('moons', True), ('equities_seq', True)]
  => UI pair is (recurrence, spirals). compatible?  False
```

Under the recommended fix, in a deployment lacking one optional data extra:

1. `recurrence`'s Select is **enabled** (unary gate passes — `compatible_datasets` is non-empty).
2. The user clicks it. `model-selection-store` → `recurrence`, `model-class-store` → `one_shot`.
3. The gate fires, `enabled == []`, hits `:2704`, returns `dash.no_update`.
4. The dropdown **stays on `spirals`** and **every one of its six options is now disabled** —
   the user cannot repair the state from the control that caused it.
5. The UI is parked on `(recurrence, spirals)` — `compatible(...) is False`, executed.

This is the *identical* defect the recommended fix cites as the reason a naive
`disabled=False` is unsound. The unary form does not avoid it — **it narrows the trigger
from "a model with no compatible dataset" to "a model whose compatible datasets are all
unavailable", and the recurrence model is a member of that second set whenever the
deployment ships without `pip install juniper-data[equities]`.**

Worse, this is a **fail-open**, and I confirmed there is no downstream catch in canopy
(`probe2.py`):

```
== _resolve_oneshot_start_body_handler('one_shot', 'spirals')  [the parked pair] ==
    {'dataset': {'generator': 'spirals'}}
== _update_button_appearance_handler: is Start gated on the DATASET at all? ==
   model=cascor      start_disabled=False
   model=recurrence  start_disabled=False
```

Start is live, and pressing it POSTs a 2-D spiral generator to the LMU one-shot path
(`dashboard_manager.py:7100-7101` server transport; `:195-197` clientside transport).

**Contrast — the ✕ under the identical deployment** (`probe.py`,
`model=recurrence cur=None enabled=[] -> NO_UPDATE(park)`): the dataset stays `None`,
`_resolve_oneshot_start_body_handler("one_shot", None)` returns `None` (executed), and
`if command == "start" and oneshot_start_body:` at `:7100` is skipped, so Start posts a bare
body.

**And the asymmetry is structural, not incidental.** `RecurrenceBackend.start_training`
(`src/backend/recurrence_backend.py:130-156`) has exactly one synchronous rejection and one
synchronous success, and the two fixes land on opposite sides of it:

```python
# recurrence_backend.py:138-140  — the ✕ path lands HERE, before any thread starts
dataset_ref = {k: kwargs[k] for k in _DATASET_REF_KEYS if kwargs.get(k) is not None}
if not any(dataset_ref.get(k) for k in ("dataset_id", "name", "generator")):
    return ControlResult(ok=False, error="no dataset reference (need one of dataset_id / name / generator)")
...
# recurrence_backend.py:153-156  — the unary path lands HERE
thread = threading.Thread(target=self._run_fit, ...)
thread.start()
return ControlResult(ok=True, is_training=True, message="recurrence fit started")
```

- **✕ path**: no `generator` key at all → `ok=False` **before** `thread.start()` → canopy 409
  (pinned, `src/tests/regression/test_recurrence_routes.py:164-171`) → `raise_for_status()`
  raises at `:7103` → a **visible, synchronous danger alert**.
- **Unary path**: `{"generator": "spirals"}` is *well-formed enough to pass the guard* → the
  thread starts → `ok=True` → canopy shows **"Training started successfully"**. The real
  failure lands later in `_run_fit` (`:158-176`) as `self._error` / `state="failed"`, which
  `_completion_reason_label` (`:6308-6324`) does not map, so **nothing renders**.

**The ✕ fails closed and says so; the unary predicate fails open and says the opposite.** That
inverts the FR9 defence-in-depth argument onto the fix that invokes it.

---

## 2. R2 — the D4 mechanism is already built, already TESTED, and already passing (FATAL to claim 2)

§5.5 of `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` (line 152)
says clearing the dataset means "the model table re-activates fully via the gate as a
side-effect". That side-effect is **not a thing to be written. It exists.**

```python
# dashboard_manager.py:3018
dataset = get_dataset_spec(dataset_value) if dataset_value else None
# dashboard_manager.py:3033
reason = model_reason(model, dataset) if dataset is not None else None
```

Executed (`probe2.py`) against the real registry:

```
== _build_model_selection_table(None, 'cascor') ==
    ({'type': 'model-select-btn', 'index': 'cascor'},     'Selected', False, 'Currently active')
    ({'type': 'model-select-btn', 'index': 'recurrence'}, 'Select',   False, 'Select this model')

== _build_model_selection_table('spirals', 'cascor')  [TODAY] ==
    ({'type': 'model-select-btn', 'index': 'cascor'},     'Selected', False, 'Currently active')
    ({'type': 'model-select-btn', 'index': 'recurrence'}, 'Select',   True,  'needs 3-D data')
```

Every model becomes selectable the moment the dataset is `None`. Nothing else has to
change. The *only* reason this branch is dead is one token:

```python
# dashboard_manager.py:1331-1334
dcc.Dropdown(
    id="nn-dataset-type-dropdown",
    options=gated_dataset_options(DEFAULT_MODEL_KEY),
    value=DEFAULT_DATASET_TYPE,
    clearable=False,          # <-- this
```

**This directly refutes claim 2** ("the fix resurrects existing tested code rather than
adding new code"). Measured by code added:

| | new predicate | new notice | new label | total new logic |
|---|---|---|---|---|
| Recommended fix (`:3050` unary) | yes | yes (admitted) | yes ("Select — switches dataset to X") | 3 |
| D4 (`clearable=True`) | none | none required — the reverse-gate hint and the §5.8 alert already exist | none | 0 |

The design's own §10 A1 line-item list includes "inline ✕ (D4)" verbatim
(`…MODEL-DATASET-SELECTION-DESIGN.md:318`). It is the one A1 item that was never done.

**The null-dataset state is not aspirational — the codebase is written for it throughout.**
Nine independently-authored branches, none reachable today:

| Site | Null-dataset handling |
|---|---|
| `dashboard_manager.py:3018,3033` | table falls back to "no dataset ⇒ everything compatible" |
| `dashboard_manager.py:2678` | `if model_class != "one_shot" or not dataset_generator: return None` |
| `dashboard_manager.py:2962` | `return dataset_model_hint(dataset_value) or ""` (docstring names the case) |
| `dashboard_manager.py:2753-2755` | `f"…{label}" if label else "Current Dataset"` |
| `dashboard_manager.py:6014-6021` | `if value is None: continue` + "No dataset config selected in the sidebar." |
| `dashboard_manager.py:6053` | `payload = {k: v for k, v in payload.items() if v is not None}` |
| `dashboard_manager.py:5591-5596` | `if value is None: continue` + "No dataset config selected — …" |
| `dashboard_manager.py:5613` | `dtype = dataset_vals.get("dataset_type") or "current"` |
| `dashboard_manager.py:5623-5624` | `if dtype is not None: payload["nn_dataset_type"] = dtype` |
| `dataset_schema.py:139,248,262` | three public helpers typed `value: str \| None`, all with explicit empty-name guards |
| `main.py:3969` | `nn_dataset_type: Optional[str] = None` on the route model |

---

## 3. R3 — the snap is not D5's policy, the code names it wrongly, and `clearable=False` makes D5 unimplementable

§5.6 (`…MODEL-DATASET-SELECTION-DESIGN.md:159`) defines exactly two policies, at `:165-166`:

- *dataset-primary:* keep dataset, **clear** model + notice.
- *model-primary:* keep model, **clear** dataset + notice. *(Fits the model-centric
  benchmarking trajectory.)*

Both say **clear**. Neither says *substitute*. The snap at `:2706` keeps the model and
**substitutes** `enabled[0]` for the dataset. That is a third policy the design never
ratified, and the recommended fix would make it the shipped default while "resolving OQ-6"
(`:305`).

**And here is the structural point.** `clearable=False` at `:1334` means the dataset dropdown
**cannot hold `None`**. Therefore *neither* §5.6 policy is implementable on the dataset side:
"clear dataset" is not an expressible state. Substitution is not a design choice the
implementation made — **it is the only thing `clearable=False` leaves available.**

So the recommended fix's own goal defeats itself:

> It "resolves OQ-6 as model-primary" — and model-primary is defined at `:166` as *"keep model,
> **clear** dataset + notice"*. The fix keeps `clearable=False`, which makes clearing the
> dataset impossible, so it must substitute instead. **It settles OQ-6 in the direction the
> design prefers while permanently foreclosing the behaviour that direction specifies.**

D4's ✕ is a **prerequisite** for D5, not an alternative to it. Ship `clearable=True` and
§5.6 model-primary becomes implementable exactly as written for the first time; the snap at
`:2706` can then be replaced by, or gated behind, an actual clear-plus-notice when OQ-6 is
properly spiked.

I concede the primacy half honestly: `:166`'s parenthetical does lean model-primary, so the
fix picks the right *primacy*. It picks the wrong *action*, and it does so because it declined
to touch the one line that would have let it pick the right one.

And the code's own label for it is inverted:

```python
# dashboard_manager.py:2695
# … If the current selection became disabled, snap to the
# first enabled option (dataset-primary conflict policy, D5).
```

The code **keeps the model** — that is the *model-primary* half of §5.6, not
dataset-primary. So the fix's "resolves OQ-6 as model-primary" would ratify a policy whose
only in-repo documentation calls it by the opposite name. Fixing OQ-6 inside a bugfix, on
top of a mislabelled implementation, in a design whose §9 lists OQ-6 as "decide post-spike"
— that is three separable decisions in one patch.

The "+ notice" that §5.6 attaches to **both** policies is also absent: nothing renders
"we changed your dataset". `annotate_model_hint` (`:2649-2657`) rewrites the *reverse-gate*
hint ("rank-3 (sequence) Δt-aware models only"), which is a different sentence for a
different purpose. The recommended fix acknowledges this by adding a notice — more new code.

---

## 4. R4 — `clearable=False` predates the design of record by five weeks

```
$ git log -L 1337,1337:src/frontend/dashboard_manager.py   # the clearable= line, current :1334
13a5856 2026-05-10 feat(dataset): Apply Dataset UI + Cancel button + adapter wiring (Issue #3 Phase 1, PR-7)
```

The design of record is dated **2026-06-17**. `clearable=False` was set on **2026-05-10**,
in a PR about the Apply-Dataset button, with no relationship to model selection.

And it is an explicit **opt-out of the framework default.** Verified against the installed
runtime (`conda run -n JuniperCanopy1`, dash **4.2.0**), `dcc.Dropdown.__doc__`:

> `clearable (boolean; default True)`: Whether or not the dropdown is "clearable", that is,
> whether or not a small "x" appears on the right of the dropdown that removes the selected value.

D4's "conventional inline ✕" is literally `dcc.Dropdown`'s out-of-the-box behaviour. Somebody
had to type `clearable=False` to remove it, five weeks before anyone decided it should be there.
(`clearable=True` accepted and set cleanly on 4.2.0 — verified.)

D4 was ratified after that, on 2026-06-17, by a **four-agent independent validation pass**
(§12: *"Forks resolved (2026-06-17): … clear → inline ✕ (D4)"*). It was then listed as an
A1 deliverable (§10:318) and **silently omitted**. Nothing supersedes it: I searched every
juniper-ml note referencing the design (`JUNIPER_2026-06-18_…A1-ENABLER-SCOPE.md`,
`JUNIPER_2026-06-23_…A1-III-DASHBOARD-INTEGRATION-SCOPE.md`,
`JUNIPER_2026-06-19_…3D-DATASET-VISUALIZATION-DESIGN.md`,
`JUNIPER_2026-07-02_…STACK-INTERACTIVE-UX-AUDIT-PLAN.md`,
`JUNIPER_2026-06-21_…DOCS-REALITY-AUDIT.md`, `notes/releases/RELEASE_NOTES_juniper-canopy_v0.6.0.md`)
— **no document descopes, defers, or amends D4.** (The "D4" hits in the A1-III scope doc and
the UX audit plan are unrelated D4s belonging to those docs' own numbering.)

So the framing "the design offers two options, pick the cheaper" is false. The correct
framing is: **A1 shipped incomplete, and the reachability hole is the direct consequence of
the one A1 item that was skipped.** Finishing A1 dominates amending D2/FR5/§5.2, all three
of which the unary predicate contradicts:

- D4 line 54 / FR6 line 73 / §5.5 line 152 — the ✕ **implements** these.
- D2 line 52 / FR5 line 72 / §5.2 line 127 ("Compatible rows are selectable; incompatible rows are
  greyed") — the unary predicate **amends** these.
- The `:3005-3010` docstring is explicit that `:3050` implements a ratified choice:
  *"Per ratified option (a) a non-live model stays selectable here — ONLY *incompatible*
  models are disabled."*

The second half of D4 — "a 'clear model / show all' reset on the surface" — is **NO ARTIFACT**;
grep across `src/` for any clear-model affordance returns nothing. That half genuinely needs
building, and I count it against my own brief in §7.

---

## 5. R5 — `enabled[0]` is registry order, and the round trip destroys the user's state

Executed (`probe.py`):

```
== THE SUBSTITUTION TEST ==
  start (cascor, mnist); select recurrence -> equities_seq
  then select cascor back  -> spirals   (NOT mnist)
```

`enabled[0]` is `DATASET_TYPES[0].value` — declaration order in `model_registry.py:132-150`,
chosen for "preserving the original inlined dropdown order" (`:128-131`). It encodes no
user intent whatsoever.

Three things the snap silently discards:

1. **The user's dataset choice.** A benchmarking user on `mnist` who opens the model modal
   to *look* at recurrence loses `mnist` and cannot get it back except by re-picking it.
   In a product whose stated near-term population is 10–20+ model families each with
   several-to-many benchmark variants (§6), "browse the model list" is the *dominant*
   interaction, and the fix makes browsing destructive.
2. **Staged generator params.** `render_dataset_params` (`:2620-2631`) is an `Input` on
   `nn-dataset-type-dropdown.value`, so the snap rebuilds `nn-dataset-schema-params`
   children from scratch (`:2775`), destroying every
   `{"type": "nn-gen-param", "name": …}` control the user filled in. Those are read
   *directly* as `State(..., dash.ALL)` by `apply_dataset` (`:4928-4930`) — there is no
   store to survive the rebuild. Typed spiral fields survive only because they live in a
   separate, merely-hidden block.
3. **Agreement with the backend.** The snap does not un-stage a *staged* dataset. After
   Apply Dataset (`POST /api/stage_dataset`, `main.py:3985`) cascor holds a pending change;
   the snap rewrites the sidebar dropdown but not that pending change, so the visible
   dropdown and the backend's staged dataset diverge with no notice.

`oneshot-start-params-store` is a fourth, weaker case: `_resolve_oneshot_start_body_handler`
(`:2668-2685`) reads **only** `dataset_default_params(dataset_generator)` from the registry —
the user's `nn-gen-param` values never reach the one-shot path at all. So the snap does not
*lose* them there; they were already ignored. (That is a pre-existing defect worth its own
row, not a cost of either fix.)

---

## 6. R6/R7 — two collateral findings the unary fix un-masks

**R6 — Start has no dataset gate.** `_update_button_appearance_handler:7187-7207` force-disables
Start on `model_is_trainable(model_key)` only, i.e. on `status == "live"`. Executed: Start is
enabled for `cascor`, `recurrence`, and `None` alike. Canopy therefore has **no** UI-side
protection against training a parked invalid pair — the whole weight rests on FR9.

**R7 — the one-shot path bypasses the generator alias map.** `:2681` builds
`{"generator": dataset_generator}` from the raw canopy value. Executed:
`_resolve_oneshot_start_body_handler("one_shot", "spirals")` → `{'dataset': {'generator': 'spirals'}}`.
juniper-data's registry key is `"spiral"` (`dataset_schema.py:97-100`
`GENERATOR_NAME_ALIASES = {"spirals": "spiral", "moons": "moon"}`). Every *other* consumer
routes through `generator_name_for_type` (`:2769`, `:2846`); this one does not. It is masked
today because `equities_seq` is the only reachable one-shot generator and is identity in the
map. **The unary fix un-masks it**: the parked `(recurrence, spirals)` state would POST a
generator name that is not in juniper-data's registry at all.

Independently confirmed by the FR9 trace (§10, trace 1), which adds two things I did not have:
juniper-data answers with **400 `"Unknown generator 'spirals'"`**
(`juniper-data/juniper_data/api/routes/datasets.py:99-103`), so the recurrence 3-D shape gate
is *never reached* — the pair fails on a name, not a shape; and
`src/tests/regression/test_oneshot_start_body.py:77-81` **asserts** the un-aliased `"spirals"`,
so the defect is pinned by a passing test. That test also shows the `(recurrence, spirals)`
body is already anticipated at unit level for a pair the UI cannot currently produce.

---

## 7. Adversarial test of my OWN brief — is the ✕ genuinely safe?

I enumerated **every** callback with `nn-dataset-type-dropdown.value` as an `Input` or `State`
(`grep -rn "nn-dataset-type-dropdown" src/`) and checked each against `None`, by execution
where a handler was invocable.

| # | Site | Role | Handler | Verdict with `None` |
|---|---|---|---|---|
| 1 | `:2605-2609` | Out+State | `_gate_dataset_options_handler` | **SAFE** — `None not in enabled` → snaps on the next model change; parks harmlessly if `enabled == []`. Not triggered by the ✕ itself (its Inputs are the model store + the one-shot mount tick) |
| 2 | `:2624` | Input | `_render_dataset_params_handler` | **SAFE** (executed): `('Current Dataset', {'display':'none'}, ['No adjustable parameters…'])`. Cosmetic wart, D-W2 |
| 3 | `:2637` | Input | `_resolve_oneshot_start_body_handler` | **SAFE** (executed) → `None`; Start then posts no body and the recurrence backend bails |
| 4 | `:2649` | Input | `_dataset_model_hint_handler` | **SAFE** — `:2962` `or ""`; docstring names the case verbatim |
| 5 | `:2576` | State | `_toggle_model_modal_handler` → `_build_model_selection_table` | **SAFE, and this is the point** (executed, §2) |
| 6 | `:4922` | State | `_apply_dataset_handler` | **DEFECT — D-W1, see below** |
| 7 | `:5153` | State | `_open_live_switch_modal_handler` | **SAFE** — `:6014` `if value is None: continue`; `:6020` renders "No dataset config selected in the sidebar." |
| 8 | `:5210` | State | `_accept_live_switch_handler` | **SAFE** — `:6053` filters `None` out of the payload |
| 9 | `:5285` | State | `_open_restart_confirm_modal_handler` | **SAFE** — seeds `restart-ds-type` to `None` (an empty dropdown the operator must fill); `_build_restart_summary:5591-5596` renders "No dataset config selected — …"; `_restage_dataset:5623` omits the key |

Two clientside JS consumers: `:195-197` and `:255-256` both guard on
`if (command === 'start' && oneshot_start_body)`. **SAFE.**

### D-W1 — the one real defect the ✕ introduces (reported against my own brief)

`_apply_dataset_handler:2845` builds the payload unconditionally:

```python
payload: dict = {"nn_dataset_type": dataset_type}
```

Executed with a cleared dropdown:

```
POST http://x/api/stage_dataset body = {'nn_dataset_type': None} -> returned (True, None)
```

`main.py:3993` then does `body.model_dump(exclude_none=True)`, so `stage_dataset()` is called
with **no kwargs**, cascor stages nothing, the route returns 200 — and canopy opens the
"pending dataset change" banner for a change that does not exist. A **vacuous pass**: the UI
claims a staged change that was never staged. Not a crash, not a corruption, but a real wart.

**Cost to fix: two lines**, and the idiom is already in the file — `_restage_dataset:5623`
does exactly the right thing (`if dtype is not None:`). Either guard `:2845` the same way and
surface "select a dataset first", or add `disabled=` to the Apply Dataset button when the
dropdown is empty. This is strictly smaller than the notice + label + predicate the
recommended fix admits it needs.

### D-W2 — cosmetic

`_render_dataset_params_handler(None)` renders "No adjustable parameters — sensible generator
defaults are used." (`:2864`) where "No dataset selected" would be right. One string.

### Does the brief survive?

**Yes.** 8 of 9 Python consumers and both JS consumers are null-safe, five of them via
branches whose docstrings *name the no-dataset case explicitly*, and the most important of them
— the model table — is pinned by a **passing regression test written for the cleared state**
(`test_model_table.py:170-173`, §10(e)). The single defect is a two-line guard in a handler
that already has the correct sibling idiom (`_restage_dataset:5623`), and it is a vacuous pass
rather than an unsound train. Compare R1: the unary fix's failure is an **enabled Start button
on an invalid model/dataset pair, an unrecoverable dropdown, and a green "Training started
successfully"**.

I looked hard for a reason to report "the ✕ is genuinely unsafe" and did not find one. D-W1 is
the closest and it does not come near R1.

---

## 8. The strongest case AGAINST my brief, stated honestly

I am obliged to make this as strong as I can.

1. **The ✕ costs a click the snap does not.** Reaching `(recurrence, equities_seq)` becomes
   ✕ → change → Select (three actions) instead of change → Select (two). For the *current*
   two-model registry, where recurrence has exactly one compatible dataset, the snap's choice
   is not arbitrary — `enabled` is a singleton, executed:
   `model=recurrence cur=spirals enabled=['equities_seq'] -> value=equities_seq`. My
   "registry order is arbitrary" argument is therefore **weakest precisely where it matters
   most today** and only bites on the return leg (`→ spirals`, not `mnist`) and as the
   population grows. An honest scoring gives R5 "strong on the return leg, weak on the
   outbound leg".
2. **The ✕ does not by itself solve discovery.** A user who never thinks to clear the dataset
   still never sees recurrence. D4 buys reachability; it does not buy *discoverability*. The
   recommended fix's "Select — switches dataset to X" label is a genuinely better answer to
   *that* question, and the honest synthesis is that the label belongs on top of the ✕, not
   instead of it.
3. **D-W1 is real and the ✕ causes it.** The unary fix introduces no new null state at all.
   And five of the ten null-dataset consumers have **no test passing `None`** (§10(f)) — the
   ✕ makes five untested branches live at once. That is a genuine test debt the unary fix
   does not incur. (It is test debt, not correctness debt: I verified the branches by
   execution. But "verified by an adversarial reviewer's throwaway probe" is not "covered by
   CI", and I should not pretend otherwise.)
4. **D4's second half is unbuilt.** "clear model / show all" on the model surface: NO ARTIFACT
   (grep across `src/` finds no clear-model affordance). A complete D4 is larger than one token.

   Two honest refinements, one against me and one for me. **Against:** a literal "clear model"
   is *not* a mirror of the dataset ✕ and is genuinely harder. The dataset dropdown is pure UI
   state until Apply; the model selection is backed by a real backend swap
   (`POST /api/model/select`, `:2876-2897`), and there is no "no model" backend state — writing
   `model-selection-store = None` would desync the UI from a backend still running the old
   model. (The null itself is safe: `_gate_dataset_options_handler:2699` returns `no_update`,
   `model_is_trainable(None)` returns `True` at `model_registry.py:242-243`, and
   `_update_button_appearance_handler(model_key=None)` leaves Start enabled — executed.) **For
   me:** §5.5's own wording is *"clear model / **show all**"*, which reads as a table-filter
   reset, not a null model — and clearing `model-search-input` already does exactly that
   (`_toggle_model_modal_handler:2912` rebuilds unfiltered on an empty search). So D4's second
   half is mostly a convenience button over behaviour that already exists, and none of it is a
   prerequisite for the reachability fix.
5. **The unary predicate has a defensible reading of FR5.** FR5 says incompatible options stay
   disabled; one could argue that with the dataset unpinned, the model's *own* axis is the only
   honest predicate, and the reason cell (which the unary fix keeps) still carries D2's text.
   That is a real argument. But it is an *amendment argument*, and it should go through an
   amendment, not a bugfix.

6. **The fix matches the product's stated trajectory.** §6 describes a model-centric
   benchmarking future (10–20+ families, several-to-many variants each), `:166` says
   model-primary *"fits the model-centric benchmarking trajectory"*, and §11's alternative B
   ("ordered lead-axis, model-first") is recorded as *"a legitimate model-primary workflow;
   folded into D5's swappable policy"*. A user who picks a model and lets the dataset follow is
   doing the thing the design expects. The unary predicate is the shortest path to that
   workflow, and my brief's "the user must first express intent by clearing" is, on that
   reading, ceremony. This is the best argument against me and I do not have a rebuttal to its
   UX half — only to its correctness half (R1) and its process half (§3, §4).

**Where that leaves me.** Points 1, 2 and 6 are arguments for *adding to* the ✕, not for
*replacing* it — and note that D4 does not block the model-first workflow, it enables the only
version of it §5.6 actually specifies (`clear` dataset, then let the gate refill). Points 3
and 4 are scope, priced in §7 at two lines and one small surface control. Point 5 concedes the
unary reading is arguable — and the answer is that R1 makes it *unsound as written* regardless
of whether it is *permitted by FR5*. **Nothing in this section moves R1**, and R1 alone is
disqualifying.

---

## 9. Per-claim verdicts

### Claim 1 — "The dataset auto-snap at `:2702-2706` is dead code — it fires 0 times across all model changes a user can currently perform."

**CONFIRMED in substance — but it is a claim that cannot discriminate between the two fixes,
and the "dead code" framing is imprecise.**

Substance confirmed. With `:3050` binary and `clearable=False`, the only writer of
`model-selection-store` is `_select_model_from_table_handler` (`:2591`, `:2914`); the only
enabled Select buttons are those compatible with the current dataset; so after any model
change `current_value ∈ enabled` and `:2704` returns `no_update`. Executed:
`model=cascor cur=spirals -> NO_UPDATE(park)`, `model=cascor cur=mnist -> NO_UPDATE(park)`.
Nothing else writes the dropdown's `value` (`:2606` is the sole Output), and it has no
`persistence`, so a reload restores `(cascor, spirals)`.

Framing imprecise. The gate has a **second** Input,
`Input("params-init-interval", "n_intervals")` (`:2608`), where
`dcc.Interval(id="params-init-interval", interval=1000, max_intervals=1, n_intervals=0)`
(`:1871`) fires once on every page load, independently of any model change. On that tick
`enabled` is the **availability-gated** list, so the snap arms whenever
`DEFAULT_DATASET_TYPE ∉ enabled` — an axis with zero model changes. I checked whether it
can fire today and it cannot: `spiral` declares no `is_available()` hook
(`juniper-data/juniper_data/generators/_synthetic.py:13`; `api/routes/generators.py:184`
treats a hook-less generator as available), and `_fetch_generators()` fails **open**
(`availability_map({}).get(name, True)`). So the branch is dead by *coincidence of the current
seeds*, not by construction — one generator gaining an optional extra arms it.

**Why the claim cannot support the fix.** The snap is unreachable because of the binary gate
at `:3050` and `clearable=False` at `:1334` — the two things under review. **Both** candidate
fixes revive it: the unary predicate revives it by letting a model be chosen against an
incompatible dataset; the ✕ revives it by letting the dataset be `None` (executed:
`model=recurrence cur=None -> value=equities_seq`). "It is currently dead" is therefore true
of the status quo and equally true under either fix. It distinguishes nothing — and §12 argues
the ✕ revives it *more legitimately*, since it then fills a hole the user opened rather than
overwriting a choice the user made.

### Claim 2 — "The fix resurrects existing tested code rather than adding new code."

**REFUTED.**

The fix adds a new unary predicate at `:3050`, a new rendered notice, and a new button label
— three new pieces, two of which the fix's own description concedes. It *reuses* `:2706`,
which is one line. Meanwhile the alternative it is being compared against adds **zero** logic
and activates a branch (`:3018`, `:3033`) that is already written and already correct
(executed, §2). The claim inverts the comparison.

On "tested" (census in §10): the snap at `:2706` *is* covered
(`test_model_picker.py:91-97`) — but only on a singleton `enabled`; **R1's empty-`enabled`
branch has zero coverage and is not even injectable**, and the `enabled[0]` registry-order
choice is untested. Meanwhile the ✕ behaviour is pinned by a **passing** regression test whose
comment says *"No dataset selected (e.g. cleared)"* (`test_model_table.py:170-173`). The claim's
own phrase fits the fix it was written to displace.

### Claim 3 — "FR9 is real: the model service fails closed on a shape mismatch, so relaxing the UI gate cannot train an invalid pair."

**OVERSTATED, and REFUTED as a safety argument for the recommended fix.** Traced
independently across juniper-recurrence, juniper-canopy and juniper-cascor.

The *outcome* half survives: an invalid pair does not train. Everything else in the sentence
is wrong, and the part that matters for this decision is wrong in the fix's disfavour.

**(a) The premise is false.** §5.9 of the design says *"the target model service validates the
input shape **it receives** and fails closed"*. Canopy never sends arrays. It sends a dataset
**reference**: `dashboard_manager.py:2679-2685` builds `{"dataset": {"generator": …}}`, and
`recurrence_service_adapter.py:236` says so outright — *"The dataset is referenced (not piped)
— the recurrence service fetches the arrays from juniper-data itself."* **Nothing validates a
shape at the boundary FR9 names.**

**(b) The cited lines are the wrong lines.** `juniper_recurrence_model/model.py:138-139` and
`:161-162` are genuine hard `raise ValueError` on `X.ndim != 3` (no reshape/squeeze/broadcast
— verified by execution). But `:162` is **unreachable from every juniper-recurrence dataset
ingress**: `TrainRequest` (`juniper_recurrence/schemas.py:106-128`) has no inline `X`, so all
three ingress points pass `sequence.X`, already guaranteed 3-D by the **loader**,
`juniper_recurrence_model/data.py:69-70`. That loader line — not `model.py:162` — is the gate
that fires. And had `:162` fired, `routers/training.py:91` wraps `lifecycle.run` in **no
try/except** and the app registers no `ValueError` handler, so it would be an uncaught **500**,
not a 422. (The 422-on-shape behaviour cited actually lives on `/v1/predict`,
`routers/predict.py:66-71` — a different route.)

One layer deeper, `units/lmu_varstep.py:204-208` **silently expands 2-D → 3-D**
(`if u.ndim == 2: u = u[:, :, None]`), pinned as intended by `test_lmu_model.py:285-289`. It is
guarded today, but the permissive layer is one deleted guard away.

**(c) For the exact pair the unary fix parks on, the failure is a name typo, not a shape
check.** This independently confirms my R7. The parked body is `{"generator": "spirals"}`;
juniper-data's key is `"spiral"`, so it 400s with `"Unknown generator 'spirals'"`
(`juniper-data/juniper_data/api/routes/datasets.py:99-103`) → 422. The shape gate is never
reached. Worse: `src/tests/regression/test_oneshot_start_body.py:77-81` **asserts** the
un-aliased `"spirals"`, so the defect is pinned by a test.

**(d) THE DECIDING POINT — the fail-closed is invisible, and it is invisible on exactly the
path the unary fix creates.** `RecurrenceBackend.start_training` returns `ok=True`
**immediately** (`recurrence_backend.py:156`); the 422 lands asynchronously on a daemon thread
(`:158-173`). So canopy's `POST /api/train/start` returns **200 "Training started
successfully"**. The reason is stashed in `completion_reason` (`:220-221`), but
`dashboard_manager.py:6308-6324` maps only five *cascor* reasons and returns `None` for
anything else, so **no suffix renders**, and `_build_oneshot_result` reads `metrics_data`,
which is `{}` on failure.

> Under the recommended fix, a user in a no-equities deployment selects recurrence, is parked
> on `(recurrence, spirals)` with every dropdown option disabled, presses an enabled Start,
> and is told **"Training started successfully"**. Nothing then happens, and nothing says why.
> That is the vacuous-pass class.

Compare the ✕ path on the identical deployment: `oneshot_start_body` is `None`, so `:7100` is
skipped, the bare start hits `recurrence_backend.py:138-140`
(`ok=False, error="no dataset reference (need one of dataset_id / name / generator)"`) → **409**
(pinned, `src/tests/regression/test_recurrence_routes.py:164-171`) → `raise_for_status()` raises
at `:7103` → `success=False` + `detail` → the training-control-outcome-alert renders a
**visible, synchronous danger alert**. FR9's own stated goal — the operator cannot train an
invalid pair — is met *and communicated* only on the ✕ path.

**(e) The cascor half is not covered by the claim at all**, and has a hole.
`api/models/training.py:235` (`Literal` omitting `equities_seq` → 422→502),
`api/lifecycle/manager.py:3607-3608` (`RuntimeError` before any state assignment → 409) and
`cascade_correlation.py:1696-1697` do fail closed on the network paths. But
`juniper-cascor/src/api/app.py:522-543` (`_auto_start_training`) **bypasses
`_artifact_to_tensors` entirely — no ndim check**, mis-reads `x_train.shape[1]` (the lookback)
as `input_size` at `:536`, and dies later in a worker thread swallowed by `logger.exception`
at `:546-547`. Env-var reachable (`settings.py:546` types `auto_dataset` as bare `str`).

**(f) NO ARTIFACT for an end-to-end test.** Nothing anywhere drives an incompatible
(model, dataset) pair through the real stack. The four near-misses are all unit-level or
monkeypatched: `test_routes.py:118-122` (predict, not train), `test_routes.py:220-225`
(monkeypatches `validate_npz_contract` to raise — no real 2-D artifact),
`test_sequence_data.py:103-106` (loader unit test), and
`juniper-cascor/src/tests/unit/api/test_lifecycle_manager_swap.py:263-271`, which feeds a
**1-D** array while asserting a message about 3-D — the `(W, L, F)` case is never exercised.
`conftest.py:690`'s `wrong_shape_3d` fixture has zero consumers.

**(g) The gate being relaxed is the only canopy-side gate that exists.** `compatible` /
`dataset_reason` / `model_reason` / `gated_dataset_options` are consumed **exclusively** in
`frontend/dashboard_manager.py`. `main.py` imports only `get_model_spec` and
`RECURRENCE_PROVIDER`; `/api/train/start`, `/api/stage_dataset` and `/api/model/select` perform
**zero** compatibility checks (`StageDatasetRequest`'s own docstring, `main.py:3966-3968`: *"we
forward blindly"*). And canopy's own contribution to FR9 is nil — Start is never disabled on
dataset grounds (R6, executed).

**Net:** FR9 is a comment (`model_registry.py:288-296`, `:238-239`) and a design paragraph. The
backstop it names is real in effect but lives in three different places than claimed, rests on
a data-loader rather than a model, has an ungated auto-start ingress on the cascor side, is
partly carried by an unaliased-generator-name bug on the recurrence side, has never been
tested end-to-end, and — decisively — **does not reach the operator**. It cannot be leaned on
to license a UI relaxation.

### Claim 4 — "Un-gating the model Select changes only 3 test assertions."

**CONFIRMED on the count — and it is an argument against the fix, not for it.**

Exactly three assertions in three functions, all in `src/tests/regression/test_model_table.py`
(`:135`, `:144`, `:201`), enumerated in §10(a). Nothing else in the tree touches the model
table (`grep -rln "_build_model_selection_table\|model-select-btn" src/tests/` returns that one
file). No E2E, `ui/`, `ui_contract/`, contract, snapshot or performance test is affected.

Three reasons the number does not support the fix:

1. **Those three assertions ARE D2/FR5.** `:135` and `:144` are the bidirectional-greying tests;
   `:201` is the §5.3 "table reflects the current dataset on open" test. The fix's entire test
   delta is *removing the enforcement of a ratified decision*. A small delta here measures how
   thinly D2 is pinned, not how safe the change is.
2. **The count is only 3 because the change is narrowly scoped — and that narrowness is itself
   a defect** (§10(c)): leaving `is_compatible` binary makes each row self-contradictory
   ("needs 3-D data" beside an enabled Select), and the §5.8 alert renders above an all-enabled
   table. Making `is_compatible` unary instead breaks `:256-258` and deletes the §5.8 state.
   Either way the true delta is larger than 3.
3. **Zero of the three cover the behaviour the fix creates.** R1's park-on-invalid-pair state
   has no test, in this file or anywhere (§10(d)), and cannot easily get one —
   `_gate_dataset_options_handler` has no `generators=` injection point.

For comparison, the ✕ changes **zero** assertions and leaves `test_model_table.py:170-173`
— which already asserts the exact post-fix state — green.

---

## 10. The two independent traces

**Trace 1 — FR9 fail-closed, across juniper-recurrence / juniper-canopy / juniper-cascor.**
Folded into Claim 3 (§9) in full, including the two findings that decide it: FR9's premise is
false because canopy sends a dataset *reference* rather than arrays, and the fail-closed never
reaches the operator (`recurrence_backend.py:156` returns `ok=True` synchronously;
`dashboard_manager.py:6308-6324` renders no reason). Collateral defects B1-h and B1-i (§11).

**Trace 2 — test blast radius (claim 4 + the "tested" half of claim 2).**

Only one test file touches the model table at all:
`grep -rln "_build_model_selection_table\|model-select-btn" src/tests/` → **`src/tests/regression/test_model_table.py`**, and nothing else in `contract/`, `integration/`,
`performance/`, `snapshots/`, `ui/`, `ui_contract/`, `unit/`.

**(a) The blast radius of a unary `:3050` — exactly 3 assertions in 3 functions.**

| file:line | assertion | fate |
|---|---|---|
| `test_model_table.py:135` | `assert _button_for(table, "recurrence").disabled is True` | **FAILS** |
| `test_model_table.py:144` | `assert _button_for(table, "cascor").disabled is True` | **FAILS** |
| `test_model_table.py:201` | `assert _button_for(children, "cascor").disabled is True` (via `_toggle_model_modal_handler`) | **FAILS** |

Confirmed two ways by an independent census: a real pytest run against a patched
`_build_model_selection_table` (`3 failed, 22 passed`) and a probe evaluating all 30 assertions
in the file individually, so pytest's stop-at-first-failure could not hide later ones. Both
agree with the grep-level reference graph.

Everything else survives: `:158` (non-live-but-compatible stays `False`), `:163-164` (labels),
`:173`/`:179` (already assert all-`False`), `:256-258` (the §5.8 alert keys off
`compatible_count`, not `disabled`), `test_model_table.py:366-376` (search), and
`test_dashboard_manager_gate_coverage_inner1.py:147-162` (asserts only `is_open` / `table is
not None`). No E2E or `ui/` test reaches the model modal.

**(b) The three that break are precisely the three that encode D2/FR5.** `:135` and `:144` are
the bidirectional-greying tests; `:201` is the "table reflects the current dataset on open"
test (§5.3). So "only 3 assertions" is not reassurance — it is a measurement of how thinly the
ratified decision is pinned, and the patch's whole test delta is *deleting the enforcement of
D2*.

**(c) A narrowly-scoped unary change makes the row self-contradictory.** If only the
`disabled=` kwarg at `:3050` changes, `is_compatible` / `compatible_count` at `:3033-3035` are
untouched — so a row renders **"needs 3-D data"** in the Compatibility column beside an
**enabled "Select"**, and in the degenerate case the §5.8 alert *"No compatible model. No model
can train the selected dataset yet"* (`:3070-3079`) renders **above a table where every Select
is enabled**. The surviving assertions prove it: `:137` (`"needs 3-D data" in _all_text`),
`:145` (`"needs 2-D data"`) and `:255-258` (the §5.8 alert) all still **pass** under the patch —
the test suite would go green on a visibly contradictory UI.

If instead `is_compatible` itself is made unary, the census measured the real cost:
**8 failing assertions in 4 functions** — the three above plus `:137`, `:145`, `:255`, `:256`,
`:257` — and the §5.8 degenerate state disappears entirely (the alert stops rendering, both
compat cells start reading "✓ compatible"). Either way the fix owes more than the three
assertions, and the cheap version buys its low count by shipping an incoherent row.

**(d) The snap IS tested — twice — but not on the branch that matters.** Eight tests exercise
`_gate_dataset_options_handler`; two reach the snap at `:2706`:

| file:line | args | branch |
|---|---|---|
| `test_model_picker.py:92-96` | `("recurrence", "spirals")` | **SNAP** → `assert value == "equities_seq"` |
| `test_n7_dataset_panel.py:147-149` | `("cascor", "mnist")`, `_fetch_generators` stubbed with mnist `available: False` | **SNAP** → `assert value in enabled and value != "mnist"` |
| `test_model_picker.py:100-101`, `test_n7_dataset_panel.py:136-142`, `:160`, `inner1.py:176-177` | compatible current value | no-op `:2705` |
| `test_model_picker.py:105`, `test_n7_dataset_panel.py:155` | `("", …)` | early-out `:2701` |

So claim 2's "tested" is literally true of `:2706`. Three gaps, all load-bearing:

- **The empty-`enabled` park branch — R1's exact case — is NOT covered by any test.** Every
  test hits `current_value in enabled`, `not model_key`, or the snap. **Nobody hits
  `not enabled`.**
- **The `enabled[0]` registry-order choice is still not pinned.** The `recurrence` snap has
  `enabled` as a singleton, so it is trivially determined. The `cascor` snap does have a
  5-element `enabled` — but its assertion is deliberately weak
  (`value in enabled and value != "mnist"`) and pins no particular element. The
  `(cascor, equities_seq) → spirals` case (R5) is untested, and *no* test would fail if
  `enabled[0]` became `enabled[-1]`.
- **The availability composition is not injectable at the handler.**
  `_gate_dataset_options_handler` calls `self._fetch_generators()` internally with no
  `generators=` parameter — unlike `_render_dataset_params_handler(dataset_value,
  generators=None)`. The one test that varies availability
  (`test_n7_dataset_panel.py:147`) has to **stub the method**. That friction is *why* R1's case
  has no coverage.

Note the shape of this: the covering tests exercise the snap in its two benign forms and stop
exactly short of the malignant one. That is the vacuous-pass pattern — the branch reads
"covered" in any coverage report while its dangerous arm is untouched.

**(e) THE HEADLINE — the ✕ behaviour is already pinned by a passing regression test.**

```python
# src/tests/regression/test_model_table.py:170-173
def test_table_without_a_dataset_treats_all_models_as_compatible():
    # No dataset selected (e.g. cleared) -> no model is greyed (compatibility is best-effort).
    table = DashboardManager._build_model_selection_table(None, "cascor")
    assert all(button.disabled is False for button in _select_buttons(table))
```

Read the comment: **"(e.g. cleared)"**. Someone wrote a regression test for the D4 ✕ state, it
passes today, and the state it describes is unreachable in the product because of one token at
`:1334`. Claim 2's phrase — *"resurrects existing tested code rather than adding new code"* —
describes the ✕ fix exactly, and the unary fix not at all.

**(f) Null-dataset coverage, per handler.**

| Handler | Verdict | Evidence |
|---|---|---|
| `_build_model_selection_table` | **COVERED-WITH-NONE** | `test_model_table.py:170-173` (and `:176-179` for an unknown value) |
| `_open_live_switch_modal_handler` | **COVERED-WITH-NONE** | `test_live_dataset_switch_handlers.py:180` passes `dataset_type=None` |
| `_open_restart_confirm_modal_handler` | **COVERED-WITH-NONE** | `test_restart_orchestration_handlers.py:144-146` — `n_clicks=1` with `dataset_type` defaulting to `None` |
| `_resolve_oneshot_start_body_handler` | **COVERED-WITH-NONE** | `test_oneshot_start_body.py:74-75` — `("one_shot", None) is None` and `("one_shot", "") is None` |
| `_dataset_model_hint_handler` | COVERED (equivalent path) | `test_model_table.py:276-277` cover `""` and `"does-not-exist"`; both reach the same `get_dataset_spec → None → or ""` path. Literal `None` never passed |
| `_toggle_model_modal_handler` | NOT-COVERED-WITH-NONE | `:197`, `:205`, `:366-374`, `inner1.py:151,160` all pass a real dataset — though its only body is `_build_model_selection_table`, which **is** covered |
| `_gate_dataset_options_handler` | NOT-COVERED-WITH-NONE | `test_model_picker.py:91-105`, `test_n7_dataset_panel.py:136-162` |
| `_render_dataset_params_handler` | NOT-COVERED-WITH-NONE | `test_n7_dataset_panel.py:93-123` only `"spirals"`/`"mnist"`/`"moons"`; verified safe by execution instead (§7) |
| `_accept_live_switch_handler` | NOT-COVERED-WITH-NONE | `test_live_dataset_switch_handlers.py:226-304` all pass `"moons"`; guard exists at `:6053` |
| `_apply_dataset_handler` | NOT-COVERED-WITH-NONE | `test_n7_dataset_panel.py:181-230`, `inner2.py:58-86` — **and it is the one that is unsafe**, D-W1 |
| `clearable` asserted anywhere | **NO ARTIFACT** | `grep -rn "clearable" src/tests/ --include=*.py` → empty |

**Four of the ten consumers are already covered with `None`, including the two that matter most**
(the model table and the one-shot start body). Shipping D4 should add tests for the five
remaining NOT-COVERED rows — that is the honest cost of my brief, and it is test work, not
design work. Shipping the unary fix should add a test for R1's park branch, which does not
exist for either fix today.

*(This table corrects a first pass of mine that marked `_open_live_switch_modal_handler`,
`_open_restart_confirm_modal_handler` and `_resolve_oneshot_start_body_handler` as
NOT-COVERED; an independent census found the three tests. Recorded because the correction runs
in my brief's favour and should be visible as such.)*

**(g) Q4 — does any test reach `(recurrence, equities_seq)` through the UI?** **NO ARTIFACT**,
and the reason is itself a finding.

The 11 Playwright modules in `src/tests/ui/` contain **zero** occurrences of `recurrence`,
`equities`, `model-select`, `nn-model-change` or `model-selection`. There is no snapshot test
either — the layout seeds an empty `html.Div(id="model-selection-table-container")`
(`dashboard_manager.py:2216`) and `src/tests/regression/snapshots/` holds only
`dataset_plotter.txt` and `metrics_panel.txt`. Every model-selection test is a direct handler
call.

**But the scenario was written.** `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md:944`
specifies **W8 — Model switch cascor ⇄ recurrence**, whose step 5 (`:956`) clicks
`{"type":"model-select-btn","index":"recurrence"}` — the exact click that is impossible. It was
never run: `:947-950` gates the row — *"Without the leg, every W8 step is `N-A (no recurrence
service)`"* — and `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:1756` records
*"W7 / W8 and every recurrence-dependent row are"* blocked.

So the defect was masked by a **blocked test row, not a missing one** — the classic
"a broken thing masks the next one" shape. The recurrence-service gap deferred W8; W8's
deferral is why nobody clicked the button; and the button has been permanently disabled ever
since. **Neither fix will be caught by any existing test — the fix that ships must come with
W8 unblocked, or the same class recurs.**

---

## 11. Bottom line

**Ship D4 (`clearable=True` on `nn-dataset-type-dropdown` + the "clear model / show all"
reset on the model surface), plus the two-line D-W1 guard on `_apply_dataset_handler:2845`.
Do not ship the unary `:3050` predicate.**

Reasons, in order:

1. **R1 is disqualifying.** The unary fix parks the UI on an invalid pair with an
   unrecoverable dropdown and an enabled Start button, in the exact deployment shape the fix
   exists to enable. It fails open. The ✕ fails closed.
2. The ✕ **implements** three ratified items (D4/FR6/§5.5); the unary predicate **amends**
   three others (D2/FR5/§5.2) and settles a deferred open question (OQ-6) inside a bugfix.
3. `clearable=False` **predates the design**. This is unfinished A1 work, not a design fork.
4. The ✕ costs **zero new logic**; the mechanism is already implemented and executes
   correctly today (§2, executed).
5. The snap **substitutes** where §5.6 says **clear**, discards the user's dataset and staged
   params, and is documented under the wrong policy name at `:2695`.

If the extra click in §8.1 is judged unacceptable, the correct increment is the recommended
fix's *label* ("Select — switches dataset to X") applied to the **✕-enabled** surface, plus
the §5.6 "+ notice" — i.e. take the fix's UX ideas and drop its predicate change. That
composite ships D4, honours D2, leaves OQ-6 open for its spike, and avoids R1 entirely.

### The concrete diff I am recommending

```python
# src/frontend/dashboard_manager.py:1334  — implements D4 / FR6 / §5.5
-                clearable=False,
+                clearable=True,   # D4/§5.5 inline ✕ — clearing re-activates the model
+                                  # table via :3018/:3033 (already implemented)
```

```python
# src/frontend/dashboard_manager.py:2845  — closes D-W1, mirroring the existing :5623 idiom
-        payload: dict = {"nn_dataset_type": dataset_type}
+        if not dataset_type:
+            return dash.no_update, dbc.Alert("Select a dataset type before applying.", color="warning", duration=6000, dismissable=True)
+        payload: dict = {"nn_dataset_type": dataset_type}
```

Optional polish, not required for correctness: `:2864`'s "No adjustable parameters…" →
"No dataset selected" when `dataset_value` is falsy (D-W2); a "show all" reset button on the
model surface (§8.4). **Explicitly NOT recommended:** touching `:3050`.

Anything that lands must also carry a regression test for the state R1 describes — select a
model in a deployment where `enabled == []`, and assert the UI does not hold an incompatible
pair with an enabled Start. No such test exists today for either fix (§10(d)), and writing one
requires first giving `_gate_dataset_options_handler` a `generators=` injection point (it calls
`self._fetch_generators()` internally, unlike `_render_dataset_params_handler`). That
injectability gap is the reason R1 went unnoticed and should be closed regardless of which fix
ships.

Shipping D4 should also add the five NOT-COVERED-WITH-NONE handler tests from §10(f), and
unblock E2E row **W8** (`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md:944`),
which already specifies this exact click and has been `N-A` since the recurrence-service gap
(§10(g)). That is the honest cost of my brief: **five test functions, one unblocked E2E row,
and two lines of product code** — against the recommended fix's three deleted assertions
(or eight, §10(c)), one new predicate, one new notice, one new label, and R1.

**Separable defects surfaced, worth their own rows regardless of which fix ships:**

| id | Site | Defect |
|---|---|---|
| B1-a | `:2704-2705` | The park branch can hold an invalid `(model, dataset)` pair whenever availability empties `enabled`. Reachable today by *any* fix that lets a model be selected against an incompatible dataset. |
| B1-b | `:2695` | Comment names the policy "dataset-primary"; the code keeps the model. Inverted. |
| B1-c | `:2681` | One-shot start body bypasses `GENERATOR_NAME_ALIASES`; would emit `"spirals"` for juniper-data's `"spiral"`. Masked only by `equities_seq` being identity. |
| B1-d | `:7187-7207` | Start is gated on model `status` only, never on dataset compatibility. |
| B1-e | `:2845` | `nn_dataset_type: None` is POSTed unguarded; `exclude_none=True` at `main.py:3993` turns it into a vacuous 200 + a false pending-change banner. |
| B1-f | `:2668-2685` | One-shot start ignores the user's `nn-gen-param` inputs entirely; only registry `default_params` are forwarded. |
| B1-g | `:5422` | `restart-ds-type` is seeded `gated_dataset_options(DEFAULT_MODEL_KEY)` and **nothing ever writes its `options`** (only `:5268` writes `value`). The restart modal is permanently gated to **cascor**. Latent today; **either** fix un-masks it — on recurrence it would show `equities_seq` greyed "needs a 2-D model" and the five 2-D types selectable, exactly inverted. Shared prerequisite, not a discriminator. (Practical reachability is limited: the modal opens from the cascor pending-dataset banner.) |
| B1-h | recurrence | `RecurrenceBackend.start_training` returns `ok=True` synchronously (`recurrence_backend.py:156`) while the real 422 lands async on a daemon thread (`:158-173`), and `dashboard_manager.py:6308-6324` maps only cascor reasons → **no failure ever renders**. Canopy says "Training started successfully" for a run that never started. |
| B1-i | cascor | `api/app.py:522-543` `_auto_start_training` bypasses `_artifact_to_tensors` — **no ndim check** — mis-reads `x_train.shape[1]` (lookback) as `input_size` at `:536`, and the eventual failure is swallowed by `logger.exception` at `:546-547`. Env-var reachable (`settings.py:546`). |

---

## 12. The reachability walk under D4, verified end to end

For completeness, the exact sequence the ✕ enables, each step confirmed against code or
execution:

| # | Action | Mechanism | Verified |
|---|---|---|---|
| 1 | Click ✕ on the dataset dropdown | `clearable=True` → `value = None` (Dash 4.2.0 docstring) | executed (prop accepted) |
| 2 | Sidebar settles | `render_dataset_params(None)` → `('Current Dataset', hidden, ['No adjustable parameters…'])`; `annotate_model_hint(None)` → `""` | executed |
| 3 | Click "▸ change" | `_toggle_model_modal_handler(..., None, ...)` → `_build_model_selection_table(None, 'cascor')` | executed — **both** Select buttons `disabled=False` |
| 4 | Click Select on `recurrence` | `_select_model_from_table_handler` → `POST /api/model/select` → store=`recurrence`, class=`one_shot` | `:2914`, `:2876-2897` |
| 5 | Gate fires | `_gate_dataset_options_handler('recurrence', None)` → `enabled=['equities_seq']` → **snap to `equities_seq`** | executed |
| 6 | One-shot body resolves | `{"dataset": {"generator": "equities_seq", "params": {"max_symbols": 5, "regression_target": "return"}}}` | `:2679-2685` + registry `:148` |

Two things worth naming about step 5. First, `enabled` is a **singleton**, so the snap makes no
arbitrary registry-order choice on the outbound leg — my R5 bites on the *return* leg
(`→ spirals`, not `mnist`) and as the model population grows, not here.

Second — and this is the reframe that matters — **the ✕ is what legitimately "resurrects" the
snap at `:2706`.** Under D4 the snap runs from a state the user *deliberately emptied*: it
**fills a hole the user opened**, which is what §5.6's "keep model, clear dataset" contemplates.
Under the unary fix the same line runs from a state the user *chose*: it **overwrites a
selection**, which §5.6 never authorises. Same line of code; opposite relationship to user
intent. Claim 2's "resurrects existing tested code" is therefore not merely inverted on volume
(§9) — it is inverted on *legitimacy* too.
