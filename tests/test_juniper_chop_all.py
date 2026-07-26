"""
Tests for util/juniper_chop_all.bash

Validates the parser / grep changes introduced in Pass 2 of the
2026-05-07 startup/shutdown scripts audit:

- Pid file parser accepts both the new `name=pid` format AND the legacy
  `name: pid` format (backward-compatibility window).
- Worker-cleanup grep no longer matches arbitrary processes that happen
  to contain `cascor` and `worker` separated by other tokens.
- Missing / empty ``JuniperProject.pid`` still invokes
  ``orphaned_worker_cleanup`` then exits 1 (full-script wire; hermetic
  via ``JUNIPER_PROJECT_DIR`` + PATH-stubbed ``pgrep``).

Where running the full chop script is impractical (requires root, a real
pid file, and a live process), tests run a self-contained extract of the
parser block in a subshell. Static-text assertions guard the grep
tightening change. The missing/empty pidfile arms are the exception —
they are reachable without live services.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_chop_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 10
PIDFILE_WIRE_TIMEOUT_SECONDS = 15


def _write_fake_pgrep(bin_dir: Path, lines: list[str]) -> None:
    """Stub ``pgrep -af <term>`` that emits fixed ``PID cmdline`` rows.

    Absolute ``/bin/bash`` shebang so a restricted PATH still works.
    """
    payload = bin_dir / "pgrep_lines.txt"
    payload.write_text("\n".join(lines) + ("\n" if lines else ""))
    pgrep_path = bin_dir / "pgrep"
    pgrep_path.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        f'cat -- "{payload}"\n'
    )
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


class TestMissingEmptyPidfileWire(unittest.TestCase):
    """Missing / empty pidfile must still call orphaned_worker_cleanup then exit 1.

    Orthogonal to open ``TestOrphanedWorkerCleanup`` (#791), which extracts the
    function in isolation: these cases drive the live top-level arms so a
    refactor cannot drop the cleanup call (or continue into the service-stop
    loop) when plant never wrote a pidfile. ``KILL_WORKERS=0`` proves the call
    via the flag short-circuit message; ``KILL_WORKERS=1`` + stubbed empty
    ``pgrep`` proves the kill-path entry on the same wire.
    """

    def _run_chop(
        self,
        *,
        project_dir: Path,
        kill_workers: str,
        pgrep_lines: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = RedactedEnv(os.environ)
        env["JUNIPER_PROJECT_DIR"] = str(project_dir)
        env["KILL_WORKERS"] = kill_workers
        env["USE_SYSTEMD"] = "0"
        env["SIGTERM_TIMEOUT"] = "5"
        path_prefix = ""
        if pgrep_lines is not None:
            bin_dir = project_dir / "_test_bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            _write_fake_pgrep(bin_dir, pgrep_lines)
            path_prefix = f"{bin_dir}:"
        # Keep /usr/bin:/bin so realpath / coreutils stay available.
        env["PATH"] = f"{path_prefix}/usr/bin:/bin"
        return subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            env=env,
            timeout=PIDFILE_WIRE_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _project_with_ml(root: Path) -> Path:
        project_dir = root / "Juniper"
        (project_dir / "juniper-ml").mkdir(parents=True)
        return project_dir

    def test_missing_pidfile_calls_cleanup_and_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self._project_with_ml(Path(tmp))
            result = self._run_chop(project_dir=project_dir, kill_workers="0")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, msg=combined)
        self.assertIn("ERROR: PID file not found", combined)
        self.assertIn("No services to stop. Was juniper_plant_all.bash run?", combined)
        # Proof the early arm invoked orphaned_worker_cleanup (flag gate).
        self.assertIn("KILL_WORKERS flag is not set to 1", combined)
        # Must not reach the service-stop loop / mapfile path.
        self.assertNotIn("=== Stopping Juniper Services ===", combined)
        self.assertNotIn("Juniper Project PID File Line Array", combined)

    def test_empty_pidfile_calls_cleanup_and_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self._project_with_ml(Path(tmp))
            pidfile = project_dir / "juniper-ml" / "JuniperProject.pid"
            pidfile.write_text("")
            result = self._run_chop(project_dir=project_dir, kill_workers="0")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, msg=combined)
        self.assertIn("ERROR: PID file is empty", combined)
        self.assertIn("No services to stop. Was juniper_plant_all.bash run?", combined)
        self.assertIn("KILL_WORKERS flag is not set to 1", combined)
        self.assertNotIn("=== Stopping Juniper Services ===", combined)
        self.assertNotIn("Juniper Project PID File Line Array", combined)

    def test_missing_pidfile_kill_workers_enters_cleanup_kill_path(self) -> None:
        # Same early arm with KILL_WORKERS=1: cleanup must reach the pgrep
        # candidate scan (not only the flag short-circuit). Empty stub →
        # "No orphaned worker processes found", then the arm still exits 1.
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = self._project_with_ml(Path(tmp))
            result = self._run_chop(
                project_dir=project_dir,
                kill_workers="1",
                pgrep_lines=[],
            )
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, msg=combined)
        self.assertIn("ERROR: PID file not found", combined)
        self.assertIn("=== Cleaning up orphaned worker processes ===", combined)
        self.assertIn("No orphaned worker processes found", combined)
        self.assertNotIn("=== Stopping Juniper Services ===", combined)

    def test_early_pidfile_arms_call_cleanup_before_exit(self) -> None:
        # Drift guard: both missing and empty arms must call cleanup (no
        # `|| true` — unlike the post-service tail call) then exit 1. A
        # refactor that drops either call leaves orphaned workers up when
        # plant never wrote a pidfile.
        missing_idx = SCRIPT_TEXT.find("ERROR: PID file not found")
        empty_idx = SCRIPT_TEXT.find("ERROR: PID file is empty")
        self.assertGreater(missing_idx, 0)
        self.assertGreater(empty_idx, missing_idx)
        for label, start, end in (
            ("missing", missing_idx, empty_idx),
            ("empty", empty_idx, SCRIPT_TEXT.find("Load Juniper Pid File", empty_idx)),
        ):
            arm = SCRIPT_TEXT[start:end] if end > start else SCRIPT_TEXT[start:]
            self.assertIn(
                'orphaned_worker_cleanup "${KILL_WORKERS}" "${WORKER_SEARCH_TERM}" "${SIGTERM_TIMEOUT}"',
                arm,
                msg=f"{label} pidfile arm lost orphaned_worker_cleanup call",
            )
            self.assertNotIn(
                'orphaned_worker_cleanup "${KILL_WORKERS}" "${WORKER_SEARCH_TERM}" "${SIGTERM_TIMEOUT}" || true',
                arm,
                msg=f"{label} pidfile arm must not swallow cleanup status with || true",
            )
            self.assertIn("exit 1", arm, msg=f"{label} pidfile arm lost exit 1")


if __name__ == "__main__":
    unittest.main()
