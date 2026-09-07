# Lane B / Agent B2 — Adversarial review of the remediation PLAN

- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane B
- **Subject**: `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (§7 phasing, §11–§12 scope), read
  against `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`
- **Lenses**: SCOPE DISCIPLINE, FALSE AUTHORITY, ACTIONABILITY. (B1 attacks whether the fix
  *mechanism* is correct; this report attacks whether the *plan* is the right plan and will land.)
- **Date**: 2026-09-05. **Mode**: READ-ONLY on all repos. No edits, commits, PRs, merges;
  no service start/stop. Probes executed via `conda run -n JuniperCanopy1`.
- **Reference tree**: juniper-canopy `main` @ `fc62175`; juniper-data @ `005a82b`;
  juniper-cascor `main`.
- **Reconciled measurement this runs on**: Lane A3
  (`reports/2026-09-05_canopy-deadlock-consensus/laneA3.md`) — **zero of the six §7 items shipped**
  in 2026-09-02 → 09-05; the design's line numbers still resolve modulo two constant shifts.

---

## 0. Verdict in one paragraph

The design is a good *analysis* and a bad *plan*. Its two front-loaded PRs fix defects that no
user can currently reach; the first change a user can observe is PR 3, the largest PR in the arc,
and PR 2 is declared a prerequisite of a change (`⊥`-at-mount) that **no PR in §7 actually makes**.
The reachability defect the owner reported needs **one line** plus a small guard set, all of which
fit in one PR. The safety argument that justifies putting §4.4 first is real but is satisfied by
*co-shipping*, not by *pre-shipping* — and §4.4 as specified does not actually discharge it,
because it changes a label and gates nothing. Iteration 2 (§12) is a separate programme whose own
"hard blocker" is a cross-service auth defect unrelated to selection.

---

## 1. FATAL findings

### F-1 (FATAL) — PR 2 is the prerequisite of a change that appears in no PR

§7's PR 2 rationale is, verbatim: *"Prerequisite for `⊥`-at-mount. Landing it separately keeps the
reload regression from ever existing (N10)."* §4.10 closes with *"**Ordering is not negotiable**:
hydration lands before `⊥` becomes the mount state (§7)."*

`⊥`-at-mount means changing the dropdown's layout default. That locus is
`src/frontend/dashboard_manager.py:1333` — `value=DEFAULT_DATASET_TYPE`, one line above the
`clearable=False` at `:1334` the design cites nine times. **`:1333` and `DEFAULT_DATASET_TYPE` are
cited nowhere in either document** (`grep -n "DEFAULT_DATASET_TYPE\|1333" ` over both notes files →
no hits), and no §7 row contains the change. PR 3's contents are enumerated as *"§4.1 ✕ + §4.11
model clear + §4.2 / §4.8 guards + §4.3 naming and channels + §4.7 empty-set + G1a–G1d, G3, G6,
G8"* — no mount change. PR 4 and PR 5 are elsewhere.

Two consequences, both load-bearing on sequencing:

1. **PR 2 gates nothing in the plan.** Executing §7 exactly as written ships dataset-axis
   hydration and then never uses it for the purpose that justified building it first.
2. **`clearable=True` therefore ships without `⊥`-at-mount** — which is the brief's question 2,
   answered from the artifact. With the mount value unchanged, a page reload returns the dropdown
   to `spirals`, exactly as today. `dcc.Dropdown` value is not persisted (`model-selection-store`
   is `storage_type="memory"`, per the evaluation §1.2; the dropdown has no `persistence`), so `⊥`
   is a pure transit state the user creates by clicking ✕ and destroys by navigating. **There is no
   reload regression to prevent, so N10's prerequisite does not bind PR 3.**

Separately, the owner's accepted OQ-N2 answer (*"it should be the mount state for normal canopy
operations"*) is therefore **unimplemented by the plan of record**. That is a scope amputation, not
merely a sequencing bug: a disposition marked ACCEPTED has no delivery vehicle.

### F-2 (FATAL) — the front-loaded pair is unobservable, and its own harm is unreachable until PR 3

X1 misattribution requires *selecting the recurrence model*. In the shipped UI that is impossible:

- `_build_model_selection_table` sets `disabled=not is_compatible`
  (`src/frontend/dashboard_manager.py:3050`), with
  `dataset = get_dataset_spec(dataset_value) if dataset_value else None` (`:3018`) and
  `reason = model_reason(model, dataset) if dataset is not None else None` (`:3033`);
- the dataset can never be `equities_seq` while the model is `cascor` — executed:
  `gated_dataset_options('cascor')` returns `{'label': 'Equities (sequence) — needs a 3-D model',
  'value': 'equities_seq', 'disabled': True}`;
- the design's own OQ-N5 browser falsifier confirmed the disabled Select does not act
  (*"clicking the disabled `Recurrence (LMU)` Select left the model on CasCor"*).

So PR 1 fixes a defect no UI user can reach today, and PR 2 (per F-1) fixes a regression that will
never exist. **The first change a user can observe is PR 3** — third in order, largest in the arc,
and the only one carrying the defect the owner actually reported. A stall anywhere before it leaves
the reported defect untouched; A3 measured exactly that outcome over three days and 24 merged PRs.

**Steelman for §7's order, taken seriously.** This is a benchmarking platform; its product is a
number attributed to a model. PR 3 is precisely the change that makes a *wrong* attribution
reachable, and the wrongness is silent and durable — it lands in saved results. Shipping PR 3 alone
trades an unreachable-but-honest platform for a reachable-but-lying one. On that reading, "truth
telling precedes reach" is not ceremony; it is the ordering under which no released version can
ever produce a misattributed benchmark.

**Why it does not survive.** The obligation the steelman establishes is *"X1 must be closed **no
later than** PR 3"*, not *"X1 must be closed in an **earlier** PR."* Because X1 is unreachable
before PR 3 (measured above), merging §4.4 into the same PR as §4.1 yields a **zero-length exposure
window** — identical safety, one fewer merge cycle, and the user-visible fix arrives first rather
than third. §7's stated rationale for the split is *"Independently correct; shippable alone"* — true,
and a non-sequitur: *shippable* alone is not *valuable* alone. The steelman justifies **co-shipping**,
which §7 does not do.

---

## 2. SERIOUS findings

### S-3 (SERIOUS) — §4.4's mechanism does not discharge the safety obligation §7 uses to order it first

N5 says *"Silent misattribution is worse than a blocked control."* §4.4 specifies a **display**
change: read `swapped`/`backend`, and *"when `swapped is False` render the model summary as **not
active**, with the reason."* It blocks nothing. Traced end to end:

- `_model_state_response` (`src/main.py:3860-3871`) returns `"execution": backend.execution` — the
  **live** backend's, not the selected spec's.
- `_swap_backend` (`:3874-3895`) short-circuits to `swapped=False` when
  `_selection_targets_recurrence(nn_model) == (backend.backend_type == "recurrence")`, and
  `_selection_targets_recurrence` is False for `recurrence` whenever `settings.recurrence_service_url`
  is unset (`:3857`). Canopy's own regression pins this as *"a reachable normal flow, not a UI-gated
  one"* (`src/tests/regression/test_d8_d11_phase4_truth_up.py:54, 64-82`).
- So in an unconfigured deployment `model-class-store` becomes `"live"`, and
  `_resolve_oneshot_start_body_handler("live", "equities_seq")` returns `None` (`:2683`) — the bare
  cascor start POST.
- Start is force-disabled only by `model_is_trainable(model_key)`
  (`_update_button_appearance_handler`, `:7250`, gate at `:7269`), which reads the registry
  `status` — hardcoded `"live"` for recurrence (`src/model_registry.py:186`) — and never the backend.

**After PR 1 + PR 3 a user can still produce a cascor run labelled "Active: Recurrence (LMU)".**
The change that would discharge N5 is a **Start gate** on `swapped is False` / backend-provider
mismatch. It is in no PR, and §4.4's wording does not imply it.

### S-4 (SERIOUS) — §4.1's null-safety census is contradicted by §4.2 and is short by three unsafe consumers

§4.1 asserts: *"All **ten** Python consumers of `nn-dataset-type-dropdown.value` are null-safe;
there are **zero** JS consumers."* §4.2 then states that `_apply_dataset_handler` POSTs
`{"nn_dataset_type": None}` into a vacuous 200 — i.e. one of the "ten" is not null-safe, in the
same document.

Measured census (`grep -n 'nn-dataset-type-dropdown' src/`): **nine** `Input`/`State` consumers of
`.value` — `:2576, 2609, 2624, 2637, 2649, 4935, 5166, 5223, 5298` — plus one `Output` at `:2606`.
The "zero JS consumers" half holds (no hit in any `src/frontend/assets/*.js`, none in the 29 inline
`clientside_callback` blocks). Of the nine, **three** are unsafe at `⊥`, and only one is in the design:

| site | handler | behaviour at `⊥` | in design? |
|------|---------|------------------|-----------|
| `:4935` | `_apply_dataset_handler` (`:2831`) | POSTs `{"nn_dataset_type": None}` → vacuous 200 + false pending banner | yes (§4.2) |
| `:5223` | `_accept_live_switch_handler` (`:6046`) | `payload = {k: v for k, v in payload.items() if v is not None}` → **POSTs `/api/live_dataset_swap` with no dataset type at all** | **no** |
| `:5166` | `_open_live_switch_modal_handler` (`:6011`) | `if value is None: continue` → the *"here's what we're about to swap to"* confirmation renders **without the dataset row** | **no** |
| `:5298` | `open_restart_confirm_modal` → `_execute_restart_handler` (`:5666`) | field seeded `None`, baseline captured from the same value, `_restart_dataset_changed` False → **no re-stage; restart runs on the previously staged dataset** | partly (§4.5 covers `options`, not the null value) |

The live-switch pair is behind `experimental_functions` **and** `is_running`
(`_gate_live_switch_button_handler`, `:6000-6004`), so it is a narrower path — but it is a live
dataset swap issued with an unspecified dataset, which is X4's exact class on a control the design
never enumerates.

Confirmed by execution that `generator_name_for_type(None)` returns `''`, not `'spiral'` — so
`_apply_dataset_handler` takes the **non**-spiral branch at `⊥` and the null type reaches the POST.

### S-5 (SERIOUS) — §4.7 and §4.3 require callback-signature changes the design classes only for §4.8

§4.8 is correctly flagged as *"a **callback-signature change** and … a prerequisite of §4.1"*. Two
other items are the same class and are not flagged:

- **§4.7** — *"clear the dataset to `⊥`, render why, and gate Start"*, from inside
  `_gate_dataset_options_handler`. That callback has exactly **two** `Output`s (`:2605-2606`,
  options + value). "Render why" needs a third; "gate Start" needs a fourth (or a new store plus a
  second callback). Neither is named.
- **§4.3** — the persistent inline alert, the toast, and `aria-describedby` all need new `Output`s
  and container ids. None is named (see A-8).

An implementer costing PR 3 from §6 gets a number that excludes two of its signature changes.

### S-6 (SERIOUS) — §6 names the wrong metric as "the gate's own basis", and the "lane is not clean" claim rests on it

§6: *"The per-file 90% floor is **not** binding (`dashboard_manager.py` is 95.46% **branch-inclusive,
the gate's own basis**)"* and *"`src/backend/state_sync.py` sits at 87.38% below the file floor
already … the lane is not clean."*

The enforcing gate is **statement**-based, not branch-inclusive:

- `.github/workflows/ci.yml:255-261` runs `juniper-coverage-gap-map --coverage-json … --enforce`
  (blocking).
- `juniper-ci-tools/juniper_ci_tools/cli_coverage_gap_mapper.py:258` calls
  `report.files_below_statement_threshold(args.fail_under_file)`; `:131` documents the flag as
  *"Enforcing per-file **STATEMENT**-coverage floor … independent of the advisory `--file-threshold`
  display cut."*
- `coverage_gap_mapper.py:275-282` — `files_below_threshold` is the **ADVISORY** view;
  `:292-302` — `files_below_statement_threshold` is *"the enforcing basis"*.

And `gh run list --workflow=main-verify.yml` reports `conclusion: success` at HEAD `fc621752`. So
`state_sync.py`'s **enforcing** statement coverage is ≥ 90% and the lane *is* clean. The design's
"not clean" warning is an advisory number measured against a gate that does not read it. An
implementer who believes it will either chase a phantom or discount a real gate failure later.

### S-7 (SERIOUS) — §12 counts a generator it then excludes, and classifies one it says is unverified

§12.1 presents the ten unseeded generators *"classified by executing the registry, not by reading
prose"*, with `csv_import` and `arc_agi` in the rank-2 column. §12.3 then says:

- item 4 — `csv_import` *"belongs on G10's named exclusion list, not in the dropdown"*, so it is
  **not** one of the ten to seed;
- item 5 — *"`arc_agi`'s shape is **unverified**. Confirm its rank before seeding rather than
  assuming rank-2 from its `task_type`"* — contradicting the same table's claim to have classified
  it by execution.

Independently re-derived: `GENERATOR_REGISTRY`
(`juniper-data/juniper_data/api/routes/generators.py:44`) has exactly **16** entries — `spiral, xor,
gaussian, circles, moon, checkerboard, csv_import, equities, equities_seq, multi_sine, mackey_glass,
ar_p, irregular_sine, delay_product, mnist, arc_agi`; canopy's `DATASET_TYPES`
(`src/model_registry.py:132-149`) seeds **6**. The 16/6 headline is correct. **The seedable delta is
at most 9**, not 10, by the design's own §12.3 — and 8 if `arc_agi` fails its rank check.

---

## 3. Question 3 — the minimum change set, derived from the code

Not the minimum the design asserts. Each step below was traced against `fc62175`.

### 3.1 Load-bearing for REACHABILITY — exactly one line

`src/frontend/dashboard_manager.py:1334` — `clearable=False` → `clearable=True`.

Traversal, verified step by step:

1. ✕ sets the dropdown value to `None`. The gate does **not** re-fire: `gate_dataset_options` takes
   the dataset as `State` (`:2609`); its `Input`s are `model-selection-store.data` and
   `params-init-interval.n_intervals` (`:2607-2608`).
2. Open the model modal — `toggle_model_modal` reads the dataset as `State` (`:2576`) →
   `_build_model_selection_table(None, 'cascor')` → `dataset is None` (`:3018`) → every row
   `is_compatible = True` (`:3033-3034`) → Select Recurrence `disabled=False` (`:3050`).
3. Click Select → `_select_model_handler('recurrence')` (`:2876`) POSTs and writes
   `model-selection-store`.
4. The gate fires with `('recurrence', None)`: executed,
   `gated_dataset_options('recurrence')` leaves only `equities_seq` enabled →
   `enabled == ['equities_seq']`; `None not in enabled` and `enabled` is non-empty → the handler
   returns `(options, enabled[0])` (`:2704-2706`) → **`(recurrence, equities_seq)`**.

Nothing else is required to reach the pair. `I-safe` is not weakened: no `disabled` predicate is
relaxed, and the only new committed state is `(m, ⊥)`, which is incomplete rather than invalid.

### 3.2 Load-bearing for SAFETY once reachable — must ship in the same PR

| # | change | file:function | why it cannot wait |
|---|--------|---------------|--------------------|
| 1 | Start gate at `⊥` (§4.8) — add the dataset as a `State`, disable Start when it is null | `dashboard_manager.py:7250` `_update_button_appearance_handler` + its callback | `(cascor, ⊥)` otherwise sends the bare start POST and trains on the last-staged dataset while the sidebar shows none. **12 test call sites across 6 files** move with it (A3's count; the design says 4 — not re-derived here) |
| 2 | **Start gate on backend truth** (the missing half of §4.4 / S-3) — refuse Start when `swapped is False` / provider ≠ live backend | `dashboard_manager.py:2876` `_select_model_handler` + `:7250` | otherwise a cascor run is reported as Recurrence in any deployment without `recurrence_service_url` |
| 3 | Null guard + disable Apply at `⊥` (§4.2) | `dashboard_manager.py:2831` `_apply_dataset_handler` (idiom exists at `_restage_dataset:5629-5631`) | vacuous 200 + false pending banner |
| 4 | **Same guard on the live-switch pair (new, S-4)** — or disable the control at `⊥` | `:6011` `_open_live_switch_modal_handler`, `:6046` `_accept_live_switch_handler` | a live dataset swap POSTed with no dataset type |
| 5 | Restart-modal quarantine (§4.5, cheap form) — disable `restart-ds-type` while the sidebar model is not `DEFAULT_MODEL_KEY` | `dashboard_manager.py:5435` (hardcoded `options=gated_dataset_options(DEFAULT_MODEL_KEY)`, `clearable=False`), `:5666` `_execute_restart_handler` | with a pending banner already open from a cascor stage, the modal shows Equities and restarts on the previously staged spirals — §7's own fallback |
| 6 | Generator alias (§4.6) — route through `generator_name_for_type` | `dashboard_manager.py:2681` `_resolve_oneshot_start_body_handler` (siblings already do it at `:2769`, `:2846`) | one line, on the newly reachable one-shot path |

### 3.3 Load-bearing for HONESTY, not safety — second PR is fine

- Y9's `"✓ compatible"` for every row at `⊥` (`:3040-3043`) — a positive falsehood, not a hazard.
- The inverted docstring at `:2695` (*"dataset-primary conflict policy"* on a model-primary snap) —
  a comment; free.
- §4.11 clear-model + ungated options (`:2700-2701`). Confirmed real: `gated_dataset_options(None)`
  and `gated_dataset_options('')` both return all six enabled (executed), while the handler
  early-returns `no_update`. But this is OQ-N6's **second** affordance; it relieves nothing the ✕
  does not already relieve, and it is not on the reachability path.

### 3.4 Neither — quality-of-life, or separate defects swept into this arc

- **§4.7** empty-set recovery. A real defect (`not enabled` → `no_update`), but it fires only when
  *nothing* is both compatible and available — which §9 says is the container's normal LMU state.
  It neither gates reachability nor is worsened by `clearable=True`.
- **§4.3** toast + persistent alert + `aria-describedby`. Accessibility/UX; a worthy separate
  programme (Y7 records zero `aria-*` in the whole of `dashboard_manager.py` — re-derived: `grep -c
  'aria-'` → 0, `'aria_'` → 0).
- **§4.9** staging. Not a canopy-only change: `RecurrenceBackend` has no `stage_dataset` and neither
  does juniper-recurrence (A3), **and** cascor's `Literal`
  (`juniper-cascor/src/api/models/training.py:235`) admits `"equities"` but **not** `"equities_seq"`.
  So Apply Dataset for the target pair cannot be made to *work* by any change inside canopy — only
  guarded. Up to three repos.
- **§4.10** hydration. A real gap (`GET /api/train/status`, `src/main.py:3708-3718`, returns
  `{"backend", "execution", **status}` with no dataset field), but per F-1 it is reload fidelity,
  not a prerequisite of anything scheduled.
- **§4.12** demo-mode degraded banner. A separate defect, unrelated to selection.
- **§5's five injectable resolvers** — test infrastructure for G1c/G1d, not behaviour. (The count
  **is** right: `model_registry.py:200, 209, 264, 276, 408` all lack an injectable parameter.
  NOT A DEFECT.)
- **§12** entirely — see §4 below.

---

## 4. Question 4 — false authority / scope creep audit of §11–§12

The owner explicitly asked for the generator work, so the question is only whether **coupling** it
to the deadlock fix helps or delays. The evidence says it delays, and that decoupling costs nothing:

1. **The stated dependency is mostly false.** §7's PR 5 rationale is *"Depends on PRs 1–2 for honest
   attribution and on Y5 for a usable params panel."* But the five rank-2 seeds
   (`gaussian`, `checkerboard`, `equities`, and — pending §12.3's own caveats — `arc_agi`,
   `csv_import`) are reachable from `(cascor, *)` **today**, through the existing dropdown, with no
   part of PRs 1–4. Three of them (`gaussian`, `checkerboard`, `equities`) are already accepted by
   cascor's staging `Literal` (`juniper-cascor/src/api/models/training.py:235`). Only the five
   rank-3 seeds need the deadlock fix — and they need only §3.1's one line.
2. **Its "hard blocker" is a different subsystem.** §12.3 item 1 calls Y5 *"a hard blocker"*.
   Re-derived: `list_dataset_generators` (`src/main.py:1838-1876`) calls
   `client.get(f"{data_url}/v1/generators")` with **no headers at all**, and juniper-data
   authenticates every path not in `EXEMPT_PATHS` (`juniper_data/api/middleware.py:191, 237-246`).
   Fixing that is a canopy↔data auth change with no relationship to selection reachability — and it
   sits *inside* PR 5, so PR 5 cannot start until it lands.
3. **§12.4 requires up to nine live end-to-end validations** (generate → stage → train → render,
   observed once, per generator) plus their evidence, inside an arc whose purpose is unsticking a
   two-control workflow.
4. **§12.5 concedes several will be `available=false`** until a juniper-data packaging change lands,
   which §7 already carries as a separate parallel workstream.

**Verdict: iteration 2 is a separate programme wearing the same jacket.** Nothing about it needs to
be cancelled — it needs to be *unblocked from* the deadlock fix rather than queued behind it.

---

## 5. Question 5 — false precision beyond A3's two

A3 already found: the §4.8 arity change touches **12** call sites across **6** files (design says
4, "12 sites across 2 files"); the §4.11 premise appears **twice** (design says once). Additional,
same class:

| # | claim | where | measured |
|---|-------|-------|----------|
| 1 | *"All ten Python consumers … are null-safe"* | §4.1 | **nine** consumers; **three** unsafe, and the design's own §4.2 names one of them (S-4) |
| 2 | *"branch-inclusive, the gate's own basis"* | §6 | the enforcing basis is **statement** percent (S-6) |
| 3 | *"state_sync.py … below the file floor already … the lane is not clean"* | §6 | `main-verify` is `success` at HEAD with the gate blocking (S-6) |
| 4 | *"the ten unseeded ones split evenly by rank … classified by executing the registry"* | §12.1 | contradicted by §12.3 items 4 and 5 in the same document (S-7); seedable delta ≤ 9 |
| 5 | *"`(cascor, ⊥)` **sends** the bare start POST and trains on the last-staged dataset"* — present tense, *"as shipped"* | §2 | `⊥` is **not reachable in the shipped UI** (`clearable=False`; the gate never returns `None`). The handler analysis supports it as a *prediction about the post-§4.1 state*; the tense presents a prediction as a measurement |
| 6 | *"canopy has **zero** `Toast` components today, so this is new surface carrying its own dismiss / stacking / timer state"* | §4.3 | literally true (`grep -rn Toast src/` → 2 hits, both **test class names**: `test_apply_params_skipped_surfaced.py:129`, `test_p2_wave_batch_b.py:38`) but the **cost claim is overstated**: `dbc.Alert(..., duration=…, dismissable=True)` is the established auto-dismissing idiom, used **17** times in `dashboard_manager.py`, with a fixed-position stacking container already at `:2187`. Timer and dismiss are solved; only stacking policy is new (MINOR) |
| 7 | *"Independently correct; shippable alone."* | §7 PR 1 | true and irrelevant — the defect it fixes is unreachable (F-2) |

**Checks that passed** (recorded per §6 of the procedure — a round that changes nothing must say
so): §5's "**five** resolvers lack an injectable parameter" is exactly right
(`model_registry.py:200, 209, 264, 276, 408`). §12.1's 16-vs-6 counts are right. §4.11's registry
claim is right (executed). §4.1's destination-state claims are right — `MODELS` has exactly two
entries, so "both Select buttons `disabled=False`" is correct, and
`_dataset_model_hint_handler(None)` does return `''` (the underlying `dataset_model_hint(None)`
returns `None`; the handler's `or ""` supplies the empty string). §4.5's X2 is real: the restart
modal's own dropdown is hardcoded `options=gated_dataset_options(DEFAULT_MODEL_KEY),
clearable=False` (`:5435`).

---

## 6. Question 6 — actionability: specification or intention?

| item | verdict | what an implementer would still have to decide |
|------|---------|-----------------------------------------------|
| **§4.3** consequence naming | **INTENTION** | which container hosts the persistent alert and where (`nn-model-dataset-hint` at `:1240`? `dataset-stage-outcome-alert` at `:2187`? a new id?); `dbc.Toast` (none exists) vs. the established `dbc.Alert(duration=)` idiom (17 uses); stacking policy when two fire; which control receives `aria-describedby` and what the reason cell's `id` is; the copy for every message; and the extra callback `Output`s (the gate callback has two) |
| **§4.7** empty-set state | **HALF** | the clear is specifiable (`return options, None`); "render why" and "gate Start" are not — both need new `Output`s and, for Start, a channel from the gate handler to the button (S-5). Note the model-side idiom already exists (`model-selection-empty-alert`, `:3076`) and could be mirrored — the design does not say to |
| **§4.9** staging | **SPLIT, undecided** | *"Minimum: guard the call site … full fix is a `stage_dataset` implementation"* — two mutually exclusive scopes in one sentence, no decision recorded. The minimum is an hour (`src/main.py:4191-4192`, guard `backend.stage_dataset` + a real 501/502). The "full fix" is a **new capability in juniper-recurrence** (which has no `stage_dataset` at all) **and** a `Literal` widening in **juniper-cascor** (`training.py:235` has `"equities"`, not `"equities_seq"`) — unsized, unowned, three repos |
| **§4.1 / §4.2 / §4.6 / §4.8** | **SPECIFICATION** | buildable today, file and function named, idiom cited |
| **§4.5** | **SPECIFICATION** (quarantine form) / **HALF** (full form) | the quarantine is one `disabled` flag; the full form needs the `Output`/`State` addition §4.5 names, which is fine |
| **§4.10** | **HALF** | *"`GET /api/train/status`, **or a sibling route**"* — undecided. A3 adds that the field now lands behind X7's `offload()` and status cache, a staleness question the design does not raise |
| **§12** | **INTENTION** | rank of `arc_agi` unverified; `csv_import`'s disposition contradicts its own table; `default_params` bounds unspecified per generator; the Y5 auth fix unspecified |

---

## 7. MINOR

- **M-9 — `⊥` can be destroyed by the mount tick.** `params-init-interval` is
  `interval=1000, max_intervals=1` (`:1871`) and is an `Input` to `gate_dataset_options` (`:2608`).
  A user who clears the dataset within ~1 s of page load is snapped back to `spirals` by
  `enabled[0]` (`:2706`). One extra click, not a blocker — but the §4.1 traversal is not
  unconditional, and the PR-3 browser falsifier the design mandates must wait out the tick or it
  may fail to reproduce.
- **M-10 — the availability gate is inert on the proxy fallback.** `list_dataset_generators`
  (`src/main.py:1866-1875`) falls back to a 4-entry list with **no `available` key**, and
  `is_generator_available` returns `True` on a missing flag (executed). So whenever juniper-data is
  unreachable, §4.7's empty-set state is unreachable too — which weakens the case for building
  §4.7 inside the reachability PR.

## 8. NOT A DEFECT

See §5's "checks that passed". Additionally: the design's core diagnosis, its `I-safe`/`I-cover`
framing, its rejection of family F2, and its `⊥`-as-cut-vertex mechanism all survive this review
unchanged. The problem is the *plan*, not the *analysis*.

---

## 9. Recommended sequencing — executable today by a session with merge approval

Three PRs replace §7's five plus one. Each is independently revertible; each is smaller than §7's
PR 3; **the first one closes the defect the owner reported.**

### PR A — "the pair is reachable, and every control that could lie is gated"

*This is §7's PR 1 + PR 3's guards + PR 4's cheap halves, collapsed. It is the whole user-visible fix.*

1. `dashboard_manager.py:1334` — `clearable=False` → `clearable=True`. **(the fix)**
2. `:7250` `_update_button_appearance_handler` + callback — take the dataset; disable Start at `⊥`
   (§4.8). Repair the 12 call sites across 6 files.
3. `:2876` `_select_model_handler` — read `swapped`/`backend`; render "not active" **and disable
   Start** when the selected model is not the live backend (§4.4 **plus** the gate S-3 shows is
   missing).
4. `:2831` `_apply_dataset_handler` — null guard; disable Apply Dataset at `⊥` (§4.2).
5. `:6011` / `:6046` live-switch pair — same guard, or disable the control at `⊥` (**new, S-4**).
6. `:5435` restart modal — quarantine `restart-ds-type` when the sidebar model is not the default
   (§7's own fallback for PR 4).
7. `:2681` `_resolve_oneshot_start_body_handler` — route through `generator_name_for_type` (§4.6).
8. `:3040-3043` — do not render `"✓ compatible"` at `⊥` (Y9); `:2695` — fix the inverted docstring.
9. Tests: **G1a red first, then green**; G1b with the `∪ {(m, ⊥)}` term; G2, G5, G6. Add the
   §5 injectable parameter to `gated_dataset_options` only (the one G1 needs); defer the other four.
10. Acceptance: re-run the OQ-N5 browser falsifier on an isolated trio, per the method constraints
    recorded in §10's OQ-N5 disposition, and observe the `⊥` states for the first time.

Deliberately **not** in PR A: §4.7, §4.3's toast/alert/aria, §4.10, §4.11, §4.12, §4.9's
implementation, §5's remaining four resolvers, all of §12.

### PR B — "the second affordance, the empty set, and the notices"

*§7's PR 3 remainder. Nothing here is on the reachability path; all of it is worth having.*

- §4.11 clear-model + ungated options (`:2700-2701`) + **G8**; the OQ-N6 "clear model / show all"
  control.
- §4.7 empty-set recovery + **G3** — **and first decide the two open items S-5 names**: which
  container, and how the gate handler reaches Start.
- §4.3's channels — build on the existing `dbc.Alert(duration=)` idiom and the fixed-position
  container at `:2187` rather than inventing a `Toast` surface; add `role="status"`/`aria-live`
  and the `aria-describedby` link.
- §4.12 demo-mode degraded banner + **G9**.
- §5's remaining four injectable resolvers + **G1c/G1d**.

### PR C — "staging tells the truth" *(may run parallel to B)*

- `src/main.py:4191-4192` — guard `backend.stage_dataset` and return a real message (§4.9 minimum)
  + **G4**.
- Record the two real fixes as **separate, cross-repo** work items with owners, since neither is a
  canopy change: `RecurrenceBackend.stage_dataset` (juniper-recurrence) and `equities_seq` in
  `training.py:235`'s `Literal` (juniper-cascor). Do not leave them inside a canopy PR's scope.

### Decoupled, starting immediately and in parallel — the generator programme (§12)

Not a PR in this arc. Its own sequence, and **none of it blocks A/B/C**:

1. **Y5 first** — canopy's generators proxy must send `X-API-Key` (`src/main.py:1838-1876`), or
   `/v1/generators` must be exempted in juniper-data. This is an auth fix, not a UI fix.
2. **Rank-2 seeds now** — `gaussian`, `checkerboard`, `equities` are reachable today and already in
   cascor's `Literal`. They need no part of A/B/C.
3. **Rank-3 seeds after PR A** — `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`,
   `delay_product`, each with bounded `default_params` (**G11**) and the `mackey_glass` inert-seed
   flag.
4. **Resolve §12.3's own contradictions before counting anything**: `csv_import` onto G10's
   exclusion list; verify `arc_agi`'s rank. The honest headline is **≤ 9**, not 10.
5. **§12.4 validation** per seeded generator; a generator that fails is seeded *disabled with a
   reason*, per the existing availability-gate idiom.
6. **The juniper-data packaging workstream** (`equities` extra → `requirements.lock`) stays parallel,
   as §7 already had it.

### What changes versus §7, and why

| §7 | recommended | reason |
|----|-------------|--------|
| PR 1 alone, first | folded into PR A | X1 is unreachable until the ✕ ships (F-2); co-shipping gives a zero-length exposure window and saves a cycle |
| PR 2 (hydration) as a blocker | **dropped from the critical path**; re-file as its own item | it is the prerequisite of a change no PR makes (F-1); with the mount value unchanged there is no reload regression |
| PR 3 = the biggest PR, third | PR A = the smallest useful PR, first | the reported defect ships first |
| PR 4 "activated by PR 3" | quarantine in PR A; the real fix in PR C | §7's own fallback, promoted to the default, because §4.9's real fix is cross-repo |
| PR 5 depends on PRs 1–2 | decoupled entirely | the dependency is false for rank-2 and is only `clearable=True` for rank-3 (§4) |

---

## 10. What this review cannot support

- It does **not** re-derive A3's ship-status census; that is Lane A's, and it is taken as given.
- It does **not** re-derive A3's "12 sites across 6 files"; my own count of the §4.8 blast radius
  was not performed. If that number is wrong, PR A's size is wrong with it.
- It does **not** establish whether the operator's live deployment sets
  `settings.recurrence_service_url`. S-3's severity is **maximal** when it is unset and **nil** when
  it is set; the code path is proven either way but the deployed value was not read (no services
  touched, per the brief). **Read it before sizing PR A item 3.**
- It does **not** claim the `⊥` traversal works in a browser. It is established by reading handlers
  and executing the registry, exactly as the design's own OQ-N5 disposition says: *"Still not
  observed: the `⊥`-dataset and `⊥`-model states, because they do not exist until §4.1 and §4.11
  ship."* PR A item 10 is the check that would close it.
- It does **not** assess whether the fix mechanism is *correct* — that is B1's brief, and any
  conflict between this report's §3.1 traversal and B1's findings should be settled by opening the
  handler, not by averaging.
