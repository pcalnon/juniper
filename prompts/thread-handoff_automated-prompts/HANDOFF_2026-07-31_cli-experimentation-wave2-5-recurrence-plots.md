# HANDOFF 2026-07-31 — CLI Experimentation Program: continue with Wave 2.5 (recurrence plot set)

Continue executing the CLI test/validation/experimentation program for juniper-cascor + juniper-recurrence (plan of record: `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`; owner ratified all Q-1..Q-12).

## Completed so far

- Waves 0, 1.1-1.4, 2.1, 2.2, 2.3 + plan erratum + both handoff archives: ALL MERGED (ml#868/#875/#876/#878/#879/#881/#882, deploy#165/#166/#167).
- Wave 2.4 (this session): `util/experiments/plots_cascor.py` (§8.1 cascor plot set, client-side, Agg) + driver wiring (per-kind `outputs.plots` validation, skip-vs-acceptance semantics, `driver.plots` manifest record) + 12 new tests (78 total) — **PR ml#885 OPEN** (branch `feature/experiment-driver-cascor-plots`); verify its CI/merge state first.

## Remaining next steps (dependency order)

1. **Wave 2.5** (after ml#885 merges): the recurrence plot set (§8.2 — closes G-5) as `util/experiments/plots_recurrence.py` + driver wiring, mirroring 2.4's shape: `dataset_overview.png` (sampled `X` windows with the target marked), `dt_histogram.png` (per-step Δt distribution + `target_dt` — the irregularity signature; keys `dt_{split}` `(W,L)` / `target_dt_{split}` `(W,)`), `forecast_vs_truth.png` (predict response vs the test-split target), `residuals.png` (series + histogram + optional residual-vs-`target_dt` scatter), `crossval_folds.png` (per-fold r²/MSE bars + aggregate line), `metrics_table.png`. Target keys: `y_{split}` for the synthetics, `y_reg_{split}` ONLY for `equities_seq` (or normalize via the data-client contract helper). NO training-history plot (API-infeasible: `TrainResponse` has no per-epoch series — §8.2 note). The RECURRENCE_PLOT_NAMES set + per-kind validation already exist; replace the recurrence `plots_note` manifest stub with a real `driver.plots` record. NPZ fetch via the existing `_http_bytes` + `load_npz_bytes` idiom; predict/crossval payloads are already retained in the recurrence path or trivially stashable.
2. Wave 2.6 (`stats.json` + `summary.md` renderers §8.3 — identity/dataset/outcome/per-app blocks; sources mostly in the manifest + collected artifacts), 2.7 (`docs/REFERENCE.md` operator section + cheatsheet entries for launcher + driver).
3. P1 smoke (§10.2) via the launcher incl. the Wave-1.4 dashboard live-render check (P1.6), then Waves 3+ (YAML config layer; launcher `--config` staged-inert until 3.1/3.3).

## Key context

- **Read the memory file first**: `project_cascor_recurrence_cli_experimentation_plan.md` — Wave-2.2/2.3/2.4 paragraphs carry the implementation truths (envelope vs raw models, real boundary payload keys, plots-module file-path loading, skip-vs-fail semantics, `RequestTimeout` budget, no-`--params` CLI constraint, nested recurrence repo layout).
- Driver test idiom: scripted stub `http.server` plays all services (`_artifact_npz_bytes` pattern for NPZ endpoints — a 3-D sequence variant is needed for 2.5); `RedactedEnv` for subprocess arms; PNG-magic + size assertions for plots.
- Headless commits: `git -c commit.gpgsign=false commit`. Owner merges via admin bypass (unsigned commits leave PRs OPEN/BLOCKED under `required_signatures`).
- CI test job installs pyyaml/packaging/numpy/matplotlib — no new deps expected for 2.5.
- Owner decision still pending (not urgent): recurrence namespace alignment. Deploy micro-PR candidate still open: `tests/test_provenance_sha.py` gpg fixture.

## Verification for the new thread

```bash
gh pr list --repo pcalnon/juniper-ml --state open
git -C /home/pcalnon/Development/python/Juniper/juniper-ml log --oneline -3 origin/main
python3 -m unittest tests.test_run_experiment   # 78/78 OK expected
```

Git status at handoff: Wave-2.4 work committed + pushed on `feature/experiment-driver-cascor-plots` (PR ml#885); this handoff file rides its own docs PR; no other uncommitted changes.
