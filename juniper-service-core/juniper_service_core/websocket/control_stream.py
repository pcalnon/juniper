"""WebSocket handler for ``/ws/control`` -- the training command channel (step 2).

The de-cascored core of cascor's ``api/websocket/control_stream.py``. A client-to-server command
endpoint that accepts JSON commands::

    {"command": "start"|"stop"|"pause"|"resume"|"reset"|"set_params",
     "command_id": "<optional-uuid>",   # echoed back for correlation
     "params": { ... }}                  # optional, for start/set_params

and replies with ``command_response`` acknowledgments (no ``seq`` -- the control channel has no
replay buffer).

**The decoupling change (design §5.6).** cascor hard-wired an ``_execute_command`` that called its
own lifecycle verbs. Here, each command is dispatched to an injectable
:class:`~juniper_service_core.websocket.commands.CommandExecutor` read off
``app.state.command_executor`` (e.g. the default
:class:`~juniper_service_core.websocket.commands.LifecycleCommandExecutor`). The base hard-codes
no verb semantics.

Security gates (per-connection leaky bucket, per-origin handshake cooldown, idle timeout, origin
allowlist, optional API key) are preserved; all tunables are read off ``app.state.settings`` (with
cascor's defaults) rather than importing a service settings module, and cascor's
``api.observability`` emissions are dropped. Per-command execution timeouts and the
``asyncio.to_thread`` dispatch (so a blocking executor never wedges the event loop) are retained.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from fastapi import WebSocket, WebSocketDisconnect

from juniper_service_core.websocket.commands import DEFAULT_COMMANDS
from juniper_service_core.websocket.control_security import HandshakeCooldown, LeakyBucket, validate_control_origin
from juniper_service_core.websocket.manager import ws_authenticate
from juniper_service_core.websocket.messages import create_control_ack_message
from juniper_service_core.websocket.tunables import resolve

__all__ = ["control_stream_handler"]


def _sanitize_for_log(value: object) -> str:
    """Return a single-line, control-char-safe representation for logging."""
    text = str(value)
    text = text.replace("\r", "").replace("\n", "")
    return "".join(ch for ch in text if ch >= " " or ch == "\t")


logger = logging.getLogger("juniper_service_core.websocket.control")

_MAX_MESSAGE_SIZE = 65536  # 64KB

#: Per-command execution timeouts (seconds); ``start`` is the long pole.
_COMMAND_TIMEOUTS: dict[str, float] = {
    "start": 10.0,
    "stop": 2.0,
    "pause": 2.0,
    "resume": 2.0,
    "reset": 2.0,
    "set_params": 1.0,
}


def _setting(websocket: WebSocket, name: str):
    """Resolve a declared tunable off ``app.state.settings`` (no service settings import).

    The default now lives in :data:`~juniper_service_core.websocket.tunables.WS_TUNABLES`
    rather than at each call site, and a miss that looks like a misspelling is logged
    loudly instead of silently defaulting -- see that module for why (APD-SVCCORE-003).
    """
    return resolve(getattr(websocket.app.state, "settings", None), name)


def _get_client_ip(websocket: WebSocket) -> str:
    """Extract the client IP from the WebSocket connection."""
    if websocket.client:
        return websocket.client[0]
    return "unknown"


def _get_cooldown(websocket: WebSocket) -> HandshakeCooldown:
    """Lazily build the per-app handshake cooldown from settings and cache it on ``app.state``.

    Shared across connections on one server (cleared on restart). Cached on ``app.state`` rather
    than a module global so multiple apps in one process keep independent cooldown state.
    """
    app = websocket.app
    cooldown = getattr(app.state, "ws_control_cooldown", None)
    if cooldown is None:
        cooldown = HandshakeCooldown(
            max_rejections=_setting(websocket, "ws_control_cooldown_rejections"),
            window_sec=_setting(websocket, "ws_control_cooldown_window_sec"),
            block_sec=_setting(websocket, "ws_control_cooldown_block_sec"),
        )
        app.state.ws_control_cooldown = cooldown
    return cooldown


async def _check_handshake_gates(websocket: WebSocket, client_ip: str) -> bool:
    """Run pre-accept handshake gates. Returns ``True`` if the connection may proceed.

    **The distinct close codes below never reach the client, and that is correct** -- do not "fix"
    it (``APD-SVCCORE-016``, triaged 2026-08-29 as won't-fix). Every gate here runs *before*
    ``websocket.accept()``, so the connection is still an HTTP request: uvicorn converts a pre-accept
    close into a plain **HTTP 403** and discards both the code and the reason
    (``uvicorn/protocols/websockets/websockets_impl.py``; the sans-io implementation does the same).
    So ``1013`` "Control endpoint disabled", ``4029`` "Too many rejected handshakes", ``4003``
    "Origin not allowed" and ``manager.py``'s ``4001`` are all indistinguishable to the caller.

    Three reasons this stays as it is:

    * **It is what the RFC recommends.** A handshake failure is still HTTP, and RFC 6455 §10.2
      recommends ``403 Forbidden`` for an unacceptable Origin. Collapsing to 403 is conformant
      behaviour, not a defect in this function.
    * **The obvious "fix" is a regression.** Making the codes observable requires accepting the
      socket *first* and then closing it. The primer criticises exactly that pattern -- it is
      "harder for the client to distinguish from a network failure" -- and it would also mean
      completing a handshake for a caller the kill switch, the cooldown or the Origin allowlist has
      already refused. Rejecting before accept is the stronger posture and must be preserved.
    * **The codes are not wasted.** They are the honest ASGI-level reason and survive in
      ``uvicorn``'s own logging; only the wire representation collapses.

    The register's first wording for this row claimed these gates closed *after* accepting, which was
    a false positive -- corrected 2026-08-28. The ordering asserted here (all four rejections
    pre-accept, ``accept()`` strictly after) is the property worth protecting.
    """
    if _setting(websocket, "disable_ws_control_endpoint"):
        await websocket.close(code=1013, reason="Control endpoint disabled")
        return False

    cooldown = _get_cooldown(websocket)
    if cooldown.is_blocked(client_ip):
        remaining = cooldown.get_block_remaining(client_ip)
        logger.warning("Control WS: IP %s blocked (cooldown), remaining=%ss", client_ip, remaining)
        await websocket.close(code=4029, reason="Too many rejected handshakes")
        return False

    if not await ws_authenticate(websocket):
        cooldown.record_rejection(client_ip)
        return False

    allowed_origins = _setting(websocket, "ws_control_allowed_origins")
    if allowed_origins:
        if not validate_control_origin(websocket, allowed_origins):
            cooldown.record_rejection(client_ip)
            await websocket.close(code=4003, reason="Origin not allowed")
            return False

    return True


async def _handle_command_message(websocket: WebSocket, executor, valid_commands: set[str], msg: dict, bucket: LeakyBucket) -> None:
    """Validate and dispatch a single command message; send the response."""
    command = msg.get("command", "")
    safe_command = _sanitize_for_log(command)
    command_id = msg.get("command_id")

    if not bucket.try_acquire():
        await websocket.send_json(create_control_ack_message(command, "rate_limited", data={"retry_after": bucket.retry_after}, command_id=command_id))
        return

    if command not in valid_commands:
        await websocket.send_json(create_control_ack_message(command, "error", error=f"Unknown command: {command}", command_id=command_id, code="unknown_command"))
        return

    if executor is None:
        await websocket.send_json(create_control_ack_message(command, "error", error="Control executor not available", command_id=command_id))
        return

    timeout = _COMMAND_TIMEOUTS.get(command, 2.0)
    # Dispatch off the event loop so a blocking executor cannot wedge it; bound by the timeout.
    try:
        result = await asyncio.wait_for(asyncio.to_thread(executor.execute, command, msg.get("params")), timeout=timeout)
        await websocket.send_json(create_control_ack_message(command, "success", data=result, command_id=command_id))
    except asyncio.TimeoutError:
        logger.error("Command '%s' timed out after %ss", safe_command, timeout)
        await websocket.send_json(create_control_ack_message(command, "error", error=f"Command timed out after {timeout}s", command_id=command_id))
    except (ValueError, RuntimeError) as exc:
        # Expected control errors (bad params / invalid state transition) -- surface the message.
        logger.info("Command '%s' rejected: %s", safe_command, exc)
        await websocket.send_json(create_control_ack_message(command, "error", error=str(exc), command_id=command_id))
    except Exception as exc:  # noqa: BLE001 - an unexpected executor failure stays opaque to the client
        logger.error("Command '%s' failed: %s", safe_command, exc)
        await websocket.send_json(create_control_ack_message(command, "error", error="Command execution failed", command_id=command_id))


async def _control_ping_loop(websocket: WebSocket, client_ip: str, hb_interval: float, hb_timeout: float, pong_received: asyncio.Event) -> None:
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
            logger.info("Control WS: heartbeat timeout, closing %s -- no pong or traffic within %.0fs of ping (interval=%.0fs)", client_ip, hb_timeout, hb_interval)
            try:
                # 1011, not 1006. RFC 6455 Section 7.4.1 reserves 1006 and forbids an endpoint
                # from setting it as a Close-frame status: it exists for *receivers* to report an
                # abnormal closure that carried no Close frame at all. The ``websockets`` server
                # under uvicorn enforces this and raises on serialization, so a 1006 close frame
                # never reaches the peer -- the client is left holding a silent half-open socket
                # with no reason string. juniper-cascor hit exactly this on 2026-07-10 and fixed
                # its own copy; this is the same fix for the shared implementation.
                await websocket.close(code=1011, reason=f"Heartbeat timeout: no pong or traffic within {hb_timeout:.0f}s")
            except Exception:  # noqa: BLE001 - close after timeout is best-effort
                logger.debug("Control WS: close after heartbeat timeout failed for %s", client_ip, exc_info=True)
            return


async def _control_recv_loop(websocket: WebSocket, executor, valid_commands: set[str], bucket: LeakyBucket, pong_received: asyncio.Event, idle_timeout: float, client_ip: str) -> None:
    """Receive loop: enforce idle timeout, dispatch commands, route pong frames."""
    while True:
        try:
            if idle_timeout and idle_timeout > 0:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=idle_timeout)
            else:
                raw = await websocket.receive_text()
        except asyncio.TimeoutError:
            logger.info("Control WS: idle timeout (%ss), closing: %s", idle_timeout, client_ip)
            await websocket.close(code=1000, reason="Idle timeout")
            return

        if len(raw) > _MAX_MESSAGE_SIZE:
            # Close rather than ``continue`` (``APD-SVCCORE-005``). The size check necessarily runs
            # *after* ``receive_text()`` has already materialised the frame -- that part is a
            # property of the transport, not something this loop can fix, and the real ceiling is
            # uvicorn's ``ws_max_size`` (16 MiB by default, unset here). What *was* fixable is that
            # ``continue`` let the same connection repeat that allocation indefinitely: the oversize
            # path returns before ``_handle_command_message``, which is the only place the rate-limit
            # token is spent, so every oversize frame was free. Charging the bucket instead would be
            # accounting rather than protection -- the allocation has already happened by then.
            # Closing is also what this loop already does for the adjacent protocol violations
            # (malformed JSON, non-object JSON); an over-limit frame is the same class of client
            # fault, and reconnection is governed by the handshake cooldown.
            # 1009 is RFC 6455's "Message Too Big", which no other gate here uses.
            await websocket.send_json(create_control_ack_message("unknown", "error", error="Message too large"))
            await websocket.close(code=1009, reason="Message too large")
            return

        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await websocket.send_json(create_control_ack_message("unknown", "error", error="Invalid JSON"))
            await websocket.close(code=1003, reason="Malformed JSON")
            return

        # JSON-valid non-objects (arrays / scalars / null) must not reach
        # ``_handle_command_message``'s ``msg.get`` — that AttributeError would
        # tear down the receive loop instead of a controlled reject/close.
        if not isinstance(msg, dict):
            await websocket.send_json(create_control_ack_message("unknown", "error", error="Invalid control message"))
            await websocket.close(code=1003, reason="Malformed JSON")
            return

        if msg.get("type") == "pong":
            # The other path that reaches ``continue`` without spending a rate-limit token, and
            # deliberately so (``APD-SVCCORE-005``). The bucket is the *command* budget -- its
            # tunable is ``ws_control_rate_limit_per_sec``, "control-command rate limit" -- and pong
            # is keepalive, not command traffic. Charging it would let a burst of legitimate
            # commands exhaust the budget and rate-limit the client's pong, which
            # ``_control_heartbeat_loop`` then reads as a dead peer and closes with 1011: a
            # self-inflicted disconnect on a healthy connection. A pong is bounded by
            # ``_MAX_MESSAGE_SIZE`` like any other frame and does no work beyond setting an event.
            pong_received.set()
            continue

        await _handle_command_message(websocket, executor, valid_commands, msg, bucket)


async def control_stream_handler(websocket: WebSocket) -> None:
    """Handle ``/ws/control`` WebSocket connections.

    Security gates: kill switch -> handshake cooldown (IP block) -> API-key auth -> Origin
    allowlist -> per-connection leaky-bucket rate limiting -> bidirectional idle timeout.
    Commands are dispatched to ``app.state.command_executor``.
    """
    client_ip = _get_client_ip(websocket)

    if not await _check_handshake_gates(websocket, client_ip):
        return

    executor = getattr(websocket.app.state, "command_executor", None)
    ws_manager = getattr(websocket.app.state, "ws_manager", None)
    valid_commands = set(getattr(executor, "commands", DEFAULT_COMMANDS)) if executor is not None else set(DEFAULT_COMMANDS)

    await websocket.accept()
    await websocket.send_json({"type": "connection_established", "data": {"channel": "control"}})
    if ws_manager is not None:
        ws_manager.register_endpoint_connection(websocket, "control")

    rate_limit = _setting(websocket, "ws_control_rate_limit_per_sec")
    bucket = LeakyBucket(capacity=rate_limit, refill_rate=float(rate_limit))
    idle_timeout = _setting(websocket, "ws_control_idle_timeout_sec")

    hb_interval = _setting(websocket, "ws_heartbeat_interval_sec")
    hb_timeout = _setting(websocket, "ws_heartbeat_pong_timeout_sec")
    pong_received = asyncio.Event()
    pong_received.set()  # No outstanding ping at start

    ping_task = asyncio.create_task(_control_ping_loop(websocket, client_ip, hb_interval, hb_timeout, pong_received))

    try:
        await _control_recv_loop(websocket, executor, valid_commands, bucket, pong_received, idle_timeout, client_ip)
    except WebSocketDisconnect:
        pass
    finally:
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            logger.debug("Control WS: ping task cancelled during connection teardown: %s", client_ip)
        if ws_manager is not None:
            ws_manager.unregister_endpoint_connection(websocket)
