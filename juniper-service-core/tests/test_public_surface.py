"""APD-SVCCORE-009 / APD-SVCCORE-017 — the package's public surface.

``-009``: the surface is declared three times in ``__init__.py`` -- ``__all__``, the
``_LAZY_EXPORTS`` name->module map that PEP 562 ``__getattr__`` resolves through, and a
``TYPE_CHECKING`` import block that exists so static analysis can see the same names. All
three are maintained by hand and nothing checked that they agree. They do agree today,
which is exactly when a guard is worth adding: the failure mode is a name that is exported
but unresolvable (``AttributeError`` for a consumer) or resolvable but invisible to type
checkers, and neither shows up until someone hits it.

``-017``: ``__dir__`` returned ``sorted(__all__)``. Defining ``__dir__`` *replaces* the
default rather than extending it, so that made ``dir()`` a strictly smaller view than the
module -- ``__name__``, ``__file__``, ``__doc__``, ``__path__`` and every eagerly bound
name all vanished.

The lists are read from source with ``ast`` rather than from the imported module, because
``TYPE_CHECKING`` is ``False`` at run time: its block is invisible to a live import, and
that block is one of the three things under test.
"""

from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

# Names in ``__all__`` that are bound eagerly at module import and therefore are
# deliberately absent from ``_LAZY_EXPORTS``. Both are dependency-free, which is why they
# can be eager without costing the dependency-free-import guarantee.
EAGER_EXPORTS = frozenset({"__version__", "JuniperServiceCoreError"})

_INIT = Path(__file__).resolve().parents[1] / "juniper_service_core" / "__init__.py"


def _declared_surface() -> tuple[list[str], list[str], list[str]]:
    """``(__all__, _LAZY_EXPORTS keys, TYPE_CHECKING imported names)`` read from source."""
    tree = ast.parse(_INIT.read_text(encoding="utf-8"))
    all_names: list[str] = []
    lazy_names: list[str] = []
    type_checking: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = getattr(target, "id", "")
                if name == "__all__" and isinstance(node.value, ast.List):
                    all_names = [e.value for e in node.value.elts]
                elif name == "_LAZY_EXPORTS" and isinstance(node.value, ast.Dict):
                    lazy_names = [k.value for k in node.value.keys]
        elif isinstance(node, ast.If) and getattr(node.test, "id", "") == "TYPE_CHECKING":
            for stmt in node.body:
                if isinstance(stmt, ast.ImportFrom):
                    type_checking.extend(alias.name for alias in stmt.names)
    return all_names, lazy_names, type_checking


class TestPublicSurfaceListsAgree:
    """APD-SVCCORE-009."""

    def test_the_parse_found_all_three_lists(self) -> None:
        """Anti-vacuous guard: every comparison below is trivially true on empty lists."""
        all_names, lazy_names, type_checking = _declared_surface()

        assert len(all_names) > 50, f"__all__ parse returned {len(all_names)} names"
        assert len(lazy_names) > 50, f"_LAZY_EXPORTS parse returned {len(lazy_names)} names"
        assert len(type_checking) > 50, f"TYPE_CHECKING parse returned {len(type_checking)} names"

    def test_type_checking_block_matches_the_lazy_map(self) -> None:
        """A name lazily resolvable but absent here is invisible to every type checker."""
        _all_names, lazy_names, type_checking = _declared_surface()

        assert set(type_checking) == set(lazy_names), f"only in TYPE_CHECKING: {sorted(set(type_checking) - set(lazy_names))}; only in _LAZY_EXPORTS: {sorted(set(lazy_names) - set(type_checking))}"

    def test_all_is_exactly_the_lazy_names_plus_the_eager_ones(self) -> None:
        """The failure this catches is an ``__all__`` entry nothing can resolve.

        ``from juniper_service_core import *`` would raise ``AttributeError`` on it, and
        ``__getattr__`` would too -- the name exists only in a list.
        """
        all_names, lazy_names, _type_checking = _declared_surface()

        assert set(all_names) == set(lazy_names) | EAGER_EXPORTS

    def test_no_duplicates_in_any_list(self) -> None:
        all_names, lazy_names, type_checking = _declared_surface()

        for label, names in (("__all__", all_names), ("_LAZY_EXPORTS", lazy_names), ("TYPE_CHECKING", type_checking)):
            assert len(names) == len(set(names)), f"{label} has duplicates"

    def test_every_exported_name_actually_resolves(self) -> None:
        """The behavioural half: the lists agreeing is worthless if the names are wrong.

        A typo'd module path in ``_LAZY_EXPORTS`` passes every list comparison above and
        fails only here, at the ``__getattr__`` that a consumer would hit.
        """
        root = import_module("juniper_service_core")
        all_names, _lazy, _tc = _declared_surface()

        unresolvable = []
        for name in all_names:
            try:
                getattr(root, name)
            except Exception as exc:  # noqa: BLE001 - the point is to report, not to raise
                unresolvable.append(f"{name}: {type(exc).__name__}: {exc}")
        assert not unresolvable, "exported but unresolvable:\n" + "\n".join(unresolvable)

    def test_eager_exports_really_are_eager(self) -> None:
        """Pins the exception this guard encodes, so it cannot quietly grow.

        ``EAGER_EXPORTS`` is the one place the three-list invariant is allowed to differ.
        If a third name is added there without actually being bound at import, the
        invariant silently weakens.
        """
        root = import_module("juniper_service_core")

        for name in EAGER_EXPORTS:
            assert name in vars(root), f"{name} is declared eager but is not bound at import"


class TestDirExposesTheModule:
    """APD-SVCCORE-017."""

    def test_dir_includes_the_lazy_public_surface(self) -> None:
        """The reason a PEP 562 module defines ``__dir__`` at all."""
        root = import_module("juniper_service_core")

        assert set(root.__all__) <= set(dir(root))

    def test_dir_does_not_hide_the_module_s_own_attributes(self) -> None:
        """Defining ``__dir__`` replaces the default; returning ``__all__`` alone shrank it.

        ``__name__`` / ``__file__`` / ``__doc__`` are what ``inspect`` and REPL completion
        read, and they were all missing.
        """
        root = import_module("juniper_service_core")
        listed = set(dir(root))

        for attr in ("__name__", "__file__", "__doc__", "__path__", "__version__"):
            assert attr in listed, f"dir() hides {attr}"

    def test_dir_is_sorted_and_free_of_duplicates(self) -> None:
        """It is a union of two overlapping collections, so both are worth asserting."""
        root = import_module("juniper_service_core")
        listed = dir(root)

        assert listed == sorted(listed)
        assert len(listed) == len(set(listed))
