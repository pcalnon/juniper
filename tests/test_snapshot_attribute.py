#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   snapshots
# File Name:     test_snapshot_attribute.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Regression suite for util/snapshot_attribute.py -- the read-only dataset-attribution pass
#   that infers which dataset a snapshot was trained on (handoff 2026-08-22 §3.2).
#####################################################################################################################################################################################################
"""Pin the attribution contracts.

Every class below pins a wrong answer this arc actually produced and measured, not a
hypothetical. Attribution is a *claim about provenance*: a false positive here becomes a
label on a research artifact, so the tests are weighted toward proving the tool REFUSES.

* ``PermutationCorrectionTest``  -- raw accuracy reports a network that learned a dataset with
  swapped one-hot columns as far BELOW chance. Archive snapshots scored 0.010 on gaussian;
  those are 0.990 inverted.
* ``FloorIsTheNullMaximumTest``  -- the 327-checkerboard regression. With a p95 floor, 327
  ZERO-hidden-unit networks (linear models) were attributed to a non-linearly-separable
  problem at +0.059 median lift, from scores sitting inside the null's uncharacterised tail.
* ``UnattributableDatasetTest``  -- ``gaussian``'s floor is 1.000 because untrained networks
  score perfectly on it. No score may ever clear that.
* ``RefusesWithoutEvidenceTest`` -- ambiguity and missing nulls must produce a refusal, not a
  guess. A missing null once raised ``ValueError: max() iterable argument is empty``.
* ``PartialSidecarGuardTest``    -- a sidecar silently covering a subset is worse than none.
* ``NoDestructivePathTest``      -- retention is §6.4 and is INFORMED by this tool, never
  performed by it.
"""

from __future__ import annotations

import ast
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

import snapshot_attribute as sa  # noqa: E402 - path bootstrap must precede the import

MODULE_PATH = REPO_ROOT / "util" / "snapshot_attribute.py"


def null_from(**floors) -> dict:
    """A null where each dataset's floor (its observed max) is given directly."""
    return {name: {"p50": value - 0.1, "p95": value - 0.02, "max": value, "n": 120} for name, value in floors.items()}


class PermutationCorrectionTest(unittest.TestCase):
    """Class-index order is a convention of the training run, not a property of the data."""

    def test_perfect_agreement_scores_one(self) -> None:
        self.assertAlmostEqual(sa.permutation_corrected_accuracy([0, 1, 0, 1], [0, 1, 0, 1], 2), 1.0)

    def test_perfectly_inverted_labels_also_score_one(self) -> None:
        """The measured case: 0.010 raw on gaussian is 0.990 under the correct relabelling.

        Raw accuracy calls this 'did not learn it' -- the exact opposite of the truth, and it
        mis-ranked the snapshots with the STRONGEST signal.
        """
        self.assertAlmostEqual(sa.permutation_corrected_accuracy([1, 0, 1, 0], [0, 1, 0, 1], 2), 1.0)

    def test_chance_stays_chance(self) -> None:
        """The correction must not manufacture signal out of a coin flip."""
        self.assertAlmostEqual(sa.permutation_corrected_accuracy([0, 1, 0, 1], [0, 0, 1, 1], 2), 0.5)

    def test_three_classes_use_the_best_permutation(self) -> None:
        self.assertAlmostEqual(sa.permutation_corrected_accuracy([1, 2, 0], [0, 1, 2], 3), 1.0)


class PercentileTest(unittest.TestCase):
    def test_bounds(self) -> None:
        values = [0.0, 0.25, 0.5, 0.75, 1.0]
        self.assertAlmostEqual(sa.percentile(values, 0), 0.0)
        self.assertAlmostEqual(sa.percentile(values, 100), 1.0)
        self.assertAlmostEqual(sa.percentile(values, 50), 0.5)

    def test_empty_is_nan_not_a_crash(self) -> None:
        self.assertNotEqual(sa.percentile([], 95), sa.percentile([], 95))  # NaN != NaN


class FloorIsTheNullMaximumTest(unittest.TestCase):
    """THE regression class. The floor is the null's observed maximum, not its p95.

    With a p95 floor the first full pass attributed **327 snapshots to checkerboard** at a
    median lift of +0.059 and a median hidden-unit count of ZERO. A zero-hidden-unit network is
    a linear model and cannot learn checkerboard; those scores sat between p95 (0.565) and the
    observed untrained max (0.610) -- inside the tail a 120-sample null cannot characterise.
    """

    def test_a_score_inside_the_null_tail_is_refused(self) -> None:
        """0.624 beat checkerboard's p95 of 0.565 and its max of 0.610. It must NOT attribute."""
        null = {"checkerboard": {"p50": 0.52, "p95": 0.565, "max": 0.610, "n": 120}, "spiral": {"p50": 0.52, "p95": 0.557, "max": 0.572, "n": 120}}
        verdict = sa.adjudicate({"checkerboard": 0.624, "spiral": 0.510}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(verdict["verdict"], sa.INDETERMINATE, f"a score inside the null's tail must not attribute: {verdict}")

    def test_a_score_clearly_above_the_null_max_attributes(self) -> None:
        """The xor cluster: 0.995 against a floor of 0.690 survives the stricter rule."""
        null = null_from(xor=0.690, spiral=0.572, circles=0.730)
        verdict = sa.adjudicate({"xor": 0.995, "spiral": 0.521, "circles": 0.530}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(verdict["verdict"], sa.ATTRIBUTED)
        self.assertEqual(verdict["dataset"], "xor")

    def test_the_floor_is_max_not_p95(self) -> None:
        """Directly pins which statistic is used: a score between p95 and max must refuse."""
        null = {"xor": {"p50": 0.55, "p95": 0.60, "max": 0.90, "n": 120}}
        verdict = sa.adjudicate({"xor": 0.70}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(verdict["verdict"], sa.INDETERMINATE, "0.70 clears p95=0.60 but not max=0.90; the max must govern")

    def test_margin_is_required_on_top_of_the_floor(self) -> None:
        null = null_from(xor=0.690)
        self.assertEqual(sa.adjudicate({"xor": 0.700}, null, 0.05, 0.05)["verdict"], sa.INDETERMINATE, "+0.010 over the floor is inside noise")
        self.assertEqual(sa.adjudicate({"xor": 0.800}, null, 0.05, 0.05)["verdict"], sa.ATTRIBUTED)


class UnattributableDatasetTest(unittest.TestCase):
    """``gaussian`` is scored but can never be an ANSWER.

    Untrained networks score up to 1.000 on it (linearly separable, and permutation-correction
    amplifies that), so its floor is 1.000 and nothing can clear it. Reporting the score while
    refusing the attribution is the honest shape.
    """

    def test_a_perfect_gaussian_score_still_does_not_attribute(self) -> None:
        null = null_from(gaussian=1.0, spiral=0.572)
        verdict = sa.adjudicate({"gaussian": 1.0, "spiral": 0.52}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertNotEqual(verdict["dataset"], "gaussian", "a dataset an untrained network aces cannot be evidence of training")

    def test_gaussian_does_not_mask_a_real_winner(self) -> None:
        """The 17de4973 case: huge gaussian score, real signal underneath must still surface."""
        null = null_from(gaussian=1.0, circles=0.730)
        verdict = sa.adjudicate({"gaussian": 0.99, "circles": 0.95}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(verdict["verdict"], sa.ATTRIBUTED)
        self.assertEqual(verdict["dataset"], "circles")


class RefusesWithoutEvidenceTest(unittest.TestCase):
    def test_a_close_runner_up_is_ambiguous_not_a_guess(self) -> None:
        """Behaving like several of these datasets at once is not evidence for one of them."""
        null = null_from(xor=0.60, circles=0.60)
        verdict = sa.adjudicate({"xor": 0.90, "circles": 0.89}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(verdict["verdict"], sa.AMBIGUOUS)
        self.assertIsNone(verdict["dataset"])

    def test_no_scores_at_all_is_indeterminate(self) -> None:
        """The archive's (2,1) / (2,3) / (4,2) / (784,10) networks have no compatible dataset."""
        verdict = sa.adjudicate({}, null_from(xor=0.60), sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(verdict["verdict"], sa.INDETERMINATE)
        self.assertIn("shape-compatible", verdict["reason"])

    def test_a_missing_null_cannot_be_attributed_to(self) -> None:
        """This raised ``ValueError: max() iterable argument is empty`` before the fix.

        A shape with no scorable untrained sample has no floor; treating that as 1.0 keeps it
        out of the running rather than letting an unfloored dataset win by default.
        """
        null = {"xor": {"p50": None, "p95": None, "max": None, "n": 0}}
        verdict = sa.adjudicate({"xor": 0.99}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(verdict["verdict"], sa.INDETERMINATE)

    def test_the_reason_is_always_populated(self) -> None:
        """A refusal that does not say why sends the next investigation back to zero."""
        null = null_from(xor=0.60)
        for scores in ({}, {"xor": 0.61}, {"xor": 0.99}):
            self.assertTrue(sa.adjudicate(scores, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)["reason"])


class ScoreNetworkShapeTest(unittest.TestCase):
    """A dataset whose width does not match the network is SKIPPED, never coerced."""

    class _FakeTensor:
        def __init__(self, rows):
            self._rows = rows

        def argmax(self, dim=1):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self._rows

    class _FakeNetwork:
        def __init__(self, input_size, output_size, predictions):
            self.input_size = input_size
            self.output_size = output_size
            self._predictions = predictions

        def forward(self, _x):
            return ScoreNetworkShapeTest._FakeTensor(self._predictions)

    class _FakeTorch:
        float32 = "float32"

        @staticmethod
        def tensor(value, dtype=None):
            return value

    def _datasets(self):
        return {
            "two_out": {"X": [[0.0, 0.0]], "labels": [0], "input_size": 2, "output_size": 2, "n": 1},
            "three_out": {"X": [[0.0, 0.0]], "labels": [0], "input_size": 2, "output_size": 3, "n": 1},
            "four_in": {"X": [[0.0, 0.0, 0.0, 0.0]], "labels": [0], "input_size": 4, "output_size": 2, "n": 1},
        }

    def test_only_shape_compatible_datasets_are_scored(self) -> None:
        network = self._FakeNetwork(2, 2, [0])
        scored = sa.score_network(network, self._datasets(), self._FakeTorch)
        self.assertEqual(set(scored), {"two_out"}, "a 2x2 network must not be scored against 3-class or 4-input data")

    def test_a_network_matching_nothing_scores_nothing(self) -> None:
        network = self._FakeNetwork(10, 7, [0])
        self.assertEqual(sa.score_network(network, self._datasets(), self._FakeTorch), {})


class SidecarTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_round_trips(self) -> None:
        rows = [{"path": "/a.h5", "name": "a.h5", "verdict": sa.ATTRIBUTED, "dataset": "xor", "lift": 0.3, "gap": 0.2}]
        sa.write_sidecar(self.root, rows)
        self.assertEqual(sa.read_jsonl(self.root / sa.SIDECAR_NAME), rows)

    def test_replaces_rather_than_appends(self) -> None:
        sa.write_sidecar(self.root, [{"path": "/a.h5", "verdict": sa.INDETERMINATE}])
        sa.write_sidecar(self.root, [{"path": "/a.h5", "verdict": sa.ATTRIBUTED, "dataset": "xor"}])
        rows = sa.read_jsonl(self.root / sa.SIDECAR_NAME)
        self.assertEqual(len(rows), 1, "an attribution is a derived verdict a later run revises, not an append log")
        self.assertEqual(rows[0]["verdict"], sa.ATTRIBUTED)

    def test_truncated_line_costs_one_record(self) -> None:
        (self.root / sa.SIDECAR_NAME).write_text(json.dumps({"path": "/a.h5"}) + "\n{ truncated")
        self.assertEqual(len(sa.read_jsonl(self.root / sa.SIDECAR_NAME)), 1)

    def test_no_temp_survives(self) -> None:
        sa.write_sidecar(self.root, [{"path": "/a.h5"}])
        self.assertEqual([p.name for p in self.root.iterdir()], [sa.SIDECAR_NAME])


class PartialSidecarGuardTest(unittest.TestCase):
    """A sidecar covering a silent subset is worse than none: the next reader counts its rows
    and believes them to be the archive."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _run(self, *argv) -> "tuple[int, str]":
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sa.main(["--root", str(self.root), *argv])
        return code, out.getvalue() + err.getvalue()

    def test_write_with_sample_is_refused(self) -> None:
        code, text = self._run("--write", "--sample", "10")
        self.assertEqual(code, 2)
        self.assertIn("sampled", text)

    def test_write_with_min_hidden_is_refused(self) -> None:
        code, text = self._run("--write", "--min-hidden", "20")
        self.assertEqual(code, 2)
        self.assertIn("min-hidden", text)

    def test_write_from_sidecar_is_refused(self) -> None:
        code, text = self._run("--write", "--from-sidecar")
        self.assertEqual(code, 2)
        self.assertIn("itself", text)

    def test_the_guard_fires_before_any_expensive_work(self) -> None:
        """The refusal must not arrive after a 20-minute pass the operator already paid for.

        There is no snapshot root content here and no cascor tree configured, so reaching the
        scoring stage at all would fail differently -- exit 2 with the partial-write message is
        proof the guard ran first.
        """
        code, text = self._run("--write", "--sample", "5")
        self.assertEqual(code, 2)
        self.assertIn("sampled", text)
        self.assertNotIn("cascor", text.lower())

    def test_missing_root_exits_2(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sa.main(["--root", str(self.root / "absent"), "--stats"])
        self.assertEqual(code, 2)

    def test_from_sidecar_without_one_names_the_fix(self) -> None:
        code, text = self._run("--from-sidecar", "--stats")
        self.assertEqual(code, 2)
        self.assertIn("--write", text)


class ReportingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        sa.write_sidecar(
            self.root,
            [
                {"path": "/a.h5", "name": "a.h5", "verdict": sa.ATTRIBUTED, "dataset": "xor", "lift": 0.3, "gap": 0.2, "hidden_units": 40},
                {"path": "/b.h5", "name": "b.h5", "verdict": sa.INDETERMINATE, "dataset": None, "lift": 0.0, "gap": 0.0, "hidden_units": 0},
                {"path": "/c.h5", "name": "c.h5", "verdict": sa.AMBIGUOUS, "dataset": None, "lift": 0.1, "gap": 0.01, "hidden_units": 5},
            ],
        )

    def _run(self, *argv) -> "tuple[int, str]":
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sa.main(["--root", str(self.root), "--from-sidecar", *argv])
        return code, out.getvalue() + err.getvalue()

    def test_stats_counts_every_verdict(self) -> None:
        code, text = self._run("--stats")
        self.assertEqual(code, 0)
        summary = json.loads(text)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_verdict"][sa.ATTRIBUTED], 1)
        self.assertEqual(summary["attributed_to"], {"xor": 1})

    def test_verdict_filter_selects(self) -> None:
        code, text = self._run("--verdict", sa.ATTRIBUTED, "--json")
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(text)), 1)

    def test_summary_reports_the_share_not_just_the_count(self) -> None:
        """0.47% attributed is the headline; a bare count invites reading it as a lot."""
        _, text = self._run("--stats")
        self.assertAlmostEqual(json.loads(text)["attributed_share"], 1 / 3, places=3)


class NoDestructivePathTest(unittest.TestCase):
    """Retention is design §6.4. This tool produces the evidence for it and never acts on it."""

    def test_module_has_no_delete_surface(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text())
        called: "set[str]" = set()
        cli_flags: "set[str]" = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute):
                owner = node.func.value.id if isinstance(node.func.value, ast.Name) else ""
                called.add(f"{owner}.{node.func.attr}" if owner else node.func.attr)
                if node.func.attr == "add_argument":
                    cli_flags.update(a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str))
        for forbidden in ("os.remove", "shutil.rmtree", "rmdir"):
            self.assertNotIn(forbidden, called, f"snapshot_attribute.py must stay read-only; it calls {forbidden}")
        for flag in ("--prune", "--delete", "--yes"):
            self.assertNotIn(flag, cli_flags, f"snapshot_attribute.py must expose no destructive flag; found {flag}")

    def test_snapshots_are_never_opened_writable(self) -> None:
        source = MODULE_PATH.read_text()
        self.assertNotIn("h5py", source, "attribution goes through cascor's loader; it must not open .h5 files itself")


if __name__ == "__main__":
    unittest.main()
