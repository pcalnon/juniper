# HANDOFF 2026-07-31 — CLI Experimentation Program: continue with Wave 2.7 (operator docs), then P1 smoke

Continue executing the CLI test/validation/experimentation program for juniper-cascor + juniper-recurrence (plan of record: `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`; owner ratified all Q-1..Q-12).

## Completed so far

- Waves 0, 1.1-1.4, 2.1-2.5 + plan erratum + handoff archives: ALL MERGED (ml#868/#875/#876/#878/#879/#881/#882/#885/#886/#889/#890, deploy#165/#166/#167).
- Wave 2.6 (this session): `util/experiments/stats_summary.py` (§8.3 `stats.json` + `summary.md`, stdlib-only, every outcome) + `_emit_stats` wiring (92 tests) — **PR ml#893 OPEN** (branch `feature/experiment-driver-stats-summary`); verify its CI/merge state first.

## Remaining next steps (dependency order)

1. **Wave 2.7** (after ml#893 merges; the LAST Wave-2 item): `docs/REFERENCE.md` operator section + `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` entries for the experiment tooling. Model on the existing "Isolated Stack E2E" REFERENCE.md section: `util/experiment_stack.bash` (actions, port ranges 8110-8139/8230-8259/8260-8289, RUN_DIR contract under `~/.local/state/juniper-experiments`, `JUNIPER_EXP_*` env overrides, F-6 pidfile rule, opt-in `--grafana-bridge`, teardown semantics) + `util/experiments/run_experiment.py` (CLI flags, YAML §5.4/§5.5 blocks, exit codes 0-4, per-kind plots, stats/summary, manifest). Cross-link the §6.4 RUN_DIR artifact map. Docs-only PR — remember `juniper-check-doc-links` runs in pre-commit (relative links must resolve) and REFERENCE.md/cheatsheet are markdownlint-EXCLUDED (docs/ excluded) but keep the 512 habit anyway.
2. **P1 smoke** (§10.2, plan Wave 6.1 — live, operator-style): bring up a run with `util/experiment_stack.bash --up --cascor [--grafana-bridge]`, drive P1.1 (spiral, `max_hidden_units: 2, max_iterations: 2, max_epochs: 50`, plots [dataset, decision_boundary, training_history]), P1.3 (recurrence irregular_sine `d: 8, n_steps: 500, readout: linear`, crossval n_folds 2), P1.5 `--dry-run` arms, P1.6 the Wave-1.4 `juniper-experiments` dashboard live-render check (needs `make obs` in juniper-deploy + `--grafana-bridge`), P1.7 teardown attest (ports free, pidfiles gone, target file removed). Environments: launcher uses direct env-bin paths (`JUNIPER_EXP_CONDA_DIR`); driver runs fine from system python3 (stdlib+yaml; numpy/matplotlib for npz+plots — use JuniperData env python if system lacks them). File the evidence as a notes/ doc (`JUNIPER_<date>_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md`) mirroring the P0 evidence doc; fold any errata back into the plan.
3. Then Waves 3+ (YAML config layer in the app repos; launcher `--config` staged-inert until 3.1/3.3) / Wave 4 dataset enablement (W-1 silent-drop fix is the highest-value correctness item) per §14.

## Key context

- **Read the memory file first**: `project_cascor_recurrence_cli_experimentation_plan.md` — Waves 2.2-2.6 paragraphs carry every implementation truth (payload contracts, plots/stats loading seams, skip-vs-fail semantics, budget handling, CLI constraints).
- Headless commits: `git -c commit.gpgsign=false commit`. Owner merges via admin bypass. Verify claimed merges before building on them (`gh pr view N --json state`).
- For P1: operator ports 8100/8200/8201/8210/8050 are never touched; the on-host operator cascor may hold live training state — never restart it casually.
- Owner decision still pending (not urgent): recurrence namespace alignment. Deploy micro-PR candidate still open: `tests/test_provenance_sha.py` gpg fixture.

## Verification for the new thread

```bash
gh pr list --repo pcalnon/juniper-ml --state open
git -C /home/pcalnon/Development/python/Juniper/juniper-ml log --oneline -3 origin/main
python3 -m unittest tests.test_run_experiment   # 92/92 OK expected
```

Git status at handoff: Wave-2.6 work committed + pushed on `feature/experiment-driver-stats-summary` (PR ml#893); this handoff file rides its own docs PR; no other uncommitted changes.
