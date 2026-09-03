# Performance lane — P2 Planning: work items, sized and sequenced

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
(P4's job).

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
| 0.2 | **`spiral-smoke.yaml` must set `output_epochs` alongside `max_epochs: 50`.** The service applies `max_epochs` only to the *initial* output pass; later passes read `output_epochs`, which falls back to 10000, so the service is quietly better-trained and slower than the config asks. Required by §5 of the 60 s variance results ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md)) before **any** figure from it is quoted as a baseline. PF-1 uses it as `base_config`, and item 1.1 turns PF-1 output into the reference. | juniper-cascor | S | 0.1 |
| 0.3 | Re-run PF-1 (5 repeats) after 0.2 and confirm `total_steps` is still invariant under the corrected budget. **0.2 changes the workload**, so every count and duration measured to date describes the old one. | juniper-ml | S | 0.2 |
| 0.4 | Promote `util/ad-hoc/2026-09-02_pf1_drive_extract.py` to `util/experiments/read_run_metrics.py` + `tests/test_read_run_metrics.py`, wired into `ci.yml`. It is now the canonical reader for both gate inputs and the only tool that reads them without going through the de-ratified `wall_seconds` in `aggregate.csv`. | juniper-ml | S | 0.1 |

**Why 0.2 → 0.3 is a hard edge and not a formality.** Every number in the instrument-resolution
results, including the 804/4012 invariance that justifies the work gate, was measured under the
uncorrected budget. The invariance is very likely to survive — it follows from the iteration cap,
not the epoch budget — but "very likely" is not the standard for the one property the gate rests on.

### Wave 1 — The gate contract (cascor only; the whole point of the lane)

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 1.1 | `util/experiments/make_baseline.py` — writes the Q-8 directory specified in §4 of the P1 design ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)): `baselines/<tag>/{baseline.json,manifests/<run_id>.json,HOST.json}`. Operator-invoked only, never a side effect of a run. `HOST.json` records CPU model/count, RAM, GPU presence, `torch`/`numpy` versions and the `runtime:` thread budget. **The directory does not exist on disk today.** | juniper-ml | M | 0.3, 0.4 |
| 1.2 | `util/experiments/compare_baseline.py` — the **split** comparator. Work half: `total_steps` must match the baseline **exactly**; any difference fails. Speed half: reports `overall_mean_seconds` delta and **never fails**, per decision 2 in §7 of the instrument-resolution results. Emits a typed verdict, and refuses to compare when `HOST.json` fingerprints differ. | juniper-ml | M | 1.1 |
| 1.3 | `tests/test_compare_baseline.py` + `tests/test_make_baseline.py`, both **negative-controlled** — a synthetic `total_steps` change must fail the gate, and a synthetic 50% speed change must **not**. Wire both into `ci.yml` (the test list is hand-maintained; new suites do not self-register). | juniper-ml | S | 1.2 (same PR acceptable) |
| 1.4 | Surface the comparator verdict in `run_suite.py`'s `REPORT.md` and add a `comparison` block to `aggregate.csv`. **`aggregate.csv` currently carries `wall_seconds` only**, which is the de-ratified metric — a reader who trusts it analyses the wrong quantity with nothing flagging it. | juniper-ml | S | 1.2 |
| 1.5 | **Owner decision, not code**: what a `total_steps` mismatch *means* operationally. It is a true statement that work changed; it is not automatically a regression (a deliberate algorithm change moves it too). Needs a documented waiver path, or the gate will be disabled the first time someone legitimately changes the workload. | juniper-ml | S | 1.2 |

### Wave 2 — Execute the scenarios that have never run

**None of PF-1…PF-7 had ever been executed before 2026-08-31**, per §3 of the P1 design
([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)).
PF-1 has now run repeatedly. **PF-2, PF-3, PF-5, PF-6 and PF-7 still have not.**

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 2.1 | Execute **PF-2** (cascor dataset-size scaling) and file evidence | juniper-ml | S | 0.3 |
| 2.2 | Execute **PF-3** (candidate-pool × process scaling). Largest host-time cost in the lane: a 4×3 matrix at 2000 s driver budget. Needs an explicit host-time approval and a quiet window. | juniper-ml | M | 0.3 |
| 2.3 | Execute **PF-5 / PF-6 / PF-7** (recurrence) — **speed results are not interpretable until 3.1** | juniper-ml | M | 3.1 |
| 2.4 | **PF-4 — establish** a cascor micro-level *timing* baseline. `baseline_20260526.json` holds 10 entries with **zero** timing data, and `test_baselines.py` defines three memory tolerances and no timing tolerance. PF-4's first task is creating the reference, not comparing against one. | juniper-cascor | M | 0.1 |
| 2.5 | **Design item, owner-facing**: PF-4's *comparison* semantics must be re-derived. A stored baseline is by construction a different run and therefore inherits the 13–20.5% drift floor of §5 and §8.4 of the instrument-resolution results. Options: gate PF-4 on operation *counts* rather than durations (the micro analogue of the split gate), accept a ≥20% timing tolerance, or keep PF-4 report-only. **Do not build 2.4's comparator before this is answered.** | juniper-cascor | S | 2.4 |

### Wave 3 — Recurrence parity (blocks the recurrence half of the lane)

| #   | Item | Repo | Size | Depends on |
|-----|------|------|------|------------|
| 3.1 | **Recurrence run-tier timing into `stats.json`.** `stats_summary.py:246-253` emits no duration field. The driver already receives train/crossval payloads; surface a duration and a work-count candidate (`n_epochs`, plus fold count for crossval) in the recurrence stats block, and **measure across repeats whether the work count is invariant** — early stopping may make it vary, which would mean recurrence has no work-gate analogue at all. | juniper-ml | M | 0.1 |
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
