# Documentation Overview

## Navigation Guide to juniper-ml Documentation

**Version:** 0.2.35
**Status:** Active
**Last Updated:** 2026-09-04
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
| **Reap orphaned Juniper pytest children** | [REFERENCE.md](REFERENCE.md#pytest-orphan-reaper)                                                                              | docs/    |
| **Check installed juniper-* floor drift** | [REFERENCE.md](REFERENCE.md#environment-floor-drift-check)                                                                     | docs/    |
| **Check custom-agent suite health**     | [REFERENCE.md](REFERENCE.md#agent-suite-doctor)                                                                                  | docs/    |
| **Triage fleet PRs / sequence-safety**  | [REFERENCE.md § Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety)                                 | docs/    |
| **Run the isolated E2E trio**           | [Isolated-stack E2E checklist](../notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md) + [REFERENCE — Isolated Stack](REFERENCE.md#isolated-stack-e2e-utilities) | notes/ + docs/ |
| **Triage Cursor-fleet / predicted-merge PRs** | [REFERENCE — Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety)                            | docs/    |
| **Run a per-run experiment stack**      | [REFERENCE — Experiment Stack](REFERENCE.md#experiment-stack-utilities) (incl. partial-`--up` → `teardown_run`) + [CLI experimentation plan](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) | docs/ + notes/ |
| **Check which generators an env can run** | [REFERENCE — Generator Availability Matrix](REFERENCE.md#generator-availability-matrix-on-host) (gates, mnist/equities install paths, probe one-liner) | docs/    |
| **Attribute snapshots / pin the dataset instance** | [REFERENCE — Snapshot Attribution Dataset Pin](REFERENCE.md#snapshot-attribution-dataset-pin) (`seeded_params`, `--dataset-seed` vs `--seed`, sidecar-chain `--root` trap) | docs/    |
| **Census F-CANOPY-037 topology paint** | [REFERENCE — F-CANOPY-037 Render Census](REFERENCE.md#f-canopy-037-render-census) (11 sessions; structured JSON; `hidden_units==0` is INVALID) | docs/    |
| **Quick-reference dev tasks**           | [DEVELOPER_CHEATSHEET_JUNIPER-ML.md](DEVELOPER_CHEATSHEET_JUNIPER-ML.md)                                                         | docs/    |
| **Operate the PyPI release train**      | [Release-train operator runbook](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md)                 | notes/   |
| **Understand flood CI gates / main-verify** | [REFERENCE.md § Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates) + [flood analysis](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) | docs/ + notes/ |
| **Triage post-merge main-verify / G3.1**| [REFERENCE — Post-Merge Main Verification](REFERENCE.md#post-merge-main-verification) (incl. stable-title failure notify)       | docs/    |
| **Provision YubiKey GPG (ed448 caveat)** | [REFERENCE — YubiKey GPG](REFERENCE.md#yubikey-gpg-provisioning) + [keytocard procedure](../notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md) | docs/ + notes/ |
| **Triage an open-PR budget WARN/ALARM** | [REFERENCE — Open-PR Budget Alarm](REFERENCE.md#open-pr-budget-alarm)                                                            | docs/    |
| **Cut a GitHub Release / archive notes**| [PyPI publish procedure](../notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md)                                 | notes/   |
| **Publish an in-repo shared package**   | [REFERENCE — Sibling publish pipelines](REFERENCE.md#independent-sibling-package-publish-pipelines)                              | docs/    |
| **Understand meta TestPyPI Gate 1**     | [REFERENCE — Meta-Package Publish Pipeline](REFERENCE.md#meta-package-publish-pipeline) (10×6s poll, not `sleep 30`; two-phase verify) | docs/    |
| **Understand why a bare tag push publishes nothing** | [REFERENCE — Independent Sibling Package Publish Pipelines](REFERENCE.md#independent-sibling-package-publish-pipelines) (trigger is the gate; #555 / #1310) | docs/    |
| **Debug shared-package subdirectory CI**| [REFERENCE — Shared-Package CI Workflows](REFERENCE.md#shared-package-ci-workflows)                                              | docs/    |
| **Operate weekly docs-full-check**      | [REFERENCE — Docs Full Check](REFERENCE.md#docs-full-check)                                                                     | docs/    |
| **Understand weekly security / lockfile hygiene** | [REFERENCE — Scheduled Security Scan and Lockfile Update](REFERENCE.md#scheduled-security-scan-and-lockfile-update)     | docs/    |
| **Triage CodeQL / `Analyze (python)`** | [REFERENCE — CodeQL Analysis](REFERENCE.md#codeql-analysis) (SHA group, `merge_group` divergence, review-thread stall) | docs/    |
| **Read the release-train detect summary / Slack** | [REFERENCE — Detect Summary and Slack](REFERENCE.md#release-train-detect-summary-and-slack)                             | docs/    |
| **Understand the AGENTS.md date check** | [REFERENCE — AGENTS.md Date Check](REFERENCE.md#agentsmd-date-check)                                                             | docs/    |
| **Audit `claude.yml` access safeguards**| [REFERENCE — Claude.yml Access Validation](REFERENCE.md#claudeyml-access-validation) + [ANTHROPIC API key walkthrough](../notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md) | docs/ + notes/ |
| **Operate the GitHub `@claude` assistant** | [REFERENCE — Claude Code Action](REFERENCE.md#claude-code-action) (live pin, `@claude` `if:`, template-snapshot drift) | docs/ |
| **Debug service-core middleware / control-WS / workers** | [REFERENCE — juniper-service-core](REFERENCE.md#juniper-service-core)                                           | docs/    |
| **Create or clean a worktree**          | [Worktree setup](../notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md) / [cleanup V2](../notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md) | notes/ |
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
| **REFERENCE.md**                       | Reference  | Extras, compatibility, host-stack / isolated-stack / experiment-stack ops, agent-suite doctor, post-merge main-verify, YubiKey GPG pointer, fleet triage / sequence-safety, shared-package CI + publish pipelines (Gate 1 poll; release-only trigger), scheduled security-scan / lockfile-update, docs-full-check, release-train detect summary, AGENTS.md date check, `claude.yml` access validation, Claude Code Action (`@claude` assistant), sibling packages (incl. service-core), release-workflow, flood CI gates, and open-PR budget alarm |
| **DEVELOPER_CHEATSHEET_JUNIPER-ML.md** | Cheatsheet | Quick-reference card for common development, host-stack, CI guardrail and hygiene tasks, signing-ceremony tasks, service-core contracts, and experiment-stack tasks |
| **REFERENCE.md**                       | Reference  | Extras, compatibility, host-stack / isolated-stack / experiment-stack ops, Duplicati backup, agent-suite doctor, post-merge main-verify, YubiKey GPG, fleet triage / sequence-safety, shared-package CI + publish, security-scan / lockfile, docs-full-check, release-train detect, AGENTS.md date check, `claude.yml` access, sibling packages (incl. service-core), flood CI gates, and open-PR budget alarm |
| **DEVELOPER_CHEATSHEET_JUNIPER-ML.md** | Cheatsheet | Quick-reference card for common development, host-stack, backup-lane, CI guardrail and hygiene tasks, signing-ceremony tasks, service-core contracts, and experiment-stack tasks |

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
| **JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md**                     | Runbook     | Modes (`off`/`report`/`propose`/`ceremony`), Gate 1/2 review, HALTs, App-token setup             |
| **JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md**              | Procedure   | YubiKey 5 ed448 `keytocard` root cause + validated ed25519/cv25519 transfer (pointer in [REFERENCE](REFERENCE.md#yubikey-gpg-provisioning)) |
| **JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md**                  | Findings    | Why the July restore points are gone; scheduled lane is the replacement (pointer in [REFERENCE](REFERENCE.md#scheduled-duplicati-backup-lane)) |
| **JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md**          | Investigation | GPGFlushError / Duplicati GPG wrapper; not a reason to drop `--no-auto-compact` |
| **JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md**                      | Analysis    | Flood remediation (§4 item 9 = open-PR budget alarm; operator surface in [REFERENCE](REFERENCE.md#open-pr-budget-alarm)) |
| **JUNIPER_2026-07-30_JUNIPER-ML_CURSOR-DASHBOARD-CONFIG-REQUESTS.md**                          | Requests    | Source-side Cursor dashboard caps (companion to the repo budget alarm)                           |
| **JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md**    | Walkthrough | L2/L3 `claude.yml` safeguards + `validate_claude_yaml_access.bash`; `DEFAULT_REPOS` fan-out in [REFERENCE](REFERENCE.md#claudeyml-access-validation); live pin in [Claude Code Action](REFERENCE.md#claude-code-action) |
| **JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md**                             | Procedure   | Cut a GitHub Release + archive `notes/releases/` (mandatory for every PyPI deploy)               |
| **JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md**                                  | Procedure   | Create an isolated git worktree for task work                                                    |
| **JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md**                             | Procedure   | Merge/cleanup after a task (CWD-safe); includes batch stale-worktree sweep                       |
| **JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md**                       | Checklist   | Dedicated data/cascor/canopy E2E trio via `util/isolated_stack.bash` (compose contract also in [REFERENCE](REFERENCE.md#isolated-stack-e2e-utilities)) |
| **JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md** | Plan   | Per-run experiment stack + driver (Waves 2.1–2.7); operator contract + partial-`--up` teardown in [REFERENCE](REFERENCE.md#experiment-stack-utilities) |
| **JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md**                       | Findings    | Attribution floors + why the dataset instance must be pinned; operator surface in [REFERENCE](REFERENCE.md#snapshot-attribution-dataset-pin) |
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
**Version:** 0.2.35
**Maintainer:** Paul Calnon
