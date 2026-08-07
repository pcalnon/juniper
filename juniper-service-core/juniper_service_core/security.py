"""API security: authentication and rate limiting middleware.

De-cascored port of ``juniper-cascor``'s ``src/api/security.py``. The
:class:`APIKeyAuth` / :class:`RateLimiter` classes and the ``api_key_header``
module global are carried over verbatim; cascor's global-settings singletons
(``get_api_key_auth`` / ``get_rate_limiter`` / ``reset_security_state``) are
replaced with the pure config-injected factories :func:`build_api_key_auth`
and :func:`build_rate_limiter`. The owning service wires these from its own
settings -- there are no module-level singletons and no global settings read.
"""

import hmac
import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyAuth:
    """API key authentication handler.

    Validates requests against configured API keys. When no API keys are
    configured, authentication is disabled (open access mode for development).
    """

    def __init__(self, api_keys: list[str] | None = None) -> None:
        """Initialize with optional list of valid API keys.

        Args:
            api_keys: List of valid API keys. If None or empty, auth is disabled.
                Blank / whitespace-only entries are ignored (same rule as
                :func:`juniper_service_core.auth_posture.real_keys`) so an empty
                secret file cannot enable auth that accepts an empty ``X-API-Key``.
        """
        # Filter blanks before enabling: ``APIKeyAuth([""])`` must stay disabled,
        # not authenticate a missing/empty header via compare_digest("", "").
        self._api_keys: set[str] = {k for k in (api_keys or []) if isinstance(k, str) and k.strip()}
        self._enabled = len(self._api_keys) > 0

    @property
    def enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self._enabled

    def validate(self, api_key: str | None) -> bool:
        """Validate an API key.

        Args:
            api_key: The API key to validate.

        Returns:
            True if auth is disabled or key is valid, False otherwise.
        """
        if not self._enabled:
            return True
        if api_key is None:
            return False
        return any(hmac.compare_digest(api_key, k) for k in self._api_keys)

    async def __call__(self, request: Request) -> str | None:
        """FastAPI dependency for API key validation.

        Args:
            request: The incoming request.

        Returns:
            The validated API key, or None if auth is disabled.

        Raises:
            HTTPException: 401 if auth is enabled and key is invalid/missing.
        """
        api_key = request.headers.get("X-API-Key")

        if not self._enabled:
            return None

        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key. Provide X-API-Key header.",
            )

        if not self.validate(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
            )

        return api_key


class RateLimiter:
    """In-memory fixed-window rate limiter.

    Tracks request counts per key within fixed time windows. Thread-safe
    implementation suitable for single-process deployments.
    """

    # BUG-CC-13: bounded periodic cleanup to prevent unbounded counter growth.
    _CLEANUP_INTERVAL = 100  # Run cleanup every N check() calls.
    _MAX_ENTRIES = 10_000  # Hard cap on _counters entries.

    def __init__(
        self,
        requests_per_minute: int = 60,
        window_seconds: int = 60,
        enabled: bool = True,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per window.
            window_seconds: Window duration in seconds.
            enabled: Whether rate limiting is enabled.
        """
        self._limit = requests_per_minute
        self._window = window_seconds
        self._enabled = enabled
        self._counters: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self._lock = Lock()
        self._request_count_since_cleanup = 0  # BUG-CC-13: tracks calls between prunes.

    def _maybe_cleanup(self) -> None:
        """BUG-CC-13: lazy-prune expired counter buckets. Caller must hold ``_lock``."""
        now = time.time()
        cutoff = now - (2 * self._window)
        expired_keys = [k for k, (_, ts) in self._counters.items() if ts < cutoff]
        for k in expired_keys:
            del self._counters[k]
        if expired_keys:
            logger.debug("RateLimiter: pruned %d expired entries", len(expired_keys))
        if len(self._counters) > self._MAX_ENTRIES:
            # Hard cap: drop oldest entries by window_start timestamp.
            sorted_keys = sorted(self._counters, key=lambda k: self._counters[k][1])
            for k in sorted_keys[: len(self._counters) - self._MAX_ENTRIES]:
                del self._counters[k]

    @property
    def enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self._enabled

    @property
    def limit(self) -> int:
        """Get the rate limit."""
        return self._limit

    @property
    def window(self) -> int:
        """Get the window duration in seconds."""
        return self._window

    def _get_key(self, request: Request, api_key: str | None) -> str:
        """Generate a rate limit key for the request.

        Uses API key if available, otherwise falls back to client IP.

        Args:
            request: The incoming request.
            api_key: The authenticated API key, if any.

        Returns:
            A string key for rate limiting.
        """
        if api_key:
            return f"key:{api_key}"
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def check(self, key: str) -> tuple[bool, int, int]:
        """Check if a request is allowed under rate limit.

        Args:
            key: The rate limit key.

        Returns:
            Tuple of (allowed, remaining, reset_seconds).
        """
        if not self._enabled:
            return (True, self._limit, self._window)

        now = time.time()

        with self._lock:
            # BUG-CC-13: trigger periodic cleanup to bound memory.
            self._request_count_since_cleanup += 1
            if self._request_count_since_cleanup >= self._CLEANUP_INTERVAL:
                self._maybe_cleanup()
                self._request_count_since_cleanup = 0

            count, window_start = self._counters[key]

            if now - window_start >= self._window:
                self._counters[key] = (1, now)
                return (True, self._limit - 1, self._window)

            if count >= self._limit:
                reset_in = int(self._window - (now - window_start))
                return (False, 0, reset_in)

            self._counters[key] = (count + 1, window_start)
            return (True, self._limit - count - 1, int(self._window - (now - window_start)))

    async def __call__(self, request: Request, api_key: str | None = None) -> None:
        """FastAPI dependency for rate limit checking.

        Args:
            request: The incoming request.
            api_key: The authenticated API key, if any.

        Raises:
            HTTPException: 429 if rate limit exceeded.
        """
        if not self._enabled:
            return

        key = self._get_key(request, api_key)
        allowed, remaining, reset_in = self.check(key)

        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset_in

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {reset_in} seconds.",
                headers={
                    "X-RateLimit-Limit": str(self._limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_in),
                    "Retry-After": str(reset_in),
                },
            )

    def reset(self) -> None:
        """Reset all rate limit counters. Useful for testing."""
        with self._lock:
            self._counters.clear()
            self._request_count_since_cleanup = 0


def build_api_key_auth(api_keys: list[str] | None = None) -> APIKeyAuth:
    """Build an :class:`APIKeyAuth` from injected config.

    Pure factory: no global settings read, no module-level singleton. The
    owning service passes its own configured key list.

    Args:
        api_keys: Valid API keys. If None or empty, the returned handler has
            authentication disabled (open access).

    Returns:
        A configured :class:`APIKeyAuth` instance.
    """
    return APIKeyAuth(api_keys)


def build_rate_limiter(
    requests_per_minute: int = 60,
    window_seconds: int = 60,
    enabled: bool = True,
) -> RateLimiter:
    """Build a :class:`RateLimiter` from injected config.

    Pure factory: no global settings read, no module-level singleton. The
    owning service passes its own configured limits.

    Args:
        requests_per_minute: Maximum requests allowed per window.
        window_seconds: Window duration in seconds.
        enabled: Whether rate limiting is enabled.

    Returns:
        A configured :class:`RateLimiter` instance.
    """
    return RateLimiter(
        requests_per_minute=requests_per_minute,
        window_seconds=window_seconds,
        enabled=enabled,
    )
