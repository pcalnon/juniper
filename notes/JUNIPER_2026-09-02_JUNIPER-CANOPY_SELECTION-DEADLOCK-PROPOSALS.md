# Juniper-Canopy — Model/Dataset Selection Deadlock: Proposals & Consensus Evaluation

**Project**: Juniper — juniper-canopy
**Author**: Paul Calnon
**Date**: 2026-09-02
**Status**: Evaluation complete — recommendation ratified through two adversarial rounds
**Design of record amended**: [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
**Companion**: [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) — the design that builds on §7's ratified proposal
**Raw evidence**: `reports/2026-09-02_canopy-selection-deadlock/` (12 agent reports, preserved verbatim)

---

## 1. The defect

To load the equities dataset you must already have a 3-D model selected. To select the 3-D
model you must already have the equities dataset selected. Each control greys the option that
would let you satisfy the other.

Concretely, from the seeded default `(cascor, spirals)`:

- the sidebar dataset dropdown disables every dataset incompatible with the **current model**
  (`model_registry.gated_dataset_options`), so `Equities (sequence)` renders as
  *"— needs a 3-D model"* and cannot be picked;
- the model-selection modal disables the Select button of every model incompatible with the
  **current dataset** (`dashboard_manager.py:3050`, `disabled=not is_compatible`), so
  `Recurrence (LMU)` renders as *"needs 3-D data"* and cannot be picked;
- neither side can be unset — the dropdown is `clearable=False` (`dashboard_manager.py:1334`)
  and `model-selection-store` is seeded to `cascor` (`:1842`).

### 1.1 Measured

Four Lane A instruments agree — three agents with distinct entry points plus the reconciler's
own probe (`util/ad-hoc/2026-09-02_canopy_selection_reachability.py`) — and all four proposal
authors plus the round-2 citation audit independently reproduced the same numbers:

| quantity | value |
| --- | --- |
| total `(model, dataset)` pairs | 12 |
| **compatible** per the registry predicate | 6 |
| **reachable** from `(cascor, spirals)` | **5** |
| **compatible but unreachable** | **1** — `(recurrence, equities_seq)` |
| edges in the reachable graph | 20 |
| of those, `pick-model` edges | **0** |

**Instrument adequacy**: 20 edges were found, so the probe demonstrably *can* report
reachability; a uniformly-disabled result is not a harness artifact.

The zero `pick-model` edges is the finding under the finding. It is not merely that one pair is
stranded — **the model axis is frozen**. Every performable "model change" is a self-selection
(`cascor`→`cascor`, `recurrence`→`recurrence`). The entire A1b model-selection surface — the
modal, its search box, the table, the per-row Select buttons — is unreachable machinery. It
renders; it cannot act.

Lane A1 added two properties from an independent BFS: the target pair is an **absorbing state
with zero out-edges** (the lock is symmetric — you could not return to `cascor` either), and
`model-selection-store` is `storage_type="memory"`, so a page reload reseeds to `cascor` and is
not an escape.

### 1.2 Sole writers (enumerated from `app.callback_map`, not by grep)

Lane A1 built the real `DashboardManager` and dumped all **175** registered callbacks:

- `nn-dataset-type-dropdown.value` — sole writer `gate_dataset_options` (`:2604`).
- `model-selection-store.data` — sole writer `select_model` (`:2590`), triggered only by the
  per-row Select buttons.

Cleared as escape routes: **zero** `dcc.Location` and **zero** `dcc.Link` across all 1162 layout
components (464 of which bear ids) — there is no URL routing at all; no clientside callback on
either id; zero hits for these ids across all six `assets/*.js` and all 29 inline
`clientside_callback` blocks; `POST /api/model/select` and `/api/stage_dataset` exist but nothing
reads back into the store; `demo_mode.py` contains the string "model" zero times; snapshots only
display `dataset_type`.

---

## 2. Root cause

### 2.1 The class — the mutual-gate trap

Lane P2's formalisation, which the evaluation adopts. Let `S = D × M`, with both transitions
**unilateral** (each control changes one coordinate) and **jointly guarded** (each control's
`disabled` predicate reads the peer's *current* value). A compatible state *is an edge* of the
bipartite compatibility graph `G` on `D ⊔ M`, and a unilateral move slides one endpoint along an
edge.

> **Confinement Lemma.** Unilateral transitions + jointly-guarded predicates + no unset value ⟹
> `Reach(s₀) = E(comp_G(s₀))` — the edge set of the starting state's connected component.

`G` has two components (`{5 rank-2 datasets} ⊔ {cascor}` and `{equities_seq} ⊔ {recurrence}`),
hence 5 of 6.

Three separately-reasonable conditions produce it: joint guards (D2/FR5 of the design of
record), unilateral transitions (its D7 two-surface split), and no clearable value. **Any two are
harmless; all three give the trap.** That is why each decision looked correct in isolation.

- **Invariant enforced**: `I-safe` — every visited state is compatible. Holds perfectly.
- **Invariant missing**: `I-cover` — every compatible state is reachable. Never stated, never
  tested.

Coverage is `|E(comp(s₀))| / |E(G)|`, so §6 of the design of record — which projects
dozens-to-hundreds of model variants — makes this **monotonically worse** with scale.

### 2.2 The event — a merged-PR regression

The evaluation's initial reading (that D4's unshipped ✕ was the root cause) was **refuted** by
Lane B3 and independently verified by the reconciler:

```text
f464272  (PR #395; dashboard_manager.py byte-identical at 442673e^ = c2058be, PR #396)
         dcc.Dropdown(id="nn-model-dropdown", …)   — model-select-btn occurrences: 0
442673e  (canopy #397)
         dropdown gone                             — model-select-btn occurrences: 4
```

(Counts are within `dashboard_manager.py`; repo-wide there are 10, of which 2 of the 4 in this
file are live wiring.)

`model_options()` emits no `disabled` key, so that dropdown was **ungated**. Selecting
`recurrence` fired the gate, `enabled` became `["equities_seq"]`, and the snap moved the dataset.
**`(recurrence, equities_seq)` was reachable before #397 and unreachable after.**

The chain, dated from git:

| when (local) | PR | effect |
| --- | --- | --- |
| 2026-04-05 | `31d458f` | the repo's first `clearable=False` |
| 2026-05-10 | `13a5856` | the sidebar dataset dropdown's `clearable=False` — **38 days before** the design that specifies D4 |
| 06-24 15:40:59 | **#393** | sidebar model dropdown ships **ungated** |
| 06-24 17:41:29 | **#394** | forward gate ships; PR body defers D4's ✕, reasoning that only the model→dataset direction is needed because the model is selected first — **true when written** |
| 06-25 07:29 | **#397** | ungated dropdown replaced by the gated table. Loop closes **13 h 48 m** after the deferral. Its body claims it swaps only the input side and every downstream gate follows for free — it audits what the input side **writes**, never what it is now **conditioned on** |
| 06-25 | **#400** (`a96a114`) | flips `recurrence` `coming_soon`→`live` |

(PR-body wording above is paraphrased; the verbatim quotes are in
`reports/2026-09-02_canopy-selection-deadlock/laneA3.md`.)

So D4 was never "dropped": it was a proposal to change a **pre-existing** property that every
later PR declared itself behaviour-preserving on. Nothing revisited #394's licence after #397
falsified it.

**Scope of the word "regression"** (round-2 refinement): `recurrence` was `coming_soon` at both
`f464272` and `442673e`, going `live` only at #400, a descendant of #397. So the pair was
reachable-but-not-trainable before #397 and trainable-but-not-reachable after. **No window
existed in which it was both.** The regression is of *reachability*, not of a working capability.

Two corrections to earlier readings, recorded because both were load-bearing:

- **§5.6 of the design of record — its premise is not false, but vacuously true and therefore
  inert.** "A newly selected
  option is never incompatible" holds precisely *because* incompatible options are disabled. No
  conflict can arise, so D5's conflict-resolution policy never fires; and that same vacuity is
  what makes the far component unreachable.
- **The shipped conflict policy is labelled backwards.** §5.6 of the design of record defines
  *dataset-primary* as "keep dataset, clear model" and *model-primary* as "keep model, clear
  dataset". The snap at `:2702-2706` keeps the model and moves the dataset — **model-primary** —
  while its docstring at `:2695` calls it "dataset-primary conflict policy, D5". The docstring is
  an artifact that must be corrected before any notice is written from it (see the companion
  design's §4.3).

### 2.3 Why it was not caught

Two independent masking layers, both known ecosystem failure classes:

1. **A blocked test row, not a missing one.** E2E journey **W8**
   (`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md:944`) specifies this
   exact click: step 2 asserts the Select is disabled, step 5 clicks it. Step 5 cannot run
   because of step 2. W8 was never executed — blocked `N-A` on the recurrence service being on
   the wrong port (`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:1756`). An
   *environmental* blocker masked a *UI* blocker.
2. **Vacuous unit passes.** `TestOneshotBodyReachesAdapterEndToEnd`
   (`test_oneshot_start_body.py:205-216`) passes `("one_shot", "equities_seq")` as **literal
   arguments** — it proves the pair works once you hold it and never asks whether the UI can
   produce it. `test_model_picker.py:56` calls `_select_model_handler("recurrence")` directly,
   bypassing the disabled button that *is* the gate.

**129 tests pass across the eight selection-relevant suites. The defect is fully protected by
green.**

Somebody did half-notice: §5.8 of the design of record gives the recovery copy as *"clear the
dataset"*; the shipped alert (`:3070-3074`) says *"switch the dataset in the sidebar"* — reworded
around an affordance that was never built. `test_model_table.py:171` even carries the comment
*"(e.g. cleared)"*.

---

## 3. Method

Sized per [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
§3. The working conclusion would **overturn a standing design of record** and a **fix hangs on
it** — two escalators — placing this in the top-right cell: **3+ Lane A with distinct entry
points, 2+ Lane B with opposing briefs, ≥2 iterations.**

| lane | agent | entry point / brief |
| --- | --- | --- |
| A | A1 | execute the shipped code; enumerate writers from `app.callback_map` |
| A | A2 | the **test suite read as a specification**; derive the contract from assertions alone |
| A | A3 | the **design of record + git history**; specified-vs-shipped delta |
| A | reconciler | own BFS probe (`util/ad-hoc/2026-09-02_canopy_selection_reachability.py`) |
| P | P1 | proposals — interaction design / accessibility lens |
| P | P2 | proposals — state machines, invariants, reachability |
| P | P3 | proposals — minimal-diff pragmatic engineering |
| P | P4 | proposals — architecture and scale |
| B | B1 | **refute**; opposing brief: *D4's ✕ is right and the consensus is wrong* |
| B | B2 | **refute by omission**; what did all seven miss? |
| B | B3 | **refute**; false authority, convenient conclusions, mis-sizing |
| R2 | R2-a | **round 2**, briefed only on the corrections: *find what they broke* |
| R2 | R2-b | **round 2**, citation and numeric audit against the repos |

Proposal authors were given the same verified evidence bundle and **no candidate direction**,
with different lenses to force genuine divergence rather than seven seats for one agent.

---

## 4. The proposals

Sixteen proposals were generated across four authors. They collapse into **five distinct
mechanisms**; the table gives each author's variant and rank.

| family | mechanism | P1 | P2 | P3 | P4 |
| --- | --- | --- | --- | --- | --- |
| **F1 — Restore the unset state** | Ship D4's ✕: `clearable=True` + a "clear model / show all" reset. Introduces the unconstrained state; `⊥` is a universal cut vertex | A (2nd) | P2-2 (3rd) | P-2 (2nd) | — |
| **F2 — Unary guard + peer repair** | The Select guard depends only on the model's own axis; the existing snap repairs the dataset | B (4th) | **P2-1 (1st)** | **P-1 (1st)** | **P4-A (1st)** |
| **F3 — Pair as the unit** | Row offers `Select with… ▾` naming the dataset it will switch to; both coordinates move atomically; nothing is disabled | **C (1st)** | P2-4 (2nd) | — | — |
| **F4 — Never disable; resolve on activation** | Nothing disabled; activating an incompatible item opens a resolution dialog | D (3rd) | P2-3 (4th) | P-3 (3rd) | — |
| **F5 — Relocate the capability model** | Source compatibility facts from the producing services rather than a hand-edited local registry | — | — | — | P4-B/C/D |

Full per-proposal strengths, weaknesses, risks and guardrails are in the preserved reports
(`reports/2026-09-02_canopy-selection-deadlock/proposal_P{1..4}_*.md`). §5 records what the
adversarial rounds did to them.

### 4.1 Where the authors converged, before review

- **Three of four picked F2**, and P2 and P3 arrived at the *identical line of code* from a
  formal-invariant lens and a minimal-diff lens respectively. P1's top pick (F3) is a richer
  presentation of the same move.
- **All four independently objected to the same flaw** — that the repair is **silent**. D5's own
  wording is "keep model, clear dataset **+ notice**"; the snap ships without the notice. P4
  conceded it outright: *"silence is the flaw, not the snap."*
- **All four demanded the same guardrail** — a reachability-closure property test, exercised over
  synthetic registries with **≥3 partition components**, because with the shipped 2-component
  partition a naive implementation of almost any proposal passes.
- **Three of four flagged that fixing this activates `restart-ds-type`** rather than leaving it
  dormant.

Per procedure §2, that convergence is **not** evidence — the authors shared an evidence bundle.
It is precisely what Lane B was commissioned to attack.

---

## 5. Consensus evaluation

### 5.1 The headline: F2 was rejected, and the rejection was independently reproduced

Lane B1's decisive refutation (**R1**): the unary predicate reads `compatible_datasets(model)` —
*pure* compatibility — while the runtime `enabled` list is
`apply_availability_gate(gated_dataset_options(...))` (`:2702-2703`), which is **strictly
narrower**. `equities_seq` is the only dataset compatible with `recurrence`, and it is gated on
juniper-data's optional `equities` extra. When availability empties the set, the snap takes its
`or not enabled → no_update` branch and **parks on an invalid pair with all six options
disabled**, leaving the user unable to repair it.

The reconciler simulated the candidate independently
(`util/ad-hoc/2026-09-02_canopy_unary_guard_simulation.py`), **before** B1 reported:

| scenario | reachable | compatible | compatible-but-unreachable | **reachable-but-INVALID** |
| --- | --- | --- | --- | --- |
| S1 today (joint guard) | 5 | 6 | `(recurrence, equities_seq)` | none |
| S2 unary guard, all available | 6 | 6 | none | none |
| **S3 unary guard, `equities_seq` unavailable** | 10 | 6 | `(recurrence, equities_seq)` | **5 states** |
| S4 3-component registry, today | 5 | 7 | 2 pairs | none |
| S5 3-component registry, unary guard | 7 | 7 | none | none |

S3 is the container case (§6.3). The proposed fix **creates the product's first five
reachable-but-invalid states and still fails to reach the target pair.** Two instruments, no
shared entry point, same conclusion.

**B1's amplification (R8) settles it.** `RecurrenceBackend.start_training:154-156` returns
`ok=True` immediately after `thread.start()`, so canopy reports **"Training started
successfully"**; the real failure dies in `_run_fit` and `_completion_reason_label:6308-6324`
maps only five *cascor* reasons, so nothing renders. The ✕ path lands on the other branch of the
same function — `:138-140` returns `ok=False` *before* any thread starts → 409 (pinned,
`test_recurrence_routes.py:164-171`) → a visible danger alert.

> **The ✕ fails closed and says so; the unary predicate fails open and says the opposite.**

This canopy-side fail-open is **independent of FR9** (§5.4): even though the service correctly
returns 422, canopy has already told the user training started.

### 5.2 The guardrail everyone agreed on was vacuous

Measured by the reconciler:

```text
cascor      enabled=['spirals','xor','mnist','circles','moons']  → naive assert passes
recurrence  enabled=['equities_seq']                             → naive assert passes
```

`gated_dataset_options` gates a model *in isolation*, and in isolation nothing is wrong. **The
deadlock exists only in the composition of the two gates.** A property written over the registry
— the obvious place — goes green on the deadlocked code.

Two structural reasons it cannot be written naively:

- **Five** resolvers in `model_registry.py` lack an injectable parameter —
  `gated_dataset_options` (`:408`), `get_model_spec` (`:264`), `get_dataset_spec` (`:276`),
  `dataset_type_options` (`:200`) and `dataset_default_params` (`:209`) — while
  `compatible_models`, `compatible_datasets` and `model_options` have one. A synthetic registry
  cannot drive the real gate. `dataset_default_params` matters because
  `_resolve_oneshot_start_body_handler` calls it at `:2682`.
- `_gate_dataset_options_handler` calls live HTTP `_fetch_generators()`; under test it fails →
  `[]` → fail-open all-available, so the guardrail **structurally cannot observe** the S3 branch.

### 5.3 Claims the adversarial rounds corrected

| claim | verdict | basis |
| --- | --- | --- |
| Deadlock; 5 of 6 pairs reachable | **CONFIRMED** | 4 Lane A instruments + 4 authors + R2-b |
| Root cause = D4's ✕ "never shipped" | **REFUTED** | regression at #397; reachable at `f464272` |
| "Regression" implies a lost working capability | **OVERSTATED** | never simultaneously reachable *and* trainable (§2.2) |
| §5.6 of the design of record is falsified | **REFUTED → restated** | vacuously true, so inert |
| "Let the existing snap repair it" | **REFUTED** | `no_update` when `enabled == []` |
| "~20 lines / 2–3 assertions / 1–2 PRs" | **REFUTED** | 50–80 src + 150–250 test, three PRs |
| The reachability guardrail | **VACUOUS as specified** | passes on today's code |
| `task_type` conflict is live | **REFUTED → restated** | see below |
| FR9 does not hold | **REFUTED in round 2** | §5.4 |
| "5× larger loss" (hidden generators) | **OVERSTATED** | count confirmed; end-to-end usability unvalidated |
| 6 of 16 generators; 5 rank-3 hidden | **CONFIRMED** | §6.2 |

On `task_type`, precisely: canopy **does** read `task_type` — its own registry's, in the
`compatible()` predicate (`model_registry.py:318`, `:347`, `:367`). What it does not read is
**juniper-data's**, which `GeneratorInfo` (`juniper-data/juniper_data/core/models.py:109-128`)
does not expose at all. The divergence — canopy calls `equities_seq` `regression`, juniper-data
calls it `classification` — is therefore **latent, not live**. It becomes live under family F5,
and adopting juniper-data's value naively would make `compatible_models(equities_seq) == []`,
deleting the very pair this work unblocks.

### 5.4 FR9 holds — a round-1 correction that round 2 reversed

Round 1 reported FR9 as refuted. **Round 2 refuted that refutation, by execution, and it is
right.** The chain on canopy's actual path:

```text
routers/training.py:48   try:
:49-57                     load_sequence_data(...)      ← resolves the reference AND loads arrays
                             juniper_recurrence_model/data.py:69-70
                               raise ValueError("X_train must be 3-D (W, L, F) …")
:58                      except (JuniperDataClientError, ValueError)
:59-60                     raise map_data_error(exc)    ← ValueError ⇒ 422
```

The rank check runs during **loading**, inside the guard — not during the fit at `:91`, which is
indeed unguarded but is not where canopy's path fails. So the service **does** fail closed with a
clean 422.

This is recorded rather than quietly fixed because the round-1 error was consequential: FR9 was
the argument that relaxing the UI gate is safe. Restoring it **weakens** the case against F2 — but
does not overturn it, because F2's defect is canopy-side (§5.1): canopy reports success before the
422 is ever received, and renders nothing when it arrives.

### 5.5 Dissent, and one false dissent

- **Resolved (was recorded as dissent).** B1/B2 treated the missing
  `RecurrenceBackend.stage_dataset` as a live blocker; B3 called it OVERSTATED. Round 2 found
  they were describing **different controls**: the failure fires on **Apply Dataset**, not on
  one-shot **Start**, which bypasses staging. Both were correct about their own control. The
  method's absence is verified (`RecurrenceBackend` has 20 methods; `stage_dataset` is not among
  them, while `demo_backend.py:347`, `service_backend.py:307` and
  `cascor_service_adapter.py:1524` define it). This is a **work item, not an open question** —
  recording it as unresolved was itself an error introduced by the round-1 fix pass.
- **Open.** Whether "the snap is dead code" is precisely stated. Confirmed in substance (0
  firings across all performable model changes), but `params-init-interval`
  (`max_intervals=1`, `:1871`) gives an availability-driven trigger. Both candidate fixes revive
  it.

---

## 6. Findings beyond the deadlock

### 6.1 Must land with the fix

| id | finding | evidence |
| --- | --- | --- |
| **X1** | **The `execution`/`swapped` mirror lies.** With `recurrence_service_url` unset (the code default, `settings.py:261`) `_swap_backend` no-ops, yet `POST /api/model/select` returns 200 with `swapped=False`. `_select_model_handler` mirrors only `nn_model` and `execution` (`:2893`), so the sidebar reports *"Active: Recurrence (LMU)"* **while cascor trains** — pinned by `test_d8_d11_phase4_truth_up.py:64-82`. **The deadlock is all that now prevents silent misattribution.** | B2-5, B3; verified |
| **X2** | **`restart-ds-type` is frozen to cascor forever.** `Output("restart-ds-type", "options")` exists **nowhere** in the repo; only `.value` is ever written (`:5268`). Once the pair is reachable the restart modal inverts — offering the five 2-D datasets **enabled** and `equities_seq` **disabled**, seeded with a value its own list disables — and `execute_restart` forwards it. Masked today by the very deadlock being fixed. | P1, P2, P3, P4, B1, B3; reconciler-verified |
| **X3** | **The one-shot body bypasses the generator alias.** `_resolve_oneshot_start_body_handler` (`:2681`) sends the **raw** dropdown value as juniper-data's `generator`, skipping `generator_name_for_type`, which both sibling handlers apply (`:2769`, `:2846`). Masked only because `equities_seq` is identity-mapped; `spirals` is not juniper-data's `spiral`. | B2-3, B1 |
| **X4** | **`clearable=True` needs a guard.** `_apply_dataset_handler:2845` would POST `{"nn_dataset_type": None}`, which `main.py:3994`'s `model_dump(exclude_none=True)` strips into a vacuous 200 plus a false pending-banner. The correct idiom already exists at `_restage_dataset:5629-5631`. | B1 (executed) |
| **X5** | **Start is not gated on the dataset.** `_update_button_appearance_handler` (`:7187`) takes `(self, button_states, model_key)` — no dataset argument — and `:7206` gates Start solely on `model_is_trainable`. Under F1 this leaves Start live at `⊥`: `(recurrence, ⊥)` fails closed with a 409, but **`(cascor, ⊥)` sends the bare start POST and trains on the last-staged dataset while the sidebar shows none** — the X1 class again. Closing it requires a callback-signature change. | R2-a (executed) |
| **X6** | **The pair cannot be staged on either branch.** Default deployment: backend stays cascor and `juniper-cascor/src/api/models/training.py:235`'s `Literal` has no `equities_seq` → **502**. Configured deployment: `RecurrenceBackend` lacks `stage_dataset` and `main.py:3995` calls it unguarded → **500** with an opaque error id. Fires on **Apply Dataset**, not on one-shot Start. | B3, B2; §5.5 |

### 6.2 Larger than the deadlock — the registry is 6 of 16

`GENERATOR_REGISTRY` (`juniper-data/juniper_data/api/routes/generators.py:44`) registers **16**
generators; canopy's `DATASET_TYPES` seeds **6**. Six carry `time_unit` (the temporal marker), of
which **five are rank-3 `regression` generators canopy never shows**: `multi_sine`,
`mackey_glass`, `ar_p`, `irregular_sine`, `delay_product`.

Rank confirmed rather than inferred: three of the five window through
`juniper_data/generators/_sequence.py:237` / `:329`, emitting `(W, L, F)`; `irregular_sine` and
`delay_product` bypass that module and are rank-3 by their own construction. Two of the five
(`irregular_sine`, `delay_product`) are explicitly **non-uniform Δt**, so they satisfy the LMU via
`requires_dt=True` rather than via the regular-Δt path.

Each satisfies canopy's own predicate against the LMU. **The recurrence model has six compatible
datasets in the platform and canopy exposes one — the one it cannot reach.**

B3's caveat is retained: the five are **unvalidated end-to-end**, so "5× larger" is a count, not
a measured loss. Exposing them may surface five more broken paths.

### 6.3 Environment-scoped: the container has no equities at all

`yfinance` appears only in `juniper-data/pyproject.toml:51` as an extra, never in
`requirements.lock`; the Dockerfile's own comment confirms the lock is compiled with
`--extra api --extra observability --extra mnist`.

| stack | `yfinance` | `equities_seq` availability | F2 outcome |
| --- | --- | --- | --- |
| local conda (`JuniperData`) | 1.4.1 installed | `available=true` | works |
| juniper-data down (fail-open) | n/a | treated available | works |
| **Docker / juniper-deploy** | **absent from lock** | **`available=false`** | **parks on an invalid pair** |

So in the deployed container the LMU has **zero available datasets**, independent of any UI fix.
This is what makes S3 the realistic case rather than a hypothetical.

### 6.4 Register of remaining separable defects

Reported once each and **not** re-derived by the reconciler — leads, not facts:

| id | finding | source |
| --- | --- | --- |
| Y1 | Further `RecurrenceBackend` methods missing beyond `stage_dataset` (count disputed: 0 against `BackendProtocol`, 9 against the Demo∩Service common surface, 11 against either concrete backend); `GET /api/admin/experimental_functions` runs on every page mount → 500 + a false "Could not reach backend" alert | B2-6 |
| Y2 | Snapshot save/restore on recurrence writes cascor meta-params and zero LMU state, reporting success at both ends (vacuous-pass class) | B2-7 |
| Y3 | FR15 unimplemented on the model axis: `current_nn_model` is write-only, no `GET /api/model`, `/api/train/status` omits `nn_model`; reload shows "Active: CasCor" over a recurrence backend | P1, P4, B2-4 |
| Y4 | Model swap strands `active_tab` on a deleted tab; `layout-state-store` restores it unvalidated | B2-8 |
| Y5 | The generators proxy sends no `X-API-Key` while `/v1/generators` is not exempt → schema-less 4-entry fallback → the LMU's only dataset renders "No adjustable parameters" | B2-9 |
| Y6 | No drift test between canopy's `DATASET_TYPES` and juniper-data's registry | B2-13 |
| Y7 | `title=` at `:3051` is a dead accessibility channel (the button has text content, so `title` never becomes its accessible name); zero `aria-*` attributes in `dashboard_manager.py`; dash 4.2.0's dropdown emits no `aria-disabled`, so D2's reason-in-the-label is by accident the only surviving accessible channel | P1 |
| Y8 | The `disabled` decision is computed through the *reason-string* helpers rather than through `compatible()` — a load-bearing predicate reached via presentation code | P2 |
| Y9 | At `⊥` the model table renders "✓ compatible" for **every** model — a positive falsehood, not merely a missing reason | R2-a (executed) |

Explicitly **refuted** by B2, so the arc need not re-spend on them: `regression_target` is not
inert; the deleted poll-gate output id is harmless; demo mode is not a one-way door;
`regenerate_dataset`/`import_dataset` are `hasattr`-guarded; the metrics panel does handle
one-shot regression.

---

## 7. Recommendation

**Ship F1 (D4's ✕), with F3's presentation borrowed, plus X1/X5 in the same arc. Do not ship
F2's unary predicate.**

Ratified against both adversarial rounds rather than the proposal round:

1. **`clearable=True` at `dashboard_manager.py:1334`**, plus the X4 guard at `:2845`. The target
   state is **already implemented** — `_build_model_selection_table(None, 'cascor')` returns both
   Select buttons enabled, and `_dataset_model_hint_handler` and
   `_resolve_oneshot_start_body_handler` both take `None` cleanly (reconciler-verified) — and is
   **already pinned by a passing regression test** whose comment reads *"No dataset selected
   (e.g. cleared)"* (`test_model_table.py:170-173`). B1 verified all **ten** Python consumers of
   the dropdown value are null-safe; there are **zero** JS consumers.
2. **Borrow F3's label and D5's notice** onto the ✕-enabled surface — name the consequence at the
   locus (D2's prescribed placement), not in a `title=` tooltip (which §8 of the design of record
   rules out and which Y7 shows is a dead channel here). Fix Y9 in the same change.
3. **X1 and X5 in the same arc, X1 first.** Unblocking selection without them converts a deadlock
   into silent misattribution — strictly worse for a platform whose purpose is measurement.
4. **X2 in the same PR or quarantined** — the fix activates it.
5. **X3, X6** — the alias call, and the staging path.

Why this and not F2, given three of four authors preferred F2:

| | F1 (✕) | F2 (unary guard) |
| --- | --- | --- |
| Reaches the target pair | yes (3 clicks) **where the dataset is available**; not in the container case | same availability limit, and creates invalid states besides |
| Behaviour when `enabled == []` | user holds an explicit null — **incomplete**, nothing invalid entered | **parks on a complete-but-invalid pair**, all options disabled, unrecoverable |
| Failure mode | fails **closed**: 409, visible alert | fails **open**: "Training started successfully", nothing rendered |
| Design decisions | **implements** ratified D4/FR6 (in part — see below) | **amends** ratified D2/FR5 and settles deferred OQ-6 inside a bugfix |
| Existing test delta | **0 assertions** changed | 3 minimum (8 on the broad reading) — and those three *are* D2/FR5 |
| Expresses | user intent | system inference over registry order |
| New hazard introduced | **X5** — Start live at `⊥` | 5 reachable-invalid states |

Neither candidate reaches the target pair in the container (§6.3); that is a juniper-data
packaging problem, not a UI one. What separates them is what happens when they cannot: F1 leaves
an *incomplete* selection that refuses, F2 leaves an *invalid* one that claims success.

F2's remaining defect is not fixable by tightening the predicate, because the predicate reads
pure compatibility while the runtime set is availability-narrowed. Closing that gap means making
the guard read the *availability-composed* set — at which point the guard is no longer unary and
the Confinement Lemma reapplies.

**F1 ships only half of D4.** §5.5 of the design of record specifies **two** affordances: the
dropdown ✕ *and* a "clear model / show all" reset on the model surface. Only the first is in
scope here; the second is **NO ARTIFACT** and is carried as an open question in the companion
design (its OQ-N6).

### 7.1 What is deferred, deliberately

- **OQ-6 (conflict-policy default)** stays open. F1 does not settle it — and B1's R9 notes the
  sharp irony that `clearable=False` currently makes **both** policies in §5.6 of the design of
  record unimplementable, since
  both say *clear* and a null dataset is not expressible. Shipping the ✕ is what makes OQ-6
  answerable at all.
- **F5 (relocating the capability model)** is correctly scoped as the end-state the defect
  revealed, not the fix for it. P4 named its own over-scoping: a perfect capability feed still
  yields a disconnected graph without a connectivity fix. Note the §5.3 landmine.
- **§6.2's five hidden generators** — real, counted, unvalidated end-to-end.

---

## 8. Guardrails

Stated so they can be implemented, and specified to **fail on today's code** — the property
everyone's first draft lacked. The companion design implements these under the same identifiers.

- **G1 — reachability closure (the one that would have caught this).** BFS the `(model, dataset)`
  state graph under the **composed** transition relation and assert both
  `Reach(s₀) ⊇ {compatible ∩ available pairs}` and `Reach(s₀) ⊆ {compatible pairs} ∪ {(m, ⊥)}`
  (the second arm is what catches F2's parking; the `⊥` term is what F1 legitimately adds). It
  must be written at **handler** level, not registry level (§5.2), with the generator list
  **injected**, and exercised over a synthetic **≥3-component** registry and an **all-unavailable**
  case. Requires the five injectability changes in §5.2.
- **G2 — no reachable-invalid state.** No sequence of admitted transitions may leave the UI on a
  pair for which `compatible()` is False.
- **G3 — availability composition.** The empty compatible∩available set renders an explicit
  recovery state rather than `no_update`.
- **G4 — registry drift.** Canopy's `DATASET_TYPES` must map onto juniper-data's
  `GENERATOR_REGISTRY` **through `generator_name_for_type`** — a bare name comparison **fails
  today** (`spirals` and `moons` are not registry keys; `spiral` and `moon` are), which is X3 in
  another guise (Y6).
- **G5 — model-state truth.** The sidebar's displayed model equals the live backend's model
  (X1, Y3).
- **G6 — Start requires a dataset.** Start is disabled whenever the dataset is `⊥` (X5).

**Coverage constraint.** The lane was run twice — by B3, who self-corrected an earlier claim by
measuring, and independently in round 2. Exit 0 both times; total **96.06%**.

`coverage` runs with `branch = true` (`pyproject.toml:414`) and the gate
(`coverage_gap_mapper.parse_coverage_json`) reads the **branch-inclusive** `percent_covered` per
file. On that basis `dashboard_manager.py` is **95.46%** (1756 statements, 68 missing) — not the
96.13% `percent_statements_covered` figure, which is a different basis and must not be set beside
the branch-inclusive total. Either way it clears the per-file 90% floor comfortably, so **that
floor is not the binding constraint**.

The binding gate is the **`src/frontend` pooled 95% bar, at 96.34% across 10 files / 1965
statements — 27 uncovered statements of slack** — invisible from any single file's number.
Grouping is non-recursive (`coverage_gap_mapper.py:123-124`).

One correction to "the lane is clean": on the gate's own basis `src/backend/state_sync.py` is
**87.38%**, below the 90% file floor. It is untouched by this remediation and does not block it,
but the lane is not clean as previously asserted. Figures are n=1, Python 3.13, without `h5py` /
`.[juniper-cascor]`.

---

## 9. Residual uncertainty

Stated explicitly per procedure §5.4.

- **No browser run.** Canopy accepts TCP on 8050 but never responds (`curl` and a real browser
  navigation both time out; juniper-data on 8100 refuses immediately). No agent clicked the greyed
  option in a live DOM. Mitigating evidence: the user's screenshots show the disabled rendering,
  and A1 confirmed `disabled: true` reaches the wire on both controls via `to_plotly_json()`.
  **This is the cheapest remaining falsifier and it is still open.**
- **Sizing** (§5.3) is a single-source Lane-B3 estimate, not re-derived.
- **Y1's method count is disputed** (0 / 9 / 11 depending on the baseline); Y2–Y9 are
  single-source leads.
- **The five hidden generators** — counted, not exercised (§6.2).
- **Coverage** — n=1 lane; arithmetic re-derives from the stated inputs but the lane was not
  independently re-run to completion.
- **No artifact shows D4 was deliberately descoped** — only #394's deferral note, which nothing
  answers.

---

## 10. Validation record

- **Lane A (2026-09-02)** — 3 agents, distinct entry points (executed code + `callback_map`;
  test-suite-as-spec; design/git delta) plus the reconciler's own probe. All four confirm 5-of-6
  reachability. Two corrected the reconciler (the §5.6 vacuity, and the inverted policy label —
  both in the design of record).
- **Proposal round** — 4 agents, different lenses, no seeded direction. 16 proposals → 5 families.
  Convergence noted and explicitly **not** treated as evidence.
- **Lane B** — 3 agents, opposing briefs. Overturned the proposal consensus (§5.1), found the
  agreed guardrail vacuous (§5.2), corrected the root-cause narrative (§2.2), and resized the work
  (§5.3). B3 self-refuted its own coverage claim by measuring it. B1's brief survived its own
  adversarial test.
- **Round 2** — 2 agents, briefed on the **corrections** rather than the documents (procedure §4).
  Reversed the round-1 FR9 refutation (§5.4); found `I-cover` unsatisfiable as first stated and
  `⊥` trainable (X5); found the staging blocker absent from both documents (X6); identified a
  **restored-and-reclosed question** (§5.5) — the exact failure mode procedure §4 predicts of a
  fix pass; and corrected five citations, seven numeric claims and a guardrail-identifier
  collision.
- **Reconciler re-derivations** — every load-bearing lone finding re-derived independently:
  reachability; the dead snap; the null-state implementation; the inverted policy label;
  `restart-ds-type` having no `.options` writer; `clearable=True` never existing on any branch;
  the 16-vs-6 generator count; the `task_type` divergence and `GeneratorInfo`'s omission of it;
  `RecurrenceBackend`'s missing method; the `swapped=False` pinning test; the vacuous guardrail;
  FR9's actual guarded path; the fail-closed/fail-open branches of `start_training`; and the F2
  simulation that reproduced B1's R1 before B1 reported.
- **Termination** — round 2 changed dispositions (F1's hazards, the FR9 reversal, X5/X6), so its
  own corrections are carried into the companion design's open questions rather than being
  declared settled here.

---

## 11. References

- [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md) — the design of record this amends (D2, D4, D5, D7, D8; §5.3–§5.9; §6; §8; FR5/FR6/FR9/FR15; OQ-6).
- [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) — the review procedure and its sizing table.
- [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md) — journey W8 at line 944, which specifies this exact click.
- [`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md) — W8's `N-A` blocking, at line 1756.
- Reconciler instruments: `util/ad-hoc/2026-09-02_canopy_selection_reachability.py` (§1.1), `util/ad-hoc/2026-09-02_canopy_snap_and_null_state.py` (the dead snap + null state), `util/ad-hoc/2026-09-02_canopy_unary_guard_simulation.py` (§5.1's S1–S5 table).
- Reviewer instruments, retained for re-derivation: `util/ad-hoc/2026-09-02_canopy_model_dataset_reachability_probe.py` (Lane A2), `util/ad-hoc/2026-09-02_canopy_clearable_f1_simulation.py` and `util/ad-hoc/2026-09-02_canopy_bottom_oneway_check.py` (round 2 — the F1 simulation behind X5 and the `⊥` one-way-door check), `util/ad-hoc/2026-09-02_canopy_round2_null_state_probe.py`.
- Raw agent reports: `reports/2026-09-02_canopy-selection-deadlock/`.
- Canopy anchors: `src/model_registry.py`; `src/frontend/dashboard_manager.py:1334`, `:1842`, `:2681`, `:2702-2706`, `:2845`, `:2893`, `:3050`, `:5268`, `:5422`, `:5629-5631`, `:7187`, `:7206`; `src/backend/recurrence_backend.py:138-156`; `src/main.py:3994`.
