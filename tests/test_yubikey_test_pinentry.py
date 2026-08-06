"""
Hermetic Assuan-protocol regression for the YubiKey test pinentry stub.

The #904 post-review reformat dropped the protocol-mandatory ``OK `` prefix from
the stub greeting and BYE reply; gpg-agent then treated the stub as a dead
pinentry (``No pinentry``). #914 restored the tokens. These tests pin that
contract plus GETPIN class routing (Admin / card-PIN / passphrase) so a future
wording pass cannot re-strip Assuan syntax or mis-route secrets.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-03_yubikey_test_pinentry.bash"
SCRIPT_TIMEOUT_SECONDS = 5


def _run_pinentry(
    commands: list[str],
    *,
    admin_pin: str = "admin-secret",
    user_pin: str = "user-secret",
    passphrase: str = "pass-secret",
    log_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = RedactedEnv(
        os.environ,
        TEST_ADMIN_PIN=admin_pin,
        TEST_USER_PIN=user_pin,
        TEST_PASSPHRASE=passphrase,
    )
    if log_path is not None:
        env["PINENTRY_STUB_LOG"] = str(log_path)
    else:
        env.pop("PINENTRY_STUB_LOG", None)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        input="\n".join(commands) + "\n",
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=False,
    )


class TestYubikeyTestPinentryAssuan(unittest.TestCase):
    def test_script_exists_and_is_executable_source(self) -> None:
        self.assertTrue(SCRIPT.is_file(), msg=f"missing stub: {SCRIPT}")

    def test_greeting_and_bye_are_assuan_ok_responses(self) -> None:
        """#914 regression: greeting + BYE must be OK response lines."""
        result = _run_pinentry(["BYE"])
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        lines = result.stdout.splitlines()
        self.assertGreaterEqual(len(lines), 2, msg=result.stdout)
        self.assertTrue(
            lines[0].startswith("OK "),
            msg=f"Assuan greeting must be an OK response line; got {lines[0]!r}",
        )
        self.assertEqual(lines[0], "OK Pleased to meet you !")
        self.assertTrue(
            lines[-1].startswith("OK "),
            msg=f"BYE reply must be an OK response line; got {lines[-1]!r}",
        )
        self.assertEqual(lines[-1], "OK Closing connection...")

    def test_getpin_routes_admin_user_and_passphrase(self) -> None:
        result = _run_pinentry(
            [
                "SETDESC Please enter the Admin PIN",
                "SETPROMPT PIN:",
                "GETPIN",
                "SETDESC Please unlock the card",
                "SETPROMPT PIN:",
                "GETPIN",
                "SETDESC Enter passphrase to unlock the secret key",
                "SETPROMPT Passphrase:",
                "GETPIN",
                "BYE",
            ],
            admin_pin="A-ADMIN",
            user_pin="U-USER",
            passphrase="P-PASS",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "OK Pleased to meet you !")
        # SETDESC/SETPROMPT each ACK with OK; GETPIN emits D <secret> then OK.
        self.assertEqual(
            lines[1:7],
            ["OK", "OK", "D A-ADMIN", "OK", "OK", "OK"],
        )
        self.assertEqual(lines[7:9], ["D U-USER", "OK"])
        self.assertEqual(lines[9:13], ["OK", "OK", "D P-PASS", "OK"])
        self.assertEqual(lines[-1], "OK Closing connection...")

    def test_getpin_pin_token_routes_to_user_pin_not_passphrase(self) -> None:
        """Card PIN prompts that mention PIN (but not Admin) must use TEST_USER_PIN."""
        result = _run_pinentry(
            [
                "SETDESC Enter PIN",
                "SETPROMPT PIN:",
                "GETPIN",
                "BYE",
            ],
            user_pin="CARD-PIN",
            passphrase="NOT-THIS",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("D CARD-PIN", result.stdout.splitlines())
        self.assertNotIn("D NOT-THIS", result.stdout.splitlines())

    def test_admin_wins_when_prompt_also_mentions_pin(self) -> None:
        result = _run_pinentry(
            [
                "SETDESC Admin PIN required",
                "SETPROMPT PIN:",
                "GETPIN",
                "BYE",
            ],
            admin_pin="ADMIN-WINS",
            user_pin="USER-LOSES",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data_lines = [line for line in result.stdout.splitlines() if line.startswith("D ")]
        self.assertEqual(data_lines, ["D ADMIN-WINS"])

    def test_crlf_commands_are_accepted(self) -> None:
        """gpg-agent may send CR-terminated Assuan lines; stub strips CR."""
        result = _run_pinentry(
            [
                "SETDESC unlock the card\r",
                "GETPIN\r",
                "BYE\r",
            ],
            user_pin="CRLF-USER",
        )
        # _run_pinentry joins with \n; embed CR inside the command strings above.
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("D CRLF-USER", result.stdout.splitlines())
        self.assertEqual(result.stdout.splitlines()[-1], "OK Closing connection...")

    def test_log_records_classes_never_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "pinentry.log"
            result = _run_pinentry(
                [
                    "SETDESC Please enter the Admin PIN",
                    "GETPIN",
                    "BYE",
                ],
                admin_pin="SUPER-SECRET-ADMIN",
                log_path=log_path,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            log_text = log_path.read_text()
            self.assertIn("GETPIN -> admin-pin", log_text)
            self.assertNotIn("SUPER-SECRET-ADMIN", log_text)
            self.assertNotIn("D SUPER-SECRET-ADMIN", log_text)


if __name__ == "__main__":
    unittest.main()
