"""Security hardening for the worker subsystem (WS-2 / OUT-11 T2 step 3a).

The de-cascored core of cascor's ``api/workers/security.py``. Provides:

- :class:`TLSConfig` -- mTLS enforcement for worker WebSocket connections (CLEAN, verbatim).
- :class:`ConnectionRateLimiter` -- token-bucket per-source connection-attempt limiting (CLEAN).
- :class:`AnomalyDetector` -- suspicious-result detection over a generic bounded quality **score**.

cascor's detector was framed on the cascade ``correlation`` scalar; this generic version operates on
an opaque ``score`` in ``[0, 1]`` (any model's result-quality metric -- correlation for cascor, an
``r2`` clamp for a regressor, an accuracy for a classifier), so the checks (suspiciously fast,
perfect score, stale score, duplicate scores) carry no cascade assumption. cascor's
``cascor_constants`` imports are replaced with local module constants (the de-cascor pattern).

Pure stdlib (+ :mod:`ssl`) -- no third-party import, safe on the dependency-free import path.
"""

from __future__ import annotations

import hashlib
import logging
import ssl
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

__all__ = ["TLSConfig", "ConnectionRateLimiter", "AnomalyDetector"]

logger = logging.getLogger("juniper_service_core.workers.security")

# De-cascored local constants (were cascor_constants.constants_api).
#: Default minimum TLS version when mTLS is enabled.
_TLS_MIN_VERSION_DEFAULT: str = "TLSv1.2"
#: How often (seconds) the rate limiter prunes stale per-source buckets.
_RATE_LIMITER_CLEANUP_INTERVAL: float = 300.0
#: A |score| below this is treated as "stale" (never improving from zero).
_ANOMALY_STALE_SCORE_THRESHOLD: float = 0.001
#: How many recent results to retain per worker for duplicate-score detection.
_ANOMALY_DUPLICATE_WINDOW: int = 10


# ---------------------------------------------------------------------------
# mTLS Configuration
# ---------------------------------------------------------------------------


@dataclass
class TLSConfig:
    """TLS/mTLS configuration for the worker WebSocket endpoint."""

    enabled: bool = False
    cert_file: str | None = None
    key_file: str | None = None
    ca_file: str | None = None
    require_client_cert: bool = False
    min_tls_version: str = _TLS_MIN_VERSION_DEFAULT

    def build_ssl_context(self) -> ssl.SSLContext | None:
        """Build a server-side SSL context, or ``None`` if TLS is disabled.

        Raises:
            FileNotFoundError: If cert/key/CA files don't exist.
            ssl.SSLError: If cert/key are invalid.
        """
        if not self.enabled:
            return None

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        if self.min_tls_version == "TLSv1.3":
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        else:
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2

        # CA for client-cert verification (mTLS) -- check before loading the server cert.
        if self.require_client_cert and self.ca_file:
            ca_path = Path(self.ca_file)
            if not ca_path.exists():
                raise FileNotFoundError(f"CA cert not found: {self.ca_file}")
            ctx.load_verify_locations(cafile=str(ca_path))
            ctx.verify_mode = ssl.CERT_REQUIRED
            logger.info("mTLS enabled: requiring client certificates (CA: %s)", self.ca_file)
        elif self.require_client_cert:
            ctx.verify_mode = ssl.CERT_REQUIRED
            logger.warning("mTLS: require_client_cert=True but no CA file -- using system trust store")

        if self.cert_file and self.key_file:
            cert_path = Path(self.cert_file)
            key_path = Path(self.key_file)
            if not cert_path.exists():
                raise FileNotFoundError(f"TLS cert not found: {self.cert_file}")
            if not key_path.exists():
                raise FileNotFoundError(f"TLS key not found: {self.key_file}")
            ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
            logger.info("Loaded server TLS certificate: %s", self.cert_file)
        elif self.cert_file or self.key_file:
            # Half-config (cert XOR key) must fail closed -- a bare SSLContext with neither
            # chain nor key is a silent misconfig that looks "TLS enabled" to callers.
            raise ValueError(
                "TLS enabled with incomplete cert/key pair: both cert_file and key_file are required "
                f"(cert_file={self.cert_file!r}, key_file={self.key_file!r})"
            )

        return ctx


# ---------------------------------------------------------------------------
# Connection Rate Limiter
# ---------------------------------------------------------------------------


class ConnectionRateLimiter:
    """Token-bucket rate limiter for WebSocket connection attempts.

    Tracks connection attempts per source identifier (IP address or worker_id) and rejects
    attempts that exceed the configured rate.
    """

    def __init__(
        self,
        max_connections_per_minute: int = 10,
        burst_size: int = 3,
        cleanup_interval: float = _RATE_LIMITER_CLEANUP_INTERVAL,
    ) -> None:
        self._max_rate = max_connections_per_minute
        self._burst = burst_size
        self._cleanup_interval = cleanup_interval
        self._buckets: dict[str, _TokenBucket] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
        logger.info("Rate limiter initialized: %d/min, burst=%d", max_connections_per_minute, burst_size)

    def allow(self, source_id: str) -> bool:
        """Whether a connection attempt from ``source_id`` is allowed (``False`` if rate-limited)."""
        now = time.time()
        with self._lock:
            self._maybe_cleanup(now)
            if source_id not in self._buckets:
                self._buckets[source_id] = _TokenBucket(rate=self._max_rate / 60.0, burst=self._burst)
            bucket = self._buckets[source_id]
            allowed = bucket.consume(now)
            if not allowed:
                logger.warning("Rate limited connection from %s", source_id)
            return allowed

    def _maybe_cleanup(self, now: float) -> None:
        """Remove stale buckets to prevent unbounded memory growth. Caller holds the lock."""
        if now - self._last_cleanup < self._cleanup_interval:
            return
        stale_keys = [k for k, b in self._buckets.items() if now - b.last_access > self._cleanup_interval]
        for k in stale_keys:
            del self._buckets[k]
        if stale_keys:
            logger.debug("Rate limiter cleanup: removed %d stale entries", len(stale_keys))
        self._last_cleanup = now


@dataclass
class _TokenBucket:
    """Simple token bucket for rate limiting."""

    rate: float  # tokens per second
    burst: int
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.tokens = float(self.burst)

    def consume(self, now: float) -> bool:
        """Try to consume one token. Returns ``True`` if successful."""
        elapsed = now - self.last_refill
        self.tokens = min(float(self.burst), self.tokens + elapsed * self.rate)
        self.last_refill = now
        self.last_access = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


# ---------------------------------------------------------------------------
# Anomaly Detection
# ---------------------------------------------------------------------------


class AnomalyDetector:
    """Detects suspicious patterns in result quality from remote workers.

    Operates on a generic bounded quality ``score`` in ``[0, 1]`` (cascor's ``correlation``, a
    regressor's clamped ``r2``, a classifier's ``accuracy``). Monitors:

    - Results that arrive suspiciously fast (below ``min_training_time``).
    - Scores that are consistently too perfect (above ``perfect_score_threshold``).
    - Scores that never improve from zero (below ``stale_score_threshold``).
    - Identical scores repeated across different tasks (possible replay / stuck worker).

    The default thresholds assume a ``[0, 1]`` score; a service whose score has a different range
    configures them at construction.
    """

    def __init__(
        self,
        min_training_time: float = 0.1,
        perfect_score_threshold: float = 0.999,
        stale_score_threshold: float = _ANOMALY_STALE_SCORE_THRESHOLD,
        duplicate_window: int = _ANOMALY_DUPLICATE_WINDOW,
    ) -> None:
        self._min_training_time = min_training_time
        self._perfect_threshold = perfect_score_threshold
        self._stale_threshold = stale_score_threshold
        self._duplicate_window = duplicate_window
        self._worker_history: dict[str, list[_ResultRecord]] = {}
        self._lock = Lock()

    def check_result(self, worker_id: str, score: float, training_duration: float, task_id: str) -> list[str]:
        """Check a worker result for anomalies. Returns a list of anomaly descriptions (empty if clean).

        Args:
            worker_id: ID of the worker that produced the result.
            score: The result-quality scalar (expected in ``[0, 1]`` for the default thresholds).
            training_duration: How long the worker took (seconds).
            task_id: The task identifier.
        """
        anomalies = []

        if training_duration < self._min_training_time:
            anomalies.append(f"suspiciously_fast: {training_duration:.3f}s (min={self._min_training_time}s)")

        if score > self._perfect_threshold:
            anomalies.append(f"perfect_score: {score:.6f}")

        if abs(score) < self._stale_threshold:
            anomalies.append(f"stale_score: {score:.6f}")

        with self._lock:
            history = self._worker_history.setdefault(worker_id, [])
            history.append(_ResultRecord(task_id=task_id, score=score, duration=training_duration, timestamp=time.time()))
            if len(history) > self._duplicate_window:
                history[:] = history[-self._duplicate_window :]
            # Duplicate-score detection (possible replay attack / stuck worker).
            if len(history) >= 3:
                recent_scores = [r.score for r in history[-self._duplicate_window :]]
                score_hash = hashlib.sha256(str(sorted(recent_scores)).encode()).hexdigest()[:8]
                unique = len({f"{s:.6f}" for s in recent_scores})
                if unique == 1 and len(recent_scores) >= 3:
                    anomalies.append(f"duplicate_scores: {unique}/{len(recent_scores)} unique (hash={score_hash})")

        if anomalies:
            logger.warning("ANOMALY: worker=%s task=%s anomalies=%s", worker_id, task_id, anomalies)

        return anomalies

    def get_worker_stats(self, worker_id: str) -> dict[str, Any]:
        """Get anomaly statistics for a worker."""
        with self._lock:
            history = self._worker_history.get(worker_id, [])
            if not history:
                return {"total_results": 0}
            scores = [r.score for r in history]
            durations = [r.duration for r in history]
            return {
                "total_results": len(history),
                "avg_score": sum(scores) / len(scores),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_score": max(scores),
            }

    def clear_worker(self, worker_id: str) -> None:
        """Clear history for a deregistered worker."""
        with self._lock:
            self._worker_history.pop(worker_id, None)


@dataclass
class _ResultRecord:
    """A single worker result record for anomaly tracking."""

    task_id: str
    score: float
    duration: float
    timestamp: float
