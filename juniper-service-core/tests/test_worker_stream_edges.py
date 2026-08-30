"""High-signal edge coverage for ``/ws/workers`` transport (auth fail-closed + registration shape + busy heartbeat + disconnect/abort reclaim).

Companion to ``test_t2_worker_coordinator.py``. That suite covers origin/rate-limit/uninitialised
rejects, missing-``capabilities`` → 4008, and the *idle* heartbeat redispatch arm. This file pins the
remaining blast-radius edges that were still untested on main:

* ``worker_stream_handler`` must fail closed on auth (close 4001, never ``accept``) — the training
  stream has an equivalent handler-level pin; the worker channel did not.
* ``worker_stream_module.validate_worker_registration`` shape edges (non-string / pattern-invalid ``worker_id``, non-dict
  ``capabilities``, missing ``worker_id``) — only the missing-``capabilities`` handler arm was covered.
* Heartbeat while the worker is still busy must NOT call dispatch (the idle guard at
  ``reg.idle``) — otherwise a mid-task heartbeat double-assigns and corrupts ``active_task_id``.
* Clean disconnect of a busy worker must requeue its sole in-flight task (the stale-heartbeat
  sweep already did; the stream ``finally`` did not).
* Mid-result transport abort (expected-binary-got-text / oversize) must free the worker so the
  post-result ``_try_dispatch_task`` redispatches — distinguishable from finally-only reclaim
  by a second ``task_assign`` before the socket closes.

Self-contained doubles (no imports from the contested coordinator test module) so concurrent coverage
PRs that edit ``test_t2_worker_coordinator.py`` cannot collide.
"""

from __future__ import annotations

import json
from collections import deque
from types import SimpleNamespace

import pytest
from fastapi import WebSocketDisconnect

from juniper_service_core.security import build_api_key_auth
from juniper_service_core.websocket import attach_worker_pool, worker_stream_handler
from juniper_service_core.websocket import worker_stream as worker_stream_module
from juniper_service_core.workers import ParsedResult, WorkerCoordinator, WorkerRegistry


class _TrivialProtocol:
    """JSON-only protocol for stream edges (no binary frames)."""

    def build_assignment(self, task):
        return ({"type": "task_assign", "task_id": task.task_id, "round_id": task.round_id, "payload": task.payload}, [])

    def result_attachments(self, msg):
        return list(msg.get("attachments", []))

    def parse_result(self, worker_id, msg, frames):
        if "task_id" not in msg:
            return None
        return ParsedResult(success=msg.get("success", True), result={"task_id": msg["task_id"]}, score=msg.get("score"))


def _text(payload: dict) -> tuple[str, str]:
    return ("text", json.dumps(payload))


class FakeWorkerWebSocket:
    """Scripted async WebSocket stand-in matching the coordinator suite contract."""

    def __init__(self, *, inbound=None, headers=None, client=("10.0.0.9", 5000), app=None):
        self._inbound = deque(inbound or [])
        self.headers = headers or {}
        self.client = client
        self.app = app
        self.sent: list[dict] = []
        self.accepted = False
        self.closed: tuple[int, str] | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def send_bytes(self, data: bytes) -> None:
        pass

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
    app = SimpleNamespace(state=SimpleNamespace())
    attach_worker_pool(app, registry=registry, coordinator=coordinator, **extra)
    return app


# ======================================================================================
# worker_stream_module.validate_worker_registration — pure shape edges
# ======================================================================================


def test_validate_registration_missing_worker_id() -> None:
    errors = worker_stream_module.validate_worker_registration({"type": "register", "capabilities": {}})
    assert any("Missing required field: worker_id" in e for e in errors)


def test_validate_registration_worker_id_must_be_string() -> None:
    errors = worker_stream_module.validate_worker_registration({"worker_id": 123, "capabilities": {}})
    assert any("worker_id must be a string" in e for e in errors)


@pytest.mark.parametrize(
    "bad_id",
    [
        "",  # empty
        "-leading-hyphen",  # must start alphanumeric
        "bad id with spaces",
        "x" * 65,  # > 64 chars
        "has.dot",
    ],
)
def test_validate_registration_worker_id_pattern_rejected(bad_id: str) -> None:
    errors = worker_stream_module.validate_worker_registration({"worker_id": bad_id, "capabilities": {}})
    assert any("worker_id must be 1-64 characters" in e for e in errors)


def test_validate_registration_capabilities_must_be_dict() -> None:
    errors = worker_stream_module.validate_worker_registration({"worker_id": "node-a", "capabilities": ["gpu"]})
    assert any("capabilities must be a dict" in e for e in errors)


def test_validate_registration_happy_path_empty_errors() -> None:
    assert worker_stream_module.validate_worker_registration({"worker_id": "node_1", "capabilities": {"gpu": True}}) == []


# ======================================================================================
# Handler: auth fail-closed (never accept) + registration shape → 4008
# ======================================================================================


@pytest.mark.asyncio
async def test_worker_handler_auth_failure_never_accepts() -> None:
    """Enabled API-key auth with a bad/missing key must close 4001 and never accept the socket."""
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    app.state.api_key_auth = build_api_key_auth(["s3cret"])

    ws = FakeWorkerWebSocket(app=app, headers={"X-API-Key": "nope"}, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)

    assert ws.accepted is False
    assert ws.closed is not None and ws.closed[0] == 4001
    assert not any(m.get("type") == "connection_established" for m in ws.sent)


@pytest.mark.asyncio
async def test_worker_handler_auth_missing_key_never_accepts() -> None:
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    app.state.api_key_auth = build_api_key_auth(["s3cret"])

    ws = FakeWorkerWebSocket(app=app, headers={}, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)

    assert ws.accepted is False
    assert ws.closed is not None and ws.closed[0] == 4001


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_register",
    [
        {"type": "register", "worker_id": 99, "capabilities": {}},  # non-string id
        {"type": "register", "worker_id": "-bad", "capabilities": {}},  # pattern
        {"type": "register", "worker_id": "ok", "capabilities": "gpu"},  # non-dict caps
        {"type": "register", "capabilities": {}},  # missing worker_id
    ],
)
async def test_invalid_registration_shape_closes_4008(bad_register: dict) -> None:
    """Shape failures beyond missing-capabilities must still close 4008 (never register)."""
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(app=app, inbound=[_text(bad_register)])
    await worker_stream_handler(ws)

    assert ws.accepted is True  # auth/accept happen before registration validation
    assert ws.closed is not None and ws.closed[0] == 4008
    assert reg.worker_count == 0
    assert not any(m.get("type") == "registration_ack" for m in ws.sent)


# ======================================================================================
# Heartbeat idle guard — busy worker must not double-dispatch
# ======================================================================================


@pytest.mark.asyncio
async def test_heartbeat_while_busy_does_not_redispatch() -> None:
    """A mid-task heartbeat must ack but must not dispatch the next pending task."""
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    (tid1, tid2) = coord.submit_tasks("round-1", [{"c": 0}, {"c": 1}])
    app = _wire_app(reg, coord)

    # Connect grabs tid1; heartbeat arrives while still busy (no result yet); disconnect.
    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "heartbeat"}),
        ],
    )
    await worker_stream_handler(ws)

    assigns = [m for m in ws.sent if m.get("type") == "task_assign"]
    assert len(assigns) == 1, f"busy heartbeat must not double-dispatch; got {assigns!r}"
    assert assigns[0]["task_id"] == tid1
    assert tid2 != tid1
    # Heartbeat ack still fires (the guard skips dispatch, not the ack).
    assert any(m.get("type") == "heartbeat" for m in ws.sent)
    # tid2 was never assigned on the wire, so it stays pending regardless of whether disconnect
    # reclaims tid1. That reclaim is pinned separately in test_disconnect_requeues_sole_in_flight_task.
    assert coord.has_pending_tasks() is True
    assert coord.pending_tasks_count() >= 1


# ======================================================================================
# Disconnect / mid-result abort must reclaim in-flight work (not wait the 120s timeout)
# ======================================================================================


def _binary(payload: bytes) -> tuple[str, bytes]:
    return ("bytes", payload)


class _NeedsBlob:
    """Protocol that declares a binary attachment so abort paths are reachable."""

    def build_assignment(self, task):
        return ({"type": "task_assign", "task_id": task.task_id, "round_id": task.round_id, "payload": task.payload}, [])

    def result_attachments(self, msg):
        return ["blob"]

    def parse_result(self, worker_id, msg, frames):  # pragma: no cover - abort must not parse
        raise AssertionError("parse_result must not run after a transport abort")


@pytest.mark.asyncio
async def test_disconnect_requeues_sole_in_flight_task() -> None:
    """Clean disconnect of a busy worker must requeue its *only* assigned task.

    The stale-heartbeat sweep already reclaims; the stream ``finally`` used to deregister
    only. With a single in-flight task there is no leftover unassigned sibling to hide the
    gap (unlike the busy-heartbeat fixture), so ``has_pending_tasks()`` going False is the
    production failure: the round waits the full ``task_reassignment_timeout``.
    """
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _TrivialProtocol())
    (tid,) = coord.submit_tasks("round-1", [{"c": 0}])
    app = _wire_app(reg, coord)

    ws = FakeWorkerWebSocket(app=app, inbound=[_text(_REGISTER)])
    await worker_stream_handler(ws)

    assigns = [m for m in ws.sent if m.get("type") == "task_assign"]
    assert len(assigns) == 1
    assert assigns[0]["task_id"] == tid
    assert reg.worker_count == 0  # finally deregistered
    assert coord.has_pending_tasks() is True
    task = coord._pending_tasks[tid]
    assert task.assigned_worker_id is None
    assert task.completed is False


@pytest.mark.asyncio
async def test_expected_binary_got_text_requeues_and_frees_worker() -> None:
    """A result that promises a blob but sends text must free the worker *before* disconnect.

    Distinguishes abort-path reclaim from finally-only reclaim: after the error frame the
    handler still calls ``_try_dispatch_task``, so a freed+requeued worker receives a second
    ``task_assign`` for the same id while the socket is still open.
    """
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _NeedsBlob())
    (tid,) = coord.submit_tasks("round-1", [{"c": 0}])
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "task_result", "task_id": tid}),
            _text({"type": "heartbeat"}),  # text where the blob was required
        ],
    )
    await worker_stream_handler(ws)

    assert any("Expected binary frame" in m.get("error", "") for m in ws.sent)
    assert not any(m.get("type") == "result_ack" for m in ws.sent)
    assigns = [m for m in ws.sent if m.get("type") == "task_assign"]
    assert [m["task_id"] for m in assigns] == [tid, tid], f"abort must free+requeue so the post-result dispatch re-sends the same task; got {assigns!r}"
    assert coord.has_pending_tasks() is True
    assert coord._pending_tasks[tid].assigned_worker_id is None


@pytest.mark.asyncio
async def test_oversize_binary_frame_requeues_and_frees_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    """Oversize attachment abort must free the worker so post-result dispatch can requeue."""
    import juniper_service_core.websocket.worker_stream as worker_stream_mod

    monkeypatch.setattr(worker_stream_mod, "_MAX_BINARY_SIZE", 16)
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, _NeedsBlob())
    (tid,) = coord.submit_tasks("round-1", [{"c": 0}])
    app = _wire_app(reg, coord)
    ws = FakeWorkerWebSocket(
        app=app,
        inbound=[
            _text(_REGISTER),
            _text({"type": "task_result", "task_id": tid}),
            _binary(b"x" * 17),
        ],
    )
    await worker_stream_handler(ws)

    assert any(m.get("error") == "Binary frame too large" for m in ws.sent)
    assert not any(m.get("type") == "result_ack" for m in ws.sent)
    assigns = [m for m in ws.sent if m.get("type") == "task_assign"]
    assert [m["task_id"] for m in assigns] == [tid, tid], f"oversize abort must redispatch; got {assigns!r}"
    assert coord.has_pending_tasks() is True
    assert coord._pending_tasks[tid].assigned_worker_id is None


# Attachment-list bounds — APD-SVCCORE-001
#
# The per-frame cap bounds each item, never the sum, and ``frames`` retains every accepted
# item in memory until the submission completes. Two independent bounds are added: a
# cardinality cap checked BEFORE the first receive, and a cumulative byte budget.
# ======================================================================================


def _dispatched(protocol=None):
    """A registry+coordinator with one task already dispatched to ``node-a`` (so a result is valid)."""
    reg = WorkerRegistry()
    reg.register("node-a", {})
    coord = WorkerCoordinator(reg, protocol or _TrivialProtocol())
    (tid,) = coord.submit_tasks("round-1", [{"c": 0}])
    coord.get_next_assignment("node-a")
    return reg, coord, tid


@pytest.mark.asyncio
async def test_over_long_attachment_list_is_rejected_before_any_frame_is_read() -> None:
    """A declaration of more than ``_MAX_ATTACHMENTS`` is refused without consuming a single frame.

    **The decisive assertion is the un-consumed queue, not the error frame.** A cardinality check
    placed *inside* the receive loop would also produce an error and also reject the submission --
    and would still let a hostile worker hold the handler through 32 frames first. Pinning that the
    inbound queue is untouched is what distinguishes the two implementations.

    Uses the real ``_MAX_ATTACHMENTS`` rather than a monkeypatched one, so this arm pins the shipped
    value and not just the mechanism.
    """
    _reg, coord, tid = _dispatched()
    too_many = [f"t{i}" for i in range(worker_stream_module._MAX_ATTACHMENTS + 1)]
    # Frames that WOULD satisfy the declaration, so consuming them is possible if the guard is late.
    ws = FakeWorkerWebSocket(inbound=[("bytes", b"x") for _ in too_many])
    inbound_before = len(ws._inbound)

    await worker_stream_module._handle_task_result(ws, "node-a", {"task_id": tid, "attachments": too_many}, coord)

    assert len(ws._inbound) == inbound_before, "guard must fire before the first receive()"
    assert ws.sent and ws.sent[-1]["error"] == "Too many binary attachments"
    assert coord.collect_results(timeout=0.1) == [], "an over-long declaration must not submit"


@pytest.mark.asyncio
async def test_cumulative_attachment_budget_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Frames that each pass the per-frame cap are still refused once their SUM exceeds the budget.

    This is the defect itself: ``len(attachment_names) x _MAX_BINARY_SIZE`` was reachable because a
    bound on each item is not a bound on the sum. The budget is monkeypatched down so the arm costs
    bytes rather than hundreds of megabytes -- the shipped magnitudes are pinned separately below.
    """
    monkeypatch.setattr(worker_stream_module, "_MAX_TOTAL_BINARY_SIZE", 10)
    _reg, coord, tid = _dispatched()
    # Each frame is 6 bytes: individually fine, cumulatively 12 > 10.
    ws = FakeWorkerWebSocket(inbound=[("bytes", b"aaaaaa"), ("bytes", b"bbbbbb")])

    await worker_stream_module._handle_task_result(ws, "node-a", {"task_id": tid, "attachments": ["a", "b"]}, coord)

    assert ws.sent and ws.sent[-1]["error"] == "Binary attachments exceed total size limit"
    assert coord.collect_results(timeout=0.1) == [], "an over-budget submission must not reach the coordinator"


@pytest.mark.asyncio
async def test_attachments_within_both_budgets_are_still_accepted() -> None:
    """Negative control: the two new guards must not reject a legitimate submission.

    Without this, an implementation that refused every attachment list would pass both arms above.
    """
    _reg, coord, tid = _dispatched()
    ws = FakeWorkerWebSocket(inbound=[("bytes", b"aaaaaa"), ("bytes", b"bbbbbb")])

    await worker_stream_module._handle_task_result(ws, "node-a", {"task_id": tid, "attachments": ["a", "b"]}, coord)

    assert ws.sent and ws.sent[-1]["type"] == "result_ack"
    assert ws.sent[-1]["status"] == "accepted"
    assert len(ws._inbound) == 0, "both declared frames were consumed"


def test_the_shipped_attachment_bounds_are_finite_and_independent() -> None:
    """Structural. **Not the proof** -- pins the shipped magnitudes the arms above monkeypatch away.

    The independence assertion is the load-bearing half: the two constants coincide today by a
    stated principle, and a future change that raises the aggregate budget must not silently raise
    the per-frame cap with it.
    """
    assert worker_stream_module._MAX_ATTACHMENTS == 32  # mirrors cascor's _MAX_TENSOR_MANIFEST_ENTRIES
    assert worker_stream_module._MAX_TOTAL_BINARY_SIZE == worker_stream_module._MAX_BINARY_SIZE
    assert worker_stream_module._MAX_TOTAL_BINARY_SIZE is not None
