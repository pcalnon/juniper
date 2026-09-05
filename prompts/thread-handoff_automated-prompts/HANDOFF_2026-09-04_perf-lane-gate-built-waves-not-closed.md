# HANDOFF 2026-09-05 — the gate is BUILT, its premise SETTLED, and all six comparator defects CLOSED

Successor to `HANDOFF_2026-09-01_perf-lane-p3-and-arc-tail.md`.

> **READ THIS FIRST — DO NOT RUN BRANCH CLEANUP ON A LIST FROM THIS DOCUMENT.** Item **3.1**
> shipped as `juniper-ml#1683`, **merged `06e81d3a`** shortly after this was written; its content is
> verified present on `main`. But **several PRs in this lane remain open and peers are opening more
> as you read** — at last check #1691, #1696, #1698, #1704, #1707, with #1685/#1688/#1689 having
> merged in the interim. **The count is a moving target: run `gh pr list --state open` and
> `git branch --no-merged origin/main` yourself.** `fix/notes-doc-pf1-linting-and-responses`, which
> the predecessor flagged, is still unmerged.
>
> Note for anyone checking ancestry: `feat/recurrence-work-not-countable` (`a11b6203`) is **not** an
> ancestor of `origin/main` even though its work is merged — squash-merge creates a new commit.
> **A SHA's absence from `main` is not evidence its content is missing.** Verify by content.
>
> An earlier draft of this handoff asserted "every branch merged and deleted". That was false when
> written — #1683 was open — and was caught by consensus validation (§9 of this document). It is
> recorded because the same sentence would have destroyed item 3.1.

**Nothing is running**: no campaign, suite, monitor or background task survives this session. Verify
with a PROCESS check, not only ports:
`pgrep -c -x sha256sum` and
`ps -eo pid,cmd --no-headers | grep -E "run_suite|contention_load|headroom_sweep" | grep -v grep`.

`origin/main` was `d5969022` when this was finalised (`63ca9306` at first draft; it moved repeatedly
during validation and the determinism fix) — **re-check it, do not branch from a recorded sha.**

---

## GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. The gate is built and works; **no wave is formally
closed**, and the cheapest remaining work needs no host time at all.

**The gate, usable today** (all merged):

```bash
python3 util/experiments/make_baseline.py    --tag <tag> --suite <suite_dir>
python3 util/experiments/compare_baseline.py --baseline <tag> --suite <suite_dir>
python3 util/experiments/run_suite.py --suite <yaml> --compare-baseline <tag>
```

Two baselines are on disk; the usable one is **`pf1-2026-09-04b`**, at
`~/.local/state/juniper-experiments/baselines/pf1-2026-09-04b` — **outside the repo, untracked by
git**. (The earlier `pf1-2026-09-04` predates the termination-branch guard and is now correctly
refused; that is the guard working, not a fault.) If that state directory is cleaned, verification command 3 below fails for that reason and
not because anything drifted.

**Immediate next actions, cheapest first. All item numbers refer to
[`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
unless stated otherwise.**

0. ~~Land `ml#1735`, then the comparator defects.~~ **DONE 2026-09-05.** `ml#1741` `d8c0fc81`
   closed the two fail-open holes; `ml#1743` `d5969022` closed all six comparator defects
   (A1/A2/A3/A4/A6/A7). `ml#1735` (Cursor fleet) was **superseded, not landed** — it branched from
   `fix/step-count-determinism-guard`, and once `ml#1733` squash-merged and that branch was deleted
   GitHub retargeted it to `main`, where it conflicts (`update-branch` → 422). Close it or let the
   fleet rebase it into a no-op. The determinism blocker
   is **settled and merged** (`ml#1733`), but `compare_baseline.py` still PASSes on unmeasured
   cells (A1) and on `timed_out` cells (A2) — both one-line imports of refusals
   `make_baseline.py` already implements — PASSes on zero-work runs (A4), converts a real FAIL
   into a REFUSE when any unreadable suite is on the command line (A3), and mishandles partial
   scenario coverage (A6) and duplicate fingerprints (A7). **A3 must be settled before any CI
   wiring**, since a caller treating exit 2 as "cannot compare" would lose a real regression.
1. **Free — land the remaining open lane PRs** (peer-authored; enumerate them yourself, the set
   moves). Item 3.1 is already in via #1683 `06e81d3a`, so `main` can read a recurrence run and the
   three gate suites run **88 tests**.
2. **Free — P4 (Documentation) is a whole PHASE that is missing and never started.** §1.1 of the
   phasing note
   ([`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`](../../notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md))
   defines it as the operator surface in `docs/REFERENCE.md` + the cheatsheet + the baseline
   directory documented as a first-class artifact location, and it is **the last gate before §12
   development may begin**. `docs/REFERENCE.md` and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`
   mention none of `make_baseline` / `compare_baseline` / `read_run_metrics` / `baselines/`
   (the only "Q-8"-looking hits are `OQ-8`, an unrelated design question). PRs #1691/#1696/#1678/#1680
   are peer P4 work already in flight — coordinate, do not duplicate.
3. **Free — two owner decisions.** **2.5**: PF-4's comparison semantics, given a stored baseline is
   by construction a different run and inherits the drift floor. **0.5**: `xor-staged.yaml`'s
   undocumented `max_epochs: 200` / no `output_epochs`, parked in
   `PENDING_EPOCH_SPLIT_DECISIONS` in `tests/test_experiment_config_schemas.py` — deliberately not
   blessed. Also still open and named in §5 of the P2 plan and §6 of the P1 design
   ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](../../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)):
   **whether the run tier ever gates CI.** Item 1.4 deliberately leaves `run_suite`'s exit code
   untouched by a verdict *pending that decision* — a test is named for it.
4. **Free — item 0.1 is the reason Wave 0 is not closed**: the P2 plan's own §6 acceptance still
   reads `- [ ] **Reviewed — owner**`.
5. **~S, host time — item 3.3**, the cheapest measurement left and unblocked by 3.1: launch a
   recurrence run with `--grafana-bridge` and confirm timings appear under
   `environment="host-experiment"`. Zero recurrence series have ever been observed there.
6. **Host time — item 2.1 (PF-2), but RE-CALIBRATE IT FIRST.** `perf/pf2-cascor-dataset-scaling.yaml`
   sets **no epoch and no budget override**, so post-`cascor#618` it runs `spiral-smoke.yaml` at its
   native `(2, 2)` / 50 epochs — the configuration §2.1 of the P2 plan measured at **15.09 s /
   32 steps, below the ~40 s scrapeability floor**. PF-1 needed exactly this fix (item 0.3); PF-2
   has never had it. It also declares only `per_run_timeout_seconds`, **not**
   `outputs.max_wall_seconds` — and §4 of the P2 plan is explicit that the driver budget, not the
   suite timeout, ends a run. Re-survey with `util/ad-hoc/2026-08-20_wall_ordering_survey.py`.
   *A timeout is not a measurement.*
7. **Item 2.2 (PF-3) is sized M (≈ a day) by the P2 plan, not an afternoon** — a 4×3 matrix at
   `max_wall_seconds: 2000`, worst case ~6.7 h, and its own comment names the
   `num_processes: 1` / `pool: 16` leg as the slowest cell. Needs **explicit host-time approval and
   a quiet window**.
8. **Wave 4 (PF-8) exists and is unblocked.** Do **4.3 before 4.1**: re-scope PF-8 against the
   headroom sweep first, because §8.4 of the instrument-resolution results
   ([`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md))
   already answers "is contention real". 4.1 must not reuse the sweep driver's naive teardown, and
   cascor `parallel > 1` is still refused from one checkout (`util/experiments/run_suite.py:18-20`).

---

## 2. Key context the successor must not re-derive

- **`timings.drive` is DE-RATIFIED.** It is quantized to the driver's status-poll interval
  (`util/experiments/run_experiment.py`, `DEFAULT_POLL_INTERVAL = 5.0`; the drive loop breaks only
  on a poll). Independently re-derived over 331 runs: `drive = (polls−1)×poll_interval + ~18 ms per
  poll`, residual **strictly positive** in every run (median 0.243 s, max 25.5 s on the longest).
  `poll_interval` is a parameter — one run used 2.0.
- **The 25×–182× understatement is a COEFFICIENT-OF-VARIATION ratio, and it is specific to 20 s
  cells.** Raw sd ratio is 18.75–151.58×. At ≥60 s it **collapses to 0.86–1.25×**, where `drive` sd
  can *exceed* `step_sum` sd. Do not restate it as a general property of `drive`.
- ~~**The quiet-run drift floor is 15.0–20.5%**~~ — **REFUTED 2026-09-05; the original 13–20.5% was
  correct and stands.** This bullet claimed the band mixed normalizations, "the 13% is
  `(max−min)/max` on the 20 s runs, the 20.5% is `max/min−1` on the sweep's quiet blocks". Recomputed
  from the six values in §5 / §8.4 of
  [`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md):
  the two quiet 20 s runs (18.42 → 20.81 ms) give **12.98%** under `max/min − 1` and **11.48%** under
  `(max−min)/max`, so the 13.0% figure is *already* `max/min − 1` — the same formula as the 20.5%.
  The band was never mixed. Worse, **15.0% is the `modest load 4/16` run** (18.42 → 21.18 ms), a
  LOADED measurement; promoting it to the lower bound of a *quiet* floor folds a load effect into the
  noise band and makes §8.4's central claim circular (6 workers at +19.9% sitting *inside* a 20.5%
  quiet band only means something while that band holds no loaded runs). **Do not "correct" the
  13–20.5% string in source, tests or docs** — it is right in all 9 sites. Normalization is now
  pinned in the sweep note itself so this cannot be re-derived.
- **THE WORK GATE'S PREMISE IS SETTLED (2026-09-04, `ml#1733` `a0420375`) — it was UNDER-specified, not wrong.**
  `step_count` was claimed deterministic and contention-immune. Consensus validation produced a
  counterexample from the existing corpus, which I then reproduced directly. Cell `c006-9c53874e`,
  **identical `config_sha256` `ab06aca2…`, identical seeds, same host, all `outcome: succeeded`**:

  | run | completion_reason | step_count |
  |---|---|---|
  | `20260814T024131Z-2aab` | `early_stopped` | **6496** |
  | `20260823T205835Z-a794` | `below_threshold` | **6095** |
  | `20260826T075813Z-4a15` | `early_stopped` | **6496** |

  Blessing the first and comparing the second yields **FAIL, exit 1** — a false regression. Lane B1
  reports **29 of the **79 repeated** configs (153 distinct overall)** in the corpus show divergent `step_count`; the mechanism is
  wall-clock-sensitive termination (the stopping *branch* moves, and `max_wall_seconds` can truncate
  the histogram).

  **My stated mechanism for the invariance was also wrong.** §2.1 of the P2 plan says invariance
  "follows from the iteration cap, not the epoch budget". It does not: **every** PF-1 run, at both
  20 s and 65 s, terminates `early_stopped` — none is cap-bound. So the 21-cell invariance is a real
  empirical regularity with a **misattributed cause**, and the baseline `pf1-2026-09-04` is cut from
  an early-stopping workload, i.e. the same class as the counterexample.

  **Settled by census over the whole corpus** (`util/ad-hoc/2026-09-04_step_count_determinism_census.py`):
  333 runs, 153 distinct configs, 79 repeated, **29 divergent in `step_count` — and all 29 fully
  explained by `completion_reason`, with ZERO still divergent within a branch.** So `step_count` is
  exact and deterministic *given how training ended*; the original claim simply omitted that
  condition.

  **`ml#1733` makes the branch part of the precondition**, so a flip REFUSES (exit 2) instead of
  FAILing (exit 1). Use **`pf1-2026-09-04b`**; `pf1-2026-09-04` predates the guard and is correctly
  refused.

  **`ml#1733` SHIPPED TWO FAIL-OPEN HOLES — both CLOSED in `ml#1741` (`d8c0fc81`).** Recorded because
  the shapes recur, and because both were found by validating the FIX rather than re-validating the
  original claim:

  1. **The truncated-termination guard CANNOT FIRE on real data.** It matches
     `{timed_out, torn_down_early, stalled}` against **`completion_reason`** — but those are
     **`outcome`** values. Across 370 manifests, `completion_reason` is only
     `{early_stopped 254, None 46, no_candidate 35, below_threshold 21, max_iterations 14}`; all 15
     driver-stopped runs carry `completion_reason=None`. My test passed **only because the fixture
     stuffed the string into the wrong field** — a vacuous pass, of exactly the class §5 of this
     document catalogues.
  2. **The candidate side fails OPEN on a mixed set.** `read_run_metrics` builds the reason set as
     `{... for r in rows if r.get("completion_reason")}`, dropping null-reason cells *before*
     uniqueness. So `4× early_stopped + 1× None` reads as a single branch and is compared. Only an
     all-null candidate refuses. The baseline side is unconditional and does fail closed; the doc's
     earlier "fails closed on both sides" was wrong.

  **The gate is now safe to CI-wire on its own merits** — but whether the run tier gates at all
  remains an open OWNER decision (§6 of the P1 design), and `run_suite`'s exit code is still
  deliberately independent of the verdict.

  **One caveat on the census itself**: the 29 divergent configs partition into 74 branches, **54 of
  them singletons**, where within-branch agreement is definitionally guaranteed. Only **20 branches
  have n≥2** and genuinely corroborate. The finding holds — no counterexample exists — but it rests
  on 20 real comparisons, not 29.

- **The gate is SPLIT.** WORK = `step_count`, compared **exactly**. SPEED = mean step duration,
  reported and **structurally ungated** — there is deliberately no threshold field to set later.
- **Identity is checked BEFORE work.** `registry.jsonl`'s `config_sha256` cannot be the workload
  identity: it hashes `experiment.description`, so PF-1's five repeats have five different values.
  `read_run_metrics.workload_fingerprint()` strips cosmetic keys but **not** `seed`. Independently
  confirmed: 3 distinct fingerprints across 35 PF-1 cells, partitioning exactly on real workload.
- **Recurrence work is NOT countable** (item 3.1). `n_epochs` takes two values across 36 runs — 1
  (28) and 200 (2) — by readout type, invariant to `d` and `n_steps`. `n_windows` is input size.
  PF-5/6/7 are **report-only forever** absent new instrumentation in juniper-recurrence.
- **Pre- and post-2026-09-02 figures are not comparable.** `cascor#618` gave `spiral-smoke.yaml`
  both epoch keys; PF-1 was re-calibrated to `max_epochs = output_epochs = 4000` (65.3 s median).
  Any baseline must be cut from post-fix runs only.
- **`aggregate.csv` now carries `step_count` and `mean_step_seconds`** alongside the de-ratified
  `wall_seconds`, and `REPORT.md` has a "Gate inputs" section (item 1.4). It is no longer a trap —
  but `wall_seconds` alone still is.

---

## 3. Verification commands

```bash
git fetch origin && git rev-parse --short origin/main
gh pr list --state open --limit 20          # enumerate; the count moves as peers ship
python3 -m unittest -q tests/test_read_run_metrics.py tests/test_make_baseline.py tests/test_compare_baseline.py
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-04b \
  --suite ~/.local/state/juniper-experiments/suites/pf1-cascor-spiral-repeats-20260903T040803Z
```

| command | expected |
|---|---|
| `rev-parse origin/main` | `63ca9306` **or later** |
| `gh pr list` | several open lane PRs, peer-authored; the set moves — enumerate, do not trust a count |
| three gate suites | **88 OK** (27 reader + 24 baseline + 37 comparator) after `ml#1743` |
| `compare_baseline` | `verdict: PASS`, `step_count baseline=1770.0 candidate=1770.0`, exit 0 |

**Stop conditions.** If the comparator does not say PASS on the suite its own baseline was cut from,
either the baseline or the reader has drifted — do not proceed. The count moves with every landed
PR in this lane — treat a mismatch as a prompt to enumerate, not as a fault.

---

## 4. Retained state — DO NOT DELETE (carried forward from the predecessor; verified still present)

- **Cascor pin worktree** `worktrees/juniper-cascor--exp--e-c-cap64--20260828-1922--67d7ea35`
  (detached at `67d7ea3`), with `~/.local/state/juniper-experiments/shadow-ec-cap64/juniper-cascor`
  symlinked to it. **The symlink is load-bearing and fails silently** — a dangling one makes
  `_resolve_base_config` fall back to the primary's config, producing pinned code against primary
  config with nothing in the manifest revealing it.
- **`util/remove_stale_worktrees.bash` has NO staleness predicate.** Run from juniper-ml it
  enumerates every `.claude/worktrees/*` session checkout, and there are 10+ live. Do not run it
  unguarded.
- PF-1 run artifacts and `headroom-sweep-*` / `pf1-epoch-calibration-*` /
  `output-epochs-impact-*` suites under `~/.local/state/juniper-experiments/`.

---

## 5. Traps this session paid for

- **A stable number can be a saturated instrument.** The tell: `drive` was ~100× quieter than its
  own siblings (`plots` 8.40%, `start` 3.63%) on the same host.
- **`ECOSYSTEM_ROOT = REPO_ROOT.parent` breaks from a session worktree** — juniper-ml keeps
  worktrees *inside* itself, so every cross-repo drift test skipped with a plausible "sibling conf
  dir not on disk" while checking nothing.
- **Never assert a flag's absence by grepping source.** A test did
  `assertNotIn("--force", getsource(mb))` and failed on the docstring saying there is no `--force`.
- **Never `except ImportError: return <empty>` for a sibling module.** It shipped item 1.4 silently
  doing nothing — blank columns plus "work invariant: BROKEN".
- **`auto-merge net disarmed` does not reliably mean a check failed.** Twice it meant an unresolved
  CodeQL thread: `mergeable_state=blocked` with all required contexts green. Neither `gh pr checks`
  nor `wait_for_checks` sees review threads — query `reviewThreads` via GraphQL.
- **`$?` after a pipe reports the pipe's last command**, not the tool's.
- **`gh pr view`'s `mergeable=UNKNOWN` is lazily computed** — `gh api repos/.../pulls/N` forces the
  real `mergeable_state`.
- **`util/` is not pre-commit-lint-gated** (hooks are scoped to `scripts/` and `tests/`), so
  `util/` work draws a vacuous "(no files to check) Skipped". Run `flake8` and `bandit` directly.
- **The juniper-ml CI test list is hand-maintained** — a new suite is not gated merely by existing.
- **`include` cells do NOT inherit `matrix`**; a suite with `include` and no `matrix` also emits a
  bare base-config cell (a deliberate, documented idiom in the p4 suites, not a defect).
- **juniper-ml formats with black; juniper-recurrence with ruff. `flake8` checks neither.**
- **`git -C` reaches sibling repos but NOT juniper-ml's own shared checkout** from a worktree
  session — relevant to items 0.5 / 2.4 / 2.5, all juniper-cascor.

---

## 6. CLI-experimentation arc tail — STILL OPEN, carried rather than dropped

The predecessor carried these and an earlier draft of this handoff dropped every one. From §0/§0.1/§4
of the tail re-probe
([`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md`](../../notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md)):

- **The title-repair ACCEPTANCE GATE — work-destroying if dropped.** §5 of that document records
  that **163 of 172 broken titles were produced BY a repair pass**. Any further repair must be gated
  on `util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py --check`, which **still exits 1
  with 91 artifacts remaining** (84 truncated, 41 unbalanced-bold, 8 field-label, 1 blockquote).
  Owner must choose the extraction rule.
- **`JR-ML-OBS-003`** survives as its own item — a different class from the 172.
- **R-1's second clause** — cascor must not report `succeeded` when zero candidates were installable
  due to allocation failures. Owner: cascor.
- **F-P4-7** (why the noise-free spiral is harder), **E-C's 0.10/0.20 rows at cap 128**,
  **W-12/Q-7** (csv_import corpus), **F-P1-2** (Grafana render), **G-16's refusal half now
  untestable in `JuniperData`**.
- **The owner's standing rider on the withdrawn 0.5% threshold** — *"come back and verify after this
  gate goes live"* (§7 of the loaded-and-bridged results) — is neither honoured nor retired. Speed
  is now structurally ungated, so it is arguably moot; decide and record which.

**Cross-repo, still true**: juniper-recurrence pins `juniper-data>=0.9.0,<0.12.0` (0.12.0 shipped
2026-08-31); `JuniperCascor1` has `juniper-service-core` 0.5.0, below recurrence's `>=0.6.0` floor,
so `tests/test_app_smoke.py::test_docs_require_auth_when_enabled` fails locally and passes in CI.

---

## 7. Shipped this session

**juniper-ml** — #1570 `abf15824`, #1578 `ee48ec44`, #1587 `aa0a8653`, #1592 `24aef672`,
#1600 `03d2bf12`, #1601 `8ff925db`, #1605 `fbe82c04`, #1613 `24e448e3`, #1622 `3116147e`,
#1643 `255603ef`, #1683 `06e81d3a`, #1710 `6d9725ef`, #1733 `a0420375`, #1739 `52f83db3`, #1741 `d8c0fc81`, #1743 `d5969022`. **juniper-cascor** — #618 `2dec835`. **Open at hand-off**: `ml#1735` (fixes #1733's two holes) plus a large and moving set of peer PRs — enumerate with `gh pr list`, do not trust a count.

**Files created**: `util/experiments/read_run_metrics.py`, `make_baseline.py`, `compare_baseline.py`;
`tests/test_read_run_metrics.py`, `tests/test_make_baseline.py`, `tests/test_compare_baseline.py`;
`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`,
`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`; several `util/ad-hoc/2026-09-0*`
instruments.
**Files modified**: `util/experiments/run_suite.py`, `run_experiment.py`;
`tests/test_experiment_config_schemas.py`, `tests/test_run_suite.py`; `.github/workflows/ci.yml`;
`util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml`;
`juniper-cascor/conf/experiments/spiral-smoke.yaml`; the three 2026-08-31/09-01 PF-1 results notes
(correction banners); `notes/JUNIPER_2026-08-16_…PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`.

---

## 8. What this handoff does NOT cover

Deliberate, so a dropped item stays distinguishable from an out-of-scope one: the backup/Duplicati
arc, the canopy E2E arc, the defect register, P5 fleet rollout, the soak arc, and
juniper-service-core work all have other owners and moved independently.

---

## 9. Consensus validation of this document

Validated under
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
— two Lane A agents re-deriving from raw artifacts with independent entry points (forbidden from
using `read_run_metrics.py` or the session's own ad-hoc scripts), two Lane B agents briefed to
refute.

**The first draft was substantially wrong and is not what you are reading.** It claimed "every
branch merged and deleted" (false — would have destroyed #1683), "Waves 0, 1 and 3 are CLOSED"
(four open items, one of which the draft itself listed as open nine lines later), omitted phase P4
and Wave 4 entirely, dropped the whole arc tail and retained-state section, and never named the P2
plan its nine item references pointed at.

~~**Refuted numerically**: the “13–20.5%” drift band, a mixed-normalization artifact — corrected to
**15.0–20.5%** above.~~ — **this consensus finding was itself WRONG and is withdrawn (2026-09-05);
see the struck bullet in §2.** Both endpoints are `max/min − 1` over quiet runs; 15.0% is the
`modest load 4/16` measurement. A consensus lane can agree on a wrong recomputation — the arithmetic
was never re-run against the six source values, only the *claim* about which formula produced them.
**Qualified**: the 25×–182× figure is a CV ratio specific to 20 s cells.

**Refuted structurally — the most consequential result.** Lane B1 broke the gate's core premise
(§2 of this document) and found six ways `compare_baseline.py` reaches a wrong verdict. **C2 is now
settled and fixed (`ml#1733`); the other five remain OPEN** and are the first code work a successor
should do:

| # | defect | why it matters |
|---|---|---|
| ~~C2~~ | ~~`step_count` not deterministic~~ — **SETTLED and FIXED in `ml#1733`**: all 29 divergences are explained by `completion_reason`, which is now part of the precondition | was producing **false FAILs**; now REFUSES |
| **A1** | `compare_baseline` does not refuse runs with **missing** step data; `make_baseline` does | 4 of 5 cells unmeasured still PASSes |
| **A2** | `compare_baseline` never reads `outcome`; `make_baseline` refuses non-`succeeded` | every cell `timed_out` still PASSes |
| **A3** | `if reasons: verdict = REFUSED` is evaluated **before** the work-mismatch branch | adding one unreadable suite converts a true **FAIL(1)** into **REFUSED(2)** — settle before any CI wiring |
| **A4** | `bool(counts)` is True for `[0.0, 0.0, 0.0]` | a do-nothing run baselines and passes |
| **A6/A7** | scenario coverage unchecked; duplicate fingerprints collapse in a dict comprehension | partial comparisons PASS; duplicate-workload baselines produce a **false FAIL** |

A1/A2 are one-line asymmetries — `compare_baseline` should adopt the refusals `make_baseline`
already has.

**C4, documentation over-reach**: "`drive` cannot serve as an upper bound on noise" is stated
unconditionally in `util/experiments/read_run_metrics.py` and is **false above ~60 s**, where the
`step_sum`/`drive` sd ratio is 0.86–1.25 across five suites out to 225.8 s. The quantization is
**additive** (~4.3 s residual, near-constant), so its relative cost falls from 33% below 30 s to
0.4% above 700 s. E-A/E-C cells at 120–670 s are in the faithful regime. No capability was lost —
`drive` is still recorded — but the wording should be duration-conditional.

**C3, recurrence uncountability: NOT refuted, but re-ground the reason.** The doc rejects `n_epochs`
for being invariant to `d`/`n_steps`; the stronger and correct reason is that
`juniper-recurrence-model/.../model.py:218` is `n_epochs = max(1, getattr(self._readout,
"n_epochs_", 1))`, and a closed-form readout never sets `n_epochs_` — so for 28/30 runs it is a
**literal constant**, not a low-resolution measurement. One carve-out: `_readout_mlp.py:145-161`
*does* maintain a genuine counter, so "recurrence exposes no work-done counter" is too absolute.

Lane A reproduced, independently and exactly: `step_count` 1770 across five cells; drive median
65.272 s; five distinct `config_sha256`; the stripped-hash workload identity; `n_epochs` 28×1 / 2×200
/ 6 missing; the epoch calibration at 500/2000/5000. Instrument retained as provenance:
`util/ad-hoc/2026-09-04_laneA1_independent_verify.py`.

**One caveat on the calibration**: the 50-epoch anchor is a cross-suite n=2 mean with 26% internal
spread (11.886 and 9.139), and the 500/2000/5000 points are n=1 each. The 4000 choice is sound but
rests on a thinner base than four clean points would suggest.
