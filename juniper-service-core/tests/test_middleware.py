"""Tests for :mod:`juniper_service_core.middleware`.

Drives each middleware through a real :class:`fastapi.FastAPI` app with
:class:`fastapi.testclient.TestClient`.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from juniper_service_core.middleware import (
    RequestBodyLimitMiddleware,
    SecurityHeadersMiddleware,
    SecurityMiddleware,
)
from juniper_service_core.security import APIKeyAuth, RateLimiter


def _base_app() -> FastAPI:
    app = FastAPI()

    @app.get("/v1/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/data")
    async def data():
        return {"data": "value"}

    @app.post("/v1/echo")
    async def echo():
        return {"ok": True}

    return app


# --- SecurityHeadersMiddleware ----------------------------------------------


def test_security_headers_are_added():
    app = _base_app()
    app.add_middleware(SecurityHeadersMiddleware)
    client = TestClient(app)

    response = client.get("/v1/data")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_security_headers_custom_csp():
    app = _base_app()
    app.add_middleware(SecurityHeadersMiddleware, content_security_policy="default-src 'self'")
    client = TestClient(app)

    response = client.get("/v1/data")
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"


def test_hsts_only_when_forwarded_https():
    app = _base_app()
    app.add_middleware(SecurityHeadersMiddleware)
    client = TestClient(app)

    plain = client.get("/v1/data")
    assert "Strict-Transport-Security" not in plain.headers

    https = client.get("/v1/data", headers={"X-Forwarded-Proto": "https"})
    assert "Strict-Transport-Security" in https.headers


# --- RequestBodyLimitMiddleware ---------------------------------------------


def test_body_limit_rejects_oversized_post():
    app = _base_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=10)
    client = TestClient(app)

    response = client.post("/v1/echo", content=b"x" * 50)
    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"


def test_body_limit_allows_within_limit():
    app = _base_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=100)
    client = TestClient(app)

    response = client.post("/v1/echo", content=b"x" * 5)
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_body_limit_rejects_invalid_content_length():
    app = _base_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=100)
    client = TestClient(app)

    response = client.post("/v1/echo", content=b"x", headers={"content-length": "not-a-number"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Content-Length header"


# --- SecurityMiddleware -----------------------------------------------------


def _secured_app(api_keys: list[str] | None) -> FastAPI:
    app = _base_app()
    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(api_keys),
        rate_limiter=RateLimiter(enabled=False),
    )
    return app


def test_security_middleware_401_without_key():
    client = TestClient(_secured_app(["k"]))
    response = client.get("/v1/data")
    assert response.status_code == 401


def test_security_middleware_200_with_valid_key():
    client = TestClient(_secured_app(["k"]))
    response = client.get("/v1/data", headers={"X-API-Key": "k"})
    assert response.status_code == 200
    assert response.json() == {"data": "value"}


def test_security_middleware_401_with_invalid_key():
    client = TestClient(_secured_app(["k"]))
    response = client.get("/v1/data", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_security_middleware_exempts_health_path():
    # /v1/health is in EXEMPT_PATHS -> reachable without a key even when auth is on.
    client = TestClient(_secured_app(["k"]))
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_security_middleware_open_when_auth_disabled():
    # No keys configured -> auth disabled -> all paths reachable without a key.
    client = TestClient(_secured_app(None))
    assert client.get("/v1/data").status_code == 200


def test_security_middleware_rate_limit_headers_present_when_enabled():
    app = _base_app()
    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(None),
        rate_limiter=RateLimiter(requests_per_minute=60, enabled=True),
    )
    client = TestClient(app)
    response = client.get("/v1/data")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_security_middleware_rate_limit_429_json_preserves_retry_after():
    """HTTPException from RateLimiter must surface as JSONResponse with Retry-After headers.

    Pins the middleware catch path (``except HTTPException`` -> ``JSONResponse(..., headers=)``)
    that unit tests of ``RateLimiter.__call__`` alone cannot exercise.
    """
    app = _base_app()
    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(None),
        rate_limiter=RateLimiter(requests_per_minute=1, enabled=True),
    )
    client = TestClient(app)
    assert client.get("/v1/data").status_code == 200
    response = client.get("/v1/data")
    assert response.status_code == 429
    body = response.json()
    assert "Rate limit exceeded" in body["detail"]
    assert response.headers["Retry-After"]
    assert response.headers["X-RateLimit-Limit"] == "1"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.headers["X-RateLimit-Reset"]
