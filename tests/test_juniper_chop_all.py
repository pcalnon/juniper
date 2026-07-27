"""
Tests for util/juniper_chop_all.bash

Validates the parser / grep changes introduced in Pass 2 of the
2026-05-07 startup/shutdown scripts audit:

- Pid file parser accepts both the new `name=pid` format AND the legacy
  `name: pid` format (backward-compatibility window).
- Worker-cleanup grep no longer matches arbitrary processes that happen
  to contain `cascor` and `worker` separated by other tokens.
- ``orphaned_worker_cleanup`` kill-path filter (KILL_WORKERS gate, pgrep →
  strict cmdline match → ``graceful_stop``) via a hermetic extract + PATH
  stubbed ``pgrep``.

Where running the full chop script is impractical (requires root, a real
pid file, and a live process), tests run a self-contained extract of the
parser / orphaned_worker_cleanup block in a subshell. Static-text
assertions guard the grep tightening change.
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
ORPHANED_WORKER_TIMEOUT_SECONDS = 15


def _extract_orphaned_worker_cleanup() -> str:
    """Pull the live ``orphaned_worker_cleanup`` body (avoids harness drift)."""
    match = re.search(
        r"^function orphaned_worker_cleanup\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("orphaned_worker_cleanup function not found in juniper_chop_all.bash")
    return match.group(0)


def _write_fake_pgrep(bin_dir: Path, lines: list[str]) -> None:
    """Stub ``pgrep -af <term>`` that emits fixed ``PID cmdline`` rows.

    Absolute ``/bin/bash`` shebang so a restricted PATH still works. Ignores
    the search term (the suite feeds only the candidate set under test).
    """
    payload = bin_dir / "pgrep_lines.txt"
    payload.write_text("\n".join(lines) + ("\n" if lines else ""))
    pgrep_path = bin_dir / "pgrep"
    pgrep_path.write_text("#!/bin/bash\n" "set -euo pipefail\n" f'cat -- "{payload}"\n')
    pgrep_path.chmod(0o755)


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


class TestOrphanedWorkerCleanup(unittest.TestCase):
    """Behavioral pins for ``orphaned_worker_cleanup`` kill-path filter.

    Host-mode chop optionally reaps leftover cascor workers after the pidfile
    loop. A refactor that drops the ``KILL_WORKERS`` gate, treats every pgrep
    hit as a worker (the old ``cascor.*worker`` class), or forgets to call
    ``graceful_stop`` leaves orphaned workers up — or kills unrelated shells.
    Prior suite only had static ``TestWorkerGrepTightening``; this extract
    drives the live function with a PATH-stubbed ``pgrep`` and a recording
    ``graceful_stop`` (no real signals).
    """

    def _run_cleanup(
        self,
        *,
        kill_workers: str,
        search_term: str,
        pgrep_lines: list[str],
        sigterm_timeout: str = "15",
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            _write_fake_pgrep(bin_dir, pgrep_lines)
            graceful_log = Path(tmp) / "graceful_stop.log"
            harness = f"""
                set -euo pipefail
                JUNIPER_SCRIPT_NAME="juniper_chop_all.bash"
                graceful_stop() {{
                    # Record pid/name/timeout; never signal (hermetic).
                    printf 'pid=%s name=%s timeout=%s\\n' "$1" "$2" "$3" >> "{graceful_log}"
                    return 0
                }}
                {_extract_orphaned_worker_cleanup()}
                set +e
                orphaned_worker_cleanup "$1" "$2" "$3"
                status=$?
                set -e
                echo "STATUS=${{status}}"
                if [[ -f "{graceful_log}" ]]; then
                    echo "---GRACEFUL---"
                    cat "{graceful_log}"
                else
                    echo "---GRACEFUL---"
                fi
                exit 0
            """
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
            return subprocess.run(
                ["bash", "-c", harness, "_", kill_workers, search_term, sigterm_timeout],
                capture_output=True,
                text=True,
                env=env,
                timeout=ORPHANED_WORKER_TIMEOUT_SECONDS,
            )

    @staticmethod
    def _graceful_lines(stdout: str) -> list[str]:
        if "---GRACEFUL---" not in stdout:
            return []
        return [ln for ln in stdout.split("---GRACEFUL---", 1)[1].strip().splitlines() if ln.strip()]

    def test_kill_workers_flag_off_skips_cleanup(self) -> None:
        result = self._run_cleanup(
            kill_workers="0",
            search_term="juniper-cascor-worker",
            # Even if pgrep would return hits, the flag gate must short-circuit.
            pgrep_lines=["4242 /usr/bin/juniper-cascor-worker --bind 0.0.0.0"],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("KILL_WORKERS flag is not set to 1", result.stdout)
        self.assertEqual(self._graceful_lines(result.stdout), [])

    def test_no_candidates_reports_none_found(self) -> None:
        result = self._run_cleanup(
            kill_workers="1",
            search_term="juniper-cascor-worker",
            pgrep_lines=[],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("No orphaned worker processes found", result.stdout)
        self.assertEqual(self._graceful_lines(result.stdout), [])

    def test_dash_variant_calls_graceful_stop(self) -> None:
        result = self._run_cleanup(
            kill_workers="1",
            search_term="juniper-cascor-worker",
            pgrep_lines=["4242 /opt/miniforge3/envs/JuniperCascor1/bin/juniper-cascor-worker --bind 0.0.0.0"],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertIn("Found 1 worker process(es) to stop", result.stdout)
        # Production hard-codes timeout=5 (not SIGTERM_TIMEOUT) for workers.
        self.assertEqual(
            self._graceful_lines(result.stdout),
            ["pid=4242 name=cascor-worker timeout=5"],
        )

    def test_underscore_import_path_calls_graceful_stop(self) -> None:
        result = self._run_cleanup(
            kill_workers="1",
            search_term="juniper-cascor-worker",
            pgrep_lines=["5252 python -m juniper_cascor_worker.cli --bind 127.0.0.1"],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertEqual(
            self._graceful_lines(result.stdout),
            ["pid=5252 name=cascor-worker timeout=5"],
        )

    def test_overgreedy_cascor_worker_pair_is_not_killed(self) -> None:
        # The pre-audit third alternative was `cascor.*worker`, which matched
        # unrelated shells that merely mentioned both tokens in order. Feed a
        # pgrep hit that would match that old pattern but contains neither
        # strict variant nor the search term — must NOT call graceful_stop.
        result = self._run_cleanup(
            kill_workers="1",
            search_term="juniper-cascor-worker",
            pgrep_lines=[
                "6262 bash -c 'cd ~/notes && run cascor then worker cleanup'",
            ],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("No orphaned worker processes found", result.stdout)
        self.assertEqual(self._graceful_lines(result.stdout), [])

    def test_multiple_workers_stop_each_pid(self) -> None:
        result = self._run_cleanup(
            kill_workers="1",
            search_term="juniper-cascor-worker",
            pgrep_lines=[
                "1001 /usr/bin/juniper-cascor-worker --bind 0.0.0.0",
                "1002 python -m juniper_cascor_worker.cli",
            ],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertIn("Found 2 worker process(es) to stop", result.stdout)
        self.assertEqual(
            self._graceful_lines(result.stdout),
            [
                "pid=1001 name=cascor-worker timeout=5",
                "pid=1002 name=cascor-worker timeout=5",
            ],
        )

    def test_tail_call_sites_tolerate_cleanup_failure(self) -> None:
        # Drift guard: the post-pidfile call uses `|| true` so a no-worker
        # return 1 cannot fail the whole chop after services already stopped.
        self.assertIn(
            'orphaned_worker_cleanup "${KILL_WORKERS}" "${WORKER_SEARCH_TERM}" "${SIGTERM_TIMEOUT}" || true',
            SCRIPT_TEXT,
        )


if __name__ == "__main__":
    unittest.main()
