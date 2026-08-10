# juniper-cascor v0.8.0 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-08-10
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-cascor

---

This is a security-bearing release of `juniper-cascor` v0.8.0. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-cascor` |
| **Fixed in** | 0.8.0 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.8.0

### Added

- **C2b progress-pair reset regression tests** — pin that `_run_training` zeroes `output_epoch` / `candidate_epoch` pairs before `model.fit`, and that growth-phase `training_end` clears both pairs (bug-fix-only commits 0eb78d1 / 79e8ad7). Extends `test_c2b_epochs_cap_and_surfaces.py`.
- **Training start while INVESTIGATING / REPLAYING → HTTP 409** — route-level pins that Canopy receives the specific RuntimeError reason string (not a generic 500). Extends `test_training_route_coverage.py`.
- **`InvalidCandidatePoolError` → HTTP 422 route pin** — `PATCH /v1/training/params` must not collapse the typed C2.1 violation into bare `ValueError`→404. Extends `test_api_runtime_params.py`.
- **C7 classification_metrics edges** — Inf-in-target degradation + weighted average with a never-true (zero-support) class. Extends `test_classification_metrics.py`.

### Fixed

- **Worker anomaly history cleared on deregister.** `AnomalyDetector.clear_worker` existed but was never called from the `/ws/v1/workers` session teardown path, so `_worker_history` grew without bound across worker churn and a recycled `worker_id` could inherit stale `duplicate_correlations` / `perfect_correlation` signals. The worker-stream `finally` now clears anomaly history alongside registry/audit/metrics cleanup. Tests: `src/tests/unit/api/test_worker_security_integration.py`.
- **`ws_identity_key` treats blank / whitespace-only `X-API-Key` as anonymous.** Empty or whitespace-only headers previously hashed into a shared per-identity digest under the SEC-F19 D4b cap (self-DoS). The helper now strips before the falsy check so blank keys follow the anonymous (global/per-IP only) path. Tests: `src/tests/unit/api/test_ws_connection_caps.py`.
- **Snapshot restore/resume/retrain while REPLAYING (and retrain while STARTED/PAUSED) → HTTP 409.** Route preflights previously omitted `is_replaying()` (and `/retrain` had no FSM preflight at all), so lifecycle `loaded=False` rejections were misreported as 404 "snapshot not found". Aligns restore/resume/retrain with the same conflict contract. Tests in `test_snapshot_route_coverage.py`.
- **`stop_training` while INVESTIGATING / REPLAYING no longer desyncs FSM vs `training_state`.** STOP was rejected by the state machine but `training_state` was still forced to Stopped and broadcast — Canopy could show Stopped while `start_training` remained blocked. Now raises `RuntimeError`; REST maps to HTTP 409. Tests in `test_lifecycle_manager.py` / `test_training_route_coverage.py`.
- **`validate_task_result` rejects JSON bool for int/numeric fields.** `isinstance(True, int)` previously accepted `candidate_id` / `epochs_completed` / `correlation` as bool. Tests in `test_worker_protocol.py`.
- **`WorkerCoordinator.cancel_round` frees registry `active_task_id`.** Cancelling a round previously cleared coordinator pending/unassigned tracking but left workers marked busy in `WorkerRegistry`. Subsequent `get_next_assignment` calls then permanently refused work (`assign_task` → False), and `_check_task_timeouts` could not reclaim capacity because pending tracking was already gone — stuck remote-worker capacity until reconnect. `cancel_round` now calls `complete_task(..., success=False)` for every worker that still held an in-flight assignment. Regression tests in `test_worker_coordinator.py`.
- **InlineDataset + `_reload_dataset` — reject misaligned / half-specified splits at the boundary.**
  `InlineDataset` now cross-validates `train_x`/`train_y` lengths and requires `val_x`/`val_y` as a pair (matching lengths), so `POST /v1/training/start` returns 422 instead of constructing tensors that fail mid-`fit`. `_reload_dataset` likewise rejects juniper-data artifacts with non-2-D train/val arrays, train or validation sample-count mismatches, a partial `X_test`/`y_test` pair, or non-numeric train payloads — leaving prior tensors untouched so staged swaps can retry. Tests: `src/tests/unit/api/test_inline_dataset_validation.py`, extended `TestReloadDataset` in `test_lifecycle_manager_swap.py`.
- **`WorkerProtocol.validate_tensors`** — malformed tensor manifests (missing `shape`/`dtype`, non-dict entries) and empty `weights` arrays now return validation errors instead of raising `KeyError` / empty-reduction errors that could crash the coordinator result path. Tests: `test_worker_protocol.py::TestValidateTensors`.
- **CR-024 — `RequestBodyLimitMiddleware` no longer trusts a present `Content-Length` as a floor.** Previously the stream-cap path only ran when `Content-Length` was absent, so a client that under-declared the header (`Content-Length: N` with `N <= max`) and then streamed more than `max_bytes` bypassed the body limit (docstring claimed CR-024 protection; the `content_length is None` gate contradicted it). Mutating methods (`POST`/`PUT`/`PATCH`) now always stream-read with the cumulative byte cap after the oversized-declared early reject. Tests: `TestRequestBodyLimitMiddleware` under-declared + truthful Content-Length cases in `src/tests/unit/api/test_api_middleware.py`.
- **Worker result integrity — reject `success=True` without weights** (`src/api/workers/coordinator.py`): `submit_result` previously accepted a successful `task_result` when `tensor_manifest` was empty/missing (skipping `validate_tensors`), so a worker could claim success with no `weights` tensor. Downstream `_dispatch_to_remote_workers` then rebuilt a `CandidateUnit` with random init weights, poisoning candidate selection. Successful results now require a non-empty `weights` tensor; `success=False` may still omit weights. Covered by `test_worker_coordinator.py`.
- **Worker dispatch send-failure rollback** (`src/api/websocket/worker_stream.py`, `src/api/workers/coordinator.py`): `_try_dispatch_task` called `get_next_assignment` (marking the worker busy) then bare `send_json`/`send_bytes` with no rollback, so a socket write failure orphaned the assignment until `_task_reassignment_timeout` (default 120s). Failures now call `requeue_after_dispatch_failure` to free the worker and return the task to the unassigned queue immediately. Covered by `test_worker_stream.py` / `test_worker_coordinator.py`.
- **Control WS leaky-bucket `retry_after` no longer divides by zero when `refill_rate <= 0`.** Misconfiguration (or a future settings clamp that allows a zero rate) previously crashed the rate-limit ack path with `ZeroDivisionError` after `try_acquire` failed. `LeakyBucket.retry_after` now returns `0.0` (no finite wait estimate) when refill is non-positive. Tests: `src/tests/unit/api/test_control_security.py`.
- Soft `/ws/v1/workers` `task_result` binary-frame aborts (text instead of bytes, oversized frame, or decode failure) now free the worker and immediately requeue the in-flight task via `WorkerCoordinator.abort_in_flight_result`. Previously the socket stayed open, the worker remained busy, and the task waited for `_task_reassignment_timeout` (default 120s) while heartbeats kept CONC-10 from recovering it.
- **Companion auto-start cleanup:** `ManagedService.terminate` now closes the subprocess log handle in a `finally` (even if post-SIGKILL `wait` raises), and `start_service` always removes a failed-health service from `_active_services` even when `terminate()` itself raises or the health probe throws — preventing orphaned juniper-data/canopy processes and leaked FDs on local auto-start.
- **Remote worker reject-requeue:** `WorkerCoordinator.submit_result` now immediately requeues a task when schema or tensor validation rejects the worker's result (clearing `assigned_worker_id` and pushing `_unassigned_tasks`) instead of leaving the task orphaned until the full `_task_reassignment_timeout` (default 120s) fires.
- **Worker mid-disconnect task requeue:** `WorkerCoordinator.handle_worker_disconnect` (wired from `/ws/v1/workers` session cleanup) immediately requeues any in-flight task when a worker socket closes — including mid-binary-frame result receive — instead of leaving the task orphaned until `_task_reassignment_timeout` (default 120s). Distinct from CONC-10 heartbeat-timeout reaping. Tests: `test_worker_coordinator.py` (`TestHandleWorkerDisconnect`) and `test_worker_stream.py` (`test_mid_binary_frame_disconnect_requeues_assigned_task`).
- Unit tests no longer pin the service version as a literal: the four `0.6.0` assertions in `test_api_app.py`, `test_api_app_coverage_deep.py`, and `test_api_health.py` (red on `main` since the v0.7.0 bump merged in #429 without CI running) now assert against `api.app._API_VERSION` — the BUG-CC-04 canonical runtime read — so a release version bump can no longer break the suite.
- **CAN-015c — `update_params` / `PATCH /v1/training/params` / WS `set_params` reject REPLAYING (HTTP 409).**
  The FSM contract states that meta-param mutations are rejected while a snapshot replay session is active, but `TrainingLifecycleManager.update_params` never consulted `is_replaying()`. Live knobs could change mid-replay and desync the synthetic epoch stream. The manager now raises `RuntimeError`; the REST route maps it to **409** (WS inherits via the shared lifecycle call).
- **`get_secret` fail-soft on unreadable / non-UTF-8 Docker `_FILE` mounts.**
  `path.read_text()` previously propagated `OSError` / `UnicodeDecodeError` and could crash Settings resolution at boot. Both now fall through to the plain env var (same posture as a missing path).

### Security

- **Worker result ownership** — `WorkerCoordinator.submit_result` now rejects results whose submitting `worker_id` does not match the task's `assigned_worker_id`, so a peer worker cannot complete work it was never assigned. Tests: `test_worker_coordinator.py::TestSubmitResult::test_reject_wrong_worker_ownership`.

### Tests

- Gate-level regression: empty `ws_control_allowed_origins` skips the control WebSocket Origin check (documented opt-out) in `test_control_stream_coverage.py`.
- `get_secret` when `_FILE` points at a directory falls back to the plain env var (or `None`) without raising — `test_api_secrets.py`.

---

## References

- [CHANGELOG.md](../../CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-cascor_v0.8.0.md`

<!-- Auto-generated release-train DRAFT (util/release_train/notes_render.py).
     Source template: notes/templates/TEMPLATE_SECURITY_RELEASE_NOTES.md.
     Complete or delete these template sections before the release ceremony:
       - Affected Versions
       - Remediation / Upgrade Instructions
       - Testing & Quality
       - Upgrade Recommendation
-->
