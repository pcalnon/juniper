"""
Tests for util/experiment_stack.bash

Contract + behavioural tests for the per-run experiment stack launcher (Wave 2.1 of
``notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md``).
The launcher's live ``--up`` path starts real juniper-data / juniper-cascor /
juniper-recurrence servers out of conda envs on real ports, so — as with
``test_isolated_stack_script.py`` and ``test_juniper_plant_all.py`` — this suite
NEVER brings a stack up, never touches docker, and never contacts the network. It
pins:

- ``bash -n`` cleanliness and the CLI misuse matrix (exit 2);
- the §9.3 port ranges and the §6.4 RUN_DIR contract by text inspection;
- the §6.1 launch recipes (exact env sets per service) by text inspection;
- **F-6**: pidfiles hold the LISTENER pid resolved from ``ss`` after the health
  gate — never the ``$!`` of the backgrounded ``cd … && nohup … &`` subshell;
- the §7.3 bridge: suffix-based ``_monitoring$`` network discovery, the exact
  socat relay command, relay pidfiles under ``RUN_DIR/relays/``;
- the §7.2 target file (rendered for real, parsed as JSON, four labels);
- the operator-safety invariants: no ``JuniperProject.pid``, no canopy, no repo
  ``.env`` write, no operator port;
- ``--dry-run --up`` behaviourally: every launch class printed with allocated
  ports expanded while the run root, the lock root and the targets dir stay
  untouched;
- ``allocate_port`` lockdir semantics with a stubbed ``ss``;
- teardown behaviourally: pidfile-first (a stubbed ``ss`` reports NO listener, so
  only the pidfile path can kill the process), target-file removal, lockdir
  release, and artifacts preserved.

Hermetic mechanics: ``JUNIPER_EXP_RUN_ROOT`` / ``JUNIPER_EXP_LOCK_ROOT`` /
``JUNIPER_EXP_DEPLOY_DIR`` / ``JUNIPER_EXP_PROJECT_DIR`` redirect every path into a
temp dir, ``JUNIPER_EXP_CONDA_DIR`` points at a fixture env tree, and
``ss``/``curl``/``docker``/``socat`` are PATH stubs (keep ``/usr/bin:/bin`` for
``mkdir``/``sed``/``stat``/``tr``). The only real processes any test creates are
detached ``sleep`` children it spawned itself and always reaps.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "experiment_stack.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 20
TEARDOWN_TIMEOUT_SECONDS = 45
DO_UP_PARTIAL_TIMEOUT_SECONDS = 45


def _strip_comment_lines(text: str) -> str:
    """Drop whole-line ``#`` comments so structural invariants test CODE, not prose.

    The script documents the very hazards these tests forbid (``JuniperProject.pid``,
    the operator ports, the ``$!`` wrapper-pid trap), so a naive substring assertion
    over the raw text would be tripped by its own documentation.
    """
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


SCRIPT_CODE = _strip_comment_lines(SCRIPT_TEXT)


def _extract_experiment_fn(name: str) -> str:
    """Pull a live ``<name>() { ... }`` body from experiment_stack.bash (no harness drift).

    Named distinctly from the sibling launcher suites' extractors so a merge can
    never silently alias the wrong helper.
    """
    match = re.search(
        rf"^{re.escape(name)}\(\) \{{.*?\n\}}\n",
        SCRIPT_TEXT,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"{name} function not found in experiment_stack.bash")
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


def _write_stub(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(0o755)


def _stage_stub_bin(root: Path, *, busy_ports: "list[int] | None" = None) -> Path:
    """PATH stub dir: ``ss`` (reports only ``busy_ports``), plus inert curl/docker/socat."""
    stub_bin = root / "path-stubs"
    stub_bin.mkdir(parents=True, exist_ok=True)
    busy = " ".join(str(port) for port in (busy_ports or []))
    # ss is called as `ss -tlnH "sport = :<port>"` / `ss -tlnpH "sport = :<port>"`;
    # echo a LISTEN line only for a port in the fixture's busy list.
    _write_stub(
        stub_bin / "ss",
        "#!/usr/bin/env bash\n" f'busy="{busy}"\n' 'want=""\n' 'for arg in "$@"; do\n' '  case "$arg" in\n' '    *sport*) want="${arg##*:}" ;;\n' "  esac\n" "done\n" "for port in $busy; do\n" '  if [[ "$port" == "$want" ]]; then\n' '    echo "LISTEN 0 128 127.0.0.1:${port} 0.0.0.0:* users:((\\"python\\",pid=424242,fd=3))"\n' "    exit 0\n" "  fi\n" "done\n" "exit 0\n",
    )
    _write_stub(stub_bin / "curl", "#!/usr/bin/env bash\nexit 0\n")
    _write_stub(stub_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
    _write_stub(stub_bin / "socat", "#!/usr/bin/env bash\nexec sleep 60\n")
    return stub_bin


def _stage_conda_fixture(root: Path) -> Path:
    """Fixture conda tree with the three env bins the launcher resolves directly."""
    conda_dir = root / "conda"
    for env_name, bins in (
        ("JuniperData", ("python",)),
        ("JuniperCascor1", ("uvicorn", "juniper-recurrence")),
    ):
        bin_dir = conda_dir / "envs" / env_name / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        for bin_name in bins:
            _write_stub(bin_dir / bin_name, "#!/usr/bin/env bash\nexec sleep 60\n")
    return conda_dir


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

    def test_strict_mode_and_nounset_guard(self) -> None:
        self.assertIn("set -euo pipefail", SCRIPT_TEXT)
        # Fail-closed activate: +u around activate, -u restored on BOTH success
        # and failure arms (a +u/+u restore silently disables nounset; a bare
        # ``conda activate`` failure + successful ``set -u`` masks OR-list callers).
        body = _extract_experiment_fn("activate_conda")
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


class TestPortRanges(unittest.TestCase):
    """The §9.3 experiment ranges, verbatim and disjoint from every operator port."""

    def test_ranges_match_plan_section_9_3(self) -> None:
        for line in (
            "DATA_PORT_MIN=8110",
            "DATA_PORT_MAX=8139",
            "CASCOR_PORT_MIN=8230",
            "CASCOR_PORT_MAX=8259",
            "RECURRENCE_PORT_MIN=8260",
            "RECURRENCE_PORT_MAX=8289",
        ):
            self.assertIn(line, SCRIPT_TEXT, msg=f"missing §9.3 range constant: {line}")

    def test_no_operator_port_anywhere(self) -> None:
        # 8100 data / 8200 cascor default / 8201 operator cascor / 8210 recurrence
        # default + worker health / 8050 + 8051 canopy must never appear.
        for port in ("8050", "8051", "8100", "8200", "8201", "8210"):
            self.assertNotRegex(
                SCRIPT_CODE,
                rf"(?<![0-9]){port}(?![0-9])",
                msg=f"operator port {port} must never appear in the experiment launcher",
            )


class TestOperatorSafetyInvariants(unittest.TestCase):
    """The plan §9.1 hazards this launcher must be structurally incapable of hitting."""

    def test_never_references_juniper_project_pid(self) -> None:
        # H-10: JuniperProject.pid belongs to juniper_plant_all.bash / juniper_chop_all.bash.
        self.assertNotIn("JuniperProject.pid", SCRIPT_CODE)

    def test_never_starts_canopy(self) -> None:
        self.assertNotIn("canopy_up", SCRIPT_CODE)
        self.assertNotIn("JUNIPER_CANOPY_", SCRIPT_CODE)

    def test_never_writes_a_dot_env(self) -> None:
        # H-3: cascor loads .env from CWD, so the launcher passes process env only.
        # (RUN_DIR/env/launch.env is a run record, not a dotfile a pydantic-settings
        # source would ever load — the guard targets `/.env` and bare `.env` writes.)
        self.assertNotRegex(SCRIPT_TEXT, r">>?\s*\"?[^\"\n]*/\.env\b")
        self.assertNotRegex(SCRIPT_TEXT, r">>?\s*\"?\.env\b")

    def test_teardown_never_deletes_artifacts(self) -> None:
        teardown = _extract_experiment_fn("teardown_run")
        self.assertNotIn("rm -rf", teardown)
        self.assertIn("artifacts kept", teardown)


class TestRunDirContract(unittest.TestCase):
    """§6.2 run identity + §6.4 RUN_DIR layout."""

    def test_run_root_is_durable_state_not_tmp(self) -> None:
        # H-15: results must survive a reaped sandbox, so RUN_ROOT is under $HOME.
        self.assertIn('RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"', SCRIPT_TEXT)

    def test_lock_root_is_ephemeral_runtime_state(self) -> None:
        self.assertIn('LOCK_ROOT="${JUNIPER_EXP_LOCK_ROOT:-${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments}"', SCRIPT_TEXT)

    def test_run_id_is_utc_timestamp_plus_four_hex(self) -> None:
        new_run_id = _extract_experiment_fn("new_run_id")
        self.assertIn("date -u +%Y%m%dT%H%M%SZ", new_run_id)
        self.assertIn("openssl rand -hex 2", new_run_id)

    def test_run_dir_layout_matches_section_6_4(self) -> None:
        create = _extract_experiment_fn("create_run_dir")
        for subdir in ("logs", "relays", "config", "env", "data", "equities-cache", "artifacts/plots", "artifacts/results"):
            self.assertIn(subdir, create, msg=f"§6.4 run-dir subdir missing: {subdir}")

    def test_pidfiles_live_in_the_run_dir(self) -> None:
        self.assertIn('"${RUN_DIR}/${svc}.pid"', SCRIPT_TEXT)

    def test_ports_json_written_before_launch(self) -> None:
        do_up = _extract_experiment_fn("do_up")
        self.assertLess(
            do_up.index("write_ports_json"),
            do_up.index("data_up"),
            msg="ports.json must be written before any launch so a partial run is still teardown-able",
        )


class TestLaunchLines(unittest.TestCase):
    """The §6.1 canonical recipes, env set by env set."""

    def test_direct_env_bin_launch_form(self) -> None:
        self.assertIn("printf '%s' \"${CONDA_DIR}/envs/${env_name}/bin/${bin_name}\"", SCRIPT_TEXT)
        self.assertIn('CONDA_DIR="${JUNIPER_EXP_CONDA_DIR:-/opt/miniforge3}"', SCRIPT_TEXT)

    def test_data_launch_recipe(self) -> None:
        data_up = _extract_experiment_fn("data_up")
        self.assertIn("JUNIPER_DATA_STORAGE_PATH", data_up)
        self.assertIn("JUNIPER_DATA_METRICS_ENABLED=true", data_up)
        self.assertIn("JUNIPER_DATA_EQUITIES_CACHE_DIR", data_up)
        self.assertIn("PYTHON_GIL=0", data_up)
        self.assertIn("-m juniper_data --host 127.0.0.1 --port", data_up)
        self.assertIn("/v1/health", data_up)

    def test_cascor_launch_recipe(self) -> None:
        cascor_up = _extract_experiment_fn("cascor_up")
        # The uvicorn CLI owns the bind, so experiment YAML can never override it (§6.1).
        self.assertIn("api.app:create_app --factory --host 127.0.0.1 --port", cascor_up)
        self.assertIn("LD_LIBRARY_PATH=''", cascor_up)
        self.assertIn("JUNIPER_CASCOR_METRICS_ENABLED=true", cascor_up)
        self.assertIn("JUNIPER_CASCOR_AUTO_START=false", cascor_up)
        self.assertIn("JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false", cascor_up)
        self.assertIn('JUNIPER_DATA_URL="${DATA_URL}"', cascor_up)
        self.assertIn('cd "${CASCOR_SRC_DIR}"', cascor_up)

    def test_recurrence_launch_recipe(self) -> None:
        recurrence_up = _extract_experiment_fn("recurrence_up")
        self.assertIn("serve --host 127.0.0.1 --port", recurrence_up)
        self.assertIn("JUNIPER_RECURRENCE_METRICS_ENABLED=true", recurrence_up)
        self.assertIn("JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false", recurrence_up)
        self.assertIn('JUNIPER_DATA_URL="${DATA_URL}"', recurrence_up)
        # Recurrence is the /v1/health/ready service (heavy import stack).
        self.assertIn("/v1/health/ready", recurrence_up)

    def test_health_timeout_sized_for_cold_start(self) -> None:
        # F-8: 90 s default; the 1.1 s warm number is NOT the design point.
        self.assertIn('HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-90}"', SCRIPT_TEXT)

    def test_bring_up_order_is_data_cascor_recurrence(self) -> None:
        do_up = _extract_experiment_fn("do_up")
        self.assertLess(do_up.index("data_up"), do_up.index("cascor_up"))
        self.assertLess(do_up.index("cascor_up"), do_up.index("recurrence_up"))


class TestListenerPidRule(unittest.TestCase):
    """F-6: the pidfile holds the LISTENER pid, resolved from ss after the health gate.

    ``$!`` taken after ``( cd … && nohup <server> … & )`` is the backgrounded
    SUBSHELL, not the server — the Wave 0 preflight proved all three such "recorded"
    pids died on signal while the servers lived on. A regression that reintroduces
    the ``$!`` form silently breaks every teardown.
    """

    def test_record_listener_pid_uses_ss(self) -> None:
        record = _extract_experiment_fn("record_listener_pid")
        self.assertIn("port_listener_pid", record)
        self.assertIn('"${RUN_DIR}/${svc}.pid"', record)
        # The cmdline is recorded so teardown can prove identity before killing.
        self.assertIn("proc_cmdline", record)

    def test_ss_listener_query_idiom(self) -> None:
        port_listener_pid = _extract_experiment_fn("port_listener_pid")
        self.assertIn('ss -tlnpH "sport = :${port}"', port_listener_pid)
        self.assertIn("pid=[0-9]+", port_listener_pid)

    def test_no_service_pidfile_is_written_from_bang_bang(self) -> None:
        for fn_name in ("data_up", "cascor_up", "recurrence_up"):
            body = _strip_comment_lines(_extract_experiment_fn(fn_name))
            self.assertNotIn('echo "$!"', body, msg=f"{fn_name} must not record the subshell pid (F-6)")
            self.assertNotIn("$!", body, msg=f"{fn_name} must not reference $! at all (F-6)")

    def test_every_service_records_its_listener_after_the_health_gate(self) -> None:
        for fn_name in ("data_up", "cascor_up", "recurrence_up"):
            # Code-only: prose in comments may mention the helper names out of order.
            body = _strip_comment_lines(_extract_experiment_fn(fn_name))
            self.assertIn("record_listener_pid", body, msg=f"{fn_name} must record a listener pid")
            self.assertLess(
                body.index("wait_for_health"),
                body.index("record_listener_pid"),
                msg=f"{fn_name} must resolve the listener pid AFTER the health gate (F-6)",
            )

    def test_teardown_verifies_owner_and_cmdline_before_killing(self) -> None:
        kill_verified = _extract_experiment_fn("kill_verified_pid")
        self.assertIn("kill -0", kill_verified)
        self.assertIn("stat -c '%u'", kill_verified)
        self.assertIn("$(id -u)", kill_verified)
        self.assertIn("refusing to kill", kill_verified)
        terminate = _extract_experiment_fn("terminate_pid")
        self.assertIn("kill -TERM", terminate)
        self.assertIn("kill -KILL", terminate)
        self.assertLess(terminate.index("kill -TERM"), terminate.index("kill -KILL"))


class TestGrafanaBridge(unittest.TestCase):
    """§7.3 relay + gateway discovery, opt-in only."""

    def test_monitoring_network_discovered_by_suffix(self) -> None:
        discover = _extract_experiment_fn("discover_gateway_ip")
        # Compose projects launched from a worktree rename the network, so the
        # discovery is by SUFFIX, never by a hard-coded project name.
        self.assertIn("grep -E '_monitoring$'", discover)
        self.assertNotIn("juniper-deploy_monitoring", discover)

    def test_default_bridge_fallback_is_loud(self) -> None:
        discover = _extract_experiment_fn("discover_gateway_ip")
        self.assertIn("docker network inspect bridge", discover)
        self.assertIn("WARNING", discover)

    def test_relay_command_matches_plan_section_7_3(self) -> None:
        relay_up = _extract_experiment_fn("relay_up")
        self.assertIn(
            'socat "TCP-LISTEN:${port},bind=${GATEWAY_IP},fork,reuseaddr" "TCP:127.0.0.1:${port}"',
            relay_up,
        )
        self.assertIn('"${RUN_DIR}/relays/${svc}.pid"', relay_up)

    def test_socat_preflight_only_when_bridge_requested(self) -> None:
        bridge_up = _extract_experiment_fn("bridge_up")
        self.assertIn("require_cmd socat", bridge_up)
        do_up = _extract_experiment_fn("do_up")
        self.assertNotIn("require_cmd socat", do_up)
        self.assertIn("WANT_BRIDGE == 1", do_up)
        self.assertIn("UNSCRAPED", do_up)

    def test_target_file_lives_in_the_deploy_targets_dir(self) -> None:
        # F-3: prometheus/targets/ is already inside the existing :ro mount.
        self.assertIn('TARGETS_DIR="${DEPLOY_DIR}/prometheus/targets"', SCRIPT_TEXT)
        self.assertIn('DEPLOY_DIR="${JUNIPER_EXP_DEPLOY_DIR:-${PROJECT_DIR}/juniper-deploy}"', SCRIPT_TEXT)

    def test_target_file_removed_at_teardown(self) -> None:
        bridge_down = _extract_experiment_fn("bridge_down")
        self.assertIn('rm -f "${TARGETS_DIR}/${TARGET_RUN_ID}.json"', bridge_down)


class TestTargetFileShape(unittest.TestCase):
    """§7.2: the rendered file_sd target must be valid JSON with the four labels."""

    def _render(self, targets: "list[str]", run_id: str, experiment: str) -> str:
        array = " ".join(f'"{entry}"' for entry in targets)
        harness = "set -euo pipefail\n" f'RUN_ID="{run_id}"\n' f'EXPERIMENT="{experiment}"\n' f"SCRAPE_TARGETS=({array})\n" + _extract_experiment_fn("render_target_file") + "render_target_file\n"
        result = subprocess.run(
            ["/bin/bash", "-c", harness],
            capture_output=True,
            text=True,
            env=RedactedEnv(os.environ),
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return result.stdout

    def test_rendered_targets_parse_as_json_with_plan_labels(self) -> None:
        rendered = self._render(["juniper-data:8110", "juniper-cascor:8230"], "20260730T000000Z-abcd", "spiral-baseline")
        parsed = json.loads(rendered)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["targets"], ["host.docker.internal:8110"])
        self.assertEqual(parsed[1]["targets"], ["host.docker.internal:8230"])
        for entry, service in zip(parsed, ("juniper-data", "juniper-cascor")):
            self.assertEqual(
                sorted(entry["labels"]),
                ["environment", "experiment", "run_id", "service"],
                msg="the §7.2 label set is exactly service/environment/run_id/experiment",
            )
            self.assertEqual(entry["labels"]["service"], service)
            # Parallels the existing docker / docker-demo values so dashboards can filter.
            self.assertEqual(entry["labels"]["environment"], "host-experiment")
            self.assertEqual(entry["labels"]["run_id"], "20260730T000000Z-abcd")
            self.assertEqual(entry["labels"]["experiment"], "spiral-baseline")

    def test_single_target_still_valid_json(self) -> None:
        parsed = json.loads(self._render(["juniper-recurrence:8260"], "20260730T000000Z-beef", "adhoc"))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["labels"]["service"], "juniper-recurrence")


class TestDocumentedOverrides(unittest.TestCase):
    """The header docstring must advertise every env override the script honours."""

    def test_env_overrides_documented(self) -> None:
        for var in (
            "JUNIPER_EXP_RUN_ROOT",
            "JUNIPER_EXP_LOCK_ROOT",
            "JUNIPER_EXP_PROJECT_DIR",
            "JUNIPER_EXP_DEPLOY_DIR",
            "JUNIPER_EXP_CONDA_DIR",
            "JUNIPER_EXP_HEALTH_TIMEOUT",
            "JUNIPER_EXP_KILL_TIMEOUT",
        ):
            self.assertIn(var, SCRIPT_TEXT)


class TestHelpAndErrors(unittest.TestCase):
    """CLI surface: help exits 0; every misuse exits 2."""

    def test_help_exits_zero(self) -> None:
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)

    def test_no_action_exits_two(self) -> None:
        self.assertEqual(_run().returncode, 2)

    def test_unknown_flag_exits_two(self) -> None:
        self.assertEqual(_run("--bogus").returncode, 2)

    def test_two_actions_exit_two(self) -> None:
        self.assertEqual(_run("--up", "--down").returncode, 2)

    def test_up_without_app_selector_exits_two(self) -> None:
        result = _run("--up")
        self.assertEqual(result.returncode, 2)
        self.assertIn("at least one app selector", result.stdout)

    def test_up_with_a_run_id_exits_two(self) -> None:
        self.assertEqual(_run("--up", "--cascor", "20260730T000000Z-abcd").returncode, 2)

    def test_down_without_run_id_exits_two(self) -> None:
        result = _run("--down")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs a RUN_ID", result.stdout)

    def test_down_with_run_id_and_all_mine_exits_two(self) -> None:
        self.assertEqual(_run("--down", "20260730T000000Z-abcd", "--all-mine").returncode, 2)

    def test_value_flag_without_value_exits_two(self) -> None:
        for flag in ("--config", "--experiment", "--shared-data"):
            self.assertEqual(_run(flag).returncode, 2, msg=f"{flag} with no value must exit 2")


class _DryRunHarness(unittest.TestCase):
    """Temp run/lock/deploy roots + PATH stubs so a dry run is fully hermetic."""

    def _env(self, root: Path, stub_bin: Path, conda_dir: Path) -> "dict[str, str]":
        env = {
            "JUNIPER_EXP_RUN_ROOT": str(root / "runs"),
            "JUNIPER_EXP_LOCK_ROOT": str(root / "locks"),
            "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
            "JUNIPER_EXP_PROJECT_DIR": "/opt/juniper-exp-fixture",
            "JUNIPER_EXP_CONDA_DIR": str(conda_dir),
            "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
        }
        return env

    def _dry_up(self, root: Path, *args: str, busy_ports: "list[int] | None" = None) -> subprocess.CompletedProcess:
        stub_bin = _stage_stub_bin(root, busy_ports=busy_ports)
        conda_dir = _stage_conda_fixture(root)
        return _run("--dry-run", "--up", *args, env_extra=self._env(root, stub_bin, conda_dir))


class TestDryRunUp(_DryRunHarness):
    """``--dry-run --up`` prints every launch class with ports expanded, and creates NOTHING."""

    def test_dry_up_exit_zero_and_prints_all_three_launch_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self._dry_up(root, "--cascor", "--recurrence")
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            out = result.stdout
            # data (§6.1): dedicated per-run instance, free-threaded, per-run storage.
            self.assertIn("-m juniper_data --host 127.0.0.1 --port 8110", out)
            self.assertIn("PYTHON_GIL=0", out)
            self.assertIn("JUNIPER_DATA_METRICS_ENABLED=true", out)
            # cascor (§6.1): uvicorn factory owns the bind.
            self.assertIn("api.app:create_app --factory --host 127.0.0.1 --port 8230", out)
            self.assertIn("LD_LIBRARY_PATH=", out)
            self.assertIn("JUNIPER_CASCOR_METRICS_ENABLED=true", out)
            self.assertIn("JUNIPER_DATA_URL=http://127.0.0.1:8110", out)
            # recurrence (§6.1): the env's console script.
            self.assertIn("serve --host 127.0.0.1 --port 8260", out)
            self.assertIn("JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false", out)

    def test_dry_up_uses_the_fixture_env_bins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._dry_up(root, "--cascor", "--recurrence").stdout
            self.assertIn(str(root / "conda" / "envs" / "JuniperData" / "bin" / "python"), out)
            self.assertIn(str(root / "conda" / "envs" / "JuniperCascor1" / "bin" / "uvicorn"), out)
            self.assertIn(str(root / "conda" / "envs" / "JuniperCascor1" / "bin" / "juniper-recurrence"), out)

    def test_dry_up_touches_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._dry_up(root, "--cascor", "--recurrence", "--grafana-bridge")
            self.assertFalse((root / "runs").exists(), "dry-run --up must not create the run root")
            self.assertFalse((root / "locks").exists(), "dry-run --up must not create the lock root")
            self.assertFalse((root / "deploy").exists(), "dry-run --up must not create the targets dir")

    def test_dry_up_bridge_prints_relay_and_target_but_writes_neither(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._dry_up(root, "--recurrence", "--grafana-bridge", "--experiment", "smoke").stdout
            self.assertIn("grep -E '_monitoring$'", out)
            self.assertIn('socat "TCP-LISTEN:8110,bind=<monitoring-gateway>,fork,reuseaddr" "TCP:127.0.0.1:8110"', out)
            self.assertIn('socat "TCP-LISTEN:8260,bind=<monitoring-gateway>,fork,reuseaddr" "TCP:127.0.0.1:8260"', out)
            self.assertIn("prometheus/targets/", out)
            self.assertFalse((root / "deploy").exists())

    def test_dry_up_without_bridge_says_the_run_is_unscraped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(Path(tmp), "--recurrence").stdout
            self.assertIn("UNSCRAPED", out)
            self.assertNotIn("socat", out)

    def test_dry_up_skips_ports_reported_busy_by_ss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(Path(tmp), "--cascor", busy_ports=[8110, 8111, 8230]).stdout
            self.assertIn("allocated juniper-data port 8112", out)
            self.assertIn("allocated juniper-cascor port 8231", out)

    def test_dry_up_shared_data_skips_the_data_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._dry_up(Path(tmp), "--cascor", "--shared-data", "http://127.0.0.1:8100").stdout
            self.assertIn("Reusing shared juniper-data at http://127.0.0.1:8100", out)
            self.assertNotIn("-m juniper_data", out)
            self.assertIn("JUNIPER_DATA_URL=http://127.0.0.1:8100", out)


class TestAllocatePort(unittest.TestCase):
    """Lockdir + ``ss`` probe allocation (§6.2), driven against the live function body."""

    def _run_allocate(self, *, lock_root: Path, busy_ports: "list[int]", low: int = 8110, high: int = 8112) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            stub_bin = _stage_stub_bin(Path(tmp), busy_ports=busy_ports)
            harness = "set -euo pipefail\n" 'SCRIPT_NAME="experiment_stack.bash"\n' "DRY_RUN=0\n" f'LOCK_ROOT="{lock_root}"\n' "HELD_LOCK_PORTS=()\n" 'log() { echo "[${SCRIPT_NAME}] $*"; }\n' 'is_dry() { [[ "${DRY_RUN}" == "1" ]]; }\n' + _extract_experiment_fn("port_in_use") + _extract_experiment_fn("allocate_port") + f'allocate_port "juniper-data" {low} {high}\n' 'printf "PORT=%s\\n" "${ALLOCATED_PORT}"\n' 'printf "HELD=%s\\n" "${HELD_LOCK_PORTS[*]:-}"\n'
            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_takes_the_first_free_port_and_holds_its_lockdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_root = Path(tmp) / "locks"
            lock_root.mkdir()
            result = self._run_allocate(lock_root=lock_root, busy_ports=[])
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("PORT=8110", result.stdout)
            self.assertIn("HELD=8110", result.stdout)
            self.assertTrue((lock_root / "8110.lock").is_dir(), "the allocated port's lockdir must be held")

    def test_skips_a_port_another_launcher_already_locked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_root = Path(tmp) / "locks"
            (lock_root / "8110.lock").mkdir(parents=True)
            result = self._run_allocate(lock_root=lock_root, busy_ports=[])
            self.assertIn("PORT=8111", result.stdout)
            self.assertTrue((lock_root / "8111.lock").is_dir())

    def test_releases_the_lockdir_when_the_port_is_already_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_root = Path(tmp) / "locks"
            lock_root.mkdir()
            result = self._run_allocate(lock_root=lock_root, busy_ports=[8110])
            self.assertIn("PORT=8111", result.stdout)
            self.assertFalse((lock_root / "8110.lock").exists(), "a lock taken over a bound port must be released")

    def test_exhausted_range_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_root = Path(tmp) / "locks"
            lock_root.mkdir()
            result = self._run_allocate(lock_root=lock_root, busy_ports=[8110, 8111, 8112])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no free juniper-data port in 8110-8112", result.stdout)


class TestTeardownBehaviour(unittest.TestCase):
    """``--down`` behaviourally: pidfile FIRST, target file removed, locks released.

    The stubbed ``ss`` reports NO listener, so the kill-by-port fallback is inert —
    the recorded process can only die through the pidfile path. That is the whole
    point of F-6 plus the plan's "kill by recorded pid first" rule.
    """

    def _spawn_detached(self) -> int:
        launcher = "setsid bash -c 'exec sleep 120' </dev/null >/dev/null 2>&1 & echo $!"
        result = subprocess.run(["/bin/bash", "-c", launcher], capture_output=True, text=True, timeout=SCRIPT_TIMEOUT_SECONDS)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        pid = int(result.stdout.strip().splitlines()[-1])
        time.sleep(0.2)
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

    @staticmethod
    def _proc_cmdline(pid: int) -> str:
        return Path(f"/proc/{pid}/cmdline").read_bytes().decode().replace("\0", " ")

    def test_pidfile_first_teardown_removes_target_and_releases_locks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "20260730T000000Z-abcd"
            run_root = root / "runs"
            lock_root = root / "locks"
            targets_dir = root / "deploy" / "prometheus" / "targets"
            run_dir = run_root / run_id
            (run_dir / "artifacts" / "results").mkdir(parents=True)
            (run_dir / "logs").mkdir()
            targets_dir.mkdir(parents=True)
            (lock_root / "8110.lock").mkdir(parents=True)
            (lock_root / "8260.lock").mkdir(parents=True)
            (targets_dir / f"{run_id}.json").write_text("[]\n")
            keeper = run_dir / "artifacts" / "results" / "metrics_final.json"
            keeper.write_text("{}\n")
            (run_dir / "ports.json").write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "data": 8110,
                        "cascor": None,
                        "recurrence": 8260,
                        "data_url": "http://127.0.0.1:8110",
                        "experiment": "smoke",
                        "grafana_bridge": True,
                    },
                    indent=2,
                )
                + "\n"
            )

            pid = self._spawn_detached()
            try:
                (run_dir / "juniper-recurrence.pid").write_text(f"{pid}\n")
                (run_dir / "juniper-recurrence.cmdline").write_text(self._proc_cmdline(pid))

                stub_bin = _stage_stub_bin(root, busy_ports=[])
                env = {
                    "JUNIPER_EXP_RUN_ROOT": str(run_root),
                    "JUNIPER_EXP_LOCK_ROOT": str(lock_root),
                    "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
                    "JUNIPER_EXP_KILL_TIMEOUT": "5",
                    "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
                }
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT_PATH), "--down", run_id],
                    capture_output=True,
                    text=True,
                    env=RedactedEnv(os.environ, **env),
                    timeout=TEARDOWN_TIMEOUT_SECONDS,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)

                # Pidfile path ran BEFORE the port fallback for the same service.
                out = result.stdout
                self.assertLess(
                    out.index("recorded listener pid first"),
                    out.index("fallback, ONLY this run's recorded port"),
                    msg="teardown must try the recorded pid before any kill-by-port",
                )
                # The recorded process is gone (only the pidfile path could kill it —
                # the stubbed ss reports no listener at all).
                for _ in range(60):
                    if not Path(f"/proc/{pid}").exists():
                        break
                    time.sleep(0.1)
                self.assertFalse(Path(f"/proc/{pid}").exists(), "teardown must kill the recorded listener pid")

                self.assertFalse((run_dir / "juniper-recurrence.pid").exists(), "pidfile must be cleared")
                self.assertFalse((targets_dir / f"{run_id}.json").exists(), "the Prometheus target file must be removed")
                self.assertFalse((lock_root / "8110.lock").exists(), "the data port lockdir must be released")
                self.assertFalse((lock_root / "8260.lock").exists(), "the recurrence port lockdir must be released")
                self.assertTrue(keeper.exists(), "teardown must NEVER delete artifacts/")
                teardown = json.loads((run_dir / "teardown.json").read_text())
                self.assertEqual(teardown["run_id"], run_id)
                self.assertIn("juniper-recurrence", teardown["services_stopped"])
                self.assertIn(8110, teardown["ports_released"])
            finally:
                self._force_kill(pid)

    def test_refuses_a_pid_whose_cmdline_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "20260730T000000Z-beef"
            run_root = root / "runs"
            run_dir = run_root / run_id
            run_dir.mkdir(parents=True)
            (run_dir / "ports.json").write_text(json.dumps({"run_id": run_id, "data": None, "cascor": None, "recurrence": 8260}) + "\n")

            pid = self._spawn_detached()
            try:
                (run_dir / "juniper-recurrence.pid").write_text(f"{pid}\n")
                # A pid-reuse forgery: the recorded cmdline does not match the live one.
                (run_dir / "juniper-recurrence.cmdline").write_text("some other process ")

                stub_bin = _stage_stub_bin(root, busy_ports=[])
                env = {
                    "JUNIPER_EXP_RUN_ROOT": str(run_root),
                    "JUNIPER_EXP_LOCK_ROOT": str(root / "locks"),
                    "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
                    "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
                }
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT_PATH), "--down", run_id],
                    capture_output=True,
                    text=True,
                    env=RedactedEnv(os.environ, **env),
                    timeout=TEARDOWN_TIMEOUT_SECONDS,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("cmdline changed since launch", result.stdout)
                self.assertTrue(Path(f"/proc/{pid}").exists(), "a mismatched cmdline must NOT be killed")
            finally:
                self._force_kill(pid)

    def test_down_on_a_missing_run_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run("--down", "20260730T000000Z-none", env_extra={"JUNIPER_EXP_RUN_ROOT": str(Path(tmp) / "runs")})
            self.assertEqual(result.returncode, 1)
            self.assertIn("no such run dir", result.stdout)


class TestStatus(unittest.TestCase):
    """``--status`` reports ports, pids, and whether the run is scraped."""

    def _status(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        stub_bin = _stage_stub_bin(root, busy_ports=[])
        env = {
            "JUNIPER_EXP_RUN_ROOT": str(root / "runs"),
            "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
            "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
        }
        return _run("--status", *args, env_extra=env)

    def _make_run(self, root: Path, run_id: str, *, bridge: bool) -> Path:
        run_dir = root / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "ports.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "data": 8110,
                    "cascor": 8230,
                    "recurrence": None,
                    "data_url": "http://127.0.0.1:8110",
                    "experiment": "smoke",
                    "grafana_bridge": bridge,
                },
                indent=2,
            )
            + "\n"
        )
        return run_dir

    def test_status_reports_unscraped_when_the_bridge_is_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_run(root, "20260730T000000Z-abcd", bridge=False)
            result = self._status(root, "20260730T000000Z-abcd")
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("UNSCRAPED", result.stdout)
            self.assertIn("port=8110", result.stdout)
            self.assertIn("port=8230", result.stdout)

    def test_status_reports_published_when_the_target_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "20260730T000000Z-abcd"
            self._make_run(root, run_id, bridge=True)
            targets = root / "deploy" / "prometheus" / "targets"
            targets.mkdir(parents=True)
            (targets / f"{run_id}.json").write_text("[]\n")
            self.assertIn("scrape: PUBLISHED", self._status(root, run_id).stdout)

    def test_status_flags_a_missing_target_file_as_unscraped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "20260730T000000Z-abcd"
            self._make_run(root, run_id, bridge=True)
            self.assertIn("UNSCRAPED", self._status(root, run_id).stdout)

    def test_status_with_no_run_id_lists_every_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_run(root, "20260730T000000Z-aaaa", bridge=False)
            self._make_run(root, "20260730T000000Z-bbbb", bridge=False)
            out = self._status(root).stdout
            self.assertIn("20260730T000000Z-aaaa", out)
            self.assertIn("20260730T000000Z-bbbb", out)


class TestConfigStaging(unittest.TestCase):
    """``--config`` stages the YAML into the run dir (§6.4) without inventing app flags."""

    def test_config_copied_and_exported_to_cascor(self) -> None:
        stage_config = _extract_experiment_fn("stage_config")
        self.assertIn('cp "${CONFIG_PATH}" "${RUN_DIR}/config/experiment.yaml"', stage_config)
        cascor_up = _extract_experiment_fn("cascor_up")
        self.assertIn("JUNIPER_CASCOR_CONFIG_FILE", cascor_up)

    def test_recurrence_never_passes_an_unsupported_config_flag(self) -> None:
        # `juniper-recurrence serve` has no --config flag until Wave 3.3; passing one
        # would be an argparse error at launch, so the launcher stages and says so.
        recurrence_up = _extract_experiment_fn("recurrence_up")
        self.assertNotIn("serve --config", recurrence_up)
        self.assertIn("Wave 3.3", recurrence_up)


class TestOrListFailClosedPins(unittest.TestCase):
    """Static pins: ``*_up || failed=1`` disables set -e — critical steps must ``|| return 1``."""

    def test_service_up_critical_steps_return_1(self) -> None:
        data_up = _extract_experiment_fn("data_up")
        cascor_up = _extract_experiment_fn("cascor_up")
        recurrence_up = _extract_experiment_fn("recurrence_up")
        # OR-list invocation disables set -e inside each *_up — critical steps must
        # ``|| return 1`` or a mid-function failure false-greens via a later success.
        self.assertIn('require_env_bin "${DATA_CONDA}" python || return 1', data_up)
        self.assertIn(
            'wait_for_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health" || return 1',
            data_up,
        )
        self.assertIn('record_listener_pid "juniper-data" "${DATA_PORT}" || return 1', data_up)
        self.assertIn('activate_conda "${DATA_CONDA}" || return 1', data_up)

        self.assertIn('require_env_bin "${CASCOR_CONDA}" uvicorn || return 1', cascor_up)
        self.assertIn(
            'wait_for_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health" || return 1',
            cascor_up,
        )
        self.assertIn('activate_conda "${CASCOR_CONDA}" || return 1', cascor_up)

        self.assertIn('require_env_bin "${RECURRENCE_CONDA}" juniper-recurrence || return 1', recurrence_up)
        self.assertIn(
            'wait_for_health "juniper-recurrence" "http://127.0.0.1:${RECURRENCE_PORT}/v1/health/ready" || return 1',
            recurrence_up,
        )
        self.assertIn('activate_conda "${RECURRENCE_CONDA}" || return 1', recurrence_up)

    def test_bridge_up_and_do_up_teardown_on_bridge_failure(self) -> None:
        bridge_up = _extract_experiment_fn("bridge_up")
        do_up = _extract_experiment_fn("do_up")
        self.assertIn("require_cmd socat || return 1", bridge_up)
        self.assertIn("require_cmd docker || return 1", bridge_up)
        self.assertIn("discover_gateway_ip || return 1", bridge_up)
        self.assertIn("if ! bridge_up; then", do_up)
        self.assertIn("Grafana bridge bring-up failed", do_up)
        self.assertIn("teardown_run", do_up)


class TestActivateCondaOrList(unittest.TestCase):
    """``activate_conda`` must propagate failure under OR-list callers (#967 parity)."""

    def test_conda_activate_failure_propagates_under_or_list(self) -> None:
        """OR-list callers must still see activate failure (not a masked exit 0)."""
        with tempfile.TemporaryDirectory() as tmp:
            conda_sh = Path(tmp) / "conda.sh"
            conda_sh.write_text(
                "#!/usr/bin/env bash\n"
                "conda() {\n"
                '  if [[ "$1" == "activate" ]]; then\n'
                "    return 1\n"
                "  fi\n"
                "}\n"
            )
            harness = (
                "set -euo pipefail\n"
                'log() { echo "$*"; }\n'
                f'CONDA_SH="{conda_sh}"\n'
                + _extract_experiment_fn("activate_conda")
                + "failed=0\n"
                + 'activate_conda "JuniperCascor1" || failed=1\n'
                + 'echo "failed=${failed}"\n'
                + "if (( failed != 1 )); then exit 2; fi\n"
            )
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


class TestDoUpHealthGateFailClosedTeardown(unittest.TestCase):
    """``do_up`` must tear a partial run back down when a later service fails health.

    Distinct from open #919's missing-bin arm (``require_env_bin`` → last-command
    failure). This pins the wait_for_health false-green: without
    ``wait_for_health … || return 1``, OR-list ``cascor_up || failed=1`` lets an
    unhealthy cascor still succeed via ``record_listener_pid`` finding the sleep
    stub's ``ss`` listener — ``failed=0``, no teardown, data listener orphaned.
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

    def test_cascor_health_fail_tears_down_data_listener(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            run_root = root / "runs"
            lock_root = root / "locks"
            deploy_dir = root / "deploy"
            listeners_dir = root / "listeners"
            stub_bin = root / "bin"
            conda_dir = root / "conda"
            listeners_dir.mkdir()
            stub_bin.mkdir()
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)

            # First free ports in the §9.3 ranges (ss reports none busy).
            data_port = "8110"
            cascor_port = "8230"

            # Env bins: record listener pid then sleep (ss reads the pidfile).
            for env_name, bins, port in (
                ("JuniperData", ("python",), data_port),
                ("JuniperCascor1", ("uvicorn",), cascor_port),
            ):
                bin_dir = conda_dir / "envs" / env_name / "bin"
                bin_dir.mkdir(parents=True)
                for bin_name in bins:
                    _write_stub(
                        bin_dir / bin_name,
                        "#!/usr/bin/env bash\n"
                        f'printf "%s\\n" "$$" >"{listeners_dir}/{port}.pid"\n'
                        "exec sleep 60\n",
                    )

            # curl: data health OK only once the stub has recorded its listener pid
            # (avoids wait_for_health racing record_listener_pid); cascor always fails.
            # Without wait_for_health || return 1 this false-greens: record_listener_pid
            # still finds the uvicorn sleep stub via ss and cascor_up returns 0.
            _write_stub(
                stub_bin / "curl",
                "#!/usr/bin/env bash\n"
                'case "$*" in\n'
                f"  *:8110*) [[ -f '{listeners_dir}/8110.pid' ]] && exit 0; exit 22 ;;\n"
                "esac\n"
                "exit 22\n",
            )
            _write_stub(
                stub_bin / "ss",
                "#!/usr/bin/env bash\n"
                'port=""\n'
                'for a in "$@"; do\n'
                '  case "$a" in\n'
                '    *sport*) port="${a##*:}" ;;\n'
                "  esac\n"
                "done\n"
                f'listener="{listeners_dir}/$port.pid"\n'
                'if [[ -n "$port" && -f "$listener" ]]; then\n'
                '  pid="$(cat "$listener")"\n'
                '  echo "LISTEN 0 128 127.0.0.1:${port} 0.0.0.0:* users:((\\"python\\",pid=${pid},fd=3))"\n'
                "fi\n"
                "exit 0\n",
            )
            _write_stub(stub_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
            _write_stub(stub_bin / "socat", "#!/usr/bin/env bash\nexec sleep 60\n")

            env = RedactedEnv(os.environ)
            env["JUNIPER_EXP_PROJECT_DIR"] = str(project_dir)
            env["JUNIPER_EXP_RUN_ROOT"] = str(run_root)
            env["JUNIPER_EXP_LOCK_ROOT"] = str(lock_root)
            env["JUNIPER_EXP_DEPLOY_DIR"] = str(deploy_dir)
            env["JUNIPER_EXP_CONDA_DIR"] = str(conda_dir)
            env["JUNIPER_EXP_HEALTH_TIMEOUT"] = "4"
            env["JUNIPER_EXP_KILL_TIMEOUT"] = "5"
            env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "--up", "--cascor"],
                capture_output=True,
                text=True,
                env=env,
                timeout=DO_UP_PARTIAL_TIMEOUT_SECONDS,
            )
            child_pids: list[int] = []
            for port in (data_port, cascor_port):
                listener = listeners_dir / f"{port}.pid"
                if listener.is_file():
                    try:
                        child_pids.append(int(listener.read_text().strip()))
                    except ValueError:
                        pass
            try:
                self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("bring-up failed — tearing the partial run back down", result.stdout)
                self.assertIn("failed to become healthy", result.stdout)
                self.assertIn("Teardown complete", result.stdout)
                # data must have launched (listener pidfile written) before cascor failed.
                self.assertTrue(
                    (listeners_dir / f"{data_port}.pid").exists()
                    or any(Path(f"/proc/{pid}").exists() for pid in child_pids),
                    "data_up must run before cascor health fails",
                )
                runs = list(run_root.iterdir()) if run_root.exists() else []
                self.assertTrue(runs, "partial run dir must exist for teardown")
                run_dir = runs[0]
                self.assertTrue((run_dir / "teardown.json").exists(), "teardown_run must write teardown.json")
                self.assertFalse(
                    (run_dir / "juniper-data.pid").exists(),
                    "teardown must clear the data pidfile",
                )
                for pid in child_pids:
                    for _ in range(60):
                        if not Path(f"/proc/{pid}").exists():
                            break
                        time.sleep(0.1)
                    self.assertFalse(
                        Path(f"/proc/{pid}").exists(),
                        f"partial teardown must kill listener pid {pid}",
                    )
            finally:
                for pid in child_pids:
                    self._force_kill(pid)


class TestBridgeUpFailureTeardown(unittest.TestCase):
    """``--grafana-bridge`` failure after services are up must tear the run down."""

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

    def test_missing_socat_tears_down_healthy_services(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            run_root = root / "runs"
            lock_root = root / "locks"
            deploy_dir = root / "deploy"
            listeners_dir = root / "listeners"
            stub_bin = root / "bin"
            conda_dir = root / "conda"
            listeners_dir.mkdir()
            stub_bin.mkdir()
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)

            data_port = "8110"
            cascor_port = "8230"
            for env_name, bins, port in (
                ("JuniperData", ("python",), data_port),
                ("JuniperCascor1", ("uvicorn",), cascor_port),
            ):
                bin_dir = conda_dir / "envs" / env_name / "bin"
                bin_dir.mkdir(parents=True)
                for bin_name in bins:
                    _write_stub(
                        bin_dir / bin_name,
                        "#!/usr/bin/env bash\n"
                        f'printf "%s\\n" "$$" >"{listeners_dir}/{port}.pid"\n'
                        "exec sleep 60\n",
                    )
            # Health OK only after the stub records its listener (no race with ss).
            _write_stub(
                stub_bin / "curl",
                "#!/usr/bin/env bash\n"
                'port=""\n'
                'case "$*" in\n'
                "  *:8110*) port=8110 ;;\n"
                "  *:8230*) port=8230 ;;\n"
                "  *) exit 22 ;;\n"
                "esac\n"
                f'[[ -f "{listeners_dir}/$port.pid" ]] && exit 0\n'
                "exit 22\n",
            )
            _write_stub(
                stub_bin / "ss",
                "#!/usr/bin/env bash\n"
                'port=""\n'
                'for a in "$@"; do\n'
                '  case "$a" in\n'
                '    *sport*) port="${a##*:}" ;;\n'
                "  esac\n"
                "done\n"
                f'listener="{listeners_dir}/$port.pid"\n'
                'if [[ -n "$port" && -f "$listener" ]]; then\n'
                '  pid="$(cat "$listener")"\n'
                '  echo "LISTEN 0 128 127.0.0.1:${port} 0.0.0.0:* users:((\\"python\\",pid=${pid},fd=3))"\n'
                "fi\n"
                "exit 0\n",
            )
            _write_stub(stub_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
            # Deliberately omit socat from PATH so require_cmd fails at bridge_up.

            env = RedactedEnv(os.environ)
            env["JUNIPER_EXP_PROJECT_DIR"] = str(project_dir)
            env["JUNIPER_EXP_RUN_ROOT"] = str(run_root)
            env["JUNIPER_EXP_LOCK_ROOT"] = str(lock_root)
            env["JUNIPER_EXP_DEPLOY_DIR"] = str(deploy_dir)
            env["JUNIPER_EXP_CONDA_DIR"] = str(conda_dir)
            env["JUNIPER_EXP_HEALTH_TIMEOUT"] = "4"
            env["JUNIPER_EXP_KILL_TIMEOUT"] = "5"
            env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "--up", "--cascor", "--grafana-bridge"],
                capture_output=True,
                text=True,
                env=env,
                timeout=DO_UP_PARTIAL_TIMEOUT_SECONDS,
            )
            child_pids: list[int] = []
            for port in (data_port, cascor_port):
                listener = listeners_dir / f"{port}.pid"
                if listener.is_file():
                    try:
                        child_pids.append(int(listener.read_text().strip()))
                    except ValueError:
                        pass
            try:
                self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("Grafana bridge bring-up failed", result.stdout)
                self.assertIn("required command 'socat' not found", result.stdout)
                self.assertIn("Teardown complete", result.stdout)
                runs = list(run_root.iterdir()) if run_root.exists() else []
                self.assertTrue(runs, "run dir must exist after service bring-up")
                self.assertTrue((runs[0] / "teardown.json").exists())
                for pid in child_pids:
                    for _ in range(60):
                        if not Path(f"/proc/{pid}").exists():
                            break
                        time.sleep(0.1)
                    self.assertFalse(
                        Path(f"/proc/{pid}").exists(),
                        f"bridge failure must tear down listener pid {pid}",
                    )
            finally:
                for pid in child_pids:
                    self._force_kill(pid)


if __name__ == "__main__":
    unittest.main()
