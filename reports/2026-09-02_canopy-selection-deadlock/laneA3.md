# Lane A verifier A3 — SPECIFIED-vs-SHIPPED delta, canopy model×dataset selection

**Entry point used**: the design of record + git history. No runtime/browser observation was
used anywhere in this report; every assertion below is a quote from a committed artifact.

**Repos read (read-only, unmodified)**:
- `/home/pcalnon/Development/python/Juniper/juniper-canopy` @ `30e15b7` (branch `main`, clean tree)
- `/home/pcalnon/Development/python/Juniper/juniper-ml` (notes + reports)

**Design of record**:
`/home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`
(hereafter *the design doc*).

---

## 0. Verdict table

| Claim | Verdict | One-line basis |
|---|---|---|
| **C1** — D4/§5.5 specified an inline ✕ on the dataset dropdown whose side-effect was "the model table re-activates fully via the gate" | **CONFIRMED, verbatim** | design doc `:54` (D4) and `:152-157` (§5.5) |
| **C2** — the escape hatch was NOT implemented; dataset dropdown `clearable=False` (`:1334`) and restart-modal one likewise (`:5422`) | **CONFIRMED**, and *explicitly recorded as deferred* in the shipping PR | `dashboard_manager.py:1334`, `:5422`; `git log -S"clearable=True"` returns **zero commits on any branch, ever**; PR #394 body states "**Inline ✕ (D4) deferred**" |
| **C3** — §5.6's premise is FALSE as shipped; both sides hold a value and each hard-disables the far side, so the far-side option is permanently greyed | **CONFIRMED IN SUBSTANCE, REFUTED IN WORDING** | The consequence is exactly right and statically provable. But the premise sentence is not *false* — it is **vacuously true and therefore inert**. See §3. |
| **C4** — OQ-6 never resolved; no model-side conflict *policy*, only a hard block; dataset side auto-snaps (`:2687`) vs model side hard-blocks (`:3050`) | **CONFIRMED**, plus a **bonus defect**: the shipped snap is labelled with the *wrong* policy name | design doc `:305` (OQ-6 open); `_gate_dataset_options_handler:2687` docstring says "dataset-primary conflict policy, D5" but the behaviour it describes is the design's **model-primary** |
| **C5** — `restart-ds-type` (`:5422`) is gated statically against `DEFAULT_MODEL_KEY` and never re-gated on model change | **CONFIRMED** (with one wording correction: *disabled with a reason suffix*, not *hidden*) | the **only** `Output` on `restart-ds-type` anywhere is `:5268` on `"value"`; there is **no** `Output` on `restart-ds-type.options` in the repo |

**Previously recorded anywhere?** **No.** See §6. The nearest thing is a *pre-registered
test step that would have hit it* (E2E matrix W8 step 5), which was never run.

---

## 1. C1 — the design text (CONFIRMED, verbatim)

Design doc, decision table, `:54`:

```
| D4 | **Clear/reset = conventional inline ✕** on each control (clearing one auto-widens the other via the gate). The original cross-placement is retained as a **spike alternative** (OQ-2), not the default. |
```

Design doc §5.5, `:152-157`:

```
### 5.5 Clear / reset (D4 / Fork 4)

Conventional **inline ✕** on the dataset dropdown (clears itself; the model table
re-activates fully via the gate as a side-effect) and a "clear model / show all" reset on
the surface. Cross-placement ("clear the constraint on *this* list") is kept as the
OQ-2 spike alternative, not the default.
```

Also design doc `:73` FR6: "Clear/reset each selection (inline ✕ — D4) → restores the full
active set on the other side."

The claim's quoted side-effect is **verbatim**. C1 is confirmed on the artifact.

Note the design specifies **two** clear affordances in §5.5, not one:
1. the inline ✕ on the dataset dropdown, and
2. a "clear model / show all" reset **on the model surface**.

**Neither shipped.** `grep -n -i -E "clear model|show all|reset model|model-clear"` over
`src/frontend/dashboard_manager.py` returns **nothing**. The model-selection modal
(`:2223-2228`) contains a search box, the table container, and a Close button — no reset.
(The search box's native `type="search"` clear resets the *search string*, not the model.)

---

## 2. C2 — the shipped controls (CONFIRMED)

`juniper-canopy/src/frontend/dashboard_manager.py:1330-1337` (sidebar dataset dropdown):

```python
dcc.Dropdown(
    id="nn-dataset-type-dropdown",
    options=gated_dataset_options(DEFAULT_MODEL_KEY),
    value=DEFAULT_DATASET_TYPE,
    clearable=False,
    ...
)
```

`:5422` (restart modal):

```python
dcc.Dropdown(id="restart-ds-type", options=gated_dataset_options(DEFAULT_MODEL_KEY), value=DEFAULT_DATASET_TYPE, clearable=False, className="mb-2"),
```

Both line numbers in the claim are exact.

**Stronger than the claim**: `git log --all -S"clearable=True"` in juniper-canopy returns
**zero commits**. The literal ✕ was never implemented on any branch at any point in the
repository's history. This is not a regression or a revert — it never existed.

`git blame -L 1330,1337`:

| line | commit | date | note |
|---|---|---|---|
| `:1331` `id=` | `13a5856d` | 2026-05-10 | control predates the design doc by 5 weeks |
| `:1332` `options=gated_dataset_options(...)` | `2122a7d6` | 2026-06-24 | forward gate added |
| `:1333` `value=DEFAULT_DATASET_TYPE` | `9d1274b9` | 2026-06-18 | A0 registry rewire |
| `:1334` `clearable=False` | `13a5856d` | **2026-05-10** | **predates the design; never revisited** |

So D4 was written on 2026-06-17 against a control that had already been `clearable=False`
for five weeks, and the A1 work that touched the two lines above it left `:1334` alone.

---

## 3. C3 — REFUTED IN WORDING, CONFIRMED IN SUBSTANCE

Design doc §5.6, `:161-162`:

```
A newly *selected* option is never incompatible (greyed). A conflict can only arise by
**changing** an already-set value so the other side is stranded.
```

### 3a. Why the wording is wrong

The claim says this premise "is FALSE as shipped". It is not false. As shipped, you
genuinely *cannot* select an incompatible option — the option is `disabled` and the button
is `disabled`. Sentence 1 holds. Sentence 2 also holds, *trivially*: no conflict can ever
arise, because no cross-partition change is possible at all.

The premise is **vacuously true**, and that is the actual defect: §5.6 exists to introduce a
**conflict-resolution policy**, and in the shipped build that policy's triggering condition
is **unreachable**. The design plainly expects conflicts to occur ("A conflict *can* arise
by changing an already-set value so the other side is stranded. Resolution is a **single
swappable policy** in the resolver"). Both listed resolutions —

```
- *dataset-primary:* keep dataset, clear model + notice.
- *model-primary:* keep model, clear dataset + notice.
```

— require the ability to **clear** a side, i.e. D4. Without D4 there is nothing to clear,
so the policy cannot be expressed, and nothing can strand anything because nothing can move.

Recommendation to the parent: restate C3 as *"§5.6 is vacuously satisfied and its conflict
policy is unreachable dead specification"*, not *"the premise is false"*. The distinction
matters because the steelman (§7) turns on it.

### 3b. Why the substance is right — the static reachability proof

**Partition (registry seeds, `src/model_registry.py`)**:
- `DATASET_TYPES` (`:133-143`): `spirals`, `xor`, `mnist`, `circles`, `moons` — all
  `ndim=2, classification`; plus `equities_seq` (`:139-142`) — `ndim=3, regression,
  temporal="irregular"`.
- `MODELS` (`:168-189`): `cascor` (`input_ndim=frozenset({2})`, `status="live"`) and
  `recurrence` (`input_ndim=frozenset({3})`, `requires_dt`, `status="live"` since A1-iv-5).
- `DEFAULT_DATASET_TYPE = DATASET_TYPES[0].value` → `"spirals"` (`:153`);
  `DEFAULT_MODEL_KEY = MODELS[0].key` → `"cascor"` (`:197`).
- `compatible()` (`:311-318`) = `ndim ∈ input_ndim ∧ task_type ∈ supported_task_types ∧ temporal_ok`.

The compatibility relation is a **perfect bipartition with no overlap**:
`{5 rank-2 datasets} × {cascor}` and `{equities_seq} × {recurrence}`.

**Both sides always hold a value.**
- dataset: `value=DEFAULT_DATASET_TYPE` (`:1333`), `clearable=False` (`:1334`).
- model: `dcc.Store(id="model-selection-store", storage_type="memory", data=DEFAULT_MODEL_KEY)` (`:1842`).

**Each side hard-disables the far side.**
- model → dataset: `gated_dataset_options()` (`model_registry.py:408-424`) emits
  `{"label": f"{label} — {reason}", "value": ..., "disabled": True}` at `:423` for every
  incompatible dataset. `apply_availability_gate()` (`dataset_schema.py:268-286`) only ever
  *adds* `disabled`; it never clears it (`:281`).
- dataset → model: `_build_model_selection_table` (`:3000-3079`) computes
  `reason = model_reason(model, dataset)` (`:3033`), `is_compatible = reason is None`
  (`:3034`), and builds the row's Select as `disabled=not is_compatible` (`:3050`).

**Complete writer enumeration (this is the load-bearing step).**

`grep -n "nn-dataset-type-dropdown" src/frontend/dashboard_manager.py` — the **only**
`Output`s are `:2605` (`.options`) and `:2606` (`.value`), both on the single callback
`gate_dataset_options` (`:2604-2613`). Its handler `_gate_dataset_options_handler`
(`:2687-2706`) ends:

```python
options = apply_availability_gate(gated_dataset_options(model_key), self._fetch_generators())
enabled = [option["value"] for option in options if not option.get("disabled")]
if current_value in enabled or not enabled:
    return options, dash.no_update
return options, enabled[0]
```

So the dataset value can only ever become `enabled[0]` **of the set gated against the
current model**. With `model_key == "cascor"`, `equities_seq` is never in `enabled`.

`grep -n "model-selection-store"` — the **only** `Output` is `:2591`, on the callback
`select_model` (`:2590-2599`), whose sole `Input` is
`{"type": "model-select-btn", "index": ALL}.n_clicks` — i.e. the table buttons, which are
`disabled` for incompatible models.

There is **no** FR15 re-hydration writer: nothing initialises `model-selection-store` or the
dataset dropdown from backend state. (Design doc `:83` FR15 — "Selection initializes from
current backend state, is **re-validated against the registry** on load" — is a separate
unshipped requirement; `model-class-store` is hydrated from `GET /api/train/status`, but
`model-selection-store` is not.)

**Therefore**: from the seeded state `(cascor, spirals)` the reachable state set is
`{cascor} × {spirals, xor, mnist, circles, moons}`. `recurrence` and `equities_seq` are
**unreachable through the UI**. C3's consequence is confirmed by static callback-graph
analysis, with no runtime observation required.

### 3c. The tests pin the deadlock as expected behaviour

`juniper-canopy/src/tests/regression/test_model_table.py:132-144`:

```python
# spirals = 2-D classification: cascor compatible, the 3-D recurrence model is not.
assert _button_for(table, "cascor").disabled is False
assert _button_for(table, "recurrence").disabled is True
...
# equities_seq = 3-D irregular regression: recurrence compatible, the 2-D cascor model is not.
table = DashboardManager._build_model_selection_table("equities_seq", "recurrence")
assert _button_for(table, "recurrence").disabled is False
assert _button_for(table, "cascor").disabled is True
```

The second block, and `:197` (`_toggle_model_modal_handler("nn-model-change-button",
"equities_seq", "recurrence")`), and `:254`, `:263`, `:273`, `:345`, `:372` all **construct
the `equities_seq` state directly by argument**. Every one of them tests a state the UI
cannot enter. This is the *vacuous-pass* shape: the unit under test is correct in a state
the composed system never reaches, and the suite is green either way.

---

## 4. C4 — CONFIRMED, plus a policy-label defect

### 4a. OQ-6 open

Design doc §9, `:305`:

```
- **OQ-6:** conflict-policy default (dataset- vs model-primary) — decide post-spike (D5).
```

Nothing anywhere resolves it. `grep -rn "OQ-6"` across both repos' `notes/` returns hits in
other documents, but every canopy-selection hit is either this line or a **different OQ-6 in
a different namespace** — `notes/JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md:314`
defines its own "OQ-6: the 3-D dataset **visualization** design (D2)", and its "D4" at `:207`
is "Recurrence image — DONE". **The enabler-scope doc's D/OQ numbering is a separate
namespace from the design doc's** — do not conflate them when citing.

### 4b. The asymmetry, as shipped

| side | mechanism | file:line |
|---|---|---|
| dataset (driven by model change) | **auto-snap** to `enabled[0]` | `_gate_dataset_options_handler`, `dashboard_manager.py:2687-2706` (snap at `:2706`) |
| model (driven by dataset value) | **hard block**, no resolution path | `_build_model_selection_table`, `dashboard_manager.py:3050` |

Confirmed exactly as claimed. There is no model-side policy at all — no clear, no notice, no
swap; the far-side row is simply un-clickable.

### 4c. Bonus defect — the shipped snap is labelled with the wrong policy name

`_gate_dataset_options_handler` docstring, `:2695`:

> "If the current selection became disabled, snap to the first enabled option
> (**dataset-primary conflict policy, D5**)."

PR #394's body repeats it: "a stranded selection **auto-snaps to the first compatible**
dataset (dataset-primary conflict policy, D5)."

But the design doc defines the two policies at `:166-168`:

```
- *dataset-primary:* keep dataset, clear model + notice.
- *model-primary:* keep model, clear dataset + notice. (Fits the model-centric
  benchmarking trajectory.)
```

The handler **keeps the model and changes the dataset**. By the design's own vocabulary that
is **model-primary**, not dataset-primary. The code and both PR bodies name it backwards.
This matters beyond pedantry: it is the only place OQ-6 is ever "answered", and it answers it
with the wrong label, so a reader reconciling code against design gets the opposite reading.

---

## 5. C5 — CONFIRMED (with a wording correction)

`grep -rn "restart-ds-type" src/` — complete, 6 hits, all in `dashboard_manager.py`:

| line | role |
|---|---|
| `:490` | entry in the staged-field name table |
| `:5268` | **`Output("restart-ds-type", "value")`** — the *only* Output on this id, anywhere |
| `:5315` | `Input(..., "value")` — summary refresh |
| `:5366` | `State(..., "value")` — read on Confirm |
| `:5421` | `dbc.Label` |
| `:5422` | the `dcc.Dropdown` construction |

There is **no `Output` on `restart-ds-type.options`** in the repository. Its options are
therefore frozen at layout-build time at the value of `gated_dataset_options(DEFAULT_MODEL_KEY)`
— `DEFAULT_MODEL_KEY` being a module constant (`model_registry.py:197`), this is invariant
across the process lifetime and across page loads regardless of whether the layout is a
value or a callable.

**Correction to the claim's wording**: the 3-D dataset is not *hidden* — `gated_dataset_options`
`:423` emits it with `"disabled": True` and a reason-suffixed label ("Equities … — needs a
2-D model"). It is visible and un-selectable. The operational effect the claim asserts
(unavailable in the restart modal even under the 3-D model) holds.

**Second-order consequence worth recording**: `:5268` copies the *sidebar* dataset value into
`restart-ds-type` on modal open (`State("nn-dataset-type-dropdown", "value")`, `:5285`). If the
sidebar ever held `equities_seq`, the restart modal would open displaying a value its own
options list marks `disabled` — a self-inconsistent control. Today that is unreachable only
because the sidebar itself can never reach `equities_seq` (§3b): **the deadlock is the only
thing preventing this second defect from being observable.** (Cf. the standing "a broken
thing masks the next one" pattern.)

Blame: `:5422` is `281d6f3e`, 2026-07-20, "fix(training): N3b — restart modal granular modify".

---

## 6. Dating the delta, and prior-record search

### 6.1 The causal chain, entirely from committed artifacts

| when | commit / PR | what | did it acknowledge the deadlock? |
|---|---|---|---|
| 2026-05-10 | `13a5856d` | sidebar dataset dropdown created with `clearable=False` | n/a (predates the design) |
| 2026-06-17 | — | design doc ratified: D2 (grey both sides), **D4 (✕ escape)**, D5/§5.6 (swappable policy), OQ-6 open | n/a |
| 2026-06-18 | `9d1274b` (#372) | A0: registry becomes single source for dataset options | no |
| 2026-06-24 17:41 | `c6ad56d` (#393) | A1-iv-3a: sidebar `nn-model-dropdown` added with `options=model_options()` — **no compatibility gating whatsoever** on the model side | no |
| 2026-06-24 17:41 | **`2122a7d` (#394)** | A1-iv-3b: **forward gate ships** (`gated_dataset_options`) + the `equities_seq` 3-D seed. **D4 explicitly deferred.** | **the deferral is recorded; the deadlock is not — and at this moment there was none** |
| 2026-06-25 07:29 | **`442673e` (#397)** | A1b-1: replaces the ungated dropdown with the modal table, `disabled=not is_compatible` (`:3050`). **The loop closes here.** | **no** |
| 2026-06-25 | `44365b7` (#398) | A1b-2: "completes the bidirectional gate"; adds the empty-set recovery message | no |
| 2026-06-25 | `a96a114` (#400) | A1-iv-5: `recurrence` flipped `coming_soon` → `live`, making the unreachable half a *shipped, trainable* model | no |
| 2026-07-20 | `281d6f3` | N3b: `restart-ds-type` built statically against `DEFAULT_MODEL_KEY` | no |

**The delta dates to 2026-06-25, PR #397 — roughly fourteen hours after the ✕ was deferred in
PR #394.**

### 6.2 The two artifacts that make this a *reasoning* trail, not just a gap

**PR #394 body ("Scope notes"), 2026-06-24** — this is the deferral *and* its justification:

> **Inline ✕ (D4) deferred.** In the sidebar both dropdowns always need a value
> (model→backend, dataset→training), so a literal "✕-to-none" creates invalid/desynced
> states. The **conflict-snap** delivers D4's "clearing one auto-widens the other" intent
> coherently. Happy to add a literal ✕ if wanted.
>
> **Bidirectional gate**: only model→dataset is needed for the sidebar flow (**the model is
> selected first**; §5.6 "a newly selected option is never incompatible"). The reverse
> (dataset→models) belongs to the A1b surface (iv-4).

Both paragraphs were **true when written**. With `model_options()` ungated, "the model is
selected first" was literally the shipped flow, and model-primary auto-snap is a *complete*
traversal of the partition. #394 also correctly forecast that the reverse gate "belongs to
the A1b surface".

**PR #397 body, 2026-06-25** — the reverse gate arrives, and its central claim is:

> **The insulation insight (why A1b-1 is well-bounded):** the downstream gates key off the
> **stores**, not the dropdown … A1b-1 swaps only the **input** side; the table's Select
> writes those same stores via the unchanged `_select_model_handler`, so every downstream
> gate follows for free (both kept **byte-unchanged**).

This is the error, and it is a precise one. The audit is over *outputs* (which stores the
downstream gates read) and finds no change. It never asks what the *input* side is now
**conditioned on** — and the answer is: on the dataset value, i.e. on the output of the very
gate it just declared untouched. `gate_dataset_options` really is byte-unchanged; the cycle
it now participates in is new. #397 replaced an **unconditioned** input with a
**dataset-conditioned** one and reported it as a pure relocation.

Neither #397's PR body, its commit message, nor its CHANGELOG entry (`juniper-canopy/CHANGELOG.md:616-636`)
mentions that "the model is selected first" — #394's stated licence for deferring D4 — had
just stopped being true.

### 6.3 Was the deadlock ever recorded? **NO ARTIFACT.**

Searched, in both repos, over `notes/**`, `CHANGELOG.md`, and `reports/e2e/*/statuses.tsv`:
`catch-22`, `catch 22`, `deadlock`, `unreachable`, `stranded`, `chicken(-and-egg)`, `OQ-6`,
`escape hatch`, plus regexes for `both (sides|dropdowns).*(disab|grey)`, `never
(be )?(selectable|reachable)`, `cannot ever select`, `no way to (pick|select|reach)`,
`mutually (block|disab|exclu)`.

Every hit is unrelated (recurrence *service* PRs stranded off main; CI rate-gate deadlocks;
unreachable *code* branches; the P5 gradient-unreachability discussion; `equities` optional-extra
availability). **Nothing describes this.**

Also checked: `gh issue view 368` — body predates D1–D8, **0 comments**. `gh pr view 394/397`
— covered above. `juniper-ml/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
— no row. `juniper-canopy/CHANGELOG.md:616-679` (the five A1b entries) — no mention.

**The nearest miss, and it is very near.** The E2E click-by-click matrix,
`juniper-ml/notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`,
journey **W8 — Model switch cascor ⇄ recurrence**, contains both halves of the contradiction
in adjacent steps and does not notice:

- step 2 (`:~951`): "incompatible rows show the reason and a **disabled** Select"
- step 5 (`:956`): "Click the `{"type":"model-select-btn","index":"recurrence"}` Select →
  `POST /api/model/select` …"
- step 9 (`:960`): "`#nn-dataset-type-dropdown` options re-gate to the 3-D-capable set and,
  if the current value is now incompatible, snap to a compatible one"

Step 5 cannot execute from the default `spirals` state *because of* step 2. Step 9 is
written as the consequence of a step that cannot happen.

**W8 was never run.** Its preconditions say: "**Without the leg, every W8 step is `N-A (no
recurrence service)`**". And
`juniper-ml/notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:1756`:

> **Consequence (recorded to prevent a false finding)**: **W7 / W8 and every
> recurrence-dependent row are BLOCKED until the isolated leg is restored on 8212.**

So an **environmental** blocker (recurrence service on the wrong port) masked a **UI**
blocker that would have prevented the journey anyway. The rows that did run and PASS are
presence checks that never cross the partition: C2.6-18 "opens the modal and rebuilds the
table" (PASS), C2.6-19 "reads 'rank-2 (tabular) models only'" (PASS), C2.10-01 "Model picker"
(PASS), C2.7-07 "`nn-dataset-type-dropdown` … Options gated by the selected model" (PASS —
gating *observed*, traversal never attempted), C2.10-07 `restart-ds-type` "select (Dropdown)"
(PASS — driven only among enabled options).

---

## 7. REQUIRED CRITICAL CHECK — steelman the shipped implementation

**The strongest case that the code correctly implements the design:**

1. **D2 mandates exactly what shipped, on both surfaces.** Design doc `:52`: "Incompatible
   options are **disabled (greyed) to prevent selection**". §5.2 `:135-136`: "Compatible rows
   are selectable; **incompatible rows are greyed** with the reason in the compatibility
   cell (D2)." §5.3 `:141-142`: "Selecting a **model** … greys incompatible **datasets** in
   the sidebar dropdown." The design asks for symmetric hard greying in three separate
   places. `:3050` and `gated_dataset_options:423` are a faithful, literal implementation.
2. **§5.6 is not violated.** Its premise holds as shipped (§3a). No conflict ever arises, so
   no conflict is ever mis-resolved. A reader could say the shipped build *satisfies* §5.6
   maximally: it makes the conflict class empty.
3. **D5's correctness guarantee is honoured, and it is the guarantee the design names.**
   `:169-171`: "The predicate + backend (§5.9) enforce correctness regardless … greying is
   best-effort, **not** the guarantee." The pure predicate is implemented, browser-free and
   unit-tested (the "B0 gate", `:103-104`). Nothing invalid can be trained.
4. **D4 was deferred with a stated, engineering-grade rationale, in public, in the PR body**
   — not silently dropped. And the rationale identifies a real problem: `clearable=True` on
   a control the backend requires a value for *does* create a desync class.
5. **The deferral rationale was correct when made.** On 2026-06-24, with `model_options()`
   ungated (`c6ad56d`), the model→dataset auto-snap was a genuinely complete traversal:
   pick any model, the dataset follows. #394's claim that "the conflict-snap delivers D4's
   intent coherently" was **true**, and #394's own words — "**the model is selected first**"
   — describe a coherent, shippable model-primary design that needs no ✕ at all.
6. **The design itself invited a spike-time revision.** D4 keeps cross-placement as "the OQ-2
   spike alternative", D5 says the conflict policy is chosen "after the A1 spike / first real
   use", and OQ-1/OQ-3/OQ-4 were all legitimately re-decided during A1b. A team may
   reasonably re-decide D4 in the same breath.

**Where the steelman fails.**

It fails at exactly one join, and the failure is documented in the artifacts themselves.

- The steelman's strongest plank is #5 — "the deferral was justified because the model is
  selected first". That justification is a **claim about the shipped flow**, not about the
  design. Fourteen hours later `442673e` **falsified it** by making the model side
  dataset-conditioned, and no artifact re-examines the deferral against the new flow. A
  justification whose premise has been deleted is not a justification.
- Reading D2's symmetric greying as *sufficient* requires ignoring the sentence in §5.5 that
  states the escape's mechanism — "the model table re-activates fully via the gate as a
  side-effect". That clause is not decoration; it is the design saying **how the greying is
  meant to be escaped**. §5.5 and §5.6 only cohere with D4 present: ✕ the dataset → the table
  un-greys → select `recurrence` → the dropdown re-gates → `equities_seq` becomes enabled.
  That is the single traversal edge the design provides, and it is the one that did not ship.
- The re-decision reading (#6) has **no artifact**. OQ-1 and OQ-4 were re-decided *on the
  record* ("A1b design ratified 2026-06-25 (OQ-1 / OQ-4 spike)", #397 body). D4 has no such
  ratification — only #394's "**deferred** … Happy to add a literal ✕ if wanted", which is
  the opposite of a decision to drop it, and which no later artifact answers.
- The "correctness is the predicate, not the greying" plank (#3) is true and irrelevant here.
  D5's disclaimer protects against greying being **too coarse** (letting an invalid pair
  through). This failure is greying being **too complete** — a class D5 explicitly does not
  cover.
- The vacuity reading (#2) proves too much. If "no conflict can arise" were the intent, then
  §5.6's swappable policy, its two named resolutions, and OQ-6's "decide post-spike" are all
  specification for a mechanism the design knew would never run — while D5 is simultaneously
  listed as one of the eight **ratified decisions** (`:55`) and A1's phasing (`:320`)
  explicitly ships "the swappable conflict policy (D5)". A design does not ratify, phase, and
  leave an open question on dead code.

**Which reading the artifacts support.** The **uncharitable reading is the correct one**, and
the artifacts do not merely permit it — they contain its confession. The design specified a
single escape edge (D4/§5.5, `:54` + `:152-157`); PR #394 deferred it on 2026-06-24 on the
explicit ground that "the model is selected first"; PR #397 deleted that ground on 2026-06-25
while asserting nothing downstream had changed. The shipped build faithfully implements D2,
D5's predicate, D7, D8 and §5.2/§5.3 — and, having shipped neither of §5.5's two clear
affordances, partitions its own state space with no edge between the halves.

Framed as a delta, not a diagnosis: **the design specifies a reachable `recurrence` /
`equities_seq` state; the shipped callback graph makes it unreachable; the difference is
exactly D4/§5.5, whose deferral is recorded and whose justification was invalidated the next
day by a PR that did not revisit it.**

---

## 8. Scope notes / what I did NOT verify

- **No runtime observation.** Whether `dcc.Dropdown`'s per-option `disabled` and
  `dbc.Button`'s `disabled` are actually honoured by the installed Dash/dbc is asserted by
  the design doc §8 (`:271-274`, "verified vs installed `JuniperCanopy1`: dash 4.1.0 / dbc
  2.0.4") and by `test_model_table.py`, not by me. My entry point is specification + history.
  If either attribute were inert at runtime the deadlock would not manifest — but the shipped
  *intent*, and the pinned tests, are unambiguous.
- **`equities_seq` availability** is a separate axis: `apply_availability_gate`
  (`dataset_schema.py:268-286`) can *additionally* disable it when juniper-data lacks the
  `[equities]` extra. That is a second, independent blocker documented at
  `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:4782-4789` and resolved for
  E2E at `:4856`. It does not affect the compatibility-partition finding — `:281` shows the
  availability gate never *removes* a `disabled` flag.
- I did not evaluate fixes. Per instruction, no solutions are proposed.
