# Juniper-Canopy — Selection Deadlock: Consensus Validation of the Remediation Design

- **Project**: Juniper — juniper-canopy
- **Author**: Paul Calnon
- **Date**: 2026-09-05
- **Status**: Validation complete; design **upheld with corrections**. Phases 1 and 2 shipped and **accepted in a live browser** (§8.1).
- **Validates**: [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md)
  and its evaluation of record [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md)
- **Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Agent reports**: `reports/2026-09-05_canopy-deadlock-consensus/{laneA1,laneA2,laneA3,laneB1,laneB2}.md`
- **Acceptance evidence**: `reports/2026-09-05_canopy-deadlock-consensus/browser_acceptance.md`

---

## 1. Why this ran

The design of record was merged 2026-09-02 (juniper-ml#1571, #1575) after sixteen proposals and two
adversarial rounds. Three days later the defect it specifies a remedy for was **still present**, and
canopy had shipped 24 unrelated PRs in the interim. Before spending further effort executing a plan
that had not moved, the plan itself was put through the consensus procedure.

Sizing under §3 of the procedure: **high criticality** (document of record, gates a ship) ×
**medium-to-high uncertainty** (the code had moved substantially under the plan; the design carries
several universal quantifiers). That places it in the top-right cell: **3+ Lane A agents with
distinct entry points, 2+ Lane B agents with opposing briefs.** Five were run.

---

## 2. What had actually been built: nothing

Lane A3 established this from git and PR history, independently of source inspection, then
confirmed each verdict against the diff that would have implemented it.

| §7 phase | contents | verdict |
|---|---|---|
| PR 1 | §4.4 X1 model-state truth | **NOT SHIPPED** |
| PR 2 | §4.10 dataset/model hydration | **NOT SHIPPED** |
| PR 3 | §4.1 ✕ + §4.2/§4.7/§4.8/§4.11/§4.12 | **NOT SHIPPED**, every part |
| PR 4 | §4.5 restart modal + §4.6 alias + §4.9 staging | **NOT SHIPPED** |
| PR 5 | §12 generator expansion | **NOT SHIPPED** |
| ∥ | juniper-data `equities` extra into `requirements.lock` | **NOT SHIPPED** |

`git log --all -S 'clearable=True'` is **empty over canopy's entire history**. `src/model_registry.py`
does not appear in the `30e15b7..fc62175` diffstat at all.

The 24 intervening canopy PRs: **8 X7**, **8 F-CANOPY-0xx**, **8 other**, **0 deadlock plan**. The X7
work was not a detour — X7 (canopy blocking entirely, `/v1/health` included, whenever cascor is
unreachable) was discovered *during* the 09-02 browser falsifier and was the environmental blocker
that made that falsifier look impossible.

**Critically: zero of the nine target handlers drifted.** All byte-identical by whole-function sha1;
only `_update_button_appearance_handler` (+63) and `open_restart_confirm_modal` (+13) moved position.
The plan still applied to the code it would be applied to. Two one-line retargetings were needed, not
a re-plan: §4.10's new field lands behind X7's `offload()` wrapper, and §4.9's guard goes on an
`offload()` call.

---

## 3. The design's core claim survives — measured, not argued

Lane A1 executed the traversal end-to-end at handler level:

> **BFS over the shipped handlers gives Reach = 5 today. With `clearable=True` as the only change,
> Reach = 8 with 0 invalid states.**

Lane A2, which was **forbidden from reading either design document** and worked only from source,
independently reproduced the whole defect: 6 compatible pairs, 5 reachable, the missing one is
`(recurrence, equities_seq)`, and the mechanism is the mutual gate between `dashboard_manager.py:2702`
/ `model_registry.py:423` and `dashboard_manager.py:3018`/`:3033`/`:3050`. Two genuinely independent
entry points converging on the same measurement is what makes this a validation rather than an echo.

This is now pinned in CI as **G1a/G1b/G2** and verified red-before-green: reverting the one keyword
yields `compatible but unreachable: {('recurrence', 'equities_seq')}` with reach reduced to exactly
the five cascor pairs.

---

## 4. Corrections to the design of record

### 4.1 Refuted

| # | design claim | reality |
|---|---|---|
| R1 | §4.1: "All **ten** Python consumers … are null-safe" | There are **nine** consumers; the tenth `.value` reference is the *writer* at `:2606`. And **three are not null-safe**: `_apply_dataset_handler`, `_accept_live_switch_handler`, `_open_live_switch_modal_handler`. §4.2 documents one of them, contradicting §4.1's own census. |
| R2 | §4.10 / G7: "`GET /api/train/status` carries **no** dataset field" | It carries `pending_dataset` (`service_backend.py:308`, `demo_backend.py:131`). No *active-type* field — which is the substance — but a channel exists, so "a new route or route field" forecloses a real fork. |
| R3 | §5: G4 "status before: **fails**" | As worded (*through* `generator_name_for_type`) it **passes** today; the alias map shipped at `dataset_schema.py:97-100`. §5's "specified to fail on today's code" does not hold for G4. |
| R4 | §4.12: one demo-mode fallback site | **Three**: `demo_mode.py:551-554`, `:1821-1824`, `:2242-2245`. A banner on the constructor alone lets demo mode *become* degraded mid-session unannounced. |
| R5 | §2: the F2 rejection, stated unconditionally | Reproduced (10/5/unreached) **only** when `equities_seq` is unavailable. Under all-available the same F2 gives 6/0/**reached**. The rejection holds; its unconditional phrasing does not. |
| R6 | §6: "the gate's own basis" is branch-inclusive coverage | Enforcement is **statement**-based. The `state_sync.py` "lane is not clean" remark is an advisory number against a gate that does not read it. |

### 4.2 Under-counted

- §4.8's arity change touches **12 handler call sites across 6 files** (design: 4), plus **2 genuine
  callback-arity sites**. Confirmed empirically when the change was made.
- The §4.11 premise assertion appears **twice** (`test_model_picker.py:105`,
  `test_n7_dataset_panel.py:155`), not once.
- §5's "enabling change": five resolvers lack injection (correct), but **five** others have it, not
  three.
- §12.1 counts `csv_import` among "the ten" while §12.3 puts it on the exclusion list, and places
  `arc_agi` in rank-2 from a table claiming execution while §12.3 calls its shape unverified. The
  seedable delta is **≤ 9**.

### 4.3 The design cannot deliver one of its own accepted decisions

**`⊥`-at-mount (OQ-N2) is ACCEPTED by the owner and has no delivery vehicle.** Making `⊥` the mount
state means editing `dashboard_manager.py:1333` (`value=DEFAULT_DATASET_TYPE`). That line, and the
constant, appear **nowhere** in either document, and no §7 row contains the change. PR 2's entire
stated rationale is "prerequisite for `⊥`-at-mount" — so **PR 2 gated nothing**.

Worse, the decision is self-defeating as specified. `params-init-interval` (`interval=1000,
max_intervals=1`) is an **`Input` of `gate_dataset_options`**, which owns the dropdown's `value`; the
snap at `:2702-2706` finds `None not in enabled` and returns `enabled[0]`. Measured in all four
availability scenarios: a `⊥` mount becomes `spirals` one second after load. **§4.1 asserts that snap
is correct; §4.10 requires the opposite.** The two sections contradict each other.

A second-order problem sits behind it: §4.10's hydration must write
`Output("nn-dataset-type-dropdown", "value")`, which `gate_dataset_options` solely owns with no
`allow_duplicate`, and would fire off the same interval — two writers, one output, undefined order.

**A user-initiated clear is unaffected** (the interval has already fired), so the deadlock fix itself
is untouched by this. `⊥`-at-mount is deferred pending resolution of the contradiction.

---

## 5. Defects found that the design does not contain

| id | finding |
|---|---|
| **X4′** | The null-dataset defect is **destructive, not vacuous**. `{}` reaches cascor, which documents an empty body as *clearing any prior staging* — so Apply Dataset at `⊥` discarded a staged change while reporting success. The live swap's `{}` reaches `swap_dataset_live()`, which **stops the training future and discards in-flight candidates**. And `_restage_dataset`, which §4.2 names as *"the correct idiom"*, is itself unguarded. |
| **X8** | **`task_type` diverges between registries, and "fixing" it deletes the reachability target.** canopy calls `equities_seq` `regression` (`model_registry.py:141`); juniper-data calls it `classification` (`generators.py:117`). `compatible()` tests `task_type in supported_task_types` and recurrence declares regression-only, so relabelling gives `compatible_models(equities_seq) → []` — the LMU loses its only dataset. Found independently twice. **The third possibility is the answer**: the generator is genuinely dual-target and the LMU reads `y_reg` preferentially; both labels are locally correct and neither vocabulary has "both". Inert on the wire today (`GeneratorInfo` omits `task_type`) and inert in `compatible()` (dropping the clause changes 0 of 12 verdicts) — it becomes load-bearing **exactly at §12's ten new seeds**, which nowhere state that upstream `task_type` is non-authoritative. |
| **X9** | **Clearing the model would ship an ungated Start.** `model_is_trainable(None) → True` by design (`model_registry.py:245`), so §4.11's affordance would reintroduce, on the model axis, the misattribution class PR 1 exists to close. Gated pre-emptively in #593. |
| **X10** | `_selection_is_live` (and §4.4's `swapped` predicate equally) is blind to backend **health**: `RecurrenceBackend.initialize()` returns `True` unconditionally with no probe, so `main.py`'s 502 is unreachable and a dead recurrence service still reports `backend="recurrence"`. |
| **X11** | A `DemoBackend` simulation renders as *"Active: CasCor"*. The provider partition cannot separate real from simulated cascor by construction, and `_initial_model_summary` passes no `backend`, so **first paint always reads "Active: CasCor"** whatever is running. This is Y3's class on the model axis. |

---

## 6. What was attacked and held (honest negatives)

Recorded because a validation that reports only defects is not a validation.

- **The dash 4.2.0 Dropdown ✕ emits `null`, not `''`** — proven from the shipped component source
  map, not the docs. Every null check in the design behaves as intended.
- **The traversal terminates at `equities_seq` for a structural reason** — recurrence has exactly one
  compatible dataset and `apply_availability_gate` preserves order.
- **No `⊥` persists.** The dropdown has no `persistence`; all three selection stores are
  `storage_type="memory"`.
- **The empty compatible∩available set does not strand the user** — both Selects are enabled at `⊥`.
- **The Start gate is enforceable where §4.8 puts it** — one writer, both transports key off
  `n_clicks`.
- **FR9 holds**, and `equities_seq` is a real juniper-data generator (a Lane B hypothesis to the
  contrary was refuted at `generators.py:113`).

**One instrument was found inadequate and discarded by its own author** (A1): a rank discriminator
imported a guessed module, silently fell to `None`, and scored 16/16 rank-2 — a clean false REFUTED
of §12.1. It was caught because 16/16 is implausible for a registry containing `equities_seq`. This
is the §2 "instrument adequacy" requirement doing its job.

---

## 7. Disposition and revised sequencing

The design's **mechanism** is upheld; its **phasing** is not. Lane B2 established that the front-loaded
pair (PR 1, PR 2) is unobservable to a user before PR 3 — X1's harm requires selecting the recurrence
model, which is exactly what the deadlock prevents — so "truth-telling precedes reach" establishes
only that X1 must close *no later than* the reachability fix, not before it. The content of PR 1
survives; its sequencing does not.

Executed:

| shipped | contents |
|---|---|
| **canopy#592** | §4.4 X1 model-state truth + **G5**. Departs from §4.4 deliberately: `swapped is False` is *also* correct when re-selecting the already-live model, so agreement is tested on the model's **provider** instead. |
| **canopy#593** | §4.1 ✕ + §4.8 Start gate (both axes, pre-closing X9) + §4.2 guards on **all three** commit paths + §4.5 restart-modal regate + **G1a/G1b/G2/G6**. Also repairs a defect in #592's guardrail: it pinned a `backend_type` of `"cascor"`, which the property never returns (real domain `{"service","demo","recurrence"}`). |

Remaining, in order:

1. **PR B** — §4.11 clear-model + G8, §4.7 empty-set + G3, §4.3 notice channels (built on the
   existing `dbc.Alert(duration=)` idiom used 17× — canopy's "zero Toast components" cost is
   overstated), §4.12 across **all three** fallback sites + G9, and the four remaining resolver
   injection points + G1c/G1d.
2. **PR C** *(parallel)* — §4.6 alias, §4.9 staging guard + G4 as re-specified, and the two real
   fixes filed as **cross-repo** items: `RecurrenceBackend.stage_dataset` (juniper-recurrence) and
   `equities_seq` in `juniper-cascor/src/api/models/training.py:235`'s `Literal`.
3. **§12 generator programme** — decoupled, blocking nothing, and startable now. **Y5 auth first**;
   then the rank-2 seeds, which are already in cascor's `Literal` and reachable with no part of
   PR B or C. **X8 must be settled before any seed sources `task_type` upstream.**
4. **`⊥`-at-mount** — only after §4.1-vs-§4.10's contradiction is resolved and the two-writer
   problem on the dropdown's `value` has an answer. Hydration (§4.10) is smaller than costed: a
   `pending_dataset` channel already exists and `_init_params_from_backend_handler` is the natural
   host.
5. **X10 / X11** — backend health probing and first-paint model truth. Neither is a regression from
   #592; both are uncovered cases it does not reach.

---

## 8. Acceptance, and what remains unestablished

### 8.1 OQ-N5 is CLOSED — the traversal was observed

Evidence: `reports/2026-09-05_canopy-deadlock-consensus/browser_acceptance.md`. Run against canopy
`main` @ `aa61156` on an isolated trio **plus the recurrence service** (data 8105 with the
`equities` extra, cascor 8206, recurrence 8215, canopy 8055), chosen off the documented default
ports because a concurrent session's stack already held those. The operator's stack and that
session's stack were both verified untouched afterwards.

```text
(cascor, Spirals) --✕--> (cascor, ⊥)  [Start DISABLED, Apply DISABLED]
                  --Select Recurrence--> (recurrence, ⊥)
                  --gate snap--> (Recurrence (LMU), Equities (sequence))  [both re-ENABLED]
```

The `<a class="dash-dropdown-clear">` element is present in the rendered DOM — under
`clearable=False` it is not rendered at all — and carries an `aria-label`, so unlike the greyed
dataset *option* (Y7) this affordance is exposed to assistive technology. At `⊥` the model table's
`Recurrence (LMU)` Select is **enabled**; on 2026-09-02 the same click was proven inert.

Two method findings worth carrying:

- **A first-run "Welcome to Juniper Canopy" modal covers the sidebar**, and because
  `force: true` skips the hit-test, the first ✕ click silently landed on the modal instead and
  looked like an inert control. Hit-test the target's own centre with `document.elementFromPoint`
  before concluding a control does nothing.
- **A single sample after a fixed sleep is not a settled reading.** The step-3 probe read the
  dataset as `""` at 4000 ms and was briefly written up as "the snap did not fire"; it had fired,
  just later. Poll for the expected value with a deadline on a page whose callbacks are
  continuously in flight.

**Y9 was observed rather than inferred**: at `⊥` the model table renders `✓ compatible` for *both*
models — a positive falsehood, scheduled for §4.3 in PR B.

### 8.2 Still not established

- The `⊥`-**model** state and the empty compatible∩available set were **not** exercised — §4.11 has
  not shipped, and all 16 generators reported `available: true` with the `equities` extra installed.
- **No training run was started**, so nothing here says whether the LMU can actually train on
  `equities_seq` end-to-end. §12.4's unvalidated-capability caveat stands.
- No live service was contacted during the Lane A/B analysis itself, so §4.9's 502 and §4.2's wire
  behaviour are traced through code and cascor's own route docstring, not observed.
- **Availability scenarios remain injected, not read from a running container.** §9's "the LMU has
  zero available datasets in the container" additionally holds only while juniper-data is **up** and
  reporting `available:false`; two fail-open layers mean a *down* juniper-data reports
  `equities_seq` available and the failure surfaces later as a 501.
