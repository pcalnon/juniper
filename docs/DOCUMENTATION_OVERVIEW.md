# Documentation Overview

## Navigation Guide to juniper-ml Documentation

**Version:** 0.2.7
**Status:** Active
**Last Updated:** 2026-08-05
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
| **Run the local host stack**            | [REFERENCE.md](REFERENCE.md#host-orchestration-utilities)                                                                        | docs/    |
| **Reap orphaned Juniper pytest children** | [REFERENCE.md](REFERENCE.md#pytest-orphan-reaper)                                                                              | docs/    |
| **Check installed juniper-* floor drift** | [REFERENCE.md](REFERENCE.md#environment-floor-drift-check)                                                                     | docs/    |
| **Check custom-agent suite health**     | [REFERENCE.md](REFERENCE.md#agent-suite-doctor)                                                                                  | docs/    |
| **Run the isolated E2E trio**           | [Isolated-stack E2E checklist](../notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md) + [REFERENCE — Isolated Stack](REFERENCE.md#isolated-stack-e2e-utilities) | notes/ + docs/ |
| **Run a per-run experiment stack**      | [REFERENCE — Experiment Stack](REFERENCE.md#experiment-stack-utilities) (+ [staging lock release](REFERENCE.md#staging-failure--release_held_locks-open-juniper-ml979)) + [CLI experimentation plan](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) | docs/ + notes/ |
| **Quick-reference dev tasks**           | [DEVELOPER_CHEATSHEET_JUNIPER-ML.md](DEVELOPER_CHEATSHEET_JUNIPER-ML.md)                                                         | docs/    |
| **Operate the PyPI release train**      | [Release-train operator runbook](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md)                 | notes/   |
| **Cut a GitHub Release / archive notes**| [PyPI publish procedure](../notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md)                                 | notes/   |
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
| **REFERENCE.md**                       | Reference  | Extras, compatibility, host-stack / isolated-stack / experiment-stack ops, agent-suite doctor, sibling packages, and release-workflow reference |
| **DEVELOPER_CHEATSHEET_JUNIPER-ML.md** | Cheatsheet | Quick-reference card for common development, host-stack, and experiment-stack tasks              |

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
| **JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md**                             | Procedure   | Cut a GitHub Release + archive `notes/releases/` (mandatory for every PyPI deploy)               |
| **JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md**                                  | Procedure   | Create an isolated git worktree for task work                                                    |
| **JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md**                             | Procedure   | Merge/cleanup after a task (CWD-safe); includes batch stale-worktree sweep                       |
| **JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md**                       | Checklist   | Dedicated data/cascor/canopy E2E trio via `util/isolated_stack.bash` (compose contract also in [REFERENCE](REFERENCE.md#isolated-stack-e2e-utilities)) |
| **JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md** | Plan   | Per-run experiment stack + driver (Waves 2.1–2.7); operator contract in [REFERENCE](REFERENCE.md#experiment-stack-utilities) |
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

- **juniper-data-client** -- [Docs](https://github.com/pcalnon/juniper-data-client) (HTTP client for juniper-data)
- **juniper-cascor-client** -- [Docs](https://github.com/pcalnon/juniper-cascor-client) (HTTP/WS client for juniper-cascor)
- **juniper-cascor-worker** -- [Docs](https://github.com/pcalnon/juniper-cascor-worker) (distributed training worker)
- **juniper-observability** -- [Local docs](../juniper-observability/README.md) (shared health, logging, middleware, Prometheus, and Sentry primitives)
- **juniper-doc-tools** -- [Local docs](../juniper-doc-tools/README.md) (markdown link validator)
- **juniper-ci-tools** -- [Local docs](../juniper-ci-tools/README.md) (dep-docs / coverage-gap / env-drift CLIs)

### Upstream Services

- **juniper-data** -- [Dataset Service](https://github.com/pcalnon/juniper-data)
- **juniper-cascor** -- [Training Service](https://github.com/pcalnon/juniper-cascor)
- **juniper-canopy** -- [Dashboard / control surface](https://github.com/pcalnon/juniper-canopy)

---

**Last Updated:** 2026-08-05
**Version:** 0.2.7
**Maintainer:** Paul Calnon
