"""Smoke tests for ``juniper-service-core``.

Covers the two load-bearing properties of the scaffold:

1. The dependency-free top-level import path: ``import juniper_service_core`` exposes
   ``__version__`` without importing ``fastapi`` / ``pydantic-settings`` (verified in a
   subprocess that actively blocks those imports). This is what lets the TestPyPI
   publish-verify run a clean ``--no-deps`` import check.
2. ``create_app`` and ``SettingsBase`` are reachable lazily via PEP 562
   ``__getattr__`` once their dependencies are present.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path

import juniper_service_core

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _declared_version() -> str:
    """The canonical static ``[project].version`` -- never hardcode a literal here.

    A hardcoded ``"0.4.0"`` sat latent-red after the ml#702 dunder heal (this
    path-filtered CI only runs when ``juniper-service-core/**`` changes) -- the
    ml#701 stale-version class, in test form."""
    with _PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def test_version_is_exposed_eagerly():
    assert juniper_service_core.__version__ == _declared_version()


def test_lazy_public_surface_is_accessible():
    # Accessing these triggers the PEP 562 __getattr__ lazy imports.
    assert juniper_service_core.create_app is not None
    assert juniper_service_core.SettingsBase is not None
    assert callable(juniper_service_core.create_app)


def test_unknown_attribute_raises_attribute_error():
    try:
        juniper_service_core.does_not_exist  # noqa: B018  (intentional attribute access)
    except AttributeError:
        return
    raise AssertionError("expected AttributeError for unknown attribute")


def test_top_level_import_does_not_require_fastapi_or_pydantic_settings():
    """The top-level import must succeed with fastapi / pydantic_settings blocked.

    Run in a subprocess that installs a meta-path finder rejecting those modules, so a
    regression that pulls them in at module top level fails loudly here (and would break
    the ``--no-deps`` TestPyPI verify).
    """
    code = textwrap.dedent(
        """
        import sys

        _BLOCKED = ("fastapi", "pydantic_settings")

        class _DepBlocker:
            def find_spec(self, name, path=None, target=None):
                if name in _BLOCKED or any(name.startswith(b + ".") for b in _BLOCKED):
                    raise ImportError(f"{name} is intentionally blocked for this test")
                return None

        for mod in [m for m in list(sys.modules) if m in _BLOCKED or any(m.startswith(b + ".") for b in _BLOCKED)]:
            del sys.modules[mod]
        sys.meta_path.insert(0, _DepBlocker())

        import juniper_service_core

        assert juniper_service_core.__version__ == __EXPECTED_VERSION__
        assert "fastapi" not in sys.modules, "top-level import unexpectedly pulled fastapi"
        assert "pydantic_settings" not in sys.modules, "top-level import unexpectedly pulled pydantic_settings"
        # APD-SVCCORE-006: the package base exception is exported EAGERLY, so a consumer
        # can write ``except JuniperServiceCoreError`` without the lazy machinery
        # importing the optional deps to resolve the name. That is only true while
        # ``exceptions.py`` stays dependency-free, which this blocked-import run is what
        # actually proves.
        assert juniper_service_core.JuniperServiceCoreError is not None
        raise_ok = False
        try:
            raise juniper_service_core.JuniperServiceCoreError("x")
        except juniper_service_core.JuniperServiceCoreError:
            raise_ok = True
        assert raise_ok
        print("DEPENDENCY_FREE_OK")
        """
    ).replace("__EXPECTED_VERSION__", repr(_declared_version()))
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"subprocess failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert "DEPENDENCY_FREE_OK" in result.stdout
