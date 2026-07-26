"""
Tests for util/juniper_plant_all.bash

Validates the script-level invariants introduced in the 2026-05-07 audit:

- Default conda env for juniper-canopy is JuniperCanopy1 (LIBTORCH-isolated).
- Worker process receives canonical CASCOR_* env vars at launch.
- Worker health is probed via /v1/health/ready (not the prior 2-second kill -0).
- Canopy receives canonical pydantic-prefixed env vars (NOT the deprecated
  CASCOR_SERVICE_URL legacy alias).
- Pre-flight aborts if the juniper-cascor-worker binary is missing from the
  JuniperCascor conda env.

Where possible, tests inspect the script as text — running the full script
under unittest is impractical because it source-activates conda, allocates
ports, and launches four long-lived background services. The single
end-to-end smoke test exercises only the pre-flight failure path against a
synthetic JUNIPER_PROJECT_DIR / JUNIPER_CONDA_DIR layout, asserting the
script exits before any service is launched.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_plant_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 15


def _extract_safe_conda_activate() -> str:
    """Pull the live ``safe_conda_activate`` body (avoids harness drift)."""
    live = SCRIPT_PATH.read_text()
    match = re.search(
        r"^safe_conda_activate\(\) \{.*?\n\}\n",
        live,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("safe_conda_activate function not found in juniper_plant_all.bash")
    return match.group(0)


class TestSyntax(unittest.TestCase):
    """The script must pass `bash -n` cleanly."""

    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestCanopyEnvDefault(unittest.TestCase):
    """Audit fix #2 — canopy conda env defaults to JuniperCanopy1."""

    def test_canopy_conda_default_is_juniper_canopy_1(self) -> None:
        # The default must be JuniperCanopy1 (LIBTORCH-strip activate hook),
        # but still respect a caller-provided JUNIPER_CANOPY_CONDA override.
        self.assertIn(
            'JUNIPER_CANOPY_CONDA="${JUNIPER_CANOPY_CONDA:-JuniperCanopy1}"',
            SCRIPT_TEXT,
        )

    def test_old_unconditional_juniper_canopy_default_removed(self) -> None:
        # The prior unconditional `JUNIPER_CANOPY_CONDA="JuniperCanopy"` must
        # not still be present (would override the new default unconditionally).
        self.assertNotIn(
            'JUNIPER_CANOPY_CONDA="JuniperCanopy"\n',
            SCRIPT_TEXT,
        )


class TestWorkerEnvWiring(unittest.TestCase):
    """Audit fix #1 — worker invocation exports CASCOR_SERVER_URL etc."""

    def test_cascor_server_url_default_is_derived(self) -> None:
        # JUNIPER_WORKER_SERVER_URL must default to a ws:// URL pointing at the
        # cascor host:port pair, but accept a CASCOR_SERVER_URL override.
        self.assertIn(
            'JUNIPER_WORKER_SERVER_URL="${CASCOR_SERVER_URL:-ws://${JUNIPER_CASCOR_HOST}:${JUNIPER_CASCOR_PORT}/ws/v1/workers}"',
            SCRIPT_TEXT,
        )

    def test_worker_invocation_exports_cascor_server_url(self) -> None:
        # The actual nohup line must front-load CASCOR_SERVER_URL.
        self.assertIn(
            'CASCOR_SERVER_URL="${JUNIPER_WORKER_SERVER_URL}"',
            SCRIPT_TEXT,
        )

    def test_worker_invocation_passes_health_port_and_bind(self) -> None:
        self.assertIn(
            'CASCOR_WORKER_HEALTH_PORT="${JUNIPER_WORKER_HEALTH_PORT}"',
            SCRIPT_TEXT,
        )
        self.assertIn(
            'CASCOR_WORKER_HEALTH_BIND="${JUNIPER_WORKER_HEALTH_HOST}"',
            SCRIPT_TEXT,
        )

    def test_worker_invocation_forwards_optional_auth_token(self) -> None:
        self.assertIn(
            'CASCOR_AUTH_TOKEN="${CASCOR_AUTH_TOKEN:-}"',
            SCRIPT_TEXT,
        )


class TestWorkerHealthProbe(unittest.TestCase):
    """Audit fix #5 — worker health probed via /v1/health/ready."""

    def test_health_url_uses_ready_endpoint(self) -> None:
        self.assertIn(
            'JUNIPER_WORKER_HEALTH_URL="http://${JUNIPER_WORKER_HEALTH_HOST}:${JUNIPER_WORKER_HEALTH_PORT}/v1/health/ready"',
            SCRIPT_TEXT,
        )

    def test_wait_for_health_called_for_worker(self) -> None:
        # Both the nohup and systemd code paths must probe /v1/health/ready.
        nohup_call = 'wait_for_health "juniper-cascor-worker" "${JUNIPER_WORKER_HEALTH_URL}"'
        systemd_call = 'wait_for_health "juniper-cascor-worker" ' '"http://${JUNIPER_WORKER_HEALTH_HOST}:${JUNIPER_WORKER_HEALTH_PORT}/v1/health/ready"'
        self.assertIn(nohup_call, SCRIPT_TEXT)
        self.assertIn(systemd_call, SCRIPT_TEXT)

    def test_legacy_kill_dash_zero_check_removed(self) -> None:
        # The 2-second `kill -0 "${JUNIPER_WORKER_PID}"` warning-only check
        # must have been replaced; the BROKEN-behavior comment is the smoking gun.
        self.assertNotIn(
            "Worker has no HTTP health endpoint",
            SCRIPT_TEXT,
        )
        self.assertNotIn(
            "WARNING: juniper-cascor-worker process exited immediately",
            SCRIPT_TEXT,
        )


class TestCanopyEnvVarRename(unittest.TestCase):
    """Audit fix #3 — canopy uses canonical pydantic-prefixed names."""

    def test_canonical_cascor_service_url_used(self) -> None:
        self.assertIn(
            'JUNIPER_CANOPY_CASCOR_SERVICE_URL="${JUNIPER_CASCOR_URL}"',
            SCRIPT_TEXT,
        )

    def test_canonical_juniper_data_url_used(self) -> None:
        self.assertIn(
            'JUNIPER_CANOPY_JUNIPER_DATA_URL="${JUNIPER_DATA_URL_FOR_CANOPY}"',
            SCRIPT_TEXT,
        )

    def test_legacy_cascor_service_url_removed(self) -> None:
        # The legacy plain CASCOR_SERVICE_URL=... assignment on the canopy
        # nohup line must no longer be present.
        legacy_line = 'CASCOR_SERVICE_URL="${JUNIPER_CASCOR_URL}" ' 'nohup "${JUNIPER_CANOPY_PYTHON}"'
        self.assertNotIn(legacy_line, SCRIPT_TEXT)


class TestPreflightChecks(unittest.TestCase):
    """Audit fix #6 — pre-flight validates worker env + binary."""

    def test_worker_conda_env_validated(self) -> None:
        self.assertIn(
            'validate_conda_env "${JUNIPER_WORKER_CONDA}"',
            SCRIPT_TEXT,
        )

    def test_worker_binary_executable_check(self) -> None:
        self.assertIn(
            '[[ ! -x "${JUNIPER_WORKER_BIN}" ]]',
            SCRIPT_TEXT,
        )

    def test_worker_health_port_availability_checked(self) -> None:
        self.assertIn(
            'check_port_available "${JUNIPER_WORKER_HEALTH_PORT}"',
            SCRIPT_TEXT,
        )


class TestPreflightFailureSmoke(unittest.TestCase):
    """End-to-end: missing worker binary aborts pre-flight before any launch.

    Builds a synthetic JUNIPER_PROJECT_DIR / JUNIPER_CONDA_DIR layout where:
      - All required conda envs exist with stub `python` binaries (so
        validate_conda_env passes for JuniperData, JuniperCascor1, and
        JuniperCanopy1 — the post-2026-05-07 defaults).
      - JuniperCascor1 (which is also the worker's default env per
        JUNIPER_WORKER_CONDA) is missing the `juniper-cascor-worker` binary.
    Asserts the script fails with the pre-flight error message and the
    expected non-zero exit code, without touching any service ports.
    """

    def _make_env(self, root: Path, name: str, with_worker_bin: bool) -> None:
        env_bin = root / "envs" / name / "bin"
        env_bin.mkdir(parents=True, exist_ok=True)
        python = env_bin / "python"
        python.write_text("#!/usr/bin/env bash\nexit 0\n")
        python.chmod(0o755)
        if with_worker_bin:
            worker_bin = env_bin / "juniper-cascor-worker"
            worker_bin.write_text("#!/usr/bin/env bash\nexit 0\n")
            worker_bin.chmod(0o755)

    def test_missing_worker_binary_aborts_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            conda_dir = root / "miniforge3"

            for sub in ("juniper-data", "juniper-cascor/src", "juniper-canopy/src", "juniper-cascor-worker"):
                (project_dir / sub).mkdir(parents=True, exist_ok=True)

            (conda_dir / "etc" / "profile.d").mkdir(parents=True, exist_ok=True)
            conda_sh = conda_dir / "etc" / "profile.d" / "conda.sh"
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() { :; }\n" "export -f conda\n")

            # Post-2026-05-07: JuniperCascor1 is the unified server+worker env
            # (legacy JuniperCascor deprecated). The worker binary is omitted
            # from JuniperCascor1's bin/ to exercise the missing-binary path.
            for env_name, with_bin in (
                ("JuniperData", False),
                ("JuniperCascor1", False),  # <-- no worker binary; also cascor server env
                ("JuniperCanopy1", False),
            ):
                self._make_env(conda_dir, env_name, with_worker_bin=with_bin)

            env = RedactedEnv(os.environ)
            env["JUNIPER_PROJECT_DIR"] = str(project_dir)
            env["JUNIPER_CONDA_DIR"] = str(conda_dir)
            env["JUNIPER_DATA_PORT"] = "65010"
            env["JUNIPER_CASCOR_PORT"] = "65011"
            env["JUNIPER_CANOPY_PORT"] = "65012"
            env["JUNIPER_WORKER_HEALTH_PORT"] = "65013"
            env["PATH"] = env.get("PATH", "") + os.pathsep + str(conda_dir / "envs" / "JuniperData" / "bin")

            result = subprocess.run(
                ["bash", str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("juniper-cascor-worker binary not found", combined)
            # Must abort BEFORE any service launch — no worker URL or health probe should appear.
            self.assertNotIn("Starting juniper-cascor-worker", combined)

    def test_missing_worker_conda_env_aborts_preflight(self) -> None:
        """Regression: if JUNIPER_WORKER_CONDA env doesn't exist, abort with
        a conda-env error before reaching the worker-binary check.

        This pins the failure mode the original (now-fixed) test was
        accidentally hitting — guarding against future env-name drift between
        the script defaults and this test fixture.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            conda_dir = root / "miniforge3"

            for sub in ("juniper-data", "juniper-cascor/src", "juniper-canopy/src", "juniper-cascor-worker"):
                (project_dir / sub).mkdir(parents=True, exist_ok=True)

            (conda_dir / "etc" / "profile.d").mkdir(parents=True, exist_ok=True)
            conda_sh = conda_dir / "etc" / "profile.d" / "conda.sh"
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() { :; }\n" "export -f conda\n")

            # Only JuniperData and JuniperCanopy1 exist; both cascor + worker
            # envs are absent.
            for env_name in ("JuniperData", "JuniperCanopy1"):
                self._make_env(conda_dir, env_name, with_worker_bin=False)

            env = RedactedEnv(os.environ)
            env["JUNIPER_PROJECT_DIR"] = str(project_dir)
            env["JUNIPER_CONDA_DIR"] = str(conda_dir)
            env["JUNIPER_DATA_PORT"] = "65020"
            env["JUNIPER_CASCOR_PORT"] = "65021"
            env["JUNIPER_CANOPY_PORT"] = "65022"
            env["JUNIPER_WORKER_HEALTH_PORT"] = "65023"
            env["PATH"] = env.get("PATH", "") + os.pathsep + str(conda_dir / "envs" / "JuniperData" / "bin")

            result = subprocess.run(
                ["bash", str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Conda environment 'JuniperCascor1' not found", combined)
            self.assertNotIn("Starting juniper-cascor-worker", combined)

    def test_worker_binary_check_uses_overridden_worker_conda(self) -> None:
        """JUNIPER_WORKER_CONDA override is honored by the binary check.

        Guards against the binary-check path silently using a different env
        than validate_conda_env does.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            conda_dir = root / "miniforge3"

            for sub in ("juniper-data", "juniper-cascor/src", "juniper-canopy/src", "juniper-cascor-worker"):
                (project_dir / sub).mkdir(parents=True, exist_ok=True)

            (conda_dir / "etc" / "profile.d").mkdir(parents=True, exist_ok=True)
            conda_sh = conda_dir / "etc" / "profile.d" / "conda.sh"
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() { :; }\n" "export -f conda\n")

            # Stage a non-default worker env name; validate_conda_env passes
            # for it but no worker binary exists.
            for env_name in ("JuniperData", "JuniperCascor1", "JuniperCanopy1", "CustomWorkerEnv"):
                self._make_env(conda_dir, env_name, with_worker_bin=False)

            env = RedactedEnv(os.environ)
            env["JUNIPER_PROJECT_DIR"] = str(project_dir)
            env["JUNIPER_CONDA_DIR"] = str(conda_dir)
            env["JUNIPER_WORKER_CONDA"] = "CustomWorkerEnv"
            env["JUNIPER_DATA_PORT"] = "65030"
            env["JUNIPER_CASCOR_PORT"] = "65031"
            env["JUNIPER_CANOPY_PORT"] = "65032"
            env["JUNIPER_WORKER_HEALTH_PORT"] = "65033"
            env["PATH"] = env.get("PATH", "") + os.pathsep + str(conda_dir / "envs" / "JuniperData" / "bin")

            result = subprocess.run(
                ["bash", str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("juniper-cascor-worker binary not found", combined)
            self.assertIn("envs/CustomWorkerEnv/bin/juniper-cascor-worker", combined)


class TestEnvOverridesDocumented(unittest.TestCase):
    """The script docstring must list the new env-var overrides."""

    def test_canopy_conda_documented(self) -> None:
        self.assertIn("JUNIPER_CANOPY_CONDA", SCRIPT_TEXT)

    def test_worker_health_overrides_documented(self) -> None:
        self.assertIn("JUNIPER_WORKER_HEALTH_HOST", SCRIPT_TEXT)
        self.assertIn("JUNIPER_WORKER_HEALTH_PORT", SCRIPT_TEXT)

    def test_cascor_auth_token_documented(self) -> None:
        self.assertIn("CASCOR_AUTH_TOKEN", SCRIPT_TEXT)

    def test_data_host_documented(self) -> None:
        # Pass 2 fix #7 + #9 — JUNIPER_DATA_HOST is a documented override.
        self.assertIn("JUNIPER_DATA_HOST", SCRIPT_TEXT)

    def test_canopy_cascor_ws_origin_documented(self) -> None:
        # 2026-07-09 training-start diagnosis §4.3 — the control-WS Origin
        # override is a documented env var.
        self.assertIn("JUNIPER_CANOPY_CASCOR_WS_ORIGIN", SCRIPT_TEXT)


class TestDataHostHonorsOverride(unittest.TestCase):
    """Audit fix #7 + #9 — JUNIPER_DATA_HOST respects caller value."""

    def test_data_host_uses_default_expansion(self) -> None:
        # SEC-F28: default is loopback (juniper-data has no bind guard); the
        # ``${JUNIPER_DATA_HOST:-...}`` form still honors a caller override.
        self.assertIn(
            'JUNIPER_DATA_HOST="${JUNIPER_DATA_HOST:-127.0.0.1}"',
            SCRIPT_TEXT,
        )

    def test_legacy_unconditional_data_host_removed(self) -> None:
        # The prior `JUNIPER_DATA_HOST="0.0.0.0"` (unconditional, ignored
        # caller value) must not still be present.
        self.assertNotIn(
            'JUNIPER_DATA_HOST="0.0.0.0"\n',
            SCRIPT_TEXT,
        )


class TestUvicornPreflightDeferred(unittest.TestCase):
    """Audit fix #8 — uvicorn dropped from global pre-flight."""

    def test_uvicorn_not_in_command_check_loop(self) -> None:
        # The for-loop that checks required commands must no longer include
        # uvicorn (which lives inside conda envs, not the launcher PATH).
        self.assertNotIn("for cmd in curl ss uvicorn", SCRIPT_TEXT)
        self.assertIn("for cmd in curl ss", SCRIPT_TEXT)


class TestCascorHostExported(unittest.TestCase):
    """Audit fix #4 — JUNIPER_CASCOR_HOST exported to cascor process."""

    def test_cascor_invocation_exports_host(self) -> None:
        # The nohup line for cascor must front-load JUNIPER_CASCOR_HOST.
        self.assertIn(
            'JUNIPER_CASCOR_HOST="${JUNIPER_CASCOR_HOST}"',
            SCRIPT_TEXT,
        )


class TestCanopyWsOriginExported(unittest.TestCase):
    """2026-07-09 training-start diagnosis §4.3 — canopy must be launched with
    a control-WS Origin cascor's localhost allowlist accepts.

    Canopy's built-in default derives from socket.gethostname(), which cascor's
    ``/ws/control`` Origin allowlist (localhost forms only by default) rejects
    with 403 on host-mode dev — a permanent 30s reconnect loop that also kills
    hot set_params over WS. juniper-deploy pre-aligns both ends for compose;
    this launcher owns the host-mode alignment.
    """

    def test_ws_origin_default_is_localhost_and_overridable(self) -> None:
        # Default tracks JUNIPER_CANOPY_PORT and honors a caller override.
        self.assertIn(
            'JUNIPER_CANOPY_CASCOR_WS_ORIGIN="${JUNIPER_CANOPY_CASCOR_WS_ORIGIN:-http://localhost:${JUNIPER_CANOPY_PORT}}"',
            SCRIPT_TEXT,
        )

    def test_canopy_invocation_exports_ws_origin(self) -> None:
        # The nohup launch line must front-load the Origin env var.
        self.assertIn(
            'JUNIPER_CANOPY_CASCOR_WS_ORIGIN="${JUNIPER_CANOPY_CASCOR_WS_ORIGIN}"',
            SCRIPT_TEXT,
        )


class TestPidFileFormat(unittest.TestCase):
    """Audit fix #10 — pid file written as `name=pid`."""

    def test_pid_file_uses_equals_format(self) -> None:
        self.assertIn('echo "juniper-data=${JUNIPER_DATA_PID}"', SCRIPT_TEXT)
        self.assertIn('echo "juniper-cascor=${JUNIPER_CASCOR_PID}"', SCRIPT_TEXT)
        self.assertIn('echo "juniper-canopy=${JUNIPER_CANOPY_PID}"', SCRIPT_TEXT)
        self.assertIn(
            'echo "juniper-cascor-worker=${JUNIPER_WORKER_PID}"',
            SCRIPT_TEXT,
        )

    def test_legacy_colon_format_removed_from_writer(self) -> None:
        # Plant must not still emit the legacy "name: pid" format.
        self.assertNotIn('echo "juniper-data:', SCRIPT_TEXT)
        self.assertNotIn('echo "juniper-cascor:', SCRIPT_TEXT)


class TestSafeCondaActivate(unittest.TestCase):
    """``safe_conda_activate`` nounset contract (ADDR2LINE class).

    Conda activate scripts (e.g. activate-binutils_linux-64.sh) reference
    unset vars like ADDR2LINE. The wrapper must disable nounset for the
    activate call only and restore it afterward — the same one-character
    ``set +u``/``set -u`` restore bug that bit isolated-stack (#785). Host-mode
    plant calls this before every service; a broken restore silently disables
    ``set -u`` for the rest of bring-up.
    """

    def _run_activate(self, bin_dir: Path) -> subprocess.CompletedProcess:
        # Concatenate (do not f-string) so bash `${...}` braces in the extract
        # are not interpreted as Python format fields.
        harness = (
            "set -euo pipefail\n"
            f'export PATH="{bin_dir}:/usr/bin:/bin"\n' + _extract_safe_conda_activate() + 'safe_conda_activate "JuniperCanopy1"\n'
            "case $- in\n"
            '  *u*) echo "NOUNSET_ON" ;;\n'
            '  *) echo "NOUNSET_OFF"; exit 1 ;;\n'
            "esac\n"
            # Prove nounset is actually enforced (not just a stale $- flag bit).
            'if (echo "${__plant_safe_conda_definitely_unset__}") >/dev/null 2>&1; then\n'
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
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            conda = bin_dir / "conda"
            # Mimic ADDR2LINE class: activate scripts reference unset vars.
            conda.write_text("#!/bin/bash\n" 'if [[ "$1" == "activate" ]]; then\n' '  : "${ADDR2LINE}"\n' "fi\n")
            conda.chmod(0o755)
            result = self._run_activate(bin_dir)
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("NOUNSET_ON", result.stdout)
            self.assertIn("OK", result.stdout)

    def test_restore_arm_is_set_minus_u(self) -> None:
        # Static pin: the pre/post pair must be +u then -u (not +u/+u).
        body = _extract_safe_conda_activate()
        self.assertRegex(
            body,
            r"set \+u\n\s*conda activate[^\n]+\n\s*set -u\n",
            msg="safe_conda_activate must restore nounset with set -u after conda activate",
        )


if __name__ == "__main__":
    unittest.main()
