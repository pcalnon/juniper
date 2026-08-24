"""Hermetic coverage for the scheduled-backup lane (#1292).

The 2026-07-13 archive damage went undetected for six weeks because backups
ran under a gnome-shell scope with Linger=no and nothing reported a stop.
These tests PATH-stub `mountpoint` / `duplicati-cli` / `journalctl` /
`notify-send` / `loginctl` / `systemctl` so the guards, skip/escalate
contract, installer, and OnFailure reporter are proven without touching a
real Duplicati process, mount, or user systemd.

util/ is not pre-commit-lint-gated; this unittest is the gate.
"""

from __future__ import annotations

import os
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
FAILURE_REPORTER = REPO_ROOT / "util" / "duplicati_backup_failure.bash"
INSTALLER = REPO_ROOT / "util" / "install_duplicati_timer.bash"
UNIT_DIR = REPO_ROOT / "util" / "systemd"
SERVICE_UNIT = UNIT_DIR / "duplicati-backup.service"
TIMER_UNIT = UNIT_DIR / "duplicati-backup.timer"
FAILURE_UNIT = UNIT_DIR / "duplicati-backup-failure.service"
SCRIPT_TIMEOUT_SECONDS = 20
# Longer than SCRIPT_TIMEOUT: the lock holder must outlive the runner under test.
LOCK_HOLDER_SECONDS = 40
PASSPHRASE_OK = "fixture-passphrase"  # nosec B105 — test value; RedactedEnv masks it
PASSPHRASE_SHORT = "short"  # nosec B105 — 5 chars, under the 12-char floor


def write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


def _status_fields(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            fields[key] = value
    return fields


class BackupFixture:
    """Temp dest/state/source + PATH stubs for the scheduled runner."""

    def __init__(self, tmpdir: str, *, mount_ok: bool = True, cli_rc: int = 0, fstype: str | None = None) -> None:
        self.root = Path(tmpdir)
        self.bin_dir = self.root / "bin"
        self.state_dir = self.root / "state"
        self.mount = self.root / "mnt"
        self.dest_path = self.mount / "Ubuntu"
        self.temp_dir = self.root / "staging"
        self.source = self.root / "source"
        self.dbpath = self.root / "local.sqlite"
        self.cli_log = self.root / "cli.log"
        self.bin_dir.mkdir()
        self.state_dir.mkdir()
        self.dest_path.mkdir(parents=True)
        self.temp_dir.mkdir()
        self.source.mkdir()
        self.dbpath.write_text("not-a-real-db\n", encoding="utf-8")
        self._write_mountpoint(mount_ok)
        self._write_duplicati_cli(cli_rc)
        if fstype is not None:
            self._write_stat_fstype(fstype)

    def _write_mountpoint(self, mount_ok: bool) -> None:
        rc = 0 if mount_ok else 1
        write_executable(
            self.bin_dir / "mountpoint",
            f"""\
#!/usr/bin/env bash
exit {rc}
""",
        )

    def _write_duplicati_cli(self, cli_rc: int) -> None:
        write_executable(
            self.bin_dir / "duplicati-cli",
            f"""\
#!/usr/bin/env bash
printf '%s\\n' "$@" >> "${{CLI_LOG}}"
exit {cli_rc}
""",
        )

    def _write_stat_fstype(self, fstype: str) -> None:
        write_executable(
            self.bin_dir / "stat",
            f"""\
#!/usr/bin/env bash
if [[ "$1" == "-f" ]]; then
  printf '%s\\n' "{fstype}"
  exit 0
fi
exec /usr/bin/stat "$@"
""",
        )

    def env(self, **overrides: str) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        for key in list(env):
            if key == "PASSPHRASE" or key.startswith("DUPLICATI_"):
                del env[key]
        env["PATH"] = f"{self.bin_dir}{os.pathsep}{env.get('PATH', '/usr/bin:/bin')}"
        env["CLI_LOG"] = str(self.cli_log)
        env["PASSPHRASE"] = PASSPHRASE_OK
        env["DUPLICATI_DEST_URL"] = f"file://{self.dest_path}"
        env["DUPLICATI_DEST_PATH"] = str(self.dest_path)
        env["DUPLICATI_DEST_MOUNT"] = str(self.mount)
        env["DUPLICATI_DBPATH"] = str(self.dbpath)
        env["DUPLICATI_SOURCE"] = str(self.source)
        env["DUPLICATI_STATE_DIR"] = str(self.state_dir)
        env["DUPLICATI_TEMP_DIR"] = str(self.temp_dir)
        env.update(overrides)
        return env

    def cli_args(self) -> list[str]:
        if not self.cli_log.exists():
            return []
        return self.cli_log.read_text(encoding="utf-8").splitlines()

    def status_path(self) -> Path:
        return self.state_dir / "last-run.status"

    def stamp_ok(self, *, age_seconds: int = 0) -> None:
        self.status_path().write_text(
            "result=OK\nwhen=2026-08-20T00:00:00+00:00\nreason=\nlog=/dev/null\n",
            encoding="utf-8",
        )
        if age_seconds:
            stamped = time.time() - age_seconds
            os.utime(self.status_path(), (stamped, stamped))


def run_runner(fixture: BackupFixture, **env_overrides: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(RUNNER)],
        capture_output=True,
        text=True,
        env=fixture.env(**env_overrides),
        timeout=SCRIPT_TIMEOUT_SECONDS,
        cwd=str(REPO_ROOT),
    )


def hold_lock(lock_file: Path) -> subprocess.Popen[str]:
    """Hold flock on ``backup.lock`` in a child so the runner takes the skip path."""
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    ready = lock_file.parent / "lock.ready"
    proc = subprocess.Popen(
        [
            "bash",
            "-c",
            'exec 9>"$1"; flock -n 9 || exit 2; printf ok > "$2"; sleep "$3"',
            "_",
            str(lock_file),
            str(ready),
            str(LOCK_HOLDER_SECONDS),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if ready.exists():
            return proc
        if proc.poll() is not None:
            raise AssertionError(f"lock holder exited {proc.returncode} before ready")
        time.sleep(0.02)
    proc.kill()
    raise AssertionError("lock holder did not become ready")


class TestSyntax(unittest.TestCase):
    def test_runner_bash_syntax(self) -> None:
        result = subprocess.run(["bash", "-n", str(RUNNER)], capture_output=True, text=True, timeout=SCRIPT_TIMEOUT_SECONDS)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_failure_reporter_bash_syntax(self) -> None:
        result = subprocess.run(["bash", "-n", str(FAILURE_REPORTER)], capture_output=True, text=True, timeout=SCRIPT_TIMEOUT_SECONDS)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_installer_bash_syntax(self) -> None:
        result = subprocess.run(["bash", "-n", str(INSTALLER)], capture_output=True, text=True, timeout=SCRIPT_TIMEOUT_SECONDS)
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestScheduledBackupGuards(unittest.TestCase):
    def test_empty_passphrase_refuses_without_invoking_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_runner(fixture, PASSPHRASE="")
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            self.assertEqual(_status_fields(fixture.status_path())["result"], "FAILED")
            self.assertIn("PASSPHRASE is unset or empty", _status_fields(fixture.status_path())["reason"])

    def test_short_passphrase_refuses_without_invoking_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_runner(fixture, PASSPHRASE=PASSPHRASE_SHORT)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            self.assertIn("under the 12-char floor", _status_fields(fixture.status_path())["reason"])

    def test_unmounted_destination_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir, mount_ok=False)
            result = run_runner(fixture)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            self.assertIn("NOT a mountpoint", _status_fields(fixture.status_path())["reason"])

    def test_missing_destination_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            missing = fixture.root / "no-such-dest"
            result = run_runner(fixture, DUPLICATI_DEST_PATH=str(missing))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            self.assertIn("does not exist", _status_fields(fixture.status_path())["reason"])

    def test_nonempty_dest_without_duplicati_volumes_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            (fixture.dest_path / "readme.txt").write_text("not ours\n", encoding="utf-8")
            result = run_runner(fixture)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            self.assertIn("wrong filesystem", _status_fields(fixture.status_path())["reason"])

    def test_tmpfs_staging_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir, fstype="tmpfs")
            result = run_runner(fixture)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            self.assertIn("tmpfs", _status_fields(fixture.status_path())["reason"])


class TestSkipOrFail(unittest.TestCase):
    def test_lock_held_with_recent_ok_skips_and_stamps_current_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            fixture.stamp_ok()
            holder = hold_lock(fixture.state_dir / "backup.lock")
            try:
                result = run_runner(fixture)
            finally:
                holder.kill()
                holder.wait(timeout=5)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            fields = _status_fields(fixture.status_path())
            self.assertEqual(fields["result"], "SKIPPED")
            self.assertIn("another run holds", fields["reason"])
            # A skip must not freeze last-run.status at the old OK timestamp.
            age = time.time() - fixture.status_path().stat().st_mtime
            self.assertLess(age, 10.0)

    def test_lock_held_without_prior_ok_escalates_to_failure(self) -> None:
        """No successful run in STALE_DAYS: skip would be a silent stop."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            holder = hold_lock(fixture.state_dir / "backup.lock")
            try:
                result = run_runner(fixture)
            finally:
                holder.kill()
                holder.wait(timeout=5)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            fields = _status_fields(fixture.status_path())
            self.assertEqual(fields["result"], "FAILED")
            self.assertIn("escalating", fields["reason"])

    def test_lock_held_with_stale_ok_escalates_to_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            fixture.stamp_ok(age_seconds=4 * 86400)
            holder = hold_lock(fixture.state_dir / "backup.lock")
            try:
                result = run_runner(fixture)
            finally:
                holder.kill()
                holder.wait(timeout=5)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            self.assertEqual(_status_fields(fixture.status_path())["result"], "FAILED")
            self.assertIn("escalating", _status_fields(fixture.status_path())["reason"])

    def test_open_db_with_recent_ok_skips_without_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            fixture.stamp_ok()
            with fixture.dbpath.open("a", encoding="utf-8"):
                result = run_runner(fixture)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.cli_args(), [])
            fields = _status_fields(fixture.status_path())
            self.assertEqual(fields["result"], "SKIPPED")
            self.assertIn("already has", fields["reason"])


class TestCliInvocation(unittest.TestCase):
    def test_happy_path_invokes_cli_with_compact_guard_and_hides_passphrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            (fixture.dest_path / "duplicati-existing.dblock.zip.aes").write_bytes(b"x")
            result = run_runner(fixture)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            args = fixture.cli_args()
            self.assertGreater(len(args), 0)
            self.assertEqual(args[0], "backup")
            self.assertIn("--no-auto-compact=true", args)
            self.assertIn("--encryption-module=gpg", args)
            self.assertIn(f"--tempdir={fixture.temp_dir}", args)
            self.assertIn(f"--dbpath={fixture.dbpath}", args)
            joined = "\n".join(args)
            self.assertNotIn(PASSPHRASE_OK, joined)
            self.assertEqual(_status_fields(fixture.status_path())["result"], "OK")

    def test_cli_nonzero_writes_failed_status_and_exits_that_rc(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir, cli_rc=7)
            result = run_runner(fixture)
            self.assertEqual(result.returncode, 7, msg=result.stdout + result.stderr)
            fields = _status_fields(fixture.status_path())
            self.assertEqual(fields["result"], "FAILED")
            self.assertIn("rc=7", fields["reason"])

    def test_source_retains_no_auto_compact(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("--no-auto-compact=true", text)


class TestFailureReporter(unittest.TestCase):
    def _reporter_env(self, tmpdir: str, *, notify_fail: bool, journal_fail: bool) -> tuple[Path, RedactedEnv]:
        root = Path(tmpdir)
        bin_dir = root / "bin"
        state = root / "state"
        bin_dir.mkdir()
        state.mkdir()
        write_executable(
            bin_dir / "journalctl",
            f"""\
#!/usr/bin/env bash
{"echo journal-unavailable >&2; exit 1" if journal_fail else "printf 'journal-tail\\n'; exit 0"}
""",
        )
        # Always stub notify-send so a host binary cannot fire a real desktop
        # notification (and so `command -v` is deterministic).
        write_executable(
            bin_dir / "notify-send",
            f"""\
#!/usr/bin/env bash
exit {1 if notify_fail else 0}
""",
        )
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '/usr/bin:/bin')}"
        env["DUPLICATI_STATE_DIR"] = str(state)
        env["HOME"] = str(root / "home")
        return state, env

    def _run_reporter(self, env: RedactedEnv, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(FAILURE_REPORTER), *argv],
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
        )

    def test_durable_record_includes_status_and_exits_zero_when_notify_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state, env = self._reporter_env(tmpdir, notify_fail=True, journal_fail=True)
            (state / "last-run.status").write_text("result=FAILED\nreason=cli-died\n", encoding="utf-8")
            result = self._run_reporter(env, "duplicati-backup.service")
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            log = (state / "failures.log").read_text(encoding="utf-8")
            self.assertIn("FAILURE  unit=duplicati-backup.service", log)
            self.assertIn("result=FAILED", log)
            self.assertIn("cli-died", log)
            self.assertIn("journal unavailable", log)

    def test_missing_status_is_recorded_and_notify_success_still_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state, env = self._reporter_env(tmpdir, notify_fail=False, journal_fail=False)
            result = self._run_reporter(env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            log = (state / "failures.log").read_text(encoding="utf-8")
            self.assertIn("no last-run.status present", log)
            self.assertIn("journal-tail", log)


class TestInstaller(unittest.TestCase):
    def _home_env(self, tmpdir: str, *, linger: str = "yes") -> tuple[Path, Path, RedactedEnv]:
        root = Path(tmpdir)
        home = root / "home"
        bin_dir = root / "bin"
        home.mkdir()
        bin_dir.mkdir()
        systemctl_log = root / "systemctl.log"
        write_executable(
            bin_dir / "loginctl",
            f"""\
#!/usr/bin/env bash
printf '%s\\n' "{linger}"
""",
        )
        write_executable(
            bin_dir / "systemctl",
            """\
#!/usr/bin/env bash
printf '%s\\n' "$*" >> "${SYSTEMCTL_LOG}"
exit 0
""",
        )
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '/usr/bin:/bin')}"
        env["HOME"] = str(home)
        env["USER"] = "fixture-user"
        env["SYSTEMCTL_LOG"] = str(systemctl_log)
        return home, systemctl_log, env

    def _write_creds(self, home: Path, *, mode: int = 0o600, body: str = "PASSPHRASE=fixture-passphrase\n") -> Path:
        cred = home / ".config" / "duplicati-backup" / "env"
        cred.parent.mkdir(parents=True)
        cred.write_text(body, encoding="utf-8")
        cred.chmod(mode)
        return cred

    def _run(self, env: RedactedEnv) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(INSTALLER)],
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
        )

    def test_happy_path_copies_not_symlinks_and_does_not_enable_timer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home, systemctl_log, env = self._home_env(tmpdir)
            self._write_creds(home)
            result = self._run(env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            runner = home / ".local" / "bin" / "duplicati-scheduled-backup.bash"
            reporter = home / ".local" / "bin" / "duplicati-backup-failure.bash"
            service = home / ".config" / "systemd" / "user" / "duplicati-backup.service"
            self.assertTrue(runner.is_file())
            self.assertFalse(runner.is_symlink())
            self.assertEqual(runner.read_text(encoding="utf-8"), RUNNER.read_text(encoding="utf-8"))
            self.assertTrue(reporter.is_file())
            self.assertFalse(reporter.is_symlink())
            self.assertTrue(service.is_file())
            self.assertFalse(service.is_symlink())
            self.assertIn("The timer is NOT enabled yet", result.stdout)
            ctl = systemctl_log.read_text(encoding="utf-8") if systemctl_log.exists() else ""
            self.assertIn("--user daemon-reload", ctl)
            self.assertNotIn("enable", ctl)

    def test_missing_cred_file_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _home, systemctl_log, env = self._home_env(tmpdir)
            result = self._run(env)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("is missing", result.stderr)
            self.assertFalse(systemctl_log.exists())

    def test_cred_mode_not_600_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home, systemctl_log, env = self._home_env(tmpdir)
            cred = self._write_creds(home, mode=0o644)
            # Honor umask: chmod again in case write_text raced.
            cred.chmod(0o644)
            self.assertEqual(stat.S_IMODE(cred.stat().st_mode), 0o644)
            result = self._run(env)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("expected 600", result.stderr)
            self.assertFalse(systemctl_log.exists())

    def test_cred_without_passphrase_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home, systemctl_log, env = self._home_env(tmpdir)
            self._write_creds(home, body="OTHER=1\n")
            result = self._run(env)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("no PASSPHRASE=", result.stderr)
            self.assertFalse(systemctl_log.exists())

    def test_linger_disabled_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home, systemctl_log, env = self._home_env(tmpdir, linger="no")
            self._write_creds(home)
            result = self._run(env)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Linger is NOT enabled", result.stderr)
            self.assertFalse(systemctl_log.exists())


class TestSystemdUnits(unittest.TestCase):
    def test_service_chains_onfailure_and_hides_passphrase_from_cmdline(self) -> None:
        text = SERVICE_UNIT.read_text(encoding="utf-8")
        self.assertIn("OnFailure=duplicati-backup-failure.service", text)
        self.assertIn("TimeoutStartSec=infinity", text)
        self.assertIn("EnvironmentFile=%h/.config/duplicati-backup/env", text)
        self.assertNotIn("PASSPHRASE", text)
        self.assertIn("ExecStart=%h/.local/bin/duplicati-scheduled-backup.bash", text)

    def test_timer_is_persistent_overnight(self) -> None:
        text = TIMER_UNIT.read_text(encoding="utf-8")
        self.assertIn("Persistent=true", text)
        self.assertIn("OnCalendar=", text)
        self.assertIn("Unit=duplicati-backup.service", text)

    def test_failure_unit_invokes_reporter_and_does_not_chain_another_onfailure(self) -> None:
        text = FAILURE_UNIT.read_text(encoding="utf-8")
        self.assertIn("ExecStart=%h/.local/bin/duplicati-backup-failure.bash duplicati-backup.service", text)
        directives = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        self.assertFalse(
            any(ln.startswith("OnFailure=") for ln in directives),
            "reporter unit must not chain OnFailure= (a failing reporter would loop)",
        )


if __name__ == "__main__":
    unittest.main()
