"""Boot-time dependency-floor self-check (E-8) — fail loud before a service binds.

The **prevention** companion to the E-2 env-floor-drift **detector** (juniper-ml's
``util/env_floor_drift_check.py`` + the ``juniper-env-drift-check`` CI console script):
those detect a below-floor ``juniper-*`` wheel out of band; this stops a service from
serving on top of one. A service calls :func:`enforce_dependency_floors` at startup —
before it binds — and if any of its declared ``juniper-*`` floors is unsatisfied by the
installed environment, the call raises :class:`DependencyFloorError` with a
``dep + floor + installed`` message, so the server's startup fails loudly instead of the
service limping along on a stale wheel. This is the failure mode behind the canopy
"green tests / dead app" incident (a client wheel below its ``pyproject`` floor passed
unit tests but broke the live app), and it is the automatic enforcement the manual /
CI-less E-2 posture lacks.

**Dependency-light and stdlib-first.** ``importlib.metadata`` reads installed versions
and Requires-Dist; ``tomllib`` reads a source ``pyproject.toml``. ``packaging`` is used
for version comparison when importable, with a numeric-tuple fallback, so this module
adds **no** hard dependency and preserves the dependency-free ``import
juniper_service_core`` guarantee.

**Escape hatch.** ``JUNIPER_SKIP_DEP_FLOOR_CHECK`` (by default), when truthy, bypasses
the check — logged loudly — so a false positive can never permanently block a
legitimate start.
"""

from __future__ import annotations

import logging
import os
import re
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from importlib import metadata
from pathlib import Path
from typing import NamedTuple

from juniper_service_core.exceptions import JuniperServiceCoreError

try:  # ``packaging`` is near-universal (pip depends on it) but not a hard dep here.
    from packaging.version import InvalidVersion, Version
except ModuleNotFoundError:  # pragma: no cover - exercised only in a packaging-free env
    Version = None  # type: ignore[assignment]
    InvalidVersion = Exception  # type: ignore[assignment,misc]

_LOG = logging.getLogger("juniper_service_core.dependency_floors")

#: Default escape-hatch environment variable; set truthy to bypass the check.
DEFAULT_SKIP_ENV_VAR = "JUNIPER_SKIP_DEP_FLOOR_CHECK"
#: Only distributions whose name starts with this prefix are enforced by default.
DEFAULT_PREFIX = "juniper-"

_TRUTHY = {"1", "true", "yes", "on"}

# A ``>=`` lower bound in a Requires-Dist / pyproject dependency string. Handles both
# the bare ``name>=1.2.3`` and the older parenthesised ``name (>=1.2.3)`` forms.
_FLOOR_RE = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*\(?[^)]*?>=\s*([0-9]+(?:\.[0-9]+)*)")


class DependencyFloorError(JuniperServiceCoreError, RuntimeError):
    """Raised when an installed ``juniper-*`` distribution is below its declared floor.

    Carries the structured violations alongside the rendered message (APD-SVCCORE-014).
    ``check_dependency_floors`` computes a ``list[FloorViolation]`` -- distribution, floor,
    and installed version per row -- and :func:`enforce_dependency_floors` used to format
    that into prose and throw the list away. A caller that wanted to do anything but print
    the message, such as report which distribution to upgrade, had to parse the text back
    apart. The message is unchanged; the structure is now simply also available.

    Attributes:
        violations: The unsatisfied floors, in the order reported. Empty when the error is
            constructed without them, so existing single-argument call sites keep working.
    """

    def __init__(self, message: str = "", *, violations: Sequence[FloorViolation] = ()) -> None:
        # ``violations`` is keyword-only and is NOT forwarded to ``super()``. Forwarding it
        # would put it in ``args`` and turn ``str(exc)`` into a tuple repr, rewriting every
        # boot-failure message an operator has ever seen.
        #
        # No ``__reduce__`` override is needed to keep it across pickle/copy, which is
        # worth stating because the obvious assumption is the opposite: CPython's
        # ``BaseException.__reduce__`` returns ``(cls, args, self.__dict__)`` whenever the
        # instance dict is non-empty, so the attribute is restored automatically -- and
        # ``args`` here is just the message, which this signature accepts positionally.
        # Verified by ``test_context_survives_pickle_and_copy``, and by removing a draft
        # override and watching that test keep passing.
        super().__init__(message)
        self.message = message
        self.violations: tuple[FloorViolation, ...] = tuple(violations)


class FloorViolation(NamedTuple):
    """One unsatisfied floor. ``installed`` is ``None`` when the dist is not installed."""

    distribution: str
    floor: str
    installed: str | None


def _is_truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in _TRUTHY


def _vtuple(v: str) -> tuple[int, ...]:
    """Leading numeric release of a version as an int tuple (packaging-free fallback)."""
    head = re.split(r"[^0-9.]", v, maxsplit=1)[0]
    parts = [int(p) for p in head.split(".") if p.isdigit()]
    return tuple(parts) or (0,)


def _below(installed: str, floor: str) -> bool:
    """True if ``installed`` < ``floor``. Uses ``packaging`` when available; if either
    operand fails to parse, both fall back to a numeric-tuple compare so they stay
    comparable."""
    if Version is not None:
        try:
            return Version(installed) < Version(floor)
        except InvalidVersion:  # pragma: no cover - non-PEP440 versions are rare
            pass
    return _vtuple(installed) < _vtuple(floor)


def _normalize(name: str) -> str:
    """PEP 503 name normalization (``Foo_Bar`` -> ``foo-bar``)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def check_dependency_floors(floors: Mapping[str, str]) -> list[FloorViolation]:
    """Return the violations among ``floors`` (``{distribution: min_version}``).

    A distribution violates when it is not installed, or its installed version is below
    the floor. Pure and side-effect-free — the testable core of the check.
    """
    violations: list[FloorViolation] = []
    for dist, floor in floors.items():
        try:
            installed = metadata.version(dist)
        except metadata.PackageNotFoundError:
            violations.append(FloorViolation(dist, floor, None))
            continue
        if _below(installed, floor):
            violations.append(FloorViolation(dist, floor, installed))
    return violations


def floors_from_requirements(requirements: Iterable[str], *, prefix: str = DEFAULT_PREFIX) -> dict[str, str]:
    """Extract ``{dist: floor}`` for ``prefix`` deps with a ``>=`` bound.

    Requirements carrying an environment marker (anything after a ``;`` — extras,
    ``python_version`` guards, etc.) are **skipped**: a boot check only enforces the
    unconditional runtime floors, never a dep that may legitimately be absent.
    """
    floors: dict[str, str] = {}
    for raw in requirements or ():
        if ";" in raw:  # conditional / extra-gated dep — not an unconditional floor
            continue
        match = _FLOOR_RE.match(raw)
        if not match:
            continue
        name = match.group(1)
        if not _normalize(name).startswith(_normalize(prefix)):
            continue
        floors[name] = match.group(2)
    return floors


def floors_from_distribution(distribution: str, *, prefix: str = DEFAULT_PREFIX) -> dict[str, str]:
    """Read ``distribution``'s installed Requires-Dist metadata -> ``{juniper-* dep: floor}``.

    The robust runtime path: the metadata ships inside the installed wheel, so this works
    whether the caller is installed as a wheel or as an editable install, with no reliance
    on a source ``pyproject.toml`` being present on disk.
    """
    return floors_from_requirements(metadata.requires(distribution) or [], prefix=prefix)


def floors_from_pyproject(pyproject_path: str | Path, *, prefix: str = DEFAULT_PREFIX) -> dict[str, str]:
    """Parse ``[project].dependencies`` from a source ``pyproject.toml`` -> ``{dep: floor}``."""
    data = tomllib.loads(Path(pyproject_path).read_text(encoding="utf-8"))
    deps = data.get("project", {}).get("dependencies", []) or []
    return floors_from_requirements(deps, prefix=prefix)


def _resolve_floors(
    floors: Mapping[str, str] | None,
    distribution: str | None,
    pyproject_path: str | Path | None,
    prefix: str,
) -> dict[str, str]:
    if floors is not None:
        return dict(floors)
    if distribution is not None:
        return floors_from_distribution(distribution, prefix=prefix)
    if pyproject_path is not None:
        return floors_from_pyproject(pyproject_path, prefix=prefix)
    raise ValueError("enforce_dependency_floors: provide one of floors=, distribution=, or pyproject_path=")


def _format_violations(violations: Iterable[FloorViolation]) -> str:
    lines = []
    for v in violations:
        if v.installed is None:
            lines.append(f"  - {v.distribution}: requires >={v.floor}, but it is NOT INSTALLED")
        else:
            lines.append(f"  - {v.distribution}: requires >={v.floor}, but {v.installed} is installed")
    return "\n".join(lines)


def enforce_dependency_floors(
    floors: Mapping[str, str] | None = None,
    *,
    distribution: str | None = None,
    pyproject_path: str | Path | None = None,
    prefix: str = DEFAULT_PREFIX,
    skip_env_var: str = DEFAULT_SKIP_ENV_VAR,
    logger: logging.Logger | None = None,
) -> None:
    """Fail loud (raise :class:`DependencyFloorError`) if any resolved ``juniper-*``
    floor is unsatisfied by the installed environment.

    Call this at service startup, **before binding**, so a service never serves on top of
    a below-floor wheel. Floors are resolved from the first provided of: ``floors`` (an
    explicit ``{dist: min_version}`` mapping), ``distribution`` (that dist's installed
    Requires-Dist — the robust runtime path), or ``pyproject_path`` (a source
    ``pyproject.toml``).

    The ``skip_env_var`` escape hatch (default ``JUNIPER_SKIP_DEP_FLOOR_CHECK``), when set
    to a truthy value (``1``/``true``/``yes``/``on``), logs loudly and returns without
    checking — so a false positive can never permanently block a legitimate start.
    """
    log = logger or _LOG
    if skip_env_var and _is_truthy(os.getenv(skip_env_var)):
        log.warning(
            "Dependency floor check SKIPPED via %s — this environment may be running below its juniper-* floors.",
            skip_env_var,
        )
        return

    resolved = _resolve_floors(floors, distribution, pyproject_path, prefix)
    if not resolved:
        log.debug("Dependency floor check: no %s* floors to enforce.", prefix)
        return

    violations = check_dependency_floors(resolved)
    if violations:
        message = f"Dependency floor check FAILED — installed juniper-* wheel(s) are below this service's declared floor(s). Reinstall/upgrade the environment before starting (or set {skip_env_var}=1 to bypass, at your own risk):\n" + _format_violations(violations)
        log.error(message)
        raise DependencyFloorError(message, violations=violations)

    log.info("Dependency floor check passed (%d %s* floor(s) satisfied).", len(resolved), prefix)
