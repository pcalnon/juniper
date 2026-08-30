"""Hermetic coverage for the systemd --user Duplicati scheduled-backup lane (#1292).

The 2026-07-13 archive damage went undetected for six weeks because a backup that
silently stops is indistinguishable from one that works. #1292 shipped the
replacement lane — runner, OnFailure reporter, installer, three unit files —
with zero tests. util/ is outside every pre-commit Python hook, so this unittest
is the gate.

This suite never talks to a live Duplicati server or mutates the real user
systemd. PATH stubs cover mountpoint / duplicati-cli / journalctl / notify-send /
loginctl / systemctl. Destination, state dir, and local-DB path live in a
TemporaryDirectory. /proc is walked only to prove the db-holder skip leaves our
unique path alone.
"""

from __future__ import annotations

import fcntl
import os
import re
import stat
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "util" / "duplicati_scheduled_backup.bash"
REPORTER = REPO_ROOT / "util" / "duplicati_backup_failure.bash"
INSTALLER = REPO_ROOT / "util" / "install_duplicati_timer.bash"
UNIT_DIR = REPO_ROOT / "util" / "systemd"
BACKUP_SERVICE = UNIT_DIR / "duplicati-backup.service"
BACKUP_TIMER = UNIT_DIR / "duplicati-backup.timer"
FAILURE_SERVICE = UNIT_DIR / "duplicati-backup-failure.service"

RUNNER_TEXT = RUNNER.read_text(encoding="utf-8")
REPORTER_TEXT = REPORTER.read_text(encoding="utf-8")
INSTALLER_TEXT = INSTALLER.read_text(encoding="utf-8")
BACKUP_SERVICE_TEXT = BACKUP_SERVICE.read_text(encoding="utf-8")
BACKUP_TIMER_TEXT = BACKUP_TIMER.read_text(encoding="utf-8")
FAILURE_SERVICE_TEXT = FAILURE_SERVICE.read_text(encoding="utf-8")

SCRIPT_TIMEOUT_SECONDS = 20
_PASSPHRASE = "test-passphrase-ok"  # nosec B105 — dummy; runner length floor is 12
_SHORT_PASSPHRASE = "short"  # nosec B105 — 5 chars, under the floor


def _write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


def _parse_status(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            parsed[key] = value
    return parsed


def _bash_n(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-n", str(script)],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class _LaneFixture:
    """Temp dest/state/db plus PATH stubs. No live Duplicati, no real systemd."""

    def __init__(self, tmpdir: str) -> None:
        self.root = Path(tmpdir)
        self.dest_mount = self.root / "dest_mount"
        self.dest_path = self.dest_mount / "Ubuntu"
        self.temp_dir = self.dest_mount / "_duplicati_tmp"
        self.state_dir = self.root / "state"
        self.source_path = self.root / "source"
        self.dbpath = self.root / "local.sqlite"
        self.stub_bin = self.root / "stubs"
        self.cli_log = self.root / "duplicati-cli.log"
        self.systemctl_log = self.root / "systemctl.log"
        self.dest_mount.mkdir()
        self.dest_path.mkdir()
        self.temp_dir.mkdir()
        self.state_dir.mkdir()
        self.source_path.mkdir()
        self.dbpath.write_bytes(b"")
        self.stub_bin.mkdir()
        self._write_stub_mountpoint(rc=0)
        self._write_stub_duplicati_cli(rc=0)
        self._write_stub_journalctl()
        self._write_stub_loginctl(linger="yes")
        self._write_stub_systemctl()

    @property
    def status_file(self) -> Path:
        return self.state_dir / "last-run.status"

    @property
    def lock_file(self) -> Path:
        return self.state_dir / "backup.lock"

    @property
    def failure_log(self) -> Path:
        return self.state_dir / "failures.log"

    def _write_stub_mountpoint(self, *, rc: int) -> None:
        _write_executable(
            self.stub_bin / "mountpoint",
            f"""\
            #!/usr/bin/env bash
            exit {rc}
            """,
        )

    def _write_stub_duplicati_cli(self, *, rc: int) -> None:
        _write_executable(
            self.stub_bin / "duplicati-cli",
            f"""\
            #!/usr/bin/env bash
            log="${{DUPLICATI_CLI_LOG:-/dev/null}}"
            for arg in "$@"; do
              printf '%s\\n' "$arg" >> "$log"
            done
            exit {rc}
            """,
        )

    def _write_stub_journalctl(self) -> None:
        _write_executable(
            self.stub_bin / "journalctl",
            """\
            #!/usr/bin/env bash
            printf 'journal-stub-line\\n'
            exit 0
            """,
        )

    def _write_stub_notify_send(self, *, rc: int) -> None:
        _write_executable(
            self.stub_bin / "notify-send",
            f"""\
            #!/usr/bin/env bash
            exit {rc}
            """,
        )

    def _write_stub_loginctl(self, *, linger: str) -> None:
        _write_executable(
            self.stub_bin / "loginctl",
            f"""\
            #!/usr/bin/env bash
            printf '%s\\n' "{linger}"
            exit 0
            """,
        )

    def _write_stub_systemctl(self) -> None:
        _write_executable(
            self.stub_bin / "systemctl",
            """\
            #!/usr/bin/env bash
            printf '%s\\n' "$*" >> "${SYSTEMCTL_LOG}"
            exit 0
            """,
        )

    def env(self, **overrides: str) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        for key in list(env):
            if key == "PASSPHRASE" or key.startswith("DUPLICATI_"):
                env.pop(key, None)
        env["PATH"] = f"{self.stub_bin}{os.pathsep}/usr/bin:/bin"
        env["PASSPHRASE"] = _PASSPHRASE
        env["DUPLICATI_DEST_URL"] = f"file://{self.dest_path}"
        env["DUPLICATI_DEST_PATH"] = str(self.dest_path)
        env["DUPLICATI_DEST_MOUNT"] = str(self.dest_mount)
        env["DUPLICATI_DBPATH"] = str(self.dbpath)
        env["DUPLICATI_SOURCE"] = str(self.source_path)
        env["DUPLICATI_STATE_DIR"] = str(self.state_dir)
        env["DUPLICATI_TEMP_DIR"] = str(self.temp_dir)
        env["DUPLICATI_CLI_LOG"] = str(self.cli_log)
        env["SYSTEMCTL_LOG"] = str(self.systemctl_log)
        env.update(overrides)
        return env

    def run_runner(self, env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(RUNNER)],
            capture_output=True,
            text=True,
            env=self.env() if env is None else env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
        )

    def run_reporter(self, env: RedactedEnv | None = None, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(REPORTER), *args],
            capture_output=True,
            text=True,
            env=self.env() if env is None else env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
        )

    def run_installer(self, env: RedactedEnv) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(INSTALLER)],
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
        )


def _hold_exclusive_lock(path: Path) -> int:
    # 0o600: this lock file needs no group/other access -- flock(2) works the
    # same either way, and a world-readable temp file is a CodeQL py/overly-
    # permissive-file finding (CWE-732) for no benefit.
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return fd


class TestSyntax(unittest.TestCase):
    def test_runner_bash_syntax(self) -> None:
        result = _bash_n(RUNNER)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_reporter_bash_syntax(self) -> None:
        result = _bash_n(REPORTER)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_installer_bash_syntax(self) -> None:
        result = _bash_n(INSTALLER)
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestRunnerTextPins(unittest.TestCase):
    """Load-bearing flags and the lock that must not be a self-matching pgrep."""

    def test_no_auto_compact_is_on_the_cli_invocation(self) -> None:
        self.assertIn("--no-auto-compact=true", RUNNER_TEXT)

    def test_pgrep_is_not_the_lock(self) -> None:
        for line in RUNNER_TEXT.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            self.assertNotIn("pgrep", stripped, msg=line)

    def test_flock_is_nonblocking(self) -> None:
        self.assertIn("flock -n 9", RUNNER_TEXT)


class TestUnitWiring(unittest.TestCase):
    """A failed run must be reported; a missed window must not be dropped."""

    def test_backup_service_chains_onfailure(self) -> None:
        self.assertIn("OnFailure=duplicati-backup-failure.service", BACKUP_SERVICE_TEXT)

    def test_passphrase_is_environmentfile_not_argv(self) -> None:
        self.assertIn("EnvironmentFile=%h/.config/duplicati-backup/env", BACKUP_SERVICE_TEXT)
        self.assertNotIn("PASSPHRASE=", BACKUP_SERVICE_TEXT)
        self.assertIn("ExecStart=%h/.local/bin/duplicati-scheduled-backup.bash", BACKUP_SERVICE_TEXT)

    def test_oneshot_start_timeout_is_infinity(self) -> None:
        self.assertIn("TimeoutStartSec=infinity", BACKUP_SERVICE_TEXT)

    def test_timer_is_persistent(self) -> None:
        self.assertIn("Persistent=true", BACKUP_TIMER_TEXT)
        self.assertIn("Unit=duplicati-backup.service", BACKUP_TIMER_TEXT)

    def test_reporter_does_not_chain_another_onfailure(self) -> None:
        for line in FAILURE_SERVICE_TEXT.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#") or not stripped:
                continue
            self.assertFalse(
                stripped.startswith("OnFailure="),
                msg=f"reporter unit must not chain OnFailure=: {line}",
            )
        self.assertIn("ExecStart=%h/.local/bin/duplicati-backup-failure.bash duplicati-backup.service", FAILURE_SERVICE_TEXT)


class TestInstallerTextPins(unittest.TestCase):
    def test_installs_copies_not_symlinks(self) -> None:
        self.assertIsNone(re.search(r"^\s*ln\s+-s\b", INSTALLER_TEXT, flags=re.MULTILINE))
        self.assertIn("install -m 0755", INSTALLER_TEXT)
        self.assertIn("install -m 0644", INSTALLER_TEXT)

    def test_does_not_enable_the_timer(self) -> None:
        """`enable --now` may appear in comments / echo instructions, never as a command."""
        for line in INSTALLER_TEXT.splitlines():
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#") or stripped.startswith("echo "):
                continue
            self.assertNotIn("enable --now", stripped, msg=line)


class TestRunnerRefuseClosed(unittest.TestCase):
    """Guards 1–3b: refuse rather than write an archive nobody can open / restore."""

    def test_empty_passphrase_refuses_and_stamps_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            env = fx.env()
            env.pop("PASSPHRASE", None)
            result = fx.run_runner(env)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("PASSPHRASE is unset or empty", status["reason"])
            self.assertFalse(fx.cli_log.exists())

    def test_short_passphrase_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            result = fx.run_runner(fx.env(PASSPHRASE=_SHORT_PASSPHRASE))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("under the 12-char floor", status["reason"])
            self.assertFalse(fx.cli_log.exists())

    def test_unmounted_destination_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fx._write_stub_mountpoint(rc=1)
            result = fx.run_runner()
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("NOT a mountpoint", status["reason"])
            self.assertFalse(fx.cli_log.exists())

    def test_missing_dest_path_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            missing = fx.dest_mount / "does-not-exist"
            result = fx.run_runner(fx.env(DUPLICATI_DEST_PATH=str(missing)))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("does not exist", status["reason"])

    def test_unwritable_dest_path_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fx.dest_path.chmod(0o555)
            try:
                result = fx.run_runner()
            finally:
                fx.dest_path.chmod(0o755)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("is not writable", status["reason"])

    def test_nonempty_dest_without_duplicati_volumes_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            (fx.dest_path / "not-ours.txt").write_text("wrong filesystem\n", encoding="utf-8")
            result = fx.run_runner()
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("holds no duplicati-* volumes", status["reason"])
            self.assertFalse(fx.cli_log.exists())

    def test_tmpfs_tempdir_refuses(self) -> None:
        shm = Path("/dev/shm")
        fstype = subprocess.run(
            ["stat", "-f", "-c", "%T", str(shm)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if fstype.returncode != 0 or fstype.stdout.strip() not in {"tmpfs", "ramfs"}:
            self.skipTest("/dev/shm is not tmpfs/ramfs on this host")
        with tempfile.TemporaryDirectory(dir=shm) as shm_tmp, tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            result = fx.run_runner(fx.env(DUPLICATI_TEMP_DIR=shm_tmp))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("RAM-backed", status["reason"])
            self.assertFalse(fx.cli_log.exists())


class TestSkipOrFail(unittest.TestCase):
    """A skip is not silently successful: stale / never-OK must escalate to OnFailure."""

    def test_lock_held_with_recent_ok_skips_and_does_not_stamp_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fx.status_file.write_text("result=OK\nwhen=now\nreason=\nlog=\n", encoding="utf-8")
            fd = _hold_exclusive_lock(fx.lock_file)
            try:
                result = fx.run_runner()
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "SKIPPED")
            self.assertIn("another run holds", status["reason"])
            self.assertFalse(fx.cli_log.exists())

    def test_lock_held_with_stale_ok_escalates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fx.status_file.write_text("result=OK\nwhen=old\nreason=\nlog=\n", encoding="utf-8")
            age = time.time() - (5 * 86400)
            os.utime(fx.status_file, (age, age))
            fd = _hold_exclusive_lock(fx.lock_file)
            try:
                result = fx.run_runner(fx.env(DUPLICATI_STALE_DAYS="3"))
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("escalating", status["reason"])

    def test_lock_held_with_no_prior_ok_escalates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fd = _hold_exclusive_lock(fx.lock_file)
            try:
                result = fx.run_runner()
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("escalating", status["reason"])


class TestCliOutcome(unittest.TestCase):
    def test_success_stamps_ok_and_preserves_no_auto_compact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            (fx.dest_path / "duplicati-existing.dblock.zip.aes").write_bytes(b"x")
            result = fx.run_runner()
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "OK")
            args = fx.cli_log.read_text(encoding="utf-8").splitlines()
            self.assertIn("--no-auto-compact=true", args)
            self.assertTrue(any(a.startswith("--dbpath=") for a in args))
            self.assertTrue(any(a.startswith("--tempdir=") for a in args))
            self.assertIn("--encryption-module=gpg", args)

    def test_cli_failure_stamps_failed_and_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fx._write_stub_duplicati_cli(rc=7)
            result = fx.run_runner()
            self.assertEqual(result.returncode, 7, msg=result.stdout + result.stderr)
            status = _parse_status(fx.status_file)
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("duplicati-cli rc=7", status["reason"])


class TestFailureReporter(unittest.TestCase):
    def test_missing_status_still_writes_failures_log_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            self.assertFalse(fx.status_file.exists())
            result = fx.run_reporter()
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            log = fx.failure_log.read_text(encoding="utf-8")
            self.assertIn("FAILURE", log)
            self.assertIn("no last-run.status present", log)
            self.assertIn("journal-stub-line", log)

    def test_notify_send_failure_does_not_change_exit_or_drop_the_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fx.status_file.write_text("result=FAILED\nwhen=now\nreason=boom\nlog=\n", encoding="utf-8")
            fx._write_stub_notify_send(rc=1)
            result = fx.run_reporter(fx.env(), "duplicati-backup.service")
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            log = fx.failure_log.read_text(encoding="utf-8")
            self.assertIn("result=FAILED", log)
            self.assertIn("reason=boom", log)
            self.assertIn("unit=duplicati-backup.service", log)


class TestInstallerBehavioral(unittest.TestCase):
    def _installer_home_env(self, fx: _LaneFixture, home: Path, **overrides: str) -> RedactedEnv:
        env = fx.env()
        env["HOME"] = str(home)
        env["USER"] = "coverage-user"
        env["SYSTEMCTL_LOG"] = str(fx.systemctl_log)
        env.update(overrides)
        return env

    def _write_cred(self, home: Path, body: str, mode: int = 0o600) -> Path:
        cred_dir = home / ".config" / "duplicati-backup"
        cred_dir.mkdir(parents=True)
        cred = cred_dir / "env"
        cred.write_text(body, encoding="utf-8")
        cred.chmod(mode)
        return cred

    def test_missing_cred_file_exits_1_and_does_not_enable_timer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            home = fx.root / "home"
            home.mkdir()
            result = fx.run_installer(self._installer_home_env(fx, home))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("is missing", result.stderr)
            self.assertFalse(fx.systemctl_log.exists())
            installed = home / ".local" / "bin" / "duplicati-scheduled-backup.bash"
            self.assertTrue(installed.is_file())
            self.assertFalse(installed.is_symlink())

    def test_cred_mode_not_600_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            home = fx.root / "home"
            home.mkdir()
            self._write_cred(home, "PASSPHRASE=placeholder-value\n", mode=0o644)
            result = fx.run_installer(self._installer_home_env(fx, home))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("expected 600", result.stderr)
            self.assertFalse(fx.systemctl_log.exists())

    def test_cred_without_passphrase_key_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            home = fx.root / "home"
            home.mkdir()
            self._write_cred(home, "OTHER=1\n", mode=0o600)
            result = fx.run_installer(self._installer_home_env(fx, home))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("has no PASSPHRASE= entry", result.stderr)

    def test_linger_not_yes_exits_1_and_does_not_enable_timer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            fx._write_stub_loginctl(linger="no")
            home = fx.root / "home"
            home.mkdir()
            self._write_cred(home, "PASSPHRASE=placeholder-value\n", mode=0o600)
            result = fx.run_installer(self._installer_home_env(fx, home))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Linger is NOT enabled", result.stderr)
            self.assertFalse(fx.systemctl_log.exists())

    def test_success_copies_units_reloads_and_does_not_enable_now(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _LaneFixture(tmp)
            home = fx.root / "home"
            home.mkdir()
            self._write_cred(home, "PASSPHRASE=placeholder-value\n", mode=0o600)
            result = fx.run_installer(self._installer_home_env(fx, home))
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertIn("timer is NOT enabled yet", combined)
            runner = home / ".local" / "bin" / "duplicati-scheduled-backup.bash"
            reporter = home / ".local" / "bin" / "duplicati-backup-failure.bash"
            self.assertTrue(runner.is_file() and not runner.is_symlink())
            self.assertTrue(reporter.is_file() and not reporter.is_symlink())
            self.assertEqual(runner.read_text(encoding="utf-8"), RUNNER_TEXT)
            unit_dir = home / ".config" / "systemd" / "user"
            self.assertTrue((unit_dir / "duplicati-backup.service").is_file())
            self.assertTrue((unit_dir / "duplicati-backup.timer").is_file())
            self.assertTrue((unit_dir / "duplicati-backup-failure.service").is_file())
            self.assertFalse((unit_dir / "duplicati-backup.service").is_symlink())
            logged = fx.systemctl_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(logged, ["--user daemon-reload"])
            self.assertEqual(stat.S_IMODE((home / ".config" / "duplicati-backup" / "env").stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
