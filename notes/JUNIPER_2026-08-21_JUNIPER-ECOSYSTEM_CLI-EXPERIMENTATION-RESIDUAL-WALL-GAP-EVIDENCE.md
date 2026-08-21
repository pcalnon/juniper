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

### 3.2 Cap 16 — paired, interleaved

<!-- PENDING — campaign in flight. -->

### 3.3 Cap 64

<!-- PENDING — k to be sized from §3.2. -->

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

### 4.2 Remaining hypotheses

<!-- PENDING -->

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
