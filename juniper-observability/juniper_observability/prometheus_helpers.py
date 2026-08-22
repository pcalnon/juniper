"""Idempotent ``prometheus_client`` collector helpers.

The four helpers in this module solve a recurring failure mode in the
Juniper fleet: ``prometheus_client`` collector classes (``Counter``,
``Gauge``, ``Histogram``, ``Summary``, ``Info``, ``Enum``) register
themselves with the global ``REGISTRY`` on construction and raise
``ValueError("Duplicated timeseries ...")`` if the metric name is
already present. The library does not provide a "register-if-absent"
or "get-or-create" primitive — every consumer that might re-instantiate
a collector must implement that themselves. Pre-2026-05-05 the same
try/except + REGISTRY-lookup pattern was copy-pasted in ~10 production
sites across 5 repos, with two subtly different implementations
("adopt existing" vs "drop and recreate") in the wild.

These helpers consolidate the pattern. See
``notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md``
in the juniper-ml repo for the full analysis, rationale, and
migration plan.

Public API:

- :func:`register_or_reuse` — adopt-existing on duplicate (samples
  preserved; latest call's ``args`` ignored). The default choice for
  almost every call site.
- :func:`register_fresh` — drop-and-recreate on duplicate (samples
  discarded; latest call's ``args`` take effect). Use only when a
  test fixture or migration path *intentionally* wants different
  buckets/labels.
- :func:`register_info_or_update` — sugar over :func:`register_or_reuse`
  for the ``Info`` collector, which has both a registration step and
  a separate ``.info({...})`` label-update step.
- :func:`lazy_register_or_reuse` — like :func:`register_or_reuse` but
  caches the result in a module-private dict keyed by metric name.
  For the "lazy-init with ``None`` sentinel" pattern that several
  consumers use.

All four lazy-import ``prometheus_client`` so callers without the
optional dependency only pay the import cost on the path that actually
needs the SDK. Logging is intentionally absent — consumers that want
to surface unexpected re-registrations can wrap.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:  # pragma: no cover - typing only
    # ``prometheus_client`` is an optional extra, so it must never be imported
    # at runtime here. ``from __future__ import annotations`` makes the
    # annotation a string, so this import costs nothing outside a type checker.
    from prometheus_client import Info

T = TypeVar("T")


__all__ = [
    "lazy_register_or_reuse",
    "register_fresh",
    "register_info_or_update",
    "register_or_reuse",
]


# ---------------------------------------------------------------------------
# Lazy-cache plumbing for ``lazy_register_or_reuse``.
# ---------------------------------------------------------------------------

# Module-private cache shared across all consumers. Keyed by metric name
# (the value passed as the second argument to the helper). Access goes
# through the lock for thread safety; the per-call fast path is a single
# unsynchronized dict ``get`` so the steady-state cost on a hot path is
# the same as a normal sentinel check.
_lazy_cache: dict[str, Any] = {}
_lazy_cache_lock = threading.Lock()


def _clear_lazy_cache() -> None:
    """Clear the :func:`lazy_register_or_reuse` cache.

    Test-only helper — production code should never need to call this.
    The :func:`juniper_observability.testing.reset_prometheus_registry`
    pytest fixture invokes it as part of its REGISTRY scrub.
    """
    with _lazy_cache_lock:
        _lazy_cache.clear()


# ---------------------------------------------------------------------------
# The four public helpers.
# ---------------------------------------------------------------------------


def register_or_reuse(
    factory: Callable[..., T],
    name: str,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Construct a ``prometheus_client`` collector idempotently (adopt mode).

    On first call with a given ``name``, behaves identically to
    ``factory(name, *args, **kwargs)`` — the collector is registered
    with the default ``REGISTRY`` and returned.

    On a subsequent call with the same ``name`` (typically because a
    test fixture cleared a module-level cache without unregistering, or
    because the host module was re-imported), catches the resulting
    ``ValueError("Duplicated timeseries ...")`` and **adopts** the
    already-registered collector — accumulated samples are preserved,
    and the latest call's ``args`` / ``kwargs`` are silently ignored.
    Use :func:`register_fresh` instead when the latest call's args are
    intentionally different from the original.

    Lazy-imports ``prometheus_client`` so callers without the optional
    dependency only pay the import cost on the path that actually needs
    the SDK.

    Args:
        factory: A ``prometheus_client`` collector class — ``Counter``,
            ``Gauge``, ``Histogram``, ``Summary``, ``Info``, ``Enum``.
        name: The metric name passed as the first positional argument
            to ``factory``.
        *args: Forwarded to ``factory`` on first call; ignored on the
            adopt path.
        **kwargs: Forwarded to ``factory`` on first call; ignored on
            the adopt path.

    Returns:
        The collector — newly registered on first call, or the existing
        collector from ``REGISTRY`` on the duplicate path.

    Raises:
        ValueError: For any ``ValueError`` from ``factory`` whose
            message does not include ``"Duplicated timeseries"`` (e.g.
            genuinely invalid metric name). The duplicate-only filter
            avoids masking unrelated misuse.
    """
    from prometheus_client import REGISTRY

    try:
        return factory(name, *args, **kwargs)
    except ValueError as exc:
        if "Duplicated timeseries" not in str(exc):
            raise
        # ``prometheus_client`` registers each collector under both the
        # bare name and the suffixed sample names (``_total`` /
        # ``_created`` / ``_bucket`` / ``_sum`` / ``_count`` / ``_info``);
        # all entries point at the same collector object, so a lookup
        # by the name we passed always finds the existing collector
        # whenever the duplicate-detection branch fired.
        existing = REGISTRY._names_to_collectors.get(name)
        if existing is None:
            # The name is registered (Prometheus said so) but our lookup
            # missed — most likely an internal contract change in
            # ``prometheus_client``. Re-raise the original error rather
            # than silently returning ``None``.
            raise
        return existing


def register_fresh(
    factory: Callable[..., T],
    name: str,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Construct a ``prometheus_client`` collector, dropping any existing one.

    On first call: identical to ``factory(name, *args, **kwargs)``.

    On a subsequent call with the same ``name``: unregisters the
    pre-existing collector from ``REGISTRY``, *then* re-runs ``factory``
    with the latest call's ``args`` / ``kwargs``. The newly returned
    collector reflects the latest call's description / labels / buckets;
    any samples accumulated by the prior collector are **discarded**.

    Use this only when the latest call's args are intentionally
    different from the prior registration — test fixtures exercising
    different bucket boundaries, migrations that change a label set,
    etc. For the common case where a re-registration just means "the
    same metric, re-instantiated", :func:`register_or_reuse` is the
    cheaper and more correct choice.

    Args:
        factory: A ``prometheus_client`` collector class.
        name: Metric name.
        *args: Forwarded to ``factory`` on every call.
        **kwargs: Forwarded to ``factory`` on every call.

    Returns:
        The newly-registered collector. On the duplicate path, this is
        a different object from any prior return value.

    Raises:
        ValueError: For any ``ValueError`` from ``factory`` whose
            message does not include ``"Duplicated timeseries"``.
    """
    from prometheus_client import REGISTRY

    try:
        return factory(name, *args, **kwargs)
    except ValueError as exc:
        if "Duplicated timeseries" not in str(exc):
            raise
        # Find and drop the orphaned collector by name. ``REGISTRY._
        # collector_to_names`` is the same lookup ``REGISTRY.register``
        # uses for the duplicate check, so anything that triggered the
        # ValueError above must be in here.
        for collector, names in list(REGISTRY._collector_to_names.items()):
            if name in names:
                REGISTRY.unregister(collector)
                break
        # Retry the original construction with the caller's args. Any
        # second ValueError is a hard error (something else holds the
        # name) — let it propagate.
        return factory(name, *args, **kwargs)


def register_info_or_update(
    name: str,
    description: str,
    **info_labels: str,
) -> Info:
    """Register a ``prometheus_client.Info`` collector and set its labels.

    ``Info`` is the one collector type with a two-step registration:
    construct with ``Info(name, description)``, then call
    ``.info({"k": "v", ...})`` to populate the label set. This helper
    composes the two steps so a caller writes::

        register_info_or_update(
            "juniper_data_build",
            "Build information for juniper-data",
            version="1.2.3",
            python_version="3.13.0",
        )

    On first call the helper registers the ``Info`` collector and sets
    its labels. On a subsequent call with the same ``name`` the helper
    adopts the existing collector (via :func:`register_or_reuse`) and
    overwrites its labels with the latest values — the typical
    ``set_build_info`` semantics, which expects later calls to update
    the displayed version even after the metric is already registered.

    Args:
        name: ``Info`` metric name (without the ``_info`` suffix that
            ``prometheus_client`` adds internally).
        description: Help text. On the adopt path this is ignored —
            the original collector keeps its description.
        **info_labels: Label values applied via ``info.info(...)``.
            All values are coerced to strings by ``prometheus_client``.

    Returns:
        The ``Info`` collector — newly registered or adopted from a
        prior call.
    """
    from prometheus_client import Info

    info = register_or_reuse(Info, name, description)
    info.info(info_labels)
    return info


def lazy_register_or_reuse(
    factory: Callable[..., T],
    name: str,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Cached :func:`register_or_reuse` for the lazy-init sentinel pattern.

    Several Juniper services keep a module-level ``_foo: Optional[T] =
    None`` sentinel and a wrapper function that constructs the collector
    on first call and returns the cached object thereafter. That pattern
    is fragile under tests that reset the module-level sentinel without
    also unregistering from ``REGISTRY``. This helper inverts the
    ownership: the cache lives **here**, keyed by metric name, so the
    consumer's lazy wrapper becomes a single line.

    Equivalent to :func:`register_or_reuse` plus a process-wide cache.
    Subsequent calls with the same ``name`` return the cached collector
    without re-entering the ``factory`` / ``REGISTRY`` paths at all —
    so the steady-state hot-path cost is one dict lookup.

    The cache is process-wide and module-private; tests that reset
    consumer state should use the
    :func:`juniper_observability.testing.reset_prometheus_registry`
    fixture which clears this cache as part of its teardown.

    Args:
        factory: A ``prometheus_client`` collector class.
        name: Metric name. Also the cache key — two calls with
            different ``name`` return different collectors even when
            ``factory`` matches.
        *args: Forwarded to :func:`register_or_reuse` on first call.
        **kwargs: Forwarded to :func:`register_or_reuse` on first call.

    Returns:
        The cached or freshly-registered collector.
    """
    # Fast path: unsynchronized ``get`` on the cache. Repeated reads of
    # a stable dict entry are race-free for our purposes — the worst
    # case is a momentarily-stale ``None`` which falls into the slow
    # path and re-acquires the cache under the lock.
    cached = _lazy_cache.get(name)
    if cached is not None:
        return cached
    with _lazy_cache_lock:
        cached = _lazy_cache.get(name)
        if cached is not None:
            return cached
        collector = register_or_reuse(factory, name, *args, **kwargs)
        _lazy_cache[name] = collector
        return collector
