"""Supplementary coverage for the top-level modules of ``juniper_service_core``.

Targets the error / timeout / fallback branches that the existing per-module
suites (``test_launcher.py`` / ``test_security.py`` / ``test_middleware.py``)
leave uncovered, without duplicating their happy-path assertions:

* ``launcher.py`` — the SIGKILL-on-timeout terminate path, the log-close error
  swallow, the atexit cleanup registry, and every ``start_service`` failure
  branch (env overrides, log-open ``OSError``, ``Popen`` raising, and the two
  unhealthy outcomes). Subprocess + health-poll are driven against in-process
  fakes: no real processes, no sleeps, fully deterministic.
* ``security.py`` — the ``RateLimiter`` cleanup internals (expired-entry prune +
  hard-cap eviction), the api-key rate-limit key, the periodic-cleanup trigger,
  and the async dependency's disabled + 429 branches.
* ``middleware.py`` — the ``RequestBodyLimitMiddleware`` chunked / no-
  Content-Length streaming branch (accept-within-cap + reject-oversized), driven
  with a generator request body so httpx omits ``Content-Length``.
"""

from __future__ import annotations

import asyncio
import subprocess
import time

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from juniper_service_core import launcher
from juniper_service_core.launcher import ManagedService, start_service
from juniper_service_core.middleware import RequestBodyLimitMiddleware
from juniper_service_core.security import RateLimiter

# =====================================================================
# launcher.py
# =====================================================================


class _FakeProc:
    """Minimal ``subprocess.Popen`` stand-in for launcher tests.

    ``poll_returns`` of ``None`` models a still-running process; any other value
    models an exited process with that return code.
    """

    def __init__(self, poll_returns=None, pid=4321, returncode=0):
        self._poll = poll_returns
        self.pid = pid
        self.returncode = returncode
        self.terminate_calls = 0
        self.kill_calls = 0
        self.wait_calls = 0

    def poll(self):
        return self._poll

    def terminate(self):
        self.terminate_calls += 1

    def kill(self):
        self.kill_calls += 1

    def wait(self, timeout=None):
        self.wait_calls += 1
        return self.returncode


@pytest.fixture
def registry_guard():
    """Snapshot, clear, then restore ``launcher._active_services`` around a test."""
    saved = list(launcher._active_services)
    launcher._active_services.clear()
    try:
        yield launcher._active_services
    finally:
        launcher._active_services[:] = saved


async def _health_true(*args, **kwargs):
    return True


async def _health_false(*args, **kwargs):
    return False


def test_terminate_sends_sigkill_on_wait_timeout():
    """Graceful ``wait`` timing out escalates to ``kill()`` + a second ``wait``."""

    class _TimeoutProc(_FakeProc):
        def wait(self, timeout=None):
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired(cmd="x", timeout=timeout)
            return -9

    proc = _TimeoutProc(poll_returns=None, pid=222)
    svc = ManagedService("stubborn", proc)
    svc.terminate(timeout=0.01)
    assert proc.terminate_calls == 1
    assert proc.kill_calls == 1
    assert proc.wait_calls == 2


def test_close_log_swallows_close_error_on_already_stopped():
    """An already-stopped service still closes its log handle; a raising close is swallowed."""

    class _BadHandle:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True
            raise RuntimeError("close boom")

    handle = _BadHandle()
    svc = ManagedService("done", _FakeProc(poll_returns=0), log_handle=handle)
    svc.terminate()  # must not raise despite the close() error
    assert handle.closed is True
    # Second call takes the already-cleared handle path (no-op, still no raise).
    svc.terminate()


def test_cleanup_at_exit_swallows_terminate_errors(registry_guard):
    """``_cleanup_at_exit`` terminates every registered service and swallows failures."""

    class _RaisingProc(_FakeProc):
        def poll(self):
            raise RuntimeError("poll boom")

    class _Handle:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    handle = _Handle()
    good_svc = ManagedService("good", _FakeProc(poll_returns=0), log_handle=handle)
    bad_svc = ManagedService("bad", _RaisingProc())
    registry_guard.extend([good_svc, bad_svc])

    launcher._cleanup_at_exit()  # must not raise even though bad_svc.terminate() throws

    assert handle.closed is True  # good_svc was processed before bad_svc raised


def test_start_service_applies_env_overrides_when_healthy(monkeypatch, tmp_path, registry_guard):
    monkeypatch.setenv("JUNIPER_SERVICE_LOG_DIR", str(tmp_path))
    captured: dict = {}

    def fake_popen(cmd_parts, **kwargs):
        captured["cmd"] = cmd_parts
        captured["env"] = kwargs.get("env")
        return _FakeProc(poll_returns=None, pid=999)

    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(launcher, "wait_for_health", _health_true)

    svc = asyncio.run(
        start_service(
            "svc-a",
            "run --flag value",
            "http://127.0.0.1:9/health",
            env_overrides={"JUNIPER_TEST_TOKEN": "abc"},
            health_timeout=1,
        )
    )
    try:
        assert svc is not None
        assert svc in registry_guard
        assert captured["cmd"] == ["run", "--flag", "value"]
        assert captured["env"]["JUNIPER_TEST_TOKEN"] == "abc"
        assert (tmp_path / "subprocess_svc_a.log").exists()
    finally:
        if svc is not None:
            svc.terminate()  # close the real log handle to avoid a leaked fd


def test_start_service_log_open_oserror_falls_back(monkeypatch, tmp_path, registry_guard):
    monkeypatch.setenv("JUNIPER_SERVICE_LOG_DIR", str(tmp_path))

    def raise_oserror(*args, **kwargs):
        raise OSError("no space left on device")

    # launcher uses a bare ``open`` builtin; a module-level attribute shadows it.
    monkeypatch.setattr(launcher, "open", raise_oserror, raising=False)
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: _FakeProc(poll_returns=None))
    monkeypatch.setattr(launcher, "wait_for_health", _health_true)

    svc = asyncio.run(start_service("svc-b", "run", "http://127.0.0.1:9/health", health_timeout=1))
    assert svc is not None
    assert svc in registry_guard


def test_start_service_returns_none_when_popen_raises(monkeypatch, tmp_path, registry_guard):
    monkeypatch.setenv("JUNIPER_SERVICE_LOG_DIR", str(tmp_path))

    def raise_popen(*args, **kwargs):
        raise RuntimeError("cannot exec")

    monkeypatch.setattr(launcher.subprocess, "Popen", raise_popen)
    monkeypatch.setattr(launcher, "wait_for_health", _health_true)

    svc = asyncio.run(start_service("svc-c", "run", "http://127.0.0.1:9/health", health_timeout=1))
    assert svc is None
    assert registry_guard == []  # never registered


def test_start_service_unhealthy_but_running_terminates(monkeypatch, tmp_path, registry_guard):
    monkeypatch.setenv("JUNIPER_SERVICE_LOG_DIR", str(tmp_path))
    proc = _FakeProc(poll_returns=None, pid=555)  # is_running() -> True
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(launcher, "wait_for_health", _health_false)

    svc = asyncio.run(start_service("svc-d", "run", "http://127.0.0.1:9/health", health_timeout=1))
    assert svc is None
    assert registry_guard == []  # removed after the failed health check
    assert proc.terminate_calls == 1


def test_start_service_unhealthy_and_exited(monkeypatch, tmp_path, registry_guard):
    monkeypatch.setenv("JUNIPER_SERVICE_LOG_DIR", str(tmp_path))
    proc = _FakeProc(poll_returns=1, returncode=1)  # exited prematurely
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(launcher, "wait_for_health", _health_false)

    svc = asyncio.run(start_service("svc-e", "run", "http://127.0.0.1:9/health", health_timeout=1))
    assert svc is None
    assert registry_guard == []


# =====================================================================
# security.py
# =====================================================================


def _bare_request(headers=None, client=("testclient", 50000)) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw,
        "client": client,
    }
    return Request(scope)


def test_maybe_cleanup_prunes_expired_entries():
    limiter = RateLimiter(requests_per_minute=5, window_seconds=1)
    now = time.time()
    limiter._counters["stale"] = (3, now - 1000)  # ts < now - 2*window -> expired
    limiter._counters["fresh"] = (1, now)
    limiter._maybe_cleanup()
    assert "stale" not in limiter._counters
    assert "fresh" in limiter._counters


def test_maybe_cleanup_enforces_hard_cap():
    limiter = RateLimiter(requests_per_minute=5, window_seconds=60)
    limiter._MAX_ENTRIES = 1  # shrink the cap so the eviction branch runs
    now = time.time()
    # All fresh (none expired) so pruning is driven purely by the hard cap.
    limiter._counters["a"] = (1, now)
    limiter._counters["b"] = (1, now + 1)
    limiter._counters["c"] = (1, now + 2)
    limiter._maybe_cleanup()
    assert len(limiter._counters) == 1
    assert "c" in limiter._counters  # oldest-by-window_start dropped first


def test_get_key_prefers_api_key_over_ip():
    limiter = RateLimiter()
    assert limiter._get_key(_bare_request(), "secret") == "key:secret"


def test_get_key_falls_back_to_ip_unknown_when_client_missing():
    # ASGI scopes without a client (some proxies / internal calls) must not crash;
    # they share the ``ip:unknown`` bucket so unauthenticated traffic still rate-limits.
    limiter = RateLimiter()
    req = _bare_request(client=None)
    assert limiter._get_key(req, None) == "ip:unknown"
    assert limiter._get_key(req, "secret") == "key:secret"


def test_check_triggers_periodic_cleanup():
    limiter = RateLimiter(requests_per_minute=5)
    limiter._CLEANUP_INTERVAL = 1  # cleanup fires on the very next check()
    limiter.check("k")
    assert limiter._request_count_since_cleanup == 0


@pytest.mark.asyncio
async def test_rate_limiter_call_returns_when_disabled():
    limiter = RateLimiter(enabled=False)
    assert await limiter(_bare_request()) is None


@pytest.mark.asyncio
async def test_rate_limiter_call_raises_429_when_exceeded():
    limiter = RateLimiter(requests_per_minute=1)
    req = _bare_request()
    await limiter(req)  # first request consumes the single slot
    with pytest.raises(HTTPException) as exc_info:
        await limiter(req)  # second exceeds the limit
    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["X-RateLimit-Limit"] == "1"
    assert exc_info.value.headers["Retry-After"]


# =====================================================================
# middleware.py
# =====================================================================


def _echo_app() -> FastAPI:
    app = FastAPI()

    @app.post("/v1/echo")
    async def echo():
        return {"ok": True}

    return app


def _chunked(payload: bytes):
    """One-shot generator body so httpx sends a chunked request (no Content-Length)."""

    def _gen():
        yield payload

    return _gen()


def test_body_limit_streams_within_cap_when_no_content_length():
    app = _echo_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=100)
    client = TestClient(app)
    response = client.post("/v1/echo", content=_chunked(b"x" * 20))
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_body_limit_rejects_oversized_chunked_stream():
    app = _echo_app()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=10)
    client = TestClient(app)
    response = client.post("/v1/echo", content=_chunked(b"x" * 50))
    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"
