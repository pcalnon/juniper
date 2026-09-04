#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/2026-08-26_p5_fleet_state.py`` -- the P5 fleet census
that reports whether ``Memory Budget`` is still ``--advisory`` and whether it is
a required context.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the
gate. Hermetic: ``subprocess.run`` / ``gh_api`` / ``time.sleep`` are replaced;
nothing talks to GitHub.

What it pins, and why the roster pin in ``tests/test_require_context_safely.py``
cannot see it:

- ``_size_check_is_advisory`` reconstructs the ``memory_budget_check.py``
  invocation. ``"--advisory" in wf`` read True fleet-wide on 2026-08-26 because
  every de-advisory workflow mentions the flag in a comment, and juniper-ml
  keeps a real ``--advisory`` on the SEPARATE ``relocation_check.py`` line.
- ``gh_api`` returns ``None`` only on HTTP 404. Any other non-2xx (rate-limit,
  5xx) must raise after retries -- a false ``None`` is "the file is absent",
  which invents or hides step-e work (ml#1403).
- File sizes are ``len()`` of decoded text (CHARS). The GitHub ``size`` field
  is BYTES; using it concluded two repos were over ceiling when both sat
  exactly at it.
- ``memory_budget_required`` is an exact context-name match. A near-miss must
  not count.

Run: python3 -m unittest -v tests/test_p5_fleet_state.py
"""

from __future__ import annotations

import base64
import importlib.util
import json
import unittest
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-26_p5_fleet_state.py"


def _load():
    spec = importlib.util.spec_from_file_location("p5_fleet_state", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


# Comment mentions the removed flag; relocation_check keeps a live --advisory.
# Whole-file substring is True; the reconstructed invocation is False.
BLOCKING_WF = """\
# Memory Budget (BLOCKING) -- `--advisory` (the soak setting) is gone.
python3 util/memory_budget_check.py \\
  --base-ref FETCH_HEAD \\
  --trailers-file memory-budget-trailers.txt

python3 util/relocation_check.py \\
  --base FETCH_HEAD --head HEAD \\
  --advisory
"""

ADVISORY_WF = """\
python3 util/memory_budget_check.py \\
  --base-ref FETCH_HEAD \\
  --advisory
"""

INLINE_COMMENT_WF = """\
python3 util/memory_budget_check.py --base-ref FETCH_HEAD  # --advisory was removed
"""

COMMENTED_INVOCATION_WF = """\
# python3 util/memory_budget_check.py --advisory
python3 util/memory_budget_check.py --base-ref FETCH_HEAD
"""

UNITTEST_MENTION_WF = """\
python3 -m unittest -v tests/test_memory_budget_check.py
python3 util/memory_budget_check.py --base-ref FETCH_HEAD
"""

NO_INVOCATION_WF = """\
# no memory-budget job on this workflow
echo hello
"""


class SizeCheckAdvisoryTest(unittest.TestCase):
    """The 2026-08-26 whole-file substring false alarm."""

    def test_comment_and_relocation_advisory_do_not_count(self) -> None:
        """NEGATIVE CONTROL. The live juniper-ml shape.

        A whole-file ``"--advisory" in wf`` is True here (comment + relocation
        invocation). The census must still report BLOCKING / not-advisory.
        """
        self.assertIn("--advisory", BLOCKING_WF)
        self.assertFalse(mod._size_check_is_advisory(BLOCKING_WF))

    def test_live_memory_budget_advisory_flag_is_advisory(self) -> None:
        self.assertTrue(mod._size_check_is_advisory(ADVISORY_WF))

    def test_inline_comment_mention_is_stripped(self) -> None:
        self.assertFalse(mod._size_check_is_advisory(INLINE_COMMENT_WF))

    def test_commented_out_invocation_is_ignored(self) -> None:
        self.assertFalse(mod._size_check_is_advisory(COMMENTED_INVOCATION_WF))

    def test_unittest_mention_is_not_an_invocation(self) -> None:
        self.assertFalse(mod._size_check_is_advisory(UNITTEST_MENTION_WF))

    def test_missing_invocation_is_not_advisory(self) -> None:
        self.assertFalse(mod._size_check_is_advisory(NO_INVOCATION_WF))

    def test_same_line_advisory_is_advisory(self) -> None:
        self.assertTrue(
            mod._size_check_is_advisory("python3 util/memory_budget_check.py --advisory\n")
        )


class GhApiFailClosedTest(unittest.TestCase):
    """404 is the only benign None. Everything else must raise."""

    def setUp(self) -> None:
        self._run = mod.subprocess.run
        self._sleep = mod.time.sleep

    def tearDown(self) -> None:
        mod.subprocess.run = self._run
        mod.time.sleep = self._sleep

    @staticmethod
    def _proc(returncode: int, stdout: str = "", stderr: str = "") -> SimpleNamespace:
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    def test_2xx_json_returns_the_object(self) -> None:
        mod.subprocess.run = lambda *a, **k: self._proc(0, stdout='{"ok": true}')
        self.assertEqual(mod.gh_api("repos/x/y"), {"ok": True})

    def test_http_404_is_none(self) -> None:
        mod.subprocess.run = lambda *a, **k: self._proc(1, stderr="gh: HTTP 404: Not Found")
        self.assertIsNone(mod.gh_api("repos/x/y/contents/missing"))

    def test_json_status_404_is_none(self) -> None:
        mod.subprocess.run = lambda *a, **k: self._proc(1, stderr='{"status":"404","message":"Not Found"}')
        self.assertIsNone(mod.gh_api("repos/x/y/contents/missing"))

    def test_rate_limit_raises_instead_of_none(self) -> None:
        sleeps: list[float] = []
        mod.time.sleep = sleeps.append
        mod.subprocess.run = lambda *a, **k: self._proc(1, stderr="HTTP 403: API rate limit exceeded")
        with self.assertRaises(RuntimeError) as ctx:
            mod.gh_api("repos/x/y/contents/AGENTS.md")
        self.assertIn("rate limit", str(ctx.exception))
        self.assertNotIn("None", str(ctx.exception))
        self.assertEqual(len(sleeps), 4)

    def test_unparseable_2xx_raises_immediately(self) -> None:
        calls = {"n": 0}

        def _run(*a, **k):
            calls["n"] += 1
            return self._proc(0, stdout="not-json")

        mod.subprocess.run = _run
        mod.time.sleep = lambda *_a, **_k: self.fail("must not retry a 2xx parse error")
        with self.assertRaises(RuntimeError) as ctx:
            mod.gh_api("repos/x/y")
        self.assertIn("unparseable", str(ctx.exception))
        self.assertEqual(calls["n"], 1)


class ContentsCharCountTest(unittest.TestCase):
    """Decoded-text ``len()`` is CHARS. GitHub ``size`` is BYTES."""

    def setUp(self) -> None:
        self._orig = mod.gh_api

    def tearDown(self) -> None:
        mod.gh_api = self._orig

    def test_multibyte_glyph_is_one_char_not_two_bytes(self) -> None:
        text = "é"  # U+00E9 -- 2 UTF-8 bytes, 1 char
        payload = {
            "encoding": "base64",
            "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
            "size": len(text.encode("utf-8")),
        }
        self.assertEqual(payload["size"], 2)

        def _gh(path: str):
            self.assertIn("contents/", path)
            return payload

        mod.gh_api = _gh
        decoded = mod.contents("juniper-ml", "AGENTS.md")
        self.assertEqual(decoded, text)
        self.assertEqual(len(decoded), 1)
        self.assertNotEqual(len(decoded), payload["size"])

    def test_non_base64_payload_is_absent(self) -> None:
        mod.gh_api = lambda path: [{"name": "dir-listing"}]
        self.assertIsNone(mod.contents("juniper-ml", "docs"))


class RequiredContextExactNameTest(unittest.TestCase):
    def setUp(self) -> None:
        self._orig = mod.gh_api

    def tearDown(self) -> None:
        mod.gh_api = self._orig

    def test_memory_budget_exact_match(self) -> None:
        mod.gh_api = lambda path: [
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [
                        {"context": "tests"},
                        {"context": "Memory Budget"},
                    ]
                },
            }
        ]
        names = mod.required_contexts("juniper-ml")
        self.assertIn(mod.CONTEXT, names)
        self.assertTrue(mod.CONTEXT in names)

    def test_near_miss_name_is_not_memory_budget(self) -> None:
        """NEGATIVE CONTROL. A similarly-named check must not count as required."""
        mod.gh_api = lambda path: [
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [
                        {"context": "Memory Budget (Python 3.12)"},
                        {"context": "tests"},
                    ]
                },
            }
        ]
        names = mod.required_contexts("juniper-ml")
        self.assertNotIn(mod.CONTEXT, names)

    def test_non_list_rules_payload_is_empty(self) -> None:
        mod.gh_api = lambda path: {"message": "wrong shape"}
        self.assertEqual(mod.required_contexts("juniper-ml"), [])


class CensusRequiredAndCharsTest(unittest.TestCase):
    """``census`` consumes the helpers: exact required match + char headroom."""

    def setUp(self) -> None:
        self._orig = mod.gh_api

    def tearDown(self) -> None:
        mod.gh_api = self._orig

    def test_census_reports_chars_and_exact_required(self) -> None:
        agents = "é" * 10  # 10 chars, 20 bytes
        budget = json.dumps(
            {"files": {"AGENTS.md": {"ceiling_chars": 10}}},
            indent=2,
        )
        wf = BLOCKING_WF
        ref = "Memory Budget is BLOCKING\n"

        def _b64(text: str) -> dict:
            raw = text.encode("utf-8")
            return {
                "encoding": "base64",
                "content": base64.b64encode(raw).decode("ascii"),
                "size": len(raw),
            }

        def _gh(path: str):
            if path.endswith("/commits/main"):
                return {"sha": "abcdef12deadbeef"}
            if "/rules/branches/main" in path:
                return [
                    {
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [
                                {"context": "Memory Budget"},
                                {"context": "tests"},
                            ]
                        },
                    }
                ]
            if "conf/memory_budget.json" in path:
                return _b64(budget)
            if path.endswith("/AGENTS.md?ref=main"):
                return _b64(agents)
            if "ci.yml" in path:
                return _b64(wf)
            if "REFERENCE.md" in path:
                return _b64(ref)
            raise AssertionError(f"unexpected gh_api path: {path}")

        mod.gh_api = _gh
        row = mod.census("juniper-ml", None, ".github/workflows/ci.yml")
        self.assertTrue(row["memory_budget_required"])
        self.assertFalse(row["advisory_flag"])
        self.assertEqual(row["banner"], "BLOCKING")
        self.assertEqual(row["files"][0]["chars"], 10)
        self.assertEqual(row["files"][0]["headroom"], 0)
        # Bytes would have been 20 and invented a 10-char overrun.
        self.assertNotEqual(row["files"][0]["chars"], len(agents.encode("utf-8")))

    def test_census_near_miss_required_is_false(self) -> None:
        def _b64(text: str) -> dict:
            raw = text.encode("utf-8")
            return {
                "encoding": "base64",
                "content": base64.b64encode(raw).decode("ascii"),
                "size": len(raw),
            }

        def _gh(path: str):
            if path.endswith("/commits/main"):
                return {"sha": "abcdef12"}
            if "/rules/branches/main" in path:
                return [
                    {
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [
                                {"context": "Memory Budget (Python 3.12)"},
                            ]
                        },
                    }
                ]
            if "conf/memory_budget.json" in path:
                return None
            if "ci.yml" in path:
                return _b64(BLOCKING_WF)
            if "REFERENCE.md" in path or path.endswith("/AGENTS.md?ref=main"):
                return None
            raise AssertionError(f"unexpected gh_api path: {path}")

        mod.gh_api = _gh
        row = mod.census("juniper-ml", None, ".github/workflows/ci.yml")
        self.assertFalse(row["memory_budget_required"])


if __name__ == "__main__":
    unittest.main()
