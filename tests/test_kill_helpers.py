"""
Hermetic behavioral coverage for emergency kill helpers:

- util/kill_all_pythons.bash
- util/juniper_worker_kill.bash

These scripts are safety-critical: a filter regression can SIGKILL the agent,
CI Python, or unrelated user processes. Tests PATH-stub `ps` / `sudo` / `kill`
so decisions are deterministic and never touch live PIDs.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
KILL_ALL_PYTHONS = REPO_ROOT / "util" / "kill_all_pythons.bash"
JUNIPER_WORKER_KILL = REPO_ROOT / "util" / "juniper_worker_kill.bash"
SCRIPT_TIMEOUT_SECONDS = 10


def write_executable(path: Path, body: str) -> None:
    # Shebang must be at byte 0 — strip the leading newline left by dedent("""...).
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


class KillHelperFixture:
    """Deterministic process table + kill logging for the emergency helpers."""

    def __init__(self, tmpdir: str, ps_rows: list[str]):
        self.root = Path(tmpdir)
        self.bin_dir = self.root / "bin"
        self.kill_log = self.root / "kill.log"
        self.bin_dir.mkdir()
        self._write_fake_ps(ps_rows)
        self._write_fake_sudo()
        self._write_fake_kill()

    def _write_fake_ps(self, rows: list[str]) -> None:
        # Trailing newline so the pipeline mirrors real `ps aux` output.
        # Keep the heredoc body unindented so stub lines are not space-prefixed.
        output = "\n".join(rows) + ("\n" if rows else "")
        write_executable(
            self.bin_dir / "ps",
            f"""\
#!/usr/bin/env bash
cat <<'EOF'
{output}EOF
""",
        )

    def _write_fake_sudo(self) -> None:
        # Log the delegated command; never execute a real kill.
        write_executable(
            self.bin_dir / "sudo",
            """\
#!/usr/bin/env bash
printf 'sudo %s\\n' "$*" >> "${KILL_LOG}"
exit 0
""",
        )

    def _write_fake_kill(self) -> None:
        write_executable(
            self.bin_dir / "kill",
            """\
#!/usr/bin/env bash
printf 'kill %s\\n' "$*" >> "${KILL_LOG}"
exit 0
""",
        )

    def env(self) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        env["PATH"] = f"{self.bin_dir}{os.pathsep}{env['PATH']}"
        env["KILL_LOG"] = str(self.kill_log)
        return env

    def kill_lines(self) -> list[str]:
        if not self.kill_log.exists():
            return []
        return [line for line in self.kill_log.read_text(encoding="utf-8").splitlines() if line]


def run_script(script: Path, fixture: KillHelperFixture) -> subprocess.CompletedProcess[str]:
    # Disable bash's kill builtin in the same shell so PATH stubs win.
    # A nested `bash script` would re-enable the builtin and touch live PIDs.
    return subprocess.run(
        ["bash", "-c", 'enable -n kill; source "$1"', "_", str(script)],
        capture_output=True,
        text=True,
        env=fixture.env(),
        timeout=SCRIPT_TIMEOUT_SECONDS,
        cwd=str(REPO_ROOT),
    )


class TestSyntax(unittest.TestCase):
    def test_kill_all_pythons_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(KILL_ALL_PYTHONS)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_juniper_worker_kill_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(JUNIPER_WORKER_KILL)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestKillAllPythons(unittest.TestCase):
    def test_kills_only_python_matching_pids_via_sudo_kill_9(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = KillHelperFixture(
                tmpdir,
                [
                    "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND",
                    "pcalnon  11111  0.0  0.1  10000  2000 pts/0    S+   12:00   0:00 python -m pytest",
                    "pcalnon  22222  0.0  0.1  10000  2000 pts/1    S+   12:00   0:00 /opt/conda/bin/python3 worker.py",
                    "pcalnon  33333  0.0  0.1  10000  2000 pts/2    S+   12:00   0:00 bash util/isolated_stack.bash",
                    "root     44444  0.0  0.0   1000   100 ?        Ss   12:00   0:00 /usr/sbin/sshd",
                ],
            )

            result = run_script(KILL_ALL_PYTHONS, fixture)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(
                fixture.kill_lines(),
                ["sudo kill -9 11111", "sudo kill -9 22222"],
            )
            self.assertIn("11111", result.stdout)
            self.assertIn("22222", result.stdout)
            self.assertNotIn("33333", result.stdout)

    def test_empty_process_table_is_a_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = KillHelperFixture(tmpdir, [])

            result = run_script(KILL_ALL_PYTHONS, fixture)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.kill_lines(), [])

    def test_grep_self_match_line_is_selected_without_grep_v_guard(self) -> None:
        """Document the missing `grep -v grep` class (worker_kill has the guard)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = KillHelperFixture(
                tmpdir,
                [
                    "pcalnon  55555  0.0  0.0   1000   100 pts/0    S+   12:00   0:00 grep python",
                ],
            )

            result = run_script(KILL_ALL_PYTHONS, fixture)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.kill_lines(), ["sudo kill -9 55555"])


class TestJuniperWorkerKill(unittest.TestCase):
    def test_kills_only_juniper_and_pcalnon_pids_via_kill_KILL(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = KillHelperFixture(
                tmpdir,
                [
                    "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND",
                    "pcalnon  10001  0.0  0.1  10000  2000 pts/0    S+   12:00   0:00 python -m juniper_cascor_worker",
                    "alice    10002  0.0  0.1  10000  2000 pts/1    S+   12:00   0:00 python -m juniper_cascor_worker",
                    "pcalnon  10003  0.0  0.1  10000  2000 pts/2    S+   12:00   0:00 python -m pytest tests/",
                    "pcalnon  10004  0.0  0.0   1000   100 pts/3    S+   12:00   0:00 grep juniper",
                ],
            )

            result = run_script(JUNIPER_WORKER_KILL, fixture)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.kill_lines(), ["kill -KILL 10001"])
            self.assertIn("1. 10001", result.stdout)
            self.assertNotIn("10002", result.stdout)
            self.assertNotIn("10003", result.stdout)
            self.assertNotIn("10004", result.stdout)

    def test_empty_match_set_is_a_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = KillHelperFixture(
                tmpdir,
                [
                    "pcalnon  20001  0.0  0.1  10000  2000 pts/0    S+   12:00   0:00 python -m pytest",
                    "alice    20002  0.0  0.1  10000  2000 pts/1    S+   12:00   0:00 python -m juniper_data",
                ],
            )

            result = run_script(JUNIPER_WORKER_KILL, fixture)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(fixture.kill_lines(), [])

    def test_does_not_invoke_sudo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = KillHelperFixture(
                tmpdir,
                [
                    "pcalnon  30001  0.0  0.1  10000  2000 pts/0    S+   12:00   0:00 /home/pcalnon/juniper-cascor-worker/.venv/bin/python",
                ],
            )

            result = run_script(JUNIPER_WORKER_KILL, fixture)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            lines = fixture.kill_lines()
            self.assertEqual(lines, ["kill -KILL 30001"])
            self.assertFalse(any(line.startswith("sudo ") for line in lines))


if __name__ == "__main__":
    unittest.main()
