"""Injectable command dispatch for the WebSocket control channel (WS-2 / OUT-11 T2 step 2).

The ADAPTER seam from design §5.6: cascor's ``/ws/control`` handler hard-wired an
``_execute_command(lifecycle, command, params)`` that called cascor's own
``start_training()`` / ``stop_training()`` / ... . The generic control handler instead
dispatches to an injectable :class:`CommandExecutor` read off ``app.state.command_executor``,
so a service maps the wire commands onto *its* orchestration without the base hard-coding any
verb semantics.

Why ``start`` in particular must be injected: the generic
:class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager.start_training` requires
the training arrays as explicit arguments, whereas a service's ``start`` command typically pulls
a *pre-loaded* dataset (and, for cascor, constructs the network) before calling it. That binding
is service-specific, so :class:`LifecycleCommandExecutor` takes a ``start`` callback; the other
five verbs (stop / pause / resume / reset / set_params) map straight onto the generic manager.

Pure stdlib + typing -- no ``fastapi`` import (the control handler owns the transport).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, final, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Callable

    from juniper_service_core.lifecycle.manager import ServiceLifecycleManager

__all__ = ["CommandExecutor", "LifecycleCommandExecutor", "DEFAULT_COMMANDS"]

#: The standard control verbs cascor's ``/ws/control`` accepts; the generic default executor
#: maps all but ``start`` directly onto the manager.
DEFAULT_COMMANDS: tuple[str, ...] = ("start", "stop", "pause", "resume", "reset", "set_params")


@runtime_checkable
class CommandExecutor(Protocol):
    """Structural contract the control handler dispatches each command through.

    A service injects any object satisfying this protocol on ``app.state.command_executor``.
    :meth:`execute` runs **off the event loop** (the handler calls it via ``asyncio.to_thread``
    under a per-command timeout), so a blocking implementation is fine. It should return a
    JSON-ready ``dict`` result on success and raise ``ValueError`` for an unknown / malformed
    command (the handler maps that to a ``command_response`` error).
    """

    @property
    @abstractmethod
    def commands(self) -> tuple[str, ...]:
        """The closed set of command names this executor accepts (drives the early reject)."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, command: str, params: dict[str, Any] | None) -> dict[str, Any]:
        """Execute one validated command and return its JSON-ready result."""
        raise NotImplementedError


@final
class LifecycleCommandExecutor:
    """Default :class:`CommandExecutor` mapping the standard verbs onto a manager.

    ``stop`` / ``pause`` / ``resume`` / ``reset`` / ``set_params`` delegate straight to the
    injected :class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager`. ``start``
    is delegated to the ``start`` callback (because binding training data is service-specific);
    when no ``start`` callback is supplied, ``start`` is dropped from :attr:`commands` and a
    ``start`` request is rejected as an unknown command.

    **Not an extension point -- subclassing is refused, at runtime.** This class exists so that
    publishing :class:`CommandExecutor` does not leave extension as pure obligation; it is *not* a
    base class. Vary behaviour the way the design intends:

    * **by injection** -- the ``start`` callback is the designed variation point;
    * **by implementing** :class:`CommandExecutor` directly (it is structural: no import, no
      inheritance, no registration); or
    * **by wrapping** an instance of this class and delegating the verbs you do not change.

    Subclassing instead re-creates the fragile-base-class coupling the composition-only design
    exists to avoid: ``execute``'s verb chain, ``_commands``' construction and the ``start``-unbound
    fallback would all silently become frozen contract. ``@final`` alone would not stop it --
    nothing type-checks this package (the repo's mypy hook is scoped to ``^(scripts|tests)/``, and
    the sub-packages are governed by Ruff, whose selected rules do not enforce ``@final``), so the
    decorator would read as a protection it does not provide. :meth:`__init_subclass__` is what
    actually holds.
    """

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Refuse subclassing. See the class docstring for the three supported variation points."""
        raise TypeError(f"LifecycleCommandExecutor is final and is not an extension point (tried to subclass it as {cls.__name__!r}). Vary behaviour by injection (the `start` callback), by implementing the CommandExecutor protocol directly, or by wrapping an instance and delegating.")

    def __init__(
        self,
        manager: ServiceLifecycleManager,
        *,
        start: Callable[[dict[str, Any] | None], dict[str, Any]] | None = None,
    ) -> None:
        self._manager = manager
        self._start = start
        # Advertise only the verbs we can actually service: omit ``start`` when unbound.
        self._commands: tuple[str, ...] = DEFAULT_COMMANDS if start is not None else tuple(c for c in DEFAULT_COMMANDS if c != "start")

    @property
    def commands(self) -> tuple[str, ...]:
        return self._commands

    def execute(self, command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Dispatch one command to the manager. Raises ``ValueError`` for unknown/malformed input."""
        if command == "start":
            if self._start is None:
                raise ValueError("start command requires a configured start handler")
            return self._start(params)
        if command == "stop":
            return self._manager.stop_training()
        if command == "pause":
            return self._manager.pause_training()
        if command == "resume":
            return self._manager.resume_training()
        if command == "reset":
            return self._manager.reset()
        if command == "set_params":
            if not params:
                raise ValueError("set_params requires a 'params' dict")
            return self._manager.update_params(params)
        raise ValueError(f"Unhandled command: {command!r}")
