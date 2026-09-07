# Perf lane — item 3.3 discharged (G-17 recurrence bridge), and why 2.1 / 2.2 did not run

**Closes item 3.3** of
[`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
— *"launch a recurrence run with `--grafana-bridge` and confirm recurrence timings actually appear
under `environment="host-experiment"`"*. Owner granted host time for items 3.3, 2.1 and 2.2 on
2026-09-05.

**3.3 PASSES.** **2.1 and 2.2 are NOT run**, for a measured reason recorded in §4 — not a refusal,
a scheduling constraint the lane's own calibration table settles.

---

## 1. Item 3.3 — result

Run `20260905T200957Z-9d59`, experiment label `pf-g17-recurrence-bridge`, config
`juniper-recurrence/conf/experiments/irregular-sine-smoke.yaml`, driver exit **0**.

**Before the run**, `{environment="host-experiment"}` returned `{"status":"success","data":[]}` —
zero series, confirming the plan's premise that no bridged recurrence run had ever happened.

**After the run**, read back from Prometheus (`127.0.0.1:9090`), not from the service:

```text
juniper_recurrence_train_last_duration_seconds     = 0.07834455301053822
juniper_recurrence_crossval_last_duration_seconds  = 0.09607286495156586
  labels: environment="host-experiment"  service="juniper-recurrence"
          run_id="20260905T200957Z-9d59"  experiment="pf-g17-recurrence-bridge"
```

144 series across 34 metric names arrived under `service="juniper-recurrence"`, including
`juniper_recurrence_{train,crossval}_{last_duration_seconds,last_metric,runs_total}`. Both
file_sd targets (`juniper-data`, `juniper-recurrence`) reported `health: up`.

**The plumbing was correct as believed.** `render_target_file`
(`util/experiment_stack.bash:770-790`) writes `environment: "host-experiment"`, and
`SCRAPE_TARGETS` includes the recurrence port (`util/experiment_stack.bash:900`). Nothing needed
fixing; the item was unexecuted, not broken. Teardown was clean — target file removed, ports
8110/8260 released.

---

## 2. Trap: the targets directory resolves INSIDE the worktree, and fails silently

`experiment_stack.bash --help` from a session worktree prints:

```text
Targets  : /home/pcalnon/…/juniper-ml/.claude/worktrees/juniper-deploy/prometheus/targets
```

That path **does not exist**. Prometheus mounts the real one:

```text
/home/pcalnon/Development/python/Juniper/juniper-deploy/prometheus  ->  /etc/prometheus
```

`DEPLOY_DIR="${JUNIPER_EXP_DEPLOY_DIR:-${PROJECT_DIR}/juniper-deploy}"`
(`util/experiment_stack.bash:113`) derives from `PROJECT_DIR`, and juniper-ml keeps its session
worktrees *inside itself*, so `PROJECT_DIR` lands on `.claude/worktrees/`. This is the same
`ECOSYSTEM_ROOT = REPO_ROOT.parent` class already catalogued in the 2026-09-04 handoff's trap list.

**Why it matters here specifically: it fails silently and inverts the result.** The bridge would
write a target file into a directory Prometheus does not mount, every other step would succeed, and
the acceptance query would return zero series — reporting item 3.3 as FAILED when the plumbing is
fine. A wrong negative, produced by a green run.

**Fix used**: `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`. Verify before
launching — `--help` prints the resolved `Targets` line, and it must be under `juniper-deploy/`,
not under `.claude/worktrees/`.

The same trap makes `util/ad-hoc/2026-08-20_wall_ordering_survey.py` report **UNRESOLVED** for every
suite whose `base_config` is a sibling repo, PF-1 and PF-2 included. It fails visibly there (the
verdict column says `UNRESOLVED`, not `OK`), so it is a nuisance rather than a hazard — but the
survey cannot be used from a worktree without the override.

---

## 3. Trap: `/metrics` 307-redirects, so a naive scrape reads EMPTY

```text
$ curl -s http://127.0.0.1:8260/metrics | wc -l
0
$ curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}' http://127.0.0.1:8260/metrics
307 -> http://127.0.0.1:8260/metrics/
```

The metrics live at `/metrics/` **with a trailing slash**. Prometheus follows redirects by default,
so the scrape works and the series are complete — this is not a service defect and needs no fix.

It is an **operator** trap: `curl http://…/metrics | grep juniper_recurrence` returns nothing, which
reads exactly like "the service is not exporting the metric". Anyone hand-verifying a bridged run
will hit it. Use `curl -sL`.

---

## 4. Why 2.1 (PF-2) and 2.2 (PF-3) did not run

**The host was not quiet, and the lane's own sweep says by how much that matters.** Measured
2026-09-05 15:11Z, immediately before the decision:

```text
nproc            : 16
load average     : 14.75 (1m)  12.70 (5m)  10.27 (15m)     <- rising during the session
CPU              : 45.7 us  10.4 sy  1.1 ni  36.6 id  6.0 wa
swap             : 20997 MB of 20999 MB used                <- effectively exhausted
```

Against §8.4 of the instrument-resolution results
([`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md)):

| synthetic load | measured effect on mean step | verdict |
|---|---|---|
| 6 workers | +19.9% | inside the 20.5% quiet band |
| 8 workers | **+86.1%** | SEPARABLE |
| 12 workers | **+181.6%** | SEPARABLE |

A load average of ~14 on 16 cores sits **past the 12-worker point**, where the sweep measured
**+181.6%**. PF-2 varies dataset size and PF-3 varies pool × processes; at this contention the
dominant term in either result would be the ambient load, not the axis under test. Both suites
would have produced well-formed measurements of the wrong thing, and 2.2's own plan row asks for
*"an explicit host-time approval **and a quiet window**"* — the approval was given, the window was
not available.

6.0% iowait with swap exhausted is a second, independent disqualifier: the box is paging.

**These are deferred, not declined.** Both are one command away once the host is idle; §5 records
what 2.1 still needs first.

---

## 5. Item 2.1 (PF-2) — calibration state, established

`util/experiments/suites/perf/pf2-cascor-dataset-scaling.yaml` resolved against its base config:

| property | value | verdict |
|---|---|---|
| `execution.per_run_timeout_seconds` | 2400 (suite) | — |
| `outputs.max_wall_seconds` | 600 (inherited from `spiral-smoke.yaml`) | **driver budget binds first — ordering OK** |
| `max_epochs` / `output_epochs` | 50 / 50 (inherited) | **both set — no epoch-split hazard** |
| `max_iterations` / `max_hidden_units` | 2 / 2 — the NATIVE budget | **duration too short** |
| matrix | `n_points_per_spiral: [250, 500, 1000, 2000]` | — |

Two of the three concerns raised in the 2026-09-04 handoff's item 6 are **discharged**:

- *"declares only `per_run_timeout_seconds`, not `outputs.max_wall_seconds`"* — true of the suite
  file, but the base config supplies `max_wall_seconds: 600`, and 600 < 2400, so the driver budget
  binds first. The §4 ordering requirement of the P2 plan is **satisfied**. PF-1 sits in exactly the
  same position (1200 timeout / 600 budget).
- The epoch split is closed: `cascor#618` gave `spiral-smoke.yaml` both keys, and PF-2 inherits both.

**The remaining concern stands**: at the native `(2, 2)` / 50-epoch budget the workload measures
**15.09 s / 32 steps** (§2.1 of the P2 plan), short of the ~60 s cell length PF-1 was calibrated to.

**What is NOT settled, and is not guessable.** PF-1's calibration (item 0.3) reached 4000 epochs by
*probing* 500 / 2000 / 5000 and interpolating within the upper segment, because the log-log slope
changes (~0.32 below 2000, ~0.71 above) where early stopping stops binding. PF-2 is harder than PF-1
was: its cells deliberately differ in dataset size across a **10×** range, so a single epoch value
must put the *smallest* cell over the duration floor while keeping the *largest* inside
`max_wall_seconds: 600`. Whether one value satisfies both is an empirical question.

Picking that value needs a probe run — which needs the quiet window §4 describes. **No epoch
override is proposed here**, deliberately: writing a guessed number into the suite would look like
calibration and would not be.

---

## 6. What this closes and what it leaves

| item | state |
|---|---|
| **3.3** | **DONE** — evidence in §1; plumbing confirmed correct, not fixed |
| **2.1** | Calibration state established (§5); 2 of 3 concerns discharged; probe + run pending a quiet host |
| **2.2** | Pending a quiet host (§4); no work needed beforehand |

Nothing in this document changes the gate, the comparator, or any suite file.
