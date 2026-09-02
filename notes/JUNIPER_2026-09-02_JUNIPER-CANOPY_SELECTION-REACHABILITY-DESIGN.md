# Juniper-Canopy — Selection Reachability: Remediation Design

**Project**: Juniper — juniper-canopy
**Author**: Paul Calnon
**Date**: 2026-09-02
**Status**: Design of record for the remediation — open questions in §10
**Amends**: [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
**Evaluation of record**: [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md)

Guardrail identifiers **G1–G6** and defect identifiers **X1–X6 / Y1–Y9** are defined in the
evaluation document (its §8 and §6) and are used here with the same meaning.

---

## 1. Scope

Restore reachability of every compatible-and-available `(model, dataset)` pair in canopy's
selection UI, and land the companions that the restoration **activates**. The defect, its
measurement, the sixteen proposals and the two adversarial rounds that selected among them are in
the evaluation document; this document specifies what to build.

Out of scope, deliberately: relocating the capability model to the producing services (family F5
of the evaluation), and exposing the ten juniper-data generators canopy does not seed (its §6.2).
Both are recorded there as follow-on work.

---

## 2. The invariant this establishes

From §2.1 of the evaluation document, the shipped code enforces `I-safe` (every visited state is
compatible) and never stated `I-cover` (every compatible state is reachable). The remediation adds
`I-cover` **without weakening `I-safe`**:

> **I-safe** — no sequence of admitted transitions leaves the UI on a *committed* pair for which
> `compatible()` is False.
> **I-cover** — every pair that is both `compatible()` **and available** is reachable from the
> mount state.

**`I-cover` is conditioned on availability, and that condition is load-bearing.** A dataset whose
generator is unavailable is legitimately unreachable; §6.3 of the evaluation shows this is the
container's normal state, where the LMU has zero available datasets. An unconditioned `I-cover`
would be unsatisfiable by any UI change.

The rejected alternative (family F2) established `I-cover` **by breaking `I-safe`**: measured, it
created five reachable-but-invalid states while still failing to reach the target pair (evaluation
§5.1). That is the trade this design refuses.

The mechanism satisfying both is a **universal cut vertex**: a null dataset value `⊥`, compatible
with every model, joining every connected component of the compatibility graph.

**`⊥` is an incomplete state, not a valid one, and the distinction must be enforced rather than
assumed.** An earlier draft asserted `⊥` was "not trainable"; that is **false** as shipped —
`_update_button_appearance_handler` (`:7187`) takes `(self, button_states, model_key)` with no
dataset argument, and `:7206` gates Start solely on `model_is_trainable`. At `⊥` today,
`(recurrence, ⊥)` fails closed with a 409, but **`(cascor, ⊥)` sends the bare start POST and
trains on the last-staged dataset while the sidebar shows no dataset.** X5 (§4.8) closes this and
is a prerequisite of `⊥`, not an enhancement.

---

## 3. Decisions

| id | decision |
| --- | --- |
| **N1** | **Reachability is a stated invariant, not an emergent property.** `I-cover` and `I-safe` (§2) are written down, tested at handler level, and fail the build when violated. The design of record's silence on reachability is the root omission. |
| **N2** | **Restore the unset dataset state (implements ratified D4/FR6, in part).** `clearable=True` on the sidebar dataset dropdown. §5.5 of the design of record specifies **two** affordances; only the dropdown ✕ is in scope here (see OQ-N6). |
| **N3** | **The gate stays symmetric and hard (upholds D2/FR5 unchanged).** No `disabled` predicate is relaxed. Family F2 would have amended this, and both adversarial rounds rejected that amendment (evaluation §5.1, §7). |
| **N4** | **Name the consequence at the locus, in rendered content.** Never via `title=`, which §8 of the design of record rules out and which Y7 shows is a dead accessibility channel here. |
| **N5** | **A model whose displayed identity differs from the live backend is a defect, not a display lag.** The UI reads `swapped` and `backend`. Silent misattribution is worse than a blocked control for a benchmarking platform (X1). |
| **N6** | **Fail closed and say so.** The `ok=True`-then-fail-in-thread pattern (`recurrence_backend.py:154-156`) is not acceptable on a newly-reachable path. |
| **N7** | **OQ-6 remains open.** This design does not choose a conflict-policy default; it makes OQ-6 *answerable*, since under `clearable=False` both policies in §5.6 of the design of record were unimplementable — both say *clear*, and a null dataset was not expressible. |
| **N8** | **The empty compatible∩available set is an explicit state.** It renders a recovery affordance, never `no_update`. |
| **N9** | **A control that cannot be honoured is disabled at the control, not discovered at the backend.** Start requires a dataset (X5); Apply Dataset requires a dataset (X4). |

---

## 4. Mechanism

### 4.1 The clear affordance (N2)

`dashboard_manager.py:1334` — `clearable=False` → `clearable=True`.

The destination state is **already built and already tested**. Verified by execution:
`_build_model_selection_table(None, 'cascor')` returns both Select buttons `disabled=False`;
`_dataset_model_hint_handler(None)` returns `''`; `_resolve_oneshot_start_body_handler('one_shot',
None)` returns `None`. It is pinned by a passing regression test whose comment already reads *"No
dataset selected (e.g. cleared)"* (`test_model_table.py:170-173`). All **ten** Python consumers of
`nn-dataset-type-dropdown.value` are null-safe; there are **zero** JS consumers.

Traversal to the previously-unreachable pair, where the dataset is available:

```text
(cascor, spirals)  --clear dataset-->       (cascor, ⊥)
                   --Select Recurrence-->   (recurrence, ⊥)
                   --gate re-fires, enabled == ["equities_seq"] -->  (recurrence, equities_seq)
```

The third step is the existing snap at `:2702-2706`. Note the mechanism precisely: the snap
behaves identically whether the current value is `None` or `'spirals'` — what differs is where its
`or not enabled` branch leaves you. From `⊥` that branch leaves an *incomplete* selection; from a
concrete dataset it leaves a *complete but invalid* one. Clearing is also not itself re-gated,
because `gate_dataset_options` reads the dataset as `State` (`:2609`), not `Input`.

### 4.2 The null-dataset guard (X4)

`_apply_dataset_handler:2845` must not POST `{"nn_dataset_type": None}` — `main.py:3994`'s
`model_dump(exclude_none=True)` strips it into a vacuous 200 plus a false pending-banner. Guard it
and disable **Apply Dataset** at `⊥` (N9). The correct idiom already exists at
`_restage_dataset:5629-5631`.

### 4.3 Consequence naming (N4)

- **Fix the inverted docstring first.** `:2695` labels the snap "dataset-primary" when it is
  model-primary (evaluation §2.2). The notice is written from that description; correcting the
  artifact must precede writing UI copy from it.
- When the dataset is `⊥`, the model table's compatibility cell must **not** render "✓ compatible"
  for every model (Y9) — that is a positive falsehood. Render what the row *would* require.
- Render the §5.6 notice — the notice D5 always specified and the snap never shipped — when the
  gate moves the dataset, naming the old and new value.
- Both in rendered DOM content (N4). Give the reason cell an `id` and point the row's control at
  it with `aria-describedby` (Y7).

### 4.4 Model-state truth (N5 / X1)

`_select_model_handler` currently mirrors only `nn_model` and `execution` (`:2893`; def at
`:2876`). It must also read `swapped` and `backend`, and when `swapped is False` render the model
summary as **not active**, with the reason. Canopy's own test already pins the response shape
(`test_d8_d11_phase4_truth_up.py:64-82`).

**This ships first.** Unblocking selection without it converts the deadlock into silent benchmark
misattribution.

### 4.5 The restart modal (X2)

`restart-ds-type` has no writer for `.options` anywhere in the repo. Add
`Output("restart-ds-type", "options")` + `State("model-selection-store", "data")` to
`open_restart_confirm_modal` (`:5260-5293`), composing `apply_availability_gate` as the sidebar
does at `:2702`. Without this, the fix *activates* an inverted gate that `execute_restart`
forwards.

### 4.6 The generator alias (X3)

`_resolve_oneshot_start_body_handler` (`:2681`) must route its value through
`generator_name_for_type`, as both sibling handlers do (`:2769`, `:2846`).

### 4.7 The empty-set state (N8)

`_gate_dataset_options_handler`'s `if current_value in enabled or not enabled: return options,
dash.no_update` (`:2702-2706`) must distinguish its two arms. `not enabled` — no dataset is both
compatible and available — is a **recovery state**: clear the dataset to `⊥`, render why, and gate
Start.

### 4.8 Start requires a dataset (X5 / N9)

`_update_button_appearance_handler` (`:7187`, gate at `:7206`) must take the dataset value and
disable Start at `⊥`. This is a **callback-signature change** and is a prerequisite of §4.1, not an
enhancement — without it `(cascor, ⊥)` trains silently on a stale dataset (§2).

### 4.9 Staging the pair (X6)

Apply Dataset fails on both branches today: default deployment reaches cascor, whose `Literal`
(`juniper-cascor/src/api/models/training.py:235`) has no `equities_seq` → **502**; a configured
deployment reaches `RecurrenceBackend`, which has no `stage_dataset`, called unguarded at
`main.py:3995` → **500**. One-shot Start bypasses staging and is unaffected. Minimum: guard the
call site and surface a real message; full fix is a `stage_dataset` implementation.

---

## 5. Test plan

Specified to **fail on today's code**, which the guardrail everyone first proposed did not
(evaluation §5.2). Identifiers match the evaluation's §8.

| id | test | status before | status after |
| --- | --- | --- | --- |
| **G1a** | BFS the composed transition relation; assert `Reach ⊇ compatible ∩ available` | fails (5 of 6) | passes |
| **G1b** | same BFS; assert `Reach ⊆ compatible ∪ {(m, ⊥)}` | passes | passes — **fails under F2** |
| **G1c** | G1a/G1b over a synthetic **≥3-component** registry | fails (2 unreachable) | passes |
| **G1d** | G1a/G1b with an **injected all-unavailable** generator list | fails (parks) | passes **vacuously for `⊥`** — asserts the recovery state, not reachability |
| **G2** | no committed pair with `compatible()` False is reachable | passes | passes |
| **G3** | empty compatible∩available renders recovery, not `no_update` | fails | passes |
| **G4** | canopy `DATASET_TYPES` maps onto juniper-data `GENERATOR_REGISTRY` **through `generator_name_for_type`** | **fails** (`spirals`/`moons` are not keys) | passes |
| **G5** | model summary reflects `swapped is False` | fails | passes |
| **G6** | Start disabled at `⊥` | fails | passes |

Two specification notes that cost round 1 a defect each:

- **G1b needs `⊥` admitted explicitly.** `⊥` is not in `compatible()`, so a bare
  `Reach ⊆ compatible` fails on this design's own change. The `∪ {(m, ⊥)}` term is the whole
  difference between "incomplete" and "invalid" and must be in the assertion, not only the prose.
- **G1d cannot assert reachability.** With nothing available there is nothing to reach; it asserts
  the §4.7 recovery state instead. An earlier draft filed it under "must pass after", which is
  unsatisfiable.

**Enabling change**: **five** resolvers in `model_registry.py` lack an injectable parameter —
`gated_dataset_options` (`:408`), `get_model_spec` (`:264`), `get_dataset_spec` (`:276`),
`dataset_type_options` (`:200`) and `dataset_default_params` (`:209`) — while `compatible_models`,
`compatible_datasets` and `model_options` have one. G1c/G1d cannot be written without adding it,
and `dataset_default_params` is on G1's path via `:2682`. `_gate_dataset_options_handler` also
needs its generator list injectable, since it calls live HTTP and fails open under test.

**G1 must live at handler level.** Written over `model_registry` alone it goes green on the
deadlocked code — measured.

---

## 6. Sizing

B3's independent estimate, which corrected the proposal round's "~20 lines": **50–80 src +
150–250 test** for the narrow fix; **75–125 + 230–370** for the full arc; **three PRs**. Single-source
and not re-derived (evaluation §9). §4.8's signature change and §4.9 are additional to it.

Existing test sites to touch before a new test is written: 4 forced assertion inversions, 3
rendered vacuous, 1 premise destroyed, 4 callback-arity breaks — **12 sites across 2 files**.

**Coverage gate.** Measured twice, exit 0 both times; total 96.06%. The per-file 90% floor is
**not** binding (`dashboard_manager.py` is 95.46% branch-inclusive, the gate's own basis). The
binding constraint is the **`src/frontend` pooled 95% bar at 96.34% — 27 uncovered statements of
slack**. Note `src/backend/state_sync.py` sits at 87.38% below the file floor already; it is
untouched here but means the lane is not clean.

---

## 7. Phasing

| PR | contents | rationale |
| --- | --- | --- |
| **1** | §4.4 (X1 model-state truth) + **G5** | Must precede reachability. Independently correct; shippable alone. |
| **2** | §4.1 ✕ + §4.2 guard + §4.8 Start gate + §4.3 naming + §4.7 empty-set + **G1a–G1d, G3, G6** | The reachability fix and its invariant, landed together. **Land G1a red first**, then green it. §4.8 is a prerequisite, not a follow-up. |
| **3** | §4.5 restart modal + §4.6 alias + §4.9 staging + **G2, G4** | Activated by PR 2; smaller and independently reviewable. |

If PR 3 cannot land with PR 2, the restart modal must be **quarantined** (its dataset field
disabled) in PR 2 rather than left inverted.

---

## 8. Rollback

Each PR is independently revertible. PR 2's functional change is one keyword plus guards; a revert
restores the deadlock without leaving an inconsistent state. The invariant tests are the thing not
to revert — if a rollback is needed, mark G1 `xfail` with a reason rather than deleting it, so the
gap stays visible.

---

## 9. What this does not fix

- **The container has no equities generator at all** (evaluation §6.3): `yfinance` is absent from
  `juniper-data/requirements.lock`. In the deployed stack the LMU has zero *available* datasets
  regardless of this work. §4.7 makes that state legible rather than a silent park; it does not
  make the dataset available. Fixing it is a juniper-data packaging change.
- **Ten unseeded generators**, five of them rank-3 regression datasets that satisfy canopy's
  predicate against the LMU (evaluation §6.2). Whether the LMU can actually train on them
  end-to-end is **unvalidated** — the evaluation grades that claim OVERSTATED.
- **Y1–Y9** (evaluation §6.4), including further missing `RecurrenceBackend` methods — a count the
  round could not agree on (0 / 9 / 11 depending on baseline) and which is recorded as a lead, not
  a fact — and the vacuous snapshot save/restore.

---

## 10. Open questions

- **OQ-N1** — *(closed by round 2; retained for the record)* whether the newly-reachable path
  invokes `RecurrenceBackend.stage_dataset`. **It does not** — the failure fires on **Apply
  Dataset**; one-shot Start bypasses staging. Round 1 recorded this as unresolved dissent, which
  was itself an error: two reviewers were describing different controls. Carried as work item §4.9.
- **OQ-N2** — should `⊥` be the *mount* state rather than a transit state? It would make the first
  interaction an explicit choice and remove the seeded-default asymmetry, at the cost of an extra
  click for the common case and an FR15 interaction.
- **OQ-N3** — *(narrowed)* §4.8 settles that Start must be gated at `⊥`. Remaining: should Apply
  Dataset be disabled at `⊥` (§4.2 assumes yes), or should `⊥` be non-committable by construction?
- **OQ-N4** — is the §5.6 notice a toast, an inline alert, or a persistent annotation? N4 fixes the
  *locus*, not the form.
- **OQ-N5** — the browser falsifier is still open (evaluation §9): no agent clicked the greyed
  option in a live DOM, because canopy accepts TCP on 8050 but never responds. Cheapest remaining
  check.
- **OQ-N6** — D4's **second** affordance, the "clear model / show all" reset on the model surface
  (§5.5 of the design of record), is NO ARTIFACT and out of scope here. Ship it, or descope it on
  the record — it should not remain silently unbuilt a second time, which is how this defect
  arose.
