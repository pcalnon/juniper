"""Edge-path coverage for the ``/ws/control`` handler internals (C-4a).

The both-stacks-green contract test drives the happy control path through ``TestClient``. This
module unit-tests the rejection gates, the command-dispatch error arms (executor-missing /
timeout / unexpected-exception), the heartbeat ping loop, and the receive loop (idle timeout /
oversized / malformed-JSON / pong routing) directly with fake sockets -- deterministic, no
transport threading.

Also pins ``_sanitize_for_log`` (broader than the security-module strip: drops other
control chars) and the command-dispatch log path so a CRLF/control-char command name
cannot forge multi-line control-plane ERROR/INFO records.
"""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import pathlib
import threading
import types

import pytest
from fastapi import WebSocketDisconnect

import juniper_service_core.websocket.control_stream as control_stream
from juniper_service_core.security import build_api_key_auth
from juniper_service_core.websocket.control_security import HandshakeCooldown, LeakyBucket
from juniper_service_core.websocket.control_stream import (
    _check_handshake_gates,
    _control_ping_loop,
    _control_recv_loop,
    _get_client_ip,
    _handle_command_message,
    _sanitize_for_log,
    control_stream_handler,
)

_HANG = object()


def _settings(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = {
        "disable_ws_control_endpoint": False,
        "ws_control_cooldown_rejections": 10,
        "ws_control_cooldown_window_sec": 60,
        "ws_control_cooldown_block_sec": 300,
        "ws_control_allowed_origins": None,
        "ws_control_rate_limit_per_sec": 10,
        "ws_control_idle_timeout_sec": 120,
        "ws_heartbeat_interval_sec": 30,
        "ws_heartbeat_pong_timeout_sec": 10,
    }
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _app(**state: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(state=types.SimpleNamespace(**state))


class ControlFakeWS:
    """A control-channel fake socket: async accept / send_json / close / receive_text."""

    def __init__(self, *, client: tuple[str, int] | None = ("1.2.3.4", 5000), headers: dict | None = None, app: types.SimpleNamespace | None = None, incoming: list | None = None) -> None:
        self.client = client
        self.headers = headers or {}
        self.app = app or _app()
        self.sent: list[dict] = []
        self.accepted = False
        self.closed: tuple[int, str] | None = None
        self._incoming = list(incoming or [])

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._incoming:
            raise WebSocketDisconnect(code=1000)
        item = self._incoming.pop(0)
        if item is _HANG:
            await asyncio.Event().wait()
        if isinstance(item, BaseException):
            raise item
        return item


class SendFailWS(ControlFakeWS):
    async def send_json(self, message: dict) -> None:
        raise RuntimeError("socket gone")


class CloseFailAfterSendWS(ControlFakeWS):
    async def close(self, code: int = 1000, reason: str = "") -> None:
        raise RuntimeError("close failed")


# ----------------------------------------------------------------------------------------
# Client-IP helper
# ----------------------------------------------------------------------------------------


def test_get_client_ip_returns_peer() -> None:
    assert _get_client_ip(ControlFakeWS(client=("5.6.7.8", 42))) == "5.6.7.8"


def test_get_client_ip_unknown_without_client() -> None:
    assert _get_client_ip(ControlFakeWS(client=None)) == "unknown"


# ----------------------------------------------------------------------------------------
# Log sanitizer (control-char / CRLF injection)
# ----------------------------------------------------------------------------------------


def test_sanitize_for_log_strips_crlf_and_control_chars() -> None:
    # Broader than control_security: also drop BEL / other C0 controls (keep tab).
    dirty = "start\r\ninjected\x07\x1bX\tok"
    clean = _sanitize_for_log(dirty)
    assert "\r" not in clean
    assert "\n" not in clean
    assert "\x07" not in clean
    assert "\x1b" not in clean
    assert "\t" in clean
    # BEL + ESC dropped; printable X and tab kept.
    assert clean == "startinjectedX\tok"
    assert _sanitize_for_log(None) == "None"
    assert _sanitize_for_log(12) == "12"


@pytest.mark.asyncio
async def test_handle_command_reject_log_is_single_line(caplog) -> None:
    # A CRLF command name that reaches the executor-reject log must stay one line.
    class _RejectingExecutor:
        commands = ("start\ninjected",)

        def execute(self, command: str, params: dict | None) -> dict:
            raise ValueError("bad params")

    malicious = "start\ninjected"
    ws = ControlFakeWS()
    with caplog.at_level(logging.INFO, logger=control_stream.logger.name):
        await _handle_command_message(ws, _RejectingExecutor(), {malicious}, {"command": malicious}, LeakyBucket())
    assert ws.sent[-1]["data"]["status"] == "error"
    reject_msgs = [r.getMessage() for r in caplog.records if "rejected" in r.getMessage()]
    assert reject_msgs, "expected a command-rejected log line"
    for msg in reject_msgs:
        assert "\n" not in msg
        assert "\r" not in msg
        assert "injected" in msg


# ----------------------------------------------------------------------------------------
# Handshake gates
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handshake_gate_rejects_when_disabled() -> None:
    ws = ControlFakeWS(app=_app(settings=_settings(disable_ws_control_endpoint=True)))
    assert await _check_handshake_gates(ws, "1.2.3.4") is False
    assert ws.closed == (1013, "Control endpoint disabled")


@pytest.mark.asyncio
async def test_handshake_gate_rejects_blocked_ip() -> None:
    cooldown = HandshakeCooldown(max_rejections=1, block_sec=300)
    cooldown.record_rejection("1.2.3.4")  # max=1 -> blocked immediately
    ws = ControlFakeWS(app=_app(settings=_settings(), ws_control_cooldown=cooldown))
    assert await _check_handshake_gates(ws, "1.2.3.4") is False
    assert ws.closed == (4029, "Too many rejected handshakes")


@pytest.mark.asyncio
async def test_handshake_gate_rejects_failed_auth() -> None:
    auth = build_api_key_auth(["s3cret"])
    ws = ControlFakeWS(headers={}, app=_app(settings=_settings(), api_key_auth=auth))
    assert await _check_handshake_gates(ws, "1.2.3.4") is False


@pytest.mark.asyncio
async def test_handshake_gate_rejects_bad_origin() -> None:
    ws = ControlFakeWS(headers={"origin": "https://evil.example"}, app=_app(settings=_settings(ws_control_allowed_origins=["https://good.example"])))
    assert await _check_handshake_gates(ws, "1.2.3.4") is False
    assert ws.closed == (4003, "Origin not allowed")


@pytest.mark.asyncio
async def test_handshake_gate_allows_clean_connection() -> None:
    ws = ControlFakeWS(app=_app(settings=_settings()))
    assert await _check_handshake_gates(ws, "1.2.3.4") is True


# ----------------------------------------------------------------------------------------
# Command dispatch error arms
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_command_executor_unavailable() -> None:
    ws = ControlFakeWS()
    await _handle_command_message(ws, None, {"start"}, {"command": "start"}, LeakyBucket())
    assert ws.sent[-1]["data"]["status"] == "error"
    assert "not available" in ws.sent[-1]["data"]["error"]


@pytest.mark.asyncio
async def test_handle_command_unexpected_exception() -> None:
    class _RaisingExecutor:
        commands = ("start",)

        def execute(self, command: str, params: dict | None) -> dict:
            raise KeyError("unexpected")

    ws = ControlFakeWS()
    await _handle_command_message(ws, _RaisingExecutor(), {"start"}, {"command": "start"}, LeakyBucket())
    assert ws.sent[-1]["data"]["status"] == "error"
    assert ws.sent[-1]["data"]["error"] == "Command execution failed"


@pytest.mark.asyncio
async def test_handle_command_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    class _BlockingExecutor:
        commands = ("start",)

        def execute(self, command: str, params: dict | None) -> dict:
            release.wait(timeout=5)  # released in the test's finally; safety-bounded
            return {"ok": True}

    monkeypatch.setattr(control_stream, "_COMMAND_TIMEOUTS", {"start": 0.05})
    ws = ControlFakeWS()
    try:
        await _handle_command_message(ws, _BlockingExecutor(), {"start"}, {"command": "start"}, LeakyBucket())
        assert ws.sent[-1]["data"]["status"] == "error"
        assert "timed out" in ws.sent[-1]["data"]["error"]
    finally:
        release.set()


@pytest.mark.asyncio
async def test_handle_command_timeout_log_is_single_line(monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    """Timeout ERROR must stay single-line when ``command`` carries CRLF/control chars.

    Complements open #961's reject-path pin: timeout / unexpected-failure also
    interpolate ``safe_command`` and are equally forgeable if sanitizing regresses.
    """
    release = threading.Event()
    malicious = "start\r\ninjected\x07"

    class _BlockingExecutor:
        commands = (malicious,)

        def execute(self, command: str, params: dict | None) -> dict:
            release.wait(timeout=5)
            return {"ok": True}

    monkeypatch.setattr(control_stream, "_COMMAND_TIMEOUTS", {malicious: 0.05})
    ws = ControlFakeWS()
    try:
        with caplog.at_level(logging.ERROR, logger=control_stream.logger.name):
            await _handle_command_message(ws, _BlockingExecutor(), {malicious}, {"command": malicious}, LeakyBucket())
        assert ws.sent[-1]["data"]["status"] == "error"
        assert "timed out" in ws.sent[-1]["data"]["error"]
        timeout_msgs = [r.getMessage() for r in caplog.records if "timed out" in r.getMessage()]
        assert timeout_msgs, "expected a command-timeout ERROR log line"
        for msg in timeout_msgs:
            assert "\n" not in msg
            assert "\r" not in msg
            assert "\x07" not in msg
            assert "injected" in msg
    finally:
        release.set()


@pytest.mark.asyncio
async def test_handle_command_failed_log_is_single_line(caplog) -> None:
    """Unexpected-failure ERROR must stay single-line when ``command`` carries CRLF/control chars."""
    malicious = "start\ninjected\x1bX"

    class _RaisingExecutor:
        commands = (malicious,)

        def execute(self, command: str, params: dict | None) -> dict:
            raise KeyError("boom")

    ws = ControlFakeWS()
    with caplog.at_level(logging.ERROR, logger=control_stream.logger.name):
        await _handle_command_message(ws, _RaisingExecutor(), {malicious}, {"command": malicious}, LeakyBucket())
    assert ws.sent[-1]["data"]["status"] == "error"
    assert ws.sent[-1]["data"]["error"] == "Command execution failed"
    failed_msgs = [r.getMessage() for r in caplog.records if "failed:" in r.getMessage()]
    assert failed_msgs, "expected a command-failed ERROR log line"
    for msg in failed_msgs:
        assert "\n" not in msg
        assert "\r" not in msg
        assert "\x1b" not in msg
        assert "injected" in msg


@pytest.mark.asyncio
async def test_handle_command_rate_limited() -> None:
    ws = ControlFakeWS()
    bucket = LeakyBucket(capacity=0, refill_rate=0.0001)  # no tokens -> rate-limited
    await _handle_command_message(ws, None, {"start"}, {"command": "start"}, bucket)
    assert ws.sent[-1]["data"]["status"] == "rate_limited"


# ----------------------------------------------------------------------------------------
# Heartbeat ping loop
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_control_ping_loop_closes_on_pong_timeout() -> None:
    ws = ControlFakeWS()
    await _control_ping_loop(ws, "1.2.3.4", 0.001, 0.001, asyncio.Event())
    code, reason = ws.closed
    # 1011 (internal error), never 1006. RFC 6455 Section 7.4.1 reserves 1006 and forbids an
    # endpoint from setting it as a Close-frame status; the ``websockets`` server raises rather
    # than serialize it, so a 1006 close never reaches the peer and the client is left holding a
    # silent half-open socket. Asserting the exact code -- and asserting 1006 explicitly -- is
    # what stops that regression coming back.
    assert code == 1011
    assert code != 1006
    assert reason.startswith("Heartbeat timeout")
    assert any(m.get("type") == "ping" for m in ws.sent)


@pytest.mark.asyncio
async def test_control_ping_loop_returns_on_send_failure() -> None:
    ws = SendFailWS()
    await _control_ping_loop(ws, "1.2.3.4", 0.001, 5.0, asyncio.Event())
    assert ws.closed is None


@pytest.mark.asyncio
async def test_control_ping_loop_swallows_close_failure() -> None:
    ws = CloseFailAfterSendWS()
    await _control_ping_loop(ws, "1.2.3.4", 0.001, 0.001, asyncio.Event())


# ----------------------------------------------------------------------------------------
# Receive loop
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recv_loop_idle_timeout_closes() -> None:
    ws = ControlFakeWS(incoming=[_HANG])
    await _control_recv_loop(ws, None, {"start"}, LeakyBucket(), asyncio.Event(), idle_timeout=0.01, client_ip="1.2.3.4")
    assert ws.closed == (1000, "Idle timeout")


@pytest.mark.asyncio
async def test_recv_loop_no_idle_timeout_and_malformed_json() -> None:
    class _RecordingExecutor:
        commands = ("start",)

        def execute(self, command: str, params: dict | None) -> dict:
            return {"echo": command}

    ws = ControlFakeWS(incoming=[json.dumps({"command": "start"}), "not-json"])
    await _control_recv_loop(ws, _RecordingExecutor(), {"start"}, LeakyBucket(), asyncio.Event(), idle_timeout=0, client_ip="1.2.3.4")
    assert any(m["data"].get("command") == "start" and m["data"]["status"] == "success" for m in ws.sent)
    assert ws.closed == (1003, "Malformed JSON")


@pytest.mark.asyncio
async def test_recv_loop_rejects_oversized_message() -> None:
    """An over-limit frame is answered and then closes the connection (1009).

    **This assertion was inverted by the APD-SVCCORE-005 fix, and the previous form pinned the
    defect.** It formerly wrapped the call in ``pytest.raises(WebSocketDisconnect)`` -- i.e. it
    asserted the loop *kept running* past the oversize frame and only ended when the scripted input
    ran out. That ``continue`` is what let one connection repeat the allocation indefinitely, since
    the oversize path returns before ``_handle_command_message``, the only place a rate-limit token
    is spent. Third instance of this shape in one arc, after ``test_docs_reachable_and_exempt`` and
    ``test_worker_task_protocol_default_bodies_return_none``.
    """
    ws = ControlFakeWS(incoming=["x" * (65536 + 1)])
    await _control_recv_loop(ws, None, {"start"}, LeakyBucket(), asyncio.Event(), idle_timeout=0, client_ip="1.2.3.4")
    assert ws.sent[-1]["data"]["error"] == "Message too large"
    assert ws.closed == (1009, "Message too large")


@pytest.mark.asyncio
async def test_oversized_frame_cannot_be_repeated_on_one_connection() -> None:
    """**The decisive arm.** A second oversize frame is never read, because the first one closed.

    Asserting only the close code would pass against an implementation that closed *after*
    draining the rest of the queue. What the entry is about is repetition: the allocation itself is
    unavoidable (``receive_text()`` has already materialised the frame, and the real ceiling is
    uvicorn's ``ws_max_size``), so the only thing that changes an abusive client's cost is being
    unable to do it again on the same connection.
    """
    oversize = "x" * (65536 + 1)
    ws = ControlFakeWS(incoming=[oversize, oversize, oversize])

    await _control_recv_loop(ws, None, {"start"}, LeakyBucket(), asyncio.Event(), idle_timeout=0, client_ip="1.2.3.4")

    assert ws.closed == (1009, "Message too large")
    # Exactly one rejection was sent: frames two and three were never received.
    assert len([m for m in ws.sent if m.get("data", {}).get("error") == "Message too large"]) == 1


@pytest.mark.asyncio
async def test_a_pong_still_costs_no_rate_limit_token() -> None:
    """Deliberate non-change, pinned so it reads as a decision rather than an oversight.

    The bucket is the *command* budget (``ws_control_rate_limit_per_sec``). Charging keepalive would
    let a burst of legitimate commands exhaust it and rate-limit the client's pong, which the
    heartbeat loop then reads as a dead peer and closes with 1011 -- a self-inflicted disconnect on
    a healthy connection. An empty bucket must therefore still route a pong.
    """
    empty = LeakyBucket(capacity=1, refill_rate=0.0)
    assert empty.try_acquire() is True  # drain the single token
    assert empty.try_acquire() is False  # bucket is now empty and never refills

    pong = asyncio.Event()
    ws = ControlFakeWS(incoming=[json.dumps({"type": "pong"})])
    with pytest.raises(WebSocketDisconnect):
        await _control_recv_loop(ws, None, {"start"}, empty, pong, idle_timeout=0, client_ip="1.2.3.4")

    assert pong.is_set(), "keepalive must not be gated on the command budget"


@pytest.mark.asyncio
async def test_recv_loop_routes_pong() -> None:
    pong = asyncio.Event()
    pong.clear()
    ws = ControlFakeWS(incoming=[json.dumps({"type": "pong"})])
    with pytest.raises(WebSocketDisconnect):
        await _control_recv_loop(ws, None, {"start"}, LeakyBucket(), pong, idle_timeout=0, client_ip="1.2.3.4")
    assert pong.is_set()


# ----------------------------------------------------------------------------------------
# Handler-level early return
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_control_handler_returns_when_gate_fails() -> None:
    ws = ControlFakeWS(app=_app(settings=_settings(disable_ws_control_endpoint=True)))
    await control_stream_handler(ws)
    assert ws.closed == (1013, "Control endpoint disabled")
    assert ws.accepted is False


# ----------------------------------------------------------------------------------------
# Anti-resurrection: close code 1006 must never be sent by this package
# ----------------------------------------------------------------------------------------


def test_no_module_sends_reserved_close_code_1006() -> None:
    """No WebSocket handler may set 1006 as a Close-frame status.

    RFC 6455 Section 7.4.1: "1006 is a reserved value and MUST NOT be set as a status code in a
    Close control frame by an endpoint." It is designated for a *receiver* to report a closure
    that carried no Close frame at all. The ``websockets`` server used under uvicorn enforces
    this and raises on serialization, so a handler that asks for 1006 sends no close frame --
    the peer is left with a silent half-open socket and no reason string, which is exactly how
    the 2026-07-10 control-WS incident stayed invisible for hours.

    The two heartbeat sites are unit-tested above; this scans the whole package so a *new*
    handler cannot reintroduce the code somewhere without a test.
    """
    package = pathlib.Path(control_stream.__file__).parent
    offenders = []
    for path in sorted(package.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # Match ``...close(code=1006, ...)`` structurally rather than by text, so the prose
            # explaining *why* 1006 is banned does not trip the guard it documents.
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "close"):
                continue
            for kw in node.keywords:
                if kw.arg == "code" and isinstance(kw.value, ast.Constant) and kw.value.value == 1006:
                    offenders.append(f"{path.name}:{node.lineno}")
    assert offenders == [], "close code 1006 is forbidden by RFC 6455 Section 7.4.1 -- use 1011:\n" + "\n".join(offenders)
