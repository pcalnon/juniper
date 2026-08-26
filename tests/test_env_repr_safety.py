"""Lint + behaviour gate for the env-repr secret-leak class (tests/redacted_env.py).

The class: a test builds ``env = os.environ.copy()`` (or ``dict(os.environ)`` /
``{**os.environ}``) for ``subprocess.run``; on a failure, pytest-style
``--showlocals`` / rich-traceback runs render that frame-local through ``saferepr``
(alphabetically sorted + truncated), putting real secrets at the visible head of
the paste. The fix is building the mapping as ``tests.redacted_env.RedactedEnv``,
whose repr is masked.

This module is the sole gate: the LINT half forbids raw ``os.environ``-derived
mapping construction anywhere under ``tests/``; the BEHAVIOUR half proves the
wrapper masks its repr, keeps dict semantics, and drives a real subprocess.
``unittest.mock.patch.dict(os.environ, ...)`` (in-process env patching, not a
subprocess mapping) is deliberately NOT flagged.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

_TESTS_DIR = Path(__file__).resolve().parent

#: Raw env-mapping constructions that must not appear in test code. ``**os.environ``
#: (rather than ``{**os.environ``) also catches the multi-line spread form; the
#: negative lookbehind exempts ``[mock.]patch.dict(os.environ, ...)``.
_RAW_ENV_PATTERN = re.compile(r"os\.environ\.copy\(\)|(?<!patch\.)\bdict\(os\.environ|\*\*os\.environ")

#: Files allowed to mention the raw patterns (the wrapper itself and this gate).
_ALLOWED_FILES = {"redacted_env.py", "test_env_repr_safety.py"}


class EnvReprLintTest(unittest.TestCase):
    """No test file may construct a raw os.environ-derived mapping."""

    def test_no_raw_environ_derived_mappings_in_tests(self):
        offenders: list[str] = []
        for path in sorted(_TESTS_DIR.glob("*.py")):
            if path.name in _ALLOWED_FILES:
                continue
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if _RAW_ENV_PATTERN.search(line):
                    offenders.append(f"{path.name}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], msg="Raw os.environ-derived mappings leak secrets via frame-local reprs; build them with tests.redacted_env.RedactedEnv instead: " + "; ".join(offenders))

    def test_scanner_bites_on_synthetic_violations(self):
        # The gate must actually detect each raw form (the negative case that
        # proves this lint is live -- house convention).
        self.assertTrue(_RAW_ENV_PATTERN.search("env = os.environ.copy()"))
        self.assertTrue(_RAW_ENV_PATTERN.search("env = dict(os.environ, FOO='bar')"))
        self.assertTrue(_RAW_ENV_PATTERN.search("env = {**os.environ, 'FOO': 'bar'}"))
        self.assertTrue(_RAW_ENV_PATTERN.search("    **os.environ,"))  # multi-line spread form

    def test_scanner_ignores_in_process_env_patching(self):
        self.assertIsNone(_RAW_ENV_PATTERN.search("with patch.dict(os.environ, {'FOO': 'bar'}):"))
        self.assertIsNone(_RAW_ENV_PATTERN.search("with mock.patch.dict(os.environ, {'FOO': 'bar'}):"))


class RedactedEnvBehaviourTest(unittest.TestCase):
    """The wrapper masks reprs while behaving as a normal subprocess env mapping."""

    def test_repr_and_str_render_no_keys_or_values(self):
        env = RedactedEnv({"HOME": "/nowhere"}, SECRET_TOKEN="hunter2")  # nosec B106 — deliberately secret-shaped test value; the assertions prove it never renders
        for rendered in (repr(env), str(env), f"{env}"):
            self.assertNotIn("hunter2", rendered)
            self.assertNotIn("SECRET_TOKEN", rendered)
            self.assertNotIn("/nowhere", rendered)
            self.assertIn("RedactedEnv", rendered)

    def test_dict_semantics_and_copy_preserve_redaction(self):
        env = RedactedEnv({"A": "1"}, B="2")
        env["PATH"] = "/usr/bin"
        self.assertEqual(env["A"], "1")
        self.assertEqual(env.get("B"), "2")
        clone = env.copy()
        self.assertIsInstance(clone, RedactedEnv)
        self.assertEqual(dict(clone), dict(env))
        self.assertNotIn("/usr/bin", repr(clone))

    def test_subprocess_child_sees_injected_vars(self):
        import os

        env = RedactedEnv(os.environ, ENV_REPR_SAFETY_PROBE="ok")
        proc = subprocess.run([sys.executable, "-c", "import os; print(os.environ['ENV_REPR_SAFETY_PROBE'])"], env=env, capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(proc.stdout.strip(), "ok")


if __name__ == "__main__":
    unittest.main()
