# Performance lane — P2 Planning: work items, sized and sequenced

Operator surface for the shipped PF-1…PF-7 instruments (how to run, PF-1 traps, PF-3 stall/wall, PF-4/PF-8 not driver suites): [`docs/REFERENCE.md` § PF Scenario Suites](../docs/REFERENCE.md#pf-scenario-suites).

> **Operator surface (2026-09-05, supersedes the 2026-09-04 banner).** The work-gate tools
> (`read_run_metrics` / `make_baseline` / `compare_baseline`) shipped, and the premise consensus
> validation ([juniper-ml#1710](https://github.com/pcalnon/juniper-ml/pull/1710)) attacked is now
> **settled**: `step_count` was not *wrong*, it was **under-specified**. A corpus census over 333
> runs / 153 distinct configs found 29 of the 79 repeated configs divergent, and **all 29 are
> explained by `completion_reason` — none remains divergent within a termination branch**. `ml#1733`
> made the branch part of the precondition (a flip now REFUSES, exit 2, rather than FAILing), and
> `ml#1741` + `ml#1743` closed the two fail-open holes and all six comparator defects (A1–A4, A6, A7).
> **Do not wire the exact-match work gate to CI** — but the reason has changed: it is now an unmade
> **owner** decision (*whether the run tier gates CI at all*, §6 of the P1 design), not a soundness
> bar. Operator contract: [`docs/REFERENCE.md` § Perf-Lane Work Gate](../docs/REFERENCE.md#perf-lane-work-gate).

**Closes P2** of the four-phase gate in §1.1 of the phasing note
([`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md)),
whose deliverable is *"work items with repo, size, and dependencies — the §14-style wave table this
program uses everywhere else"*, done when *"items are enumerated and sequenced"*.

**Out of order, deliberately.** Tier 4 of that same phasing note sequences the lane
**F-P1 → F-P2 → F-P3 → F-P4**, and P3 measurement ran first at the owner's direction. That
compression turned out to be load-bearing rather than merely convenient: the P3 measurements
recorded in the instrument-resolution results
([`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md))
de-ratified the metric a P2 written in August would have planned around, and would have made most of
Wave 1 below wrong. A P2 authored before P3 would have been a plan to build the wrong comparator.

**Scope.** This document enumerates and sequences. It ratifies no thresholds (P3's job, and §7 of
the instrument-resolution results records the decisions already taken) and writes no operator docs
(P4's job). Item 1.4's operator surface now lives in
[`docs/REFERENCE.md` § Suite Report Gate Inputs](../docs/REFERENCE.md#suite-report-gate-inputs)
(juniper-ml#1643).

**Operator surface (item 3.1).** Recurrence work is **not countable**: `n_epochs` is degenerate
(1-or-200 by readout type), `n_windows` is input size, and the tooling refuses to baseline or gate
on speed alone. Runbook: [`docs/REFERENCE.md` § Recurrence Work Is Not Countable](../docs/REFERENCE.md#recurrence-work-is-not-countable).

---

## 1. What P3 already settled, and what it costs this plan

Five results from the instrument-resolution results
([`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md))
constrain every item below.

| # | result | consequence for P2 |
|---|---|---|
| 1 | `timings.drive` is poll-quantized and **de-ratified** | No item may gate on it. The comparator reads the step-duration histogram. |
| 2 | Gate is **split**: exact `step_count` (work), ungated speed | Wave 1's comparator has two halves with different contracts, not one threshold. |
| 3 | Between-run drift is **13%**, quiet-block spread **20.5%** | Any stored-baseline comparison inherits that floor. This is what breaks PF-4 as written. |
| 4 | `step_count` is invariant under contention (804 across 21 cells, 3x speed range) | The work half needs no host-state precondition. It is the only part of the lane that can gate today. |
| 5 | The resolving instrument is Prometheus-independent (driver samples `/metrics` directly) | No juniper-deploy dependency for the gate itself; the bridge remains needed only for Grafana surfaces. |

### 1.1 The single largest saving: both gate inputs already exist

`step_duration_stats` in `util/experiments/stats_summary.py:92-122` already computes, and every run
already persists to `artifacts/results/stats.json` under `cascor.training_step_duration`:

```json
{
  "basis": "per-poll mean (delta-sum/delta-count); true per-step quantiles are not recoverable from a sum/count exposition",
  "overall_mean_seconds": 0.03074124190157348,
  "total_steps": 4012,
  "p50_seconds": 0.03033643303635089,
  "p95_seconds": 0.07510142156454717,
  "poll_samples": 25
}
```

`total_steps` **is** the work half; `overall_mean_seconds` **is** the speed half. **No new
instrumentation, no cascor change, and no metric family is required for the cascor gate.** Wave 1 is
therefore a comparator over an existing artifact, not an instrumentation project — which is why it
is sized S/M rather than L.

Note the `basis` string is honest and matters: `p50`/`p95` are per-poll means, not true per-step
quantiles. The gate uses `total_steps` and `overall_mean_seconds`, both of which are exact.

> **CORRECTED 2026-09-04 — §1.2 below overstated the gap, and item 3.1 has now ANSWERED its open
> question with a "no".** The claim that *"recurrence timing exists only as Prometheus gauges"* is
> **wrong**: the driver already records `timings.train` and `timings.crossval` in every recurrence
> manifest (`_phase("train", …)`), and `stats.json` already carries them under `outcome.timings`.
> They are driver-measured and Prometheus-independent, and — unlike cascor's `drive` — carry **no
> quantization**, because `POST /v1/train` is synchronous: the response *is* completion, so there is
> no poll loop. The real gap was narrower: `read_run_metrics` knew only the cascor histogram, so the
> reader and comparator could not consume a recurrence run at all. Fixed.
>
> **The open question — is `n_epochs` a usable work-count analogue? — is answered NO**, from a survey
> of 36 real recurrence runs rather than from repeats:
>
> | candidate | measures | verdict |
> |---|---|---|
> | `n_epochs` | iterations to convergence | **degenerate** — exactly two values across 36 runs, **1** (28, "converged") and **200** (2, "max_epochs"), tracking the *readout type*. Invariant to `d` and `n_steps`, the two dimensions PF-5 and PF-6 exist to vary. |
> | `dataset.n_windows` | input size | varies (349 / 1346 / 1574 / 3149) but is fixed by the config. A code change doing redundant work does not move it. |
> | `timings.train` | duration | this is the **speed** half, not work. |
>
> cascor's `step_count` measures work **done**; `n_windows` measures work **asked for**. So the split
> gate's WORK half **has no recurrence equivalent**, and PF-5/6/7 can be **reported but not gated**
> without new instrumentation inside juniper-recurrence itself.
>
> The tooling now says so rather than mis-gating: `read_run_metrics` returns `work_countable: False`
> with a reason, `summarise` keeps that as a **third state** distinct from "counted and matched",
> `make_baseline` **refuses** to bless such a run (a baseline exists to support the work gate; a
> speed-only reference would invite exactly the comparison the drift floor rules out), and
> `compare_baseline` refuses with the same explanation.

### 1.2 The single largest gap: recurrence has no timing surface at all

`stats_summary.py:246-253` builds the recurrence block from `final_metrics`, `n_epochs`,
`stopped_reason`, `dataset_descriptor`, `theta`, `readout` and `crossval`. **There is no duration
field of any kind.** Recurrence timing exists only as
`juniper_recurrence_{train,crossval}_last_duration_seconds` reaching Prometheus through the service
path — and §0 of the tail re-probe
([`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md))
records that **zero** recurrence series have ever been observed under `environment="host-experiment"`.

Consequence: **PF-5, PF-6 and PF-7 cannot be gated in the same shape as the cascor scenarios**, and
cannot even be *reported* on a run-tier timing basis, until item 3.1 lands. This is the most
significant dependency this plan discovers, and it was not visible before P3.

Whether `n_epochs` is a usable work-count analogue for recurrence is **open** — cascor's
`total_steps` is invariant because the budget is iteration-capped, whereas recurrence trains to an
early-stopping criterion. Item 3.1 must answer it with repeats, not assume it.

---

## 2. Work-item summary and sequencing

Dependency-ordered. Size: **S** ≈ one focused sitting, **M** ≈ a day, **L** ≈ multi-day. Each row is
intended as **its own PR** unless noted.

### Wave 0 — Corrections that gate every measurement below (no gate code)

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 0.1 | This plan, reviewed and ratified by the owner | juniper-ml | S | — |
| 0.2 | **SHIPPED — `cascor#618`.** **`spiral-smoke.yaml` must set `output_epochs` alongside `max_epochs: 50`.** The service applies `max_epochs` only to the *initial* output pass; later passes read `output_epochs`, which falls back to 10000, so the service is quietly better-trained and slower than the config asks. Required by §5 of the 60 s variance results ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md)) before **any** figure from it is quoted as a baseline. PF-1 uses it as `base_config`, and item 1.1 turns PF-1 output into the reference. | juniper-cascor | S | 0.1 |
| 0.3 | **DONE 2026-09-02 — calibrated to 4000 epochs; `drive` median 65.3 s, `step_count` 1770 invariant across 5 repeats (§2.1 of this document).** **Re-calibrate PF-1's override, then re-run.** 0.2's measured effect is far larger than this row originally assumed: at PF-1's `(10, 10)` budget the corrected config runs **15.1 s / 32 steps** against **65–126 s / 4012 steps** before. That is below the ~40 s scrapeability floor (`scrape_confirmed` false), so **0.2 undoes 2026-09-01 owner decision 2** — cells lengthened to ~60 s. PF-1 must override `max_epochs` **and** `output_epochs` together at a calibrated value to restore ~60 s, then re-run 5 repeats and re-confirm `total_steps` invariance. The duration requirement belongs to PF-1, not to a config whose purpose is a fast smoke run. | juniper-ml | M | 0.2 |
| 0.5 | **`xor-staged.yaml` carries the same undocumented split** (`max_epochs: 200`, no `output_epochs`). `spiral-baseline.yaml` (2000 / unset) splits *deliberately* and is documented as such; `xor-staged` is not, and no suite consumes it. Decide intent and either set both keys or record the split as intentional. | juniper-cascor | S | — |
| 0.6 | **DONE 2026-09-03** — `EpochBudgetSplitDriftTest` in `tests/test_experiment_config_schemas.py`, with blessed and pending-decision exemptions kept in *separate* dicts, a staleness check so an exemption cannot outlive its condition, and always-on predicate self-checks (the cross-repo walk skips in the normal CI job). Both negative controls verified to fail. Also fixes `ECOSYSTEM_ROOT` resolution, which made the whole cross-repo walk skip vacuously from an in-repo worktree. **Add a drift gate** so this cannot recur silently: extend `tests/test_experiment_config_schemas.py` to fail any cascor experiment config that sets `max_epochs` without `output_epochs`, with an explicit allowlist for the configs that split deliberately. Today the only defence is a driver **warning**, which lands in the manifest and is easy to read past — every PF-1 run carried it and the campaign ran anyway. | juniper-ml | S | 0.5 |
| 0.4 | **DONE 2026-09-03.** Promote `util/ad-hoc/2026-09-02_pf1_drive_extract.py` to `util/experiments/read_run_metrics.py` + `tests/test_read_run_metrics.py` (18 tests, wired into `ci.yml`). The ad-hoc original is **retained** as provenance per the 2026-08-25 policy and marked superseded in its docstring. It is now the canonical reader for both gate inputs and the only tool that reads them without going through the de-ratified `wall_seconds` in `aggregate.csv`. | juniper-ml | S | 0.1 |

**Why 0.2 → 0.3 is a hard edge and not a formality.** Every number in the instrument-resolution
results, including the 804/4012 invariance that justifies the work gate, was measured under the
uncorrected budget. The invariance is very likely to survive — but "very likely" is not the standard
for the one property the gate rests on.

> **Correction (2026-09-05).** The stated cause above was wrong and is **withdrawn**. This sentence
> originally read "it follows from the iteration cap, not the epoch budget". It does not: **every**
> PF-1 run, at both 20 s and 65 s, terminates `early_stopped`, so **none is cap-bound** and the cap
> cannot be what makes the count invariant. The 21-cell invariance is a real empirical regularity
> with a misattributed mechanism. The mechanism actually established by the `ml#1733` census is the
> **termination branch**: `step_count` is exact and deterministic *given how training ended*, and
> divergence appears only when the branch moves (or `max_wall_seconds` truncates the histogram).
> This matters beyond bookkeeping — the baseline `pf1-2026-09-04` was cut from an early-stopping
> workload, i.e. the same class as the counterexample, which is precisely why the guard, not the
> cap, is what makes the comparison safe.

**Measured 2026-09-02, and it is bigger than this plan first assumed.** The correction was probed on
two live cells before touching the shared config (`util/ad-hoc/2026-09-02_output_epochs_impact_suite.yaml`,
expressed as a suite override so the primary cascor checkout was not edited mid-measurement):

| at PF-1's `(10, 10)` | `max_epochs: 50` only | `+ output_epochs: 50` |
|---|---|---|
| `timings.drive` | 65.2–125.8 s | **15.09 s** |
| `step_count` | **4012** | **32** |
| `scrape_confirmed` | true | **false** |

The service was doing **~125x** the work the config requests. Two consequences the original 0.3
did not carry: the corrected run falls below the scrapeability floor, so PF-1 needs re-calibration
rather than a bare re-run; and **`step_count` is dominated by output-pass epochs**, which means the
work gate's *sensitivity* is set by the epoch budget — a fact worth knowing before item 1.2 fixes a
tolerance of zero.

The split also **surfaces at the native `(2, 2)` budget**, refuting the claim at
`util/experiments/run_experiment.py:242-243` that smoke-scale runs cannot show it: `output_epoch`
rows reach 10000 for *both* non-initial passes, and 10000 can only be the `output_epochs` fallback
since the candidate default is 400.

### 2.1 Item 0.3 executed — the epoch budget is 4000, and the work invariant survives

**Calibration** (`util/ad-hoc/2026-09-02_pf1_epoch_calibration_suite.yaml`), all at PF-1's `(10, 10)`
with both epoch keys matched:

| epochs | `step_sum` | `step_count` |
|---|---|---|
| 50 | 10.5 s | 32 |
| 500 | 22.2 s | 230 |
| 2000 | 34.6 s | 890 |
| 5000 | 66.1 s | 2210 |

**The curve is not a single power law, and assuming it was produced a wrong answer.** The log-log
slope is **~0.32** up to 2000 and **~0.71** from 2000 to 5000 — early stopping binds below ~2000 and
stops binding above it. A fit on the low segment predicts **46 s** at 5000 against **66 s** measured.

That fit looked *validated* before the 5000 point arrived, because it reproduced the pre-fix run's
~62 s to within 1%. That agreement was spurious: the pre-fix run is **not** a uniform-epoch point at
all — it was 50 on the initial pass and 10000 on every later one, a mixed configuration with no place
in the fit. Two errors cancelling is not confirmation, and one extra measured point was enough to
separate them.

Interpolating **within the upper segment** gives ~3900 for a ~55 s `step_sum`. **4000** is used.

**Re-run result** (5 repeats, `JUNIPER_SUITE_GRAFANA_BRIDGE=1`):

```text
cell   polls   drive    step_sum   steps   mean_ms
c000     13    60.239    58.507    1770    33.055
c001     15    70.263    66.016    1770    37.297
c002     14    65.234    63.383    1770    35.809
c003     15    70.259    67.044    1770    37.878
c004     14    65.272    61.553    1770    34.776

drive     median 65.272   sd 6.327%
step_sum  median 63.383   sd 5.439%
step_count IDENTICAL across all 5 cells (1770)
```

- **Duration restored**: median 65.3 s, inside decision 2's ~60 s target and well under its 120 s
  ceiling.
- **The work invariant survives the corrected budget** — 1770 in every cell, matching the 1770 the
  interpolation predicted. This is the property the whole work-gate rests on, and item 0.3 existed to
  re-establish it after 0.2 changed the workload.
- **Sample size improved 55x**, from 32 steps to 1770, so the per-step mean is far better determined
  than at the corrected config's native budget.

**Scrapeability was NOT re-confirmed, and that is an environment state rather than a result.** The
bridge was armed and `target_file_written` is true, but Prometheus was down
(`connection refused` on `127.0.0.1:9090`), so `scrape_confirmed` is **`None`** — the tri-state's
"could not ask". That is `metrics_scraped` behaving exactly as ml#1550 designed it; the old boolean
would have recorded a false negative here. At 65 s the run sits far above the ~40 s floor established
on 2026-09-01 (40.17 s → confirmed, 255 series), so nothing suggests a problem — but it is untested
since, and should be re-checked the next time the observability stack is up.

**Figures before and after 2026-09-02 are not comparable.** Pre-fix was 50-initial + 10000-later;
this is 4000 uniform. The duration is restored, the workload is not the same one — necessarily,
because the old one was incoherent by construction. This bears directly on item 1.1: PF-1 output is
what becomes the Q-8 baseline, so the baseline must be cut from post-fix runs only.

### 2.2 Item 1.5 decided — a `step_count` mismatch FAILS, behind an identity precondition

**Owner decision, 2026-09-04: a `step_count` mismatch is a FAILURE, not a warning.** That is the
tight half of the split gate doing its job — the work count is exact by construction and
contention-immune, so a change in it is a real statement about the code, never about the host.

The rest of this section is what the decision needs in order to survive contact, and it is the part
the original 1.5 row warned about: *"without a documented waiver path the gate gets switched off the
first time it fires correctly."*

#### The precondition: identity before comparison

A mismatch only means *"the code regressed"* when both sides ran the **same workload**. So the
comparator's **first** check is identity, and the two outcomes are kept distinct:

| condition | verdict | exit |
|---|---|---|
| workload fingerprints differ | **REFUSE** — invalid comparison, not a regression | non-zero, but a *different* code from a failure |
| fingerprint unknown on either side | **REFUSE** — cannot compare what cannot be identified | as above |
| same workload, `step_count` differs | **FAIL** — work regression | failure |
| same workload, `step_count` matches | PASS; speed reported, never gated | 0 |

Collapsing the first two rows into "fail" is how the gate would get switched off: an ordinary config
edit would be reported as a code regression, everyone would learn the gate lies, and it would be
disabled while still green.

#### `config_sha256` cannot serve as that identity — measured, not assumed

`registry.jsonl` carries a `config_sha256` per cell, and the obvious move is to compare it. It does
not work: it hashes the whole materialised cell YAML **including `experiment.description`**, and
PF-1's five repeats differ precisely there. Measured 2026-09-03 on
`pf1-cascor-spiral-repeats-20260903T040803Z`: **five cells, five different `config_sha256` values.**
A comparator using it would refuse every legitimate comparison, including a suite against its own
baseline.

`read_run_metrics.workload_fingerprint()` hashes the same YAML with the cosmetic keys
(`experiment.description`, `experiment.name`) removed. `experiment.seed` is deliberately **not**
cosmetic — two runs at different seeds are different workloads.

Verified both directions:

- **Stable across repeats** — `52184ba2…` for all five PF-1 cells.
- **Moves when the workload moves** — pre-`cascor#618` reads `d09edcc1…`, post-fix reads
  `52184ba2…`. So the "figures before and after 2026-09-02 are not comparable" boundary is detected
  **mechanically**, not remembered.

#### The waiver path

A deliberate workload change is legitimate and must be landable. The escape is an explicit
`--accept-work-change "<reason>"` on the comparator, which:

- requires a **non-empty reason** (a bare flag is not an argument),
- yields the verdict **`WAIVED`**, never `PASS` — the artifact records that the gate fired and a
  human overrode it,
- writes the reason into the comparison output, so the next reader sees *why* the work moved.

This mirrors `make_baseline.py --accept-warnings`, which already refuses runs carrying
`validation_warnings` unless the acceptance is recorded. Same principle: the escape exists, and
using it leaves a trace.

**The right response to a legitimate workload change is usually a NEW BASELINE, not a waiver** —
baselines supersede by name and are cheap. The waiver is for the case where a comparison must be
run before a new baseline can be blessed.

#### What this does not decide

Whether the run tier ever gates **CI** remains open (§6 of the P1 design,
[`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)).
Item 1.5 fixes what the comparator *does*; wiring its exit code to a required check is a separate
owner decision, and until it is taken the comparator is an operator tool whose failure is read by a
person.

### Wave 1 — The gate contract (cascor only; the whole point of the lane)

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 1.1 | **DONE 2026-09-03** — `util/experiments/make_baseline.py` + `tests/test_make_baseline.py` (19 tests, wired into `ci.yml`). Refuses to overwrite a tag (no `--force` exists, asserted behaviourally), refuses a broken `step_count` invariant, failed or unmeasured runs, and runs carrying `validation_warnings` (overridable, recorded). `HOST.json` records CPU model/count, RAM, GPU, thread budget and torch/numpy — with an explicit caveat when the tool's interpreter differs from the runs', since the manifests carry only `juniper-*` versions. `util/experiments/make_baseline.py` — writes the Q-8 directory specified in §4 of the P1 design ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)): `baselines/<tag>/{baseline.json,manifests/<run_id>.json,HOST.json}`. Operator-invoked only, never a side effect of a run. `HOST.json` records CPU model/count, RAM, GPU presence, `torch`/`numpy` versions and the `runtime:` thread budget. **The directory does not exist on disk today.** | juniper-ml | M | 0.3, 0.4 |
| 1.2 | **DONE 2026-09-04** — `util/experiments/compare_baseline.py` + `tests/test_compare_baseline.py` (20 tests, wired into `ci.yml`). Three exit codes so a caller can tell the cases apart: **0** PASS/WAIVED, **1** FAIL (work moved), **2** REFUSED (identity, host, or an incoherent candidate). Verified live against the real artifacts: the recalibrated PF-1 run passes against its own baseline, and the **pre-`cascor#618`** run — 4012 steps against the baseline's 1770 — is **REFUSED as a different workload rather than reported as a 127% regression**. `util/experiments/compare_baseline.py` — the **split** comparator. Work half: `total_steps` must match the baseline **exactly**; any difference fails. Speed half: reports `overall_mean_seconds` delta and **never fails**, per decision 2 in §7 of the instrument-resolution results. Emits a typed verdict, and refuses to compare when `HOST.json` fingerprints differ. | juniper-ml | M | 1.1 |
| 1.3 | `tests/test_compare_baseline.py` + `tests/test_make_baseline.py`, both **negative-controlled** — a synthetic `total_steps` change must fail the gate, and a synthetic 50% speed change must **not**. Wire both into `ci.yml` (the test list is hand-maintained; new suites do not self-register). | juniper-ml | S | 1.2 (same PR acceptable) |
| 1.4 | **DONE 2026-09-04** — `aggregate.csv` now carries `step_count` and `mean_step_seconds` beside `wall_seconds`; `REPORT.md` gains a **Gate inputs** section stating that `wall_seconds` is de-ratified, plus the work-invariant and single-workload verdicts. `run_suite --compare-baseline TAG` records a comparator verdict in `REPORT.md` — **reporting only**: the suite's exit code is deliberately unchanged by the verdict, because whether the run tier gates is a separate owner decision (§6 of the P1 design), and a test pins that a FAIL verdict still exits 0. Surface the comparator verdict in `run_suite.py`'s `REPORT.md` and add a `comparison` block to `aggregate.csv`. **`aggregate.csv` currently carries `wall_seconds` only**, which is the de-ratified metric — a reader who trusts it analyses the wrong quantity with nothing flagging it. | juniper-ml | S | 1.2 |
| 1.5 | **DECIDED 2026-09-04 — a `step_count` mismatch FAILS.** Full rule, including the identity precondition and the waiver path, in §2.2 of this document. **Owner decision, not code**: what a `total_steps` mismatch *means* operationally. It is a true statement that work changed; it is not automatically a regression (a deliberate algorithm change moves it too). Needs a documented waiver path, or the gate will be disabled the first time someone legitimately changes the workload. | juniper-ml | S | 1.2 |

### Wave 2 — Execute the scenarios that have never run

**None of PF-1…PF-7 had ever been executed before 2026-08-31**, per §3 of the P1 design
([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)).
PF-1 has now run repeatedly. **PF-2, PF-3, PF-5, PF-6 and PF-7 still have not.**

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 2.1 | Execute **PF-2** (cascor dataset-size scaling) and file evidence | juniper-ml | S | 0.3 |
| 2.2 | Execute **PF-3** (candidate-pool × process scaling). Largest host-time cost in the lane: a 4×3 matrix at 2000 s driver budget. Needs an explicit host-time approval and a quiet window. | juniper-ml | M | 0.3 |
| 2.3 | Execute **PF-5 / PF-6 / PF-7** (recurrence) — **unblocked by 3.1, but REPORT-ONLY.** Recurrence has no work counter, so these scenarios can never be gated; their value is the scaling *curves* (fit time vs `d`, vs `n_steps`, per readout rung), not a pass/fail. Do not cut a baseline from them — `make_baseline` refuses, deliberately. | juniper-ml | M | 3.1 (done) |
| 2.4 | **PF-4 — establish** a cascor micro-level *timing* baseline. `baseline_20260526.json` holds 10 entries with **zero** timing data, and `test_baselines.py` defines three memory tolerances and no timing tolerance. PF-4's first task is creating the reference, not comparing against one. | juniper-cascor | M | 0.1 |
| 2.5 | **Design item, owner-facing**: PF-4's *comparison* semantics must be re-derived. A stored baseline is by construction a different run and therefore inherits the 13–20.5% drift floor of §5 and §8.4 of the instrument-resolution results. Options: gate PF-4 on operation *counts* rather than durations (the micro analogue of the split gate), accept a ≥20% timing tolerance, or keep PF-4 report-only. **Do not build 2.4's comparator before this is answered.** | juniper-cascor | S | 2.4 |

### Wave 3 — Recurrence parity (blocks the recurrence half of the lane)

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 3.1 | **DONE 2026-09-04 — and its open question answered NO.** The timings already existed (`timings.train` / `timings.crossval`, driver-measured, unquantized because `/v1/train` is synchronous); the gap was that `read_run_metrics` could not read a recurrence run. Now it can. **`n_epochs` is NOT a work-count analogue** — two values across 36 runs (1 / 200) by readout type, invariant to `d` and `n_steps`; `n_windows` is input size. So **PF-5/6/7 can be reported but never gated**, and the tooling refuses rather than mis-gating. Correction banner above §1.2 of this document. **Recurrence run-tier timing into `stats.json`.** `stats_summary.py:246-253` emits no duration field. The driver already receives train/crossval payloads; surface a duration and a work-count candidate (`n_epochs`, plus fold count for crossval) in the recurrence stats block, and **measure across repeats whether the work count is invariant** — early stopping may make it vary, which would mean recurrence has no work-gate analogue at all. | juniper-ml | M | 0.1 |
| 3.2 | ~~Add a `performance` pytest marker to the recurrence app~~ — **ALREADY DONE**. Registered at `juniper-recurrence/juniper-recurrence/pyproject.toml:153` with a comment naming "G-17 / CLI-experimentation plan 12.2 item 2"; `--strict-markers` makes registration a prerequisite rather than bookkeeping, and `tests/test_markers.py` pins it. Nothing is marked yet, which is the correct state — the marker must exist before the first test can carry one. **Carried here only so it is not re-enumerated a third time.** | juniper-recurrence | — | done |
| 3.3 | **G-17 second sub-item**: launch a recurrence run with `--grafana-bridge` and confirm recurrence timings actually appear under `environment="host-experiment"`. The panels and plumbing are believed correct; what has never happened is a bridged recurrence run. The enabler shipped in `juniper-ml#1547`; the consumer item was dropped. | juniper-ml | S | 3.1 |

### Wave 4 — PF-8, the item P1 deferred here

§3 of the P1 design
([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md))
deferred PF-8 to this plan with its shape stated: `run_suite`'s `execution.mode: parallel` runs cells
of **one** suite, not two suites at once, so no concurrent-launch harness exists.

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 4.1 | Concurrent-launch harness: start two suites with pinned, equal thread budgets and disjoint port ranges, and collect both. Must not reuse the sweep driver's naive teardown — see §4 of this document. **Two constraints from `util/experiments/run_suite.py:18-20`**: cascor `parallel > 1` is still **refused from one checkout** (Q-6's override landed in `cascor#523`, but `run_suite` cannot verify the installed cascor honours it — H-7), so a two-cascor-run PF-8 needs either two checkouts or a verified override; recurrence is unconstrained. A cascor+recurrence pairing is the cheapest first arm. | juniper-ml | L | 1.4 |
| 4.2 | `perf/pf8-two-run-concurrency.yaml` (or a harness-level descriptor if a suite cannot express it) + execution + evidence | juniper-ml | M | 4.1 |
| 4.3 | **Reconcile PF-8 with the headroom sweep.** §8.4 of the instrument-resolution results already answers a neighbouring question — the knee is between 6 and 8 competing workers — so PF-8's marginal value is now *"what does a second **Juniper** run cost"*, not *"is contention real"*. Re-scope before building 4.1, or it measures something already known. | juniper-ml | S | 1.4 |

### Wave 5 — Alerting

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 5.1 | ~~**Q-9**: exclude `environment="host-experiment"` from the experiment-facing alert rules~~ — **ALREADY DONE, and completely.** Verified 2026-09-02 by parsing `juniper-deploy/prometheus/alert_rules.yml`: **29 of 29 alerts carry `environment!="host-experiment"`**, including all three named in §12.4 item 4 of the CLI experimentation plan — `SlowDatasetGeneration` (`:207`), `CascorTrainStepLatencyFastBurn` (`:725`), `CascorTrainStepLatencySlowBurn` (`:800`) — and the three that reference no `juniper_*` series at all (`ServiceDown`, `ServiceRestartLoop`, `JuniperServiceScrapeDown`), which a series-level check would have missed. Zero partial coverage: no alert excludes on one series and not another. | juniper-deploy | — | done |
| 5.2 | Optional experiment-scoped alerts, if wanted. Genuinely optional — with 5.1 done there is no page risk, only an absence of experiment-specific signal. | juniper-deploy | S | — |

**The §12.4 line numbers have drifted** — that section cites `697`/`766` for the two cascor alerts,
which are now `725`/`800`. Anyone re-checking Q-9 by line number would land in the wrong rule.

---

## 3. Dependency graph

```text
0.1 ─┬─> 0.2 ──> 0.3 ─┬─> 1.1 ──> 1.2 ─┬─> 1.3
     │                │                ├─> 1.4 ──> 4.3 ──> 4.1 ──> 4.2
     │                │                └─> 1.5 (owner)
     ├─> 0.4 ─────────┘
     ├─> 2.1, 2.2  (need 0.3 only)
     ├─> 2.4 ──> 2.5 (owner)
     └─> 3.1 ─┬─> 2.3
              └─> 3.3

3.2  DONE (recurrence performance marker)
5.1  DONE (Q-9 alert scoping, 29/29)
5.2  independent, optional
```

**Critical path**: `0.1 → 0.2 → 0.3 → 1.1 → 1.2 → 1.4` — roughly S + S + S + M + M + S.

**Nothing is urgent-and-unbuilt.** An earlier draft of this plan put "do 5.1 first, it prevents live
pages" here; verification showed 5.1 was already fully done. The only genuinely time-sensitive edge
is `0.2 → 0.3`, and it is time-sensitive in the sense that **every measurement taken before it
describes a different workload**, not in the sense that anything is at risk.

### 3.1 Two items were already complete when this plan was drafted

3.2 and 5.1 were both enumerated as work and both turned out to be done — one shipped with a comment
naming the very plan section that requested it. Recorded rather than silently deleted, because the
pattern is the point: **§12-derived work items are stale by default.** §12 of the CLI experimentation
plan ([`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md))
was written 2026-07-29 and other sessions have been shipping against it since. Anyone picking up a
row below should re-verify it exists to be done before starting — and by file content, not by the
line numbers §12 quotes, two of which have drifted.

---

## 4. Hazards this plan inherits

- **`aggregate.csv` carries `wall_seconds` only** — the de-ratified metric. Item 1.4 exists because
  nothing currently warns a reader.
- **The juniper-ml CI test list is hand-maintained**; new suites do not self-register. Items 0.4 and
  1.3 must edit `.github/workflows/ci.yml` explicitly.
- **Pre-commit's Python hooks are scoped to `scripts/` and `tests/`**, so anything added under
  `util/` draws a vacuous *"(no files to check) Skipped"* and is **not linted**. Run `flake8` and
  `bandit` directly on `util/` work.
- **The driver's `outputs.max_wall_seconds`, not the suite's `per_run_timeout_seconds`, ends a run**
  (§1.3 of the phasing note,
  [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md)).
  Any scenario added by Wave 2 or 4 must be re-surveyed with
  `util/ad-hoc/2026-08-20_wall_ordering_survey.py`. *A timeout is not a measurement.*
- **A load generator that ignores a stop request.** §8.3 of the instrument-resolution results records
  three teardown defects found by running the sweep, including a bare `sleep` that defers a bash
  TERM trap for the full load duration, and a `kill -KILL` on a driver orphaning a 12-worker load the
  reaper cannot see. Item 4.1 launches two stacks concurrently and must not repeat them.
- **`include` cells do not inherit `matrix`** — repeats must be a matrix axis, or the cells are not
  repeats of each other.

---

## 5. What P2 does not decide

- **Threshold values** — none is proposed here. The work half is exact by construction; the speed
  half is ungated by decision 2 in §7 of the instrument-resolution results.
- **Whether the run tier ever gates CI** — §6 of the P1 design
  ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md))
  names it a separate owner decision. Items 1.1–1.4 build the comparator and its report; wiring it
  to a required check is out of scope here.
- **What a `total_steps` mismatch means operationally** — item 1.5, owner.
- **PF-4's comparison semantics** — item 2.5, owner.
- **Optimization work** — §12.5 of the CLI experimentation plan
  ([`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md))
  sequences it strictly after measurement, and nothing here advances it.

---

## 6. Acceptance for P2

§1.1 of the phasing note
([`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md))
sets the bar at *"items are enumerated and sequenced"*.

- [x] Items enumerated with repo, size and dependencies — §2 of this document
- [x] Sequenced, with a critical path and a dependency graph — §3 of this document
- [x] PF-8's deferral from §3 of the P1 design discharged into concrete items — Wave 4
- [x] Inherited hazards carried forward rather than rediscovered — §4 of this document
- [ ] **Reviewed — owner**

The two items most worth an owner's attention are **1.5** (what a work-count mismatch means, without
which the gate gets switched off the first time it fires correctly) and **2.5** (PF-4's comparison
semantics, which the drift floor makes non-obvious).
