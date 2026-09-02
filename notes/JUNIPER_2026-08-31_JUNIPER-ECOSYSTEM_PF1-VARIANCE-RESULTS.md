# PF-1 — host variance measured; the workload is stable and the *metric choice* is the decision

> **CORRECTED 2026-09-02 — the title claim does not hold.** §1's `drive` sd of **0.03%** is an
> instrument artifact, not workload stability. `timings.drive` is quantized to the driver's 5-second
> status-poll interval, and this run's 20-second cells sat entirely inside one poll cycle, so `drive`
> reported ~20.08 s regardless of whether the work took 14.6 s or 18.3 s. Measured on the
> poll-independent step-duration histogram, this run's within-run spread is **5.92% sd**, ~180x
> larger. See
> [`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md)
> §1, §3 and §4.1. The `total`, `start` and `plots` rows are unaffected — they are not poll-bounded.

**Run**: `pf1-cascor-spiral-repeats-20260831T233254Z`, 5/5 succeeded, cascor **0.10.0** (primary
checkout), service tier, sequential.
**Purpose**: the prerequisite named in
[`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md` §5](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)
— run-to-run spread with **nothing under test**, so that a P3 threshold has a measured noise floor
to sit above rather than an invented number.

**This is P3 input, not a P3 verdict.** No threshold is ratified here.

---

## 1. Result

Five repeats of one unchanged config (`spiral-smoke.yaml`, `max_iterations: 2`,
`max_hidden_units: 2`), differing only in `experiment.description`.

| component | mean (s) | sd (s) | **sd %** | min | max |
|---|---|---|---|---|---|
| **`drive`** (the training loop) | 20.084 | 0.0065 | **0.03%** | 20.078 | 20.095 |
| `total` (driver end-to-end) | 21.974 | 0.0812 | 0.37% | 21.854 | 22.064 |
| suite `wall_seconds` | 33.861 | 0.0985 | 0.29% | 33.724 | 33.979 |
| `start` | 0.535 | 0.0194 | 3.63% | 0.502 | 0.554 |
| `plots` | 1.061 | 0.0892 | 8.40% | 0.934 | 1.179 |
| `dataset_create` | 0.083 | 0.0090 | 10.85% | 0.069 | 0.094 |
| `collect` | 0.169 | 0.0229 | 13.58% | 0.142 | 0.197 |
| `stage` | 0.023 | 0.0059 | 25.54% | 0.018 | 0.033 |

**The workload is extraordinarily reproducible: `drive` varies by 0.03%.** Every noisy component is
infrastructure — staging, plotting, artifact collection — and every one of them is small in
absolute terms. The noise is real but it is not in the thing being measured.

This held **under load**, which strengthens it: the host snapshot at launch recorded load average
**6.31**, with firefox at 55% CPU, an isolated web content process at 45%, gnome-shell at 24%,
four sibling agent sessions at ~40% combined, and a VirtualBox headless guest at 12%. Ordinary
interactive load does not perturb this workload measurably.

---

## 2. The finding: metric choice dominates threshold design

The three candidate run-tier metrics differ in stability by **more than an order of magnitude**:

```text
drive             0.03%      the training loop
total             0.37%      + staging, plots, collection  (12x noisier)
suite wall_secs   0.29%      + stack bring-up and teardown (10x noisier)
```

P1 §2 said the run tier measures "total wall-clock". That is the **worst** of the three choices
available, and this measurement is what shows it: a threshold on `wall_seconds` inherits the
variance of plot rendering and service startup, neither of which is the performance of anything
anyone wants to gate.

**Recommendation for P3: gate `timings.drive`, and report the others.** `drive` is already recorded
in every manifest, needs no new instrumentation, and isolates the workload from the harness. This
refines P1 §2 rather than contradicting it — the tier and the baseline are unchanged; only the
metric within the tier is sharpened.

---

## 3. Applying P1 §5's derivation rule

The rule fixed in advance:

> at least **3× the observed standard deviation**, and never smaller than the largest single
> contention excursion observed on this host.

| clause | value on `drive` |
|---|---|
| 3 × sd | 3 × 0.0065 s = 0.0195 s → **0.10%** |
| largest observed contention excursion | **+6.8%** (a 13-hour `clamscan` against a budget-equivalent spiral cell: 552.0 s vs 516.9 s) |

**The contention floor binds, and it binds by a factor of 68.** A threshold that honours the rule
sits at 6.8% while the workload's own 3-sigma is 0.10%. A gate at 6.8% detects only catastrophic
regressions; anything tighter fires when someone runs a virus scan.

### 3.1 But the floor may be duration-dependent, and that is testable

The 6.8% excursion was measured on a **552-second** cell. PF-1's cells run **20 seconds**. A short
run can finish between contention bursts; a long one cannot avoid overlapping them. So the two
numbers may not describe the same risk, and treating the long-run floor as universal may be
needlessly pessimistic for short scenarios.

This is a **falsifiable claim with a cheap test**: re-run PF-1 with a deliberate CPU/IO load and
compare the resulting spread against the 0.03% quiet-host figure. If short runs stay tight under
load, the floor is duration-scoped and short scenarios can be gated far tighter than 6.8%. If they
do not, the 6.8% floor is general and P1 §5's "this host cannot gate that metric" conclusion
follows for everything.

**Recommended before ratification**, because it is the difference between a useful gate and a
decorative one — and it is one more PF-1 run, not a campaign.

---

## 4. What PF-1 did not deliver

**No step-duration histogram data.** Plan §12.3 specifies PF-1's primary metric as *"p50/p95 step
duration; total wall-clock"*. Only the second half exists. The manifests record:

```json
"metrics_scraped": {"grafana_bridge": false, "present": false}
```

The run did not pass `--grafana-bridge`, so no socat relay ran, no Prometheus target file was
registered, and `juniper_cascor_training_step_duration_seconds` was never scraped. Nothing is
wrong; the instrument simply was not switched on.

Consequence: the p50/p95 half of PF-1 is **still unmeasured**, and a threshold on step duration has
no noise floor behind it. Either re-run PF-1 with the bridge, or drop step duration from PF-1's
metric list and let the `drive` phase stand as the run-tier quantity. **Recommendation: the
latter** — `drive` is already reproducible to 0.03% and requires no scrape path, so the histogram
would add operational surface for a quantity the manifest already answers better.

---

## 5. A caveat on the config these numbers describe

Every cell emitted:

> `training.params.max_epochs=50 is set without output_epochs`: on the SERVICE this bounds only the
> INITIAL output pass (later passes fall back to the `output_epochs` default 10000), while the
> direct CLI aliases `max_epochs` onto EVERY output pass.

**It does not affect the variance result** — the divergence is identical across all five repeats, so
it cannot inflate the spread, which is the only quantity this run reports.

**It does affect what the numbers mean.** These figures describe a config whose effective budget is
larger than `max_epochs: 50` suggests. If any of them are later quoted as a *baseline* rather than
a *spread*, `spiral-smoke.yaml` should set both keys explicitly first. Recorded here so the number
and its caveat travel together.

---

## 6. For P3 (owner)

1. **Ratify the metric before the number.** `timings.drive`, not `wall_seconds` — §2.
2. **Decide whether to run the loaded-repeat test** in §3.1 before fixing a threshold. It is one
   PF-1 run and it determines whether a meaningful gate is possible at all.
3. **Then ratify a threshold**, which by P1 §5's rule is 6.8% unless §3.1 narrows the floor.
4. **Accept or reject dropping step duration** from PF-1's metric list — §4.

Items 1 and 4 are refinements to P1 that this measurement produced; they are recorded here rather
than edited into P1, because P1 is a reviewed document and this is the evidence that would justify
amending it.
