# P1 — Interaction Design & the User's Mental Model

**Author lens**: discoverability, accessibility (WCAG/ARIA), error prevention vs. error recovery,
whether the interface *teaches* the user why something is unavailable, first-time vs. daily user.

**Repo read (read-only)**: `/home/pcalnon/Development/python/Juniper/juniper-canopy`
**Design of record**: `juniper-ml/notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`
**Environment probed**: `JuniperCanopy1` — dash **4.2.0**, dash-bootstrap-components **2.0.4**.

---

## 1. Verdict: **CONFIRMED** — and stronger than stated

The hypothesis is confirmed, and I can put an exhaustive proof under it rather than an argument.

I ran the app's *own* transition functions as a reachability closure from the seeded default pair
(`model_registry.DEFAULT_MODEL_KEY` = `cascor`, `DEFAULT_DATASET_TYPE` = `spirals`), using exactly
three moves the UI permits:

1. pick any **non-`disabled`** option from `gated_dataset_options(model)` (the sidebar dropdown);
2. click any model Select button whose `model_reason(model, dataset) is None` (the only enabled ones);
3. apply `_gate_dataset_options_handler`'s auto-snap after move 2.

Result:

```
REACHABLE from ('cascor', 'spirals'):
    ('cascor', 'circles')  ('cascor', 'mnist')  ('cascor', 'moons')
    ('cascor', 'spirals')  ('cascor', 'xor')

COMPATIBLE-but-UNREACHABLE: [('recurrence', 'equities_seq')]
```

There are exactly **six** compatible `(model, dataset)` pairs in the registry. **Five are reachable.
The sixth — the only pair that exercises the LMU model and the only pair that exercises the
`equities_seq` dataset — is unreachable from the shipped default.** Both of those registry entries
exist solely to make that one pair work (`model_registry.py:138-149`, `:179-192`), and the product
cannot reach it. The recurrence backend, its service wiring (`RECURRENCE_PROVIDER`,
`_swap_backend`, juniper-deploy #132), the one-shot Start body (`_resolve_oneshot_start_body_handler`),
and the cascade-panel suppression path are all dead from the UI.

A second, sharper way to say it: **`_gate_dataset_options_handler`'s snap branch
(`dashboard_manager.py:2703-2705`) is unreachable in the model-change direction.** A model can only
be selected when it is compatible with the current dataset; a compatible model by definition leaves
the current dataset enabled; therefore `current_value in enabled` is always true on a model change,
and the snap never fires. The single piece of conflict-resolution logic in the whole feature has
**never run** on the path it was written for. (It can still fire at mount via `params-init-interval`
if the availability gate disables the current generator.)

### 1.1 Anchor-by-anchor

| Anchor | Status | Note |
|---|---|---|
| `src/model_registry.py` — `DATASET_TYPES` (6 seeds, `equities_seq` ndim=3 temporal=irregular), `MODELS` (`cascor` ndim={2}; `recurrence` ndim={3} `requires_dt=True`), `compatible()`, `dataset_reason()`, `model_reason()`, `gated_dataset_options()`, `dataset_model_hint()` | **CORRECT** | All present, exactly as described. `:132-150`, `:167-193`, `:311-318`, `:337-351`, `:354-372`, `:382-405`, `:408-424`. |
| `dashboard_manager.py:1334` — sidebar dropdown, `options=gated_dataset_options(DEFAULT_MODEL_KEY)`, `clearable=False` | **CORRECT** | Component id `nn-dataset-type-dropdown` opens at `:1331`; `options=` is `:1332`, `value=` `:1333`, `clearable=False` `:1334`. |
| `:1842` — `model-selection-store` seeded to `DEFAULT_MODEL_KEY` | **CORRECT** | `storage_type="memory"`. See §7 defect D-2: it is *never* hydrated from backend state (FR15). |
| `:2687` `_gate_dataset_options_handler` — re-gates on model change and auto-snaps | **CORRECT, with a correction** | The snap exists (`:2703-2705`) but is **dead in the model-change direction** (above). Also composes a *second* gate: `apply_availability_gate` (`dataset_schema.py:267`). |
| `:3000` `_build_model_selection_table`, `:3050` `disabled=not is_compatible` | **CORRECT** | `def` at `:2999`; `disabled=not is_compatible` at `:3050`; `title=(reason or …)` at `:3051`. |
| `:5422` `restart-ds-type` — statically gated to `DEFAULT_MODEL_KEY`, never re-gated | **CORRECT** | Only six references repo-wide; `options=` is built once at layout-build time and no callback ever writes `restart-ds-type.options`. See §7 defect D-1. |
| `src/tests/regression/test_model_table.py:134-135, :143-144` pin current behavior | **CORRECT** | `:134-135` pin `recurrence.disabled is True` against spirals; `:143-144` pin `cascor.disabled is True` against `equities_seq`. Both are *correct assertions about a per-row render* — neither is wrong, and neither can catch the defect, because **the defect is not in any single render; it is in the closure over renders.** That is the whole lesson (§6, INV-1). |

### 1.2 One correction worth having: the "cleared" state is already built

`_build_model_selection_table` already treats a falsy `dataset_value` as *unconstrained*
(`:3016` `dataset = get_dataset_spec(dataset_value) if dataset_value else None`; `:3033`
`reason = model_reason(model, dataset) if dataset is not None else None`). I ran it:

```
cleared dataset=None -> select buttons (key, disabled) = [('cascor', False), ('recurrence', False)]
cleared dataset=''   -> select buttons (key, disabled) = [('cascor', False), ('recurrence', False)]
hint(None)    -> ''            # _dataset_model_hint_handler clears cleanly
title(None)   -> 'Current Dataset'
oneshot(None) -> None          # _resolve_oneshot_start_body_handler already guards
```

**The unconstrained state that D4/§5.5 specified is already implemented in four handlers, and it is
unreachable because of one keyword argument** (`clearable=False`, `:1334`). That is the single most
economically-interesting fact in this investigation and it reshapes the proposal ranking below.

---

## 2. What the interface teaches (the mental-model failure)

The gate is not merely blocking; it is **actively instructional, and the instruction is a lie**.

A first-time user who wants the LMU model does one of two walks. Both terminate in a contradiction:

- **Dataset-first.** Opens the dataset dropdown. Sees `Equities (sequence) — needs a 3-D model`
  (greyed). Reads that as *"go get a 3-D model."* Opens the model surface. Sees
  `Recurrence (LMU) · needs 3-D data` with a dead **Select**. The UI has just told them, in order,
  to fetch A to get B and to fetch B to get A.
- **Model-first.** Clicks **▸ change**. Sees the LMU row, a green `LIVE` badge
  (`_status_badge`, `:2987`), a description promising exactly what they want — and a dead button.
  Then reads the sidebar hint `rank-2 (tabular) models only` (`dataset_model_hint`), which is a
  *statement about the current world*, not an *instruction*, and offers no verb.

Three specific interaction-design faults produce this:

1. **Every reason is a diagnosis; none is a prescription.** `dataset_reason` returns
   `"needs a 3-D model"`; `model_reason` returns `"needs 3-D data"`; `dataset_model_hint` returns
   `"rank-2 (tabular) models only"`. All three are *true*, *well-worded*, correctly placed at the
   locus (D2 — genuinely well executed), and **none names an action the user can take.** WCAG SC
   3.3.3 (*Error Suggestion*) is the codified version of this: identifying a constraint is only half
   the obligation; suggesting the correction is the other half. The system knows the correction —
   `compatible_datasets(recurrence)` returns exactly one answer — and withholds it.
2. **Both controls present as filters and behave as latches.** A dropdown with `clearable=False` and
   a modal with no *"show all / clear"* affordance teach "these are pickers, one of many values."
   The user's model of a picker includes *undo by re-picking*. Here, re-picking is the operation
   that is unavailable. There is no state in the UI vocabulary for "I have not decided yet," even
   though the code supports it (§1.2).
3. **The disabled state is where the actionable content lives.** The reason string is only ever
   attached to something the user cannot interact with. That is an inversion: the more relevant
   the information is to what the user is trying to do, the less reachable it is.

**Daily user vs. first-time user.** A daily user never meets this, because the reachable subgraph
(all-cascor) is the whole product they know; the defect is invisible to them and will read as "the
LMU work isn't wired up yet." A first-time user meets it on their second click and concludes the
dashboard is broken. That asymmetry is why the defect survived: *the population that could report
it has already stopped believing the feature exists.*

---

## 3. Accessibility findings (this lens owns these)

Grepping `dashboard_manager.py` for `aria-`, `aria_`, `role=`, `tabIndex`: **zero hits**. (`grep -c
aria` reports 4; all four are the substring inside the word *variable*.) There is no
`aria-describedby`, no `role="status"`, no live region anywhere in the 7,967-line layout+callback
module. So the following are not "could be better" — they are the whole story.

### A11Y-1 — the disabled Select button conveys its reason to no one (`:3050-3052`)

`dbc.Button(disabled=True)` (dbc 2.0.4, no `href`) renders a native `<button … disabled>`. Native
`disabled`:

- **removes the element from the tab sequence** — there is no keyboard path to it at all;
- **suppresses pointer events** in every major browser, so the `title=` at `:3051` does not
  reliably render a native tooltip on hover either;
- and — decisively — **`title` is the last-resort accessible-name source, used only when the element
  has no content.** This button has content (`"Select"` / `"Selected"`), so per HTML-AAM the `title`
  **never becomes the accessible name**. Some AT expose `title` as a *description*, but only for an
  element that can be reached, which this one cannot.

Net: `title=(reason or …)` at `:3051` is a **dead channel**. It is worse than absent, because it
reads in the source like the reason *is* conveyed, and an implementer auditing the row will tick it
off. The design's own §8 says precisely this — *"a `dbc.Tooltip` target must be focusable to be
keyboard-reachable … disabled elements don't fire hover/focus — which is exactly why D2 puts the
reason in the label/cell, not a tooltip on a disabled option"* — so `:3051` contradicts the design's
stated reasoning. (SC 4.1.2 *Name, Role, Value*.)

### A11Y-2 — the reason cell has no programmatic relationship to the control it explains

`compat_cell` (`:3037-3040`) is a sibling `<td>`. It has **no `id`**, and the Select button has **no
`aria-describedby`**. The relationship is purely spatial. A screen-reader user navigating by form
control — the standard efficient mode — hears *"Select, button, unavailable"* and nothing else; to
get the reason they must recognise they are in a table, switch to table-navigation mode, and read
the sibling cell. (SC 1.3.1 *Info and Relationships*.)

### A11Y-3 — the dropdown does not expose the disabled state at all (dash 4.2.0)

The design §8 correctly notes Dash 4's `dcc.Dropdown` is the new native virtualized control. I
enumerated the ARIA attributes its bundle can emit:

```
async-dropdown.js  ->  aria-label(2) aria-labelledby(1) aria-hidden(1) aria-haspopup(1) aria-expanded(1)
```

**There is no `aria-disabled` in the bundle.** A `disabled` dataset option's *state* is therefore
not programmatically exposed; it is simply inert. The **only** channel that survives is the option's
text — which is exactly what D2's reason-suffix uses. **D2 is, by accident of implementation, the
one accessible thing in this feature.** That is the generalisable lesson for every proposal below:
*put the reason in the accessible NAME of a control the user can actually reach.*

### A11Y-4 — silent state mutation with no status message

`_gate_dataset_options_handler` can rewrite `nn-dataset-type-dropdown.value` (`:2705`). There is no
`role="status"` / `aria-live` region anywhere, so that change is announced to nobody. Today this is
latent (the branch is dead in the model path — §1). **Every proposal below that revives the snap
must ship a live region with it**, or it converts a visible-only surprise into an invisible one.
(SC 4.1.3 *Status Messages*.)

### A11Y-5 — contrast, and why the exemption is the point

The reason cell is `text-muted small fst-italic`. Light mode: `#6c757d` on white ≈ 4.68:1 — passes
AA for normal-size text, narrowly. Dark mode: `--text-muted: #adb5bd` (`dark_mode.css:35`) on the
dark surface — comfortable. So it *passes*. The interesting part is that **WCAG 1.4.3 exempts
inactive/disabled UI components from contrast requirements at all** — and the drafters granted that
exemption on the assumption that *disabled controls do not carry information the user needs to act
on*. Here they carry the only information the user needs to act on. The exemption is a signal that
this information is in the wrong place, not a licence to leave it there.

---

## 4. Proposals

Four distinct mechanisms. Not four settings of one knob: **(A)** make the constraint removable;
**(B)** make selection auto-resolving; **(C)** make the *pair* the unit of selection; **(D)** replace
the dead control with a resolution affordance.

---

### P1-A — "Ship the ✕": make the constraint removable (D4/§5.5, four years late)

> **Mechanism**: introduce the *unconstrained* state as a first-class, reachable UI state on both
> surfaces. Clearing either selection widens the other to everything. The escape from any deadlock —
> present or future — is "stop constraining."

#### How it works

1. `dashboard_manager.py:1334` — `clearable=False` → `clearable=True`; add
   `placeholder="No dataset — all models shown"`.
2. `_gate_dataset_options_handler` (`:2687`) — add an early branch: when `current_value` is falsy,
   return `(options, dash.no_update)`; **never snap a deliberately-cleared dataset back to a value.**
   This is the one place a careless implementer will re-break it, because the existing snap logic
   reads "if the current value isn't enabled, pick one."
3. Model surface — add `dbc.Button("Show all models", id="model-clear-dataset-filter", …)` next to
   `model-search-input` (`:2209`). **Do not give it its own `Output("nn-dataset-type-dropdown","value")`** —
   `gate_dataset_options` (`:2605`) already owns that Output, and canopy has an explicit history of
   removing two-writer bugs (F-CANOPY-018 / F-CANOPY-027, cited in-source at `:3117-3120`). Add it
   as an **Input to that same callback** and branch on `dash.callback_context.triggered_id`.
4. `_build_model_selection_table` — **no change required** (§1.2: the `dataset is None` path already
   enables every row). Render an explicit banner in the cleared state: *"No dataset selected —
   showing all models. Selecting a model will filter the dataset list."* so the state is *named*, not
   just empty.
5. **Guard the five downstream consumers** that will now see `None`:
   `apply_dataset` (`:4934`), `open_live_switch_modal` (`:5160`), `accept_live_switch` (`:5218`),
   `open_restart_confirm_modal` (`:5293`), and `execute_restart` via `restart-ds-type` (`:5380`).
   Each must disable its trigger button with a visible reason ("select a dataset first") rather than
   POST `dataset_type=None`.

#### Strengths

- **It is the design of record.** D4 and FR6 specify exactly this and it was never shipped. No
  amendment needed; this is a completion, not a change.
- **Cheapest correct fix by a wide margin** — the table builder, the hint handler, the section-title
  handler and the one-shot body resolver *already* handle the cleared state (§1.2, run and verified).
- **Universal.** It is the only proposal whose correctness argument does not depend on the shape of
  the compatibility partition. Two components, three, seventeen — clear, then re-pick, always works.
- Upholds **D1, D2, D5, D7, D8** unchanged; implements the unimplemented **FR6**.
- Adds no disabled controls, so no new a11y debt.

#### Weaknesses

- **It does not teach.** The user still has to *infer* that clearing is the move. The ✕ is a
  conventional glyph for "remove this value"; nothing about it says "removing this is how you reach
  the LMU model." A first-time user who never suspects the two controls are coupled will not think
  to clear one. This is error *recovery* offered without error *explanation*.
- **Two-step, and the intermediate step is worse at scale.** Clearing the dataset when there are
  100+ models destroys the only filter that makes the table navigable (§6 of the design is explicit
  that organisation, not gating, is the long pole). "Show all models" is a *de-filtering* action
  presented as the remedy for a *filtering* problem.
- Adds a null to a value that ~5 call sites currently assume is a non-empty string.

#### Risks

- **The `None` fan-out is the real cost**, and it is the part a careless implementer gets wrong:
  shipping `clearable=True` alone (a one-word diff that *looks* complete and unblocks the deadlock in
  manual testing) leaves five POST paths that will send a null dataset type to staging / live-switch /
  restart routes.
- **Snap-back regression**: if step 2 is missed, clearing the dropdown immediately re-snaps to
  `spirals` on the next gate fire and the fix silently evaporates — with a green test suite.
- At **3+ partition components**: fully correct; complete reachability by construction.
- At **scale (§6)**: correctness fine, usability degrades (above).

#### Guardrails

- **INV-1 (reachability closure)** — see §6. Must be run with the cleared state as a legal node.
- **INV-2 (no dead-end control)**: assert that for every gated dropdown render, either ≥1 option is
  enabled **or** `clearable is True`. This single assertion is the machine-checkable form of "the user
  is never stuck."
- Regression: `_gate_dataset_options_handler("recurrence", None)` must return `dash.no_update` for
  the value — a directly-invocable unit test in the existing `test_model_table.py` style.
- Regression per consumer: `_apply_dataset_handler(1, None, …)` and the four siblings must return a
  refusal/notice, never issue a request. Assert with a mocked `requests.post` that **zero** calls are made.
- CI: a static check that `Output("nn-dataset-type-dropdown", "value")` has exactly one owning
  callback (see INV-6).

#### Design-of-record impact

Upholds D1/D2/D5/D7/D8; **implements D4 and FR6** as written. **Does not resolve OQ-6** — with a
clear affordance available, no conflict policy is forced, which is arguably the honest answer to
OQ-6 but is not *an* answer. Amends nothing.

---

### P1-B — "Selecting resolves": auto-migrate the dataset, announce it, offer undo

> **Mechanism**: decide D5's conflict policy as **model-primary** and let the existing (currently
> dead) auto-snap do the work. Selecting an incompatible model is permitted; the dataset moves to
> that model's first compatible dataset; the change is announced and reversible.

#### How it works

1. `_build_model_selection_table` `:3050` — `disabled=not is_compatible` → **`disabled=False`** for
   the compatibility axis (D8's lifecycle gate stays at the training controls per the ratified
   option (a), `test_model_table.py:148`).
2. Reword the compatibility cell for incompatible rows from a refusal to a **consequence**:
   `model_reason` stays for the "why", and a new
   `model_registry.switch_consequence(model, dataset) -> str | None` returns
   `"will switch dataset to Equities (sequence)"` (derived from `compatible_datasets(model)[0]`), or
   `"no compatible dataset"` when the set is empty (§5.8 per-row).
3. `_gate_dataset_options_handler` (`:2687`) — **unchanged**; its snap branch becomes live for the
   first time.
4. New notice: `html.Div(id="model-switch-notice", role="status", aria_live="polite")` beside
   `nn-model-dataset-hint` (`:1237-1242`), written by the same callback that owns the dataset value.
   Text: *"Dataset switched to Equities (sequence) because Recurrence (LMU) needs rank-3 (sequence)
   data. [Undo]"*.
5. Undo: a `dcc.Store(id="last-selection-store")` holding the prior `(model, dataset)`; the Undo
   button restores both through the single dataset-value-owning callback.
6. Delete `title=` at `:3051` (A11Y-1).

#### Strengths

- **The machine already knows the answer.** `compatible_datasets(recurrence)` has exactly one
  element. Making the human solve a constraint-satisfaction puzzle the resolver can solve in O(n) is
  the core design error, and this addresses it head-on.
- **Smallest behavioural diff to shipped code**: the snap already exists at `:2703-2705`; this
  proposal mostly *unblocks* it.
- One click from the default state to the target pair — best-in-class for the daily user.
- **Resolves OQ-6** explicitly (model-primary), which the design left open and which §5.6 notes
  *"fits the model-centric benchmarking trajectory."*
- No disabled controls in the table → A11Y-1/A11Y-2 dissolve.

#### Weaknesses

- **It violates the spirit of FR4** (*"When >1 option remains compatible, the user chooses within the
  set — no silent auto-pick"*). Auto-snapping to `compatible_datasets(model)[0]` is exactly a silent
  auto-pick, on the dataset axis. With today's seeds the target set has size 1 so it is defensible;
  the moment a second 3-D dataset lands — which §1 of the design says is imminent — the UI starts
  choosing for the user. This requires an FR4 amendment, honestly stated.
- **Silent destruction of context.** A user who clicks a model row *to read about it* (the description
  is in the row, so reading is a plausible intent) loses their dataset. Worse: selecting a model POSTs
  `/api/model/select`, which **re-creates the process-global backend** (`main.py:3689-3729`) and 409s
  during training. Clicking a row is already destructive; this makes it more so.
- Undo is real new state and a real new failure mode (undo after the backend swap has to swap back).

#### Risks

- **What a careless implementer gets wrong**: shipping step 1 without step 4. Then the dataset
  changes with no announcement at all — a strictly worse product than the deadlock, because the user
  now silently trains on a dataset they did not choose.
- **At 3+ partition components**: reachability is complete, but "first compatible" becomes arbitrary.
  The user clicks a model and is teleported to a dataset from a component they have never seen. The
  notice text is doing *all* the work of orientation, from a `text-muted` aside in a sidebar.
- **At scale (§6)**: one mis-click among 100+ rows silently mutates global state. Risk grows linearly
  with row count while the notice stays the same size.
- Regression: `test_model_table.py:135` and `:144` assert `disabled is True` and **will fail**. They
  must be rewritten, not deleted — replace with assertions on the *consequence text* and on
  `disabled is False`, so the intent (incompatibility is communicated) survives the mechanism change.

#### Guardrails

- **INV-1** with the pair transition included.
- **INV-4 (no silent mutation)**: any callback returning a changed `nn-dataset-type-dropdown.value`
  must, in the same return, produce non-empty `model-switch-notice` children. Assert on the handler's
  return tuple — cheap, and it is exactly the assertion that stops the "shipped step 1, forgot step 4"
  failure.
- Assert `model-switch-notice` carries `role="status"` in the built layout (a11y regression).
- **FR4 tripwire**: a test asserting that when `len(compatible_datasets(model)) > 1` the handler does
  **not** auto-pick but instead routes to a chooser. Ship it failing/skipped with an xfail naming the
  FR4 amendment, so the debt is recorded rather than forgotten.
- Property test over synthetic registries with 3 and 4 components (§6).

#### Design-of-record impact

**Resolves OQ-6** (model-primary). Upholds D5 (uses the swappable-policy slot as intended), D2 (reason
stays at the locus, reworded), D8, FR2, FR9. **Overturns D2's "incompatible options are DISABLED"
clause for the model table** and **amends FR4** — both must be written into the design doc, not left
implicit.

---

### P1-C — "The pair is the unit": `Select with…` (recommended)

> **Mechanism**: stop presenting model and dataset as two independently-gated controls with a hidden
> mutual dependency. Every model row offers exactly one enabled control: **`Select`** when compatible,
> or **`Select with… ▾`** (a menu of that model's compatible datasets) when not. Choosing a menu item
> applies both selections as one transaction. **Nothing is ever disabled.**

#### How it works

1. `_build_model_selection_table` (`:2999`) — replace the single `select_button` construction
   (`:3041-3052`) with a branch:
   - **compatible** → `dbc.Button("Select" | "Selected", id={"type":"model-select-btn","index":key}, …)` — unchanged, never disabled;
   - **incompatible, `compatible_datasets(model)` non-empty** →
     ```
     dbc.DropdownMenu(
         label="Select with…",
         id={"type": "model-pair-menu", "index": key},
         toggle_style=…,  size="sm",
         children=[dbc.DropdownMenuItem(d.label,
                       id={"type":"model-pair-btn","index":f"{key}|{d.value}"})
                   for d in compatible_datasets(model)[:5]] + overflow,
     )
     ```
     with `aria_label=f"Select {model.label} — {reason}; choose a compatible dataset"` on the toggle,
     so the **reason is in the accessible name of a focusable control** (the A11Y-3 lesson);
   - **incompatible, empty compatible set** → static text *"no compatible dataset available"*
     (the §5.8 degenerate state, rendered per-row instead of only table-wide).
2. Add a **"Trains on"** column: `", ".join(d.label for d in compatible_datasets(model)[:3])` with
   `"+N more"`. This is D3's compatibility grid, folded into the row the user is already reading,
   instead of hidden behind a separate help affordance.
3. **Delete `title=`** at `:3051` (A11Y-1).
4. **The pair transaction — the part to get right.** Do **not** add a second writer of
   `nn-dataset-type-dropdown.value`. Instead:
   - extend the existing `select_model` callback (`:2591-2601`) with a second pattern-matching Input
     `Input({"type":"model-pair-btn","index":ALL}, "n_clicks")` and one new Output
     `Output("pending-dataset-store", "data")` (a new `dcc.Store`);
   - `select_model` parses `"<model>|<dataset>"` from `ctx.triggered_id["index"]`, POSTs the model as
     today via `_select_model_handler`, and writes the dataset into `pending-dataset-store`;
   - add `Input("pending-dataset-store","data")` to `gate_dataset_options` (`:2605`), which **remains
     the sole writer** of `nn-dataset-type-dropdown.value`. It re-gates options against the new model
     and sets the value to the pending dataset (enabled by construction).

   Both stores are written in one callback return, so the downstream gate fires **once** with both
   values consistent. Ordering is thereby structural, not incidental.
5. Add the same `role="status"` notice as P1-B for the resulting dataset change (it is now
   user-chosen, so the notice confirms rather than surprises).

#### Strengths

- **No control in the feature is ever `disabled` for compatibility.** A11Y-1, A11Y-2 and A11Y-3
  dissolve *by construction* rather than by remediation; every reason lives in the accessible name of
  a focusable, keyboard-operable control.
- **It teaches.** The row does not say "you can't"; it says "here is what this model trains on." A
  first-time user learns the compatibility structure *by browsing*, which is the mode they are already
  in. That is the difference between error prevention and error *education*.
- **Satisfies FR4 without amendment** — the user chooses within the compatible set. P1-B reaches the
  same end state by choosing for them; C is the version that does not need FR4 rewritten.
- **Best behaviour at 3+ components** — each row displays its own component. Where P1-B's "first
  compatible" becomes arbitrary and P1-D's dialog must grow into a list, C already *is* the list.
  (Analytically: **C is the limit of D as the partition grows** — D's resolution dialog, done at the
  locus and inlined.)
- Upholds **D1, D2** (reason at the locus, now in an accessible name), **D5** (policy expressed as a
  per-instance user choice rather than a global default), **D7** (all of it lives on the dedicated
  surface; the sidebar is untouched), **D8** (lifecycle gate stays at the controls),
  **FR2, FR4, FR5's intent, FR7, FR9**. Delivers **D3** cheaply as a column.

#### Weaknesses

- **Two affordances where there was one.** `Select` vs `Select with… ▾` is itself a discoverability
  cost — a user must notice that the *shape* of the control encodes compatibility. Mitigation: the
  "Trains on" column carries the same information redundantly, in text.
- **Most implementation of the four**, and the only one that adds a compound widget
  (`DropdownMenu` = toggle + menu + items) with its own keyboard-navigation contract to verify in
  dbc 2.0.4.
- Does **not** deliver FR6 (clear/reset). A user who wants to browse *all* models with no dataset
  constraint still cannot. C removes the *need* for clearing to escape a deadlock, but not the *want*.
  (This is why my ship recommendation pairs C with A — see §5.)
- Duplicates a dataset choice into the model surface — conceptually the sidebar dropdown is no longer
  the only place a dataset is chosen.

#### Risks

- **The two-writer trap is the #1 careless-implementer failure**, and canopy has a documented history
  with exactly this class (`dashboard_manager.py:3117-3120` cites F-CANOPY-018 / F-CANOPY-027 as
  *"the two-writer class this arc has been removing"*). Anyone implementing C by adding
  `Output("nn-dataset-type-dropdown","value", allow_duplicate=True)` to `select_model` will produce
  a race between the pair transaction and the gate. The `pending-dataset-store` indirection (step 4)
  exists solely to prevent this and must be treated as load-bearing, not as an implementation detail.
- **Ordering**: applying the model first and the dataset second (or vice versa, in two round-trips)
  creates a visible intermediate state where the gate snaps the dataset somewhere else before the
  pending value lands. The single-callback-return design eliminates the window; a two-callback
  implementation does not.
- **At scale (§6)**: `compatible_datasets` per row is O(models × datasets) per render — 100×6 = 600
  predicate calls, trivial; but 100 `DropdownMenu` components is real DOM weight in a modal that
  `scrollable`s rather than virtualizes (OQ-4 was deferred). Mitigate: render the menu only for rows
  that are incompatible (already the case), cap the item list, and revisit under OQ-4's virtualization
  decision. **Pin a render-count budget test** so this is caught by CI, not by a user.
- Regression: `test_model_table.py:135` / `:144` assert `disabled is True` and will fail; rewrite to
  assert *"the row's enabled control is the pair menu, and its accessible name contains the reason."*

#### Guardrails

- **INV-1 (reachability closure)** including the pair transition — see §6.
- **INV-2 (no dead-end control)**: every model row must yield ≥1 interactive component with
  `disabled` falsy. Directly assertable on the built tree with the existing `_walk` helper.
- **INV-3 (reason is programmatically reachable)**: for every incompatible row, the `model_reason`
  string must appear in the enabled control's children **or** its `aria_label` / `aria_describedby`
  target. Plus the negative half: **assert no component in the tree conveys a reason via `title=`
  alone.** This is the assertion that retires A11Y-1 permanently.
- **INV-6 (single writer)**: assert `Output("nn-dataset-type-dropdown","value")` has exactly one
  owning callback in `app.callback_map`. This is the machine-checkable form of canopy's two-writer
  discipline and is worth having regardless of which proposal ships.
- Transaction unit test: `_select_model_from_table_handler` with
  `triggered_id={"type":"model-pair-btn","index":"recurrence|equities_seq"}` returns both the model
  store and the pending-dataset store in one call.
- Property test over synthetic 3- and 4-component registries (§6).
- Render-budget test: `_build_model_selection_table` over a synthetic 100-model registry completes
  under a fixed component-count / wall-clock budget.

#### Design-of-record impact

Upholds D1, D3 (delivers it), D5, D7, D8, FR2, FR4, FR5-intent, FR7, FR9. **Amends D2** — the reason
still sits at the locus, but the locus becomes an *enabled* control's accessible name rather than a
disabled item's label. **Amends FR5** — "visible but disabled" becomes "visible and actionable, with
the reason in the control's name"; the prevention guarantee moves entirely to FR9/D5 where the design
already says it belongs (*"greying is best-effort, NOT the correctness guarantee"*). **Resolves OQ-6**
in a form the design did not enumerate: the conflict policy becomes **explicit-at-the-locus** rather
than a global default — which is strictly more informative than either candidate and should be written
back as a third policy option.

---

### P1-D — "Never disable; the dead control becomes a resolution dialog"

> **Mechanism**: revive alternative **D** from design §11 (*indicator-only, no greying*), which was
> rejected as the *sole prevention* mechanism — but FR9 says prevention was never the UI's job. Nothing
> is disabled anywhere. Activating an incompatible option opens a small `role="alertdialog"` that
> names the conflict and offers only *resolving* actions.

#### How it works

1. `_build_model_selection_table` `:3050` — drop the compatibility `disabled`; keep the reason cell;
   append the reason to the button's visible label (`"Select — needs rank-3 (sequence) data"`) so it
   is the accessible name. Delete `title=`.
2. `gated_dataset_options` (`model_registry.py:408`) — return incompatible options **enabled**, with
   the reason suffix retained, plus a new key `"reason_class": "incompatible"`.
   **Critically**: `apply_availability_gate` (`dataset_schema.py:267`) must continue to emit
   `disabled: True` with `"reason_class": "unavailable"` — an unavailable generator has **no
   resolution**, so un-disabling it would be a regression. The composition rule inverts: *compatibility
   is negotiable, availability is not.*
3. New `dbc.Modal(id="selection-conflict-modal", role="alertdialog")` opened by a selection whose pair
   is incompatible. Body names the conflict in plain language and offers exactly two buttons:
   **"Switch dataset to Equities (sequence)"** and **"Keep Spirals — choose a different model"**.
   **It must not offer "proceed anyway."**
4. Both buttons route through the single dataset-value-owning callback (the P1-C `pending-dataset-store`
   pattern applies verbatim).

#### Strengths

- **Best pure-accessibility outcome of the four**: nothing leaves the tab order, every reason is on a
  focusable element, and the resolution is an `alertdialog` — a role AT handle well and announce
  automatically.
- **Resolves OQ-6 by not resolving it**: the policy becomes a user decision at the moment of conflict,
  which is the most honest reading of D5's *"greying is best-effort, NOT the correctness guarantee."*
- **Lowest DOM weight at scale** — one dialog, no per-row widgets. Better than C at 100+ rows.
- Error *recovery* replaces error *prevention*, appropriate when the "error" is cheap and reversible
  (a backend swap that FR9 backstops) and the prevention creates a trap.

#### Weaknesses

- **A modal inside a modal.** `selection-conflict-modal` opens over `model-selection-modal`. Nested
  dialogs are a focus-trap hazard and a well-known usability smell; dbc will not manage the nesting for
  you.
- **Overturns D2 and FR5 outright** — more design-doc surgery than any other proposal.
- **It interrupts.** Every incompatible click costs a dialog. For a user exploring 100 rows this is
  modal fatigue, and modal fatigue trains click-through, which is how a user ends up somewhere they
  did not intend.
- **It degenerates into C** as soon as a model has more than one compatible dataset: the dialog's
  "Switch dataset to X" must become a list. At that point you have built C's menu, in a worse location.

#### Risks

- **The dangerous mis-implementation is adding "Proceed anyway."** It is the obvious third button, and
  it is a trap: `POST /api/model/select` validates only that the key exists in the registry
  (`main.py:3736-3743`); it does **not** validate the model against the staged dataset. The swap
  succeeds, canopy holds an incompatible pair, and the failure surfaces at **Start**, in the recurrence
  service, far from the decision. That relocates the error to the worst possible locus. The dialog must
  offer only resolutions.
- **The availability/compatibility conflation** (step 2) is the second trap: un-disabling *everything*
  makes unavailable generators clickable with no possible resolution.
- **At 3+ components**: as above, degenerates toward C.
- Same test-rewrite cost at `test_model_table.py:135` / `:144`.

#### Guardrails

- **INV-1**, **INV-2**, **INV-3** as above.
- **INV-5 (disable-class separation)**: assert that an option carrying `reason_class == "unavailable"`
  is `disabled` in **every** render path, and that no code path un-disables it. This is the assertion
  that stops the composition trap.
- Assert `selection-conflict-modal`'s children contain **no** control whose handler applies an
  incompatible pair — a structural test that "Proceed anyway" can never be added without a failing test.
- Focus-management test: opening the nested dialog moves focus into it and closing restores focus to
  the originating row control.

#### Design-of-record impact

**Overturns D2** (disabled) and **FR5**. Upholds D5 (leans on it hard), D7, D8, FR9. **Resolves OQ-6**
as "policy is chosen per-conflict by the user" — a third option to add to §5.6.

---

## 5. Ranking, and what I would ship

| Rank | Proposal | Teaches? | A11y | FR4 | 3+ components | Scale (§6) | Cost |
|---|---|---|---|---|---|---|---|
| **1** | **P1-C** pair-as-unit | **yes** | **best by construction** | **satisfied** | **best** | DOM weight; mitigable | high |
| 2 | P1-A ship the ✕ | no | neutral | n/a | complete | de-filters at scale | **lowest** |
| 3 | P1-D never-disable + dialog | partly | best | satisfied | degenerates → C | best DOM weight | medium |
| 4 | P1-B auto-snap | no | good | **amended** | arbitrary | mis-click risk grows | **lowest code** |

**I would ship P1-A and P1-C together, in that order, as two PRs.**

- **P1-A first, alone, as the unblocking PR.** It is the design of record (D4/FR6), the cleared state
  is already implemented in four handlers and gated by one keyword (§1.2), and it is the only fix whose
  correctness does not depend on the partition's shape. It restores reachability *today* and it is the
  right permanent floor: whatever gating we build later, "stop constraining" must always be one click
  away. Ship it with INV-1 and INV-2, and with the five `None` guards — that last part is where the
  work actually is.
- **P1-C second, as the design PR.** A is an escape hatch; C is the interface that means the user never
  needs one. C is the only proposal that makes the compatibility structure *legible* rather than merely
  *enforced*, retires all three a11y findings by construction rather than by remediation, satisfies FR4
  without amending it, and is the only one that gets *better* as the partition grows — which §1 of the
  design says is imminent and §6 says is the long pole.

**Not P1-B**, despite it being the cheapest code, because it trades a visible deadlock for an invisible
state mutation, and because its FR4 amendment expires the moment a second 3-D dataset lands.
**Not P1-D standalone**, because it converges on C while paying nested-modal and interruption costs C
does not.

### The single strongest objection to P1-C — stated against myself

**C puts a dataset chooser inside the model surface, which creates a second writer of
`nn-dataset-type-dropdown.value` — and that is the exact bug class this codebase has spent an arc
removing.** The in-source comment at `dashboard_manager.py:3117-3120` names it: *"Deliberately NOT a
second `allow_duplicate` writer … keeps exactly one, per the F-CANOPY-018 / F-CANOPY-027 two-writer
class this arc has been removing."* `gate_dataset_options` (`:2605`) owns that Output today. The
obvious implementation of C — hang `Output("nn-dataset-type-dropdown","value", allow_duplicate=True)`
off `select_model` — reintroduces the class into the one feature that is already broken, and it will
pass every per-render test.

My mitigation (the `pending-dataset-store` indirection, step 4) is sound, but it is a *discipline*, not
a *mechanism*: nothing structural stops a later contributor from adding the duplicate writer. That is
why **INV-6 (exactly one owning callback for `nn-dataset-type-dropdown.value`, asserted against
`app.callback_map`) is not optional for C** — it is the thing that converts my discipline into a gate.
If the team is not willing to land INV-6, ship P1-A alone and defer C; A does not touch that Output at
all beyond the existing owner.

---

## 6. The guardrail that would have caught this (and the suite around it)

The pinning tests are not wrong. `test_model_table.py:134-135` and `:143-144` correctly assert what a
*single render* does. **The defect does not exist in any single render.** It exists in the closure over
renders — which no test in the repo takes. That is the transferable lesson, and it generalises well
beyond this feature: *when two controls gate each other, per-control tests are structurally incapable
of finding a deadlock.*

### INV-1 — reachability closure (the one that catches it)

> From the seeded default state, the set of `(model, dataset)` pairs reachable through the UI's own
> transition functions **must contain every pair for which `compatible(dataset, model)` is true.**

Implement as a pure BFS (browser-free, so it fits the design's B0 gate) over exactly three moves:
non-`disabled` options from `gated_dataset_options(model)`; enabled Select controls from
`_build_model_selection_table(dataset, model)`; and the post-selection snap from
`_gate_dataset_options_handler`. Seed at `(DEFAULT_MODEL_KEY, DEFAULT_DATASET_TYPE)`. Assert
`compatible_pairs - reachable == set()`.

Two properties make it worth the effort:

1. It fails **today**, on the shipped seeds, naming `('recurrence','equities_seq')` — so it is
   verifiable against a known-bad baseline rather than being aspirational.
2. It is **mechanism-agnostic** — the same test passes under A, B, C or D, so it is a permanent
   invariant rather than a pin on one implementation.

**Run it as a property test over generated registries with 2, 3 and 4 partition components, not only
the shipped seeds.** With today's two-component partition a naive implementation of any proposal
passes; the 3-component case is where "snap to first enabled" and "one resolution in the dialog" break.
Generate: N models with random `input_ndim`/`temporal`/`task_type` draws, M datasets, assert the
closure covers the compatible relation.

### The rest of the suite

| ID | Invariant | Catches |
|---|---|---|
| **INV-2** | Every rendered gated control offers ≥1 enabled option, **or** a clear affordance exists. | Dead-end controls in general — the class, not this instance. |
| **INV-3** | For every incompatible item, the reason appears in the accessible **name/description of a focusable control**; and **no** component conveys a reason via `title=` alone. | A11Y-1, A11Y-2; retires the dead `title=` at `:3051`. |
| **INV-4** | Any handler that changes `nn-dataset-type-dropdown.value` returns non-empty `role="status"` notice children in the same call. | A11Y-4; B's "shipped step 1, forgot the notice" failure. |
| **INV-5** | An option disabled for **availability** stays disabled on every path; `reason_class` distinguishes negotiable (incompatible) from non-negotiable (unavailable). | D's composition trap; conflating two disable classes with different resolutions. |
| **INV-6** | `Output("nn-dataset-type-dropdown","value")` has exactly one owning callback in `app.callback_map`. | The F-CANOPY-018/027 two-writer class; C's strongest objection. |
| **INV-7** | `compatible(get_dataset_spec(DEFAULT_DATASET_TYPE), get_model_spec(DEFAULT_MODEL_KEY))` is true (FR11). | A registry reorder — both defaults are `[0]`-element conventions (`model_registry.py:153`, `:197`) — silently shipping an incompatible default pair. |

---

## 7. Separate defects found along the way

Flagged, **not** folded into any proposal.

### D-1 — `restart-ds-type` is permanently gated to `cascor` (`dashboard_manager.py:5422`)

Its `options` are `gated_dataset_options(DEFAULT_MODEL_KEY)`, built once at layout-build time; **no
callback ever writes `restart-ds-type.options`** (all six repo-wide references confirmed: `:490`,
`:5268` writes `.value`, `:5315` reads `.value`, `:5366` reads `.value` as State, `:5421` label,
`:5422` construction). Meanwhile `:5268` **populates its value on open from the sidebar's current
dataset** (`:5285`, State on `nn-dataset-type-dropdown`).

Consequences, all currently **masked by the deadlock this document is about**:

- Once `(recurrence, equities_seq)` is reachable, the restart modal renders a `clearable=False`
  dropdown whose selected value `equities_seq` is one of its own **`disabled`** options — a control
  displaying a value it simultaneously declares invalid. There is no way to change it and no way to
  clear it.
- It never receives the `apply_availability_gate` composition either, so an unavailable generator is
  offered here while being correctly greyed in the sidebar.

**This is the "a broken thing masks the next one" pattern: fixing the deadlock EXPOSES D-1.** Whichever
proposal ships must fix or explicitly quarantine `restart-ds-type` in the same PR, or the first user to
reach the LMU pair will hit a worse control than the one we set out to fix.

### D-2 — FR15 is unimplemented: no hydration of the selected model from backend state

There is **no `GET /api/model/*` route** — `main.py` has only `@app.post("/api/model/select")`
(`:3731`). `model-selection-store` is seeded statically to `DEFAULT_MODEL_KEY` (`:1842`), while the
authoritative selection lives in the process-global `current_nn_model` (`main.py:485`, written at
`:3707` and `:3723`). So after a model swap, **a browser reload shows "Active: CasCor" while the
backend is running recurrence** — and worse, the mount-time `gate_dataset_options` pass then re-gates
against `cascor` and **silently snaps the dataset**. Two browser tabs desync the same way. FR15
explicitly requires *"initialise from current backend state, re-validate against the registry, fall
back to the first compatible pair with a notice if stale"* — none of which exists.

### D-3 — `title=` at `:3051` is a dead accessibility channel that reads as a live one

Detailed in A11Y-1. Not the deadlock, but it makes the reason *look* conveyed in code review while
conveying it to nobody, and it contradicts the design's own §8. Delete it in whichever PR ships;
INV-3's negative assertion keeps it deleted.

### D-4 (observation, not a defect) — `POST /api/model/select` does not validate the pair

`_ModelSelectBody` carries only `nn_model`; the route validates registry membership and swaps
(`main.py:3731-3743`). This is **by design** (D5 + §5.9/FR9: the *target model service* fails closed on
shape), and it is what makes P1-B/C/D safe. Recording it because every proposal that permits a
transient incompatible pair is relying on FR9 being real **in the recurrence service** — which is
outside this repo and which I did **not** verify. Someone should.

### D-5 — the deployment-availability gate can independently hide `equities_seq`

`apply_availability_gate` (`dataset_schema.py:267`) disables any dataset whose juniper-data generator
reports `available: false`, with reason `"unavailable in this deployment"`
(`_UNAVAILABLE_REASON_DEFAULT`, `:110`). So **even after the deadlock is fixed, the LMU pair may remain
unreachable for an entirely different reason, with entirely different (and correct) messaging.** Any
verification of a fix must assert the availability gate is not the thing under test, and any proposal
must keep the two disable classes distinguishable (INV-5).
