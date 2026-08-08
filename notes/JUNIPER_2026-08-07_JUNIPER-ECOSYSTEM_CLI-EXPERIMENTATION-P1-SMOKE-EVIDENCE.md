# CLI Experimentation P1 Smoke — Evidence (§10.2, plan Wave 6.1)

**Project**: Juniper — CLI test/validation/experimentation program
**Author**: Paul Calnon (executed by Claude Code)
**Date**: 2026-08-07
**Plan of record**: [`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §10.2
**Predecessor**: [`JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md`](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md)
**Tooling under test**: `util/experiment_stack.bash` (Wave 2.1) + `util/experiments/run_experiment.py` (Waves 2.2–2.6), both at main `6609fcc`+ (post ml#909/#911 docs)

---

## 1. Results

| Step | Verdict | Evidence |
| --- | --- | --- |
| P1.5 dry-runs | **PASS** | `--dry-run --up --cascor` and `--dry-run --up --recurrence --grafana-bridge` both exit 0; run root + lock root listings byte-identical before/after; no target file written |
| P1.1 cascor **service** | **PASS** | RUN `20260807T195013Z-32d8` (data 8110 / cascor 8230): driver exit **0**, FSM `COMPLETED` (`completion_reason=below_threshold`) in 24.2 s / 13 polls / 0 sampling errors; `dataset_id=spiral-1.0.0-f98fd84bccbfe1dd`; 3 plots (`dataset`, `decision_boundary`, `training_history`) all valid PNG; `metrics_series.csv` 13 rows with real per-round correlation (0.0 @ 0 units → 0.0144 @ 1 unit); `stats.json` step-duration p50 0.0132 s / p95 0.336 s; manifest `acceptance.ok=true`, `stats_error=null` |
| P1.2 cascor **direct CLI** — exit arms | **PASS** | `JUNIPER_DATA_URL` unset → exit **3**; dead data port → exit **4** (exactly the §6.1 documented contract) |
| P1.2 cascor **direct CLI** — full run | **PARTIAL** (finding F-P1-3) | Launch + dataset fetch + live training demonstrated (26 k log lines, candidate training progressing, snapshots written); killed at the smoke's 480 s bound (exit 124) — the direct CLI exposes **no budget flags** (profiling only), so a smoke-scale completion is structurally unreachable until **W-11** (Wave 3.6) maps the experiment `training:` block onto it |
| P1.3 recurrence **service** | **PASS** | RUN `20260807T195239Z-0610` (data **8111** / recurrence 8260): driver exit **0** in 4.8 s; synchronous train 0.275 s, `stopped_reason=converged`, train r² **0.9907**; predict shape `[87, 1]`; 2-fold CV aggregate r² **0.9874**; `dataset_id=irregular_sine-1.0.0-a0cd2c54c7aa8fc1`; all 5 plots (`dataset_overview`, `dt_histogram`, `forecast_vs_truth`, `residuals`, `crossval_folds`) valid PNG; θ recorded data-driven |
| P1.4 recurrence **train CLI** | **PASS** | `juniper-recurrence train --generator irregular_sine … --out model.npz` exit **0** against the live 8111 data instance; metrics printed (r² **0.9888** — consistent with service mode, the §10.4 comparability signal); `model.npz` loadable (`meta`, `readout__coef`) |
| P1.6 dashboards | **PASS (datasource layer)** / owner follow-up (render) | Both runs' `juniper-host-experiments` targets **`up`** in Prometheus with scrape-side `run_id`/`experiment`/`service` labels; run-scoped instant queries return series (`juniper_cascor_training_loss{run_id=…}` = 0.2405; `juniper_recurrence_build_info{run_id=…}` present); `juniper-experiments.json` + `juniper-recurrence.json` provisioned in juniper-deploy. Interactive panel render blocked by findings F-P1-1/F-P1-2 (below) — the panels' underlying queries are exactly the series proven present |
| P1.7 teardown | **PASS** | Both `--down` exit 0; all three ranges (8110–8139 / 8230–8259 / 8260–8289) **0 listeners**; both Prometheus target files removed; socat relays gone; per-run pidfiles removed; `teardown.json` written; **`artifacts/` preserved** (3 + 5 plots); `JuniperProject.pid` **absent before and after** (H-10 holds) |

Bonus observations:

- **Isolation (a §10.4 criterion, observed live)**: the second run's port allocator correctly skipped the busy 8110 and took **8111** while both runs were concurrently up; both runs completed independently with distinct RUN_DIRs and both were visible in Prometheus simultaneously.
- **F-2 holds post-merge**: the launcher discovered the monitoring gateway `172.31.0.1` by `_monitoring$` suffix and both relays bound it.

## 2. Findings

| ID | Finding | Consequence / follow-up |
| --- | --- | --- |
| **F-P1-1** | `make obs` is now refused by the image-provenance preflight (deploy#150-152 guard family): `juniper-cascor:latest` is 10 commits behind its checkout. P1 instead started **only** the Prometheus container (`docker compose --profile monitoring up -d --no-deps prometheus`), which is sufficient for the scrape path. | Operator: `make build` in juniper-deploy (or `JUNIPER_IMAGE_STALE_OK=1`) before the next full `make obs`. The targeted-prometheus form is a useful minimal recipe for experiment-only sessions. |
| **F-P1-2** | A **native (non-docker) Grafana v13.0.1 now owns `:3000`** on this host (401 for anonymous and default creds) — environment drift since P0 (2026-07-30), when the containerized stack ran. Deploy's grafana container cannot bind. | Owner: stop/relocate the native Grafana or remap deploy's grafana host port, then eyeball the `juniper-experiments` dashboard once during a live run (the remaining interactive half of P1.6). Datasource-level evidence in §1 already proves the panels' queries return data. |
| **F-P1-3** | The cascor **direct CLI** (`src/main.py`) exposes only profiling flags — no budget knobs — so P1.2's "exit 0 + plots" is unreachable at smoke scale under constants defaults (killed at 480 s mid-candidate-training). | Expected-by-design gap: **W-11 (Wave 3.6)** maps the experiment `training:`/`dataset:` blocks onto the direct CLI. P1.2's full-completion row re-runs after W-11; the exit-code arms and launch path are proven now. |
| **F-P1-4** | H-4/H-5 as designed: the smoke left 4 snapshot `.h5` files in `juniper-cascor/src/cascor_snapshots/` (the hard-coded snapshot dirs). Files left in place for the owner. | **W-6** (`JUNIPER_CASCOR_SNAPSHOTS_DIR`, Wave 5.1) redirects these into `RUN_DIR/snapshots/`; until then the one-instance-per-checkout rule stands. |

## 3. Environment restoration

- Prometheus container stopped after the smoke; compose networks removed; **0 containers** running (the pre-P1 state).
- Both RUN_DIRs preserved under `~/.local/state/juniper-experiments/` (`20260807T195013Z-32d8`, `20260807T195239Z-0610`) with full artifacts (plots, results, stats, manifests) for owner inspection.
- The temporary `p1-smoke-*` experiment YAMLs lived in the session scratchpad (not the repo); their exact content is reproducible from §1's parameters and the run dirs' `config/experiment.yaml` copies.

## 4. Disposition

**P1 smoke: PASS** for every arm the current wave-set can reach (P1.1, P1.2-exit-arms, P1.3, P1.4, P1.5, P1.6-datasource, P1.7), with the two remaining halves — P1.2 full completion and P1.6 interactive render — blocked on **W-11** and the **F-P1-2 owner follow-up** respectively, not on the program tooling. The program may proceed to Waves 3+ (YAML config layer) and Wave 4 dataset enablement (W-1 first) per §14.
