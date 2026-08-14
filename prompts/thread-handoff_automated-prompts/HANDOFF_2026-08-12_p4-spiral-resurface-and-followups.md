# HANDOFF 2026-08-12 — P4 Spiral Re-Surface Complete; A GPU Leak That Corrupts Experiments Silently

Continue the **CLI experimentation program** (successor to `HANDOFF_2026-08-10_cli-experimentation-f-p4-1-followups.md`). The spiral surface is re-run and published; F-P4-1 is confirmed dead. Every **PR** opened this arc is merged; two cascor **issues** remain open, and the residual work is one scoped re-run plus owner design calls.

## Completed this session (do not redo)

- **F-P4-1 CONFIRMED FIXED.** E-A / E-B / E-C re-run against the fixed stack. Units track the budget (cap 4→4, 8→8, 16→12) where the original campaign recruited **0 units in all twelve E-A cells**; wall scales 246s→2494s; completion is `early_stopped` / `max_iterations`, never `below_threshold`.
- **Evidence note MERGED** (ml#1070): [`notes/JUNIPER_2026-08-12_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-SPIRAL-RESURFACE-EVIDENCE.md`](../../notes/JUNIPER_2026-08-12_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-SPIRAL-RESURFACE-EVIDENCE.md) — tables (E-A 12/12, E-B 6/6, E-C 8/8, all `oom == 0`), findings F-1..F-7, follow-ups R-1..R-6.
- **Two NEW defects found, both SILENT** (run reports `outcome: succeeded`, exit 0, carrying wrong numbers):
  - **GPU leak — juniper-cascor#509 (OPEN issue).** Candidate forkserver children survive teardown holding CUDA contexts, ~285 MiB/cell on an 8 GiB card. Once full, `CandidateUnit.__init__` dies `CUDA error: out of memory`, every candidate is discarded, and the run reports `no_candidate` / 1 unit / chance accuracy — **the same shape F-P4-1 wore**. Measured (recorded in #509): 63 GPU procs, 180 MiB free of 8192.
  - **Stall window — FIXED, ml#1069 (MERGED).** The driver's 120s `--stall-seconds` default (`run_experiment.py:123`) could not be overridden by a suite before #1069. No `current_epoch` progress is reported while the candidate pool trains, so the **pool-16 cells (c002/c005/c008)** were killed as `stalled` / 0 units; given room they complete in **513-1258s**. (c011, pool 32, was only ever run with the window already widened — 2494s.) Added `execution.stall_seconds` beside `per_run_timeout_seconds`.
- **§6 of the evidence note was CORRECTED in this same PR.** An earlier revision claimed the original P4 evidence was contaminated and overstated its E-B ranking / E-C moon dip. **That was wrong and is retracted**: the original records xor 0.9600 and circles 0.9650 at 2 units and moon-n20 0.9650 with the prose "dipping to 0.965 at 0.20" — it **agrees with the clean re-run**, and the contaminated values were this arc's own first-pass re-runs. New §6.1 enumerates the deltas that *are* real: the original has moon/gaussian/checkerboard at **1** unit where this re-run recruits **2**, with accuracy moving both ways (gaussian −0.006, checkerboard −0.025). Two custom agents caught this during handoff validation; see "Validation lesson" below.
- **Also merged**: ml#1060 (isolated-stack marker atomicity — the ml#1045 flake, root-caused as `.partial`+`mv` publication), ml#1061 (launcher dead-process fast-fail), ml#1063 (launcher `DEFAULT_MODEL` derived from the script so a model switch is never a red build), cascor#504.
- **Campaign tooling** under `util/ad-hoc/2026-08-10_{p4_spiral_resurface_campaign.bash,ea_finish_cells.bash,ea_aggregate_clean.py,driver_stall_shim.py,spiral_correlation_threshold_diagnostic.yaml}`, each with a retirement condition in its header. (`2026-08-10_ruleset_context_audit.py` shares the date prefix but belongs to a different arc.)

## Remaining work (priority order)

All code work: **use a worktree, open a PR, never self-merge**, and `gh pr list` dup-guard first (concurrent sessions run on this repo).

1. **R-2 — scoped re-run only.** Of the remaining P4 suites, **only `util/experiments/suites/p4/e-h-real-data.yaml` is `app: cascor`**; E-D / E-E / E-F / E-G and `e-h-recurrence-real-data.yaml` are `app: recurrence`, emit no `logs/juniper-cascor.log`, and are not implicated by cascor#509 (a cascor-path defect). Re-run the cascor leg under the `oom == 0` screen; leave the recurrence suites as published unless a recurrence-side mechanism is found. **The tooling is E-A-shaped**: `2026-08-10_ea_finish_cells.bash` needs `JUNIPER_SUITE_YAML=<suite>` plus explicit cell ids, and `2026-08-10_ea_aggregate_clean.py` is hard-scoped to `e-a-cascor-budget-sweep-*` with a fixed 12-cell expectation — generalize it before use.
2. **R-3 — raise `max_iterations` with the unit cap** in any future E-A. Cascade installs one unit per iteration against `max_iterations: 12`, so cap-16 and cap-32 are *the same experiment* — they returned bit-identical results (c006≡c009, c007≡c010).
3. **R-4 — give E-C's spiral rows an E-A-class budget, or make E-C moon-only.** At a 2-unit cap the spiral noise curve is flat because the cap binds, not the noise.
4. **R-5 — investigate the service-vs-CLI spiral accuracy gap.** Best cell 0.670 val vs ≈0.995 for the direct CLI at radius-10. Budget ceiling, scale/parameterisation difference, or a real service-path limit — open.
5. **R-6 — adopt `execution.stall_seconds` in `util/experiments/suites/p4/*.yaml`** and delete `util/ad-hoc/2026-08-10_driver_stall_shim.py`.
6. **cascor#509 / #505** — owner's call. For #509 the standalone-valuable half: a run that installed zero candidates because of allocation failures **must not report `succeeded`**.

**Owner items carried unchanged** from the predecessor handoff: Q-6 (log-dir override retires H-7, unlocks cascor-parallel `run_suite`); F-P1-2 (`:3000` Grafana squatter); §12 PF threshold ratification + F-P1-3b profiling lane; W-12/Q-7 (`csv_import` corpus); Q-8/Q-10 (perf-baselines home; recurrence conda env); JR-REC ingest at the next requirements-snapshot refresh.

## Key context

- **Never trust a cascor cell without checking OOM.** `grep -c "out of memory" <run_dir>/logs/juniper-cascor.log` before treating any row as data. Contamination is not always a collapse — E-A c010 kept all 12 units and quietly lost 0.06 accuracy.
- Suspect contamination when: several cells share a `best corr` to six significant figures; `no_candidate` at 1 unit; implausibly fast wall time; **results degrade with position in a campaign** (early suites fine, late suites degenerate).
- **Reap before every cell** (`util/reap_pytest_orphans.bash`), not once per suite — the card refills after 4-5 healthy cells.
- cascor is **one-per-checkout** (H-7): never run two suites concurrently.
- Campaign env: `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`, `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- `CUDA_VISIBLE_DEVICES=` removes the GPU confound, but CPU training is slow enough that the 120s stall detector fires almost immediately — raise `stall_seconds` if going CPU-only.
- Healthy E-A cells take **246-2494s**, so batches exceed a 10-minute harness timeout: launch detached (`nohup … & disown`) and poll the log.
- **Validation lesson (cost: a wrong claim in a merged doc).** The retracted §6 came from comparing this arc's contaminated first pass against its own clean re-run and attributing the delta to a prior document **without opening it**. Any claim that prior evidence is wrong must quote that evidence directly.

## Verification commands

```bash
gh issue view 509 --repo pcalnon/juniper-cascor --json state -q '.state'   # OPEN (GPU leak)
gh issue view 505 --repo pcalnon/juniper-cascor --json state -q '.state'   # OPEN
gh pr list --repo pcalnon/juniper-ml --state open                          # empty for this arc
grep -c "stall_seconds" util/experiments/run_suite.py                      # 9 (ml#1069 landed)
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py                       # "clean cells: 12/12"
grep -nE "app: (cascor|recurrence)" util/experiments/suites/p4/*.yaml       # R-2 scoping
nvidia-smi --query-gpu=memory.free --format=csv                            # before any campaign
```

## Git state at handoff

**Do not trust a SHA in this section — re-derive it.** Concurrent sessions push docs straight to `main`; during this handoff's own validation, `main` moved from `c90584c` to `e33f842` (a +46/-45 reformat of the evidence note by the owner) and a draft was nearly committed on the stale blob, which would have silently reverted it. Always:

```bash
git fetch --prune && git log --oneline HEAD..origin/main    # must be empty before you commit
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor fetch && git -C ... status -sb
```

- `juniper-ml`: this arc's commits (ml#1055/#1060/#1061/#1063/#1069/#1070) are all ancestors of `main` and GitHub-signed (`verified: true`). At handoff `origin/main` was `e33f842`.
- `juniper-cascor`: at handoff `origin/main` was `ed7c590` and the primary checkout was in sync. `e1e2e38` is only the #504 merge commit (3 behind `ed7c590`) — it appears in §3 of the evidence note as the sha the campaign *ran* at, which is historical, not current.
- No open PRs in juniper-ml. **None of this arc's branches** (`docs/p4-spiral-resurface-evidence`, `feat/run-suite-stall-seconds`, `fix/f-p4-1-stage-spiral-driver`) remain on the remote; stale local `origin/*` tracking refs for them clear with `git fetch --prune`. The surviving `arc/canopy-e2e-phase1*` branches belong to the canopy E2E arc, and `tmp/resign-1070` is checked out in another worktree.
- Session worktree detached at main; tree clean apart from this handoff and the §6 correction, which land together.
- Environment attested: 0 listeners on both experiment port ranges, 0 lockdirs, orphans reaped.
