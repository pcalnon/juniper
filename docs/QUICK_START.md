# Quick Start Guide

## Install Juniper Packages with juniper-ml

**Version:** 0.3.40
**Status:** Active
**Last Updated:** 2026-09-05
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Install](#1-install)
- [Verify](#2-verify)
- [Next Steps](#3-next-steps)

---

## Prerequisites

- **Python 3.12+** (`python --version`)

---

## 1. Install

`juniper-ml` is a meta-package with no code of its own. Choose the extra that matches your use case:

```bash
# Client libraries only (juniper-data-client + juniper-cascor-client)
pip install juniper-ml[clients]

# Distributed training worker only (juniper-cascor-worker)
pip install juniper-ml[worker]

# Server packages (juniper-canopy + juniper-cascor + juniper-data)
pip install juniper-ml[servers]

# Shared tooling (juniper-ci-tools + juniper-doc-tools + juniper-observability)
pip install juniper-ml[tools]

# Markdown link validator only (back-compat alias for one entry in [tools])
pip install juniper-ml[doc-tools]

# Everything
pip install juniper-ml[all]
```

> **Note on install size.** `juniper-ml[all]` transitively pulls a multi-GB dependency tree (notably `torch` via `juniper-cascor-worker` and `juniper-cascor`). On a fresh environment this resolves to approximately **5 GB on disk after install** (measured on Python 3.13 + Linux x86_64 against PyPI on 2026-05-21).
> Callers who do not need the worker or server distributions should prefer a narrower extra: `[clients]`, `[tools]`, and `[doc-tools]` each resolve to under 50 MB; `[servers]` is under 200 MB (no torch).

### What Each Extra Installs

| Extra       | Packages                                                                                                                                                                                                     |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clients`   | `juniper-data-client>=0.4.1`, `juniper-cascor-client>=0.5.0`                                                                                                                                                 |
| `worker`    | `juniper-cascor-worker>=0.4.0`                                                                                                                                                                               |
| `servers`   | `juniper-canopy>=0.5.0`, `juniper-cascor>=0.5.0`, `juniper-data>=0.6.0`                                                                                                                                      |
| `tools`     | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.2.0`, `juniper-service-core>=0.2.0,<0.8.0` |
| `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)                                                                                                                     |
| `recurrence`| `juniper-recurrence-model>=0.1.5,<0.3.0`, `juniper-recurrence>=0.2.0,<0.5.0`, `juniper-recurrence-client>=0.2.0,<0.3.0`                                                                                      |
| `all`       | All packages from `clients` + `worker` + `servers` + `tools` + `recurrence`                                                                                                                                  |

### Shared Observability Package

Since `juniper-ml` 0.5.0, `juniper-observability` is also aggregated under the `[tools]` and `[all]` extras, so a `pip install juniper-ml[all]` will install it alongside the rest of the platform. Callers that only want the shared observability primitives without the full meta-package can still install it directly:

```bash
pip install "juniper-observability[all]"
```

See [`../juniper-observability/README.md`](../juniper-observability/README.md) for its public surface and independent release workflow.

---

## 2. Verify

```bash
# Check installed packages
pip list | grep juniper
```

Expected output (with `[all]`):

```bash
juniper-canopy           0.5.x
juniper-cascor           0.5.x
juniper-cascor-client    0.5.x
juniper-cascor-worker    0.4.x
juniper-ci-tools         0.4.x
juniper-config-tools     0.1.x
juniper-data             0.6.x
juniper-data-client      0.4.x
juniper-doc-tools        0.1.x
juniper-ml               0.6.0
juniper-observability    0.2.x
```

```python
# Verify client imports
from juniper_data_client import JuniperDataClient
from juniper_cascor_client import JuniperCascorClient
from juniper_cascor_worker import CandidateTrainingWorker
```

REST `base_url` is normalised at construction on GitHub-main of the three HTTP clients (whitespace, case-insensitive `http(s)://`, host required, trailing `/v1` stripped). A hostless value raises `Juniper*ConfigurationError` rather than failing inside `requests` on the first call. `pip install juniper-ml[clients]` does **not** yet require those tips — see [HTTP Client Base-URL Contract](REFERENCE.md#http-client-base-url-contract).

---

## 3. Next Steps

- [Documentation Overview](DOCUMENTATION_OVERVIEW.md) -- navigation index
- [Reference](REFERENCE.md) -- extras, compatibility, and version reference
- [Host Orchestration Utilities](REFERENCE.md#host-orchestration-utilities) -- run services on-host with `util/juniper_plant_all.bash` and `util/juniper_chop_all.bash`
- [Conda Env Torch Shadow Diagnostic](REFERENCE.md#conda-env-torch-shadow-diagnostic-p-5) -- classify `import torch` / `torch._C` (exit **2** = P-5 free-threaded; exit **4** = May-7; does not rebuild)
- [Cascor Primary Freeze Tell](REFERENCE.md#cascor-primary-freeze-tell) -- whether a live importer holds the cascor primary; exit 0 is "no user-owned importer", not "no importer"
- [Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety) -- `predict_merge` + `Allow-Docs-Rewrite` trailer parity (#926)
- [Resident-Hazard Gap Triage](REFERENCE.md#resident-hazard-gap-triage) -- re-run after an `AGENTS.md` cut; the candidate count grows by construction (health is score ≥ 3)
- [Ruleset Context Audit](REFERENCE.md#ruleset-context-audit) -- why a required name that never reports leaves `main` unmergeable; re-run, do not quote the 2026-08-10 §1 counts
- [Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates) -- G4 pre-commit split, advisory Sequence Safety / Fleet PR Lint, post-merge `main-verify` catch-up
- [Post-Merge Main Verification](REFERENCE.md#post-merge-main-verification) -- G3 / G3.1 catch-up BASE, stable-title failure notify, trailers vs labels, battery path-gate
- [YubiKey GPG Provisioning](REFERENCE.md#yubikey-gpg-provisioning) -- ed448-on-card caveat + pointer to the validated transfer procedure
- [Juniper Project-Tree Backup](REFERENCE.md#juniper-project-tree-backup) -- per-repo `.tbz2.gpg` to external media; restore with `tar -xjf`; not the Duplicati `$HOME` lane
- [Open-PR Budget Alarm](REFERENCE.md#open-pr-budget-alarm) -- daily report-only open-PR / `cursor/` queue guardrail
- [Ruleset Scope Guard](REFERENCE.md#ruleset-scope-guard) -- `~ALL` re-arms deleted dependabot/Copilot bypass rows; exit 2 is not clean
- [Experiment Stack Utilities](REFERENCE.md#experiment-stack-utilities) -- per-run cascor/recurrence experiments via `util/experiment_stack.bash` + `run_experiment.py` (failed `--up` auto-tears down)
- [PF Scenario Suites](REFERENCE.md#pf-scenario-suites) -- Wave 7.3 instruments (`--dry-run` first; PF-1 matched 4000/4000 epochs; `JUNIPER_SUITE_GRAFANA_BRIDGE`; PF-4/PF-8 are not driver suites)
- [Perf-Lane Work Gate](REFERENCE.md#perf-lane-work-gate) -- `read_run_metrics` / `make_baseline` / `compare_baseline`; sound since ml#1743, but do **not** wire the exact `step_count` gate to CI — an open owner decision (P1 design §6), not a soundness bar
- [Equities Symbol Cap](REFERENCE.md#equities-symbol-cap) -- default `equities` / `equities_seq` is 422 at 14 symbols (cost is per request; silent slice deleted in data#354)
- [Canopy E2E Matrix Writes](REFERENCE.md#canopy-e2e-matrix-writes) -- fill / set-verdicts / rescore for the click-by-click ledger (fill is dry-run; set-verdicts is not)
- [F-CANOPY-027 Poller Starvation Probes](REFERENCE.md#f-canopy-027-poller-starvation-probes) -- 12-slot dash-renderer starvation (FIXED); do not add a new Interval; isolated stack only
- [Worktree Divergence / in-use probe](REFERENCE.md#worktree-divergence-is-a-memory-cost) -- cwd-only liveness is not enough; STRONG cwd/open-fd vs WEAK cmdline
- [Canopy E2E Finding Triage](REFERENCE.md#canopy-e2e-finding-triage) -- header-only P0/P1 open-count; ACCEPTED is a third disposition; always exits 0
- [CSV Import Byte Cap](REFERENCE.md#csv-import-byte-cap) -- csv_import 128 MiB bound (422 until opt-in); experiment-stack `IMPORT_DIR` pitfall; equities `max_symbols` still silent
- [F-CANOPY-037 Render Census](REFERENCE.md#f-canopy-037-render-census) -- 11-session topology-graph paint tally; exit 0 is not a paint PASS
- [Defect Register Close Protocol](REFERENCE.md#defect-register-close-protocol) -- `**FIXED` token, cwd pitfall, third reading vs the two §4 counters
- [Pointer-Follow Soak](REFERENCE.md#pointer-follow-soak) -- unprimed probe loop, characterisation vs least-covered, `--force` on terminal verdicts
- [Canopy E2E Topology Driver](REFERENCE.md#canopy-e2e-topology-driver) -- Playwright scorer for Topology-tab rows; `STEPS` is the authority; M-06/M-07/M-12 can PASS the easier half
- [Snapshot Sidecar Chain](REFERENCE.md#snapshot-sidecar-chain) -- index / classify / backfill the cascor archive (`--root`, not `JUNIPER_CASCOR_SNAPSHOTS_DIR`)
- [Recurrence Work Is Not Countable](REFERENCE.md#recurrence-work-is-not-countable) -- PF-5/6/7 report-only; `read_run_metrics.py --json`; `make_baseline` / `compare_baseline` refuse a recurrence suite
- [Perf-lane metrics and baselines](REFERENCE.md#perf-lane-metrics-and-baselines) -- `read_run_metrics.py` / `make_baseline.py`; gate `step_count` exactly, never `wall_seconds` or `timings.drive`
- [Perf-Lane Split Comparator](REFERENCE.md#perf-lane-split-comparator) -- `compare_baseline.py`: identity first, work exact / speed reported, exit 0/1/2 (#1622)
- [Suite Report Gate Inputs](REFERENCE.md#suite-report-gate-inputs) -- `run_suite` `aggregate.csv` / `REPORT.md` carry `step_count` + mean step; `--compare-baseline` is reporting only (P2 1.4 / #1643)
- [Run lister / pruner](REFERENCE.md#run-lister--pruner-list_runspy) -- `list_runs.py` directory-truth scan; `--prune` deletes the `RUN_DIR`, `--down` keeps `artifacts/`
- [Suite Driver](REFERENCE.md#suite-driver) -- multi-cell `run_suite.py` (expansion, resume, cascor parallel floor, Grafana env toggle)
- [Suite driver](REFERENCE.md#suite-driver) -- multi-cell campaigns via `util/experiments/run_suite.py` (`--dry-run` / `--resume`; cascor parallel needs launched tree ≥ 0.10.0)
- [Experiment Stats Summary](REFERENCE.md#experiment-stats-summary-ss83) -- how to read `stats.json` / `summary.md` (de-ratified wall, per-poll p50/p95, scrape_confirmed tri-state)
- [Shared-Package CI Workflows](REFERENCE.md#shared-package-ci-workflows) -- the six in-repo `ci-<pkg>.yml` contracts (paths, floors, coverage enforce)
- [Docs Full Check](REFERENCE.md#docs-full-check) -- weekly cross-repo link validation + the `ECOSYSTEM_REPOS` clone-list lockstep
- [Scheduled Security Scan and Lockfile Update](REFERENCE.md#scheduled-security-scan-and-lockfile-update) -- weekly `pip-audit --strict` + the lockfile refresh PR
- [Release-Train Detect Summary and Slack](REFERENCE.md#release-train-detect-summary-and-slack) -- action set vs the ceremonial class, hard-fail banner
- [AGENTS.md Date Check](REFERENCE.md#agentsmd-date-check) -- verifies `**Last Updated**:` was bumped on PRs touching `AGENTS.md`
- [Claude.yml Access Validation](REFERENCE.md#claudeyml-access-validation) -- L2/L3 `ANTHROPIC_API_KEY` safeguards + `DEFAULT_REPOS` fan-out
- [juniper-service-core](REFERENCE.md#juniper-service-core) -- body limit, 429 headers, control-WS sanitizer, `/ws/workers` contracts
- [HTTP Client Base-URL Contract](REFERENCE.md#http-client-base-url-contract) -- shared REST `_normalize_url`, TLS-downgrade pitfall, WS streams still rstrip-only
- [X7 Off-Loop Census](REFERENCE.md#x7-off-loop-census) -- canopy event-loop blocking; count is 58 (canopy#567); the slice-1a gate is authority for `main.py` only (do not quote the v1 name-matching census)
- [Topology Step Order and Blast-Radius IDs](REFERENCE.md#canopy-e2e-topology-step-order-and-blast-radius-ids) -- `topostate` first or alone; the `W4-*` / `W1-12..14` IDs are real matrix §4 steps (F-E2E-007 claimed otherwise and was withdrawn)
- [P4 Campaign Suites](REFERENCE.md#p4-campaign-suites) -- 19 YAML catalog; `include` does not inherit `matrix`; cap-128 H2H is n=2; recurrence P4 cells report, they do not gate
- [Memory-Budget Slack (Planning)](REFERENCE.md#memory-budget-slack-planning) -- `measure-growth` sizes a ceiling; headroom below that figure is not a `Memory Budget` failure
- [F-039 Store Probe](REFERENCE.md#f-039-store-probe) -- apply / soak / report / revert when a canopy store looks empty after a correct wire response; read the whole series; `--target topology` refuses
- [MEMORY.md Index Check](REFERENCE.md#memorymd-index-check) -- local Claude Code index gate; 200/25k silent newest-first truncate; hook-not-line 120 on NEW slugs; CI cannot see `~/.claude`
- [F-CANOPY-037 Render Census](REFERENCE.md#f-canopy-037-render-census) -- 11-session topology-paint instrument; one green session is not a claim; exit 2 = failed to measure
- [X7 Off-Loop Census](REFERENCE.md#x7-off-loop-census) -- canopy event-loop blocking; slice-1a count is **58**; C5 remedy refuted
- [Train / Val / Test Partition Contract](REFERENCE.md#train--val--test-partition-contract) -- shipped NPZ still requires `*_full`; design drops it; recurrence `dataset.split: validation` is exit 2
- [Canopy E2E Dataset Drivers](REFERENCE.md#canopy-e2e-dataset-drivers) -- W6 `--steps` (no ranges; never confirm restart) vs §3.6 `--step`; `LD_LIBRARY_PATH=` + `JuniperCanopy1`
- [Pointer-Follow Soak](REFERENCE.md#pointer-follow-soak) -- unprimed probe loop; do not run n≈8–10; `--force` is an open owner decision; full slugs; `--class` on miss
- [Requirements Snapshot Consolidation](REFERENCE.md#requirements-snapshot-consolidation) -- refresh `notes/requirements/` from `by-area` (never from the ledger); `--check-roundtrip` then `--check-views`
- [Canopy E2E Unfilled-Rows Ledger](REFERENCE.md#canopy-e2e-unfilled-rows-ledger) -- plan matrix re-drives from `e2e_unfilled_rows.py` (status cells), not the TSV estimator
- [juniper-observability README](../juniper-observability/README.md) -- shared observability primitives
- [juniper-data-client Quick Start](https://github.com/pcalnon/juniper-data-client) -- dataset client usage
- [juniper-cascor-client Quick Start](https://github.com/pcalnon/juniper-cascor-client) -- training client usage
- [juniper-cascor-worker Quick Start](https://github.com/pcalnon/juniper-cascor-worker) -- worker setup

---

**Last Updated:** 2026-09-04
**Version:** 0.3.39
**Status:** Active
