"""Regression tests for scripts/claude_interactive.bash (the `claudey` entry).

Pins the permission / remote-control / model-effort compose that
``default_interactive_session_claude_code.bash`` already covers for the older
launcher. ``claude_interactive.bash`` is the repo-root ``claudey`` symlink
target and ships with ``DEBUG=TRUE``, which *forces*
``--dangerously-skip-permissions`` even though the comment below that block
says the flag is opt-in only. That DEBUG→skip coupling is the blast-radius
regression this suite locks.

Convention note (script-local, inverted vs the default launcher):
  TRUE="0", FALSE="1"  — so ``CLAUDE_SKIP_PERMISSIONS=0`` means *enabled*.

Hermetic: copies the launcher into a temp ``scripts/`` dir beside a fake
``wake_the_claude.bash`` that only logs argv (same stack as
``DefaultInteractiveLauncherRuntimeTests`` in ``test_wake_the_claude.py``).
No network, no real Claude binary.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_SRC = REPO_ROOT / "scripts" / "claude_interactive.bash"
CLAUDEY_LINK = REPO_ROOT / "claudey"

# Script-local boolean literals (TRUE="0", FALSE="1").
SCRIPT_TRUE = "0"
SCRIPT_FALSE = "1"


class ClaudeInteractiveLauncherRuntimeTests(unittest.TestCase):
    """Runtime tests for claude_interactive.bash argument compose."""

    def _install_fake_launcher_stack(
        self,
        temp_dir: str,
        *,
        debug: bool = True,
    ) -> tuple[Path, Path]:
        scripts_dir = Path(temp_dir) / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        text = LAUNCHER_SRC.read_text(encoding="utf-8")
        if not debug:
            # Flip only the shipped DEBUG default; leave the rest of the
            # script (including the TRUE/FALSE literals) untouched.
            old = 'DEBUG="${TRUE}"'
            new = 'DEBUG="${FALSE}"'
            self.assertIn(old, text, "DEBUG default marker drifted")
            text = text.replace(old, new, 1)
        launcher_path = scripts_dir / "claude_interactive.bash"
        launcher_path.write_text(text, encoding="utf-8")
        launcher_path.chmod(0o755)

        args_log = Path(temp_dir) / "claude_interactive_args.log"
        fake_wake = scripts_dir / "wake_the_claude.bash"
        fake_wake.write_text(
            "#!/usr/bin/env bash\n"
            "{\n"
            '  echo "__CALL__"\n'
            '  for arg in "$@"; do\n'
            "    printf 'ARG=%s\\n' \"$arg\"\n"
            "  done\n"
            '} >> "$WTC_WRAPPER_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_wake.chmod(0o755)
        return launcher_path, args_log

    @staticmethod
    def _extract_logged_args(args_log: Path) -> list[str]:
        if not args_log.exists():
            return []
        args: list[str] = []
        for line in args_log.read_text(encoding="utf-8").splitlines():
            if line.startswith("ARG="):
                args.append(line.removeprefix("ARG="))
        return args

    def _base_env(self, args_log: Path) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        for var in (
            "CLAUDE_SKIP_PERMISSIONS",
            "CLAUDE_REMOTE_CONTROL",
            "CLAUDE_MODEL",
            "CLAUDE_EFFORT",
            "CLAUDE_ID",
            "CLAUDE_WORKTREE",
            "CLAUDE_PROMPT",
            "BASH_ENV",
            "ENV",
        ):
            env.pop(var, None)
        env["WTC_WRAPPER_ARGS_LOG"] = str(args_log)
        return env

    def _run_launcher(
        self,
        launcher_path: Path,
        temp_dir: str,
        env: RedactedEnv,
        extra_args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(launcher_path), *(extra_args or [])],
            cwd=temp_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_script_and_claudey_symlink_exist(self) -> None:
        self.assertTrue(LAUNCHER_SRC.is_file(), f"missing: {LAUNCHER_SRC}")
        self.assertTrue(CLAUDEY_LINK.is_symlink(), f"claudey is not a symlink: {CLAUDEY_LINK}")
        self.assertEqual(
            CLAUDEY_LINK.readlink().as_posix(),
            "scripts/claude_interactive.bash",
            "claudey symlink target drifted",
        )

    def test_shipped_debug_true_forces_skip_permissions(self) -> None:
        """DEBUG=TRUE (shipped) forces --dangerously-skip-permissions.

        The comment above the opt-in block claims the flag is only added
        when explicitly requested; the DEBUG block above it overrides that
        for every interactive launch. Pin the force so a silent DEBUG flip
        or a comment-only "fix" cannot regress unnoticed.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=True)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertTrue(args, "Expected wrapper to invoke wake_the_claude.bash")
            self.assertIn("--dangerously-skip-permissions", args)
            # Defaults that ride alongside the permission force.
            self.assertEqual(args[args.index("--model") + 1], "fable")
            self.assertEqual(args[args.index("--effort") + 1], "max")
            self.assertIn("--remote-control", args)
            self.assertEqual(args[args.index("--id") + 1], SCRIPT_TRUE)
            self.assertEqual(args[args.index("--worktree") + 1], SCRIPT_TRUE)
            self.assertIn("Hello World, Claude!", args)

    def test_debug_false_omits_skip_permissions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertTrue(args, "Expected wrapper to invoke wake_the_claude.bash")
            self.assertNotIn("--dangerously-skip-permissions", args)
            self.assertIn("--remote-control", args)

    def test_debug_false_includes_skip_permissions_when_opted_in(self) -> None:
        """Explicit opt-in uses the script's TRUE=\"0\" convention."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            env["CLAUDE_SKIP_PERMISSIONS"] = SCRIPT_TRUE

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertIn("--dangerously-skip-permissions", args)

    def test_skip_permissions_one_is_false_under_script_convention(self) -> None:
        """``CLAUDE_SKIP_PERMISSIONS=1`` means FALSE here (unlike the default launcher).

        The older ``default_interactive_session_claude_code.bash`` treats ``1``
        as opt-in. Crossing the conventions silently re-enables (or disables)
        skip-permissions; pin that ``1`` does *not* enable the flag when DEBUG
        is off.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            env["CLAUDE_SKIP_PERMISSIONS"] = SCRIPT_FALSE  # "1"

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertNotIn("--dangerously-skip-permissions", args)

    def test_debug_true_overrides_explicit_skip_permissions_false(self) -> None:
        """Even an explicit FALSE cannot disarm the shipped DEBUG force."""
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=True)
            env = self._base_env(args_log)
            env["CLAUDE_SKIP_PERMISSIONS"] = SCRIPT_FALSE

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertIn("--dangerously-skip-permissions", args)

    def test_remote_control_false_omits_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)
            env["CLAUDE_REMOTE_CONTROL"] = SCRIPT_FALSE

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertNotIn("--remote-control", args)

    def test_positional_model_and_effort(self) -> None:
        """Positional ``$1``/``$2`` become ``--model`` / ``--effort``.

        Note: the script does not ``shift`` after reading effort, so the
        leftover effort token is also appended as a passthrough arg. Pin
        that current compose (a silent second ``shift`` would drop it).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir, debug=False)
            env = self._base_env(args_log)

            result = self._run_launcher(
                launcher_path,
                temp_dir,
                env,
                extra_args=["sonnet", "high"],
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertEqual(args[args.index("--model") + 1], "sonnet")
            self.assertEqual(args[args.index("--effort") + 1], "high")
            # Leftover positional after the unshifted effort read.
            self.assertEqual(args[-1], "high")


if __name__ == "__main__":
    unittest.main()
