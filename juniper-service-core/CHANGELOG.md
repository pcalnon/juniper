# Changelog

All notable changes to `juniper-service-core` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] - 2026-07-28

### Fixed

- `juniper_service_core/_version.py` `__version__` healed `0.4.0` -> `0.5.0` (the ml#701 stale-dunder class, second live instance — undetected for five days because no gate existed; healed in juniper-ml#702). The 0.5.0 wheel on PyPI carries correct metadata but its `__version__` dunder reports `0.4.0`; this patch release ships the corrected dunder. The release-train now bumps a static package's `_version.py` in lockstep with `pyproject.toml` (juniper-ml#710) and a generic gate guards the class.

## [0.5.0] - 2026-07-17

### Added

- **`enforce_auth_posture(...)`** (new `auth_posture` module) — a boot-time auth-posture
  self-check (**SEC-F01**), the security companion to the E-8 `enforce_dependency_floors`
  check. A service calls it at startup, before binding, passing its resolved API keys and
  whether auth is required in this deployment (`require_auth`); it **fails loud** (logs
  `CRITICAL` and raises `AuthPostureError`) when `require_auth=True` but no real key is
  configured, so the server refuses to start rather than silently serving open. This is the
  failure mode confirmed in the containerized-stack security audit (HO-2): every juniper
  HTTP service computes `enabled = len(api_keys) > 0`, so an empty/placeholder secret
  disables `APIKeyAuth` and serves protected routes unauthenticated — with no startup error
  and a `healthy` health check. Three outcomes: a real key → `INFO` (secured); no key +
  `require_auth` False → loud `WARNING` (running OPEN); no key + `require_auth` True →
  `CRITICAL` + raise. A blank/whitespace key (what an empty secret file resolves to) counts
  as unset. Stdlib-only (preserving the dependency-free top-level import); escape hatch
  `JUNIPER_SKIP_AUTH_POSTURE_CHECK` bypasses the check, logged loudly. Exported lazily:
  `enforce_auth_posture`, `auth_is_configured`, `AuthPostureError`. Consuming services adopt
  it at lifespan (mirroring the E-8 `enforce_dependency_floors(distribution=..., logger=...)`
  adoption) and set `require_auth=True` outside an explicit dev/open profile — a follow-up
  per service, gated on the next `juniper-service-core` release.

### Fixed

- **`[test]` extra now includes `prometheus-client>=0.20.0`** — the `workers/metrics`
  tests exercise `WorkerRegistryCollector` (a `prometheus_client` bridge), but the
  dependency was absent from the `test` extra, so those tests silently **skipped** in CI
  and `workers/metrics.py` under-measured. Adding the pin makes CI exercise them. The
  floor mirrors the sibling `juniper-observability` package. Test-only surface — no
  runtime dependency and no version bump.

### Changed

- **Test coverage lifted** for the `workers/`, `lifecycle/`, `routes/`, and top-level
  `juniper_service_core` sub-modules — part of work-unit **C-4** of the per-file coverage
  rollout ([`notes/JUNIPER_2026-06-30_JUNIPER-ECOSYSTEM_PER-FILE-COVERAGE-ROLLOUT-SCOPING.md`](../notes/JUNIPER_2026-06-30_JUNIPER-ECOSYSTEM_PER-FILE-COVERAGE-ROLLOUT-SCOPING.md)).
  Each named source file reaches ≥90% statement coverage and each of these sub-modules
  ≥95% statement-weighted pooled coverage, via **real tests only** (no source changes).
  The `websocket/` sub-module is lifted in a parallel sibling PR (C-4a); the blocking
  coverage gate is wired in a follow-up PR once both land.

## [0.4.0] - 2026-07-01

### Added

- **`enforce_dependency_floors(...)`** (new `dependency_floors` module) — a boot-time
  dependency-floor self-check (**E-8**). A service calls it at startup, before binding, and
  it **fails loud** (raises `DependencyFloorError` naming dep + floor + installed) if any
  installed `juniper-*` wheel is below the service's declared floor — the automatic
  *prevention* companion to the E-2 env-floor-drift *detector*, which would have caught the
  canopy "green tests / dead app" incident at first start with zero human action. Floors
  resolve from an explicit `{dist: min_version}` mapping, the caller's installed Requires-Dist
  metadata (`distribution=`), or a source `pyproject.toml` (`pyproject_path=`). Stdlib-only
  (`importlib.metadata` / `tomllib`; `packaging` optional), so the dependency-free top-level
  import is preserved. An escape hatch (`JUNIPER_SKIP_DEP_FLOOR_CHECK`) bypasses the check —
  logged loudly — so a false positive can never permanently block a legitimate start.

## [0.3.0] - 2026-06-25

### Added

- **`create_app(lifespan=...)`** — the app factory now accepts an optional FastAPI
  `lifespan` context manager and forwards it to `FastAPI(lifespan=...)`. A consuming
  service can run startup/shutdown hooks (logging configuration, build-info, resource
  setup/teardown) in a lifespan instead of at import time or in its CLI entrypoint.
  Backward-compatible: omitting `lifespan` is unchanged.

## [0.2.0] - 2026-06-21

The **T2 surface** of the OUT-11 service-tier extraction: the full training-lifecycle orchestrator,
generic HTTP routes, snapshot persistence + replay, the websocket subsystem, and the remote-worker
subsystem — all extracted and de-cascored from `juniper-cascor` with zero cascor coupling. Additive
over 0.1.0; cascor is untouched (its adoption of these bases is WS-6's A-phase). The cascade-bound
parts (correlation reduction, the `Task`/`TaskResult` envelope, cascade frames, dataset-swap history)
stay cascor-side per the OUT-11 design audit (OQ-11).

### Added

#### Training lifecycle (threaded) + generic routes (step 1)

- `ServiceLifecycleManager` — the model-agnostic, **background-threaded** lifecycle body that
  model-core's `TrainingLifecycleBase` deferred to WS-2: drives an injected `TrainableModel` through
  `fit()` on a worker thread, tracks a `LifecycleStateMachine`
  (`STOPPED → STARTED → {PAUSED, COMPLETED, FAILED}`, phase = open `str`), folds `TrainingEvent`s into
  a thread-safe `LifecycleMonitor` (live-state snapshot + bounded metric history), and honors
  cooperative pause/stop at event boundaries.
- **Generic HTTP routes** (`juniper_service_core.routes`) — model-agnostic training-control
  (`/v1/training/{start,stop,pause,resume,reset,status,params}`), metrics (`/v1/metrics`,
  `/v1/metrics/history`), dataset (`/v1/dataset`, `/v1/dataset/data`), and read-only
  model-introspection (`/v1/network`, `/v1/network/topology`) routes over the injected lifecycle
  (`app.state.lifecycle`), plus the shared `ResponseEnvelope` / `success_response` (with numpy-scalar
  coercion). Mount via `create_app(routers=build_routers())`.

#### Snapshot persistence + replay (steps 1b / 1c)

- **Snapshot persistence** — a serializer-injected `SnapshotStore` (one bundle directory per
  snapshot: the model written by an injected `juniper-model-core` `ModelSerializer` + a JSON sidecar
  of lifecycle state) plus the `ServiceLifecycleManager` methods `save_snapshot` / `list_snapshots` /
  `get_snapshot` / `load_snapshot` (→ `INVESTIGATING`) / `restore_for_retrain` (→ `STOPPED`) /
  `resume_from_snapshot` (→ `RESUME_READY`), and the `/v1/snapshots` routes (disk I/O off the event
  loop). Enabled only when a service injects a `ModelSerializer` (otherwise the routes return `501`).
- **Snapshot replay** — `ReplaySession` plays a snapshot's stored metric history back as timed frames
  on a background daemon (play / pause / seek / speed / range / stop / status; an injectable
  `on_frame` sink), plus `start_replay` (→ `REPLAYING`) / `replay_control` / `stop_replay` /
  `get_replay_state` and the `POST /v1/snapshots/{id}/replay[/control]` routes.

#### WebSocket subsystem (step 2)

- `juniper_service_core.websocket` — the model-agnostic websocket surface: `WebSocketManager`
  (monotonic sequencing, bounded replay buffer, oversized-message chunking, thread-safe broadcast,
  per-endpoint connection accounting) + the generic message builders (the 7 model-agnostic frames) +
  control-path security (`validate_control_origin` / `LeakyBucket` / `HandshakeCooldown`) + the
  `/ws/training` (metrics stream) and `/ws/control` (command channel) handlers + `build_websocket_router`.
- **Injectable `CommandExecutor`** (default `LifecycleCommandExecutor`) — the control-channel dispatch
  adapter, so a service maps the wire commands onto its own orchestration.
- `attach_websocket` lifecycle→broadcast bridge — live-training **and** replay frames push to
  `/ws/training` clients via the manager's additive `frame_sink`.

#### Worker subsystem (step 3)

- **Worker-pool foundations** (`juniper_service_core.workers`) — `WorkerRegistry` /
  `WorkerRegistration` / `WorkerRegistryFullError` + security primitives (`TLSConfig` mTLS,
  `ConnectionRateLimiter` token-bucket, `AnomalyDetector` over a generic bounded quality `score`) +
  audit (`AuditLogger` / `WorkerMetrics` / `AuditEventType`) + `WorkerRegistryCollector` (a
  `prometheus_client` bridge; configurable `metric_prefix`, pending-tasks via an injected callable).
- **`WorkerCoordinator`** — generic task dispatch / collect / timeout / retry with a worker-liveness
  early-exit and a background health monitor, over an injectable `WorkerTaskProtocol` seam
  (`build_assignment` + `parse_result` + `result_attachments`; the `CommandExecutor` analogue). Result
  reduction stays consumer-side (`collect_results` returns the raw list).
- **`/ws/workers` stream** (`worker_stream_handler`) — the machine-to-machine worker channel
  (origin-reject, `X-API-Key` auth, per-source rate-limit, registration handshake with a
  server-assigned id, heartbeat + enriched-field forwarding, dispatch + binary-frame transport), plus
  `attach_worker_pool` app-wiring and `build_worker_router`.

### Changed

- `lifecycle` is now a subpackage (`lifecycle/{sync,manager,monitor,state_machine,snapshots,replay}.py`);
  the synchronous `TrainingLifecycle` / `EventCollector` moved to `lifecycle/sync.py` and are
  re-exported, so `from juniper_service_core.lifecycle import TrainingLifecycle` is unchanged.
- All new lifecycle / route / websocket / worker public names are exported **lazily** via the PEP 562
  `__getattr__` (and listed in the `TYPE_CHECKING` block for CodeQL), so the dependency-free top-level
  import (`import juniper_service_core`) still holds (`fastapi` loads only when a subsystem is accessed).

### Notes

- **Adds a `numpy>=1.24` runtime dependency** (the generic routes marshal inline request arrays at the
  model boundary). It loads lazily with `.routes`, so the dependency-free top-level import is preserved.
- **Cascade-bound parts stay cascor-side** per OQ-11: correlation-based result reduction, the
  `Task`/`TaskResult` envelope, the `cascade_add` / `candidate_progress` frames, topology /
  per-sample-weight replay, and dataset-swap history. cascor adopts the generic bases in WS-6.
- Every generic surface is proven by a both-stacks-green contract test driven by model-core's
  **regression** reference models (the RK-6 guard against classification/cascade assumptions).

## [0.1.0] - 2026-06-14

### Added

- Initial package scaffold for the shared service-tier library (WS-2 of the
  model/middleware refactor).
- `SettingsBase` — `pydantic-settings` base with generic `service_name` / `host` /
  `port` / `log_level` fields; subclasses set their own `env_prefix`.
- `create_app(...)` — model-agnostic FastAPI application factory that mounts the
  generic health router and any service-supplied routers.
- Generic health router (`health_router()`) exposing `GET /v1/health` (liveness) and
  `GET /v1/health/ready` (readiness), plus a `HealthStatus` model.
- Dependency-free top-level import: `import juniper_service_core` exposes only
  `__version__` eagerly; `create_app` / `SettingsBase` load lazily via PEP 562
  `__getattr__`.
- Generic service-infra extraction from `juniper-cascor` (de-cascored, zero cascor
  coupling): `security` (`APIKeyAuth`, `RateLimiter`, `api_key_header`, plus the
  config-injected `build_api_key_auth` / `build_rate_limiter` factories replacing
  cascor's global-settings singletons), `secrets` (`get_secret` Docker file-secret
  reader), and `middleware` (`SecurityHeadersMiddleware`, `RequestBodyLimitMiddleware`,
  `SecurityMiddleware`, `EXEMPT_PATHS`) — with cascor's `cascor_constants` body-size /
  status-code imports replaced by local module constants. All exported lazily via the
  PEP 562 `__getattr__` so the dependency-free top-level import still holds.
- `launcher` — generic subprocess-managed companion-service runner extracted from
  `juniper-cascor` (de-cascored, zero cascor coupling): `ManagedService` (subprocess
  wrapper with `is_running` / `terminate`), `wait_for_health` (poll an HTTP health
  endpoint), `start_service` (`Popen` a service and wait for health), plus the
  `atexit`-registered cleanup of the module-level active-services registry. Cascor's
  `cascor_constants` timeout/interval imports are replaced by local module constants,
  and the log-dir resolution is generic (`JUNIPER_SERVICE_LOG_DIR`, else `./logs`).
  Exported lazily via the PEP 562 `__getattr__` (stdlib-only, so the dependency-free
  top-level import still holds).
- `lifecycle` — the **synchronous** `TrainingLifecycleBase` body: `TrainingLifecycle`
  drives a `juniper-model-core` `TrainableModel`'s `fit()` to completion and forwards its
  `TrainingEvent`s to the injected sink, stamping a monotonic run-scoped `seq` so the
  lifecycle owns event ordering; plus an `EventCollector` ordered sink. Growable models
  grow inside `fit()` (model-core contract), so this one body drives both fixed-topology
  and growable models. The threaded / FSM / worker-coordinated bodies (OQ-11) are
  deferred. Exported lazily so the dependency-free top-level import still holds.
- Publish (`publish-service-core.yml`) and CI (`ci-service-core.yml`) workflows.

### Notes

- Additive only. Extracts cascor's generic service infra (security / secrets / middleware /
  launcher); the websocket / worker / generic-route helpers are not extracted yet.
- The `lifecycle` body adds a dependency on **`juniper-model-core`** (the model contract).
  **Publish-first:** `juniper-model-core` must be on PyPI before `juniper-service-core` is
  published; in the monorepo, CI installs it editable from the sibling subdir first. The
  dependency-free top-level import is preserved (the lifecycle module is imported lazily).
- Published to PyPI 2026-06-16 (tag `juniper-service-core-v0.1.0`).

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/juniper-service-core-v0.2.0...HEAD
[0.2.0]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.2.0
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.1.0
