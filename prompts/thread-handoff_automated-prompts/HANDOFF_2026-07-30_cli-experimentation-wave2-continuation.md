# HANDOFF 2026-07-30 — CLI Experimentation Program: continue after Waves 0-2.1

Continue executing the CLI test/validation/experimentation program for juniper-cascor + juniper-recurrence (plan of record: `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`, merged ml#867; owner ratified all Q-1..Q-12).

## Completed so far

- Wave 0 (P0 preflight + relay probe): merged ml#868; evidence doc `notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md` (findings F-1..F-8 are BINDING implementation guidance).
- Wave 1.1/1.2 (host-experiment scrape lane + structural test): merged deploy#165.
- Wave 1.3 (juniper-recurrence dashboard + recording-rule extension): OPEN deploy#166, CI green.
- Wave 1.4 (juniper-experiments run-scoped dashboard): OPEN deploy#167, CI green.
- Wave 2.1 (util/experiment_stack.bash + tests/test_experiment_stack_script.py): OPEN ml#876, CI green; live smoke passed (F-6 pidfile=ss-listener confirmed).
- Plan erratum (recurrence HTTP families are GENERIC `juniper_http_*` — no namespace kwarg at `juniper_recurrence/app.py:118`): OPEN ml#875, CI green.

## Remaining next steps (dependency order, after owner merges the 4 open PRs)

1. Wave 2.2: `util/experiments/run_experiment.py` cascor path + tests (plan §6.3: drive POST /v1/training/start -> poll to COMPLETED, sample loopback `/metrics` into `metrics_series.csv` each poll — correlation is NOT in `/v1/metrics/history`; plots per §8.1; manifest per §13.4).
2. Wave 2.3: driver recurrence path (train/predict/crossval; `y_` keys for synthetics, `y_reg_` only for equities_seq).
3. P1 smoke (§10.2) via the launcher incl. the Wave-1.4 dashboard live-render check (P1.6), then Waves 3+ (YAML layer; `--config` is currently staged-inert in the launcher awaiting 3.1/3.3).

## Key context

- All P0/F-findings + Wave lessons are in memory file `project_cascor_recurrence_cli_experimentation_plan.md` (read it first) and the evidence doc. Highlights: explicit-IP extra_hosts (172.31.0.1); monitoring network discovered by `_monitoring$` suffix; pidfiles = ss listener pids; rebase captures gpg-sign at START (use `git commit --no-gpg-sign` for resolutions); headless commits need `-c commit.gpgsign=false`.
- Owner decision pending (not urgent): align recurrence to `namespace="juniper_recurrence"` (series rename => lockstep dashboard+rule updates) vs keep generic-family + service-label scoping (shipped).
- Deploy micro-PR candidate: `tests/test_provenance_sha.py` fixture commits without `-c commit.gpgsign=false` (fails locally on YubiKey hosts).
- Session worktrees: juniper-ml session worktree on branch `docs/plan-erratum-recurrence-http-prefix`; deploy worktrees for #166/#167 live under `worktrees/` (clean up after merges per the V2 procedure); Wave-2.1 agent worktree `juniper-ml/.claude/worktrees/agent-a0832c6a845609e81`.
- Verification for the new thread: `gh pr list --repo pcalnon/juniper-ml --state open` + same for juniper-deploy; `git -C <repo> log --oneline -3 origin/main` per repo; memory file for the full ledger.

Git status at handoff: all work pushed; no uncommitted changes anywhere except this handoff file's own PR.
