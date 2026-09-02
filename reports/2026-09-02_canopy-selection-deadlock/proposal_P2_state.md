# P2 — State machines, invariants, and reachability

**Author lens**: P2 (state space / transition relation / reachability)
**Subject**: juniper-canopy model + dataset selection, canopy #368
**Design of record**: `/home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`
**Repo read**: `/home/pcalnon/Development/python/Juniper/juniper-canopy` @ read-only, nothing edited
**Date**: 2026-09-02

---

## 0. Verification of the hypothesis and of every anchor

The hypothesis is **confirmed**, and I confirmed it two ways: by reading the transition
relation out of the code, and by executing a breadth-first search over that relation
against the real registry.

### 0.1 Anchors — all correct, no corrections needed

| Anchor | Verified |
|---|---|
| `src/model_registry.py` `DATASET_TYPES` — 6 seeds, `equities_seq` `ndim=3 temporal="irregular" task_type="regression"` | ✔ `model_registry.py:132-150` |
| `MODELS` — `cascor` `input_ndim={2}` tasks `{classification, regression}`; `recurrence` `input_ndim={3}` tasks `{regression}` `requires_dt=True` | ✔ `model_registry.py:167-193` |
| `compatible()` / `temporal_ok()` / `compatible_models()` / `compatible_datasets()` / `dataset_reason()` / `model_reason()` / `gated_dataset_options()` | ✔ `model_registry.py:299-424` |
| `dashboard_manager.py:1334` sidebar dataset dropdown `clearable=False` | ✔ exact (dropdown `id="nn-dataset-type-dropdown"` at `:1331`) |
| `:1842` `model-selection-store` seeded `DEFAULT_MODEL_KEY` (`"cascor"`), `storage_type="memory"` | ✔ exact |
| `:2687` `_gate_dataset_options_handler` — re-gate + auto-snap to first enabled | ✔ exact |
| `:3000` `_build_model_selection_table` | ✔ exact |
| `:3050` `disabled=not is_compatible`, no auto-snap on the model side | ✔ exact |
| `:5422` `restart-ds-type` statically gated | ✔ exact — `options=gated_dataset_options(DEFAULT_MODEL_KEY)`, built once at layout time |
| `src/tests/regression/test_model_table.py:134-135, :143-144` pin current behaviour | ✔ exact |

Two additions the brief did not name, both load-bearing:

- **There is no model dropdown at all any more.** A1b-1 replaced it with a compact
  summary + a "▸ change" button (`dashboard_manager.py:1216-1231`). So the model axis is
  not merely "not clearable" — it has **no input control other than the per-row Select
  buttons**, every one of which is joint-gated at `:3050`.
- **Each store has exactly one writer.** `model-selection-store` is written only by
  `select_model` (`:2591`); `nn-dataset-type-dropdown.value` is written only by
  `gate_dataset_options` (`:2606`). Every other reference is `State`/`Input`. There is no
  second, ungated path into either coordinate. The transition relation below is therefore
  complete, not a sample.

### 0.2 Executed reachability check (not asserted — run)

BFS from the default state over the shipped relation, using the real
`gated_dataset_options` for the sidebar edge and the real `model_reason(...) is None`
predicate for the table edge, against the real registry:

```
|S| total          = 12          (6 datasets x 2 models)
|S_compat|         = 6
|Reach(s0)|        = 5
reachable          = [('circles','cascor'), ('mnist','cascor'), ('moons','cascor'),
                      ('spirals','cascor'), ('xor','cascor')]
COMPATIBLE-BUT-UNREACHABLE = [('equities_seq','recurrence')]
REACHABLE-BUT-INCOMPATIBLE = []
```

The last two lines are the whole defect in two lines: **safety is perfect, coverage is
83 %**, and the missing sixth state is the only state in which the product's flagship
second model can be used at all. `recurrence` is `status="live"` since A1-iv-5 and its
service is deployed and wired (juniper-deploy #132) — the model is shipped and
unreachable.

---

## 1. Formalisation

### 1.1 State space

```
S  :=  D × M
D  =  {spirals, xor, mnist, circles, moons, equities_seq}      (DATASET_TYPES, ordered)
M  =  {cascor, recurrence}                                      (MODELS, ordered)
s0 =  (DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY) = (spirals, cascor)
```

The two coordinates are held in two independent Dash stores — the dataset in
`nn-dataset-type-dropdown.value`, the model in `model-selection-store.data`. There is no
object anywhere in the system that represents the *pair*. That absence is the root of the
whole problem and I will return to it.

`compatible : D × M → Bool` (`model_registry.py:311`) is the joint predicate:
`d.ndim ∈ m.input_ndim ∧ d.task_type ∈ m.supported_task_types ∧ temporal_ok(d, m)`.

```
S_compat := { s ∈ S : compatible(s) },   |S_compat| = 6
```

### 1.2 The transition relation the UI actually implements

Two transition families, one per control. Both are **unilateral** (each changes exactly
one coordinate) and both are guarded by the **full joint predicate** evaluated against
the *other coordinate's current value*.

```
T_dataset :  (d, m) → (d', m)     enabled iff  d' ∈ enabled_datasets(m)
             where enabled_datasets(m) = [ o.value for o in gated_dataset_options(m)
                                           if not o.disabled ]                  -- :2701
             i.e.  iff  dataset_reason(d', m) is None  ≡  compatible(d', m)

T_model   :  (d, m) → (σ(m', d), m')   enabled iff  model_reason(m', d) is None
                                                     ≡  compatible(d, m')       -- :3050
             where σ is the D5 auto-snap in _gate_dataset_options_handler (:2687):
                 σ(m', d) = d                if d ∈ enabled_datasets(m')  or  enabled = ∅
                          = enabled_datasets(m')[0]   otherwise
```

`T_model`'s guard reads the *current dataset*; `T_dataset`'s guard reads the *current
model*. Neither control can be cleared: `clearable=False` at `:1334`, and the model has no
control to clear.

**Note that σ is a no-op on every enabled `T_model` edge.** If the Select button is
enabled then `compatible(d, m')` holds, so `d ∈ enabled_datasets(m')` and σ returns `d`.
The auto-snap — the entire D5 conflict-resolution mechanism — is **unreachable through the
compatibility axis**. It survives only through the *availability* axis (see §4, defect
F-2). So `T_model` reduces exactly to "move the model endpoint along an edge of the
compatibility graph".

### 1.3 The compatibility bipartite graph, and the confinement lemma

Let `G = (D ⊔ M, E)` with `E = { {d, m} : compatible(d, m) }`. A **state in `S_compat` is
literally an edge of `G`**. Then:

- `T_dataset` slides the `D`-endpoint of the current edge to another edge incident on the
  same `M`-vertex.
- `T_model` slides the `M`-endpoint to another edge incident on the same `D`-vertex.

Both moves keep one endpoint fixed. Two edges connected by such a move are adjacent in
`G`. Therefore:

> **Confinement Lemma.** If every transition is *unilateral* and *jointly guarded*, then
> the reachable set from `s0` is exactly the edge set of the connected component of `G`
> containing `s0`:
> **`Reach(s0) = E(comp_G(s0))`**.
>
> *Proof sketch.* (⊆) Every move keeps one endpoint, so successive states are adjacent
> edges; adjacency preserves the component. σ cannot escape either — it lands on an edge
> incident to `m'`, which is already in the component. (⊇) Any two edges in one component
> are joined by a walk `d0 — m1 — d1 — m2 — …`; each alternation is exactly one legal
> unilateral move. ∎

`G` here has **two components**:

```
C1 = {spirals, xor, mnist, circles, moons} ⊔ {cascor}      — 5 edges
C2 = {equities_seq}                        ⊔ {recurrence}  — 1 edge
```

`s0 ∈ C1`, so `Reach(s0) = E(C1)`, `|E(C1)| = 5`. The BFS in §0.2 is this lemma,
executed. **The single missing state is not a bug in a callback; it is the second
component of a disconnected graph, and the UI has no edge that crosses components because
crossing components is precisely what a unilateral jointly-guarded move cannot do.**

### 1.4 The two invariants

| | Statement | Status |
|---|---|---|
| **I-safe** | *Every visited state is compatible.* `∀ s ∈ Reach(s0) . compatible(s)` | **HOLDS.** Enforced by construction — every guard is the joint predicate. Verified: `REACHABLE-BUT-INCOMPATIBLE = ∅`. |
| **I-cover** | *Every compatible state is reachable.* `S_compat ⊆ Reach(s0)` | **FAILS.** `(equities_seq, recurrence)` is compatible and unreachable. |

The implementation believes it enforces "the user can only ever be in a valid
configuration". It does. What it never had, never stated, and never tested is the dual
obligation: **that the valid configurations are all *available*.** Safety and coverage are
independent properties; disabling controls buys the first at the direct expense of the
second, and nothing in the codebase or the design doc names the trade.

`I-safe` is over-strong in a precise sense: it is imposed on *every intermediate state*,
when the property the product actually needs is only over *committed* states. The backend
agrees with me — `POST /api/model/select` (`src/main.py:3731-3746`) validates the model
key against the registry and **nothing else**; it has never heard of the dataset. FR9's
fail-closed lives in the *target model service* at train time. So `I-safe` at every
intermediate UI state is a self-imposed constraint with no counterpart in the system it
is protecting.

### 1.5 The class of bug

> **The mutual-gate trap** (equivalently: *component-confined selection*).
>
> A UI exposes *k* coordinates of a product state space through *k* independent controls,
> and enforces a joint constraint by **disabling, in each control, the options that violate
> the constraint against the other controls' current values**. Because every transition is
> unilateral and every guard is joint, the reachable set collapses to one connected
> component of the constraint graph. Safety holds by construction and looks like
> correctness. Coverage silently equals `|E(comp(s0))| / |E(G)|` and is never measured.

**Recognition heuristic — three conditions, all locally reasonable:**

1. Every control refuses options invalid *against the current value of its peers*
   (joint guard).
2. Every control changes exactly one coordinate (unilateral transition).
3. No coordinate admits an unset / wildcard / "any" value, and none can be cleared.

Any two of those are harmless. All three give you the trap. In canopy, (1) is D2/FR5,
(2) is the two-surface split of D7, and (3) is D4/§5.5's inline ✕ *never having been
implemented*. **The defect is the intersection of three separately-ratified decisions and
one unshipped one — which is exactly why no single code review catches it.**

**The corollary that makes this urgent, not cosmetic.** §6 of the design projects
"dozens-to-hundreds" of model variants across categories i and ii. Every new capability
island — a model on a new input contract plus the dataset that feeds it — is a new
component. Coverage under the current relation is `|E(comp(s0))| / |E(G)|`, so the
fraction of the product that is unreachable **grows monotonically with the registry**.
Today it is 1 state in 6. The design's own roadmap makes it worse on purpose.

**The unary-guard rule** (the mechanically checkable principle the fixes below are
justified by, stated once here because three of the four proposals are instances of it):

> A selector's `disabled` predicate must be a function of that selector's own axis alone —
> "does this option participate in *any* compatible pair?" — never of the peer selector's
> current value. Peer-dependence in a `disabled` predicate is the trap.

Formally: replace `disabled(m') := ¬compatible(d, m')` with
`disabled(m') := compatible_datasets(m') = ∅`. The joint predicate does not disappear; it
moves from *guarding the transition* to *repairing, blocking, or annotating the
destination*. That relocation is the entire content of proposals P2-1, P2-3 and P2-4.

### 1.6 §5.6's premise, tested as shipped

> §5.6: *"A newly **selected** option is never incompatible (greyed). A conflict can only
> arise by **changing** an already-set value so the other side is stranded."*

The premise **holds — and holds too well.** Both controls disable incompatible options, so
the antecedent is satisfied. But the second sentence is *false as shipped*: a conflict can
**never** arise at all, because the only way to strand the other side would be to change a
value to something the peer rejects, and both guards forbid exactly that. §5.6 describes a
conflict state that the implementation made unreachable.

This is not a happy accident. **The mechanism that eliminates the conflict is the same
mechanism that causes the deadlock.** §5.6 reasoned about how to *resolve* a conflict and
never asked what it costs to *prevent* one. The cost is `I-cover`.

Two consequences worth stating plainly:

- **D5's swappable conflict policy has no reachable conflict to switch on.** OQ-6
  ("dataset-primary vs model-primary, decide post-spike") is not merely open — it is
  currently *unobservable*, because both policies produce identical behaviour on an empty
  conflict set. Any proposal that fixes reachability necessarily forces OQ-6, because it
  necessarily creates the first reachable conflict.
- **`test_model_picker.py:91` is a vacuous pass in the integration sense.**
  `test_gate_dataset_options_handler_greys_and_snaps_for_recurrence` asserts
  `(spirals, recurrence) → (equities_seq, recurrence)`. It passes. The transition it
  verifies **cannot be performed by the product**, because reaching `model_key="recurrence"`
  requires clicking a Select button that is disabled whenever the dataset is 2-D. The test
  calls the handler with an argument pair the UI cannot supply. This is the structural
  reason unit-level handler testing cannot see reachability defects: *a unit test chooses
  its own predecessor state; reachability is a property of which predecessor states exist.*

---

## 2. Proposals

Four proposals. They are the four ways to break the Confinement Lemma's hypotheses, which
is also why the brief's options (a)–(d) map onto them one-to-one — the option list is
exhaustive, and I can now say *why* it is exhaustive rather than merely agreeing with it.
An extra mechanism (M5) and two rejections follow in §2.5.

| | Hypothesis broken | Brief's option |
|---|---|---|
| **P2-1** | joint guard → **unary** guard on the model axis; peer repaired | (a) primary axis |
| **P2-2** | adds a universally-guard-passing value `⊥` on each axis | (c) UNSET/null |
| **P2-3** | drops the guard; admits a transient invalid state | (b) transient + resolution |
| **P2-4** | drops **unilaterality**: the transition changes both coordinates atomically | (d) pair as the unit |

---

### P2-1 — Unary model guard with peer repair (model-primary)

**One line.** The model table's Select button stops asking "is this model compatible with
the *current* dataset?" and starts asking "does this model have *any* compatible dataset?";
the already-shipped, already-tested D5 auto-snap then repairs the dataset coordinate.

#### How it works

1. **`_build_model_selection_table` (`:3000`), line `:3050`.** Replace
   `disabled=not is_compatible` with `disabled=not has_any_peer`, where
   `has_any_peer := bool(compatible_datasets(model))` — computed with the injectable
   `compatible_datasets(model, dataset_types=…)` already in `model_registry.py:329`. The
   compatibility cell (`:3041-3044`) is **unchanged**: `model_reason(model, dataset)` still
   renders "needs 3-D data" as *information*. The reason stops being a *prohibition* and
   becomes an *annotation* — which is what D2/FR5 asked for and D-in-§11 ("indicator-only")
   was rejected only as the *sole* mechanism, not as an annotation.
2. **`_gate_dataset_options_handler` (`:2687`) is unchanged.** Its snap branch —
   `if current_value in enabled or not enabled: … return options, enabled[0]` — starts
   firing for the first time on the compatibility axis. This is the whole point: the repair
   machinery exists, is correct, and is unit-tested at `test_model_picker.py:91`. **The fix
   is to delete the guard that made an already-shipped, already-tested repair
   unreachable.**
3. **Notice (required, not optional).** `select_model` (`:2591`) gains an output writing a
   dismissible `dbc.Alert` into a new `model-dataset-snap-notice` div in the sidebar:
   *"Switched to Recurrence (LMU); dataset changed to Equities (sequence) — CasCor's Spirals
   is not 3-D."* Copy the existing `train-gate-notice` pattern (`:2658-2664`,
   `_train_gate_notice_handler` at `:2966`). Without this the change violates FR4.
4. **`restart-ds-type` (`:5422`) must be fixed in the same PR** — see F-1 in §4. Once
   `(equities_seq, recurrence)` is reachable, that statically-gated dropdown becomes a live
   `REACHABLE-BUT-INCOMPATIBLE` path.

#### Invariant established

```
I-safe   PRESERVED, in the strong form:   ∀ s ∈ Reach(s0) . compatible(s)
I-cover  ESTABLISHED:                     S_compat ⊆ Reach(s0),  and in fact
                                          Reach(s0) = S_compat exactly
I-strong ESTABLISHED:                     the reachable subgraph is strongly connected
                                          (from any s, selecting cascor returns you to C1)
I-unary  NEW, and the machine-checkable justification:
         ∀ m ∈ M . (model-table Select for m is disabled)  ⟺  compatible_datasets(m) = ∅
```

`I-safe` is **preserved, not weakened**, because σ repairs the peer *within the same
transition*: there is no intermediate published state. This is P2-1's decisive advantage —
it is the only proposal of the four that gains `I-cover` at zero cost to `I-safe`.

`I-unary` is the important one: it is a property of *one function of one argument*, so it
is checkable by a test that never has to enumerate the state space, and it *implies*
`I-cover` given the Confinement Lemma's converse. That is what "justified by an invariant
rather than by a patch that unsticks this pair" means here.

#### Strengths

- **Smallest diff of the four.** One predicate at `:3050`, plus a notice. No new state, no
  new store, no new control, no downstream consumer touched.
- **Reuses tested machinery.** σ is already implemented and already has a passing unit test;
  P2-1 converts that test from vacuous to load-bearing.
- **Resolves OQ-6 decisively as model-primary** — the option §5.6 itself notes "fits the
  model-centric benchmarking trajectory", and which D6/D7/§6 (model browsing is the load-
  bearing problem; the sidebar carries no scale pressure) independently argue for.
- **Scales.** Coverage is `1.0` for any registry, any number of components, without change.
- **Keeps `I-safe` at every published state**, so every downstream consumer of the two
  stores (`resolve_oneshot_start_body` at `:2639`, `apply_dataset`, `execute_restart` at
  `:5381`, `open_live_switch_modal` at `:5147`) keeps its current precondition exactly.

#### Weaknesses

- **Silently mutates a coordinate the user did not touch.** Clicking a model row *to read
  its description* changes the dataset. Mitigated by the notice; not eliminated.
- **σ picks `enabled_datasets(m')[0]` — registry order.** The repaired value is an
  arbitrary, unaudited choice that will change silently when someone reorders
  `DATASET_TYPES`. At 6 datasets this is invisible; at 30 it is a real usability defect and
  a real reproducibility defect for benchmarking.
- **Asymmetric.** The dataset dropdown keeps its joint guard. Defensible (the dataset is the
  repaired axis) but it will read as arbitrary to anyone who has not read this document.
- **Discards staged dataset work.** The sidebar carries schema-driven generator params
  (`nn-dataset-schema-params`, `:2793-2800`) and an "Apply Dataset" staging flow; a snap
  invalidates them without asking.

#### Risks

- **R1 — a model with no compatible dataset breaks `I-safe`.** If
  `compatible_datasets(m') = ∅`, σ's `or not enabled` branch returns `no_update` and the UI
  lands in `(d, m')` with `d` incompatible — a `REACHABLE-BUT-INCOMPATIBLE` state, the first
  the product would ever have had. **This is precisely why the guard must be `I-unary` and
  not simply removed.** With `I-unary` that row is disabled and the state is unreachable.
  A code review that "just deletes the `disabled=`" introduces this; the guardrail below
  catches it.
- **R2 — the notice is the only thing standing between P2-1 and an FR4 violation.** It is
  the easiest part to drop under time pressure and the hardest to test. Pin it.
- **R3 — F-1 (`:5422`) is *activated* by this fix.** Unreachable-today becomes
  reachable-tomorrow. Classic "a broken thing masks the next one".

#### Guardrails

The property test in §3 (mandatory, and it is the deliverable of this whole proposal),
plus:

- `test_model_table_disabled_predicate_is_unary` — for every model in a **synthetic**
  registry containing at least one model with a compatible peer and one without, assert the
  Select button's `disabled` equals `compatible_datasets(m) == ∅` and is **invariant under
  the `dataset_value` argument**. Written as: build the table once per dataset in `D` and
  assert the disabled-set is identical across all of them. That single assertion *is*
  `I-unary`, and it is the assertion that fails the day someone re-introduces a joint guard.
- `test_model_swap_emits_a_pair_change_notice` — assert `select_model` returns non-empty
  notice children exactly when `σ(m', d) ≠ d`.
- `test_restart_ds_type_options_track_the_selected_model` — F-1's regression pin.

#### Behaviour at ≥3 components, and at the §5.8 degenerate state

- **≥3 components:** fully correct with no change. Every model is one click from every
  state, and every model lands in its own component. `Reach = S_compat` for any `G`.
- **A model with no compatible dataset:** disabled by `I-unary`, with a reason cell reading
  "no compatible dataset in this deployment". The row stays *visible* (D8/§5.7's "shown but
  not trainable" precedent) — but note this is a *third* disable reason, distinct from both
  incompatibility and lifecycle status, and the modal now needs three visually distinct
  states. Say so in the UI copy.
- **A dataset with no compatible model:** unchanged from today — `_build_model_selection_table`
  already renders the §5.8 recovery alert (`:3062-3072`). But see F-6: that alert's advice is
  not verified against the gate that would have to admit it.

#### Design-of-record impact

- **Upholds** D2 (reason at the locus — the reason cell stays, it just stops prohibiting),
  D5 (the swappable policy is retained and, for the first time, *invoked*), D7, D8, FR9.
- **Resolves OQ-6 → model-primary.** This should be recorded as a ratified decision, not
  left open. §5.6's dataset-primary/model-primary framing survives verbatim; only the
  default is filled in.
- **Amends §5.6's premise.** The sentence *"A newly selected option is never incompatible
  (greyed)"* becomes false by design on the model axis and must be rewritten, together with
  a new clause stating the coverage obligation. Proposed replacement text:
  *"A newly selected **model** may be incompatible with the current dataset; the dataset is
  then repaired to the model's first compatible dataset with a notice (model-primary, OQ-6
  ratified 2026-09-XX). A control disables an option only when that option participates in
  no compatible pair at all (the unary-guard rule); no control's disabled set depends on the
  peer's current value. Coverage — every compatible pair reachable from the default pair —
  is a first-class obligation alongside safety and is enforced by
  `test_selection_reachability.py`."*
- **Amends §5.4/FR5** to distinguish *annotating* an incompatible option from *disabling* it.
- **Does not close** FR6/D4 (the inline ✕ is still unshipped) — see F-4.

---

### P2-2 — `⊥` on both axes ("Any" / clear), shipping D4's unshipped ✕

**One line.** Give each axis an explicit *unset* value that is compatible with everything;
the graph gains a universal vertex on each side and becomes connected through it.

#### How it works

1. **Dataset axis.** `:1334` `clearable=False` → `clearable=True`. Then
   `_gate_dataset_options_handler` (`:2687`) must gain a `⊥` guard as its **first** line —
   `if current_value is None: return options, dash.no_update` — because today
   `None ∉ enabled` and `enabled ≠ ∅`, so clearing would immediately snap the value back to
   `enabled[0]` and the ✕ would appear broken. This is a two-line change with a one-line
   trap in it.
2. **Model axis.** Add a "Show all models / clear selection" button to the modal footer
   (`:2220` region, beside `model-selection-modal-close`) writing `None` into
   `model-selection-store`. `_gate_dataset_options_handler` already returns
   `(no_update, no_update)` for a falsy `model_key` (`:2701`) — so a cleared model already
   ungates the dataset dropdown, correctly, today. That half is *already implemented*.
3. **Table.** `_build_model_selection_table(None, …)` already treats every model as
   compatible when `dataset_value` is falsy (`:3036`, `dataset = … if dataset_value else
   None`), and this is **already tested** — `test_model_table.py`
   `test_table_without_a_dataset_treats_all_models_as_compatible`. That code path is
   currently **dead**: reachable from tests only. P2-2 makes it live.
4. **Train gate.** `_update_button_appearance_handler` must force-disable Start when either
   coordinate is `⊥`, alongside the existing `model_is_trainable` gate, with a notice
   ("select a dataset to train"). Same pattern as `train-gate-notice` (`:2658`).
5. **Downstream `None`-tolerance audit.** Every consumer of
   `nn-dataset-type-dropdown.value` must accept `None`: `resolve_oneshot_start_body`
   (`:2639` — already returns `None` on falsy), `render_dataset_params` (`:2624`),
   `annotate_model_hint` (`:2649` — already handles it, `_dataset_model_hint_handler`
   returns `""`), `open_live_switch_modal` (`:5153`), the live-switch accept path (`:5210`),
   `execute_restart` (`:5285`). Three of six already tolerate it; three need review.

#### Invariant established

```
I-safe   WEAKENED, deliberately, to:
         ∀ s ∈ Reach(s0) . complete(s) ⇒ compatible(s)
         where complete(d, m) := d ≠ ⊥ ∧ m ≠ ⊥
I-train  NEW (and this is what actually protects the backend):
         the Start button is enabled ⇒ complete(s) ∧ compatible(s) ∧ model_is_trainable(m)
I-cover  ESTABLISHED:  S_compat ⊆ Reach(s0)
         via the 2-step path  (d, m) → (⊥, m) → (⊥, m') → (d', m')  for any m'
```

The weakening is real and must be stated as such: the product now admits states that are
not compatible pairs — they are simply not *pairs*. Everything that consumed "there is
always a selected dataset" must be re-verified. In exchange, `⊥` is a cut vertex adjacent
to every edge, so `G ∪ {⊥}` is connected **for any registry, unconditionally** — P2-2 is the
only proposal whose connectivity argument does not depend on the shape of `G` at all.

#### Strengths

- **Closes an outstanding design commitment.** D4 and §5.5 specified the inline ✕; FR6
  requires clear/reset. It was never shipped. P2-2 is *implementation debt repayment*, not a
  design amendment — the cheapest possible governance story.
- **Half of it already exists and is already tested** (items 2 and 3 above). The table's
  `dataset=None` branch and the gate handler's `not model_key` branch are both live code
  today, reachable only from tests.
- **Most robust degenerate behaviour of the four** (see below).
- **Never silently mutates a user's choice** — the user does the clearing. FR4 is satisfied
  trivially. No notice needed for correctness.
- **Composes with every other proposal** — `⊥` is orthogonal to how transitions are guarded.

#### Weaknesses

- **Two clicks to change model, not one** — clear, then select. At 100+ variants (§6) this
  is a genuine friction cost on the product's *primary* workflow.
- **Widest blast radius of the four.** Six downstream consumers, a new Start gate, and a new
  "incomplete" presentation state across the sidebar, the restart modal, and the live-switch
  modal.
- **`⊥` is a new state class that every future consumer must know about.** It is the kind of
  thing that gets forgotten in the *next* feature, producing `None`-propagation bugs a long
  way from here.

#### Risks

- **R1 — the snap-back trap.** If the `current_value is None` guard is omitted from
  `_gate_dataset_options_handler`, clearing the dropdown silently re-selects `enabled[0]`
  and the ✕ appears to do nothing. Cheap to write, easy to omit, and it will look like a
  Dash quirk rather than a logic error.
- **R2 — `⊥` reaches a service.** `_resolve_oneshot_start_body_handler` returns `None` for a
  falsy generator, so the one-shot Start body becomes `None` and
  `RecurrenceBackend.start_training` bails with "no dataset reference". That is a *silent
  no-op start*, not a clear error. `I-train` must be enforced at the button, not discovered
  at the backend.
- **R3 — `⊥` persists across a reload?** `model-selection-store` is `storage_type="memory"`,
  so no. But if anyone later promotes it to `"local"` (as `layout-state-store` and
  `pinned-params-store` already are), a user returns to a dashboard with no model selected
  and no obvious reason. Pin the storage type in a test.

#### Guardrails

- The §3 property test, with `⊥` added to `D` and `M` and `I-cover` asserted over
  `S_compat` only (the `⊥` states are reachable but are not required to be compatible).
- `test_clearing_the_dataset_does_not_snap_back` — call
  `_gate_dataset_options_handler("cascor", None)` and assert the returned value is
  `dash.no_update`. **This is R1's tripwire and it is one line.**
- `test_start_is_disabled_on_an_incomplete_selection` — parametrised over
  `(⊥, m), (d, ⊥), (⊥, ⊥)`.
- `test_selection_stores_are_memory_scoped` — pin `storage_type="memory"` on both stores.

#### Behaviour at ≥3 components, and at the §5.8 degenerate state

- **≥3 components:** correct, unconditionally, and this is P2-2's structural distinction.
  `⊥` is adjacent to every vertex, so the graph is connected however many islands the
  registry grows. Every other proposal argues connectivity from the *transition relation*;
  P2-2 argues it from the *graph*, which is a stronger and simpler argument.
- **A model with no compatible peer:** selectable (it is compatible with `⊥`); the dataset
  dropdown then shows every option disabled and the §5.8 message fires. The state is
  `(⊥, m)` — *incomplete*, not *invalid* — Start is blocked by `I-train`, and the user
  escapes by clearing the model. **This is the cleanest degenerate handling of the four**:
  it needs no third disable-reason and no special case, because "no compatible peer" is
  just "the only compatible peer is `⊥`".
- **A dataset with no compatible model:** symmetric.

#### Design-of-record impact

- **Upholds and finally implements** D4, §5.5, FR6 — all currently unshipped.
- **Upholds** D2, D5, D7, D8 unchanged.
- **Amends §5.8** to distinguish *incomplete* (a `⊥` coordinate — a normal, expected,
  escapable state) from *degenerate* (a genuinely empty compatible set). The current text
  conflates them.
- **Does not resolve OQ-6.** With `⊥` available the user resolves conflicts manually, so no
  automatic policy is needed. OQ-6 becomes *lower priority*, not answered — and that is a
  weakness, because it leaves a ratified-but-undecided decision open indefinitely.
- **Requires a new FR** for the train gate: *"FR16 — Start is enabled only for a complete,
  compatible, trainable pair."*

---

### P2-3 — Explicit conflict state with a resolution step

**One line.** Remove both guards; let the pair be incompatible; make the conflict a
first-class, visible, non-trainable state with a one-click resolution — i.e. actually build
the §5.6 machine the design describes.

#### How it works

1. **`:3050`** `disabled=not is_compatible` → `disabled=False` (lifecycle greying via D8
   still applies elsewhere). **`gated_dataset_options`** stops emitting `disabled: True` for
   the model-compat axis and emits a `⚠` reason suffix instead; `apply_availability_gate`'s
   deployment-availability disabling is **retained** (it is a genuinely unary property of
   the dataset — see F-2 — and is exactly the kind of guard the unary rule permits).
2. **`_gate_dataset_options_handler` (`:2687`) loses its snap entirely** and becomes a pure
   options-recomputation. σ is deleted, not merely bypassed.
3. **New derived state.** A single callback with `Input(model-selection-store)` +
   `Input(nn-dataset-type-dropdown.value)` writes a `selection-conflict-store` holding
   `None` or `{"dataset": d, "model": m, "reason": model_reason(m, d)}`. Derived, never
   authored — one writer, no `allow_duplicate`, consistent with the F-CANOPY-018/027
   two-writer discipline this codebase has been enforcing.
4. **Resolution UI.** When the store is non-`None`, a persistent sidebar banner:
   *"Recurrence (LMU) cannot train Spirals — needs 3-D data. [Use Equities (sequence)]
   [Back to CasCor]"* — the two buttons are literally D5's model-primary and dataset-primary
   policies, offered at the moment of conflict rather than chosen in advance.
5. **Train gate.** Start force-disabled while `selection-conflict-store` is non-`None`.

#### Invariant established

```
I-safe   REPLACED.  "every visited state is compatible"  is abandoned.
I-train  NEW, and it is now the ONLY safety property:
         Start enabled  ⇒  compatible(s) ∧ model_is_trainable(m)
I-escape NEW:  ∀ s ∈ S . ¬compatible(s) ⇒ ∃ one-click t with compatible(t)
         (i.e. no conflict is a dead end — the resolution buttons are always both offered
          and at least one always leads somewhere valid)
I-cover  ESTABLISHED:  Reach(s0) = S  (the FULL product space; S_compat ⊆ S trivially)
```

This is a **replacement**, not a weakening, and it is the honest one: it relocates safety
from "where can the user be" to "what can the user do", which is where the backend already
puts it. FR9 already says the target service fails closed on shape mismatch; §5.9 already
says "a UI desync cannot train an invalid pair"; D5 already says "greying is best-effort,
**not** the correctness guarantee". P2-3 is the only proposal that takes D5 completely at
its word. Under P2-3, `I-safe` was never the correctness guarantee — and D5 says so in
writing.

`I-escape` is the property that stops this becoming a *different* trap; it must be tested,
not assumed.

#### Strengths

- **Most faithful to the design of record.** D5 states the predicate + backend are the
  guarantee and greying is best-effort. P2-3 is that sentence, implemented.
- **`Reach = S`.** No component argument needed at all — the relation is total. This is the
  only proposal for which the Confinement Lemma is simply inapplicable.
- **Generalises to non-binary constraints.** The moment compatibility acquires a *warning*
  tier (a model that *works* on a dataset but poorly — inevitable across 100+ benchmark
  variants, §6), disable-based gating has nowhere to put it. A conflict/notice state does.
- **Resolves OQ-6 by making it a runtime choice**, per conflict, which is strictly more
  informative than a global default — and it makes both policies *observable*, which they
  are not today.
- **Every state is one click from every other state on each axis** — the best possible
  navigation for a benchmarking product.

#### Weaknesses

- **Largest change and the largest test surface.** A new store, a new banner, a new train
  gate, two callback rewrites, and the deletion of σ.
- **Abandons an invariant that currently holds perfectly.** That is a hard sell on review
  even when correct, and it will read as a regression to anyone who has not read §1.4.
- **Users can sit in an invalid state.** For a research dashboard this is fine; the cost is
  that every downstream reader of the two stores must now tolerate an incompatible pair
  without crashing — a real audit across the six consumers listed in P2-2 item 5.
- **The conflict banner competes for sidebar space** with `nn-model-dataset-hint`,
  `train-gate-notice`, and the §5.8 alert. Three notices in one rail is a design problem in
  its own right.

#### Risks

- **R1 — an invalid pair reaches a service.** `_resolve_oneshot_start_body_handler` (`:2639`)
  keys only on `model-class-store == "one_shot"` and the raw dropdown value; it will happily
  build `{"dataset": {"generator": "spirals"}}` for the recurrence service. FR9 says the
  service fails closed — but "fails closed" here means an opaque 4xx/5xx surfaced as a
  failed training run, not a clear UI message. `I-train` must be enforced at the button.
- **R2 — `I-escape` is easy to break.** If both resolution buttons are ever rendered
  conditionally (e.g. the "Use Equities" button suppressed when the dataset is
  availability-gated), a user can be stuck in a conflict with no exit. Must be tested
  exhaustively over the registry, not spot-checked.
- **R3 — the conflict state is persistable.** If a future FR15 hydration restores an
  incompatible pair from the backend, the user opens the dashboard *in* a conflict. Correct
  under P2-3, but the first-paint copy has to be written for it.

#### Guardrails

- The §3 property test, with `I-cover` asserted as `Reach(s0) == S` (the full product), plus:
- **`test_every_incompatible_state_has_a_one_click_escape`** — for every
  `(d, m) ∈ S \ S_compat`, assert the conflict store is non-`None` and that at least one
  offered resolution leads to a state in `S_compat`. **This is `I-escape` and it is the test
  that keeps P2-3 from becoming a new trap.**
- `test_start_is_disabled_in_every_incompatible_state` — parametrised over `S \ S_compat`.
- `test_conflict_store_has_exactly_one_writer` — a callback-graph lint; note this repo
  already has `src/tests/unit/test_control_graph_lint.py`, so the harness exists.

#### Behaviour at ≥3 components, and at the §5.8 degenerate state

- **≥3 components:** irrelevant by construction — the relation is total. P2-3 is the only
  proposal where the number of components has *no bearing whatsoever* on behaviour.
- **A model or dataset with no compatible peer:** selecting it produces a permanent conflict
  state. `I-escape` still holds — the escape is to change the *other* coordinate back —
  and the banner should say so explicitly: *"No dataset in this deployment can train
  Recurrence (LMU). [Back to CasCor]"*. This is §5.8's degenerate state, reached and handled
  by the *same* mechanism as an ordinary conflict, with no special case. That uniformity is
  P2-3's real elegance.

#### Design-of-record impact

- **Upholds** D5 completely (it is the first implementation that honours "greying is
  best-effort, not the correctness guarantee"), D2, D7, D8, FR9, §5.9.
- **Overturns FR5** — *"Incompatible options stay visible but **disabled**"*. Under P2-3
  they stay visible and **enabled**, with the reason attached. This is a genuine overturn
  and must be balloted, not slipped in.
- **Resolves OQ-6** by dissolving the "swappable global policy" framing into a per-conflict
  choice. D5's text needs amending to say the policy is *offered*, not *configured*.
- **Amends §5.6** wholesale: the premise ("a newly selected option is never incompatible")
  is deliberately inverted.
- **Adds FR16** (train gate) and **FR17** (*"every incompatible state has a one-click
  escape"*).

---

### P2-4 — The pair is the unit of selection (atomic pair commit)

**One line.** Break *unilaterality*: a model-table row commits `(model, dataset)` together —
an incompatible row expands to let the user pick which compatible dataset to move to, and
the transition changes both coordinates in one step.

#### How it works

1. **`_build_model_selection_table` (`:3000`)**: an incompatible row's Select button becomes
   a split control — `Select ▾` — whose menu lists `compatible_datasets(model)` by label
   (registry order, injectable). A compatible row keeps its plain `Select` (committing
   `(m', d)` with the dataset unchanged). The button id gains the dataset:
   `{"type": "model-select-btn", "index": m, "dataset": d'}`. Dash pattern-matching
   supports a third key; the `ALL` wildcard at `:2595` becomes
   `{"type": "model-select-btn", "index": ALL, "dataset": ALL}`.
2. **`_select_model_from_table_handler` (`:2913`)** reads both `triggered_id["index"]` and
   `triggered_id["dataset"]` and returns **five** outputs — adding
   `Output("nn-dataset-type-dropdown", "value", allow_duplicate=True)`. **This is the one
   real architectural cost**: `nn-dataset-type-dropdown.value` gains a second writer, and
   this codebase has been actively *removing* two-writer patterns (F-CANOPY-018 /
   F-CANOPY-027, see the comments at `:2470` and `:3078`). The mitigation is to route the
   pair through a single new `selection-store` holding `{"model": …, "dataset": …}` and have
   *one* callback fan it out to the dropdown and the model store — which restores
   single-writer discipline at the cost of one more store.
3. **`_gate_dataset_options_handler` (`:2687`)** keeps its joint gate (correct: the dataset
   dropdown is now a *within-model* refinement) and σ becomes provably dead — assert it.
4. **Sidebar dropdown** unchanged.

#### Invariant established

```
I-safe   PRESERVED, in the strongest form of the four:
         every transition maps S_compat → S_compat atomically; no intermediate state
         is ever published, not even within a callback chain.
I-cover  ESTABLISHED:  Reach(s0) = S_compat, with diameter 1 in the model coordinate —
         every compatible pair is reachable in ONE click from every other.
I-atomic NEW and machine-checkable:
         ∀ enabled controls c . commit(c) ∈ S_compat
         (the destination is a literal, complete, compatible pair carried in the
          control's own id — so validity is checkable by inspecting the rendered tree,
          with no reference to current state at all)
```

`I-atomic` is the strongest invariant available here and the easiest to check: **you can
verify correctness by walking the rendered component tree and validating each button's id
against `compatible()`. No state-space search, no BFS, no simulation.** Every other
proposal needs a reachability argument; P2-4 needs only a well-formedness argument on the
rendered output. For a lens that insists fixes be justified by mechanically checkable
invariants, that is the strongest thing on this page.

#### Strengths

- **FR4 satisfied exactly** — "when >1 option remains compatible, the user chooses within
  the set (no silent auto-pick)". No silent mutation, no notice needed, no undo needed.
- **Diameter 1.** One click from any compatible pair to any other. Best navigation of the
  four.
- **Correct model for a benchmarking product.** §6/D6/FR13 make "which (model, dataset) pair
  produced this benchmark result" the central object; making the pair the unit of selection
  aligns the UI with the domain. The absence of a pair object (§1.1) is the root cause; P2-4
  is the only proposal that *removes* the root cause rather than working around it.
- **Never discards staged dataset config silently** — the dataset change is the user's
  explicit act.

#### Weaknesses

- **Most new UI**: a split-button/menu control per incompatible row, at exactly the moment
  §6 says the table will have hundreds of rows.
- **Menu length is unbounded.** A model compatible with 40 datasets gets a 40-item menu.
  Needs a "…more" escape to a dataset picker, which is scope creep.
- **The second writer problem** (item 2) is a real regression risk against a discipline this
  codebase has been deliberately enforcing; the extra store is a real cost.
- **Does not resolve OQ-6 — it dissolves it.** There is no conflict, so there is no policy.
  Defensible, but it leaves a ratified decision formally open.

#### Risks

- **R1 — pattern-matching id shape change breaks the existing select callback.** `:2595`'s
  `ALL` wildcard and `test_model_table.py`'s `button.id["index"]` assertions both assume a
  two-key id. Cheap to fix, easy to miss, and it will fail loudly. Acceptable.
- **R2 — the split button's *default* action.** If clicking the main body of `Select ▾`
  (rather than the menu) does anything at all, it must not silently pick a dataset — that
  would re-introduce P2-1's silent snap through the back door, while claiming FR4
  compliance. Specify: the main body opens the menu, full stop.
- **R3 — the two-writer mitigation store adds a third state object** to a page that already
  has `model-selection-store`, `model-class-store` and `oneshot-start-params-store`.
  Consolidation is the right answer and it is a bigger PR.

#### Guardrails

- The §3 property test, plus the strongest and cheapest check available anywhere in this
  document:
- **`test_every_rendered_select_control_commits_a_compatible_pair`** — build the table for
  **every** dataset in `D` (and for `None`), walk every rendered control, and assert
  `compatible(get_dataset_spec(btn.id["dataset"]), get_model_spec(btn.id["index"]))` for
  every enabled one. That is `I-atomic`, it needs no simulation, and it scales to any
  registry.
- `test_no_enabled_control_omits_a_dataset` — every enabled select id carries both keys.
- `test_select_menu_covers_compatible_datasets_exactly` — for each model, the offered
  dataset set equals `compatible_datasets(m)`. Pins `I-cover` at the control level.
- `test_dataset_dropdown_has_exactly_one_writer` (the `allow_duplicate` guard).

#### Behaviour at ≥3 components, and at the §5.8 degenerate state

- **≥3 components:** fully correct, unconditionally — every row offers its own component's
  datasets, so every component is one click away. Like P2-3, component count is irrelevant.
- **A model with no compatible dataset:** `compatible_datasets(m) = ∅` ⇒ the menu is empty
  ⇒ the row is disabled with reason "no compatible dataset in this deployment". **This is
  the unary-guard rule falling out of the mechanism for free**, rather than being imposed on
  top of it as in P2-1 — the guard is "is the menu empty", which is definitionally unary.
  That is a genuine structural advantage.
- **A dataset with no compatible model:** the §5.8 alert as today; and unlike today the
  advice is actionable, because every row's menu offers a dataset the user can move to (see
  F-6).

#### Design-of-record impact

- **Upholds** D2, D7, D8, FR9, and satisfies **FR4** more exactly than any other proposal.
- **Amends FR5**: incompatible rows are visible and *actionable*, not disabled.
- **Amends §5.6** by removing its subject matter — with atomic pair commits there is no
  stranded side, so the conflict-resolution section becomes vestigial. Record this
  explicitly rather than leaving a stale section.
- **Amends §5.1/§5.3**: the sidebar dropdown becomes a *within-model refinement*, not a
  co-equal selector. The two-surface split of D7 survives but the surfaces stop being
  symmetric.
- **Does not resolve OQ-6**; recommend recording OQ-6 as *withdrawn — no reachable conflict
  under D-pair*.
- **Suggests a new decision D9**: *"the (model, dataset) pair is the unit of selection and
  the unit of benchmark identity"*, which also serves FR13.

---

### 2.5 Mechanisms considered and not proposed

**M5 — Initial-state widening (FR15 hydration + deep links).** Hydrate
`model-selection-store` from the backend at mount and accept `?model=&dataset=` query
params, validating the pair against the registry and falling back to the first compatible
pair with a notice. This *does* make `(equities_seq, recurrence)` reachable — from a URL. It
changes `Reach(s0)` into `Reach(S0) = ⋃_{s ∈ S0} E(comp(s))`, so with a wide enough `S0`
every component is entered.

**Rejected as a fix, for a reason worth stating.** It does not repair the transition
relation; it only widens the entry points. In-session navigation stays confined, so a user
who arrives at `(equities_seq, recurrence)` by URL and then clicks anything falls back into
`C1` and cannot return. Worse, **it hides the defect**: coverage looks fixed, the trap is
still there, and the next component to land is unreachable again with no symptom until
someone tries. A fix that removes the symptom while preserving the mechanism is the worst
outcome available. M5 is nonetheless **required independently** — FR15 is unimplemented and
is causing a live split-brain (F-3) — so it should ship, on its own merits, in its own PR,
and never be described as addressing this defect.

**M6 — Connector element ("universal" dataset or model).** Seed a synthetic dataset
compatible with every model (or vice versa) so `G` is connected by construction.
**Rejected**: it makes the registry lie about capabilities to work around a UI limitation,
it puts a fake entry in front of users, and it fails the moment a genuinely exotic model
lands that the connector cannot honestly claim to feed. `⊥` (P2-2) is the principled
version of this idea — a connector that is explicitly *not a dataset*.

**M7 — Compute the compatible set at build time and forbid disconnected registries (a CI
gate on component count = 1).** **Rejected**: it constrains the *domain* to fit the UI. §6
promises capability islands; a registry that must stay connected cannot express them. Worth
keeping only as a *warning* in the property test's failure message — "this registry has N
components; verify the selection surface can cross them" — which is exactly how I have
written §3.

---

## 3. The guardrail artifact — a reachability property test over the full registry

This is the single most valuable deliverable in this document. It is **proposal-independent**:
it fails today, passes under any of P2-1..P2-4, and fails again the day a 7th dataset or a
3rd model lands in a new component. Ship it *first*, watch it go red, then fix.

Location: `src/tests/regression/test_selection_reachability.py`.

```python
"""Reachability of the (dataset x model) selection state space (canopy #368).

The A1b selection surface enforces SAFETY -- "every visited pair is compatible" -- by
disabling, in each control, the options incompatible with the OTHER control's current
value. Safety is not the whole obligation. The dual property is COVERAGE: every
compatible pair must be REACHABLE from the default pair by legal UI moves. The two are
independent, and only safety was ever tested.

Coverage failed for ("equities_seq", "recurrence") from A1b-1 until <fix PR>: the
compatibility relation is a bipartite graph on datasets x models, unilateral
jointly-guarded transitions cannot cross its connected components, and the 3-D seed pair
is a component of its own. The UI could not reach the product's flagship second model.

These tests recompute the transition relation FROM THE SHIPPED FUNCTIONS the callbacks
call -- not from a re-derivation -- do a BFS from the default state, and compare
Reach(s0) against S_compat over the FULL registry. Anything that lands in a new component
fails `test_every_compatible_pair_is_reachable` on the next CI run.

Do NOT weaken these to the two current seeds. The value of this file is that it is
quantified over the registry, not over an example.
"""
```

Core helpers — note that each one calls the *production* function, so a change to the
gating logic changes the test's model of the transition relation automatically:

```python
def _enabled_datasets(model_key):
    """Dataset values the sidebar dropdown will let the user pick, given model_key.

    Computed the way the callback computes it (dashboard_manager.py:2701): the real
    gated_dataset_options composed with the availability gate. An ALL-AVAILABLE generator
    list is passed so this measures the COMPATIBILITY gate only -- deployment availability
    is a separate, unary axis and is asserted separately.
    """
    from dataset_schema import apply_availability_gate
    opts = apply_availability_gate(gated_dataset_options(model_key), [])
    return [o["value"] for o in opts if not o.get("disabled")]


def _enabled_models(dataset_value):
    """Model keys whose table Select button is not `disabled`.

    Read out of the REAL _build_model_selection_table output, not re-derived from
    model_reason -- so a change to :3050 is caught here even if the registry is untouched.
    """
    table = DashboardManager._build_model_selection_table(dataset_value, None)
    return [b.id["index"] for b in _select_buttons(table) if not b.disabled]


def _successors(manager, state):
    d, m = state
    out = set()
    for d2 in _enabled_datasets(m):                  # T_dataset
        out.add((d2, m))
    for m2 in _enabled_models(d):                    # T_model, incl. the D5 snap
        _opts, snapped = manager._gate_dataset_options_handler(m2, d)
        out.add((d if snapped is dash.no_update else snapped, m2))
    return out


def _reachable(manager, start):
    seen, stack = {start}, [start]
    while stack:
        for t in _successors(manager, stack.pop()):
            if t not in seen:
                seen.add(t)
                stack.append(t)
    return seen


def _components():
    """Connected components of the dataset x model compatibility bipartite graph."""
    parent = {("d", d.value): ("d", d.value) for d in DATASET_TYPES}
    parent.update({("m", x.key): ("m", x.key) for x in MODELS})
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for d in DATASET_TYPES:
        for m in MODELS:
            if compatible(d, m):
                parent[find(("d", d.value))] = find(("m", m.key))
    groups = {}
    for node in parent:
        groups.setdefault(find(node), set()).add(node)
    return list(groups.values())
```

The five tests:

```python
def test_every_compatible_pair_is_reachable_from_the_default_pair(manager):
    """COVERAGE (I-cover). The headline property. This is the one that was missing."""
    s0 = (DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY)
    compat = {(d.value, m.key) for d in DATASET_TYPES for m in MODELS if compatible(d, m)}
    missing = compat - _reachable(manager, s0)
    assert not missing, (
        f"{len(missing)} compatible pair(s) are UNREACHABLE from {s0}: {sorted(missing)}.\n"
        f"The compatibility graph has {len(_components())} connected component(s); "
        f"unilateral jointly-guarded UI transitions cannot cross components (canopy #368). "
        f"A new model or dataset in its own component needs the selection surface to offer "
        f"a component-crossing transition -- see the P2 reachability analysis."
    )


def test_no_incompatible_pair_is_reachable(manager):
    """SAFETY (I-safe). Never previously asserted anywhere -- it held by accident of the
    guards. Under P2-2 restate as 'no incompatible COMPLETE pair'; under P2-3 replace with
    test_start_is_disabled_in_every_incompatible_state."""
    s0 = (DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY)
    bad = {s for s in _reachable(manager, s0)
           if not compatible(get_dataset_spec(s[0]), get_model_spec(s[1]))}
    assert not bad, f"reachable but INCOMPATIBLE: {sorted(bad)}"


def test_reachability_is_strongly_connected(manager):
    """No compatible pair is a one-way door. Forward reachability alone would allow a
    'roach motel' state the user can enter and never leave -- a second-order form of the
    same trap, and the most likely way a naive fix goes wrong."""
    s0 = (DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY)
    for s in _reachable(manager, s0):
        assert s0 in _reachable(manager, s), f"{s} cannot return to the default pair {s0}"


def test_default_pair_is_compatible():
    """FR11. Cheap, and it is the anchor every other test in this file depends on."""
    assert compatible(get_dataset_spec(DEFAULT_DATASET_TYPE),
                      get_model_spec(DEFAULT_MODEL_KEY))


def test_every_model_and_dataset_has_a_compatible_peer():
    """The section-5.8 degenerate state is NOT currently entered by the seeds. If this
    starts failing, the empty-compatible-set path becomes live and must be exercised --
    it is currently only covered for the dataset side (test_model_table.py)."""
    for m in MODELS:
        assert compatible_datasets(m), f"{m.key} has no compatible dataset (section 5.8)"
    for d in DATASET_TYPES:
        assert compatible_models(d), f"{d.value} has no compatible model (section 5.8)"
```

And the test that proves the fix generalises rather than merely unsticking this pair —
**the most important one after the headline**:

```python
@pytest.mark.parametrize("n_components", [3, 4])
def test_reachability_holds_for_a_synthetic_registry_with_n_components(manager, n_components):
    """The real registry has 2 components today. A fix that only crosses ONE boundary is a
    patch, not an invariant. Build a synthetic registry with N disjoint capability islands
    (ndim = 4, 5, ... are pairwise incompatible under `compatible`) and assert full
    coverage still holds.

    REQUIRES an enabling change: `gated_dataset_options` reads the module-global
    DATASET_TYPES/MODELS and is NOT injectable, unlike compatible_models /
    compatible_datasets / model_options / model_is_trainable. Either add
    `*, dataset_types=DATASET_TYPES, models=MODELS` to it (preferred -- it makes the
    registry module uniformly injectable), or monkeypatch model_registry.DATASET_TYPES and
    model_registry.MODELS here. The former is a two-line change and removes the last
    non-injectable resolver.
    """
```

**Wiring**: `src/tests/regression/` is collected by canopy's existing suite, so no CI edit
is needed on the canopy side. Confirm against canopy's `AGENTS.md` test invocation before
merging — juniper-ml's CI test list is hand-maintained, and while this file lives in canopy,
that habit is worth checking rather than assuming.

**Why this test and not a browser test.** The defect is a property of the *transition
relation*, and the transition relation is fully determined by two pure functions
(`gated_dataset_options`, `_build_model_selection_table`) plus one handler. A Playwright
walk would find the same defect far more slowly, non-exhaustively, and would not scale to
the synthetic-registry case at all. A property test over the registry is the right
instrument, and it is fast enough to be quantified over every state.

---

## 4. Other defects found (flagged separately — NOT folded into any proposal)

**F-1 — `restart-ds-type` is frozen to `DEFAULT_MODEL_KEY` (`dashboard_manager.py:5422`).**
`options=gated_dataset_options(DEFAULT_MODEL_KEY)` is evaluated once at layout-build time
and never re-gated. Two consequences, and the second is the dangerous one:
(i) the availability gate (`apply_availability_gate`) is **never applied here at all**,
unlike the sidebar — an unavailable generator is offered as selectable in the restart modal;
(ii) it is permanently gated against **cascor**, so the instant the main trap is fixed and
`(equities_seq, recurrence)` becomes reachable, this dropdown greys the *only* valid dataset
and enables *five invalid ones*, and `execute_restart` (`:5381-5385`) forwards the chosen
`dataset_type` into the restart orchestration. That is a live `REACHABLE-BUT-INCOMPATIBLE`
path **created by the fix**.
*This is the "a broken thing masks the next one" pattern exactly: F-1 is invisible today
only because the state that exposes it is unreachable.* Fix: drive `restart-ds-type.options`
from a callback on `model-selection-store` reusing `_gate_dataset_options_handler`, and pin
it with `test_restart_ds_type_options_track_the_selected_model`. **This must land in the
same PR as any of P2-1..P2-4.**

**F-2 — the D5 auto-snap is unreachable on the compatibility axis, and
`test_model_picker.py:91` is a vacuous pass.** As shown in §1.2, σ is a no-op on every
enabled `T_model` edge. Its only live trigger is the *availability* axis: the generator list
is TTL-cached for 30 s (`_GENERATORS_CACHE_TTL_S`, `:2708`), so a dataset that was available
at selection time can become unavailable, and a subsequent model re-select then snaps.
So the D5 conflict machinery exists, is tested, is correct, and fires only for a reason it
was not designed for. Two actions: (i) record in the design that OQ-6 is currently
*unobservable*, not merely undecided; (ii) treat
`test_gate_dataset_options_handler_greys_and_snaps_for_recurrence` as a known vacuous pass
until a fix makes its transition performable — and add a comment saying so, so it is not
mistaken for coverage of the model swap.

**F-3 — FR15 is unimplemented on the model axis, producing a live split-brain.**
`model-class-store` **is** hydrated from `GET /api/train/status` (`hydrate_model_class`,
`:2519-2531`, via `_resolve_model_class` at `:2275`). `model-selection-store` **is not** —
it is seeded `DEFAULT_MODEL_KEY` at `:1842` and written only by `select_model`. So if the
process-global backend is already recurrence (a direct `POST /api/model/select` from another
client, or a reload after a swap), canopy renders `Active: CasCor` in the sidebar while
`model-class-store == "one_shot"` suppresses the cascade tabs. Concretely reachable
consequence: `_resolve_oneshot_start_body_handler` (`:2664-2673`) keys on
`model_class == "one_shot"` and the *cascor-gated* dropdown value, and will build
`{"dataset": {"generator": "spirals"}}` for the recurrence service. FR9 means the service
fails closed — but as an opaque failed run, not a UI message. Fix: hydrate
`model-selection-store` from the same status call, re-validate the pair against the
registry, and fall back to the first compatible pair with a notice — which is FR15 verbatim.
(This is M5 from §2.5; it belongs here, as a defect, not there, as a fix.)

**F-4 — D4 / §5.5 / FR6 (clear-reset) never shipped on either axis, and the dead code that
proves it is tested.** The dataset dropdown is `clearable=False` at `:1334` (and again at
`:5422`); the model axis lost its dropdown to A1b-1 and gained no clear affordance. Yet
`_build_model_selection_table(None, …)` fully handles a cleared dataset (`:3036`) and
`test_model_table.py::test_table_without_a_dataset_treats_all_models_as_compatible` asserts
it. Live, correct, tested, unreachable code. Either ship the ✕ (P2-2) or delete the branch
and its test — leaving it is how a future reader concludes clearing works.

**F-5 — `gated_dataset_options` is the only non-injectable resolver in `model_registry.py`.**
`compatible_models` (`:321`), `compatible_datasets` (`:329`), `model_options` (`:222`),
`model_is_trainable` (`:232`) and `dataset_model_hint` (`:382`) all take injectable
`models=` / `dataset_types=`; `gated_dataset_options` (`:408`) reads module globals. This
blocks the synthetic-registry property test in §3 without monkeypatching. Two-line fix,
and it makes the module uniformly injectable.

**F-6 — §5.8's recovery advice is not verified against the gate that would have to admit
it.** `_build_model_selection_table`'s empty-compatible-set alert (`:3062-3072`) says
*"switch the dataset in the sidebar"* — but the sidebar dropdown is joint-gated against the
**current model**, so if that model has no compatible dataset every option is greyed and the
advice is unactionable. Same defect class as the headline one, one level down: **a recovery
path was written without checking that the recovery action is reachable.** Any recovery copy
that names a control should be accompanied by an assertion that the named control offers at
least one enabled option in that state.

**F-7 — the `disabled` decision is derived from the *reason* functions, not from
`compatible()`.** `:3050` uses `model_reason(model, dataset) is None`; `gated_dataset_options`
(`:419`) uses `dataset_reason(dataset, spec) is None`. Both are independent
re-derivations of the same predicate through presentation-layer code. They agree today
(`test_model_registry.py::test_model_reason_inverse_consistent_with_dataset_reason_over_seeds`
pins it), but a future axis added to `compatible()` and forgotten in one reason function
would silently change the *transition relation* while every compatibility test still passed.
The `disabled` decision should call `compatible()` directly; the reason functions should
supply text only. Low severity today, but it is a load-bearing predicate reached through a
string-formatting helper, and my lens says that is the wrong dependency direction.

---

## 5. Ranking, and what I would ship

| Rank | Proposal | Invariant gained | Cost | Ship? |
|---|---|---|---|---|
| **1** | **P2-1** unary model guard + peer repair | `I-cover` at **zero cost to `I-safe`**; `I-unary` | smallest | **Ship now** |
| 2 | **P2-4** atomic pair commit | `I-atomic` — strongest and cheapest to check | medium-high | **Ship next**, once the model population passes ~10 |
| 3 | **P2-2** `⊥` / clear | `I-cover` unconditionally; best degenerate behaviour | medium, wide | Ship **alongside** P2-1 as FR6/D4 debt |
| 4 | **P2-3** explicit conflict state | most faithful to D5; generalises to warning tiers | highest | Defer until compatibility acquires a non-binary tier |

**What I would ship: P2-1, with a mandatory confirm-on-pair-change, plus the §3 property
test landed *first* (red), plus F-1 in the same PR.**

Reasons, in order of weight:

1. **The property test is the durable artifact and it is proposal-independent.** Landing it
   first, red, converts an anecdote into a measured invariant and makes every later
   proposal's success falsifiable. If only one thing ships from this document, it is §3.
2. **P2-1 is the only proposal that gains coverage without spending safety.** σ repairs the
   peer inside the transition; no incompatible state is ever published; every downstream
   consumer keeps its exact current precondition. That is worth a great deal in a codebase
   with six independent readers of `nn-dataset-type-dropdown.value`.
3. **The repair already exists and is already tested.** σ is implemented at `:2687` and unit-
   tested at `test_model_picker.py:91`. P2-1 is, almost exactly, *deleting the guard that
   made an already-shipped repair unreachable*. The smallest correct diff is usually the
   right first move, and here it is unusually small.
4. **It resolves OQ-6 in the direction the design already leaned** (§5.6: model-primary
   "fits the model-centric benchmarking trajectory"; D6/D7/§6: model browsing is the load-
   bearing problem). Closing a ratified-but-open decision is worth more than deferring it
   again.
5. **The unary-guard rule generalises past this instance.** `I-unary` is a property of one
   function of one argument. It is checkable without simulation, it states *why* the fix is
   right rather than *that* it works, and it is the sentence to paste into the design doc so
   the next person building a gated selector does not rebuild the trap.

Sequencing: (§3 test, red) → (P2-1 + notice + F-1, test green) → (P2-2 for FR6/D4) →
(F-3 FR15 hydration, separately) → (P2-4 when the model table grows).

### The strongest objection to my own top pick

**P2-1 makes the dataset coordinate silently mutable by a model click, and the value it
mutates to is `enabled_datasets(m')[0]` — registry order.** Three consequences, and the
third is the one that would change my mind:

1. **FR4 violation.** *"When >1 option remains compatible, the user chooses within the set
   (no silent auto-pick)."* When a model has several compatible datasets, σ auto-picks. The
   notice reports it; it does not make it a choice. P2-1 does not satisfy FR4, it apologises
   for not satisfying it.
2. **Silent loss of staged work.** The sidebar carries schema-driven generator params
   (`:2793-2800`) and an "Apply Dataset" staging flow. A user who clicks a model row *to
   read its description* loses that configuration with no undo.
3. **The repaired value is unaudited and order-dependent.** It changes when someone reorders
   `DATASET_TYPES` — a change nobody would think of as behavioural. In a product whose stated
   purpose (§6, FR13) is *benchmarking*, a silently order-dependent dataset choice is a
   reproducibility hazard, not just a UX wrinkle. At 6 datasets this is invisible. At 30 it
   is a defect.

This objection is strong enough that I would not ship bare P2-1. **My shipped form borrows
P2-4's confirm step**: when `σ(m', d) ≠ d`, the Select click opens a small confirm —
*"Switching to Recurrence (LMU) also changes the dataset to Equities (sequence). [Switch]
[Cancel]"* — which converts the silent auto-pick into an explicit, auditable, cancellable
pair transition and closes objections 1 and 2 outright. It leaves objection 3 standing
(the *offered* value is still `[0]`), which is precisely the residue P2-4 exists to remove
by letting the user choose from the menu.

So the honest statement of my ranking is: **P2-1 and P2-4 are the two ends of one axis —
whether the user *confirms* the peer or *chooses* it — and I take confirm as the correct
first increment, with choose as the planned second.** They remain distinct proposals because
they establish different invariants (`I-safe` preserved by repair, versus `I-atomic`
established by construction) and because P2-4 carries an architectural cost — a second
writer on `nn-dataset-type-dropdown.value`, against a discipline this codebase has been
actively enforcing — that is not worth paying until the model table is large enough to
justify it.

One further caution against my own pick, recorded because it is the thing most likely to go
wrong: **P2-1 is one line from being unsafe.** A reviewer who reads "remove the disabled
guard at `:3050`" and does exactly that — without `I-unary` — introduces the product's first
`REACHABLE-BUT-INCOMPATIBLE` state the moment a model with no compatible dataset lands
(risk R1). The invariant, not the edit, is the deliverable. `test_no_incompatible_pair_is_reachable`
and `test_model_table_disabled_predicate_is_unary` are what make the difference between
P2-1-as-designed and P2-1-as-misread, and neither exists today.
