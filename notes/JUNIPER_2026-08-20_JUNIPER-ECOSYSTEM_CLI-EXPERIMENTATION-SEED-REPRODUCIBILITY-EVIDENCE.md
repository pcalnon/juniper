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

### 3.4 What is NOT established from shipped logs — the precision limit

> **Resolved in §3.6 by an instrumented build.** The hypothesis raised here turned out to be
> **wrong**, which is exactly why it was worth building the instrument rather than reasoning
> further. Kept as written because the reasoning that motivated the instrument is the useful part.

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

### 3.6 Resolved with exact floats — the near-tie hypothesis is refuted

A diagnostic cascor build ([`2026-08-20_cascor_candidate_identity_diag.patch`](../util/ad-hoc/2026-08-20_cascor_candidate_identity_diag.patch))
adds two INFO records: per candidate, its `candidate_index` with the **full-repr** correlation and
epoch count; per installed unit, the iteration and `installed_index`. Eight CLI runs, read by
[`2026-08-20_determinism_diag.py`](../util/ad-hoc/2026-08-20_determinism_diag.py):

| over 105 pair-rounds, to first difference | count |
| --- | ---: |
| rounds identical (index→correlation map **and** installed index) | 92 |
| **NEAR-TIE FLIP** (identical correlations, different unit installed) | **0** |
| **JITTER** (same `candidate_index`, different correlation) | **13** |

Rounds 0 and 1 are bit-identical in all eight runs — installed index `7` then `3`, at correlations
`0.09118530330282648` and `0.07080879140992169` **to the last digit**. No ordering change occurs
anywhere in the campaign.

**Both of #532's original code leads are therefore dead**, on independent grounds: the arrival-order
tie-break is exercised in 189/190 pairs without ever causing a divergence (§4.2b), and no exact or
near tie is ever resolved differently.

### 3.7 What actually varies — a shared input, not per-worker noise

"Jitter" is too vague for what the DIAG records show. When round 2 first differs between two runs,
**all 8 of 8 candidates differ** — they did not independently wobble, their common input changed.
Tracing the boundary:

| | run-1 | run-3 |
| --- | --- | --- |
| output pass feeding round 2 | `0.235021` | `0.235021` |
| round-2 candidate `index=0` | `0.022853421257993008` (118 epochs) | `0.023402814673351112` (126 epochs) |
| output pass **after** round 2 | `0.229579` | `0.228024` |

So the perturbation is **below 6 dp when it enters the candidate pool** and plainly visible after
it. The amplifier is candidate early stopping: the same candidate runs 118 epochs in one run and
126 in the other, and a patience-based stop is a discontinuous function of a continuous quantity.

That is the signature of a sub-precision difference in the **parent's** output-layer weights, not of
arithmetic noise inside the workers.

### 3.8 Thread count is NOT the driver — a hypothesis of this document, refuted

An intervention arm at `OMP_/MKL_/OPENBLAS_NUM_THREADS=1`:

| arm | correlation-fingerprint rate | 95% CI |
| --- | ---: | --- |
| CLI baseline (N=20) | 0.768 | [0.553, 0.847] |
| CLI at `threads=1` (n=6) | **0.600** | [0.000, 0.800] |

Capping BLAS to a single thread does not fix it, and the intervals overlap heavily — no thread
effect is demonstrated.

Recording this as a correction, because an earlier reading in this investigation went the other
way. Eight historical cap-4 runs split 0/6 divergent pairs at bounded thread counts against 5/6 at
unset, which looked like a clean modulation. It was four runs per group. §6's rule — *no small
sample supports a mechanism claim on a ~50%-of-pairs effect* — applies to the analyst as readily as
to anyone else, and #532's own body had already declined to claim a thread effect on the same data.

The refutation is informative rather than merely negative: with MKL single-threaded, the remaining
multithreading in the training path is the **parent's** ATen pool, which
`torch.set_num_threads(max(2, worker_thread_count * 2))` floors at **2** and which no environment
variable reaches.

### 3.9 The cause — the two entry points run `fit()` on different threads

One structural difference survives every check. The service executes training on a worker thread:

```python
self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cascor-train")
# api/lifecycle/manager.py:2237 — and then self.model.fit(...) at :2359
```

The direct CLI calls it inline, on the **main** thread (`main.py`, `sp.evaluate(...)`). Everything
else matches: same commit, same materialised cell, same content-addressed dataset, same 7-process
candidate pool, same (unset) BLAS environment.

This is a plausible cause rather than a coincidence. OpenMP's `nthreads-var` is a **per-thread**
internal control variable, and `torch.set_num_threads()` sets it for the *calling* thread. A `fit()`
running on a different thread from the one that configured the pool therefore meets parallel regions
under a different thread count than the main-thread path does — which changes how reductions are
split, and hence their floating-point accumulation order.

**Tested directly.** A second diagnostic build
([`2026-08-20_cascor_thread_context_diag.patch`](../util/ad-hoc/2026-08-20_cascor_thread_context_diag.patch))
wraps the CLI's `sp.evaluate(...)` in the same executor shape and changes nothing else:

| CLI arm | runs | pairs | trace rate | **correlation rate** |
| --- | ---: | ---: | ---: | ---: |
| baseline — `fit()` on the main thread | 20 | 190 | 0.632 | **0.768** [0.553, 0.847] |
| probe — `fit()` on a pool thread | 6 | 15 | 0.000 | **0.000** |
| **verification — same probe** | **20** | **190** | **0.000** | **0.337** [0.100, 0.505] |

**Read the third row, not the second.** At n=6 the probe looked like a complete fix — 0/15 on both
fingerprints. At N=20 the trace rate is still 0, but the correlation fingerprint finds **64 of 190
pairs** divergent. The screen was not wrong, it was underpowered, and it is the second time in this
campaign that a six-run result would have been published as a clean zero.

So the honest statement is a **large mitigation, not a cure**: thread context is a dominant
contributor — it removes trace-level divergence entirely and cuts the correlation rate by more than
half — but a residual mechanism survives it. Details in §4.4.

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

**And it is the cleanest available refutation of the tie-break lead.** Localising the service arm
returns `190 / 190 pairs agree` — alongside `pool reordered, same corrs: 190`. In other words the
candidate pool completed in a **different order in every single pair** of an arm that is
*perfectly* reproducible. Arrival order varies constantly and changes nothing; a defect that
tracked it would have shown up here first.

**This retires the withdrawn claim properly.** *"The service is deterministic"* was asserted on two
agreeing runs and correctly withdrawn as unsupported against a ~50%-of-pairs effect. At 190 pairs on
two independent fingerprints it is now supported — for this cell, this cap, this seed, this host.
It also discharges the open caveat on **#533**'s safety check, which rested on the same two runs:
the service tier's behaviour is unchanged and stable at N=20.

### 4.2 Direct-CLI arm — nondeterministic, 120 / 190 pairs

| statistic | trace fingerprint | correlation fingerprint |
| --- | --- | --- |
| runs | 20 | 20 |
| pairs | 190 | 190 |
| **divergent pairs** | **120** | **146** |
| **rate** (95% CI, run-level bootstrap) | **0.632** [0.416, 0.747] | **0.768** [0.553, 0.847] |
| distinct outcomes | **5** | **7** |

Outcome histogram (trace): `649f5366ac0c` ×11, `6bdea2933bc7` ×6, and three singletons.

**The trace fingerprint undercounts, exactly as anticipated in §1.2.** 26 pairs share a trace and
still did different candidate arithmetic. It is visible in the run table without any tooling: runs
`cli-08` and `cli-12` carry the modal trace fingerprint `649f5366ac0c` yet finish at
train 0.6613 / val 0.6300 where the other nine carry 0.6587 / 0.6350. A cap-4 run's **fourth**
candidate round has no `grow_network` line, so a divergence there is invisible to the trace and
lands only in the final accuracy. **Quote 0.768, not 0.632.**

### 4.2a Where it starts — never round 0

First divergent candidate round, over the 146 divergent pairs:

| round | pairs |
| ---: | ---: |
| 0 | **0** |
| 1 | 103 |
| 2 | 17 |
| 3 | 26 |

Round 0 is byte-identical across all 20 CLI runs and never begins a divergence. That is
structural, not luck: at round 0 the candidates see only the raw 2-D input, and from round 1 the
input carries the installed hidden activations and grows with the network. Whatever the mechanism
is, it does not engage at the smallest input width.

### 4.2b Localisation at N=20 reproduces the historical finding

| observation | pairs |
| --- | ---: |
| pool completed in a **different order** on a round whose sorted correlations are equal | **189 / 190** |
| pairs that agree completely | 44 |
| divergent pairs localising to **candidate math** | **146** |
| divergent pairs localising to **selection given equal correlations** | **0** |

Identical in shape to the 8-run historical set (§3.2), now at 190 pairs. The §3.4 precision limit
still applies to the "candidate math" attribution.

### 4.3 Cross-arm — the two paths do not start from the same state

This is *not* a reproducibility result; each arm is internally consistent about it. But it is
visible the moment both arms are put side by side on one cell, and it matters for §4 of the
successor arc, which compares the arms:

| | service | direct CLI |
| --- | --- | --- |
| iteration 0 train loss / accuracy | `0.239994` / `0.6088` | `0.239272` / `0.5775` |
| round-0 candidate correlations | `.032619 .032643 .032975 .033128` `.090884 .090908 .090983 .091058` | `.032521 .033113 .033281` `.091006 .091072 .091138 .091184 .091185` |
| candidate epochs (modal) | 11,360 | 10,510 |

Both arms ran the **same materialised cell**, resolved the **same content-addressed dataset**
(`spiral-1.0.0-cc74e49e366cfc9f`), on the **same cascor SHA**, and both default their network seed
to 42 (`_CASCOR_RANDOM_SEED` and `_CASCADE_CORRELATION_NETWORK_RANDOM_SEED` both resolve to
`_PROJECT_RANDOM_SEED = 42`). They nevertheless produce different candidates from round 0 — note
the *clustering* differs, 4+4 on the service against 3+5 on the CLI, so this is not a small
numerical offset.

The cause is **not identified here** and is out of scope for a reproducibility campaign. Recording
it because a wall-clock comparison between two arms that begin from different states is measuring
something other than the path difference, and the wide-budget campaign's equalisation doctrine
(which checked every key the config file can express) would not have caught it — the same blind
spot that hid the BLAS entry-point asymmetry in #531.

### 4.4 The thread-context mitigation, verified at N=20 — large, cheap, and incomplete

Direct CLI, `fit()` moved onto a `ThreadPoolExecutor` worker, nothing else changed, 20 runs:

| | baseline | with the mitigation |
| --- | ---: | ---: |
| trace-fingerprint rate | 0.632 | **0.000** |
| correlation-fingerprint rate | 0.768 [0.553, 0.847] | **0.337** [0.100, 0.505] |
| distinct trace outcomes | 5 | **1** |
| distinct correlation outcomes | 7 | **2** |
| training span | 280.8 ± 14.7 s | 282.9 ± 5.7 s |

**Cost: none measurable.** 282.9 s against 280.8 s, and the mitigated arm's span cv is *lower*
(2.0% vs 5.2%). Whatever this does, it is not buying reproducibility with throughput — unlike
capping BLAS threads, which #531 measured at up to 1.30× on the candidate phase (re-measured
rep-paired at k=3 on 2026-08-22: **1.016× [0.885, 1.148]** — no effect demonstrated) and which §3.8
shows does not work anyway.

**What survives, precisely.** The 20 runs split **16 / 4**:

| group | runs | train | val | candidate epochs |
| --- | ---: | --- | --- | ---: |
| A | 16 | 0.6637 | **0.6350** | 10,960 |
| B | 4 | 0.6625 | **0.6400** | 10,950 |

All 20 share one trace fingerprint because the three logged `grow_network` iterations are identical
in every run — the surviving divergence lives entirely in the **fourth and final candidate round**,
which never gets an iteration line. It is not cosmetic: it moves validation accuracy by **0.5 pp**
and candidate work by 10 epochs. A campaign reading only the iteration trace would call this arm
perfectly reproducible and be wrong about the number it actually reports.

This is the concrete payoff of carrying two fingerprints (§1.2) and of N=20 over n=6. Either
shortcut alone would have published "fixed".

### 4.5 What the timing columns show, and why they are still not a noise floor

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

### 5.2 Load is excluded as the driver — by an accident of scheduling

The concern was real before the data arrived: if the mechanism were scheduling variability under
an oversubscribed thread pool, the *rate* would be a function of host load, and a campaign run on a
busy machine would not generalise.

The campaign happens to contain the control. The two arms ran at **opposite** ends of the
contention range, and each contradicts the load explanation in the direction that matters:

| arm | host load during the arm | span cv | divergence rate |
| --- | --- | ---: | ---: |
| service | **heavy** — load1 up to 39.5, wall 825 s → 190 s | 67.4% | **0.000** |
| direct CLI | **quiet** — load1 5.6 – 9.7 throughout | **5.2%** | **0.768** |

High load did not break the service; low load did not save the CLI. A rate of 0 across 190 pairs on
a machine at load 38, against 0.768 across 190 pairs on the same machine at load 6, is not what a
contention-driven effect looks like.

It also means the CLI arm's *timing* is comparatively clean (cv 5.2%) — but it is still not usable
as a cross-arm noise floor, because the service arm it would be compared against is not (§5.1).

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

Diagnostic arms (§3.6, §3.8, §3.9) additionally need a stack up with an explicitly pinned
`DATA_URL` and one of the two preserved patches applied to a throwaway cascor worktree:

```bash
eval "$(util/ad-hoc/2026-08-14_r5_stack_up.bash)"     # then VERIFY $DATA_URL against
                                                      # <RUN_DIR>/ports.json before proceeding
git -C <DIAG_WT> apply util/ad-hoc/2026-08-20_cascor_candidate_identity_diag.patch
DATA_URL=... util/ad-hoc/2026-08-20_determinism_arm.bash <DIAG_WT>/src <CELL> <OUT> <LABEL> <N> default
python util/ad-hoc/2026-08-20_determinism_diag.py <OUT>/<LABEL>/run-*
```

### 7.1 Teardown attestation

Checked after the last arm, with `util/experiment_stack.bash --down <RUN_ID>` run for every stack:

| check | result |
| --- | --- |
| listeners on 8110–8139 / 8230–8259 / 8260–8289 | **0** |
| port lockdirs in `/run/user/1000/juniper-experiments` | **0** |
| orphaned Juniper python processes (`util/reap_pytest_orphans.bash --dry-run`) | **0** ("No Juniper python processes found") |
| `artifacts/` preserved | yes — teardown reports "never deleted" and the trees are present |

Per-cell teardown was also verified *during* the service arm: exactly two lockdirs and two
listeners at any moment, matching the one live cell.

---

## 8. Disposition

**§3.7 outcome: (b) characterised — with the cause identified and a mitigation measured, but not
removed.** Stating that precisely, because it sits between the handoff's two branches:

| the handoff's exit condition | met? |
| --- | --- |
| (a) root cause identified | **yes** — §3.9, tested by intervention, not inferred |
| (a) a cascor PR lands | **no** — not authored; see below |
| (a) re-run at N≥20 shows a divergence rate of **0** | **no** — 0.000 on the trace, **0.337** on correlations |
| (b) rate, divergence points and noise floor published | rate and divergence points **yes**; noise floor **deferred** (§5.1) |

So this is not "we could not find it", which the handoff rightly refuses as an exit. The cause is
identified and demonstrated: **the two entry points execute `fit()` on different threads**, and
moving the CLI's call onto a pool thread removes trace-level divergence entirely and cuts the
correlation-fingerprint rate from 0.768 to 0.337 at no measurable wall-clock cost.

**Why no fix PR yet.** A mitigation that halves a reproducibility defect is not the same as a fix,
and shipping `ThreadPoolExecutor` into `main.py` would encode a *symptom-shaped* workaround into the
CLI entry point before the residual 0.337 is understood. The right sequence is: understand the
residual, then decide whether the correct change is at the entry point at all or in how the trainer
configures its thread pool. Two things should land regardless, and both are cheap:

1. **Observability.** `_add_best_candidate` logs `{best_candidate}` — a `CandidateUnit` with no
   `__repr__`, so a memory address (`cascade_correlation.py:4850`). The installed unit's identity is
   the single fact that separates a selection flip from arithmetic jitter, and it is unrecoverable
   from any shipped log. Log `candidate_index`; consider full-precision correlations behind a debug
   level. Patch: [`2026-08-20_cascor_candidate_identity_diag.patch`](../util/ad-hoc/2026-08-20_cascor_candidate_identity_diag.patch).
2. **A latent seeding defect, found in passing and not the cause of anything here.**
   `CandidateUnit._initialize_randomness` seeds numpy, *then* draws its roll count from the
   **stdlib `random`** stream (`candidate_unit.py:317` → `:364`) — which at that point has not yet
   been seeded for this candidate (`random.seed` happens on the *next* call, `:319`). numpy's stream
   position therefore depends on leftover interpreter state. It is inert today only because nothing
   in candidate training draws from `np.random`; the torch stream, which *does* seed the weights, is
   rolled after `random.seed` and is deterministic. Any future use of `np.random` in that path would
   silently inherit run-to-run nondeterminism.

### 8.1 What this unblocks, and what it does not

**Unblocked:** the service tier. 0/190 pairs on both fingerprints means service-arm single-run
results carry no reproducibility caveat at this cap and seed, and #533's safety check is discharged.

**Still qualified:** every **direct-CLI single-run** result. At 0.768 the CLI path cannot support a
single-run A/B, and the successor arc's §4 residual measurement must therefore be many-run on that
arm — the handoff's §4.3 "k pairs" branch, not its one-pair branch. The k should be sized against a
noise floor this campaign deliberately did not publish (§5.1).

**Newly opened:** §4.3 — the two arms do not start from the same state on an identical cell. A
wall-clock comparison between them is measuring that as well as the path difference.
