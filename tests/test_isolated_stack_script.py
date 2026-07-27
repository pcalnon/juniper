"""
Tests for util/isolated_stack.bash

Contract tests for the isolated training-runtime E2E bring-up helper (roadmap
unit E1 of the canopy training-runtime defects plan). The script encodes the
recipe documented in
``notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md``.

The live ``--up`` path launches long-lived services against conda envs, a
python3.14 venv, and real ports (8101/8202/8051), so — as with
``test_juniper_plant_all.py`` — this suite never brings the full stack up. It
pins:

- ``bash -n`` cleanliness;
- the launch-line invariants by text inspection (the exact commands + env vars
  the checklist promises);
- the ``--dry-run`` contract behaviourally: every action prints its commands
  with the configured ports expanded and touches NOTHING (no process, no
  filesystem), and the CLI rejects bad invocations;
- live ``cascor_up`` / ``canopy_up`` compose (conda activate → nohup launch →
  pid write → health gate) via a fake ``conda.sh`` + PATH-stubbed
  ``uvicorn``/``python``/``curl`` — no real conda envs or network.

``--dry-run`` short-circuits before any filesystem or process side effect, so
those behavioural tests are fully hermetic — no real repos, conda, or network.
``JUNIPER_E2E_PROJECT_DIR`` / ``JUNIPER_E2E_RUN_DIR`` pin paths deterministically.
The conda-service cases extract live function bodies and stub tools on ``PATH``
(keep ``/usr/bin:/bin`` for ``mkdir``/``nohup``). Orthogonal to open data_up /
port_pid / wait_for_health / activate_conda-nounset coverage PRs.
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
CONDA_UP_TIMEOUT_SECONDS = 25
# data_up launches a short-lived stubbed nohup child; keep headroom for mkdir/pip/health.
DATA_UP_TIMEOUT_SECONDS = 25


def _extract_isolated_fn(name: str) -> str:
    """Pull a live ``<name>() { ... }`` body from isolated_stack.bash (no harness drift)."""
    match = re.search(
        rf"^{re.escape(name)}\(\) \{{.*?\n\}}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"{name} function not found in isolated_stack.bash")
    return match.group(0)


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


def _read_marker_when_written(path: Path, timeout_seconds: float = 10.0) -> str:
    """Read a marker file written asynchronously by a nohup-backgrounded launch stub.

    The ``*_up`` arms background the launcher and return as soon as the (stubbed,
    instant) health probe passes, so the stub may not have written its marker yet
    when the harness returns -- poll briefly instead of asserting on a snapshot race.
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.exists():
            text = path.read_text()
            if text.strip():
                return text
        time.sleep(0.025)
    raise AssertionError(f"marker file {path} not written within {timeout_seconds}s")


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


class _CondaServiceUpHarness(unittest.TestCase):
    """Shared PATH-stub + fake conda.sh helpers for cascor_up / canopy_up."""

    def _stage_conda_and_stubs(
        self,
        root: Path,
        *,
        with_conda_sh: bool = True,
        launch_name: str,
    ) -> tuple[Path, Path, Path, Path, Path]:
        """Return (stub_bin, conda_dir, conda_log, launch_log, env_log)."""
        stub_bin = root / "path-stubs"
        stub_bin.mkdir(parents=True, exist_ok=True)
        conda_dir = root / "conda"
        conda_sh = conda_dir / "etc" / "profile.d" / "conda.sh"
        conda_log = root / "conda.log"
        launch_log = root / "launch.log"
        env_log = root / "launch.env"
        for path in (conda_log, launch_log, env_log):
            path.write_text("")

        if with_conda_sh:
            conda_sh.parent.mkdir(parents=True, exist_ok=True)
            # activate prepends stub_bin so uvicorn/python resolve to our stubs.
            conda_sh.write_text(f"""#!/usr/bin/env bash
conda() {{
    if [[ "${{1-}}" == "activate" ]]; then
        printf 'conda activate %s\\n' "${{2-}}" >>"{conda_log}"
        PATH="{stub_bin}:${{PATH-}}"
        export PATH
        return 0
    fi
    echo "unexpected conda invocation: $*" >&2
    return 2
}}
""")

        curl = stub_bin / "curl"
        curl.write_text("#!/usr/bin/env bash\nexit 0\n")
        curl.chmod(0o755)

        # Shared launch stub body: log argv + selected env, exit immediately.
        launch_body = f"""#!/usr/bin/env bash
{{
  printf '%s' "{launch_name}"
  printf ' %q' "$@"
  printf '\\n'
}} >>"{launch_log}"
{{
  printf 'LD_LIBRARY_PATH=%s\\n' "${{LD_LIBRARY_PATH-__UNSET__}}"
  printf 'JUNIPER_DATA_URL=%s\\n' "${{JUNIPER_DATA_URL-}}"
  printf 'JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=%s\\n' "${{JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS-}}"
  printf 'JUNIPER_CANOPY_DEMO_MODE=%s\\n' "${{JUNIPER_CANOPY_DEMO_MODE-}}"
  printf 'JUNIPER_CANOPY_PORT=%s\\n' "${{JUNIPER_CANOPY_PORT-}}"
  printf 'JUNIPER_CANOPY_CASCOR_SERVICE_URL=%s\\n' "${{JUNIPER_CANOPY_CASCOR_SERVICE_URL-}}"
  printf 'JUNIPER_CANOPY_JUNIPER_DATA_URL=%s\\n' "${{JUNIPER_CANOPY_JUNIPER_DATA_URL-}}"
  printf 'JUNIPER_CANOPY_CASCOR_WS_ORIGIN=%s\\n' "${{JUNIPER_CANOPY_CASCOR_WS_ORIGIN-}}"
}} >"{env_log}"
exit 0
"""
        launcher = stub_bin / launch_name
        launcher.write_text(launch_body)
        launcher.chmod(0o755)
        return stub_bin, conda_dir, conda_log, launch_log, env_log

    def _run_up(
        self,
        *,
        fn_name: str,
        stub_bin: Path,
        conda_dir: Path,
        run_dir: Path,
        src_dir: Path,
        data_port: str = "65101",
        cascor_port: str = "65202",
        canopy_port: str = "65051",
        cascor_conda: str = "JuniperCascor1",
        canopy_conda: str = "JuniperCanopy1",
    ) -> subprocess.CompletedProcess[str]:
        src_dir.mkdir(parents=True, exist_ok=True)
        log_dir = run_dir / "logs"
        harness = f"""
            set -euo pipefail
            SCRIPT_NAME="isolated_stack.bash"
            DRY_RUN=0
            RUN_DIR="{run_dir}"
            LOG_DIR="{log_dir}"
            CASCOR_SRC_DIR="{src_dir if fn_name == "cascor_up" else src_dir.parent / "cascor-src"}"
            CANOPY_SRC_DIR="{src_dir if fn_name == "canopy_up" else src_dir.parent / "canopy-src"}"
            DATA_PORT="{data_port}"
            CASCOR_PORT="{cascor_port}"
            CANOPY_PORT="{canopy_port}"
            CANOPY_ORIGIN="http://127.0.0.1:{canopy_port}"
            CASCOR_CONDA="{cascor_conda}"
            CANOPY_CONDA="{canopy_conda}"
            CONDA_DIR="{conda_dir}"
            CONDA_SH="{conda_dir}/etc/profile.d/conda.sh"
            HEALTH_TIMEOUT=5
            log() {{ echo "[${{SCRIPT_NAME}}] $*"; }}
            banner() {{ echo ""; echo "[${{SCRIPT_NAME}}] === $* ==="; }}
            announce() {{ echo "[${{SCRIPT_NAME}}] \\$ $*"; }}
            is_dry() {{ [[ "${{DRY_RUN}}" == "1" ]]; }}
            {_extract_isolated_fn("ensure_dir")}
            {_extract_isolated_fn("wait_for_health")}
            {_extract_isolated_fn("activate_conda")}
            {_extract_isolated_fn(fn_name)}
            set +e
            (
              set -euo pipefail
              {fn_name}
            )
            status=$?
            set -e
            echo "STATUS=${{status}}"
            exit 0
        """
        env = RedactedEnv(os.environ)
        # Stubs first so curl is ours; uvicorn/python appear after conda activate.
        env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"
        return subprocess.run(
            ["/bin/bash", "-c", harness],
            capture_output=True,
            text=True,
            env=env,
            timeout=CONDA_UP_TIMEOUT_SECONDS,
        )


class TestCascorUp(_CondaServiceUpHarness):
    """Behavioral pins for live ``cascor_up`` (conda → uvicorn → pid → health).

    ``cascor_up`` is the only path that points cascor at the isolated data URL,
    neutralizes ``LD_LIBRARY_PATH`` (libtorch collision), and sets the control-WS
    allowlist to canopy's origin. A regression that drops any of those env vars
    or the pid write breaks the checklist's cascor leg. Fake ``conda.sh`` +
    PATH-stubbed ``uvicorn``/``curl`` — no real conda or network. Does not
    re-test ``activate_conda`` nounset (#785) or ``wait_for_health`` alone (#793).
    """

    def test_happy_path_env_uvicorn_pid_and_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            src_dir = root / "project" / "juniper-cascor" / "src"
            stub_bin, conda_dir, conda_log, launch_log, env_log = self._stage_conda_and_stubs(root, launch_name="uvicorn")
            result = self._run_up(
                fn_name="cascor_up",
                stub_bin=stub_bin,
                conda_dir=conda_dir,
                run_dir=run_dir,
                src_dir=src_dir,
                data_port="65101",
                cascor_port="65202",
                canopy_port="65051",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("STATUS=0", result.stdout)
            self.assertIn("juniper-cascor is healthy", result.stdout)
            self.assertIn("conda activate JuniperCascor1", conda_log.read_text())

            launch = _read_marker_when_written(launch_log)
            self.assertIn("api.app:create_app", launch)
            self.assertIn("--factory", launch)
            self.assertIn("--host", launch)
            self.assertIn("127.0.0.1", launch)
            self.assertIn("--port", launch)
            self.assertIn("65202", launch)

            env_text = _read_marker_when_written(env_log)
            # Empty LD_LIBRARY_PATH (not unset) — rust_mudgeon libtorch guard.
            self.assertIn("LD_LIBRARY_PATH=\n", env_text)
            self.assertIn("JUNIPER_DATA_URL=http://127.0.0.1:65101", env_text)
            self.assertIn(
                "JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://127.0.0.1:65051",
                env_text,
            )

            pid_path = run_dir / "juniper-cascor.pid"
            self.assertTrue(pid_path.is_file(), "cascor_up must write juniper-cascor.pid")
            self.assertRegex(pid_path.read_text().strip(), r"^[0-9]+$")

    def test_missing_conda_sh_aborts_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            src_dir = root / "project" / "juniper-cascor" / "src"
            stub_bin, conda_dir, _conda_log, launch_log, _env_log = self._stage_conda_and_stubs(root, with_conda_sh=False, launch_name="uvicorn")
            result = self._run_up(
                fn_name="cascor_up",
                stub_bin=stub_bin,
                conda_dir=conda_dir,
                run_dir=run_dir,
                src_dir=src_dir,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("conda not found at", result.stdout)
            self.assertEqual(launch_log.read_text(), "")
            self.assertFalse((run_dir / "juniper-cascor.pid").exists())


class TestCanopyUp(_CondaServiceUpHarness):
    """Behavioral pins for live ``canopy_up`` (conda → python main.py → pid → health).

    ``canopy_up`` is the only path that forces service mode (``DEMO_MODE=0``),
    wires cascor/data URLs to the isolated ports, and sets the control-WS Origin
    to match cascor's allowlist. Dropping ``DEMO_MODE=0`` or the Origin pair is
    the classic 403-reconnect failure class. Fake ``conda.sh`` + PATH-stubbed
    ``python``/``curl`` — no real conda or network.
    """

    def test_happy_path_service_mode_env_pid_and_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            src_dir = root / "project" / "juniper-canopy" / "src"
            stub_bin, conda_dir, conda_log, launch_log, env_log = self._stage_conda_and_stubs(root, launch_name="python")
            result = self._run_up(
                fn_name="canopy_up",
                stub_bin=stub_bin,
                conda_dir=conda_dir,
                run_dir=run_dir,
                src_dir=src_dir,
                data_port="65101",
                cascor_port="65202",
                canopy_port="65051",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("STATUS=0", result.stdout)
            self.assertIn("juniper-canopy is healthy", result.stdout)
            self.assertIn("conda activate JuniperCanopy1", conda_log.read_text())

            launch = _read_marker_when_written(launch_log)
            self.assertIn("main.py", launch)

            env_text = _read_marker_when_written(env_log)
            self.assertIn("JUNIPER_CANOPY_DEMO_MODE=0", env_text)
            self.assertIn("JUNIPER_CANOPY_PORT=65051", env_text)
            self.assertIn(
                "JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://127.0.0.1:65202",
                env_text,
            )
            self.assertIn(
                "JUNIPER_CANOPY_JUNIPER_DATA_URL=http://127.0.0.1:65101",
                env_text,
            )
            self.assertIn(
                "JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://127.0.0.1:65051",
                env_text,
            )

            pid_path = run_dir / "juniper-canopy.pid"
            self.assertTrue(pid_path.is_file(), "canopy_up must write juniper-canopy.pid")
            self.assertRegex(pid_path.read_text().strip(), r"^[0-9]+$")

    def test_missing_conda_sh_aborts_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            src_dir = root / "project" / "juniper-canopy" / "src"
            stub_bin, conda_dir, _conda_log, launch_log, _env_log = self._stage_conda_and_stubs(root, with_conda_sh=False, launch_name="python")
            result = self._run_up(
                fn_name="canopy_up",
                stub_bin=stub_bin,
                conda_dir=conda_dir,
                run_dir=run_dir,
                src_dir=src_dir,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("conda not found at", result.stdout)
            self.assertEqual(launch_log.read_text(), "")
            self.assertFalse((run_dir / "juniper-canopy.pid").exists())

    def test_cascor_and_canopy_bodies_pin_control_ws_pair(self) -> None:
        # Drift guard: the Origin/allowlist pair must stay co-located in both ups.
        cascor_body = _extract_isolated_fn("cascor_up")
        canopy_body = _extract_isolated_fn("canopy_up")
        self.assertIn("JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=", cascor_body)
        self.assertIn('JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS="${CANOPY_ORIGIN}"', cascor_body)
        self.assertIn("LD_LIBRARY_PATH=''", cascor_body)
        self.assertIn('echo "$!" >"${RUN_DIR}/juniper-cascor.pid"', cascor_body)
        self.assertIn("JUNIPER_CANOPY_DEMO_MODE=0", canopy_body)
        self.assertIn('JUNIPER_CANOPY_CASCOR_WS_ORIGIN="${CANOPY_ORIGIN}"', canopy_body)
        self.assertIn('echo "$!" >"${RUN_DIR}/juniper-canopy.pid"', canopy_body)


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
            'cat >"$dest/bin/activate" <<ACT\n'
            '_OLD_VIRTUAL_PATH="\\$PATH"\n'
            'VIRTUAL_ENV="$dest"\n'
            "export VIRTUAL_ENV\n"
            'PATH="\\$VIRTUAL_ENV/bin:\\$PATH"\n'
            "export PATH\n"
            "deactivate() {\n"
            '  PATH="\\$_OLD_VIRTUAL_PATH"\n'
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
            'is_dry() { [[ "${DRY_RUN}" == "1" ]]; }\n' + _extract_data_up_fn("require_cmd") + _extract_data_up_fn("ensure_dir") + _extract_data_up_fn("wait_for_health") + _extract_data_up_fn("data_up") + "data_up\n"
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
                self.assertEqual(_read_marker_when_written(marker_dir / "python.env").strip(), "PYTHON_GIL=0")
                py_args = _read_marker_when_written(marker_dir / "python.args")
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
            (data_venv / "bin" / "activate").write_text('_OLD_VIRTUAL_PATH="$PATH"\n' f'VIRTUAL_ENV="{data_venv}"\n' "export VIRTUAL_ENV\n" 'PATH="$VIRTUAL_ENV/bin:$PATH"\n' "export PATH\n" "deactivate() {\n" '  PATH="$_OLD_VIRTUAL_PATH"\n' "  export PATH\n" "  unset VIRTUAL_ENV\n" "  unset -f deactivate 2>/dev/null || true\n" "}\n")
            (data_venv / "bin" / "pip").write_text("#!/usr/bin/env bash\n" f'printf "%s\\n" "$@" >>"{marker_dir}/pip.log"\n' "exit 0\n")
            (data_venv / "bin" / "pip").chmod(0o755)
            (data_venv / "bin" / "python").write_text("#!/usr/bin/env bash\n" f'printf "PYTHON_GIL=%s\\n" "${{PYTHON_GIL-}}" >"{marker_dir}/python.env"\n' f'printf "%s\\n" "$@" >"{marker_dir}/python.args"\n' "exec sleep 60\n")
            (data_venv / "bin" / "python").chmod(0o755)
            # python3.14 stub that FAILS if -m venv is invoked (proves skip).
            (bin_dir / "python3.14").write_text("#!/usr/bin/env bash\n" f'echo "VENV_SHOULD_NOT_RUN" >>"{marker_dir}/venv.log"\n' "exit 99\n")
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
                self.assertEqual(_read_marker_when_written(marker_dir / "python.env").strip(), "PYTHON_GIL=0")
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
