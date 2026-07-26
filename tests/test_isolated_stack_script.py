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
- ``wait_for_health`` / ``probe_health`` live arms (hermetic ``curl`` / ``ss``
  stubs) — the bring-up gate and ``--status`` reporter that prior dry-run
  tests never exercised.

``--dry-run`` short-circuits before any filesystem or process side effect, so
those behavioural tests are fully hermetic — no real repos, conda, or network.
``JUNIPER_E2E_PROJECT_DIR`` / ``JUNIPER_E2E_RUN_DIR`` pin paths deterministically.
The health cases extract live function bodies and stub ``curl``/``ss`` on
``PATH`` (keep ``/usr/bin:/bin`` for ``grep``/``cut``/``head``).
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
# wait_for_health sleeps 2s per poll; a 2s timeout needs one sleep → keep headroom.
HEALTH_HELPER_TIMEOUT_SECONDS = 20


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


if __name__ == "__main__":
    unittest.main()
