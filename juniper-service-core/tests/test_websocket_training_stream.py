"""Edge-path coverage for the ``/ws/training`` handler internals (C-4a).

The both-stacks-green contract test drives the happy metrics-stream path through ``TestClient``.
This module unit-tests the resume-handshake arms, the initial-state / metrics-burst error
handling, the heartbeat ping loop, the pong / subscribe_metrics receive loop, the resume
success / malformed / out-of-range branches, and the handler's early-return guards directly with
fake sockets -- deterministic, no transport threading.
"""

from __future__ import annotations

import asyncio
import json
import types

import pytest
from fastapi import WebSocketDisconnect

from juniper_service_core.security import build_api_key_auth
from juniper_service_core.websocket.manager import ReplayOutOfRange
from juniper_service_core.websocket.training_stream import (
    _await_resume_frame,
    _handle_resume,
    _handle_subscribe_metrics,
    _heartbeat_ping_loop,
    _recv_pong_loop,
    _send_initial_state,
    _send_metrics_burst,
    training_stream_handler,
)

_HANG = object()


def _app(**state: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(state=types.SimpleNamespace(**state))


class TrainingFakeWS:
    """A training-channel fake socket: async accept / send_json / close / receive_text."""

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


class SendFailWS(TrainingFakeWS):
    async def send_json(self, message: dict) -> None:
        raise RuntimeError("socket gone")


class CloseFailAfterSendWS(TrainingFakeWS):
    async def close(self, code: int = 1000, reason: str = "") -> None:
        raise RuntimeError("close failed")


class RecordingWsManager:
    """Records personal messages + stubs the resume surface training_stream_handler needs."""

    def __init__(self, *, current_seq: int = 0, server_instance_id: str = "srv", replay: list | None = None, replay_error: Exception | None = None, connect_pending_result: bool = True) -> None:
        self.current_seq = current_seq
        self.server_instance_id = server_instance_id
        self.personal: list[dict] = []
        self._replay = replay or []
        self._replay_error = replay_error
        self._connect_pending_result = connect_pending_result
        self.event_loop_set = False
        self.promoted: list = []
        self.registered: list[str] = []
        self.unregistered: list = []
        self.disconnected = False

    async def send_personal_message(self, websocket: object, message: dict) -> bool:
        self.personal.append(message)
        return True

    def replay_since(self, last_seq: int) -> list:
        if self._replay_error is not None:
            raise self._replay_error
        return self._replay

    def set_event_loop(self, loop: object) -> None:
        self.event_loop_set = True

    async def connect_pending(self, websocket: object) -> bool:
        return self._connect_pending_result

    async def promote_to_active(self, websocket: object) -> None:
        self.promoted.append(websocket)

    def register_endpoint_connection(self, websocket: object, endpoint: str) -> None:
        self.registered.append(endpoint)

    def unregister_endpoint_connection(self, websocket: object) -> None:
        self.unregistered.append(websocket)

    async def disconnect(self, websocket: object) -> None:
        self.disconnected = True


class _StaticLifecycle:
    def __init__(self, metrics: list) -> None:
        self._metrics = metrics

    def get_metrics_history(self, count: int) -> list:
        return self._metrics[:count]


class _RaisingLifecycle:
    def get_metrics_history(self, count: int) -> list:
        raise RuntimeError("history unavailable")


class _NoneLifecycle:
    def get_metrics_history(self, count: int) -> None:
        return None


# ----------------------------------------------------------------------------------------
# Resume-handshake frame arms
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_await_resume_frame_timeout_is_fresh_connect() -> None:
    ws = TrainingFakeWS(incoming=[_HANG])
    assert await _await_resume_frame(ws, RecordingWsManager(), 0.01) == (False, False)


@pytest.mark.asyncio
async def test_await_resume_frame_non_json_is_fresh_connect() -> None:
    ws = TrainingFakeWS(incoming=["not-json"])
    assert await _await_resume_frame(ws, RecordingWsManager(), 1.0) == (False, False)


@pytest.mark.asyncio
async def test_await_resume_frame_disconnect_reports_disconnected() -> None:
    ws = TrainingFakeWS(incoming=[WebSocketDisconnect(code=1000)])
    assert await _await_resume_frame(ws, RecordingWsManager(), 1.0) == (False, True)


@pytest.mark.asyncio
async def test_await_resume_frame_generic_error_is_fresh_connect() -> None:
    ws = TrainingFakeWS(incoming=[RuntimeError("boom")])
    assert await _await_resume_frame(ws, RecordingWsManager(), 1.0) == (False, False)


# ----------------------------------------------------------------------------------------
# Initial-state / metrics burst
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_initial_state_noop_without_lifecycle() -> None:
    mgr = RecordingWsManager()
    await _send_initial_state(TrainingFakeWS(), mgr, None, 100)
    assert mgr.personal == []


@pytest.mark.asyncio
async def test_send_metrics_burst_swallows_history_error() -> None:
    mgr = RecordingWsManager(current_seq=3)
    await _send_metrics_burst(TrainingFakeWS(), mgr, _RaisingLifecycle(), 10)
    assert mgr.personal[-1]["type"] == "initial_metrics"
    assert mgr.personal[-1]["data"]["count"] == 0


@pytest.mark.asyncio
async def test_send_metrics_burst_handles_none_history() -> None:
    mgr = RecordingWsManager()
    await _send_metrics_burst(TrainingFakeWS(), mgr, _NoneLifecycle(), 5)
    assert mgr.personal[-1]["data"]["count"] == 0


# ----------------------------------------------------------------------------------------
# Heartbeat ping loop
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_heartbeat_ping_loop_closes_on_pong_timeout() -> None:
    ws = TrainingFakeWS()
    await _heartbeat_ping_loop(ws, 0.001, 0.001, asyncio.Event())
    code, reason = ws.closed
    # See the matching assertion in test_websocket_control_stream.py: RFC 6455 Section 7.4.1
    # forbids an endpoint from setting 1006 as a Close-frame status, and the ``websockets``
    # server raises rather than serialize it.
    assert code == 1011
    assert code != 1006
    assert reason.startswith("Heartbeat timeout")
    assert any(m.get("type") == "ping" for m in ws.sent)


@pytest.mark.asyncio
async def test_heartbeat_ping_loop_returns_on_send_failure() -> None:
    ws = SendFailWS()
    await _heartbeat_ping_loop(ws, 0.001, 5.0, asyncio.Event())
    assert ws.closed is None


@pytest.mark.asyncio
async def test_heartbeat_ping_loop_swallows_close_failure() -> None:
    ws = CloseFailAfterSendWS()
    await _heartbeat_ping_loop(ws, 0.001, 0.001, asyncio.Event())


# ----------------------------------------------------------------------------------------
# Receive loop + subscribe_metrics
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recv_pong_loop_handles_frame_types() -> None:
    ws = TrainingFakeWS(
        incoming=[
            "not-json",
            json.dumps({"type": "pong"}),
            json.dumps({"type": "subscribe_metrics", "data": {"max_count": 2}}),
            WebSocketDisconnect(code=1000),
        ]
    )
    mgr = RecordingWsManager(current_seq=1)
    lifecycle = _StaticLifecycle(metrics=[{"mse": 1.0}, {"mse": 0.5}, {"mse": 0.25}])
    pong = asyncio.Event()
    pong.clear()
    await _recv_pong_loop(ws, pong, ws_manager=mgr, lifecycle=lifecycle, subscribe_metrics_max_count=5)
    assert pong.is_set()
    assert any(m["type"] == "initial_metrics" for m in mgr.personal)


@pytest.mark.asyncio
async def test_handle_subscribe_metrics_invalid_count_uses_default() -> None:
    mgr = RecordingWsManager()
    lifecycle = _StaticLifecycle(metrics=[{"mse": 1.0}])
    await _handle_subscribe_metrics(TrainingFakeWS(), mgr, lifecycle, {"data": {"max_count": "abc"}}, 3)
    assert mgr.personal[-1]["type"] == "initial_metrics"


@pytest.mark.asyncio
async def test_handle_subscribe_metrics_missing_count_uses_default() -> None:
    mgr = RecordingWsManager()
    lifecycle = _StaticLifecycle(metrics=[{"mse": 1.0}])
    await _handle_subscribe_metrics(TrainingFakeWS(), mgr, lifecycle, {}, 2)
    assert mgr.personal[-1]["type"] == "initial_metrics"


# ----------------------------------------------------------------------------------------
# Resume dispatch branches
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_resume_malformed_frame() -> None:
    mgr = RecordingWsManager(server_instance_id="srv")
    assert await _handle_resume(TrainingFakeWS(), mgr, {"data": {}}) is False
    assert mgr.personal[-1]["data"]["reason"] == "malformed_resume"


@pytest.mark.asyncio
async def test_handle_resume_out_of_range() -> None:
    mgr = RecordingWsManager(server_instance_id="srv", replay_error=ReplayOutOfRange("too old"))
    result = await _handle_resume(TrainingFakeWS(), mgr, {"data": {"last_seq": 1, "server_instance_id": "srv"}})
    assert result is False
    assert mgr.personal[-1]["data"]["reason"] == "out_of_range"


@pytest.mark.asyncio
async def test_handle_resume_success_replays_events() -> None:
    events = [{"type": "metrics", "seq": 2}, {"type": "metrics", "seq": 3}]
    mgr = RecordingWsManager(server_instance_id="srv", replay=events)
    result = await _handle_resume(TrainingFakeWS(), mgr, {"data": {"last_seq": 1, "server_instance_id": "srv"}})
    assert result is True
    assert mgr.personal[0]["type"] == "resume_ok"
    assert mgr.personal[0]["data"]["replayed_count"] == 2
    assert mgr.personal[1:] == events


# ----------------------------------------------------------------------------------------
# Handler-level early-return guards
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_training_handler_returns_on_auth_failure() -> None:
    auth = build_api_key_auth(["k"])
    ws = TrainingFakeWS(headers={}, app=_app(api_key_auth=auth))
    await training_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4001


@pytest.mark.asyncio
async def test_training_handler_closes_without_ws_manager() -> None:
    ws = TrainingFakeWS(app=_app())
    await training_stream_handler(ws)
    assert ws.closed == (1011, "WebSocket manager not available")


@pytest.mark.asyncio
async def test_training_handler_returns_when_connect_pending_rejected() -> None:
    mgr = RecordingWsManager(connect_pending_result=False)
    ws = TrainingFakeWS(app=_app(ws_manager=mgr))
    await training_stream_handler(ws)
    assert mgr.promoted == []
    assert mgr.event_loop_set is True


@pytest.mark.asyncio
async def test_training_handler_returns_on_disconnect_during_handshake() -> None:
    mgr = RecordingWsManager(connect_pending_result=True)
    ws = TrainingFakeWS(app=_app(ws_manager=mgr, settings=types.SimpleNamespace(ws_resume_handshake_timeout_s=1.0, ws_initial_metrics_count=10)), incoming=[WebSocketDisconnect(code=1000)])
    await training_stream_handler(ws)
    assert mgr.promoted == []  # returned before promotion
    assert mgr.disconnected is True  # finally cleaned up
