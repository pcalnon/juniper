# Train / Eval / Test partition — design of record

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
needs three**. `X_test` is being used as an in-loop signal because there is no `X_eval` to use.
The fix is to finish the partition design, not to pick an arm.

**Decision requested**: adopt a three-way `train` / `eval` / `test` split as the ecosystem data
contract, with `eval` consumed in-loop and `test` touched exactly once after training completes.
§6 lists the options; §7 the consequences; §9 the questions only the owner can settle.

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
| `eval` | early stopping, patience, best-checkpoint selection, LR schedules, any in-loop decision | every validation interval |
| `test` | the final reported score | **exactly once**, after training completes |

The invariant that makes it worth doing: **no quantity computed on `test` may influence any
decision made during training.** If a number is allowed to change what the run does, it is `eval`
by definition, whatever it is named.

Both arms consume the same three partitions, so the tiers become comparable by construction and
#578 reduces to a fixed-overhead question rather than a semantics question.

## 6. Options

### O-1 — juniper-data emits the third partition (recommended)

Add `X_eval`/`y_eval` to the NPZ contract alongside `X_train`/`y_train`, `X_test`/`y_test`,
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

**Recommendation: O-1**, with O-2's mechanism as the *fallback path* for artifacts that predate
the contract change (see below) — not as the primary design.

### Compatibility rule

Consumers must handle artifacts with and without the new keys, and must never silently guess:

1. `X_eval` present → use it for in-loop validation; `X_test` is reserved for the final score.
2. `X_eval` absent, `X_test` present → **either** refuse, **or** proceed with an explicit,
   recorded `validation_warnings` entry naming the fallback and marking the run's reported metrics
   as selected-on. Which of those is right is §9 Q3.
3. Neither present → refuse. The current "else the training split" fallback should be removed; it
   produces a number that looks like validation and is not.

The run manifest already carries `validation_warnings` (juniper-ml#1159 uses it for the
`max_epochs` / `output_epochs` footgun), so there is an existing channel for (2).

## 7. Consequences to plan for

- **Existing baselines shift.** Any change to what `train` contains, or to whether early stopping
  runs, moves results. The T6 re-baseline, the P3 thresholds and the attribution corpora were all
  measured under the current semantics.
- **Reported metrics change meaning, not just value.** After the change, `f1`/`roc_auc` become
  genuinely held-out. Comparing a post-change number to a pre-change one is a category error and
  should be blocked by provenance, not by convention — see §9 Q4.
- **Ratio of the split** is a live choice: 1000 → 800/200 today. A three-way split must decide
  whether to shrink `train` (e.g. 600/200/200) or re-generate at a larger N. Shrinking `train`
  changes the learning problem; the honest options are (a) accept the shift and re-baseline, or
  (b) hold `train` at 800 and generate 1000+ additional rows for `eval`.
- **Snapshot metadata** carrying metrics should record which partition each metric came from, so a
  future reader can tell a selected-on number from a held-out one without reading this document.

## 8. Proposed measurement before the change

Cheap and worth doing first: on the current build, run one cell and compute the final metric on
**both** the promoted `X_test` (as today) and a freshly held-out slice never seen by early
stopping. The gap is the bias this design removes. One cell, both arms, no new tooling beyond a
metrics hook — the same harness used for the tensor probe. Without it the design ships with an
unquantified motivation, and §7's "existing baselines shift" has no size attached.

## 9. Open questions for the owner

1. **Who owns the split — juniper-data (O-1) or cascor (O-2)?** Recommendation O-1.
2. **Split ratio, and does `train` shrink?** 600/200/200 from the existing 1000, or hold `train`
   at 800 and generate more rows.
3. **Legacy artifacts without `X_eval`: refuse, or proceed with a recorded warning?** Refusing is
   safer and louder; proceeding keeps the existing corpus runnable.
4. **Do pre-change results get retired, re-measured, or annotated?** They are not wrong, they
   answer a different question — but nothing currently distinguishes them.
5. **Should the CLI arm early-stop at all?** Giving it `eval` makes the tiers comparable; leaving
   it budget-bound keeps a deliberately unregularised reference. Either is defensible; the choice
   should be explicit rather than an artefact of the CLI never having been passed a val set.

## 10. References

- [cascor#582](https://github.com/pcalnon/juniper-cascor/issues/582) — tier parity (this document's origin)
- [cascor#578](https://github.com/pcalnon/juniper-cascor/issues/578) — baseline-tier decision (blocked on this)
- [cascor#572](https://github.com/pcalnon/juniper-cascor/issues/572) — global-stream roll defect (independent, confirmed 2026-08-29)
- `reports/tensor-hash-probe-2026-08-28/` — the probe, its evidence, and reproduce steps
- Ecosystem data contract — `Juniper/CLAUDE.md` § Data Contract (`X_train`, `y_train`, `X_test`, `y_test`, `X_full`, `y_full`)
