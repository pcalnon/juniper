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
* ``DatasetInstanceIsFixedTest`` -- generators declaring ``seed=None`` must be pinned;
  a declared seed (spiral) must be left alone; the CLI ``--dataset-seed`` flag (not the
  snapshot-sampling ``--seed``) is what ``load_datasets`` receives.
* ``RegenerateSidecarChainGuardTest`` -- the ad-hoc chain driver refuses to start without
  a complete backup and must not redirect ``JUNIPER_CASCOR_SNAPSHOTS_DIR``.
"""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

import snapshot_attribute as sa  # noqa: E402 - path bootstrap must precede the import

MODULE_PATH = REPO_ROOT / "util" / "snapshot_attribute.py"
CHAIN_SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-24_regenerate_sidecar_chain.bash"
CHAIN_TIMEOUT_SECONDS = 15
SIDECAR_BASENAMES = (
    "snapshots_index.jsonl",
    "snapshots_classification.jsonl",
    "snapshots_attribution.jsonl",
    "snapshots_backfill.jsonl",
)


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


def attributed_row(name: str, dataset: str, **scores) -> dict:
    """A first-pass row, the shape ``build_cross_dataset_floor`` consumes."""
    return {"name": name, "verdict": sa.ATTRIBUTED, "dataset": dataset, "scores": dict(scores)}


class _ParamsDeclaringNoSeed:
    """Stands in for the five generators whose params declare ``seed=None``."""

    __slots__ = ("seed",)

    def __init__(self, seed=None):
        self.seed = seed


class _ParamsDeclaringItsOwnSeed:
    """Stands in for ``spiral``, whose params declare a real default seed."""

    OWN = 4242

    def __init__(self, seed=None):
        self.seed = self.OWN if seed is None else seed


class DatasetInstanceIsFixedTest(unittest.TestCase):
    """THE reproducibility class: attribution must score against the SAME data every run.

    Five of the six 2-D generators declare ``seed: int | None = Field(default=None)``, so
    ``params_cls()`` draws different data on every call. Measured on the real tree: two calls
    to ``load_datasets`` in ONE process returned different arrays for checkerboard, circles,
    gaussian, moon and xor — spiral alone was stable, because spiral is the only one declaring
    a default seed.

    The cost was not theoretical. A rebuild of the archive sidecar moved moon's attributed
    count from 0 to 6: moon's own score shifted 1.000 -> 0.995, which flipped one snapshot's
    first-pass winner, which removed it from moon's reference class, which dropped moon's
    cross floor 1.000 -> 0.850.

    Hermetic by construction — the stand-ins above mean this needs no juniper-data tree.
    """

    def test_a_generator_declaring_no_seed_is_given_one(self) -> None:
        params = sa.seeded_params(_ParamsDeclaringNoSeed, 20260824)
        self.assertEqual(params.seed, 20260824, "a generator that declares no seed must be pinned, or it redraws every run")

    def test_a_generator_declaring_its_own_seed_keeps_it(self) -> None:
        """spiral's canonical instance must not be silently redefined.

        Every spiral conclusion on record was derived against spiral's own default instance;
        overriding it here would invalidate them for no reproducibility gain, because spiral
        was already reproducible.
        """
        params = sa.seeded_params(_ParamsDeclaringItsOwnSeed, 20260824)
        self.assertEqual(params.seed, _ParamsDeclaringItsOwnSeed.OWN, "a declared seed is the generator's canonical instance and must win")

    def test_the_same_seed_produces_the_same_params_twice(self) -> None:
        first = sa.seeded_params(_ParamsDeclaringNoSeed, 7)
        second = sa.seeded_params(_ParamsDeclaringNoSeed, 7)
        self.assertEqual(first.seed, second.seed, "two calls must agree, or the dataset differs between the two passes of one run")

    def test_a_params_class_with_no_seed_field_is_left_alone(self) -> None:
        """Absence and None are different answers and must not be collapsed.

        Every 2-D generator declares ``seed`` today, but the helper is generic. A params class
        with no such field would REJECT ``seed=...``, so treating "absent" as "unseeded" turns a
        generator this tool merely cannot pin into one it cannot load at all.
        """

        class _NoSeedField:
            def __init__(self):
                self.noise = 0.1

        params = sa.seeded_params(_NoSeedField, 20260824)
        self.assertFalse(hasattr(params, "seed"), "a class without a seed field must come back untouched")
        self.assertEqual(params.noise, 0.1)

    def test_the_module_pins_a_constant_rather_than_leaving_it_to_a_default(self) -> None:
        """A drifting default would silently redefine the canonical instance.

        20260824 is the published instance every seeded sidecar was scored against.
        Changing it is allowed, but it is a new canonical instance, not a silent tweak.
        """
        self.assertEqual(sa.DATASET_SEED, 20260824, "changing DATASET_SEED redefines the canonical instance and invalidates existing sidecars")

    def test_a_different_seed_is_a_different_instance(self) -> None:
        """The pin is only load-bearing if the seed actually reaches the params."""
        self.assertNotEqual(
            sa.seeded_params(_ParamsDeclaringNoSeed, 1).seed,
            sa.seeded_params(_ParamsDeclaringNoSeed, 2).seed,
            "distinct seeds must produce distinct params, or the pin is a no-op",
        )

    def test_dataset_seed_cli_defaults_to_the_pinned_constant(self) -> None:
        """Without the flag, the pin is unreachable from the operator surface."""
        found = None
        for node in ast.walk(ast.parse(MODULE_PATH.read_text())):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"):
                continue
            flags = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if "--dataset-seed" not in flags:
                continue
            found = node
            break
        assert found is not None, "--dataset-seed must exist; without it the pin cannot be overridden or inspected"
        default = next((k.value for k in found.keywords if k.arg == "default"), None)
        assert isinstance(default, ast.Name), "--dataset-seed must default to the DATASET_SEED name, not a drifting literal"
        self.assertEqual(default.id, "DATASET_SEED")

    def test_load_datasets_is_wired_to_dataset_seed_not_the_sampling_seed(self) -> None:
        """--seed samples snapshots; --dataset-seed pins the generator instance.

        Confusing them is the remaining footgun. ``--seed`` defaults to 20260823 and
        ``--dataset-seed`` to 20260824. Wiring ``load_datasets(..., seed=args.seed)``
        would silently redefine the canonical instance and invalidate every comparison
        with an existing sidecar, while still looking reproducible run-to-run.
        """
        calls = [node for node in ast.walk(ast.parse(MODULE_PATH.read_text())) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "load_datasets"]
        self.assertEqual(len(calls), 1, f"expected exactly one load_datasets call, found {len(calls)}")
        seed_kw = next((k for k in calls[0].keywords if k.arg == "seed"), None)
        self.assertIsNotNone(seed_kw, "load_datasets must be passed seed= explicitly so the sampling seed cannot sneak in positionally")
        assert seed_kw is not None
        assert isinstance(seed_kw.value, ast.Attribute), "load_datasets seed= must be an attribute access like args.dataset_seed"
        self.assertEqual(seed_kw.value.attr, "dataset_seed", f"load_datasets seed= must be args.dataset_seed, not args.{seed_kw.value.attr}")
        assert isinstance(seed_kw.value.value, ast.Name)
        self.assertEqual(seed_kw.value.value.id, "args")
        """A drifting default would silently redefine the canonical instance."""
        self.assertIsInstance(sa.DATASET_SEED, int)
        self.assertIsNotNone(sa.DATASET_SEED)


class DisplacementFlagTest(unittest.TestCase):
    """The winner is chosen by LIFT, not by raw score, and the two can disagree.

    §3.2 of the null-model findings: a snapshot attributed to spiral at 0.624 while scoring
    gaussian 0.890 and moon 0.835. It won because spiral's floor (0.572) was the lowest one
    available -- floor arithmetic, not evidence, and the reasoning that made spiral's whole
    cohort withdrawable. `lift` alone does not reveal it, so the verdict now says so.

    Lift stays the criterion (raw score cannot separate "learned this" from "this one is easy"),
    so NO verdict changes here -- this is a diagnostic over the same decision.
    """

    def test_the_spiral_case_from_the_findings_is_flagged(self) -> None:
        """The six SCORES are verbatim from §3.2; the floors are set so spiral clears cleanly.

        §3.2 quotes the score vector but not all six floors for that snapshot, and the real row
        did attribute. Floors here are therefore chosen to reproduce that outcome -- spiral the
        only positive lift -- rather than invented to force the flag. Getting this wrong once was
        instructive: with floors set equal to the top scores, the row came back AMBIGUOUS and the
        assertion failed, which is the correct behaviour for a vector nothing separates.
        """
        null = null_from(gaussian=0.890, moon=0.870, spiral=0.500, checkerboard=0.600, xor=0.600, circles=0.600)
        scores = {"gaussian": 0.890, "moon": 0.835, "spiral": 0.624, "checkerboard": 0.560, "xor": 0.550, "circles": 0.510}
        verdict = sa.adjudicate(scores, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)

        self.assertEqual(verdict["verdict"], sa.ATTRIBUTED, f"the verdict itself must be unchanged: {verdict}")
        self.assertEqual(verdict["dataset"], "spiral", "lift still decides the winner")
        self.assertTrue(verdict["displaced"], "spiral scores below gaussian and moon; that must be visible")
        self.assertEqual(verdict["raw_best"], "gaussian")
        self.assertEqual(verdict["raw_best_score"], 0.890)
        self.assertIn("DISPLACED", verdict["reason"])

    def test_an_undisplaced_attribution_is_not_flagged(self) -> None:
        """NON-VACUITY. If the flag were always true it would carry no information.

        The xor cluster wins on raw score AND on lift, so it must come back displaced=False.
        """
        null = null_from(xor=0.690, spiral=0.572, circles=0.730)
        verdict = sa.adjudicate({"xor": 0.995, "spiral": 0.521, "circles": 0.530}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)

        self.assertEqual(verdict["verdict"], sa.ATTRIBUTED)
        self.assertFalse(verdict["displaced"], "xor is both the highest scorer and the highest lifter")
        self.assertNotIn("raw_best", verdict, "an undisplaced row must not carry a raw_best")
        self.assertNotIn("DISPLACED", verdict["reason"])

    def test_displacement_does_not_change_which_dataset_wins(self) -> None:
        """The flag is a report, not a veto: same winner with and without the disagreement."""
        null = null_from(gaussian=0.890, spiral=0.572)
        undisplaced = sa.adjudicate({"spiral": 0.900, "gaussian": 0.700}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        displaced = sa.adjudicate({"spiral": 0.900, "gaussian": 0.950}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)

        self.assertEqual(undisplaced["dataset"], "spiral")
        self.assertEqual(displaced["dataset"], "spiral", "a displaced winner is still the winner")
        self.assertFalse(undisplaced["displaced"])
        self.assertTrue(displaced["displaced"])

    def test_non_attributed_verdicts_carry_no_displacement_field(self) -> None:
        """Displacement is only meaningful once something has actually been attributed."""
        null = null_from(checkerboard=0.610, spiral=0.572)
        verdict = sa.adjudicate({"checkerboard": 0.624, "spiral": 0.510}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)

        self.assertEqual(verdict["verdict"], sa.INDETERMINATE)
        self.assertNotIn("displaced", verdict, "an unattributed row has no winner to displace")

    def test_schema_version_is_not_bumped_by_an_additive_field(self) -> None:
        """SCHEMA_VERSION encodes what a verdict MEANS; displacement changes no verdict.

        Bumping would declare every existing v2 row incomparable and force regeneration of a
        28k-row sidecar to gain nothing. Pinned so a later author does not bump it reflexively.
        """
        self.assertEqual(sa.SCHEMA_VERSION, 2)


class CrossDatasetFloorTest(unittest.TestCase):
    """THE second regression class: the untrained null answers the WRONG QUESTION.

    It asks "did this network learn anything?". Attribution needs "did it learn THIS rather
    than something else?". The two diverge whenever a network trained on A also scores well on
    B, which is common because these six generators are not orthogonal.

    Every test here pins the contrast directly: the SAME score vector is adjudicated with
    ``cross_floor=None`` (the single-floor behaviour that shipped first) and again with the
    second floor. If the second floor were removed, the two arms would agree and these tests
    would fail.
    """

    def test_a_candidate_that_only_clears_the_untrained_floor_is_refused(self) -> None:
        """The measured spiral case, reduced. Every number here is from the real cohort.

        A snapshot scoring 0.644 on spiral clears spiral's untrained floor of 0.572 by +0.072
        and attributes. But networks trained on OTHER datasets reach 0.598 on spiral, so the
        real bar is 0.598 and the lift is only +0.046 -- inside the margin. This is one of the
        16 of 20 spiral attributions that the second floor withdrew.

        The neighbouring case is deliberately NOT this one: a snapshot at 0.660 lifts +0.062
        over the same cross floor and survives. The rule discriminates; it does not simply
        delete spiral.
        """
        null = null_from(spiral=0.572, xor=0.720)
        scores = {"spiral": 0.644, "xor": 0.510}

        without = sa.adjudicate(scores, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP)
        self.assertEqual(without["verdict"], sa.ATTRIBUTED, "precondition: the single-floor rule attributes this")
        self.assertEqual(without["dataset"], "spiral")

        with_cross = sa.adjudicate(scores, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP, cross_floor={"spiral": 0.598})
        self.assertEqual(with_cross["verdict"], sa.INDETERMINATE, f"0.644 must not clear a 0.598 cross floor by the margin: {with_cross}")
        self.assertIsNone(with_cross["dataset"])

        survivor = sa.adjudicate({"spiral": 0.660, "xor": 0.510}, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP, cross_floor={"spiral": 0.598})
        self.assertEqual(survivor["verdict"], sa.ATTRIBUTED, "+0.062 clears the same floor; the rule must discriminate, not blanket-refuse")

    def test_the_effective_floor_is_the_higher_of_the_two(self) -> None:
        """Clearing BOTH floors is the same as clearing the stricter one -- in both directions."""
        null = null_from(xor=0.720)
        # Cross floor BELOW the untrained floor must not weaken anything.
        lenient = sa.adjudicate({"xor": 0.800}, null, 0.05, 0.05, cross_floor={"xor": 0.400})
        self.assertEqual(lenient["verdict"], sa.ATTRIBUTED, "a lower cross floor must not override the untrained floor")
        self.assertEqual(lenient["floors"]["untrained"], 0.720)
        # Cross floor ABOVE it must bind.
        strict = sa.adjudicate({"xor": 0.800}, null, 0.05, 0.05, cross_floor={"xor": 0.790})
        self.assertEqual(strict["verdict"], sa.INDETERMINATE, "a higher cross floor must bind")

    def test_a_dataset_with_no_reference_class_falls_back_to_the_untrained_floor(self) -> None:
        """Absence of a second floor must not be read as a floor of zero, or of one."""
        null = null_from(xor=0.720)
        verdict = sa.adjudicate({"xor": 0.800}, null, 0.05, 0.05, cross_floor={"moon": 0.99})
        self.assertEqual(verdict["verdict"], sa.ATTRIBUTED, "xor has no cross floor; the untrained floor still governs")
        self.assertNotIn("cross_dataset", verdict["floors"], "no cross floor applied means none is recorded")

    def test_the_reason_names_the_floor_that_actually_bound(self) -> None:
        """A refusal that blames the wrong floor sends the next investigation to the wrong place."""
        null = null_from(spiral=0.572)
        verdict = sa.adjudicate({"spiral": 0.630}, null, 0.05, 0.05, cross_floor={"spiral": 0.598})
        self.assertEqual(verdict["verdict"], sa.INDETERMINATE)
        self.assertIn("cross-dataset floor", verdict["reason"], f"the cross floor bound here, not the untrained one: {verdict['reason']}")

    def test_both_floors_are_recorded_so_a_verdict_can_be_re_derived(self) -> None:
        verdict = sa.adjudicate({"xor": 0.990}, null_from(xor=0.720), 0.05, 0.05, cross_floor={"xor": 0.775})
        self.assertEqual(verdict["verdict"], sa.ATTRIBUTED)
        self.assertEqual(verdict["floors"], {"untrained": 0.720, "cross_dataset": 0.775})


class CrossDatasetReferenceClassTest(unittest.TestCase):
    """What may enter the reference class, and what may not."""

    def test_a_snapshot_does_not_contribute_to_its_own_datasets_floor(self) -> None:
        """Otherwise every attribution raises the bar it was just judged against."""
        rows = [attributed_row("a.h5", "xor", xor=0.99, spiral=0.55)]
        cross = sa.build_cross_dataset_floor(rows)
        self.assertNotIn("xor", cross, "an xor-attributed snapshot must not set xor's floor")
        self.assertEqual(cross["spiral"]["max"], 0.55, "it may set the floor for datasets it was NOT attributed to")

    def test_only_attributed_rows_enter_the_reference_class(self) -> None:
        """An indeterminate snapshot is of UNKNOWN training; it is evidence about nothing."""
        rows = [
            {"name": "u.h5", "verdict": sa.INDETERMINATE, "dataset": None, "scores": {"spiral": 0.95}},
            {"name": "b.h5", "verdict": sa.AMBIGUOUS, "dataset": None, "scores": {"spiral": 0.93}},
            attributed_row("a.h5", "xor", spiral=0.55),
        ]
        cross = sa.build_cross_dataset_floor(rows)
        self.assertEqual(cross["spiral"]["max"], 0.55, "only the attributed row may set spiral's floor")
        self.assertEqual(cross["spiral"]["n"], 1)

    def test_a_snapshot_is_excluded_from_the_bar_it_is_judged_against(self) -> None:
        """A snapshot that helps set its own bar is not being tested against anything."""
        rows = [attributed_row("high.h5", "xor", moon=0.98), attributed_row("low.h5", "xor", moon=0.60)]
        cross = sa.build_cross_dataset_floor(rows)
        self.assertEqual(cross["moon"]["max"], 0.98)

        for_other = sa.cross_floor_excluding(cross, "low.h5")
        self.assertEqual(for_other["moon"], 0.98, "a snapshot that did not set the max sees the max")

        for_setter = sa.cross_floor_excluding(cross, "high.h5")
        self.assertEqual(for_setter["moon"], 0.60, "the snapshot that SET the max must be judged against the runner-up")

    def test_a_reference_class_of_one_drops_out_entirely_for_its_setter(self) -> None:
        """The measured moon case: the whole floor rested on a single snapshot.

        With no runner-up there is no cross floor left, and the dataset must fall back to the
        untrained floor rather than keep a bar of its own making.
        """
        cross = sa.build_cross_dataset_floor([attributed_row("only.h5", "circles", moon=1.000)])
        self.assertEqual(cross["moon"]["max"], 1.000)
        self.assertIsNone(cross["moon"]["runner_up"])
        self.assertNotIn("moon", sa.cross_floor_excluding(cross, "only.h5"), "a floor of one's own making must drop out")
        self.assertEqual(sa.cross_floor_excluding(cross, "other.h5")["moon"], 1.000)

    def test_an_empty_first_pass_yields_no_second_floor(self) -> None:
        self.assertEqual(sa.build_cross_dataset_floor([]), {})
        self.assertEqual(sa.cross_floor_excluding({}, "any.h5"), {})

    def test_a_snapshot_cannot_suppress_its_own_rival_by_topping_that_rivals_floor(self) -> None:
        """The measured `5af596ef` case, and the reason self-exclusion is not a nicety.

        That snapshot scores circles 0.880 but **moon 1.000**. Because its own 1.000 was the
        highest moon score in the reference class, it set moon's floor to 1.000 — which drove
        its OWN moon lift to zero, removed moon as a runner-up, and left circles looking
        cleanly separated. A snapshot scoring a perfect 1.000 on moon must not be recorded as
        confidently circles.

        With the snapshot excluded from the bar it is judged against, moon's floor falls to the
        runner-up (0.875), its own moon lift becomes +0.125, and moon returns as a live
        alternative — so the verdict is AMBIGUOUS, which is the honest answer.
        """
        rows = [
            attributed_row("contested.h5", "circles", circles=0.880, moon=1.000),
            # Puts circles' floor at its measured 0.750 and moon's runner-up at its measured
            # 0.875, so the two lifts (+0.130 and +0.125) land inside the gap rule as they do
            # in the archive.
            attributed_row("other.h5", "xor", moon=0.875, circles=0.750),
        ]
        cross = sa.build_cross_dataset_floor(rows)
        self.assertEqual(cross["moon"]["max"], 1.000)
        self.assertEqual(cross["moon"]["setter"], "contested.h5")

        null = null_from(circles=0.0, moon=0.0)
        scores = {"circles": 0.880, "moon": 1.000}

        naive = sa.adjudicate(scores, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP, cross_floor={n: e["max"] for n, e in cross.items()})
        self.assertEqual(naive["verdict"], sa.ATTRIBUTED, "precondition: without self-exclusion it looks like a clean circles")
        self.assertEqual(naive["dataset"], "circles")

        correct = sa.adjudicate(scores, null, sa.DEFAULT_MARGIN, sa.DEFAULT_GAP, cross_floor=sa.cross_floor_excluding(cross, "contested.h5"))
        self.assertEqual(correct["verdict"], sa.AMBIGUOUS, f"a perfect moon score must resurface as a rival: {correct}")
        self.assertIsNone(correct["dataset"])


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


def _run_chain(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(CHAIN_SCRIPT), *argv],
        capture_output=True,
        text=True,
        timeout=CHAIN_TIMEOUT_SECONDS,
        check=False,
    )


def _complete_backup(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    for name in SIDECAR_BASENAMES:
        (path / name).write_text("{}\n")
    return path


class RegenerateSidecarChainGuardTest(unittest.TestCase):
    """The chain overwrites four gitignored sidecars that cost ~1h to rebuild.

    The backup refuse is the load-bearing guard: without it a typo in --root still
    runs, and the script's own comment records that JUNIPER_CASCOR_SNAPSHOTS_DIR is
    both cascor's write dir AND snapshot_index.default_root(), so redirecting it
    would point every stage at a scratch dir and look like success.
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "snapshots"
        self.root.mkdir()
        for name in SIDECAR_BASENAMES:
            (self.root / name).write_text("")
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.backup = _complete_backup(Path(self.tmp.name) / "backup")

    def _argv(self, *extra: str) -> list[str]:
        return [
            "--root",
            str(self.root),
            "--repo",
            str(self.repo),
            "--python",
            "/bin/false",
            "--backup",
            str(self.backup),
            *extra,
        ]

    def test_refuses_to_start_without_a_backup(self) -> None:
        result = _run_chain("--root", str(self.root), "--repo", str(self.repo), "--python", "/bin/false", "--dry-run")
        self.assertEqual(result.returncode, 2, msg=result.stderr)
        self.assertIn("--backup", result.stderr)

    def test_refuses_an_incomplete_backup(self) -> None:
        (self.backup / "snapshots_attribution.jsonl").unlink()
        result = _run_chain(*self._argv("--dry-run"))
        self.assertEqual(result.returncode, 2, msg=result.stderr)
        self.assertIn("incomplete", result.stderr)
        self.assertIn("snapshots_attribution.jsonl", result.stderr)

    def test_dry_run_does_not_invoke_python(self) -> None:
        """/bin/false as --python would fail the script if any stage actually ran."""
        result = _run_chain(*self._argv("--dry-run"))
        self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
        self.assertIn("[dry-run] not executed", result.stdout)
        self.assertIn("CHAIN COMPLETE", result.stdout)

    def test_skip_index_omits_the_index_stage(self) -> None:
        result = _run_chain(*self._argv("--dry-run", "--skip-index"))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("1/4 index", result.stdout)
        self.assertIn("2/4 classify", result.stdout)

    def test_does_not_redirect_the_snapshots_dir(self) -> None:
        """Assigning JUNIPER_CASCOR_SNAPSHOTS_DIR would retarget every stage at scratch.

        The probe scripts in this directory redirect it so they cannot grow the archive;
        this chain must not, or index/classify/attribute/backfill would look for the
        archive in the scratch dir and report success against nothing.
        """
        source = CHAIN_SCRIPT.read_text()
        self.assertNotIn(
            "JUNIPER_CASCOR_SNAPSHOTS_DIR=",
            source,
            "the chain must pass --root explicitly; assigning JUNIPER_CASCOR_SNAPSHOTS_DIR retargets snapshot_index.default_root()",
        )


class WholeDatasetSurvivesDecision11Test(unittest.TestCase):
    """``_whole_dataset`` must build "every row" from whichever artifact shape it is handed.

    ``load_datasets`` read ``produced["X_full"]`` directly, and that subscript sat OUTSIDE
    the ``try/except`` that turns a broken generator into a recorded gap. Decision 11
    (juniper-data#369) removes the key, so every generator would have raised ``KeyError``
    and taken the module down instead of being excluded with a warning -- attribution would
    stop, loudly, on the first generator.
    """

    @staticmethod
    def _numpy():
        import numpy as np

        return np

    def _artifact(self, np, *, with_full: bool, with_val: bool = True):
        produced = {
            "X_train": np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32),
            "y_train": np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
            "X_test": np.array([[3.0, 3.0]], dtype=np.float32),
            "y_test": np.array([[1.0, 0.0]], dtype=np.float32),
        }
        if with_val:
            produced["X_val"] = np.array([[2.0, 2.0]], dtype=np.float32)
            produced["y_val"] = np.array([[0.0, 1.0]], dtype=np.float32)
        if with_full:
            order = ["train", "val", "test"] if with_val else ["train", "test"]
            produced["X_full"] = np.vstack([produced[f"X_{p}"] for p in order])
            produced["y_full"] = np.vstack([produced[f"y_{p}"] for p in order])
        return produced

    def test_a_post_369_artifact_yields_the_whole_dataset(self) -> None:
        np = self._numpy()
        X, y = sa._whole_dataset(self._artifact(np, with_full=False), np)
        self.assertEqual(X.shape, (4, 2))
        self.assertEqual(y.shape, (4, 2))

    def test_the_derived_rows_are_in_train_val_test_order(self) -> None:
        """Order is load-bearing: ``labels`` is taken from ``y`` positionally."""
        np = self._numpy()
        X, _ = sa._whole_dataset(self._artifact(np, with_full=False), np)
        self.assertEqual([row[0] for row in X.tolist()], [0.0, 1.0, 2.0, 3.0])

    def test_a_legacy_artifact_keeps_the_producers_own_arrays(self) -> None:
        """A stored pre-369 snapshot must attribute byte-identically to what it scored before."""
        np = self._numpy()
        produced = self._artifact(np, with_full=True)
        produced["X_full"][0, 0] = 99.0  # a sentinel the concatenation could not produce
        X, _ = sa._whole_dataset(produced, np)
        self.assertEqual(X[0, 0], 99.0)

    def test_derived_and_producer_arrays_agree_when_both_are_available(self) -> None:
        """The concatenation reproduces what juniper-data used to ship, row for row."""
        np = self._numpy()
        legacy = self._artifact(np, with_full=True)
        current = {k: v for k, v in legacy.items() if not k.endswith("_full")}
        self.assertTrue(np.array_equal(sa._whole_dataset(legacy, np)[0], sa._whole_dataset(current, np)[0]))
        self.assertTrue(np.array_equal(sa._whole_dataset(legacy, np)[1], sa._whole_dataset(current, np)[1]))

    def test_a_legacy_two_way_artifact_derives_without_val(self) -> None:
        np = self._numpy()
        X, _ = sa._whole_dataset(self._artifact(np, with_full=False, with_val=False), np)
        self.assertEqual(X.shape, (3, 2))

    def test_an_artifact_with_no_partitions_raises_rather_than_returning_empty(self) -> None:
        """An empty result would read as "this generator produced nothing", which is a lie."""
        np = self._numpy()
        with self.assertRaises(KeyError):
            sa._whole_dataset({"something_else": np.zeros((2, 2))}, np)

    def test_the_read_is_inside_the_recorded_gap_handler(self) -> None:
        """A generator whose output cannot be read must be EXCLUDED, not fatal.

        Pinned structurally: the call must sit inside the ``try`` whose handler prints the
        "unavailable ... excluded" warning and continues. It previously sat one line below
        the handler, so any failure to read the arrays escaped as an uncaught exception.
        """
        tree = ast.parse(MODULE_PATH.read_text())
        loader = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "load_datasets")
        guarded = [node for node in ast.walk(loader) if isinstance(node, ast.Try) for stmt in node.body for sub in ast.walk(stmt) if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == "_whole_dataset"]
        self.assertTrue(guarded, "_whole_dataset must be called inside load_datasets' try/except, or a bad artifact is fatal instead of a recorded gap")


if __name__ == "__main__":
    unittest.main()
