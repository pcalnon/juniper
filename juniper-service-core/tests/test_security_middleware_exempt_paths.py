"""Pin SecurityMiddleware EXEMPT_PATHS beyond the sole /v1/health arm in test_middleware.py.

``/metrics`` and ``/metrics/`` must stay API-key-exempt: MetricsAuthMiddleware owns the
IP allowlist for scrapers (SEC-16). ``/v1/health/live`` and ``/v1/health/ready`` are the
probe paths load balancers hit without credentials. A regression that drops any of these
from EXEMPT_PATHS turns authenticated-only scrapers/probes into silent 401 outages.

Lives in a dedicated file so it does not collide with open PRs editing test_middleware.py
(#985 Retry-After, #986 CR-024 body limit).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from juniper_service_core.middleware import EXEMPT_PATHS, SecurityMiddleware
from juniper_service_core.security import APIKeyAuth, RateLimiter


def _app_with_exempt_routes() -> FastAPI:
    app = FastAPI()

    @app.get("/v1/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/health/live")
    async def health_live():
        return {"status": "live"}

    @app.get("/v1/health/ready")
    async def health_ready():
        return {"status": "ready"}

    @app.get("/metrics")
    async def metrics():
        return "# TYPE up gauge\nup 1\n"

    @app.get("/metrics/")
    async def metrics_slash():
        return "# TYPE up gauge\nup 1\n"

    @app.get("/v1/data")
    async def data():
        return {"data": "value"}

    return app


def _secured(app: FastAPI, *, rate_limit: bool = False, rpm: int = 60) -> TestClient:
    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(["required-key"]),
        rate_limiter=RateLimiter(requests_per_minute=rpm, enabled=rate_limit),
    )
    return TestClient(app)


def test_exempt_paths_constant_includes_metrics_and_probe_variants() -> None:
    # Structural pin: the SEC-16 / probe set must remain in the module constant.
    for path in ("/metrics", "/metrics/", "/v1/health", "/v1/health/live", "/v1/health/ready"):
        assert path in EXEMPT_PATHS


def test_metrics_and_metrics_slash_reachable_without_api_key() -> None:
    client = _secured(_app_with_exempt_routes())
    for path in ("/metrics", "/metrics/"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "up 1" in response.text


def test_health_live_and_ready_reachable_without_api_key() -> None:
    # test_middleware.py only pins /v1/health; live/ready are the k8s-style probes.
    client = _secured(_app_with_exempt_routes())
    live = client.get("/v1/health/live")
    ready = client.get("/v1/health/ready")
    assert live.status_code == 200 and live.json() == {"status": "live"}
    assert ready.status_code == 200 and ready.json() == {"status": "ready"}


def test_non_exempt_path_still_requires_api_key() -> None:
    # Negative control: exemption is path-scoped, not a global auth disable.
    client = _secured(_app_with_exempt_routes())
    assert client.get("/v1/data").status_code == 401
    assert client.get("/v1/data", headers={"X-API-Key": "required-key"}).status_code == 200


def test_metrics_exemption_also_skips_rate_limiting() -> None:
    # EXEMPT_PATHS short-circuits before rate limiting; scrapers must not 429 on /metrics.
    client = _secured(_app_with_exempt_routes(), rate_limit=True, rpm=1)
    for _ in range(5):
        assert client.get("/metrics").status_code == 200
    # Same limiter still enforces on a non-exempt path once the key is supplied.
    headers = {"X-API-Key": "required-key"}
    assert client.get("/v1/data", headers=headers).status_code == 200
    assert client.get("/v1/data", headers=headers).status_code == 429
