# PF-1 at 60 s and under heavy load — three separable effects, and why a bare percentage cannot gate this host

**Executes** the owner's 2026-09-01 decisions — cells lengthened to ~60 s (decision 2), step duration
retained (decision 4), plus the **new requirement** for a scenario loading all 16 cores rather than
leaving the stack effectively-dedicated ones.

**Supersedes the threshold recommendation** in
[`JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-LOADED-AND-BRIDGED-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-LOADED-AND-BRIDGED-RESULTS.md) §2.
That document proposed 0.5% on `timings.drive`, derived from 20-second cells. **At 66 seconds that
threshold would have fired on the very first run.** The measurement that produced it was not wrong;
its scope was narrower than the recommendation implied.

---

## 1. Every measurement so far

| condition | n | `drive` mean | sd | sd % | note |
|---|---|---|---|---|---|
| 20 s, quiet, unbridged | 5 | 20.084 s | 0.0065 | 0.033% | |
| 20 s, quiet, bridged | 5 | 20.081 s | 0.0099 | 0.049% | bridge costs nothing in `drive` |
| 20 s, **modest** load (4/16) | 5 | 20.091 s | 0.0084 | 0.042% | +0.051% vs quiet |
| **66 s, quiet** | 5 | 66.223 s | 2.2229 | **3.357%** | four cells within 0.02%, **one at +7.6%** |
| **124 s, heavy** (14/16, ramping) | 5 | 123.716 s | 2.7906 | 2.256% | **+90%** vs quiet |
| 173 s, heavy (14/16, settled) | 3 | 172.697 s | 2.95 | 1.71% | **+165%** vs quiet |

---

## 2. Three effects, and they were previously conflated

**(a) Intrinsic workload variance: ~0.02%.** At 66 s, four of five cells landed within
65.211–65.244 s. The workload is essentially deterministic; nothing in the earlier measurements
contradicted this and nothing here does either.

**(b) Duration exposure to transients: +7.6%, roughly one cell in five at 66 s.** The fifth cell
took 70.199 s. Across ten cells at 20 s no such excursion occurred; at 66 s one in five did. Host
load rose 2.82 → 4.74 during that run and the outlier was the **last** cell. The excursion
magnitude sits beside the historical clamscan figure of **+6.8%** — most likely the same
phenomenon, sampled at a duration long enough to catch it.

**(c) Core contention: +90% to +165%.** This is the effect the owner's new requirement exposed and
the `modest` profile entirely concealed. Under `modest`, twelve of sixteen cores stayed free, so the
stack still ran on effectively dedicated cores and the measured cost was +0.051%. Remove that
headroom and the same workload takes **1.9× to 2.6× longer**.

### 2.1 The contaminated run is evidence, not waste

The first `heavy` attempt was mis-sized — the load was budgeted from *quiet* cell durations and
expired during cell 4. The resulting gradient is causally unambiguous:

```text
c000 170.999  loaded
c001 176.102  loaded
c002 170.990  loaded
c003 105.560  load expiring mid-cell
c004  70.211  unloaded — back to the quiet range
```

Removing the load **restored the quiet timing**. That upgrades (c) from a correlation to a
demonstrated mechanism. The three loaded cells are reported as n=3 above and are not mixed into any
five-repeat statistic.

---

## 3. A defect in this measurement's own tooling

**`heavy` was not yet a reproducible condition**, which defeats the point of naming a profile. Two
`heavy` runs at the same worker count produced **+165%** and **+90%**, because they were launched at
different load *ages*: the clean run began at load average 8.55 and ended at 22.88, i.e. the load
was still ramping through the measurement.

Two causes, both inherent to the generator's shape: load average is a lagging one-minute figure, and
the workers' first pass reads from disk while later passes hit page cache — so the load's character
shifts from I/O-bound to CPU-bound over the first minutes.

**Fixed**: the generator now settles for `LOAD_SETTLE` (default 120 s) and announces `READY` with the
observed load average. A caller wanting a comparable measurement waits for that line before starting
its workload. **The +90% figure above was taken during ramp and should be treated as a lower bound**;
the +165% figure, taken against an already-running load, is the better estimate of settled `heavy`.

**A settled-`heavy` five-repeat measurement has not yet been taken.** It is the obvious next run and
costs about 20 minutes.

---

## 4. Consequence: a bare percentage cannot gate this host

Any single threshold must simultaneously not fire on (b)'s +7.6% transient or (c)'s +90–165%
contention, while still catching a regression worth catching. Those constraints are incompatible: a
threshold above contention is ~200% and detects nothing; one that catches a real regression fires
constantly.

Two shapes are viable, and they compose:

1. **A host-state precondition.** Refuse to *evaluate* the gate unless free-core headroom at run
   time meets a floor. This promotes `HOST.json` from provenance to a **gating input** — the P1 §4
   contract already records the fingerprint, so the data exists; what is missing is a rule that
   consults it. Effect (c) then cannot reach the comparison at all.
2. **A median-of-repeats statistic.** PF-1 already runs five repeats. The median is unmoved by one
   outlier in five, which is exactly (b)'s observed frequency — the 66 s median is 65.244 s against
   a mean of 66.223 s. Gating the median rather than any single run removes (b) without loosening
   sensitivity to a real shift.

**With both, a threshold near 1% on the median of `drive` is defensible** — comfortably above (a)'s
0.02% intrinsic noise, robust to (b), and never evaluated in (c)'s regime. That is roughly 7× tighter
than the 6.8% the original contention figure would have forced, and it is honest about *why* it can
be that tight: because the conditions under which it applies are stated rather than assumed.

**Not proposed as ratified.** It rests on a settled-`heavy` measurement that has not been taken (§3),
and the owner's standing instruction is that thresholds are ratified after analysis, not during it.

---

## 5. Step duration — decision 4 is satisfied

Lengthening the cells did what decision 2 intended. Every cell of every 60 s+ run reports
`scrape_confirmed: true` with 255–357 series, and the histogram is present and usable:

```text
p50 step duration  25.1 ms
p95 step duration  47.7 ms
```

Two notes for whoever reads this next. Prometheus **instant queries only return series inside the
lookback window**, so querying a finished run minutes later shows nothing — query at the run's own
timestamp. This nearly produced a false "the metric is still missing" conclusion here. And the
calibration point is worth keeping: at `(6, 6)` → 40.17 s drive the histogram was already captured,
so ~40 s is the empirical floor for scrapeability, not 60 s.

---

## 6. For the owner

1. **The 0.5% candidate is withdrawn** as scoped — it was derived at 20 s and fires at 66 s (§1).
2. **Decide the gate's shape before its number**: host-state precondition, median-of-repeats, or
   both (§4). The number follows from the shape.
3. **A settled-`heavy` five-repeat run** is the outstanding measurement (§3), ~20 minutes.
4. **Other duration classes remain unmeasured** — E-A/E-C sit at hundreds of seconds, where (b)'s
   exposure is by construction higher than anything measured here.
