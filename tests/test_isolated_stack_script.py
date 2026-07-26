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
- ``data_up`` live compose (hermetic ``python3.14`` / ``pip`` / ``curl`` stubs)
  — venv create, editable install, ``PYTHON_GIL=0`` nohup launch, pid write,
  and health gate. Orthogonal to open coverage on ``activate_conda`` /
  ``port_pid`` / ``wait_for_health`` helpers.

``--dry-run`` short-circuits before any filesystem or process side effect, so
those behavioural tests are fully hermetic — no real repos, conda, or network.
``JUNIPER_E2E_PROJECT_DIR`` / ``JUNIPER_E2E_RUN_DIR`` pin paths deterministically.
The ``data_up`` cases extract the live function body and stub tools on ``PATH``
(keep ``/usr/bin:/bin`` for ``nohup`` / ``sleep`` / coreutils).
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

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "isolated_stack.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 15
# data_up launches a short-lived stubbed nohup child; keep headroom for mkdir/pip/health.
DATA_UP_TIMEOUT_SECONDS = 25


def _extract_data_up_fn(name: str) -> str:
    """Pull a live ``<name>() { ... }`` body for ``data_up`` harnesses.

    Named distinctly from concurrent coverage PRs' generic ``_extract_function``
    / health-specific extractors so a merge cannot silently alias the wrong helper.
    """
    match = re.search(
        rf"^{re.escape(name)}\(\) \{{.*?\n\}}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"{name} function not found in isolated_stack.bash")
    return match.group(0)


def _run(*args: str, env_extra: "dict[str, str] | None" = None) -> subprocess.CompletedProcess:
    env = RedactedEnv(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["/bin/bash", str(SCRIPT_PATH), *args],
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


class TestDataUpLive(unittest.TestCase):
    """Behavioral pins for live ``data_up`` compose (venv / install / pid / GIL).

    ``data_up`` is the only dedicated-venv bring-up for the isolated E2E trio. A
    regression that skips venv create, drops ``PYTHON_GIL=0``, forgets the pid
    file, or bypasses the health gate leaves checklist runs pointing at a dead
    or free-threaded-wrong data service. Extracted from the live script with
    PATH-stubbed ``python3.14`` / ``curl`` — no real python3.14, pip, or network.
    Orthogonal to open #785 (activate_conda), #786 (port_pid/stop_port), #793
    (wait_for_health/probe_health helpers).
    """

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

    def _write_python314_stub(self, bin_dir: Path, marker_dir: Path) -> None:
        """Stub ``python3.14 -m venv DEST`` that builds a minimal activatable venv."""
        # The stub's body is a shell script written to disk; marker_dir is interpolated.
        stub = bin_dir / "python3.14"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [[ "${1:-}" != "-m" || "${2:-}" != "venv" || -z "${3:-}" ]]; then\n'
            '  echo "unexpected python3.14 invocation: $*" >&2\n'
            "  exit 2\n"
            "fi\n"
            'dest="$3"\n'
            f'marker_dir="{marker_dir}"\n'
            'mkdir -p "$dest/bin"\n'
            'printf "VENV_CREATED:%s\\n" "$dest" >>"$marker_dir/venv.log"\n'
            # activate: put this venv's bin first; provide deactivate for data_up.
            "cat >\"$dest/bin/activate\" <<ACT\n"
            "_OLD_VIRTUAL_PATH=\"\\$PATH\"\n"
            "VIRTUAL_ENV=\"$dest\"\n"
            "export VIRTUAL_ENV\n"
            "PATH=\"\\$VIRTUAL_ENV/bin:\\$PATH\"\n"
            "export PATH\n"
            "deactivate() {\n"
            "  PATH=\"\\$_OLD_VIRTUAL_PATH\"\n"
            "  export PATH\n"
            "  unset VIRTUAL_ENV\n"
            "  unset -f deactivate 2>/dev/null || true\n"
            "}\n"
            "ACT\n"
            # pip: record install argv (editable + extras + metrics deps).
            "cat >\"$dest/bin/pip\" <<'PIP'\n"
            "#!/usr/bin/env bash\n"
            f'printf "%s\\n" "$@" >>"{marker_dir}/pip.log"\n'
            "exit 0\n"
            "PIP\n"
            # python: record PYTHON_GIL + argv, then sleep so the pidfile stays live.
            "cat >\"$dest/bin/python\" <<'PY'\n"
            "#!/usr/bin/env bash\n"
            f'printf "PYTHON_GIL=%s\\n" "${{PYTHON_GIL-}}" >"{marker_dir}/python.env"\n'
            f'printf "%s\\n" "$@" >"{marker_dir}/python.args"\n'
            "exec sleep 60\n"
            "PY\n"
            'chmod 755 "$dest/bin/pip" "$dest/bin/python"\n'
        )
        stub.chmod(0o755)

    def _write_curl_ok(self, bin_dir: Path) -> None:
        curl = bin_dir / "curl"
        curl.write_text("#!/usr/bin/env bash\nexit 0\n")
        curl.chmod(0o755)

    def _run_data_up(
        self,
        *,
        run_dir: Path,
        data_dir: Path,
        marker_dir: Path,
        bin_dir: Path,
        data_extras: str = "api",
        data_port: str = "65301",
        path: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        # Concatenate (do not f-string) so bash `${...}` braces in the extract
        # are not interpreted as Python format fields.
        harness = (
            "set -euo pipefail\n"
            'SCRIPT_NAME="isolated_stack.bash"\n'
            "DRY_RUN=0\n"
            f'RUN_DIR="{run_dir}"\n'
            f'DATA_VENV="{run_dir}/.venv-data"\n'
            f'LOG_DIR="{run_dir}/logs"\n'
            f'DATA_DIR="{data_dir}"\n'
            f'DATA_EXTRAS="{data_extras}"\n'
            f'DATA_PORT="{data_port}"\n'
            "HEALTH_TIMEOUT=4\n"
            'log() { echo "[${SCRIPT_NAME}] $*"; }\n'
            'banner() { echo ""; echo "[${SCRIPT_NAME}] === $* ==="; }\n'
            'announce() { echo "[${SCRIPT_NAME}] \\$ $*"; }\n'
            'is_dry() { [[ "${DRY_RUN}" == "1" ]]; }\n'
            + _extract_data_up_fn("require_cmd")
            + _extract_data_up_fn("ensure_dir")
            + _extract_data_up_fn("wait_for_health")
            + _extract_data_up_fn("data_up")
            + "data_up\n"
        )
        env = RedactedEnv(os.environ)
        env["PATH"] = path if path is not None else (str(bin_dir) + os.pathsep + "/usr/bin:/bin")
        return subprocess.run(
            ["/bin/bash", "-c", harness],
            capture_output=True,
            text=True,
            env=env,
            timeout=DATA_UP_TIMEOUT_SECONDS,
        )

    def test_creates_venv_installs_launches_with_gil_and_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            data_dir = root / "juniper-data"
            marker_dir = root / "markers"
            bin_dir = root / "bin"
            data_dir.mkdir()
            marker_dir.mkdir()
            bin_dir.mkdir()
            self._write_python314_stub(bin_dir, marker_dir)
            self._write_curl_ok(bin_dir)

            result = self._run_data_up(
                run_dir=run_dir,
                data_dir=data_dir,
                marker_dir=marker_dir,
                bin_dir=bin_dir,
                data_extras="api,mnist",
                data_port="65301",
            )
            pid_path = run_dir / "juniper-data.pid"
            child_pid: int | None = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("juniper-data is healthy", result.stdout)
                self.assertTrue((marker_dir / "venv.log").exists(), "python3.14 -m venv must run")
                self.assertIn(str(run_dir / ".venv-data"), (marker_dir / "venv.log").read_text())
                # pip stub logs each argv on its own line (printf '%s\n' "$@").
                pip_log = (marker_dir / "pip.log").read_text().splitlines()
                self.assertIn("-e", pip_log)
                self.assertIn(f"{data_dir}[api,mnist]", pip_log)
                self.assertIn("prometheus_client", pip_log)
                self.assertIn("juniper-observability", pip_log)
                self.assertTrue(pid_path.exists(), "data_up must write juniper-data.pid")
                child_pid = int(pid_path.read_text().strip())
                self.assertTrue(Path(f"/proc/{child_pid}").exists(), f"pid {child_pid} not live")
                self.assertEqual((marker_dir / "python.env").read_text().strip(), "PYTHON_GIL=0")
                py_args = (marker_dir / "python.args").read_text()
                self.assertIn("-m", py_args)
                self.assertIn("juniper_data", py_args)
                self.assertIn("--port", py_args)
                self.assertIn("65301", py_args)
                self.assertTrue((run_dir / "logs").is_dir(), "LOG_DIR must be created")
            finally:
                if child_pid is not None:
                    self._force_kill(child_pid)

    def test_skips_venv_create_when_venv_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            data_dir = root / "juniper-data"
            marker_dir = root / "markers"
            bin_dir = root / "bin"
            data_dir.mkdir()
            marker_dir.mkdir()
            bin_dir.mkdir()
            # Pre-seed an existing venv with the same activate/pip/python shape
            # the stub would create — data_up must NOT call python3.14 -m venv.
            data_venv = run_dir / ".venv-data"
            (data_venv / "bin").mkdir(parents=True)
            (data_venv / "bin" / "activate").write_text(
                "_OLD_VIRTUAL_PATH=\"$PATH\"\n"
                f'VIRTUAL_ENV="{data_venv}"\n'
                "export VIRTUAL_ENV\n"
                'PATH="$VIRTUAL_ENV/bin:$PATH"\n'
                "export PATH\n"
                "deactivate() {\n"
                '  PATH="$_OLD_VIRTUAL_PATH"\n'
                "  export PATH\n"
                "  unset VIRTUAL_ENV\n"
                "  unset -f deactivate 2>/dev/null || true\n"
                "}\n"
            )
            (data_venv / "bin" / "pip").write_text(
                "#!/usr/bin/env bash\n"
                f'printf "%s\\n" "$@" >>"{marker_dir}/pip.log"\n'
                "exit 0\n"
            )
            (data_venv / "bin" / "pip").chmod(0o755)
            (data_venv / "bin" / "python").write_text(
                "#!/usr/bin/env bash\n"
                f'printf "PYTHON_GIL=%s\\n" "${{PYTHON_GIL-}}" >"{marker_dir}/python.env"\n'
                f'printf "%s\\n" "$@" >"{marker_dir}/python.args"\n'
                "exec sleep 60\n"
            )
            (data_venv / "bin" / "python").chmod(0o755)
            # python3.14 stub that FAILS if -m venv is invoked (proves skip).
            (bin_dir / "python3.14").write_text(
                "#!/usr/bin/env bash\n"
                f'echo "VENV_SHOULD_NOT_RUN" >>"{marker_dir}/venv.log"\n'
                "exit 99\n"
            )
            (bin_dir / "python3.14").chmod(0o755)
            self._write_curl_ok(bin_dir)

            result = self._run_data_up(
                run_dir=run_dir,
                data_dir=data_dir,
                marker_dir=marker_dir,
                bin_dir=bin_dir,
            )
            pid_path = run_dir / "juniper-data.pid"
            child_pid: int | None = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertFalse(
                    (marker_dir / "venv.log").exists(),
                    "existing DATA_VENV must skip python3.14 -m venv",
                )
                self.assertTrue((marker_dir / "pip.log").exists(), "pip install must still run")
                self.assertTrue(pid_path.exists())
                child_pid = int(pid_path.read_text().strip())
                self.assertEqual((marker_dir / "python.env").read_text().strip(), "PYTHON_GIL=0")
            finally:
                if child_pid is not None:
                    self._force_kill(child_pid)

    def test_missing_python314_aborts_before_venv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            data_dir = root / "juniper-data"
            marker_dir = root / "markers"
            bin_dir = root / "bin"
            data_dir.mkdir()
            marker_dir.mkdir()
            bin_dir.mkdir()
            # Stub-only PATH (no host python3.14 leak): require_cmd must fail.
            result = self._run_data_up(
                run_dir=run_dir,
                data_dir=data_dir,
                marker_dir=marker_dir,
                bin_dir=bin_dir,
                path=str(bin_dir),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required command 'python3.14' not found", result.stdout + result.stderr)
            self.assertFalse((run_dir / ".venv-data").exists())
            self.assertFalse((run_dir / "juniper-data.pid").exists())

    def test_do_up_wires_data_up_first(self) -> None:
        # Drift guard: --up must compose data → cascor → canopy (data_up first).
        do_up = _extract_data_up_fn("do_up")
        self.assertRegex(
            do_up,
            r"data_up\n\s*cascor_up\n\s*canopy_up\n",
            msg="do_up must call data_up before cascor_up/canopy_up",
        )
        data_up = _extract_data_up_fn("data_up")
        self.assertIn("PYTHON_GIL=0", data_up)
        self.assertIn('echo "$!" >"${RUN_DIR}/juniper-data.pid"', data_up)
        self.assertIn('python3.14 -m venv "${DATA_VENV}"', data_up)


if __name__ == "__main__":
    unittest.main()
