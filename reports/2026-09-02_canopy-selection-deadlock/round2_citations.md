# Round-2 Citation Audit — FALSE AUTHORITY lens

**Auditor**: round-2 citation auditor, independent-agent consensus review
**Date**: 2026-09-02
**Documents under audit** (NOT edited):

- `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` (hereafter **PROPOSALS**)
- `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (hereafter **DESIGN**)

Both live in the worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/wondrous-spinning-piglet/notes/`.

Repos verified against: `juniper-canopy` @ `30e15b7` (clean), `juniper-data`, `juniper-recurrence`,
`juniper-ml`.

Method: every `file:line` and bare `:NNN` citation was extracted programmatically from both documents
(script: `scratchpad/inventory.py`), then each was opened at the cited line. Numeric claims were
re-derived with an **independent** BFS (`scratchpad/indep_bfs.py`) that reads the model gate off the
real rendered `_build_model_selection_table` buttons rather than re-implementing `model_reason` —
a different entry point from the reconciler's probe.

---

## 0. Executive summary

| bucket | count |
| --- | --- |
| WRONG LINE (citation resolves to the wrong line) | **4** |
| WRONG CLAIM / NOT FOUND (the asserted fact is false or unlocatable) | **6** |
| WRONG or unscoped NUMBER / DATE | **6** |
| MISQUOTE (quoted material not verbatim) | **2** |
| Internal contradiction between / within the documents | **3** |
| Notation / convention defect | **3** |
| CONFIRMED correct (spot-verified) | ~55 |

Four citations land **inside docstring prose** or on a bare `try:` rather than on the code they
name. Two of those four appear in **both** documents.

---

## 1. WRONG LINE — citation resolves to the wrong line (BLOCKS MERGE)

### 1.1 `main.py:3993` — off by one, cited TWICE

| | |
| --- | --- |
| **Cited in** | PROPOSALS §6.1 row X4 (doc line 344); DESIGN §4.2 (doc line 90) |
| **Claim** | "`main.py:3993`'s `model_dump(exclude_none=True)` strips it into a vacuous 200" |
| **Actual** | `src/main.py:3993` is `    try:`. `params = body.model_dump(exclude_none=True)` is at **`:3994`**. |
| **Verdict** | **WRONG LINE** (off by 1, repeated in both documents) |

```
3992|     """
3993|     try:                                          <- the cited line
3994|         params = body.model_dump(exclude_none=True)   <- the actual line
3995|         result = await asyncio.to_thread(backend.stage_dataset, **params)
```

The *mechanism* is correct — `StageDatasetRequest.nn_dataset_type` is `Optional[str] = None`
(`main.py:3971`), so `exclude_none=True` does strip a `None`.

### 1.2 `_restage_dataset:5623` — lands in a docstring, cited TWICE

| | |
| --- | --- |
| **Cited in** | PROPOSALS §6.1 row X4 (doc line 344); DESIGN §4.2 (doc line 93) |
| **Claim** | "The correct idiom already exists at `_restage_dataset:5623`." |
| **Actual** | `:5623` is docstring prose: `fields only when present. N3b uses the ROUTE (not a new staging path) so`. The idiom is at **`:5629-5631`**. |
| **Verdict** | **WRONG LINE** (off by 6–8; points at prose, not code) |

```
5618|     def _restage_dataset(self, dataset_vals):
5623|         fields only when present. N3b uses the ROUTE (not a new staging path) so   <- cited
5628|         payload = {}
5629|         dtype = dataset_vals.get("dataset_type")     <- the actual idiom
5630|         if dtype is not None:
5631|             payload["nn_dataset_type"] = dtype
```

### 1.3 `:2836` — lands in a docstring, cited TWICE

| | |
| --- | --- |
| **Cited in** | PROPOSALS §6.1 row X3 (doc line 343); DESIGN §4.6 (doc line 126) |
| **Claim** | "skipping `generator_name_for_type`, which both sibling handlers apply (`:2769`, `:2836`)" |
| **Actual** | `:2836` is docstring prose inside `_apply_dataset_handler`. The `generator_name_for_type` call is at **`:2846`**. |
| **Verdict** | **WRONG LINE** (off by 10). `:2769` is **CORRECT**. |

```
2831|     def _apply_dataset_handler(self, n_clicks, dataset_type, ...):
2836|         as before (the force-blur clientside callback commits the numeric inputs first, so...  <- cited
2845|         payload: dict = {"nn_dataset_type": dataset_type}
2846|         if generator_name_for_type(dataset_type) == "spiral":   <- the actual call
```

### 1.4 `:2896` — points at the `except` tail, not the response read

| | |
| --- | --- |
| **Cited in** | DESIGN §4.4 (doc line 107) |
| **Claim** | "`_select_model_handler` (`:2896`) must read `swapped` and `backend` from the `POST /api/model/select` response" |
| **Actual** | `:2896` is `self.logger.debug("Model select request failed: %s", exc)` — inside the `except`. The function `def` is `:2876`; the response read is `:2891-2893`. |
| **Verdict** | **WRONG LINE** |

```
2876|     def _select_model_handler(self, model_key):        <- the function
2891|             if resp.ok:
2892|                 data = resp.json()
2893|                 return data.get("nn_model", model_key), data.get("execution", "live"), self._model_summary_text(data)   <- where the change goes
2895|         except Exception as exc:
2896|             self.logger.debug("Model select request failed: %s", exc)   <- cited
```

### 1.5 `test_model_table.py:170` — off by one (minor)

PROPOSALS §2.3 (doc line 160): "`test_model_table.py:170` even carries the comment *'(e.g. cleared)'*."
`:170` is the `def` line; the comment is at **`:171`**. The *same document* cites `:170-173`
correctly elsewhere (doc lines 410 and DESIGN line 72). **WRONG LINE, minor.**

---

## 2. WRONG CLAIM / NOT FOUND (BLOCKS MERGE)

### 2.1 "both JS consumers of the dropdown value" — NOT FOUND, and self-contradicted

| | |
| --- | --- |
| **Cited in** | DESIGN §4.1 (doc lines 72–73); PROPOSALS §7 item 1 (doc line 411) |
| **Claim** | "B1 verified all ten Python consumers **and both JS consumers** of `nn-dataset-type-dropdown.value` are null-safe." |
| **Actual** | **Zero** JS references to `nn-dataset-type-dropdown` exist anywhere in canopy: 0 hits across all six `src/frontend/assets/*.js`, and 0 across all 29 inline `clientside_callback` blocks in `dashboard_manager.py`. All **10** consumers of `.value` are server-side Python callbacks (`:2576, 2606, 2609, 2624, 2637, 2649, 4922, 5153, 5210, 5285` — none inside a clientside registration; the nearest clientside block, `:5179–5200`, does not touch the id). |
| **Verdict** | **NOT FOUND** |

This is **directly contradicted by PROPOSALS §1.2** (doc line 68), which states "zero hits for these
ids across all six `assets/*.js`". Both statements cannot be true. My grep confirms §1.2.

The nearest real artifact is one clientside callback at `:4366` whose 8th `State` is
`oneshot-start-params-store` — a *derived* store, not the dropdown value — and its twin at `:4410`
is the **server-side** branch of the same `if/else`, so even "two" is wrong there.

**"ten Python consumers" is CORRECT** (exactly 10), though one of the ten (`:2606`) is the `Output`,
i.e. 9 readers + 1 writer.

### 2.2 "the only three resolvers with no injectable parameter" — there are FIVE

| | |
| --- | --- |
| **Cited in** | PROPOSALS §5.2 (doc lines 278–280); DESIGN §5 "Enabling change" (doc lines 154–156), the latter in the stronger form "while **every sibling** has one" |
| **Claim** | "`gated_dataset_options`, `get_model_spec` and `get_dataset_spec` are the only three resolvers in `model_registry.py` with **no injectable parameter**, while their siblings (`compatible_models`, `compatible_datasets`, `model_options`) all have one." |
| **Actual** | **Five** functions resolve against a module-level registry with no injectable parameter |
| **Verdict** | **WRONG CLAIM** — and load-bearing |

| function | line | injectable? |
| --- | --- | --- |
| `dataset_type_options()` | `model_registry.py:200` | **NO** — iterates `DATASET_TYPES` directly |
| `dataset_default_params(value)` | `:209` | **NO** — iterates `DATASET_TYPES` directly |
| `get_model_spec(key)` | `:264` | NO (as documented) |
| `get_dataset_spec(value)` | `:276` | NO (as documented) |
| `gated_dataset_options(model_key)` | `:408` | NO (as documented) |

`dataset_type_options()` is the **exact dataset-side counterpart of `model_options()`** — which the
documents name as a *sibling that has one*. So the claim is false on its own taxonomy.

**Why this matters beyond pedantry:** `dataset_default_params` is called by
`_resolve_oneshot_start_body_handler` at `dashboard_manager.py:2682` — squarely on the path
DESIGN §4.6/G5 will test. The DESIGN's §5 "Enabling change" list is therefore **incomplete**: G1c/G1d
driven from a synthetic registry would still hit two hardcoded resolvers the plan does not name.

### 2.3 "canopy reads it nowhere" (`task_type`) — false, and self-contradicted

| | |
| --- | --- |
| **Cited in** | PROPOSALS §5.3 table (doc line 295): "`task_type` conflict is live \| **REFUTED** \| `GeneratorInfo` omits it; canopy reads it nowhere" |
| **Actual** | canopy reads `task_type` in production code at `src/model_registry.py:90` (field decl), **`:318`** (the `compatible()` predicate — one of three axes), **`:347–348`** (`dataset_reason`), **`:367`** (`model_reason`). |
| **Verdict** | **WRONG CLAIM** |

The defensible narrower claim is: *canopy never reads `task_type` from juniper-data's payload — it
hardcodes its own copy in the `DATASET_TYPES` seeds.* That is true and verifiable
(`src/dataset_schema.py:230–246` reads only `name` and `available` from `/v1/generators`).

**Contradicted by §7.1 of the same document** (doc line 449): "adopting juniper-data's `task_type`
naively would make `compatible_models(equities_seq) == []`" — an effect only possible *because*
canopy reads `task_type`. (§7.1's own claim is **CORRECT**: juniper-data declares
`equities_seq` as `task_type: "classification"` at `generators.py:113–118`, while recurrence
supports only `regression`.)

### 2.4 `_synthetic.py` "is their shared windowing module and emits `(W, L, F)`" — wrong module

| | |
| --- | --- |
| **Cited in** | PROPOSALS §6.2 (doc lines 352–353) |
| **Claim** | "Rank confirmed rather than inferred — `juniper_data/generators/_synthetic.py` is their shared windowing module and emits `(W, L, F)`." |
| **Actual** | `_synthetic.py` (115 lines) contains **zero** array-shaping code — no `reshape`, `stack`, `newaxis`, or rank-3 indexing. It is a params-base + scaling-glue module (`SyntheticSequenceParams` `:48`, `attach_scaling` `:96`, five-line delegator `build_sequence_arrays` `:76`). The real windowing module is **`juniper_data/generators/_sequence.py`**, where `x = arr[win_idx]  # (W, L, F)` appears at **`:237`** (`window_regular_series`) and **`:329`** (`window_timed_series`). |
| **Verdict** | **WRONG CLAIM** |

"All five use it" is also false: only **3 of 5** route windowing through `_synthetic`
(`multi_sine/generator.py:56`, `mackey_glass/generator.py:52`, `ar_p/generator.py:49`).
`irregular_sine/generator.py:24` and `delay_product/generator.py:35` import `window_timed_series`
**directly** from `_sequence.py` — necessarily so, since `_synthetic.build_sequence_arrays`
hardcodes `window_regular_series`, which cannot express their non-uniform Δt.

The *rank-3 conclusion* survives; only the named evidence is wrong.

### 2.5 §6.2 "regular Δt so `temporal_ok` passes" — wrong reason for 2 of the 5

PROPOSALS §6.2 (doc lines 355–356): "Each satisfies canopy's own predicate against the LMU (rank 3 ✓,
regression ✓, **regular Δt** so `temporal_ok` passes ✓)."

juniper-data's own registry descriptions say the opposite for two of them:

- `irregular_sine` (`generators.py:145`): "K sinusoids sampled at **NON-uniform (jittered)** times …
  with a non-uniform per-step dt and variable target_dt."
- `delay_product` (`generators.py:153`): "**Irregularly-sampled** sinusoid superposition (the same
  non-uniform Δt as irregular_sine)."

**Verdict: WRONG REASON, conclusion survives.** `temporal_ok` passes for irregular data too, because
recurrence carries `requires_dt=True` (`model_registry.py:187`, `:306–308`). The count of five holds.

### 2.6 Y1 "Eight backend methods missing from `RecurrenceBackend`" — no basis yields 8

PROPOSALS §6.4 row Y1 (doc line 383).

| basis | true missing count |
| --- | --- |
| vs `BackendProtocol` (`src/backend/protocol.py:220`) | **0** — `RecurrenceBackend` implements it exactly |
| vs the Demo ∩ Service common surface | **9** |
| vs `ServiceBackend` (31 public) | **11** |
| vs `DemoBackend` (31 public) | **11** |

The nine: `cancel_pending_dataset`, `cancel_swap_dataset_live`, `get_dataset_swap_events`,
`get_experimental_functions`, `get_pending_dataset`, `get_snapshot_dataset_swaps`,
`set_experimental_functions`, `stage_dataset`, `swap_dataset_live`.

**Mitigating**: PROPOSALS §6.4 explicitly frames Y1–Y8 as "Reported once each and **not** re-derived
by the reconciler — leads, not facts". The label is doing its job. Report, don't block.

---

## 3. WRONG / UNSCOPED NUMBERS AND DATES

### 3.1 "11 sites across 2 files" — the components sum to 12

DESIGN §6 (doc line 170–171): "4 forced assertion inversions, 3 rendered vacuous, 1 premise
destroyed, 4 callback-arity breaks — **11 sites across 2 files**."

4 + 3 + 1 + 4 = **12**. **Arithmetic error** (the source, `reports/…/laneB3.md:176`, carries the same
"11"). Either a component is over-counted or the total is under-counted; the document does not say
which.

### 3.2 PR #393's timestamp is wrong by two hours

PROPOSALS §2.2 chain table (doc line 120) gives **#393 = `06-24 17:41`** and **#394 = `06-24 17:41`**.

| PR | merge commit | git author=commit date | `gh` mergedAt |
| --- | --- | --- | --- |
| #393 | `c6ad56d` | **2026-06-24 15:40:59 -0500** | `2026-06-24T20:41:00Z` |
| #394 | `2122a7d` | 2026-06-24 17:41:29 -0500 | `2026-06-24T22:41:30Z` |

They are **2h 00m 30s apart**, not the same minute. All commits in this repo are `-0500`; no timezone
renders `20:41:00Z` as `17:41`. This looks like #394's local time copied onto #393's row.
The "both landed the same minute" reading the table invites is **false**. **WRONG.**

#397 (`442673e`, `2026-06-25 07:29:48 -0500`) and #400 (`a96a114`, `2026-06-25 17:17:53 -0500`) are
**CORRECT**.

### 3.3 `f464272` is not `442673e`'s parent

PROPOSALS §2.2 code block (doc line 107) frames `f464272` as "(before #397)". It is PR **#395**;
`git rev-parse 442673e^` returns **`c2058be`** (PR #396, a README-only commit).

**Evidence not damaged**: `git diff --stat f464272 c2058be` → `README.md | 279 +++---`, 1 file
changed; `dashboard_manager.py` is byte-identical, and `c2058be` also has `model-select-btn` count 0
and the `nn-model-dropdown` at `:1069`. But a reader running `git show 442673e^` gets a different SHA
than the document names. **MISLEADING ANCHOR.**

### 3.4 `model-select-btn count: 4` is unscoped, and half of it is prose

At `442673e`: **4** in `dashboard_manager.py`, **10** repo-wide (CHANGELOG 1, dashboard_manager 4,
`test_model_table.py` 5). Of the 4 in `dashboard_manager.py`, only **2** are live wiring
(`:2155` `Input({"type": "model-select-btn", ...})`, `:2332` `id={"type": "model-select-btn", ...}`);
`:2144` is a comment and `:2257` a docstring. **AMBIGUOUS/UNSCOPED.**

### 3.5 `13a5856` "`clearable=False` ships" is unscoped

True for `nn-dataset-type-dropdown` (the diff introduces the whole block; date `2026-05-10 03:07:08
-0500` is **CORRECT**). But the repo's **first** `clearable=False` is `31d458f`, **2026-04-05**
(`nn-init-output-weights-dropdown`) — five weeks earlier. As written ("`clearable=False` ships"), the
row is wrong. **UNSCOPED.**

### 3.6 "five weeks before" understates by three days

2026-05-10 → 2026-06-17 (the design of record's own date, verified in its header) is **38 days** =
5 weeks 3 days. **IMPRECISE** (~9% understatement).

### 3.7 "464-component layout" — the number is real but the noun is wrong

PROPOSALS §1.2 (doc line 67): "no `dcc.Location`/`Link` anywhere in the 464-component layout".

Measured on the real `DashboardManager({})` app layout:

| counting method | value |
| --- | --- |
| recursive component walk | **1162** |
| components with a non-`None` `id` | **464** |
| unique non-`None` ids | **464** |
| `layout._traverse()` | 1201 |
| top-level children | 81 |

So **464 = id-bearing components**, not the layout's component count. The *conclusion* is
**CONFIRMED and stronger than claimed**: `Location = 0`, `Link = 0` across all **1162** components,
not merely the 464. **NUMBER CORRECT under a stated reading; noun imprecise.**

### 3.8 "~14 h after the deferral" — CORRECT as an approximation

#394 → #397 is exactly **13h 48m 19s** (identical on author dates and on `gh` `mergedAt`). Flagged
"~", so acceptable. Note it is right only because the table's *other* time (#393) is the wrong one.

---

## 4. MISQUOTES

### 4.1 #394's PR body — unmarked elision inside quotation marks

- **Doc** (line 121): *"only model→dataset is needed for the sidebar flow (the model is selected first)"*
- **Real**: `Bidirectional gate**: only model→dataset is needed for the sidebar flow (the model is selected first; §5.6 "a newly selected option is never incompatible").`

The document **closes the parenthesis where the original has a semicolon**, silently deleting the
§5.6 clause. Exact-match count against the real body: **0**. **MISQUOTE** (substantively faithful).

### 4.2 #397's PR body — unmarked splice across ~90 characters

- **Doc** (line 122): *"swaps only the input side; every downstream gate follows for free"*
- **Real**: `A1b-1 swaps only the **input** side; the table's Select writes those same stores via the unchanged `_select_model_handler`, so every downstream gate follows for free (both kept **byte-unchanged**).`

Two fragments spliced with no ellipsis, dropping the `so` that makes the second clause consequential.
Exact-match count: **0**; each fragment individually: 1. **MISQUOTE.**

### 4.3 #394's second quote — CORRECT (case-normalised)

*"deferred … happy to add a literal ✕ if wanted"* — real text has `Happy` capitalised (two separate
sentences, ellipsis correctly marked). **CORRECT.**

---

## 5. INTERNAL CONTRADICTIONS AND CROSS-REFERENCE DEFECTS

### 5.1 The `G` identifiers collide between the two documents

PROPOSALS §8 defines G1–G5. DESIGN §5 **redefines G2, G3 and G5 to mean different things**, and
never says it is renumbering. The two documents cross-reference each other on every page.

| id | PROPOSALS §8 "Guardrails" | DESIGN §5 "Test plan" |
| --- | --- | --- |
| G1 | reachability closure | (G1a–G1d) BFS reachability — **compatible** |
| **G2** | no reachable-invalid state | **`restart-ds-type.options` re-gate on model change** |
| **G3** | availability composition | **model summary reflects `swapped is False`** |
| G4 | registry drift | canopy `DATASET_TYPES` ⊆ `GENERATOR_REGISTRY` — **same** |
| **G5** | model-state truth | **one-shot body routes through `generator_name_for_type`** |

Concretely: DESIGN §7 says "PR 1 = §4.4 + **G3**" and "PR 3 = §4.5 + §4.6 + **G2, G4, G5**". A reader
resolving those against PROPOSALS §8 concludes PR 1 ships *availability composition* and PR 3 ships
*no-reachable-invalid-state* and *model-state truth* — none of which is what the DESIGN means.
PROPOSALS G2 maps to DESIGN G1b; PROPOSALS G3 maps to DESIGN G1d/N8; PROPOSALS G5 maps to DESIGN G3.

**This is the highest-value cross-reference defect found.**

### 5.2 §1.2 vs §7 / DESIGN §4.1 on JS consumers

See §2.1 above. "zero hits for these ids across all six `assets/*.js`" (PROPOSALS §1.2) vs
"both JS consumers of the dropdown value" (PROPOSALS §7, DESIGN §4.1). The former is correct.

### 5.3 §5.3 vs §7.1 on `task_type`

See §2.3 above.

### 5.4 "Six independent instruments" vs "All four confirm"

PROPOSALS §1.1 (doc line 32): "**Six** independent instruments agree." PROPOSALS §10 (doc lines
504–506): "Lane A — 3 agents … + the reconciler's own probe. **All four** confirm 5-of-6
reachability." §5.3's table also says "6 instruments". The six presumably include two Lane-B agents,
but the document never enumerates them. **Unreconciled; not necessarily contradictory.**

### 5.5 `§1756` used for a LINE number

PROPOSALS §11 References (doc line 531): "`JUNIPER_2026-08-09_…E2E-VALIDATION-EVIDENCE.md` **§1756**
— W8's `N-A` blocking." 1756 is a **line** number; the same document cites it correctly as `:1756` at
doc line 148. There is no §1756 in that 4,884-line file. **NOTATION ERROR.**

### 5.6 Bare section references violate the mandatory naming convention

`CLAUDE.md` / `Juniper/AGENTS.md` § Cross-Project Conventions: *"if [a summary] references two or
more [documents], **every** reference carries its filename."* Both documents reference 4+ documents.
Bare `§5.6` appears at PROPOSALS doc lines 131, 135, 291, 443, 506 with no document named; `§5.6`,
`§5.5`, `§5.9`, `§2.1`, `§2.2` etc. do not resolve within the citing document. Most are
contextually recoverable (DESIGN consistently prefixes "evaluation §…"; PROPOSALS names "design
§5.8" at line 158), but PROPOSALS §5.3's table row "§5.6's premise is false" and §7.1's "both §5.6
policies" are bare. **CONVENTION BREACH.**

### 5.7 §5.4's "the parked pair fails on a name … not a shape" — undefined referent

PROPOSALS §5.4 (doc lines 316–318). Read as *"what happens at runtime to a pair that gets past a
relaxed UI gate"*, the claim is **mechanically CORRECT**: `_resolve_oneshot_start_body_handler`
(`:2681`) emits `{"generator": <raw dropdown value>}`, `main.py:750–773` (`_recurrence_start_kwargs`)
copies it verbatim, `generator_name_for_type` is never called in `main.py`, canopy's value is
`spirals` (`model_registry.py:133`) and juniper-data registers `spiral` (`generators.py:54`), and
`recurrence_service_adapter.py:236–237` states "The dataset is referenced (not piped)".

Read as *"why the pair is unreachable today"*, it is **wrong**: today the pair is parked by canopy's
own `ndim` gate (`model_registry.py:318`, `:183`) — a shape axis, and the UI reason is literally
shape-worded (`f"needs a {dataset.ndim}-D model"`, `:346`). The paragraph never names which pair.
**AMBIGUOUS WORDING** — one adversarial reviewer read it the second way and graded it WRONG.

---

## 6. CONFIRMED CORRECT — the load-bearing set

### 6.1 `dashboard_manager.py` citations

| citation | claim | verdict |
| --- | --- | --- |
| `:1334` | `clearable=False` on `nn-dataset-type-dropdown` | **CORRECT** |
| `:1842` | `model-selection-store` seeded to `DEFAULT_MODEL_KEY`, `storage_type="memory"` | **CORRECT** |
| `:1871` | `params-init-interval`, `max_intervals=1` | **CORRECT** |
| `:2590` | sole writer of `model-selection-store.data` = `select_model` | **CORRECT** (decorator line; `def select_model` at `:2598`) |
| `:2604` | sole writer of `nn-dataset-type-dropdown.value` = `gate_dataset_options` | **CORRECT** (decorator line; `def` at `:2612`) |
| `:2609` | the dataset is read as `State`, not `Input` | **CORRECT** |
| `:2681` | one-shot body sends the raw dropdown value as `generator` | **CORRECT** |
| `:2695` | docstring says "dataset-primary conflict policy, D5" | **CORRECT** |
| `:2702-2706` | availability∘compatibility composition + the snap + `no_update` arm | **CORRECT** |
| `:2702-2703` | `apply_availability_gate(gated_dataset_options(...))` | **CORRECT** |
| `:2769` | sibling handler applies `generator_name_for_type` | **CORRECT** |
| `:2845` | `payload: dict = {"nn_dataset_type": dataset_type}` (unconditional) | **CORRECT** |
| `:3050` | `disabled=not is_compatible` | **CORRECT** |
| `:3051` | `title=(reason or …)` on a button whose text content is "Select"/"Selected" (`:3045`) | **CORRECT** |
| `:3070-3074` | alert says "switch the dataset in the sidebar" (at `:3072`) | **CORRECT** |
| `:5260-5293` | `open_restart_confirm_modal` callback | **CORRECT** |
| `:5268` | `Output("restart-ds-type", "value")` | **CORRECT** |
| `:5422` | `restart-ds-type` dropdown, `options=gated_dataset_options(DEFAULT_MODEL_KEY)`, `clearable=False` | **CORRECT** |
| `:6308-6324` | `_completion_reason_label` maps exactly five cascor reasons | **CORRECT** |
| `:7206` | `if not model_is_trainable(model_key)` gates Start on status only | **CORRECT** |

Note: `:3018` and `:3033` (listed in the audit brief) are **not cited in either document** — nothing
to verify.

### 6.2 The inverted D5 label — CONFIRMED, and it is a real defect

Design of record `…MODEL-DATASET-SELECTION-DESIGN.md:165-167`:

```
165| - *dataset-primary:* keep dataset, clear model + notice.
166| - *model-primary:* keep model, clear dataset + notice. (Fits the model-centric
167|   benchmarking trajectory.)
```

The snap at `dashboard_manager.py:2702–2706` keeps the model and moves the dataset =
**model-primary**; its docstring at `:2695` calls it "dataset-primary conflict policy, D5".
PROPOSALS §2.2 is **CORRECT**.

### 6.3 Design-of-record anchors — all CONFIRMED

| ref | line in design of record | verdict |
| --- | --- | --- |
| D2 | `:52` — "disabled (greyed) … reason on the option itself … No reverse-mapped selected-side tooltip as the sole channel" | **CORRECT** |
| D4 | `:54` — "Clear/reset = conventional inline ✕ on each control" | **CORRECT** |
| D5 | `:55` — swappable policy, default chosen after the A1 spike | **CORRECT** |
| D7 | `:57` — dedicated full-width surface; sidebar keeps the dataset dropdown | **CORRECT** |
| D8 | `:58` — lifecycle status drives presentation | **CORRECT** |
| §5.5 | `:152` — "Conventional inline ✕ … and a 'clear model / show all' reset" | **CORRECT** |
| §5.6 | `:159` — "A newly *selected* option is never incompatible (greyed)" `:161` | **CORRECT** |
| §5.6 policies | `:165-167` (brief said `:166-168` — off by one, but the document itself cites no line numbers here) | **CORRECT** |
| §5.8 | `:181-185` — "clear the dataset" recovery copy | **CORRECT** |
| §5.9 / FR9 | `:191-196`, `:77` — "fails closed on shape mismatch" | **CORRECT** |
| §6 | `:200-220` + FR12 `:80` — "dozens-to-hundreds" | **CORRECT** |
| §8 rules out `title=` | `:272-274` ("no per-option `title`/tooltip") and `:285-288` ("disabled elements don't fire hover/focus") | **CORRECT** — though §8 addresses dropdown options and disabled elements, not `title=` generally; the Y7 button *is* disabled when incompatible, so the generalisation holds |
| FR5 | `:72` | **CORRECT** |
| FR6 | `:73` | **CORRECT** |
| FR15 | `:83` | **CORRECT** |
| OQ-6 | `:305` — "conflict-policy default … decide post-spike (D5)" | **CORRECT** |

Note: the design of record's §8 header says **dash 4.1.0**, but the installed `JuniperCanopy1` is
**dash 4.2.0** — so PROPOSALS Y7's "dash 4.2.0's dropdown" is **CORRECT** and it is the *older*
document that is stale.

### 6.4 Test-file citations

| citation | verdict |
| --- | --- |
| `test_model_table.py:170-173` | **CORRECT** — comment "No dataset selected (e.g. cleared)" at `:171`, `_build_model_selection_table(None, "cascor")` at `:172`, `all(button.disabled is False …)` at `:173` |
| `test_model_table.py:134-135` | **CORRECT** — cascor `False` / recurrence `True` against `spirals` |
| `test_model_table.py:143-144` | **CORRECT** — recurrence `False` / cascor `True` against `equities_seq` |
| `test_model_table.py:201` | **CORRECT** — `_button_for(children, "cascor").disabled is True` |
| `test_d8_d11_phase4_truth_up.py:64-82` | **CORRECT** — `swapped is False` (`:81`), `backend != "recurrence"` (`:82`), comment "the successful selection of a model that is not actually active" (`:78`) |
| `test_recurrence_routes.py:164-171` | **CORRECT** — 409 + "no dataset reference" pinned |
| `test_oneshot_start_body.py:205-216` | **CORRECT** — `("one_shot", "equities_seq")` as literal arguments at `:207` |
| `test_model_picker.py:56` | **CORRECT** — `manager._select_model_handler("recurrence")` called directly |

### 6.5 `recurrence_backend.py`, `settings.py`, backends

| citation | verdict |
| --- | --- |
| `recurrence_backend.py:138-140` | **CORRECT** — `ControlResult(ok=False, error="no dataset reference …")` before any thread |
| `recurrence_backend.py:153-156` | **CORRECT** — thread created `:153`, `start()` `:155`, `ok=True` `:156` |
| `settings.py:261` | **CORRECT** — `recurrence_service_url: Optional[str] = None` (the code default) |
| `demo_backend.py:347` / `service_backend.py:307` / `cascor_service_adapter.py:1524` | **CORRECT** — all three `def stage_dataset` exactly at those lines |
| "`RecurrenceBackend` has 20 methods; `stage_dataset` is not among them" | **CORRECT** — 22 defs, 20 public (excl. `__init__` and `_run_fit`) |
| `recurrence_service_adapter.py` "referenced not piped" | **CORRECT** — `:236-237` verbatim; `train()` `:222-271` posts `{"dataset": {generator, params, split, …}}`, no arrays |

### 6.6 juniper-recurrence `routers/training.py`

All six line numbers in PROPOSALS §5.4's code block verified verbatim in
`juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/training.py` (mono-repo nesting;
there is **no** `src/` layout, so the bare path is correct only relative to the sub-package dir):

| line | actual | verdict |
| --- | --- | --- |
| 47 | `    try:` (4-space) — pairs with `    finally:` at `:104`, no `except` | **CORRECT** |
| 48 | `        try:` (8-space) | **CORRECT** |
| 58 | `        except (JuniperDataClientError, ValueError) as exc:` | **CORRECT** |
| 66 | `        try:` (8-space) | **CORRECT** |
| 81 | `        except ValueError as exc:` | **CORRECT** |
| 91 | `        result = lifecycle.run(sequence.X, sequence.y, **sequence.fit_kwargs())` | **CORRECT** |

"Uncaught 500" **CONFIRMED**: `juniper_recurrence` registers zero exception handlers; service-core's
`create_app` registers none (checked in **both** the repo source at 0.7.0 **and** the installed 0.4.0
copies in all three conda envs); no middleware catches `ValueError`; `TrainingLifecycle.run`
(`lifecycle/sync.py:72`) is a bare delegator.

### 6.7 juniper-data

| claim | verdict |
| --- | --- |
| `api/routes/generators.py:44` = `GENERATOR_REGISTRY` | **CORRECT** (AST lineno 44) |
| 16 generators | **CORRECT** (11 classification, 5 regression) |
| canopy `DATASET_TYPES` seeds 6 | **CORRECT** (`model_registry.py:132-150`) |
| six carry `time_unit`; five are rank-3 regression canopy never shows | **CORRECT** (`generators.py:118,126,134,142,150,158`) |
| `pyproject.toml:51` = `"yfinance>=0.2.40"` inside the `equities` extra (opened `:48`) | **CORRECT** |
| `yfinance` absent from `requirements.lock` | **CORRECT** (`grep` exits 1) |
| Dockerfile comment `--extra api --extra observability --extra mnist` | **CORRECT** — `Dockerfile:20`, exact flag match; cross-checked against `lockfile-update.yml:143-146` and `ci.yml:642-645` |
| `core/models.py:109-128` = `GeneratorInfo`, omits `task_type` | **CORRECT** — exact range (`:109` class, `:128` last field) |
| §6.3: "local conda (`JuniperData`) \| 1.4.1 installed" | **CONFIRMED** — `conda run -n JuniperData python -c "import yfinance"` → `1.4.1` |

### 6.8 Canopy structural claims from §1.2 / X1 / X2

| claim | verdict |
| --- | --- |
| exactly **175** registered callbacks (`len(app.callback_map)`) | **CONFIRMED — 175** |
| sole writer of `nn-dataset-type-dropdown.value` | **CONFIRMED** — exactly one `callback_map` key, `fn=gate_dataset_options` |
| sole writer of `model-selection-store.data` | **CONFIRMED** — exactly one key, `fn=select_model` |
| no clientside callback on either id | **CONFIRMED** |
| no `dcc.Location` / `dcc.Link` anywhere | **CONFIRMED** — 0 and 0 across all 1162 components |
| zero hits for the ids across all six `assets/*.js` | **CONFIRMED** — 6 files, 0 hits |
| `demo_mode.py` contains "model" zero times | **CONFIRMED** — `grep -c model` → 0 |
| `Output("restart-ds-type", "options")` exists nowhere (X2) | **CONFIRMED** — only `.value` at `:5268`; reads at `:5315` (Input) and `:5366` (State → `execute_restart` at `:5381`) |
| zero `aria-*` attributes in `dashboard_manager.py` (Y7) | **CONFIRMED** — 0 |
| X1: `_swap_backend` no-ops when `recurrence_service_url` unset | **CONFIRMED** — `main.py:3659-3671` `_selection_targets_recurrence` returns False on falsy URL; pinned at `test_d8_d11_phase4_truth_up.py:71` |
| X1: "The UI reads neither field" | **CONFIRMED** — `grep swapped src/frontend/` → 0 hits; `_model_summary_text` (`:2932`) reads only `nn_model` + `status` |
| `_fetch_generators` calls live HTTP and degrades to `[]` (fail-open) | **CONFIRMED** — `:2713-2735`, `except … generators = []` |
| DESIGN §4.7: `_update_button_appearance_handler` keys Start on status only, **no dataset input** | **CONFIRMED** — the callback's only Inputs are `button-states.data` (`:4472`) and `model-selection-store.data` (`:4478`); `:7206` `if not model_is_trainable(model_key)` |
| PROPOSALS §7 table: F1 changes **0 existing assertions** | **CONFIRMED plausible** — **zero** test files reference `nn-dataset-type-dropdown` (`grep -rl … src/tests/` → 0), no test asserts `clearable` on it, and the only two layout snapshots (`snapshots/dataset_plotter.txt`, `snapshots/metrics_panel.txt`) do not contain the sidebar dropdown |
| DESIGN §4.1 traversal: clearing does not re-fire the gate | **CONFIRMED** — the gate's Inputs are `model-selection-store.data` (`:2607`) and `params-init-interval.n_intervals` (`:2608`); the dataset is `State` (`:2609`). With `current_value=None` and `enabled=["equities_seq"]`, `:2704`'s test fails and `:2706` returns `enabled[0]` |

### 6.9 E2E claims

| claim | verdict |
| --- | --- |
| journey W8 at `E2E-CLICK-BY-CLICK-TEST-MATRIX.md:944` | **CORRECT** — `:944` is exactly `### W8 — Model switch cascor ⇄ recurrence  [FA-3]` |
| "step 2 asserts the Select is disabled, step 5 clicks it" | **CORRECT** — step 2 (`:953`) "incompatible rows show the reason and a **disabled** Select"; step 5 (`:956`) "Click the `{"type":"model-select-btn","index":"recurrence"}` Select" |
| "W8 was never executed" | **CORRECT** — `W8` appears exactly **once** in the 4,884-line evidence document, at `:1756`, and only to record the block |
| N-A blocking at `E2E-VALIDATION-EVIDENCE.md:1756` | **line CORRECT** — "W7 / W8 and every recurrence-dependent row are BLOCKED until the isolated leg is restored on 8212" |
| "…on the recurrence service being on the **wrong port**" | **COMPRESSED** — the recorded cause (`:1749-1754`) is that the relocated 8212 leg **exited**, leaving canopy pointed at a dead port; and `TEST-MATRIX.md:946-948` gives a *different* primary reason ("requires … the `--with-recurrence` fourth leg … every W8 step is `N-A (no recurrence service)`") |

---

## 7. NUMBERS — independent re-derivation

Run: `conda run -n JuniperCanopy1 python scratchpad/indep_bfs.py` (independent entry point: the model
gate is read off the **real rendered** `_build_model_selection_table` buttons, not a re-implementation
of `model_reason`).

```
INDEPENDENT RE-DERIVATION (round-2 auditor)
  MODELS                     : ['cascor', 'recurrence']
  DATASET_TYPES              : ['spirals','xor','mnist','circles','moons','equities_seq']
  start                      : ('cascor', 'spirals')
  total pairs                : 12   [doc claims 12]          CONFIRMED
  compatible                 : 6    [doc claims 6]           CONFIRMED
  reachable                  : 5    [doc claims 5]           CONFIRMED
  edges                      : 20   [doc claims 20]          CONFIRMED
  pick-model edges           : 0    [doc claims 0]           CONFIRMED
  compatible-but-unreachable : [('recurrence','equities_seq')]  CONFIRMED
  (recurrence,equities_seq) out-edges: dataset=[] model=[]   ABSORBING — CONFIRMED
```

Null-state claims (DESIGN §4.1 / PROPOSALS §7 item 1) — all **CONFIRMED** by execution:

```
_build_model_selection_table(None,'cascor')          -> [('cascor', False), ('recurrence', False)]
_dataset_model_hint_handler(None)                    -> ''
_resolve_oneshot_start_body_handler('one_shot',None) -> None
```

§5.1's S1–S5 simulation table re-run (`util/ad-hoc/2026-09-02_canopy_unary_guard_simulation.py`) —
**every cell CONFIRMED**:

| scenario | reachable | compatible | unreachable | reachable-but-INVALID |
| --- | --- | --- | --- | --- |
| S1 | 5 | 6 | `(recurrence, equities_seq)` | none |
| S2 | 6 | 6 | none | none |
| S3 | **10** | 6 | `(recurrence, equities_seq)` | **5** |
| S4 | 5 | 7 | 2 pairs | none |
| S5 | 7 | 7 | none | none |

Test count: `pytest src/tests/regression/{test_model_table,test_model_picker,test_model_select,
test_oneshot_start_body,test_d8_d11_phase4_truth_up}.py src/tests/unit/{test_model_registry,
test_dataset_schema}.py src/tests/unit/frontend/test_n7_dataset_panel.py` in `JuniperCanopy1`
→ **`129 passed in 9.35s`**. **CONFIRMED.**
Caveat: the documents say bare "**129 tests pass**" without naming the scope; the underlying source
(`reports/…/laneA2.md:19,222,234`) scopes it to "the eight selection-relevant files". Note
`test_recurrence_routes.py` — cited in §5.1 — is **not** among the eight.

Instruments and evidence:
- `util/ad-hoc/2026-09-02_canopy_selection_reachability.py` — **EXISTS** (worktree)
- `util/ad-hoc/2026-09-02_canopy_snap_and_null_state.py` — **EXISTS**
- `util/ad-hoc/2026-09-02_canopy_unary_guard_simulation.py` — **EXISTS**
- `reports/2026-09-02_canopy-selection-deadlock/` — **EXISTS**, **10 files** (laneA1–A3, laneB1–B3,
  proposal_P1–P4) matching "10 agent reports"

**Merge hazard**: all four instruments and the reports directory exist **only in this worktree** —
`ls /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/ | grep 2026-09-02` on the primary
checkout returns nothing, and `juniper-ml/reports/2026-09-02_canopy-selection-deadlock` does not
exist. The link validator does not catch these (they are inline-code paths, not markdown links). If
the two documents land without the instruments and reports, **every** §11 reference and the §1.1 /
§5.1 instrument citations become dangling.

---

## 8. TOOL RUNS — exact commands and output

### 8.1 Documentation link validator — PASSED

```
$ cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/wondrous-spinning-piglet
$ juniper-check-doc-links \
    notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md \
    notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md \
    --cross-repo check
============================================================
Documentation Link Validation
============================================================
Cross-repo links: check (ecosystem root: /home/pcalnon/Development/python/Juniper)

Scanning 2 markdown files...
------------------------------------------------------------
All links valid across 2 files.
============================================================
PASSED: Documentation link validation
============================================================
exit 0
```

(binary: `/opt/miniforge3/envs/JuniperCascor1/bin/juniper-check-doc-links`)

All four referenced notes files exist at the cited paths:
`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` (367 lines),
`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` (1205),
`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (4884),
`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (168).

### 8.2 markdownlint — 5 violations (would fail the pre-commit hook)

Run read-only (the repo hook passes `--fix`, which would edit the files; not used here):

```
$ /home/pcalnon/.cache/pre-commit/repoft72ba_k/node_env-default/bin/markdownlint \
    --config ./.markdownlint.yaml \
    notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md \
    notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md

…SELECTION-DEADLOCK-PROPOSALS.md:106     MD040/fenced-code-language  Fenced code blocks should have a language specified [Context: "```"]
…SELECTION-DEADLOCK-PROPOSALS.md:267     MD040/fenced-code-language  Fenced code blocks should have a language specified [Context: "```"]
…SELECTION-DEADLOCK-PROPOSALS.md:307     MD040/fenced-code-language  Fenced code blocks should have a language specified [Context: "```"]
…SELECTION-DEADLOCK-PROPOSALS.md:341:513 MD013/line-length           Line length [Expected: 512; Actual: 634]
…SELECTION-REACHABILITY-DESIGN.md:77     MD040/fenced-code-language  Fenced code blocks should have a language specified [Context: "```"]
```

Neither MD040 nor MD013 is auto-fixable, so `--fix` will not clear these. PROPOSALS:341 is the §6.1
X1 table row.

(markdownlint-cli v0.42.0, the version pinned at `.pre-commit-config.yaml:226`.)

---

## 9. UNVERIFIED / NOT RE-DERIVED

- ~~Coverage figures~~ — **NOW MEASURED**, see §12 below. Three of five figures confirmed exact; the
  per-file number is on the wrong basis and "the gate is currently clean" is refuted on the gate's
  own basis.
- **Sizing** 50–80 src / 150–250 test / 75–125 + 230–370 / three PRs — a single-source Lane-B3
  estimate; no way to re-derive. Both documents attribute it. **UNVERIFIED, correctly attributed.**
- **"3 minimum (8 on the broad reading)"** existing-test delta for F2 (PROPOSALS §7 table) —
  **UNVERIFIED**.
- **"snapshots only display `dataset_type`"** (PROPOSALS §1.2) — `src/snapshots/` holds only
  `snapshot_history.jsonl`; the rendering code is elsewhere. **NOT RE-DERIVED.**
- **§9 "Canopy accepts TCP on 8050 but never responds"** — environment-dependent, not re-checked.
- **Y2–Y6, Y8** — single-source leads; the documents label them as such.
- **service-core version skew** (found incidentally): repo source is `0.7.0`
  (`juniper-service-core/juniper_service_core/_version.py:5`) while all three conda envs have
  **`0.4.0`** installed. Verified for the exception-handler question specifically (zero handlers in
  both). Any *other* service-core claim verified only against repo source may not describe what runs.

---

## 10. CLAIMS STATED AS FACT THAT THE DOCUMENTS ELSEWHERE MARK UNCERTAIN

Per the audit brief's item 4. The documents are, on the whole, **disciplined** about this — the
residual-uncertainty section (PROPOSALS §9) and the "leads, not facts" framing (§6.4) do real work.
The exceptions:

1. **`RecurrenceBackend.stage_dataset` blocking status.** PROPOSALS §5.5 records **unresolved
   dissent** (B1/B2 say live blocker, B3 says OVERSTATED) and §9 lists it as residual uncertainty;
   DESIGN §10 OQ-N1 correctly keeps it open. **But DESIGN §9** states flatly: *"Y1–Y8 (evaluation
   §6.4), **including the eight missing `RecurrenceBackend` methods** and the vacuous snapshot
   save/restore"* — asserting both the count and the fact in a "what this does not fix" list, with no
   hedge. The count is additionally wrong (§2.6 above).
2. **"5× larger loss".** PROPOSALS §5.3 grades this **OVERSTATED** and §6.2 retains B3's caveat
   ("a count, not a measured loss") — good. But **DESIGN §9** states: *"Ten unseeded generators,
   **five of them rank-3 regression datasets the LMU could train on**"*. "*could train on*" is the
   end-to-end usability claim that the evaluation explicitly declined to make. The compatible-per-
   predicate claim is verified; "could train on" is not.
3. **"129 tests pass"** (PROPOSALS §2.3) is stated bare; the scope ("the eight selection-relevant
   files") lives only in the underlying lane report, not in either document.
4. **"Six independent instruments agree"** (§1.1) vs "All four confirm" (§10) — see §5.4 above.
5. **PROPOSALS §7 item 1** asserts *"B1 verified all ten Python consumers **and both JS consumers**…"*
   as an established verification, in the ratified recommendation. It is not verifiable (§2.1).

---

## 11. RECOMMENDED MERGE GATE

Must fix (false authority — a reader following these learns something untrue):

1. `main.py:3993` → `:3994` (two places)
2. `_restage_dataset:5623` → `:5629-5631` (two places)
3. `:2836` → `:2846` (two places)
4. `:2896` → `:2893` (DESIGN §4.4)
5. Drop or correct "both JS consumers" (two places) — it contradicts §1.2
6. "the only three resolvers" → five, and add `dataset_type_options` / `dataset_default_params` to
   DESIGN §5's enabling-change list
7. "canopy reads it nowhere" → "canopy never reads it from juniper-data"
8. `_synthetic.py` → `_sequence.py:237,329`; "all five" → "three of five"
9. #393's timestamp (`15:41`, not `17:41`) and drop the same-minute implication
10. "11 sites" vs its own 12-item breakdown
11. The `G2`/`G3`/`G5` collision between the two documents
12. `§1756` → `:1756` in PROPOSALS §11

Should fix (imprecision that will mislead):

13. `f464272` framed as the parent (it is the grandparent; `442673e^` is `c2058be`)
14. `model-select-btn count: 4` — scope it
15. `13a5856` — scope `clearable=False` to `nn-dataset-type-dropdown`
16. "five weeks" → 38 days
17. "464-component layout" → "464 id-bearing components"
18. The two unmarked PR-body elisions/splices
19. §6.2's "regular Δt" reason (wrong for `irregular_sine`, `delay_product`)
20. `test_model_table.py:170` → `:171`
21. Y1's "eight" → nine (vs the common surface) / zero (vs `BackendProtocol`)
22. The five markdownlint violations
23. Bare `§5.6` references (naming-convention breach)
24. Land the instruments and `reports/2026-09-02_canopy-selection-deadlock/` in the same PR

---

## 12. COVERAGE — MEASURED (completed after the first pass)

Re-ran **laneB3's exact documented command**:

```
$ cd /home/pcalnon/Development/python/Juniper/juniper-canopy
$ conda run -n JuniperCanopy1 python -m pytest \
    -m "not requires_cascor and not requires_server and not slow" \
    src/tests/unit/ src/tests/regression/ \
    --cov=src --cov-report=json:…/cov.json -p no:randomly -q
…
Required test coverage of 80.0% reached. Total coverage: 96.06%
exit 0   (platform linux, python 3.13.13-final-0)
```

Then fed the JSON to **the actual gate** (`juniper_ci_tools.coverage_gap_mapper.load_coverage_json`,
`file_threshold=90.0`, `submodule_bar=95.0`, no `omit`) — the same entry point laneB3 says it used.

| figure | documents claim | measured | verdict |
| --- | --- | --- | --- |
| total | 96.06% | **96.06%** | **CONFIRMED exact** |
| `src/frontend` pooled | 96.34%, 10 files, 1965 stmts | **96.34%, 10 files, 1965 stmts** | **CONFIRMED exact** |
| slack to the 95% pooled bar | 27 | **27** | **CONFIRMED exact** |
| `dashboard_manager.py` stmts / missing | 1756 / 68 | **1756 / 68** | **CONFIRMED exact** |
| `dashboard_manager.py` percentage | **96.13%** | the gate reports **95.46%** | **MIXED BASIS** |
| headroom to the 90% file floor | ~119 statements | 119 — but on the statement basis | **right number, wrong basis** |
| "files below the 90% FILE floor: `[]` — gate currently clean" | clean | **`src/backend/state_sync.py` = 87.38%**, below the floor | **REFUTED on the gate's basis** |
| `src/frontend/components` pooled | 97.91% | **97.91%** | **CONFIRMED exact** |

### 12.1 The mechanism

`pyproject.toml:414` sets `[tool.coverage.run] branch = true`, so coverage.py's `percent_covered` is
**branch-inclusive**, and it also emits a separate `percent_statements_covered`. For
`dashboard_manager.py` the two differ materially:

```
percent_covered            : 95.46 %   (1688+477 covered of 1756+512)   <- what the gate reads
percent_statements_covered : 96.13 %   (1688 of 1756)                    <- what the documents quote
percent_branches_covered   : 93.16 %
excluded_lines             : 481
```

`parse_coverage_json` reads `summary["percent_covered"]` **per file** (branch-inclusive) but pools
sub-modules from `num_statements` / `covered_lines` (**statement-only**). So the pooled 96.34% is
exactly right and the per-file 96.13% is not the number the gate sees.

The documents also juxtapose two bases as if comparable: "the lane runs clean at **96.06%** total"
(branch-inclusive) next to "`dashboard_manager.py` sits at **96.13%**" (statement-only). Like for
like, the total is **97.17%** on the statement basis, or the file is **95.46%** on the branch basis.

### 12.2 What survives, and what does not

**The documents' actual argument is intact.** `dashboard_manager.py` at 95.46% is still far above the
90% file floor, so "the per-file 90% floor is *not* binding" **holds**; and the binding constraint is
still the `src/frontend` pooled 95% bar at 96.34% with **27** statements of slack — **confirmed to the
digit**. §8 of PROPOSALS and §6 of DESIGN reach the right conclusion.

**What does not survive**: the specific per-file figure (96.13% → 95.46%), the headroom arithmetic's
basis, and the assertion that the gate is currently clean. On the gate's own basis exactly one file —
`src/backend/state_sync.py`, 87.38% branch-inclusive / 93.83% statement-only, 81 stmts, 5 missing —
sits **below the 90% floor**. It is untouched by this remediation, so it does not block the fix, but
"Measured, not assumed: the lane runs clean" (DESIGN §6) and laneB3's
"files below the 90 % FILE floor: `[]` <- gate currently clean" are **false as written**.

Note also `excluded_lines: 481` on `dashboard_manager.py` — over a fifth of the file is removed from
measurement by `[tool.coverage.report] exclude_lines` (`pyproject.toml:423-433`) before any
percentage is computed. Not a claim under audit, but it bounds what the 95–96% figure means.
