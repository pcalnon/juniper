# HANDOFF 2026-08-13 — P4 Follow-Ups: R-6 Shipped, R-1 Designed and Ready to Write

Continue the **CLI experimentation program**. Successor to
[`HANDOFF_2026-08-12_p4-spiral-resurface-and-followups.md`](HANDOFF_2026-08-12_p4-spiral-resurface-and-followups.md),
which remains accurate for everything it records. The owner approved **all six** §7 follow-ups
(R-1..R-6) plus two decisions captured below. R-6 is shipped as a PR; R-1 is fully designed but
**no cascor code is written yet**.

## Owner decisions this session (binding)

- **R-4**: give E-C's spiral rows an **E-A-class budget** — do *not* reduce E-C to a moon-only study.
- **R-1**: attempt the cascor work **from the current session** rather than a separate one. Confirmed
  workable: `git -C <cascor> worktree add …` succeeds from a juniper-ml session worktree.

## Completed this session (do not redo)

- **R-6 — PR [ml#1074](https://github.com/pcalnon/juniper-ml/pull/1074), OPEN, not merged.** Branch
  `feat/p4-suites-adopt-stall-seconds`. Adopts `execution.stall_seconds: 1200` in the suites, deletes
  `util/ad-hoc/2026-08-10_driver_stall_shim.py`, and adds `tests/test_experiment_suite_yamls.py`.
- **The gate found two suites outside the R-6 scope with the same latent defect**, both fixed in the PR:
  `util/experiments/suites/cascor-budget-sweep.yaml` (pool→32) and
  `util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml` (pool→16). PF-3 is the consequential one —
  a stall misclassification there would corrupt the speedup curve the suite exists to measure.
- **`tests/test_run_suite.py` and `tests/test_list_runs.py` were documented in AGENTS.md but never wired
  into `ci.yml`** — so ml#1069's own `stall_seconds` tests were themselves ungated. All three are wired now.
- **The §6 retraction (ml#1072) is absorbed.** Do not reintroduce any claim that the *original* P4
  evidence was contaminated; it agrees with the clean re-run. See §6.1 of the evidence note.

## Remaining work (priority order)

All code work: worktree, PR, **never self-merge**, `gh pr list` dup-guard first.

1. **R-1 — cascor#509, honest outcomes (the standalone-valuable half). DESIGN IS DONE; write it.**
   Create a worktree off cascor `origin/main` per the ecosystem convention (a prior session's worktree
   was created, left unused, and cleaned up again — there is nothing to resume, only to write).

   The defect: in `src/cascade_correlation/cascade_correlation.py`, `grow_network` (~line 4388) does

   ```python
   if not (training_results := self._get_training_results(...)) or not training_results.best_candidate:
       self._completion_reason = "no_candidate"; break
   ```

   which conflates **"no candidate was good enough"** (a real algorithmic outcome) with **"no candidate
   could be trained at all"** (infrastructure — a full GPU, where `CandidateUnit.__init__` dies with
   `AcceleratorError: CUDA error: out of memory`, every candidate is discarded, and the run still
   reports `succeeded` / `no_candidate` / 1 unit).

   **The signal already exists and is simply not consulted.** In `_process_training_results` (~line 2889):
   - `success_count` = candidates that trained **without erroring** ← **use this**
   - `successful_candidates` = candidates meeting the **correlation threshold**
   - `failed_count` = `len(results) - successful_candidates` ← **conflated; do NOT use it as an error count**

   Predicate: candidates were attempted (`len(training_results.candidate_ids) > 0`) **and**
   `success_count == 0` → infrastructure failure, not `no_candidate`.

   Escalation: **raise**. `TrainingLifecycleManager` (`src/api/lifecycle/manager.py` ~line 2386) wraps
   `self.model.fit(...)` in `except Exception as e: sm.mark_failed(str(e)); state.update_state(status="Failed"…)`,
   so any exception out of `fit` already yields the correct terminal state, metric, and broadcast — no new
   plumbing. Set a new `_completion_reason` (e.g. `candidate_training_failed`) **before** raising; it
   survives the raise because `get_status` reads it off the persisted network object.
   `TrainingError` lives in `src/cascade_correlation/cascade_correlation_exceptions/cascade_correlation_exceptions.py:53`.

   **Must also update** `_KNOWN_COMPLETION_REASONS` in `src/tests/integration/test_golden_trajectory.py:31`
   (currently `{residual_collapsed, no_candidate, below_threshold, early_stopped, max_iterations}`), and add
   unit coverage beside `src/tests/unit/test_completion_reason.py`. `completion_reason` is consumed by canopy
   (`src/api/models/cascor_model.py:109` → `stopped_reason`), so a new value is a cross-repo-visible contract.

2. **R-1 second half — forkserver lifecycle** (cascor#509 directions 1/2): candidate forkserver children
   (`mp.get_context` at cascade_correlation.py ~:1062 / ~:1111) outlive teardown holding ~116 MiB CUDA each.
   Larger and independent of the honest-outcome half; consider a separate PR.

3. **R-3 — raise `max_iterations` with the unit cap in E-A.** `spiral-baseline.yaml` pins
   `max_iterations: 12` while E-A sweeps `max_hidden_units` to 32, so cap-16 and cap-32 are the same
   experiment (c006≡c009, c007≡c010). **`run_suite` matrix expansion is a cross-product**, so adding
   `max_iterations` as a second axis over-generates — use a fixed override or explicit `include:` pairs.
   **Note the conflict**: R-3 edits `p4/e-a-cascor-budget-sweep.yaml`, which ml#1074 also touches — land or
   rebase on #1074 first.

4. **R-4 — E-C spiral rows at E-A-class budget** (owner-decided). Currently based on `spiral-smoke.yaml`
   (2-unit cap), where the noise curve is flat because the cap binds. Will also need its own
   `execution.stall_seconds` once the pool grows — the new gate enforces that automatically.

5. **R-2 prereq — generalize the campaign tooling.** `2026-08-10_ea_finish_cells.bash` **already has**
   `JUNIPER_SUITE_YAML` (line 27) — the handoff's R-2 row describes usage, not a gap. Only
   `2026-08-10_ea_aggregate_clean.py` needs work: it is hard-scoped to the glob `e-a-cascor-budget-sweep-*`
   with a fixed 12-cell expectation.

6. **R-2 — re-run the E-H cascor leg only.** Verified independently: of the remaining suites only
   `p4/e-h-real-data.yaml` is `app: cascor`; E-D/E-E/E-F/E-G and `e-h-recurrence-real-data.yaml` are
   `app: recurrence` and are not implicated by cascor#509. Do not re-run them.

7. **R-5 — service-vs-CLI spiral gap.** Best cell 0.670 val vs ≈0.995 for the direct CLI at radius-10.
   Sequence **after R-3**, which removes the "budget ceiling" explanation. **Confirm the two paths are even
   the same problem** before concluding anything — the CLI figure is radius-10, the service config is
   `n_rotations: 3.0` / `noise: 0.05` via juniper-data's generator.

## Key context (this session's discoveries)

- **This session type is worktree-isolated.** Compound shell commands that `cd` into another repo, or use
  redirects/loops, are **refused**. Use plain single `git -C <abs-path> …` commands; they work, including
  `worktree add`. `until`-loops and `sleep`-chains are blocked — poll by re-running a plain command.
- **Reproduce the sequence-safety screens locally** instead of fighting the CI log API:
  `pip install 'juniper-ci-tools>=0.8.0,<0.9.0'` then `juniper-symbol-loss-check` / `juniper-docs-additions-check`
  with `--base origin/main --head HEAD` and the ml scope. This diagnosed #1074's red in one shot.
- **Deleting a `util/**/*.py` FAILs the symbol screen.** The waiver is a commit trailer in the BASE..HEAD
  range whose value is the bare `func:<name>` form (verified: the shim's `main` waived correctly; a `*`
  wildcard is rejected). Because the value must survive squash, keep it in the commit message.
- **The AGENTS.md touch-up bot pushes a commit onto your PR branch.** Always `git pull` before amending or
  you will need a force-push. It also means a branch you just pushed is already behind.
- `get_candidates_error_messages` returns a **dict** despite `TrainingResults.error_messages: List[str]` —
  a pre-existing annotation inconsistency; handle defensively.
- `spiral-smoke.yaml` caps `max_epochs` but **not** `candidate_epochs` — the candidate phase is full-length
  even at smoke budget. That is why stall risk keys on **pool size, not overall budget**.

## Verification commands

```bash
gh pr view 1074 --repo pcalnon/juniper-ml --json state,mergeable -q '.state'   # OPEN until owner merges
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q '.state'       # OPEN
python3 -m unittest tests/test_experiment_suite_yamls.py                       # 5 tests, green
grep -nE "app: (cascor|recurrence)" util/experiments/suites/p4/*.yaml          # R-2 scoping
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor worktree list   # R-1 worktree present
nvidia-smi --query-gpu=memory.free --format=csv                                # before any campaign
```

## Git state at handoff

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main`.

```bash
git fetch --prune && git log --oneline HEAD..origin/main   # must be empty before you commit
```

- `juniper-ml`: session worktree `.claude/worktrees/gleaming-riding-ritchie` on branch
  `feat/p4-suites-adopt-stall-seconds` (the feature commit, the touch-up bot's `AGENTS.md` date bump, the
  symbol-loss waiver, and this handoff). Pushed and **CI green**; PR #1074 needs only the owner's merge.
  `origin/main` was `adbd49b` at branch point. Other open PR: **#1073** (ruleset validation, different arc).
- `juniper-cascor`: `origin/main` = `ed7c590`, primary checkout in sync. **No cascor code was modified and
  no cascor branch or worktree remains** — the R-1 worktree was created, never written to, and removed
  during cleanup. Issues #509 and #505 remain OPEN.
- Environment: no experiment campaign was run. GPU untouched; no listeners, no lockdirs claimed. One
  side effect worth knowing: `juniper-ci-tools` was pip-installed into the active `JuniperCascor1` env to
  reproduce the sequence-safety screens locally. It is a plain wheel (not an editable), so it does not
  affect the editable-install drift checker; leave it or uninstall it, either is harmless.

## Final update to state

Where R-1 stopped

The design is settled and recorded in the archived handoff, so it survives this pause. The last thing I confirmed — and it matters — is that train_candidates re-raises CandidateTrainingError unchanged (line 2152) rather than swallowing it, and _get_training_results only wraps other exceptions into TrainingError. So a raise from grow_network propagates cleanly to the lifecycle manager's except Exception → mark_failed → status "Failed". No handler in the path would eat it.

That also means the existing CandidateTrainingError is the correct type to reuse — its docstring describes the identical failure class ("raising this error instead fails loudly"), so R-1 adds no new exception, just a guard and a new completion_reason value.

Two things still to decide when you pick it back up: whether the new completion_reason string is worth the cross-repo contract change (canopy consumes it via stopped_reason), and whether the forkserver-lifecycle half ships as a separate PR — I'd recommend yes, since the honest-outcome half is independently valuable and much smaller.

---
