# Performance lane — P1 Design of record

> **Operator surface (2026-09-05).** Q-8 writer + split comparator are on main. `step_count` is exact **within a termination branch** ([juniper-ml#1733](https://github.com/pcalnon/juniper-ml/pull/1733); census closed the #1710 counterexample). A branch flip is REFUSE, not FAIL. Do not wire `compare_baseline.py` to CI — unmeasured-drop / fingerprint-collapse remain. Operator contract: [`docs/REFERENCE.md` § Perf-Lane Work Gate](../docs/REFERENCE.md#perf-lane-work-gate).

**Closes**: phase **P1** of the four-phase gate in
[`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md` §1.1](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md).
That table's P1 deliverable: *"Design-of-record note: what is measured, on which tier, against which
baseline, at what budget, and what regression means. Must resolve §12.3 scenario matrix, draft →
fixed, and specify Q-8 baseline directory (name, layout, retention, who writes it)."*

**Does not close**: P2 (work items), P3 (**threshold ratification** — owner), P4 (docs). §12 development
remains gated. This document is the specification P2 plans against, not permission to build.

**Plan §12** = [`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md)
§12, which opens by calling itself *"a design start, not a final design."*

---

## 1. The finding that changes the scenario matrix

**`baseline_20260526.json` contains no timing data.** Plan §12.1 reuses it as *"the persisted-baseline
mechanism and its regression tolerances stay authoritative for micro-level work"*, and PF-4 is
specified as *"existing perf suite vs `baseline_20260526.json` → per-op timings; regression %"*.

Measured 2026-08-31:

```text
entries                          : 10
entries with any timing-ish key  : 0
entries with memory keys         : 6
```

The timing entries carry only their parameters — `forward_5_hidden` records
`results: {"hidden_units": 5}` and nothing else. Correspondingly `test_baselines.py` defines
`MEMORY_DELTA_THRESHOLD_MB`, `MEMORY_ABSOLUTE_THRESHOLD_MB` and
`MEMORY_REGRESSION_TOLERANCE_PCT` — and **no timing tolerance of any kind**.

So the micro tier today detects **memory** regressions and nothing else. §12.1's reuse claim is
true for memory and false for timing, and **PF-4 cannot be evaluated as written**.

This is a design input, not a defect report: it means PF-4's first work item is *establishing* a
timing baseline, not *comparing against* one. Recorded rather than patched, because the same
sentence would otherwise be inherited by P2 as though the instrument were ready.

---

## 2. Tiers — what is measured, and what regression means at each

| tier | instrument | baseline | regression means | gate? |
|---|---|---|---|---|
| **Micro** | cascor `src/tests/performance/` (10 modules), `--run-performance` + `CASCOR_BENCHMARK_MODE=1` | `baselines/baseline_20260526.json` | **memory**: RSS over baseline by >50%, or absolute >2000 MB. **timing**: undefined — no baseline data exists (§1) | memory yes (already); timing no |
| **Run** | `util/experiments/run_suite.py` + the PF suites | a *set of run manifests* under a named tag, in the Q-8 directory (§4) | a statistically meaningful slowdown of the **same YAML, same hardware, same thread budget** | **no** — report-only until variance is characterised (§5) |
| **Cross-app** | the `juniper-experiments` Grafana dashboard | none | not a regression surface; a comparison surface | never |

**The run tier never compares across differing `runtime:` blocks.** That is why H-11 records the
thread budget in every manifest: two runs with different budgets are different workloads, and
comparing them produces a number that looks like a regression and is not one.

---

## 3. Scenario matrix — draft → fixed

Plan §12.3's draft is adopted with three changes, all forced by what exists on disk.

| ID | scenario | suite | status |
|---|---|---|---|
| **PF-1** | cascor spiral, fixed budget, 5 repeats | `util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml` | **FIXED — and promoted to prerequisite** (§5) |
| **PF-2** | cascor dataset-size scaling | `perf/pf2-cascor-dataset-scaling.yaml` | FIXED |
| **PF-3** | cascor candidate-pool × process scaling | `perf/pf3-cascor-pool-scaling.yaml` | FIXED |
| **PF-4** | cascor micro-benchmarks | *(no suite — reuses cascor's pytest layer)* | **RESCOPED**: establish a timing baseline first; comparison is a later item (§1) |
| **PF-5** | recurrence `d`-scaling | `perf/pf5-recurrence-d-scaling.yaml` | FIXED |
| **PF-6** | recurrence dataset-size scaling | `perf/pf6-recurrence-nsteps-scaling.yaml` | FIXED |
| **PF-7** | recurrence readout-rung cost | `perf/pf7-recurrence-readout-rungs.yaml` | FIXED |
| **PF-8** | two-run concurrency cost | **none exists** | **DEFERRED to P2** — needs a concurrent-launch harness `run_suite` does not have; `execution.mode: parallel` runs cells of *one* suite, not two suites at once |

**None of PF-1…PF-7 has ever been executed** — `~/.local/state/juniper-experiments/suites/` contains
no `pf*` run directory as of 2026-08-31. Every number in this lane is therefore prospective. The
suites are instruments; PF-1's own header says so: *"this file is the instrument, not the verdict."*

### 3.1 The budget trap, and why these suites are clear of it

The phasing note's §1.3 trap: the driver's `outputs.max_wall_seconds` — **not** the suite's
`per_run_timeout_seconds` — is what ends a run, and `run_suite` never passes `--max-wall-seconds`,
so an unoverridden cell silently inherits its base config's budget. *A timeout is not a
measurement.*

Verified for every PF suite via `util/ad-hoc/2026-08-20_wall_ordering_survey.py`:

```text
perf/pf1-cascor-spiral-repeats.yaml      cascor    1200    600  OK
perf/pf2-cascor-dataset-scaling.yaml     cascor    2400    600  OK
perf/pf3-cascor-pool-scaling.yaml        cascor    2400   2000  OK  (declares execution.max_wall_seconds)
perf/pf5-recurrence-d-scaling.yaml       recurrence 1800   900  OK
perf/pf6-recurrence-nsteps-scaling.yaml  recurrence 1800   900  OK
perf/pf7-recurrence-readout-rungs.yaml   recurrence 1800   900  OK
```

In every case the driver budget is the smaller number, so it binds first and the suite timeout
cannot mask it. PF-1 additionally runs `spiral-smoke.yaml` (`max_iterations: 2`,
`max_hidden_units: 2`) against a 600 s budget — orders of magnitude of headroom, so it measures the
workload rather than the ceiling.

**This ordering is a standing requirement, not a one-off check.** Any scenario added later must be
re-surveyed; the survey is the acceptance test for that property.

---

## 4. Q-8 — the run-level baseline directory

Q-8 was answered by the owner on 2026-08-16: **a dedicated, new directory**, with location, layout
and retention *"part of the §12 design phase, not an implementation detail to be improvised"*. That
is this section.

**Location**: `~/.local/state/juniper-experiments/baselines/` — a sibling of `suites/`, not a
subdirectory of it. Rationale: a baseline outlives the suite run that produced it, and nesting it
under `suites/<run-id>/` would tie its lifetime to a directory whose retention policy is about run
evidence. It stays outside the repo because these are host-specific measurements — a baseline taken
on this workstation is not meaningful on another machine, and committing it would invite exactly
the cross-hardware comparison §2 forbids.

**Layout**:

```text
baselines/
  <tag>/                       # operator-chosen, e.g. pf1-2026-08-31
    baseline.json              # the aggregate: per-scenario summary statistics
    manifests/<run_id>.json    # the constituent run manifests, copied verbatim
    HOST.json                  # hardware + thread budget + package versions at capture time
```

**`HOST.json` is load-bearing, not metadata.** The run tier's regression definition is "same YAML,
same hardware, same thread budget"; without a recorded host fingerprint the *first* condition a
comparison must check cannot be checked, and the comparison silently becomes cross-hardware. It
records at minimum: CPU model and count, total RAM, GPU presence, `torch`/`numpy` versions, and the
`runtime:` thread budget the manifests were produced under.

**Who writes it**: a `util/experiments/` tool, invoked explicitly by an operator — never a side
effect of a suite run. A baseline is a deliberate act of blessing a measurement; a run that
promotes itself to baseline can launder a bad number into the reference.

**Retention**: baselines are **never** auto-deleted. They are small (JSON only) and their value is
historical comparison. This mirrors the snapshot-retention decision already ratified for cascor.
Superseded tags stay on disk and are superseded *by name*, not by removal.

**Q-8 also gates `JR-CAS-OBS-004`** (§16 of the plan); that dependency is now unblocked by this
section.

---

## 5. Thresholds — how they will be derived, and why none is proposed here

**This document proposes no threshold numbers, and that is deliberate.** P3 ratifies thresholds;
P1's job is to specify how a defensible number is obtained. Inventing one here would hand P3 a
figure with no measurement behind it to ratify.

**The blocking prerequisite is host variance, and it is unmeasured.** Plan §12.4 already forbids a
CI gate *"until variance is characterised on this host (a shared workstation, not a quiesced
runner)"*. What exists today is a single contention datapoint, n=1: a budget-equivalent spiral cell
took **552.0 s** with a 13-hour `clamscan` running against **516.9 s** without — **+6.8%**. One
observation of one interference source is not a variance characterisation.

**PF-1 is therefore promoted from scenario to prerequisite.** Its five repeats of an unchanged
config measure exactly the quantity a threshold must exceed: run-to-run spread with no change under
test. The derivation rule this design fixes:

> A run-tier regression threshold is **at least 3× the observed standard deviation** of PF-1's
> repeat distribution for the same metric, and never smaller than the largest single contention
> excursion observed on this host. If that floor exceeds the effect size anyone cares about
> detecting, the correct conclusion is that **this host cannot gate that metric** — not that the
> threshold should be lowered to make it detectable.

That last clause is the one worth defending. A shared workstation has a noise floor; a threshold
below it produces alerts that are indistinguishable from someone opening a browser, which is how a
perf gate gets muted and then ignored.

**Sequence to P3**: run PF-1 (5 repeats, ~an hour, needs owner approval for the host time) →
compute the spread → derive candidate thresholds by the rule above → the owner ratifies or rejects
them → P3's second half, a dry measurement pass reproducing end-to-end, can then run.

---

## 6. What this design deliberately does not decide

- **Threshold values** — P3, and blocked on PF-1 as above.
- **Whether the run tier ever gates CI** — §12.4 says report-only "at first"; whether "first" ends
  is a separate owner decision, and §5's floor may answer it in the negative.
- **PF-8's harness** — deferred to P2 with its shape stated (§3).
- **Q-9, alert scoping** — plan §12.4 item 4 recommends excluding `environment="host-experiment"`
  from existing alert rules so a deliberately brutal benchmark does not page. That recommendation
  stands and is unchanged by this design; it is a `juniper-deploy` change, not a §12 one.
- **Optimization work** — plan §12.5 sequences it strictly after measurement, and nothing here
  advances it.

---

## 7. Acceptance for P1

The phasing table's P1 is *"done when: a `notes/` design doc exists and is reviewed."*

- [x] What is measured, on which tier, against which baseline, at what budget — §2, §3
- [x] What regression *means*, per tier — §2
- [x] §12.3 scenario matrix, draft → fixed — §3 (PF-4 rescoped, PF-8 deferred, rationale recorded)
- [x] Q-8 baseline directory: name, layout, retention, who writes it — §4
- [x] **Reviewed** — owner, in session 2026-09-01 ("design reviewed and approved"); the four P3 decisions that followed are recorded in §7 of the loaded-and-bridged results ([`JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-LOADED-AND-BRIDGED-RESULTS.md`](JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-LOADED-AND-BRIDGED-RESULTS.md))

Review is the remaining half. The two items most worth an owner's attention are **§1** (PF-4's
instrument does not hold timing data, so the reuse decision behind it is half-true) and **§5's
derivation rule**, which commits in advance to concluding "this host cannot gate that metric" if
the noise floor says so.
