"""The package's base exception (APD-SVCCORE-006).

Before this existed, the five exceptions this package raises had nothing in common. Three
subclassed ``RuntimeError`` and two ``KeyError``, so the only way a consumer could catch
"anything juniper-service-core raises" was to name all five, and the only way to catch
them by category was ``except RuntimeError`` -- which also swallows every unrelated
runtime failure in the call, including ones that mean the process should die.

Every exception in the package now derives from :class:`JuniperServiceCoreError` **in
addition to** its original base, never instead of it. That ordering matters: an existing
``except RuntimeError`` or ``except KeyError`` handler in a consuming service keeps
working exactly as before, so this is additive. ``SnapshotNotFoundError`` in particular is
raised where a mapping lookup would be, and callers legitimately treat it as a ``KeyError``.

This module is deliberately dependency-free so the package root can import it eagerly
without breaking the dependency-free ``import juniper_service_core`` guarantee.
"""

from __future__ import annotations

__all__ = ["JuniperServiceCoreError"]


class JuniperServiceCoreError(Exception):
    """Base class for every exception raised by ``juniper_service_core``.

    Catch this to handle any failure originating in this package without also catching
    unrelated ``RuntimeError`` / ``KeyError`` from the surrounding call.
    """
