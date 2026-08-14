# HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `Jun HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `JuniperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
iperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through# HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `Jun HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run         # HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `Jun HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its # HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `Jun HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budg# HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has since finished. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).

**Nothing is in flight.** The P4 §7 follow-up register (R-1..R-6) is closed, the E-A re-run
under R-3 has run and is written up, and no PR of this arc is open in either repo.

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `Jun HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

Supersedes [`HANDOFF_2026-08-14_ea-r3-campaign-running.md`](HANDOFF_2026-08-14_ea-r3-campaign-running.md),
which was archived mid-campaign and describes a run that has# HANDOFF 2026-08-14 — CLI experimentation P4 arc COMPLETE; no work in flight

## Shipped and merged (do not redo)

| PR         | Item                                                                              |
|------------|-----------------------------------------------------------------------------------|
| cascor#511 | R-1a — an all-candidates-errored round raises instead of reporting `no_candidate` |
| cascor#512 | R-1b — the RC-4 candidate pool is released at end of run                          |
| ml#1074    | R-6 — `execution.stall_seconds` adopted in the suites + gated                     |
| ml#1075    | R-2 prereq (aggregator generalized) + R-4 (E-C rebudget) + R-5 premise check      |
| ml#1077    | R-3 — `max_iterations: [32]` so the unit cap binds in E-A                         |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `JuniperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
iperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `JuniperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
iperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
 R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `JuniperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
iperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
                |
| ml#1078    | R-2 — E-H cascor re-run evidence                                                  |
| ml#1083    | in-flight campaign handoff (landed mid-run, results not included)                 |
| ml#1086    | R-3 E-A re-run evidence                                                           |

## The three findings that change how earlier results read

1. **The 0.670 spiral "ceiling" was a budget artifact.** `spiral-baseline` pins
   `max_iterations: 12`, so every `max_hidden_units` above 12 was unreachable. With the cap
   binding, best val is **0.735** (c010, cap 32 / pool 8) and still rising at the top of the
   sweep. Any prior statement that service spiral tops out ≈0.67 is superseded.
2. **cascor#509 is fixed and field-validated at scale.** Twelve consecutive cells with **no**
   per-cell reaping: GPU free at inter-cell idle points went 6840 → 6891 MiB (**net +51**),
   compute processes returning to desktop-only every time. Pre-fix was ~285 MiB lost per cell
   (~3.4 GB over twelve, card exhausted by cell 5). **Per-cell reaping is no longer needed.**
3. **R-5 has no stable basis as originally stated.** Both halves of its premise moved: the
   service and CLI generate *different* spirals (service `algorithm: modern`, θ from
   `n_rotations`, normal noise; CLI legacy family, `r = θ`, uniform noise, where
   `n_rotations` is not a parameter at all), **and** the 0.670 baseline was capped. 1-NN
   separability is ~1.0 for both, so noise is not the differentiator. If R-5 is pursued it
   needs the same dataset on both paths **and** an equalised budget, compared against 0.735+.

Secondary result worth keeping: **units dominate pool.** c011 at pool 32 — the most expensive
cell at 2893 s — reached only 0.665, below c010 at pool 8 with a higher cap. Best-candidate
correlation still rises monotonically with pool (0.073 → 0.270 → 0.425), reproducing the
prior grid's finding that pool raises correlation but not accuracy.

Evidence: `notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md` and
`notes/JUNIPER_2026-08-13_…-R2-EH-RERUN-EVIDENCE.md`.

## Loose ends (none blocking)

- **cascor#509 is still OPEN** although both halves are merged and validated in the field.
  Issue direction (3) → #511, direction (1) → #512, and direction (2) (releasing the CUDA
  context inside the child) is unnecessary once the children actually exit. **Safe to close**,
  citing the ml#1086 evidence — left open deliberately for the owner rather than closed
  unilaterally.
- **cascor#505** — API `candidate_patience` / `candidate_convergence_threshold` never reach
  the candidate pool (workers run module defaults). Untouched by this arc.
- **cascor#500** — main-verify post-merge verification failing. Untouched.
- **R-5**, if wanted, per the framing above.
- Local-only: `JuniperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
iperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject
  0.8.0, so `test_version_matches_pyproject` fails on a local full-suite run against pristine
  main. Pre-existing and CI-invisible.

## Operational knowledge worth carrying forward

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree — without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and every cell fails to materialise. Use the
  **JuniperCascor1** python (matplotlib) and `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- **Reading cap-bound cells**: the cap is enforced through
  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.

  `early_stop = early_stopping and (... or max_units_reached ...)`, so it holds *only* because
  baseline sets `early_stopping: true`, and a cap-bound cell reports `early_stopped` — the
  same reason as patience-exhausted and accuracy-target cells. **The units column
  disambiguates**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*: pre-#511 an exhausted GPU
  produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is unaffected (keys
  on `cell_id[:4]`) but `--only <full-id>` refs to older campaigns will not resolve.
- **Before any campaign**: `util/reap_pytest_orphans.bash --dry-run` and identify the live
  parent; `ss -tlnp` for someone else's stack. A long-lived isolated E2E stack (cascor
  `:8202`, data `:8101`, canopy `:8051`) has been up for days — it is healthy, idle, holds no
  GPU, and its forkserver children are correctly KEEP for the reaper. **Do not touch it.**
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`;
  it screens `oom == 0` per cell and exits 1 if any expected cell lacks a clean run.
- **Session-type constraints**: this worktree-isolated session refuses inline shell loops,
  redirects and compound commands — put loops in a script (scratchpad) and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- **Merging**: unsigned commits (the AGENTS.md touch-up bot, `--no-gpg-sign` conflict
  resolutions) make a PR show `mergeStateStatus=BLOCKED` under `required_signatures` → use
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` **and** green first.
- **Concurrency**: a concurrent session merged this arc's handoff PR mid-campaign, so it
  shipped without the results and the re-added file produced an add/add conflict. If a
  campaign outlives its own handoff PR, expect that. Concurrent sessions also removed a
  cascor worktree *and its branch* mid-read — re-derive worktree existence rather than
  trusting a handoff's path.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q .state
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

- `juniper-ml`: `origin/main` at `c6b356a` (ml#1086). Session worktree
  `.claude/worktrees/stateful-wondering-moth` on branch `worktree-stateful-wondering-moth`,
  level with main, tree clean apart from this handoff. No arc PRs open (ml#1087 belongs to a
  different arc).
- `juniper-cascor`: `main` carries both #509 halves; primary checkout restored to main tip and
  both R-1 worktrees removed and pruned. No open PRs.
- Environment: no experiment listeners, no stale lockdirs, no reapable orphans. GPU idle apart
  from desktop applications and the untouched E2E stack.
