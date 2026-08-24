#!/usr/bin/env python3
"""Hermetic coverage for util/juniper-backup.bash.

The production class (ml#1221): the draft assigned ``ENCRPYTED`` but gpg read
``${ENCRYPTED}`` — empty ``-o``, no artifact, exit 0. ml#1223 added the second
YubiKey recipient so key loss is not a restore-side SPOF, and counts
``:pubkey enc packet:`` rather than trusting argv.

These tests PATH-stub ``mountpoint`` / ``gpg`` / ``tar`` so they never touch a
real YubiKey or external drive. ``--source`` / ``--dest`` point at a tempfile
tree. ``RedactedEnv`` keeps subprocess env repr from leaking secrets.

Run: python3 -m unittest -v tests/test_juniper_backup.py
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKUP_SCRIPT = REPO_ROOT / "util" / "juniper-backup.bash"
SCRIPT_TEXT = BACKUP_SCRIPT.read_text(encoding="utf-8")
SCRIPT_TIMEOUT_SECONDS = 10

YUBIKEY_3C = "Yubikey-3c_2026-08-06"
YUBIKEY_3A = "Yubikey-3a_2026-08-11"


def write_executable(path: Path, body: str) -> None:
    # Shebang must be at byte 0 — strip the leading newline left by dedent("""...).
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


class BackupFixture:
    """Tiny source/dest tree + PATH stubs for mountpoint / gpg / tar."""

    def __init__(self, tmpdir: str):
        self.root = Path(tmpdir)
        self.bin_dir = self.root / "bin"
        self.source = self.root / "source" / "Juniper"
        self.dest = self.root / "dest"
        self.gpg_log = self.root / "gpg.log"
        self.mount_log = self.root / "mount.log"
        self.tar_log = self.root / "tar.log"
        self.bin_dir.mkdir()
        self.source.mkdir(parents=True)
        self.dest.mkdir()
        (self.source / "README").write_text("fixture\n", encoding="utf-8")
        self._write_fake_mountpoint()
        self._write_fake_gpg()
        self._write_fake_tar()
        self._write_fake_uuidgen()

    def _write_fake_mountpoint(self) -> None:
        write_executable(
            self.bin_dir / "mountpoint",
            """\
#!/usr/bin/env bash
printf 'mountpoint %s\\n' "$*" >> "${MOUNT_LOG}"
exit "${MOUNTPOINT_RC:-0}"
""",
        )

    def _write_fake_gpg(self) -> None:
        # --list-keys: preflight recipient resolve.
        # --list-packets: post-encrypt OpenPGP parse + recipient-count.
        # else: encrypt path; consume stdin so a real tar|gpg pipe does not SIGPIPE.
        write_executable(
            self.bin_dir / "gpg",
            """\
#!/usr/bin/env bash
printf 'gpg %s\\n' "$*" >> "${GPG_LOG}"
joined=" $* "
if [[ "${joined}" == *" --list-keys "* ]]; then
  exit "${GPG_LIST_KEYS_RC:-0}"
fi
if [[ "${joined}" == *" --list-packets "* ]]; then
  count="${GPG_PACKET_COUNT:-2}"
  i=0
  while (( i < count )); do
    echo ":pubkey enc packet: version 3, algo 1, keyid DEADBEEF"
    i=$((i + 1))
  done
  exit "${GPG_LIST_PACKETS_RC:-0}"
fi
outfile=""
prev=""
for arg in "$@"; do
  if [[ "${prev}" == "-o" ]]; then
    outfile="${arg}"
  fi
  prev="${arg}"
done
cat >/dev/null
if [[ -n "${outfile}" ]]; then
  if [[ "${GPG_WRITE_EMPTY:-0}" == "1" ]]; then
    : > "${outfile}"
  else
    printf 'dummy-openpgp\\n' > "${outfile}"
  fi
fi
exit "${GPG_ENCRYPT_RC:-0}"
""",
        )

    def _write_fake_tar(self) -> None:
        write_executable(
            self.bin_dir / "tar",
            """\
#!/usr/bin/env bash
printf 'tar %s\\n' "$*" >> "${TAR_LOG}"
printf 'dummy-tar\\n'
exit 0
""",
        )

    def _write_fake_uuidgen(self) -> None:
        # Cloud / slim images often omit uuidgen; the stamp only has to be unique per run.
        write_executable(
            self.bin_dir / "uuidgen",
            """\
#!/usr/bin/env bash
echo 00000000-0000-4000-8000-000000000001
""",
        )

    def env(self, **overrides: str) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{self.bin_dir}{os.pathsep}{env['PATH']}"
        env["GPG_LOG"] = str(self.gpg_log)
        env["MOUNT_LOG"] = str(self.mount_log)
        env["TAR_LOG"] = str(self.tar_log)
        env["MOUNTPOINT_RC"] = "0"
        env["GPG_LIST_KEYS_RC"] = "0"
        env["GPG_LIST_PACKETS_RC"] = "0"
        env["GPG_PACKET_COUNT"] = "2"
        env["GPG_ENCRYPT_RC"] = "0"
        env["GPG_WRITE_EMPTY"] = "0"
        env.update(overrides)
        return env

    def gpg_lines(self) -> list[str]:
        if not self.gpg_log.exists():
            return []
        return [line for line in self.gpg_log.read_text(encoding="utf-8").splitlines() if line]

    def tar_lines(self) -> list[str]:
        if not self.tar_log.exists():
            return []
        return [line for line in self.tar_log.read_text(encoding="utf-8").splitlines() if line]

    def archives(self) -> list[Path]:
        return sorted(self.dest.glob("*.tgz.gpg"))


def run_backup(fixture: BackupFixture, extra_args: list[str], **env_overrides: str) -> subprocess.CompletedProcess[str]:
    argv = [
        "bash",
        str(BACKUP_SCRIPT),
        "--source",
        str(fixture.source),
        "--dest",
        str(fixture.dest),
        *extra_args,
    ]
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env=fixture.env(**env_overrides),
        timeout=SCRIPT_TIMEOUT_SECONDS,
        cwd=str(REPO_ROOT),
    )


class TestSyntax(unittest.TestCase):
    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(BACKUP_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestScriptContracts(unittest.TestCase):
    """Static pins for the silent-success class the rewrite closed."""

    def test_strict_mode_includes_nounset_and_pipefail(self) -> None:
        self.assertIn("set -euo pipefail", SCRIPT_TEXT)

    def test_two_independent_yubikey_recipients(self) -> None:
        self.assertIn(YUBIKEY_3C, SCRIPT_TEXT)
        self.assertIn(YUBIKEY_3A, SCRIPT_TEXT)
        keys = [line for line in SCRIPT_TEXT.splitlines() if "Yubikey-" in line]
        self.assertGreaterEqual(len(keys), 2)

    def test_no_encrpyted_typo_split(self) -> None:
        # Comments may name the bug; live assignments must not resurrect the split
        # (ENCRPYTED written, ${ENCRYPTED} read → empty -o, exit 0, no archive).
        live = "\n".join(line for line in SCRIPT_TEXT.splitlines() if not line.lstrip().startswith("#"))
        self.assertNotIn("ENCRPYTED", live)
        self.assertNotIn("ENCRYPTED=", live)
        self.assertNotIn("${ENCRYPTED}", live)

    def test_streamed_tar_into_gpg_not_staged_plaintext(self) -> None:
        self.assertIn("tar -czf - -C", SCRIPT_TEXT)
        self.assertIn("| gpg --batch --yes", SCRIPT_TEXT)
        self.assertNotIn("tar -czf ${", SCRIPT_TEXT)

    def test_unmounted_dest_refuses_with_system_disk_warning(self) -> None:
        self.assertIn("mountpoint -q", SCRIPT_TEXT)
        self.assertIn("writing to an unmounted path would silently fill the system disk", SCRIPT_TEXT)

    def test_partial_cleanup_is_trapped_on_exit(self) -> None:
        self.assertIn("trap cleanup_partial EXIT", SCRIPT_TEXT)
        self.assertIn("removing partial archive", SCRIPT_TEXT)

    def test_recipient_packet_count_must_match_encrypt_keys(self) -> None:
        self.assertIn(":pubkey enc packet:", SCRIPT_TEXT)
        self.assertIn('"${FOUND_RECIPIENTS}" -ne "${#ENCRYPT_KEYS[@]}"', SCRIPT_TEXT)

    def test_tar_stores_paths_relative_to_parent(self) -> None:
        self.assertIn('tar -czf - -C "${SOURCE_PARENT}" "${SOURCE_LEAF}"', SCRIPT_TEXT)


class TestPreflight(unittest.TestCase):
    def test_unknown_argument_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, ["--not-a-flag"])
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown argument", result.stderr)
            self.assertEqual(fixture.tar_lines(), [])
            self.assertEqual(fixture.archives(), [])

    def test_missing_source_exits_one_before_gpg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            missing = fixture.root / "no-such-source"
            result = subprocess.run(
                ["bash", str(BACKUP_SCRIPT), "--source", str(missing), "--dest", str(fixture.dest)],
                capture_output=True,
                text=True,
                env=fixture.env(),
                timeout=SCRIPT_TIMEOUT_SECONDS,
                cwd=str(REPO_ROOT),
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("source not found", result.stderr)
            self.assertEqual(fixture.gpg_lines(), [])
            self.assertEqual(fixture.tar_lines(), [])

    def test_unmounted_dest_exits_one_and_never_tars(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, [], MOUNTPOINT_RC="1")
            self.assertEqual(result.returncode, 1)
            self.assertIn("is not a mount point", result.stderr)
            self.assertIn("silently fill the system disk", result.stderr)
            self.assertEqual(fixture.tar_lines(), [])
            encrypts = [line for line in fixture.gpg_lines() if " -e " in f" {line} "]
            self.assertEqual(encrypts, [])
            self.assertEqual(fixture.archives(), [])

    def test_unwritable_dest_exits_one_before_gpg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            fixture.dest.chmod(stat.S_IRUSR | stat.S_IXUSR)
            try:
                result = run_backup(fixture, [])
            finally:
                fixture.dest.chmod(stat.S_IRWXU)
            self.assertEqual(result.returncode, 1)
            self.assertIn("not writable", result.stderr)
            self.assertEqual(fixture.gpg_lines(), [])
            self.assertEqual(fixture.tar_lines(), [])

    def test_missing_gpg_recipient_exits_one_before_tar(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, [], GPG_LIST_KEYS_RC="1")
            self.assertEqual(result.returncode, 1)
            self.assertIn("gpg recipient not found", result.stderr)
            self.assertEqual(fixture.tar_lines(), [])
            self.assertEqual(fixture.archives(), [])
            self.assertTrue(any("--list-keys" in line for line in fixture.gpg_lines()))


class TestDryRun(unittest.TestCase):
    def test_dry_run_exits_zero_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, ["--dry-run"])
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("[dry-run] would run:", result.stdout)
            self.assertIn("recipients: 2", result.stdout)
            self.assertEqual(fixture.tar_lines(), [])
            self.assertEqual(fixture.archives(), [])
            encrypts = [line for line in fixture.gpg_lines() if " -e " in f" {line} "]
            self.assertEqual(encrypts, [])

    def test_dry_run_still_requires_a_mounted_dest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, ["--dry-run"], MOUNTPOINT_RC="1")
            self.assertEqual(result.returncode, 1)
            self.assertIn("is not a mount point", result.stderr)
            self.assertNotIn("[dry-run]", result.stdout)


class TestEncryptAndVerify(unittest.TestCase):
    def test_happy_path_writes_archive_with_two_recipient_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, [])
            archives = fixture.archives()
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertEqual(len(archives), 1)
            self.assertGreater(archives[0].stat().st_size, 0)
            self.assertIn("verified: valid OpenPGP message, 2 recipient(s)", result.stdout)
            self.assertTrue(fixture.tar_lines())
            encrypts = [line for line in fixture.gpg_lines() if " -e " in f" {line} "]
            self.assertEqual(len(encrypts), 1)
            self.assertIn("--batch --yes", encrypts[0])
            self.assertGreaterEqual(encrypts[0].count(" -r "), 2)

    def test_empty_archive_is_fatal_and_cleaned_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, [], GPG_WRITE_EMPTY="1")
            leftovers = fixture.archives()
            self.assertEqual(result.returncode, 1)
            self.assertIn("archive is empty", result.stderr)
            self.assertEqual(leftovers, [])

    def test_unparseable_openpgp_is_fatal_and_cleaned_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, [], GPG_LIST_PACKETS_RC="1")
            leftovers = fixture.archives()
            self.assertEqual(result.returncode, 1)
            self.assertIn("not a parseable OpenPGP message", result.stderr)
            self.assertEqual(leftovers, [])

    def test_recipient_count_mismatch_is_fatal_and_cleaned_up(self) -> None:
        # The #1223 class: argv asked for two recipients, the packet count is 1,
        # and a file that looks like a backup must not be left behind.
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, [], GPG_PACKET_COUNT="1")
            leftovers = fixture.archives()
            self.assertEqual(result.returncode, 1)
            self.assertIn("archive encrypted to 1 recipient(s), expected 2", result.stderr)
            self.assertEqual(leftovers, [])

    def test_encrypt_failure_removes_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = BackupFixture(tmpdir)
            result = run_backup(fixture, [], GPG_ENCRYPT_RC="1")
            leftovers = fixture.archives()
            self.assertEqual(result.returncode, 1)
            self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
