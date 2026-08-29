# HANDOFF 2026-08-29 — E-C closed, the requirements corpus made self-consistent; the arc's unowned tail

Successor to
[`HANDOFF_2026-08-26_t6-rebaseline-complete.md`](HANDOFF_2026-08-26_t6-rebaseline-complete.md), and
through it to [`HANDOFF_2026-08-24_t6-rebaseline-campaign.md`](HANDOFF_2026-08-24_t6-rebaseline-campaign.md),
which **remains canonical** for T6's rationale, its §0 decision record (L-2 in particular: do *not*
"fix" the `max_epochs` warning by forwarding it into `grow_network` — it is golden-suite-visible),
its trap catalogue, and its §4 merge-trap rules (`util/safe_merge.py` mandatory; waiver trailer must
reach the squash commit). Those are not superseded by this document.

The 08-26 handoff left **two owner items plus an unowned tail**. Both owner items shipped, three
tail items with them. This records what closed, the one question this session *opened*, the traps it
added, and what is still unowned.

**Nothing is in flight.** No campaign, stack, or monitor survives this session.

> **This document was adversarially validated** by three independent agents (factual re-probe,
> amputation hunt, actionability attack) before archiving. Their findings are folded in; §3 and §6
> exist because the amputation pass proved a plain "remaining work" list loses items at every hop.

---

## 0. What closed (10 PRs, all merged, all verified on `main`)

| item | PR |
|---|---|
| **T6 owner item 2** — a `stalled`/`timed_out` cell is stopped BEFORE collect, not left to `experiment_stack.bash`'s SIGTERM. New manifest key `teardown_preempt`. | **ml#1408** |
| **T6 owner item 1** — `util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml` pinned to `max_hidden_units: 64` **and** `max_iterations: 64`, matrix + every moon `include` | **ml#1409** |
| Campaigns can pin cascor to a **worktree** (`JUNIPER_EXP_CASCOR_SRC_DIR`); `_resolve_base_config` override-precedence bug | **ml#1412** |
| Recurrence brought under the wall-ordering gate; last 5 offenders cleared | **ml#1414** |
| Cross-view inconsistency **measured**: 52 + 149 title/body diffs on matching ids, ZERO id and ZERO metadata divergence, collapsing to 4 cosmetic artifacts | **ml#1415** |
| Driver consumes `install_hint` instead of pointing at the response it already holds | **ml#1423** |
| `util/ad-hoc/2026-08-26_push_signed_fixup.py` — land a signed fixup on an existing PR branch | **ml#1426** |
| **E-C re-run executed and published** (F-P4-7) | **ml#1455** |
| `by-repo` / `by-status` become a **projection** of `by-area`, gated by `--check-views` | **ml#1462** |
| The five extraction artifacts repaired in the canonical corpus | **ml#1467** |

### E-C, the headline result — and its limits

`e-c-cascor-noise-robustness-20260829T003546Z`, cascor **`67d7ea3`** (the T6 pin), 8/8, 2,437 s.
**The 12-unit iteration cap was what flattened the spiral curve**: ≈0.63–0.66 became **0.805 /
1.000 / 0.980 / 0.975** at cap 64. `moon-n20`'s cap-bound 0.975 resolved to a genuine **0.965** at
32 units, and the moon curve (1.0 / 1.0 / 1.0 / 0.965, 2/1/3/32 units) is the clean deliverable.

**Do NOT say "nothing is cap-bound now."** All four spiral cells recruited *exactly* their 64-unit
cap. Only noise 0.00 was probed above it (§1); `c002` (0.9800) and `c003` (0.9750) sit at the cap
untested higher. The defensible sentence is: *the 12-unit iteration cap no longer binds, and the one
row probed above 64 gained +0.04.*

> **`completion_reason: early_stopped` does NOT mean "converged before the cap."** Hitting the unit
> cap *produces* that label —
> `early_stop = early_stopping and (train_accuracy_reached or max_units_reached or patience_exhausted)`
> (`cascade_correlation.py:5697`, set at `:4954`); `max_iterations` appears only on the for-else. So
> a UNIT-cap exhaustion reads `early_stopped` and an ITERATION-cap exhaustion reads `max_iterations`.
> **Read `units` against `max_hidden_units`; never infer convergence from the label.** This is why
> the first draft of the grid write-up said "nothing is cap-bound".

**No accuracy or wall figure here is attributed to any commit.** The cap-12 → cap-64 jump is a
BUDGET change at one sha. Attribution across the #514 … #589 interval still needs the control arm
F-P4-6 named and that was never budgeted.

**The control reproduces exactly.** `spiral-baseline` pins `noise: 0.05`, so E-C `c001` is
**budget-equivalent** to T6's E-I `c001` — identical val (1.0000), train (0.9950), units (64),
epoch (65), from a **different checkout**. *Equivalent, not identical*: the two cell YAMLs differ in
three keys — `experiment.name`, `max_iterations` (128 vs 64) and `max_wall_seconds` (14400 vs
3600) — so `config_sha256` differs (the name alone would do that). Neither budget key binds: the
64-unit stop comes from `check_hidden_units_max()`, not the iteration bound, and both cells
finished in ~9 min against 1 h / 4 h wall budgets. `dataset_id` (`spiral-1.0.0-7a976ad4…`) and seed
(20260729) are the same. Say "budget-equivalent"; "config-identical" is falsifiable by `diff`.

**Walls are ADVISORY** — a 13-hour `clamscan` ran throughout, measured at **+6.8%** on the
budget-equivalent `c001` (552.0 s vs E-I's 516.9 s).

---

## 1. The one question this session OPENED — F-P4-7

**The spiral noise curve is non-monotonic, and capacity is not the dominant constraint.** noise 0.00
(0.8050) sits below noise 0.05 (1.0000). A one-cell probe
(`ec-noise0-cap128-probe-20260829T012038Z`, `util/ad-hoc/2026-08-28_ec_noise0_cap128_probe.yaml`):
at cap 128 val moves only **0.8050 → 0.8450**, while noise 0.05 saturates at 1.0000 on half that
budget. That **cross-cell comparison — one tier, identical split roles — is the entire basis.**

> **Do not upgrade this to "rules out capacity."** The probe's pre-registered rule was "jumps toward
> 1.0 → capacity; stays near 0.805 → real"; 0.8450 is neither, and the cap-128 cell *also* recruited
> exactly its cap, so no unconstrained stop was ever observed. Capacity buys little here; it is not
> excluded. The evidence doc was corrected on 2026-08-29 after saying otherwise.

> **Guardrail, and it cost this session a published error.** The first write-up also argued that
> train falling below val (0.8413 vs 0.8450) showed the network "is not fitting its training set".
> **cascor#582 (OPEN) invalidates that**: on the SERVICE tier `_reload_dataset` maps the artifact's
> `X_test`/`y_test` into *validation tensors* feeding patience and early stopping **in-loop**
> (`src/api/lifecycle/manager.py:3402-3403`, assigned at `:3484` — note cascor#582's own body cites
> `:3391`, which is the presence check in `_artifact_to_tensors`, not the mapping). The direct CLI
> passes none. **Both noise-0 cells** — the cap-64 grid row and the cap-128 probe — terminated
> `early_stopped`, so that series drove their stop. Train below an in-loop-selected val is the expected
> signature of the promotion, not evidence about fit. Corrected in the evidence doc §3/§4 on
> 2026-08-29. **Any train-vs-val reasoning on a service-path grid must cite #582 or be wrong.**

*Why* the noise-free spiral is harder is unanswered and **less constrained than first written**.
It is a cascor-learner investigation, not a suite change. No entry point exists yet — that is
itself the first task: a hypothesis and a probe, not a re-run.

---

## 2. Traps added by this session

- **The editable install does NOT drag a worktree run back to the primary.**
  `__editable___juniper_cascor_*_finder.install()` registers via `sys.meta_path.append(...)` (`:76`, its first statement — the function then ends on an unrelated `sys.path.append`) — **after**
  the default `PathFinder` — so CWD wins and the finder is only a fallback. Verify, don't assume:

  ```bash
  /opt/miniforge3/envs/JuniperCascor1/bin/python3.13 util/ad-hoc/2026-08-26_cascor_import_provenance.py <cascor-worktree>/src
  ```

  (Requires the `JuniperCascor1` env — that is the env every cascor experiment uses. Exit 1 on a
  mixed tree. **That script's own header is stale**: it cites `experiment_stack.bash:95` and calls
  `CASCOR_SRC_DIR` hard-wired, which ml#1412 changed — fix it if you touch the file.)
- **What this does and does NOT retire.** It retires the belief that a pinned worktree yields a
  mixed tree. It does **not** retire (i) the T6 campaign driver's own freeze —
  `util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash` still reads the **primary** checkout's status
  and SHA and exits 2/3 on drift (its `:25-27` comment still states the now-refuted rationale, and
  `:39` hard-codes `CASCOR_DIR`); nor (ii) **peer holds**, which were CPU/GPU contention holds — a
  module-resolution fact says nothing about GPU contention, and this session's own +6.8% clamscan
  figure shows contention is real. Use `util/ad-hoc/2026-08-28_ec_cap64_launch.bash` (pin-aware) or
  update the driver.
- **The run record does not prove the pin, and one field actively contradicts it.** A pinned run's
  `manifest.json` carries `git = {}` (empty) and
  `packages["juniper-cascor"].editable_source = "…/juniper-cascor"` — **the PRIMARY** — because that
  is where the editable install points regardless of what ran. `JUNIPER_CASCOR_GIT_SHA` (in
  `env/launch.env`) is the only pin record and it **cannot fail**, since the launcher stamps it from
  the *requested* tree. Evidence is the import probe plus `/proc/<pid>/cwd`, captured while the
  service is alive — after the run, the pin is not recoverable from the artifacts.
- **A pinned campaign needs THREE variables, not two**, and the wrong value is silent:
  `JUNIPER_EXP_CASCOR_SRC_DIR=<worktree>/src` (which code),
  `JUNIPER_EXP_PROJECT_DIR=<shadow dir>` (which **config** — this must be the shadow, *not* the
  ecosystem root; §5's survey stanza uses the ecosystem root for a different purpose, do not copy it
  here), and `JUNIPER_EXP_DEPLOY_DIR=<real juniper-deploy>` (the shadow has no `juniper-deploy`).
  `_resolve_base_config` **falls back silently** when the override does not resolve, so a wrong or
  dangling `PROJECT_DIR` reads the PRIMARY's `spiral-baseline.yaml` — pinned code, primary config.
  `util/ad-hoc/2026-08-28_ec_cap64_launch.bash` sets all three and preflight-fails on a missing pin;
  prefer it to hand-rolling.
- **A `#` at line start is a "heading" to the docs screen, wherever it sits** — including inside a
  `**Detail**:` body. Two such lines failed Sequence Safety; 307 one-line normalizations were only
  WARN. It fails on *heading* deletions, not volume.
- **Re-cut, don't fixup, when a commit needs a waiver trailer.** The screen reads `BASE..HEAD` so a
  fixup satisfies the PR check — but **Post-Merge Main Verification re-runs it against main**, and
  whether the trailer survives the squash is not guaranteed. Verified landed: `d1738886`, `07a8514a`.
- **An idempotence guard that counts the OLD string first breaks when `old` is a SUBSTRING of
  `new`** (backtick-wrapping is exactly that shape) — mask applied sites before counting. The tell
  was a dry run printing `wrote` for a file that should have said `unchanged`.
- **A cross-view check finds families DISAGREEING; it can never find a defect all three SHARE.**
  `JR-ML-TRAIN-054` had both defect shapes and never appeared in the diff. Intra-entry quality needs
  its own scan.
- **This session's shell gate** refuses `git -C <sibling-repo>` outright (you *will* hit this
  checking `main`), plus loops and heredocs. `&&` / `;` chains and `$(…)` are fine. Multi-step logic
  belongs in a `util/ad-hoc/` script.

---

## 3. The remaining tail — UNOWNED

"The plan" throughout = `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`
(one of 17 `CLI-EXPERIMENTATION` notes — always name it).

**From the CLI-experimentation arc**

- **G-16's live-refusal half** (plan `:238`, `mnist` unavailable on this host) is unverified. Needs a
  live juniper-data; experiment ranges are data `8110-8139`, cascor `8230-8259`
  (`util/experiment_stack.bash:122-127`).
- **`install_hint` is shipped (ml#1423) but INERT.** Re-checked 2026-08-29: juniper-data's newest
  *release* is v0.11.0 (2026-07-29) and `install_hint` is **absent from that tag**; it is present on
  the default branch. Two ways to mis-check this: juniper-data carries newer **alpha tags**
  (`v0.15.1-alpha` etc.) that are not releases and also lack the field — so do not use `git tag`;
  and GitHub marks **v0.10.0** as `Latest`, so anything resolving "latest release" programmatically
  gets the wrong one. Compare by date across `gh release list`. The named downstream casualty is
  **T4's generator-parity CI lane** (juniper-data-client#157), which installs `juniper-data[api]`
  from PyPI. A juniper-data release is what makes the fix visible.
- **T2's permanent residual** — the read-only settings surface for cascor / recurrence was
  **declined, not deferred**. No PR, issue, or scoped design exists; reviving it means writing that
  scope first, then an owner decision.
- **T7's Wave 7.6 minimum — FIVE items, not four**: the **experiment-config layer** (dropped from
  the 08-26 tail, restored here), plus **G-5** (zero recurrence plotting code, plan `:217`),
  **W-5** (register `ar_p` in the bench registry, plan `:945`) and **W-7** (`--results-dir` for
  `bench.run_benchmark`, plan `:947`), **G-4** (no recurrence Grafana dashboard, plan `:216`), and
  **G-17** (no `performance` pytest marker, plan `:240`). These are **plan gap/work IDs, not `JR-*`
  requirement IDs** — do not grep `notes/requirements/` for them. (Line numbers verified
  2026-08-29; a first pass of this handoff had four of the five crossed, so re-check rather than
  trusting them after the plan is next edited.)
- **R-1's second clause** — do not report `succeeded` when zero candidates were installable. **Beware
  a name collision**: the plan's own `R-1` (`:1236`) is an unrelated Prometheus-scrape risk. The
  clause lives in
  `notes/JUNIPER_2026-08-12_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-SPIRAL-RESURFACE-EVIDENCE.md:183`.
  Homeless since `HANDOFF_2026-08-15_cli-experimentation-second-sweep.md`.
- **Plan §12.2 items 1 and 3** — run-level durations are not a metric; no cross-app comparison
  surface. (§12.2 item 2 **is G-17**, also listed above — one item, two homes.)
- **PF-4 / PF-8** — need a decision, not a suite, **gated behind the perf-lane phasing note** (that
  gating is what says whether the decision is actionable yet).
- **PF threshold ratification (§12)**, **W-12/Q-7** (csv_import corpus — parked), **F-P1-2**
  (Grafana render) — evidence-doc §6 lists all three still open; no handoff in this chain has
  carried them.
- **Q-6's unfollowed half** — `util/experiments/run_suite.py:112` still refuses `app: cascor` with
  `parallel > 1`. Lifting it needs a cascor version floor asserted at suite load, and no *released*
  cascor carries #523.
- **Launcher fast-fail** — the health gate cannot distinguish "slow boot" from "crashed at import";
  a dead-process check turns 180 s waits into instant, correctly-classified failures. Evidence doc
  §4 calls it worth a follow-up; never carried.
- **F-7 provenance re-pin** — ml#1142 recorded the recurrence re-pin beneath the plan's
  authoring-time table; the table is deliberately unchanged, **no further action assumed**. Dropped
  from the chain at the 08-26 hop; restored here so the disposition stays recorded.
- **Two ml#1412 callers were never updated** — see §2. `util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash`
  states a refuted rationale and hard-codes the primary; and
  `util/ad-hoc/2026-08-21_h2h_paired_campaign.bash:67` derives the service arm's SHA from
  `${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor` and refuses when it differs from the CLI arm's
  worktree (recorded in `reports/tensor-hash-probe-2026-08-28/ANALYSIS.md:165-168`). **Nuance:**
  under the shadow-dir configuration §2 prescribes, that path *is* the pin and the check **passes**
  — it fails only with the script's default `JUNIPER_EXP_PROJECT_DIR` (`:53`, the ecosystem root).
  So this is a default-value trap, not a broken script; do not "fix" it before reproducing it.
- **NEW — F-P4-7's learner question** (§1), with no entry point yet.
- **NEW, minor** — E-C's noise 0.10 / 0.20 rows are untested at cap 128 (both ≥0.975 at 64; the
  0.00 probe showed +0.04 per doubling, so expected gain is small).

**From the requirements arc**

- **Detail *selection*.** `JR-ML-OBS-003`'s Detail quotes the first-pass revision line its own source
  supersedes. Re-extraction, a different evidence bar; ml#1467 deliberately did not. Scope unknown —
  no scan exists for it, which is the same gap §2's last trap names.
- **The plan's §97 design statement** (`notes/JUNIPER_2026-05-11_…REQUIREMENTS-IDENTIFICATION-PLAN.md:97`)
  still describes `by-repo`/`by-status` as *"thin indexes that link into by-area — not duplicates"*.
  Shipped reality (ml#1462) is a **generated projection with full bodies**, deliberately. Nobody owns
  reconciling the plan text. (Its §11 v5-1 row **was** stale on the same subject and is corrected as
  part of this session.)

---

## 4. State at handoff

- **juniper-ml `origin/main` was `9cc08605` when this was written — RE-CHECK IT, do not branch from
  a recorded sha.** `git fetch origin && git rev-parse --short origin/main`. Whole-file PRs from a
  behind-main copy are this repo's recorded self-clobber class.
- **The PRIMARY checkout's local `main` is behind `origin/main`** (4 commits at time of writing).
  The cleanup procedure's Phase-7 "restore the primary to up-to-date main" did not run. Worth doing
  before anyone works there — but note a session isolated in a worktree **cannot**: `git -C` at the
  shared checkout is refused (§2).
- **Three uncommitted artifacts** at the time of writing, all landing on `main` by the closing PR:
  this document, and corrections to
  `notes/JUNIPER_2026-08-09_…P4-STUDIES-EVIDENCE.md` (the #582 guardrail, the capacity walk-back,
  the `early_stopped` mechanism, the ml#1397 discharge) and to
  `notes/JUNIPER_2026-05-11_…REQUIREMENTS-IDENTIFICATION-PLAN.md:450`. **If you are reading this on
  `main`, that PR merged and §5's stanzas will find them**; if you branched from an `origin/main`
  older than the closing PR, the `CORRECTION 2026-08-29` grep returns nothing and that is expected,
  not a missing file.
- **Cascor pin worktree RETAINED**:
  `worktrees/juniper-cascor--exp--e-c-cap64--20260828-1922--67d7ea35` (detached at `67d7ea3`), with
  `~/.local/state/juniper-experiments/shadow-ec-cap64/juniper-cascor` symlinked to it.
  - **HAZARD — `util/remove_stale_worktrees.bash` has no staleness predicate whatsoever.** It is a
    bare loop over `git worktree list | grep worktrees` calling `git worktree remove` on every hit.
    **Its blast radius is whichever repo you run it from, and it lives in juniper-ml's `util/`** —
    so run there it enumerates the ~70 `juniper-ml/.claude/worktrees/*` session checkouts, *not*
    cascor's. It reaches this cascor pin only if someone first `cd`s into the cascor checkout.
    Either way do not run it unguarded: the larger loss is every unlocked juniper-ml session
    worktree, which is where in-flight uncommitted work lives (this session's own worktree survived
    a hypothetical run only because it is `locked`).
  - It **is** cheaply rebuildable, so this is not precious: `git -C <juniper-cascor> worktree add
    --detach <path> 67d7ea3`, then re-point the shadow symlink. Its ignored files are 24
    `__pycache__` dirs, nothing else.
  - **The shadow symlink is load-bearing and fails SILENTLY.** Dangling → `_resolve_base_config`
    falls back to the PRIMARY's config, producing the invisible mixed tree §2 warns about. If you
    remove the worktree, remove or re-point the symlink in the same breath.
- **Merge approval**: granted for this session ("approve all, I'll spot-check after"). **Session
  scoped — re-ask.** The predecessor's standing *ask-before* list still applies and this session
  exercised two of its clauses: ask before spending GPU hours beyond named suites, before lowering
  the quiet bar or running unattended overnight, before pulling the shared cascor checkout if a live
  peer objects, and before acting on any predecessor §0.1 residual.
- Host at close: campaign ranges clear, GPU ~803 MiB. An unrelated E2E stack may hold `:8202`,
  `:8201`, `:8050` from the **primary** cascor checkout; per §2 that no longer blocks a pinned
  campaign, but it does still contend for CPU/GPU.

## 5. Verification (one stanza per Bash call — `git -C` at a sibling repo is refused here)

```bash
python3 util/requirements_consolidate.py --check-roundtrip

python3 util/requirements_consolidate.py --check-views

python3 util/ad-hoc/2026-08-26_t6_render_grids.py /home/pcalnon/.local/state/juniper-experiments/suites/e-c-cascor-noise-robustness-20260829T003546Z

JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper python3 util/ad-hoc/2026-08-20_wall_ordering_survey.py

grep -n "F-P4-7\|CORRECTION 2026-08-29" notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md

ss -tlnpH | grep -E ":(811[0-9]|812[0-9]|813[0-9]|82[3-5][0-9])" || echo "campaign ranges clear"
```

Expected: `1814 entries, 15 area files, 0 mismatching`; `1814 entries, 16 derived files, 0
mismatching`; the 8-cell E-C grid (all four spiral rows at `hidden 64`); the survey's **first**
summary block `INVERTED 0 / EQUAL 0 / OK 25` — it prints a **second** AD-HOC block ending `OK 2 /
TOTAL 2`, which is not a regression; the F-P4-7 finding and the #582 correction; clear campaign
ranges. The survey needs `JUNIPER_EXP_PROJECT_DIR` because from a juniper-ml-only checkout 15 of 25
suites are `UNRESOLVED` and it still prints a clean-looking summary.

## 6. What this document does NOT cover

Absence here is deliberate, so a dropped item stays distinguishable from an out-of-scope one:

- The **backup / Duplicati arc**, the **P5 fleet rollout**, the **defect register**, the **canopy E2E
  arc**, and **juniper-service-core**'s round-29 work — all had other owners and moved during this
  session.
- Open cascor issues **#572, #573, #578** (other owners). **#582 is in scope** only as §1's
  interpretation guardrail.
- The **requirements corpus's content quality beyond the five repaired artifacts** — see §3.
