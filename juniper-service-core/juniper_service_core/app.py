"""FastAPI application factory for Juniper model services.

:func:`create_app` builds a model-agnostic FastAPI app, mounts the generic health
router, then includes any service-supplied routers. It carries **no** model,
classification, or training logic -- those live in the owning service and are passed in
as ``routers``. This keeps the service-tier scaffolding reusable across every Juniper
model service (WS-2).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI

from juniper_service_core.health import health_router

if TYPE_CHECKING:
    from starlette.types import Lifespan


def create_app(
    *,
    title: str = "Juniper Service",
    version: str = "0.1.0",
    routers: Iterable[APIRouter] = (),
    lifespan: Lifespan[FastAPI] | None = None,
    explorers_enabled: bool = True,
) -> FastAPI:
    """Create a FastAPI app with the generic health router plus any extra routers.

    Args:
        title: OpenAPI title for the app.
        version: OpenAPI version string for the app.
        routers: Additional service routers to mount after the health router.
        lifespan: Optional FastAPI lifespan context manager, forwarded to
            ``FastAPI(lifespan=...)``. Lets a consuming service run startup/shutdown
            hooks (logging configuration, build-info, resource setup/teardown) in a
            lifespan instead of at import time or in its CLI entrypoint. Omit for the
            previous behaviour (no lifespan).
        explorers_enabled: Whether to mount the interactive API explorers
            (``/docs``, ``/redoc``). Pass ``not settings.api_keys`` -- they are
            browser pages that fetch ``/openapi.json`` by XHR with no
            ``X-API-Key`` header, so under auth they could only ever 401.
            ``/openapi.json`` itself stays mounted either way and is
            authenticated by :class:`SecurityMiddleware` (it is deliberately not
            in ``EXEMPT_PATHS``), so a secured deployment stays self-describing
            to authenticated callers instead of silently schema-less. Defaults to
            ``True``, which preserves the previous behaviour for unauthenticated
            deployments.

    Returns:
        A configured :class:`~fastapi.FastAPI` instance. Model-agnostic by design.
    """
    app = FastAPI(
        title=title,
        version=version,
        lifespan=lifespan,
        docs_url="/docs" if explorers_enabled else None,
        redoc_url="/redoc" if explorers_enabled else None,
        openapi_url="/openapi.json",
    )
    app.include_router(health_router())
    for router in routers:
        app.include_router(router)
    return app
