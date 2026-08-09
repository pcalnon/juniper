# HANDOFF 2026-08-09 — CLI Experimentation Program Wrap-Up (P0–P4 complete)

Continue the **Juniper CLI test/validation/experimentation program** follow-ups. The program itself is COMPLETE — this handoff carries only residual work items and open owner questions.

## Completed so far (do not redo)

- **Entire program plan executed** (`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`): Waves 0–7 (launcher, driver, plots/stats, YAML config layer both apps, W-1…W-11 register, run_suite sequential+parallel, list_runs, PF suites, Q-9 alert scoping, JR-REC proposal) and phases P0–P4.
- Evidence chain in `notes/`: P0 preflight · P1 smoke · P2 dataset matrix (11/11) · P3 acceptance roll-up (9/9 criteria; bit-identical reproducibility; service≡bench parity) · **P4 studies (`…P4-STUDIES-EVIDENCE.md`, 55/55 cells)**.
- P4 headlines: E-E DP-3 capacity separation live in service mode (delay_product linear −0.005 / rff 0.908 / mlp 0.941); E-H dual efficient-market-ceiling checks (CV r² −0.18 seq; 0.528 ≈ 0.532 base-rate tabular); E-D/E-F/E-G curves; E-B/E-C rankings (checkerboard beyond smoke budget; moon noise curve).
- All arc PRs merged (ml #1020–#1045 arc set incl. #1027/#1030/#1031/#1032/#1033/#1034/#1045; cascor #483–#494; recurrence #97–#102; data-client #142; deploy #169/#171). Images rebuilt + provenance-verified (F-P1-1 cleared); buildx cache pruned (306 GB).

## Remaining work (priority order)

1. **F-P4-1 (raised, priority)** — the cascor SERVICE path terminates spiral training at ≈epoch 2 (chance, ≤1 hidden unit) at EVERY budget incl. the 2000-epoch baseline; P1.1 retroactively shows the same signature; direct CLI trains spiral for minutes; staged easy tasks train fine. Suspect: termination semantics at `POST /v1/training/start` (early-stop / convergence-threshold / iteration handling). Investigation base: the 12 E-A cell registries + manifests under `~/.local/state/juniper-experiments/suites/e-a-cascor-budget-sweep-20260809T085929Z/`. E-A/E-B/E-C spiral surfaces are F-P4-1 measurements until fixed.
2. **Launcher fast-fail on dead process during health-wait** (P4 ops finding): `experiment_stack.bash wait_for_health` cannot distinguish slow-boot from crashed-at-import — 180 s waits against a dead uvicorn. Add a liveness probe of the launched process between health polls.
3. **TestCanopyUp cmdline flake**: `tests/test_isolated_stack_script.py:659` asserts `main.py` in a `/proc` cmdline that can read bare `python` mid-exec (bit ml#1045 once; healed by rerun). Poll-until-stable or assert against the stub artifact.
4. **§13.3 deferred half**: `run_experiment.py` does not append `RUN_ROOT/index.jsonl` for standalone runs (only `run_suite` appends); `list_runs` stays scan-based fallback by design — wire the driver append if the shared discovery surface is wanted.
5. **Open juniper-ml#979**: launcher staging-lock gap (failed `--config` staging strands port lockdirs `--down` cannot release; two were hand-cleared this arc after a session restart).
6. **Q-6 (owner)**: `JUNIPER_CASCOR_LOG_DIR`-class override — resolving it retires the one-cascor-instance-per-checkout rule (H-7) AND unlocks `run_suite` cascor-parallel (currently refused at load).
7. **F-P1-2 (owner)**: `:3000` Grafana squatter — full context package + 3 options in the P3 roll-up §3; blocks only live dashboard-render verification (Prometheus lane fully proven). After deciding, verify the experiments dashboard renders (incl. deploy#171's PF Performance row).
8. **§12 perf lane**: PF-1…PF-8 suites are committed and runnable (`util/experiments/suites/perf/`); thresholds need their ratification pass; F-P1-3b (direct-CLI compute-bound profiling) is the lane's first scenario; E-B's difficulty ranking is a standing input.
9. **W-12 / Q-7 (owner, parked)**: `csv_import` corpus definition, then the cascor matrix row.
10. **Q-8 / Q-10 (owner, non-blocking)**: perf-baselines home; dedicated recurrence conda env.
11. **JR-REC block**: proposal merged (ml#1031); ingest at the next requirements snapshot refresh (map interim `JR-RECURRENCE-*` spellings per its §3).

## Key context

- Suite machinery: `run_suite.py --suite … [--resume SUITE_ID] [--only CELL_ID]`; registries append-only last-row-wins; from a worktree set `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`; campaign settings `JUNIPER_EXP_HEALTH_TIMEOUT=180`, study groups sequential (concurrent cascor bring-ups caused the P4 health-timeout class), readout-crossing suites must null non-matching train keys (`rff_*` only with rff; no `ridge` with mlp — service 422s otherwise).
- The 2026-08-09 cascor broken-boot window (`4081f5b` swept 5 snapshot modules with `.h5` debris; healed as cascor#501 by a concurrent session) is fully documented in the P4 evidence §4.
- **Hands-off flag**: the primary `/home/pcalnon/Development/python/Juniper/juniper-ml` checkout's `main` is diverged with the owner's local commit `3fd46da "(support): adding manual prompt…"` — owner's content; do not rebase/push it.
- Sequence-safety soak promotion (~2026-08-21) and the canopy E2E arc are separate arcs with their own memory topics.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git log --oneline -3   # expect P4 evidence + handoff merges at tip
gh pr list --repo pcalnon/juniper-ml --state open                                # expect empty (or only newer concurrent work)
ls ~/.local/state/juniper-experiments/suites/ | wc -l                            # 10 suite dirs (9 studies + superseded e-e first run)
python3 util/experiments/list_runs.py | tail -3                                  # run inventory; no 'up?' rows expected
ss -tlnH 'sport >= :8110 and sport <= :8139'; ss -tlnH 'sport >= :8230 and sport <= :8289'  # both empty
```

## Git state at handoff

All session branches merged and deleted (ml/cascor/recurrence/data-client/deploy); primaries synced to their tips except the owner-diverged juniper-ml main above; no open PRs authored by this session; experiment port ranges, lockdirs, and stale runs all clean.
