"""Pin FSM START rejection while INVESTIGATING / REPLAYING (lifecycle/state_machine.py).

``_handle_start`` explicitly refuses START while a snapshot is loaded for inspection
(INVESTIGATING) or an active replay is running (REPLAYING). Existing coverage enters
those states (predicates / snapshot routes / manager.start_training) but never asserts
the pure FSM contract that START returns False and leaves the status unchanged —
a regression that auto-starts training from INVESTIGATING would discard the loaded
snapshot inspection session.

Hermetic stdlib-only; no FastAPI / network.
"""

from __future__ import annotations

from juniper_service_core.lifecycle.state_machine import (
    LifecycleCommand,
    LifecycleStateMachine,
    LifecycleStatus,
)


def test_start_rejected_while_investigating_leaves_status_unchanged() -> None:
    sm = LifecycleStateMachine()
    assert sm.mark_investigating() is True
    assert sm.status is LifecycleStatus.INVESTIGATING

    assert sm.handle_command(LifecycleCommand.START) is False
    assert sm.status is LifecycleStatus.INVESTIGATING
    assert sm.is_investigating() is True


def test_start_rejected_while_replaying_leaves_status_unchanged() -> None:
    # Manager-level start_training is covered in test_t2_replay.py; this pins the FSM arm.
    sm = LifecycleStateMachine()
    assert sm.mark_replaying() is True
    assert sm.status is LifecycleStatus.REPLAYING

    assert sm.handle_command(LifecycleCommand.START) is False
    assert sm.status is LifecycleStatus.REPLAYING
    assert sm.is_replaying() is True


def test_stop_rejected_while_investigating_does_not_exit_inspection() -> None:
    # STOP only clears STARTED/PAUSED; INVESTIGATING requires an explicit exit path
    # (retrain/resume via mark_* / RESET). Pin so STOP cannot silently drop inspection.
    sm = LifecycleStateMachine()
    assert sm.mark_investigating() is True
    assert sm.handle_command(LifecycleCommand.STOP) is False
    assert sm.status is LifecycleStatus.INVESTIGATING


def test_start_from_resume_ready_still_succeeds() -> None:
    # Negative control for the INVESTIGATING/REPLAYING gate: RESUME_READY must START.
    sm = LifecycleStateMachine()
    assert sm.mark_resume_ready() is True
    assert sm.handle_command(LifecycleCommand.START) is True
    assert sm.status is LifecycleStatus.STARTED
