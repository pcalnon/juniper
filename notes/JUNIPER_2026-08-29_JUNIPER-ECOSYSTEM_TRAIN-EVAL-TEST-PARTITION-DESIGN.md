# Train / Validation / Test partition — design of record

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (juniper-data → juniper-data-client → juniper-cascor)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-09-01
**Status**: DESIGN — decisions 1–5 settled 2026-08-29; **6–8 settled 2026-08-31 (§9.2)**;
**9 settled 2026-09-01 (§9.3.2): P-1b, per-partition name-keyed seed substreams**, after P-1a was
measured BLOCKED (§9.3.1). Prefix stability is abandoned as unobtainable.
**Two items now gate Chunk 3.** (1) P-1b introduces a leak P-1a did not have — independently
generated partitions can share grid positions, producing **byte-identical train/val rows at
`noise=0`, which is reachable config** (§9.3.2); three guards are specified, **none ruled**.
(2) **P-1b applies only to the SYNTHESISED generator class** (§9.3.3) — 5 of 16 generators draw from
a finite pool, and for the ordered ones (`equities`) applying P-1b would be a **regression**, not an
improvement. Decisions 8 and 9 both need that scope limit read before implementation.
**Tracks**: [cascor#582](https://github.com/pcalnon/juniper-cascor/issues/582) (tier parity),
[cascor#578](https://github.com/pcalnon/juniper-cascor/issues/578) (baseline-tier decision),
[cascor#530](https://github.com/pcalnon/juniper-cascor/issues/530) (no seed field)
**Evidence**: `reports/tensor-hash-probe-2026-08-28/`, measured at cascor `67d7ea35`

---

## 1. Summary

The service tier promotes the dataset's `X_test`/`y_test` to in-loop validation, and **also reports
its final evaluation metrics from that same partition**. Selection and reporting therefore share
one set of rows. The direct CLI passes no validation data at all, so it neither early-stops nor
reports a held-out score.

The natural reading — "one arm is wrong, bend it to match the other" — is the wrong frame. Both
arms are downstream of a **data contract that defines only two partitions where the training loop
needs three**. `X_test` is being used as an in-loop signal because there is no `X_val` to use.
The fix is to finish the partition design, not to pick an arm.

**Decision**: adopt a three-way `train` / `validation` / `test` split as the ecosystem data
contract, with `validation` consumed in-loop and `test` touched exactly once after training
completes. §6 records the options and the owner's decisions; §7 the consequences; §9 the decision
table; **§10 settles the naming, and it is not `eval`** — see there before writing any code.

---

## 2. What was measured

One cell (`e-n-profile-cap4`, `seed_policy: fixed`, seed 42, cap 4), both arms at cascor
`67d7ea35`, the CLI leg handed the exact cell the service leg materialised
(`config_sha256 a4fc5746…`). A probe at `fit()` — the single entry point both arms reach — hashed
its four tensor arguments before the initial output pass.

| tensor | CLI | service |
| --- | --- | --- |
| `x_train` | `(800,2)` `raw=341d9dd0cb9ed0ea` | **identical** |
| `y_train` | `(800,2)` `raw=8d92cbeba78a414e` | **identical** |
| `x_val` | `None` | `(200,2)` `raw=e0ecd7ffe171d447` |
| `y_val` | `None` | `(200,2)` `raw=22cd2024464128c0` |

1000 samples → 800 train / 200 test. The service passes those 200 test rows as `x_val`/`y_val`.
The CLI passes nothing.

**The reported metrics come from the same 200 rows.** `artifacts/results/metrics_final.json` from
the service run:

```json
"eval_metrics": { "n_samples": 200, "split": "validation", "enabled": true, "n_classes": 2 },
"f1": 0.56995699569957, "precision": 0.5705128205128205,
"recall": 0.5704281712685074, "roc_auc": 0.6280512204881953,
"val_accuracy": 0.57, "val_loss": 0.24778318405151367
```

There is no separate test metric in the artifact at all. `f1`, `precision`, `recall` and `roc_auc`
— the numbers a reader would take as the run's held-out performance — are computed on the
partition that drove early stopping, patience and `Best Val Loss`.

## 3. The code says so in its own words

In `src/api/lifecycle/manager.py` (cascor `67d7ea35`), the block guarded by `has_x_test` /
`has_y_test` builds the validation tensors directly from the test keys:

```python
new_val_x = torch.tensor(arrays["X_test"], dtype=torch.float32)
new_val_y = torch.tensor(arrays["y_test"], dtype=torch.float32)
```

and its own error strings call them **validation** arrays while reading **test** keys:

> `"juniper-data artifact validation arrays must be 2-D; got X_test.ndim=…"`
> `"juniper-data artifact validation sample count mismatch: X_test=… y_test=…"`

The method docstring records the intent plainly — validation comes from *"dataset's
`X_test`/`y_test`) when present, **else the training split**"*.

That is the tell. The code is reaching for a validation partition, finding only `X_test` in the
contract, and using it; and where even that is absent it falls back to validating on the training
split — a second, worse leak. This is an unfinished design, not a deliberate choice.

## 4. Why this matters

**A. The reported service metrics are optimistically biased.** Early stopping selects the epoch
that minimises loss on exactly the rows later reported as the score. The magnitude is unmeasured
(§8 proposes measuring it), but the direction is not in doubt.

**B. The two tiers are not comparable, and #578 cannot be answered while that holds.** A P3
threshold calibrated on the service's selected-on metric and applied to a CLI run that never
early-stops is comparing different quantities. The CLI's own log says as much:
`validate_training: Iteration 0 (no val data)`.

**C. The CLI has no early stopping at all.** It trains to budget. That is not a leak but it is not
a baseline either — the two arms differ in *regularisation*, not just in reporting.

**D. Any corpus carrying these metrics inherits the bias** — snapshot metadata, aggregate CSVs, and
any downstream analysis that read `f1`/`roc_auc` as held-out performance.

**Scope limit.** This is *not* the whole cross-arm gap. The tensor probe showed both arms are
byte-identical through the initial output pass, and [cascor#572](https://github.com/pcalnon/juniper-cascor/issues/572)
was separately confirmed 2026-08-29 as a live defect: `_seed_random_generator`'s first call site
draws its roll count from the global `random` module before that module is re-seeded, so numpy's
position differs between a fresh CLI process and a long-lived service worker. Fixing partitions
will not fix that, and vice versa. They are independent and both real.

## 5. The design

Three partitions, three distinct jobs:

| partition | used for | touched |
| --- | --- | --- |
| `train` | gradient updates; candidate correlation | every epoch |
| `validation` | early stopping, patience, best-checkpoint selection, LR schedules, any in-loop decision | every validation interval |
| `test` | the final reported score | **exactly once**, after training completes |

The invariant that makes it worth doing: **no quantity computed on `test` may influence any
decision made during training.** If a number is allowed to change what the run does, it is
`validation` by definition, whatever it is named.

Both arms consume the same three partitions, so the tiers become comparable by construction and
#578 reduces to a fixed-overhead question rather than a semantics question.

## 6. Options considered — **DECIDED 2026-08-29: O-1**

> **Owner decision.** juniper-data owns the split (O-1). cascor consumes `X_val` when present and
> may fall back to `X_test` **only** behind an explicit run-with-warnings switch (§6.1). For legacy
> datasets whose metadata carries sufficient provenance / construction detail, juniper-data
> compensates rather than refusing — see §6.2.
>
> The sizing model is **not** either option's "carve up the existing N". See §6.3: the requested
> training count is honoured literally and the other partitions are generated as *additional*
> points. That materially changes §7, because `train` no longer shrinks.

The three options as originally analysed:

### O-1 — juniper-data emits the third partition (recommended)

Add `X_val`/`y_val` to the NPZ contract alongside `X_train`/`y_train`, `X_test`/`y_test`,
`X_full`/`y_full`. The generator owns the split, so every consumer gets the same partitioning for a
given `dataset_id` and the split is reproducible from the dataset seed.

*For*: one place to change; content-addressed datasets keep their meaning; consumers get it for
free; the split is recorded in the artifact rather than re-derived per consumer.
*Against*: a contract change across the ecosystem, and every existing cached artifact lacks the
keys — needs the compatibility rule below.

### O-2 — cascor sub-splits `train` locally

cascor carves `eval` out of `X_train` at load time.

*For*: no contract change; lands in one repo.
*Against*: the split is re-derived per consumer and per run, so it depends on cascor's RNG — which
[#572](https://github.com/pcalnon/juniper-cascor/issues/572) has just shown is not a function of
the seed. Two consumers of the same `dataset_id` would disagree about what `eval` is. It also
shrinks `train` silently relative to every existing baseline.

### O-3 — document the asymmetry, change nothing

*For*: free.
*Against*: leaves the reported metrics selected-on and leaves #578 permanently unanswerable. Not
recommended, and listed only so the do-nothing cost is explicit.

**Decision: O-1.** O-2's mechanism is explicitly *not* adopted even as a fallback — §6.2 replaces it
with generation/re-partitioning performed by juniper-data, so the split is never re-derived
per-consumer from cascor's RNG.

### 6.1 Consumer contract (cascor) — fail loudly, never silently guess

1. **`X_val` present** → use it for in-loop validation. `X_test` is reserved for the final score
   and must not be read during training.
2. **`X_val` absent, `X_test` present** → **do not proceed by default.** Present a gated choice
   (§6.4). Proceeding is permitted only behind an explicit run-with-warnings switch, and then the
   run is marked: a `validation_warnings` manifest entry, a warning visible on every dashboard tab
   for the run's lifetime, and a caveat attached to the reported metrics themselves.
3. **Neither present** → refuse. The current *"else the training split"* fallback is removed
   outright; it produces a number that looks like validation and is not.

The run manifest already carries `validation_warnings` (juniper-ml#1159 uses it for the
`max_epochs` / `output_epochs` footgun), so (2) has an existing channel.

### 6.2 Legacy datasets — juniper-data compensates

Where a legacy artifact lacks `X_val` **and** its metadata carries sufficient provenance and
set-construction detail, juniper-data repairs it rather than the consumer coping. Two mechanisms,
in preference order:

1. **Generate the shortfall.** Use the recorded generator and its specs to synthesise the additional
   `eval` and/or `test` points needed to satisfy the configured partition breakdown. Preferred,
   because it leaves the existing `train` rows untouched — no existing training baseline moves.
2. **Re-partition.** Combine the available partitions and re-split by the configured percentages.
   Use only when (1) is impossible. This *does* move `train`, so any run against a re-partitioned
   legacy dataset is not comparable to its own history and must be recorded as such.

Both require the metadata to actually identify the generator and its parameters. Where it does not —
no generator, no generator specs, or a dataset type not amenable to synthesis (real-world data,
notably the `e-h-real-data` suites) — neither mechanism applies and §6.4's gate is the only path.

### 6.3 Sizing model — honour the requested train count, generate the rest

The default is **not** to carve `eval`/`test` out of the requested N:

- A request for a 1000-point training set yields a **1000-point training set**.
- `eval` and `test` are built from **additional** points drawn from the same generator, sized by the
  configured breakdown.
- Percentages are therefore expressed **relative to train**, which starts at 100 %. A default
  breakdown of `train/eval/test = 100/40/30` at N=1000 yields **1000 / 400 / 300**.

Normalised percentages, if a consumer needs them summing to 100, are derived rather than configured:
with 1000 + 400 + 300 = 1700 total, `train = 1000/1700 = 58.8 %`, `eval = 23.5 %`,
`test = 17.6 %` — rounded to **59 / 23 / 18**.

Percentages may be adjusted away from the default — shifting to a conventional carve-up of a fixed N
— when any of these holds: an explicit CLI switch, environment variable or config setting; the
dataset has no generator or no generator specs; or the dataset type is not amenable to synthetic
generation.

**Why this matters more than it looks.** Carving 1000 into 600/200/200 would shrink every training
set in the corpus and invalidate every existing baseline by construction. Generating additional
points keeps `train` identical to what it is today, so the only behavioural change is that early
stopping now has a partition to consult. That converts §7's "existing baselines shift" from a
certainty into a much narrower question.

**V-1 MEASURED 2026-08-30 — the baseline-preservation benefit does NOT hold. Do not claim it.**

The question was whether generating N+M points yields the *same* first N rows as generating N.
Measured across all six cascor-relevant generators with `seed=42` held fixed
(`util/ad-hoc/2026-08-30_v1_generator_prefix_check.py`):

| generator | `X_full` | `X_train` |
| --- | --- | --- |
| spiral | DIFFERS | **DIFFERS** |
| moon | DIFFERS | **DIFFERS** |
| xor | DIFFERS | **DIFFERS** |
| circles | DIFFERS | **DIFFERS** |
| checkerboard | DIFFERS | **DIFFERS** |
| gaussian | DIFFERS | **DIFFERS** |

**6/6 differ, on both keys.** Two mechanisms, and the second is the more general one:

1. Nine of sixteen generators call `shuffle_and_split(X, y, …)` over the **full** generated set
   before splitting, so a permutation over 1,700 rows shares nothing with one over 1,000.
2. `X_full` differs too — so it is not only the shuffle. The raw generation itself is not
   prefix-stable: a larger N consumes the RNG stream differently (vectorised draws are sized to N),
   so even the pre-split data changes.

**The precise consequence — keep these two apart:**

- *"`train` does not shrink"* — **TRUE**, and unaffected. Ask for 1,000 training points and you get
  1,000. The COUNT is preserved.
- *"existing baselines are preserved"* — **FALSE**. The CONTENT changes: different rows, same count.

So §6.3's stated advantage over a 600/200/200 carve-up — that it avoids invalidating the corpus —
**evaporates**. Under either sizing model every existing baseline moves, and a re-baseline is
required either way. The choice between them must now be made on other grounds (dataset economy,
whether a 1,000-row training set is wanted at all), not on baseline preservation.

This does **not** overturn decision 2 — honouring the requested training count is still a defensible
default, and is still what a caller asking for 1,000 points expects. It removes the *reason* that
was given for it, and it re-prices decision 4 (re-measure pre-change results) from "narrow" back to
"required".

Instrument note: the first run of this check reported `xor` and `gaussian` as PREFIX-STABLE. That
was **vacuous** — their size parameters are `n_points_per_quadrant` and `n_samples_per_class`, the
generic `n_samples` kwarg was silently ignored by the params model, and both runs came out at the
default size, so the comparison was between two identical generations. The script now refuses to
report stability when the two runs produced the same row count.

### 6.4 The gate when `X_val` is missing

Explain the problem, then **refuse to continue until the user chooses**:

| # | option | effect |
| --- | --- | --- |
| 0 | **Fill synthetically** | Apply §6.2 where possible — generate the missing partition(s) and proceed cleanly. |
| 1 | **Continue with recorded warning** | Proceed on the `X_test`-as-eval fallback. Warning visible on all tabs for the run's lifetime; metrics carry an explicit caveat; `validation_warnings` recorded on the manifest. |
| 2 | **Back to dataset selection** | Return control to the dataset page (top tab menu) and its left context menu, config intact. |
| 3 | **Cancel the run** | Abort with the clean-up / close-out appropriate to the current operating mode. |

**Headless runs get a safe default: refuse and shut down.** That default is overridden only by an
explicit run-with-warnings or add-synthetic-data switch — as a CLI flag, an environment variable, or
a config entry. A headless run must never silently take option 1; that is precisely how the current
situation went unnoticed.

## 7. Consequences to plan for

- **Ratio: SETTLED (§6.3).** `train` does **not** shrink — the requested training count is honoured
  literally and `eval`/`test` are generated as additional points. This removes the largest source of
  baseline invalidation before it happens.
- **Existing baselines still shift, but for one reason instead of two.** `train` is preserved
  in COUNT but **not in content** (V-1, measured 2026-08-30 — see §6.3), so the rows move under
  either sizing model and a re-baseline is required regardless. Beyond that the change is
  behavioural: the service already early-stopped and
  will now do so against a partition it does not report, and the CLI gains early stopping it never
  had (§9 decision 5). The T6 re-baseline, the P3 thresholds and the attribution corpora were all
  measured under the old semantics and none of them are wrong — they answer a different question.
- **Pre-change results: re-measure, and keep the originals annotated** (owner decision 4). Preference
  is a genuine re-measurement rather than a paper annotation; the old numbers are retained with an
  annotation recording which semantics produced them, so nothing is silently discarded and nothing is
  silently compared across the boundary.
- **Reported metrics change meaning, not just value.** After the change, `f1`/`roc_auc` become
  genuinely held-out. Comparing a post-change number to a pre-change one is a category error and
  should be blocked by provenance, not by convention.
- **Snapshot metadata** carrying metrics should record which partition each metric came from, so a
  future reader can tell a selected-on number from a held-out one without reading this document.
- **The CLI gains early stopping** (owner decision 5), which changes CLI results — a CLI run that
  previously trained to budget may now stop earlier. This is the intended fix for the tier
  asymmetry, but it *is* a behavioural change to the arm that was previously unbiased-but-
  unregularised, and it should be measured, not assumed benign.

## 8. Proposed measurement before the change — **DONE 2026-08-29, and it did not find a resolvable effect**

> **Result**: mean optimism **+0.0088**, sd 0.0323, n=8 dataset seeds at cap 4; 95 % CI
> **[-0.0136, +0.0311] includes zero**. Early stopping genuinely engaged, so the measurement is not
> vacuous — but at this scale the bias is not distinguishable from noise, and the single-cell figure
> (+0.0400) was the second-highest of eight. **The motivation for this design is methodological, not
> a measured inflation.** Full result and caveats:
> [`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md) §2.


Cheap and worth doing first: on the current build, run one cell and compute the final metric on
**both** the promoted `X_test` (as today) and a freshly held-out slice never seen by early
stopping. The gap is the bias this design removes. One cell, both arms, no new tooling beyond a
metrics hook — the same harness used for the tensor probe. Without it the design ships with an
unquantified motivation, and §7's "existing baselines shift" has no size attached.

## 9. Owner decisions — SETTLED 2026-08-29

| # | question | **decision** |
| --- | --- | --- |
| 1 | Who owns the split? | **juniper-data (O-1).** cascor consumes; it may fall back to `X_test` only behind an explicit switch (§6.1). Legacy gaps are repaired by juniper-data via generation or re-partitioning (§6.2), **not** by cascor sub-splitting. |
| 2 | Split ratio; does `train` shrink? | **`train` does not shrink.** The requested training count is honoured literally; `eval`/`test` are generated as *additional* points. Percentages are relative to train-at-100 % (default `100/40/30` → 1000/400/300). Normalised form is derived, not configured (59/23/18). Adjustable by switch/env/config, or forced when no generator/specs exist or the data is not synthesisable (§6.3). |
| 3 | Legacy artifacts without the eval partition | **Gated choice, never a silent default** (§6.4): fill synthetically / continue with recorded warning / back to dataset config / cancel. **Headless default is refuse-and-shut-down**, overridable only by an explicit run-with-warnings or add-synthetic-data switch. |
| 4 | Pre-change results | **Re-measure preferentially, retain the originals annotated.** Not retired, not merely annotated — the annotation records which semantics produced them so nothing is silently compared across the boundary. |
| 5 | Should the CLI early-stop? | **Yes.** There should be no fundamental structural or methodological difference between the CLI and canopy arms. The CLI gains `eval` and early stopping. |

### 9.1 Still open — carried forward

- **N-1 — the partition's NAME is not settled.** This document says `X_val` throughout because that
  is how the question was framed, but `eval` may be the wrong token: it names an *action* in most ML
  APIs, not a partition. Under external validation as of 2026-08-29; see §10.1. **Do not treat
  `X_val` as decided.** Whatever name wins, the contract key, the config vocabulary and the
  consumer code should all use it consistently.
- **V-1 — RESOLVED 2026-08-30: NO.** All six cascor-relevant generators produce different
  rows when asked for N+M vs N at the same seed, on both `X_full` and `X_train`. The COUNT
  is preserved; the CONTENT is not, so baseline preservation was never available under this
  sizing model. See §6.3 for the table, the two mechanisms, and what it re-prices.
- **V-2 — measure the leak before removing it** (§8). Still the right first step, and now doubly so:
  it is the only way to size what decision 4's re-measurement will change.
- **V-3 — CLI early stopping changes CLI results.** Decision 5 is correct for parity but is a
  behavioural change to the arm that was previously unregularised. Measure it rather than assuming
  it is benign.

### 9.2 Owner decisions — SETTLED 2026-08-31 (plan §3's D-1 and D-2)

Ruled after the implementation plan's D-1 was **re-posed**: the plan justified the question by
claiming `full == train + test` is *"already violated by every shuffled tabular generator"*, which is
false. Both normative clauses (`USER_MANUAL.md:367`, `JUNIPER_DATA_API.md:1001`) are **length**
identities, which shuffling cannot violate, and
`juniper_data/tests/integration/test_e2e_workflow.py:299-301` asserts
`n_train + n_test == n_full` and passes today. What *is* true: the **array-equality** form fails for
shuffled tabular generators, and the length clause is violable **via request params**, since the two
cross-field validators reject only `train_ratio + test_ratio > 1.0`.

| # | question | **decision** |
| --- | --- | --- |
| 6 | **D-1** — what does `X_full` mean under three partitions? | **`X_full` is ASSEMBLED, not split.** The three subsets are generated first, each given its appropriate shuffling and normalisation, and `X_full` is then produced by concatenating them. This **inverts today's data flow** (generate `X_full` → `shuffle_and_split`) and makes the identity true *by construction* — in the array-equality form, not merely by length. It is stronger than the plan's option (a), which would only have made the length clause normative. Rationale of record: with deterministic pseudorandomness configured properly and a shared seed, this permits **dataset comparison across snapshots**. |
| 7 | **Normalisation fit scope** (sub-question of D-1) | **Fit on `train` only; apply those statistics unchanged to `val` and `test`.** No quantity derived from the reported partition may reach the training data — the same invariant §5 states for the reported score, applied to the scaler. **Consequence to state in the contract: `X_full` is deliberately NOT uniformly normalised**, because it is a concatenation of three subsets scaled by train's statistics rather than a uniformly-scaled array. Any consumer that treats `X_full` as a homogeneous array must be checked (§7). |
| 8 | **D-2** — how is additive sizing implemented? | **Dataset-level row counts.** The ratios denote absolute rows of the realised dataset, identically for every generator regardless of its native size knob (`n_points_per_spiral`, `n_points_per_quadrant`, `n_samples_per_class`, `n_samples`). `n_points_per_spiral=500, n_spirals=2` with `100/40/30` means `n_train=1000, n_val=400, n_test=300` — 1700 rows total. This resolves the plan's open question *"what '40 % of train' means for a per-spiral knob"*: it means rows, never per-spiral units. |
| 9 | **P-1** — how is cross-snapshot comparability obtained? | **P-1b: per-partition, NAME-KEYED seed substreams** (§9.3.2). Prefix stability (P-1a) is abandoned as unobtainable — §9.3.1 measured it blocked, partly for a semantic reason rather than a cost one. Keyed by partition NAME, not by `spawn()` position, so adding or reordering a partition cannot move another's stream. **Introduces one leak that must be guarded before Chunk 3 ships** — see §9.3.2. |

### 9.3 Derived requirement — PREFIX STABILITY (new, opened 2026-08-31)

**D-1's stated rationale is not achievable under D-2 without a further change to the generators, and
this is measured, not predicted.**

D-1 wants a shared seed to permit dataset comparison across snapshots. D-2 makes the request for a
third partition an ask for **N + M rows instead of N**. V-1 measured exactly that case: **all six
cascor-relevant generators return different rows for N+M vs N at the same seed**, on both `X_full`
and `X_train` — the count is preserved, the content is not (§6.3; instrument
`util/ad-hoc/2026-08-30_v1_generator_prefix_check.py`, ml#1492).

So under decisions 6 and 8 as ruled, adding the third partition **moves the training rows of every
existing baseline**, and two snapshots taken either side of the change are not comparable *even on
`train`* — which is the property D-1 was ruled in order to obtain.

Two ways to close it:

- **P-1a — prefix-stable generation.** Guarantee the first N rows are invariant to the requested
  total, so `generate(N+M)[:N] == generate(N)`. Would preserve the existing corpus.
- **P-1b — per-partition seed streams.** Derive each partition from an independent, named substream
  (e.g. `seed` → `seed_train` / `seed_val` / `seed_test`) so adding a partition cannot perturb the
  others. Does not preserve the existing corpus, but makes the invariant structural rather than a
  property each generator must be individually audited for.

#### 9.3.1 P-1a is BLOCKED — measured 2026-09-01

V-1 established *that* the generators are not prefix-stable. It did not establish *why*, and §6.3's
stated mechanism — *"vectorised draws are sized to N, so a larger N consumes the RNG stream
differently"* — turns out to be **not quite right**, in a way that changes the ruling.

Instrument: `util/ad-hoc/2026-09-01_prefix_stability_mechanism.py` (seven probes, each falsifiable
alone; `small=500 large=850 seed=42`).

| probe | result | what it isolates |
| --- | --- | --- |
| Q1 `normal(size=N)` prefix | **STABLE** | numpy itself |
| Q1b `random(size=N)` prefix | **STABLE** | numpy itself |
| Q2 one spiral arm, fresh rng | DIFFERS | per-stratum generation, layout excluded |
| Q3 arm 1 under shared rng | DIFFERS | cross-stratum RNG coupling |
| Q4 `X_full` under vstack | DIFFERS | stratified layout |
| Q5 spiral `legacy_cascor` (pure RNG) | DIFFERS | **refuted** the "RNG paths are fine" guess |
| Q6 bare `np.linspace` | DIFFERS | **mechanism A**, no juniper-data code involved |
| Q7 2nd of two N-sized draws | DIFFERS | **mechanism B**, no juniper-data code involved |

**numpy is not the problem** (Q1/Q1b). Two independent mechanisms are, and both bite:

- **Mechanism A — parametric-curve sampling.** `np.linspace(0, r, N)`'s spacing is a function of N,
  so a larger N **resamples the whole curve more densely** rather than extending it. `spiral`'s
  default `modern` path is built on it (`generator.py:138-139`), as is `moon`
  (`generator.py:81,86`). **Not fixable without redefining the dataset**: making
  `arm(N+M)[:N] == arm(N)` requires fixed-density sampling, so the extra points *extend* the curve —
  a longer spiral, i.e. a different dataset, not the same one with more rows.
  **Scope: 2 of 17 generators.** `gaussian`'s `linspace` is over `n_classes`
  (`generator.py:119`), not the point count, so A does not apply to it.
- **Mechanism B — sequential multi-draw offset.** A generator making *k* draws each sized N has
  draw #2 begin at stream position N, so changing N moves it — draw #1 is prefix-stable, draw #2 is
  not. This is why spiral's *pure-RNG* `legacy_cascor` path also differs (Q5): it draws distance,
  then x-noise, then y-noise off one rng. `gaussian` is hit the same way — a per-class
  `standard_normal` off a shared rng (`generator.py:89`) plus a whole-array noise draw (`:95`).
  Fixable in principle (per-draw substreams, or one max-sized draw), but that is **surgery on every
  generator's draw structure**.

**Ruling implication: P-1a is not merely expensive, it is partly semantic.** Mechanism B is a cost;
mechanism A means that for `spiral` and `moon` *"the same dataset with more rows"* is not a thing
that exists. **P-1b sidesteps both**, because each partition is generated at its own size and never
claims to be a prefix of another.

**Recommended: P-1b.** It does not preserve the existing corpus — but per V-1, **nothing does**, so
that was never a live advantage. Decision 4 (re-measure) stands regardless, as §9.1's V-1 entry
already records.

**What this evidence does not cover.** Only `spiral` was probed in situ (Q2–Q5); `moon` and
`gaussian` were read from source, not measured. The mechanism-A/B isolations (Q6/Q7) are
generator-independent and hold regardless. The other 14 generators were not classified.

#### 9.3.2 P-1b ADOPTED — owner ruling 2026-09-01, and the hazard it introduces

**Decision 9: P-1b.** Each partition is drawn from its own named seed substream. Prefix stability is
abandoned as unobtainable (§9.3.1); the corpus is not preserved, and decision 4's re-measure carries
that, as it already had to.

**The scheme.** Derive each partition's stream from the dataset seed **by partition NAME**, not by
position:

```python
key = int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")
substream = np.random.SeedSequence(entropy=seed, spawn_key=(key,))
rng = np.random.default_rng(substream)
```

Name-keyed rather than `SeedSequence.spawn(k)` positional, because positional keys are assigned in
call order: adding, removing or reordering a partition would silently move every later partition's
stream — reintroducing, at the level of the partition list, exactly the coupling P-1b exists to
remove. A name-keyed stream is invariant to what else exists.

**Verified, not assumed** (`util/ad-hoc/2026-09-01_p1b_substream_check.py`; P-1a was rejected for a
plausible-sounding RNG claim that proved wrong, so P-1b's premise was probed before being built on):

| probe | result |
| --- | --- |
| P1 `spawn(3)[:2]` vs `spawn(2)`, compared as **drawn values** | **stable** |
| P2 incremental spawn off a reused parent | consistent with a fresh spawn |
| P2b name-keyed stream invariant to interleaving, and distinct per name | **holds** |

**How it composes with the other rulings.** P-1b is not an extra step — decision 6 already requires
generating the three subsets separately and assembling `X_full` from them, so per-partition streams
are the natural way to seed that:

1. derive `seed_train` / `seed_val` / `seed_test` by name;
2. generate each partition at its own size (decision 8: dataset-level row counts);
3. fit the normaliser on `train` only, apply to all three (decision 7);
4. `X_full = concat(train, val, test)`.

**THE HAZARD P-1b INTRODUCES — and P-1a did not have.** Independently generating partitions at
*different sizes* means, for a mechanism-A generator, **a different grid over the same curve**. Those
grids can coincide.

Measured at the default `100/40/30` → 1000/400/300:

- `train ∩ val` share **4** grid positions (not the 2 endpoints); `train ∩ test` and `val ∩ test`
  share 2.
- At `noise=0.0`: **4 of 400 val rows are byte-identical to a train row.**
- At `noise=0.1` (the default): 0 duplicates — independent noise is what normally hides it.

`noise=0.0` is **reachable configuration**, not a corner case: `SpiralParams.noise` is `ge=MIN_NOISE`
with `MIN_NOISE = 0`, and `SpiralParams(noise=0.0)` constructs fine. So a legitimate request can
produce a dataset whose validation split contains exact copies of training rows — the precise leak
this arc exists to remove, reintroduced by its own fix.

**Required guard, before Chunk 3 ships.** Not yet ruled which:

- **G-a — de-duplicate at assembly.** After generating the three partitions, drop any row in `val` /
  `test` that appears in `train`, and top up. Correct for every generator, costs an exact-match pass,
  and makes the partition sizes approximate rather than exact.
- **G-b — offset the grid per partition.** Give each partition a half-step phase offset so the grids
  cannot coincide by construction. Cheap and exact, but is a per-generator change and only addresses
  mechanism-A generators.
- **G-c — constrain the sizes.** Require the partition counts to be pairwise coprime so only the
  endpoints coincide. Cheapest, but pushes a subtle numeric constraint onto the caller and still
  leaves 2 shared positions.

**G-a is the only one that is generator-independent**, which matters because §9.3.1 classified only
three of seventeen generators. A duplicate-row assertion belongs in the §6a consumer gate regardless
of which guard is chosen — it is the check that would have caught this.

**What this evidence does not cover.** Only `spiral` was probed for duplicate rows. `moon` is the
other known mechanism-A generator and was not measured. Generators whose points are purely
RNG-drawn should not collide at all under name-keyed streams, but that was not verified.

#### 9.3.3 SCOPE LIMIT — P-1b applies only to the SYNTHESISED class

Everything in §9.3.2 assumes a generator that **synthesises** points, so that asking for a
partition of size *n* produces *n* fresh points. **Five of the sixteen generators do not.** For those,
"generate each partition independently from its own substream" is not merely suboptimal — it is
wrong, and for one class it is *worse* than the defect this arc is removing.

| class | generators | what P-1b means |
| --- | --- | --- |
| **1 — synthesised** | `spiral`, `moon`, `gaussian`, `xor`, `checkerboard`, `circles`, `ar_p`, `delay_product`, `irregular_sine`, `mackey_glass`, `multi_sine` | §9.3.2 as written. Mechanism-A grid caveat applies to `spiral` and `moon`. |
| **2 — finite pool, exchangeable** | `mnist`, `arc_agi`, `csv_import` | **Partition the pool ONCE, disjointly.** Independent per-partition sampling draws from the *same* pool three times and overlaps by construction. |
| **3 — finite pool, ORDERED** | `equities`, `equities_seq` | **Chronological carve-up, already implemented.** Independent sampling would also destroy the time ordering. |

**Class 2 — the overlap is structural, not incidental.** `mnist` selects via
`ds.shuffle(seed=params.seed)` then `ds.select(range(n_samples))` (`mnist/generator.py:128-131`) —
the first *n* of a seeded shuffle over the real dataset. Give `train` and `val` different substream
seeds and you get two *different* shuffles of the same ~70k pool; expected overlap for 1000 and 400
is ≈ 6 images, and it grows as the requested sizes approach the pool size. `arc_agi` is worse:
`rng.choice(len(tasks), min(params.n_tasks, len(tasks)), replace=False)`
(`arc_agi/generator.py:134,166`) — `replace=False` prevents duplicates **within** a partition and
does nothing across partitions, so if `n_tasks` is a large fraction of the pool the overlap
approaches total.

**Class 3 — applying P-1b here would be a REGRESSION.** `equities` carves chronologically:
`frame.iloc[:n_train]` then `frame.iloc[n_train : n_train + n_test]`
(`equities/generator.py:206-207`). That ordering is what prevents look-ahead leakage in a time
series. Drawing partitions from independent substreams would interleave past and future rows across
`train` / `val` / `test` — a *worse* leak than the selected-on-reporting one being fixed, and one
that no duplicate-row guard would detect, because the rows are genuinely distinct.

**Consequences.**

- **§9.3.2's guards G-a / G-b / G-c are class-1 remedies only.** G-a (de-duplicate at assembly)
  would "fix" class 2 by silently distorting the sample, and would not see class 3's failure at all.
- **Decision 8's additive sizing cannot apply to classes 2 and 3** — you cannot generate additional
  MNIST digits or additional trading days. §6.3 already anticipates this: additive sizing is
  overridden *"when no generator or generator specs exist, or the data is not synthesisable."*
  **Classes 2 and 3 are exactly that carve-up path**, and this is the first place the design names
  which generators it covers.
- **Prefix stability is achievable for classes 2 and 3** — partitioning a fixed, ordered pool at
  index boundaries is prefix-stable by construction. So P-1a was never blocked *here*; §9.3.1's
  blockage is a class-1 result. The two classes want opposite mechanisms, which is why this scope
  limit has to be explicit rather than inferred.

**Not verified.** `equities_seq` was classified from its name and its shared lineage with `equities`,
not read. `csv_import` was classified from its loader, not from its selection logic. The class-1 list
is by exclusion — only `spiral`, `moon` and `gaussian` were examined directly (§9.3.1).

## 10. Naming — SETTLED: `X_val` / `y_val`, **not** `X_eval`

N-1 is resolved. Validated 2026-08-29 by three independent agents — an authoritative-literature
lens, a framework-API lens, and an adversarial lens briefed to *refute* the premise — none shown
another's findings, each required to quote a fetched URL for every claim. The full record, including
what each lens could **not** source, is in
[`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_PARTITION-NAMING-VALIDATION.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_PARTITION-NAMING-VALIDATION.md).

### The decisive finding: `eval` is not merely non-standard, it is *inverted*

The Hugging Face Hub — the largest dataset registry — publishes split-name aliases:

> "There are several ways to refer to train/validation/test splits. Validation splits are sometimes
> called "dev", and test splits may be referred to as "eval". These other split names are also
> supported, and the following keywords are equivalent:
> - train, training
> - validation, valid, val, dev
> - **test, testing, eval, evaluation**"
> — <https://huggingface.co/docs/hub/en/datasets-file-names-and-splits>

**`eval` resolves to `test`.** A contract shipping `X_train` / `X_eval` / `X_test` would be read by
HF-shaped tooling as *two test splits and no validation split* — precisely inverting the fix this
document exists to make. Corroborated independently:

- **XGBoost's canonical idiom** attaches `'eval'` to the *test* matrix:
  `evallist = [(dtrain, 'train'), (dtest, 'eval')]` — <https://xgboost.readthedocs.io/en/stable/python/python_intro.html>
- **TRIPOD+AI** (BMJ reporting standard) renamed "validation" *because it is ambiguous*, and its
  replacement term means the test set: *"we refer to data used to evaluate model performance as
  evaluation data"* — <https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/>
- **Hugging Face contradicts itself across its own stack**: the Hub maps `eval`→test, while
  `Trainer(eval_dataset=…)` uses it for the validation role. One vendor, two opposite meanings.
- `eval` is further overloaded as an *action* (`Trainer.evaluate`, `metric_key_prefix='eval'`), a
  *model mode* (`torch.nn.Module.eval()` — "Set the module in evaluation mode"), and a *benchmark
  suite* (OpenAI Evals).

Negative evidence, gathered programmatically rather than impressionistically: **0** occurrences of
standalone "eval" in Google's full ML Glossary text, and **0** occurrences of `X_eval` across all
17 corpora fetched. There is no `EVAL` member in `datasets.Split` or `tfds.Split`.

### What survived the adversarial attack

The adversary was briefed to break "there is one accepted convention" and largely succeeded — the
term is genuinely contested across disciplines (clinical prediction modelling uses `validation` for
what ML calls `test`; NLP uses `dev`; TFDS declares any string a valid split name; sklearn's default
splitter yields only two partitions). But three things held under attack:

1. **`train` / `validation` / `test` is the dominant mainstream-ML convention.** Google, ESL,
   Goodfellow, scikit-learn, TFDS and HF `datasets` all use it.
2. **`train` is universal** — zero counter-examples found.
3. **`test` = final held-out assessment is stable within ML tooling.** The reversals are
   cross-disciplinary, not intra-ML.

So the correct conclusion is the *opposite* of the framing this document started with: adopt
`validation`, and treat `eval` as a reserved-and-poisoned token.

### The decision

| layer | name | why |
| --- | --- | --- |
| NPZ contract keys | **`X_val`, `y_val`** | `val` is an explicit HF alias for validation; matches the contract's existing sklearn-style capitalisation (`X_train`, `X_test`) |
| split/config vocabulary | **`validation`** | matches `datasets.Split.VALIDATION` and `tfds.Split.VALIDATION`; unambiguous in prose |
| cascor call signatures | **`x_val` / `y_val`** (already present) | no change required — see below |

**The clinching practical argument is repo-local: cascor already uses this name.**

- `src/cascade_correlation/cascade_correlation.py` — `def fit(self, x_train, y_train, x_val=None, y_val=None, …)`
- `src/api/models/cascor_model.py` — `def fit(self, X, y, *, X_val=None, y_val=None, …)`

The codebase already carries `x_val`/`X_val` in both tiers. Adopting `X_val` in the contract makes
the contract agree with code that already exists; adopting `X_eval` would introduce a **third**
spelling for a concept that already has two.

**Residual inconsistency to fix while here (not caused by this design):** the two `fit` signatures
disagree on capitalisation — `x_val` in the core network, `X_val` in the service wrapper. The
contract keys use capital `X` (matrix) and lowercase `y` (vector), the sklearn convention. Worth
aligning the wrapper and the network on one spelling as part of the same change, rather than
leaving a third variant to accumulate.

**One honesty note on `X_val` itself**: the literature lens found **0** occurrences of `X_val` in
the scikit-learn docs (against 11 each for `X_train`/`X_test`) and did not establish it as a
*documented* variable convention. Its support is (a) HF's alias list, (b) Keras's own docstring
example `(x_val, y_val)`, (c) torchvision's `split='val'`, (d) Lightning's `val_dataloader`, and
(e) cascor's existing signatures. That is strong practical support, not a citation from a style
guide — and no such style guide appears to exist.

## 11. References

- [cascor#582](https://github.com/pcalnon/juniper-cascor/issues/582) — tier parity (this document's origin)
- [cascor#578](https://github.com/pcalnon/juniper-cascor/issues/578) — baseline-tier decision (blocked on this)
- [cascor#572](https://github.com/pcalnon/juniper-cascor/issues/572) — global-stream roll defect (independent, confirmed 2026-08-29)
- `reports/tensor-hash-probe-2026-08-28/` — the probe, its evidence, and reproduce steps
- Ecosystem data contract — `Juniper/CLAUDE.md` § Data Contract (`X_train`, `y_train`, `X_test`, `y_test`, `X_full`, `y_full`)
