# Train / Validation / Test partition — design of record

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (juniper-data → juniper-data-client → juniper-cascor)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-29
**Status**: DESIGN — owner decision required before any code moves
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
