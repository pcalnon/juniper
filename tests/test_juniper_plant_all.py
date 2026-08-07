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
- ``wait_for_health`` clamps a zero/invalid poll interval (avoids busy-loop).

Where possible, tests inspect the script as text — running the full script
under unittest is impractical because it source-activates conda, allocates
ports, and launches four long-lived background services. Pre-flight failure
smokes exercise the nohup path against a synthetic JUNIPER_PROJECT_DIR /
JUNIPER_CONDA_DIR layout. ``TestSystemdModeBehavioral`` is a separate
full-script PATH-stub lane for the pre-preflight ``USE_SYSTEMD=1`` arm.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "juniper_plant_all.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 15
CLEANUP_TIMEOUT_SECONDS = 20


def _extract_function(name: str) -> str:
    """Pull a live ``function <name>() { ... }`` body (avoids harness drift)."""
    match = re.search(
        rf"^function {re.escape(name)}\(\) \{{.*?\n\}}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"{name} function not found in juniper_plant_all.bash")
    return match.group(0)


def _extract_validate_conda_env() -> str:
    """Pull the live ``function validate_conda_env() { ... }`` body (no harness drift).

    Named distinctly from concurrent coverage PRs' generic ``_extract_function``
    helpers so a merge cannot silently alias the wrong extractor.
    """
    match = re.search(
        r"^function validate_conda_env\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("validate_conda_env function not found in juniper_plant_all.bash")
    return match.group(0)


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

    def _stage_cmd_stubs(self, root: Path) -> Path:
        """Stub ``curl`` + ``ss`` so preflight is hermetic without iproute2.

        Cloud / minimal images often lack ``ss``; without stubs the smoke
        cases abort at the command check and never reach the worker-binary
        / conda-env arms they intend to pin.
        """
        stub_bin = root / "path-stubs"
        stub_bin.mkdir(parents=True, exist_ok=True)
        for name in ("curl", "ss"):
            stub = stub_bin / name
            stub.write_text("#!/usr/bin/env bash\nexit 0\n")
            stub.chmod(0o755)
        return stub_bin

    def _preflight_env(self, *, project_dir: Path, conda_dir: Path, stub_bin: Path, ports: tuple[str, str, str, str]) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        env["JUNIPER_PROJECT_DIR"] = str(project_dir)
        env["JUNIPER_CONDA_DIR"] = str(conda_dir)
        env["JUNIPER_DATA_PORT"] = ports[0]
        env["JUNIPER_CASCOR_PORT"] = ports[1]
        env["JUNIPER_CANOPY_PORT"] = ports[2]
        env["JUNIPER_WORKER_HEALTH_PORT"] = ports[3]
        env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "") + os.pathsep + str(conda_dir / "envs" / "JuniperData" / "bin")
        return env

    def test_missing_worker_binary_aborts_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            conda_dir = root / "miniforge3"
            stub_bin = self._stage_cmd_stubs(root)

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

            env = self._preflight_env(
                project_dir=project_dir,
                conda_dir=conda_dir,
                stub_bin=stub_bin,
                ports=("65010", "65011", "65012", "65013"),
            )

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH)],
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
            stub_bin = self._stage_cmd_stubs(root)

            for sub in ("juniper-data", "juniper-cascor/src", "juniper-canopy/src", "juniper-cascor-worker"):
                (project_dir / sub).mkdir(parents=True, exist_ok=True)

            (conda_dir / "etc" / "profile.d").mkdir(parents=True, exist_ok=True)
            conda_sh = conda_dir / "etc" / "profile.d" / "conda.sh"
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() { :; }\n" "export -f conda\n")

            # Only JuniperData and JuniperCanopy1 exist; both cascor + worker
            # envs are absent.
            for env_name in ("JuniperData", "JuniperCanopy1"):
                self._make_env(conda_dir, env_name, with_worker_bin=False)

            env = self._preflight_env(
                project_dir=project_dir,
                conda_dir=conda_dir,
                stub_bin=stub_bin,
                ports=("65020", "65021", "65022", "65023"),
            )

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH)],
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
            stub_bin = self._stage_cmd_stubs(root)

            for sub in ("juniper-data", "juniper-cascor/src", "juniper-canopy/src", "juniper-cascor-worker"):
                (project_dir / sub).mkdir(parents=True, exist_ok=True)

            (conda_dir / "etc" / "profile.d").mkdir(parents=True, exist_ok=True)
            conda_sh = conda_dir / "etc" / "profile.d" / "conda.sh"
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() { :; }\n" "export -f conda\n")

            # Stage a non-default worker env name; validate_conda_env passes
            # for it but no worker binary exists.
            for env_name in ("JuniperData", "JuniperCascor1", "JuniperCanopy1", "CustomWorkerEnv"):
                self._make_env(conda_dir, env_name, with_worker_bin=False)

            env = self._preflight_env(
                project_dir=project_dir,
                conda_dir=conda_dir,
                stub_bin=stub_bin,
                ports=("65030", "65031", "65032", "65033"),
            )
            env["JUNIPER_WORKER_CONDA"] = "CustomWorkerEnv"

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH)],
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
        systemctl.write_text("#!/usr/bin/env bash\n" "set -euo pipefail\n" f'printf "%s\\n" "$*" >>"{systemctl_log}"\n' 'args=("$@")\n' 'if [[ "${1:-}" == "--user" ]]; then shift; fi\n' 'cmd="${1:-}"\n' 'case "${cmd}" in\n' "  start) exit 0 ;;\n" f"  is-active) exit {is_active_exit} ;;\n" "  status) exit 0 ;;\n" "  stop) exit 0 ;;\n" "  *) exit 0 ;;\n" "esac\n")
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


class TestCheckPortAvailable(unittest.TestCase):
    """Behavioral pins for ``check_port_available`` busy / ss-missing arms."""

    def _run_check(self, *, ss_script: str, port: str = "65099") -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            ss = bin_dir / "ss"
            ss.write_text("#!/usr/bin/env bash\n" + ss_script)
            ss.chmod(0o755)
            harness = f"""
                set -euo pipefail
                JUNIPER_SCRIPT_NAME="juniper_plant_all.bash"
                {_extract_function("check_port_available")}
                set +e
                check_port_available "{port}" "juniper-data"
                status=$?
                set -e
                echo "STATUS=${{status}}"
                exit 0
            """
            env = RedactedEnv(os.environ)
            # Stub bin first so ``ss`` is ours; keep /usr/bin for ``grep``.
            env["PATH"] = str(bin_dir) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_busy_port_returns_one(self) -> None:
        result = self._run_check(ss_script='echo "LISTEN 0 128 127.0.0.1:65099 0.0.0.0:*"\n')
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("Port 65099 is already in use", result.stdout)

    def test_free_port_returns_zero(self) -> None:
        result = self._run_check(ss_script='echo "LISTEN 0 128 127.0.0.1:1 0.0.0.0:*"\n')
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertIn("Port 65099 is available", result.stdout)

    def test_ss_missing_fail_open(self) -> None:
        # If ``ss`` is absent, the pipeline yields empty stdout and the helper
        # treats the port as free (fail-open). Pre-flight ``for cmd in curl ss``
        # is the real gate; this pins the helper's own degrade path.
        with tempfile.TemporaryDirectory() as tmp:
            empty_bin = Path(tmp) / "empty"
            empty_bin.mkdir()
            harness = f"""
                set -euo pipefail
                JUNIPER_SCRIPT_NAME="juniper_plant_all.bash"
                {_extract_function("check_port_available")}
                set +e
                check_port_available "65099" "juniper-data"
                status=$?
                set -e
                echo "STATUS=${{status}}"
                exit 0
            """
            env = RedactedEnv(os.environ)
            # Empty stub dir first — ``ss`` resolves as missing; keep grep.
            env["PATH"] = str(empty_bin) + os.pathsep + "/usr/bin:/bin"
            result = subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("STATUS=0", result.stdout)
            self.assertIn("Port 65099 is available", result.stdout)


class TestCleanupOnFailure(unittest.TestCase):
    """Behavioral pins for ``cleanup_on_failure`` (JR-ML-SEC-042).

    A mid-plant health failure must SIGTERM then SIGKILL every PID in
    ``STARTED_PIDS`` and remove the project pidfile — otherwise a partial
    plant leaves orphaned services that confuse the next chop/plant cycle.
    Extracted from the live script; ``sleep`` is stubbed so CI does not wait
    the production 3s settle (kill logic is what we pin).
    """

    def _spawn_detached(self, inner_bash: str) -> int:
        """Start a session-leader child reparented to init.

        ``cleanup_on_failure`` polls ``kill -0`` after SIGTERM/SIGKILL. If the
        test process remains the parent, a dead child stays a zombie and
        ``kill -0`` keeps succeeding — a false "survived SIGKILL". Launch
        under a short-lived ``setsid`` shell so init reaps the exit.
        """
        launcher = "setsid bash -c " + repr(inner_bash) + " </dev/null >/dev/null 2>&1 & echo $!"
        result = subprocess.run(
            ["/bin/bash", "-c", launcher],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        pid = int(result.stdout.strip().splitlines()[-1])
        time.sleep(0.15)
        self.assertTrue(Path(f"/proc/{pid}").exists(), f"detached pid {pid} missing")
        return pid

    def _force_kill(self, pid: int) -> None:
        for kill_target in (lambda: os.killpg(pid, signal.SIGKILL), lambda: os.kill(pid, signal.SIGKILL)):
            try:
                kill_target()
                break
            except ProcessLookupError:
                return
            except PermissionError:
                continue
        for _ in range(20):
            if not Path(f"/proc/{pid}").exists():
                return
            time.sleep(0.05)

    def _run_cleanup(self, pids: list[int], pid_file: Path) -> subprocess.CompletedProcess[str]:
        pid_array = " ".join(str(p) for p in pids)
        harness = f"""
            set -euo pipefail
            JUNIPER_SCRIPT_NAME="juniper_plant_all.bash"
            JUNIPER_PROJECT_PID_FILE="$1"
            STARTED_PIDS=({pid_array})
            # Production settles 3s between SIGTERM and SIGKILL; shorten for CI
            # but keep a real delay so cooperative children can exit before the
            # SIGKILL arm (a no-op sleep falsely escalates every PID).
            sleep() {{ command sleep 0.2; }}
            {_extract_function("cleanup_on_failure")}
            cleanup_on_failure
        """
        env = RedactedEnv(os.environ)
        return subprocess.run(
            ["/bin/bash", "-c", harness, "_", str(pid_file)],
            capture_output=True,
            text=True,
            env=env,
            timeout=CLEANUP_TIMEOUT_SECONDS,
        )

    def test_empty_started_pids_removes_pidfile_and_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pid_file = Path(tmp) / "JuniperProject.pid"
            pid_file.write_text("juniper-data=1\n")
            result = self._run_cleanup([], pid_file)
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Cleaning up started Juniper Project services", result.stdout)
            self.assertIn("Cleanup complete", result.stdout)
            self.assertFalse(pid_file.exists(), "pidfile must be removed on failure cleanup")

    def test_cooperative_process_stops_on_sigterm(self) -> None:
        pid = self._spawn_detached("exec sleep 60")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pid_file = Path(tmp) / "JuniperProject.pid"
                pid_file.write_text(f"juniper-data={pid}\n")
                result = self._run_cleanup([pid], pid_file)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn(f"Sending SIGTERM to PID {pid}", result.stdout)
                self.assertNotIn("Sending SIGKILL", result.stdout)
                self.assertFalse(pid_file.exists())
                self.assertFalse(Path(f"/proc/{pid}").exists())
        finally:
            self._force_kill(pid)

    def test_sigterm_ignore_escalates_to_sigkill(self) -> None:
        pid = self._spawn_detached("exec python3 -c 'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pid_file = Path(tmp) / "JuniperProject.pid"
                pid_file.write_text(f"juniper-cascor={pid}\n")
                result = self._run_cleanup([pid], pid_file)
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn(f"Sending SIGTERM to PID {pid}", result.stdout)
                self.assertIn(f"Sending SIGKILL to PID {pid}", result.stdout)
                self.assertFalse(pid_file.exists())
                self.assertFalse(Path(f"/proc/{pid}").exists())
        finally:
            self._force_kill(pid)

    def test_err_trap_and_started_pids_wire(self) -> None:
        # Drift guards: ERR trap + STARTED_PIDS append after each launch.
        self.assertIn("trap cleanup_on_failure ERR", SCRIPT_TEXT)
        self.assertIn('STARTED_PIDS+=("${JUNIPER_DATA_PID}")', SCRIPT_TEXT)
        self.assertIn('STARTED_PIDS+=("${JUNIPER_CASCOR_PID}")', SCRIPT_TEXT)
        self.assertIn('STARTED_PIDS+=("${JUNIPER_CANOPY_PID}")', SCRIPT_TEXT)
        self.assertIn('STARTED_PIDS+=("${JUNIPER_WORKER_PID}")', SCRIPT_TEXT)


class TestWaitForHealth(unittest.TestCase):
    """Behavioral pins for ``wait_for_health`` success / timeout arms."""

    def _run_wait(
        self,
        *,
        curl_script: str,
        timeout: int = 2,
        interval: int = 1,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            curl = bin_dir / "curl"
            curl.write_text("#!/usr/bin/env bash\n" + curl_script)
            curl.chmod(0o755)
            harness = f"""
                set -euo pipefail
                JUNIPER_SCRIPT_NAME="juniper_plant_all.bash"
                HEALTH_CHECK_TIMEOUT=60
                HEALTH_CHECK_INTERVAL=2
                # Stub settle sleeps; elapsed arithmetic still advances.
                sleep() {{ :; }}
                {_extract_function("wait_for_health")}
                set +e
                wait_for_health "juniper-data" "http://127.0.0.1:9/v1/health" "{timeout}" "{interval}"
                status=$?
                set -e
                echo "STATUS=${{status}}"
                exit 0
            """
            env = RedactedEnv(os.environ)
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_healthy_endpoint_returns_zero(self) -> None:
        result = self._run_wait(curl_script="exit 0\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertIn("juniper-data is healthy", result.stdout)

    def test_unhealthy_endpoint_times_out(self) -> None:
        result = self._run_wait(curl_script="exit 22\n", timeout=2, interval=1)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("failed to become healthy within 2s", result.stdout)


class TestWaitForHealthIntervalGuard(unittest.TestCase):
    """``HEALTH_CHECK_INTERVAL=0`` must not busy-loop forever.

    ``wait_for_health`` advances ``elapsed`` by ``interval`` each poll. A zero
    (or non-positive / non-numeric) interval leaves ``elapsed`` stuck at 0 while
    ``sleep 0`` returns immediately — an infinite curl hammer that never hits
    the timeout arm and leaves a partial plant hung until the operator kills it.
    """

    def _run_wait(self, *, interval: str, timeout: int = 2) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            curl = bin_dir / "curl"
            curl.write_text("#!/usr/bin/env bash\nexit 22\n")
            curl.chmod(0o755)
            harness = f"""
                set -euo pipefail
                JUNIPER_SCRIPT_NAME="juniper_plant_all.bash"
                HEALTH_CHECK_TIMEOUT=60
                HEALTH_CHECK_INTERVAL=2
                # Stub settle sleeps; elapsed arithmetic still advances.
                sleep() {{ :; }}
                {_extract_function("wait_for_health")}
                set +e
                wait_for_health "juniper-data" "http://127.0.0.1:9/v1/health" "{timeout}" "{interval}"
                status=$?
                set -e
                echo "STATUS=${{status}}"
                exit 0
            """
            env = RedactedEnv(os.environ)
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_zero_interval_clamps_and_times_out(self) -> None:
        result = self._run_wait(interval="0", timeout=2)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("clamping to 1s", result.stdout)
        self.assertIn("failed to become healthy within 2s", result.stdout)

    def test_non_numeric_interval_clamps_and_times_out(self) -> None:
        result = self._run_wait(interval="fast", timeout=2)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("clamping to 1s", result.stdout)


class TestValidateCondaEnv(unittest.TestCase):
    """Behavioral pins for ``validate_conda_env`` missing-dir / non-exec arms.

    Preflight smoke stages every env with an executable stub ``python`` so it
    never reaches the ``! -x`` arm. A broken or non-executable ``bin/python``
    would otherwise let plant proceed into conda activate / launch against a
    dead env — large blast radius across all four services.
    """

    def _run_validate(self, *, stage) -> subprocess.CompletedProcess:
        """Run extracted ``validate_conda_env`` against a synthetic conda tree.

        ``stage(conda_dir)`` prepares ``envs/<name>/...`` under the temp root.
        """
        with tempfile.TemporaryDirectory() as tmp:
            conda_dir = Path(tmp) / "miniforge3"
            conda_dir.mkdir()
            env_name = stage(conda_dir)
            harness = f"""
                set -euo pipefail
                JUNIPER_SCRIPT_NAME="juniper_plant_all.bash"
                JUNIPER_CONDA_DIR="$1"
                {_extract_validate_conda_env()}
                set +e
                validate_conda_env "{env_name}"
                status=$?
                set -e
                echo "STATUS=${{status}}"
                exit 0
            """
            env = RedactedEnv(os.environ)
            return subprocess.run(
                ["/bin/bash", "-c", harness, "_", str(conda_dir)],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_missing_env_directory_returns_one(self) -> None:
        def stage(conda_dir: Path) -> str:
            (conda_dir / "envs").mkdir()
            return "MissingEnv"

        result = self._run_validate(stage=stage)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("Conda environment 'MissingEnv' not found", result.stdout)
        self.assertNotIn("Python binary not found", result.stdout)

    def test_missing_python_binary_returns_one(self) -> None:
        def stage(conda_dir: Path) -> str:
            (conda_dir / "envs" / "BrokenEnv" / "bin").mkdir(parents=True)
            return "BrokenEnv"

        result = self._run_validate(stage=stage)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("Python binary not found or not executable", result.stdout)
        self.assertIn("envs/BrokenEnv/bin/python", result.stdout)

    def test_non_executable_python_returns_one(self) -> None:
        def stage(conda_dir: Path) -> str:
            bin_dir = conda_dir / "envs" / "NonExecEnv" / "bin"
            bin_dir.mkdir(parents=True)
            python = bin_dir / "python"
            python.write_text("#!/usr/bin/env bash\nexit 0\n")
            python.chmod(0o644)  # present but not executable — the ! -x arm
            return "NonExecEnv"

        result = self._run_validate(stage=stage)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("Python binary not found or not executable", result.stdout)
        self.assertIn("envs/NonExecEnv/bin/python", result.stdout)

    def test_executable_python_returns_zero(self) -> None:
        def stage(conda_dir: Path) -> str:
            bin_dir = conda_dir / "envs" / "GoodEnv" / "bin"
            bin_dir.mkdir(parents=True)
            python = bin_dir / "python"
            python.write_text("#!/usr/bin/env bash\nexit 0\n")
            python.chmod(0o755)
            return "GoodEnv"

        result = self._run_validate(stage=stage)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertIn("Conda environment 'GoodEnv' validated", result.stdout)

    def test_preflight_validates_all_four_envs(self) -> None:
        # Drift guard: plant must validate data/cascor/canopy/worker, not just worker.
        self.assertIn('validate_conda_env "${JUNIPER_DATA_CONDA}"', SCRIPT_TEXT)
        self.assertIn('validate_conda_env "${JUNIPER_CASCOR_CONDA}"', SCRIPT_TEXT)
        self.assertIn('validate_conda_env "${JUNIPER_CANOPY_CONDA}"', SCRIPT_TEXT)
        self.assertIn('validate_conda_env "${JUNIPER_WORKER_CONDA}"', SCRIPT_TEXT)


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

    def test_conda_activate_failure_propagates_under_or_list(self) -> None:
        """OR-list callers must still see activate failure (not a masked exit 0).

        Bash disables ``set -e`` inside a function invoked as ``fn || …``. A
        trailing successful ``set -u`` must not mask ``conda activate`` failure
        and let the next host service launch on the ambient PATH (same class as
        isolated-stack #967 / experiment_stack OR-list absorb).
        """
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            conda = bin_dir / "conda"
            conda.write_text("#!/bin/bash\n" 'if [[ "$1" == "activate" ]]; then\n' "  exit 1\n" "fi\n")
            conda.chmod(0o755)
            harness = "set -euo pipefail\n" f'export PATH="{bin_dir}:/usr/bin:/bin"\n' + _extract_safe_conda_activate() + "failed=0\n" + 'safe_conda_activate "JuniperCanopy1" || failed=1\n' + 'echo "failed=${failed}"\n' + "if (( failed != 1 )); then exit 2; fi\n"
            result = subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=RedactedEnv(os.environ),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("failed=1", result.stdout)
            self.assertIn("conda activate", result.stdout + result.stderr)

    def test_restore_arm_is_set_minus_u(self) -> None:
        # Static pin: every activate path must restore nounset (not +u/+u).
        # Success and failure arms both end in ``set -u`` before return/fallthrough.
        body = _extract_safe_conda_activate()
        self.assertIn("set +u", body)
        self.assertRegex(
            body,
            r"if ! conda activate[^\n]+; then\n\s*set -u\n",
            msg="safe_conda_activate failure arm must restore set -u before return 1",
        )
        self.assertRegex(
            body,
            r"fi\n\s*set -u\n\}\n",
            msg="safe_conda_activate success arm must restore set -u after conda activate",
        )
