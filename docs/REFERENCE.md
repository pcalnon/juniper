# Reference

## juniper-ml Technical Reference

**Version:** 0.6.6
**Status:** Active
**Last Updated:** 2026-08-07
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Package Overview](#package-overview)
- [Extras Reference](#extras-reference)
- [Ecosystem Compatibility](#ecosystem-compatibility)
- [Host Orchestration Utilities](#host-orchestration-utilities)
- [Editable Install Drift Check](#editable-install-drift-check)
- [Pytest Orphan Reaper](#pytest-orphan-reaper)
- [Environment Floor Drift Check](#environment-floor-drift-check)
- [Agent Suite Doctor](#agent-suite-doctor)
- [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities)
- [Fleet Triage and Sequence Safety](#fleet-triage-and-sequence-safety)
- [Post-Merge Main Verification](#post-merge-main-verification)
- [Experiment Stack Utilities](#experiment-stack-utilities)
- [Shared-Package CI Workflows](#shared-package-ci-workflows)
- [Docs Full Check](#docs-full-check)
- [Scheduled Security Scan and Lockfile Update](#scheduled-security-scan-and-lockfile-update)
- [Release-Train Detect Summary and Slack](#release-train-detect-summary-and-slack)
- [AGENTS.md Date Check](#agentsmd-date-check)
- [Claude.yml Access Validation](#claudeyml-access-validation)
- [Sibling Packages](#sibling-packages)
- [Version History](#version-history)
- [Build and Release](#build-and-release)
- [Flood-Remediation CI Gates](#flood-remediation-ci-gates)
- [YubiKey GPG Provisioning](#yubikey-gpg-provisioning)
- [Open-PR Budget Alarm](#open-pr-budget-alarm)

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
|             | `juniper-service-core`                                                                   | `>=0.2.0,<0.6.0`  |
| `doc-tools` | `juniper-doc-tools` (back-compat alias for the doc-tools entry in `tools`)               | `>=0.1.0,<0.2.0`  |
| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.1.5,<0.3.0`  |
|             | `juniper-recurrence`                                                                     | `>=0.2.0,<0.4.0`  |
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

The three services intentionally ship with **different** `rate_limit_enabled` defaults — `juniper-data` enables rate limiting out of the box; `juniper-cascor` and `juniper-canopy` leave it disabled by default for local-dev ergonomics. The per-minute threshold is uniform across services (60 req/min) so only the enable flag varies.

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

The split-default is intentional, not an oversight: `juniper-data` is a higher-risk public-shaped surface (dataset generation, paginated reads), so it ships rate-limited by default; the other two run behind a known reverse-proxy / authenticated client surface where the rate-limit value adds operator friction during local development. Closes the documentation gap tracked in the v7 outstanding-development roadmap under CFG-08.

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

Failure / health / port contract (`nohup` mode):

- After each successful `nohup` launch, the PID is appended to `STARTED_PIDS`. An `ERR` trap runs `cleanup_on_failure` (JR-ML-SEC-042): SIGTERM every tracked PID, wait 3s, SIGKILL any survivors, always `rm -f` the project pidfile, then exit 1 — even when `STARTED_PIDS` is still empty (preflight / early failure).
- `wait_for_health` polls `curl -sf` every `HEALTH_CHECK_INTERVAL` seconds (default `2`) until success or `HEALTH_CHECK_TIMEOUT` (default `60`). Timeout returns 1 and trips the ERR cleanup above; it does not hang forever.
- `check_port_available` rejects a busy port (exit 1). If `ss` is missing or unusable when the helper runs, it **fail-opens** (treats the port as free). The `nohup` preflight still hard-requires `ss`, so normal host-mode plant never relies on that fail-open; hermetic tests and any out-of-band caller of the helper can.
- In systemd mode (`--systemd` or `USE_SYSTEMD=1`), both scripts call `systemctl --user` for the same four units and **never** read or write `JuniperProject.pid`. See [systemd mode](#systemd-mode) below.

#### Health-check interval clamp (juniper-ml#782)

`wait_for_health` polls `curl -sf` and advances `elapsed` by the poll interval each loop (default `HEALTH_CHECK_INTERVAL=2`, timeout `HEALTH_CHECK_TIMEOUT=60`). An interval `<= 0` never advances `elapsed` (`sleep 0` is a no-op) and busy-loops forever — including `HEALTH_CHECK_INTERVAL=0` or a zero/invalid 4th argument.

Post-[#782](https://github.com/pcalnon/juniper-ml/pull/782): if the interval is not a positive integer (`^[1-9][0-9]*$`), plant logs `WARNING: invalid health-check interval … clamping to 1s` and uses `1`. Prefer the default `2`. Do **not** set `HEALTH_CHECK_INTERVAL=0` to "poll as fast as possible" — that was the busy-loop class. Coverage: `tests/test_juniper_plant_all.py` (`TestWaitForHealth`).

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
| Mid-plant health timeout / abort | Read the failing service log under that repo's `logs/`. `cleanup_on_failure` already tried SIGTERM→SIGKILL on `STARTED_PIDS` and removed `JuniperProject.pid`. Confirm nothing is still listening (`ss -tlnp`) before re-planting; do not expect `chop_all` to find a pidfile after a failed plant. |
| `juniper-cascor` never reaches `/v1/health` | Inspect `juniper-cascor/logs/juniper-cascor_*.log`. Prefer the default `JuniperCascor1` env; the legacy `JuniperCascor` Python 3.14 / torch layout is a known health-startup trap. See [`notes/JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md`](../notes/JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md). |
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
| Mid-plant unset-variable / odd conda activate noise | Confirm `safe_conda_activate` restores with `set -u` (see above). A broken restore disables nounset for later steps, so typos that should have failed may look like unrelated mid-plant failures. |

#### Orphaned worker cleanup (`KILL_WORKERS`)

Host-mode `chop_all` optionally reaps leftover cascor workers that are **not** in `JuniperProject.pid` (crashed plant, manual launches, or workers started outside the pidfile loop). This path is **opt-in** and **nohup-only**:

- Gate: `KILL_WORKERS` must be exactly `1` (default `0`). Otherwise chop logs `KILL_WORKERS flag is not set to 1` and returns without signaling.
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
| Every line stopped or skipped as stale / wrong process (`STOP_FAILURES == 0`) | Truncated (`: >` the file) — chop exits 0 |
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
4. **Known blast-radius gap:** systemd starts are **not** appended to `STARTED_PIDS`. On a mid-plant health timeout the ERR trap still runs `cleanup_on_failure` (logs cleanup + `rm -f` the unused pidfile path), but it **does not** `systemctl --user stop` any units already started. Operators must stop leftovers manually or with `util/juniper_chop_all.bash --systemd`. Do not "fix" this by inventing `systemctl stop` inside cleanup without updating the hermetic pin.

**Chop (`util/juniper_chop_all.bash --systemd`):**

1. Stops units in **reverse** dependency order: `juniper-cascor-worker` → `juniper-canopy` → `juniper-cascor` → `juniper-data`.
2. Soft-fails per unit (`was not running or failed to stop`) and continues — overall exit is still `0`.
3. Always `exit 0` after the systemd loop — never falls through to the pidfile parser, `validate_pid` / `graceful_stop`, or `orphaned_worker_cleanup` / `KILL_WORKERS`.

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Port preflight fails | Run `ss -tlnp` and free the reported port (`8100`, `8201`, `8050`, or `8210` by default), or override the matching `JUNIPER_*_PORT` before startup. |
| Mid-plant health timeout / abort | Read the failing service log under that repo's `logs/`. `cleanup_on_failure` already tried SIGTERM→SIGKILL on `STARTED_PIDS` and removed `JuniperProject.pid`. Confirm nothing is still listening (`ss -tlnp`) before re-planting; do not expect `chop_all` to find a pidfile after a failed plant. |
| `juniper-cascor` never reaches `/v1/health` | Inspect `juniper-cascor/logs/juniper-cascor_*.log`. Prefer the default `JuniperCascor1` env; the legacy `JuniperCascor` Python 3.14 / torch layout is a known health-startup trap. See [`notes/JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md`](../notes/JUNIPER_2026-05-07_JUNIPER-CASCOR_CONDA-ENV-FIX.md). |
| Worker startup says binary missing | Activate the worker env and install the package: `conda activate JuniperCascor1 && pip install juniper-cascor-worker`. |
| `chop_all` cannot find `JuniperProject.pid` | Confirm `plant_all` completed successfully in `nohup` mode and check the PID path printed at startup. In non-standard layouts, rerun shutdown with `JUNIPER_PROJECT_DIR` set to that same project root. If using systemd mode, stop with `util/juniper_chop_all.bash --systemd` instead. |
| systemd plant: `'curl' not found in PATH` | Install/expose `curl` before `--systemd` plant; no units were started. |
| systemd plant health timeout / partial stack | `cleanup_on_failure` did **not** stop user units. Inspect `systemctl --user status juniper-{data,cascor,canopy,cascor-worker}` and tear down with `util/juniper_chop_all.bash --systemd` (or matching `systemctl --user stop`) before re-planting. |
| Worker WARNING: healthy but unit not active | HTTP `/v1/health/ready` passed but `is-active` failed — check `journalctl --user -u juniper-cascor-worker` / unit file; plant still exited 0. |
| Mixed plant/chop modes | Never plant with `--systemd` and chop via pidfile (or the reverse). Match the mode used at start. |

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

`STALE` is **soft** — exit stays `0`, because `import` still resolves. `--strict-version` makes it exit `1`. `--strict` remains about the path axis only.

```bash
python util/editable_install_drift_check.py                     # report (STALE is soft)
python util/editable_install_drift_check.py --strict-version    # exit 1 on any STALE
python util/editable_install_drift_check.py --fix --fix-stale --dry-run   # preview refresh
python util/editable_install_drift_check.py --fix --fix-stale             # re-stamp metadata
```

`--fix-stale` repairs a stale-but-`FRESH` install against the path it **already points at** (`drift: "stale-metadata"`), not a canonical-discovery result — reinstalling from the recorded path is what re-stamps the metadata, and routing it through discovery could re-point a deliberate checkout. `ORPHANED` items keep resolving to their canonical repo (`drift: "path"`).

A dynamic version is read only from an **explicit** declaration (setuptools `[tool.setuptools.dynamic] version.attr`, hatch `[tool.hatch.version] path`); an unrecognized backend reports `UNKNOWN` rather than guessing at a plausible `_version.py`.

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

**A live experiment stack or campaign is never an orphan, however it is parented.** `experiment_stack.bash` and `isolated_stack.bash` launch their services with `nohup` inside a subshell, so the services reparent to `systemd --user` — which is precisely the orphan predicate below. A campaign orchestrator or watchdog started with `setsid` / `disown` lands there too.

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

`SKIPPED` increments (never WOULD REAP / kill) when:

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

Troubleshooting:

| Symptom | Check / Fix |
|---------|-------------|
| Expected orphan never listed | Confirm cmdline contains a `JuniperC*` env path or `Juniper/worktrees/`; other-user and non-Juniper python are intentionally excluded. |
| High `skipped` count, zero reaped | Transient ps→gone race or incomplete `/proc/<pid>/status`; re-run `--dry-run --verbose` once the process table settles. |
| Live pytest session would be killed | Parent still exists and is not init / `systemd --user` → script prints `KEEP` under `--verbose` and does not kill. |

---

## Environment Floor Drift Check

`util/env_floor_drift_check.py` (gap I-2) compares each `juniper-*` floor declared in a target repo's `pyproject.toml` against the **installed** wheel version read from `*.dist-info/METADATA` — the below-floor plain-wheel case that pin-linters and the editable checker miss. It does **not** invoke the environment's interpreter (so a broken env still reports).

Classifications: `OK` (installed ≥ floor), `BELOW_FLOOR` (installed < floor), `MISSING` (not installed). Exit `0` when no `BELOW_FLOOR`; `1` on any `BELOW_FLOOR` (`--strict` also fails on `MISSING`); `2` on invocation / resolution errors.

#### Env selection precedence (`resolve_site_dirs`)

Env names are **never** hardcoded. Resolution order (`util/env_floor_drift_check.py` `resolve_site_dirs`):

1. `--site-packages PATH` (repeatable) — scan those dirs; missing paths → exit `2` with `no --site-packages dir exists: …`
2. Else `--env NAME` (repeatable) — expand `<conda-dir>/envs/<NAME>/lib/python*/site-packages`; empty expand → exit `2` with `no site-packages under …`
3. Else `prompts/agent_templates/data/ecosystem.yaml` — map the target `[project].name` via `conda_envs[].used_by`; missing name / mapping / site-packages → exit `2` with the matching reason (pass `--env` or `--site-packages` to override)

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

Constraints / pitfalls:

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

`--down` does **not** use `JuniperProject.pid`. It stops canopy → cascor → data via `stop_port`, which asks `ss -tlnpH "sport = :<port>"` for the first `pid=N` (`port_pid`), then `kill`s that PID.

Soft-fail when `ss` is missing, exits nonzero, or reports no `pid=` (logs "nothing listening"; not a failure). `--dry-run --down` announces the kill line but never kills. After stop, live mode removes `${RUN_DIR}/data`, the data venv, `*.pid`, and `snapshot_*.h5` under canopy `src/snapshots/` (non-matching names are left alone). It deliberately does **not** touch cascor's shared snapshot root `juniper-cascor/cascor-snapshots/` — that is a project asset store outliving every stack, and repointing the teardown glob at it is the mistake the in-script comment guards against. Per-run snapshot sweeping is done by giving the run its own `JUNIPER_CASCOR_SNAPSHOTS_DIR`, as `experiment_stack.bash` does.

Orphaned listeners on `8101`/`8202`/`8051` after a broken teardown collide with the next `--up` — prefer `--down`, then `ss -tlnH 'sport = :8101 or sport = :8202 or sport = :8051'` (should print nothing).

Coverage: `tests/test_isolated_stack_script.py` (`TestPortPid` / `TestStopPort` / `TestLiveDown` in juniper-ml#786/#788).

#### Health wait / status probe

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
| Canopy looks "up" but training APIs are demo stubs | `JUNIPER_CANOPY_DEMO_MODE` must be `0` on the live launch line. |
| Control-WS `403` / reconnect churn | Cascor allowlist + canopy Origin must both be canopy's origin (`http://127.0.0.1:<CANOPY_PORT>`). See checklist §4. |

Do **not** point isolated ports at the host stack or run `--up` on ports `plant_all` already owns.

---

## Fleet Triage and Sequence Safety

Flood-remediation tooling for Cursor-fleet / third-party open PRs and for silent symbol / docs damage that ordinary lint cannot see. Two layers:

| Layer | Path | Role |
|-------|------|------|
| Sequence-safety screens | the `juniper-symbol-loss-check` / `juniper-docs-additions-check` console scripts (PyPI `juniper-ci-tools>=0.8.0`) | Path-invoked BASE..HEAD screens used by CI (`sequence-safety` job, `main-verify.yml`) |
| Predicted-merge triage | `util/fleet_triage/predict_merge.py` | Detached-clone merge of `origin/main` into a PR tip; runs fast gates + screens on the **merge RESULT** |
| Fleet supervisor agent | `.claude/agents/fleet-supervisor.md` | Read-only adjudication over a `--batch` report (never pushes / merges / closes) |

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
- Per-PR labels `allow-symbol-loss` / `docs-rewrite` only demote the advisory CI job via `--advisory` (WARN-only exit 0). They are invisible to `push:main` `main-verify` — use the commit trailer for post-merge green.
- Exit codes: `0` clean, `1` ≥1 unwaived FAIL, `2` usage / bad ref. Gates: `tests/test_symbol_loss_check.py`, `tests/test_docs_additions_check.py`.

### `predict_merge.py` operator contract

```bash
python util/fleet_triage/predict_merge.py --pr 895 --json
python util/fleet_triage/predict_merge.py --batch --json
python util/fleet_triage/predict_merge.py --pr 895 --repo-root .
# Skip the pre-commit battery when hooks are unavailable locally:
JUNIPER_FLEET_SKIP_PRECOMMIT=1 python util/fleet_triage/predict_merge.py --pr 895
```

Per PR the script:

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

`--batch` also builds a same-file cluster map and a suggested merge order. Heal-first detection (`_is_heal`) looks at the PR **title** and **branch** (case-insensitive) for any of `restore` / `heal` / `repair` / `fix-first`, sorts those ahead of ordinary PRs, then ascending same-file contention. `triage_batch` **continues** after a per-PR `PredictMergeError` (the `ERROR` row above). Exit `0` always reports (even when every verdict is `DAMAGED` / `CONFLICT` / `ERROR`); exit `2` is usage / precondition only (`gh` missing, bad `--repo-root`, or an unresolvable ref in single `--pr` mode).

**`--pr` hard-fail vs `--batch` soft-ERROR.** The two modes deliberately diverge on a `gh` failure: in single-PR mode `triage_pr` raises `PredictMergeError` when `gh` exits nonzero or returns non-JSON, so the CLI exits `2` (there is no partial report worth printing). In `--batch`, the same condition becomes a soft `ERROR` row for that PR only and the rest of the open-PR set still runs. An exit `2` from `--pr` is a precondition failure, never a damage finding.

Degrade paths (never crash the report): missing / broken `symbol_loss_check.py`, checker exit `2`, or non-JSON stdout → symbol screen `status=skip`. A delta with no `.py`/`.bash` short-circuits the symbol subprocess. Gate: `tests/test_predict_merge.py` (incl. `Allow-Symbol-Loss` and `Allow-Docs-Rewrite` trailer → `MERGE-CLEAN` arms).

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

On 2026-08-19, of 23 live worktrees there were **11 distinct `AGENTS.md` contents
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
state — merged, clean, not the current cwd. Even together those are necessary and
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

The flag is still only a *supplement* to judgement: a session idling elsewhere while
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
be seen. Remove worktrees individually and **never with `--force`**, so git's own
dirty-check stays live as a time-of-check/time-of-use guard.

---

## Memory File Size Budget

P2 of the [shared-session-memory plan](../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md).
`util/memory_budget_check.py` enforces a character ceiling on always-loaded memory
files, declared in `conf/memory_budget.json`. Run by the standalone `Memory Budget`
job in `ci.yml`.

> **BLOCKING as of 2026-08-20 (P4).** The budget step no longer passes `--advisory`;
> a violation exits 1 and fails the check. The companion **G3** step in the same job
> stays advisory — see [Relocation Completeness](#relocation-completeness-g3) for why.
>
> To make it actually gate a merge it must also be a **required context** in the branch
> ruleset. That is a settings change, not a repo change, and it is deliberately promoted
> there rather than through the Quality Gate `needs:` — a standalone job that skips on
> `push` must never be able to fail the aggregate gate.
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
path **without moving the ceiling** — the debt is still owed and the next author
still sees it. That is the property the house `Allow-Symbol-Loss:` idiom lacks.
Waivers are always reported, never silent. Carry the trailer into the **squash**
commit message; trailers travel in git history.

### Not governed: `docs/REFERENCE.md`

Deliberately absent from the budget. It is the migration **destination**; capping it
would penalise exactly the relocation the plan wants, and it is not an always-loaded
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
```

Exit **0** pass or advisory / **1** over budget / **2** misuse or broken machinery.

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
computed on normalised prose (markdown emphasis, link syntax, list markers and
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

Getting this backwards makes the gate tautological. It is pinned directly by
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

For P3 the distinction matters little: relocation moves prose largely intact.
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

## Test Suite Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`
- `tests/test_env_repr_safety.py` -- Lint + behaviour gate for the env-repr secret-leak class: forbids raw `os.environ`-derived subprocess `env=` mappings in `tests/` (they leak secrets through pytest `--showlocals`-style frame-local reprs) and proves `tests/redacted_env.py`'s `RedactedEnv` masks its repr while behaving as a normal subprocess env mapping. Includes a synthetic-violation self-test; `patch.dict(os.environ, ...)` is deliberately exempt.
- Doc-link validator regression tests live in [`juniper-doc-tools/tests/`](juniper-doc-tools/tests/) (Wave 4 of the doc-link migration; exercised by the dedicated `CI -- juniper-doc-tools` workflow).
- `tests/test_worktree_cleanup.py` -- Tests for `util/worktree_cleanup.bash` argument parsing, dry-run, and error handling; Phase 1 dirty porcelain exit-1 gate (juniper-ml#747) and clean push / Phase 2 path-collision arms (open #753) drive fixture repos via sourced `phase_1_save_and_push` / `phase_2_create_new_worktree`
- `tests/test_worktree_sweep_scripts.py` -- Tests for `util/ad-hoc/worktree_sweep_*.bash`: survey/apply row compatibility, `SAFE`-only removal, and unknown-repo skips
- `tests/test_cleanup_session_worktrees.py` -- Hermetic tests for `scripts/cleanup_session_worktrees.py`: `_has_merged_pr` fail-closed (gh fail / bad JSON), dirty/unmerged/detached keeps, self-cwd skip, and `--dry-run` remove of main-ancestor / MERGED-PR clean tips. `LockGateTest` pins the 2026-08-21 liveness gate against real locked worktrees: an otherwise-removable locked tree is kept, the `--dry-run` plan does not promise to remove it, unlocking the same tree makes it removable again (proving the lock is what held it), and an anti-resurrection arm asserts the source never passes `--force`/`-f` to `worktree remove`
- `tests/test_reap_pytest_orphans.py` -- Tests for `util/reap_pytest_orphans.bash` dry-run, live-parent safety, orphan detection, and isolated kill invocation
  - `TestLiveExperimentProtection`: the P1 pidfile + P2 cmdline keys, reproducing the three shapes a 2026-08-16 dry run would have killed (service / orchestrator / watchdog); the load-bearing live-mode arm proving a genuine orphan still dies while the protected service does not; stale-pidfile conservatism; and a malformed pidfile not aborting the sweep under `set -euo pipefail`
- `tests/test_kill_helpers.py` -- Hermetic process-filter / kill-path tests for `util/kill_all_pythons.bash` and `util/juniper_worker_kill.bash` (PATH-stubbed `ps`/`sudo`/`kill`; bash `kill` builtin disabled; never touches live PIDs)
- `tests/test_check_conda_env_torch.py` -- Hermetic exit-matrix tests for `util/check_conda_env_torch.bash` (P-5 torch._C shadow diagnostic: 0/1/2/3/4 via `JUNIPER_CONDA_DIR` + stub python; no real conda/torch)
- `tests/test_requirements_drift_check.py` -- Tests for `util/requirements_drift_check.py`: structural range validation, BAD_PATH / BAD_RANGE classification, `--ecosystem-root` rewriting, CLI exit codes, JSON output
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
- `tests/test_service_fork_drift.py` -- Drift gate for the security guards that must hold identically in `juniper-data`'s and `juniper-cascor`'s forks of the `juniper-service-core` middleware / security code (defect-register §2.3 "Copy drift").
  - A registry of named guards, each detected by a small source marker, rather than a file diff: the forks diverge legitimately and constantly (juniper-data deliberately holds API keys in a `list` for `compare_digest` timing where service-core uses a `set`), so a diff would drown the signal.
  - Two-sided by design. `ENFORCED` guards must be **present** in every fork; their disappearance is a regression. `KNOWN_GAP` guards must still be **absent** -- when someone closes one, the gate fails and instructs them to promote the row to `ENFORCED`, so the ledger cannot rot into a list of things that used to be true.
  - Cross-repo assertions gate exactly like `test_ci_tools_drift.py` (`GITHUB_ACTIONS=true` or `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`); the registry-structure checks and the matcher's negative controls always run. It bites in `docs-full-check.yml`, the only job that clones the siblings.
  - A site may be marked **`ordered`**, meaning its markers must appear in the declared sequence, not merely be present. `cors-outside-auth` (register `APD-CASCOR-001b` / `APD-DATA-035`) is the reason the flag exists: that guard regresses by two `add_middleware` calls **swapping places**, so both markers are present either way and a presence-only check would report SUCCESS on the exact defect it guards -- the vacuous-pass class. Requiring `RequestIdMiddleware` to be registered before `CORSMiddleware` *is* the invariant "CORS is registered last, so it runs outermost". Its negative controls live in the always-on structural class, so they still run in `ci.yml` where the cross-repo arms skip.
  - **No `KNOWN_GAP` rows currently remain** -- all six copy-drift guards are `ENFORCED`. The `KNOWN_GAP` machinery is retained for the next row that acquires a reference implementation; note that with zero such rows `test_known_gaps_are_still_open_or_get_promoted` iterates an empty set and passes **vacuously**.
- `tests/test_assert_release_tag.py` -- Behavioural tests for `util/assert_release_tag.bash` plus a **wiring gate** asserting all 7 publishers invoke it with their own `--expect-prefix`, and that **no publisher grants `id-token` at workflow level** (P4).
  - Drives synthetic dist directories: happy paths (meta, sub-package, `-rc1` normalization, alpha), and the refusals that matter -- branch ref, **empty** ref_type (must fail closed, not read as a tag), tag/version mismatch, wrong package prefix, missing dist dir, sdist-only, version-less tag, misuse exit 2.
  - The mismatch case is a live regression guard: it originally passed because `tr -d '-_'` errored on this host and both sides normalized to empty. `util/` is outside every pre-commit Python hook's scope, so this suite is the gate.
- `tests/test_publish_env_policy_drift.py` -- Drift gate for the **tag-only deployment ref policy** on every `pypi` / `testpypi` environment ([publish-path design](../notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md) §6 Option A / §12.5).
  - The control lives in GitHub **settings, not the repo**: no test covered it, no reviewer sees a diff when a policy is deleted, and the failure is silent -- the publish path just becomes permissive again.
  - Two load-bearing invariants: **no branch-type policy may exist** (adding a `main` branch policy re-opens branch dispatch while every tag pattern stays intact and the environment still looks configured -- owner decision D3 was tag-only), and **`pypi` must retain `required_reviewers`** (a `PUT` is create-or-update, so a careless payload clears the human gate while successfully setting a ref policy -- the environment then looks *more* configured while being weaker).
  - Structural checks + the detector's **negative control** always run offline (a gate that cannot fail is not a gate; an untyped policy must read as `branch`, never `tag`). The live half is gated on `GITHUB_ACTIONS=true` / `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` and is read-only (`gh api` GETs).
  - **No silent caps**: per-PR CI's built-in `GITHUB_TOKEN` reaches juniper-ml only, so the live half partitions the registry repos into readable / unreadable, verifies the readable ones, **names** the unverified ones, and refuses to pass if nothing at all was readable. A repo that IS readable but whose environment 404s is a real finding (deleted environment), not a permission skip. Full-fleet cover: `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`.
  - Repair: `util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> <env>`.
- `tests/test_pyproject_extras.py` -- Lint test pinning the `[project.optional-dependencies]` surface (`clients`, `worker`, `servers`, `tools`, `doc-tools`, `all`). Asserts the exact set of extras, the exact membership of each, that `[all]` aggregates every non-alias extra exactly once, and that `[project].version` is semver-ish. Added pre-0.5.0 after juniper-ml#295 introduced `[servers]` + `[tools]` without regression coverage; any future edit to extras must update the lint contract in the same PR.
  - juniper-ml's own pin check runs every PR; the cross-repo assertion auto-skips when siblings aren't on disk and additionally skips local runs by default. Set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to opt in locally.
- `tests/test_template_library_drift.py` -- Lint test enforcing manifest <-> template consistency for the custom-agent template library (`prompts/agent_templates/`): every registered template exists and every template is registered; each follows the canonical section skeleton in order; every `{{placeholder}}` matches the systematic convention; the `generic` fallback always matches.
  - The **sole gate** for the library because `prompts/**` is excluded from all pre-commit hooks, so it must stay wired into `ci.yml`. Design-of-record §5.4/§9.
- `tests/test_template_selection.py` -- Lint validating `manifest.yaml`'s `match_signals` support deterministic category selection: exactly one always-match fallback (`generic`), every other template has non-empty keyword signals, no two share an identical keyword set, and every `class` is allowed. Companion gate to the library drift test.
- `tests/test_template_select_preview.py` -- Tests for `util/template_select_preview.py` (the offline selection preview, P2): drives the real manifest (so it also guards selection drift) -- a task with a template's keyword selects that template (`failing-tests`), a no-keyword task falls back to `generic`, the ranked candidates exclude the always-match fallback, and the CLI exits 0 with the documented JSON shape.
- `tests/test_template_data_resolver.py` -- Tests + drift gate for the custom-agent suite data layer (PR 6b): the five `prompts/agent_templates/data/*.yaml` files load, `util/template_data_resolver.py`'s `load`/`resolve` (dotted lookup) work, and -- since `prompts/**` is pre-commit-excluded -- this is the sole gate; also asserts `conventions.line_length` matches `.markdownlint.yaml` and the handoff threshold is the current 95-99% (not a stale 80%).
- `tests/test_safe_merge.py` -- Tests for `util/safe_merge.py` (the R4 merge gate). Hermetic: `_gh`, `pr_state`, `wait_for_required` and `update_branch` are replaced with recorders, so no network / `gh` / repo / PR is touched.
  Pins the safety contract -- every refusal path (closed / draft / conflicted / checks-failed / checks-unfinished / unsettled-ref / sync-cycles-exhausted / merge-returned-but-PR-not-merged) asserts that **no** `pr merge` was issued, plus `--match-head-commit` head pinning, the server-side (`PUT`) branch refresh, the async ref-settle poll, moved-head-is-a-refusal, the no-local-git invariant, and dry-run writing nothing.
- `tests/test_open_signed_pr.py` -- Tests for `util/open_signed_pr.py` (signed cross-repo PR opener). Hermetic: `gh` is a PATH stub that records argv and replays canned stdout, so no network / repo / `git` is touched.
  - Pins the mutation name (`createCommitOnBranch` -- the whole point), `expectedHeadOid` == the resolved base sha, base64 additions, `fileChanges.deletions` present for `--delete` and **omitted** when unused, and the explicit `ref=refs/heads/<branch>` on the refs POST (the ml#770 R7 lesson).
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
  Covers every §8 precondition HALT (main-CI / anomaly / missing-CHANGELOG / notes-render-failed / TestPyPI-verify), execute `RELEASED` when both publish gates completed, the happy-path exact action sequence, dup-guard/idempotent re-entry, the R7 gh-surface invariant (live seam issues only the allowlisted verbs + the 2 archive api calls -- `git/refs` POST + `createCommitOnBranch`), and a dry-run leaving `git status` clean. The gate for `util/`.
  - Execute-time open-PR reuse + archive-already-on-main idempotent re-entry arms (juniper-ml#730).
  - R7 archive-lane `ref=` required (juniper-ml#770): missing/empty `ref=` on a `git/refs` POST is `SeamViolation` (not deferred to the live API).
- `tests/test_agents_md_version_drift.py` -- Lint test pinning `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s `[project].version`. Added after juniper-ml#295 bumped pyproject 0.4.1→0.5.0 but left AGENTS.md at 0.4.0 for ~6 days (fixed in juniper-ml#304); this lint makes the drift impossible to ship. Intentionally portable: auto-locates the repo root, so the module can be dropped into any Juniper repo's `tests/` (skips loudly if AGENTS.md has no canonical header).
- `tests/test_agents_md_header_schema.py` -- Lint pinning `AGENTS.md`'s canonical header schema. Six required fields in this relative order: `**Project**`, `**Repository**`, `**Author**`, `**License**`, `**Version**`, `**Last Updated**`. Extras (e.g. `**Python**:`) may be interleaved freely. Validates each value non-empty and `**Last Updated**` is `YYYY-MM-DD`. Currency of the date is enforced by `.github/workflows/agents-md-touch-up.yml`. Portable (self-locating).
- `tests/test_agents_md_tree_drift.py` -- Lint (gap G-3) asserting every tracked non-hidden top-level dir (`git ls-tree`; the `ls -d */` surface) appears as a node in `AGENTS.md`'s fenced Repository-Structure tree, catching the indented-tree omission the grep-based `test_agent_suite_path_drift.py` cannot (stale `templates/`, missing `conf/`/`papers/` + 6 sub-package dirs). Portable; a synthetic negative case proves it bites.
- `tests/test_isolated_stack_script.py` -- Contract tests for `util/isolated_stack.bash` (plan unit E1): `bash -n` syntax, launch-line text assertions (dedicated-venv install, `python -m juniper_data`, `uvicorn api.app:create_app --factory`, canonical canopy env vars, the control-WS origin/allowlist pair), and hermetic `--dry-run` behavioural checks (prints commands with ports expanded, touches nothing; misuse exits 2).
- `tests/test_experiment_stack_script.py` -- Contract + behavioural tests for `util/experiment_stack.bash` (CLI experimentation plan Wave 2.1; `util/` is not
  pre-commit-lint-gated, so this unittest is the gate): `bash -n` syntax, the CLI misuse matrix (exit 2), the §9.3 port ranges and §6.4 RUN_DIR contract, the §6.1 launch
  recipes env-set by env-set, the **F-6** listener-pid rule (no `$!` in any `*_up`; `record_listener_pid` runs after `wait_for_health`; teardown verifies uid + cmdline),
  §7.3 suffix-based `_monitoring$` gateway discovery + the exact socat relay line, the §7.2 target file rendered and parsed as JSON (four labels), and the operator-safety
  invariants (no `JuniperProject.pid`, no canopy, no repo `.env` write, no operator port).
  - Behavioural arms are hermetic: `JUNIPER_EXP_{RUN,LOCK}_ROOT` / `_DEPLOY_DIR` / `_CONDA_DIR` redirect every path into a tempdir and `ss`/`curl`/`docker`/`socat` are PATH
    stubs -- `--dry-run --up` prints all three launch classes with allocated ports expanded while leaving run root / lock root / targets dir non-existent; `allocate_port`
    skips locked and bound ports and fails loudly on an exhausted range; `--down` kills a self-spawned detached child through the **pidfile** path (the stubbed `ss` reports
    no listener, so kill-by-port cannot be what fired), removes the target file, releases the lockdirs, writes `teardown.json`, and preserves `artifacts/`.
  Live `cascor_up` / `canopy_up` compose pins (`TestCascorUp` / `TestCanopyUp` — fake `conda.sh` + PATH stubs; juniper-ml#813). Wired into `ci.yml` beside the `test_juniper_{plant,chop}_all.py` launcher tests.
  - Live compose coverage for `data_up` (`TestDataUpLive`: venv create/skip, pip extras, `PYTHON_GIL=0`, pidfile, missing-`python3.14` abort — juniper-ml#807).
- `tests/test_run_experiment.py` -- Hermetic tests for `util/experiments/run_experiment.py` (CLI experimentation plan Waves 2.2-2.6: the cascor + recurrence service paths, the §8.1 + §8.2 plot sets, and the §8.3 stats/summary renderers (e2e stats assertions for both kinds + every-outcome coverage + the `StatsSummaryUnitTest` percentile/delta/grouping/degraded-notes units) --
  plot arms cover all-rendered PNGs for both kinds (sequence-NPZ stub artifact for §8.2), per-kind plot-name validation, skip-vs-acceptance semantics (eval-disabled / degraded-sampling / disabled-phase skips, matplotlib-unavailable failure), and the `plots_cascor.py` / `plots_recurrence.py` renderer units incl. the `y_reg_` target-key preference;
  `util/` is not pre-commit-lint-gated, so this unittest is the gate). A scripted stub HTTP server stands in for juniper-data, cascor, and recurrence (no live services): the
  §5.6 YAML validation arms (unknown block/key, `schema_version`, mandatory `experiment.seed`, the rule-6 infra-key rejection, kind resolution, the §5.5 recurrence blocks
  incl. `dataset.split` / `crossval.n_folds` / `predict.from_dataset_split`), the cascor drive loop (completion / `FAILED` / Q-2 stall / wall-clock budget with
  CLI-beats-YAML precedence), the F-1 `/metrics` 307-redirect sampling arm + the G-3 404 degrade, the G-6 staging path (alias map, no inline `dataset` on start,
  shape-assert pass/mismatch, unstageable-generator refusal), the recurrence path (synchronous train 200/409/422/socket-timeout arms, predict/crossval `dataset_id` refs +
  record-and-continue on failure, the G-18 `save_model` CLI re-run via a PATH stub + missing-CLI acceptance failure), `ports.json` endpoint resolution, the §13.4 manifest
  written for every outcome, and the full 0/1/2/3/4 exit matrix incl. `RedactedEnv` subprocess arms.
- `tests/test_experiment_config_schemas.py` -- Wave 3.5 drift gate (§10.6 row 3): walks the sibling checkouts' `conf/experiments/*.yaml` (cascor Wave 3.2, recurrence Wave 3.4) and asserts each loads through the driver's §5.6 `load_config` AND that every `service:` key names a real app `Settings` field --
  extracted statically via AST (cascor `Settings`; recurrence `Settings` + the in-repo service-core `SettingsBase`), so no torch-heavy app import is needed. Cross-repo walk gated like `test_doc_tools_drift.py` (`GITHUB_ACTIONS=true` or `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`; sibling-absent skips loudly); the AST-extractor self-check always runs.
- `tests/test_experiment_suite_yamls.py` -- Drift gate (R-6) over the shipped suites in `util/experiments/suites/**`, which no test loaded before it: every suite must pass `run_suite.load_suite` (catching the unknown-`execution:`-key / `stall_second` typo class that otherwise surfaces hours into a GPU campaign), and any oversize `app: cascor` suite must declare an `execution.stall_seconds` above the driver's `DEFAULT_STALL_SECONDS` (read from the driver source, not hardcoded).
  - **Oversize is pool OR cap.** The original gate triggered on `candidate_pool_size >= 16` only, so a wide-**cap** suite at a modest pool shipped and then lost its widest cells to a false `stalled` hours in — the candidate phase slows every iteration as the cascade widens each candidate's input, i.e. "the ml#1069 class, arriving through width instead of through pool size" (`suites/p4/e-i-cascor-cap-ceiling.yaml:46-50`). `max_hidden_units >= 64` now triggers too.
  - **Third contract — wide-cap suites must pin a wall budget**, via either `execution.max_wall_seconds` or a dotted `outputs.max_wall_seconds` override (E-I uses the latter, so accepting only the former would fail a correctly-budgeted suite). Thresholds are measured, not guessed: E-I at fixed pool 8 ran cap 32 → 1497.4 s, cap 64 → 2907.1 s, cap 128 → **4243.6 s** against a 3600 s inherited default, so 128 would have been truncated and 64 clears by only 693 s.
  - **Known limitation**: only the suite's own `matrix` / `include` are read, so a pool or cap inherited from `suite.base_config` is invisible — deliberate, because resolving `base_config` reaches into sibling repos and would turn a structural gate into one that skips whenever the ecosystem is not checked out.
  The Q-2 detector watches `current_epoch`, which does not advance while the CANDIDATE pool trains, so those cells are recorded `stalled` while perfectly healthy -- the P4 E-A grid lost its pool-16 cells to exactly that. Structural only: deliberately never calls `expand_cells`, which would resolve sibling-repo `base_config` and turn the gate into a skip. Carries a negative control plus an anti-resurrection check for the retired `util/ad-hoc/2026-08-10_driver_stall_shim.py`.
- `scripts/test.bash` -- Manual end-to-end harness for session create/resume launcher flows
- `scripts/test_resume_file_safety.bash` -- Regression script ensuring invalid `--resume <file.txt>` input does not delete the source file

---

## Utility Script Reference

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

- `util/worktree_cleanup.bash` -- Automated worktree cleanup with CWD-safe session continuity (V2 procedure). `MAIN_REPO` derives from `${BASH_SOURCE[0]}` (one dir up) with a `JUNIPER_ML_MAIN_REPO` override for test fixtures. Flags: `--old-worktree`, `--old-branch`, `--parent-branch`, `--new-worktree`, `--new-branch`, `--skip-pr`, `--skip-remote-delete`, `--dry-run`. Phase 7 always restores the primary checkout to up-to-date `main` (skips on dirty tree or checkout refusal; F-6 stale-checkout class).
  - Phase 1: non-empty `status --porcelain` in the old worktree → `exit 1` (`Commit or stash…`) before any push; `--dry-run` skips the check. Clean tree then pushes when ahead / `-u` when no upstream / skips when synced. Phase 2 refuses an existing `NEW_WORKTREE` path (`exit 1`, never clobbers).
- `util/reap_pytest_orphans.bash` -- Safely reaps orphaned Juniper pytest multiprocessing children (`--dry-run` / `--verbose`).
  - Candidate awk gate: current-user + `/python/` + (`JuniperC[a-z0-9]+` conda path or `Juniper/worktrees/`); empty set exits 0 with "No Juniper python processes found."
  - Orphan when ppid is `1`, user `systemd --user`, or parent gone; live parents KEEP. `SKIPPED` on ps→gone race or missing `PPid:` (never kill).
  - **Live-experiment protection, checked BEFORE the orphan predicate.** `experiment_stack.bash` / `isolated_stack.bash` launch services under `nohup` in a subshell, so they reparent to `systemd --user` — the orphan predicate itself; orchestrators / watchdogs started with `setsid`/`disown` land there too.
  - Two protection keys, either sufficient: **P1** the pid is in a run-dir `*.pid`; **P2** the pid's cmdline references a run root (`JUNIPER_EXP_RUN_ROOT`, default `~/.local/state/juniper-experiments`, or `JUNIPER_E2E_RUN_DIR`). Prints `PROTECT` **always** (not `--verbose`-gated) and counts separately.
  - Observed live 2026-08-16 on campaign `e-j-h2h-wide-cap6`: a dry run called the orchestrator, the experiment cascor service, and the watchdog all `WOULD REAP` while healthy. Over-protection is the deliberate safe direction — a stale pidfile still protects.
  - Test hooks: `JUNIPER_REAP_PROC_ROOT`, `JUNIPER_REAP_KILL_CMD` (plus the two run-root vars, redirected per-test). Operator surface: [docs/REFERENCE.md § Pytest Orphan Reaper](#pytest-orphan-reaper).
- Documentation link validator now lives in [`juniper-doc-tools/`](juniper-doc-tools/) and is published to PyPI as `juniper-doc-tools` (Wave 4 of the doc-link migration plan; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`).
- `util/requirements_drift_check.py` -- Drift checker for the requirements snapshot at `notes/requirements/id_assignments.yaml`. Default `--mode quick` validates path resolution + structural line-range integrity for every citation; emits a human report or `--json`. Exit code 1 on any drift. Implements the spec in [the requirements next-steps doc §7](../notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection); `--mode full` / `--mode rewrite` are reserved for future work.
- `util/template_data_resolver.py` -- Loader + dotted `resolve()` for the custom-agent suite data layer (`prompts/agent_templates/data/*.yaml`: standing rules, anti-hallucination doctrine, conventions, ecosystem facts, known-misses ledger). Path-invoked (`python util/template_data_resolver.py conventions.handoff_threshold`) or imported; the Template Agent maps these into template slots and RUBRIC R2.5 checks injected conventions against them. Tests: `tests/test_template_data_resolver.py`.
- `util/template_select_preview.py` -- Offline preview of the Template Agent's category selection (P2): given a task string, prints which template the Skill's `match_signals` step would pick (matched keywords + ranked runner-ups). A preview heuristic (keyword-substring scoring; `generic` fallback), not the Skill's exact judgement. `python util/template_select_preview.py "TASK" [--repo-root P] [--json] [--top N]`; exit 0 always. Tests: `tests/test_template_select_preview.py`.
- `util/editable_install_drift_check.py` -- Drift checker for juniper editable installs in the conda environments. Reads each env's `*.dist-info/direct_url.json` directly (robust to broken envs); classifies every `juniper-*` editable as `FRESH` / `WORKTREE_PINNED` (under a `worktrees` path) / `ORPHANED` (missing). `*-DEPRECATED` skipped by default; exit 1 on ORPHANED; `--json`; `--fix` re-points orphans to their canonical repo (`--dry-run` previews).
  - **Version axis** (`MATCH` / `STALE` / `UNKNOWN`), orthogonal to the path axis: compares the version the install RECORDED at pip time against the version its target declares NOW. An editable never re-derives its version — `import` follows the live tree while `*.dist-info/METADATA` stays frozen — so a `FRESH` install can be badly stale.
  - Blind spot it closes: on 2026-08-14 **7 of 8** installs on this host were FRESH *and* stale (juniper-data 5 minors behind, `0.6.0` vs `0.11.0`), invisible to both the path axis and `juniper-env-drift-check`'s floor check — a stale editable sits above every floor and is still wrong. It breaks whatever reads the *installed* version: a repo's `version == pyproject` self-check (cascor's `test_version_matches_pyproject`) and a host-launched service's build-info metric.
  - STALE is **soft** (exit 0 — `import` still resolves); `--strict-version` makes it exit 1, while `--strict` stays about the path axis. `--fix-stale` refreshes stale installs against the path they ALREADY point at (`drift: "stale-metadata"`) rather than a canonical-discovery result, which would risk re-pointing a deliberate checkout; ORPHANED repair is unchanged (`drift: "path"`).
  - Dynamic versions are read only from an explicit `[tool.setuptools.dynamic] version.attr` (flat or `src/`) / `[tool.hatch.version] path` declaration — an unrecognized backend reports UNKNOWN instead of guessing at a `_version.py`. Operator surface: [`docs/REFERENCE.md` § Editable Install Drift Check](#editable-install-drift-check).
  - Ambiguous canonical (juniper-ml#795 coverage): `discover_canonical` returns `(None, [.., ..])` when two+ non-worktree checkouts share a `[project].name`; `--fix` then `action=SKIP` with `reason` containing `ambiguous` (never picks `candidates[0]`). Operator surface: `docs/REFERENCE.md` Editable Install Drift Check + cheatsheet tip.
  - Live `--fix` actions (juniper-ml#802 coverage): `run_fix` marks `FIXED` on successful `pip install -e <canonical> --no-deps --force-reinstall`; `OSError` / `CalledProcessError` become `action=ERROR` (stderr truncated to 500 chars) without aborting later plan items; after a non-dry run, `main` re-scans so exit `1` still reflects remaining orphans. Operator surface: `docs/REFERENCE.md` Editable Install Drift Check + cheatsheet tip.
- `util/env_floor_drift_check.py` -- Floor-drift checker (gap I-2): reads each installed `juniper-*` version from its `*.dist-info/METADATA` and compares to the target repo's `pyproject.toml` floors -> `OK` / `BELOW_FLOOR` / `MISSING` -- the below-floor plain-wheel case the pins/editable checkers miss. Env selection is data-driven (`--site-packages`/`--env`/`ecosystem.yaml`); exit 1 on `BELOW_FLOOR` (`--strict` also `MISSING`); `--json`; structural CI gate. Tests: `tests/test_env_floor_drift_check.py`.
  - `resolve_site_dirs` precedence: `--site-packages` → `--env` → `ecosystem.yaml` `used_by` for `[project].name`; unresolved paths exit 2 with the reason string (never invent an env name). Operator surface: `docs/REFERENCE.md` Environment Floor Drift Check.
  - Multi-site / multi-interpreter: `installed_juniper_versions` keeps the **highest** version across site-packages dirs; malformed / unreadable `METADATA` and non-`juniper-*` are skipped. Coverage: open #796 / #802.
- `util/release_train/` -- PyPI release-train tooling (release-train plan §12). `registry.yaml`: the data-driven 18-package / 8-repo registry (§4.1). `detect.py`: the per-package "needs a PyPI deploy?" engine (§4.2/4.3, Phase 1, report-only) -- PyPI truth vs declared version, tag-matched diff base, `gh compare` (`--local-git` fallback past the 300-file cap), and a substantive-hunk SHIP filter discounting the notes-rename comment/docstring/link class; report-only, exit 0/1/2.
  - SHIP / SemVer edges: whitespace + pure comment deletion discounted; pure code deletion ships; `local_git_compare` A/D/R/**C** of a `.py` module is inherently substantive (no blob compare); Keep-a-Changelog `Security` → patch, `Changed`/`feat!`/`BREAKING CHANGE` → minor pre-1.0. Operator tables: release-train operator runbook §3.1.
  - Soft-fail `SHIP_UNCERTAIN` (unreadable declared version / missing tag / `comp.ok=False` / truncated empty window / patch-uncertain) is an action class — never silent `UP_TO_DATE`.
  - Hygiene `list_releases` `SourceError` sets `tag_only=None` + an unavailable note (does not exit 2 or invent TAG_ONLY). Offline `--local-git` must raise (open #773), not return `set()`. Operator tables: release-train runbook §3.1.
  - On the live daily path a Releases-API 404 / `None` from `_gh_lines` must **raise** rather than coerce via `or []` into an empty set — an empty set makes `diff_base_tag not in releases` always true and yields a false TAG_ONLY for every package. An *authenticated* empty Releases list remains a genuine TAG_ONLY.
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
  - `touches_releases` inspects **both** sides of a rename/copy so a rename-OUT of `notes/releases/` is still an archive PR and FAILs (never SKIP). Copy (`C`) and Typechange (`T`) are non-`A` and FAIL rule1. Operator triage: release-train runbook §3.3.
  - `Allow-Archive-Edit: <path>|<basename>|*` commit trailer (house `Allow-*` idiom; injected via `--trailers-file`, produced by `ci.yml` from `git log --format=%B FETCH_HEAD..HEAD`) waives rules 1/4 for in-place edits of FLAT `notes/releases/RELEASE_NOTES_*.md` files -> distinct `WAIVED` verdict (exit 0, waived paths named); anything dragging an out-of-archive or nested path still FAILs. The #1003 link-repair class / issue #1013. **Carry the trailer into the squash commit message.**
- `util/release_train/ceremony.py` -- Exempt-archive + Release ceremony (Phase 3.2, plan §7/§8/§10) for `BUMPED_NOT_RELEASED` packages: §8 preconditions (each HALTs + dedup issue), notes from the CHANGELOG `[<version>]` section, open the exempt archive PR (signed API commit), enable auto-merge, cut the Release (`--latest=false`; no `--verify-tag`), monitor -> `PENDING_PYPI_APPROVAL`. R7 gh-surface allowlist; idempotent re-entry. **`--dry-run` writes nothing.** Tests: `tests/test_release_train_ceremony.py`.
  - Signed-archive re-entry: reuse tip-at-base / single-commit-atop-base; HALT on unresolvable base/tip, non-422 refs errors, or diverged branch (never invent a sha). Operator table: release-train operator runbook §3.3.
  - Open archive-PR reuse (juniper-ml#730): `enable_automerge(…, pr_ref or plan.archive_branch)`; archive-already-on-main → release only; Release-exists → `RESUME_MONITOR`.
  - Precondition: `notes-render-failed` HALTs when `notes_render.render_notes` raises `OSError` (missing/unreadable `TEMPLATE_RELEASE_NOTES.md` / security template) — restore the template, re-run; never invent archive body. Operator catalog: release-train operator runbook §4.
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
  - **Defense in depth, not the control.** Anyone who can edit a workflow can delete this step; the environment tag policy is what survives that. Value here is failing earlier, naming the reason, and keeping the invariant visible in the repo.
  - `--ref` / `--dist-dir` / `--expect-prefix`; exit 0 pass / 1 assertion failed / 2 misuse. Tests: `tests/test_assert_release_tag.py` (wired into `ci.yml`'s Regression Tests — `util/` is outside every pre-commit Python hook's scope, so that suite is the gate).
    - **`--ref` takes the fully-formed `github.ref`** (`refs/tags/<tag>`), NOT `github.ref_name` plus a separate `github.ref_type`. The two-flag form was deliberately rejected (`util/assert_release_tag.bash:38-44`): `ref_type`'s value on a `release` event is far less clearly specified, and an assumption that is wrong there "does not fail safe, it fails EVERY publish". This line documented the rejected form until 2026-08-19 — a caller following it got `unknown argument` → exit 2 on all 7 publishers.
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
  - **Kill-proof net (RC-4):** whenever there is something to wait for, the merge is ALSO handed to GitHub via `gh pr merge --auto`, so a killed run does not strand it. Gated on the repo's `allow_auto_merge` -- where that is false `--auto` does not arm but falls back to an **immediate merge**, which with the owner's `always` bypass could land a PR whose checks never finished.
    Enabled fleet-wide 2026-08-19 (`util/ad-hoc/2026-08-19_enable_allow_auto_merge.py`); the gate stays because a setting can be switched off again. Not armed on an already-green PR (there `--auto` merges at once, skipping head pinning). `--no-auto-fallback` opts out.
  - **Net armed on `BLOCKED` / `BEHIND` / `UNKNOWN`** (`ARMABLE_STATES`, fixes D1). It previously armed on `BLOCKED` only, while the `BEHIND` branch `continue`d past the arming site — so the **post-sync full CI re-run, the longest and most kill-exposed wait the tool performs, was the one wait entered with no net**. That is the exact shape of the incident. Arming now happens *before* the `update-branch`, covering the sync itself.
  - **A refusal disarms the net** (`disarm_auto_merge`, fixes D3). Previously a refusal left a live server-side auto-merge, so a stated refusal could still become a merge minutes later — observed live on ml#1185. The disarm wraps *every* refusal path at one choke point rather than at each `raise` site. If the teardown itself fails the refusal says so **loudly** and names the PR; that is the one state where a refusal and a live net coexist.
    **Ordering is load-bearing:** D1 strictly increases the number of refusals that would leave a live net, so D3 must hold before D1 widens the exposure. Never ship D1 alone.
    Exit **4 (INTERRUPTED) deliberately does NOT disarm** — surviving the kill is the entire point of the net — and the interrupt message now says so and prints the `--disable-auto` command, instead of the previous flat "nothing was merged".
  - **`UNKNOWN` is re-polled, not refused** (fixes D2). GitHub reports `mergeStateStatus=UNKNOWN` while recomputing mergeability, routinely for seconds after an `update-branch`; treating it as a verdict produced spurious refusals indistinguishable from real blockers. Bounded by `MERGEABILITY_POLLS` x `MERGEABILITY_INTERVAL`.
  - **The armed net is pinned at ARMING time only** (D4, now fixed — and the fix rests on a measurement, not a reading of the docs). Both paths pass `--match-head-commit`: the local one at merge time, the net via `EnablePullRequestAutoMergeInput.expectedHeadOid`.
    **Measured (probe ml#1225, 2026-08-21):** armed a net *with* a pin, pushed a commit to move the head, re-read the PR — `autoMergeRequest` was **still present with an unchanged `enabledAt`**, so it had neither been dropped nor silently re-armed. `expectedHeadOid` is therefore an **enable-time optimistic-concurrency guard**, not a continuous constraint.
    That distinction was load-bearing and is why it was measured rather than assumed: had it been continuous, pinning would kill the net the moment GitHub moved the head itself to satisfy `strict` — i.e. exactly when the net matters — silently negating the D1 fix. A *push* is a stronger head move than GitHub's own sync, so the probe settles the case that mattered.
    What pinning buys: the net cannot be armed over a **stale read**. What it still does not buy: once armed, the net merges whatever head is current when the checks pass. So the net carries *"merges only when required checks are green"* but not *"merges only the SHA this run vouched for"* — callers needing the stronger property use `--no-auto-fallback`.
    Note the flag needs the **full 40-char OID** (`headRefOid`); an abbreviated SHA is rejected with `Could not coerce value ... to GitObjectID`.
  - **Not enforcement.** A script can be skipped; the owner's `always` ruleset bypass is what makes required checks advisory for that actor. `python util/safe_merge.py --pr N [--repo R] [--execute]`; **`--dry-run` is the default**. Exit 0 merged / 1 refused / 2 misuse / 3 hard error / **4 interrupted**. Tests: `tests/test_safe_merge.py`.
- `util/memory_budget_check.py` + `util/relocation_check.py` -- Memory-size gates (ADVISORY `Memory Budget` job). **Don't grow `AGENTS.md`: relocate to `docs/REFERENCE.md`, leaving a pointer that keeps an accurate open/closed status.** G3 proves a relocation moved the *prose*, not just the identifiers — the docs screen cannot see that shape. `Allow-Budget-Overrun:` is a loan, not a pass. [Budget](#memory-file-size-budget) / [G3](#relocation-completeness-g3).
- `util/open_signed_pr.py` -- Opens a PR on any Juniper repo whose commit is **GitHub-signed**, by creating branch + commit + PR through the API (`createCommitOnBranch`) instead of a local checkout. Promoted from `util/ad-hoc/` after it landed the ml#1099 signing fan-out across 8 repos.
  - Why it exists: `required_signatures` (2026-08-12) rejects unsigned commits fleet-wide, GPG/YubiKey signing is unavailable to a runner, and an unsigned commit **anywhere** in a branch's history blocks the merge (squash does not rescue it). GitHub signs API-authored commits, so this is the portable way to land a signed change. It needs no working tree, which also makes it the path of choice when a session is confined to one worktree and cannot commit in sibling checkouts.
  - `python util/open_signed_pr.py --repo R --branch B --add LOCAL:REPOPATH [--delete REPOPATH] --message M --title T --body-file F [--base main] [--owner pcalnon] [--dry-run]`. `--add` / `--delete` are repeatable and together express a file move; at least one is required. Exit 0 opened / 1 refused / 2 hard error.
  - Safety: refuses on an existing open PR for the branch (dup-guard -- concurrent sessions are a real hazard here) and on an existing branch (never force-updates another ref); `expectedHeadOid` is pinned to the resolved base sha so a concurrent push fails loudly rather than clobbering; `--dry-run` resolves read-only and writes nothing. Mirrors `util/release_train/propose.py`'s `create_signed_commit`. Tests: `tests/test_open_signed_pr.py`.
- `util/wait_for_checks.py` -- Waits for a PR's **required** status checks to finish, then reports honestly. The shared replacement for the hand-rolled "wait for CI" loops that sessions keep re-writing and keep getting wrong the same two ways. Read-only (only `gh pr view` / `gh api .../rules/...` reads — never merges, updates a branch, pushes or comments), so any session can run it at any time.
  - `python util/wait_for_checks.py --pr N [--repo juniper-cascor] [--owner pcalnon] [--anchor required|observed] [--fail-fast] [--timeout 1800] [--interval 20] [--json] [--verbose]`. Exit **0** all required green / **1** a required check failed (named) / **2** timeout with the still-running and never-reported contexts named / **3** hard error.
  - `--fail-fast` returns on the first failed required context instead of waiting for the full picture. The result also carries a `stalled` flag — true when nothing is in flight **and** something failed **and** required contexts are still absent, which means those absent contexts are downstream jobs (`needs:` a failed job) that will never report, so further polling cannot change the answer. Found by dogfooding: the tool burned 27 polls in exactly that state on its own PR.
  - **Trap 1 — terminal is defined POSITIVELY.** An in-flight check run carries `conclusion: null` and no `state`, so a loop written as "not in my list of pending states" reads it as finished. The pending set is open-ended (`QUEUED`/`IN_PROGRESS`/`WAITING`/`REQUESTED`/…); the finished set is closed. `is_terminal` therefore asks "is it definitely done?" and an unrecognized future conclusion reads as unfinished.
  - **Trap 2 — the rollup GROWS, so "everything I can see is done" is not "the suite is done".** Jobs are appended to `statusCheckRollup` as they start, so a lull between waves (pre-commit matrix finished, test matrix not yet created) is indistinguishable from completion.
  - The only stable anchor is therefore the branch ruleset's **required** contexts; a required context that has not appeared is `absent`, not `running`. `--anchor observed` reproduces the buggy behaviour and is opt-in only — `tests/test_wait_for_checks.py` pins both anchors side by side so the difference is executable, not just asserted.
  - `absent` is deliberately its own bucket: a required context that never reports may never report (the `[skip ci]` head-commit orphan class, where the aggregate rollup can read SUCCESS while the PR is permanently unmergeable), so the tool names it instead of waiting mutely.
  - A `gh` non-zero exit is a `ProbeError` → exit 3, never a silently-empty result; that conflation is the same class as trap 1. A missing `required_status_checks` rule is likewise a hard error rather than a quiet downgrade.
  - Probes retry up to `PROBE_RETRIES` (3) times with backoff. The retry is **delay-only** and never classifies errors as transient-vs-permanent — a genuinely broken probe fails every attempt and still raises, so the honesty property holds. It exists because two of the first three live runs died on a transient `TLS handshake timeout` / `unexpected EOF`, discarding a wait that was minutes from finishing.
  - `mergeStateStatus` is reported but never gated on. `BEHIND` is branch freshness, not check completion — all 9 repos set `strict_required_status_checks_policy: true` ("Require branches to be up to date before merging"), which is a **different** setting from the removed `update` rule ("Restrict updates"); the signing-safe fix is `gh api repos/<owner>/<repo>/pulls/<n>/update-branch -X PUT` (server-side, therefore GitHub-signed). Tests: `tests/test_wait_for_checks.py`.
- `util/ad-hoc/` -- Home for single-use / temporary / unfinished scripts. See `util/ad-hoc/README.md` for file-header conventions and graduation lifecycle. `/tmp/` is prohibited for script source files per the [Script placement](../AGENTS.md#script-placement-mandatory) rule.
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
- `util/isolated_stack.bash` -- Brings up / tears down the isolated training-runtime E2E trio (data 8101 dedicated `python3.14` venv, cascor 8202 `JuniperCascor1`, canopy 8051 `JuniperCanopy1` service mode) with the documented env (control-WS origin pair, `JUNIPER_DATA_URL`, `LD_LIBRARY_PATH=`); `--up`/`--down`/`--status`/`--dry-run`, ports 8101/8202/8051 (`JUNIPER_E2E_*` overrides), `--dry-run` starts nothing. See [E2E checklist](../notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md).
  - Live compose (juniper-ml#813): `cascor_up` empties `LD_LIBRARY_PATH`, points `JUNIPER_DATA_URL` at isolated data, sets control-WS allowlist to `CANOPY_ORIGIN`, writes `juniper-cascor.pid`, then health-gates; `canopy_up` forces `DEMO_MODE=0`, wires isolated cascor/data URLs + matching `CASCOR_WS_ORIGIN`, writes `juniper-canopy.pid`, then health-gates. Missing `conda.sh` aborts before launch/pid. Operator details: [`docs/REFERENCE.md` Isolated Stack E2E](#isolated-stack-e2e-utilities).
  - `data_up` (juniper-ml#807): dedicated `${RUN_DIR}/.venv-data` via `python3.14 -m venv` (skip create if present), `pip install -e juniper-data[${JUNIPER_E2E_DATA_EXTRAS:-api}] prometheus_client juniper-observability`, launch with `PYTHON_GIL=0`, write `juniper-data.pid`, health-gate; missing `python3.14` aborts via `require_cmd` before side effects. `do_up` order is data → cascor → canopy.
  - Nounset (juniper-ml#785): `activate_conda` must `set -u` after `conda activate` (matching plant `safe_conda_activate`); pre-#785 left `set +u` so live `--up` ran without nounset after cascor/canopy activate.
  - Partial-failure teardown: `do_up` absorbs each leg as `*_up || failed=1` and on failure logs `bring-up failed — tearing the partial trio back down`, then calls `do_down` (experiment_stack parity) so a mid-bring-up failure cannot orphan listeners on 8101/8202/8051. Because the OR-list disables `set -e` inside each `*_up`, critical steps must end with `|| return 1` or a mid-function failure false-greens.
  - Fail-closed `activate_conda` under those OR-list callers: `source … || return 1` and `if ! conda activate …; then set -u; return 1; fi` (both arms restore nounset). A bare activate followed by a successful trailing `set -u` would return 0 and launch cascor/canopy on the ambient PATH.
  - Teardown: `--down` is kill-by-port via `port_pid`/`stop_port` (`ss` first `pid=`), canopy→cascor→data, then RUN_DIR + `snapshot_*` cleanup — not `JuniperProject.pid`. Empty/`ss` soft-fail is a noop; `--dry-run` never kills.
  - Health: `wait_for_health` polls `/v1/health` every 2s until `JUNIPER_E2E_HEALTH_TIMEOUT` (default 60); `--status` `probe_health` reports code + pid and does not fail the script. Operator details: [`docs/REFERENCE.md` Isolated Stack E2E](#isolated-stack-e2e-utilities).
- `util/experiment_stack.bash` -- Brings up / tears down a **per-run** experiment stack (dedicated juniper-data + `--cascor` and/or `--recurrence`; never canopy) for the
  [CLI experimentation plan](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §6.2 (Wave 2.1).
  `--up` (with `--shared-data URL` / `--config PATH` / `--experiment NAME` / `--grafana-bridge`), `--down <RUN_ID>|--all-mine`, `--status [RUN_ID]`, `--dry-run`; misuse exits 2.
  Services launch from direct env-bin paths (`JUNIPER_EXP_CONDA_DIR`, default `/opt/miniforge3`) with the §6.1 env sets verbatim: `PYTHON_GIL=0` + per-run
  `JUNIPER_DATA_STORAGE_PATH`/`_EQUITIES_CACHE_DIR`; cascor `LD_LIBRARY_PATH=''` + `uvicorn api.app:create_app --factory` from `juniper-cascor/src` with AUTO_START off;
  recurrence `serve` with metrics on / rate-limit off — all three metrics toggles on and `JUNIPER_DATA_URL` at the run's data port.
  - RUN_DIR contract (§6.4): `RUN_ID=<UTC yyyymmddThhmmssZ>-<4 hex>` under `JUNIPER_EXP_RUN_ROOT` (default `~/.local/state/juniper-experiments` — under `$HOME`, **not** `/tmp`,
    so a reaped sandbox cannot destroy results, H-15); everything (pidfiles, `logs/`, `relays/`, `config/`, `env/launch.env`, `data/`, `equities-cache/`,
    `artifacts/{plots,results}/`, `ports.json`, `teardown.json`) lives inside it. `JuniperProject.pid` is never read or written, no repo `.env` is ever written (all per-run
    config is process env, H-3), and operator ports 8100/8200/8201/8210/8050 are never touched.
  - Ports (§9.3): first free port in data `8110-8139` / cascor `8230-8259` / recurrence `8260-8289`, claimed by an atomic `mkdir "$LOCK_ROOT/<port>.lock"`
    (`JUNIPER_EXP_LOCK_ROOT`, default `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments`) plus an `ss` probe, released at teardown. The lockdir serialises experiment launchers
    against each other; the residual race vs a non-participating binder is deliberately left to surface as the service's own bind failure through the health gate (H-1).
  - **F-6 pid rule (binding)**: `$!` after `( cd … && nohup <server> … & )` is the backgrounded **subshell**, not the server, so no `*_up` records it. Each service's pidfile
    is written by `record_listener_pid` from `ss -tlnpH "sport = :<port>"` **after** the health gate, with the process cmdline stored alongside; teardown kills pidfile-first
    and only after proving the pid is alive, owned by the current uid, and still running the recorded cmdline (SIGTERM then bounded SIGKILL). If the pidfile path refuses
    (pid gone / wrong uid / cmdline mismatch), `stop_service` logs `pidfile path refused — falling back to the recorded port <N>` and kills via `ss` only on that run's
    recorded port. `artifacts/` is never deleted.
  - Partial-failure teardown: `do_up` writes `ports.json` before any `*_up`; on `failed=1` it logs
    `bring-up failed — tearing the partial run back down` and calls `teardown_run` (live only; not `--dry-run`), keeping `logs/` + `artifacts/` and releasing lockdirs.
  - Health: `wait_for_health` polls `/v1/health` (data, cascor) and `/v1/health/ready` (recurrence) every 2s until `JUNIPER_EXP_HEALTH_TIMEOUT` (default **90** — F-8 sizes it
    for a cold start; the 1.1 s warm number is not the design point).
  - **Dead-process fast-fail**: `wait_for_health` takes an optional 4th arg, a `pgrep -f` liveness pattern, and each leg passes a **port-scoped** one (`-m juniper_data .*--port
    ${DATA_PORT}` / `api.app:create_app .*--port ${CASCOR_PORT}` / `juniper-recurrence serve .*--port ${RECURRENCE_PORT}`) so a sibling run can never satisfy this run's gate.
    Two **consecutive** misses end the wait with `process is gone … died during startup` naming the leg's log, instead of burning the full 90 s per leg on a process that already
    exited (the P4-campaign class). Two misses, not one, and the first probe runs after the first sleep — the launch subshell returns before its child execs, so fork+exec keeps a
    >=4 s grace. **F-6 intact**: the pattern is only ever read; it never resolves a pid and never kills. No `pgrep` on PATH degrades to the prior timeout-only behaviour (an
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
    Without it `--status` reports the run as UNSCRAPED.
- `util/experiments/run_experiment.py` -- Single-run experiment driver (plan §6.3; Wave 2.2 = the cascor **service** path, Wave 2.3 = the recurrence **service** path, Waves 2.4/2.5 = the §8.1/§8.2 plot sets via `plots_cascor.py` / `plots_recurrence.py` (2.5 closes G-5), Wave 2.6 = the §8.3 stats/summary via `stats_summary.py`).
  - Stats (§8.3): every run also writes `artifacts/results/stats.json` + human-readable `summary.md` (stdlib-only renderer, every outcome incl. stalled/failed): identity / dataset-shape (tabular vs sequence from meta) / outcome-timing blocks from the manifest, cascor candidate-correlation-per-round + step-duration p50/p95 from the driver's own `metrics_series.csv` (honestly labeled per-poll means -- true per-step quantiles are not recoverable from a sum/count exposition), the recurrence train/CV/θ/readout block.
  - Stats degraded-mode notes surface G-3 sampling errors, collect errors, plot skips, eval-disabled, and G-6 failures; a stats failure is recorded on the manifest (`stats_error`), never fatal.
  - Recurrence plots (§8.2): `dataset_overview` (sampled 3-D windows, target starred), `dt_histogram` (per-step Δt + `target_dt` -- the irregularity signature; skips non-Δt artifacts), `forecast_vs_truth` + `residuals` (predict response vs the predict split's target, `y_reg_{split}` preferred over `y_{split}` -- the equities regression target; residual-vs-`target_dt` panel when available), `crossval_folds` (per-fold eval bars + aggregate line), `metrics_table` (train + CV ± std).
  - A disabled/failed predict or crossval phase is a per-plot SKIP. Deliberately NO recurrence training-history plot (TrainResponse carries no per-epoch series -- §8.2 note).
  - Plots (§8.1, `outputs.plots`, validated per kind): `dataset` (fetched NPZ artifact scatter; 2-feature generators only), `decision_boundary` (collected grid + sample overlay), `training_history` (history rows, hidden-unit-insertion markers), `candidate_correlation` (from the driver's own `metrics_series.csv` -- the sole source), `eval_metrics` (scalar bars) -- rendered client-side by `plots_cascor.py` (lazy-loaded, Agg backend; NEVER imports cascor, whose plotter imports torch).
  - Plot semantics: structurally-unavailable data = recorded per-plot SKIP (exit 0); a render error / failed fetch / missing matplotlib on a requested plot = acceptance failure (exit 1); the manifest `driver.plots` block records requested/rendered/skipped.
  - A renderer `ValueError` is the explicit **no-renderable-data contract**: recorded as a per-plot SKIP only, with no PNG and no acceptance error (exit 0) — distinct from a non-`ValueError` render exception, a failed payload fetch, or a
    missing matplotlib on a requested plot, which are SKIP **and** acceptance failure. Soft edges that deliberately do not raise: a misaligned optional `target_dt` just omits the residual-vs-dt panel, and an empty `eval_aggregate` falls
    back to `folds[0].eval_metrics`. Operator table: [`docs/REFERENCE.md` § Plot SKIP vs acceptance](#plot-skip-vs-acceptance-valueerror-contract).
  Path-invoked: `python util/experiments/run_experiment.py --config <yaml> --run-dir <RUN_DIR>` against a stack from `experiment_stack.bash` -- service URLs resolve from the run's `ports.json` (`--data-url` / `--cascor-url` override). Stdlib + PyYAML; numpy lazily only for the `.npz` artifact (JSON fallback); HTTP via redirect-following `urllib` GETs (F-1: bare `/metrics` 307s to `/metrics/`).
  - Validates the §5.4/§5.5 YAML (driver-owned §5.6 subset): unknown blocks/keys rejected, `schema_version` gated, `experiment.seed` REQUIRED (with the `dataset.params.seed` derivation rule + run-scoped default tags), rule-6 infra keys (`service.host/port/juniper_data_url/eval_metrics_enabled`) rejected; `training:` selects the cascor path, `train:`/`crossval:`/`predict:` (+ `dataset.split`) the recurrence path.
  - **`max_epochs` is NOT an all-passes budget on the service — always set `output_epochs` beside it.** `TrainingParams.max_epochs` bounds only the **initial** output pass; every later per-round pass reads `self.output_epochs`, which falls back to `_PROJECT_MODEL_OUTPUT_EPOCHS = 10000` when unset (`cascade_correlation.py:716`, stated outright at `:1876-1882`).
    The direct CLI instead **aliases** `max_epochs → output_epochs` (`main.py:238-249`) so it bounds every pass, and an explicit `output_epochs` wins over the alias (`:291-292`). A config carrying only `max_epochs: N` therefore runs the CLI at N per pass and the service at N then 10000 — several-fold per-pass divergence over a 64-128-unit run, which makes the service both slower and better-trained than the config appears to ask for.
    **Any CLI-vs-service comparison must set both, to the same value.** `load_config` emits a `validation_warnings` entry (carried on the manifest) but never raises — a service-only run may want the split, and `spiral-baseline.yaml` ships that way. Found by juniper-ml#1143 §2.2; gate: `ConfigValidationTest.test_max_epochs_without_output_epochs_warns`.
  - Drive: generator preflight (`GET /v1/generators` must report `available: true`), `POST /v1/datasets` (content-addressed `dataset_id` recorded), then `POST /v1/training/start` and poll `GET /v1/training/status` to `COMPLETED`/`FAILED` under the Q-2 wall-clock budget (`outputs.max_wall_seconds`, CLI `--max-wall-seconds` wins) + stall detector (no `current_epoch` progress for `--stall-seconds`, default 120 -> `outcome: "stalled"`).
  - Every cascor-path generator stages through `POST /v1/training/dataset` (alias map incl. gaussian/checkerboard since W-3, juniper-cascor#490) with a post-run G-6 input-width assert (mismatch = acceptance failure).
    - Spiral joined the staged path with F-P4-1: the old spiral-only inline `dataset` source made cascor materialize its in-process fallback (unit-radius, params silently ignored) instead of the configured juniper-data dataset, terminating every service spiral run below_threshold with zero hidden units.
    - Root-cause note: [`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md`](../notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md); cascor-side fidelity fix cascor#504; candidate-param plumbing gap cascor#505.
  - Each poll samples the loopback `/metrics` allowlist (`candidate_correlation` / `hidden_units_total` / `training_loss` / `training_accuracy_ratio` / step-duration sum+count) into `artifacts/results/metrics_series.csv` -- correlation exists ONLY there, never in `/v1/metrics/history` rows; a 404 (metrics disabled, G-3) degrades sampling, not the run.
  - Recurrence drive (Wave 2.3): health-gates `/v1/health/ready`, then the **synchronous** `POST /v1/train` (the response IS completion — no poll loop; the Q-2 budget is the request's socket timeout → `timed_out`), then optional `POST /v1/predict` (`predict.from_dataset_split`, default `test`) and `POST /v1/crossval` (same LMU hyperparams as `train:` for bench comparability); every phase refs the dataset by content-addressed `dataset_id` (H-8).
  - Predict/crossval failures are recorded and the run continues to the manifest (acceptance failure), never dying mid-evidence. `outputs.save_model: true` (G-18) re-runs the `juniper-recurrence train` CLI with `--dataset <dataset_id>` + identical hyperparam flags + `--out .../model.npz` as a manifest-recorded extra step (the CLI has no `--params` flag, so the dataset_id ref is the only faithful form).
  - Collects `metrics_final.json` / `metrics_history.json` / `topology.json` / `decision_boundary.npz` (2-D input only) + optional `POST /v1/snapshots` (cascor), `train_response.json` / `predict_response.json` / `crossval_response.json` (recurrence); ALWAYS writes the §13.4 `manifest.json` (also for stalled / timed-out / failed runs) and prints a one-screen summary.
  - **409 preempt (§3.4)**: `start_fresh: true` does NOT stop a live run — the lifecycle lock is held, so the 409 is raised before `start_fresh` is consulted, and after a driver-side stall/budget abort the naive re-run dies on `Training already in progress`. A 409 now gets ONE preemption attempt: `POST /v1/training/stop`, wait for the lifecycle to leave the active set, retry start once.
  - Preemption is decided on **lifecycle state, not message text**: cascor's `routes/training.py:117` wraps every start failure as 409 (including "Training data not provided"), so only `STARTED` / `PAUSED` are preempted. `REPLAYING` rejects all training commands (exit is `/replay/control`) and `INVESTIGATING` needs `/retrain` / `/resume` — a stop there would fail and bury the real reason.
  - **Inert stall window**: when `--stall-seconds >=` the resolved wall budget the Q-2 stall detector can never fire (the budget ends the run first) — a healthy long candidate phase is then labelled `timed_out` rather than `stalled`. Reported as a WARNING plus `driver.stall_window_inert` on the manifest, never fatal: the run is valid, only its guard is weaker than declared.
  - The driver is the sole place both Q-2 knobs are resolved, so it is the only layer that can see their interaction — the suite gate structurally cannot, since a budget may be inherited from `base_config` (`pf3-cascor-pool-scaling` shipped exactly this shape: a 1200 s window against a 600 s inherited budget).
  - Exit codes: 0 success / 1 acceptance (stalled, timed_out, G-6 mismatch, missing essential artifact) / 2 misuse-validation / 3 unreachable / 4 FAILED-5xx. Tests: `tests/test_run_experiment.py`.
- `util/experiments/run_suite.py` -- Suite driver. `EXECUTION_KEYS` forwards **both** Q-2 budget knobs to the driver: `execution.stall_seconds` → `--stall-seconds` (ml#1069) and `execution.max_wall_seconds` → `--max-wall-seconds`. Absent key ⇒ flag omitted entirely, so the driver keeps owning its default.
  - Do not confuse `execution.max_wall_seconds` with `execution.per_run_timeout_seconds`: the latter is only the **subprocess** timeout, which kills the driver from the OUTSIDE and records `timed_out` where the driver would otherwise write an honest `timed_out` manifest (§13.4). Size `per_run_timeout_seconds` ABOVE the wall budget so the driver is the one that stops.
  - A suite could always reach the budget through a dotted `outputs.max_wall_seconds` override (`suites/p4/e-i-cascor-cap-ceiling.yaml:71` does exactly that), but before this key an un-overridden cell silently inherited `base_config`'s value — 3600 s for `spiral-baseline` — with no signal. Both mechanisms are accepted by the R-6 gate. Tests: `tests/test_run_suite.py`.
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
│   ├── DOCUMENTATION_OVERVIEW.md         # Navigation index for all docs
│   ├── QUICK_START.md                    # Installation and verification guide
│   ├── REFERENCE.md                      # Extras, compatibility, env vars, service ports
│   └── DEVELOPER_CHEATSHEET_JUNIPER-ML.md# Quick-reference card for development tasks
│
├── conf/                      # Project configuration files
├── images/                    # Project branding (logos v0-v9 in PNG/XCF/ICO, tree photos)
├── logs/                      # Runtime log output (.gitkeep)
├── papers/                    # Research papers and references
├── reports/                   # Per-run evidence artifacts (e2e/<RUN_ID>/statuses.tsv — canopy E2E arc verdicts)
├── resources/                 # External resources (AppImages, etc.)
│
├── notes/                     # Development notes, plans, and procedures
│   ├── JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md       # Worktree creation procedure
│   ├── JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md  # Worktree cleanup procedure (CWD-safe)
│   ├── JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md       # Thread handoff protocol
│   ├── JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md              # Secrets encryption guide
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
│   ├── test_env_repr_safety.py           # Lint gate: no raw os.environ-derived subprocess env in tests/ + RedactedEnv behaviour
│   ├── test_worktree_cleanup.py          # Worktree cleanup script tests (225 lines)
│   ├── test_worktree_sweep_scripts.py    # Ad-hoc sweep script safety/contract tests
│   ├── test_cleanup_session_worktrees.py # Session .claude/worktrees cleaner (merged-PR fail-closed + dry-run)
│   ├── test_reap_pytest_orphans.py       # Orphan pytest process reaper tests
│   ├── test_kill_helpers.py              # Emergency kill helpers: process-filter / kill-path (hermetic PATH stubs)
│   ├── test_check_conda_env_torch.py     # Hermetic P-5 torch._C shadow diagnostic exit matrix (0/1/2/3/4)
│   ├── test_requirements_drift_check.py  # Requirements snapshot drift checker tests
│   ├── test_editable_install_drift_check.py # Editable-install drift checker tests (orphaned / worktree-pinned)
│   ├── test_env_floor_drift_check.py     # Lint/behavioural: util/env_floor_drift_check.py floor-drift (I-2; synthetic dist-info)
│   ├── test_prompt_discovery.py          # Behavioural: util/prompt_discovery/ grounding-bundle (schema + provenance + cold/empty)
│   ├── test_symbol_overlay.py            # Serena symbol overlay (OQ-8) deterministic merge (Serena wins, grep fallback)
│   ├── test_generated_prompt_index.py    # Behavioural: util/generated_prompt_index.py index + safety-gated prune/archive (P4)
│   ├── test_thread_handoff_archive.py    # Drift: archived handoff prompt filenames + top-level note references
│   ├── test_install_agents.py            # Behavioural: util/install_agents.bash ~/.claude mirror (idempotent/reversible/dry-run/no-clobber)
│   ├── test_agent_suite_doctor.py        # Behavioural: util/agent_suite_doctor.py suite health check (dogfood; consumes every layer)
│   ├── test_agent_suite_summary.py       # Behavioural: util/agent_suite_summary.py suite quick-reference (P3)
│   ├── test_predict_merge.py             # Behavioural: util/fleet_triage/predict_merge.py predicted-merge (4 verdicts, TRUE-delta, cluster/order, no-mutate, exit codes; hermetic)
│   ├── test_fleet_supervisor_contract.py # Lint: fleet-supervisor subagent frontmatter + body wiring (predict_merge.py, 4 verdicts, read-only/never-push, two-key DUP-CLOSE)
│   ├── test_workflow_script_paths.py     # Lint: every .github/workflows/*.yml script path exists
│   ├── test_doc_tools_drift.py           # Lint: consumer-repo juniper-doc-tools pins still admit current version (plan §5.1)
│   ├── test_service_fork_drift.py        # Drift gate: security guards that must not diverge across the data/cascor service-core forks (register §2.3; ENFORCED + self-maintaining KNOWN_GAP ledger)
│   ├── test_publish_env_policy_drift.py  # Drift gate: publish envs stay tag-only ref-gated (publish-path design §6/§12); settings-not-code, so nothing else would notice a deletion
│   ├── test_assert_release_tag.py        # Behavioural + wiring: util/assert_release_tag.bash (P3) — tag-shape + tag<->built-wheel version, and that all 7 publishers invoke it with the right prefix
│   ├── test_pyproject_extras.py          # Lint: pyproject [project.optional-dependencies] surface matches the contract
│   ├── test_template_library_drift.py    # Lint: custom-agent template library (prompts/agent_templates/) manifest <-> templates
│   ├── test_template_selection.py        # Lint: custom-agent template match_signals selection coherence
│   ├── test_template_select_preview.py   # Behavioural: util/template_select_preview.py offline match_signals selector (P2)
│   ├── test_template_data_resolver.py    # Tests + drift gate: data layer (prompts/agent_templates/data/) + resolver
│   ├── test_scaffold_template.py         # Behavioural: util/scaffold_template.py new-template generator (P5; drift-compliant output)
│   ├── test_open_signed_pr.py            # Behavioural: util/open_signed_pr.py signed cross-repo PR opener (hermetic gh stub; dry-run/dup-guard/refs-ref=/deletions)
│   ├── test_wait_for_checks.py           # Behavioural: util/wait_for_checks.py required-context CI waiter (hermetic scripted-gh stub; positive-terminal, growing-rollup + observed-anchor negative control, absent-vs-running, hard-error, read-only)
│   ├── test_experiment_stack_script.py   # Contract + behavioural: util/experiment_stack.bash per-run launcher (§6.1 recipes, §6.4 RUN_DIR, §7.2 target file, §9.3 ranges, F-6 listener pid, dry-run + teardown; hermetic)
│   ├── test_run_suite.py                 # Behavioural: util/experiments/run_suite.py suite driver (expansion + cell_ids, per_cell seeds, driver-validated cells, stubbed up/drive/down loop, registry/index/aggregate, resume, both Q-2 budget flags; hermetic)
│   ├── test_list_runs.py                 # Behavioural: util/experiments/list_runs.py lister/pruner (state classification, --older-than, prune safety gates; hermetic RUN_ROOT fixtures)
│   ├── test_snapshot_index.py            # Behavioural: util/snapshot_index.py snapshot index/query (design §6.2) — bytes-attr decode, append-only rescan, --limit deferred-vs-present counting, D-C provenance filters, and an AST anti-resurrection guard that the tool stays READ-ONLY (retention is §6.4 and gated)
│   ├── test_snapshot_classify.py         # Behavioural: util/snapshot_classify.py owner-scheme classifier (handoff 2026-08-22 §2.4) — the two-axis category/health rule (incl. the attributed zero-node row that made category 5 read empty), `readable`-is-not-loadable, iterations-not-epochs (inert meta.current_epoch), replace-not-append sidecar, fd-level stdout muffling, the train-stage scratch-root refusal, and an AST anti-resurrection guard that the tool stays READ-ONLY
│   ├── test_run_experiment.py            # Behavioural: util/experiments/run_experiment.py cascor + recurrence driver (§6.3 drive loops, Q-2 stall/budget, F-1 redirect sampling, G-6 staging, §5.5 blocks + G-18 save_model, §8.1/§8.2 plot sets, §8.3 stats/summary, §13.4 manifest, exit matrix 0-4; hermetic stub HTTP)
│   ├── test_experiment_config_schemas.py # Drift gate (Wave 3.5): sibling conf/experiments/*.yaml ↔ driver load_config + AST-extracted app Settings fields (CI/force-local gated; always-on extractor self-check)
│   ├── test_experiment_suite_yamls.py    # Drift gate (R-6): every util/experiments/suites/**/*.yaml passes run_suite.load_suite + oversize cascor suites (pool >= 16 OR cap >= 64) declare execution.stall_seconds (ml#1069) + wide-cap suites pin a wall budget; anti-resurrection for the ad-hoc stall shim
│   ├── test_prompt_validator_contract.py # Lint: prompt-validator subagent frontmatter + pinned verdict schema/fixtures
│   ├── test_template_agent_skill_lint.py # Lint: template-agent Skill frontmatter + wiring to real artifacts (PR 5)
│   ├── test_service_smoke_skill_lint.py  # Lint: service-smoke Skill frontmatter (declared browser MCP for opt-in --ui, NO Agent) + teardown wiring (E-1 Stage 1/2)
│   ├── test_ui_test_author_skill_lint.py # Lint: ui-test-author Skill frontmatter (Write + declared browser MCP, NO Agent) + models canopy src/tests/ui/ + teardown (E-6)
│   ├── test_agents_frontmatter.py        # Lint: every .claude/agents/*.md honours the suite frontmatter contract (opus+max)
│   ├── test_agents_md_version_drift.py   # Lint: AGENTS.md **Version** header matches pyproject.toml [project].version
│   ├── test_agents_md_header_schema.py   # Lint: AGENTS.md canonical header schema (6 required fields, ISO date format)
│   ├── test_agents_md_tree_drift.py       # Lint: every tracked top-level dir appears in the Repository-Structure tree (G-3)
│   ├── test_coverage_gap_mapper_drift.py  # Dogfood/drift (E-4): juniper-coverage-gap-map console script registered + version/pin coherent (ci-tools)
│   ├── test_env_drift_check_drift.py      # Dogfood/drift (§10.1): juniper-env-drift-check entry point registered + every cli*.py wired (0.5.1 #580-clobber guard)
│   ├── test_release_train_registry.py    # Lint + drift gate: util/release_train/registry.yaml (18 packages/8 repos/enums) <-> pyproject resolution (plan §4.1) + the ml#701 static-package pyproject==dunder lockstep gate
│   ├── test_release_train_detect.py      # Behavioural: util/release_train/detect.py detection engine (classifications, substantive-hunk, SemVer, exit codes; hermetic)
│   ├── test_release_train_propose.py     # Behavioural: util/release_train/{propose,notes_render}.py proposal-PR generator (dry-run bump+CHANGELOG move+notes, dup-guard, conflict refusal; hermetic) (plan §5.4)
│   ├── test_release_train_archive_guard.py # Behavioural: util/release_train/archive_guard.py exempt notes-archive structural guard (add-only/path-confined/name-valid/single-purpose; SKIP for non-archive; hermetic) (plan §7.2 / step 3.1)
│   ├── test_release_train_ceremony.py    # Behavioural: util/release_train/ceremony.py exempt-archive + Release ceremony (§8 HALTs, happy-path, signed-archive HALT/parse edges, dup-guard/idempotent, R7 gh-surface, dry-run; hermetic) (plan §7/§8/§9.3 / step 3.2)
│   └── fixtures/
│       └── prompt_validator/             # PR 3: verdict.schema.json + verdict.sample.{pass,fail}.json (validator contr
│   # Doc-link validator regression tests moved to juniper-doc-tools/tests/
│   # (Wave 4 of the doc-link migration plan; published under the dedicated
│   #  juniper-doc-tools PyPI package).
│
└── util/                      # Utility scripts and tools
    ├── ad-hoc/                           # Single-use / temporary / unfinished scripts (see ad-hoc/README.md)
    ├── assert_release_tag.bash            # Publish guard (P3): ref must be a TAG, and the tag's version must match the wheel actually built
    ├── open_signed_pr.py                  # Cross-repo: open a PR on any Juniper repo with a GitHub-SIGNED commit (createCommitOnBranch)
    ├── wait_for_checks.py                  # Cross-repo: wait for a PR's REQUIRED status checks (ruleset-anchored) to finish; read-only, exit 0/1/2/3
    ├── requirements_drift_check.py       # Drift checker for the requirements snapshot (--mode quick)
    ├── editable_install_drift_check.py   # Drift checker for juniper editable installs across conda envs
    ├── env_floor_drift_check.py          # Floor-drift checker: installed juniper-* vs target-repo pyproject floors (I-2)
    ├── release_train/                     # PyPI release-train: registry.yaml (18-package registry) + detect.py (report-only "needs deploy?" engine, Phase 1) + propose.py/notes_render.py (manifest -> proposal-PR content, dry-run, Phase 2.1) + archive_guard.py (exempt notes-archive PR structural guard, Phase 3.1) + ceremony.py (exempt-archive + Release ceremony, dry-run, Phase 3.2)
    ├── prompt_discovery/                  # Custom-agent suite (PR 4): env-discovery probes -> JSON grounding bundle (path-invoked, --repo-root)
    ├── fleet_triage/                      # Flood §4 item 7 (Stage-0 supervisor script layer): predict_merge.py -- detached-clone predicted-merge per PR (4 verdicts, TRUE delta, cluster map + order; delegates the 2 screens to juniper-ci-tools console scripts); --pr N | --batch, exit 0/2
    ├── generated_prompt_index.py         # Custom-agent suite (P4): index + safety-gated prune of prompts/generated/
    ├── template_data_resolver.py         # Custom-agent suite (PR 6b): loads prompts/agent_templates/data/*.yaml (data-layer resolver)
    ├── template_select_preview.py        # Custom-agent suite (P2): offline preview of the Template Agent's match_signals selection
    ├── install_agents.bash               # Custom-agent suite (PR 6a): mirror .claude/{agents,skills} -> ~/.claude (idempotent, reversible)
    ├── scaffold_template.py              # Custom-agent suite (P5): generate a new prompts/agent_templates/ template + manifest stanza
    ├── agent_suite_doctor.py             # Custom-agent suite: read-only health check (dogfood; OK/WARN/FAIL over every layer)
    ├── agent_suite_summary.py            # Custom-agent suite (P3): quick-reference listing of agents + templates
    ├── worktree_cleanup.bash             # V2 cleanup orchestrator (CWD-safe)
    ├── worktree_new.bash                 # Creates new git worktree
    ├── worktree_activate.bash            # Bash helper for worktree activation
    ├── worktree_close.bash               # Removes a worktree, branch, and prunes
    ├── worktree_wipeout.bash             # Bulk removal by pattern
    ├── remove_stale_worktrees.bash       # Removes all stale worktrees
    ├── cleanup_open_worktrees.bash       # Removes all active worktrees
    ├── prune_git_branches_without_working_dirs.bash  # Branch hygiene
    ├── juniper_plant_all.bash            # Starts all Juniper ecosystem services
    ├── juniper_chop_all.bash             # Stops all Juniper ecosystem services
    ├── snapshot_index.py                 # Snapshot archive index + query (design §6.2, delivers R2): --scan builds an append-only snapshots_index.jsonl per snapshot root; queries filter on the D-C provenance (--experiment/--cell-id/--run-id), tier and attribution. `dataset_id` is DERIVED, not stored — it is content-addressed on a generator version only known from a live juniper-data query after bring-up, so `--resolve-datasets` (implied by `--dataset-id`) joins run_id -> <RUN_ROOT>/<run_id>/manifest.json instead; opt-in because it reads outside the snapshot root. READ-ONLY BY CONSTRUCTION — no prune/delete path, because retention is §6.4 and gated on this index existing; an AST test enforces it. Records which groups a file has rather than judging validity, so cascor keeps sole ownership of the format policy (--verify opts into cascor's own verifier).
    ├── snapshot_classify.py             # Snapshot classifier over the §6.2 index (handoff 2026-08-22 §2.4). STAGED because the five categories cost between a second and CPU-days: `--stage index` (~1s) settles categories 4/5; `--stage load` asks cascor's OWN `load_network_result` and settles category 1 (~15 min, 27.9k files); `--stage train` is deliberately unimplemented (item 3) and refuses without a scratch $JUNIPER_CASCOR_SNAPSHOTS_DIR, because `train_output_layer` calls `create_snapshot()` unconditionally and would grow the archive under study. Emits TWO axes — `category` (must we reconstruct this snapshot's metadata?) and `health` (what can the artifact do?) — because the owner's five categories are not a partition and a literal first-match reading leaves category 5 unreachable. Reports `iterations_lower_bound` from arch.num_hidden_units, never an epoch count (meta.current_epoch is INERT: 0 across all 27,908). Writes only a derived, replace-not-append snapshots_classification.jsonl sidecar, read back by `--from-sidecar` in ~0.5s (without it the tool could WRITE a verdict it could not READ -- only the load stage sets `fails_to_load`, so a later `--category fails_to_load` re-derived from the index and reported "no matching snapshots" against a sidecar holding 526 of them). READ-ONLY over snapshots, AST-enforced, with no prune path because retention is §6.4 and gated on this output
    ├── isolated_stack.bash               # Isolated training-runtime E2E trio (data 8101 / cascor 8202 / canopy 8051): --up/--down/--status/--dry-run
    ├── experiment_stack.bash             # Per-run experiment launcher (data 8110-8139 / cascor 8230-8259 / recurrence 8260-8289): --up/--down/--status/--dry-run
    ├── experiments/                      # Experiment driver layer (Waves 2.2-2.6): run_experiment.py single-run cascor + recurrence driver (§6.3) + plots_cascor.py / plots_recurrence.py (§8.1 + §8.2 plot sets; 2.5 closes G-5) + stats_summary.py (§8.3 stats.json + summary.md) + list_runs.py (Wave 7.2: safety-gated lister/pruner) + run_suite.py + suites/ (Waves 7.1+7.5: suite driver — matrix expansion, per-cell up→drive→down, registry/index/aggregate; parallel + H-11 split, cascor refused per Q-6)
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
7. **release-train-archive-guard** (`pull_request` + `merge_group`) -- Runs `util/release_train/archive_guard.py` over the PR's changed files to prove the exempt notes-archive PR is add-only / path-confined / name-valid / single-purpose (plan §7.2 / step 3.1). SKIPs (passes) for any PR not touching `notes/releases/`, so it never blocks a normal PR; a violation fails only this check (the PR falls back to the standard owner gate).
    It also admits `merge_group` so the required context re-posts on a queued merge commit — but `merge_group` has no `github.base_ref`, so the job short-circuits to a green notice before any checkout and every real work step stays
    `if: github.event_name == 'pull_request'`. Standalone (and absent from the Quality Gate `needs:`) so the owner can later mark it a **required** status check (step 3.3). Gate: `tests/test_archive_guard_workflow.py`.
8. **sequence-safety** (ADVISORY; `pull_request` + `merge_group`) -- Installs `juniper-ci-tools` (>=0.8.0) + runs `juniper-symbol-loss-check` (explicit ml `--scope`) + `juniper-docs-additions-check` over the PR base..HEAD (P2 G1/G2); uploads `sequence-safety-report` (G5-vi). Standalone, ABSENT from the Quality Gate `needs:` so its skip-on-push never fails the gate — soak-advisory, promoted in the ruleset later, never via the QG `needs:`. WARN-only `allow-symbol-loss` / `docs-rewrite` label hatch.
9. **fleet-pr-lint** (ADVISORY; `cursor/*` PRs only) -- Warnings-only signals to the step summary (P2 G5-iv; flood §4 item 8 phase 4): commit count, `black --check`, fan-out, and AGENTS.md / cheatsheet hotspot notes. Never fails, never comments.
10. **required-checks** -- Quality gate enforcing all checks must pass

### Publishing (`publish.yml`)

Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first, then PyPI (`pypi needs: testpypi`). The Gate 1 verify installs `juniper-ml` bare, then `[clients]`, then `[tools]` from TestPyPI with PyPI as the extra index — never `--no-deps`, and never the heavy `[worker]` / `[servers]` / `[all]` / `[recurrence]` extras. The `build` job skips `juniper-<pkg>-v*` tags. Gate: `tests/test_publish_testpypi_verify.py`.

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
So the detect/report path stays `contents: read` and the write scope is unreachable off the propose path — the R7 privilege boundary (plan §9.3), pinned by `tests/test_release_train_workflow_guard.py`.
It runs `util/release_train/propose.py --execute` to open **standard-gated** release-proposal PRs (owner reviews and merges; never auto-merged; touches neither TestPyPI nor PyPI). The optional `packages` dispatch input (whitespace/comma-separated pypi_names; empty = all eligible) restricts which packages are proposed.
Garbage `packages` tokens (Title Case, underscores, path fragments, shell metacharacters) exit **2** with `::error::` in **both** write jobs before python runs (`release-train.yml` propose/ceremony shell; pin open juniper-ml#729 `PackagesInputRehearsalTest`). `--cross-repo` is appended **only** when `APP_TOKEN` is non-empty. Operator: runbook §3.2.
**Cross-repo write identity (Phase 4.1, plan §9.2 / §12 step 4.1).** The propose job mints a GitHub App installation token (`actions/create-github-app-token`, SHA-pinned) scoped to the 8 publishing repos and passes `propose.py --cross-repo`, so a sibling package's proposal branches from that repo's `origin/main`, edits its own checkout, pushes with the App token, and opens the PR **in that sibling repo** (the dup-guard runs per-repo).
In-repo meta consumer-pin co-changes (the #661 RK-11 lockstep) apply only to juniper-ml packages; a sibling proposal never edits the meta from a sibling checkout — it emits the §13 propagation edge instead.
**Graceful degradation is mandatory:** the mint step is gated on the repo variable `RELEASE_TRAIN_APP_ID` (owner-provisioned with the `RELEASE_TRAIN_APP_PRIVATE_KEY` secret), and when it is unset the job falls back to the single-repo `GITHUB_TOKEN` and `propose.py` skips sibling packages with a clear reason — the prior in-repo-only behaviour.
The App private-key secret is referenced **only** in the mint step and the minted token **only** in the propose job (both pinned by `tests/test_release_train_workflow_guard.py`); the App token is never a `pypi` environment reviewer (R7).
The cross-repo **ceremony** (`ceremony.py --cross-repo`) keeps the exempt notes-archive PR **central in juniper-ml** (§10.2) while cutting the Release on the owning repo (`gh release create --repo pcalnon/<repo>`); its seam bounds every `--repo` — and the archive lane's two api calls' repo bind — to the 8 publishing repos without widening the verb allowlist.
**Both** write lanes create their commits through the GitHub API (`createCommitOnBranch`, no local commit), so every commit is **GitHub-signed / Verified** and satisfies the ruleset's `required_signatures` rule -> hands-free auto-merge (2026-07-23 ml#707 was the unsigned-commit block that motivated this for `ceremony.py`).
`propose.py` previously made **unsigned** local git commits (`-c commit.gpgsign=false`) so a headless run never tripped the owner's YubiKey config. Once the 2026-08-12 branch-protection normalization added `required_signatures` to all 9 repos, that made every proposal PR unmergeable — an unsigned commit anywhere on the branch blocks the merge and squash does not rescue it (cascor#515; the pre-normalization cascor#497 merged with the identical unsigned commits).
`execute_proposal` and `execute_follow_on` both route through one `_execute_signed_pr` helper, and `propose.py` deliberately carries **no** local-`git` helper so the unsigned path cannot grow back (anti-resurrection pin: `ExecuteCrossRepoGuardTest.test_execute_path_makes_no_local_git_commit`). The API path needs no working tree — checkouts are read-only inputs.

`propose.py` also bumps the `AGENTS.md` **Last Updated** header in the same edit as **Version**, which now satisfies the `agents-md-touch-up.yml` **date check** as authored (the lane verifies the header rather than rewriting the branch — juniper-ml#1099).
Before #1099 that lane pushed its own `[skip ci]` commit when the date was stale; that commit became the PR head, and because it carried `[skip ci]` **no required context ever reported on it**, leaving the proposal permanently BLOCKED with every check stuck at "expected" (the other half of cascor#515). It also raced `Update Lockfile (Dependabot)`, whose push was then rejected. Pre-setting the date remains correct and is now the *only* thing needed.
Both write jobs must configure that headless git identity with `git config --global` (not repo-local) so sibling clones inherit `user.name` / `user.email` / `commit.gpgsign` — a juniper-ml-only identity fails the first sibling commit with `Author identity unknown` (ml#705 / run 30040138774; workflow-guard invariant `(g)` in #718).

**Ceremony mode (Phase 4.3, opt-in).** Dispatching with `mode=ceremony` (or setting `RELEASE_TRAIN_MODE=ceremony`) adds a second write-scoped `ceremony` job — identical `permissions: {contents: write, pull-requests: write}`, gated `if: needs.detect.outputs.mode == 'ceremony'`, with its own App-token mint step — that runs `util/release_train/ceremony.py --execute --monitor-timeout 900` for `BUMPED_NOT_RELEASED` packages.
It opens the central archive PR (branch + single-file commit via the GitHub API -> a **GitHub-signed** commit satisfying `required_signatures`, so the PR auto-merges hands-free), enables `--auto` behind the required guard, cuts the Release on the owning repo, and monitors the publish run to `PENDING_PYPI_APPROVAL`; the PyPI deploy still waits at the owner-gated `pypi` environment (Gate 2). The job renders a ceremony step summary (ceremonies / resume-monitors / HALTs / `PENDING_PYPI_APPROVAL`).
A per-package HALT (plan §8) is a normal green outcome surfaced in the step summary + a dedup issue + Slack (ceremony exit 1 does not fail the run; only exit >= 2 does). The HALT-issue upsert **degrades gracefully** if the App token lacks the Issues permission — a loud log line + a step-summary `halt_issue_failed` flag, never a crash (a `SeamViolation` code bug still propagates; the R7 gh surface is unchanged).
The workflow's R7 boundary — both write jobs' exact perms, the mode gates, off-quiescence, and the App secret referenced mint-only (once per write job) — is pinned by `tests/test_release_train_workflow_guard.py`, which also rehearses the actual mode-resolution shell, the ceremony **and** propose step summaries (`ProposeSummaryRehearsalTest`: `opened:`/`skip:` bucketing + empty-output banner, juniper-ml#730), and the `packages` / `--cross-repo` shell prefix (juniper-ml#729) via the YAML-extraction pattern.

The same guard pins every `<<'PY'` heredoc as balanced (`HeredocBalanceTest`, ml#708) and `compile()`-clean (`HeredocCompileTest`, ml#723) so a broken summary/Slack body cannot turn a successful run red only after the real work finishes.

**Known limitation (degraded no-App path only):** on the fallback path (`RELEASE_TRAIN_APP_ID` unset), a PR opened with the built-in `GITHUB_TOKEN` does **not** trigger CI workflows (GitHub's recursion guard), so a proposal PR shows **no checks** until the owner re-triggers them — close and reopen the PR, or push an empty commit.
When the GitHub App token is minted (the primary Phase 4.1 path) the PR is opened by the App identity and CI runs normally, so the caveat no longer applies; the repo's `can_approve_pull_request_reviews` setting is already enabled.

With the `SLACK_WEBHOOK_URL` repo secret present (owner-provisioned incoming webhook; Q-CHANNEL), each run also posts a compact summary — classification counts, packages needing action, run URL — to the Juniper Slack channel. Strictly non-blocking: a missing secret skips the step, and a post failure never fails the run.

### Claude Code Action (`claude.yml`)

Triggered by issue/PR comments and events mentioning @claude. Uses `anthropics/claude-code-action` for automated issue/PR assistance.

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
required status checks and merges clean with nothing having run:

```bash
gh api repos/pcalnon/<repo>/rules/branches/feature%2Fanything --jq length   # -> 0
gh api repos/pcalnon/<repo>/rules/branches/main               --jq length   # -> 9
```

This workflow carries no `branches:` filter, so it is the **only** check that runs on such a
PR. It cannot block the merge there -- no ruleset applies -- but it turns a silent merge into
a visibly red one.

**If it fails.** Re-open the work against the default branch. The house practice is
**close and re-open** a fresh PR titled `[retarget #NNN]`. Retargeting in place is *not*
sufficient on its own: every `ci*.yml` here uses the default `pull_request` types
`[opened, synchronize, reopened]`, which exclude `edited`, so a retarget re-runs this guard
and nothing else -- the PR stays blocked on its other required contexts until a push or a
close/re-open.

**`stacked-pr` label.** Silences this guard for a deliberate stack. It does **not** make the
PR mergeable into `main`, and it does **not** re-land the stack -- do that separately.

Rollout and rationale: [juniper-ml#434](https://github.com/pcalnon/juniper-ml/issues/434).

## Shared Service-Core Contracts

Relocated verbatim from `AGENTS.md` (P3 of the shared-session-memory plan) so it is read on demand rather than loaded into every session.

`juniper-service-core` (this repo's `juniper-service-core/` subdirectory) owns the shared FastAPI middleware, the `/ws/control` security + command dispatch, and the distributed worker pool that model services inject executors into. The load-bearing invariants — the ones a well-meaning refactor silently breaks:

- **CR-024 body limit** — `RequestBodyLimitMiddleware` treats `Content-Length` as an early-reject hint only and **always** stream-caps `POST` / `PUT` / `PATCH` against the cumulative limit (default 10 MiB), so an under-declared header or a chunked body with none still 413s. Skipping the stream when the declared length is present-and-small is the classic bypass.
- **Auth before rate limit** — with API keys configured, `APIKeyAuth` runs first, so a 401 never consumes a rate-limit token. Blank / whitespace-only configured keys are filtered out (the `auth_posture.real_keys` rule) so an empty secret file cannot enable auth that then accepts an empty `X-API-Key`.
- **429 header passthrough** — `RateLimiter` raises `HTTPException` carrying `Retry-After` + `X-RateLimit-*`; `SecurityMiddleware.dispatch` must rebuild `JSONResponse(..., headers=exc.headers)`. RateLimiter unit tests alone do not exercise that catch path.
- **Control-WS log sanitizing** — reject logs that interpolate untrusted Origin / command text go through the module-local `_sanitize_for_log` helpers (`control_security` strips `\r`/`\n`; `control_stream` also drops other C0 controls, keeping tab) so CRLF cannot forge multi-line control-plane records. Sanitizing changes log records only, never handshake outcomes or ack JSON.
- **Zero rate limit** — `ws_control_rate_limit_per_sec=0` builds a `LeakyBucket` with no refill; `retry_after` returns `3600.0` (hard backoff) rather than dividing by zero and tearing down the receive loop.
- **`/ws/workers` fail-closed** — a bad/missing `X-API-Key` closes **4001** without accepting; a non-object or shape-invalid registration closes **4008** with no `registration_ack`; `submit_result` rejects wrong-worker / unassigned results before the protocol parse; binary attachments over 100 MB get `Binary frame too large`. Control receive rejects malformed / non-object JSON with close **1003** rather than an `AttributeError`.
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

Contrast `ci.yml` (`group: ci-${{ github.ref }}` + `cancel-in-progress: true`): rapid serial merges to `main` cancel each other's CI runs, so only the last tip survives. Main-verify **must not** drop intermediate merges during a storm — each SHA gets its own group and is never cancelled (may queue behind the runner cap).

#### G3.1 catch-up BASE

A quoted `[skip ci]` in a merge-commit body can skip this workflow entirely (2026-07-30 incident on ml#870/#872/#873). The next successful run must therefore screen the skipped window, not only `HEAD^1`.

BASE resolution order (written to the job step summary as “Post-merge sequence-safety base”):

1. **Catch-up** — `head_sha` of the most recent **successful** `main-verify` run on `main`, when that commit is an ancestor of `HEAD` and ≠ `HEAD` → reason `catch-up from <sha> (N commits)`.
2. Else **`github.event.before`** (the push's first parent), when resolvable and not the all-zero SHA.
3. Else **`HEAD^1`** (force-push / initial commit / dispatch fallback).

Screens then run as `juniper-{symbol-loss,docs-additions}-check --base <BASE> --head <HEAD>` (human log + guarded `--json` artifact). Exit `≥2` is invocation error; exit `≥1` is a compositional-loss finding.

#### Waivers: trailers vs PR labels

| Mechanism | Per-PR `sequence-safety` job (`ci.yml`) | Post-merge `main-verify` |
|-----------|-----------------------------------------|--------------------------|
| Commit trailer `Allow-Symbol-Loss: <qualified.symbol>` / `Allow-Docs-Rewrite: …` in `BASE..HEAD` | Honored by the screen CLIs | **Honored** — required for post-merge green on intentional removals |
| PR label `allow-symbol-loss` / `docs-rewrite` | Demotes that screen to `--advisory` (WARN-only exit 0) | **Invisible** — labels never reach `push:main` |

Do not expect a label hatch to green main after merge. Blanket `Allow-Symbol-Loss: *` is rejected.

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
3. If there is still no base (orphan / initial tip / force push) → **fail-open** `run=true` (`No resolvable base (initial / force push) -> running the battery to be safe.`).
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
| Waiver was written but main is still red | Check the *merged* commit, not the branch: `git log -1 --format='%B' <sha> \| grep Allow-Symbol-Loss`. Squash ships the **first** commit's message, so a waiver added as a second commit never lands. Repair with a follow-up PR whose own first commit carries the trailer. |
| Suspected `[skip ci]` gap | Open the next main-verify run's step summary — look for `catch-up from <sha> (N commits)`. That run screens every merge since the last successful tip. |
| Docs-only merge, no battery | Expected — `battery` path-gate skips; `symbol-screen` still always runs. |
| Initial / force-push tip never ran the battery | The detector must fail-open to `run=true` when no parent base resolves — inspect the `Detect relevant path changes` step log. |
| Many open “main-verify failed at \<SHA\>” issues | Pre-0.3.0 per-SHA titles. Current notify uses one stable title; close stale SHA-keyed issues after adjudication and rely on `main-verify: post-merge verification failing`. |
| Silent main red (no Slack) | Confirm `SLACK_WEBHOOK_URL` is set; notify is non-blocking and never fails the workflow. Tracking issue title is SHA-keyed (re-runs comment, not reopen). |
| Tracking issue still open after green | Expected — notify does not auto-close. Owner closes after adjudication. |
| Battery list drift vs `ci.yml` | Keep both enumerations in lockstep in the same PR (see SYNC NOTE in `main-verify.yml`). |

Related: per-PR advisory screens live in `ci.yml`'s standalone `sequence-safety` job (absent from the Quality Gate `needs:`). Fleet predicted-merge shells out to the same symbol CLI on a throwaway merge result (`util/fleet_triage/predict_merge.py` → the `juniper-symbol-loss-check` console script (juniper-ci-tools >=0.8.0); the 2026-07-28 flood-census ad-hoc screens are retired under `util/ad-hoc/retired/` with a `_RETIRED-2026-08-05` suffix).

## Experiment Stack Utilities

`util/experiment_stack.bash` + `util/experiments/run_experiment.py` are the **per-run** CLI experimentation tooling (plan Wave 2.1–2.6; this section is Wave 2.7). They bring up a throwaway juniper-data instance plus **cascor and/or recurrence** (never canopy), drive a single experiment YAML against that stack, and write plots/stats/manifest under a durable `RUN_DIR`.

Primary design: [`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md). Preflight evidence: [`notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md`](../notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md).

This is **not** the isolated E2E trio (`util/isolated_stack.bash` on `8101`/`8202`/`8051`) and **not** the host stack (`plant_all` / `8100`/`8201`/`8050`).

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

Port locks use atomic `mkdir "$LOCK_ROOT/<port>.lock"` (`JUNIPER_EXP_LOCK_ROOT`, default `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments`) plus an `ss` probe. The lockdir serialises experiment launchers against each other; a foreign binder can still race — that surfaces as the service's own bind failure through the health gate.

#### Concurrency (Wave 5)

`cascor_up` exports `JUNIPER_CASCOR_SNAPSHOTS_DIR=$RUN_DIR/snapshots` (W-6), so each run's cascor writes snapshots into its own `RUN_DIR` instead of the shared root `juniper-cascor/cascor-snapshots/` (the `.h5`-debris class). This is the sanctioned use of the override: the shared root is the default precisely so CLI, service and container runs find each other's models, and a per-run root is the opt-out for isolated experiments; concurrent bench runs use `python -m bench.run_benchmark --results-dir` (W-7, juniper-recurrence). Two live runs are fully isolated — disjoint ports via the lockdirs, and `--down` of one run touches nothing of the other (pinned by `TestTwoRunConcurrency`).

**Q-6 is resolved (2026-08-15) and the one-cascor-per-checkout rule is retired.** `cascor_up` now also exports `JUNIPER_CASCOR_LOG_DIR=$RUN_DIR/logs` (juniper-cascor#523), so each run's cascor writes its own file log instead of the repo-shared `logs/juniper_cascor.log` (H-7). Requires `juniper-cascor` carrying that override; against an older cascor the export is simply ignored and the shared-log constraint below still applies.

Why this mattered more than ordinary log interleaving: **cascor's parent logger writes only to that file** — stdout carries just candidate-worker lines — so the markers that decide a run's verdict (`Training completed`, `Completed solving …`) exist nowhere else. A second cascor process in the same checkout does not merely mix the logs, it **rotates the evidence away**, which is how the F-P1-3 arm A/B run logs were lost. One other cascor process is enough, so the previous mitigation (use a distinct checkout per instance) never actually protected a single run against a long-lived service sharing its checkout.

Data and recurrence instances never had a per-checkout constraint.

#### F-6 listener pid rule (binding)

`$!` after `( cd … && nohup <server> … & )` is the backgrounded **subshell**, not the server. No `*_up` records `$!`. After the health gate, `record_listener_pid` writes the listener from `ss -tlnpH "sport = :<port>"` plus the process cmdline. Teardown kills pidfile-first only after proving the pid is alive, owned by the current uid, and still running the recorded cmdline (SIGTERM then bounded SIGKILL).

If the pidfile path refuses (pid gone, wrong uid, or cmdline no longer matches — the pid-reuse class), `stop_service` logs `pidfile path refused — falling back to the recorded port <N>` and kills via `ss` **only** on that run's recorded port. A listener still present after both attempts logs a WARNING. `artifacts/` is never deleted.

#### Partial-failure teardown (`do_up` → `teardown_run`)

`do_up` writes `ports.json` **before** any `*_up` launch so a half-started run is still teardown-able. Launch order is data → cascor → recurrence; the first failing leg sets `failed=1` and skips later services.

On failure (live mode, not `--dry-run`):

1. Logs `ERROR: bring-up failed — tearing the partial run back down (logs kept under ${LOG_DIR})`.
2. Calls `teardown_run "${RUN_ID}"` (same path as `--down`): reverse-order `stop_service`, release port lockdirs, write `teardown.json`, keep `artifacts/` + `logs/`.
3. Returns `1` (does **not** leave the partial listeners / locks for the operator to discover later).

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
| `data_up` / `cascor_up` / `recurrence_up` | `require_env_bin`, `activate_conda`, `wait_for_health`, and `record_listener_pid` each end with `\|\| return 1`, so the OR-list absorb sees a real failure |
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
| `2` | Misuse / validation (bad CLI/YAML/generator, API `422`) |
| `3` | Unreachable (health-wait / connection failures) |
| `4` | Run `FAILED` / service `5xx` |

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

Do not read a SKIP-only `ValueError` as a blank-PNG or acceptance regression.

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
| Driver exit `1` `stalled` / `timed_out` | Cascor: raise `--stall-seconds` / `--max-wall-seconds` only after confirming the run is still progressing; recurrence `timed_out` is the train socket budget. |
| Missing correlation / empty plot | Correlation is only in the driver's `metrics_series.csv` (not `/v1/metrics/history`). A `/metrics` 404 degrades sampling (G-3), not the run. |
| `--down` deleted results | It must not — `artifacts/` is preserved; if results are gone, check you pointed at the wrong `RUN_ROOT` or cleaned the durable home dir manually. |
| `--up` exited `0` but a listener remains / the next `--up` starves | OR-list false-green class — confirm the `\|\| return 1` pins (`rg -n 'wait_for_health.*\|\| return 1' util/experiment_stack.bash`). Run `--down <RUN_ID>`, then clear any stale `$JUNIPER_EXP_LOCK_ROOT/<port>.lock`. |
| `grafana bridge failed — tearing the run back down` | Expected when `--grafana-bridge` cannot preflight `socat` / `docker`, relay, or write the target file after the services are healthy — the run is already torn down. Install the tools or omit the flag. |
| Port range exhausted after a failed `--config` | Staging aborted after `allocate_port` and before `ports.json`, so `--down` cannot release the lockdirs (open #979). Clear `*.lock` under `JUNIPER_EXP_LOCK_ROOT` only once no live listener holds the port. |
| Plot `skipped` with a `ValueError` reason, exit `0` | No-renderable-data SKIP, not an acceptance failure — inspect `jq '.driver.plots' $RUN_DIR/manifest.json`. |
| Exit `1` with `matplotlib unavailable` | Install matplotlib in the driver env, or drop `outputs.plots` from the YAML. |
| `residuals.png` has only 2 panels | Optional `target_dt_*` missing or length-mismatched — pred/truth still plotted; not a SKIP. |

Do **not** point experiment ports at `plant_all` / isolated-stack ports, and do not use this launcher when you need canopy (use `isolated_stack.bash` or the host stack instead).

---

## Generator Availability Matrix (On-Host)

Which juniper-data generators are usable in which on-host environment, and what each availability gate needs (CLI experimentation plan §11 items W-4/W-10). juniper-data's registry (`juniper_data/api/routes/generators.py::GENERATOR_REGISTRY`, 16 generators) reports per-generator availability through `generator_available()`: a generator MAY declare an `is_available()` hook probing its optional dependencies; generators without the hook are always available (the numpy-only synthetics), and `arc_agi` — whose Hugging Face source has a local-file fallback — relies on the request-time `ImportError → 501` backstop instead.

### The gates

| Generators | Gate | Enable with |
| --- | --- | --- |
| `spiral`, `xor`, `gaussian`, `circles`, `moon`, `checkerboard`, `csv_import`, `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product` | none (numpy-only / stdlib) | — |
| `equities`, `equities_seq` | `is_available()`: pandas + yfinance importable | `pip install 'juniper-data[equities]'` |
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

---

## Shared-Package CI Workflows

Each in-repo published sub-package has its own subdirectory CI at `.github/workflows/ci-<suffix>.yml`. These are **distinct** from the meta `ci.yml` and from the `publish-*.yml` publishers: they are the only always-on gate for that package's pytest / coverage / wheel smoke.

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
| Gap-map enforce | `juniper-coverage-gap-map --coverage-json coverage.json --enforce` | Without `--enforce` the gap map is advisory and a gutted module ships green |
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

`ci.yml`'s `release-train-archive-guard` is a required merge-queue context, so it runs on `pull_request` **and** `merge_group`. On `merge_group` there is no `github.base_ref`, so the job short-circuits to a green notice before any checkout or base-ref work, and every real work step stays `if: github.event_name == 'pull_request'`. It remains ABSENT from Quality Gate `needs:` so its skip on push cannot paint `push:main` red. Gate: `tests/test_archive_guard_workflow.py` (classifier behaviour stays in `tests/test_release_train_archive_guard.py`).

---

## Scheduled Security Scan and Lockfile Update

Operator contract for the two Monday scheduled workflows that keep dependency hygiene unattended. Both are distinct from the per-PR `ci.yml` `security` / `dependency-docs` jobs.

### Security Scan (`security-scan.yml`)

| Item | Value |
|------|-------|
| Triggers | Cron `0 6 * * 1` (Monday 06:00 UTC) + `workflow_dispatch` |
| Permissions | `contents: read` only |
| Python | `3.12` |
| Install | `pip install pip-audit` then `pip install -e .` |
| Audit | a **sole** invocation: `pip-audit --strict --desc on` |

**Why `--strict` here but not in per-PR CI.** The scheduled scan must fail the run on a known finding. The per-PR `ci.yml` `security` job intentionally runs with `--skip-editable` and **omits** `--strict`: pip-audit counts a skipped editable install as a dependency-collection failure, and `--strict` would escalate that to a fatal error on every PR that installs the unreleased meta-package editable. Do **not** copy `--skip-editable` into the scheduled workflow, and do **not** drop `--strict` from it. Structural gate: `tests/test_security_scan_workflow.py`.

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

## Release-Train Detect Summary and Slack

Operator contract for the detect job's **Render step summary** and **Slack notification** heredocs in [`.github/workflows/release-train.yml`](../.github/workflows/release-train.yml). The full mode / Gate / HALT surface stays in the [release-train operator runbook](../notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) §3.1. Hermetic YAML-extraction pins: `DetectSummaryRehearsalTest` / `DetectSlackPayloadRehearsalTest` in `tests/test_release_train_workflow_guard.py`.

### Action set vs the ceremonial class

Both renderers treat `UNRELEASED_CHANGES`, `BUMPED_NOT_RELEASED`, and `SHIP_UNCERTAIN` as needing release action. `BUMPED_NOT_RELEASED` **alone** is the ceremonial class (Gate 2 / the ceremony job). Do not read "needs action" as "ceremony will run".

| Mode | Footer counts | Operator reading |
|------|---------------|------------------|
| `report` (default) | Full action set | Report-only; no write job ran |
| `propose` | Full action set | Read the **propose** job summary for `opened:` / `skip:` |
| `ceremony` | **Only** `BUMPED_NOT_RELEASED` | `UNRELEASED_CHANGES` / `SHIP_UNCERTAIN` are not ceremony candidates |

With a present, non-empty manifest the summary carries the title, package total, per-classification counts, a `Release hygiene: TAG_ONLY=N, NOTES_MISSING=M` line (truthy values only), the per-package table, collapsed detector notes, and the mode footer.

### Hard-fail banner and Slack

If `release-manifest.json` is absent or blank the summary writes only `**Detector failed hard -- no manifest was produced.** See the run log.` — no package table. The step still exits 0 (`if: always()`); treat it as a red detector outcome, never a quiet "0 packages need action". The Slack step posts only when `SLACK_WEBHOOK_URL` is set, is `continue-on-error`, and sends counts plus the run URL (or the `detector FAILED HARD` line) — no secrets, diffs, or CHANGELOG bodies.

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

Behaviour: check out the PR head with full history; if `AGENTS.md` has **no** `**Last Updated**:` line, emit a `::warning::` and pass; otherwise the value must be a well-formed `YYYY-MM-DD` date, must not be in the future, and the line must have **changed in this PR** (`git diff <base>...HEAD`). Anything else fails the check and prints the exact line to write.

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

The bash auditor covers L2/L3 structure only; juniper-ml's own `on:` event matrix and exact job `permissions` are pinned separately in `tests/test_validate_claude_yaml_access.py` — a permissions widen that still carries an `@claude` guard would not trip L2/L3 alone.

---

## Sibling Packages

### juniper-observability

`juniper-observability` lives under `juniper-observability/` in this repository and publishes independently from the `juniper-ml` meta-package. Since `juniper-ml` 0.5.0 it is also aggregated under the `[tools]` and `[all]` extras, so a `pip install juniper-ml[all]` will pull it in alongside the rest of the platform.

Services that don't need the full meta-package can still depend on `juniper-observability` directly when they only want the shared health models, request-ID logging/middleware, Prometheus helpers, or Sentry setup.

| Field                 | Value                                                                      |
|-----------------------|----------------------------------------------------------------------------|
| **PyPI Name**         | `juniper-observability`                                                    |
| **Current Version**   | `0.1.1`                                                                    |
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

`juniper-service-core` lives under `juniper-service-core/` and publishes independently (`juniper-service-core-v*` → `.github/workflows/publish-service-core.yml`; CI: `ci-service-core.yml`). Since `juniper-ml` 0.5.0 it is aggregated under the `[tools]` and `[all]` extras. Model services inject lifecycle / command executors; this package owns the shared FastAPI + WebSocket + worker-pool plumbing.

| Field                 | Value                                                                    |
|-----------------------|--------------------------------------------------------------------------|
| **PyPI Name**         | `juniper-service-core`                                                   |
| **Current Version**   | `0.5.1`                                                                  |
| **Python**            | `>=3.12`                                                                 |
| **Importable Module** | `juniper_service_core`                                                   |
| **Meta pin**          | `juniper-service-core>=0.2.0,<0.6.0` under `[tools]` / `[all]`            |
| **Package Docs**      | [`../juniper-service-core/README.md`](../juniper-service-core/README.md) |

#### HTTP middleware contracts

- **CR-024 request body limit.** `RequestBodyLimitMiddleware` caps mutating bodies (default 10 MiB). `Content-Length` is an **early-reject hint only**: a declared length over the max returns 413 immediately and an unparseable one returns 400 `Invalid Content-Length header`, but `POST` / `PUT` / `PATCH` are then **always** stream-read with a cumulative cap, so an under-declared `Content-Length` or a chunked body with none still hits 413. The read body is cached on `request._body` for downstream handlers (BUG-CC-15). Skipping the stream when the declared length is present-and-small is the classic bypass — do not reintroduce it.
- **Auth before rate limit.** When API-key auth is enabled, `APIKeyAuth` runs before the rate limiter, so a 401 never consumes a token.
- **429 header passthrough.** `RateLimiter` raises `HTTPException` carrying `Retry-After` and the `X-RateLimit-*` headers; `SecurityMiddleware.dispatch` catches it and rebuilds `JSONResponse(..., headers=exc.headers)`. Dropping those headers makes well-behaved clients retry immediately, and `RateLimiter` unit tests alone do not exercise the catch path.
- **Exempt paths.** `EXEMPT_PATHS` covers `/v1/health`, `/v1/health/live`, `/v1/health/ready`, `/docs`, `/openapi.json`, `/redoc`, and both literal `/metrics` forms (gated instead by the parallel `MetricsAuthMiddleware` allowlist). WebSocket upgrades are not intercepted by `BaseHTTPMiddleware`, so `/ws/*` is inherently outside this path.
- **Blank API keys.** `APIKeyAuth` filters blank / whitespace-only configured keys (the `auth_posture.real_keys` rule), so an empty secret file cannot enable auth that would then accept an empty `X-API-Key`.
- **Rate-limit keying.** `RateLimiter._get_key` buckets by `key:<api_key>` when the request authenticated, otherwise by `ip:<client.host>` — falling back to `ip:unknown` when Starlette reports no client. Authenticated callers therefore get their own budget rather than sharing one per source IP (and a shared NAT egress cannot exhaust an authenticated client's budget).
- **Worker mTLS half-config.** `TLSConfig` (`juniper_service_core.workers.security`) fails closed: with TLS enabled and only one of `cert_file` / `key_file` set it raises `ValueError` naming both paths, rather than returning a bare `SSLContext` with neither chain nor key. A silent half-config is the dangerous shape — it looks "TLS enabled" to callers while presenting nothing.

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

Repeated *rejected handshakes* are throttled separately by `HandshakeCooldown`, which tracks rejections per client IP: more than `max_rejections` (default **10**) within `window_sec` (default **60**) blocks that IP for `block_sec` (default **300**, i.e. 5 minutes) and closes further attempts with **4029** `Too many rejected handshakes`. The state is in-memory only, so a server restart clears it — a deliberate NAT-hostile escape hatch, since many clients can share one egress IP.

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

Control receive rejects malformed / non-object JSON with close **1003** rather than an `AttributeError`.

| Symptom | Check / Fix |
|---------|-------------|
| HTTP 429 arrives without `Retry-After` | `SecurityMiddleware` must pass `exc.headers` into the `JSONResponse` — RateLimiter unit tests alone do not cover that catch path. |
| A health probe gets 429 | Health / docs / metrics are exempt in service-core — check an upstream proxy or a non-exempt path. |
| A large POST is accepted despite the body limit | The mutating-method stream cap must be unconditional; a `Content-Length`-only fast path is the bypass class. |
| Multi-line or forged log record after a bad Origin / command | `_sanitize_for_log` regression — never interpolate unsanitized Origin / command into logger format strings. |
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
3. **Verify TestPyPI Install (Gate 1)** -- reads `[project].version`, waits briefly for index lag, then verifies in **two phases** (2026-08-08 amendment: pip has **no index priority**, so a merged `--index-url` + `--extra-index-url` namespace resolves to the highest version across *both* indexes and lets a TestPyPI squatter outrank the real package — TestPyPI `fastapi 1.0` beat production `fastapi 0.141.1` and killed the v0.7.0 verify, run 31281873275):
   1. **Provenance** -- `pip download --no-deps --index-url https://test.pypi.org/simple/ --dest <tmp> "juniper-ml==${VERSION}"`. The artifact comes from TestPyPI and **only** TestPyPI, at the exact built version; a missing `juniper_ml-${VERSION}-py3-none-any.whl` fails the step rather than handing pip a bogus path.
   2. **Resolution** -- **three** installs of that local wheel in order, each `--index-url https://pypi.org/simple/` (production PyPI **only**, no `--extra-index-url`) and **never** `--no-deps`, so extras resolution is still genuinely exercised:
      1. bare `"${WHEEL}"` → `importlib.metadata` version check
      2. `"${WHEEL}[clients]"` → imports `juniper_data_client`, `juniper_cascor_client`
      3. `"${WHEEL}[tools]"` → imports `juniper_ci_tools`, `juniper_doc_tools`, `juniper_observability`

   Light extras only — do **not** add `[worker]` / `[servers]` / `[all]` / `[recurrence]` here (torch, multi-GB). A broken extras declaration that a bare install alone would miss fails at this gate, before production PyPI.
4. **Publish to PyPI** (`needs: testpypi`) -- runs only after Gate 1 succeeds and publishes the same artifact with OIDC trusted publishing and attestations enabled.

**Tag guard:** the `build` job runs only for `workflow_dispatch` or a Release whose tag starts with `v`, so a shared-package Release (`juniper-<pkg>-v*`) cannot fire the meta publisher. Always-on gate for the two-phase verify (including the anti-regression check that no verify command may carry `--extra-index-url` or name both index URLs), the tag guard, and `pypi needs: testpypi`: `tests/test_publish_testpypi_verify.py`.

**Upload strictness:** the TestPyPI upload sets `skip-existing: true` so re-cutting a Release for a version TestPyPI already holds is a no-op rather than an immutable-upload 400; the production PyPI upload deliberately stays strict.

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
| **Release-only trigger** (`release: published` + `workflow_dispatch`; **no** `push: tags`) | Cutting a Release also creates the tag. Subscribing to both fired two concurrent publishes that raced the immutable TestPyPI upload (juniper-ml#555). |
| **Build-job tag-prefix guard** | `release: published` fires *every* `publish-*.yml`, so each build job gates on `startsWith(github.event.release.tag_name, '<pkg>-v')` to keep package A's Release from publishing package B. |
| **`--no-deps` TestPyPI-only verify** | With `--no-deps` no dependencies are fetched, so adding an `--extra-index-url` to production PyPI would only risk resolving a squatted *target* package during TestPyPI index lag. Sibling verify must not add a PyPI fallback. |
| **`skip-existing: true`** on both publish steps | Residual overlap (a manual dispatch during a Release) is a no-op instead of an immutable-upload 400. |
| **OIDC + concurrency** | `permissions: {id-token: write, contents: read}`; `concurrency.group: publish-<suffix>-${{ github.ref_name }}` with `cancel-in-progress: false`; environments `testpypi` then `pypi`. |

Retry a stuck publish without re-cutting a Release:

```bash
gh workflow run publish-ci-tools.yml --repo pcalnon/juniper-ml --ref juniper-ci-tools-vX.Y.Z
```

Sibling package release flow:

1. **Build and Validate** -- the build job sets `defaults.run.working-directory` to the package subdirectory (so every step is subdir-relative without repeating the path), runs `python -m build --sdist --wheel`, validates with `twine check dist/*`, and uploads that subdirectory's `dist/` artifact with `if-no-files-found: error` so a silently empty build fails here instead of surfacing as a confusing publish-step error.
2. **Publish to TestPyPI** -- downloads the artifact into `dist/`, publishes with `packages-dir: dist/`, `repository-url: https://test.pypi.org/legacy/`, and `verbose: true` so trusted-publisher or upload errors include the server response body.
3. **Verify TestPyPI Install** -- sparse-checks out the package `pyproject.toml`, reads the package version, retries the TestPyPI install up to five times to tolerate index lag, then imports the package's version module.
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
| Per-PR sequence-safety | `ci.yml` → `sequence-safety` | `pull_request` + `merge_group` only | **Advisory** (absent from Quality Gate `needs:`) |
| Fleet PR lint | `ci.yml` → `fleet-pr-lint` | `pull_request` whose head starts with `cursor/` | **Advisory** (never fails, never comments) |
| Post-merge net | `main-verify.yml` | every `push:main` + dispatch | **Bypass-proof** (owner/Cursor App cannot skip by merging green) |

Quality Gate (`required-checks`) needs exactly: `pre-commit`, `tests`, `build`, `docs`, `security`, `claude-yaml-audit`, `dependency-docs`. Folding `sequence-safety` / `fleet-pr-lint` / `release-train-archive-guard` into that `needs:` would fail every `push:main` (those jobs skip on push while the gate is `if: always()`).

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

`ci.yml` also listens on `merge_group` so required contexts re-post on the queued merge commit (merge-queue ruleset prerequisite). Without it the queue stalls with no required check.

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

| Lever | Effect |
|-------|--------|
| PR label `allow-symbol-loss` / `docs-rewrite` | Adds `--advisory` for that screen only → WARN findings, exit 0. Read live via `gh pr view` (re-run job; no re-push). |
| Commit trailer `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` | Primary, auditable waiver inside the modules; travels in history → also covers post-merge `main-verify`. |
| `merge_group` event | No PR object → **strict** (label hatch unavailable). |

Promote to REQUIRED later in the **branch ruleset**, never by adding the job to Quality Gate `needs:`. Soak convention mirrors CodeQL.

Local repro:

```bash
juniper-symbol-loss-check --base origin/main --head HEAD --json
juniper-docs-additions-check --base origin/main --head HEAD --json
# WARN-only (label-hatch equivalent); exit 2 is never masked:
juniper-symbol-loss-check --base origin/main --head HEAD --advisory
```

### Fleet PR Lint (#880 phase 4)

`cursor/*` head branches only (`pull_request` + `startsWith(github.head_ref, 'cursor/')`), `contents: read` only. Every signal goes to the job step summary and the shell ends with `exit 0` under `set +e`, so a probe failure cannot paint the check red.

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
| Per-PR Sequence Safety red, Quality Gate green | Expected while advisory — inspect the `sequence-safety-report` artifact; waive with commit trailers (or owner label for WARN-only) |
| Label greens Sequence Safety but `main-verify` fails after merge | Labels are PR-only; put `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` on a commit in the landed range |
| Merge queue stuck with no required check | Confirm `ci.yml` still has `on.merge_group` and every required context re-posts on queue runs |
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

The pinentry stub answers Admin PIN / user PIN / passphrase from `TEST_ADMIN_PIN` / `TEST_USER_PIN` / `TEST_PASSPHRASE`. It defeats interactive secret entry — **never** point it at a real keyring or a live-provisioned card.

### Related

- Code-signing migration status: [`notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md`](../notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md)
- Release-train headless commits are **API-signed on both lanes** (`createCommitOnBranch` in propose *and* ceremony), so they avoid the owner’s YubiKey while still satisfying `required_signatures`. Propose was unsigned until the 2026-08-12 ruleset normalization made that unmergeable (cascor#515) — see AGENTS.md / release-train runbook

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
# Manual dry look at the same counts the alarm uses
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

Constraint: the workflow queries with `gh pr list --limit 500`. Past 500 open PRs the counts understate the real queue — read a near-ceiling number as a soft floor, not exact cardinality.

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
| `CASCOR_SERVICE_URL`     | juniper-cascor-client | `http://localhost:8200` | juniper-cascor service URL                |
| `JUNIPER_CASCOR_API_KEY` | juniper-cascor-client | *(none)*                | API key for juniper-cascor authentication |
| `CASCOR_MANAGER_HOST`    | juniper-cascor-worker | `127.0.0.1`             | Worker manager host                       |
| `CASCOR_MANAGER_PORT`    | juniper-cascor-worker | `50000`                 | Worker manager port                       |

> These are not set by juniper-ml itself — they are consumed by the installed sub-packages.
> `CASCOR_SERVICE_URL` defaults to the cascor service/container port (`8200`). The host-level stack and `util/get_cascor_*.bash` helpers target the host-facing port (`8201`) unless overridden.

Local orchestration scripts in `util/` also read the host-stack variables documented in [Host Orchestration Utilities](#host-orchestration-utilities), the E2E overrides in [Isolated Stack E2E Utilities](#isolated-stack-e2e-utilities), and the per-run experiment overrides in [Experiment Stack Utilities](#experiment-stack-utilities).

---

**Last Updated:** 2026-08-07
**Version:** 0.6.6
**Maintainer:** Paul Calnon
