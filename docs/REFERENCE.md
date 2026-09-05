# Reference

## juniper-ml Technical Reference

**Version:** 0.6.59
**Status:** Active
**Last Updated:** 2026-09-05
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Package Overview](#package-overview)
- [Extras Reference](#extras-reference)
- [Ecosystem Compatibility](#ecosystem-compatibility)
- [HTTP Client Base-URL Contract](#http-client-base-url-contract)
- [Host Orchestration Utilities](#host-orchestration-utilities)
- [Scheduled Duplicati Backup Lane](#scheduled-duplicati-backup-lane)
- [Juniper Project-Tree Backup](#juniper-project-tree-backup)
- [Editable Install Drift Check](#editable-install-drift-check)
- [Cascor Primary Freeze Tell](#cascor-primary-freeze-tell)
- [Pytest Orphan Reaper](#pytest-orphan-reaper)
- [Pointer-Follow Soak](#pointer-follow-soak)
- [Environment Floor Drift Check](#environment-floor-drift-check)
- [Conda Env Torch Shadow Diagnostic (P-5)](#conda-env-torch-shadow-diagnostic-p-5)
- [Agent Suite Doctor](#agent-suite-doctor)
- [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities)
- [F-039 Store Probe](#f-039-store-probe)
- [Canopy E2E Matrix Writes](#canopy-e2e-matrix-writes)
- [F-CANOPY-027 Poller Starvation Probes](#f-canopy-027-poller-starvation-probes)
- [Canopy E2E Finding Triage](#canopy-e2e-finding-triage)
- [Canopy E2E Topology Driver](#canopy-e2e-topology-driver)
- [Canopy E2E Dataset Drivers](#canopy-e2e-dataset-drivers)
- [Canopy E2E Unfilled-Rows Ledger](#canopy-e2e-unfilled-rows-ledger)
- [Fleet Triage and Sequence Safety](#fleet-triage-and-sequence-safety)
- [Resident-Hazard Gap Triage](#resident-hazard-gap-triage)
- [Ruleset Context Audit](#ruleset-context-audit)
- [Worktree Divergence Is a Memory Cost](#worktree-divergence-is-a-memory-cost)
- [Post-Merge Main Verification](#post-merge-main-verification)
- [Experiment Stack Utilities](#experiment-stack-utilities)
- [PF Scenario Suites](#pf-scenario-suites)
- [Perf-Lane Work Gate](#perf-lane-work-gate)
- [Perf-lane metrics and baselines](#perf-lane-metrics-and-baselines)
- [Perf-Lane Split Comparator](#perf-lane-split-comparator)
- [Suite Report Gate Inputs](#suite-report-gate-inputs)
- [CSV Import Byte Cap](#csv-import-byte-cap)
- [Snapshot Sidecar Chain](#snapshot-sidecar-chain)
- [Suite Driver](#suite-driver)
- [Recurrence Work Is Not Countable](#recurrence-work-is-not-countable)
- [Experiment Stats Summary (SS8.3)](#experiment-stats-summary-ss83)
- [Run lister / pruner (`list_runs.py`)](#run-lister--pruner-list_runspy)
- [Snapshot Attribution Dataset Pin](#snapshot-attribution-dataset-pin)
- [P4 Campaign Suites](#p4-campaign-suites)
- [X7 Off-Loop Census](#x7-off-loop-census)
- [Canopy E2E Topology Step Order and Blast-Radius IDs](#canopy-e2e-topology-step-order-and-blast-radius-ids)
- [MEMORY.md Index Check](#memorymd-index-check)
- [F-CANOPY-037 Render Census](#f-canopy-037-render-census)
- [Train / Val / Test Partition Contract](#train--val--test-partition-contract)
- [Requirements Snapshot Consolidation](#requirements-snapshot-consolidation)
- [Shared-Package CI Workflows](#shared-package-ci-workflows)
- [F-CANOPY-037 Render Census](#f-canopy-037-render-census)
- [Docs Full Check](#docs-full-check)
- [Defect Register Close Protocol](#defect-register-close-protocol)
- [Scheduled Security Scan and Lockfile Update](#scheduled-security-scan-and-lockfile-update)
- [Equities Symbol Cap](#equities-symbol-cap)
- [Release-Train Detect Summary and Slack](#release-train-detect-summary-and-slack)
- [AGENTS.md Date Check](#agentsmd-date-check)
- [Claude.yml Access Validation](#claudeyml-access-validation)
- [Claude Code Action](#claude-code-action)
- [CodeQL Analysis](#codeql-analysis)
- [Required-Context Ruleset Writer](#required-context-ruleset-writer)
- [Ruleset Scope Guard](#ruleset-scope-guard)
- [Sibling Packages](#sibling-packages)
- [Version History](#version-history)
- [Build and Release](#build-and-release)
- [Flood-Remediation CI Gates](#flood-remediation-ci-gates)
- [YubiKey GPG Provisioning](#yubikey-gpg-provisioning)
- [Open-PR Budget Alarm](#open-pr-budget-alarm)
- [Memory File Size Budget](#memory-file-size-budget)
- [Memory-Budget Slack (Planning)](#memory-budget-slack-planning)

---

## Package Overview

`juniper-ml` is a meta-package with zero base dependencies and no importable Python modules. It exists solely to provide optional dependency groups for installing Juniper ecosystem packages.

| Field                  | Value        |
|------------------------|--------------|
| **PyPI Name**          | `juniper-ml` |
| **Version**            | `0.6.0`      |
| **Python**             | `>=3.12`     |
| **Base Dependencies**  | None         |
| **Importable Modules** | None         |

---

## Extras Reference

### Available Extras

| Extra       | Packages Installed                                                                       | Min Version       |
|-------------|------------------------------------------------------------------------------------------|-------------------|
| `clients`   | `juniper-data-client`                                                                    | `>=0.4.1`         |
|             | `juniper-cascor-client`                                                                  | `>=0.5.0`         |
| `worker`    | `juniper-cascor-worker`                                                                  | `>=0.4.0`         |
| `servers`   | `juniper-canopy`                                                                         | `>=0.5.0`         |
|             | `juniper-cascor`                                                                         | `>=0.5.0`         |
|             | `juniper-data`                                                                           | `>=0.6.0`         |
| `tools`     | `juniper-ci-tools`                                                                       | `>=0.1.0`         |
|             | `juniper-config-tools`                                                                   | `>=0.1.0,<0.2.0`  |
|             | `juniper-doc-tools`                                                                      | `>=0.1.0,<0.2.0`  |
|             | `juniper-model-core`                                                                     | `>=0.1.0,<0.4.0`  |
|             | `juniper-observability`                                                                  | `>=0.2.0`         |
|             | `juniper-service-core`                                                                   | `>=0.2.0,<0.8.0`  |
| `doc-tools` | `juniper-doc-tools` (back-compat alias for the doc-tools entry in `tools`)               | `>=0.1.0,<0.2.0`  |
| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.1.5,<0.3.0`  |
|             | `juniper-recurrence`                                                                     | `>=0.2.0,<0.5.0`  |
|             | `juniper-recurrence-client`                                                              | `>=0.2.0,<0.3.0`  |
| `all`       | All packages from `clients` + `worker` + `servers` + `tools` + `recurrence`              | --                |

### Installation Commands

```bash
pip install juniper-ml[clients]   # Data + CasCor HTTP/WS clients
pip install juniper-ml[worker]    # Distributed training worker
pip install juniper-ml[servers]   # Canopy + Cascor + Data services
pip install juniper-ml[tools]     # CI/doc tools + model-core + observability + service-core
pip install juniper-ml[doc-tools] # Markdown link validator only (back-compat alias)
pip install juniper-ml[recurrence]# Δt-native LMU model + FastAPI app + HTTP client
pip install juniper-ml[all]       # Everything
```

> **Extras lint contract (two gates).** Any edit to `[project.optional-dependencies]` in `pyproject.toml` must co-update, in the **same PR**:
>
> 1. `tests/test_pyproject_extras.py` `EXPECTED_EXTRAS` — schema + pin-string contract (`PyprojectExtrasTest`).
> 2. Documented extras tables in `AGENTS.md`, `README.md`, `docs/QUICK_START.md`, and this section — pin strings must match `pyproject.toml` **exactly** (`ExtrasDocsLockstepTest`, juniper-ml#907).
>
> `PyprojectExtrasTest` already fails Regression Tests on `EXPECTED_EXTRAS` drift. After juniper-ml#907 merges, `ExtrasDocsLockstepTest` also fails when a docs table drifts. Dependabot-only pin bumps update neither surface; a human must co-update both (juniper-ml#905 / #907).
>
> **Parser constraints (lockstep gate):** inline tables (AGENTS / README / QUICK_START) must put the full pin in backticks (`juniper-foo>=X,<Y`); this REFERENCE table uses a separate pin-spec column (`` `>=X,<Y` ``). Omitting a package row or leaving a stale ceiling (the historical `service-core<0.3.0` class) is what the gate catches.

### Package Descriptions

| Package                   | Purpose                                                                                          |
|---------------------------|--------------------------------------------------------------------------------------------------|
| **juniper-canopy**        | Real-time monitoring dashboard (Dash/FastAPI) for training dynamics                              |
| **juniper-cascor**        | Cascade-Correlation training service (REST + WebSocket)                                          |
| **juniper-data**          | Dataset-generation REST service (FastAPI)                                                        |
| **juniper-data-client**   | Synchronous HTTP client for the juniper-data REST API (dataset generation)                       |
| **juniper-cascor-client** | Synchronous HTTP + async WebSocket client for the juniper-cascor API (training)                  |
| **juniper-cascor-worker** | Remote candidate training worker using multiprocessing IPC                                       |
| **juniper-ci-tools**      | Dependency-documentation generator (`juniper-generate-dep-docs`) used by every Juniper repo's CI |
| **juniper-config-tools**  | Env-prefix migration helpers (stdlib-only)                                                       |
| **juniper-doc-tools**     | Markdown link validator (`juniper-check-doc-links`) for intra- and cross-repo docs               |
| **juniper-model-core**    | Model-core conformance kit + crossval layer                                                      |
| **juniper-observability** | Shared Prometheus collector helpers, structured-JSON logging, Starlette middleware               |
| **juniper-service-core**  | Shared FastAPI service-tier primitives                                                           |
| **juniper-recurrence-model** | Closed-form variable-Δt LMU regressor library                                                 |
| **juniper-recurrence**    | FastAPI/CLI application wrapping the recurrence model                                            |
| **juniper-recurrence-client** | HTTP client for the juniper-recurrence service                                               |

---

## Ecosystem Compatibility

`juniper-ml` 0.6.0 declares the following pins. Every package below ships from PyPI; servers and tools land under their own extras, clients and worker keep their existing groups.

| juniper-ml | juniper-data | juniper-cascor | juniper-canopy | juniper-data-client | juniper-cascor-client | juniper-cascor-worker | juniper-ci-tools | juniper-doc-tools  | juniper-observability |
|------------|--------------|----------------|----------------|---------------------|-----------------------|-----------------------|------------------|--------------------|-----------------------|
| 0.6.x      | >=0.6.0      | >=0.5.0        | >=0.5.0        | >=0.4.1             | >=0.5.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.2.0               |

### Service Ports

`juniper-cascor` has two commonly visible ports: the service/container default is `8200`, while the host-level Juniper stack and Docker published port use `8201`. Local utilities in this repository target the host-facing port.

| Service                  | Service / Container Port | Host-Facing Port | Health Endpoint             |
|--------------------------|--------------------------|------------------|-----------------------------|
| juniper-data             | 8100                     | 8100             | `/v1/health`                |
| juniper-cascor           | 8200                     | 8201             | `/v1/health`                |
| juniper-canopy           | 8050                     | 8050             | `/v1/health`                |
| juniper-cascor-worker    | n/a                      | 8210             | `/v1/health/ready`          |

#### Startup port overrides (juniper-deploy)

Every published host port is settable **at startup via an environment variable**, so no Juniper port
is hard-coded into an image. The defaults below are the Juniper-specific values declared in the
project tree (`juniper-deploy/docker-compose.yml`); export the variable to override.

| Service       | Host port default | Startup env var        | Bind host                |
|---------------|-------------------|------------------------|--------------------------|
| juniper-cascor      | `8201`      | `CASCOR_HOST_PORT`     | `${BIND_HOST:-127.0.0.1}` |
| juniper-recurrence  | `8211`      | `RECURRENCE_HOST_PORT` | `${BIND_HOST:-127.0.0.1}` |
| juniper-canopy      | `8050`      | `CANOPY_PORT`          | `${BIND_HOST:-127.0.0.1}` |
| Grafana             | `3001`      | `GRAFANA_HOST_PORT`    | `${BIND_HOST:-127.0.0.1}` |
| Prometheus          | `9090`      | `PROMETHEUS_HOST_PORT` | `${BIND_HOST:-127.0.0.1}` |

Notes, and two gaps worth knowing before you rely on this table:

- **Grafana defaults to `3001`, not `3000`, deliberately.** `docker-compose.yml:921-931` records why:
  port `3000` is commonly held by a system-installed Grafana or another agent. On the development
  host it is held by an unrelated Domotz agent — see
  [the F-P1-2 closure evidence](../notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_F-P1-2-GRAFANA-RENDER-CLOSURE-EVIDENCE.md).
  Do not "fix" this back to `3000`.
- **Both former gaps are now closed** (juniper-deploy #183 and #186, 2026-08-18). Prometheus
  previously published a literal `127.0.0.1:9090:9090` with **no** environment variable — the one
  service whose host port could not be set at startup — and the monitoring tier pinned `127.0.0.1`
  literally while the application tier honoured `${BIND_HOST}`, so one variable did not move the
  whole stack. Both now follow the same pattern as every other service. Defaults are unchanged:
  with nothing set, every port still binds loopback on the values above.
- `juniper-data` publishes no host port in the default compose profile — it is reached over the
  compose network. The host-level `juniper_plant_all.bash` stack is what exposes `8100`.
- Experiment runs never use any port in this table; they draw from the disjoint ranges in
  [Experiment Stack Utilities](#experiment-stack-utilities) (data `8110-8139`, cascor `8230-8259`,
  recurrence `8260-8289`).

### Rate Limiting Defaults

The three services intentionally ship with **different** `rate_limit_enabled` defaults — `juniper-data` enables rate limiting out of the box; `juniper-cascor` and `juniper-canopy` leave it disabled by default for local-dev ergonomics. The per-minute threshold is uniform across services (60 req/min), so only the enable flag varies.

| Service          | `rate_limit_enabled` default | `rate_limit_requests_per_minute` default | Source                                                                  |
|------------------|------------------------------|------------------------------------------|-------------------------------------------------------------------------|
| `juniper-data`   | **`True`**                   | `60`                                     | `juniper-data/juniper_data/api/settings.py:151-152` (sentinel-defined)  |
| `juniper-cascor` | `False`                      | `60`                                     | `juniper-cascor/src/api/settings.py:208-209` (sentinel-defined)         |
| `juniper-canopy` | `False`                      | `60`                                     | `juniper-canopy/src/settings.py:164-165` (literal-defined)              |

**Production**: enable rate limiting on every service. Each service's pydantic `Settings` class picks the value up from its own prefixed env var via `env_prefix`:

| Service          | Enable env var                       | Per-minute env var                                |
|------------------|--------------------------------------|---------------------------------------------------|
| `juniper-data`   | `JUNIPER_DATA_RATE_LIMIT_ENABLED`    | `JUNIPER_DATA_RATE_LIMIT_REQUESTS_PER_MINUTE`     |
| `juniper-cascor` | `JUNIPER_CASCOR_RATE_LIMIT_ENABLED`  | `JUNIPER_CASCOR_RATE_LIMIT_REQUESTS_PER_MINUTE`   |
| `juniper-canopy` | `JUNIPER_CANOPY_RATE_LIMIT_ENABLED`  | `JUNIPER_CANOPY_RATE_LIMIT_REQUESTS_PER_MINUTE`   |

The split-default is intentional, not an oversight: `juniper-data` is a higher-risk, public-facing surface (dataset generation, paginated reads), so it ships rate-limited by default; the other two run behind a known reverse proxy / authenticated client surface, where the rate-limit value adds operator friction during local development. Closes the documentation gap tracked in the v7 outstanding-development roadmap under CFG-08.

---

## HTTP Client Base-URL Contract

The three separately released HTTP clients — `juniper-data-client`, `juniper-cascor-client`, and `juniper-recurrence-client` — now share one REST `base_url` treatment. That closes defect-register `APD-DCLIENT-004` / `APD-CCLIENT-005` (sibling PRs [data-client#165](https://github.com/pcalnon/juniper-data-client/pull/165) + [#166](https://github.com/pcalnon/juniper-data-client/pull/166), [cascor-client#129](https://github.com/pcalnon/juniper-cascor-client/pull/129), [recurrence#129](https://github.com/pcalnon/juniper-recurrence/pull/129)). Register status is recorded by open [juniper-ml#1331](https://github.com/pcalnon/juniper-ml/pull/1331).

**This is GitHub-main of those clients, not a `juniper-ml` extra floor.** `[clients]` still pins `juniper-data-client>=0.4.1` and `juniper-cascor-client>=0.5.0`; the latest *released* data-client wheel is `0.4.2` (2026-06-18) and still lacks the host guard. `pip install juniper-ml[clients]` can resolve a wheel that silently accepts `HTTPS://host` (TLS downgrade) or a hostless URL. Confirm `JuniperDataConfigurationError` / `JuniperCascorConfigurationError` exist before relying on the fail-fast path.

### What REST constructors do

`JuniperDataClient`, `JuniperCascorClient`, and `JuniperRecurrenceClient` run `_normalize_url` on the constructor `base_url` (defaults: data `http://localhost:8100`, cascor REST `http://localhost:8200`). Steps, in order:

1. `str.strip()`
2. If the value does **not** case-insensitively start with `http://` or `https://`, prefix `http://`. A case-sensitive check re-prefixed `HTTPS://host` into `http://HTTPS://host` — silent TLS downgrade, API key sent to hostname `https`.
3. `urllib.parse.urlparse`. Empty **`hostname`** (not `netloc`) raises the client's configuration error: `base_url must include a host; got {url!r}` with `status_code=None`. `netloc` is truthy for userinfo-only `http://user:secret@` while `hostname` is `None`.
4. Rebuild `{scheme}://{netloc}{path}`, `rstrip("/")`, then strip a trailing `/v1`.

Cascor REST then sets `api_url = f"{self.base_url}{API_VERSION_PATH}"` (`/v1`). Stripping the suffix is what stops a caller-supplied `…/v1` from becoming `…/v1/v1`.

Each configuration error subclasses that client's base (`JuniperDataClientError`, `JuniperCascorClientError`, `JuniperRecurrenceClientError`), so existing `except Juniper*ClientError` handlers still catch a hostless URL.

```python
from juniper_data_client import JuniperDataClient
from juniper_data_client.exceptions import JuniperDataConfigurationError
from juniper_cascor_client import JuniperCascorClient

JuniperDataClient("http://localhost:8100")       # unchanged
JuniperDataClient("localhost:8100")              # → http://localhost:8100
JuniperDataClient("HTTPS://data.example/v1/")    # → https://data.example  (scheme lowercased, /v1 stripped)
JuniperDataClient("http://")                     # raises JuniperDataConfigurationError

cascor = JuniperCascorClient("http://localhost:8200/v1")
assert cascor.base_url == "http://localhost:8200"
assert cascor.api_url == "http://localhost:8200/v1"
```

Hostless shapes that raise (pinned in each client's constructor tests): `""`, whitespace-only, `http://`, `https://`, `/v1`, `http:///v1`, `http://user:secret@`.

### Deliberately not covered

| Surface | URL treatment | Why |
|---------|---------------|-----|
| `CascorTrainingStream` / `CascorControlStream` | `base_url.rstrip("/")` only | `ws://` / `wss://` defaulting is a different scheme family; no register row names them. Default `ws://localhost:8200`. |
| `FakeCascorClient` / `FakeCascorTrainingStream` | `rstrip("/")` only | Test doubles; they do not run `_normalize_url`. |

### Remaining sibling drift (retries)

Base-URL normalisation/validation is aligned. The last sibling-package retry drift is still open: `juniper-cascor-client` `RETRY_ALLOWED_METHODS` is `GET` / `POST` / `DELETE` / `PUT` / `PATCH` (`APD-CCLIENT-001`). `juniper-data-client` retries `HEAD` / `GET` / `PUT`; `juniper-recurrence-client` retries `HEAD` / `GET` only. Do not assume a failed cascor `POST` was not retried.

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| `Juniper*ConfigurationError: base_url must include a host` | Constructor got `""`, `http://`, `/v1`, or `http://user:secret@`. Fix the URL; this is not a retryable transport error. |
| `HTTPS://host` talks HTTP / hostname is `https` | Wheel predates the case-insensitive scheme check. Install from GitHub main of the client, or wait for the next PyPI release past data-client `0.4.2` / cascor-client `0.7.0`. |
| Cascor REST to `:8200` on the host stack | Constructor default is the **container** port. Host `plant_all` / Docker publish `:8201` — pass `base_url="http://localhost:8201"`. |
| WS stream accepts a hostless / schemeless URL | Expected. REST `_normalize_url` is not applied to `CascorTrainingStream` / `CascorControlStream`. |
| Catch-all `except Exception` around client init | Configuration errors subclass the client base, but a bare `Exception` handler will swallow a hostless URL as if the service were down. |

---

## Host Orchestration Utilities

`util/juniper_plant_all.bash` starts the host-level stack in dependency order (`juniper-data`, then `juniper-cascor`, then `juniper-canopy`, then `juniper-cascor-worker`), waits for health checks, and writes `JuniperProject.pid` for `util/juniper_chop_all.bash`.

Prerequisites:

- Sibling repositories are expected next to `juniper-ml` under the same Juniper project root: `juniper-data`, `juniper-cascor`, `juniper-canopy`, and `juniper-cascor-worker`.
- `nohup` mode preflight requires both `curl` and `ss` on `PATH` (hard exit if either is missing). Health polls use `curl`; port preflight uses `ss`.
- Conda must be available at `JUNIPER_CONDA_DIR` (default `/opt/miniforge3`) with `JuniperData`, `JuniperCascor1`, and `JuniperCanopy1` environments. The cascor server and worker both default to `JuniperCascor1`.
- The worker console script must exist at `${JUNIPER_CONDA_DIR}/envs/${JUNIPER_WORKER_CONDA}/bin/juniper-cascor-worker`.

| Utility | Purpose | Key Overrides |
|---------|---------|---------------|
| `util/juniper_plant_all.bash` | Start the host-level stack with health gates | `JUNIPER_DATA_HOST`, `JUNIPER_DATA_PORT`, `JUNIPER_CASCOR_HOST`, `JUNIPER_CASCOR_PORT`, `JUNIPER_CANOPY_PORT`, `JUNIPER_WORKER_HEALTH_HOST`, `JUNIPER_WORKER_HEALTH_PORT` |
| `util/juniper_chop_all.bash` | Stop services from `JuniperProject.pid` | `JUNIPER_PROJECT_DIR`, `SIGTERM_TIMEOUT`, `KILL_WORKERS`, `USE_SYSTEMD` (`JUNIPER_CHOP_PROC_ROOT` is tests-only) |
| `util/get_cascor_*.bash` | Query cascor REST endpoints from a shell | `CASCOR_HOST`, `CASCOR_PORT` |

Important pitfall: the startup script uses the `JUNIPER_CASCOR_HOST` / `JUNIPER_CASCOR_PORT` names, but the `get_cascor_*.bash` query helpers intentionally use the shorter legacy `CASCOR_HOST` / `CASCOR_PORT` names. Both default to `localhost:8201` for local host-mode access.

```bash
JUNIPER_CASCOR_PORT=8201 util/juniper_plant_all.bash
CASCOR_PORT=8201 util/get_cascor_status.bash
util/juniper_chop_all.bash
```

Query helpers:

| Script                              | Endpoint                        |
|-------------------------------------|---------------------------------|
| `util/get_cascor_status.bash`       | `/v1/training/status`           |
| `util/get_cascor_metrics.bash`      | `/v1/metrics`                   |
| `util/get_cascor_history.bash`      | `/v1/metrics/history?count=10`  |
| `util/get_cascor_history-plus.bash` | `/v1/metrics/history?count=100` |
| `util/get_cascor_network.bash`      | `/v1/network`                   |
| `util/get_cascor_topology.bash`     | `/v1/network/topology`          |

Lifecycle details:

- In `nohup` mode, `plant_all` writes one `name=pid` entry per service to `juniper-ml/JuniperProject.pid`; `chop_all` reads that file, **validates each PID against `/proc/<pid>/cmdline`**, then sends `SIGTERM` and escalates to `SIGKILL` after `SIGTERM_TIMEOUT` seconds if needed. Legacy `name: pid` lines are still accepted (see [non-empty pidfile stop path](#non-empty-pidfile-stop-path-validate_pid)).
- In systemd mode (`--systemd` or `USE_SYSTEMD=1`), both scripts call `systemctl --user` for `juniper-data`, `juniper-cascor`, `juniper-canopy`, and `juniper-cascor-worker`. This mode does not use `JuniperProject.pid` and only preflight-checks `curl` (not `ss` / port availability).
- `plant_all` derives the Juniper project root from the script location (`util/` -> repository -> parent directory). `chop_all` honors `JUNIPER_PROJECT_DIR` directly instead of deriving it from the checkout, so non-standard layouts must stop with the same root explicitly set, for example `JUNIPER_PROJECT_DIR=/path/to/Juniper util/juniper_chop_all.bash`.
- Default data bind is loopback: `JUNIPER_DATA_HOST` defaults to `127.0.0.1` (export `0.0.0.0` only when you intentionally want all-interfaces). See [`notes/JUNIPER_2026-07-06_JUNIPER-ECOSYSTEM_LAUNCH-PATH-BIND-AUDIT.md`](../notes/JUNIPER_2026-07-06_JUNIPER-ECOSYSTEM_LAUNCH-PATH-BIND-AUDIT.md) (SEC-F28).

Failure/health/port contract (`nohup` mode):

- After each successful `nohup` launch, the PID is appended to `STARTED_PIDS`. An `ERR` trap runs `cleanup_on_failure` (JR-ML-SEC-042): SIGTERM every tracked PID, wait 3s, SIGKILL any survivors, `rm -f` the project pidfile, then exit 1 — even when `STARTED_PIDS` is still empty (preflight/early-failure).
  - **The pidfile removal is skipped in systemd mode** (2026-08-23). The `ERR` trap is armed *before* the systemd branch, so a failed `--systemd` plant used to delete a pidfile it never wrote — one belonging to a **nohup** stack that was very likely still running, stranding those services with no PID record to chop them by and removing one of the orphan reaper's two protection keys. The guard is inside `cleanup_on_failure` rather than fixed by moving the trap, deliberately: the trap must still fire in systemd mode so a failed plant aborts with exit 1. Gate: `tests/test_juniper_plant_all.py` `TestSystemdCleanupLeavesNohupPidfile`.
- `wait_for_health` polls `curl -sf` every `HEALTH_CHECK_INTERVAL` seconds (default `2`) until success or `HEALTH_CHECK_TIMEOUT` (default `60`). Timeout returns 1 and trips the ERR cleanup above; it does not hang forever.
- `check_port_available` rejects a busy port (exit 1). If `ss` is missing or unusable when the helper runs, it **fail-opens** (treats the port as free). The `nohup` preflight still hard-requires `ss`, so normal host-mode plant never relies on that fail-open; hermetic tests and any out-of-band caller of the helper can.
- In systemd mode (`--systemd` or `USE_SYSTEMD=1`), both scripts call `systemctl --user` for the same four units and **never** read or write `JuniperProject.pid`. See [systemd mode](#systemd-mode) below.

#### Health-check interval clamp (juniper-ml#782)

`wait_for_health` polls `curl -sf` and advances `elapsed` by the poll interval each loop (default `HEALTH_CHECK_INTERVAL=2`, timeout `HEALTH_CHECK_TIMEOUT=60`). An interval `<= 0` never advances `elapsed` (`sleep 0` is a no-op) and busy-loops forever — including `HEALTH_CHECK_INTERVAL=0` or a zero/invalid 4th argument.

Post-[#782](https://github.com/pcalnon/juniper-ml/pull/782): if the interval is not a positive integer (`^[1-9][0-9]*$`), plant logs `WARNING: invalid health-check interval … clamping to 1s` and use `1`. Prefer the default `2`. Do **not** set `HEALTH_CHECK_INTERVAL=0` to "poll as fast as possible" — that was the busy-loop class. Coverage: `tests/test_juniper_plant_all.py` (`TestWaitForHealth`).

#### Conda activate nounset (`safe_conda_activate`)

Host-mode `plant_all` runs under `set -euo pipefail`. Each service activate goes through `safe_conda_activate`, which temporarily disables nounset because conda activation scripts (for example `activate-binutils_linux-64.sh`) may reference unset variables such as `ADDR2LINE`.

**Contract:** `set +u` → `conda activate <env>` → `set -u`. The restore arm must be `set -u` (not a second `set +u`). A one-character restore mistake silently leaves nounset off for the rest of bring-up — the same class that bit `util/isolated_stack.bash` before [#785](https://github.com/pcalnon/juniper-ml/pull/785). Isolated-stack's `activate_conda` must match this plant contract.

**Fail-closed under OR-list callers.** Bash disables `set -e` inside a function invoked as `fn || …`. Today's plant call sites are bare (`safe_conda_activate "${ENV}"` under `set -e`), but the helper itself must still propagate an activate failure so a future absorber — or any harness that OR-lists it — cannot mask the failure as exit `0` and launch the next service on the **ambient PATH** (wrong interpreter / missing editable). The helper therefore restores nounset on **both** arms:

```bash
set +u
if ! conda activate "${env_name}"; then
    set -u
    echo "ERROR: conda activate '${env_name}' failed" >&2
    return 1
fi
set -u
```

Same class as isolated-stack `activate_conda` and the `experiment_stack.bash` OR-list absorb.

```bash
# Confirm both arms (expect: if ! conda activate … / set -u / return 1, then trailing set -u)
rg -n -A12 '^safe_conda_activate' util/juniper_plant_all.bash
```

Coverage: open juniper-ml#795 (`tests/test_juniper_plant_all.py` — `TestSafeCondaActivate`).

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Port preflight fails | Run `ss -tlnp` and free the reported port (`8100`, `8201`, `8050`, or `8210` by default), or override the matching `JUNIPER_*_PORT` before startup. |
| Mid-plant health timeout/abort | Read the failing service log under that repo's `logs/`. `cleanup_on_failure` already tried SIGTERM→SIGKILL on `STARTED_PIDS` and removed `JuniperProject.pid`. Confirm nothing is still listening (`ss -tlnp`) before re-planting; do not expect `chop_all` to find a pidfile after a failed plant. |
| `juniper-cascor` never reaches `/v1/health` | Inspect `juniper-cascor/logs/juniper-cascor_*.log`. If it dies on `import torch`, run `util/check_conda_env_torch.bash` before flipping `JUNIPER_CASCOR_CONDA` (exit **2** = P-5 FT; **4** = May-7). Prefer `JuniperCascor1`. See [Conda Env Torch Shadow](#conda-env-torch-shadow-diagnostic-p-5). |
| Worker startup says binary missing | Activate the worker env and install the package: `conda activate JuniperCascor1 && pip install juniper-cascor-worker`. |
| `chop_all` cannot find `JuniperProject.pid` | Confirm `plant_all` completed successfully in `nohup` mode and check the PID path printed at startup (`${JUNIPER_PROJECT_DIR}/juniper-ml/JuniperProject.pid`). Missing **and** empty (zero-byte) files both abort before the service-stop loop — see below. In non-standard layouts, rerun with `JUNIPER_PROJECT_DIR` set to that same project root. For systemd mode, stop with `util/juniper_chop_all.bash --systemd` instead (no pidfile path). |
| `chop_all` logs `ERROR: PID file is empty` | Zero-byte `JuniperProject.pid` is treated like missing: best-effort `orphaned_worker_cleanup`, then `exit 1`. Re-run `plant_all` (or restore a real pidfile); do not hand-create an empty file. |
| Missing/empty pidfile but workers still running | Early wire still invokes `orphaned_worker_cleanup` before abort. Default `KILL_WORKERS=0` only logs the short-circuit; set `KILL_WORKERS=1` on that chop if you need the opt-in pgrep reap before exit. |
| systemd plant: `'curl' not found in PATH` | Install/expose `curl` before `--systemd` plant; no units were started. |
| systemd plant health timeout / partial stack | `cleanup_on_failure` did **not** stop user units. Inspect `systemctl --user status juniper-{data,cascor,canopy,cascor-worker}` and tear down with `util/juniper_chop_all.bash --systemd` (or matching `systemctl --user stop`) before re-planting. |
| Mixed plant/chop modes | Never plant with `--systemd` and chop via pidfile (or the reverse). Match the mode used at start. |
| Orphaned `juniper-cascor-worker` still running after chop | Pidfile stop only covers workers recorded at plant time. Opt in with `KILL_WORKERS=1 util/juniper_chop_all.bash` (nohup mode only; ignored under `--systemd`). See below. |
| Chop logs `KILL_WORKERS flag is not set to 1` | Expected when `KILL_WORKERS` is unset/`0` (default). Benign on the post-pidfile path (`|| true`); set `KILL_WORKERS=1` only when you intend the pgrep cleanup. |
| Chop WARNING `cmdline does not match … skipping (stale PID / wrong process)` | Expected when the pidfile PID was reused by an unrelated process — `validate_pid` refuses the kill (JR-ML-SEC-045). Not a `STOP_FAILURES` increment; successful chop still truncates the pidfile. See [non-empty pidfile stop path](#non-empty-pidfile-stop-path-validate_pid). |
| Chop WARNING `PID file preserved … for investigation` | At least one `graceful_stop` failed (`STOP_FAILURES > 0`) — pidfile is **not** truncated. Inspect survivors with `ss -tlnp` / the preserved lines, then re-chop or kill manually. |
| Mid-plant unset-variable / odd conda activate noise | Confirm `safe_conda_activate` restores with `set -u` (see above). A broken restore disables nounset for subsequent steps, so typos that should have failed may appear as unrelated mid-plant failures. |

#### Orphaned worker cleanup (`KILL_WORKERS`)

Host-mode `chop_all` optionally reaps leftover cascor workers that are **not** in `JuniperProject.pid` (crashed plant, manual launches, or workers started outside the pidfile loop). This path is **opt-in** and **nohup-only**:

- Gate: `KILL_WORKERS` must be exactly `1` (default `0`). Otherwise, chop logs: `KILL_WORKERS flag is not set to 1` and returns without signaling.
- Discovery: `pgrep -af juniper-cascor-worker`, then a **strict** cmdline filter that keeps only `juniper-cascor-worker`, `juniper_cascor_worker`, or the search term. The old `cascor.*worker` alternative was over-greedy (matched unrelated shells that merely mentioned both tokens).
- Stop: each match calls `graceful_stop <pid> cascor-worker 5` — timeout is hard-coded `5` seconds here (not `SIGTERM_TIMEOUT`).
- Call sites: missing/empty pidfile (best-effort before `exit 1`); after the pidfile loop with `|| true` so a benign "nothing to clean" return `1` cannot abort chop under `set -e` when every pidfile service already stopped.
- systemd mode (`--systemd` / `USE_SYSTEMD=1`) stops units via `systemctl --user` and **never** reaches this function — use systemd unit lifecycle there, not `KILL_WORKERS`.

```bash
# Default chop: pidfile services only (workers outside the pidfile stay up)
util/juniper_chop_all.bash

# Also reap orphaned cascor workers (console-script or python -m path)
KILL_WORKERS=1 util/juniper_chop_all.bash
```

Coverage: open juniper-ml#791 (`tests/test_juniper_chop_all.py` — `TestOrphanedWorkerCleanup`).

#### Missing / empty `JuniperProject.pid` (early wire)

In `nohup` mode, `chop_all` refuses to enter the service-stop loop without a usable pidfile. Both failure arms share the same contract (verified by open juniper-ml#798 / `TestMissingOrEmptyPidfileWire`):

1. **Missing file** → `ERROR: PID file not found: …` plus `No services to stop. Was juniper_plant_all.bash run?`
2. **Empty file** (`! -s`, zero bytes) → `ERROR: PID file is empty: …` with the same follow-up line
3. **Best-effort cleanup** → calls `orphaned_worker_cleanup` (honors `KILL_WORKERS`) **before** `exit 1`
4. **Never reaches** `=== Stopping Juniper Services ===` (no pidfile parse / SIGTERM loop)

Constraints operators miss:

- The two early call sites are **hard** (no `|| true`). The post-pidfile cleanup site is soft (`|| true`) so a benign "nothing to clean" return cannot abort a successful chop under `set -e`. Softening the early sites would hide a real cleanup failure behind a generic abort.
- `KILL_WORKERS` defaults to `0`; on the early wire that still runs cleanup, but the function short-circuits with `KILL_WORKERS flag is not set to 1…`. Use `KILL_WORKERS=1 util/juniper_chop_all.bash` when orphaned workers may be the only live leftovers after a failed/partial plant.
- systemd mode (`--systemd` / `USE_SYSTEMD=1`) never reads `JuniperProject.pid` and never hits this wire.

```bash
# Diagnose which arm you hit, then re-plant (or fix JUNIPER_PROJECT_DIR)
util/juniper_chop_all.bash
# Optional: also attempt orphaned-worker reap on the abort path
KILL_WORKERS=1 JUNIPER_PROJECT_DIR=/path/to/Juniper util/juniper_chop_all.bash
```

Coverage: open juniper-ml#798 (`tests/test_juniper_chop_all.py` — missing/empty → cleanup → exit 1; early sites stay hard).

#### Non-empty pidfile stop path (`validate_pid`)

When `JuniperProject.pid` is present and non-empty, `chop_all` enters `=== Stopping Juniper Services ===` and walks every line. This is the path hermetic coverage in open [#913](https://github.com/pcalnon/juniper-ml/pull/913) pins (`TestNonEmptyPidfileWire`) — complementary to the missing/empty early wire above.

**Line formats** (first delimiter wins):

| Format | Example | Notes |
|--------|---------|-------|
| Current `name=pid` | `juniper-cascor=12345` | Written by modern `plant_all` (post-2026-05-07) |
| Legacy `name: pid` | `juniper-cascor: 12345` | Still parsed (`=` preferred when both could appear) |

**Per-line contract (`validate_pid` then `graceful_stop`):**

1. Parse name + PID from the line (`=` or legacy `:`).
2. `validate_pid <pid> <name>` (JR-ML-SEC-045 / D-05) checks `${JUNIPER_CHOP_PROC_ROOT:-/proc}/<pid>/cmdline`:
   - Rejects non-numeric PIDs, missing `/proc` entries, and empty/unreadable cmdline.
   - Accepts a match after hyphen/underscore/case fold so conda paths like `.../envs/JuniperCascor1/bin/python` match pidfile key `juniper-cascor` (plant launches cascor/canopy as relative `python server.py` / `python main.py` — the env token is often the only stable substring).
   - Extra guard: pidfile key `juniper-cascor` must **not** match a worker cmdline that contains `worker` (normalized `junipercascor` is a prefix of `junipercascorworker`).
3. On accept → `graceful_stop` (SIGTERM, then SIGKILL after `SIGTERM_TIMEOUT`). On reject → log WARNING and **skip** (no signal).
4. A `validate_pid` skip is **not** a stop failure. Only a failed `graceful_stop` increments `STOP_FAILURES`.

**Pidfile outcome:**

| Result | Pidfile |
|--------|---------|
| Every line stopped or skipped as stale/wrong process (`STOP_FAILURES == 0`) | Truncated (`: >` the file) — chop exits 0 |
| Any `graceful_stop` failure (`STOP_FAILURES > 0`) | **Preserved** for investigation — chop exits 1 |

```bash
# Typical stale-PID warning (safe skip — unrelated process kept alive)
# WARNING: PID 12345 (juniper-data) cmdline does not match expected service 'juniper-data' — skipping (stale PID / wrong process)

# After a clean chop (including skips), pidfile is empty:
wc -c "${JUNIPER_PROJECT_DIR:-$HOME/Development/python/Juniper}/juniper-ml/JuniperProject.pid"
```

`JUNIPER_CHOP_PROC_ROOT` is **tests-only** (hermetic fake `/proc`); never set it on a live host. systemd mode never reaches this loop.

Coverage: open juniper-ml#913 (`tests/test_juniper_chop_all.py` — `TestNonEmptyPidfileWire` + `TestValidatePid`).

#### systemd mode

Opt in with `--systemd` or `USE_SYSTEMD=1` (default `0`). Both launchers enter the systemd arm **before** the `nohup` preflight / pidfile path, so there is no conda activation, no `ss` port check, and no `JuniperProject.pid` I/O. Verified by hermetic PATH-stub suites in `tests/test_juniper_plant_all.py` / `tests/test_juniper_chop_all.py` (`TestSystemdModeBehavioral`; open juniper-ml#804).

**Plant (`util/juniper_plant_all.bash --systemd`):**

1. Requires `curl` on `PATH` for health polls — missing `curl` exits `1` **before** any `systemctl --user start` (unlike `nohup` mode, `ss` is not required here).
2. Starts units in dependency order: `juniper-data` → `juniper-cascor` → `juniper-canopy` → `juniper-cascor-worker`, waiting on each health gate (`/v1/health`, worker `/v1/health/ready`).
3. After the worker health gate, if `systemctl --user is-active juniper-cascor-worker.service` fails, plant logs a WARNING and runs `systemctl --user status … --no-pager`, then still exits `0` (HTTP-ready is treated as success).
4. **Known blast-radius gap:** systemd starts are **not** appended to `STARTED_PIDS`. On a mid-plant health timeout, the ERR trap still runs `cleanup_on_failure` (logs cleanup; it no longer touches the pidfile in this mode — see below), but it **does not** `systemctl --user stop` any units already started.
   - This entry previously described the removal as `rm -f` of "the **unused** pidfile path". That assumption was the bug: the path is unused only if no *nohup* stack ever wrote to it, and when one did, a failed systemd plant deleted a live stack's only PID record. Fixed 2026-08-23. Operators must stop leftovers manually or with `util/juniper_chop_all.bash --systemd`. Do not "fix" this by inventing `systemctl stop` inside cleanup without updating the hermetic pin.

**Chop (`util/juniper_chop_all.bash --systemd`):**

1. Stops units in **reverse** dependency order: `juniper-cascor-worker` → `juniper-canopy` → `juniper-cascor` → `juniper-data`.
2. Soft-fails per unit (`was not running or failed to stop`) and continues — overall exit is still `0`.
3. Always `exit 0` after the systemd loop — never falls through to the pidfile parser, `validate_pid` / `graceful_stop`, or `orphaned_worker_cleanup` / `KILL_WORKERS`.

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Port preflight fails | Run `ss -tlnp` and free the reported port (`8100`, `8201`, `8050`, or `8210` by default), or override the matching `JUNIPER_*_PORT` before startup. |
| Mid-plant health timeout/abort | Read the failing service log under that repo's `logs/`. `cleanup_on_failure` already tried SIGTERM→SIGKILL on `STARTED_PIDS` and removed `JuniperProject.pid`. Confirm nothing is still listening (`ss -tlnp`) before re-planting; do not expect `chop_all` to find a pidfile after a failed plant. |
| `juniper-cascor` never reaches `/v1/health` | Inspect `juniper-cascor/logs/juniper-cascor_*.log`. If it dies on `import torch`, run `util/check_conda_env_torch.bash` before flipping `JUNIPER_CASCOR_CONDA` (exit **2** = P-5 FT; **4** = May-7). Prefer `JuniperCascor1`. See [Conda Env Torch Shadow](#conda-env-torch-shadow-diagnostic-p-5). |
| Worker startup says binary missing | Activate the worker env and install the package: `conda activate JuniperCascor1 && pip install juniper-cascor-worker`. |
| `chop_all` cannot find `JuniperProject.pid` | Confirm `plant_all` completed successfully in `nohup` mode and check the PID path printed at startup. In non-standard layouts, rerun shutdown with `JUNIPER_PROJECT_DIR` set to that same project root. If using systemd mode, stop with `util/juniper_chop_all.bash --systemd` instead. |
| systemd plant: `'curl' not found in PATH` | Install/expose `curl` before `--systemd` plant; no units were started. |
| systemd plant health timeout / partial stack | `cleanup_on_failure` did **not** stop user units. Inspect `systemctl --user status juniper-{data,cascor,canopy,cascor-worker}` and tear down with `util/juniper_chop_all.bash --systemd` (or matching `systemctl --user stop`) before re-planting. |
| Worker WARNING: healthy but unit not active | HTTP `/v1/health/ready` passed but `is-active` failed — check `journalctl --user -u juniper-cascor-worker` / unit file; plant still exited 0. |
| Mixed plant/chop modes | Never plant with `--systemd` and chop via pidfile (or the reverse). Match the mode used at start. |

---

## Scheduled Duplicati Backup Lane

Host-level `$HOME` backup under `systemd --user`, independent of the GNOME tray instance and of Duplicati's own scheduler (the server DB `Schedule` table was empty when this lane shipped). Merged in [juniper-ml#1292](https://github.com/pcalnon/juniper-ml/pull/1292). This is **not** `util/juniper-backup.bash` — that script is the project-tree / external-media leg. Operator surface: [Juniper Project-Tree Backup](#juniper-project-tree-backup).

The 2026-07-13 archive damage went undetected for six weeks because the only runner was a gnome-shell-launched scope under a user manager with `Linger=no`: it died at logout and nothing said so. This lane is the replacement.

### Install (copies, not symlinks)

```bash
util/install_duplicati_timer.bash
# after the first full backup AND a restore drill against the new set:
systemctl --user enable --now duplicati-backup.timer
systemctl --user list-timers duplicati-backup.timer
```

`install_duplicati_timer.bash` copies (never symlinks) into `~/.local/bin/` and `~/.config/systemd/user/`:

| Installed path | Source |
|----------------|--------|
| `~/.local/bin/duplicati-scheduled-backup.bash` | `util/duplicati_scheduled_backup.bash` |
| `~/.local/bin/duplicati-backup-failure.bash` | `util/duplicati_backup_failure.bash` |
| `~/.config/systemd/user/duplicati-backup.service` | `util/systemd/duplicati-backup.service` |
| `~/.config/systemd/user/duplicati-backup.timer` | `util/systemd/duplicati-backup.timer` |
| `~/.config/systemd/user/duplicati-backup-failure.service` | `util/systemd/duplicati-backup-failure.service` |

Canonical copies live in a git worktree. A symlink into one turns `git worktree remove` into a silent breakage of the backup lane — the same class that left a live passphrase inside a disposable worktree.

The installer **does not** `enable --now` the timer. Enabling while a first full backup is still in flight risks a second run against the same local DB. It refuses unless:

1. `~/.config/duplicati-backup/env` exists, is mode `600`, and contains a `PASSPHRASE=` line (the service will not start without it).
2. `loginctl show-user "$USER" --property=Linger --value` is `yes` (`loginctl enable-linger $USER` otherwise — without linger the user manager exits at logout and the timer never fires).

Then `systemctl --user daemon-reload`.

### Timer and unit contract

| Knob | Value | Why |
|------|-------|-----|
| `OnCalendar` | `*-*-* 02:30:00` | Overnight, off the interactive work window |
| `RandomizedDelaySec` | `30m` | Wake-from-suspend does not stampede other timers |
| `Persistent` | `true` | A workstation powered off at 02:30 still runs the missed window; without this the set silently goes stale |
| `TimeoutStartSec` | `infinity` | A full run takes many hours; an inherited start timeout would kill a healthy backup and leave a partial fileset |
| `Nice` / `IOSchedulingPriority` | `10` / `7` (`best-effort`) | Workstation neighbour |
| `EnvironmentFile` | `%h/.config/duplicati-backup/env` | Passphrase via environment, **never** on the command line (`/proc/<pid>/cmdline` is world-readable; `environ` is not) |
| `OnFailure` | `duplicati-backup-failure.service` | A backup that silently stops is indistinguishable from one that works |

The failure unit writes `${DUPLICATI_STATE_DIR:-$HOME/.local/state/duplicati}/failures.log` first (journal tail + `last-run.status`), then best-effort `notify-send` (`|| true` — under `Linger=yes` with no graphical session there is no session bus). The reporter always exits `0` so a second failed unit does not bury the original. It is **not** chained to another `OnFailure=`.

### Runner guards

`util/duplicati_scheduled_backup.bash` encodes failures actually observed in this arc. Defaults are overridable; destination / dbpath / source / tempdir are host paths, not ecosystem ports.

| Override | Default | Role |
|----------|---------|------|
| `PASSPHRASE` | *(required)* | GPG passphrase; length floor 12 chars (cannot detect a *wrong* value — Duplicati will encrypt a fresh set under any passphrase) |
| `DUPLICATI_DEST_URL` / `DUPLICATI_DEST_PATH` | `file:///media/pcalnon/temp_backups/Ubuntu` / that path | Backend URL and local directory |
| `DUPLICATI_DEST_MOUNT` | `/media/pcalnon/temp_backups` | Must be a real mountpoint (`mountpoint -q`) |
| `DUPLICATI_DBPATH` | `~/.config/Duplicati/DQRVQNDIFX.sqlite` | Local job DB |
| `DUPLICATI_SOURCE` | `/home/pcalnon` | Source tree |
| `DUPLICATI_TEMP_DIR` | `/media/pcalnon/temp_backups/_duplicati_tmp` | Volume staging; a **sibling** of the destination, same filesystem (finished volumes rename, not copy). Must not be tmpfs/ramfs |
| `DUPLICATI_STATE_DIR` | `~/.local/state/duplicati` | `backup.lock`, `last-run.status`, per-run logs, `failures.log` |
| `DUPLICATI_STALE_DAYS` | `3` | Skip-escalation ceiling (see below) |

Guards, in order:

| # | Check | On fail |
|---|-------|---------|
| 1 | `PASSPHRASE` set and ≥ 12 chars | `FATAL` |
| 2 | dest is a mounted, existing, writable directory | `FATAL` (an unmounted path is an empty dir on `/` and reads to Duplicati as "everything is missing") |
| 3 | dest is empty **or** already holds `duplicati-*` volumes | `FATAL` (wrong filesystem) |
| 3b | `DUPLICATI_TEMP_DIR` fstype is not `tmpfs` / `ramfs` | `FATAL` (observed 2026-08-23: unset `--tempdir` staged 500 MB volumes in `/tmp` tmpfs — 8.4 GB RAM in flight) |
| 4 | non-blocking `flock` on `${STATE_DIR}/backup.lock` | `skip_or_fail` |
| 5 | no other live process has `DBPATH` open (`/proc/*/fd` realpath, **not** `pgrep -f`) | `skip_or_fail` |

Guard 5 is on the **database**, not the process name: a hand-started `duplicati-cli backup`, the same binary by absolute path, and `duplicati-server` running the job in-process from the web UI all hold the DB open. `pgrep -f` self-matches and already produced a wrong status line in this arc.

`--no-auto-compact=true` is load-bearing. An interrupted compact on 2026-07-13 deleted 1,208 dblock/dindex pairs and wrote zero replacements. Do not drop it without a considered compaction-safety decision.

### Skip vs failure (OnFailure only fires on non-zero)

A skip is `exit 0`, so systemd reports success and `OnFailure=` does **not** run. Two properties make that safe:

1. Every skip still stamps `last-run.status` with a **current** timestamp (`result=SKIPPED`), so the file cannot freeze at an old `OK`.
2. `skip_or_fail` only treats the file as a success stamp when its *current* contents match `^result=OK`. After one skip the next skip sees no OK stamp (`last_ok=0`) and **always escalates** to `FATAL` (OnFailure fires) — including a first skip that never had a prior OK. A persistently hung `duplicati` therefore cannot make every nightly run skip forever.

Do **not** read `DUPLICATI_STALE_DAYS` as "N consecutive skips are allowed." The OK stamp is overwritten on the first skip.

### Related (do not treat as runnable restore steps)

- Archive damage findings: [`notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](../notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md)
- GPGFlushError investigation (open; not a reason to drop `--no-auto-compact`): [`notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`](../notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md)
- `notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md` is **withdrawn** — restoring the archived job DB reproduces the wedge. Do not execute it.
- Project-tree / external-media archives: [Juniper Project-Tree Backup](#juniper-project-tree-backup) (`util/juniper-backup.bash`).

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Installer: missing `env` / not mode `600` / no `PASSPHRASE=` | Create `~/.config/duplicati-backup/env` mode `600` with a `PASSPHRASE=` line; the service reads it via `EnvironmentFile=` |
| Installer: Linger is NOT enabled | `loginctl enable-linger $USER`; without this the timer dies at logout |
| Timer never fires after logout | Linger was the original failure class — confirm `Linger=yes` and `systemctl --user list-timers duplicati-backup.timer` |
| `FATAL: … is NOT a mountpoint` | The dest path resolved onto `/` — mount the backup volume before retrying |
| `FATAL: … tmpfs (RAM-backed)` | Point `DUPLICATI_TEMP_DIR` at any disk-backed path — the runner stats the filesystem and refuses a RAM-backed one; `/tmp` is tmpfs on this host |
| Skip then the next run `FATAL` escalating | Expected — a skip overwrites `result=OK`; the following skip always escalates. Inspect `last-run.status` and `failures.log` |
| Two runners / web UI plus timer | Guard 4/5: wait, or stop the other holder of `DBPATH`; do not `pgrep -f` to decide |
| Failed run, no desktop popup | Reporter still wrote `failures.log`; `notify-send` is best-effort under linger with no session bus |
| Partial fileset / killed run | The unit sets `TimeoutStartSec=infinity` so systemd will not SIGTERM a long healthy run. An abrupt `kill -9` mid-WAL is the class the [archive-damage findings](../notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md) warn against — TERM, then wait. |

---

## Juniper Project-Tree Backup

[`util/juniper-backup.bash`](../util/juniper-backup.bash) archives **each Juniper application repo** as its own bzip2 + OpenPGP file, builds the ciphertext **once**, and copies that finished file onto every attached configured drive. It is the project-tree / external-media leg. It is **not** the Duplicati `$HOME` lane ([Scheduled Duplicati Backup Lane](#scheduled-duplicati-backup-lane)).

A coherent restore takes **every** archive that shares one UUID (one run). The timestamp records when the backup **ran**, not what the tree contains — label a `--source` of a restored snapshot.

### Usage

```bash
util/juniper-backup.bash --dry-run
util/juniper-backup.bash
util/juniper-backup.bash --source ~/juniper-restore-2026-02-27 --label snapshot-2026-02-27 \
    --repos "juniper-cascor juniper-data JuniperLegacy"
util/juniper-backup.bash --dest /path/to/writable-dir
```

| Flag | Contract |
|------|----------|
| `--dry-run` | Preview only. Writes nothing. **Must** `exit 0` before the build loop (a prior revision fell through and wrote real archives while printing COMPLETE). |
| `--source DIR` | Parent whose children are repos. Default `$HOME/Development/python/Juniper`. |
| `--dest DIR` | One writable directory; skips `MEDIA_NAMES` fan-out. Not mount-checked — an explicit path is the caller's decision. |
| `--repos "LIST"` | Space-separated leaf names. Each must match `[A-Za-z0-9._-]+` (blocks `../`). Empty list is exit 2. |
| `--label TEXT` | Same charset. Inserted into every filename. Use when `--source` is a restored tree. |

Default `APPLICATION_REPOS`: `juniper-canopy`, `juniper-cascor`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-data`, `juniper-data-client`, `juniper-deploy`, `juniper-ml`, `juniper-recurrence`, `juniper-slacker`. A missing leaf is a WARNING skip; zero found is FATAL. `juniper-legacy` is **not** in the default list.

### Restore

Archives are named `Juniper[_<label>]_<repo>_<uuid>_<stamp>.tbz2.gpg`. The compressor is **bzip2** (`TAR_COMPRESS_FLAG=-j` / `TAR_EXT=tbz2`). An earlier revision named them `.tgz` while writing bzip2, so the documented gzip restore failed on every archive it produced.

```bash
gpg -d Juniper_<repo>_<uuid>_<stamp>.tbz2.gpg | tar -xjf -
# list-only:
gpg -d FILE.tbz2.gpg | tar -tjf -
```

Use `-xjf`, not `-xzf`. Encryption is asymmetric (`gpg -r <uid> -e`) to the two `ENCRYPT_KEYS` UIDs in the script. **No YubiKey is needed to write**; any one recipient can decrypt. You cannot retro-fit a recipient onto an archive already written.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Every configured device holds a verified archive of every found repo, or `--dry-run` previewed |
| `1` | Fatal — nothing written (bad source, no usable dest, missing recipient, empty repo list, build/verify failed) |
| `2` | Misuse (unknown flag, empty `--repos`, illegal `--label` / repo name) |
| `4` | PARTIAL — cross-repo `TOTAL_WRITTEN < TOTAL_EXPECTED`. Visible to cron. Already-verified copies stay. |

### Contract (verified against `util/juniper-backup.bash` on `origin/main`)

- **Streamed, not staged.** `tar | gpg` with `set -o pipefail`. No plaintext scratch copy. `gpg --compress-algo=none -z 0` because tar already bzip2'd.
- **Build once, replicate.** First usable `MEDIA_NAMES` entry (or `--dest`) is the build device; the rest get `cp` of the ciphertext. Destinations are derived per iteration (`target_dir_for`) so a loop cannot rewrite the first drive.
- **`--dry-run` exits before the build loop.** The preview is rendered from `TAR_COMPRESS_FLAG` / `TAR_EXT` / `GPG_RECIPIENT_ARGS`, not a hardcoded `tar -czf`.
- **Unattended verify is OpenPGP structure only.** `gpg --list-packets --list-only` plus a `:pubkey enc packet:` count matching `${#ENCRYPT_KEYS[@]}`. That path does **not** prove the tar is intact.
  Pipeline byte-for-byte: [`util/ad-hoc/2026-08-26_backup_restore_drill.bash`](../util/ad-hoc/2026-08-26_backup_restore_drill.bash) (PASSES).
  The YubiKey decrypt of a real archive is recorded closed in [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](../notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md) §6.4.2 q3 (2026-08-28); `verify_archive` still cannot do that half.
- **Exclude patterns are relative and top-level.** `--exclude=<leaf>/<name>` from the same `PROJECT_DIR` for both `du` and `tar`.
  Absolute or quote-baked patterns were shellcheck-clean and matched nothing (`du` ~205 MB vs `tar` ~103 GB).
  Repro: [`util/ad-hoc/2026-08-28_exclude_arg_repro.bash`](../util/ad-hoc/2026-08-28_exclude_arg_repro.bash).
- **`cascor-snapshots` is archived by default.** `EXCLUDE_CASCOR_SNAPSHOTS` defaults to the script's `FALSE` (`1`). The script's `TRUE` is `0`. Set `EXCLUDE_CASCOR_SNAPSHOTS=0` to drop the corpus; setting `1` does **not** mean "yes, exclude".
- **Mount check is the mount root.** `mountpoint -q` on `/media/<user>/<MEDIA_NAME>`, not on `BACKUP_DIR`. An unmounted path is an empty dir on `/` and would fill the system disk.
- **One missing drive degrades; zero usable is fatal.**
- **Free-space floor is the uncompressed source**, not half. This tree is mostly already-compressed `.h5` / `.npz` / `.gpg`.
- **Cross-repo totals decide COMPLETE.** Per-repo counters used to reset each iteration and print COMPLETE over a missing archive.
- **`cleanup_partial` removes only `IN_PROGRESS`.** Verified copies on earlier devices stay.

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| `tar` cannot extract a `.tbz2.gpg` | Used `-xzf`. Use `-xjf`. |
| `--dry-run` created archives | Script must `exit 0` after the preview. Current `origin/main` does. |
| `FATAL: gpg recipient not found` | Both `ENCRYPT_KEYS` UIDs must resolve in the local keyring **before** tar starts. |
| `SKIP … is not a mount point` | Drive not attached. Attach it, or pass `--dest DIR`. |
| Exit `4` PARTIAL | A copy/verify failed. Already-verified archives stay. Re-run makes a **new** UUID. |
| Archive huge / includes `data/` `venv/` | Exclude flags inert (quoted or absolute). Confirm `--dry-run` `tar args:` shows `--exclude=<leaf>/<name>`. |
| Backup of a restored tree looks like today's | Timestamp is when the backup ran. Pass `--label`. |
| `cascor-snapshots` missing from the archive | `EXCLUDE_CASCOR_SNAPSHOTS=0` (the script's `TRUE`). Default `1` includes the corpus. |

---

## Editable Install Drift Check

`util/editable_install_drift_check.py` scans conda envs for `juniper-*` editables (via `*.dist-info/direct_url.json`), classifies each as `FRESH` / `WORKTREE_PINNED` / `ORPHANED`, and optionally re-points orphans with `--fix` (preview with `--dry-run`). Exit `1` on any `ORPHANED` finding.

#### Version axis: `MATCH` / `STALE` / `UNKNOWN`

A second, **orthogonal** axis compares the version an install *recorded* at `pip install -e` time against the version its source tree declares *now*. An editable never re-derives its version when the source moves on: `import` follows the live tree, but `*.dist-info/METADATA` stays frozen at the last pip run.

| Verdict | Meaning |
|---------|---------|
| `MATCH` | Recorded version equals the target's declared version. |
| `STALE` | They disagree — metadata frozen at install time. |
| `UNKNOWN` | Not comparable: `ORPHANED` target, or no resolvable declared version. |

The axes are independent — a `FRESH` install can be `STALE`, and so can a `WORKTREE_PINNED` one. This is why the path axis alone missed it: on 2026-08-14 **7 of 8** installs on this host were `FRESH` **and** stale simultaneously, `juniper-data` five minors behind (`0.6.0` recorded vs `0.11.0` declared).

What it breaks, since `import` keeps working: anything reading the *installed* version rather than the source — a repo's own `version == pyproject` self-check (juniper-cascor's `test_version_matches_pyproject` failed locally on exactly this), and the build-info/provenance metric a host-launched service exports.

Distinct from `juniper-env-drift-check` (juniper-ci-tools), which asks whether an installed version satisfies a consumer's declared **floor**. A stale editable can sit comfortably above every floor and still be wrong; only an editable install can drift this way.

`STALE` is **soft** — exit stays `0`, because `import` still resolves. `--strict-version` makes it exit `1`. `--strict` applies only to the path axis.

```bash
python util/editable_install_drift_check.py                     # report (STALE is soft)
python util/editable_install_drift_check.py --strict-version    # exit 1 on any STALE
python util/editable_install_drift_check.py --fix --fix-stale --dry-run   # preview refresh
python util/editable_install_drift_check.py --fix --fix-stale             # re-stamp metadata
```

`--fix-stale` repairs a stale-but-`FRESH` install against the path it **already points at** (`drift: "stale-metadata"`), not a canonical-discovery result — reinstalling from the recorded path is what re-stamps the metadata, and routing it through discovery could re-point a deliberate checkout. `ORPHANED` items keep resolving to their canonical repo (`drift: "path"`).

A dynamic version is read-only from an **explicit** declaration (setuptools `[tool.setuptools.dynamic] version.attr`, hatch `[tool.hatch.version] path`); an unrecognized backend reports `UNKNOWN` rather than guessing at a plausible `_version.py`.

> **Live services:** `--fix`/`--fix-stale` reinstall into the env. Scope with `--env NAME` if a long-lived service is running from one of them.

#### Ambiguous canonical `--fix` SKIP

`--fix` resolves a unique canonical source under the ecosystem root via `discover_canonical(pkg_name, ecosystem_root)`:

- Exactly one non-worktree checkout whose `[project].name` matches → that path is the canonical.
- Zero matches → `action=SKIP`, reason `no canonical source found`.
- Two or more matches → `action=SKIP`, reason contains `ambiguous`, `canonical=null`, and `candidates` lists every match. The tool **must not** pick `candidates[0]` — auto-picking the first tree would re-point an orphaned editable at the wrong fork/mirror.

```bash
# Preview repairs (never writes). Ambiguous packages stay SKIP in the JSON "fix" array.
python util/editable_install_drift_check.py --fix --dry-run --json
```

Coverage: open juniper-ml#795 (`tests/test_editable_install_drift_check.py` — `test_discover_canonical_ambiguous_returns_none`, `test_fix_skips_when_canonical_ambiguous`).

#### Live `--fix` actions (`FIXED` / `ERROR`)

`--fix` without `--dry-run` is the only path that mutates conda envs. `run_fix` walks the plan item-by-item and never aborts the rest of the plan on a single failure:

| `action` | When | Effect |
|----------|------|--------|
| `DRY_RUN` | `--fix --dry-run` and the item is resolvable | Prints the pip command; writes nothing. |
| `FIXED` | Live `--fix`; `subprocess.run(..., check=True)` succeeds | Re-points the editable via `<env>/bin/python -m pip install -e <canonical> --no-deps --force-reinstall -q`. |
| `ERROR` | Live `--fix`; `OSError` (missing env python) or `CalledProcessError` (pip failed) | Captures stderr/`str(exc)` truncated to 500 chars; continues to the next plan item. |
| `SKIP` | Item not resolvable (`no canonical` or `ambiguous: N candidates`) | No pip; see Ambiguous canonical guidance (open [#801](https://github.com/pcalnon/juniper-ml/pull/801) / [#795](https://github.com/pcalnon/juniper-ml/pull/795)). |

After a live (non-dry) `--fix`, `main` re-scans findings before reporting exit codes. A `FIXED` orphan clears that env/package from `ORPHANED`; an `ERROR` leaves it orphaned so the process still exits `1` until the underlying cause is fixed and `--fix` is re-run.

```bash
# Preview (action=DRY_RUN / SKIP only — never mutates)
python util/editable_install_drift_check.py --fix --dry-run --json

# Live repair (action=FIXED or ERROR per item; re-scan afterward)
python util/editable_install_drift_check.py --fix --json
```

Coverage: open juniper-ml#802 (`test_run_fix_executes_and_reports_fixed`, `test_run_fix_reports_called_process_error`, `test_run_fix_reports_oserror`).

The JuniperCascor1 editable finder maps every `juniper-cascor` import onto the primary checkout's `src`. That is why a live importer makes the primary unsafe to edit — see [Cascor Primary Freeze Tell](#cascor-primary-freeze-tell).

---

## Cascor Primary Freeze Tell

`util/ad-hoc/cascor_freeze_tell.py` decides whether the **juniper-cascor primary checkout freeze** is in force. The freeze exists because the JuniperCascor1 editable finder maps every cascor package onto the primary's `src`: editing that tree under a live importer corrupts the running process.

This is a **reader**. It prints holds and exits. It does not kill anything. Do not substitute the [Pytest Orphan Reaper](#pytest-orphan-reaper) (kills orphaned pytest children) or `juniper_chop_all.bash` (stops the plant tree).

```bash
python3 util/ad-hoc/cascor_freeze_tell.py
```

No flags. No env override for the primary path. `PRIMARY` is hardcoded to `/home/pcalnon/Development/python/Juniper/juniper-cascor`.

### What counts as a hold

`_is_primary_path` is an **exact path prefix** plus `os.sep` (after `os.path.normpath`). Two corrections over the round-28 handoff tell, which was unsound in both directions:

| Old tell | What it got wrong | Live rule |
|----------|-------------------|-----------|
| `"juniper-cascor" in cwd` | Also matches `juniper-cascor-client` / `juniper-cascor-worker`, and every centralized `worktrees/juniper-cascor--*` | Exact prefix against `PRIMARY`. Sibling repos are not holds. |
| cwd only | `cd /tmp && python -c "import cascade_correlation"` still resolves into the primary via the editable finder | Also scan cmdline, environ (`os.pathsep` parts), open fds, and mapped files. |

Worktree roots are excluded even when they sit under a `juniper-cascor--*` name:

- `/home/pcalnon/Development/python/Juniper/worktrees`
- `<PRIMARY>/.claude/worktrees`

An unreadable cwd does **not** abandon the process: cmdline is still world-readable, so a later arm can still catch the hold.

`maps` entries that are not absolute paths are ignored (a relative `juniper-cascor/src/foo.so` is not evidence).

### Exit codes

| Exit | Stdout | Meaning |
|------|--------|---------|
| `1` | `HOLDS-PRIMARY  pid=…` then `FREEZE IN FORCE -- N process(es) hold the cascor primary.` | Do not edit the primary. |
| `0` | `no user-owned process holds the cascor primary -- freeze NOT in force` plus `(root-owned processes are invisible to an unprivileged scan)` | No **user-owned** importer. Not "no importer exists". |

`/proc/<pid>/{fd,environ,maps}` are unreadable for other users. A root-owned importer is invisible to this tell and to any unprivileged scan. Treat a clean result as "no user-owned importer".

### Operator pitfalls

| Symptom | Check |
|---------|-------|
| Tell freezes because you are in `juniper-cascor-client` / `-worker` | That was the substring bug. Live `_is_primary_path` does not treat siblings as holds. |
| Tell freezes a `worktrees/juniper-cascor--*` checkout | Both worktree roots are excluded. If you still see a hold, a process is importing the **primary**, not the worktree. |
| Exit 0 but `import cascade_correlation` from `/tmp` is live | The cwd-only tell missed this. Live tell should print `argv=` / `env=` / `fd=` / `map=`. If it does not, the importer is likely root-owned. |
| Exit 0, then you edit the primary and a service dies | Root-owned or other-user importer. The banner already says they are invisible. Confirm with a privileged `lsof` / `fuser` on `PRIMARY/src` before editing. |
| `PRIMARY` is not your checkout | There is no `--primary` / env override. The constant is the host primary. Do not fork a copy that substring-matches. |
| Used this to *stop* cascor | Wrong tool. Chop the plant / experiment stack. This tell only classifies. |

Dedicated unittest arm is **not on main** (open juniper-ml#1667). Complementary process-table gate that *is* on main: `tests/test_reap_pytest_orphans.py` (different predicate — do not reuse its orphan filter here).

---

## Pytest Orphan Reaper

`util/reap_pytest_orphans.bash` finds and `SIGKILL`s multiprocessing forkserver / worker children left behind when a Juniper pytest session dies before teardown (OOM, `kill -9`, closed terminal). Orphans can hold hundreds of MB RSS for many minutes until the forkserver notices the parent is gone.

This is **not** the host-stack `KILL_WORKERS` / `orphaned_worker_cleanup` path in `juniper_chop_all.bash` (cascor-worker cmdline filter). Use the reaper after crashed **pytest** sessions; use chop for the plant/nohup service tree.

```bash
util/reap_pytest_orphans.bash --dry-run          # list WOULD REAP / summary only
util/reap_pytest_orphans.bash --dry-run --verbose  # also print KEEP (live parent)
util/reap_pytest_orphans.bash                    # REAP with kill -KILL
```

Exit codes: `0` success (zero or more reaped); `2` unknown argument.

#### Candidate awk filter (false-positive wall)

`ps -eo pid=,user=,cmd=` → awk keeps a PID only when **all** hold:

1. `user` equals `id -un` (never touch another user's Juniper session)
2. cmdline matches `/python/`
3. cmdline matches `/JuniperC[a-z0-9]+/` (conda env like `JuniperCascor1`) **or** `/Juniper\/worktrees\//`

Empty candidate set → `No Juniper python processes found.` and exit `0` (no kill). Loosening this filter is the false-positive class that kills foreign sessions or plain `python -m pytest` outside Juniper.

#### Live-experiment protection (checked FIRST)

**A live experiment stack or campaign is never an orphan; however, it is parented.** `experiment_stack.bash` and `isolated_stack.bash` launch their services with `nohup` inside a subshell, so the services reparent to `systemd --user` — which is precisely the orphan predicate below. A campaign orchestrator or watchdog started with `setsid` / `disown` lands there too.

Observed live on **2026-08-16** against campaign `e-j-h2h-wide-cap6`: a `--dry-run` classified the campaign **orchestrator**, the experiment **cascor service**, and the follow-on **watchdog** all as `WOULD REAP` while every one was healthy and mid-run. A live sweep would have destroyed a multi-hour campaign.

Two independent protection keys, either sufficient:

| Key | Catches | Mechanism |
|-----|---------|-----------|
| **P1** pidfile | the services | pid recorded in a `*.pid` under a run root (written by `record_listener_pid` after the health gate) |
| **P2** cmdline | orchestrators, drivers, watchdogs | the pid's cmdline references a run root — none of these carry a pidfile |

Protected candidates print `PROTECT pid=… (live experiment)` **always** (not gated on `--verbose`, so an operator sweeping during a campaign sees the decline) and are counted separately.

Over-protection is deliberately the safe direction: a false protect costs one retained orphan until the next sweep; a false reap costs the campaign. A stale pidfile from a torn-down run therefore still protects.

#### Orphan decision and SKIPPED races

For each candidate not protected above, read `PPid:` from `${JUNIPER_REAP_PROC_ROOT:-/proc}/<pid>/status`. Mark orphan when parent is PID `1` (init), the resolved user-session `systemd --user` PID, or the parent directory is gone. Live parents → `KEEP` (printed only with `--verbose`).

`SKIPPED` increments (never WOULD REAP/kill) when:

- `/proc/<pid>` disappeared between `ps` and the loop (ps→gone race)
- status is missing / unreadable / has no `PPid:` line

Summary line: `N reaped, M kept (live parent), P protected (live experiment), K skipped` (`would be reaped` under `--dry-run`).

| Override | Default | Role |
|----------|---------|------|
| `JUNIPER_REAP_PROC_ROOT` | `/proc` | Synthetic proc root for hermetic tests |
| `JUNIPER_REAP_KILL_CMD` | `kill` | Kill binary override for tests (must accept `-KILL <pid>`) |
| `JUNIPER_EXP_RUN_ROOT` | `${HOME}/.local/state/juniper-experiments` | Experiment run root protected from reaping (same var `experiment_stack.bash` reads) |
| `JUNIPER_E2E_RUN_DIR` | `${TMPDIR:-/tmp}/juniper-e2e` | Isolated-stack run dir protected from reaping (same var `isolated_stack.bash` reads) |

Regression coverage: `tests/test_reap_pytest_orphans.py` (incl. candidate-filter + SKIPPED arms from juniper-ml#784).

A live soak probe is also a P1/P2 protectee: `util/soak_run_probe.py` writes `$JUNIPER_EXP_RUN_ROOT/soak-probes/soak-probe-<pid>.pid`. A pidfile under `reports/soak/runs/` is **not** scanned. Operator surface: [Pointer-Follow Soak](#pointer-follow-soak).

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Expected orphan never listed | Confirm cmdline contains a `JuniperC*` env path or `Juniper/worktrees/`; other-user and non-Juniper python are intentionally excluded. |
| High `skipped` count, zero reaped | Transient ps→gone race or incomplete `/proc/<pid>/status`; re-run `--dry-run --verbose` once the process table settles. |
| Live pytest session would be killed | Parent still exists and is not init / `systemd --user` → script prints `KEEP` under `--verbose` and does not kill. |
| Soak probe `WOULD REAP` | Guard pidfile missing from `$JUNIPER_EXP_RUN_ROOT/soak-probes/`, or the interpreter path is `JuniperC*` (`/usr/bin/python3` is not a candidate). |

---

## Pointer-Follow Soak

The pointer-follow soak measures whether a **fresh, unprimed** Claude session retrieves a **relocated** fact from its pointer (usually a `docs/REFERENCE.md` heading) rather than from source. Owner decision 2026-09-03: the soak exists **to inform relocation decisions**, not to print a pooled pass/fail about "relocation in general."

Protocol: [`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](../notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md). Trigger and characterisation: [`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`](../notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md) §§8–9.

### Pieces

| Piece | Role |
|-------|------|
| `conf/soak_probes.json` | Frozen seeded-arm registry. Never edit a probe that already has runs; add a new id. |
| `reports/soak/pointer_follow_soak.jsonl` | Append-only ledger (observations, rescores, resolves, invalidates). |
| `util/soak_next_probe.py` | Prints the **task only** (probe id on stderr). `--reveal` is scoring-only. `--status` is coverage, no task text. |
| `util/soak_run_probe.py` | Headless `claude -p` wrapper: dispatch, capture, retrieval channel, scoring packet. |
| `util/soak_ledger.py` | `probe-run` / `report` / `status` / `verify-probes` / `resolve` / `rescore`. |
| `util/systemd/juniper-soak-probe.{service,timer,path}` | Unattended **user** units (same wrapper). |

`verify-probes` is the residency gate: every probe's `must_be_absent_from_source` phrases must be absent from `AGENTS.md`, and every `pointer` anchor must resolve. The 2026-08-21 pilot ran nine probes whose facts had never left `AGENTS.md`; those tested nothing. CI runs `python3 util/soak_ledger.py verify-probes`.

Probe ids are **full slugs**. `--probe-id P19` exits `2` (`no such probe: P19`). Real ids look like `P19-port-check-fail-opens`. List them from `conf/soak_probes.json` or `soak_next_probe.py --status`.

### Operator loop

```bash
python3 util/soak_run_probe.py --dry-run                    # no claude binary required
python3 util/soak_run_probe.py                              # least-covered probe
python3 util/soak_run_probe.py --probe-id P23-reaper-over-protection-bias
python3 util/soak_run_probe.py --probe-id <ID> --force      # when status is BET-FAILING / HOLDS-AT-*
python3 util/soak_next_probe.py --reveal --probe-id <id>    # AFTER the run, for scoring
python3 util/soak_ledger.py probe-run --probe-id <id> \
    --outcome follow|source-recovered|miss --session <uuid> --scored-by <who>
python3 util/soak_ledger.py probe-run --probe-id P15-worktree-converge-not-remove \
    --outcome miss --class discoverability --session <uuid> --scored-by <who>
python3 util/soak_ledger.py report
python3 util/soak_ledger.py status
```

`--dry-run` must not print the task, fact, or discriminator: this wrapper's stdout is read by the operator who later **scores** the run, and echoing the task there re-primes at the far end of the pipeline.

The terminal-verdict refuse in `soak_run_probe.py` runs **before** the `--dry-run` branch. `BET-FAILING` / `HOLDS-AT-*` makes even a dry run exit `2` unless `--force`. On current `main` the ledger is `INCONCLUSIVE` (interval spans 0.75), so the default invocation does run; `--force` is the characterisation override when a pooled verdict later goes terminal.

Wrapper exit codes: `0` usable answer + scoring packet; `1` timeout / empty / error result; `2` misuse, or the harness failed before the probe started (including terminal-verdict refuse).

Ledger: `probe-run` / `record` / `resolve` → `0` written / `2` rejected (`_reject`); `report` always `0`; `status` → `0` for `IN-PROGRESS` / `HOLDS-AT-*` / `INCONCLUSIVE` with no escalations, **`1` on `BET-FAILING` or an open escalation**, `2` for `NO-DATA` / `DEGRADED` / `NO-SEEDED-DATA`; `verify-probes` → `0` sound / `1` defective.

### Automated vs judgement

Automated (mechanical): probe selection, unprimed dispatch, transcript capture, the **retrieval channel** — did tool inputs **or the answer text** contain the pointer *document path* (anchor stripped)? That match is in `retrieval_channel`: `blob = tool_inputs + answer`. Reciting the path in the answer scores as a pointer hit even when no tool opened the document.

Not automated: correctness against the frozen `discriminator`. The wrapper writes `reports/soak/runs/<stamp>-<probe>/scoring_packet.md` and stops. `soak_ledger.py probe-run` still needs a scorer to supply `--outcome`.

Outcomes (`OUTCOMES` in `util/soak_ledger.py`):

| Outcome | Meaning | Follow-rate |
|---------|---------|-------------|
| `follow` | Correct **and** retrieved via the pointer | numerator |
| `source-recovered` | Correct, reached from source (helper / test / grep), not the pointer | stays in **denominator** |
| `miss` | Acted without the fact | denominator |

`rate` = follows / (follow + miss + source-recovered). `retention` = (follow + source-recovered) / n answers a different question — *did relocation lose the fact?* — and is printed beside the rate, never instead of it. Dropping source-recovered from the denominator was considered and rejected: it would convert `INCONCLUSIVE` into a pass by redefinition.

### Least-covered vs characterisation

Default `soak_next_probe.py` / `soak_run_probe.py` pick **least-covered, then registry order**. That evens the **pooled** estimate.

For a relocation decision the pooled rate is a **mixture**. Characterisation runs (juniper-ml#1616, 2026-09-04; design-conversation §9) selected probes to test membership, not coverage:

- Permutation test (15 probes, 40 seeded runs, 26 follows, 20,000 draws): heterogeneity statistic 30.84, **p = 0.0017**. The probes do not share one rate. Use the stratum, not ~65%, for a specific section.
- **Per-probe membership is not resolved at n=2–4.** P23 left the "never-follow" group on its third run (0/2 → follow → 1/3). No probe's 95% CI excludes 50% or the pooled rate. Do not treat "P14 never follows" as a property from 0/3.
- Next cheapest design: drive ambiguous probes (P21 / P23 at 1/3; the 0/3 set) to **n≈8–10**, not even coverage. The timer still fires least-covered — pass `--probe-id` for characterisation.
- Stopping rule: `soak_run_probe.py` refuses when `status` starts with `BET-FAILING` or `HOLDS-AT-` unless `--force`. Under decision support a terminal **pooled** verdict does not answer the next relocation; `--force` is the deliberate override, not a way to ignore a real stop. Design-conversation §8.3 flagged that the guard is keyed on the demoted signal; it stays in place so unattended spend cannot run away.

As of origin/main after #1616: `python3 util/soak_ledger.py report` prints **INCONCLUSIVE**, seeded 40/35, rate 65.0%, Wilson 95% CI [0.495, 0.779], **retention 95.0%**. Retention is high: relocation is not losing facts; pointer-following is not what prevents the loss.

### Verdicts (seeded arm)

Wilson 95% interval vs one reachable boundary (`DECISION_BOUNDARY = 0.75`). Named after what was proven. `BET-HOLDS` is **not** a printable verdict. `IN-PROGRESS` until `TARGET_PROBE_RUNS = 35` seeded runs **and** `MIN_DISTINCT_PROBES = 15`.

| Verdict | Meaning |
|---------|---------|
| `IN-PROGRESS` | fewer than 35 seeded runs or 15 distinct probes |
| `HOLDS-AT-0.75` | Wilson lower bound ≥ 0.75 |
| `BET-FAILING` | Wilson upper bound < 0.75 |
| `INCONCLUSIVE` | interval spans 0.75, or hazard stratum empty |
| `DEGRADED` / `NO-DATA` / `NO-SEEDED-DATA` | instrument integrity; outranks a healthy-looking rate |

Escalations (hazard rung 2, area-systematic rung 3, pointer-defect rung 0) print **alongside** the verdict, never instead of it. `status` exits `1` when they are open or the verdict is `BET-FAILING` — that is the design. `resolve` appends to an append-only ledger; there is no un-resolve. Do not discharge to make the exit code 0.

The **organic** arm is descriptive only (an upper bound). Never used for a verdict.

### Unattended path

These are **user** units, not system units: the probe must see `~/.claude/projects/.../memory/MEMORY.md`. A system unit runs as root with a different `HOME` and measures nothing (same class that ruled out cloud routines).

```bash
mkdir -p ~/.config/systemd/user
cp util/systemd/juniper-soak-probe.* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now juniper-soak-probe.timer   # or the .path unit
systemctl --user start juniper-soak-probe                # one-off; no [Install] on the service
```

Enable the **timer** or **path** unit, not the service. An `[Install]` block on the service is deliberately absent: enabling it would fire an extra uncoordinated probe at every login.

- `ExecStart=/usr/bin/python3 util/soak_run_probe.py --timeout 900` — the reaper candidate filter matches cmdline text `/JuniperC[a-z0-9]+/`; a conda interpreter is reapable from the same cwd. `/usr/bin/python3` is not a candidate.
- `TimeoutStartSec=1500` must exceed dispatch (120s) + claude (900s) + `--reveal` (120s). If systemd wins the race it cgroup-kills the wrapper **before** `status.json` is written ("crash, not timeout").
- Timer: `OnCalendar=*-*-* 03,09,15,21:23:00`, `Persistent=false` (a laptop resuming after two days must not stampede missed intervals).
- Both the unit and the wrapper unset `ANTHROPIC_API_KEY` — a stale key fails with `Credit balance is too low` before the probe starts.
- The wrapper resolves `claude` itself (`resolve_claude`); the unit still prepends `%h/.local/bin` because the user-manager `PATH` does not include it.
- Reaper P1 pidfile: `$JUNIPER_EXP_RUN_ROOT/soak-probes/soak-probe-<pid>.pid` (default `~/.local/state/juniper-experiments`). A pidfile under `reports/soak/runs/` is **not scanned**.

### Pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Primed follow | `--reveal` or echoing the task **before** the run. Dry-run stdout is scored later; a leak cannot be un-primed. |
| Registry leak | `conf/soak_probes.json` is inside the repo and carries every `fact` / `discriminator`. Scoring must run `util/ad-hoc/2026-08-21_soak_probe_evidence.py`; contaminated runs are discarded. |
| Completed session, empty parse | `parse_events` used to do `ev.get("message") or {}`; a **string** `message` then raised `AttributeError` **after the session was spent**. Type guard is in-tree (juniper-ml#1616): `if not isinstance(msg, dict): continue`. Keep `stream.jsonl` and re-parse; do not re-run. |
| Channel says follow, maybe not | Mechanical match is `pointer_doc in tool_inputs+answer`. If the task itself contains `--dest docs/REFERENCE.md` (P06), the path appears whether or not the doc was read. Verify by hand (`grep` headings, then a line-range read). |
| `--dry-run` exits 2, no preview | Ledger verdict is terminal. Pass `--force`; the refuse is before the dry-run branch. |
| Probe reaped mid-run | Interpreter was `JuniperC*`, or the pidfile was only in `reports/soak/runs/`. A lost run is **not** a miss. |
| Timer keeps spending after a terminal verdict | Pass `--force` only for a deliberate characterisation probe; disable the timer if the pooled question is done. Characterisation also needs `--probe-id` — least-covered will not pick the ambiguous probes. |
| Discriminator under-specifies | Enumerating acceptable answers (P06: "scope **or** refuse") mis-scores a better third path. Score the **property**; record tension in `--note`. Registry-author item. |
| `status` exits 1 | Open escalation or `BET-FAILING`. Do not `resolve` to green it. |
| `--probe-id P19` → `no such probe` | Bare ids do not resolve. Use the full slug (`P19-port-check-fail-opens`). |
| `probe-run --outcome miss` rejected | Missing `--class`. Required values: `discoverability` / `hazard` / `pointer-defect`. |
| `--status` numbers look like a follow table | They are **post-intervention run counts**, a different quantity. |
| Three more non-follows redden `main` | 26/40 → 26/43 Wilson upper 0.736 arms the guard; `DryRunDoesNotLeakTheTask` fails on 3.12/3.13/3.14. No code change required. |
| `report` looks terminal after a channel change | `analyse()` pools pre- and post-intervention. Split as §15.4 requires before treating a pooled upper bound as a stop. |
| Retention jumped with no new follows | `rescore` is one-way to `source-recovered`. Re-read the original `outcome` column. |

Coverage: `tests/test_soak_ledger.py`, `tests/test_soak_next_probe.py`, `tests/test_soak_run_probe.py` (hermetic — never launches `claude`). `util/` is outside every pre-commit Python hook, so those suites **are** the gate.

---

## Pointer-Follow Soak

The pointer-follow soak measures whether a **fresh, unprimed** Claude session retrieves a **relocated** fact from its pointer (usually a `docs/REFERENCE.md` heading) rather than from source. Owner decision 2026-09-03: the soak exists **to inform relocation decisions**, not to print a pooled pass/fail about "relocation in general."

Protocol: [`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](../notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md). Trigger and characterisation: [`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`](../notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md).

### Pieces

| Piece | Role |
|-------|------|
| `conf/soak_probes.json` | Frozen seeded-arm registry. Never edit a probe that already has runs; add a new id. |
| `reports/soak/pointer_follow_soak.jsonl` | Append-only ledger (observations, rescores, resolves, invalidates). |
| `util/soak_next_probe.py` | Prints the **task only** (probe id on stderr). `--reveal` is scoring-only. |
| `util/soak_run_probe.py` | Headless `claude -p` wrapper: dispatch, capture, retrieval channel, scoring packet. |
| `util/soak_ledger.py` | `probe-run` / `report` / `status` / `verify-probes` / `resolve` / `rescore`. |
| `util/systemd/juniper-soak-probe.{service,timer,path}` | Unattended **user** units (same wrapper). |

`verify-probes` is the residency gate: every probe's `must_be_absent_from_source` phrases must be absent from `AGENTS.md`, and every `pointer` anchor must resolve. The 2026-08-21 pilot ran nine probes whose facts had never left `AGENTS.md`; those tested nothing. CI runs `python3 util/soak_ledger.py verify-probes`.

### Operator loop

```bash
python3 util/soak_run_probe.py --dry-run                    # no claude binary required
python3 util/soak_run_probe.py                              # least-covered probe
python3 util/soak_run_probe.py --probe-id P23-reaper-over-protection-bias
python3 util/soak_next_probe.py --reveal --probe-id <id>    # AFTER the run, for scoring
python3 util/soak_ledger.py probe-run --probe-id <id> \
    --outcome follow|source-recovered|miss --session <uuid> --scored-by <who>
python3 util/soak_ledger.py report
python3 util/soak_ledger.py status                          # exit 1 is often by design
```

`--dry-run` must not print the task, fact, or discriminator: this wrapper's stdout is read by the operator who later **scores** the run, and echoing the task there re-primes at the far end of the pipeline.

Wrapper exit codes: `0` usable answer + scoring packet; `1` timeout / empty / error result; `2` misuse, or the harness failed before the probe started (including terminal-verdict refuse). Ledger: `probe-run` / `record` / `resolve` → `0` written / `2` rejected; `report` always `0`; `status` → `0` in-progress or holds, **`1` action due**, `2` no data; `verify-probes` → `0` sound / `1` defective.

### Automated vs judgement

Automated (mechanical): probe selection, unprimed dispatch, transcript capture, the **retrieval channel** — did tool inputs or the answer contain the pointer *document path* (anchor stripped)?

Not automated: correctness against the frozen `discriminator`. The wrapper writes `reports/soak/runs/<stamp>-<probe>/scoring_packet.md` and stops. `soak_ledger.py probe-run` still needs a scorer to supply `--outcome`.

Outcomes (`OUTCOMES` in `util/soak_ledger.py`):

| Outcome | Meaning | Follow-rate |
|---------|---------|-------------|
| `follow` | Correct **and** retrieved via the pointer | numerator |
| `source-recovered` | Correct, reached from source (helper / test / grep), not the pointer | stays in **denominator** |
| `miss` | Acted without the fact | denominator |

`rate` = follows / (follow + miss + source-recovered). `retention` = (follow + source-recovered) / n answers a different question — *did relocation lose the fact?* — and is printed beside the rate, never instead of it. Dropping source-recovered from the denominator was considered and rejected: it would convert `INCONCLUSIVE` into a pass by redefinition.

### Least-covered vs characterisation

Default `soak_next_probe.py` / `soak_run_probe.py` pick **least-covered, then registry order**. That evens the **pooled** estimate.

For a relocation decision the pooled rate is a **mixture**. Characterisation runs (juniper-ml#1616, 2026-09-04; design-conversation §9) selected probes to test membership, not coverage:

- Permutation test (15 probes, 40 runs, 26 follows, 20,000 draws): heterogeneity statistic 30.84, **p = 0.0017**. The probes do not share one rate. Use the stratum, not ~65%, for a specific section.
- **Per-probe membership is not resolved at n=2–4.** P23 left the "never-follow" group on its third run (0/2 → follow → 1/3). No probe's 95% CI excludes 50% or the pooled rate. Do not treat "P14 never follows" as a property from 0/3.
- Next cheapest design: drive ambiguous probes (P21 / P23 at 1/3; the 0/3 set) to **n≈8–10**, not even coverage. The timer still fires least-covered — pass `--probe-id` for characterisation.
- Stopping rule: `soak_run_probe.py` refuses when `status` starts with `BET-FAILING` or `HOLDS-AT-` unless `--force`. Under decision support a terminal **pooled** verdict does not answer the next relocation; `--force` is the deliberate override, not a way to ignore a real stop.

### Verdicts (seeded arm)

Wilson 95% interval vs one reachable boundary (`DECISION_BOUNDARY = 0.75`). Named after what was proven. `BET-HOLDS` is **not** a printable verdict.

| Verdict | Meaning |
|---------|---------|
| `IN-PROGRESS` | fewer than 35 seeded runs or 15 distinct probes |
| `HOLDS-AT-0.75` | Wilson lower bound ≥ 0.75 |
| `BET-FAILING` | Wilson upper bound < 0.75 |
| `INCONCLUSIVE` | interval spans 0.75, or hazard stratum empty |
| `DEGRADED` / `NO-DATA` / `NO-SEEDED-DATA` | instrument integrity; outranks a healthy-looking rate |

Escalations (hazard rung 2, area-systematic rung 3, pointer-defect rung 0) print **alongside** the verdict, never instead of it. `status` exits `1` when they are open — that is the design. `resolve` appends to an append-only ledger; there is no un-resolve. Do not discharge to make the exit code 0.

The **organic** arm is descriptive only (an upper bound). Never used for a verdict.

### Unattended path

These are **user** units, not system units: the probe must see `~/.claude/projects/.../memory/MEMORY.md`. A system unit runs as root with a different `HOME` and measures nothing (same class that ruled out cloud routines).

```bash
mkdir -p ~/.config/systemd/user
cp util/systemd/juniper-soak-probe.* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now juniper-soak-probe.timer   # or the .path unit
systemctl --user start juniper-soak-probe                # one-off; no [Install] on the service
```

Enable the **timer** or **path** unit, not the service. An `[Install]` block on the service is deliberately absent: enabling it would fire an extra uncoordinated probe at every login.

- `ExecStart=/usr/bin/python3 util/soak_run_probe.py --timeout 900` — the reaper candidate filter matches cmdline text `/JuniperC[a-z0-9]+/`; a conda interpreter is reapable from the same cwd. `/usr/bin/python3` is not a candidate.
- `TimeoutStartSec=1500` must exceed dispatch (120s) + claude (900s) + `--reveal` (120s). If systemd wins the race it cgroup-kills the wrapper **before** `status.json` is written ("crash, not timeout").
- Timer: `OnCalendar=*-*-* 03,09,15,21:23:00`, `Persistent=false` (a laptop resuming after two days must not stampede missed intervals).
- Both the unit and the wrapper unset `ANTHROPIC_API_KEY` — a stale key fails with `Credit balance is too low` before the probe starts.
- Reaper P1 pidfile: `$JUNIPER_EXP_RUN_ROOT/soak-probes/soak-probe-<pid>.pid` (default `~/.local/state/juniper-experiments`). A pidfile under `reports/soak/runs/` is **not scanned**.

### Pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Primed follow | `--reveal` or echoing the task **before** the run. Dry-run stdout is scored later; a leak cannot be un-primed. |
| Registry leak | `conf/soak_probes.json` is inside the repo and carries every `fact` / `discriminator`. Scoring must run `util/ad-hoc/2026-08-21_soak_probe_evidence.py`; contaminated runs are discarded. |
| Completed session, empty parse | `parse_events` does `ev.get("message") or {}`; a **string** `message` then raises `AttributeError` **after the session is spent**. Keep `stream.jsonl` and re-parse; do not re-run. Type guard: open juniper-ml#1616. |
| Channel says follow, maybe not | Mechanical match is `pointer_doc in tool_inputs+answer`. If the task itself contains `--dest docs/REFERENCE.md` (P06), the path appears whether or not the doc was read. Verify by hand (`grep` headings, then a line-range read). |
| Probe reaped mid-run | Interpreter was `JuniperC*`, or the pidfile was only in `reports/soak/runs/`. A lost run is **not** a miss. |
| Timer keeps spending | Terminal verdict refuse needs `--force`. Characterisation also needs `--probe-id` — least-covered will not pick the ambiguous probes. |
| Discriminator under-specifies | Enumerating acceptable answers (P06: "scope **or** refuse") mis-scores a better third path. Score the **property**; record tension in `--note`. Registry-author item. |
| `status` exits 1 | Open escalation or `BET-FAILING`. Do not `resolve` to green it. |

Coverage: `tests/test_soak_ledger.py`, `tests/test_soak_next_probe.py`, `tests/test_soak_run_probe.py` (hermetic — never launches `claude`). `util/` is outside every pre-commit Python hook, so those suites **are** the gate.

A live soak probe is also a P1 protectee: `util/soak_run_probe.py` writes `$JUNIPER_EXP_RUN_ROOT/soak-probes/soak-probe-<pid>.pid`. A pidfile under `reports/soak/runs/` is **not** scanned. Operator surface: [Pointer-Follow Soak](#pointer-follow-soak).

---

## Pointer-Follow Soak

The pointer-follow soak asks whether a **fresh, unprimed** local `claude -p` session retrieves a relocated fact from the auto-memory index.

- Protocol: [`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](../notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md)
- Trigger / unattended-path design: [`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`](../notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md)
- Role analysis (why a user unit, not a system unit): [`notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md)

Subagents, cloud routines, and CronCreate cannot see the intervention (ledger §§17, 19). The wrappers exist so the only remaining human step is the judgement the protocol reserves: correctness against the frozen `discriminator`.

| Tool | Role |
|------|------|
| `conf/soak_probes.json` | Frozen seeded-arm registry. Never edit a probe that already has runs; add a new id. |
| `util/soak_next_probe.py` | Prints the **task only** (probe id on stderr). `--reveal` is scoring-only. `--status` is **post-intervention run counts**, not a follow/n table. |
| `util/soak_run_probe.py` | Headless `claude -p` wrapper: dispatch, capture, retrieval channel, scoring packet. |
| `util/soak_ledger.py` | `probe-run` / `report` / `status` / `verify-probes` / `resolve` / `rescore`. |

`verify-probes` is the residency gate: every probe's `must_be_absent_from_source` phrases must be absent from `AGENTS.md`, and every `pointer` anchor must resolve. CI runs `python3 util/soak_ledger.py verify-probes` after the three soak suites.

Probe ids are **full slugs**. `--probe-id P19` exits `2` (`no such probe: P19`). Real ids look like `P19-port-check-fail-opens`.

```bash
python3 util/soak_run_probe.py --dry-run                    # no claude binary required
python3 util/soak_run_probe.py                              # least-covered probe
python3 util/soak_run_probe.py --probe-id P23-reaper-over-protection-bias
python3 util/soak_run_probe.py --probe-id P23-reaper-over-protection-bias --force
python3 util/soak_next_probe.py --reveal --probe-id P23-reaper-over-protection-bias
python3 util/soak_ledger.py probe-run --probe-id P23-reaper-over-protection-bias \
    --outcome follow --session <uuid> --scored-by <who>
python3 util/soak_ledger.py probe-run --probe-id P15-worktree-converge-not-remove \
    --outcome miss --class discoverability --session <uuid> --scored-by <who>
python3 util/soak_ledger.py report
python3 util/soak_ledger.py status
```

`--outcome miss` **requires** `--class` (`discoverability` / `hazard` / `pointer-defect`). Omitting it is a `_reject` (exit `2`). `--class` on `follow` is also rejected.

`--dry-run` must not print the task, fact, or discriminator: this wrapper's stdout is read by the operator who later **scores** the run, and echoing the task there re-primes at the far end of the pipeline.

### Dry-run is not a billed session

The stopping rule in `soak_run_probe.py` rations **billed sessions**. Both call sites go through `verdict_is_terminal()` (`BET-FAILING` / `HOLDS-AT-` prefix). `refuses_terminal_verdict(verdict, force=, dry_run=)` (juniper-ml#1690) is false when `force` **or** `dry_run` is set — the exemptions are not symmetric: `--force` is a deliberate spend override; `--dry-run` spends nothing and was never in the rule's scope.

| Invocation | Terminal verdict (`BET-FAILING` / `HOLDS-AT-*`) | Non-terminal (`INCONCLUSIVE`, …) |
|------------|-----------------------------------------------|----------------------------------|
| `--dry-run` | exit **0**; preview on stdout; `NOTE: … This dry run proceeds (it spends no session); a real run would refuse without --force.` on stderr. No `REFUSING`. | exit **0**; preview; no NOTE |
| real run | exit **2**; `REFUSING: soak verdict is … each one spends a session.` unless `--force` | proceeds |
| real run `--force` | proceeds (re-baseline / characterisation) | proceeds |

`--dry-run` still does not require the `claude` binary (resolved lazily after the dry-run branch). A dry run must not depend on the thing it is only describing — that comment predates #1690; the verdict check reintroduced the same class through a different door.

**Pre-#1690 (the defect, not the contract).** The refuse ran *before* the `--dry-run` branch, so a terminal ledger made `--dry-run` exit 2 with **empty stdout**. That is the failure `DryRunDoesNotLeakTheTask` hits on every CI Python once any three non-follow rows push the Wilson upper bound under 0.75 — data, not a code change.

From today's 26/40 the ledger's own `wilson()` gives 26/42 upper `0.750002742` (still INCONCLUSIVE) and **26/43 upper `0.736`**, which arms the unfixed guard. Do not "fix" a dry-run preview by passing `--force`; after #1690 the preview is the default.

`--force` overrides a **real** run only. Design-conversation §8.3 leaves the pooled-verdict guard in place so unattended spend cannot run away; under decision support a terminal pooled verdict does not answer the next relocation. Do not pass `--force` to preview (that is `--dry-run`) or to keep a timer spending after the pooled question is done (disable the timer).

Wrapper exit codes: `0` usable answer + scoring packet (or a successful dry-run preview); `1` timeout / empty / error result; `2` misuse, harness failure before the probe started, or a real-run terminal refuse.

Ledger exits (`util/soak_ledger.py` docstring): `probe-run` / `record` / `resolve` → `0` written / `2` rejected; `report` always `0`; `status` → `0` for `IN-PROGRESS` / `HOLDS-AT-*` / `INCONCLUSIVE` with no escalations, **`1` on `BET-FAILING` or an open escalation**, `2` for `NO-DATA` / `DEGRADED` / `NO-SEEDED-DATA`; `verify-probes` → `0` sound / `1` defective.

### What is automated

Automated, because it is mechanical: least-covered probe pick, unprimed dispatch, transcript capture, and the **retrieval channel** (did the run touch the pointer document?).

Not automated: correctness against the frozen `discriminator`. The wrapper writes `reports/soak/runs/<stamp>-<probe>/scoring_packet.md` and stops. `soak_ledger.py probe-run` still needs a scorer to supply `--outcome`.

Outcomes (`OUTCOMES` in `util/soak_ledger.py`): `follow`, `miss`, `source-recovered`. **Seeded** arm decides; **organic** describes (an upper bound, never a verdict). `source-recovered` stays in the follow-rate denominator — dropping it would convert INCONCLUSIVE into a pass by redefinition.

Default `soak_next_probe.py` / `soak_run_probe.py` pick **least-covered, then registry order**. That evens the **pooled** estimate. Characterisation of a named probe uses `--probe-id`. `--reveal` is scoring-only and must not run before the session.

`analyse()` has **no era filter**. Ledger §15.4 says not to pool post-intervention runs with the pre-`2026-08-31` ones. Split on this tree with the ledger's own `wilson()` after `analyse()`'s invalidate/rescore/`in_scope` filters:

| era | follows/n | Wilson 95% | terminal? |
|-----|-----------|------------|-----------|
| pre-intervention (`ts < 2026-08-31`) | 24/35 = 68.6% | [0.520, 0.814] | no |
| post-intervention | 2/5 = 40.0% | [0.118, 0.769] | no |
| pooled (what `report` prints) | 26/40 = 65.0% | [0.495, 0.779] | no (`INCONCLUSIVE`) |

Per-probe (effective outcome after rescores; Wilson on follows/n): `P14` / `P15` / `P19` are 0/3 → [0.000, 0.561]; `P21` / `P23` are 1/3 → [0.061, 0.792]. None excludes 50%.

**Do not drive the ambiguous probes to n≈8–10.** Design-conversation §9.4 recommended that band; it cannot resolve stratum membership at the observed 1/3 rate. Re-derived with this repo's `wilson()`: 3/8 [0.137, 0.694], 3/10 [0.108, 0.603], 9/26 [0.194, 0.538] — none excludes 50%. First exclude is **10/31** [0.186, 0.499]. `--probe-id` still picks a named probe if an owner later authorises one; the default / timer path will not.

### Verdicts

Wilson 95% interval vs `DECISION_BOUNDARY = 0.75` (`util/soak_ledger.py` `analyse`). Named after what was proven, not the point estimate.

| Verdict | Meaning |
|---------|---------|
| `IN-PROGRESS` | fewer than `TARGET_PROBE_RUNS = 35` seeded runs or `MIN_DISTINCT_PROBES = 15` |
| `HOLDS-AT-0.75` | Wilson lower bound ≥ 0.75 |
| `BET-FAILING` | Wilson upper bound < 0.75 |
| `INCONCLUSIVE` | interval spans 0.75, or the hazard stratum is empty |
| `NO-DATA` / `DEGRADED` / `NO-SEEDED-DATA` | instrument is not readable; `status` exits 2 |

Escalations (hazard rung 2, area-systematic rung 3, pointer-defect rung 0) print **alongside** the verdict, never instead of it. `status` exits `1` when they are open or the verdict is `BET-FAILING` — that is the design. `resolve` appends to an append-only ledger; there is no un-resolve. Do not discharge to make the exit code 0.

Verified against `origin/main` `d69c9a73` (`python3 util/soak_ledger.py status` / `report`): **INCONCLUSIVE**, seeded 40/35, rate 65.0%, Wilson 95% CI [0.495, 0.779], **retention 95.0%** [0.835, 0.986], escalations 0, `status` exit 0. Retention is high: relocation is not losing facts; pointer-following is not what prevents the loss.

### Retrieval channel

`parse_events` walks `tool_use` blocks only (none of the three soak scripts read `tool_result`). `retrieval_channel` then searches `tool_inputs + answer` for the pointer **document path** with the `#anchor` stripped.

Reciting the path in the answer scores as a pointer hit even when no tool opened the document. A directory-scoped grep that names `docs/` (not `docs/REFERENCE.md`) is invisible to it. P06's task contains `--dest docs/REFERENCE.md`, so the path appears whether or not the doc was read. The channel only `suggests`; a human supplies `--outcome`.

Keep `stream.jsonl` if parse crashes: some events carry `message` as a bare string; `parse_events` type-guards `isinstance(msg, dict)` (juniper-ml#1616).

`rescore` accepts **only** `--to source-recovered` (`RESCORE_OUTCOMES`). The verb is one-way and can only raise retention.

### Reaper and systemd

Pidfile must be under `$JUNIPER_EXP_RUN_ROOT/soak-probes/` (`JUNIPER_EXP_RUN_ROOT` default `~/.local/state/juniper-experiments`). `collect_protected_pids` walks only that root and `$JUNIPER_E2E_RUN_DIR`. A pidfile under `reports/soak/runs/` grants nothing.

User units in `util/systemd/` (not system units — the probe must see the operator's `MEMORY.md`):

- `ExecStart=/usr/bin/python3 util/soak_run_probe.py --timeout 900` — the reaper candidate filter matches cmdline text `/JuniperC[a-z0-9]+/`; a conda interpreter is reapable from the same cwd. `/usr/bin/python3` is not a candidate.
- `TimeoutStartSec=1500` vs wrapper `--timeout 900` (dispatch 120 + claude 900 + reveal 120 = 1140; 1500 is the real margin).
- Timer: `OnCalendar=*-*-* 03,09,15,21:23:00`, `Persistent=false` (a laptop resuming after two days must not stampede missed intervals).
- `Type=oneshot` with no `SuccessExitStatus=`. A real-run terminal refuse is exit 2, so once the verdict is terminal every timer firing marks `failed`. The units are additive; they are not installed by a repo hook. #1690 does not cause this but makes it reachable.
- No `[Install]` on the service — enable the `.timer` / `.path`, never the service itself (an extra uncoordinated probe at every login).
- Both the unit and the wrapper unset `ANTHROPIC_API_KEY` — a stale key fails with `Credit balance is too low` before the probe starts.

### Known-not-fixed (do not "simplify")

The guard **fails open**. `st.returncode` is never checked. An absent or unreadable ledger yields `NO-DATA` (rc=2 from `status`), not `verdict=""` — empty verdict requires the ledger *tool* itself to fail to run. `DEGRADED` and `NO-SEEDED-DATA` pass the spend control too. Closing this is a fail-closed semantics change (how much an unattended timer may spend when it cannot read a verdict) and is out of scope for #1690.

### Operator pitfalls

| Symptom | Check / Fix |
|---------|-------------|
| `--dry-run` exits 2, empty stdout | Pre-#1690 refuse-before-dry-run. After #1690 a terminal verdict still previews (NOTE on stderr). Do not pass `--force` just to see the preview. |
| Real run exits 2 with `REFUSING` | Ledger is terminal. `--force` overrides a real run only; disable the timer if the pooled question is done. Characterisation also needs `--probe-id`. |
| `--probe-id P19` → `no such probe` | Bare ids do not resolve. Use the full slug (`P19-port-check-fail-opens`). |
| `probe-run --outcome miss` rejected | Missing `--class`. Required: `discoverability` / `hazard` / `pointer-defect`. |
| `--status` numbers look like a follow table | They are **post-intervention run counts**, a different quantity. |
| Driving P21/P23 to n≈8–10 "to resolve membership" | Wilson at 1/3 does not exclude 50% inside that band (first exclude is 10/31). |
| Three more non-follows redden `main` | 26/40 → 26/43 Wilson upper 0.736 arms the pre-#1690 guard; `DryRunDoesNotLeakTheTask` fails on 3.12/3.13/3.14. |
| Channel says follow, maybe not | Mechanical match is `pointer_doc in tool_inputs+answer`. P06's `--dest docs/REFERENCE.md` is a false-positive risk. The instrument does not see `tool_result`. |
| `report` looks terminal after a channel change | `analyse()` pools pre- and post-intervention. Split as §15.4 requires before treating a pooled upper bound as a stop. |
| Retention jumped with no new follows | `rescore` is one-way to `source-recovered`. Re-read the original `outcome` column. |
| Dry-run stdout contains the task | Bug — priming leak. `tests/test_soak_run_probe.py` `DryRunDoesNotLeakTheTask` is the gate. |
| Timer keeps spending after a terminal verdict | Disable the timer; `--force` is not the stop. |
| `status` exits 1 | Open escalation or `BET-FAILING`. Do not `resolve` to green it. |
| Probe reaped mid-run | Pidfile was under `reports/soak/runs/`, or the interpreter was a `JuniperC*` conda path. |
| Timer unit `failed` after a terminal verdict | `Type=oneshot` treats exit 2 as failure. Expected once the pooled question is done. |

Coverage: `tests/test_soak_ledger.py`, `tests/test_soak_next_probe.py`, `tests/test_soak_run_probe.py` (hermetic — never launches `claude`). `util/` is outside every pre-commit Python hook, so those suites **are** the gate. #1690 adds `TerminalVerdictDoesNotGateADryRun` (predicate + `main()`-level stub of the ledger line; the live-ledger end-to-end pin was vacuous and was rewritten).

---

## Pointer-Follow Soak

The pointer-follow soak measures whether a **fresh, unprimed** Claude session retrieves a **relocated** fact from its pointer (usually a `docs/REFERENCE.md` heading) rather than from source. Owner decision 2026-09-03: the soak exists **to inform relocation decisions**, not to print a pooled pass/fail about "relocation in general."

Protocol: [`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](../notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md). Trigger and characterisation: [`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`](../notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md).

### Pieces

| Piece | Role |
|-------|------|
| `conf/soak_probes.json` | Frozen seeded-arm registry. Never edit a probe that already has runs; add a new id. |
| `reports/soak/pointer_follow_soak.jsonl` | Append-only ledger (observations, rescores, resolves, invalidates). |
| `util/soak_next_probe.py` | Prints the **task only** (probe id on stderr). `--reveal` is scoring-only. |
| `util/soak_run_probe.py` | Headless `claude -p` wrapper: dispatch, capture, retrieval channel, scoring packet. |
| `util/soak_ledger.py` | `probe-run` / `report` / `status` / `verify-probes` / `resolve` / `rescore`. |
| `util/systemd/juniper-soak-probe.{service,timer,path}` | Unattended **user** units (same wrapper). |

`verify-probes` is the residency gate: every probe's `must_be_absent_from_source` phrases must be absent from `AGENTS.md`, and every `pointer` anchor must resolve. The 2026-08-21 pilot ran nine probes whose facts had never left `AGENTS.md`; those tested nothing. CI runs `python3 util/soak_ledger.py verify-probes`.

### Operator loop

```bash
python3 util/soak_run_probe.py --dry-run                    # no claude binary required
python3 util/soak_run_probe.py                              # least-covered probe
python3 util/soak_run_probe.py --probe-id P23-reaper-over-protection-bias
python3 util/soak_next_probe.py --reveal --probe-id <id>    # AFTER the run, for scoring
python3 util/soak_ledger.py probe-run --probe-id <id> \
    --outcome follow|source-recovered|miss --session <uuid> --scored-by <who>
python3 util/soak_ledger.py report
python3 util/soak_ledger.py status                          # exit 1 is often by design
```

`--dry-run` must not print the task, fact, or discriminator: this wrapper's stdout is read by the operator who later **scores** the run, and echoing the task there re-primes at the far end of the pipeline.

Wrapper exit codes: `0` usable answer + scoring packet; `1` timeout / empty / error result; `2` misuse, or the harness failed before the probe started (including terminal-verdict refuse). Ledger: `probe-run` / `record` / `resolve` → `0` written / `2` rejected; `report` always `0`; `status` → `0` in-progress or holds, **`1` action due**, `2` no data; `verify-probes` → `0` sound / `1` defective.

### Automated vs judgement

Automated (mechanical): probe selection, unprimed dispatch, transcript capture, the **retrieval channel** — did tool inputs or the answer contain the pointer *document path* (anchor stripped)?

Not automated: correctness against the frozen `discriminator`. The wrapper writes `reports/soak/runs/<stamp>-<probe>/scoring_packet.md` and stops. `soak_ledger.py probe-run` still needs a scorer to supply `--outcome`.

Outcomes (`OUTCOMES` in `util/soak_ledger.py`):

| Outcome | Meaning | Follow-rate |
|---------|---------|-------------|
| `follow` | Correct **and** retrieved via the pointer | numerator |
| `source-recovered` | Correct, reached from source (helper / test / grep), not the pointer | stays in **denominator** |
| `miss` | Acted without the fact | denominator |

`rate` = follows / (follow + miss + source-recovered). `retention` = (follow + source-recovered) / n answers a different question — *did relocation lose the fact?* — and is printed beside the rate, never instead of it. Dropping source-recovered from the denominator was considered and rejected: it would convert `INCONCLUSIVE` into a pass by redefinition.

### Least-covered vs characterisation

Default `soak_next_probe.py` / `soak_run_probe.py` pick **least-covered, then registry order**. That evens the **pooled** estimate.

For a relocation decision the pooled rate is a **mixture**. Characterisation runs (juniper-ml#1616, 2026-09-04; design-conversation §9) selected probes to test membership, not coverage:

- Permutation test (15 probes, 40 runs, 26 follows, 20,000 draws): heterogeneity statistic 30.84, **p = 0.0017**. The probes do not share one rate. Use the stratum, not ~65%, for a specific section.
- **Per-probe membership is not resolved at n=2–4.** P23 left the "never-follow" group on its third run (0/2 → follow → 1/3). No probe's 95% CI excludes 50% or the pooled rate. Do not treat "P14 never follows" as a property from 0/3.
- Next cheapest design: drive ambiguous probes (P21 / P23 at 1/3; the 0/3 set) to **n≈8–10**, not even coverage. The timer still fires least-covered — pass `--probe-id` for characterisation.
- Stopping rule: `soak_run_probe.py` refuses when `status` starts with `BET-FAILING` or `HOLDS-AT-` unless `--force`. Under decision support a terminal **pooled** verdict does not answer the next relocation; `--force` is the deliberate override, not a way to ignore a real stop.

### Verdicts (seeded arm)

Wilson 95% interval vs one reachable boundary (`DECISION_BOUNDARY = 0.75`). Named after what was proven. `BET-HOLDS` is **not** a printable verdict.

| Verdict | Meaning |
|---------|---------|
| `IN-PROGRESS` | fewer than 35 seeded runs or 15 distinct probes |
| `HOLDS-AT-0.75` | Wilson lower bound ≥ 0.75 |
| `BET-FAILING` | Wilson upper bound < 0.75 |
| `INCONCLUSIVE` | interval spans 0.75, or hazard stratum empty |
| `DEGRADED` / `NO-DATA` / `NO-SEEDED-DATA` | instrument integrity; outranks a healthy-looking rate |

Escalations (hazard rung 2, area-systematic rung 3, pointer-defect rung 0) print **alongside** the verdict, never instead of it. `status` exits `1` when they are open — that is the design. `resolve` appends to an append-only ledger; there is no un-resolve. Do not discharge to make the exit code 0.

The **organic** arm is descriptive only (an upper bound). Never used for a verdict.

### Unattended path

These are **user** units, not system units: the probe must see `~/.claude/projects/.../memory/MEMORY.md`. A system unit runs as root with a different `HOME` and measures nothing (same class that ruled out cloud routines).

```bash
mkdir -p ~/.config/systemd/user
cp util/systemd/juniper-soak-probe.* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now juniper-soak-probe.timer   # or the .path unit
systemctl --user start juniper-soak-probe                # one-off; no [Install] on the service
```

Enable the **timer** or **path** unit, not the service. An `[Install]` block on the service is deliberately absent: enabling it would fire an extra uncoordinated probe at every login.

- `ExecStart=/usr/bin/python3 util/soak_run_probe.py --timeout 900` — the reaper candidate filter matches cmdline text `/JuniperC[a-z0-9]+/`; a conda interpreter is reapable from the same cwd. `/usr/bin/python3` is not a candidate.
- `TimeoutStartSec=1500` must exceed dispatch (120s) + claude (900s) + `--reveal` (120s). If systemd wins the race it cgroup-kills the wrapper **before** `status.json` is written ("crash, not timeout").
- Timer: `OnCalendar=*-*-* 03,09,15,21:23:00`, `Persistent=false` (a laptop resuming after two days must not stampede missed intervals).
- Both the unit and the wrapper unset `ANTHROPIC_API_KEY` — a stale key fails with `Credit balance is too low` before the probe starts.
- Reaper P1 pidfile: `$JUNIPER_EXP_RUN_ROOT/soak-probes/soak-probe-<pid>.pid` (default `~/.local/state/juniper-experiments`). A pidfile under `reports/soak/runs/` is **not scanned**.

### Pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Primed follow | `--reveal` or echoing the task **before** the run. Dry-run stdout is scored later; a leak cannot be un-primed. |
| Registry leak | `conf/soak_probes.json` is inside the repo and carries every `fact` / `discriminator`. Scoring must run `util/ad-hoc/2026-08-21_soak_probe_evidence.py`; contaminated runs are discarded. |
| Completed session, empty parse | `parse_events` does `ev.get("message") or {}`; a **string** `message` then raises `AttributeError` **after the session is spent**. Keep `stream.jsonl` and re-parse; do not re-run. Type guard: open juniper-ml#1616. |
| Channel says follow, maybe not | Mechanical match is `pointer_doc in tool_inputs+answer`. If the task itself contains `--dest docs/REFERENCE.md` (P06), the path appears whether or not the doc was read. Verify by hand (`grep` headings, then a line-range read). |
| Probe reaped mid-run | Interpreter was `JuniperC*`, or the pidfile was only in `reports/soak/runs/`. A lost run is **not** a miss. |
| Timer keeps spending | Terminal verdict refuse needs `--force`. Characterisation also needs `--probe-id` — least-covered will not pick the ambiguous probes. |
| Discriminator under-specifies | Enumerating acceptable answers (P06: "scope **or** refuse") mis-scores a better third path. Score the **property**; record tension in `--note`. Registry-author item. |
| `status` exits 1 | Open escalation or `BET-FAILING`. Do not `resolve` to green it. |

Coverage: `tests/test_soak_ledger.py`, `tests/test_soak_next_probe.py`, `tests/test_soak_run_probe.py` (hermetic — never launches `claude`). `util/` is outside every pre-commit Python hook, so those suites **are** the gate.

---

## Environment Floor Drift Check

`util/env_floor_drift_check.py` (gap I-2) compares each `juniper-*` floor declared in a target repo's `pyproject.toml` against the **installed** wheel version read from `*.dist-info/METADATA` — the below-floor plain-wheel case that pin-linters and the editable checker miss. It does **not** invoke the environment's interpreter (so a broken env still reports).

Classifications: `OK` (installed ≥ floor), `BELOW_FLOOR` (installed < floor), `MISSING` (not installed). Exit `0` when no `BELOW_FLOOR`; `1` on any `BELOW_FLOOR` (`--strict` also fails on `MISSING`); `2` on invocation/resolution errors.

#### Env selection precedence (`resolve_site_dirs`)

Env names are **never** hardcoded. Resolution order (`util/env_floor_drift_check.py` `resolve_site_dirs`):

1. `--site-packages PATH` (repeatable) — scan those dirs; missing paths → exit `2` with `no --site-packages dir exists: …`
2. Else `--env NAME` (repeatable) — expand `<conda-dir>/envs/<NAME>/lib/python*/site-packages`; empty expand → exit `2` with `no site-packages under …`
3. Else `prompts/agent_templates/data/ecosystem.yaml` — map the target `[project].name` via `conda_envs[].used_by`; missing name/mapping/site-packages → exit `2` with the matching reason (pass `--env` or `--site-packages` to override)

Default `--conda-dir` is `$JUNIPER_CONDA_DIR` or `/opt/miniforge3`.

```bash
# Explicit env (host verify against canopy floors)
python util/env_floor_drift_check.py --repo-root ../juniper-canopy --env JuniperCanopy1

# CI / hermetic: point at a synthetic or known site-packages tree
python util/env_floor_drift_check.py --repo-root . --site-packages /path/to/site-packages --json

# Let ecosystem.yaml used_by resolve the env for this checkout's [project].name
python util/env_floor_drift_check.py --repo-root .
```

#### Multi-site / multi-interpreter versions

When an env (or repeated `--site-packages`) yields several `site-packages` dirs, `installed_juniper_versions` keeps the **highest** version across them. A later lower wheel must not clobber an earlier higher one (false `BELOW_FLOOR`). Underscore dist names normalize to kebab-case; malformed / unreadable `METADATA` and non-`juniper-*` dists are skipped.

Coverage: open juniper-ml#796 (`ResolveSiteDirsTest` — precedence + exit-2 reasons) and #802 (`InstalledVersionsTest` — highest-across-dirs / malformed skip). Structural CI gate: `tests/test_env_floor_drift_check.py` (synthetic dist-info only; real-env scan is host-manual).

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Exit `2`: `no --site-packages dir exists` | Path typo or stale CI fixture — pass a real directory, or drop `--site-packages` and use `--env`. |
| Exit `2`: `no site-packages under … for env(s)` | Env missing under `--conda-dir`, or no `lib/python*/site-packages` yet — create/install into the env. |
| Exit `2`: `no conda env maps to '…' in ecosystem.yaml` | Target `[project].name` has no `used_by` entry — pass `--env` / `--site-packages`, or add the mapping. |
| Unexpected `BELOW_FLOOR` after a partial upgrade | Multi-interpreter env may still have an older site-packages tree — the tool reports the **highest** installed version; upgrade every tree or remove the stale one. |
| `MISSING` but `pip show` works | Checker reads `METADATA` on disk under the resolved dirs only — confirm `--env` / `--site-packages` matches the interpreter you inspected. |
| Floor / editable green, `import torch` still fails | Those checkers never import torch. Classify the ABI/`_C` layout with [Conda Env Torch Shadow Diagnostic](#conda-env-torch-shadow-diagnostic-p-5). |

---

## Conda Env Torch Shadow Diagnostic (P-5)

`util/check_conda_env_torch.bash` classifies a conda env's `import torch` / `torch._C` layout. It does **not** rebuild, rename, or `mamba install`. A misread exit code sends the operator down the wrong recovery: the P-5 free-threaded rebuild versus the May-7 regular-3.14 wheel-layout class.

Both notes surface the same `ImportError: Failed to load PyTorch C extensions` / `torch/_C` folder text. They are **not** the same ABI:

| Note | Typical ABI | Script exit |
|------|-------------|-------------|
| [`JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_CONDA-ENV-REBUILD-PROCEDURE.md`](../notes/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_CONDA-ENV-REBUILD-PROCEDURE.md) (P-5) | Free-threaded `cp*t` interpreter + regular (`cp*`, no `t`) torch wheel | **2** |
| [`JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md`](../notes/JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md) | Regular `cp314` + torch 2.9.1 ships `torch/_C/` stubs **and** `_C.cpython-314-*.so`; import prefers the directory | **4** |

`util/juniper_plant_all.bash` already defaults `JUNIPER_CASCOR_CONDA` and `JUNIPER_WORKER_CONDA` to `JuniperCascor1`. Run the diagnostic before overriding either back to `JuniperCascor`.

### Usage

```bash
util/check_conda_env_torch.bash JuniperCascor
util/check_conda_env_torch.bash JuniperCascor1
util/check_conda_env_torch.bash JuniperCanopy
JUNIPER_CONDA_DIR=/opt/miniforge3 util/check_conda_env_torch.bash JuniperCascor1
```

`JUNIPER_CONDA_DIR` defaults to `/opt/miniforge3`. The script execs `${JUNIPER_CONDA_DIR}/envs/<name>/bin/python` directly — it never `conda activate`s. Missing argv or a non-executable `bin/python` is exit **1** (read stderr: `usage:` vs `env … not found`).

### Exit codes

| Exit | Meaning | What to do |
|------|---------|------------|
| 0 | `import torch` works and `torch._C.__file__` is the `.so` | Env is healthy. A free-threaded `EXT_SUFFIX` **warning** can still print; the warning alone is not a failure. |
| 1 | No env-name argument, or `${CONDA_DIR}/envs/<name>/bin/python` is not executable | Fix the name or `JUNIPER_CONDA_DIR`. |
| 2 | `EXT_SUFFIX` matches `*-cp*t-*` or `*t-x86_64*` **and** `import torch` failed **and** a `torch/_C/` directory exists | P-5 free-threaded shadow. Use Option A (`*1` env) or Option B (rebuild regular CPython) in the [rebuild procedure](../notes/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_CONDA-ENV-REBUILD-PROCEDURE.md). Do **not** treat this as May-7. |
| 3 | `import torch` failed and `find` (`-maxdepth 5`) found no `torch/_C/` directory | Not the shadow. Missing torch (`JuniperData` never ships it), a broken install, or a separate `LIBTORCH` / rust-mudgeon `LD_LIBRARY_PATH` leak. Isolated-stack `cascor_up` empties `LD_LIBRARY_PATH` for that last class. |
| 4 | Non-FT interpreter + import fail + `torch/_C/` on disk, **or** imported `torch._C` has no `__file__` | May-7 namespace-package class. Prefer `JuniperCascor1` / `JuniperCanopy1`. See the [May-7 conda-env fix](../notes/JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md). |

### What the script does not do

- It does not rebuild the env or write conda activate hooks. Recovery lives in the two notes above.
- It does not inspect `LIBTORCH` or rust-mudgeon `LD_LIBRARY_PATH` (P-5 §5 / May-7 §2 secondary). Isolated stack and the env-local activate hooks own that. A leak with no `torch/_C/` directory classifies as exit **3**.
- Floor-drift and editable-drift can stay green on a shadowed env — they read `METADATA`, they never `import torch`.

Coverage: `tests/test_check_conda_env_torch.py` (hermetic stub `bin/python` under `JUNIPER_CONDA_DIR`; no real conda/torch). Wired in `.github/workflows/ci.yml` and `main-verify.yml`.

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Exit `2` after `mamba install python-freethreading` | Expected P-5 class. Do not repair in place (Option C usually fails). Switch to `*1` or rebuild regular CPython. Keep FT exploration in a sandbox env (`JuniperCascor-FT`). |
| Exit `4` on regular 3.14 / torch 2.9.x | Expected May-7 class. Keep plant on `JuniperCascor1`; do not run the P-5 FT rebuild. |
| Exit `3` on `JuniperData` | Expected — that env has no torch. The P-5 plan-doc entry that listed it was over-broad. |
| Exit `0` but stdout warned `free-threaded` | Import and `_C.__file__` succeeded. The warning is ABI-only; do not rebuild from the warning alone. |
| Cascor plant health timeout, log dies at `import torch` | Classify that env first. Default plant already uses `JuniperCascor1` for cascor **and** the worker. |
| Floor / editable report `OK` / `FRESH` | Irrelevant to this failure. Re-run the torch diagnostic. |

---

## Agent Suite Doctor

`util/agent_suite_doctor.py` is the read-only health check for the custom-agent suite (`.claude/agents`, Template Agent Skill, template library, `RUBRIC.md`, data layer, discovery CLI, `~/.claude` mirror). Run it before relying on `/template-agent` or the suite subagents; it writes nothing.

```bash
python util/agent_suite_doctor.py                         # walk up for .github/workflows/
python util/agent_suite_doctor.py --repo-root . --json    # machine-readable report
python util/agent_suite_doctor.py --strict                # WARN counts as failure
python util/agent_suite_doctor.py --no-discovery          # skip discovery CLI (offline / fast)
```

| Flag | Effect |
|------|--------|
| `--repo-root PATH` | Suite root; must contain `.github/workflows/` (else exit `2`) |
| `--json` | Emit `{repo_root, checks[{name,status,reason}], summary}` |
| `--strict` | Exit `1` when any check is `WARN` (default: only `FAIL` fails) |
| `--no-discovery` | Omit the `discovery` check entirely (no `SKIP` row) |

Exit codes: `0` healthy (`WARN` allowed unless `--strict`); `1` ≥1 `FAIL` (or ≥1 `WARN` under `--strict`); `2` bad arguments / non-repo root.

Design-of-record: [`notes/JUNIPER_2026-06-25_JUNIPER-ML_AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md`](../notes/JUNIPER_2026-06-25_JUNIPER-ML_AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md) §P1.

#### Discovery check (`check_discovery`) — fail-closed

Unless `--no-discovery`, the doctor runs `python util/prompt_discovery/cli.py --repo-root <root>` (120s timeout) and requires a contract-shaped grounding bundle. This is the only live validation that the Template Agent’s grounding CLI still works; a broken discovery surface must not report healthy.

| Condition | Status | Reason contains |
|-----------|--------|-----------------|
| `util/prompt_discovery/cli.py` missing | `FAIL` | `missing` |
| CLI exit ≠ 0 | `FAIL` | `exited <code>` + stderr snippet (≤120 chars) |
| stdout is not valid JSON | `FAIL` | `not valid JSON` |
| JSON lacks `schema_version` **or** `provenance.head_sha` | `FAIL` | `schema_version` / `provenance.head_sha` |
| Bundle well-formed | `OK` | `well-formed bundle` |

`--no-discovery` is for offline / CI-speed paths that already exercise discovery elsewhere (`tests/test_prompt_discovery.py`). Do not treat a green `--no-discovery` run as proof the grounding CLI is healthy.

Regression coverage: `tests/test_agent_suite_doctor.py` (`DoctorDiscoveryCheckTest` hermetic fake `cli.py`; juniper-ml#825). Broader suite: same file covers real-repo exit 0, `--json` shape, `--strict`, and non-repo exit 2.

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| `[FAIL] discovery missing .../cli.py` | Restore `util/prompt_discovery/cli.py`; do not paper over with `--no-discovery` for session readiness. |
| `[FAIL] discovery cli.py exited N: ...` | Re-run `python util/prompt_discovery/cli.py --repo-root .` and fix the probe failure (non-git root exits 2). |
| `[FAIL] discovery ... not valid JSON` / missing `schema_version` | CLI must print one JSON object with top-level `schema_version` and `provenance.head_sha`. |
| Doctor green but `/template-agent` grounding fails | Confirm you did **not** use `--no-discovery`; re-run without that flag. |
| `[WARN] mirror ... not fully installed` | Optional; run `util/install_agents.bash` (or ignore unless you need the `~/.claude` mirror). |

---

## Isolated Stack E2E Utilities

`util/isolated_stack.bash` brings up a **throwaway** data / cascor / canopy trio on non-default ports so the training-runtime E2E checklist can run without touching the operator host stack (`8100` / `8201` / `8050`) or the deploy Docker stack. The primary recipe is [`notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md`](../notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md); this section is the operator contract for the helper.

Recording click-by-click verdicts into the 298-row matrix is a **separate write path**: [Canopy E2E Matrix Writes](#canopy-e2e-matrix-writes).

| Utility | Purpose | Key Overrides |
|---------|---------|---------------|
| `util/isolated_stack.bash --up` | Create the data venv, then launch data → cascor → canopy (health-gated); a mid-leg failure tears the partial trio back down | `JUNIPER_E2E_DATA_PORT`, `JUNIPER_E2E_CASCOR_PORT`, `JUNIPER_E2E_CANOPY_PORT`, `JUNIPER_E2E_HEALTH_TIMEOUT`, `JUNIPER_E2E_DATA_EXTRAS`, `JUNIPER_E2E_RUN_DIR`, `JUNIPER_E2E_*_CONDA` / `*_DIR` |
| `util/isolated_stack.bash --down` | Kill-by-port teardown + clean run / snapshot artifacts | same port / `RUN_DIR` / project overrides |
| `util/isolated_stack.bash --status` | Probe each `/v1/health` and report listening PID | same |
| `util/isolated_stack.bash --dry-run …` | Print every command; execute nothing (safe when ports are busy) | same |

Defaults: data `8101` (dedicated `python3.14` venv), cascor `8202` (`JuniperCascor1`), canopy `8051` (`JuniperCanopy1` service mode). Scratch under `${TMPDIR:-/tmp}/juniper-e2e`. Exactly one of `--up` / `--down` / `--status` is required (misuse exits `2`).

```bash
util/isolated_stack.bash --dry-run --up   # preview only
util/isolated_stack.bash --up
util/isolated_stack.bash --status
util/isolated_stack.bash --down
```

#### Dedicated data venv bring-up (`data_up`)

`--up` runs `do_up` in dependency order **`data_up` → `cascor_up` → `canopy_up`**. Only the data leg uses a dedicated venv; cascor/canopy stay on their conda envs. `data_up` does **not** touch the `JuniperData` conda env.

Live compose (verified against `util/isolated_stack.bash`; coverage in `tests/test_isolated_stack_script.py` `TestDataUpLive`, juniper-ml#807):

1. `require_cmd python3.14` — missing interpreter aborts **before** any venv, pip, or pidfile side effect.
2. Ensure `${RUN_DIR}` and `${LOG_DIR}` exist (`JUNIPER_E2E_RUN_DIR`, default `${TMPDIR:-/tmp}/juniper-e2e`).
3. Create `${RUN_DIR}/.venv-data` with `python3.14 -m venv` **only when that directory is absent** — an existing venv skips create but still re-runs pip install + launch.
4. `pip install -q -e "${DATA_DIR}[${DATA_EXTRAS}]" prometheus_client juniper-observability` — `DATA_EXTRAS` defaults to `api` (`JUNIPER_E2E_DATA_EXTRAS`; use `api,mnist` for checklist D2/I-5).
5. Launch from `${RUN_DIR}` with `PYTHON_GIL=0 nohup python -m juniper_data --host 127.0.0.1 --port ${DATA_PORT}`, stdout/stderr → `${LOG_DIR}/juniper-data.log`.
6. Write `$!` to `${RUN_DIR}/juniper-data.pid`, then `wait_for_health` on `http://127.0.0.1:${DATA_PORT}/v1/health`.

`--dry-run --up` announces the venv/pip/launch lines and returns from `data_up` without creating the venv or writing a pidfile.

Constraints/pitfalls:

- `PYTHON_GIL=0` is required for the free-threading `python3.14` path the checklist assumes; dropping it leaves a wrong or dead data service on `8101` while later legs still start.
- Pidfiles under `RUN_DIR` are bring-up bookkeeping — `--down` still stops by **port** (`stop_port`), not by reading `juniper-data.pid`.
- Manual checklist §3.1 must match this compose (especially `PYTHON_GIL=0` and the explicit `prometheus_client` + `juniper-observability` install). Prefer `util/isolated_stack.bash --up` over hand-rolling when the helper is available.

#### Live `cascor_up` / `canopy_up` compose

`--up` launches data → cascor → canopy. The conda-backed legs are the classic failure class on checklist runs (libtorch collision, control-WS `403` reconnect churn, accidental demo mode). Live compose (not `--dry-run`) does:

**`cascor_up`** (after `activate_conda` of `JUNIPER_E2E_CASCOR_CONDA`, default `JuniperCascor1`):

1. `cd` to `${PROJECT_DIR}/juniper-cascor/src`
2. `nohup uvicorn api.app:create_app --factory --host 127.0.0.1 --port ${CASCOR_PORT}` with:
   - `LD_LIBRARY_PATH=''` — **empty string, not unset** (neutralizes rust_mudgeon / libtorch bleed-through that otherwise shadows the env's torch)
   - `JUNIPER_DATA_URL=http://127.0.0.1:${DATA_PORT}` — isolated data, never host `:8100`
   - `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=${CANOPY_ORIGIN}` where `CANOPY_ORIGIN=http://127.0.0.1:${CANOPY_PORT}`
3. Writes `${RUN_DIR}/juniper-cascor.pid`, then gates on `http://127.0.0.1:${CASCOR_PORT}/v1/health`

**`canopy_up`** (after `activate_conda` of `JUNIPER_E2E_CANOPY_CONDA`, default `JuniperCanopy1`):

1. `cd` to `${PROJECT_DIR}/juniper-canopy/src`
2. `nohup python main.py` with:
   - `JUNIPER_CANOPY_DEMO_MODE=0` — **service mode** (demo mode skips real cascor/data wiring)
   - `JUNIPER_CANOPY_PORT=${CANOPY_PORT}`
   - `JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://127.0.0.1:${CASCOR_PORT}`
   - `JUNIPER_CANOPY_JUNIPER_DATA_URL=http://127.0.0.1:${DATA_PORT}`
   - `JUNIPER_CANOPY_CASCOR_WS_ORIGIN=${CANOPY_ORIGIN}` — must match cascor's allowlist (checklist §4)
3. Writes `${RUN_DIR}/juniper-canopy.pid`, then gates on `http://127.0.0.1:${CANOPY_PORT}/v1/health`

**Constraints:**

- Missing `${JUNIPER_E2E_CONDA_DIR}/etc/profile.d/conda.sh` aborts inside `activate_conda` **before** any launch or pid write (both paths).
- `--dry-run --up` prints the announce lines only — no conda activate, nohup, pid, or health side effects.
- Dropping `LD_LIBRARY_PATH=''`, the Origin/allowlist pair, or `DEMO_MODE=0` is the libtorch-collision / `403`-reconnect / demo-mode failure class the checklist already documents in §3.2 / §3.3 / §4.

Coverage: `tests/test_isolated_stack_script.py` (`TestCascorUp` / `TestCanopyUp` in juniper-ml#813).

#### Partial-failure teardown (`do_up` → `do_down`)

`do_up` launches **data → cascor → canopy**. Under `set -e`, a bare mid-leg failure would exit the script immediately and leave earlier listeners orphaned on `8101` / `8202` / `8051`, poisoning the next checklist run. `do_up` instead mirrors `experiment_stack.bash`: absorb each leg as `*_up || failed=1`, skip the later legs, then tear down.

On failure (live mode, not `--dry-run`):

1. Logs `ERROR: bring-up failed — tearing the partial trio back down (logs kept under ${LOG_DIR})`.
2. Calls `do_down` (same kill-by-port + RUN_DIR / snapshot cleanup as `--down`).
3. Returns `1` — it does **not** leave partial listeners for the operator to discover later.

**OR-list `|| return 1` constraint:** `data_up || failed=1` (and the cascor/canopy siblings) disables `set -e` inside each `*_up` body (bash OR-list rule). Critical steps — `require_cmd`, venv create, `activate_conda`, `wait_for_health` — must therefore end with `|| return 1`, or a mid-function failure falls through to a false-green health gate and skips `do_down`.

`--dry-run --up` never launches and never calls `do_down`. After a live partial failure, inspect `${LOG_DIR}` (kept under `JUNIPER_E2E_RUN_DIR`), confirm the ports are free with `ss -tlnH 'sport = :8101 or sport = :8202 or sport = :8051'`, then re-`--up`.

#### Nounset and fail-closed `activate_conda` (juniper-ml#785)

The script runs under `set -euo pipefail`. Cascor/canopy bring-up calls `activate_conda`, which temporarily `set +u` around `conda activate` because conda activation scripts may reference unset vars (e.g. `ADDR2LINE`) — the same class as plant's `safe_conda_activate`.

**Contract:** restore nounset with `set -u` immediately after `conda activate` so later unset expansions still fail. Pre-[#785](https://github.com/pcalnon/juniper-ml/pull/785) the restore arm was a second `set +u`, so live `--up` continued **without** nounset after every cascor/canopy activate. If a mid-`--up` failure looks like a silent missing-env typo that plant would have caught, confirm #785 is present (`rg -n 'set -u' util/isolated_stack.bash` inside `activate_conda`).

**Fail-closed under the OR-list absorb.** Because `cascor_up` / `canopy_up` are invoked as `*_up || failed=1` (and call `activate_conda … || return 1`), a bare `conda activate` whose failure is followed by a successful `set -u` would return `0` — the leg would continue and launch `uvicorn` / `python` from the **ambient PATH** instead of the env (wrong torch / site-packages, possibly a false-green `/v1/health`). `activate_conda` therefore propagates explicitly:

- `source "${CONDA_SH}" || { log ERROR; return 1; }`
- `if ! conda activate "${env_name}"; then set -u; log ERROR; return 1; fi` — nounset is restored on the **failure** arm too
- the success arm still ends with `set -u` (#785)

Confirm with `rg -n 'if ! conda activate' util/isolated_stack.bash`. A missing `${JUNIPER_E2E_CONDA_DIR}/etc/profile.d/conda.sh` still aborts before any launch or pid write.

#### Kill-by-port teardown (`port_pid` / `stop_port`)

`--down` does **not** use `JuniperProject.pid`. It stops the canopy → cascor → data via `stop_port`, which runs `ss -tlnpH "sport = :<port>"` to find the first `pid=N` (`port_pid`), then `kill`s that PID.

Soft-fail when `ss` is missing, exits nonzero, or reports no `pid=` (logs "nothing listening"; not a failure). `--dry-run --down` announces the kill line but never kills. After stop, live mode removes `${RUN_DIR}/data`, the data venv, `*.pid`, and `snapshot_*.h5` under canopy `src/snapshots/` (non-matching names are left alone). It deliberately does **not** touch cascor's shared snapshot root `juniper-cascor/cascor-snapshots/` — that is a project asset store outliving every stack, and repointing the teardown glob at it is the mistake the in-script comment guards against. Per-run snapshot sweeping is done by giving the run its own `JUNIPER_CASCOR_SNAPSHOTS_DIR`, as `experiment_stack.bash` does.

Orphaned listeners on `8101`/`8202`/`8051` after a broken teardown collide with the next `--up` — prefer `--down`, then `ss -tlnH 'sport = :8101 or sport = :8202 or sport = :8051'` (should print nothing).

Coverage: `tests/test_isolated_stack_script.py` (`TestPortPid` / `TestStopPort` / `TestLiveDown` in juniper-ml#786/#788).

#### Health wait/status probe

- `wait_for_health` (live `--up` only): polls `curl -sf` every **2s** (hard-coded; not plant's `HEALTH_CHECK_INTERVAL`) until success or `JUNIPER_E2E_HEALTH_TIMEOUT` (default `60`). Timeout logs `ERROR: … see ${LOG_DIR}` and returns `1` (aborts `--up` under `set -e`).
- `probe_health` (`--status`): reports HTTP code (or `000` on curl failure) plus `port_pid`; never fails the script on an unhealthy service.
- Health URLs are always `http://127.0.0.1:<port>/v1/health` for all three services.

Coverage: `tests/test_isolated_stack_script.py` (`TestWaitForHealth` / `TestProbeHealth` in juniper-ml#793).

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| `ERROR: required command 'python3.14' not found` | Install/expose `python3.14` on `PATH` before `--up`; no venv or pidfile should exist yet under `JUNIPER_E2E_RUN_DIR`. |
| Data health timeout / free-threading oddities | Confirm launch used `PYTHON_GIL=0`; inspect `${RUN_DIR}/logs/juniper-data.log` and that `.venv-data` was created with `python3.14`. |
| Stale editable install in data venv | Delete `${RUN_DIR}/.venv-data` (or run `--down`) and re-`--up`, or set a fresh `JUNIPER_E2E_RUN_DIR`. Existing venv skips `python3.14 -m venv` but still re-pip-installs. |
| `--up` dies with unset-variable / odd conda activate noise | Need #785 nounset restore; also confirm `JUNIPER_E2E_CONDA_DIR` points at a real `conda.sh`. |
| `bring-up failed — tearing the partial trio back down` | Expected on a mid-`--up` leg failure — `do_down` already ran. Read `${LOG_DIR}`, confirm the ports are free, then retry. |
| `ERROR: conda activate '…' failed` | Expected fail-closed path — fix `JUNIPER_E2E_CASCOR_CONDA` / `JUNIPER_E2E_CANOPY_CONDA` / `JUNIPER_E2E_CONDA_DIR`, then re-`--up`. |
| Cascor/canopy "up" but wrong torch / odd site-packages after a conda env rename | Confirm `activate_conda` still fail-closes (`rg -n 'if ! conda activate' util/isolated_stack.bash`); a masked activate failure launches on the ambient PATH. |
| Ports still busy after `--down` | Confirm `ss` is on `PATH` and can see user processes; re-run `--down` or kill the `pid=` from `ss -tlnpH` manually. |
| Health timeout mid-`--up` | Inspect `${JUNIPER_E2E_RUN_DIR:-/tmp/juniper-e2e}/logs/*.log`; raise `JUNIPER_E2E_HEALTH_TIMEOUT` only after fixing the service, not as a silent hang workaround. |
| Cascor dies / wrong torch after `--up` | Confirm live launch emptied `LD_LIBRARY_PATH` (`--dry-run --up` shows `LD_LIBRARY_PATH=`); prefer default `JuniperCascor1`. |
| Canopy looks "up," but training APIs are demo stubs | `JUNIPER_CANOPY_DEMO_MODE` must be `0` on the live launch line. |
| Isolated canopy is live but Candidate Metrics / Decision Boundary / Topology stay at mount defaults | 12-slot starvation, not missing wiring. Do **not** add a new Interval. Run [F-CANOPY-027 Poller Starvation Probes](#f-canopy-027-poller-starvation-probes). |
| Control-WS `403` / reconnect churn | Cascor allowlist + canopy Origin must both be canopy's origin (`http://127.0.0.1:<CANOPY_PORT>`). See checklist §4. |
| Topology / metrics store looks empty while the wire is correct | Do not trust a browser `_store()` read or the first TOPOPROBE lines. Run the apply / soak / report / revert loop in [F-039 Store Probe](#f-039-store-probe). |
| One green topology paint "proves" F-CANOPY-037 | 2 of 11 was the finding — a single session is ~18% likely while still broken. Run [F-CANOPY-037 Render Census](#f-canopy-037-render-census). |

Do **not** point isolated ports at the host stack or run `--up` on ports `plant_all` already owns.

Store-apply contradictions (correct `/api/topology` body, empty DOM) are a different class from bring-up failures — see [F-039 Store Probe](#f-039-store-probe).

---

## F-039 Store Probe

The instrument that root-caused **F-CANOPY-039** (FIXED in juniper-canopy#549; heading on [`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md)). Operators still need it when a topology or metrics tab looks empty after a correct wire response, or when someone quotes a store as "never advancing."

The finding shape is a **contradiction between two simultaneous values for one store id**. Browser-side `_store()` reads are unreliable — they returned `None` while that store's writer fired 12 times in 60 s. What settled it was logging the comparison's operands **server-side**, inside the handler, where the value Dash delivered as `State` is visible.

Finding triage (`e2e_finding_triage.py`) only classifies ledger headings. The census (`e2e_f037_render_census.py`) only scores `topodiag` JSON. Neither of those tools is this probe.

### Workflow

```bash
# Playwright lives only in JuniperCanopy1. Empty LIBTORCH / LD_LIBRARY_PATH or an
# ambient rust_mudgeon libtorch breaks import with `_PyObject_NextNotImplemented`.
LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
  util/ad-hoc/e2e_f039_topoprobe_instrument.py apply --checkout /path/to/juniper-canopy --target metrics

# Restart THAT canopy leg (instrumentation is a source edit). Then hold a live tab:
LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
  util/ad-hoc/e2e_f039_metrics_store_soak.py --seconds 120

python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py report --log /tmp/juniper-e2e/logs/juniper-canopy.log --target metrics

# ALWAYS revert before committing anything from that checkout
python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py revert --checkout /path/to/juniper-canopy
```

`--target metrics` probes `metrics-panel-metrics-store` via `_update_metrics_store_handler` / `current_metrics`. `--target topology` is the **default in argparse and REFUSES on current canopy**: `_update_topology_store_handler` takes only `(n, active_tab)` and no longer receives the client's store copy. Emitting a probe that reads a name not in scope is the stale-identifier class this arc already hit; `apply` exits **2** with the `State("network-visualizer-topology-store", "data")` instructions instead.

`apply` is idempotent one-target-at-a-time (`TOPOPROBE` already in the file → exit **1**, revert first). A renamed handler or a missing anchor exits **2**.

### Read the whole series

`report` prints distinct `cur_len` values so a head-only reading cannot recur. Topology's measured healthy shape is `eq=False` ×4 then `eq=True` ×11: the client's copy is empty for ~22 s, then **converges** and holds the correct payload. The original reading of that same log said "permanently empty" because it generalised from the first four lines.

| `report` observation | Verdict (from `do_report`) |
|----------------------|----------------------------|
| Some comparisons `eq=True` | Client copy **does** advance. Refutes "never advances." This is topology's shape. |
| Every comparison unequal, and `cur_len` **varies** | Neither never-advances nor a deterministic asymmetry. Investigate before concluding. |
| `cur_len=0` or `cur_type=NoneType` | The `State` is **not delivered**. Different defect from written-but-empty. Not a unification confirmation. |
| Constant small `cur_len` (≤ 8) | Matches the store's empty default — client's copy never advances. For `--target metrics` this supports F-035 / F-038 / F-039 being one defect. |
| Constant **large** `cur_len` and never-equal | Client copy is populated and stable yet never compares equal: deterministic round-trip asymmetry. **Refutes** the unification. |

`cur_len` alone does not discriminate: the metrics store's empty default serialises to `cur_len=2`, and an unresolved `State` is `cur_len=0` via the probe's `"" if current is None` branch. Discriminate by **writer** before concluding — `metrics-panel-metrics-store` has a second, unguarded writer (`append_ws_metrics_store`, `allow_duplicate=True`) whose every write is `no_update`-free by construction.

### Backup must not land in the work tree

The first version wrote `<file>.f039bak` beside `dashboard_manager.py`. That file was untracked and unignored, so `git add -A` would sweep a full copy of the instrumented module into a commit. The backup now goes in the git dir (`git rev-parse --absolute-git-dir` → `f039-topoprobe.f039bak`) because in a worktree `.git` is a file. `revert` still honours a beside-the-file leftover.

### Companion probes that are not this instrument

| Script | What it measures | What it is not |
|--------|------------------|----------------|
| `e2e_f039_metrics_store_soak.py` | Holds a Playwright session so `fast-update-interval` can tick. Exit **0** if the session stayed open for `--seconds` (default 120). | Not a store verdict. `curl` cannot produce a single sample — a Dash interval only fires inside a live browser. |
| `e2e_f039_duplicate_store_probe.py` | Live layout-tree walk. `occurrences > 1` **and** `distinct_data > 1` is the finding; `occurrences == 1` **refutes** it. | Not a DOM check (`dcc.Store` has none). Not `e2e_f027_dup_ids.py` (declared layout). Not `paths.strs` (duplicate id → one winner; F-027 trap). Exit **1** = could not run, **not** a verdict. |

Shared browser helpers come from `e2e_w3_params_driver.py`. Default canopy URL is `JUNIPER_E2E_CANOPY_URL` (`http://127.0.0.1:8051`).

### Exit codes (`e2e_f039_topoprobe_instrument.py`)

| Code | Meaning |
|------|---------|
| 0 | `apply` wrote the probe / `revert` restored / `report` found lines and printed a verdict |
| 1 | Already instrumented / not instrumented / no `TOPOPROBE` lines in the log |
| 2 | Missing `--checkout`, missing file, renamed handler, refused topology target, missing log |

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| `_PyObject_NextNotImplemented` on import | Ambient libtorch. Prefix `LIBTORCH= LD_LIBRARY_PATH=` and use `JuniperCanopy1`'s python. |
| `REFUSING: … has no current_metrics / current parameter` | Expected for `--target topology` on current canopy. Add the `State` or probe `metrics`. |
| `already instrumented` | One target at a time. `revert` first. |
| `no TOPOPROBE lines` | Leg is not running the instrumented checkout, or the tab was never driven. Restart after `apply`. Isolated `--up` writes `${JUNIPER_E2E_RUN_DIR:-/tmp/juniper-e2e}/logs/juniper-canopy.log` — the argparse default is the A/B path `/tmp/juniper-e2e/juniper-canopy-ab.log`. |
| First four lines are `eq=False` | Read the whole series. Topology converges after ~22 s. |
| `git add -A` wants `dashboard_manager.py` + a `.f039bak` | Backup leaked into the work tree. `revert`, delete the leftover bak, never commit the probe. |
| DOM / `paths.strs` / static layout says the store is unique | Expected. Use `e2e_f039_duplicate_store_probe.py` on the live tree. |
| `curl` / log scrape shows no metrics-store samples | Need a live browser session (`e2e_f039_metrics_store_soak.py`). |
| Duplicate-store probe exits 1 | Probe could not run. Not a refutation and not a confirmation. |

These scripts are **not CI**. They edit a sibling checkout. Revert is part of the contract, not optional cleanup.

---

## Canopy E2E Matrix Writes

The ledger is [`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md) (298 rows). Hand-editing a status cell is how a neighbouring row silently acquires a verdict nobody measured. Four ad-hoc tools write or read that ledger; they are **not** interchangeable.

Companion plan: [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md). Evidence: [`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md). Bring-up stays in [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities).

### Which tool

| Job | Tool | Default | Writes if some rows fail? |
|-----|------|---------|---------------------------|
| After a run, fill empty `status` cells from `statuses.tsv` / `rowlog.md` | `util/ad-hoc/e2e_matrix_fill.py` | **dry-run** (`--write` to apply) | No write unless `--write`. Exit `1` if nothing to fill. |
| Set named rows that **all currently hold the same** status | `util/ad-hoc/2026-09-02_matrix_set_verdicts.py` | **writes immediately** (no dry-run) | **No.** Any missing / `--from` mismatch → exit `1`, file bytes unchanged. |
| Re-score **exactly** the rows a fix re-opened, regardless of current status | `util/ad-hoc/e2e_matrix_rescore.py` | **dry-run** (`--write` to apply) | **Yes, the found rows.** Missing ids are a stderr WARNING; exit `0`. |
| List placeholder `status` cells from the ledger | `util/ad-hoc/e2e_unfilled_rows.py` | read-only | n/a |

Do **not** plan the next segment from `util/ad-hoc/e2e_row_coverage.py`. That script is an estimator over verdict records: it mis-reads compressed enumerations and over-credits rows whose only record is `pending …`. Segment 15's first handoff draft would have re-driven two already-`PASS` rows and dropped three unfilled ones. `e2e_unfilled_rows.py` reads the matrix with the filler's own pipe splitter and placeholder set.

Do **not** use `e2e_matrix_fill.py --overwrite` to re-score a named subset. `--overwrite` rewrites **every** cell any verdict source covers, including hand-authored `INCONCLUSIVE` / `DIVERGENCE …` cells that no TSV reproduces. That is why `e2e_matrix_rescore.py` exists.

### How to run

```bash
# Ledger: what is still a placeholder? (plan from this, not from e2e_row_coverage.py)
python3 util/ad-hoc/e2e_unfilled_rows.py

# After a drive: newest run FIRST (first source that carries a row wins)
python3 util/ad-hoc/e2e_matrix_fill.py \
  --verdicts reports/e2e/<NEWEST>/statuses.tsv \
  --verdicts reports/e2e/<OLDER>/rowlog.md
python3 util/ad-hoc/e2e_matrix_fill.py --verdicts reports/e2e/<NEWEST>/statuses.tsv --write

# Named rows that all currently say BLOCKED (no dry-run — review the --from value)
python3 util/ad-hoc/2026-09-02_matrix_set_verdicts.py \
  --matrix notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md \
  --from BLOCKED --set M-TOPOLOGY-09=PASS --set M-TOPOLOGY-12=FAIL

# After a fix: touch only the re-opened rows (dry-run first)
python3 util/ad-hoc/e2e_matrix_rescore.py --row M-DATASET-01 --row M-DATASET-02 --status PASS
python3 util/ad-hoc/e2e_matrix_rescore.py --row M-DATASET-01 --status PASS --write
```

### Contracts verified against source

**Fill** (`e2e_matrix_fill.py`):

- Locates the `status` column **by header name per table**. Column sets differ (C2.4 WS-badge vs M-*); a fixed index silently writes into the wrong column.
- Splits on unescaped pipes only (`\|` stays inside its cell). A naive split turned C2.2-04 (`display:block\|none`) into an extra phantom cell and wrote the verdict into the previous column.
- Refuses a write that would change the row's cell count (exit `2`).
- Namespaces with a status cell: `C2.*` and `M-*` only. W-lane ids (`W3-*`, `W5-*`, …) are numbered prose steps — reported as no-matrix-row, not an error.
- `--verdicts` is repeatable. Sources are consulted in order; **first source wins**. Pass the newest run first.
- Range / slash tokens (`M-TOPOLOGY-01..06,09..18`, `M-PARAMETERS-01/02/03`) expand; lane suffixes `-L` / `-D` become `PASS (LIVE arm)` / `PASS (DEMO arm)` so a single-arm drive cannot fold onto the other arm.
- Non-terminal prefixes (`pending`, `todo`, `in progress`, `deferred`, `not run`) never reach a status cell.
- Default `--max-len 44`; `shorten` drops a trailing rider rather than amputating a finding id mid-parenthesis.
- Without `--overwrite`, an already-filled cell is left alone (placeholders: empty, `—`, `-`, `--`, `TBD`, `n/a`).
- Exit: `0` ok, `1` nothing to fill, `2` misuse / unreadable input / cell-count refuse.

**Set-verdicts** (`2026-09-02_matrix_set_verdicts.py`):

- **No dry-run.** A successful `--from` match writes the file.
- `--from` is required and applies to **every** named row. Mixed current statuses need two invocations (or use rescore).
- Status is `cells[-2]` after a **naive** `line.split("|")` — last data cell. Do **not** use this tool on a row whose cells contain `\|`; use fill/rescore, which share `split_row`.
- Row identity is `cells[1]` exact match (`M-TOPOLOGY-09` will not retarget `M-TOPOLOGY-090`). An id that appears only in a later cell is ignored.
- Atomic: one bad `--set` among two updates **neither** row.
- Exit: `0` all updated, `1` any missing / `--from` mismatch, `2` bad `ROW=VERDICT` syntax.

**Rescore** (`e2e_matrix_rescore.py`):

- Reuses fill's `split_row` / `status` header lookup. Cell-count change → exit `3`, no write of that line.
- Refuses a status that starts with `pending` (exit `2`).
- Missing `--row` ids: stderr WARNING, **still writes the found rows**, exit `0`. Confirm the printed list before `--write`.

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Neighbouring row now says PASS | Hand-edit, or `set_verdicts` on a row with an escaped pipe (naive split). Use the tools; dry-run fill/rescore first |
| `set_verdicts` wrote immediately | It has no dry-run. Review `--from` / `--set` before invoking |
| `rescore --write` landed 1 of 3 rows | Missing ids warn and still write. Check the WARNING list |
| `--overwrite` clobbered `DIVERGENCE D-1 …` | Expected. Use `e2e_matrix_rescore.py --row` for a named subset |
| W-lane verdict "didn't fill" | Those rows have no status cell. Expected `no-matrix-row` |
| Older `rowlog.md` overwrote a newer TSV | First source wins. Pass newest `--verdicts` first |
| Planned from `e2e_row_coverage.py` | Estimator. Use `e2e_unfilled_rows.py` against the ledger |
| Fill wrote into the FA / AUTO column | Old index-guessing class. Current fill uses the `status` header; do not reintroduce a fixed index |
| `pending demo lane` in a status cell | Non-terminal. Fill drops it; rescore refuses `pending*` |

Ad-hoc inventory: [`util/ad-hoc/README.md`](../util/ad-hoc/README.md) § Canopy E2E matrix writes.
Starvation / tab-gated poller forensics for a live isolated canopy: [F-CANOPY-027 Poller Starvation Probes](#f-canopy-027-poller-starvation-probes).

---

## F-CANOPY-027 Poller Starvation Probes

F-CANOPY-027 was "a panel's data store is written repeatedly and nothing downstream of it ever runs" (Candidate Metrics / Decision Boundary / Topology frozen at mount defaults). It is **FIXED** in juniper-canopy (#507 / #509 / #511 — tab-gated intervals + Stage 2 suppressed chained store rewrites). Ledger: [`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md) entry F-CANOPY-027.

The root cause is **callback starvation under dash-renderer's hard-coded 12-slot pool**, not missing wiring. Twenty wiring mechanisms were refuted in situ; retain that record. Recurrence looks identical (store fills on the wire, consumers never paint), so the probes stay in `util/ad-hoc/` as provenance.

### The pool, not the graph

dash-renderer 4.2.0 (`dash_renderer.dev.js` ~2846) promotes `callbacks.prioritized` with:

```text
available = Math.max(0, 12 - executing.length - watched.length)
```

If `executing + watched >= 12`, **nothing** leaves `prioritized` on that pass. Ordering is `sortPriority` / `getPriority` (base-36 downstream depth×breadth, **DESCENDING**). A terminal render callback — outputs feed no further callback — scores the minimum and loses every arbitration while the pool is contended. The callback is registered, resolvable, and queued; it is simply never picked.

`getReadyCallbacks` only promotes `requested` → `prioritized` when none of the callback's INPUTS is an OUTPUT of a still-pending callback. One never-leaving pending writer pins every consumer of its outputs in `requested` forever (`blocked` / `executing` / `executed` all 0). That is "never READY", not "never wired".

### Which probe

Run against a **live isolated** canopy (`JuniperCanopy1`, `DEMO_MODE=0`). Empty `LD_LIBRARY_PATH` as for cascor/canopy launch. `e2e_f027_queues.py` / `e2e_f027_ready.py` / `e2e_f027_slots.py` have **no** `--base-url` — they inherit `JUNIPER_E2E_CANOPY_URL` (default `http://127.0.0.1:8051`) from `e2e_w3_params_driver.open_dashboard`.

```bash
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
  util/ad-hoc/e2e_f027_queues.py --tab 'Candidate Metrics'
# control arm (a winner, not a starvation loser):
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
  util/ad-hoc/e2e_f027_queues.py --tab 'Training Metrics' \
  --store metrics-panel-training-state-store

LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
  util/ad-hoc/e2e_f027_ready.py --tab 'Candidate Metrics'

LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
  util/ad-hoc/e2e_f027_slots.py --tab 'Candidate Metrics' --seconds 60
```

| Probe | Question it answers |
|-------|---------------------|
| `e2e_f027_queues.py` | When the dead store's prop changes: consumer **queued-and-stuck**, or never queued? Hooks `store.dispatch` before injecting via `setProps`. |
| `e2e_f027_ready.py` | Which pending callback is pinning each `requested` consumer, and which queue is that blocker in? |
| `e2e_f027_slots.py` | How often is `available == 0`? Who occupies `watched`/`executing`, who sits in `prioritized` unpicked? |
| `e2e_f027_deps_endpoint.py` | Does `/dashboard/_dash-dependencies` (client graph) list the consumer with the store as an Input? (`callback_map` is the **server** registry.) Run from `juniper-canopy/src`. |
| `e2e_f027_cleanroom.py` | Smallest app with canopy's `visualization-tabs` shape. Default **includes** the once-only children rewrite (`suppress_cascade_tabs`); `--no-rebuild` omits it. Self-hosted on port `8399` (`--port`). |

### Operator pitfalls

| Symptom | Cause |
|---------|-------|
| "Must be unwired — consumers never fire" | Check queues first. F-027 consumers **were** in `requested`. |
| New Interval to "fix" a frozen panel | **Forbidden.** The F-027 rule: feed an existing store (canopy#524 used `metrics-panel-metrics-store`). A new poller re-saturates the 12-slot pool. |
| Topology graph dead after a "correct" server render | Same family: 12-Input rebuild on the 1 s `fast-update-interval`. #509 gated it to `tabpoll-topology`. |
| Probe against host `plant_all` canopy | Ports / DEMO_MODE collide. Isolated stack only ([Isolated Stack E2E](#isolated-stack-e2e-utilities)). |
| `F-CANOPY-034` "store written by nothing" | Orthogonal: a poller with **no consumer**. Do not treat as 027. |
| `F-CANOPY-035` empty candidate-loss figure | Not starvation — `/api/state` never carried `epochs`/`losses`/`phases`. Fixed canopy#524 by reading the shared metrics store. |

These scripts are **not** CI. They need a live Dash page and Playwright/`e2e_w3_params_driver.py` helpers.

---

## Canopy E2E Finding Triage

Phase 2's exit criterion ([the frontend validation plan](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md) §6.3) is "every P0 and P1 closed or explicitly deferred with owner sign-off". [`util/ad-hoc/e2e_finding_triage.py`](../util/ad-hoc/e2e_finding_triage.py) is the mechanical count of that ledger. Do not hand-maintain a parallel open list — it drifts.

```bash
python3 util/ad-hoc/e2e_finding_triage.py
python3 util/ad-hoc/e2e_finding_triage.py --open-only
```

Default ledger: [`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md). Override with `--note PATH`.

### What it reads

Only **line-starting** bold headers of the form `**F-<AREA>-<NNN> — …**` (optional trailing letter, e.g. `F-CANOPY-041b`). The body is non-greedy to the first closing `**`. Finding prose below the header, later mentions of the same id, and indented headings are invisible.

The first heading for an id wins. A later restatement of the same id is skipped.

### Dispositions

Tokens are taken from the **last 170 characters** of the header body (the text between the em-dash and the closing `**`), case-insensitive whole words:

| Token in that tail | Printed | Counts as |
|--------------------|---------|-----------|
| `FIXED` or `HEALED` | `FIXED` | closed, shipped |
| `ACCEPTED` and not also FIXED | `ACCEPT` | owner-deferred — **not** open, **not** fixed |
| neither | `OPEN` | still on the Phase 2 exit criterion |

**ACCEPTED is a third disposition.** The defect is real and unrepaired, but the owner signed off (plan §6.3 "explicitly deferred"). Counting it as FIXED overstates what shipped; counting it as OPEN keeps an already-settled exit criterion red.

`--open-only` hides FIXED and ACCEPTED rows from the table. The totals block underneath still counts every finding.

### Priority

First match of `P0/P1`, `P0`, `P1`, `P2`, `CRITICAL`, or `LEDGER` in the **full** header body (not only the tail). The alternation lists `P0/P1` before `P0`, so a `P0/P1` header is not classified as `P0`. Untagged → `?`.

### Constraints

- Always exits **0**. A green shell is not "no open P0/P1".
- A `FIXED` token more than 170 characters before the end of the header body does **not** close an OPEN tail. Put the disposition in the header, near the end.
- Putting `FIXED` / `HEALED` / `ACCEPTED` only in the finding's body paragraphs does nothing.
- The printed summary is `header.split(":")[0]` truncated to 78 characters — a colon in the title cuts the line short; the id and disposition are unaffected.
- A missing `--note` path is an uncaught `FileNotFoundError` (exit 1), not a triage table.

Re-run; the counts drift. On 2026-09-04 against `origin/main` this printed **54** findings, **34** fixed, **1** accepted (`F-CANOPY-004`), **19** open (1 `P0/P1` + 3 `P1` + 15 `P2`).
Scoring the Topology tab against this trio is a **separate driver**: [Canopy E2E Topology Driver](#canopy-e2e-topology-driver).

---

## Canopy E2E Topology Driver

`util/ad-hoc/e2e_seg17_topology_driver.py` is the Playwright scorer for the Network Topology control surface. Bring-up is [Isolated Stack E2E](#isolated-stack-e2e-utilities) (`:8051` by default). This section is the **scorer** contract.

Row text: [`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md). Findings: [`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md).

The registered step names are the `STEPS` dict at the bottom of the file. `--step` rejects anything else (exit `2`). The module docstring's "NOT IMPLEMENTED" list is **stale** for M-TOPOLOGY-13 and -14 — those have scorers (`topostate`, `topoexport`). Trust `STEPS`, not the prose list.

```bash
# Playwright lives in JuniperCanopy1. Empty LD_LIBRARY_PATH (same class as isolated cascor).
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
    util/ad-hoc/e2e_seg17_topology_driver.py --step probe
```

`--step` is required, comma-separated, order preserved. A successful run always exits `0` (unknown names are the only `2`). Results merge into `JUNIPER_E2E_SEG17_RESULTS` (default `${JUNIPER_E2E_RUN_DIR:-/tmp/juniper-e2e}/seg17_results.json`) if that file already exists.

### Which step scores which row (verified against `origin/main`)

| `--step` | Scores exactly | Not this step |
|----------|----------------|---------------|
| `probe` | DOM dump of the four topology controls (dcc widgets are **not** native `<select>`) | no verdicts |
| `topo` | M-TOPOLOGY-01..08 and -17 | not -09 (theme-on-topology is `topoevents`); not -16 |
| `topoevents` | M-TOPOLOGY-09, -10, -12, -15 | not M-DATASET-14 (`theme`); real mouse click, never `gd.emit('plotly_click')` |
| `topostate` | M-TOPOLOGY-13 (zoom persist) and -18 (raw-store gate) | -18 is scored on the **store**, not browser `/api/topology/raw` traffic (that fetch is server-side) |
| `topoexport` | M-TOPOLOGY-14 (modebar PNG) | a missing download with `data:` raster OK + `blob:` blocked is canopy CSP (`img-src` omits `blob:`), not a headless quirk |
| `theme` | M-DATASET-14 only (Dataset tab figures) | does **not** score M-TOPOLOGY-09 |
| `topodiag` / `rebuildprobe` / `wirecensus` / `quietread` / `storestorm` / `f031` | diagnostic instruments | not matrix row scorers |

No step exists for **M-TOPOLOGY-11** (box/lasso — driver gap, do not file as a product defect) or **M-TOPOLOGY-16** (cascade-add glow; needs an unsaturated fixture). W1-12..14 and W4-* live in the matrix/ledger, not in this driver.

### Three predicates that can PASS the easier half

These are the **shipped** scorers on `main`. An `OR` over two independent claims scores the easier one. [juniper-ml#1672](https://github.com/pcalnon/juniper-ml/pull/1672) tightens them; that change is **not** on `main` — do not treat the tightened predicates as current.

| Row | What `main` actually asserts | What a PASS can hide |
|-----|------------------------------|----------------------|
| **M-TOPOLOGY-06** (`topo`) | `idiom is not None` **and** (`label == "{k} of {N}"` **OR** `counts["hidden"] == want`) | Stats bar filtered, label still `"0 of 40"`. F-CANOPY-042's rest-state label was invisible to this row. |
| **M-TOPOLOGY-07** (`topo`) | Depth-slider **container** `display` is not `none` | Comment says the label should read `"all"`. The scorer **records** `label` and does not assert it. A rest-state `"0 of 40"` still PASSes. |
| **M-TOPOLOGY-12** (`topoevents`) | After a real empty-space click, `-selection-info` hides or its text is empty → PASS; else FAIL. BLOCKED only when nothing was selected (vacuous clear). | plotly emits `plotly_click` only for POINT hits. `plotly_click_events=0` is recorded; the row still FAIL-scores the withdrawn empty-space gesture. |

Observation discipline the driver already encodes (do not regress it): poll for **transitions** (not "label ≠ all", which is true at rest because the slider sits at `0`); verify every widget write by its **effect** (figure hash, not "the DOM moved"); settle the figure before a gesture (rebuild is 1.5–31 s); never cap a capture buffer.
### Predicates that landed with #1672

An earlier scorer used `OR` / display-only / empty-space-as-FAIL. That let a `topo` PASS hide a rest-state `"0 of 40"` label (F-CANOPY-042) and made `topoevents` FAIL-score a gesture plotly never emits (F-CANOPY-046). Those predicates are **gone**. What `main` asserts now:

| Row | What `main` asserts | What a FAIL / BLOCKED means |
|-----|---------------------|-----------------------------|
| **M-TOPOLOGY-06** (`topo`) | `idiom is not None` **and** `label == "{k} of {N}"` **and** `counts["hidden"] == want` | Stats-bar-only filter (label still `"0 of 40"`) is now FAIL. The wait is a real transition (wanted label **or** figure-hash change) — not `label != "all"`, which is already true at rest because the slider sits at `0`. |
| **M-TOPOLOGY-07** (`topo`) | Depth-slider container `display` is not `none` **and** the label reads `"all"` | A rest-state `"0 of 40"` FAIL-scores. Recording the label as decoration is no longer enough. |
| **M-TOPOLOGY-12** (`topoevents`) | After a real node selection, click `network-visualizer-clear-selection`. PASS if `-selection-info` hides. BLOCKED if nothing was selected, or if the control is absent. FAIL if the control is visible but the selection survives. | Empty-space click is **recorded, not scored** (`plotly_click_events`). Do not "fix" a leftover `0` with `gd.emit`. |

`topo` then resets the slider to `0` **with an effect** (figure-hash change). A pre-#1672 reset used synthetic idioms that cannot satisfy `updatemode="mouseup"`, so a working M-06 leaked a filtered graph into M-17. If reset counts ≠ server, the driver logs `!! depth filter did NOT reset` and continues — read that line before filing M-17.

M-10 also asserts `Layer: Hidden` on the selected node (F-CANOPY-045). `shown && names_node && not layer_ok` is the product layer-label defect, not a miss-click.

Observation discipline (do not regress it): poll for **transitions**; verify every widget write by its **effect** (figure hash, not "the DOM moved"); settle the figure before a gesture (rebuild is 1.5–31 s); never cap a capture buffer.

### Second-instance verify launcher

`util/ad-hoc/2026-09-04_canopy_verify_instance.bash` brings up a **second** canopy from a worktree beside the shared isolated stack, so a fix can be driven without restarting `:8051`.

```bash
util/ad-hoc/2026-09-04_canopy_verify_instance.bash up   /path/to/juniper-canopy/src   # default :8052
util/ad-hoc/2026-09-04_canopy_verify_instance.bash down                               # default :8052
```

Contract (verified against the script on `main`):

- Shares isolated cascor `:8202` and data `:8101`. Does **not** `POST /v1/network`.
- Default listen `:8052`. Override the third `up` / second `down` argument. Point the scorer at it with `JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052`.
- `DEMO_MODE=0`. Origin/allowlist are this instance's own origin. `LIBTORCH=` and `LD_LIBRARY_PATH=` are emptied (conda hooks do not run on a direct interpreter invoke).
- Snapshot dir defaults to the host cascor archive (`JUNIPER_CANOPY_SNAPSHOT_DIR`). Override if that path is wrong on this machine.
- Launch is `nohup` → reparents to `systemd --user`. A pidfile is written under `CANOPY_VERIFY_RUN_DIR` (default `/tmp/juniper-canopy-verify`) because a run-dir `*.pid` is one of `reap_pytest_orphans.bash`'s two protection keys. Leave it in place for the life of the instance.
- `down` kills **by pid**, never by port (killing "whatever listens on 8052" would stop a process this script did not start).
- `up` with no `main.py` in the worktree-src, or a bare invocation, exits `2`. Already-up is exit `0`. Health wait is 60 s; failure exits `1` and leaves the log.
Dataset-tab / W6 COLD-migration scoring is a separate Playwright surface: [Canopy E2E Dataset Drivers](#canopy-e2e-dataset-drivers). Those scripts read `JUNIPER_E2E_CANOPY_URL` (default `http://127.0.0.1:8051`), not `JUNIPER_E2E_CANOPY_PORT`.

---

## Canopy E2E Dataset Drivers

Two Playwright drivers score the canopy **dataset** rows of [`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md). They are **not** red/green tests: every check is printed (`PASS` / `FAIL` / `BLOCKED` / `!!`) and a completed run exits `0`. Ledger: [`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md).

They share helpers from `util/ad-hoc/e2e_w3_params_driver.py` (browser, `http_get`/`http_post`, `JUNIPER_E2E_CANOPY_URL`). They do **not** share W3's `--steps` range parser.

| Driver | Matrix | Flag | What it drives |
|--------|--------|------|----------------|
| `util/ad-hoc/e2e_w6_dataset_driver.py` | W6 COLD migration (sidebar stage → banner → restart modal) | `--steps` (plural) | `#nn-dataset-type-dropdown`, `#apply-dataset-button`, `#pending-dataset-banner`, restart **modal** through cancel |
| `util/ad-hoc/e2e_seg16_dataset_driver.py` | §3.6 Dataset View (`M-DATASET-01`…`27`) | `--step` (singular, required) | Dataset **panel** toolbar / modal / selector / tiles / plots / sequence controls |

Playwright lives only in `JuniperCanopy1`. Invoking that interpreter directly bypasses conda's `LD_LIBRARY_PATH` strip, so an ambient libtorch then fails import with `undefined symbol: _PyObject_NextNotImplemented` (reads like a test failure; it is not):

```bash
# Isolated trio first (canopy :8051). Then:
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
    util/ad-hoc/e2e_w6_dataset_driver.py --steps 1,2,4,7

LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
    util/ad-hoc/e2e_seg16_dataset_driver.py --step start,toolbar,selector
```

### W6 — do not confirm the restart

`STEPS` is the authority: `1`, `2`, `4`, `7`, `10`, `11b`, `10b`, `cleanup`. There is **no** step `16` and no `#restart-confirm-button` click. `step_10` logs `STOPPING BEFORE step 16` on purpose: `POST /api/train/restart` ships `reset=True` (`dashboard_manager.py` restart handler) and **wipes the live network** that carries segment-6/7 evidence. That is an owner call, not a driver's.

| Key | Matrix rows | Notes |
|-----|-------------|-------|
| `1` | W6-01 | Baseline dropdown + `/api/status`. `#network-visualizer-input-count` is the F-CANOPY-006 dead-oracle — do not score it. |
| `2` | W6-02 | Switch generator (default preference: Moon / Moons / Circles / Xor / XOR / Gaussian). `--target-dataset` overrides. |
| `4` | W6-04/05/06 | `#apply-dataset-button` → `POST /api/stage_dataset`, banner, `pending_dataset`. |
| `7` | W6-07/08 | Cancel pending (`DELETE /api/cancel_pending_dataset`) + one 10 s reconcile tick. |
| `10` | W6-10…15 | Open restart modal, Escape, start-fresh toggle, granular collapse, `#restart-ds-type`, **cancel**. Needs a staged pending dataset. |
| `11b` | W6-11/12 | Escape **and** backdrop dismiss. Consequence lines are **static** layout text, not wired to the toggle. |
| `10b` | W6-10 fidelity | Compares `#restart-confirm-summary` to `/api/status` `pending_dataset` (they have disagreed). |
| `cleanup` | — | Logs leftover `pending_dataset` only. |

Default `--steps 1,2,4,7` **cancels** the stage. To open the restart modal, pass `1,2,4,10` (no `7` in between). `--granular-target` defaults to `Spirals` for W6-14.

`--steps` is comma tokens only. Unknown names are **dropped**; if nothing remains, exit `2`. The module docstring example `--steps 1-9` is wrong on this driver — `1-9` is not a key. W3's `parse_steps` expands ranges; W6 does not import it.

### §3.6 Dataset View

`STEPS` is the authority: `start`, `inventory`, `wire`, `inputs`, `ctxmenu`, `badge`, `degraded`, `toolbar`, `upload`, `selector`, `stats`, `plots`, `seq`. Unknown names exit `2` (no silent drop). `--step` is required.

| Step | Rows | Constraint |
|------|------|------------|
| `start` | (precondition) | Clicks `#start-button` so `/api/dataset` reports `loaded`. A GET at run start can exceed the 10 s default (F-CANOPY-004); the driver uses `timeout=90`. |
| `toolbar` | M-DATASET-01/02/09 | Generate modal. Under live-run congestion the open was measured at **~39 s** — a 3 s sample reports the FIXED modal as dead. |
| `upload` | M-DATASET-05/07 | File-picker contract; confirm ships disabled; URL fill. |
| `selector` | M-DATASET-10/11/12 | **Select is inert** (no `/api/dataset*` on select alone). Load on the LIVE arm is expected **400**. Split changes are client re-filter (no `/api/`). Scope `[role=option]` by the trigger's `aria-controls` or you scrape every other open menu. |
| `stats` | M-DATASET-13/14 | Four tiles + theme recolour. |
| `plots` | M-DATASET-15/16 | Scatter + distribution. Matrix class **MANUAL**. |
| `seq` | M-DATASET-17…27 | Sequence controls; 2-D inverse expects them hidden. |

`ensure_no_modal` polls the welcome dialog. A single early `dismiss_welcome` can report "not present" before render; the leftover `aria-modal` then intercepts every click as a 30 s Playwright timeout.

### Visibility and the confirm modal

`offsetParent` is **null** for `position:fixed`. Both drivers use computed style + a non-zero border box. The restart confirm modal's DOM **does not exist** while closed — poll for appearance (`wait_appear`); a one-shot visibility read races.

### Environment

| Variable | Default | Role |
|----------|---------|------|
| `JUNIPER_E2E_CANOPY_URL` | `http://127.0.0.1:8051` | Target (from `e2e_w3_params_driver.py`) |
| `JUNIPER_E2E_CANOPY_LOG` | `/tmp/juniper-e2e/logs/juniper-canopy.log` | Log tail for diagnostics |
| `JUNIPER_E2E_RUN_DIR` | `/tmp/juniper-e2e` | Screenshots + default results parent |
| `JUNIPER_E2E_SEG17_RESULTS` | `$JUNIPER_E2E_RUN_DIR/seg17_results.json` | Merged JSON (one object, keyed by step) |
| `JUNIPER_E2E_STORM_WATCH_S` | `60` | `storestorm` census window |
| `JUNIPER_E2E_REBUILD_WATCH_S` | `120` | `rebuildprobe` watch |
| `JUNIPER_E2E_REBUILD_STOP_AFTER` | `3` | `rebuildprobe` stop |
| `JUNIPER_E2E_QUIET_WAIT_S` | `90` | `quietread` wait |

There is **no** unittest for this driver on `main`. A second-instance A/B launcher (`2026-09-04_canopy_verify_instance.bash`) is proposed in #1672; it is **not** on `main` — do not invoke it as a shipped entry point.

### Operator pitfalls

| Symptom | Check / Fix |
|---------|-------------|
| `unknown step(s): …; valid: …` (exit `2`) | Name is not in `STEPS`. `w1grow` / `toposel` were removed. `topostate` / `topoexport` **are** registered even though the docstring still lists -13/-14 as unimplemented. |
| `ModuleNotFoundError: playwright` | Use `JuniperCanopy1`'s python, not ambient. |
| Cascor/canopy die or wrong torch during the drive | `LD_LIBRARY_PATH=` must be the empty string (isolated-stack cascor class). |
| `topo` PASS while the depth **label** still reads `"0 of 40"` | Expected on `main` — M-06's `OR` can pass on the stats bar alone; M-07 never asserts the label. |
| `topoevents` M-12 FAIL with `plotly_click_events=0` | Expected on `main` — empty-space click is unreachable. Do not "fix" it with `gd.emit`. |
| M-10 FAIL, every node `Layer: Output` | Product layer-label defect (F-CANOPY-045), not a miss-click. |
| M-13 / M-11 INDETERMINATE or "no plotly_* event" | Gesture never reached plotly — **driver** gap; do not file as a product FAIL. |
| `topo` FAIL, depth **label** still `"0 of 40"` | Expected until the product label follows the slider (F-CANOPY-042). M-06 now requires **both** halves; M-07 requires `"all"` at rest. |
| `topoevents` M-12 BLOCKED, no `-clear-selection` | Build predates the Clear button. Empty-space `plotly_click_events=0` is recorded, not a FAIL. Do not `gd.emit`. |
| `topoevents` M-12 FAIL, control visible | Selection survived the Clear button — F-CANOPY-046 regression. |
| M-17 FAIL after a green M-06 | Read `!! depth filter did NOT reset`. A leaked filter is this step's leftover, not a store-refresh defect. |
| M-18 FAIL / "store empty" after counting `/api/topology/raw` | Wrong traffic. The handler fetches server-side. Score the store: empty in Node Graph, populated in Weight Matrix. |
| M-14 FAIL, camera config looks correct | Control is the two-scheme SVG raster: `blob:` blocked + `data:` OK ⇒ canopy CSP, not the browser. |
| Ran `theme` and thought M-TOPOLOGY-09 was covered | `theme` is Dataset-tab M-DATASET-14. Topology-tab recolour is `topoevents`. |
| Ran `topo` and thought -09/-16/-18 were covered | `step_topo`'s function docstring still says `01..09/16..18`. The records it writes are 01–08 and 17. |
| Depth filter leaked into M-17 | `topo` resets the slider to `0` after M-06; if counts ≠ server it logs and continues. Read that line before filing M-17. |
| Restarted `:8051` to see a worktree fix | Use `2026-09-04_canopy_verify_instance.bash up <src>` instead; `:8051` serves what it imported at launch. |
| Verify instance vanished / reaper log `WOULD REAP` | Pidfile missing under `CANOPY_VERIFY_RUN_DIR`. Leave `canopy-<port>.pid` in place. |
| `down` killed the shared isolated canopy | `down` must be by pid. Do not `kill` whatever listens on the port. |
| `undefined symbol: _PyObject_NextNotImplemented` | Missing `LD_LIBRARY_PATH=`. Not a Playwright/assertion bug. |
| `--steps 1-9` → `no runnable steps` / exit `2` | W6 has no range parser. Use `1,2,4,7`. |
| Default W6 run never opens the restart modal | Default includes `7` (cancel). Use `1,2,4,10`. |
| Live 10-unit network gone after a "full W6" | You clicked `#restart-confirm-button` or called `/api/train/restart`. The driver refuses that on purpose. |
| `!! #restart-with-new-dataset-button absent` | Nothing staged. Run `1,2,4` first. |
| Generate modal "never opened" at 3 s | F-CANOPY-004 congestion. The driver polls ~40 s. |
| Every click times out at 30 s | Welcome modal still up. `ensure_no_modal` is the fix; do not treat as a dead control. |
| Selector option list is nonsense | Unscoped `[role=option]`. Use `aria-controls`. |
| Load-selected returns 400 | Expected on the LIVE arm (M-DATASET-11). |
| `offsetParent` says the modal is hidden | `position:fixed`. Use computed style + rect. |
| Exit `0` but the log is full of `!!` | By design. Read the log; do not gate on the process exit. |

Plan pointer (row ids, not this scorer): [`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md) §6.3.

---

## Canopy E2E Unfilled-Rows Ledger

`util/ad-hoc/e2e_unfilled_rows.py` answers "which click-by-click matrix rows still need a status cell?" by reading **the matrix and nothing else**. The matrix is the ledger. Plan a re-drive from this output, not from the verdict-file estimator.

Segment 15's first handoff draft planned from `e2e_row_coverage.py` under the ledger's headline — it would have re-driven already-`PASS` rows while dropping still-empty ones. The two tools can disagree on the same checkout.

### Why the estimator is not the ledger

| Surface | Path | What it reads | What "done" means |
|---------|------|---------------|-------------------|
| **Ledger (authority)** | `util/ad-hoc/e2e_unfilled_rows.py` | The matrix markdown only | Status cell is **not** a placeholder |
| Estimator | `util/ad-hoc/e2e_row_coverage.py` | Matrix row-id inventory **plus** `reports/e2e/*/statuses.tsv` and `rowlog.md` | A verdict-file token expands to that row id |

The estimator also over-credits compressed enumerations and treats a non-terminal `pending …` record as coverage. It is useful for "which run files mention this id?"; it is not the plan-from list.

Probed on `origin/main` `8da1f87e` (2026-09-05):

| | matrix rows | verdicted | remaining |
|---|------------:|----------:|----------:|
| Ledger | 298 | 298 | **0 UNFILLED** |
| Estimator | 298 | 296 | **2** (`M-PARAMETERS-02`, `M-PARAMETERS-03`) |

Both `M-PARAMETERS-02` and `M-PARAMETERS-03` are already `PASS` in the matrix status column. Planning from the estimator would re-drive them. The estimator also printed **129 unmatched tokens** (W-ids, finding ids, phase labels) that are not matrix rows.

### Contract (verified against `e2e_unfilled_rows.py` + `e2e_matrix_fill.py`)

- Default matrix: `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` (`e2e_matrix_fill.DEFAULT_MATRIX`). Override with `--matrix` or `--repo-root`.
- Reuses the filler's `split_row` / `is_separator` / `PLACEHOLDERS` / `MATRIX_NAMESPACES` so the answer cannot drift from what `e2e_matrix_fill.py` will write.
- **Namespaces counted:** row ids starting with `C2.` or `M-` only. W-series ids are **not** ledger rows here — they never enter the count, even if a TSV mentions them.
- **Placeholders** (unfilled): `""`, `—`, `-`, `--`, `TBD`, `n/a`. Any other status cell counts as verdicted — including `PASS`, `FAIL`, `BLOCKED`, `SKIP`, `N/A`, and a qualified `PASS (name arm; …)`.
- Status column is the header cell whose stripped name is `status` (case-insensitive). Row id is `cells[1]` after an escaped-pipe split (`\\|` stays inside its cell — the C2.2-04 `display:block\|none` class).
- Grouped by the nearest preceding `###` heading. Sections with zero unfilled ids are omitted from the table; the header totals still include them.
- **Exit 0 always** (report-only). A zero `UNFILLED` count is a measurement, not a CI gate.
- Does **not** read `reports/e2e/**` and does **not** expand `01..06` / `01/02/03` tokens. Those are estimator / filler concerns.

```bash
python3 util/ad-hoc/e2e_unfilled_rows.py
python3 util/ad-hoc/e2e_unfilled_rows.py --repo-root /path/to/juniper-ml
python3 util/ad-hoc/e2e_unfilled_rows.py --matrix /path/to/other-matrix.md
```

The filler that writes status cells is `util/ad-hoc/e2e_matrix_fill.py`. This page does not replace that writer; it is the reader that agrees with it.

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Estimator `remaining` is non-zero but ledger says `UNFILLED: 0` | Trust the ledger. The matrix status cell is already filled; the TSV/rowlog never recorded that id (or recorded it as a non-head token). |
| Estimator `remaining` is zero but ledger still lists ids | Estimator over-credited a compressed range or a `pending …` record. Re-drive the ledger's list. |
| W-ids appear in estimator `unmatched` / "remaining by group" | Not `C2.` / `M-`. The ledger ignores them. Do not invent matrix rows from TSV tokens. |
| Status looks filled in the Evidence column but UNFILLED | Wrong column — only the `status` header cell counts. |
| A `\\|` cell shifted every verdict left and the status cell stayed empty | Pre-`split_row` bug (C2.2-04). Confirm you are on a tree that imports `e2e_matrix_fill.split_row`. |
| Script exits 0 with `UNFILLED: 0` and you treat that as CI-green | Exit 0 is unconditional. Read the `UNFILLED` line. |

No unittest for this reader is on `origin/main` yet (open test PR #1645 does not land the pin). Do not claim hermetic coverage until that suite merges.

---

## Fleet Triage and Sequence Safety

Flood-remediation tooling for Cursor-fleet / third-party open PRs and for silent symbol/docs damage that ordinary lint cannot see. Two layers:

| Layer | Path | Role |
|-------|------|------|
| Sequence-safety screens | the `juniper-symbol-loss-check` / `juniper-docs-additions-check` console scripts (PyPI `juniper-ci-tools>=0.8.0`) | Path-invoked BASE..HEAD screens used by CI (`sequence-safety` job, `main-verify.yml`) |
| Predicted-merge triage | `util/fleet_triage/predict_merge.py` | Detached-clone merge of `origin/main` into a PR tip; runs fast gates + screens on the **merge RESULT** |
| Fleet supervisor agent | `.claude/agents/fleet-supervisor.md` | Read-only adjudication over a `--batch` report (never pushes/merges/closes) |

Design context: [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) §4 items 7–8.

### Sequence-safety CLIs

```bash
juniper-symbol-loss-check --base origin/main --head HEAD --json
juniper-docs-additions-check --base origin/main --head HEAD --json
# WARN-only exit 0 (label hatch); exit 2 is never masked:
juniper-symbol-loss-check --base origin/main --head HEAD --advisory
```

| Concern | Default scope | FAIL classes | Primary waiver |
|---------|---------------|--------------|----------------|
| Symbol loss | `tests/*.py` + `util/**/*.{py,bash}` | `LOST` / `WEAKENED` / `DUPLICATED` (py FAIL; bash LOST FAIL, WEAKENED/DUPLICATED WARN) | Commit trailer `Allow-Symbol-Loss: <qualified.symbol>[, …]` in BASE..HEAD |
| Docs deletions | `AGENTS.md` + `docs/**` + `notes/**` | Deleted heading, or ≥`--min-run` (default 5) consecutive deleted lines | Commit trailer `Allow-Docs-Rewrite: <path>` (or enumerated paths / `*`) |

Constraints (verified in the checkers):

- Qualified symbols only (`func:name`, `method:Class.name`, …). Bare-name relocation is **not** a downgrade (SF3).
- `Allow-Symbol-Loss: *` / blanket wildcards are **rejected** (waive nothing).
- `Allow-Docs-Rewrite: *` **is** accepted (waives every deleted `.md` in scope) — opposite of the symbol wildcard rule.
- Per-PR labels `allow-symbol-loss` / `docs-rewrite` only demote the per-PR job via `--advisory` (WARN-only exit 0). That greens the required `Sequence Safety` context on the PR. They are invisible to `push:main` `main-verify` — use the commit trailer for post-merge green.
- Exit codes: `0` clean, `1` ≥1 unwaived FAIL, `2` usage / bad ref. Gates: `tests/test_symbol_loss_check.py`, `tests/test_docs_additions_check.py`.

### `predict_merge.py` operator contract

```bash
python util/fleet_triage/predict_merge.py --pr 895 --json
python util/fleet_triage/predict_merge.py --batch --json
python util/fleet_triage/predict_merge.py --pr 895 --repo-root .
# Skip the pre-commit battery when hooks are unavailable locally:
JUNIPER_FLEET_SKIP_PRECOMMIT=1 python util/fleet_triage/predict_merge.py --pr 895
```

Per PR, the script:

1. Creates a throwaway **detached** `git clone --shared` under the system tempdir (never a worktree, never writes the source checkout, never pushes).
2. Merges `origin/main` into the branch tip (`git merge --no-ff`, `commit.gpgsign=false`).
3. On the RESULT: runs `pre-commit` hooks `black` / `isort` / `flake8` / `mypy` / `check-ast` over `changed_existing` — the TRUE delta filtered to paths that still resolve as a blob at `HEAD` — and **only when that set contains at least one `.py` file**; otherwise each hook reports `status=skip` with detail `no .py files in delta` (docs-only / non-Python PRs never invoke the gate runner). A **deleted** `.py` therefore stays in `true_delta` for the symbol screen but is never handed to `pre-commit --files`, so a pure-deletion PR can be gate-clean and still `DAMAGED-FIX-FIRST` from the symbol screen. `JUNIPER_FLEET_SKIP_PRECOMMIT=1` forces `skip_all`. It also shells out to `juniper-symbol-loss-check (juniper-ci-tools) --repo-root <clone> --base <base> --head <result> --json` (same CLI as `main-verify` — juniper-ml#895 / ml#872); runs an **inline** docs additions-only screen that flags **any** removed content line on a changed `.md` (deliberately stricter than `juniper-docs-additions-check`'s heading / `--min-run` gate) and honors `Allow-Docs-Rewrite: <path>[, …]` / `*` trailers in `BASE..RESULT` (juniper-ml#926 — same escape hatch as sequence-safety so intentional rewrites are not forever `DAMAGED-FIX-FIRST`).
4. Emits the **TRUE** changed-file delta from `git diff --name-only origin/main <result>` (not the stale `gh pr … --json files` list).

| Verdict | Meaning (verified in `simulate_merge`) |
|---------|----------------------------------------|
| `MERGE-CLEAN` | Merge succeeds; not behind main; no gate / symbol-screen / docs-screen `status=fail` |
| `NEEDS-UPDATE-BRANCH` | Merge succeeds; branch tip is **behind** `origin/main`; screens/gates did not fail |
| `DAMAGED-FIX-FIRST` | Merge succeeds; a fast-gate hook **or** symbol screen **or** docs screen reports `status=fail` |
| `CONFLICT` | Merge conflict against `origin/main` |
| `ERROR` | `--batch` only: soft-fail row when a single PR cannot be simulated (e.g. unresolvable `origin/<headRefName>`); `true_delta=[]` and the rest of the open-PR set still runs |

`--batch` also builds a same-file cluster map and a suggested merge order. Heal-first detection (`_is_heal`) looks at the PR **title** and **branch** (case-insensitive) for any of `restore` / `heal` / `repair` / `fix-first`, sorts those ahead of ordinary PRs, then ascending same-file contention. `triage_batch` **continues** after a per-PR `PredictMergeError` (the `ERROR` row above). Exit `0` always reports (even when every verdict is `DAMAGED` / `CONFLICT` / `ERROR`); exit `2` is usage/precondition only (`gh` missing, bad `--repo-root`, or an unresolvable ref in single `--pr` mode).

**`--pr` hard-fail vs `--batch` soft-ERROR.** The two modes deliberately diverge on a `gh` failure: in single-PR mode `triage_pr` raises `PredictMergeError` when `gh` exits nonzero or returns non-JSON, so the CLI exits `2` (there is no partial report worth printing). In `--batch`, the same condition becomes a soft `ERROR` row for that PR only, and the rest of the open-PR set still runs. An exit `2` from `--pr` is a precondition failure, never a damage finding.

Degrade paths (never crash the report): missing/broken `symbol_loss_check.py`, checker exit `2`, or non-JSON stdout → symbol screen `status=skip`. A delta with no `.py`/`.bash` short-circuits the symbol subprocess. Gate: `tests/test_predict_merge.py` (incl. `Allow-Symbol-Loss` and `Allow-Docs-Rewrite` trailer → `MERGE-CLEAN` arms).

#### Docs screen vs `docs_additions_check.py` (honesty)

| | `docs_additions_check.py` (CI / main-verify) | `predict_merge` inline docs screen |
|--|---------------------------------------------|-------------------------------------|
| Scope | `AGENTS.md` + `docs/**` + `notes/**` | Every changed `.md` in the TRUE delta |
| FAIL threshold | Deleted heading, or ≥`N` consecutive deleted lines (default 5) | **Any** removed content line (`-` not `---`) |
| `Allow-Docs-Rewrite` trailer | Yes (path / basename / `*`) | Yes (path / basename / `*` — juniper-ml#926) |
| JSON | Full screen report | `deletions` + `waived` lists on the docs screen object |

Do not assume trailer-less docs deletions that pass `--min-run` on main-verify will be `MERGE-CLEAN` in fleet triage — the inline screen is stricter by design.

### Operator pitfalls

| Symptom | Check / Fix |
|---------|-------------|
| Local run hangs on pre-commit | Set `JUNIPER_FLEET_SKIP_PRECOMMIT=1`, or ensure `pre-commit` is installed and hooks cached |
| `DAMAGED-FIX-FIRST` after intentional **symbol** deletion | Add `Allow-Symbol-Loss: func:…` (qualified) on a commit in the PR range; re-run `--pr`. Wildcard `*` is rejected. |
| `DAMAGED-FIX-FIRST` after intentional **docs** rewrite | Add `Allow-Docs-Rewrite: docs/REFERENCE.md` (or `*` / basename) on a commit in BASE..RESULT; re-run `--pr` (#926). Wrong-path trailers do not waive. |
| Trailer present but still DAMAGED (symbols) | Wildcard `*` is rejected; bare names do not match; trailer must be in BASE..HEAD of the **merged** result |
| Trailer present but still DAMAGED (docs) | Path must match the deleted `.md` (full path or basename); confirm the trailer commit is in `origin/main..<result>` |
| Expecting docs screen == `docs_additions_check.py` | Same trailer escape hatch, different FAIL threshold — see honesty table above |
| Agent closes / merges PRs | Forbidden — `fleet-supervisor` is read-only; DUP-CLOSE needs overlap **and** owner confirmation |

## Worktree Divergence Is a Memory Cost

**A stale worktree silently doubles the memory bill of every session run inside it.**
The mechanism is entirely non-obvious, which is why it went unnoticed for months.

### Why

Claude Code deduplicates memory files **by content**. The main checkout's `AGENTS.md`
is a filesystem *ancestor* of `.claude/worktrees/<name>/`, so:

| Worktree `AGENTS.md` vs main checkout | Result |
|---------------------------------------|--------|
| identical | injected **once** |
| differs | **both load** |

Confirmed empirically by the P1 canary probe
([`util/ad-hoc/2026-08-19_build_ancestor_canary_probe.bash`](../util/ad-hoc/2026-08-19_build_ancestor_canary_probe.bash)):
a synthetic tree with deliberately different plain-text canaries at root and
worktree level returned **both** canaries, with a positive control confirming the
method. Full evidence:
[mechanism facts §8c](../notes/JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md).

### The scale of it, measured

On 2026-08-19, of 23 live worktrees, there were **11 distinct `AGENTS.md` contents
and only 1 matched the main checkout** — so 22 of 23 sessions were loading two full
copies. A session in a divergent worktree carried **344,450 characters (~43% of a
200k window)** against 204,889 (~26%) for a matching one.

**The baseline understated the real cost by roughly 2× for almost every session.**

### What to do

- **Prune worktrees on merge.** A merged, clean worktree left lying around is a
  permanent second copy of `AGENTS.md` in every future session that lands in it.
- **Keep long-lived worktrees rebased**, so their `AGENTS.md` converges with main
  and dedup keeps working.
- This **compounds with** the P3 relocation rather than competing: after the cut a
  divergent worktree costs 2 × 45K instead of 2 × 173K.

### Before removing anything: check for a live session

`scripts/cleanup_session_worktrees.py` gates on **not locked**, then on *branch*
state — merged, clean, not the current cwd. Even together, those are necessary and
**not sufficient: merged-and-clean does not mean idle.** A session can have just
merged its PR and be about to start the next task in the same worktree.

The `locked` flag is the built-in liveness signal — Claude Code locks a live
session's worktree and names the session and pid in the lock reason. **The script
did not read it until 2026-08-21.** Measured against the real set that day, the old
code reported `removed=8`, of which **three were locked live sessions**, one holding
the head branch of an open PR: merge state says nothing about whether someone is
working in there right now. A single `--force` does not defeat a lock (git refuses),
so a live run could never actually delete a session — the damage was to the *plan*,
because `--dry-run` promised removals a real run would refuse, and the operator who
reconciles that contradiction reaches for `-f -f` or unlocks by hand. The removal
call no longer passes `--force` at all. Gate: `tests/test_cleanup_session_worktrees.py`
`LockGateTest`.

The flag is still only a *supplement* to judgment: a session idling elsewhere while
holding a worktree open is invisible to it, and during the 2026-08-20 sweep both
worktrees locked earlier in that effort had already released.

So run
[`util/ad-hoc/2026-08-20_worktree_liveness_probe.py`](../util/ad-hoc/2026-08-20_worktree_liveness_probe.py)
first. It walks `/proc/<pid>/cwd` and reports any process working inside a
candidate. **On its first use it caught `piped-drifting-dragon`** — which passed
every gate the cleaner has while a live session held it, with MCP servers rooted
inside.

A hit is a hard stop for that worktree. **No hits is corroboration, not proof:** a
session idling elsewhere in the filesystem while holding the worktree open would not
be seen. cwd-only also misses an editor or a long `pytest` whose cwd is elsewhere
while a file inside the tree is still open. The P5 cleaner
[`util/ad-hoc/2026-08-28_p5_worktree_cleanup.py`](../util/ad-hoc/2026-08-28_p5_worktree_cleanup.py)
uses the same cwd-only `occupied()` gate (never argv).

### Wider second opinion: open files and argv

[`util/ad-hoc/2026-09-02_worktree_inuse_probe.py`](../util/ad-hoc/2026-09-02_worktree_inuse_probe.py)
is an independent second opinion with a wider net, for sweeping another session's
possible workspace. It does not remove anything. Read-only: opens `/proc` entries
and nothing else.

```bash
python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py <worktree-dir> [<worktree-dir> ...]
```

| Signal | Predicate | Strength | Effect |
|--------|-----------|----------|--------|
| cwd | exact match, or cwd starts with `tree/` (`os.sep`) | STRONG | `IN USE`, exit 1 `REFUSE` |
| open fd | any fd target inside the tree | STRONG | same |
| cmdline | path substring in argv | WEAK | `review` / `CAUTION`; exit stays 0 |

**Why WEAK does not fail the process.** The first run reported every tree `IN USE`
because the probe itself and the launching shell named the paths as arguments. A
checker whose own invocation trips it is useless: a real hit is indistinguishable
from the noise floor, and the natural next move is to ignore it. Self and parent
pids are excluded from WEAK by pid, not by pattern. Any *other* process naming the
path is still printed — glance before removing.

**Sibling prefix.** `foo-extra` is not inside `foo`. cwd/fd use `== t or startswith(t + os.sep)`, never bare `startswith(t)`.

**Other users.** Unreadable `/proc` entries (other uids) are counted and reported
(`NOT checked`), never treated as in-use.

**Empty argv.** Prints the docstring and exits **2**. The cwd-only liveness probe
exits 0 on the same misuse — do not copy that.

Status per tree: `IN USE` (any STRONG), `review` (WEAK only), `free` (neither).
Run this after the cwd-only probe, then remove worktrees individually and
**never with `--force`**, so git's own dirty-check stays live as a
time-of-check/time-of-use guard.

---

## Worktree Procedures Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

> **OPERATING INSTRUCTION**: All feature, bugfix, and task work SHOULD use git worktrees for isolation. Worktrees keep the main working directory on the default branch while task work proceeds in a separate checkout.

### What This Is

Git worktrees allow multiple branches of a repository to be checked out simultaneously in separate directories. For the Juniper ecosystem, all worktrees are centralized in **`/home/pcalnon/Development/python/Juniper/worktrees/`** using a standardized naming convention.

The full setup and cleanup procedures are defined in:

- **`notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`** -- Creating a worktree for a new task
- **`notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`** -- Merging, removing, and pushing after task completion (V2 -- fixes CWD-trap bug)

Read the appropriate file when starting or completing a task.

### Worktree Directory Naming

Format: `<repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>`

Example: `juniper-ml--chore--update-deps--20260225-1430--519bda91`

- Slashes in branch names are replaced with `--`
- All worktrees reside in `/home/pcalnon/Development/python/Juniper/worktrees/`

### When to Use Worktrees

| Scenario                                    | Use Worktree? |
| ------------------------------------------- | ------------- |
| Feature development (new feature branch)    | **Yes**       |
| Bug fix requiring a dedicated branch        | **Yes**       |
| Quick single-file documentation fix on main | No            |
| Exploratory work that may be discarded      | **Yes**       |
| Hotfix requiring immediate merge            | **Yes**       |

### Quick Reference

**Setup** (full procedure in `notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`):

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git checkout main && git pull origin main
BRANCH_NAME="chore/my-task"
git branch "$BRANCH_NAME" main
REPO_NAME=$(basename "$(pwd)")
SAFE_BRANCH=$(echo "$BRANCH_NAME" | sed 's|/|--|g')
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/${REPO_NAME}--${SAFE_BRANCH}--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD)"
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
cd "$WORKTREE_DIR"
```

**Cleanup** (full procedure in `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`):

```bash
# Phase 1: Push current work
cd "$OLD_WORKTREE_DIR" && git push origin "$OLD_BRANCH"
# Phase 2: Create new worktree BEFORE removing old (prevents CWD-trap)
git fetch origin
git worktree add "$NEW_WORKTREE_DIR" -b "$NEW_BRANCH" origin/main
cd "$NEW_WORKTREE_DIR"
# Phase 3: Create PR (do NOT merge directly to main)
gh pr create --base main --head "$OLD_BRANCH" --title "<title>" --body "<body>"
# Phase 4: Cleanup
git worktree remove "$OLD_WORKTREE_DIR"
git branch -d "$OLD_BRANCH"
git worktree prune
# Phase 6: Sync to latest main (Case A — still in the continuity worktree): sync in place
git fetch --all && git pull --ff-only origin main
# Case B (terminal — no session worktrees left): git fetch --all && git checkout main && git pull --ff-only origin main
# Phase 7 (always, after every merged-PR cleanup): restore the PRIMARY checkout to up-to-date main
# (skip if its tree is dirty — F-6 stale-checkout guard)
cd <path-to-repo-root> && git checkout main && git pull --ff-only origin main
```

**Automated cleanup** (via script):

```bash
util/worktree_cleanup.bash \
  --old-worktree "$OLD_WORKTREE_DIR" \
  --old-branch "$OLD_BRANCH" \
  --parent-branch main
```

### Rules

- **Centralized location**: All worktrees go in `/home/pcalnon/Development/python/Juniper/worktrees/`. Never create worktrees inside the repo directory.
- **Clean before you start**: Ensure the main working directory is clean before creating a worktree.
- **Push before you merge**: Always push the working branch to remote before merging (backup).
- **Prune after cleanup**: Run `git worktree prune` after removing a worktree to clean metadata.
- **Do not leave stale worktrees**: Clean up worktrees promptly after merging.

---

---

## Memory File Size Budget

P2 of the [shared-session-memory plan](../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md).
`util/memory_budget_check.py` enforces a character ceiling on always-loaded memory
files, declared in `conf/memory_budget.json`. Run by the standalone `Memory Budget`
job in `ci.yml`.

> **BLOCKING as of 2026-08-20 (P4).** The budget step no longer passes `--advisory`;
> a violation exits `exit 1` and fails the check. The companion **G3** step in the same job
> stays advisory — see [Relocation Completeness](#relocation-completeness-g3) for why.
>
> To make it actually gate a merge, it must also be a **required context** in the branch
> ruleset. That is a settings change, not a repo change, and it is deliberately promoted
> there rather than through the Quality Gate `needs:` — a standalone job that skips on
> `push` must never be able to fail the aggregate gate.
>
> A required context with **no** `integration_id` is satisfied by any app publishing that
> name ([juniper-ml#1611](https://github.com/pcalnon/juniper-ml/issues/1611)). Pin the
> publisher with `--amend-integration-id` — see [Required-Context Ruleset Writer](#required-context-ruleset-writer).
> Do not hand-roll a ruleset PUT.
>
> **If it blocks you:** relocate the content to this file and leave a pointer that keeps
> an accurate open/closed status. If the growth is genuinely warranted, add
> `Allow-Budget-Overrun: AGENTS.md` and **carry it into the squash message** — that is a
> loan, not a pass: the ceiling does not move, so the debt blocks the next author until
> someone relocates.

**Why it exists.** `AGENTS.md` grew ~20× in six months *while under four active CI
gates* — every one of them enforces structure or currency, none enforces size. 172
of 200 main-line merges grew it; 14 shrank it, by 2,628 bytes between them. A
one-time cut is undone in ~44 days, so the ratchet is what makes a cut durable.

**Characters, not bytes.** The shipped Claude Code check compares `content.length`.
`AGENTS.md` is 173,591 bytes but 171,765 characters; using bytes overstates by ~1%.

### The three rules

| Rule | Behaviour |
|------|-----------|
| **Ceiling** | Each governed file has a `ceiling_chars` in `conf/memory_budget.json`. |
| **No-worsening** | Over-ceiling alone does **not** fail — the change must *also* grow the file. |
| **Ratchet** | `--ratchet` rewrites ceilings **downward only**; it can never loosen one. |

The no-worsening rule is load-bearing and is stated by none of the source
proposals. Without it, a single over-budget file on `main` blocks every unrelated
PR until someone fixes it — which is how a gate gets disabled rather than obeyed.
A PR that *shrinks* an over-ceiling file always passes, so the gate never punishes
the cleanup it is asking for.

### The waiver is a loan, not a pass

`Allow-Budget-Overrun: <path>` in a commit message suppresses the failure for that
path **without moving the ceiling** — the debt is still owed, and the next author
still sees it. That is the property the house `Allow-Symbol-Loss:` idiom lacks.
Waivers are always reported, never silent. Carry the trailer into the **squash**
commit message; trailers travel in git history.

**Both forms parse** (since 2026-08-24) — a bare path, or a path plus a reason after a
`-`, `–` or `—` separator. **One path per line**; a second path on the same line is
*not* a second waiver:

```text
Allow-Budget-Overrun: AGENTS.md
Allow-Budget-Overrun: AGENTS.md — landing the relocation, debt repaid in #1234
```

Anything that starts with `Allow-Budget-Overrun:` / `Allow-Ceiling-Raise:` and does not
parse is reported as a `::warning::` naming the offending line. Before 2026-08-24 only
the bare form parsed and the reason form was dropped **silently**, while two design docs
mandated the reason form and stated the inverse — so a waiver written from the
documentation did nothing and gave no clue why.

### Not governed: `docs/REFERENCE.md`

Deliberately absent from the budget. It is the migration **destination**; capping it
would penalize exactly the relocation the plan wants, and it is not an always-loaded
memory file — it is read on demand, which is the entire point.
`tests/test_memory_budget_check.py` pins this.

### Vacuous-pass resistance

This repo has a documented class where a check's machinery breaks and reports
SUCCESS. Each way this gate could go blind is a hard exit 2, with a negative
control in the test suite: a governed file that is **missing**, an **empty**
governed set, an **unreadable** or **absent** budget file, and a non-positive
ceiling. A gate that cannot fail is not a gate.

### Usage

```bash
python util/memory_budget_check.py                      # check (exit 0/1/2)
python util/memory_budget_check.py --advisory           # report, always exit 0
python util/memory_budget_check.py --json               # machine-readable
python util/memory_budget_check.py --ratchet            # tighten to current sizes
# The CI job's exact form. The bare form has NO git-log fallback, so a branch carrying an
# Allow-Budget-Overrun / Allow-Ceiling-Raise trailer FAILS locally where CI passes:
git fetch origin && git log --format=%B origin/main..HEAD > /tmp/mb-trailers.txt
python util/memory_budget_check.py --base-ref origin/main --trailers-file /tmp/mb-trailers.txt
```

`--base-ref` supplies the tip the no-worsening rule compares against (CI uses `FETCH_HEAD` of the
PR base); `--trailers-file` is the only way trailers reach the checker — it never shells out for
them, so the classifier stays pure.

Exit **0** pass or advisory / **1** over budget / **2** misuse or broken machinery.

`headroom` in this output is `ceiling_chars - current chars`. It is **not** "required slack".
Sizing slack after a cut is a planning step on a different tool — see
[Memory-Budget Slack (Planning)](#memory-budget-slack-planning).

---

## Memory-Budget Slack (Planning)

The CI gate above answers "may this PR grow `AGENTS.md`?" The planning tools answer "how much
working room should the *ceiling* keep after a cut?" Mixing the two is how a green `Memory Budget`
check gets read as an emergency relocation.

Plan: [`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md) §P5.
Cut / promote helpers: `util/ad-hoc/2026-08-28_p5_cut.py`, `util/ad-hoc/2026-08-26_p5_promote_ready.py`
(`SLACK_FLOOR = 2000`). Growth instrument: `util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth`.
Fleet census: `util/ad-hoc/2026-08-26_p5_fleet_state.py`.

### Two numbers, two tools

| Number | Who computes it | Formula | Gates a PR? |
|--------|-----------------|---------|-------------|
| **headroom** | `memory_budget_check.py` (`evaluate`, printed as `headroom=`) and `p5_fleet_state.py` | `ceiling_chars - chars` | No. The gate fails only when the file is **over ceiling and grew**, or the ceiling was **raised** without `Allow-Ceiling-Raise:`. |
| **planning slack** | `p5_cut.py` / `p5_promote_ready.py` after they shell `measure-growth` | `max(largest 30-day growing commit, 2000)` | No. Used only to *set* a ceiling after a cut. |

`util/memory_budget_check.py` never reads growth stats, never computes slack, and has no
`--exclude` / required-slack flag. A checkout can be CI-green with headroom well below the
planning figure.

The 2,000 floor is the fleet-wide fan-out class: one 2026-08-21 docs sweep added 1,982 chars to
six repos' `AGENTS.md` at once (`p5_promote_ready.py` docstring). A zero-slack ceiling fails
that class by construction.

### How to measure

`measure-growth` defaults `--ref` to the checkout's `HEAD`. A primary that has not been pulled
reports yesterday's `main`. After a fetch, pass `--ref origin/main`. The helper's own docstring:
run it, do not quote it.

```bash
git fetch origin
python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth . --days 30 --ref origin/main
python3 util/ad-hoc/2026-08-26_p5_fleet_state.py          # nine-repo census from GitHub API (chars, not bytes)
python util/memory_budget_check.py --json                 # this checkout's headroom only
```

`measure-growth` prints `median`, nearest-rank `p90` (`ceil(n * 0.9)`-th growing commit;
`tests/test_p5_port_memory_budget.py` pins the floor form that printed p90 < median), and `max`,
then:

```text
=> slack must absorb a single growing commit: >= <max> covers the largest seen.
```

There is **no** `required slack` field. A number that is neither `max` nor the 2,000 floor was
not produced by this instrument — it was hand-picked. Size slack from `max` (then the 2,000
floor), **never from p90**. The helper reports p90 because a reader will size from it anyway;
`p5_promote_ready.py` states p90 is unreliable below ~10 growing commits.

Worked example, re-measured on `origin/main` `06e81d3a` (2026-09-04), 30-day window: this repo
printed `median 498  p90 2838  max 61435` and `headroom=3216` against ceiling 38,000. Against
p90 the file looks loose; against `max` it looks starved. Both readings are the same instrument
pair. The 61,435 `max` is a pre-cut growing commit still inside the window — the tool has **no
exclusion flag** for cuts or relocations. Do not invent a third "required slack" between those
two figures, and do not start a relocation because headroom < `max`.

### After a cut, do not `--ratchet`

`--ratchet` rewrites every ceiling **down to the exact current size** (`memory_budget_check.py`).
That leaves **zero** headroom, so the next author who adds one character fails. After a real cut,
hand-edit `conf/memory_budget.json` to `current + slack` with slack re-measured in *that* repo.
`render-config` seeds at exact size on purpose (the soak); promotion is a later hand-edit.

Order the fleet by **rate**, not file size. The 2026-08-25 measurement in the helper docstring:
cascor ~730 chars/day vs canopy ~81/day — nine times faster, smaller file. Re-measure; do not
reuse that pair.

`p5_fleet_state.py` reads origin `main` through `gh api` and counts `len()` of UTF-8 text. The
API `size` field is **bytes**; a census that compared bytes to a char ceiling reported two repos
over when both sat exactly at ceiling (2026-08-26). It prints `headroom`, not planning slack.

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| `Memory Budget` green, but headroom < planning slack | Expected. Slack is not a CI input. Do not relocate on that comparison. |
| A note quotes "required slack" that is neither `max` nor 2,000 | Not an instrument output. Re-run `measure-growth --ref origin/main`. |
| Slack sized from `p90` | The helper warns against this. Use `max`, then the 2,000 floor. |
| `% of slack` disagrees with a sibling note | Different denominators (headroom / ceiling / `max` / 2,000). Name the inputs. |
| `measure-growth` looks stale vs GitHub | Default `--ref` is `HEAD`. Fetch and pass `--ref origin/main`. |
| `--ratchet` right after a cut | Next growing PR fails. Hand-edit slack. |
| Ordered the cut by file size | Rate axis. Re-run `measure-growth` per repo. |
| Fleet census says over-ceiling, local check says OK | Bytes vs chars, or a stale local checkout. Trust `len()` / `--json`. |
| `only N commit(s) touched AGENTS.md` | Widen `--days`; fewer than two commits is "no growth", not zero slack. |

Ad-hoc inventory: [`util/ad-hoc/README.md`](../util/ad-hoc/README.md) § Memory-budget slack.

Distinct from [`MEMORY.md` Index Check](#memorymd-index-check) (`util/memory_index_check.py`): that tool governs the always-loaded Claude Code index outside the repo. This section is the `AGENTS.md` CI ceiling.


## MEMORY.md Index Check

`util/memory_index_check.py` — option A of [`notes/JUNIPER_2026-08-24_JUNIPER-ML_MEMORY-INDEX-RUNWAY-AND-ENFORCEMENT-OPTIONS.md`](../notes/JUNIPER_2026-08-24_JUNIPER-ML_MEMORY-INDEX-RUNWAY-AND-ENFORCEMENT-OPTIONS.md). Local linter for the Claude Code project index. Distinct from [Memory File Size Budget](#memory-file-size-budget) (`AGENTS.md` CI).

**Why it exists.** `MEMORY.md` is loaded into every session and truncates **silently, newest-first** at **200 lines / 25,000 UTF-8 bytes**. The newest rows are the ones a session just learned. Eviction, trim, or rewrite cannot buy more than the whole cap (~40 days from empty at any observed rate). Only governing what goes **in** moves the date.

The tool prints the current rate from `conf/memory_index_baseline.json` `history`. Do not transcribe a runway number into a note — it went stale twice while the checker was being written.

### What it measures

| Quantity | How | Cap |
|----------|-----|-----|
| Lines | `len(text.splitlines())` — **every** line, including headings and blanks | 200 |
| Bytes | `len(text.encode("utf-8"))` | 25,000 |
| Rows | lines matching `- [Title](slug)hook` | not a hard cap |
| New-row hook | `len(hook)` vs `--hook-max` (default **120**) | new slugs only |

Owner decision #4 is "120 bytes on NEW entries only". A **whole-line** 120-byte reading is unwritable: the link alone averages ~90 characters and reaches 115. The shipped comparison is `len(hook)` (Python characters after the closing `)`), which is the only reading the corpus can satisfy. Grandfathered slugs never fire, so the first run does not produce 137 findings and get ignored.

"NEW" is any parsed slug absent from `conf/memory_index_baseline.json`. `MEMORY.md` has **no git history**, so the tool carries its own baseline. A missing baseline is tolerated (`slugs: []`); every row is then new.

### Where the file lives

Default path is `~/.claude/projects/<slug>/memory/MEMORY.md`. `<slug>` is the **primary checkout** path with `/` replaced by `-`, resolved via `git rev-parse --path-format=absolute --git-common-dir` then `.parent`. A worktree must share the main checkout's index; if git is unavailable the resolver falls back to `--repo-root` and will look at a nonexistent worktree-local path.

CI **cannot** see the real file. `ci.yml` runs `tests/test_memory_index_check.py` against fixtures. That suite **is** the gate (`util/` is outside every pre-commit Python hook). Pass `--skip-if-absent` only on a host that legitimately has no index; the skip is printed. Without it, a missing file is **exit 2**, not a silent pass.

### Usage

python3 util/memory_index_check.py                     # check (exit 0/1/2)
python3 util/memory_index_check.py --json
python3 util/memory_index_check.py --advisory          # report, always exit 0
python3 util/memory_index_check.py --accept            # grandfather current slugs + one growth sample
python3 util/memory_index_check.py --skip-if-absent    # CI / hosts with no ~/.claude index
python3 util/memory_index_check.py --memory-file PATH --baseline PATH

Exit **0** pass, advisory, skipped, or `--accept` / **1** over the hard cap or a new oversize hook / **2** missing file (unless skipped), unreadable text, or malformed baseline.

`--accept` always exits 0, even when the file is already over the hard cap — it grandfathers slugs and records today's `(date, rows, lines, bytes)` sample (replacing a same-day sample). Re-run the bare check after accept to see remaining hard-cap debt.

Runway uses the **last two** `history` samples with integer `bytes` and parseable dates. Fewer than two, a same-day pair, or a non-positive span → `n/a`. A shrinking index → `no growth` (`inf`), never a negative day count. Warns at 85% of either hard cap (`::warning::`); over either cap prints `OVER THE HARD CAP`.


| Symptom | Cause / fix |
|---------|-------------|
| Exit 2 `memory index not found` | Default path uses the **primary** checkout slug. Pass `--memory-file`, or `--skip-if-absent` on CI. |
| First run flags every row | No baseline / empty `slugs`. `--accept` once after reviewing hooks, then keep new hooks ≤ 120. |
| Long slug fails a "120-byte line" reading you invented | Cap is the **hook**, not the line. A 130-character slug with ` — tiny` is OK. |
| Grandfathered long hook still listed | It should not fail. If it does, the slug in the baseline does not match the `(slug)` in the row. |
| `--accept` then still over the hard cap | Expected. Accept does not evict. Shorten or demote **detail**; keep STATUS (open / shipped / refuted) on the row. |
| Runway `n/a` | Need two dated samples. Run `--accept` on different days. |
| CI green, local index exploding | CI never reads `~/.claude`. Run the checker on the host that writes the index. |

Tests: `tests/test_memory_index_check.py`. Pins: missing file → 2; `--skip-if-absent` announced; malformed baseline → 2; hook-not-line; grandfathered oversize passes; `--advisory` still reports; `--accept` records a sample; shrinking runway is `inf`; shipped constants 200 / 25000 / 120.

---

## Relocation Completeness (G3)

`util/relocation_check.py` — gate **G3** of the
[shared-session-memory plan](../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md).
Runs as an advisory step of the `Memory Budget` job.

**Why it must exist before the P3 cut.** The repo's only mechanical content-loss
alarm cannot see a relocation:

- `juniper-docs-additions-check` FAILs only when `added == 0`. *"Delete a block,
  leave a pointer, keep the heading"* — exactly what a relocation looks like — is a
  WARN at any magnitude.
- A **token-level** check does not help either. A relocation that carries the
  identifiers but drops the surrounding reasoning scores as complete, because the
  identifiers survive in the destination while the prose that explained them does
  not. That is the loss this repo actually suffers.

So without G3 the migration would proceed with **no** content-loss control.

### What it asserts

Every substantive line **removed** from the source between BASE and HEAD must have
a sufficiently similar line **present** in the destination at HEAD. Similarity is
computed on normalized prose (markdown emphasis, link syntax, list markers and
backticks stripped; whitespace collapsed; lowercased), so a faithfully reworded
relocation passes while a dropped explanation does not.

It is not a plagiarism check — the default threshold of `0.72` is below 1.0 because
relocation legitimately rewrites lead-ins, but high enough that losing a sentence
fails.

Ignored as non-substantive: blank lines, headings, fence delimiters, table rules,
and anything under `--min-chars` (default 40).

### The containment asymmetry — the anti-tautology property

| Direction | Verdict | Why |
|-----------|---------|-----|
| `needle in candidate` | **full match** | The destination contains the whole removed line — a merge, not a loss. |
| `candidate in needle` | **not a match** | The destination holds only a *fragment* — the bare identifier survived and the reasoning did not. |

Getting this backward makes the gate tautological. It is pinned directly by
`ContainmentAsymmetryTest` and by
`test_identifiers_carried_but_prose_dropped_fails`.

### "Lost" means gone from both files

The haystack is the destination **and** the source as it stands at HEAD. An
in-place reword — keep the bullet in `AGENTS.md`, just rewrite it — appears in the
diff exactly like a relocation, and searching only the destination would report it
as content loss. Found by running the gate on its own PR.

### Known limitation: it is line-granular

A removed line whose content is **redistributed** across several destination lines
scores low and is reported, even though nothing was lost. This false-positive class
is left in deliberately:

- the gate is advisory, and *"this line's prose is no longer findable as a unit —
  check it"* is a useful thing to say;
- the fix would be union/coverage matching, where an arbitrary scatter of tokens
  can cover any needle — which is how this gate would decay into the token-level
  check it exists to replace.

For P3, the distinction matters little: relocation leaves the prose largely intact.
Compression-and-redistribution is a different operation, and a human should verify
it when flagged.

### Vacuous-pass resistance

Hard exit 2, never a pass, when the source or destination is absent at HEAD, a git
invocation fails, or `--expect-removals` was set and the diff removed nothing (the
check would otherwise have passed on empty input).

### Usage

```bash
python util/relocation_check.py --base origin/main --head HEAD \
    --source AGENTS.md --dest docs/REFERENCE.md
python util/relocation_check.py --advisory        # report, always exit 0
python util/relocation_check.py --expect-removals # refuse a vacuous pass
```

Exit **0** complete (or advisory) / **1** content lost / **2** misuse or broken
machinery.

---

## Resident-Hazard Gap Triage

The P5 cut gave every governed repo a resident `## Hazards` block. Three
ad-hoc tools ask complementary questions. Using only the first one is a
structural miss: it cannot surface a directive that was never in
`AGENTS.md`.

Fleet record:
[`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md`](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md).

### The three tools

| Tool | Reads | Question | Default print threshold |
|------|-------|----------|-------------------------|
| `util/ad-hoc/2026-08-28_hazard_triage.py` | `AGENTS.md` via `gh api` on **GitHub `main`** (not the local tree) | Which *already-resident* blocks look like hazards? | `--min-score 2` |
| `util/ad-hoc/2026-08-28_resident_gap_scan.py` | Local checkout, read-only | Which source comments are hazard-shaped and resident *nowhere*? | ranked by **identifier count**; `--max 30` |
| `util/ad-hoc/2026-08-31_resident_gap_triage.py` | Local checkout; loads the two siblings by path | Gap finding, scored with the four severity signals | `--min-score 3`, `--top 12` |

### Scoring

Four signals, one point each: **prohibition** / **silent-failure** /
**irreversible** / **hazard-noun**. Score the **block**, not a line and
not a 2-sentence window. A window-scored build put cascor's known-real
`max_epochs` / `output_epochs` split (`cascade_correlation.py:1927`) at
score 2 and buried it; block scoring puts it at 3, rank 1. The sentence
window survives only to pick the printed snippet.

`WARNING` / `CRITICAL` / `IMPORTANT` used as a **log level** lose the
`hazard-noun` point only. The demotion is recorded in `demoted`; nothing
is silently dropped. `--json` writes **every** scored row, including
those below `--min-score`.

Sort: score desc, then silence-marker present, then identifier count.

### Usage

```bash
# Already-resident ranking (needs `gh`; hits GitHub main)
python3 util/ad-hoc/2026-08-28_hazard_triage.py juniper-canopy --min-score 2

# Source-only gap list (local tree; ranks by identifier count, not danger)
python3 util/ad-hoc/2026-08-28_resident_gap_scan.py . --max 40

# Joined triage — the one to re-run after a cut
python3 util/ad-hoc/2026-08-31_resident_gap_triage.py \
    ../juniper-cascor ../juniper-canopy ../juniper-data \
    --min-score 3 --json /tmp/fleet_triage.json

# Positive control (cascor pre-#609 AGENTS.md)
git -C ../juniper-cascor show e1b4988c:AGENTS.md > /tmp/pre609.md
python3 util/ad-hoc/2026-08-31_resident_gap_triage.py \
    ../juniper-cascor --self-check --agents /tmp/pre609.md
```

A normal scan always exits **0** (including zero candidates).
`--self-check` exits **1** if `cascade_correlation.py:1927` is missing,
scores below 3, or ranks outside the top 5.

### The candidate count is not a health metric

Relocation moves facts *out* of `AGENTS.md`, so source identifiers that
used to have a resident counterpart no longer do. The gap predicate then
matches them. **Cutting widens the gap by construction.**

Recorded on the 2026-08-31 fleet pass (notes §3 / §7a / §8):

| Pass | Scored rows | What changed |
|------|------------:|--------------|
| First fleet pass | 285 | eight sibling repos; juniper-ml was the scanner, not a row |
| After the first promotions landed | 281 | each promotion removes itself — expected |
| Canopy after its cut | 90 (was 63 on 2026-08-28) | ten sections left `AGENTS.md`; the rise is correct |

The health signal is the **score ≥ 3 count** (and whether anything
*new* appears there), not the total. Re-run after every cut, not only
before.

### Operator pitfalls

| Symptom | Cause |
|---------|-------|
| Total went up after a successful relocation | Expected. Read score ≥ 3 / new rows, not the total. |
| Using `hazard_triage` alone | Can only rank text already in `AGENTS.md`. Both cascor promotions were invisible to it. |
| Trusting `resident_gap_scan` top rows | Identifier-count ranking. Fleet-wide first run: ~630 raw; tops were long docstrings. |
| Huge file / candidate counts on juniper-ml | Pre-[#1519](https://github.com/pcalnon/juniper-ml/pull/1519) the default glob walked in-repo worktrees. `SKIP_DIRS` now drops `.claude`, `worktrees`, `.venv`, and other copy trees. |
| `hazard_triage` ignores local edits | It fetches `repos/pcalnon/<repo>/contents/AGENTS.md?ref=main` via `gh api`. |
| Dual-tree repos (juniper-data) | Every hit appears twice (`juniper_data/` and `src/`). Halve before quoting. |
| Top score is noise | Fleet-highest was recurrence `bench/plots.py` at 4 — presentational. Human review; do not raise the threshold to hide it (that also drops `max_epochs`). |
| Promoting on severity alone | The residency test is whether **reading the code recovers the fact**. Adjacent rationale stays in the comment. |

Related: [Relocation Completeness (G3)](#relocation-completeness-g3),
[Memory File Size Budget](#memory-file-size-budget),
[`AGENTS.md` § Hazards](../AGENTS.md#hazards-resident--do-not-relocate).

---

## Test Suite Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

Two unittest entry points exist for every `tests/test_*.py` file, and they can disagree.

- `python3 tests/<file>.py` calls `unittest.main()` at the `if __name__ == "__main__"` block. Classes defined **after** that block are never collected.
- `python3 -m unittest …` (what AGENTS.md and CI use) imports the module fully first, so it sees every class.

Review catch on [juniper-ml#1612](https://github.com/pcalnon/juniper-ml/pull/1612): `ObservedContextAppsTest` was appended after the existing `__main__` block. Direct execution reported 8 tests; `-m unittest` reported 12. The two negative controls (exact-name near-miss; Bandit app `57789` must not publish `Memory Budget`) were the ones going missing — a green result from a runner that never loaded the cases. Keep `__main__` at EOF so both entry points agree.

- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`
- `tests/test_env_repr_safety.py` -- Lint + behavior gate for the env-repr secret-leak class: forbids raw `os.environ`-derived subprocess `env=` mappings in `tests/` (they leak secrets through pytest `--showlocals`-style frame-local reprs) and proves `tests/redacted_env.py`'s `RedactedEnv` masks its repr while behaving as a normal subprocess env mapping. Includes a synthetic-violation self-test; `patch.dict(os.environ, ...)` is deliberately exempt.
- Doc-link validator regression tests live in [`juniper-doc-tools/tests/`](juniper-doc-tools/tests/) (Wave 4 of the doc-link migration; exercised by the dedicated `CI -- juniper-doc-tools` workflow).
- `tests/test_worktree_cleanup.py` -- Tests for `util/worktree_cleanup.bash` argument parsing, dry-run, and error handling; Phase 1 dirty porcelain exit-1 gate (juniper-ml#747) and clean push / Phase 2 path-collision arms (open #753) drive fixture repos via sourced `phase_1_save_and_push` / `phase_2_create_new_worktree`
- `tests/test_worktree_sweep_scripts.py` -- Tests for `util/ad-hoc/worktree_sweep_*.bash`: survey/apply row compatibility, `SAFE`-only removal, and unknown-repo skips
- `tests/test_p5_worktree_cleanup.py` -- Hermetic gate for `util/ad-hoc/2026-08-28_p5_worktree_cleanup.py` (the sweeper that deletes trees; `#1632` pins only the independent in-use probe): `pr_state` empty/`null` → `NO-PR-ON-HEAD` and three `gh` failures → `LOOKUP-FAILED` (never conflated); `undisposable` treats `*.log` as disposable including nested `logs/system.log` but a `logs/` directory and `.h5` block; `occupied` is cwd-only and prefix-safe; `harvest` copies and does not delete the source. Fake `proc_root`; no live `/proc` or `gh`.
- `tests/test_cleanup_session_worktrees.py` -- Hermetic tests for `scripts/cleanup_session_worktrees.py`: `_has_merged_pr` fail-closed (gh fail / bad JSON), dirty/unmerged/detached keeps, self-cwd skip, and `--dry-run` remove of main-ancestor / MERGED-PR clean tips. `LockGateTest` pins the 2026-08-21 liveness gate against real locked worktrees: an otherwise-removable locked tree is kept, the `--dry-run` plan does not promise to remove it, unlocking the same tree makes it removable again (proving the lock is what held it), and an anti-resurrection arm asserts the source never passes `--force`/`-f` to `worktree remove`
- `tests/test_reap_pytest_orphans.py` -- Tests for `util/reap_pytest_orphans.bash` dry-run, live-parent safety, orphan detection, and isolated kill invocation
  - `TestLiveExperimentProtection`: the P1 pidfile + P2 cmdline keys, reproducing the three shapes a 2026-08-16 dry run would have killed (service/orchestrator/watchdog); the load-bearing live-mode arm proving a genuine orphan still dies while the protected service does not; stale-pidfile conservatism; and a malformed pidfile not aborting the sweep under `set -euo pipefail`
- `tests/test_soak_ledger.py` -- Gate for `util/soak_ledger.py` (pointer-follow soak). Pins seeded-vs-organic, Wilson-interval verdicts (never `BET-HOLDS`), fail-closed scope, escalations alongside the verdict, session-id collision, and `NO-DATA`/`DEGRADED` on a lost ledger. `util/` is outside pre-commit Python hooks, so this suite **is** the gate.
- `tests/test_soak_next_probe.py` -- Gate for `util/soak_next_probe.py`. Load-bearing **negative** property: stdout carries the task and nothing else (a leaked fact/pointer/discriminator primes the session and cannot be un-primed).
- `tests/test_soak_run_probe.py` -- Gate for `util/soak_run_probe.py`. Hermetic (never launches `claude`). Pins dry-run stdout leaking no task/fact/discriminator, and that a pointer miss is never reported as a scored miss (consistent with source-recovered **or** wrong).
- `tests/test_cascor_freeze_tell.py` -- **not on main** (open juniper-ml#1667). Pins exact-prefix + sibling/worktree exclusion, independent cmdline/environ/fd/maps arms, and `main()` exit 1 iff any hold. Operator surface: [Cascor Primary Freeze Tell](#cascor-primary-freeze-tell).
- `tests/test_kill_helpers.py` -- Hermetic process-filter / kill-path tests for `util/kill_all_pythons.bash` and `util/juniper_worker_kill.bash` (PATH-stubbed `ps`/`sudo`/`kill`; bash `kill` builtin disabled; never touches live PIDs)
- `tests/test_check_conda_env_torch.py` -- Hermetic exit-matrix tests for `util/check_conda_env_torch.bash` (P-5 torch._C shadow diagnostic: 0/1/2/3/4 via `JUNIPER_CONDA_DIR` + stub python; no real conda/torch). Operator surface: [Conda Env Torch Shadow Diagnostic](#conda-env-torch-shadow-diagnostic-p-5).
- `tests/test_requirements_drift_check.py` -- Tests for `util/requirements_drift_check.py`: structural range validation, BAD_PATH / BAD_RANGE classification, `--ecosystem-root` rewriting, CLI exit codes, JSON output
- `tests/test_requirements_consolidate.py` -- Live-tree gate for `util/requirements_consolidate.py` (v5 refresh). Pins byte-identical `render(parse(x))` on every shipped view, `--check-roundtrip` / `--check-views` agreement, Detail survival (ledger has no `detail`), derived-family projection of `by-area`, unique IDs, the official 11-entry `rec` block, incoming-only exact/fuzzy dedup, and `load_incoming` refusals. `util/` is outside every pre-commit Python hook, so this unittest is the gate.
- `tests/test_editable_install_drift_check.py` -- Tests for `util/editable_install_drift_check.py`: FRESH / WORKTREE_PINNED / ORPHANED classification, `*-DEPRECATED` env exclusion, `--env` filtering, dedup across interpreter trees, CLI exit codes (0/1/2), JSON output, and `--fix --dry-run` canonical-source resolution (synthetic conda-dir fixture; no real pip)
  - `VersionDriftTest` (version axis): static + dynamic version resolution (setuptools `attr` flat and `src/` layouts, hatch `path`), MATCH/STALE classification, orthogonality (a WORKTREE_PINNED install still gets a version verdict), STALE soft by default / hard under `--strict-version` with `--strict` unaffected, the summary+JSON version fields, and `--fix-stale` repairing in place (`drift: "stale-metadata"`, canonical == the recorded path) while ORPHANED repair still resolves canonically
  - Honesty pins in the same class: an undeclared `_version.py` is **never** guessed at (unrecognized backend → UNKNOWN, so no `STALE` can be manufactured from the wrong file), and an ORPHANED target is UNKNOWN rather than a fabricated comparison
  - Ambiguous canonical SKIP (open #795): two non-worktree checkouts with the same `[project].name` → `discover_canonical` returns `(None, [..])`; `--fix --dry-run` emits `action=SKIP` with `ambiguous` in `reason` (never re-points to `candidates[0]`).
  - Live `run_fix` (open #802): mocked `subprocess.run` covers `FIXED` on success, `ERROR` on `CalledProcessError`, and `ERROR` then `FIXED` when the first item raises `OSError` (plan continues).
- `tests/test_env_floor_drift_check.py` -- Tests for `util/env_floor_drift_check.py` (I-2): floor parsing (juniper-* `>=` bound; skips non-juniper/floorless/self-ref; dedup-highest), numeric version compare (`0.10.0 > 0.9.0`), OK/BELOW_FLOOR/MISSING classification, exit codes (0/1/2, `--strict`), `--json` -- via a synthetic site-packages fixture (no real pip/conda); also asserts no hardcoded env name. Sole gate (`util/` not lint-gated); real-env scan is manual-verify.
  - Open #796 adds `ResolveSiteDirsTest` (`--site-packages` wins, `--env` expand, ecosystem `used_by`, exit-2 reasons). Open #802 adds `InstalledVersionsTest` (highest-across-dirs, malformed/unreadable skip, underscore normalize).
- `tests/test_workflow_script_paths.py` -- Lint test: every `python <path.py>` / `bash <path.bash>` invocation in `.github/workflows/*.yml` must reference a path that exists in the repo. Cross-repo paths (`juniper-X/...`) are skipped as runtime-resolved. Catches the failure class that broke 3 juniper-X CIs on 2026-05-18.
- The sequence-safety screen unit tests (symbol + docs: `LOST`/`WEAKENED`/`DUPLICATED`, SF3 masking pin, relocation WARN, heading / `>=N`-run FAIL, both trailer escapes + wildcard, `--min-run`, the `--scope` glob engine, exit codes 0/1/2) moved to `juniper-ci-tools/tests/` with the package migration (rollout W3); they run under the dedicated `CI -- juniper-ci-tools` workflow. juniper-ml's `tests/test_ci_tools_drift.py` carries the anti-resurrection guard + the two new screen-pin drift checks.
- `tests/test_doc_tools_drift.py` -- Lint test (plan §5.1) for `juniper-doc-tools` pins. Extracts the `juniper-doc-tools>=X,<Y` pin from juniper-ml's own workflows and each cloned consumer repo's `ci.yml`, then asserts the range still admits the current version (read from `juniper-doc-tools/pyproject.toml`). Soft-warns on pins more than 2 minors behind; hard-fails when the upper bound excludes current.
- `tests/test_service_fork_drift.py` -- Drift gate for the security guards that must hold identically in `juniper-data`'s and `juniper-cascor`'s forks of the `juniper-service-core` middleware/security code (defect-register §2.3 "Copy drift").
  - A registry of named guards, each detected by a small source marker, rather than a file diff: the forks diverge legitimately and constantly (juniper-data deliberately holds API keys in a `list` for `compare_digest` timing where service-core uses a `set`), so a diff would drown the signal.
  - Two-sided by design. `ENFORCED` guards must be **present** in every fork; their disappearance is a regression. `KNOWN_GAP` guards must still be **absent** -- when someone closes one, the gate fails and instructs them to promote the row to `ENFORCED`, so the ledger cannot rot into a list of things that used to be true.
  - Cross-repo assertions gate exactly like `test_ci_tools_drift.py` (`GITHUB_ACTIONS=true` or `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`); the registry-structure checks and the matcher's negative controls always run. It bites in `docs-full-check.yml`, the only job that clones the siblings.
  - A site may be marked **`ordered`**, meaning its markers must appear in the declared sequence, not merely be present. `cors-outside-auth` (register `APD-CASCOR-001b` / `APD-DATA-035`) is the reason the flag exists: that guard regresses by two `add_middleware` calls **swapping places**, so both markers are present either way and a presence-only check would report SUCCESS on the exact defect it guards -- the vacuous-pass class. Requiring `RequestIdMiddleware` to be registered before `CORSMiddleware` *is* the invariant "CORS is registered last, so it runs outermost". Its negative controls are in the always-on structural class, so they still run in `ci.yml`, where the cross-repo arms are skipped.
  - **No `KNOWN_GAP` rows currently remain** -- all six copy-drift guards are `ENFORCED`. The `KNOWN_GAP` machinery is retained for the next row that acquires a reference implementation; note that with zero such rows `test_known_gaps_are_still_open_or_get_promoted` iterates an empty set and passes **vacuously**.
- `tests/test_assert_release_tag.py` -- Behavioral tests for `util/assert_release_tag.bash` plus a **wiring gate** asserting all 7 publishers invoke it with their own `--expect-prefix`, and that **no publisher grants `id-token` at workflow level** (P4).
  - Drives synthetic dist directories: happy paths (meta, sub-package, `-rc1` normalization, alpha), and the refusals that matter -- branch ref, **empty** ref_type (must fail closed, not read as a tag), tag/version mismatch, wrong package prefix, missing dist dir, sdist-only, version-less tag, misuse exit 2.
  - The mismatch case is a live regression guard: it originally passed because `tr -d '-_'` errored on this host and both sides normalized to empty. `util/` is outside every pre-commit Python hook's scope, so this suite is the gate.
- `tests/test_publish_testpypi_verify.py` -- Structural + hermetic YAML-extraction gate for `.github/workflows/publish.yml` TestPyPI **Gate 1**.
  Pins the two-phase verify (TestPyPI-only `pip download --no-deps` provenance, then three PyPI-only local-wheel installs of bare / `[clients]` / `[tools]`, never `--extra-index-url`, never the heavy extras), the `v*` tag guard, TestPyPI `skip-existing` vs strict PyPI, and `pypi needs: testpypi`.
  Since juniper-ml#1310, the index-lag buffer is a **bounded poll** (no unconditional `sleep 30`; remaining `sleep` values are poll intervals `<=10s`; exhausting the loop is a real `::error::`, not a silent fall-through).
  The extracted verify shell is rehearsed with PATH stubs so a rewrite that drops a phase fails in CI without hitting the network.
- `tests/test_publish_release_only_trigger.py` -- Glob-discovered gate that `release: published` stays the **only** automatic trigger on every `publish*.yml` (juniper-ml#1310).
  Re-adding `push:` recreates the #555 double-publish race against the immutable TestPyPI upload; removing `release:` disarms publishing silently (a workflow that never fires reports nothing).
  Also pins that no step is gated on `github.event_name == 'push'` — the six sub-package publishers used to carry an unreachable `Require a GitHub Release for this tag` step under that condition.
  `workflow_dispatch` stays as the deliberate escape hatch.
- `tests/test_publish_env_policy_drift.py` -- Drift gate for the **tag-only deployment ref policy** on every `pypi` / `testpypi` environment ([publish-path design](../notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md) §6 Option A / §12.5).
  - The control lives in GitHub **settings, not the repo**: no test covered it, no reviewer sees a diff when a policy is deleted, and the failure is silent -- the publish path just becomes permissive again.
  - Two load-bearing invariants: **no branch-type policy may exist** (adding a `main` branch policy re-opens branch dispatch while every tag pattern stays intact and the environment still looks configured -- owner decision D3 was tag-only), and **`pypi` must retain `required_reviewers`** (a `PUT` is create-or-update, so a careless payload clears the human gate while successfully setting a ref policy -- the environment then looks *more* configured while being weaker).
  - Structural checks + the detector's **negative control** always run offline (a gate that cannot fail is not a gate; an untyped policy must read as `branch`, never `tag`). The live half is gated on `GITHUB_ACTIONS=true` / `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` and is read-only (`gh api` GETs).
  - **No silent caps**: per-PR CI's built-in `GITHUB_TOKEN` reaches juniper-ml only, so the live half partitions the registry repos into readable/unreadable, verifies the readable ones, **names** the unverified ones, and refuses to pass if nothing at all was readable. A repo that IS readable but whose environment 404s is a real finding (deleted environment), not a permission skip. Full-fleet cover: `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`.
  - Repair: `util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> <env>`.
- `tests/test_pyproject_extras.py` -- Lint test pinning the `[project.optional-dependencies]` surface (`clients`, `worker`, `servers`, `tools`, `doc-tools`, `all`). Asserts the exact set of extras, the exact membership of each, that `[all]` aggregates every non-alias extra exactly once, and that `[project].version` is semver-ish. Added pre-0.5.0 after juniper-ml#295 introduced `[servers]` + `[tools]` without regression coverage; any future edit to extras must update the lint contract in the same PR.
  - juniper-ml's own pin check runs every PR; the cross-repo assertion auto-skips when siblings aren't on disk and additionally skips local runs by default. Set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to opt in locally.
- `tests/test_template_library_drift.py` -- Lint test enforcing manifest <-> template consistency for the custom-agent template library (`prompts/agent_templates/`): every registered template exists, and every template is registered; each follows the canonical section skeleton in order; every `{{placeholder}}` matches the systematic convention; the `generic` fallback always matches.
  - The **sole gate** for the library because `prompts/**` is excluded from all pre-commit hooks, so it must stay wired into `ci.yml`. Design-of-record §5.4/§9.
- `tests/test_template_selection.py` -- Lint validating `manifest.yaml`'s `match_signals` support deterministic category selection: exactly one always-match fallback (`generic`), every other template has non-empty keyword signals, no two share an identical keyword set, and every `class` is allowed. Companion gate to the library drift test.
- `tests/test_template_select_preview.py` -- Tests for `util/template_select_preview.py` (the offline selection preview, P2): drives the real manifest (so it also guards selection drift) -- a task with a template's keyword selects that template (`failing-tests`), a no-keyword task falls back to `generic`, the ranked candidates exclude the always-match fallback, and the CLI exits 0 with the documented JSON shape.
- `tests/test_template_data_resolver.py` -- Tests + drift gate for the custom-agent suite data layer (PR 6b): the five `prompts/agent_templates/data/*.yaml` files load, `util/template_data_resolver.py`'s `load`/`resolve` (dotted lookup) work, and -- since `prompts/**` is pre-commit-excluded -- this is the sole gate; also asserts `conventions.line_length` matches `.markdownlint.yaml` and the handoff threshold is the current 95-99% (not a stale 80%).
- `tests/test_safe_merge.py` -- Tests for `util/safe_merge.py` (the R4 merge gate). Hermetic: `_gh`, `pr_state`, `wait_for_required` and `update_branch` are replaced with recorders, so no network / `gh` / repo / PR is touched.
  Pins the safety contract -- every refusal path (closed / draft / conflicted / checks-failed / checks-unfinished / unsettled-ref / sync-cycles-exhausted / merge-returned-but-PR-not-merged) asserts that **no** `pr merge` was issued, plus `--match-head-commit` head pinning, the server-side (`PUT`) branch refresh, the async ref-settle poll, moved-head-is-a-refusal, the no-local-git invariant, and dry-run writing nothing.
- `tests/test_open_signed_pr.py` -- Tests for `util/open_signed_pr.py` (signed cross-repo PR opener). Hermetic: `gh` is a PATH stub that records argv and replays canned stdout, so no network/repo/`git` is touched.
  - Pins the mutation name (`createCommitOnBranch` -- the whole point), `expectedHeadOid` == the resolved base SHA, base64 additions, `fileChanges.deletions` present for `--delete` and **omitted** when unused, and the explicit `ref=refs/heads/<branch>` on the refs POST (the ml#770 R7 lesson).
  - Also pins every refusal path writing nothing: dup-guard exit 1, existing-branch exit 1, no-changes exit 2, unreadable source exit 2. `util/` is outside every pre-commit Python hook's scope, so this suite is the gate.
- `tests/test_scaffold_template.py` -- Tests for `util/scaffold_template.py` (P5 generator): the generated template passes the real library-drift helpers (skeleton order + placeholder well-formedness), `--dry-run` writes nothing, refuse-on-collision (exit 1), bad-class / missing-keywords (exit 2), and -- the safety contract -- the tool NEVER edits `manifest.yaml` (prints the stanza).
- `tests/test_prompt_validator_contract.py` -- Static contract test for the `prompt-validator` subagent (`.claude/agents/prompt-validator.md`, PR 3): frontmatter shape (`tools` = exactly `Read, Grep, Glob, Bash`, `model` concretely pinned per OQ-4), every rubric ID it cites exists in `RUBRIC.md` (incl. the `R2.0`/`R3.4` hard gates), and the pinned verdict schema + PASS/FAIL samples in `tests/fixtures/prompt_validator/` match the §5.3 contract. E-3: re-probe block is `<target>`-qualified (not CWD).
- `tests/test_prompt_discovery.py` -- Behavioural tests for `util/prompt_discovery/` (custom-agent suite PR 4): the grounding-bundle schema + provenance envelope emitted by `cli.py`, per-probe graceful degradation, the hard-stop on a non-git root (exit 2), the `test_status` `cold_cache`/empty distinction, plus E-3 `--target-repo` cross-repo grounding. `util/` is not pre-commit-lint-gated (flake8/black scope to `scripts`+`tests`), so this unittest is the gate; imported via the `sys.path.insert` idiom.
- `tests/test_symbol_overlay.py` -- Tests for `util/prompt_discovery/symbol_overlay.py` (the Serena symbol overlay, design OQ-8): the deterministic merge of Skill-resolved Serena facts into a bundle's `symbol_probe` slice -- Serena-resolved wins, grep is the fallback, an unresolvable symbol stays `UNRESOLVED`, the input bundle is not mutated, and `cli.py`'s contract is untouched. Stdlib only; importlib-loaded.
- `tests/test_predict_merge.py` -- Hermetic tests for `util/fleet_triage/predict_merge.py` (Stage-0 supervisor script layer): bare-origin + branch fixtures drive the four verdicts (symbol-loss / docs-deletion / injected gate-fail DAMAGED, plus MERGE-CLEAN / NEEDS-UPDATE-BRANCH / CONFLICT), TRUE-delta-vs-stale-file-list discrimination, `--batch` cluster map + order (fake `gh`), detached-clone-never-mutates-source, CLI exit codes.
  - Also covers docs-screen edges (header ignore / additions-only / non-`.md`), no-`.py` gate skip, and `repair`/`fix-first` heal tokens (juniper-ml#910). `util/` not lint-gated so this is the gate; `sys.path.insert` + `RedactedEnv`.
- `tests/test_fleet_supervisor_contract.py` -- Static contract for the `fleet-supervisor` subagent (`.claude/agents/fleet-supervisor.md`, flood §4 item 7): frontmatter (`tools` == exactly `{Read,Grep,Glob,Bash}`, `model` opus + `effort` max, name == stem) and body wiring -- references `util/fleet_triage/predict_merge.py`, documents all four verdict tokens, states the read-only / never-push mandate + the two-key DUP-CLOSE rule (overlap AND owner confirmation). Modeled on `test_prompt_validator_contract.py`.
- `tests/test_generated_prompt_index.py` -- Tests for `util/generated_prompt_index.py` (P4): name-convention parsing, `.gitkeep`/malformed ignored, and the destructive-path safety -- `--prune`/`--archive` without `--yes` (or under `--dry-run`) delete/move nothing, `--prune --yes` / `--archive DIR --yes` act only on convention-named stale files (never `.gitkeep`/hand-placed), and the generated-dir location is read from `conventions.yaml`.
- `tests/test_thread_handoff_archive.py` -- Drift guard for `prompts/thread-handoff_automated-prompts/`: every archived handoff prompt filename must follow `HANDOFF_YYYY-MM-DD_subject.md` with ASCII subject text, and top-level `notes/*.md` references to archived handoff prompts must resolve to real files. Added after PR #617 standardized old `handoff_subject_YYYY-MM-DD.md` archive names.
- `tests/test_install_agents.py` -- Tests for `util/install_agents.bash` (custom-agent suite PR 6a): drives the `~/.claude` mirror against a synthetic source repo + throwaway target (`JUNIPER_ML_REPO_ROOT`/`JUNIPER_CLAUDE_HOME` overrides) and asserts it is idempotent, reversible (`--reverse`), `--dry-run`-safe, and never clobbers or removes a file it does not own.
- `tests/test_agent_suite_doctor.py` -- Tests for `util/agent_suite_doctor.py` (the suite health-check dogfood utility): the real suite has zero FAIL; synthetic trees missing a component FAIL the matching check (exit 1); `--json` shape; `--no-discovery` skips the subprocess; `--strict` promotes WARN to exit 1; a non-repo `--repo-root` exits 2. Stdlib-only; importlib-loaded.
  - `DoctorDiscoveryCheckTest` (juniper-ml#825): pins discovery fail-closed arms (missing CLI / nonzero exit / invalid JSON / missing schema or provenance / well-formed OK) via hermetic fake `cli.py`.
- `tests/test_agent_suite_summary.py` -- Tests for `util/agent_suite_summary.py` (P3 quick-reference): drives the real suite so every agent and template appears, `--json` round-trips, and `--markdown` rows respect the 512-char line-length convention. Stdlib + PyYAML; importlib-loaded.
- `tests/test_template_agent_skill_lint.py` -- Static lint for the `template-agent` Skill (`.claude/skills/template-agent/SKILL.md`, PR 5): frontmatter (`allowed-tools` includes `Agent`, `model: opus` + `effort: max`, user-only) and that the bounded state machine wires to real artifacts (template library, `RUBRIC.md`, `util/prompt_discovery/cli.py`, the emission dir, the `prompt-validator` subagent). E-3: threads `<target>` to the validator. The Skill-surface gate (pre-commit-excluded except markdownlint).
- `tests/test_service_smoke_skill_lint.py` -- Static lint for the `service-smoke` Skill (`.claude/skills/service-smoke/SKILL.md`, E-1 Stage 1/2): the **Stage-2 boundary** -- a browser MCP (`mcp__playwright`) MUST be declared for the opt-in `--ui` smoke (inverts Stage 1's no-browser rule), `Agent` still forbidden -- plus `opus`+`max`/user-only frontmatter, browser-close teardown, the `--ui`/`/dashboard`/console smoke, `UI_UNHEALTHY_REPORTED`, and bounded waits. Structural-only gate.
- `tests/test_ui_test_author_skill_lint.py` -- Static lint for the `ui-test-author` Skill (E-6): frontmatter (suite `opus`+`max`, user-only, `Write` + a declared browser MCP, NO `Agent`) + that it models canopy's `src/tests/ui/` harness (`dashboard_page` / `@pytest.mark.ui` / the `dbc.Input` wall via `/api/state`), the browser-close teardown, the reviewed-never-auto-merged contract, terminal states, and bounded waits. Structural-only gate; live authoring = manual smoke-verify.
- `tests/test_agents_frontmatter.py` -- Suite-wide frontmatter gate over every `.claude/agents/*.md` (the `prompt-validator` plus the round-2 `planner` / `auditor` / `task-executor`): `name` equals the filename, the `description` is substantive, `tools` are declared, the body is non-trivial, and the owner-directed defaults `model: opus` + `effort: max` hold -- so a new agent cannot drift from the standing defaults. The shared invariant complementing `test_prompt_validator_contract.py`.
- `tests/test_ci_tools_drift.py` -- Lint test (dep-docs plan §5.1) for `juniper-ci-tools` pins. Mirrors `test_doc_tools_drift.py`: walks juniper-ml's own workflows (`ci.yml`, `main-verify.yml`, `lockfile-update.yml`, `docs-full-check.yml`) plus each cloned consumer repo's `ci.yml`, extracts the `juniper-ci-tools>=X,<Y` pin, and asserts the range still admits current (read from `juniper-ci-tools/pyproject.toml`). Same skip semantics + `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` override as the doc-tools sibling.
  - Also carries the **sequence-safety anti-resurrection gate** (rollout W3 / plan §W3 step 3.3): `SequenceSafetyPackageMigrationTest` asserts juniper-ml's tree has no resurrected inline `util/sequence_safety/` copy or the two moved screen tests (a synthetic-fixture negative proves it bites); `main-verify.yml` in the scanned workflows enforces the two new `>=0.8.0,<0.9.0` screen pins still admit current.
- `tests/test_ruleset_scope_guard.py` -- Hermetic gate for `util/ruleset_scope_guard.py` (`util/` is outside every pre-commit Python hook).
  - `~DEFAULT_BRANCH` passes; `~ALL` fails naming the ruleset and the `29110` rows it re-arms; one-wide-among-narrow still fails.
  - Empty ruleset list exits 2 (not clean); a failed probe exits 2 not 0; `_get` retries then recovers; `getter` is call-time so tests can patch it.
  - Source must not read `bypass_actors` (redacted unauthenticated). `FleetListDriftTest` pins `FLEET` to the release-train registry publishers plus `juniper-deploy`.
  - Operator surface: [Ruleset Scope Guard](#ruleset-scope-guard).
- `tests/test_coverage_gap_mapper_drift.py` -- Dogfood/drift gate (E-4 + C-0) for the `juniper-coverage-gap-map` console script in `juniper-ci-tools` (modeled on `test_ci_tools_drift.py`). STRUCTURAL: script registered, `_version.py` matches version, pins admit it, `--enforce`/`--fail-under-*`/`--omit` wired. END-TO-END (C-0): `--enforce` exits 1 on a gap / 0 clean over a synthetic `coverage.json`. Full matrix in `juniper-ci-tools/tests/`.
- `tests/test_env_drift_check_drift.py` -- Structural drift gate for the `juniper-env-drift-check` console script (env floor-drift guard, test-suite audit §10.1).
  - Mirrors `test_coverage_gap_mapper_drift.py`: asserts the entry point is registered (`juniper_ci_tools.cli_env_drift_check:main`), both module halves ship, version/pin coherence, **plus a class guard** that *every* `juniper_ci_tools/cli*.py` has a `[project.scripts]` entry.
  - Added in `juniper-ci-tools` 0.5.1 after #580 silently dropped the 0.5.0 entry point -- the always-on assertion the `python -m` behavioural dogfood (`tests/test_env_drift_check.py`) lacked.
- `tests/test_release_train_registry.py` -- Structural lint + registry<->pyproject drift gate for `util/release_train/registry.yaml` (plan §4.1): always-on checks (18 packages, 8 repos incl. `juniper-recurrence`, required fields, enums, the dynamic-version set, archive-name convention, `depends_on`) plus resolution -- the 7 in-repo juniper-ml packages unconditionally (forward + reverse), the 11 cross-repo entries via the `test_doc_tools_drift.py` sibling auto-skip.
  - Also home of the always-on `VersionDunderLockstepTest` (ml#701): every in-repo static-version package with a `_version.py` must keep `[project].version` == `__version__` (dynamic packages exempt -- their dunder IS the source); the ci-tools 0.7.0 / service-core 0.5.0 stale-dunder class.
- `tests/test_release_train_detect.py` -- Hermetic tests for `util/release_train/detect.py` (plan §4.2/4.3); no network / gh / pip (sources injected). Covers each classification, static/dynamic version reads, tag resolution, the substantive-hunk filter (discount comment/docstring/link; catch real code), path-scoping (subdir vs cascor repo-minus-subpkgs), CHANGELOG conflict surfacing, SemVer, manifest JSON shape, and exit codes 0/1/2. `util/` is not lint-gated, so this unittest is the gate.
  - Soft-fail pins: truncated-without-ship / unreadable-declared / compare-not-ok → `SHIP_UNCERTAIN` (juniper-ml#763); hygiene `SourceError` → `tag_only=None` (juniper-ml#761); offline `list_releases` raise (open #773).
- `tests/test_release_train_propose.py` -- Hermetic tests for `util/release_train/propose.py` + `notes_render.py` (Phase 2.1); no network / gh / repo writes. Covers a dry-run proposal for a static- and a dynamic-version package, the CHANGELOG move, notes render vs the template skeleton + the `RELEASE_NOTES_<pkg>_v<version>.md` convention, dup-guard suppression, the `changelog_conflict` refusal, and that a dry-run writes nothing. `util/` is not lint-gated, so this is the gate.
  - ml#701 dunder-lockstep shapes: static-with-dunder bumps BOTH files; static-without-dunder emits no phantom `_version.py` edit; the dynamic path is unchanged; a present-but-unparseable dunder is flagged REQUIRED-manual in the checklist.
  - Sibling/meta AGENTS.md shapes (ml#706 / #720): primary co-change; sub-package host skip; unexpected header REQUIRED; already-at-target silent; absent / missing-Version REQUIRED.
  - notes_render meta/MAJOR/Breaking/`*` bullets: juniper-ml#756.
- `tests/test_release_train_archive_guard.py` -- Hermetic tests for `archive_guard.py` (Phase 3.1, §7.2); no network/git/gh. Drives the four-rule classifier with synthetic `git diff --name-status` sets + the CLI (`--name-status-file`) against the real `registry.yaml`: a pure notes-add PASSES, a non-archive PR SKIPs, and modify/delete/out-of-path/bad-name/mixed diffs each FAIL; plus filename convention, parsing, exit codes 0/1/2. The gate for `util/`.
- `tests/test_release_train_ceremony.py` -- Hermetic tests for `ceremony.py` (Phase 3.2, plan §7/§8/§9.3); no network/gh/git/writes.
  Covers every §8 precondition HALT (main-CI / anomaly / missing-CHANGELOG / notes-render-failed / TestPyPI-verify), execute `RELEASED` when both publish gates are completed, the happy-path exact action sequence, dup-guard/idempotent re-entry, the R7 gh-surface invariant (live seam issues only the allowlisted verbs + the 2 archive api calls -- `git/refs` POST + `createCommitOnBranch`), and a dry-run leaving `git status` clean. The gate for `util/`.
  - Execute-time open-PR reuse + archive-already-on-main idempotent re-entry arms (juniper-ml#730).
  - R7 archive-lane `ref=` required (juniper-ml#770): missing/empty `ref=` on a `git/refs` POST is `SeamViolation` (not deferred to the live API).
- `tests/test_agents_md_version_drift.py` -- Lint test pinning `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s `[project].version`. Added after juniper-ml#295 bumped pyproject 0.4.1→0.5.0 but left AGENTS.md at 0.4.0 for ~6 days (fixed in juniper-ml#304); this lint makes the drift impossible to ship. Intentionally portable: auto-locates the repo root, so the module can be dropped into any Juniper repo's `tests/` (skips loudly if AGENTS.md has no canonical header).
- `tests/test_agents_md_header_schema.py` -- Lint pinning `AGENTS.md`'s canonical header schema. Six required fields in this relative order: `**Project**`, `**Repository**`, `**Author**`, `**License**`, `**Version**`, `**Last Updated**`. Extras (e.g. `**Python**:`) may be interleaved freely. Validates each value as non-empty and `**Last Updated**` is `YYYY-MM-DD`. Currency of the date is enforced by `.github/workflows/agents-md-touch-up.yml`. Portable (self-locating).
- `tests/test_agents_md_tree_drift.py` -- Lint (gap G-3) asserting every tracked non-hidden top-level dir (`git ls-tree`; the `ls -d */` surface) appears as a node in `AGENTS.md`'s fenced Repository-Structure tree, catching the indented-tree omission the grep-based `test_agent_suite_path_drift.py` cannot (stale `templates/`, missing `conf/`/`papers/` + 6 sub-package dirs). Portable; a synthetic negative case proves it bites.
- `tests/test_isolated_stack_script.py` -- Contract tests for `util/isolated_stack.bash` (plan unit E1): `bash -n` syntax, launch-line text assertions (dedicated-venv install, `python -m juniper_data`, `uvicorn api.app:create_app --factory`, canonical canopy env vars, the control-WS origin/allowlist pair), and hermetic `--dry-run` behavioural checks (prints commands with ports expanded, touches nothing; misuse exits 2).
- `tests/test_experiment_stack_script.py` -- Contract + behavioural tests for `util/experiment_stack.bash` (CLI experimentation plan Wave 2.1; `util/` is not
  pre-commit-lint-gated, so this unittest is the gate): `bash -n` syntax, the CLI misuse matrix (exit 2), the §9.3 port ranges and §6.4 RUN_DIR contract, the §6.1 launch
  recipes env-set by env-set (incl. the APD-DATA-018 pin that `data_up` does **not** set `JUNIPER_DATA_IMPORT_DIR` / `CSV_IMPORT_MAX_BYTES` / `CSV_IMPORT_ALLOW_TRUNCATION` — operators export them; the child inherits), the **F-6** listener-pid rule (no `$!` in any `*_up`; `record_listener_pid` runs after `wait_for_health`; teardown verifies uid + cmdline),
  §7.3 suffix-based `_monitoring$` gateway discovery + the exact socat relay line, the §7.2 target file rendered and parsed as JSON (four labels), and the operator-safety
  invariants (no `JuniperProject.pid`, no canopy, no repo `.env` write, no operator port).
  - Behavioral arms are hermetic: `JUNIPER_EXP_{RUN,LOCK}_ROOT` / `_DEPLOY_DIR` / `_CONDA_DIR` redirect every path into a tempdir and `ss`/`curl`/`docker`/`socat` are PATH
    stubs -- `--dry-run --up` prints all three launch classes with allocated ports expanded while leaving run root/lock root/targets dir non-existent; `allocate_port`
    skips locked and bound ports and fails loudly on an exhausted range; `--down` kills a self-spawned detached child through the **pidfile** path (the stubbed `ss` reports
    no listener, so kill-by-port cannot be what fired), removes the target file, releases the lockdirs, writes `teardown.json`, and preserves `artifacts/`.
  Live `cascor_up` / `canopy_up` compose pins (`TestCascorUp` / `TestCanopyUp` — fake `conda.sh` + PATH stubs; juniper-ml#813). Wired into `ci.yml` beside the `test_juniper_{plant,chop}_all.py` launcher tests.
  - Live compose coverage for `data_up` (`TestDataUpLive`: venv create/skip, pip extras, `PYTHON_GIL=0`, pidfile, missing-`python3.14` abort — juniper-ml#807).
- `tests/test_snapshot_index.py` -- Hermetic tests for `util/snapshot_index.py` (design §6.2). Pins bytes-attr decode, append-only rescan, `--limit` deferred-vs-present counting, D-C provenance filters, the query-time `dataset_id` join, and an AST read-only guard. Operator surface: [Snapshot Sidecar Chain](#snapshot-sidecar-chain).
- `tests/test_snapshot_classify.py` -- Hermetic tests for `util/snapshot_classify.py` (handoff 2026-08-22 §2.4). Pins the two-axis category/health rule (attributed zero-node is category 5, not empty), `readable`-is-not-loadable, iterations-not-epochs, replace-not-append sidecar, `--write`/`--from-sidecar` refusals, and the train-stage scratch-root + unimplemented exits. Operator surface: [Snapshot Sidecar Chain](#snapshot-sidecar-chain).
- `tests/test_snapshot_backfill.py` -- Hermetic tests for `util/snapshot_backfill.py` (handoff §3.4). Pins the four derivation levels, the `380/380` of `15927` trainability claim staying in `population`, never-invented run identity, both format-attribute spellings mapping to cohort B, and an AST read-only guard. Operator surface: [Snapshot Sidecar Chain](#snapshot-sidecar-chain).
- `tests/test_snapshot_attribute.py` -- Hermetic tests for `util/snapshot_attribute.py` (handoff §3.2). Pins permutation-corrected scoring, the untrained floor as the null's **maximum** (not p95), the schema-v2 cross-dataset floor, `--write` refusals for `--sample`/`--min-hidden`, and an AST read-only guard.
  - `DatasetInstanceIsFixedTest` (juniper-ml#1333): a generator declaring `seed=None` is given `DATASET_SEED`; a declared seed (spiral) is kept; two calls with the same seed agree; a params class with **no** `seed` field is left untouched; `DATASET_SEED` is a constant, not a drifting default. Stand-ins — no cascor tree, no juniper-data tree, no archive. Operator surface: [Snapshot Attribution Dataset Pin](#snapshot-attribution-dataset-pin).
- `tests/test_read_run_metrics.py` -- Hermetic tests for `util/experiments/read_run_metrics.py` (P2 item 0.4): last-row `step_count` / `step_sum`, scrape tri-state, `work_invariant` over **measured** cells only (`summarise` drops `None`), fingerprint strips `description`/`name`, recurrence `work_countable: False`. Operator surface: [Perf-Lane Work Gate](#perf-lane-work-gate).
- `tests/test_make_baseline.py` -- Hermetic tests for `util/experiments/make_baseline.py` (P2 item 1.1): no `--force`; refuses broken work invariant / unmeasured / failed / mixed-workload / not-countable; `--accept-warnings` is recorded. Operator surface: [Perf-Lane Work Gate](#perf-lane-work-gate).
- `tests/test_compare_baseline.py` -- Hermetic tests for `util/experiments/compare_baseline.py` (P2 item 1.2): exact work, ungated speed, identity-first REFUSE, host blocking vs advisory, WAIVED ≠ PASS, 0/1/2 stay distinct, and the A1-A7 refusal ladder (unmeasured / not-succeeded / zero-work / FAIL-over-REFUSED precedence / partial coverage / duplicate fingerprints) closed by ml#1741 + ml#1743. Operator surface: [Perf-Lane Work Gate](#perf-lane-work-gate).
- `tests/test_run_experiment.py` -- Hermetic tests for `util/experiments/run_experiment.py` (CLI experimentation plan Waves 2.2-2.6: the cascor + recurrence service paths, the §8.1 + §8.2 plot sets, and the §8.3 stats/summary renderers (e2e stats assertions for both kinds + every-outcome coverage + the `StatsSummaryUnitTest` percentile/delta/grouping/degraded-notes units) --
  Operator facts for those units (per-poll `p50`, sequence `n_windows`, data-driven `theta`): [Experiment Stats Summary](#experiment-stats-summary-ss83).
  plot arms cover all-rendered PNGs for both kinds (sequence-NPZ stub artifact for §8.2), per-kind plot-name validation, skip-vs-acceptance semantics (eval-disabled / degraded-sampling / disabled-phase skips, matplotlib-unavailable failure), and the `plots_cascor.py` / `plots_recurrence.py` renderer units incl. the `y_reg_` target-key preference;
  `util/` is not pre-commit-lint-gated, so this unittest is the gate. A scripted stub HTTP server stands in for juniper-data, cascor, and recurrence (no live services): the
  §5.6 YAML validation arms (unknown block/key, `schema_version`, mandatory `experiment.seed`, the rule-6 infra-key rejection, kind resolution, the §5.5 recurrence blocks
  incl. `dataset.split` / `crossval.n_folds` / `predict.from_dataset_split`), the cascor drive loop (completion / `FAILED` / Q-2 stall/wall-clock budget with
  CLI-beats-YAML precedence), the F-1 `/metrics` 307-redirect sampling arm + the G-3 404 degrade, the G-6 staging path (alias map, no inline `dataset` on start,
  shape-assert pass/mismatch, unstageable-generator refusal), the recurrence path (synchronous train 200/409/422/socket-timeout arms, predict/crossval `dataset_id` refs +
  record-and-continue on failure, the G-18 `save_model` CLI re-run via a PATH stub + missing-CLI acceptance failure), `ports.json` endpoint resolution, the §13.4 manifest
  written for every outcome, and the full 0/1/2/3/4 exit matrix incl. `RedactedEnv` subprocess arms.
  csv_import operator surface (APD-DATA-018, the half that lives in this repo): `create_dataset` 422 is `ConfigError` / exit 2 on both the recurrence and cascor paths (create runs *before* staging; a 500 stays `RunFailed`); csv_import is registered-available on the stub but not in `STAGEABLE_GENERATOR_ALIASES`, so a successful create still cannot stage (the arc_agi-only unstageable arm is a false green if csv_import is added to the alias map).
- `tests/test_read_run_metrics.py` -- Hermetic tests for `util/experiments/read_run_metrics.py` (P2 item 0.4): last-row `step_count`, scrape tri-state (`None` is not `False`), `work_invariant` negative control. juniper-ml#1613 adds `WorkloadFingerprintTest` (cosmetic `description`/`name` ignored, `seed` is not, missing YAML is `None` not a shared identity, `single_workload` false when identities are unknown). `util/` is outside pre-commit Python hooks, so this unittest is the gate.
- `tests/test_make_baseline.py` -- Hermetic tests for `util/experiments/make_baseline.py` (P2 item 1.1): no `--force`, refuse broken work invariant / failed / unmeasured / `validation_warnings` (override recorded), `HOST.json` python-mismatch caveat. juniper-ml#1613 adds mixed-workload refusal + fingerprint recording. Operator surface: [Perf-lane metrics and baselines](#perf-lane-metrics-and-baselines).
- `tests/test_compare_baseline.py` -- Hermetic gate for `util/experiments/compare_baseline.py` (P2 item 1.2, ships in juniper-ml#1622).
  Pins the three outcomes staying distinct: PASS/FAIL on the exactly-compared work half (**exit 1**, not merely non-zero), REFUSED on identity or host mismatch (exit 2), WAIVED never collapsing into PASS.
  Also pins that SPEED cannot fail the gate at any magnitude (a 10× slowdown with matching work still PASSes), that a one-step `step_count` difference is enough, that a waiver cannot override a refusal, that a whitespace-only `--accept-work-change` is not a reason, and that the renderer does not claim a waiver that had no effect.
  `util/` is outside pre-commit Python hooks, so this unittest **is** the gate. Operator surface: [Perf-Lane Split Comparator](#perf-lane-split-comparator).
- `tests/test_list_runs.py` -- Hermetic tests for `util/experiments/list_runs.py` (Wave 7.2). Pins convention-name recognition, `down` / `stale` / `up?` classification (including a dead pid with a recorded cmdline → `stale`), cell enumeration, `--older-than` JSON filtering, and the prune safety contract: `--prune` without `--yes` (or under `--dry-run`) removes nothing; a live recorded pid is never pruned. Synthetic `RUN_ROOT` only. Operator surface: [Run lister / pruner](#run-lister--pruner-list_runspy).
- `tests/test_experiment_config_schemas.py` -- Wave 3.5 drift gate (§10.6 row 3): walks the sibling checkouts' `conf/experiments/*.yaml` (cascor Wave 3.2, recurrence Wave 3.4) and asserts each loads through the driver's §5.6 `load_config` AND that every `service:` key names a real app `Settings` field --
  extracted statically via AST (cascor `Settings`; recurrence `Settings` + the in-repo service-core `SettingsBase`), so no torch-heavy app import is needed. Cross-repo walk gated like `test_doc_tools_drift.py` (`GITHUB_ACTIONS=true` or `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`; sibling-absent skips loudly); the AST-extractor self-check always runs.
- `tests/test_experiment_suite_yamls.py` -- Drift gate (R-6) over the shipped suites in `util/experiments/suites/**`: `load_suite` plus oversize-stall / wall-pin / timeout-ordering. Operator surface: [P4 Campaign Suites](#p4-campaign-suites).
- `tests/test_run_suite.py` -- Behavioral suite-driver coverage, including P2 item 1.4 (`GateInputsInAggregateTest` / `ComparisonReportingTest`): `aggregate.csv` must carry both gate inputs beside `wall_seconds`; `REPORT.md` must say `wall_seconds` is DE-RATIFIED and print work-invariant / single-workload; `--compare-baseline` is reporting-only (missing tag and FAIL verdict still exit 0). Operator surface: [Suite Report Gate Inputs](#suite-report-gate-inputs).
- `tests/test_experiment_suite_yamls.py` -- Drift gate (R-6) over the shipped suites in `util/experiments/suites/**`, which no test loaded before it: every suite must pass `run_suite.load_suite` (catching the unknown-`execution:`-key / `stall_second` typo class that otherwise surfaces hours into a GPU campaign), and any oversize `app: cascor` suite must declare an `execution.stall_seconds` above the driver's `DEFAULT_STALL_SECONDS` (read from the driver source, not hardcoded).
  Fourth contract: `execution.per_run_timeout_seconds` must sit **above** the wall budget (`>` not `>=`) so the driver writes the honest manifest — `perf/pf5` shipped 900/900 and was raised to 1800. Operator surfaces: [§ PF Scenario Suites](#pf-scenario-suites) and [P4 Campaign Suites](#p4-campaign-suites).
- `tests/test_memory_index_check.py` -- Hermetic gate for `util/memory_index_check.py` (`util/` is outside every pre-commit Python hook, so this suite IS the gate).
  Load-bearing: missing `MEMORY.md` is exit 2 not a silent pass; `--skip-if-absent` is announced; malformed baseline is exit 2; absent baseline treats every row as new.
  The 120 cap binds the **hook** (`len(hook)`), not the line (a 130-char slug with a tiny hook must pass); grandfathered oversize hooks do not fire.
  `--advisory` reports and exits 0; `--accept` writes slugs + a history sample; runway needs two dated samples, shrinking is `inf`, same-day does not divide by zero; shipped constants 200 / 25000 / 120.
- `tests/test_hazard_triage.py` -- Hermetic gate for the pre-cut HAZARD FINDER `util/ad-hoc/2026-08-28_hazard_triage.py` (`util/` is outside every pre-commit Python hook).
  A first version scored per LINE and found ZERO of four real hazards in this repo's own `AGENTS.md` -- wrapped prose never reaches two signals on one line, so the finder reported a clean file over real hazards.
  Same vacuous-pass class as a census that certified 36 sites where 58 is true.
  Pins block scoring of wrapped bullets, CommonMark fence exclusion (code samples must not spend reviewer judgement), the `<40`-char skip, the min-score threshold, and the live `AGENTS.md` positive control (`>=3` Hazards-section candidates, including `KILL_WORKERS` and `max_epochs`).
- `tests/test_p5_port_memory_budget.py` -- Hermetic gate for the P5 fleet-rollout porting helper `util/ad-hoc/2026-08-25_p5_port_memory_budget.py` (`util/` is outside every pre-commit Python hook): growth statistics from a temp git repo measured in CHARS with a nearest-rank `p90` (the floor form returned the *smallest* growth at n=2, so four of the 2026-08-25 fleet measurements printed p90 < median); `render-job` / `render-workflow` / `render-config` output parses and carries the figures MEASURED in the target (the first two ports found every transcribed figure stale); `insert-job` lands before `required-checks` and outside its `needs:` (C9); `adapt-test` rewrites the repo-root depth and adds SPACE-separated `# nosec` codes (the comma form under-suppresses on bandit 1.9.4 and reads as applied).
- `tests/test_p5_fleet_state.py` -- Hermetic gate for the P5 fleet census `util/ad-hoc/2026-08-26_p5_fleet_state.py`. Complementary leftover the `TARGETS`/`ROSTER` pin in `tests/test_require_context_safely.py` cannot see: `_size_check_is_advisory` reconstructs the `memory_budget_check.py` invocation (a whole-file `"--advisory" in wf` read True fleet-wide because de-advisory comments mention the flag and juniper-ml keeps a live `--advisory` on `relocation_check.py`); `gh_api` returns `None` only on HTTP 404 (a rate-limit used to look like an absent file); sizes are `len()` of decoded text (CHARS), never the API `size` field (BYTES); `memory_budget_required` is an exact context-name match.
- `tests/test_resident_gap_triage.py` -- Hermetic gate for the third P5 hazard tool `util/ad-hoc/2026-08-31_resident_gap_triage.py` (`util/` is outside every pre-commit Python hook). `#1663` pins the AGENTS.md finder; this pins the leftover that finder cannot see -- SOURCE comments that are resident nowhere. A first version scored a 2-sentence window and buried the known-real cascor `max_epochs` / `output_epochs` split (score 2, below threshold) because prohibition and silence sit four paragraphs apart. Pins block scoring of spread signals, the identifier-already-in-AGENTS.md gap predicate, log-level demotion that never drops a remaining-score hit, `test_*.py` / `worktrees/` skip, silent-failure sort preference, `--min-score` as a print threshold (JSON keeps every scored row), and a synthetic L-2 `self_check` at `cascade_correlation.py:1927`.
- `tests/test_resident_gap_scan.py` -- Hermetic gate for the P5 resident-gap FINDER `util/ad-hoc/2026-08-28_resident_gap_scan.py` (`util/` is outside every pre-commit Python hook). `#1663` pins the AGENTS.md finder; `#1697` pins triage severity. This pins the leftover those cannot see: IDENT rejects prose-in-backticks (first version filled `names:` with fragments like `), and the verbatim rejection detail (`); `.claude/worktrees` copies are skipped (the documented 23,120-file multiplication; `#1697` only pins `worktrees/`); `legacy/` copies are skipped; contiguous `#` lines join into one block (a per-line split fails `--min-len`); missing `AGENTS.md` is exit 2; ranking is identifier count (why the triage exists); `no_update` is STOP.
  - **Oversize is pool OR cap.** The original gate triggered on `candidate_pool_size >= 16` only, so a wide-**cap** suite at a modest pool shipped and then lost its widest cells to a false `stalled` hours in — the candidate phase slows every iteration as the cascade widens each candidate's input, i.e. "the ml#1069 class, arriving through width instead of through pool size" (`suites/p4/e-i-cascor-cap-ceiling.yaml:46-50`). `max_hidden_units >= 64` now triggers too.
  - **Third contract — wide-cap suites must pin a wall budget**, via either `execution.max_wall_seconds` or a dotted `outputs.max_wall_seconds` override (E-I uses the latter, so accepting only the former would fail a correctly-budgeted suite). Thresholds are measured, not guessed: E-I at fixed pool 8 ran cap 32 → 1497.4 s, cap 64 → 2907.1 s, cap 128 → **4243.6 s** against a 3600 s inherited default, so 128 would have been truncated and 64 clears by only 693 s.
  - **Fourth contract — `per_run_timeout_seconds` > driver wall** (`>` not `>=`): equal destroys the manifest (subprocess kill before the driver writes). Both apps.
  - **Limitation, partially lifted.** Declared `matrix` / `include` are unioned with per-cell effective values when the base resolves (`_effective_numbers`, via `expand_cells`). Sibling-repo bases stay `unresolved` in a juniper-ml-only checkout; in-repo bases always resolve, so `e-k` / `e-l` read as cap-16 / cap-4 rather than inherited 64. Anti-resurrection check for the retired `util/ad-hoc/2026-08-10_driver_stall_shim.py`.
  The Q-2 detector watches `current_epoch`, which does not advance while the CANDIDATE pool trains, so those cells are recorded `stalled` while perfectly healthy -- the P4 E-A grid lost its pool-16 cells to exactly that.
- `tests/test_p5_port_memory_budget.py` -- Hermetic gate for the P5 fleet-rollout porting helper `util/ad-hoc/2026-08-25_p5_port_memory_budget.py` (`util/` is outside every pre-commit Python hook): growth statistics from a temp git repo measured in CHARS with a nearest-rank `p90` (the floor form returned the *smallest* growth at n=2, so four of the 2026-08-25 fleet measurements printed p90 < median); `render-job` / `render-workflow` / `render-config` output parses and carries the figures MEASURED in the target (the first two ports found every transcribed figure stale); `insert-job` lands before `required-checks` and outside its `needs:` (C9); `adapt-test` rewrites the repo-root depth and adds SPACE-separated `# nosec` codes (the comma form under-suppresses on bandit 1.9.4 and reads as applied).
- `tests/test_matrix_set_verdicts.py` -- Hermetic gate for the E2E matrix verdict writer `util/ad-hoc/2026-09-02_matrix_set_verdicts.py` (`util/` is outside every pre-commit Python hook), which shipped with zero tests: verdict tokens, row identity, and the write-back path.
- `tests/test_e2e_matrix_fill.py` -- Hermetic gate for the E2E matrix bulk-fill writer, which shipped with zero tests: which cells a fill may touch, and that an already-filled cell is not silently overwritten.
- `tests/test_e2e_matrix_rescore.py` -- Hermetic gate for the named-row matrix re-score writer, which shipped with zero tests: row lookup by name, and that a re-score rewrites only the named row.
- `tests/test_e2e_unfilled_rows.py` -- Hermetic gate for the unfilled-rows ledger reader, which shipped with zero tests: what counts as unfilled, and that a partially-filled row is not reported complete.
- `tests/test_e2e_f037_render_census.py` -- Hermetic gate for the F-CANOPY-037 render census, which can certify a VACUOUS run -- a census over an empty or unrendered set reporting success is the failure this pins.
- `tests/test_e2e_row_coverage.py` -- Hermetic gate for the row-coverage estimator, which can certify a PARTIAL ledger as complete -- coverage computed over the rows present, not the rows required.
- `tests/test_soak_probe_evidence.py` -- Hermetic gate for the soak retrieval-evidence extractor, which shipped with zero tests: what counts as evidence for a probe, and that a probe with none is not scored as satisfied.
- `tests/test_soak_wilson_resolving.py` -- Hermetic gate for the Wilson power table: a table that spends sessions for a WORSE bound is the defect -- monotonicity of the interval in n, and that the resolving-n it reports is actually resolving.
- `tests/test_soak_run_probe_stopping_rule.py` -- Stopping-rule paths in `util/soak_run_probe.py` that the dry-run suite cannot reach: the dry run never enters the arms that decide to STOP, so those arms shipped unexercised.
- `tests/test_soak_ledger_status_token.py` -- The `util/soak_ledger.py` status first-token contract the dry-run suite cannot see: the token a downstream reader keys on, pinned against a renaming that keeps the line but changes its meaning.
- `tests/test_soak_analyse_date_pool.py` -- Pins that `analyse()` pools the corpus the probe picker now SPLITS by date -- a pooled analysis over a split corpus silently mixes cohorts and reports one number for two populations.
- `tests/test_run_suite_gate_metrics.py` -- Suite-report gate values that the header pin in #1643 cannot see: the header can be correct while the gate VALUES beneath it are stale or absent.
- `tests/test_list_runs_classify_guards.py` -- The `list_runs` classification guards the happy-path suite never reaches -- the arms that REFUSE to classify, which a well-formed run never enters.
- `tests/test_register_close_protocol.py` -- The defect-register operator pair that #1648/#1717 cannot see: the close protocol itself, distinct from the open-set reader and the status crosscheck.
- `tests/test_stats_summary_render.py` -- `summary.md` scrape-honesty line collection: which lines the renderer must emit, the conditional class-distribution line, the reason sub-bullet, and `present`/`written` key precedence.
- `tests/test_stats_summary_git_and_confirmed.py` -- The `summary.md` scrape tri-state and git provenance the producer suite cannot see -- `confirmed` None-is-not-False, the N/A fallback, unavailable git, clean-head, and a decreasing count that must not mint a poll sample. Independent sibling of `test_stats_summary_render.py`; see its header for why both were kept.
- `tests/test_canopy_poller_inventory.py` -- The canopy poller census that can certify a PARTIAL inventory -- a census counting the pollers it found, not the pollers that exist, reports completeness it cannot know.
- `tests/test_cascor_freeze_tell.py` -- The cascor freeze tell that FALSE-FROZE siblings and missed the real one: both error directions of the same predicate, which a one-sided test cannot separate.
- `tests/test_ruleset_context_audit.py` -- The ruleset context audit that can make `main` UNMERGEABLE -- promoting a context that never reports leaves every PR blocked forever, so the audit's failure mode is worse than its absence.
- `tests/test_snapshot_index_root_resolution.py` -- The env-root resolver the `--root` suites cannot see: they always pass `--root` explicitly, so the DEFAULT resolution path they exist to protect is never entered.
- `tests/test_equities_symbol_cap_operator.py` -- The suite and stack surfaces that can defeat the 14-symbol equities cap (APD-DATA-018), with two anti-vacuous controls -- the cap is only a cap if every surface honours it.
- `tests/test_e2e_append_statuses.py` -- Hermetic gate for the E2E TSV verdict appender, which shipped with zero tests: which column a verdict lands in, and that an append does not rewrite a neighbouring row.
- `tests/test_recurrence_kind_edges.py` -- Recurrence-kind edges in `util/experiments/read_run_metrics.py`: a manifest whose `timings`, `drive_loop` or `dataset` is a truthy NON-mapping. `or {}` guards absence, not type, so a list or string reached `.get` and took down `read_suite` -- and with it make_baseline, compare_baseline, and run_suite.aggregate, which then destroys its own aggregate.csv.
- `tests/test_e2e_topology_row_predicates.py` -- The three M-TOPOLOGY row predicates, extracted from `util/ad-hoc/e2e_seg17_topology_driver.py` into `util/ad-hoc/e2e_topology_row_predicates.py` so they can be unit-tested at all: `util/` is outside every pre-commit Python hook. Pins that M-TOPOLOGY-06 requires the label AND the count (an OR over two independent claims scores the easier one), that M-TOPOLOGY-07 asserts the label it reads, and that M-TOPOLOGY-12's absent-control case is BLOCKED rather than FAIL.
- `tests/test_e2e_topology_score_contracts.py` -- Heatmap / export / store-gate score contracts extracted into `util/ad-hoc/e2e_topology_score_contracts.py`: what each row's verdict actually turns on, and which inputs must make it FAIL rather than being recorded as decoration.
- `tests/test_e2e_topology_step_order.py` -- `--step` parsing extracted into `util/ad-hoc/e2e_topology_step_cli.py`: order is preserved, an unknown step is rejected loudly rather than silently skipped, and the driver walks the WANTED list rather than the registered one.
- `tests/test_compare_baseline_defects.py` -- The A1-A7 comparator refusals the happy-path suite cannot reach: partial scenario coverage, duplicate baseline fingerprints, a driver-truncated candidate, and the mixed measured/unmeasured suite whose one surviving cell used to satisfy the work invariant vacuously.
- `tests/test_work_countable_contract.py` -- The `work_countable` third state end to end: a recurrence candidate is REFUSED with the honest reason rather than FAILed, and no waiver can override a refusal that says the WORK half of the gate does not apply.
- `tests/test_termination_branch_precondition.py` -- The termination-branch precondition: `step_count` is deterministic only WITHIN a branch (29 of 79 repeated configs diverge across branches, zero within one), a driver-truncated `outcome` measures the budget rather than the code, and an unannotated cell is its own branch rather than being filtered into unanimity.
- `tests/test_run_suite_uncountable_report.py` -- REPORT.md's third state: `not countable` must stay distinct from HOLDS and BROKEN, an empty gate must remain the cascor-unmeasured case, and the report must ask `summarise` rather than re-deriving `len(counts) == 1` -- which reads HOLDS on a half-measured suite.
- `tests/test_worktree_inuse_probe.py` -- Hermetic coverage for `util/ad-hoc/2026-09-02_worktree_inuse_probe.py`, the guard that REFUSES a destructive worktree cleanup: cwd and open-fd hits are STRONG, a cmdline mention alone is only a caution, and a process owned by another user is reported unreadable rather than counted as absent.
- `tests/test_e2e_finding_triage.py` -- The E2E finding-triage dispositions, which shipped with zero tests: `accepted` is a THIRD state and not a synonym for fixed or open, the first heading wins so a later `fixed` cannot close an earlier `open`, and `--open-only` hides rows without changing the totals.
- `tests/test_e2e_finding_triage_nested_bold.py` -- Header truncation in `util/ad-hoc/e2e_finding_triage.py`: a nested-bold heading must not be cut at the inner marker, which would split one finding's identity into two and double-count it.
- `tests/test_e2e_finding_triage_priority.py` -- `pri_of` first-token severity, lifted out of a nested function so it can be imported: the FIRST severity token anywhere in the bolded header body wins, so a header naming another severity in prose before the parenthetical triages as that severity (F-CANOPY-037 / F-E2E-007).
- `tests/test_require_context_safely.py` -- Hermetic gate for `util/ad-hoc/2026-08-20_require_context_safely.py` (`util/` is outside every pre-commit Python hook). `gh_json` is monkeypatched; nothing talks to GitHub.
  - Pins `find_ruleset` reporting a failed per-ruleset GET as an error (never an absence — ml#1429), genuine absence / ambiguity as the negative controls, and `TARGETS` lockstep with the census `ROSTER` in `util/ad-hoc/2026-08-26_p5_fleet_state.py` (a missing repo is a silent incomplete `--status`).
  - As of [juniper-ml#1612](https://github.com/pcalnon/juniper-ml/pull/1612) also pins `observed_context_apps` (amend pre-flight): publisher from PR heads, `main` fallback, exact-name negative control, and `57789` (Bandit) must not count as a publisher of `Memory Budget`. Operator surface: [Required-Context Ruleset Writer](#required-context-ruleset-writer).
- `scripts/test.bash` -- Manual end-to-end harness for session create/resume launcher flows
- `scripts/test_resume_file_safety.bash` -- Regression script ensuring invalid `--resume <file.txt>` input does not delete the source file

---

## Utility Script Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

- `util/worktree_cleanup.bash` -- Automated worktree cleanup with CWD-safe session continuity (V2 procedure). `MAIN_REPO` derives from `${BASH_SOURCE[0]}` (one dir up) with a `JUNIPER_ML_MAIN_REPO` override for test fixtures. Flags: `--old-worktree`, `--old-branch`, `--parent-branch`, `--new-worktree`, `--new-branch`, `--skip-pr`, `--skip-remote-delete`, `--dry-run`. Phase 7 always restores the primary checkout to an up-to-date `main` (skips on a dirty tree or a checkout refusal; F-6 stale-checkout class).
  - Phase 1: non-empty `status --porcelain` in the old worktree → `exit 1` (`Commit or stash…`) before any push; `--dry-run` skips the check. Clean tree then pushes when ahead/`-u` when no upstream/skips when synced. Phase 2 refuses an existing `NEW_WORKTREE` path (`exit 1`, never clobbers).
- `util/ad-hoc/2026-09-02_worktree_inuse_probe.py` -- Independent second opinion for a worktree sweep. STRONG hits (cwd or an open fd inside the tree) exit 1 `REFUSE`; WEAK hits (cmdline substring) print `CAUTION` and do not set the exit code; this process and its parent are excluded from weak by pid so the probe's own argv cannot report every tree in use. Empty argv exits 2. Read-only. Operator surface: [Worktree Divergence Is a Memory Cost](#worktree-divergence-is-a-memory-cost).
- `util/ad-hoc/e2e_finding_triage.py` -- Mechanical P0/P1 open-count for the canopy E2E Phase 2 exit criterion. Reads only line-starting `**F-… — …**` headers; FIXED/HEALED/ACCEPTED from the last 170 chars of that header; ACCEPTED is a third disposition (not FIXED, not OPEN); `--open-only` hides closed rows but still prints full totals; always exits 0. Operator surface: [Canopy E2E Finding Triage](#canopy-e2e-finding-triage).
- `util/duplicati_scheduled_backup.bash` / `util/install_duplicati_timer.bash` / `util/duplicati_backup_failure.bash` -- Host `$HOME` Duplicati lane under `systemd --user` (#1292).
  - Installer **copies** (never symlinks) the runner, OnFailure reporter, and three user units; does **not** `enable --now` the timer.
  - Runner fail-closes on empty/short passphrase, unmounted dest, wrong-filesystem dest, and tmpfs `--tempdir`; `flock` / DB-open holders `skip_or_fail` (a skip overwrites `result=OK`, so the next skip always escalates).
  - `--no-auto-compact=true` is load-bearing. Distinct from `util/juniper-backup.bash` (project-tree `tar | gpg -e`). Operator surface: [`docs/REFERENCE.md` § Scheduled Duplicati Backup Lane](#scheduled-duplicati-backup-lane).
- `util/juniper-backup.bash` -- Per-repo project-tree archive to attached external media: `tar -cjf` (bzip2) piped into `gpg -e` (asymmetric, two `ENCRYPT_KEYS`). Build once, copy ciphertext. `--dry-run` writes nothing. Restore is `gpg -d FILE | tar -xjf -` (not `-xzf`). Exit 0/1/2/4. Unattended verify is `--list-packets` only. Operator surface: [Juniper Project-Tree Backup](#juniper-project-tree-backup).
- `util/soak_next_probe.py` -- Emits the next pointer-follow soak probe's **task only** (unprimed). Default pick is least-covered then registry order; `--probe-id` needs the **full slug** (`P19-port-check-fail-opens`, not `P19`); `--reveal` is scoring-only; `--status` is post-intervention run counts with no task text. Tests: `tests/test_soak_next_probe.py`.
- `util/soak_run_probe.py` -- Headless `claude -p` wrapper: dispatch, capture, mechanical retrieval channel (`tool_use` inputs + answer text; no `tool_result`), scoring packet. `--dry-run` does not require the `claude` binary and must not print the task. On this tree it refuses `BET-FAILING` / `HOLDS-AT-*` **before** the dry-run branch unless `--force` (`--force` is an open owner decision, not sanctioned). Reaper P1 pidfile is `$JUNIPER_EXP_RUN_ROOT/soak-probes/soak-probe-<pid>.pid`, not `reports/soak/runs/`. Tests: `tests/test_soak_run_probe.py`. Operator surface: [Pointer-Follow Soak](#pointer-follow-soak).
- `util/soak_ledger.py` -- Append-only soak ledger (`probe-run` / `report` / `status` / `verify-probes` / `resolve` / `rescore`). Seeded arm decides; organic describes. `source-recovered` stays in the follow-rate denominator. `--outcome miss` requires `--class`. `rescore` is one-way to `source-recovered`. `analyse()` has no era filter (ledger §15.4 is not applied). `status` exits `1` on `BET-FAILING` or an open escalation (by design). Tests: `tests/test_soak_ledger.py`.
- `util/reap_pytest_orphans.bash` -- Safely reaps orphaned Juniper pytest multiprocessing children (`--dry-run` / `--verbose`).
  - Candidate awk gate: current-user + `/python/` + (`JuniperC[a-z0-9]+` conda path or `Juniper/worktrees/`); empty set exits 0 with "No Juniper python processes found."
  - Orphan when ppid is `1`, user `systemd --user`, or parent gone; live parents KEEP. `SKIPPED` on ps→gone race or missing `PPid:` (never kill).
  - **Live-experiment protection, checked BEFORE the orphan predicate.** `experiment_stack.bash` / `isolated_stack.bash` launch services under `nohup` in a subshell, so they reparent to `systemd --user` — the orphan predicate itself; orchestrators/watchdogs started with `setsid`/`disown` land there too.
  - Two protection keys, either sufficient: **P1** the pid is in a run-dir `*.pid`; **P2** the pid's cmdline references a run root (`JUNIPER_EXP_RUN_ROOT`, default `~/.local/state/juniper-experiments`, or `JUNIPER_E2E_RUN_DIR`). Prints `PROTECT` **always** (not `--verbose`-gated) and counts separately.
  - Observed live 2026-08-16 on campaign `e-j-h2h-wide-cap6`: a dry run called the orchestrator, the experiment cascor service, and the watchdog all `WOULD REAP` while healthy. Over-protection is the deliberate safe direction — a stale pidfile still protects.
  - Test hooks: `JUNIPER_REAP_PROC_ROOT`, `JUNIPER_REAP_KILL_CMD` (plus the two run-root vars, redirected per-test). Operator surface: [docs/REFERENCE.md § Pytest Orphan Reaper](#pytest-orphan-reaper).
- `util/soak_next_probe.py` -- Unprimed dispatcher for one pointer-follow soak probe. Default stdout is the **task only** (probe id on stderr). `--reveal` is scoring-only (fact / pointer / discriminator). Least-covered then registry order; pass `--probe-id` for characterisation. Tests: `tests/test_soak_next_probe.py`.
- `util/soak_run_probe.py` -- Headless `claude -p` wrapper (dispatch, capture, mechanical retrieval channel, scoring packet). Correctness is **not** scored here. `--dry-run` must not require `claude`. Refuses terminal `BET-FAILING` / `HOLDS-AT-*` unless `--force`. Reaper P1 pidfile under `$JUNIPER_EXP_RUN_ROOT/soak-probes/` (not `reports/soak/runs/`). Tests: `tests/test_soak_run_probe.py`. Operator surface: [`docs/REFERENCE.md` § Pointer-Follow Soak](#pointer-follow-soak).
- `util/soak_ledger.py` -- Append-only pointer-follow soak ledger (`probe-run` / `record` / `report` / `status` / `verify-probes` / `resolve` / `rescore`). Seeded arm decides; organic arm describes. Wilson interval vs 0.75; `source-recovered` stays in the follow-rate denominator. `status` exits 1 when action is due. Tests: `tests/test_soak_ledger.py`. Operator surface: [`docs/REFERENCE.md` § Pointer-Follow Soak](#pointer-follow-soak).
- `util/ruleset_scope_guard.py` -- Token-free GET-only guard that fails if any Juniper ruleset is scoped `~ALL` instead of `~DEFAULT_BRANCH`.
  - Removing the dependabot (`29110`) / Copilot (`1143301`) bypass rows on 2026-08-23 is safe only while that scope holds; `~ALL` re-evaluates `creation` on every branch and those rows become load-bearing again.
  - Reports **scope only** (`bypass_actors` is redacted unauthenticated — row checks belong in `util/ad-hoc/2026-08-23_bypass_removal_verify.py`).
  - Exit 0/1/2, fail-closed (empty list and probe failure are **not** clean). CI job `Ruleset Scope Guard` is a hard Quality Gate need.
  - Operator surface: [Ruleset Scope Guard](#ruleset-scope-guard). Tests: `tests/test_ruleset_scope_guard.py`.
- Documentation link validator now lives in [`juniper-doc-tools/`](juniper-doc-tools/) and is published to PyPI as `juniper-doc-tools` (Wave 4 of the doc-link migration plan; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`).
- X7 off-loop census (ad-hoc; lands with juniper-ml#1631) -- exploratory sibling of the canopy slice-1a gate. **Not the authority.** Operator surface: [§ X7 Off-Loop Census](#x7-off-loop-census). Do not quote v1 counts; do not reintroduce module-global expression exemptions.
- `util/ad-hoc/e2e_seg17_topology_driver.py` -- `--step` is order-preserving on one browser page; `topostate` must run first or alone or M-TOPOLOGY-18 reports `INDETERMINATE`. The module docstring's `W4-01..17` / `W1-12..14` list is **correct** (matrix §4 steps); three of its step→row aliases are not. Operator surface: [§ Canopy E2E Topology Step Order and Blast-Radius IDs](#canopy-e2e-topology-step-order-and-blast-radius-ids). Scorer predicates remain in-flight docs #1675.
- `util/ad-hoc/e2e_finding_triage.py` -- `pri_of` takes the first severity token anywhere in the bolded header body (not only the parenthetical). Do not name another severity in header prose. Dispositions remain in-flight docs #1646. Same section as the bullet above.
- Canopy E2E matrix writes (ad-hoc) -- `e2e_matrix_fill.py` (dry-run default; `status` header per table; escaped-pipe split), `2026-09-02_matrix_set_verdicts.py` (**no dry-run**; `--from` + last-cell write; naive `line.split("|")`), `e2e_matrix_rescore.py` (named rows; missing ids warn and still write). Ledger reader: `e2e_unfilled_rows.py`. Do not plan from `e2e_row_coverage.py`. Operator surface: [§ Canopy E2E Matrix Writes](#canopy-e2e-matrix-writes).
- X7 off-loop census (`util/ad-hoc/2026-09-04_x7_offload_census_v2.py`) -- exploratory sibling of the canopy slice-1a gate. **Not the authority.** After canopy#567 the shipped count is **58**. Operator surface: [§ X7 Off-Loop Census](#x7-off-loop-census). Do not quote v1 counts; do not reintroduce module-global expression exemptions; a green `main.py` gate is not proof the adapter is clean.
- `util/ad-hoc/e2e_unfilled_rows.py` -- Canopy E2E **ledger** reader. Prints which `C2.` / `M-` matrix status cells are still placeholders. Reuses `e2e_matrix_fill` pipe-splitting + placeholder set. Exit 0 always. **Not** `e2e_row_coverage.py` (that diffs TSVs and can list already-`PASS` rows as remaining). Operator surface: [§ Canopy E2E Unfilled-Rows Ledger](#canopy-e2e-unfilled-rows-ledger).
- `util/requirements_drift_check.py` -- Drift checker for the requirements snapshot at `notes/requirements/id_assignments.yaml`. Default `--mode quick` validates path resolution + structural line-range integrity for every citation; emits a human report or `--json`. Exit code 1 on any drift. Implements the spec in [the requirements next-steps doc §7](../notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection); `--mode full` / `--mode rewrite` are reserved for future work.
- `util/requirements_consolidate.py` -- v5 refresh tool for `notes/requirements/`. **`by-area/*.md` is the corpus of record**; the ledger has no `detail` field, so regenerating views from `id_assignments.yaml` would silently delete the ~910 Detail sections that exist only in the views.
  - `--check-roundtrip` is by-area only; `--check-views` asserts `by-repo` / `by-status` are the projection of `by-area`. `--merge` / `--regenerate-views` write nothing without `--apply`. Operator surface: [Requirements Snapshot Consolidation](#requirements-snapshot-consolidation). Tests: `tests/test_requirements_consolidate.py`.
- `util/template_data_resolver.py` -- Loader + dotted `resolve()` for the custom-agent suite data layer (`prompts/agent_templates/data/*.yaml`: standing rules, anti-hallucination doctrine, conventions, ecosystem facts, known-misses ledger). Path-invoked (`python util/template_data_resolver.py conventions.handoff_threshold`) or imported; the Template Agent maps these into template slots and RUBRIC R2.5 checks injected conventions against them. Tests: `tests/test_template_data_resolver.py`.
- `util/template_select_preview.py` -- Offline preview of the Template Agent's category selection (P2): given a task string, prints which template the Skill's `match_signals` step would pick (matched keywords + ranked runner-ups). A preview heuristic (keyword-substring scoring; `generic` fallback), not the Skill's exact judgement. `python util/template_select_preview.py "TASK" [--repo-root P] [--json] [--top N]`; exit 0 always. Tests: `tests/test_template_select_preview.py`.
- `util/ad-hoc/register_open_set.py` -- Authoritative open/fixed **counter** for [`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`](../notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md). Keys on `"**FIXED" in line` after `\| (APD-[A-Z]+-\d+[ab]?) `; unique-id sets; relative `Path("notes/…")` so cwd **must** be the repo root. Same measurement as `grep -cE '\*\*FIXED'`. Operator surface: [Defect Register Close Protocol](#defect-register-close-protocol).
- `util/ad-hoc/register_status_crosscheck.py` -- Independent third reading of the same register (§4 `**FIXED` vs §2 prose vs §5.1). Exit 0 `AGREE` / 1 `DISAGREE`. Locates the file via `__file__` (`parents[2]`), so it runs from any cwd. `table_fixed` is currently a whole-file scan. Operator surface: [Defect Register Close Protocol](#defect-register-close-protocol).
- `util/editable_install_drift_check.py` -- Drift checker for juniper editable installs in the conda environments. Reads each env's `*.dist-info/direct_url.json` directly (robust to broken envs); classifies every `juniper-*` editable as `FRESH` / `WORKTREE_PINNED` (under a `worktrees` path) / `ORPHANED` (missing). `*-DEPRECATED` skipped by default; exit 1 on ORPHANED; `--json`; `--fix` re-points orphans to their canonical repo (`--dry-run` previews).
  - **Version axis** (`MATCH` / `STALE` / `UNKNOWN`), orthogonal to the path axis: compares the version the install RECORDED at pip time against the version its target declares NOW. An editable never re-derives its version — `import` follows the live tree while `*.dist-info/METADATA` stays frozen — so a `FRESH` install can be badly stale.
  - Blind spot it closes: on 2026-08-14 **7 of 8** installs on this host were FRESH *and* stale (juniper-data 5 minors behind, `0.6.0` vs `0.11.0`), invisible to both the path axis and `juniper-env-drift-check`'s floor check — a stale editable sits above every floor and is still wrong. It breaks whatever reads the *installed* version: a repo's `version == pyproject` self-check (cascor's `test_version_matches_pyproject`) and a host-launched service's build-info metric.
  - STALE is **soft** (exit 0 — `import` still resolves); `--strict-version` makes it exit 1, while `--strict` stays about the path axis. `--fix-stale` refreshes stale installs against the path they ALREADY point at (`drift: "stale-metadata"`) rather than a canonical-discovery result, which would risk re-pointing a deliberate checkout; ORPHANED repair is unchanged (`drift: "path"`).
  - Dynamic versions are read-only from an explicit `[tool.setuptools.dynamic] version.attr` (flat or `src/`) / `[tool.hatch.version] path` declaration — an unrecognized backend reports UNKNOWN instead of guessing at a `_version.py`. Operator surface: [`docs/REFERENCE.md` § Editable Install Drift Check](#editable-install-drift-check).
  - Ambiguous canonical (juniper-ml#795 coverage): `discover_canonical` returns `(None, [.., ..])` when two+ non-worktree checkouts share a `[project].name`; `--fix` then `action=SKIP` with `reason` containing `ambiguous` (never picks `candidates[0]`). Operator surface: `docs/REFERENCE.md` Editable Install Drift Check + cheatsheet tip.
  - Live `--fix` actions (juniper-ml#802 coverage): `run_fix` marks `FIXED` on successful `pip install -e <canonical> --no-deps --force-reinstall`; `OSError` / `CalledProcessError` become `action=ERROR` (stderr truncated to 500 chars) without aborting later plan items; after a non-dry run, `main` re-scans so exit `1` still reflects remaining orphans. Operator surface: `docs/REFERENCE.md` Editable Install Drift Check + cheatsheet tip.
- `util/env_floor_drift_check.py` -- Floor-drift checker (gap I-2): reads each installed `juniper-*` version from its `*.dist-info/METADATA` and compares to the target repo's `pyproject.toml` floors -> `OK` / `BELOW_FLOOR` / `MISSING` -- the below-floor plain-wheel case the pins/editable checkers miss. Env selection is data-driven (`--site-packages`/`--env`/`ecosystem.yaml`); exit 1 on `BELOW_FLOOR` (`--strict` also `MISSING`); `--json`; structural CI gate. Tests: `tests/test_env_floor_drift_check.py`.
  - `resolve_site_dirs` precedence: `--site-packages` → `--env` → `ecosystem.yaml` `used_by` for `[project].name`; unresolved paths exit 2 with the reason string (never invent an env name). Operator surface: `docs/REFERENCE.md` Environment Floor Drift Check.
  - Multi-site / multi-interpreter: `installed_juniper_versions` keeps the **highest** version across site-packages dirs; malformed / unreadable `METADATA` and non-`juniper-*` are skipped. Coverage: open #796 / #802.
- `util/check_conda_env_torch.bash` -- Classifies a conda env's `import torch` / `torch._C` layout (P-5). Exit 0 healthy / 1 missing env / 2 free-threaded shadow / 3 other import fail / 4 namespace-package `_C` (May-7 regular-3.14 wheel class, or imported `_C` has no `__file__`). Does **not** rebuild. `JUNIPER_CONDA_DIR` default `/opt/miniforge3`. Tests: `tests/test_check_conda_env_torch.py`. Operator surface: [Conda Env Torch Shadow Diagnostic](#conda-env-torch-shadow-diagnostic-p-5).
- `util/release_train/` -- PyPI release-train tooling (release-train plan §12). `registry.yaml`: the data-driven 18-package / 8-repo registry (§4.1). `detect.py`: the per-package "needs a PyPI deploy?" engine (§4.2/4.3, Phase 1, report-only) -- PyPI truth vs declared version, tag-matched diff base, `gh compare` (`--local-git` fallback past the 300-file cap), and a substantive-hunk SHIP filter discounting the notes-rename comment/docstring/link class; report-only, exit 0/1/2.
  - SHIP / SemVer edges: whitespace + pure comment deletion discounted; pure code deletion ships; `local_git_compare` A/D/R/**C** of a `.py` module is inherently substantive (no blob compare); Keep-a-Changelog `Security` → patch, `Changed`/`feat!`/`BREAKING CHANGE` → minor pre-1.0. Operator tables: release-train operator runbook §3.1.
  - Soft-fail `SHIP_UNCERTAIN` (unreadable declared version / missing tag / `comp.ok=False` / truncated empty window / patch-uncertain) is an action class — never silent `UP_TO_DATE`.
  - Hygiene `list_releases` `SourceError` sets `tag_only=None` + an unavailable note (does not exit 2 or invent TAG_ONLY). Offline `--local-git` must raise (open #773), not return `set()`. Operator tables: release-train runbook §3.1.
  - On the live daily path, a Releases-API 404 / `None` from `_gh_lines` must **raise** rather than coerce via `or []` into an empty set — an empty set makes `diff_base_tag not in releases` always true and yields a false TAG_ONLY for every package. An *authenticated* empty Releases list remains a genuine TAG_ONLY.
  - Detect step summary / Slack footers: report and propose count the full action set `UNRELEASED_CHANGES` + `BUMPED_NOT_RELEASED` + `SHIP_UNCERTAIN`, while the ceremony footer counts **only** `BUMPED_NOT_RELEASED` (the ceremonial class). A missing or empty `release-manifest.json` surfaces the hard-fail banner / `FAILED HARD` Slack line, never a quiet clear.
    Pins: `DetectSummaryRehearsalTest` / `DetectSlackPayloadRehearsalTest`. Operator surface: [`docs/REFERENCE.md` § Release-Train Detect Summary and Slack](#release-train-detect-summary-and-slack).
- `util/release_train/propose.py` -- Proposal-PR generator (Phase 2.1, plan §5.4): from `detect.py`'s manifest, for each `UNRELEASED_CHANGES` package builds the standard-gated proposal -- static/dynamic version bump, the CHANGELOG `[Unreleased]`->`[<version>]` move, a `notes_render` notes draft (not archived), the meta AGENTS.md co-change, and `propagation_edges`; dup-guard + `changelog_conflict` refusal via a seam. **`--dry-run` default writes nothing.** Tests: `tests/test_release_train_propose.py`.
  - ml#701 dunder lockstep: a static-version package that also ships a `_version.py` gets BOTH files bumped in one proposal (auto-detected by file presence; no registry field), with the co-change named in the PR body + the S5.4 checklist. Gate: `VersionDunderLockstepTest` in `tests/test_release_train_registry.py`.
  - Sibling/meta AGENTS.md **Version** (worker#140 / ml#706): step 5 (meta) / 5a (sibling primary, `pypi_name == repo`) rewrites a from-version header; sub-packages never touch the host header.
  - Already-at-target / re-entry + absent edges (juniper-ml#720): header already at `to_version` is silent success (no false `REQUIRED`); absent file or missing `**Version**` line surfaces checklist `REQUIRED` (never invents a header).
  - AGENTS.md per-package version TABLE row (juniper-ml#851; the worker#140 class, table variant): step 5a's `set_agents_table_version` bumps the version cell of any `|`-row naming the released `pypi_name` in backticks with exactly one standalone version cell -- recurrence's `AGENTS.md:22-24` table is pinned to `_version.py` by its `version-drift` hook, so header-only proposals shipped red (recurrence#92/#93). Per-PACKAGE, not per-repo: a sub-package bumps its own row, never the host header.
  - Table honesty rules + single-edit composition (juniper-ml#851): already-at-target is silent success, no such table = no phantom edit and no checklist noise, an unexpected/ambiguous cell is byte-untouched + checklist `REQUIRED`, prose version mentions are left alone (the target hook does not gate prose); the header, table-row, and extras-pin true-ups compose into ONE `AGENTS.md` `FileEdit`. Operator triage: release-train runbook §3.2.
  - CHANGELOG refuse clear-on-refuse (juniper-ml#751): empty/missing Unreleased or missing CHANGELOG after the version/dunder bump is staged → `prop.edits.clear()` so the skipped stub is `edits=[]` + `skipped_reason` (matches dup-guard / `bump=none`). Operator guidance: release-train runbook §3.2.
- `util/release_train/notes_render.py` -- Template-driven release-notes generator (plan §10.1), imported by `propose.py` and independently invokable: renders a DRAFT from `TEMPLATE_RELEASE_NOTES.md` (or the security template when a `Security` category is present), grouping CHANGELOG `[Unreleased]` bullets by Keep-a-Changelog category, and surfaces the `notes/releases/RELEASE_NOTES_<pkg>_v<version>.md` archive convention (`--print-archive-name`). Tests: `tests/test_release_train_propose.py`.
  - `link_base` rewrite (`--link-base`; ceremony = owning repo's tag-pinned blob URL, propose = `blob/main`): repo-relative CHANGELOG links render absolute so centrally archived notes don't 404 (the canopy v0.6.0 class).
  - Gate 1 draft signals: meta `display_name` → `Juniper ML`; `release_type("major")` → MAJOR (`none`/unknown → PATCH); Breaking YES iff a `Removed` category is present; `_split_bullets` accepts `*` as well as `-` and folds continuations. Operator table: release-train runbook §3.2 (coverage juniper-ml#756).
- `util/release_train/archive_guard.py` -- Structural guard (Phase 3.1, plan §7.2) for the release-train's gate-exempt notes-archive PR. Passes a PR diff (`git diff --name-status`; injected) ONLY if it is **add-only**, **path-confined** to `notes/releases/RELEASE_NOTES_*.md`, **name-valid** (`_v<semver>`, registry `pypi_name`), and **single-purpose**; non-archive PRs `SKIP`, a violation only `FAIL`s the check (R7). Run by `ci.yml`'s PR-only lane. Tests: `tests/test_release_train_archive_guard.py`.
  - `touches_releases` inspects **both** sides of a rename/copy so a rename-OUT of `notes/releases/` is still an archive PR and `FAIL`s (never `SKIP`s). Copy (`C`) and Typechange (`T`) are non-`A` and FAIL rule1. Operator triage: release-train runbook §3.3.
  - `Allow-Archive-Edit: <path>|<basename>|*` commit trailer (house `Allow-*` idiom; injected via `--trailers-file`, produced by `ci.yml` from `git log --format=%B FETCH_HEAD..HEAD`) waives rules 1/4 for in-place edits of FLAT `notes/releases/RELEASE_NOTES_*.md` files -> distinct `WAIVED` verdict (exit 0, waived paths named); anything dragging an out-of-archive or nested path still FAILs. The #1003 link-repair class/issue #1013. **Carry the trailer into the squash commit message.**
- `util/release_train/ceremony.py` -- Exempt-archive + Release ceremony (Phase 3.2, plan §7/§8/§10) for `BUMPED_NOT_RELEASED` packages: §8 preconditions (each HALTs + dedup issue), notes from the CHANGELOG `[<version>]` section, open the exempt archive PR (signed API commit), enable auto-merge, cut the Release (`--latest=false`; no `--verify-tag`), monitor -> `PENDING_PYPI_APPROVAL`. R7 gh-surface allowlist; idempotent re-entry. **`--dry-run` writes nothing.** Tests: `tests/test_release_train_ceremony.py`.
  - Signed-archive re-entry: reuse tip-at-base / single-commit-atop-base; HALT on unresolvable base/tip, non-422 refs errors, or diverged branch (never invent a sha). Operator table: release-train operator runbook §3.3.
  - Open archive-PR reuse (juniper-ml#730): `enable_automerge(…, pr_ref or plan.archive_branch)`; archive-already-on-main → release only; Release-exists → `RESUME_MONITOR`.
  - Precondition: `notes-render-failed` HALTs when `notes_render.render_notes` raises `OSError` (missing/unreadable `TEMPLATE_RELEASE_NOTES.md` / security template) — restore the template, re-run; never invent archive body. Operator catalogue: release-train operator runbook §4.
  - Monitor: `NOT_FOUND` (run invisible right after `cut_release`) is **not** terminal — keep polling; timeout while still building or permanently missing → honest `IN_PROGRESS` (never invent PENDING/RELEASED/HALT). Operator guidance: release-train operator runbook §3.3.
  - Monitor run **selection** (`select_publish_run`): a Release fires EVERY `release: published` publisher in the owning repo, and the tag-guarded ones finish `completed/skipped`
    sharing the real run's `displayTitle` **and** `headBranch`. Feeding a skipped run to `classify_publish_run` yields `IN_PROGRESS` forever, so the monitor burns its whole
    `--monitor-timeout` per package and the ceremony job's `timeout-minutes: 30` kills the run — surfacing as a bogus `cancelled` (the 2026-08-09/10 class; both legs of the
    cascor 0.8.0 + protocol 0.2.0 ceremony hit it). Selection drops `skipped` runs, prefers an exact `headBranch` match over a substring `displayTitle` match (bare `v0.2.0` is a
    substring of `juniper-cascor-protocol v0.2.0`), and prefers an unfinished run over a finished one. All-skipped → `None` → non-terminal `NOT_FOUND`. Pin: `SelectPublishRunTest`.
  - R7 archive-lane (`_assert_api_allowed`): a `git/refs` POST must carry explicit `ref=refs/heads/*` — missing/empty `ref=` is `SeamViolation` (juniper-ml#770; pre-#770 deferred omit to the live API).
  - Execute terminal `RELEASED`: publish run `completed`+`success` (both gates done) surfaces as final state with **no** halt issue — distinct from plan-time `ALREADY_RELEASED` (PyPI already serves target). Operator guidance: runbook §3.3.
- `util/prompt_discovery/` -- Discovery helpers for the custom-agent suite (PR 4); path-invoked (`python util/prompt_discovery/cli.py --repo-root <path>`), emits a JSON grounding bundle (closed-world facts + provenance: `head_sha`/`dirty`/`ttl_seconds`/`per_probe_status`) from seven probes (`repo_context`, `test_status`, `file_probe`, `symbol_probe`, `dependency_facts`, `conventions`, `concurrency`). Accepts `--target-repo` (cross-repo alias of `--repo-root`). A discovery failure is a hard stop (exit 2).
- The **sequence-safety screens** now ship in `juniper-ci-tools` (>=0.8.0) as two console scripts; rollout W3 deleted the inline `util/sequence_safety/` copy (unit tests → `juniper-ci-tools/tests/`; resurrection-guarded by `tests/test_ci_tools_drift.py`). `juniper-symbol-loss-check` -- symbol-loss screen (P2 gate G1/G3): AST inventory of BASE vs HEAD; FAIL on a deleted (`LOST`) / gutted (`WEAKENED`) / duplicated def, with an SF3 qualified-name relocation downgrade and a `Allow-Symbol-Loss:` trailer escape.
- `juniper-docs-additions-check` -- docs deletion-magnitude screen (P2 gate G2 / G3 step 4): for `AGENTS.md` + `docs/**` + `notes/**`, FAIL on a deleted heading or a `>=N`-line deletion run (default 5, `--min-run`); WARN on small deletions / swaps / retitles; `Allow-Docs-Rewrite:` trailer escape.
- Both screens keep `--base/--head [--files] [--advisory] [--json]`, exit 0/1/2, the WARN-only `--advisory` label hatch (SF5), and add a repeatable `--scope GLOB`. juniper-ml's `ci.yml` (per-PR) + `main-verify.yml` (post-merge G3) install the package; the symbol screen passes the explicit ml scope `--scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash'` (docs = universal default), reproducing the in-repo predicate byte-for-byte.
- `util/fleet_triage/predict_merge.py` -- Deterministic predicted-merge triage for third-party fleet PRs (Stage-0 supervisor script layer; flood §4 item 7). Per PR, in a throwaway detached `git clone` under the system tempdir (never a `git worktree`, never a push), merges `origin/main` into the branch tip and on the result runs the repo-pinned fast gates + an AST symbol-loss screen + a docs additions-only screen. `--pr N | --batch [--json] [--repo-root P]`; exit 0/2. Tests: `tests/test_predict_merge.py`.
  - Emits per-PR JSON (`verdict` MERGE-CLEAN / NEEDS-UPDATE-BRANCH / DAMAGED-FIX-FIRST / CONFLICT + the TRUE changed-file delta from the merge result, NOT `gh --json files`); `--batch` builds the same-file cluster map + a heal-first (`restore`/`heal`/`repair`/`fix-first`), least-colliding merge order.
    - The read-only `fleet-supervisor` agent invokes it once per batch.
    - The AST symbol + docs screens shell out to the `juniper-ci-tools` console scripts (`juniper-symbol-loss-check` / `juniper-docs-additions-check`, >=0.8.0) on the merged RESULT (same CLIs as post-merge `main-verify`; rollout W3 replaced the in-repo `util/sequence_safety/` paths). predict_merge therefore now **requires juniper-ci-tools installed** alongside `gh`; an absent console script degrades that screen to `skip` (never crashes the report).
    - The docs screen counts removed content `-` lines on changed `.md` only (ignores unified-diff `---` headers); no-`.py` TRUE deltas skip the pre-commit battery.
    - `--pr` / `triage_pr`: a `gh` nonzero exit or non-JSON response raises `PredictMergeError` -> CLI exit `2` (hard-fail; there is no partial report worth printing). `--batch` / `triage_batch`: the same condition becomes a soft `ERROR` row and the rest of the open-PR set still runs.
    - The gate battery runs over `changed_existing` (TRUE delta filtered to paths that still resolve as a blob at `HEAD`), so a **deleted** `.py` stays in `true_delta` for the symbol screen but is never passed to `pre-commit --files` — a pure-deletion PR can be gate-clean and still `DAMAGED-FIX-FIRST`. `JUNIPER_FLEET_SKIP_PRECOMMIT=1` forces hook `skip_all`.
    - Operator surface: [`docs/REFERENCE.md` § Fleet Triage and Sequence Safety](#fleet-triage-and-sequence-safety).
- `util/generated_prompt_index.py` -- Indexes the Template Agent's `prompts/generated/` output (P4): lists each prompt parsed by the `PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md` convention, with `--older-than DAYS` + a safety-gated `--prune`/`--archive` (acts only with explicit `--yes`, never under `--dry-run`; `.gitkeep` / non-convention files never touched). The dir is read from `conventions.yaml`. Tests: `tests/test_generated_prompt_index.py`.
- `util/install_agents.bash` -- Mirrors this repo's `.claude/{agents,skills}/*` into `~/.claude` by symlink (design D-6) so the suite is available cross-repo; the project stays source of truth (OQ-6). Idempotent, reversible (`--reverse`), `--dry-run`; `JUNIPER_ML_REPO_ROOT`/`JUNIPER_CLAUDE_HOME` overrides for tests. Never clobbers a non-symlink; `--reverse` removes only owned links. Tests: `tests/test_install_agents.py`.
- `util/scaffold_template.py` -- Generates a new `prompts/agent_templates/<id>.md` (P5): writes the canonical skeleton with well-formed placeholders (so a new template can't drift from the library contract) and **prints** the `manifest.yaml` stanza to paste -- it deliberately does NOT edit the manifest (the human-curated selection contract). Refuses to overwrite. `python util/scaffold_template.py --id ID --title T --class C --keywords k1,k2 [--dry-run]`. Tests: `tests/test_scaffold_template.py`.
- `util/agent_suite_doctor.py` -- Read-only health check for the custom-agent suite (a `planner`-designed dogfood): reports existence + structural validity of every component (agents incl. `opus`/`max`, the Skill, the template library, `RUBRIC.md`, the data layer, the discovery CLI, the `~/.claude` mirror) as `OK`/`WARN`/`FAIL`.
  - `python util/agent_suite_doctor.py [--repo-root P] [--json] [--strict] [--no-discovery]`; exit 0/1/2.
  - Discovery (`check_discovery`) is fail-closed unless `--no-discovery`: missing `util/prompt_discovery/cli.py`, nonzero CLI exit, non-JSON stdout, or bundle missing `schema_version` / `provenance.head_sha` → `FAIL` (never silent OK). `--no-discovery` omits the check (no `SKIP` row).
  - Operator surface: [docs/REFERENCE.md § Agent Suite Doctor](#agent-suite-doctor). Tests: `tests/test_agent_suite_doctor.py`.
- `util/agent_suite_summary.py` -- Quick-reference for the custom-agent suite (P3; the human counterpart to the doctor): lists the agents (name, model/effort, one-line description) and the templates (id, class, when-to-use). `python util/agent_suite_summary.py [--repo-root P] [--agents|--templates] [--json|--markdown]`; read-only, exit 0. Tests: `tests/test_agent_suite_summary.py`.
- `util/assert_release_tag.bash` -- Publish-path guard invoked by all 7 publishers' build jobs (P3; [design](../notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md) §6 Option B, closing the surviving asks of juniper-ml#357 / #358).
  - Asserts (1) the run is on a **tag**, not a branch, and the tag carries this package's prefix; (2) the tag's version equals the version actually built.
  - The built version is read from the **wheel filename**, not `pyproject.toml` -- it is the version that will really be uploaded, and it works identically for static and dynamic (setuptools-scm / hatch) version backends where parsing pyproject reports nothing useful.
  - Versions compare PEP 440-normalized, so a `v1.0.0-rc1` tag agrees with a `1.0.0rc1` wheel. `tr -d -- '-_'` needs the `--`: some `tr` builds (the Rust coreutils rewrite) parse a leading-dash SET as an option, and without it BOTH sides normalize to empty, making the mismatch check pass **vacuously**. An explicit empty-result guard backs that up.
  - **Defence in depth, not the control.** Anyone who can edit a workflow can delete this step; the environment tag policy is what survives that. Value here is failing earlier, naming the reason, and keeping the invariant visible in the repo.
  - `--ref` / `--dist-dir` / `--expect-prefix`; exit 0 pass / 1 assertion failed / 2 misuse. Tests: `tests/test_assert_release_tag.py` (wired into `ci.yml`'s Regression Tests — `util/` is outside every pre-commit Python hook's scope, so that suite is the gate).
    - **`--ref` takes the fully-formed `github.ref`** (`refs/tags/<tag>`), NOT `github.ref_name` plus a separate `github.ref_type`. The two-flag form was deliberately rejected (`util/assert_release_tag.bash:38-44`): `ref_type`'s value on a `release` event is far less clearly specified, and an assumption that is wrong there "does not fail safe; it fails EVERY publish". This line documented the rejected form until 2026-08-19 — a caller following it got `unknown argument` → exit 2 on all 7 publishers.
- `util/safe_merge.py` -- Merge gate (synthesis R4): merges a PR **only** after its REQUIRED checks have finished green, refusing otherwise. Closes the measured failure where **12% of freshness-synced PRs merged before the re-test they had just paid for could finish**.
  - Evidence: ml#932 merged 66 s after its sync on a head with zero CI check-runs; ml#924 merged 25 s after its update-branch head. Both then reddened `main` -- strictly worse than not syncing, since a stale-but-tested head is replaced by a fresh-but-untested one.
  - Delegates "is it finished?" to `util/wait_for_checks.py` as a **subprocess** (deliberately not an import -- the waiter owns that definition and coupling would let the two drift), and maps its 0/1/2/3 exit codes.
  - **TOCTOU contract:** the head SHA is captured **before** the wait and passed to `gh pr merge --match-head-commit`, so a head that moves during the wait is rejected **server-side**. Without this the gate would be decorative -- it is the ml#924 shape.
  - The guard earned its place on the FIRST live run (ml#1170), rejected with *"Head branch was modified"*. Cause: `update-branch` answers **202 Accepted** and moves the ref **asynchronously**, so an immediate read returns the OLD head.
    `update_branch` now polls until the ref moves, and such a rejection maps to a **refusal** (exit 1), not a hard error: nothing was merged, which is correct.
  - `BEHIND` is repaired with the server-side `update-branch` API (**GitHub-signed**, accepted by `required_signatures`); no local git is ever invoked, so no checkout is needed. Re-sync is bounded by `MAX_SYNC_CYCLES` -- sustained concurrent merges refuse rather than spin.
  - `--merge-method rebase` is **rejected outright** (exit 2): rebase re-creates commits unsigned. A zero exit from `gh pr merge` is not trusted -- the PR is re-read and must report `MERGED`.
  - **Kill-resilience** (after a session's run was killed mid-wait, before its second PR merged): the waiter is spawned via `Popen` with `prctl(PR_SET_PDEATHSIG)`, so a SIGKILLed parent cannot orphan it -- measured before the fix, the orphan kept polling GitHub for up to 32 min.
    `SIGTERM`/`SIGINT`/`SIGHUP` reap the child and exit **4 = INTERRUPTED**, distinct from refused (1) and hard error (3), so a killed run is never read as a decision. `--dry-run` no longer blocks on the wait (~2 s, was up to the full timeout).
  - **Why the kill-resilience work exists, measured (2026-08-20).** Kill forensics §3.4 identified the mechanism: a background task runs on a `[bg]` worker, **spare workers hold a hard ~3600 s lease**, and a task **cannot outlive its host worker**. A task placed on a fresh spare gets an hour; the same command placed on a spare already 3372 s old gets 229 s. **The runway is not knowable in advance** — which is why elapsed-at-kill shows no duration pattern and why "it worked last time" predicts nothing. Hold the completion condition off-process.
  - **CI budget is PER-REPO** (`REPO_TIMEOUTS`, `timeout_for()`), re-measured 2026-08-20 across *all required contexts on one head* (`util/ad-hoc/2026-08-20_measure_required_check_span.py`), not one workflow. Spans differ ~6x: ml p90 263 s / max 273; data 1100 / 1196; cascor 1065 / 1547; cascor-worker 1122 / 1717; canopy 1371 / 1719.
    The prior single `900 s` was derived from ml's `ci.yml` median alone and sat at **canopy's median**, so roughly half of canopy's healthy merges would have refused with "checks did not finish". Tiers ≈ 2x p90: ml 900, data/cascor/worker 2400 (also the fallback), canopy/cascor-client 3300.
    Sized on **p90, not max**: cascor-client's max is 15,616 s (4h20m) — a *queued* check, not CI working. Absorbing that would make stuck indistinguishable from slow, which is the one distinction the timeout exists to draw. `TIMEOUT_CEILING = 3300` sits below the 3600 s worker lease, because a local wait longer than the lease is unreachable for a background-run invocation.
  - **Kill-proof net (RC-4):** whenever there is something to wait for, the merge is ALSO handed to GitHub via `gh pr merge --auto`, so a killed run does not strand it. Gated on the repo's `allow_auto_merge` -- where that is false, `--auto` does not arm but falls back to an **immediate merge**, which with the owner's `always` bypass could land a PR whose checks never finished.
    Enabled fleet-wide 2026-08-19 (`util/ad-hoc/2026-08-19_enable_allow_auto_merge.py`); the gate stays because a setting can be switched off again. Not armed on an already-green PR (there `--auto` merges at once, skipping head pinning). `--no-auto-fallback` opts out.
  - **Net armed on `BLOCKED` / `BEHIND` / `UNKNOWN`** (`ARMABLE_STATES`, fixes D1). It previously armed on `BLOCKED` only, while the `BEHIND` branch `continue`d past the arming site — so the **post-sync full CI re-run, the longest and most kill-exposed wait the tool performs, was the one wait entered with no net**. That is the exact shape of the incident. Arming now happens *before* the `update-branch`, covering the sync itself.
  - **A refusal disarms the net** (`disarm_auto_merge`, fixes D3). Previously, a refusal left a live server-side auto-merge in place, so a stated refusal could still become a merge minutes later — observed live on ml#1185. The disarm wraps *every* refusal path at one choke point rather than at each `raise` site. If the teardown itself fails, the refusal says so **loudly** and names the PR; that is the one state where a refusal and a live net coexist.
    **Ordering is load-bearing:** D1 strictly increases the number of refusals that would leave a live net, so D3 must hold before D1 widens the exposure. Never ship D1 alone.
    Exit **4 (INTERRUPTED) deliberately does NOT disarm** — surviving the kill is the entire point of the net — and the interrupt message now says so and prints the `--disable-auto` command, instead of the previous flat "nothing was merged".
  - **`UNKNOWN` is re-polled, not refused** (fixes D2). GitHub reports `mergeStateStatus=UNKNOWN` while recomputing mergeability, routinely for seconds after an `update-branch`; treating it as a verdict produced spurious refusals indistinguishable from real blockers. Bounded by `MERGEABILITY_POLLS` x `MERGEABILITY_INTERVAL`.
  - **The armed net is pinned at ARMING time only** (D4, now fixed — and the fix rests on a measurement, not a reading of the docs). Both paths pass `--match-head-commit`: the local one at merge time, the net via `EnablePullRequestAutoMergeInput.expectedHeadOid`.
    **Measured (probe ml#1225, 2026-08-21):** armed a net *with* a pin, pushed a commit to move the head, re-read the PR — `autoMergeRequest` was **still present with an unchanged `enabledAt`**, so it had neither been dropped nor silently re-armed. `expectedHeadOid` is therefore an **enable-time optimistic-concurrency guard**, not a continuous constraint.
    That distinction was load-bearing and is why it was measured rather than assumed: had it been continuous, pinning would kill the net the moment GitHub moved the head itself to satisfy `strict` — i.e. exactly when the net matters — silently negating the D1 fix. A *push* is a stronger head move than GitHub's own sync, so the probe settles the case that mattered.
    What pinning buys: the net cannot be armed over a **stale read**. What it still does not buy: once armed, the net merges whatever head is current when the checks pass. So the net carries *"merges only when required checks are green"* but not *"merges only the SHA this run vouched for"* — callers needing the stronger property use `--no-auto-fallback`.
    Note the flag needs the **full 40-char OID** (`headRefOid`); an abbreviated SHA is rejected with `Could not coerce value ... to GitObjectID`.
  - **No enforcement** A script can be skipped; the owner's `always` ruleset bypass is what makes required checks advisory for that actor. `python util/safe_merge.py --pr N [--repo R] [--execute]`; **`--dry-run` is the default**. Exit 0 merged / 1 refused / 2 misuse / 3 hard error / **4 interrupted**. Tests: `tests/test_safe_merge.py`.
- `util/memory_index_check.py` -- Local `MEMORY.md` index gate (enforcement option A). Hard cap 200 lines / 25,000 UTF-8 bytes (silent newest-first truncate). New-row hook cap is `len(hook)` vs 120, not the whole line. Baseline `conf/memory_index_baseline.json` decides NEW. Missing file is exit 2 (`--skip-if-absent` for CI). `--accept` grandfathers + samples and always exits 0. Operator surface: [§ MEMORY.md Index Check](#memorymd-index-check). Tests: `tests/test_memory_index_check.py`.
- `util/memory_budget_check.py` + `util/relocation_check.py` -- Memory-size gates (`Memory Budget` job — BLOCKING and a required context since 2026-08-20 (P4); only its G3 step stays advisory). **Don't grow `AGENTS.md`: relocate to `docs/REFERENCE.md`, leaving a pointer that keeps an accurate open/closed status.** G3 proves a relocation moved the *prose*, not just the identifiers — the docs screen cannot see that shape. `Allow-Budget-Overrun:` is a loan, not a pass. The checker reports `headroom = ceiling - chars` and never reads planning slack. [Budget](#memory-file-size-budget) / [Slack](#memory-budget-slack-planning) / [G3](#relocation-completeness-g3).
- `util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth` -- 30-day `AGENTS.md` burn in **chars** (`median` / nearest-rank `p90` / `max`). Planning only; default `--ref` is `HEAD` (pass `origin/main` after a fetch). No required-slack field, no exclusion flag. Slack for a cut is `max(max, 2000)` in `p5_cut.py` / `p5_promote_ready.py`. Operator surface: [§ Memory-Budget Slack (Planning)](#memory-budget-slack-planning).
- `util/ad-hoc/2026-08-26_p5_fleet_state.py` -- Read-only nine-repo census from the GitHub API (chars via `len()`, never the API byte `size`). Prints `headroom`, advisory, required — not planning slack.
- `util/open_signed_pr.py` -- Opens a PR on any Juniper repo whose commit is **GitHub-signed**, by creating branch + commit + PR through the API (`createCommitOnBranch`) instead of a local checkout. Promoted from `util/ad-hoc/` after it landed the ml#1099 signing fan-out across 8 repos.
  - Why it exists: `required_signatures` (2026-08-12) rejects unsigned commits fleet-wide, GPG/YubiKey signing is unavailable to a runner, and an unsigned commit **anywhere** in a branch's history blocks the merge (squash does not rescue it). GitHub signs API-authored commits, so this is the portable way to land a signed change. It needs no working tree, which also makes it the path of choice when a session is confined to one worktree and cannot commit in sibling checkouts.
  - `python util/open_signed_pr.py --repo R --branch B --add LOCAL:REPOPATH [--delete REPOPATH] --message M --title T --body-file F [--base main] [--owner pcalnon] [--dry-run]`. `--add` / `--delete` are repeatable and together express a file move; at least one is required. Exit 0 opened / 1 refused / 2 hard error.
  - Safety: refuses on an existing open PR for the branch (dup-guard -- concurrent sessions are a real hazard here) and on an existing branch (never force-update another ref); `expectedHeadOid` is pinned to the resolved base sha so a concurrent push fails loudly rather than clobbering; `--dry-run` resolves read-only and writes nothing. Mirrors `util/release_train/propose.py`'s `create_signed_commit`. Tests: `tests/test_open_signed_pr.py`.
- `util/wait_for_checks.py` -- Waits for a PR's **required** status checks to finish, then reports honestly. The shared replacement for the hand-rolled "wait for CI" loops that sessions keep re-writing and keep getting wrong the same two ways. Read-only (only `gh pr view` / `gh api .../rules/...` reads — never merges, updates a branch, pushes, or comments), so any session can run it at any time.
  - `python util/wait_for_checks.py --pr N [--repo juniper-cascor] [--owner pcalnon] [--anchor required|observed] [--fail-fast] [--timeout 1800] [--interval 20] [--json] [--verbose]`. Exit **0** all required green / **1** a required check failed (named) / **2** timeout with the still-running and never-reported contexts named / **3** hard error.
  - `--fail-fast` returns on the first failed required context instead of waiting for the full picture. The result also carries a `stalled` flag — true when nothing is in flight **and** something failed **and** required contexts are still absent, which means those absent contexts are downstream jobs (`needs:` a failed job) that will never report, so further polling cannot change the answer. Found by dogfooding: the tool burned 27 polls in exactly that state on its own PR.
  - **Trap 1 — terminal is defined POSITIVELY.** An in-flight check run carries `conclusion: null` and no `state`, so a loop written as "not in my list of pending states" reads it as finished. The pending set is open-ended (`QUEUED`/`IN_PROGRESS`/`WAITING`/`REQUESTED`/…); the finished set is closed. `is_terminal` therefore asks "is it definitely done?" and an unrecognized future conclusion reads as unfinished.
  - **Trap 2 — the rollup GROWS, so "everything I can see is done" is not "the suite is done".** Jobs are appended to `statusCheckRollup` as they start, so a lull between waves (pre-commit matrix finished, test matrix not yet created) is indistinguishable from completion.
  - The only stable anchor is therefore the branch ruleset's **required** contexts; a required context that has not appeared is `absent`, not `running`. `--anchor observed` reproduces the buggy behavior and is opt-in only — `tests/test_wait_for_checks.py` pins both anchors side by side so the difference is executable, not just asserted.
  - `absent` is deliberately its own bucket: a required context that never reports may never report (the `[skip ci]` head-commit orphan class, where the aggregate rollup can read SUCCESS while the PR is permanently unmergeable), so the tool names it instead of waiting mutely.
  - A `gh` non-zero exit is a `ProbeError` → exit 3, never a silently-empty result; that conflation is the same class as trap 1. A missing `required_status_checks` rule is likewise a hard error rather than a quiet downgrade.
  - Probes retry up to `PROBE_RETRIES` (3) times with backoff. The retry is **delay-only** and never classifies errors as transient vs. permanent — a genuinely broken probe fails every attempt and still raises, so the honesty property holds. It exists because two of the first three live runs died due to a transient `TLS handshake timeout` / `unexpected EOF`, discarding a wait that was minutes away from finishing.
  - `mergeStateStatus` is reported but never gated on. `BEHIND` is branch freshness, not check completion — all 9 repos set `strict_required_status_checks_policy: true` ("Require branches to be up to date before merging"), which is a **different** setting from the removed `update` rule ("Restrict updates"); the signing-safe fix is `gh api repos/<owner>/<repo>/pulls/<n>/update-branch -X PUT` (server-side, therefore GitHub-signed). Tests: `tests/test_wait_for_checks.py`.
- `util/ad-hoc/2026-08-28_hazard_triage.py` / `2026-08-28_resident_gap_scan.py` / `2026-08-31_resident_gap_triage.py` -- Complementary P5 hazard finders. The first ranks *already-resident* `AGENTS.md` blocks via `gh api` on GitHub `main` (default `--min-score 2`). The second finds hazard-shaped source comments whose identifiers are absent from `AGENTS.md` (local, read-only; ranks by identifier count). The third joins them: gap finding scored with four severity signals on the **block** (default `--min-score 3`; `--json` writes every scored row; `--self-check` pins cascor `cascade_correlation.py:1927`). `SKIP_DIRS` excludes in-repo worktrees (#1519). The candidate **total is not a health metric** — cutting widens the gap by construction. Operator surface: [Resident-Hazard Gap Triage](#resident-hazard-gap-triage).
- `util/ad-hoc/2026-08-10_ruleset_context_audit.py` -- Read-only fleet classifier for `required_status_checks` (BLOCKING / MATCHED / Tier 1 / path-gated / advisory). Human exit 1 only on `BLOCKING`; `--json` also fails on `error`. Operator surface: [Ruleset Context Audit](#ruleset-context-audit).
- `util/ad-hoc/2026-08-20_require_context_safely.py` -- Fleet writer that adds, or with `--amend-integration-id` ([juniper-ml#1612](https://github.com/pcalnon/juniper-ml/pull/1612)) **re-pins**, one required status-check context. Dry-run default; `--apply` writes; `--status` never writes.
  - Observed-only pre-flight (no `--require-observed` flag); amend asks *which app* publishes the exact name.
  - Six invariants: `rules` verbatim, every *other* context keeps its own `integration_id`, `bypass_actors` verbatim, disk snapshot before the PUT, live re-read immediately before it, post-write verify (drift check stays live except the one intended amend pair).
  - Do not hand-roll a ruleset PUT. Operator surface: [Required-Context Ruleset Writer](#required-context-ruleset-writer). Tests: `tests/test_require_context_safely.py`.
- `util/ad-hoc/` -- Home for single-use / temporary / unfinished scripts. See `util/ad-hoc/README.md` for file-header conventions and graduation lifecycle. `/tmp/` is prohibited for script source files per the [Script placement](../AGENTS.md#script-placement-mandatory) rule.
- `util/ad-hoc/e2e_f027_{queues,ready,slots,deps_endpoint,cleanroom}.py` -- F-CANOPY-027 starvation forensics (FIXED canopy#507/#509/#511). 12-slot pool, not wiring. Operator surface: [F-CANOPY-027 Poller Starvation Probes](#f-canopy-027-poller-starvation-probes).
- `util/ad-hoc/cascor_freeze_tell.py` -- Read-only tell for whether a LIVE process holds the juniper-cascor primary checkout. Exit 1 = freeze in force; exit 0 is "no user-owned importer", not "no importer". Exact path prefix; sibling `juniper-cascor-client` / `-worker` and both worktree roots are not holds. Operator surface: [Cascor Primary Freeze Tell](#cascor-primary-freeze-tell).
- Dependency-documentation generator now lives in [`juniper-ci-tools/`](juniper-ci-tools/) and is published to PyPI as `juniper-ci-tools` (Wave 4 of the dep-docs migration plan; install with `pip install juniper-ci-tools` and invoke via `juniper-generate-dep-docs`). The legacy `util/generate_dep_docs.sh` was deleted in juniper-ml#298.
- `util/juniper_plant_all.bash` -- Starts all Juniper ecosystem services. `JUNIPER_CASCOR_HOST` defaults to `localhost` and `JUNIPER_CASCOR_PORT` defaults to `8201`; both can be overridden via the environment (e.g. `JUNIPER_CASCOR_HOST=remote.example.com JUNIPER_CASCOR_PORT=8201 util/juniper_plant_all.bash`).
  - `safe_conda_activate` nounset (juniper-ml#795 coverage): `set +u` → `conda activate` → `set -u` (ADDR2LINE class). A `+u`/`+u` restore silently disables nounset for the rest of host bring-up — isolated-stack `activate_conda` must match. Operator surface: `docs/REFERENCE.md` Host Orchestration + cheatsheet tip. Tests: `tests/test_juniper_plant_all.py` (`TestSafeCondaActivate`).
  - The helper is also fail-closed for OR-list callers (`if ! conda activate …; then set -u; return 1; fi`), so a masked activate failure cannot launch the next service on the ambient PATH even though today's plant call sites are bare under `set -e`.
  - `--systemd` / `USE_SYSTEMD=1` enters the user-unit arm before nohup preflight: dependency-ordered `systemctl --user start` (data→cascor→canopy→worker), `curl`-only gate (no `ss`), no `JuniperProject.pid`.
  - Missing `curl` aborts before any start. Worker HTTP-ready + inactive unit → WARNING + `status --no-pager`, still exit 0.
  - Mid-plant health timeout runs `cleanup_on_failure` but does **not** `systemctl stop` (systemd starts are never in `STARTED_PIDS`) — operators must chop with `--systemd`.
  - Hermetic pins: `tests/test_juniper_plant_all.py` `TestSystemdModeBehavioral` (open juniper-ml#804). Operator detail: [`docs/REFERENCE.md`](REFERENCE.md) § systemd mode.
- `util/juniper_chop_all.bash` -- Stops all Juniper ecosystem services from `JuniperProject.pid` (`SIGTERM_TIMEOUT` default 15; `KILL_WORKERS`; `--systemd` / `USE_SYSTEMD`).
  - `orphaned_worker_cleanup` (juniper-ml#791 coverage): opt-in `KILL_WORKERS=1` (default `0`, nohup-only — ignored under systemd). `pgrep -af juniper-cascor-worker` then strict cmdline filter (`juniper-cascor-worker` / `juniper_cascor_worker` / search term; rejects over-greedy `cascor.*worker`).
  - Each match: `graceful_stop <pid> cascor-worker 5` (hard-coded 5s, not `SIGTERM_TIMEOUT`). Post-pidfile call uses `|| true` so a benign return 1 cannot abort chop under `set -e`. Operator surface: `docs/REFERENCE.md` Host Orchestration + cheatsheet. Tests: `tests/test_juniper_chop_all.py` (`TestOrphanedWorkerCleanup`).
  - Missing or empty (zero-byte) `JuniperProject.pid`: logs the matching ERROR, calls `orphaned_worker_cleanup` (honors `KILL_WORKERS`), then `exit 1` — never enters the service-stop loop (open #798).
  - Early cleanup call sites are hard (no `|| true`); the post-pidfile site is soft so a benign "nothing to clean" return cannot abort a successful chop under `set -e`.
  - `--systemd` / `USE_SYSTEMD=1` stops units in reverse dependency order (worker→canopy→cascor→data), soft-fails per unit, and always `exit 0`.
  - Never falls through to the pidfile parser or `orphaned_worker_cleanup` / `KILL_WORKERS`.
  - Hermetic pins: `tests/test_juniper_chop_all.py` `TestSystemdModeBehavioral` (open juniper-ml#804). Operator detail: [`docs/REFERENCE.md`](REFERENCE.md) § systemd mode.
- `util/ad-hoc/e2e_f039_topoprobe_instrument.py` -- Revertible server-side TOPOPROBE for canopy store writers (`apply` / `report` / `revert`). `--target metrics` is the live path; `--target topology` refuses unless the handler receives the client's `State`. Backup goes in the git dir, never beside the file. Exit 0/1/2. Not CI. Operator surface: [F-039 Store Probe](#f-039-store-probe).
- `util/ad-hoc/e2e_f039_metrics_store_soak.py` -- Holds a Playwright session so `fast-update-interval` can tick. Exit 0 if the session stayed open. `curl` cannot produce a sample.
- `util/ad-hoc/e2e_f039_duplicate_store_probe.py` -- Live layout-tree walk. `occurrences > 1` and `distinct_data > 1` is the finding; exit 1 is "could not run", not a verdict. Blind to `dcc.Store` DOM and to `paths.strs`.
- `util/isolated_stack.bash` -- Brings up / tears down the isolated training-runtime E2E trio (data 8101 dedicated `python3.14` venv, cascor 8202 `JuniperCascor1`, canopy 8051 `JuniperCanopy1` service mode) with the documented env (control-WS origin pair, `JUNIPER_DATA_URL`, `LD_LIBRARY_PATH=`); `--up`/`--down`/`--status`/`--dry-run`, ports 8101/8202/8051 (`JUNIPER_E2E_*` overrides), `--dry-run` starts nothing. See [E2E checklist](../notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md).
- `util/ad-hoc/e2e_seg17_topology_driver.py` -- Playwright scorer for the canopy Topology tab (M-TOPOLOGY-* / M-DATASET-14). `--step` is required; names must be in `STEPS` (exit `2` otherwise).
  - On `main` (#1672), `topo` M-06 requires **both** label and hidden count; M-07 asserts the label `"all"`; `topoevents` M-12 scores the Clear button (empty-space click is recorded, not scored).
  - Trust `STEPS`, not the module docstring's stale "NOT IMPLEMENTED" list (`topostate` / `topoexport` exist). Companion: `util/ad-hoc/2026-09-04_canopy_verify_instance.bash`. Operator surface: [Canopy E2E Topology Driver](#canopy-e2e-topology-driver).
  - Live compose (juniper-ml#813): `cascor_up` empties `LD_LIBRARY_PATH`, points `JUNIPER_DATA_URL` at isolated data, sets control-WS allowlist to `CANOPY_ORIGIN`, writes `juniper-cascor.pid`, then health-gates; `canopy_up` forces `DEMO_MODE=0`, wires isolated cascor/data URLs + matching `CASCOR_WS_ORIGIN`, writes `juniper-canopy.pid`, then health-gates. Missing `conda.sh` aborts before launch/pid. Operator details: [`docs/REFERENCE.md` Isolated Stack E2E](#isolated-stack-e2e-utilities).
  - `data_up` (juniper-ml#807): dedicated `${RUN_DIR}/.venv-data` via `python3.14 -m venv` (skip create if present), `pip install -e juniper-data[${JUNIPER_E2E_DATA_EXTRAS:-api}] prometheus_client juniper-observability`, launch with `PYTHON_GIL=0`, write `juniper-data.pid`, health-gate; missing `python3.14` aborts via `require_cmd` before side effects. `do_up` order is data → cascor → canopy.
  - Nounset (juniper-ml#785): `activate_conda` must `set -u` after `conda activate` (matching plant `safe_conda_activate`); pre-#785 left `set +u` so live `--up` ran without nounset after cascor/canopy activate.
  - Partial-failure teardown: `do_up` absorbs each leg as `*_up || failed=1` and on failure logs `bring-up failed — tearing the partial trio back down`, then calls `do_down` (experiment_stack parity) so a mid-bring-up failure cannot orphan listeners on 8101/8202/8051. Because the OR-list disables `set -e` inside each `*_up`, critical steps must end with `|| return 1` or a mid-function failure false-greens.
  - Fail-closed `activate_conda` under those OR-list callers: `source … || return 1` and `if ! conda activate …; then set -u; return 1; fi` (both arms restore nounset). A bare activate followed by a successful trailing `set -u` would return 0 and launch cascor/canopy on the ambient PATH.
  - Teardown: `--down` is kill-by-port via `port_pid`/`stop_port` (`ss` first `pid=`), canopy→cascor→data, then RUN_DIR + `snapshot_*` cleanup — not `JuniperProject.pid`. Empty/`ss` soft-fail is a noop; `--dry-run` never kills.
  - Health: `wait_for_health` polls `/v1/health` every 2s until `JUNIPER_E2E_HEALTH_TIMEOUT` (default 60); `--status` `probe_health` reports code + pid and does not fail the script. Operator details: [`docs/REFERENCE.md` Isolated Stack E2E](#isolated-stack-e2e-utilities).
- `util/ad-hoc/e2e_f037_render_census.py` -- Multi-session topology-graph paint census for F-CANOPY-037 (`--step topodiag` in N separate processes). Default 11 sessions (the finding's sample).
  Exit 0 means every session produced PASS or FAIL (even if painted==0); exit 2 means a session produced no verdict. Does not start canopy; inherits `JUNIPER_E2E_CANOPY_URL` (default `:8051`).
  Idle populated is VALID; all-zero `hidden_units` is INVALID. Companion A/B leg: `util/ad-hoc/e2e_f037_ab_premerge_leg.bash`. Operator surface: [F-CANOPY-037 Render Census](#f-canopy-037-render-census).
- `util/ad-hoc/e2e_seg17_topology_driver.py` -- Playwright scorer for the canopy Topology tab (M-TOPOLOGY-* / M-DATASET-14). `--step` is required; names must be in `STEPS` (exit `2` otherwise).
  - On `main`, `topo` M-06 is `label == want OR hidden count == want`; M-07 asserts container display only; `topoevents` M-12 scores empty-space clear as product FAIL.
  - Trust `STEPS`, not the module docstring's stale "NOT IMPLEMENTED" list (`topostate` / `topoexport` exist). Operator surface: [Canopy E2E Topology Driver](#canopy-e2e-topology-driver).
- `util/ad-hoc/e2e_w6_dataset_driver.py` / `util/ad-hoc/e2e_seg16_dataset_driver.py` -- Isolated-stack Playwright drivers for the canopy dataset matrix (W6 COLD migration vs §3.6 Dataset View). `--steps` (W6, comma tokens only) vs `--step` (seg16, required). W6 **stops before** `#restart-confirm-button` (`reset=True` wipes the live network). Shared helpers from `e2e_w3_params_driver.py`; W6 does **not** inherit W3's range parser. Operator surface: [Canopy E2E Dataset Drivers](#canopy-e2e-dataset-drivers).
- `util/experiment_stack.bash` -- Brings up / tears down a **per-run** experiment stack (dedicated juniper-data + `--cascor` and/or `--recurrence`; never canopy) for the
  [CLI experimentation plan](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §6.2 (Wave 2.1).
  `--up` (with `--shared-data URL` / `--config PATH` / `--experiment NAME` / `--grafana-bridge`), `--down <RUN_ID>|--all-mine`, `--status [RUN_ID]`, `--dry-run`; misuse exits 2.
  Services launch from direct env-bin paths (`JUNIPER_EXP_CONDA_DIR`, default `/opt/miniforge3`) with the §6.1 env sets verbatim: `PYTHON_GIL=0` + per-run
  `JUNIPER_DATA_STORAGE_PATH`/`_EQUITIES_CACHE_DIR` (cache only — does **not** set `JUNIPER_DATA_EQUITIES_MAX_SYMBOLS` / `_ALLOW_TRUNCATION`; see [Equities Symbol Cap](#equities-symbol-cap)); cascor `LD_LIBRARY_PATH=''` + `uvicorn api.app:create_app --factory` from `juniper-cascor/src` with AUTO_START off;
  recurrence `serve` with metrics on / rate-limit off — all three metrics toggles on and `JUNIPER_DATA_URL` at the run's data port.
  - RUN_DIR contract (§6.4): `RUN_ID=<UTC yyyymmddThhmmssZ>-<4 hex>` under `JUNIPER_EXP_RUN_ROOT` (default `~/.local/state/juniper-experiments` — under `$HOME`, **not** `/tmp`,
    so a reaped sandbox cannot destroy results, H-15); everything (pidfiles, `logs/`, `relays/`, `config/`, `env/launch.env`, `data/`, `equities-cache/`,
    `artifacts/{plots,results}/`, `ports.json`, `teardown.json`) lives inside it. `JuniperProject.pid` is never read or written; no repo `.env` is ever written (all per-run
    config is process env, H-3), and operator ports 8100/8200/8201/8210/8050 are never touched.
  - Ports (§9.3): first free port in data `8110-8139` / cascor `8230-8259` / recurrence `8260-8289`, claimed by an atomic `mkdir "$LOCK_ROOT/<port>.lock"`
    (`JUNIPER_EXP_LOCK_ROOT`, default `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments`) plus an `ss` probe, released at teardown. The lockdir serializes experiment launchers
    against each other; the residual race vs a non-participating binder is deliberately left to surface as the service's own bind failure through the health gate (H-1).
  - **F-6 pid rule (binding)**: `$!` after `( cd … && nohup <server> … & )` is the backgrounded **subshell**, not the server, so no `*_up` records it. Each service's pidfile
    is written by `record_listener_pid` from `ss -tlnpH "sport = :<port>"` **after** the health gate, with the process cmdline stored alongside; teardown kills pidfile-first
    and only after proving the pid is alive, owned by the current uid, and still running the recorded cmdline (SIGTERM then bounded SIGKILL). If the pidfile path refuses
    (pid-gone/wrong-uid/cmdline-mismatch), `stop_service` logs `pidfile path refused — falling back to the recorded port <N>` and kills via `ss` only on that run's
    recorded port. `artifacts/` is never deleted.
  - Partial-failure teardown: `do_up` writes `ports.json` before any `*_up`; on `failed=1` it logs
    `bring-up failed — tearing the partial run back down` and calls `teardown_run` (live only; not `--dry-run`), keeping `logs/` + `artifacts/` and releasing lockdirs.
  - Health: `wait_for_health` polls `/v1/health` (data, cascor) and `/v1/health/ready` (recurrence) every 2s until `JUNIPER_EXP_HEALTH_TIMEOUT` (default **90** — F-8 sizes it
    for a cold start; the 1.1 s warm number is not the design point).
  - **Dead-process fast-fail**: `wait_for_health` takes an optional 4th arg, a `pgrep -f` liveness pattern, and each leg passes a **port-scoped** one (`-m juniper_data .*--port
    ${DATA_PORT}` / `api.app:create_app .*--port ${CASCOR_PORT}` / `juniper-recurrence serve .*--port ${RECURRENCE_PORT}`) so a sibling run can never satisfy this run's gate.
    Two **consecutive** misses end the wait with `process is gone … died during startup` naming the leg's log, instead of burning the full 90 s per leg on a process that already
    exited (the P4-campaign class). Two misses, not one, and the first probe runs after the first sleep — the launch subshell returns before its child execs, so fork+exec keeps a
    >=4 s grace. **F-6 intact**: the pattern is only ever read; it never resolves a pid and never kills. No `pgrep` on PATH degrades to the prior timeout-only behavior (an
    unavailable probe must never manufacture a failure), and passing no pattern is unchanged back-compat. Pins: `TestHealthGateLiveness` in `tests/test_experiment_stack_script.py`.
  - **OR-list fail-closed**: `do_up` invokes `*_up || failed=1`, which disables `set -e` inside each body. `require_env_bin` / `activate_conda` / `wait_for_health` / `record_listener_pid` therefore each end with `|| return 1`, or a health
    timeout with a live listener false-greens `--up` and skips `teardown_run`. A mid-`allocate_port` failure calls `release_held_locks` (else prior `*.lock` dirs starve later `--up`), and an opt-in `bridge_up` failure after healthy
    services logs `grafana bridge failed — tearing the run back down` and runs `teardown_run` instead of a bare `set -e` abort.
  - **Staging lock release (fixed by #979)**: `create_run_dir` / `stage_config` / `write_ports_json` each `|| { release_held_locks; …; }`, so a missing `--config` no longer exits
    with the lockdirs held and `ports.json` unwritten — the state `--down` could not recover, which starved the 30-port ranges. Should leftovers ever appear (an operator `kill -9`
    mid-staging), clear them under `JUNIPER_EXP_LOCK_ROOT` only after confirming no live listener holds the port.
  - Grafana bridge is **opt-in** (`--grafana-bridge`): only then does it preflight `socat`, discover the monitoring gateway by network-name **suffix**
    (`docker network ls | grep -E '_monitoring$'` — a worktree-launched compose project renames the network; loud default-bridge fallback), start one
    `socat "TCP-LISTEN:<port>,bind=<gateway>,fork,reuseaddr" "TCP:127.0.0.1:<port>"` relay per scraped service (pids under `RUN_DIR/relays/`), and write the §7.2 target file
    to `<JUNIPER_EXP_DEPLOY_DIR>/prometheus/targets/<RUN_ID>.json` (labels `service` / `environment=host-experiment` / `run_id` / `experiment`; removed at teardown).
    Without it, `--status` reports the run as UNSCRAPED.
- `util/experiments/run_experiment.py` -- Single-run experiment driver (plan §6.3; Wave 2.2 = the cascor **service** path, Wave 2.3 = the recurrence **service** path, Waves 2.4/2.5 = the §8.1/§8.2 plot sets via `plots_cascor.py` / `plots_recurrence.py` (2.5 closes G-5), Wave 2.6 = the §8.3 stats/summary via `stats_summary.py`).
  - Stats (§8.3): every run also writes `artifacts/results/stats.json` + human-readable `summary.md` (stdlib-only renderer, every outcome incl. stalled/failed): identity / dataset-shape (tabular vs sequence from meta) / outcome-timing blocks from the manifest, cascor candidate-correlation-per-round + step-duration p50/p95 from the driver's own `metrics_series.csv` (honestly labeled per-poll means -- true per-step quantiles are not recoverable from a sum/count exposition), the recurrence train/CV/θ/readout block.
    Operator read-path: [Experiment Stats Summary (SS8.3)](#experiment-stats-summary-ss83).
  - Stats degraded-mode notes surface G-3 sampling errors, collect errors, plot skips, eval-disabled, and G-6 failures; a stats failure is recorded on the manifest (`stats_error`), never fatal.
  - Recurrence plots (§8.2): `dataset_overview` (sampled 3-D windows, target starred), `dt_histogram` (per-step Δt + `target_dt` -- the irregularity signature; skips non-Δt artifacts), `forecast_vs_truth` + `residuals` (predict response vs the predict split's target, `y_reg_{split}` preferred over `y_{split}` -- the equities regression target; residual-vs-`target_dt` panel when available), `crossval_folds` (per-fold eval bars + aggregate line), `metrics_table` (train + CV ± std).
  - A disabled/failed predict or crossval phase is a per-plot SKIP. Deliberately NO recurrence training-history plot (TrainResponse carries no per-epoch series -- §8.2 note).
  - Plots (§8.1, `outputs.plots`, validated per kind): `dataset` (fetched NPZ artifact scatter; 2-feature generators only), `decision_boundary` (collected grid + sample overlay), `training_history` (history rows, hidden-unit-insertion markers), `candidate_correlation` (from the driver's own `metrics_series.csv` -- the sole source), `eval_metrics` (scalar bars) -- rendered client-side by `plots_cascor.py` (lazy-loaded, Agg backend; NEVER imports cascor, whose plotter imports torch).
  - Plot semantics: structurally unavailable data = recorded per-plot SKIP (exit 0); a render error / failed fetch / missing matplotlib on a requested plot = acceptance failure (exit 1); the manifest `driver.plots` block records requested/rendered/skipped.
  - A renderer `ValueError` is the explicit **no-renderable-data contract**: recorded as a per-plot SKIP only, with no PNG and no acceptance error (exit 0) — distinct from a non-`ValueError` render exception, a failed payload fetch, or a
    missing matplotlib on a requested plot, which are SKIP **and** acceptance failure. Soft edges that deliberately do not raise: a misaligned optional `target_dt` just omits the residual-vs-dt panel, and an empty `eval_aggregate` falls
    back to `folds[0].eval_metrics`. Operator table: [`docs/REFERENCE.md` § Plot SKIP vs acceptance](#plot-skip-vs-acceptance-valueerror-contract).
  Path-invoked: `python util/experiments/run_experiment.py --config <yaml> --run-dir <RUN_DIR>` against a stack from `experiment_stack.bash` -- service URLs resolve from the run's `ports.json` (`--data-url` / `--cascor-url` override). Stdlib + PyYAML; numpy lazily only for the `.npz` artifact (JSON fallback); HTTP via redirect-following `urllib` GETs (F-1: bare `/metrics` 307s to `/metrics/`).
  - Validates the §5.4/§5.5 YAML (driver-owned §5.6 subset): unknown blocks/keys rejected, `schema_version` gated, `experiment.seed` REQUIRED (with the `dataset.params.seed` derivation rule + run-scoped default tags), rule-6 infra keys (`service.host/port/juniper_data_url/eval_metrics_enabled`) rejected; `training:` selects the cascor path, `train:`/`crossval:`/`predict:` (+ `dataset.split`) the recurrence path.
  - **`max_epochs` is NOT an all-passes budget on the service — always set `output_epochs` beside it.** `TrainingParams.max_epochs` bounds only the **initial** output pass; every later per-round pass reads `self.output_epochs`, which falls back to `_PROJECT_MODEL_OUTPUT_EPOCHS = 10000` when unset (`cascade_correlation.py:716`, stated outright at `:1876-1882`).
    The direct CLI instead **aliases** `max_epochs → output_epochs` (`main.py:238-249`) so it bounds every pass, and an explicit `output_epochs` wins over the alias (`:291-292`). A config carrying only `max_epochs: N` therefore runs the CLI at N per pass and the service at N then 10000 — several-fold per-pass divergence over a 64-128-unit run, which makes the service both slower and better-trained than the config appears to ask for.
    **Any CLI-vs-service comparison must set both, to the same value.** `load_config` emits a `validation_warnings` entry (carried on the manifest) but never raises — a service-only run may want the split, and `spiral-baseline.yaml` ships that way. Found by juniper-ml#1143 §2.2; gate: `ConfigValidationTest.test_max_epochs_without_output_epochs_warns`.
  - Drive: generator preflight (`GET /v1/generators` must report `available: true`), `POST /v1/datasets` (content-addressed `dataset_id` recorded), then `POST /v1/training/start` and poll `GET /v1/training/status` to `COMPLETED`/`FAILED` under the Q-2 wall-clock budget (`outputs.max_wall_seconds`, CLI `--max-wall-seconds` wins) + stall detector (no `current_epoch` progress for `--stall-seconds`, default 120 -> `outcome: "stalled"`).
  - csv_import over the 128 MiB cap without `allow_truncation` 422s at `POST /v1/datasets` (driver exit 2). `csv_import` is not in `STAGEABLE_GENERATOR_ALIASES`. [CSV Import Byte Cap](#csv-import-byte-cap).
  - Every cascor-path generator stages through `POST /v1/training/dataset` (alias map incl. gaussian/checkerboard since W-3, juniper-cascor#490) with a post-run G-6 input-width assert (mismatch = acceptance failure). `csv_import` / `arc_agi` / the 3-D sequence family are **not** in `STAGEABLE_GENERATOR_ALIASES` and fail here before any byte cap applies.
    - Spiral joined the staged path with F-P4-1: the old spiral-only inline `dataset` source made cascor materialize its in-process fallback (unit-radius, params silently ignored) instead of the configured juniper-data dataset, terminating every service spiral run below_threshold with zero hidden units.
    - Root-cause note: [`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md`](../notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md); cascor-side fidelity fix cascor#504; candidate-param plumbing gap cascor#505.
  - Each poll samples the loopback `/metrics` allowlist (`candidate_correlation` / `hidden_units_total` / `training_loss` / `training_accuracy_ratio` / step-duration sum+count) into `artifacts/results/metrics_series.csv` -- correlation exists ONLY there, never in `/v1/metrics/history` rows; a 404 (metrics disabled, G-3) degrades sampling, not the run.
  - Recurrence drive (Wave 2.3): health-gates `/v1/health/ready`, then the **synchronous** `POST /v1/train` (the response IS completion — no poll loop; the Q-2 budget is the request's socket timeout → `timed_out`), then optional `POST /v1/predict` (`predict.from_dataset_split`, default `test`) and `POST /v1/crossval` (same LMU hyperparams as `train:` for bench comparability); every phase refs the dataset by content-addressed `dataset_id` (H-8).
  - Predict/crossval failures are recorded, and the run continues to the manifest (acceptance failure), never dying mid-evidence. `outputs.save_model: true` (G-18) re-runs the `juniper-recurrence train` CLI with `--dataset <dataset_id>` + identical hyperparam flags + `--out .../model.npz` as a manifest-recorded extra step (the CLI has no `--params` flag, so the dataset_id ref is the only faithful form).
  - Collects `metrics_final.json` / `metrics_history.json` / `topology.json` / `decision_boundary.npz` (2-D input only) + optional `POST /v1/snapshots` (cascor), `train_response.json` / `predict_response.json` / `crossval_response.json` (recurrence); ALWAYS writes the §13.4 `manifest.json` (also for stalled / timed-out / failed runs) and prints a one-screen summary.
  - **409 preempt (§3.4)**: `start_fresh: true` does NOT stop a live run — the lifecycle lock is held, so the 409 is raised before `start_fresh` is consulted, and after a driver-side stall/budget abort the naive re-run dies on `Training already in progress`. A 409 now gets ONE preemption attempt: `POST /v1/training/stop`; wait for the lifecycle to leave the active set; retry starting once.
  - Preemption is decided on **lifecycle state, not message text**: cascor's `routes/training.py:117` wraps every start failure as 409 (including "Training data not provided"), so only `STARTED` / `PAUSED` are preempted. `REPLAYING` rejects all training commands (exit is `/replay/control`) and `INVESTIGATING` needs `/retrain` / `/resume` — a stop there would fail and bury the real reason.
  - **Inert stall window**: when `--stall-seconds >=` the resolved wall budget, the Q-2 stall detector can never fire (the budget ends the run first) — a healthy long candidate phase is then labeled `timed_out` rather than `stalled`. Reported as a WARNING plus `driver.stall_window_inert` on the manifest, never fatal: the run is valid, only its guard is weaker than declared.
  - The driver is the sole place both Q-2 knobs are resolved, so it is the only layer that can see their interaction — the suite gate structurally cannot, since a budget may be inherited from `base_config` (`pf3-cascor-pool-scaling` shipped exactly this shape: a 1200 s window against a 600 s inherited budget).
  - Exit codes: 0 success / 1 acceptance (stalled, timed_out, G-6 mismatch, missing essential artifact) / 2 misuse-validation / 3 unreachable / 4 FAILED-5xx. Tests: `tests/test_run_experiment.py`.
- `util/experiments/read_run_metrics.py` -- Canonical reader for the perf-lane's two ratified inputs (P2 item 0.4). Last row of `metrics_series.csv` (`step_sum` / `step_count`); de-ratifies `wall_seconds` and `timings.drive`. `workload_fingerprint` strips cosmetic `experiment.description`/`name`. Recurrence returns `work_countable: False`. Path-invoked; `--sweep` is docstring-only. Operator surface: [Perf-Lane Work Gate](#perf-lane-work-gate). Tests: `tests/test_read_run_metrics.py`.
- `util/experiments/make_baseline.py` -- Operator-only Q-8 writer (P2 item 1.1 / P1 §4). Writes `baselines/<tag>/{baseline.json,HOST.json,manifests/}` under `--run-root` (default `~/.local/state/juniper-experiments`).
  - No `--force`; refuses failed / unmeasured / not-invariant / mixed-workload / not-countable suites.
  - `metric_contract`'s work string is **under-specified**: it still reads "deterministic for a seed-fixed config and contention-immune" without the termination-branch condition `ml#1733` established. The written `baseline.json` inherits that wording; the guard itself is correct. Known source gap.
  - Operator surface: [Perf-Lane Work Gate](#perf-lane-work-gate). Tests: `tests/test_make_baseline.py`.
- `util/experiments/compare_baseline.py` -- Split comparator (P2 item 1.2). WORK exact, SPEED reported never gated, identity first. Exit 0 PASS/WAIVED, 1 FAIL, 2 REFUSED.
  - **Do not wire to CI** — sound since ml#1743, but whether the run tier gates at all is an open OWNER decision (P1 design §6).
  - Writer refusals the comparator still lacks: unmeasured cells, `timed_out` cells, zero-work, `--suite` collapse, duplicate-fingerprint last-wins, unchecked scenario coverage.
  - Operator surface: [Perf-Lane Work Gate](#perf-lane-work-gate). Tests: `tests/test_compare_baseline.py`.
- `util/experiments/stats_summary.py` -- Wave 2.6 SS8.3 renderer (not a CLI; no `__main__`). `build_stats` / `render_summary_md` write `juniper-experiment-stats/1`. Recurrence duration lives under `outcome.timings`, not `recurrence.*`. `scrape_confirmed` is tri-state. Operator surface: [Experiment Stats Summary (SS8.3)](#experiment-stats-summary-ss83). Tests: `tests/test_run_experiment.py` (`StatsSummaryUnitTest`).
- `util/experiments/compare_baseline.py` -- Split comparator (P2 item 1.2 / juniper-ml#1622). Identity first (`workload_fingerprint`), then work (`step_count` exact → PASS/FAIL), speed reported and never gated.
  Exit `0` PASS or WAIVED / `1` FAIL / `2` REFUSED. `--accept-work-change REASON` blesses a work change only (never a refusal; whitespace-only is exit 2). Host `cpu_model` / `cpu_count` / `thread_budget` block; torch/numpy/`python_runs` are advisory.
  Tests: `tests/test_compare_baseline.py`. Operator surface: [Perf-Lane Split Comparator](#perf-lane-split-comparator).
- `util/experiments/run_suite.py` -- Suite driver. `EXECUTION_KEYS` forwards **both** Q-2 budget knobs to the driver: `execution.stall_seconds` → `--stall-seconds` (ml#1069) and `execution.max_wall_seconds` → `--max-wall-seconds`. Absent key ⇒ flag omitted entirely, so the driver keeps owning its default.
  Wave 7.3 instruments: [§ PF Scenario Suites](#pf-scenario-suites). `include` cells carry only their own overrides and do **not** inherit `matrix` (`expand_cells`) — PF-1's repeats are a matrix axis for that reason.
  - Do not confuse `execution.max_wall_seconds` with `execution.per_run_timeout_seconds`: the latter is only the **subprocess** timeout, which kills the driver from the OUTSIDE and records `timed_out` where the driver would otherwise write an honest `timed_out` manifest (§13.4). Size `per_run_timeout_seconds` ABOVE the wall budget so the driver is the one that stops.
  - A suite could always reach the budget through a dotted `outputs.max_wall_seconds` override (`suites/p4/e-i-cascor-cap-ceiling.yaml:71` does exactly that), but before this key, an un-overridden cell silently inherited `base_config`'s value — 3600 s for `spiral-baseline` — with no signal. Both mechanisms are accepted by the R-6 gate. Tests: `tests/test_run_suite.py`.
  - **`include` does not inherit `matrix`.** Empty matrix still yields one cell per `base_config`. P4 catalog + the cap-128 n=2 trap: [P4 Campaign Suites](#p4-campaign-suites).
- `util/experiments/read_run_metrics.py` -- Canonical reader for the cascor perf-lane gate inputs (P2 item 0.4). Reads the last `metrics_series.csv` step-duration row (`step_count` / `step_sum`); `summarise().work_invariant` is true iff every cell shares one count.
  - `timings.drive` and `aggregate.csv` `wall_seconds` are de-ratified. `--sweep` is docstring-only, not a flag.
  - juniper-ml#1613 adds `workload_fingerprint()` (strips `experiment.description`/`name`, keeps `seed`) and `summarise().single_workload`.
  - Operator surface: [Perf-lane metrics and baselines](#perf-lane-metrics-and-baselines). Tests: `tests/test_read_run_metrics.py`.
- `util/experiments/make_baseline.py` -- Operator-invoked Q-8 baseline writer (P2 item 1.1). Writes `baselines/<tag>/{baseline.json,manifests/,HOST.json}`; no `--force`; refusals exit 2.
  - Refuses failed / unmeasured / broken work invariant / `validation_warnings`. `--accept-warnings` is recorded.
  - juniper-ml#1613 also refuses mixed workloads and stores `workload_fingerprint`. Never called from `run_suite.py` / `run_experiment.py`.
  - Tests: `tests/test_make_baseline.py`. Operator surface: [Perf-lane metrics and baselines](#perf-lane-metrics-and-baselines).
- `util/experiments/list_runs.py` -- Safety-gated lister / pruner for experiment `RUN_DIR`s (Wave 7.2, plan §13.3). Directory-truth: scans convention-named children of `--run-root`; does **not** read `run_suite`'s `index.jsonl` and does **not** honor `JUNIPER_EXP_RUN_ROOT` (pass `--run-root`). States `down` / `up?` / `stale`; `--prune` deletes only `down`/`stale` and only with `--yes` (never under `--dry-run`; never `up?`). Distinct from `--down`, which keeps `artifacts/`. Tests: `tests/test_list_runs.py`. Operator surface: [Run lister / pruner](#run-lister--pruner-list_runspy).
- `util/snapshot_index.py` -- Read-only archive index + query (design §6.2). `--scan` is append-only over `root/*.h5`; `--verify` opts into cascor's own verifier; `dataset_id` is a query-time join on `JUNIPER_EXP_RUN_ROOT`. No `--prune`. Tests: `tests/test_snapshot_index.py`. Operator surface: [Snapshot Sidecar Chain](#snapshot-sidecar-chain).
- `util/snapshot_classify.py` -- Staged two-axis classifier over the index (handoff §2.4). `--stage load` uses cascor's loader; `--stage train` is unimplemented and refuses without a scratch `JUNIPER_CASCOR_SNAPSHOTS_DIR`; `--write` refuses `--sample`. Tests: `tests/test_snapshot_classify.py`. Operator surface: [Snapshot Sidecar Chain](#snapshot-sidecar-chain).
- `util/snapshot_backfill.py` -- Consolidates index + classification + attribution into one labelled record (handoff §3.4). Population claims stay in their own bucket; run identity is never invented. Tests: `tests/test_snapshot_backfill.py`. Operator surface: [Snapshot Sidecar Chain](#snapshot-sidecar-chain).
- `util/experiments/compare_baseline.py` -- Split comparator (exit 0 PASS/WAIVED, 1 FAIL, 2 REFUSED). Recurrence overlay (juniper-ml#1683): refuses a candidate with no countable work; `--accept-work-change` cannot override REFUSED. Cascor WORK/SPEED/host contract: [#1628](https://github.com/pcalnon/juniper-ml/pull/1628). Tests: `tests/test_compare_baseline.py`.
- `util/snapshot_attribute.py` -- Read-only dataset attribution over the classification sidecar (handoff §3.2). Scores each loadable snapshot against the six 2-D generators with permutation-corrected accuracy, gated on the untrained-null **max** plus a schema-v2 cross-dataset floor.
  - **Dataset instance must be pinned** or the scores are not reproducible: five generators declare `seed=None` and redraw every call.
  - `seeded_params` (juniper-ml#1333) supplies `DATASET_SEED` (`20260824`) only where a generator declares none; spiral keeps its declared seed; `--dataset-seed` overrides; `--seed` only samples snapshots. `--write` refuses `--sample`/`--min-hidden`. Tests: `tests/test_snapshot_attribute.py`. Operator surface: [Snapshot Attribution Dataset Pin](#snapshot-attribution-dataset-pin).
- `util/ad-hoc/e2e_f037_render_census.py` -- Multi-session F-CANOPY-037 topology-paint census. Default 11 sessions (the finding's sample); verdicts from structured `topodiag` JSON only; exit 2 means the census failed to measure, not a low paint rate. Operator surface: [F-CANOPY-037 Render Census](#f-canopy-037-render-census).
- `util/get_cascor_*.bash` -- Cascor REST API query utilities (status, metrics, history, network, topology). These helpers read legacy `CASCOR_HOST` and `CASCOR_PORT` environment variables (with `localhost` / `8201` defaults). Do not confuse them with the `JUNIPER_CASCOR_*` variables used by `util/juniper_plant_all.bash`.

---

## Repository Structure Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

```bash
juniper-ml/
├── AGENTS.md                  # This file (CLAUDE.md is a symlink to this)
├── CHANGELOG.md               # Version history (Keep a Changelog format)
├── LICENSE                    # MIT License
├── MANIFEST.in                # Source distribution includes
├── README.md                  # PyPI landing page content
├── pyproject.toml             # Package metadata, version, dependency extras
├── claudey                    # Symlink -> scripts/claude_interactive.bash
│
├── .claude/                   # Custom-agent suite surface (git-tracked via .gitignore negation; design D-6)
│   ├── agents/
│   │   ├── prompt-validator.md  # PR 3: headless validator subagent (applies RUBRIC R1-R5 -> pinned typed JSON verdict)
│   │   ├── planner.md           # Round-2: Planning subagent -> design/plan/analysis doc in notes/ (read-heavy + Write)
│   │   ├── auditor.md           # Round-2: Audit subagent -> findings report in notes/ (read-heavy + WebFetch + Write)
│   │   ├── mock-seam-auditor.md # E-5: read-only masked-seam hunter (autouse/session mocks of an integration boundary)
│   │   ├── task-executor.md     # Round-2: Task subagent -> code changes via PR (worktree isolation; may fan out)
│   │   └── fleet-supervisor.md  # Flood §4 item 7: read-only open-PR-set triage (predicted-merge via util/fleet_triage; cluster/order/dup; never pushes)
│   └── skills/
│       └── template-agent/SKILL.md  # PR 5: interactive orchestrator Skill (bounded state machine; opus + effort max)
│
├── .github/
│   ├── CODEOWNERS             # Code ownership (@pcalnon)
│   ├── dependabot.yml         # Automated dependency updates (pip + actions)
│   └── workflows/
│       ├── ci.yml             # Main CI pipeline (pre-commit, tests, build, docs, security)
│       ├── main-verify.yml    # Post-merge main verification (G3: symbol/docs-loss screen + gated battery + notify)
│       ├── publish.yml        # PyPI publishing (TestPyPI + PyPI, OIDC)
│       ├── docs-full-check.yml# Weekly full documentation link validation (cross-repo; ECOSYSTEM_REPOS clone list)
│       ├── security-scan.yml  # Weekly pip-audit --strict security scanning
│       ├── lockfile-update.yml# Weekly juniper-generate-dep-docs -> chore/lockfile-update PR
│       ├── codeql.yml         # Python semantic SAST; required context Analyze (python); SHA-grouped Dependabot bumps
│       ├── ci-*.yml           # Six shared sub-package CIs (ci-tools/config-tools/doc-tools/model-core/observability/service-core)
│       ├── publish-*.yml      # Six shared sub-package PyPI publishers (Release-tag-prefix guarded)
│       ├── release-train.yml  # Daily PyPI release-train detection (report-only, Phase 1)
│       └── claude.yml         # Claude Code action for issue/PR automation
│
├── .serena/                   # Serena code agent integration config
│   └── project.yml            # Project: juniper_ml, language: python
│
├── juniper-ci-tools/          # Published sub-package: dependency-docs generator (juniper-generate-dep-docs)
├── juniper-config-tools/      # Published sub-package: env-prefix migration helpers (stdlib-only)
├── juniper-doc-tools/         # Published sub-package: markdown link validator (juniper-check-doc-links)
├── juniper-model-core/        # Published sub-package: model-core conformance kit + crossval layer
├── juniper-observability/     # Published sub-package: shared prometheus/middleware/logging helpers
├── juniper-service-core/      # Published sub-package: shared FastAPI service-tier primitives
│
├── docs/                      # User-facing documentation
│   ├── DOCUMENTATION_OVERVIEW.md           # Navigation index for all docs
│   ├── QUICK_START.md                      # Installation and verification guide
│   ├── REFERENCE.md                        # Extras, compatibility, env vars, service ports
│   └── DEVELOPER_CHEATSHEET_JUNIPER-ML.md  # Quick-reference card for development tasks
│
├── conf/                      # Project configuration files
├── images/                    # Project branding (logos v0-v9 in PNG/XCF/ICO, tree photos)
├── logs/                      # Runtime log output (.gitkeep)
├── papers/                    # Research papers and references
├── reports/                   # Per-run evidence artifacts (e2e/<RUN_ID>/statuses.tsv; soak/pointer_follow_soak.jsonl — pointer-follow soak ledger)
├── resources/                 # External resources (AppImages, etc.)
│
├── notes/                     # Development notes, plans, and procedures
│   ├── JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md       # Worktree creation procedure
│   ├── JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md  # Worktree cleanup procedure (CWD-safe)
│   ├── JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md       # Thread handoff protocol
│   ├── JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md        # Secrets encryption guide
│   ├── backups/               # Backup analysis/plan documents
│   ├── concurrency/           # Concurrency-related handoff notes
│   ├── development/           # Development analysis documents
│   ├── documentation/         # Documentation audit plans
│   ├── history/               # Historical plans and procedures
│   ├── proposals/             # Research proposals
│   ├── pull_requests/         # PR description archives
│   └── templates/             # Document templates (roadmap, issue, PR, release notes)
│
├── prompts/                   # Claude Code session prompts (chronological archive)
│   ├── agent_templates/       # Custom-agent prompt templates: manifest.yaml + generic.md + RUBRIC (drift-linted)
│   │   └── data/              # PR 6b: data layer (standing_rules/anti_hallucination/conventions/ecosystem/known_misses .yaml)
│   └── generated/             # PR 5: emission target for /template-agent output (.gitkeep)
│
├── scripts/                   # Claude Code launcher and test scripts
│   ├── wake_the_claude.bash              # Core launcher: flag parsing, session persistence, resume
│   ├── claude_interactive.bash           # Interactive Claude Code agent launcher
│   ├── default_interactive_session_claude_code.bash  # Config template for interactive sessions
│   ├── activate_conda_env.bash           # Conda environment management
│   ├── resume_session.bash               # Session resume convenience wrapper
│   ├── cleanup_session_worktrees.py      # Bulk-clean Claude Code session worktrees in .claude/worktrees/
│   ├── test.bash                         # End-to-end test harness for launcher flows
│   ├── test_resume_file_safety.bash      # Regression: invalid --resume input safety
│   ├── test_prompt-*.md                  # Test prompt files for launcher testing
│   ├── sessions/                         # Session ID storage (.gitkeep)
│   └── backups/                          # Backup copies of older script versions
│
├── tests/                     # Regression test suites (Python unittest)
│   ├── test_wake_the_claude.py           # Launcher script regression (1470 lines)
│   ├── redacted_env.py                   # RedactedEnv helper: subprocess env mapping with masked repr (secret-leak class)
│   ├── test_env_repr_safety.py           # Lint gate: no raw os.environ-derived subprocess env in tests/ + RedactedEnv behavior
│   ├── test_worktree_cleanup.py          # Worktree cleanup script tests (225 lines)
│   ├── test_worktree_sweep_scripts.py    # Ad-hoc sweep script safety/contract tests
│   ├── test_p5_worktree_cleanup.py       # P5 worktree sweeper: PR-lookup naming, disposable vs harvest, cwd-only occupancy
│   ├── test_cleanup_session_worktrees.py # Session .claude/worktrees cleaner (merged-PR fail-closed + dry-run)
│   ├── test_reap_pytest_orphans.py       # Orphan pytest process reaper tests
│   ├── test_soak_ledger.py               # Pointer-follow soak ledger (seeded arm, Wilson verdicts, escalations)
│   ├── test_soak_next_probe.py           # Unprimed soak dispatcher (stdout = task only)
│   ├── test_soak_run_probe.py            # Soak wrapper (hermetic parse + retrieval channel; never launches claude)
│   ├── test_kill_helpers.py              # Emergency kill helpers: process-filter / kill-path (hermetic PATH stubs)
│   ├── test_check_conda_env_torch.py     # Hermetic P-5 torch._C shadow diagnostic exit matrix (0/1/2/3/4)
│   ├── test_memory_index_check.py        # Hermetic MEMORY.md index gate (missing file = 2; hook-not-line; grandfathered oversize)
│   ├── test_requirements_drift_check.py  # Requirements snapshot drift checker tests
│   ├── test_requirements_consolidate.py  # Live-tree gate: util/requirements_consolidate.py v5 refresh (round-trip + derived-view projection + incoming-only dedup)
│   ├── test_editable_install_drift_check.py # Editable-install drift checker tests (orphaned / worktree-pinned)
│   ├── test_env_floor_drift_check.py     # Lint/behavioural: util/env_floor_drift_check.py floor-drift (I-2; synthetic dist-info)
│   ├── test_prompt_discovery.py          # Behavioural: util/prompt_discovery/ grounding-bundle (schema + provenance + cold/empty)
│   ├── test_symbol_overlay.py            # Serena symbol overlay (OQ-8) deterministic merge (Serena wins, grep fallback)
│   ├── test_generated_prompt_index.py    # Behavioural: util/generated_prompt_index.py index + safety-gated prune/archive (P4)
│   ├── test_thread_handoff_archive.py    # Drift: archived handoff prompt filenames + top-level note references
│   ├── test_install_agents.py            # Behavioral: util/install_agents.bash ~/.claude mirror (idempotent/reversible/dry-run/no-clobber)
│   ├── test_agent_suite_doctor.py        # Behavioural: util/agent_suite_doctor.py suite health check (dogfood; consumes every layer)
│   ├── test_agent_suite_summary.py       # Behavioural: util/agent_suite_summary.py suite quick-reference (P3)
│   ├── test_predict_merge.py             # Behavioral: util/fleet_triage/predict_merge.py predicted-merge (4 verdicts, TRUE-delta, cluster/order, no-mutate, exit codes; hermetic)
│   ├── test_fleet_supervisor_contract.py # Lint: fleet-supervisor subagent frontmatter + body wiring (predict_merge.py, 4 verdicts, read-only/never-push, two-key DUP-CLOSE)
│   ├── test_workflow_script_paths.py     # Lint: every .github/workflows/*.yml script path exists
│   ├── test_doc_tools_drift.py           # Lint: consumer-repo juniper-doc-tools pins still admit current version (plan §5.1)
│   ├── test_service_fork_drift.py        # Drift gate: security guards that must not diverge across the data/cascor service-core forks (register §2.3; ENFORCED + self-maintaining KNOWN_GAP ledger)
│   ├── test_publish_env_policy_drift.py  # Drift gate: publish envs stay tag-only ref-gated (publish-path design §6/§12); settings-not-code, so nothing else would notice a deletion
│   ├── test_publish_testpypi_verify.py   # Structural + hermetic: publish.yml Gate 1 two-phase verify + bounded TestPyPI poll (no sleep 30; #1310)
│   ├── test_publish_release_only_trigger.py # Glob gate: every publish*.yml is release: published only (no push:; no push-gated steps; #1310 / #555)
│   ├── test_assert_release_tag.py        # Behavioural + wiring: util/assert_release_tag.bash (P3) — tag-shape + tag<->built-wheel version, and that all 7 publishers invoke it with the right prefix
│   ├── test_pyproject_extras.py          # Lint: pyproject [project.optional-dependencies] surface matches the contract
│   ├── test_template_library_drift.py    # Lint: custom-agent template library (prompts/agent_templates/) manifest <-> templates
│   ├── test_template_selection.py        # Lint: custom-agent template match_signals selection coherence
│   ├── test_template_select_preview.py   # Behavioural: util/template_select_preview.py offline match_signals selector (P2)
│   ├── test_template_data_resolver.py    # Tests + drift gate: data layer (prompts/agent_templates/data/) + resolver
│   ├── test_scaffold_template.py         # Behavioural: util/scaffold_template.py new-template generator (P5; drift-compliant output)
│   ├── test_open_signed_pr.py            # Behavioural: util/open_signed_pr.py signed cross-repo PR opener (hermetic gh stub; dry-run/dup-guard/refs-ref=/deletions)
│   ├── test_wait_for_checks.py           # Behavioural: util/wait_for_checks.py required-context CI waiter (hermetic scripted-gh stub; positive-terminal, growing-rollup + observed-anchor negative control, absent-vs-running, hard-error, read-only)
│   ├── test_experiment_stack_script.py   # Contract + behavioural: util/experiment_stack.bash per-run launcher (§6.1 recipes, §6.4 RUN_DIR, §7.2 target file, §9.3 ranges, F-6 listener pid, dry-run + teardown, APD-DATA-018 data_up does not set IMPORT_DIR/MAX_BYTES/ALLOW_TRUNCATION; hermetic)
│   ├── test_read_run_metrics.py          # Hermetic: util/experiments/read_run_metrics.py last-row step_count/step_sum, fingerprint, work_invariant over measured cells, recurrence not countable
│   ├── test_make_baseline.py             # Hermetic: util/experiments/make_baseline.py Q-8 writer refusals (no --force, unmeasured/failed/not-invariant/mixed-workload)
│   ├── test_compare_baseline.py          # Hermetic: util/experiments/compare_baseline.py split comparator (exact work, ungated speed, identity-first REFUSE, 0/1/2 exits, A1-A7 refusal ladder closed by ml#1741 + ml#1743)
│   ├── test_run_suite.py                 # Behavioral: util/experiments/run_suite.py suite driver (expansion + cell_ids, per_cell seeds, driver-validated cells, stubbed up/drive/down loop, registry/index/aggregate, resume, both Q-2 budget flags, JUNIPER_SUITE_GRAFANA_BRIDGE env toggle; hermetic). PF instruments: § PF Scenario Suites
│   ├── test_require_context_safely.py    # Hermetic: ad-hoc ruleset writer (find_ruleset error-vs-absence, TARGETS↔census roster, observed_context_apps amend pre-flight)
│   ├── test_ruleset_scope_guard.py       # Hermetic: util/ruleset_scope_guard.py ~ALL-scope guard (narrow pass, ~ALL fail names 29110 rows, empty list / probe failure exit 2 not 0, bypass_actors pin, FLEET lockstep)
│   ├── test_list_runs.py                 # Behavioral: util/experiments/list_runs.py lister/pruner (state classification, --older-than, prune safety gates; hermetic RUN_ROOT fixtures)
│   ├── test_snapshot_index.py            # Behavioral: util/snapshot_index.py snapshot index/query (design §6.2) — bytes-attr decode, append-only rescan, --limit deferred-vs-present counting, D-C provenance filters, and an AST anti-resurrection guard that the tool stays READ-ONLY (retention is §6.4 and gated)
│   ├── test_snapshot_classify.py         # Behavioral: util/snapshot_classify.py owner-scheme classifier (handoff 2026-08-22 §2.4) — the two-axis category/health rule (incl. the attributed zero-node row that made category 5 read empty), `readable`-is-not-loadable, iterations-not-epochs (inert meta.current_epoch), replace-not-append sidecar, fd-level stdout muffling, the train-stage scratch-root refusal, and an AST anti-resurrection guard that the tool stays READ-ONLY
│   ├── test_snapshot_attribute.py        # Behavioural: util/snapshot_attribute.py dataset attribution (handoff §3.2) — permutation-corrected scoring (raw accuracy reports an inverted-label network as BELOW chance; archive snapshots at 0.010 are 0.990 inverted), the null floor being the untrained MAXIMUM rather than its p95 (a zero-hidden-unit network is a linear model yet scored ~0.624 on non-linearly-separable checkerboard, inside the tail a 120-sample null cannot characterise), the SECOND (cross-dataset) floor — a candidate must clear both, because the untrained null only asks "did this learn anything?" while attribution needs "did it learn THIS rather than something else?" — that a snapshot may not help set the bar it is judged against (a perfect 1.000 on moon must not be recorded as confidently circles), that a dataset an untrained network aces (gaussian, floor 1.000) can never be an answer, ambiguity/missing-null refusals, the partial-sidecar --write guards, and an AST read-only guard. Hermetic — no cascor tree, no juniper-data tree, no archive
│   ├── test_snapshot_backfill.py           # Behavioural: util/snapshot_backfill.py consolidated recovered-metadata record (handoff §3.4) — the caveats ARE the feature. Pins that a SAMPLED cohort result (380 of 15,927 zero-node snapshots trained) stays quarantined in the `population` bucket rather than being written onto 15,547 files nobody trained, that an inferred dataset never reads as observed/measured, that run identity is never invented (zero run dirs survive from before 2026-07-30), that every failing snapshot gets a named root cause, and an AST read-only guard
│   ├── test_run_experiment.py              # Behavioural: util/experiments/run_experiment.py cascor + recurrence driver (§6.3 drive loops, Q-2 stall/budget, F-1 redirect sampling, G-6 staging, csv_import 422/unstageable, §5.5 blocks + G-18 save_model, §8.1/§8.2 plot sets, §8.3 stats/summary, §13.4 manifest, exit matrix 0-4; hermetic stub HTTP)
│   ├── test_read_run_metrics.py            # Hermetic: util/experiments/read_run_metrics.py last-row step_count, scrape tri-state, work_invariant; #1613 workload_fingerprint (cosmetic vs seed, None ≠ shared identity)
│   ├── test_make_baseline.py               # Hermetic: util/experiments/make_baseline.py Q-8 writer refusals (no --force, work invariant, warnings recorded); #1613 mixed-workload refuse + fingerprint
│   ├── test_compare_baseline.py            # Hermetic: util/experiments/compare_baseline.py split comparator (P2 1.2) — exit 0/1/2 distinct, speed cannot fail, waiver cannot mask REFUSED (#1622)
│   ├── test_experiment_config_schemas.py   # Drift gate (Wave 3.5): sibling conf/experiments/*.yaml ↔ driver load_config + AST-extracted app Settings fields (CI/force-local gated; always-on extractor self-check)
│   ├── test_experiment_suite_yamls.py      # Drift gate (R-6): every util/experiments/suites/**/*.yaml passes run_suite.load_suite + oversize cascor suites (pool >= 16 OR cap >= 64) declare execution.stall_seconds (ml#1069) + wide-cap suites pin a wall budget + per_run_timeout > wall (pf5 was 900/900); PF instruments: § PF Scenario Suites
│   ├── test_p5_fleet_state.py              # Behavioral: util/ad-hoc/2026-08-26_p5_fleet_state.py census (invocation --advisory, 404-only-None, CHAR vs BYTE, exact Memory Budget required match; hermetic)
│   ├── test_resident_gap_triage.py         # Hermetic: util/ad-hoc/2026-08-31_resident_gap_triage.py block score / gap predicate / log-level demotion (the leftover #1663 cannot see)
│   ├── test_resident_gap_scan.py           # Hermetic: util/ad-hoc/2026-08-28_resident_gap_scan.py IDENT / .claude/worktrees skip / CLI exit 2 (the leftover #1663/#1697 cannot see)
│   ├── test_prompt_validator_contract.py   # Lint: prompt-validator subagent frontmatter + pinned verdict schema/fixtures
│   ├── test_template_agent_skill_lint.py   # Lint: template-agent Skill frontmatter + wiring to real artifacts (PR 5)
│   ├── test_service_smoke_skill_lint.py    # Lint: service-smoke Skill frontmatter (declared browser MCP for opt-in --ui, NO Agent) + teardown wiring (E-1 Stage 1/2)
│   ├── test_ui_test_author_skill_lint.py   # Lint: ui-test-author Skill frontmatter (Write + declared browser MCP, NO Agent) + models canopy src/tests/ui/ + teardown (E-6)
│   ├── test_agents_frontmatter.py          # Lint: every .claude/agents/*.md honours the suite frontmatter contract (opus+max)
│   ├── test_agents_md_version_drift.py     # Lint: AGENTS.md **Version** header matches pyproject.toml [project].version
│   ├── test_agents_md_header_schema.py     # Lint: AGENTS.md canonical header schema (6 required fields, ISO date format)
│   ├── test_agents_md_tree_drift.py        # Lint: every tracked top-level dir appears in the Repository-Structure tree (G-3)
│   ├── test_coverage_gap_mapper_drift.py   # Dogfood/drift (E-4): juniper-coverage-gap-map console script registered + version/pin coherent (ci-tools)
│   ├── test_env_drift_check_drift.py       # Dogfood/drift (§10.1): juniper-env-drift-check entry point registered + every cli*.py wired (0.5.1 #580-clobber guard)
│   ├── test_release_train_registry.py      # Lint + drift gate: util/release_train/registry.yaml (18 packages/8 repos/enums) <-> pyproject resolution (plan §4.1) + the ml#701 static-package pyproject==dunder lockstep gate
│   ├── test_release_train_detect.py        # Behavioral: util/release_train/detect.py detection engine (classifications, substantive-hunk, SemVer, exit codes; hermetic)
│   ├── test_release_train_propose.py       # Behavioral: util/release_train/{propose,notes_render}.py proposal-PR generator (dry-run bump+CHANGELOG move+notes, dup-guard, conflict refusal; hermetic) (plan §5.4)
│   ├── test_release_train_archive_guard.py # Behavioral: util/release_train/archive_guard.py exempt notes-archive structural guard (add-only/path-confined/name-valid/single-purpose; SKIP for non-archive; hermetic) (plan §7.2 / step 3.1)
│   ├── test_release_train_ceremony.py      # Behavioral: util/release_train/ceremony.py exempt-archive + Release ceremony (§8 HALTs, happy-path, signed-archive HALT/parse edges, dup-guard/idempotent, R7 gh-surface, dry-run; hermetic) (plan §7/§8/§9.3 / step 3.2)
│   └── fixtures/
│       └── prompt_validator/             # PR 3: verdict.schema.json + verdict.sample.{pass,fail}.json (validator contr
│                                         # Doc-link validator regression tests moved to juniper-doc-tools/tests/
│                                         # (Wave 4 of the doc-link migration plan; published under the dedicated
│                                         #  juniper-doc-tools PyPI package).
│
└── util/                                 # Utility scripts and tools
    ├── ad-hoc/                           # Single-use/temporary/unfinished scripts (see ad-hoc/README.md); 2026-08-10_ruleset_context_audit.py = required-context fleet classifier (REFERENCE § Ruleset Context Audit)
    ├── assert_release_tag.bash           # Publish guard (P3): ref must be a TAG, and the tag's version must match the wheel actually built
    ├── open_signed_pr.py                 # Cross-repo: open a PR on any Juniper repo with a GitHub-SIGNED commit (createCommitOnBranch)
    ├── wait_for_checks.py                # Cross-repo: wait for a PR's REQUIRED status checks (ruleset-anchored) to finish; read-only, exit 0/1/2/3
    ├── requirements_drift_check.py       # Drift checker for the requirements snapshot (--mode quick)
    ├── requirements_consolidate.py       # v5 refresh: by-area is corpus of record; --check-roundtrip / --check-views / --merge / --regenerate-views (default dry-run)
    ├── editable_install_drift_check.py   # Drift checker for juniper editable installs across conda envs
    ├── env_floor_drift_check.py          # Floor-drift checker: installed juniper-* vs target-repo pyproject floors (I-2)
    ├── check_conda_env_torch.bash        # P-5 / May-7 torch._C shadow diagnostic (exit 0/1/2/3/4; does not rebuild)
    ├── memory_index_check.py             # MEMORY.md index gate (option A): 200 lines / 25k UTF-8 bytes; new-row hook len() vs 120; --accept samples history
    ├── release_train/                    # PyPI release-train: registry.yaml (18-package registry) + detect.py (report-only "needs deploy?" engine, Phase 1) + propose.py/notes_render.py (manifest -> proposal-PR content, dry-run, Phase 2.1) + archive_guard.py (exempt notes-archive PR structural guard, Phase 3.1) + ceremony.py (exempt-archive + Release ceremony, dry-run, Phase 3.2)
    ├── prompt_discovery/                 # Custom-agent suite (PR 4): env-discovery probes -> JSON grounding bundle (path-invoked, --repo-root)
    ├── fleet_triage/                     # Flood §4 item 7 (Stage-0 supervisor script layer): predict_merge.py -- detached-clone predicted-merge per PR (4 verdicts, TRUE delta, cluster map + order; delegates the 2 screens to juniper-ci-tools console scripts); --pr N | --batch, exit 0/2
    ├── generated_prompt_index.py         # Custom-agent suite (P4): index + safety-gated prune of prompts/generated/
    ├── template_data_resolver.py         # Custom-agent suite (PR 6b): loads prompts/agent_templates/data/*.yaml (data-layer resolver)
    ├── template_select_preview.py        # Custom-agent suite (P2): offline preview of the Template Agent's match_signals selection
    ├── install_agents.bash               # Custom-agent suite (PR 6a): mirror .claude/{agents,skills} -> ~/.claude (idempotent, reversible)
    ├── scaffold_template.py              # Custom-agent suite (P5): generate a new prompts/agent_templates/ template + manifest stanza
    ├── agent_suite_doctor.py             # Custom-agent suite: read-only health check (dogfood; OK/WARN/FAIL over every layer)
    ├── agent_suite_summary.py            # Custom-agent suite (P3): quick-reference listing of agents + templates
    ├── worktree_cleanup.bash             # V2 cleanup orchestrator (CWD-safe)
    ├── ruleset_scope_guard.py            # Token-free GET-only ~ALL-scope guard (Quality Gate hard need; bypass rows NOT checked)
    ├── worktree_new.bash                 # Creates new git worktree
    ├── worktree_activate.bash            # Bash helper for worktree activation
    ├── worktree_close.bash               # Removes a worktree, branch, and prunes
    ├── worktree_wipeout.bash             # Bulk removal by pattern
    ├── remove_stale_worktrees.bash       # Removes all stale worktrees
    ├── cleanup_open_worktrees.bash       # Removes all active worktrees
    ├── prune_git_branches_without_working_dirs.bash  # Branch hygiene
    ├── juniper_plant_all.bash            # Starts all Juniper ecosystem services
    ├── juniper_chop_all.bash             # Stops all Juniper ecosystem services
    ├── juniper-backup.bash               # Per-repo project-tree archive (tar -cjf | gpg -e); build-once, copy ciphertext. Operator surface: Juniper Project-Tree Backup
    ├── snapshot_index.py                 # Snapshot archive index + query (design §6.2, delivers R2): --scan builds an append-only snapshots_index.jsonl per snapshot root; queries filter on the D-C provenance (--experiment/--cell-id/--run-id), tier and attribution. `dataset_id` is DERIVED, not stored — it is content-addressed on a generator version only known from a live juniper-data query after bring-up, so `--resolve-datasets` (implied by `--dataset-id`) joins run_id -> <RUN_ROOT>/<run_id>/manifest.json instead; opt-in because it reads outside the snapshot root. READ-ONLY BY CONSTRUCTION — no prune/delete path, because retention is §6.4 and gated on this index existing; an AST test enforces it. Records which groups a file belongs to rather than judging validity, so cascor retains sole ownership of the format policy (--verify opts into cascor's own verifier).
    ├── snapshot_classify.py             # Snapshot classifier over the §6.2 index (handoff 2026-08-22 §2.4). STAGED because the five categories cost between a second and CPU-days: `--stage index` (~1s) settles categories 4/5; `--stage load` asks cascor's OWN `load_network_result` and settles category 1 (~15 min, 27.9k files); `--stage train` is deliberately unimplemented (item 3) and refuses without a scratch $JUNIPER_CASCOR_SNAPSHOTS_DIR, because `train_output_layer` calls `create_snapshot()` unconditionally and would grow the archive under study. Emits TWO axes — `category` (must we reconstruct this snapshot's metadata?) and `health` (what can the artifact do?) — because the owner's five categories are not a partition and a literal first-match reading leaves category 5 unreachable. Reports `iterations_lower_bound` from arch.num_hidden_units, never an epoch count (meta.current_epoch is INERT: nonzero in 0 of the 28,040 archive files censused 2026-08-26, with best_value_loss inf in 27,907 of them — but NOT `snapshot_counter`, nonzero in 13,001 of 28,040, which the docstring no longer calls dead and which a regression test now pins as live-but-still-not-the-bound; the archive-vs-current split is a WRITER-PATH split, not a serializer-version one — 28,034 archive files are already serializer_version 2.0.0, and `current_epoch` present ⟺ best_value_loss inf holds without exception across all 30,948 files measured; re-derive with `util/ad-hoc/2026-08-26_snapshot_meta_field_survey.py`). Writes only a derived, replace-not-append snapshots_classification.jsonl sidecar, read back by `--from-sidecar` in ~0.5s (without it the tool could WRITE a verdict it could not READ -- only the load stage sets `fails_to_load`, so a later `--category fails_to_load` re-derived from the index and reported "no matching snapshots" against a sidecar holding 526 of them). READ-ONLY over snapshots, AST-enforced, with no prune path because retention is §6.4 and gated on this output
    ├── snapshot_attribute.py            # Dataset attribution over the classification sidecar (handoff §3.2): which dataset was each snapshot trained on? Scores every shape-compatible juniper-data 2-D classification generator (spiral/xor/gaussian/circles/moon/checkerboard) with a PERMUTATION-CORRECTED accuracy — one-hot column order is an arbitrary convention, so a network that learned a set with swapped columns scores 1-p and raw accuracy reads it as below chance. Gated against an UNTRAINED-NETWORK NULL per (input, output) shape, because 'beats chance' is not evidence here: an untrained net already beats chance on Gaussian by +0.408 (up to a perfect 1.000), so Gaussian is structurally unattributable. The floor is the null's observed MAX, not p95 — zero-hidden-unit linear models scored ~0.624 on checkerboard, inside the tail a 120-sample null cannot characterize. SECOND FLOOR (schema v2): that untrained null only answers 'did this learn anything?', so a cross-dataset empirical floor built from snapshots attributed ELSEWHERE answers 'did it learn THIS rather than something else?', and a candidate must clear BOTH; a snapshot is excluded from the bar it is judged against, since one that tops a rival's floor with its own score would suppress that rival. `--no-cross-dataset-floor` restores the single-floor behaviour. DATASET INSTANCE IS PINNED: 5 of the 6 generators declare `seed: int | None = Field(default=None)`, so building them from bare defaults REDREW the data on every call and attribution was not reproducible — two `load_datasets` calls in one process returned different arrays for checkerboard/circles/gaussian/moon/xor, and a rebuild moved moon's count 0 → 6 (its score shifted 1.000 → 0.995, flipping one snapshot's first-pass winner, removing it from moon's reference class, dropping moon's cross floor 1.000 → 0.850). `seeded_params` supplies `DATASET_SEED` only where a generator declares none, so spiral keeps the exact instance every prior analysis used; `--dataset-seed` overrides, and changing it redefines the canonical instance. Verdicts: attributed/ambiguous/indeterminate; on the 27,689-row seeded rebuild, 124 single-floor attributions become **108** under both floors (xor 94, circles 7, spiral 4, moon 3) plus 8 ambiguous, 0 with zero hidden units. Validated by a 4/4 positive control. A capacity-matched null was measured and is NOT the fix — it withdrew only 3, because ~100 random cascade units inject noise columns and push the score toward chance, making the matched floor LOWER than the zero-unit one (notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md). READ-ONLY; --write refuses --sample/--min-hidden so the sidecar can never silently cover a subset
    ├── snapshot_backfill.py             # Consolidates the index + classification + attribution sidecars into ONE record per snapshot (handoff §3.4 'backfill'), with every field labelled by HOW it was obtained. Four derivation levels that differ in KIND, not degree: `observed` (read from the .h5), `measured` (obtained by running the artifact — load status, per-dataset accuracy), `inferred` (a judgement from those measurements — dataset attribution, always carrying confidence/meaning/evidence/caveat), and `population` (true of the COHORT, NOT verified for this snapshot). That fourth level is the point: item 3 trained 380 of 15,927 zero-node snapshots, so writing `formerly_broken` onto all of them as fact would fabricate a per-snapshot result for 15,547 files — a confidence SCORE would have licensed exactly that. Names a root cause for all 273 failing snapshots (cohort B, truncated writes). Run identity is never invented: no run dir survives from before 2026-07-30, so absence stays absence. `--explain NAME` prints one snapshot's full provenance. READ-ONLY — writes only snapshots_backfill.jsonl beside the index and never touches a .h5 (it does not import h5py at all); no prune path, because retention is §6.4
    ├── isolated_stack.bash               # Isolated training-runtime E2E trio (data 8101 / cascor 8202 / canopy 8051): --up/--down/--status/--dry-run
    ├── experiment_stack.bash             # Per-run experiment launcher (data 8110-8139 / cascor 8230-8259 / recurrence 8260-8289): --up/--down/--status/--dry-run
    ├── experiments/                      # Experiment driver layer (Waves 2.2-2.6): run_experiment.py + plots_cascor.py / plots_recurrence.py + stats_summary.py + list_runs.py + run_suite.py + read_run_metrics.py / make_baseline.py / compare_baseline.py (Q-8 split gate — sound since ml#1743; CI-wiring is an open OWNER decision) + suites/ (7.1+7.5) + suites/perf/ (Wave 7.3 PF instruments; PF-4/PF-8 are not driver suites — § PF Scenario Suites)
    ├── get_cascor_status.bash            # GET /v1/training/status
    ├── get_cascor_metrics.bash           # GET /v1/metrics
    ├── get_cascor_history.bash           # GET /v1/metrics/history?count=10
    ├── get_cascor_history-plus.bash      # GET /v1/metrics/history?count=100
    ├── get_cascor_network.bash           # GET /v1/network
    ├── get_cascor_topology.bash          # GET /v1/network/topology
    ├── kill_all_pythons.bash             # Emergency Python process terminator
    ├── search_file_in_all_repos_and_worktrees.bash   # Cross-repo file search
    └── global_text_replace.bash          # Batch sed find-and-replace
```

---

## Pre-commit Hook Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

Setup:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Configured hooks (`.pre-commit-config.yaml`):

| Hook Group         | Version   | Scope                                            | Purpose                                                                                                                       |
|--------------------|-----------|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| pre-commit-hooks   | v4.6.0    | All files                                        | YAML/TOML/JSON check, EOF fixer, trailing whitespace, merge conflicts, large files, AST check, debug statements, private keys |
| flake8             | 7.1.1     | `scripts/`, `tests/` `.py`                       | Python linting (max-line-length: 512) with bugbear, comprehensions, simplify                                                  |
| bandit             | 1.9.4     | `scripts/`, `tests/` `.py`                       | Python security scanning                                                                                                      |
| shellcheck         | v0.10.0.1 | `.sh`, `.bash`                                   | Shell script linting (severity: warning)                                                                                      |
| markdownlint       | v0.42.0   | `.md` (excl. CHANGELOG, notes/, docs/, prompts/) | Markdown linting with auto-fix                                                                                                |
| yamllint           | v1.35.1   | YAML files                                       | YAML linting (relaxed mode)                                                                                                   |
| no-unencrypted-env | local     | `.env`, `.env.secrets`                           | Blocks unencrypted env files from commit                                                                                      |

---

## CI/CD Pipeline Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

### Main CI (`ci.yml`)

Triggered on push to `main`/`develop`/`feature/**`/`fix/**` branches and PRs to `main`/`develop`.

Jobs:

1. **pre-commit** -- Runs all pre-commit hooks (flake8, bandit, shellcheck, yamllint, markdownlint). G4 changed-files split (flood §4 item 8 phase 2): `pull_request` / `merge_group` scope to the event's changed files (`--from-ref <BASE> --to-ref HEAD`); `push` keeps `--all-files`. The 3 required `Pre-commit (Python 3.1x)` context names are unchanged.
2. **tests** -- Python unittest (`test_wake_the_claude.py`, `test_workflow_script_paths.py`, etc.) and bash regression tests
3. **build** -- Package build, twine validation, extras metadata verification
4. **docs** -- Documentation link validation (`--cross-repo skip`)
5. **security** -- pip-audit for dependency vulnerabilities
6. **dependency-docs** -- Generates dependency documentation via the `juniper-generate-dep-docs` console script from the PyPI-published `juniper-ci-tools>=0.1.0,<0.2.0` package (replaces the legacy `util/generate_dep_docs.sh` deleted in juniper-ml#298)
7. **release-train-archive-guard** (`pull_request` + `merge_group`) -- Runs `util/release_train/archive_guard.py` over the PR's changed files to prove the exempt notes-archive PR is add-only / path-confined / name-valid / single-purpose (plan §7.2 / step 3.1). SKIPs (passes) for any PR that doesn't touch `notes/releases/`, so it never blocks a normal PR; a violation fails only this check (the PR falls back to the standard owner gate).
    It also admits `merge_group` so the required context re-posts on a queued merge commit — but `merge_group` has no `github.base_ref`, so the job short-circuits to a green notice before any checkout and every real work step stays
    `if: github.event_name == 'pull_request'`. Standalone (and absent from the Quality Gate `needs:`) so the owner can later mark it a **required** status check (step 3.3). Gate: `tests/test_archive_guard_workflow.py`.
8. **sequence-safety** (`pull_request` + `merge_group`) -- Installs `juniper-ci-tools` (>=0.8.0) + runs `juniper-symbol-loss-check` (explicit ml `--scope`) + `juniper-docs-additions-check` over the PR base..HEAD (P2 G1/G2); uploads `sequence-safety-report` (G5-vi).
    Standalone, ABSENT from the Quality Gate `needs:` so its skip-on-push never fails the gate. **Required** in `juniper-ml-rules` (context `Sequence Safety`, live GET 2026-09-04) — Quality Gate green does not mean mergeable. Never fold this job into QG `needs:`. WARN-only `allow-symbol-loss` / `docs-rewrite` label hatch greens the PR check; trailers cover `main-verify`.
9. **fleet-pr-lint** (ADVISORY; `cursor/*` PRs only) -- Warnings-only signals to the step summary (P2 G5-iv; flood §4 item 8 phase 4): commit count, `black --check`, fan-out, and AGENTS.md / cheatsheet hotspot notes. Never fails, never comments.
10. **required-checks** -- Quality gate enforcing all checks must pass

### Publishing (`publish.yml`)

Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first, then PyPI (`pypi needs: testpypi`).
Gate 1 is **two-phase** (2026-08-08): a TestPyPI-only `pip download --no-deps` of the exact version (provenance; bounded poll, not `sleep 30` — juniper-ml#1310), then three installs of that **local wheel** against production PyPI only (`"${WHEEL}"`, `"${WHEEL}[clients]"`, `"${WHEEL}[tools]"`; never `--no-deps`, never `--extra-index-url`, never the heavy `[worker]` / `[servers]` / `[all]` / `[recurrence]` extras).
The `build` job skips `juniper-<pkg>-v*` tags. Gates: `tests/test_publish_testpypi_verify.py` (verify shape + poll) and `tests/test_publish_release_only_trigger.py` (trigger IS the release-convention gate).

**Publish-path authorization (all 7 publishers, 2026-08-17).** Three layers, in decreasing order of how much they survive:

1. **Environment tag policies** — the actual control. Each `pypi` / `testpypi` environment admits only release tags (`v*`, `juniper-*-v*`, `rc*`, `juniper-*-rc*`, `hf*`, `juniper-*-hf*`), so a dispatch from a branch is refused **before the job starts** and no OIDC credential is minted. It is settings, not code, so it survives a workflow edit — and is guarded by `tests/test_publish_env_policy_drift.py`.
2. **P3 `util/assert_release_tag.bash`** — the build job asserts ref-is-a-tag and tag-version-equals-built-wheel. Defense in depth: deletable by anyone editing the workflow, but fails earlier and names the reason.
3. **P4 job-scoped `id-token`** — `id-token: write` sits on the two publish jobs, never the workflow block, so the build job cannot mint a PyPI credential at all. Job-level `permissions` **replace** the workflow block rather than merging, so each publish job restates `contents: read` for its checkout.

Full design + the controls that proved it: [`notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md`](../notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md).

### Documentation Full Check (`docs-full-check.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch. Clones the siblings named in `env.ECOSYSTEM_REPOS` and runs full cross-repo documentation link validation (`--cross-repo check`), the consumer `juniper-doc-tools` / `juniper-ci-tools` pin lints plus downstream integration, and the L2/L3 `claude.yml` audit in `JUNIPER_ROOT` mode.

`ECOSYSTEM_REPOS` membership must equal the registry publishing repos minus `juniper-ml` (already the workflow checkout) plus `juniper-deploy` (a doc / `claude.yml` consumer with no PyPI package). The clone list historically omitted
`juniper-recurrence`, silently dropping that publishing sibling from every weekly screen; `tests/test_docs_full_check_ecosystem.py` now pins the membership, and `tests/test_doc_tools_drift.py` walks every consumer
`.github/workflows/*.{yml,yaml}` so a pin declared in `ci-docs.yml` (recurrence) is not skipped.

### Security Scan — workflow contract (`security-scan.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch, permissions `contents: read`. Installs the meta-package editable, then runs a **sole** `pip-audit --strict --desc on` (no `--skip-editable`). This is the hard weekly CVSS screen — distinct from the per-PR `ci.yml` `security` job, which intentionally uses `--skip-editable` and omits `--strict` so an unreleased editable meta install does not fail every PR. Do not copy either contract onto the other path. Gate: `tests/test_security_scan_workflow.py`.

### Lockfile Update — workflow contract (`lockfile-update.yml`)

Weekly schedule (Monday 08:00 UTC) and manual dispatch, permissions exactly `contents: write` + `pull-requests: write`. Installs `juniper-ci-tools` from PyPI, runs `juniper-generate-dep-docs` to regenerate `conf/requirements_ci.txt` +
`conf/conda_environment_ci.yaml`, and opens a PR on `chore/lockfile-update` (labels `dependencies` + `automated`) via SHA-pinned `peter-evans/create-pull-request` when the tree changes. A clean tree opens no PR, and the PR is reviewed
like any dependency change — never auto-merged. The legacy `util/generate_dep_docs.sh` was deleted in juniper-ml#298; this workflow must keep the console-script path. Gates: `tests/test_lockfile_update_workflow.py` +
`tests/test_ci_tools_drift.py`.

### Release Train (`release-train.yml`)

Daily schedule (13:00 UTC = 08:00 America/Chicago CDT; Q-CADENCE) and manual dispatch. Phase 1 report-only detection for the PyPI release train ([plan](../notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 1.3): full-history clones of the 7 sibling package repos, then `util/release_train/detect.py --json` classifies all 18 registry packages; the run publishes the release-manifest artifact plus a step-summary table.

Detector exit 1 (action needed) is a normal green outcome; only exit >= 2 (hard source error) fails the run. The `detect` job writes nothing: no PRs, no Releases, no (Test)PyPI interaction. The `RELEASE_TRAIN_MODE` repo variable (`off`|`report`|`propose`|`ceremony`, default `report`; an unknown value warns and degrades to `report`) plus the `mode` dispatch input is the instant kill switch and mode selector (precedence: dispatch input > repo variable > `report`).
The operator's guide to the four modes, the two owner gates, the §8 HALT catalog, and rollback is [`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md).

**Propose mode (Phase 2.2, opt-in).** Dispatching with `mode=propose` (or setting `RELEASE_TRAIN_MODE=propose`) adds a second, **write-scoped** `propose` job — `permissions: {contents: write, pull-requests: write}`, gated `if: needs.detect.outputs.mode == 'propose'`.
So the detect/report path stays `contents: read`, and the write scope is unreachable off the propose path — the R7 privilege boundary (plan §9.3), pinned by `tests/test_release_train_workflow_guard.py`.
It runs `util/release_train/propose.py --execute` to open **standard-gated** release-proposal PRs (owner reviews and merges; never auto-merged; touches neither TestPyPI nor PyPI). The optional `packages` dispatch input (whitespace/comma-separated pypi_names; empty = all eligible) restricts which packages are proposed.
Garbage `packages` tokens (Title Case, underscores, path fragments, shell metacharacters) exit **2** with `::error::` in **both** write jobs before Python runs (`release-train.yml` propose/ceremony shell; pin open juniper-ml#729 `PackagesInputRehearsalTest`). `--cross-repo` is appended **only** when `APP_TOKEN` is non-empty. Operator: runbook §3.2.
**Cross-repo write identity (Phase 4.1, plan §9.2 / §12 step 4.1).** The propose job mints a GitHub App installation token (`actions/create-github-app-token`, SHA-pinned) scoped to the 8 publishing repos and passes `propose.py --cross-repo`, so a sibling package's proposal branches from that repo's `origin/main`, edits its own checkout, pushes with the App token, and opens the PR **in that sibling repo** (the dup-guard runs per-repo).
In-repo meta consumer-pin co-changes (the #661 RK-11 lockstep) apply only to juniper-ml packages; a sibling proposal never edits the meta from a sibling checkout — it emits the §13 propagation edge instead.
**Graceful degradation is mandatory:** the mint step is gated on the repo variable `RELEASE_TRAIN_APP_ID` (owner-provisioned with the `RELEASE_TRAIN_APP_PRIVATE_KEY` secret), and when it is unset the job falls back to the single-repo `GITHUB_TOKEN` and `propose.py` skips sibling packages with a clear reason — the prior in-repo-only behavior.
The App private-key secret is referenced **only** in the mint step and the minted token **only** in the propose job (both pinned by `tests/test_release_train_workflow_guard.py`); the App token is never a `pypi` environment reviewer (R7).
The cross-repo **ceremony** (`ceremony.py --cross-repo`) keeps the exempt notes-archive PR **central in juniper-ml** (§10.2) while cutting the Release on the owning repo (`gh release create --repo pcalnon/<repo>`); its seam bounds every `--repo` — and the archive lane's two api calls' repo bind — to the 8 publishing repos without widening the verb allowlist.
**Both** write lanes create their commits through the GitHub API (`createCommitOnBranch`, no local commit), so every commit is **GitHub-signed / Verified** and satisfies the ruleset's `required_signatures` rule -> hands-free auto-merge (2026-07-23 ml#707 was the unsigned-commit block that motivated this for `ceremony.py`).
`propose.py` previously made **unsigned** local git commits (`-c commit.gpgsign=false`) so a headless run never tripped the owner's YubiKey config. Once the 2026-08-12 branch-protection normalization added `required_signatures` to all 9 repos, that made every proposal PR unmergeable — an unsigned commit anywhere on the branch blocks the merge, and squash does not rescue it (cascor#515; the pre-normalization cascor#497 merged with the identical unsigned commits).
`execute_proposal` and `execute_follow_on` both route through one `_execute_signed_pr` helper, and `propose.py` deliberately carries **no** local-`git` helper so the unsigned path cannot grow back (anti-resurrection pin: `ExecuteCrossRepoGuardTest.test_execute_path_makes_no_local_git_commit`). The API path needs no working tree — checkouts are read-only inputs.

`propose.py` also bumps the `AGENTS.md` **Last Updated** header in the same edit as **Version**, which now satisfies the `agents-md-touch-up.yml` **date check** as authored (the lane verifies the header rather than rewriting the branch — juniper-ml#1099).
Before #1099, that lane pushed its own `[skip ci]` commit when the date was stale; that commit became the PR head, and because it carried `[skip ci]` **no required context ever reported on it**, leaving the proposal permanently BLOCKED with every check stuck at "expected" (the other half of cascor#515). It also raced `Update Lockfile (Dependabot)`, whose push was then rejected. Pre-setting the date remains correct and is now the *only* thing needed.
Both write jobs must configure that headless git identity with `git config --global` (not repo-local) so sibling clones inherit `user.name` / `user.email` / `commit.gpgsign` — a juniper-ml-only identity fails the first sibling commit with `Author identity unknown` (ml#705 / run 30040138774; workflow-guard invariant `(g)` in #718).

**Ceremony mode (Phase 4.3, opt-in).** Dispatching with `mode=ceremony` (or setting `RELEASE_TRAIN_MODE=ceremony`) adds a second write-scoped `ceremony` job — identical `permissions: {contents: write, pull-requests: write}`, gated `if: needs.detect.outputs.mode == 'ceremony'`, with its own App-token mint step — that runs `util/release_train/ceremony.py --execute --monitor-timeout 900` for `BUMPED_NOT_RELEASED` packages.
It opens the central archive PR (branch + single-file commit via the GitHub API -> a **GitHub-signed** commit satisfying `required_signatures`, so the PR auto-merges hands-free), enables `--auto` behind the required guard, cuts the Release on the owning repo, and monitors the publish run to `PENDING_PYPI_APPROVAL`; the PyPI deploy still waits at the owner-gated `pypi` environment (Gate 2). The job renders a ceremony step summary (ceremonies / resume-monitors / HALTs / `PENDING_PYPI_APPROVAL`).
A per-package HALT (plan §8) is a normal green outcome surfaced in the step summary + a dedup issue + Slack (ceremony exit 1 does not fail the run; only exit >= 2 does). The HALT-issue upsert **degrades gracefully** if the App token lacks the Issues permission — a loud log line + a step-summary `halt_issue_failed` flag, never a crash (a `SeamViolation` code bug still propagates; the R7 gh surface is unchanged).
The workflow's R7 boundary — both write jobs' exact perms, the mode gates, off-quiescence, and the App secret referenced mint-only (once per write job) — is pinned by `tests/test_release_train_workflow_guard.py`, which also rehearses the actual mode-resolution shell, the ceremony **and** propose step summaries (`ProposeSummaryRehearsalTest`: `opened:`/`skip:` bucketing + empty-output banner, juniper-ml#730), and the `packages` / `--cross-repo` shell prefix (juniper-ml#729) via the YAML-extraction pattern.

The same guard pins every `<<'PY'` heredoc as balanced (`HeredocBalanceTest`, ml#708) and `compile()`-clean (`HeredocCompileTest`, ml#723) so a broken summary/Slack body cannot turn a successful run red only after the real work finishes.

**Known limitation (degraded no-App path only):** on the fallback path (`RELEASE_TRAIN_APP_ID` unset), a PR opened with the built-in `GITHUB_TOKEN` does **not** trigger CI workflows (GitHub's recursion guard), so a proposal PR shows **no checks** until the owner re-triggers them — close and reopen the PR, or push an empty commit.
When the GitHub App token is minted (the primary Phase 4.1 path), the PR is opened by the App identity, and CI runs normally, so the caveat no longer applies; the repo's `can_approve_pull_request_reviews` setting is already enabled.

With the `SLACK_WEBHOOK_URL` repo secret present (owner-provisioned incoming webhook; Q-CHANNEL), each run also posts a compact summary — classification counts, packages needing action, run URL — to the Juniper Slack channel. Strictly non-blocking: a missing secret skips the step, and a post failure never fails the run.

### Claude Code Action (`claude.yml`)

GitHub `@claude` assistant (`anthropics/claude-code-action`). Event-driven (comments/reviews/issues), SHA-pinned, **not** a required check and **not** the local `claudey` launcher. Operator surface: [Claude Code Action](#claude-code-action). Access audit: [Claude.yml Access Validation](#claudeyml-access-validation).

### CodeQL Analysis (`codeql.yml`)

Python semantic SAST. Required ruleset context **`Analyze (python)`** — **not** a Quality Gate `needs:` member (soak-then-promote, same convention sequence-safety copies). SHA-pinned `github/codeql-action/{init,autobuild,analyze}` must share one SHA; Dependabot group `codeql-action` (`github/codeql-action*`) is what keeps a bump atomic. Operator surface: [`docs/REFERENCE.md` § CodeQL Analysis](#codeql-analysis).

---

## PR Base-Branch Guard


`.github/workflows/pr-base-branch-guard.yml` fails any PR whose base branch is not the
default branch. Its job name -- **`Guard PR base branch`** -- is a **required status check**
in this repo's ruleset, so renaming the job or deleting the file makes `main` unmergeable
until the context is un-required first.

**What it protects against.** A PR based on another feature branch can squash-merge into
that branch, stranding its content off `main` behind a green **MERGED** badge. It has
happened three times in this ecosystem (`juniper-recurrence#7`/`#8`, `juniper-canopy#365`).

**Why it matters more than it looks.** Both rulesets here are scoped to `~DEFAULT_BRANCH`, so
a PR whose base is a feature branch is governed by **no ruleset at all** -- it has zero
required status checks and merges cleanly with nothing having run:

```bash
gh api repos/pcalnon/<repo>/rules/branches/feature%2Fanything --jq length   # -> 0
gh api repos/pcalnon/<repo>/rules/branches/main               --jq length   # -> 9
```

This workflow carries no `branches:` filter, so it is the **only** check that runs on such a
PR. It cannot block the merge there, since no ruleset applies, but it turns a silent merge into
a visibly red one.

**If it fails.** Re-open the work against the default branch. The house practice is
**close and re-open** a fresh PR titled `[retarget #NNN]`. Retargeting in place is *not*
sufficient on its own: every `ci*.yml` here uses the default `pull_request` types
`[opened, synchronized, reopened]`, which exclude `edited`, so a retarget re-runs this guard
and nothing else -- the PR stays blocked on its other required contexts until a push or a
close/re-open.

**`stacked-pr` label.** Silences this guard for a deliberate stack. It does **not** make the
PR mergeable into `main`, and it does **not** re-land the stack -- do that separately.

To promote this context, or to re-pin its `integration_id`, use the
[Required-Context Ruleset Writer](#required-context-ruleset-writer). Do not hand-roll a ruleset PUT.

Rollout and rationale: [juniper-ml#434](https://github.com/pcalnon/juniper-ml/issues/434).

## Ruleset Context Audit

`util/ad-hoc/2026-08-10_ruleset_context_audit.py` is the **read-only** fleet classifier for `required_status_checks`. It exists because that rule **cannot** be copy-pasted across repos: it names each repo's actual job strings, and a required name that never reports is never satisfied.

The 2026-08-10 incident applied one fleet-union list of 30 contexts to all 9 publishing repos. Every `main` became unmergeable except by admin bypass (200 blocking contexts across the fleet). Incident record: [`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`](../notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md). **§1 counts in that note are historical** — re-run the auditor; do not quote them.

This is the **reader**. The writer that adds one context (with a pre-flight that the repo's CI actually publishes the string) is `util/ad-hoc/2026-08-20_require_context_safely.py`. The CI gate that `~ALL` scope re-arms dependabot / Copilot bypass rows is `util/ruleset_scope_guard.py`. Do not substitute one for another.

### Invoke

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py              # all 9 publishing repos
python util/ad-hoc/2026-08-10_ruleset_context_audit.py --repo juniper-ml
python util/ad-hoc/2026-08-10_ruleset_context_audit.py --json       # machine-readable; see exit codes
```

Read-only: `gh api` GET of `/repos/pcalnon/<repo>/rules/branches/main` plus `gh pr list --state all --limit 8 --json statusCheckRollup`. Writes nothing. Needs `gh` authenticated to those 9 repos.

Hardcoded fleet (`REPOS`): `juniper-ml`, `juniper-cascor`, `juniper-canopy`, `juniper-data`, `juniper-cascor-worker`, `juniper-deploy`, `juniper-data-client`, `juniper-cascor-client`, `juniper-recurrence`. `--repo` is **not** validated against that list.

### Classification (verified against `audit()`)

| Bucket | Meaning | Require it? |
|--------|---------|-------------|
| `BLOCKING` | Required, never seen on the sampled rollups | **No** — remove or rename. This is the 2026-08-10 class. |
| `MATCHED` | Required and seen at least once | Already required. Human text prints the **count** only; names are in `--json`. |
| `TIER 1` | Seen on **every** sampled PR after filters, and not advisory | Safe to require. |
| `PATH-GATED` | Seen on some sampled PRs only (`name [freq/n]`) | **Do not require** — blocks every PR that misses those paths. |
| `advisory_seen` | Reports, but default-advisory (and not in the live required set) | Leave advisory. **`--json` only** — the human report omits this list. |

Two filters decide Tier 1 vs path-gated (not "every check that reports"):

1. **Always ∩ not-advisory.** A context that misses even one kept PR is path-gated. Dependabot/docs PRs (~22 checks) vs code PRs (~37) is preserved on purpose — those thinner PRs must stay mergeable.
2. **Half-median rollup drop.** A PR that merged before CI settled (juniper-ml#1061 carried 5 of ~37) would make **every** context look path-gated and collapse Tier 1. Rollups with `len < median/2` are discarded.

### Advisory predicate

`ADVISORY_EXACT` / `ADVISORY_PREFIXES` is a **default**, not the verdict. `advisory_predicate(required)` treats a name as advisory only when it matches the default **and** is **not** in that repo's live required set.

Without the subtraction, promoting a check (ml#1011 made `Sequence Safety` required fleet-wide) leaves the string in `ADVISORY_EXACT` and the now-required context **vanishes from Tier 1** — it looks missing when it is fine. Keeping promoted names in the default list is deliberate: a sibling that has not promoted the check still classifies it as advisory.

Prefix match is `startswith("Cursor Automation:")`, **not** a substring. A wrapped label that merely contains those words is not advisory.

`ADVISORY_EXACT` includes `claude`, `Sequence Safety` / `Sequence Safety (Advisory)`, `Fleet PR Lint`, notification/mutation side-jobs, the pre-#1099 `Bump AGENTS.md Last Updated` name, `Verify AGENTS.md Last Updated`, `Update requirements.lock`, and the umbrella `CodeQL` (the real gate is `Analyze (python)`).

### Exit codes

| Mode | Exit 0 | Exit 1 |
|------|--------|--------|
| Human (default) | `TOTAL BLOCKING` is 0 | Any repo has a non-empty `blocking` list |
| `--json` | No `blocking` and no `error` | Any `blocking` **or** any `error` |

Human mode can exit **0 with `ERROR:` rows** (a `gh` failure does not increment `TOTAL BLOCKING`). `--json` fails closed on those same errors. Do not treat a silent text-mode 0 as "the fleet probe succeeded" — read the `ERROR:` lines, or use `--json`.

A repo whose sampled rollups are all dropped (or that has no recent PRs) has `reported = ∅`, so **every** required context becomes `BLOCKING`. That is a sampling failure, not a 200-context incident. Re-run; do not strip the ruleset from a one-shot empty sample.

### Operator pitfalls

| Symptom | Check |
|---------|-------|
| `main` `BLOCKED`, every visible check green | Required name never reports — the class this tool names `BLOCKING`. Confirm with `--repo` before adding another context. |
| Tier 1 empty / everything path-gated | Thin rollup slipped past the half-median filter, or `--limit 8` hit an unlucky window. The filter is `>= median/2`, not "drop dependabot". |
| Promoted check missing from Tier 1 | `advisory_predicate` must subtract the live required set. If you forked the script and inlined `is_advisory()` only, you reintroduced the ml#1011 miss. |
| `Cursor Automation: …` in Tier 1 | Prefix must stay `startswith`. A `in` / substring test will also swallow unrelated labels. |
| Text exit 0 but one repo says `ERROR:` | Expected — human mode ignores probe failures. Re-run `--json` (exit 1) or that `--repo` alone. |
| Quoted 23/200 blocking from the 2026-08-10 note | Historical. Re-run; the note's §1 table is the incident, not the live fleet. |
| Used this script to *add* a required context | Wrong tool. `require_context_safely.py` is the writer (pre-flight + snapshot). This auditor only GETs. |
| `--help` still says `CANDIDATE` | Stale `__doc__`. Live `audit()` split that bucket into `tier1` / `path_gated` / `advisory_seen`. Trust the function, not the banner. |

Dedicated unittest arm is **not on main** (open juniper-ml#1670). Complementary gates that *are* on main: `tests/test_require_context_safely.py` (writer), `tests/test_ruleset_scope_guard.py` (`~ALL` scope), `tests/test_wait_for_checks.py` (required-context waiter).
Related: both rulesets are `~DEFAULT_BRANCH`-scoped on purpose. The companion that fails a re-scope to `~ALL` (which would re-arm deleted bot bypass rows) is [Ruleset Scope Guard](#ruleset-scope-guard).

## Ruleset Scope Guard

`util/ruleset_scope_guard.py` fails if any Juniper ruleset is scoped `~ALL` instead of `~DEFAULT_BRANCH`. The CI job name is **`Ruleset Scope Guard`** (`ruleset-scope-guard`). It is a **hard Quality Gate need** (`tests/test_ci_quality_gate.py` `REQUIRED_NEEDS`): it runs on every event, including `push:main`, so folding it into `required-checks.needs` does not paint pushes red the way the PR-only soak jobs would.

### Why `~ALL` is a hole

On 2026-08-23 the `dependabot[bot]` (`29110`) and `Copilot SWE Agent` (`1143301`) bypass rows were removed from all 9 repos. That removal is safe **only while every ruleset stays `~DEFAULT_BRANCH`-scoped**:

- Under `~DEFAULT_BRANCH`, the `creation` rule is evaluated only when creating the default branch — which no bot ever does — so those rows were inert and removing them changed nothing.
- Under `~ALL`, `creation` is evaluated on **every** branch, including `dependabot/*`. The rows were genuinely load-bearing there: that is exactly what the 24 `creation: fail` bypass events between 2026-07-20 and 2026-08-10 were.

Re-scoping any ruleset back to `~ALL` silently re-arms a dependency on rows that no longer exist. The symptom is dependency PRs stopping fleet-wide, with nothing pointing at the cause. Determination and evidence: [`notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md`](../notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md).

### What it does **not** check

**Bypass-row presence.** `bypass_actors` is redacted for unauthenticated callers. This guard is deliberately token-free so it can run on any PR without a secret. It reports scope only, and says so on stdout (`bypass rows are NOT checked`). For the row half use the authenticated `util/ad-hoc/2026-08-23_bypass_removal_verify.py`.

That split is load-bearing: a token-free tool that appeared to verify rows would report a redacted field as empty — looking green while checking nothing. `ScopeContractTest` pins that the source does not `get("bypass_actors")`.

The tool is **read-only** (GET only). It never PUTs a ruleset and never adds or amends required contexts.

### Usage

```bash
python3 util/ruleset_scope_guard.py                  # this repo only (per-PR / CI default)
python3 util/ruleset_scope_guard.py --fleet          # all 9 repos (manual)
python3 util/ruleset_scope_guard.py --repo juniper-data --json
```

`--fleet` and `--repo` are mutually exclusive. Default repo is `juniper-ml`. `FLEET` is a stdlib-only list kept in lockstep with the release-train registry's publishing repos plus `juniper-deploy` (`FleetListDriftTest` — adding a sibling means updating this list too).

No token is required: all 9 repos are public and `GET /repos/{o}/{r}/rulesets[/{id}]` answers 200 unauthenticated. `GITHUB_TOKEN` / `GH_TOKEN` is used when present purely for the higher rate limit (60/hr unauthenticated is per-IP and shared on hosted runners). CI passes `secrets.GITHUB_TOKEN`.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | every ruleset narrowly scoped |
| 1 | at least one `~ALL` ruleset — the guard firing |
| 2 | could not verify (probe failed after retries) **or** no rulesets found at all |

Both non-zero codes fail the job on purpose (fail-closed). An empty ruleset list is **not** a pass — the repo is unprotected, or the probe degraded. A failed `_get` raises `ProbeError` rather than returning `[]` / `None` (a failed probe that reads as "nothing found" reports a broken check as clean). Transient flakiness is absorbed by 3 retries with backoff, not by treating an unverifiable result as a pass.

`audit_repo`'s `getter` resolves at **call** time, not definition time — a `getter=_get` default would bind the original function object and make the module attribute unpatchable, so the hermetic tests would silently hit the network.

### Repair

| Symptom | Check / Fix |
|---------|-------------|
| Exit 1, `FAIL: N ruleset(s) scoped ~ALL` | Re-scope the named ruleset to `~DEFAULT_BRANCH`, **or** restore the dependabot (`29110`) / Copilot (`1143301`) bypass rows deliberately and update the determination note |
| Exit 2, `COULD NOT VERIFY` | Not the same as clean. Re-run; if it persists, check `api.github.com` before assuming the rulesets are fine |
| Exit 2, `no rulesets found at all` | Unprotected repo or a degraded empty list — never treat as a pass |
| Quality Gate red, this job skipped | Membership in `required-checks.needs` is not decorative: the gate runs `if: always()` and tests each `needs.<job>.result` — a job listed with no `if` arm in the script gates nothing (`test_ci_quality_gate.py`) |

CI wiring: `.github/workflows/ci.yml` job `ruleset-scope-guard` (`needs: [pre-commit]`). Gate: `python3 -m unittest -v tests/test_ruleset_scope_guard.py`. Hermetic: `_get` is monkeypatched; no network. Coverage includes narrow pass, `~ALL` fail naming the ruleset and the `29110` rows, one-wide-among-narrow, empty list → 2, probe failure → 2 not 0, retry-then-recover, and the `bypass_actors` source pin.

## CI/CD Workflow Inventory

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

- `.github/workflows/ci.yml` -- Main CI pipeline: pre-commit (G4 changed-files split — `pull_request` / `merge_group` use `--from-ref <BASE> --to-ref HEAD`; `push` keeps `--all-files`), unit tests, release-train archive-guard (PR-only), the `Sequence Safety` and advisory `Fleet PR Lint` (`cursor/*`) standalone jobs, build, docs, security, dependency docs.
  - **`Sequence Safety` is a REQUIRED ruleset context**, despite the job banner still saying advisory and despite being absent from Quality Gate `needs:`. Labels `allow-symbol-loss` / `docs-rewrite` add `--advisory` (WARN, exit 0) and **do** green the PR check; they do **not** cover post-merge `main-verify`. Only an `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite: <path>` **commit trailer** waives the finding inside the screens and travels in history.
- `.github/workflows/main-verify.yml` -- Post-merge main-verification (P2 gate G3): on `push:main` (per-SHA, no-cancel) it installs `juniper-ci-tools` (>=0.8.0) and runs the `juniper-symbol-loss-check` (explicit ml `--scope`) + `juniper-docs-additions-check` screens over `BASE..<merge>` (`sequence-safety-report`), a path-gated battery mirror + failure-only `notify`. G3.1 CATCH-UP BASE = last successful main-verify tip that is an ancestor of HEAD, else `github.event.before`, else `HEAD^1`.
- `.github/workflows/publish.yml` -- Meta PyPI publish: TestPyPI **Gate 1** two-phase verify (TestPyPI-only download, then local-wheel bare -> `[clients]` -> `[tools]` against PyPI only; never `--no-deps` on the installs, never `--extra-index-url`, never the heavy extras; provenance fetch is a 10×6s poll, not `sleep 30`), then PyPI (`needs: testpypi`, OIDC).
  The `build` job is tag-guarded to `v*` Releases so a `juniper-<pkg>-v*` Release cannot fire the meta publisher.
  Gates: `tests/test_publish_testpypi_verify.py`, `tests/test_publish_release_only_trigger.py`. Operator surface: [`docs/REFERENCE.md` § Meta-Package Publish Pipeline](#meta-package-publish-pipeline).
- `.github/workflows/publish-*.yml` -- Six shared sub-package publishers. All are **Release-only** (`release: published` + `workflow_dispatch`; deliberately **no** `push: tags`, which double-fired and raced TestPyPI in juniper-ml#555 — the trigger **is** the gate; a bare `git push <tag>` starts no run).
  Each build job is gated on its own `startsWith(github.event.release.tag_name, '<pkg>-v')`, with a `--no-deps` TestPyPI-only verify (5×10s retry) and `skip-existing: true` on both publish steps.
  Do not resurrect a `Require a GitHub Release for this tag` step under `if: github.event_name == 'push'` — that condition is unreachable.
  Operator table: [`docs/REFERENCE.md` § Independent Sibling Package Publish Pipelines](#independent-sibling-package-publish-pipelines).
- `.github/workflows/ci-*.yml` -- Six in-repo shared-package CIs (`ci-tools` / `config-tools` / `doc-tools` / `model-core` / `observability` / `service-core`), distinct from meta `ci.yml` and from `publish-*.yml`.
  Path filters must include `<subdir>/**` **and** the workflow's own path; matrices carry declared Python floors; coverage uses `--cov-fail-under` plus a blocking `juniper-coverage-gap-map --enforce` (only ci-tools may `--omit`
  `__main__.py`); `build.needs: test`; service-core installs sibling `juniper-model-core` from the monorepo root (no test-job `working-directory`).
  Gate: `tests/test_subpackage_ci_workflows.py`. Operator table: [`docs/REFERENCE.md` § Shared-Package CI Workflows](#shared-package-ci-workflows).
- `.github/workflows/docs-full-check.yml` -- Weekly full documentation link validation including cross-repo checks. `env.ECOSYSTEM_REPOS` (the clone list) must equal the registry's publishing repos minus `juniper-ml` plus `juniper-deploy`; omitting a sibling silently drops it from every weekly screen. Gate: `tests/test_docs_full_check_ecosystem.py`. Operator surface: [`docs/REFERENCE.md` § Docs Full Check](#docs-full-check).
- `.github/workflows/codeql.yml` -- Python semantic SAST (`queries: +security-and-quality`). Required ruleset context **`Analyze (python)`**; absent from Quality Gate `needs:`. `merge_group:` is an accepted juniper-ml-only divergence so that context re-posts on a queued merge. Dependabot group `codeql-action` keeps `init` / `autobuild` / `analyze` on one SHA. Operator surface: [`docs/REFERENCE.md` § CodeQL Analysis](#codeql-analysis).
- `.github/workflows/security-scan.yml` -- Weekly `pip-audit --strict --desc on` after `pip install -e .` (read-only permissions). Deliberately unlike the per-PR `ci.yml` `security` job, which uses `--skip-editable` and omits `--strict` so an unreleased editable meta install cannot fail every PR. Do not copy either contract onto the other path. Gate: `tests/test_security_scan_workflow.py`.
- `.github/workflows/lockfile-update.yml` -- Weekly (Monday 08:00 UTC) `juniper-generate-dep-docs` refresh; a SHA-pinned `peter-evans/create-pull-request` opens `chore/lockfile-update` with labels `dependencies` + `automated` (permissions exactly `contents: write` + `pull-requests: write`). Never resurrect the deleted `util/generate_dep_docs.sh` (juniper-ml#298). Gates: `tests/test_lockfile_update_workflow.py` (structure) + `tests/test_ci_tools_drift.py` (pin ceiling).
- `.github/workflows/release-train.yml` -- Daily (13:00 UTC) PyPI release-train orchestrator.
  - The `detect` job (report path) runs `util/release_train/detect.py` over the 18-package registry and renders a step-summary table; it never writes.
  - Two opt-in write-scoped lanes gate on the resolved mode: `propose` (Phase 2.2/4.1 — standard-gated proposal PRs) and `ceremony` (Phase 4.3 — exempt archive PR + Release cut → owner-gated `pypi` Gate 2).
  - Mode switch/rollback: repo variable `RELEASE_TRAIN_MODE` (`off`|`report`|`propose`|`ceremony`, default `report`) + a dispatch `mode` override; `off` quiesces entirely.
  - Operator guide: `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`.
- `.github/workflows/pr-budget-alarm.yml` -- Daily (14:00 UTC) scheduled open-PR budget alarm (flood-remediation guardrail, analysis §4 item 9 / P1 §5): counts total open PRs + `cursor/`-headed PRs against repo variables `PR_BUDGET_WARN` (default 15) / `PR_BUDGET_ALARM` (default 30), always writes a step-summary table, and on breach posts to Slack via `SLACK_WEBHOOK_URL` under the non-blocking contract mirrored from `release-train.yml`. Report-only -- a breach never blocks a PR.
- `.github/workflows/claude.yml` -- `@claude` assistant (`anthropics/claude-code-action`; SHA-pinned; not a required check). Operator surface: [Claude Code Action](#claude-code-action).
- `.github/workflows/agents-md-touch-up.yml` -- **Verifies** (never rewrites) `AGENTS.md`'s `**Last Updated**:` field on every PR that touches `AGENTS.md`: the value must be a well-formed `YYYY-MM-DD`, not in the future, and **either already equal to today's UTC date OR changed in this PR** (`git diff <base>...HEAD`); a missing field warns and passes. Job `Verify AGENTS.md Last Updated`, `permissions: contents: read`, no fork guard (verification needs no token).
  - The **already-today** arm is a real escape hatch, not a rounding of the rule: a second same-day PR touching `AGENTS.md` — or a **stacked** PR whose base branch already carries the bump, so the line legitimately does not appear in its own diff — passes on the value alone. Note which arm each PR is relying on: the already-today arm is **re-evaluated every run** and expires at the next UTC midnight, while the changed-in-this-PR arm is **stable for the life of the PR** (that is the workflow's stated reason for preferring it — see `.github/workflows/agents-md-touch-up.yml`).
  - **A stacked pair that sits overnight: bump the line in the CHILD, not the base.** The child's own diff then contains `+**Last Updated**:`, which satisfies the durable changed-in-this-PR arm and keeps satisfying it however long the PR stays open. Re-bumping the **base** only re-arms the already-today arm for the child, so it passes today and is stale again tomorrow — a one-day shelf life, repaid every morning until the stack lands. (Earlier revisions of this page recommended exactly that; corrected 2026-08-24.) The child must set a value that actually differs from the base's, or the line does not appear in its diff and the durable arm is not engaged.
  - It used to bump the date and push the commit itself. Removed in juniper-ml#1099: a runner's local `git commit` is UNSIGNED, which `required_signatures` rejects (an unsigned commit anywhere in the history blocks the merge; squash does not rescue it), and the `[skip ci]` bump commit became the PR head so **no required context ever reported on it** -- the PR sat permanently BLOCKED with every check at "expected" (cascor#515). It also raced `Update Lockfile (Dependabot)` for the push slot.
  - The predicate is "the line changed", not "equals today", so a PR that spans days keeps passing on re-run. `propose.py` sets the header in its own commit, so release proposals satisfy it as authored.
  - Companion to `tests/test_agents_md_header_schema.py`; gate: `tests/test_agents_md_touch_up.py` (11 arms incl. an anti-resurrection assertion that the shell can never `git commit` / `git push` / `sed -i`). Operator surface: [`docs/REFERENCE.md` § AGENTS.md Date Check](#agentsmd-date-check).
- `util/validate_claude_yaml_access.bash` -- Structural auditor for public-repo `ANTHROPIC_API_KEY` safeguards (L2: no `pull_request_target` / `workflow_run`; L3: the `claude:` job `if:` must `contains(..., '@claude')`).
  Per-PR via `ci.yml`'s `claude-yaml-audit` job (Quality Gate); weekly via `docs-full-check.yml` under `JUNIPER_ROOT`. The `JUNIPER_ROOT` fan-out iterates the hard-coded `DEFAULT_REPOS` array (registry publishers plus `juniper-deploy`),
  **not** every cloned directory — it is orthogonal to `ECOSYSTEM_REPOS`, and the two lists must move together when a publishing sibling is added.
  Gate: `tests/test_validate_claude_yaml_access.py`. Operator surface: [`docs/REFERENCE.md` § Claude.yml Access Validation](#claudeyml-access-validation).

---

## Shared Observability Helpers Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

`juniper-observability` (this repo's `juniper-observability/` subdirectory, published as a standalone PyPI package) is the canonical home for cross-service observability primitives — middlewares, the build-info `Info` metric helper, structured-JSON logging, and **idempotent `prometheus_client` collector helpers**. Any new `Counter` / `Gauge` / `Histogram` / `Summary` / `Info` / `Enum` registration in any Juniper service should go through:

- `register_or_reuse(factory, name, *args, **kwargs)` — adopt-existing on duplicate (preserves accumulated samples; **default choice for almost every call site**).
- `register_fresh(factory, name, *args, **kwargs)` — drop-and-recreate (use only when test fixtures or migrations intentionally want different buckets/labels).
- `register_info_or_update(name, description, **info_labels)` — sugar for the `Info` two-step register-then-`.info({...})` pattern.
- `lazy_register_or_reuse(factory, name, *args, **kwargs)` — like `register_or_reuse` but caches the result in a module-private dict; for the lazy-init-with-`None`-sentinel pattern.

Tests touching these collectors should use `juniper_observability.testing.reset_prometheus_registry`. Minimum pin: `juniper-observability>=0.2.0`. See [`notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md`](../notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md) for the design rationale and the migration history.

---

## Shared Service-Core Contracts

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

`juniper-service-core` (this repo's `juniper-service-core/` subdirectory) owns the shared FastAPI middleware, the `/ws/control` security + command dispatch, and the distributed worker pool that model services inject executors into. The load-bearing invariants — the ones a well-meaning refactor silently breaks:

- **CR-024 body limit** — `RequestBodyLimitMiddleware` treats `Content-Length` as an early-reject hint only and **always** stream-caps `POST` / `PUT` / `PATCH` against the cumulative limit (default 10 MiB), so an under-declared header or a chunked body with none still 413s. Skipping the stream when the declared length is present-and-small is the classic bypass.
- **Auth before rate limit** — with API keys configured, `APIKeyAuth` runs first, so a 401 never consumes a rate-limit token. Blank / whitespace-only configured keys are filtered out (the `auth_posture.real_keys` rule) so an empty secret file cannot enable auth that then accepts an empty `X-API-Key`.
- **429 header passthrough** — `RateLimiter` raises `HTTPException` carrying `Retry-After` + `X-RateLimit-*`; `SecurityMiddleware.dispatch` must rebuild `JSONResponse(..., headers=exc.headers)`. RateLimiter unit tests alone do not exercise that catch path.
- **Control-WS log sanitizing** — reject logs that interpolate untrusted Origin/command text; go through the module-local `_sanitize_for_log` helpers (`control_security` strips `\r`/`\n`; `control_stream` also drops other C0 controls, keeping tabs) so CRLF cannot forge multi-line control-plane records. Sanitizing changes log records only, never handshake outcomes or ack JSON.
- **Zero rate limit** — `ws_control_rate_limit_per_sec=0` builds a `LeakyBucket` with no refill; `retry_after` returns `3600.0` (hard backoff) rather than dividing by zero and tearing down the receive loop.
- **`/ws/workers` fail-closed** — a bad/missing `X-API-Key` closes **4001** without accepting; a non-object or shape-invalid registration closes **4008** with no `registration_ack`; `submit_result` rejects wrong-worker / unassigned results before the protocol parse; binary attachments over 100 MB get `Binary frame too large`. A clean disconnect and a mid-result transport abort (expected-binary-got-text / oversize) **requeue** the in-flight task rather than leaving it assigned until `task_reassignment_timeout`. Control receive rejects malformed / non-object JSON with close **1003** rather than an `AttributeError`.
- **WS tunables are declared, not implicit** — `websocket/tunables.py` holds all eleven settings fields the WebSocket handlers read, each with its default and a `security` flag. Six are security controls: the Origin allowlist, the control-endpoint kill switch, the control rate limit, and the three handshake-cooldown parameters. Call sites pass only a name; the default lives in the registry.
  - The `getattr`-based decoupling is deliberate and kept — the shared package still never imports a consuming service's settings class. What changes is that a miss which looks like a misspelling now logs a WARNING naming both spellings, instead of silently reverting a security control to a library default forever (`ws_control_rate_limit_per_second` vs `..._per_sec`).
  - `resolve()` on an undeclared name raises rather than defaulting; `audit(settings)` is the boot-time counterpart, reporting defaulted security controls and suspected typos. Closes APD-SVCCORE-003 / -010. `tests/test_ws_tunables.py` pins the pre-refactor defaults byte-for-byte and source-scans both handlers so registry and call sites cannot drift.

Operator surface: [`docs/REFERENCE.md` § juniper-service-core](#juniper-service-core).

---

## Post-Merge Main Verification

`.github/workflows/main-verify.yml` is the bypass-proof compositional-loss net (flood-remediation P2 gate G3). It runs on every `push` to `main` (plus `workflow_dispatch`) so a merge that skipped or greenwashed per-PR checks still gets screened after it lands. Design notes: [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) §4 item 8.

| Job | When it runs | What it does |
|-----|--------------|--------------|
| `symbol-screen` | **Always** | the `juniper-symbol-loss-check` + `juniper-docs-additions-check` console scripts (juniper-ci-tools) over `BASE..HEAD`; uploads `sequence-safety-report` (`symbol-report.json` / `docs-report.json`, 30-day retention) |
| `battery` | Path-gated | Re-runs the enumerated unittest + bash battery from `ci.yml`'s `tests` job when the push touched `tests/` \| `util/` \| `scripts/` \| `.github/` \| `pyproject.toml`; docs-only merges skip it |
| `notify` | On `failure()` only | Upserts **one** open GitHub issue with the stable title `main-verify: post-merge verification failing` (comment per subsequent failing SHA) and posts a non-blocking Slack summary (`SLACK_WEBHOOK_URL`; missing secret skips) |

#### Failure notify (stable-title issue dedup)

Workflow header version **0.3.0** (juniper-ml#928). A red streak must stay loud without opening one issue per failing push (the 2026-07-31..08-01 streak filed six: #883 / #884 / #891 / #892 / #896 / #897).

| Rule | Behavior |
|------|----------|
| **Stable title** | Exact string `main-verify: post-merge verification failing` (not SHA-keyed) |
| **First failure** | `gh issue create` with that title; body names the first failing SHA, job results, run URL, and the standing remediation pointer (`Allow-Symbol-Loss` / `Allow-Docs-Rewrite` trailers; flood-remediation analysis doc) |
| **Later failures in the streak** | Search open issues for that **exact** title; `gh issue comment` with the new SHA + run URL (no second issue) |
| **Green path** | `notify` is `if: failure()` only — success is a no-op; the issue is **not** auto-closed |
| **Owner close** | Close the tracking issue **after adjudication** (restore the loss, or land a trailer-waived follow-up that greens main-verify) |
| **Slack** | Non-blocking; missing `SLACK_WEBHOOK_URL` skips; a post failure never fails the workflow |

Re-runs of the **same** failing SHA still hit `failure()` and comment again if the issue remains open — that is intentional (loud until the owner closes).

#### Concurrency (per-SHA, no cancel)

```yaml
concurrency:
  group: main-verify-${{ github.sha }}
  cancel-in-progress: false
```

Contrast `ci.yml` (`group: ci-${{ github.ref }}` + `cancel-in-progress: true`): rapid serial merges to `main` cancel each other's CI runs, so only the last tip survives. Main-verify **must not** drop intermediate merges during a storm — each SHA gets its own group and is never canceled (may queue behind the runner cap).

#### G3.1 catch-up BASE

A quoted `[skip ci]` in a merge-commit body can skip this workflow entirely (2026-07-30 incident on ml#870/#872/#873). The next successful run must therefore screen the skipped window, not only `HEAD^1`.

BASE resolution order (written to the job step summary as “Post-merge sequence-safety base”):

1. **Catch-up** — `head_sha` of the most recent **successful** `main-verify` run on `main`, when that commit is an ancestor of `HEAD` and ≠ `HEAD` → reason `catch-up from <sha> (N commits)`.
2. Else **`github.event.before`** (the push's first parent), when resolvable and not the all-zero SHA.
3. Else **`HEAD^1`** (force-push/initial-commit/dispatch-fallback).

Screens then run as `juniper-{symbol-loss,docs-additions}-check --base <BASE> --head <HEAD>` (human log + guarded `--json` artifact). Exit `≥2` is an invocation error; exit `≥1` is a compositional-loss finding.

#### Waivers: trailers vs PR labels

| Mechanism | Per-PR `sequence-safety` job (`ci.yml`) | Post-merge `main-verify` |
|-----------|-----------------------------------------|--------------------------|
| Commit trailer `Allow-Symbol-Loss: <qualified.symbol>` / `Allow-Docs-Rewrite: …` in `BASE..HEAD` | Honored by the screen CLIs | **Honored** — required for post-merge green on intentional removals |
| PR label `allow-symbol-loss` / `docs-rewrite` | Demotes that screen to `--advisory` (WARN-only exit 0) | **Invisible** — labels never reach `push:main` |

Do not expect a label hatch to turn green on main after a merge. Blanket `Allow-Symbol-Loss: *` is rejected.

**The trailer must ride on the commit that survives the squash — a waiver added as a *second* commit is silently discarded.** Squash-and-merge composes the merge commit's message from the PR's *first* commit, so a correct, well-argued waiver commit pushed on top of an existing branch never reaches `main`, and the screen behaves exactly as if it had never been written. Observed 2026-08-21 on ml#1228: waiver commit `38df160a` carried a valid `Allow-Symbol-Loss:` trailer, the PR merged as `14e7af4` **without** it, and main-verify then failed on every subsequent merge via the G3.1 catch-up base. Before merging a PR that removes a symbol, verify the trailer is where it will land:

```bash
# the trailer must appear in the FIRST commit of the PR branch, not a follow-up
git log --format='%B' origin/main..HEAD | grep -c 'Allow-Symbol-Loss'   # expect >= 1
git log -1 --format='%B' <squashed-merge-sha> | grep 'Allow-Symbol-Loss'  # after merge
```

If it did not land, the repair is a follow-up PR whose **own first commit** carries the trailer; the symbol does not need restoring and no code change is required beyond whatever that PR legitimately does.

#### Battery path gate (detector + fail-open)

The `battery` job runs its own `Detect relevant path changes` step (P2 S3 burst-cost mitigation). Base resolution, in order:

1. Start from `github.event.before`.
2. If it is empty, the all-zero SHA, or unresolvable → fall back to `HEAD^1`.
3. If there is still no base (orphan/initial-tip/force-push) → **fail-open** `run=true` (`No resolvable base (initial / force push) -> running the battery to be safe.`).
4. Otherwise `git diff --name-only <base> <HEAD>` → `run=true` on a match against `tests/` | `util/` | `scripts/` | `.github/` | `pyproject.toml`, else `run=false`.

This detector is **independent of** the G3.1 catch-up BASE used by `symbol-screen`: the screen sweeps skipped windows, the battery only decides whether the enumerated suite is worth re-running. `symbol-screen` still always runs when the battery skips, so a docs-only merge legitimately shows a skipped battery and a green screen. Hermetic rehearsal: `tests/test_main_verify_battery_paths.py`.

#### Battery sync constraint

The battery job's unittest list is a **manual mirror** of `ci.yml`'s `tests` job (no pytest auto-discovery). Adding or removing a test module in `ci.yml` must update `main-verify.yml` in the same PR.

#### Operator triage

```bash
# Reproduce the screens locally against the same window main-verify would use:
juniper-symbol-loss-check --base <BASE> --head <HEAD>
juniper-docs-additions-check --base <BASE> --head <HEAD>

# Inspect the artifact from a failed run:
gh run download <run-id> -n sequence-safety-report
```

| Symptom | Check / Fix |
|---------|-------------|
| Red `symbol-screen` after a “green” PR | Per-PR job may have been `--advisory` via labels, or BASE was narrower than G3.1 catch-up. Download `sequence-safety-report`; waive with a **commit trailer** on a follow-up commit, or restore the deleted symbol/docs. |
| Waiver was written, but main is still red | Check the *merged* commit, not the branch: `git log -1 --format='%B' <sha> \| grep Allow-Symbol-Loss`. Squash ships the **first** commit's message, so a waiver added as a second commit never lands. Repair with a follow-up PR whose own first commit carries the trailer. |
| Suspected `[skip ci]` gap | Open the next main-verify run's step summary — look for `catch-up from <sha> (N commits)`. That run screens every merge since the last successful tip. |
| Docs-only merge, no battery | Expected — `battery` path-gate skips; `symbol-screen` still always runs. |
| Initial / force-push tip never ran the battery | The detector must fail-open to `run=true` when no parent base resolves — inspect the `Detect relevant path changes` step log. |
| Many open “main-verify failed at \<SHA\>” issues | Pre-0.3.0 per-SHA titles. Current notify uses one stable title; close stale SHA-keyed issues after adjudication and rely on `main-verify: post-merge verification failing`. |
| Silent main red (no Slack) | Confirm `SLACK_WEBHOOK_URL` is set; notify is non-blocking and never fails the workflow. Tracking issue title is SHA-keyed (re-runs comment, not reopen). |
| Tracking issue still open after green | Expected — notify does not auto-close. Owner closes after adjudication. |
| Battery list drift vs `ci.yml` | Keep both enumerations in lockstep in the same PR (see SYNC NOTE in `main-verify.yml`). |

Related: the per-PR `sequence-safety` job in `ci.yml` is a **required** ruleset context (absent from Quality Gate `needs:`). Fleet predicted-merge shells out to the same symbol CLI on a throwaway merge result (`util/fleet_triage/predict_merge.py` → the `juniper-symbol-loss-check` console script (juniper-ci-tools >=0.8.0); the 2026-07-28 flood-census ad-hoc screens are retired under `util/ad-hoc/retired/` with a `_RETIRED-2026-08-05` suffix).

## Experiment Stack Utilities

`util/experiment_stack.bash` + `util/experiments/run_experiment.py` are the **per-run** CLI experimentation tooling (plan Wave 2.1–2.6; this section is Wave 2.7). They bring up a throwaway juniper-data instance plus **cascor and/or recurrence** (never canopy), drive a single experiment YAML against that stack, and write plots/stats/manifest under a durable `RUN_DIR`. The Wave 7.3 PF scenario instruments that drive them as a matrix are [§ PF Scenario Suites](#pf-scenario-suites).

After a suite finishes, read the ratified metrics with `util/experiments/read_run_metrics.py` and bless a named baseline with `util/experiments/make_baseline.py` — see [Perf-lane metrics and baselines](#perf-lane-metrics-and-baselines).

Multi-cell campaigns go through `util/experiments/run_suite.py`. After #1643 the suite report carries the ratified gate inputs — see [Suite Report Gate Inputs](#suite-report-gate-inputs).

Multi-cell campaigns use `util/experiments/run_suite.py` (Wave 7.1 / 7.5) — operator contract: [Suite Driver](#suite-driver).

Primary design: [`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md). Preflight evidence: [`notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md`](../notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md).

This is **not** the isolated E2E trio (`util/isolated_stack.bash` on `8101`/`8202`/`8051`) and **not** the host stack (`plant_all` / `8100`/`8201`/`8050`). Recurrence **timings** already land on the manifest; the split gate still has **no recurrence work counter** — see [Recurrence Work Is Not Countable](#recurrence-work-is-not-countable) (lands with juniper-ml#1683).

Recurrence YAML still allow-lists `dataset.split` / `predict.from_dataset_split` as `{train, test, full}` — `"validation"` is exit 2. That is the shipped NPZ contract, not the closed design. Operator surface: [Train / Val / Test Partition Contract](#train--val--test-partition-contract).

### Launcher (`util/experiment_stack.bash`)

| Utility | Purpose | Key overrides |
|---------|---------|---------------|
| `--up (--cascor \| --recurrence)` | Allocate ports, write `ports.json`, then launch data → selected app(s) and health-gate | `JUNIPER_EXP_*` (below) |
| `--down RUN_ID` / `--down --all-mine` | Pidfile-first teardown; release locks; keep `artifacts/` | same |
| `--status [RUN_ID]` | Probe health / pids / scrape state (or list runs) | same |
| `--dry-run …` | Print expanded commands; create/start/kill nothing | same |

Port ranges (plan §9.3; disjoint from operator ports):

| Service | Range | Health URL |
|---------|-------|------------|
| juniper-data | `8110`–`8139` | `/v1/health` |
| juniper-cascor | `8230`–`8259` | `/v1/health` |
| juniper-recurrence | `8260`–`8289` | `/v1/health/ready` |

Never touches `8100` / `8200` / `8201` / `8210` / `8050` / `8051`. Never reads or writes `JuniperProject.pid`. Never starts canopy. Never writes a repo `.env`.

```bash
# Preview a cascor arm (no side effects)
util/experiment_stack.bash --dry-run --up --cascor --config conf/experiments/example.yaml

# Live bring-up (writes RUN_DIR under ~/.local/state/juniper-experiments/)
util/experiment_stack.bash --up --cascor --config path/to/experiment.yaml
util/experiment_stack.bash --up --recurrence --config path/to/experiment.yaml
util/experiment_stack.bash --up --cascor --recurrence   # both apps + one data

# Status / teardown (RUN_ID from the --up banner / RUN_DIR basename)
util/experiment_stack.bash --status
util/experiment_stack.bash --down <RUN_ID>
```

Optional flags on `--up`:

- `--shared-data URL` — reuse an existing juniper-data instead of launching one.
- `--config PATH` — copy YAML to `$RUN_DIR/config/experiment.yaml` and export **both** `JUNIPER_CASCOR_CONFIG_FILE` and `JUNIPER_RECURRENCE_CONFIG_FILE`; each app's Wave-3 `ExperimentYamlSettingsSource` projects the `service:` block (activation is by env var only, so the export is the threading mechanism).
- `--experiment NAME` — Prometheus `experiment` label (default: config basename).
- `--grafana-bridge` — **opt-in** socat relays + Prometheus target file under `JUNIPER_EXP_DEPLOY_DIR/prometheus/targets/<RUN_ID>.json`. Without it, `--status` reports UNSCRAPED.

#### RUN_DIR contract (§6.4)

`RUN_ID=<UTC yyyymmddThhmmssZ>-<4 hex>` under `JUNIPER_EXP_RUN_ROOT` (default `~/.local/state/juniper-experiments` — under `$HOME`, **not** `/tmp`, so a reaped sandbox cannot destroy results). Everything for the run lives inside `$RUN_DIR`: pidfiles + recorded cmdlines, `logs/`, `relays/`, `config/`, `env/launch.env`, `data/`, `equities-cache/`, `snapshots/`, `artifacts/{plots,results}/`, `ports.json`, `teardown.json`.

Port locks use atomic `mkdir "$LOCK_ROOT/<port>.lock"` (`JUNIPER_EXP_LOCK_ROOT`, default `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments`) plus an `ss` probe. The lockdir serializes experiment launchers against each other; a foreign binder can still race — that surfaces as the service's own bind failure through the health gate.

#### Concurrency (Wave 5)

`cascor_up` exports `JUNIPER_CASCOR_SNAPSHOTS_DIR=$RUN_DIR/snapshots` (W-6), so each run's cascor writes snapshots into its own `RUN_DIR` instead of the shared root `juniper-cascor/cascor-snapshots/` (the `.h5`-debris class). This is the sanctioned use of the override: the shared root is the default precisely so CLI, service, and container runs find each other's models, and a per-run root is the opt-out for isolated experiments; concurrent bench runs use `python -m bench.run_benchmark --results-dir` (W-7, juniper-recurrence). Two live runs are fully isolated — disjoint ports via the lockdirs, and `--down` of one run touches nothing of the other (pinned by `TestTwoRunConcurrency`).

**Q-6 is resolved (2026-08-15) and the one-cascor-per-checkout rule is retired.** `cascor_up` now also exports `JUNIPER_CASCOR_LOG_DIR=$RUN_DIR/logs` (juniper-cascor#523), so each run's cascor writes its own file log instead of the repo-shared `logs/juniper_cascor.log` (H-7). Requires `juniper-cascor` carrying that override; against an older cascor, the export is simply ignored, and the shared-log constraint below still applies.

Why this mattered more than ordinary log interleaving: **cascor's parent logger writes only to that file** — stdout carries just candidate-worker lines — so the markers that decide a run's verdict (`Training completed`, `Completed solving …`) exist nowhere else. A second cascor process in the same checkout does not merely mix the logs; it **rotates the evidence away**, which is how the F-P1-3 arm A/B run logs were lost. One other cascor process is enough, so the previous mitigation (using a distinct checkout per instance) never actually protected a single run against a long-lived service that shares its checkout.

Data and recurrence instances never had a per-checkout constraint.

#### F-6 listener pid rule (binding)

`$!` after `( cd … && nohup <server> … & )` is the backgrounded **subshell**, not the server. No `*_up` records `$!`. After the health gate, `record_listener_pid` writes the listener from `ss -tlnpH "sport = :<port>"` plus the process cmdline. Teardown kills pidfile-first only after proving the pid is alive, owned by the current uid, and still running the recorded cmdline (sending SIGTERM, then a bounded SIGKILL).

If the pidfile path refuses (pid gone, wrong uid, or cmdline no longer matches — the pid-reuse class), `stop_service` logs `pidfile path refused — falling back to the recorded port <N>` and kills via `ss` **only** on that run's recorded port. A listener still present after both attempts logs a WARNING. `artifacts/` is never deleted.

#### Partial-failure teardown (`do_up` → `teardown_run`)

`do_up` writes `ports.json` **before** any `*_up` launch, so a half-started run is still teardown-able. Launch order is data → cascor → recurrence; the first failing leg sets `failed=1` and skips later services.

On failure (live mode, not `--dry-run`):

1. Logs `ERROR: bring-up failed — tearing the partial run back down (logs kept under ${LOG_DIR})`.
2. Calls `teardown_run "${RUN_ID}"` (same path as `--down`): reverse-order `stop_service`, release port lockdirs, write `teardown.json`, keep `artifacts/` + `logs/`.
3. Returns `1` (does **not** leave the partial listeners/locks for the operator to discover later).

`--dry-run --up` never creates dirs or calls `teardown_run`. After a live partial failure, inspect `$RUN_DIR/logs/` and `$RUN_DIR/teardown.json`; re-run `--up` only after confirming the port range is free (`ss` / lockdirs under `JUNIPER_EXP_LOCK_ROOT`). Source: `util/experiment_stack.bash` `do_up` / `teardown_run`. Pidfile-refuse → port fallback coverage: open juniper-ml#923 (`TestTeardownBehaviour`).

#### Health / conda

- `wait_for_health` polls every **2s** until `JUNIPER_EXP_HEALTH_TIMEOUT` (default **90** — sized for cold start; recurrence imports alone can take 10–15s).
- Default launch uses direct env-bin paths (`${JUNIPER_EXP_CONDA_DIR}/envs/<env>/bin/...`). Set `JUNIPER_EXP_CONDA_ACTIVATE=1` only if an env grows `activate.d` hooks.
- From a **git worktree**, set `JUNIPER_EXP_PROJECT_DIR` to the ecosystem root — the script's default derivation lands inside `worktrees/` otherwise.

Coverage: `tests/test_experiment_stack_script.py` (incl. live `*_up` compose + pidfile-refuse teardown).

#### OR-list fail-closed bring-up

`do_up` absorbs each leg as `*_up || failed=1`. Bash disables `set -e` inside a function invoked that way, so a bare `require_env_bin` / `activate_conda` / `wait_for_health` / `record_listener_pid` that returns nonzero would **not** stop the function. The pre-fix class: health times out while an `ss` listener is already bound → `record_listener_pid` succeeds → `*_up` returns `0` → `failed` stays `0` → no `teardown_run` → an orphan on `8110`–`8289` plus a false-green `--up`.

| Path | Fail-closed behavior |
|------|----------------------|
| `data_up` / `cascor_up` / `recurrence_up` | `require_env_bin`, `activate_conda`, `wait_for_health`, and `record_listener_pid` each end with `\|\| return 1`, so the OR-list `absorb` sees a real failure |
| `activate_conda` (only when `JUNIPER_EXP_CONDA_ACTIVATE=1`) | `source … \|\| return 1`; `if ! conda activate …; then set -u; return 1; fi` — the trailing `set -u` must not mask an activate failure as exit `0` (ambient-PATH launch). Same class as isolated-stack and plant |
| Mid-`allocate_port` exhaustion | `release_held_locks` before returning, so earlier `*.lock` dirs do not starve a later `--up` |
| Opt-in `--grafana-bridge` after healthy services | `if ! bridge_up`, log `ERROR: grafana bridge failed — tearing the run back down`, call `teardown_run` (live only), return `1` — a bare `bridge_up` under `set -e` used to abort without teardown. `bridge_up` itself pins `require_cmd socat` / `docker`, `discover_gateway_ip`, `relay_up`, and both target-file writes with `\|\| return 1` |

This section is *why* `failed=1` actually fires; what happens once it does is [Partial-failure teardown](#partial-failure-teardown-do_up--teardown_run) above.

#### Staging failure and held port locks

`do_up` allocates ports **before** staging: `allocate_port` records `HELD_LOCK_PORTS` and creates the `*.lock` dirs, then `create_run_dir` → `stage_config` → `write_ports_json`, then the launches.

Each of those three staging steps is fail-closed as `<step> || { release_held_locks; return 1; }` ([#979](https://github.com/pcalnon/juniper-ml/pull/979)). Before that fix they were bare under `set -e`, so a missing `--config` (or an `mkdir` / `cp` / `ports.json` write failure) exited `do_up` *after* the lockdirs existed and *before* `ports.json` was written — `--down` could not recover them (it keys off `ports.json`) and the in-process `HELD_LOCK_PORTS` died with the shell, starving the 30-port ranges until the lockdirs were removed by hand.

If you still find orphaned `*.lock` dirs under `JUNIPER_EXP_LOCK_ROOT` (a pre-#979 run, or a hard kill that outran the trap), clear them only after confirming no live listener holds the port.

### Driver (`util/experiments/run_experiment.py`)

Path-invoked against a live (or already-up) stack from the launcher. Resolves service URLs from `$RUN_DIR/ports.json` unless overridden.

```bash
python util/experiments/run_experiment.py \
  --config path/to/experiment.yaml \
  --run-dir ~/.local/state/juniper-experiments/<RUN_ID>
```

| Flag | Role |
|------|------|
| `--config` / `--run-dir` | Required. YAML + launcher RUN_DIR |
| `--data-url` / `--cascor-url` / `--recurrence-url` | Override `ports.json` |
| `--max-wall-seconds` | Q-2 wall-clock budget (CLI > YAML `outputs.max_wall_seconds` > `3600`) |
| `--stall-seconds` | Cascor: no `current_epoch` progress → `outcome: "stalled"` (default `120`) |
| `--health-timeout` | Per-service health wait (default `90`, matches the launcher) |

Kind selection from YAML shape: `training:` → cascor path; `train:` / `crossval:` / `predict:` → recurrence path. `experiment.seed` is required. Rule-6 infra keys (`service.host` / `port` / `juniper_data_url` / `eval_metrics_enabled`) are rejected (exit `2`).

| Exit | Meaning |
|------|---------|
| `0` | Success (COMPLETED + acceptance) |
| `1` | Acceptance failure (stalled, timed_out, G-6 mismatch, missing essential artifact, predict/crossval fail) |
| `2` | Misuse/validation (bad CLI/YAML/generator, API `422`) |
| `3` | Unreachable (health-wait/connection-failures) |
| `4` | Run-`FAILED`/service-`5xx` |

Always writes §13.4 `manifest.json` (including stalled / timed-out / failed runs). Also writes `artifacts/results/stats.json` + `summary.md` (Wave 2.6; stats failure → `stats_error` on the manifest, never fatal). Plots (Wave 2.4/2.5) render client-side when `outputs.plots` requests them — structurally unavailable data is a per-plot SKIP; render errors / missing matplotlib on a requested plot fail acceptance.

Cascor path polls `GET /v1/training/status` and samples loopback `/metrics` (redirect-following — bare `/metrics` 307s) into `metrics_series.csv`; candidate correlation exists **only** there. Recurrence path uses synchronous `POST /v1/train` (response IS completion; Q-2 budget = socket timeout → `timed_out`). `outputs.save_model: true` re-runs `juniper-recurrence train --dataset <dataset_id> … --out …/model.npz` (G-18).

Coverage: `tests/test_run_experiment.py`.

#### Plot SKIP vs acceptance (`ValueError` contract)

`plots_cascor.py` / `plots_recurrence.py` are lazy-loaded on the headless `Agg` backend (the driver stays importable without matplotlib, and they never import cascor/torch). Every requested plot lands in `manifest["driver"]["plots"]` as `requested` / `rendered` / `skipped`.

| Outcome | Driver behavior | Exit impact |
|---------|-----------------|-------------|
| Applicability skip before a renderer is called (e.g. `n_features != 2`, missing `metrics_final`, predict/crossval disabled or failed) | Recorded SKIP with a `reason` | `0` when otherwise green |
| Renderer raises `ValueError` (the no-renderable-data contract) | Recorded SKIP only; no PNG, **no** acceptance error | `0` |
| Matplotlib / plot-module `ImportError` while `outputs.plots` is non-empty | Every requested name marked SKIP **plus** an acceptance error (`matplotlib unavailable`) | `1` |
| Payload fetch failure (`ServiceUnreachable` / `RunFailed`) or any other render `Exception` | SKIP recorded **and** an acceptance error appended | `1` |

Concrete `ValueError` triggers (not exhaustive) — cascor: an empty decision-boundary `predictions` grid, empty metrics-history rows, no `candidate_correlation` samples in `metrics_series.csv` (G-3 degraded sampling), no scalar eval metrics. Recurrence: prediction-vs-target length mismatch (`forecast_vs_truth` / `residuals`), empty `folds` or no numeric CV metrics, an empty / non-numeric `metrics_table`.

Soft edges that are deliberately **not** a `ValueError`: `render_residuals` silently omits the residual-vs-`target_dt` panel when the optional `target_dt_{split}` length does not match (2 panels instead of 3; a pred/truth mismatch still raises), and `render_crossval_folds` falls back to numeric keys from `folds[0].eval_metrics` when `eval_aggregate` is empty.

```bash
jq '.driver.plots' "$RUN_DIR/manifest.json"
ls "$RUN_DIR/artifacts/plots/"
```

Do not read a SKIP-only `ValueError` as a blank PNG or acceptance regression.

### Perf-lane metrics and baselines

The cascor perf lane gates **work**, not wall-clock. Two quantities look like "how long did it take" and are the wrong ones:

| Quantity | Where it lives | Why it is not a gate |
|---------|----------------|----------------------|
| `wall_seconds` | `aggregate.csv` (the only timing column there) | Absorbs plot rendering and stack bring-up. De-ratified. |
| `timings.drive` | `manifest.json` | Quantized to the driver's 5 s status-poll interval (`DEFAULT_POLL_INTERVAL` in `run_experiment.py`). Measured 2026-09-02: at 20 s cells it understated real spread by 25×–182×, and at a poll boundary it overstated by 5×. Not a bound in either direction. |

The resolving instrument is the cascor step-duration histogram, sampled by the driver into `$RUN_DIR/artifacts/results/metrics_series.csv`. It is poll-independent **and** Prometheus-independent: `scrape_confirmed: false` still carries a complete histogram, because that flag describes the Prometheus scrape, not the series.

The gate is **split** (owner decision 2026-09-02):

| Half | Field | Contract |
|------|-------|----------|
| **WORK** | `step_count` (last sampled `juniper_cascor_training_step_duration_seconds_count`) | Deterministic for a seed-fixed config and contention-immune (identical across 21 cells spanning a 3× speed range). Gated **exactly**. |
| **SPEED** | `mean_step_seconds` = `step_sum` / `step_count` | Carries a 13–20.5% host drift floor. **Reported, never gated.** |

`step_totals` reads the **last** series row that carries the pair. The drive loop samples `/metrics` *before* it tests for termination, so that row is post-completion and the count is exact — which is why zero-tolerance gating is safe. A mid-run sample would fail a correct run.

`scrape_confirmed` is a tri-state (ml#1550): `True` scraped, `False` asked and nothing was there, `None` could not ask (Prometheus unreachable). Never collapse `None` into `False`.

Coverage: `tests/test_read_run_metrics.py`, `tests/test_make_baseline.py`. Design: [`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) (items 0.4 / 1.1 / 1.5). Recurrence has no equivalent timing surface yet (P2 item 3.1) — this reader is cascor-only.

#### Reader (`util/experiments/read_run_metrics.py`)

Canonical reader for both gate halves. Path-invoked; `--sweep` appears in the module docstring but is **not** a CLI flag.

```bash
python util/experiments/read_run_metrics.py SUITE_DIR [SUITE_DIR ...]
python util/experiments/read_run_metrics.py --run RUN_DIR
python util/experiments/read_run_metrics.py SUITE_DIR --json
```

`read_suite` walks `registry.jsonl` and attaches per-cell `config_sha256` (from the registry) plus, as of juniper-ml#1613, `workload_fingerprint` (from the materialised cell YAML). `summarise` is the load-bearing aggregate:

| Field | Meaning |
|-------|---------|
| `work_invariant` | `True` iff every measured cell reports the **same** `step_count` (and at least one count exists). A suite of repeats that fails it is not a set of repeats. |
| `single_workload` (#1613) | `True` iff exactly one distinct fingerprint is present. Kept **separate** from `work_invariant` so "cells ran different configs" and "same config, work moved" stay distinguishable. Unknown identities (`None`) do not collapse into a shared identity — `single_workload` is then `False`. |

The table renderer prints `WORK INVARIANT HOLDS` / `BROKEN` and a `drive` vs `step_sum` spread ratio. JSON (`--json`) is the form that carries fingerprints.

#### Workload identity (juniper-ml#1613)

Owner decision 2026-09-04: a `step_count` mismatch is a **FAILURE**, not a warning. That statement is only true when both sides ran the **same workload**, so identity is checked first:

| Condition | Verdict | What it is |
|-----------|---------|------------|
| Fingerprints differ, or either side is unknown | **REFUSE** | Invalid comparison, not a regression |
| Same workload, `step_count` differs | **FAIL** | Work regression |
| Same workload, `step_count` matches | PASS | Speed is reported, never gated |

Collapsing REFUSE into FAIL is how the gate gets switched off: an ordinary config edit would be reported as a code regression, everyone would learn the gate lies, and it would be disabled while still green.

`registry.jsonl`'s `config_sha256` **cannot** serve as that identity. It hashes the whole materialised cell YAML, including `experiment.description`. PF-1's five repeats differ only there — five cells, five different hashes on `pf1-cascor-spiral-repeats-20260903T040803Z`. A comparator using it would refuse every legitimate comparison, including a suite against its own baseline.

`workload_fingerprint(suite_dir, cell_id)` hashes the same YAML with the cosmetic keys stripped:

| Key | Cosmetic? | Why |
|-----|-----------|-----|
| `experiment.description` | yes | Human label for a repeat ("repeat 1" … "repeat 5") |
| `experiment.name` | yes | Same class |
| `experiment.seed` | **no** | Changes the computation; two seeds are two workloads |
| `training.params.*` (e.g. `max_epochs` / `output_epochs`) | **no** | Computation-relevant; the pre-/post-cascor#618 boundary moves the hash |

Missing or unreadable `cells/<cell_id>/experiment.yaml` returns `None`, not a shared identity. Measured both directions: stable `52184ba2…` across all five PF-1 repeats; `d09edcc1…` pre-cascor#618 vs `52184ba2…` post-fix.

`make_baseline` records the fingerprint per scenario and **refuses** a suite whose cells ran different workloads. That is distinct from the work-invariant refusal.

The split **comparator** (`util/experiments/compare_baseline.py`, P2 item 1.2) is **not shipped**. The planned escape `--accept-work-change "<reason>"` does not exist yet; do not invent a flag. Until 1.2 lands, a deliberate workload change is a **new baseline** (tags supersede by name). Whether the run tier ever gates CI remains open (P1 design §6).

#### Baseline (`util/experiments/make_baseline.py`)

Writes the Q-8 directory in §4 of [`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md). **Operator-invoked only** — never called from `run_suite.py` or `run_experiment.py`; there is no auto mode. A run that promotes itself can launder a bad number into the reference.

```bash
python util/experiments/make_baseline.py --tag pf1-2026-09-03 --suite SUITE_DIR
python util/experiments/make_baseline.py --tag t --suite A --suite B --dry-run
python util/experiments/make_baseline.py --tag t --suite SUITE_DIR --accept-warnings   # recorded, not silent
```

Layout under `--run-root` (default `~/.local/state/juniper-experiments`):

```text
baselines/<tag>/
  baseline.json              per-scenario summary + metric_contract
  manifests/<run_id>.json    constituent run manifests, copied verbatim
  HOST.json                  hardware + thread budget + torch/numpy at capture time
```

`HOST.json` is load-bearing, not metadata. The run-tier regression definition is "same YAML, same hardware, same thread budget". torch/numpy versions come from **this** interpreter (manifests record only `juniper-*`); a python mismatch is recorded as `versions.caveat` rather than assumed.

There is **no `--force`**. Overwriting a tag in place is the one operation retention forbids, so the flag is absent. Want a different baseline? New tag. Tags must be a single path segment (no `/`, no leading `.`). Refusals and misuse exit `2`. `--dry-run` validates and prints JSON, writes nothing.

| Refusal | Why |
|---------|-----|
| No `registry.jsonl` / no cells | Nothing to bless |
| Any cell `outcome != succeeded` | Failed cells are not a reference |
| `work_invariant` is false | `step_count` moved between cells — these are not repeats |
| Cells ran different workloads (#1613) | `single_workload` is false — a scenario must be one workload |
| Missing `step_count` | Cannot baseline an unmeasured run |
| `validation_warnings` present | Re-run clean, or pass `--accept-warnings` (sets `accepted_warnings` in `baseline.json`) |
| Target directory already exists | Supersede by name |
### Run lister / pruner (`list_runs.py`)

`util/experiments/list_runs.py` is the Wave 7.2 safety-gated lister for experiment `RUN_DIR`s (CLI experimentation plan §13.3). It is **directory-truth**: it scans convention-named children of `--run-root` and never reads `run_suite.py`'s append-only `index.jsonl` (Wave 7.1 does write that file). `--down` stops services and keeps `artifacts/`; `--prune --yes` deletes the whole directory.

```bash
python util/experiments/list_runs.py
python util/experiments/list_runs.py --json --state down
python util/experiments/list_runs.py --older-than 7 --state stale
python util/experiments/list_runs.py --prune --older-than 7 --dry-run
python util/experiments/list_runs.py --prune --older-than 7 --yes   # destructive
```

`--run-root` defaults to `~/.local/state/juniper-experiments`. Unlike the launcher and `run_suite.py`, this tool **does not** read `JUNIPER_EXP_RUN_ROOT` — pass `--run-root "$JUNIPER_EXP_RUN_ROOT"` when you overrode the default.

A directory is a run only when its name matches `<UTC yyyymmddThhmmssZ>-<4 hex>` (the launcher's `RUN_ID`). Everything else — `suites/`, `index.jsonl`, soak probe dirs, ad-hoc folders — is ignored.

| State | Meaning |
|-------|---------|
| `down` | `teardown.json` present (checked first) |
| `up?` | no teardown, and at least one `*.pid` whose pid is alive **and** still running the sibling `*.cmdline` (F-6, read-only here) |
| `stale` | no teardown and no live recorded pid (crash, reap, or dead pidfile) |

`--state up` matches the tentative `up?` label. A malformed pidfile or missing `.cmdline` is skipped; if none qualify, the run is `stale`. A dead pid with a recorded cmdline is `stale` (pinned).

`--prune` removes only `down` / `stale` rows that also match `--older-than` (when given). `up?` always prints `SKIP (live recorded pid)` and is never removed, even with `--yes`. `--prune` without `--yes`, or any `--dry-run`, prints `WOULD PRUNE` and deletes nothing. `main()` returns `0` on every successful invocation; argparse misuse is exit `2`.

`--json` emits `{run_root, runs, pruned}`. Each row carries `run_id`, `created_utc`, `state`, `experiment` / `ports` from `ports.json` (`data` / `cascor` / `recurrence` only), `cells` (relative paths with `manifest.json` one or two levels down), `has_root_manifest`, and `path`. `--older-than` drops rows whose `created_utc` is missing.

Coverage: `tests/test_list_runs.py` (hermetic `RUN_ROOT` fixtures; no live launcher state).
### Suite driver

`util/experiments/run_suite.py` expands a suite YAML into cells, then for each cell runs `--up` → `run_experiment.py` → `--down`. It is the Wave 7.1 / 7.5 multi-run layer (plan §13.1 / §13.2). Coverage: `tests/test_run_suite.py`. Shipped suites live under `util/experiments/suites/**` and must pass the R-6 load gate (`tests/test_experiment_suite_yamls.py`).

```bash
# Preview the expansion (writes nothing)
python util/experiments/run_suite.py --suite util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml --dry-run

# Run, then resume only the cells that have not already succeeded
python util/experiments/run_suite.py --suite path/to/suite.yaml
python util/experiments/run_suite.py --suite path/to/suite.yaml --resume <SUITE_ID>
python util/experiments/run_suite.py --suite path/to/suite.yaml --only c000-deadbeef
```

| Exit | Meaning |
|------|---------|
| `0` | Every executed cell succeeded (and `--dry-run`) |
| `1` | Suite finished with at least one failed / stalled / timed-out cell, or aggregation found none succeeded |
| `2` | Misuse / suite-validation (`SuiteError`, unknown `--only` id, `--resume` dir missing) |

`--compare-baseline TAG` pastes a standalone comparator verdict into `REPORT.md` and **never** changes this exit code. Use `util/experiments/compare_baseline.py` when you want the comparator's own 0/1/2.

#### Suite YAML

`schema_version` must be `1`. Allowed top-level keys: `schema_version`, `suite`, `execution`, `matrix`, `include`, `exclude`, `outputs`. Unknown keys exit `2` (the `stall_second` typo class).

| `suite.` | Constraint |
|----------|------------|
| `name` | Required |
| `app` | `cascor` or `recurrence` |
| `base_config` | Non-empty list of experiment YAML paths, resolved relative to the suite file |
| `seed_policy` | `fixed` (default) or `per_cell` (`experiment.seed` and `dataset.params.seed` become `base + cell.index`) |

`matrix` is an `itertools.product` of dotted-path → non-empty lists. `exclude` drops an exact override match. `include` appends extra cells that carry **only** their own `overrides` — they do **not** inherit the matrix. PF-1's repeats are a matrix axis of `experiment.description` for that reason: expressing repeats as `include` while putting the workload in `matrix` would run one real cell and N inherited smokes.

Cell ids are `c{index:03d}-{sha8(relative_config + sorted_overrides)}`. The hash uses the **relative** `base_config` string so ids stay identical between the canonical checkout and a `JUNIPER_EXP_PROJECT_DIR` rebase.

#### Execution knobs

| `execution.` | Default | Role |
|--------------|---------|------|
| `mode` | `sequential` | `parallel` + `max_parallel > 1` starts a bounded pool |
| `max_parallel` | `1` | Worker count; ignored unless `mode: parallel` |
| `continue_on_failure` | `true` | `false` stops submitting (parallel drains already-running cells) |
| `per_run_timeout_seconds` | `3600` | **Subprocess** kill from the outside — records `timed_out` with no honest driver manifest |
| `stall_seconds` | omitted | Forwarded as `--stall-seconds`; absent ⇒ driver keeps `120` |
| `max_wall_seconds` | omitted | Forwarded as `--max-wall-seconds`; absent ⇒ driver keeps its YAML / `3600` default |

Size `per_run_timeout_seconds` **above** the wall budget so the driver is the one that stops. The Q-2 stall detector watches `current_epoch`, which does not advance during candidate-pool training — pool ≥ 16 or cap ≥ 64 cascor cells need an explicit `stall_seconds` (R-6 enforces this on shipped suites). A dotted `outputs.max_wall_seconds` override is also accepted (E-I uses that form).

**Cascor parallel is version-gated.** `app: cascor` + `max_parallel > 1` requires the **launched** cascor tree ≥ `0.10.0` (`CASCOR_PARALLEL_FLOOR`; `JUNIPER_CASCOR_LOG_DIR` / cascor#523). The version is read from that tree's `pyproject.toml`, not `importlib.metadata` (the driver env is not what uvicorn serves).

Resolution: `JUNIPER_EXP_CASCOR_SRC_DIR` parent, else `$JUNIPER_EXP_PROJECT_DIR/juniper-cascor`, else an ancestor probe for a `juniper-cascor` sibling. Unreadable version **refuses** (exit `2`). Sequential cascor and any recurrence parallel are never gated.

Parallel cells get the H-11 budget: `max(1, nproc // (2 * max_parallel))`. Cascor pins BLAS at 2 and sets `CASCOR_NUM_PROCESSES`; recurrence sets the BLAS vars to the split.

#### Paths, resume, and outputs

Default run root is `$JUNIPER_EXP_RUN_ROOT` (falls back to `~/.local/state/juniper-experiments`). Suite dir is `outputs.suite_dir` if set, else `$JUNIPER_EXP_RUN_ROOT/suites/<suite_id>`. A fresh `suite_id` is `<name>-<UTC yyyymmddTHHMMSSZ>`; `--resume SUITE_ID` reuses that id. When `outputs.suite_dir` is unset, pass the existing directory's basename.

`--resume` skips only cells whose `registry.jsonl` outcome is `succeeded`. Failed / stalled / timed-out / not-run cells run again. `--dry-run` prints the expansion and the exact `--up` / driver / `--down` lines, creates no directory, and appends no `index.jsonl`.

Each cell writes:

- `$SUITE_DIR/cells/<cell_id>/experiment.yaml` — materialised, driver-validated YAML
- `$SUITE_DIR/registry.jsonl` — append-only per-cell row (lock-safe under parallel)
- `$JUNIPER_EXP_RUN_ROOT/index.jsonl` — `{suite_id, cell_id, run_id, outcome, run_dir}` (the suite's own index, not a directory-truth listing)
- `$SUITE_DIR/suite_manifest.json`, `aggregate.csv`, `REPORT.md`

`--up` is invoked with `--experiment <cell_id>` and the process env gets `JUNIPER_CASCOR_CELL_ID` plus `JUNIPER_CASCOR_EXPERIMENT=<suite.name>` so snapshots record both identities.

`JUNIPER_SUITE_GRAFANA_BRIDGE=1` (also `true` / `yes` / `on`) adds `--grafana-bridge` to every `--up`. It is an **env toggle, not a suite key** — a suite key would change every cell's `config_sha256` between a bridged and an unbridged run of the same YAML. Off by default; unbridged runs stay `UNSCRAPED`. The host file_sd discover+scrape cycle is 15 s + 15 s, so a cell shorter than that still yields no step-duration histogram even with the bridge on (PF-1's duration is load-bearing for that reason).

#### `JUNIPER_EXP_PROJECT_DIR` rebase

Sibling `base_config` walks (`../../../../juniper-cascor/conf/experiments/…`) assume the canonical layout. When `JUNIPER_EXP_PROJECT_DIR` is set, the path is rebased onto it from the first `juniper-*` component. The override **wins** over a literal that also exists — otherwise a worktree-pinned cascor would take CODE from the worktree and CONFIG from the primary. A rebase that does not exist on disk falls back to the literal (stale override degrades; it does not hard-fail).

Test seams (operator-visible): `JUNIPER_SUITE_LAUNCHER`, `JUNIPER_SUITE_DRIVER`, `JUNIPER_SUITE_PYTHON`.

#### Suite-author pitfalls

- **`include` does not inherit `matrix`.** Repeats of one workload belong on a matrix axis (see `suites/perf/pf1-cascor-spiral-repeats.yaml`).
- **`max_epochs` and `output_epochs` are a matched pair** on the cascor service. Setting only `max_epochs` bounds the *initial* output pass; later passes fall back to 10000. Any CLI-vs-service comparison (and any suite that claims a duration) must set both to the same value. PF-1 pins both at 4000.
- **Unknown `execution:` keys exit `2` immediately.** The R-6 gate exists because a `stall_second` typo otherwise surfaces hours into a GPU campaign.
- Do not point suite ports at `plant_all` / isolated-stack ports. The suite driver never launches canopy.

### Environment overrides

| Variable | Default | Description |
|----------|---------|-------------|
| `JUNIPER_EXP_RUN_ROOT` | `~/.local/state/juniper-experiments` | Durable run root (not `/tmp`) |
| `JUNIPER_EXP_LOCK_ROOT` | `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments` | Ephemeral port lockdirs |
| `JUNIPER_EXP_PROJECT_DIR` | parent of juniper-ml | Ecosystem root (set this in worktrees) |
| `JUNIPER_EXP_DEPLOY_DIR` | `<ecosystem>/juniper-deploy` | Prometheus targets dir for `--grafana-bridge` |
| `JUNIPER_EXP_CONDA_DIR` | `/opt/miniforge3` | Conda/miniforge root |
| `JUNIPER_EXP_DATA_CONDA` | `JuniperData` | Data env name |
| `JUNIPER_EXP_CASCOR_CONDA` | `JuniperCascor1` | Cascor env name |
| `JUNIPER_EXP_RECURRENCE_CONDA` | `JuniperCascor1` | Recurrence env name (same default as cascor) |
| `JUNIPER_EXP_HEALTH_TIMEOUT` | `90` | Per-service health wait (seconds) |
| `JUNIPER_EXP_KILL_TIMEOUT` | `10` | SIGTERM → SIGKILL grace (seconds) |
| `JUNIPER_EXP_CONDA_ACTIVATE` | `0` | `1` = `conda activate` instead of direct env-bin |
| `JUNIPER_SUITE_GRAFANA_BRIDGE` | unset | `1` / `true` / `yes` / `on` adds `--grafana-bridge` to every suite `--up` (never a suite-YAML key) |
| `JUNIPER_SUITE_LAUNCHER` / `JUNIPER_SUITE_DRIVER` / `JUNIPER_SUITE_PYTHON` | in-tree defaults | Test / operator seams for the suite driver |

### Troubleshooting

| Symptom | Check / Fix |
|---------|-------------|
| Misuse exit `2` on `--up` | Need exactly one action and at least one of `--cascor` / `--recurrence`. |
| Health timeout mid-`--up` | Inspect `$RUN_DIR/logs/`; cold recurrence often needs the default `90s` — raise `JUNIPER_EXP_HEALTH_TIMEOUT` only after fixing the service. Partial bring-up should already have called `teardown_run` (see above). |
| `bring-up failed — tearing the partial run back down` | Expected on a failed `*_up` leg — `do_up` auto-tears down. Check `$RUN_DIR/logs/` + `teardown.json`; confirm port locks released under `JUNIPER_EXP_LOCK_ROOT` before retrying. |
| Worktree can't find cascor `src/` | Set `JUNIPER_EXP_PROJECT_DIR` to the real ecosystem root. |
| Teardown killed the wrong process / left orphans | Pre-F-6 `$!` class — confirm pidfiles came from `record_listener_pid` (post-health `ss`), not shell `$!`. |
| Log says `pidfile path refused — falling back to the recorded port` | Pid reuse / cmdline mismatch refused the pidfile kill; port fallback should still stop **this run's** listener. If WARNING persists, inspect `ss -tlnpH "sport = :<port>"` before reuse. |
| `--status` says UNSCRAPED | Expected without `--grafana-bridge`; opt in only when `socat` + deploy `prometheus/targets/` are available. |
| Driver exit `2` on YAML | Unknown block/key, missing `experiment.seed`, or rule-6 infra key — see stderr. |
| Driver exit `2` `POST /v1/datasets rejected (422)` on csv_import | Source over the 128 MiB cap without opt-in — [CSV Import Byte Cap](#csv-import-byte-cap). |
| Driver exit `2` `dataset.split` / `from_dataset_split` | Recurrence allow-list is `{train, test, full}`. `"validation"` is refused today; `X_val` is design-closed, not shipped. See [Partition Contract](#train--val--test-partition-contract). |
| Driver exit `1` `stalled` / `timed_out` | Cascor: raise `--stall-seconds` / `--max-wall-seconds` only after confirming the run is still progressing; recurrence `timed_out` is the train socket budget. |
| Missing correlation / empty plot | Correlation is only in the driver's `metrics_series.csv` (not `/v1/metrics/history`). A `/metrics` 404 degrades sampling (G-3), not the run. |
| `--down` deleted results | `--down` must keep `artifacts/`. If results are gone, you either pointed at the wrong `RUN_ROOT` or ran `list_runs.py --prune --yes` (that path deletes the whole `RUN_DIR`). |
| `list_runs.py` shows `No experiment runs` but the stack wrote a RUN_DIR | Default `--run-root` ignores `JUNIPER_EXP_RUN_ROOT`. Pass `--run-root` to the overridden root. Non-convention names (soak probes, `suites/`) are invisible by design. |
| `WOULD PRUNE (missing --yes)` / `--dry-run` | Expected — nothing was removed. Destructive prune needs `--prune --yes` without `--dry-run`. |
| `SKIP (live recorded pid)` after `--prune --yes` | The run classified `up?` (F-6 pid+cmdline still match). `--down` it first; do not delete a live listener by hand from this tool. |
| `--up` exited `0` but a listener remains / the next `--up` starves | OR-list false-green class — confirm the `\|\| return 1` pins (`rg -n 'wait_for_health.*\|\| return 1' util/experiment_stack.bash`). Run `--down <RUN_ID>`, then clear any stale `$JUNIPER_EXP_LOCK_ROOT/<port>.lock`. |
| `grafana bridge failed — tearing the run back down` | Expected when `--grafana-bridge` cannot preflight `socat` / `docker`, relay, or write the target file after the services are healthy — the run is already torn down. Install the tools or omit the flag. |
| Port range exhausted after a failed `--config` | Staging aborted after `allocate_port` and before `ports.json`, so `--down` cannot release the lockdirs (open #979). Clear `*.lock` under `JUNIPER_EXP_LOCK_ROOT` only once no live listener holds the port. |
| Plot `skipped` with a `ValueError` reason, exit `0` | No-renderable-data SKIP, not an acceptance failure — inspect `jq '.driver.plots' $RUN_DIR/manifest.json`. |
| Exit `1` with `matplotlib unavailable` | Install matplotlib in the driver env, or drop `outputs.plots` from the YAML. |
| `residuals.png` has only 2 panels | Optional `target_dt_*` missing or length-mismatched — pred/truth still plotted; not a SKIP. |
| Driver exit `2` on default `equities` / API `422` | Universe exceeded the **14-symbol** cap. Set `dataset.params.symbols` to ≤14 names, or opt in with `allow_truncation: true` (permanent `DatasetMeta.truncation`). See [Equities Symbol Cap](#equities-symbol-cap). |
| Gating on `aggregate.csv` `wall_seconds` or `timings.drive` | De-ratified — read `metrics_series.csv` via `read_run_metrics.py` (last row is the exact `step_count`). |
| `scrape_confirmed` is `None` / "Prometheus down" | Tri-state "could not ask", not a missing histogram — the series is still the gate input. |
| `make_baseline` exit `2` `NOT invariant` | `step_count` differed across cells — not a set of repeats; do not `--accept-warnings` this away. |
| `make_baseline` exit `2` `different workloads` | Fingerprints diverged (#1613) — config edit, not host noise. Cut a **new** baseline; there is no `--force` and no `--accept-work-change` yet. |
| Using `config_sha256` as "same workload" | It hashes `experiment.description`; PF-1 repeats all differ. Use `workload_fingerprint` (strips `description`/`name`, keeps `seed`). |
| `make_baseline: … already exists` | Retention: supersede by a new `--tag`. The overwrite flag is deliberately absent. |
| Blessing from `run_suite` / a self-promoting run | Not hooked up — operator-invoked only. `--dry-run` first. |
| Suite exit `2` `unknown execution: keys` | Typo in `execution:` (`stall_second`, …). The R-6 gate (`tests/test_experiment_suite_yamls.py`) catches this on shipped suites. |
| Suite exit `2` cascor `max_parallel > 1` | Launched tree below `0.10.0` or version unreadable. Use `mode: sequential`, or point `JUNIPER_EXP_CASCOR_SRC_DIR` / `JUNIPER_EXP_PROJECT_DIR` at a ≥ floor tree. |
| Suite cells `stalled` at ~130 s then finish | Candidate-phase inert stall — set `execution.stall_seconds` (and size `per_run_timeout_seconds` above the wall). |
| `--resume` re-runs a succeeded cell | Only `outcome == succeeded` is skipped; check `$SUITE_DIR/registry.jsonl`. `--resume` dir missing is exit `2`. |
| Bridged vs unbridged PF-1 hashes differ | `JUNIPER_SUITE_GRAFANA_BRIDGE` leaked into the YAML. Keep it an env toggle. |
| Worktree suite takes primary cascor YAML | `JUNIPER_EXP_PROJECT_DIR` rebase must win — confirm the rebased `juniper-cascor/conf/experiments/…` exists. |
| Repeats are not repeats | `include` cells do not inherit `matrix`. Put the repeat axis on `matrix` (PF-1's `experiment.description` list). |
| `make_baseline` / `compare_baseline` names "no countable work" on a recurrence suite | Expected — recurrence has no work-done counter. Report the run (`read_run_metrics.py --run RUN_DIR --json`); do not cut a speed-only baseline. See [Recurrence Work Is Not Countable](#recurrence-work-is-not-countable). |
| Recurrence `work_invariant` is false even when every cell looks the same | Third state: `work_countable` is false, so the invariant is false because the question does not apply — not because the counts differed. Use `--json`; the human table is cascor-shaped. |

Do **not** point experiment ports at `plant_all` / isolated-stack ports, and do not use this launcher when you need canopy (use `isolated_stack.bash` or the host stack instead).

Q-8 baselines and the split comparator are a **separate** operator surface: [Perf-Lane Work Gate](#perf-lane-work-gate). A `compare_baseline.py` FAIL is now interpretable — it means the workload, host, termination branch and measurement all matched and `step_count` still moved. Do not wire that tool to CI: whether the run tier gates at all is an unmade **owner** decision (§6 of the P1 design), not a soundness question.

---

## Perf-Lane Work Gate

The Q-8 run-level tools are on main: `util/experiments/read_run_metrics.py` (reader), `make_baseline.py` (writer), `compare_baseline.py` (split comparator). They implement the rule in item 1.5 / §2.2 of [`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) and the directory contract in §4 of [`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md).

**The determinism question is SETTLED, and the reason not to CI-wire has changed.** Consensus
validation ([juniper-ml#1710](https://github.com/pcalnon/juniper-ml/pull/1710)) produced a
counterexample — identical `workload_fingerprint`, seed, and host, all `outcome: succeeded`,
different `step_count` — and a corpus census then explained it. Over 333 runs / 153 distinct
configs, **79 configs repeat, 29 of those diverge in `step_count`, and all 29 are explained by
`completion_reason`: zero remain divergent within a termination branch.** So `step_count` is exact
and deterministic *given how training ended*; the original contract simply omitted that condition.
[`ml#1733`](https://github.com/pcalnon/juniper-ml/pull/1733) made the branch part of the
precondition, so a branch flip now **REFUSES (exit 2)** instead of FAILing.

Read the census caveat before leaning on it: the 29 divergent configs partition into 74 branches,
**54 of them singletons**, where within-branch agreement is definitionally guaranteed. Only **20
branches have n≥2** and genuinely corroborate. No counterexample exists, but the finding rests on
20 real comparisons.

The P2 plan's "invariance follows from the iteration cap" attribution was **misattributed** and is
withdrawn: every PF-1 run at both 20 s and 65 s terminates `early_stopped`, so none is cap-bound.
The 21-cell invariance is a real empirical regularity with the wrong stated cause.

**Do not wire `compare_baseline.py` to CI — but for a different reason than this section used to
give.** The tool is now safe on its own merits (see the refusal ladder below). What remains open is
a **policy** question that belongs to the owner: *whether the run tier gates CI at all*, §6 of the
P1 design. Item 1.4 deliberately leaves `run_suite`'s exit code untouched by a verdict pending that
decision, and a test is named for it. `ci.yml` already runs the **unittests**; that is not the same
as a run-tier gate against a blessed baseline.

### What each tool does

| Tool | Role | Operator fact |
|------|------|----------------|
| `read_run_metrics.py` | Canonical reader for the two ratified inputs | Last row of `artifacts/results/metrics_series.csv` that carries `juniper_cascor_training_step_duration_seconds_{sum,count}`. The drive loop samples `/metrics` **before** it tests termination, so that last row is taken after training completed. |
| `make_baseline.py` | Operator-invoked Q-8 writer | Writes `~/.local/state/juniper-experiments/baselines/<tag>/{baseline.json,HOST.json,manifests/}`. Never called from `run_suite.py` / `run_experiment.py`. **No `--force`**: a tag is superseded by name. |
| `compare_baseline.py` | Split comparator | WORK (`step_count`) compared with `==`. SPEED (`mean_step_seconds`) reported, never gated. Identity (`workload_fingerprint`) is checked first; a mismatch is REFUSED, not FAIL. |

De-ratified (do not gate on these): `aggregate.csv`'s `wall_seconds` (absorbs plot render + stack bring-up) and `timings.drive` (quantized to the 5 s poll; can understate or overstate real spread). `config_sha256` cannot serve as identity — it hashes the whole cell YAML, including `experiment.description`, so PF-1's five repeats all hash differently.

```bash
python util/experiments/read_run_metrics.py SUITE_DIR [SUITE_DIR ...]
python util/experiments/read_run_metrics.py --run RUN_DIR
python util/experiments/make_baseline.py --tag pf1-2026-09-03 --suite SUITE_DIR
python util/experiments/make_baseline.py --tag t --suite A --suite B --dry-run
python util/experiments/compare_baseline.py --baseline pf1-2026-09-03 --suite SUITE_DIR
python util/experiments/compare_baseline.py --baseline t --suite S --accept-work-change "cascor#618 raised the epoch budget"
```

Default `--run-root` is `~/.local/state/juniper-experiments` (`JUNIPER_EXP_RUN_ROOT`). `--sweep` is docstring-only on the reader — there is no such flag.

### Exit codes (do not collapse 1 and 2)

| Exit | Verdict | Meaning |
|------|---------|---------|
| `0` | PASS or WAIVED | Same workload, work matched — or an operator blessed a work change with `--accept-work-change REASON` |
| `1` | FAIL | Same workload, same host, **same termination branch**, every cell `succeeded` and measured — and `step_count` still moved. Since `ml#1733` this is interpretable: a cross-branch flip lands on `2`, not here. |
| `2` | REFUSED | Cannot compare — see the refusal ladder below. A waiver **cannot** override a refusal (`render` must print `had NO effect`). |

Whitespace-only `--accept-work-change` is exit 2. Prefer cutting a **new baseline tag** over a waiver — tags supersede by name and are cheap.

**Precedence is FAIL > REFUSED > PASS, and the order is load-bearing.** It used to be `if reasons:
REFUSED` first, so one unreadable `--suite` on the command line converted a *real* FAIL on another
suite into a REFUSE — and a caller treating exit 2 as "cannot compare, don't block" would lose the
regression. `ml#1733` made that worse by adding four more refusal paths; `ml#1743` fixed the
ordering. A positively-detected work regression is knowledge and wins; a refusal only means "could
not verify", which must still beat PASS, so an unverifiable comparison never reports clean. Host
and baseline-load failures (`basis_reasons`) are the one exception that outranks FAIL — without a
valid basis there is nothing to have detected.

### Identity and host

`workload_fingerprint()` hashes the cell YAML with `experiment.description` / `name` stripped and `experiment.seed` kept. Two runs at different seeds are different workloads.

Host blocking (REFUSE): `cpu_model`, `cpu_count`, `thread_budget`. Advisory only (reported, never a refusal): `torch`, `numpy`, `python_runs`. Not compared: RAM, GPU, platform, `python_tool`. `HOST.json` is load-bearing: without it the comparison silently becomes cross-hardware. Torch/numpy versions come from **this** interpreter; a python mismatch is recorded as a caveat, not assumed away.

### Writer vs comparator — the asymmetry, now CLOSED

**The asymmetry is closed.** It was real, and this section used to document it as a live hazard:
`make_baseline` refused inputs the comparator quietly accepted, so a PASS did not mean "every cell
succeeded and was measured." [`ml#1741`](https://github.com/pcalnon/juniper-ml/pull/1741) and
[`ml#1743`](https://github.com/pcalnon/juniper-ml/pull/1743) imported every one of those refusals
into `compare_baseline`. Verified against the source on `origin/main`:

| Input | `make_baseline` | `compare_baseline` |
|-------|-----------------|--------------------|
| Any cell `outcome != succeeded` (incl. `timed_out`) | REFUSE | REFUSE (A2) |
| Any cell with `step_count is None` | REFUSE | REFUSE (A1) — no longer dropped before uniqueness |
| Any cell `step_count == 0` | REFUSE | REFUSE (A4) — an equal count of nothing proves nothing |
| Candidate `step_count` spread across cells | REFUSE ("not repeats") | REFUSE (same) |
| Cells ended on **different termination branches** | REFUSE | REFUSE (`ml#1733`) |
| Baseline records **no** `completion_reason` (cut pre-guard) | n/a | REFUSE — fails closed on both sides |
| Baseline holds duplicate workload fingerprints | n/a | REFUSE (A7) — collision detected, not resolved arbitrarily |
| Candidate covers only some baseline scenarios | n/a | REFUSE (A6) — names the uncovered ones |
| Recurrence / `work_countable: False` | REFUSE | REFUSE (speed alone is not gated; source comments quote a 13–20.5% host drift floor) |
| Any cell `outcome != succeeded` | REFUSE | `outcome` is still not read. Truncating **reasons** (`timed_out` / `torn_down_early` / `stalled`) REFUSE; a `failed` cell with a non-truncating reason can still PASS |
| Both sides `step_count == 0` | writes a zero-work baseline (if a single non-truncating reason) | PASS (`0 == 0`) |
| Mixed / truncating `completion_reason` | REFUSE | REFUSE (same) |
| Absent `completion_reason` on every cell | writes `completion_reason: null` | REFUSE (fail closed) |

A PASS now does mean "same workload, same host, same termination branch, every cell succeeded and
measured, every baseline scenario covered." That is the whole point of the ladder: the operator
should not have to re-read `manifest.outcome` and the series file to know whether a PASS was earned.

### The refusal ladder (source-verified, `compare()` order)

Each rung `continue`s to the next suite rather than judging it. Order matters — the truncated-
termination check runs before the rest so a driver-stopped run is never mistaken for a measurement:

1. **Truncated termination** — the driver stopped before the workload did, so `step_count` measures
   the *budget*, not the code.
2. **`outcome != succeeded`** (A2) · 3. **`step_count is None`** (A1) · 4. **`step_count == 0`** (A4)
5. **Multiple workloads in one candidate** — its own spread is not a property of the code.
6. **`work_countable: False`** — the WORK half does not apply, and speed alone is not gateable.
7. **Work not invariant across cells** — not a set of repeats.
8. **Mixed termination branches** (`ml#1733`) · 9. **Workload absent from the baseline** — invalid
   comparison, not a regression. 10. **Baseline/candidate branch mismatch.**

Then, after the per-suite loop: **host mismatch** and **duplicate baseline fingerprints** are
`basis_reasons` (they outrank FAIL); **no scenarios compared** and **partial scenario coverage**
(A6) are ordinary refusals.

These are pinned by `tests/test_compare_baseline.py`, which is wired in `ci.yml`.
[`#1713`](https://github.com/pcalnon/juniper-ml/pull/1713) adds further coverage of the A1–A7
refusals. `#1617` / `#1626` (mixed known+unknown identity) and `#1625` (complementary tests) remain
open follow-ups; they are not a license to CI-wire the gate — that call is the owner's, above.

### Recurrence is not countable

`read_run_metrics` returns `work_countable: False` for a recurrence run (`n_epochs` is 1-or-200 by readout type and invariant to `d` / `n_steps`; `n_windows` is input size). `summarise` keeps that as a third state. Both the writer and the comparator refuse rather than quietly compare speed. Report those runs; do not baseline them.

### Troubleshooting

| Symptom | Check / Fix |
|---------|-------------|
| `compare_baseline` FAIL, exit 1, same YAML / seed / host | Interpretable since `ml#1733`/`ml#1743`: the branch, `outcome`, measurement and coverage checks all passed and the count still moved. Investigate the change. Cut a new tag or `--accept-work-change REASON` only once you know *why* it moved. |
| `compare_baseline` REFUSED, "cells ended on different branches" | Not a regression. The candidate terminated differently from the baseline (`early_stopped` vs `below_threshold` is the canonical pair). Re-run, or re-cut the baseline in the branch you mean to track. |
| `compare_baseline` REFUSED, "records no completion_reason" | The baseline predates the `ml#1733` guard (e.g. `pf1-2026-09-04`). Expected — re-cut under a new tag; use `pf1-2026-09-04b` or later. |
| `compare_baseline` PASS, but several cells have no `metrics_series.csv` | **No longer possible** — A1 refuses unmeasured cells. If you see this, the reader drifted; stop and check `read_run_metrics.py`. |
| `compare_baseline` PASS, every cell `timed_out` | **No longer possible** — A2 reads `outcome`. Same stop condition as above. |
| `compare_baseline` REFUSED, exit 2, after a real work miss | **No longer possible** — A3 gives FAIL precedence over REFUSED. A real work miss now exits 1 even when another `--suite` is unreadable. |
| `compare_baseline` REFUSED, "covered N of M baseline scenario(s)" | A6. The candidate did not run every blessed workload; a PASS would have meant only that the ones you ran still match. Run the rest, or cut a narrower baseline. |
| `compare_baseline` REFUSED, "DUPLICATE workload fingerprint(s)" | A7. Two blessed scenarios share a workload, so which one a candidate compares against is arbitrary. Re-cut the baseline from distinct workloads. |
| `compare_baseline` FAIL, exit 1, same YAML / seed / host / **same** `completion_reason` | Treat as a work regression. The guard did not swallow it. Cut a new tag only if the move is deliberate, or waive with a reason. |
| `compare_baseline` FAIL, exit 1, and `TRUNCATING_TERMINATIONS` is absent from the reader | Pre-#1733 checkout — a branch flip is still a false FAIL. Confirm both sides reached the same `completion_reason` by hand, or land / cherry-pick #1733. |
| `compare_baseline` REFUSED, "baseline … records no completion_reason" | Expected for tags cut before #1733. Re-cut under a new name (`pf1-2026-09-04` → `pf1-2026-09-04b`). |
| `compare_baseline` REFUSED, "deterministic only WITHIN a termination branch" | Branch flip (6496 `early_stopped` vs 6095 `below_threshold`). Not a work regression. Compare like with like, or re-cut. |
| `compare_baseline` REFUSED, "driver stopped before the workload did" | Candidate (or its cells) ended `timed_out` / `torn_down_early` / `stalled`. Raise the budget and re-run; do not gate on a truncated histogram. |
| `make_baseline: … already exists` | No `--force`. Choose a new tag. |
| `make_baseline` refuses `validation_warnings` | Re-run clean, or pass `--accept-warnings` (recorded in `baseline.json`). |
| `workload … is not in baseline` / `INVALID comparison` | Fingerprint mismatch (often a real config edit, or `output_epochs` / seed). Not a work regression. |
| Host REFUSED (`cpu_model` / `cpu_count` / `thread_budget`) | Cross-hardware. Re-run on the baseline host or cut a new baseline. |
| Recurrence suite REFUSED "no countable work" | Expected. There is no recurrence work-done counter. |
| Reader says WORK INVARIANT HOLDS, one cell has no series | `summarise` dropped the None. The invariant is only over **measured** cells. |
| Tempted to gate SPEED | Source comments quote a 13–20.5% host drift floor, larger than six competing CPU-bound processes. SPEED is reported, never gated. |

Coverage: `tests/test_read_run_metrics.py`, `tests/test_make_baseline.py`, `tests/test_compare_baseline.py` (wired in `ci.yml`). Those suites pin last-row reads, writer refusals, identity-first compare, exact work, ungated speed, and the 0/1/2 exit split. Since ml#1741 + ml#1743 they also pin the A1-A7 refusals; #1713 adds further coverage.


## PF Scenario Suites

Wave 7.3 instruments for the plan §12.3 performance-scenario matrix. They live under `util/experiments/suites/perf/` and run through `util/experiments/run_suite.py`. **Thresholds are unratified** — each file is the instrument, not the verdict. P3 ratifies numbers; a green suite is not a pass/fail gate.

In-tree table: [`util/experiments/suites/perf/README.md`](../util/experiments/suites/perf/README.md). Design of record: [`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md). P2 work items: [`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md).

### Inventory

| ID | File | Measures | Notes |
|----|------|----------|-------|
| PF-1 | `pf1-cascor-spiral-repeats.yaml` | step-duration p50/p95 + wall variance over 5 identical cells | Load-bearing cell length; repeats are a **matrix axis** |
| PF-2 | `pf2-cascor-dataset-scaling.yaml` | wall vs `n_points_per_spiral` `{250, 500, 1000, 2000}` | RSS from the experiments dashboard Process RSS panel |
| PF-3 | `pf3-cascor-pool-scaling.yaml` | speedup vs `candidate_pool_size` × `runtime.num_processes` | Must declare stall **and** wall (below) |
| PF-4 | — | cascor in-repo pytest vs `baseline_20260526.json` | **Not a driver suite.** That baseline has memory keys and **no timing data** (P1 §1) |
| PF-5 | `pf5-recurrence-d-scaling.yaml` | fit time vs `train.d` `{8, 16, 32, 64}` | Thresholds unratified; instrument only |
| PF-6 | `pf6-recurrence-nsteps-scaling.yaml` | fit time vs `dataset.params.n_steps` `{1000, 4000, 16000}` | same |
| PF-7 | `pf7-recurrence-readout-rungs.yaml` | fit time + r² per `train.readout` `{linear, rff, mlp}` | same |
| PF-8 | — | two simultaneous pinned-budget runs | **Not a sequential suite.** Wave 7.5 parallel / two-terminal |

### How to run

```bash
# Inspect first — write nothing
python util/experiments/run_suite.py --suite util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml --dry-run

# Live PF-1 (needs the Grafana bridge for the p50/p95 histogram)
JUNIPER_SUITE_GRAFANA_BRIDGE=1 python util/experiments/run_suite.py --suite util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml
```

`--dry-run` prints the expanded cell list and every command. For PF-1, expect **5 cells**, every one carrying `max_hidden_units: 10`, `max_iterations: 10`, and the matched `max_epochs` / `output_epochs` pair of `4000`. If the dry-run shows fewer than 5 cells, or cells with differing overrides, **stop** — the repeats are not repeats.

Exit `0` = every executed cell succeeded; `1` = suite completed with failed cells (or aggregation found none succeeded); `2` = misuse / suite-validation.

`JUNIPER_SUITE_GRAFANA_BRIDGE` is an **env toggle, not a suite key**. A suite key would change every cell's `config_sha256` between a bridged and an unbridged run of the same scenario — destroying the comparability PF-1 exists to provide (`run_suite.execute_cell`). Off by default: without it the run is UNSCRAPED and `metrics_scraped.scrape_confirmed` is `false`.

### PF-1 load-bearing contracts

Three traps sit between a reader and a usable PF-1 number.

**1. Repeats are a matrix axis, not `include` entries.** `expand_cells` builds the cartesian product of `matrix`, then appends `include` cells that carry **only their own overrides** and do **not** inherit the matrix (`run_suite.py`). Putting the workload in `matrix` and the five repeats in `include` would run one cell at `(10, 10)` and four at the inherited smoke `(2, 2)` — five cells that are not repeats.

PF-1 therefore puts `experiment.description: ["PF-1 repeat 1", …, "PF-1 repeat 5"]` on the matrix next to the budget keys.

**2. `max_epochs` and `output_epochs` must be a matched pair.** The service applies `max_epochs` only to the *initial* output pass; later passes read `output_epochs`, which falls back to 10000. The direct CLI aliases the two. cascor#618 gave `spiral-smoke.yaml` `output_epochs: 50` to match `max_epochs: 50`, which dropped PF-1's cell from 65–126 s / 4012 steps to **15.1 s / 32 steps** — below the scrapeability floor.

The duration requirement belongs in PF-1's override, not in a smoke config. Calibrated 2026-09-02 at `(10, 10)` (`util/ad-hoc/2026-09-02_pf1_epoch_calibration_suite.yaml`):

| epochs   | 50     | 500    | 2000   | 5000   |
|----------|--------|--------|--------|--------|
| step_sum | 10.5 s | 22.2 s | 34.6 s | 66.1 s |
| steps    | 32     | 230    | 890    | 2210   |

4000 is used (interpolated in the upper segment for ~55 s `step_sum` / ~60 s drive). Both keys are single-element lists so the matrix cannot pair them with anything but each other. Overriding only `output_epochs` would leave `max_epochs: 50` and re-introduce the split in the opposite direction. Figures from before 2026-09-02 are **not comparable**: pre-fix was 50-initial + 10000-later; this is 4000 uniform.

**3. Cell duration is load-bearing for scrapeability.** The host-experiments Prometheus job discovers targets by `file_sd` every 15 s and scrapes every 15 s. The target file is written at bring-up and deleted at teardown. A ~20 s smoke-length cell is **never scraped**. Calibrated 2026-09-01: `(6, 6)` → 40.17 s drive, 255 series including `juniper_cascor_training_step_duration_seconds`. `(10, 10)` targets ~60 s (owner ceiling ~120 s).

`metrics_scraped` used to mean `prometheus_target.json` existed. Five bridged PF-1 runs on 2026-09-01 all reported `present: true` while Prometheus held **zero** series. The driver now reports two facts (`run_experiment._metrics_scraped`):

| Field | Meaning |
|-------|---------|
| `target_file_written` | Local act — the JSON file exists |
| `scrape_confirmed` | Prometheus returned at least one `juniper_*` series with this `run_id`. `false` when the bridge is off or the series count is zero. `null` when Prometheus is unreachable — "could not check" is not "nothing was scraped" |

Default Prometheus URL: `JUNIPER_EXP_PROMETHEUS_URL` = `http://127.0.0.1:9090`.

### PF-3 stall and wall

`spiral-smoke` caps `max_epochs` but **not** `candidate_epochs`, so the CANDIDATE phase is full-length. The Q-2 detector watches `current_epoch`, which does not advance during candidate training. Pool-16 cells (and the `num_processes: 1` serialisation of that pool) would be recorded `stalled` at the 120 s driver default while healthy.

`execution.stall_seconds: 1200` alone was inert until `execution.max_wall_seconds: 2000` existed: `spiral-smoke` pins `outputs.max_wall_seconds: 600`, and without the suite forwarding `--max-wall-seconds` every cell ended at 600 s — a healthy long candidate phase labeled `timed_out` instead of `stalled`.

2000 sits above the stall window and below `per_run_timeout_seconds: 2400`, so the **driver** stops the run and writes a manifest. A subprocess kill at or below the wall budget records `timed_out` with `exit_code: null` and no manifest (R-6: `per_run_timeout_seconds` must be `>` the wall budget, not `>=`).

### Operator pitfalls

| Symptom | Check |
|---------|-------|
| `--dry-run` shows fewer than 5 PF-1 cells, or cells with differing hidden/iteration/epoch overrides | Repeats leaked into `include`, or the matched epoch pair was split. Stop. |
| PF-1 `scrape_confirmed: false` with `target_file_written: true` | Cell died before `file_sd` + scrape (15 s + 15 s). Confirm `(10, 10)` + 4000/4000 and `JUNIPER_SUITE_GRAFANA_BRIDGE=1`. |
| `scrape_confirmed: null` | Prometheus unreachable at `JUNIPER_EXP_PROMETHEUS_URL`. Not a negative scrape. |
| PF-1 `drive` ~15 s / 32 steps | Only `output_epochs` (or neither) was overridden — the smoke pair is 50/50. Set both to 4000. |
| Comparing PF-1 figures across 2026-09-02 | Pre-fix workload is 50-initial + 10000-later. Not the same experiment. |
| PF-3 cells `stalled` at ~120 s while the candidate pool is still training | Missing `execution.stall_seconds` above the driver default, or `max_wall_seconds` still inherited 600. |
| PF-3 `timed_out` with `exit_code: null` and no manifest | `per_run_timeout_seconds` ≤ wall budget. The suite subprocess killed the driver. |
| Treating a green PF-5 / PF-6 / PF-7 suite as a work-gate | Thresholds are unratified. These files measure fit time vs `d` / `n_steps` / readout. They are instruments. |
| Editing a suite key (or adding `execution.grafana_bridge`) to turn scraping on | That changes `config_sha256`. Use `JUNIPER_SUITE_GRAFANA_BRIDGE=1`. |

Coverage: `tests/test_experiment_suite_yamls.py` (R-6 load + oversize stall + wide-cap wall + timeout-above-budget). Driver scrape split: `tests/test_run_experiment.py`. Suite expansion / Grafana env: `tests/test_run_suite.py`.
After a cascor suite finishes, compare it to a named Q-8 baseline with [`util/experiments/compare_baseline.py`](#perf-lane-split-comparator) — identity first, work exact, speed reported.

---

## Perf-Lane Split Comparator

> **This section is the `compare_baseline.py` CLI reference. The CURRENT contract -- the
> termination-branch precondition, the settled determinism question, and the comparator's
> remaining open defects -- is [Perf-Lane Work Gate](#perf-lane-work-gate).** Where the two
> disagree, the Work Gate is newer.

`util/experiments/compare_baseline.py` is the perf-lane **split comparator** (P2 item 1.2). It implements the rule decided in item 1.5 and written up in [`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) §2.2: **identity is checked first**, then work is compared exactly, and speed is reported and never gated.

The CLI ships in [juniper-ml#1622](https://github.com/pcalnon/juniper-ml/pull/1622). It reads a baseline cut by `util/experiments/make_baseline.py` that records `workload_fingerprint` per scenario ([juniper-ml#1613](https://github.com/pcalnon/juniper-ml/pull/1613), on `main`). Prefer merging this docs PR **after** #1622 so the path exists. Concurrent docs [#1619](https://github.com/pcalnon/juniper-ml/pull/1619) described the comparator as unshipped — **this section supersedes that sentence**.

Whether the run tier ever becomes a required CI check remains open (P1 design §6). `ci.yml` runs `tests/test_compare_baseline.py` (the comparator's own hermetic gate); it does **not** invoke the CLI against live suites.

### Two halves

| Half | Field | Contract |
|------|-------|----------|
| **WORK** | `step_count` (last sampled histogram count) | Compared **exactly**. Deterministic for a seed-fixed config and contention-immune (identical across 21 cells spanning a 3× step-duration range), so a change is a statement about the **code**. A one-step difference is enough; there is no tolerance to tune. |
| **SPEED** | mean step duration (`step_sum` / `step_count`) | **Reported, never gated.** The host's own drift floor is 13–20.5%, larger than six competing CPU-bound processes. A speed threshold here would fire on an idle machine. A 10× slowdown with matching work still **PASS**es (`speed.gated` is always `false`). |

Do not gate on `aggregate.csv`'s `wall_seconds` or `manifest.json`'s `timings.drive`. Both are de-ratified (plot/stack overhead, and 5 s poll quantization). The resolving instrument is the cascor step-duration histogram in `$RUN_DIR/artifacts/results/metrics_series.csv`. Recurrence has no equivalent timing surface yet (P2 item 3.1).

### Identity first

A `step_count` difference only means "the code moved" when both sides ran the **same workload**. Collapsing a config edit into a work FAIL is how a gate earns a reputation for lying and gets switched off while still green.

| Condition | Verdict | Exit | What it is |
|-----------|---------|------|------------|
| Fingerprint missing from the baseline, candidate mixed/unknown, candidate `work_invariant` broken, or host identity differs | **REFUSED** | `2` | Invalid comparison, not a regression |
| Same workload, `step_count` differs, no waiver | **FAIL** | `1` | Work regression — the gate firing correctly |
| Same workload, `step_count` matches | **PASS** | `0` | Speed is printed; it cannot fail the gate |
| Same workload, `step_count` differs, `--accept-work-change REASON` | **WAIVED** | `0` | Blesses a **work** change. Never PASS. Never overrides a refusal. |

`registry.jsonl`'s `config_sha256` **cannot** serve as identity: it hashes `experiment.description`, so PF-1's five repeats are five hashes. `workload_fingerprint` strips `experiment.description` / `name` and keeps `seed` and `training.params.*`.

Measured on the real artifacts (the case the design exists for):

- Recalibrated PF-1 vs its own baseline → **PASS** (`1770 == 1770`, exit `0`).
- Pre-cascor#618 PF-1 vs that baseline → **REFUSED** (workload `d09edcc1…` not in baseline `52184ba2…`, exit `2`). Without the precondition the gate would have reported a **127% WORK REGRESSION** (4012 vs 1770) for a different config.

### CLI

Path-invoked. `--suite` is repeatable. Default `--run-root` is `~/.local/state/juniper-experiments` (same as `make_baseline.DEFAULT_RUN_ROOT`). Baseline files are `<run-root>/baselines/<tag>/baseline.json` and `HOST.json`.

```bash
python util/experiments/compare_baseline.py --baseline pf1-2026-09-03 --suite SUITE_DIR
python util/experiments/compare_baseline.py --baseline t --suite S --json
python util/experiments/compare_baseline.py --baseline t --suite S \
  --accept-work-change "cascor#618 raised the epoch budget"
```

`--json` emits the typed verdict (parseable; `verdict` is `PASS` / `FAIL` / `WAIVED` / `REFUSED`). Missing tag, unreadable `baseline.json`, or a whitespace-only waiver reason → exit `2` on stderr, no comparison.

`--suite` is repeatable. On #1622, **any** leftover refusal reason wins the whole verdict — a sibling identity miss collapses a real work FAIL to exit `2`, which callers treat as "not a code problem". [juniper-ml#1626](https://github.com/pcalnon/juniper-ml/pull/1626) changes that: FAIL wins over a sibling refusal unless the host is blocked (host mismatch still REFUSES even when work also moved). Until #1626 lands, compare one suite at a time if you need FAIL to stay visible.

An empty candidate (no `registry.jsonl` / no cells) is REFUSED, not a vacuous PASS. A config edit that keeps `step_count` identical is still REFUSED (identity), not PASS — the silent-green complement of the 4012-vs-1770 case.

Cut the baseline first with `python util/experiments/make_baseline.py --tag <tag> --suite SUITE_DIR` (operator-invoked; no `--force`; tags supersede **by name**). Full reader/baseline contract: docs [#1619](https://github.com/pcalnon/juniper-ml/pull/1619) and [`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md) §4.

### Host split

`compare_host` splits `HOST.json` differences:

| Class | Fields | Effect |
|-------|--------|--------|
| **Blocking** (P1 §2: "same hardware, same thread budget") | `cpu_model`, `cpu_count`, `thread_budget` | Any mismatch → **REFUSED** |
| **Advisory** | `versions.torch`, `versions.numpy`, `versions.python_runs` | Reported; **PASS** still allowed. Refusing here would make a routine dependency bump un-comparable. |
| **Not compared** | `total_ram_kb`, `gpu_present`, `platform`, `versions.python_tool` | Ignored by the comparator |

Candidate host is rebuilt by `make_baseline.collect_host` from the candidate manifests **plus this interpreter** (torch/numpy come from the tool, not the run). Same fidelity caveat as cutting the baseline: a HOST.json whose torch was read under a different Python than the runs is worse than one that says it could not tell.

### Waiver

`--accept-work-change` requires a non-empty reason (whitespace-only is refused, exit `2`). It yields **WAIVED**, never PASS, and records the reason. Prefer cutting a **new baseline** — they supersede by name and are cheap.

A waiver blesses a WORK change, never an invalid comparison. Passing it on a REFUSED run does **not** override the refusal (exit stays `2`). The renderer must not claim otherwise: under REFUSED it prints `had NO effect`, not `WAIVED by operator`. Found by running it — the first draft had the exit code right and the words wrong, and the words are what an operator acts on.

### Pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Exit `2` treated as a work regression | REFUSED is identity/host/incoherent-candidate, not FAIL. Distinct on purpose — do not `set -e` them together. |
| `--accept-work-change` on a config-edit suite | No effect. Cut a new baseline; the waiver cannot "compare anything to anything". |
| Renderer says `WAIVED by operator` but exit is `2` | Bug class pinned by `test_render_does_not_claim_a_waiver_that_had_no_effect`. Current source prints `had NO effect`. |
| Using `config_sha256` as "same workload" | Hashes `experiment.description`. Use `workload_fingerprint`. |
| Mixed known + missing cell YAML looks like one workload | **Fixed.** `summarise` used to drop `None` before uniqueness, so one identified cell plus one unknown could **PASS**; [ml#1776](https://github.com/pcalnon/juniper-ml/pull/1776) removed the filter, and `completion_reasons` now keeps the unknown member so a mixed set is not one branch. |
| Repeatable `--suite`: FAIL became exit `2` | **Fixed.** A leftover reason from a sibling suite used to win the whole verdict, hiding a real work FAIL behind exit `2`; [ml#1741](https://github.com/pcalnon/juniper-ml/pull/1741) / [#1743](https://github.com/pcalnon/juniper-ml/pull/1743) landed the precedence, and `VerdictPrecedenceTest` pins both directions. |
| Adding a speed threshold | There is no threshold field **by design**. Item 1.5 closed that question. |
| Gating CI on the CLI today | Tests of the module are wired; the run-tier gate itself is not (P1 §6). |

Coverage: `tests/test_compare_baseline.py` (54 tests on `main`; `util/` is outside pre-commit Python hooks, so this unittest **is** the gate). Wired in `.github/workflows/ci.yml` by #1622. Complementary pins: [#1625](https://github.com/pcalnon/juniper-ml/pull/1625) (same-`step_count` identity miss, empty candidate, `--suite` batch). Fail-closed mixed identity/unmeasured + FAIL-over-sibling-refusal: [#1626](https://github.com/pcalnon/juniper-ml/pull/1626).

---

## Suite Report Gate Inputs

`util/experiments/run_suite.py` writes `SUITE_DIR/aggregate.csv` + `REPORT.md` after every suite. Until juniper-ml#1643 (perf-lane P2 item 1.4) the aggregate carried **`wall_seconds` and nothing else** — and `wall_seconds` is **de-ratified**: it absorbs plot rendering and stack bring-up, and enabling the Grafana bridge alone moves it ~5%. A reader who opened the CSV was analysing the wrong quantity with nothing flagging it.

Design of record: [`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) item 1.4. The two ratified inputs come from `util/experiments/read_run_metrics.py` (`step_count` = WORK, `mean_step_seconds` = SPEED). The split comparator lives in `util/experiments/compare_baseline.py`.

### What the report now carries

| Surface | What you get |
|---------|--------------|
| `aggregate.csv` | `step_count` and `mean_step_seconds` sit **next to** `wall_seconds`. The de-ratified column stays for continuity; it is no longer the only number. |
| `REPORT.md` cell table | `step_count`, mean step **in milliseconds** (`mean_step_seconds * 1000`), then wall (s). CSV stays in seconds. |
| `REPORT.md` **Gate inputs** | States `wall_seconds` is DE-RATIFIED, then two suite-level verdicts (computed independently, not via `summarise()`). |
| `REPORT.md` **Baseline comparison** | Only when `--compare-baseline TAG` is passed. The text is `compare_baseline.render(...)`. |

Suite-level verdicts:

- **work invariant HOLDS** when every *measured* `step_count` is the same; **BROKEN** when they differ (the report then says these cells are **not repeats** and a baseline must not be cut from them). Unmeasured cells are omitted from the set — an empty set prints `step_count not measured`.
- **single workload yes** when every computed `workload_fingerprint` is the same; **NO** otherwise. Fingerprints are the first 12 hex chars plus `...`. The fingerprint hashes the materialised cell YAML with cosmetic `experiment.description` / `experiment.name` stripped (`config_sha256` cannot serve: PF-1's five repeats differ only by "repeat N" and would all look different).

Verified live after #1643 against the recalibrated PF-1 suite: every row `step_count` 1770, `work invariant: HOLDS`, `single workload: yes`, PASS against `pf1-2026-09-04`.

### `--compare-baseline` is reporting only

```bash
python util/experiments/run_suite.py --suite util/experiments/suites/perf/<file>.yaml --compare-baseline pf1-2026-09-04
```

The flag compares the just-written suite against `JUNIPER_EXP_RUN_ROOT/baselines/<TAG>/` (default root `~/.local/state/juniper-experiments`) and pastes the verdict under `## Baseline comparison`.

**The suite's own exit code does not change with the verdict.** Wiring a FAIL to `run_suite`'s status would silently make the run tier a CI gate — and §6 of the P1 design ([`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md)) records that as a **separate owner decision, still open**.

`test_a_failing_verdict_does_NOT_change_the_suite_exit_code` pins it: a FAIL verdict still exits 0, the verdict is still visible, and the report says so in the text. If that test ever fails, someone has made the gating decision by accident.

`run_suite` exit codes stay the cell-outcome contract:

| Exit | Meaning |
|------|---------|
| `0` | Every executed cell succeeded (a FAIL/REFUSED/missing-baseline comparison does **not** override this) |
| `1` | Suite completed with failed / other-than-succeeded cells |
| `2` | Misuse / suite-validation error |

A missing tag is **not** fatal: `_run_comparison` catches `CompareError` and writes `comparison could not run: …`. Without the flag there is no `## Baseline comparison` section. To get the comparator's own exit codes (0 PASS/WAIVED, 1 FAIL, 2 REFUSED), run `compare_baseline.py` directly.

### Import failure is loud on purpose

`_gate_metrics` / `_run_comparison` import the sibling modules **without** `try/except ImportError`. The first draft swallowed the error; under the test harness the imports *did* fail, and the feature degraded to blank `step_count` columns plus `work invariant: BROKEN -- step_count not measured` — indistinguishable from a genuinely broken suite.

Two pins keep that from returning:

1. `util/` is inserted on `sys.path` at module import so the siblings resolve whether `run_suite.py` is executed as a script (`sys.path[0] = util/experiments`) or imported as a module.
2. A missing sibling is a packaging bug and must raise, not blank the columns.

Cells with no `run_dir` in `registry.jsonl` are skipped (empty gate columns), which is a missing-run fact, not an import failure.

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| CSV / report only show `wall_seconds` as the useful number | Pre-#1643 artifact. Re-run the suite on a tree that has item 1.4, or read `read_run_metrics.py` against each `run_dir`. |
| `work invariant: BROKEN -- step_count not measured` | Either the cells truly have no step totals, **or** (pre-fix) a swallowed `ImportError`. On current main a missing sibling **raises** — if you still see this wording, the runs were not measured. |
| `--compare-baseline` FAIL / REFUSED but suite exits 0 | Expected. Read `REPORT.md`; run `compare_baseline.py` if you need its exit code. |
| `comparison could not run: no baseline 'TAG'` | Tag is missing under `JUNIPER_EXP_RUN_ROOT/baselines/`. Cut one with `make_baseline.py` first. |
| Mean-step column looks 1000× too large vs the CSV | Report table is **milliseconds**; `aggregate.csv` is **seconds**. |
| `single workload: NO` on a suite of "repeats" | Fingerprint strips only `experiment.description` / `name`. A seed change, or leftover `output_epochs` / budget drift, is a different workload. Do not cut a baseline from it. |
| Trusting `config_sha256` as "same workload" | It hashes the whole cell YAML including the cosmetic description. PF-1's five repeats all differ. Use the fingerprint printed in **Gate inputs**. |

Coverage: `tests/test_run_suite.py` (`GateInputsInAggregateTest`, `ComparisonReportingTest`).

---

## Suite Driver

`util/experiments/run_suite.py` is the **multi-cell** CLI experimentation driver (plan Wave 7.1 sequential + Wave 7.5 bounded-parallel). It expands a suite YAML into an ordered cell list, materialises each cell as a standalone experiment YAML, then runs **per-cell** `experiment_stack.bash --up` → `run_experiment.py` → `--down`. Design-of-record: [`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) Wave 7. Shipped suites live under `util/experiments/suites/**` and are gated by `tests/test_experiment_suite_yamls.py` (R-6).

This is **not** a replacement for the per-run launcher, **not** `list_runs.py` (directory-truth over `RUN_DIR`s), and **not** the standalone Q-8 baseline writer / comparator.

```bash
# Preview expansion + the exact --up / drive / --down lines (writes nothing)
python util/experiments/run_suite.py --suite util/experiments/suites/p4/e-a-cascor-budget-sweep.yaml --dry-run

# Live suite (honours JUNIPER_EXP_RUN_ROOT; default ~/.local/state/juniper-experiments)
python util/experiments/run_suite.py --suite path/to/suite.yaml

# Resume: skip cells whose registry outcome is already succeeded
python util/experiments/run_suite.py --suite path/to/suite.yaml --resume SUITE_ID

# Execute a named subset (unknown ids exit 2)
python util/experiments/run_suite.py --suite path/to/suite.yaml --only c000-abcd1234
```

`--dry-run` prints the **full** expansion (it does not honour `--only`) and creates neither `SUITE_DIR` nor `$JUNIPER_EXP_RUN_ROOT/index.jsonl`.

### Suite YAML

`schema_version` must be `1`. Unknown top-level / `suite:` / `execution:` keys are exit `2` (the `stall_second` / `max_wall_second` typo class).

| Block | Required keys | Notes |
|-------|---------------|-------|
| `suite` | `name`, `app` (`cascor` \| `recurrence`), non-empty `base_config` list | `seed_policy`: `fixed` (default) or `per_cell` |
| `execution` | none | `mode` `sequential` (default) \| `parallel`; `max_parallel` ≥ 1; `continue_on_failure` default **true**; `per_run_timeout_seconds` default `3600` |
| `matrix` | dotted path → non-empty list | Cartesian product across `base_config` entries |
| `exclude` | non-empty mappings | Drop a combo when **every** key matches |
| `include` | mappings with `overrides` | Appended after the product; optional `name` / `config` |
| `outputs.suite_dir` | optional | Absolute path wins over `$JUNIPER_EXP_RUN_ROOT/suites/<SUITE_ID>` |

`cell_id` is `c{index:03d}-{sha8}` of the **relative** `base_config` string plus `json.dumps(overrides, sort_keys=True)` — stable between the canonical checkout and a `JUNIPER_EXP_PROJECT_DIR` rebase. Zero cells after exclude is exit `2`.

`seed_policy: per_cell` sets `experiment.seed` and, when present, `dataset.params.seed` to `base_seed + cell.index`. `fixed` leaves the base YAML seeds alone. Each cell also gets `experiment.name = "{suite.name}-{cell_id}"`.

`JUNIPER_EXP_PROJECT_DIR`, when set, rebases a sibling `base_config` from its first `juniper-*` component **even if the literal relative walk already resolves** (mixed-tree class: worktree CODE + primary CONFIG). A stale / missing override falls back to the literal.

### Budget flags vs the subprocess timeout

| Suite key | Forwarded to the driver? | Default when absent |
|-----------|--------------------------|---------------------|
| `execution.stall_seconds` | `--stall-seconds` | Flag omitted — driver keeps `120` |
| `execution.max_wall_seconds` | `--max-wall-seconds` | Flag omitted — driver keeps YAML / `3600` |
| `execution.per_run_timeout_seconds` | **No** — kills the driver from outside | `3600` |

Size `per_run_timeout_seconds` **above** the wall budget. The outer timeout records `timed_out` with no honest driver `manifest.json`. A dotted `outputs.max_wall_seconds` matrix override is also accepted by the R-6 gate (E-I uses that form). Oversize cascor suites (`candidate_pool_size >= 16` **or** `max_hidden_units >= 64`) must declare a stall window above the driver's default — otherwise a healthy candidate phase is marked `stalled` at ~130 s.

### Parallel cascor floor (Q-6 / H-7)

`execution.mode: parallel` with `max_parallel > 1` and `app: cascor` is gated on the tree that will actually **launch**, not `importlib.metadata.version("juniper-cascor")`. Resolution mirrors `experiment_stack.bash`: `JUNIPER_EXP_CASCOR_SRC_DIR` → `JUNIPER_EXP_PROJECT_DIR/juniper-cascor` → ancestor probe for a `juniper-cascor/pyproject.toml` sibling.

Floor is `CASCOR_PARALLEL_FLOOR = (0, 10, 0)` (first release with `JUNIPER_CASCOR_LOG_DIR`, cascor#523). Below that, or if the version **cannot be read**, `load_suite` refuses (exit `2`). Sequential cascor and parallel recurrence are never gated.

Parallel cells also get the H-11 budget (`thread_budget_env`): `split = max(1, nproc // (2 * max_parallel))`. Cascor pins BLAS at `2` and sets `CASCOR_NUM_PROCESSES=split`; recurrence sets the BLAS vars to `split`. Sequential rows record `thread_budget: null`. `continue_on_failure: false` stops **submitting** after the first failure; already-running parallel cells drain.

### Resume, `--only`, and exit codes

`--resume SUITE_ID` skips a cell only when `registry.jsonl` already has `outcome == "succeeded"`. Failed / stalled / timed_out cells **re-run**. The argparse help saying "terminal" is looser than the code.

When `outputs.suite_dir` is set, that path is the suite dir and `--resume` is only the id written onto new registry rows. Otherwise the dir is `$JUNIPER_EXP_RUN_ROOT/suites/<SUITE_ID>` (`SUITE_ID` is `--resume` or `{name}-{UTC}`).

| Exit | Meaning |
|------|---------|
| `0` | Every cell in the **full expansion** has `outcome == succeeded` in the registry |
| `1` | Suite finished with failed / not-run cells, or a cell failed |
| `2` | Suite YAML / `--only` / `--resume` dir / materialise validation |

`--only` still aggregates the full expansion. Unselected cells that are not already `succeeded` count as not-run, so a partial `--only` exits `1` even when every selected cell succeeded. Resume a previous suite (or `--only` the entire expansion) when you need exit `0`.

Each executed cell appends `SUITE_DIR/registry.jsonl` and `$JUNIPER_EXP_RUN_ROOT/index.jsonl`. `list_runs.py` does **not** read that index — it scans `RUN_DIR` names.

### Grafana bridge and snapshot provenance

`JUNIPER_SUITE_GRAFANA_BRIDGE` is an **env toggle**, not a suite key: `1` / `true` / `yes` / `on` add `--grafana-bridge` to every `--up`. `0` / empty / `false` / `no` do not. A suite key would change every cell's `config_sha256` between a bridged and an unbridged run of the same scenario (PF-1 comparability). Off by default — without it `--status` reports UNSCRAPED.

The suite is the only layer that knows both identities. Every `--up` gets `--experiment <cell_id>` plus `JUNIPER_CASCOR_CELL_ID` and, when present, `JUNIPER_CASCOR_EXPERIMENT=<suite.name>` so snapshots record the cell **and** the suite.

### What this section does not own

After the last cell, `aggregate` writes `aggregate.csv` + `REPORT.md`. Those files also carry perf-lane gate-input columns (`step_count` / `mean_step_seconds` beside de-ratified `wall_seconds`) and an optional `--compare-baseline TAG` block. That contract is a **separate** operator surface (in-flight docs #1649) and is reporting-only: a FAIL verdict does **not** change this driver's exit code.

Coverage: `tests/test_run_suite.py` (expansion, project-dir override, cascor parallel floor, grafana toggle, resume, `--only`, both Q-2 budget flags, H-11 budget, provenance env).

### Environment overrides

| Variable | Default | Description |
|----------|---------|-------------|
| `JUNIPER_EXP_RUN_ROOT` | `~/.local/state/juniper-experiments` | Run root **and** default `suites/` parent. Honoured here (unlike `list_runs.py`'s hardcoded default). |
| `JUNIPER_EXP_PROJECT_DIR` | unset | Rebase sibling `base_config` paths; also the cascor-tree probe for the parallel floor |
| `JUNIPER_EXP_CASCOR_SRC_DIR` | unset | Cascor `src/` of the tree that will launch (version floor). Not `importlib.metadata`. |
| `JUNIPER_SUITE_GRAFANA_BRIDGE` | unset / off | Opt-in `--grafana-bridge` on every `--up` |
| `JUNIPER_SUITE_LAUNCHER` / `JUNIPER_SUITE_DRIVER` / `JUNIPER_SUITE_PYTHON` | in-tree paths / this interpreter | Test seams; operators should leave them unset |

### Troubleshooting

| Symptom | Check / Fix |
|---------|-------------|
| Exit `2` `unknown execution: keys` | Typo (`stall_second`, `max_wall_second`) — the allow-list is exact. |
| Exit `2` cascor parallel / "could not be read" | Point `JUNIPER_EXP_CASCOR_SRC_DIR` at a tree ≥ `0.10.0`, or use `mode: sequential`. An unreadable version refuses rather than assuming. |
| Healthy pool ≥ 16 marked `stalled` at ~130 s | Candidate phase does not advance `current_epoch`. Set `execution.stall_seconds` (P4 E-A). |
| Cap-128 cell `timed_out` at 3600 s | Inherited `spiral-baseline` wall. Set `execution.max_wall_seconds` or a dotted `outputs.max_wall_seconds` override (E-I measured 4243.6 s). |
| `--resume` re-ran a failed cell | Expected — only `succeeded` is skipped. |
| `--only` one cell, exit `1`, cell succeeded | Aggregate scores the full expansion; unselected cells are not-run. |
| `--dry-run` still listed cells you `--only`'d out | Dry-run prints the full product. |
| Bridged vs unbridged PF-1 hashes differ | Do not put the bridge in the suite YAML. Use `JUNIPER_SUITE_GRAFANA_BRIDGE=1`. |
| Worktree ran worktree cascor against primary YAML | Set `JUNIPER_EXP_PROJECT_DIR` — the override wins over a resolving literal. |
| Snapshots have a cell id but no suite name | Pre-provenance run. Current `--up` exports `JUNIPER_CASCOR_EXPERIMENT`. |
| `list_runs.py` does not show the suite | It ignores `index.jsonl` and `suites/`. Look under `$JUNIPER_EXP_RUN_ROOT/suites/<SUITE_ID>/`. |
| `--compare-baseline` FAIL but suite exit `0` | Reporting-only — see docs #1649. |

---

## Recurrence Work Is Not Countable

Lands with [juniper-ml#1683](https://github.com/pcalnon/juniper-ml/pull/1683) (P2 item 3.1). Operator surface for `util/experiments/read_run_metrics.py`, `make_baseline.py`, and `compare_baseline.py` on **recurrence** runs.

The cascor identity / split-gate contract (fingerprint, exact `step_count`, ungated speed, host blocking fields) is a different surface — in-flight docs [#1619](https://github.com/pcalnon/juniper-ml/pull/1619) / [#1628](https://github.com/pcalnon/juniper-ml/pull/1628). Suite-report `--compare-baseline` wiring is [#1649](https://github.com/pcalnon/juniper-ml/pull/1649). This section is only the recurrence finding and the refuse-rather-than-mis-gate contract.

Design: [`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) (item 3.1). The plan's own §1.2 overstated the gap as "recurrence has no timing surface"; #1683 corrects that in the plan. The timings already existed.

### Intent

The split gate has two halves: **WORK** (`step_count`, gated exactly) and **SPEED** (reported, never gated; this host's drift floor is 13–20.5%). Recurrence has **no work-done counter**, so PF-5 / PF-6 / PF-7 can be **reported but never gated** without new instrumentation inside juniper-recurrence. The tools say so and refuse, rather than blessing a speed-only baseline that would invite exactly the comparison the floor rules out.

### Kind detection

`read_run` defaults to `kind: "cascor"` / `work_countable: True`, then overlays recurrence when the manifest has **no** `timings.drive` and **does** have `timings.train`:

| Manifest `timings` | Kind | Work countable | Duration field |
|--------------------|------|----------------|----------------|
| `drive` present | `cascor` | `True` | `drive_seconds` (poll-quantized; de-ratified) |
| no `drive`, `train` present | `recurrence` | `False` | `train_seconds` / `crossval_seconds` (driver-measured, **unquantized**) |

Recurrence `POST /v1/train` is **synchronous**: the response *is* completion, so there is no poll loop and none of cascor `drive`'s 5 s quantization. A run that carries **both** keys stays cascor (the `drive` key wins). A run that carries **neither** also stays the cascor default — do not treat a missing `train` key as "recurrence with zero work".

Recurrence extras (from `artifacts/results/train_response.json`): `n_epochs`, `stopped_reason`, `n_windows`, plus `work_uncountable_reason`.

### Why the work-count candidates fail

Surveyed across **36** real recurrence runs on 2026-09-04 (not assumed from repeats):

| Candidate | Measures | Verdict |
|-----------|----------|---------|
| `n_epochs` | iterations to convergence | **Degenerate.** Exactly two values: **1** (28 runs, `stopped_reason=converged`) and **200** (2 runs, `max_epochs`). Tracks the **readout type** (closed-form readouts converge in one epoch). Invariant to `d` and `n_steps` — the two dimensions PF-5 and PF-6 exist to vary — so a gate on it would be vacuous exactly where it is needed. |
| `dataset.n_windows` | input size | Varies (349 / 1346 / 1574 / 3149) but is **fixed by the config**. A code change that does redundant work does not move it. cascor `step_count` measures work **done**; this measures work **asked for**. |
| `timings.train` | duration | This is the **speed** half, not work. |

Measured example from #1683 (run `20260809T080104Z-5ebf`): `kind=recurrence`, `work_countable=false`, `train` 0.518 s, `crossval` 1.928 s, `n_epochs` 1, `n_windows` 1574.

### Third state: `work_countable` vs `work_invariant`

`summarise()` keeps three distinguishable outcomes so a caller never reads "not countable" as "counted, and they matched":

| State | `work_countable` | `work_invariant` | Meaning |
|-------|------------------|------------------|---------|
| Counted and matched | `True` | `True` | Every cell reports the same `step_count` |
| Counted and differed | `True` | `False` | `step_count` spread — not a set of repeats |
| Not countable | `False` | `False` | The work question does not apply (recurrence). `kinds` lists `recurrence`. |

`work_invariant` is `countable AND unique(step_counts) AND nonempty`. An empty suite is also `work_countable: False`. Callers that still treat a missing key as countable stay compatible (`row.get("work_countable", True)`).

The human table from `read_run_metrics.py` is **cascor-shaped** (`polls` / `drive` / `step_sum` / `steps`). It does not print `train_seconds` or `work_uncountable_reason`. Use `--json` (or `--run RUN_DIR`, which always emits JSON) for a recurrence run.

`--sweep` appears only in the module docstring. It is **not** an argparse flag.

### `make_baseline` refuses

A baseline exists to support the WORK gate. `build_baseline` appends a refusal when `summarise().work_countable` is false and raises `BaselineError` (CLI exit **2**). The message names `n_epochs` / input-size and says **Report these runs instead of baselining them.**

A recurrence suite can also trip the later `work_invariant` refusal (`step_counts` is empty). The first message is the one that explains why.

There is still no `--force`. Operator-invoked only — never called from `run_suite.py` / `run_experiment.py`.

```bash
# Inspect a recurrence RUN_DIR (JSON is the operator path)
python util/experiments/read_run_metrics.py --run ~/.local/state/juniper-experiments/<RUN_ID> --json

# This exits 2 on a recurrence suite — do not pass --accept-warnings to "make it work"
python util/experiments/make_baseline.py --tag pf5-try --suite SUITE_DIR --dry-run
```

### `compare_baseline` refuses

After the single-workload check, `compare()` refuses a candidate whose summary is not `work_countable`. Verdict **REFUSED**, exit **2**. Reason text: the WORK half does not apply; speed alone cannot be compared here (13–20.5% drift floor); report the run rather than gating it.

`--accept-work-change REASON` blesses a **work** change (WAIVED, never PASS). It **cannot** override a refusal — the renderer prints `had NO effect`.

```bash
python util/experiments/compare_baseline.py --baseline SOME-TAG --suite SUITE_DIR
# recurrence candidate -> verdict REFUSED, exit 2
```

### Operator pitfalls

| Pitfall | What actually happens |
|---------|------------------------|
| Gate PF-5/6/7 on `n_epochs` | Vacuous — 1 vs 200 by readout type, invariant to `d` / `n_steps`. |
| Treat `n_windows` as cascor `step_count` | Input size, not work done. Redundant work does not move it. |
| Cut a "speed-only" baseline so compare can run | `make_baseline` refuses. A speed reference would exist solely to back the comparison the drift floor rules out. |
| Read `work_invariant: false` as "counts differed" | Check `work_countable` first. False+false is the third state. |
| Trust the human table for recurrence | Cascor columns only. Use `--json`. |
| `--accept-work-change` to force a recurrence compare | Still REFUSED. A waiver cannot override a refusal. |
| Point `--compare-baseline` at a recurrence suite from `run_suite.py` | Same `summarise()` refuse (once #1683 has landed). A failing verdict still does not change the suite exit code — that wiring is [#1649](https://github.com/pcalnon/juniper-ml/pull/1649). |

Coverage: `tests/test_read_run_metrics.py` (`RecurrenceKindTest`) and `tests/test_make_baseline.py` (`RecurrenceRefusalTest`) land with #1683.

In-flight [#1689](https://github.com/pcalnon/juniper-ml/pull/1689) adds `tests/test_work_countable_contract.py` for the leftover those cannot see: `compare()` REFUSED (exit 2) with the honest reason (not FAIL / not "not a set of repeats"), waiver cannot override, planted cascor histogram counts do not make an uncountable suite `work_invariant`, and `drive` wins when both timing keys are present.

---

## Experiment Stats Summary (SS8.3)

`util/experiments/stats_summary.py` is **not a CLI**. The driver loads it as a sibling module and writes `artifacts/results/stats.json` + `artifacts/results/summary.md` on every outcome (succeeded, stalled, timed_out, failed). A render exception is recorded on the manifest as `stats_error` and **never** costs the manifest write (`run_experiment.py` `_emit_stats`). Schema: `juniper-experiment-stats/1`. Stdlib only — stats render on any host the driver runs on.

This page is how to **read** those files. The WORK/SPEED gate reader is `read_run_metrics.py` (cascor histogram; recurrence work is not countable — in-flight [#1691](https://github.com/pcalnon/juniper-ml/pull/1691) / feature [#1683](https://github.com/pcalnon/juniper-ml/pull/1683)). Do not treat `stats.json` as that gate.

```bash
# After a run
jq '{schema, outcome, provenance}' "$RUN_DIR/artifacts/results/stats.json"
jq '.cascor.training_step_duration // .recurrence' "$RUN_DIR/artifacts/results/stats.json"
less "$RUN_DIR/artifacts/results/summary.md"
# Render failed? The manifest still exists.
jq '.stats_error' "$RUN_DIR/manifest.json"
```

### What each block is

| Block | Source | Operator meaning |
|-------|--------|------------------|
| `identity` | manifest | `run_id`, experiment name/description, `config_sha256`, seeds, git SHAs + dirty flags, package versions |
| `dataset.shapes` | dataset `meta` | `kind: tabular` **or** `kind: sequence`. Sequence `n_windows` is `meta.n_samples` (input size, not work done) |
| `outcome.wall_seconds` | `timings.total` | **De-ratified.** Absorbs plot render + stack bring-up. Not the SPEED half |
| `outcome.timings` | driver `_phase` | The honest duration map. Cascor keys include `health_wait` / `dataset_create` / `stage` / `start` / `drive`. Recurrence keys include `train` / `crossval` (driver-measured; `/v1/train` is synchronous) |
| `cascor.training_step_duration` | last-row histogram + per-poll deltas from `metrics_series.csv` | Gateable **work** is `total_steps`. `p50_seconds` / `p95_seconds` are **per-poll means** (`delta-sum / delta-count`); true per-step quantiles are not recoverable from a sum/count exposition — `basis` says so |
| `cascor.candidate_correlation` | same CSV | Best sampled correlation **per growth round** (round = a `current_hidden_units` increment). Sole source — `/v1/metrics/history` does not carry it |
| `recurrence.*` | train / crossval payloads + YAML `train` | `n_epochs`, `stopped_reason`, `theta` (explicit vs data-driven), readout rung, CV folds. **No duration field in this block** — train/crossval seconds live under `outcome.timings` |
| `provenance.metrics_scraped` | driver `_metrics_scraped` | Two facts, never collapsed — see below |
| `provenance.degraded_notes` | manifest | G-3 sampling errors, collect failures, plot skips, eval-disabled, G-6 mismatch |

### Step-duration honesty (cascor)

`step_duration_stats` walks the driver's sampled `_sum` / `_count` pair. A per-poll mean exists only when the count **advanced**. A constant series (same sum/count on every row) yields `p50_seconds: null` and still reports `total_steps` / `overall_mean_seconds`.

Pinned by `StatsSummaryUnitTest.test_step_duration_stats_from_deltas`: rows `(sum=1,count=2) → (2,4) → (5,5)` → `total_steps=5`, two poll samples (0.5 s and 3.0 s), `p50_seconds=1.75`, `overall_mean_seconds=1.0`. Non-numeric scraped cells soft-None (Prometheus label noise) rather than aborting the render.

### Recurrence: timings are not in the recurrence block

P2 item 3.1 surveyed this. `stats["recurrence"]` (lines 246–253 of `stats_summary.py`) emits `final_metrics` / `n_epochs` / `stopped_reason` / `dataset_descriptor` / `theta` / `readout` / `crossval` — **no duration**. The driver already recorded `timings.train` / `timings.crossval` on the manifest, and `build_stats` copies the whole `timings` dict to `outcome.timings`.

```bash
# Recurrence duration — not under .recurrence
jq '.outcome.timings' "$RUN_DIR/artifacts/results/stats.json"
# n_epochs is iterations-to-stop (1 vs 200 by readout type), not a work count
jq '.recurrence.n_epochs, .dataset.shapes.n_windows' "$RUN_DIR/artifacts/results/stats.json"
```

`theta.note` is `"data-driven (resolved from per-window elapsed time)"` when the YAML left `theta` unset, else `"explicit"`. Sequence `n_windows` is input size (pinned: `test_build_stats_sequence_shapes_and_summary`).

### `scrape_confirmed` is tri-state

`present: prometheus_target.json.is_file()` used to stand in for "metrics were scraped". Writing the target file is the same act that set the flag, so it could not fail. On **2026-09-01** five bridged PF-1 runs all reported `present: true` while Prometheus held **zero** series for any of them (file_sd refresh 15 s + scrape 15 s outran a ~20 s service).

The driver now reports two named facts (`JUNIPER_EXP_PROMETHEUS_URL`, default `http://127.0.0.1:9090`):

| Field | Meaning |
|-------|---------|
| `target_file_written` | Local act. Useful when the bridge did nothing |
| `scrape_confirmed` | Query `count({__name__=~"juniper_.+", run_id="<id>"})`. **True** / **False** / **None** |

| `scrape_confirmed` | When |
|--------------------|------|
| `true` | Prometheus returned at least one series for this `run_id` |
| `false` | Bridge was **off** (`reason` says so) **or** the query succeeded and found zero series |
| `null` | Prometheus was unreachable or returned a non-success — the question could not be asked. `reason` names why. **Not** the same as "nothing was scraped" |

`summary.md` prints both facts and falls back to the pre-2026-09-01 key `present` when `target_file_written` is absent. Never let the local file stand in for the remote scrape.

### Operator pitfalls

| Pitfall | What actually happens |
|---------|------------------------|
| Gate or compare on `outcome.wall_seconds` | De-ratified `timings.total`. Use `read_run_metrics` (`step_count` / `mean_step_seconds`) |
| Treat cascor `p50` / `p95` as per-step quantiles | Per-poll means. Read `basis`. A no-advance series has `p50: null` |
| Look under `stats.recurrence` for train seconds | Not there. `outcome.timings.train` / `.crossval` |
| Treat `n_epochs` or `n_windows` as cascor `step_count` | Iterations-to-stop / input size. Recurrence work is not countable |
| `target_file_written: true` ⇒ scraped | Five PF-1 runs disproved this. Read `scrape_confirmed` |
| Collapse `scrape_confirmed: null` into false | Unreachable Prometheus ≠ zero series |
| Missing `stats.json` means the run did not finish | Check `manifest.stats_error`. The manifest is still the source of truth |
| Invoke `python util/experiments/stats_summary.py` | No `__main__`. The driver calls `build_stats` / `render_summary_md` |

Coverage: `tests/test_run_experiment.py` (`StatsSummaryUnitTest` + e2e stats assertions for both kinds). `util/` is not pre-commit-lint-gated; that unittest is the gate.

After a cascor suite finishes, compare it to a named Q-8 baseline with [`util/experiments/compare_baseline.py`](#perf-lane-split-comparator) — identity first, work exact, speed reported.


## Perf-Lane Split Comparator

`util/experiments/compare_baseline.py` is the perf-lane **split comparator** (P2 item 1.2). It implements the rule decided in item 1.5 and written up in [`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md) §2.2: **identity is checked first**, then work is compared exactly, and speed is reported and never gated.

The CLI ships in [juniper-ml#1622](https://github.com/pcalnon/juniper-ml/pull/1622). It reads a baseline cut by `util/experiments/make_baseline.py` that records `workload_fingerprint` per scenario ([juniper-ml#1613](https://github.com/pcalnon/juniper-ml/pull/1613), on `main`). Prefer merging this docs PR **after** #1622 so the path exists. Concurrent docs [#1619](https://github.com/pcalnon/juniper-ml/pull/1619) described the comparator as unshipped — **this section supersedes that sentence**.

Whether the run tier ever becomes a required CI check remains open (P1 design §6). `ci.yml` runs `tests/test_compare_baseline.py` (the comparator's own hermetic gate); it does **not** invoke the CLI against live suites.

### Two halves

| Half | Field | Contract |
|------|-------|----------|
| **WORK** | `step_count` (last sampled histogram count) | Compared **exactly**. Deterministic for a seed-fixed config and contention-immune (identical across 21 cells spanning a 3× step-duration range), so a change is a statement about the **code**. A one-step difference is enough; there is no tolerance to tune. |
| **SPEED** | mean step duration (`step_sum` / `step_count`) | **Reported, never gated.** The host's own drift floor is 13–20.5%, larger than six competing CPU-bound processes. A speed threshold here would fire on an idle machine. A 10× slowdown with matching work still **PASS**es (`speed.gated` is always `false`). |

Do not gate on `aggregate.csv`'s `wall_seconds` or `manifest.json`'s `timings.drive`. Both are de-ratified (plot/stack overhead, and 5 s poll quantization). The resolving instrument is the cascor step-duration histogram in `$RUN_DIR/artifacts/results/metrics_series.csv`. Recurrence has no equivalent timing surface yet (P2 item 3.1).

### Identity first

A `step_count` difference only means "the code moved" when both sides ran the **same workload**. Collapsing a config edit into a work FAIL is how a gate earns a reputation for lying and gets switched off while still green.

| Condition | Verdict | Exit | What it is |
|-----------|---------|------|------------|
| Fingerprint missing from the baseline, candidate mixed/unknown, candidate `work_invariant` broken, or host identity differs | **REFUSED** | `2` | Invalid comparison, not a regression |
| Same workload, `step_count` differs, no waiver | **FAIL** | `1` | Work regression — the gate firing correctly |
| Same workload, `step_count` matches | **PASS** | `0` | Speed is printed; it cannot fail the gate |
| Same workload, `step_count` differs, `--accept-work-change REASON` | **WAIVED** | `0` | Blesses a **work** change. Never PASS. Never overrides a refusal. |

`registry.jsonl`'s `config_sha256` **cannot** serve as identity: it hashes `experiment.description`, so PF-1's five repeats are five hashes. `workload_fingerprint` strips `experiment.description` / `name` and keeps `seed` and `training.params.*`.

Measured on the real artifacts (the case the design exists for):

- Recalibrated PF-1 vs its own baseline → **PASS** (`1770 == 1770`, exit `0`).
- Pre-cascor#618 PF-1 vs that baseline → **REFUSED** (workload `d09edcc1…` not in baseline `52184ba2…`, exit `2`). Without the precondition the gate would have reported a **127% WORK REGRESSION** (4012 vs 1770) for a different config.

### CLI

Path-invoked. `--suite` is repeatable. Default `--run-root` is `~/.local/state/juniper-experiments` (same as `make_baseline.DEFAULT_RUN_ROOT`). Baseline files are `<run-root>/baselines/<tag>/baseline.json` and `HOST.json`.

```bash
python util/experiments/compare_baseline.py --baseline t --suite S --json
python util/experiments/compare_baseline.py --baseline t --suite S \
  --accept-work-change "cascor#618 raised the epoch budget"
```

`--json` emits the typed verdict (parseable; `verdict` is `PASS` / `FAIL` / `WAIVED` / `REFUSED`). Missing tag, unreadable `baseline.json`, or a whitespace-only waiver reason → exit `2` on stderr, no comparison.

`--suite` is repeatable. On #1622, **any** leftover refusal reason wins the whole verdict — a sibling identity miss collapses a real work FAIL to exit `2`, which callers treat as "not a code problem". [juniper-ml#1626](https://github.com/pcalnon/juniper-ml/pull/1626) changes that: FAIL wins over a sibling refusal unless the host is blocked (host mismatch still REFUSES even when work also moved). Until #1626 lands, compare one suite at a time if you need FAIL to stay visible.

An empty candidate (no `registry.jsonl` / no cells) is REFUSED, not a vacuous PASS. A config edit that keeps `step_count` identical is still REFUSED (identity), not PASS — the silent-green complement of the 4012-vs-1770 case.

Cut the baseline first with `python util/experiments/make_baseline.py --tag <tag> --suite SUITE_DIR` (operator-invoked; no `--force`; tags supersede **by name**). Full reader/baseline contract: docs [#1619](https://github.com/pcalnon/juniper-ml/pull/1619) and [`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md) §4.

### Host split

`compare_host` splits `HOST.json` differences:

| Class | Fields | Effect |
|-------|--------|--------|
| **Blocking** (P1 §2: "same hardware, same thread budget") | `cpu_model`, `cpu_count`, `thread_budget` | Any mismatch → **REFUSED** |
| **Advisory** | `versions.torch`, `versions.numpy`, `versions.python_runs` | Reported; **PASS** still allowed. Refusing here would make a routine dependency bump un-comparable. |
| **Not compared** | `total_ram_kb`, `gpu_present`, `platform`, `versions.python_tool` | Ignored by the comparator |

Candidate host is rebuilt by `make_baseline.collect_host` from the candidate manifests **plus this interpreter** (torch/numpy come from the tool, not the run). Same fidelity caveat as cutting the baseline: a HOST.json whose torch was read under a different Python than the runs is worse than one that says it could not tell.

### Waiver

`--accept-work-change` requires a non-empty reason (whitespace-only is refused, exit `2`). It yields **WAIVED**, never PASS, and records the reason. Prefer cutting a **new baseline** — they supersede by name and are cheap.

A waiver blesses a WORK change, never an invalid comparison. Passing it on a REFUSED run does **not** override the refusal (exit stays `2`). The renderer must not claim otherwise: under REFUSED it prints `had NO effect`, not `WAIVED by operator`. Found by running it — the first draft had the exit code right and the words wrong, and the words are what an operator acts on.

### Pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Exit `2` treated as a work regression | REFUSED is identity/host/incoherent-candidate, not FAIL. Distinct on purpose — do not `set -e` them together. |
| `--accept-work-change` on a config-edit suite | No effect. Cut a new baseline; the waiver cannot "compare anything to anything". |
| Renderer says `WAIVED by operator` but exit is `2` | Bug class pinned by `test_render_does_not_claim_a_waiver_that_had_no_effect`. Current source prints `had NO effect`. |
| Using `config_sha256` as "same workload" | Hashes `experiment.description`. Use `workload_fingerprint`. |
| Mixed known + missing cell YAML looks like one workload | On `main` (`#1613`) and #1622, `summarise` drops `None` before uniqueness, so one identified cell plus one unknown/unmeasured cell can **PASS**. [juniper-ml#1617](https://github.com/pcalnon/juniper-ml/pull/1617) / [#1626](https://github.com/pcalnon/juniper-ml/pull/1626) refuse on the rows. Until they land, do not compare a suite with a missing `cells/*/experiment.yaml`. |
| Repeatable `--suite`: FAIL became exit `2` | #1622: leftover reasons win, so a sibling REFUSE hides a work FAIL. Compare one suite, or wait for #1626 (FAIL wins unless host-blocked). |
| Adding a speed threshold | There is no threshold field **by design**. Item 1.5 closed that question. |
| Gating CI on the CLI today | Tests of the module are wired; the run-tier gate itself is not (P1 §6). |

Coverage: `tests/test_compare_baseline.py` (20 tests on #1622; `util/` is outside pre-commit Python hooks, so this unittest **is** the gate). Wired in `.github/workflows/ci.yml` by #1622. Complementary pins: [#1625](https://github.com/pcalnon/juniper-ml/pull/1625) (same-`step_count` identity miss, empty candidate, `--suite` batch). Fail-closed mixed identity/unmeasured + FAIL-over-sibling-refusal: [#1626](https://github.com/pcalnon/juniper-ml/pull/1626).

---

## Generator Availability Matrix (On-Host)

Which juniper-data generators are usable in which on-host environment, and what each availability gate needs (CLI experimentation plan §11 items W-4/W-10). juniper-data's registry (`juniper_data/api/routes/generators.py::GENERATOR_REGISTRY`, 16 generators) reports per-generator availability through `generator_available()`: a generator MAY declare an `is_available()` hook probing its optional dependencies; generators without the hook are always available (the numpy-only synthetics), and `arc_agi` — whose Hugging Face source has a local-file fallback — relies on the request-time `ImportError → 501` backstop instead.

### The gates

| Generators | Gate | Enable with |
| --- | --- | --- |
| `spiral`, `xor`, `gaussian`, `circles`, `moon`, `checkerboard`, `csv_import`, `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product` | none (numpy-only / stdlib) | — |
| `equities`, `equities_seq` | `is_available()`: pandas + yfinance importable | `pip install 'juniper-data[equities]'` — default universe is the bundled 503 S&P names and is **refused** at 14 symbols unless the caller opts in; see [Equities Symbol Cap](#equities-symbol-cap) |
| `mnist` | `is_available()`: Hugging Face `datasets` importable | `pip install 'juniper-data[mnist]'` — installs `datasets[vision]>=4.0.0` (the `[vision]` Pillow leg is required to decode the 28×28 PNGs; bare `datasets` fails at generation time). First generation downloads from the Hub — air-gapped deployments need a seeded HF cache (juniper-data README § MNIST / Fashion-MNIST). |
| `arc_agi` | no hook — parameter-conditional (`[arc-agi]` extra or local task files) | `pip install 'juniper-data[arc-agi]'`, or point params at local ARC task files |

### On-host matrix (probed 2026-08-08)

| Environment | juniper-data install | Unavailable generators | Notes |
| --- | --- | --- | --- |
| `JuniperData` (experiment-stack / launcher data-service env) | editable → the live `juniper-data` checkout | `mnist` | Has `[equities]` deps; the per-run experiment stack serves everything except mnist. |
| `JuniperCascor1` (cascor + recurrence launcher env; bench harness) | editable → the live `juniper-data` checkout | `equities`, `equities_seq`, `mnist` | Matters for **in-process** generation (`bench/`): synthetics all available; the equities pair needs `[equities]` installed into this env. |
| `JuniperCanopy1` | wheel `0.6.0` (genuinely old) | probe absent | Pre-sequence-generator vintage — no `generator_available()`, none of the 7 W-9-era generators exist there. Not a serving env; upgrade only if canopy-side generation is ever needed. |

Caveats: an **editable** install's `importlib.metadata` version (and a stale `__version__` dunder) reflect install time, not the checkout — both `JuniperData` and `JuniperCascor1` report `0.6.0` while running live `0.11.0` code. The probe answers *usable?*, never *which version*. Availability is also **per-env, not per-repo**: the same checkout probes differently under different interpreter environments.

Re-derive any row with the probe one-liner (swap the env path):

```bash
/opt/miniforge3/envs/JuniperData/bin/python -c "
from juniper_data.api.routes.generators import GENERATOR_REGISTRY, generator_available
print(sorted(n for n, i in GENERATOR_REGISTRY.items() if not generator_available(i)))"
```

Against a **running** data service, the same facts come from the API: `GET /v1/generators/{name}/schema` includes `"available"`, and unavailable generators return `501` at dataset-creation time.

The six numpy-only 2-D classification generators (`spiral`, `xor`, `gaussian`, `circles`, `moon`, `checkerboard`) are also the attribution roster in `util/snapshot_attribute.py`. Their `seed` fields are **not** interchangeable — five declare `None` and redraw every call unless pinned. Operator contract: [Snapshot Attribution Dataset Pin](#snapshot-attribution-dataset-pin). `load_datasets` still reads `X_full` / `y_full` — see [Train / Val / Test Partition Contract](#train--val--test-partition-contract).

`csv_import` stays in the "no optional-dep gate" row above: it is always *registered*. The I/O bound that shipped with juniper-data#326 is a **runtime** refusal, not an availability hook — [CSV Import Byte Cap](#csv-import-byte-cap).

---

## CSV Import Byte Cap

`csv_import` generation still runs inside the request (`APD-DATA-018`). The owner chose Option 6 of [`notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md`](../notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md) — **bound the inputs**, not an async job store. The csv_import half shipped in [juniper-data#326](https://github.com/pcalnon/juniper-data/pull/326) (`cf387a82`). The register row stays **OPEN** for the `equities` half.

Canonical constants live in juniper-data `juniper_data/core/limits.py` (imported by both `api.settings` and the generator; putting them in the generator package is circular).

### Contract (verified against juniper-data `main`)

| Knob | Value | Why it is that way |
|------|-------|--------------------|
| Cap | **128 MiB** (`CSV_IMPORT_DEFAULT_MAX_BYTES`) | Whole `generate()` path measured at median **14.4 MB/s** (`util/ad-hoc/2026-09-04_measure_csv_import_throughput.py`) → ~8.9 s parse, inside the ~30 s client budget. Above this the binding constraint is memory: `_parse_csv_stream` materialises one dict per row. |
| Default | **Refusal** (`InputTooLargeError` → HTTP **422** with a **string** `detail`) | Truncation is opt-in, never a default. Schema 422s stay a list; this one is a string so a generated client cannot mistake it for field errors. 422 is already on the API surface — `APD-DATA-022` (new status code in `responses={}`) stays parked. |
| Opt-in | request `allow_truncation`, `JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION`, or the matching `.env` entry | Logical **OR**: a client cannot opt *out* of a deployment-wide opt-in. |
| Effective cap | `min(requested, settings.csv_import_max_bytes)` | A request may only **lower** the ceiling. The first draft let `max_bytes` win outright, which made the DoS bound caller-controlled; a generated client serialising schema defaults also sends `max_bytes=134217728` on every request and would have raised a *lower* operator ceiling. |
| Enforcement | `stat` is a cheap pre-check; **the read is the bound** (`_read_capped_bytes(path, cap+1)`) | Trusting `stat` let a FIFO (`st_size == 0`) or a file that grew between stat and open be ingested without limit. `Settings.csv_import_max_bytes` carries `gt=0` because Python `read(-1)` is unbounded. |
| Annotation | `DatasetMeta.truncation` (`truncated`, `reason=source_exceeded_byte_cap`, `bytes_read`, `bytes_total`, `cap_bytes`, `records_imported`) | Permanent, popped from the generate dict before checksum + NPZ persist (`TRUNCATION_META_KEY`, mirroring `core/scaling.py`). `None`/absent means complete — a caller must never distinguish "not truncated" from "the generator forgot to say". |
| Path | `file_path` is relative to `JUNIPER_DATA_IMPORT_DIR` (default `/data/imports`) | Traversal outside that prefix is `ValueError`. This is **not** the 10 MB HTTP body limit. |

`InputTooLargeError` subclasses `ValueError` so a missed 422 mapping still lands 400, not 500.

### What this means on a juniper-ml experiment stack

`util/experiments/run_experiment.py` `create_dataset` already maps `POST /v1/datasets` **422** to `ConfigError` (driver exit **2**) — an oversized csv_import without opt-in fails closed at dataset creation, not as a 5xx.

`csv_import` is **not** in `STAGEABLE_GENERATOR_ALIASES`. A cascor-path YAML with `dataset.generator: csv_import` is refused *before* the byte cap matters (`stage_dataset` ConfigError: not a cascade-correlation staging target, plan SS10.3). The recurrence path *can* create a csv_import dataset and train against the `dataset_id`.

`experiment_stack.bash` `data_up` does **not** set `JUNIPER_DATA_IMPORT_DIR` or the two cap env vars. They inherit from the parent shell. The service default `/data/imports` is a container path — on-host `--up` will raise `FileNotFoundError` unless you export a real directory first:

```bash
export JUNIPER_DATA_IMPORT_DIR="$PWD/imports"   # file_path is relative to this
mkdir -p "$JUNIPER_DATA_IMPORT_DIR"
# optional: export JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION=true
util/experiment_stack.bash --up --recurrence --config path/to/csv-import.yaml
```

In the YAML, put `allow_truncation` / `max_bytes` under `dataset.params`. `max_bytes` can only lower the deployment ceiling.

### Still open: `equities` silent truncation

The csv_import ruling (truncation acceptable, **silence** not) has **not** been applied to `equities`. On juniper-data `main`, `EquitiesGenerator._resolve_symbols` does `ordered = ordered[: params.max_symbols]` at `generators/equities/generator.py:286` — a bare slice, no 422, no `DatasetMeta.truncation`. Defect-register `APD-DATA-018` still cites `:264`; that anchor drifted (line 264 is now CIK parsing). The cap *value* for equities is a separate owner call.

The E-H suite YAML (`util/experiments/suites/p4/e-h-real-data.yaml`) uses `symbols: [AAPL]` and does **not** set `max_symbols`, so that cell is unaffected. A run that *does* set `max_symbols` is the trap: the dataset looks complete.

| Symptom | Check / Fix |
|---------|-------------|
| Driver exit `2` `POST /v1/datasets rejected (422)` on csv_import | Source over 128 MiB without opt-in. Set `dataset.params.allow_truncation: true`, or export `JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION=true` before `--up`. Read `DatasetMeta.truncation` on the result — a truncated import is permanently annotated. |
| `FileNotFoundError` / path-traversal `ValueError` | `file_path` is not under `JUNIPER_DATA_IMPORT_DIR`. Export a real on-host directory; do not assume `/data/imports` exists. |
| Cascor YAML with `generator: csv_import` | Expected ConfigError — not in `STAGEABLE_GENERATOR_ALIASES`. Use a stageable generator, or the recurrence path. |
| Equities run silently shorter than `symbols` / the S&P universe | `max_symbols` sliced the ticker list (`:286`). Not the csv_import 422 class. |

Do **not** raise `JUNIPER_DATA_CSV_IMPORT_MAX_BYTES` without a streaming loader — 128 MiB of 20-feature rows is ~700k dicts and several GB of peak objects.

---

## Snapshot Sidecar Chain

The shared cascor archive is queryable only through four derived sidecars. None of the tools write into a `.h5`, and none ship `--prune` — retention is design §6.4 and is gated on this chain existing ([`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](../notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md) §6.2 / §6.4). Step 3 (attribution) has its own pin contract: [Snapshot Attribution Dataset Pin](#snapshot-attribution-dataset-pin).

| Step | Tool | Sidecar | What it records |
|------|------|---------|-----------------|
| 1 | `util/snapshot_index.py` | `snapshots_index.jsonl` (append-only) | Observations: path, tier, groups present, D-C provenance. Does **not** judge validity. |
| 2 | `util/snapshot_classify.py` | `snapshots_classification.jsonl` (replace) | Two axes: `category` (must we reconstruct metadata?) and `health` (what can the artifact do?). |
| 3 | `util/snapshot_attribute.py` | `snapshots_attribution.jsonl` | Dataset family, gated on the untrained-null max + cross-dataset floor. |
| 4 | `util/snapshot_backfill.py` | `snapshots_backfill.jsonl` (replace) | One record per snapshot; every field labelled `observed` / `measured` / `inferred` / `population`. |

Default `--root` is `$JUNIPER_CASCOR_SNAPSHOTS_DIR`, else `~/Development/python/Juniper/juniper-cascor/cascor-snapshots`. That env is also cascor's **write** directory. Pass `--root` explicitly for this chain; do not export the override (experiment `--up` redirects it to `$RUN_DIR/snapshots`). All four import `h5py` via `snapshot_index` — activate `JuniperCascor1` first.

### Index (`util/snapshot_index.py`)

`--scan` walks `root/*.h5` (`iterdir`, not a glob, not recursive) and appends records for files not already in the index. `--rebuild` and `--verify` apply **only with** `--scan` (`--rebuild` starts a fresh file; `--verify` imports cascor's own verifier rather than re-implementing `_validate_format_detail`).

`--limit` on a scan caps **new** files. `already_present` and `deferred_by_limit` are counted separately so a capped first pass is not reported as "almost entirely indexed".

`readable` means **h5py opened the file**, not that cascor can load it. `--unreadable` is the h5py-open failures only.

`dataset_id` is **derived**, not stored. `--resolve-datasets` (implied by `--dataset-id`) joins `provenance.run_id` → `$JUNIPER_EXP_RUN_ROOT/<run_id>/manifest.json` (honours the env; default `~/.local/state/juniper-experiments`). The join is query-time so a mid-run scan cannot bake "no dataset" into the index.

`--attributed` / `--unattributed` are mutually exclusive (exit 2). Missing root or missing index exits 2. Tiers: `cascor_snapshot_*` → `model`, `snapshot_*` → `service`, else `unknown`.

### Classify (`util/snapshot_classify.py`)

The owner's five categories are not a partition. The tool emits two axes and maps them in one place (`assign_category`):

- `fails_to_load` overrides attribution (a broken file is never `fully_attributed`).
- An attributed zero-node snapshot is category `fully_attributed` with `health=zero_node`. Ask health questions with `--health`, never `--category`.
- Unattributed zero-node stays `undetermined` until the train stage (category 2 vs 3).

| `--stage` | Cost | Resolves |
|-----------|------|----------|
| `index` (default) | ~1s | `loads_hidden_nodes` / `fully_attributed`; narrows the rest |
| `load` | minutes over the archive; probe with `--sample` | `fails_to_load` via cascor's `load_network_result` |
| `train` | not implemented (handoff item 3) | `fails_to_train` vs `formerly_broken` |

`--stage train` always exits 2. It first refuses unless `JUNIPER_CASCOR_SNAPSHOTS_DIR` is set to a scratch dir that is **not** the real archive (`train_output_layer` calls `create_snapshot()` unconditionally), then states the stage is unimplemented.

`--write` refuses `--sample` (would replace the sidecar with a partial). `--from-sidecar` cannot combine with `--stage` other than the default `index`, or with `--write`. `--from-sidecar` is how you query `fails_to_load` after a load pass — re-deriving from the index cannot produce that category.

Default `--seed` is `20260822` and samples the **index**, not classified rows. `--verbose` lets cascor logging through and breaks `--json`. Load stage reads `$JUNIPER_CASCOR_SRC` (else `~/Development/python/Juniper/juniper-cascor/src`).

`iterations_lower_bound` is `arch.num_hidden_units`. `meta.current_epoch` is inert and is never consulted; `snapshot_counter` is live but counts writes, not training progress.

### Backfill (`util/snapshot_backfill.py`)

Merges the three upstream sidecars. Missing classification / attribution is a **warning**, not a hard fail — those buckets stay empty.

| Level | Kind |
|-------|------|
| `observed` | Read from the `.h5` / index (arch, created, uuid, groups, D-C provenance). |
| `measured` | Obtained by running the artifact (load status, health, per-dataset scores, `iterations_lower_bound`). |
| `inferred` | Judgement from measurements. Dataset attribution carries `confidence` / `meaning` / `evidence` / `caveat`. Never written as observed/measured. |
| `population` | True of the **cohort**, not this file. Zero-node rows get `trainability=formerly_broken` from the hardcoded sample `380/380` of `15927` (`upper_bound_95=0.008`, `not_verified_here: true`). |

Run identity is never invented: there are no surviving experiment run dirs before 2026-07-30. Absence stays `null`; `--explain` says `IDENTITY: UNRECOVERABLE`.

Load-failure root causes come from [`JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_SNAPSHOT-CLASSIFICATION-STAGE-1-FINDINGS.md`](../notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_SNAPSHOT-CLASSIFICATION-STAGE-1-FINDINGS.md). Cohorts A and C are FIXED (juniper-cascor#560 / #559). Only B (truncated writes) still fails. Both `"Missing required attribute: format"` and `"Invalid format"` map to B so a pre-#575 sidecar still classifies.

`--from-sidecar` reads the stored record (exit 2 if missing). `--explain NAME` matches a substring of `name` or an exact `path`.

### Commands

```bash
ROOT=/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots
python util/snapshot_index.py --scan --root "$ROOT"
python util/snapshot_index.py --root "$ROOT" --stats
python util/snapshot_index.py --root "$ROOT" --unattributed --limit 20
python util/snapshot_index.py --root "$ROOT" --dataset-id <id>   # implies --resolve-datasets

python util/snapshot_classify.py --root "$ROOT" --stats
python util/snapshot_classify.py --root "$ROOT" --stage load --sample 300
python util/snapshot_classify.py --root "$ROOT" --stage load --write
python util/snapshot_classify.py --root "$ROOT" --from-sidecar --category fails_to_load

python util/snapshot_backfill.py --root "$ROOT" --write
python util/snapshot_backfill.py --root "$ROOT" --explain cascor_snapshot_
python util/snapshot_backfill.py --root "$ROOT" --from-sidecar --derivation inferred --limit 20
```

### Operator pitfalls

| Symptom | Check / fix |
|---------|-------------|
| `ERROR: h5py is required` | `conda activate JuniperCascor1` |
| `no index … run --scan first` | Index is a prerequisite for classify / backfill |
| Scan reported the archive as already indexed | `--limit` remainder is `deferred`, not `already_present` |
| `--category fully_attributed` looks empty | First-match reading of the five labels. Use `--health`. |
| `--category fails_to_load` is empty after `--write` | Re-derived from the index. Use `--from-sidecar`. |
| `--write` exits 2 on classify | `--sample` with `--write` is refused |
| `--stage train` exits 2 | Unimplemented. Unset / real-archive `JUNIPER_CASCOR_SNAPSHOTS_DIR` fails first. |
| Sidecars land in a scratch dir | The env was redirected. Unset it; pass `--root`. |
| Quoted `formerly_broken` on every zero-node file | That is a **population** claim (`380/380` sample). `--explain` shows `not_verified_here`. |
| Invented `run_id` / `experiment` | The tool will not. Pre-2026-07-30 identity is gone. |

Regression: `python3 -m unittest -v tests/test_snapshot_index.py tests/test_snapshot_classify.py tests/test_snapshot_backfill.py`.

---

## Snapshot Attribution Dataset Pin

`util/snapshot_attribute.py` infers which dataset a cascor snapshot was trained on (handoff §3.2). It scores every loadable snapshot against the six juniper-data 2-D classification generators, writes only a derived `snapshots_attribution.jsonl` sidecar, and never touches a `.h5`. An AST test forbids prune/delete paths.

Until juniper-ml#1333, **attribution was not reproducible.** Five of the six generators declare `seed: int | None = Field(default=None)`, and `load_datasets` built them from bare defaults, so every run scored against freshly drawn data.

### What broke

Two `load_datasets` calls **in the same process** returned different arrays for `checkerboard`, `circles`, `gaussian`, `moon`, and `xor`. `spiral` alone declares a real default seed — and spiral was the only column whose counts held across every rebuild.

The cost was not theoretical. Regenerating the archive sidecar moved moon's attributed count **0 → 6**:

1. moon's own score shifted `1.000 → 0.995`
2. one snapshot's first-pass winner flipped from `circles` to `moon`
3. that snapshot left moon's reference class
4. moon's cross-dataset floor fell **`1.000 → 0.850`**
5. every remaining moon attribution then cleared the floor

A one-in-a-thousand jitter in generated data moved a floor by 0.15 and changed six verdicts. Two identical invocations (`--sample 300 --seed 4242 --json`) also produced different output, including a verdict `gap` of `0.0334 → 0.0134`.

### The pin (`seeded_params`, ships with #1333)

`seeded_params(params_cls, seed)` supplies a seed **only where the generator declares none**:

| Params `seed` field | Action |
|---------------------|--------|
| **Absent** | leave the instance untouched. Absence and `None` are different answers; passing `seed=` would raise. |
| **Not `None`** | keep it. This is spiral: it stays on the exact instance every prior analysis used. |
| **`None`** | rebuild with `seed=DATASET_SEED`. |

`DATASET_SEED = 20260824` is a **pinned constant**, not a drifting default. Changing it redefines the canonical instance and invalidates comparisons with an existing sidecar.

| Flag | Default | What it actually seeds |
|------|---------|------------------------|
| `--dataset-seed` | `DATASET_SEED` (`20260824`) | generators that declare `seed=None` |
| `--seed` | `20260823` | `--sample` snapshot selection **only** |

Passing `--seed` does **not** pin the generators. That mix-up is the operator class this section exists to stop.

Every scoring run logs `dataset seed: <n> (applied only to generators declaring none; spiral keeps its own)` on stderr. Until #1333 is on the checkout you are running, `seeded_params` / `--dataset-seed` / that log line do not exist, and two identical invocations will still differ.

### Reproducibility check

```bash
ROOT=/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots
python util/snapshot_attribute.py --root "$ROOT" --sample 300 --seed 4242 --json > A.json
python util/snapshot_attribute.py --root "$ROOT" --sample 300 --seed 4242 --json > B.json
diff A.json B.json      # must be empty after #1333; was non-empty before it
```

`--write` refuses `--sample` and `--min-hidden` (exit 2) so a partial sidecar can never silently replace a full one. The untrained floor is the null's observed **maximum**, not its p95 (`adjudicate._untrained_floor`).

### Sidecar chain

The four sidecars are strictly ordered: **index → classify → attribute → backfill**. Operator contracts for index / classify / backfill: [Snapshot Sidecar Chain](#snapshot-sidecar-chain). Attribution reads the classification sidecar and covers only what it lists, so a stale classification silently caps coverage.

Do **not** export `JUNIPER_CASCOR_SNAPSHOTS_DIR` for this chain. That variable is both cascor's snapshot **write** directory and `snapshot_index.default_root()`. Probe scripts under `util/ad-hoc/` redirect them so they cannot grow the archive; the chain must not, or every stage will look for the archive in the scratch dir. Pass `--root` explicitly instead.

The one-off driver `util/ad-hoc/2026-08-24_regenerate_sidecar_chain.bash` lands with #1333. It refuses to start without `--backup DIR` that contains all four `snapshots_*.jsonl` files — the sidecars are gitignored, and a full run takes ~1h. Pass `--repo` / `--python` when not on the hardcoded worktree path. `--skip-index` is the only skip (append-only scan is cheap); classification, attribution, and backfill always re-derive.

### Counts you may quote

The findings doc §2.1 table is **run-specific and not reproducible** — it was produced before the pin. After the seeded full-chain rebuild (27,962 indexed / 27,689 attributable):

| dataset | both floors (seeded, reproducible) |
|---------|-----------------------------------:|
| xor | **94** |
| circles | **7** |
| spiral | **4** |
| moon | **3** |
| *ambiguous* | 8 |
| **attributed** | **108** |

spiral is 4 under every rebuild because it was the one generator already seeded. Pre-pin moon=0 and the unseeded-rebuild moon=6 are both artefacts of redrawing.

Full measurement, including why a capacity-matched null is not the fix: [`notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md`](../notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md) §8.

Regression: `python3 -m unittest -v tests/test_snapshot_attribute.py` (`DatasetInstanceIsFixedTest` is the hermetic pin — 5 stand-in tests, no juniper-data tree; 49 tests on #1333, was 44).

| Symptom | Check / fix |
|---------|-------------|
| Two identical `--sample --seed` runs differ | Generators are unpinned — need #1333 on the checkout. `--seed` only samples snapshots. |
| `--seed 4242` did not make attribution reproducible | Use `--dataset-seed` (or the `DATASET_SEED` constant). `--seed` is the sampler. |
| Regenerated sidecars are empty / point at scratch | `JUNIPER_CASCOR_SNAPSHOTS_DIR` was redirected. Unset it and pass `--root`. |
| `--write` exits 2 immediately | `--sample` or `--min-hidden` (or `--from-sidecar`) with `--write` is refused by design. |
| Quoted counts do not match a rebuild | Pre-pin §2.1 figures are not properties of the archive. Quote the seeded table above. |
| Chain driver errors on a missing backup file | Copy all four `snapshots_{index,classification,attribution,backfill}.jsonl` into `--backup` first. |
| `KeyError: 'X_full'` from `load_datasets` | Expected until required-fix 0 lands a replacement. Do not add a new required-`X_full` caller; see [Partition Contract](#train--val--test-partition-contract). |

---

## Train / Val / Test Partition Contract

The NPZ data contract still **emits and consumes** `X_full` / `y_full` (and sequence `dt_full` / `target_dt_full`). The design of record has **closed** the partitioning question and **drops** the `*_full` family from the contract — that removal is **not implemented**. Do not treat the six-key cheatsheet list as finished, and do not write new code that *requires* `X_full`.

- Design of record: [`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`](../notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md) — read the header + §9.5 / §9.6; §§9.3–9.4 are HISTORY.
- Implementation plan: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`](../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md) (S-3 still unhomes `NPZ_SPLITS`).
- Naming: contract keys are `X_val` / `y_val`, never `X_eval` (design §10 — Hugging Face maps `eval` → test).

### Shipped today (this repo)

| Surface | What it does |
|---------|--------------|
| `util/experiments/run_experiment.py` `RECURRENCE_SPLITS` | Allow-list `{"train", "test", "full"}`. `dataset.split` / `predict.from_dataset_split` of `"validation"` raises `ConfigError` (driver exit 2). Tests: `test_recurrence_bad_dataset_split_rejected`, `test_recurrence_bad_predict_split_rejected`. |
| Fake NPZ in `tests/test_run_experiment.py` | Tabular and sequence fixtures still write `X_full` / `y_full` (sequence also `dt_full` / `target_dt_full`). No `X_val`. |
| `util/snapshot_attribute.py` `load_datasets` | Reads `produced["X_full"]`, `produced["y_full"]` — "give me the whole dataset", not partition indices. |
| `prompts/agent_templates/data/ecosystem.yaml` | Still lists `X_train`, `y_train`, `X_test`, `y_test`, `X_full`, `y_full`. |

Partitions on the producer side are cut by `shuffle_and_split` / `temporal_split_index` and are **index-disjoint by construction** (design decision 9 REVERSED). This repo does not re-implement that split; the experiment driver only *selects* a named split from an already-built NPZ.

### Design — closed, not yet on the wire

| Decision | Ruling | Shipped? |
|----------|--------|----------|
| 9 REVERSED | Keep the current carve. P-1a and P-1b abandoned. | Yes — existing generator behaviour. The arc's net effect on the split mechanism was **zero code change**. |
| 10 COLLAPSED | No duplicate-row guard. | Yes — nothing to build. |
| 11 | `X_full` / the whole `*_full` family leave the contract. Generators emit `train` / `val` / `test` plus metadata. | **No.** Required-fix 0. |
| 12 | `partition_provenance` blob **inside the NPZ**, plus one ingestion gate. | **No.** Schema described, not specified. |
| 7 | Normaliser fit on `train` only; apply those statistics unchanged to `val` and `test`. | Decision stands. The three-generator leak is **shipped** (juniper-data#314 / data#323). |

**Closed companion tickets** (verified `CLOSED` on `pcalnon/juniper-data`, 2026-09-04): #314 (normaliser; data#323), #316 (circular import; data#333), #317 (`arc_agi` empty; data#318), #319 (seed defaults; data#322), #320 (Postgres schema; data#343).

### Remaining work — required-fix 0 only

Scoped in design §9.5.4; **none of these have started**:

1. `DatasetMeta.n_samples` is `len(X_full)` today — redefine as the partition sum (`test_e2e_metadata_consistency`).
2. Canopy's artifact validation ladder validates `X_full` (`demo_mode.py`). Re-point it or the guard is **silently lost**.
3. The data-client preview serves the first *n* rows of `X_full` — needs a new source (`train` changes semantics slightly).
4. `NPZ_SPLITS` (`juniper-data-client` `constants.py`) is `("train", "test", "full")` — drop `"full"`, add `"val"` (plan S-3; still unhomed).

**Backward compatibility.** Stored artifacts carry `X_full`. Consumers must **tolerate** it after producers stop emitting it; only the *requirement* is dropped. The design census names cascor `data_provider.py` `required_keys` as the site that would reject absence. This repo's fixtures and `snapshot_attribute.py` still *require* the key.

Items 2–4 live in sibling repos; they are listed here so a juniper-ml change that drops `X_full` from fixtures / `RECURRENCE_SPLITS` / attribution does not land first and silently break those consumers.

### Operator pitfalls

- **`dataset.split: validation` is refused today.** The design name for the third partition is `val` / `X_val`, but the experiment driver allow-list is still `{train, test, full}`. Adding `val` is implementation-plan Chunk 9, not a one-line YAML change.
- **Do not index `X_full` with partition-derived indices.** Every fleet use in the design census is "the whole dataset". `util/ad-hoc/verify_*.py` masks by ticker and re-sorts by date — that pattern does not depend on `X_full` being the pre-split array.
- **Do not treat `X_full` as uniformly normalised.** Decision 7 fits on `train` only. Until `*_full` is gone, a concatenated array can mix scales.
- **`X_eval` is the wrong name.** Hugging Face maps `eval` → test. Contract keys are `X_val` / `y_val` (design §10).
- **A new consumer that requires `X_full` extends the debt.** Tolerate the key on stored artifacts; read `train` / `test` (and `val` once it exists) for work.
- **§§9.3 and 9.4 of the design are HISTORY.** Prefix-stability / P-1b / guard measurements will mislead a successor who starts there.

### Example — recurrence split as shipped

```yaml
dataset:
  generator: mackey_glass
  split: test          # one of: train | test | full
predict:
  enabled: true
  from_dataset_split: test
```

`split: validation` (or `val`) fails at YAML load with `dataset.split must be one of ['full', 'test', 'train']`. The allow-list is the shipped contract; do not "fix" a YAML by inventing `X_val` until Chunk 9 lands.

### Related

- Attribution still regenerates via `X_full`: [Snapshot Attribution Dataset Pin](#snapshot-attribution-dataset-pin)
- Recurrence split allow-list: [Experiment Stack Utilities](#experiment-stack-utilities)

---

## P4 Campaign Suites

Scientific campaign instruments under `util/experiments/suites/p4/` (plan §10.5). They are **not** verdicts and **not** the Wave 7.3 PF instruments in `suites/perf/`. Driver: `python util/experiments/run_suite.py --suite PATH`. Always `--dry-run` first — it expands cells and prints commands, and writes nothing.

Plan of record: [`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §10.5.
First-nine evidence (E-A…E-H): [`JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md).
That note's 55-cell / nine-file census is historical — the tree now has **19** YAMLs (E-I…E-P plus a second E-H and three E-J files). Do not quote 55 as the current catalog.

### Catalog (verified against the YAML on `origin/main`)

| File | App | What it sweeps | Parallel? |
|------|-----|----------------|-----------|
| `e-a-cascor-budget-sweep.yaml` | cascor | cap × pool on spiral (exclude 32×16; include `wide-pool-long`) | no |
| `e-b-cascor-dataset-difficulty.yaml` | cascor | spiral-smoke + five generator includes | no |
| `e-c-cascor-noise-robustness.yaml` | cascor | noise × cap-64 spiral + four moon includes | no |
| `e-d-recurrence-d-sweep.yaml` | recurrence | `train.d` × three primaries | no |
| `e-e-recurrence-readout-spectrum.yaml` | recurrence | two bases + four readout includes | no |
| `e-f-recurrence-irregularity.yaml` | recurrence | jitter on `irregular_sine` | `max_parallel: 2` |
| `e-g-recurrence-cv-scheme.yaml` | recurrence | scheme × embargo | `max_parallel: 2` |
| `e-h-real-data.yaml` | cascor | equities AAPL vs spiral control | no |
| `e-h-recurrence-real-data.yaml` | recurrence | `equities_seq` AAPL vs irregular_sine control | no |
| `e-i-cascor-cap-ceiling.yaml` | cascor | cap 32/64/128 at pool 8 | no |
| `e-j-h2h-wide-cap64.yaml` | cascor | service H2H, cap 64, **3** description replicates | no |
| `e-j-h2h-wide-cap128.yaml` | cascor | service H2H, cap 128, **2** replicates (`r0`/`r1`) | no |
| `e-j-h2h-wide-cap64-init42.yaml` | cascor | init-control (dataset+init seed 42) | no |
| `e-k-thread-probe-cap16.yaml` | cascor | RC-1 service reference, cap 16 | no |
| `e-l-determinism-cap4.yaml` | cascor | 20 description replicates, cap 4 | no |
| `e-m-h2h-paired-cap64.yaml` | cascor | paired cap-64 service leg | no |
| `e-n-profile-cap4.yaml` | cascor | forked-worker profile service leg | no |
| `e-o-val-split-bias-cap4.yaml` | cascor | 8 dataset seeds, network seed 42 | no |
| `e-p-val-split-bias-cap16.yaml` | cascor | 20 dataset seeds, network seed 42 | no |

Two E-H files. `e-h-real-data.yaml` is cascor; `e-h-recurrence-real-data.yaml` is recurrence. Do not run one and cite the other.

Root-level `suites/cascor-budget-sweep.yaml` and `suites/recurrence-d-sweep.yaml` are **not** this catalog.

### Expansion (do not guess cell counts from the description string)

`expand_cells` (`run_suite.py:252`): `base_config` × `matrix` product, minus `exclude` (key-subset match), **then** `include` appended. An empty `matrix` still yields **one cell per base** — `e-e` has two bases, so it starts at two cells before the four includes.

**`include` does not inherit `matrix`.** Only `item["overrides"]` apply (plus optional `item["config"]`, else `base_config[0]`). E-A's `wide-pool-long` therefore restates `max_iterations` and pins `outputs.max_wall_seconds: 5400` itself — without that restatement it would keep spiral-baseline's 12 iterations and 3600 s wall.

```bash
python util/experiments/run_suite.py --suite util/experiments/suites/p4/e-a-cascor-budget-sweep.yaml --dry-run
# Resume / subset (cell ids from the dry-run / registry):
python util/experiments/run_suite.py --suite util/experiments/suites/p4/e-a-cascor-budget-sweep.yaml --resume SUITE_ID --only CELL_ID
```

E-A…E-H `base_config` walks into `juniper-cascor` / `juniper-recurrence`. From a worktree set `JUNIPER_EXP_PROJECT_DIR` to the ecosystem root — the override **wins** over a literal walk that happens to resolve (`run_suite.py:216-221`). Forgetting it mixes worktree **code** with primary **config**. E-J…E-P use the in-repo base `util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml`.

### R-6 budget contracts (`tests/test_experiment_suite_yamls.py`)

Defaults from the driver source: `DEFAULT_STALL_SECONDS = 120`, `DEFAULT_MAX_WALL_SECONDS = 3600`.

| Contract | Rule | Why |
|----------|------|-----|
| Oversize stall | cascor `candidate_pool_size >= 16` **or** `max_hidden_units >= 64` must declare `execution.stall_seconds` **> 120** | Q-2 watches `current_epoch`, which does not advance while the CANDIDATE pool trains. E-A lost every pool-16 cell at ~130 s. E-I: the same class arrives through **width** at pool 8 (`e-i-cascor-cap-ceiling.yaml:46-50`). |
| Wide-cap wall | cap ≥ 64 must pin a wall, via `execution.max_wall_seconds` **or** dotted `outputs.max_wall_seconds` | Unpinned cells inherit the base (3600 s on `spiral-baseline`) with no signal. E-I at pool 8: cap 32 → 1497.4 s, 64 → 2907.1 s, 128 → **4243.6 s**. |
| Timeout ordering | `execution.per_run_timeout_seconds` **>** the driver wall (`>` not `>=`) | The timeout is run_suite's **subprocess** ceiling. Equal or below: the driver is killed before it writes `manifest.json` (`run_suite.py:350-354`). E-A `wide-pool-long` is 5400 wall / 7200 timeout. |

The oversize / wall checks now **union** declared `matrix`/`include` values with per-cell effective values when the base resolves (`_effective_numbers` / `_inherited_wall_budgets`). Sibling-repo bases are `unresolved` in a juniper-ml-only checkout (CI) and the gate declines to judge them. In-repo bases always resolve — `e-k` / `e-l` inherit cap 64 from the H2H file and override **down** to 16 / 4, so reading the base alone would flag suites they are not.

E-J…E-N still set `stall_seconds: 1200` at pool 8 because the H2H base is a wide-cap / wide-wall shape; do not strip it to "match E-A pool 8".

### Cap-128 n=2 (do not quote a 3-seed spread)

`e-j-h2h-wide-cap128.yaml` `suite.description` still says "3 seeded replicates". The matrix has `r0` and `r1` only. The file header records the cut: cap 128 is the expensive half (E-I 4244 s vs 2907 s at 64); the hours went to `e-j-h2h-wide-cap64-init42.yaml`. **n = 2.** Quote the two paired deltas and the n. Seeds still start at 0, so they match the first two cap-64 seeds (`20260729` / `20260730`).

The H2H base is one config for **both** arms. The service arm never reads that file directly — `run_suite` writes `<suite_dir>/cells/<cell_id>/experiment.yaml`. The CLI arm (`util/ad-hoc/2026-08-16_h2h_cli_arm.bash`) must be handed **that generated cell file**. Feeding the base gives every CLI replicate one seed while the service arm varies.

Service vs CLI seed spreads are **not** commensurate: the CLI threads the dataset seed into network init; the service re-seeds to 42. The init-control cell is the only measurement that makes a path effect quantifiable.

### Recurrence P4 cells report; they do not gate

`e-d` / `e-e` / `e-f` / `e-g` / `e-h-recurrence-real-data` expand and write manifests. `make_baseline` / `compare_baseline` **refuse** them (exit 2) because recurrence has no work counter — landed in #1683, `read_run_metrics._recurrence_fields`. A refuse is not a missing `stats.json`. Do not add `--force`; there is none.

Only E-F and E-G are `execution.mode: parallel`. Recurrence may parallelise. Cascor `max_parallel > 1` needs a verifiable cascor `>= 0.10.0` (`CASCOR_PARALLEL_FLOOR`, `JUNIPER_CASCOR_LOG_DIR`); an unreadable version **refuses** (`run_suite.py:123-153`). None of the shipped cascor P4 files request parallel.

P4 cells ran unscraped by design — `JUNIPER_SUITE_GRAFANA_BRIDGE` is an env toggle, not a suite key. The driver's loopback `/metrics` sample still feeds `metrics_series.csv`.

### Pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Healthy cascor cell `stalled` at ~130 s | Missing or `<= 120` `stall_seconds` on pool ≥ 16 **or** cap ≥ 64. E-A pool-16 class; E-I width class. |
| `timed_out` with `exit_code: null` / no `manifest.json` | `per_run_timeout_seconds` ≤ driver wall. Raise the subprocess ceiling, not the wall, so the driver writes the honest row. |
| Include cell missing matrix axes / inherited 12 iterations | `include` is append-only. Restate every override the cell needs (E-A `wide-pool-long`). |
| Quoted 3-seed spread at cap 128 | Description is stale. n = 2 (`r0`/`r1`). |
| CLI H2H replicates share one seed | You fed the ad-hoc **base**. Use the generated `cells/<id>/experiment.yaml`. |
| Worktree run used primary cascor YAML | Set `JUNIPER_EXP_PROJECT_DIR`; the override wins over a literal resolve. |
| `make_baseline` exit 2 on E-D…E-G | Expected. Recurrence work is not countable. |
| Cascor suite refuses `max_parallel > 1` | Need cascor ≥ 0.10.0 with a readable version, or `mode: sequential`. |
| Quoted 55 cells / nine files as the tree | That census is the 2026-08-09 E-A…E-H note. Count the YAML. |
| Ran `e-h-real-data` and cited recurrence equities | Two E-H files. Check `suite.app`. |

R-6 gate: `python3 -m unittest -v tests.test_experiment_suite_yamls`. Suite driver mechanics (resume, registry, H-11): [Experiment Stack Utilities](#experiment-stack-utilities) and the `run_suite.py` utility-script bullet. PF instruments: `suites/perf/` (separate fill).

---

## X7 Off-Loop Census

X7 is event-loop blocking in juniper-canopy: synchronous retrying `requests` I/O inside `async def` route handlers on a **single-worker** uvicorn. While juniper-cascor is unreachable, canopy stops answering HTTP — `/v1/health` included. Measured end-to-end (design §2): **5.7 ms** healthy, **3.0 s** cascor stopped, **123.12 s** cascor hung (`SIGSTOP`), **5.1 ms** recovery with no restart.

Design of record (revision 4): [`notes/JUNIPER_2026-09-03_JUNIPER-CANOPY_X7-EVENT-LOOP-BLOCKING-REMEDIATION-DESIGN.md`](../notes/JUNIPER_2026-09-03_JUNIPER-CANOPY_X7-EVENT-LOOP-BLOCKING-REMEDIATION-DESIGN.md). First labelled in [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md) §6.1. Read design §§3, 5.2, 6, 7 before writing canopy code.

Slice **1a** (off-loop discipline) closes X7 **alone**. Slices 1c/1d are load reduction and honesty. Acceptance is mechanical: an AST scan of un-offloaded blocking calls in async handlers returns **0**. Splitting by mechanism is exhaustive; "core now, remaining paths later" is how SEC-F20 recurred as X7.

### Authority vs exploratory sibling

| Surface | Role | Pre-fix count |
|---------|------|--------------------|
| Site | Why a receiver-resolving `main.py` scan reports 0 |
|------|---------------------------------------------------|
| Canopy gate `src/tests/regression/test_x7_off_loop_discipline.py` | **Authority for `main.py` — and only for `main.py`.** | **52** blocking, `UNRESOLVED 0` |
| Canopy `util/ad-hoc/2026-09-04_async_blocking_callgraph.py` | **Authority everywhere else.** Transitive taint over canopy + both client libraries; sees calls that block *through a helper*. | the **6** the gate cannot |
| `util/ad-hoc/2026-09-04_x7_offload_census_v2.py` (juniper-ml; v0.3.0) | Exploratory sibling. Same classification as the gate; does **not** carry its `VERIFIED_NO_IO_CALLS` exclusions. | **54** |
| `util/ad-hoc/2026-09-04_x7_offload_census.py` (v1) | **Negative example. Do not quote its counts.** | unsound (name-matching) |
| Canopy gate `src/tests/regression/test_x7_off_loop_discipline.py` (after canopy#567) | **Authority for `main.py`.** Decide when in-file 1a is done. | 52 direct + 2 `HELPER` = **54** in `main.py`. `UNRESOLVED` fails on purpose. |
| `juniper-canopy/util/ad-hoc/2026-09-04_async_blocking_callgraph.py` (lands with canopy#567) | **Authority for the four sites outside `main.py`.** Run it when touching the adapter. | Transitive taint over canopy plus both client libraries. |
| [`util/ad-hoc/2026-09-04_x7_offload_census_v2.py`](../util/ad-hoc/2026-09-04_x7_offload_census_v2.py) (v0.3.0) | Exploratory sibling. Same classification as the pre-`HELPER` gate; no `VERIFIED_NO_IO_CALLS`. | **54** in `main.py`. Cannot see `HELPER` or the adapter. |
| [`util/ad-hoc/2026-09-04_x7_offload_census.py`](../util/ad-hoc/2026-09-04_x7_offload_census.py) (v1) | **Negative example. Do not quote its counts.** | Unsound (name-matching). |

**The count is 58, and slice 1a shipped it** (juniper-canopy#567, squashed at `e6c27e92`). The history is 40 → 39 → 37 → **52** → **58**; design §5.2 carries it in full, so "36" and "52" are both superseded.

The 54-vs-52 delta is exactly two `backend._demo` accessors (`get_network`, `get_current_state`), read and confirmed in-process. **The 52-vs-58 delta is the one that matters**: six sites the gate is *structurally* unable to see, not six it happened to miss. `_extract_meta_params()` and `_seed_training_state()` are bare module functions in `main.py` whose **bodies** hold `backend.get_status()` — at their call sites there is no receiver to resolve, so a receiver-resolving scan reports a clean 0 over calls that block identically; `create_snapshot` called the first one twice. Four more live outside `main.py`, which the gate does not read at all: adapter `connect()` and `_relay_loop()`, and `service_backend.initialize()`'s two calls — the latter on a **request** path, since `_swap_backend` awaits `initialize()` for a runtime model change.

The gate has since been extended to resolve module-level sync helpers transitively (`HELPER` bucket) and now reads 0 legitimately for `main.py`; the four sites outside it are guarded by the call-graph instrument instead. **Run that instrument when touching the adapter** — a green gate is not by itself proof that 1a is intact.

### Why `ruff --select ASYNC` is green on the bug

Canopy's pre-commit hook runs `ruff --select ASYNC` ("Async-route audit (BUG-JD-10 class)"). Verified against 35–40 live sites: **"All checks passed!"**. Ruff's `ASYNC2xx` rules match a hardcoded callee list; `backend.get_status()` is an opaque method call. **No ruff configuration can see this defect.** A second name-matching census would license the same complacency — that is why v1 is retained unfixed.

### v1 vs v2

**v1 matches receiver names.** The set is `backend`, `_adapter`, `adapter`, `_client`, `client`. In `main.py` the bare name `client` is bound to the cascor client, the redis client, the cassandra client, **and** an `httpx.AsyncClient`. It therefore reports `client.stream` at `main.py:1646` as blocking when that receiver is an awaited async client.

v1 is **closure-aware** (bare-attribute `to_thread(backend.get_status)` and named closures) — that part is correct. A naive lexical scan is not (50 unguarded / 0 guarded on this codebase).

**v2 resolves assignment provenance** inside the enclosing handler, then classifies:

| Bucket | Meaning | Counted as blocking? |
|--------|---------|----------------------|
| `ASYNC` | Bound from `httpx.AsyncClient`; calls are awaited | no |
| `CASCOR` | Module-level `backend` or a chain rooted at it | yes |
| `OTHER` | Other sync factories (`get_redis_client`, `get_cassandra_client`) — same mechanism, different upstream | yes (in scope) |
| `LOCAL` | `DataAdapter` — no network I/O (CPU only) | no |
| `UNRESOLVED` | Provenance not determined. Reported separately; never silently included or excluded | yes, if the receiver name is `client` / `adapter` / `_adapter` / `_client` |

`UNRESOLVED` fails the canopy gate on purpose. Adjudicate new receivers into the tables at the top of the test; never widen a blanket rule.

### The unsound exemption — do not reintroduce

The slice-1a gate (and v2 before v0.3.0) used an **expression-based, module-global** offload exemption: any call whose expression appeared handed to `to_thread` / `run_in_executor` *anywhere* in `main.py` was skipped *everywhere*.

Because `main.py:3574` offloads `backend.get_status`, every **other** `backend.get_status()` was invisible — including `health_check()`, `health_check_deprecated()`, and `readiness_probe()`, the three endpoints X7 is **defined by**. It degraded as work progressed: offloading one site drove the count 37 → 35 because its cassandra twin shares the expression and vanished un-fixed.

| | reported (unsound) | reality |
|---|--------------------|---------|
| distinct expressions among the 37 | 31 | — |
| edits to reach a green gate | **31** | ~21 sites still blocking |

A gate that certifies a partial fix as complete is the failure slice 1a exists to prevent. Fixed in canopy `d33ab0a` and v2 v0.3.0: exemption is **site-local only** (calls inside a nested def that is itself offloaded). Do not match by expression across sites. The `HELPER` miss is the same class of failure reached by a different route.

v1 still has `if call in offloaded` against a **module-global** name set — another reason not to trust it.

### C5 — premise holds; remedy is refuted

The blocked loop pinned outbound concurrency at 1, and slice 1a removes that accidental protection. The documented `threading.local()` session remedy does **not** apply to this client.

`JuniperCascorClient` mutates session state **only in `__init__`** (two `mount()` calls and one API-key header). `_request` passes method, url, json, params and timeout as arguments and touches nothing on the session. What is shared is the `HTTPAdapter` urllib3 pool, which is thread-safe by construction (`pool_maxsize`). A `threading.local()` session would give every worker its own pool and discard keep-alive.

Restated invariant: **the client must not mutate session state per request.** T-A4 pins it (8 threads × 4 uniquely-tagged requests, no cross-talk; session headers unchanged afterwards; vacuity: all 32 calls saw **one** `Session`). **No juniper-cascor-client change ships.** If per-request mutation is ever added upstream, T-A4 fails and the original remedy becomes correct.

### Behavioural tests (landed in canopy#567)

| ID | What it pins | Pre-fix / vacuity | After |
|----|--------------|-------------------|-------|
| **T-A1** | Closure-aware AST scan, including `HELPER` | fails (52 direct + 2 helper) | **0** |
| **T-A2** | ≥3 concurrent drivers against a 2.0 s stub; `/v1/health/live` max **< 500 ms** | fails (**6.019 s** by mutation check; design had 5.813 s from an independent run) | passes |
| **T-A3** | T-A2 vacuity: sample non-empty, each driver waited the stub bound, the route reached the backend *at the stub*, **and** the same harness **fails** against an un-offloaded control app | — | all must hold |
| **T-A4** | No per-request session mutation (C5 restated) | premise unpinned | passes |

Constraint **C4** (bounded concurrency) is **deferred to 1d**, not satisfied by 1a. Slice 1a ships bare `to_thread` because 1b already bounds per-call cost. Design §4.2 refutes unbounded offload on a measured 3 → 42 upstream amplification with the executor at 20/20. Do not imply 1a satisfies C4.

### How to run

The juniper-ml census scripts hardcode `CANOPY_MAIN = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src/main.py")`. On any other host, edit that path (or symlink) before running. They are read-only static AST walks; v2 exits `1` while blocking findings remain.

```bash
# Authority for main.py — from a juniper-canopy worktree, inside src/
conda run -n JuniperCanopy1 python -m pytest tests/regression/test_x7_off_loop_discipline.py -q

# The adapter / service_backend half has no census script in this repo -- canopy#567
# carries its own gate; do not infer an adapter count from the two scripts below.

# Exploratory sibling in this repo (do not use v1 for a count)
python util/ad-hoc/2026-09-04_x7_offload_census_v2.py
```

Offload pattern already used correctly ~30 times in `main.py`; exemplar at `:1239`:

```python
# X.method(a, b=c)  →  await asyncio.to_thread(X.method, a, b=c)
await asyncio.to_thread(backend.get_status)
```

Bare `to_thread` is intentional for slice 1a (slice 1b already bounds per-call cost). Constraint C4 (bounded concurrency) is **deferred to 1d**, not satisfied by 1a. Do not imply otherwise in a PR body. Design §4.2 refutes unbounded offload partly on a measured 3 → 42 upstream amplification with the executor at 20/20.

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Census / gate count dropped after offloading one site, twin still blocking | Module-global expression exemption — exemption must be site-local |
| `ruff --select ASYNC` is green | Expected. Opaque `backend.*` calls are invisible. Trust the gate. |
| v1 reports an awaited `httpx` call as blocking | Name-matching: `client` is overloaded. Use v2 or the gate. |
| v2 is 54, gate is 52 | Pre-fix figures. Two `backend._demo` accessors excluded by exact expression in the gate only |
| Gate is 0 — is 1a intact? | Not on its own. The gate reads `main.py`. Run `juniper-canopy/util/ad-hoc/2026-09-04_async_blocking_callgraph.py` for the adapter and `service_backend` |
| A doc says 36, or 52 | Both superseded. The count is **58** (juniper-canopy#567); design §5.2 carries the history |
| `FileNotFoundError` on `CANOPY_MAIN` | Hardcoded host path. Point it at your juniper-canopy `src/main.py` |
| Health still hangs after offloading "the hot handlers" | One un-offloaded handler reinstates the full outage. Exhaustive over the mechanism. |
| Passing `timeout=30, retries=3` "to bound it" | Those **are** the library defaults — a literal no-op. Slice 1b is `retries=0`. |
| Gate is 0, two helpers still block through `create_snapshot` / `_swap_backend` | Receiver-resolving scan without `HELPER`. Trust the post-#567 gate, not v2 |
| Gate is 0, adapter still blocks ~123 s unattended | Scope is `main.py` only. Run the callgraph; inspect `extract_network_topology()` |
| v2 is 54, gate (pre-#567) is 52 | Two `backend._demo` accessors excluded by exact expression in the gate only |
| Design still says 36, or a docs PR still says 52 | Both superseded. Shipped count is **58**. Body history: juniper-ml#1661 |
| Adding a `threading.local()` session "for C5" | Remedy refuted. T-A4 pins the no-per-request-mutation invariant. Do not discard the shared pool |
| Callgraph prints a confident 0 | First draft did that over 52 known sites. Seed taint; do not root chains at `self` |

Ad-hoc inventory: [`util/ad-hoc/README.md`](../util/ad-hoc/README.md) § X7 off-loop census.

---

## Canopy E2E Topology Step Order and Blast-Radius IDs

Operator contract for re-driving the canopy topology block without treating a harness artifact as a regression, and without re-deriving a claim about the walkthrough IDs that has already been refuted once. Triggered by [juniper-ml#1695](https://github.com/pcalnon/juniper-ml/pull/1695), which filed **F-E2E-007** and then **withdrew it the same day** after an independent-consensus review; F-CANOPY-037 remains **OPEN**. Distinct from the F-037 **render census** (in-flight docs #1652), the topology **scorer predicates** (in-flight docs #1675), and finding-triage **dispositions** (in-flight docs #1646).

Verified against `origin/main` `d69c9a73`: `util/ad-hoc/e2e_seg17_topology_driver.py`, `util/ad-hoc/e2e_finding_triage.py`, `reports/e2e/*/statuses.tsv`, and [`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md). F-CANOPY-037 is **OPEN** on main and stays open — #1695 no longer closes it. Do not copy that PR's earlier pass counts: the single combined drive scored 15 PASS / 1 INDETERMINATE, with the 16th PASS coming from a separate control run.

### `topostate` first, or alone

`step_topostate` scores M-TOPOLOGY-18 on the raw-topology **store**, not on browser traffic to `/api/topology/raw` (that fetch is server-side and Playwright cannot see it). The gate is two-sided:

| Store in Node Graph | Store in Weight Matrix | Verdict |
|---------------------|------------------------|---------|
| empty | populated | `PASS` |
| already populated | populated | `INDETERMINATE` |
| empty | still empty | `FAIL` (F-CANOPY-040 shape) |
| unreadable | — | `BLOCKED` (never score unreadable as empty) |

`topo` opens Weight Matrix for M-TOPOLOGY-03 (`set_radio(..., "weight_matrix")`). Once filled, the store stays filled for the life of the page. `--step` is comma-separated and **order-preserving** (`STEPS[name](page, capture)` on one `page`); nothing in `STEPS` rejects `topo` before `topostate`. Combined `--step topo,topoevents,topostate` in one browser session therefore trips the already-populated arm.

`INDETERMINATE` here is the scorer working: the first half was not measurable. It is not a product regression. Re-drive `--step topostate` **alone** (or put it first). Same class as the M-06 → M-17 depth-filter leak already logged in `step_topo`.

```bash
# Score M-TOPOLOGY-13 / -18 without a prior Weight Matrix visit
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
    util/ad-hoc/e2e_seg17_topology_driver.py --step topostate
```

Playwright lives in `JuniperCanopy1`. Default canopy URL is `JUNIPER_E2E_CANOPY_URL` (`http://127.0.0.1:8051`). Results merge into `JUNIPER_E2E_SEG17_RESULTS`. Isolated trio bring-up remains [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities).

### `W4-01..17` / `W1-12..14` are matrix §4 steps — they are NOT phantom IDs

A 2026-09-04 finding (**F-E2E-007**) claimed these 20 identifiers "have never existed" and used that to
close F-CANOPY-037. **It was withdrawn the same day.** This section records the corrected facts so the
claim is not re-derived by the next person who greps for the token.

They are defined, in the matrix's §4 workflow scripts:

| ID form | Definition | Steps |
|---------|------------|-------|
| `W4-NN` | `### W4 — Topology exploration` (matrix `:1005-1023`) | **17**, numbered |
| `W1-NN` | `### W1 — Cold-start cascor training` | 19; **12/13/14** are the topology-DOM steps |

Both were added 2026-08-09 in `e835e2b4` (juniper-ml#1036) and **never deleted** — `git log --all -S`
on three distinctive step strings returns that one commit each. The plan-coverage audit of the same day
states it outright: *"W4 is a 17-step script"*.

**Why a token grep reads zero.** The steps are written as ordinals (`9.`) under a section heading, not
as `W4-09`. The `W<n>-NN` form is *section + ordinal*, and it is the id form carrying **98 W-verdicts**
across `reports/e2e/*/statuses.tsv` — `W5-01`…`W5-29`, `W6-01`…`W6-21` and `W11-01`…`W11-11` all hold
individual per-step verdicts, including per-step FAILs. **Absence of the token is evidence about the
spelling, never about the definition.**

**The plan's zero `W4-` matches are the documented design, not evidence of absence.** The plan delegates
workflow ids to the matrix in terms: *"Workflow ids are the companion matrix's (`W1 … W14`, its §4
scripts are canonical); this list is a summary, not a second numbering."*

**The driver's module docstring is CORRECT.** It says these ids *"live in the MATRIX … NOT in the
plan"*. Do not treat it as stale and do not delete it — it is the pointer that resolves this.

**What IS true is coverage, not definition.** W4 has been driven once (`W4-02`, BLOCKED, run
`20260826T215010Z`) where W5 was driven thirty times. And the driver's step→row aliases carry three
defects, so do not trust them un-checked:

| Driver comment | Defect |
|----------------|--------|
| `M-TOPOLOGY-12 / W4-13` | W4-13 is box-select; the "selection can be cleared" row is **W4-12** |
| `M-TOPOLOGY-18 / W4-15` | W4-15 is the modebar camera export = **M-TOPOLOGY-14**; M-18 has no W4 step |
| `M-TOPOLOGY-08 / W1-14` | **Structurally false** — W1-14 compares the *top status bar* against the topology counts; `counts()` never reads the top bar, and the two surfaces are *designed* to diverge under the depth filter |

**F-CANOPY-037 stays OPEN.** Its fix was an `Input` → `State` demotion, so cascade growth now reaches
the rebuild through exactly one Input, `ws-cascade-add-buffer`. The 2026-09-04 re-drive produced **zero
cascade adds** on a `COMPLETED` 40/40 fixture, so the trigger the fix created is undriven. Step coverage
is 9 of 20, not "most". M-TOPOLOGY-11 (select-mode drag) and M-TOPOLOGY-16 (cascade add) stay BLOCKED —
the latter on a fixture the arc *deliberately* saturated on 2026-09-02 to preserve the 2/40/2/944
baseline, which is a reversible decision rather than an independent cause.

> **The durable tell, worth more than the facts above.** A non-existence claim that has to *spell* the
> identifier in order to deny it has already refuted itself. The literal token `W1-13` had never appeared
> anywhere in this repository's history; it entered for the first time **inside the sentence asserting it
> had never existed**. Identifiers can be defined without being spelled — ordinals under a heading, table
> positions, enum indices, generated ids — and a token grep answers only "is this string present?".

### Finding-header severity trap

`util/ad-hoc/e2e_finding_triage.py` `pri_of` takes the **first** `\b(P0/P1|P0|P1|P2|CRITICAL|LEDGER)\b` anywhere in the bolded header body after the em-dash — not only the parenthetical. A header that says "holding the arc's only P0/P1 open" before `(LEDGER; …)` is triaged **P0/P1**. Disposition parsing (`FIXED` / `HEALED` / `ACCEPTED` in the last 170 characters) is the in-flight #1646 surface; this pitfall is only the first-token rule. Do not name another severity in a header's prose.

```bash
python3 util/ad-hoc/e2e_finding_triage.py
python3 util/ad-hoc/e2e_finding_triage.py --open-only   # still prints full totals; exit is always 0
```

| Symptom | Check / fix |
|---------|-------------|
| M-TOPOLOGY-18 `INDETERMINATE` after a combined `--step` | An earlier step visited Weight Matrix. Re-drive `--step topostate` alone. |
| "The `W4-*` IDs don't exist" | They do — matrix §4, 17 numbered steps. F-E2E-007 made this claim and was withdrawn. Grep `### W4`, not `W4-09`. |
| Triage invents a P0/P1 from a bookkeeping note | First severity token in the header won. Rewrite the prose; keep one priority in the parenthetical. |
| Driver docstring lists `W4-*` / `W1-12..14` as matrix rows | **Correct — leave it.** They are matrix §4 steps. `STEPS` is what is *implemented*; the docstring is what is *specified*. |
## F-CANOPY-037 Render Census

`util/ad-hoc/e2e_f037_render_census.py` re-drives the topology-graph paint that F-CANOPY-037 measured in **2 of 11** live sessions. A single green session is ~18% likely while still broken, so this driver runs `e2e_seg17_topology_driver.py --step topodiag` in **N separate processes** (own browser, Dash session, renderer-slot pool) and tallies how many painted.

Ledger: [`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md) (F-CANOPY-037 / later F-CANOPY-039 re-drive). Bring-up stays in [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities). The census does **not** start canopy.

### How to run

```bash
util/isolated_stack.bash --up          # canopy defaults to :8051
# Train a network first — hidden_units all-0 / absent makes the census INVALID (nothing to draw)
python3 util/ad-hoc/e2e_f037_render_census.py
python3 util/ad-hoc/e2e_f037_render_census.py --sessions 5 --out reports/e2e/<run>/f037_census.json
```

Default `--sessions` is **11** (the finding's sample). `2/11` vs `11/11` is a claim; `2/11` vs `1/1` is not.

A/B a pre-merge canopy on `:8052` against the isolated cascor/data trio (live `:8051` stays up):

```bash
bash util/ad-hoc/e2e_f037_ab_premerge_leg.bash up <canopy-checkout-dir>   # dir must contain src/
JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 python3 util/ad-hoc/e2e_f037_render_census.py
bash util/ad-hoc/e2e_f037_ab_premerge_leg.bash down
```

The census inherits `JUNIPER_E2E_CANOPY_URL` (driver default `http://127.0.0.1:8051` from `e2e_w3_params_driver.py`). It does **not** take `--base-url`. `up` refuses if `:8052` is already occupied (exit `1`); misuse of `{up,down}` is exit `2`.

### What a number means

Two independent questions (`_topology_conditions`). Conflating them produced a wrong claim once:

| Field | Question | If false |
|-------|----------|----------|
| `populated` | Did any session see a non-trivial topology (`hidden_units` not `0` / `None` / empty)? | **INVALID.** Neither PASS nor FAIL can be read. Train a network. |
| `varied` | Did sessions observe **distinct** topologies? | Still **VALID** (idle scope). Tests the single mount-time rebuild. Does **not** prove the panel tracks a live cascade. |

`populated = bool(nonzero)` after filtering `"0"` / `"None"` / `""`. `bool(["0"])` is True — that is the conflation. An idle *populated* census is VALID and must not be discarded as "census tested nothing". Growth scope compares values each session **observed**; it cannot distinguish "the cascade grew while a session watched" from "consecutive sessions saw different static topologies".

### Contracts verified against source

- Verdicts come from structured `topodiag` JSON via per-session `JUNIPER_E2E_SEG17_RESULTS` (temp file). Missing or corrupt → `verdict is None`. Stdout that says `PASS` cannot clean a missing results file.
- Exit **2** if any session has no PASS/FAIL verdict (the census failed to measure). Exit **0** when every session is PASS or FAIL, **even if `painted==0`** — the tool does not judge the render rate.
- `_find_juniper_root` walks UP until a directory contains **both** `juniper-canopy` and `juniper-cascor`. Three hops from a nested worktree (`juniper-ml/.claude/worktrees/<name>/util/ad-hoc`) lands on `worktrees/` and recorded `sha=None`. One sibling is not enough. Falls back to three-hop only if the walk finds nothing.
- Provenance records the stack's `CANOPY_SRC_DIR` / `--canopy-src` (same for cascor), not a hardcoded primary. A fix under test usually lives in a worktree while the primary sits on `main`.
- Each session subprocess clears `LIBTORCH` and `LD_LIBRARY_PATH` (the `JuniperCanopy1` activate hooks do not run for a direct binary).
- `--timeout` default **420** s; the driver's own paint budget is **240** s.
- `util/ad-hoc/` is outside every pre-commit Python hook. Hermetic pins for this contract are proposed on juniper-ml#1650 and are **not** on `main` yet.

### Pitfalls

| Symptom | Check / fix |
|---------|-------------|
| Exit 0 but `painted` is 0 | Census measured. Read `scope` / `populated`. All-zero topologies → INVALID, not a render FAIL. |
| `scope=invalid` | Train a network on the isolated cascor before censusing. |
| `sha=None` for canopy | Nested worktree walk. Confirm both sibling repos sit under the resolved root, or pass `--canopy-src` / `CANOPY_SRC_DIR`. |
| Green tally from one session | Sample size 11 is the finding. `1/1` is not comparable to `2/11`. |
| A/B leg on `:8052` still hits `:8051` | Export `JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052`. The census does not take `--base-url`. |
| `up` refuses "port 8052 is already occupied" | `e2e_f037_ab_premerge_leg.bash down` kills the pidfile then `fuser -k`. Do not reuse the host `:8050` stack. |
## Requirements Snapshot Consolidation

`util/requirements_consolidate.py` is the v5 refresh tool for [`notes/requirements/`](../notes/requirements/). It exists because the v1–v4 consolidator (`phase4_consolidate.py`) was authored in `/tmp/` and is irrecoverable — the incident that produced the ecosystem-wide [Script placement](../AGENTS.md#script-placement-mandatory) rule.

**`by-area/*.md` is the corpus of record, not the ledger.** `id_assignments.yaml` has no `detail` field. Regenerating views from the ledger would silently delete the ~910 Detail sections that exist only in the views (plus `**Design**:` blocks and `*Merged from N extraction candidates (slices: X).*` provenance lines whose `slices` value lives nowhere else).

This is **not** `util/requirements_drift_check.py` (citation path / line-range integrity). Run both: consolidate owns corpus shape; the drift checker owns whether cited sources still resolve.

Design / procedure: [`JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md`](../notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md) §11 v5-1 / v5-2, [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md`](../notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md) §8.
Cross-view measurement: [`JUNIPER_2026-08-26_JUNIPER-ECOSYSTEM_REQUIREMENTS-CROSS-VIEW-MEASUREMENT.md`](../notes/JUNIPER_2026-08-26_JUNIPER-ECOSYSTEM_REQUIREMENTS-CROSS-VIEW-MEASUREMENT.md). Schema: [`notes/requirements/README.md`](../notes/requirements/README.md).

### Intent

Refresh the snapshot without losing view-only content, and without letting `by-repo` / `by-status` drift as independently-maintained copies. v5 shipped **1,814** entries (the v4 1,803 plus the official 11-entry `rec` / `juniper-recurrence` block).

### What is canonical

| Artifact | Role |
|----------|------|
| `notes/requirements/by-area/*.md` (15 locked area codes) | Corpus of record. Parse here. |
| `notes/requirements/id_assignments.yaml` | Derived ledger: ID order + `merged_count`. Briefs are truncated — never grep it for content. |
| `notes/requirements/by-repo/*.md` / `by-status/*.md` | Projection of `by-area` (ml#1415). One writer: `regenerate_views`. |

The three families used to be maintained as full copies. Measured 2026-08-29 they differed on **zero IDs and zero metadata** — 52 / 149 "content" diffs were trailing punctuation and a blank line after `**Sources**:`. Independent writers were the source of the drift, not the protection against it.

Entry bodies are re-emitted **verbatim**. Modelling every optional section as a field is the wrong shape: each omitted field was a silent corpus-wide deletion that only `--check-roundtrip` caught.

### How to run

Default is a dry run. `--apply` is required to write. `--dry-run` is accepted for symmetry.

```bash
# Safety first — by-area only. Exit 0 clean / 1 mismatch.
python3 util/requirements_consolidate.py --check-roundtrip

# Derived families must match the projection of by-area. Exit 0 / 1.
python3 util/requirements_consolidate.py --check-views

# Preview a merge (writes nothing).
python3 util/requirements_consolidate.py --merge notes/requirements/v5_rec_extraction.yaml

# Append new IDs, then project by-repo / by-status.
python3 util/requirements_consolidate.py --merge notes/requirements/v5_rec_extraction.yaml --apply

# Rewrite derived families from by-area (refuses if round-trip is already broken).
python3 util/requirements_consolidate.py --regenerate-views
python3 util/requirements_consolidate.py --regenerate-views --apply
```

`--req-root` overrides `notes/requirements` (tests). No flags prints `corpus: N entries` and exits 0 without writing.

### Merge contract

Dedup applies to **incoming** entries only. The v2–v4 quality passes (ARCH re-bucket, fuzzy cross-repo, cross-round, thin-brief repair) already ran on the shipped corpus; re-running them would churn 1,814 entries.

| Rule | Behaviour |
|------|-----------|
| Bucket | `(owner, category)` — same brief in a different area is a different requirement |
| Exact | Normalized brief match folds `merged_count` into the survivor (`DEDUP exact`) |
| Fuzzy | v3-1 overlap coefficient ≥ 0.65 (`DEDUP fuzzy`) |
| Mint | `JR-<OWNER>-<AREA>-<NNN>` via `max(used)+1`, zero-padded to 3 |
| Reused ID | `ValueError` — IDs are permanent and never reused |
| Incoming schema | `owner` / `category` / `status` / `priority` / `brief` required; unknown enum refused |

`write_all` is **append-only on `by-area`**: only files that receive a new entry are rewritten, from their own parsed entries plus the addition. The ledger is appended as raw YAML (a full `safe_dump` would re-quote ~1,100 truncated briefs). `by-repo` / `by-status` are projected **after** the post-write round-trip succeeds.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Check clean, dry-run, `--apply` with nothing new, or regenerate listed the files it wrote / would write |
| 1 | `--check-roundtrip` / `--check-views` mismatch, or `--regenerate-views` refused because `by-area` does not round-trip |
| 2 | Post-`--apply` round-trip or derived-view check failed — the tree is inconsistent; do not ship |

Malformed incoming YAML raises `ValueError` (unknown owner / category / status / priority, missing field, reused ID).

### Operator pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Regenerated views from the ledger; Detail vanished | Expected. Restore from git. Parse `by-area`, never `id_assignments.yaml`. |
| `--check-roundtrip` green, `--check-views` red | Round-trip never reads `by-repo` / `by-status`. Run both. `--regenerate-views --apply` after round-trip is green. |
| `--merge` "succeeded" but nothing changed | Default is dry-run. Pass `--apply`. `--apply` with zero new IDs also writes nothing. |
| Absolute source paths point at `.claude/worktrees/…` | `ECOSYSTEM_ROOT` walks parents for sibling `juniper-ml` + `juniper-cascor`. A worktree checkout makes `REPO_ROOT.parent` the worktrees dir; parse and render share the constant, so round-trip cannot see the corruption. |
| Orphan `by-status/foo.md` after a status emptied | `--check-views` reports `ORPHAN` and does **not** delete. Decide deliberately. |
| New area code / owner | The 15 area codes and 9 owner shortcodes are locked. A new code is a schema change, not a refresh. |
| Grepped `id_assignments.yaml` for a brief | Briefs there are truncated. Read `by-area/<CODE>.md`. |

Regression: `python3 -m unittest -v tests/test_requirements_consolidate.py` (23 tests; live tree, not a fixture — a renderer that drops one optional section fails against the shipped files).

---

## Shared-Package CI Workflows

Each in-repo published sub-package has its own subdirectory CI at `.github/workflows/ci-<suffix>.yml`. These are **distinct** from the meta `ci.yml` and the `publish-*.yml` publishers: they are the only always-on gate for that package's pytest/coverage/wheel smoke.

| Workflow | Package dir | Python matrix (min) | `--cov-fail-under` | Test `working-directory` | Wheel smoke (installed into a throwaway venv) |
|----------|-------------|---------------------|--------------------|--------------------------|-----------------------------------------------|
| `ci-ci-tools.yml` | `juniper-ci-tools/` | 3.11–3.14 | 85 | package subdir | `juniper-generate-dep-docs --version`, `juniper-env-drift-check --version`, `juniper-coverage-gap-map --version` |
| `ci-config-tools.yml` | `juniper-config-tools/` | 3.11–3.14 | 85 | package subdir | `python -m juniper_config_tools --version` |
| `ci-doc-tools.yml` | `juniper-doc-tools/` | 3.12–3.14 | 85 | package subdir | `juniper-check-doc-links --version` + `python -m juniper_doc_tools --version` |
| `ci-model-core.yml` | `juniper-model-core/` | 3.12–3.14 | 95 | package subdir | `import juniper_model_core` (asserts `TrainableModel`, no third-party runtime dep) |
| `ci-observability.yml` | `juniper-observability/` | 3.12–3.13 | 90 | package subdir | none (`twine check` only) |
| `ci-service-core.yml` | `juniper-service-core/` | 3.12–3.13 | 80 | **none** (monorepo root) | none (`twine check` only) |

Matrix rows are **minimum floors** — extra versions are fine. Every workflow is `permissions: contents: read`.

| Contract | Rule | Why it matters |
|----------|------|----------------|
| Triggers | `push` and `pull_request` on `main`, plus `workflow_dispatch` | Manual re-runs without a code change |
| Path filters | `push` / `pull_request` paths include `<subdir>/**` **and** the workflow's own path | Dropping the self-path lets a broken gate land with no red check |
| `fail-fast` | `strategy.fail-fast: false` on the test matrix | One Python version must not cancel the rest |
| Coverage | `--cov=<import>` + `--cov-fail-under=<floor>` + `coverage.json` | Per-package line-coverage floor |
| Gap-map enforce | `juniper-coverage-gap-map --coverage-json coverage.json --enforce` | Without `--enforce`, the gap map is advisory and a gutted module ships green |
| ci-tools omit | Only `ci-ci-tools.yml` passes `--omit "*/__main__.py"` (the C-2 shim) | Other packages must not silently adopt a broad omit |
| Build after test | `build.needs: test`; build `working-directory` is the package subdir | A red matrix must not look like a successful wheel smoke |
| service-core install | No test-job `working-directory`; install sibling `juniper-model-core` **before** `juniper-service-core` | Sibling-first ordering; a package-scoped WD would break the path |

Structural gate: `tests/test_subpackage_ci_workflows.py`.

| Symptom | Check |
|---------|-------|
| A workflow edit never runs CI | Confirm `paths:` still lists the workflow file itself |
| Gap map "passes" on a hollow module | Look for a dropped `--enforce` or a new broad `--omit` |
| service-core editable install fails | Confirm root-level order: model-core, then service-core |
| Build green while tests red | Confirm `build.needs: [test]` |

---

## F-CANOPY-037 Render Census

F-CANOPY-037 is "the topology graph is starved ABSENT" — the rebuild used to race a 1 Hz identical store rewrite and painted in **2 of 11** live sessions. Ledger: [`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](../notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md) entry F-CANOPY-037. A single green `topodiag` cannot validate a fix: one PASS is ~18% likely while the race is still live.

[`util/ad-hoc/e2e_f037_render_census.py`](../util/ad-hoc/e2e_f037_render_census.py) is the instrument. It launches N **separate processes** (each gets its own browser, Dash session, and renderer-slot pool) of [`e2e_seg17_topology_driver.py --step topodiag`](../util/ad-hoc/e2e_seg17_topology_driver.py) and tallies how many painted. Bring-up stays in [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities).

```bash
# isolated trio already up on 8101 / 8202 / 8051
python3 util/ad-hoc/e2e_f037_render_census.py
python3 util/ad-hoc/e2e_f037_render_census.py --sessions 5 --out reports/e2e/<run>/f037_census.json
# A/B a pre-merge canopy checkout on :8052 against the same cascor/data:
bash util/ad-hoc/e2e_f037_ab_premerge_leg.bash up /path/to/juniper-canopy
JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 python3 util/ad-hoc/e2e_f037_render_census.py
```

### Verdict source and exits

Each session writes its own file via `JUNIPER_E2E_SEG17_RESULTS` and the census reads `topodiag` from that JSON. Stdout that says `PASS` cannot clean a missing or corrupt results file — those sessions become `verdict is None`.

| Exit | Meaning |
|------|---------|
| `0` | Every session produced `PASS` or `FAIL`. Read the tally. `painted==0` is still exit 0 — the tool does **not** judge the render rate. |
| `2` | At least one session crashed, timed out, or produced no verdict. The census failed to measure. |

Default `--sessions` is **11** (the finding). `2/11` vs `1/1` is not a claim. `--timeout` defaults to 420 s; `topodiag`'s own paint budget is 240 s.

### Scope: populated vs varied

Two independent questions. Conflating them produced a wrong claim once (`bool(["0"])` is True — an all-zero `hidden_units` run is **not** idle, it is invalid):

| `scope` | `populated` | `varied` | What you may conclude |
|---------|-------------|----------|------------------------|
| `invalid` | false (`0` / absent / empty in every session) | — | Nothing. Neither PASS nor FAIL. Train a network first. |
| `idle` | true | false | VALID test of the **single** mount-time rebuild (F-CANOPY-039's core question). Do not generalise a PASS to "the panel tracks a live cascade". |
| `growth` | true | true | Distinct topologies **across sessions**. Cannot distinguish "cascade grew while a session watched" from "consecutive sessions saw different static topologies". For mid-growth paint, read per-session `elapsed_s` and trace counts. |

`populated` is "any observed `hidden_units` not in `0` / `None` / empty". `varied` is "more than one distinct observed value". An idle *populated* census is a real measurement and must not be thrown out.

### Provenance and root walk

`_find_juniper_root` walks **up** until a directory contains **both** `juniper-canopy` and `juniper-cascor`. A fixed three-`dirname` hop from `juniper-ml/.claude/worktrees/<name>/util/ad-hoc` lands on `worktrees/` and recorded `sha=None` (2026-08-31). One sibling is not enough.

`--canopy-src` / `CANOPY_SRC_DIR` (and the cascor pair) record the tree the **stack** ran from. Defaulting to the primary checkout while the isolated trio is a worktree writes an authoritative-looking wrong SHA.

The census strips `LIBTORCH` and `LD_LIBRARY_PATH` because `JuniperCanopy1` activate hooks do not run for a direct interpreter invocation (same libtorch collision class as isolated `cascor_up`).

### Pitfalls

| Symptom | Cause / fix |
|---------|-------------|
| Exit 0 with `painted==0` | Expected. The census measured; the graph did not paint. Compare to 2/11, then read `scope`. |
| `scope=invalid` after a "green" tally | Server never offered a non-zero topology. Train first. |
| `sha=None` for canopy | Nested worktree + one-sibling walk. Need both sibling dirs, or pass `--canopy-src`. |
| `1/1` published as the re-drive | Sample size is part of the claim. Keep `--sessions 11` unless you are debugging the harness. |
| Stdout `PASS` but census `BROKEN` | Results JSON missing. Do not scrape the log. |
| Host `plant_all` canopy | Ports / `DEMO_MODE` collide. Isolated stack only. |

Hermetic pins for the vacuity / walk-up / exit contract land with juniper-ml#1650 (`tests/test_e2e_f037_render_census.py`); they are not yet on `main`.

---

## Docs Full Check

Weekly (Monday 06:00 UTC) + `workflow_dispatch` workflow [`.github/workflows/docs-full-check.yml`](../.github/workflows/docs-full-check.yml). It does **not** run on PRs — per-PR CI uses `--cross-repo skip`. The weekly job clones sibling checkouts and runs the screens PR CI cannot:

1. `juniper-check-doc-links --cross-repo check` across the cloned workspace.
2. Consumer `juniper-doc-tools` pin lint (`tests/test_doc_tools_drift.py`).
3. Downstream consumer doc-link integration (per-repo failure threshold).
4. The matching `juniper-ci-tools` pin + dep-docs integration screens.
5. `util/validate_claude_yaml_access.bash` in `JUNIPER_ROOT` mode (see [Claude.yml Access Validation](#claudeyml-access-validation)).

### `ECOSYSTEM_REPOS` lockstep

`env.ECOSYSTEM_REPOS` is the clone list, and its membership must equal the registry's publishing repos minus `juniper-ml` (already the workflow checkout) plus `juniper-deploy` (a doc / `claude.yml` consumer with no PyPI package, deliberately absent from the release-train registry). Omitting a sibling silently drops it from every weekly cross-repo screen — the historical `juniper-recurrence` gap. Gate: `tests/test_docs_full_check_ecosystem.py`.

When adding a publishing sibling: register it in `util/release_train/registry.yaml`, add it to `env.ECOSYSTEM_REPOS` (and the workflow's `CONSUMERS=(...)` arrays when it pins doc-tools / ci-tools), keep `_CONSUMER_REPOS` in `tests/test_doc_tools_drift.py` aligned, then re-run `python3 -m unittest -v tests/test_docs_full_check_ecosystem.py`.

### Doc-tools pin discovery

`juniper-recurrence` pins `juniper-doc-tools` in `.github/workflows/ci-docs.yml`, not `ci.yml`. `test_doc_tools_drift.py` therefore walks **every** `*.yml` / `*.yaml` under each consumer's `.github/workflows/` so a dedicated docs workflow is not silently skipped. It soft-warns when a pin lags more than two minors and hard-fails when the upper bound excludes the current version. Local sibling trees can lag `origin/main` — set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to opt in outside CI.

### Archive-guard `merge_group` short-circuit

`ci.yml`'s `release-train-archive-guard` is a required merge-queue context, so it runs on `pull_request` **and** `merge_group`. On `merge_group`, there is no `github.base_ref`, so the job short-circuits to a green notice before any checkout or base-ref work, and every real work step stays `if: github.event_name == 'pull_request'`. It remains ABSENT from Quality Gate `needs:` so its skip on push cannot paint `push:main` red. Gate: `tests/test_archive_guard_workflow.py` (classifier behaviour stays in `tests/test_release_train_archive_guard.py`).

---

## Defect Register Close Protocol

Closing a row in [`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`](../notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md) is four touches plus a whole-file read, not a table edit. Two ad-hoc scripts re-derive counts; they are **not** interchangeable.

### The four touches

1. The **§4 table row** — set the status cell to `` `**FIXED` `` (a WON'T FIX close still writes `` `**FIXED` `` with the qualification *inside* the marker).
2. The **§5.1 verification row** — the PR and what was actually verified.
3. The **§2 Status paragraph** — add the id to the enumerated list and update the open count.
4. The header **`Last Updated`** date.

Then `grep -n 'APD-<ID>'` and **read every hit**. Ids also live in prose notes, cross-references, and other rows' cells. After a close, also re-read any sentence that counts or ranks something without naming an id — those are invisible to an ID-keyed sweep.

### Two counters, one measurement

`util/ad-hoc/register_open_set.py` is the authoritative open/fixed **counter** the close protocol keys on. `grep -cE '\*\*FIXED'` over the same file is the same §4-shaped scan reported twice: they can agree with each other and still both be wrong.

```bash
# cwd MUST be the juniper-ml repo root (relative Path("notes/..."))
python3 util/ad-hoc/register_open_set.py
# live 2026-09-04: 96 rows | 78 fixed | 18 open
```

Contract, verified against `util/ad-hoc/register_open_set.py` on `main`:

| Rule | What the script actually does |
|------|-------------------------------|
| Token | `"**FIXED" in line` after `\| (APD-[A-Z]+-\d+[ab]?) `. Lookalikes `FIXED`, `**CLOSED`, `**PARKED`, `*FIXED*` stay OPEN. |
| Union | An id is FIXED if **any** matching line carries the token (detail row + §5.1 row). Not last-row-wins. |
| Headline | Unique ids (`set`), even though the print says "rows". Letter-suffix ids (`001a` / `001b`) are distinct. |
| Prefix | `rsplit("-", 1)` so `APD-CASCOR-001a` groups as `APD-CASCOR`. |
| Cwd | `REG = pathlib.Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md")` — relative. From any other directory it raises `FileNotFoundError`. |

### The third reading

`util/ad-hoc/register_status_crosscheck.py` is the independent check: §4 `` `**FIXED` `` ids vs the §2 prose enumeration vs §5.1 verification rows. Exit **0** `AGREE` / **1** `DISAGREE`. It locates the register via `__file__` (`parents[2]`), so it runs from any cwd.

```bash
python3 util/ad-hoc/register_status_crosscheck.py
# live 2026-09-04: 96 unique ids, 78 **FIXED, 78 prose, 78 §5.1 — AGREE
```

- §2 line match: `line.startswith("**Seventy")` **or** `"have since been fixed**" in line`. The second arm is the durable one once the count leaves the seventies.
- §5.1 block: headings `### 5.1` through `### 5.2`. Missing either heading → stderr + exit 1.
- `table_fixed` currently scans **the whole file**, not only §4. A §5.1 cell that contains the `` `**FIXED` `` token can pull an OPEN §4 id into the fixed set. Combined with a matching §2 mention, `AGREE` can hide an incomplete close. Read the §4 row.
- `AGREE` is not proof that ID-free state claims ("three prefixes read zero") are current. Those have no automation.

Parked rows stay OPEN (no `` `**FIXED` ``). All three park shapes in the register (row-level, group-level, foreign-cell) stop unilateral action; they do not change these counters.

`util/ad-hoc/` is outside every pre-commit Python hook. A green hook run is not coverage of these scripts.

| Symptom | Check |
|---------|-------|
| `FileNotFoundError` on `notes/JUNIPER_…_DEFECT-REGISTER.md` | You ran `register_open_set.py` outside the repo root. `cd` there, or use `register_status_crosscheck.py` which is `__file__`-relative. |
| `grep -cE '\*\*FIXED'` matches `register_open_set.py` | Expected — they read the same rows. Run the crosscheck. |
| `AGREE` but a §4 cell is still OPEN | Whole-file `table_fixed` poison, or an ID-free sentence. Read the §4 row and any count/rank prose. |
| `DISAGREE`: FIXED in §4, absent from §2 / §5.1 | Four-touch close missed a touch. |
| Lookalike `FIXED` / `**CLOSED` / `*FIXED*` still in the open set | Only `` `**FIXED` `` counts. A WON'T FIX close still writes `` `**FIXED` ``. |

---

## Scheduled Security Scan and Lockfile Update

Operator contract for the two Monday-scheduled workflows that keep dependency hygiene unattended. Both are distinct from the per-PR `ci.yml` `security` / `dependency-docs` jobs.

### Security Scan (`security-scan.yml`)

| Item | Value |
|------|-------|
| Triggers | Cron `0 6 * * 1` (Monday 06:00 UTC) + `workflow_dispatch` |
| Permissions | `contents: read` only |
| Python | `3.12` |
| Install | `pip install pip-audit` then `pip install -e .` |
| Audit | a **sole** invocation: `pip-audit --strict --desc on` |

**Why `--strict` here but not in per-PR CI.** The scheduled scan must fail the run on a known finding. The per-PR `ci.yml` `security` job intentionally runs with `--skip-editable`, and **omits** `--strict`: pip-audit counts a skipped editable install as a dependency-collection failure, and `--strict` would escalate that to a fatal error on every PR that installs the unreleased meta-package editable. Do **not** copy `--skip-editable` into the scheduled workflow, and do **not** drop `--strict` from it. Structural gate: `tests/test_security_scan_workflow.py`.

### Lockfile Update (`lockfile-update.yml`)

| Item | Value |
|------|-------|
| Triggers | Cron `0 8 * * 1` (Monday 08:00 UTC) + `workflow_dispatch` |
| Permissions | exactly `contents: write` + `pull-requests: write` |
| Tooling | `pip install "juniper-ci-tools>=0.1.0,<0.8.0"` then `juniper-generate-dep-docs` |
| PR | SHA-pinned `peter-evans/create-pull-request` → branch `chore/lockfile-update`, labels `dependencies` + `automated`, commit/title `chore(deps): refresh CI lockfiles` |

Regenerates `conf/requirements_ci.txt` and `conf/conda_environment_ci.yaml` via the published console script. The legacy `util/generate_dep_docs.sh` was deleted in juniper-ml#298 — do **not** resurrect it here. A no-diff week opens no PR, and the opened PR is reviewed like any dependency change (never auto-merged). Companion pin lint: `tests/test_ci_tools_drift.py`; structural gate: `tests/test_lockfile_update_workflow.py`.

| Symptom | Fast check |
|---------|------------|
| Weekly scan green but a known CVE is open | Confirm the audit step is still `pip-audit --strict --desc on` |
| Scheduled scan fails on every run | Do **not** add `--skip-editable` here — that belongs only to per-PR `ci.yml` |
| No lockfile PR for several Mondays | A clean tree is expected when pins did not move; confirm the job still calls `juniper-generate-dep-docs` |
| `test_ci_tools_drift` red after a ci-tools bump | Widen the `<Y` ceiling in `lockfile-update.yml`, `ci.yml`, and `docs-full-check.yml` in the same PR |

---

## Equities Symbol Cap

`equities` / `equities_seq` generation still runs inside the request. The owner declined an async job store ([`notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md`](../notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md) Option 6) and bound the **inputs** instead.

The two halves of that decision took **different units**, because the cost is different:

| Half | Unit | Why |
|------|------|-----|
| `csv_import` ([juniper-data#326](https://github.com/pcalnon/juniper-data/pull/326)) | **bytes** (128 MiB) | Input is a file; bytes are what an operator can enforce without parsing |
| `equities` ([juniper-data#354](https://github.com/pcalnon/juniper-data/pull/354), `ed099920`) | **symbols** (14) | Cost is per *request* — 163× the payload costs 1.16× the time |

*The unit belongs to the cost, not to the register.* A byte cap on equities would admit the expensive request and reject the cheap one. Measurement: [`notes/JUNIPER_2026-09-04_JUNIPER-DATA_EQUITIES-INGEST-SIZING-AND-FIELD-AVAILABILITY.md`](../notes/JUNIPER_2026-09-04_JUNIPER-DATA_EQUITIES-INGEST-SIZING-AND-FIELD-AVAILABILITY.md) (landed via juniper-ml#1669). Producer contract lives in juniper-data; this page is the **experiment-stack** view.

### Why a byte cap is the wrong unit

Measured 2026-09-04 (`juniper-data/util/ad-hoc/2026-09-04_measure_equities_payloads.py`). Holding the symbol fixed and varying only the horizon, Yahoo chart payload scales **163×** while wall time moves **1.16×**.

| Request | Wire bytes | Wall time |
|---------|-----------:|----------:|
| 1 symbol × 26 years | **210 KB** | **~2 s** |
| Russell 3000 × **1 day** | **92 KB** | **1.7–3.2 h** |
| 1 symbol × 26 years (`since 2000`) | **210 KB** | **~2 s** |

Per-symbol cost is **~2.1 s** (2026-09-04, optimistic) / **4.01 s** (2026-09-02, conservative). `14 = 30 s ÷ 2.1 s/symbol` — the owner's choice from that range. Yahoo is `yf.download(..., threads=False)` plus 1–2 SEC `companyconcept` GETs (`_SEC_MIN_INTERVAL = 0.12`). The data-client default timeout is **30 s**.

The previous default — `EQUITIES_DEFAULT_MAX_SYMBOLS = None`, meaning all **503** bundled S&P names — was 36× to 67× over budget (18–34 min). The cut was a bare slice at `_resolve_symbols` that truncated **silently**. Both are gone as of data#354.

### Shipped contract (verified against juniper-data `main` after data#354)

| Knob | Value | What it does |
|------|-------|--------------|
| `EQUITIES_DEFAULT_MAX_SYMBOLS` | **`14`** (`juniper_data/core/limits.py`) | Deployment default / `EquitiesParams.max_symbols` default. Settings field `gt=0` so a mistyped `0` or `-1` fails construction instead of emptying the slice. |
| `EQUITIES_DEFAULT_ALLOW_TRUNCATION` | **`False`** | Truncation is opt-in, never a default. |
| Effective cap | `min(requested, settings.equities_max_symbols)` | A request may only **lower** the cap. `max_symbols=None` means *no request-side limit*, **not** unbounded — the deployment ceiling still applies. There is no way for a caller to ask for an unbounded universe. |
| Opt-in | request `allow_truncation` **OR** `JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION` / `.env` | Logical OR. A client cannot opt *out* of a deployment-wide opt-in. |
| Default `EquitiesParams()` against 503 names | `InputTooLargeError` → HTTP **422** with **string** `detail` | Route: `datasets.py` `HTTPException(..., detail=str(e))`. Schema 422s remain a list. 422 was chosen because it is already on the surface (`APD-DATA-022` stays parked). |
| Authorised cut | deterministic prefix + `build_truncation_meta` | `reason=universe_exceeded_symbol_cap`, `unit=symbols`. `generate()` fills `records_imported` after conditioning (`-1` until then — recording `0` would be a lie). Descriptor rides `TRUNCATION_META_KEY` and is popped **before** checksum + NPZ persist. |
| Shared descriptor | `truncated` / `reason` / `unit` / `cap` / `requested` / `imported` / `records_imported` | Same shape as `csv_import` (that half uses `unit=bytes`). |
| `equities_seq` | reuses `EquitiesGenerator._resolve_symbols` | Inherits the bound **and** the annotation. `EquitiesSeqParams` subclasses `EquitiesParams`, so the knobs need no redeclaration. |
| Cache | `JUNIPER_DATA_EQUITIES_CACHE_DIR` | `experiment_stack.bash` `data_up` sets this to `$RUN_DIR/equities-cache`. It does **not** set the two cap env vars — they inherit. |
| Default universe | bundled `sp500_constituents.csv` (**503** tickers) when `symbols` is omitted | `_resolve_symbols` sorts the CSV keys. Index *titles* over-claim (Russell 3000 published 2,923; Wilshire 5000 published 3,414 as of the 2026-09-04 count). |
| Boundary | `ordered = ordered[: params.max_symbols]` at `generators/equities/generator.py:286` | Bare slice. **No 422**, no `DatasetMeta.truncation`, no record of dropped tickers. Register `APD-DATA-018` still cites `:264` — that line is now CIK parsing in `_load_constituents`. |
| Features | 10 `float32` columns in `EQUITIES_FEATURE_COLUMNS` | `open, high, low, close, volume, week52_high, week52_low, total_shares, market_cap, cost_basis`. `Adj Close` is downloaded (`auto_adjust=False`) and kept as `adj_close` for optional `basis_price_field`, then **dropped** from `X`. |
| `seed` | defaulted (`DEFAULT_GENERATOR_SEED`) | Unused for the temporal split. Real non-reproducibility: `end_date` defaults to the wall clock. |
| Shares fill | `fundamentals_fill` default `"zero"` | Missing SEC facts → `total_shares` / `market_cap` become **0.0**. The rows stay. |

Failed Yahoo downloads still skip. Missing SEC facts + `fundamentals_fill="zero"` still write `0.0`. The generator never calls `Ticker.info`.

### What this means on a juniper-ml experiment stack

`equities` **is** in `STAGEABLE_GENERATOR_ALIASES` (`util/experiments/run_experiment.py`). `equities_seq` is **not** (3-D sequence family, plan SS10.3) — a cascor-path YAML with `dataset.generator: equities_seq` is `ConfigError` before any download.

`create_dataset` maps API `400` / `422` / `501` to `ConfigError` (driver exit **2**). A default-universe YAML that used to sit in `create_dataset` for tens of minutes (or hit the 30 s client timeout) now fails immediately with the curated `InputTooLargeError` message.

The E-H suite (`util/experiments/suites/p4/e-h-real-data.yaml` and `e-h-recurrence-real-data.yaml`) sets `symbols: [AAPL]` and does **not** set `max_symbols` or `allow_truncation`, so those cells stay inside the cap with no annotation.

`JuniperCascor1` does **not** have `[equities]` — see [Generator Availability Matrix](#generator-availability-matrix-on-host). In-process `bench/` generation of the equities pair fails `is_available()` there. The experiment-stack `JuniperData` env does have the extra.

```yaml
# stay inside the 14-symbol refuse — pick an explicit list:
dataset:
  generator: equities
  params:
    symbols: [AAPL, MSFT, GOOGL]
    # allow_truncation: true       # opt-in prefix cut; writes DatasetMeta.truncation
    # max_symbols: 10              # may only lower the deployment ceiling
    start_date: "2015-01-01"
    end_date: "2022-01-01"         # pin this; default is today
    regression_target: log_return  # recurrence E-H; default next_close is non-stationary
```

To raise the **deployment** ceiling (not the request), set `JUNIPER_DATA_EQUITIES_MAX_SYMBOLS` on the data service. `experiment_stack.bash` does not set it. Raising it past ~14 spends the 30 s client budget again; raising it to 503 restores the 18–34 min fan-out the cap exists to stop.

### Operator pitfalls

| Symptom | Check / Fix |
|---------|-------------|
| Driver exit `2` / API `422` on default `equities` | You asked for the full S&P 500. Set `symbols` to ≤14 names, or set `allow_truncation: true` and accept a permanent `DatasetMeta.truncation`. |
| Requested `max_symbols: 50` still caps at 14 | A request may only *lower* the ceiling. Raise `JUNIPER_DATA_EQUITIES_MAX_SYMBOLS` on the **service**, then re-request. |
| Truncated dataset looks complete | Authorised cut writes `meta.truncation` (`reason=universe_exceeded_symbol_cap`). Count `ticker_vocab` against `imported`. The old silent slice is deleted. |
| Dataset create hangs / client timeout on default `equities` | You asked for the full S&P 500. Set `symbols` to a short list. `max_symbols` also bounds the list but **truncates silently**. |
| Equities run silently shorter than `symbols` / the S&P universe | `max_symbols` sliced at `:286`. The NPZ looks complete. Count `ticker_vocab`. |
| `total_shares` / `market_cap` are all zeros | SEC returned no facts for that CIK, then `fundamentals_fill: zero`. Use `nan` or `drop` if zeros would train. |
| Cascor YAML with `generator: equities_seq` | Expected `ConfigError` — not in `STAGEABLE_GENERATOR_ALIASES`. Use the recurrence path, or flat `equities`. |
| `501` / `equities` unavailable | Install `juniper-data[equities]` into the **serving** env (`JuniperData` for the experiment stack; `JuniperCascor1` for in-process bench). |
| Assumed Yahoo `.info` fields (`trailingPE`, `floatShares`, …) | The generator never calls `Ticker.info`. It uses `yf.download` (chart) + SEC XBRL. |
| Expected a byte cap to bound wall time | Anti-correlated. One symbol × 26 y is 210 KB / ~2 s; Russell 3000 × 1 day is 92 KB / 1.7–3.2 h. |
| Expected splits / dividends / 52-week **dates** / reporting date in `X` | Not in `EQUITIES_FEATURE_COLUMNS`. Splits/dividends need `actions=True` (not passed). 52-week **values** are already features; dates and SEC `filed` are computed/downloaded and discarded. |

Do **not** re-introduce a silent prefix slice. Do **not** treat a byte threshold as the binding bound.

---

## Release-Train Detect Summary and Slack

Operator contract for the detect job's **Render step summary** and **Slack notification** heredocs in [`.github/workflows/release-train.yml`](../.github/workflows/release-train.yml). The full mode / Gate / HALT surface stays in the [release-train operator runbook](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.1. Hermetic YAML-extraction pins: `DetectSummaryRehearsalTest` / `DetectSlackPayloadRehearsalTest` in `tests/test_release_train_workflow_guard.py`.

### Action set vs the ceremonial class

Both renderers treat `UNRELEASED_CHANGES`, `BUMPED_NOT_RELEASED`, and `SHIP_UNCERTAIN` as needing release action. `BUMPED_NOT_RELEASED` **alone** is the ceremonial class (Gate 2 / the ceremony job). Do not read "needs action" as "ceremony will run".

| Mode | Footer counts | Operator reading |
|------|---------------|------------------|
| `report` (default) | Full action set | Report-only; no write job ran |
| `propose` | Full action set | Read the **propose** job summary for `opened:` / `skip:` |
| `ceremony` | **Only** `BUMPED_NOT_RELEASED` | `UNRELEASED_CHANGES` / `SHIP_UNCERTAIN` are not ceremony candidates |

With a present, non-empty manifest, the summary carries the title, package total, per-classification counts, a `Release hygiene: TAG_ONLY=N, NOTES_MISSING=M` line (truthy values only), the per-package table, collapsed detector notes, and the mode footer.

### Hard-fail banner and Slack

If `release-manifest.json` is absent or blank, the summary writes only `**Detector failed hard -- no manifest was produced.** See the run log.` — no package table. The step still exits 0 (`if: always()`); treat it as a red detector outcome, never a quiet "0 packages need action". The Slack step posts only when `SLACK_WEBHOOK_URL` is set, is `continue-on-error`, and sends counts plus the run URL (or the `detector FAILED HARD` line) — no secrets, diffs, or CHANGELOG bodies.

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| Ceremony footer says 0 while the report footer said N > 0 | The action set includes `UNRELEASED_CHANGES` / `SHIP_UNCERTAIN` | Run `propose` for those; ceremony only after the versions are bumped |
| "Detector failed hard" on a green job | Manifest missing after an early abort | Open the detect log; do not invent a quiet clear |
| No Slack post | Secret unset or a post error | Expected non-blocking behaviour — read the step summary |

---

## AGENTS.md Date Check

[`.github/workflows/agents-md-touch-up.yml`](../.github/workflows/agents-md-touch-up.yml) keeps `AGENTS.md`'s `**Last Updated**:` header aligned with the UTC date the file actually changed — by **verifying** it, never by rewriting your branch. The companion schema lint is `tests/test_agents_md_header_schema.py` (presence + `YYYY-MM-DD`); version equality is a separate concern (`tests/test_agents_md_version_drift.py`).

| Item | Value |
|------|-------|
| Events | `pull_request` types `opened` / `reopened` / `synchronize` |
| Paths filter | `AGENTS.md` only |
| Job `if` | none — fork PRs are checked too (verification needs no token) |
| Permissions | `contents: read` |
| Concurrency | `agents-md-date-check-<PR number>`, `cancel-in-progress: true` |

Behavior: check out the PR head with full history; if `AGENTS.md` has **no** `**Last Updated**:` line, emit a `::warning::` and pass; otherwise, the value must be a well-formed `YYYY-MM-DD` date and must not be in the future. It then passes on **either** of two arms, checked in this order: the value **already equals today's UTC date**, or the line **changed in this PR** (`git diff <base>...HEAD` contains `+**Last Updated**:`). Anything else fails the check and prints the exact line to write.

> Both arms are load-bearing, and this paragraph previously named only the second — which made a same-day PR that legitimately has nothing to bump look like a check failure waiting to happen. The two arms differ in **durability**: already-today is re-evaluated every run and expires at the next UTC midnight; changed-in-this-PR holds for the life of the PR. That distinction determines the stacked-PR remedy above.

The predicate is "the line changed", not "the line equals today": a PR opened Monday and merged Thursday would fail an equals-today check on every re-run. `util/release_train/propose.py` sets this header in its own commit, so release-train proposals satisfy the check as authored.

**This job used to bump the date and push the commit itself.** That was removed in juniper-ml#1099 because it produced two failure classes under the 2026-08-12 `required_signatures` normalization:

| Class | Effect |
|-------|--------|
| Unsigned commit | A local `git commit` on a runner is unsigned; `required_signatures` rejects it, and an unsigned commit anywhere in the branch history blocks the merge (squash does not rescue it) |
| `[skip ci]` orphan | The bump commit became the PR head, and because it carried `[skip ci]` **no required context ever reported on it** — the PR sat permanently BLOCKED with every check stuck at "expected" (juniper-cascor#515) |

It also raced `Update Lockfile (Dependabot)` for the push slot. Verifying eliminates all three, and drops the lane's write scope entirely. Coverage: `tests/test_agents_md_touch_up.py` (11 arms, including an anti-resurrection assertion that the shell can never `git commit` / `git push` / `sed -i` again).

---

## Claude.yml Access Validation

Public Juniper repos that run [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action) spend `ANTHROPIC_API_KEY`. A missing `@claude` job guard or a dangerous trigger turns drive-by events into secret spend. The structural auditor is [`util/validate_claude_yaml_access.bash`](../util/validate_claude_yaml_access.bash); the long-form procedure is [`notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md`](../notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md).

| Level | Finding | Why it matters |
|-------|---------|----------------|
| **L2** | `on:` contains `pull_request_target:` or `workflow_run:` | Fork PRs / untrusted workflows inherit repo secrets |
| **L3a** | The `claude:` job has no job-level `if:` | Every matching event runs the action |
| **L3b** | The job `if:` lacks `contains(..., '@claude')` | Comments / issues without `@claude` still spend the key |

Exit codes: `0` clean (or no targets, with a warning), `1` finding, `2` usage / I/O.

```bash
# This repo's live workflow (what ci.yml's claude-yaml-audit job runs)
bash util/validate_claude_yaml_access.bash .github/workflows/claude.yml

# Explicit file or directory targets
bash util/validate_claude_yaml_access.bash /path/to/juniper-canopy

# Cross-repo fan-out (what the weekly docs-full-check runs after sibling clones)
JUNIPER_ROOT=/path/to/Juniper bash util/validate_claude_yaml_access.bash
```

With no arguments and no `JUNIPER_ROOT`, the script audits `juniper-ml/.github/workflows/claude.yml` relative to the script location. A missing `claude.yml` under a `JUNIPER_ROOT/<repo>/` path is skipped, so a clone miss never invents a FAIL.

### `DEFAULT_REPOS` fan-out (orthogonal to `ECOSYSTEM_REPOS`)

`JUNIPER_ROOT` mode does **not** scan every directory under the root — it iterates the hard-coded `DEFAULT_REPOS` array in the bash source, whose membership is the registry's publishing repos plus `juniper-deploy`. This is orthogonal to [`ECOSYSTEM_REPOS`](#docs-full-check): the clone list decides which siblings are *cloned*; `DEFAULT_REPOS` decides which cloned checkouts the auditor actually *opens*. Adding a publishing sibling to one without the other leaves a silent audit gap, so the two lists must move together (both currently include `juniper-recurrence`).

| Surface | When | What runs |
|---------|------|-----------|
| `ci.yml` job `claude-yaml-audit` | Every push / PR | The validator against this repo's live `claude.yml`; required by the Quality Gate |
| `ci.yml` / `main-verify.yml` battery | Same | `python3 -m unittest -v tests/test_validate_claude_yaml_access.py` |
| `docs-full-check.yml` | Weekly Mon 06:00 UTC + dispatch | `JUNIPER_ROOT="$GITHUB_WORKSPACE" bash juniper-ml/util/validate_claude_yaml_access.bash` after the sibling clones |

The bash auditor covers L2/L3 structure only; juniper-ml's own `on:` event matrix and exact job `permissions` are pinned separately in `tests/test_validate_claude_yaml_access.py` — a permissions widen that still carries an `@claude` guard would not trip L2/L3 alone. Live pin, inputs, and Dependabot contract: [Claude Code Action](#claude-code-action).

---

## Claude Code Action

`.github/workflows/claude.yml` is the GitHub Actions `@claude` assistant. It is **not** the local CLI launcher (`scripts/wake_the_claude.bash` / `claudey`). Mentioning `@claude` on a public issue or PR spends `secrets.ANTHROPIC_API_KEY`. Access-safeguard audit (L2/L3, `DEFAULT_REPOS`) is [Claude.yml Access Validation](#claudeyml-access-validation); this section is the **live workflow contract** — triggers, permissions, SHA pin, and Dependabot.

The job is **not** a required status check and is **not** in Quality Gate `needs:`. It has no `push` or `pull_request` trigger, so a commit to `main` does not start it.

### Workflow contract

| Item | Value |
|------|-------|
| Workflow/job-name | `Claude Code`/`claude` |
| Triggers | `issue_comment` (`created`); `pull_request_review_comment` (`created`); `issues` (`opened`, `assigned`); `pull_request_review` (`submitted`) |
| Job `if:` | Every `on:` event is named in the expression; each arm requires the literal `@claude` (comment body, review body, or issue body/title) |
| Permissions | Exact map: `contents: write`, `pull-requests: write`, `issues: write`, `id-token: write`, `actions: read` |
| Checkout | SHA-pinned `actions/checkout` with `fetch-depth: 1` (shallow) |
| Action | SHA-pinned `anthropics/claude-code-action` with a `# vX.Y.Z` comment. Only input: `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` |
| Required secret | Repo secret `ANTHROPIC_API_KEY` (personal-account owner — not an org Actions secret) |

Read the live `# v…` comments in the workflow for the current pin — do not copy a version number out of this page.

Gate: `tests/test_validate_claude_yaml_access.py` (`LiveClaudeWorkflowContractTests`) pins the `on:` set, that every event is named in `if:`, and the exact permissions map. It does **not** pin the action SHA — Dependabot patch bumps of `anthropics/claude-code-action` are expected and do not fail the suite.

### SHA pin and Dependabot

Both `uses:` lines are SHA-pinned with a trailing `# vX.Y.Z` comment. Do not retarget a floating tag (`@v1`).

`.github/dependabot.yml` (`github-actions`, weekly Monday, `open-pull-requests-limit: 3`) groups **only** `github/codeql-action*`. `claude-code-action` is a single `uses:` line, so an ungrouped bump (one file, one SHA) is the healthy PR. That is unlike CodeQL, where an ungrouped bump splits `init` / `autobuild` / `analyze`.

`notes/templates/ci/claude.yml` is the 2026-04-29 rollout snapshot (`actions/checkout` v6.0.2, `anthropics/claude-code-action` v1.0.107). The live workflow is the source of truth (the template header already says so). Copying the template over `.github/workflows/claude.yml` rewinds both pins.

### Operator pitfalls

| Symptom | What it actually is | What to do |
|---------|---------------------|------------|
| `@claude` did not run | Job `if:` requires the literal `@claude` in that event's body (or issue title). `issues: assigned` still needs it | Add `@claude` to the comment/review/issue text |
| Action ran on every comment | Missing or weakened `if:` (L3) | Restore the four-arm `@claude` guard; `bash util/validate_claude_yaml_access.bash .github/workflows/claude.yml` |
| Fork PR spent the key | `on:` gained `pull_request_target` or `workflow_run` (L2) | Remove those triggers; never add them |
| Template "sync" rewound the pin | `notes/templates/ci/` snapshot lags Dependabot | Restore `.github/workflows/claude.yml` from `main`; leave the template as a historical snapshot |
| Floating `@v1` / un-SHA'd tag | Mutable tag; SHA pin is the contract | Keep `uses: ...@<sha>  # vX.Y.Z` |
| Permissions widen, auditor still green | L2/L3 bash does not pin the permissions map | `LiveClaudeWorkflowContractTests.test_job_permissions_exact` fails; do not drop that test |
| Workflow file present, action cannot resolve the key | `ANTHROPIC_API_KEY` is a **repo** secret on this personal-account owner | Set the secret on the repo; walkthrough [§1.1](../notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md) |

---

## CodeQL Analysis

[`.github/workflows/codeql.yml`](../.github/workflows/codeql.yml) is the Python semantic-SAST lane. It is **not** a Quality Gate `needs:` member — the check context **`Analyze (python)`** is promoted in the **branch ruleset** (`required_status_checks`), the same soak-then-promote path later jobs copy (see [Flood-Remediation CI Gates](#flood-remediation-ci-gates)). SARIF from the job also feeds the ruleset `code_scanning` rule (tool: CodeQL). There is no in-repo `tests/test_codeql_*.py` and no `.github/codeql-config.yml`; the live workflow file is the contract.

### Workflow contract

| Item | Value |
|------|-------|
| Workflow name | `CodeQL Analysis` |
| Job / check context | `analyze` / **`Analyze (python)`** (`strategy.matrix.language: ['python']`) |
| Triggers | `push` to `main`/`develop`; `pull_request` targeting `main`; `merge_group`; cron `0 6 * * 1` (Monday 06:00 UTC) |
| Permissions | `actions: read`, `contents: read`, `security-events: write` |
| Queries | `+security-and-quality` (security pack **plus** quality queries) |
| Config file | none — no `config-file:` input |
| Action pins | SHA-pinned `github/codeql-action/{init,autobuild,analyze}` — **one SHA across all three**, with a `# vX.Y.Z` trailing comment |

`actions/checkout` is pinned separately and is **not** in the CodeQL Dependabot group. Read the live `# v…` comments in the workflow for the current pin — do not copy a version number out of this page.

### Dependabot group (split-pin prevention)

`.github/dependabot.yml` (`github-actions` ecosystem) defines group `codeql-action` with pattern `github/codeql-action*`. That group is load-bearing. Without it, Dependabot opens one PR per subaction and the pins diverge.

A split pin fails the job with `Loaded a configuration file for version 'X', but running version 'Y'`: `init` writes a config for its version, and a different `analyze` refuses it. The healthy bump is **one** PR titled like `ci: bump the codeql-action group … with 3 updates` that moves `init`, `autobuild`, and `analyze` together. Do not merge a partial bump; do not delete the group.

`notes/templates/ci/codeql.yml` is the 2026-04-29 rollout snapshot (older SHA, no `merge_group`). Copy from the **live** workflow, not the template.

Design: [`notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ENV-REPR-CODEQL-AND-RECURRENCE-PARITY-PLAN.md`](../notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ENV-REPR-CODEQL-AND-RECURRENCE-PARITY-PLAN.md) §2.2.

### `merge_group` is an accepted juniper-ml-only divergence

The file header still calls this a fleet template sourced from `juniper-data/.github/workflows/codeql.yml` with "no per-repo customization". juniper-ml is the only copy that listens on `merge_group`, so the required `Analyze (python)` context re-posts on a queued merge commit (flood-remediation §4 item 1). The divergence is deliberate:

- Do **not** overwrite this file with the data / template copy — that drops `merge_group` and stalls a queue with no required check.
- Do **not** sweep `merge_group` into siblings until that sibling enables its own merge queue.

A User-owned repo cannot currently add the merge-queue **rule** ([enablement runbook](../notes/JUNIPER_2026-08-16_JUNIPER-ML_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md) §4). The trigger stays as the prerequisite. Standing-item record: [`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md`](../notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md) §3.12.

### Operator pitfalls

| Symptom | What it actually is | What to do |
|---------|---------------------|------------|
| `Analyze (python)` red: version mismatch | `init` / `autobuild` / `analyze` SHAs diverged | Align all three to one SHA; confirm `groups.codeql-action` still exists |
| Dependabot opened 3 CodeQL PRs instead of 1 | Group missing or pattern not matching | Restore `groups.codeql-action` with pattern `github/codeql-action*` |
| Checks green, merge `BLOCKED` | CodeQL left a PR review comment; unresolved threads do **not** appear in the check rollup | Read Conversation (or `gh pr view N --json mergeStateStatus`); **fix the finding in code** (export or delete an unused module global; add a new public name to `__all__`). Do not dismiss the bot thread by hand |
| Merge stalled: "waiting for results from CodeQL" | Ruleset `code_scanning` has no SARIF for that SHA yet | Wait for `Analyze (python)` to finish; if a queued merge never gets a context, restore `on.merge_group` |
| Quality Gate green, CodeQL red | Expected — CodeQL is not in `required-checks.needs` | Fix the CodeQL job or the finding; **never** add this job to Quality Gate `needs:` (a skip on `push:main` would fail the gate the same way sequence-safety would) |
| Copying `notes/templates/ci/codeql.yml` "to sync the fleet" | Template has no `merge_group` and a stale SHA | Edit `.github/workflows/codeql.yml` |

`code_scanning` wait strings observed in ruleset suites: [`notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md`](../notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md) §4.3.

---

## Required-Context Ruleset Writer

[`util/ad-hoc/2026-08-20_require_context_safely.py`](../util/ad-hoc/2026-08-20_require_context_safely.py) is the fleet writer that adds — or, as of [juniper-ml#1612](https://github.com/pcalnon/juniper-ml/pull/1612), **re-pins** — one required status-check context on a repo ruleset. It is retained ad-hoc tooling (owner policy 2026-08-25): there is no general ruleset editor in `util/` proper, and a hand-rolled `gh api .../rulesets/N -X PUT` is the class of edit this module exists to prevent.

Default `--context` is `Guard PR base branch`. Default `--integration-id` is `15368` (the GitHub Actions app). Dry-run is the default; `--apply` writes. `--status` reports and never writes.

### Why a missing `integration_id` is a hole

A required context with no `integration_id` is satisfied by **any** app that publishes a check-run of that name. [juniper-ml#1611](https://github.com/pcalnon/juniper-ml/issues/1611) is the concrete case: `Memory Budget` was the only one of this repo's 17 required contexts left unpinned (the other 16 pin `15368`), so the gate that enforces the memory-budget ratchet for the whole fleet could be satisfied by a namesake from the wrong app.

The add path cannot fix that. An already-required context short-circuits:

```text
ALREADY REQUIRED (integration_id=...) — no-op
```

`--amend-integration-id` mutates that one entry in place and leaves every other context object untouched.

### Two pre-flights, on purpose

| Path | Question the pre-flight answers | Lookup |
|------|----------------------------------|--------|
| **Add** (default) | Does **anything** publish this exact context **name** here? | `observed_contexts`: check-run names on the 8 most recently updated PR heads, conclusion-agnostic |
| **Amend** (`--amend-integration-id`) | Is **this app** the publisher of that exact name? | `observed_context_apps`: `{app_id: slug}` for check-runs whose name matches **exactly**; falls back to `main`'s check-runs when PR heads show nothing |

Getting the amend question wrong is not hypothetical: a hardcoded id retargeted `Bandit` (`57789`) at an app that never reports it and left five repos' `main` unmergeable with nothing red — PRs `BLOCKED`, zero failing checks, every required context reporting `SUCCESS`.

Both paths refuse unless the answer is yes. `--allow-unobserved` is the dangerous opt-out (a never-reporting required context blocks every PR, silently). There is **no** `--require-observed` flag — observed-only is simply the default.

### Six invariants (unchanged on amend)

1. `rules` is carried **verbatim** — never rebuilt from a schema-derived allowlist. REST emits `code_quality`, which is absent from the documented REST enum; an allowlist rebuild silently drops it.
2. Each **other** existing context keeps its **own** `integration_id`. Never rewrite them from a constant: `Bandit` is `57789` on five repos, not Actions' `15368`. Amend mutates exactly one entry.
3. `bypass_actors` carried verbatim (full-replacement; includes a `null` `actor_id` DeployKey row).
4. Snapshot to disk **before** the PUT, outside the repo (`~/.local/state/juniper-ruleset-snapshots/`), so rollback does not depend on the history API.
5. Re-read the live ruleset **immediately** before the PUT — concurrent sessions edit these.
6. Post-write re-read: rule count, rule-type set, bypass count, enforcement, ref include, `strict`, every prior context still present. `integration_id` drift fails **except** the one intended `(context, new_id)` pair on an amend. Two extra amend assertions: the new id must have **taken**, and the context **count** must be unchanged.

`find_ruleset` selects the ruleset that **carries** `required_status_checks` (by content, not by name). A failed per-ruleset GET is an error, never an absence (ml#1429). Two carrying rulesets is `AMBIGUOUS`.

### Roster

Default `--status` / no-`--repo` `--apply` walks `TARGETS` (nine repos, including `juniper-recurrence`). A repo missing here is silently absent from `--status` and reads as a complete census (ml#1403's class). `tests/test_require_context_safely.py` pins `TARGETS` to the census `ROSTER` in `util/ad-hoc/2026-08-26_p5_fleet_state.py`.

### Usage

```bash
# Census (never writes)
python3 util/ad-hoc/2026-08-20_require_context_safely.py --status

# Add: dry-run, then write (default context is Guard PR base branch)
python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-cascor --context 'Memory Budget'
python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-cascor --context 'Memory Budget' --apply

# Amend: re-pin an already-required context (juniper-ml#1612). Dry-run first.
python3 util/ad-hoc/2026-08-20_require_context_safely.py \
  --repo juniper-ml --context 'Memory Budget' --amend-integration-id
python3 util/ad-hoc/2026-08-20_require_context_safely.py \
  --repo juniper-ml --context 'Memory Budget' --amend-integration-id --apply

# Negative control: the Bandit app must refuse for Memory Budget
python3 util/ad-hoc/2026-08-20_require_context_safely.py \
  --repo juniper-ml --context 'Memory Budget' --amend-integration-id --integration-id 57789
```

`--integration-id` defaults to `15368` and is never `None`, so there is no "is the id explicit?" guard — the observed-publisher refusal is the real gate whether the id was typed or defaulted.

On a failed post-write verify the script prints the rollback:

```bash
gh api repos/<owner>/<repo>/rulesets/<id> -X PUT --input ~/.local/state/juniper-ruleset-snapshots/<snap>
```

### Operator pitfalls

| Symptom | What it actually is | What to do |
|---------|---------------------|------------|
| `ALREADY REQUIRED … — no-op` | Add path; the context is already on the ruleset | Use `--amend-integration-id` to change its `integration_id` (#1612). Do not hand-roll a PUT |
| `REFUSING: app N has not been observed publishing` | Amend pre-flight: that app does not publish this exact name here | Pass the id the publishers line named, or land the workflow first. `--allow-unobserved` only with a reason |
| `REFUSING: nothing in … recent check-runs publishes` | Add pre-flight: the name has never reported | Land the workflow and let it report once; a `pull_request`-only job reading `skipped` on `main` is still observed from PR heads |
| `ALREADY PINNED` | Amend no-op: current id already equals `--integration-id` | Nothing to do |
| PR `BLOCKED`, zero failing checks, every required context `SUCCESS` | A required context is pinned to an app that never reports it, or was required before anything published the name | Un-require or re-pin with this writer; then `update-branch`. This is the five-repo outage |
| `--require-observed` is unknown | Not a flag; observed-only is the default | Drop it |
| `--status` looks complete but a governed repo is missing | `TARGETS` omission; silent census | Confirm `juniper-recurrence` (and the other eight) appear; the unittest pins the roster |
| Post-write `integration_id DRIFT` on a neighbour | Invariant 2 failed — some other context's id moved | Rollback from the snapshot; do not re-run `--apply` to "fix" it |

Prefer this writer over `util/ad-hoc/2026-08-20_add_required_context.py`, which writes no snapshot, omits `integration_id` on the new context, and verifies contexts only.

Gate: `python3 -m unittest -v tests/test_require_context_safely.py` (`util/` is outside every pre-commit Python hook). Hermetic: `gh_json` is monkeypatched. Coverage includes `find_ruleset` error-vs-absence (ml#1429), roster lockstep, and (as of #1612) `observed_context_apps` — including two negative controls: a near-miss name (`Memory Budget (Python 3.12)`) must not count as a publisher, and `57789` must not appear for `Memory Budget`.

Related: [PR Base-Branch Guard](#pr-base-branch-guard) (the default context this writer was built to promote), [Memory File Size Budget](#memory-file-size-budget) (the #1611 pin), [CodeQL Analysis](#codeql-analysis) (soak-then-promote via the ruleset, never Quality Gate `needs:`).

---

## Sibling Packages

### juniper-observability

`juniper-observability` lives under `juniper-observability/` in this repository and publishes independently from the `juniper-ml` meta-package. Since `juniper-ml` 0.5.0 it is also aggregated under the `[tools]` and `[all]` extras, so a `pip install juniper-ml[all]` will pull it in alongside the rest of the platform.

Services that don't need the full meta-package can still depend on `juniper-observability` directly when they only want the shared health models, request-ID logging/middleware, Prometheus helpers, or Sentry setup.

| Field                 | Value                                                                      |
|-----------------------|----------------------------------------------------------------------------|
| **PyPI Name**         | `juniper-observability`                                                    |
| **Current Version**   | `0.4.0`                                                                    |
| **Python**            | `>=3.12`                                                                   |
| **Importable Module** | `juniper_observability`                                                    |
| **Package Docs**      | [`../juniper-observability/README.md`](../juniper-observability/README.md) |

Available extras:

| Extra        | Additional packages          |
|--------------|------------------------------|
| `prometheus` | `prometheus-client>=0.20.0`  |
| `sentry`     | `sentry-sdk[fastapi]>=2.0.0` |
| `all`        | Both optional groups         |

Publish and CI constraints:

1. `ci-observability.yml` runs package tests on Python 3.12 and 3.13, then builds and validates the distribution.
2. `publish-observability.yml` runs on `release: published` when the Release tag starts with `juniper-observability-v` (or on `workflow_dispatch`), builds from the subdirectory, publishes to TestPyPI, verifies installation, then publishes the same artifact to PyPI. It deliberately does **not** subscribe to `push: tags` — see [Independent Sibling Package Publish Pipelines](#independent-sibling-package-publish-pipelines).
3. The publish workflow uses OIDC trusted publishing, GitHub-hosted `ubuntu-latest` runners, and SHA-pinned actions. If the runner type or pinned artifact actions change, verify compatibility before cutting a Release.

### juniper-service-core

`juniper-service-core` lives under `juniper-service-core/` and publishes independently (`juniper-service-core-v*` → `.github/workflows/publish-service-core.yml`; CI: `ci-service-core.yml`). Since `juniper-ml` 0.5.0, it is aggregated under the `[tools]` and `[all]` extras. Model services inject lifecycle / command executors; this package owns the shared FastAPI + WebSocket + worker-pool plumbing.

| Field                 | Value                                                                    |
|-----------------------|--------------------------------------------------------------------------|
| **PyPI Name**         | `juniper-service-core`                                                   |
| **Current Version**   | `0.7.0`                                                                  |
| **Python**            | `>=3.12`                                                                 |
| **Importable Module** | `juniper_service_core`                                                   |
| **Meta pin**          | `juniper-service-core>=0.2.0,<0.8.0` under `[tools]` / `[all]`            |
| **Package Docs**      | [`../juniper-service-core/README.md`](../juniper-service-core/README.md) |

#### HTTP middleware contracts

- **CR-024 request body limit.** `RequestBodyLimitMiddleware` caps mutating bodies (default 10 MiB). `Content-Length` is an **early-reject hint only**: a declared length over the max returns 413 immediately and an unparseable one returns 400 `Invalid Content-Length header`, but `POST` / `PUT` / `PATCH` are then **always** stream-read with a cumulative cap, so an under-declared `Content-Length` or a chunked body with none still hits 413. The read body is cached on `request._body` for downstream handlers (BUG-CC-15). Skipping the stream when the declared length is present-and-small is the classic bypass — do not reintroduce it.
- **Auth before rate limit.** When API-key auth is enabled, `APIKeyAuth` runs before the rate limiter, so a 401 never consumes a token.
- **429 header passthrough.** `RateLimiter` raises `HTTPException` carrying `Retry-After` and the `X-RateLimit-*` headers; `SecurityMiddleware.dispatch` catches it and rebuilds `JSONResponse(..., headers=exc.headers)`. Dropping those headers makes well-behaved clients retry immediately, and `RateLimiter` unit tests alone do not exercise the catch path.
- **Exempt paths.** `EXEMPT_PATHS` covers `/v1/health`, `/v1/health/live`, `/v1/health/ready`, `/docs`, `/openapi.json`, `/redoc`, and both literal `/metrics` forms (gated instead by the parallel `MetricsAuthMiddleware` allowlist). WebSocket upgrades are not intercepted by `BaseHTTPMiddleware`, so `/ws/*` is inherently outside this path.
- **Blank API keys.** `APIKeyAuth` filters blank / whitespace-only configured keys (the `auth_posture.real_keys` rule), so an empty secret file cannot enable auth that would then accept an empty `X-API-Key`.
- **Rate-limit keying.** `RateLimiter._get_key` buckets by `key:<api_key>` when the request is authenticated, otherwise by `ip:<client.host>` — falling back to `ip:unknown` when Starlette reports no client. Authenticated callers therefore get their own budget rather than sharing one per source IP (and a shared NAT egress cannot exhaust an authenticated client's budget).
- **Worker mTLS half-config.** `TLSConfig` (`juniper_service_core.workers.security`) fails closed: with TLS enabled and only one of `cert_file` / `key_file` set, it raises `ValueError` naming both paths, rather than returning a bare `SSLContext` with neither chain nor key. A silent half-config is the dangerous shape — it looks "TLS enabled" to callers while presenting nothing.

#### Control WS log sanitizer

`/ws/control` logs reject untrusted client text (Origin headers, command names). Both modules keep those records **single-line** so CRLF or control characters cannot forge multi-line control-plane logs:

| Module | Helper | Strip rule | Call sites |
|--------|--------|------------|------------|
| `juniper_service_core.websocket.control_security` | `_sanitize_for_log(str)` | Removes `\r` and `\n` | The allowlist-reject INFO (`origin %r not in allowlist`) |
| `juniper_service_core.websocket.control_stream` | `_sanitize_for_log(object)` | Removes `\r` / `\n`, then other C0 controls except tab; `str()` of non-strings | Command timeout / reject / unexpected-failure logs (`safe_command`) |

Sanitizing flattens log *records* only — it does not change handshake outcomes, close codes, or the `command` echoed in acks, and payload text stays visible after flattening. Do not log raw `Origin` / `command` strings outside these helpers when adding a reject path. A missing Origin is fail-closed (rejected with no sanitize path, since there is no client text to log).

#### Control WS rate limiting (`ws_control_rate_limit_per_sec`)

Control-plane WebSockets build a per-connection `LeakyBucket` from `ws_control_rate_limit_per_sec` (default `10`); a denied command acks `rate_limited` with `data.retry_after` from `LeakyBucket.retry_after`.

| Setting | Effect |
|---------|--------|
| `> 0` (default) | Normal refill; `retry_after` is roughly the seconds until one token |
| `= 0` | No refill — `retry_after` returns `3600.0` (hard backoff) rather than dividing by zero and tearing down the receive loop |

A client seeing a very large `retry_after` on a zero limit is the expected hard-backoff path; raise the setting if you want faster refill.

Repeated *rejected handshakes* are throttled separately by `HandshakeCooldown`, which tracks rejections per client IP: more than `max_rejections` (default **10**) within `window_sec` (default **60**) blocks that IP for `block_sec` (default **300**, i.e. 5 minutes) and closes further attempts with **4029** `Too many rejected handshakes`. The state is in memory only, so a server restart clears it — a deliberate NAT-hostile escape hatch, since many clients can share a single egress IP.

#### `/ws/workers` contracts

The handshake runs **Origin → auth → per-source rate limit → accept → registration → message loop**, so four of the five close codes fire *before* `accept()`:

| Order | Condition | Close | Reason string |
|-------|-----------|-------|---------------|
| 1 | Any `Origin` header present | **4003** | `Origin header not allowed on worker endpoint` — workers are not browsers, so any Origin is a browser/CSRF shape |
| 2 | `ws_authenticate` fails (bad or missing `X-API-Key` while `app.state.api_key_auth` is enabled) | **4001** | `Authentication required` |
| 3 | Optional `worker_rate_limiter` denies the source IP | **4029** | `Rate limited` |
| 4 | `worker_coordinator` or `worker_registry` missing | **4004** | `Worker system not initialized` — the pool never came up; not a client fault |
| 5 | *(after accept)* registration shape invalid | **4008** | `Invalid registration` |

- **Auth fail-closed.** The socket is never accepted on an auth failure — the close happens before `accept()`, so a client that sees a connection "open" has already passed auth.
- **Registration shape.** After accept, registration requires a pattern-valid string `worker_id` and a dict `capabilities`; a non-object frame or a shape failure closes **4008** with no `registration_ack` (distinct from the malformed-JSON close). The client-supplied id is display-only — the server assigns `worker-{uuid12}`.
- **Result ownership.** `WorkerCoordinator.submit_result` rejects wrong-worker / unassigned results before the protocol parse.
- **Binary frame cap.** Attachments over `_MAX_BINARY_SIZE` (100 MB) get `Binary frame too large` before `submit_result`.
- **Unknown lifecycle frames.** `build_frame_sink` maps unknown or missing frame types onto the generic `event` envelope rather than dropping or raising.

Control receives rejects malformed/non-object JSON with close **1003** rather than an `AttributeError`.

| Symptom | Check / Fix |
|---------|-------------|
| HTTP 429 arrives without `Retry-After` | `SecurityMiddleware` must pass `exc.headers` into the `JSONResponse` — RateLimiter unit tests alone do not cover that catch path. |
| A health probe gets 429 | Health/docs/metrics are exempt in service-core — check an upstream proxy or a non-exempt path. |
| A large POST is accepted despite the body limit | The mutating-method stream cap must be unconditional; a `Content-Length`-only fast path is the bypass class. |
| Multi-line or forged log record after a bad Origin/command | `_sanitize_for_log` regression — never interpolate unsanitized Origin/command into logger format strings. |
| Worker WS closes 4001 before `connection_established` | API-key auth is enabled — send `X-API-Key`, or disable `app.state.api_key_auth` locally. |
| Worker WS closes 4008 after accept | Fix the registration shape: string `worker_id` plus dict `capabilities`. |
| Worker WS closes 4003 immediately | The client sent an `Origin` header — workers are not browsers; drop it from the client's WS options. |
| Worker WS closes 4029 before accept | `HandshakeCooldown` or the per-source worker rate limiter is throttling that IP; back off, or restart the server to clear the in-memory block. |
| Worker WS closes 4004 | Server-side: `worker_coordinator` / `worker_registry` never initialized — check the service's worker-pool startup, not the client. |
| Worker TLS "enabled" but presents no chain | Half-config — `TLSConfig` raises `ValueError` when only one of `cert_file` / `key_file` is set; supply both. |
| One noisy IP throttles authenticated clients | Expected only for unauthenticated traffic — `RateLimiter` keys authenticated requests as `key:<api_key>`, so confirm the caller is actually sending `X-API-Key`. |
| Two `task_assign` frames while the first task runs | A mid-task heartbeat must ack without dispatching — confirm the idle guard. |

---

## Version History

| Version | Date       | Changes                                                                                                                                                                  |
|---------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0.6.49  | 2026-09-04 | PF scenario suites (Wave 7.3): operator surface for the six `util/experiments/suites/perf/` instruments — PF-1 matched epoch pair + matrix-axis repeats + scrapeability, `scrape_confirmed` vs `target_file_written`, PF-3 stall/wall, PF-4/PF-8 not driver suites |
| 0.6.50  | 2026-09-05 | Topology step order + blast-radius IDs: `topostate` first or alone (M-TOPOLOGY-18 INDETERMINATE is a harness artifact); `W4-01..17` / `W1-12..14` **are** matrix §4 steps — F-E2E-007 claimed otherwise and was withdrawn; triage `pri_of` takes the first severity token in the header |
| 0.6.51  | 2026-09-04 | P4 campaign suites: 19 YAML catalog; `include` does not inherit `matrix`; oversize stall is pool ≥ 16 **or** cap ≥ 64; timeout must sit **above** the driver wall; cap-128 H2H is n=2 (description still says 3); recurrence P4 cells report, they do not gate |
| 0.6.52  | 2026-09-04 | Perf-lane work gate: reader / `make_baseline` / `compare_baseline` operator surface. `step_count` is exact as a measurement; it is **not** established as deterministic. Do not wire the exact-match work gate to CI (juniper-ml#1710). Writer-vs-comparator asymmetry + six source-verified comparator defects. |
| 0.6.53  | 2026-09-04 | Memory-budget slack (planning): headroom is `ceiling - chars` and is not a CI input; `measure-growth` prints median / nearest-rank p90 / max and has no required-slack field; size slack as `max(largest 30-day growing commit, 2000)`; `--ratchet` after a cut leaves zero headroom |
| 0.6.54  | 2026-09-04 | Equities symbol cap: default universe is refused at **14 symbols** (422 until opt-in); unit is symbols because cost is per request; silent slice deleted in data#354; `equities_seq` inherits |
| 0.6.55  | 2026-09-04 | F-039 store probe: apply / soak / report / revert for the server-side TOPOPROBE; read the whole series; `--target topology` refuses on current canopy; backup lives in the git dir |
| 0.6.56  | 2026-09-04 | Conda env torch shadow diagnostic: `util/check_conda_env_torch.bash` exit **2** is P-5 free-threaded, exit **4** is the May-7 regular-3.14 wheel-layout class; do not rebuild from the wrong code |
| 0.6.57  | 2026-09-05 | MEMORY.md index check: local `util/memory_index_check.py` runbook — hard cap 200/25000 (silent newest-first), hook-not-line 120 on NEW slugs only, fail-closed missing file, `--accept` always exits 0 |
| 0.6.59  | 2026-09-05 | Perf-lane work gate, post-`ml#1743`: determinism **settled** — `step_count` is exact *within a termination branch* (census: 333 runs, 29 of 79 repeated configs diverge, all explained by `completion_reason`), and `ml#1733` made the branch a precondition so a flip REFUSES. Writer-vs-comparator asymmetry and all six defects (A1-A4/A6/A7) **closed**; exit 1 is interpretable; FAIL outranks REFUSED. CI-wiring prohibition **re-grounded**: an owner decision (P1 §6), not a soundness bar. |
| 0.6.58  | 2026-09-05 | Juniper project-tree backup: `util/juniper-backup.bash` per-repo `.tbz2.gpg` (bzip2, restore `-xjf`), build-once / copy ciphertext, `--dry-run` must not write, unattended verify is `--list-packets` only, `EXCLUDE_CASCOR_SNAPSHOTS` TRUE is `0` |
| 0.6.47  | 2026-09-04 | Pointer-follow soak operator surface: do not run n≈8–10 (P21/P23 at 1/3 first resolve at 10/31); `--force` is an open owner decision; `--dry-run` is gated by the terminal verdict on this tree (+3 non-follows from 26/40 arms it); full probe slugs; `--outcome miss` needs `--class`; `analyse()` has no era filter |
| 0.6.48  | 2026-09-04 | Pointer-follow soak operator surface: `--dry-run` is exempt from the terminal-verdict stop (juniper-ml#1690); do not drive n≈8–10; era split required; `source-recovered` stays in the denominator; soak-probes reaper pidfile |
| 0.6.60  | 2026-09-05 | Canopy E2E unfilled-rows ledger: plan re-drives from `e2e_unfilled_rows.py` (matrix status cells only; `C2.` / `M-`; exit 0). `e2e_row_coverage.py` is an estimator and can list already-`PASS` rows as remaining |
| 0.6.61  | 2026-09-05 | Perf-lane work gate: `step_count` is exact **within a termination branch** (juniper-ml#1733 census: 29 of 79 repeated-config divergences, 0 within a branch). Branch flip / truncating / absent `completion_reason` REFUSE; same-branch move still FAILS. Do not CI-wire — unmeasured-drop and fingerprint-collapse remain. Supersedes the in-flight #1715 "FAIL is uninterpretable" page. |
| 0.6.22  | 2026-09-04 | X7 off-loop census: the count is **58** (canopy#567); the gate is authority for `main.py` only and the call-graph instrument covers the rest; v1 is the name-matching negative example; module-global expression exemptions certify a partial fix |
| 0.6.59  | 2026-09-05 | Ruleset Context Audit: read-only fleet classifier for `required_status_checks` (`2026-08-10_ruleset_context_audit.py`); BLOCKING vs Tier 1 vs path-gated; advisory_predicate subtracts the live required set; text-mode 0 can still carry `ERROR:` rows |
| 0.6.16  | 2026-09-04 | Required-context ruleset writer: add vs `--amend-integration-id` (#1612), observed-publisher pre-flight, six invariants, `Memory Budget` unpinned-id hole (#1611) |
| 0.6.17  | 2026-09-04 | Perf-lane reader / baseline operator surface: split work (`step_count` exact) vs speed (reported); de-ratified `wall_seconds`/`timings.drive`; last-row histogram; scrape tri-state; `make_baseline` refusals (no `--force`); #1613 workload fingerprint vs `config_sha256` and fail-on-mismatch behind identity |
| 0.6.18  | 2026-09-04 | Pointer-follow soak operator surface: seeded vs organic, characterisation vs least-covered, `source-recovered` denominator, retrieval-channel / `parse_events` pitfalls (#1616) |
| 0.6.19  | 2026-09-04 | Dual unittest entry-point trap (#1612 synchronize): `python3 tests/<file>.py` misses `TestCase` classes below `__main__`; CI's `-m unittest` does not. Keep `__main__` at EOF |
| 0.6.21  | 2026-09-04 | Ruleset Scope Guard operator surface: `~ALL` re-arms deleted dependabot/Copilot bypass rows; token-free GET-only (bypass rows NOT checked); exit 0/1/2 fail-closed; Quality Gate hard need |
| 0.6.23  | 2026-09-04 | Canopy E2E matrix writes: fill is dry-run / header-located; set-verdicts has no dry-run and is atomic `--from`; rescore writes found rows even when some `--row` ids are missing. Do not plan from `e2e_row_coverage.py`. Skipped 0.6.16–0.6.22 (in-flight docs PRs) |
| 0.6.27  | 2026-09-04 | F-CANOPY-027 poller starvation probes: 12-slot dash-renderer cap, queued-vs-unwired, no-new-poller rule; finding FIXED canopy#507/#509/#511 |
| 0.6.30  | 2026-09-04 | F-CANOPY-037 render census: 11-session instrument; structured `topodiag` JSON only; exit 2 = failed to measure; `hidden_units` 0/absent is INVALID not idle; walk-up root needs both sibling repos. Skipped 0.6.16–0.6.29 (in-flight docs PRs) |
| 0.6.32  | 2026-09-04 | Pointer-follow soak operator surface: least-covered vs characterisation, `--force` before `--dry-run` on terminal verdicts, `source-recovered` denominator, retrieval channel searches tool inputs **and** answer text, soak-probes reaper pidfile |
| 0.6.33  | 2026-09-04 | X7 off-loop census: shipped count is **58** (52 direct + 2 `HELPER` + 4 outside `main.py`); C5 `threading.local()` remedy refuted (T-A4); callgraph guards the adapter; v1 remains the name-matching negative example |
| 0.6.34  | 2026-09-04 | Experiment run lister / pruner (`list_runs.py`): directory-truth scan, `down`/`up?`/`stale`, `--prune` ≠ `--down`, `--run-root` ignores `JUNIPER_EXP_RUN_ROOT` |
| 0.6.35  | 2026-09-04 | Train / val / test partition contract: shipped NPZ still requires `*_full`; design drops it (decision 11) but required-fix 0 has not started; `RECURRENCE_SPLITS` still refuses `validation` |
| 0.6.36  | 2026-09-04 | Equities symbol-cap operator surface (`APD-DATA-018` equities half): per-request cost, silent `max_symbols` slice at `generator.py:286`, default 503-ticker universe is ~67× over the 30 s budget |
| 0.6.37  | 2026-09-04 | Canopy E2E topology driver: `STEPS` is the authority; M-06/M-07/M-12 on `main` can PASS the easier half of an `OR` / display-only / empty-space gesture |
| 0.6.38  | 2026-09-04 | Canopy E2E topology driver after #1672: M-06/M-07 are AND predicates; M-12 scores Clear selection; second-instance `2026-09-04_canopy_verify_instance.bash` is on `main`. Supersedes the 0.6.37 draft in #1674 |
| 0.6.40  | 2026-09-04 | Suite driver operator surface: `run_suite.py` expansion / resume / `--only` exit, cascor parallel floor, Grafana env toggle, Q-2 flag forwarding. Distinct from gate-input docs #1649 |
| 0.6.43  | 2026-09-04 | Canopy E2E dataset drivers: W6 (`--steps`, no ranges, stops before restart-confirm wipe) vs §3.6 (`--step`); `JUNIPER_E2E_CANOPY_URL` is the target, not `JUNIPER_E2E_CANOPY_PORT` |
| 0.6.45  | 2026-09-04 | Recurrence work is not countable (#1683): kind detection from `timings.train`, `work_countable` third state, `make_baseline` / `compare_baseline` refuse rather than mis-gate PF-5/6/7 |
| 0.6.44  | 2026-09-04 | Cascor Primary Freeze Tell: `cascor_freeze_tell.py` exact-prefix hold test (not substring); sibling client/worker and both worktree roots excluded; exit 0 is "no user-owned importer", never "no importer" |
| 0.6.46  | 2026-09-04 | Experiment stats summary (SS8.3): how to read `stats.json` / `summary.md` — de-ratified `wall_seconds`, per-poll step-duration honesty, `scrape_confirmed` tri-state, recurrence timings under `outcome.timings` |
| 0.6.19  | 2026-09-04 | Perf-lane split comparator (`compare_baseline.py`, #1622): identity first, work exact / speed reported, exit 0/1/2, waiver cannot mask a refusal, host block vs advisory |
| 0.6.11  | 2026-08-24 | Claude Code Action operator surface: live `claude.yml` triggers / exact permissions / SHA pin, ungrouped Dependabot bumps, template-snapshot drift, not the local `claudey` launcher |
| 0.6.12  | 2026-08-24 | Publish #1310 operator surface: Gate 1 provenance is a 10×6s TestPyPI poll (not `sleep 30`); sibling `push:`-gated Release steps were unreachable — the trigger is the gate. Also carries the Snapshot Attribution Dataset Pin operator section (juniper-ml#1341), which landed in this version — its own row lost the merge race |
| 0.6.41  | 2026-09-04 | Resident-hazard gap triage: three complementary scanners, block scoring, `--self-check`, and why the candidate count grows after a successful cut |
| 0.6.24  | 2026-09-04 | Worktree in-use probe: cwd-only liveness is not enough (open fd is STRONG); WEAK cmdline must not set the exit code (self/parent argv); sibling prefix; empty argv exits 2 |
| 0.6.28  | 2026-09-04 | Suite report gate inputs (P2 1.4 / #1643): `aggregate.csv` carries `step_count` + `mean_step_seconds` beside de-ratified `wall_seconds`; `REPORT.md` **Gate inputs** + reporting-only `--compare-baseline` (FAIL does not change suite exit). Skipped 0.6.16–0.6.27 (in-flight sibling docs PRs) |
| 0.6.29  | 2026-09-04 | CSV import byte cap (APD-DATA-018 csv_import half, juniper-data#326): 128 MiB, 422 until opt-in, read-enforced bound; experiment-stack `IMPORT_DIR` pitfall; equities `max_symbols` still silent |
| 0.6.31  | 2026-09-04 | Defect-register close protocol: `register_open_set.py` is the §4 counter (cwd-relative; `**FIXED` only); `register_status_crosscheck.py` is the independent third reading. `grep` + open-set can agree and both be wrong |
| 0.6.39  | 2026-09-04 | Snapshot sidecar chain operator surface: index / classify / backfill commands, two-axis scheme, derivation levels, `--root` vs `JUNIPER_CASCOR_SNAPSHOTS_DIR` |
| 0.6.40  | 2026-09-04 | Suite driver operator surface (`util/experiments/run_suite.py`): expansion / resume / cascor parallel floor / `JUNIPER_EXP_PROJECT_DIR` rebase / Grafana env toggle |
| 0.6.15   | 2026-08-24 | Scheduled Duplicati backup lane (#1292): `systemd --user` timer, copy-not-symlink installer, fail-closed dest/tmpfs/passphrase guards, skip-escalation, `--no-auto-compact` |
| 0.6.20  | 2026-09-04 | Sequence Safety is a **required** `juniper-ml-rules` context (live GET 2026-09-04), not advisory: Quality Gate green does not mean mergeable. Labels green the PR check only; trailers cover `main-verify`. QG `needs:` also lists `ruleset-scope-guard` + `sops-validation`. |
| 0.6.1   | 2026-08-05 | Experiment Stack: `do_up` partial-failure → `teardown_run` + F-6 pidfile-refuse → kill-by-port operator guidance (code on main; refuse coverage open juniper-ml#923)       |
| 0.6.0   | 2026-05-23 | Floor-bumped `[clients]` / `[worker]` / `[servers]` extras to today's ecosystem release wave (cascor/canopy 0.5.0, cascor-client/cascor-worker 0.4.0, data-client 0.4.1) |
| 0.5.0   | 2026-05-21 | Added `[servers]` and `[tools]` extras; expanded `[all]` to install every Juniper package                                                                                |
| 0.4.1   | 2026-04-28 | Added `juniper-observability` sibling package and dedicated CI/publish workflows                                                                                         |
| 0.4.0   | 2026-04-09 | Added service orchestration utilities, worktree cleanup tooling, and updated package pins                                                                                |
| 0.2.0   | 2026-02-27 | Added CLAUDE.md, raised Python to >=3.12, renamed from "juniper"                                                                                                         |
| 0.1.0   | 2026-02-22 | Initial release with TestPyPI + PyPI publishing                                                                                                                          |

---

## Build and Release

### Build

```bash
python -m build
```

### Meta-Package Publish Pipeline

The `.github/workflows/publish.yml` workflow publishes the `juniper-ml` meta-package. It runs when a GitHub Release is published and also supports manual `workflow_dispatch` reruns against a tag:

```bash
gh workflow run publish.yml --repo pcalnon/juniper-ml --ref <tag>
```

Release flow:

1. **Build and Validate** -- checks out the tag, installs `build` and `twine`, runs `python -m build`, validates with `twine check dist/*`, and uploads the `dist/` artifact.
2. **Publish to TestPyPI** -- downloads the artifact, publishes to TestPyPI with OIDC trusted publishing, and enables PyPI attestations.
3. **Verify TestPyPI Install (Gate 1)** -- reads `[project].version`, then **polls** TestPyPI for the just-uploaded wheel (10 attempts × 6s, ~60s ceiling — not an unconditional `sleep 30`; juniper-ml#1310), then verifies in **two phases**.
   2026-08-08 amendment: pip has **no index priority**, so a merged `--index-url` + `--extra-index-url` namespace resolves to the highest version across *both* indexes and lets a TestPyPI squatter outrank the real package — TestPyPI `fastapi 1.0` beat production `fastapi 0.141.1` and killed the v0.7.0 verify, run 31281873275:
   1. **Provenance** -- `pip download --no-deps --index-url https://test.pypi.org/simple/ --dest <tmp> "juniper-ml==${VERSION}"` inside the poll loop. The artifact comes from TestPyPI and **only** TestPyPI, at the exact built version; a missing `juniper_ml-${VERSION}-py3-none-any.whl` fails the step rather than handing pip a bogus path. The fetch stays on **one line and outside any `if`** — `tests/test_publish_testpypi_verify.py` matches `^pip download` against the stripped line.
   2. **Resolution** -- **three** installs of that local wheel in order, each `--index-url https://pypi.org/simple/` (production PyPI **only**, no `--extra-index-url`) and **never** `--no-deps`, so extras resolution is still genuinely exercised:
      1. bare `"${WHEEL}"` → `importlib.metadata` version check
      2. `"${WHEEL}[clients]"` → imports `juniper_data_client`, `juniper_cascor_client`
      3. `"${WHEEL}[tools]"` → imports `juniper_ci_tools`, `juniper_doc_tools`, `juniper_observability`

   Light extras only — do **not** add `[worker]` / `[servers]` / `[all]` / `[recurrence]` here (torch, multi-GB). A broken extras declaration that a bare install alone would miss fails at this gate, before production PyPI.
4. **Publish to PyPI** (`needs: testpypi`) -- runs only after Gate 1 succeeds and publishes the same artifact with OIDC trusted publishing and attestations enabled.

**Tag guard:** the `build` job runs only for `workflow_dispatch` or a Release whose tag starts with `v`, so a shared-package Release (`juniper-<pkg>-v*`) cannot fire the meta publisher. Always-on gate for the two-phase verify (including the anti-regression check that no verify command may carry `--extra-index-url` or name both index URLs), the bounded poll, the tag guard, and `pypi needs: testpypi`: `tests/test_publish_testpypi_verify.py`.

**Upload strictness:** the TestPyPI upload sets `skip-existing: true` so re-cutting a Release for a version TestPyPI already holds is a no-op rather than an immutable-upload 400; the production PyPI upload deliberately stays strict.

**Index-lag poll (juniper-ml#1310).** TestPyPI's simple index is CDN-fronted, and lags uploads by ~5–30s, so the first fetch of a just-published version can return a 404.
The previous unconditional `sleep 30` was 77% of a measured 39s step, paid in full on **every** publish, even when the index was already warm, and still a coin flip if propagation ran long.
The poll returns as soon as the artifact is servable (usually the first attempt) and fails with `::error::TestPyPI never served juniper-ml==${VERSION} within ~60s of upload` if the ceiling is hit. Do not restore `sleep 30`.

**The trigger is the gate (juniper-ml#1310).** Every publisher is `release: published` + `workflow_dispatch` only. A bare `git push <tag>` starts **no run** — nothing is built, nothing is uploaded.
The six sub-package publishers used to carry a `Require a GitHub Release for this tag` step gated on `if: github.event_name == 'push'`; none of them subscribe to `push:` (removed after #555), so those steps could never run.
Dead code shaped like a guard is worse than no guard: it reads as though a tag push is blocked here.
Gate: `tests/test_publish_release_only_trigger.py` (glob-discovered; pins both directions — re-adding `push:` recreates the #555 race, removing `release:` disarms publishing silently).
Re-measured 2026-08-24: 12 tags exist with no Release and none of them published.

### Independent Sibling Package Publish Pipelines

The six in-repo shared packages each ship via their own `publish-<pkg>.yml`, intentionally decoupled from the meta-package Release. Cut a GitHub Release whose tag matches the package prefix (never a bare `git push <tag>`):

| Package                 | Release tag prefix          | Workflow                                      | Build Directory          |
|-------------------------|-----------------------------|-----------------------------------------------|--------------------------|
| `juniper-ml` (meta)     | `v*`                        | `.github/workflows/publish.yml`               | repository root          |
| `juniper-ci-tools`      | `juniper-ci-tools-v*`       | `.github/workflows/publish-ci-tools.yml`      | `juniper-ci-tools/`      |
| `juniper-config-tools`  | `juniper-config-tools-v*`   | `.github/workflows/publish-config-tools.yml`  | `juniper-config-tools/`  |
| `juniper-doc-tools`     | `juniper-doc-tools-v*`      | `.github/workflows/publish-doc-tools.yml`     | `juniper-doc-tools/`     |
| `juniper-model-core`    | `juniper-model-core-v*`     | `.github/workflows/publish-model-core.yml`    | `juniper-model-core/`    |
| `juniper-observability` | `juniper-observability-v*`  | `.github/workflows/publish-observability.yml` | `juniper-observability/` |
| `juniper-service-core`  | `juniper-service-core-v*`   | `.github/workflows/publish-service-core.yml`  | `juniper-service-core/`  |

Contracts every one of them shares:

| Contract | Why it matters |
|----------|----------------|
| **Release-only trigger** (`release: published` + `workflow_dispatch`; **no** `push: tags`) | Cutting a Release also creates the tag. Subscribing to both raced the immutable TestPyPI upload (#555). The trigger **is** the gate: a bare `git push <tag>` starts no run. Do not resurrect a push-gated Release step (#1310). Gate: `tests/test_publish_release_only_trigger.py`. |
| **Build-job tag-prefix guard** | `release: published` fires *every* `publish-*.yml`, so each build job gates on `startsWith(github.event.release.tag_name, '<pkg>-v')` to keep package A's Release from publishing package B. |
| **`--no-deps` TestPyPI-only verify** | With `--no-deps`, no dependencies are fetched, so adding an `--extra-index-url` to production PyPI would only risk resolving a squatted *target* package during TestPyPI index lag. Sibling verify must not add a PyPI fallback. Index lag is a 5×10s retry around `pip install` (~50s), distinct from the meta publisher's 10×6s `pip download` poll (~60s). |
| **`skip-existing: true`** on both publish steps | Residual overlap (a manual dispatch during a Release) is a no-op instead of an immutable-upload 400. |
| **OIDC + concurrency** | `permissions: {id-token: write, contents: read}`; `concurrency.group: publish-<suffix>-${{ github.ref_name }}` with `cancel-in-progress: false`; environments `testpypi` then `pypi`. |

Retry a stuck publish without re-cutting a Release:

```bash
gh workflow run publish-ci-tools.yml --repo pcalnon/juniper-ml --ref juniper-ci-tools-vX.Y.Z
```

Sibling package release flow:

1. **Build and Validate** -- the build job sets `defaults.run.working-directory` to the package subdirectory (so every step is subdir-relative without repeating the path), runs `python -m build --sdist --wheel`, validates with `twine check dist/*`, and uploads that subdirectory's `dist/` artifact with `if-no-files-found: error` so a silently empty build fails here instead of surfacing as a confusing publish-step error.
2. **Publish to TestPyPI** -- downloads the artifact into `dist/`, publishes with `packages-dir: dist/`, `repository-url: https://test.pypi.org/legacy/`, and `verbose: true` so trusted-publisher or upload errors include the server response body.
3. **Verify TestPyPI Install** -- sparse-checks out the package `pyproject.toml`, reads the package version, retries `pip install --no-deps --index-url https://test.pypi.org/simple/` up to five times with a 10s interval (~50s ceiling) to tolerate index lag, then confirms the installed version (`import` of the package, or `importlib.metadata` when `--no-deps` would leave an import broken).
4. **Publish to PyPI** -- runs only after TestPyPI install verification and publishes the same artifact with `packages-dir: dist/` and `verbose: true`.

These publish workflows require GitHub Actions environments named `testpypi` and `pypi`, plus matching trusted-publisher entries on TestPyPI and PyPI for the workflow file, environment, owner, repository, and project name.

Release runbooks:

- [`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) — cut a GitHub Release and archive `notes/releases/` (mandatory for every PyPI deploy; never a bare `git push <tag>`).
- [`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) — daily release-train modes (`off`/`report`/`propose`/`ceremony`), Gate 1 proposal review, Gate 2 `pypi` approval, HALTs, and App-token setup. Workflow: `.github/workflows/release-train.yml`; engines: `util/release_train/{detect,propose,ceremony}.py`.
- [`notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`](../notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md) covers the expanded extras surface and the TestPyPI extras-resolution verify step.
- [`notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md`](../notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md) remains the canonical source for the trusted-publisher prerequisite and pending-publisher gotchas.

---

## Flood-Remediation CI Gates

Operator surface for the flood-remediation CI layers landed in [#869](https://github.com/pcalnon/juniper-ml/pull/869) / [#880](https://github.com/pcalnon/juniper-ml/pull/880) (Proposal P2 / flood analysis §4 items 1–2 + 8 phases 2–4). These jobs catch **serial same-file damage** that per-PR green checks miss. The CLIs they invoke are the `juniper-ci-tools` console scripts (`juniper-symbol-loss-check` / `juniper-docs-additions-check` — install with `pip install "juniper-ci-tools>=0.8.0,<0.9.0"`; the inline `util/sequence_safety/` copy was retired in ml#1024); predicted-merge triage for open fleet PRs is `util/fleet_triage/predict_merge.py` (see AGENTS.md Key Files).

Design context: [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md).

### Workflow map

| Surface | Workflow / job | When | Gate role |
|---------|----------------|------|-----------|
| G4 pre-commit split | `ci.yml` → `pre-commit` | every CI event | **Required** (Quality Gate) |
| Per-PR sequence-safety | `ci.yml` → `sequence-safety` | `pull_request` + `merge_group` only | **Required** in the branch ruleset (`Sequence Safety`); **absent** from Quality Gate `needs:` |
| Fleet PR lint | `ci.yml` → `fleet-pr-lint` | `pull_request` whose head starts with `cursor/` | **Advisory** (never fails, never comments) |
| Post-merge net | `main-verify.yml` | every `push:main` + dispatch | **Bypass-proof** (owner/Cursor App cannot skip by merging green) |

Quality Gate (`required-checks`) needs exactly the following: `pre-commit`, `tests`, `build`, `docs`, `security`, `claude-yaml-audit`, `ruleset-scope-guard`, `dependency-docs`, `sops-validation`. Folding `sequence-safety` / `fleet-pr-lint` / `release-train-archive-guard` into that `needs:` would fail every `push:main` (those jobs skip on push while the gate is `if: always()`). The Quality Gate can therefore be green while Sequence Safety is red — that does **not** mean the PR is mergeable.

#### Security soft-fail

`security` is the only need with a **soft-fail** predicate. Every other need is checked with `!= "success"`, so a skip is fatal; `security` is checked with `== "failure"`, so a skip stays green:

| Job result | Hard needs (`pre-commit`, `tests`, …) | `security` |
|------------|---------------------------------------|------------|
| `success`  | pass | pass |
| `failure`  | gate fails | gate fails |
| `skipped`  | gate fails | **pass** |

The workflow comment is explicit (`# Security: failure = error, skipped = OK`). Do **not** rewrite the security arm to `!= "success"` — that turns an intentional skip into a red Quality Gate. Hermetic YAML-extraction rehearsal: `tests/test_ci_quality_gate.py`.

### Concurrency and merge queue (#869)

| Workflow | Concurrency group | Cancel in progress |
|----------|-------------------|--------------------|
| `ci.yml` | `ci-${{ sha }}` on **push**; `ci-${{ ref }}` otherwise | `false` on push; `true` otherwise |
| `main-verify.yml` | `main-verify-${{ sha }}` | **always `false`** |

Rapid serial merges on `main` must each complete their own `ci` / `main-verify` run — a ref-keyed cancel group would drop every merge except the last.

`ci.yml` **and** `codeql.yml` listen on `merge_group` so required contexts (`Quality Gate` jobs **and** `Analyze (python)`) re-post on the queued merge commit (merge-queue ruleset prerequisite). Without either trigger the queue stalls with no required check. The CodeQL `merge_group` listen is an accepted juniper-ml-only divergence — see [CodeQL Analysis](#codeql-analysis).

### G4 — pre-commit changed-files split (#880 phase 2)

```text
pull_request / merge_group  →  pre-commit run --from-ref <BASE> --to-ref HEAD
push (incl. main)           →  pre-commit run --all-files
```

BASE is `github.event.pull_request.base.sha` or `github.event.merge_group.base_sha`. Checkout uses `fetch-depth: 0` so BASE is present.

Constraints (from the workflow comments / Proposal P2 §4):

- Hooks with `pass_filenames: false` (e.g. the local `juniper-check-doc-links` hook) still run **globally** under `--from-ref`.
- Changed-files scope is blind to a union effect in a file the PR did **not** touch; `--all-files` on push is the union check at land time.

### Per-PR Sequence Safety (#880 phase 3)

Runs `juniper-symbol-loss-check` then `juniper-docs-additions-check` (juniper-ci-tools console scripts) over `<BASE>..HEAD`, uploads `sequence-safety-report` (`symbol-report.json` + `docs-report.json`, 30-day retention).

**Required in the branch ruleset; absent from Quality Gate `needs:`.** Live `juniper-ml-rules` `required_status_checks` (GET 2026-09-04) includes the context `Sequence Safety`. A red Sequence Safety check **blocks merge** even when Quality Gate is green. The job stays out of `required-checks.needs` because it skips on `push:main` while that gate is `if: always()` — folding it in would fail every push. Promotion already landed (2026-08-18); do not add it to Quality Gate `needs:`.

The `ci.yml` job banner still says "ADVISORY" (soak-convention wording from before the ruleset promotion). Believe the ruleset, not the banner. `Fleet PR Lint` is the one that is still truly advisory (always `exit 0`, not a ruleset context).

| Lever | Effect |
|-------|--------|
| PR label `allow-symbol-loss` / `docs-rewrite` | Adds `--advisory` for that screen only → WARN findings, exit 0. That **does** green the required PR context. Read live via `gh pr view` (re-run job; no re-push). Invisible to `main-verify`. |
| Commit trailer `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` | Primary, auditable waiver inside the modules; travels in history → also covers post-merge `main-verify`. |
| `merge_group` event | No PR object → **strict** (label hatch unavailable). |

Local repro:

```bash
juniper-symbol-loss-check --base origin/main --head HEAD --json
juniper-docs-additions-check --base origin/main --head HEAD --json
# WARN-only (label-hatch equivalent); exit 2 is never masked:
juniper-symbol-loss-check --base origin/main --head HEAD --advisory
```

### Fleet PR Lint (#880 phase 4)

`cursor/*` head branches only (`pull_request` + `startsWith(github.head_ref, 'cursor/')`), `contents: read` only. Every signal goes to the job step summary, and the shell ends with `exit 0` under `set +e`, so a probe failure cannot paint the check red.

| Signal | Threshold / match |
|--------|-------------------|
| Commit count | `> 1` → single-tidy-commit warning |
| Black | `black==26.3.1` (pinned to match the `.pre-commit-config.yaml` hook) with `--check --line-length 512` on changed `.py`, excluding deletions |
| Fan-out | touched-file count `> 15` |
| Hotspots | exact path match for `AGENTS.md` and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` only — near-miss or nested paths do not fire |

Gate: `tests/test_ci_fleet_pr_lint.py` (the G4 pre-commit split and the label hatch are pinned by `tests/test_ci_precommit_g4.py` and `tests/test_ci_sequence_safety_hatch.py`).

### Post-merge main-verify (pointer)

[`.github/workflows/main-verify.yml`](../.github/workflows/main-verify.yml) is the bypass-proof G3 net (`symbol-screen` always + path-gated `battery` + failure `notify`). **G3.1** resolves BASE to the last successful main-verify tip when it is an ancestor of HEAD (sweeps `[skip ci]` gaps), else `event.before`, else `HEAD^1`. Per-PR labels never demote this job — only commit trailers do. Operator deep-dive for catch-up / notify / battery sync: AGENTS.md CI/CD Pipelines (`main-verify.yml`) and the open sibling docs PR that owns the dedicated Post-Merge Main Verification section when present.

### Operator pitfalls (ci.yml-focused)

| Symptom | Check / Fix |
|---------|-------------|
| Per-PR Sequence Safety red, Quality Gate green | Expected split: Sequence Safety is not in QG `needs:`, but it **is** a required ruleset context, so the PR stays BLOCKED. Inspect `sequence-safety-report`; waive with commit trailers (owner labels green the PR check only) |
| Label greens Sequence Safety but `main-verify` fails after merge | Labels are PR-only; put `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` on a commit in the landed range |
| Merge queue stuck with no required check | Confirm `ci.yml` **and** `codeql.yml` still have `on.merge_group`; `Analyze (python)` must re-post on queue runs |
| Rapid main merges “lost” a CI run | `ci.yml` push group must be per-SHA with cancel disabled; `main-verify` is always per-SHA / no-cancel |
| `pass_filenames: false` hook still red on a tiny PR | Expected under G4 — those hooks run globally even with `--from-ref` |

## YubiKey GPG Provisioning

Operator pointer for host GPG / YubiKey 5 code-signing setup. Full validated procedure (commands, evidence, interoperability): [`notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md`](../notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md) (#904; pinentry stub fix #914).

### Intent

Juniper release-train / git signing may use a YubiKey-backed OpenPGP key. Operators hitting `gpg: KEYTOCARD failed: Invalid value` when moving an **ed448** key to the card need the hardware constraint, not another passphrase retry.

### Hardware constraint (verified)

YubiKey 5 series OpenPGP (incl. firmware 5.7.x) **does not implement Ed448 / X448**. `keytocard` of an ed448/x448 key fails with `Invalid value` / `SC_OP_FAILURE` even with correct passphrase + Admin PIN — the card rejects the algorithm attribute switch.

Validated layout (ed448 requirement kept where hardware allows):

| Role | Algorithm | Lives |
|------|-----------|-------|
| Certify (primary) | **ed448** | Offline / local ceremony dir — **never** on card |
| Sign | ed25519 | YubiKey slot 1 |
| Encrypt | cv25519 (X25519) | YubiKey slot 2 |
| Authenticate | ed25519 | YubiKey slot 3 |

### Related pitfalls

| Symptom / class | Guidance |
|-----------------|----------|
| Cannot *create* Ed448/Curve448 under gpg 2.4.x | A **downstream Ubuntu/Debian (FreePG-lineage) patch gate**, not upstream GnuPG: pass `--compliance=gnupg` (or set `compliance gnupg` in the ceremony `gpg.conf`). Required on patched builds, harmless on upstream, which creates v5 keys silently. |
| Scripted heredoc / shared loopback fd corrupts secrets | Never mix `--pinentry-mode=loopback` when a flow prompts for **both** passphrase and card PIN; use interactive or the stub harness for transfer |
| Headless re-validation | Ad-hoc harness: `util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash` + `util/ad-hoc/2026-08-03_yubikey_test_pinentry.bash` (**throwaway credentials only**) |
| Stub pinentry “No pinentry” | Greeting must be Assuan `OK …` (#914); non-OK greeting → gpg-agent treats pinentry as dead |

### Harness safety

The pinentry stub answers Admin-PIN/user-PIN/passphrase from `TEST_ADMIN_PIN` / `TEST_USER_PIN` / `TEST_PASSPHRASE`. It defeats interactive secret entry — **never** point it at a real keyring or a live-provisioned card.

### Related

- Code-signing migration status: [`notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md`](../notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md)
- Release-train headless commits are **API-signed on both lanes** (`createCommitOnBranch` in propose *and* ceremony), so they avoid the owner’s YubiKey while still satisfying `required_signatures`. The propose was unsigned until the 2026-08-12 ruleset normalization made it unmergeable (cascor#515) — see AGENTS.md / release-train runbook

## Open-PR Budget Alarm

Daily (and dispatchable) **report-only** guardrail for Cursor-fleet open-PR pile-ups. Workflow: [`.github/workflows/pr-budget-alarm.yml`](../.github/workflows/pr-budget-alarm.yml) (merged via [#870](https://github.com/pcalnon/juniper-ml/pull/870); flood analysis §4 item 9 / P1 §5).

### Intent

GitHub has no native “max open PRs” setting. This job is the **repo-side smoke detector**: it counts open PRs and alarms when the queue approaches a ceiling so same-file clusters do not fan out into merge damage. It is **not** a merge gate — a breach never blocks a PR and never turns the cron red.

Source-side throttle (Cursor dashboard per-run caps) is a separate owner action; see [`notes/JUNIPER_2026-07-30_JUNIPER-ML_CURSOR-DASHBOARD-CONFIG-REQUESTS.md`](../notes/JUNIPER_2026-07-30_JUNIPER-ML_CURSOR-DASHBOARD-CONFIG-REQUESTS.md).

### Schedule and privileges

| Item | Value |
|------|-------|
| Cron | `0 14 * * *` (14:00 UTC daily) — offset from Monday 06:00 docs/security scans and the 13:00 UTC release train |
| Manual | `workflow_dispatch` |
| Permissions | `contents: read` + `pull-requests: read` only (never writes PRs/comments/labels/Releases) |
| Concurrency | `group: pr-budget-alarm`, `cancel-in-progress: true` |

```bash
# Manual dry run to look at the same counts the alarm uses
gh pr list --repo pcalnon/juniper-ml --state open --limit 500 --json number,headRefName
gh workflow run pr-budget-alarm.yml --repo pcalnon/juniper-ml
```

### Thresholds and levels

Repo variables (empty → shell defaults):

| Variable | Default | Meaning |
|----------|---------|---------|
| `PR_BUDGET_WARN` | `15` | WARN when total open **or** `cursor/`-headed open PRs ≥ this |
| `PR_BUDGET_ALARM` | `30` | ALARM when either count ≥ this |

Level resolution (either metric can trip the level):

1. `ALARM` if `total >= alarm` **or** `cursor >= alarm`
2. else `WARN` if `total >= warn` **or** `cursor >= warn`
3. else `OK`

`cursor` = open PRs whose `headRefName` starts with `cursor/`.

Constraint: the workflow queries with `gh pr list --limit 500`. Past 500 open PRs, the counts understate the real queue — read a near-ceiling number as a soft floor, not exact cardinality.

### Outputs and Slack

- **Always** writes a GitHub Actions step-summary table (`total` / `cursor` / thresholds / `level`).
- Slack fires **only** when `level != OK`, via `secrets.SLACK_WEBHOOK_URL`, under the same non-blocking Q-CHANNEL contract as `release-train.yml`:
  - missing secret → skip (exit 0)
  - POST failure → `continue-on-error` (run stays green)
- Slack text is counts + run URL only (no diffs, no secrets).

### Failure modes (still green)

| Situation | Behavior |
|-----------|----------|
| `gh pr list` hard failure | `::warning::` annotation + step summary note; `level=OK` so Slack is skipped; exit 0 |
| Budget WARN / ALARM | Step summary + optional Slack; exit 0 (report-only) |
| Missing `SLACK_WEBHOOK_URL` on breach | Log skip; exit 0 |

Only the `gh pr list` call is wrapped in the downgrade. A later `jq` parse failure on an otherwise successful response is **not** specially handled (the step runs under `set -euo pipefail`) — that path is expected never to fire on well-formed `gh --json` output.

### Operator triage on WARN / ALARM

1. Open the workflow run step summary for exact `total` / `cursor` counts.
2. Drain or merge the oldest same-file clusters first (fleet-supervisor / `util/fleet_triage/predict_merge.py` when triaging `cursor/` fleets).
3. Confirm Cursor dashboard per-run caps are set (companion pack above) — the alarm detects; caps throttle at source.
4. Raise thresholds only via repo variables `PR_BUDGET_WARN` / `PR_BUDGET_ALARM` when the team deliberately accepts a larger open queue.

Design-of-record: [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) §4 item 9 / P1 §5.

---

## Environment Variables

These variables are consumed by Juniper packages documented in this repository. `juniper-ml` itself does not set them; they belong to the extras-installed packages.

| Variable                 | Used By               | Default                 | Description                               |
|--------------------------|-----------------------|-------------------------|-------------------------------------------|
| `JUNIPER_DATA_URL`       | juniper-data-client   | `http://localhost:8100` | juniper-data service URL                  |
| `JUNIPER_DATA_API_KEY`   | juniper-data-client   | *(none)*                | API key for juniper-data authentication   |
| `JUNIPER_DATA_EQUITIES_MAX_SYMBOLS` | juniper-data | `14` | Deployment ceiling for `equities` / `equities_seq` (`gt=0`). A request may only **lower** this. See [Equities Symbol Cap](#equities-symbol-cap). |
| `JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION` | juniper-data | `false` | Deployment-wide opt-in to a prefix cut. Logical OR with the request flag; a caller cannot opt out. |
| `JUNIPER_DATA_EQUITIES_CACHE_DIR` | juniper-data | `~/.cache/juniper_data/equities` | OHLCV / SEC cache. `experiment_stack.bash` `data_up` sets this to `$RUN_DIR/equities-cache`. |
| `JUNIPER_DATA_IMPORT_DIR` | juniper-data         | `/data/imports`         | Prefix `csv_import` `file_path` is resolved against. `experiment_stack` `data_up` does not set this — export a real on-host directory before `--up`. |
| `JUNIPER_DATA_CSV_IMPORT_MAX_BYTES` | juniper-data | `134217728` (128 MiB) | Deployment ceiling for csv_import. A request `max_bytes` may only lower it. `gt=0` — a negative value would make `read()` unbounded. |
| `JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION` | juniper-data | `false`            | Deployment-wide opt-in to a partial csv_import. Logical OR with the request field; a client cannot opt out. |
| `CASCOR_SERVICE_URL`     | juniper-cascor-client | `http://localhost:8200` | juniper-cascor service URL                |
| `JUNIPER_CASCOR_API_KEY` | juniper-cascor-client | *(none)*                | API key for juniper-cascor authentication |
| `CASCOR_MANAGER_HOST`    | juniper-cascor-worker | `127.0.0.1`             | Worker manager host                       |
| `CASCOR_MANAGER_PORT`    | juniper-cascor-worker | `50000`                 | Worker manager port                       |

> These are not set by juniper-ml itself — they are consumed by the installed sub-packages.
> `CASCOR_SERVICE_URL` defaults to the cascor service/container port (`8200`). The host-level stack and `util/get_cascor_*.bash` helpers target the host-facing port (`8201`) unless overridden.
> REST constructor `base_url` values are normalised as of the GitHub-main clients documented in [HTTP Client Base-URL Contract](#http-client-base-url-contract); those env vars are **not** themselves passed through `_normalize_url` unless the caller feeds them into the constructor.
Local orchestration scripts in `util/` also read the host-stack variables documented in [Host Orchestration Utilities](#host-orchestration-utilities), the E2E overrides in [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities), the per-run experiment overrides in [Experiment Stack Utilities](#experiment-stack-utilities), the Duplicati lane overrides in [Scheduled Duplicati Backup Lane](#scheduled-duplicati-backup-lane), and `EXCLUDE_CASCOR_SNAPSHOTS` on [Juniper Project-Tree Backup](#juniper-project-tree-backup) (script `TRUE` is `0`).
`JUNIPER_CONDA_DIR` (default `/opt/miniforge3`) is also the conda root for `util/check_conda_env_torch.bash` — see [Conda Env Torch Shadow Diagnostic](#conda-env-torch-shadow-diagnostic-p-5).

Local orchestration scripts in `util/` also read the host-stack variables documented in [Host Orchestration Utilities](#host-orchestration-utilities), the E2E overrides in [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities), the F-039 store-probe overrides in [F-039 Store Probe](#f-039-store-probe) (`JUNIPER_E2E_CANOPY_URL`, `JUNIPER_E2E_CANOPY_LOG`), the per-run experiment overrides in [Experiment Stack Utilities](#experiment-stack-utilities), and the Duplicati lane overrides in [Scheduled Duplicati Backup Lane](#scheduled-duplicati-backup-lane).

`JUNIPER_CASCOR_SNAPSHOTS_DIR` is **dual-use**: cascor's snapshot write directory **and** `snapshot_index.default_root()`.
Experiment `--up` may redirect it to `$RUN_DIR/snapshots` (W-6). The sidecar chain must **not** — pass `--root` instead.
See [Snapshot Sidecar Chain](#snapshot-sidecar-chain) and [Snapshot Attribution Dataset Pin](#snapshot-attribution-dataset-pin).
`JUNIPER_CASCOR_SRC` / `JUNIPER_DATA_ROOT` override the trees `snapshot_classify.py` (load stage) and `snapshot_attribute.py` import when the fallbacks
(`~/Development/python/Juniper/juniper-cascor/src` and `.../juniper-data`) are wrong.
`JUNIPER_EXP_RUN_ROOT` is the query-time join root for `snapshot_index.py --resolve-datasets` / `--dataset-id`.

`JUNIPER_SUITE_GRAFANA_BRIDGE` (`1`/`true`/`yes`/`on`) adds `--grafana-bridge` to every suite `--up`. It is an env toggle, not a suite key — a suite key would change PF-1's `config_sha256` between bridged and unbridged repeats. `JUNIPER_EXP_PROMETHEUS_URL` (default `http://127.0.0.1:9090`) is where `_metrics_scraped` asks `scrape_confirmed`. See [PF Scenario Suites](#pf-scenario-suites).

---

**Last Updated:** 2026-09-04
**Version:** 0.6.59
**Maintainer:** Paul Calnon
