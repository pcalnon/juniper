#!/usr/bin/env python3
"""Tests for util/wait_for_checks.py (required-context CI waiter).

``util/`` is outside every pre-commit Python hook's scope (flake8/black/bandit
scope to ``scripts/`` + ``tests/``), so this suite IS the gate.

Hermetic: ``gh`` is a PATH stub that replays a *scripted sequence* of canned
responses -- one per poll -- so the growing-rollup case can actually be exercised.
No network, no real repo.

Contract pinned here, trap by trap. Both traps below were live bugs in
hand-rolled waiters during the 2026-08-16 throttle arc; each has a test that
fails if the implementation regresses to the naive form.

- **Terminal is defined POSITIVELY.** An in-progress check run has
  ``conclusion: null`` and no ``state``. ``is_terminal`` must call that NOT done.
  A "not in my list of pending states" implementation passes the all-green test
  and fails ``test_in_progress_null_conclusion_is_not_terminal``.
- **The rollup GROWS.** Waiting until "every row I can see is terminal" finishes
  early during a lull between job waves. The wait must be anchored to the
  ruleset's required contexts, so a required context that has not appeared yet
  counts as unfinished -- ``GrowingRollupTest``, which pins BOTH anchors so the
  naive behaviour is an executable negative control rather than a claim.
- **``absent`` is distinct from ``running``.** A required context that never
  reports (the ``[skip ci]`` orphan class) must be named as absent on timeout,
  not silently waited on.
- **A failed probe is never an empty result.** ``gh`` exiting nonzero raises
  ``ProbeError`` -> exit 3. Defaulting to ``[]`` is the same conflation as trap 1.
- **A missing required-status-checks rule is a hard error**, not a silent
  downgrade to the observed rollup; ``--anchor observed`` is the explicit opt-in.
- **Read-only.** The stub records argv and the suite asserts no mutating verb
  (``merge``, ``update-branch``, ``create``, ``comment``, ``edit``) is ever issued.

Run: python3 -m unittest -v tests/test_wait_for_checks.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-17
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess  # nosec B404 - drives the util's CLI with a PATH-stubbed `gh`
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from tests.redacted_env import RedactedEnv


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_MODULE_PATH = _REPO_ROOT / "util" / "wait_for_checks.py"


def _load():
    spec = importlib.util.spec_from_file_location("wait_for_checks", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()

REQUIRED = ["Alpha", "Beta", "Gamma"]


def _rules_payload(contexts=REQUIRED, *, include_rule=True):
    rules = [{"type": "pull_request", "parameters": {}}]
    if include_rule:
        rules.append(
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [{"context": c} for c in contexts],
                },
            }
        )
    return rules


def _run(name, *, conclusion=None, status="COMPLETED"):
    """A check-run rollup row. ``conclusion=None`` models an in-flight job."""
    row = {"__typename": "CheckRun", "name": name, "status": status}
    if conclusion is not None:
        row["conclusion"] = conclusion
    return row


def _ctx(name, state):
    """A legacy commit-status rollup row."""
    return {"__typename": "StatusContext", "context": name, "state": state}


class _Harness:
    """Tempdir with a stub `gh` that replays a scripted sequence of rollups."""

    def __init__(self, tmp: Path, *, rollups, rules=None, pr_state="OPEN", merge_state="CLEAN", fail_on=None, flaky_on=None, flaky_times=0):
        self.tmp = tmp
        self.log = tmp / "gh.log"
        self.log.write_text("", encoding="utf-8")
        self.counter = tmp / "poll.n"
        self.counter.write_text("0", encoding="utf-8")
        self.flaky_counter = tmp / "flaky.n"
        self.flaky_counter.write_text("0", encoding="utf-8")

        seq_dir = tmp / "seq"
        seq_dir.mkdir()
        for i, rows in enumerate(rollups):
            (seq_dir / f"{i}.json").write_text(json.dumps({"statusCheckRollup": rows}), encoding="utf-8")
        # Past the end of the script, keep replaying the final entry.
        self.last_index = len(rollups) - 1

        rules_file = tmp / "rules.json"
        rules_file.write_text(json.dumps(_rules_payload() if rules is None else rules), encoding="utf-8")

        pr_file = tmp / "pr.json"
        pr_file.write_text(
            json.dumps(
                {
                    "baseRefName": "main",
                    "state": pr_state,
                    "mergeStateStatus": merge_state,
                    "url": "https://github.com/pcalnon/juniper-ml/pull/1",
                }
            ),
            encoding="utf-8",
        )

        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(
            "#!/usr/bin/env bash\n" f'LOG="{self.log}"\n' f'SEQ="{seq_dir}"\n' f'CNT="{self.counter}"\n' f"LAST={self.last_index}\n" 'printf "%s\\n" "$*" >>"$LOG"\n'
            # Optional forced failure, to prove a bad probe is a hard error.
            f'if [ -n "{fail_on or ""}" ]; then\n' f'  case "$*" in *"{fail_on or "@@never@@"}"*) echo "boom" >&2; exit 1 ;; esac\n' "fi\n"
            # Optional FLAKY failure: fail the first N matching calls, then succeed.
            # Models the transient TLS/EOF errors seen in live use.
            f'if [ -n "{flaky_on or ""}" ]; then\n'
            f'  case "$*" in *"{flaky_on or "@@never@@"}"*)\n'
            f'    fn=$(cat "{self.flaky_counter}")\n'
            f'    if [ "$fn" -lt {int(flaky_times)} ]; then\n'
            f'      echo $((fn + 1)) >"{self.flaky_counter}"\n'
            '      echo "transient: unexpected EOF" >&2; exit 1\n'
            "    fi ;;\n"
            "  esac\n"
            "fi\n"
            'case "$*" in\n'
            '  *"statusCheckRollup"*)\n'
            '    n=$(cat "$CNT")\n'
            "    i=$n\n"
            '    if [ "$i" -gt "$LAST" ]; then i=$LAST; fi\n'
            '    cat "$SEQ/$i.json"\n'
            '    echo $((n + 1)) >"$CNT"\n'
            "    exit 0 ;;\n"
            '  *"baseRefName"*)\n'
            f'    cat "{pr_file}"; exit 0 ;;\n'
            '  *"rules/branches"*)\n'
            f'    cat "{rules_file}"; exit 0 ;;\n'
            "esac\n"
            'echo "unexpected gh invocation: $*" >&2\n'
            "exit 1\n",
            encoding="utf-8",
        )
        gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
        self.bin_dir = bin_dir

    def env(self):
        env = RedactedEnv(os.environ)
        env["PATH"] = str(self.bin_dir) + os.pathsep + env.get("PATH", "")
        return env

    def calls(self) -> list:
        return [ln for ln in self.log.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _cli(harness: _Harness, extra=None) -> tuple:
    argv = [sys.executable, str(_MODULE_PATH), "--pr", "1", "--interval", "1", "--timeout", "3"]
    argv.extend(extra or [])
    proc = subprocess.run(  # nosec B603 - fixed argv, hermetic PATH stub
        argv,
        capture_output=True,
        text=True,
        env=harness.env(),
        cwd=str(_REPO_ROOT),
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


class TerminalDefinitionTest(unittest.TestCase):
    """Trap 1: terminal must be a positive test, not the complement of 'pending'."""

    def test_in_progress_null_conclusion_is_not_terminal(self):
        row = {"name": "Alpha", "conclusion": "", "state": ""}
        self.assertFalse(MOD.is_terminal(row))
        self.assertEqual(MOD.outcome_of(row), "")

    def test_queued_and_in_progress_are_not_terminal(self):
        for status in ("QUEUED", "IN_PROGRESS", "WAITING", "PENDING", "REQUESTED"):
            with self.subTest(status=status):
                self.assertFalse(MOD.is_terminal({"name": "A", "conclusion": "", "state": status}))

    def test_every_completed_conclusion_is_terminal(self):
        for concl in sorted(MOD.TERMINAL_CONCLUSIONS):
            with self.subTest(conclusion=concl):
                self.assertTrue(MOD.is_terminal({"name": "A", "conclusion": concl, "state": ""}))

    def test_legacy_status_context_states(self):
        self.assertTrue(MOD.is_terminal({"name": "A", "conclusion": "", "state": "SUCCESS"}))
        self.assertTrue(MOD.is_terminal({"name": "A", "conclusion": "", "state": "FAILURE"}))
        self.assertFalse(MOD.is_terminal({"name": "A", "conclusion": "", "state": "EXPECTED"}))

    def test_unknown_future_conclusion_reads_as_unfinished(self):
        """A value GitHub adds later must not be mistaken for finished."""
        self.assertFalse(MOD.is_terminal({"name": "A", "conclusion": "FLARGLE", "state": ""}))


class ClassifyTest(unittest.TestCase):
    def test_absent_is_distinct_from_running(self):
        rows = [
            {"name": "Alpha", "conclusion": "SUCCESS", "state": ""},
            {"name": "Beta", "conclusion": "", "state": ""},
        ]
        res = MOD.classify(REQUIRED, rows)
        self.assertEqual([c for c, _ in res["done"]], ["Alpha"])
        self.assertEqual(res["running"], ["Beta"])
        self.assertEqual(res["absent"], ["Gamma"])
        self.assertFalse(res["settled"])

    def test_settled_only_when_nothing_running_or_absent(self):
        rows = [{"name": c, "conclusion": "SUCCESS", "state": ""} for c in REQUIRED]
        res = MOD.classify(REQUIRED, rows)
        self.assertTrue(res["settled"])
        self.assertEqual(res["failed"], [])

    def test_failing_conclusions_are_collected(self):
        rows = [
            {"name": "Alpha", "conclusion": "SUCCESS", "state": ""},
            {"name": "Beta", "conclusion": "FAILURE", "state": ""},
            {"name": "Gamma", "conclusion": "TIMED_OUT", "state": ""},
        ]
        res = MOD.classify(REQUIRED, rows)
        self.assertTrue(res["settled"])
        self.assertEqual([c for c, _ in res["failed"]], ["Beta", "Gamma"])

    def test_neutral_and_skipped_are_done_but_not_failures(self):
        rows = [
            {"name": "Alpha", "conclusion": "NEUTRAL", "state": ""},
            {"name": "Beta", "conclusion": "SKIPPED", "state": ""},
            {"name": "Gamma", "conclusion": "SUCCESS", "state": ""},
        ]
        res = MOD.classify(REQUIRED, rows)
        self.assertTrue(res["settled"])
        self.assertEqual(res["failed"], [])

    def test_non_required_noise_is_ignored(self):
        """Cursor-automation rows and other extras must not gate the wait."""
        rows = [{"name": c, "conclusion": "SUCCESS", "state": ""} for c in REQUIRED]
        rows.append({"name": "Cursor Automation: Find bugs", "conclusion": "", "state": ""})
        res = MOD.classify(REQUIRED, rows)
        self.assertTrue(res["settled"])


class GrowingRollupTest(unittest.TestCase):
    """Trap 2: a lull between job waves must not read as completion.

    Wave 1 shows only ``Alpha``, already SUCCESS -- a waiter anchored on the
    observed rollup declares victory there and returns after ONE poll. Wave 2 adds
    ``Beta``/``Gamma`` still in flight; wave 3 completes them. The required-context
    anchor is what forces the loop past wave 1.
    """

    WAVES = [
        [{"name": "Alpha", "conclusion": "SUCCESS", "state": ""}],
        [
            {"name": "Alpha", "conclusion": "SUCCESS", "state": ""},
            {"name": "Beta", "conclusion": "", "state": ""},
            {"name": "Gamma", "conclusion": "", "state": ""},
        ],
        [{"name": c, "conclusion": "SUCCESS", "state": ""} for c in REQUIRED],
    ]

    def _wave_feeder(self):
        calls = {"n": 0}

        def fake_rollup(_owner, _repo, _pr):
            idx = min(calls["n"], len(self.WAVES) - 1)
            calls["n"] += 1
            return list(self.WAVES[idx])

        return fake_rollup

    def _run_wait(self, anchor):
        facts = {"base": "main", "state": "OPEN", "merge_state": "CLEAN", "url": "u"}
        with unittest.mock.patch.object(MOD, "rollup", self._wave_feeder()), unittest.mock.patch.object(MOD, "pr_facts", lambda *a: dict(facts)), unittest.mock.patch.object(MOD, "required_contexts", lambda *a: list(REQUIRED)):
            return MOD.wait_for(
                "o",
                "r",
                1,
                anchor=anchor,
                timeout=1000,
                interval=0,
                sleeper=lambda _: None,
                clock=lambda: 0.0,
            )

    def test_required_anchor_keeps_polling_through_the_lull(self):
        res = self._run_wait("required")
        self.assertEqual(res["status"], "green")
        self.assertGreaterEqual(res["polls"], 3, "must keep polling while required contexts are absent")

    def test_observed_anchor_demonstrates_the_early_finish(self):
        """Negative control: this is the bug the required anchor exists to avoid.

        Pinning it makes the difference between the two anchors executable rather
        than a claim in a docstring -- and documents why ``observed`` is opt-in.
        """
        res = self._run_wait("observed")
        self.assertEqual(res["status"], "green")
        self.assertEqual(res["polls"], 1, "observed anchor finishes on wave 1 -- the trap")


class CliTest(unittest.TestCase):
    def test_all_required_green_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[_run(c, conclusion="SUCCESS") for c in REQUIRED]])
            rc, out, err = _cli(h)
        self.assertEqual(rc, 0, f"out={out} err={err}")
        self.assertIn("GREEN", out)
        self.assertIn("3/3", out)

    def test_required_failure_exits_one_and_names_it(self):
        with tempfile.TemporaryDirectory() as td:
            rollup = [_run("Alpha", conclusion="SUCCESS"), _run("Beta", conclusion="FAILURE"), _run("Gamma", conclusion="SUCCESS")]
            h = _Harness(Path(td), rollups=[rollup])
            rc, out, err = _cli(h)
        self.assertEqual(rc, 1, f"out={out} err={err}")
        self.assertIn("FAILED", out)
        self.assertIn("Beta", out)

    def test_absent_required_context_times_out_and_is_named(self):
        """The skip-ci orphan class: a required context that never reports."""
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[_run("Alpha", conclusion="SUCCESS")]])
            rc, out, err = _cli(h)
        self.assertEqual(rc, 2, f"out={out} err={err}")
        self.assertIn("never reported", out)
        self.assertIn("Beta", out)
        self.assertIn("Gamma", out)

    def test_in_flight_context_times_out_as_running_not_absent(self):
        with tempfile.TemporaryDirectory() as td:
            rollup = [_run("Alpha", conclusion="SUCCESS"), _run("Beta", status="IN_PROGRESS"), _run("Gamma", conclusion="SUCCESS")]
            h = _Harness(Path(td), rollups=[rollup])
            rc, out, err = _cli(h)
        self.assertEqual(rc, 2, f"out={out} err={err}")
        self.assertIn("still running", out)
        self.assertIn("Beta", out)

    def test_transient_probe_failure_is_retried(self):
        """Bounded retry survives API flakiness without masking a real failure.

        Two of the first three live runs died on a transient ``TLS handshake
        timeout`` / ``unexpected EOF``, discarding a nearly-finished wait.
        """
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(
                Path(td),
                rollups=[[_run(c, conclusion="SUCCESS") for c in REQUIRED]],
                flaky_on="rules/branches",
                flaky_times=2,
            )
            rc, out, err = _cli(h)
        self.assertEqual(rc, 0, f"out={out} err={err}")
        self.assertIn("GREEN", out)

    def test_persistent_probe_failure_still_hard_errors(self):
        """Retry is delay-only: it must never turn a real failure into success."""
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[]], fail_on="rules/branches")
            rc, out, err = _cli(h)
        self.assertEqual(rc, 3, f"out={out} err={err}")
        self.assertIn("attempts", err)

    def test_gh_failure_is_a_hard_error_not_an_empty_result(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[]], fail_on="statusCheckRollup")
            rc, out, err = _cli(h)
        self.assertEqual(rc, 3, f"out={out} err={err}")
        self.assertIn("error:", err)
        self.assertNotIn("GREEN", out)

    def test_missing_required_rule_is_a_hard_error(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[]], rules=_rules_payload(include_rule=False))
            rc, out, err = _cli(h)
        self.assertEqual(rc, 3, f"out={out} err={err}")
        self.assertIn("no required_status_checks rule", err)
        self.assertIn("--anchor observed", err)

    def test_anchor_observed_is_the_explicit_opt_in(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[_run("Alpha", conclusion="SUCCESS")]], rules=_rules_payload(include_rule=False))
            rc, out, err = _cli(h, ["--anchor", "observed"])
        self.assertEqual(rc, 0, f"out={out} err={err}")

    def test_merged_pr_short_circuits(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[]], pr_state="MERGED")
            rc, out, err = _cli(h)
        self.assertEqual(rc, 0, f"out={out} err={err}")
        self.assertIn("MERGED", out)

    def test_json_output_shape(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[_run(c, conclusion="SUCCESS") for c in REQUIRED]])
            rc, out, err = _cli(h, ["--json"])
        self.assertEqual(rc, 0, f"out={out} err={err}")
        payload = json.loads(out)
        for key in ("status", "contexts", "done", "running", "absent", "failed", "merge_state", "polls"):
            self.assertIn(key, payload)
        self.assertEqual(payload["status"], "green")
        self.assertEqual(payload["contexts"], REQUIRED)

    def test_merge_state_is_reported_but_does_not_gate(self):
        """BEHIND is a branch-freshness fact, not a check-completion fact."""
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(
                Path(td),
                rollups=[[_run(c, conclusion="SUCCESS") for c in REQUIRED]],
                merge_state="BEHIND",
            )
            rc, out, err = _cli(h, ["--json"])
        self.assertEqual(rc, 0, f"out={out} err={err}")
        self.assertEqual(json.loads(out)["merge_state"], "BEHIND")

    def test_is_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[_run(c, conclusion="SUCCESS") for c in REQUIRED]])
            rc, out, err = _cli(h)
            calls = h.calls()
        self.assertEqual(rc, 0, f"out={out} err={err}")
        self.assertTrue(calls)
        for call in calls:
            for verb in (" merge", "update-branch", "pr create", " comment", " edit", " -X PUT", " -X POST", " -X PATCH", " -X DELETE"):
                self.assertNotIn(verb, call, f"mutating call issued: {call}")

    def test_legacy_status_contexts_are_honoured(self):
        """Real rollups mix check runs with legacy commit-status contexts.

        A row that carries ``context``/``state`` instead of ``name``/``conclusion``
        must still satisfy its required context -- otherwise the wait hangs
        forever on a context that has in fact reported.
        """
        with tempfile.TemporaryDirectory() as td:
            rollup = [_run("Alpha", conclusion="SUCCESS"), _ctx("Beta", "SUCCESS"), _ctx("Gamma", "SUCCESS")]
            h = _Harness(Path(td), rollups=[rollup])
            rc, out, err = _cli(h)
        self.assertEqual(rc, 0, f"out={out} err={err}")
        self.assertIn("3/3", out)

    def test_legacy_pending_context_is_not_terminal(self):
        with tempfile.TemporaryDirectory() as td:
            rollup = [_run("Alpha", conclusion="SUCCESS"), _ctx("Beta", "PENDING"), _ctx("Gamma", "SUCCESS")]
            h = _Harness(Path(td), rollups=[rollup])
            rc, out, err = _cli(h)
        self.assertEqual(rc, 2, f"out={out} err={err}")
        self.assertIn("still running", out)

    def test_fail_fast_returns_on_the_first_failure(self):
        """Without --fail-fast the loop waits for the full picture; with it, it returns.

        Found by dogfooding: on its own PR this tool burned 27 polls in a state
        where nothing was in flight and the remaining required contexts were gated
        behind jobs that had already failed.
        """
        with tempfile.TemporaryDirectory() as td:
            rollup = [_run("Alpha", conclusion="FAILURE")]  # Beta/Gamma absent
            h = _Harness(Path(td), rollups=[rollup])
            rc, out, err = _cli(h, ["--fail-fast"])
        self.assertEqual(rc, 1, f"out={out} err={err}")
        self.assertIn("Alpha", out)

    def test_stalled_is_reported_when_nothing_is_in_flight(self):
        """running=0 + failed>0 + absent>0 means further polling cannot help."""
        with tempfile.TemporaryDirectory() as td:
            rollup = [_run("Alpha", conclusion="FAILURE")]
            h = _Harness(Path(td), rollups=[rollup])
            rc, out, err = _cli(h, ["--json"])
        self.assertEqual(rc, 2, f"out={out} err={err}")
        self.assertTrue(json.loads(out)["stalled"])

    def test_not_stalled_while_something_is_still_running(self):
        with tempfile.TemporaryDirectory() as td:
            rollup = [_run("Alpha", conclusion="FAILURE"), _run("Beta", status="IN_PROGRESS")]
            h = _Harness(Path(td), rollups=[rollup])
            rc, out, err = _cli(h, ["--json"])
        self.assertEqual(rc, 2, f"out={out} err={err}")
        self.assertFalse(json.loads(out)["stalled"])

    def test_stalled_text_appears_in_human_output(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[_run("Alpha", conclusion="FAILURE")]])
            rc, out, _err = _cli(h)
        self.assertEqual(rc, 2)
        self.assertIn("STALLED", out)

    def test_all_green_is_never_stalled(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[_run(c, conclusion="SUCCESS") for c in REQUIRED]])
            rc, out, err = _cli(h, ["--json"])
        self.assertEqual(rc, 0, f"out={out} err={err}")
        self.assertFalse(json.loads(out)["stalled"])

    def test_bad_interval_is_usage_error(self):
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), rollups=[[]])
            rc, _out, err = _cli(h, ["--interval", "0"])
        self.assertEqual(rc, 3)
        self.assertIn("--interval", err)


if __name__ == "__main__":
    unittest.main()
