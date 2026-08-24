"""Thread-safe registry for connected workers (WS-2 / OUT-11 T2 step 3a).

The de-cascored core of cascor's ``api/workers/registry.py`` (CLEAN per design §5.6: the
pool-infra layer is model-agnostic). Tracks worker connections, capabilities, heartbeats, and
health scores, and enforces one active connection per ``worker_id`` (a new connection replaces
the old). The cascade-specific task payload never reaches here -- ``active_task_id`` is an opaque
string assigned by the coordinator (step 3b), so this registry is fully generic.

Pure stdlib -- no third-party import, safe on the dependency-free import path.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from juniper_service_core.exceptions import JuniperServiceCoreError

__all__ = ["WorkerRegistration", "WorkerRegistry", "WorkerRegistryFullError", "DEFAULT_MAX_WORKERS"]

logger = logging.getLogger("juniper_service_core.workers.registry")

#: Cap on the registry size so a misbehaving worker pool (or a malicious / runaway client storm)
#: cannot grow the registry unbounded. 250 is a deliberate ceiling -- well above any realistic
#: fleet size and below a memory-meaningful threshold for the per-registration heartbeat state.
#: A service tunes it via ``WorkerRegistry(max_workers=...)``.
DEFAULT_MAX_WORKERS: int = 250


class WorkerRegistryFullError(JuniperServiceCoreError, RuntimeError):
    """Raised by :meth:`WorkerRegistry.register` when the registry is at capacity.

    Distinct from a generic :class:`RuntimeError` so the websocket worker-handshake handler can
    catch this specific case and emit a structured "registry full" close frame rather than an
    opaque server error. Re-registrations of an existing ``worker_id`` do NOT raise -- they
    replace the existing entry and the dict size stays unchanged.
    """


@dataclass
class WorkerRegistration:
    """Tracks a single connected worker.

    ``worker_id`` is the server-assigned authoritative identity (see :meth:`WorkerRegistry.register`).
    The optional ``client_name`` captures the worker's self-proposed display name for audit logging
    and operator debugging -- it is never used as identity, and two workers may report the same
    ``client_name`` without collision because their ``worker_id`` values are independently generated.

    The enriched heartbeat fields (``in_flight_tasks`` / ``last_task_completed_at`` / ``rss_mb`` /
    ``last_task_duration_seconds`` / ``recent_task_durations_seconds`` / ``gpu_utilization_pct``) are
    populated by workers that report them; workers running older images leave them at their defaults.
    """

    worker_id: str
    capabilities: dict[str, Any] = field(default_factory=dict)
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    tasks_completed: int = 0
    tasks_failed: int = 0
    active_task_id: str | None = None
    client_name: str | None = None
    # Enriched heartbeat fields -- populated by workers that report them; left at defaults otherwise.
    in_flight_tasks: int = 0
    last_task_completed_at: float | None = None
    rss_mb: float | None = None
    # Training-loop instrumentation, same None-default-preserves-prior-value semantics:
    # * last_task_duration_seconds -- wall-clock duration of the most recent completed task.
    # * recent_task_durations_seconds -- sliding window (oldest -> newest) of the last N durations.
    # * gpu_utilization_pct -- best-effort 0-100 reading; None when no GPU telemetry.
    last_task_duration_seconds: float | None = None
    recent_task_durations_seconds: list[float] = field(default_factory=list)
    gpu_utilization_pct: float | None = None

    @property
    def health_score(self) -> float:
        """Health score in ``[0.0, 1.0]`` from the task success rate (1.0 if no tasks yet)."""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 1.0
        return self.tasks_completed / total

    @property
    def idle(self) -> bool:
        """Whether the worker is idle (not assigned a task)."""
        return self.active_task_id is None

    def record_heartbeat(
        self,
        *,
        in_flight_tasks: int | None = None,
        last_task_completed_at: float | None = None,
        rss_mb: float | None = None,
        tasks_completed: int | None = None,
        tasks_failed: int | None = None,
        last_task_duration_seconds: float | None = None,
        recent_task_durations_seconds: list[float] | None = None,
        gpu_utilization_pct: float | None = None,
    ) -> None:
        """Update the last-heartbeat timestamp and (optionally) the enriched fields.

        Keyword-only enriched fields are accepted from richer workers; a ``None`` (the default)
        for any field preserves the registration's prior value.
        """
        self.last_heartbeat = time.time()
        if in_flight_tasks is not None:
            self.in_flight_tasks = in_flight_tasks
        if last_task_completed_at is not None:
            self.last_task_completed_at = last_task_completed_at
        if rss_mb is not None:
            self.rss_mb = rss_mb
        if tasks_completed is not None:
            self.tasks_completed = tasks_completed
        if tasks_failed is not None:
            self.tasks_failed = tasks_failed
        if last_task_duration_seconds is not None:
            self.last_task_duration_seconds = last_task_duration_seconds
        if recent_task_durations_seconds is not None:
            # Defensive copy: callers shouldn't be able to mutate the window through a shared ref.
            self.recent_task_durations_seconds = list(recent_task_durations_seconds)
        if gpu_utilization_pct is not None:
            self.gpu_utilization_pct = gpu_utilization_pct

    def is_alive(self, timeout: float) -> bool:
        """Whether the worker is alive based on the heartbeat timeout."""
        return (time.time() - self.last_heartbeat) < timeout


class WorkerRegistry:
    """Thread-safe registry of connected workers.

    Provides registration, deregistration, heartbeat tracking, and queries for available workers.
    All public methods are thread-safe.
    """

    def __init__(
        self,
        heartbeat_timeout: float = 30.0,
        *,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        if max_workers <= 0:
            raise ValueError(f"max_workers must be positive, got {max_workers!r}")
        self._workers: dict[str, WorkerRegistration] = {}
        self._lock = Lock()
        self._heartbeat_timeout = heartbeat_timeout
        self._max_workers = max_workers
        logger.info("WorkerRegistry initialized (heartbeat_timeout=%.1fs, max_workers=%d)", heartbeat_timeout, max_workers)

    @property
    def worker_count(self) -> int:
        """Number of currently registered workers."""
        with self._lock:
            return len(self._workers)

    @property
    def max_workers(self) -> int:
        """Configured registry capacity."""
        return self._max_workers

    @property
    def heartbeat_timeout(self) -> float:
        """The heartbeat timeout (seconds) used for liveness checks.

        Exposes the construction-time timeout so a collaborator (the step-3b ``WorkerCoordinator``
        health monitor) can re-check a stale worker's liveness via :meth:`WorkerRegistration.is_alive`
        without reaching into the private ``_heartbeat_timeout`` attribute.
        """
        return self._heartbeat_timeout

    @property
    def available_worker_count(self) -> int:
        """Number of idle, alive workers available for task assignment."""
        with self._lock:
            return sum(1 for w in self._workers.values() if w.idle and w.is_alive(self._heartbeat_timeout))

    def register(self, worker_id: str, capabilities: dict[str, Any], client_name: str | None = None) -> WorkerRegistration:
        """Register a worker; replaces any existing registration for the same ID.

        ``worker_id`` must be a server-assigned authoritative identity (the websocket handshake
        generates it), not a client-supplied value.

        Raises:
            WorkerRegistryFullError: If the registry is at capacity (:attr:`max_workers`) AND the
                registration is for a NEW ``worker_id``. Re-registrations of an existing ID do not
                raise (the dict size is unchanged) -- they replace the existing entry.
        """
        with self._lock:
            is_replacement = worker_id in self._workers
            if is_replacement:
                logger.warning("Worker %s re-registering (replacing existing connection)", worker_id)
            elif len(self._workers) >= self._max_workers:
                logger.warning(
                    "WorkerRegistry rejected new registration: at cap %d (client_name=%s, proposed_id=%s)",
                    self._max_workers,
                    client_name or "<none>",
                    worker_id,
                )
                raise WorkerRegistryFullError(f"WorkerRegistry at capacity ({self._max_workers}); reject new worker {worker_id!r}")
            reg = WorkerRegistration(worker_id=worker_id, capabilities=capabilities, client_name=client_name)
            self._workers[worker_id] = reg
            logger.info("Worker registered: %s (client_name=%s, total=%d)", worker_id, client_name or "<none>", len(self._workers))
            return reg

    def deregister(self, worker_id: str) -> WorkerRegistration | None:
        """Remove a worker from the registry. Returns the removed registration, or ``None``."""
        with self._lock:
            reg = self._workers.pop(worker_id, None)
            if reg:
                logger.info("Worker deregistered: %s (total: %d)", worker_id, len(self._workers))
            return reg

    def get(self, worker_id: str) -> WorkerRegistration | None:
        """Get a worker registration by ID."""
        with self._lock:
            return self._workers.get(worker_id)

    def heartbeat(
        self,
        worker_id: str,
        *,
        in_flight_tasks: int | None = None,
        last_task_completed_at: float | None = None,
        rss_mb: float | None = None,
        tasks_completed: int | None = None,
        tasks_failed: int | None = None,
        last_task_duration_seconds: float | None = None,
        recent_task_durations_seconds: list[float] | None = None,
        gpu_utilization_pct: float | None = None,
    ) -> bool:
        """Record a heartbeat for a worker. Returns ``True`` if the worker exists, ``False`` otherwise.

        Keyword-only enriched fields are forwarded to :meth:`WorkerRegistration.record_heartbeat`;
        pass ``None`` (the default) for any field the worker does not report.
        """
        with self._lock:
            reg = self._workers.get(worker_id)
            if reg is None:
                return False
            reg.record_heartbeat(
                in_flight_tasks=in_flight_tasks,
                last_task_completed_at=last_task_completed_at,
                rss_mb=rss_mb,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                last_task_duration_seconds=last_task_duration_seconds,
                recent_task_durations_seconds=recent_task_durations_seconds,
                gpu_utilization_pct=gpu_utilization_pct,
            )
            return True

    def assign_task(self, worker_id: str, task_id: str) -> bool:
        """Assign a task to a worker. Returns ``False`` if the worker is unknown or already busy."""
        with self._lock:
            reg = self._workers.get(worker_id)
            if reg is None or not reg.idle:
                return False
            reg.active_task_id = task_id
            return True

    def complete_task(self, worker_id: str, success: bool) -> bool:
        """Mark a worker's active task complete. Returns ``False`` if unknown or had no active task."""
        with self._lock:
            reg = self._workers.get(worker_id)
            if reg is None or reg.active_task_id is None:
                return False
            reg.active_task_id = None
            if success:
                reg.tasks_completed += 1
            else:
                reg.tasks_failed += 1
            return True

    def get_idle_workers(self) -> list[WorkerRegistration]:
        """All idle, alive workers, sorted by health score (best first)."""
        with self._lock:
            idle = [w for w in self._workers.values() if w.idle and w.is_alive(self._heartbeat_timeout)]
            return sorted(idle, key=lambda w: w.health_score, reverse=True)

    def get_stale_workers(self) -> list[WorkerRegistration]:
        """Workers whose heartbeat has timed out."""
        with self._lock:
            return [w for w in self._workers.values() if not w.is_alive(self._heartbeat_timeout)]

    def get_all_workers(self) -> list[WorkerRegistration]:
        """A snapshot list of all registered workers."""
        with self._lock:
            return list(self._workers.values())

    def snapshot_for_metrics(self) -> list[dict[str, Any]]:
        """Per-worker frozen snapshots of metric-relevant fields (read by the metrics collector).

        Walks every registration under ``self._lock`` and returns immutable, fully-copied snapshots
        so a concurrent :meth:`WorkerRegistration.record_heartbeat` cannot mutate a window while the
        collector computes percentiles over it. The returned list is fresh; the caller may mutate it.
        """
        with self._lock:
            return [
                {
                    "worker_id": reg.worker_id,
                    "last_heartbeat": reg.last_heartbeat,
                    "last_task_duration_seconds": reg.last_task_duration_seconds,
                    "gpu_utilization_pct": reg.gpu_utilization_pct,
                    # Tuple is immutable so a caller mutating the snapshot cannot pollute the window.
                    "recent_task_durations_seconds": tuple(reg.recent_task_durations_seconds or ()),
                }
                for reg in self._workers.values()
            ]

    def clear(self) -> int:
        """Remove all workers. Returns the number removed."""
        with self._lock:
            count = len(self._workers)
            self._workers.clear()
            logger.info("Registry cleared (%d workers removed)", count)
            return count
