# HANDOFF 2026-07-31 — CLI Experimentation Program: continue with Wave 2.6 (stats.json + summary.md renderers)

Continue executing the CLI test/validation/experimentation program for juniper-cascor + juniper-recurrence (plan of record: `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`; owner ratified all Q-1..Q-12).

## Completed so far

- Waves 0, 1.1-1.4, 2.1-2.4 + plan erratum + handoff archives: ALL MERGED (ml#868/#875/#876/#878/#879/#881/#882/#885/#886, deploy#165/#166/#167).
- Wave 2.5 (this session): `util/experiments/plots_recurrence.py` (§8.2 set, closes G-5) + driver wiring + sequence-NPZ test artifact (86 tests) — **PR ml#889 OPEN** (branch `feature/experiment-driver-recurrence-plots`); verify its CI/merge state first.

## Remaining next steps (dependency order)

1. **Wave 2.6** (after ml#889 merges): `artifacts/results/stats.json` + a human-readable `summary.md` per §8.3, rendered by the driver at the end of every run (both kinds). §8.3 blocks: **Identity** (run_id, experiment name, config SHA-256, git SHAs, package versions, seeds — all already in the manifest), **Dataset** (dataset_id, generator+version, params, resolved shapes: `n_windows`/`lookback`/`n_features` for 3-D vs `n_train`/`n_test`/`n_features`/`n_classes` for 2-D, class balance from meta `class_distribution` or target summary stats), **Outcome** (terminal state, wall-clock, per-phase timings), **cascor** (final loss/accuracy train+test, F1/precision/recall/ROC-AUC when present, hidden units added, best candidate correlation per round + `training_step_duration` p50/p95 — BOTH from the driver's `metrics_series.csv`, neither exists in `/v1/metrics/history` rows), **recurrence** (`final_metrics`, `n_epochs`, `stopped_reason`, per-fold + aggregate CV, resolved θ note, readout rung), **Provenance/health** (metrics_scraped, degraded-mode notes — sampling errors, collect_errors, plot skips). Most inputs are already assembled for the manifest — factor a shared builder rather than re-fetching; p50/p95 need a tiny percentile helper over the series CSV step-duration columns (sum/count deltas per poll).
2. Wave 2.7: `docs/REFERENCE.md` operator section + `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` entries for `experiment_stack.bash` + `run_experiment.py` (mirror the isolated-stack section's shape).
3. P1 smoke (§10.2) via the launcher — P1.1 cascor spiral (`max_hidden_units: 2, max_iterations: 2, max_epochs: 50`), P1.3 recurrence irregular_sine (`d: 8, n_steps: 500, readout: linear`), P1.5 `--dry-run` arms, P1.6 the Wave-1.4 dashboard live-render check (needs `--grafana-bridge`), P1.7 teardown attest — file evidence in `notes/`. Then Waves 3+ (YAML config layer; launcher `--config` staged-inert until 3.1/3.3).

## Key context

- **Read the memory file first**: `project_cascor_recurrence_cli_experimentation_plan.md` — Waves 2.2-2.5 paragraphs carry the implementation truths (payload contracts, sequence-NPZ keys, `y_reg_` preference, plots-module loading, skip-vs-fail semantics, `RequestTimeout` budget, no-`--params` CLI constraint).
- Driver test idiom: scripted stub `http.server`; `state.artifact_kind` tabular/sequence NPZ artifacts; `RedactedEnv` subprocess arms; PNG-magic assertions.
- Headless commits: `git -c commit.gpgsign=false commit`. Owner merges via admin bypass (unsigned commits sit OPEN/BLOCKED under `required_signatures`).
- CI test job installs pyyaml/packaging/numpy/matplotlib — no new deps expected for 2.6.
- Owner decision still pending (not urgent): recurrence namespace alignment. Deploy micro-PR candidate still open: `tests/test_provenance_sha.py` gpg fixture.

## Verification for the new thread

```bash
gh pr list --repo pcalnon/juniper-ml --state open
git -C /home/pcalnon/Development/python/Juniper/juniper-ml log --oneline -3 origin/main
python3 -m unittest tests.test_run_experiment   # 86/86 OK expected
```

Git status at handoff: Wave-2.5 work committed + pushed on `feature/experiment-driver-recurrence-plots` (PR ml#889); this handoff file rides its own docs PR; no other uncommitted changes.
