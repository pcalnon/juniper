# P4 — Architecture & Scale lens: the canopy model×dataset deadlock

**Author**: proposal author P4 (architecture and scale)
**Date**: 2026-09-02
**Subject repo**: juniper-canopy (read-only inspection)
**Design of record**: `notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` (in juniper-ml)
**Companion of record**: `notes/JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md` (in juniper-ml — **note: it has its own independent D1–D6 / OQ-1–6 numbering; every citation below names its document**)

---

## 1. Verification of the hypothesis

**Verdict: CONFIRMED — and stronger than stated.** The pair is not merely hard to reach; it is
*provably unreachable*, and the unreachability is structural rather than incidental.

### 1.1 The anchors, checked

Every anchor in the brief is correct. Corrections and additions are marked.

| Anchor | Status | Evidence |
|---|---|---|
| `src/model_registry.py` — local hardcoded registry, 6 datasets / 2 models | **CORRECT** | `DatasetTypeSpec` `model_registry.py:84-98`; `ModelSpec` `:101-125`; `DATASET_TYPES` `:132-150` (6 entries); `MODELS` `:167-193` (2 entries); `compatible()` `:311-318`; `gated_dataset_options()` `:408-424`; `model_reason()` `:354-372` |
| `dashboard_manager.py:1334` `clearable=False` | **CORRECT** | sidebar `nn-dataset-type-dropdown`, `options=gated_dataset_options(DEFAULT_MODEL_KEY)` at `:1332`, `clearable=False` at `:1334` |
| `:1842` model-selection store | **CORRECT** | `dcc.Store(id="model-selection-store", …, data=DEFAULT_MODEL_KEY)` at `:1842` — seeded, **never hydrated from the backend** (see §5, Defect 3) |
| `:2687` `_gate_dataset_options_handler` with auto-snap | **CORRECT** | `:2687-2711`; snap at `:2709-2711` (`return options, enabled[0]`) |
| `:3050` `disabled=not is_compatible`, no auto-snap | **CORRECT** | `_build_model_selection_table`, Select button `:3042-3051`; `is_compatible` computed `:3033-3034` |
| `:5422` `restart-ds-type` statically gated | **CORRECT — and worse than "static"** | `:5422`; its `options` prop is **never** an `Output` of any callback (only `value` is, at `:5268`). See §5, Defect 1 |
| `_fetch_generators` / `apply_availability_gate` — service-sourced capability feed precedent | **CORRECT, and it is the right precedent** | `_fetch_generators` `:2713-2740` (30 s TTL cache at `:2711`); composition `:2702`; pure helpers in `dataset_schema.py:230-286`; canopy's own proxy route `main.py:1681-1720` |
| `src/dataset_schema.py` — schema-driven param plumbing | **CORRECT** | `parse_schema_fields` `:206-227`; `availability_map` `:230-245`; `apply_availability_gate` `:268-286` |

### 1.2 Formal proof of unreachability

I re-implemented the two gates' *actual transition rules* against the real registry and
enumerated the reachable state space by BFS from the seeded default `(spirals, cascor)`:

- **dataset move**: any option in `gated_dataset_options(model)` that is not `disabled`
  (`clearable=False` at `:1334` means there is no null state to pass through).
- **model move**: any model whose `model_reason(model, dataset)` is `None` (`:3050` disables the
  Select button otherwise), followed by the dataset-side snap at `:2709-2711`.

Result:

```
START                : ('spirals', 'cascor')
REACHABLE      (5)   : circles/cascor, mnist/cascor, moons/cascor, spirals/cascor, xor/cascor
VALID pairs    (6)   : the above + ('equities_seq', 'recurrence')
VALID but UNREACHABLE: [('equities_seq', 'recurrence')]
```

**The one pair the whole recurrence integration exists to enable is the one pair the UI cannot
reach.** 100% of the recurrence feature surface is dead from the default state.

### 1.3 Why this is structural, not a slip

The transition rule is: *you may move one coordinate only if the new value is compatible with the
other coordinate's current value.* That rule confines the user to **the connected component of the
compatibility bipartite graph containing the initial pair.** Today that graph has exactly two
components — `{cascor} × {spirals, xor, mnist, circles, moons}` and `{recurrence} × {equities_seq}` —
because no model declares `input_ndim ⊇ {2,3}` (`model_registry.py:172,183`).

The design of record anticipated this and closed it, in `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`:

- **D4** — "Clear/reset = conventional inline ✕ on each control (clearing one auto-widens the other
  via the gate)"; **FR6** — "Clear/reset each selection … → restores the full active set on the
  other side"; **§5.5** — the ✕ on the dataset dropdown *and* "a 'clear model / show all' reset on
  the surface."
- **§5.6 (D5)** reasons: *"A newly selected option is never incompatible (greyed). A conflict can
  only arise by **changing** an already-set value so the other side is stranded."*

That §5.6 sentence is only true **if a clear exists.** The clear introduces a universal hub node
(the null selection) that every state connects to, which makes the graph a star and reachability
total *regardless of how the compatibility relation fragments*. **D4's ✕ is not a UX nicety — it is
the connectivity guarantee**, and it was silently dropped on both surfaces:

- dataset side: `clearable=False` (`dashboard_manager.py:1334`, and again `:5422`);
- model side: the modal footer contains only a Close button (`:2219-2221`); there is no
  "clear model / show all" control anywhere in `_build_model_selection_table` (`:3005-3090`) or the
  modal body (`:2197-2227`).

With D4 dropped, the connectivity guarantee vanished and nothing replaced it. **The deadlock is the
exact, predicted consequence of shipping D5's conflict reasoning without D4's escape hatch.**

### 1.4 The defect gets strictly worse with scale — this is the load-bearing point

The number of stranded pairs is not bounded by 1. It is bounded by the number of connected
components of the compatibility graph, which grows with the number of *distinct capability
signatures*, not with the number of models. Per
`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` §6, the near-term population is
1 feedforward + 3–5 established-TS + 10–20+ growth families, "each spawning several-to-many benchmark
variants", "most sharing the 3-D input contract". Under that trajectory:

- adding 100 more 3-D models adds **zero** reachability — they all land in the already-unreachable
  component;
- adding one 3-D *classification* dataset, or one regression-only 3-D model, **splits** the 3-D
  component further (`task_type` is a partition axis: `compatible()` `model_registry.py:318`);
- adding a Δt-*unaware* 3-D model against `equities_seq` (`temporal="irregular"`,
  `model_registry.py:143`) splits it again (`temporal_ok` `:299-308`).

So the status quo does not merely have one stranded pair today; it has an **architecture that
manufactures stranded pairs at exactly the rate the platform grows.** Any proposal that fixes only
`(equities_seq, recurrence)` is fixing an instance of a generator.

---

## 2. What capability metadata actually EXISTS today, service by service

Surveyed across juniper-data, juniper-recurrence, juniper-recurrence-model, juniper-cascor,
juniper-model-core and juniper-service-core. Every row below is **found in source**; nothing is
assumed. `NOT FOUND` means an explicit grep across the repo returned nothing.

### 2.1 juniper-data — the dataset producer

| Fact canopy hardcodes | Emitted on `GET /v1/generators` today? | Known in juniper-data's code? |
|---|---|---|
| generator exists, name, version, description | **YES** | `GeneratorInfo` — `juniper_data/core/models.py:109-128`, built at `juniper_data/api/routes/generators.py:234-254` |
| `available: bool` | **YES** | same; from each generator's `is_available()` hook (3 of 16 declare one) |
| `install_hint: str \| None` | **YES** | `core/models.py:118-128` — **canopy does not consume it** (see Defect 7) |
| params JSON-Schema | **YES** (wire key `schema`, via `Field(alias="schema")`) | canopy already consumes it — `dataset_schema.parse_schema_fields` |
| **`task_type`** | **NO — absent from the payload** | **YES**, declared per generator in `GENERATOR_REGISTRY` (`api/routes/generators.py:58, 65, …, 172`), used only for `POST /v1/datasets` metadata dispatch. Never copied into `GeneratorInfo`. |
| **temporal / Δt regularity** | **NO** | **PARTIALLY** — `"time_unit"` key exists on the 6 sequence generators (`"calendar_days"` for `equities_seq` at `:118`; `"steps"` for the five synthetics at `:126, 134, 142, 150, 158`); regularity itself is only in free prose in `description`. No boolean or enum. |
| **input rank / ndim** | **NO** | **ONLY POST-GENERATION** — `derive_sequence_meta()` (`core/meta.py:102-124`) reads `X_train.ndim == 3` and stamps `DatasetMeta.sequence` / `lookback`; that runs inside `POST /v1/datasets`, i.e. *after* generating the artifact. Pre-generation, rank is inferable only by the unstated convention "the params class has a `lookback` field". |
| output shape (`n_features`, `n_classes`, `lookback`) | **NO** on the generator list; **YES** on `DatasetMeta` post-generation (`core/models.py:19-83`, returned by `POST /v1/datasets` and `GET /v1/datasets/{id}`) | yes, post-generation |
| a generator category / family taxonomy | **NOT FOUND** — no Enum, no Literal, no field | family exists only as Python class inheritance (`SyntheticSequenceParams`, `EquitiesSeqParams(EquitiesParams)`) |
| user-uploaded datasets | **NOT FOUND** — zero hits for `upload`; no dynamic generator registration (`GENERATOR_REGISTRY` is a static module-level dict) | the nearest analogue is the `csv_import` generator reading a server-side path under `Settings.import_dir` |

**The number that matters most in this whole document:** juniper-data registers **16** generators.
canopy's `DATASET_TYPES` (`model_registry.py:132-150`) exposes **6**. juniper-data serves **six 3-D
sequence generators** — `equities_seq`, `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`,
`delay_product` — and **canopy exposes exactly one of them.** The recurrence/LMU model could train on
all six today. **Five ready-to-use 3-D datasets are invisible to the dashboard**, not because of a
gate, but because a hand-written tuple in canopy has never been updated. That is the drift cost of
the current ownership model, already incurred, measurable, and it is 5× larger than the deadlock this
brief is about.

### 2.2 juniper-recurrence / juniper-recurrence-model — the model service

- **`GET /v1/capabilities` — NOT FOUND.** Nor `/v1/models`, `/v1/info`, `/v1/schema`. A repo-wide
  search for those route strings across *every* Juniper repo returned zero.
- Route surface: `/v1/health`, `/v1/health/ready` (both from `juniper-service-core`, bodies literally
  `{"status": "ok"}` — no model identity), `POST /v1/train`, `GET /v1/training/status`,
  `POST /v1/predict`, `GET /v1/model`, `GET /v1/dataset`, `POST /v1/crossval`,
  `GET /v1/crossval/status`.
- **The request schemas are shape-blind.** `TrainRequest.dataset` is a `DatasetRef` carrying no rank
  or Δt field; `PredictRequest.X` and `.dt` are bare `list`. Nothing in the OpenAPI document pins
  rank-3 or Δt-awareness.
- **It DOES fail closed at runtime, exactly as FR9 requires** —
  `juniper-recurrence-model/juniper_recurrence_model/model.py:161-162`:
  `if X.ndim != 3: raise ValueError(f"X must be 3-D (n, T, F); got shape {X.shape}")`, mapped to
  **HTTP 422** by the router and pinned by a passing test (`tests/test_routes.py:118-122`).
- Model identity (`model_type: "lmu"`, `task_type: "regression"`) exists **only post-fit**, via
  `describe_topology()["meta"]` and `GET /v1/model` — which 409s until a model has been trained.
- Build identity exists as a Prometheus `Info` metric only (`/metrics`), and carries version/git-sha,
  **not** model contract.

**Verdict: the requirement is enforced, and advertised nowhere. There is no pre-hoc, machine-readable
declaration of the LMU's input contract anywhere in the ecosystem.**

### 2.3 juniper-cascor — the other model service

- **`GET /v1/capabilities` — NOT FOUND.** The many `capabilities` hits in cascor are a **false
  friend**: they are *distributed-compute-worker* capabilities (`api/workers/registry.py`,
  `api/workers/protocol.py`) — what hardware a worker node offers, unrelated to model contracts.
- **It also fails closed on rank, with an unusually good error** —
  `juniper-cascor/src/api/lifecycle/manager.py:3607-3608`: train arrays "must be 2-D … 3-D sequence
  artifacts belong to the juniper-recurrence tier, not cascade-correlation (W-2 tier boundary)".
  So **both** model services enforce the tier boundary at runtime; **neither** publishes it.
- `GET /v1/network` returns model info but **404s until a model exists** — post-hoc, same as
  recurrence.
- `/v1/health` carries `version`/`service`/`git_sha`/`build_date` — deploy identity, no model
  contract.
- And separately: `src/api/models/training.py:235` pins the **dataset vocabulary** as a Literal — see
  §3.1 row 5 and Defect 4.

### 2.4 juniper-model-core — the shared conformance kit

- **What it is:** ABCs + a pytest conformance mixin suite + shared validation functions + a `Topology`
  TypedDict + a `ModelSerializer` ABC + a generic walk-forward cross-validation executor. Zero HTTP
  code, zero third-party runtime deps at import.
- **A capability/shape descriptor type — NOT FOUND.** No `CapabilitySpec`, no `InputSpec`, no
  contract TypedDict. The two nearest things:
  - `TrainableModel.input_shape` / `.output_shape` — abstract properties
    (`juniper_model_core/interfaces.py:140-148`). **Populated only after `fit()`.**
  - `TaskType = Literal["classification", "regression"]` (`interfaces.py:50`) — a type alias. This is
    the one genuinely shared vocabulary item that exists today, and canopy does not import it.
- **A model registry — NOT FOUND** (zero hits for `registry` in the package). Deliberate: its D10
  keeps `Topology.model_type` an open `str` so "the cost of model #20 must equal the cost of model
  #2".
- **Real consumers today:** juniper-cascor (`src/api/models/cascor_model.py`), juniper-recurrence-model
  (`model.py:37`), juniper-recurrence's service, and juniper-service-core's lifecycle layer. Exactly
  **two real model implementers** — cascor's `CascadeCorrelationNetwork` and `LMURegressor`.
  **juniper-canopy is not a consumer.**
- **A found hazard, not a hypothetical one:** `input_shape` is documented as the **per-sample** shape
  *excluding the batch axis* — `(F,)` or `(T, F)` (`interfaces.py:142`). canopy's `ndim` **includes**
  the batch axis (2 = tabular, 3 = sequence, `model_registry.py:91`). juniper-data's
  `derive_sequence_meta` also includes it (`X.ndim == 3`). **So canopy and juniper-data agree on the
  rank convention and juniper-model-core is off by one.** Any unification that crosses that seam
  without pinning the convention silently inverts the gate. (canopy has already been bitten once by a
  rank-vs-feature-count confusion — the N7 note at `model_registry.py:375-379`.)

### 2.5 juniper-service-core — the shared FastAPI tier

- **`build_routers()` EXISTS** (`juniper_service_core/routes/__init__.py:54-60`) and returns
  training / metrics / dataset / **network** / snapshots routers.
- `GET /v1/network` → `ServiceLifecycleManager.get_network_info()`
  (`lifecycle/manager.py:360-374`) returns `{model_type, task_type, input_shape, output_shape}` —
  **this is the closest thing to a capability descriptor anywhere in the ecosystem.** It is still
  strictly post-hoc ("empty dict when no model").
- **It has ZERO live consumers.** I verified independently: `grep -rn "build_routers\|ServiceLifecycleManager("`
  across juniper-recurrence and juniper-cascor/src returns nothing. Both services hand-rolled their
  own parallel lifecycle + network routes. The shared pattern is designed, tested in isolation, and
  wired into nothing.

### 2.6 Summary — EXISTS vs WOULD-NEED-BUILDING

**EXISTS (can be used today, no new service work):**

1. `GET /v1/generators` with `name` / `version` / `description` / `available` / **`install_hint`** /
   params `schema` — canopy already fetches it and already uses three of the six fields.
2. Post-generation `DatasetMeta` with `task_type`, `sequence`, `lookback`, `time_unit`, `n_features`,
   `n_classes`, `dt_scaling` — the full dataset contract, available after `POST /v1/datasets`.
3. Runtime fail-closed rank enforcement in **both** model services (recurrence rank-3 → 422; cascor
   rank-2 → RuntimeError naming the recurrence tier). **FR9 of
   `…MODEL-DATASET-SELECTION-DESIGN.md` §5.9 is genuinely satisfied today** — which is what licenses a
   fail-open UI.
4. `juniper_model_core.TaskType` — a shared task vocabulary, unused by canopy.
5. `juniper-service-core.build_routers()` + `get_network_info()` — a ready-made capability-ish router,
   adopted by nobody.
6. `juniper-data`'s in-code `task_type` and `time_unit` per generator — the facts exist, they are
   simply not copied into the response model.

**WOULD NEED BUILDING:**

1. **Any** pre-training, machine-readable capability endpoint on **any** model service. Nothing of the
   kind exists.
2. A declarative input-contract descriptor in juniper-model-core (today: prose docstrings plus a
   runtime `ValueError`).
3. Rank / Δt / task on the **generator listing** (three additive fields on an existing response
   model — genuinely small; the values already exist in `GENERATOR_REGISTRY`, except rank).
4. A pre-generation "describe shapes" call (rank is currently only derivable *after* generating).
5. Any model or generator registry that is not a hand-edited Python literal.
6. Adoption of `build_routers()` by an actual service.

**The one-sentence answer to "is canopy guessing at something another service already answers?"** —
For `available` and the params schema, no: canopy already consumes the service's answer. For
`install_hint`, yes, and the answer is already on the wire (Defect 7). For **rank**, **task** and
**temporal**, the services *know* but do not *say*; for **model requirements**, nobody says
anything anywhere, and canopy's local `MODELS` tuple is currently the only machine-readable
statement of the LMU's input contract in the entire platform.

---

## 3. Architectural assessment

### 3.1 UI defect, capability-model defect, or both?

**Both — and they are cleanly separable, which is good news for phasing.**

**(a) The immediate cause is a UI defect** with a one-sentence description: *the dataset side of the
bidirectional gate has a conflict-resolution policy and the model side does not.* `:2709-2711` snaps
a stranded dataset to the first compatible one; `:3050` merely disables. That asymmetry is the whole
bug. It is repairable inside `dashboard_manager.py` with no registry change, no schema change and no
other service.

**(b) The deeper cause is a capability-model defect**: the facts that decide compatibility are
duplicated across at least **six** hand-maintained locations, no two of which agree, and **not one of
them is owned by the party that actually knows the fact.**

| # | Location | Fact it encodes | Who actually knows it | Divergence found |
|---|---|---|---|---|
| 1 | `juniper-canopy/src/model_registry.py:132-150` `DATASET_TYPES` | dataset rank / task / temporal / label / default params | **juniper-data** (owns the generators) | **6 of juniper-data's 16 generators; 1 of its 6 rank-3 generators.** And `equities_seq`'s `task_type` directly contradicts juniper-data's (§5, Defect 6) |
| 2 | `juniper-canopy/src/model_registry.py:167-193` `MODELS` | model input rank / task / Δt / status / provider | **juniper-recurrence, juniper-cascor** (own the models) | 2 of a planned 100+ |
| 3 | `juniper-canopy/src/dataset_schema.py:97-100` `GENERATOR_NAME_ALIASES` + `:106-109` `_UNAVAILABLE_REASONS` | canopy-value → juniper-data-name mapping; per-generator install hints | **juniper-data** | only `spirals→spiral`, `moons→moon`; hints hardcoded for `mnist`, `arc_agi` |
| 4 | `juniper-canopy/src/main.py:1710-1718` fallback generator list | generator existence | **juniper-data** | 4 entries (`spiral`, `xor`, `circles`, `moon`) — missing `mnist`, `equities*`, everything else |
| 5 | `juniper-cascor/src/api/models/training.py:235` `StageDatasetRequest.dataset_type` Literal | the accepted dataset vocabulary at the staging boundary | **juniper-data** | **8 values — `spirals, xor, mnist, circles, moons, equities, gaussian, checkerboard`. It has `gaussian`/`checkerboard` (canopy does not) and it does NOT have `equities_seq` (canopy's only 3-D dataset).** |
| 6 | `juniper-canopy/src/demo_mode.py:1854`, `:1961`, `:2009` | rank + Δt, **derived empirically from the artifact** (`x_probe.ndim == 3` → `dataset_kind: "sequence"`, `dt_*` → Δt histogram) | the artifact itself | agrees with nothing — it is computed, never fed back into `compatible()` |

Row 5 is the sharpest evidence: **canopy's only 3-D dataset value is not in cascor's accepted
vocabulary.** Row 6 is the most interesting: **canopy already computes the exact facts its registry
hardcodes**, by a different mechanism, and throws the result away as far as compatibility is
concerned.

A seventh location is canopy's own backend abstraction: `BackendProtocol`
(`src/backend/protocol.py:220-330`) declares 20 members and **`stage_dataset` is not one of them**,
yet `main.py:3995` calls `backend.stage_dataset(**params)`. `DemoBackend` (`demo_backend.py:347`) and
`ServiceBackend` (`service_backend.py:307`) implement it; **`RecurrenceBackend` does not** (see §5,
Defect 2). Canopy's backends already have divergent capabilities and there is no capability
declaration at the seam that would have caught it.

### 3.2 Where the compatibility facts SHOULD live

The organising principle, and it is not "put it all in one place":

> **Properties belong to the producer. Requirements belong to the consumer. The predicate belongs to
> the presenter. The vocabulary belongs to a shared package. The instances never do.**

| Fact | Rightful owner | Why |
|---|---|---|
| Dataset **properties** — rank, `task_type`, temporal character, label | **juniper-data** | It is the only party that is *necessarily* correct when a generator is added, removed, or changes shape. It already ships per-generator metadata over the same wire (`GET /v1/generators`, consumed at `dashboard_manager.py:2713-2740`). |
| Model **requirements** — accepted ranks, task types, Δt need, family/variant/version/status | **the serving service** (juniper-recurrence for LMU, juniper-cascor for cascor) | It is the party that will actually *fail closed* under FR9 of `…MODEL-DATASET-SELECTION-DESIGN.md` §5.9. Any other owner is by construction a copy that can be wrong. |
| The **predicate**, faceting, search, reason phrasing, lifecycle presentation | **juniper-canopy** | It is presentation. It must keep working with every service down; `…MODEL-DATASET-SELECTION-DESIGN.md` §5.8 already requires "the sidebar summary shows the last-known model … training is not blocked by a picker load error". |
| The **descriptor types + the predicate function + the vocabulary** (`ndim`, `task_type` values, temporal enum) | **juniper-model-core** (published sub-package, `juniper-ml/juniper-model-core/`) | One definition of the words, importable by canopy, cascor and recurrence, so a schema change is a compile-time event in three repos instead of a silent runtime divergence. |
| The **instances** (which models exist, which generators exist) | **nobody shared** | *This is the trap.* Moving `MODELS` / `DATASET_TYPES` into a shared package does **not** fix drift — it relocates the hand-maintained copy one layer up and adds a release cycle between the truth and the copy. |

That last row is the finding I most want on record: **the tempting unification is the wrong one.**
The design of record says, in `…MODEL-DATASET-SELECTION-DESIGN.md` §5.9, "a shared capability source
across services is a possible later unification (noted, not required)". I would sharpen it: a shared
capability **schema** is right; a shared capability **registry** is wrong.

### 3.3 Is canopy guessing at something another service already answers?

Partly — and the part it is guessing at is the part with the *worst* consequences.

- For **dataset params**, canopy already stopped guessing: N7 replaced the spiral-centric typed
  inputs with schema-driven fields read from juniper-data's own JSON-Schema
  (`dataset_schema.parse_schema_fields`, wired at `dashboard_manager.py:2760-2800`). That migration
  is the working template for the capability facts.
- For **generator availability**, canopy already stopped guessing: `available: bool` comes from the
  service (`dataset_schema.availability_map:230-245`).
- For **install hints**, canopy is still guessing at a string the service already sends
  (`install_hint` on `GeneratorInfo`), behind a TODO that has gone stale (§5, Defect 7).
- For **dataset rank / task / temporal**, canopy is guessing at facts juniper-data *knows in code but
  does not emit* (`task_type` and `time_unit` are in `GENERATOR_REGISTRY`; rank is derived only
  post-generation).
- For **model requirements**, nobody in the platform is answering at all: no model service publishes
  a pre-training input contract (§2.2, §2.3). **canopy's `MODELS` tuple is currently the only
  machine-readable statement of the LMU's input contract anywhere.** It is not a duplicate of a
  service's answer; it is a *substitute* for an answer nobody gives.

So the architectural verdict is not "canopy invented a registry it should not have". It is two
things: **canopy half-finished a migration it already started** on the dataset side (availability and
params schema moved to the service; rank, task, temporal and install hints did not), and on the model
side **canopy is holding a contract that does not belong to it because no other party has claimed
it.** Those two halves have different fixes and different costs, which is why P4-B and P4-C are
separate proposals.

---

## 4. Proposals

Four proposals, distinct in *where the knowledge lives*. P4-A ships without touching another service.
P4-B and P4-C are cross-service and labelled with their dependency. P4-D is a complement, not a
replacement.

---

### P4-A — Symmetric conflict policy: give the model side the snap the dataset side already has

**One-line mechanism.** Make the model surface obey the same D5 conflict policy the dataset dropdown
already implements — selecting an incompatible model adopts that model *and* moves the dataset to its
first compatible one, with an explicit, named consequence — which reconnects the state graph without
adding a null state.

#### How it works

1. **`_build_model_selection_table` (`dashboard_manager.py:3005-3090`)** — the Select button at
   `:3042-3051` keeps `disabled=not is_compatible` for its *primary* action (preserving FR5 of
   `…MODEL-DATASET-SELECTION-DESIGN.md`), and gains a **secondary action on incompatible rows only**:
   `Select — switches dataset to <label>`, where `<label>` is
   `compatible_datasets(model)[0].label` (`model_registry.py:329-334`, already exists and is already
   tested). Rows with an empty compatible set keep a genuinely disabled button and the §5.8 recovery
   alert (already built at `:3078-3088`).
2. **`_select_model_from_table_handler` (`:2914-2931`)** — pattern-match id gains a second `type`
   (`model-select-with-dataset-btn`); the handler resolves the target dataset from
   `compatible_datasets`, POSTs `/api/model/select` exactly as today (`:2876-2897`), and writes the
   dataset value as an additional Output into `nn-dataset-type-dropdown.value`.
3. **`_gate_dataset_options_handler` (`:2687-2711`)** — unchanged. Its existing snap
   (`return options, enabled[0]`) is a safety net and would produce the same result; making the
   choice *explicit and named in the button label* is what turns a silent mutation into an informed
   one.
4. **Post-swap notice** — reuse the `train-gate-notice` pattern (`:2955-2985`) for a dismissable
   `dbc.Alert`: "Switched to Equities (sequence) — Recurrence (LMU) needs rank-3 (sequence) data."
   `…MODEL-DATASET-SELECTION-DESIGN.md` §5.6 requires the notice; today there is none on either side.

**Where compatibility knowledge lives afterwards.** Exactly where it lives now: canopy's local
`model_registry.py`. **This proposal deliberately changes nothing about ownership.** Owner on a new
model or dataset: still a canopy PR — unchanged, and still wrong at scale. That is the honest cost,
and it is why P4-A is a *fix*, not an *architecture*.

**Behaviour at scale.** The mechanism is O(1) per selection and independent of N — the snap target is
`compatible_datasets(model)[0]`, one list comprehension over `DATASET_TYPES`. At 100+ variants it
still guarantees reachability of every valid pair (proof: the graph becomes connected because *every*
model is now reachable from *every* state, and each model arrival lands on a compatible dataset).
It does **not** solve browsing at 100+ (that is D6/D7/FR12 and OQ-4, still open — see §6). For
user-imported datasets of unknown rank, `get_dataset_spec()` returns `None`
(`model_registry.py:276-285`) and `_build_model_selection_table` already treats all models as
compatible (`:3033`, pinned by `test_table_unknown_dataset_value_treats_all_models_as_compatible`);
that fail-open path is correct and P4-A leaves it alone. When the capability feed is unavailable:
**not applicable — there is no feed.** The registry is a local constant and cannot degrade. This is
simultaneously P4-A's greatest operational strength and its whole architectural weakness.

**Strengths.**
- Smallest possible diff that provably restores reachability; the snap machinery already exists and
  is already unit-tested (`src/tests/regression/test_model_picker.py:88-96`).
- Removes an *asymmetry* rather than adding a *control* — nothing new to learn, nothing new to
  maintain.
- Resolves **OQ-6** in the direction the design itself endorses: `…MODEL-DATASET-SELECTION-DESIGN.md`
  §5.6 says model-primary "Fits the model-centric benchmarking trajectory".
- Zero cross-repo coordination; shippable this week.

**Weaknesses.**
- Leaves all six duplicated fact-locations of §3.1 intact. Drift continues; this proposal has *no*
  drift story, by design.
- Mutates a user's dataset choice as a side effect of a model click, inside a modal that then closes.
- Requires amending **FR5** for the model surface (visible-but-disabled → visible with an enabled
  secondary consequence action). Declare the amendment; do not smuggle it.

**Risks.**
- **R1 (severe): this fix UNMASKS two live defects that the deadlock is currently hiding.** Reaching
  `(equities_seq, recurrence)` makes "Apply Dataset" call `RecurrenceBackend.stage_dataset`, which
  **does not exist** → `AttributeError` → opaque HTTP 500 (§5, Defect 2). And reaching
  `equities_seq` while still on cascor sends `dataset_type="equities_seq"` into cascor's Literal at
  `juniper-cascor/src/api/models/training.py:235`, which does not contain it → 422 → canopy 502
  (§5, Defect 4). **P4-A must not ship before both are closed**, or the deadlock is traded for a
  500.
- **R2:** the D4 ✕ that this proposal declines to implement remains a ratified, unimplemented
  decision. Either implement it too, or amend D4 explicitly.

**Guardrails (concrete, implementable).**
- **G1 — the reachability invariant test.** Pure, browser-free, in the existing
  `src/tests/unit/test_model_registry.py` lane. BFS the `(dataset, model)` state space from
  `(DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY)` under the *real* transition rules and assert
  `{(d,m) : compatible(d,m)} ⊆ reachable`. O(N·M·(N+M)) — microseconds at 6×2, still milliseconds at
  50×200. **This is the test that would have caught the original defect**, it would have caught it at
  A1b merge time, and it keeps working unchanged as the population grows. It is the single highest-
  value artifact in this document.
- **G2 — an anti-vacuity assertion on the existing snap test.**
  `test_gate_dataset_options_handler_greys_and_snaps_for_recurrence`
  (`src/tests/regression/test_model_picker.py:88-96`) passes today while testing a transition the UI
  cannot perform. Add `assert ("equities_seq", "recurrence") in reachable_pairs()` to it so a
  handler-level snap test cannot be green while its precondition is unreachable.
- **G3 — drift detection, canopy↔cascor vocabulary.** Follow the established precedent of
  `src/tests/contract/test_param_map_completeness.py`: parse
  `juniper-cascor/src/api/models/training.py:235`'s `Literal` and assert
  `{d.value for d in DATASET_TYPES} ⊆ literal ∪ DOCUMENTED_CANOPY_ONLY`. **This test fails today**
  (`equities_seq` ∉ Literal), which is the point.
- **G4 — drift detection, canopy↔serving-service.** P4-A cannot do this properly (no feed). The
  cheap partial: assert every `ModelSpec.provider` that is not `"in-process"` resolves to a
  configured service URL, and log a WARNING at startup naming any `status="live"` model whose
  provider service is unreachable — so a UI that claims a model is live and a fleet where it is not
  disagree loudly instead of silently.

**Design-of-record impact.** Upholds D1, D2 (reasons still at the locus), D5 (conflict policy is a
policy, now applied symmetrically), D7, D8. **Amends FR5** for the model surface. **Amends D4**:
declares the ✕ not-required-for-connectivity given a symmetric snap (or, in the alternative
variant, implements it alongside). **Resolves OQ-6 → model-primary.** Leaves D6/FR12/OQ-3/OQ-4 open.

**Migration path + phasing.** Ships first: fix Defect 2 and Defect 4 (§5) — those are prerequisites,
not follow-ups. Then G1+G2 (they go red, proving the bug). Then the secondary Select action + notice
(they go green). Deferred: everything about ownership. **Fully reversible** — one callback Output and
one button; revert restores today's behaviour exactly.

---

### P4-B — Producer-owned dataset properties: juniper-data emits the rank/task/temporal contract; canopy's registry demotes to a fallback

**CROSS-SERVICE. Dependency: juniper-data must add three fields (or one nested object) to each
`GET /v1/generators` entry. No canopy release is blocked on it — the composition degrades to today's
behaviour when the fields are absent.**

**One-line mechanism.** Extend the generator payload canopy *already fetches* with the dataset's
capability contract, and compose it over the local seeds exactly the way
`apply_availability_gate` already composes the availability flag over the compatibility gate.

#### How it works

1. **juniper-data**: each generator entry in `GET /v1/generators`
   (`juniper_data/api/routes/generators.py:234-254`) gains `contract: {ndim, temporal, targets}` —
   the axes `DatasetTypeSpec` carries (`model_registry.py:88-92`), with **one deliberate shape
   change** forced by what I found (see risk R3): `targets` is a **map**, not a single `task_type`
   string. Two of the three values already exist in `GENERATOR_REGISTRY` and merely need copying into
   `GeneratorInfo` (`core/models.py:109-128`) — `task_type` at `generators.py:58…172`, `time_unit` at
   `:118, 126, 134, 142, 150, 158`. Only `ndim` is genuinely new, and it is a one-word constant per
   generator (the six with a `lookback` param are rank-3). Additive and optional; older services omit
   it and canopy falls back.
2. **canopy `dataset_schema.py`**: new pure helper `contract_map(generators) -> dict[str, DatasetContract]`,
   mirroring `availability_map` (`:230-245`) including its flag-absent posture — except the fallback
   is **the local registry seed, not "anything goes"**.
3. **canopy `model_registry.py`**: `get_dataset_spec()` (`:276-285`) and `gated_dataset_options()`
   (`:408-424`) take an optional resolved-contract override; the seeds stay as the offline default
   and keep owning the *presentation* fields (`label`, `default_params`) that juniper-data has no
   opinion about.
4. **canopy `dashboard_manager.py`**: `_gate_dataset_options_handler` at `:2702` becomes
   `apply_availability_gate(gated_dataset_options(model_key, contracts=contract_map(gens)), gens)`.
   One line. The 30 s TTL cache at `:2711-2740` already exists and already serves both the render and
   the gate callback.
5. **The un-registered generator becomes visible — this is the payoff, and it is already worth 5×
   the deadlock.** Today a generator juniper-data serves but canopy has never heard of is
   *invisible*: `DATASET_TYPES` is the only source of options. juniper-data registers **16**
   generators and canopy shows **6**; of juniper-data's **six** 3-D sequence generators
   (`equities_seq`, `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product`) canopy
   shows **one**. With a contract on the wire canopy can list all sixteen, gate them correctly, and
   the LMU gains five more trainable datasets **with no canopy change at all**. That is FR7/FR14
   actually satisfied on the dataset side.

**Where compatibility knowledge lives afterwards.** Dataset properties: **juniper-data**, owned by
whoever adds the generator, in the same PR that adds it. Presentation and the predicate: canopy. The
canopy seeds survive as a **named fallback**, not as truth. Model requirements: still canopy's
`MODELS` — untouched by this proposal (that is P4-C).

**Behaviour at scale.** Adding a dataset becomes a juniper-data-only change; canopy learns about it
on the next 30 s cache expiry. User-imported datasets are *not* covered by this proposal (they never
pass through juniper-data) — see P4-D. At 100+ models nothing changes; this proposal is entirely
about the dataset axis.

**When the feed is unavailable.** `_fetch_generators` already returns `[]` on any error
(`:2731-2735`) and the availability helpers already read that as all-available. For *compatibility*
the correct degrade is different and better: **fall back to the local seed, not to all-compatible.**
Canopy therefore never loses a gate it previously had, and never invents one it never had. For a
generator with no seed and no contract, degrade **fail-open + labelled**: the option is enabled and
suffixed "compatibility unverified — dataset service unreachable".

Is fail-open right, and does it contradict anything? **It is right, and it contradicts nothing**:
`…MODEL-DATASET-SELECTION-DESIGN.md` §5.9/FR9 already ratifies that the UI gate is best-effort and
"the target model service validates the input shape it receives and **fails closed**"; D5 says
greying "is a best-effort affordance, **not** the correctness guarantee". Fail-*closed* in the UI is
the strictly worse option: a down juniper-data would grey every dataset and reproduce the deadlock
platform-wide. The one refinement I would insist on: **fail-open silently is wrong.** Today the
availability degrade is invisible (`self.logger.debug`, `:2733`). Label the degraded state in the UI,
because an FR9 fail-closed after a blocking one-shot fit costs the user minutes, not milliseconds.

**Strengths.** Smallest possible cross-service change — two of three values already exist in
juniper-data's own registry and merely need copying into the response model; the payload is one canopy
already fetches through a proxy that already exists (`main.py:1681`). Follows a template that already
shipped in this exact code (N7's schema-driven params). Makes the dataset half of FR7/FR14 true.
Kills fact-locations 1, 3 and 4 of §3.1. **Unlocks five ready 3-D datasets for the LMU** — a bigger
functional win than the deadlock fix itself.

**Weaknesses.** Only fixes the dataset axis; the model axis (the harder one) is untouched. Introduces
a live dependency into a gate that was previously a pure constant — a new class of runtime variance
in the UI. Requires the *canopy* fallback to be maintained anyway for the offline path, so the
duplicate does not fully disappear; it becomes a *declared, tested* duplicate.

**Risks.**
- **R3 (found, not hypothetical — and it would BREAK the feature if adopted naively).**
  juniper-data declares `equities_seq` as **`task_type: "classification"`**
  (`juniper_data/api/routes/generators.py:117`). canopy declares the same dataset
  **`task_type="regression"`** (`model_registry.py:141`). canopy's recurrence model declares
  `supported_task_types=frozenset({"regression"})` (`:185`). **If canopy adopted juniper-data's
  `task_type` verbatim, `compatible(equities_seq, recurrence)` would evaluate False, the compatible
  set would become empty, and the feature would die a different death** (the §5.8 degenerate state).
  Neither side is wrong: the generator emits **both** targets — a one-hot next-day-direction `y_*`
  *and* a `y_reg_*` close/return rider — and juniper-data's own registry comment says so
  (`generators.py:49-51`). canopy makes it regression by *parameter*, forwarding
  `regression_target: "return"` (`model_registry.py:148`). **The single-valued `task_type: str` is
  the wrong shape for the fact.** Hence the `targets` map in step 1: a generator declares which
  targets it can emit, and *which one is selected is a function of the params*, not of the generator.
  That makes task-compatibility a predicate over `(generator, params)`, which is a genuine FR3 axis
  refinement and is squarely **OQ-5** of `…MODEL-DATASET-SELECTION-DESIGN.md` ("the precise
  input-requirement axes separating category-i/ii models as they land").
- **R4 (rank convention) — checked, and canopy is safe on this seam.** juniper-data's
  `derive_sequence_meta` (`core/meta.py:102-124`) tests `X_train.ndim == 3`, i.e. **including** the
  batch axis, the same convention as canopy's `ndim` (`model_registry.py:91`). The mismatch is with
  **juniper-model-core**, whose `TrainableModel.input_shape` is documented as per-sample *excluding*
  the batch axis — `(F,)` or `(T, F)` (`interfaces.py:140-148`) — i.e. **off by one**. So P4-B's seam
  is safe and **P4-C's is not**; pin the convention in the field description and assert it in G5.
- **R5.** juniper-data has no pre-generation rank: `ndim` must be added as a static per-generator
  declaration, which reintroduces a hand-maintained fact — but one maintained *next to the generator
  it describes*, by its author, which is the whole point. P4-D's measurement is the check on it.

**Guardrails.**
- **G5 — reconciliation test (the drift detector).** In canopy's `src/tests/contract/` lane, against
  a live juniper-data in the `isolated_stack`/`experiment_stack` CI leg: for every generator present
  in both, assert `service.contract == registry_seed`. A mismatch is a **failing test naming both
  values**, not a log line. This is the concrete answer to "drift between canopy's view and the
  service's actual contract" on the dataset axis.
- **G6 — offline-parity test.** Assert `gated_dataset_options(m, contracts={})` is byte-identical to
  today's output for every model, so the degrade path is pinned and can never quietly change
  behaviour when the service is down.
- **G3** from P4-A still applies and is now *more* valuable: the cascor Literal becomes the third
  party to reconcile.
- **G1** (reachability) still applies, and must now run against *service-sourced* contracts too — a
  live juniper-data that emits a contract splitting the graph is a **CI failure**, which is exactly
  the safety property scale demands.

**Design-of-record impact.** Upholds D1, D2, D5, D6, D7, D8, FR3, FR7. Does **not** resolve OQ-6
(orthogonal). **Amends §7's registry shape**: `DatasetTypeSpec` becomes a fallback-and-presentation
record rather than the source of truth. Executes the dataset half of §5.9's "possible later
unification".

**Migration path + phasing.** Phase 1 (juniper-data): add the field, no consumer. Phase 2 (canopy):
`contract_map` + composition + G6, behind no flag — absence of the field is already the fallback, so
the two phases are independently deployable in either order. Phase 3: G5 wired into the stack CI leg.
Phase 4 (deferred): surface generators canopy has no seed for. **Reversible at every phase**; the
field can be ignored, the composition removed, seeds are still there.

---

### P4-C — Consumer-owned model requirements: `GET /v1/capabilities` on every model service, with the descriptor and predicate in `juniper-model-core`

**CROSS-SERVICE, LARGE. Dependency: juniper-recurrence and juniper-cascor each expose a capability
endpoint; `juniper-model-core` publishes the descriptor type and the predicate; canopy pins it.
This is the end-state architecture and it is TOO BIG to be the fix for this bug.**

**One-line mechanism.** Each service that serves a model publishes its own machine-readable input
contract; `juniper-model-core` owns the *schema and the predicate* (never the instances); canopy's
`MODELS` becomes a TTL-cached, offline-seeded view rather than the truth.

#### How it works

1. **`juniper-model-core`** gains `juniper_model_core.capability`: a frozen `ModelCapability`
   dataclass (the fields of `ModelSpec` `model_registry.py:101-125` minus canopy presentation),
   a `DatasetContract` dataclass (the fields of `DatasetTypeSpec`), the vocabularies, and the
   `compatible()` / `temporal_ok()` predicate lifted verbatim from `model_registry.py:299-334`.
   **Types and functions only — no registry of instances.** It has the right substrate already:
   `TaskType = Literal["classification","regression"]` (`interfaces.py:50`) is exactly the shared
   vocabulary item, `TrainableModel.input_shape`/`.output_shape` (`interfaces.py:140-148`) is the
   shape concept, and the conformance suite (`conformance/suite.py`) is the enforcement mechanism.
   **The declarative half is what is missing**: `input_shape` is populated only after `fit()`, so it
   answers "what did this model turn out to accept" and never "what does this model family require".
   The new type is the pre-hoc twin of the existing post-hoc property — and **the conformance suite
   should assert they agree after a fit**, which is what makes the declaration honest.
   **Pin the rank convention explicitly** (P4-B risk R4): model-core's `input_shape` excludes the
   batch axis while canopy's and juniper-data's `ndim` include it. Either the new descriptor uses
   `input_shape`-style per-sample ranks and canopy converts at the boundary, or it uses `ndim` and
   the two coexist with a named adapter. Choosing silently is how the gate inverts.
2. **juniper-recurrence** exposes `GET /v1/capabilities → {models: [ModelCapability]}` built from the
   same constant its `X.ndim != 3` check reads
   (`juniper-recurrence-model/juniper_recurrence_model/model.py:161-162`), so the advertised contract
   and the enforced contract cannot diverge *within* the service. **There is a ready mounting point
   that nobody uses**: `juniper-service-core.build_routers()`
   (`juniper_service_core/routes/__init__.py:54-60`) already ships a `/v1/network` route whose
   `get_network_info()` (`lifecycle/manager.py:360-374`) returns
   `{model_type, task_type, input_shape, output_shape}` — the closest thing to a capability
   descriptor in the ecosystem. It is post-hoc ("empty dict when no model") and **has zero live
   consumers** (verified: neither recurrence nor cascor imports `build_routers` or
   `ServiceLifecycleManager`). So P4-C is not greenfield — it is "make the post-hoc descriptor
   pre-hoc, and finally adopt the shared router". That reframing roughly halves it.
3. **juniper-cascor** does the same for `cascor` (and for its variants as the growth families land).
4. **canopy** gains `_fetch_capabilities()` alongside `_fetch_generators()` (`:2713-2740`) — same TTL
   cache, same fail-soft shape — and a canopy proxy route `GET /api/model/capabilities` mirroring
   `main.py:1681`. `MODELS` (`model_registry.py:167-193`) becomes `SEED_MODELS`, merged under
   last-known-good caching.
5. **FR9 becomes a closed loop**: the fail-closed rejection from the model service carries the
   contract it enforced, so canopy can diff its cached view against the enforcing view *at the moment
   of failure* and invalidate — turning drift into a self-healing event instead of a support ticket.

**Where compatibility knowledge lives afterwards.** Model requirements: **the service that serves the
model**, in the repo that ships it, changed in the same commit that changes the model. Dataset
properties: juniper-data (P4-B). Vocabulary + predicate: `juniper-model-core`, versioned and pinned.
Presentation + facets + the offline seed: canopy. **Owner on a new model: the model's author, in
their own repo. FR14 becomes true across repos** — which is the requirement the design of record
wrote down (`…MODEL-DATASET-SELECTION-DESIGN.md` FR14: "Adding a model/variant for benchmarking is
registry-only") and which is *false today* the moment the model is served by another service.

**Behaviour at scale.** This is the only proposal that survives the §6 trajectory. At 100+ variants
across several serving services canopy is never edited to learn about a model; a family that ships 30
benchmark variants ships them in its own repo. The `/v1/capabilities` payload at 200 models is a few
tens of KB — cache it, ETag it, and page it if it ever matters. It is also the only proposal that
handles **a model whose capabilities are only known at runtime** (a service that loads a checkpoint
and discovers its own input width): the service answers from what it actually loaded.

**When the feed is unavailable.** Layered, and this is where the design needs care:
`live capabilities → last-known-good cache → local seed → "unverified, all-enabled"`. Only the last
tier is truly fail-open, and it must be **labelled and time-stamped** ("model list from cache,
2026-09-02 14:11"). Fail-open is consistent with §5.9/FR9 as argued in P4-B, but the stakes are
higher on the model axis: enabling a model whose service is *down* leads to a training failure, and
`model_is_trainable()` (`model_registry.py:232-247`) already returns `True` for an unknown key
"so a transient desync never strands Start". That posture is correct for a *desync* and wrong for a
*known-down service* — P4-C should split the two: unknown → trainable (fail-open), known-unreachable
→ shown, not trainable, with the D8 status reason (`status="broken"` already exists in the vocabulary
at `model_registry.py:115` and is currently unused).

**Strengths.** The only proposal whose maintenance cost does not grow with the model population.
Makes drift *impossible by construction* on the model axis rather than *detectable*. Puts a real job
in front of `juniper-model-core`, which by its own framing ("model conformance kit") is the right
home for a conformance contract. Executes §5.9's noted unification, correctly scoped (schema shared,
instances not). And it is the only proposal that fills a hole rather than moving a fact: **no service
in the platform answers "what inputs does this model require" before training**, so canopy's local
`MODELS` is not a redundant copy — it is a stand-in for a missing contract, and P4-C is what retires
it honestly. Two of the three pieces already exist unused (`build_routers()`, `TrainableModel.input_shape`).

**Weaknesses.** Three repos plus a published package version, coordinated. Introduces a distributed
cache-coherence problem where there was none. Buys nothing at N=2 that P4-A does not buy for 1% of
the cost. **It does not fix the deadlock** — a perfectly service-sourced capability model still
produces a disconnected transition graph unless P4-A's symmetric policy (or D4's ✕) also ships. That
is worth stating twice: **P4-C is not a fix for this bug at all.** It is the architecture the bug
revealed.

**Risks.** Over-scoping — the characteristic failure of this lens, and I am naming it. A capability
endpoint that is written by hand and drifts from the enforcement path inside the *same service* is a
worse lie than canopy's honest local copy, because it is now authoritative. Mitigate with G8.

**Guardrails.**
- **G7 — cross-repo contract test.** In canopy's contract lane against the live stack: for every
  model in `SEED_MODELS`, assert the seed equals the service-advertised capability. Fails on drift,
  names both sides.
- **G8 — self-consistency test inside each model service** (the important one). The advertised
  contract must be *derived from* the same constant the validator uses; a service test feeds a
  deliberately non-conforming input for each declared axis and asserts the service rejects it with
  the documented status. Without G8 the endpoint is decoration.
- **G9 — schema version pin.** `juniper-model-core` version in the capability payload; canopy refuses
  (and falls back to seed, labelled) on a major mismatch, rather than mis-parsing.
- **G1** (reachability) runs against the *live merged* capability set in the stack CI leg — so a new
  model that fragments the graph fails CI before it reaches a user.

**Design-of-record impact.** Upholds D1, D5, D6, D7, D8. **Amends §7** (registry shape becomes a
cached projection). **Amends FR13/FR14** to be cross-repo rather than canopy-local. **Overturns
nothing.** Does not resolve OQ-6. **Elevates §5.9's parenthetical** — "a shared capability source
across services is a possible later unification (noted, not required)" — from optional to the
recommended end-state, with the sharpening that the shared thing is the schema.

**Migration path + phasing.** Strictly after P4-A and P4-B. Phase 1: `juniper-model-core.capability`
types + predicate, published, consumed by canopy *only as the type of its existing seeds* (zero
behaviour change, pure refactor, immediately reversible). Phase 2: recurrence exposes
`/v1/capabilities` + G8. Phase 3: canopy merges live over seed for recurrence-provided models only;
cascor stays seeded. Phase 4: cascor. Phase 5: retire the seeds to a genuine fallback. **Every phase
is independently valuable and independently revertible**; the seeds are never deleted.

---

### P4-D — Measure, don't declare: derive the contract from the artifact for datasets that have no metadata

**Partly canopy-only (the already-materialised case ships today); the pre-materialisation case is
CROSS-SERVICE. Dependency for the full version: a cheap juniper-data "describe" that returns shapes
without generating the full artifact.**

**One-line mechanism.** For any dataset whose properties are not declared — a CSV upload, a URL
fetch, an unregistered generator — compute rank / Δt-presence / task from the array itself and feed
*that* into the same predicate, instead of falling back to "compatible with everything".

#### How it works

1. Canopy **already does the measurement**: `demo_mode.py:1854` dispatches on `x_probe.ndim == 3`;
   `_install_sequence_dataset` (`:1936-2030`) derives `(W, L, F)`, reads `dt_full`/`dt_train`, and
   stamps `dataset_kind: "sequence"` at `:2009`. The result is used for *plotting* and discarded for
   *gating*.
2. Promote that derivation to a named pure function — `derive_dataset_contract(npz_or_arrays) ->
   DatasetContract` — returning `ndim` from `X.ndim`, `temporal="irregular"` when a `dt_*` array is
   present with non-constant spacing (`regular` when constant, `none` when absent), and `task_type`
   from the target dtype/one-hot shape (the exact test `demo_mode.py:1858-1859` already performs:
   `np.argmax(y_full, axis=1)` ⇒ classification).
3. Store it in a `dataset-contract-store` and let `get_dataset_spec()` prefer a measured contract
   over a seeded one for the currently-installed dataset.
4. The import surfaces that need it already exist: `dataset_import.py`, `/api/dataset/import_url`
   (`main.py:1640-1679`), and the plotter's Upload / Fetch-URL tabs.
5. **Cross-service arm**: `POST /v1/generators/{name}/describe` in juniper-data returning shapes only
   (no arrays) lets canopy measure *before* paying for generation — necessary because a 500-symbol
   equities pull is exactly what `DatasetTypeSpec.default_params` (`model_registry.py:148`) exists to
   bound.

**Where compatibility knowledge lives afterwards.** **Nowhere durable — it is derived.** Owner:
nobody, which is the point: a measured fact cannot drift from itself. The declared contracts (P4-B)
remain for the pre-materialisation case; the measured contract is authoritative once the artifact
exists, and a **disagreement between them is a first-class alert** (see G10) — that is the sharpest
drift detector in this whole document, because it compares a claim to a measurement rather than one
claim to another claim.

**Behaviour at scale.** This is the only proposal that is *correct* for user-imported datasets of
unknown rank, and it is the only one whose correctness is independent of the number of models,
datasets and services. Cost is O(1) per install and canopy already pays it.

**When the feed is unavailable.** Mostly not applicable — measurement is local. For the
pre-materialisation `describe` call: fall back to the declared contract, then to the seed, then to
optimistic-and-labelled. Never fail closed.

**Strengths.** Kills fact-location 6's redundancy by making it the *authority* instead of an orphan.
Turns the imported-dataset fail-open path from a blind spot into a measured answer. Provides the
claim-vs-measurement check nothing else can.

**Weaknesses.** Chicken-and-egg: you cannot gate on a shape you have not generated. Inverts the UX
(gate after selection rather than before) unless the `describe` arm ships. Δt regularity from a
sample is a heuristic, not a proof.

**Risks.** A measured contract that disagrees with a declared one will, sooner or later, be *right*
while the UI has already greyed the option — so the alert (G10) must be an alert, not a silent
override.

**Guardrails.**
- **G10 — claim-vs-measurement assertion.** On every install where both a declared and a measured
  contract exist, assert equality; on mismatch log at WARNING with both, surface a UI badge, and
  (in CI, against the stack) fail. This is the only drift check in this document that does not
  compare two hand-written copies to each other.
- **G11 — the measurement is a pure function with a golden-file test** over saved NPZ fixtures
  covering 2-D one-hot, 2-D regression, 3-D regular-Δt and 3-D irregular-Δt.

**Design-of-record impact.** Upholds D1 and FR3 (it *adds* an axis source, which §4 explicitly
provides for: "A new distinguishing property is one field on both specs + one clause"). **Amends
§5.8's degenerate-state handling** to distinguish "unknown, optimistic" from "measured, definite".
Does not resolve OQ-6.

**Migration path + phasing.** Phase 1 (canopy-only, ships now): extract `derive_dataset_contract`
from `demo_mode.py:1936-2030` and use it for the *imported* dataset path only — no behaviour change
for registered generators, fully reversible. Phase 2: G10 as a warning. Phase 3 (cross-service):
`describe`. **I would not schedule Phase 3 until P4-B has shipped**, because a declared contract is
the cheaper source for a registered generator.

---

## 5. Separately flagged defects (NOT folded into any proposal)

These are independent findings. Several of them **block** P4-A.

### Defect 1 — `restart-ds-type` is gated to `DEFAULT_MODEL_KEY` forever, and its options are never re-gated

`dashboard_manager.py:5422`:

```python
dcc.Dropdown(id="restart-ds-type", options=gated_dataset_options(DEFAULT_MODEL_KEY), value=DEFAULT_DATASET_TYPE, clearable=False, className="mb-2")
```

Assessment, as requested:

1. **The options are frozen at import time against `cascor`.** `restart-ds-type` appears as an
   `Output` exactly once — `:5268`, for **`value`** — and never for `options`. There is no analogue
   of `gate_dataset_options` (`:2603-2613`) for this control. So for any non-cascor model the restart
   modal's greying is *wrong*, not merely stale.
2. **It has no availability gate at all.** The sidebar composes
   `apply_availability_gate(gated_dataset_options(...), self._fetch_generators())` (`:2702`); the
   restart modal composes nothing. A generator juniper-data cannot serve is selectable here and
   greyed there — two controls for the same fact giving opposite answers in the same page.
3. **It can be populated with a value that its own options disable.** `open_restart_confirm_modal`
   (`:5284-5294`) seeds `restart-ds-type.value` from `nn-dataset-type-dropdown.value`. Once
   `(equities_seq, recurrence)` is reachable, the restart modal opens showing a value that its own
   option list marks `disabled` — unselectable, un-clearable (`clearable=False`), and still
   submitted on Confirm.
4. **The same fossil extends to its sibling fields.** `_build_restart_dataset_fields` (`:5416-5427`)
   offers only the four spiral-centric inputs (`samples`/`noise`/`rotations`/`spirals`); it never
   received N7's schema-driven treatment.
5. **And `_restage_dataset` (`:5618-5651`) forwards those spiral fields unconditionally for every
   dataset type** — whereas the sidebar's `apply_dataset` (`:2832-2874`) correctly restricts them
   with `if generator_name_for_type(dataset_type) == "spiral":`. So the restart path sends
   `nn_spiral_rotations` for an equities dataset. The N7 fix was applied to one of the two staging
   call sites.

**Severity: medium now, high the moment P4-A lands.** It is a second, unmaintained copy of the whole
dataset-selection surface. My recommendation is not to patch it five times but to make both controls
call one shared builder — which is a small refactor and exactly the "one predicate, two surfaces"
shape `…MODEL-DATASET-SELECTION-DESIGN.md` §5 already prescribes.

### Defect 2 — `RecurrenceBackend` has no `stage_dataset`; every dataset-staging control 500s once recurrence is selected

`main.py:3995` calls `backend.stage_dataset(**params)`. `DemoBackend` implements it
(`demo_backend.py:347-351`), `ServiceBackend` implements it (`service_backend.py:307-311`),
**`RecurrenceBackend` does not** — and `BackendProtocol` (`protocol.py:220-330`) does not declare it,
so no type checker flags the gap. The blanket `except Exception` at `main.py:4003-4008` converts the
`AttributeError` into an opaque `500 {"error": "Internal server error", "error_id": …}`. Three
controls reach it: sidebar **Apply Dataset**, the restart modal's **Confirm**
(`_restage_dataset:5638`), and **Live Dataset Switch**. **This is currently masked by the deadlock**
and is a hard blocker for P4-A. The structural fix is to declare the dataset-staging members on
`BackendProtocol` (which is what a "backend capability contract" would be, in miniature) and give
`RecurrenceBackend` an explicit, honest rejection rather than an `AttributeError`.

### Defect 3 — FR15 is unimplemented; `current_nn_model` is a write-only global and the sidebar can lie about the active model

`main.py:485` declares `current_nn_model`; `:3707` and `:3723` assign it; **nothing ever reads it**,
and no endpoint exposes it — there is no `GET /api/model`, only `POST /api/model/select` (`:3731`).
`/api/train/status` (`:3524-3530`) returns `backend` and `execution` but **not** `nn_model`.
Consequently `model-selection-store` is seeded to `DEFAULT_MODEL_KEY` (`dashboard_manager.py:1842`)
and never hydrated, while `model-class-store` *is* hydrated (`:2514-2531`). Because the backend is
**process-global and survives a page reload**, after selecting recurrence and refreshing the browser
the dashboard shows "Active: CasCor (Cascade-Correlation)" (`_initial_model_summary:2940-2948`) and
re-gates the dataset dropdown against cascor, while the live backend is recurrence. That is a
canopy-internal instance of exactly the drift class this document is about, and it directly
contradicts **FR15** of `…MODEL-DATASET-SELECTION-DESIGN.md` ("Selection initializes from current
backend state, is re-validated against the registry on load"). Fix: add `"nn_model": current_nn_model`
to `main.py:3530` and hydrate `model-selection-store` from it. One line plus one callback.

### Defect 4 — cascor's staging vocabulary does not contain canopy's only 3-D dataset

`juniper-cascor/src/api/models/training.py:235` pins
`Literal["spirals","xor","mnist","circles","moons","equities","gaussian","checkerboard"]`.
`equities_seq` is absent, so any staging of canopy's 3-D dataset through cascor is a 422 → canopy 502
(`main.py:3996-3999`). Conversely `gaussian` and `checkerboard` are accepted by cascor and unknown to
canopy's registry — a fourth divergent copy of the vocabulary (§3.1 row 5). **Also masked by the
deadlock**, and a blocker for P4-A. Guardrail G3 pins it.

### Defect 5 — the E2E walkthrough for this feature is vacuous, and the unit test that "covers" the snap tests an unreachable transition

`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` walkthrough **W8**
(lines 944–966) is the model-switch scenario. Its step 2 states that incompatible rows show a
**disabled** Select, and its step 5 instructs the tester to **click the `recurrence` Select** — from
the default preconditions those two steps are mutually impossible, and nobody noticed because W8 is
marked `N-A (no recurrence service)` and has never been executed. Meanwhile
`src/tests/regression/test_model_picker.py:88-96` asserts the dataset snap for `model_key="recurrence"`
and passes — while testing a transition the UI cannot produce. **Both are vacuous-pass instances**:
green machinery, no covered behaviour. Guardrails G1 and G2 close them.

### Defect 6 — canopy and juniper-data disagree about what `equities_seq` *is*, and canopy's answer is the one that keeps the feature alive

`juniper-data/juniper_data/api/routes/generators.py:117` declares `equities_seq` as
`task_type: "classification"`; `juniper-canopy/src/model_registry.py:141` declares it
`task_type="regression"`. Both are defensible — the generator emits a one-hot direction target *and*
a `y_reg_*` rider, and juniper-data's own registry comment says so (`generators.py:49-51`) — but the
metadata cannot express it because `task_type` is a single `str` on both sides
(`juniper_data/core/models.py:36`; `model_registry.py:90`). Not a live failure today, because the two
copies never meet. It becomes one the moment anybody wires juniper-data's `task_type` into canopy's
predicate: `compatible(equities_seq, recurrence)` would flip to False and the compatible set would
empty. Flagged separately because it is a **latent trap in the obvious next step**, and because the
correct resolution — model a generator's *emitted targets* as a set, and treat target selection as a
parameter — is an FR3/OQ-5 refinement worth deciding on its own merits rather than inside a PR that
is trying to do something else.

### Defect 7 — canopy hardcodes install hints that juniper-data already sends, behind a stale TODO

`juniper-canopy/src/dataset_schema.py:106-110` hardcodes `_UNAVAILABLE_REASONS` for `mnist` and
`arc_agi` with a generic fallback, under a module TODO at `:54-56`: *"Surface the generator's per-501
install hint verbatim once the /v1/generators list carries it (today only the create-time 501 body
carries the hint text)."* **That TODO is stale — the list payload carries it now**:
`GeneratorInfo.install_hint` (`juniper-data/juniper_data/core/models.py:118-128`), whose own comment
says it exists precisely so a preflight has "somewhere to send an operator". canopy is guessing at a
string the service is already sending, for exactly two generators out of sixteen, and every other
unavailable generator gets "unavailable in this deployment" instead of an actionable hint. A
five-line fix, independent of every proposal here, and a clean miniature of the whole thesis.

### Defect 8 — no facets, and the table component decision (OQ-4) is due for revisit

`…MODEL-DATASET-SELECTION-DESIGN.md` §5.2 and FR12 require facets over `category` / ndim-fit /
task-fit / `status` / `tags`. Only free-text search shipped
(`model_matches_search`, `model_registry.py:250-261`; the input at `dashboard_manager.py:2208-2215`).
`_build_model_selection_table` (`:3005-3090`) renders an unvirtualized `dbc.Table`; the code comment
at `:3021-3023` justifies that under OQ-4 as having "no virtualization payoff at this row count" —
true at 2 rows, and explicitly conditional on the row count. Not a defect today; a scheduled one
against §6's trajectory. Also: `ModelSpec.tags` is `frozenset()` for both seeds
(`model_registry.py:117`, `:167-193`), so the facet vocabulary does not yet exist to facet on.

---

## 6. Ranking, and what is too big

| Rank | Proposal | Verdict | Why |
|---|---|---|---|
| **1** | **P4-A — symmetric conflict policy** | **SHIP NOW** (after Defects 2 and 4) | Provably restores reachability; smallest diff; reuses machinery that already exists and is already tested; resolves OQ-6; fully reversible. It is the right *fix*. |
| **2** | **P4-B — producer-owned dataset contracts** | **SCHEDULE NEXT** (next sprint) | Three additive fields on a payload canopy already fetches, two of whose values already exist in juniper-data's own registry, following a migration template that already shipped in this code (N7). Highest architectural value per unit of risk — **and its functional payoff (five hidden 3-D datasets become usable) is larger than the deadlock fix's.** Independently deployable in either order. |
| **3** | **P4-C — service capability endpoints + `juniper-model-core` schema** | **SCHEDULE — end-state, not this bug** | The only design that survives 100+ variants across several serving services, and the only one that answers a question **no service currently answers at all**. Smaller than it first looks: `juniper-service-core.build_routers()` + `get_network_info()` already exist and are adopted by nobody. Still **TOO BIG to be the fix for this bug**, and — importantly — **it would not fix it**: a perfect capability feed still yields a disconnected transition graph without P4-A. |
| **4** | **P4-D — measure, don't declare** | **PHASE 1 NOW (cheap), PHASE 3 DEFERRED** | Phase 1 is a canopy-only extraction of code that already exists (`demo_mode.py:1936-2030`) and is the correct answer for user-imported data. **Phase 3 (the `describe` endpoint) is TOO BIG for this bug.** Best value as the imported-dataset arm of P4-B, not as a standalone architecture. |

**Naming the over-scoping, as required.** P4-C and P4-D-Phase-3 are over-scoped as answers to *this*
defect. The characteristic failure of my lens is to answer "the dataset dropdown is deadlocked" with
"and therefore the platform needs a federated capability plane", and I want that on the record:
**the deadlock is caused by a missing `else` branch on the model side of a bidirectional gate.** It
took me a bipartite-connectivity argument to prove it, but the fix is twenty lines. The capability
architecture is what the defect *revealed*; it is not what the defect *requires*. Shipping P4-C first
would leave the user with a beautifully-sourced capability model and a dashboard that still cannot
reach the LMU.

Equally, the reverse over-correction should be named: shipping **only** P4-A leaves six divergent
copies of the compatibility facts and a `DATASET_TYPES` tuple hand-edited in canopy every time
juniper-data adds a generator. That is not a future risk — it is a present, measured loss. The copies
have **already** diverged three ways (Defect 4: cascor's vocabulary lacks canopy's only 3-D dataset;
Defect 6: canopy and juniper-data disagree on that dataset's task type; §2.1: canopy shows 6 of 16
generators and 1 of 6 rank-3 generators). P4-A fixes one stranded pair. **P4-B recovers five entire
datasets.**

**Recommended sequence:** Defect 3 (one line) → Defect 2 + Defect 4 (unmask blockers) →
G1/G2 (red) → **P4-A** (green) → Defect 7 (five lines, free) → Defect 1 (unify the two dataset
surfaces) → decide Defect 6's `targets` shape → **P4-B** + G5/G6 → P4-D Phase 1 + G10 → **P4-C**
phased, only if the model population actually reaches the §6 numbers.

---

## 7. The strongest objection to my top pick

**The objection.** P4-A resolves OQ-6 by fiat, in the direction that *silently mutates a choice the
user already made*, at the moment they are least able to notice — they clicked inside a modal, the
modal closed, and the sidebar changed underneath them. `…MODEL-DATASET-SELECTION-DESIGN.md` §5.6
specifies the conflict policy as "keep model, **clear** dataset + notice" — *clear*, not *silently
substitute*. A reviewer can fairly say: the ratified decision D4 already solved this with an explicit
✕ that expresses **user intent**, whereas a snap expresses **the system's inference**; implementing
the ratified decision is strictly preferable to amending FR5 to make room for an unratified one. And
P4-A hardcodes one global policy when the two surfaces may honestly want different ones.

**My answer, and its limits.** D4-as-written is not free, and I do not think its cost was ever
priced: `clearable=True` on `nn-dataset-type-dropdown` produces a `None` dataset that at least four
downstream consumers do not handle — `apply_dataset` (`:2832`, sends `nn_dataset_type: None`),
`resolve_oneshot_start_body` (`:2662-2681`, returns `None`, which is precisely the "no dataset
reference" bail at `recurrence_backend.py:140`), `render_dataset_params` (`:2760`), and
`annotate_model_hint` (`:2956-2962`). So D4 is a larger, riskier change than the snap, for a state
(null dataset) that no other part of canopy models. The snap reuses a code path that already exists
and already has tests.

But the objection lands on one point and I concede it: **silence is the flaw, not the snap.** That is
why P4-A's shipped form keeps FR5's disabled primary button and adds a *secondary action whose label
names the consequence* — `Select — switches dataset to Equities (sequence)` — plus the post-swap
notice §5.6 requires and neither surface renders today. That converts the system's inference into the
user's informed intent, which is what D4 was actually protecting. If the reviewer still prefers the
✕, the honest resolution is to ship both: the secondary action for reachability now, and D4's clear
as a follow-up once a null-dataset state is properly modelled — and to say so in the decision record
rather than letting D4 remain ratified-but-unimplemented for a third release.
