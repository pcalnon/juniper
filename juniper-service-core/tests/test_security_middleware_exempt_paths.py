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

from juniper_service_core.app import create_app
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


# --- APD-DATA-024 sibling: the doc paths must stay OUT of EXEMPT_PATHS --------
#
# Defect register §4.3. The sibling of APD-DATA-024 (juniper-data#295), and the
# one that was LIVE rather than latent: juniper-recurrence is the sole
# production consumer of this middleware and mounted the document.
# ``_is_exempt`` is a bare
# membership test evaluated regardless of auth configuration, so listing a doc
# path here does not "enable" the document -- it PUBLISHES it. These tests pin
# the ABSENCE, because the regression is additive: a well-meaning "re-enable the
# API docs" change re-adds the three literals and silently serves the service's
# entire API surface to unauthenticated callers.


def test_doc_paths_are_absent_from_exempt_paths() -> None:
    # Structural pin. Asserting absence, not presence -- see the note above.
    for path in ("/docs", "/openapi.json", "/redoc"):
        assert path not in EXEMPT_PATHS, f"{path} is in EXEMPT_PATHS -- SecurityMiddleware exempts it regardless of whether API keys are configured, so this publishes the OpenAPI surface to unauthenticated callers (defect register §4.3, sibling of APD-DATA-024)."


def test_openapi_document_requires_api_key_when_auth_is_on() -> None:
    # Behavioural pin: the structural test above still passes if someone renames
    # the constant, so also prove the wire behaviour through a real secured app.
    app = create_app(title="Secured", version="1.0.0", explorers_enabled=False)
    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(["required-key"]),
        rate_limiter=RateLimiter(requests_per_minute=60, enabled=False),
    )
    client = TestClient(app)

    assert client.get("/openapi.json").status_code == 401
    authorised = client.get("/openapi.json", headers={"X-API-Key": "required-key"})
    assert authorised.status_code == 200
    # Still self-describing to an authenticated caller.
    assert "openapi" in authorised.json()


def test_explorers_unmounted_under_auth_but_health_still_exempt() -> None:
    # Two-arm pin. SecurityMiddleware runs BEFORE routing, so the unauthenticated
    # arm proves the exposure is closed (401, not the 200 this entry is about) and
    # cannot distinguish mounted from unmounted; the authenticated arm is what
    # proves the explorers are genuinely not mounted (404). Asserting only the
    # first arm would pass even if the pages were still mounted.
    app = create_app(title="Secured", version="1.0.0", explorers_enabled=False)
    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(["required-key"]),
        rate_limiter=RateLimiter(requests_per_minute=60, enabled=False),
    )
    client = TestClient(app)
    headers = {"X-API-Key": "required-key"}

    for path in ("/docs", "/redoc"):
        assert client.get(path).status_code == 401, path
        assert client.get(path, headers=headers).status_code == 404, path
    # Negative control: the exemption mechanism itself still works.
    assert client.get("/v1/health").status_code == 200


def test_explorers_mounted_by_default_for_unauthenticated_deployments() -> None:
    # Default must preserve the previous behaviour: no auth -> explorers usable.
    client = TestClient(create_app(title="Open", version="1.0.0"))
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 200, path
