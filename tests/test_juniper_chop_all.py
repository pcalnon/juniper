"""
Tests for util/juniper_chop_all.bash

Validates the parser / grep changes introduced in Pass 2 of the
2026-05-07 startup/shutdown scripts audit:

- Pid file parser accepts both the new `name=pid` format AND the legacy
  `name: pid` format (backward-compatibility window).
- Worker-cleanup grep no longer matches arbitrary processes that happen
  to contain `cascor` and `worker` separated by other tokens.
- ``validate_pid`` rejects stale / wrong-process PIDs by matching
  ``/proc/<pid>/cmdline`` against the pidfile service name (D-05 /
  JR-ML-SEC-045) — hermetic via ``JUNIPER_CHOP_PROC_ROOT``.

Where running the full chop script is impractical (requires root, a real
pid file, and a live process), tests run a self-contained extract of the
parser / validate_pid block in a subshell. Static-text assertions guard
the grep tightening change.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_chop_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 10


def _extract_validate_pid_function() -> str:
    """Pull ``_chop_normalize_token`` + ``validate_pid`` from the script (avoids harness drift)."""
    # validate_pid depends on the normalize helper; extract both in source order.
    helper = re.search(
        r"^function _chop_normalize_token\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    match = re.search(
        r"^function validate_pid\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if helper is None:
        raise AssertionError("_chop_normalize_token function not found in juniper_chop_all.bash")
    if match is None:
        raise AssertionError("validate_pid function not found in juniper_chop_all.bash")
    return helper.group(0) + match.group(0)


class TestSyntax(unittest.TestCase):
    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestPidParser(unittest.TestCase):
    """The parser block must accept both `=` and `:` delimiters."""

    PARSER_HARNESS = """
        set -euo pipefail
        raw="$1"
        if [[ "${raw}" == *=* ]]; then
            name="${raw%%=*}"
            pid="${raw#*=}"
        else
            name="${raw%%:*}"
            pid="$(echo "${raw#*:}" | tr -d ' ')"
        fi
        name="${name## }"
        name="${name%% }"
        echo "name=${name} pid=${pid}"
    """

    def _parse(self, line: str) -> str:
        result = subprocess.run(
            ["bash", "-c", self.PARSER_HARNESS, "_", line],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return result.stdout.strip()

    def test_new_format_simple(self) -> None:
        self.assertEqual(self._parse("juniper-data=12345"), "name=juniper-data pid=12345")

    def test_new_format_with_dashes_in_name(self) -> None:
        self.assertEqual(
            self._parse("juniper-cascor-worker=98765"),
            "name=juniper-cascor-worker pid=98765",
        )

    def test_legacy_colon_format(self) -> None:
        self.assertEqual(
            self._parse("juniper-data:           12345"),
            "name=juniper-data pid=12345",
        )

    def test_legacy_colon_format_with_single_space(self) -> None:
        self.assertEqual(
            self._parse("juniper-cascor: 9999"),
            "name=juniper-cascor pid=9999",
        )


class TestParserBlockMatchesHarness(unittest.TestCase):
    """The parser block in the script must contain the dual-delimiter logic."""

    def test_equals_branch_present(self) -> None:
        self.assertIn('if [[ "${JUNIPER_PIDFILE_LINE_RAW}" == *=* ]]; then', SCRIPT_TEXT)

    def test_legacy_branch_present(self) -> None:
        # The else-branch with the colon-and-tr fallback.
        self.assertIn("${JUNIPER_PIDFILE_LINE_RAW#*:}", SCRIPT_TEXT)


class TestWorkerGrepTightening(unittest.TestCase):
    """Audit fix #11 — over-greedy `cascor.*worker` alternative removed."""

    def test_overgreedy_alternative_removed(self) -> None:
        # The old grep contained `cascor.*worker` as a third alternative
        # inside a quoted regex. That live alternation must not appear in the
        # active grep call. (The comment block above the grep call still
        # references the term to explain the rationale; that's intentional.)
        self.assertNotIn("cascor.*worker\\|", SCRIPT_TEXT)
        self.assertNotIn("\\|cascor.*worker", SCRIPT_TEXT)

    def test_strict_variants_present(self) -> None:
        # The dash and underscore variants must still be matched.
        self.assertIn("juniper-cascor-worker", SCRIPT_TEXT)
        self.assertIn("juniper_cascor_worker", SCRIPT_TEXT)


class TestSystemdModePreserved(unittest.TestCase):
    """Pass 2 must not touch the systemd codepath in chop."""

    def test_systemd_loop_intact(self) -> None:
        self.assertIn(
            "for svc in juniper-cascor-worker juniper-canopy juniper-cascor juniper-data",
            SCRIPT_TEXT,
        )


class TestIntentionalEchoDuplicatesPreserved(unittest.TestCase):
    """Per memory `feedback_chop_all_echo_debug`, duplicate echo lines around
    SIGTERM_TIMEOUT / KILL_WORKERS are intentional placeholders. The audit
    must NOT have removed them."""

    def test_sigterm_echo_appears_at_least_twice(self) -> None:
        count = SCRIPT_TEXT.count('SIGTERM_TIMEOUT=\\"${SIGTERM_TIMEOUT}\\"')
        self.assertGreaterEqual(count, 2, "intentional duplicate echo lines were removed")


class TestValidatePid(unittest.TestCase):
    """D-05 / JR-ML-SEC-045: cmdline must match the pidfile service name.

    A reused PID pointing at an unrelated process must return 1 so chop never
    SIGTERM/SIGKILLs the wrong process. Hermetic via ``JUNIPER_CHOP_PROC_ROOT``.
    """

    def _run_validate_pid(self, proc_root: Path, pid: str, expected_name: str) -> subprocess.CompletedProcess[str]:
        harness = f"""
            set -euo pipefail
            JUNIPER_SCRIPT_NAME="juniper_chop_all.bash"
            JUNIPER_CHOP_PROC_ROOT="{proc_root}"
            {_extract_validate_pid_function()}
            set +e
            validate_pid "$1" "$2"
            status=$?
            set -e
            echo "STATUS=${{status}}"
            exit 0
        """
        env = RedactedEnv(os.environ)
        return subprocess.run(
            ["bash", "-c", harness, "_", pid, expected_name],
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )

    def _add_proc(self, proc_root: Path, pid: int, cmdline_parts: list[str]) -> None:
        process_dir = proc_root / str(pid)
        process_dir.mkdir(parents=True)
        (process_dir / "cmdline").write_bytes(b"\0".join(part.encode("utf-8") for part in cmdline_parts) + b"\0")

    def test_matching_underscore_module_path_is_accepted(self) -> None:
        # plant launches uvicorn juniper_data... while pidfile key is juniper-data.
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            self._add_proc(
                proc_root,
                4242,
                ["/opt/conda/envs/JuniperData1/bin/python", "-m", "uvicorn", "juniper_data.api.app:get_app"],
            )
            result = self._run_validate_pid(proc_root, "4242", "juniper-data")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=0", result.stdout)

    def test_plant_cascor_conda_env_cmdline_is_accepted(self) -> None:
        # plant: nohup "$JUNIPER_CASCOR_PYTHON" server.py  (relative module; token is JuniperCascor1).
        # Literal juniper-cascor / juniper_cascor substring matching false-rejects this and
        # leaves cascor running while chop clears the PID file.
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            self._add_proc(
                proc_root,
                4343,
                ["/opt/miniforge3/envs/JuniperCascor1/bin/python", "server.py"],
            )
            result = self._run_validate_pid(proc_root, "4343", "juniper-cascor")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=0", result.stdout)

    def test_plant_canopy_conda_env_cmdline_is_accepted(self) -> None:
        # plant: nohup "$JUNIPER_CANOPY_PYTHON" main.py under JuniperCanopy1.
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            self._add_proc(
                proc_root,
                4545,
                ["/opt/miniforge3/envs/JuniperCanopy1/bin/python", "main.py"],
            )
            result = self._run_validate_pid(proc_root, "4545", "juniper-canopy")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=0", result.stdout)

    def test_hyphenated_binary_name_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            self._add_proc(
                proc_root,
                5151,
                ["/opt/conda/envs/JuniperCascor1/bin/juniper-cascor-worker", "--health-port", "8210"],
            )
            result = self._run_validate_pid(proc_root, "5151", "juniper-cascor-worker")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=0", result.stdout)

    def test_unrelated_cmdline_is_rejected(self) -> None:
        # Stale PID reused by sshd — must NOT return 0 (would kill the wrong process).
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            self._add_proc(proc_root, 6060, ["/usr/sbin/sshd", "-D"])
            result = self._run_validate_pid(proc_root, "6060", "juniper-canopy")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("does not match expected service", result.stdout)

    def test_cascor_does_not_match_worker_cmdline(self) -> None:
        # juniper-cascor substring would otherwise match juniper_cascor_worker.
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            self._add_proc(
                proc_root,
                7070,
                ["/opt/conda/envs/JuniperCascor1/bin/python", "-m", "juniper_cascor_worker"],
            )
            result = self._run_validate_pid(proc_root, "7070", "juniper-cascor")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("looks like a worker", result.stdout)

    def test_missing_proc_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            proc_root.mkdir()
            result = self._run_validate_pid(proc_root, "99999", "juniper-data")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("is not running", result.stdout)

    def test_non_numeric_pid_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            proc_root.mkdir()
            result = self._run_validate_pid(proc_root, "not-a-pid", "juniper-data")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("Invalid PID", result.stdout)

    def test_empty_cmdline_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_root = Path(tmpdir) / "proc"
            process_dir = proc_root / "8080"
            process_dir.mkdir(parents=True)
            (process_dir / "cmdline").write_bytes(b"")
            result = self._run_validate_pid(proc_root, "8080", "juniper-data")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("empty/unreadable cmdline", result.stdout)

    def test_script_wires_proc_root_override(self) -> None:
        # Drift guard: the live function must honour JUNIPER_CHOP_PROC_ROOT.
        self.assertIn("JUNIPER_CHOP_PROC_ROOT", SCRIPT_TEXT)
        self.assertIn("${JUNIPER_CHOP_PROC_ROOT:-/proc}", SCRIPT_TEXT)


if __name__ == "__main__":
    unittest.main()
