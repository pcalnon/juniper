# HANDOFF 2026-07-31 — CLI Experimentation Program: continue with Wave 2.3 (recurrence driver path)

Continue executing the CLI test/validation/experimentation program for juniper-cascor + juniper-recurrence (plan of record: `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`; owner ratified all Q-1..Q-12).

## Completed so far

- Waves 0, 1.1-1.4, 2.1 + plan erratum: ALL MERGED (ml#868/#875/#876, deploy#165/#166/#167).
- Wave 2.2 (this session): `util/experiments/run_experiment.py` cascor service path + `tests/test_run_experiment.py` (50 hermetic tests) + ci.yml wiring — **PR ml#878 OPEN** (branch `feature/run-experiment-driver-cascor`); verify its CI/merge state first.
- Post-merge worktree hygiene done (20 stale session worktrees removed 2026-07-31).

## Remaining next steps (dependency order)

1. **Wave 2.3** (after ml#878 merges): recurrence path in `run_experiment.py` + test extension. Spec §6.3 step 4: `POST /v1/train` is **synchronous** (the response IS completion — `routers/training.py:37`), then optional `POST /v1/predict` (re-ref the same dataset with `split=test`), then optional `POST /v1/crossval`. §5.5 YAML blocks: `train:` / `crossval:` / `predict:` + `dataset.split`; health path `/v1/health/ready`. Target keys: `y_` for the synthetics, `y_reg_` ONLY for `equities_seq`. `outputs.save_model: true` = re-run `juniper-recurrence train --out` with identical params as an explicit manifest-recorded extra step (G-18: service mode leaves no model artifact). The 2.2 driver's recurrence arm currently exits 2 with a Wave-2.3 pointer — replace it; extend `load_config` (recurrence dataset keys incl. `split`, the three new blocks).
2. Wave 2.4 (cascor plot set §8.1, client-side matplotlib), 2.6 (stats.json + summary.md renderers §8.3), 2.7 (docs/REFERENCE.md operator section).
3. P1 smoke (§10.2) via the launcher incl. the Wave-1.4 dashboard live-render check (P1.6), then Waves 3+ (YAML config layer; launcher `--config` is staged-inert until 3.1/3.3).

## Key context

- **Read the memory file first**: `project_cascor_recurrence_cli_experimentation_plan.md` — the Wave-2.2 paragraph records the implementation truths (cascor envelope shape, ports.json contract, staged-Literal aliases, urllib/F-1 redirect decision, Q-2 defaults, manifest-for-every-outcome rule) the 2.3 work builds on.
- Driver test idiom: scripted stub `http.server` plays both services; `RedactedEnv` for subprocess arms; `sys.path.insert(REPO_ROOT/"util")` + `from experiments import run_experiment`.
- Headless commits need `git -c commit.gpgsign=false commit`; rebase conflict resolutions need `git commit --no-gpg-sign`.
- Owner decision still pending (not urgent): recurrence `namespace="juniper_recurrence"` alignment vs shipped generic-family + service-label scoping.
- Deploy micro-PR candidate still open: `tests/test_provenance_sha.py` fixture commits without `-c commit.gpgsign=false` (fails locally on YubiKey hosts).

## Verification for the new thread

```bash
gh pr list --repo pcalnon/juniper-ml --state open
git -C /home/pcalnon/Development/python/Juniper/juniper-ml log --oneline -3 origin/main
python3 -m unittest tests/test_run_experiment.py   # 50/50 OK expected
```

Git status at handoff: Wave-2.2 work committed + pushed on `feature/run-experiment-driver-cascor` (PR ml#878); this handoff file rides its own docs PR; no other uncommitted changes.
