"""Generic task coordinator for remote WebSocket workers (WS-2 / OUT-11 T2 step 3b).

The de-cascored core of cascor's ``api/workers/coordinator.py``. Distributes opaque task payloads to
registered remote workers, collects results, and handles task timeouts / reassignment -- all
model-agnostic. The two cascade-bound operations are injected behind a :class:`WorkerTaskProtocol`
seam (the step-2 ``CommandExecutor`` analogue):

* **Building** the wire assignment (cascor: ``WorkerProtocol.build_task_assign`` + numpy
  ``BinaryFrame.encode``) -- :meth:`WorkerTaskProtocol.build_assignment`.
* **Parsing** a worker result (cascor: ``WorkerProtocol.validate_task_result`` + ``TaskResult``
  construction over ``correlation`` / ``candidate_id`` / numpy tensors) --
  :meth:`WorkerTaskProtocol.parse_result`.

Everything else -- idle-worker assignment bookkeeping, per-task timeout / retry, result collection
(with the worker-liveness early-exit), :meth:`WorkerCoordinator.pending_tasks_count` (consumed by
step-3a's :class:`~juniper_service_core.workers.metrics.WorkerRegistryCollector` via its injected
callable), and the background health monitor -- is generic.

**Result reduction is NOT here.** cascor's correlation-based candidate selection runs *downstream* of
``collect_results`` (in ``parallelism/task_distributor.py`` + the network), so
:meth:`WorkerCoordinator.collect_results` returns the raw list of parsed result objects and the
consumer reduces them. This keeps the coordinator reduction-agnostic, matching OUT-11's OQ-11 verdict
("result reduction stays cascade-bound / WS-8") and avoiding a speculative reducer hook (RK-4).

Thread-safety: the coordinator is called from both the async WebSocket handler (result submission,
dispatch) and a synchronous caller (task submission, collection). All shared state is protected by
``self._lock``.

Pure stdlib -- no ``numpy`` / ``fastapi`` import, safe on the dependency-free import path.
"""

from __future__ import annotations

import logging
import time
import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from threading import Event, Lock, Thread
from typing import TYPE_CHECKING, Any, Protocol, final, runtime_checkable

if TYPE_CHECKING:
    from juniper_service_core.workers.registry import WorkerRegistry

__all__ = [
    "WorkerCoordinator",
    "PendingTask",
    "WorkerTaskProtocol",
    "JsonTaskProtocol",
    "ParsedResult",
]

logger = logging.getLogger("juniper_service_core.workers.coordinator")

#: Poll cadence (seconds) for :meth:`WorkerCoordinator.collect_results`. The wait is sliced into
#: intervals of this length so the worker-liveness early-exit can fire promptly when every worker
#: disconnects mid-round, rather than blocking for the full (training-scaled) collection budget.
#: Small enough to be responsive, large enough to be cheap. (cascor ISSUE-319 defect #3.)
_RESULT_COLLECTION_POLL_INTERVAL = 1.0


@dataclass
class PendingTask:
    """A task that has been dispatched but not yet completed.

    ``payload`` is opaque: the coordinator never inspects it. The injected
    :meth:`WorkerTaskProtocol.build_assignment` knows how to wire-encode it -- cascor packs the
    candidate config + shared training tensors here, a JSON-only worker packs a plain dict.
    """

    task_id: str
    round_id: str
    payload: Any
    assigned_worker_id: str | None = None
    dispatched_at: float = field(default_factory=time.time)
    completed: bool = False


@dataclass
class ParsedResult:
    """The coordinator-visible projection of a parsed worker result.

    ``result`` is the opaque parsed object the *consumer* reduces (cascor's ``TaskResult``). ``score``
    + ``duration`` are the generic anomaly-detector inputs (cascor maps its ``correlation`` ->
    ``score``); leave them ``None`` to skip the anomaly check for this result.
    """

    success: bool
    result: Any
    score: float | None = None
    duration: float | None = None


@runtime_checkable
class WorkerTaskProtocol(Protocol):
    """The cascade-bound seam the coordinator dispatches encode / decode through.

    A service injects an implementation on ``app.state.worker_task_protocol`` (and passes it to the
    :class:`WorkerCoordinator`). These methods are the *only* place model-specific schema lives;
    everything else in the coordinator and the ``/ws/workers`` stream is generic. cascor's WS-6
    adapter wraps its ``WorkerProtocol`` + numpy ``BinaryFrame`` codec behind this protocol.
    """

    @abstractmethod
    def build_assignment(self, task: PendingTask) -> tuple[dict[str, Any], list[bytes]]:
        """Encode a dispatched task as a JSON envelope + ordered binary frames (the list may be empty)."""
        raise NotImplementedError

    @abstractmethod
    def result_attachments(self, msg: dict[str, Any]) -> list[str]:
        """Names of the binary frames that follow a result ``msg`` (in receive order); ``[]`` if none.

        The ``/ws/workers`` stream uses this to know how many binary frames to read after a
        ``task_result`` envelope before handing ``(msg, frames)`` to :meth:`parse_result`.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_result(self, worker_id: str, msg: dict[str, Any], frames: dict[str, bytes]) -> ParsedResult | None:
        """Validate + build a result object. Return ``None`` to reject (schema / validation failure).

        ``frames`` maps each attachment name from :meth:`result_attachments` to its raw bytes; the
        protocol owns any decode (cascor: numpy ``BinaryFrame.decode``) + validation.
        """
        raise NotImplementedError


@final
class JsonTaskProtocol:
    """The package default :class:`WorkerTaskProtocol` -- a JSON-only worker with no binary frames.

    The :class:`~juniper_service_core.websocket.commands.LifecycleCommandExecutor` analogue for the
    worker seam: publishing the Protocol *and* a working default means a consumer implements the
    three methods only when it actually carries a model-specific wire schema. A service whose task
    payloads are plain JSON-serialisable dicts -- the shape :class:`PendingTask` documents as "a
    JSON-only worker packs a plain dict" -- can inject this unchanged.

    Structural, not inherited: like ``LifecycleCommandExecutor`` this satisfies the Protocol by shape
    rather than by subclassing, so a consumer may use it, wrap it, or ignore it.

    Deliberately declares **no** attachments, so it never enters the binary-receive loop in
    ``websocket/worker_stream.py`` at all. That loop is now bounded in both dimensions
    (``_MAX_ATTACHMENTS`` and ``_MAX_TOTAL_BINARY_SIZE``, ``APD-SVCCORE-001``, fixed); declaring
    nothing remains the right default regardless, since a consumer that needs binary frames is
    writing its own codec anyway and takes on those bounds itself.

    **Not an extension point -- subclassing is refused, at runtime** (``APD-SVCCORE-012``, the same
    contract :class:`~juniper_service_core.websocket.commands.LifecycleCommandExecutor` carries).
    A consumer needing a different wire schema is in the case this seam exists for: **implement**
    :class:`WorkerTaskProtocol` directly, or **wrap** an instance of this class. Subclassing would
    freeze the envelope keys and the ``task_id`` rejection rule as inherited contract.
    """

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Refuse subclassing. Implement :class:`WorkerTaskProtocol` directly, or wrap an instance."""
        raise TypeError(f"JsonTaskProtocol is final and is not an extension point (tried to subclass it as {cls.__name__!r}). Implement the WorkerTaskProtocol protocol directly, or wrap an instance and delegate.")

    #: Wire ``type`` of the dispatch envelope. Matches cascor's ``MessageType.TASK_ASSIGN`` so a
    #: worker written against either speaks the same verb. Defined here rather than imported from
    #: ``websocket.worker_stream`` to keep this module on the dependency-free import path.
    ASSIGN_MESSAGE_TYPE = "task_assign"

    def build_assignment(self, task: PendingTask) -> tuple[dict[str, Any], list[bytes]]:
        """Encode ``task`` as a JSON envelope carrying the opaque payload, and no binary frames.

        ``task_id`` is included because :meth:`WorkerCoordinator.submit_result` looks the task up by
        the ``task_id`` the worker echoes back; omitting it makes every result unattributable.
        """
        return (
            {
                "type": self.ASSIGN_MESSAGE_TYPE,
                "task_id": task.task_id,
                "round_id": task.round_id,
                "payload": task.payload,
            },
            [],
        )

    def result_attachments(self, msg: dict[str, Any]) -> list[str]:
        """No binary frames ever follow a result under this protocol."""
        return []

    def parse_result(self, worker_id: str, msg: dict[str, Any], frames: dict[str, bytes]) -> ParsedResult | None:
        """Project a JSON result envelope onto :class:`ParsedResult`; reject one with no ``task_id``.

        ``score`` / ``duration`` are forwarded when present so the coordinator's anomaly detector can
        run; absent, they stay ``None`` and the anomaly check is skipped for this result.
        """
        if "task_id" not in msg:
            logger.warning("Result from worker %s has no task_id -- rejected", worker_id)
            return None
        return ParsedResult(
            success=bool(msg.get("success", True)),
            result=msg.get("result"),
            score=msg.get("score"),
            duration=msg.get("duration"),
        )


class WorkerCoordinator:
    """Coordinates task distribution and result collection for remote workers.

    Lifecycle of a training round:

    1. A synchronous caller submits a batch of opaque task payloads via :meth:`submit_tasks`.
    2. Tasks are dispatched to idle workers via :meth:`get_next_assignment` (called by the stream).
    3. Results are collected from workers via :meth:`submit_result` (called by the stream).
    4. The caller retrieves the completed results via :meth:`collect_results`.

    A background health monitor thread handles stale workers and per-task timeouts / reassignment.
    """

    def __init__(
        self,
        registry: WorkerRegistry,
        protocol: WorkerTaskProtocol,
        *,
        task_reassignment_timeout: float = 120.0,
        health_check_interval: float = 10.0,
        anomaly_detector: Any | None = None,
    ) -> None:
        self._registry = registry
        self._protocol = protocol
        self._task_reassignment_timeout = task_reassignment_timeout
        self._health_check_interval = health_check_interval
        #: Optional :class:`~juniper_service_core.workers.security.AnomalyDetector` (or any object
        #: with a compatible ``check_result``); set here or assigned later. ``None`` disables checks.
        self._anomaly_detector: Any | None = anomaly_detector

        # Task tracking
        self._pending_tasks: dict[str, PendingTask] = {}  # task_id -> PendingTask
        self._unassigned_tasks: list[str] = []  # task_ids waiting for workers
        self._results: dict[str, Any] = {}  # task_id -> parsed result object
        self._completed_task_ids: set[str] = set()  # for duplicate detection
        self._lock = Lock()

        # Current round
        self._current_round_id: str | None = None
        self._current_round_task_count: int = 0
        self._results_ready = Event()

        # Health monitor thread
        self._monitor_stop = Event()
        self._monitor_thread: Thread | None = None

        # WebSocket send callbacks (set by the worker stream; bookkeeping for proactive push).
        self._send_callbacks: dict[str, Any] = {}  # worker_id -> async callback

        logger.info(
            "WorkerCoordinator initialized (reassignment_timeout=%.1fs, health_check=%.1fs)",
            task_reassignment_timeout,
            health_check_interval,
        )

    @property
    def protocol(self) -> WorkerTaskProtocol:
        """The injected task protocol (the ``/ws/workers`` stream reads result attachments through it)."""
        return self._protocol

    @property
    def anomaly_detector(self) -> Any | None:
        """The wired anomaly detector (or ``None``)."""
        return self._anomaly_detector

    @anomaly_detector.setter
    def anomaly_detector(self, detector: Any | None) -> None:
        self._anomaly_detector = detector

    def start_monitor(self) -> None:
        """Start the background health monitoring thread (idempotent)."""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return
        self._monitor_stop.clear()
        self._monitor_thread = Thread(
            target=self._health_monitor_loop,
            name="worker-health-monitor",
            daemon=True,
        )
        self._monitor_thread.start()
        logger.info("Health monitor thread started")

    def stop_monitor(self) -> None:
        """Stop the background health monitoring thread."""
        self._monitor_stop.set()
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        logger.info("Health monitor thread stopped")

    def register_send_callback(self, worker_id: str, callback: Any) -> None:
        """Register an async send callback for a worker connection."""
        with self._lock:
            self._send_callbacks[worker_id] = callback

    def unregister_send_callback(self, worker_id: str) -> None:
        """Remove the send callback for a disconnected worker."""
        with self._lock:
            self._send_callbacks.pop(worker_id, None)

    def release_worker_tasks(self, worker_id: str, *, free_worker: bool = False) -> int:
        """Requeue incomplete tasks assigned to ``worker_id``.

        Two production callers share this helper:

        * The ``/ws/workers`` stream ``finally`` (clean disconnect). The stale-heartbeat
          sweep already reclaims before deregister; a clean disconnect used to
          ``deregister`` only, so the in-flight task sat assigned until
          ``task_reassignment_timeout`` (default 120s). ``free_worker`` stays False
          because the stream deregisters immediately afterwards.
        * Mid-result transport aborts (expected-binary-got-text / oversize). The worker
          is still connected, so ``free_worker=True`` clears ``active_task_id`` and the
          handler's post-result ``_try_dispatch_task`` can redispatch.

        Idempotent: a second call after the assignment is already cleared is a no-op and
        does not duplicate the unassigned queue entry.

        Returns:
            The number of tasks requeued.
        """
        with self._lock:
            return self._release_worker_tasks_locked(worker_id, free_worker=free_worker)

    def _release_worker_tasks_locked(self, worker_id: str, *, free_worker: bool = False) -> int:
        requeued = 0
        for task in self._pending_tasks.values():
            if task.assigned_worker_id == worker_id and not task.completed:
                task.assigned_worker_id = None
                task.dispatched_at = time.time()
                if task.task_id not in self._unassigned_tasks:
                    self._unassigned_tasks.append(task.task_id)
                    logger.info("Task %s reassigned to queue (worker %s released)", task.task_id, worker_id)
                requeued += 1
        if free_worker:
            self._registry.complete_task(worker_id, success=False)
        return requeued

    def submit_tasks(self, round_id: str, payloads: list[Any]) -> list[str]:
        """Submit a batch of opaque task payloads for the current round.

        Called by the synchronous caller at the start of a training round. Each ``payload`` is
        whatever the injected :class:`WorkerTaskProtocol` knows how to encode (cascor packs the
        candidate config + a reference to the shared round tensors).

        Returns:
            The list of generated ``task_id`` strings, in submission order.
        """
        with self._lock:
            self._current_round_id = round_id
            self._current_round_task_count = len(payloads)
            self._results_ready.clear()
            self._results.clear()
            self._completed_task_ids.clear()
            task_ids = []

            for payload in payloads:
                task_id = str(uuid.uuid4())
                pending = PendingTask(task_id=task_id, round_id=round_id, payload=payload)
                self._pending_tasks[task_id] = pending
                self._unassigned_tasks.append(task_id)
                task_ids.append(task_id)

            logger.info("Submitted %d tasks for round %s", len(payloads), round_id)
            return task_ids

    def get_next_assignment(self, worker_id: str) -> tuple[dict[str, Any], list[bytes]] | None:
        """Get the next task assignment for a worker, or ``None`` if none is available.

        Called by the WebSocket handler when a worker is ready for work. The cascade-specific wire
        encoding is delegated to :meth:`WorkerTaskProtocol.build_assignment`.

        Returns:
            ``(json_message, binary_frames)`` to send to the worker, or ``None``.
        """
        with self._lock:
            # Close the assignment-vs-deregister race: ``_check_stale_workers`` deregisters under
            # ``self._lock``, so if the worker is already gone we must NOT pop a task on its behalf
            # -- otherwise the task waits the full reassignment timeout before the next reaper sweep.
            if self._registry.get(worker_id) is None:
                return None
            if not self._unassigned_tasks:
                return None

            task_id = self._unassigned_tasks.pop(0)
            task = self._pending_tasks.get(task_id)
            if task is None:
                return None

            # Assign to the worker (state mutation is generic; the wire encoding is injected).
            task.assigned_worker_id = worker_id
            task.dispatched_at = time.time()
            self._registry.assign_task(worker_id, task_id)

            msg, frames = self._protocol.build_assignment(task)
            logger.debug("Assigned task %s to worker %s", task_id, worker_id)
            return msg, frames

    def submit_result(self, worker_id: str, msg: dict[str, Any], frames: dict[str, bytes]) -> bool:
        """Submit a task result from a worker. Returns ``True`` if accepted, ``False`` if rejected.

        Called by the WebSocket handler when a worker sends a result envelope (+ any binary frames).
        Generic envelope handling (``task_id`` lookup, duplicate detection, round bookkeeping) is
        done here; the cascade-specific validation + result construction is delegated to
        :meth:`WorkerTaskProtocol.parse_result`.
        """
        task_id = msg.get("task_id")

        with self._lock:
            # Duplicate detection.
            if task_id in self._completed_task_ids:
                logger.warning("Duplicate result for task %s from worker %s -- rejected", task_id, worker_id)
                return False

            # Task tracking.
            task = self._pending_tasks.get(task_id)
            if task is None:
                logger.warning("Result for unknown task %s from worker %s -- rejected", task_id, worker_id)
                return False

            # Ownership: only the assigned worker may submit a result. Reject before parse so a
            # wrong-worker (or still-unassigned) envelope cannot free the assignee, poison the
            # result map, or burn a parse side-effect on a task it does not own.
            if task.assigned_worker_id is None:
                logger.warning("Result for unassigned task %s from worker %s -- rejected", task_id, worker_id)
                return False
            if task.assigned_worker_id != worker_id:
                logger.warning(
                    "Result for task %s from worker %s -- rejected (assigned to %s)",
                    task_id,
                    worker_id,
                    task.assigned_worker_id,
                )
                return False

            # Cascade-bound validation + parse (schema / tensor checks live in the injected protocol).
            parsed = self._protocol.parse_result(worker_id, msg, frames)
            if parsed is None:
                logger.warning("Result parse/validation failed for task %s from worker %s", task_id, worker_id)
                # Free the worker AND reclaim the task. Pre-fix: complete_task cleared
                # active_task_id but left task.assigned_worker_id set and out of
                # _unassigned_tasks — has_pending_tasks() went False while the task was
                # still in-flight, then a later timeout sweep called complete_task again
                # and could steal a newer active_task_id on the same worker.
                self._registry.complete_task(worker_id, success=False)
                if task.assigned_worker_id == worker_id:
                    task.assigned_worker_id = None
                    task.dispatched_at = time.time()
                    if task_id not in self._unassigned_tasks:
                        self._unassigned_tasks.append(task_id)
                return False

            # Anomaly detection over the generic quality score (log warnings; do not reject).
            if self._anomaly_detector is not None and parsed.score is not None:
                anomalies = self._anomaly_detector.check_result(
                    worker_id=worker_id,
                    score=parsed.score,
                    training_duration=parsed.duration or 0.0,
                    task_id=task_id,
                )
                if anomalies:
                    logger.warning("Anomalies detected for worker %s on task %s: %s", worker_id, task_id, anomalies)

            # Accept the result.
            self._results[task_id] = parsed.result
            self._completed_task_ids.add(task_id)
            task.completed = True
            self._registry.complete_task(worker_id, success=parsed.success)

            logger.info(
                "Accepted result for task %s from worker %s (%d/%d complete)",
                task_id,
                worker_id,
                len(self._results),
                self._current_round_task_count,
            )

            # Signal if all results are in.
            if len(self._results) >= self._current_round_task_count:
                self._results_ready.set()

            return True

    def collect_results(self, timeout: float = 120.0) -> list[Any]:
        """Wait for all results from the current round and return them (raw, unreduced).

        Blocks until every result is received, the timeout expires, or -- the worker-liveness
        early-exit -- no workers remain connected to finish the in-flight tasks (with no registered
        workers the remaining tasks can never complete, so we stop waiting promptly and let the
        caller fall back). A healthy round returns the instant the last result arrives.

        Returns:
            The parsed result objects received (may be fewer than submitted on timeout / loss of all
            workers). **Reduction is the caller's job** -- cascor's ``TaskDistributor`` selects the
            winning candidate from this list.
        """
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            with self._lock:
                complete = len(self._results) >= self._current_round_task_count
            if complete:
                break
            if self._registry.worker_count == 0:
                logger.warning(
                    "collect_results: no remote workers connected -- abandoning wait for round %s after %d/%d results",
                    self._current_round_id,
                    len(self._results),
                    self._current_round_task_count,
                )
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            self._results_ready.wait(timeout=min(_RESULT_COLLECTION_POLL_INTERVAL, remaining))

        with self._lock:
            results = list(self._results.values())
            logger.info(
                "Collected %d/%d results for round %s",
                len(results),
                self._current_round_task_count,
                self._current_round_id,
            )
            return results

    def has_pending_tasks(self) -> bool:
        """Whether there are unassigned tasks waiting for workers."""
        with self._lock:
            return len(self._unassigned_tasks) > 0

    def pending_tasks_count(self) -> int:
        """The current number of pending (in-flight) tasks.

        Counts every task in :attr:`_pending_tasks` regardless of round / status / assignment
        (unassigned + dispatched-but-not-yet-completed). Wired into step-3a's
        :class:`~juniper_service_core.workers.metrics.WorkerRegistryCollector` via its
        ``pending_tasks_source`` callable so the pending-tasks gauge updates on every scrape.
        """
        with self._lock:
            return len(self._pending_tasks)

    def cancel_round(self) -> None:
        """Cancel the current round and clear all pending tasks."""
        with self._lock:
            self._pending_tasks.clear()
            self._unassigned_tasks.clear()
            self._results.clear()
            self._completed_task_ids.clear()
            self._current_round_id = None
            self._current_round_task_count = 0
            self._results_ready.set()  # Unblock any waiting collector.
            logger.info("Current round cancelled")

    def shutdown(self) -> None:
        """Shut down the coordinator: stop the monitor, cancel the round, drop send callbacks."""
        self.stop_monitor()
        self.cancel_round()
        with self._lock:
            self._send_callbacks.clear()
        logger.info("WorkerCoordinator shut down")

    def _health_monitor_loop(self) -> None:
        """Background thread: monitor worker health and handle task reassignment."""
        logger.debug("Health monitor loop started")
        while not self._monitor_stop.wait(timeout=self._health_check_interval):
            self._check_stale_workers()
            self._check_task_timeouts()

    def _check_stale_workers(self) -> None:
        """Deregister workers whose heartbeat has timed out, reassigning their active task.

        Holds ``self._lock`` across the liveness re-check, the active-task reassignment, and the
        deregister so the deregistration is atomic with respect to :meth:`get_next_assignment`: an
        in-flight assignment either runs before the worker is considered dead (assigns normally) or
        after it is removed (sees no eligible worker). A worker that sent a heartbeat between the
        stale snapshot and the re-check is skipped.
        """
        stale = self._registry.get_stale_workers()
        for worker in stale:
            with self._lock:
                current = self._registry.get(worker.worker_id)
                if current is None:
                    continue
                if current.is_alive(self._registry.heartbeat_timeout):
                    logger.debug("Worker %s recovered (heartbeat since stale snapshot) -- skipping deregister", worker.worker_id)
                    continue

                logger.warning("Worker %s heartbeat timeout -- deregistering", worker.worker_id)
                # Scan by assigned_worker_id under this lock so a task dispatched between the
                # stale snapshot and the re-check is not lost (get_next_assignment takes the
                # same lock). Mirrors the disconnect/abort reclaim helper.
                self._release_worker_tasks_locked(worker.worker_id)
                self._registry.deregister(worker.worker_id)
            # Send-callback bookkeeping takes its own lock; keep it outside the registry critical section.
            self.unregister_send_callback(worker.worker_id)

    def _check_task_timeouts(self) -> None:
        """Reassign tasks that have been pending on a worker for longer than the reassignment timeout."""
        now = time.time()
        with self._lock:
            for task in self._pending_tasks.values():
                if task.assigned_worker_id is not None and not task.completed and (now - task.dispatched_at) > self._task_reassignment_timeout:
                    logger.warning(
                        "Task %s timed out on worker %s (%.1fs) -- reassigning",
                        task.task_id,
                        task.assigned_worker_id,
                        now - task.dispatched_at,
                    )
                    # Only free the worker when it still holds THIS task. An orphaned
                    # assigned_worker_id (e.g. historical parse-None path) must not
                    # clear a newer active_task_id via complete_task.
                    assignee = task.assigned_worker_id
                    reg = self._registry.get(assignee)
                    if reg is not None and reg.active_task_id == task.task_id:
                        self._registry.complete_task(assignee, success=False)
                    task.assigned_worker_id = None
                    task.dispatched_at = now
                    if task.task_id not in self._unassigned_tasks:
                        self._unassigned_tasks.append(task.task_id)
