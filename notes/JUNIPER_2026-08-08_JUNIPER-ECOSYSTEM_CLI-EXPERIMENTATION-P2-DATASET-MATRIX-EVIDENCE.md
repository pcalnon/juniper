# CLI Experimentation — P2 Dataset-Matrix Evidence

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Sub-Project**: CLI test / validation / experimentation program (plan §10.3)
**Author**: Paul Calnon
**Date**: 2026-08-08
**Status**: EXECUTED — all runnable matrix rows PASS (11/11 first-try)
**Plan of record**: [JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §10.3
**Prior evidence**: [P0 preflight](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md) · [P1 smoke](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md)

---

## 1. Scope

P2 runs the smallest meaningful configuration for **every compatible dataset, per app, in service mode** (§10.3), after the Wave-4 register unblocked the last rows (W-3 staged gaussian/checkerboard, W-5 `ar_p`). Eleven rows executed this session; two more were already live-proven in P1 (`spiral` P1.1, `irregular_sine` P1.3). Deferred rows, per the plan: `mnist` (host `available=false` → 501; install path now documented in `docs/REFERENCE.md` § Generator Availability Matrix — the W-4 docs half), `csv_import` (Q-7/W-12: no experiment corpus defined), `arc_agi` (not a cascade-correlation target for this program).

## 2. Method

- **Stack**: one per-run experiment stack, `RUN_ID=20260808T142719Z-0145` (`util/experiment_stack.bash --up --cascor --recurrence --grafana-bridge --experiment p2-matrix`): juniper-data :8110 (`JuniperData` env), cascor :8230 + recurrence :8260 (`JuniperCascor1`), socat relays on the monitoring gateway 172.31.0.1 + the §7.2 file_sd target file. Prometheus ran as the **targeted single container** (`docker compose --profile monitoring up -d --no-deps prometheus` from juniper-deploy — the F-P1-1 stale-image workaround).
- **Per-dataset isolation on one stack**: each row ran `util/experiments/run_experiment.py --config <yaml> --run-dir $RUN_DIR/p2/<row>` against a **per-row run-dir subdirectory** holding a copied `ports.json` — manifests, plots, and results stay separate while sharing the live services. Cascor rows rely on the driver default `start_fresh: true`; every non-spiral cascor row goes through the G-6 staging path (`POST /v1/training/dataset`) with the post-run shape assert.
- **Configs**: seed `20260808` throughout (`experiment.seed` = `dataset.params.seed`); cascor rows use the xor-staged reference budget (`max_epochs 200 / max_iterations 4 / max_hidden_units 6 / candidate_pool_size 4`), recurrence rows the irregular-sine-smoke shape (`ridge 1.0`, 2-fold expanding CV, predict from `test`). Each row's exact YAML is preserved at `$RUN_DIR/p2/<row>/config.yaml` (durable under `~/.local/state/juniper-experiments/`, H-15). `dataset.params` use **juniper-data param names verbatim** — the driver's stage body is `{dataset_type, params}` and the generic `params` dict is forwarded verbatim (typed-field translation is the other, unit-tested path).

## 3. Results — 11/11 PASS, first try

| Row | Kind | Exit | Outcome | Plots (req/ok/skip) | NPZ contract | G-6 | `dataset_id` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `p2-xor` | cascor staged | 0 | succeeded | 3/3/0 | `tabular` | OK | `xor-1.0.0-e700406e` |
| `p2-circles` | cascor staged | 0 | succeeded | 3/3/0 | `tabular` | OK | `circles-1.0.0-290fdc5a` |
| `p2-moon` | cascor staged | 0 | succeeded | 3/3/0 | `tabular` | OK | `moon-1.0.0-2353c687` |
| `p2-gaussian` | cascor staged (W-3 row) | 0 | succeeded | 3/3/0 | `tabular` | OK | `gaussian-1.0.0-502adc53` |
| `p2-checkerboard` | cascor staged (W-3 row) | 0 | succeeded | 3/3/0 | `tabular` | OK | `checkerboard-1.0.0-061fe8fe` |
| `p2-equities` | cascor staged, networked | 0 | succeeded | 1/1/0 | `tabular` | OK | `equities-1.0.0-f37f16f3` |
| `p2-multi-sine` | recurrence | 0 | succeeded | 5/5/0 | `sequence` | n/a | `multi_sine-1.0.0-d21bd418` |
| `p2-mackey-glass` | recurrence | 0 | succeeded | 5/5/0 | `sequence` | n/a | `mackey_glass-1.0.0-5bed318e` |
| `p2-delay-product` | recurrence (rff readout) | 0 | succeeded | 5/5/0 | `sequence` | n/a | `delay_product-1.0.0-9d01ba84` |
| `p2-ar-p` | recurrence (W-5 row) | 0 | succeeded | 5/5/0 | `sequence` | n/a | `ar_p-1.0.0-a37b642c` |
| `p2-equities-seq` | recurrence, networked | 0 | succeeded | 5/5/0 | `sequence` | n/a | `equities_seq-1.0.0-8c12baca` |

Cascor plot set: `dataset` + `decision_boundary` + `training_history` (equities plot-reduced to `training_history` — F=10, boundary and 2-feature scatter structurally inapplicable, requested set trimmed rather than SKIP-recorded). Recurrence plot set: `dataset_overview` + `dt_histogram` + `forecast_vs_truth` + `residuals` + `crossval_folds`.

## 4. Acceptance evidence (§10.3 per-dataset criteria)

- **Run completes**: exit 0 / `outcome: succeeded` / `acceptance: true` in all 11 manifests (schema `juniper-experiment-manifest/1`, `driver.wave 2.6`).
- **NPZ contract**: each row's artifact fetched from `GET /v1/datasets/{id}/artifact` and passed through `juniper_data_client.validate_npz_contract` → `"tabular"` for all 6 cascor rows, `"sequence"` for all 5 recurrence rows (11/11).
- **Plots non-degenerate**: every requested plot rendered (renderers raise `ValueError` on no-renderable-data, so rendered ⇒ non-empty/finite); 0 skips across the campaign.
- **Prometheus labels**: `up{run_id="20260808T142719Z-0145"} == 1` for all three services with `experiment="p2-matrix"`, and app families (e.g. `juniper_cascor_hidden_units_total`) carry the same labels. (Labels are per-stack: one `run_id` for the campaign; per-row identity lives in the manifests/tags.)
- **Manifest records**: `dataset_id`, full resolved dataset meta, and seeds present in every manifest. Dims spot-checks: gaussian `n_features=2, n_classes=3, class_distribution {0:300, 1:300, 2:300}` (per-class params verbatim — exactly as requested); checkerboard `n_features=2, n_samples=2000, n_squares=4`; equities `n_features=10, n_samples=504` (real AAPL 2020–2022 trading days); xor `n_features=2, n_samples=1000`.
- **G-6 anti-silence**: `g6_shape_check` present and OK on all 6 staged cascor rows; absent (by design) on recurrence rows.

Timings: recurrence rows 1.7–6.5 s total (equities_seq dominated by the 3.0 s networked generation); cascor rows tens of seconds at the reference budget.

## 5. Observations (no adverse findings)

1. **Zero re-runs.** All 11 rows passed on the first invocation — the Wave-2 driver, W-1/W-3 staging surface, and W-11-era config layer composed without friction.
2. **Verbatim-params staging is now live-proven** alongside the unit-tested typed-field path: the driver forwards `dataset.params` verbatim (generic `params` wins), so W-3's `n_samples → n_samples_per_class` translation is bypassed when callers speak juniper-data's own param names — both entry shapes are covered.
3. `equities` defaults (`regression_target: next_close`, `task_type: classification` with the direction label) are what the tabular cascor row trains on; the recurrence row overrides to `log_return` per the recurrence#28 doctrine. Both behaved.
4. The networked rows (`equities`, `equities_seq`) fetched live Yahoo data without retries this session.

## 6. Teardown attestation (H-10)

`--down 20260808T142719Z-0145`: services + relays stopped (pidfile path; port fallback exercised only for the data relay), port locks released, the Prometheus target file removed (`targets/` back to `.gitkeep`), `teardown.json` written, **artifacts preserved**. Post-teardown: `ss` shows 0 listeners in 8110–8139 and 8230–8289; the targeted Prometheus container stopped and removed; 0 containers running.

## 7. Program state after P2

P0 ✓ · P1 ✓ (F-P1-3b CLI-path completion open as a §12 perf item) · Wave 4 register ✓ (W-1/2/3/5/8/9/10/11 + W-4 docs) · **P2 ✓ (this document)**. The §10.4 P3 criteria are substantially evidenced by P1 (spiral reference run), the W-8 bench baseline (ratified bands PASS; `delay_product` RFF ≫ linear in-repo), and this matrix. Remaining program work: Wave 5 concurrency hardening (W-6 snapshots dir, W-7 `--results-dir`, launcher multi-run + Q-6 log-dir class), W-12/Q-7 `csv_import` corpus, and the §12 performance lane (owns F-P1-3b). Owner decisions still open: F-P1-2 (native Grafana v13 squatting :3000), stale cascor image rebuild, F-P1-3b profiling priority.

> **Update (2026-08-15) — F-P1-3b is REFUTED; this paragraph's forward-looking items are superseded.**
> Three references above are stale and must not be picked up as work:
>
> - "P1 ✓ (**F-P1-3b** CLI-path completion open as a §12 perf item)" — P1.2 full completion is **PASS**
>   ([P1 note §6](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md)); it was
>   never blocked on compute, but on a post-training `plt.show()` (cascor#517).
> - "the §12 performance lane (**owns F-P1-3b**)" — the perf lane no longer owns it. The lane itself
>   remains open; its F-P1-3b premise does not.
> - "Owner decisions still open: … **F-P1-3b profiling priority**" — withdrawn as a decision. There is
>   nothing to prioritise profiling *for* on this finding.
>
> F-P1-3b claimed structural direct-CLI compute overhead. It was **withdrawn** for lack of evidence
> ([F-P1-3 root cause §3](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md))
> — the 590 s was a *block, not a workload*, so no compute gap was ever measured — and then positively
> **refuted** by direct measurement
> ([head-to-head §5](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md)):
> on identical data at an identical budget the CLI is not slower at all (36 s vs 46 s; 35 s vs 35 s).
> Of this paragraph's other items, **F-P1-2 and Q-6 remain genuinely open owner calls.**
