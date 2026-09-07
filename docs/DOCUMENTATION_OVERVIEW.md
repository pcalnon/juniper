# Documentation Overview

## Navigation Guide to juniper-ml Documentation

**Version:** 0.2.54
**Status:** Active
**Last Updated:** 2026-09-05
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Quick Navigation](#quick-navigation)
- [Document Index](#document-index)
- [Ecosystem Context](#ecosystem-context)
- [Related Documentation](#related-documentation)

---

## Quick Navigation

### I Want To

| Goal                                    | Document                                                                                                                         | Location |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|----------|
| **Install Juniper packages**            | [QUICK_START.md](QUICK_START.md)                                                                                                 | docs/    |
| **See extras and version info**         | [REFERENCE.md](REFERENCE.md)                                                                                                     | docs/    |
| **Configure HTTP client `base_url`**    | [REFERENCE.md](REFERENCE.md#http-client-base-url-contract)                                                                       | docs/    |
| **Run the local host stack**            | [REFERENCE.md](REFERENCE.md#host-orchestration-utilities)                                                                        | docs/    |
| **Operate the scheduled Duplicati backup lane** | [REFERENCE — Scheduled Duplicati Backup Lane](REFERENCE.md#scheduled-duplicati-backup-lane)                                | docs/    |
| **Archive the Juniper project tree to external media** | [REFERENCE — Juniper Project-Tree Backup](REFERENCE.md#juniper-project-tree-backup) (per-repo `.tbz2.gpg`; restore `-xjf`; not Duplicati) | docs/    |
| **Reap orphaned Juniper pytest children** | [REFERENCE.md](REFERENCE.md#pytest-orphan-reaper)                                                                              | docs/    |
| **Run / score a pointer-follow soak probe** | [REFERENCE — Pointer-Follow Soak](REFERENCE.md#pointer-follow-soak) (least-covered vs characterisation; `source-recovered` denominator) | docs/    |
| **Decide whether the cascor primary is frozen** | [REFERENCE — Cascor Primary Freeze Tell](REFERENCE.md#cascor-primary-freeze-tell) (exit 1 = in force; 0 ≠ no importer) | docs/    |
| **Check installed juniper-* floor drift** | [REFERENCE.md](REFERENCE.md#environment-floor-drift-check)                                                                     | docs/    |
| **Diagnose a broken conda `import torch`** | [REFERENCE — Conda Env Torch Shadow](REFERENCE.md#conda-env-torch-shadow-diagnostic-p-5) (exit **2** = P-5 free-threaded; exit **4** = May-7 wheel layout; does not rebuild) | docs/    |
| **Check custom-agent suite health**     | [REFERENCE.md](REFERENCE.md#agent-suite-doctor)                                                                                  | docs/    |
| **Triage fleet PRs / sequence-safety**  | [REFERENCE.md § Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety)                                 | docs/    |
| **Triage resident-hazard gaps after an AGENTS.md cut** | [REFERENCE — Resident-Hazard Gap Triage](REFERENCE.md#resident-hazard-gap-triage) (count grows after a cut; health is score ≥ 3) + [fleet record](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md) | docs/ + notes/ |
| **Run the isolated E2E trio**           | [Isolated-stack E2E checklist](../notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md) + [REFERENCE — Isolated Stack](REFERENCE.md#isolated-stack-e2e-utilities) | notes/ + docs/ |
| **Write canopy E2E matrix verdicts**    | [REFERENCE — Canopy E2E Matrix Writes](REFERENCE.md#canopy-e2e-matrix-writes) (fill is dry-run; set-verdicts is not; do not plan from `e2e_row_coverage.py`) | docs/    |
| **Diagnose F-CANOPY-027 poller starvation (12-slot pool)** | [REFERENCE — F-CANOPY-027 Poller Starvation Probes](REFERENCE.md#f-canopy-027-poller-starvation-probes) + [cheatsheet](DEVELOPER_CHEATSHEET_JUNIPER-ML.md) | docs/ |
| **Triage canopy E2E findings (P0/P1 exit)** | [REFERENCE — Canopy E2E Finding Triage](REFERENCE.md#canopy-e2e-finding-triage) (`e2e_finding_triage.py`; ACCEPTED ≠ FIXED ≠ OPEN) | docs/ |
| **Score canopy Topology-tab rows**      | [REFERENCE — Canopy E2E Topology Driver](REFERENCE.md#canopy-e2e-topology-driver) (`e2e_seg17_topology_driver.py`; `STEPS` is the authority; M-06/M-07/M-12 can PASS the easier half) | docs/ |
| **Drive canopy dataset-tab / W6 rows**  | [REFERENCE — Canopy E2E Dataset Drivers](REFERENCE.md#canopy-e2e-dataset-drivers) (W6 `--steps` vs §3.6 `--step`; never confirm restart) | docs/ |
| **Triage Cursor-fleet / predicted-merge PRs** | [REFERENCE — Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety)                            | docs/    |
| **Audit required-status-check contexts / why `main` is BLOCKED** | [REFERENCE — Ruleset Context Audit](REFERENCE.md#ruleset-context-audit) (read-only; 2026-08-10 class; do not quote the note's §1 counts) | docs/    |
| **Run a per-run experiment stack**      | [REFERENCE — Experiment Stack](REFERENCE.md#experiment-stack-utilities) (incl. partial-`--up` → `teardown_run`) + [CLI experimentation plan](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) | docs/ + notes/ |
| **Run a PF scenario suite (PF-1…PF-7)** | [REFERENCE — PF Scenario Suites](REFERENCE.md#pf-scenario-suites) (`--dry-run` first; PF-1 matched 4000/4000 epochs; `JUNIPER_SUITE_GRAFANA_BRIDGE`; PF-4/PF-8 are not driver suites) + [P1 design](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md) | docs/ + notes/ |
| **Bless / compare a perf-lane baseline** | [REFERENCE — Perf-Lane Work Gate](REFERENCE.md#perf-lane-work-gate) (`read_run_metrics` / `make_baseline` / `compare_baseline`; sound since ml#1743, but do **not** wire the exact work gate to CI — that is an open owner decision, P1 design §6) | docs/ |
| **Read ratified perf metrics / bless a baseline** | [REFERENCE — Perf-lane metrics and baselines](REFERENCE.md#perf-lane-metrics-and-baselines) (`read_run_metrics.py` / `make_baseline.py`; `step_count` FAIL behind workload fingerprint, not `config_sha256`) | docs/ |
| **Compare a suite to a Q-8 baseline**   | [REFERENCE — Perf-Lane Split Comparator](REFERENCE.md#perf-lane-split-comparator) (identity first; work exact / speed reported; exit 0/1/2) | docs/    |
| **Read a suite report's gate inputs**   | [REFERENCE — Suite Report Gate Inputs](REFERENCE.md#suite-report-gate-inputs) (`step_count` / mean step beside de-ratified `wall_seconds`; `--compare-baseline` is reporting only) + [P2 plan](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) item 1.4 | docs/ + notes/ |
| **List or prune experiment RUN_DIRs**   | [REFERENCE — Run lister / pruner](REFERENCE.md#run-lister--pruner-list_runspy) (directory-truth; `--prune` deletes the `RUN_DIR`, `--down` keeps `artifacts/`) | docs/ |
| **Run a multi-cell experiment suite**   | [REFERENCE — Suite Driver](REFERENCE.md#suite-driver) (`run_suite.py`: expansion, resume, cascor parallel floor, Grafana env toggle) + [CLI experimentation plan](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) Wave 7 | docs/ + notes/ |
| **Report (not gate) a recurrence perf run** | [REFERENCE — Recurrence Work Is Not Countable](REFERENCE.md#recurrence-work-is-not-countable) (`work_countable` third state; `make_baseline` / `compare_baseline` refuse; PF-5/6/7 report-only) + [P2 plan](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) | docs/ + notes/ |
| **Read a run's `stats.json` / `summary.md`** | [REFERENCE — Experiment Stats Summary](REFERENCE.md#experiment-stats-summary-ss83) (de-ratified `wall_seconds`, per-poll step duration, `scrape_confirmed` tri-state, recurrence timings under `outcome.timings`) | docs/    |
| **Check which generators an env can run** | [REFERENCE — Generator Availability Matrix](REFERENCE.md#generator-availability-matrix-on-host) (gates, mnist/equities install paths, probe one-liner) | docs/    |
| **Run `equities` / `equities_seq` without a 422** | [REFERENCE — Equities Symbol Cap](REFERENCE.md#equities-symbol-cap) (14-symbol refuse; unit is symbols because cost is per request; silent slice deleted) | docs/    |
| **Import a CSV/JSON dataset (byte cap)** | [REFERENCE — CSV Import Byte Cap](REFERENCE.md#csv-import-byte-cap) (128 MiB, 422 until opt-in, `IMPORT_DIR` pitfall; equities `max_symbols` still silent) | docs/    |
| **Bound an `equities` request (do not use a byte cap)** | [REFERENCE — Equities Symbol Cap](REFERENCE.md#equities-symbol-cap) (per-request cost, silent `max_symbols` slice, default 503 names ≈ 34 min) | docs/    |
| **Index / classify / backfill the snapshot archive** | [REFERENCE — Snapshot Sidecar Chain](REFERENCE.md#snapshot-sidecar-chain) (`--scan`, two-axis classify, derivation levels, `--root` trap) | docs/    |
| **Attribute snapshots / pin the dataset instance** | [REFERENCE — Snapshot Attribution Dataset Pin](REFERENCE.md#snapshot-attribution-dataset-pin) (`seeded_params`, `--dataset-seed` vs `--seed`, sidecar-chain `--root` trap) | docs/    |
| **Run a P4 campaign suite** | [REFERENCE — P4 Campaign Suites](REFERENCE.md#p4-campaign-suites) (19 YAMLs; `include` ≠ `matrix`; cap-128 H2H is n=2; recurrence P4 cells report, they do not gate) | docs/    |
| **Census X7 off-loop / slice 1a** | [REFERENCE — X7 Off-Loop Census](REFERENCE.md#x7-off-loop-census) (canopy gate is authority for `main.py` only; count 58; do not quote v1; site-local exemption only) | docs/    |
| **Re-drive the topology block** | [REFERENCE — Topology Step Order and Blast-Radius IDs](REFERENCE.md#canopy-e2e-topology-step-order-and-blast-radius-ids) (`topostate` first or alone; the `W4-*` IDs are real matrix §4 steps) | docs/    |
| **Size memory-budget slack after a cut** | [REFERENCE — Memory-Budget Slack (Planning)](REFERENCE.md#memory-budget-slack-planning) (`measure-growth` `max`, floored at 2,000; headroom is not a CI failure) | docs/    |
| **Re-probe a canopy store that "never advances"** | [REFERENCE — F-039 Store Probe](REFERENCE.md#f-039-store-probe) (apply / soak / report / revert; read the whole series; `--target topology` refuses) | docs/    |
| **Check the Claude Code MEMORY.md index** | [REFERENCE — MEMORY.md Index Check](REFERENCE.md#memorymd-index-check) (200/25k silent newest-first truncate; hook-not-line 120 on NEW slugs; CI cannot see `~/.claude`) | docs/    |
| **Census F-CANOPY-037 topology paint** | [REFERENCE — F-CANOPY-037 Render Census](REFERENCE.md#f-canopy-037-render-census) (11 sessions; structured JSON; `hidden_units==0` is INVALID) | docs/    |
| **Census F-CANOPY-037 topology-graph paint** | [REFERENCE — F-CANOPY-037 Render Census](REFERENCE.md#f-canopy-037-render-census) (11 sessions; exit 0 is not a paint PASS; idle populated is VALID) | docs/    |
| **Close or count a defect-register row** | [REFERENCE — Defect Register Close Protocol](REFERENCE.md#defect-register-close-protocol) (`**FIXED` token, cwd pitfall, third reading vs the two §4 counters) | docs/    |
| **Read the NPZ / partition contract (`X_full` vs `X_val`)** | [REFERENCE — Train / Val / Test Partition Contract](REFERENCE.md#train--val--test-partition-contract) + [partition design](../notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md) | docs/ + notes/ |
| **Run / score a pointer-follow soak probe** | [REFERENCE — Pointer-Follow Soak](REFERENCE.md#pointer-follow-soak) (least-covered vs characterisation; `--dry-run` is exempt from the terminal-verdict stop) | docs/    |
| **Refresh the requirements snapshot** | [REFERENCE — Requirements Snapshot Consolidation](REFERENCE.md#requirements-snapshot-consolidation) (`by-area` is the corpus of record; ledger has no `detail`; `--check-roundtrip` then `--check-views`) | docs/    |
| **See which E2E matrix rows are still empty** | [REFERENCE — Unfilled-Rows Ledger](REFERENCE.md#canopy-e2e-unfilled-rows-ledger) (`e2e_unfilled_rows.py`; do not plan from the TSV estimator) | docs/    |
| **Quick-reference dev tasks**           | [DEVELOPER_CHEATSHEET_JUNIPER-ML.md](DEVELOPER_CHEATSHEET_JUNIPER-ML.md)                                                         | docs/    |
| **Operate the PyPI release train**      | [Release-train operator runbook](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md)                 | notes/   |
| **Understand flood CI gates / main-verify** | [REFERENCE.md § Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates) + [flood analysis](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) | docs/ + notes/ |
| **Triage Sequence Safety red / Quality Gate green** | [REFERENCE — Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates) (`Sequence Safety` is required in `juniper-ml-rules`; QG green does not mean mergeable) | docs/    |
| **Triage post-merge main-verify / G3.1**| [REFERENCE — Post-Merge Main Verification](REFERENCE.md#post-merge-main-verification) (incl. stable-title failure notify)       | docs/    |
| **Provision YubiKey GPG (ed448 caveat)** | [REFERENCE — YubiKey GPG](REFERENCE.md#yubikey-gpg-provisioning) + [keytocard procedure](../notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md) | docs/ + notes/ |
| **Triage an open-PR budget WARN/ALARM** | [REFERENCE — Open-PR Budget Alarm](REFERENCE.md#open-pr-budget-alarm)                                                            | docs/    |
| **Triage a Ruleset Scope Guard / `~ALL` fail** | [REFERENCE — Ruleset Scope Guard](REFERENCE.md#ruleset-scope-guard) (`~ALL` re-arms deleted bot bypass rows; exit 2 is not clean) | docs/    |
| **Cut a GitHub Release / archive notes**| [PyPI publish procedure](../notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md)                                 | notes/   |
| **Publish an in-repo shared package**   | [REFERENCE — Sibling publish pipelines](REFERENCE.md#independent-sibling-package-publish-pipelines)                              | docs/    |
| **Understand meta TestPyPI Gate 1**     | [REFERENCE — Meta-Package Publish Pipeline](REFERENCE.md#meta-package-publish-pipeline) (10×6s poll, not `sleep 30`; two-phase verify) | docs/    |
| **Understand why a bare tag push publishes nothing** | [REFERENCE — Independent Sibling Package Publish Pipelines](REFERENCE.md#independent-sibling-package-publish-pipelines) (trigger is the gate; #555 / #1310) | docs/    |
| **Debug shared-package subdirectory CI**| [REFERENCE — Shared-Package CI Workflows](REFERENCE.md#shared-package-ci-workflows)                                              | docs/    |
| **Operate weekly docs-full-check**      | [REFERENCE — Docs Full Check](REFERENCE.md#docs-full-check)                                                                     | docs/    |
| **Understand weekly security / lockfile hygiene** | [REFERENCE — Scheduled Security Scan and Lockfile Update](REFERENCE.md#scheduled-security-scan-and-lockfile-update)     | docs/    |
| **Triage CodeQL / `Analyze (python)`** | [REFERENCE — CodeQL Analysis](REFERENCE.md#codeql-analysis) (SHA group, `merge_group` divergence, review-thread stall) | docs/    |
| **Add or re-pin a required status-check context** | [REFERENCE — Required-Context Ruleset Writer](REFERENCE.md#required-context-ruleset-writer) (`--amend-integration-id`; do not hand-roll a ruleset PUT) | docs/    |
| **Read the release-train detect summary / Slack** | [REFERENCE — Detect Summary and Slack](REFERENCE.md#release-train-detect-summary-and-slack)                             | docs/    |
| **Understand the AGENTS.md date check** | [REFERENCE — AGENTS.md Date Check](REFERENCE.md#agentsmd-date-check)                                                             | docs/    |
| **Audit `claude.yml` access safeguards**| [REFERENCE — Claude.yml Access Validation](REFERENCE.md#claudeyml-access-validation) + [ANTHROPIC API key walkthrough](../notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md) | docs/ + notes/ |
| **Operate the GitHub `@claude` assistant** | [REFERENCE — Claude Code Action](REFERENCE.md#claude-code-action) (live pin, `@claude` `if:`, template-snapshot drift) | docs/ |
| **Debug service-core middleware / control-WS / workers** | [REFERENCE — juniper-service-core](REFERENCE.md#juniper-service-core)                                           | docs/    |
| **Create or clean a worktree**          | [Worktree setup](../notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md) / [cleanup V2](../notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md) + [REFERENCE — in-use probe](REFERENCE.md#wider-second-opinion-open-files-and-argv) | notes/ + docs/ |
| **Check a worktree is idle before removing it** | [REFERENCE — Worktree Divergence](REFERENCE.md#worktree-divergence-is-a-memory-cost) (cwd-only liveness, then STRONG cwd/fd vs WEAK cmdline) | docs/ |
| **Understand the project**              | [README.md](../README.md)                                                                                                        | Root     |
| **Use shared observability primitives** | [juniper-observability README](../juniper-observability/README.md)                                                               | juniper-observability/ |
| **See development conventions**         | [AGENTS.md](../AGENTS.md)                                                                                                        | Root     |
| **See version history**                 | [CHANGELOG.md](../CHANGELOG.md)                                                                                                  | Root     |

---

## Document Index

### docs/ Directory

| File                                   | Type       | Purpose                                                                                          |
|----------------------------------------|------------|--------------------------------------------------------------------------------------------------|
| **DOCUMENTATION_OVERVIEW.md**          | Overview   | This file -- navigation index                                                                    |
| **QUICK_START.md**                     | Tutorial   | Install Juniper packages in under a minute                                                       |
| **REFERENCE.md**                       | Reference  | Extras, compatibility, host-stack / isolated-stack / experiment-stack ops, Duplicati backup, project-tree / external-media backup, agent-suite doctor, post-merge main-verify, YubiKey GPG pointer, fleet triage / sequence-safety, shared-package CI + publish pipelines (Gate 1 poll; release-only trigger), scheduled security-scan / lockfile-update, docs-full-check, release-train detect summary, AGENTS.md date check, `claude.yml` access validation, Claude Code Action (`@claude` assistant), sibling packages (incl. service-core), release-workflow, flood CI gates, open-PR budget alarm, X7 off-loop census, PF scenario suites, P4 campaign suites, perf-lane work gate, memory-budget planning slack, `MEMORY.md` index check, conda torch-shadow diagnostic, equities 14-symbol refuse, canopy topology step order / blast-radius IDs, and the F-039 store-apply probe |
| **DEVELOPER_CHEATSHEET_JUNIPER-ML.md** | Cheatsheet | Quick-reference card for common development, host-stack, backup-lane, CI guardrail and hygiene tasks, signing-ceremony tasks, service-core contracts, experiment-stack tasks, X7 census pitfalls, PF-suite scrapeability / epoch-pair traps, P4 campaign-suite catalog, perf-lane work-gate reads, memory-budget slack vs CI headroom, `MEMORY.md` index limits, conda torch-shadow triage, equities symbol-cap operator surface, topology step order / W-id facts, and the F-039 store-apply probe |

> The deprecated monolithic cheatsheet (`DEVELOPER_CHEATSHEET-ORIGINAL.md`)
> was relocated to `notes/history/` in 2026-04 and consolidated into
> `notes/legacy/` in 2026-05. Use the per-project
> `DEVELOPER_CHEATSHEET.md` files in each repo's `docs/` directory instead.

### Root Directory

| File             | Type     | Purpose                                                              |
|------------------|----------|----------------------------------------------------------------------|
| **README.md**    | Overview | PyPI landing page and installation examples                          |
| **AGENTS.md**    | Guide    | Conventions, worktree/handoff rules, CI surfaces, release-train summary |
| **CHANGELOG.md** | History  | Version history and release notes                                    |

### In-repo published subpackages

| Path                     | Purpose                                                                 |
|--------------------------|-------------------------------------------------------------------------|
| `juniper-observability/` | Shared Prometheus / middleware / logging helpers (`juniper-observability`) |
| `juniper-doc-tools/`     | Markdown link validator (`juniper-check-doc-links`)                     |
| `juniper-ci-tools/`      | Dep-docs generator + coverage-gap / env-drift CLIs                      |
| `juniper-config-tools/`  | Env-prefix migration helpers (stdlib-only)                              |
| `juniper-model-core/`    | Model-core conformance kit + crossval layer                             |
| `juniper-service-core/`  | Shared FastAPI service-tier primitives                                  |

Each subpackage has its own `README.md`, `CHANGELOG.md`, and `pyproject.toml`.

### notes/ Directory (Selected Runbooks)

| File                                                                                          | Type        | Purpose                                                                                          |
|-----------------------------------------------------------------------------------------------|-------------|--------------------------------------------------------------------------------------------------|
| **JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md**                                     | Register    | Ecosystem defect register; four-touch close + counters in [REFERENCE](REFERENCE.md#defect-register-close-protocol) |
| **JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md**                     | Runbook     | Modes (`off`/`report`/`propose`/`ceremony`), Gate 1/2 review, HALTs, App-token setup             |
| **JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md**              | Procedure   | YubiKey 5 ed448 `keytocard` root cause + validated ed25519/cv25519 transfer (pointer in [REFERENCE](REFERENCE.md#yubikey-gpg-provisioning)) |
| **JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md**                  | Findings    | Why the July restore points are gone; scheduled lane is the replacement (pointer in [REFERENCE](REFERENCE.md#scheduled-duplicati-backup-lane)) |
| **JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md**               | Design      | Snapshot retention + `juniper-backup.bash` restore-drill gate (SS6.4.2 q3); operator surface in [REFERENCE](REFERENCE.md#juniper-project-tree-backup) |
| **JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md**          | Investigation | GPGFlushError / Duplicati GPG wrapper; not a reason to drop `--no-auto-compact` |
| **JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md**                      | Analysis    | Flood remediation (§4 item 9 = open-PR budget alarm; operator surface in [REFERENCE](REFERENCE.md#open-pr-budget-alarm)) |
| **JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md**                | Incident    | 2026-08-10 fleet-union of 30 required contexts; §1 counts are historical — live classifier in [REFERENCE](REFERENCE.md#ruleset-context-audit) |
| **JUNIPER_2026-07-30_JUNIPER-ML_CURSOR-DASHBOARD-CONFIG-REQUESTS.md**                          | Requests    | Source-side Cursor dashboard caps (companion to the repo budget alarm)                           |
| **JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md**    | Walkthrough | L2/L3 `claude.yml` safeguards + `validate_claude_yaml_access.bash`; `DEFAULT_REPOS` fan-out in [REFERENCE](REFERENCE.md#claudeyml-access-validation); live pin in [Claude Code Action](REFERENCE.md#claude-code-action) |
| **JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md**                             | Procedure   | Cut a GitHub Release + archive `notes/releases/` (mandatory for every PyPI deploy)               |
| **JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md**                                  | Procedure   | Create an isolated git worktree for task work                                                    |
| **JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md**                             | Procedure   | Merge/cleanup after a task (CWD-safe); includes batch stale-worktree sweep                       |
| **JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_CONDA-ENV-REBUILD-PROCEDURE.md**                         | Procedure   | P-5 torch._C free-threaded shadow recovery (Option A/B). Classify first: [REFERENCE](REFERENCE.md#conda-env-torch-shadow-diagnostic-p-5) |
| **JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md**                                          | Fix         | May-7 regular-3.14 wheel-layout class + plant default `JuniperCascor1`. Classify first: [REFERENCE](REFERENCE.md#conda-env-torch-shadow-diagnostic-p-5) |
| **JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md**                       | Checklist   | Dedicated data/cascor/canopy E2E trio via `util/isolated_stack.bash` (compose contract also in [REFERENCE](REFERENCE.md#isolated-stack-e2e-utilities)) |
| **JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md** | Evidence | First-nine P4 studies (E-A…E-H, 55 cells — historical); operator catalog of the current 19 YAMLs in [REFERENCE — P4 Campaign Suites](REFERENCE.md#p4-campaign-suites) |
| **JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md** | Plan   | Per-run experiment stack + driver (Waves 2.1–2.7); operator contract + partial-`--up` teardown in [REFERENCE](REFERENCE.md#experiment-stack-utilities); P4 §10.5 catalog in [REFERENCE — P4 Campaign Suites](REFERENCE.md#p4-campaign-suites) |
| **JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md** | Design | Q-8 baseline directory + regression definition; operator surface in [REFERENCE — Perf-Lane Work Gate](REFERENCE.md#perf-lane-work-gate) |
| **JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md** | Plan   | Split work/speed gate + wave table. The "step_count is deterministic" premise is **settled with a condition** — exact within a termination branch (ml#1733) — and all six comparator defects are closed (ml#1741/ml#1743); still do not CI-wire, but that is now an open owner decision, not a soundness bar. Operator surface in [REFERENCE — Perf-Lane Work Gate](REFERENCE.md#perf-lane-work-gate) |
| **JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md**                        | Test matrix | 298-row canopy click-by-click ledger. Write path in [REFERENCE](REFERENCE.md#canopy-e2e-matrix-writes) (do not hand-edit status cells) |
| **JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md**                              | Ledger      | F-CANOPY-027 (FIXED canopy#507/#509/#511) and sibling findings; operator probes in [REFERENCE](REFERENCE.md#f-canopy-027-poller-starvation-probes) |
| **JUNIPER_2026-09-04_JUNIPER-CANOPY_F042-F046-FIX-DECISION-BRIEF.md**                          | Decision    | F-042/F-046 design-of-record; scorer AND predicates landed with #1672. Operator surface in [REFERENCE](REFERENCE.md#canopy-e2e-topology-driver) |
| **JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md**               | Design      | Snapshot identity / index / retention order (§6.2 / §6.4); operator surface in [REFERENCE](REFERENCE.md#snapshot-sidecar-chain) |
| **JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_SNAPSHOT-CLASSIFICATION-STAGE-1-FINDINGS.md**           | Findings    | Load-failure root-cause cohorts; backfill maps A/C FIXED, B truncated; operator surface in [REFERENCE](REFERENCE.md#snapshot-sidecar-chain) |
| **JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md**                       | Findings    | Attribution floors + why the dataset instance must be pinned; operator surface in [REFERENCE](REFERENCE.md#snapshot-attribution-dataset-pin) |
| **JUNIPER_2026-09-04_JUNIPER-DATA_EQUITIES-INGEST-SIZING-AND-FIELD-AVAILABILITY.md**            | Analysis    | Why equities bounds **symbols** (14), not bytes; operator surface in [REFERENCE](REFERENCE.md#equities-symbol-cap) |
| **JUNIPER_2026-09-03_JUNIPER-CANOPY_X7-EVENT-LOOP-BLOCKING-REMEDIATION-DESIGN.md**              | Design      | X7 event-loop blocking; slice 1a closes it. Operator surface in [REFERENCE](REFERENCE.md#x7-off-loop-census) (gate is authority for `main.py`; the count is 58 — canopy#567) |
| **JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md**                                | Ledger      | Canopy E2E findings. Operator traps (step order, W-id definitions, header severity) in [REFERENCE](REFERENCE.md#canopy-e2e-topology-step-order-and-blast-radius-ids); F-CANOPY-037 is OPEN |
| **JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md**                         | Matrix      | Click-by-click rows **and** §4's canonical workflow scripts — `### W4` is 17 numbered steps, `### W1` is 19 |
| **JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md**                                 | Plan        | Shared-session memory / P5 fleet ratchet. Operator surface for slack vs headroom in [REFERENCE](REFERENCE.md#memory-budget-slack-planning) |
| **JUNIPER_2026-08-24_JUNIPER-ML_MEMORY-INDEX-RUNWAY-AND-ENFORCEMENT-OPTIONS.md**                | Analysis    | MEMORY.md runway + hook-not-line 120; option A is `util/memory_index_check.py`. Operator surface in [REFERENCE](REFERENCE.md#memorymd-index-check) |
| **JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md**                          | Triage      | Fleet-wide source-vs-resident hazard pass; operator surface in [REFERENCE](REFERENCE.md#resident-hazard-gap-triage) |
| **JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md**                                | Protocol    | Seeded vs organic soak, Wilson verdicts, `source-recovered`; operator surface in [REFERENCE](REFERENCE.md#pointer-follow-soak) |
| **JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md**                          | Design      | Soak exists to inform relocation decisions; characterisation §8–§9 (strata real, membership not); [REFERENCE](REFERENCE.md#pointer-follow-soak) |
| **JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md**                   | Design      | Partition question CLOSED; `*_full` leaves the contract (not yet implemented). Operator surface in [REFERENCE](REFERENCE.md#train--val--test-partition-contract) |
| **JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md**                             | Procedure   | Snapshot consumption + refresh. Operator surface in [REFERENCE](REFERENCE.md#requirements-snapshot-consolidation) (`by-area` is the corpus of record) |
| **JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md**                    | Plan        | Requirements identification plan; §11 v5-1/v5-2 forced the consolidator redesign |
| **JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md**                                  | Procedure   | Thread handoff instead of compaction                                                             |

Full naming rules for `notes/`: [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](../notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md).

---

## Ecosystem Context

`juniper-ml` is a meta-package that provides a single `pip install` entry point for the Juniper ecosystem. The root package contains no importable Python code -- only optional dependency groups that install the actual servers, client libraries, worker, shared tooling, and recurrence packages.

This repository also houses six independently published subpackages under `juniper-*/`. Since `juniper-ml` 0.5.0 they are aggregated under the `[tools]` and `[all]` extras (plus `[doc-tools]` as a back-compat alias); they can also be installed directly when callers only want one library.

### What It Installs

```bash
juniper-ml[clients]    ──> juniper-data-client, juniper-cascor-client
juniper-ml[worker]     ──> juniper-cascor-worker
juniper-ml[servers]    ──> juniper-canopy, juniper-cascor, juniper-data
juniper-ml[tools]      ──> juniper-ci-tools, juniper-config-tools, juniper-doc-tools,
                           juniper-model-core, juniper-observability, juniper-service-core
juniper-ml[doc-tools]  ──> juniper-doc-tools  (back-compat alias)
juniper-ml[recurrence] ──> juniper-recurrence-model, juniper-recurrence, juniper-recurrence-client
juniper-ml[all]        ──> clients + worker + servers + tools + recurrence
```

Exact floors and ranges: [`REFERENCE.md`](REFERENCE.md#extras-reference) and `pyproject.toml`.

### Compatibility

| juniper-ml | juniper-canopy | juniper-cascor | juniper-data | juniper-data-client | juniper-cascor-client | juniper-cascor-worker | juniper-ci-tools | juniper-doc-tools | juniper-observability |
|------------|----------------|----------------|--------------|---------------------|-----------------------|-----------------------|------------------|-------------------|-----------------------|
| 0.6.x      | >=0.5.0        | >=0.5.0        | >=0.6.0      | >=0.4.1             | >=0.5.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0    | >=0.2.0               |

---

## Related Documentation

### Installed Packages

- **juniper-data-client** -- [Docs](https://github.com/pcalnon/juniper-data-client) (HTTP client for juniper-data) + [REFERENCE `base_url`](REFERENCE.md#http-client-base-url-contract)
- **juniper-cascor-client** -- [Docs](https://github.com/pcalnon/juniper-cascor-client) (HTTP/WS client for juniper-cascor) + [REFERENCE `base_url`](REFERENCE.md#http-client-base-url-contract)
- **juniper-cascor-worker** -- [Docs](https://github.com/pcalnon/juniper-cascor-worker) (distributed training worker)
- **juniper-observability** -- [Local docs](../juniper-observability/README.md) (shared health, logging, middleware, Prometheus, and Sentry primitives)
- **juniper-doc-tools** -- [Local docs](../juniper-doc-tools/README.md) (markdown link validator)
- **juniper-ci-tools** -- [Local docs](../juniper-ci-tools/README.md) (dep-docs / coverage-gap / env-drift CLIs)
- **juniper-service-core** -- [Local docs](../juniper-service-core/README.md) + [REFERENCE](REFERENCE.md#juniper-service-core) (shared FastAPI / WebSocket service tier, worker pool)

### Upstream Services

- **juniper-data** -- [Dataset Service](https://github.com/pcalnon/juniper-data)
- **juniper-cascor** -- [Training Service](https://github.com/pcalnon/juniper-cascor)
- **juniper-canopy** -- [Dashboard / control surface](https://github.com/pcalnon/juniper-canopy)

---

**Last Updated:** 2026-09-04
**Version:** 0.2.54
**Maintainer:** Paul Calnon
