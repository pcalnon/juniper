#!/usr/bin/env python3
"""Hermetic restore-integrity coverage for the #1319 Duplicati harnesses.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/duplicati_dlist_crosscheck.py`` decides whether a destination
fileset is a restore point or a synthetic/incomplete manifest. A false COMPLETE
is a restore of a fileset nobody certified. ``duplicati_decrypt_validate_all.bash``
is the ciphertext-authorship residual: whole-file hashes cannot catch a stream
garbled before hashing; MDC decrypt-to-/dev/null can.

Neither script had tests. These pins are behavioral, stdlib-only, and never
touch a live archive, Duplicati, or credential file. ``util/`` is not
pre-commit-lint-gated, so this unittest is the gate.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import textwrap
import unittest
import unittest.mock as mock
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
CROSSCHECK = REPO_ROOT / "util" / "ad-hoc" / "duplicati_dlist_crosscheck.py"
DECRYPT_ALL = REPO_ROOT / "util" / "ad-hoc" / "duplicati_decrypt_validate_all.bash"
SCRIPT_TIMEOUT_SECONDS = 10
# The mount both harnesses used to assert unconditionally. It is now only ever used as a
# NEGATIVE fixture: the gate must follow --dest / $1, so declaring *this* path mounted while
# the destination is elsewhere has to REFUSE. Before 2026-08-30 it made both tools pass
# regardless of the destination, and -- since sdc4 is not in fstab -- would have made them
# refuse every destination after a reboot (note 8.20.3).
LEGACY_SCRATCH_MOUNT = "/media/pcalnon/temp_backups"
FIXTURE_VALUE = "restore-integrity-fixture-VALUE"
OLD_FIXTURE_VALUE = "old-archive-fixture-VALUE"
BLOCKSIZE = 1024 * 1024

_spec = importlib.util.spec_from_file_location("duplicati_dlist_crosscheck", CROSSCHECK)
crosscheck = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(crosscheck)


def _sys_exit_code(exc: BaseException) -> int:
    code = getattr(exc, "code", 1)
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    return 1


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _hash32(tag: str) -> bytes:
    return hashlib.sha256(tag.encode()).digest()


def _write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


def _zip_bytes(entries: dict[str, bytes | str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, payload in entries.items():
            data = payload if isinstance(payload, bytes) else payload.encode()
            zf.writestr(name, data)
    return buf.getvalue()


def _dindex_zip(*, vol_name: str, hashes: list[str], list_entries: dict[str, bytes] | None = None) -> bytes:
    entries: dict[str, bytes | str] = {f"vol/{vol_name}": json.dumps({"blocks": [{"hash": h} for h in hashes]})}
    for name, raw in (list_entries or {}).items():
        entries[f"list/{name}"] = raw
    return _zip_bytes(entries)


def _dlist_zip(*, files: list[dict], blockhash: str = "SHA256", filehash: str = "SHA256", blocksize: int = BLOCKSIZE) -> bytes:
    return _zip_bytes(
        {
            "filelist.json": json.dumps(files),
            "manifest": json.dumps({"BlockHash": blockhash, "FileHash": filehash, "Blocksize": blocksize}),
            "fileset": json.dumps({"IsFullBackup": True}),
        }
    )


def _dest_fingerprint(dest: Path) -> dict[str, tuple[int, int, bytes]]:
    return {p.name: (p.stat().st_mtime_ns, p.stat().st_size, p.read_bytes()) for p in dest.iterdir() if p.is_file()}


class CrosscheckHarness:
    """Temp dest/workdir + monkeypatched gpg/ismount for the coverage tool."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        # The temp root stands in for the destination's real mountpoint, so the derived
        # walk-up guard has something to find. Nothing here names a real filesystem.
        self.mount_root = os.path.realpath(str(tmp))
        self.dest = tmp / "dest"
        self.work = tmp / "work"
        self.dest.mkdir()
        self.work.mkdir()
        self.cred = tmp / "cred.env"
        self.cred.write_text(f'export PASSPHRASE_OLD="{OLD_FIXTURE_VALUE}"\nPASSPHRASE="{FIXTURE_VALUE}"\n', encoding="utf-8")
        self.dblock = "fresh.dblock.vol.gpg"
        self.dindex = "fresh.dindex.vol.gpg"
        self.dlist = "fresh.dlist.vol.gpg"
        (self.dest / self.dblock).write_bytes(b"ciphertext-dblock")
        (self.dest / self.dindex).write_bytes(b"ciphertext-dindex")
        (self.dest / self.dlist).write_bytes(b"ciphertext-dlist")
        self.payloads: dict[str, bytes] = {}

    def fingerprint(self) -> dict[str, tuple[int, int, bytes]]:
        return _dest_fingerprint(self.dest)

    def run(
        self,
        *,
        mounted: bool = True,
        extra_argv: list[str] | None = None,
        workdir: Path | None = None,
        mount_root: str | None = None,
        omit_workdir: bool = False,
        omit_dest: bool = False,
    ) -> tuple[int, str, str]:
        work = workdir if workdir is not None else self.work
        fake_mount = self.mount_root if mount_root is None else mount_root

        def ismount(path: str) -> bool:
            return mounted and os.path.realpath(path) == fake_mount

        def gpg_decrypt(src: str, dst: str, passphrase: str) -> None:
            name = os.path.basename(src)
            if name not in self.payloads:
                raise AssertionError(f"unexpected decrypt of {name}")
            Path(dst).write_bytes(self.payloads[name])

        argv = ["duplicati_dlist_crosscheck.py"]
        if not omit_dest:
            argv.extend(["--dest", str(self.dest)])
        if not omit_workdir:
            argv.extend(["--workdir", str(work)])
        argv.extend(["--cred-file", str(self.cred)])
        if extra_argv:
            argv.extend(extra_argv)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(crosscheck.os.path, "ismount", ismount),
            mock.patch.object(crosscheck, "gpg_decrypt", gpg_decrypt),
            mock.patch.object(crosscheck.sys, "argv", argv),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            try:
                crosscheck.main()
                code = 0
            except SystemExit as exc:
                code = _sys_exit_code(exc)
        return code, stdout.getvalue(), stderr.getvalue()


class DecryptAllHarness:
    """PATH-stubbed mountpoint + gpg for the MDC decrypt-all script."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.bin = tmp / "bin"
        self.bin.mkdir()
        self.dest = tmp / "dest"
        self.dest.mkdir()
        self.cred = tmp / "cred.env"
        self.cred.write_text(f'export PASSPHRASE="{FIXTURE_VALUE}"\nPASSPHRASE_OLD="{OLD_FIXTURE_VALUE}"\n', encoding="utf-8")
        self.argv_log = tmp / "gpg-argv.log"
        self.stdin_log = tmp / "gpg-stdin.log"
        self.mount_ok = tmp / "mount_ok"
        self.mount_ok.write_text("1", encoding="utf-8")
        # The ONE path the stub reports as a mountpoint. The script derives its guard by
        # walking up from DEST, so this is what makes "the gate follows the destination"
        # testable: point it at LEGACY_SCRATCH_MOUNT with a dest elsewhere and the run must
        # be refused -- which is exactly the case the old hardcoded gate let through.
        self.fake_mount = tmp / "fake_mount"
        self.fake_mount.write_text(os.path.realpath(str(tmp)), encoding="utf-8")
        _write_executable(
            self.bin / "mountpoint",
            f"""\
            #!/usr/bin/env bash
            # stub: `mountpoint -q PATH` succeeds only for the one designated path
            [[ -f "{self.mount_ok}" ]] || exit 1
            [[ "$2" == "$(cat "{self.fake_mount}")" ]] && exit 0
            exit 1
            """,
        )
        _write_executable(
            self.bin / "gpg",
            f"""\
            #!/usr/bin/env bash
            printf '%s\\n' "$*" >> "{self.argv_log}"
            cat >> "{self.stdin_log}"
            case "$*" in
              *fail.gpg*) echo "decrypt failed" >&2; exit 1 ;;
            esac
            exit 0
            """,
        )

    def env(self) -> RedactedEnv:
        return RedactedEnv(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}")

    def run(self, dest: Path | None = None, cred: Path | None = None, *, no_args: bool = False) -> subprocess.CompletedProcess[str]:
        argv = ["bash", str(DECRYPT_ALL)]
        if not no_args:
            argv.extend([str(dest if dest is not None else self.dest), str(cred if cred is not None else self.cred)])
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            env=self.env(),
            timeout=SCRIPT_TIMEOUT_SECONDS,
            check=False,
        )


class TestDecryptValidateAllSyntax(unittest.TestCase):
    def test_bash_syntax(self) -> None:
        result = subprocess.run(["bash", "-n", str(DECRYPT_ALL)], capture_output=True, text=True, timeout=SCRIPT_TIMEOUT_SECONDS)
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestDecryptValidateAllPreflight(unittest.TestCase):
    def test_unmounted_destination_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            h.mount_ok.unlink()
            before = _dest_fingerprint(h.dest)
            result = h.run()
            self.assertEqual(result.returncode, 2, msg=result.stderr + result.stdout)
            self.assertIn("not on a mounted filesystem", result.stderr)
            self.assertEqual(_dest_fingerprint(h.dest), before)

    def test_mount_gate_follows_the_destination_not_the_legacy_scratch_path(self) -> None:
        """The gate must derive from $1, not assert a filesystem $1 cannot influence.

        Regression pin for note 8.20.3. The stub reports ONLY the old hardcoded
        ``/media/pcalnon/temp_backups`` as a mountpoint while the destination lives
        elsewhere -- the exact shape of a post-reboot run against the live sda1 set.
        The pre-2026-08-30 script passed this preflight (it never looked at $1) and
        went on to validate whatever it was pointed at; it must now refuse.
        """
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            h.fake_mount.write_text(LEGACY_SCRATCH_MOUNT, encoding="utf-8")
            (h.dest / "ok.gpg").write_bytes(b"cipher-ok")
            result = h.run()
            self.assertEqual(result.returncode, 2, msg=result.stderr + result.stdout)
            self.assertIn("not on a mounted filesystem", result.stderr)
            self.assertNotIn("DECRYPT-VALID", result.stdout)
            self.assertFalse(h.argv_log.exists(), "refused preflight must not decrypt anything")

    def test_missing_dest_argument_refuses_with_usage(self) -> None:
        """No default destination: a bare run must not silently pick a stale path."""
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            result = h.run(no_args=True)
            self.assertEqual(result.returncode, 2, msg=result.stderr + result.stdout)
            self.assertIn("usage:", result.stderr)
            self.assertIn("REQUIRED", result.stderr)

    def test_zero_volumes_is_operational_failure_not_a_clean_pass(self) -> None:
        """An empty destination must not read as ALL VOLUMES DECRYPT-VALID.

        Found while de-drifting the mount gate: the loop simply never ran, so
        ``total=0, bad=0`` fell through to the success branch and exit 0. That is a
        vacuous pass, and it is what an unmounted, mistyped, or wrong-``ENCRYPTION``
        destination looks like -- the very condition the hardcoded mount gate had been
        the accidental proxy for.
        """
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            result = h.run()
            self.assertEqual(result.returncode, 2, msg=result.stderr + result.stdout)
            self.assertIn("NO VOLUMES FOUND", result.stdout)
            self.assertNotIn("ALL VOLUMES DECRYPT-VALID", result.stdout)

    def test_missing_destination_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            missing = Path(tmp) / "no-such-dest"
            result = h.run(dest=missing)
            self.assertEqual(result.returncode, 2, msg=result.stderr + result.stdout)
            self.assertIn("no such destination", result.stderr)

    def test_missing_passphrase_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            h.cred.write_text(f'PASSPHRASE_OLD="{OLD_FIXTURE_VALUE}"\n', encoding="utf-8")
            result = h.run()
            self.assertEqual(result.returncode, 2, msg=result.stderr + result.stdout)
            self.assertIn("PASSPHRASE", result.stderr)
            self.assertNotIn(OLD_FIXTURE_VALUE, result.stdout)
            self.assertNotIn(OLD_FIXTURE_VALUE, result.stderr)


class TestDecryptValidateAllDecrypt(unittest.TestCase):
    def test_all_volumes_ok_uses_fresh_passphrase_on_fd_not_argv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            (h.dest / "ok-a.gpg").write_bytes(b"cipher-a")
            (h.dest / "ok-b.gpg").write_bytes(b"cipher-b")
            before = _dest_fingerprint(h.dest)
            result = h.run()
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("ALL VOLUMES DECRYPT-VALID", result.stdout)
            self.assertEqual(_dest_fingerprint(h.dest), before)
            argv = h.argv_log.read_text(encoding="utf-8")
            stdin = h.stdin_log.read_text(encoding="utf-8")
            self.assertIn("--passphrase-fd", argv)
            self.assertIn("--decrypt", argv)
            self.assertNotIn(FIXTURE_VALUE, argv)
            self.assertNotIn(OLD_FIXTURE_VALUE, argv)
            self.assertIn(FIXTURE_VALUE, stdin)
            self.assertNotIn(OLD_FIXTURE_VALUE, stdin)
            self.assertIn("ok-a.gpg", argv)
            self.assertIn("ok-b.gpg", argv)
            self.assertNotIn(FIXTURE_VALUE, result.stdout)
            self.assertNotIn(FIXTURE_VALUE, result.stderr)

    def test_one_failure_still_walks_every_volume_and_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            h = DecryptAllHarness(Path(tmp))
            (h.dest / "ok.gpg").write_bytes(b"cipher-ok")
            (h.dest / "fail.gpg").write_bytes(b"cipher-bad")
            before = _dest_fingerprint(h.dest)
            result = h.run()
            self.assertEqual(result.returncode, 1, msg=result.stderr + result.stdout)
            self.assertIn("INVALID VOLUME", result.stdout)
            self.assertIn("DECRYPT FAIL: fail.gpg", result.stdout)
            self.assertEqual(_dest_fingerprint(h.dest), before)
            argv = h.argv_log.read_text(encoding="utf-8")
            self.assertIn("ok.gpg", argv)
            self.assertIn("fail.gpg", argv)


class TestDlistCrosscheckPassphrase(unittest.TestCase):
    def test_load_passphrase_reads_quoted_export_form(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cred = Path(tmp) / "cred.env"
            cred.write_text(f'export PASSPHRASE="{FIXTURE_VALUE}"\n', encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                got = crosscheck.load_passphrase(str(cred), "PASSPHRASE")
            self.assertEqual(got, FIXTURE_VALUE)
            rendered = stdout.getvalue()
            self.assertNotIn(FIXTURE_VALUE, rendered)
            self.assertIn(hashlib.sha256(FIXTURE_VALUE.encode()).hexdigest()[:16], rendered)

    def test_load_passphrase_missing_key_is_operational_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cred = Path(tmp) / "cred.env"
            cred.write_text(f'PASSPHRASE_OLD="{OLD_FIXTURE_VALUE}"\n', encoding="utf-8")
            with self.assertRaises(SystemExit) as ctx, redirect_stderr(io.StringIO()):
                crosscheck.load_passphrase(str(cred), "PASSPHRASE")
            self.assertEqual(_sys_exit_code(ctx.exception), 2)

    def test_default_cred_key_is_passphrase_not_old(self) -> None:
        src = CROSSCHECK.read_text(encoding="utf-8")
        self.assertIn('default="PASSPHRASE"', src)
        self.assertIn("never PASSPHRASE_OLD", src)


class TestDlistCrosscheckPreflight(unittest.TestCase):
    def test_unmounted_destination_refuses_before_listing_dest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            before = h.fingerprint()
            code, _out, err = h.run(mounted=False)
            self.assertEqual(code, 2)
            self.assertIn("not on a mounted filesystem", err)
            self.assertEqual(h.fingerprint(), before)

    def test_mount_gate_follows_the_destination_not_the_legacy_scratch_path(self) -> None:
        """The gate must derive from --dest, not assert a filesystem --dest cannot influence.

        Regression pin for note 8.20.3, mirroring the bash harness test of the same
        name. Only the old hardcoded ``/media/pcalnon/temp_backups`` is reported
        mounted, while the destination is elsewhere -- the shape of every run once
        sdc4 (not in fstab) is gone. The pre-2026-08-30 script passed this preflight
        without ever consulting --dest.
        """
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            before = h.fingerprint()
            code, out, err = h.run(mount_root=LEGACY_SCRATCH_MOUNT)
            self.assertEqual(code, 2, msg=out + err)
            self.assertIn("not on a mounted filesystem", err)
            self.assertNotIn("COMPLETE COVERAGE", out)
            self.assertEqual(h.fingerprint(), before)

    def test_dest_is_required(self) -> None:
        """No default destination: a bare run must not cross-check a stale fileset."""
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            code, _out, err = h.run(omit_dest=True)
            self.assertEqual(code, 2)
            self.assertIn("--dest", err)

    def test_default_workdir_is_a_private_tempdir_outside_dest(self) -> None:
        """Omitting --workdir must not fall back to a hardcoded scratch path.

        The old default (``/media/pcalnon/temp_backups/_fresh_dlist_check``) dies with
        sdc4. The replacement is a generated temp dir registered for removal, so there
        is no path left that can rot.
        """
        content = _b64(_hash32("content"))
        meta = _b64(_hash32("meta"))
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[content, meta])
            h.payloads[h.dlist] = _dlist_zip(files=[{"type": "File", "path": "/tmp/a.txt", "size": 100, "hash": content, "metahash": meta, "metasize": 64}])
            registered: list[tuple] = []
            with mock.patch.object(crosscheck.atexit, "register", lambda *a: registered.append(a)):
                code, out, err = h.run(omit_workdir=True)
            self.assertEqual(code, 0, msg=out + err)
            self.assertIn("COMPLETE COVERAGE", out)
            workdir = next(line.split(":", 1)[1].split("(mount")[0].strip() for line in out.splitlines() if line.startswith("workdir"))
            self.assertTrue(os.path.basename(workdir).startswith("dlist-crosscheck-"), workdir)
            self.assertFalse(workdir.startswith(str(h.dest)), "temp workdir must not be inside the destination")
            self.assertNotIn(LEGACY_SCRATCH_MOUNT, workdir)
            self.assertEqual(registered, [(crosscheck.shutil.rmtree, workdir, True)])
            crosscheck.shutil.rmtree(workdir, True)

    def test_workdir_inside_dest_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            nested = h.dest / "scratch"
            nested.mkdir()
            before = h.fingerprint()
            code, _out, err = h.run(workdir=nested)
            self.assertEqual(code, 2)
            self.assertIn("must not be inside the destination", err)
            self.assertEqual(h.fingerprint(), before)

    def test_zero_dlists_refuses(self) -> None:
        """No dlist at all is still fatal -- there is nothing to cross-check against."""
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            (h.dest / h.dlist).unlink()
            code, _out, err = h.run()
            self.assertEqual(code, 2)
            self.assertIn("no dlist in destination", err)

    def test_multiple_dlists_are_allowed_and_the_newest_is_checked(self) -> None:
        """Several dlists must NOT refuse -- the newest is selected and checked.

        A live destination accumulates one dlist per backup run, and the
        2026-08-28 archive purge deliberately retained ten of them, so a
        refusal on more than one would make this tool useless against the real
        destination. Selection is lexical-last because the names embed the UTC
        start stamp; taking dlists[0] would pin the ORIGINAL full backup
        forever, which is the regression this test exists to catch.
        """
        content = _b64(_hash32("content"))
        meta = _b64(_hash32("meta"))
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            # Sorts BEFORE "fresh.", so "fresh" is the newest of the two. It is
            # deliberately given no payload: the stub decrypt raises on any
            # unexpected file, so this also proves the older dlist is never read.
            (h.dest / "aged.dlist.vol.gpg").write_bytes(b"older-ciphertext")
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[content, meta])
            h.payloads[h.dlist] = _dlist_zip(files=[{"type": "File", "path": "/tmp/a.txt", "size": 100, "hash": content, "metahash": meta, "metasize": 64}])
            before = h.fingerprint()
            code, out, _err = h.run()
            self.assertEqual(code, 0)
            self.assertIn("2 dlist", out)
            self.assertIn(f"{h.dlist} (newest of 2)", out)
            self.assertEqual(h.fingerprint(), before)


class TestDlistCrosscheckCoverage(unittest.TestCase):
    def test_complete_coverage_exits_0_and_does_not_write_dest(self) -> None:
        content = _b64(_hash32("content"))
        meta = _b64(_hash32("meta"))
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[content, meta])
            h.payloads[h.dlist] = _dlist_zip(files=[{"type": "File", "path": "/tmp/a.txt", "size": 100, "hash": content, "metahash": meta, "metasize": 64}])
            before = h.fingerprint()
            code, out, err = h.run()
            self.assertEqual(code, 0, msg=out + err)
            self.assertIn("COMPLETE COVERAGE", out)
            self.assertEqual(h.fingerprint(), before)
            self.assertNotIn(FIXTURE_VALUE, out)
            self.assertNotIn(FIXTURE_VALUE, err)
            self.assertNotIn(OLD_FIXTURE_VALUE, out)

    def test_missing_hash_exits_1(self) -> None:
        needed = _b64(_hash32("needed"))
        other = _b64(_hash32("other"))
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[other])
            h.payloads[h.dlist] = _dlist_zip(files=[{"type": "File", "path": "/tmp/a.txt", "size": 100, "hash": needed, "metasize": 0}])
            before = h.fingerprint()
            code, out, err = h.run()
            self.assertEqual(code, 1, msg=out + err)
            self.assertIn("MISSING hash", out)
            self.assertIn(needed, out)
            self.assertEqual(h.fingerprint(), before)

    def test_unexpandable_blocklist_exits_1(self) -> None:
        blh = _b64(_hash32("blocklist-missing-list-entry"))
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[blh])
            h.payloads[h.dlist] = _dlist_zip(files=[{"type": "File", "path": "/tmp/big.bin", "size": 2 * BLOCKSIZE, "blocklists": [blh], "metasize": 0}])
            code, out, err = h.run()
            self.assertEqual(code, 1, msg=out + err)
            self.assertIn("UNEXPANDABLE blocklist", out)
            self.assertIn(blh, out)

    def test_poisoned_list_entry_is_operational_failure(self) -> None:
        raw = _hash32("block-a") + _hash32("block-b")
        poisoned_name = _b64(_hash32("not-the-content")).replace("+", "-").replace("/", "_")
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[], list_entries={poisoned_name: raw})
            h.payloads[h.dlist] = _dlist_zip(files=[{"type": "File", "path": "/tmp/a.txt", "size": 1, "hash": _b64(_hash32("x")), "metasize": 0}])
            code, out, err = h.run()
            self.assertEqual(code, 2, msg=out + err)
            self.assertIn("poisoned list/", err)
            self.assertIn("untrustworthy", err)

    def test_list_entry_length_not_divisible_by_hash_bytes_refuses(self) -> None:
        raw = b"\x00" * 31
        name = _b64(hashlib.sha256(raw).digest()).replace("+", "-").replace("/", "_")
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[], list_entries={name: raw})
            h.payloads[h.dlist] = _dlist_zip(files=[])
            code, _out, err = h.run()
            self.assertEqual(code, 2)
            self.assertIn("not divisible by", err)
            self.assertIn("refusing to under-build NEEDED", err)

    def test_non_sha256_manifest_aborts(self) -> None:
        content = _b64(_hash32("content"))
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(vol_name=h.dblock, hashes=[content])
            h.payloads[h.dlist] = _dlist_zip(
                files=[{"type": "File", "path": "/tmp/a.txt", "size": 100, "hash": content, "metasize": 0}],
                blockhash="MD5",
            )
            code, _out, err = h.run()
            self.assertEqual(code, 2)
            self.assertIn("not SHA256", err)

    def test_expanded_blocklist_complete_coverage(self) -> None:
        h1 = _hash32("data-1")
        h2 = _hash32("data-2")
        raw = h1 + h2
        bl_plain = _b64(hashlib.sha256(raw).digest())
        bl_url = bl_plain.replace("+", "-").replace("/", "_")
        h1_b64 = _b64(h1)
        h2_b64 = _b64(h2)
        with tempfile.TemporaryDirectory() as tmp:
            h = CrosscheckHarness(Path(tmp))
            h.payloads[h.dindex] = _dindex_zip(
                vol_name=h.dblock,
                hashes=[bl_plain, h1_b64, h2_b64],
                list_entries={bl_url: raw},
            )
            h.payloads[h.dlist] = _dlist_zip(files=[{"type": "File", "path": "/tmp/big.bin", "size": 2 * BLOCKSIZE, "blocklists": [bl_plain], "metasize": 0}])
            code, out, err = h.run()
            self.assertEqual(code, 0, msg=out + err)
            self.assertIn("COMPLETE COVERAGE", out)


class TestDlistCrosscheckHashWidth(unittest.TestCase):
    def test_hash_bytes_is_sha256(self) -> None:
        self.assertEqual(crosscheck.HASH_BYTES, 32)


if __name__ == "__main__":
    unittest.main()
