"""
Tests for util/isolated_stack.bash

Contract tests for the isolated training-runtime E2E bring-up helper (roadmap
unit E1 of the canopy training-runtime defects plan). The script encodes the
recipe documented in
``notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md``.

The live ``--up`` path launches long-lived services against conda envs, a
python3.14 venv, and real ports (8101/8202/8051), so — as with
``test_juniper_plant_all.py`` — this suite never brings the stack up. It pins:

- ``bash -n`` cleanliness;
- the launch-line invariants by text inspection (the exact commands + env vars
  the checklist promises);
- the ``--dry-run`` contract behaviourally: every action prints its commands
  with the configured ports expanded and touches NOTHING (no process, no
  filesystem), and the CLI rejects bad invocations;
- ``activate_conda`` nounset restore (live ``--up`` cascor/canopy path) via a
  hermetic function extract — conda activate scripts reference unset vars, so
  nounset is disabled for the call only and must be restored afterward.

``--dry-run`` short-circuits before any filesystem or process side effect, so
these behavioural tests are fully hermetic — no real repos, conda, or network.
``JUNIPER_E2E_PROJECT_DIR`` / ``JUNIPER_E2E_RUN_DIR`` pin paths deterministically.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "isolated_stack.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 15


def _extract_activate_conda_function() -> str:
    """Pull the live ``activate_conda`` body from the script (avoids harness drift)."""
    live = SCRIPT_PATH.read_text()
    match = re.search(
        r"^activate_conda\(\) \{.*?\n\}\n",
        live,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("activate_conda function not found in isolated_stack.bash")
    return match.group(0)


def _run(*args: str, env_extra: "dict[str, str] | None" = None) -> subprocess.CompletedProcess:
    env = RedactedEnv(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestSyntax(unittest.TestCase):
    """The script must pass ``bash -n`` cleanly."""

    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestPortDefaults(unittest.TestCase):
    """Non-default isolated ports 8101/8202/8051, each overridable."""

    def test_data_port_default_and_override(self) -> None:
        self.assertIn('DATA_PORT="${JUNIPER_E2E_DATA_PORT:-8101}"', SCRIPT_TEXT)

    def test_cascor_port_default_and_override(self) -> None:
        self.assertIn('CASCOR_PORT="${JUNIPER_E2E_CASCOR_PORT:-8202}"', SCRIPT_TEXT)

    def test_canopy_port_default_and_override(self) -> None:
        self.assertIn('CANOPY_PORT="${JUNIPER_E2E_CANOPY_PORT:-8051}"', SCRIPT_TEXT)


class TestCondaEnvDefaults(unittest.TestCase):
    """The known-good conda envs, each overridable."""

    def test_cascor_env_default(self) -> None:
        self.assertIn('CASCOR_CONDA="${JUNIPER_E2E_CASCOR_CONDA:-JuniperCascor1}"', SCRIPT_TEXT)

    def test_canopy_env_default(self) -> None:
        self.assertIn('CANOPY_CONDA="${JUNIPER_E2E_CANOPY_CONDA:-JuniperCanopy1}"', SCRIPT_TEXT)


class TestLaunchLines(unittest.TestCase):
    """The launch commands the checklist §3 recipe promises appear verbatim."""

    def test_data_dedicated_venv(self) -> None:
        self.assertIn("python3.14 -m venv", SCRIPT_TEXT)

    def test_data_install_pulls_server_and_metrics_deps(self) -> None:
        # [api] provides uvicorn; prometheus_client + juniper-observability added
        # explicitly (belt-and-suspenders across [api]-extra drift).
        self.assertIn("prometheus_client juniper-observability", SCRIPT_TEXT)
        self.assertIn("${DATA_EXTRAS}", SCRIPT_TEXT)
        self.assertIn('DATA_EXTRAS="${JUNIPER_E2E_DATA_EXTRAS:-api}"', SCRIPT_TEXT)

    def test_data_module_launch_form(self) -> None:
        self.assertIn("python -m juniper_data --host 127.0.0.1 --port", SCRIPT_TEXT)

    def test_cascor_uvicorn_factory(self) -> None:
        self.assertIn("uvicorn api.app:create_app --factory", SCRIPT_TEXT)

    def test_cascor_libtorch_neutralized(self) -> None:
        # The rust_mudgeon libtorch collision guard (empty LD_LIBRARY_PATH).
        self.assertIn("LD_LIBRARY_PATH=", SCRIPT_TEXT)

    def test_cascor_points_at_isolated_data(self) -> None:
        self.assertIn("JUNIPER_DATA_URL=http://127.0.0.1:", SCRIPT_TEXT)

    def test_canopy_service_mode(self) -> None:
        self.assertIn("JUNIPER_CANOPY_DEMO_MODE=0", SCRIPT_TEXT)

    def test_canopy_uses_canonical_service_url(self) -> None:
        # Canonical prefixed env var, NOT the deprecated bare CASCOR_SERVICE_URL alias.
        self.assertIn("JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://127.0.0.1:", SCRIPT_TEXT)


class TestControlWsOriginPair(unittest.TestCase):
    """The control-WS Origin/allowlist pair (the '403 mystery' config fix)."""

    def test_cascor_allowlist_env(self) -> None:
        self.assertIn("JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=", SCRIPT_TEXT)

    def test_canopy_ws_origin_env(self) -> None:
        self.assertIn("JUNIPER_CANOPY_CASCOR_WS_ORIGIN=", SCRIPT_TEXT)

    def test_pair_shares_canopy_origin(self) -> None:
        # Both halves resolve to canopy's own origin.
        self.assertIn('CANOPY_ORIGIN="http://127.0.0.1:${CANOPY_PORT}"', SCRIPT_TEXT)


class TestDocumentedOverrides(unittest.TestCase):
    """The header docstring must advertise the env overrides."""

    def test_env_overrides_documented(self) -> None:
        for var in (
            "JUNIPER_E2E_DATA_PORT",
            "JUNIPER_E2E_CASCOR_PORT",
            "JUNIPER_E2E_CANOPY_PORT",
            "JUNIPER_E2E_DATA_EXTRAS",
            "JUNIPER_E2E_PROJECT_DIR",
        ):
            self.assertIn(var, SCRIPT_TEXT)


class TestHelpAndErrors(unittest.TestCase):
    """CLI surface: help exits 0; misuse exits 2."""

    def test_help_exits_zero(self) -> None:
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)

    def test_unknown_flag_exits_two(self) -> None:
        result = _run("--bogus")
        self.assertEqual(result.returncode, 2)

    def test_no_action_exits_two(self) -> None:
        result = _run()
        self.assertEqual(result.returncode, 2)

    def test_two_actions_exit_two(self) -> None:
        result = _run("--up", "--down")
        self.assertEqual(result.returncode, 2)


class TestDryRunUp(unittest.TestCase):
    """``--dry-run --up`` prints the recipe with ports expanded and starts nothing."""

    def _dry_up(self, run_dir: Path, env_extra: "dict[str, str] | None" = None) -> subprocess.CompletedProcess:
        env = {"JUNIPER_E2E_PROJECT_DIR": "/opt/juniper-e2e-fixture", "JUNIPER_E2E_RUN_DIR": str(run_dir)}
        if env_extra:
            env.update(env_extra)
        return _run("--dry-run", "--up", env_extra=env)

    def test_dry_up_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self._dry_up(Path(tmp) / "run")
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_dry_up_prints_expanded_launch_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(Path(tmp) / "run").stdout
            self.assertIn("python3.14 -m venv", out)
            self.assertIn("[api]' prometheus_client juniper-observability", out)
            self.assertIn("python -m juniper_data --host 127.0.0.1 --port 8101", out)
            self.assertIn("uvicorn api.app:create_app --factory --host 127.0.0.1 --port 8202", out)
            self.assertIn("JUNIPER_CANOPY_DEMO_MODE=0", out)
            self.assertIn("python main.py", out)

    def test_dry_up_prints_control_ws_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(Path(tmp) / "run").stdout
            self.assertIn("JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://127.0.0.1:8051", out)
            self.assertIn("JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://127.0.0.1:8051", out)

    def test_dry_up_uses_overridden_project_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(Path(tmp) / "run").stdout
            self.assertIn("/opt/juniper-e2e-fixture/juniper-data", out)
            self.assertIn("/opt/juniper-e2e-fixture/juniper-cascor/src", out)

    def test_dry_up_touches_nothing(self) -> None:
        # The scratch RUN_DIR must NOT be created by a dry-run (no mkdir, no venv).
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            self._dry_up(run_dir)
            self.assertFalse(run_dir.exists(), "dry-run --up must not create the scratch run dir")

    def test_dry_up_honors_port_and_extras_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(
                Path(tmp) / "run",
                env_extra={"JUNIPER_E2E_CANOPY_PORT": "9051", "JUNIPER_E2E_DATA_EXTRAS": "api,mnist"},
            ).stdout
            # canopy takes its port via JUNIPER_CANOPY_PORT (env), not a --port flag.
            self.assertIn("JUNIPER_CANOPY_PORT=9051", out)
            self.assertIn("[api,mnist]", out)
            # The WS pair must track the overridden canopy port on both ends.
            self.assertIn("JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://127.0.0.1:9051", out)


class TestDryRunDown(unittest.TestCase):
    """``--dry-run --down`` prints teardown commands and removes nothing."""

    def test_dry_down_exit_zero_and_prints_kill_and_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            result = _run(
                "--dry-run",
                "--down",
                env_extra={"JUNIPER_E2E_PROJECT_DIR": "/opt/juniper-e2e-fixture", "JUNIPER_E2E_RUN_DIR": str(run_dir)},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("stop juniper-canopy on 8051", result.stdout)
            self.assertIn("snapshot_*", result.stdout)
            self.assertFalse(run_dir.exists(), "dry-run --down must not create/remove anything on disk")


class TestActivateCondaNounset(unittest.TestCase):
    """``activate_conda`` must match plant's safe_conda_activate nounset contract.

    Regression: the restore arm was ``set +u`` (same as the pre-activate arm),
    so live ``--up`` continued with nounset disabled after every conda activate
    — masking unset-variable mistakes for the rest of cascor/canopy bring-up.
    """

    def _run_activate(self, conda_sh: Path) -> subprocess.CompletedProcess:
        # Concatenate (do not f-string) so bash `${...}` braces in the extract
        # are not interpreted as Python format fields.
        harness = (
            "set -euo pipefail\n"
            "log() { :; }\n"
            f'CONDA_SH="{conda_sh}"\n' + _extract_activate_conda_function() + 'activate_conda "JuniperCascor1"\n'
            "case $- in\n"
            '  *u*) echo "NOUNSET_ON" ;;\n'
            '  *) echo "NOUNSET_OFF"; exit 1 ;;\n'
            "esac\n"
            # Prove nounset is actually enforced (not just a stale $- flag bit).
            'if (echo "${__isolated_stack_definitely_unset__}") >/dev/null 2>&1; then\n'
            '  echo "NOUNSET_INEFFECTIVE"\n'
            "  exit 1\n"
            "fi\n"
            'echo "OK"\n'
        )
        return subprocess.run(
            ["/bin/bash", "-c", harness],
            capture_output=True,
            text=True,
            env=RedactedEnv(os.environ),
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )

    def test_restores_nounset_after_activate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conda_sh = Path(tmp) / "conda.sh"
            # Mimic plant's ADDR2LINE class: activate scripts reference unset vars.
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() {\n" '  if [[ "$1" == "activate" ]]; then\n' '    : "${ADDR2LINE}"\n' "  fi\n" "}\n")
            result = self._run_activate(conda_sh)
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("NOUNSET_ON", result.stdout)
            self.assertIn("OK", result.stdout)

    def test_missing_conda_sh_errors(self) -> None:
        harness = "set -euo pipefail\n" 'log() { echo "$*"; }\n' 'CONDA_SH="/nonexistent/conda.sh"\n' + _extract_activate_conda_function() + 'activate_conda "JuniperCascor1"\n'
        result = subprocess.run(
            ["/bin/bash", "-c", harness],
            capture_output=True,
            text=True,
            env=RedactedEnv(os.environ),
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conda not found", result.stdout + result.stderr)

    def test_restore_arm_is_set_minus_u(self) -> None:
        # Static pin: the pre/post pair must be +u then -u (not +u/+u).
        body = _extract_activate_conda_function()
        self.assertRegex(
            body,
            r"set \+u\n\s*conda activate[^\n]+\n\s*set -u\n",
            msg="activate_conda must restore nounset with set -u after conda activate",
        )


if __name__ == "__main__":
    unittest.main()
