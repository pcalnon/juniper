"""Unit coverage for the control-path security primitives (C-4a).

Exercises :func:`validate_control_origin` (allow / fail-closed / disallowed), the
:class:`LeakyBucket` ``retry_after`` full-bucket branch, and the :class:`HandshakeCooldown`
rejection / block / expiry / stale-prune paths directly (pure stdlib, no transport).
"""

from __future__ import annotations

import time
import types

from juniper_service_core.websocket.control_security import HandshakeCooldown, LeakyBucket, validate_control_origin


def _origin_ws(origin: str | None) -> types.SimpleNamespace:
    headers = {} if origin is None else {"origin": origin}
    return types.SimpleNamespace(headers=headers)


def test_validate_origin_rejects_missing_origin() -> None:
    assert validate_control_origin(_origin_ws(None), ["https://app.example"]) is False


def test_validate_origin_allows_normalized_match() -> None:
    ws = _origin_ws("HTTPS://App.Example/")
    assert validate_control_origin(ws, ["https://app.example"]) is True


def test_validate_origin_rejects_disallowed() -> None:
    ws = _origin_ws("https://evil.example")
    assert validate_control_origin(ws, ["https://good.example"]) is False


def test_leaky_bucket_retry_after_zero_when_full() -> None:
    bucket = LeakyBucket(capacity=5, refill_rate=5.0)
    assert bucket.retry_after == 0.0


def test_leaky_bucket_consumes_then_reports_deficit() -> None:
    bucket = LeakyBucket(capacity=1, refill_rate=1.0)
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False
    assert bucket.retry_after > 0.0


def test_leaky_bucket_retry_after_zero_refill_does_not_divide_by_zero() -> None:
    # control_stream wires ``refill_rate=float(rate_limit)``; rate_limit=0 used to
    # ZeroDivisionError on the rate-limited ack path instead of returning retry_after.
    bucket = LeakyBucket(capacity=0, refill_rate=0.0)
    assert bucket.try_acquire() is False
    assert bucket.retry_after == 3600.0


def test_handshake_cooldown_records_and_blocks() -> None:
    cooldown = HandshakeCooldown(max_rejections=3, window_sec=60, block_sec=300)
    assert cooldown.record_rejection("1.2.3.4") is False
    assert cooldown.record_rejection("1.2.3.4") is False
    assert cooldown.record_rejection("1.2.3.4") is True  # threshold reached -> block
    assert cooldown.is_blocked("1.2.3.4") is True
    assert cooldown.get_block_remaining("1.2.3.4") is not None


def test_handshake_cooldown_reports_none_for_unblocked_ip() -> None:
    cooldown = HandshakeCooldown()
    assert cooldown.is_blocked("9.9.9.9") is False
    assert cooldown.get_block_remaining("9.9.9.9") is None


def test_handshake_cooldown_block_expires() -> None:
    cooldown = HandshakeCooldown(max_rejections=1, window_sec=60, block_sec=0)
    assert cooldown.record_rejection("5.5.5.5") is True  # block for 0s -> already expired
    assert cooldown.is_blocked("5.5.5.5") is False  # expiry deletes the block entry


def test_handshake_cooldown_get_block_remaining_expired() -> None:
    cooldown = HandshakeCooldown(max_rejections=1, window_sec=60, block_sec=0)
    assert cooldown.record_rejection("6.6.6.6") is True
    assert cooldown.get_block_remaining("6.6.6.6") is None  # remaining <= 0 -> deletes + None


def test_handshake_cooldown_prunes_stale_histories() -> None:
    cooldown = HandshakeCooldown(max_rejections=100, window_sec=60)
    stale = time.monotonic() - 10_000  # far outside 2 * window
    cooldown._rejections["1.1.1.1"] = [stale]
    cooldown._total_rejections_since_cleanup = HandshakeCooldown._CLEANUP_EVERY_N - 1
    # The next rejection ticks the counter to the cleanup threshold -> full stale prune.
    assert cooldown.record_rejection("2.2.2.2") is False
    assert "1.1.1.1" not in cooldown._rejections
