# CLI Experimentation — seeded-run reproducibility, characterised at N=20

**Project**: juniper-ml (ecosystem) · **Author**: Paul Calnon · **Created**: 2026-08-20
**Defect**: [juniper-cascor#532](https://github.com/pcalnon/juniper-cascor/issues/532)
**cascor SHA (both arms)**: `4bec1beff89b6b14ca00d06a9ecdc7c85f0ebdcb` (post-#533, post-#539)
**Predecessor**: [`JUNIPER_2026-08-16_…WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md)

---

## 1. Why the instrument had to change shape before anything could be measured

Identically-seeded cascor runs do not reliably reproduce. That was known. What was *not* available
was any honest number attached to it, and the reason is worth stating plainly because it shaped
every tool built here.

The effect fires in roughly **half of run-pairs**. Against an effect like that:

- two runs that agree are not evidence of determinism;
- two runs that differ are not evidence of a mechanism;
- and a tool whose output is the word `DETERMINISTIC` or `NONDETERMINISTIC` over an `(a, b)` pair
  will, with high probability, print a confident answer that is wrong.

Three claims in this investigation were made and withdrawn on exactly that error — *"the 19.5 pp
accuracy spread is monotonic in thread count"* (three ordered points), *"the service is
deterministic, the CLI is not"* (two service runs), and *"every divergence lands on one of two
values at iteration 2"* (one thread configuration). A fourth near-miss: the predecessor tool once
reported a confident `NONDETERMINISTIC` verdict by diffing a still-running log against a finished
one.

So the first deliverable is not a number, it is an instrument that **cannot express a verdict over
a pair**: [`util/ad-hoc/2026-08-20_determinism_nrun.py`](../util/ad-hoc/2026-08-20_determinism_nrun.py)
reports a rate over N runs with an interval, and names every run it excluded rather than dropping
it silently.

### 1.1 What the headline statistic is, and why it is the right one

`pair_divergence_rate` = the fraction of the C(N,2) unordered run-pairs whose fingerprints differ.

Two properties make this the right choice rather than a convenience:

1. **It is in the same units as the original observation.** #532 opened on "3 of 5 run-pairs
   diverged". A rate over pairs is directly comparable; a count of distinct outcomes is not.
2. **It is an unbiased estimator, not just a description.** If runs are i.i.d. draws from a
   distribution over outcomes, the pairwise agreement rate is an unbiased U-statistic for
   `P(two independent runs agree)` — the collision probability `Σ p_k²`.

Its sampling variance, however, is **not** binomial: the C(N,2) pairs share runs and are therefore
not independent, so a binomial interval on `n_divergent / n_pairs` would be far too narrow. The
interval reported is a **run-level bootstrap** — resample the N runs with replacement, recompute
the rate — which is the correct procedure for a U-statistic and is what makes a rate near 0.5 at
N=20 mean something a rate near 0.5 at N=4 does not.

`distinct_outcomes` and the outcome histogram are reported alongside, because a rate near 1.0 means
something very different coming from two near-equal clusters than from twenty singletons.

### 1.2 What counts as an "outcome"

The fingerprint is the **full per-iteration `grow_network` trace** — the ordered tuple of
`(iteration, train_loss, train_accuracy, early_stop)` strings exactly as logged.

Final accuracy alone is too coarse: a cap-4 run has only three logged iterations, and two
genuinely different trajectories can land on the same rounded endpoint. Log strings are compared
rather than parsed floats, so the fingerprint is exactly what the run recorded.

---

## 2. Design

### 2.1 Cap 4, and why that is not a corner-cut

Divergence appears inside the first two or three growth iterations — established, not assumed: runs
are bit-identical through iteration 1 and first differ at iteration 2 in some pairs, at iteration 1
in others. Cap 16 buys no extra signal about *whether* runs diverge; it buys 25-minute runs.

Cap 4 reproduces the phenomenon in a few minutes, which is what turns determinism from something
affordable once into something affordable twenty times. Repeated trials are the only thing that
says anything sound about a stochastic effect, so the cap is chosen to buy trials.

### 2.2 Both arms, at one recorded SHA

The service arm is 20 cells of
[`util/experiments/suites/p4/e-l-determinism-cap4.yaml`](../util/experiments/suites/p4/e-l-determinism-cap4.yaml);
the direct-CLI arm is 20 runs of the cell that suite materialises, through
[`util/ad-hoc/2026-08-17_h2h_thread_probe.bash`](../util/ad-hoc/2026-08-17_h2h_thread_probe.bash).

[`2026-08-20_determinism_campaign.bash`](../util/ad-hoc/2026-08-20_determinism_campaign.bash)
**refuses to start** if the two checkouts are at different commits. That guard is not ceremony: an
earlier CLI arm was silently run from a pre-#533 worktree, which re-inserted `main.py`'s BLAS cap
into one arm only and invalidated the comparison. Both arms here are `4bec1be`.

### 2.3 The replicate axis, and the trap inside it

`run_suite` has no replicate primitive. The 20 cells come from a 20-valued
**`experiment.description`** matrix axis — the only config key that is legal (driver
`EXPERIMENT_KEYS`), inert (recorded on the manifest, never sent to any service), and free of side
effects.

`seed_policy` **must** stay `fixed`. `per_cell` rewrites both seeds to `base_seed + cell.index`,
which would silently turn a 20-replicate expansion into a **20-seed sweep** and report a false
"20 distinct outcomes, 100% nondeterministic" — the precise conclusion the suite exists to test.

### 2.4 A configuration key that reads as a control and is not

`runtime.blas_threads: 2` appears in the shared base config. It is validated by the driver
(`RUNTIME_KEYS`, `run_experiment.py:161`) and **applied nowhere** — no consumer exists in
`run_experiment.py`, `experiment_stack.bash`, or cascor. Verified at runtime: the live cascor
service process carries no `OMP_NUM_THREADS` / `MKL_NUM_THREADS` / `OPENBLAS_NUM_THREADS` at all.

Both arms therefore run at the host BLAS default. That is the correct state for this comparison,
but it is true by accident rather than by configuration, and anyone reading the base config would
reasonably conclude the opposite.

---

## 3. Where the divergence originates

This is the part that does **not** depend on the rate, and it is where the existing code leads go
to die.

### 3.1 The two hypotheses, and why the end-to-end trace cannot separate them

- **(a) Candidate math** — the eight candidates train to different correlations run to run.
- **(b) Selection** — candidates train identically, but a different one is installed, because
  `_process_training_results` sorts an **arrival-ordered** list with a **stable** sort keyed only on
  `(correlation is not None, |correlation|)`, so an exact tie is broken by whichever worker finished
  first.

Both produce the same downstream symptom — a trajectory that separates and amplifies. Per-candidate
correlations, already logged at INFO, can separate them;
[`2026-08-20_determinism_localize.py`](../util/ad-hoc/2026-08-20_determinism_localize.py) does that,
comparing correlations as a **sorted multiset** (log order is worker arrival order and therefore
timing-dependent by construction — comparing unsorted would report a difference on every pair and
answer nothing).

### 3.2 The arrival-order tie-break is exercised constantly and has never caused a divergence

Over the eight available post-#533 cap-4 runs (28 pairs):

| observation | count |
|---|---:|
| pairs where the pool completed in a **different order** on a round whose sorted correlations are equal | **28 / 28** |
| pairs that are byte-identical downstream **anyway** | 15 |
| divergent pairs localising to **candidate math** | 13 |
| divergent pairs localising to **selection given equal correlations** | **0** |

The pool genuinely reorders in every single pair. In 15 of them the outcome is byte-identical
regardless. The stable-sort tie-break is therefore being exercised continuously and is not what
separates the divergent pairs from the identical ones.

> **A correction to this document's own instrument.** The first version of the localiser tracked
> arrival order as the sequence of candidate **UUIDs**. `CandidateUnit` mints a fresh
> `uuid.uuid4()` per instantiation (`candidate_unit.py:1154`), so two runs never share a UUID
> sequence: the check reported "arrival order differs" for 100% of pairs *including bit-identical
> ones*. A check that cannot fail measures nothing, and this one was load-bearing. It now compares
> the arrival-ordered sequence of correlation **values**, and only counts a reordering when the
> sorted multiset for that round is equal — same multiset, different sequence, i.e. a genuine
> permutation. The corrected check makes the refutation stronger, not weaker.

### 3.3 What survives regardless of precision: the proposed secondary sort key is not the fix

A deterministic secondary key (e.g. on `candidate_id`) engages **only on an exact tie**. Floats that
differ anywhere below the primary key's resolution are already ordered by the primary key. No
divergence observed here required an exact tie, so this fix would have prevented none of them.

### 3.4 What is NOT established — the precision limit

`CandidateUnit.train` logs its correlation with `:.6f` (`candidate_unit.py:670`). "Identical
correlations" above therefore means **identical to six decimal places**, and in this cell that
is a live limitation rather than a pedantic one:

- the top two round-0 correlations are **`0.091185`** and **`0.091184`** — adjacent at the printed
  precision;
- round 0 is byte-identical across all eight runs at that precision;
- round-1 correlations in the divergent pairs differ by **tens of percent** (`0.034541` vs
  `0.021808`), not by float jitter — and **all eight** differ, which is what a changed candidate
  *input* looks like, not what per-candidate arithmetic jitter looks like.

That pattern is consistent with a **sub-1e-6 difference flipping a near-tie at round 0**, installing
a different hidden unit, and every later round then seeing a different candidate input. The
localiser would classify such a pair as "candidate math", because round 1 is where it first sees a
difference, even though the operative event was a selection flip one round earlier.

Settling it needs the installed candidate's identity, and **no current log carries it**:
`_add_best_candidate` interpolates `{best_candidate}` — a `CandidateUnit` with no `__repr__` — so
what reaches the log is a memory address (`cascade_correlation.py:4850`). It identifies nothing and
differs every run.

### 3.5 The parent side is exonerated to logged precision

The output-layer pass losses run *ahead* of the first differing correlations and agree until after
them:

| pass | `unset-a` | `unset-b` |
|---|---|---|
| initial | 0.246147 | 0.246147 |
| after iteration 0 | 0.239272 | 0.239272 |
| after iteration 1 | **0.235021** | **0.235058** |

Round-0 candidate correlations: identical. Round-**1** candidate correlations: differ. The output
pass that *feeds* round 1 (`0.239272`) is identical in both. So the candidate workers were handed
the same inputs, to logged precision, and returned different correlations — the divergence is on
the worker side of that boundary, not in the parent's output-layer training.

The same 6-dp caveat applies: identical printed loss does not prove identical weights.

---

## 4. Results

Suite `e-l-determinism-cap4-20260820T080932Z`, 20/20 cells `succeeded`. Direct-CLI arm under
`~/.local/state/juniper-experiments/determinism-n20/cli-*`, one stack
(`20260820T100406Z-d4da`, `DATA_URL` verified against that run's own `ports.json` before the arm
proceeded). All cells resolved the same content-addressed dataset
`spiral-1.0.0-cc74e49e366cfc9f`.

### 4.1 Service arm — deterministic, 0 / 190 pairs

| statistic | trace fingerprint | correlation fingerprint |
| --- | --- | --- |
| runs | 20 | 20 |
| pairs | 190 | 190 |
| **divergent pairs** | **0** | **0** |
| rate (95% CI, run-level bootstrap) | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| distinct outcomes | **1** | **1** |

Every one of the 20 runs produced the identical trajectory:

```
Iteration 0 - Train Loss: 0.239994, Train Accuracy: 0.6088, Early stop: False
Iteration 1 - Train Loss: 0.239165, Train Accuracy: 0.5713, Early stop: False
Iteration 2 - Train Loss: 0.235091, Train Accuracy: 0.5913, Early stop: False
```

and the identical **11,360** candidate epochs (`sd = 0`, cv 0.0%) and the identical 32 candidate
correlations per run, round by round.

Two things make this stronger than the count alone:

1. **It holds on the finer fingerprint.** A rate of 0 on the logged iteration trace would not by
   itself be a determinism result — a cap-4 run trains 32 candidates but logs only 3 iterations,
   and the final candidate round never gets an iteration line. The correlation fingerprint covers
   all 32, and it is also 0/190.
2. **It holds across a cascor code change.** The 2026-08-18 service run of the same cell, on the
   **pre-#539** tree, produced a byte-identical trace. That is 21 runs across two trees with one
   outcome, and it independently confirms #539 (`_adopt_prior_output_optimizer_state`) is inert for
   a fresh fit — on a grow pass the output parameter space changes every call, so the adopt branch
   never fires.

**This retires the withdrawn claim properly.** *"The service is deterministic"* was asserted on two
agreeing runs and correctly withdrawn as unsupported against a ~50%-of-pairs effect. At 190 pairs on
two independent fingerprints it is now supported — for this cell, this cap, this seed, this host.
It also discharges the open caveat on **#533**'s safety check, which rested on the same two runs:
the service tier's behaviour is unchanged and stable at N=20.

### 4.2 Direct-CLI arm (N=20)

<!-- PENDING — in flight. -->

### 4.3 Cross-arm

<!-- PENDING — in flight. -->

### 4.4 What the timing columns show, and why they are still not a noise floor

Worth reading precisely because it is such a clean demonstration of §5.1. Across the 20 service
runs:

| quantity | mean ± sd | cv |
| --- | --- | ---: |
| candidate **epochs** | 11360 ± 0 | **0.0%** |
| training **span** | 311.0 ± 209.5 s | **67.4%** |
| s / candidate epoch | 0.02659 ± 0.01769 s | 66.5% |

The work is *byte-identical* — same epochs, same correlations, same trajectory, twenty times over —
and the wall clock still ranges from **825 s to 190 s**, a 4.3× spread. Every bit of that is the
host: the early cells ran against a concurrent training stack and a 21-hour `clamscan` at load ~38,
the later ones at load ~6.

A 67% cv is not the trainer's noise floor, it is a busy laptop's. Reporting it as one would size
the §4 residual measurement against an interval more than an order of magnitude too wide.

---

## 5. Honest limits

### 5.1 The timing figures in this campaign are NOT publishable as a noise floor

The campaign ran on a host under heavy, uncontrolled, *time-varying* contention: a 21-hour
`clamscan` at ~84% of a core, a `nethogs` at ~98% for three days, a concurrent Claude session
running its own full cascor + juniper-data + canopy stack and actively training, and Chrome. Load
average reached **38 on 16 cores**.

Per-cell wall time moved from 907 s to 756 s across the first three cells of one arm on identical
work — a ~17% swing driven entirely by what else the host was doing. The measured `sd` is therefore
dominated by contention, not by the trainer.

Consequence, stated as a decision rather than a caveat: **the span / candidate-phase / throughput
figures here must not be used to size the residual wall-gap measurement.** That noise floor needs a
quiet host and is deferred. The divergence *rate* is unaffected — the fingerprint is a function of
the arithmetic, not of how long it took.

Host load was sampled throughout
([`2026-08-20_load_sampler.bash`](../util/ad-hoc/2026-08-20_load_sampler.bash)) so the contention is
attributable rather than mysterious.

### 5.2 The rate itself may be load-dependent

If the mechanism is scheduling variability under an oversubscribed thread pool, then the *rate* is
plausibly a function of host load too. A rate measured at load 38 is not necessarily the rate at
load 2. This is a genuine external-validity limit and is not resolved here.

### 5.3 Cross-arm accuracy provenance

`train_acc` / `val_acc` are the last two `calculate_accuracy` records. On the CLI arm these come
from `SpiralProblem.evaluate`'s post-fit pair; on the service arm from `fit`'s own call sites. Same
function, different provenance — fine *within* an arm, which is all the divergence rate uses, but a
cross-arm accuracy delta must not be read off this field without confirming the two measure the
same thing.

### 5.4 Sample size is 20, and 20 is not large

At a true rate near 0.5, the run-level bootstrap interval at N=20 is still wide. The claim this
campaign supports is "the rate is in this interval", not a point estimate. Where the interval is
reported, it is reported.

---

## 6. A defect found in the instrumentation itself

[`2026-08-16_h2h_phase_split.py`](../util/ad-hoc/2026-08-16_h2h_phase_split.py) — the tool that
produced the published cap-16 candidate/output phase split — was anchored on emitting **source line
numbers** (`train_candidates:2166`, `train_output_layer:2100`, `train_output_layer:2120`).
juniper-cascor#539 shifted `cascade_correlation.py` by ~90 lines, and all three now point at
statements that log nothing. On any current log the tool reported `nothing parseable`.

That it failed loudly was luck, not design: `analyse()` bails only when **both** phase lists are
empty, so a shift breaking one anchor and sparing the others would have produced a confident,
silently wrong phase split. Re-anchored on message text; verified it still reproduces the published
**1103 s** CLI candidate phase on the original cap-16 logs.

The same class of failure is why the N-run harness asserts its derived counts are non-zero and exits
non-zero on a stale anchor rather than reporting a clean 0.

---

## 7. Reproduction

```bash
export JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper   # load-bearing from a worktree
export JUNIPER_EXP_HEALTH_TIMEOUT=180                                    # stack default 90 is too short

# 0. a DEDICATED cascor checkout at the SHA both arms will use (a shared checkout's parent log
#    rotates out from under the run; that is how an earlier arm's evidence was lost)
git -C juniper-cascor worktree add --detach <WT> origin/main
git -C <WT> rev-parse HEAD          # record this; the driver refuses if the arms disagree

# 1. both arms, strictly sequential (the driver enforces the SHA match and the sequencing)
util/ad-hoc/2026-08-20_determinism_campaign.bash <WT>/src 20

# 2. the rate, per arm
python util/ad-hoc/2026-08-20_determinism_nrun.py \
    --arm service <SUITE_RUN_DIRS...> --arm cli <OUT_ROOT>/cli-* --json rate.json

# 3. where it diverges
python util/ad-hoc/2026-08-20_determinism_localize.py <RUN_DIRS...>
```

### 7.1 Teardown attestation

<!-- PENDING -->

---

## 8. Disposition

<!-- PENDING — §3.7 outcome: (a) fixed, or (b) characterised and accepted. -->
