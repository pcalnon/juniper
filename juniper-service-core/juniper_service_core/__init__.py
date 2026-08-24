"""``juniper-service-core`` -- shared service-tier scaffolding for Juniper ML model services.

A genuinely-shared abstraction (the ``-core`` suffix): the minimal, model-agnostic
FastAPI plumbing every Juniper model service needs -- an app factory
(:func:`create_app`), a pydantic-settings base (:class:`SettingsBase`), and a generic
liveness/readiness health router. WS-2 of the model/middleware refactor
(``notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md`` in the
juniper-ml repo).

**Dependency-free top-level import.** Importing this top-level package pulls **no**
third-party runtime dependency. Only :data:`__version__` is exposed eagerly; the rest
of the public surface (``create_app``, ``SettingsBase``, the security helpers, the
secrets helper, and the middleware classes) is imported lazily on attribute access
(PEP 562 ``__getattr__``) from submodules that *do* require ``fastapi`` /
``pydantic-settings`` / ``starlette``. This is what lets the TestPyPI publish-verify
run a clean ``--no-deps`` ``import juniper_service_core`` check.

cascor's generic service infra extracted so far (de-cascored): API-key auth + rate
limiting (:mod:`~juniper_service_core.security`), Docker-secrets reading
(:mod:`~juniper_service_core.secrets`), the security / body-limit middleware
(:mod:`~juniper_service_core.middleware`), the subprocess service launcher
(:mod:`~juniper_service_core.launcher`), the **synchronous** and **threaded-orchestrator**
lifecycle bodies (:mod:`~juniper_service_core.lifecycle` -- ``TrainingLifecycle`` and
``ServiceLifecycleManager``, which drive a ``juniper-model-core`` ``TrainableModel`` through a
status FSM + a ``TrainingEvent`` monitor), and the **generic HTTP routes**
(:mod:`~juniper_service_core.routes` -- training control, metrics, dataset, and model
introspection over the injected lifecycle). The websocket / worker subsystems -- and the
worker-coordinated lifecycle body (OQ-11) -- remain deferred (later T2 follow-ups; OUT-11
steps 2-3).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from juniper_service_core._version import __version__

# APD-SVCCORE-006: eager, like ``__version__``. Both are dependency-free, and a
# consumer must be able to write ``except JuniperServiceCoreError`` without the
# lazy machinery importing fastapi/pydantic-settings to resolve the name.
from juniper_service_core.exceptions import JuniperServiceCoreError

if TYPE_CHECKING:
    # Static-analysis-only imports. ``TYPE_CHECKING`` is False at run time, so these never
    # execute -- the dependency-free top-level import is preserved and the PEP 562
    # ``__getattr__`` below does the real lazy resolution. Their purpose is to make every
    # lazily-exported name resolvable for type checkers and for CodeQL's ``py/undefined-export``
    # query, which cannot see through ``__getattr__``.
    from juniper_service_core.app import create_app
    from juniper_service_core.auth_posture import AuthPostureError, auth_is_configured, enforce_auth_posture
    from juniper_service_core.dependency_floors import DependencyFloorError, enforce_dependency_floors
    from juniper_service_core.launcher import ManagedService, start_service, wait_for_health
    from juniper_service_core.lifecycle import (
        EventCollector,
        LifecycleCommand,
        LifecycleMonitor,
        LifecycleStateMachine,
        LifecycleStatus,
        ReplaySession,
        ServiceLifecycleManager,
        SnapshotNotFoundError,
        SnapshotStore,
        TrainingLifecycle,
    )
    from juniper_service_core.middleware import (
        RequestBodyLimitMiddleware,
        SecurityHeadersMiddleware,
        SecurityMiddleware,
    )
    from juniper_service_core.routes import (
        ResponseEnvelope,
        build_routers,
        error_response,
        get_lifecycle,
        success_response,
    )
    from juniper_service_core.secrets import get_secret
    from juniper_service_core.security import (
        APIKeyAuth,
        FailedAuthThrottle,
        RateLimiter,
        api_key_header,
        build_api_key_auth,
        build_failed_auth_throttle,
        build_rate_limiter,
    )
    from juniper_service_core.settings import SettingsBase
    from juniper_service_core.websocket import (
        CommandExecutor,
        LifecycleCommandExecutor,
        ReplayOutOfRange,
        WebSocketManager,
        attach_websocket,
        attach_worker_pool,
        build_websocket_router,
        build_worker_router,
        control_stream_handler,
        training_stream_handler,
        worker_stream_handler,
        ws_authenticate,
    )
    from juniper_service_core.workers import (
        AnomalyDetector,
        AuditEventType,
        AuditLogger,
        ConnectionRateLimiter,
        ParsedResult,
        PendingTask,
        TLSConfig,
        WorkerCoordinator,
        WorkerMetrics,
        WorkerRegistration,
        WorkerRegistry,
        WorkerRegistryCollector,
        WorkerRegistryFullError,
        WorkerTaskProtocol,
    )

__all__ = [
    "__version__",
    "JuniperServiceCoreError",
    "create_app",
    "SettingsBase",
    # Dependency-floor boot self-check (lazy, from .dependency_floors -- stdlib-only)
    "enforce_dependency_floors",
    "DependencyFloorError",
    # Auth-posture boot self-check (lazy, from .auth_posture -- stdlib-only; SEC-F01)
    "enforce_auth_posture",
    "auth_is_configured",
    "AuthPostureError",
    # Security (lazy, from .security)
    "APIKeyAuth",
    "FailedAuthThrottle",
    "RateLimiter",
    "api_key_header",
    "build_api_key_auth",
    "build_failed_auth_throttle",
    "build_rate_limiter",
    # Secrets (lazy, from .secrets)
    "get_secret",
    # Middleware (lazy, from .middleware)
    "SecurityHeadersMiddleware",
    "RequestBodyLimitMiddleware",
    "SecurityMiddleware",
    # Launcher (lazy, from .launcher -- stdlib-only)
    "ManagedService",
    "start_service",
    "wait_for_health",
    # Lifecycle (lazy, from .lifecycle -- requires juniper-model-core)
    "TrainingLifecycle",
    "EventCollector",
    "ServiceLifecycleManager",
    "LifecycleStateMachine",
    "LifecycleStatus",
    "LifecycleCommand",
    "LifecycleMonitor",
    "SnapshotStore",
    "SnapshotNotFoundError",
    "ReplaySession",
    # Generic routes (lazy, from .routes -- requires fastapi)
    "build_routers",
    "get_lifecycle",
    "success_response",
    "error_response",
    "ResponseEnvelope",
    # WebSocket subsystem (lazy, from .websocket -- requires fastapi)
    "WebSocketManager",
    "ws_authenticate",
    "ReplayOutOfRange",
    "CommandExecutor",
    "LifecycleCommandExecutor",
    "training_stream_handler",
    "control_stream_handler",
    "build_websocket_router",
    "attach_websocket",
    # Worker channel (lazy, from .websocket -- requires fastapi; step 3b /ws/workers)
    "worker_stream_handler",
    "build_worker_router",
    "attach_worker_pool",
    # Worker-pool subsystem (lazy, from .workers -- stdlib-only foundations)
    "WorkerRegistry",
    "WorkerRegistration",
    "WorkerRegistryFullError",
    "TLSConfig",
    "ConnectionRateLimiter",
    "AnomalyDetector",
    "AuditLogger",
    "WorkerMetrics",
    "AuditEventType",
    "WorkerRegistryCollector",
    # Worker coordinator (lazy, from .workers -- stdlib-only; step 3b)
    "WorkerCoordinator",
    "PendingTask",
    "WorkerTaskProtocol",
    "ParsedResult",
]

# Maps each lazily-resolved public name to the submodule that defines it. Keeping
# these imports out of module top level preserves the dependency-free
# ``import juniper_service_core`` guarantee: ``fastapi`` / ``pydantic-settings`` /
# ``starlette`` are only imported when one of these names is actually accessed.
# (``.secrets`` is stdlib-only, but is routed here too for uniformity.)
_LAZY_EXPORTS = {
    "create_app": "juniper_service_core.app",
    "SettingsBase": "juniper_service_core.settings",
    # .dependency_floors is stdlib-only (importlib.metadata / tomllib; packaging optional),
    # but is routed through the lazy path too so the PEP 562 pattern stays uniform.
    "enforce_dependency_floors": "juniper_service_core.dependency_floors",
    "DependencyFloorError": "juniper_service_core.dependency_floors",
    "enforce_auth_posture": "juniper_service_core.auth_posture",
    "auth_is_configured": "juniper_service_core.auth_posture",
    "AuthPostureError": "juniper_service_core.auth_posture",
    "APIKeyAuth": "juniper_service_core.security",
    "FailedAuthThrottle": "juniper_service_core.security",
    "RateLimiter": "juniper_service_core.security",
    "api_key_header": "juniper_service_core.security",
    "build_api_key_auth": "juniper_service_core.security",
    "build_failed_auth_throttle": "juniper_service_core.security",
    "build_rate_limiter": "juniper_service_core.security",
    "get_secret": "juniper_service_core.secrets",
    "SecurityHeadersMiddleware": "juniper_service_core.middleware",
    "RequestBodyLimitMiddleware": "juniper_service_core.middleware",
    "SecurityMiddleware": "juniper_service_core.middleware",
    # .launcher is stdlib-only (asyncio / subprocess / urllib), but is routed
    # through the lazy path too so the PEP 562 pattern stays uniform.
    "ManagedService": "juniper_service_core.launcher",
    "start_service": "juniper_service_core.launcher",
    "wait_for_health": "juniper_service_core.launcher",
    # .lifecycle requires juniper-model-core; kept lazy so the top-level import stays
    # dependency-free and the --no-deps publish-verify still works.
    "TrainingLifecycle": "juniper_service_core.lifecycle",
    "EventCollector": "juniper_service_core.lifecycle",
    "ServiceLifecycleManager": "juniper_service_core.lifecycle",
    "LifecycleStateMachine": "juniper_service_core.lifecycle",
    "LifecycleStatus": "juniper_service_core.lifecycle",
    "LifecycleCommand": "juniper_service_core.lifecycle",
    "LifecycleMonitor": "juniper_service_core.lifecycle",
    "SnapshotStore": "juniper_service_core.lifecycle",
    "SnapshotNotFoundError": "juniper_service_core.lifecycle",
    "ReplaySession": "juniper_service_core.lifecycle",
    # .routes requires fastapi; kept lazy so the top-level import stays dependency-free.
    "build_routers": "juniper_service_core.routes",
    "get_lifecycle": "juniper_service_core.routes",
    "success_response": "juniper_service_core.routes",
    "error_response": "juniper_service_core.routes",
    "ResponseEnvelope": "juniper_service_core.routes",
    # .websocket requires fastapi; kept lazy so the top-level import stays dependency-free.
    "WebSocketManager": "juniper_service_core.websocket",
    "ws_authenticate": "juniper_service_core.websocket",
    "ReplayOutOfRange": "juniper_service_core.websocket",
    "CommandExecutor": "juniper_service_core.websocket",
    "LifecycleCommandExecutor": "juniper_service_core.websocket",
    "training_stream_handler": "juniper_service_core.websocket",
    "control_stream_handler": "juniper_service_core.websocket",
    "build_websocket_router": "juniper_service_core.websocket",
    "attach_websocket": "juniper_service_core.websocket",
    # Worker channel (.websocket; requires fastapi). The /ws/workers handler + its app wiring.
    "worker_stream_handler": "juniper_service_core.websocket",
    "build_worker_router": "juniper_service_core.websocket",
    "attach_worker_pool": "juniper_service_core.websocket",
    # .workers is stdlib-only (prometheus_client is a lazy import inside the collector's
    # collect()); routed through the lazy path too so the PEP 562 pattern stays uniform.
    "WorkerRegistry": "juniper_service_core.workers",
    "WorkerRegistration": "juniper_service_core.workers",
    "WorkerRegistryFullError": "juniper_service_core.workers",
    "TLSConfig": "juniper_service_core.workers",
    "ConnectionRateLimiter": "juniper_service_core.workers",
    "AnomalyDetector": "juniper_service_core.workers",
    "AuditLogger": "juniper_service_core.workers",
    "WorkerMetrics": "juniper_service_core.workers",
    "AuditEventType": "juniper_service_core.workers",
    "WorkerRegistryCollector": "juniper_service_core.workers",
    # Worker coordinator (.workers; stdlib-only). Task dispatch/collect over the protocol seam.
    "WorkerCoordinator": "juniper_service_core.workers",
    "PendingTask": "juniper_service_core.workers",
    "WorkerTaskProtocol": "juniper_service_core.workers",
    "ParsedResult": "juniper_service_core.workers",
}


def __getattr__(name: str):
    """Lazily resolve the third-party-dependent public surface (PEP 562).

    Keeping these imports out of module top level preserves the dependency-free
    ``import juniper_service_core`` guarantee: ``fastapi`` / ``pydantic-settings`` /
    ``starlette`` are only imported when one of the lazy exports is accessed.
    """
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        from importlib import import_module

        return getattr(import_module(module_name), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """The lazy public surface **plus** what the module actually has (APD-SVCCORE-017).

    Defining ``__dir__`` replaces the default entirely rather than extending it, so
    returning ``__all__`` alone made ``dir()`` a strictly *smaller* view than the module:
    ``__name__``, ``__file__``, ``__doc__``, ``__path__`` and every eagerly bound name all
    disappeared. That is the opposite of what a ``__dir__`` on a PEP 562 module is for --
    it exists to *add* the lazily resolvable names, which ``globals()`` cannot know about,
    not to hide the ones already there. REPL completion and ``inspect``-style tooling both
    read this.
    """
    return sorted(set(__all__) | set(globals()))
