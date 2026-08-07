"""Coverage for the lifecycle -> WebSocket broadcast bridge (C-4a + unknown-frame degrade).

``test_t2_websocket.py`` always passes an explicit ``ws_manager`` to ``attach_websocket`` and
exercises live/replay sinks with known ``metrics`` / ``state`` types. This file pins:

* the omitted-``ws_manager`` default-construction branch;
* ``build_frame_sink`` unknown ``type`` → generic ``event`` envelope (must not drop/crash).
"""

from __future__ import annotations

from fastapi import FastAPI
from juniper_model_core.conformance.reference import ReferenceGrowableModel

from juniper_service_core.lifecycle import ServiceLifecycleManager
from juniper_service_core.websocket import WebSocketManager, attach_websocket, build_frame_sink


class _RecordingWsManager:
    """Captures ``broadcast_from_thread`` calls for synchronous sink assertions."""

    def __init__(self) -> None:
        self.broadcasts: list[dict] = []

    def broadcast_from_thread(self, message: dict) -> None:
        self.broadcasts.append(message)


def test_attach_websocket_constructs_default_manager() -> None:
    app = FastAPI()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())
    try:
        ws_manager = attach_websocket(app, manager=manager)  # no ws_manager -> default constructed
        assert isinstance(ws_manager, WebSocketManager)
        assert app.state.ws_manager is ws_manager
        assert app.state.lifecycle is manager
    finally:
        manager.shutdown()


def test_build_frame_sink_unknown_type_degrades_to_event() -> None:
    """Unknown frame types must fall back to the event envelope, not drop or raise."""
    recording = _RecordingWsManager()
    sink = build_frame_sink(recording)  # type: ignore[arg-type]

    sink({"type": "cascade_add", "data": {"unit": 3}})
    sink({"type": "candidate_progress", "data": {"pct": 0.5}})
    # Missing type also degrades via the default lookup key ("event") / fallback builder.
    sink({"data": {"note": "typeless"}})

    assert len(recording.broadcasts) == 3
    assert all(b["type"] == "event" for b in recording.broadcasts)
    assert recording.broadcasts[0]["data"] == {"unit": 3}
    assert recording.broadcasts[1]["data"] == {"pct": 0.5}
    assert recording.broadcasts[2]["data"] == {"note": "typeless"}


def test_build_frame_sink_known_types_keep_their_envelopes() -> None:
    """Regression guard: the unknown-type fallback must not swallow metrics/state."""
    recording = _RecordingWsManager()
    sink = build_frame_sink(recording)  # type: ignore[arg-type]

    sink({"type": "metrics", "data": {"mse": 0.1}})
    sink({"type": "state", "data": {"phase": "running"}})
    sink({"type": "event", "data": {"name": "epoch_end"}})

    assert [b["type"] for b in recording.broadcasts] == ["metrics", "state", "event"]
    assert recording.broadcasts[0]["data"] == {"mse": 0.1}
    assert recording.broadcasts[1]["data"] == {"phase": "running"}
