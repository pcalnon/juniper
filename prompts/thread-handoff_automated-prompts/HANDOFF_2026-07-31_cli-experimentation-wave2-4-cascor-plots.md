# HANDOFF 2026-07-31 — CLI Experimentation Program: continue with Wave 2.4 (cascor plot set)

Continue executing the CLI test/validation/experimentation program for juniper-cascor + juniper-recurrence (plan of record: `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`; owner ratified all Q-1..Q-12).

## Completed so far

- Waves 0, 1.1-1.4, 2.1, 2.2 + plan erratum: ALL MERGED (ml#868/#875/#876/#878/#879, deploy#165/#166/#167).
- Wave 2.3 (this session): recurrence path in `util/experiments/run_experiment.py` (synchronous train / predict / crossval + G-18 `save_model` CLI re-run) + 16 new tests (66 total) — **PR ml#881 OPEN** (branch `feature/run-experiment-driver-recurrence`); verify its CI/merge state first.

## Remaining next steps (dependency order)

1. **Wave 2.4** (after ml#881 merges): the cascor plot set (§8.1) as a separate PR. Driver plots **client-side** from JSON/array payloads (never import cascor — the plotter imports torch): `dataset.png` (NPZ `X_full`/`y_full` scatter, any 2-feature classification generator), `decision_boundary.png` (from the collected `/v1/decision-boundary` grid; 2-D input only), `training_history.png` (loss + accuracy vs epoch with hidden-unit-insertion markers, from `/v1/metrics/history`), `candidate_correlation.png` (from the driver's own `metrics_series.csv` — correlation exists nowhere else), `eval_metrics.png` (F1/precision/recall/ROC-AUC bars when eval metrics enabled). `outputs.plots` is already validated + recorded ("plots_note" in the manifest); matplotlib must be imported lazily (headless `Agg` backend) so the driver stays importable without it. Per-dataset acceptance (§10.3): plots non-degenerate (non-empty, finite axes). Hermetic tests from synthetic payloads (§10.6 row 2 names "plot files produced from synthetic payloads").
2. Wave 2.5 (recurrence plot set §8.2 — closes G-5), 2.6 (`stats.json` + `summary.md` renderers §8.3), 2.7 (`docs/REFERENCE.md` operator section + cheatsheet).
3. P1 smoke (§10.2) via the launcher incl. the Wave-1.4 dashboard live-render check (P1.6), then Waves 3+ (YAML config layer; launcher `--config` staged-inert until 3.1/3.3).

## Key context

- **Read the memory file first**: `project_cascor_recurrence_cli_experimentation_plan.md` — the Wave-2.2/2.3 paragraphs record the implementation truths (cascor envelope vs recurrence raw models, ports.json contract, `RequestTimeout` budget semantics, staged-Literal aliases, the no-`--params` CLI constraint, nested recurrence repo layout).
- Driver test idiom: scripted stub `http.server` plays all services; `RedactedEnv` for subprocess arms; `sys.path.insert(REPO_ROOT/"util")` + `from experiments import run_experiment`.
- Headless commits need `git -c commit.gpgsign=false commit`. Merging: unsigned commits leave PRs OPEN/BLOCKED under the `required_signatures` ruleset — the owner merges with the admin bypass (`gh pr merge --squash --admin` completed the owner-stated merges of ml#878/#879 this session).
- CI already installs numpy for the driver tests; matplotlib will need the same treatment in the tests job when Wave 2.4 lands (mirror the numpy install-comment pattern).
- Owner decision still pending (not urgent): recurrence `namespace="juniper_recurrence"` alignment vs shipped generic-family scoping. Deploy micro-PR candidate still open: `tests/test_provenance_sha.py` gpg fixture.

## Verification for the new thread

```bash
gh pr list --repo pcalnon/juniper-ml --state open
git -C /home/pcalnon/Development/python/Juniper/juniper-ml log --oneline -3 origin/main
python3 -m unittest tests.test_run_experiment   # 66/66 OK expected
```

Git status at handoff: Wave-2.3 work committed + pushed on `feature/run-experiment-driver-recurrence` (PR ml#881); this handoff file rides its own docs PR; no other uncommitted changes.
