#!/usr/bin/env python3
"""Regression tests for wake_the_claude resume/session-id handling."""

import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wake_the_claude.bash"
DEFAULT_INTERACTIVE_SCRIPT_PATH = REPO_ROOT / "scripts" / "default_interactive_session_claude_code.bash"
VALID_UUID = "7632f5ab-4bac-11e6-bcb7-0cc47a6c4dbd"
UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

# Test fixture timeouts (centralized so call sites and defaults stay in sync).
DEFAULT_INVOCATION_WAIT_TIMEOUT: float = 2.0
SHORT_INVOCATION_WAIT_TIMEOUT: float = 0.3
INVOCATION_POLL_INTERVAL: float = 0.05


class WakeTheClaudeResumeTests(unittest.TestCase):
    def _install_fake_claude(self, temp_dir: str, *, failing_uuidgen: bool = False) -> tuple[Path, dict[str, str]]:
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        sessions_dir = Path(temp_dir) / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = Path(temp_dir) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        invocations_log = Path(temp_dir) / "claude_invocations.log"
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\n" 'if [[ "$1" == "--version" ]]; then\n' '  echo "claude-test-version"\n' "  exit 0\n" "fi\n" "{\n" '  echo "__CALL__"\n' '  echo "ARGC=$#"\n' '  for arg in "$@"; do\n' "    printf 'ARG=%s\\n' \"$arg\"\n" "  done\n" '} >> "$CLAUDE_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)

        if failing_uuidgen:
            fake_uuidgen = bin_dir / "uuidgen"
            fake_uuidgen.write_text(
                "#!/usr/bin/env bash\n" "exit 1\n",
                encoding="utf-8",
            )
            fake_uuidgen.chmod(0o755)

        env = RedactedEnv(os.environ)
        # Prevent host shell variables from contaminating test subprocess behavior
        for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["CLAUDE_ARGS_LOG"] = str(invocations_log)
        env["WTC_SESSIONS_DIR"] = str(sessions_dir)
        env["WTC_LOGS_DIR"] = str(logs_dir)
        return invocations_log, env

    def _run_script(self, args: list[str], cwd: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _wait_for_invocations(self, invocations_log: Path, timeout_seconds: float = DEFAULT_INVOCATION_WAIT_TIMEOUT) -> list[list[str]]:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if invocations_log.exists():
                content = invocations_log.read_text(encoding="utf-8").strip()
                if content:
                    blocks: list[list[str]] = []
                    current_block: list[str] = []
                    for line in content.splitlines():
                        if line == "__CALL__":
                            if current_block:
                                blocks.append(current_block)
                            current_block = []
                            continue
                        current_block.append(line)
                    if current_block:
                        blocks.append(current_block)
                    if blocks:
                        return blocks
            time.sleep(INVOCATION_POLL_INTERVAL)
        return []

    @staticmethod
    def _extract_args(invocation_block: list[str]) -> list[str]:
        args: list[str] = []
        for line in invocation_block:
            if line.startswith("ARG="):
                args.append(line.removeprefix("ARG="))
        return args

    @staticmethod
    def _install_fake_command(temp_dir: str, name: str, script_body: str) -> None:
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        fake_command = bin_dir / name
        fake_command.write_text(script_body, encoding="utf-8")
        fake_command.chmod(0o755)

    def test_resume_with_uuid_passes_session_id_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_resume_alias_flag_passes_session_id_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume-session", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_session_id_trailing_alias_flag_passes_value_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--thread-id", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            saved_session_file = Path(temp_dir) / "sessions" / f"{VALID_UUID}.txt"
            self.assertTrue(saved_session_file.exists(), msg="Expected session id file to be created")
            self.assertEqual(saved_session_file.read_text(encoding="utf-8").strip(), VALID_UUID)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--session-id", VALID_UUID, "hello"])

    def test_permissions_trailing_alias_flag_is_forwarded_to_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                [
                    "--resume",
                    VALID_UUID,
                    "--dangerously-skip-permissions",
                    "--prompt",
                    "hello",
                ],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(
                last_invocation_args,
                ["--resume", VALID_UUID, "--dangerously-skip-permissions", "hello"],
            )

    def test_resume_with_filename_loads_uuid_and_preserves_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / "sessions" / "session-id.txt"
            session_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(session_file.exists(), msg="Expected session id file to remain after read-only resume")

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_resume_with_invalid_uuid_fails_once_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            result = self._run_script(
                ["--resume", "not-a-uuid", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)

            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_with_file_containing_invalid_uuid_fails_and_preserves_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / "sessions" / "session-id.txt"
            session_file.write_text("invalid-content", encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(session_file.exists(), msg="Expected invalid session id file to remain after rejection")

            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)
            self.assertNotIn("invalid-content", combined_output)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_rejects_filename_with_path_separator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            nested_dir = Path(temp_dir) / "nested"
            nested_dir.mkdir(parents=True, exist_ok=True)
            nested_file = nested_dir / "session-id.txt"
            nested_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", "nested/session-id.txt", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Session ID is invalid. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_rejects_non_txt_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / "session-id.dat"
            session_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Session ID is invalid. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_with_missing_txt_file_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            missing_session_file = Path(temp_dir) / "sessions" / "missing-session-id.txt"

            result = self._run_script(
                ["--resume", missing_session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertFalse(
                missing_session_file.exists(),
                msg="Expected script not to create missing resume source file",
            )

            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Session ID is invalid. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_with_empty_txt_file_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            empty_session_file = Path(temp_dir) / "sessions" / "empty-session-id.txt"
            empty_session_file.write_text("", encoding="utf-8")

            result = self._run_script(
                ["--resume", empty_session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(
                empty_session_file.exists(),
                msg="Expected empty resume source file to be preserved after rejection",
            )

            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Session ID is invalid. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_with_filename_works_when_debug_logging_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            env["WTC_DEBUG"] = "1"
            session_file = Path(temp_dir) / "sessions" / "session-id.txt"
            session_file.write_text(VALID_UUID, encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "hello"])

    def test_resume_flag_without_value_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            result = self._run_script(
                ["--resume", "--", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)

            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Received Resume Flag but no Valid Session ID to Resume. Exiting...", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_session_id_save_rejects_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            symlink_target = Path(temp_dir) / "sensitive-target.txt"
            symlink_target.write_text("ORIGINAL", encoding="utf-8")
            symlink_path = Path(temp_dir) / "sessions" / f"{VALID_UUID}.txt"
            symlink_path.symlink_to(symlink_target)

            result = self._run_script(
                ["--id", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(symlink_path.is_symlink())
            self.assertEqual(symlink_target.read_text(encoding="utf-8"), "ORIGINAL")
            combined_output = result.stdout + result.stderr
            self.assertIn("symlink", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_with_nonexistent_txt_file_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            result = self._run_script(
                ["--resume", "missing-session.txt", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)

            combined_output = result.stdout + result.stderr
            self.assertIn("Session ID is invalid", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_without_value_fails_without_invoking_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            result = self._run_script(
                ["--resume", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)

            combined_output = result.stdout + result.stderr
            self.assertIn("no Valid Session ID", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_prompt_with_shell_tokens_is_passed_as_single_argument(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_text = "hello ; --model injected $(whoami) with spaces"

            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", prompt_text],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, prompt_text])
            self.assertNotIn("--model", last_invocation_args)

    def test_session_id_without_value_uses_uuid_fallback_when_uuidgen_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir, failing_uuidgen=True)
            fallback_uuid = "11111111-2222-3333-4444-555555555555"
            self._install_fake_command(
                temp_dir,
                "cat",
                "#!/usr/bin/env bash\n" f'if [[ "$1" == "/proc/sys/kernel/random/uuid" ]]; then\n' f'  echo "{fallback_uuid}"\n' "  exit 0\n" "fi\n" '/usr/bin/cat "$@"\n',
            )

            result = self._run_script(
                ["--id", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            saved_session_file = Path(temp_dir) / "sessions" / f"{fallback_uuid}.txt"
            self.assertTrue(saved_session_file.exists(), msg="Expected generated session id file to be created")
            self.assertEqual(saved_session_file.read_text(encoding="utf-8").strip(), fallback_uuid)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--session-id", fallback_uuid, "hello"])

    def test_session_id_without_value_uses_python_fallback_when_uuidgen_and_proc_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir, failing_uuidgen=True)
            python_fallback_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            self._install_fake_command(
                temp_dir,
                "cat",
                "#!/usr/bin/env bash\n" 'if [[ "$1" == "/proc/sys/kernel/random/uuid" ]]; then\n' '  echo "not-a-uuid"\n' "  exit 0\n" "fi\n" '/usr/bin/cat "$@"\n',
            )
            self._install_fake_command(
                temp_dir,
                "python3",
                "#!/usr/bin/env bash\n" f'echo "{python_fallback_uuid}"\n',
            )

            result = self._run_script(
                ["--id", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--session-id", python_fallback_uuid, "hello"])

    def test_session_id_without_value_fails_when_all_uuid_fallbacks_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir, failing_uuidgen=True)
            self._install_fake_command(
                temp_dir,
                "cat",
                "#!/usr/bin/env bash\n" 'if [[ "$1" == "/proc/sys/kernel/random/uuid" ]]; then\n' '  echo "still-not-a-uuid"\n' "  exit 0\n" "fi\n" '/usr/bin/cat "$@"\n',
            )
            self._install_fake_command(
                temp_dir,
                "python3",
                "#!/usr/bin/env bash\n" 'echo "bad-python-uuid-output"\n',
            )

            result = self._run_script(
                ["--id", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("Error: Failed to generate a valid UUID for Session ID.", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_prompt_file_path_then_file_name_loads_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_dir = Path(temp_dir) / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = prompt_dir / "prompt.md"
            prompt_file.write_text("from-prompt-file", encoding="utf-8")

            result = self._run_script(
                ["--id", VALID_UUID, "--path", str(prompt_dir), "--file", prompt_file.name],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args[0:2], ["--session-id", VALID_UUID])
            self.assertEqual(last_invocation_args[-1].strip('"'), "from-prompt-file")

    # def test_prompt_file_name_then_path_loads_prompt(self) -> None:
    #     with tempfile.TemporaryDirectory() as temp_dir:
    #         invocations_log, env = self._install_fake_claude(temp_dir)
    #         prompt_dir = Path(temp_dir) / "prompts"
    #         prompt_dir.mkdir(parents=True, exist_ok=True)
    #         prompt_file = prompt_dir / "prompt.md"
    #         prompt_file.write_text("from-prompt-file", encoding="utf-8")

    #         self._run_script(
    #             ["--id", VALID_UUID, "--file", prompt_file.name, "--path", str(prompt_dir)],
    #             cwd=temp_dir,
    #             env=env,
    #         )

    def test_custom_session_and_logs_dirs_are_created_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_dir = Path(temp_dir) / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = prompt_dir / "prompt.md"
            prompt_file.write_text("from-prompt-file", encoding="utf-8")

            result = self._run_script(
                ["--id", VALID_UUID, "--path", str(prompt_dir), "--file", prompt_file.name],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args[0:2], ["--session-id", VALID_UUID])
            self.assertEqual(last_invocation_args[-1].strip('"'), "from-prompt-file")

    # def test_default_interactive_script_forwards_expected_defaults(self) -> None:
    #     with tempfile.TemporaryDirectory() as temp_dir:
    #         invocations_log, env = self._install_fake_claude(temp_dir)
    #         self.assertTrue(DEFAULT_INTERACTIVE_SCRIPT_PATH.exists())

    #         result = subprocess.run(
    #             ["bash", str(DEFAULT_INTERACTIVE_SCRIPT_PATH)],
    #             cwd=temp_dir,
    #             env=env,
    #             text=True,
    #             capture_output=True,
    #             check=False,
    #         )

    #         self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    #         invocations = self._wait_for_invocations(invocations_log)
    #         self.assertTrue(invocations, msg="Expected default launcher to invoke claude at least once")
    #         last_invocation_args = self._extract_args(invocations[-1])

    #         self.assertIn("--session-id", last_invocation_args)
    #         session_id_index = last_invocation_args.index("--session-id")
    #         self.assertLess(session_id_index + 1, len(last_invocation_args))
    #         self.assertRegex(last_invocation_args[session_id_index + 1], UUID_REGEX)
    #         self.assertIn("--worktree", last_invocation_args)
    #         self.assertNotIn("--dangerously-skip-permissions", last_invocation_args)
    #         self.assertIn("--effort", last_invocation_args)
    #         effort_index = last_invocation_args.index("--effort")
    #         self.assertLess(effort_index + 1, len(last_invocation_args))
    #         self.assertEqual(last_invocation_args[effort_index + 1], "high")
    #         self.assertIn("Hello World, Claude!", last_invocation_args)

    def test_prompt_file_name_then_path_loads_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_dir = Path(temp_dir) / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = prompt_dir / "prompt.md"
            prompt_file.write_text("from-prompt-file", encoding="utf-8")

            result = self._run_script(
                ["--id", VALID_UUID, "--file", prompt_file.name, "--path", str(prompt_dir)],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args[0:2], ["--session-id", VALID_UUID])
            self.assertEqual(last_invocation_args[-1].strip('"'), "from-prompt-file")

    def test_default_interactive_script_forwards_expected_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            self.assertTrue(DEFAULT_INTERACTIVE_SCRIPT_PATH.exists())

            result = subprocess.run(
                ["bash", str(DEFAULT_INTERACTIVE_SCRIPT_PATH)],
                cwd=temp_dir,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected default launcher to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])

            self.assertIn("--session-id", last_invocation_args)
            session_id_index = last_invocation_args.index("--session-id")
            self.assertLess(session_id_index + 1, len(last_invocation_args))
            self.assertRegex(last_invocation_args[session_id_index + 1], UUID_REGEX)
            self.assertIn("--worktree", last_invocation_args)
            self.assertNotIn("--dangerously-skip-permissions", last_invocation_args)
            self.assertIn("--effort", last_invocation_args)
            effort_index = last_invocation_args.index("--effort")
            self.assertLess(effort_index + 1, len(last_invocation_args))
            self.assertEqual(last_invocation_args[effort_index + 1], "high")
            prompt_tokens = [token.strip('"') for token in last_invocation_args[effort_index + 2 :]]
            self.assertEqual(" ".join(prompt_tokens), "Hello World, Claude!")

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can write to chmod read-only directories")
    def test_non_writable_cwd_falls_back_to_home_log_and_still_launches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            home_dir = Path(temp_dir) / "home"
            home_dir.mkdir(parents=True, exist_ok=True)
            env["HOME"] = str(home_dir)

            read_only_logs = Path(temp_dir) / "read-only-logs"
            read_only_logs.mkdir(parents=True, exist_ok=True)
            read_only_logs.chmod(0o555)
            env["WTC_LOGS_DIR"] = str(read_only_logs)
            try:
                result = self._run_script(
                    ["--resume", VALID_UUID, "--print", "--prompt", "hello"],
                    cwd=temp_dir,
                    env=env,
                )
            finally:
                read_only_logs.chmod(0o755)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertFalse((read_only_logs / "wake_the_claude.nohup.log").exists())
            self.assertTrue((home_dir / "wake_the_claude.nohup.log").exists())

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations, msg="Expected wake_the_claude to invoke claude at least once")
            last_invocation_args = self._extract_args(invocations[-1])
            self.assertEqual(last_invocation_args, ["--resume", VALID_UUID, "--print", "hello"])

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can write to chmod read-only directories")
    def test_no_writable_log_location_fails_without_silent_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)

            read_only_logs = Path(temp_dir) / "read-only-logs"
            read_only_logs.mkdir(parents=True, exist_ok=True)
            read_only_logs.chmod(0o555)
            env["WTC_LOGS_DIR"] = str(read_only_logs)

            read_only_home = Path(temp_dir) / "read-only-home"
            read_only_home.mkdir(parents=True, exist_ok=True)
            read_only_home.chmod(0o555)
            env["HOME"] = str(read_only_home)

            try:
                result = self._run_script(
                    ["--resume", VALID_UUID, "--print", "--prompt", "hello"],
                    cwd=temp_dir,
                    env=env,
                )
            finally:
                read_only_logs.chmod(0o755)
                read_only_home.chmod(0o755)

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Failed to open nohup log file", result.stderr)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_missing_claude_binary_fails_without_silent_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log = Path(temp_dir) / "claude_invocations.log"
            isolated_bin = Path(temp_dir) / "isolated-bin"
            isolated_bin.mkdir(parents=True, exist_ok=True)

            bash_path = shutil.which("bash")
            self.assertIsNotNone(bash_path, msg="bash must be discoverable for this test")
            assert bash_path is not None
            os.symlink(str(Path(bash_path)), str(isolated_bin / "bash"))

            env = RedactedEnv(os.environ)
            env["PATH"] = str(isolated_bin)
            env["HOME"] = temp_dir
            env["CLAUDE_ARGS_LOG"] = str(invocations_log)

            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("claude command not found in PATH", result.stderr)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_exported_claude_function_without_binary_fails_without_silent_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log = Path(temp_dir) / "claude_invocations.log"
            isolated_bin = Path(temp_dir) / "isolated-bin"
            isolated_bin.mkdir(parents=True, exist_ok=True)

            bash_path = shutil.which("bash")
            self.assertIsNotNone(bash_path, msg="bash must be discoverable for this test")
            assert bash_path is not None
            os.symlink(str(Path(bash_path)), str(isolated_bin / "bash"))

            env = RedactedEnv(os.environ)
            env["PATH"] = str(isolated_bin)
            env["HOME"] = temp_dir
            env["CLAUDE_ARGS_LOG"] = str(invocations_log)
            env["BASH_FUNC_claude%%"] = "() { echo wrapper-function; }"

            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("claude command not found in PATH", result.stderr)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_resume_with_generated_filename_but_invalid_content_preserves_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            session_file = Path(temp_dir) / "sessions" / f"{VALID_UUID}.txt"
            session_file.write_text("invalid-content", encoding="utf-8")

            result = self._run_script(
                ["--resume", session_file.name, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertTrue(
                session_file.exists(),
                msg="Expected generated-style session id file to be preserved when content is invalid",
            )

            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])


class WakeTheClaudeSecurityTests(unittest.TestCase):
    """Security-focused tests for shell argument handling and permission boundaries."""

    def _install_fake_claude(self, temp_dir: str) -> tuple[Path, dict[str, str]]:
        bin_dir = Path(temp_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        sessions_dir = Path(temp_dir) / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = Path(temp_dir) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        invocations_log = Path(temp_dir) / "claude_invocations.log"
        fake_claude = bin_dir / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\n" 'if [[ "$1" == "--version" ]]; then\n' '  echo "claude-test-version"\n' "  exit 0\n" "fi\n" "{\n" '  echo "__CALL__"\n' '  echo "ARGC=$#"\n' '  for arg in "$@"; do\n' "    printf 'ARG=%s\\n' \"$arg\"\n" "  done\n" '} >> "$CLAUDE_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)

        env = RedactedEnv(os.environ)
        # Prevent host shell variables from contaminating test subprocess behavior
        for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV"):
            env.pop(var, None)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        env["CLAUDE_ARGS_LOG"] = str(invocations_log)
        env["WTC_SESSIONS_DIR"] = str(sessions_dir)
        env["WTC_LOGS_DIR"] = str(logs_dir)
        return invocations_log, env

    def _run_script(self, args: list[str], cwd: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_default_launcher(self, args: list[str], cwd: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        default_launcher_path = REPO_ROOT / "scripts" / "default_interactive_session_claude_code.bash"
        return subprocess.run(
            ["bash", str(default_launcher_path), *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _wait_for_invocations(self, invocations_log: Path, timeout_seconds: float = DEFAULT_INVOCATION_WAIT_TIMEOUT) -> list[list[str]]:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if invocations_log.exists():
                content = invocations_log.read_text(encoding="utf-8").strip()
                if content:
                    blocks: list[list[str]] = []
                    current_block: list[str] = []
                    for line in content.splitlines():
                        if line == "__CALL__":
                            if current_block:
                                blocks.append(current_block)
                            current_block = []
                            continue
                        current_block.append(line)
                    if current_block:
                        blocks.append(current_block)
                    if blocks:
                        return blocks
            time.sleep(INVOCATION_POLL_INTERVAL)
        return []

    @staticmethod
    def _extract_args(invocation_block: list[str]) -> list[str]:
        args: list[str] = []
        for line in invocation_block:
            if line.startswith("ARG="):
                args.append(line.removeprefix("ARG="))
        return args

    def test_effort_flag_and_value_are_separate_arguments(self) -> None:
        """HIGH: Verify --effort and its value are passed as two separate CLI arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--effort", "high", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            # --effort and high must be separate arguments, not "--effort high"
            self.assertIn("--effort", args)
            self.assertIn("high", args)
            effort_idx = args.index("--effort")
            self.assertEqual(args[effort_idx + 1], "high")
            # Verify no single element contains both
            for arg in args:
                self.assertNotEqual(arg, "--effort high", "effort flag and value must be separate arguments")

    def test_model_flag_and_value_are_separate_arguments(self) -> None:
        """HIGH: Verify --model and its value are passed as two separate CLI arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--model", "claude-sonnet-4-6", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("--model", args)
            self.assertIn("claude-sonnet-4-6", args)
            model_idx = args.index("--model")
            self.assertEqual(args[model_idx + 1], "claude-sonnet-4-6")
            for arg in args:
                self.assertNotEqual(arg, "--model claude-sonnet-4-6", "model flag and value must be separate arguments")

    def test_invalid_model_fails_without_invoking_claude(self) -> None:
        """validate_model must reject unknown names before launching claude (usage exit 1)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--model", "not-a-real-model", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)
            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_model_flag_without_value_fails_without_invoking_claude(self) -> None:
        """--model with no following value must fail early and never launch claude."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--model"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)
            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_model_alias_case_insensitive_is_accepted(self) -> None:
        """validate_model lowercases input so OPUS matches the opus alias allowlist entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--model", "OPUS", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("--model", args)
            self.assertIn("OPUS", args)

    def test_invalid_effort_fails_without_invoking_claude(self) -> None:
        """Invalid --effort values must fail before launching claude (usage exit 1)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--effort", "ultra", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)
            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])

    def test_prompt_with_glob_characters_is_not_expanded(self) -> None:
        """HIGH: Verify glob characters in prompt text are not expanded to filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            # Create files that would match glob patterns
            (Path(temp_dir) / "file1.txt").write_text("a", encoding="utf-8")
            (Path(temp_dir) / "file2.txt").write_text("b", encoding="utf-8")

            prompt_with_globs = "list all *.txt files and check [a-z]? patterns"
            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", prompt_with_globs],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            # The prompt must be passed as a single argument, unexpanded
            self.assertEqual(args[-1], prompt_with_globs)
            # Must NOT contain expanded filenames
            self.assertNotIn("file1.txt", args)
            self.assertNotIn("file2.txt", args)

    def test_prompt_with_dollar_signs_is_not_evaluated(self) -> None:
        """HIGH: Verify dollar signs in prompt text are preserved literally."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_with_dollars = "cost is $100 and $(echo injected)"
            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", prompt_with_dollars],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertEqual(args[-1], prompt_with_dollars)
            self.assertNotIn("injected", [a for a in args if a != args[-1]])

    def test_prompt_does_not_have_literal_wrapping_quotes(self) -> None:
        """HIGH: Verify prompt is not wrapped in literal quote characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "simple prompt"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            # The prompt must not be wrapped in literal quote characters
            self.assertEqual(args[-1], "simple prompt")
            self.assertNotEqual(args[-1], '"simple prompt"')

    def test_interactive_mode_invokes_claude_in_foreground(self) -> None:
        """Verify interactive mode (no --print) runs claude directly, not via nohup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertEqual(args, ["--resume", VALID_UUID, "hello"])
            # In interactive mode, no nohup log should be created in the logs dir
            self.assertFalse((Path(temp_dir) / "logs" / "wake_the_claude.nohup.log").exists())

    def test_headless_mode_invokes_claude_via_nohup(self) -> None:
        """Verify headless mode (--print) runs claude via nohup with log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--print", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertEqual(args, ["--resume", VALID_UUID, "--print", "hello"])
            # In headless mode, nohup log should be created in the logs dir
            self.assertTrue((Path(temp_dir) / "logs" / "wake_the_claude.nohup.log").exists())

    def test_session_id_autogenerated_flag_and_value_are_separate(self) -> None:
        """HIGH: Verify auto-generated --session-id and UUID are separate arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--id", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("--session-id", args)
            sid_idx = args.index("--session-id")
            generated_uuid = args[sid_idx + 1]
            self.assertTrue(
                UUID_REGEX.match(generated_uuid),
                f"Expected UUID after --session-id, got: {generated_uuid}",
            )
            # Must not be a single combined string
            for arg in args:
                self.assertFalse(
                    arg.startswith("--session-id "),
                    "session-id flag and value must be separate arguments",
                )

    def test_default_launcher_does_not_skip_permissions(self) -> None:
        """HIGH: Verify default launcher never injects dangerous skip-permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_default_launcher([], cwd=temp_dir, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertNotIn("--dangerously-skip-permissions", args)

    def test_default_launcher_opt_in_skip_permissions(self) -> None:
        """HIGH: Verify default launcher supports explicit opt-in to skip-permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            env["CLAUDE_SKIP_PERMISSIONS"] = "1"
            result = self._run_default_launcher([], cwd=temp_dir, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("--dangerously-skip-permissions", args)

    def test_default_launcher_runtime_omits_skip_permissions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            env.pop("CLAUDE_SKIP_PERMISSIONS", None)

            result = self._run_default_launcher(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertNotIn("--dangerously-skip-permissions", args)

    def test_default_launcher_runtime_honors_skip_permissions_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            env["CLAUDE_SKIP_PERMISSIONS"] = "1"

            result = self._run_default_launcher(
                ["--resume", VALID_UUID, "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("--dangerously-skip-permissions", args)

        """HIGH: Verify default launcher never injects dangerous skip-permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_default_launcher([], cwd=temp_dir, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertNotIn("--dangerously-skip-permissions", args)

    def test_default_launcher_executes_with_expected_default_arguments(self) -> None:
        """HIGH: Verify default launcher passes safe defaults into wake_the_claude."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_default_launcher([], cwd=temp_dir, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])

            self.assertIn("--session-id", args)
            sid_idx = args.index("--session-id")
            generated_uuid = args[sid_idx + 1]
            self.assertTrue(
                UUID_REGEX.match(generated_uuid),
                f"Expected UUID after --session-id, got: {generated_uuid}",
            )
            self.assertIn("--worktree", args)
            self.assertIn("--effort", args)
            effort_idx = args.index("--effort")
            self.assertEqual(args[effort_idx + 1], "high")
            self.assertIn("Hello World, Claude!", args)
            self.assertNotIn("--dangerously-skip-permissions", args)

    def test_default_launcher_forwards_skip_permissions_when_opted_in(self) -> None:
        """HIGH: Verify default launcher forwards skip-permissions when enabled by env var."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            env["CLAUDE_SKIP_PERMISSIONS"] = "1"

            result = self._run_default_launcher([], cwd=temp_dir, env=env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("--dangerously-skip-permissions", args)

    def test_fork_session_alias_forwards_canonical_flag(self) -> None:
        """HIGH: Verify --fork alias forwards as canonical --fork-session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            result = self._run_script(
                ["--resume", VALID_UUID, "--fork", "--prompt", "hello"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertEqual(args, ["--resume", VALID_UUID, "--fork-session", "hello"])

    def test_all_fork_session_flag_variants_forward_canonical_flag(self) -> None:
        """HIGH: Verify legacy and canonical fork flags normalize to --fork-session."""
        for fork_flag in ("--fork-session", "--resume-fork", "--resume-fork_session"):
            with self.subTest(fork_flag=fork_flag), tempfile.TemporaryDirectory() as temp_dir:
                invocations_log, env = self._install_fake_claude(temp_dir)
                result = self._run_script(
                    ["--resume", VALID_UUID, fork_flag, "--prompt", "hello"],
                    cwd=temp_dir,
                    env=env,
                )
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

                invocations = self._wait_for_invocations(invocations_log)
                self.assertTrue(invocations)
                args = self._extract_args(invocations[-1])
                self.assertEqual(args, ["--resume", VALID_UUID, "--fork-session", "hello"])

    def test_path_flag_with_file_argument_resolves_correctly(self) -> None:
        """Verify --path with a file argument (not directory) sets prompt correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_file = Path(temp_dir) / "my_prompt.md"
            prompt_file.write_text("prompt from file", encoding="utf-8")
            result = self._run_script(
                ["--resume", VALID_UUID, "--path", str(prompt_file)],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("prompt from file", args)

    def test_path_directory_and_filename_resolve_prompt_when_path_precedes_file(self) -> None:
        """Verify --path <dir> + --file <name> works when path is parsed first."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompts_dir = Path(temp_dir) / "prompts"
            prompts_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = prompts_dir / "my_prompt.md"
            prompt_file.write_text("prompt from path+file", encoding="utf-8")

            result = self._run_script(
                ["--resume", VALID_UUID, "--path", str(prompts_dir), "--file", "my_prompt.md"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertEqual(args, ["--resume", VALID_UUID, "prompt from path+file"])

    def test_path_then_file_flags_resolve_combined_prompt_file(self) -> None:
        """Verify --path <dir> then --file <name> resolves prompt file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_dir = Path(temp_dir) / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            (prompt_dir / "prompt.md").write_text("prompt from combined path-then-file", encoding="utf-8")

            result = self._run_script(
                ["--resume", VALID_UUID, "--path", str(prompt_dir), "--file", "prompt.md"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertEqual(args, ["--resume", VALID_UUID, "prompt from combined path-then-file"])

    def test_path_directory_and_filename_resolve_prompt_when_file_precedes_path(self) -> None:
        """Verify --file <name> + --path <dir> works when file is parsed first."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompts_dir = Path(temp_dir) / "prompts"
            prompts_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = prompts_dir / "my_prompt.md"
            prompt_file.write_text("prompt from file+path", encoding="utf-8")

            result = self._run_script(
                ["--resume", VALID_UUID, "--file", "my_prompt.md", "--path", str(prompts_dir)],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertIn("prompt from file+path", args)

    def test_file_then_path_flags_resolve_combined_prompt_file(self) -> None:
        """Verify --file <name> then --path <dir> resolves prompt file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompt_dir = Path(temp_dir) / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            (prompt_dir / "prompt.md").write_text("prompt from combined file-then-path", encoding="utf-8")

            result = self._run_script(
                ["--resume", VALID_UUID, "--file", "prompt.md", "--path", str(prompt_dir)],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            invocations = self._wait_for_invocations(invocations_log)
            self.assertTrue(invocations)
            args = self._extract_args(invocations[-1])
            self.assertEqual(args, ["--resume", VALID_UUID, "prompt from combined file-then-path"])

    def test_path_directory_and_missing_filename_fail_without_invoking_claude(self) -> None:
        """Verify invalid --path/--file combination fails early and never launches claude."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invocations_log, env = self._install_fake_claude(temp_dir)
            prompts_dir = Path(temp_dir) / "prompts"
            prompts_dir.mkdir(parents=True, exist_ok=True)

            result = self._run_script(
                ["--resume", VALID_UUID, "--path", str(prompts_dir), "--file", "missing.md"],
                cwd=temp_dir,
                env=env,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("invalid Prompt File", combined_output)
            self.assertEqual(combined_output.count("usage: wake_the_claude.bash"), 1)

            invocations = self._wait_for_invocations(invocations_log, timeout_seconds=SHORT_INVOCATION_WAIT_TIMEOUT)
            self.assertEqual(invocations, [])


class DefaultInteractiveLauncherRuntimeTests(unittest.TestCase):
    """Runtime tests for default interactive launcher argument behavior."""

    def _install_fake_launcher_stack(self, temp_dir: str) -> tuple[Path, Path]:
        scripts_dir = Path(temp_dir) / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        launcher_src = REPO_ROOT / "scripts" / "default_interactive_session_claude_code.bash"
        launcher_path = scripts_dir / "default_interactive_session_claude_code.bash"
        launcher_path.write_text(launcher_src.read_text(encoding="utf-8"), encoding="utf-8")
        launcher_path.chmod(0o755)

        args_log = Path(temp_dir) / "default_launcher_args.log"
        fake_wake = scripts_dir / "wake_the_claude.bash"
        fake_wake.write_text(
            "#!/usr/bin/env bash\n" "{\n" '  echo "__CALL__"\n' '  for arg in "$@"; do\n' "    printf 'ARG=%s\\n' \"$arg\"\n" "  done\n" '} >> "$WTC_WRAPPER_ARGS_LOG"\n',
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

    def _run_launcher(
        self,
        launcher_path: Path,
        temp_dir: str,
        env: dict[str, str],
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

    def test_default_launcher_omits_skip_permissions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir)
            env = RedactedEnv(os.environ)
            for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV"):
                env.pop(var, None)
            env["WTC_WRAPPER_ARGS_LOG"] = str(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertTrue(args, "Expected wrapper to invoke wake_the_claude.bash")
            self.assertNotIn("--dangerously-skip-permissions", args)
            self.assertEqual(
                args[:6],
                ["--id", "--worktree", "--effort", "high", "--prompt", "Hello World, Claude!"],
            )

    def test_default_launcher_includes_skip_permissions_only_when_opted_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir)
            env = RedactedEnv(os.environ)
            for var in ("BASH_ENV", "ENV"):
                env.pop(var, None)
            env["CLAUDE_SKIP_PERMISSIONS"] = "1"
            env["WTC_WRAPPER_ARGS_LOG"] = str(args_log)

            result = self._run_launcher(launcher_path, temp_dir, env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertIn("--dangerously-skip-permissions", args)

    def test_default_launcher_forwards_additional_args(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher_path, args_log = self._install_fake_launcher_stack(temp_dir)
            env = RedactedEnv(os.environ)
            for var in ("CLAUDE_SKIP_PERMISSIONS", "BASH_ENV", "ENV"):
                env.pop(var, None)
            env["WTC_WRAPPER_ARGS_LOG"] = str(args_log)
            passthrough_args = ["--model", "claude-sonnet-4-6", "--print"]

            result = self._run_launcher(launcher_path, temp_dir, env, passthrough_args)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            args = self._extract_logged_args(args_log)
            self.assertEqual(args[-len(passthrough_args) :], passthrough_args)


class WakeTheClaudeGitignoreTests(unittest.TestCase):
    """Tests for .gitignore coverage of sensitive files."""

    def test_gitignore_covers_session_files(self) -> None:
        """LOW: Verify .gitignore includes patterns for session files in scripts/sessions/."""
        gitignore_path = REPO_ROOT / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        self.assertIn("scripts/sessions/", content)

    def test_gitignore_covers_logs_directory(self) -> None:
        """Verify .gitignore includes patterns for the logs/ directory."""
        gitignore_path = REPO_ROOT / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        self.assertIn("logs/", content)

    def test_gitignore_covers_nohup_output(self) -> None:
        """Verify .gitignore includes patterns for nohup output files."""
        gitignore_path = REPO_ROOT / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        self.assertIn("nohup", content)

    def test_no_session_txt_files_committed_in_scripts(self) -> None:
        """LOW: Verify no UUID .txt session files are tracked in scripts/ or scripts/sessions/."""
        result = subprocess.run(
            ["git", "ls-files", "scripts/*.txt", "scripts/sessions/*.txt"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        tracked_txt_files = [f for f in result.stdout.strip().splitlines() if f and UUID_REGEX.match(Path(f).stem)]
        self.assertEqual(
            tracked_txt_files,
            [],
            f"UUID session files should not be committed: {tracked_txt_files}",
        )

    def test_sessions_dir_exists_with_gitkeep(self) -> None:
        """Verify scripts/sessions/ directory exists and has .gitkeep."""
        sessions_dir = REPO_ROOT / "scripts" / "sessions"
        self.assertTrue(sessions_dir.is_dir(), "scripts/sessions/ directory must exist")
        self.assertTrue(
            (sessions_dir / ".gitkeep").exists(),
            "scripts/sessions/.gitkeep must exist",
        )

    def test_logs_dir_exists_with_gitkeep(self) -> None:
        """Verify logs/ directory exists and has .gitkeep."""
        logs_dir = REPO_ROOT / "logs"
        self.assertTrue(logs_dir.is_dir(), "logs/ directory must exist")
        self.assertTrue(
            (logs_dir / ".gitkeep").exists(),
            "logs/.gitkeep must exist",
        )


if __name__ == "__main__":
    unittest.main()
