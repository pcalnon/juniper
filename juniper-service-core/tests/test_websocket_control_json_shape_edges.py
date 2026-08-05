"""Fail-closed coverage for JSON-valid non-object control frames.

``_control_recv_loop`` already rejects JSONDecodeError with close 1003. Arrays /
scalars / null parse successfully but are not command dicts — without an
``isinstance(msg, dict)`` gate, ``_handle_command_message`` AttributeErrors on
``msg.get`` and tears down the receive loop. New file avoids contested
``test_websocket_control_stream.py`` (#982).
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import WebSocketDisconnect

from juniper_service_core.websocket.control_security import LeakyBucket
from juniper_service_core.websocket.control_stream import _control_recv_loop


class _ControlFakeWS:
    def __init__(self, incoming: list | None = None) -> None:
        self.sent: list[dict] = []
        self.closed: tuple[int, str] | None = None
        self._incoming = list(incoming or [])

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._incoming:
            raise WebSocketDisconnect(code=1000)
        return self._incoming.pop(0)


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", ["[]", "null", '"x"', "42", "true"])
async def test_recv_loop_rejects_non_object_json(raw: str) -> None:
    ws = _ControlFakeWS(incoming=[raw])
    await _control_recv_loop(
        ws,
        executor=None,
        valid_commands={"start"},
        bucket=LeakyBucket(),
        pong_received=asyncio.Event(),
        idle_timeout=0,
        client_ip="1.2.3.4",
    )
    assert ws.closed == (1003, "Malformed JSON")
    assert any(m.get("data", {}).get("error") == "Invalid control message" for m in ws.sent)


@pytest.mark.asyncio
async def test_recv_loop_still_accepts_object_command_after_shape_gate() -> None:
    class _RecordingExecutor:
        commands = ("start",)

        def execute(self, command: str, params: dict | None) -> dict:
            return {"echo": command}

    ws = _ControlFakeWS(incoming=[json.dumps({"command": "start"})])
    with pytest.raises(WebSocketDisconnect):
        await _control_recv_loop(
            ws,
            executor=_RecordingExecutor(),
            valid_commands={"start"},
            bucket=LeakyBucket(),
            pong_received=asyncio.Event(),
            idle_timeout=0,
            client_ip="1.2.3.4",
        )
    assert any(m.get("data", {}).get("command") == "start" and m["data"]["status"] == "success" for m in ws.sent)
    assert ws.closed is None
