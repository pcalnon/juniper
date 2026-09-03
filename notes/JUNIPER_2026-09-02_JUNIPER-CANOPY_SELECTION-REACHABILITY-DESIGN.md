# Juniper-Canopy — Selection Reachability: Remediation Design

- **Project**: Juniper — juniper-canopy
- **Author**: Paul Calnon
- **Date**: 2026-09-02
- **Status**: Design of record for the remediation — §10 answered and dispositioned (2026-09-02); scope extended to iteration 2 (§12)
- **Amends**: [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
- **Evaluation of record**: [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md)

Guardrail identifiers **G1–G6** and defect identifiers **X1–X6 / Y1–Y9** are defined in the
evaluation document (its §8 and §6) and are used here with the same meaning. **G7–G11** and
decisions **N10–N13** are introduced here, when the §10 open questions were answered.

---

## 1. Scope

Restore reachability of every compatible-and-available `(model, dataset)` pair in canopy's
selection UI, and land the companions that the restoration **activates**. The defect, its
measurement, the sixteen proposals and the two adversarial rounds that selected among them are in
the evaluation document; this document specifies what to build.

**Scope revision (2026-09-02, §11).** The ten unseeded juniper-data generators are **in scope for
this arc**, as iteration 2 — specified in §12. The stated goal is a platform without gaps in
required functionality, and a research platform that exposes 6 of its 16 datasets has a capability
gap of the same standing as a workflow defect.

One refinement to that framing, which changes sequencing rather than scope: the missing generators
are a **capability gap**, while X1 is a **correctness defect**. A missing dataset is visible and
safe; a misreported model is invisible and unsafe, because it silently corrupts the provenance of
a benchmark result. Both ship in this arc; correctness-of-reporting leads (§7).

Out of scope, deliberately: relocating the capability model to the producing services (family F5
of the evaluation), which remains follow-on work.

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

| id     | decision                                                                                                                                                                                                                                                               |
|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **N1** | **Reachability is a stated invariant, not an emergent property.** `I-cover` and `I-safe` (§2) are written down, tested at handler level, and fail the build when violated. The design of record's silence on reachability is the root omission.                        |
| **N2** | **Restore the unset dataset state (implements ratified D4/FR6, in part).** `clearable=True` on the sidebar dataset dropdown. §5.5 of the design of record specifies **two** affordances; only the dropdown ✕ is in scope here (see OQ-N6).                             |
| **N3** | **The gate stays symmetric and hard (upholds D2/FR5 unchanged).** No `disabled` predicate is relaxed. Family F2 would have amended this, and both adversarial rounds rejected that amendment (evaluation §5.1, §7).                                                    |
| **N4** | **Name the consequence at the locus, in rendered content.** Never via `title=`, which §8 of the design of record rules out and which Y7 shows is a dead accessibility channel here.                                                                                    |
| **N5** | **A model whose displayed identity differs from the live backend is a defect, not a display lag.** The UI reads `swapped` and `backend`. Silent misattribution is worse than a blocked control for a benchmarking platform (X1).                                       |
| **N6** | **Fail closed and say so.** The `ok=True`-then-fail-in-thread pattern (`recurrence_backend.py:154-156`) is not acceptable on a newly-reachable path.                                                                                                                   |
| **N7** | **OQ-6 remains open.** This design does not choose a conflict-policy default; it makes OQ-6 *answerable*, since under `clearable=False` both policies in §5.6 of the design of record were unimplementable — both say *clear*, and a null dataset was not expressible. |
| **N8** | **The empty compatible∩available set is an explicit state.** It renders a recovery affordance, never `no_update`.                                                                                                                                                      |
| **N9** | **A control that cannot be honoured is disabled at the control, not discovered at the backend.** Start requires a dataset (X5); Apply Dataset requires a dataset (X4).                                                                                                 |

Decisions **N10–N13** were added 2026-09-02 when the §10 open questions were answered. Each
records a prerequisite the answer needs in order not to reintroduce the defect class this design
exists to close.

| id | decision |
|-----|----------|
| **N10** | **`⊥` at mount requires backend hydration first.** The dataset axis becomes unset-by-default (OQ-N2) **only once canopy hydrates it from the backend**. Without that, `⊥`-at-mount converts a usually-correct default into a post-reload state where Start and Apply Dataset are both disabled over a staged, ready backend — the X1 class on the dataset axis (§4.10). |
| **N11** | **Both axes are clearable, and a cleared axis ungates its peer.** OQ-N6 ships the "clear model / show all" reset. A cleared model must render **ungated** dataset options; today the handler early-returns `no_update` and would freeze the dropdown at the previous model's gate (§4.11). |
| **N12** | **A transient notice and a blocking state are different channels.** A successful gate repair is a **toast**; an unresolvable empty compatible∩available set is a **persistent inline alert**. Neither replaces N4's rendered annotation at the locus, because a toast alone is invisible to assistive technology (§4.3). |
| **N13** | **Demo mode dogfoods the platform, and degrades loudly.** It keeps auto-loading the default spiral dataset and continues to source it from juniper-data; the local generator survives only as a **visibly announced** degraded mode, never a silent parallel implementation (§4.12). |

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
- **Two events, two channels (N12).** OQ-N4 asked for "a toast when the gate fails and a persistent
  error until the situation is resolved". Those are two different events and the split is what
  makes the answer coherent:

  | event | nature | channel |
  |-------|--------|---------|
  | the gate **successfully** moved the dataset (D5's notice) | informational; nothing to resolve | **toast**, auto-dismissing |
  | compatible ∩ available is **empty** (§4.7) | blocking; resolvable | **persistent inline alert**, cleared only by resolution |

  "Persistent until resolved" only applies to the second — the first is not a situation to resolve.
  Two practicalities: canopy has **zero** `Toast` components today, so this is new surface carrying
  its own dismiss / stacking / timer state; and a toast without `role="status"` / `aria-live` is
  invisible to assistive technology (Y7 records zero `aria-*` attributes in `dashboard_manager.py`).
  The toast therefore **supplements** the rendered annotation at the locus; it must not be the only
  channel, or the notice is an accessibility regression against simply rendering it inline.
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

### 4.10 Dataset-axis hydration — the prerequisite for `⊥` at mount (N10 / OQ-N2)

**Measured**: canopy has *never* hydrated the dataset from the backend. There is no
dataset-hydration callback, and `GET /api/train/status` carries no dataset field —
`nn_dataset_type` (`main.py:3971`) is a *request* model. The mount value is purely the layout
default.

Today that divergence is masked, because `spirals` is also the backend's default: the UI is right
by coincidence. Setting mount to `⊥` does not remove the divergence, it **changes its failure
mode** — after any mid-session reload the UI shows no dataset and, by N9 (X4 + X5), *both* Start
and Apply Dataset are disabled, over a backend that is staged and ready. Recovering requires
re-selecting and re-applying, which re-stages and can reset training state.

That is X1's class on the dataset axis, so it gets X1's remedy: extend the model-state hydration of
§4.4 to the dataset axis (`GET /api/train/status`, or a sibling route, must report the staged
dataset; canopy seeds the dropdown from it at mount). With hydration in place, `⊥` appears **only
when the backend genuinely has nothing staged** — which is the honest reading of OQ-N2, strictly
better than today, and free of the reload regression.

**Ordering is not negotiable**: hydration lands *before* `⊥` becomes the mount state (§7).

### 4.11 Clearing the model must ungate the dataset (N11 / OQ-N6)

OQ-N6 ships §5.5's second affordance, the "clear model / show all" reset. The registry is already
correct — `gated_dataset_options(None)` returns all six datasets enabled (executed). The handler is
not:

```text
_gate_dataset_options_handler:
    if not model_key:
        return dash.no_update, dash.no_update     # <- options stay frozen at the OLD model's gate
```

So clearing the model to escape a constraint would leave that constraint in force: the dataset
dropdown keeps the previous model's disabled set. **That is the mutual-gate trap again, on the
model axis** — a defect this design exists to prevent, shipped by the affordance meant to relieve
it. The early return must instead render ungated options composed with `apply_availability_gate`.

Consequence worth recording: with **both** axes clearable, OQ-6 becomes fully answerable for the
first time. §5.6's *dataset-primary* policy ("keep dataset, clear model") is finally expressible,
where under `clearable=False` neither policy was.

### 4.12 Demo mode (N13 / OQ-N2)

Demo mode keeps auto-loading the default spiral dataset — `⊥`-at-mount is for normal operation
only. Its dogfooding is largely already true: `demo_mode.py:551-554` calls juniper-data first
(`_generate_spiral_dataset`) and only falls back to `_generate_spiral_dataset_local` on exception.

The demo-only code to minimise is that fallback. It should **not** simply be deleted: its own
comment names its purpose ("Docker standalone, CI smoke test"), and removing it makes demo mode
hard-depend on juniper-data being reachable. Instead it must **degrade loudly** — a visible
degraded-mode banner whenever the local generator is used — so demo mode never *quietly* runs on
non-platform data. That satisfies the stated intent (no silent divergence from the platform) without
breaking standalone or CI.

---

## 5. Test plan

Specified to **fail on today's code**, which the guardrail everyone first proposed did not
(evaluation §5.2). Identifiers match the evaluation's §8.

| id      | test                                                                                                     | status before                              | status after                                                                |
|---------|----------------------------------------------------------------------------------------------------------|--------------------------------------------|-----------------------------------------------------------------------------|
| **G1a** | BFS the composed transition relation; assert `Reach ⊇ compatible ∩ available`                            | fails (5 of 6)                             | passes                                                                      |
| **G1b** | same BFS; assert `Reach ⊆ compatible ∪ {(m, ⊥)}`                                                         | passes                                     | passes — **fails under F2**                                                 |
| **G1c** | G1a/G1b over a synthetic **≥3-component** registry                                                       | fails (2 unreachable)                      | passes                                                                      |
| **G1d** | G1a/G1b with an **injected all-unavailable** generator list                                              | fails (parks)                              | passes **vacuously for `⊥`** — asserts the recovery state, not reachability |
| **G2**  | no committed pair with `compatible()` False is reachable                                                 | passes                                     | passes                                                                      |
| **G3**  | empty compatible∩available renders recovery, not `no_update`                                             | fails                                      | passes                                                                      |
| **G4**  | canopy `DATASET_TYPES` maps onto juniper-data `GENERATOR_REGISTRY` **through `generator_name_for_type`** | **fails** (`spirals`/`moons` are not keys) | passes                                                                      |
| **G5**  | model summary reflects `swapped is False`                                                                | fails                                      | passes                                                                      |
| **G6**  | Start disabled at `⊥`                                                                                    | fails                                      | passes                                                                      |
| **G7**  | the mount dataset value equals the backend's staged dataset (§4.10)                                      | **fails** — no hydration exists at all     | passes                                                                      |
| **G8**  | a **cleared model** renders ungated dataset options, not `no_update` (§4.11)                             | **fails** — options freeze at the old gate | passes                                                                      |
| **G9**  | demo mode's local-generator fallback is visibly announced (§4.12)                                        | **fails** — degrades silently              | passes                                                                      |
| **G10** | every juniper-data generator is either seeded in `DATASET_TYPES` or on a named exclusion list (§12)       | **fails** — 10 unseeded, none excluded     | passes                                                                      |
| **G11** | every seeded generator has bounded `default_params` (§12)                                                | fails for any new seed without them        | passes                                                                      |

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
150–250 test** for the narrow fix; **75–125 + 230–370** for the full arc. Single-source and not
re-derived (evaluation §9).

That estimate predates the §10 answers and the §11 scope revision, and it costed **three** PRs. It
does not include: §4.8's callback-signature change, §4.9 staging, §4.10 hydration (a new route or
route field plus a mount callback), §4.11, the §4.3 toast surface (new to canopy), §4.12, or any of
§12. The arc is now **five PRs plus a parallel packaging workstream** (§7), and the estimate should
be treated as a floor for PRs 3–4 only, not as a total. It is deliberately not re-estimated here —
inventing a precise number for work this under-specified would be false authority of the kind
round 2 was commissioned to catch.

Existing test sites to touch before a new test is written: 4 forced assertion inversions, 3
rendered vacuous, 1 premise destroyed, 4 callback-arity breaks — **12 sites across 2 files**.

**Coverage gate.** Measured twice, exit 0 both times; total 96.06%. The per-file 90% floor is
**not** binding (`dashboard_manager.py` is 95.46% branch-inclusive, the gate's own basis). The
binding constraint is the **`src/frontend` pooled 95% bar at 96.34% — 27 uncovered statements of
slack**. Note `src/backend/state_sync.py` sits at 87.38% below the file floor already; it is
untouched here but means the lane is not clean.

---

## 7. Phasing

Revised 2026-09-02 for the §10 answers and the §11 scope revision. Five PRs plus one parallel
workstream. The ordering principle is that **truth-telling precedes reach, and reach precedes
breadth** — a UI that misreports which model produced a result is a worse platform than one with
fewer datasets, because its output is wrong rather than absent.

| PR    | contents                                                                                            | rationale                                                                                                                                |
|-------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| **1** | §4.4 (X1 model-state truth) + **G5**                                                                | Correctness of reporting leads. Independently correct; shippable alone.                                                                  |
| **2** | §4.10 hydration, **both** axes (X1's dataset-side sibling, Y3) + **G7**                              | Prerequisite for `⊥`-at-mount. Landing it separately keeps the reload regression from ever existing (N10).                                |
| **3** | §4.1 ✕ + §4.11 model clear + §4.2 / §4.8 guards + §4.3 naming and channels + §4.7 empty-set + **G1a–G1d, G3, G6, G8** | The reachability fix proper, now with both axes clearable. **Land G1a red first**, then green it. §4.8 and §4.11 are prerequisites, not follow-ups. |
| **4** | §4.5 restart modal + §4.6 alias + §4.9 staging + **G2, G4**                                         | Activated by PR 3; smaller and independently reviewable.                                                                                 |
| **5** | §12 generator expansion — Y5 first, then the seeds + `default_params` + the `mackey_glass` seed flag + **G10, G11** | Iteration 2 (§11). Depends on PRs 1–2 for honest attribution and on Y5 for a usable params panel.                                          |
| **∥** | juniper-data packaging: the `equities` extra into `requirements.lock`, and any other extra a newly-seeded generator needs | Parallel and non-blocking. Without it several datasets are correctly `available=false` in the container (§9).                              |

§4.12 (demo mode, **G9**) rides with PR 3, since `⊥`-at-mount is what makes demo mode's behaviour
a distinguishable case.

If PR 4 cannot land with PR 3, the restart modal must be **quarantined** (its dataset field
disabled) in PR 3 rather than left inverted.

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
- ~~**Ten unseeded generators**~~ — **moved into scope** as iteration 2 by the §11 revision;
  specified in §12. The caveat stands and is carried there: whether the LMU can actually train on
  the five rank-3 generators end-to-end is **unvalidated**, and the evaluation grades the
  "5× larger" framing OVERSTATED. §12 therefore treats validation as part of the work, not an
  assumption.
- **Y1–Y9** (evaluation §6.4), including further missing `RecurrenceBackend` methods — a count the
  round could not agree on (0 / 9 / 11 depending on baseline) and which is recorded as a lead, not
  a fact — and the vacuous snapshot save/restore.

---

## 10. Open questions

- **OQ-N1** — *(closed by round 2; retained for the record)* whether the newly-reachable path
  invokes `RecurrenceBackend.stage_dataset`. **It does not** — the failure fires on **Apply
  Dataset**; one-shot Start bypasses staging. Round 1 recorded this as unresolved dissent, which
  was itself an error: two reviewers were describing different controls. Carried as work item §4.9.
  - Response: already resolved.

- **OQ-N2** — should `⊥` be the *mount* state rather than a transit state? It would make the first
  interaction an explicit choice and remove the seeded-default asymmetry, at the cost of an extra
  click for the common case and an FR15 interaction.
  - Response: it should be the mount state for normal canopy operations.
  demo mode should continue to auto-load the default spiral dataset.
  this apporoach honors the fundamental design philosophy of the juniper project: power and flexibility over simplicity for the research platform--as normally utilzed--and a simpler, works-out-of-the-box user experience for demo mode.
  Specifically, the demo mode design should enable processing of an actual, live dataset, defaulting to dog-fooding the platform code and infrastruture, and minimizing custom, demo-only code or local versions of functions that exist elsewhere in the platform.
  - **Disposition: ACCEPTED, with a prerequisite (N10).** `⊥` at mount is adopted for normal
    operation, and demo mode keeps auto-loading spirals. But canopy has never hydrated the dataset
    from the backend (measured, §4.10), so `⊥`-at-mount alone would disable Start *and* Apply after
    every reload over a staged, ready backend. §4.10 lands dataset-axis hydration **first** (PR 2),
    after which `⊥` appears only when the backend truly holds nothing — the honest reading of this
    answer, with no reload regression.
  - On demo mode: the dogfooding is largely already true (`demo_mode.py:551-554` calls juniper-data
    first). The demo-only code to minimise is the local fallback — which §4.12 makes **loud** rather
    than deleting, since its own comment names Docker-standalone and CI smoke tests as its purpose.
    That keeps the intent (never silently run on non-platform data) without breaking those lanes.

- **OQ-N3** — *(narrowed)* §4.8 settles that Start must be gated at `⊥`. Remaining: should Apply
  Dataset be disabled at `⊥` (§4.2 assumes yes), or should `⊥` be non-committable by construction?
  - Response: yes, apply dataset should be disabled when no dataset has been selected or dataset selection has been cleared.
  - **Disposition: ACCEPTED as written.** No prerequisite; consistent with N9 and already specified
    at §4.2. Closed.

- **OQ-N4** — is the §5.6 notice a toast, an inline alert, or a persistent annotation? N4 fixes the
  *locus*, not the form.
  - Response: let's go with a toast when the gate fails and a persistent error message until the situation is resolved.
  - **Disposition: ACCEPTED, split across two events (N12).** The answer describes two distinct
    events, and the split is what makes it coherent: a **toast** for the gate's *successful* repair
    (informational — nothing to resolve), a **persistent inline alert** for the empty
    compatible∩available set (blocking, and the only one "until resolved" applies to). Detail and
    the two practicalities — canopy has zero `Toast` components today, and a toast without
    `aria-live` is invisible to assistive technology — are at §4.3.

- **OQ-N5** — the browser falsifier is still open (evaluation §9): no agent clicked the greyed
  option in a live DOM, because canopy accepts TCP on 8050 but never responds. Cheapest remaining
  check.
  - Response: in the interest of being thorough, and avoiding the introduction of subtle gaps, let's perform the check.
  - **Disposition: ACCEPTED — and DONE (2026-09-02). Both gates hold.** Executed on an isolated trio
    (data 8103 / cascor 8204 / canopy 8053) with trusted CDP clicks, leaving the operator's stack
    and a concurrent session's stack untouched. Clicking the greyed `Equities (sequence)` option
    left the dropdown on `Spirals`; clicking the disabled `Recurrence (LMU)` Select left the model
    on CasCor. Record: `reports/2026-09-02_canopy-selection-deadlock/oqn5_browser_falsifier.md`.
  - Three by-products, all carried into the evaluation document
    (`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`): **X7** (canopy blocks
    entirely, health included, whenever cascor is unreachable — the environmental blocker turns out
    to be a canopy defect); a **correction** that the "canopy never responds" condition is transient
    rather than standing; and a measured refinement of **Y7** — the dataset option carries no
    `aria-disabled` at all, so its gate is invisible to assistive technology, while the model Select
    is a correctly-exposed native disabled button.
  - **Still not observed**: the `⊥`-dataset and `⊥`-model states, because they do not exist until
    §4.1 and §4.11 ship. Re-run this falsifier as an acceptance step for PR 3 — the traversal in
    §4.1 is so far established only by executing handlers, never in a DOM.
  - **Driver note for whoever runs it**: canopy never reaches DOM stability (its polling keeps a
    callback in flight, so `document.title` sits at `"Updating..."`). Both chrome-devtools `click`
    and Playwright's default `locator.click()` time out on the stability wait, and untrusted
    synthetic events are ignored outright because the widgets are **Radix**. Use
    `locator.click({force: true})`; coordinate clicking is unreliable because the coordinates go
    stale as the page re-renders.

- **OQ-N6** — D4's **second** affordance, the "clear model / show all" reset on the model surface
  (§5.5 of the design of record), is NO ARTIFACT and out of scope here. Ship it, or descope it on
  the record — it should not remain silently unbuilt a second time, which is how this defect
  arose.
  - Response: we should ship the "clear model / show all" reset.
  - **Disposition: ACCEPTED, with a prerequisite (N11).** The registry already ungates correctly on
    a cleared model — `gated_dataset_options(None)` returns all six datasets enabled (executed).
    The *handler* does not: it early-returns `no_update`, so clearing the model would leave the
    dataset dropdown frozen at the previous model's gate — **the mutual-gate trap again, on the
    model axis**, shipped by the very affordance meant to relieve it. §4.11 changes that early
    return. Consequence worth having: with both axes clearable, OQ-6 becomes answerable for the
    first time, because §5.6's *dataset-primary* policy ("keep dataset, clear model") is finally
    expressible.

**Status**: all six answered and dispositioned. OQ-N1 and OQ-N3 are closed outright; OQ-N2, N4, N5
and N6 are accepted with the prerequisites recorded above and specified in §4.

---

## 11. Notes

### Revaluation of scope-of-work, prioritization of fixes, and overarching goals for this development plan

the ten unseeded generators represent a substantial gap between the project requirements, along with their corresponding implementation of functionality, and the reality of the research platform as it currently exists.
the availability of all of the specified datasets is critical if the juniper research platform is to be actually useful.
while the missing generators might have been overshadowed by the work-flow deadlock initially, i would argue that they are, effectively, just as critical a defect in the juniper platform.
as such, i'd like to include the dataset defects in this work arc and design, even if added as a second iteration of work.
getting the platform to a usable state--without the current gaps in required functionality--is my primary goal for this development plan and this work arc.

---

## 12. Iteration 2 — closing the generator gap

Adopted from §11. This section makes that scope concrete and records what it depends on.

### 12.1 What is actually missing

`GENERATOR_REGISTRY` (`juniper-data/juniper_data/api/routes/generators.py:44`) registers **16**
generators; canopy's `DATASET_TYPES` seeds **6**. The ten unseeded ones split evenly by rank —
classified by executing the registry, not by reading prose:

| rank-2 classification (cascor-compatible) | rank-3 regression (LMU-compatible) |
|-------------------------------------------|-------------------------------------|
| `gaussian`, `checkerboard`, `equities`, `arc_agi`, `csv_import` | `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product` |

Two of the rank-3 five (`irregular_sine`, `delay_product`) are explicitly non-uniform Δt, so they
satisfy the LMU through `requires_dt=True` rather than the regular-Δt path.

### 12.2 The reassuring part

**This expansion adds no deadlock surface.** Rank-2 generators join cascor's component and rank-3
join recurrence's, so the compatibility graph keeps exactly **two** connected components. The
Confinement Lemma's reach is unchanged, and G1c's ≥3-component case correctly remains synthetic.
Growth in dataset count is not, by itself, growth in trap risk.

### 12.3 Prerequisites — none of which are optional

1. **Y5 is a hard blocker.** The generators proxy sends no `X-API-Key` while `/v1/generators` is
   not auth-exempt, so canopy falls back to a schema-less 4-entry list. Seeding ten generators on
   top of that ships ten datasets whose params panel reads *"No adjustable parameters"*. Y5 lands
   first, inside PR 5.
2. **`default_params` is hand-maintained and load-bearing.** `equities_seq` needed
   `max_symbols=5` to keep the one-shot fit inside the 300 s train timeout. Every new seed needs a
   bounded default or the one-shot path times out — **G11** enforces it.
3. **`mackey_glass` accepts a `seed` and ignores it.** A known ecosystem finding: generator
   seeding has three states, and this one is *seed-accepted-but-inert*. Exposing it in a
   benchmarking UI without flagging that ships irreproducible runs. Fix upstream or label at the
   locus before seeding.
4. **`csv_import` is not a peer of the others.** It is an import path, and canopy already has
   `dataset_import.py`. It belongs on G10's named exclusion list, not in the dropdown.
5. **`arc_agi`'s shape is unverified.** Confirm its rank before seeding rather than assuming
   rank-2 from its `task_type`.

### 12.4 Validation is part of the work, not an assumption

The evaluation grades "five ready 3-D datasets" as a **count**, not a measured capability — B3
graded the "5× larger" framing OVERSTATED precisely because none of the five has been exercised
end-to-end. §12 therefore requires, per newly-seeded generator: generate → stage → train → render,
observed once. A generator that cannot complete that sequence is seeded **disabled with a reason**
(the existing availability-gate idiom), not seeded silently broken. That is the difference between
closing a capability gap and moving it somewhere less visible.

### 12.5 Deployment reality

Several of these will legitimately be `available=false` in the container until the parallel
packaging workstream (§7) lands their extras — `equities` needs `yfinance`, which is absent from
`juniper-data/requirements.lock` today (§9). The availability gate already renders that honestly
with an install hint; §4.7 makes the fully-empty case legible. The UI work and the packaging work
proceed independently.
