"""Tests for ``juniper_observability.prometheus_helpers``.

The seven test groups in §6 of
``notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md``
plus a few extras for ``register_info_or_update`` and the
:func:`lazy_register_or_reuse` cache.
"""

from __future__ import annotations

import threading

import pytest
from prometheus_client import REGISTRY, Counter, Enum, Gauge, Histogram, Info, Summary

from juniper_observability.prometheus_helpers import (
    _clear_lazy_cache,
    lazy_register_or_reuse,
    register_fresh,
    register_info_or_update,
    register_or_reuse,
)


def _unregister(name: str) -> None:
    """Remove any collector registered under ``name`` so each test
    starts from a clean REGISTRY for that metric name."""
    for collector, names in list(REGISTRY._collector_to_names.items()):
        if name in names:
            try:
                REGISTRY.unregister(collector)
            except KeyError:  # pragma: no cover — already gone
                pass
            return


@pytest.fixture(autouse=True)
def _scrub_registry_and_lazy_cache():
    """Function-scoped scrub so tests in this file are independent.

    Snapshots REGISTRY before each test, unregisters anything new
    afterwards, and clears the lazy cache. Mirrors what
    ``juniper_observability.testing.reset_prometheus_registry``
    provides for consumers.
    """
    before = set(REGISTRY._collector_to_names.keys())
    yield
    after = set(REGISTRY._collector_to_names.keys())
    for collector in after - before:
        try:
            REGISTRY.unregister(collector)
        except Exception:  # nosec B110
            pass
    _clear_lazy_cache()


# ---------------------------------------------------------------------------
# register_or_reuse
# ---------------------------------------------------------------------------


class TestRegisterOrReuse:
    def test_first_call_registers_and_returns_fresh_collector(self):
        c = register_or_reuse(Counter, "test_ror_counter_1", "doc", ["lbl"])
        assert isinstance(c, Counter)
        # Verify it's actually in REGISTRY (lookup by passed name).
        assert REGISTRY._names_to_collectors["test_ror_counter_1"] is c

    def test_second_call_adopts_existing_collector(self):
        first = register_or_reuse(Counter, "test_ror_counter_2", "doc", ["lbl"])
        second = register_or_reuse(Counter, "test_ror_counter_2", "doc", ["lbl"])
        assert first is second  # adopt-existing returns the same object

    def test_second_call_args_silently_ignored(self):
        # First registration: explicit description.
        first = register_or_reuse(Counter, "test_ror_counter_3", "first description", ["lbl"])
        # Second call with a different description should still return
        # the original collector — the latest call's args are dropped.
        second = register_or_reuse(Counter, "test_ror_counter_3", "second description", ["lbl"])
        assert first is second
        # The collector's documentation is whatever was on the first
        # construction; ``prometheus_client`` exposes it via
        # ``Counter.documentation``.
        assert second._documentation == "first description"

    def test_accumulated_samples_preserved_across_adopt(self):
        c1 = register_or_reuse(Counter, "test_ror_counter_4", "doc", ["lbl"])
        c1.labels(lbl="a").inc(7)
        c2 = register_or_reuse(Counter, "test_ror_counter_4", "doc", ["lbl"])
        # Same object, so the value survives.
        assert c2.labels(lbl="a")._value.get() == 7.0

    def test_non_duplicate_value_error_propagates(self):
        # ``Histogram`` rejects ``le`` as a label name (it's reserved
        # for the bucket-bound label that ``Histogram`` adds itself).
        # The resulting ``ValueError`` does NOT include "Duplicated
        # timeseries"; the helper must let it through unchanged
        # rather than masking it as a registry-state issue.
        with pytest.raises(ValueError) as excinfo:
            register_or_reuse(Histogram, "test_ror_bad_label", "doc", ["le"])
        assert "Duplicated timeseries" not in str(excinfo.value)

    @pytest.mark.parametrize(
        ("factory", "name", "args"),
        [
            (Counter, "test_ror_each_counter", ("doc", ["lbl"])),
            (Gauge, "test_ror_each_gauge", ("doc", ["lbl"])),
            (
                Histogram,
                "test_ror_each_histogram",
                ("doc", ["lbl"]),
            ),
            (Summary, "test_ror_each_summary", ("doc", ["lbl"])),
            (Info, "test_ror_each_info", ("doc",)),
            (
                Enum,
                "test_ror_each_enum",
                ("doc", ["lbl"]),
            ),
        ],
    )
    def test_round_trip_each_collector_type(self, factory, name, args):
        # ``Enum`` requires a ``states=`` kwarg, ``Histogram`` accepts
        # ``buckets=``, etc. Use generic args so each type's own
        # validation runs and surfaces.
        kwargs = {}
        if factory is Enum:
            kwargs["states"] = ["a", "b"]
        first = register_or_reuse(factory, name, *args, **kwargs)
        second = register_or_reuse(factory, name, *args, **kwargs)
        assert first is second


# ---------------------------------------------------------------------------
# register_fresh
# ---------------------------------------------------------------------------


class TestRegisterFresh:
    def test_first_call_registers_and_returns_fresh_collector(self):
        c = register_fresh(Counter, "test_rf_counter_1", "doc", ["lbl"])
        assert isinstance(c, Counter)
        assert REGISTRY._names_to_collectors["test_rf_counter_1"] is c

    def test_second_call_returns_different_object(self):
        first = register_fresh(Counter, "test_rf_counter_2", "doc", ["lbl"])
        second = register_fresh(Counter, "test_rf_counter_2", "doc", ["lbl"])
        assert first is not second
        # Only the new one is in REGISTRY.
        assert REGISTRY._names_to_collectors["test_rf_counter_2"] is second

    def test_second_call_args_take_effect(self):
        first = register_fresh(Counter, "test_rf_counter_3", "first doc", ["lbl"])
        second = register_fresh(Counter, "test_rf_counter_3", "second doc", ["lbl"])
        assert first is not second
        assert second._documentation == "second doc"

    def test_samples_discarded_on_recreate(self):
        c1 = register_fresh(Counter, "test_rf_counter_4", "doc", ["lbl"])
        c1.labels(lbl="a").inc(7)
        c2 = register_fresh(Counter, "test_rf_counter_4", "doc", ["lbl"])
        # Different object; new starts at zero.
        assert c1 is not c2
        assert c2.labels(lbl="a")._value.get() == 0.0

    def test_non_duplicate_value_error_propagates(self):
        # Same idea as TestRegisterOrReuse — ``le`` is a reserved
        # ``Histogram`` label name; the resulting ``ValueError`` is
        # not a duplicate-registration error and must propagate
        # unchanged.
        with pytest.raises(ValueError) as excinfo:
            register_fresh(Histogram, "test_rf_bad_label", "doc", ["le"])
        assert "Duplicated timeseries" not in str(excinfo.value)


# ---------------------------------------------------------------------------
# register_info_or_update
# ---------------------------------------------------------------------------


class TestRegisterInfoOrUpdate:
    def test_first_call_registers_and_sets_labels(self):
        info = register_info_or_update(
            "test_iou_build_1",
            "Build info",
            version="1.0.0",
            python_version="3.13.0",
        )
        assert isinstance(info, Info)
        # ``Info`` exposes the current label set via ``_value``.
        assert info._value == {"version": "1.0.0", "python_version": "3.13.0"}

    def test_second_call_adopts_and_overwrites_labels(self):
        first = register_info_or_update(
            "test_iou_build_2",
            "Build info",
            version="1.0.0",
        )
        second = register_info_or_update(
            "test_iou_build_2",
            "Build info",
            version="1.0.1",
        )
        # Same Info object, latest labels.
        assert first is second
        assert second._value == {"version": "1.0.1"}

    def test_returns_info_collector(self):
        info = register_info_or_update("test_iou_build_3", "doc", k="v")
        assert isinstance(info, Info)


# ---------------------------------------------------------------------------
# lazy_register_or_reuse
# ---------------------------------------------------------------------------


class TestLazyRegisterOrReuse:
    def test_first_call_registers_and_caches(self):
        c = lazy_register_or_reuse(Counter, "test_lazy_counter_1", "doc", ["lbl"])
        assert isinstance(c, Counter)
        # Hot-path: second call returns from cache without re-entering
        # REGISTRY logic.
        c2 = lazy_register_or_reuse(Counter, "test_lazy_counter_1", "doc", ["lbl"])
        assert c is c2

    def test_different_names_get_different_collectors(self):
        a = lazy_register_or_reuse(Counter, "test_lazy_counter_2a", "doc")
        b = lazy_register_or_reuse(Counter, "test_lazy_counter_2b", "doc")
        assert a is not b

    def test_clear_cache_forces_relookup(self):
        first = lazy_register_or_reuse(Counter, "test_lazy_counter_3", "doc", ["lbl"])
        _clear_lazy_cache()
        # After clearing the cache, the helper goes back to REGISTRY
        # and adopts the existing collector — same object, but a
        # fresh dict-cache slot.
        second = lazy_register_or_reuse(Counter, "test_lazy_counter_3", "doc", ["lbl"])
        assert first is second  # adoption finds the registered one

    def test_thread_safety_double_init(self):
        # Concurrent first-time calls with the same name must end up
        # with the same single collector — the lock on the slow path
        # guarantees only one thread enters the construction step.
        results = []
        barrier = threading.Barrier(8)

        def _worker():
            barrier.wait()
            results.append(lazy_register_or_reuse(Counter, "test_lazy_counter_4", "doc", ["lbl"]))

        threads = [threading.Thread(target=_worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # All eight workers see the same collector.
        assert len({id(c) for c in results}) == 1


class TestPublicReturnAnnotations:
    """APD-OBS-003: ``register_info_or_update`` returned ``Any``, unlike its siblings.

    ``prometheus_client`` is an optional extra, so the collector types cannot be imported
    at module scope -- which is why this one helper was left as ``Any`` while
    ``register_or_reuse`` / ``register_fresh`` / ``lazy_register_or_reuse`` all return
    ``T``. ``Any`` silently disables checking at every call site: with it, assigning the
    result to an ``int`` type-checks clean.

    The fix is a ``TYPE_CHECKING``-only import, so these tests pin BOTH halves -- the
    annotation is a real type, and the runtime import cost stays zero. Checking only the
    annotation would pass a change that imports ``prometheus_client`` eagerly and breaks
    every consumer that installed the package without the extra.
    """

    def test_no_public_helper_returns_bare_any(self):
        import typing

        from juniper_observability import prometheus_helpers as helpers

        for name in helpers.__all__:
            # ``Info`` is a TYPE_CHECKING-only import, so it is genuinely absent from the
            # module's runtime globals -- supply it, exactly as a type checker would.
            hints = typing.get_type_hints(getattr(helpers, name), localns={"Info": Info})
            assert hints["return"] is not typing.Any, f"{name} returns bare Any -- every call site loses checking"

    def test_register_info_or_update_is_annotated_as_info(self):
        import typing

        from juniper_observability.prometheus_helpers import register_info_or_update

        hints = typing.get_type_hints(register_info_or_update, localns={"Info": Info})
        assert hints["return"] is Info

    def test_the_annotation_is_not_resolvable_without_the_optional_extra(self):
        """The TYPE_CHECKING guard is real, not decorative.

        ``get_type_hints`` above needs ``localns`` precisely because ``Info`` is absent
        from the module's runtime namespace. If someone "fixes" the import by hoisting it
        to module scope this raises nothing and the test fails -- which is the point:
        that hoist is what breaks installs without the ``prometheus`` extra.
        """
        import typing

        from juniper_observability.prometheus_helpers import register_info_or_update

        with pytest.raises(NameError):
            typing.get_type_hints(register_info_or_update)

    def test_importing_the_module_does_not_import_prometheus_client(self):
        """The TYPE_CHECKING guard must keep the optional extra optional."""
        import subprocess
        import sys

        probe = "import juniper_observability.prometheus_helpers as h, sys; print('prometheus_client' in sys.modules)"
        out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True)
        assert out.stdout.strip() == "False", "prometheus_client was imported at module scope -- the optional extra is no longer optional"
