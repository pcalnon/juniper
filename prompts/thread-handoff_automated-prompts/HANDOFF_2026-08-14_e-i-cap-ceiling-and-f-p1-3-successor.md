# HANDOFF 2026-08-14 — E-I shipped; the spiral arc is closed, F-P1-3 is the successor

Continue the **CLI experimentation program**. Successor to
[`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md).
The P4 §7 register (R-1..R-6) is closed, **R-5 is closed**, and the spiral capacity question is
**answered**. There is no campaign in flight and nothing of this arc is unmerged.

## Do not redo — all merged

| PR | Item |
| --- | --- |
| ml#1086 | R-3 E-A re-run evidence (cap binds; 0.670 was a budget artifact) |
| ml#1093 | **R-5 closed** — the gap was `n_rotations`, not the service tier |
| ml#1094 | **E-I cap-ceiling** — spiral reaches 0.995; suite + campaign driver + evidence |
| cascor#511 / #512 | R-1a honest outcomes / R-1b forkserver lifecycle |
| cascor#514 | #505 — candidate patience + convergence now reach the pool |

ml main at the E-I merge `f312f32`; cascor main at #514. **cascor has zero open issues and zero
open PRs** — #509, #505 and #500 were all closed 2026-08-14 (the first two by their fixes, #500
as stale after six consecutive green main-verify runs).

## What was settled, so you do not reopen it

**The spiral question is closed from two independent directions.** Two campaigns ran concurrently
on 2026-08-14 and agree:

- ml#1093 held the budget fixed and moved the dataset: at cap 8, `n_rotations` 3.0 -> 1.0 moves
  val **0.595 -> 1.000**.
- ml#1094 (E-I) held the dataset fixed and moved the budget: at `n_rotations` 3.0, cap 32/64/128
  gives val **0.735 / 0.945 / 0.995**, ROC-AUC 1.000 at 128 units.

They meet on a shared anchor — ml#1093's control arm *is* E-A's c004 at val 0.595, exactly the
8-unit point of E-I's curve. **F-5's first two hypotheses are both true and its third is false**:
budget ceiling yes, parameterisation difference yes, genuine service-tier limitation **no**. The
derived number neither produces alone is a **~16x capacity ratio** — 8 units for `n_rotations` 1.0
vs 128 for 3.0. Full pool-8 curve: 4u .545 / 8u .595 / 16u .610 / 32u .735 / 64u .945 / 128u .995.

**Do not re-run E-A or E-I to "confirm" this.** Both notes carry their own controls; E-I's cap-32
cell reproduced E-A's c010 to the digit off the same content-addressed `dataset_id`.

## Remaining work

### 1. F-P1-3 — the direct CLI still cannot be run at a controlled budget (the successor)

This is the live open defect and the natural next question. ml#1093 reproduced it the same day
and explicitly left it: *"Diagnosing which budget actually governs that phase is out of scope
here and is left with F-P1-3."*

The symptom, freshly observed: an arm chosen to be trivially small (`max_hidden_units: 2`,
`candidate_pool_size: 4`, `candidate_epochs: 50`, `max_epochs: 100`) trained its 8 candidates
across 2 growth rounds in ~4 minutes, **reached its 2-unit cap**, then produced **no further log
output for ~11 minutes** while the process and its forkserver stayed alive, and had to be killed.

The load-bearing detail: **the phase it stalls in is not the one the W-11-mapped knobs govern.**
W-11 (cascor#489/#491) mapped the candidate-pool knobs and they demonstrably apply — the pool
trained and the cap bound. Something *after* cap-reached does not terminate. Start by finding what
runs between "cap reached" and "process exit" on the direct-CLI path, not by re-checking the knob
plumbing, which two waves have now verified.

Note this is a **CLI-path** defect: the service path terminates correctly at the cap in all 12
E-A cells and all 3 E-I cells.

### 2. Restore the primary checkout (one line, blocked here)

Phase 7 of the worktree cleanup procedure was **not** performed — a worktree-isolated session
refuses `git -C` into the shared checkout. From a non-isolated session:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git checkout main && git pull --ff-only origin main
```

### 3. Owner-decision items, still parked (unchanged, not blocking)

Q-6 (one-cascor-per-checkout / H-7 shared `logs/juniper_cascor.log`), Q-7 + W-12, F-P1-2 (the
native Grafana squatting `:3000`), PF threshold ratification (plan §12), F-P1-3b (direct-CLI
profiling priority). ml open issues #1011 / #1012 are the owner-decision branch-protection pair.

### 4. Not mine, do not merge without checking ownership

ml#1096 (`fix/release-train-propose-signed-commits`) was open at handoff time and belongs to a
concurrent session.

## Reusable findings from this arc

- **The budget trap.** The limit that actually ends a run is the **driver's**
  `outputs.max_wall_seconds`, *not* the suite's `per_run_timeout_seconds` — `run_suite` never
  passes `--max-wall-seconds`, so an unoverridden cell silently inherits `spiral-baseline`'s
  **3600**. E-A's note records its widest cell (c011, 2893 s) as never approaching the 7200 s
  per-cell timeout; it was within **707 s** of the 3600 s that would really have stopped it. Two
  of E-I's three cells would have been truncated by that default. **Override
  `outputs.max_wall_seconds` in the matrix for any long cell.**
- **Cap-binding still requires `early_stopping: true`**, and a cap-bound cell reports
  `early_stopped` — the same reason as patience and accuracy stops. Disambiguate with the units
  column: `units == max_hidden_units` means the cap bound. `epoch == units + 1` in every cell.
- **Cost is ~linear in the cap** (`derive_epochs_cap`: `effective_iterations = min(max_iterations,
  max_hidden_units)`); measured 1.94x then 1.46x per doubling. Plan with the linear bound — it
  errs high, which is the safe direction.
- **cascor#512 is validated at width, not just count.** E-I held a 128-unit cascade for 71 minutes
  with no per-cell reaping; desktop-baseline idle points read 6851 -> 6848 -> 6848 -> 6848 MiB.
  Per-cell reaping is no longer needed anywhere.
- **`gh pr checks` has no `--json` flag in this gh build.** A watcher built on it gets an empty
  string every poll and sleeps forever — silence indistinguishable from "still pending". Use
  `gh pr view N --json statusCheckRollup`. Likewise `gh pr edit` fails on deprecated
  `projectCards`; patch bodies with `gh api -X PATCH repos/OWNER/REPO/pulls/N -F body=@file`.

## Method lesson worth carrying (it bit twice in this arc)

E-I's first draft asserted, on ml#1075's authority, that the service and CLI generate **different
spirals**, and treated the ~0.995 comparator as a direct-CLI figure. **Both wrong.** ml#1093 showed
the CLI also fetches from juniper-data (both get `modern` at `radius 10.0`; only `n_rotations`
differs) and that the ~0.995 number is a *service-path* in-process repro on x4pi-scaled
route-fallback coordinates — **no direct-CLI spiral accuracy exists on record at all**. ml#1075's
conclusion was right and its mechanism wrong: it reimplemented functions carrying a
`DeprecationWarning` that are off the live path.

Caught only because ml#1093 landed on main mid-session and the rebase forced a read. Same class as
this arc's earlier retraction. **A reimplementation is only as good as its choice of source, and a
reachability check is part of that choice.** Quote prior evidence directly; do not cite it from
memory.

## Environment facts that bite

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** in a
  worktree — without it `base_config` resolves under `.claude/worktrees/juniper-cascor/...` and
  every cell fails to materialise. Use the **JuniperCascor1** python
  (`/opt/miniforge3/envs/JuniperCascor1/bin/python`, has matplotlib) and
  `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- A **live isolated E2E stack** is up and healthy: cascor `:8202`, data `:8101`, canopy `:8051`.
  It holds **zero** GPU. **Do not touch it.** Always `--dry-run` `reap_pytest_orphans.bash` and
  identify the live parent before reaping — it correctly KEEPs that stack's children.
- **Concurrent sessions push to main constantly.** Main moved under this session **twice** during
  a single merge attempt. With `strict_required_status_checks_policy` on, a behind branch is
  structurally unmergeable — re-check `behind_by == 0` immediately before every merge, and expect
  to rebase + re-run CI more than once.
- This session type is **worktree-isolated**: inline shell loops, redirects and compound commands
  are refused, and `git -C <juniper-ml>` is refused. Put loops in a script and invoke it plainly.
  `git -C <other-repo>` works.
- `JuniperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject 0.8.0, so
  `test_version_matches_pyproject` fails locally on pristine main. Pre-existing, CI-invisible.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main    # must be empty before committing
gh issue list --repo pcalnon/juniper-cascor --state open    # expect empty
gh pr list --repo pcalnon/juniper-ml --state open           # expect only others' PRs
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader   # expect desktop only
ss -tlnH | grep -cE ':(81[1-3][0-9]|82[3-8][0-9])'          # expect 0 experiment listeners
ls /run/user/1000/juniper-experiments                        # expect no stale lockdirs
```

## Git state

- `juniper-ml`: session worktree `.claude/worktrees/happy-bubbling-pinwheel` on branch
  `worktree-happy-bubbling-pinwheel`, reset to main after the E-I merge. **Re-derive the SHA —
  concurrent sessions push to main.**
- `juniper-cascor`: primary checkout at main with #511 / #512 / #514.
- Post-campaign attest clean: 0 experiment listeners, 0 stale lockdirs, GPU at the desktop
  baseline (~6841 MiB free / 945 used).
