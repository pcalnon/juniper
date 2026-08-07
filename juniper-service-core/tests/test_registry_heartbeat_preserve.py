"""Pin WorkerRegistration.record_heartbeat None-preserve + defensive duration copy.

Sparse heartbeats (older worker images, or workers that omit enrichment) pass ``None``
for enriched fields. The contract is preserve-prior — a regression that treats ``None``
as a wipe would zero ``rss_mb`` / ``in_flight_tasks`` / GPU telemetry between ticks and
poison the metrics collector / idle-dispatch health view.

``recent_task_durations_seconds`` must be defensively copied so a caller mutating the
list after heartbeat cannot rewrite the registry window through a shared reference.

Hermetic stdlib-only; no FastAPI / network. New file avoids contested workers coverage
files touched by open coordinator / TLS PRs.
"""

from __future__ import annotations

from juniper_service_core.workers.registry import WorkerRegistration, WorkerRegistry


def test_record_heartbeat_none_preserves_prior_enriched_fields() -> None:
    reg = WorkerRegistration(worker_id="w1")
    reg.record_heartbeat(
        in_flight_tasks=3,
        rss_mb=512.5,
        tasks_completed=10,
        tasks_failed=1,
        last_task_duration_seconds=2.5,
        recent_task_durations_seconds=[1.0, 2.0, 2.5],
        gpu_utilization_pct=77.0,
        last_task_completed_at=1234.5,
    )
    prior_hb = reg.last_heartbeat

    # Sparse tick: only the timestamp should advance; every enriched field stays put.
    reg.record_heartbeat()
    assert reg.last_heartbeat >= prior_hb
    assert reg.in_flight_tasks == 3
    assert reg.rss_mb == 512.5
    assert reg.tasks_completed == 10
    assert reg.tasks_failed == 1
    assert reg.last_task_duration_seconds == 2.5
    assert reg.recent_task_durations_seconds == [1.0, 2.0, 2.5]
    assert reg.gpu_utilization_pct == 77.0
    assert reg.last_task_completed_at == 1234.5


def test_record_heartbeat_partial_update_does_not_wipe_siblings() -> None:
    reg = WorkerRegistration(worker_id="w1")
    reg.record_heartbeat(rss_mb=256.0, gpu_utilization_pct=40.0, in_flight_tasks=1)
    reg.record_heartbeat(rss_mb=300.0)  # only RSS reported this tick
    assert reg.rss_mb == 300.0
    assert reg.gpu_utilization_pct == 40.0
    assert reg.in_flight_tasks == 1


def test_recent_task_durations_defensive_copy() -> None:
    reg = WorkerRegistration(worker_id="w1")
    window = [1.0, 2.0, 3.0]
    reg.record_heartbeat(recent_task_durations_seconds=window)
    window.append(999.0)
    window[0] = -1.0
    assert reg.recent_task_durations_seconds == [1.0, 2.0, 3.0]


def test_registry_heartbeat_none_preserves_via_public_api() -> None:
    # Same contract through WorkerRegistry.heartbeat (the websocket call path).
    registry = WorkerRegistry()
    registry.register("w1", {})
    assert registry.heartbeat(
        "w1",
        rss_mb=128.0,
        in_flight_tasks=2,
        recent_task_durations_seconds=[4.0, 5.0],
        gpu_utilization_pct=11.0,
    )
    assert registry.heartbeat("w1") is True  # sparse
    snap = registry.get("w1")
    assert snap is not None
    assert snap.rss_mb == 128.0
    assert snap.in_flight_tasks == 2
    assert snap.recent_task_durations_seconds == [4.0, 5.0]
    assert snap.gpu_utilization_pct == 11.0
