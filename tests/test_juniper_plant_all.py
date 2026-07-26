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
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_plant_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 15


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


class TestSystemdModeBehavioral(unittest.TestCase):
    """Full-script PATH-stub coverage for the ``USE_SYSTEMD=1`` / ``--systemd`` branch.

    The systemd arm runs *before* preflight (no conda / nohup / pidfile), so a
    hermetic ``systemctl`` + ``curl`` + ``sleep`` stub PATH is enough. This is
    the only live exercise of start order, the missing-curl abort, the worker
    healthy-but-inactive WARNING, and the documented gap that ``cleanup_on_failure``
    does not ``systemctl stop`` units started in this mode (``STARTED_PIDS`` stays
    empty). Static text pins elsewhere only assert the worker health URL shape.
    """

    _EXPECTED_START_ORDER = (
        "juniper-data.service",
        "juniper-cascor.service",
        "juniper-canopy.service",
        "juniper-cascor-worker.service",
    )

    def _stage_stubs(
        self,
        root: Path,
        *,
        with_curl: bool = True,
        curl_exit: int = 0,
        is_active_exit: int = 0,
    ) -> tuple[Path, Path]:
        stub_bin = root / "path-stubs"
        stub_bin.mkdir(parents=True, exist_ok=True)
        systemctl_log = root / "systemctl.log"
        systemctl_log.write_text("")

        systemctl = stub_bin / "systemctl"
        systemctl.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f'printf "%s\\n" "$*" >>"{systemctl_log}"\n'
            'args=("$@")\n'
            'if [[ "${1:-}" == "--user" ]]; then shift; fi\n'
            'cmd="${1:-}"\n'
            'case "${cmd}" in\n'
            "  start) exit 0 ;;\n"
            f"  is-active) exit {is_active_exit} ;;\n"
            "  status) exit 0 ;;\n"
            "  stop) exit 0 ;;\n"
            "  *) exit 0 ;;\n"
            "esac\n"
        )
        systemctl.chmod(0o755)

        sleep = stub_bin / "sleep"
        sleep.write_text("#!/usr/bin/env bash\nexit 0\n")
        sleep.chmod(0o755)

        if with_curl:
            curl = stub_bin / "curl"
            curl.write_text(f"#!/usr/bin/env bash\nexit {curl_exit}\n")
            curl.chmod(0o755)

        return stub_bin, systemctl_log

    def _systemd_env(self, stub_bin: Path, *, include_usr_bin: bool = True) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        env["USE_SYSTEMD"] = "1"
        env["HEALTH_CHECK_TIMEOUT"] = "1"
        env["HEALTH_CHECK_INTERVAL"] = "1"
        env["JUNIPER_DATA_PORT"] = "65040"
        env["JUNIPER_CASCOR_PORT"] = "65041"
        env["JUNIPER_CANOPY_PORT"] = "65042"
        env["JUNIPER_WORKER_HEALTH_PORT"] = "65043"
        # Prefer stubs; keep a minimal host PATH for bash helpers when needed.
        # Missing-curl cases omit /usr/bin so a host curl cannot mask the gap.
        if include_usr_bin:
            env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"
        else:
            env["PATH"] = str(stub_bin) + os.pathsep + "/bin"
        return env

    def _run_plant(
        self,
        env: RedactedEnv,
        *,
        args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        cmd = ["/bin/bash", str(SCRIPT_PATH)]
        if args:
            cmd.extend(args)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )

    def _started_units(self, log: Path) -> list[str]:
        starts: list[str] = []
        for line in log.read_text().splitlines():
            parts = line.split()
            if "--user" in parts and "start" in parts:
                # ``systemctl --user start <unit>``
                try:
                    idx = parts.index("start")
                    starts.append(parts[idx + 1])
                except (ValueError, IndexError):
                    continue
        return starts

    def test_happy_path_starts_units_in_dependency_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_stubs(root)
            env = self._systemd_env(stub_bin)
            result = self._run_plant(env)
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertIn("Starting services via systemd", combined)
            self.assertIn("All Juniper services started via systemd", combined)
            self.assertNotIn("=== Pre-flight Checks ===", combined)
            self.assertNotIn("nohup", combined)
            starts = self._started_units(systemctl_log)
            self.assertEqual(starts, list(self._EXPECTED_START_ORDER))
            self.assertIn("http://localhost:65040/v1/health", combined)
            self.assertIn("http://127.0.0.1:65043/v1/health/ready", combined)

    def test_systemd_flag_enters_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_stubs(root)
            env = self._systemd_env(stub_bin)
            del env["USE_SYSTEMD"]
            result = self._run_plant(env, args=["--systemd"])
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertEqual(self._started_units(systemctl_log), list(self._EXPECTED_START_ORDER))

    def test_missing_curl_aborts_before_systemctl_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_stubs(root, with_curl=False)
            # This image ships curl in both /bin and /usr/bin, so a restricted
            # host PATH still finds it. Symlink only the early-script helpers
            # the launcher needs before the curl gate (no curl symlink).
            host_tools = root / "host-tools"
            host_tools.mkdir()
            for name in ("realpath", "basename", "dirname", "date"):
                for base in (Path("/usr/bin"), Path("/bin")):
                    src = base / name
                    if src.exists():
                        (host_tools / name).symlink_to(src)
                        break
            env = self._systemd_env(stub_bin, include_usr_bin=False)
            env["PATH"] = str(stub_bin) + os.pathsep + str(host_tools)
            result = self._run_plant(env)
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 1, msg=combined)
            self.assertIn("'curl' not found in PATH", combined)
            self.assertEqual(self._started_units(systemctl_log), [])
            self.assertNotIn("Starting juniper-data", combined)

    def test_worker_healthy_but_inactive_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_stubs(root, is_active_exit=1)
            env = self._systemd_env(stub_bin)
            result = self._run_plant(env)
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertIn(
                "WARNING: juniper-cascor-worker reports healthy but systemd unit not active",
                combined,
            )
            log_text = systemctl_log.read_text()
            self.assertIn("is-active juniper-cascor-worker.service", log_text)
            self.assertIn("status juniper-cascor-worker.service --no-pager", log_text)

    def test_health_timeout_does_not_systemctl_stop(self) -> None:
        """systemd starts are not tracked in STARTED_PIDS — cleanup cannot stop them.

        Pins the blast-radius gap: a mid-plant health failure still exits 1 via
        the ERR trap / cleanup_on_failure, but must not invent a ``systemctl stop``
        (operators must stop units manually / via chop --systemd).
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub_bin, systemctl_log = self._stage_stubs(root, curl_exit=22)
            env = self._systemd_env(stub_bin)
            result = self._run_plant(env)
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 1, msg=combined)
            self.assertIn("failed to become healthy within 1s", combined)
            self.assertIn("Cleaning up started Juniper Project services", combined)
            # data was started before the first health wait failed
            self.assertEqual(self._started_units(systemctl_log), ["juniper-data.service"])
            self.assertNotIn(" stop ", f" {systemctl_log.read_text()} ")


if __name__ == "__main__":
    unittest.main()
