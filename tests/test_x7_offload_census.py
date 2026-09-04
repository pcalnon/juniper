#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/ad-hoc/2026-09-04_x7_offload_census_v2.py`` (and a characterisation of v1).

``util/ad-hoc`` is outside every pre-commit Python hook, so this suite is the only check
on the census. X7 slice 1a's acceptance is "zero un-offloaded blocking calls in async
handlers" -- the census IS the test, and it has to be right in both directions.

What it pins
------------
1. **Site-local exemption, not expression-global.** Offloading ``backend.get_status`` at
   one site must NOT hide another ``backend.get_status()`` in a different handler. That
   was v0.2.0's unsoundness: because canopy ``main.py:3574`` offloads the name, every
   other ``backend.get_status()`` vanished -- including the three health endpoints X7 is
   defined by -- and the miss grew as work progressed (reported 39, true count 54).
   Reintroducing ``if expr in offloaded: continue`` turns this red.
2. **A nested closure handed to ``to_thread`` IS exempt.** That is the site-local rule
   the global skip replaced incorrectly.
3. **Provenance, not the bare name ``client``.** An ``httpx.AsyncClient`` bound as
   ``client`` is ASYNC (not a finding); the same name bound from ``get_redis_client`` is
   OTHER (blocking). v1 name-matching reported the awaited async client as blocking --
   the ruff ASYNC-hook class -- and is retained as that negative example.
4. **UNRESOLVED is fail-open for plausible I/O names, silent for helpers.** Unbound
   ``client.*`` counts as blocking; ``helper.foo()`` does not.
5. **CASCOR / LOCAL buckets.** ``backend`` roots and ``_require_service_adapter``
   bindings are CASCOR; ``DataAdapter`` is LOCAL and not in the blocking total.
"""

from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V2 = REPO_ROOT / "util" / "ad-hoc" / "2026-09-04_x7_offload_census_v2.py"
V1 = REPO_ROOT / "util" / "ad-hoc" / "2026-09-04_x7_offload_census.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


v2 = _load(V2, "x7_offload_census_v2")
v1 = _load(V1, "x7_offload_census_v1")


def _blocking(buckets: dict) -> list[tuple[int, str, str]]:
    return buckets["CASCOR"] + buckets["OTHER"] + buckets["UNRESOLVED"]


def _exprs(rows: list[tuple[int, str, str]]) -> set[str]:
    return {expr for _, _, expr in rows}


def _handlers(rows: list[tuple[int, str, str]]) -> set[str]:
    return {handler for _, handler, _ in rows}


TWIN_GET_STATUS = """\
import asyncio
backend = object()

async def health_check():
    return backend.get_status()

async def other():
    return await asyncio.to_thread(backend.get_status)
"""

OFFLOADED_CLOSURE = """\
import asyncio
backend = object()

async def handler():
    def _fetch():
        return backend.get_status()
    return await asyncio.to_thread(_fetch)
"""


class SiteLocalExemptionTest(unittest.TestCase):
    """The v0.2.0 hole: module-global expression skip certified a partial fix."""

    def test_offloading_one_get_status_does_not_hide_another(self) -> None:
        buckets = v2.census_source(TWIN_GET_STATUS)
        rows = [r for r in buckets["CASCOR"] if r[2] == "backend.get_status"]
        self.assertEqual(_handlers(rows), {"health_check"}, buckets)
        self.assertNotIn("other", _handlers(_blocking(buckets)))

    def test_offloaded_named_closure_is_exempt(self) -> None:
        buckets = v2.census_source(OFFLOADED_CLOSURE)
        self.assertEqual(_blocking(buckets), [], buckets)

    def test_direct_unoffloaded_backend_call_is_cascor(self) -> None:
        src = "async def handler():\n    return backend.get_status()\n"
        buckets = v2.census_source(src)
        self.assertEqual(_exprs(buckets["CASCOR"]), {"backend.get_status"})
        self.assertEqual(_blocking(buckets), buckets["CASCOR"])


class ProvenanceTest(unittest.TestCase):
    def test_async_client_bound_as_client_is_not_blocking(self) -> None:
        src = """\
import httpx
async def handler():
    async with httpx.AsyncClient() as client:
        return await client.get("http://x")
"""
        buckets = v2.census_source(src)
        self.assertEqual(_blocking(buckets), [], buckets)

    def test_redis_client_bound_as_client_is_other(self) -> None:
        src = """\
async def handler():
    client = get_redis_client()
    return client.get("k")
"""
        buckets = v2.census_source(src)
        self.assertEqual(_exprs(buckets["OTHER"]), {"client.get"})
        self.assertEqual(_blocking(buckets), buckets["OTHER"])

    def test_cassandra_client_is_other(self) -> None:
        src = """\
async def handler():
    client = get_cassandra_client()
    return client.execute("q")
"""
        buckets = v2.census_source(src)
        self.assertEqual(_exprs(buckets["OTHER"]), {"client.execute"})

    def test_require_service_adapter_binding_is_cascor(self) -> None:
        src = """\
async def handler():
    adapter = _require_service_adapter()
    return adapter.get_status()
"""
        buckets = v2.census_source(src)
        self.assertEqual(_exprs(buckets["CASCOR"]), {"adapter.get_status"})

    def test_backend_attribute_chain_is_cascor(self) -> None:
        src = """\
async def handler():
    return backend._adapter._client.get_status()
"""
        buckets = v2.census_source(src)
        self.assertEqual(_exprs(buckets["CASCOR"]), {"backend._adapter._client.get_status"})

    def test_data_adapter_is_local_not_blocking(self) -> None:
        src = """\
async def handler():
    adapter = DataAdapter()
    return adapter.compute()
"""
        buckets = v2.census_source(src)
        self.assertEqual(_exprs(buckets["LOCAL"]), {"adapter.compute"})
        self.assertEqual(_blocking(buckets), [])

    def test_unbound_client_is_unresolved_and_blocking(self) -> None:
        src = """\
async def handler():
    return client.get("k")
"""
        buckets = v2.census_source(src)
        self.assertEqual(_exprs(buckets["UNRESOLVED"]), {"client.get"})
        self.assertTrue(_blocking(buckets))

    def test_unknown_helper_is_not_reported(self) -> None:
        src = """\
async def handler():
    return helper.foo()
"""
        buckets = v2.census_source(src)
        self.assertEqual(_blocking(buckets), [])
        self.assertEqual(buckets["UNRESOLVED"], [])


class MainExitTest(unittest.TestCase):
    def test_main_exits_1_when_blocking_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.py"
            path.write_text(TWIN_GET_STATUS, encoding="utf-8")
            previous = v2.CANOPY_MAIN
            try:
                v2.CANOPY_MAIN = path
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(v2.main(), 1)
            finally:
                v2.CANOPY_MAIN = previous

    def test_main_exits_0_when_the_only_call_is_offloaded(self) -> None:
        src = """\
import asyncio
backend = object()
async def handler():
    return await asyncio.to_thread(backend.get_status)
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.py"
            path.write_text(src, encoding="utf-8")
            previous = v2.CANOPY_MAIN
            try:
                v2.CANOPY_MAIN = path
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(v2.main(), 0)
            finally:
                v2.CANOPY_MAIN = previous


class V1NegativeExampleTest(unittest.TestCase):
    """v1 is retained unsound on purpose -- pin that, so a silent 'fix' is a diff."""

    def test_v1_hides_the_twin_get_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.py"
            path.write_text(TWIN_GET_STATUS, encoding="utf-8")
            findings = v1.census(path)
        self.assertEqual(
            findings,
            [],
            "v1 is the negative example: the global expression skip must still hide health_check. "
            "If this fails, v1 was 'fixed' -- delete this characterisation or the file, do not leave a second unsound gate.",
        )

    def test_v1_reports_awaited_async_client_as_blocking(self) -> None:
        src = """\
import httpx
async def handler():
    async with httpx.AsyncClient() as client:
        return client.stream("GET", "http://x")
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "main.py"
            path.write_text(src, encoding="utf-8")
            findings = v1.census(path)
        self.assertEqual([call for _, _, call in findings], ["client.stream"])


if __name__ == "__main__":
    unittest.main()
