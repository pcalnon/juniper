# CLI Experimentation — the residual CLI-vs-service wall gap, re-measured post-#533

**Project**: juniper-ml (ecosystem) · **Author**: Paul Calnon · **Created**: 2026-08-21
**cascor SHA (both arms)**: `362b88b1475eb40f4f8aa0a28caa9755ec812722`
**Predecessors**: [seed-reproducibility evidence](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md) ·
[wide-budget head-to-head](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md)

---

## 1. What this re-measures, and why the old number cannot be reused

The wide-budget campaign published **1.99 ± 0.21×** as the direct CLI's wall-clock penalty. That
number is **superseded**: all twelve of its runs were cascor `3909d27`, i.e. **pre-#531/#533**,
when `main.py` capped `OMP_/MKL_/OPENBLAS_NUM_THREADS` to 2 on the CLI path and the service path
was uncapped. The cap alone accounted for **1.30× of a 1.52×** candidate-phase penalty at cap 16.

What survives from that campaign, unchanged and re-confirmed here:

- **100% of the difference is the candidate phase.** The output phase is ~1.0×.
- **The total gap compounds per growth iteration**, which is why a 2-unit smoke run saw none of it.

What must be re-measured is the *magnitude* on post-#533 `main` — this document — and the two
things that had to be settled before the measurement was worth making at all.

### 1.1 Why this could not simply be re-run

Two prerequisites came out of the reproducibility campaign, and both change the design:

1. **The direct-CLI arm cannot support a single-run A/B.** It diverges in **0.768** of run-pairs
   [0.553, 0.847] at N=20; the service arm diverges in **0 of 190**. So the service side is a
   sound single-run instrument and the CLI side is not: every CLI figure here is a **k-paired**
   mean, never one run.
2. **The predecessor's timing was contaminated by block ordering, not by contention.** It ran all
   20 service cells and then all 20 CLI runs; over eight hours host load fell from ~38 to ~6, so
   one arm absorbed nearly all the contention. Its service arm did byte-identical work twenty
   times — 11,360 candidate epochs, `sd = 0` — and still spanned **825 s to 190 s**.

Point 2 is the design constraint that matters most, and it is worth stating precisely because the
obvious reading is wrong: **contention is not the enemy, drift across a block boundary is.** A load
that is merely *constant* cancels in a ratio. A load that *changes* between "all of arm A" and "all
of arm B" biases whichever arm ran during the busy half, and no amount of averaging within an arm
recovers it.

---

## 2. Design

### 2.1 Interleaved pairs, still strictly sequential

[`2026-08-21_h2h_paired_campaign.bash`](../util/ad-hoc/2026-08-21_h2h_paired_campaign.bash)
alternates **service, CLI, service, CLI …** so a pair's two legs are adjacent in time. Residual
drift then hits both legs of a pair roughly equally instead of accumulating against one arm.

The arms are never run *concurrently*. The workload is ~8 forked candidate workers at ~90% CPU
each; two arms at once would contend with each other and void the comparison outright.

### 2.2 The statistic: ratio-of-pairs

[`2026-08-21_h2h_paired_ratio.py`](../util/ad-hoc/2026-08-21_h2h_paired_ratio.py) forms the ratio
**inside** each pair and then averages those ratios. Averaging each arm first and dividing at the
end does not cancel the shared per-pair condition, and lets a single slow leg move the headline.

Both are printed. **When they disagree by more than 2% the tool says so**, because that
disagreement is itself the finding: it means the pairs were not seeing comparable hosts, and the
campaign needs re-running rather than re-interpreting.

The tool also derives the **number of pairs required** for a target precision from the observed
pairwise `sd`. The original failure mode of this whole arc was quoting a ratio from one run per
arm; "how many is enough" is now computed rather than asserted.

### 2.3 Guards that stop the campaign rather than warn

- **One cascor SHA across arms.** The driver refuses to start otherwise — and it earned that on
  its first invocation, catching a primary checkout one commit behind the CLI worktree.
- **One `config_sha256` across every service leg and the CLI's cell.** Each service leg
  re-materialises its own cell; if any differs from the cell the CLI arm was handed, the arms are
  running different experiments and the campaign stops.
- **`DATA_URL` verified against the launching stack's own `ports.json`** before any CLI leg runs,
  since `r5_stack_up.bash` resolves "the newest run dir carrying a `ports.json`" and a service leg
  coming up mid-campaign could otherwise re-point the CLI arm.

---

## 3. Results

### 3.1 Cap 4 — a gap survives #533, and it is entirely throughput

Not a purpose-built pair campaign: this is extracted from the reproducibility campaign's own runs
(20 CLI, and the **6 service cells whose load window matches the CLI arm's**). It is included
because the match is good enough to be worth reporting and it supplies the smallest-cap point.

Load over the two windows is statistically indistinguishable — service mean **7.72** (range
5.97–11.75), CLI mean **7.99** (range 5.09–11.47) — which is the specific confound §1.1 point 2
warns about, and it is absent here.

| metric | service (n=6) | CLI (n=20) | ratio |
| --- | ---: | ---: | ---: |
| training span | 192.5 s | 280.8 s | **1.459×** |
| candidate phase | 187.8 s | 276.1 s | **1.470×** |
| output phase | 3.83 s | 3.75 s | 0.978× |
| candidate epochs | 11,360 | 10,734 | **0.945×** |
| s / candidate epoch | 0.01652 | 0.02571 | **1.555×** |

Three things follow:

1. **A substantial gap survives #533.** Removing the BLAS entry-point asymmetry did not remove the
   penalty; at cap 4 the CLI's candidate phase is still ~1.47× the service's.
2. **It is 100% candidate-phase.** The output ratio is 0.978× — within noise of 1.0, and
   consistent with the wide-budget campaign's 1.03–1.05×.
3. **It is a throughput penalty, not extra work.** The CLI does **5.5% fewer** candidate epochs and
   still takes 1.47× as long; the per-epoch rate ratio is **1.555×**. Whatever the cause, it makes
   each epoch more expensive rather than causing more of them.

> **This is a cross-arm comparison and inherits §4.3 of the reproducibility note**: the two paths
> do not start from the same state on an identical cell. The 0.945× work ratio is partly that, not
> purely a scheduling difference. The *rate* ratio is the more robust of the two figures because it
> is normalised by the work each arm actually did.

### 3.2 Cap 16 — paired and interleaved, k=4

Suite `e-k-thread-probe-cap16-20260821T083547Z`, one `config_sha256` (`2a60040aff9d`) across all
four service legs and the CLI's cell, one stack (`20260821T085116Z-85cd`, `DATA_URL` verified).
Per-leg load1 ranged 2.66–7.13 across the whole campaign.

| pair | svc span | cli span | span× | svc cand | cli cand | cand× | svc epochs | cli epochs | work× | rate× |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 908 | 1607 | 1.770 | 890 | 1554 | 1.746 | 44,910 | 57,450 | 1.279 | 1.365 |
| 2 | 833 | 1306 | 1.568 | 816 | 1253 | 1.536 | 44,910 | 50,350 | 1.121 | 1.370 |
| 3 | 790 | 1525 | 1.930 | 773 | 1472 | 1.904 | 44,910 | 55,340 | 1.232 | 1.545 |
| 4 | 777 | 1299 | 1.672 | 761 | 1248 | 1.640 | 44,910 | 53,420 | 1.189 | 1.379 |

| paired ratio (CLI / service) | mean ± sd | 95% CI |
| --- | ---: | --- |
| **training span** | **1.735 ± 0.154** | [1.584, 1.886] |
| **candidate phase** | **1.706 ± 0.157** | [1.552, 1.861] |
| output phase | 0.969 ± 0.108 | [0.863, 1.075] |
| **candidate work (epochs)** | **1.206 ± 0.067** | [1.140, 1.271] |
| **per-candidate-epoch rate** | **1.415 ± 0.087** | [1.329, 1.500] |

**The design validated itself.** Ratio-of-means is **1.734** against ratio-of-pairs **1.735** — they
agree to three decimals, which is what "the pairs saw comparable hosts" looks like. Had they
diverged, the campaign would have needed re-running rather than re-interpreting.

**The service column is the reproducibility result made visible.** All four service legs did
**exactly 44,910** candidate epochs — the 0/190 divergence rate in operational form. The CLI legs
ranged **50,350 to 57,450**, a 14% spread. That is precisely why k-pairing was mandatory here: a
single CLI run could have reported a work ratio of 1.12 *or* 1.28 with equal honesty.

#### 3.2a This supersedes the cap-16 figure the arc has been carrying

The residual has been tracked as **~1.17×** from the cap-16 `e-k` thread probe in juniper-cascor#531.
That probe was **one run per arm**:

| cap-16 candidate phase | #531 probe (n=1/arm) | this campaign (k=4, paired) |
| --- | ---: | ---: |
| phase ratio | 1.17× | **1.706×** [1.552, 1.861] |
| work ratio | 1.03× | **1.206×** [1.140, 1.271] |
| rate ratio | 1.14× | **1.415×** [1.329, 1.500] |

The single-run figures sit outside the k=4 intervals on every line. Two candidate explanations, and
they are not mutually exclusive:

1. **Sampling.** The CLI's candidate work varies 14% run to run (above), so a single CLI draw can
   land anywhere in a wide band. `1.03×` is inside that band.
2. **A real methodological difference.** #531's probe set `OMP_NUM_THREADS=16` **explicitly** on the
   CLI; this campaign runs the CLI at `default`, i.e. the variables **unset**, which is the shipped
   post-#533 behaviour and what the service does. Those are *intended* to be the same 16 threads,
   but "unset, library picks" and "explicitly 16" are not guaranteed to resolve identically —
   OpenMP and MKL both have defaulting heuristics that an explicit value bypasses.

**Not resolved here**, and worth stating plainly rather than picking the flattering reading. It is
cheaply testable — a few CLI legs at explicit `16` against the existing `default` legs — and is
recorded in §6 as an open item rather than folded into the headline.

#### 3.2b The gap grows with cap, but not in the way the decomposition suggests

| | cap 4 | cap 16 |
| --- | ---: | ---: |
| candidate phase | 1.470× | **1.706×** |
| candidate work | 0.945× | **1.206×** |
| per-epoch rate | 1.555× | **1.415×** |
| output phase | 0.978× | 0.969× |

The total gap grows, and it is the **work** term that drives it — flipping from the CLI doing 5.5%
*less* work at cap 4 to 20.6% *more* at cap 16. The **rate** term moves the other way, easing from
1.555× to 1.415×.

That is consistent with two separate effects rather than one: a roughly constant per-epoch overhead
that matters less as the matrices grow, plus a divergence in *when candidate early stopping fires*
that compounds as the network deepens. The output phase stays at ~1.0× throughout, so none of this
is the output layer.

**It also means neither cap licenses an extrapolation to cap 64** — the two terms move in opposite
directions, so the product is not something to fit a line through. Hence §3.3.

### 3.3 Cap 64 — paired, k=4, and the result splits in two

Suite `e-m-h2h-paired-cap64-20260821T111154Z`, one `config_sha256` (`2bf1b3c6af6a`), one verified
stack, ~10 h. Per-leg load1 3.77–7.14.

| pair | svc span | cli span | span× | svc epochs | cli epochs | work× | rate× |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2737 | 5780 | 2.112 | 134,500 | 221,580 | 1.647 | 1.289 |
| **2** | 2478 | **2967** | **1.197** | 134,500 | **122,840** | **0.913** | **1.316** |
| 3 | 2372 | 5195 | 2.190 | 134,500 | 212,020 | 1.576 | 1.402 |
| 4 | 2500 | 5492 | 2.197 | 134,500 | 225,980 | 1.680 | 1.317 |

| paired ratio | mean ± sd | 95% CI |
| --- | ---: | --- |
| training span | 1.924 ± 0.486 | [1.448, 2.400] |
| candidate phase | 1.937 ± 0.492 | [1.455, 2.420] |
| output phase | 0.900 ± 0.271 | [0.635, 1.166] |
| **candidate work** | **1.454 ± 0.363** | [1.098, 1.810] |
| **per-candidate-epoch rate** | **1.331 ± 0.049** | [1.283, 1.379] |

Ratio-of-means 1.927 against ratio-of-pairs 1.924 — the pairs saw comparable hosts.

**Pair 2 is not an anomaly to discard; it is the reproducibility defect in the wall clock.** Its CLI
leg did **122,840** candidate epochs where the other three did 212k–226k — roughly half the work,
on a byte-identical config. The service leg did **exactly 134,500** in all four pairs. That is
cascor#532 (direct-CLI divergence rate 0.768) expressed as wall time.

#### 3.3a The finding: one stable term and one stochastic term

The single most useful thing in this table is that **the rate ratio barely moves while the work
ratio swings 2×**:

| pair | work× | rate× |
| ---: | ---: | ---: |
| 1 | 1.647 | 1.289 |
| 2 | **0.913** | 1.316 |
| 3 | 1.576 | 1.402 |
| 4 | 1.680 | 1.317 |

Work ranges 0.913–1.680 (sd 0.363, cv 25%). Rate ranges 1.289–1.402 (sd 0.049, **cv 3.7%**), and
pair 2 — the one that did half the work — sits in the middle of the rate band.

The analyser's own sizing says the same thing: for a 0.05 half-width the span needs **k=363** and
the rate needs **k=4, already SUFFICIENT**.

So "the CLI is ~1.9× slower" is a poor headline. The gap is:

> **a STABLE ~1.33× per-candidate-epoch throughput penalty — the genuine path difference —
> multiplied by a VARIABLE amount of work the CLI happens to do, which is cascor#532 and not a
> performance property at all.**

Those are different defects with different owners. The rate term is what §4.6 should fix. The work
term is already tracked as G1/G1a and is only reducible by making the CLI path reproducible.

#### 3.3b The cap series — the compounding is entirely the work term

| cap | span× | work× | rate× | output× | work × rate | measured phase× |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 1.459 | 0.945 | 1.555 | 0.978 | 1.469 | 1.470 |
| 16 | 1.735 | 1.206 | 1.415 | 0.969 | 1.706 | 1.706 |
| 64 | 1.924 | 1.454 | 1.331 | 0.900 | 1.935 | 1.937 |

The decomposition closes to within 0.002 at every cap, so the two terms are a complete account of
the candidate phase.

Read across the rows: **work grows monotonically (0.945 → 1.454) while rate falls monotonically
(1.555 → 1.331).** The much-quoted "the gap compounds per growth iteration" is true of the total —
and it is *entirely* the work term doing it. The per-epoch penalty actually *improves* with cap, as
larger matrices amortise a fixed overhead.

This is why §3.2b warned against extrapolating: a fit through the total would have been fitting the
product of two opposing trends.

#### 3.3c #533 did not measurably reduce the cap-64 gap

The wide-budget campaign measured **1.99 ± 0.21×** pre-#533, with the CLI arm carrying `main.py`'s
`OMP=2` cap that juniper-cascor#531 valued at **1.30× of a 1.52×** candidate-phase penalty at
cap 16. Removing that cap should therefore have moved the cap-64 headline substantially.

Measured post-#533 at k=4: **1.924 ± 0.486** — squarely overlapping the pre-#533 1.99 ± 0.21.

Two caveats before this is read as "#533 achieved nothing": the designs differ (ml#1143 used three
*different* seeds, this uses one seed × four replicates), and my interval is wide because of the
work term. But the comparison is informative in the same direction as §3.2a: **#531's 1.30×
thread-cap attribution also rests on single runs**, and single-run attributions in this system have
now twice failed to survive k=4. Testing that is the OMP control in §6.

---

## 4. Root cause

### 4.1 Thread context is eliminated — it explains the determinism, not the speed

The reproducibility campaign found that the two entry points run `fit()` on different threads
(service on a `ThreadPoolExecutor` worker, CLI on the main thread) and that moving the CLI onto a
pool thread cuts its divergence rate from 0.768 to 0.337.

It is a natural next thought that the same difference explains the *wall* gap — one mechanism, both
symptoms. **It does not.** From that campaign's own N=20 arms, at cap 4:

| CLI variant | training span |
| --- | ---: |
| baseline — `fit()` on the main thread | 280.8 ± 14.7 s |
| probe — `fit()` on a pool thread | 282.9 ± 5.7 s |

Moving to a pool thread changed the wall time by **0.7%**, well inside the spread, while the
service arm under a matched load window sat at 192.5 s. The thread-context difference is therefore
**not** the wall-clock mechanism, and the two symptoms have different causes.

Recording this as an elimination rather than a footnote: it was the leading hypothesis going in,
and it is cheap for a later reader to re-propose.

### 4.2 The work term — the two paths train DIFFERENT CANDIDATES, by three draws

`candidate_seeds` are drawn once per growth iteration from the **parent's stdlib `random` stream**
(`cascade_correlation.py:2298`), not derived from the configured `random_seed`. Logged on both arms
from one instrumented build:

```
SERVICE round 0: [698594025, 1525876051, 2878380452, 2727210979, 1051454923, 1985392498, 240251661, 3529615275]
CLI     round 0: [                                    2727210979, 1051454923, 1985392498, 240251661, 3529615275, 3457645390, 1722989659, 284277889]
SERVICE round 1: [3457645390, 1722989659, 284277889, 3083418319, …]
```

Line them up. The CLI's round-0 list **begins at the service's 4th element**, and its last three are
the service's **round-1 first three**. Both arms walk the *same* deterministic stream — the CLI is
simply **offset by exactly three draws**, and stays offset for the whole run.

**So the two paths do not train the same candidates, and never did.** Not because of a seed
mismatch — `network_seed=42` on both — but because something on the CLI path consumes three extra
values from `random` before the first candidate round, and candidate seeds are *positional* on that
stream.

Consequences, in order of how much they matter:

1. **Part of the measured work ratio is "different candidates", not "slower path".** A candidate
   seeded differently trains for a different number of epochs. The work term (0.945× / 1.206× /
   1.454× across the caps) is therefore *not* purely a path property, and any fix that equalises
   the seeds will move it.
2. **It is fragile in a way nothing declares.** Adding a single `random` call anywhere on either
   path — logging, a retry, a shuffle — silently re-seeds every candidate in every subsequent
   round. Nothing would fail; the numbers would just change.
3. **It makes any cross-path comparison structurally suspect** unless the two paths happen to have
   consumed the same number of draws first, which nothing checks or guarantees.

The fix is small and obvious: derive candidate seeds from `(network_seed, iteration,
candidate_index)` rather than by drawing from a shared global stream. That makes them a function of
configuration alone and independent of draw history. Carried into §4.6.

### 4.3 The rate term — NOT pool packing; the penalty is real

§3.3a's stable ~1.33× per-epoch penalty was measured as candidate-phase wall ÷ **total** epochs.
That is not a per-epoch cost. A round runs 8 candidates over 7 workers, so at least one worker runs
two sequentially and the round's wall is set by the **busiest worker's critical path**, not the
total. A path whose candidates finish unevenly looks slower per epoch than one whose candidates
finish together, at identical arithmetic cost.

[`2026-08-21_h2h_pool_balance.py`](../util/ad-hoc/2026-08-21_h2h_pool_balance.py) computes the
critical path per round (LPT: sort candidates descending, greedily assign to the least-loaded
worker) and an imbalance figure — critical ÷ perfect-split:

| arm | rounds | total epochs | critical epochs | imbalance |
| --- | ---: | ---: | ---: | ---: |
| service | 16 | 45,199 | 9,685 | 1.533 ± 0.460 |
| CLI | 16 | 56,095 | 12,561 | 1.552 ± 0.280 |
| **CLI / service** | | **1.241×** | **1.297×** | **1.012×** |

**Imbalance is 1.012× — the two arms pack equally badly.** Both waste ~53% over a perfect split,
and neither is worse than the other. Pool packing is therefore *not* what separates them, and the
rate penalty is a genuine per-epoch cost difference: **profiling should target the worker
environment, not the scheduler.**

One correction falls out of the same table, and it goes against the headline. The correct
denominator (critical epochs, 1.297×) is larger than the one the rate column uses (total epochs,
1.241×), so measuring against totals **overstates the per-epoch penalty by ~4.5%**. Applied to the
cap-16 figure, 1.415× becomes ≈**1.354×**; the cap-64 1.331× shifts similarly. The penalty is real
and substantial either way, but the published rate numbers should be read as a slight over-estimate
until recomputed against critical path across a full campaign.

> Caveat: this is **one pair**, run under host load 25–28. That does not affect it — every quantity
> here is an epoch *count*, not a time — but the imbalance figures are n=1 per arm and would be
> worth confirming across the k=4 campaigns before being leaned on hard.

### 4.4 Remaining hypotheses

With packing eliminated (§4.3) and thread context eliminated (§4.1), what is left for the ~1.33×
per-epoch penalty is the **worker environment**: the candidate workers are forked from a
`uvicorn` parent on one path and a bare `python main.py` parent on the other. Forkserver preload
set, allocator state, copy-on-write layout and inherited interpreter state all differ, and none of
them are visible from the logs.

That is what §4.6's profiling pass has to discriminate, and it is now correctly aimed: a per-epoch
cost difference inside the worker, not a scheduling or ordering effect.

---

## 5. Impact

<!-- PENDING -->

---

## 6. Honest limits

<!-- PENDING -->

---

## 7. Reproduction

```bash
export JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper
export JUNIPER_EXP_HEALTH_TIMEOUT=180

# a DEDICATED cascor worktree at the SAME commit as the primary checkout the service arm uses
git -C juniper-cascor worktree add --detach <WT> origin/main
git -C juniper-cascor pull --ff-only origin main     # the driver REFUSES if these differ

util/ad-hoc/2026-08-21_h2h_paired_campaign.bash <WT>/src \
    util/experiments/suites/p4/e-k-thread-probe-cap16.yaml 4

python util/ad-hoc/2026-08-21_h2h_paired_ratio.py \
    ~/.local/state/juniper-experiments/h2h-paired-e-k-thread-probe-cap16
```

---

## 8. Disposition

<!-- PENDING -->
