"""Unit coverage for the injectable control-command dispatch (C-4a).

Drives :class:`LifecycleCommandExecutor` directly (bypassing the transport) so every verb branch
-- including the ``start``-unbound reject, the ``set_params``-without-params reject, and the
unhandled-command fall-through -- is exercised deterministically. Also pins the
:class:`CommandExecutor` protocol's abstract-method bodies via a ``super()``-delegating subclass.
"""

from __future__ import annotations

from typing import Any

import pytest

from juniper_service_core.websocket.commands import DEFAULT_COMMANDS, CommandExecutor, LifecycleCommandExecutor


class _FakeManager:
    """Minimal manager stand-in recording the verb each executor call delegates to."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def stop_training(self) -> dict[str, str]:
        self.calls.append(("stop", None))
        return {"status": "stopped"}

    def pause_training(self) -> dict[str, str]:
        self.calls.append(("pause", None))
        return {"status": "paused"}

    def resume_training(self) -> dict[str, str]:
        self.calls.append(("resume", None))
        return {"status": "resumed"}

    def reset(self) -> dict[str, str]:
        self.calls.append(("reset", None))
        return {"status": "reset"}

    def update_params(self, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("set_params", params))
        return dict(params)


def test_start_unbound_drops_verb_and_rejects() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    assert "start" not in executor.commands
    with pytest.raises(ValueError, match="start handler"):
        executor.execute("start")


def test_start_bound_delegates_to_callback() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr, start=lambda params: {"started": params})
    assert executor.commands == DEFAULT_COMMANDS
    assert executor.execute("start", {"epochs": 3}) == {"started": {"epochs": 3}}


def test_stop_and_resume_delegate_to_manager() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    assert executor.execute("stop") == {"status": "stopped"}
    assert executor.execute("resume") == {"status": "resumed"}
    assert [c[0] for c in mgr.calls] == ["stop", "resume"]


def test_pause_and_reset_delegate_to_manager() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    assert executor.execute("pause") == {"status": "paused"}
    assert executor.execute("reset") == {"status": "reset"}


def test_set_params_requires_params() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    with pytest.raises(ValueError, match="params"):
        executor.execute("set_params", None)
    assert executor.execute("set_params", {"lr": 0.1}) == {"lr": 0.1}


def test_unhandled_command_raises() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    with pytest.raises(ValueError, match="Unhandled command"):
        executor.execute("frobnicate")


def test_command_executor_protocol_abstract_bodies_raise() -> None:
    class _Impl(CommandExecutor):
        @property
        def commands(self) -> tuple[str, ...]:
            return super().commands

        def execute(self, command: str, params: dict[str, Any] | None) -> dict[str, Any]:
            return super().execute(command, params)

    impl = _Impl()
    with pytest.raises(NotImplementedError):
        _ = impl.commands
    with pytest.raises(NotImplementedError):
        impl.execute("start", None)


# ======================================================================================
# LifecycleCommandExecutor is not an extension point (APD-SVCCORE-012)
# ======================================================================================


def test_subclassing_the_default_executor_is_refused() -> None:
    """Subclassing raises at class-definition time.

    **This is the decisive arm.** ``@final`` is checker-only, and nothing type-checks this package
    -- the repo's mypy hook is scoped to ``^(scripts|tests)/`` and the sub-packages are governed by
    Ruff, whose selected rules (``E,F,W,B,I,N``) do not enforce it. So an assertion that the class
    carries ``__final__`` would pass while the constraint did nothing: exactly the "marker that
    reads as protection it does not provide" shape ``APD-SVCCORE-001`` names about
    ``_MAX_BINARY_SIZE``. ``__init_subclass__`` is what actually holds.

    Built with ``type(...)`` rather than a ``class`` statement **deliberately** -- a `class` block
    inside ``pytest.raises`` binds a name that can never be read (the definition raises), which
    CodeQL correctly reports as an unused local. ``type(name, bases, ns)`` is exactly what the
    ``class`` statement compiles to and triggers ``__init_subclass__`` identically, as an
    expression. Do not "simplify" it back.
    """
    with pytest.raises(TypeError, match="not an extension point"):
        type("_Subclass", (LifecycleCommandExecutor,), {})


def test_the_refusal_names_the_offending_class_and_an_alternative() -> None:
    """The error tells the consumer what to do instead, rather than only saying no."""
    with pytest.raises(TypeError) as excinfo:
        type("_Subclass", (LifecycleCommandExecutor,), {})

    message = str(excinfo.value)
    assert "_Subclass" in message  # names the offending class, not just the base
    assert "injection" in message
    assert "wrapping" in message


def test_the_default_executor_still_constructs_and_dispatches() -> None:
    """Negative control: the subclass guard must not disturb ordinary use.

    Without this, a guard that broke construction outright would still pass the arms above.
    """
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    assert "stop" in executor.commands
    assert executor.execute("stop") == {"status": "stopped"}


def test_final_decorator_is_declared() -> None:
    """Structural. **Not the proof** -- kept so a later type-checker adoption reads the intent."""
    assert getattr(LifecycleCommandExecutor, "__final__", False) is True
