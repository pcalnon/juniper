# P3 — Minimal-Diff Pragmatic Engineering: unlocking (recurrence, equities_seq)

**Author lens**: smallest correct change, shipped this week, smallest blast radius.
**Repo**: `/home/pcalnon/Development/python/Juniper/juniper-canopy` (read-only for this pass; no file was edited).
**Design of record**: `/home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` (cited below as *the design doc*).
**Env used**: `JuniperCanopy1` (dash 4.2.0 / dbc 2.0.4). Baseline: `src/tests/regression/test_model_table.py` 25 passed; `test_model_picker.py` + `test_model_registry.py` + `test_n7_dataset_panel.py` + `test_dashboard_manager_gate_coverage_inner1.py` 136 passed.

---

## 1. Verification of the hypothesis — **CONFIRMED** (with two anchor corrections)

The deadlock is real and I reproduced it by direct handler invocation (probe:
`scratchpad/probe_p3_clear_flow.py`, run under `JuniperCanopy1`).

| Claim | Verdict | Evidence |
|---|---|---|
| Defaults are (cascor, spirals) | CONFIRMED | `src/model_registry.py:153` `DEFAULT_DATASET_TYPE = DATASET_TYPES[0].value` → `"spirals"`; `src/model_registry.py:197` `DEFAULT_MODEL_KEY = MODELS[0].key` → `"cascor"`; seeded into the layout at `src/frontend/dashboard_manager.py:1333` (dropdown `value=`) and `:1842` (`model-selection-store`). |
| Dataset dropdown disables every dataset incompatible with the current model | CONFIRMED | `src/model_registry.py:408-424` `gated_dataset_options()` emits `{"disabled": True}` + reason suffix. Probe: `gate(cascor, spirals)` → `equities_seq` disabled, label `"Equities (sequence) — needs a 3-D model"`. |
| Model modal disables the Select button of every model incompatible with the current dataset | CONFIRMED | `src/frontend/dashboard_manager.py:3050` `disabled=not is_compatible`. Probe: table(spirals, cascor) → `{'cascor': False, 'recurrence': True}`. |
| Neither control can be cleared | CONFIRMED | `src/frontend/dashboard_manager.py:1334` `clearable=False`; there is no "clear model" control at all — `model-selection-store` is written only by `_select_model_from_table_handler` (`:2591-2599`), which requires a click on an enabled Select button. |
| **Net: (recurrence, equities_seq) is unreachable from the default state** | CONFIRMED | Every path to it requires one of the two gates to yield first, and neither does. |

**Anchor corrections (two, both minor):**

1. `:2687` is the **docstring line**, not the code. `_gate_dataset_options_handler` is defined at
   `src/frontend/dashboard_manager.py:2686`; the auto-snap is `:2702-2706`
   (`enabled = [...]; if current_value in enabled or not enabled: return options, dash.no_update; return options, enabled[0]`).
2. `:3033` is `reason = model_reason(model, dataset) if dataset is not None else None`; the
   *`dataset is None` decision* is one line earlier at `:3018`
   (`dataset = get_dataset_spec(dataset_value) if dataset_value else None`). Both matter for §2.

Everything else in the anchor list verified as stated, including `:5422`
(`restart-ds-type`, statically gated to `DEFAULT_MODEL_KEY`, `options` never re-emitted — the only
Outputs on that id are `.value` at `:5268`). See §6.

**One important nuance the hypothesis under-states**: the dataset gate reads the dropdown value as a
**`State`**, not an `Input` (`src/frontend/dashboard_manager.py:2609`). That single fact is what makes
the cheapest fixes work — see §2.

---

## 2. Does the codebase already contain the fix? — **YES. Two mechanisms, both real, one with a trap.**

This is the highest-value finding in this document, so I traced both by executing the handlers rather
than reading them.

### 2(a) Ship the D4 inline ✕ (`clearable=True` at `:1334`) — **IT ACTUALLY WORKS.**

The specific trap you flagged — "does clearing the dataset really re-enable the model Select buttons,
given `dataset is None`?" — resolves in our favour, and there is already a test pinning it.

Step-by-step, click by click (probe output verbatim in the appendix):

| # | User action | What fires | Result |
|---|---|---|---|
| 0 | at rest | — | dropdown: `equities_seq` disabled. table: `recurrence` Select disabled. **Deadlocked.** |
| 1 | click the dropdown's ✕ | `nn-dataset-type-dropdown.value → None`. **`gate_dataset_options` does NOT re-fire** — the dataset is a `State` there (`:2609`), and its two `Input`s (`model-selection-store`, `params-init-interval` with `max_intervals=1` at `:1871`) did not change. So **nothing snaps the dataset back.** Three callbacks do fire: `render_dataset_params` (`:2624`), `resolve_oneshot_start_body` (`:2637`), `annotate_model_hint` (`:2649`) — none raise. | dataset = `None`, held. |
| 2 | click "▸ change" | `toggle_model_modal` (`:2571-2581`) reads the dataset as `State` → `None` → `_build_model_selection_table(None, "cascor")`. At `:3018` `dataset_value` is falsy → `dataset = None`; at `:3033` `reason = None` for every row; `is_compatible = True`; `:3050` `disabled=False`. | **Every Select button enabled, `recurrence` included.** |
| 3 | click Select on Recurrence | `_select_model_from_table_handler` → `POST /api/model/select` (`src/main.py:3731-3746`, which validates the key against the registry only — **no dataset-compat check**) → `model-selection-store = "recurrence"`, `model-class-store = "one_shot"`, modal closes. | model swapped. |
| 4 | *(automatic)* | The store write is an `Input` of `gate_dataset_options` → `_gate_dataset_options_handler("recurrence", None)`. `enabled == ["equities_seq"]`; `None not in enabled` and `enabled` is non-empty → **`return options, enabled[0]`**. | **Dataset auto-snaps to `equities_seq`.** |

Probe result: `reached pair = (recurrence, equities_seq)`, and
`_resolve_oneshot_start_body_handler("one_shot", "equities_seq")` →
`{'dataset': {'generator': 'equities_seq', 'params': {'max_symbols': 5, 'regression_target': 'return'}}}`
— i.e. the pair is not just *reachable*, it is *trainable*: the one-shot Start body is correct.

Three clicks. Zero new code paths. The existing auto-snap at `:2702-2706` does the last step for you.
The `dataset is None` behaviour is already pinned by
`src/tests/regression/test_model_table.py:170-173`
(`test_table_without_a_dataset_treats_all_models_as_compatible`) — the mechanism was built, tested,
and then locked behind `clearable=False`.

**But it is not sound *as a bare one-liner*.** While the dataset is `None`:

- `apply-dataset-button` stays enabled. `_apply_dataset_handler` (`:2828`) builds
  `{"nn_dataset_type": None}`; `src/main.py:3994` does `body.model_dump(exclude_none=True)`, which
  **drops the key entirely**, and the handler's own docstring says *"`dataset_type` is ALWAYS sent —
  cascor's `_reload_dataset` hard-requires it."* Outcome is a backend rejection or a silent no-op.
- The spiral typed-field block is hidden (`_render_dataset_params_handler(None)` →
  `style={'display': 'none'}`, title falls back to `"Current Dataset"`). Cosmetic, self-healing.
- If the user clears within the first second, the `params-init-interval` mount pass re-fires the gate
  and snaps back to `spirals`. Benign race; the user simply clicks ✕ again.

So the honest cost of 2(a) is **1 line + a ~4-line guard in `_apply_dataset_handler`**.

### 2(b) Generalise the auto-snap at `:2702-2706` to the model side — **NO. It cannot fire.**

This is the fix that looks right and is not.

The dataset auto-snap is triggered by a **model change**. To mirror it, a *dataset* change would have
to snap the *model*. But:

1. The user **cannot produce a conflicting dataset change**: `gated_dataset_options` marks every
   incompatible dataset `disabled`, so `equities_seq` is unclickable while cascor is active. The
   would-be trigger never occurs. A model-side snap added today is dead code.
2. Even if you ungated the dropdown, `gate_dataset_options` reads the dataset as **`State`**
   (`:2609`) — a dataset change does not re-enter that callback at all. You would need a *new*
   callback with `Input("nn-dataset-type-dropdown","value")` writing
   `Output("model-selection-store","data", allow_duplicate=True)` **plus** `model-class-store`
   (already an `allow_duplicate` co-owner at `:2592`) **plus** `nn-model-summary` — and it must
   `POST /api/model/select` to actually swap the process-global backend
   (`src/main.py:3688-3714`), which can 409 mid-training.

That is a new network-writing callback, a third writer on two stores, and an ungating of the primary
D5 correctness gate — materially larger than any proposal below, for the same end state. **Rejected.**

### Is there a fix so small it is one line? — **Yes, two of them. Neither is fully sound alone. Say so out loud.**

- **One-liner Z**: `:1334` `clearable=False` → `clearable=True`. Reaches the pair in 3 clicks
  (§2a). Residual: Apply Dataset becomes a typeless stage POST. **Visible** failure (an alert), not a
  silent one — but still a new failure mode.
- **One-liner Y**: `:3050` `disabled=not is_compatible` → `disabled=False`. Reaches the pair in
  2 clicks via the already-tested snap. Residual: a model with **zero** compatible datasets in the
  registry becomes selectable, and `_gate_dataset_options_handler` then hits its
  `not enabled → return options, dash.no_update` branch (`:2704-2705`) — leaving the UI parked on a
  silently invalid pair with every dataset option greyed and no snap. **This is the "plausible
  one-liner that quietly leaves a broken state" case.** Today it is unreachable (both seeded models
  have a compatible dataset), which is exactly why it would ship green and detonate on the third
  model.

The cheapest **sound** fix is one-liner Y with its predicate tightened by one call — Proposal 1.

---

## 3. Proposals (ordered by increasing blast radius)

Blast radius here = *how many existing behaviours change for a user who does nothing new*, then lines.

---

### Proposal 1 — **Un-gate Select; let the existing snap resolve the conflict** (model-primary)

**Mechanism (one line):** stop disabling a Select button because the *current* dataset is
incompatible; disable it only when the model has **no compatible dataset in the registry at all**.
Clicking Select then swaps the model, and the already-shipped, already-tested dataset auto-snap
(`:2702-2706`) moves the dataset to the model's first compatible type.

**How it works**

- `src/frontend/dashboard_manager.py:51` — add `compatible_datasets` to the existing
  `from model_registry import ...` line.
- `src/frontend/dashboard_manager.py:3050` —
  `disabled=not is_compatible` → `disabled=not compatible_datasets(model)`.
- `src/frontend/dashboard_manager.py:3040-3043` — the compatibility cell keeps `reason`, and gains
  the consequence in the **same visible text** (D2's locus, not a tooltip):
  `"needs 3-D data · selecting switches dataset → Equities (sequence)"`, where the label comes from
  `compatible_datasets(model)[0].label`. `title=` on the button (`:3051`) gets the same string.
- `:3068-3078` — reword the §5.8 recovery alert (keep the literal phrase `"No compatible model"`,
  which `src/tests/regression/test_model_table.py:257` asserts).

**Click flow to (recurrence, equities_seq)** — two clicks:

1. "▸ change" → `toggle_model_modal` builds the table against `"spirals"`. `recurrence` row reads
   *"needs 3-D data · selecting switches dataset → Equities (sequence)"*, Select **enabled**
   (`compatible_datasets(recurrence) == [equities_seq]`, non-empty).
2. Select → `POST /api/model/select` → `model-selection-store = "recurrence"` → that store write is
   an `Input` of `gate_dataset_options` → `_gate_dataset_options_handler("recurrence", "spirals")`
   → `spirals` now disabled, `enabled == ["equities_seq"]`, `"spirals" not in enabled` → snap.
   **This exact call is already asserted green** at
   `src/tests/regression/test_model_picker.py:91-96`.

**Diff estimate**

| Item | Count |
|---|---|
| Files touched (product) | 1 — `src/frontend/dashboard_manager.py` |
| Product lines | ~12 changed/added (1 functional, ~6 text/label, ~5 docstring) |
| Callbacks added / modified | **0 / 0** |
| New value domains introduced | **0** |
| Existing test assertions that MUST change | **exactly 2** |

Assertions to change:

- `src/tests/regression/test_model_table.py:135` — `assert _button_for(table, "recurrence").disabled is True` → `is False`
- `src/tests/regression/test_model_table.py:144` — `assert _button_for(table, "cascor").disabled is True` → `is False`

Verified **not** affected: `:137`, `:145` (reason text still rendered); `:158`
(`cs3d` has a compatible dataset → still enabled); `:173`, `:179` (all-enabled paths unchanged);
`:250-258` and `:261-265` (the §5.8 alert assertions check the `Div` wrapper, the alert id, the
phrase and the presence of a `Table` — never a button's `disabled`); `test_model_picker.py:91-105`;
`test_dashboard_manager_gate_coverage_inner1.py:144-197`.

**Strengths** — smallest functional diff of any working fix; two clicks; zero new callbacks;
zero new value domains; the resolution path it relies on is *already covered by a green test*; the
D5 conflict machinery finally becomes reachable from the UI instead of being tested-but-dead;
symmetric (from `equities_seq`, clicking CasCor snaps back to `spirals`).

**Weaknesses** — silently mutates the user's dataset on click; unilaterally resolves **OQ-6** as
*model-primary* inside a bugfix; drops the "disabled" half of **FR5/D2** on the model side (the
reason text stays, so D2's *reason-at-the-locus* survives).

**Risks** — (R1) a future model with no compatible dataset: handled by the `compatible_datasets`
predicate, which disables it. (R2) a user reads "Select" as non-destructive: mitigated by putting the
consequence in the rendered cell, not a tooltip (§8 of the design doc says per-option tooltips are
unreliable — so do not rely on `title=` alone). (R3) `POST /api/model/select` 409s mid-training
(`src/main.py:3710-3714`) — pre-existing, `_select_model_handler` already no-ops and leaves the modal
open (`test_model_picker.py:68-77`).

**Guardrails (concrete)**

- `src/tests/regression/test_model_table.py` — `test_table_disables_a_model_with_no_compatible_dataset_at_all`:
  inject `ModelSpec(key="r4", input_ndim=frozenset({4}), supported_task_types=frozenset({"regression"}))`
  and assert its Select is `disabled is True`. This is the soundness guard for one-liner Y's hole.
- `src/tests/regression/test_model_table.py` — `test_incompatible_row_names_the_dataset_it_will_switch_to`:
  assert `"Equities (sequence)"` appears in the recurrence row's text against `spirals`.
- **The test that would have caught the original defect and will catch its recurrence**
  (`src/tests/unit/test_model_registry.py`), parametrized over `MODELS × DATASET_TYPES` so a newly
  seeded model or dataset is covered with no test edit:

  ```
  @pytest.mark.parametrize("model", MODELS, ids=lambda m: m.key)
  @pytest.mark.parametrize("dataset", DATASET_TYPES, ids=lambda d: d.value)
  def test_every_compatible_pair_is_reachable_from_the_default_state(model, dataset, manager):
      if not compatible(dataset, model):
          pytest.skip("not a compatible pair")
      # 1. the model's Select is enabled in the table built against the DEFAULT dataset
      table = DashboardManager._build_model_selection_table(DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY)
      assert _button_for(table, model.key).disabled is False
      # 2. after selecting it, the dataset gate offers `dataset` as an ENABLED option
      options, _snapped = manager._gate_dataset_options_handler(model.key, DEFAULT_DATASET_TYPE)
      by_value = {o["value"]: o for o in options}
      assert by_value[dataset.value].get("disabled") in (None, False)
  ```

  Today this fails on `(recurrence, equities_seq)` at step 1 — it *is* the defect, expressed as an
  invariant. Note it must stub `_fetch_generators` (or accept the all-available fallback).

**What it does NOT fix** — the `:5422` restart-modal gate hole (§6); the absence of any "clear
dataset" affordance (D4 still unshipped); the absence of a post-snap **notice**, which D5's
model-primary wording explicitly calls for; the `:5422` availability-gate inconsistency.

**Design-of-record impact** — *Upholds* D5 (a conflict is resolved by a single swappable policy) and
D2 (reason at the locus). *Amends* FR5 on the model side: incompatible model rows stay visible with
their reason but are **no longer disabled**. *Resolves OQ-6* as **model-primary** — which the design
doc's §5.6 already flags as the one that *"fits the model-centric benchmarking trajectory."*
Leaves D4 unshipped.

---

### Proposal 2 — **Ship D4's inline ✕ as specified** (`clearable=True`)

**Mechanism (one line + one guard):** give the dataset dropdown the conventional inline clear the
design doc already specified in D4/§5.5; clearing widens the model table via the existing
`dataset is None` path, and the existing auto-snap re-narrows the dataset after the model is chosen.

**How it works**

- `src/frontend/dashboard_manager.py:1334` — `clearable=False` → `clearable=True`.
- `src/frontend/dashboard_manager.py:2828` `_apply_dataset_handler` — add, right after the
  `if not n_clicks` guard: `if not dataset_type: return dash.no_update, dbc.Alert("Select a dataset type before applying.", color="warning", duration=6000, dismissable=True)`.
  Without this, Apply POSTs a body whose type key is stripped by `src/main.py:3994`.
- `src/frontend/dashboard_manager.py` `_accept_live_switch_handler` — same 2-line guard (the
  live-switch path reads the same `State` at `:5210`; the button at `:1363` ships `disabled=True`
  and is re-gated inside `update_unified_status_bar` (`:3308`), so this is belt-and-braces).

**Click flow** — three clicks: ✕ → "▸ change" → Select(Recurrence); then the dataset **auto-snaps**
to `equities_seq` (traced in §2a; verified by probe).

**Diff estimate**

| Item | Count |
|---|---|
| Files touched (product) | 1 — `src/frontend/dashboard_manager.py` |
| Product lines | ~10 (1 functional + ~6 guard + docstrings) |
| Callbacks added / modified | 0 / 0 (two handler bodies gain an early return) |
| Existing test assertions that MUST change | **zero** |

Verified zero: no test asserts `clearable` on `nn-dataset-type-dropdown` (the only `clearable` hits
under `src/tests/` are in `src/tests/regression/snapshots/dataset_plotter.txt`, an unrelated
component's snapshot); the two layout snapshots (`dataset_plotter.txt`, `metrics_panel.txt`) do not
cover the sidebar.

**Strengths** — fewest lines of any option; **zero** existing assertions touched; ships a decision
that was already *ratified* (D4) rather than making a new one; keeps FR5's "incompatible = disabled"
prescription intact on both sides; leaves OQ-6 open, which is what D5 asks for.

**Weaknesses** — three clicks and a non-obvious one (nothing tells the user that clearing the dataset
is how you reach a 3-D model); it introduces a **new value domain (`None`)** into a control read by
9 callbacks (`:2576`, `:2609`, `:2624`, `:2637`, `:2649`, `:4922`, `:5153`, `:5210`, `:5285`) — I
traced each and none raise, but that is the widest surface of the four proposals.

**Risks** — (R1) `Apply Dataset` with no type (guarded above). (R2) the restart modal seeds
`restart-ds-type` from the sidebar `State` (`:5268` ← `:5285`), so a cleared sidebar hands it `None`;
the chain is closed by the Apply guard, because the pending-dataset banner that opens that modal only
appears after a successful stage. (R3) mount race with `params-init-interval` (benign, ≤1 s window).

**Guardrails**

- `src/tests/unit/frontend/test_n7_dataset_panel.py` — `test_apply_dataset_rejects_a_cleared_type`:
  `_apply_dataset_handler(1, None, ...)` returns `(no_update, <Alert>)` and issues **no** `requests.post`.
- `src/tests/regression/test_model_table.py` — `test_clear_then_select_reaches_the_3d_pair`: the
  §2a chain as a unit test (table(None) all-enabled → `_gate_dataset_options_handler("recurrence", None)`
  returns `"equities_seq"`). This is the recurrence guard for the clear path.
- The same parametrized reachability invariant from Proposal 1, with step 1 run against
  `_build_model_selection_table(None, DEFAULT_MODEL_KEY)` — it will catch a future
  `clearable=False` regression or a future model whose only route in is the clear path.

**What it does NOT fix** — everything Proposal 1 leaves (`:5422`, no snap notice) **plus**: the
discoverability problem (a user must guess that clearing is the escape); the greyed `equities_seq`
option still reads as "you cannot have this" until the model is changed.

**Design-of-record impact** — *Upholds* D2, D5, FR5 unchanged. *Ships* D4/§5.5 as written, including
its stated side-effect ("the model table re-activates fully via the gate"). Does **not** resolve
OQ-6. Closes FR6 ("Clear/reset each selection → restores the full active set on the other side"),
which is currently unimplemented on the dataset side.

---

### Proposal 3 — **"Show all models" opt-in toggle in the modal**

**Mechanism:** add one switch to the model modal that rebuilds the table with `dataset_value=None`,
reusing the already-tested all-compatible path — without introducing a `None` dataset anywhere else
in the app, and without changing any default behaviour.

**How it works**

- Layout, `src/frontend/dashboard_manager.py:2207-2218` (next to `model-search-input`) — add
  `dbc.Switch(id="model-show-all-toggle", label="Show models for other datasets", value=False, className="mb-2")`.
- Callback `:2570-2581` `toggle_model_modal` — add `Input("model-show-all-toggle", "value")` after
  the search `Input`, and pass it through.
- `_toggle_model_modal_handler` (`:2899`) — new parameter `show_all=False`; final line becomes
  `self._build_model_selection_table(None if show_all else dataset_value, selected_model, search=search or "")`.
  Also force `is_open` to stay open when the toggle is the trigger (same shape as the search branch).

**Click flow** — three clicks: "▸ change" → flip "Show all models" → Select(Recurrence) → dataset
auto-snaps to `equities_seq` via `:2702-2706`.

**Diff estimate**

| Item | Count |
|---|---|
| Files touched (product) | 1 — `src/frontend/dashboard_manager.py` |
| Product lines | ~15 (7 layout, 2 callback wiring, ~6 handler + docstring) |
| Callbacks added / modified | 0 added / **1 modified** (`toggle_model_modal` gains an Input) |
| Existing test assertions that MUST change | **0 assertions, but 2 call sites** |

Call sites to change (raw-callback arity — Dash passes Inputs before States positionally):

- `src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py:149` —
  `cb(1, None, "", DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY)` → needs the new `show_all` positional
  after `""`.
- `src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py:158` — same.

`src/tests/regression/test_model_table.py:197`, `:205` (3 positional) and `:366`, `:370`, `:374`
(4 positional) call `_toggle_model_modal_handler` directly and are all unaffected **provided
`show_all` is added last with a default** — the arity break is confined to the two raw-callback
call sites above, which invoke the registered closure rather than the handler.

**Strengths** — changes **zero** existing behaviour; no new value domain outside the modal; explicit
and discoverable ("Show models for other datasets" says exactly what it does); leaves both D2/FR5 and
OQ-6 untouched; the L1 control-graph lint (`util/ui_control_graph.py`) is satisfied because the new
switch is a callback `Input`.

**Weaknesses** — the largest of the three cheap options; adds UI surface for a two-model registry;
still three clicks; the switch's state is not persisted and resets on every modal open (arguably
correct, but it is a decision).

**Risks** — (R1) the arity change silently breaks two raw-callback tests (enumerated above; they fail
loudly with `TypeError`, so low severity). (R2) the per-file coverage gate in
`.github/workflows/ci.yml:255-261` is **blocking at ≥90% statement coverage per file** — every new
line in `dashboard_manager.py` must be exercised, so the tests below are not optional.

**Guardrails**

- `test_toggle_show_all_builds_an_ungated_table` — `_toggle_model_modal_handler("model-show-all-toggle", "spirals", "cascor", show_all=True)`
  → every Select enabled; with `show_all=False` → `recurrence` disabled.
- `test_show_all_toggle_keeps_the_modal_open` — the toggle must not close the modal.
- The same parametrized reachability invariant from Proposal 1, run in both toggle positions.

**What it does NOT fix** — same residuals as Proposal 2, minus the `None`-dataset window; plus it
leaves the *default* experience still reading "Recurrence is not available", which is the actual
user-facing complaint.

**Design-of-record impact** — *Upholds* D2, D5, FR5, D7 unchanged. Is a concrete instance of **OQ-2**'s
"cross-placed clear" alternative ("clear the constraint on *this* list"), which the design doc kept
as a spike alternative — so shipping it is evidence for the OQ-2 comparison rather than a decision
against D4.

---

### Proposal 4 — **Ratify OQ-6 and encode reachability as a registry invariant**

**Mechanism:** adopt Proposal 1's behaviour as the *named, tested* D5 default; move the conflict
resolution out of an `if` inside a dashboard handler and into `model_registry`, add the **notice**
D5's model-primary policy actually specifies, and add a registry-level invariant that no future
seed can create an unreachable pair.

**How it works**

- `src/model_registry.py` — add `CONFLICT_POLICY: str = "model-primary"` and
  `resolve_conflict(model_key, dataset_value) -> tuple[str | None, str | None]` returning the
  post-conflict dataset plus a human notice ("Dataset switched to Equities (sequence) — Recurrence
  (LMU) needs rank-3 (sequence) Δt-aware data."). Also `model_is_reachable(model)` =
  `bool(compatible_datasets(model))`.
- `src/frontend/dashboard_manager.py` — `_gate_dataset_options_handler` routes its snap through
  `resolve_conflict`; Proposal 1's `:3050` change adopts `model_is_reachable`; the notice is rendered
  into a new `dataset-snap-notice` `html.Div` beside `nn-model-dataset-hint` (`:1240`), written by a
  third Output on the existing `annotate_model_hint` callback (`:2647-2652`) — no new callback, no
  new `allow_duplicate` writer.
- Tests: Proposal 1's two flipped assertions, plus a new `src/tests/unit/test_conflict_policy.py`,
  plus the parametrized reachability invariant.
- Docs: amend `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` §5.6/§9 to record
  OQ-6 as resolved and FR5 as amended; add the reachability invariant to canopy's `AGENTS.md`
  Hazards or the docs tree (watch `src/tests/test_memory_budget_check.py`).

**Click flow** — identical to Proposal 1 (two clicks), plus a visible notice after the snap.

**Diff estimate**

| Item | Count |
|---|---|
| Files touched (product) | 2 — `src/model_registry.py`, `src/frontend/dashboard_manager.py` |
| Product lines | ~90 (registry ~40, dashboard ~30, layout ~8, docstrings ~12) |
| Callbacks added / modified | 0 added / 1 modified (`annotate_model_hint` gains an Output) |
| Test lines | ~110 across 3 files |
| Docs | 1 notes amendment + 1 agent-file line |
| Existing test assertions that MUST change | **2** (`test_model_table.py:135`, `:144`) — same as Proposal 1 |

**Strengths** — the only option that ships the *whole* of D5's model-primary policy (snap **and**
notice); makes the policy a named constant so switching to dataset-primary later is a one-line
change; the invariant makes the whole defect class impossible to reintroduce by seeding.

**Weaknesses / Risks** — largest diff; touches the shared `model_registry` module that
`src/main.py:3668,3676,3742` and `src/backend/` also import; the notes amendment invites a design
re-litigation in review; a new Output on `annotate_model_hint` means a Div that must exist at mount
(a missing id is a hard Dash registration error — caught by any `DashboardManager({})` fixture).

**Guardrails** — everything from Proposals 1 and 3, plus:
`test_conflict_policy_is_the_only_snap_path` (grep-free: assert `_gate_dataset_options_handler`'s
snapped value equals `resolve_conflict(...)[0]` for every `MODELS × DATASET_TYPES` pair), and
`test_no_model_is_unreachable` (`assert all(compatible_datasets(m) for m in MODELS)`).

**What it does NOT fix** — `:5422` (§6), which I deliberately keep out of every proposal.

**Design-of-record impact** — *Resolves* **OQ-6** (model-primary) with a recorded rationale.
*Amends* FR5/D2 on the model side. *Upholds* D5's "swappable policy" by making it literally
swappable. *Partially informs* **OQ-2** (D4 vs cross-placed clear) by shipping neither.

---

## 4. Ranking and ship recommendation

Ranked by (correctness × smallness):

| Rank | Proposal | Clicks | Product lines | Assertions changed | Sound alone? |
|---|---|---|---|---|---|
| **1** | **P-1 Un-gate Select (model-primary)** | **2** | ~12 | **2** | **Yes** |
| 2 | P-2 Ship D4's inline ✕ | 3 | ~10 | **0** | Only with the Apply guard |
| 3 | P-3 "Show all models" toggle | 3 | ~15 | 0 (2 call sites) | Yes |
| 4 | P-4 Ratify OQ-6 + invariant | 2 | ~90 | 2 | Yes |

P-2 has *fewer lines* than P-1 and touches *zero* assertions, and on a pure line count it wins. I
still rank P-1 first because line count is the wrong metric here: P-2 introduces a brand-new value
domain (`None`) into a control that nine callback bindings read, whereas P-1 changes one boolean prop
on one component and routes the click into a path that already has a passing test
(`src/tests/regression/test_model_picker.py:91-96`). P-1 is also the only option that fixes the
*default* experience — the others require the user to discover an escape hatch.

**Ship recommendation — two PRs, in this order, one this week:**

1. **PR 1 (ship now): Proposal 1.** `fix(model-selection): make an incompatible model selectable and
   let the dataset snap (OQ-6 → model-primary)`. ~12 product lines, 2 flipped assertions, 3 new
   tests including the parametrized reachability invariant. This closes the defect.
2. **PR 2 (follow-up, independent): Proposal 2.** `feat(dataset): ship the D4 inline clear on the
   dataset dropdown`. Worth having on its own merits — it closes FR6, which is currently
   unimplemented — but it must **not** be the PR that closes this bug, because its residual surface
   is wider and it does nothing for the default experience.

**Do not ship P-3** if P-1 lands: P-1 makes the toggle redundant, and a redundant control is a
liability in a modal that D7 wants to scale to hundreds of rows. **Defer P-4** until P-1 has had one
release of real use — that is precisely what D5 says ("Default chosen post-spike"); PR 1 should carry
a one-line note that OQ-6 is *provisionally* model-primary, with P-4 as the ratification.

**Strongest objection to my top pick (P-1)**, stated as an opponent would:

> P-1 makes a **destructive action reachable in one click with no confirmation and no notice**.
> Clicking "Select" on Recurrence silently discards the dataset the user chose. The design doc's own
> model-primary wording is *"keep model, clear dataset **+ notice**"* (§5.6) — P-1 ships the snap and
> drops the notice, which is the half that makes the policy safe. Worse, it resolves **OQ-6** — a
> decision §5.6 explicitly deferred to "post-spike" — inside a one-line bugfix, where no reviewer will
> read it as a policy change. And its only warning channel, a `title=` tooltip, is exactly the
> affordance §8 of the design doc rules out as unreliable (hover/focus-only, invisible on touch).

My answer: put the consequence in the **rendered compatibility cell**, not the tooltip — it is
already-visible text at D2's prescribed locus, it costs two lines, and it makes the click
self-describing *before* it happens. That converts the objection from "unsafe" to "less ceremonious
than D5 imagined", which is the right trade for a defect that currently makes a shipped model
unusable. The OQ-6 half of the objection stands and should be answered in the PR body, not in code.

---

## 5. Honest answer on the one-liner question

There **is** a one-line change that makes the pair reachable — in fact two, at `:1334` and `:3050`.
I verified both by execution, not inspection.

- `:1334` `clearable=True` is a **sound-ish** one-liner: it works, and its residual failure
  (Apply Dataset with no type) is *visible* — a backend error alert, not silent corruption. Cost:
  one new failure mode, plus three clicks and zero discoverability.
- `:3050` `disabled=False` is the **unsound** one-liner. It works today for both seeded models and it
  will ship green, because the state it breaks — a model with no compatible dataset — does not exist
  yet. When it does, `_gate_dataset_options_handler` takes its `not enabled` branch (`:2704-2705`),
  returns `dash.no_update`, and parks the UI on an invalid pair with every dataset greyed and no way
  out except re-opening the modal. That is the worst outcome available here, and it is one character
  away from the fix I am recommending. The recommended form —
  `disabled=not compatible_datasets(model)` — is the same one line with the predicate tightened, and
  it is sound.

---

## 6. Separately flagged defects (NOT folded into any proposal)

**D-1 (the `:5422` anchor) — the restart modal's dataset dropdown is a permanent hole in the
forward gate. Assessed: real, latent-but-not-theoretical.**

`src/frontend/dashboard_manager.py:5422` builds `restart-ds-type` with
`options=gated_dataset_options(DEFAULT_MODEL_KEY)` at layout-construction time. Grep confirms the
only Outputs on that id are `.value` (`:5268`) — **`options` is never re-emitted**. Consequences:

1. **It is gated to cascor forever.** With Recurrence active, the restart modal offers `spirals`,
   `xor`, `mnist`, `circles`, `moons` as **enabled**, and `equities_seq` as **disabled** — exactly
   inverted. An operator can select a 2-D dataset for a 3-D model and Confirm; the restart POSTs it
   (`:5366` `State("restart-ds-type","value")` → `execute_restart` → `dataset_vals["dataset_type"]`).
   FR9 (§5.9 of the design doc — the model service fails closed) is the only thing standing between
   that and an invalid train.
2. **It can be handed a value its own option list disables.** `:5268` seeds it from the sidebar
   `State` (`:5285`), so with the sidebar on `equities_seq` the control's selected value is an option
   flagged `disabled=True`.
3. **It never composes `apply_availability_gate`.** The sidebar does (`:2702`); this does not. A
   generator whose optional data extra is missing is greyed in one control and selectable in the
   other — two controls writing the same backend field disagree.

Reachability today is narrow (the pending-dataset banner that opens this modal is driven by cascor's
`pending_dataset` field, so the recurrence path rarely lights it), which is *why* it should be filed
rather than patched inside a selection-gate PR. **Suggested fix, separate PR:** give
`restart-ds-type` the same treatment the sidebar dropdown got — add
`Output("restart-ds-type","options")` to the existing `open_restart_confirm_modal` callback
(decorator `:5260-5292`, handler `:5293`; it already carries 17 Outputs and reads the sidebar
value as a `State` at `:5285`) computed as
`apply_availability_gate(gated_dataset_options(<model-selection-store>), self._fetch_generators())`,
which requires adding `State("model-selection-store","data")`. ~6 lines.

**D-2 — the D5 conflict-snap branch is tested but UI-unreachable on the model axis.**
`src/tests/regression/test_model_picker.py:91-96` asserts
`_gate_dataset_options_handler("recurrence", "spirals")` snaps to `equities_seq`. The UI cannot
produce that call, because selecting `recurrence` while `spirals` is active is precisely what the
modal prevents. The branch is only reachable via the *availability* axis (a generator going
unavailable under a fixed model). This is a **vacuous-coverage** pattern: a green test standing in
for a user path that does not exist. Any of the four proposals makes it genuinely reachable.

**D-3 — `_apply_dataset_handler`'s "ALWAYS sent" contract is not enforced.** Its docstring
(`:2828-2841`) states *"`dataset_type` is ALWAYS sent — cascor's `_reload_dataset` hard-requires
it"*, but nothing enforces it, and `src/main.py:3994`'s `model_dump(exclude_none=True)` silently
drops the key if it is `None`. Today `clearable=False` makes `None` unproducible, so the contract
holds *by accident of a UI prop*. That is the same shape as the defect under investigation: a
correctness property resting on a control's `clearable` flag. Worth a 2-line assertion regardless of
which proposal ships.

**D-4 — the §5.8 recovery alert's copy assumes the dataset is the only lever.**
`:3070-3074` tells the user to *"switch the dataset in the sidebar"* — which, in the state that
triggers the alert, the sidebar gate may not allow. Cosmetic today, wrong under P-1.

---

## Appendix — probe output (verbatim)

Script: `scratchpad/probe_p3_clear_flow.py`, run as
`conda run -n JuniperCanopy1 python <script>`. `_fetch_generators` stubbed to `[]` (the documented
flag-absent → all-available fallback), so no network call.

```
== step 0: at-rest defaults ==
  gate(cascor, spirals) -> [('spirals', False), ('xor', False), ('mnist', False), ('circles', False), ('moons', False), ('equities_seq', True)]
  gate(cascor, spirals) -> value: <NoUpdate>
  model table(spirals, cascor) select-disabled: {'recurrence': True, 'cascor': False}

== step 1: click the inline x -> dataset value None ==
  render_dataset_params(None) -> title='Current Dataset' style={'display': 'none'} n_children=1 (no exception)
  hint(None) -> ''
  oneshot_body('live', None) -> None
  NOTE: gate_dataset_options reads the dataset as State -> does NOT re-fire on clear.

== step 2: open the model modal with dataset=None ==
  is_open: True | select-disabled: {'recurrence': False, 'cascor': False}

== step 3: click Select on 'recurrence' (POST mocked ok) ==
  model-selection-store: recurrence | model-class-store: one_shot
  summary: Active: Recurrence (LMU) | modal_open: False

== step 4: store change re-fires the dataset gate with current_value=None ==
  gate(recurrence, None) -> options: [('spirals', True), ('xor', True), ('mnist', True), ('circles', True), ('moons', True), ('equities_seq', False)]
  gate(recurrence, None) -> SNAPPED VALUE: equities_seq

== RESULT ==
  reached pair = (recurrence, equities_seq)
  one_shot start body now: {'dataset': {'generator': 'equities_seq', 'params': {'max_symbols': 5, 'regression_target': 'return'}}}

== control: does the CURRENT code (no clear) reach it? ==
  with cascor selected, equities_seq option: [{'label': 'Equities (sequence) — needs a 3-D model', 'value': 'equities_seq', 'disabled': True}]
  with spirals selected, recurrence Select disabled: True

== extra: model-primary snap direction (proposal 2 feasibility) ==
  compatible_datasets(cascor) -> ['spirals', 'xor', 'mnist', 'circles', 'moons']
  compatible_datasets(recurrence) -> ['equities_seq']
```

**CI context for every diff estimate above** (`/home/pcalnon/Development/python/Juniper/juniper-canopy/.github/workflows/ci.yml`):
the unit lane runs `src/tests/unit/ src/tests/regression/` with `--cov-fail-under=80`, and
`:255-261` runs a **blocking per-file gate at ≥90% statement coverage per file / ≥95% pooled per
sub-module** (`juniper-coverage-gap-map --enforce`). Every new product line in
`dashboard_manager.py` or `model_registry.py` must therefore ship with a test — which is why each
proposal's guardrails are costed as part of the diff, not as optional extras.
