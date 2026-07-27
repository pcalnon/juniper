"""
Tests for util/juniper_chop_all.bash

Validates the parser / grep changes introduced in Pass 2 of the
2026-05-07 startup/shutdown scripts audit:

- Pid file parser accepts both the new `name=pid` format AND the legacy
  `name: pid` format (backward-compatibility window).
- Worker-cleanup grep no longer matches arbitrary processes that happen
  to contain `cascor` and `worker` separated by other tokens.
- Missing / empty JuniperProject.pid still invokes orphaned_worker_cleanup
  then exits 1 (full-script smoke against a synthetic project dir).

Where running the full chop script is impractical (requires root, a real
pid file, and a live process), tests run a self-contained extract of the
parser block in a subshell — except the pidfile-absent/empty wire, which
is reachable hermetically with KILL_WORKERS=0 (cleanup short-circuits).
Static-text assertions guard the grep tightening change.
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


class TestSystemdModeBehavioral(unittest.TestCase):
    """Full-script PATH-stub coverage for chop's ``USE_SYSTEMD=1`` / ``--systemd`` branch.

    The systemd arm exits before the pidfile parser and ``orphaned_worker_cleanup``,
    so a hermetic ``systemctl`` stub is enough. Pins reverse stop order, soft-fail
    continue-on-error, and that successful systemd teardown never falls through to
    the pidfile path (static text pins alone cannot prove the early ``exit 0``).
    """

    _EXPECTED_STOP_ORDER = (
        "juniper-cascor-worker.service",
        "juniper-canopy.service",
        "juniper-cascor.service",
        "juniper-data.service",
    )

    def _stage_systemctl(self, root: Path, *, fail_units: set[str] | None = None) -> tuple[Path, Path]:
        stub_bin = root / "path-stubs"
        stub_bin.mkdir(parents=True, exist_ok=True)
        systemctl_log = root / "systemctl.log"
        systemctl_log.write_text("")
        fail_list = " ".join(sorted(fail_units or ()))
        systemctl = stub_bin / "systemctl"
        systemctl.write_text("#!/usr/bin/env bash\n" "set -euo pipefail\n" f'printf "%s\\n" "$*" >>"{systemctl_log}"\n' 'if [[ "${1:-}" == "--user" ]]; then shift; fi\n' 'cmd="${1:-}"\n' 'unit="${2:-}"\n' f'fail_units="{fail_list}"\n' 'case "${cmd}" in\n' "  stop)\n" "    for bad in ${fail_units}; do\n" '      if [[ "${unit}" == "${bad}" ]]; then exit 1; fi\n' "    done\n" "    exit 0\n" "    ;;\n" "  *) exit 0 ;;\n" "esac\n")
        systemctl.chmod(0o755)
        return stub_bin, systemctl_log

    def _chop_env(self, stub_bin: Path) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        env["USE_SYSTEMD"] = "1"
        env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"
        return env

    def _run_chop(
        self,
        env: RedactedEnv,
        *,
        args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        cmd = ["/bin/bash", str(SCRIPT_PATH)]
        if args:
            cmd.extend(args)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )

    def _stopped_units(self, log: Path) -> list[str]:
        stops: list[str] = []
        for line in log.read_text().splitlines():
            parts = line.split()
            if "--user" in parts and "stop" in parts:
                try:
                    idx = parts.index("stop")
                    stops.append(parts[idx + 1])
                except (ValueError, IndexError):
                    continue
        return stops

    def test_happy_path_stops_units_in_reverse_dependency_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_systemctl(root)
            env = self._chop_env(stub_bin)
            result = self._run_chop(env)
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertIn("Stopping services via systemd", combined)
            self.assertIn("All Juniper services stopped via systemd", combined)
            self.assertNotIn("Stopping services via pidfile", combined)
            self.assertEqual(self._stopped_units(systemctl_log), list(self._EXPECTED_STOP_ORDER))
            for unit_name in (
                "juniper-cascor-worker",
                "juniper-canopy",
                "juniper-cascor",
                "juniper-data",
            ):
                self.assertIn(f"{unit_name} stopped.", combined)

    def test_systemd_flag_enters_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_systemctl(root)
            env = self._chop_env(stub_bin)
            del env["USE_SYSTEMD"]
            result = self._run_chop(env, args=["--systemd"])
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertEqual(self._stopped_units(systemctl_log), list(self._EXPECTED_STOP_ORDER))
            self.assertNotIn("Stopping services via pidfile", combined)

    def test_stop_failure_soft_fails_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_systemctl(
                root,
                fail_units={"juniper-canopy.service"},
            )
            env = self._chop_env(stub_bin)
            result = self._run_chop(env)
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertIn("juniper-canopy was not running or failed to stop.", combined)
            self.assertIn("juniper-cascor-worker stopped.", combined)
            self.assertIn("juniper-data stopped.", combined)
            # All four stops were still attempted in reverse order.
            self.assertEqual(self._stopped_units(systemctl_log), list(self._EXPECTED_STOP_ORDER))
            self.assertNotIn("Stopping services via pidfile", combined)


class TestIntentionalEchoDuplicatesPreserved(unittest.TestCase):
    """Per memory `feedback_chop_all_echo_debug`, duplicate echo lines around
    SIGTERM_TIMEOUT / KILL_WORKERS are intentional placeholders. The audit
    must NOT have removed them."""

    def test_sigterm_echo_appears_at_least_twice(self) -> None:
        count = SCRIPT_TEXT.count('SIGTERM_TIMEOUT=\\"${SIGTERM_TIMEOUT}\\"')
        self.assertGreaterEqual(count, 2, "intentional duplicate echo lines were removed")


class TestMissingOrEmptyPidfileWire(unittest.TestCase):
    """Full-script pin: missing/empty pidfile → orphaned_worker_cleanup → exit 1.

    Orthogonal to open #778 (graceful_stop escalate) and #791
    (orphaned_worker_cleanup kill-path filter). Those extract functions;
    this exercises the two early call sites that must still run cleanup
    before aborting when plant never wrote a usable JuniperProject.pid.
    """

    def _run_chop(self, *, create_empty_pidfile: bool) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "Juniper"
            ml_dir = project_dir / "juniper-ml"
            ml_dir.mkdir(parents=True, exist_ok=True)
            if create_empty_pidfile:
                (ml_dir / "JuniperProject.pid").write_text("")

            env = RedactedEnv(os.environ)
            env["JUNIPER_PROJECT_DIR"] = str(project_dir)
            # Keep cleanup on the short-circuit arm (no pgrep / live PIDs).
            env["KILL_WORKERS"] = "0"
            env["USE_SYSTEMD"] = "0"
            # Absolute bash + minimal PATH (memory: plant/chop PATH stubs).
            env["PATH"] = "/usr/bin:/bin"

            return subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                env=env,
                timeout=PIDFILE_WIRE_TIMEOUT_SECONDS,
            )

    def test_missing_pidfile_runs_cleanup_then_exits_1(self) -> None:
        result = self._run_chop(create_empty_pidfile=False)
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, msg=combined)
        self.assertIn("ERROR: PID file not found", combined)
        self.assertIn("No services to stop. Was juniper_plant_all.bash run?", combined)
        # Prove the early call site invoked cleanup (KILL_WORKERS=0 short-circuit).
        self.assertIn(
            "KILL_WORKERS flag to Optionally clean up orphaned worker processes: 0",
            combined,
        )
        self.assertIn(
            "KILL_WORKERS flag is not set to 1. No orphaned worker processes cleanup",
            combined,
        )
        # Must not reach the service-stop loop.
        self.assertNotIn("=== Stopping Juniper Services ===", combined)

    def test_empty_pidfile_runs_cleanup_then_exits_1(self) -> None:
        result = self._run_chop(create_empty_pidfile=True)
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, msg=combined)
        self.assertIn("ERROR: PID file is empty", combined)
        self.assertIn("No services to stop. Was juniper_plant_all.bash run?", combined)
        self.assertIn(
            "KILL_WORKERS flag to Optionally clean up orphaned worker processes: 0",
            combined,
        )
        self.assertIn(
            "KILL_WORKERS flag is not set to 1. No orphaned worker processes cleanup",
            combined,
        )
        self.assertNotIn("=== Stopping Juniper Services ===", combined)

    def test_early_pidfile_cleanup_call_sites_are_not_softened(self) -> None:
        # Drift guard: the missing/empty arms must call cleanup without
        # `|| true` (unlike the post-stop site owned by #791). Softening
        # them would hide a cleanup failure and still look like a clean abort.
        self.assertIn("ERROR: PID file not found:", SCRIPT_TEXT)
        self.assertIn("ERROR: PID file is empty:", SCRIPT_TEXT)
        early_call = 'orphaned_worker_cleanup "${KILL_WORKERS}" ' '"${WORKER_SEARCH_TERM}" "${SIGTERM_TIMEOUT}"'
        soft_call = early_call + " || true"
        self.assertGreaterEqual(SCRIPT_TEXT.count(early_call), 3)
        # Exactly one soft call (post-stop); the two early sites stay hard.
        self.assertEqual(SCRIPT_TEXT.count(soft_call), 1)


if __name__ == "__main__":
    unittest.main()
