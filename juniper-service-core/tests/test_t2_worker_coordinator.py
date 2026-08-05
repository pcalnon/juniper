"""Contract test for the WS-2 / OUT-11 T2 step-3b worker coordinator + ``/ws/workers`` stream.

Drives the generic :class:`WorkerCoordinator` and the worker stream handler with a *trivial* injected
:class:`WorkerTaskProtocol` -- the RK-6 guard: because the protocol carries no cascade schema
(candidate / correlation / numpy tensors), nothing model-specific can hide in the "generic" coordinator
or transport. cascor is untouched; its real ``WorkerProtocol`` adapter is WS-6. The cascade-bound
``Task`` / ``TaskResult`` envelope (WS-8) is out of scope here.

Coverage:

* ``WorkerCoordinator`` -- submit / dispatch (assignment built via the protocol) / submit-result
  (accept, reject-unknown, reject-duplicate, reject-on-parse-None) / collect (+ worker-liveness
  early-exit) / pending-count / task-timeout reassignment / stale-worker reassignment / anomaly hook /
  send-callback bookkeeping / cancel + shutdown.
* ``/ws/workers`` stream -- origin reject, uninitialised-pool reject, rate-limit reject, registration
  (server-assigned id + client_name), invalid-registration reject, registry-full reject, the full
  register -> dispatch -> result -> collect flow, heartbeat ack + enriched-field forwarding, and a
  binary-attachment result round-trip.
"""

from __future__ import annotations

import json
import time
from collections import deque
from types import SimpleNamespace

import pytest
from fastapi import WebSocketDisconnect

from juniper_service_core.websocket import attach_worker_pool, worker_stream_handler
from juniper_service_core.workers import ParsedResult, WorkerCoordinator, WorkerRegistry

# ======================================================================================
# Test doubles
# ======================================================================================


class _RecordingProtocol:
    """A trivial :class:`WorkerTaskProtocol` for the coordinator unit tests.

    Encodes the opaque payload into a JSON envelope + one synthetic binary frame, declares its result
    attachments from ``msg["attachments"]``, and parses a result with no cascade fields. ``msg["ok"]``
    set to ``False`` makes :meth:`parse_result` reject (the validation-failure arm).
    """

    def __init__(self) -> None:
        self.built: list[str] = []

    def build_assignment(self, task):
        self.built.append(task.task_id)
        return ({"type": "task_assign", "task_id": task.task_id, "payload": task.payload}, [b"frame-" + task.task_id.encode()])

    def result_attachments(self, msg):
        return list(msg.get("attachments", []))

    def parse_result(self, worker_id, msg, frames):
        if not msg.get("ok", True):
            return None
        return ParsedResult(
            success=msg.get("success", True),
            result={"task_id": msg.get("task_id"), "frames": dict(frames)},
            score=msg.get("score"),
            duration=msg.get("duration"),
        )


class _RecordingDetector:
    """Records :meth:`check_result` calls so the anomaly hook can be asserted."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def check_result(self, worker_id, score, training_duration, task_id):
        self.calls.append((worker_id, score, training_duration, task_id))
        return []


class _TrivialProtocol:
    """A trivial JSON-only :class:`WorkerTaskProtocol` for the stream tests (no binary frames)."""

    def build_assignment(self, task):
        return ({"type": "task_assign", "task_id": task.task_id, "round_id": task.round_id, "payload": task.payload}, [])

    def result_attachments(self, msg):
        return list(msg.get("attachments", []))

    def parse_result(self, worker_id, msg, frames):
        if "task_id" not in msg:
            return None
        return ParsedResult(success=msg.get("success", True), result={"task_id": msg["task_id"], "frames": dict(frames)}, score=msg.get("score"))


class _SpyRegistry(WorkerRegistry):
    """A registry that records the kwargs of each :meth:`heartbeat` (to assert enriched forwarding)."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.heartbeats: list[dict] = []

    def heartbeat(self, worker_id, **kwargs):
        self.heartbeats.append(kwargs)
        return super().heartbeat(worker_id, **kwargs)


def _text(payload: dict) -> tuple[str, str]:
    return ("text", json.dumps(payload))


def _binary(data: bytes) -> tuple[str, bytes]:
    return ("bytes", data)


class FakeWorkerWebSocket:
    """A scripted async WebSocket stand-in for the ``/ws/workers`` handler.

    ``inbound`` is an ordered list of ``_text(...)`` / ``_binary(...)`` frames the worker "sends". The
    registration uses :meth:`receive_text`; the message loop uses :meth:`receive`. When the script is
    exhausted, both raise :class:`WebSocketDisconnect` so the handler's loop ends cleanly.
    """

    def __init__(self, *, inbound=None, headers=None, client=("10.0.0.9", 5000), app=None):
        self._inbound = deque(inbound or [])
        self.headers = headers or {}
        self.client = client
        self.app = app
        self.sent: list[dict] = []
        self.sent_bytes: list[bytes] = []
        self.accepted = False
        self.closed: tuple[int, str] | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def send_bytes(self, data: bytes) -> None:
        self.sent_bytes.append(data)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._inbound:
            raise WebSocketDisconnect(1000)
        _kind, payload = self._inbound.popleft()
        return payload

    async def receive(self) -> dict:
        if not self._inbound:
            raise WebSocketDisconnect(1000)
        kind, payload = self._inbound.popleft()
        return {"text": payload} if kind == "text" else {"bytes": payload}


_REGISTER = {"type": "register", "worker_id": "node-a", "capabilities": {"gpu": True}}


def _wire_app(registry, coordinator, **extra):
    """Build a SimpleNamespace 'app' wired via ``attach_worker_pool`` (also exercises that helper)."""
    app = SimpleNamespace(state=SimpleNamespace())
    attach_worker_pool(app, registry=registry, coordinator=coordinator, **extra)
    return app


# ======================================================================================
# WorkerCoordinator -- synchronous surface
# ======================================================================================


def test_submit_tasks_creates_pending_and_ids() -> None:
    coord = WorkerCoordinator(WorkerRegistry(), _RecordingProtocol())
    ids = coord.submit_tasks("round-1", [{"c": 0}, {"c": 1}, {"c": 2}])
    assert len(ids) == 3
    assert len(set(ids)) == 3  # unique
    assert coord.pending_tasks_count() == 3
    assert coord.has_pending_tasks() is True


def test_get_next_assignment_builds_via_protocol_and_marks_busy() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    proto = _RecordingProtocol()
    coord = WorkerCoordinator(reg, proto)
    (tid,) = coord.submit_tasks("r", [{"c": 0}])

    msg, frames = coord.get_next_assignment("w1")
    assert msg["task_id"] == tid
    assert frames == [b"frame-" + tid.encode()]  # the protocol's binary frame round-trips
    assert proto.built == [tid]
    assert reg.get("w1").idle is False  # worker is now busy
    assert coord.has_pending_tasks() is False  # the only task was popped


def test_get_next_assignment_none_when_empty_or_unknown_worker() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _RecordingProtocol())
    assert coord.get_next_assignment("w1") is None  # no tasks
    coord.submit_tasks("r", [{"c": 0}])
    assert coord.get_next_assignment("ghost") is None  # unknown worker -> no pop
    assert coord.has_pending_tasks() is True  # task not consumed by the ghost


def test_submit_result_accepts_and_collects() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _RecordingProtocol())
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")  # dispatch

    assert coord.submit_result("w1", {"task_id": tid, "success": True, "score": 0.5}, {}) is True
    results = coord.collect_results(timeout=0.5)
    assert len(results) == 1
    assert results[0]["task_id"] == tid
    assert reg.get("w1").tasks_completed == 1  # success recorded
    assert reg.get("w1").idle is True  # task complete -> idle again


def test_submit_result_rejects_unknown_and_duplicate() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _RecordingProtocol())
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")

    assert coord.submit_result("w1", {"task_id": "no-such-task"}, {}) is False  # unknown
    assert coord.submit_result("w1", {"task_id": tid, "success": True}, {}) is True
    assert coord.submit_result("w1", {"task_id": tid, "success": True}, {}) is False  # duplicate


def test_submit_result_rejects_on_parse_none_and_marks_failed() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _RecordingProtocol())
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")

    # ok=False makes the protocol reject; the coordinator records a failed task and returns False.
    assert coord.submit_result("w1", {"task_id": tid, "ok": False}, {}) is False
    assert reg.get("w1").tasks_failed == 1
    assert coord.collect_results(timeout=0.1) == []  # nothing accepted


def test_anomaly_detector_receives_generic_score() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    detector = _RecordingDetector()
    coord = WorkerCoordinator(reg, _RecordingProtocol(), anomaly_detector=detector)
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")
    coord.submit_result("w1", {"task_id": tid, "success": True, "score": 0.95, "duration": 2.0}, {})

    assert detector.calls == [("w1", 0.95, 2.0, tid)]  # generic score + duration, not 'correlation'


def test_anomaly_detector_skipped_when_score_is_none() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    detector = _RecordingDetector()
    coord = WorkerCoordinator(reg, _RecordingProtocol(), anomaly_detector=detector)
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")
    coord.submit_result("w1", {"task_id": tid, "success": True}, {})  # no score
    assert detector.calls == []  # no score -> no anomaly check


def test_collect_results_early_exit_without_workers() -> None:
    coord = WorkerCoordinator(WorkerRegistry(), _RecordingProtocol())
    coord.submit_tasks("r", [{"c": 0}, {"c": 1}])  # 2 tasks, but zero registered workers
    start = time.monotonic()
    results = coord.collect_results(timeout=30.0)
    elapsed = time.monotonic() - start
    assert results == []
    assert elapsed < 5.0  # worker-liveness early-exit fired, did NOT block the full 30s budget


def test_pending_count_and_cancel_round() -> None:
    coord = WorkerCoordinator(WorkerRegistry(), _RecordingProtocol())
    coord.submit_tasks("r", [{"c": 0}, {"c": 1}, {"c": 2}])
    assert coord.pending_tasks_count() == 3
    coord.cancel_round()
    assert coord.pending_tasks_count() == 0
    assert coord.has_pending_tasks() is False


def test_task_timeout_reassigns() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _RecordingProtocol(), task_reassignment_timeout=1.0)
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")  # dispatch -> w1 busy
    assert coord.has_pending_tasks() is False

    # Backdate the dispatch so the task is over its reassignment budget, then run the timeout sweep.
    coord._pending_tasks[tid].dispatched_at = time.time() - 10.0
    coord._check_task_timeouts()

    assert coord.has_pending_tasks() is True  # task requeued
    assert reg.get("w1").tasks_failed == 1  # the timed-out worker took a failure
    assert reg.get("w1").idle is True  # active task cleared


def test_stale_worker_reassigns_active_task() -> None:
    reg = WorkerRegistry(heartbeat_timeout=30.0)
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _RecordingProtocol())
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")  # w1 holds the task

    # Make w1 stale, then run the stale sweep: w1 is deregistered and its task is requeued.
    reg.get("w1").last_heartbeat = time.time() - 1000.0
    coord._check_stale_workers()

    assert reg.get("w1") is None  # deregistered
    assert coord.has_pending_tasks() is True  # task back in the unassigned queue


def test_send_callback_register_unregister() -> None:
    coord = WorkerCoordinator(WorkerRegistry(), _RecordingProtocol())

    async def _cb(msg, frames=None):
        return True

    coord.register_send_callback("w1", _cb)
    assert coord._send_callbacks["w1"] is _cb
    coord.unregister_send_callback("w1")
    assert "w1" not in coord._send_callbacks


def test_shutdown_clears_round_and_callbacks() -> None:
    coord = WorkerCoordinator(WorkerRegistry(), _RecordingProtocol())
    coord.submit_tasks("r", [{"c": 0}])

    async def _cb(msg, frames=None):
        return True

    coord.register_send_callback("w1", _cb)
    coord.shutdown()
    assert coord.pending_tasks_count() == 0
    assert coord._send_callbacks == {}


# ======================================================================================
# /ws/workers stream -- rejection paths
# ======================================================================================


@pytest.mark.asyncio
async def test_origin_header_rejected() -> None:
    ws = FakeWorkerWebSocket(headers={"origin": "http://evil.example"})
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4003
    assert ws.accepted is False


@pytest.mark.asyncio
async def test_uninitialised_pool_rejected() -> None:
    app = SimpleNamespace(state=SimpleNamespace())  # no worker_coordinator / worker_registry
    ws = FakeWorkerWebSocket(app=app)
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4004


@pytest.mark.asyncio
async def test_rate_limited_rejected() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord, rate_limiter=SimpleNamespace(allow=lambda ip: False))
    ws = FakeWorkerWebSocket(app=app)
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4029


@pytest.mark.asyncio
async def test_invalid_registration_rejected() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    # Missing 'capabilities' -> validation failure -> close 4008.
    ws = FakeWorkerWebSocket(app=app, inbound=[_text({"type": "register", "worker_id": "node-a"})])
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4008


@pytest.mark.asyncio
async def test_first_message_must_be_registration() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(app=app, inbound=[_text({"type": "heartbeat", "worker_id": "x"})])
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4007


@pytest.mark.asyncio
async def test_registry_full_rejected() -> None:
    reg = WorkerRegistry(max_workers=1)
    reg.register("pre-existing", {})  # registry now at capacity
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4013


# ======================================================================================
# /ws/workers stream -- registration + full dispatch/result/collect flow
# ======================================================================================


@pytest.mark.asyncio
async def test_registration_assigns_server_id_and_acks() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)

    types_sent = [m["type"] for m in ws.sent]
    assert types_sent[0] == "connection_established"
    ack = next(m for m in ws.sent if m["type"] == "registration_ack")
    assert ack["worker_id"].startswith("worker-")  # server-assigned, NOT the client's "node-a"
    assert ack["worker_id"] != "node-a"
    assert ack["data"]["client_name"] == "node-a"  # client value captured as display name only


@pytest.mark.asyncio
async def test_register_dispatch_result_collect_flow() -> None:
    reg = WorkerRegistry()
    proto = _TrivialProtocol()
    coord = WorkerCoordinator(reg, proto)
    # Pre-submit a task so the connect-time dispatch has work; we know its id for the scripted result.
    (tid,) = coord.submit_tasks("round-1", [{"candidate": 0}])
    app = _wire_app(reg, coord)

    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "task_result", "task_id": tid, "success": True, "score": 0.7}),
        ],
    )
    await worker_stream_handler(ws)

    # Dispatched on connect: a task_assign for tid was sent.
    assign = next(m for m in ws.sent if m.get("type") == "task_assign")
    assert assign["task_id"] == tid
    # Result accepted + acked.
    result_ack = next(m for m in ws.sent if m.get("type") == "result_ack")
    assert result_ack["task_id"] == tid and result_ack["status"] == "accepted"
    # The coordinator collected exactly the submitted result.
    results = coord.collect_results(timeout=0.5)
    assert len(results) == 1 and results[0]["task_id"] == tid


@pytest.mark.asyncio
async def test_heartbeat_ack_and_enriched_field_forwarding() -> None:
    reg = _SpyRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "heartbeat", "worker_id": "ignored", "gpu_utilization_pct": 55.0, "rss_mb": 1024.0}),
        ],
    )
    await worker_stream_handler(ws)

    # A heartbeat ack was sent.
    assert any(m.get("type") == "heartbeat" for m in ws.sent)
    # The enriched fields were forwarded verbatim to the registry.
    assert reg.heartbeats[-1]["gpu_utilization_pct"] == 55.0
    assert reg.heartbeats[-1]["rss_mb"] == 1024.0


@pytest.mark.asyncio
async def test_unknown_message_type_errors_but_keeps_connection() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER), _text({"type": "frobnicate"})])
    await worker_stream_handler(ws)
    err = next(m for m in ws.sent if m.get("type") == "error")
    assert "Unknown message type" in err["error"]


@pytest.mark.asyncio
async def test_binary_attachment_result_round_trip() -> None:
    """A result that declares one attachment: the stream reads the binary frame and parse_result sees it."""

    class _BinaryProtocol:
        def build_assignment(self, task):
            return ({"type": "task_assign", "task_id": task.task_id}, [])

        def result_attachments(self, msg):
            return ["blob"]

        def parse_result(self, worker_id, msg, frames):
            return ParsedResult(success=True, result={"task_id": msg["task_id"], "blob": frames.get("blob")})

    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _BinaryProtocol())
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    app = _wire_app(reg, coord)

    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "task_result", "task_id": tid}),  # declares attachment "blob"
            _binary(b"tensor-bytes"),  # the one attachment frame
        ],
    )
    await worker_stream_handler(ws)

    result_ack = next(m for m in ws.sent if m.get("type") == "result_ack")
    assert result_ack["status"] == "accepted"
    results = coord.collect_results(timeout=0.5)
    assert results[0]["blob"] == b"tensor-bytes"  # the binary frame reached parse_result


# ======================================================================================
# /ws/workers stream -- error / edge paths (transport robustness)
# ======================================================================================


@pytest.mark.asyncio
async def test_oversized_registration_rejected() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    big = {"type": "register", "worker_id": "node-a", "capabilities": {"blob": "x" * 70000}}  # > 64KB JSON
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(big)])
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4005


@pytest.mark.asyncio
async def test_invalid_json_registration_rejected() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(app=app, inbound=[("text", "{not valid json")])
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4006


@pytest.mark.asyncio
async def test_message_loop_oversized_and_invalid_json_keep_connection() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            ("text", json.dumps({"type": "heartbeat", "pad": "x" * 70000})),  # oversized loop frame
            ("text", "{bad json"),  # invalid JSON loop frame
        ],
    )
    await worker_stream_handler(ws)
    errors = [m for m in ws.sent if m.get("type") == "error"]
    assert any("too large" in m["error"].lower() for m in errors)
    assert any("invalid json" in m["error"].lower() for m in errors)


@pytest.mark.asyncio
async def test_task_result_expecting_binary_gets_text_is_rejected() -> None:
    """A result declaring an attachment but followed by a text frame -> error, no submit."""

    class _NeedsBlob:
        def build_assignment(self, task):
            return ({"type": "task_assign", "task_id": task.task_id}, [])

        def result_attachments(self, msg):
            return ["blob"]

        def parse_result(self, worker_id, msg, frames):  # pragma: no cover - never reached
            return ParsedResult(success=True, result=msg)

    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _NeedsBlob())
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "task_result", "task_id": tid}),  # declares "blob" attachment...
            _text({"type": "heartbeat"}),  # ...but the next frame is text, not the binary blob
        ],
    )
    await worker_stream_handler(ws)
    assert any("Expected binary frame" in m.get("error", "") for m in ws.sent)
    assert coord.collect_results(timeout=0.1) == []  # nothing accepted


@pytest.mark.asyncio
async def test_stray_binary_frame_is_ignored() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    # A bare binary frame outside a result sequence is logged + ignored (no crash, no error frame).
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER), _binary(b"stray")])
    await worker_stream_handler(ws)
    assert any(m.get("type") == "registration_ack" for m in ws.sent)


@pytest.mark.asyncio
async def test_dispatch_sends_binary_frames() -> None:
    """A protocol whose build_assignment returns frames -> the stream sends them after the envelope."""

    class _FrameProtocol:
        def build_assignment(self, task):
            return ({"type": "task_assign", "task_id": task.task_id}, [b"f1", b"f2"])

        def result_attachments(self, msg):
            return []

        def parse_result(self, worker_id, msg, frames):  # pragma: no cover - not exercised here
            return ParsedResult(success=True, result=msg)

    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _FrameProtocol())
    coord.submit_tasks("r", [{"c": 0}])
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)
    assert ws.sent_bytes == [b"f1", b"f2"]  # both binary frames dispatched after the task_assign


@pytest.mark.asyncio
async def test_heartbeat_redispatches_to_idle_worker() -> None:
    """After a worker frees up, a heartbeat re-triggers dispatch of newly-available work."""
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    # Two tasks: task1 is grabbed at connect; task2 waits. The result frees the worker, the
    # post-result dispatch grabs task2... so to isolate the heartbeat path, submit only one task and
    # assert the idle-guard branch runs (a heartbeat on an idle, work-free worker is a safe no-op).
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "task_result", "task_id": tid, "success": True}),  # frees the worker
            _text({"type": "heartbeat"}),  # worker now idle -> heartbeat dispatch branch runs
        ],
    )
    await worker_stream_handler(ws)
    assert any(m.get("type") == "heartbeat" for m in ws.sent)  # heartbeat ack returned


@pytest.mark.asyncio
async def test_rate_limiter_allows_then_registers() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    # allow=True path (the reject path is covered by test_rate_limited_rejected).
    app = _wire_app(reg, coord, rate_limiter=SimpleNamespace(allow=lambda ip: True))
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)
    assert any(m.get("type") == "registration_ack" for m in ws.sent)


@pytest.mark.asyncio
async def test_attach_worker_pool_wires_all_optionals_and_audit_metrics_fire() -> None:
    from juniper_service_core.workers import AuditLogger, WorkerMetrics

    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    audit = AuditLogger()
    metrics = WorkerMetrics()
    app = SimpleNamespace(state=SimpleNamespace())
    attach_worker_pool(
        app,
        registry=reg,
        coordinator=coord,
        rate_limiter=SimpleNamespace(allow=lambda ip: True),
        audit_logger=audit,
        worker_metrics=metrics,
        ws_manager=None,
    )
    # All optionals wired onto app.state.
    assert app.state.worker_coordinator is coord
    assert app.state.worker_registry is reg
    assert app.state.worker_task_protocol is coord.protocol
    assert app.state.audit_logger is audit
    assert app.state.worker_metrics is metrics

    # Drive a registration so the audit + metrics on_register hooks fire, then disconnect (deregister).
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)
    assert audit.get_counts().get("worker_register") == 1
    assert audit.get_counts().get("worker_deregister") == 1
    assert len(metrics.get_all_metrics()) == 1  # the worker was registered with the metrics tracker


@pytest.mark.asyncio
async def test_send_callback_pushes_and_reports_failure() -> None:
    from juniper_service_core.websocket import worker_stream as ws_mod

    ok = FakeWorkerWebSocket()
    cb = ws_mod._make_send_callback(ok)
    assert await cb({"type": "ping"}, [b"frame"]) is True
    assert ok.sent == [{"type": "ping"}]
    assert ok.sent_bytes == [b"frame"]

    class _BrokenSocket(FakeWorkerWebSocket):
        async def send_json(self, message):
            raise RuntimeError("socket closed")

    broken = _BrokenSocket()
    cb_broken = ws_mod._make_send_callback(broken)
    assert await cb_broken({"type": "ping"}) is False  # exceptions are swallowed -> False


@pytest.mark.asyncio
async def test_build_worker_router_mounts_handler_and_custom_path() -> None:
    from juniper_service_core.websocket import build_worker_router

    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)

    router = build_worker_router()
    routes = [r for r in router.routes if getattr(r, "path", None) == "/ws/workers"]
    assert routes, "expected a /ws/workers route"
    # Invoke the mounted endpoint (covers the inner delegate -> worker_stream_handler).
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER)])
    await routes[0].endpoint(ws)
    assert any(m.get("type") == "registration_ack" for m in ws.sent)

    custom = build_worker_router(path="/ws/v1/workers")
    assert any(getattr(r, "path", None) == "/ws/v1/workers" for r in custom.routes)
