"""Tests for :mod:`juniper_service_core.security`.

Covers :class:`APIKeyAuth` (validate + the async dependency ``__call__``),
:class:`RateLimiter` (fixed-window counting, ``reset``, and the read-only
props), and the pure config-injected factories.
"""

from __future__ import annotations

import time

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from juniper_service_core.security import (
    APIKeyAuth,
    FailedAuthThrottle,
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


class TestRetryAfterNeverTellsTheClientZero:
    """APD-SVCCORE-004 — ``Retry-After: 0`` is an instruction to hammer.

    ``reset_in`` was ``int(window - elapsed)``, which truncates toward zero, so any
    sub-second remainder became ``0``. A client obeying the header retries *immediately*
    into a limiter guaranteed to reject it again, and keeps doing so for the tail of every
    window. Measured before the fix on a 1-second window: ``Retry-After: 0`` at 0.30s,
    0.60s, 0.90s and 0.99s in -- every rejection, not an edge case.
    """

    @pytest.mark.parametrize("elapsed", [0.30, 0.60, 0.90, 0.99])
    def test_rejection_never_reports_zero_seconds(self, elapsed: float) -> None:
        """The defect, at the four points that used to return 0."""
        limiter = RateLimiter(requests_per_minute=1, window_seconds=1)
        limiter.check("k")
        time.sleep(elapsed)

        allowed, _remaining, reset_in = limiter.check("k")

        assert allowed is False
        assert reset_in >= 1, f"Retry-After={reset_in} tells the caller to retry immediately"

    def test_value_rounds_up_rather_than_down(self) -> None:
        """Rounding direction is the fix, not the floor.

        A ``max(1, int(...))`` would pass the arm above while still under-reporting every
        other remainder -- 4.2s left would say 4, waking the caller before the window
        rolls. Only rounding up is correct: waiting a fraction too long costs nothing,
        waking a fraction early reproduces the defect.
        """
        limiter = RateLimiter(requests_per_minute=1, window_seconds=10)
        limiter.check("k")
        time.sleep(0.4)

        _allowed, _remaining, reset_in = limiter.check("k")

        # 9.6s remain; truncation would say 9.
        assert reset_in == 10

    def test_realistic_window_still_reports_the_real_wait(self) -> None:
        """The floor must not flatten every answer to 1."""
        limiter = RateLimiter(requests_per_minute=1, window_seconds=60)
        limiter.check("k")

        _allowed, _remaining, reset_in = limiter.check("k")

        assert reset_in == 60

    def test_allowed_path_agrees_with_the_rejection_path(self) -> None:
        """Both feed headers describing the same instant.

        ``check`` returns ``reset_in`` on the allowed path too, which becomes
        ``X-RateLimit-Reset``. It carried the identical truncation, so the two headers
        could disagree by a second for the same window.
        """
        limiter = RateLimiter(requests_per_minute=5, window_seconds=10)
        _allowed, _remaining, reset_allowed = limiter.check("k")

        assert reset_allowed >= 1
        assert reset_allowed == 10

    @pytest.mark.asyncio
    async def test_429_response_carries_the_corrected_header(self) -> None:
        """End to end: the header a caller actually receives.

        Asserting on ``check`` alone would pass even if the middleware formatted a
        different value into the response.
        """
        limiter = RateLimiter(requests_per_minute=1, window_seconds=1)
        request = _make_request()
        await limiter(request)  # first call consumes the budget
        time.sleep(0.5)

        with pytest.raises(HTTPException) as excinfo:
            await limiter(request)

        assert excinfo.value.status_code == 429
        assert int(excinfo.value.headers["Retry-After"]) >= 1
        assert excinfo.value.headers["Retry-After"] == excinfo.value.headers["X-RateLimit-Reset"]


class TestRateLimiterScopeIsStated:
    """APD-SVCCORE-007 — the per-process limit must be discoverable where it is used.

    The scope is a deliberate constraint, not an oversight, and the register says so. What
    was missing was not enforcement but *disclosure*: the class said "suitable for
    single-process deployments" without saying what happens otherwise, and
    ``build_rate_limiter`` -- the function a consuming service actually calls -- said
    nothing at all. A caller choosing ``requests_per_minute`` had no way to learn that
    four replicas admit four times the configured budget.

    Asserting on docstrings follows the precedent already set in this repo by
    ``tests/test_safe_merge.py``'s ``NetGuaranteeDocTest``: when the guarantee a reader
    relies on *is* the prose, the prose is what has to be pinned.
    """

    def test_class_states_the_multi_replica_consequence(self) -> None:
        doc = RateLimiter.__doc__ or ""

        assert "single-process" in doc
        # The consequence, not just the scope -- "suitable for single-process deployments"
        # alone is what left a reader to infer the rest.
        assert "replica" in doc
        assert "shared store" in doc

    def test_factory_states_it_too(self) -> None:
        """The class docstring is not where a consumer looks; the factory is what they call."""
        doc = build_rate_limiter.__doc__ or ""

        assert "per process" in doc
        assert "replica" in doc

    def test_wording_matches_the_sibling_control_in_this_module(self) -> None:
        """``FailedAuthThrottle`` already documented this properly; the two should agree.

        They are the same mechanism with the same limitation, in the same file. Letting
        one explain it and the other not is how a reader concludes the quiet one does not
        have the problem.
        """
        throttle_doc = FailedAuthThrottle.__doc__ or ""
        limiter_doc = RateLimiter.__doc__ or ""

        for phrase in ("single-process", "replica", "shared store"):
            assert phrase in throttle_doc, f"sibling lost its own disclosure: {phrase}"
            assert phrase in limiter_doc, f"RateLimiter is missing: {phrase}"
