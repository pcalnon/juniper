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
| P1.2 cascor **direct CLI** — full run | **PASS** (as of §6, 2026-08-14) — originally **PARTIAL** (finding F-P1-3) | Launch + dataset fetch + live training demonstrated (26 k log lines, candidate training progressing, snapshots written); killed at the smoke's 480 s bound (exit 124) — the direct CLI exposes **no budget flags** (profiling only), so a smoke-scale completion is structurally unreachable until **W-11** (Wave 3.6) maps the experiment `training:` block onto it. **Closed in [§6](#6-p12-full-completion-row--closed-2026-08-14): the run never was compute-bound** — it blocked in `plt.show()` *after* training, and completed direct-CLI runs now exist |
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
| **F-P1-3** | The cascor **direct CLI** (`src/main.py`) exposes only profiling flags — no budget knobs — so P1.2's "exit 0 + plots" is unreachable at smoke scale under constants defaults (killed at 480 s mid-candidate-training). | ~~Expected-by-design gap: **W-11 (Wave 3.6)** maps the experiment `training:`/`dataset:` blocks onto the direct CLI.~~ **CLOSED ([§6](#6-p12-full-completion-row--closed-2026-08-14))** — the diagnosis above is wrong: the CLI was not budget-starved but blocked in `plt.show()` *after* training. Fixed in cascor#517; W-11 was necessary but never sufficient. |
| **F-P1-4** | H-4/H-5 as designed: the smoke left 4 snapshot `.h5` files in `juniper-cascor/src/cascor_snapshots/` (the hard-coded snapshot dirs). Files left in place for the owner. | **W-6** (`JUNIPER_CASCOR_SNAPSHOTS_DIR`, Wave 5.1) redirects these into `RUN_DIR/snapshots/`; until then the one-instance-per-checkout rule stands. |

## 3. Environment restoration

- Prometheus container stopped after the smoke; compose networks removed; **0 containers** running (the pre-P1 state).
- Both RUN_DIRs preserved under `~/.local/state/juniper-experiments/` (`20260807T195013Z-32d8`, `20260807T195239Z-0610`) with full artifacts (plots, results, stats, manifests) for owner inspection.
- The temporary `p1-smoke-*` experiment YAMLs lived in the session scratchpad (not the repo); their exact content is reproducible from §1's parameters and the run dirs' `config/experiment.yaml` copies.

## 4. Disposition

**P1 smoke: PASS** for every arm the current wave-set can reach (P1.1, P1.2-exit-arms, P1.3, P1.4, P1.5, P1.6-datasource, P1.7), with the two remaining halves — P1.2 full completion and P1.6 interactive render — blocked on **W-11** and the **F-P1-2 owner follow-up** respectively, not on the program tooling. The program may proceed to Waves 3+ (YAML config layer) and Wave 4 dataset enablement (W-1 first) per §14.

> **Update (2026-08-14):** **P1.2 full completion is now PASS** — see [§6](#6-p12-full-completion-row--closed-2026-08-14). It was never blocked on W-11; it was blocked on a post-training `plt.show()` (cascor#517). **P1.6 interactive render remains open** against the F-P1-2 owner follow-up, unchanged. P1 smoke is therefore PASS on every arm but that one.

> **Update (2026-08-16): P1 smoke is now PASS on EVERY arm — the last one closed.**
> **P1.6 interactive render is PASS**, and **F-P1-2 is closed with its premise refuted.** The
> `Juniper Experiments` dashboard was driven in a browser against live run
> `20260817T011726Z-6d05` and rendered all 13 panels with data (Targets Up = 2; build info for
> cascor 0.9.0 / data 0.11.0; training loss 0.204/0.263, accuracy 57.5%/35%, hidden units 2,
> candidate correlation ≈0.19, step duration p50 25.5 ms / p95 48.4 ms).
>
> Two rows above are superseded by that finding and must not be actioned:
>
> - **F-P1-2's remedy** ("stop/relocate the native Grafana or remap deploy's grafana host port") —
>   **nothing to do.** The `:3000` listener is the **Domotz Pro agent**, not Grafana, and deploy's
>   Grafana has mapped host **`:3001`** since 2026-05-27 (juniper-deploy `c36e52b`/#90). There was
>   never a bind conflict. Neither remedy was performed.
> - **P1.6's "blocked by findings F-P1-1/F-P1-2"** — F-P1-1 was cleared 2026-08-09 (image rebuild);
>   F-P1-2 is closed here. The row's own parenthetical, "the panels' underlying queries are exactly
>   the series proven present", turned out to be exactly right.
>
> **F-P1-4 is unchanged and still open**, and note its "4 snapshot `.h5` files" is long superseded —
> the directory now holds **27,867 files / 1.8 GB**, 65 of them from 2026-08. W-6 only redirects when
> `JUNIPER_CASCOR_SNAPSHOTS_DIR` is exported, so direct-CLI runs still write to the checkout. Per the
> owner (2026-08-16), this is to be addressed by a **designed, validated, documented** snapshot
> lifecycle — **not** an ad-hoc sweep; the design requirement is that historical models and runs stay
> loadable for replay, further experimentation, training pauses, and crash recovery. That design now
> exists:
> [snapshot lifecycle management](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md).
>
> **Its census inverts this row.** The archive is **not debris**: a read-only census plus a stratified
> sample verified with cascor's own `verify_saved_network` found **27,863 of 27,869 snapshots valid
> and loadable** (88/89 sampled valid, across every cohort including the 0.3.2 files six minors
> behind current) — 1.74 GiB of replayable models, only 6 empty stubs. A sweep sized to "reclaim
> 1.8 GB" would have destroyed ~27.8k real assets. The actual problems are three **silent-failure**
> defects — optimizer state discarded on every load (breaking resume-from-pause on the current
> version), `load_network` returning `None` for corrupt *and* absent alike, and no run provenance
> anywhere in the archive — plus the fact that `mtime` is not creation time here, so any age-based
> retention keyed on it would misjudge every file.
>
> Evidence:
> [F-P1-2 closure](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_F-P1-2-GRAFANA-RENDER-CLOSURE-EVIDENCE.md).

---

## 5. P1.2 full-completion re-run (2026-08-08, post-W-11) — addendum

W-11 (Wave 3.6; juniper-cascor#489 + the #491 pool amendment) landed the direct-CLI YAML mapping that F-P1-3 was waiting on. The re-run campaign (fresh launcher stack, data on 8110; smoke-shape YAML driven through `main.py --config`):

| Attempt | Bound set | Outcome |
| --- | --- | --- |
| 1 | smoke YAML budgets via W-11 (`output_epochs` 50 via the `max_epochs` alias, `max_hidden_units` 2) | timeout 590 s — **W-11 verified applying** (file log: 9 overrides active; `candidate_pool_size`/`max_iterations`/`early_stopping` correctly reported service-tier-only); candidate phase dominated |
| 2 | + `candidate_epochs` 100, `patience` 25 | timeout — candidates cap at epoch 100 ✓; **156 distinct candidates** (constants pool × 2 rounds) dominate |
| 3 | + `CASCOR_NUM_PROCESSES=4` (H-11 env knob) | timeout — the env knob bounds concurrency, not the candidate count |
| 4 | + `candidate_pool_size: 4` via the **#491 amendment** (`SpiralProblem` takes the kwarg; `main()` never passed it) | timeout — pool verified **156 → 12 candidates**; still compute-bound |
| 5 | + `JUNIPER_CASCOR_LOG_LEVEL=WARNING` (6 stdout lines total) | timeout — **compute-bound, not log-bound** |

**Finding F-P1-3b (supersedes the F-P1-3 disposition)**: with every documented bound verifiably applied, the direct-CLI training path exceeds a 590 s smoke bound on this host, where the **service** path completes the identical shape (spiral 200×2, pool 4, hidden 2) in **24 s** (§1 P1.1). The gap is structural CLI-path compute overhead — a §12 performance-lane scenario (`main.py --profile` exists for exactly this). P1.2's full-completion row stays open against F-P1-3b; the exit arms, launch path, W-11 mapping, and pool amendment are all live-proven.

Environmental notes from the campaign: a fresh checkout crashes on the hard-coded `logs/` dir being absent (`FileNotFoundError` at logger init — adjacent to Q-6/H-7); teardown re-attested clean (ranges empty, `JuniperProject.pid` untouched).

---

## 6. P1.2 full-completion row — CLOSED (2026-08-14)

**Verdict: PASS.** A completed direct-CLI run exists, so the row's own acceptance criterion is met.

**F-P1-3b (§5) is WITHDRAWN.** The five attempts above were never compute-bound. `solve_n_spiral_problem` ended with `plt.show()` followed by `self.plotter.join()`: under an interactive backend the first parks the process in the GUI event loop and the second waits on a non-daemon plot child parked in its own `plt.show()`. Training had *already finished* at that point in every attempt. The campaign therefore measured a **block, not a workload** — no attempt observed the CLI finish, so no compute gap was ever measured, and no budget knob could have moved any of them. That is why attempts 1–5 were each verifiably applying their bound and each still "timed out": the bound was working and the hang was downstream of it.

It survived two "plumbing verified" waves because it depends on the **launching environment**, not the config — a genuinely headless host resolves matplotlib to `Agg`, where `plt.show()` is a no-op — and because the W-11 key maps carry no plot knob, so `outputs.plots: []` was never read by the direct CLI.

Root cause, the controlled A/B/C experiment, and the fix (cascor#517, `--no-plots` + a `_backend_is_interactive()` guard) are in [`…F-P1-3-ROOT-CAUSE.md`](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md). Preserved evidence for the completed run: `~/.local/state/juniper-experiments/20260814T224846Z-0565/artifacts/results/fp13-armC-preserved/` — `Completed solving` ×1, `Training completed` ×1, `Started plotting` ×0, 2-unit cap, train 0.95625.

**This row closes on existence, not on a comparison.** Deliberately **no** CLI-vs-service ratio is recorded here, and §5's "24 s" service figure must **not** be paired with any 2026-08-14 direct-CLI number: that service run predates juniper-cascor#514, after which spiral figures are not comparable (candidates now get the configured patience 100 rather than the module constant's 50 — R-5 §5.1). A genuine head-to-head needs both arms on one side of #514 and remains open as a fresh campaign.

One further correction to §5's reading: the direct CLI was *also* not applying the budget it appeared to. The YAML's `max_epochs` reached `SpiralProblem` but not the initial output-layer pass, which ran a module constant's 10000 epochs instead — finding L-1, live and fixed in cascor#522 (F-P1-3 note §9). This does not reinstate F-P1-3b: it is one measured call site, not a structural ratio, and it was never what blocked these five attempts.
