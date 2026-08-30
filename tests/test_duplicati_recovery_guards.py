#!/usr/bin/env python3
"""
Hermetic coverage for Duplicati *recovery* tooling (#1268 / #1281).

These scripts are not the scheduled-backup lane and not juniper-backup: they
are the fail-closed wrappers around a destructive archive repair
(``purge-broken-files``) and the only check that can see a file-vs-process
passphrase divergence. ``util/ad-hoc`` is outside every pre-commit Python
hook's scope, so this suite IS the gate.

Pins, each able to fail for the reason it exists:

* dest override derives the mount from DEST (the fail-open was a hardcoded
  ``/mnt/Backups/Ubuntu`` while the purge ran against a different URL);
* remote destinations refuse (cannot be mount-checked);
* unmounted dest refuse (an unmounted mountpoint lists empty and a purge
  against "nothing there" is how a config error becomes data loss);
* too-few visible ``*.gpg`` volumes refuse (same empty-dest shape);
* missing / empty ``DUPLICATI_PW_FILE`` refuse (no silent ``.env`` fallback
  onto the web-UI password);
* the assembled argv actually contains ``--dry-run=true``; this script
  cannot apply a live purge;
* the passphrase is exported, never placed on argv;
* the credential file is parsed, never ``source``d;
* ``secret_check`` MATCH / DIFFER / UNDETERMINED, without writing any
  secret value to stdout.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
import unittest.mock as mock
import uuid
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
PURGE_SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "duplicati_purge_dryrun.bash"
SECRET_CHECK = REPO_ROOT / "util" / "ad-hoc" / "duplicati_secret_check.py"
SCRIPT_TIMEOUT_SECONDS = 20
UBUNTU_MOUNT = "/mnt/Backups/Ubuntu"
# Throwaway literals -- not credentials. Distinct so a leak of either is visible.
FIXTURE_A = "unit-test-fixture-AAA"
FIXTURE_B = "unit-test-fixture-BBB"


def _load_secret_check():
    spec = importlib.util.spec_from_file_location("duplicati_secret_check", SECRET_CHECK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sc = _load_secret_check()


def write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class PurgeHarness:
    """Temp dest + PATH stubs for ``duplicati_purge_dryrun.bash``."""

    def __init__(self, tmp: Path, *, mounted: bool = True) -> None:
        self.root = tmp
        self.dest = tmp / "dest"
        self.dest.mkdir()
        self.db = tmp / "drill.sqlite"
        self.db.write_text("not-a-real-db\n", encoding="utf-8")
        self.pw = tmp / "archive.pass"
        self.pw.write_text(f"PASSPHRASE={FIXTURE_A}\n", encoding="utf-8")
        self.bin = tmp / "bin"
        self.bin.mkdir()
        self.cli_log = tmp / "duplicati-cli.log"
        self.mount_log = tmp / "mountpoint.log"
        write_executable(
            self.bin / "mountpoint",
            f"""\
#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{self.mount_log}"
exit {0 if mounted else 1}
""",
        )
        write_executable(
            self.bin / "duplicati-cli",
            f"""\
#!/usr/bin/env bash
printf 'argv:' >> "{self.cli_log}"
printf ' %q' "$@" >> "{self.cli_log}"
printf '\\n' >> "{self.cli_log}"
if [ -n "${{PASSPHRASE+x}}" ]; then
  printf 'env_passphrase_set=1 len=%s\\n' "${{#PASSPHRASE}}" >> "{self.cli_log}"
else
  printf 'env_passphrase_set=0\\n' >> "{self.cli_log}"
fi
exit 0
""",
        )

    def populate_volumes(self, count: int) -> None:
        for i in range(count):
            (self.dest / f"vol-{i:03d}.gpg").write_text("", encoding="utf-8")

    def env(self, **overrides: str) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{self.bin}{os.pathsep}{env.get('PATH', '')}"
        env["DUPLICATI_PW_FILE"] = str(self.pw)
        env.pop("DUPLICATI_PW_KEY", None)
        env.update(overrides)
        return env

    def run(self, *extra_args: str, env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        dest_url = f"file://{self.dest}"
        return subprocess.run(
            ["bash", str(PURGE_SCRIPT), str(self.db), dest_url, "5", *extra_args],
            capture_output=True,
            text=True,
            env=env if env is not None else self.env(),
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
            check=False,
        )

    def cli_log_text(self) -> str:
        if not self.cli_log.exists():
            return ""
        return self.cli_log.read_text(encoding="utf-8")


def _assert_no_secret_leak(testcase: unittest.TestCase, blob: str) -> None:
    testcase.assertNotIn(FIXTURE_A, blob)
    testcase.assertNotIn(FIXTURE_B, blob)


class TestPurgeDryrunSourceContract(unittest.TestCase):
    """Structural pins so a wording pass cannot re-open the fail-open paths."""

    def setUp(self) -> None:
        self.src = PURGE_SCRIPT.read_text(encoding="utf-8")

    def test_script_exists(self) -> None:
        self.assertTrue(PURGE_SCRIPT.is_file(), msg=f"missing {PURGE_SCRIPT}")

    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(PURGE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_dry_run_is_hardcoded_true(self) -> None:
        self.assertIn("--dry-run=true", self.src)
        self.assertNotIn("--dry-run=false", self.src)
        self.assertNotIn("purge-broken-files --force", self.src)

    def test_credential_file_is_parsed_never_sourced(self) -> None:
        self.assertNotRegex(self.src, r"(?m)^\s*(source|\.)\s+(\"|')?\$\{?PPFILE")
        self.assertNotRegex(self.src, r"(?m)^\s*(source|\.)\s+(\"|')?\$\{?DUPLICATI_PW_FILE")

    def test_passphrase_is_exported_not_placed_on_the_cli_array(self) -> None:
        self.assertIn("export PASSPHRASE", self.src)
        cmd_block = self.src.split("CMD=(", 1)[1].split(")", 1)[0]
        self.assertNotIn("PASSPHRASE", cmd_block)
        self.assertNotIn("passphrase", cmd_block.lower())

    def test_mount_is_derived_from_dest_not_a_ubuntu_literal(self) -> None:
        """#1268: dest override used to mount-check Ubuntu while purging elsewhere."""
        self.assertIn("file://*) MOUNT=${DEST#file://} ;;", self.src)
        self.assertNotIn(f"MOUNT={UBUNTU_MOUNT}", self.src)
        self.assertNotIn(f'MOUNT="{UBUNTU_MOUNT}"', self.src)


class TestPurgeDryrunPreflight(unittest.TestCase):
    def test_remote_destination_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp))
            result = subprocess.run(
                ["bash", str(PURGE_SCRIPT), str(harness.db), "s3://bucket/archive", "5"],
                capture_output=True,
                text=True,
                env=harness.env(),
                timeout=SCRIPT_TIMEOUT_SECONDS,
                cwd=str(REPO_ROOT),
                check=False,
            )
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("REFUSING: only local file:// destinations", result.stderr)
            self.assertEqual(harness.cli_log_text(), "")
            _assert_no_secret_leak(self, result.stdout + result.stderr)

    def test_unmounted_dest_is_refused_and_never_invokes_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp), mounted=False)
            result = harness.run()
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("is not a mountpoint", result.stderr)
            self.assertEqual(harness.cli_log_text(), "")
            self.assertIn(f"mount to check: {harness.dest}", result.stdout)
            self.assertNotIn(f"mount to check: {UBUNTU_MOUNT}", result.stdout)

    def test_dest_override_mount_checks_the_override_not_ubuntu(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp), mounted=False)
            result = harness.run()
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            mount_args = harness.mount_log.read_text(encoding="utf-8")
            self.assertIn(str(harness.dest), mount_args)
            self.assertNotIn(UBUNTU_MOUNT, mount_args)
            self.assertNotIn(UBUNTU_MOUNT, result.stdout)
            self.assertNotIn(UBUNTU_MOUNT, result.stderr)

    def test_too_few_volumes_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp), mounted=True)
            harness.populate_volumes(5)
            result = harness.run()
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("REFUSING: only 5 volumes visible", result.stderr)
            self.assertEqual(harness.cli_log_text(), "")

    def test_missing_passphrase_file_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp), mounted=True)
            harness.populate_volumes(100)
            env = harness.env()
            env.pop("DUPLICATI_PW_FILE", None)
            result = harness.run(env=env)
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("set DUPLICATI_PW_FILE to the ARCHIVE passphrase file", result.stderr)
            self.assertEqual(harness.cli_log_text(), "")

    def test_empty_passphrase_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp), mounted=True)
            harness.populate_volumes(100)
            harness.pw.write_text("PASSPHRASE=\n", encoding="utf-8")
            result = harness.run()
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("empty passphrase", result.stderr)
            self.assertEqual(harness.cli_log_text(), "")

    def test_missing_database_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp), mounted=True)
            harness.populate_volumes(100)
            harness.db.unlink()
            result = harness.run()
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("database not readable", result.stderr)
            self.assertEqual(harness.cli_log_text(), "")

    def test_dry_run_reaches_cli_with_flag_and_without_passphrase_on_argv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = PurgeHarness(Path(tmp), mounted=True)
            harness.populate_volumes(100)
            result = harness.run()
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            log = harness.cli_log_text()
            self.assertIn("purge-broken-files", log)
            self.assertIn("--dry-run=true", log)
            self.assertNotIn(FIXTURE_A, log)
            self.assertNotIn("--passphrase", log)
            self.assertIn("env_passphrase_set=1", log)
            self.assertIn(f"mount to check: {harness.dest}", result.stdout)
            self.assertNotIn(f"mount to check: {UBUNTU_MOUNT}", result.stdout)
            _assert_no_secret_leak(self, result.stdout + result.stderr)
            # Length is logged (the live script does this); the value is not.
            self.assertIn(f"({len(FIXTURE_A)} chars", result.stdout)


class TestSecretFromFile(unittest.TestCase):
    def test_plain_key_equals_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cred"
            path.write_text(f"PASSPHRASE={FIXTURE_A}\n", encoding="utf-8")
            self.assertEqual(sc.secret_from_file(str(path), "PASSPHRASE"), FIXTURE_A)

    def test_export_and_single_quotes_are_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cred"
            path.write_text(f"export PASSPHRASE='{FIXTURE_A}'\n", encoding="utf-8")
            self.assertEqual(sc.secret_from_file(str(path), "PASSPHRASE"), FIXTURE_A)

    def test_double_quotes_are_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cred"
            path.write_text(f'PASSPHRASE="{FIXTURE_A}"\n', encoding="utf-8")
            self.assertEqual(sc.secret_from_file(str(path), "PASSPHRASE"), FIXTURE_A)

    def test_missing_key_is_none_not_the_whole_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cred"
            path.write_text(f"OTHER={FIXTURE_B}\n", encoding="utf-8")
            self.assertIsNone(sc.secret_from_file(str(path), "PASSPHRASE"))

    def test_wrong_key_is_not_silently_taken_from_another_line(self) -> None:
        """Same-length secrets are indistinguishable by length — the key must bind."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cred"
            path.write_text(
                f"WEB_UI_PASSWORD={FIXTURE_B}\nPASSPHRASE={FIXTURE_A}\n",
                encoding="utf-8",
            )
            self.assertEqual(sc.secret_from_file(str(path), "PASSPHRASE"), FIXTURE_A)
            self.assertEqual(sc.secret_from_file(str(path), "WEB_UI_PASSWORD"), FIXTURE_B)


class TestFindPid(unittest.TestCase):
    def test_skips_grep_and_the_checker_itself(self) -> None:
        ps_out = textwrap.dedent(f"""\
            PID COMMAND
              1 /sbin/init
            222 duplicati-cli backup {UBUNTU_MOUNT}
            333 grep duplicati-cli backup
            444 pgrep duplicati-cli
            555 python3 util/ad-hoc/duplicati_secret_check.py --match-cmd duplicati-cli backup
            """)
        completed = subprocess.CompletedProcess(args=["ps"], returncode=0, stdout=ps_out, stderr="")
        with mock.patch.object(sc.subprocess, "run", return_value=completed):
            hits = sc.find_pid("duplicati-cli backup")
        self.assertEqual(hits, [222])


class TestSecretCheckCli(unittest.TestCase):
    def _write_cred(self, tmp: Path, body: str) -> Path:
        path = tmp / "cred.env"
        path.write_text(body, encoding="utf-8")
        return path

    def _spawn_holder(self, secret: str) -> subprocess.Popen[str]:
        # Hold PASSPHRASE in a child so /proc/<pid>/environ is readable as us.
        env = RedactedEnv(os.environ, PASSPHRASE=secret)
        return subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

    def _run_checker(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SECRET_CHECK), *argv],
            capture_output=True,
            text=True,
            env=RedactedEnv(os.environ),
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
            check=False,
        )

    def test_refuses_without_pid_or_match_cmd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cred = self._write_cred(Path(tmp), f"PASSPHRASE={FIXTURE_A}\n")
            result = self._run_checker("--file", str(cred), "--key", "PASSPHRASE")
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("REFUSING: give --pid or --match-cmd", result.stdout)
            _assert_no_secret_leak(self, result.stdout + result.stderr)

    def test_undetermined_when_no_process_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cred = self._write_cred(Path(tmp), f"PASSPHRASE={FIXTURE_A}\n")
            needle = f"no-such-duplicati-process-{uuid.uuid4().hex}"
            result = self._run_checker(
                "--match-cmd",
                needle,
                "--file",
                str(cred),
                "--key",
                "PASSPHRASE",
            )
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("UNDETERMINED: no process matches", result.stdout)
            _assert_no_secret_leak(self, result.stdout + result.stderr)

    def test_match_when_file_still_holds_what_the_process_uses(self) -> None:
        holder = self._spawn_holder(FIXTURE_A)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cred = self._write_cred(Path(tmp), f"PASSPHRASE={FIXTURE_A}\n")
                result = self._run_checker(
                    "--pid",
                    str(holder.pid),
                    "--file",
                    str(cred),
                    "--key",
                    "PASSPHRASE",
                )
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertIn("MATCH", result.stdout)
                self.assertNotIn("DIFFER", result.stdout)
                _assert_no_secret_leak(self, result.stdout + result.stderr)
        finally:
            holder.kill()
            holder.wait(timeout=5)

    def test_differ_does_not_print_either_secret(self) -> None:
        """#1281: the running job kept a rotated secret in RAM only."""
        holder = self._spawn_holder(FIXTURE_A)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cred = self._write_cred(Path(tmp), f"PASSPHRASE={FIXTURE_B}\n")
                result = self._run_checker(
                    "--pid",
                    str(holder.pid),
                    "--file",
                    str(cred),
                    "--key",
                    "PASSPHRASE",
                )
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn("DIFFER", result.stdout)
                self.assertNotIn("MATCH —", result.stdout)
                _assert_no_secret_leak(self, result.stdout + result.stderr)
        finally:
            holder.kill()
            holder.wait(timeout=5)

    def test_missing_key_on_disk_is_differ_not_undetermined(self) -> None:
        holder = self._spawn_holder(FIXTURE_A)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cred = self._write_cred(Path(tmp), f"WEB_UI_PASSWORD={FIXTURE_B}\n")
                result = self._run_checker(
                    "--pid",
                    str(holder.pid),
                    "--file",
                    str(cred),
                    "--key",
                    "PASSPHRASE",
                )
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn("has no PASSPHRASE= entry", result.stdout)
                _assert_no_secret_leak(self, result.stdout + result.stderr)
        finally:
            holder.kill()
            holder.wait(timeout=5)

    def test_gone_pid_is_undetermined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cred = self._write_cred(Path(tmp), f"PASSPHRASE={FIXTURE_A}\n")
            result = self._run_checker(
                "--pid",
                "1073741824",
                "--file",
                str(cred),
                "--key",
                "PASSPHRASE",
            )
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertTrue(
                "UNDETERMINED: pid 1073741824 is gone" in result.stdout or "has no PASSPHRASE in its environment" in result.stdout,
                msg=result.stdout + result.stderr,
            )
            _assert_no_secret_leak(self, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
