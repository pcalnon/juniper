# Round-2 review — what the eight corrections broke

**Reviewer brief**: round 2 of the independent-agent consensus procedure
(`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4).
Target: the corrections, not the artifact.

**Documents under review**

- EVAL = `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`
- DESIGN = `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`

**Instruments written for this review** (all read-only simulations; no canopy file modified)

- `util/ad-hoc/2026-09-02_canopy_clearable_f1_simulation.py` — the F1 (`clearable=True`) BFS,
  built to mirror `2026-09-02_canopy_unary_guard_simulation.py` so F1 and F2 are measured on
  ONE instrument.
- `util/ad-hoc/2026-09-02_canopy_bottom_oneway_check.py` — forward BFS from `(cascor, ⊥)`.
- `util/ad-hoc/2026-09-02_canopy_round2_null_state_probe.py` — executes the cleared-dataset
  consumers, incl. the three DESIGN did not itself execute.

---

## 0. The F1 simulation the flip skipped

EVAL §5.1 measured F2 with `2026-09-02_canopy_unary_guard_simulation.py` and rejected it on
S3. **F1 was never run through that instrument.** Executed
(`conda run -n JuniperCanopy1 python util/ad-hoc/2026-09-02_canopy_clearable_f1_simulation.py`):

| id | scenario | reachable | compatible | compatible-but-UNREACHABLE | reachable-INVALID (strict) | reachable-INVALID (design defn) | Start LIVE with no dataset |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | today, joint guard, `clearable=False` | 5 | 6 | `(recurrence, equities_seq)` | 0 | 0 | 0 |
| T2 | **F1**, all available | 8 | 6 | none | 2 (`(cascor,⊥)`,`(recurrence,⊥)`) | 0 | **2** |
| T3 | **F1**, `equities_seq` unavailable = **the container case (S3)** | 7 | 6 | **`(recurrence, equities_seq)`** | 2 | 0 | **2** |
| T4 | **F1**, ALL unavailable (the design's own G1d fixture) | 3 | 6 | **5 pairs** | 2 | 0 | **2** |
| T3b | F2 unary guard, `equities_seq` unavailable (S3 reproduced) | 10 | 6 | `(recurrence, equities_seq)` | 5 | 5 | 0 |
| T5 | today, synthetic 3-component | 5 | 7 | 2 pairs | 0 | 0 | 0 |
| T6 | **F1**, 3-component | 10 | 7 | none | 3 | 0 | **3** |
| T7 | **F1**, 3-component, `graph_ds` unavailable | 9 | 7 | `(gnn, graph_ds)` | 3 | 0 | **3** |

Two definitions are reported because the documents silently switch between them: STRICT is the
definition the EVAL §5.1 table used (`Reach − {(m,d) : compatible(d,m)}`); DESIGN is the one
DESIGN §2 introduces (`⊥` is compatible with every model).

**Headline**: on the DESIGN definition F1 creates no invalid pair (real, and better than F2).
But the definition is only sound if `⊥` is non-committable, and it is not (§B-2). And F1
**does not reach the target pair in the container case** (T3) — the exact charge that
disqualified F2.

---

## BLOCKS MERGE

### B-1 | DESIGN §2 (`I-cover`), §5 rows G1a/G1d; EVAL §8 G1

**WHAT IS WRONG.** `I-cover` is stated unconditionally — *"every pair for which `compatible()`
is True is reachable from the mount state"* (DESIGN §2, line 34). It cannot hold in the
deployed container, which DESIGN §9 concedes on the same page (*"the LMU has zero available
datasets regardless of this work"*). The two statements are in direct contradiction, and the
test row built on it is unsatisfiable: DESIGN §5's column header is **"must fail before, pass
after"**, and row **G1d** is *"G1a/G1b with an injected all-unavailable generator list — fails
today (parks)"*. G1a (`Reach ⊇ compatible`) **cannot pass after the fix** under that fixture.

**EVIDENCE.** T4 above: with every generator unavailable, F1 reaches 3 states and leaves
**5 of 6 compatible pairs unreachable** — `(cascor, circles/mnist/moons/xor)` and
`(recurrence, equities_seq)`. T3 (the realistic container fixture, EVAL §6.3) leaves
`(recurrence, equities_seq)` compatible-but-unreachable **after** the fix.

**FIX.** `I-cover` must be conditioned on availability — "every pair that is compatible **and
available** is reachable" — and G1a/G1d must state which arm each fixture asserts (G1d can only
assert G1b plus an explicit recovery state, never G1a).

**SEVERITY: blocks-merge.** The design's central invariant is false as written and one of its
five gating tests cannot be made to pass.

---

### B-2 | DESIGN §2 (the universal-cut-vertex argument) vs §4.7

**WHAT IS WRONG.** DESIGN §2 licenses `⊥` with: *"`⊥` joins every connected component … without
admitting any invalid committed pair, because **`⊥` is not trainable — it is a transit state,
not a destination**."* That is the entire reason F1 is said not to break `I-safe`. It is
**false on the shipped code**, and the design never specifies the change that would make it
true.

**EVIDENCE (executed).**

```
_update_button_appearance_handler signature params: ('self', 'button_states', 'model_key')
model_is_trainable('cascor')     = True
model_is_trainable('recurrence') = True
```

`src/frontend/dashboard_manager.py:7187` takes **no dataset argument**; its callback
(`:4471-4484`) has Inputs `button-states` and `model-selection-store` only. `:7206` force-disables
Start solely on `model_is_trainable(model_key)`. So Start is enabled at `(cascor, ⊥)` and
`(recurrence, ⊥)` — 2 states in the real registry, 3 in the 3-component one (table above).

DESIGN §4.7 *does* say "gate Start", but only inside the `not enabled` recovery arm of
`_gate_dataset_options_handler`. The ordinary `⊥` — the one the user creates with the ✕ — never
enters that arm at all, because `gate_dataset_options` reads the dataset as `State` (`:2609`),
so a clear does not fire the gate. DESIGN §4.1 relies on exactly that fact three paragraphs
earlier. The two claims are mutually exclusive: the clear cannot both bypass the gate (§4.1) and
be caught by the gate's recovery arm (§4.7).

Worse, the two model classes fail **differently** at `⊥`, and DESIGN treats them as one:

- `(recurrence, ⊥)` → `_resolve_oneshot_start_body_handler('one_shot', None)` returns `None`
  (executed) → no dataset ref → `recurrence_backend.py:139-140` `ok=False` → `main.py:3433`
  **409, visible alert**. Fails closed. ✓
- `(cascor, ⊥)` → `model_class != 'one_shot'` → `None` → the **bare reset-only start POST is
  unchanged** (`_resolve_oneshot_start_body_handler` docstring, `:2675`). cascor **trains** on
  whatever is staged service-side while the sidebar shows no dataset. Fails **open**, and it is
  the same displayed-identity-vs-live-backend class the arc itself calls a defect in N5/X1.

**FIX.** Either add `Input("nn-dataset-type-dropdown", "value")` to `update_button_appearance`
and gate Start on `⊥` unconditionally — a callback-signature change that appears in **none** of
§4, §6's touch list ("4 callback-arity breaks") or §7's phasing — or drop the "not trainable"
premise and re-argue `I-safe`.

**SEVERITY: blocks-merge.** The premise that justifies the flip is false, and the remedy is
mis-scoped and unbudgeted.

---

### B-3 | EVAL §6.1 (X1–X4) and §9; DESIGN §9 — the pair still cannot be STAGED, on either branch

**WHAT IS WRONG.** Both documents treat "reach `(recurrence, equities_seq)`" as the success
criterion. Round 1 measured that the pair is unusable **after** it is reached, on **both**
deployment branches, and **neither document carries the finding** — not in X1–X4, not in Y1–Y8,
not in EVAL §9 "residual uncertainty", not in DESIGN §9 "what this does not fix".

**EVIDENCE.** `reports/2026-09-02_canopy-selection-deadlock/laneB3.md:378-386` states it as an
executed branch-exclusive matrix. Re-derived here:

| deployment | active backend after selecting recurrence | Apply Dataset with `equities_seq` |
| --- | --- | --- |
| `recurrence_service_url` **unset** (the code default, `src/settings.py:261`) | cascor `ServiceBackend` (`main.py:3705` no-ops) | `juniper-cascor/src/api/models/training.py:235` `Literal[...]` has **no `equities_seq`** → cascor rejects → canopy **502** (`main.py:3999`) |
| `recurrence_service_url` **set** (juniper-deploy) | `RecurrenceBackend` | `RecurrenceBackend` has **no `stage_dataset`** (executed: 20 public attrs, `hasattr → False`); `main.py:3995` calls it **unguarded** → `except Exception` at `:4001` → **500 + opaque `error_id`** |

Executed cross-check:

```
canopy DATASET_TYPES not in cascor StageDatasetRequest Literal: ['equities_seq']
hasattr(RecurrenceBackend,'stage_dataset')        = False
hasattr(RecurrenceBackend,'get_pending_dataset')  = False
```

DESIGN §4.2 changes `_apply_dataset_handler` — the *very* handler that hits this — and guards it
only for `⊥`. Nothing guards it for `equities_seq`.

**SEVERITY: blocks-merge.** The arc's own success criterion is not met by the shipped
recommendation, and the evidence was in the round-1 reports the fix pass was written from.

---

### B-4 | EVAL §5.3 row "FR9 makes gate-relaxation safe → REFUTED"; §5.4 (correction C4)

**WHAT IS WRONG.** C4 is itself an over-correction that **inverts a true claim**. §5.4 asserts
*"canopy sends a dataset REFERENCE not arrays, so **the model's rank check is not on this
path**"*. Measured: the service resolves the reference to arrays **itself**, inside the guarded
block, and rank-checks them there.

**EVIDENCE (executed).**

```
ValueError RAISED at load time: X_train must be 3-D (W, L, F) for a sequence artifact; got 2-D
```

Chain: `routers/training.py:49-57` calls `load_sequence_data` → `juniper_recurrence/data.py:78`
`sequence_data_from_arrays` → `juniper_recurrence_model/data.py:69-70`
`raise ValueError("X_{split} must be 3-D …")` → caught by
`routers/training.py:58 except (JuniperDataClientError, ValueError)` → `map_data_error`
(`routers/_common.py:49-52`) → **HTTP 422 "invalid dataset: …"**.

§5.4's structural read of `training.py` is accurate (`:47` outer `try` with `finally` only;
`:91` guarded by neither). But `:91` is **unreachable with a rank-mismatched artifact**, because
`:49-57` rejects it first. FR9 — *"the target model service validates the input shape it
receives and fails closed on mismatch"* (design of record §5.9,
`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md:191-196`) — **holds**.

§5.4 itself says *"the correction is load-bearing because FR9 was the argument that relaxing the
UI gate is safe."* Restoring FR9 restores that argument, which weakens the case against F2 —
i.e. weakens the flip.

**SEVERITY: blocks-merge.** A correction that the document flags as load-bearing is false, and
it is one of the pillars of C3.

---

## MUST FIX

### M-1 | EVAL §7, comparison table, row "Reaches the target pair"

Reads `F1: yes (3 clicks)` vs `F2: yes only when availability is permissive`. Measured (T2 vs
T3): **F1 also reaches it only when availability is permissive.** Under `equities_seq`
unavailable — the container case EVAL §6.3 calls "the realistic case" — F1 leaves
`(recurrence, equities_seq)` unreachable. The cell that most directly justifies the flip
over-claims for F1 and contradicts DESIGN §9 and EVAL §6.3. **Both cells should read the same
caveat**; the honest discriminator is *where you land when `enabled == []`*, not *whether you
arrive*.

### M-2 | EVAL §7 item 1 **and** DESIGN §4.1 — "all ten Python consumers and both JS consumers … are null-safe"

Three errors in one sentence, repeated verbatim in both documents.

1. **The count is nine.** `grep -n 'nn-dataset-type-dropdown' src/frontend/dashboard_manager.py`
   → 13 mentions, of which **9** are `Input(`/`State(`: `:2576 :2609 :2624 :2637 :2649 :4922
   :5153 :5210 :5285`. `laneB1.md:398-408` enumerates exactly those nine.
2. **They are not all null-safe.** `laneB1.md:405` marks site 6 (`_apply_dataset_handler`)
   **DEFECT — D-W1**, and `laneB1.md:443-449` says "8 of 9". D-W1 *is* X4 in the same document.
   The sentence therefore contradicts EVAL §6.1 X4 two sections away.
3. **There are zero JS consumers of that id.** `grep -rn "nn-dataset-type-dropdown"
   src/frontend/assets/*.js` → empty. EVAL §1.2 says so itself: *"zero hits for these ids across
   all six `assets/*.js`"*. B1's two JS sites guard `oneshot_start_body`, a different id.

### M-3 | EVAL §5.3 row "`task_type` conflict is live → REFUTED … canopy reads it nowhere" (correction C5)

Canopy reads `task_type` in the predicate the whole document is about:

- `src/model_registry.py:318` — `compatible()`: `… and dataset.task_type in model.supported_task_types and …`
- `:347` — `dataset_reason`: `if dataset.task_type not in model.supported_task_types`
- `:367` — `model_reason`: same

And EVAL §7.1 contradicts it directly: *"adopting juniper-data's `task_type` naively would make
`compatible_models(equities_seq) == []` and delete the very pair this work unblocks"* — which
is only possible **because** canopy reads it. The correct restatement is "canopy never reads
**juniper-data's** `task_type`, because `GeneratorInfo` omits it". As written, C5 over-corrects
into a false claim that the same document refutes.

### M-4 | DESIGN §5 row **G4**, EVAL §8 **G4**

Specified as *"canopy `DATASET_TYPES` ⊆ juniper-data `GENERATOR_REGISTRY` **by name**"*,
annotated **"passes today; guards drift"**. It **fails today** as specified:

```
canopy DATASET_TYPES : spirals xor mnist circles moons equities_seq
juniper-data keys     : spiral xor gaussian circles moon checkerboard csv_import equities
                        equities_seq multi_sine mackey_glass ar_p irregular_sine
                        delay_product mnist arc_agi
```

`spirals ∉ registry`, `moons ∉ registry`. The assertion must route through
`generator_name_for_type` first (executed: `spirals→'spiral'`, `moons→'moon'`) — which the
design never says. This is the *same* alias fact the arc reports as **X3**, so the guardrail
contradicts its own sibling finding. It is also the second guardrail in this arc specified at
the wrong level (cf. EVAL §5.2). Separately, G4 guards the wrong boundary for the newly-activated
path — the 502 in **B-3** is against **cascor's** `Literal`, which no proposed test covers.

### M-5 | DESIGN §5 row **G1b**

*"same BFS; assert `Reach ⊆ compatible` | passes today; **fails under F2**"*. Under the literal
definition it also **fails on PR 2's own change**: `⊥ ∉ DATASET_TYPES`, so every `(m, ⊥)` state
is outside `compatible` (measured: strict-invalid = 2 in T2/T3/T4, 3 in T6/T7). PR 2 must extend
`compatible` to admit `(m, ⊥)` for G1b to stay green — the definitional move DESIGN §2 makes in
prose but §5 never states as a test requirement. An implementer who writes G1b literally will
land PR 2 red and mistake it for a real violation.

### M-6 | DESIGN §4.3 second bullet — the "labelled backwards" correction is never carried

EVAL §2.2 records, as one of *"two corrections to earlier readings … because both were
load-bearing"*: *"The shipped conflict policy is labelled backwards … the snap at `:2702-2706`
keeps the model and moves the dataset — **model-primary** — while its docstring at `:2695` calls
it 'dataset-primary conflict policy, D5'."*

DESIGN then orders the implementer to *"Render the §5.6 notice … when the gate moves the
dataset, naming the old and new value"* — and contains **no decision, no mechanism line, and no
test** correcting the docstring. Verified still present:

```
docstring says: first enabled option (dataset-primary conflict policy, D5). Returns ``(no_update, no_update)``
```

An implementer reading `:2695` will write the notice for the wrong policy ("keeping your
dataset, clearing the model") — i.e. the correction's only consumer is left pointing at the
uncorrected source. A load-bearing correction that reaches no artifact is a dropped correction.

### M-7 | DESIGN §4.1 — "already built and already tested" over-claims; the ⊥ table states a falsehood

*"The destination state is **already built and already tested** … pinned by a passing regression
test whose comment already reads 'No dataset selected (e.g. cleared)'."*

The test is one assertion:

```python
# test_model_table.py:170-173
def test_table_without_a_dataset_treats_all_models_as_compatible():
    table = DashboardManager._build_model_selection_table(None, "cascor")
    assert all(button.disabled is False for button in _select_buttons(table))
```

It pins `disabled is False`. Nothing else about `⊥` is tested. Executed, the state it "already
built" **renders a positive falsehood**:

```
_build_model_selection_table(None,'cascor') select buttons: [('cascor', False, 'Currently active'), ('recurrence', False, 'Select this model')]
compatibility CELL text at a CLEARED dataset: ['✓ compatible', '✓ compatible']
```

`dashboard_manager.py:3033` (`reason = model_reason(...) if dataset is not None else None`) →
`:3034 is_compatible = True` → `:3041` renders **"✓ compatible"** for every model, including one
that is compatible with nothing available. DESIGN §4.3 says to *"replace the per-row reason"* at
`⊥` — there **is** no reason at `⊥`; there is a false affirmative. Under the arc's own N5/X1
standard ("a model whose displayed identity differs from the live backend is a defect, not a
display lag") this is the same class and is named nowhere.

This is also the arc reproducing the failure mode it diagnoses: EVAL §2.3 rejects
`TestOneshotBodyReachesAdapterEndToEnd` because it *"proves the pair works once you hold it and
never asks whether the UI can produce it"*. `test_model_table.py:170-173` proves the buttons are
enabled once you hold `None` and never asks whether the state is truthful.

### M-8 | DESIGN §10 **OQ-N1**; EVAL §5.5 first bullet — a question the round already answered

**This is the restored-and-reclosed pattern.** EVAL §5.5 records *"**Whether the newly-reachable
path invokes it is unresolved** and is the first thing the implementing PR must determine"*, and
DESIGN §10 OQ-N1 makes it a blocking gate on PR 2.

Round 1 answered it, twice, with executed evidence:

- `laneB3.md:344-358` — *"`RecurrenceBackend` has no `stage_dataset` → 500 — **CONFIRMED, but NOT
  on the Start path** … The 500 fires only if the user presses **Apply Dataset** (`:1345`),
  which is never suppressed for a one-shot model."*
- `laneB2.md:179-184` — `stage_dataset` listed among the methods `main.py` calls **unguarded**.

B1/B2 ("live blocker") and B3 ("OVERSTATED") are **not in conflict** — they are talking about
different controls. The fix pass collapsed a scope difference into a contradiction, declared it
unresolved, and shipped it as an open question. Re-derived here (B-3 evidence): `stage_dataset`
absent, `main.py:3995` unguarded, `except Exception` → 500. The answer is known; what is
missing is a *fix*, not a determination.

---

## SHOULD FIX

### S-1 | DESIGN §4.1 — the stated mechanism is not the mechanism

*"It works here and not under F2 because the user has **opened** the hole rather than the system
**overwriting** a choice."* The snap does not distinguish those cases. Executed:

```
'recurrence'   cur=None       enabled=['equities_seq'] -> value='equities_seq'
'recurrence'   cur='spirals'  enabled=['equities_seq'] -> value='equities_seq'
```

Identical behaviour. The real discriminator is the `or not enabled` branch: F2 lands there on a
*wrong pair*, F1 lands there on `⊥`. An implementer reasoning from the stated rationale will
build the wrong safeguard. (The second half of the sentence — the `State`-not-`Input` point at
`:2609` — is **correct** and verified.)

### S-2 | EVAL §7 table, row "Behaviour when `enabled == []`" — "unrecoverable" is asymmetric

F2's cell reads *"parks on an invalid pair, all options disabled, **unrecoverable**"*; F1's reads
*"user holds an explicit null; nothing invalid is entered"*. Measured
(`2026-09-02_canopy_bottom_oneway_check.py`), under the design's own G1d fixture:

```
ALL unavailable | from (cascor, BOTTOM): 2 states [('cascor','BOTTOM'), ('recurrence','BOTTOM')]
                | can LEAVE BOTTOM to a committed dataset? NO  <-- one-way door
```

`⊥` is a **one-way door** there: every dropdown option is disabled and the snap's
`or not enabled` branch returns `current`, so no dataset can ever be committed again in-page.
Symmetrically, F2's park is *also* escapable by page reload (`model-selection-store` is
`storage_type="memory"`, EVAL §1.1; the dropdown layout default is `DEFAULT_DATASET_TYPE`), so
"unrecoverable" over-states F2 by the same standard that under-states F1.

### S-3 | DESIGN N1 / N2 — residue of the omission narrative C1 refuted; and "regression" over-claims

- **Residue.** N2: *"it was **never descoped, only never built**"*; N1: *"the design of record's
  silence on reachability, which is **the root omission**"*. EVAL §2.2's own heading is *"The
  event — **a merged-PR regression, not an omission**"*. Two adjacent decision rows keep the
  refuted framing and cite §2.2 for it.
- **Over-claim.** C1 says *"the pair WAS reachable at `f464272`"* — true of *selection*, but the
  pair was never **usable**. Verified:

  ```
  f464272 (#395)  status="coming_soon"   nn-model-dropdown: 2   model-select-btn: 0
  442673e (#397)  status="coming_soon"   nn-model-dropdown: 1   model-select-btn: 4
  a96a114 (#400)  status -> "live"       2026-06-25 17:17:53    (descendant of 442673e)
  ```

  While the pair was reachable, `recurrence` was `coming_soon` → Start force-disabled by
  `model_is_trainable` (design of record §5.7). By the time it was `live` (#400) the ungated
  dropdown was already gone (#397). **`(recurrence, equities_seq)` has never been simultaneously
  reachable and trainable.** "A merged-PR regression" implies a lost capability; none existed.
  EVAL §2.2's own chain table contains both facts and never draws the conclusion.

### S-4 | DESIGN N2 / EVAL §7 table row "Design decisions" — "implements ratified D4/FR6" is half of D4

Design of record `…MODEL-DATASET-SELECTION-DESIGN.md:152-157` (§5.5) specifies **two**
affordances: *"Conventional **inline ✕** on the dataset dropdown … **and a 'clear model / show
all' reset on the surface**."* FR6 (`:73`) says *"Clear/reset **each** selection"*. The second
half is **NO ARTIFACT** — `laneB1.md:318` and `:483-484` say so explicitly (*"A complete D4 is
larger than one token"*) — and appears nowhere in DESIGN §3, §4, §5 or §7. EVAL §4's own family
definition includes it (*"`clearable=True` + 'show all models' reset"*) and §7's recommendation
drops it. Claiming F1 "**implements** ratified D4/FR6" against F2's "**amends** ratified D2/FR5"
is the table's decisive row and it over-claims.

### S-5 | DESIGN N7 vs §4.3 — F1 settles OQ-6 in a bugfix too

EVAL §7's table charges F2 with *"amends ratified D2/FR5 **and settles deferred OQ-6 inside a
bugfix**"*. DESIGN N7 answers *"OQ-6 remains open. This design does not choose a conflict-policy
default."* But §4.3 orders the D5 notice rendered on the snap, and the snap **is** model-primary
(EVAL §2.2). Shipping the user-visible notice for one policy entrenches it. The row is therefore
not discriminating in the way the flip relies on. Either N7 should acknowledge that §4.3
operationalises model-primary, or §4.3 should be deferred with OQ-6.

### S-6 | EVAL §5.4 — "fails on a name, not a shape" is contingent on a bug the same arc removes

*"The parked pair fails on a **name** (`{"generator": "spirals"}` versus juniper-data's
`"spiral"`), not a shape."* True today, and true only because of **X3**, which DESIGN §4.6
fixes in PR 3. After PR 3 the name resolves and the shape path is live. (It still fails
closed — see B-4 — so the conclusion survives, but the stated reason does not, and the document
presents it as a standing property.)

### S-7 | DESIGN §4.1 / EVAL §7 — F1 makes a deliberate clear indistinguishable from a desync

`dashboard_manager.py:3018` is `dataset = get_dataset_spec(dataset_value) if dataset_value else
None` — the **same** branch serves `⊥` and an unknown/stale value. Both are pinned by
adjacent tests with the same shape (`test_model_table.py:170-173` "e.g. cleared" and `:176-179`
"An unknown/stale dataset value … never grey every model"). Today that branch is a *desync
fallback*; F1 promotes it to a *user-facing state* without separating them, so a genuine
`FR15`-class desync now renders as a deliberate clear. Worth one predicate and one test.

### S-8 | DESIGN §7 phasing vs §6 sizing vs §10 OQ-N1

PR 2 carries `§4.1 + §4.2 + §4.3 + §4.7 + G1a–G1d` **and** a blocking unknown (OQ-N1, which
M-8 shows is already answered and is a *defect*, not an unknown). §6's budget (50–80 src) has no
line for a missing backend method, a `hasattr` guard, the Start-gate callback-signature change
(B-2), or the cascor `Literal` widening (B-3). §7 also says *"if PR 3 cannot land with PR 2, the
restart modal must be quarantined"* — but `restart-ds-type` is `clearable=False` at `:5422` and
its `.value` is seeded from the sidebar (`:5285`), so under F1 it can be seeded `None`; no
phase addresses that.

---

## NITS (citation drift — all followed by an implementer)

| # | doc | says | actual |
| --- | --- | --- | --- |
| N-1 | DESIGN §4.4 | `_select_model_handler` (`:2896`) | def is at **`:2876`**; `:2896` is `except Exception as exc:` inside it |
| N-2 | DESIGN §4.6, EVAL X3 | sibling `generator_name_for_type` at `:2769`, `:2836` | `:2769` ✓ and **`:2846`** |
| N-3 | DESIGN §4.2, EVAL X4 | `main.py:3993`'s `model_dump(exclude_none=True)` | `:3993` is `try:`; the call is **`:3994`** |
| N-4 | DESIGN §4.2, EVAL X4 | "the correct idiom already exists at `_restage_dataset:5623`" | `:5623` is a docstring line; the idiom is **`:5629-5631`** |
| N-5 | EVAL §5.4 | `47: try:` / `58: except` / `91: result = lifecycle.run(...)` | **all three verified exactly** — recorded as a re-derivation, not a finding |

---

## RE-DERIVATIONS THAT HELD (recorded so they are not re-litigated)

- **C7 coverage (both docs).** Sound. `juniper-coverage-gap-map`'s sub-module key is the POSIX
  **dirname**, non-recursive (`coverage_gap_mapper.py:123-124`), so `src/frontend` pools only its
  direct files. Measured with `coverage.parser`: `src/frontend/*.py` = **2086** statements
  (`components/` = 3317, a separate group). Slack to the 95% pooled bar at 96.34% =
  **28.0 statements** (docs say 27). `dashboard_manager.py` = 1870 statements → headroom to the
  90% per-file floor at 96.13% = **114.6** (docs say ~119). The gate is confirmed at
  `.github/workflows/ci.yml:255-261` (">=90 file / >=95 pooled").
- **DESIGN §4.1 traversal, all-available case.** Correct. Executed:
  `_gate_dataset_options_handler('recurrence', None) → ('…', 'equities_seq')`;
  `_build_model_selection_table(None, 'cascor')` → both Select buttons `disabled=False`;
  `_dataset_model_hint_handler(None) → ''`; `_resolve_oneshot_start_body_handler('one_shot',
  None) → None`. The `State`-not-`Input` point at `:2609` is verified.
- **DESIGN §4.1's unverified consumer.** `_render_dataset_params_handler(None)` (site `:2624`) is
  null-safe — executed → `('Current Dataset', {'display':'none'}, [P('No adjustable parameters —
  sensible generator defaults are used.')])`. Matches B1's D-W2 (cosmetic).
- **EVAL §5.2 / DESIGN §5 "G1 must live at handler level".** The injectability claim holds:
  `gated_dataset_options(model_key)`, `get_model_spec(key)`, `get_dataset_spec(value)` take no
  registry parameter, while `model_options`, `compatible_models`, `compatible_datasets` and
  `model_is_trainable` all do.
- **X1 / N5.** `src/settings.py:261 recurrence_service_url: Optional[str] = None` ✓;
  `main.py:3659-3671 _selection_targets_recurrence` requires the URL ✓; `:3705` no-ops the swap ✓.
- **X2.** `Output("restart-ds-type", "options")` exists nowhere; only `.value` is written
  (`:5268`); `:5422` is `clearable=False` with `options=gated_dataset_options(DEFAULT_MODEL_KEY)` ✓.
- **X4 / D-W1.** `:2845 payload: dict = {"nn_dataset_type": dataset_type}` unconditional ✓;
  `main.py:3994 exclude_none=True` ✓; `_restage_dataset` guards with `if dtype is not None` ✓.
- **EVAL §6.2.** `GENERATOR_REGISTRY` = **16** keys ✓; canopy seeds 6 ✓.
- **EVAL §2.2 git chain.** `f464272` → 2 `nn-model-dropdown` / 0 `model-select-btn`;
  `442673e` (#397) → 1 / 4; `clearable=False` present at `f464272` ✓.
