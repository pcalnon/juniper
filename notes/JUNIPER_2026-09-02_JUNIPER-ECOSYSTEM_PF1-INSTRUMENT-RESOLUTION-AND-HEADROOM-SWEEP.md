# PF-1: the ratified metric was saturated — `timings.drive` is poll-quantized, and three published findings do not survive it

**Corrects already-merged work.** Every quantitative claim in §1 and §2 of the heavy-load results
([`JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md))
and §2 of the loaded-and-bridged results
([`JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-LOADED-AND-BRIDGED-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-LOADED-AND-BRIDGED-RESULTS.md))
at 20-second cell length was measured with an instrument that could not resolve the differences
being reported. The measurements were taken correctly; the instrument's resolution was never
characterised.

**Records the owner's 2026-09-02 decisions** on gate shape, effect size and host time (§7 of this
document), and the headroom sweep taken under them (§8 of this document).

---

## 1. The finding

`util/experiments/run_experiment.py:123` sets `DEFAULT_POLL_INTERVAL = 5.0`. The drive loop
(`util/experiments/run_experiment.py:894-944`) polls `GET /v1/training/status` and **breaks only on
a poll**, sleeping `poll_interval` between iterations. So:

```text
timings.drive  ~=  (polls - 1) * 5.0  +  accumulated per-poll HTTP overhead
```

The poll counts recorded in each run's `manifest.json` under `drive_loop.polls` confirm this
exactly, with no exceptions across 31 cells:

| polls | `drive` | implied `(polls-1) x 5` | residual |
|---|---|---|---|
| 5  | 20.08 s  | 20.0 s  | 0.08 s |
| 9  | 40.17 s  | 40.0 s  | 0.17 s |
| 14 | 65.2 s   | 65.0 s  | 0.2 s  |
| 15 | 70.199 s | 70.0 s  | 0.2 s  |
| 25 | 120.6 s  | 120.0 s | 0.65 s |
| 26 | 125.7 s  | 125.0 s | 0.75 s |

The residual grows linearly with poll count — it is the accumulated cost of the status GET plus the
`/metrics` fetch performed on every poll.

**Consequence: `timings.drive` cannot resolve any variation smaller than one 5-second poll cycle.**
At a 20-second cell that is 25% of the measured quantity.

---

## 2. The resolving instrument was present in every run all along

The cascor step-duration histogram is sampled **directly from the service** by the driver's own poll
loop (`util/experiments/run_experiment.py:917`) into `artifacts/results/metrics_series.csv`, as
`juniper_cascor_training_step_duration_seconds_sum` / `_count`.

This matters twice over:

1. It is **poll-independent** in value. The poll interval decides how often the counter is *read*;
   the counter itself accumulates real per-step wall time inside the service.
2. It is **independent of Prometheus**. The PF-1 suite header
   (`util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml`) records that a 20-second cell
   "was NEVER SCRAPED", and lengthened cells to ~60 s for that reason. That is true of the
   *Prometheus* host-experiments job, which discovers by `file_sd` every 15 s and scrapes every
   15 s. It is **not** true of the driver's own sampling: all fifteen 20-second cells carry a
   complete 804-step histogram despite reporting `scrape_confirmed: absent`. The `absent` flag
   describes the Prometheus scrape, not the data.

So the gate-relevant metric was obtainable at 20 s for the entire history of this lane.

---

## 3. Evidence: what each instrument reports on the *same* runs

Reproduce with `util/ad-hoc/2026-09-02_pf1_drive_extract.py` (reads `registry.jsonl` →
`manifest.json` → `metrics_series.csv`; transcribes nothing).

| PF-1 run | condition | `drive` sd | `step_sum` sd | understated by |
|---|---|---|---|---|
| `20260831T233254Z` | 20 s, quiet, unbridged | 0.033% | **5.92%** | **182x** |
| `20260901T071754Z` | 20 s, quiet, bridged   | 0.049% | **1.25%** | 25x |
| `20260901T072151Z` | 20 s, modest load 4/16 | 0.042% | **4.08%** | 97x |
| `20260901T101126Z` | 66 s, quiet            | 3.357% | 4.198% | 1.3x |
| `20260901T103324Z` | 126 s, heavy 14/16     | 2.256% | 1.970% | 0.9x |

**The understatement is not uniform — it is positional.** It collapses to ~1x at 66 s and 126 s
only because the workload there happens to straddle a 5-second boundary, so a crossing leaks the
variation through as a whole extra cycle. Where a config lands relative to the 5-second grid is not
a stable property: it moves with the config, with host speed, and with any code change under test.
A gate whose sensitivity varies uncontrollably with duration is worse than one that is uniformly
coarse, because nothing in the output signals which regime it is in.

**And the error runs in both directions.** The `01-sweep6` block of the sweep's aborted first attempt
(`headroom-sweep-block-20260902T110421Z`; the block itself ran correctly under a settled load, the
abort came later — §8.3 of this document) landed on a boundary, with cells at 5, 6 and 6 polls.
There `drive` reports **12.378% sd** against a true spread of **2.430%** — it *overstates* by 5x,
having *understated* by 182x elsewhere. `drive` is therefore not a conservative approximation in
either direction, which rules out the usual mitigation of treating a coarse metric as an upper bound
on noise.

The completed sweep reconfirms the positional pattern across seven more blocks: `drive` understates
by **34x–91x** in the five blocks whose cells shared a poll count, and by **~1x** in the two
(`04-sweep8`, `05-sweep12`) whose cells straddled a boundary.

---

## 4. Three published findings that do not survive

All three compared `drive` medians differing by **less than 0.06%** — well inside the instrument's
blind spot. The same runs, read on `step_sum`:

| comparison | `drive` Δ | `step_sum` Δ |
|---|---|---|
| unbridged → bridged (both quiet) | −0.015% | **−11.5%** |
| bridged quiet → modest load (4/16) | +0.050% | **+15.0%** |
| unbridged quiet → modest load (4/16) | +0.035% | **+1.8%** |

### 4.1 "Intrinsic workload variance ~0.02%"

§2 of the heavy-load results
([`…PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md))
reports effect (a) as ~0.02%. At 20 s the workload occupies 14.6–18.3 s of step time — comfortably
inside poll cycle 4 for all fifteen cells across three runs — so `drive` read ~20.08 s regardless.
**The metric was saturated, not stable.** True within-run spread on `step_sum` is **1.25%–5.92%**
(sd), 60x–180x larger.

This is the vacuous-pass class: the number was steady because the instrument was not resolving.

### 4.2 "The Grafana bridge costs nothing in `drive`" (+0.015%)

On `step_sum` the bridged run was **11.5% faster** than the unbridged one. A bridge that reduces
work is not a credible mechanism, so the difference is almost certainly drift (§5 of this document)
— which is the point: the comparison never had the resolution to say anything either way.

### 4.3 "Modest 4-of-16 load costs +0.051%" — the load-bearing negative

The 2026-09-01 handoff describes this as *"a valid and load-bearing negative: the only evidence that
a regime exists in which a tight gate is possible."*

**That evidence does not survive.** Against the bridged quiet run the modest-loaded run is **+15.0%**
on `step_sum`; against the unbridged quiet run it is **+1.8%**. The apparent effect of the load
spans an order of magnitude depending purely on which of two quiet baselines is chosen.

Note carefully what this does and does not establish. It does **not** show that modest load slows
the workload by 15% — the two *quiet* runs differ from each other by 11.5%, so the load effect is
**not separable from run-to-run drift** at n=1 per condition. What it establishes is that the
`+0.051%` figure carries no information, and with it goes the only measured basis for believing a
tight-gate regime exists on this host.

### 4.4 Effect (b), "duration exposure", is not a separate effect

§2 of the heavy-load results
([`…PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md))
separates (b) "duration exposure +7.6%" from (a) "intrinsic variance". On `step_sum` the 66 s
outlier cell `c004` is genuinely 8.6% slower than its four siblings (68.393 s against a 61.8–63.7 s
cluster; 6.6 sd out), so a real excursion did occur. But it is an ordinary **host speed excursion**,
the same phenomenon as (a) and as the drift in §5 of this document — `drive` merely rendered it as a
discrete 5-second jump because it happened to push the run across a poll boundary.

This also corrects §6 item 4 of the heavy-load results
([`…PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md)),
which expects E-A/E-C at hundreds of seconds to have *higher* exposure "by construction". For the
quantization component the opposite holds: one cycle is a fixed 5 s, so it is 25% of a 20 s cell,
7.6% of a 66 s cell and 0.9% of a 552 s cell. Longer runs cross boundaries more often but pay less
each time.

### 4.5 It also explains an anomaly a previous correction left open

§3 of the heavy-load results
([`…PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md))
already refuted its own "+90% is a lower bound" inference by observing that the heavy-clean run's
cells are **125.783, 125.736, 120.677, 120.642, 125.744** — *"non-monotone and bimodal, with the
middle two the fastest"*, where a monotone load ramp predicts monotonically increasing durations.
The refutation was right; the bimodality itself was left unexplained.

**It is the poll quantum.** Those five cells ran 26, 26, 25, 25 and 26 polls. `drive` cannot take a
value between 120.6 and 125.7, so a continuous distribution is rendered as two clusters ~5 s apart.
The underlying `step_sum` values — 123.334, 119.347, 117.850, 117.461, 118.707 — are not bimodal at
all, and they even *reorder* the cells: `drive` places `c001` and `c004` within 8 ms of each other
while `step_sum` separates them by 0.64 s.

That correction's conclusion — load average is a poor predictor of workload cost in this regime —
survives, and matters more now: it was the instrument a host-state precondition would have consulted.

---

## 5. Between-run drift dominates, and it was measurable all along

Mean step duration across the three 20-second five-repeat runs:

| run | condition | mean step | vs. fastest |
|---|---|---|---|
| `20260901T071754Z` | quiet, bridged | 18.42 ms | — |
| `20260831T233254Z` | quiet, unbridged | 20.81 ms | +13.0% |
| `20260901T072151Z` | modest load 4/16 | 21.18 ms | +15.0% |

**Two quiet runs differ by 13%** — more than the within-run spread of either, and the same order as
every load effect the lane has tried to measure.

**The sweep raises this to 20.5%.** Its three quiet control blocks, taken inside a single
26-minute window with no synthetic load, span 18.282 / 22.024 / 18.663 ms per step (§8.4 of this
document). So the drift floor is not a property of runs taken hours apart — it is present within
half an hour, and it is larger than the effect of six competing CPU-bound processes.

The 2026-09-01 handoff records between-run variability as unmeasured (true at 66 s, where n=1). At
20 s three runs sat in the artifact tree holding the answer, unread because `drive` reported them as
identical to within 0.06%.

**This is fatal to PF-4 as designed.** §4.1 of the 2026-09-01 handoff and §1 of the P1 design
([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md))
have PF-4 compare a run against a stored baseline (`baseline_20260526.json`). A stored baseline is by
construction a different run from the one under test, so it inherits the full 13% drift floor —
independently of the separate, already-known problem that the file holds no timing data.

---

## 6. What is actually gateable on this host

`step_count` is **identical across every cell of every run**: 804 at `(max_iterations, max_hidden_units) = (2, 2)`,
4012 at `(10, 10)`. The workload is deterministic in work *amount*. That splits regressions into two
classes with radically different noise:

| class | signal | noise floor | gateable? |
|---|---|---|---|
| **work** — extra epochs, extra candidate passes, redundant steps | `step_count` moves | **~0%** (exact across 31 cells) | **yes, tightly** |
| **speed** — same work, slower | `step_sum / step_count` moves | **13–15%** (drift) | not usefully |

The work half is also **contention-immune**: a loaded host runs the same number of steps, just
slower. The sweep confirms this directly and at strength — **all 21 cells report exactly 804 steps
across seven load levels spanning a 3x range of step duration** (18.3 → 55.4 ms), §8.4 of this
document.

**Why the count is exact rather than approximately exact.** It is read from the driver's final
`/metrics` sample, and the drive loop samples *before* it tests for termination
(`util/experiments/run_experiment.py:917-930`): it polls status, fetches `/metrics`, writes the CSV
row, and only then breaks on a terminal FSM state. So the last recorded sample is always taken after
training has completed, never mid-run. That is why all 34 cells measured to date report exactly 804
or 4012 with no off-by-a-few scatter, and it is what makes a zero-tolerance gate safe.

That is the class most real regressions fall into, and it is gateable at essentially zero
tolerance — far tighter than the ~1% that §4 of the heavy-load results
([`…PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md))
proposed for `drive`, and defensible rather than merely tight.

Applying the ratified derivation rule from §5 of the P1 design
([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md))
— threshold ≥ 3x observed sd — to the speed half gives **3.75%–17.8%** within-run, before drift.
That rule's terminal clause then applies as written: the floor exceeds any effect size worth
detecting, so **this host cannot gate step speed**.

---

## 7. Owner decisions, 2026-09-02

| # | decision | consequence |
|---|---|---|
| 1 | **Split gate**: exact `step_count`, loose mean step duration | `timings.drive` is de-ratified as the gate metric |
| 2 | **Gate work regressions only, at any size**; speed is not gated | §5's terminal clause is accepted for speed; the speed number becomes report-only |
| 3 | **Spend host time on the headroom sweep** (6/8/10/12 loaded cores) | §8 of this document |

Decision 2 reframes the sweep. Its purpose in the 2026-09-01 handoff was to find a floor for a
**host-state precondition** protecting the speed gate. With speed ungated there is no such gate to
protect, so the sweep now answers a narrower question: **at what headroom does the report-only speed
number stop being interpretable?** It also feeds Q-9 alert scoping, recommended in §6 of the P1
design ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md))
and now more pressing.

---

## 8. The headroom sweep

### 8.1 Design, and why it is not a bare sweep

Run by `util/ad-hoc/2026-09-02_headroom_sweep.bash` against
`util/ad-hoc/2026-09-02_headroom_sweep_suite.yaml`, using the load profiles `sweep6` / `sweep8` /
`sweep10` / `sweep12` added to `util/ad-hoc/2026-09-01_contention_load.bash`.

Given §5 of this document, a sweep run as 6 → 8 → 10 → 12 would be **uninterpretable**: a 13% drift
over the ~30 minutes it takes would produce a clean monotonic "trend" indistinguishable from a
response to load. Two controls address this:

1. **Quiet control blocks bracket and bisect** the sweep (`00-quiet-a`, `03-quiet-b`, `06-quiet-c`),
   giving a drift trace across the measurement window.
2. **The load points run out of order** — 6, 10, 8, 12. A monotonic drift in host speed therefore
   cannot masquerade as a monotonic response to load, because load level is not monotonic in time.

Cells are 20 s rather than PF-1's 60 s, for the reason in §2 of this document: `step_sum` is fully
resolved at 20 s, and points-per-unit-time is the binding constraint on separating load from drift.

### 8.2 Ambient load is not zero

The host carried a load average of **4.74** at sweep start, against 16 cores. "Quiet" here means
ambient, not idle, and a `sweepN` block means N synthetic workers *on top of* whatever else the host
was doing. The driver records `/proc/loadavg` at each block start in `blocks.tsv` so the realised
condition is recoverable rather than assumed.

### 8.3 Three defects in the sweep's own tooling, found by running it

The first sweep attempt stalled and had to be aborted. All three are fixed, and each fix was
verified against a live load before the re-run.

1. **A bare `sleep` defers a bash TERM trap indefinitely.** The load generator's body was
   `sleep "${REMAIN}"`, and *bash does not run a trap while waiting for a foreground external
   command to finish*. So the driver's polite `kill -TERM` + `wait` blocked for **13 minutes** with
   all six workers still hashing — the load ignored a stop request and ran its full `LOAD_DURATION`.
   This is a latent bug for **any** caller, not just this sweep. Fixed with `sleep N & wait $!`,
   which bash *does* interrupt.

2. **The fix moved the hang rather than removing it.** With that in place the trap fired and the
   workers died — and then cleanup's bare `wait` blocked on the backgrounded `sleep` the helper had
   just created, for the same remaining duration. Fixed by tracking and killing that pid first.
   Worth stating plainly because the symptom was identical before and after the first fix, which is
   exactly the shape that gets a real fix mistaken for a failed one.

3. **`$!` does not name a `setsid` child.** The driver group-kills the load so orphaned
   `find`/`xargs`/`sha256sum` grandchildren cannot survive their subshell. That needs the leader's
   pid — and `setsid` **forks**, so `$!` is setsid's own wrapper, already exited by the time it is
   read. Measured: `$!` = 2091060, leader = 2091061, `pgid` = 2091061. The off-by-one is a
   coincidence of fork ordering, not a contract, so the generator now publishes its pid to
   `LOAD_PIDFILE` and the driver reads it.

A fourth issue was cosmetic but mattered for provenance: an interrupted load logged
`duration reached`, misstating the condition a measurement was taken under. It now logs
`stopped EARLY (signal) … did NOT run its full Ns`.

**Cost of finding these the hard way**: killing the stalled driver let its blocked `wait` return, so
it advanced to the next block and started a fresh 10-worker load — which a `kill -KILL` on the
driver then **orphaned**, because KILL skips the exit trap. That orphan was hashing on 10 cores with
nothing supervising it. The reaper would not have caught it either: its cmdline references neither a
run root nor a run-dir pid file, which are the two protection keys — and it is not `systemd --user`
reparented in a way the predicate recognises.

### 8.4 Results

Run `headroom-sweep-20260902T111357Z`, 7 blocks x 3 cells, 26 minutes, every block `rc=0` and every
load reaching `READY`. Reproduce with
`python3 util/ad-hoc/2026-09-02_pf1_drive_extract.py --sweep <sweep_dir>`.

```text
block          workers  loadavg  n  mean step ms   vs quiet
00-quiet-a           0     5.92  3        18.282      -7.0%
01-sweep6            6    10.25  3        23.558     +19.9%  within quiet band -- NOT separable
02-sweep10          10    17.63  3        36.406     +85.2%  SEPARABLE
03-quiet-b           0    16.95  3        22.024     +12.0%
04-sweep8            8    17.32  3        36.589     +86.1%  SEPARABLE
05-sweep12          12    23.31  3        55.353    +181.6%  SEPARABLE
06-quiet-c           0    18.64  3        18.663      -5.1%

quiet baseline = 19.656 ms/step (3 quiet blocks: 18.282, 22.024, 18.663)
quiet spread   = 20.5%   <- the noise band
step count IDENTICAL across all 21 cells at every load level (804)
```

**The quiet controls span 20.5% among themselves**, in a 26-minute window, with no synthetic load
running. That is the single most consequential number here, and it is larger than the 13%
between-run drift of §5 of this document. It is also the reason no quiet block is discarded as
"contaminated": `03-quiet-b` ran directly after the 10-worker block and is the slow one, which
*looks* like incomplete recovery — but `06-quiet-c` ran directly after the **12**-worker block and
recovered fully (−5.1%). With three controls there is no way to separate residual load from ordinary
drift, and dropping the inconvenient one would manufacture the very separation being tested for.

**What the sweep establishes:**

1. **The knee is between 6 and 8 synthetic workers, and it is sharp** — +19.9% to +86.1%. Below it,
   nothing is attributable; above it, the effect is unmistakable.
2. **6 workers is NOT separable from noise.** At +19.9% against a 20.5% band, the mildest load point
   carries no information. Note the direction this cuts: it does *not* show 6 workers are harmless,
   it shows this instrument cannot tell.
3. **8 and 10 workers are indistinguishable** — 36.589 vs 36.406 ms, 0.5% apart. They ran **seven
   minutes apart and out of order** (10 first), so a time-ordered artifact cannot produce this. It is
   a genuine plateau: past the knee, adding load stops mattering until 12.
4. **12 workers costs +181.6%**, consistent with the +90–165% previously measured at 14 workers.
5. **`step_count` is 804 in all 21 cells, at every load level**, across a **3x** span of step
   duration (18.3 → 55.4 ms). The work invariant holds under contention severe enough to triple
   runtime. This is the strongest evidence available for decision 1's work-gate, and it was not
   obtainable before this sweep.
6. The design controls worked. `01-sweep6` also reproduced across two independent runs — 23.558 ms
   here against 23.410 ms in the aborted first attempt (§8.3 of this document), 0.6% apart.

**What it does not establish.** A free-core *floor* in absolute terms. The synthetic worker count is
not free-core headroom: ambient load was 5.92 at the start and never returned to it, so "6 workers"
means six workers *on top of* an unquantified ambient occupancy. The knee is located in worker
count, not in cores. Locating it in headroom would need per-core occupancy sampled during each cell,
which this sweep does not collect.

**Consequence for decision 2.** The sweep independently confirms it from a second direction: with a
20.5% quiet band, a speed gate would need a threshold above 20.5% merely to avoid firing on an
unloaded host — at which point it cannot see the 19.9% that six competing processes cost. Speed is
not gateable here, and the answer does not depend on the instrument-resolution argument of §1–§4 of
this document.

---

## 9. What this does not settle

- **Whether modest load actually costs anything.** §4.3 of this document removes the `+0.051%`
  answer without supplying a replacement, and the sweep does not supply one either: its closest
  point, 6 workers at +19.9%, sits inside a 20.5% quiet band (§8.4 of this document). The question
  is now *better characterised* and still open — a light load's cost is below what this host can
  measure, which is a different statement from "a light load is free".
- **Where the free-core floor sits in cores.** The knee is located between 6 and 8 *synthetic
  workers*, not at a headroom figure, because ambient occupancy was neither zero nor constant.
  Converting one to the other needs per-core occupancy sampled during each cell.
- **The 66 s and 126 s runs' `drive` figures are not refuted.** At those lengths `drive` and
  `step_sum` agree to ~1x (§3 of this document). The +90–165% contention finding stands.
- **The cause of the 13% drift is unidentified.** Thermal state, page cache, ambient host activity
  and CPU frequency scaling are all candidates; none was instrumented.
- **Other duration classes remain unmeasured** on the resolving instrument. E-A/E-C sit at hundreds
  of seconds.
- **`max_epochs` / `output_epochs`.** `spiral-smoke.yaml` still sets `max_epochs: 50` with no
  `output_epochs`, so under the service path later output passes fall back to 10000. §5 of the 60 s
  variance results
  ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md))
  requires both keys before any figure from it is quoted as a baseline. Unchanged by this document,
  and it applies to the step counts here as much as to any other figure — 804 and 4012 are stable
  *across repeats*, which is what the work-gate needs, but they are not the counts the config
  appears to ask for.

---

## 10. Reproduction

```bash
# Two-instrument comparison across every PF-1 run (no transcription)
python3 util/ad-hoc/2026-09-02_pf1_drive_extract.py

# The quantization itself: drive against poll count
python3 -c "import json,pathlib;d=json.loads((pathlib.Path.home()/'.local/state/juniper-experiments/20260901T103325Z-cc9b/manifest.json').read_text());print(d['timings']['drive'], d['drive_loop']['polls'])"

# The headroom sweep (~30 min, needs owner approval for host time)
setsid nohup bash util/ad-hoc/2026-09-02_headroom_sweep.bash > sweep.log 2>&1 &
```
