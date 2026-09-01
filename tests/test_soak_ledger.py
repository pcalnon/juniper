#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License

Tests for ``util/soak_ledger.py`` v0.2 (shared-session-memory plan §6).

``util/`` is outside every pre-commit Python hook's scope, so this suite IS the
gate -- and it is wired into ``ci.yml``'s Regression Tests, because a gate that
never runs is the defect plan §8 already records.

WHY THIS SUITE WAS REWRITTEN. The v0.1 suite contained three vacuous passes --
tests that asserted the harmless case and never touched the harmful one:

* the union-merge test wrote the *identical* line three times, so it pinned
  "byte-identical duplicate collapses" and never the real hazard, two DISTINCT
  rows colliding on one key and one being silently deleted;
* the scope test hand-wrote ``in_scope=False`` into a dict and never called
  ``at_or_after_marker``, so the fail-open behaviour it existed to prevent was
  asserted but never executed;
* ``test_excluded_from_architectural_rate_but_reported`` asserted that a ledger
  with a 50% miss rate correctly reads BET-HOLDS.

Each of those now has a test that fails if the defect returns. The rule applied
throughout: **a test must be able to fail for the reason it exists.**
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "util" / "soak_ledger.py"

_spec = importlib.util.spec_from_file_location("soak_ledger", MODULE_PATH)
assert _spec and _spec.loader
sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sl)

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "PATH": "/usr/bin:/bin",
}


def obs(**kw) -> dict:
    d = {
        "obs_id": str(uuid.uuid4()),
        "kind": "observation",
        "ts": "2026-08-21T00:00:00Z",
        "in_scope": True,
        "arm": "seeded",
        "severity": "operational",
        "area": "publish",
        "probe_id": "P01",
        "session": "s1",
        "outcome": "follow",
    }
    d.update(kw)
    return d


def seeded_run(n_follow: int, n_miss: int, probes: int = 15, severity_hazard: bool = True) -> list[dict]:
    rows, i = [], 0
    for k in range(n_follow):
        rows.append(obs(session=f"s{i}", probe_id=f"P{i % probes:02d}", outcome="follow", severity="hazard" if (severity_hazard and k % 3 == 0) else "operational"))
        i += 1
    for k in range(n_miss):
        rows.append(obs(session=f"s{i}", probe_id=f"P{i % probes:02d}", outcome="miss", miss_class="discoverability", area=["publish", "docs-ci", "experiments", "worktrees"][k % 4]))
        i += 1
    return rows


def write(tmp: Path, rows: list[dict], name: str = "l.jsonl") -> Path:
    p = tmp / name
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(MODULE_PATH), *args], capture_output=True, text=True, cwd=str(cwd) if cwd else None)


class UnionMergeDataLoss(unittest.TestCase):
    """v0.1 keyed on (session, seq); concurrent worktrees both computed seq=1."""

    def test_distinct_rows_from_one_session_all_survive(self) -> None:
        # THE test v0.1 lacked. Two real observations, same session, recorded
        # concurrently. Under the old key one was deleted and which one survived
        # depended on merge order -- opposite conclusions from the same data.
        with TemporaryDirectory() as t:
            a = obs(session="SHARED", outcome="follow", fact="publish-gate")
            b = obs(session="SHARED", outcome="miss", miss_class="discoverability", fact="ecosystem-repos")
            p = write(Path(t), [a, b])
            rows, _ = sl.load_rows(p)
            self.assertEqual(len(rows), 2)

    def test_merge_order_does_not_change_the_result(self) -> None:
        with TemporaryDirectory() as t:
            a = obs(session="SHARED", outcome="follow")
            b = obs(session="SHARED", outcome="miss", miss_class="discoverability")
            fwd = sl.analyse(sl.load_rows(write(Path(t), [a, b], "f.jsonl"))[0])
            rev = sl.analyse(sl.load_rows(write(Path(t), [b, a], "r.jsonl"))[0])
            self.assertEqual(fwd["seeded"]["follows"], rev["seeded"]["follows"])
            self.assertEqual(fwd["seeded"]["misses"], rev["seeded"]["misses"])

    def test_true_duplicate_still_collapses(self) -> None:
        with TemporaryDirectory() as t:
            r = obs()
            p = write(Path(t), [r, r, r])
            self.assertEqual(len(sl.load_rows(p)[0]), 1)

    def test_row_without_obs_id_is_rejected_not_counted(self) -> None:
        with TemporaryDirectory() as t:
            p = Path(t) / "l.jsonl"
            bad = {k: v for k, v in obs().items() if k != "obs_id"}
            p.write_text(json.dumps(bad) + "\n", encoding="utf-8")
            rows, nbad = sl.load_rows(p)
            self.assertEqual(rows, [])
            self.assertEqual(nbad, 1)


class ScopeFailsClosed(unittest.TestCase):
    """v0.1 returned in_scope=True when the marker was undecidable."""

    def _repo(self, tmp: Path) -> Path:
        subprocess.run(["git", "init", "-q", "-b", "main", str(tmp)], check=True, capture_output=True, env={**_GIT_ENV, "HOME": str(tmp)})
        (tmp / "f.txt").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True, capture_output=True, env={**_GIT_ENV, "HOME": str(tmp)})
        subprocess.run(["git", "-C", str(tmp), "commit", "-qm", "c"], check=True, capture_output=True, env={**_GIT_ENV, "HOME": str(tmp)})
        return tmp

    def test_marker_absent_is_undecidable_not_true(self) -> None:
        # Executes the real predicate -- v0.1's test never called it.
        with TemporaryDirectory() as t:
            self.assertIsNone(sl.at_or_after_marker(self._repo(Path(t))))

    def test_record_refuses_when_scope_undecidable(self) -> None:
        with TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            r = cli("--repo-root", str(repo), "--ledger", str(repo / "l.jsonl"), "record", "--outcome", "follow", "--fact", "f", "--pointer", "p", "--task", "t", "--session", "S", "--dry-run")
            self.assertEqual(r.returncode, 2)
            self.assertIn("fails CLOSED", r.stderr)

    def test_force_scope_overrides_but_marks_out_of_scope(self) -> None:
        with TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            r = cli("--repo-root", str(repo), "--ledger", str(repo / "l.jsonl"), "record", "--outcome", "follow", "--fact", "f", "--pointer", "p", "--task", "t", "--session", "S", "--force-scope", "--dry-run")
            self.assertEqual(r.returncode, 0)
            self.assertIs(json.loads(r.stdout)["in_scope"], False)

    def test_in_scope_must_be_explicitly_true(self) -> None:
        # v0.1 used `is not False`, so None / missing / 0 / "no" all counted.
        for bad in (None, 0, "false", "no"):
            self.assertEqual(sl.analyse([obs(in_scope=bad)])["seeded"]["runs"], 0, bad)
        self.assertEqual(sl.analyse([obs()])["seeded"]["runs"], 1)

    def test_row_missing_in_scope_key_does_not_count(self) -> None:
        r = obs()
        del r["in_scope"]
        self.assertEqual(sl.analyse([r])["seeded"]["runs"], 0)


class PointerDefectCannotBuyAPass(unittest.TestCase):
    """v0.1: 20 follows + 20 pointer-defect misses printed BET-HOLDS."""

    def _ledger(self) -> list[dict]:
        rows = [obs(session=f"s{i}", probe_id=f"P{i % 15:02d}", outcome="follow") for i in range(20)]
        rows += [obs(session=f"p{i}", probe_id=f"P{i % 15:02d}", outcome="miss", miss_class="pointer-defect") for i in range(20)]
        return rows

    def test_half_the_runs_defective_does_not_read_as_success(self) -> None:
        st = sl.analyse(self._ledger())
        self.assertNotIn("HOLDS", st["verdict"])

    def test_it_raises_a_pointer_defect_escalation(self) -> None:
        kinds = [e["kind"] for e in sl.analyse(self._ledger())["escalations"]]
        self.assertIn("pointer-defect", kinds)

    def test_defects_never_trigger_area_escalation(self) -> None:
        rows = seeded_run(30, 0) + [obs(session=f"p{i}", outcome="miss", miss_class="pointer-defect", area="publish") for i in range(8)]
        areas = [e for e in sl.analyse(rows)["escalations"] if e["kind"] == "area-systematic"]
        self.assertEqual(areas, [])


class DenominatorIntegrity(unittest.TestCase):
    def test_sessions_counted_only_from_rate_bearing_rows(self) -> None:
        # v0.1: 19 pointer-defect sessions + 1 follow reached "N=20" on denom 1.
        rows = [obs(session=f"p{i}", outcome="miss", miss_class="pointer-defect") for i in range(19)] + [obs(session="real", outcome="follow")]
        st = sl.analyse(rows)
        self.assertEqual(st["sessions"], 1)
        self.assertNotIn("HOLDS", st["verdict"])

    def test_unclassified_rows_do_not_inflate_the_denominator(self) -> None:
        rows = seeded_run(10, 0) + [obs(session="x", outcome="MISS")]  # wrong case
        st = sl.analyse(rows)
        self.assertEqual(st["seeded"]["denom"], 10)
        self.assertEqual(st["seeded"]["unclassified"], 1)

    def test_arm_sums_are_consistent(self) -> None:
        st = sl.analyse(seeded_run(30, 5))["seeded"]
        self.assertEqual(st["follows"] + st["misses"] + st["pointer_defects"] + st["unclassified"], st["runs"])

    def test_organic_rows_never_enter_the_seeded_denominator(self) -> None:
        rows = seeded_run(20, 0) + [obs(session=f"o{i}", arm="organic", outcome="follow") for i in range(50)]
        self.assertEqual(sl.analyse(rows)["seeded"]["denom"], 20)


class EscalationsAreNotVerdicts(unittest.TestCase):
    """v0.1's if/elif let a hazard miss mask an 11% follow rate."""

    def test_hazard_miss_does_not_mask_a_failing_rate(self) -> None:
        rows = seeded_run(14, 25, severity_hazard=True)
        rows.append(obs(session="hz", probe_id="P09", outcome="miss", miss_class="hazard", severity="hazard"))
        st = sl.analyse(rows)
        self.assertEqual(st["verdict"], "BET-FAILING")
        self.assertIn("hazard", [e["kind"] for e in st["escalations"]])

    def test_hazard_escalation_can_be_discharged(self) -> None:
        m = obs(session="hz", outcome="miss", miss_class="hazard", severity="hazard")
        rows = seeded_run(38, 0) + [m]
        self.assertIn("hazard", [e["kind"] for e in sl.analyse(rows)["escalations"]])
        rows.append({"obs_id": str(uuid.uuid4()), "kind": "resolve", "resolves": m["obs_id"], "ref": "ml#9999"})
        self.assertNotIn("hazard", [e["kind"] for e in sl.analyse(rows)["escalations"]])

    def test_soak_does_not_go_dark_after_one_old_finding(self) -> None:
        # v0.1: one hazard miss pinned ESCALATE-HAZARD forever; 500 later clean
        # sessions could not change it, so every future status exited 1.
        m = obs(session="hz", outcome="miss", miss_class="hazard", severity="hazard")
        rows = [m] + seeded_run(200, 0)
        rows.append({"obs_id": str(uuid.uuid4()), "kind": "resolve", "resolves": m["obs_id"], "ref": "ml#9999"})
        st = sl.analyse(rows)
        self.assertEqual(st["escalations"], [])
        self.assertTrue(st["verdict"].startswith("HOLDS-AT"))

    def test_resolve_requires_a_real_obs_id(self) -> None:
        with TemporaryDirectory() as t:
            p = write(Path(t), [obs()])
            r = cli("--ledger", str(p), "resolve", "--obs-id", "nope", "--ref", "ml#1")
            self.assertEqual(r.returncode, 2)


class VerdictNaming(unittest.TestCase):
    def test_bet_holds_is_never_printable(self) -> None:
        # The old name asserted something no feasible study here can carry, and
        # it is what unblocks the P5 rollout across nine repos. Per §10, promoting
        # a status's strength is the same sin as demoting it.
        for rows in (seeded_run(40, 0), seeded_run(38, 2), seeded_run(35, 5)):
            self.assertNotEqual(sl.analyse(rows)["verdict"], "BET-HOLDS")

    def test_terminal_verdict_names_the_boundary_it_proved(self) -> None:
        st = sl.analyse(seeded_run(38, 2))
        self.assertEqual(st["verdict"], f"HOLDS-AT-{sl.DECISION_BOUNDARY}")

    def test_interval_spanning_the_boundary_is_inconclusive(self) -> None:
        st = sl.analyse(seeded_run(28, 12))
        self.assertEqual(st["verdict"], "INCONCLUSIVE")

    def test_upper_bound_below_boundary_fails(self) -> None:
        st = sl.analyse(seeded_run(14, 26))
        self.assertEqual(st["verdict"], "BET-FAILING")

    def test_empty_hazard_stratum_cannot_pass(self) -> None:
        rows = seeded_run(40, 0, severity_hazard=False)
        self.assertEqual(sl.analyse(rows)["verdict"], "INCONCLUSIVE")


class WilsonInterval(unittest.TestCase):
    def test_matches_known_values(self) -> None:
        lo, hi = sl.wilson(18, 20)
        self.assertAlmostEqual(lo, 0.6990, places=3)
        self.assertAlmostEqual(hi, 0.9721, places=3)

    def test_perfect_run_is_not_certainty(self) -> None:
        lo, hi = sl.wilson(20, 20)
        self.assertLess(lo, 1.0)
        self.assertAlmostEqual(hi, 1.0, places=6)

    def test_never_leaves_the_unit_interval(self) -> None:
        for k, n in ((0, 5), (5, 5), (27, 30), (1, 100)):
            lo, hi = sl.wilson(k, n)
            self.assertGreaterEqual(lo, 0.0)
            self.assertLessEqual(hi, 1.0)

    def test_zero_denominator_is_none_not_a_crash(self) -> None:
        self.assertEqual(sl.wilson(0, 0), (None, None))

    def test_an_observed_090_never_clears_a_090_lower_bound(self) -> None:
        # Why RATE_BET_HOLDS=0.90 was withdrawn: at the target rate the lower
        # bound approaches 0.90 from below at every n.
        for n in (20, 50, 100, 500, 2000):
            k = round(0.9 * n)
            self.assertLess(sl.wilson(k, n)[0], 0.90, n)


class AreaRuleIsExposureInvariant(unittest.TestCase):
    """v0.1's bare count was an absorbing barrier: it fires eventually."""

    def test_background_misses_spread_over_areas_do_not_escalate(self) -> None:
        rows, i = [], 0
        areas = [f"a{j}" for j in range(10)]
        for j in range(200):
            miss = j % 7 == 0
            rows.append(obs(session=f"s{i}", probe_id=f"P{i % 15:02d}", area=areas[j % 10], outcome="miss" if miss else "follow", miss_class="discoverability" if miss else None))
            i += 1
        areas_hit = [e for e in sl.analyse(rows)["escalations"] if e["kind"] == "area-systematic"]
        self.assertEqual(areas_hit, [], "a bare count rule fires here; a rate rule must not")

    def test_a_genuinely_bad_area_does_escalate(self) -> None:
        # Needs CONTRAST: a healthy background in other areas, and the misses
        # concentrated in one. (seeded_run() puts every follow in `publish`, so
        # using it here would make the "bad area" the whole population and the
        # rule would correctly stay silent -- which is the next test.)
        rows = [obs(session=f"g{i}", probe_id=f"P{i % 15:02d}", area=f"a{i % 10}", outcome="follow") for i in range(60)]
        rows += [obs(session=f"b{i}", probe_id="P07", area="publish", outcome="miss", miss_class="discoverability") for i in range(8)]
        areas_hit = [e for e in sl.analyse(rows)["escalations"] if e["kind"] == "area-systematic"]
        self.assertEqual([e["areas"] for e in areas_hit], [["publish"]])

    def test_a_uniformly_failing_system_is_not_an_area_problem(self) -> None:
        # When everything fails at once no single area is anomalous. That is
        # BET-FAILING's job, not rung 3's -- escalating both would send the
        # operator to a path-scoped rule for a global problem.
        rows = seeded_run(60, 0) + [obs(session=f"b{i}", probe_id="P07", area="publish", outcome="miss", miss_class="discoverability") for i in range(8)]
        areas_hit = [e for e in sl.analyse(rows)["escalations"] if e["kind"] == "area-systematic"]
        self.assertEqual(areas_hit, [])

    def test_area_is_normalised(self) -> None:
        self.assertEqual(sl.norm_area("  Publish "), "publish")
        self.assertIsNone(sl.norm_area("   "))
        self.assertIsNone(sl.norm_area(None))

    def test_min_miss_floor_blocks_a_one_of_one_area(self) -> None:
        rows = seeded_run(40, 0)
        rows.append(obs(session="z", area="tiny", outcome="miss", miss_class="discoverability"))
        areas_hit = [e for e in sl.analyse(rows)["escalations"] if e["kind"] == "area-systematic"]
        self.assertEqual(areas_hit, [])


class DataIntegrityVerdicts(unittest.TestCase):
    """A destroyed instrument must not read as a healthy one."""

    def test_missing_ledger_is_no_data_exit_2(self) -> None:
        with TemporaryDirectory() as t:
            r = cli("--ledger", str(Path(t) / "absent.jsonl"), "status")
            self.assertEqual(r.returncode, 2)
            self.assertIn("NO-DATA", r.stdout)

    def test_empty_ledger_is_no_data_exit_2(self) -> None:
        with TemporaryDirectory() as t:
            p = Path(t) / "e.jsonl"
            p.write_text("", encoding="utf-8")
            r = cli("--ledger", str(p), "status")
            self.assertEqual(r.returncode, 2)

    def test_corrupt_ledger_is_degraded_exit_2(self) -> None:
        with TemporaryDirectory() as t:
            p = Path(t) / "c.jsonl"
            p.write_text("<<<<<<< HEAD\nnot json\n", encoding="utf-8")
            r = cli("--ledger", str(p), "status")
            self.assertEqual(r.returncode, 2)
            self.assertIn("DEGRADED", r.stdout)

    def test_organic_only_cannot_produce_a_verdict(self) -> None:
        rows = [obs(session=f"o{i}", arm="organic", outcome="follow") for i in range(60)]
        st = sl.analyse(rows)
        self.assertEqual(st["verdict"], "NO-SEEDED-DATA")

    def test_organic_rate_is_reported_as_an_upper_bound(self) -> None:
        with TemporaryDirectory() as t:
            rows = [obs(session=f"o{i}", arm="organic", outcome="follow") for i in range(10)]
            r = cli("--ledger", str(write(Path(t), rows)), "report")
            self.assertIn("UPPER BOUND", r.stdout)
            self.assertIn("biased UP", r.stdout)


class SensitivityMath(unittest.TestCase):
    def test_quarter_logging_maps_090_back_to_about_070(self) -> None:
        # The headline number from the reviews: if misses are logged at ~26% of
        # follows, a true BET-FAILING 0.70 prints as exactly 0.900. Inverting at
        # q=0.25 lands just under, at 0.6923.
        self.assertAlmostEqual(dict(sl.sensitivity(0.9))[0.25], 0.6923, places=3)

    def test_the_forward_direction_agrees(self) -> None:
        # Cross-check the inverse against the forward map, so an algebra slip in
        # one direction cannot pass unnoticed.
        for p_true, q in ((0.70, 0.25), (0.60, 0.50), (0.80, 0.10)):
            observed = p_true / (p_true + (1 - p_true) * q)
            self.assertAlmostEqual(dict(sl.sensitivity(observed))[q], p_true, places=9)

    def test_perfect_logging_is_the_identity(self) -> None:
        self.assertAlmostEqual(dict(sl.sensitivity(0.8))[1.0], 0.8, places=9)


class RecordValidation(unittest.TestCase):
    def test_probe_run_rejects_unknown_probe(self) -> None:
        r = cli("probe-run", "--probe-id", "NOPE", "--outcome", "follow", "--session", "S", "--dry-run", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 2)

    def test_probe_run_takes_severity_from_the_frozen_registry(self) -> None:
        # Severity must not be settable at the CLI, or the hazard stratum can be
        # defined after the observation.
        #
        # --force-scope is load-bearing here, not incidental: CI checks out at
        # depth 1, so the START_MARKER object is absent, the scope predicate is
        # undecidable, and the tool fails CLOSED. That is correct behaviour; this
        # test is about severity provenance, so it opts out of the scope gate
        # rather than depending on the repo's git history.
        r = cli("probe-run", "--probe-id", "P02-assert-release-tag-ref", "--outcome", "follow", "--session", "S", "--force-scope", "--dry-run", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["severity"], "hazard")

    def test_probe_run_has_no_severity_flag(self) -> None:
        r = cli("probe-run", "--probe-id", "P02-assert-release-tag-ref", "--outcome", "follow", "--session", "S", "--severity", "reference", "--dry-run", cwd=REPO_ROOT)
        self.assertNotEqual(r.returncode, 0)

    def test_miss_requires_class(self) -> None:
        r = cli("record", "--outcome", "miss", "--fact", "f", "--pointer", "p", "--task", "t", "--area", "publish", "--session", "S", "--dry-run", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 2)

    def test_organic_miss_requires_area(self) -> None:
        r = cli("record", "--outcome", "miss", "--class", "discoverability", "--fact", "f", "--pointer", "p", "--task", "t", "--session", "S", "--dry-run", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--area", r.stderr)

    def test_empty_fields_are_rejected(self) -> None:
        r = cli("record", "--outcome", "follow", "--fact", "", "--pointer", "p", "--task", "t", "--session", "S", "--dry-run", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 2)

    def test_unknown_session_is_rejected(self) -> None:
        r = cli("record", "--outcome", "follow", "--fact", "f", "--pointer", "p", "--task", "t", "--session", "unknown", "--dry-run", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 2)

    def test_area_systematic_is_not_recordable(self) -> None:
        self.assertNotIn("area-systematic", sl.MISS_CLASSES)

    def test_dry_run_writes_nothing(self) -> None:
        # --force-scope keeps this honest. Without it, under CI's depth-1
        # checkout the command is REFUSED at exit 2 and writes nothing for the
        # wrong reason -- the assertion would hold while never exercising the
        # dry-run path at all. Asserting exit 0 pins that it really got there.
        with TemporaryDirectory() as t:
            p = Path(t) / "l.jsonl"
            r = cli("--ledger", str(p), "probe-run", "--probe-id", "P02-assert-release-tag-ref", "--outcome", "follow", "--session", "S", "--force-scope", "--dry-run", cwd=REPO_ROOT)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(p.exists())

    def test_shallow_checkout_refuses_rather_than_guessing(self) -> None:
        # The CI-visible consequence of failing closed, pinned deliberately: in a
        # checkout without the marker object (depth-1, as CI does) a real record
        # is refused, not silently marked in-scope. v0.1 marked it in-scope.
        r = cli("probe-run", "--probe-id", "P02-assert-release-tag-ref", "--outcome", "follow", "--session", "S", "--dry-run", cwd=REPO_ROOT)
        self.assertIn(r.returncode, (0, 2))
        if r.returncode == 2:
            self.assertIn("fails CLOSED", r.stderr)
        else:
            self.assertIs(json.loads(r.stdout)["in_scope"], True)


class ProbeRegistry(unittest.TestCase):
    def test_shipped_registry_verifies(self) -> None:
        r = cli("verify-probes", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_an_under_populated_registry_cannot_reach_a_verdict(self) -> None:
        # The real invariant. The shipped registry currently holds 6 valid probes
        # against a floor of 15 -- the 2026-08-21 pilot retired 9 as invalid
        # (their facts had never left AGENTS.md). That shortfall must SHOW as
        # IN-PROGRESS rather than quietly permitting a terminal verdict off a
        # thin registry, and it must not be a permanently red build either.
        reg = sl.load_probes(REPO_ROOT / sl.DEFAULT_PROBES)
        n = len(reg["probes"])
        rows = [obs(session=f"s{i}", probe_id=f"P{i % max(1, n):02d}") for i in range(60)]
        st = sl.analyse(rows)
        if n < sl.MIN_DISTINCT_PROBES:
            self.assertEqual(st["verdict"], "IN-PROGRESS")
            self.assertIn("distinct probes", st["note"])

    def test_every_shipped_probe_is_structurally_complete(self) -> None:
        reg = sl.load_probes(REPO_ROOT / sl.DEFAULT_PROBES)
        for p in reg["probes"]:
            for field in ("probe_id", "severity", "area", "fact", "pointer", "task", "discriminator", "must_be_absent_from_source"):
                self.assertTrue(p.get(field), f"{p.get('probe_id')}: {field}")

    def test_retired_probes_record_why(self) -> None:
        # Retiring a probe silently would erase the pilot's most useful finding.
        reg = sl.load_probes(REPO_ROOT / sl.DEFAULT_PROBES)
        for p in reg.get("retired", []):
            self.assertTrue(p.get("reason"), p.get("probe_id"))
            self.assertIn("INVALID", p["reason"])

    def test_registry_has_hazard_probes(self) -> None:
        reg = sl.load_probes(REPO_ROOT / sl.DEFAULT_PROBES)
        self.assertTrue([p for p in reg["probes"] if p["severity"] == "hazard"])

    def test_a_dangling_anchor_is_caught(self) -> None:
        # The verifier must be able to fail, or it is a vacuous pass itself.
        with TemporaryDirectory() as t:
            root = Path(t)
            (root / "docs").mkdir()
            (root / "docs" / "REFERENCE.md").write_text("## Real Section\n", encoding="utf-8")
            (root / "conf").mkdir()
            (root / "conf" / "soak_probes.json").write_text(json.dumps({"probes": [{"probe_id": "X", "severity": "hazard", "area": "a", "fact": "f", "pointer": "docs/REFERENCE.md#no-such-anchor", "task": "t", "discriminator": "d"}]}), encoding="utf-8")
            r = cli("--repo-root", str(root), "verify-probes")
            self.assertEqual(r.returncode, 1)
            self.assertIn("anchor", r.stdout)

    def test_a_bad_severity_is_caught(self) -> None:
        with TemporaryDirectory() as t:
            root = Path(t)
            (root / "docs").mkdir()
            (root / "docs" / "REFERENCE.md").write_text("## Real Section\n", encoding="utf-8")
            (root / "conf").mkdir()
            (root / "conf" / "soak_probes.json").write_text(json.dumps({"probes": [{"probe_id": "X", "severity": "critical", "area": "a", "fact": "f", "pointer": "docs/REFERENCE.md#real-section", "task": "t", "discriminator": "d"}]}), encoding="utf-8")
            r = cli("--repo-root", str(root), "verify-probes")
            self.assertEqual(r.returncode, 1)


class RepoRootResolution(unittest.TestCase):
    def test_a_subdirectory_does_not_fork_a_phantom_ledger(self) -> None:
        # v0.1 trusted cwd, so a `cd` into a subdir created a new ledger that was
        # never merged, never read, never committed -- and reported success.
        sub = REPO_ROOT / "util"
        self.assertEqual(sl.repo_root(sub), REPO_ROOT)


class Constants(unittest.TestCase):
    def test_boundary_is_the_reachable_one(self) -> None:
        self.assertEqual(sl.DECISION_BOUNDARY, 0.75)

    def test_precision_target_not_a_session_count(self) -> None:
        self.assertEqual(sl.TARGET_PROBE_RUNS, 35)
        self.assertEqual(sl.MIN_DISTINCT_PROBES, 15)

    def test_start_marker_is_the_post_p3_commit(self) -> None:
        self.assertEqual(sl.START_MARKER, "500508b")

    def test_never_re_inline_is_stated_on_failure(self) -> None:
        with TemporaryDirectory() as t:
            p = write(Path(t), seeded_run(14, 26))
            self.assertIn("NEVER re-inline", cli("--ledger", str(p), "status").stdout)


class StatusGuidanceSafety(unittest.TestCase):
    """`status` must not talk an operator into an irreversible discharge.

    Two output defects, both fixed 2026-08-24. The escalation block printed ABOVE
    the verdict-driven action, so `status` led with "rung 2" and read as though
    rung 2 were the next step -- when rung 2 is neither taken nor closed. And the
    rung-2 line suggested a bare ``soak_ledger.py resolve``, with nothing saying
    that it appends to an APPEND-ONLY ledger and cannot be undone.

    That combination points at the one command that makes a non-zero exit go away,
    while the non-zero exit is exactly the design. Output only -- exit codes and
    the ledger are untouched.
    """

    @staticmethod
    def _with_open_hazard(t: str):
        rows = seeded_run(24, 11)
        rows.append(
            obs(
                session="s-haz",
                probe_id="P07",
                outcome="miss",
                severity="hazard",
                miss_class="discoverability",
                area="publish",
            )
        )
        return write(Path(t), rows)

    def _status(self, t: str) -> str:
        return cli("--ledger", str(self._with_open_hazard(t)), "status").stdout

    def test_verdict_action_precedes_the_escalation_block(self) -> None:
        with TemporaryDirectory() as t:
            out = self._status(t)
            self.assertIn("rung 1", out)
            self.assertIn("rung 2", out)
            self.assertLess(out.index("rung 1"), out.index("rung 2"), msg=f"rung 2 must not lead:\n{out}")

    def test_escalations_are_marked_open_and_verdict_independent(self) -> None:
        with TemporaryDirectory() as t:
            out = self._status(t)
            self.assertIn("OPEN and INDEPENDENT of the verdict", out)

    def test_discharge_is_labelled_irreversible(self) -> None:
        with TemporaryDirectory() as t:
            out = self._status(t)
            self.assertIn("IRREVERSIBLE", out)
            self.assertIn("no un-resolve", out)

    def test_discharge_is_not_offered_as_a_way_to_go_green(self) -> None:
        """The whole point: exiting 1 is the design, not a thing to clear."""
        with TemporaryDirectory() as t:
            out = self._status(t)
            self.assertIn("Do NOT run it to make `status` exit 0", out)

    def test_open_hazard_obs_ids_are_named(self) -> None:
        """An operator cannot discharge correctly without the id; printing it is
        also what makes the count auditable against the ledger."""
        with TemporaryDirectory() as t:
            out = self._status(t)
            self.assertIn("open:", out)

    def test_status_still_exits_one_with_an_open_escalation(self) -> None:
        with TemporaryDirectory() as t:
            r = cli("--ledger", str(self._with_open_hazard(t)), "status")
            self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)


class ResidencyGate(unittest.TestCase):
    """A probe whose fact never left the source tests nothing.

    The 2026-08-21 pilot ran 15 probes; NINE were invalid because their facts
    were still resident in AGENTS.md, and one of those tested a fact in the
    resident ``## Hazards`` list that the protocol explicitly excludes. Checking
    that a pointer RESOLVES says nothing about whether the fact LEFT.
    """

    def _registry(self, root: Path, probe_extra: dict) -> None:
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs" / "REFERENCE.md").write_text("## Real Section\n", encoding="utf-8")
        (root / "conf").mkdir(exist_ok=True)
        probe = {
            "probe_id": "X",
            "severity": "hazard",
            "area": "a",
            "fact": "f",
            "pointer": "docs/REFERENCE.md#real-section",
            "task": "t",
            "discriminator": "d",
        }
        probe.update(probe_extra)
        (root / "conf" / "soak_probes.json").write_text(json.dumps({"source_file": "AGENTS.md", "probes": [probe]}), encoding="utf-8")

    def test_missing_declaration_is_refused(self) -> None:
        with TemporaryDirectory() as t:
            root = Path(t)
            (root / "AGENTS.md").write_text("nothing relevant\n", encoding="utf-8")
            self._registry(root, {})
            r = cli("--repo-root", str(root), "verify-probes")
            self.assertEqual(r.returncode, 1)
            self.assertIn("must_be_absent_from_source", r.stdout)

    def test_resident_phrase_invalidates_the_probe(self) -> None:
        with TemporaryDirectory() as t:
            root = Path(t)
            (root / "AGENTS.md").write_text("the KILL_WORKERS hazard\n", encoding="utf-8")
            self._registry(root, {"must_be_absent_from_source": ["KILL_WORKERS"]})
            r = cli("--repo-root", str(root), "verify-probes")
            self.assertEqual(r.returncode, 1)
            self.assertIn("still resident", r.stdout)

    def test_genuinely_relocated_phrase_passes(self) -> None:
        with TemporaryDirectory() as t:
            root = Path(t)
            (root / "AGENTS.md").write_text("nothing relevant\n", encoding="utf-8")
            self._registry(root, {"must_be_absent_from_source": ["KILL_WORKERS"]})
            r = cli("--repo-root", str(root), "verify-probes")
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_shipped_registry_declares_residency_for_every_probe(self) -> None:
        reg = sl.load_probes(REPO_ROOT / sl.DEFAULT_PROBES)
        for p in reg["probes"]:
            self.assertTrue(p.get("must_be_absent_from_source"), p["probe_id"])


class Invalidation(unittest.TestCase):
    """A run against a defective probe must leave the denominator by an
    auditable append, never by deleting the line."""

    def test_invalidated_row_leaves_the_denominator(self) -> None:
        r = obs(session="s1", outcome="miss", miss_class="discoverability")
        rows = [r] + seeded_run(4, 0)
        self.assertEqual(sl.analyse(rows)["seeded"]["misses"], 1)
        rows.append({"obs_id": str(uuid.uuid4()), "kind": "invalidate", "invalidates": r["obs_id"], "reason": "probe was defective"})
        after = sl.analyse(rows)["seeded"]
        self.assertEqual(after["misses"], 0)
        self.assertEqual(after["runs"], 4)

    def test_the_original_row_is_not_deleted(self) -> None:
        with TemporaryDirectory() as t:
            r = obs()
            p = write(Path(t), [r, {"obs_id": str(uuid.uuid4()), "kind": "invalidate", "invalidates": r["obs_id"], "reason": "why"}])
            # Still on disk: the ledger records what was RUN, not only what counted.
            self.assertEqual(len(sl.load_rows(p)[0]), 2)
            self.assertEqual(sl.analyse(sl.load_rows(p)[0])["seeded"]["runs"], 0)

    def test_requires_a_real_obs_id(self) -> None:
        with TemporaryDirectory() as t:
            p = write(Path(t), [obs()])
            r = cli("--ledger", str(p), "invalidate", "--obs-id", "nope", "--reason", "x")
            self.assertEqual(r.returncode, 2)

    def test_requires_a_reason(self) -> None:
        with TemporaryDirectory() as t:
            rec = obs()
            p = write(Path(t), [rec])
            r = cli("--ledger", str(p), "invalidate", "--obs-id", rec["obs_id"], "--reason", " ")
            self.assertEqual(r.returncode, 2)

    def test_invalidate_does_not_discharge_an_escalation(self) -> None:
        # invalidate says "this was never data"; resolve says "this was real and
        # is fixed". Conflating them would let a live hazard be tidied away.
        m = obs(session="hz", outcome="miss", miss_class="hazard", severity="hazard")
        rows = seeded_run(38, 0) + [m]
        rows.append({"obs_id": str(uuid.uuid4()), "kind": "resolve", "resolves": m["obs_id"], "ref": "ml#1"})
        self.assertEqual(sl.analyse(rows)["seeded"]["runs"], 39)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class RescoreSourceRecovered(unittest.TestCase):
    """Re-scoring must reclassify a run WITHOUT flattering the follow rate.

    Owner decision 2026-08-31: a run where the agent produced the correct answer
    from source rather than through the relocated pointer is not the same event
    as failing to obtain the fact. The dangerous implementation is the one that
    also drops the run from the denominator: 9 of the real ledger's 11
    architectural misses are source-recovered, so dropping them moves the rate
    from 24/35 (68.6%, spanning the 0.75 boundary) to 24/26 (92.3%, clearing it)
    and converts INCONCLUSIVE into a pass by redefinition. These tests pin the
    denominator against exactly that.
    """

    def _rows(self, n_follow: int, n_miss: int, n_rescored: int) -> list[dict]:
        rows = [obs(session="f%d" % i, outcome="follow") for i in range(n_follow)]
        misses = [obs(session="m%d" % i, outcome="miss", miss_class="discoverability") for i in range(n_miss)]
        rows += misses
        for r in misses[:n_rescored]:
            rows.append(
                {
                    "obs_id": "rs-" + r["obs_id"],
                    "kind": "rescore",
                    "rescores": r["obs_id"],
                    "from_outcome": "miss",
                    "to_outcome": "source-recovered",
                    "reason": "correct answer, reached from source",
                }
            )
        return rows

    def test_rescored_run_stays_in_the_denominator(self) -> None:
        st = sl.analyse(self._rows(24, 11, 9))["seeded"]
        self.assertEqual(st["denom"], 35, "re-scoring must not shrink the denominator")

    def test_rescoring_does_not_change_the_follow_rate(self) -> None:
        before = sl.analyse(self._rows(24, 11, 0))["seeded"]["rate"]
        after = sl.analyse(self._rows(24, 11, 9))["seeded"]["rate"]
        self.assertAlmostEqual(before, after)

    def test_rescored_runs_leave_the_miss_column(self) -> None:
        st = sl.analyse(self._rows(24, 11, 9))["seeded"]
        self.assertEqual(st["misses"], 2)
        self.assertEqual(st["source_recovered"], 9)

    def test_retention_is_reported_and_differs_from_the_rate(self) -> None:
        st = sl.analyse(self._rows(24, 11, 9))["seeded"]
        self.assertAlmostEqual(st["retention"], 33 / 35)
        self.assertLess(st["rate"], st["retention"])

    def test_arm_sums_stay_consistent_with_a_source_recovered_bucket(self) -> None:
        st = sl.analyse(self._rows(24, 11, 9))["seeded"]
        total = st["follows"] + st["misses"] + st["source_recovered"] + st["pointer_defects"] + st["unclassified"]
        self.assertEqual(total, st["runs"])

    def test_a_rescored_hazard_miss_stops_escalating(self) -> None:
        haz = obs(session="h", outcome="miss", miss_class="hazard", severity="hazard")
        rows = seeded_run(20, 0) + [haz]
        kinds = [e["kind"] for e in sl.analyse(rows)["escalations"]]
        self.assertIn("hazard", kinds)
        rows.append(
            {
                "obs_id": "rs-h",
                "kind": "rescore",
                "rescores": haz["obs_id"],
                "from_outcome": "miss",
                "to_outcome": "source-recovered",
                "reason": "correct, cited the gate while answering",
            }
        )
        kinds_after = [e["kind"] for e in sl.analyse(rows)["escalations"]]
        self.assertNotIn("hazard", kinds_after)

    def test_rescore_rows_are_not_themselves_counted_as_runs(self) -> None:
        st = sl.analyse(self._rows(10, 4, 4))["seeded"]
        self.assertEqual(st["runs"], 14)

    def test_an_all_rescored_ledger_does_not_read_as_a_pass(self) -> None:
        # The degenerate case the denominator rule exists to prevent. If every
        # miss were re-scored AND re-scoring removed rows, this would be 0/0 or a
        # perfect score. It must stay a real rate over every run.
        st = sl.analyse(self._rows(0, 10, 10))["seeded"]
        self.assertEqual(st["denom"], 10)
        self.assertEqual(st["rate"], 0.0)
        self.assertAlmostEqual(st["retention"], 1.0)

    def test_rescoring_does_not_shrink_the_session_count(self) -> None:
        # Regression: source-recovered rows are rate-bearing (they sit in the
        # denominator), so their sessions must still count. The first cut of this
        # change built `sessions` from follows+misses only, and N silently fell
        # from 35 to 26 the moment the backlog was re-scored -- a reclassification
        # that quietly shrank the reported size of the study.
        before = sl.analyse(self._rows(24, 11, 0))["sessions"]
        after = sl.analyse(self._rows(24, 11, 9))["sessions"]
        self.assertEqual(before, after)
