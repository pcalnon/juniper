"""
Tests for util/global_text_search.bash.

Pins the empty-query hard-fail and the exclude-dir / exclude-file argv compose
that the operator search helper forwards to grep. Uses a PATH-stub grep that
logs argv so CI never depends on real recursive search of the checkout.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "global_text_search.bash"
SCRIPT_TIMEOUT_SECONDS: int = 15


def write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    path.chmod(0o755)


def _run_script(
    *args: str,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env if env is not None else RedactedEnv(os.environ),
        cwd=cwd,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestGlobalTextSearchGates(unittest.TestCase):
    """CLI validation and exclude-argv compose."""

    def test_no_args_exits_one_with_missing_term_message(self):
        result = _run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Source Code Search Term NOT Provided", result.stdout)

    def test_empty_string_arg_exits_one_with_missing_term_message(self):
        result = _run_script("")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Source Code Search Term NOT Provided", result.stdout)

    def test_search_forwards_excludes_term_and_default_location_to_grep(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            argv_log = root / "grep_argv.log"
            write_executable(
                bin_dir / "grep",
                f"""
                #!/usr/bin/env bash
                printf '%s\\0' "$@" >> "{argv_log}"
                printf '\\n' >> "{argv_log}"
                exit 0
                """,
            )
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

            result = _run_script("remote_client", env=env)
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertTrue(argv_log.is_file(), msg="stub grep never ran")
            recorded = argv_log.read_text(encoding="utf-8")
            # NUL-joined argv from the stub (one call, trailing newline).
            argv = [part for part in recorded.rstrip("\n").split("\0") if part != ""]
            self.assertIn("--exclude-dir", argv)
            self.assertIn("notes", argv)
            self.assertIn("prompts", argv)
            self.assertIn("--exclude", argv)
            self.assertIn("CHANGELOG.md", argv)
            self.assertIn("AGENTS.md", argv)
            self.assertIn("-r", argv)
            self.assertIn("-n", argv)
            self.assertIn("-I", argv)
            self.assertIn("remote_client", argv)
            # Default search location is the final grep operand.
            self.assertEqual(argv[-1], ".", msg=f"argv={argv!r}")
            self.assertEqual(argv[-2], "remote_client", msg=f"argv={argv!r}")

    def test_custom_location_is_forwarded_as_final_grep_arg(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bin_dir = root / "bin"
            search_root = root / "src"
            search_root.mkdir()
            bin_dir.mkdir()
            argv_log = root / "grep_argv.log"
            write_executable(
                bin_dir / "grep",
                f"""
                #!/usr/bin/env bash
                printf '%s\\0' "$@" >> "{argv_log}"
                printf '\\n' >> "{argv_log}"
                exit 0
                """,
            )
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

            result = _run_script("needle", str(search_root), env=env)
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            recorded = argv_log.read_text(encoding="utf-8")
            self.assertIn("needle", recorded)
            self.assertIn(str(search_root), recorded)


if __name__ == "__main__":
    unittest.main()
