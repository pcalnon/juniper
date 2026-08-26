#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   snapshots
# File Name:     test_snapshot_backfill.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Regression suite for util/snapshot_backfill.py -- the consolidated recovered-metadata
#   record (handoff §3.4), whose entire purpose is that no recovered value can be read
#   without its derivation label.
#####################################################################################################################################################################################################
"""Pin the caveats, because the caveats ARE the feature.

The owner's instruction (§3.4) was explicit: backfilled metadata must carry "a clear and
visible label capturing the approximate, inferred, or recreated nature of their metadata [...]
a potentially important caution against naive reasoning."

So the tests here are weighted toward proving the tool CANNOT quietly present an inference as
a fact:

* ``DerivationSeparationTest``   -- observed / measured / inferred / population never mix. An
  inferred dataset must not appear where an observed field is read.
* ``PopulationClaimTest``        -- THE load-bearing class. Item 3 trained **380 of 15,927**
  zero-node snapshots. Writing ``formerly_broken`` onto all of them as a per-snapshot fact
  would fabricate a result for 15,547 files nobody trained. The claim is quarantined in its
  own bucket and self-describes as unverified.
* ``IdentityIsNeverInventedTest`` -- run identity is UNRECOVERABLE (zero surviving run dirs
  before 2026-07-30). Absence must stay absence.
* ``RootCauseTest``              -- every failing snapshot gets a named cause in the arc's own
  four-cause vocabulary, because §3.4 puts root-causing above everything else for research value.
* ``NoDestructivePathTest``      -- writes a sidecar, never a .h5. Snapshots are read-only
  project assets.
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

import snapshot_backfill as sb  # noqa: E402 - path bootstrap must precede the import

MODULE_PATH = REPO_ROOT / "util" / "snapshot_backfill.py"


def index_row(**overrides) -> dict:
    row = {
        "path": "/archive/snap.h5",
        "name": "snap.h5",
        "created": "2026-04-01T00:00:00",
        "uuid": "aaaaaaaa-0000-0000-0000-000000000000",
        "juniper_version": "0.3.2",
        "format_version": "2",
        "size_bytes": 48893,
        "tier": "model",
        "groups": ["arch", "config", "meta", "mp", "params", "random"],
        "arch": {"input_size": 2, "output_size": 2, "num_hidden_units": 0},
        "provenance": None,
    }
    row.update(overrides)
    return row


def classification_row(**overrides) -> dict:
    row = {
        "path": "/archive/snap.h5",
        "name": "snap.h5",
        "health": "zero_node",
        "category": "undetermined",
        "iterations_lower_bound": 0,
        "load": {"status": "ok", "detail": ""},
    }
    row.update(overrides)
    return row


def attribution_row(**overrides) -> dict:
    row = {
        "path": "/archive/snap.h5",
        "name": "snap.h5",
        "verdict": "attributed",
        "dataset": "xor",
        "lift": 0.265,
        "gap": 0.29,
        "reason": "scores 0.985 vs untrained floor 0.720",
        "scores": {"xor": 0.985, "spiral": 0.52},
    }
    row.update(overrides)
    return row


class DerivationSeparationTest(unittest.TestCase):
    """The four levels differ in KIND, not degree, and must never be read as one another."""

    def test_observed_fields_come_from_the_file(self) -> None:
        record = sb.build_record(index_row(), None, None)
        self.assertEqual(record[sb.OBSERVED]["created"], "2026-04-01T00:00:00")
        self.assertEqual(record[sb.OBSERVED]["arch"]["num_hidden_units"], 0)

    def test_an_inferred_dataset_never_appears_as_observed_or_measured(self) -> None:
        """A reader pulling 'observed' must not receive a judgement."""
        record = sb.build_record(index_row(), classification_row(health="has_hidden"), attribution_row())
        self.assertIn("dataset", record[sb.INFERRED])
        self.assertNotIn("dataset", record[sb.OBSERVED])
        self.assertNotIn("dataset", record[sb.MEASURED])

    def test_raw_scores_are_measured_but_the_verdict_is_inferred(self) -> None:
        """Accuracy is reproducible fact; 'it was trained on xor' is a judgement from it."""
        record = sb.build_record(index_row(), classification_row(health="has_hidden"), attribution_row())
        self.assertIn("dataset_accuracy", record[sb.MEASURED])
        self.assertEqual(record[sb.INFERRED]["dataset"]["value"], "xor")

    def test_an_unattributed_snapshot_gets_no_inferred_dataset(self) -> None:
        record = sb.build_record(index_row(), classification_row(), attribution_row(verdict="indeterminate", dataset=None))
        self.assertEqual(record[sb.INFERRED], {})

    def test_every_inferred_value_carries_its_caveat(self) -> None:
        record = sb.build_record(index_row(), classification_row(health="has_hidden"), attribution_row())
        dataset = record[sb.INFERRED]["dataset"]
        for required in ("confidence", "meaning", "evidence", "caveat"):
            self.assertIn(required, dataset, f"an inferred value without {required!r} can be read as a fact")
        self.assertIn("not definitive", dataset["confidence"])

    def test_the_derivation_summary_lists_every_level(self) -> None:
        record = sb.build_record(index_row(), classification_row(), attribution_row())
        self.assertEqual(set(record["derivation_summary"]), set(sb.DERIVATIONS))


class PopulationClaimTest(unittest.TestCase):
    """THE load-bearing class.

    Item 3 trained **380 of 15,927** zero-node snapshots and all 380 succeeded. Writing
    ``formerly_broken`` onto every zero-node snapshot as a per-snapshot fact would fabricate a
    result for 15,547 files nobody ever trained -- exactly the "naive reasoning" §3.4's caveat
    exists to prevent.
    """

    def test_trainability_is_quarantined_in_the_population_bucket(self) -> None:
        record = sb.build_record(index_row(), classification_row(health="zero_node"), None)
        self.assertIn("trainability", record[sb.POPULATION])
        self.assertNotIn("trainability", record[sb.MEASURED], "a sampled cohort result must never sit beside per-snapshot measurements")
        self.assertNotIn("trainability", record[sb.OBSERVED])

    def test_the_claim_says_it_was_not_verified_here(self) -> None:
        record = sb.build_record(index_row(), classification_row(health="zero_node"), None)
        claim = record[sb.POPULATION]["trainability"]
        self.assertTrue(claim["not_verified_here"])
        self.assertIn("POPULATION claim", claim["caveat"])

    def test_the_claim_carries_its_sample_size(self) -> None:
        """A cohort claim without its n cannot be re-judged by a later reader."""
        claim = sb.build_record(index_row(), classification_row(health="zero_node"), None)[sb.POPULATION]["trainability"]
        self.assertIn("380", claim["basis"])
        self.assertEqual(claim["cohort_size"], 15927)
        self.assertGreater(claim["upper_bound_95_dysfunctional_rate"], 0.0)

    def test_a_grown_snapshot_gets_no_trainability_claim(self) -> None:
        """The sample covered the zero-node cohort only; it must not leak onto other rows."""
        record = sb.build_record(index_row(arch={"num_hidden_units": 40}), classification_row(health="has_hidden"), None)
        self.assertEqual(record[sb.POPULATION], {})

    def test_explain_renders_the_population_warning(self) -> None:
        text = sb.explain(sb.build_record(index_row(), classification_row(health="zero_node"), None))
        self.assertIn("NOT verified for this snapshot", text)


class IdentityIsNeverInventedTest(unittest.TestCase):
    """Run identity is UNRECOVERABLE: zero experiment run dirs survive from before 2026-07-30
    and the cohort is March-April. Absence must stay absence."""

    def test_missing_provenance_stays_none(self) -> None:
        record = sb.build_record(index_row(provenance=None), classification_row(), None)
        self.assertIsNone(record[sb.OBSERVED]["provenance"])

    def test_real_provenance_is_preserved_verbatim(self) -> None:
        provenance = {"run_id": "20260821T2210Z-a1b2", "experiment": "e-i-cap-ceiling"}
        record = sb.build_record(index_row(provenance=provenance), classification_row(), None)
        self.assertEqual(record[sb.OBSERVED]["provenance"], provenance)

    def test_explain_states_identity_is_unrecoverable(self) -> None:
        text = sb.explain(sb.build_record(index_row(provenance=None), classification_row(), None))
        self.assertIn("UNRECOVERABLE", text)

    def test_summary_separates_recovered_from_unrecoverable_identity(self) -> None:
        records = [
            sb.build_record(index_row(provenance={"run_id": "r"}), classification_row(), None),
            sb.build_record(index_row(provenance=None), classification_row(), None),
        ]
        summary = sb.summarise(records)
        self.assertEqual(summary["identity_recovered"], 1)
        self.assertEqual(summary["identity_unrecoverable"], 1)


class RootCauseTest(unittest.TestCase):
    """§3.4 puts root-causing the broken cohorts above everything else for research value."""

    def test_each_truncated_write_signature_maps_to_cohort_b(self) -> None:
        for detail in ("Missing required group: random", "Missing required group: params", "Invalid format: None"):
            cause = sb.classify_root_cause(detail)
            self.assertIsNotNone(cause, f"no root cause for {detail!r}")
            self.assertEqual(cause["cohort"], "B")
            self.assertIn("truncated write", cause["explanation"])

    def test_the_random_group_case_names_the_irrecoverable_loss(self) -> None:
        """265 of the 273 died inside _save_hidden_units; those tensors are simply gone."""
        cause = sb.classify_root_cause("Missing required group: random")
        self.assertIn("unrecoverable", cause["explanation"])

    def test_recoverable_causes_name_their_fix(self) -> None:
        for detail, cohort in (("output_size disagrees: …", "A"), ("snapshot could not be deserialized into a network", "C")):
            cause = sb.classify_root_cause(detail)
            self.assertEqual(cause["cohort"], cohort)
            self.assertIn("recoverable", cause["explanation"])

    def test_an_unknown_failure_gets_no_invented_cause(self) -> None:
        self.assertIsNone(sb.classify_root_cause("something nobody has seen before"))

    def test_a_failing_snapshot_records_both_detail_and_cause(self) -> None:
        record = sb.build_record(index_row(), classification_row(health="fails_to_load", load={"status": "snapshot_corrupt", "detail": "Missing required group: random"}), None)
        self.assertEqual(record[sb.MEASURED]["load_failure"], "Missing required group: random")
        self.assertEqual(record[sb.MEASURED]["root_cause"]["cohort"], "B")

    def test_a_healthy_snapshot_has_no_root_cause(self) -> None:
        record = sb.build_record(index_row(), classification_row(), None)
        self.assertNotIn("root_cause", record[sb.MEASURED])


class IterationsNotEpochsTest(unittest.TestCase):
    """``meta.current_epoch`` is inert (0 across all 27,908). The live measure is the
    hidden-unit count, and it is a LOWER BOUND on completed cascor iterations."""

    def test_the_field_is_named_as_a_bound(self) -> None:
        record = sb.build_record(index_row(), classification_row(iterations_lower_bound=95), None)
        self.assertEqual(record[sb.MEASURED]["iterations_lower_bound"], 95)
        self.assertNotIn("epoch", json.dumps(record[sb.MEASURED]).lower())

    def test_zero_is_recorded_rather_than_dropped(self) -> None:
        """0 hidden units is a measurement, not a missing value."""
        record = sb.build_record(index_row(), classification_row(iterations_lower_bound=0), None)
        self.assertEqual(record[sb.MEASURED]["iterations_lower_bound"], 0)


class SidecarAndCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _run(self, *argv) -> "tuple[int, str]":
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sb.main(["--root", str(self.root), *argv])
        return code, out.getvalue() + err.getvalue()

    def test_round_trips(self) -> None:
        records = [sb.build_record(index_row(), classification_row(), attribution_row())]
        sb.write_sidecar(self.root, records)
        self.assertEqual(sb.read_jsonl(self.root / sb.SIDECAR_NAME), records)

    def test_replaces_rather_than_appends(self) -> None:
        sb.write_sidecar(self.root, [sb.build_record(index_row(), None, None)])
        sb.write_sidecar(self.root, [sb.build_record(index_row(), None, None)])
        self.assertEqual(len(sb.read_jsonl(self.root / sb.SIDECAR_NAME)), 1)

    def test_missing_index_exits_2_and_names_the_fix(self) -> None:
        code, text = self._run("--stats")
        self.assertEqual(code, 2)
        self.assertIn("snapshot_index.py", text)

    def test_from_sidecar_without_one_exits_2(self) -> None:
        code, text = self._run("--from-sidecar", "--stats")
        self.assertEqual(code, 2)
        self.assertIn("--write", text)

    def test_explain_on_an_unknown_name_exits_2(self) -> None:
        sb.write_sidecar(self.root, [sb.build_record(index_row(), None, None)])
        code, _ = self._run("--from-sidecar", "--explain", "not-a-real-snapshot")
        self.assertEqual(code, 2)

    def test_missing_root_exits_2(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sb.main(["--root", str(self.root / "absent"), "--stats"])
        self.assertEqual(code, 2)


class NoDestructivePathTest(unittest.TestCase):
    """Snapshots are read-only project assets. §3.4: use the index, do not write into them."""

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
            self.assertNotIn(forbidden, called, f"snapshot_backfill.py must stay read-only; it calls {forbidden}")
        for flag in ("--prune", "--delete", "--yes"):
            self.assertNotIn(flag, cli_flags, f"snapshot_backfill.py must expose no destructive flag; found {flag}")

    def test_it_never_opens_a_snapshot_at_all(self) -> None:
        """Backfill reads the sidecars, not the archive. It must not touch HDF5."""
        self.assertNotIn("h5py", MODULE_PATH.read_text())


if __name__ == "__main__":
    unittest.main()
