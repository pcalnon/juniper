"""WebSocket handler for ``/ws/training`` -- the real-time training-metrics stream (step 2).

The de-cascored core of cascor's ``api/websocket/training_stream.py``. Server-to-client
streaming with optional resume. On connect:

1. ``connection_established`` (from ``manager.connect_pending``).
2. Optional resume handshake: the client sends a ``resume`` frame within the timeout.
3. On resume success: replayed events + promote to active.
4. On a fresh connect: ``initial_status`` + ``state`` + an ``initial_metrics`` burst + promote.
5. Ongoing ``metrics`` / ``state`` broadcasts during training (pushed by the lifecycle bridge).

After promotion, the server sends application-level ``{"type":"ping","ts":<float>}`` heartbeats
every ``ws_heartbeat_interval_sec`` (default 30s); the client must reply ``{"type":"pong"}``
within ``ws_heartbeat_pong_timeout_sec`` (default 10s) or the connection is closed with close
code **1011** and reason ``"Heartbeat timeout: no pong or traffic within <N>s"``. It is
deliberately not 1006: RFC 6455 Section 7.4.1 reserves that value and forbids an endpoint from
setting it as a Close-frame status, and the ``websockets`` server raises rather than serialize
it -- so a 1006 close sends no frame at all and leaves the peer on a silent half-open socket.

De-cascored from cascor: reads the live state through the generic
:class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager` query surface
(``get_status`` / ``monitor.get_state`` / ``get_metrics_history``), drops cascor's
``api.observability`` emissions, and reads tunables off ``app.state.settings`` (with cascor's
defaults) instead of importing a service settings module.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from fastapi import WebSocket, WebSocketDisconnect

from juniper_service_core.websocket.manager import ReplayOutOfRange, ws_authenticate
from juniper_service_core.websocket.messages import create_initial_metrics_message, create_state_message
from juniper_service_core.websocket.tunables import resolve

__all__ = ["training_stream_handler"]

logger = logging.getLogger("juniper_service_core.websocket.training")


def _setting(websocket: WebSocket, name: str):
    """Resolve a declared tunable off ``app.state.settings`` (no service settings import).

    The default now lives in :data:`~juniper_service_core.websocket.tunables.WS_TUNABLES`
    rather than at each call site, and a miss that looks like a misspelling is logged
    loudly instead of silently defaulting -- see that module for why (APD-SVCCORE-003).
    """
    return resolve(getattr(websocket.app.state, "settings", None), name)


async def _await_resume_frame(websocket: WebSocket, ws_manager, resume_timeout: float) -> tuple[bool, bool]:
    """Wait for an optional resume frame.

    Returns ``(resumed, disconnected)``. If ``disconnected`` is ``True``, the caller should
    return without further work.
    """
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=resume_timeout)
        msg = json.loads(raw)
        if msg.get("type") == "resume":
            return await _handle_resume(websocket, ws_manager, msg), False
    except asyncio.TimeoutError:
        pass  # No resume frame -- fresh connect
    except json.JSONDecodeError:
        logger.debug("Non-JSON frame during resume handshake, treating as fresh connect")
    except WebSocketDisconnect:
        return False, True
    except Exception:  # noqa: BLE001 - any handshake error degrades to a fresh connect
        logger.debug("Error during resume handshake, treating as fresh connect")
    return False, False


async def _send_initial_state(websocket: WebSocket, ws_manager, lifecycle, initial_metrics_count: int = 100) -> None:
    """Send initial status + state + a recent-metrics burst to a freshly-connected client.

    ``initial_metrics`` is sent after ``state`` so a client can paint its time-series chart
    without a parallel REST poll. ``initial_metrics_count=0`` disables the burst.
    """
    if lifecycle is None:
        return
    status = lifecycle.get_status()
    await ws_manager.send_personal_message(websocket, {"type": "initial_status", "data": status})
    state_data = lifecycle.monitor.get_state()
    await ws_manager.send_personal_message(websocket, create_state_message(state_data))
    if initial_metrics_count > 0:
        await _send_metrics_burst(websocket, ws_manager, lifecycle, initial_metrics_count)


async def _send_metrics_burst(websocket: WebSocket, ws_manager, lifecycle, count: int) -> None:
    """Send an ``initial_metrics`` burst with the most-recent metrics."""
    try:
        metrics = lifecycle.get_metrics_history(count=count)
    except Exception:  # noqa: BLE001 - a history read must not abort the connect path
        logger.debug("Training WS: get_metrics_history failed; sending empty burst", exc_info=True)
        metrics = []
    if metrics is None:
        metrics = []
    await ws_manager.send_personal_message(websocket, create_initial_metrics_message(metrics, current_seq=ws_manager.current_seq))


async def _heartbeat_ping_loop(websocket: WebSocket, hb_interval: float, hb_timeout: float, pong_received: asyncio.Event) -> None:
    """Application-level ping/pong loop closing the connection on pong timeout."""
    while True:
        await asyncio.sleep(hb_interval)
        pong_received.clear()
        try:
            await websocket.send_json({"type": "ping", "ts": time.time()})
        except Exception:  # noqa: BLE001 - connection already closed
            return
        try:
            await asyncio.wait_for(pong_received.wait(), timeout=hb_timeout)
        except asyncio.TimeoutError:
            logger.info("Training WS: heartbeat timeout, closing -- no pong or traffic within %.0fs of ping (interval=%.0fs)", hb_timeout, hb_interval)
            try:
                # 1011, not 1006 -- RFC 6455 Section 7.4.1 forbids an endpoint from setting 1006
                # as a Close-frame status, and the ``websockets`` server raises rather than
                # serialize it, so the peer would be left with a silent half-open socket.
                # See the fuller note at the matching site in ``control_stream.py``.
                await websocket.close(code=1011, reason=f"Heartbeat timeout: no pong or traffic within {hb_timeout:.0f}s")
            except Exception:  # noqa: BLE001 - close after timeout is best-effort
                logger.debug("Training WS: close after heartbeat timeout failed", exc_info=True)
            return


async def _recv_pong_loop(websocket: WebSocket, pong_received: asyncio.Event, ws_manager=None, lifecycle=None, subscribe_metrics_max_count: int = 100) -> None:
    """Receive-loop dispatcher.

    Forwards ``pong`` frames to the heartbeat event and handles ``subscribe_metrics`` requests
    by replying with an ``initial_metrics`` envelope. All other frame types are ignored.
    """
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, AttributeError):
                continue  # Non-JSON keep-alive frames are fine
            mtype = msg.get("type") if isinstance(msg, dict) else None
            if mtype == "pong":
                pong_received.set()
            elif mtype == "subscribe_metrics" and ws_manager is not None and lifecycle is not None:
                await _handle_subscribe_metrics(websocket, ws_manager, lifecycle, msg, subscribe_metrics_max_count)
    except WebSocketDisconnect:
        logger.debug("Training WS: receive loop ended due to client disconnect")
        return


async def _handle_subscribe_metrics(websocket: WebSocket, ws_manager, lifecycle, msg: dict, default_count: int) -> None:
    """Respond to a client ``subscribe_metrics`` with a metrics burst.

    Used when a client reconnects via the resume path (which only replays ``seq>last_seq`` from
    the broadcast buffer) but also wants the rolling metrics window.
    """
    data = msg.get("data") or {}
    requested = data.get("max_count")
    try:
        count = int(requested) if requested is not None else default_count
    except (TypeError, ValueError):
        count = default_count
    count = max(1, min(count, default_count))
    await _send_metrics_burst(websocket, ws_manager, lifecycle, count)


async def training_stream_handler(websocket: WebSocket) -> None:
    """Handle ``/ws/training`` WebSocket connections with optional resume.

    Protocol flow:
    1. Authenticate via the API-key header.
    2. Accept as pending (``connect_pending`` -- not broadcast-eligible).
    3. Wait for an optional ``resume`` frame within the handshake timeout.
    4. On resume: validate ``server_instance_id``, replay buffered events.
    5. On fresh connect / failed resume: send ``initial_status`` + ``state``.
    6. Promote to active (now receives broadcasts).
    7. Heartbeat + keep-alive recv loop.
    """
    if not await ws_authenticate(websocket):
        return

    ws_manager = getattr(websocket.app.state, "ws_manager", None)
    lifecycle = getattr(websocket.app.state, "lifecycle", None)

    if ws_manager is None:
        await websocket.close(code=1011, reason="WebSocket manager not available")
        return

    # Capture the serving loop so the training thread's broadcast_from_thread can reach it. The
    # handler runs on the app's event loop, so this needs no separate startup hook (idempotent).
    ws_manager.set_event_loop(asyncio.get_running_loop())

    connected = await ws_manager.connect_pending(websocket)
    if not connected:
        return

    resume_timeout = _setting(websocket, "ws_resume_handshake_timeout_s")
    initial_metrics_count = _setting(websocket, "ws_initial_metrics_count")

    try:
        resumed, disconnected = await _await_resume_frame(websocket, ws_manager, resume_timeout)
        if disconnected:
            return

        # Promote to active (now eligible for broadcasts).
        await ws_manager.promote_to_active(websocket)
        ws_manager.register_endpoint_connection(websocket, "training")

        if not resumed:
            await _send_initial_state(websocket, ws_manager, lifecycle, initial_metrics_count)

        # Broadcasts come from the training thread via ws_manager.broadcast_from_thread() (wired
        # by the lifecycle bridge). The recv loop handles pong responses and subscribe_metrics.
        hb_interval = _setting(websocket, "ws_heartbeat_interval_sec")
        hb_timeout = _setting(websocket, "ws_heartbeat_pong_timeout_sec")
        pong_received = asyncio.Event()
        pong_received.set()  # No outstanding ping at start

        ping_task = asyncio.create_task(_heartbeat_ping_loop(websocket, hb_interval, hb_timeout, pong_received))
        try:
            await _recv_pong_loop(websocket, pong_received, ws_manager=ws_manager, lifecycle=lifecycle, subscribe_metrics_max_count=initial_metrics_count or 100)
        finally:
            ping_task.cancel()
            try:
                await ping_task
                # Expected when awaiting a task after explicit cancellation during shutdown.
            except asyncio.CancelledError:
                pass
    finally:
        ws_manager.unregister_endpoint_connection(websocket)
        await ws_manager.disconnect(websocket)


async def _handle_resume(websocket: WebSocket, ws_manager, msg: dict) -> bool:
    """Handle a resume request. Returns ``True`` if resume succeeded."""
    data = msg.get("data", {})
    last_seq = data.get("last_seq")
    client_server_id = data.get("server_instance_id")

    if last_seq is None or client_server_id is None:
        await ws_manager.send_personal_message(
            websocket,
            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "malformed_resume"}},
        )
        logger.debug("Resume failed: malformed resume frame (missing last_seq or server_instance_id)")
        return False

    # Server-restart detection via UUID mismatch.
    if client_server_id != ws_manager.server_instance_id:
        await ws_manager.send_personal_message(
            websocket,
            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "server_restarted"}},
        )
        logger.info("Resume failed: server_instance_id mismatch (server restarted)")
        return False

    try:
        events = ws_manager.replay_since(last_seq)
    except ReplayOutOfRange as e:
        await ws_manager.send_personal_message(
            websocket,
            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "out_of_range"}},
        )
        logger.info("Resume failed: %s", e)
        return False

    # Resume succeeded.
    await ws_manager.send_personal_message(
        websocket,
        {"type": "resume_ok", "timestamp": time.time(), "data": {"replayed_count": len(events)}},
    )
    for event in events:
        await ws_manager.send_personal_message(websocket, event)
    logger.info("Resume succeeded: replayed %d events from seq %d", len(events), last_seq)
    return True
