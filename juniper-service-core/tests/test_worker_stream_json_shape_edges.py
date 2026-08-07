"""Fail-closed coverage for JSON-valid non-object worker registration frames.

``_handle_registration`` already closes 4006 on JSONDecodeError. Arrays /
scalars / null parse successfully but are not registration dicts — without an
``isinstance(msg, dict)`` gate, ``msg.get`` AttributeErrors before the 4008
shape path. New file avoids contested ``test_worker_stream_edges.py`` (#989)
and ``test_t2_worker_coordinator.py`` (#984).
"""

from __future__ import annotations

from collections import deque
from types import SimpleNamespace

import pytest
from fastapi import WebSocketDisconnect

from juniper_service_core.websocket import attach_worker_pool, worker_stream_handler
from juniper_service_core.workers import ParsedResult, WorkerCoordinator, WorkerRegistry


class _TrivialProtocol:
    def build_assignment(self, task):
        return ({"type": "task_assign", "task_id": task.task_id, "round_id": task.round_id, "payload": task.payload}, [])

    def result_attachments(self, msg):
        return list(msg.get("attachments", []))

    def parse_result(self, worker_id, msg, frames):
        return ParsedResult(success=True, result={"task_id": msg.get("task_id")}, score=msg.get("score"))


class _FakeWorkerWS:
    def __init__(self, *, inbound=None) -> None:
        self._inbound = deque(inbound or [])
        self.headers: dict = {}
        self.client = ("10.0.0.9", 5000)
        self.app = None
        self.sent: list[dict] = []
        self.accepted = False
        self.closed: tuple[int, str] | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._inbound:
            raise WebSocketDisconnect(1000)
        return self._inbound.popleft()

    async def receive(self) -> dict:
        if not self._inbound:
            raise WebSocketDisconnect(1000)
        return {"text": self._inbound.popleft()}


def _wire_app(registry: WorkerRegistry, coordinator: WorkerCoordinator) -> SimpleNamespace:
    app = SimpleNamespace(state=SimpleNamespace())
    attach_worker_pool(app, registry=registry, coordinator=coordinator)
    return app


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", ["[]", "null", '"register"', "42", "true"])
async def test_registration_rejects_non_object_json(raw: str) -> None:
    registry = WorkerRegistry()
    coord = WorkerCoordinator(registry, _TrivialProtocol())
    app = _wire_app(registry, coord)
    ws = _FakeWorkerWS(inbound=[raw])
    ws.app = app
    await worker_stream_handler(ws)
    assert ws.closed is not None and ws.closed[0] == 4008
    assert registry.worker_count == 0
    assert any(m.get("type") == "error" and "Invalid registration" in m.get("error", "") for m in ws.sent)
