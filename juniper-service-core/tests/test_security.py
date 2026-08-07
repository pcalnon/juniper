"""Tests for :mod:`juniper_service_core.security`.

Covers :class:`APIKeyAuth` (validate + the async dependency ``__call__``),
:class:`RateLimiter` (fixed-window counting, ``reset``, and the read-only
props), and the pure config-injected factories.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from juniper_service_core.security import (
    APIKeyAuth,
    RateLimiter,
    api_key_header,
    build_api_key_auth,
    build_rate_limiter,
)


def _make_request(headers: dict[str, str] | None = None) -> Request:
    """Build a minimal Starlette :class:`Request` with the given headers."""
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
        "client": ("testclient", 50000),
    }
    return Request(scope)


# --- APIKeyAuth: validate() -------------------------------------------------


def test_disabled_when_no_keys():
    auth = APIKeyAuth(None)
    assert auth.enabled is False
    assert auth.validate("anything") is True
    assert auth.validate(None) is True


def test_disabled_when_empty_list():
    auth = APIKeyAuth([])
    assert auth.enabled is False
    assert auth.validate("anything") is True


def test_validate_with_configured_keys():
    auth = APIKeyAuth(["k"])
    assert auth.enabled is True
    assert auth.validate("k") is True
    assert auth.validate("x") is False
    assert auth.validate(None) is False


def test_blank_only_configured_keys_disable_auth():
    """Empty/placeholder secret files resolve to blanks — must not enable auth."""
    auth = APIKeyAuth(["", "  ", "\n", "\t"])
    assert auth.enabled is False
    assert auth.validate("") is True  # open mode when no real keys
    assert auth.validate(None) is True


def test_blank_keys_filtered_alongside_real_key():
    auth = APIKeyAuth(["", "  ", "real-key"])
    assert auth.enabled is True
    assert auth.validate("real-key") is True
    assert auth.validate("") is False
    assert auth.validate("  ") is False


# --- APIKeyAuth: async __call__ dependency ----------------------------------


@pytest.mark.asyncio
async def test_call_returns_none_when_disabled():
    auth = APIKeyAuth(None)
    assert await auth(_make_request()) is None


@pytest.mark.asyncio
async def test_call_returns_key_when_valid():
    auth = APIKeyAuth(["k"])
    assert await auth(_make_request({"X-API-Key": "k"})) == "k"


@pytest.mark.asyncio
async def test_call_raises_401_on_missing_key():
    auth = APIKeyAuth(["k"])
    with pytest.raises(HTTPException) as exc_info:
        await auth(_make_request())
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_call_raises_401_on_invalid_key():
    auth = APIKeyAuth(["k"])
    with pytest.raises(HTTPException) as exc_info:
        await auth(_make_request({"X-API-Key": "wrong"}))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_call_blank_only_keys_are_open_not_empty_header_auth():
    """Blank-only config must stay open (disabled), not authenticate empty X-API-Key."""
    auth = APIKeyAuth([""])
    assert auth.enabled is False
    assert await auth(_make_request({"X-API-Key": ""})) is None
    assert await auth(_make_request()) is None


def test_build_api_key_auth_filters_blank_keys():
    auth = build_api_key_auth(["", "  ", "k"])
    assert auth.enabled is True
    assert auth.validate("k") is True
    assert auth.validate("") is False

    disabled = build_api_key_auth(["", "\n"])
    assert disabled.enabled is False


# --- RateLimiter ------------------------------------------------------------


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(requests_per_minute=2)
    allowed1, _, _ = limiter.check("key-a")
    allowed2, _, _ = limiter.check("key-a")
    allowed3, remaining3, _ = limiter.check("key-a")
    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is False
    assert remaining3 == 0


def test_rate_limiter_reset_clears_counters():
    limiter = RateLimiter(requests_per_minute=2)
    limiter.check("key-a")
    limiter.check("key-a")
    assert limiter.check("key-a")[0] is False
    limiter.reset()
    assert limiter.check("key-a")[0] is True


def test_rate_limiter_disabled_always_allows():
    limiter = RateLimiter(requests_per_minute=1, enabled=False)
    assert limiter.enabled is False
    for _ in range(5):
        allowed, _, _ = limiter.check("key-a")
        assert allowed is True


def test_rate_limiter_props():
    limiter = RateLimiter(requests_per_minute=42, window_seconds=30)
    assert limiter.enabled is True
    assert limiter.limit == 42
    assert limiter.window == 30


def test_rate_limiter_counters_are_independent_per_key():
    limiter = RateLimiter(requests_per_minute=1)
    assert limiter.check("key-a")[0] is True
    assert limiter.check("key-b")[0] is True  # separate bucket
    assert limiter.check("key-a")[0] is False  # key-a now exhausted


# --- Factories --------------------------------------------------------------


def test_build_api_key_auth_returns_configured_instance():
    auth = build_api_key_auth(["k"])
    assert isinstance(auth, APIKeyAuth)
    assert auth.enabled is True
    assert auth.validate("k") is True

    disabled = build_api_key_auth()
    assert isinstance(disabled, APIKeyAuth)
    assert disabled.enabled is False


def test_build_rate_limiter_returns_configured_instance():
    limiter = build_rate_limiter(requests_per_minute=5, window_seconds=10, enabled=True)
    assert isinstance(limiter, RateLimiter)
    assert limiter.limit == 5
    assert limiter.window == 10
    assert limiter.enabled is True

    disabled = build_rate_limiter(enabled=False)
    assert disabled.enabled is False


def test_api_key_header_module_global():
    # Carried over verbatim from cascor: an APIKeyHeader on X-API-Key, non-erroring.
    assert api_key_header.model.name == "X-API-Key"
    assert api_key_header.auto_error is False
