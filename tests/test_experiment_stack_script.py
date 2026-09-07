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
  release, artifacts preserved, and the kill-by-port fallback when the pidfile
  path refuses a reused PID whose cmdline no longer matches.
- live ``data_up`` / ``cascor_up`` / ``recurrence_up`` compose (F-6 listener pid
  via ``ss`` after health, §6.1 env recipes) with PATH-stubbed env bins — no real
  conda / network / docker;
- ``do_up`` partial-failure → ``teardown_run`` (locks released, recorded data
  listener killed) when a later service fails require_env_bin.
- OR-list fail-closed: ``*_up || failed=1`` disables ``set -e`` inside each
  ``*_up``, so critical steps must ``|| return 1`` (health-timeout + live listener
  must not false-green; activate_conda must not mask conda failure; bridge failure
  after healthy services must still teardown).

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
import textwrap
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "experiment_stack.bash"
SCRIPT_TEXT = SCRIPT_PATH.read_text()
SCRIPT_TIMEOUT_SECONDS = 20
TEARDOWN_TIMEOUT_SECONDS = 45
# Full --up with a short health timeout + tear-down of a stubbed listener.
DO_UP_PARTIAL_TIMEOUT_SECONDS = 30
LIVE_UP_TIMEOUT_SECONDS = 30


def _strip_comment_lines(text: str) -> str:
    """Drop whole-line ``#`` comments so structural invariants test CODE, not prose.

    The script documents the very hazards these tests forbid (``JuniperProject.pid``,
    the operator ports, the ``$!`` wrapper-pid trap), so a naive substring assertion
    over the raw text would be tripped by its own documentation.
    """
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _env_lines_for_key(env_text: str, key: str) -> list:
    """Return only the ``KEY=...`` lines of a captured env blob (F-E2E-005).

    The live-up stubs capture ``env | grep -E '^(...|JUNIPER_)'`` and that grep
    also captures ambient secrets (``JUNIPER_ML_PYPI`` / ``JUNIPER_ML_TEST_PYPI``
    tokens). A failing ``assertIn(needle, env_text)`` renders the WHOLE blob --
    the exact leak class ``tests/redacted_env.py`` exists to prevent -- so every
    assertion over a captured env compares against the lines for its own key,
    and a failure renders nothing but those.
    """
    return [line for line in env_text.splitlines() if line.split("=", 1)[0] == key]


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
            # ``-c`` answers ``data_up``'s free-threading probe (1 = free-threaded); without
            # it the probe's command substitution would block on the sleep below.
            _write_stub(bin_dir / bin_name, "#!/usr/bin/env bash\n" 'if [[ "${1-}" == "-c" ]]; then echo 1; exit 0; fi\n' "exec sleep 60\n")
    return conda_dir


def _force_kill(pid: int) -> None:
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


def _stage_live_path_stubs(root: Path, listeners_dir: Path) -> Path:
    """PATH stubs for live ``*_up``: curl waits for listener pidfile; ``ss`` reads it.

    The env-bin stub registers ``$$`` under ``listeners_dir/<port>.pid`` *after* it is
    backgrounded. ``wait_for_health`` can beat that write on the first poll if curl is
    always-OK — then ``record_listener_pid`` fails with "no listener pid resolved via ss".
    Curl therefore polls the pidfile (up to ~1s) before exiting 0; missing → exit 22 so
    the health loop retries.
    """
    stub_bin = root / "live-path-stubs"
    stub_bin.mkdir(parents=True, exist_ok=True)
    listeners_dir.mkdir(parents=True, exist_ok=True)
    _write_stub(
        stub_bin / "ss",
        textwrap.dedent(f"""\
            #!/usr/bin/env bash
            want=""
            for arg in "$@"; do
              case "$arg" in
                *sport*) want="${{arg##*:}}" ;;
              esac
            done
            [[ -n "$want" ]] || exit 0
            pidfile="{listeners_dir}/$want.pid"
            if [[ -f "$pidfile" ]]; then
              pid="$(cat "$pidfile")"
              echo "LISTEN 0 128 127.0.0.1:${{want}} 0.0.0.0:* users:((\\"python\\",pid=${{pid}},fd=3))"
            fi
            exit 0
            """),
    )
    _write_stub(
        stub_bin / "curl",
        textwrap.dedent(f"""\
            #!/usr/bin/env bash
            url=""
            for arg in "$@"; do
              case "$arg" in
                http://*|https://*) url="$arg" ;;
              esac
            done
            # http://127.0.0.1:68110/v1/health -> 68110
            port="$(printf '%s' "$url" | sed -n 's#.*://[^/:]*:\\([0-9][0-9]*\\)/.*#\\1#p')"
            [[ -n "$port" ]] || exit 0
            pidfile="{listeners_dir}/$port.pid"
            for _ in 1 2 3 4 5 6 7 8 9 10; do
              if [[ -f "$pidfile" ]]; then
                exit 0
              fi
              sleep 0.1
            done
            exit 22
            """),
    )
    _write_stub(stub_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
    _write_stub(stub_bin / "socat", "#!/usr/bin/env bash\nexec sleep 60\n")
    return stub_bin


def _write_listening_env_bin(path: Path, *, listeners_dir: Path, marker_dir: Path, label: str) -> None:
    """Conda env bin that registers ``$$`` for ``ss`` then sleeps (F-6 live compose).

    Also answers ``data_up``'s free-threading probe (``-c ...``) before the ``--port``
    parsing: the default answer is 1 (free-threaded) so the ``PYTHON_GIL=0`` pins hold,
    and a ``gil_probe_answer`` marker file overrides it to rehearse a stock CPython.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_stub(
        path,
        textwrap.dedent(f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ "${{1-}}" == "-c" ]]; then
              if [[ -f "{marker_dir}/gil_probe_answer" ]]; then cat "{marker_dir}/gil_probe_answer"; else echo 1; fi
              exit 0
            fi
            port=""
            prev=""
            for arg in "$@"; do
              if [[ "$prev" == "--port" ]]; then
                port="$arg"
              fi
              prev="$arg"
            done
            [[ -n "$port" ]] || {{ echo "missing --port in $*" >&2; exit 2; }}
            mkdir -p "{listeners_dir}" "{marker_dir}"
            printf '%s\\n' "$@" >"{marker_dir}/{label}.args"
            {{
              printf 'PWD=%s\\n' "$PWD"
              # Prefix match for JUNIPER_* (not JUNIPER_=); keep PYTHON_GIL / LD_LIBRARY_PATH / PATH.
              env | grep -E '^(PYTHON_GIL|LD_LIBRARY_PATH|PATH|JUNIPER_)' || true
            }} >"{marker_dir}/{label}.env"
            printf '%s\\n' "$$" >"{listeners_dir}/${{port}}.pid"
            exec sleep 60
            """),
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

    def test_strict_mode_and_nounset_guard(self) -> None:
        self.assertIn("set -euo pipefail", SCRIPT_TEXT)
        # Fail-closed activate: every path restores nounset (not +u/+u). A bare
        # ``conda activate`` failure followed by ``set -u`` would return 0 under
        # OR-list callers and let services launch on the ambient PATH.
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
        for subdir in ("logs", "relays", "config", "env", "data", "equities-cache", "snapshots", "artifacts/plots", "artifacts/results"):
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

    def test_staging_failure_releases_held_port_locks(self) -> None:
        """Missing --config (or mkdir/cp failure) must not starve the experiment ranges.

        allocate_port creates *.lock dirs before ports.json exists; a set -e exit from
        stage_config without release_held_locks leaves locks that --down cannot recover.
        """
        do_up = _extract_experiment_fn("do_up")
        for step in ("create_run_dir", "stage_config", "write_ports_json"):
            self.assertRegex(
                do_up,
                rf"{step} \|\| \{{\s*release_held_locks",
                msg=f"{step} failure must call release_held_locks (ports.json may be absent)",
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
        # APD-DATA-018 csv_import half: operators export these before --up; the child
        # inherits. data_up must not hardcode /data/imports or clobber a caller-set
        # ceiling / truncation opt-in (and must not unset them either).
        for var in (
            "JUNIPER_DATA_IMPORT_DIR",
            "JUNIPER_DATA_CSV_IMPORT_MAX_BYTES",
            "JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION",
        ):
            self.assertNotIn(var, data_up, f"data_up must not set {var}; operators export it before --up")

    def test_cascor_launch_recipe(self) -> None:
        cascor_up = _extract_experiment_fn("cascor_up")
        # The uvicorn CLI owns the bind, so experiment YAML can never override it (§6.1).
        self.assertIn("api.app:create_app --factory --host 127.0.0.1 --port", cascor_up)
        self.assertIn("LD_LIBRARY_PATH=''", cascor_up)
        self.assertIn("JUNIPER_CASCOR_METRICS_ENABLED=true", cascor_up)
        self.assertIn("JUNIPER_CASCOR_AUTO_START=false", cascor_up)
        self.assertIn("JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false", cascor_up)
        # Wave 5.3 (W-6 wiring): per-run snapshots home — retires the shared src/snapshots debris (H-4).
        self.assertIn('JUNIPER_CASCOR_SNAPSHOTS_DIR="${RUN_DIR}/snapshots"', cascor_up)
        # Q-6 wiring (H-7): per-run file log — retires the shared logs/juniper_cascor.log that a
        # concurrent cascor process interleaves and rotates away (how the F-P1-3 arm A/B evidence
        # was lost). cascor#523 supplies the override this points at.
        self.assertIn('JUNIPER_CASCOR_LOG_DIR="${LOG_DIR}"', cascor_up)
        self.assertIn('JUNIPER_DATA_URL="${DATA_URL}"', cascor_up)
        self.assertIn('cd "${CASCOR_SRC_DIR}"', cascor_up)

    def test_q6_log_dir_exported_at_every_cascor_site(self) -> None:
        """The Q-6 export must appear at all three synchronized cascor_up sites.

        ``cascor_up`` states its launch env three times — the ``announce`` dry-run line, the
        ``record_launch_env`` array persisted to ``env/launch.env``, and the live ``nohup``
        invocation. Updating only the live one is the standing failure mode here (it is how the
        dry-run and the recorded env silently drift from what actually ran), and it is invisible
        to any test that greps the function as a whole. Pin the count, not the presence.
        """
        cascor_up = _extract_experiment_fn("cascor_up")
        self.assertEqual(
            cascor_up.count("JUNIPER_CASCOR_LOG_DIR"),
            3,
            "expected the Q-6 log-dir export at all 3 cascor_up sites (announce / record_launch_env / nohup)",
        )
        # Same invariant for its W-6 sibling — if that count ever changes, this test should be
        # updated deliberately rather than the two drifting apart unnoticed.
        self.assertEqual(cascor_up.count("JUNIPER_CASCOR_SNAPSHOTS_DIR"), 3)

    def test_dc_provenance_exported_at_every_cascor_site(self) -> None:
        """D-C: all five provenance vars, at all three synchronized cascor_up sites.

        Same standing failure mode as the Q-6 export above — updating only the live nohup
        leaves the dry-run line and the recorded ``env/launch.env`` describing a launch that
        did not happen. That matters more here than usual: ``env/launch.env`` is what an
        operator reads to find out which run identity a snapshot was written under, so a
        drifted copy is actively misleading rather than merely stale.
        """
        cascor_up = _extract_experiment_fn("cascor_up")
        # Vars the launcher OWNS are named once per site: ``NAME=${SOURCE:-}``.
        for var in ("JUNIPER_CASCOR_RUN_ID", "JUNIPER_CASCOR_GIT_SHA"):
            self.assertEqual(cascor_up.count(var), 3, f"expected {var} at all 3 cascor_up sites (announce / record_launch_env / nohup)")
        # Vars that PASS THROUGH name themselves twice per site — ``NAME=${NAME:-}`` — so
        # the expected count is 6, not 3. Asserting 3 here would fail against correct code.
        for var in ("JUNIPER_CASCOR_EXPERIMENT", "JUNIPER_CASCOR_CELL_ID", "JUNIPER_CASCOR_DATASET_ID"):
            self.assertEqual(cascor_up.count(var), 6, f"expected {var} at all 3 cascor_up sites, named twice each as a pass-through")

    def test_dc_provenance_survives_unset_run_identity(self) -> None:
        """Every provenance expansion must tolerate an unset variable under ``set -u``.

        ``cascor_up`` is also executed standalone by this suite's harness, where the file-scope
        ``RUN_ID=""`` / ``EXPERIMENT=""`` defaults do not exist. An unguarded ``${RUN_ID}``
        aborts the whole bring-up with ``unbound variable`` — which is how this was caught.
        """
        cascor_up = _extract_experiment_fn("cascor_up")
        self.assertNotIn("${RUN_ID}", cascor_up, "RUN_ID must be expanded as ${RUN_ID:-} so an unset value cannot abort cascor_up")
        self.assertNotIn("${EXPERIMENT}", cascor_up, "EXPERIMENT must be expanded with a :- default")

    def test_dc_git_sha_is_resolved_inline(self) -> None:
        """The SHA lookup must not live in a file-scope helper.

        The harness extracts ``cascor_up`` on its own, so anything it calls at file scope is
        undefined there and the bring-up dies. Keeping the lookup inline is the constraint,
        not a style preference.
        """
        cascor_up = _extract_experiment_fn("cascor_up")
        self.assertIn("rev-parse", cascor_up, "the git SHA must be resolved inside cascor_up, not via a file-scope helper")
        self.assertIn("|| true", cascor_up, "a missing git or non-repo checkout must yield empty, not fail the launch")

    def test_q6_log_dir_exists_before_cascor_launch(self) -> None:
        """The target dir must be created before the service starts.

        cascor derives its log path from the checkout root and a fresh worktree has no ``logs/``,
        so pointing the override at a directory that does not exist yet trades one failure for
        another. ``ensure_dir "${LOG_DIR}"`` already runs in ``cascor_up`` for the nohup redirect;
        this pins that it stays there, since the override now depends on it too.
        """
        cascor_up = _extract_experiment_fn("cascor_up")
        self.assertIn('ensure_dir "${LOG_DIR}"', cascor_up)
        ensure_at = cascor_up.index('ensure_dir "${LOG_DIR}"')
        # Anchor on the real invocation, not the bare word: the ``announce`` dry-run line carries a
        # trailing ``# nohup -> ...`` comment that precedes ensure_dir and would match first.
        launch_at = cascor_up.index('nohup "${uvicorn_bin}"')
        self.assertLess(ensure_at, launch_at, "LOG_DIR must be created before the cascor launch")

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
        # Use the ``|| failed=1`` call sites (not bare names in comments).
        self.assertIn("data_up || failed=1", do_up)
        self.assertIn("cascor_up || failed=1", do_up)
        self.assertIn("recurrence_up || failed=1", do_up)
        self.assertLess(do_up.index("data_up || failed=1"), do_up.index("cascor_up || failed=1"))
        self.assertLess(do_up.index("cascor_up || failed=1"), do_up.index("recurrence_up || failed=1"))
        self.assertIn("tearing the partial run back down", do_up)
        # OR-list disables set -e inside each *_up — critical steps must || return 1.
        expected = (
            (
                "data_up",
                'wait_for_health "juniper-data" "http://127.0.0.1:${DATA_PORT}/v1/health" "${HEALTH_TIMEOUT}" "-m juniper_data .*--port ${DATA_PORT}" || return 1',
                'record_listener_pid "juniper-data" "${DATA_PORT}" || return 1',
                'activate_conda "${DATA_CONDA}" || return 1',
            ),
            (
                "cascor_up",
                'wait_for_health "juniper-cascor" "http://127.0.0.1:${CASCOR_PORT}/v1/health" "${HEALTH_TIMEOUT}" "api.app:create_app .*--port ${CASCOR_PORT}" || return 1',
                'record_listener_pid "juniper-cascor" "${CASCOR_PORT}" || return 1',
                'activate_conda "${CASCOR_CONDA}" || return 1',
            ),
            (
                "recurrence_up",
                'wait_for_health "juniper-recurrence" "http://127.0.0.1:${RECURRENCE_PORT}/v1/health/ready" "${HEALTH_TIMEOUT}" "juniper-recurrence serve .*--port ${RECURRENCE_PORT}" || return 1',
                'record_listener_pid "juniper-recurrence" "${RECURRENCE_PORT}" || return 1',
                'activate_conda "${RECURRENCE_CONDA}" || return 1',
            ),
        )
        for fn_name, health_line, record_line, activate_line in expected:
            body = _extract_experiment_fn(fn_name)
            self.assertIn("require_env_bin", body)
            self.assertIn(health_line, body, msg=f"{fn_name} must fail-closed on wait_for_health")
            self.assertIn(record_line, body, msg=f"{fn_name} must fail-closed on record_listener_pid")
            self.assertIn(activate_line, body, msg=f"{fn_name} must fail-closed on activate_conda")
        # Bridge failure after healthy services must tear down (not abort via set -e).
        self.assertIn("if ! bridge_up; then", do_up)
        self.assertIn("grafana bridge failed", do_up)
        bridge_up = _extract_experiment_fn("bridge_up")
        self.assertIn("require_cmd socat || return 1", bridge_up)
        self.assertIn("require_cmd docker || return 1", bridge_up)
        # Every allocate_port site must clear HELD_LOCK_PORTS on failure (helper was dead).
        for svc in ("juniper-data", "juniper-cascor", "juniper-recurrence"):
            self.assertRegex(
                do_up,
                rf'allocate_port "{svc}".*?\|\| \{{\s*release_held_locks',
                msg=f"{svc} allocate failure must call release_held_locks",
            )


class TestHealthGateLiveness(unittest.TestCase):
    """The health gate fails fast when the process it is waiting on is already dead.

    A leg that dies during startup (bad env, import error, port stolen) used to burn
    the whole ``HEALTH_TIMEOUT`` -- 90 s per leg -- before the operator learned
    anything, even though the cause was already in the leg's log. ``wait_for_health``
    takes an optional ``pgrep -f`` liveness pattern and ends the wait after two
    CONSECUTIVE misses.

    Two misses, not one, because the launch subshell returns before its child has
    exec'd; and the probe runs after the first sleep, so fork+exec gets a >=4 s grace.

    F-6 is untouched: the pattern is only ever read. Teardown still resolves the pid
    from the listener socket and verifies uid + cmdline before signalling anything.
    """

    #: Instant ``sleep`` keeps the arms fast; ``elapsed`` still advances by 2 per loop.
    _SLEEP_STUB = "#!/usr/bin/env bash\nexit 0\n"

    def _harness(self, *, timeout: int, pattern: str, log_dir: Path) -> str:
        pattern_arg = f' "{pattern}"' if pattern else ""
        return f"""
            set -euo pipefail
            SCRIPT_NAME="experiment_stack.bash"
            LOG_DIR="{log_dir}"
            HEALTH_TIMEOUT={timeout}
            log() {{ echo "[${{SCRIPT_NAME}}] $*"; }}
            {_extract_experiment_fn("wait_for_health")}
            set +e
            wait_for_health "juniper-data" "http://127.0.0.1:65999/v1/health" {timeout}{pattern_arg}
            status=$?
            set -e
            echo "STATUS=${{status}}"
            exit 0
        """

    def _run_gate(
        self,
        *,
        curl_body: str,
        pgrep_body: "str | None",
        pattern: str,
        timeout: int = 20,
    ) -> "tuple[subprocess.CompletedProcess[str], Path]":
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        stub_bin = root / "path-stubs"
        stub_bin.mkdir(parents=True, exist_ok=True)
        log_dir = root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        _write_stub(stub_bin / "curl", curl_body)
        _write_stub(stub_bin / "sleep", self._SLEEP_STUB)
        if pgrep_body is not None:
            _write_stub(stub_bin / "pgrep", pgrep_body)
        env = RedactedEnv(os.environ)
        # No /usr/bin:/bin fallback when pgrep must be ABSENT, else the real one resolves.
        tail = "" if pgrep_body is None else os.pathsep + "/usr/bin:/bin"
        env["PATH"] = str(stub_bin) + tail
        result = subprocess.run(
            ["/bin/bash", "-c", self._harness(timeout=timeout, pattern=pattern, log_dir=log_dir)],
            capture_output=True,
            text=True,
            env=env,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )
        return result, root

    def _counting_curl(self, root: Path) -> str:
        """curl that always fails but records each poll, so we can bound the wait."""
        return "#!/usr/bin/env bash\n" f'echo poll >>"{root}/curl.count"\n' "exit 1\n"

    def test_dead_process_fails_fast_instead_of_burning_the_timeout(self) -> None:
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        result, gate_root = self._run_gate(
            curl_body=self._counting_curl(root),
            pgrep_body="#!/usr/bin/env bash\nexit 1\n",  # nothing matches: the leg is gone
            pattern="-m juniper_data .*--port 65999",
            timeout=60,
        )
        self.assertIn("STATUS=1", result.stdout, msg=result.stdout + result.stderr)
        self.assertIn("process is gone", result.stdout)
        self.assertIn("died during startup", result.stdout)
        # Names the log to read -- the whole point of failing fast.
        self.assertIn("juniper-data.log", result.stdout)
        # Two consecutive misses => 2 polls, NOT the 30 a 60s timeout would allow.
        polls = (root / "curl.count").read_text().splitlines()
        self.assertLessEqual(len(polls), 3, msg=f"expected a fast fail, got {len(polls)} polls")
        self.assertTrue((gate_root / "logs").is_dir())

    def test_single_transient_miss_does_not_declare_death(self) -> None:
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        # pgrep misses on odd calls, hits on even: never two in a row.
        pgrep_body = "#!/usr/bin/env bash\n" f'n=$(cat "{root}/pgrep.n" 2>/dev/null || echo 0)\n' "n=$((n+1))\n" f'echo "$n" >"{root}/pgrep.n"\n' "if (( n % 2 == 1 )); then exit 1; fi\n" "exit 0\n"
        # curl fails 4 times then succeeds: the gate must survive to see it.
        curl_body = "#!/usr/bin/env bash\n" f'n=$(cat "{root}/curl.n" 2>/dev/null || echo 0)\n' "n=$((n+1))\n" f'echo "$n" >"{root}/curl.n"\n' "if (( n <= 4 )); then exit 1; fi\n" "exit 0\n"
        result, _ = self._run_gate(curl_body=curl_body, pgrep_body=pgrep_body, pattern="-m juniper_data .*--port 65999", timeout=60)
        self.assertIn("STATUS=0", result.stdout, msg=result.stdout + result.stderr)
        self.assertIn("is healthy", result.stdout)
        self.assertNotIn("process is gone", result.stdout)

    def test_slow_boot_with_live_process_still_becomes_healthy(self) -> None:
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        curl_body = "#!/usr/bin/env bash\n" f'n=$(cat "{root}/curl.n" 2>/dev/null || echo 0)\n' "n=$((n+1))\n" f'echo "$n" >"{root}/curl.n"\n' "if (( n <= 6 )); then exit 1; fi\n" "exit 0\n"
        result, _ = self._run_gate(
            curl_body=curl_body,
            pgrep_body="#!/usr/bin/env bash\nexit 0\n",  # process alive throughout
            pattern="-m juniper_data .*--port 65999",
            timeout=60,
        )
        self.assertIn("STATUS=0", result.stdout, msg=result.stdout + result.stderr)
        self.assertNotIn("process is gone", result.stdout)

    def test_no_pattern_keeps_timeout_only_behaviour_and_never_probes(self) -> None:
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        pgrep_body = "#!/usr/bin/env bash\n" f'echo called >>"{root}/pgrep.calls"\n' "exit 1\n"
        result, _ = self._run_gate(curl_body="#!/usr/bin/env bash\nexit 1\n", pgrep_body=pgrep_body, pattern="", timeout=6)
        self.assertIn("STATUS=1", result.stdout, msg=result.stdout + result.stderr)
        self.assertIn("failed to become healthy within", result.stdout)
        self.assertNotIn("process is gone", result.stdout)
        self.assertFalse((root / "pgrep.calls").exists(), "no pattern must mean no liveness probe at all")

    def test_absent_pgrep_degrades_to_timeout_rather_than_a_false_death(self) -> None:
        """An unavailable probe must never manufacture a failure."""
        result, _ = self._run_gate(
            curl_body="#!/usr/bin/env bash\nexit 1\n",
            pgrep_body=None,  # pgrep not on PATH at all
            pattern="-m juniper_data .*--port 65999",
            timeout=6,
        )
        self.assertIn("STATUS=1", result.stdout, msg=result.stdout + result.stderr)
        self.assertIn("pgrep unavailable", result.stdout)
        self.assertIn("failed to become healthy within", result.stdout)
        self.assertNotIn("process is gone", result.stdout, "absent pgrep must not read as a dead process")

    def test_each_leg_passes_a_port_scoped_liveness_pattern(self) -> None:
        """Port-scoped so a sibling run's process can never satisfy this run's gate."""
        expected = (
            ("data_up", '"-m juniper_data .*--port ${DATA_PORT}"'),
            ("cascor_up", '"api.app:create_app .*--port ${CASCOR_PORT}"'),
            ("recurrence_up", '"juniper-recurrence serve .*--port ${RECURRENCE_PORT}"'),
        )
        for fn_name, pattern in expected:
            body = _strip_comment_lines(_extract_experiment_fn(fn_name))
            self.assertIn(pattern, body, msg=f"{fn_name} must pass a port-scoped liveness pattern")
            self.assertIn("wait_for_health", body)

    def test_liveness_probe_is_read_only_and_never_kills(self) -> None:
        """F-6: the pattern resolves nothing and signals nothing."""
        gate = _extract_experiment_fn("wait_for_health")
        self.assertIn("pgrep -f --", gate)
        self.assertNotIn("kill", gate, "the health gate must never signal a process")
        # pgrep exists ONLY in the gate: teardown resolves pids from the listener socket.
        pgrep_fns = [name for name in ("stop_service", "teardown_run", "record_listener_pid", "port_listener_pid", "kill_verified_pid", "terminate_pid") if "pgrep" in _extract_experiment_fn(name)]
        self.assertEqual([], pgrep_fns, msg=f"pgrep must not leak into teardown: {pgrep_fns}")


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
            # Strip comments: the OR-list fail-closed prose names record_listener_pid
            # before the live call site and would invert a naive index() order check.
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

    def test_discover_gateway_ip_fail_closed_under_or_list_callers(self) -> None:
        # Callers that wrap bridge_up in ``if !`` disable set -e inside the body;
        # without ``|| return 1`` a discover failure falls through with GATEWAY_IP="".
        bridge_up = _extract_experiment_fn("bridge_up")
        self.assertIn("discover_gateway_ip || return 1", bridge_up)

    def test_target_file_lives_in_the_deploy_targets_dir(self) -> None:
        # F-3: prometheus/targets/ is already inside the existing :ro mount.
        self.assertIn('TARGETS_DIR="${DEPLOY_DIR}/prometheus/targets"', SCRIPT_TEXT)
        self.assertIn('DEPLOY_DIR="${JUNIPER_EXP_DEPLOY_DIR:-${PROJECT_DIR}/juniper-deploy}"', SCRIPT_TEXT)

    def test_cascor_src_dir_is_overridable_on_its_own(self) -> None:
        """A campaign must be able to pin cascor to a WORKTREE without freezing the primary.

        While this was derived from PROJECT_DIR, every campaign held the primary checkout for
        its whole life, and any session running a stack out of the primary blocked every
        campaign (observed 2026-08-26: a live E2E stack on :8202 with cwd in the primary src).
        The override is independent of PROJECT_DIR so the rest of the layout stays canonical.
        """
        self.assertIn('CASCOR_SRC_DIR="${JUNIPER_EXP_CASCOR_SRC_DIR:-${PROJECT_DIR}/juniper-cascor/src}"', SCRIPT_TEXT)
        # And it must stay the thing uvicorn is launched from, or the override is decorative.
        self.assertIn('cd "${CASCOR_SRC_DIR}"', _extract_experiment_fn("cascor_up"))

    def test_the_cascor_src_override_is_documented(self) -> None:
        """The env block is the only place an operator learns the knob exists."""
        self.assertIn("JUNIPER_EXP_CASCOR_SRC_DIR", SCRIPT_TEXT.split("CASCOR_SRC_DIR=")[0])

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

    def test_kill_by_port_fallback_after_pidfile_cmdline_refuse(self) -> None:
        """Pid-reuse refuse must still tear down via the recorded port's live listener.

        The sibling arm above stubs ``ss`` with no listener, so the fallback is inert.
        Here ``ss`` reports the live PID on the recorded port; ``stop_service`` must log
        the refuse, then kill through the empty-cmdline port path (F-6 fallback).
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "20260730T000000Z-fbck"
            run_root = root / "runs"
            lock_root = root / "locks"
            run_dir = run_root / run_id
            (run_dir / "artifacts" / "results").mkdir(parents=True)
            (run_dir / "logs").mkdir()
            (lock_root / "8260.lock").mkdir(parents=True)
            keeper = run_dir / "artifacts" / "results" / "metrics_final.json"
            keeper.write_text("{}\n")
            (run_dir / "ports.json").write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "data": None,
                        "cascor": None,
                        "recurrence": 8260,
                        "data_url": None,
                        "experiment": "smoke",
                        "grafana_bridge": False,
                    },
                    indent=2,
                )
                + "\n"
            )

            pid = self._spawn_detached()
            try:
                (run_dir / "juniper-recurrence.pid").write_text(f"{pid}\n")
                (run_dir / "juniper-recurrence.cmdline").write_text("some other process ")

                stub_bin = root / "path-stubs"
                stub_bin.mkdir(parents=True, exist_ok=True)
                # Report the live PID only while it is still alive, so post-kill
                # port_in_use does not false-alarm a still-bound listener.
                _write_stub(
                    stub_bin / "ss",
                    "#!/usr/bin/env bash\n" f'pid="{pid}"\n' 'want=""\n' 'for arg in "$@"; do\n' '  case "$arg" in\n' '    *sport*) want="${arg##*:}" ;;\n' "  esac\n" "done\n" 'if [[ "$want" == "8260" ]] && kill -0 "$pid" 2>/dev/null; then\n' '  echo "LISTEN 0 128 127.0.0.1:8260 0.0.0.0:* users:((\\"python\\",pid=${pid},fd=3))"\n' "fi\n" "exit 0\n",
                )
                _write_stub(stub_bin / "curl", "#!/usr/bin/env bash\nexit 0\n")
                _write_stub(stub_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
                _write_stub(stub_bin / "socat", "#!/usr/bin/env bash\nexec sleep 60\n")

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
                out = result.stdout
                self.assertIn("cmdline changed since launch", out)
                self.assertIn("pidfile path refused", out)
                self.assertIn("falling back to the recorded port 8260", out)
                self.assertIn("(by port 8260)", out)

                for _ in range(60):
                    if not Path(f"/proc/{pid}").exists():
                        break
                    time.sleep(0.1)
                self.assertFalse(
                    Path(f"/proc/{pid}").exists(),
                    "kill-by-port fallback must terminate the live listener after a pidfile refuse",
                )
                self.assertTrue(keeper.exists(), "teardown must NEVER delete artifacts/")
                self.assertFalse((lock_root / "8260.lock").exists(), "port lockdir must still be released")
            finally:
                self._force_kill(pid)

    def test_down_on_a_missing_run_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run("--down", "20260730T000000Z-none", env_extra={"JUNIPER_EXP_RUN_ROOT": str(Path(tmp) / "runs")})
            self.assertEqual(result.returncode, 1)
            self.assertIn("no such run dir", result.stdout)


class TestTwoRunConcurrency(unittest.TestCase):
    """Wave 5.3: two concurrent runs are isolated — ``--down`` of one touches nothing of the other.

    Q-6 stays deferred, so the one-cascor-instance-per-CHECKOUT rule stands (H-7 log
    race); what Wave 5 retires is the snapshots/bench collision (W-6/W-7). This arm
    pins the launcher's per-run scoping under two live runs: run A's teardown kills
    only A's recorded pid and releases only A's lockdirs/target file, leaving run B's
    pid alive and its lockdirs, pidfile, and target file intact.
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

    def _synthesize_run(self, run_root: Path, lock_root: Path, targets_dir: Path, run_id: str, data_port: int, rec_port: int, pid: int) -> Path:
        run_dir = run_root / run_id
        (run_dir / "artifacts" / "results").mkdir(parents=True)
        (run_dir / "logs").mkdir()
        (lock_root / f"{data_port}.lock").mkdir(parents=True)
        (lock_root / f"{rec_port}.lock").mkdir(parents=True)
        (targets_dir / f"{run_id}.json").write_text("[]\n")
        (run_dir / "artifacts" / "results" / "metrics_final.json").write_text("{}\n")
        (run_dir / "ports.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "data": data_port,
                    "cascor": None,
                    "recurrence": rec_port,
                    "data_url": f"http://127.0.0.1:{data_port}",
                    "experiment": "two-run",
                    "grafana_bridge": True,
                },
                indent=2,
            )
            + "\n"
        )
        (run_dir / "juniper-recurrence.pid").write_text(f"{pid}\n")
        (run_dir / "juniper-recurrence.cmdline").write_text(self._proc_cmdline(pid))
        return run_dir

    def test_down_of_run_a_leaves_run_b_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "runs"
            lock_root = root / "locks"
            targets_dir = root / "deploy" / "prometheus" / "targets"
            targets_dir.mkdir(parents=True)
            run_a = "20260808T000000Z-aaaa"
            run_b = "20260808T000001Z-bbbb"

            pid_a = self._spawn_detached()
            pid_b = self._spawn_detached()
            try:
                self._synthesize_run(run_root, lock_root, targets_dir, run_a, 8110, 8260, pid_a)
                run_b_dir = self._synthesize_run(run_root, lock_root, targets_dir, run_b, 8111, 8261, pid_b)

                stub_bin = _stage_stub_bin(root, busy_ports=[])
                env = {
                    "JUNIPER_EXP_RUN_ROOT": str(run_root),
                    "JUNIPER_EXP_LOCK_ROOT": str(lock_root),
                    "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
                    "JUNIPER_EXP_KILL_TIMEOUT": "5",
                    "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
                }
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT_PATH), "--down", run_a],
                    capture_output=True,
                    text=True,
                    env=RedactedEnv(os.environ, **env),
                    timeout=TEARDOWN_TIMEOUT_SECONDS,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)

                # Run A fully torn down.
                for _ in range(60):
                    if not Path(f"/proc/{pid_a}").exists():
                        break
                    time.sleep(0.1)
                self.assertFalse(Path(f"/proc/{pid_a}").exists(), "run A's recorded pid must be killed")
                self.assertFalse((lock_root / "8110.lock").exists(), "run A's data lockdir must be released")
                self.assertFalse((lock_root / "8260.lock").exists(), "run A's recurrence lockdir must be released")
                self.assertFalse((targets_dir / f"{run_a}.json").exists(), "run A's target file must be removed")

                # Run B completely untouched.
                self.assertTrue(Path(f"/proc/{pid_b}").exists(), "run B's pid must stay alive")
                self.assertTrue((lock_root / "8111.lock").exists(), "run B's data lockdir must survive")
                self.assertTrue((lock_root / "8261.lock").exists(), "run B's recurrence lockdir must survive")
                self.assertTrue((targets_dir / f"{run_b}.json").exists(), "run B's target file must survive")
                self.assertTrue((run_b_dir / "juniper-recurrence.pid").exists(), "run B's pidfile must survive")
                self.assertFalse((run_b_dir / "teardown.json").exists(), "run B must not gain a teardown record")
            finally:
                self._force_kill(pid_a)
                self._force_kill(pid_b)


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

    def test_recurrence_config_threads_env_var_not_flag(self) -> None:
        # Wave 3.3 landed: the launcher threads JUNIPER_RECURRENCE_CONFIG_FILE (the app-side
        # settings source reads it) and still NEVER passes a serve --config flag -- the env
        # var is the threading mechanism, so the launcher CLI keeps owning the bind (SS5.2).
        recurrence_up = _extract_experiment_fn("recurrence_up")
        self.assertNotIn("serve --config", recurrence_up)
        self.assertIn("JUNIPER_RECURRENCE_CONFIG_FILE", recurrence_up)


class TestMissingConfigReleasesPortLocks(unittest.TestCase):
    """``--up --config <missing>`` must release allocated lockdirs (not starve ranges)."""

    def test_missing_config_releases_data_and_cascor_locks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock_root = root / "locks"
            run_root = root / "runs"
            stub_bin = _stage_stub_bin(root, busy_ports=[])
            conda_dir = _stage_conda_fixture(root)
            missing = root / "does-not-exist.yaml"
            env = RedactedEnv(os.environ)
            env.update(
                {
                    "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
                    "JUNIPER_EXP_RUN_ROOT": str(run_root),
                    "JUNIPER_EXP_LOCK_ROOT": str(lock_root),
                    "JUNIPER_EXP_CONDA_DIR": str(conda_dir),
                    "JUNIPER_EXP_PROJECT_DIR": str(root / "project"),
                    "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
                    "HOME": str(root / "home"),
                }
            )
            (root / "project").mkdir()
            (root / "home").mkdir()
            result = subprocess.run(
                [
                    "/bin/bash",
                    str(SCRIPT_PATH),
                    "--up",
                    "--cascor",
                    "--config",
                    str(missing),
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("config file not found", result.stdout + result.stderr)
            # Both ranges were claimed before stage_config; both locks must be gone.
            leftover = sorted(p.name for p in lock_root.glob("*.lock")) if lock_root.exists() else []
            self.assertEqual(
                leftover,
                [],
                msg=f"staging failure must release held port locks; leftover={leftover} stdout={result.stdout}",
            )


if __name__ == "__main__":
    unittest.main()


class TestReleaseHeldLocksOnAllocateFail(unittest.TestCase):
    """Mid-allocate failure must clear earlier lockdirs (release_held_locks was dead)."""

    def test_second_range_exhaustion_releases_the_first_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock_root = root / "locks"
            lock_root.mkdir()
            # Occupy the entire cascor range so the second allocate_port fails.
            for port in range(8230, 8260):
                (lock_root / f"{port}.lock").mkdir()
            stub_bin = _stage_stub_bin(root, busy_ports=[])
            harness = (
                "set -euo pipefail\n"
                'log() { echo "$*"; }\n'
                'announce() { echo "$*"; }\n'
                "is_dry() { return 1; }\n"
                f'LOCK_ROOT="{lock_root}"\n'
                "HELD_LOCK_PORTS=()\n"
                'ALLOCATED_PORT=""\n' + _extract_experiment_fn("port_in_use") + _extract_experiment_fn("allocate_port") + _extract_experiment_fn("release_held_locks") + "allocate_port juniper-data 8110 8110 || { release_held_locks; exit 1; }\n"
                'printf "HELD_AFTER_DATA=%s\\n" "${HELD_LOCK_PORTS[*]:-}"\n'
                "allocate_port juniper-cascor 8230 8259 || { release_held_locks; printf 'RELEASED\\n'; exit 1; }\n"
            )
            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"
            result = subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("RELEASED", result.stdout)
            self.assertIn("HELD_AFTER_DATA=8110", result.stdout)
            self.assertFalse(
                (lock_root / "8110.lock").exists(),
                "release_held_locks must rmdir the data lock after cascor range exhaustion",
            )


class TestActivateCondaOrList(unittest.TestCase):
    """OR-list callers must still see activate failure (not a masked exit 0)."""

    def test_conda_activate_failure_propagates_under_or_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conda_sh = Path(tmp) / "conda.sh"
            conda_sh.write_text("#!/usr/bin/env bash\n" "conda() {\n" '  if [[ "$1" == "activate" ]]; then\n' "    return 1\n" "  fi\n" "}\n")
            harness = "set -euo pipefail\n" 'log() { echo "$*"; }\n' f'CONDA_SH="{conda_sh}"\n' + _extract_experiment_fn("activate_conda") + "failed=0\n" + 'activate_conda "JuniperCascor1" || failed=1\n' + 'echo "failed=${failed}"\n' + "if (( failed != 1 )); then exit 2; fi\n"
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


class TestDoUpFailClosedTeardown(unittest.TestCase):
    """``do_up`` must tear a partial run back down when health fails under OR-list.

    Pre-fix: ``data_up || failed=1`` disables ``set -e`` inside ``data_up``. A
    health-timeout with a live listener then fell through to ``record_listener_pid``
    (exit 0), so ``failed`` stayed 0 and the listener was orphaned with no teardown.
    (Named distinctly from ``TestDoUpPartialFailureTeardown`` below, which covers the
    require_env_bin missing-binary arm — same subject, different failure class.)
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

    def test_health_timeout_with_live_listener_tears_down(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            listeners_dir = root / "listeners"
            stub_bin = root / "bin"
            conda_dir = root / "conda"
            listeners_dir.mkdir()
            stub_bin.mkdir()
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)

            # Env bin: parse --port, record pid for the ss stub, sleep (no real bind).
            data_bin = conda_dir / "envs" / "JuniperData" / "bin"
            data_bin.mkdir(parents=True)
            _write_stub(
                data_bin / "python",
                "#!/usr/bin/env bash\n" "set -euo pipefail\n"
                # Answer data_up's free-threading probe (free-threaded) without sleeping.
                'if [[ "${1-}" == "-c" ]]; then echo 1; exit 0; fi\n' 'port=""\n' "while [[ $# -gt 0 ]]; do\n" '  case "$1" in\n' '    --port) port="$2"; shift 2 ;;\n' "    *) shift ;;\n" "  esac\n" "done\n" f'printf "%s\\n" "$$" >"{listeners_dir}/$port.pid"\n'
                # No ``exec``: keep this bash pid's cmdline stable for kill_verified_pid.
                "sleep 60\n",
            )
            # cascor bin present but unused once data fails closed.
            cascor_bin = conda_dir / "envs" / "JuniperCascor1" / "bin"
            cascor_bin.mkdir(parents=True)
            _write_stub(cascor_bin / "uvicorn", "#!/usr/bin/env bash\nsleep 60\n")

            # curl always fails → wait_for_health times out (the false-green class).
            _write_stub(stub_bin / "curl", "#!/usr/bin/env bash\nexit 1\n")
            _write_stub(
                stub_bin / "ss",
                "#!/usr/bin/env bash\n" "set -euo pipefail\n" 'port=""\n' 'for a in "$@"; do\n' '  case "$a" in\n' '    sport\\ =\\ :*) port="${a##*:}" ;;\n' "  esac\n" "done\n" f'listener="{listeners_dir}/$port.pid"\n' 'if [[ -n "$port" && -f "$listener" ]]; then\n' '  pid="$(cat "$listener")"\n' '  echo "LISTEN 0 128 127.0.0.1:${port} 0.0.0.0:* users:((\\"python\\",pid=${pid},fd=3))"\n' "fi\n" "exit 0\n",
            )
            _write_stub(stub_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
            _write_stub(stub_bin / "socat", "#!/usr/bin/env bash\nexec sleep 60\n")

            env = RedactedEnv(os.environ)
            env.update(
                {
                    "JUNIPER_EXP_RUN_ROOT": str(root / "runs"),
                    "JUNIPER_EXP_LOCK_ROOT": str(root / "locks"),
                    "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
                    "JUNIPER_EXP_PROJECT_DIR": str(project_dir),
                    "JUNIPER_EXP_CONDA_DIR": str(conda_dir),
                    "JUNIPER_EXP_HEALTH_TIMEOUT": "2",
                    "JUNIPER_EXP_KILL_TIMEOUT": "5",
                    "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
                }
            )

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "--up", "--cascor"],
                capture_output=True,
                text=True,
                env=env,
                timeout=DO_UP_PARTIAL_TIMEOUT_SECONDS,
            )
            child_pid: int | None = None
            # Port is allocated starting at 8110 when free.
            for pid_path in listeners_dir.glob("*.pid"):
                try:
                    child_pid = int(pid_path.read_text().strip())
                except ValueError:
                    child_pid = None
                break
            try:
                self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("bring-up failed — tearing the partial run back down", result.stdout)
                self.assertIn("failed to become healthy", result.stdout)
                # Must NOT report a successful bring-up (the pre-fix false-green).
                self.assertNotIn(" is up ===", result.stdout)
                if child_pid is not None:
                    for _ in range(60):
                        if not Path(f"/proc/{child_pid}").exists():
                            break
                        time.sleep(0.1)
                    self.assertFalse(
                        Path(f"/proc/{child_pid}").exists(),
                        "partial teardown must kill the data listener after health timeout",
                    )
                # teardown.json proves teardown_run ran (ports released / artifacts kept).
                run_dirs = list((root / "runs").glob("*"))
                self.assertEqual(len(run_dirs), 1, msg=result.stdout)
                self.assertTrue((run_dirs[0] / "teardown.json").exists(), msg=result.stdout)
                self.assertTrue((run_dirs[0] / "artifacts").exists())
            finally:
                if child_pid is not None:
                    self._force_kill(child_pid)

    def test_bridge_failure_after_healthy_services_tears_down(self) -> None:
        """A failed bridge after healthy services must teardown (not orphan via set -e).

        The docker stub reports no monitoring network AND no default-bridge gateway,
        so ``discover_gateway_ip`` fails deterministically regardless of whether the
        host has a real ``socat`` on PATH (asserting on the socat require_cmd arm
        would be environment-dependent).
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "Juniper"
            listeners_dir = root / "listeners"
            stub_bin = root / "bin"
            conda_dir = root / "conda"
            listeners_dir.mkdir()
            stub_bin.mkdir()
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)

            listener_stub = (
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                # Answer data_up's free-threading probe (free-threaded) without sleeping.
                'if [[ "${1-}" == "-c" ]]; then echo 1; exit 0; fi\n'
                'port=""\n'
                "while [[ $# -gt 0 ]]; do\n"
                '  case "$1" in\n'
                '    --port) port="$2"; shift 2 ;;\n'
                "    *) shift ;;\n"
                "  esac\n"
                "done\n"
                f'printf "%s\\n" "$$" >"{listeners_dir}/$port.pid"\n'
                # No ``exec``: keep this bash pid's cmdline stable for kill_verified_pid.
                "sleep 60\n"
            )
            for env_name, bin_name in (
                ("JuniperData", "python"),
                ("JuniperCascor1", "uvicorn"),
            ):
                bin_dir = conda_dir / "envs" / env_name / "bin"
                bin_dir.mkdir(parents=True, exist_ok=True)
                _write_stub(bin_dir / bin_name, listener_stub)

            # Health OK only once the service's listener pidfile exists (faithful to a
            # real server, whose health answer arrives over the LISTENING socket) so
            # record_listener_pid cannot race the stub's pidfile write; socat absent.
            _write_stub(
                stub_bin / "curl",
                "#!/usr/bin/env bash\n" 'url="${!#}"\n' 'port="${url##*:}"\n' 'port="${port%%/*}"\n' f'[[ -n "$port" && -f "{listeners_dir}/$port.pid" ]] || exit 1\n' "exit 0\n",
            )
            _write_stub(
                stub_bin / "ss",
                "#!/usr/bin/env bash\n" "set -euo pipefail\n" 'port=""\n' 'for a in "$@"; do\n' '  case "$a" in\n' '    sport\\ =\\ :*) port="${a##*:}" ;;\n' "  esac\n" "done\n" f'listener="{listeners_dir}/$port.pid"\n' 'if [[ -n "$port" && -f "$listener" ]]; then\n' '  pid="$(cat "$listener")"\n' '  echo "LISTEN 0 128 127.0.0.1:${port} 0.0.0.0:* users:((\\"python\\",pid=${pid},fd=3))"\n' "fi\n" "exit 0\n",
            )
            # docker reports no networks at all → discover_gateway_ip must return 1.
            _write_stub(stub_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
            # socat present-but-never-invoked: require_cmd must pass on hosts WITHOUT a
            # real socat (CI runners) so the deterministic failure is the gateway probe.
            _write_stub(stub_bin / "socat", "#!/usr/bin/env bash\nexit 0\n")

            env = RedactedEnv(os.environ)
            env.update(
                {
                    "JUNIPER_EXP_RUN_ROOT": str(root / "runs"),
                    "JUNIPER_EXP_LOCK_ROOT": str(root / "locks"),
                    "JUNIPER_EXP_DEPLOY_DIR": str(root / "deploy"),
                    "JUNIPER_EXP_PROJECT_DIR": str(project_dir),
                    "JUNIPER_EXP_CONDA_DIR": str(conda_dir),
                    "JUNIPER_EXP_HEALTH_TIMEOUT": "4",
                    "JUNIPER_EXP_KILL_TIMEOUT": "5",
                    "PATH": str(stub_bin) + os.pathsep + "/usr/bin:/bin",
                }
            )

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "--up", "--cascor", "--grafana-bridge"],
                capture_output=True,
                text=True,
                env=env,
                timeout=DO_UP_PARTIAL_TIMEOUT_SECONDS,
            )
            child_pids: list[int] = []
            for pid_path in listeners_dir.glob("*.pid"):
                try:
                    child_pids.append(int(pid_path.read_text().strip()))
                except ValueError:
                    pass
            try:
                self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("grafana bridge failed — tearing the run back down", result.stdout)
                self.assertIn("no monitoring network and no default-bridge gateway", result.stdout)
                self.assertNotIn(" is up ===", result.stdout)
                for child_pid in child_pids:
                    for _ in range(60):
                        if not Path(f"/proc/{child_pid}").exists():
                            break
                        time.sleep(0.1)
                    self.assertFalse(
                        Path(f"/proc/{child_pid}").exists(),
                        f"bridge-failure teardown must kill listener pid {child_pid}",
                    )
                run_dirs = list((root / "runs").glob("*"))
                self.assertEqual(len(run_dirs), 1, msg=result.stdout)
                self.assertTrue((run_dirs[0] / "teardown.json").exists(), msg=result.stdout)
            finally:
                for child_pid in child_pids:
                    self._force_kill(child_pid)


class _LiveUpHarness(unittest.TestCase):
    """Shared helpers for live ``*_up`` compose (F-6 ss listener after health)."""

    def _common_prelude(
        self,
        *,
        run_dir: Path,
        conda_dir: Path,
        project_dir: Path,
        data_port: str = "68110",
        cascor_port: str = "68230",
        recurrence_port: str = "68260",
    ) -> str:
        # Concatenate (do not f-string) so bash `${...}` in extracts stay literal.
        return (
            "set -euo pipefail\n"
            'SCRIPT_NAME="experiment_stack.bash"\n'
            "DRY_RUN=0\n"
            "CONDA_ACTIVATE=0\n"
            f'CONDA_DIR="{conda_dir}"\n'
            f'PROJECT_DIR="{project_dir}"\n'
            f'CASCOR_SRC_DIR="{project_dir}/juniper-cascor/src"\n'
            f'RUN_DIR="{run_dir}"\n'
            f'LOG_DIR="{run_dir}/logs"\n'
            f'DATA_PORT="{data_port}"\n'
            f'CASCOR_PORT="{cascor_port}"\n'
            f'RECURRENCE_PORT="{recurrence_port}"\n'
            f'DATA_URL="http://127.0.0.1:{data_port}"\n'
            'DATA_CONDA="JuniperData"\n'
            'CASCOR_CONDA="JuniperCascor1"\n'
            'RECURRENCE_CONDA="JuniperCascor1"\n'
            "HEALTH_TIMEOUT=4\n"
            'CONFIG_PATH=""\n'
            'log() { echo "[${SCRIPT_NAME}] $*"; }\n'
            'banner() { echo ""; echo "[${SCRIPT_NAME}] === $* ==="; }\n'
            'announce() { echo "[${SCRIPT_NAME}] \\$ $*"; }\n'
            'is_dry() { [[ "${DRY_RUN}" == "1" ]]; }\n' + _extract_experiment_fn("require_cmd") + _extract_experiment_fn("ensure_dir") + _extract_experiment_fn("env_bin") + _extract_experiment_fn("require_env_bin") + _extract_experiment_fn("port_listener_pid") + _extract_experiment_fn("proc_cmdline") + _extract_experiment_fn("wait_for_health") + _extract_experiment_fn("record_listener_pid") + _extract_experiment_fn("record_launch_env")
        )

    def _run_harness(self, harness: str, *, stub_bin: Path) -> subprocess.CompletedProcess[str]:
        env = RedactedEnv(os.environ)
        env["PATH"] = str(stub_bin) + os.pathsep + "/usr/bin:/bin"
        # The launcher is the only thing allowed to set PYTHON_GIL here; an ambient value
        # would leak into the stub's recorded env and decide the GIL assertions for us.
        env.pop("PYTHON_GIL", None)
        return subprocess.run(
            ["/bin/bash", "-c", harness],
            capture_output=True,
            text=True,
            env=env,
            timeout=LIVE_UP_TIMEOUT_SECONDS,
        )


class TestDataUpLive(_LiveUpHarness):
    """Behavioral pins for live ``data_up`` (direct env-bin + F-6 listener pid)."""

    def test_happy_path_gil_env_listener_pid_and_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            marker_dir = root / "markers"
            listeners_dir = root / "listeners"
            project_dir = root / "project"
            conda_dir = root / "conda"
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)
            stub_bin = _stage_live_path_stubs(root, listeners_dir)
            _write_listening_env_bin(
                conda_dir / "envs" / "JuniperData" / "bin" / "python",
                listeners_dir=listeners_dir,
                marker_dir=marker_dir,
                label="data",
            )
            harness = self._common_prelude(run_dir=run_dir, conda_dir=conda_dir, project_dir=project_dir) + _extract_experiment_fn("data_up") + "data_up\n"
            result = self._run_harness(harness, stub_bin=stub_bin)
            pid_path = run_dir / "juniper-data.pid"
            child_pid: int | None = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("juniper-data is healthy", result.stdout)
                self.assertTrue(pid_path.is_file(), "data_up must record listener pid via ss (F-6)")
                child_pid = int(pid_path.read_text().strip())
                self.assertTrue(Path(f"/proc/{child_pid}").exists())
                self.assertEqual(
                    child_pid,
                    int((listeners_dir / "68110.pid").read_text().strip()),
                    "pidfile must match the ss-reported listener, not a subshell $!",
                )
                # F-E2E-005: compare against per-key line lists, never the whole blob.
                env_text = (marker_dir / "data.env").read_text()
                self.assertIn("PYTHON_GIL=0", _env_lines_for_key(env_text, "PYTHON_GIL"))
                self.assertIn(f"JUNIPER_DATA_STORAGE_PATH={run_dir}/data", _env_lines_for_key(env_text, "JUNIPER_DATA_STORAGE_PATH"))
                self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={run_dir}/equities-cache", _env_lines_for_key(env_text, "JUNIPER_DATA_EQUITIES_CACHE_DIR"))
                self.assertIn("JUNIPER_DATA_METRICS_ENABLED=true", _env_lines_for_key(env_text, "JUNIPER_DATA_METRICS_ENABLED"))
                args = (marker_dir / "data.args").read_text()
                self.assertIn("-m", args)
                self.assertIn("juniper_data", args)
                self.assertIn("--port", args)
                self.assertIn("68110", args)
                cmdline = (run_dir / "juniper-data.cmdline").read_text()
                self.assertTrue(cmdline.strip(), "cmdline sidecar must be recorded for teardown")
                launch_env = (run_dir / "env" / "launch.env").read_text()
                self.assertIn("PYTHON_GIL=0", launch_env)
            finally:
                if child_pid is not None:
                    _force_kill(child_pid)

    def test_stock_build_omits_python_gil(self) -> None:
        """A stock (non-free-threaded) CPython must never be handed ``PYTHON_GIL=0``.

        Passing it is FATAL at interpreter startup — "Fatal Python error:
        config_read_gil: Disabling the GIL is not supported by this build" — so the data
        leg dies pre-bind and burns the whole health gate (the 2026-08-09 host regression
        that also hit ``isolated_stack.bash``). The probe answering 0 must OMIT the toggle
        from the launched env AND record it honestly (empty) in ``env/launch.env``.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            marker_dir = root / "markers"
            listeners_dir = root / "listeners"
            project_dir = root / "project"
            conda_dir = root / "conda"
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)
            marker_dir.mkdir(parents=True)
            (marker_dir / "gil_probe_answer").write_text("0\n")
            stub_bin = _stage_live_path_stubs(root, listeners_dir)
            _write_listening_env_bin(
                conda_dir / "envs" / "JuniperData" / "bin" / "python",
                listeners_dir=listeners_dir,
                marker_dir=marker_dir,
                label="data",
            )
            harness = self._common_prelude(run_dir=run_dir, conda_dir=conda_dir, project_dir=project_dir) + _extract_experiment_fn("data_up") + "data_up\n"
            result = self._run_harness(harness, stub_bin=stub_bin)
            pid_path = run_dir / "juniper-data.pid"
            child_pid: int | None = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertTrue(pid_path.is_file(), "an omitted toggle must not disturb the F-6 listener pid")
                child_pid = int(pid_path.read_text().strip())
                # Assert over FILTERED lines, never the whole recorded env: the stub's
                # ``JUNIPER_`` grep also captures ambient secrets, and a failing assertion
                # renders its arguments (the tests/redacted_env.py leak class).
                env_lines = (marker_dir / "data.env").read_text().splitlines()
                self.assertEqual(
                    [line for line in env_lines if line.startswith("PYTHON_GIL")],
                    [],
                    "a stock CPython must be handed no PYTHON_GIL at all",
                )
                # The rest of the §6.1 recipe is untouched by the conditional.
                data_lines = [line for line in env_lines if line.startswith("JUNIPER_DATA_")]
                self.assertIn(f"JUNIPER_DATA_STORAGE_PATH={run_dir}/data", data_lines)
                self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={run_dir}/equities-cache", data_lines)
                self.assertIn("JUNIPER_DATA_METRICS_ENABLED=true", data_lines)
                # env/launch.env is evidence: empty value, never a false PYTHON_GIL=0.
                launch_env = (run_dir / "env" / "launch.env").read_text()
                self.assertNotIn("PYTHON_GIL=0", launch_env)
                self.assertIn("PYTHON_GIL=\n", launch_env)
            finally:
                if child_pid is not None:
                    _force_kill(child_pid)


class TestCascorUpLive(_LiveUpHarness):
    """Behavioral pins for live ``cascor_up`` (LD_LIBRARY_PATH='', data URL, src CWD)."""

    def test_happy_path_libtorch_neutral_data_url_and_listener(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            marker_dir = root / "markers"
            listeners_dir = root / "listeners"
            project_dir = root / "project"
            conda_dir = root / "conda"
            cascor_src = project_dir / "juniper-cascor" / "src"
            cascor_src.mkdir(parents=True)
            stub_bin = _stage_live_path_stubs(root, listeners_dir)
            _write_listening_env_bin(
                conda_dir / "envs" / "JuniperCascor1" / "bin" / "uvicorn",
                listeners_dir=listeners_dir,
                marker_dir=marker_dir,
                label="cascor",
            )
            harness = self._common_prelude(run_dir=run_dir, conda_dir=conda_dir, project_dir=project_dir) + _extract_experiment_fn("cascor_up") + "cascor_up\n"
            result = self._run_harness(harness, stub_bin=stub_bin)
            pid_path = run_dir / "juniper-cascor.pid"
            child_pid: int | None = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("juniper-cascor is healthy", result.stdout)
                self.assertTrue(pid_path.is_file())
                child_pid = int(pid_path.read_text().strip())
                # F-E2E-005: compare against per-key line lists, never the whole blob.
                env_text = (marker_dir / "cascor.env").read_text()
                self.assertIn("LD_LIBRARY_PATH=", _env_lines_for_key(env_text, "LD_LIBRARY_PATH"))
                self.assertIn("JUNIPER_DATA_URL=http://127.0.0.1:68110", _env_lines_for_key(env_text, "JUNIPER_DATA_URL"))
                self.assertIn("JUNIPER_CASCOR_AUTO_START=false", _env_lines_for_key(env_text, "JUNIPER_CASCOR_AUTO_START"))
                self.assertIn("JUNIPER_CASCOR_METRICS_ENABLED=true", _env_lines_for_key(env_text, "JUNIPER_CASCOR_METRICS_ENABLED"))
                args = (marker_dir / "cascor.args").read_text()
                self.assertIn("api.app:create_app", args)
                self.assertIn("--factory", args)
                self.assertIn("68230", args)
                self.assertIn(f"PWD={cascor_src}", (marker_dir / "cascor.env").read_text())
            finally:
                if child_pid is not None:
                    _force_kill(child_pid)

    def test_missing_uvicorn_aborts_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            listeners_dir = root / "listeners"
            project_dir = root / "project"
            conda_dir = root / "conda"
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)
            (conda_dir / "envs" / "JuniperCascor1" / "bin").mkdir(parents=True)
            stub_bin = _stage_live_path_stubs(root, listeners_dir)
            harness = self._common_prelude(run_dir=run_dir, conda_dir=conda_dir, project_dir=project_dir) + _extract_experiment_fn("cascor_up") + "set +e\n" + "cascor_up\n" + "echo STATUS=$?\n"
            result = self._run_harness(harness, stub_bin=stub_bin)
            # Harness ends with `echo STATUS=$?` under `set +e`; a non-zero STATUS is the pin.
            self.assertIn("STATUS=1", result.stdout, msg=result.stderr + result.stdout)
            self.assertIn("uvicorn not found in conda env", result.stdout)
            self.assertFalse((run_dir / "juniper-cascor.pid").exists())


class TestRecurrenceUpLive(_LiveUpHarness):
    """Behavioral pins for live ``recurrence_up`` (ready health + metrics/rate-limit env)."""

    def test_happy_path_ready_health_and_listener(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            marker_dir = root / "markers"
            listeners_dir = root / "listeners"
            project_dir = root / "project"
            conda_dir = root / "conda"
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)
            stub_bin = _stage_live_path_stubs(root, listeners_dir)
            _write_listening_env_bin(
                conda_dir / "envs" / "JuniperCascor1" / "bin" / "juniper-recurrence",
                listeners_dir=listeners_dir,
                marker_dir=marker_dir,
                label="recurrence",
            )
            harness = self._common_prelude(run_dir=run_dir, conda_dir=conda_dir, project_dir=project_dir) + _extract_experiment_fn("recurrence_up") + "recurrence_up\n"
            result = self._run_harness(harness, stub_bin=stub_bin)
            pid_path = run_dir / "juniper-recurrence.pid"
            child_pid: int | None = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn("juniper-recurrence is healthy", result.stdout)
                self.assertTrue(pid_path.is_file())
                child_pid = int(pid_path.read_text().strip())
                # F-E2E-005: compare against per-key line lists, never the whole blob.
                env_text = (marker_dir / "recurrence.env").read_text()
                self.assertIn("JUNIPER_RECURRENCE_METRICS_ENABLED=true", _env_lines_for_key(env_text, "JUNIPER_RECURRENCE_METRICS_ENABLED"))
                self.assertIn("JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false", _env_lines_for_key(env_text, "JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED"))
                self.assertIn("JUNIPER_DATA_URL=http://127.0.0.1:68110", _env_lines_for_key(env_text, "JUNIPER_DATA_URL"))
                args = (marker_dir / "recurrence.args").read_text()
                self.assertIn("serve", args)
                self.assertIn("68260", args)
            finally:
                if child_pid is not None:
                    _force_kill(child_pid)


class TestDoUpPartialFailureTeardown(unittest.TestCase):
    """``do_up`` must tear a partial run back down when a later service fails."""

    def test_cascor_missing_bin_tears_down_data_and_releases_locks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "runs"
            lock_root = root / "locks"
            deploy_dir = root / "deploy"
            project_dir = root / "project"
            conda_dir = root / "conda"
            listeners_dir = root / "listeners"
            marker_dir = root / "markers"
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)
            stub_bin = _stage_live_path_stubs(root, listeners_dir)
            _write_listening_env_bin(
                conda_dir / "envs" / "JuniperData" / "bin" / "python",
                listeners_dir=listeners_dir,
                marker_dir=marker_dir,
                label="data",
            )
            # Cascor env exists but uvicorn is missing → require_env_bin fails after data_up.
            (conda_dir / "envs" / "JuniperCascor1" / "bin").mkdir(parents=True)

            env = RedactedEnv(
                os.environ,
                JUNIPER_EXP_RUN_ROOT=str(run_root),
                JUNIPER_EXP_LOCK_ROOT=str(lock_root),
                JUNIPER_EXP_DEPLOY_DIR=str(deploy_dir),
                JUNIPER_EXP_PROJECT_DIR=str(project_dir),
                JUNIPER_EXP_CONDA_DIR=str(conda_dir),
                JUNIPER_EXP_HEALTH_TIMEOUT="4",
                JUNIPER_EXP_KILL_TIMEOUT="5",
                PATH=str(stub_bin) + os.pathsep + "/usr/bin:/bin",
            )
            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "--up", "--cascor", "--experiment", "partial-fail"],
                capture_output=True,
                text=True,
                env=env,
                timeout=TEARDOWN_TIMEOUT_SECONDS,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("bring-up failed — tearing the partial run back down", result.stdout)
            self.assertIn("uvicorn not found in conda env", result.stdout)

            runs = list(run_root.iterdir()) if run_root.is_dir() else []
            self.assertEqual(len(runs), 1, f"expected one partial RUN_DIR, got {runs}")
            run_dir = runs[0]
            self.assertTrue((run_dir / "ports.json").is_file(), "ports.json must exist before launches")
            self.assertTrue((run_dir / "teardown.json").is_file(), "teardown_run must write teardown.json")
            self.assertFalse((run_dir / "juniper-data.pid").exists(), "teardown must clear the data pidfile")
            self.assertFalse((lock_root / "8110.lock").exists(), "data port lock must be released")
            self.assertFalse((lock_root / "8230.lock").exists(), "cascor port lock must be released")
            data_listener = listeners_dir / "8110.pid"
            if data_listener.is_file():
                pid = int(data_listener.read_text().strip())
                for _ in range(60):
                    if not Path(f"/proc/{pid}").exists():
                        break
                    time.sleep(0.1)
                self.assertFalse(Path(f"/proc/{pid}").exists(), "partial teardown must kill the data listener")


if __name__ == "__main__":
    unittest.main()
