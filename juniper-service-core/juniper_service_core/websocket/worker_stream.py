"""Generic ``/ws/workers`` stream handler for remote worker communication (WS-2 / OUT-11 T2 step 3b).

The de-cascored core of cascor's ``api/websocket/worker_stream.py``. Handles the worker WebSocket
channel transport -- registration handshake, heartbeat keepalive, task dispatch, and result
collection -- onto the step-3a :class:`~juniper_service_core.workers.registry.WorkerRegistry` and the
step-3b :class:`~juniper_service_core.workers.coordinator.WorkerCoordinator`. The cascade-bound
message schema (task payload + result fields + binary tensor codec) is injected via the coordinator's
:class:`~juniper_service_core.workers.coordinator.WorkerTaskProtocol`; this module owns only the
generic transport mechanics.

Wire it onto an app with :func:`attach_worker_pool` +
:func:`~juniper_service_core.websocket.router.build_worker_router` (the worker-channel analogue of
``attach_websocket`` + ``build_websocket_router`` for the client streams)::

    from juniper_service_core import create_app
    from juniper_service_core.routes import build_routers
    from juniper_service_core.websocket import attach_worker_pool, build_worker_router
    from juniper_service_core.workers import WorkerCoordinator, WorkerRegistry

    registry = WorkerRegistry()
    coordinator = WorkerCoordinator(registry, my_task_protocol)
    app = create_app(routers=[*build_routers(), build_worker_router()])
    attach_worker_pool(app, registry=registry, coordinator=coordinator)

The path matches cascor's existing ``/ws/v1/workers`` shape via ``build_worker_router(path=...)`` (it
defaults to ``/ws/workers`` for parity with the singular ``/ws/training`` / ``/ws/control``). cascor's
cascade-specific task / result schema + numpy binary frames live behind the injected protocol (WS-6
adapter); the cascade ``Task`` / ``TaskResult`` envelope stays cascor-side (WS-8).

Requires ``fastapi``; kept off the eager import path (PEP 562 lazy export).
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket, WebSocketDisconnect

from juniper_service_core.websocket.manager import ws_authenticate
from juniper_service_core.workers.registry import WorkerRegistryFullError

if TYPE_CHECKING:
    from juniper_service_core.workers.coordinator import WorkerCoordinator
    from juniper_service_core.workers.registry import WorkerRegistry

__all__ = [
    "worker_stream_handler",
    "attach_worker_pool",
    "validate_worker_registration",
    "WORKER_WS_ENDPOINT",
]

logger = logging.getLogger("juniper_service_core.websocket.worker_stream")

#: The per-endpoint connection bucket name used for ``WebSocketManager`` accounting. Matches the
#: ``"worker"`` entry added to ``DEFAULT_WS_ENDPOINTS`` so the gauge is tracked, not silently dropped.
WORKER_WS_ENDPOINT = "worker"

#: Generic worker-protocol message types (inbound, worker -> server). The wire values match cascor's
#: ``juniper_cascor_protocol.worker.WorkerMessageType`` so WS-6 adoption is a drop-in; a different
#: consumer simply emits the same strings.
MSG_REGISTER = "register"
MSG_HEARTBEAT = "heartbeat"
MSG_TASK_RESULT = "task_result"

_MAX_JSON_SIZE = 65536  # 64KB for JSON messages
_MAX_BINARY_SIZE = 100 * 1024 * 1024  # 100MB for binary frames

#: Maximum number of binary attachments one ``task_result`` may declare (``APD-SVCCORE-001``).
#: Mirrors juniper-cascor's ``_MAX_TENSOR_MANIFEST_ENTRIES`` (``src/api/workers/protocol.py:64``,
#: enforced at ``src/api/websocket/worker_stream.py:391``) -- its fork already carried this bound and
#: the shared package did not, making the *shared* copy the weaker of the two.
#: **Checked before the first ``receive()``**, which is the point: a hostile declaration must be
#: rejected outright rather than allowed to stall the handler part-way through a binary sequence.
_MAX_ATTACHMENTS = 32

#: Aggregate binary budget across ONE result submission (``APD-SVCCORE-001``). The per-frame cap
#: alone permitted ``len(attachment_names) x _MAX_BINARY_SIZE``, which is the defect: a bound on each
#: item is not a bound on the sum, and ``frames`` accumulates every one of them in memory.
#: Set equal to the per-frame cap by a stated principle rather than an invented magnitude -- *one
#: submission may not deliver more bytes than a single frame was already permitted to carry*. The two
#: remain **independent policies** that merely coincide today: raising this budget must not silently
#: raise the per-frame cap, so both checks are kept rather than one deleted as redundant.
_MAX_TOTAL_BINARY_SIZE = _MAX_BINARY_SIZE

#: Worker-id sanity pattern (1-64 chars, alphanumeric / hyphen / underscore, alphanumeric start).
_WORKER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


def validate_worker_registration(msg: dict[str, Any]) -> list[str]:
    """Validate a registration message; returns a list of errors (empty if valid).

    Generic worker-handshake validation (worker_id shape + capabilities dict). The proposed
    ``worker_id`` is only a display name -- the server assigns the authoritative id -- but it is still
    shape-checked so audit logs carry a sane value.
    """
    errors: list[str] = []
    if "worker_id" not in msg:
        errors.append("Missing required field: worker_id")
    else:
        wid = msg["worker_id"]
        if not isinstance(wid, str):
            errors.append("worker_id must be a string")
        elif not _WORKER_ID_PATTERN.match(wid):
            errors.append("worker_id must be 1-64 characters, alphanumeric/hyphens/underscores, starting with alphanumeric")
    if "capabilities" not in msg:
        errors.append("Missing required field: capabilities")
    elif not isinstance(msg["capabilities"], dict):
        errors.append("capabilities must be a dict")
    return errors


def _error_frame(error: str, details: str | None = None) -> dict[str, Any]:
    """Build a generic error frame (the worker-channel equivalent of cascor's ``build_error``)."""
    frame: dict[str, Any] = {"type": "error", "error": error, "timestamp": time.time()}
    if details is not None:
        frame["details"] = details
    return frame


def _heartbeat_ack(worker_id: str) -> dict[str, Any]:
    """Build a heartbeat acknowledgement frame."""
    return {"type": MSG_HEARTBEAT, "worker_id": worker_id, "timestamp": time.time()}


async def worker_stream_handler(websocket: WebSocket) -> None:
    """Handle a ``/ws/workers`` WebSocket connection.

    Protocol flow: reject browser ``Origin`` (workers are machine-to-machine) -> authenticate
    (``X-API-Key``) -> per-source rate limit -> accept -> registration -> message loop
    (heartbeats / results, proactive dispatch).
    """
    # Reject connections with an Origin header (workers are machine-to-machine, not browsers).
    if websocket.headers.get("origin"):
        await websocket.close(code=4003, reason="Origin header not allowed on worker endpoint")
        return

    if not await ws_authenticate(websocket):
        return

    # Per-source connection rate limiting (before accepting the connection).
    rate_limiter = getattr(websocket.app.state, "worker_rate_limiter", None)
    if rate_limiter is not None:
        source_ip = websocket.client[0] if websocket.client else "unknown"
        if not rate_limiter.allow(source_ip):
            await websocket.close(code=4029, reason="Rate limited")
            return

    coordinator: WorkerCoordinator | None = getattr(websocket.app.state, "worker_coordinator", None)
    registry: WorkerRegistry | None = getattr(websocket.app.state, "worker_registry", None)
    if coordinator is None or registry is None:
        await websocket.close(code=4004, reason="Worker system not initialized")
        return

    await websocket.accept()
    await websocket.send_json({"type": "connection_established", "data": {"channel": WORKER_WS_ENDPOINT}})

    # Per-endpoint connection accounting (best-effort; the gauge only exists if a manager is wired).
    ws_manager = getattr(websocket.app.state, "ws_manager", None)
    if ws_manager is not None:
        ws_manager.register_endpoint_connection(websocket, WORKER_WS_ENDPOINT)

    worker_id: str | None = None
    audit_logger = getattr(websocket.app.state, "audit_logger", None)
    worker_metrics = getattr(websocket.app.state, "worker_metrics", None)

    try:
        worker_id = await _handle_registration(websocket, registry)
        if worker_id is None:
            return

        coordinator.register_send_callback(worker_id, _make_send_callback(websocket))

        if audit_logger is not None:
            from juniper_service_core.workers.audit import AuditEventType

            audit_logger.log(AuditEventType.WORKER_REGISTER, worker_id=worker_id)
        if worker_metrics is not None:
            source_ip = websocket.client[0] if websocket.client else ""
            worker_metrics.on_register(worker_id, source_ip)

        logger.info("Worker %s connected and registered", worker_id)

        await _message_loop(websocket, worker_id, registry, coordinator)

    except WebSocketDisconnect:
        logger.info("Worker %s disconnected", worker_id or "unknown")
    except Exception:
        logger.exception("Unexpected error in worker stream for %s", worker_id or "unknown")
    finally:
        if ws_manager is not None:
            ws_manager.unregister_endpoint_connection(websocket)
        if worker_id is not None:
            coordinator.unregister_send_callback(worker_id)
            # Reclaim before deregister: a clean disconnect used to leave the assigned
            # task stuck until task_reassignment_timeout (default 120s). The stale-heartbeat
            # sweep already requeued; this is the disconnect equivalent.
            coordinator.release_worker_tasks(worker_id)
            registry.deregister(worker_id)
            if audit_logger is not None:
                from juniper_service_core.workers.audit import AuditEventType

                audit_logger.log(AuditEventType.WORKER_DEREGISTER, worker_id=worker_id)
            if worker_metrics is not None:
                worker_metrics.on_deregister(worker_id)
            logger.info("Worker %s cleaned up", worker_id)


async def _handle_registration(websocket: WebSocket, registry: WorkerRegistry) -> str | None:
    """Wait for and process the worker registration message.

    The worker proposes a ``worker_id`` in its REGISTER payload, but the server does NOT trust it: it
    is captured as an untrusted ``client_name`` for audit only, and the server generates a fresh UUID
    as the authoritative id and returns it in the ``registration_ack`` payload.

    Returns:
        The server-assigned ``worker_id`` on success, ``None`` otherwise (the connection is closed).
    """
    raw = await websocket.receive_text()

    if len(raw) > _MAX_JSON_SIZE:
        await websocket.send_json(_error_frame("Registration message too large"))
        await websocket.close(code=4005, reason="Message too large")
        return None

    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        await websocket.send_json(_error_frame("Invalid JSON"))
        await websocket.close(code=4006, reason="Invalid JSON")
        return None

    # JSON-valid non-objects must not call ``msg.get`` / ``validate_worker_registration``
    # — treat as a registration shape failure (4008), never register.
    if not isinstance(msg, dict):
        await websocket.send_json(_error_frame("Invalid registration", details="Registration payload must be a JSON object"))
        await websocket.close(code=4008, reason="Invalid registration")
        return None

    if msg.get("type") != MSG_REGISTER:
        await websocket.send_json(_error_frame("First message must be registration"))
        await websocket.close(code=4007, reason="Expected registration")
        return None

    errors = validate_worker_registration(msg)
    if errors:
        await websocket.send_json(_error_frame("Invalid registration", details="; ".join(errors)))
        await websocket.close(code=4008, reason="Invalid registration")
        return None

    # The client-supplied worker_id is an untrusted display name; the server assigns the identity.
    client_name = msg["worker_id"]
    capabilities = msg["capabilities"]
    worker_id = f"worker-{uuid.uuid4().hex[:12]}"

    try:
        registry.register(worker_id, capabilities, client_name=client_name)
    except WorkerRegistryFullError as exc:
        logger.warning("Worker handshake rejected -- registry at capacity (client_name=%s): %s", client_name, exc)
        await websocket.send_json(_error_frame("Worker registry at capacity", details=str(exc)))
        await websocket.close(code=4013, reason="Worker registry at capacity")
        return None

    logger.info("Worker registered with server ID %s (client_name=%s)", worker_id, client_name)
    await websocket.send_json(
        {
            "type": "registration_ack",
            "worker_id": worker_id,
            "data": {"status": "registered", "client_name": client_name},
        }
    )
    return worker_id


async def _message_loop(websocket: WebSocket, worker_id: str, registry: WorkerRegistry, coordinator: WorkerCoordinator) -> None:
    """Main message-processing loop for a connected worker (heartbeats, results, proactive dispatch)."""
    # Dispatch immediately if work is already waiting.
    await _try_dispatch_task(websocket, worker_id, coordinator)

    while True:
        message = await websocket.receive()

        if "text" in message:
            raw = message["text"]
            if len(raw) > _MAX_JSON_SIZE:
                await websocket.send_json(_error_frame("Message too large"))
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(_error_frame("Invalid JSON"))
                continue

            msg_type = msg.get("type")

            if msg_type == MSG_HEARTBEAT:
                # Forward enriched heartbeat fields when present; absent keys stay None and the
                # registry preserves prior values (additive-compatible with older workers).
                registry.heartbeat(
                    worker_id,
                    in_flight_tasks=msg.get("in_flight_tasks"),
                    last_task_completed_at=msg.get("last_task_completed_at"),
                    rss_mb=msg.get("rss_mb"),
                    tasks_completed=msg.get("tasks_completed"),
                    tasks_failed=msg.get("tasks_failed"),
                    last_task_duration_seconds=msg.get("last_task_duration_seconds"),
                    recent_task_durations_seconds=msg.get("recent_task_durations_seconds"),
                    gpu_utilization_pct=msg.get("gpu_utilization_pct"),
                )
                await websocket.send_json(_heartbeat_ack(worker_id))

                # Deliver tasks submitted after this worker connected: a heartbeat is the trigger for
                # an already-idle worker to pick up newly-queued work (bounds dispatch latency to one
                # heartbeat interval). Guard on idle so a heartbeat mid-task does not double-dispatch.
                reg = registry.get(worker_id)
                if reg is not None and reg.idle:
                    await _try_dispatch_task(websocket, worker_id, coordinator)

            elif msg_type == MSG_TASK_RESULT:
                await _handle_task_result(websocket, worker_id, msg, coordinator)
                await _try_dispatch_task(websocket, worker_id, coordinator)

            else:
                await websocket.send_json(_error_frame(f"Unknown message type: {msg_type}"))

        elif "bytes" in message:
            # Binary frames are only expected as part of a task_result sequence (collected in
            # _handle_task_result). A stray frame here is ignored with a warning.
            logger.warning("Unexpected binary frame from worker %s (outside result sequence)", worker_id)


async def _handle_task_result(websocket: WebSocket, worker_id: str, msg: dict[str, Any], coordinator: WorkerCoordinator) -> None:
    """Handle a result message + its associated binary frames, then submit to the coordinator."""
    attachment_names = coordinator.protocol.result_attachments(msg)

    # Cardinality first, before any receive: the attachment list is worker-influenced, so an
    # over-long declaration must be refused outright rather than allowed to hold the handler in a
    # binary-receive loop it can keep feeding.
    if len(attachment_names) > _MAX_ATTACHMENTS:
        logger.error("Result from worker %s declares %d attachments (max %d) -- rejected", worker_id, len(attachment_names), _MAX_ATTACHMENTS)
        await websocket.send_json(_error_frame("Too many binary attachments", details=f"{len(attachment_names)} > {_MAX_ATTACHMENTS}"))
        return

    frames: dict[str, bytes] = {}
    total_bytes = 0

    # Receive one binary frame per attachment, in protocol-declared order.
    for name in attachment_names:
        frame_msg = await websocket.receive()
        if "bytes" not in frame_msg:
            logger.error("Expected binary frame for %s, got text from worker %s", name, worker_id)
            await websocket.send_json(_error_frame(f"Expected binary frame for: {name}"))
            coordinator.release_worker_tasks(worker_id, free_worker=True)
            return
        raw_bytes = frame_msg["bytes"]
        if len(raw_bytes) > _MAX_BINARY_SIZE:
            logger.error("Binary frame for %s exceeds size limit from worker %s", name, worker_id)
            await websocket.send_json(_error_frame("Binary frame too large"))
            coordinator.release_worker_tasks(worker_id, free_worker=True)
            return
        # Cumulative budget: the per-frame cap above bounds each item, not the sum, and every frame
        # accepted here is retained in ``frames`` until the submission completes.
        total_bytes += len(raw_bytes)
        if total_bytes > _MAX_TOTAL_BINARY_SIZE:
            logger.error("Attachments from worker %s exceed the total budget at %s (%d > %d bytes) -- rejected", worker_id, name, total_bytes, _MAX_TOTAL_BINARY_SIZE)
            await websocket.send_json(_error_frame("Binary attachments exceed total size limit"))
            return
        frames[name] = raw_bytes

    accepted = coordinator.submit_result(worker_id, msg, frames)
    await websocket.send_json(
        {
            "type": "result_ack",
            "task_id": msg.get("task_id"),
            "status": "accepted" if accepted else "rejected",
        }
    )


async def _try_dispatch_task(websocket: WebSocket, worker_id: str, coordinator: WorkerCoordinator) -> None:
    """Try to dispatch a pending task to this worker (JSON envelope + ordered binary frames)."""
    assignment = coordinator.get_next_assignment(worker_id)
    if assignment is None:
        return
    msg, frames = assignment
    await websocket.send_json(msg)
    for frame in frames:
        await websocket.send_bytes(frame)
    logger.debug("Dispatched task %s to worker %s", msg.get("task_id"), worker_id)


def _make_send_callback(websocket: WebSocket):
    """Create an async send callback for proactively pushing a message to this worker's socket."""

    async def callback(msg: dict[str, Any], frames: list[bytes] | None = None) -> bool:
        try:
            await websocket.send_json(msg)
            if frames:
                for frame in frames:
                    await websocket.send_bytes(frame)
            return True
        except Exception:
            return False

    return callback


def attach_worker_pool(
    app: Any,
    *,
    registry: WorkerRegistry,
    coordinator: WorkerCoordinator,
    rate_limiter: Any | None = None,
    audit_logger: Any | None = None,
    worker_metrics: Any | None = None,
    ws_manager: Any | None = None,
) -> WorkerCoordinator:
    """Wire the worker pool onto a FastAPI app's ``state`` for the ``/ws/workers`` handler.

    Sets ``app.state.worker_registry`` / ``worker_coordinator`` / ``worker_task_protocol`` (read from
    the coordinator) and -- when provided -- ``worker_rate_limiter`` / ``audit_logger`` /
    ``worker_metrics`` / ``ws_manager``. The omitted optionals leave the corresponding handler
    behaviour off (no rate limiting / no audit / no per-endpoint gauge), exactly as
    ``getattr(..., None)`` reads them. Idempotent on ``app.state``. The worker **router** is mounted
    separately via :func:`~juniper_service_core.websocket.router.build_worker_router`.

    Returns:
        The wired :class:`~juniper_service_core.workers.coordinator.WorkerCoordinator`.
    """
    app.state.worker_registry = registry
    app.state.worker_coordinator = coordinator
    app.state.worker_task_protocol = coordinator.protocol
    if rate_limiter is not None:
        app.state.worker_rate_limiter = rate_limiter
    if audit_logger is not None:
        app.state.audit_logger = audit_logger
    if worker_metrics is not None:
        app.state.worker_metrics = worker_metrics
    if ws_manager is not None:
        app.state.ws_manager = ws_manager
    return coordinator
