# PF-1 under load, and with the bridge — the contention floor is duration-scoped, and `metrics_scraped` is vacuous

> **CORRECTED 2026-09-02 — §1's three-row comparison cannot support its conclusions.** All three
> rows differ in `drive` by **less than 0.06%**, which is inside the blind spot of a metric quantized
> to the driver's 5-second poll interval; at 20 s all three runs sat in the same poll cycle. On the
> poll-independent step-duration histogram the same runs differ by **−11.5%** (unbridged → bridged)
> and **+15.0%** (bridged quiet → modest load). So neither *"the bridge costs nothing"* nor
> *"a 20-second `drive` phase is effectively immune"* is supported, and with them goes the
> duration-scoping claim in the title **as evidenced at 20 s**. This does not show the opposite
> either: two *quiet* runs differ by 11.5%, so load is not separable from run-to-run drift at n=1 per
> condition. The 0.5% threshold candidate derived in §2 sits far below the real noise floor. See
> [`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md)
> §3, §4.2 and §4.3. The `metrics_scraped` finding is unaffected and stands.

**Executes** the two runs the owner approved in the P3 decisions on
[`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md) §6:
the **loaded-repeat test** (decision 2) and the **bridged re-run** (decision 4, which rejected
dropping step duration). Decision 1 ratified `timings.drive` as the metric; decision 3 deferred the
threshold to this analysis.

**Still not a ratification.** Candidate thresholds are derived below under P1 §5's rule; ratifying
them remains the owner's.

---

## 1. The §3.1 question is answered: the contention floor **is** duration-scoped

| condition                    | load avg                      | `drive` mean | `drive` sd | sd %       | `total` sd % |
|------------------------------|-------------------------------|--------------|------------|------------|--------------|
| unbridged, interactive       | 6.31                          | 20.084 s     | 0.0065     | 0.033%     | 0.370%       |
| bridged, quiet               | 3.12                          | 20.081 s     | 0.0099     | 0.049%     | 0.343%       |
| **bridged, deliberate load** | **6.6 + 4 synthetic workers** | **20.091 s** | **0.0084** | **0.042%** | 0.293%       |

**Under a deliberate clamscan-shaped load, `drive` moved by +0.051%** (20.081 → 20.091 s) and its
spread did not widen at all.

The load was 4 parallel recursive-checksum workers over a conda tree — CPU hashing plus sustained
small-file reads, the shape a virus scanner produces — deliberately an **upper bound**: clamscan ran
as roughly one process, this ran four of sixteen cores, and load average reached 8.8. A 20-second
`drive` phase is effectively immune to it.

**So the 6.8% figure does not generalise to short scenarios.** It was measured on a **552-second**
cell; these are **20-second** ones. Both can be true — a long run cannot avoid overlapping sustained
contention, a short one can finish between bursts. What is now established is that the floor is a
function of run duration, and PF-1-class scenarios sit far below it.

**What this does NOT establish**: that the 552 s figure was wrong, or that long scenarios can be
gated tightly. Nothing here re-measured that duration class. It also does not cover a load that
saturates all 16 cores; 12 were left free, which is plausibly why the workload was untouched.

---

## 2. Candidate thresholds (for ratification, not ratified)

P1 §5's rule: **≥3× sd, and never below the largest contention excursion observed on this host** —
now qualified by §1 as *for the relevant duration class*.

| input                              | value                                |
|------------------------------------|--------------------------------------|
| 3 × sd(`drive`, loaded)            | 3 × 0.0084 s = 0.0252 s → **0.125%** |
| largest excursion at this duration | **+0.051%**                          |
| **binding constraint**             | **3-sigma, at 0.125%**               |

For the first time the *statistical* term binds rather than the contention floor, because the floor
collapsed from 6.8% to 0.05% once measured at the right duration. That is a **54× improvement in
achievable sensitivity**.

**Recommended candidate: a 0.5% regression threshold on `timings.drive` for PF-1-class scenarios**
(≈4× the 3-sigma figure, ≈10× the observed contention excursion). Deliberately looser than the
0.125% floor demands: 5 repeats is a small sample, and a threshold that sits only just above
3-sigma will fire on ordinary tail behaviour. 0.5% still detects a regression 10× smaller than the
6.8% figure would have allowed.

**Do not apply this to long-running scenarios** (E-A/E-C class, hundreds of seconds) without
measuring their duration class. §1 establishes the floor varies with duration; it does not say how.

---

## 3. `metrics_scraped.present` is a vacuous check

The bridged runs all record `metrics_scraped: {grafana_bridge: true, present: true}`. Prometheus
holds **zero** series for them:

```text
count by (run_id) (juniper_cascor_training_step_duration_seconds_bucket{environment="host-experiment"})  -> 0
up{environment="host-experiment"} @ run-B time                                                           -> 0
```

Not "the metric is missing" — **nothing from these runs was ever scraped**. The cause is the
field's definition (`run_experiment.py:1602`, and again at `:1950`):

```python
"present": (run_dir / "artifacts" / "prometheus_target.json").is_file(),
```

It asserts **a JSON file exists on disk**. It does not check that Prometheus discovered the target,
scraped it, or retained a sample. A field named `metrics_scraped` whose sub-field is `present`
reads as "metrics were scraped and are present" — and it cannot fail for that reason, because
writing the file is the same act that sets the flag.

This is not academic: **it misled this analysis**. On seeing `present: true` across five runs I
recorded that the bridge fix worked end-to-end. It had — the file was written, the relay ran — but
the metric the run existed to capture was still absent, and the field said nothing about that.

**Recommended fix (not made here):** rename to `target_file_written`, and add a genuinely falsifiable
`scrape_confirmed` that queries Prometheus for at least one sample bearing this `run_id`. A
provenance field that cannot fail is worse than an absent one, because it is quoted as evidence.

---

## 4. Step duration is not capturable at PF-1's cell duration

Decision 4 rejected dropping step duration and approved a bridged re-run. **The re-run happened,
the bridge worked, and there is still no step-duration data** — for a reason the bridge cannot fix.

The host-experiments job uses `refresh_interval: 15s` (file_sd discovery) and `scrape_interval: 15s`,
against a cascor service that lives roughly **20 seconds** per cell. The target file is written at
bring-up and deleted at teardown, so the discover-then-scrape cycle has to complete inside that
window. It did not, for any of the five cells, in either bridged run.

Three ways forward, in preference order:

1. **Lengthen PF-1's cells** so the service outlives discovery + scrape by a comfortable margin
   (≥60 s). This keeps step duration and costs only run time — but it changes PF-1's config, so the
   variance figures above would need re-measuring at the new duration.
2. **Shorten the host-experiments intervals** (e.g. 5 s / 5 s) for the experiment job only. Cheap,
   but it changes a shared Prometheus config for the benefit of one lane.
3. **Accept `drive` as the run-tier quantity** and record step duration as unavailable at this scale.

Not chosen here — decision 4 was explicit that step duration stays, and choosing between these is
the same kind of call. Recorded so the choice is made deliberately rather than by the metric
quietly staying empty.

---

## 5. The bridge costs nothing where it matters

`drive` means: **20.084 s unbridged, 20.081 s bridged** — three milliseconds apart across
independent runs. Meanwhile suite `wall_seconds` rose from 33.9 s to 35.7 s (~+1.8 s/cell) and the
driver's `total` did not move.

So the bridge's entire cost sits in **stack bring-up**, outside both the driver and the workload.
This is a second, independent argument for decision 1's ratified metric: a threshold on
`wall_seconds` would have registered *switching on instrumentation* as a 5% regression.

---

## 6. A defect in this session's own tooling

`util/ad-hoc/2026-08-31_pf1_launch.bash` claimed to record host snapshots **before and after** each
run. The after-snapshot **never once ran**, across all three PF-1 executions.

The hook invoked the script by path (`'${BASH_SOURCE[0]}' --snapshot-after …`) — a relative path, and
the file carries no execute bit, so every invocation died with *Permission denied* into the `|| true`
that was there to stop a snapshot problem failing a run. The suppressor that made it non-fatal also
made it invisible.

Fixed: resolve the path absolutely, invoke via `bash`, and replace the silent `|| true` with a
logged warning. The `before` snapshots are intact and are what §1's load figures rest on; the run-B
load condition is additionally established by the load generator's own 420 s window (02:21–02:28
UTC) fully containing run B (02:21–02:24 UTC).

---

## 7. For the owner

1. **Ratify or adjust the 0.5% candidate** on `timings.drive` for PF-1-class scenarios — §2.
    - Response: i concur. a 0.5% regression threshold strikes a good balance between sensitivity and noise tolerance. this is a design choice that we should come back and verify after this gate goes live.
2. **Choose among the three step-duration options** — §4. Decision 4 kept the metric; it is not obtainable at the current cell duration without one of these.
    - Response: let's go with option 1: lengthening the time for PF-1's cells.  ~60 s is a good first choice; i'd be willing to go as high as ~120 s if necessary.
3. **Note the `metrics_scraped` fix as a defect to schedule** — §3. It is not perf-lane work, but it produced a false positive in this analysis and will produce more.
    - Response: implementing the recommended fix for the metrics_scraped.present defect should be considered a high priority.
    the ability to include a range of potentially complex metrics in the performance calculations and checks will become increasingly important as the underlying model architectures become larger, hybridized, and more complex.
    the metrics scraping functionality will also become increasingly important as additional, and heterogenous, systems are brought online to support juniper platform compute.
4. **Long-duration scenarios remain unmeasured.** The 0.5% candidate is explicitly scoped to PF-1-class runs; E-A/E-C-class durations need their own measurement before any threshold.
    - Response: i concur. classes other than PF-1 should have their own run measurements performed.
