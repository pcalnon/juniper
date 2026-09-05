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


STOP_PORT_TIMEOUT_SECONDS = 20
HEALTH_HELPER_TIMEOUT_SECONDS = 20


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

    Completeness is guaranteed by the WRITER, not by this poll: the stubs build each
    marker in a ``.partial`` sibling and ``mv`` it into place, so any file observed
    here is a whole record. That is the load-bearing half of the fix -- a stub that
    wrote its multi-line env block straight to the final path was caught mid-record
    (7 of 12 lines) under CPU contention, and the test failed on a key that had not
    landed yet.

    The trailing-newline check below is only a cheap second line of defence for a
    future stub that forgets the atomic-publish idiom; it cannot catch a truncated
    record that happens to end on a line boundary, which is exactly what was observed.
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.exists():
            text = path.read_text()
            if text.strip() and text.endswith("\n"):
                return text
        time.sleep(0.025)
    raise AssertionError(f"marker file {path} not written (or left mid-record) within {timeout_seconds}s")


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


def _extract_wait_for_health() -> str:
    """Pull the live ``wait_for_health() { ... }`` body (no harness drift).

    Named distinctly from concurrent coverage PRs' generic ``_extract_function``
    helpers so a merge cannot silently alias the wrong extractor.
    """
    match = re.search(
        r"^wait_for_health\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("wait_for_health function not found in isolated_stack.bash")
    return match.group(0)


def _extract_probe_health() -> str:
    """Pull the live ``probe_health() { ... }`` body (no harness drift)."""
    match = re.search(
        r"^probe_health\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("probe_health function not found in isolated_stack.bash")
    return match.group(0)


def _extract_port_pid_for_probe() -> str:
    """Pull ``port_pid`` for ``probe_health`` harnesses (distinct from #786's extractor)."""
    match = re.search(
        r"^port_pid\(\) \{.*?\n\}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("port_pid function not found in isolated_stack.bash")
    return match.group(0)


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

    def test_canopy_browser_ws_allowlist_env(self) -> None:
        # F-E2E-006: canopy's OWN /ws/training + /ws/control admit only port-8050
        # origins by default (canopy src/settings.py:142-147); the leg must hand
        # canopy an allowlist derived from the REAL canopy port or the dashboard's
        # own browser sockets 403-loop on the isolated port.
        self.assertIn("JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS=", SCRIPT_TEXT)
        self.assertIn(
            'CANOPY_WS_ALLOWLIST="[\\"http://127.0.0.1:${CANOPY_PORT}\\",\\"http://localhost:${CANOPY_PORT}\\"]"',
            SCRIPT_TEXT,
        )


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
            self.assertIn(
                'JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS=["http://127.0.0.1:8051","http://localhost:8051"]',
                out,
            )

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
            # canopy takes its port via the NESTED JUNIPER_CANOPY_SERVER__PORT (env), not a
            # --port flag. The flat JUNIPER_CANOPY_PORT is NOT a canopy setting: Settings has
            # extra="ignore" + env_nested_delimiter="__", so the flat form is silently dropped
            # and canopy binds 8050 — the operator port (E2E plan §4.2, trap T-1).
            self.assertIn("JUNIPER_CANOPY_SERVER__PORT=9051", out)
            self.assertIn("JUNIPER_CANOPY_SERVER__HOST=127.0.0.1", out)
            # Negative guard so the T-1 bug cannot re-land: the flat form must be gone.
            self.assertNotIn("JUNIPER_CANOPY_PORT=", out)
            self.assertIn("[api,mnist]", out)
            # The WS pair must track the overridden canopy port on both ends.
            self.assertIn("JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://127.0.0.1:9051", out)
            # And the browser-facing allowlist must follow the override too (F-E2E-006).
            self.assertIn(
                'JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS=["http://127.0.0.1:9051","http://localhost:9051"]',
                out,
            )

    def test_dry_up_with_recurrence_prints_leg_and_canopy_url(self) -> None:
        # PR-M2: the fourth leg's announce lines + the canopy hand-off, all print-only.
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            result = _run(
                "--dry-run",
                "--up",
                "--with-recurrence",
                env_extra={"JUNIPER_E2E_PROJECT_DIR": "/opt/juniper-e2e-fixture", "JUNIPER_E2E_RUN_DIR": str(run_dir)},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            out = result.stdout
            self.assertIn("8211 occupancy pre-check", out)
            self.assertIn("serve --host 127.0.0.1 --port 8211", out)
            self.assertIn("JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=http://127.0.0.1:8211", out)
            self.assertIn("/v1/health/ready", out)
            self.assertFalse(run_dir.exists(), "dry-run --up --with-recurrence must not touch the run dir")

    def test_dry_up_without_recurrence_flag_omits_leg(self) -> None:
        # Default posture unchanged: no recurrence launch, no canopy recurrence URL.
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(Path(tmp) / "run").stdout
            self.assertNotIn("juniper-recurrence", out)
            self.assertNotIn("JUNIPER_CANOPY_RECURRENCE_SERVICE_URL", out)


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
            self.assertIn("snapshot_*.h5", result.stdout)
            self.assertFalse(run_dir.exists(), "dry-run --down must not create/remove anything on disk")

    def test_dry_down_includes_recurrence_port(self) -> None:
        # --down covers the optional fourth leg unconditionally (idempotent when absent).
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            result = _run(
                "--dry-run",
                "--down",
                env_extra={"JUNIPER_E2E_PROJECT_DIR": "/opt/juniper-e2e-fixture", "JUNIPER_E2E_RUN_DIR": str(run_dir)},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("stop juniper-recurrence on 8211", result.stdout)


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
        #
        # Each marker is published ATOMICALLY -- written to a ``.partial`` sibling and
        # then ``mv``'d into place. A multi-line record written straight to its final
        # path is observable half-written: a poller caught this env block after only 7
        # of its 12 lines (newline-terminated, so a trailing-newline check passes), and
        # the test then failed on a key that had not landed yet. ``mv`` within a
        # directory is a rename, so the reader sees either no file or the whole record.
        launch_body = f"""#!/usr/bin/env bash
{{
  printf '%s' "{launch_name}"
  printf ' %q' "$@"
  printf '\\n'
}} >"{launch_log}.partial"
mv -f "{launch_log}.partial" "{launch_log}"
{{
  printf 'LD_LIBRARY_PATH=%s\\n' "${{LD_LIBRARY_PATH-__UNSET__}}"
  printf 'JUNIPER_DATA_URL=%s\\n' "${{JUNIPER_DATA_URL-}}"
  printf 'JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=%s\\n' "${{JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS-}}"
  printf 'JUNIPER_CANOPY_DEMO_MODE=%s\\n' "${{JUNIPER_CANOPY_DEMO_MODE-}}"
  printf 'JUNIPER_CANOPY_SERVER__HOST=%s\\n' "${{JUNIPER_CANOPY_SERVER__HOST-}}"
  printf 'JUNIPER_CANOPY_SERVER__PORT=%s\\n' "${{JUNIPER_CANOPY_SERVER__PORT-}}"
  printf 'JUNIPER_CANOPY_PORT_FLAT=%s\\n' "${{JUNIPER_CANOPY_PORT-}}"
  printf 'JUNIPER_CANOPY_CASCOR_SERVICE_URL=%s\\n' "${{JUNIPER_CANOPY_CASCOR_SERVICE_URL-}}"
  printf 'JUNIPER_CANOPY_JUNIPER_DATA_URL=%s\\n' "${{JUNIPER_CANOPY_JUNIPER_DATA_URL-}}"
  printf 'JUNIPER_CANOPY_CASCOR_WS_ORIGIN=%s\\n' "${{JUNIPER_CANOPY_CASCOR_WS_ORIGIN-}}"
  printf 'JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS=%s\\n' "${{JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS-}}"
  printf 'JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=%s\\n' "${{JUNIPER_CANOPY_RECURRENCE_SERVICE_URL-}}"
  printf 'JUNIPER_CANOPY_SNAPSHOT_DIR=%s\\n' "${{JUNIPER_CANOPY_SNAPSHOT_DIR-}}"
}} >"{env_log}.partial"
mv -f "{env_log}.partial" "{env_log}"
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
        with_recurrence: str = "0",
        recurrence_port: str = "65211",
        recurrence_bin: "str | None" = None,
    ) -> subprocess.CompletedProcess[str]:
        src_dir.mkdir(parents=True, exist_ok=True)
        log_dir = run_dir / "logs"
        effective_recurrence_bin = recurrence_bin or str(conda_dir / "envs" / "JuniperCascor1" / "bin" / "juniper-recurrence")
        # F-CANOPY-007 remediation: canopy_up exports JUNIPER_CANOPY_SNAPSHOT_DIR, whose script-level
        # default is the SHARED snapshot root "${PROJECT_DIR}/juniper-cascor/cascor-snapshots" (the
        # 2026-08-20 storage-convention ruling; it was "${CASCOR_SRC_DIR}/snapshots" until the
        # service stopped writing into the serializer package). The harness enumerates every
        # variable the function reads and runs under `set -u`, so a new script-level variable MUST
        # be declared here or the function aborts on an unbound expansion rather than on anything
        # the test is asserting.
        cascor_src_dir = src_dir if fn_name == "cascor_up" else src_dir.parent / "cascor-src"
        snapshot_dir = cascor_src_dir.parent / "cascor-snapshots"
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
            CANOPY_WS_ALLOWLIST="[\\"http://127.0.0.1:{canopy_port}\\",\\"http://localhost:{canopy_port}\\"]"
            CANOPY_SNAPSHOT_DIR="{snapshot_dir}"
            CASCOR_CONDA="{cascor_conda}"
            CANOPY_CONDA="{canopy_conda}"
            WITH_RECURRENCE="{with_recurrence}"
            RECURRENCE_PORT="{recurrence_port}"
            RECURRENCE_CONDA="JuniperCascor1"
            RECURRENCE_BIN="{effective_recurrence_bin}"
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
            self.assertIn("JUNIPER_CANOPY_SERVER__HOST=127.0.0.1", env_text)
            self.assertIn("JUNIPER_CANOPY_SERVER__PORT=65051", env_text)
            # Negative guard (T-1): canopy_up must NOT export the flat JUNIPER_CANOPY_PORT —
            # canopy silently ignores it (extra="ignore") and would bind operator port 8050.
            self.assertIn("JUNIPER_CANOPY_PORT_FLAT=\n", env_text)
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
            # F-E2E-006: the browser-facing allowlist must reach the live process env
            # and carry the REAL canopy port (default admits only 8050 origins).
            self.assertIn(
                'JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS=["http://127.0.0.1:65051","http://localhost:65051"]',
                env_text,
            )
            # Without --with-recurrence the URL must be UNSET (empty probe line) — an empty
            # string export would read as "configured" to canopy's settings (plan §4.5).
            self.assertIn("JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=\n", env_text)
            # F-CANOPY-007: canopy CREATES snapshots through the cascor backend but LISTS them
            # off a local dir, defaulting to "./snapshots" relative to its own CWD — so on two
            # host processes with different CWDs the list is SILENTLY empty while cascor holds
            # the .h5. canopy_up must point canopy at cascor's real snapshot dir, or the whole
            # W5 snapshot lifecycle is unreachable from the UI.
            self.assertIn("JUNIPER_CANOPY_SNAPSHOT_DIR=", env_text)
            self.assertRegex(env_text, r"JUNIPER_CANOPY_SNAPSHOT_DIR=\S*/cascor-snapshots\n")

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


class TestRecurrenceLeg(_CondaServiceUpHarness):
    """PR-M2 (--with-recurrence): canopy hand-off, recurrence_up compose, 8211 pre-check."""

    def _stage_recurrence_bin(self, conda_dir: Path, root: Path) -> "tuple[Path, Path, Path]":
        """Stage a stub juniper-recurrence console script at the env-bin path recurrence_up execs."""
        launch_log = root / "recurrence-launch.log"
        env_log = root / "recurrence-env.log"
        for path in (launch_log, env_log):
            path.write_text("")
        bin_dir = conda_dir / "envs" / "JuniperCascor1" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        stub = bin_dir / "juniper-recurrence"
        # Markers published atomically (.partial then mv) -- see _stage_conda_and_stubs.
        stub.write_text(f"""#!/usr/bin/env bash
{{
  printf 'juniper-recurrence'
  printf ' %q' "$@"
  printf '\\n'
}} >"{launch_log}.partial"
mv -f "{launch_log}.partial" "{launch_log}"
{{
  printf 'LD_LIBRARY_PATH=%s\\n' "${{LD_LIBRARY_PATH-__UNSET__}}"
  printf 'JUNIPER_DATA_URL=%s\\n' "${{JUNIPER_DATA_URL-}}"
  printf 'JUNIPER_RECURRENCE_METRICS_ENABLED=%s\\n' "${{JUNIPER_RECURRENCE_METRICS_ENABLED-}}"
  printf 'JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=%s\\n' "${{JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED-}}"
}} >"{env_log}.partial"
mv -f "{env_log}.partial" "{env_log}"
exit 0
""")
        stub.chmod(0o755)
        return stub, launch_log, env_log

    def test_canopy_up_with_recurrence_exports_service_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            src_dir = root / "project" / "juniper-canopy" / "src"
            stub_bin, conda_dir, _conda_log, _launch_log, env_log = self._stage_conda_and_stubs(root, launch_name="python")
            result = self._run_up(
                fn_name="canopy_up",
                stub_bin=stub_bin,
                conda_dir=conda_dir,
                run_dir=run_dir,
                src_dir=src_dir,
                with_recurrence="1",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("STATUS=0", result.stdout)
            env_text = _read_marker_when_written(env_log)
            self.assertIn("JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=http://127.0.0.1:65211", env_text)

    def test_recurrence_up_launches_console_script_with_env_and_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            src_dir = root / "project" / "unused" / "src"
            stub_bin, conda_dir, _conda_log, _canopy_launch, _canopy_env = self._stage_conda_and_stubs(root, launch_name="python")
            stub, launch_log, env_log = self._stage_recurrence_bin(conda_dir, root)
            result = self._run_up(
                fn_name="recurrence_up",
                stub_bin=stub_bin,
                conda_dir=conda_dir,
                run_dir=run_dir,
                src_dir=src_dir,
                recurrence_bin=str(stub),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("STATUS=0", result.stdout)
            self.assertIn("juniper-recurrence is healthy", result.stdout)
            # Health gate is the READY endpoint (experiment_stack parity).
            self.assertIn("/v1/health/ready", result.stdout)

            launch = _read_marker_when_written(launch_log)
            self.assertIn("serve --host 127.0.0.1 --port 65211", launch)

            env_text = _read_marker_when_written(env_log)
            # Emptied (torch/libtorch shadow, cascor-leg parity), not merely unset.
            self.assertIn("LD_LIBRARY_PATH=\n", env_text)
            self.assertNotIn("LD_LIBRARY_PATH=__UNSET__", env_text)
            self.assertIn("JUNIPER_DATA_URL=http://127.0.0.1:65101", env_text)
            self.assertIn("JUNIPER_RECURRENCE_METRICS_ENABLED=true", env_text)
            self.assertIn("JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false", env_text)

            pid_path = run_dir / "juniper-recurrence.pid"
            self.assertTrue(pid_path.is_file(), "recurrence_up must write juniper-recurrence.pid")
            self.assertRegex(pid_path.read_text().strip(), r"^[0-9]+$")

    def test_recurrence_up_missing_bin_aborts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            src_dir = root / "project" / "unused" / "src"
            stub_bin, conda_dir, _conda_log, _launch_log, _env_log = self._stage_conda_and_stubs(root, launch_name="python")
            missing = root / "nonexistent" / "juniper-recurrence"
            result = self._run_up(
                fn_name="recurrence_up",
                stub_bin=stub_bin,
                conda_dir=conda_dir,
                run_dir=run_dir,
                src_dir=src_dir,
                recurrence_bin=str(missing),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("STATUS=1", result.stdout)
            self.assertIn("console script not found", result.stdout)
            self.assertFalse((run_dir / "juniper-recurrence.pid").exists())

    def test_up_with_recurrence_precheck_aborts_on_live_listener(self) -> None:
        # A real listener on the recurrence port must abort --up BEFORE any leg starts;
        # the expected collider is juniper-deploy's root-owned docker-proxy on 8211
        # (which ss lists without a pid= field for non-root callers — hence port_in_use,
        # not port_pid, backs the pre-check).
        import socket

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            port = srv.getsockname()[1]
            with tempfile.TemporaryDirectory() as tmp:
                run_dir = Path(tmp) / "run"
                result = _run(
                    "--up",
                    "--with-recurrence",
                    env_extra={
                        "JUNIPER_E2E_PROJECT_DIR": "/opt/juniper-e2e-fixture",
                        "JUNIPER_E2E_RUN_DIR": str(run_dir),
                        "JUNIPER_E2E_RECURRENCE_PORT": str(port),
                    },
                )
                self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
                self.assertIn("already has a listener", result.stdout)
                self.assertIn("refusing to start the recurrence leg", result.stdout)
                self.assertFalse(run_dir.exists(), "pre-check must abort before any leg touches the run dir")
        finally:
            srv.close()


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
            # python: answer the free-threading probe (-c), else record PYTHON_GIL + argv
            # and sleep so the pidfile stays live. Probe answer defaults to 1 (free-threaded)
            # and can be overridden via a gil_probe_answer marker file.
            "cat >\"$dest/bin/python\" <<'PY'\n"
            "#!/usr/bin/env bash\n"
            'if [[ "${1-}" == "-c" ]]; then\n'
            f'  if [[ -f "{marker_dir}/gil_probe_answer" ]]; then cat "{marker_dir}/gil_probe_answer"; else echo 1; fi\n'
            "  exit 0\n"
            "fi\n"
            # Published ATOMICALLY (.partial then mv) -- see _read_marker_when_written.
            # A direct write is observable mid-record, and the helper's trailing-newline
            # guard cannot catch a truncation that lands on a line boundary: CI caught
            # this one at "--port\\n" with the port value missing.
            f'printf "PYTHON_GIL=%s\\n" "${{PYTHON_GIL-}}" >"{marker_dir}/python.env.partial"\n'
            f'mv -f "{marker_dir}/python.env.partial" "{marker_dir}/python.env"\n'
            f'printf "%s\\n" "$@" >"{marker_dir}/python.args.partial"\n'
            f'mv -f "{marker_dir}/python.args.partial" "{marker_dir}/python.args"\n'
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
            # The two markers are published ATOMICALLY (.partial then mv) -- see
            # _read_marker_when_written. A direct write is observable mid-record.
            (data_venv / "bin" / "python").write_text(
                "#!/usr/bin/env bash\n" 'if [[ "${1-}" == "-c" ]]; then\n' f'  if [[ -f "{marker_dir}/gil_probe_answer" ]]; then cat "{marker_dir}/gil_probe_answer"; else echo 1; fi\n' "  exit 0\n" "fi\n" f'printf "PYTHON_GIL=%s\\n" "${{PYTHON_GIL-}}" >"{marker_dir}/python.env.partial"\n' f'mv -f "{marker_dir}/python.env.partial" "{marker_dir}/python.env"\n' f'printf "%s\\n" "$@" >"{marker_dir}/python.args.partial"\n' f'mv -f "{marker_dir}/python.args.partial" "{marker_dir}/python.args"\n' "exec sleep 60\n"
            )
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

    def test_stock_build_omits_python_gil(self) -> None:
        # On a stock (non-free-threaded) CPython, PYTHON_GIL=0 is FATAL at startup
        # ("config_read_gil: Disabling the GIL is not supported by this build") — the
        # 2026-08-09 rehearsal failure. The probe answering 0 must OMIT the toggle.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            data_dir = root / "juniper-data"
            marker_dir = root / "markers"
            bin_dir = root / "bin"
            data_dir.mkdir()
            marker_dir.mkdir()
            bin_dir.mkdir()
            (marker_dir / "gil_probe_answer").write_text("0\n")
            data_venv = run_dir / ".venv-data"
            (data_venv / "bin").mkdir(parents=True)
            (data_venv / "bin" / "activate").write_text('_OLD_VIRTUAL_PATH="$PATH"\n' f'VIRTUAL_ENV="{data_venv}"\n' "export VIRTUAL_ENV\n" 'PATH="$VIRTUAL_ENV/bin:$PATH"\n' "export PATH\n" "deactivate() {\n" '  PATH="$_OLD_VIRTUAL_PATH"\n' "  export PATH\n" "  unset VIRTUAL_ENV\n" "  unset -f deactivate 2>/dev/null || true\n" "}\n")
            (data_venv / "bin" / "pip").write_text("#!/usr/bin/env bash\n" f'printf "%s\\n" "$@" >>"{marker_dir}/pip.log"\n' "exit 0\n")
            (data_venv / "bin" / "pip").chmod(0o755)
            # The two markers are published ATOMICALLY (.partial then mv) -- see
            # _read_marker_when_written. A direct write is observable mid-record.
            (data_venv / "bin" / "python").write_text(
                "#!/usr/bin/env bash\n" 'if [[ "${1-}" == "-c" ]]; then\n' f'  if [[ -f "{marker_dir}/gil_probe_answer" ]]; then cat "{marker_dir}/gil_probe_answer"; else echo 1; fi\n' "  exit 0\n" "fi\n" f'printf "PYTHON_GIL=%s\\n" "${{PYTHON_GIL-}}" >"{marker_dir}/python.env.partial"\n' f'mv -f "{marker_dir}/python.env.partial" "{marker_dir}/python.env"\n' f'printf "%s\\n" "$@" >"{marker_dir}/python.args.partial"\n' f'mv -f "{marker_dir}/python.args.partial" "{marker_dir}/python.args"\n' "exec sleep 60\n"
            )
            (data_venv / "bin" / "python").chmod(0o755)
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
            child_pid: "int | None" = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertTrue(pid_path.exists())
                child_pid = int(pid_path.read_text().strip())
                # The toggle must be ABSENT (empty probe value), never PYTHON_GIL=0.
                self.assertEqual(_read_marker_when_written(marker_dir / "python.env").strip(), "PYTHON_GIL=")
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
        # Drift guard: --up must compose data → cascor → canopy (data_up first)
        # and absorb mid-bring-up failures into do_down (orphan-listener class).
        do_up = _extract_data_up_fn("do_up")
        self.assertIn("data_up || failed=1", do_up)
        self.assertIn("cascor_up || failed=1", do_up)
        self.assertIn("canopy_up || failed=1", do_up)
        # Use the ``|| failed=1`` call sites (not bare names in comments).
        self.assertLess(do_up.index("data_up || failed=1"), do_up.index("cascor_up || failed=1"))
        self.assertLess(do_up.index("cascor_up || failed=1"), do_up.index("canopy_up || failed=1"))
        self.assertIn("tearing the partial trio back down", do_up)
        self.assertIn("do_down", do_up)
        # OR-list invocation disables set -e inside each *_up — critical steps must
        # ``|| return 1`` or a mid-function failure false-greens via wait_for_health.
        data_up = _extract_data_up_fn("data_up")
        cascor_up = _extract_data_up_fn("cascor_up")
        canopy_up = _extract_data_up_fn("canopy_up")
        self.assertIn('activate_conda "${CASCOR_CONDA}" || return 1', cascor_up)
        self.assertIn('activate_conda "${CANOPY_CONDA}" || return 1', canopy_up)
        self.assertIn("require_cmd python3.14 || return 1", data_up)
        self.assertIn('wait_for_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health" || return 1', data_up)
        self.assertIn("PYTHON_GIL=0", data_up)
        self.assertIn('echo "$!" >"${RUN_DIR}/juniper-data.pid"', data_up)
        self.assertIn('python3.14 -m venv "${DATA_VENV}"', data_up)


if __name__ == "__main__":
    unittest.main()


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

    def test_conda_activate_failure_propagates_under_or_list(self) -> None:
        """OR-list callers must still see activate failure (not a masked exit 0).

        Bash disables ``set -e`` inside a function invoked as ``fn || …``. Open
        #963's ``activate_conda || return 1`` / ``*_up || failed=1`` absorb hits
        that path; a trailing successful ``set -u`` must not mask ``conda
        activate`` failure and let cascor/canopy launch on the ambient PATH.
        """
        with tempfile.TemporaryDirectory() as tmp:
            conda_sh = Path(tmp) / "conda.sh"
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() {\n" '  if [[ "$1" == "activate" ]]; then\n' "    return 1\n" "  fi\n" "}\n")
            harness = "set -euo pipefail\n" 'log() { echo "$*"; }\n' f'CONDA_SH="{conda_sh}"\n' + _extract_activate_conda_function() + "failed=0\n" + 'activate_conda "JuniperCascor1" || failed=1\n' + 'echo "failed=${failed}"\n' + "if (( failed != 1 )); then exit 2; fi\n"
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
        body = _extract_activate_conda_function()
        self.assertIn("set +u", body)
        self.assertRegex(
            body,
            r"if ! conda activate[^\n]+; then\n\s*set -u\n",
            msg="activate_conda failure arm must restore set -u before return 1",
        )
        self.assertRegex(
            body,
            r"fi\n\s*set -u\n\}\n",
            msg="activate_conda success arm must restore set -u after conda activate",
        )


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
            bin_dir = Path(tmp) / "bin"
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
                "juniper-cascor/cascor-snapshots",
                "juniper-canopy/src/snapshots",
            ):
                (project_dir / sub).mkdir(parents=True)

            data_venv = run_dir / ".venv-data"
            data_dir = run_dir / "data"
            data_venv.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            (run_dir / "juniper-data.pid").write_text("1\n")
            (run_dir / "juniper-cascor.pid").write_text("2\n")
            (project_dir / "juniper-cascor/src/snapshots/snapshot_20260809T000000Z.h5").write_text("x")
            (project_dir / "juniper-canopy/src/snapshots/snapshot_20260809T000001Z.h5").write_text("y")
            # The SHARED snapshot root. Teardown must not touch it: it is a project asset store
            # that outlives every stack, and a --down of one experiment deleting another
            # researcher's models is the failure this assertion exists to prevent.
            (project_dir / "juniper-cascor/cascor-snapshots/snapshot_20260809T000002Z.h5").write_text("keep")
            (project_dir / "juniper-cascor/cascor-snapshots/cascor_snapshot_20260813_010101_abc.h5").write_text("keep")
            # cascor's src/snapshots/ is a PYTHON PACKAGE: snapshot_*.py source modules
            # MUST survive teardown (a bare snapshot_* glob deleted them — the 4081f5b
            # over-deletion class, reproduced 2026-08-09).
            (project_dir / "juniper-cascor/src/snapshots/snapshot_cli.py").write_text("# source module")
            # Non-.h5 artifacts must survive the snapshot_*.h5 cleanup.
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
            # SHARED ROOT: never swept. Both naming schemes present in that directory are checked
            # because the tempting-but-wrong "fix" is to repoint the teardown glob at the new root,
            # and the service-tier name (snapshot_<ISO>Z.h5) is exactly what the old glob matched.
            self.assertTrue(
                (project_dir / "juniper-cascor/cascor-snapshots/snapshot_20260809T000002Z.h5").exists(),
                "the SHARED snapshot root must survive teardown -- it is a project asset store, " "not run scratch (storage-convention ruling 2026-08-20)",
            )
            self.assertTrue(
                (project_dir / "juniper-cascor/cascor-snapshots/cascor_snapshot_20260813_010101_abc.h5").exists(),
                "direct-CLI-named artifacts in the shared root must survive teardown too",
            )
            # cascor's src/snapshots/ receives no artifacts since the service moved to the shared
            # root, so teardown no longer sweeps it either. Pinned so a revert is visible.
            self.assertTrue(
                (project_dir / "juniper-cascor/src/snapshots/snapshot_20260809T000000Z.h5").exists(),
                "teardown must not sweep the serializer package directory",
            )
            self.assertFalse(
                (project_dir / "juniper-canopy/src/snapshots/snapshot_20260809T000001Z.h5").exists(),
                "canopy-local snapshot_*.h5 must be cleaned",
            )
            self.assertTrue(
                (project_dir / "juniper-cascor/src/snapshots/snapshot_cli.py").exists(),
                "snapshot_*.py SOURCE MODULES must survive teardown (4081f5b class)",
            )
            self.assertTrue(
                (project_dir / "juniper-cascor/src/snapshots/other.bin").exists(),
                "non-.h5 artifacts must be preserved",
            )


class TestDryRunStatus(unittest.TestCase):
    """``--dry-run --status`` announces probes and never curls or reads ss."""

    def test_dry_status_exit_zero_and_announces_all_three(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            result = _run(
                "--dry-run",
                "--status",
                env_extra={
                    "JUNIPER_E2E_PROJECT_DIR": "/opt/juniper-e2e-fixture",
                    "JUNIPER_E2E_RUN_DIR": str(run_dir),
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("juniper-data", result.stdout)
            self.assertIn("juniper-cascor", result.stdout)
            self.assertIn("juniper-canopy", result.stdout)
            # Dry-run short-circuits before the health= log line.
            self.assertNotIn("health=", result.stdout)
            self.assertFalse(run_dir.exists(), "dry-run --status must not create the scratch run dir")


class TestWaitForHealth(unittest.TestCase):
    """Behavioral pins for ``wait_for_health`` success / timeout arms.

    Live ``--up`` gates each service on this helper; a regression that skips the
    curl success arm or never times out leaves a partial trio hung (or proceeds
    against a dead endpoint). Extracted from the live script with a PATH-stubbed
    ``curl`` — no real network.
    """

    def _run_wait(self, *, curl_script: str, timeout: int = 2) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            curl = bin_dir / "curl"
            curl.write_text("#!/usr/bin/env bash\n" + curl_script)
            curl.chmod(0o755)
            harness = f"""
                set -euo pipefail
                SCRIPT_NAME="isolated_stack.bash"
                # Timeout ERROR line interpolates LOG_DIR under nounset.
                LOG_DIR="/tmp/isolated-stack-health-fixture"
                log() {{ echo "[${{SCRIPT_NAME}}] $*"; }}
                {_extract_wait_for_health()}
                set +e
                wait_for_health "juniper-data" "http://127.0.0.1:9/v1/health" "{timeout}"
                status=$?
                set -e
                echo "STATUS=${{status}}"
                exit 0
            """
            env = RedactedEnv(os.environ)
            env["PATH"] = str(bin_dir) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=HEALTH_HELPER_TIMEOUT_SECONDS,
            )

    def test_healthy_curl_returns_zero(self) -> None:
        result = self._run_wait(curl_script="exit 0\n", timeout=2)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=0", result.stdout)
        self.assertIn("juniper-data is healthy", result.stdout)
        self.assertNotIn("failed to become healthy", result.stdout)

    def test_persistent_failure_times_out(self) -> None:
        # timeout=2 with sleep 2 → one failed poll then the elapsed>=timeout arm.
        result = self._run_wait(curl_script="exit 22\n", timeout=2)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("STATUS=1", result.stdout)
        self.assertIn("failed to become healthy within 2s", result.stdout)
        # Success arm logs "is healthy (took Ns)" — must not appear on timeout.
        self.assertNotIn("is healthy (took", result.stdout)

    def test_data_cascor_canopy_up_wire_wait_for_health(self) -> None:
        # Drift guard: each bring-up path must gate on wait_for_health (not a
        # fire-and-forget nohup).
        self.assertIn(
            'wait_for_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health"',
            SCRIPT_TEXT,
        )
        self.assertIn(
            'wait_for_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health"',
            SCRIPT_TEXT,
        )
        self.assertIn(
            'wait_for_health "juniper-canopy" "http://127.0.0.1:${CANOPY_PORT}/v1/health"',
            SCRIPT_TEXT,
        )


class TestProbeHealth(unittest.TestCase):
    """Behavioral pins for ``probe_health`` live status arms.

    ``--status`` is the operator's only hermetic liveness check for the isolated
    trio; a regression that drops the curl code or ``port_pid`` field reports
    healthy when nothing listens (or vice versa). PATH-stubbed ``curl`` + ``ss``.
    """

    def _run_probe(
        self,
        *,
        curl_script: str,
        ss_script: str,
        dry_run: int = 0,
        port: str = "65101",
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            (bin_dir / "curl").write_text("#!/usr/bin/env bash\n" + curl_script)
            (bin_dir / "curl").chmod(0o755)
            (bin_dir / "ss").write_text("#!/usr/bin/env bash\n" + ss_script)
            (bin_dir / "ss").chmod(0o755)
            harness = f"""
                set -euo pipefail
                SCRIPT_NAME="isolated_stack.bash"
                DRY_RUN="{dry_run}"
                log() {{ echo "[${{SCRIPT_NAME}}] $*"; }}
                announce() {{ echo "[${{SCRIPT_NAME}}] \\$ $*"; }}
                is_dry() {{ [[ "${{DRY_RUN}}" == "1" ]]; }}
                {_extract_port_pid_for_probe()}
                {_extract_probe_health()}
                probe_health "juniper-data" "http://127.0.0.1:{port}/v1/health" "{port}"
            """
            env = RedactedEnv(os.environ)
            env["PATH"] = str(bin_dir) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_reports_http_code_and_listening_pid(self) -> None:
        # probe_health uses curl -w '%{http_code}'; stub prints the code on stdout.
        result = self._run_probe(
            curl_script="echo 200\n",
            ss_script=("echo 'LISTEN 0 128 127.0.0.1:65101 0.0.0.0:* " 'users:(("python",pid=424242,fd=3))\'\n'),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("juniper-data: health=200 port=65101 pid=424242", result.stdout)

    def test_curl_failure_reports_000_and_pid_none(self) -> None:
        # ``|| true`` + empty code → default 000; empty port_pid → pid=none.
        result = self._run_probe(curl_script="exit 7\n", ss_script="exit 0\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("juniper-data: health=000 port=65101 pid=none", result.stdout)

    def test_dry_run_short_circuits_before_curl(self) -> None:
        # Marker file proves curl was never executed under DRY_RUN=1.
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "curl_ran"
            curl_script = f'echo ran >"{marker}"\necho 200\n'
            result = self._run_probe(curl_script=curl_script, ss_script="exit 0\n", dry_run=1)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertFalse(marker.exists(), "dry-run probe_health must not invoke curl")
            self.assertNotIn("health=", result.stdout)

    def test_do_status_wires_probe_health_for_all_three_services(self) -> None:
        self.assertIn(
            'probe_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health" "${DATA_PORT}"',
            SCRIPT_TEXT,
        )
        self.assertIn(
            'probe_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health" "${CASCOR_PORT}"',
            SCRIPT_TEXT,
        )
        self.assertIn(
            'probe_health "juniper-canopy" "http://127.0.0.1:${CANOPY_PORT}/v1/health" "${CANOPY_PORT}"',
            SCRIPT_TEXT,
        )


# Full-script --up timeout: data_up compose + cascor fail-fast + do_down kill/cleanup.
DO_UP_PARTIAL_TIMEOUT_SECONDS = 30


class TestDoUpPartialFailureTeardown(unittest.TestCase):
    """``do_up`` must tear a partial trio back down when a later service fails.

    Pre-fix: under ``set -e``, a bare ``cascor_up`` / ``canopy_up`` failure exited
    the script immediately and left earlier listeners orphaned on the E2E ports.
    Mirrors experiment_stack's ``failed=1`` + teardown pattern.
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

    def test_cascor_missing_conda_tears_down_data_listener(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            run_dir = root / "run"
            listeners_dir = root / "listeners"
            marker_dir = root / "markers"
            stub_bin = root / "bin"
            conda_dir = root / "conda-missing"  # no etc/profile.d/conda.sh
            listeners_dir.mkdir()
            marker_dir.mkdir()
            stub_bin.mkdir()
            conda_dir.mkdir()
            for sub in (
                "juniper-data",
                "juniper-cascor/src/snapshots",
                "juniper-cascor/cascor-snapshots",
                "juniper-canopy/src/snapshots",
            ):
                (project_dir / sub).mkdir(parents=True)

            data_port = "65401"
            cascor_port = "65402"
            canopy_port = "65403"

            # python3.14 -m venv: minimal activatable venv; python records listener pid then sleeps.
            (stub_bin / "python3.14").write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                'if [[ "${1:-}" != "-m" || "${2:-}" != "venv" || -z "${3:-}" ]]; then\n'
                '  echo "unexpected python3.14 invocation: $*" >&2\n'
                "  exit 2\n"
                "fi\n"
                'dest="$3"\n'
                f'marker_dir="{marker_dir}"\n'
                f'listeners_dir="{listeners_dir}"\n'
                f'data_port="{data_port}"\n'
                'mkdir -p "$dest/bin"\n'
                'printf "VENV_CREATED\\n" >>"$marker_dir/venv.log"\n'
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
                "cat >\"$dest/bin/pip\" <<'PIP'\n"
                "#!/usr/bin/env bash\n"
                "exit 0\n"
                "PIP\n"
                "cat >\"$dest/bin/python\" <<'PY'\n"
                "#!/usr/bin/env bash\n"
                # Answer the free-threading probe (-c) without blocking; else act as the listener.
                'if [[ "${1-}" == "-c" ]]; then echo 1; exit 0; fi\n'
                f'printf "%s\\n" "$$" >"{listeners_dir}/{data_port}.pid"\n'
                "exec sleep 60\n"
                "PY\n"
                'chmod 755 "$dest/bin/pip" "$dest/bin/python"\n'
            )
            (stub_bin / "python3.14").chmod(0o755)
            (stub_bin / "curl").write_text("#!/usr/bin/env bash\nexit 0\n")
            (stub_bin / "curl").chmod(0o755)
            # ss → report whichever listener file matches the queried sport port.
            (stub_bin / "ss").write_text("#!/usr/bin/env bash\n" "set -euo pipefail\n" 'port=""\n' 'for a in "$@"; do\n' '  case "$a" in\n' '    sport\\ =\\ :*) port="${a##*:}" ;;\n' "  esac\n" "done\n" f'listener="{listeners_dir}/$port.pid"\n' 'if [[ -n "$port" && -f "$listener" ]]; then\n' '  pid="$(cat "$listener")"\n' '  echo "LISTEN 0 128 127.0.0.1:${port} 0.0.0.0:* users:((\\"python\\",pid=${pid},fd=3))"\n' "fi\n" "exit 0\n")
            (stub_bin / "ss").chmod(0o755)

            env = RedactedEnv(os.environ)
            env["JUNIPER_E2E_PROJECT_DIR"] = str(project_dir)
            env["JUNIPER_E2E_RUN_DIR"] = str(run_dir)
            env["JUNIPER_E2E_CONDA_DIR"] = str(conda_dir)
            env["JUNIPER_E2E_DATA_PORT"] = data_port
            env["JUNIPER_E2E_CASCOR_PORT"] = cascor_port
            env["JUNIPER_E2E_CANOPY_PORT"] = canopy_port
            env["JUNIPER_E2E_HEALTH_TIMEOUT"] = "4"
            env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "--up"],
                capture_output=True,
                text=True,
                env=env,
                timeout=DO_UP_PARTIAL_TIMEOUT_SECONDS,
            )
            child_pid: int | None = None
            listener = listeners_dir / f"{data_port}.pid"
            if listener.is_file():
                try:
                    child_pid = int(listener.read_text().strip())
                except ValueError:
                    child_pid = None
            try:
                self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("bring-up failed — tearing the partial trio back down", result.stdout)
                self.assertIn("conda not found at", result.stdout)
                self.assertIn("Teardown complete", result.stdout)
                # data_up must have launched before cascor failed.
                self.assertTrue((marker_dir / "venv.log").exists(), "data_up must run before cascor fails")
                # do_down clears pidfiles + venv; listener process must be killed via ss.
                self.assertFalse((run_dir / "juniper-data.pid").exists(), "do_down must clear data pidfile")
                self.assertFalse((run_dir / ".venv-data").exists(), "do_down must remove data venv")
                if child_pid is not None:
                    for _ in range(60):
                        if not Path(f"/proc/{child_pid}").exists():
                            break
                        time.sleep(0.1)
                    self.assertFalse(
                        Path(f"/proc/{child_pid}").exists(),
                        "partial teardown must kill the data listener",
                    )
            finally:
                if child_pid is not None:
                    self._force_kill(child_pid)


#: Source above this line is what the atomic-publish guard scans. Kept as a module
#: constant so the guard cannot match its own fixtures and report itself.
_GUARDED_SOURCE_END = "class TestStubMarkersArePublishedAtomically"


class TestStubMarkersArePublishedAtomically(unittest.TestCase):
    """Every ASYNCHRONOUSLY-published marker must be staged and moved, never written in place.

    ``_read_marker_when_written`` says outright that completeness is guaranteed by the
    WRITER, and that its trailing-newline check "cannot catch a truncated record that
    happens to end on a line boundary". CI proved the point on 2026-09-05: the three
    ``bin/python`` stubs wrote ``python.args`` straight to its final path, and a reader
    observed ``-m juniper_data --host 127.0.0.1 --port`` with the port value missing --
    a truncation ending exactly on a line boundary, invisible to the guard.

    **Scope is the async markers only.** These four are the ones read back through
    ``_read_marker_when_written``, i.e. written by a nohup-backgrounded stub that races
    the assertion. ``pip.log`` and ``venv.log`` are written by stubs the harness waits
    for and are read with a plain ``read_text()``; they are deliberately NOT covered,
    because widening the claim past the evidence would make this test assert a rule
    nobody has shown to matter there.

    Structural on purpose: the race is timing-dependent and will not reproduce on
    demand, so a behavioural test would pass for the wrong reason. Asserting that no
    stub writes an async marker in place is a property that holds or does not -- and it
    binds the stubs nobody has written yet, which is what the helper's docstring asks
    for.
    """

    #: Async markers by the literal shape their writer uses. ``python.*`` are written
    #: through ``{marker_dir}/<name>``; ``launch.log`` / ``env.log`` through an
    #: interpolated path variable, so both shapes have to be enumerated by hand --
    #: a guard that knew only the first shape would score six stubs and miss four.
    ASYNC_MARKER_PATTERNS = (
        (r'>"\{marker_dir\}/python\.args(?!\.partial)"', "python.args"),
        (r'>"\{marker_dir\}/python\.env(?!\.partial)"', "python.env"),
        (r'>"\{launch_log\}(?!\.partial)"', "launch.log"),
        (r'>"\{env_log\}(?!\.partial)"', "env.log"),
    )

    def _guarded_source(self) -> str:
        source = Path(__file__).read_text()
        return source[: source.index(_GUARDED_SOURCE_END)]

    def test_no_stub_writes_an_async_marker_to_its_final_path(self) -> None:
        source = self._guarded_source()
        offenders = []
        for pattern, name in self.ASYNC_MARKER_PATTERNS:
            for match in re.finditer(pattern, source):
                offenders.append((name, source.count("\n", 0, match.start()) + 1))
        self.assertEqual(
            offenders,
            [],
            "these stubs redirect an async marker straight to its final path; stage to " f"'<marker>.partial' and 'mv -f' it into place instead: {offenders}",
        )

    def test_every_async_marker_shape_is_actually_present_in_the_source(self) -> None:
        """The enumeration is checked separately from the predicate.

        A correct predicate over an enumeration that has gone stale reports clean
        forever. If a marker's writer is renamed or removed, this fails and says so,
        rather than the scan silently checking three shapes and calling it four.
        """
        source = self._guarded_source()
        for _pattern, name in self.ASYNC_MARKER_PATTERNS:
            self.assertIn(name, source, f"{name} no longer appears in the stub source -- update ASYNC_MARKER_PATTERNS")

    def test_the_scan_would_catch_a_direct_write(self) -> None:
        """Drive the predicate over a synthetic DIRTY input -- an empty result otherwise proves nothing."""
        pattern = self.ASYNC_MARKER_PATTERNS[0][0]
        self.assertRegex('printf "%s" "$@" >"{marker_dir}/python.args"', pattern)
        self.assertNotRegex('printf "%s" "$@" >"{marker_dir}/python.args.partial"', pattern)
