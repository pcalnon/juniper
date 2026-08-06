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
- Non-empty pidfile full-script wire: matching cmdline → SIGTERM + truncate;
  reused-PID cmdline mismatch → skip kill + still truncate; legacy
  ``name: pid`` format still stops through the live loop.

Where helper isolation is clearer, tests extract ``validate_pid`` /
``graceful_stop`` / ``orphaned_worker_cleanup``. The missing/empty and
non-empty pidfile wires run the full script hermetically
(``JUNIPER_PROJECT_DIR`` + ``JUNIPER_CHOP_PROC_ROOT`` + ``KILL_WORKERS=0``).
Static-text assertions guard the grep tightening change.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_chop_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 10
PIDFILE_WIRE_TIMEOUT_SECONDS = 15
GRACEFUL_STOP_TIMEOUT_SECONDS = 20
ORPHANED_WORKER_TIMEOUT_SECONDS = 15


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


class TestNonEmptyPidfileWire(unittest.TestCase):
    """Full-script pin: non-empty pidfile → validate → graceful_stop → summary.

    The missing/empty wire (#798 / ``TestMissingOrEmptyPidfileWire``) never
    enters the service-stop loop. Extracted ``validate_pid`` /
    ``graceful_stop`` units pin the helpers in isolation. This class is the
    end-to-end path that decides whether a live PID is killed and whether
    ``JuniperProject.pid`` is truncated or preserved — the blast-radius gap
    between those two layers.
    """

    FULL_PIDFILE_TIMEOUT_SECONDS = 25

    def _spawn_detached(self, inner_bash: str) -> int:
        launcher = "setsid bash -c " + repr(inner_bash) + " </dev/null >/dev/null 2>&1 & echo $!"
        result = subprocess.run(
            ["bash", "-c", launcher],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        pid = int(result.stdout.strip().splitlines()[-1])
        time.sleep(0.15)
        self.assertTrue(Path(f"/proc/{pid}").exists(), f"detached pid {pid} missing")
        return pid

    def _force_kill(self, pid: int) -> None:
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

    def _add_fake_proc(self, proc_root: Path, pid: int, cmdline_parts: list[str]) -> None:
        process_dir = proc_root / str(pid)
        process_dir.mkdir(parents=True)
        (process_dir / "cmdline").write_bytes(b"\0".join(part.encode("utf-8") for part in cmdline_parts) + b"\0")

    def _run_chop(
        self,
        *,
        project_dir: Path,
        proc_root: Path,
        pidfile_body: str,
        sigterm_timeout: str = "3",
    ) -> subprocess.CompletedProcess[str]:
        ml_dir = project_dir / "juniper-ml"
        ml_dir.mkdir(parents=True, exist_ok=True)
        (ml_dir / "JuniperProject.pid").write_text(pidfile_body)

        env = RedactedEnv(os.environ)
        env["JUNIPER_PROJECT_DIR"] = str(project_dir)
        env["JUNIPER_CHOP_PROC_ROOT"] = str(proc_root)
        env["KILL_WORKERS"] = "0"
        env["USE_SYSTEMD"] = "0"
        env["SIGTERM_TIMEOUT"] = sigterm_timeout
        env["PATH"] = "/usr/bin:/bin"

        return subprocess.run(
            ["/bin/bash", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            env=env,
            timeout=self.FULL_PIDFILE_TIMEOUT_SECONDS,
        )

    def test_matching_pid_stops_and_truncates_pidfile(self) -> None:
        # Happy path: validate accepts the fake cmdline, graceful_stop SIGTERMs
        # the real detached sleep, summary truncates JuniperProject.pid.
        pid = self._spawn_detached("exec sleep 60")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project_dir = Path(tmp) / "Juniper"
                proc_root = Path(tmp) / "proc"
                self._add_fake_proc(
                    proc_root,
                    pid,
                    ["/opt/conda/envs/JuniperData1/bin/python", "-m", "uvicorn", "juniper_data.api.app:get_app"],
                )
                result = self._run_chop(
                    project_dir=project_dir,
                    proc_root=proc_root,
                    pidfile_body=f"juniper-data={pid}\n",
                )
                combined = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, msg=combined)
                self.assertIn("=== Stopping Juniper Services ===", combined)
                self.assertIn("stopped gracefully", combined)
                self.assertIn("All services stopped successfully", combined)
                self.assertIn("Clearing PID file", combined)
                pidfile = project_dir / "juniper-ml" / "JuniperProject.pid"
                self.assertTrue(pidfile.exists())
                self.assertEqual(pidfile.read_text(), "")
                self.assertFalse(Path(f"/proc/{pid}").exists(), f"pid {pid} still alive after chop")
        finally:
            self._force_kill(pid)

    def test_legacy_colon_pidfile_format_stops_matching_process(self) -> None:
        # Full-script pin of the legacy ``name: pid`` parser arm (extracted
        # TestPidParser alone cannot prove the live loop still splits on `:`).
        pid = self._spawn_detached("exec sleep 60")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project_dir = Path(tmp) / "Juniper"
                proc_root = Path(tmp) / "proc"
                self._add_fake_proc(
                    proc_root,
                    pid,
                    ["/opt/miniforge3/envs/JuniperCascor1/bin/python", "server.py"],
                )
                result = self._run_chop(
                    project_dir=project_dir,
                    proc_root=proc_root,
                    pidfile_body=f"juniper-cascor: {pid}\n",
                )
                combined = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, msg=combined)
                self.assertIn("Clearing PID file", combined)
                self.assertFalse(Path(f"/proc/{pid}").exists())
        finally:
            self._force_kill(pid)

    def test_reused_pid_mismatch_skips_kill_and_still_truncates(self) -> None:
        # D-05 end-to-end: a stale pidfile entry whose PID now belongs to an
        # unrelated process must NOT be SIGTERM'd. validate_pid skip does not
        # bump STOP_FAILURES, so the summary still clears the pidfile (stale
        # entry dropped) — pin that contract so a future "preserve on skip"
        # change is intentional.
        pid = self._spawn_detached("exec sleep 60")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project_dir = Path(tmp) / "Juniper"
                proc_root = Path(tmp) / "proc"
                self._add_fake_proc(proc_root, pid, ["/usr/sbin/sshd", "-D"])
                result = self._run_chop(
                    project_dir=project_dir,
                    proc_root=proc_root,
                    pidfile_body=f"juniper-canopy={pid}\n",
                )
                combined = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, msg=combined)
                self.assertIn("does not match expected service", combined)
                self.assertNotIn("Stopping juniper-canopy", combined)
                self.assertIn("Clearing PID file", combined)
                self.assertTrue(
                    Path(f"/proc/{pid}").exists(),
                    f"reused pid {pid} was killed despite cmdline mismatch",
                )
                self.assertEqual((project_dir / "juniper-ml" / "JuniperProject.pid").read_text(), "")
        finally:
            self._force_kill(pid)


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
