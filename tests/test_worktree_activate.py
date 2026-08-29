"""
Tests for util/worktree_activate.bash.

Pins the activate_new_worktree gate arms (missing arg / missing dir / success cd)
via a hermetic bash driver that sources the helper (the intended .bashrc path).
The script defines functions only — it is never meant to be executed as a main.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "worktree_activate.bash"
SCRIPT_TIMEOUT_SECONDS: int = 15


def _run_activate_driver(*activate_args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Source worktree_activate.bash and invoke activate_new_worktree with *activate_args."""
    # No `set -u`: the helper is sourced into .bashrc (typically without nounset).
    # Under nounset, bare `${1}` in activate_new_worktree aborts before the
    # "Directory Not Specified" arm can run — that is not the intended contract.
    driver = r"""
set -eo pipefail
SCRIPT_PATH="$1"
shift
# shellcheck disable=SC1090
source "${SCRIPT_PATH}"
activate_new_worktree "$@"
pwd
"""
    env = RedactedEnv(os.environ)
    return subprocess.run(
        ["bash", "-c", driver, "activate-driver", str(SCRIPT_PATH), *activate_args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestActivateNewWorktree(unittest.TestCase):
    """Gate arms for activate_new_worktree (sourced helper path)."""

    def test_missing_arg_reports_directory_not_specified(self):
        result = _run_activate_driver()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Error, Worktree Directory Not Specified!", result.stdout)

    def test_nonexistent_directory_reports_does_not_exist(self):
        missing = "/tmp/juniper-worktree-activate-missing-dir-does-not-exist"
        result = _run_activate_driver(missing)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Error, Worktree Directory Does not Exist!", result.stdout)
        self.assertNotIn("Error, Worktree Directory Not Specified!", result.stdout)

    def test_existing_directory_changes_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir).resolve()
            result = _run_activate_driver(str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn("Error,", result.stdout)
            # Last non-empty line is pwd after a successful cd.
            lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
            self.assertTrue(lines, msg=result.stdout)
            self.assertEqual(Path(lines[-1]).resolve(), target)


class TestIsSourcedReturnCode(unittest.TestCase):
    """is_sourced exit-code contract (stdout is empty; callers use return status)."""

    def test_is_sourced_returns_true_under_bash_invocation_name(self):
        # Under bash, ${0##*/} matches the bash branch → return TRUE (0).
        # activate_new_worktree compares "$(is_sourced)" (stdout) to FALSE, so
        # this exit-code path is the real contract for .bashrc sourcing.
        # Export an empty ZSH_VERSION so the bash branch of is_sourced is taken
        # even if a parent shell enables nounset (the `[ -n "$ZSH_VERSION" ]` check).
        driver = r"""
set -eo pipefail
ZSH_VERSION="${ZSH_VERSION-}"
source "$1"
if is_sourced; then
  echo SOURCED_TRUE
else
  echo SOURCED_FALSE
fi
"""
        env = RedactedEnv(os.environ)
        env["ZSH_VERSION"] = ""
        result = subprocess.run(
            ["bash", "-c", driver, "bash", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("SOURCED_TRUE", result.stdout)


if __name__ == "__main__":
    unittest.main()
