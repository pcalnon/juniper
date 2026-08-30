# The two gated measurements — results

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (juniper-cascor)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-30
**Status**: RESULTS — both designs gated implementation on these; **both results change their designs**
**Measured at**: cascor `67d7ea35` (cap 4, logging) and `64ff9ab8` post-#598 (cap 16); probes on diag branches `diag/tensor-hash-probe-572` and `diag/valsplit-cap16-582` (neither for merge)
**Evidence**: `reports/measurements-2026-08-29/`

---

## 1. Why this document exists

Two design documents each declined to proceed without a measurement first:

- [Partition design](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md) §8 —
  *"the design ships with an unquantified motivation"* without measuring the selection bias.
- [Logging design](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md) §5 / owner
  decision 1 — the 18 % + 15 % headline is *"a ceiling, not a recovery"* until the discarded-record
  share is known.

Both have now been measured. **Both results contradict their design's framing**, which is the
argument for the gate having been worth imposing.

---

## 2. Selection bias (cascor#582) — real mechanism, effect bounded below ~2 pp at two budgets

### Method

Suite `util/experiments/suites/p4/e-o-val-split-bias-cap4.yaml` — 8 cells, dataset seeds 42–49,
network seed held at 42, cap 4. Under `JUNIPER_DIAG_VAL_SPLIT=1` the diag branch halves the incoming
validation set: the **first** half drives training exactly as the full set does today (early
stopping, patience, best-val-loss); the **second** half is stashed and never seen by any training
decision. Both halves are then scored on the **same final model**.

Both halves come from one partition and are identically distributed. The only asymmetry is whether
the training loop was allowed to look at them, so `acc_selected_on − acc_held_out` is a paired
estimate of the optimism.

### Result

| ds seed | selected_on | held_out | optimism |
| --- | --- | --- | --- |
| 42 | 0.5900 | 0.5500 | **+0.0400** |
| 43 | 0.5600 | 0.5800 | −0.0200 |
| 44 | 0.5600 | 0.5400 | +0.0200 |
| 45 | 0.5600 | 0.5400 | +0.0200 |
| 46 | 0.6600 | 0.6100 | **+0.0500** |
| 47 | 0.6400 | 0.6400 | 0.0000 |
| 48 | 0.5900 | 0.6400 | −0.0500 |
| 49 | 0.5700 | 0.5600 | +0.0100 |

**mean optimism +0.0088, sd 0.0323, n=8; 95 % CI [−0.0136, +0.0311] — the interval INCLUDES ZERO.**
5 cells positive, 1 zero, 2 negative. 8/8 cells reported; nothing missing.

### cap 16, n=20 — measured 2026-08-30, and it REFUTES this document's own caveat

The cap-4 section below argued that cap 4 is *"the weakest case, so this is a lower bound"* —
selection pressure scales with the number of decisions taken against the partition, so a larger
budget should show a larger bias. **That prediction was tested and is wrong.**

Suite `util/experiments/suites/p4/e-p-val-split-bias-cap16.yaml`, 20 dataset seeds (42–61), network
seed held at 42, cap 16, on the post-#598 build:

| | cap 4 (n=8) | **cap 16 (n=20)** |
| --- | --- | --- |
| mean optimism | +0.0088 | **+0.0055** |
| sd | 0.0323 | 0.0353 |
| se of mean | 0.0114 | **0.0079** |
| 95 % CI | [−0.0136, +0.0311] | **[−0.0100, +0.0210]** |
| sign split | 5 + / 1 zero / 2 − | **10 + / 0 zero / 10 −** |

**An exactly even 10/10 sign split** is about as close to "no effect" as a paired sample gets, and
the mean went *down* with more selection pressure, not up.

**Vacuity control passed, and more strongly than at cap 4.** A cap-16 run performs **16**
early-stopping evaluations (15 `Stop Training Early: False` plus one `True`) with the patience
counter reaching 2, against ~4 at cap 4. So the mechanism was exercised four times harder and the
bias still did not appear. This is a real test of the pressure hypothesis, not a failure to engage.

**Upper bound.** With se = 0.0079, an effect larger than about **2.1 pp** is excluded at 95 %
confidence. That is now the useful quantitative statement: not "the bias is zero", but "if there is
one at these scales it is smaller than ~2 points, and two independent samples at different budgets
both fail to distinguish it from zero."

**Accuracies are much higher at cap 16** (mean 0.789 vs 0.591), so this is not a case of the model
failing to learn and the metric being noise-dominated for that reason.

### What this does and does not say

**It does not establish a nonzero bias at this scale.** The mean is in the predicted direction and
that is all. The partition design's §4A — *"the magnitude is unmeasured, but the direction is not
in doubt"* — was right about the mechanism and should not be read as promising a measurable
inflation: at cap 4 with 100-row halves, there isn't one that this sample can see.

**Why the noise dominates, quantitatively.** A single accuracy over 100 rows has
se ≈ √(0.25/100) = 0.05; the difference of two has se ≈ 0.07. Over 8 cells the se of the mean is
0.0114 — which matches the observed 0.0323/√8 exactly. To resolve a 1 pp effect you would need
se ≈ 0.005, i.e. roughly **n ≈ 40 cells** at this eval size, or materially larger eval partitions.

**The first cell was not representative.** `+0.0400` at seed 42 is the second-highest of eight. Had
this been run at n=1 — as the design's "run one cell" wording invited — it would have reported
"+4 percentage points of optimism" and that would have been wrong. This is the
[2026-08-24 handoff §5.1] class ("no small sample supports a mechanism claim") caught prospectively
rather than in post-mortem.

**Vacuity control passed.** Early stopping genuinely engaged — `Stop Training Early: True` appears
in the run logs alongside an incrementing patience counter — so the selected-on half really was
selected on. Had early stopping never fired, there would have been no selection and the whole
measurement would have been hollow while still producing plausible numbers.

**~~cap 4 is the weakest case, so this is a lower bound.~~ SUPERSEDED 2026-08-30.** The original
argument was that selection pressure scales with decisions taken against the partition, so cap 16
or 64 should show more. Measured at cap 16 with n=20 and 4x the early-stopping evaluations: the
mean optimism *fell* to +0.0055 with an exactly even 10/10 sign split. The pressure hypothesis is
refuted at this range; see the cap-16 subsection above. Cap 64 remains unmeasured.

### Consequence for the partition design

**The motivation is methodological, not performance.** The correct argument for the three-way split
is that selection and reporting must not share rows — which is a fact about the pipeline, provable
without statistics, and independently sufficient. It is **not** "the reported numbers are inflated
by N points", and the design should not claim that.

On its own this would *reduce* the urgency of decision 4 (re-measure pre-change results): if the
bias is under ~2 pp, the existing corpus is not materially wrong, only methodologically unsound.

**But decision 4 is required anyway, for an unrelated reason.** V-1 (measured 2026-08-30) found
that all six cascor-relevant generators produce **different rows** when asked for N+M vs N at the
same seed — see the partition design §6.3. So adopting the three-way split moves every baseline's
*data*, regardless of how small the selection bias turns out to be. Decision 4 stands as
**required**; what changed is why. It is not "the old numbers were inflated" — they were not,
measurably — it is "the old numbers describe different data."

~~Open: repeat at cap 16 with n ≥ 20.~~ **DONE 2026-08-30** — see the cap-16 subsection above.
Cap 64 remains unmeasured, but two budgets differing 4× in selection pressure both return intervals
containing zero, so a cap-64 run is no longer the obvious next question.

---

## 3. Logging cost (cascor#573) — the design's priority order was backwards

### Method

No new run. The design's own guardrail G-1 said the honest instrument is caller attribution from
the existing worker profile corpus rather than a name-based grep, and that corpus already exists —
32 profiles at `67d7ea35`. `util/ad-hoc/2026-08-29_format_caller_attribution.py` walks
`pstats.Stats.stats`' caller→callee edges and sums per-caller cumulative time.

This supersedes the "run one cell with logging disabled" proposal and answers the question better:
a disabled-logging A/B gives *total* logging cost but cannot separate discarded from emitted
records, which is precisely the split that was being asked for.

### Result — decomposition over 84.96 s of worker self time

| component | calls | time | share | paid for |
| --- | --- | --- | --- | --- |
| `Tensor.__format__` chain | 2,262 → 1.81 M | 27.98 s cum | **33 %** | **emitted records only** |
| `_filter_by_level` | 646,016 | **11.19 s** | **13.2 %** | **every call — 91 % discarded** |
| `strftime` | 116,798 | 0.99 s | 1.2 % | emitted only |
| `currentframe` (eager) | 646,016 | 0.87 s | 1.0 % | every call |

Logger calls by level, exact and complete (sums to 646,016):
`trace` 264,784 · `debug` 264,223 · `verbose` 58,610 · `info` 58,399.

**91.0 % of logger calls are discarded** (587,617 of 646,016) at the INFO level these runs used.

### The finding that inverts the design

The 1.81 M `Tensor.__format__` calls come from **one function** —
`candidate_unit.py:_display_training_progress` — and specifically from **one line**, at **INFO**:

```python
if self._candidate_display_progress(epoch):
    self.logger.info(f"CandidateUnit: train: Epoch {epoch + 1} - Norm Output: {candidate_parameters_update.norm_output}, Norm Error: {candidate_parameters_update.norm_error}")
```

`norm_output` and `norm_error` are declared `torch.Tensor`. Arithmetic confirmation, not inference:
the run log contains **1,131** emitted `Norm Output:` lines × 2 tensors = **2,262**
`Tensor.__format__` calls — exactly the attributed count. The log contains **zero** VERBOSE records,
so the neighbouring unguarded `logger.verbose` line contributed nothing.

**So the dominant formatting cost is at an ENABLED level.** It is not a discarded record. No amount
of call-site guarding, lazy `%`-args or lazy callables recovers it, because the record is emitted.
The design's F-1 — "the level filter cannot prevent the work" — is a correct statement of mechanism
that turns out **not** to describe where the cost actually is.

### Revised priority order

| # | action | measured value | kind of fix |
| --- | --- | --- | --- |
| 1 | Stop formatting whole tensors into the INFO line — log a shape and a scalar norm, not the tensor | **~28 s / 33 %** | **one line**, content not timing |
| 2 | Make `_filter_by_level` cheap (resolve levels to ints once; drop per-record `_is_valid_level_name`) | **11.19 s / 13.2 %** | logger-internal (design F-4) |
| 3 | Move `frame`/`tsp` inside `_log_at_level` | 0.87 s / 1.0 % | logger-internal (design F-1) |
| 4 | Call-site migration (guards / lazy args) | **small** — the only expensive interpolation is item 1, which guards cannot help | call sites |

**The call-site migration drops from headline to last place.** The
[call-site analysis](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md)
recommended migrating ~146 hot sites; this measurement says the top two items are *one line* and
*one function*, and neither is in that set. Its own guardrail G-1 predicted this risk explicitly —
*"if G-1's real measurement contradicts the grep, this recommendation changes"* — and it did.

Item 2 is the genuinely large recoverable number, and it is a **logger-internal** fix requiring no
call-site changes at all: 13.2 % of worker self time is spent deciding whether to log, on calls that
91 % of the time then log nothing.

### Residual uncertainty, stated

f-string *construction* cost for the 587,617 discarded records is inline in each calling function's
own self time and is therefore **not separately attributable** from this corpus. It is bounded small
by the finding that the only expensive interpolation in the hot path — tensor formatting — is
entirely in the emitted INFO line. A true bound would need a build with the log calls removed
outright, which is not cheaply obtainable; raising `CASCOR_LOG_LEVEL` does **not** measure it,
because arguments are evaluated at the call site regardless of level.

---

## 4. What changes in the two designs

**Partition design**: §4A's framing softens from "biased, magnitude unknown" to "methodologically
unsound, magnitude not resolvable at cap 4"; §8's proposed measurement is done; decision 4's urgency
drops. The design's substance — juniper-data owns a third partition, `train` does not shrink — is
unaffected, because it never depended on the magnitude.

**Logging design**: §5's payoff table is replaced by §3 above; the priority order inverts; owner
decision 1 (measure first) is discharged. Owner decisions 2–6 are unaffected — they concern sinks
and levels, not what gets interpolated.

## 5. References

- `reports/measurements-2026-08-29/val_split_bias_cap4_n8.txt` — the 8-cell table and statistics
- `reports/measurements-2026-08-29/format_caller_attribution.txt` — the three attribution runs
- `util/experiments/suites/p4/e-o-val-split-bias-cap4.yaml` — the suite, with its design rationale
- `util/ad-hoc/2026-08-29_val_split_bias_collect.py` — collector (reports MISSING cells, never counts them as zero)
- `util/ad-hoc/2026-08-29_format_caller_attribution.py` — caller attribution over a cProfile corpus
