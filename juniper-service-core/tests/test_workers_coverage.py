"""Tail-coverage tests for the WS-2 / OUT-11 T2 worker-pool submodule (work-unit C-4b).

Companion to :mod:`tests.test_t2_workers` and :mod:`tests.test_t2_worker_coordinator`; these
exercise the residual error / early-exit / config-validation branches those suites leave uncovered
so ``juniper_service_core/workers`` clears its pooled statement-coverage gate. Everything here is
REAL and deterministic -- no wall-clock races: the coordinator's background health monitor is driven
by injecting a one-shot stop-event stand-in (so exactly one loop body runs) or by starting the real
thread with a long check interval and stopping it immediately; the stale-worker re-check branches are
driven with a scripted registry stand-in; and the rate-limiter cleanup / anomaly-window branches are
driven by back-dating timestamps rather than sleeping.

The Prometheus collector tests mirror :mod:`tests.test_t2_workers` -- each constructs a fresh
:class:`WorkerRegistryCollector` and inspects the metric families yielded by ``collect()`` directly,
which never registers with (and so never pollutes) the global default ``prometheus_client`` registry.

The mTLS tests write a self-signed, CA-capable *certificate* (embedded below, 100-year validity,
loadable through the stdlib :mod:`ssl` module alone -- no third-party dependency) to a ``tmp_path`` so
:meth:`TLSConfig.build_ssl_context` exercises ``load_verify_locations`` plus the CA / cert / key
file-existence guards. The server-side ``load_cert_chain`` success path is intentionally *not*
exercised here: it would require committing a private key to the repo, which the ``detect-private-key``
pre-commit hook (correctly) blocks, and covering it is unnecessary -- ``workers/security.py`` and the
``workers`` sub-module both stay above their C-4 coverage bars without it (see the PR notes).
"""

from __future__ import annotations

import ssl
import time
from types import SimpleNamespace

import pytest

from juniper_service_core.workers import (
    AnomalyDetector,
    ConnectionRateLimiter,
    ParsedResult,
    TLSConfig,
    WorkerCoordinator,
    WorkerRegistration,
    WorkerRegistry,
    WorkerRegistryCollector,
    WorkerTaskProtocol,
)

# A self-signed, CA-capable certificate (100-year validity), embedded so the mTLS tests need no
# cert-generation dependency at runtime -- the stdlib ``ssl`` module loads it directly via
# ``load_verify_locations``. No private key is committed (see the module docstring / PR notes).
_TEST_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDMTCCAhmgAwIBAgIUJUM8E7QsKak8cxdobH2xg4bmi+owDQYJKoZIhvcNAQEL
BQAwJzElMCMGA1UEAwwcanVuaXBlci1zZXJ2aWNlLWNvcmUtdGVzdC1jYTAgFw0y
NjA3MDIwNjQyMjhaGA8yMTI2MDYwODA2NDIyOFowJzElMCMGA1UEAwwcanVuaXBl
ci1zZXJ2aWNlLWNvcmUtdGVzdC1jYTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCC
AQoCggEBALiSTLDOIAxO6FcXGOI2MKMs+yUjJJV9ziUAVpv1uY/GK9YXsd3tXNg3
P2VtcT42J0m5Mke6gi2Zj0aMHVvBGic9ppOqj1QefyVMf+To3sUGU3hu3qEp5fW1
Om6bQUIugOF1Jtc+hP3bk/2j+2L3Zg2OYsJiqNHVhn5CA2TTA/9nhdPK37804C2U
IWo3Rk0v1UACKXKXG8+BYr7XPgInHgrAi/RPPeA5VsKZKfrDIy5lVlw1zNDwtzWb
uulFXcXztMJEtjtE9qhLPmmwpVf//wHXywmVULNT1TDmggo+LiOjPYkT7UeiQYVO
a/erIKEWI6o6XVxuGl77iVVv3auT1y8CAwEAAaNTMFEwHQYDVR0OBBYEFFC4o2Zc
TvbvO88LAMcYa3r7PMrmMB8GA1UdIwQYMBaAFFC4o2ZcTvbvO88LAMcYa3r7PMrm
MA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAFeFUxkULfZRbzvd
SKTPRqm2fbGVB8JaTwTtc9iKs9wFQ0F/5NCw+GMjfXtdt2ylOV6tjHPUQScaJZ1h
DoPOMpExYLnbloxojvgiWqJVt8+0mhUGQ0xjsk1gDr8AD7LNGfPW6KDfCV92tdtc
Q4tGT4aKQqBZwoxvjtz+UOUPa3Xm+0bJmEiwcSUfnd6O26SD4pX9J3l0Og3oLN1t
sMDLkPydv5s9433ny4Vv0tua+F5MN31u4kr4/na3HGyuzyVGAr8REJ83NDubwspm
7wfOoKOdmtW8sj1cj9Ecb6oic0tUtRZOrmucJ5GbRd964wsqmmvGmKljejtd8Bra
1Sg7Kws=
-----END CERTIFICATE-----
"""


# ======================================================================================
# Test doubles
# ======================================================================================


class _CoverageProtocol:
    """A trivial :class:`WorkerTaskProtocol` (JSON envelope, no binary frames) for coordinator tests.

    ``parse_result`` reflects ``score`` / ``duration`` from the message so the anomaly hook can be
    driven, and rejects (returns ``None``) when ``msg['ok']`` is ``False``.
    """

    def build_assignment(self, task):
        return ({"type": "task_assign", "task_id": task.task_id, "payload": task.payload}, [])

    def result_attachments(self, msg):
        return list(msg.get("attachments", []))

    def parse_result(self, worker_id, msg, frames):
        if not msg.get("ok", True):
            return None
        return ParsedResult(
            success=msg.get("success", True),
            result={"task_id": msg.get("task_id")},
            score=msg.get("score"),
            duration=msg.get("duration"),
        )


class _FlaggingDetector:
    """An anomaly detector that always reports one anomaly (drives the coordinator's warning branch)."""

    def check_result(self, worker_id, score, training_duration, task_id):
        return [f"perfect_score: {score:.6f}"]


class _OneShotStop:
    """A stop-event stand-in: the first ``wait()`` returns ``False`` (run one loop body), then ``True``.

    Lets :meth:`WorkerCoordinator._health_monitor_loop` execute exactly one deterministic iteration
    before exiting -- no wall-clock dependency.
    """

    def __init__(self) -> None:
        self.calls = 0

    def wait(self, timeout=None) -> bool:
        self.calls += 1
        return self.calls > 1


class _StaleCheckRegistry:
    """Scripted registry stand-in for :meth:`WorkerCoordinator._check_stale_workers`.

    ``get_stale_workers`` returns a fixed snapshot list; ``get`` resolves through ``get_map`` (so a
    worker can appear stale in the snapshot yet resolve to ``None`` -- vanished -- or to a live
    registration -- recovered -- on the re-check). Records deregistrations so the tests can assert
    the branch that skips them.
    """

    heartbeat_timeout = 30.0

    def __init__(self, stale, get_map) -> None:
        self._stale = stale
        self._get_map = get_map
        self.deregistered: list[str] = []

    def get_stale_workers(self):
        return list(self._stale)

    def get(self, worker_id):
        return self._get_map.get(worker_id)

    def deregister(self, worker_id):
        self.deregistered.append(worker_id)
        return None


class _BoomSnapshotRegistry:
    """Registry stand-in whose ``snapshot_for_metrics`` raises (collector must degrade gracefully)."""

    def snapshot_for_metrics(self):
        raise RuntimeError("snapshot boom")


class _BadSnapshotRegistry:
    """Registry stand-in returning a malformed snapshot (missing keys) -- per-snapshot skip guard."""

    def snapshot_for_metrics(self):
        return [{"worker_id": "w1"}]  # missing 'last_heartbeat' / optional fields


# ======================================================================================
# coordinator: WorkerTaskProtocol default bodies
# ======================================================================================


def test_worker_task_protocol_default_bodies_return_none() -> None:
    """The Protocol's default (``pass``) method bodies are no-ops returning ``None`` (invoked directly)."""
    sentinel = object()
    assert WorkerTaskProtocol.build_assignment(sentinel, None) is None
    assert WorkerTaskProtocol.result_attachments(sentinel, {}) is None
    assert WorkerTaskProtocol.parse_result(sentinel, "w1", {}, {}) is None


# ======================================================================================
# coordinator: anomaly_detector property + setter
# ======================================================================================


def test_anomaly_detector_property_get_and_set() -> None:
    coord = WorkerCoordinator(WorkerRegistry(), _CoverageProtocol())
    assert coord.anomaly_detector is None  # getter, default None
    sentinel = object()
    coord.anomaly_detector = sentinel  # setter
    assert coord.anomaly_detector is sentinel


# ======================================================================================
# coordinator: health-monitor thread lifecycle
# ======================================================================================


def test_start_monitor_idempotent_and_stop_joins() -> None:
    # A long check interval keeps the loop blocked in wait() (no spin); stop_monitor wakes it at once.
    coord = WorkerCoordinator(WorkerRegistry(), _CoverageProtocol(), health_check_interval=3600.0)
    coord.start_monitor()  # creates + starts the daemon thread
    try:
        assert coord._monitor_thread is not None
        assert coord._monitor_thread.is_alive()
        coord.start_monitor()  # already running -> early-return branch
        assert coord._monitor_thread.is_alive()
    finally:
        coord.stop_monitor()  # sets the stop event, joins, clears the handle
    assert coord._monitor_thread is None


def test_health_monitor_loop_runs_one_iteration_then_exits() -> None:
    coord = WorkerCoordinator(WorkerRegistry(), _CoverageProtocol())
    stop = _OneShotStop()
    coord._monitor_stop = stop  # deterministic: exactly one loop body, then exit
    coord._health_monitor_loop()  # runs the loop body once (stale + timeout sweeps over empty state)
    assert stop.calls == 2  # wait() -> False (body), then wait() -> True (exit)


# ======================================================================================
# coordinator: get_next_assignment inconsistent-state guard
# ======================================================================================


def test_get_next_assignment_none_when_task_missing_from_pending() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _CoverageProtocol())
    # An unassigned id with no matching PendingTask (inconsistent state) -> guarded None return.
    coord._unassigned_tasks.append("orphan-task-id")
    assert coord.get_next_assignment("w1") is None
    assert reg.get("w1").idle is True  # nothing was assigned


# ======================================================================================
# coordinator: anomaly-warning branch on submit_result
# ======================================================================================


def test_submit_result_logs_anomaly_but_still_accepts() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, _CoverageProtocol(), anomaly_detector=_FlaggingDetector())
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")
    # score present + detector returns a non-empty anomaly list -> warning branch runs; result accepted.
    assert coord.submit_result("w1", {"task_id": tid, "success": True, "score": 0.9999, "duration": 2.0}, {}) is True
    results = coord.collect_results(timeout=0.5)
    assert len(results) == 1 and results[0]["task_id"] == tid


# ======================================================================================
# coordinator: stale-worker re-check branches (vanished / recovered)
# ======================================================================================


def test_check_stale_workers_skips_worker_gone_on_recheck() -> None:
    snap = SimpleNamespace(worker_id="w1", active_task_id=None)
    reg = _StaleCheckRegistry(stale=[snap], get_map={})  # get() -> None: worker vanished
    coord = WorkerCoordinator(reg, _CoverageProtocol())
    coord._check_stale_workers()  # current is None -> continue (no deregister)
    assert reg.deregistered == []


def test_check_stale_workers_skips_recovered_worker() -> None:
    # Appears stale in the snapshot but is alive on the re-check (a heartbeat arrived meanwhile).
    alive = WorkerRegistration(worker_id="w1")  # fresh last_heartbeat -> is_alive() True
    snap = SimpleNamespace(worker_id="w1", active_task_id=None)
    reg = _StaleCheckRegistry(stale=[snap], get_map={"w1": alive})
    coord = WorkerCoordinator(reg, _CoverageProtocol())
    coord._check_stale_workers()  # is_alive True -> recovered branch -> continue (no deregister)
    assert reg.deregistered == []


# ======================================================================================
# metrics: WorkerRegistryCollector error / degradation paths
# ======================================================================================


def test_collector_degrades_when_snapshot_raises() -> None:
    pytest.importorskip("prometheus_client")
    collector = WorkerRegistryCollector(_BoomSnapshotRegistry(), metric_prefix="covsvc")
    families = {fam.name: fam for fam in collector.collect()}  # must not raise
    # Snapshot failed -> empty scrape: the families exist but carry no per-worker samples.
    assert families["covsvc_worker_heartbeat_age_seconds"].samples == []


def test_collector_skips_malformed_snapshot() -> None:
    pytest.importorskip("prometheus_client")
    collector = WorkerRegistryCollector(_BadSnapshotRegistry(), metric_prefix="covsvc", time_source=lambda: 1000.0)
    families = {fam.name: fam for fam in collector.collect()}  # must not raise
    assert families["covsvc_worker_heartbeat_age_seconds"].samples == []  # malformed snapshot skipped


def test_collector_skips_pending_gauge_when_source_raises() -> None:
    pytest.importorskip("prometheus_client")
    reg = WorkerRegistry()
    reg.register("w1", {})

    def _boom() -> int:
        raise ValueError("pending boom")

    collector = WorkerRegistryCollector(reg, pending_tasks_source=_boom, metric_prefix="covsvc")
    families = {fam.name: fam for fam in collector.collect()}  # must not raise
    assert "covsvc_pending_tasks" not in families  # gauge omitted when the source errors
    assert "covsvc_worker_heartbeat_age_seconds" in families  # per-worker scrape still emitted


# ======================================================================================
# security: TLSConfig mTLS / cert-chain validation
# ======================================================================================


def test_tls_mtls_loads_ca_and_requires_client_cert(tmp_path) -> None:
    ca = tmp_path / "ca.pem"
    ca.write_text(_TEST_CERT_PEM)
    ctx = TLSConfig(enabled=True, require_client_cert=True, ca_file=str(ca)).build_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED  # CA loaded + client cert required


def test_tls_mtls_missing_ca_file_raises() -> None:
    cfg = TLSConfig(enabled=True, require_client_cert=True, ca_file="/no/such/ca.pem")
    with pytest.raises(FileNotFoundError):
        cfg.build_ssl_context()


def test_tls_require_client_cert_without_ca_uses_system_trust() -> None:
    ctx = TLSConfig(enabled=True, require_client_cert=True, ca_file=None).build_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED  # required even without an explicit CA file


def test_tls_cert_present_but_key_missing_raises(tmp_path) -> None:
    cert = tmp_path / "cert.pem"
    cert.write_text(_TEST_CERT_PEM)  # cert exists...
    cfg = TLSConfig(enabled=True, cert_file=str(cert), key_file="/no/such/key.pem")  # ...key does not
    with pytest.raises(FileNotFoundError):
        cfg.build_ssl_context()


def test_tls_half_config_cert_only_raises(tmp_path) -> None:
    """enabled + cert XOR key must fail closed (bare SSLContext is a silent misconfig)."""
    cert = tmp_path / "cert.pem"
    cert.write_text(_TEST_CERT_PEM)
    cfg = TLSConfig(enabled=True, cert_file=str(cert), key_file=None)
    with pytest.raises(ValueError, match="incomplete cert/key pair"):
        cfg.build_ssl_context()


def test_tls_half_config_key_only_raises(tmp_path) -> None:
    key = tmp_path / "key.pem"
    key.write_text("-----BEGIN PRIVATE KEY-----\nnot-a-real-key\n-----END PRIVATE KEY-----\n")
    cfg = TLSConfig(enabled=True, cert_file=None, key_file=str(key))
    with pytest.raises(ValueError, match="incomplete cert/key pair"):
        cfg.build_ssl_context()


# ======================================================================================
# security: ConnectionRateLimiter stale-bucket cleanup
# ======================================================================================


def test_rate_limiter_prunes_stale_buckets() -> None:
    limiter = ConnectionRateLimiter(max_connections_per_minute=60, burst_size=5)
    assert limiter.allow("stale-src") is True  # creates a bucket
    # Back-date both the bucket's last access and the last-cleanup marker so the next allow() triggers
    # a cleanup pass that classifies the bucket as stale and prunes it (no sleep needed).
    old = time.time() - 10_000.0
    limiter._buckets["stale-src"].last_access = old
    limiter._last_cleanup = old
    assert limiter.allow("fresh-src") is True  # triggers _maybe_cleanup -> prunes 'stale-src'
    assert "stale-src" not in limiter._buckets
    assert "fresh-src" in limiter._buckets


# ======================================================================================
# security: AnomalyDetector window trim / stats / clear
# ======================================================================================


def test_anomaly_detector_trims_history_to_duplicate_window() -> None:
    det = AnomalyDetector(duplicate_window=3)
    for i in range(6):
        det.check_result("w1", score=0.1 * (i + 1), training_duration=1.0, task_id=f"t{i}")
    # History is trimmed to the last `duplicate_window` records.
    assert det.get_worker_stats("w1")["total_results"] == 3


def test_anomaly_detector_stats_empty_for_unknown_worker() -> None:
    det = AnomalyDetector()
    assert det.get_worker_stats("never-seen") == {"total_results": 0}


def test_anomaly_detector_clear_worker() -> None:
    det = AnomalyDetector()
    det.check_result("w1", score=0.5, training_duration=1.0, task_id="t1")
    assert det.get_worker_stats("w1")["total_results"] == 1
    det.clear_worker("w1")  # drops the history
    assert det.get_worker_stats("w1") == {"total_results": 0}
    det.clear_worker("never-seen")  # popping an absent worker is a safe no-op
