# HANDOFF 2026-09-01 — perf-lane P3, and what remains of the CLI-experimentation arc tail

Successor to `HANDOFF_2026-08-29_cli-experimentation-tail-and-requirements-corpus.md`, whose §3
tail this session re-probed and largely closed. **Nothing is in flight**: no campaign, suite,
monitor or background task survives this session. `origin/main` was `2dcb9e91` when this was
written — **re-check it, do not branch from a recorded sha.**
>
> **Verify "nothing in flight" with a PROCESS check, not only ports.** The contention load generator
> binds no port, so `ss` cannot see it: run `pgrep -af "sha256sum|run_suite.py"` as well. (It
> self-bounds at `LOAD_DURATION` and traps `EXIT`/`INT`/`TERM`, so a leak dies within ~25 min at the
> settings below — but a surviving load would corrupt the first measurement taken.)

> **Document-naming convention (mandatory, ml#1555, merged 2026-09-01).** Every section reference
> below names its document. That rule is in `Juniper/AGENTS.md` § Cross-Project Conventions and
> applies to handoffs. Follow it in the successor session's summaries too.

---

## GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane at phase P3**, and finish the residual
CLI-experimentation arc tail.

**Immediate next action — an OWNER DECISION, not a measurement.** Decide the gate's **shape**
before its number, per §6 of the heavy-load results
(`notes/JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`), which states
that ordering explicitly. Adversarial validation of this handoff's first draft found that the draft
had inverted it — it made a settled-`heavy` run the blocking action, and that run **does not inform
any decision on the table**: the proposed design excludes contention *by precondition*, so its
magnitude never enters the threshold arithmetic, and +90% vs +165% are both 90×–165× any candidate
threshold. Both answer the only question that matters — *can contention reach the comparison?* — with
"no, a precondition is required".

**The measurements that WOULD change a decision**, in cost order:

1. **Free — ask the owner the minimum effect size worth detecting.** P1 §5
   (`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`) terminates in "if that floor
   exceeds the effect size anyone cares about detecting, conclude *this host cannot gate that
   metric*." That effect size is stated in **no** perf-lane document, so no candidate threshold can
   be evaluated against the ratified rule at all.
2. **~6 min each — 2–4 more QUIET 66 s five-repeat runs.** The proposed gate thresholds a *median
   across runs*, and between-run variability at 66 s is **unmeasured (n=1 run, zero degrees of
   freedom)**. This also moves effect (b)'s frequency estimate off 1/5.
3. **~6 min — a 45 s cell variant.** ~40 s is the shortest duration observed to scrape successfully,
   so cells near 45 s keep the step-duration histogram while roughly halving duration exposure — it
   attacks the effect that forced the loosening, and is proposed nowhere.
4. **A headroom sweep at 6 / 8 / 10 / 12 of 16 cores.** Shape #1 needs a headroom *floor*; the
   evidence has exactly two points (4/16 → +0.051%, 14/16 → +90–165%) and nothing between. A settled
   run at 14/16 adds no information about where the floor sits.

**A settled-`heavy` five-repeat run remains available** (~20 min, owner approval is per-arc — re-ask)
but is **not** blocking. If taken, launch the load and the suite **from the same shell**: the
generator traps `EXIT` and can reap its own workers if backgrounded separately. Wait for its
`[load] READY` line, and size the load from **loaded** cell durations (~190 s/cell), never quiet ones.

**On the withdrawn 0.5% candidate — the withdrawal stands, its stated reason did not.** "Derived at
20 s, fires at 66 s" conflates the *threshold* with the *statistic*: against the 66 s run it fires on
a single cell (+7.6%) and on the mean (+1.50%), but **not on the median** (65.233 vs ~65.23 =
+0.02%). §4 of the heavy-load results
(`notes/JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`) then adopts the
median as the fix — and 0.5% survives that fix with ~25× margin. So the number should be re-examined
alongside the shape, not treated as dead. The owner's own standing rider on it is recorded in §7 of
the loaded-and-bridged results
(`notes/JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-LOADED-AND-BRIDGED-RESULTS.md`): "come back and
verify after this gate goes live."

**P2 has never been produced, and it PRECEDES P3.** Tier 4 of the perf-lane phasing note
(`notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`) orders the
lane **F-P1 → F-P2 → F-P3 → F-P4**; P2's deliverable is a §14-style wave table of work items with
repo, size and dependencies, and no such artifact exists in `notes/`. The P3 measurements were taken
ahead of it at the owner's direction, which is a legitimate compression — but **this handoff's first
draft said "do not restart P2", which both inverted the phase order and implied P2 had been started.
It has not.** Raise it with the owner rather than sealing it shut.

Separately, **P1 is not formally accepted**: its acceptance checklist still has `- [ ] Reviewed —
owner` at `notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md:202`, though the owner
approved it in session on 2026-09-01. §12 development of the CLI-experimentation plan
(`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`)
stays gated regardless.

**Key context the successor must not re-derive:**

- **Three effects, separated on 2026-09-01** — intrinsic workload variance **0.02%**, duration
  exposure **+7.6%** (one cell in five at 66 s, zero in ten cells at 20 s), core contention
  **+90–165%**. Detail in §2 of the heavy-load results
  (`notes/JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md`).
- **The `modest` 4-of-16 profile measures the PERMITTED regime, not the worst case** — twelve cores
  stayed free, so the stack ran on effectively dedicated cores and cost +0.051%. That is a valid and
  load-bearing negative: it is the only evidence that a regime exists in which a tight gate is
  possible, which is what a host-state precondition would enforce. Pair it with `heavy`; do not
  discard it.
- **Metric is ratified: `timings.drive`**, not `wall_seconds`. The latter absorbs plot-rendering and
  stack bring-up; enabling the Grafana bridge alone moves it ~5%.
- **`metrics_scraped` was fixed** (ml#1550): `target_file_written` plus a **tri-state**
  `scrape_confirmed` (`None` = could not ask). Trust `scrape_confirmed`, never the old `present`.
- **~40 s is the shortest duration OBSERVED to scrape successfully** (one run, 40.17 s drive, 255
  series). Nothing shorter was tried, so this is not a demonstrated floor — no run at ≥40 s can
  contradict it. Treat it as a lower bound on what is known, not on what works.

**Verification commands to run first** (expected results in §2 of this document):

```bash
git fetch origin && git rev-parse --short origin/main
python3 -m unittest -q tests/test_run_suite.py tests/test_run_experiment.py
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  python3 util/experiments/run_suite.py --suite util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml --dry-run
ss -tlnpH | grep -E ":(811[0-9]|823[0-9]|826[0-9])" || echo "campaign ranges clear"
```

**Git state**: this worktree's HEAD is **`feat/pf1-longer-cells-and-load-profiles`** (ml#1551,
merged); tree clean. **Delete nothing on the strength of this document** — the first draft named the
wrong branch and attached "delete or reset" to it, and `fix/notes-doc-pf1-linting-and-responses` is
genuinely UNMERGED. Run `git branch --no-merged origin/main` and read it before removing anything. Merge approval was granted for this session and arc;
it is **session-scoped — re-ask**.

---

## 2. Expected verification results

| command | expected |
|---|---|
| `rev-parse origin/main` | `2dcb9e91` **or later** — later is normal, peers merge continuously |
| `test_run_suite.py` | 52 tests OK |
| `test_run_experiment.py` | **154** tests OK (148 pre-ml#1550, +6) |
| PF-1 `--dry-run` | **5 cells**, every one carrying `max_hidden_units: 10` and `max_iterations: 10` |
| port check | `campaign ranges clear` |

If PF-1's dry run shows fewer than 5 cells, or cells with differing overrides, **stop** — the repeats
are a matrix axis and `include` cells do not inherit the matrix. See §3 of this document.

---

## 3. Traps this session paid for

- **`timings.drive` — the RATIFIED metric — is NOT in `aggregate.csv`.** That file carries
  `wall_seconds` only. Pull `drive` from each run's `manifest.json` via `registry.jsonl`. A
  successor who trusts the aggregate will silently analyse the metric this lane explicitly
  de-ratified, and nothing will flag it.
- **`include` cells do NOT inherit `matrix`.** Putting a workload override in `matrix` while leaving
  repeats as `include` entries runs one cell at the override and the rest at the base — five cells
  that are not repeats of each other. PF-1's repeats are a matrix axis for this reason.
- **Prometheus instant queries only return series inside the lookback window.** Querying a finished
  run minutes later returns nothing. Query at the run's own timestamp. This nearly produced a
  published "the metric is still missing" claim that was false.
- **A synthetic load is not stationary.** Load average lags a minute and workers shift I/O→CPU as
  page cache warms. Wait for `[load] READY`.
- **Size a load from loaded durations, not quiet ones.**
- **juniper-ml formats with black; juniper-recurrence formats with ruff.** `flake8` checks neither.
  Run `pre-commit run --files <paths>` before pushing — a black failure cost a merge cycle here.
- **`safe_merge.py` exits 0 without merging.** Look for the `MERGED` line; "auto-merge net
  disarmed" means a required check failed.
- **The harness background-task lease (~1 h) kills long commands.** An armed auto-merge net still
  lands the merge; detached `setsid nohup` runs still complete. Verify state, do not re-run.
- **`git -C` reaches sibling repos but NOT juniper-ml's own shared checkout** from a worktree
  session. Use `util/open_signed_pr.py` for sibling-repo changes.

---

## 4. Remaining work, by area

### 4.1 Perf lane (the active thread)

| item | state |
|---|---|
| settled-`heavy` 5-repeat run | **OWED** — the immediate next action |
| gate shape + threshold | owner, §6 of `notes/JUNIPER_2026-09-01_JUNIPER-ECOSYSTEM_PF1-HEAVY-LOAD-AND-DURATION-RESULTS.md` |
| other duration classes (E-A/E-C, hundreds of seconds) | unmeasured; duration exposure is higher there by construction |
| **PF-4 cannot run as written** | `baseline_20260526.json` holds **10 entries, 0 with timing data**; its first task is *establishing* a baseline. §1 of the P1 design (`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`) |
| **PF-8 has no suite** | `run_suite`'s parallel mode runs cells of ONE suite, not two suites concurrently. Deferred to P2 |
| PF-2/3/5/6/7 | suites exist; **never executed** |
| P2 (work items), P4 (docs) | gated behind P3 |

### 4.2 CLI-experimentation arc tail

Everything below is from **§0, §0.1 and §4** of the tail re-probe
(`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md`). The first draft
of this handoff cited only §0.1 and §4, which structurally excluded every item living in §0 — the
last four bullets below were recovered by adversarial validation.

- **R-1's second clause** — cascor must not report `succeeded` when zero candidates were installable
  due to allocation failures. `BUG-CC-18` (cascor#138, 2026-04-24) covers both-paths-failed and
  empty-results, **not** a per-candidate allocation failure that still returns a result. Owner: cascor.
- **F-P4-7** — why the noise-free spiral is harder. No entry point; needs a hypothesis and a probe,
  not a re-run. §1 of the arc-tail handoff chain.
- **E-C's 0.10 / 0.20 rows at cap 128** — untested, minor.
- **W-12/Q-7** (csv_import corpus, parked), **F-P1-2** (Grafana render) — open, uncarried by any handoff.
- **G-16's refusal half is now UNTESTABLE in `JuniperData`** — installing HF `datasets` made every
  generator available, so nothing refuses. Exercising it now needs a deliberately withheld optional
  dependency: a test-fixture question, not a host-provisioning one.
- **91 requirement title artifacts** — owner must choose the extraction rule. 81 were repaired
  (ml#1511); the remaining 91 are truncated or field-label titles needing editorial judgement. §5 of
  the tail re-probe (`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md`).
- **The title-repair ACCEPTANCE GATE, which is work-destroying if dropped.** §5 of the tail re-probe
  (`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md`) records that
  **163 of the 172 broken titles were produced BY a repair pass**. Any further repair must be gated
  on the detector `util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py` (`--check` exits 1
  while artifacts remain), or the next pass banks the same result undetected.
- **`JR-ML-OBS-003` (Detail selection) survives as its own item** — §5 of the tail re-probe states it
  is a *different* class from the 172 title defects and is not counted among them.
- **G-17's second sub-item: recurrence timings have NEVER been observed in Grafana.** §0 of the tail
  re-probe records zero recurrence series under `environment="host-experiment"`. The panels and
  plumbing are correct; what is missing is a recurrence run launched with `--grafana-bridge` — and
  this session shipped the enabler (ml#1547) while dropping the consumer item.
- **The `max_epochs` / `output_epochs` caveat did not travel, and it now collides with PF-4.** §5 of
  the 60 s variance results
  (`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PF1-VARIANCE-RESULTS.md`) requires that
  `spiral-smoke.yaml` set **both** keys before any figure from it is quoted as a **baseline** rather
  than a spread. It still sets `max_epochs: 50` with no `output_epochs`, and PF-1 uses it as
  `base_config` — while §4.1 of this document makes "establish a timing baseline" PF-4's first task.
- **Q-9, alert scoping** — §6 of the P1 design
  (`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`) recommends excluding
  `environment="host-experiment"` from existing alert rules so a deliberately brutal benchmark does
  not page. A `juniper-deploy` change, now more pressing: this session added a 14-of-16-core load
  profile and turned the Grafana bridge on.
- **"Whether the run tier ever gates CI"** — §6 of the P1 design names it a separate owner decision
  that §5's floor may answer in the negative.

### 4.3 Cross-repo, found in passing

- **juniper-recurrence pins `juniper-data>=0.9.0,<0.12.0`**, so its bench will not pick up
  juniper-data **0.12.0** (published 2026-08-31). Nothing in the bench needs it; raise the cap
  deliberately rather than by surprise.
- **`JuniperCascor1` has `juniper-service-core` 0.5.0**, below juniper-recurrence's declared
  `>=0.6.0` floor. Consequence: `tests/test_app_smoke.py::test_docs_require_auth_when_enabled` fails
  locally and passes in CI. `pip install -U juniper-service-core` in that env realigns it.

---

## 5. Retained state (do not delete casually)

- **Cascor pin worktree** `worktrees/juniper-cascor--exp--e-c-cap64--20260828-1922--67d7ea35`
  (detached at `67d7ea3`), with `~/.local/state/juniper-experiments/shadow-ec-cap64/juniper-cascor`
  symlinked to it. The symlink is **load-bearing and fails silently** — a dangling one makes
  `_resolve_base_config` fall back to the primary's config, producing pinned code against primary
  config with nothing in the manifest revealing it.
- **`util/remove_stale_worktrees.bash` has NO staleness predicate.** Run from juniper-ml it
  enumerates every `.claude/worktrees/*` session checkout. Do not run it unguarded.
- PF-1 run artifacts under `~/.local/state/juniper-experiments/` — `pf1-60s-quiet`,
  `pf1-60s-heavy` (contaminated, load expired mid-run — its gradient is *evidence*, not waste),
  `pf1-60s-heavy-clean`, and the `suites/pf1-cascor-spiral-repeats-*` directories.

---

## 6. What this handoff does NOT cover

Absence is deliberate, so a dropped item stays distinguishable from an out-of-scope one: the
backup/Duplicati arc, the canopy E2E arc, the defect register, P5 fleet rollout, and juniper-service-core
round-29 work all have other owners and moved independently during this session.
