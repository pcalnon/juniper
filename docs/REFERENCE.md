# Reference

## juniper-ml Technical Reference

**Version:** 0.6.3
**Status:** Active
**Last Updated:** 2026-08-05
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

```bash
# Confirm the plant restore arm (expect: set +u / conda activate / set -u)
rg -n -A3 '^safe_conda_activate' util/juniper_plant_all.bash
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

#### Orphan decision and SKIPPED races

For each candidate, read `PPid:` from `${JUNIPER_REAP_PROC_ROOT:-/proc}/<pid>/status`. Mark orphan when parent is PID `1` (init), the resolved user-session `systemd --user` PID, or the parent directory is gone. Live parents → `KEEP` (printed only with `--verbose`).

`SKIPPED` increments (never WOULD REAP / kill) when:

- `/proc/<pid>` disappeared between `ps` and the loop (ps→gone race)
- status is missing / unreadable / has no `PPid:` line

Summary line: `N reaped, M kept (live parent), K skipped` (`would be reaped` under `--dry-run`).

| Override | Default | Role |
|----------|---------|------|
| `JUNIPER_REAP_PROC_ROOT` | `/proc` | Synthetic proc root for hermetic tests |
| `JUNIPER_REAP_KILL_CMD` | `kill` | Kill binary override for tests (must accept `-KILL <pid>`) |

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
| `util/isolated_stack.bash --up` | Create the data venv, then launch data → cascor → canopy (health-gated) | `JUNIPER_E2E_DATA_PORT`, `JUNIPER_E2E_CASCOR_PORT`, `JUNIPER_E2E_CANOPY_PORT`, `JUNIPER_E2E_HEALTH_TIMEOUT`, `JUNIPER_E2E_DATA_EXTRAS`, `JUNIPER_E2E_RUN_DIR`, `JUNIPER_E2E_*_CONDA` / `*_DIR` |
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

#### Nounset after `activate_conda` (juniper-ml#785)

The script runs under `set -euo pipefail`. Cascor/canopy bring-up calls `activate_conda`, which temporarily `set +u` around `conda activate` because conda activation scripts may reference unset vars (e.g. `ADDR2LINE`) — the same class as plant's `safe_conda_activate`.

**Contract:** restore nounset with `set -u` immediately after `conda activate` so later unset expansions still fail. Pre-[#785](https://github.com/pcalnon/juniper-ml/pull/785) the restore arm was a second `set +u`, so live `--up` continued **without** nounset after every cascor/canopy activate. If a mid-`--up` failure looks like a silent missing-env typo that plant would have caught, confirm #785 is present (`rg -n 'set -u' util/isolated_stack.bash` inside `activate_conda`).

#### Kill-by-port teardown (`port_pid` / `stop_port`)

`--down` does **not** use `JuniperProject.pid`. It stops canopy → cascor → data via `stop_port`, which asks `ss -tlnpH "sport = :<port>"` for the first `pid=N` (`port_pid`), then `kill`s that PID.

Soft-fail when `ss` is missing, exits nonzero, or reports no `pid=` (logs "nothing listening"; not a failure). `--dry-run --down` announces the kill line but never kills. After stop, live mode removes `${RUN_DIR}/data`, the data venv, `*.pid`, and `snapshot_*` under cascor/canopy `src/snapshots/` (non-matching snapshot names are left alone).

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
| Sequence-safety screens | `util/sequence_safety/symbol_loss_check.py`, `docs_additions_check.py` | Path-invoked BASE..HEAD screens used by CI (`sequence-safety` job, `main-verify.yml`) |
| Predicted-merge triage | `util/fleet_triage/predict_merge.py` | Detached-clone merge of `origin/main` into a PR tip; runs fast gates + screens on the **merge RESULT** |
| Fleet supervisor agent | `.claude/agents/fleet-supervisor.md` | Read-only adjudication over a `--batch` report (never pushes / merges / closes) |

Design context: [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) §4 items 7–8.

### Sequence-safety CLIs

```bash
python util/sequence_safety/symbol_loss_check.py --base origin/main --head HEAD --json
python util/sequence_safety/docs_additions_check.py --base origin/main --head HEAD --json
# WARN-only exit 0 (label hatch); exit 2 is never masked:
python util/sequence_safety/symbol_loss_check.py --base origin/main --head HEAD --advisory
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
3. On the RESULT: runs `pre-commit` hooks `black` / `isort` / `flake8` / `mypy` / `check-ast` on touched `.py` files; shells out to `util/sequence_safety/symbol_loss_check.py --repo-root <clone> --base <base> --head <result> --json` (same CLI as `main-verify` — juniper-ml#895 / ml#872); runs an **inline** docs additions-only screen that flags **any** removed content line on a changed `.md` (deliberately stricter than `docs_additions_check.py`'s heading / `--min-run` gate) and honors `Allow-Docs-Rewrite: <path>[, …]` / `*` trailers in `BASE..RESULT` (juniper-ml#926 — same escape hatch as sequence-safety so intentional rewrites are not forever `DAMAGED-FIX-FIRST`).
4. Emits the **TRUE** changed-file delta from `git diff --name-only origin/main <result>` (not the stale `gh pr … --json files` list).

| Verdict | Meaning |
|---------|---------|
| `MERGE-CLEAN` | Merge succeeds; fast gates + screens pass |
| `NEEDS-UPDATE-BRANCH` | Merge succeeds; a fast gate fails (format / type / AST) |
| `DAMAGED-FIX-FIRST` | Merge succeeds; symbol-loss or docs-deletion screen fails |
| `CONFLICT` | Merge conflict against `origin/main` |

`--batch` also builds a same-file cluster map and a restore/heal-first, least-colliding merge order. Exit `0` always reports (even when every verdict is `DAMAGED` / `CONFLICT`); exit `2` is usage / precondition only (`gh` missing, bad `--repo-root`, unresolved ref).

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

## Post-Merge Main Verification

`.github/workflows/main-verify.yml` is the bypass-proof compositional-loss net (flood-remediation P2 gate G3). It runs on every `push` to `main` (plus `workflow_dispatch`) so a merge that skipped or greenwashed per-PR checks still gets screened after it lands. Design notes: [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) §4 item 8.

| Job | When it runs | What it does |
|-----|--------------|--------------|
| `symbol-screen` | **Always** | `util/sequence_safety/symbol_loss_check.py` + `docs_additions_check.py` over `BASE..HEAD`; uploads `sequence-safety-report` (`symbol-report.json` / `docs-report.json`, 30-day retention) |
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

Screens then run as `python3 util/sequence_safety/{symbol_loss,docs_additions}_check.py --base <BASE> --head <HEAD>` (human log + guarded `--json` artifact). Exit `≥2` is invocation error; exit `≥1` is a compositional-loss finding.

#### Waivers: trailers vs PR labels

| Mechanism | Per-PR `sequence-safety` job (`ci.yml`) | Post-merge `main-verify` |
|-----------|-----------------------------------------|--------------------------|
| Commit trailer `Allow-Symbol-Loss: <qualified.symbol>` / `Allow-Docs-Rewrite: …` in `BASE..HEAD` | Honored by the screen CLIs | **Honored** — required for post-merge green on intentional removals |
| PR label `allow-symbol-loss` / `docs-rewrite` | Demotes that screen to `--advisory` (WARN-only exit 0) | **Invisible** — labels never reach `push:main` |

Do not expect a label hatch to green main after merge. Blanket `Allow-Symbol-Loss: *` is rejected.

#### Battery sync constraint

The battery job's unittest list is a **manual mirror** of `ci.yml`'s `tests` job (no pytest auto-discovery). Adding or removing a test module in `ci.yml` must update `main-verify.yml` in the same PR.

#### Operator triage

```bash
# Reproduce the screens locally against the same window main-verify would use:
python3 util/sequence_safety/symbol_loss_check.py --base <BASE> --head <HEAD>
python3 util/sequence_safety/docs_additions_check.py --base <BASE> --head <HEAD>

# Inspect the artifact from a failed run:
gh run download <run-id> -n sequence-safety-report
```

| Symptom | Check / Fix |
|---------|-------------|
| Red `symbol-screen` after a “green” PR | Per-PR job may have been `--advisory` via labels, or BASE was narrower than G3.1 catch-up. Download `sequence-safety-report`; waive with a **commit trailer** on a follow-up commit, or restore the deleted symbol/docs. |
| Suspected `[skip ci]` gap | Open the next main-verify run's step summary — look for `catch-up from <sha> (N commits)`. That run screens every merge since the last successful tip. |
| Docs-only merge, no battery | Expected — `battery` path-gate skips; `symbol-screen` still always runs. |
| Many open “main-verify failed at \<SHA\>” issues | Pre-0.3.0 per-SHA titles. Current notify uses one stable title; close stale SHA-keyed issues after adjudication and rely on `main-verify: post-merge verification failing`. |
| Silent main red (no Slack) | Confirm `SLACK_WEBHOOK_URL` is set; notify is non-blocking and never fails the workflow. Tracking issue title is SHA-keyed (re-runs comment, not reopen). |
| Tracking issue still open after green | Expected — notify does not auto-close. Owner closes after adjudication. |
| Battery list drift vs `ci.yml` | Keep both enumerations in lockstep in the same PR (see SYNC NOTE in `main-verify.yml`). |

Related: per-PR advisory screens live in `ci.yml`'s standalone `sequence-safety` job (absent from the Quality Gate `needs:`). Fleet predicted-merge shells out to the same symbol CLI on a throwaway merge result (`util/fleet_triage/predict_merge.py` → `util/sequence_safety/symbol_loss_check.py`; the 2026-07-28 flood-census ad-hoc screens are retired under `util/ad-hoc/retired/` with a `_RETIRED-2026-08-05` suffix).

## Experiment Stack Utilities

`util/experiment_stack.bash` + `util/experiments/run_experiment.py` are the **per-run** CLI experimentation tooling (plan Wave 2.1–2.6; this section is Wave 2.7). They bring up a throwaway juniper-data instance plus **cascor and/or recurrence** (never canopy), drive a single experiment YAML against that stack, and write plots/stats/manifest under a durable `RUN_DIR`.

Primary design: [`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](../notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md). Preflight evidence: [`notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md`](../notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md).

This is **not** the isolated E2E trio (`util/isolated_stack.bash` on `8101`/`8202`/`8051`) and **not** the host stack (`plant_all` / `8100`/`8201`/`8050`).

### Launcher (`util/experiment_stack.bash`)

| Utility | Purpose | Key overrides |
|---------|---------|---------------|
| `--up (--cascor \| --recurrence)` | Allocate ports, launch data → selected app(s), health-gate, write `ports.json` | `JUNIPER_EXP_*` (below) |
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
- `--config PATH` — copy YAML to `$RUN_DIR/config/experiment.yaml` and export `JUNIPER_CASCOR_CONFIG_FILE` (app-side YAML settings are Wave 3; until then the env var is staged but inert for recurrence, which has no `--config`).
- `--experiment NAME` — Prometheus `experiment` label (default: config basename).
- `--grafana-bridge` — **opt-in** socat relays + Prometheus target file under `JUNIPER_EXP_DEPLOY_DIR/prometheus/targets/<RUN_ID>.json`. Without it, `--status` reports UNSCRAPED.

#### RUN_DIR contract (§6.4)

`RUN_ID=<UTC yyyymmddThhmmssZ>-<4 hex>` under `JUNIPER_EXP_RUN_ROOT` (default `~/.local/state/juniper-experiments` — under `$HOME`, **not** `/tmp`, so a reaped sandbox cannot destroy results). Everything for the run lives inside `$RUN_DIR`: pidfiles + recorded cmdlines, `logs/`, `relays/`, `config/`, `env/launch.env`, `data/`, `equities-cache/`, `artifacts/{plots,results}/`, `ports.json`, `teardown.json`.

Port locks use atomic `mkdir "$LOCK_ROOT/<port>.lock"` (`JUNIPER_EXP_LOCK_ROOT`, default `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments`) plus an `ss` probe. The lockdir serialises experiment launchers against each other; a foreign binder can still race — that surfaces as the service's own bind failure through the health gate.

#### F-6 listener pid rule (binding)

`$!` after `( cd … && nohup <server> … & )` is the backgrounded **subshell**, not the server. No `*_up` records `$!`. After the health gate, `record_listener_pid` writes the listener from `ss -tlnpH "sport = :<port>"` plus the process cmdline. Teardown kills pidfile-first only after proving the pid is alive, owned by the current uid, and still running the recorded cmdline (SIGTERM then bounded SIGKILL); falls back to kill-by-port only within this run's recorded ports. `artifacts/` is never deleted.

#### Health / conda

- `wait_for_health` polls every **2s** until `JUNIPER_EXP_HEALTH_TIMEOUT` (default **90** — sized for cold start; recurrence imports alone can take 10–15s).
- Default launch uses direct env-bin paths (`${JUNIPER_EXP_CONDA_DIR}/envs/<env>/bin/...`). Set `JUNIPER_EXP_CONDA_ACTIVATE=1` only if an env grows `activate.d` hooks.
- From a **git worktree**, set `JUNIPER_EXP_PROJECT_DIR` to the ecosystem root — the script's default derivation lands inside `worktrees/` otherwise.

Coverage: `tests/test_experiment_stack_script.py`.

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
| Health timeout mid-`--up` | Inspect `$RUN_DIR/logs/`; cold recurrence often needs the default `90s` — raise `JUNIPER_EXP_HEALTH_TIMEOUT` only after fixing the service. |
| Worktree can't find cascor `src/` | Set `JUNIPER_EXP_PROJECT_DIR` to the real ecosystem root. |
| Teardown killed the wrong process / left orphans | Pre-F-6 `$!` class — confirm pidfiles came from `record_listener_pid` (post-health `ss`), not shell `$!`. |
| `--status` says UNSCRAPED | Expected without `--grafana-bridge`; opt in only when `socat` + deploy `prometheus/targets/` are available. |
| Driver exit `2` on YAML | Unknown block/key, missing `experiment.seed`, or rule-6 infra key — see stderr. |
| Driver exit `1` `stalled` / `timed_out` | Cascor: raise `--stall-seconds` / `--max-wall-seconds` only after confirming the run is still progressing; recurrence `timed_out` is the train socket budget. |
| Missing correlation / empty plot | Correlation is only in the driver's `metrics_series.csv` (not `/v1/metrics/history`). A `/metrics` 404 degrades sampling (G-3), not the run. |
| `--down` deleted results | It must not — `artifacts/` is preserved; if results are gone, check you pointed at the wrong `RUN_ROOT` or cleaned the durable home dir manually. |

Do **not** point experiment ports at `plant_all` / isolated-stack ports, and do not use this launcher when you need canopy (use `isolated_stack.bash` or the host stack instead).

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
2. `publish-observability.yml` runs only for `juniper-observability-v*` tags or manual dispatch, builds from the subdirectory, publishes to TestPyPI, verifies installation, then publishes the same artifact to PyPI.
3. The publish workflow uses OIDC trusted publishing, GitHub-hosted `ubuntu-latest` runners, and SHA-pinned actions. If the runner type or pinned artifact actions change, verify compatibility before tagging a release.

---

## Version History

| Version | Date       | Changes                                                                                                                                                                  |
|---------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
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
3. **Verify TestPyPI Install** -- installs `juniper-ml==${VERSION}` from TestPyPI with PyPI as the extra index for dependencies, then verifies the installed distribution through `importlib.metadata`.
4. **Publish to PyPI** -- runs only after TestPyPI verification and publishes the same artifact with OIDC trusted publishing and attestations enabled.

### Independent Sibling Package Publish Pipelines

The sibling package publish workflows are intentionally decoupled from the meta-package release tags:

| Package                 | Tag Pattern                           | Workflow                                      | Build Directory          |
|-------------------------|---------------------------------------|-----------------------------------------------|--------------------------|
| `juniper-ml`            | `v*` GitHub releases                  | `.github/workflows/publish.yml`               | repository root          |
| `juniper-observability` | `juniper-observability-v*` tag pushes | `.github/workflows/publish-observability.yml` | `juniper-observability/` |

Sibling package release flow:

1. **Build and Validate** -- runs `python -m build --sdist --wheel` in the package subdirectory, validates with `twine check dist/*`, and uploads that subdirectory's `dist/` artifact.
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

Operator surface for the flood-remediation CI layers landed in [#869](https://github.com/pcalnon/juniper-ml/pull/869) / [#880](https://github.com/pcalnon/juniper-ml/pull/880) (Proposal P2 / flood analysis §4 items 1–2 + 8 phases 2–4). These jobs catch **serial same-file damage** that per-PR green checks miss. The CLIs they invoke live under `util/sequence_safety/`; predicted-merge triage for open fleet PRs is `util/fleet_triage/predict_merge.py` (see AGENTS.md Key Files).

Design context: [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](../notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md).

### Workflow map

| Surface | Workflow / job | When | Gate role |
|---------|----------------|------|-----------|
| G4 pre-commit split | `ci.yml` → `pre-commit` | every CI event | **Required** (Quality Gate) |
| Per-PR sequence-safety | `ci.yml` → `sequence-safety` | `pull_request` + `merge_group` only | **Advisory** (absent from Quality Gate `needs:`) |
| Fleet PR lint | `ci.yml` → `fleet-pr-lint` | `pull_request` whose head starts with `cursor/` | **Advisory** (never fails, never comments) |
| Post-merge net | `main-verify.yml` | every `push:main` + dispatch | **Bypass-proof** (owner/Cursor App cannot skip by merging green) |

Quality Gate (`required-checks`) needs exactly: `pre-commit`, `tests`, `build`, `docs`, `security`, `claude-yaml-audit`, `dependency-docs`. Folding `sequence-safety` / `fleet-pr-lint` / `release-train-archive-guard` into that `needs:` would fail every `push:main` (those jobs skip on push while the gate is `if: always()`).

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

Runs `util/sequence_safety/symbol_loss_check.py` then `docs_additions_check.py` over `<BASE>..HEAD`, uploads `sequence-safety-report` (`symbol-report.json` + `docs-report.json`, 30-day retention).

| Lever | Effect |
|-------|--------|
| PR label `allow-symbol-loss` / `docs-rewrite` | Adds `--advisory` for that screen only → WARN findings, exit 0. Read live via `gh pr view` (re-run job; no re-push). |
| Commit trailer `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` | Primary, auditable waiver inside the modules; travels in history → also covers post-merge `main-verify`. |
| `merge_group` event | No PR object → **strict** (label hatch unavailable). |

Promote to REQUIRED later in the **branch ruleset**, never by adding the job to Quality Gate `needs:`. Soak convention mirrors CodeQL.

Local repro:

```bash
python util/sequence_safety/symbol_loss_check.py --base origin/main --head HEAD --json
python util/sequence_safety/docs_additions_check.py --base origin/main --head HEAD --json
# WARN-only (label-hatch equivalent); exit 2 is never masked:
python util/sequence_safety/symbol_loss_check.py --base origin/main --head HEAD --advisory
```

### Fleet PR Lint (#880 phase 4)

`cursor/*` PRs only. Step-summary warnings for: commit count > 1, `black --check --line-length 512` on changed `.py`, fan-out > 15 files, and touches of hotspot files `AGENTS.md` / `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`. Always `exit 0`.

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
| Cannot *create* Ed448/Curve448 under gpg 2.4.x | Need `--compliance=gnupg` (or `compliance gnupg` in ceremony `gpg.conf`) |
| Scripted heredoc / shared loopback fd corrupts secrets | Never mix `--pinentry-mode=loopback` when a flow prompts for **both** passphrase and card PIN; use interactive or the stub harness for transfer |
| Headless re-validation | Ad-hoc harness: `util/ad-hoc/2026-08-03_yubikey_curve448_keytocard_e2e.bash` + `util/ad-hoc/2026-08-03_yubikey_test_pinentry.bash` (**throwaway credentials only**) |
| Stub pinentry “No pinentry” | Greeting must be Assuan `OK …` (#914); non-OK greeting → gpg-agent treats pinentry as dead |

### Harness safety

The pinentry stub answers Admin PIN / user PIN / passphrase from `TEST_ADMIN_PIN` / `TEST_USER_PIN` / `TEST_PASSPHRASE`. It defeats interactive secret entry — **never** point it at a real keyring or a live-provisioned card.

### Related

- Code-signing migration status: [`notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md`](../notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md)
- Release-train headless commits avoid the owner’s YubiKey (`commit.gpgsign false` on propose; API-signed archive on ceremony) — see AGENTS.md / release-train runbook

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

### Outputs and Slack

- **Always** writes a GitHub Actions step-summary table (`total` / `cursor` / thresholds / `level`).
- Slack fires **only** when `level != OK`, via `secrets.SLACK_WEBHOOK_URL`, under the same non-blocking Q-CHANNEL contract as `release-train.yml`:
  - missing secret → skip (exit 0)
  - POST failure → `continue-on-error` (run stays green)
- Slack text is counts + run URL only (no diffs, no secrets).

### Failure modes (still green)

| Situation | Behavior |
|-----------|----------|
| `gh pr list` / `jq` hard failure | `::warning::` annotation + step summary note; `level=OK` so Slack is skipped; exit 0 |
| Budget WARN / ALARM | Step summary + optional Slack; exit 0 (report-only) |
| Missing `SLACK_WEBHOOK_URL` on breach | Log skip; exit 0 |

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

**Last Updated:** 2026-08-05
**Version:** 0.6.3
**Maintainer:** Paul Calnon
