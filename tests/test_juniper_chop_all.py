"""
Tests for util/juniper_chop_all.bash

Validates the parser / grep changes introduced in Pass 2 of the
2026-05-07 startup/shutdown scripts audit:

- Pid file parser accepts both the new `name=pid` format AND the legacy
  `name: pid` format (backward-compatibility window).
- Worker-cleanup grep no longer matches arbitrary processes that happen
  to contain `cascor` and `worker` separated by other tokens.
- ``graceful_stop`` SIGTERM→wait→SIGKILL escalate (and already-exited
  PID) — hermetic extract against real short-lived child processes.

Where running the full chop script is impractical (requires root, a real
pid file, and a live process), tests run a self-contained extract of the
parser / graceful_stop block in a subshell. Static-text assertions guard
the grep tightening change and the STOP_FAILURES / pidfile-preserve wire.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_chop_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 10
GRACEFUL_STOP_TIMEOUT_SECONDS = 20


def _extract_graceful_stop_function() -> str:
    """Pull the live ``graceful_stop`` body from the script (avoids harness drift)."""
    match = re.search(
        r"^function graceful_stop\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("graceful_stop function not found in juniper_chop_all.bash")
    return match.group(0)


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


class TestGracefulStop(unittest.TestCase):
    """Behavioral pins for ``graceful_stop`` SIGTERM→SIGKILL escalate.

    A hung service that ignores SIGTERM must still be torn down with SIGKILL;
    an already-exited PID must not be treated as a stop failure (that would
    bump ``STOP_FAILURES`` and preserve the pidfile forever). Extracted from
    the live script so the harness cannot drift from production.
    """

    def _run_graceful_stop(self, pid: int, service_name: str, timeout: int) -> subprocess.CompletedProcess[str]:
        harness = f"""
            set -euo pipefail
            JUNIPER_SCRIPT_NAME="juniper_chop_all.bash"
            SIGTERM_TIMEOUT=15
            {_extract_graceful_stop_function()}
            set +e
            graceful_stop "$1" "$2" "$3"
            status=$?
            set -e
            echo "STATUS=${{status}}"
            exit 0
        """
        env = RedactedEnv(os.environ)
        return subprocess.run(
            ["bash", "-c", harness, "_", str(pid), service_name, str(timeout)],
            capture_output=True,
            text=True,
            env=env,
            timeout=GRACEFUL_STOP_TIMEOUT_SECONDS,
        )

    def _spawn_detached(self, inner_bash: str) -> int:
        """Start a session-leader child reparented to init.

        ``graceful_stop`` polls ``kill -0`` after SIGTERM/SIGKILL. If the
        test process remains the parent, a dead child stays a zombie and
        ``kill -0`` keeps succeeding — a false "survived SIGKILL". Launch
        under a short-lived ``setsid`` shell so init reaps the exit.
        """
        launcher = "setsid bash -c " + repr(inner_bash) + " </dev/null >/dev/null 2>&1 & echo $!"
        result = subprocess.run(
            ["bash", "-c", launcher],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        pid = int(result.stdout.strip().splitlines()[-1])
        # Brief settle so the session leader is fully up before we signal it.
        time.sleep(0.15)
        self.assertTrue(Path(f"/proc/{pid}").exists(), f"detached pid {pid} missing")
        return pid

    def _force_kill(self, pid: int) -> None:
        # Prefer process-group kill (setsid leader) so any accidental child
        # does not leak past the test; fall back to the single pid.
        for kill_target in (lambda: os.killpg(pid, signal.SIGKILL), lambda: os.kill(pid, signal.SIGKILL)):
            try:
                kill_target()
                break
            except ProcessLookupError:
                return
            except PermissionError:
                continue
        for _ in range(20):
            if not Path(f"/proc/{pid}").exists():
                return
            time.sleep(0.05)

    def test_cooperative_process_stops_on_sigterm(self) -> None:
        # Default sleep exits on SIGTERM — must take the graceful arm, never SIGKILL.
        pid = self._spawn_detached("exec sleep 60")
        try:
            result = self._run_graceful_stop(pid, "juniper-data", 5)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=0", result.stdout)
            self.assertIn("stopped gracefully", result.stdout)
            self.assertNotIn("sending SIGKILL", result.stdout)
            self.assertFalse(Path(f"/proc/{pid}").exists())
        finally:
            self._force_kill(pid)

    def test_sigterm_ignore_escalates_to_sigkill(self) -> None:
        # Single-process SIGTERM ignore (exec would drop a bash ``trap``).
        # timeout=1 keeps the wait loop to a single second before escalate.
        pid = self._spawn_detached("exec python3 -c 'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'")
        try:
            result = self._run_graceful_stop(pid, "juniper-cascor", 1)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=0", result.stdout)
            self.assertIn("sending SIGKILL", result.stdout)
            self.assertIn("killed with SIGKILL", result.stdout)
            self.assertFalse(Path(f"/proc/{pid}").exists())
        finally:
            self._force_kill(pid)

    def test_already_exited_pid_is_not_a_failure(self) -> None:
        # Stale pidfile entry whose process is gone: SIGTERM fails → return 0
        # so STOP_FAILURES stays 0 and the pidfile can still be cleared.
        pid = self._spawn_detached("exec sleep 60")
        self._force_kill(pid)
        # Confirm init reaped before we assert the already-exited arm.
        for _ in range(40):
            if not Path(f"/proc/{pid}").exists():
                break
            time.sleep(0.05)
        self.assertFalse(Path(f"/proc/{pid}").exists(), f"pid {pid} still in /proc")
        result = self._run_graceful_stop(pid, "juniper-canopy", 2)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertIn("Failed to send SIGTERM", result.stdout)
        self.assertNotIn("sending SIGKILL", result.stdout)

    def test_stop_failures_wire_preserves_pidfile(self) -> None:
        # Drift guard: graceful_stop failure must bump STOP_FAILURES and the
        # summary path must preserve the pidfile (not clear it) on failures > 0.
        self.assertIn(
            'if ! graceful_stop "${JUNIPER_APPLICATION_PID}" "${JUNIPER_APPLICATION_NAME}"; then',
            SCRIPT_TEXT,
        )
        self.assertIn("STOP_FAILURES=$(( STOP_FAILURES + 1 ))", SCRIPT_TEXT)
        self.assertIn("PID file preserved at ${JUNIPER_PROJECT_PID_FILE}", SCRIPT_TEXT)
        # Success path truncates the pidfile — regression would leave a
        # stale JuniperProject.pid and confuse the next plant/chop cycle.
        self.assertIn(': > "${JUNIPER_PROJECT_PID_FILE}"', SCRIPT_TEXT)


if __name__ == "__main__":
    unittest.main()
