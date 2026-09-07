# Train / Validation / Test partition — design of record

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (juniper-data → juniper-data-client → juniper-cascor)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-09-04
**Status**: DESIGN — **the partitioning question is CLOSED.** Decisions 1-8 settled 2026-08-29/31
(§9.2); 11 settled 2026-09-02 (§9.5); **9, 10 and 12 settled 2026-09-03 (§9.6)**.

> **Operator surface (2026-09-04):** shipped-vs-design split, this-repo consumers
> (`RECURRENCE_SPLITS`, experiment fixtures, `snapshot_attribute.load_datasets`), and required-fix 0
> scope live in [`docs/REFERENCE.md` § Train / Val / Test Partition Contract](../docs/REFERENCE.md#train--val--test-partition-contract).
> Required-fixes 1–4 plus juniper-data#316 are **shipped**. Required-fix 0 (`*_full` removal) is the
> only remaining item and has **not started**.

> **What the partition design now says, in full:**
>
> - Partitions are produced by `shuffle_and_split` / `temporal_split_index` and are **index-disjoint
>   by construction** — decision 9 REVERSED, both P-1a and P-1b abandoned (§9.6.1).
> - **No duplicate-row guard is needed** — decision 10 COLLAPSED with the leak it guarded (§9.6.2).
> - **`X_full` and the whole `*_full` family leave the contract** — decision 11 (§9.5), which also
>   RETIRED decision 6 and mooted decision 7's `X_full` consequence.
> - Generators emit `train` / `val` / `test` directly, each partitioned correctly for its own data
>   type, plus a **`partition_provenance` block inside the NPZ** and one ingestion gate — decision 12
>   (§9.6.3), adopted for auditability, not for the per-run class membership it originally answered.
> - The normaliser is fit on **`train` only** — decision 7, unaffected throughout.
>
> **§§9.3 and 9.4 are now HISTORY.** Their measurements retain their evidential value, but the
> questions they investigated — prefix stability, per-run class membership, which guard to use — are
> answered or dissolved. Read §9.6 first; go back to §9.3/§9.4 only for the evidence behind it.
>
> **Four required fixes are listed in §9.6.4.** Fixes 1–4 are **shipped** (juniper-data#314 / data#323,
> #317 / data#318, #319 / data#322, #320 / data#343; circular-import #316 / data#333 also closed).
> Required-fix 0 — drop `X_full` / the `*_full` family — is the only remaining item (decision 11,
> scoped in §9.5.4) and has not started. Required-fix 2's companion row-reuse gate was **dropped
> 2026-09-03** — with partitions index-disjoint by construction it had nothing to catch, and the
> invariant it encoded is unsatisfiable on ordinary low-cardinality data (§9.6.4).

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

| tensor    | CLI                              | service                          |
|-----------|----------------------------------|----------------------------------|
| `x_train` | `(800,2)` `raw=341d9dd0cb9ed0ea` | **identical**                    |
| `y_train` | `(800,2)` `raw=8d92cbeba78a414e` | **identical**                    |
| `x_val`   | `None`                           | `(200,2)` `raw=e0ecd7ffe171d447` |
| `y_val`   | `None`                           | `(200,2)` `raw=22cd2024464128c0` |

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

| partition    | used for                                                                                | touched                                    |
|--------------|-----------------------------------------------------------------------------------------|--------------------------------------------|
| `train`      | gradient updates; candidate correlation                                                 | every epoch                                |
| `validation` | early stopping, patience, best-checkpoint selection, LR schedules, any in-loop decision | every validation interval                  |
| `test`       | the final reported score                                                                | **exactly once**, after training completes |

The invariant that makes it worth doing: **no quantity computed on `test` may influence any
decision made during training.** If a number is allowed to change what the run does, it is
`validation` by definition, whatever it is named.

Both arms consume the same three partitions, so the tiers become comparable by construction and
`#578` reduces to a fixed-overhead question rather than a semantics question.

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

| generator    | `X_full` | `X_train`   |
|--------------|----------|-------------|
| spiral       | DIFFERS  | **DIFFERS** |
| moon         | DIFFERS  | **DIFFERS** |
| xor          | DIFFERS  | **DIFFERS** |
| circles      | DIFFERS  | **DIFFERS** |
| checkerboard | DIFFERS  | **DIFFERS** |
| gaussian     | DIFFERS  | **DIFFERS** |

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

| # | option                             | effect                                                                                                                                                                          |
|---|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0 | **Fill synthetically**             | Apply §6.2 where possible — generate the missing partition(s) and proceed cleanly.                                                                                              |
| 1 | **Continue with recorded warning** | Proceed on the `X_test`-as-eval fallback. Warning visible on all tabs for the run's lifetime; metrics carry an explicit caveat; `validation_warnings` recorded on the manifest. |
| 2 | **Back to dataset selection**      | Return control to the dataset page (top tab menu) and its left context menu, config intact.                                                                                     |
| 3 | **Cancel the run**                 | Abort with the clean-up / close-out appropriate to the current operating mode.                                                                                                  |

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
| 6 | **D-1** — what does `X_full` mean under three partitions? | ~~**`X_full` is ASSEMBLED, not split.**~~ **RETIRED 2026-09-02 by decision 11.** `X_full` is removed from the contract, so the question it answered no longer exists. Recorded rather than deleted because §9.3's prefix-stability analysis was reasoning *from* it. The ruling's surviving content is the ordering it implied: partitions are produced directly, not carved from a pre-existing whole. |
| 7 | **Normalisation fit scope** | **STANDS: fit on `train` only; apply those statistics unchanged to `val` and `test`.** No quantity derived from the reported partition may reach the training data — the same invariant §5 states for the reported score, applied to the scaler. ~~Consequence: `X_full` is deliberately NOT uniformly normalised.~~ **That consequence is moot under decision 11** — with no `X_full` there is no mixed-scale array to warn about. The fit-scope ruling itself is unaffected, and juniper-data#314 / data#323 **shipped** the three-generator leak fix. |
| 8 | **D-2** — how is additive sizing implemented? | **Dataset-level row counts.** The ratios denote absolute rows of the realised dataset, identically for every generator regardless of its native size knob (`n_points_per_spiral`, `n_points_per_quadrant`, `n_samples_per_class`, `n_samples`). `n_points_per_spiral=500, n_spirals=2` with `100/40/30` means `n_train=1000, n_val=400, n_test=300` — 1700 rows total. This resolves the plan's open question *"what '40 % of train' means for a per-spiral knob"*: it means rows, never per-spiral units. |
| 9 | **P-1** — how is cross-snapshot comparability obtained? | ~~P-1b: name-keyed seed substreams~~ **REVERSED 2026-09-03. BOTH P-1a AND P-1b ARE ABANDONED.** The current approach stands: partitions are produced by `shuffle_and_split` (tabular) / `temporal_split_index` (sequence), which are **index-disjoint by construction**. Neither prefix stability nor per-partition substreams is pursued. The §9.4 review established that P-1b was never shipped, buys nothing measurable for i.i.d. generators, and is worse for lattice ones; abandoning it removes a hazard rather than leaving one to guard. See §9.6. |
| 10 | **Which P-1b guard closes the duplicate-row leak?** | ~~G-a — de-duplicate at assembly~~ **COLLAPSED 2026-09-03 — the question no longer exists.** G-a, G-b and G-c all guarded a leak introduced by P-1b; with decision 9 reversed there is no such leak. Disjointness is achieved by construction, not by a guard. **A different and narrower check survives** as required-fix 2 of §9.6: a post-hoc degeneracy assertion on the produced partitions — see §9.6.4 for the caveat that makes it not simply G-a under another name. |
| 11 | **Does the contract keep `X_full`?** | **NO — `X_full` is DROPPED, and with it the whole `*_full` family.** Ruled 2026-09-02. Generators emit `train` / `val` / `test` directly, each partitioned in the way correct for its own data type, plus queryable metadata. Evidence: no consumer requires `X_full` to be a particular roll-up — every use is "give me the whole dataset" (canopy `demo_mode.py:821-837,965,1858,1958`; cascor `spiral_problem.py:1325-1356` plotting; the data-client preview; ml `snapshot_attribute.py:318`) — and nothing indexes it with partition-derived indices. In the equities artifact all five `*_full` arrays (`X_full`, `y_full`, `date_full`, `ticker_code_full`, `y_reg_full`) **already have `_train`/`_test` siblings**, so the family is provably redundant there. See §9.5. |
| 12 | **Does the artifact declare how it was partitioned?** | **YES — a `partition_provenance` block inside the NPZ** (not `DatasetMeta`), adapted from §9.4.1's Proposal B. It declares strategy, seed value, the generator configuration values required to reproduce the run, per-partition counts and digests, and normaliser fit scope. **One ingestion gate re-derives everything derivable and enforces a legality table on the rest.** Ruled 2026-09-03. Its original motivation — resolving per-run class membership — is gone with decision 9; it is adopted for the separate and surviving benefit of making an artifact self-describing and its partitioning auditable after the fact. See §9.6.3. |

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

| probe                                | result     | what it isolates                               |
|--------------------------------------|------------|------------------------------------------------|
| Q1 `normal(size=N)` prefix           | **STABLE** | numpy itself                                   |
| Q1b `random(size=N)` prefix          | **STABLE** | numpy itself                                   |
| Q2 one spiral arm, fresh rng         | DIFFERS    | per-stratum generation, layout excluded        |
| Q3 arm 1 under shared rng            | DIFFERS    | cross-stratum RNG coupling                     |
| Q4 `X_full` under vstack             | DIFFERS    | stratified layout                              |
| Q5 spiral `legacy_cascor` (pure RNG) | DIFFERS    | **refuted** the "RNG paths are fine" guess     |
| Q6 bare `np.linspace`                | DIFFERS    | **mechanism A**, no juniper-data code involved |
| Q7 2nd of two N-sized draws          | DIFFERS    | **mechanism B**, no juniper-data code involved |

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
*(§9.3.4 now supplies the measured census the last sentence was hedging about.)*

#### 9.3.4 The class-1 census — G-b is UNSOUND, and one generator ignores its seed entirely

§9.3.2 left G-a / G-b / G-c unruled, and the choice turns on **how many class-1 generators actually
leak** — which had been inferred from `grep linspace`, i.e. from an artifact *adjacent* to the one
that could falsify it. Measured instead:
`util/ad-hoc/2026-09-01_class1_duplicate_census.py` generates a `train` and a `val` partition
independently, each from its own name-keyed substream, and counts byte-identical rows. **All 11
class-1 generators, no skips.**

| generator | dupes @ `noise=0` | dupes @ default | verdict |
| --- | --- | --- | --- |
| `spiral` | 8 / 800 | 0 | **leaks** (mechanism A) |
| `moon` | 4 / 400 | 0 | **leaks** (mechanism A) |
| `mackey_glass` | **368 / 368** | **368 / 368** | **leaks TOTALLY — see below** |
| `gaussian`, `xor`, `circles`, `checkerboard` | 0 | 0 | clean |
| `ar_p`, `delay_product`, `irregular_sine`, `multi_sine` | 0 | 0 | clean |

**G-b is unsound; G-a is required — and G-a was RULED 2026-09-02 as decision 10.** `mackey_glass`
leaks **100 %** and is *not* linspace-parameterised, so a per-partition grid offset — which addresses
mechanism A only — would leave the worst case entirely untouched. **G-a (de-duplicate at assembly) is
the only candidate that covers the measured leak set**, and the only generator-independent one. G-c
is insufficient for the same reason. The census did not so much inform the choice as remove it.

**Why `mackey_glass` is total: it ignores its seed.** `MackeyGlassParams.init_noise_std` defaults to
`0.0` (`params.py:33`), and the seed is consumed **only** inside `if params.init_noise_std > 0`
(`generator.py:64-66`). At the default the trajectory is an exact deterministic Euler integration
from a constant history, so *every* seed produces byte-identical output — verified directly: seed 1
and seed 999999 give `max|Δ| == 0.0`.

This is **documented and intentional** — the field's own description says *"0 yields an exact
deterministic init"* — but it has a consequence the design must record: **no seeding scheme can
separate `mackey_glass`'s partitions**, because the seed is inert. P-1b is not merely leaky there;
it is *inapplicable*.

**The taxonomy needs a second axis.** §9.3.3 split generators by *where the data comes from*
(synthesised vs finite pool). `mackey_glass` shows that is not sufficient: it is fully synthesised
and still cannot use P-1b. The operative question is **whether the output is seed-dependent at the
configured parameters**:

- **seed-dependent** → P-1b applies (with G-a for the mechanism-A residue).
- **seed-invariant** → partitions must be **disjoint segments of one generated trajectory** — the
  class-3 carve-up, for a class-1 generator. `mackey_glass` at default `init_noise_std` is here.
  Raising `init_noise_std > 0` moves it to the first row, which is a **configuration-dependent
  class membership** and needs to be resolved per run, not per generator.

**A non-finding, recorded so it is not re-derived as alarm.** `mackey_glass` is used by
`util/experiments/suites/p4/e-d-recurrence-d-sweep.yaml`, but that suite runs `seed_policy: fixed`
with `seed: 0` and sweeps `train.d` (8/16/32). It does **not** rely on seed variance, so its results
are unaffected by the determinism. No existing measurement is invalidated by this finding.

**What this evidence does not cover.** One size pair only (train 1000 / val 400 as requested, which
the generators expand differently — `spiral` to 2000/800, the sequence generators to 968/368 after
windowing). Duplicate counts are size-dependent, so these are existence proofs, not magnitudes.
`train` vs `test` and `val` vs `test` were not measured — only `train` vs `val`. The five class-2/3
generators are out of scope here by construction (§9.3.3).

## 9.4 Per-run class membership — two proposals, and why NEITHER should be built

Requested 2026-09-02: two independently generated proposals for resolving partition-strategy class
membership per run, validated under
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).

**The review did not choose between them. It refuted the premise both rest on.** The recommendation
is to build neither and to revisit decisions 9 and 10. That recommendation is the owner's to accept
or reject; nothing here is settled.

### 9.4.1 The two proposals

**Proposal A — Seed-Sensitivity Contract (producer side).** Each generator gains an optional
`partition_capability(params) -> PartitionStrategy` computed from *resolved params*; a
seed-perturbation probe verifies the declaration before `INDEPENDENT_SUBSTREAM` is honoured; the
fail-closed default for an undeclared generator is "generate one realisation, carve it disjointly".

**Proposal B — Partition Provenance Block (contract side).** A `partition_provenance` blob **inside
the NPZ** (not `DatasetMeta`) declaring strategy, seed-sensitivity, per-partition counts and digests,
normaliser fit scope and assembly order; one ingestion gate re-derives what is derivable and enforces
a legality table on what is not.

They are complementary rather than competing — A decides, B transmits. Both were briefed with
deliberately non-overlapping entry points and neither saw the other's work.

### 9.4.2 The finding that reframes everything

**P-1b is not shipped behaviour.** Every one of the 16 generators already produces one realisation
and carves it — the 9 tabular ones via `shuffle_and_split` (`spiral/generator.py:44-46` and
siblings), the 7 sequence ones via `temporal_split_index` (`core/split.py:116`). A fleet-wide search
for `SeedSequence` / `spawn_key` / per-partition seeds in `juniper_data/` returns **nothing**.

Under `shuffle_and_split` the partitions are **index-disjoint by construction**, so the duplicate
leak §9.3.2 and §9.3.4 characterise **cannot occur today**. It is introduced by decision 9.

So both proposals are machinery to make safe a hazard that only exists if P-1b is adopted first.

### 9.4.3 What independent generation actually buys — measured

- **For i.i.d. generators: nothing.** `gaussian`, 200 replicates per arm, 200k values:
  KS D = 0.0032 against a 0.0068 critical value. Independent draws and disjoint carving are
  statistically indistinguishable.
- **For lattice generators: it is worse than nothing.** Two "independent" `spiral` pools at the
  **default** `noise=0.1` remain aligned on the deterministic `np.linspace` radius lattice
  (`spiral/generator.py:138`). Cross-pool nearest-neighbour distance is a fraction of the within-pool
  spacing, against ~1.0 for an i.i.d. control.

**This exposes an inadequacy in §9.3.4's own instrument.** The class-1 census measured *exact byte
duplicates* and reported "0 at default noise". That is true and misleading: the pools are
lattice-aligned at default noise, and exact-equality testing is structurally blind to it. A
duplicate-row count is not a leak measurement.

### 9.4.4 Lane B — the detection mechanism is unsound

Reproduction rigs: `util/ad-hoc/2026-09-02_laneb_probe_refutation_*.py`.

1. **The probe's discriminator is satisfied by a permutation.** `arc_agi` at `n_tasks >= pool` size
   (`generator.py:134,166`, `rng.choice(..., replace=False)`) gives probe verdict **`dependent`**
   while **40/40** rows are duplicated across partitions. The mechanism reads green on the class-2
   overlap **§9.3.3 itself documents as structural**. `mnist` (`generator.py:127-131`) has the same
   shape.
2. **No array choice repairs this.** Probe `X_full` and `arc_agi`/`mnist` pass while leaking; probe
   `X_train` and `spiral`/`moon` at `noise=0` pass while leaking, because `shuffle_and_split`
   re-permutes. For those configs the two readings give **opposite verdicts**.
3. **A schema-valid epsilon defeats the probe and G-a together.** `mackey_glass` at
   `init_noise_std=1e-8` (`params.py:33` is `ge=0`, no positive floor): probe `dependent`, G-a finds
   **0** exact duplicates, and **all 568 validation rows sit within 4.2e-5 of a training row** — 0.005 %
   of the signal span. Both gates green on a numerical carbon copy.
4. **The verdict is nondeterministic near the boundary.** At `init_noise_std=1e-13`, **19 of 60**
   random seed pairs read `dependent` and 41 read `invariant` — the same request accepted or refused
   depending on which two constants the probe hard-codes. `seed_sensitivity` is therefore **not a
   property of the run**, and cannot be recorded as one or adjudicated against a legality table.
5. **`seed` is a branch condition, so the probe cannot execute the path the run takes.**
   `arc_agi/generator.py:129,161` and `mnist/generator.py:127` branch on `seed is None`. Setting a
   seed is the probe's entire method, so it always takes the `else` branch and stamps `dependent` on
   a run that in fact took a deterministic prefix.
6. **`partition_capability(params)` is ill-typed.** Identical `CsvImportParams` yield a different
   dataset and a different verdict under a different `JUNIPER_DATA_IMPORT_DIR`
   (`csv_import/generator.py:82-86`); `equities/generator.py:175` defaults `end_date` to
   `datetime.now(UTC)`. Capability is a function of params **and environment**, so the proposed
   signature cannot be correct.
7. **The empty dataset makes every gate vacuous.** `arc_agi` at its default `source="huggingface"`
   silently returns `X_full` of shape `(0, 900)` (see §9.4.6). Two empty arrays are byte-identical, so
   the probe says `invariant`; a duplicate check says 0. Neither gate has a row-count precondition,
   and the operator is told the *partitioning* is wrong.

### 9.4.5 Decision 10's stated justification does not support it

§9.3.4 ruled *"G-b is unsound; G-a is required"* because G-b cannot fix `mackey_glass`. **G-a cannot
fix it either.**

- At default `init_noise_std=0.0` the seed is inert, so every G-a top-up regenerates the identical
  trajectory: **568 of 568 rows duplicate, 0 fresh, every round.** G-a either loops forever or emits
  an **empty** validation partition.
- **G-a's invariant is unsatisfiable on ordinary tabular data.** Records with coinciding feature
  vectors are normal for low-cardinality/categorical inputs; on a 6-record `csv_import` pool with 3
  distinct feature vectors, **5 of 8** partitionings violate "zero exact duplicates across
  partitions". G-a would delete valid records — biasing the sample — or refuse to assemble.

"G-b fails on X, therefore G-a" is invalid when G-a also fails on X. **Decision 10 stands as an owner
ruling, but the reasoning §9.3.4 gave for it is void**, and G-a is non-terminating on the case that
motivated it. It needs re-deciding on different grounds, or withdrawing.

### 9.4.6 Uncommissioned defects surfaced by the review

- **`arc_agi` silently produces an EMPTY dataset at its default configuration.** `source="huggingface"`
  cannot reach `fchollet/arc-agi`, the handler at `generator.py:106-116` falls back to a cached
  dataset with an incompatible schema (no `train`/`test`/`task_id` keys), and
  `_convert_tasks_to_arrays` returns `X_full` of shape **(0, 900)** — HTTP 200, no error, no warning,
  **511 s**. Any determinism test written against default `arc_agi` compares two empty arrays and
  passes unconditionally. **Vacuous-pass class; needs its own ticket.**
- **Nine generators default `seed=None`** and are therefore non-reproducible at their documented
  defaults. `spiral` is the only 2-D generator with a concrete default seed.
- **Normaliser fit scope**: `equities`, `equities_seq` and `csv_import` fit on the full set including
  chronologically-later rows — filed as juniper-data#314, contradicts decision 7.
- **Postgres `SCHEMA_SQL` declares `n_classes NOT NULL`** while `core/models.py` made it nullable, so
  wiring the (currently dead) Postgres store would hard-fail on the first regression dataset.

### 9.4.7 Recommendation — not a ruling

**Build neither proposal.** Instead:

1. **Revisit decision 9 (P-1b).** It is unshipped, buys nothing measurable for i.i.d. generators,
   is actively worse for lattice generators, and is the sole source of the hazard §9.3.2–§9.3.4
   describe. The existing carve is already index-disjoint and is pinned by tests that exist and pass
   (`tests/unit/test_split.py:145`, `tests/unit/test_sequence_windowing_leakage.py`).
2. **Re-decide or withdraw decision 10 (G-a)** — §9.4.5.
3. Spend the budget on three cheap, artifact-level fixes that the proposals do not deliver:
   **make `seed` required or defaulted**; **one post-hoc degeneracy assertion** on the produced arrays
   at the single route site that already calls `compute_checksum`
   (`api/routes/datasets.py:249`) — rejecting near-degenerate `X_full` and verbatim train/test row
   reuse; and **fix `arc_agi`'s silent-empty fallback**.

The third item is the only proposal on the table that catches Lane B's `xor(margin=x_range=y_range)`
case, because it operates on the artifact rather than on a declaration about the artifact.

### 9.4.8 Consensus record

**Sizing** (procedure §3): document of record × novel design with no standing answer → top-right
cell → 3+ Lane A with distinct entry points, 2+ Lane B with opposing briefs, ≥2 iterations.

**Round 1** — 2 generation agents (producer / contract entry points, mutually blind); 3 Lane A
(direct generator measurement / ingestion-and-storage code paths / filesystem-and-Docker census);
2 Lane B (over-engineering lens / detection-correctness lens).

**Reconciler re-derivations** — verified personally before adoption: the 16-generator count (four
instruments); `spiral` seed-invariance at `noise=0`; the equal-size 100 % `X_full` collision; the
`spiral`-vs-`gaussian` lattice contrast; the absence of any per-partition seeding in `juniper_data/`;
and the live/legacy artifact roots.

**A Lane A / Lane B disagreement, reconciled rather than averaged.** Lane A1 reported `gaussian`
seed-invariant at `class_std<=1e-8`; Lane B2 reported it `dependent` on 60/60 seed pairs from 1e-4 to
1e-20. **Both are right about different configurations**: A1 supplied explicit non-zero `centers`,
B2 used auto-centers, where one component is `sin(π) ≈ 0` and a subnormal perturbation survives
(`gaussian/generator.py:119,124`). Re-derived directly. This *strengthens* the Lane B conclusion —
the verdict turns on a parameter **interaction**, which no per-generator table can capture.

**Corrections to this document forced by round 1**, applied in §9.4.9 below: the generator count
(17 → 16, in two places), the artifact census (26 across 5 roots → 39 across 7, and volatile), and
the "mechanism A grid coincidence" framing, which the lattice measurement shows was the wrong
abstraction — every duplicate measured anywhere in this arc came from a seed-invariant configuration.

**Termination**: round 1 changed the disposition entirely, so under procedure §4 a round 2 is owed
and has **not** been run. This section is therefore round-1 output, and §9.4.7 is a recommendation
awaiting both the owner's ruling and that second round.

### 9.4.9 Corrections to earlier sections of this document

- **§9.3.1 says "2 of 17 generators"; the correct figure is 16.** Confirmed by AST-parsing
  `GENERATOR_REGISTRY`, by directory listing, by `docker exec` against the running service, and by the
  live `/v1/generators` endpoint. The "17" came from counting `juniper_data_client`'s 17
  `GENERATOR_*` constants, whose 17th is `GENERATOR_CIRCLE_LEGACY = "circle"` — a deprecated alias
  that the registry rejects. §9.3.3's "5 of 16" was already right; the document contradicted itself.
- **The implementation plan's §9 S-6 census is superseded**: not 26 distinct artifacts across 5
  roots but **39 across 7**. The prior count was arithmetically exact at its timestamp and had two
  structural blind spots — `juniper_data/data/datasets/` and `juniper-legacy/` — while the live
  volume has since grown 10 → 20 (~10 writes/day). **Any figure here is valid only with its
  timestamp.** A census that does not exclude `.mypy_cache` is meaningless: it uses the same
  `*.meta.json` extension and contributes >2,000 false hits.
- **§9.3.2's "mechanism A / mechanism B" framing is the wrong abstraction.** Grid coincidence never
  produced a duplicate row in a seed-*dependent* configuration; every duplicate measured came from a
  seed-*invariant* one. The operative property throughout is seed-invariance.
- **§9.3.4's `spiral` entry needs a qualifier**: `spiral(noise=0)` is seed-invariant only on
  `algorithm="modern"` (the default). At the schema-valid `algorithm="legacy_cascor"` it is
  seed-**dependent**, because that path draws radii from the RNG (`generator.py:131`). A one-parameter
  change flips the class — which is itself decisive evidence against any static per-generator table.
- **Seed-invariance is a property of `X_full`, not of the partitions.** For `spiral`/`moon`, `X_full`
  is byte-identical across seeds while `X_train`/`X_test` are not, because `shuffle_and_split(seed=…)`
  re-permutes before slicing. §9.3.4's equal-size "100 %" figure is an `X_full` measurement; on
  `X_train` at default `shuffle=True` it is ~49 %, reaching 100 % only at `shuffle=False`.

## 9.5 Decision 11 — `X_full` is dropped from the contract

Ruled 2026-09-02. **Generators emit `train` / `val` / `test` directly**, each partitioned in the way
that is correct for its own data type, accompanied by queryable metadata. The `*_full` family is
removed from the NPZ contract.

The rationale of record, in the owner's framing: `X_full` is a **dataset-context-invariant structure
imposed on a heterogeneous set of generators**, and it becomes less tractable as datasets are added.
Baking a per-generator roll-up algorithm into each generator would be complexity bought for a
structure no requirement depends on. Removing it lets each generator solve the only problem that
actually matters — correctly distributed, non-leaking, single-purpose partitions — in the manner
suited to its own data.

### 9.5.1 The consumer census that supports it

Every functional use of `X_full` across the fleet is *"give me the whole dataset"*, never *"give me
the array the partitions were cut from"*:

| repo | site | use |
| --- | --- | --- |
| canopy | `src/demo_mode.py:821-837`, `:965`, `:1858`, `:1958` | validation ladder; dataset import for demo / visualisation |
| cascor | `src/spiral_problem/spiral_problem.py:1325-1356` | **plotting only** |
| cascor | `src/spiral_problem/data_provider.py:193,203` | key-presence and shape checks |
| data-client | preview path | first *n* rows |
| juniper-ml | `util/snapshot_attribute.py:318`, attribution scripts | regenerate-and-read |

**Nothing indexes `X_full` with partition-derived indices.** The one indexing pattern in the fleet —
`X_full[mask][order]` in `util/ad-hoc/verify_*.py` — masks by ticker code and then *explicitly
re-sorts by date*, so it behaves identically on a concatenation and does not depend on row order.

**In the equities artifact the family is provably redundant.** Its 16 keys include five
`*_full` arrays — `X_full`, `y_full`, `date_full`, `ticker_code_full`, `y_reg_full` — and **every one
already has `_train` / `_test` siblings**. Nothing is lost by removing them; the partitioned form is
already complete.

### 9.5.2 What this retires

Dropping `X_full` **collapses** parts of §9 rather than changing them:

- **Decision 6 (D-1) is retired.** It existed only to define what `X_full` means under three
  partitions. With no `X_full`, the question does not arise — and neither does the
  `full == train + test` length identity that generated it, nor the plan's options (a)–(d).
- **Decision 7's consequence is moot.** The fit-on-`train` ruling stands; the warning that *"`X_full`
  is deliberately not uniformly normalised"* has no referent. (juniper-data#314 / data#323 **shipped**
  the three-generator leak fix against decision 7 itself.)
- **§9.4.4's ordering defect dissolves.** Lane B2's objection — that the proposal probes `X_full` to
  choose the strategy that *produces* `X_full` — cannot arise when nothing produces `X_full`.
- **The §9.3.1 prefix-stability measurements keep their evidential value but lose their subject.**
  They were measured on `X_full`; the property they establish (a seed-invariant configuration cannot
  yield distinct partitions) is a fact about *generation*, not about `X_full`, and survives intact.

### 9.5.3 What this does NOT settle

**Decisions 9 (P-1b) and 10 (G-a) remain open**, and §9.4.7's recommendation to revisit them is
unaffected. Decision 11 narrows the ground they stand on but does not decide them:

- It **removes the `X_full`-specific confounds** from the P-1b question — no assembly step, no
  ordering defect, no mixed-scale array.
- It does **not** answer whether partitions should be independently generated or carved. Lane B's
  central findings still apply: the existing carve is already index-disjoint, independent generation
  buys nothing measurable for i.i.d. generators and is worse for lattice ones, and G-a does not
  terminate on a seed-invariant configuration.
- Decision 11 is, however, **consistent with** the carve model — "each generator partitions in the
  way correct for its data type" is what a fail-closed carve already does, and what the 16 generators
  do today.

### 9.5.4 Implementation surface — scoped, not started

Four items are bookkeeping rather than design, and each needs a deliberate decision:

1. **`DatasetMeta.n_samples`** is currently `len(X_full)`, asserted by
   `test_e2e_metadata_consistency`. Redefine as the partition sum.
2. **canopy's only validation ladder validates `X_full`** (`demo_mode.py:821-837`). It must be
   re-pointed at the partitions or the guard is **silently lost** — which, given how much of this arc
   has concerned guards that stopped guarding, should be done explicitly and tested.
3. **The preview endpoint** serves the first *n* rows of `X_full` and needs a new source. Serving
   `train` is the obvious choice and changes the semantics slightly; that is a product decision.
4. **`NPZ_SPLITS`** (`juniper-data-client/juniper_data_client/constants.py:421`) is
   `("train", "test", "full")`. Removing `"full"` and adding `"val"` is now a single coherent edit —
   which intersects **S-3** in §9 of
   [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md),
   which flagged that extending the constant was owned by no chunk while Chunk 1 pinned the 3-tuple.

**Backward compatibility.** All 39 stored artifacts carry `X_full`. Consumers must keep *tolerating*
its presence after producers stop emitting it; only the *requirement* is dropped. cascor's
`data_provider.py:193` `required_keys` is the one site that would reject an artifact for its absence.

### 9.5.5 What this evidence does not cover

- Whether any notebook, paper workflow, or archived analysis **outside these repos** reads `X_full`.
  The census covered the eight active repos only.
- Whether the `date_*` / `ticker_code_*` / `y_reg_*` families need any change beyond dropping their
  `_full` members — their `_train`/`_test` siblings exist, but a `_val` sibling does not yet.
- The sequence tier's `t_*` / `dt_*` / `observed_mask_*` families were not inspected for `_full`
  members.

## 9.6 Decisions 9, 10 and 12 resolved — the partitioning question closes

Ruled 2026-09-03. This section closes the line of inquiry §9.3 opened.

### 9.6.1 Decision 9 REVERSED — both P-1a and P-1b are abandoned

**The current approach stands.** Partitions are produced by `shuffle_and_split` (tabular, `core/split.py:82`)
and `temporal_split_index` (sequence, `core/split.py:116`), which are **index-disjoint by construction**.
Neither prefix-stable generation (P-1a) nor per-partition seed substreams (P-1b) is pursued.

This ratifies what all 16 generators already do, and it is the outcome §9.4's review pointed to:
P-1b was never shipped; independent generation was measured to buy nothing for i.i.d. generators
(KS D = 0.0032 vs 0.0068 critical) and to be *worse* for lattice generators, whose "independent"
pools stay aligned on a shared `linspace` lattice.

**Cross-snapshot comparability — the property P-1a and P-1b were competing to deliver — is not
obtained by either, and is not pursued here.** V-1 established that no sizing model preserves the
existing corpus; decision 4 (re-measure pre-change results, retaining the originals annotated)
already carries that and is unaffected.

### 9.6.2 Decision 10 COLLAPSED — no guard is needed

G-a, G-b and G-c existed only to guard a duplicate-row leak that P-1b introduced. With decision 9
reversed, there is no such leak: **disjointness is achieved by construction, not by a guard.**

This also retires the §9.4.5 finding that decision 10's justification was void — the finding stands
as a matter of record, but the decision it invalidated no longer exists.

### 9.6.3 Decision 12 — the partition-provenance block is adopted, for a different reason

§9.4.1's **Proposal B** is adopted in modified form. Its original motivation — resolving per-run
class membership — **is gone**, because with disjointness by construction there is no strategy to
resolve per run. It is adopted for a separate and surviving benefit: **an artifact that describes how
it was partitioned can be audited after the fact, by a consumer, without re-running the generator.**

A `partition_provenance` blob lives **inside the NPZ**, not in `DatasetMeta`. The §9.4 review
confirmed the reason and found it stronger than argued: **all three** cascor ingestion paths retain
only `dataset_id` and download the NPZ (`api/lifecycle/manager.py:3698-3700`, `api/app.py:512-522`,
`spiral_problem/data_provider.py:170-174`), and `get_dataset_metadata` has **zero** non-test call
sites in cascor. A metadata-only declaration is invisible to the primary trainer.

It declares: strategy; seed value; the generator configuration values required to reproduce the run;
per-partition counts and digests; and normaliser fit scope. **One ingestion gate re-derives
everything derivable** — counts against array shapes, digests against contents — **and enforces a
legality table on the rest.**

**What the §9.4 review says this can and cannot do**, carried forward so it is not rediscovered:

- A declaration can be **truthful and the artifact still degenerate**. Lane B demonstrated an
  `xor(margin=x_range=y_range)` artifact where every provenance field was correct, every derivable
  check passed, and 40 of 40 test rows were byte-identical to train rows. **Provenance is not a
  substitute for a check on the arrays** — which is why required-fix 2 below is a separate item.
- The `seed_sensitivity` trichotomy from the original proposal is **not** adopted: §9.4.4 showed it
  is not a property of the run at all (19 of 60 seed pairs disagreed at one configuration), and with
  decision 9 reversed nothing needs it.
- Fields that are **not derivable from a single artifact** — strategy, seed, fit scope — are
  declarations the consumer must take on trust or cross-check against a legality table. That is the
  irreducible limit of the mechanism.

### 9.6.4 Required fixes — the work list

| # | fix | status |
| --- | --- | --- |
| 0 | Abandon generation and use of `X_full` entirely | **decision 11 (§9.5)**; implementation scoped in §9.5.4 |
| 1 | Fix `arc_agi`'s silent-empty fallback | filed **juniper-data#317** |
| 2 | Make `seed` required or defaulted for **all** generators — default captured in constants, exposed in config file **and** environment variable. `mackey_glass`'s `init_noise_std` gets the same treatment (§9.6.5). ~~plus a post-hoc degeneracy assertion rejecting verbatim train/val/test row reuse~~ — **that half DROPPED 2026-09-03, see below** | filed **juniper-data#319** |
| 3 | Audit generators for correct partition use — `equities`, `equities_seq`, `csv_import` currently fit the normaliser on the full, unpartitioned set | filed **juniper-data#314** |
| 4 | Bring the Postgres store online with a correct schema, ideally derived dynamically from the models as a single source of truth | filed **juniper-data#320** |

#### The row-reuse gate is DROPPED — ruled 2026-09-03

The originally-specified companion to required-fix 2 — a post-hoc assertion at
`api/routes/datasets.py:249` **rejecting verbatim train/val/test row reuse** — is **not built.**

The reason it was raised, and the reason it is dropped, are the same fact. That assertion is, in
form, the **G-a invariant**, and §9.4.5 measured G-a **unsatisfiable on ordinary low-cardinality
data**: on a 6-record `csv_import` pool with 3 distinct feature vectors, **5 of 8** partitionings
violate it. Coinciding feature vectors are the normal case for categorical inputs, not a corner case.

Under decision 9 there is nothing for it to catch. The partitions are **index-disjoint by
construction**; repeated row *values* are a property of the source data, not evidence of a leak. An
unconditional rejection would have rejected valid datasets, and every softer shape — a
distinct-row-ratio threshold, warn-not-reject, exempting declared-categorical generators — buys a
weaker signal at the cost of a threshold nobody can calibrate from first principles.

**Required-fix 2 therefore reduces to the `seed` work alone**, which stands on its own merits and is
unaffected by this: nine generators are non-reproducible at their documented defaults regardless of
how partitions are checked.

**One thing this drops that the objection did not target**, recorded so the choice is visible rather
than accidental: a *degeneracy-ratio* check — distinct rows relative to row count — would have
flagged Lane B's `xor(margin=x_range=y_range)` case, which produced 4 distinct rows out of 200. That
is a different failure (a useless dataset) from the one the gate was specified to catch (a leaked
one), and it is now uncovered. `arc_agi`'s zero-row case is covered separately by juniper-data#317.

Required-fix 4's "schema derived from the models" would also close the latent defect the review
found independently: `SCHEMA_SQL` declares `n_classes NOT NULL` while `core/models.py` made it
nullable, so a wired Postgres store would hard-fail on the first regression dataset.

### 9.6.5 `mackey_glass` — the position of record

`mackey_glass` is **seed-invariant unless `init_noise_std != 0.0`**. This is documented and
intentional: the field's own description reads *"0 yields an exact deterministic init"*, and the seed
is consumed only inside `if params.init_noise_std > 0` (`generator.py:64-66`). Verified directly —
seed 1 and seed 999999 give `max|Δ| == 0.0`.

**Under decision 9 this stops being a problem.** Its partitions are disjoint by construction whether
`init_noise_std` is `0.0` or not; there is no longer any need to separate them by seed. The 100 %
partition overlap measured in §9.3.4 was an artifact of simulating P-1b, not a property of the
shipped generator.

**`init_noise_std` should be initialisable in the same manner as the generators' seed values** —
i.e. it falls under required-fix 2's constants / config-file / environment-variable treatment.

One consequence survives and is worth keeping visible: at default configuration the `seed` parameter
has **no effect on any returned array**, so a caller varying `seed` for replicate runs gets identical
data with no signal that the knob did nothing. That is a reproducibility-reporting concern, not a
partitioning one.

### 9.6.6 What closes, and what this does not cover

**Closed by this section**: the P-1a/P-1b question; the guard question; per-run class membership as a
*partitioning* concern; and the §9.4.7 recommendation, which the owner has now ruled on.

**Not covered**:

- Round 2 of the §9.4 consensus review was never run and is now **moot for decisions 9 and 10** — the
  disposition it would have re-examined has been decided directly. It remains unrun for §9.4's other
  content.
- The `partition_provenance` schema is described, not specified. Field names, types and the legality
  table are implementation work.
- No code has moved for decision 11's required-fix 0 or for decision 12's `partition_provenance`
  schema. Required-fixes 1–4 (and juniper-data#316) are **shipped**; only `*_full` removal remains.

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
