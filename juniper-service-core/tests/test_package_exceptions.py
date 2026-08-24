"""APD-SVCCORE-006 / APD-SVCCORE-014 — the package's exception contract.

``-006``: the five exceptions this package raises had nothing in common. Three subclassed
``RuntimeError`` and two ``KeyError``, so "catch anything juniper-service-core raises"
meant naming all five, and the nearest category was ``except RuntimeError`` -- which also
swallows unrelated runtime failures that should propagate.

``-014``: ``enforce_dependency_floors`` computes a ``list[FloorViolation]`` and used to
format it into prose and discard it, leaving a caller to parse the message back apart.
"""

from __future__ import annotations

import copy
import pickle

import pytest

from juniper_service_core.auth_posture import AuthPostureError
from juniper_service_core.dependency_floors import DependencyFloorError, FloorViolation
from juniper_service_core.exceptions import JuniperServiceCoreError
from juniper_service_core.lifecycle.snapshots import SnapshotNotFoundError
from juniper_service_core.websocket.tunables import UnknownTunableError
from juniper_service_core.workers.registry import WorkerRegistryFullError

# (exception, the base it carried BEFORE the package base existed)
PACKAGE_EXCEPTIONS = [
    (AuthPostureError, RuntimeError),
    (DependencyFloorError, RuntimeError),
    (WorkerRegistryFullError, RuntimeError),
    (SnapshotNotFoundError, KeyError),
]

# ``UnknownTunableError`` is deliberately NOT in the list above. ``websocket/tunables.py``
# is pinned stdlib-only and standalone by two tests in ``test_ws_tunables.py``, one of
# which loads it by file path *bypassing the package __init__*. Importing the package
# base there would erase that property -- a path-load would start initialising
# ``juniper_service_core`` -- to add a base to the one exception in the package with no
# production consumer. The constraint is worth more than the uniformity; this test pins
# the exclusion so it stays a decision rather than an oversight.
EXCLUDED_BY_DESIGN = [UnknownTunableError]


class TestPackageBaseException:
    """APD-SVCCORE-006."""

    @pytest.mark.parametrize(("exc_type", "_legacy"), PACKAGE_EXCEPTIONS, ids=lambda v: getattr(v, "__name__", ""))
    def test_every_package_exception_derives_from_the_base(self, exc_type: type, _legacy: type) -> None:
        assert issubclass(exc_type, JuniperServiceCoreError)

    @pytest.mark.parametrize(("exc_type", "legacy"), PACKAGE_EXCEPTIONS, ids=lambda v: getattr(v, "__name__", ""))
    def test_original_base_is_retained(self, exc_type: type, legacy: type) -> None:
        """The base is added, never substituted.

        This is the arm that makes the change additive. A consumer already writing
        ``except RuntimeError`` or ``except KeyError`` keeps working -- and
        ``SnapshotNotFoundError`` in particular is raised where a mapping lookup would be,
        so callers legitimately treat it as a ``KeyError``.
        """
        assert issubclass(exc_type, legacy)

    def test_the_base_does_not_widen_to_unrelated_errors(self) -> None:
        """Catching the base must not catch things this package did not raise.

        Without this, deriving the base from ``RuntimeError`` -- the obvious shortcut,
        since three of the five already did -- would pass every other test here while
        making ``except JuniperServiceCoreError`` swallow unrelated runtime failures.
        """
        assert not issubclass(RuntimeError, JuniperServiceCoreError)
        assert not issubclass(KeyError, JuniperServiceCoreError)
        assert JuniperServiceCoreError.__mro__[1] is Exception

    def test_base_is_exported_from_the_package_root(self) -> None:
        """Reachable as ``juniper_service_core.JuniperServiceCoreError``.

        That it is reachable *without* pulling the optional dependencies is asserted where
        that guarantee already lives -- ``test_smoke.py``'s blocked-import subprocess --
        rather than restated here, where nothing in-process could actually prove it.
        """
        # Resolved through importlib rather than a bare ``import juniper_service_core``:
        # mixing that with this file's ``from juniper_service_core...`` imports trips
        # CodeQL's py/import-and-import-from, and aliasing the CamelCase name to reach it
        # by ``from`` trips ruff's N813.
        from importlib import import_module

        root = import_module("juniper_service_core")

        assert root.JuniperServiceCoreError is JuniperServiceCoreError
        assert "JuniperServiceCoreError" in root.__all__

    @pytest.mark.parametrize("exc_type", EXCLUDED_BY_DESIGN, ids=lambda v: getattr(v, "__name__", ""))
    def test_documented_exclusion_stays_excluded_and_keeps_its_base(self, exc_type: type) -> None:
        """The exclusion is deliberate, so assert it rather than leaving a silent gap.

        If someone later adds the package base to ``tunables.py``, the stdlib-only tests
        next door fail -- but this says *why* they fail, in the place a reader looking at
        the hierarchy will actually be.
        """
        assert not issubclass(exc_type, JuniperServiceCoreError)
        assert issubclass(exc_type, KeyError)

    def test_catching_the_base_catches_a_real_raise(self) -> None:
        with pytest.raises(JuniperServiceCoreError):
            raise DependencyFloorError("boot failed")


class TestDependencyFloorErrorCarriesViolations:
    """APD-SVCCORE-014."""

    @staticmethod
    def _violations() -> list[FloorViolation]:
        return [
            FloorViolation("juniper-observability", "0.2.0", "0.1.0"),
            FloorViolation("juniper-model-core", "0.3.0", None),
        ]

    def test_violations_are_available_as_structure(self) -> None:
        exc = DependencyFloorError("boot failed", violations=self._violations())

        assert [v.distribution for v in exc.violations] == ["juniper-observability", "juniper-model-core"]
        assert exc.violations[1].installed is None

    def test_message_is_unchanged(self) -> None:
        """The prose is the operator-facing artefact; adding structure must not touch it.

        Forwarding ``violations`` to ``super().__init__`` -- which is what flake8-bugbear's
        B042 suggests -- would put it in ``args`` and make this a tuple repr, silently
        rewriting every boot-failure message in the fleet.
        """
        assert str(DependencyFloorError("boot failed", violations=self._violations())) == "boot failed"

    def test_context_survives_pickle_and_copy(self) -> None:
        """Exceptions cross process boundaries here, so the added field must survive.

        No ``__reduce__`` override is required for that, contrary to the obvious
        assumption: CPython's ``BaseException.__reduce__`` returns
        ``(cls, args, self.__dict__)`` whenever the instance dict is non-empty, and
        ``args`` is just the message, which this signature takes positionally. A draft of
        this change carried an override justified by the opposite claim; removing it left
        this test passing, which is how the claim was found to be wrong. The guarantee is
        pinned here either way -- it is the behaviour that matters, not the mechanism.
        """
        exc = DependencyFloorError("boot failed", violations=self._violations())

        assert list(pickle.loads(pickle.dumps(exc)).violations) == list(exc.violations)  # noqa: S301 - our own payload
        assert list(copy.copy(exc).violations) == list(exc.violations)
        assert list(copy.deepcopy(exc).violations) == list(exc.violations)

    def test_single_argument_construction_still_works(self) -> None:
        """Back-compat: every existing call site passes only a message."""
        exc = DependencyFloorError("just a message")

        assert exc.violations == ()
        assert str(exc) == "just a message"

    def test_enforce_attaches_the_violations_it_reported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """End to end: the list the check computed is the list the caller receives.

        Asserting on the constructor alone would pass even if the raise site kept throwing
        the structure away, which is precisely what the defect was.
        """
        from juniper_service_core import dependency_floors

        # The escape hatch would short-circuit the whole check and make this vacuous.
        monkeypatch.delenv(dependency_floors.DEFAULT_SKIP_ENV_VAR, raising=False)

        with pytest.raises(DependencyFloorError) as excinfo:
            # A floor no installed build can satisfy, passed directly -- the real
            # resolution path, no internals patched.
            dependency_floors.enforce_dependency_floors(floors={"juniper-observability": "99.0.0"})

        assert excinfo.value.violations
        assert excinfo.value.violations[0].distribution == "juniper-observability"
