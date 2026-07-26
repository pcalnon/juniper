"""
Tests for util/juniper_chop_all.bash

Validates the parser / grep changes introduced in Pass 2 of the
2026-05-07 startup/shutdown scripts audit:

- Pid file parser accepts both the new `name=pid` format AND the legacy
  `name: pid` format (backward-compatibility window).
- Worker-cleanup grep no longer matches arbitrary processes that happen
  to contain `cascor` and `worker` separated by other tokens.

Where running the full chop script is impractical (requires root, a real
pid file, and a live process), tests run a self-contained extract of the
parser block in a subshell. Static-text assertions guard the grep
tightening change.
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
        systemctl.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f'printf "%s\\n" "$*" >>"{systemctl_log}"\n'
            'if [[ "${1:-}" == "--user" ]]; then shift; fi\n'
            'cmd="${1:-}"\n'
            'unit="${2:-}"\n'
            f'fail_units="{fail_list}"\n'
            'case "${cmd}" in\n'
            "  stop)\n"
            '    for bad in ${fail_units}; do\n'
            '      if [[ "${unit}" == "${bad}" ]]; then exit 1; fi\n'
            "    done\n"
            "    exit 0\n"
            "    ;;\n"
            "  *) exit 0 ;;\n"
            "esac\n"
        )
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


if __name__ == "__main__":
    unittest.main()
