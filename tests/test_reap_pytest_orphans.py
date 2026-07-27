"""
Tests for util/reap_pytest_orphans.bash.

The orphan reaper is safety-critical because a false positive can kill an active
test run. These tests use a fake process table, fake proc tree, and fake kill
command so the reaping decisions are deterministic and never touch real PIDs.
"""

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "reap_pytest_orphans.bash"
SCRIPT_TIMEOUT_SECONDS: int = 30


def write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    path.chmod(0o755)


class FakeProcessFixture:
    """Build a deterministic process environment for reap_pytest_orphans.bash."""

    def __init__(self, tmpdir: str, ps_rows: list[str]):
        self.root = Path(tmpdir)
        self.bin_dir = self.root / "bin"
        self.proc_root = self.root / "proc"
        self.kill_log = self.root / "kill.log"
        self.bin_dir.mkdir()
        self.proc_root.mkdir()

        self._write_fake_id()
        self._write_fake_ps(ps_rows)
        self._write_fake_kill()

    def _write_fake_id(self) -> None:
        write_executable(
            self.bin_dir / "id",
            """
            #!/usr/bin/env bash
            if [[ "$1" == "-un" ]]; then
                echo testuser
                exit 0
            fi
            exit 1
            """,
        )

    def _write_fake_ps(self, rows: list[str]) -> None:
        output = "\n".join(rows)
        write_executable(
            self.bin_dir / "ps",
            f"""
            #!/usr/bin/env bash
            cat <<'EOF'
            {output}
            EOF
            """,
        )

    def _write_fake_kill(self) -> None:
        write_executable(
            self.bin_dir / "fake-kill",
            """
            #!/usr/bin/env bash
            printf '%s\\n' "$*" >> "${KILL_LOG}"
            """,
        )

    def add_process(self, pid: int, ppid: int, cmdline: list[str]) -> None:
        process_dir = self.proc_root / str(pid)
        process_dir.mkdir()
        (process_dir / "status").write_text(f"Name:\tpython\nPPid:\t{ppid}\n", encoding="utf-8")
        (process_dir / "cmdline").write_bytes(b"\0".join(part.encode("utf-8") for part in cmdline) + b"\0")

    def add_parent(self, pid: int) -> None:
        (self.proc_root / str(pid)).mkdir()

    def env(self) -> dict[str, str]:
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{self.bin_dir}{os.pathsep}{env['PATH']}"
        env["KILL_LOG"] = str(self.kill_log)
        env["JUNIPER_REAP_KILL_CMD"] = str(self.bin_dir / "fake-kill")
        env["JUNIPER_REAP_PROC_ROOT"] = str(self.proc_root)
        return env


def run_script(fixture: FakeProcessFixture, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=fixture.env(),
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestReapPytestOrphans(unittest.TestCase):
    def test_dry_run_reaps_init_systemd_and_missing_parent_orphans_without_killing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "101 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                    "102 testuser /home/pcalnon/Development/python/Juniper/worktrees/repo/.venv/bin/python -c worker",
                    "103 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(101, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_process(102, 50, ["/home/pcalnon/Development/python/Juniper/worktrees/repo/.venv/bin/python", "-c", "worker"])
            fixture.add_process(103, 999, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])

            result = run_script(fixture, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WOULD REAP pid=101 ppid=1", result.stdout)
            self.assertIn("WOULD REAP pid=102 ppid=50", result.stdout)
            self.assertIn("WOULD REAP pid=103 ppid=999", result.stdout)
            self.assertIn("Dry-run summary: 3 would be reaped, 0 kept (live parent), 0 skipped.", result.stdout)
            self.assertFalse(fixture.kill_log.exists())

    def test_verbose_dry_run_keeps_juniper_python_process_with_live_parent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "201 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(201, 200, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_parent(200)

            result = run_script(fixture, "--dry-run", "--verbose")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("KEEP       pid=201 ppid=200 (live parent)", result.stdout)
            self.assertIn("Dry-run summary: 0 would be reaped, 1 kept (live parent), 0 skipped.", result.stdout)
            self.assertFalse(fixture.kill_log.exists())

    def test_real_mode_kills_only_orphaned_juniper_python_processes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "301 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                    "302 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(301, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_process(302, 300, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_parent(300)

            result = run_script(fixture)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("REAP       pid=301 ppid=1", result.stdout)
            self.assertIn("Summary: 1 reaped, 1 kept (live parent), 0 skipped.", result.stdout)
            self.assertEqual(fixture.kill_log.read_text(encoding="utf-8"), "-KILL 301\n")

    def test_kill_failure_does_not_abort_and_still_counts_reaped(self):
        """``kill ... || true`` must keep set -e from aborting mid-loop.

        A vanished PID between decision and kill is normal (race with the OS
        reaper). Without ``|| true``, ``set -euo pipefail`` would exit before
        later orphans are considered — leaving RSS held. Fake-kill exits 1.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = FakeProcessFixture(
                tmpdir,
                [
                    "50 testuser /usr/lib/systemd/systemd --user",
                    "401 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                    "402 testuser /opt/conda/envs/JuniperCaa/bin/python -m pytest",
                ],
            )
            fixture.add_process(401, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            fixture.add_process(402, 1, ["/opt/conda/envs/JuniperCaa/bin/python", "-m", "pytest"])
            write_executable(
                fixture.bin_dir / "fake-kill",
                """
                #!/usr/bin/env bash
                printf '%s\\n' "$*" >> "${KILL_LOG}"
                exit 1
                """,
            )

            result = run_script(fixture)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("REAP       pid=401 ppid=1", result.stdout)
            self.assertIn("REAP       pid=402 ppid=1", result.stdout)
            self.assertIn("Summary: 2 reaped, 0 kept (live parent), 0 skipped.", result.stdout)
            self.assertEqual(
                fixture.kill_log.read_text(encoding="utf-8"),
                "-KILL 401\n-KILL 402\n",
            )


if __name__ == "__main__":
    unittest.main()
