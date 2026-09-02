# Lane B — adversarial reviewer B3

**Lenses**: FALSE AUTHORITY · CONVENIENT CONCLUSIONS · MIS-SIZING
**Brief**: refute. A finding that the work is sound is worth nothing.
**Procedure**: `juniper-ml/notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane B
**Entry point**: the anchors themselves + `git log -S` archaeology on `juniper-canopy`. I did **not** read
`laneA*.md` or `proposal_P*.md` in the shared scratchpad, to keep the entry point independent.

---

## 0. What survived

The **core observation is CONFIRMED and I could not break it.** Re-derived from the artifacts, not the prose:

```
gated_dataset_options("cascor")     -> equities_seq disabled=True
gated_dataset_options("recurrence") -> spirals..moons disabled=True
model_reason(recurrence, spirals)   -> "needs 3-D data"  => Select disabled at :3050
```
(`conda run -n JuniperCanopy1`, `sys.path.insert(0,"src")`, 2026-09-02.)

From the mount state (`cascor`, `spirals`) there is **no transition** to `(recurrence, equities_seq)`.
6 compatible pairs exist; 5 reachable. Every anchor in the brief verified:

| anchor | verified |
|---|---|
| `dashboard_manager.py:1334` `clearable=False` | ✓ (dropdown block 1330-1337) |
| `:1842` `model-selection-store` seeded `DEFAULT_MODEL_KEY` | ✓ |
| `:2702-2706` snap in `_gate_dataset_options_handler` | ✓ |
| `:3050` `disabled=not is_compatible` | ✓ |
| `:5422` `restart-ds-type` built against `DEFAULT_MODEL_KEY` | ✓ |
| `model_registry.gated_dataset_options` | ✓ |

Everything below is where the round is wrong.

---

## 1. ROOT CAUSE — **REFUTED.** It is a merged-PR regression, not an unshipped design decision.

The round's story: D4's inline ✕ was "specified but never shipped", and that omission is the root cause.
That story is **factually true and causally false**, and it is the single most convenient framing available:
it blames an absence, exonerates every reviewer, and makes the fix small.

### 1a. `clearable=False` predates the design that specified D4 by five weeks

`git show 13a5856:src/frontend/dashboard_manager.py` (2026-05-10, "Apply Dataset UI … Issue #3 Phase 1, PR-7"):

```python
dcc.Dropdown(id="nn-dataset-type-dropdown", options=[...5 inline 2-D types...],
             value="spirals", clearable=False, ...)
```

The design of record (`juniper-ml/notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`
line 54, D4; FR6 line 73; §5.5 line 154) is dated **2026-06-17**. So D4 was not *dropped during
implementation*; it was a **proposal to change a property an existing control already had**, and every
later PR on that control declared itself behaviour-preserving. The A0 commit (`9d1274b`) says so in
`model_registry.py`'s header: *"Behavior-preserving: dataset_type_options() reproduces the previously
inlined dropdown options exactly … DEFAULT_DATASET_TYPE preserves the prior value='spirals' default."*
The behaviour-preservation discipline that protected the refactor is the mechanism that carried
`clearable=False` forward unexamined. That is a different — and more useful — root cause.

### 1b. The deadlock was CREATED by canopy PR #397, and it did not exist before it

This is the decisive artifact. Immediately before `442673e` ("A1b-1 dedicated model-selection modal
surface (#368) (#397)"), the model input was an **ungated dropdown**:

```
$ git show f464272:src/frontend/dashboard_manager.py | grep -A7 'id="nn-model-dropdown"'
    dcc.Dropdown(id="nn-model-dropdown", options=model_options(), value=DEFAULT_MODEL_KEY,
                 clearable=False, ...)
$ git show f464272:... | grep -c 'model-select-btn'   -> 0
$ git show 442673e:... | grep -c 'model-select-btn'   -> 4
$ git show 442673e:... | grep -c 'nn-model-dropdown'  -> 1   (a comment)
```

`model_options()` applies **no** compatibility filter (`model_registry.py:227`). Any model was selectable
at any time; the dataset gate then snapped the dataset. **`(recurrence, equities_seq)` was reachable at
`f464272` and unreachable at `442673e`.** The pair was lost to a merged feature PR, not to an omission.

### 1c. The PR that broke it certified the property it broke

`dashboard_manager.py:2584-2590`, written by #397:

> "…REPLACING the old nn-model-dropdown Input. … Downstream gates are insulated — `gate_dataset_options`
> keys off `model-selection-store` and `resolve_oneshot_start_body` off `model-class-store`, **NOT** the
> input control — so **swapping the input side leaves every downstream gate intact**."

The claim is true and irrelevant. The regression is not downstream; #397 added a **new upstream gate**
(`disabled=not is_compatible`) that the dropdown never had. This comment is a textbook FALSE-AUTHORITY
artifact: it reads as a safety argument and audits the wrong axis. Any round that quotes it as evidence
the swap was safe has been captured by it.

### 1d. The counter-hypothesis in the brief (#400 flipped live without exercise) is HALF right

`a96a114` (#400) flipped `recurrence` `coming_soon → live` — **after** #397. At #397's merge, recurrence
was still `coming_soon` (`git show f464272:src/model_registry.py:177 status="coming_soon"`), so the pair
was *selectable but not trainable*, and nobody had reason to try it. #400 made it trainable but by then
#397 had already removed the only selection path. **Both** commits are load-bearing: #397 removed
reachability, #400 removed the last reason anyone would have noticed. Neither is D4.

### 1e. Was D4 deliberately dropped for a good reason? — **NO ARTIFACT for deliberateness; a real reason exists latently**

I found no PR, issue, or note giving a rationale. But clearing the dataset is genuinely hazardous today,
and nobody wrote it down:
- `_build_model_selection_table(None, …)` (`:3033`) makes **every** model's Select enabled when
  `dataset is None` — including `cascor` + a subsequently-picked 3-D dataset.
- `_resolve_oneshot_start_body_handler` returns `None` on a falsy generator (`:2678`) → the one-shot
  Start silently loses its dataset ref → `RecurrenceBackend.start_training` returns
  `"no dataset reference"` (`recurrence_backend.py:139`).
- `_apply_dataset_handler` would post a body with no `nn_dataset_type`.

So D4-as-written is not a free 1-line fix either. Recommending "restore D4" without these three guards
would ship a second defect.

### 1e-bis. Somebody DID notice the missing ✕ — and reworded the copy instead of filing it

This is the strongest single artifact against "an omission nobody spotted." The design's §5.8 specifies
the empty-compatible-set recovery text as:

> *"no trainable model for this dataset yet — **clear the dataset**, or see *coming soon* models"*
> (`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` §5.8, lines 181-183)

The shipped alert (`dashboard_manager.py:3070-3074`) reads:

> *"No compatible model. No model can train the selected dataset yet — **switch the dataset in the
> sidebar**, or choose a model that supports it once one is available."*

The recovery instruction was **rewritten to avoid the affordance that was never built**. Whoever wrote
that string knew "clear the dataset" was not available and routed around it. So the round's framing —
a decision quietly lost between design and code — is not what happened; the gap was seen at the copy
level and absorbed. That is a review-process finding, and it is the opposite of flattering.

Related, and also unshipped: §5.8 FR15 — *"Default / reload: initialise from current backend state,
re-validate against the registry."* `model-selection-store` is hardcoded `data=DEFAULT_MODEL_KEY`
(`:1842`) and `main.py` boots `create_backend(service_url=…)` with no `nn_model` (`main.py:304`), so the
store never initialises from, or re-syncs with, the backend. This is the same root as §3c.

Note also §5.7: *"`coming_soon` and `experimental` models are **shown, selectable for inspection**, but
Train-disabled."* The design's own text says the model control is **selectable** and the *Train* control
is the gate. `:3050` disabling **Select** is a deviation from §5.7 as well as from D5.

### 1f. Two documents, two "D4"s

`juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md` line 207 has its
own **"D4 — Recurrence image — DONE"**. A summary that says "D4's inline ✕" without naming the document
is ambiguous across two documents in the same arc — exactly the failure the ecosystem's
"name the document in every summary reference" convention (`Juniper/AGENTS.md` § Cross-Project
Conventions) exists to prevent. Fix the citation before this lands in a document of record.

---

## 2. SIZING — **REFUTED. "~20 lines / 2-3 test assertions" is undersized by ~3-4× on source and ~10× on tests.**

Convergence of four agents on a small number is not evidence (§2 Lane A). Costed independently:

### 2a. Tests that must CHANGE (not be added) — 6 assertions minimum, in 5 named tests

`src/tests/regression/test_model_table.py`:

| line | test | effect of a unary `:3050` |
|---|---|---|
| 131-135 | `test_table_greys_incompatible_models_against_2d_dataset` — `assert _button_for(table,"recurrence").disabled is True` | **MUST INVERT** |
| 140-144 | `test_table_greys_incompatible_models_against_3d_dataset` — `assert _button_for(table,"cascor").disabled is True` | **MUST INVERT** |
| 148-158 | `test_table_option_a_non_live_stays_selectable_when_compatible` — premise is "only *incompatible* is disabled" | **premise destroyed**; rewrite or delete |
| 170-173 | `test_table_without_a_dataset_treats_all_models_as_compatible` | still green, now **VACUOUS** |
| 176-179 | `test_table_unknown_dataset_value_treats_all_models_as_compatible` | still green, now **VACUOUS** |
| 196-201 | `test_toggle_opens_and_builds_table_against_current_dataset` — `assert _button_for(children,"cascor").disabled is True` | **MUST INVERT**, and the test loses its only observable (needs re-anchoring on the compatibility *cell*, not the button) |

Plus the module docstring at lines 14 and 27-29, which states the contract in prose.

Counted precisely: **4 assertion inversions**, **3 tests rendered vacuous** (rows 4, 5, and 6 — row 6
would pass for *any* dataset argument once the button is always enabled, so it needs re-anchoring on the
`"needs 2-D data"` cell text or it stops testing the thing its name claims), **1 test whose premise no
longer exists** (row 3 — it exists solely to distinguish compat-greying from lifecycle-greying; with a
unary Select there is no compat-greying left to distinguish), and **4 signature/arity breaks** (§2b).
That is **11 test sites across 2 files before a single new test is written** — against an estimate of
"2-3 test assertions".

Note also row 4's own comment: *"No dataset selected (e.g. cleared)"* — the suite already contemplates a
cleared dataset that `clearable=False` makes unreachable. Second independent trace of the D4 gap being
seen and left (cf. §1e-bis).

### 2b. Tests that break on **arity**, which the round did not price

The recommended notice needs a third Output on `gate_dataset_options`. Three tests in
`src/tests/regression/test_model_picker.py` unpack the handler as a 2-tuple and break on the signature,
not the behaviour:
- `:91` `test_gate_dataset_options_handler_greys_and_snaps_for_recurrence`
- `:99` `test_gate_dataset_options_handler_keeps_compatible_value`
- `:104` `test_gate_dataset_options_handler_noop_without_model` (`== (dash.no_update, dash.no_update)`)

Same class for the Start-gate (§2d): `update_button_appearance` is a **10-Output** callback with exactly
two Inputs (`dashboard_manager.py:4472-4481`); adding a dataset factor changes
`_update_button_appearance_handler(button_states, model_key)` and breaks
`test_model_table.py:294 test_update_button_appearance_force_disables_start_for_non_live`.

### 2c. The **blocking** per-file coverage gate

`.github/workflows/ci.yml:255-261` runs `juniper-coverage-gap-map --enforce` from
`juniper-ci-tools>=0.8.0,<0.9.0`. Thresholds re-derived from source, not from the comment:
`juniper-ci-tools/juniper_ci_tools/coverage_gap_mapper.py:91-92`
→ `DEFAULT_FILE_THRESHOLD = 90.0`, `DEFAULT_SUBMODULE_BAR = 95.0`.
Scope: **every** file measured by the unit lane (`pytest src/tests/unit/ src/tests/regression/`,
`--cov=src`), with `[tool.coverage.run] omit` covering only tests/conftest/venv (`pyproject.toml:396-413`).
So `src/frontend/dashboard_manager.py` (7,967 lines) is inside the gate, and **every new branch must be
covered or CI fails**.

The tax is already visible in the tree — `dashboard_manager.py` alone carries **1,455 lines** of
dedicated gate-coverage suites:

```
src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py    634
src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner2.py    369
src/tests/unit/frontend/test_dashboard_manager_gate_coverage_handlers.py  452
```

Any **new file** would need ≥90 % on its own, and its sub-module ≥95 % pooled.

#### MEASURED — and this partly REFUTES my own framing above. Recorded as a correction.

I ran the real lane (`pytest -m "not requires_cascor and not requires_server and not slow"
`src/tests/unit/ src/tests/regression/ --cov=src --cov-report=json`, `JuniperCanopy1`, Python 3.13,
`-p no:randomly`; exit 0, total **96.06 %**) and fed the JSON to the actual gate
(`juniper_ci_tools.coverage_gap_mapper.load_coverage_json`, 66 files parsed):

```
files below the 90 % FILE floor:            []      <- gate currently clean
sub-modules below the 95 % POOLED bar:      []      <- gate currently clean

src/frontend/dashboard_manager.py   96.13 %   1756 stmts, 68 missing
src/model_registry.py              100.00 %     90 stmts,  0 missing
src/dataset_schema.py               95.28 %    106 stmts,  5 missing
src/backend/recurrence_backend.py   93.62 %    141 stmts,  9 missing
```

**Correction to my own argument:** the *per-file* 90 % floor is **not** the binding constraint.
`dashboard_manager.py` at 96.13 % could absorb ~**119** entirely-uncovered new statements before
breaching 90 %. My §2c framing over-weighted it, and a Lane B pass that buried a disconfirming
measurement would be exactly the review theatre §6 of the procedure warns about.

**Sharpened finding — the binding constraint is the POOLED sub-module bar, and it is tight:**

| sub-module | pooled | files | stmts | headroom to 95 % (new *uncovered* stmts) |
|---|---|---|---|---|
| `src/frontend` (contains `dashboard_manager.py`) | 96.34 % | 10 | 1965 | **27** |
| `src` | 96.21 % | 20 | 4245 | 53 |
| `src/backend` | 97.85 % | 15 | 2788 | 83 |
| `src/frontend/components` | 97.91 % | 17 | 3203 | 98 |

So a 50-80 line change to `dashboard_manager.py` that ships **more than ~27 uncovered statements**
fails CI on the sub-module bar while the file itself still reads 94 %+. That is a genuinely
counter-intuitive gate and it is not visible from the file's own number — which is why "~20 lines"
estimates miss it. **The gate does not tax the source change; it forces every new branch to be
tested — which is the argument for the *test* estimate, not the source estimate, and §2a-2b stand on
their own without any coverage argument at all.**

*Instrument caveats:* my run installed neither `h5py` nor `.[juniper-cascor]` (CI's coverage leg does
both), and ran Python 3.13 rather than CI's 3.14 leg. Those omissions depress `main.py` (sub-module
`src`) and `src/backend`; neither touches `src/frontend`, so the **27** figure should track CI closely.
The instrument could have produced a different answer — and it did: it contradicted my prior.

The gate is **not exemptible in this repo**: canopy invokes `juniper-coverage-gap-map --coverage-json
reports/coverage.json --enforce` with **no `--omit`** (`ci.yml:261`), and the tool's `--omit` is the only
per-file exclusion mechanism (`cli_coverage_gap_mapper.py:140-144`). And it is **blocking**: the `unit-tests`
job carries the gate step, and `required-checks` ("Quality Gate", `ci.yml:961-994`) hard-fails on
`needs.unit-tests.result != "success"`.

There is also a **Playwright lane on every PR** — `ui-tests` ("UI Sub-suite (Playwright)", `ci.yml:360-421`,
`-m "ui and not slow" src/tests/ui`, `JUNIPER_CANOPY_DEMO_MODE=1`), whose `failure` is likewise fatal at the
Quality Gate (`ci.yml:1005-1009`). This is where a real reachability assertion belongs — the existing
`src/tests/ui/test_dataset_apply.py` already drives the sidebar dataset panel in a browser — and the round's
estimate does not budget for it at all.

*(Snapshot tests are a non-issue and I record that as a finding against my own suspicion:
`src/tests/regression/test_panel_layout_snapshots.py` parametrises only `metrics_panel` and
`dataset_plotter`; `snapshots/` holds exactly those two `.txt` baselines. The sidebar is not snapshotted.
`src/tests/ui_contract/control_manifest.py` contains no reference to `nn-dataset-type-dropdown`,
`model-select-btn` or `restart-ds-type`. `test_ui_standards_doc_in_sync.py` covers sidebar widths only.)*

### 2d. The fix as specified is **not correct** without two more pieces

**(i) The snap does not always repair.** `_gate_dataset_options_handler` (`:2702-2706`):

```python
options = apply_availability_gate(gated_dataset_options(model_key), self._fetch_generators())
enabled = [o["value"] for o in options if not o.get("disabled")]
if current_value in enabled or not enabled:
    return options, dash.no_update      # <-- no repair when NOTHING is enabled
return options, enabled[0]
```

`equities_seq` is the **only** recurrence-compatible dataset, and it declares an availability hook:
`juniper-data/juniper_data/generators/equities_seq/generator.py:67 def is_available()` — gated on the
`equities` extra (`api/routes/generators.py:178-200`). On a deployment without that extra,
`apply_availability_gate` disables it, `enabled == []`, the snap returns `no_update`, and the user is left
at **(recurrence, spirals)** — a state today's `:3050` gate makes unreachable and the unary fix makes
reachable. This is not hypothetical: `_UNAVAILABLE_REASONS` (`src/dataset_schema.py:106-110`) has no
`equities_seq` key, so it would read the generic "unavailable in this deployment".

**(ii) Start is not gated on compatibility, only on lifecycle.**
`_update_button_appearance_handler` (`:7187-7206`) force-disables Start solely via
`model_is_trainable(model_key)` — a **status**-only predicate. There is no dataset input. So in state (i),
Start is **enabled**, `resolve_oneshot_start_body` forwards `generator="spirals"`, and the recurrence
service fails in `sequence_data_from_arrays` with `"X_train must be 3-D (W, L, F) …"`
(`juniper-recurrence-model/juniper_recurrence_model/data.py:69-70`). Fail-closed at the service (FR9), but
a **new** user-visible failure the current gate prevents. Any honest fix must add the compatibility factor
to the Start gate.

### 2e. Calibration against the PRs that built this surface

```
442673e (#397, created the deadlock): dashboard_manager 205 + model_registry 35 = 240 src, 296 test
a96a114 (#400, recurrence -> live):   dashboard_manager  73 + model_registry 41 = 114 src, 125 test
```

### 2f. **My independent estimate**

| piece | src | test |
|---|---|---|
| unary `:3050` + `title=` | 2-4 | (inverts 6 assertions, 5 tests) |
| hard guard for `enabled == []` (§2d-i) | 6-10 | 30-50 |
| "your dataset was changed to X" notice: layout div + 3rd Output + handler | 15-25 | 40-60 |
| Start gate on compatibility (§2d-ii): new Input on a 10-Output callback | 10-15 | 30-50 |
| doc/comment truth-up (2 module docstrings, `:2584-2590`, `:2692-2706`) | 15-25 | — |
| **narrow fix subtotal** | **50-80** | **150-250** |
| restart modal `restart-ds-type` re-gating (§4b) | 15-25 | 40-60 |
| `execution` mirror bug (§3c) — canopy + `main.py` | 10-20 | 40-60 |
| **realistic arc** | **75-125** | **230-370** |

**Verdict: MIS-SIZED.** "~20 lines / 2-3 test assertions" prices only the `:3050` edit and none of the
6 forced inversions, 4 arity breaks, the empty-`enabled` hole, the Start gate, or the coverage tax.
"One PR, plus a second for the restart modal" is closer to **three**: (1) unary + snap-hardening + Start
gate + notice, (2) restart modal, (3) the `execution` mirror. The round's own recognition that the
restart modal needs its own PR is the tell — it already knew the estimate did not close.

---

## 3. THE THREE "BLOCKERS" — one CONFIRMED-but-mischaracterised, one CONFIRMED-for-the-opposite-reason, one REFUTED

The round presents these as three defects stacked **behind** the deadlock, revealed in sequence by fixing
it. That is wrong in structure. Two of them are **mutually exclusive deployment branches** and the third is
inert.

### 3a. `RecurrenceBackend` has no `stage_dataset` → 500 — **CONFIRMED, but NOT on the Start path**

`grep -n "def " src/backend/recurrence_backend.py` — no `stage_dataset`. `main.py:3995` calls
`backend.stage_dataset(**params)` inside a bare `except Exception` → 500 + `error_id` (`main.py:4003-4006`).

But the brief's own question is the right one, and the answer is **the one-shot Start path never stages**:
`_resolve_oneshot_start_body_handler` (`:2668-2685`) builds `{"dataset": {generator, params}}` from the
dropdown + `dataset_default_params`, stores it in `oneshot-start-params-store` (`:1848`), and both
transports forward it as the start POST body (`:7100-7101` server-side; `:195-197` / `:255-256` clientside).
`main.py:751-768` unwraps it into `start_training` kwargs, which `RecurrenceBackend.start_training` reads
directly (`recurrence_backend.py:138`). **`stage_dataset` is never on that path.**

The 500 fires only if the user presses **Apply Dataset** (`:1345`), which is never suppressed for a one-shot
model. Real, but it is a defect on a *sibling button*, not a blocker of the pair. Calling it a blocker
**OVERSTATES** it.

### 3b. cascor's `Literal` lacks `equities_seq` — **CONFIRMED, but the brief's premise is backwards**

`juniper-cascor/src/api/models/training.py:235`:
```python
dataset_type: Optional[Literal["spirals","xor","mnist","circles","moons","equities","gaussian","checkerboard"]]
```
No `equities_seq` (and none of the five rank-3 synthetics).

The brief asks: *does that route get hit when the active backend is recurrence?* **No — and that is the
point.** It is hit precisely when the backend is **not** recurrence, which is the **default** case:

`main.py:3660-3672` — `_selection_targets_recurrence()` returns True only if the spec's provider is
`RECURRENCE_PROVIDER` **AND** `settings.recurrence_service_url` is set. Default is `None`
(`src/settings.py:261`); only `juniper-deploy/docker-compose.yml:635,768` sets it. `_swap_backend`
(`:3689-3695`) then **no-ops** — and canopy's own regression test pins this:
`src/tests/regression/test_d8_d11_phase4_truth_up.py:64-82`
`assert body["swapped"] is False` / `assert body["backend"] != "recurrence"`, HTTP **200**.

So the two "blockers" are **branch-exclusive**, not stacked:

| deployment | active backend after selecting recurrence | Apply Dataset with `equities_seq` |
|---|---|---|
| `recurrence_service_url` set (docker-compose) | `RecurrenceBackend` | canopy **500** (no `stage_dataset`) — §3a |
| unset (bare local run — the default) | cascor `ServiceBackend` | cascor rejects the `Literal` → canopy **502** "Backend rejected dataset" (`main.py:3999`) — §3b |

Neither is ever "the next one you hit after fixing the first". Presenting them as a queue is a
**mis-sizing of the fix's blast radius**, in the direction that flatters a single small PR.

### 3c. The blocker the round MISSED, which is worse than both — the `execution` mirror lies

On the unconfigured branch, selecting recurrence produces a **silently wrong model**:

- `_select_model_handler` (`:2876-2897`) mirrors `data.get("execution","live")` into `model-class-store`.
- `_model_state_response` (`main.py:3676-3686`) sets `"execution": backend.execution` — the **live
  backend's**, not the selected model's. Unswapped → `"live"`.
- Result: `model-selection-store == "recurrence"` (so the dataset gate snaps to `equities_seq`, the sidebar
  reads **"Active: Recurrence (LMU)"**, cascade panels stay visible), while `model-class-store == "live"`
  → `resolve_oneshot_start_body` returns `None` → Start sends a **bare cascor start**.

The UI claims recurrence + equities_seq; cascor trains on its own staged dataset. That is a
**vacuous-pass class defect in the product** (`reference_vacuous_pass_check_class`), and the deadlock is
currently the only thing preventing it. It must be fixed **in the same PR** as the unary change, or the
"small fix" ships a lie. The round did not mention it.

### 3d. `task_type` disagreement `regression` vs `classification` — **REFUTED as a live defect, and dangerous as stated**

- Artifact: `juniper-data/juniper_data/api/routes/generators.py:117` `equities_seq → "task_type": "classification"`.
  `juniper-canopy/src/model_registry.py:141` `task_type="regression"`. The disagreement is real.
- **Is it live?** No. `GeneratorInfo` (`juniper-data/juniper_data/core/models.py:109-128`) exposes
  `name, version, description, available, install_hint, params_schema` — **`task_type` is not on the wire.**
  `GET /v1/generators` never emits it, so canopy cannot read it. `grep -rn task_type` over
  `juniper-canopy/src` (non-test) returns **only** `model_registry.py` — canopy's own hand-authored labels.
  Nothing in canopy or cascor reads juniper-data's `task_type`. The dispatch it drives is internal to
  juniper-data's dataset route (`generators.py:45-47`).
- **Is canopy wrong?** Not obviously. `equities_seq` is **dual-target**: one-hot `y_*` next-day direction
  *and* `y_reg_*` next-day close (`generators.py:113-120`). The recurrence model **prefers `y_reg_`**
  (`juniper-recurrence-model/.../data.py:76-79`), and canopy seeds `regression_target="return"`
  (`model_registry.py:148`). juniper-data's single scalar `task_type` cannot describe a dual-target
  generator. The defect, if any, is in **juniper-data's schema**, not canopy's label.
- **And "fixing" it naively would delete the pair the round wants to unblock.** `compatible()`
  (`model_registry.py:318`) requires `dataset.task_type in model.supported_task_types`; recurrence declares
  `frozenset({"regression"})` (`:184`). Set `equities_seq.task_type="classification"` and
  `compatible_models(equities_seq) == []` — the compatible-pair count drops 6 → 5 and the recurrence model
  has **no** dataset at all.

**Verdict: REFUTED.** Not a blocker, not exposed by the fix, and the obvious remediation direction is
actively harmful. It belongs in a juniper-data schema note, not on this PR's critical path.

---

## 4. FALSE AUTHORITY — green tests whose names assert what the code denies

### 4a. A regression test named for a property that is false

`src/tests/regression/test_d8_d11_phase4_truth_up.py:56`:

```python
def test_recurrence_spec_is_live_so_the_picker_shows_it_trainable(self):
    assert spec.status == "live"
    assert model_is_trainable("recurrence") is True
```

The name claims *"the picker shows it trainable."* The body asserts a **pure registry predicate** and
touches the picker not at all. In the **same required lane**, `test_model_table.py:135` asserts
`_button_for(table, "recurrence").disabled is True` against the default 2-D dataset. Two green tests, one
of whose *names* contradicts the other's *assertion*. Anyone triaging "is recurrence reachable?" by test
name gets the wrong answer — and the D-8 truth-up (`3ce7bbc`, canopy#530) was itself a *truth-up pass*
that corrected a docstring while leaving this name in place.

### 4b. The snap is proven by a test that constructs an unreachable state

`test_model_picker.py:91` `test_gate_dataset_options_handler_greys_and_snaps_for_recurrence` calls
`manager._gate_dataset_options_handler("recurrence", "spirals")` **directly**. `model_key="recurrence"` is a
value the UI cannot produce. The snap machinery is covered; its *reachability* is not. So "let the existing
snap repair it" rests on a test that has never observed the snap run in a real session — and §2d-i shows it
does not always repair.

### 4c. `restart-ds-type` — permanently gated to cascor

`:5422` builds it with `gated_dataset_options(DEFAULT_MODEL_KEY)` at layout time. `grep -n restart-ds-type`
returns 6 hits: `:490` (a field map), `:5268` **Output(…, "value")**, `:5315` Input, `:5366` State, `:5421`
Label, `:5422` construction. **`Output("restart-ds-type","options")` appears nowhere** — the options are
never re-gated. After the fix, with recurrence active, the restart modal offers the five 2-D types as the
only enabled choices and `equities_seq` greyed. And `:5268` **does** drive its value there:
`open_restart_confirm_modal` (`:5283-5294`) seeds `Output("restart-ds-type","value")` from
`State("nn-dataset-type-dropdown","value")`, so on the recurrence path the modal opens showing
`equities_seq` **as a selected option that is marked disabled in its own option list** — and if the user
changes it away they cannot get back. It then feeds `_restage_dataset` → `/api/stage_dataset` → §3a/§3b.
Confirms the round's instinct that the restart modal needs work; refutes that it is a tidy "second PR".

---

## 5. THE HEADLINE SCALE CLAIM — numbers CONFIRMED, "5×" is RHETORIC

**Independently verified** at `juniper-data/juniper_data/api/routes/generators.py`
(`grep -n '^    "[a-z0-9_]*": {'`) — **16** registry entries at lines 54, 61, 68, 75, 85, 92, 99, 106, 113,
121, 129, 137, 145, 153, 161, 168; `ls juniper_data/generators/` confirms 16 packages. Canopy models **6**
(`model_registry.py:132-149`). The five `task_type: "regression"`, `time_unit: "steps"` entries are
`multi_sine` (:121), `mackey_glass` (:129), `ar_p` (:137), `irregular_sine` (:145), `delay_product` (:153).
All confirmed.

**But:**

1. **Canopy hides 10, not 5.** The other five are `gaussian`, `checkerboard`, `csv_import`, `equities`,
   `arc_agi`. Quoting 5 is a correct sub-count of a specific class, but "6 of 16" and "hides 5" invite the
   reader to subtract wrongly.
2. **"5× larger than the deadlock" compares different units.** One side is *unreachable pairs among modelled
   ones* (1 of 6); the other is *generators not modelled at all* (5, or 10). There is no ratio between them.
   As a **pair** count it is 5 new `(recurrence, X)` pairs vs 1 recovered — a defensible "5×" only if every
   one of the five works end-to-end, which is unmeasured. Call it "five additional candidate pairs,
   unvalidated", not "5× larger".
3. **Significance cuts the OTHER way from what a hold-the-fix argument wants.** Those five are
   numpy-only `(W, L, 1)` sequences with a per-step `dt` and a `y_{split}` regression target
   (`multi_sine/generator.py:48`). They need **no optional extra and no network**. `equities_seq` needs the
   `equities` extra *and* live Yahoo Finance + SEC EDGAR. `sequence_data_from_arrays` falls back to
   `y_{split}` when `y_reg_` is absent (`data.py:76-81`), and canopy already renders 3-D sequences
   (`src/frontend/components/dataset_plotter.py:754,792,905`). The five are plausibly **more** usable than
   the one the round is fighting to unblock.
4. **But at least one carries a known defect.** `mackey_glass` accepts a seed and ignores it (juniper-ml
   partition census, `notes/JUNIPER_2026-08-31_…`; recorded in memory as *"Generator seeding has THREE
   states"*). Exposing five generators exposes that too.
5. **Un-measured legs remain.** For all five: `Apply Dataset` → cascor `Literal` (§3b) rejects every one of
   them; `_UNAVAILABLE_REASONS` has no entry; `dataset_default_params` has none. Whether they work
   end-to-end is **NO ARTIFACT** — nobody has run it.

**Verdict: numbers CONFIRMED; "5× larger" OVERSTATED as a measure.**

---

## 6. STEELMAN BOTH DIRECTIONS

### 6a. HOLD — "this surface needs rework; a small fix entrenches a broken model"

Strongest form, on evidence:

- The bidirectional gate has **no acyclicity invariant**. Nothing in code or tests asserts every compatible
  pair is reachable. `compatible_models` / `compatible_datasets` exist (`:322`, `:330`) and are *never used
  to check reachability*. Add a third model and the same class of trap returns.
- The conflict policy is **mislabelled in the code**. `:2703` says *"snap to the first enabled option
  (dataset-primary conflict policy, D5)"*. The design's D5 §5.6 (line 165-166,
  `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`) defines *dataset-primary: keep
  dataset, clear model + notice* and *model-primary: keep model, clear dataset + notice*. The code **keeps
  the model and changes the dataset** — that is **model-primary**, and it **snaps** rather than **clears**,
  with **no notice**. Three deviations from the cited decision, in a docstring that cites it. Building on
  this without settling the policy hardens a policy nobody chose.
- The state is **split across two stores that can disagree** (`model-selection-store` vs
  `model-class-store`), and §3c shows they *do* disagree on the default deployment.
- The round's own scope already spills to 3 PRs (§2f). That is the signature of rework, not a patch.
- `test_model_table.py` would end the round with **two vacuous tests** (§2a rows 4-5) and one whose premise
  is gone — the suite gets *weaker* while reading green.

### 6b. SHIP — "fix it now"

Strongest form, on evidence:

- **It is a regression, not a design gap.** #397 removed a working path (§1b). Restoring reachability is
  reverting a defect, not designing a feature. Reverts do not need the redesign they preceded.
- The design **already ratified** the posture the fix needs: D5 (line 55) — *"Correctness comes from the
  predicate + backend (applied symmetrically); greying/labelling is a best-effort affordance, **not** the
  correctness guarantee."* A unary Select button is the design's own position; the current binary gate is
  the deviation.
- The repair machinery **exists and is covered** — `_gate_dataset_options_handler`'s snap, `model_reason`
  for the advisory cell, `dataset_model_hint` for the reverse gate. The fix wires existing parts.
- **Holding is not neutral.** While held, `recurrence` sits `status="live"`, `model_is_trainable` returns
  True, the sidebar advertises it, and the model service is deployed and wired
  (`docker-compose.yml:635,768`) — an entire shipped service is unreachable from its only UI.
- Rework has no owner, no plan, and no date. The round produced none.

### 6c. What the artifacts actually support

**SHIP the fix — but at the size in §2f, not the size in the round's estimate, and with §3c inside it.**

The HOLD case's best evidence (mislabelled conflict policy, no acyclicity invariant, split state) argues for
*additional* work, not for *withholding* the reachability repair; none of it is made worse by restoring a
path that existed at `f464272`. The SHIP case's decisive fact is that this is a **regression with a known
culprit commit**, and the design's own D5 already licenses the unary gate.

But two things are **non-negotiable inside the first PR**, and the round has neither:

1. **§3c — the `execution` mirror.** Without it, the default (unconfigured) deployment gets a UI that says
   "Active: Recurrence (LMU)" over a cascor training run. Shipping reachability without this converts a
   *blocked* path into a *silently wrong* one. That is strictly worse than the deadlock.
2. **§2d — the empty-`enabled` guard + the Start compatibility gate.** Without them, an
   `equities_seq`-unavailable deployment lands on (recurrence, spirals) with Start live.

And one thing must be **added, not fixed**: a reachability invariant test —
*for every `(d, m)` with `compatible(d, m)`, a UI transition sequence exists from the mount state.*
That is ~20 lines over `DATASET_TYPES × MODELS` and is the only artifact that stops this class returning
when the third model lands. Its absence is why four independent readers had to rediscover the deadlock by
hand.

---

### 6d. The round costed ONE fix shape and never priced the alternatives

"Unary predicate at `:3050`" is one of at least four repairs, and the round converged on it without
comparing. Four agents agreeing on a shape they were all handed is §2-Lane-A false consensus, not
evidence.

| shape | what it does | cost signal |
|---|---|---|
| **A. unary Select** (the round's) | model table never disables Select; dataset snaps | throws the model-side affordance away entirely; needs the §2d guards; 6 test inversions |
| **B. symmetric snap** | drop `disabled` from the *dataset* options instead, and snap the **model** when a dataset strands it | preserves both affordances; the snap already exists on one axis, so this mirrors it; is the design's **dataset-primary** policy (§5.6), which `:2703` already *claims* to implement |
| **C. ship D4** | `clearable=True` on `:1334` + the three guards in §1e | the design's own answer; smallest source delta; but adds a `dataset is None` state to every consumer |
| **D. disable Select only when `compatible_datasets(model) == []`** | keeps a meaningful gate; a model with *some* compatible dataset stays selectable | one-line predicate change, no affordance loss, no new None state |

**D is a one-line change that is strictly closer to "~20 lines" than A, and the round did not consider it.**
That the round's chosen shape happens to be the one requiring the most collateral test churn — while being
sized as the cheapest — is itself the mis-sizing signature.

---

## 7. What this review CANNOT support

- I did not run the canopy UI. Every UI claim here is derived from layout construction, callback
  registration, and handler source — not from a browser. The ecosystem's standing note
  (*"E2E finding mechanisms are unreliable — symptoms hold, mechanisms often wrong"*) applies to me.
- `dcc.Dropdown` per-option `disabled` is **declared supported** — `dash 4.2.0` in `JuniperCanopy1`,
  `dcc.Dropdown.__doc__`: *"An array of options {label, value}, an optional `disabled` field can be used
  for each option."* I did **not** exercise it in a browser. If Dash ignored the flag at runtime the
  dataset half of the deadlock would not exist and the whole finding would collapse to a one-sided gate,
  so this is the single cheapest falsifier left: one browser click on the greyed `equities_seq` option.
  (Note also that this env is Dash **4.2.0**, not the Dash 3 recorded in ecosystem memory.)
- The five hidden rank-3 generators are **unvalidated end-to-end**. No artifact shows any of them run
  through canopy + recurrence.
- No artifact establishes that D4 was *deliberately* dropped. Absence of a rationale is not a rationale.
- Sample size for the deployment-branch analysis (§3b) is **two configurations, both read from config
  files, neither exercised**.
- The coverage measurement **contradicted my prior** (see §2c "MEASURED"). The per-file 90 % floor is
  loose (~119 statements of headroom on `dashboard_manager.py`); the binding gate is the `src/frontend`
  pooled 95 % bar at **27** uncovered statements. I have corrected the argument rather than kept the
  stronger-sounding one. The coverage argument is now a *supporting* point, not a load-bearing one —
  §2a (11 forced test sites) stands entirely without it.
- The coverage run was **one** execution, on Python 3.13, without `h5py` and without
  `.[juniper-cascor]`, on a box running several concurrent sessions. n=1, and not CI's exact matrix.

---

## 8. Verdict table

| # | claim | verdict | key artifact |
|---|---|---|---|
| 1 | `(recurrence, equities_seq)` unreachable; 5 of 6 pairs reachable | **CONFIRMED** | re-derived; `model_registry` probe + `:3050` + `:1334` |
| 2 | all six anchors | **CONFIRMED** | see §0 table |
| 3 | root cause = D4's inline ✕ "specified but never shipped" | **REFUTED** | `13a5856` (2026-05-10) predates the design (2026-06-17); `f464272`→`442673e` = canopy#397 |
| 4 | fix ≈ "~20 lines / 2-3 assertions / 1 PR + 1" | **REFUTED (undersized ~3-4× src, ~10× test)** | §2a (11 forced test sites, counted); §2b arity; §2f |
| 4b | *my own* "coverage gate is a major cost driver" | **SELF-REFUTED, corrected** | measured: file floor has ~119 stmts headroom; binding bar is `src/frontend` pooled 95 % at **27** |
| 5 | "let the existing snap repair" | **REFUTED** | `:2702-2706` returns `no_update` when `enabled == []`; `equities_seq.is_available()` |
| 6 | `RecurrenceBackend` missing `stage_dataset` is a blocker | **OVERSTATED** | one-shot Start bypasses staging (`:2668`, `main.py:751-768`) |
| 7 | cascor `Literal` blocker | **CONFIRMED, mischaracterised** | fires on the **unswapped** branch (`main.py:3660-3672`; `test_d8_d11…:64-82`) |
| 8 | `task_type` disagreement is a blocker behind the deadlock | **REFUTED** | `task_type` absent from `GeneratorInfo` (`core/models.py:109-128`); naive fix deletes the pair |
| 9 | canopy hardcodes 6 of 16; 5 rank-3 regression generators hidden | **CONFIRMED** | `generators.py` registry; `ls juniper_data/generators/` |
| 10 | "a loss 5× larger than the deadlock" | **OVERSTATED (rhetoric)** | different units; 10 hidden, not 5; five legs unvalidated |
| 11 | (missed) `execution` mirror makes an unconfigured deployment lie | **NEW — CONFIRMED** | `:2896` + `main.py:3676-3686` |
| 12 | (missed) `restart-ds-type` options never re-gated | **NEW — CONFIRMED** | no `Output("restart-ds-type","options")` anywhere |
| 13 | (missed) `test_..._picker_shows_it_trainable` name is false | **NEW — CONFIRMED** | `test_d8_d11_phase4_truth_up.py:56` vs `test_model_table.py:135` |
| 14 | (missed) `:2703` cites D5 and names the wrong policy | **NEW — CONFIRMED** | design §5.6 lines 165-166 |

**Ship recommendation: SHIP, resized.** One PR containing the unary `:3050`, the empty-`enabled` guard,
the Start compatibility gate, the `execution` mirror fix, the snap notice, and a reachability invariant
test (~50-80 src / ~150-250 test); a second for the restart modal; a third if the `execution` mirror is
split out. Do **not** ship it as "~20 lines", and do **not** carry the D4 root-cause story or the
`task_type` blocker into a document of record.
