# Lane A verifier A2 — measurement re-creation

**Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (juniper-ml)
**Repo under test**: `/home/pcalnon/Development/python/Juniper/juniper-canopy` @ `30e15b7` (main, clean tree)
**Entry point**: the test suite read as a specification. Production code consulted only to (a) confirm
the predicate the asserted `disabled` flag is computed from, and (b) close the escape-hatch search.
**Date**: 2026-09-02

---

## 1. Verdict

**CLAIM CONFIRMED, both halves.**

1. From the default state `(model=cascor, dataset=spirals)` the pair `(recurrence, equities_seq)` is
   **unreachable** through the selection UI. Independently measured (§3), not inferred from prose.
2. The existing suite **actively pins both blocking edges** with positive `is True` assertions, at the
   exact default state. It does not merely permit the deadlock — for the two controls that exist, it
   **mandates** it (§5). All 129 tests over the eight selection-relevant files pass today (§7).

Additional, not in the claim but material:

3. **No test anywhere proves reachability.** Every test that touches the `(recurrence, equities_seq)`
   pair hand-feeds it to a handler body, bypassing the gates. There is no test that composes the two
   gates in one flow (§6). This is an instrument-adequacy gap, not merely a missing test.
4. **The two tests that *look* like escape hatches exercise UI states that cannot be entered.**
   `test_model_table.py:170-179` covers "no dataset" and "unknown dataset" → all models selectable.
   Neither is reachable: the dropdown is `clearable=False` and its options are the fixed registry list
   (`dashboard_manager.py:1330-1337`). Those two green tests describe dead UI states.

---

## 2. The contract, derived from assertions alone

### (a) Which dataset options are disabled, given a model

| Assertion | Model | Verdict encoded |
|---|---|---|
| `test_model_registry.py:416-418` | `cascor` | spirals/xor/mnist/circles/moons carry **no** `disabled` key |
| `test_model_registry.py:419` | `cascor` | `equities_seq` `disabled is True` |
| `test_model_registry.py:420` | `cascor` | label is `"Equities (sequence) — needs a 3-D model"` |
| `test_model_registry.py:408` | `recurrence` | `equities_seq` is the plain 2-key option (selectable) |
| `test_model_registry.py:410-411` | `recurrence` | `spirals` `disabled is True`, label `"Spirals — needs a 2-D model"` |
| `test_model_registry.py:425-426` | unknown key | **all** options plain (fail-open on desync) |
| `test_n7_dataset_panel.py:141` | `cascor` (handler, + availability gate) | `equities_seq` `disabled is True` — *"model-incompat gate preserved"* |
| `test_n7_dataset_panel.py:142` / `test_model_picker.py:101` | `cascor`, current `spirals` | `value is dash.no_update` — no snap |
| `test_model_picker.py:94-96` | `recurrence`, current `spirals` | spirals disabled; `equities_seq` plain; **value snaps to `equities_seq`** (D5) |
| `test_model_picker.py:105` / `test_n7_dataset_panel.py:155` | `""` | `(no_update, no_update)` — no model ⇒ no dropdown write |

### (b) Which model Select buttons are disabled, given a dataset

| Assertion | Dataset | Verdict encoded |
|---|---|---|
| `test_model_table.py:134` | `spirals` | `cascor` Select `disabled is False` |
| `test_model_table.py:135` | `spirals` | **`recurrence` Select `disabled is True`** |
| `test_model_table.py:143` | `equities_seq` | `recurrence` Select `disabled is False` |
| `test_model_table.py:144` | `equities_seq` | `cascor` Select `disabled is True` |
| `test_model_table.py:201` | `equities_seq` (via modal-open handler) | `cascor` Select `disabled is True` |
| `test_model_table.py:158` | `equities_seq` | a *compatible but non-live* model stays selectable — lifecycle is a separate axis |
| `test_model_table.py:173` | `None` | all Select buttons enabled |
| `test_model_table.py:179` | `"does-not-exist"` | all Select buttons enabled |

### (c) The underlying compatibility relation the two gates read

| Assertion | Fact |
|---|---|
| `test_model_registry.py:105` | `cascor.input_ndim == frozenset({2})` |
| `test_model_registry.py:114` | `recurrence.input_ndim == frozenset({3})` |
| `test_model_registry.py:69` | all five 2-D seeds are `ndim=2, classification, temporal="none"` |
| `test_model_registry.py:72` | `equities_seq` is `ndim=3, regression, temporal="irregular"` |
| `test_model_registry.py:165` | `compatible(spirals, recurrence) is False` |
| `test_model_registry.py:199` | `compatible_models(spirals) == [cascor]` |
| `test_model_registry.py:207` | `compatible_datasets(cascor) == [spirals, xor, mnist, circles, moons]` |
| `test_model_registry.py:209` | `compatible_datasets(recurrence) == [equities_seq]` |
| `test_model_registry.py:361-367` | `model_reason(m, d) is None` ⟺ `compatible(d, m)` for **every** seed pair |

**Consequence.** The compatibility bipartite graph the tests pin has **two disjoint components** with
no shared node: `{cascor} × {spirals, xor, mnist, circles, moons}` and `{recurrence} × {equities_seq}`.
Both gates disable exactly the cross-component edges. The state graph therefore inherits the same
partition, and `(cascor, spirals)` and `(recurrence, equities_seq)` sit in different components.

---

## 3. Independent reachability measurement

Instrument: `juniper-ml/util/ad-hoc/2026-09-02_canopy_model_dataset_reachability_probe.py` (written for
this lane; imports only `juniper-canopy/src/model_registry.py`, does not read `dashboard_manager`'s
callbacks, does not read the tests). It builds the transition relation from the two registry primitives
the UI renders from and BFS's the state graph from `(DEFAULT_MODEL_KEY, DEFAULT_DATASET_TYPE)`.

Command:

```
conda run -n JuniperCanopy1 --no-capture-output python \
  /home/pcalnon/.../util/ad-hoc/2026-09-02_canopy_model_dataset_reachability_probe.py
```

Output (verbatim):

```
registry models   : ['cascor', 'recurrence']
registry datasets : ['spirals', 'xor', 'mnist', 'circles', 'moons', 'equities_seq']
default state     : ('cascor', 'spirals')
target state      : ('recurrence', 'equities_seq')

reachable states from default (5):
    ('cascor', 'circles')
    ('cascor', 'mnist')
    ('cascor', 'moons')
    ('cascor', 'spirals')
    ('cascor', 'xor')

target reachable  : False
target is a legal (compatible) pair: True

blocking edges out of the default state:
    dataset->equities_seq  disabled=True  label='Equities (sequence) — needs a 3-D model'
    model->recurrence      model_reason(recurrence, spirals) = 'needs 3-D data'  (non-None => Select disabled)
```

**Reachable set = 5 of 12 states. The target is a legal, compatible pair that the UI cannot navigate to.**

---

## 4. Escape hatches searched and closed

| Candidate escape | Status | Evidence |
|---|---|---|
| The D5 snap (`_gate_dataset_options_handler` moves a stranded dataset value) | **Inert.** It fires only on a model change; the model can never change. | `test_model_picker.py:96`; `dashboard_manager.py:2705-2706` |
| Clear the dataset → all models selectable (`test_model_table.py:173`) | **Unreachable.** Dropdown is `clearable=False`. | `dashboard_manager.py:1334` |
| Stale/unknown dataset value → all models selectable (`test_model_table.py:179`) | **Unreachable.** Options are the fixed registry list. | `dashboard_manager.py:1332` |
| Unknown model key → all datasets ungated (`test_model_registry.py:425`) | **Unreachable.** Store is seeded to `DEFAULT_MODEL_KEY`. | `dashboard_manager.py:1842` |
| A mount-time race before the gate callback runs | **None.** The layout seeds the dropdown with `gated_dataset_options(DEFAULT_MODEL_KEY)` — the gate is applied at first paint, not only by the callback. | `dashboard_manager.py:1332` |
| A second writer to `model-selection-store` | **None.** Sole `Output` is `select_model`, driven by the pattern-matched Select buttons. | `dashboard_manager.py:2588-2598` |
| A second writer to `nn-dataset-type-dropdown.value` | **None.** Sole `Output` is `gate_dataset_options`. | `dashboard_manager.py:2605-2612` |
| The API route `POST /api/model/select` | **Works, and is not the UI.** Accepts `recurrence` with HTTP 200 regardless of config. Reaching it requires curl, not the dashboard. | `test_d8_d11_phase4_truth_up.py:74-82`; `test_model_select.py:129-142` |

Corroborating (UI copy, not evidence): the §5.8 degenerate-state recovery alert tells the user to
*"switch the dataset in the sidebar"* (`dashboard_manager.py:3072`, pinned by `test_model_table.py:257`).
That is exactly the move the dataset gate forbids.

---

## 5. MANDATE / PERMIT / SILENT

**MANDATE**, with one precise caveat.

- The tests do not merely fail to forbid the deadlock. They assert **both** blocking edges out of the
  default state with positive `is True` assertions: `test_n7_dataset_panel.py:141` (and
  `test_model_registry.py:419`) forbid the dataset move; `test_model_table.py:135` forbids the model move.
- Therefore **any fix that unblocks either of the two existing controls necessarily turns a currently
  green assertion red.** The defect is protected by green tests.
- Caveat, stated for precision: a fix that leaves both existing gates untouched and adds a *third*
  control (e.g. a combined "model + its dataset" chooser, or a "reset to a compatible pair" action)
  would break nothing. So the mandate binds *the existing controls*, not the abstract goal of
  reachability. This distinction should be preserved in the consensus record — it is the difference
  between "the tests forbid the fix" (false) and "the tests forbid fixing the gates" (true).

---

## 6. REQUIRED CRITICAL CHECK — instrument adequacy

**Is there any test that asserts `(recurrence, equities_seq)` is reachable, or exercises an end-to-end
selection flow reaching it?**

**No. Answer: NO ARTIFACT.** Searched exhaustively:

- `grep -rn "equities_seq" src/tests/` (excluding `reports/`) — 79 hits across 8 files. Every hit is one
  of: a registry-level fact, a backend/adapter call, an assertion that the pair is **blocked**, or a
  handler body **hand-fed** the pair.
- `grep -rl "playwright\|e2e" src/tests/ tests/` — the Playwright subsuite is `src/tests/ui/` (14 files).
  **Zero** hits for `recurrence` or `equities` anywhere in it. It covers dataset-apply, sidebar width,
  numeric input, WS liveness, train-after-reset. No model-selection coverage at all.
- `@pytest.mark.e2e` — 5 usages, none related (`test_parameter_persistence.py:226`,
  `test_candidate_visibility.py:14`, `test_demo_endpoints.py:92,106,291`).
- No test file calls `_gate_dataset_options_handler` **and** any of
  `_select_model_from_table_handler` / `_select_model_handler` / `_build_model_selection_table`.
  The two gates are **never composed in a single test.** The composition is where the defect lives.

The two closest things to a reachability proof, and why neither is one:

| Test | What it does | Why it is not a reachability proof |
|---|---|---|
| `test_oneshot_start_body.py:205-216` (`TestOneshotBodyReachesAdapterEndToEnd`) — labelled *"end-to-end tie-through"* | Calls `_resolve_oneshot_start_body_handler("one_shot", "equities_seq")` and round-trips it through `POST /api/train/start` to the recurrence adapter | The pair is a **literal argument**. It proves the pair *works once you hold it*; it never asks whether the UI can produce it. This is the canonical vacuous-pass shape: the strongest-sounding test in the file is the one that assumes away the defect. |
| `test_model_picker.py:56` | `manager._select_model_handler("recurrence")` → store becomes `"recurrence"` | Invokes the handler body directly, bypassing the disabled Select button that is the actual gate. |
| `test_d8_d11_phase4_truth_up.py:74-82` | `POST /api/model/select {"nn_model": "recurrence"}` → 200 | An HTTP route, not the UI. It even asserts `body["backend"] != "recurrence"` in the unconfigured case — i.e. it pins that a *successful selection can leave the wrong backend live*. Adjacent defect, not a refutation. |

**The claim is not refuted.** The suite's coverage of this surface is per-gate and never end-to-end, so
it is structurally incapable of catching the composition failure.

Note on scope: `pyproject.toml:351` puts `--ignore=src/tests/ui` in `addopts`, so the Playwright subsuite
does not run in the default invocation at all (it runs as a separate CI job, `ci.yml:399-412`, restricted
to `-m "ui and not slow"`). Even if a UI reachability test existed, it would need that marker to run.

---

## 7. Test run

Environment: **`JuniperCanopy1`** (`JuniperCanopy` is renamed `JuniperCanopy-DEPRECATED`; discovered via
`conda env list | grep -i canopy` before the first run — the brief's env name was already corrected).
No plugin-autoload guard was needed: no segfault, no hang, no `PYTEST_DISABLE_PLUGIN_AUTOLOAD`
convention exists in this repo's `AGENTS.md`, `conftest.py`, or `pyproject.toml`.

Exact command (run from `juniper-canopy/src`, per `AGENTS.md` § Testing):

```
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda run -n JuniperCanopy1 --no-capture-output python -m pytest \
  tests/regression/test_model_table.py \
  tests/regression/test_model_picker.py \
  tests/regression/test_model_select.py \
  tests/regression/test_oneshot_start_body.py \
  tests/unit/test_model_registry.py \
  tests/unit/test_dataset_schema.py \
  tests/unit/frontend/test_n7_dataset_panel.py \
  tests/regression/test_d8_d11_phase4_truth_up.py -v
```

Result:

```
collected 129 items

tests/regression/test_model_table.py .........................           [ 19%]
tests/regression/test_model_picker.py ........                           [ 25%]
tests/regression/test_model_select.py ........                           [ 31%]
tests/regression/test_oneshot_start_body.py .........                    [ 38%]
tests/unit/test_model_registry.py ......................................
.....                                                                    [ 72%]
tests/unit/test_dataset_schema.py .............                          [ 82%]
tests/unit/frontend/test_n7_dataset_panel.py .................           [ 95%]
tests/regression/test_d8_d11_phase4_truth_up.py ......                   [100%]

============================= 129 passed in 10.69s =============================
```

`pytest exit=0`. **129 passed, 0 failed, 0 errors.** The defect is fully protected by green tests.

---

## 8. DELIVERABLE — assertions a fix must change

The table builder computes `disabled=not is_compatible` where
`is_compatible = model_reason(model, dataset) is None` (`dashboard_manager.py:3033-3046`), so the
`disabled` assertions below are assertions about the compatibility gate itself, not about rendering.

### 8.1 Minimal fix — unblock Edge B only (make the recurrence Select clickable at a 2-D dataset; the existing D5 snap then moves the dataset to `equities_seq` on its own)

Exactly **three** assertions break:

| # | file:line | assertion text |
|---|---|---|
| 1 | `src/tests/regression/test_model_table.py:135` | `assert _button_for(table, "recurrence").disabled is True` |
| 2 | `src/tests/regression/test_model_table.py:144` | `assert _button_for(table, "cascor").disabled is True` |
| 3 | `src/tests/regression/test_model_table.py:201` | `assert _button_for(children, "cascor").disabled is True  # 2-D model vs the 3-D dataset` |

(#2 and #3 break because any un-greying rule is symmetric across the two components.)

Enclosing tests: `test_table_greys_incompatible_models_against_2d_dataset` (:131),
`test_table_greys_incompatible_models_against_3d_dataset` (:140),
`test_toggle_opens_and_builds_table_against_current_dataset` (:196).

**Conditionally affected** (break only if the fix redefines "compatible" for the degenerate-set count
at `dashboard_manager.py:3034`, i.e. if un-greying also makes `compatible_count` non-zero):

| # | file:line | assertion text |
|---|---|---|
| 4 | `src/tests/regression/test_model_table.py:255` | `assert type(result).__name__ == "Div"  # alert + table wrapper` |
| 5 | `src/tests/regression/test_model_table.py:256` | `assert _has_id(result, "model-selection-empty-alert")` |
| 6 | `src/tests/regression/test_model_table.py:257` | `assert "No compatible model" in _all_text(result)` |
| 7 | `src/tests/regression/test_model_table.py:265` | `assert not _has_id(result, "model-selection-empty-alert")` |

### 8.2 Alternative fix — unblock Edge A instead (let `equities_seq` be selectable while `cascor` is active, then snap the model)

| # | file:line | assertion text |
|---|---|---|
| 1 | `src/tests/unit/test_model_registry.py:419` | `assert by_value["equities_seq"]["disabled"] is True` |
| 2 | `src/tests/unit/test_model_registry.py:420` | `assert by_value["equities_seq"]["label"] == "Equities (sequence) — needs a 3-D model"` |
| 3 | `src/tests/unit/frontend/test_n7_dataset_panel.py:141` | `assert by_value["equities_seq"]["disabled"] is True  # model-incompat gate preserved` |
| 4 | `src/tests/unit/test_model_registry.py:410` | `assert by_value["spirals"]["disabled"] is True` (symmetric) |
| 5 | `src/tests/unit/test_model_registry.py:411` | `assert by_value["spirals"]["label"] == "Spirals — needs a 2-D model"` (symmetric) |

Enclosing tests: `test_gated_dataset_options_all_plain_for_cascor_then_3d_greyed`
(`test_model_registry.py:414`), `test_gate_composes_availability_over_model_options`
(`test_n7_dataset_panel.py:134`), `test_gated_dataset_options_greys_incompatible_for_recurrence`
(`test_model_registry.py:405`).

Note `test_model_picker.py:96` (`assert value == "equities_seq"`) **survives** either fix — under 8.1 it
becomes the mechanism that *completes* the transition, and it is already green.

### 8.3 Assertions a fix must NOT change (guard-rail)

The compatibility *facts* are correct; only the *navigation* is broken. A fix that edits
`compatible()` / `input_ndim` to make the pair navigable would be wrong and would break, at minimum:
`test_model_registry.py:105, 114, 165, 199, 207, 209, 311, 323, 325, 349, 351, 365-367`.

### 8.4 Coverage a fix should add (currently absent)

There is no test that composes the two gates. A fix should add at least one that starts at
`(DEFAULT_MODEL_KEY, DEFAULT_DATASET_TYPE)` and drives the real handlers — not the handler bodies with
hand-fed arguments — to `(recurrence, equities_seq)`. Without it, the fix would itself be unguarded,
and `test_oneshot_start_body.py:205-216` would continue to read as an "end-to-end" proof that it is not.

---

## 9. Artifacts

- Probe: `juniper-ml/util/ad-hoc/2026-09-02_canopy_model_dataset_reachability_probe.py`
- Raw pytest output: `<scratchpad>/pytest_v.txt`, `<scratchpad>/pytest_out.txt`
- No file in `juniper-canopy` was modified (verified clean tree at start; only reads and pytest runs performed).
