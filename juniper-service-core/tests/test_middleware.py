"""Tests for :mod:`juniper_service_core.middleware`.

Drives each middleware through a real :class:`fastapi.FastAPI` app with
:class:`fastapi.testclient.TestClient`.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from juniper_service_core.middleware import (
    RequestBodyLimitMiddleware,
    SecurityHeadersMiddleware,
    SecurityMiddleware,
)
from juniper_service_core.security import APIKeyAuth, FailedAuthThrottle, RateLimiter, build_failed_auth_throttle


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

    @app.put("/v1/echo")
    async def echo_put():
        return {"ok": True, "method": "PUT"}

    @app.patch("/v1/echo")
    async def echo_patch():
        return {"ok": True, "method": "PATCH"}

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


def test_body_limit_rejects_oversized_put_and_patch():
    """PUT/PATCH must share the POST body-cap path (CR-024 always-stream)."""
    app = _base_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=10)
    client = TestClient(app)

    put_resp = client.put("/v1/echo", content=b"x" * 50)
    assert put_resp.status_code == 413
    assert put_resp.json()["detail"] == "Request body too large"

    patch_resp = client.patch("/v1/echo", content=b"x" * 50)
    assert patch_resp.status_code == 413
    assert patch_resp.json()["detail"] == "Request body too large"


def test_body_limit_allows_put_within_limit():
    app = _base_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=100)
    client = TestClient(app)

    response = client.put("/v1/echo", content=b"x" * 5)
    assert response.status_code == 200
    assert response.json() == {"ok": True, "method": "PUT"}


@pytest.mark.asyncio
async def test_body_limit_rejects_underdeclared_content_length():
    """CR-024: a small declared CL must not skip the stream cap when the real body is larger.

    TestClient/httpx rewrites Content-Length from the payload, so drive the ASGI app directly
    with a scope that under-declares CL while the receive channel yields a bigger body.
    """
    app = _base_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=10)

    body = b"x" * 50
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/echo",
        "raw_path": b"/v1/echo",
        "query_string": b"",
        "headers": [
            (b"content-length", b"5"),  # under-declared vs real body
            (b"content-type", b"application/octet-stream"),
        ],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    sent: list[dict] = []
    body_sent = False

    async def receive():
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)

    start = next(m for m in sent if m["type"] == "http.response.start")
    assert start["status"] == 413
    body_msgs = [m for m in sent if m["type"] == "http.response.body"]
    payload = b"".join(m.get("body", b"") for m in body_msgs)
    assert b"Request body too large" in payload


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


# ----------------------------------------------------------------------------------------
# Pre-authentication failed-attempt throttle
# ----------------------------------------------------------------------------------------


def _auth_app(throttle: FailedAuthThrottle | None = None, *, requests_per_minute: int = 1000) -> TestClient:
    """An app with API-key auth enabled and a deliberately generous identity-keyed limiter.

    The quota limiter is generous so that any 429 observed in these tests comes from the
    failed-auth throttle rather than from the quota path.
    """
    app = _base_app()
    kwargs = {} if throttle is None else {"failed_auth_throttle": throttle}
    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(["s3cret"]),
        rate_limiter=RateLimiter(requests_per_minute=requests_per_minute, enabled=True),
        **kwargs,
    )
    return TestClient(app)


def test_failed_auth_attempts_are_throttled():
    """The defect: auth raised before the limiter, so 401s consumed no budget at all.

    Pre-fix, credential guessing was unthrottled -- a bad key returned 401 forever. The pre-auth
    throttle closes that: past the budget the caller gets 429 with ``Retry-After``.
    """
    client = _auth_app(build_failed_auth_throttle(max_failures=3, window_seconds=60))

    for _ in range(3):
        assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 401

    throttled = client.get("/v1/data", headers={"X-API-Key": "wrong"})
    assert throttled.status_code == 429
    assert "failed authentication" in throttled.json()["detail"].lower()
    assert int(throttled.headers["Retry-After"]) >= 1


def test_valid_credentials_never_consume_the_throttle_budget():
    """Budget is spent only on failure, which is what makes enabling this by default safe.

    A caller presenting a valid key sees no behaviour change however many requests it makes, so
    the fix cannot throttle well-behaved traffic.
    """
    client = _auth_app(build_failed_auth_throttle(max_failures=2, window_seconds=60))

    for _ in range(20):
        assert client.get("/v1/data", headers={"X-API-Key": "s3cret"}).status_code == 200

    # Budget untouched: two failures still get 401, only the third is throttled.
    assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 429


def test_missing_api_key_also_counts_as_a_failed_attempt():
    """A flood carrying no credentials is the same attack as a flood carrying wrong ones."""
    client = _auth_app(build_failed_auth_throttle(max_failures=2, window_seconds=60))

    assert client.get("/v1/data").status_code == 401
    assert client.get("/v1/data").status_code == 401
    assert client.get("/v1/data").status_code == 429


def test_throttle_is_enabled_by_default():
    """Constructing SecurityMiddleware without the argument still closes the gap.

    An opt-in security fix that nobody opts into does not fix anything. The default budget is
    the library default of 10 failures per 60 s.
    """
    client = _auth_app()  # no throttle passed

    for _ in range(10):
        assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 429


def test_throttle_can_be_opted_out():
    """``enabled=False`` restores the pre-fix behaviour for anyone who needs it."""
    client = _auth_app(build_failed_auth_throttle(enabled=False))

    for _ in range(25):
        assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 401


def test_quota_429_is_not_counted_as_an_authentication_failure():
    """Only 401 feeds the throttle.

    A 429 from the identity-keyed limiter is a quota outcome, not a credential guess. Counting it
    would let an authenticated caller throttle *itself* out of the auth path merely by exceeding
    its own quota.
    """
    throttle = build_failed_auth_throttle(max_failures=2, window_seconds=60)
    client = _auth_app(throttle, requests_per_minute=1)

    assert client.get("/v1/data", headers={"X-API-Key": "s3cret"}).status_code == 200
    for _ in range(5):
        assert client.get("/v1/data", headers={"X-API-Key": "s3cret"}).status_code == 429

    # None of those quota 429s were recorded, so the failure budget is still intact.
    assert throttle.check("testclient")[0] is False


def test_exempt_paths_bypass_the_throttle():
    """Health checks stay reachable even from an IP that is currently throttled."""
    client = _auth_app(build_failed_auth_throttle(max_failures=1, window_seconds=60))

    assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/v1/data", headers={"X-API-Key": "wrong"}).status_code == 429
    assert client.get("/v1/health").status_code == 200


# ----------------------------------------------------------------------------------------
# FailedAuthThrottle unit behaviour
# ----------------------------------------------------------------------------------------


def test_failed_auth_throttle_check_does_not_consume_budget():
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=60)
    for _ in range(10):
        assert throttle.check("1.2.3.4") == (False, 0)
    throttle.record_failure("1.2.3.4")
    blocked, retry_after = throttle.check("1.2.3.4")
    assert blocked is True
    assert retry_after >= 1


def test_failed_auth_throttle_is_keyed_per_source_ip():
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=60)
    throttle.record_failure("1.2.3.4")
    assert throttle.check("1.2.3.4")[0] is True
    assert throttle.check("5.6.7.8")[0] is False


def test_failed_auth_throttle_window_rolls_over():
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=0)  # every check starts a new window
    throttle.record_failure("1.2.3.4")
    assert throttle.check("1.2.3.4")[0] is False


def test_failed_auth_throttle_disabled_never_blocks():
    throttle = FailedAuthThrottle(max_failures=1, enabled=False)
    for _ in range(10):
        throttle.record_failure("1.2.3.4")
    assert throttle.check("1.2.3.4") == (False, 0)


def test_failed_auth_throttle_reset_clears_state():
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=60)
    throttle.record_failure("1.2.3.4")
    assert throttle.check("1.2.3.4")[0] is True
    throttle.reset()
    assert throttle.check("1.2.3.4")[0] is False


def test_failed_auth_throttle_prunes_expired_entries():
    """Bounded memory: a dict keyed by attacker-supplied source IPs is itself a DoS vector."""
    throttle = FailedAuthThrottle(max_failures=100, window_seconds=0)
    for i in range(FailedAuthThrottle._CLEANUP_INTERVAL + 10):
        throttle.record_failure(f"10.0.0.{i % 255}")
    assert len(throttle._failures) <= FailedAuthThrottle._MAX_ENTRIES
