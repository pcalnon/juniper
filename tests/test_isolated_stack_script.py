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
- ``port_pid`` / ``stop_port`` live teardown arms (hermetic ``ss`` stub + real
  short-lived children) — the only path that kills by listening port on ``--down``.

``--dry-run`` short-circuits before any filesystem or process side effect, so
those behavioural tests are fully hermetic — no real repos, conda, or network.
``JUNIPER_E2E_PROJECT_DIR`` / ``JUNIPER_E2E_RUN_DIR`` pin paths deterministically.
The ``port_pid`` / ``stop_port`` cases extract live function bodies and stub
``ss`` on ``PATH`` (keep ``/usr/bin:/bin`` for ``grep``/``cut``/``head``).
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
STOP_PORT_TIMEOUT_SECONDS = 20


def _extract_function(name: str) -> str:
    """Pull a live ``<name>() { ... }`` body (avoids harness drift)."""
    match = re.search(
        rf"^{re.escape(name)}\(\) \{{.*?\n\}}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"{name} function not found in isolated_stack.bash")
    return match.group(0)


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


class TestPortPid(unittest.TestCase):
    """Behavioral pins for ``port_pid`` ss→pid extraction (empty / first-match)."""

    def _run_port_pid(self, *, ss_script: str, port: str = "65101") -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            ss = bin_dir / "ss"
            ss.write_text("#!/usr/bin/env bash\n" + ss_script)
            ss.chmod(0o755)
            harness = f"""
                set -euo pipefail
                SCRIPT_NAME="isolated_stack.bash"
                {_extract_function("port_pid")}
                out="$(port_pid "{port}")"
                printf 'PID=%s\\n' "${{out}}"
            """
            env = RedactedEnv(os.environ)
            # Stub bin first so ``ss`` is ours; keep /usr/bin:/bin for grep/cut/head.
            env["PATH"] = str(bin_dir) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_extracts_first_pid_from_ss_output(self) -> None:
        # Real ss -tlnp lines embed users:(("proc",pid=N,fd=F)); port_pid must
        # take the first pid= token (head -n1) and ignore later listeners.
        result = self._run_port_pid(
            ss_script=("echo 'LISTEN 0 128 127.0.0.1:65101 0.0.0.0:* users:((\"python\",pid=424242,fd=3))'\n" "echo 'LISTEN 0 128 127.0.0.1:65101 0.0.0.0:* users:((\"python\",pid=999999,fd=4))'\n"),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "PID=424242")

    def test_empty_when_nothing_listening(self) -> None:
        result = self._run_port_pid(ss_script="exit 0\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "PID=")

    def _write_curl_ok(self, bin_dir: Path) -> None:
        curl = bin_dir / "curl"
        curl.write_text("#!/usr/bin/env bash\nexit 0\n")
        curl.chmod(0o755)

class TestStopPort(unittest.TestCase):
    """Behavioral pins for ``stop_port`` kill-by-port / nothing-listening arms.

    ``--down`` is the only live teardown path for the isolated E2E trio; a
    regression that drops the kill arm or mis-parses ``pid=`` leaves services
    bound on 8101/8202/8051 and poisons the next checklist run. Extracted from
    the live script so the harness cannot drift from production.
    """

    def _spawn_detached(self, inner_bash: str) -> int:
        """Start a session-leader child reparented to init (zombie-safe kill -0)."""
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

    def _run_stop_port(self, *, ss_script: str, port: str, name: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            data_dir = root / "juniper-data"
            marker_dir = root / "markers"
            bin_dir = root / "bin"
            data_dir.mkdir()
            marker_dir.mkdir()
            bin_dir.mkdir()
            ss = bin_dir / "ss"
            ss.write_text("#!/usr/bin/env bash\n" + ss_script)
            ss.chmod(0o755)
            # log/announce/is_dry are single-line helpers in the script; inline
            # them here and extract only the multi-line kill path (port_pid /
            # stop_port) so the harness cannot drift from production.
            harness = f"""
                set -euo pipefail
                SCRIPT_NAME="isolated_stack.bash"
                DRY_RUN=0
                log() {{ echo "[${{SCRIPT_NAME}}] $*"; }}
                announce() {{ echo "[${{SCRIPT_NAME}}] \\$ $*"; }}
                is_dry() {{ [[ "${{DRY_RUN}}" == "1" ]]; }}
                {_extract_function("port_pid")}
                {_extract_function("stop_port")}
                stop_port "{port}" "{name}"
            """
            env = RedactedEnv(os.environ)
            env["PATH"] = str(bin_dir) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=STOP_PORT_TIMEOUT_SECONDS,
            )

    def test_kills_listening_pid(self) -> None:
        pid = self._spawn_detached("exec sleep 60")
        try:
            result = self._run_stop_port(
                ss_script=f"echo 'LISTEN 0 128 127.0.0.1:65111 0.0.0.0:* users:((\"sleep\",pid={pid},fd=3))'\n",
                port="65111",
                name="juniper-data",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"Stopping juniper-data (pid {pid}) on port 65111", result.stdout)
            self.assertNotIn("nothing listening", result.stdout)
            # Brief poll — kill is async to the waiter's /proc view.
            for _ in range(40):
                if not Path(f"/proc/{pid}").exists():
                    break
                time.sleep(0.05)
            self.assertFalse(Path(f"/proc/{pid}").exists(), f"pid {pid} still alive after stop_port")
        finally:
            self._force_kill(pid)

    def test_nothing_listening_is_a_noop(self) -> None:
        result = self._run_stop_port(ss_script="exit 0\n", port="65112", name="juniper-canopy")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("juniper-canopy: nothing listening on port 65112", result.stdout)
        self.assertNotIn("Stopping juniper-canopy", result.stdout)

    def test_do_down_wires_stop_port_for_all_three_services(self) -> None:
        # Drift guard: --down must tear down canopy → cascor → data by port.
        self.assertIn('stop_port "${CANOPY_PORT}" "juniper-canopy"', SCRIPT_TEXT)
        self.assertIn('stop_port "${CASCOR_PORT}" "juniper-cascor"', SCRIPT_TEXT)
        self.assertIn('stop_port "${DATA_PORT}" "juniper-data"', SCRIPT_TEXT)
        # Kill path must go through port_pid (not a hard-coded pidfile-only stop).
        stop_body = _extract_function("stop_port")
        self.assertIn('pid="$(port_pid "${port}")"', stop_body)
        self.assertIn('kill "${pid}"', stop_body)


class TestLiveDown(unittest.TestCase):
    """Hermetic live ``--down``: kill-by-port + artifact cleanup (no conda/up)."""

    def test_live_down_removes_run_artifacts_when_ports_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            run_dir = root / "run"
            stub_bin = root / "bin"
            stub_bin.mkdir()
            # Empty ss → all three stop_port arms take the nothing-listening path.
            (stub_bin / "ss").write_text("#!/usr/bin/env bash\nexit 0\n")
            (stub_bin / "ss").chmod(0o755)

            for sub in (
                "juniper-data",
                "juniper-cascor/src/snapshots",
                "juniper-canopy/src/snapshots",
            ):
                (project_dir / sub).mkdir(parents=True)

            data_venv = run_dir / ".venv-data"
            data_dir = run_dir / "data"
            data_venv.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            (run_dir / "juniper-data.pid").write_text("1\n")
            (run_dir / "juniper-cascor.pid").write_text("2\n")
            (project_dir / "juniper-cascor/src/snapshots/snapshot_keepme.bin").write_text("x")
            (project_dir / "juniper-canopy/src/snapshots/snapshot_keepme.bin").write_text("y")
            # Non-matching snapshot name must survive the snapshot_* cleanup.
            (project_dir / "juniper-cascor/src/snapshots/other.bin").write_text("z")

            env = RedactedEnv(os.environ)
            env["JUNIPER_E2E_PROJECT_DIR"] = str(project_dir)
            env["JUNIPER_E2E_RUN_DIR"] = str(run_dir)
            env["JUNIPER_E2E_DATA_PORT"] = "65201"
            env["JUNIPER_E2E_CASCOR_PORT"] = "65202"
            env["JUNIPER_E2E_CANOPY_PORT"] = "65203"
            env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "--down"],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("nothing listening on port 65203", result.stdout)
            self.assertIn("nothing listening on port 65202", result.stdout)
            self.assertIn("nothing listening on port 65201", result.stdout)
            self.assertIn("Teardown complete", result.stdout)
            self.assertFalse(data_venv.exists(), "data venv must be removed")
            self.assertFalse(data_dir.exists(), "run data dir must be removed")
            self.assertFalse((run_dir / "juniper-data.pid").exists())
            self.assertFalse((run_dir / "juniper-cascor.pid").exists())
            self.assertFalse(
                (project_dir / "juniper-cascor/src/snapshots/snapshot_keepme.bin").exists(),
                "cascor snapshot_* must be cleaned",
            )
            self.assertFalse(
                (project_dir / "juniper-canopy/src/snapshots/snapshot_keepme.bin").exists(),
                "canopy snapshot_* must be cleaned",
            )
            self.assertTrue(
                (project_dir / "juniper-cascor/src/snapshots/other.bin").exists(),
                "non-snapshot_* artifacts must be preserved",
            )


if __name__ == "__main__":
    unittest.main()
