# HANDOFF 2026-08-10 — CLI Experimentation Follow-Ups: F-P4-1 Root-Caused + Fixed; Launcher/Test Items In Flight

Continue the **CLI experimentation program residual work** (successor to `HANDOFF_2026-08-09_cli-experimentation-program-wrapup.md`). The headline item — F-P4-1 — is root-caused, fixed, and live-verified this session; two PRs await owner review and three smaller items are mid-flight.

## Completed this session (do not redo)

- **F-P4-1 ROOT-CAUSED** (not termination semantics). Chain: the driver's spiral-only inline `dataset` source made cascor substitute its in-process fallback for the configured juniper-data dataset; the fallback was param-deaf (`n_per_spiral` vs `n_points_per_spiral` → 200 pts, no noise/seed) and **unit-radius** (1/(4π) normalized); at that scale the default candidate init (`randn×0.1`) leaves every tanh candidate in its linear regime, where the output-layer-converged residual is least-squares-orthogonal → best-of-pool correlation pinned ≈2.7e-4 → `grow_network` breaks `below_threshold` at iteration 1 (0 units, chance acc). Same run at radius-10 scale: 12 units, 0.995 acc. Full write-up: [`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md`](../../notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md). Repro committed as cascor `util/ad-hoc/f_p4_1_spiral_service_repro.py`. CUDA-OOM noise excluded by `CUDA_VISIBLE_DEVICES=` control.
- **cascor#504 (OPEN PR)** — fallback `_generate_spiral_data` honors SpiralParams (`n_points_per_spiral`/`n_rotations`/`noise`/`radius`/`seed`, legacy key kept), radius-10 default; 33/33 route tests + pre-commit green.
- **ml#1055 (OPEN PR)** — driver stages spiral like every other generator (inline branch removed from `start_training`; G-6 now covers spiral); 118/118 `tests.test_run_experiment`; AGENTS.md + root-cause note included.
- **cascor#505 (OPEN issue)** — API `candidate_patience`/`candidate_convergence_threshold` never reach the pool (workers hardcode module defaults 50/0.001); fix shape documented in the issue.
- **Live acceptance smoke PASSED** (run `20260810T071512Z-b9d6`, artifacts kept): staged spiral = real juniper-data dataset (eval split `validation` n=200 = the 0.2 split of 1000), **3 hidden units recruited**, acc 0.604 > chance, `completion_reason: max_iterations`, `g6_shape_check` ok. Stack torn down; both port ranges clear.
- **§13.3 deferred half ASSESSED — keep deferred**: driver `index.jsonl` append would be write-only (no consumer; `list_runs` scan-based by design) and needs an out-of-RUN_ROOT `--run-dir` guard. Report-only; no code.
- **#979 RECONCILED**: the staging-lock gap was FIXED by merged PR juniper-ml#979 (2026-08-07; `release_held_locks` on `create_run_dir`/`stage_config`/`write_ports_json` failure — verified present in `util/experiment_stack.bash:830-845`). The prior handoff's item 5 and AGENTS.md's "**Staging lock gap (open #979)**" bullet (~line 499) are **stale**; the doc correction is still uncommitted (below).

## Remaining work (priority order)

1. **TestCanopyUp marker-race fix — finish + PR**: root cause found (`tests/test_isolated_stack_script.py::_read_marker_when_written` returns on the stub's first `printf` — bare `python` — before argv lands; ml#1045's flake). Fix written (require newline-terminated complete record) in worktree `worktrees/juniper-ml--fix--exp-launcher-followups--20260810-0230--2d5ad285`, branch `fix/canopy-up-marker-race`, **UNCOMMITTED**. Module then passed 5 of 7 runs with ONE unidentified intermittent failure whose test name was never captured (hunt interrupted). Before committing: loop `python3 -m unittest tests.test_isolated_stack_script >log 2>&1` until failure, name the test, decide pre-existing vs introduced, then commit + PR.
2. **Launcher dead-process fast-fail (designed, not implemented)**: `wait_for_health` (`util/experiment_stack.bash:346`) gains optional `liveness_pattern` arg; between curl polls run `pgrep -f -- "$pattern"`, two consecutive misses → log + `return 1`. Callers pass per-service patterns (data `-m juniper_data.*--port ${DATA_PORT}`; cascor `api.app:create_app.*--port ${CASCOR_PORT}`; recurrence its serve line + port). F-6 stays intact (no `$!`, liveness only — never used to kill). Hermetic arms in `tests/test_experiment_stack_script.py` w/ a `pgrep` PATH stub: dead-fast-fail, slow-boot-continues, no-pattern back-compat, launch-line contract.
3. **AGENTS.md #979 staleness correction** (small docs PR): rewrite the "Staging lock gap (open #979)" bullet as fixed-by-#979, keep the leftover-lockdir cleanup guidance.
4. **PR shepherding**: cascor#504 + ml#1055 are owner-gated (never self-merge; headless-merge policy). After merges: V2 worktree cleanups for `juniper-cascor--fix--f-p4-1-service-spiral-termination--20260809-1930--d8ae2f97`, the session worktree branch `fix/f-p4-1-stage-spiral-driver`, and the follow-ups worktree.
5. **Spiral-surface re-runs (owner-scheduled)**: E-A grid + E-B/E-C spiral rows remain F-P4-1 measurements until re-run against the fixed stack; real spiral cells train minutes each (E-A full budget ≈ 18 min for 200 pts in-process; the 800-pt staged dataset is longer). P1.1 reference metrics describe the fallback dataset (mechanics remain valid).
6. **cascor#505 implementation** if owner wants it (multiprocessing task-format blast radius; CASCOR-P0-005 key-name class — needs construct-level tests).
7. **Owner items carried unchanged**: Q-6 (log-dir override retires H-7, unlocks cascor-parallel `run_suite`); F-P1-2 (`:3000` Grafana squatter; options in P3 roll-up §3); §12 PF threshold ratification + F-P1-3b profiling lane; W-12/Q-7 (`csv_import` corpus); Q-8/Q-10 (perf-baselines home; recurrence conda env); JR-REC ingest at the next requirements-snapshot refresh.

## Key context

- **Hands-off flag (unchanged)**: primary `/home/pcalnon/Development/python/Juniper/juniper-ml` main is owner-diverged (`3fd46da`); never rebase/push it. Work from worktrees.
- ml#1055's new test contract: staging POST carries `dataset_type: "spirals"` + params, start body has **no** `dataset` key, `g6_shape_check` populated.
- ml origin/main moved past the session base (concurrent arcs; `bfdfb3b`+); both open PRs merge independently.
- Campaign settings still apply for any re-runs: `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`, `JUNIPER_EXP_HEALTH_TIMEOUT=180`, study groups sequential, readout-crossing suites null non-matching train keys.

## Verification commands

```bash
gh pr view 504 --repo pcalnon/juniper-cascor --json state,title -q '.state'    # OPEN until owner merges
gh pr view 1055 --repo pcalnon/juniper-ml --json state,title -q '.state'       # OPEN until owner merges
gh issue view 505 --repo pcalnon/juniper-cascor --json state -q '.state'       # OPEN
python3 -m json.tool ~/.local/state/juniper-experiments/20260810T071512Z-b9d6/artifacts/results/metrics_final.json | head -8   # hidden_units: 3
git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--fix--exp-launcher-followups--20260810-0230--2d5ad285 status --short   # marker-race fix, uncommitted
ss -tlnH 'sport >= :8110 and sport <= :8139'; ss -tlnH 'sport >= :8230 and sport <= :8289'   # both empty
```

## Git state at handoff

- `juniper-ml` session worktree (`.claude/worktrees/silly-snuggling-ullman`): branch `fix/f-p4-1-stage-spiral-driver`, clean, pushed, PR ml#1055 open.
- `worktrees/juniper-cascor--fix--f-p4-1-service-spiral-termination--20260809-1930--d8ae2f97`: branch `fix/f-p4-1-service-spiral-termination`, clean, pushed, PR cascor#504 open.
- `worktrees/juniper-ml--fix--exp-launcher-followups--20260810-0230--2d5ad285`: branch `fix/canopy-up-marker-race`, **dirty** — the uncommitted marker-race fix in `tests/test_isolated_stack_script.py` (sole uncommitted state in the arc).
- No other session branches; experiment port ranges and lockdirs clean; smoke-run artifacts retained at `~/.local/state/juniper-experiments/20260810T071512Z-b9d6/`.
