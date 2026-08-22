#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   snapshots
# File Name:     test_snapshot_classify.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Regression suite for util/snapshot_classify.py -- the read-only classifier that implements the
#   owner's five-category snapshot scheme (handoff 2026-08-22 §2.4) over the §6.2 index.
#####################################################################################################################################################################################################
"""Pin the classifier's contracts.

Each class below pins a failure this arc actually hit or narrowly avoided, not a
hypothetical:

* ``CategoryAssignmentTest``   -- the two-axis rule, including the attributed zero-node
  row that the first cut of the tool dropped into ``undetermined`` so category 5 came
  out empty against an archive that demonstrably has one attributed snapshot.
* ``ReadableIsNotLoadableTest`` -- the handoff's §3.1 claim that category 1 is derivable
  from the index. It is not: ``readable`` is an h5py fact. Measured 7/300.
* ``IterationsNotEpochsTest``  -- ``meta.current_epoch`` is inert (0 across all 27,908
  snapshots, including a network that grew to 260 units). Reading it as progress is what
  would have justified deleting 27,005 real models.
* ``SidecarTest``             -- replace-not-append, because a deeper stage revises a
  verdict and two contradictory rows for one path would make the answer file-order.
* ``NoDestructivePathTest``   -- anti-resurrection, mirroring the same guard on
  ``snapshot_index.py``. Retention is §6.4 and is gated on this tool's output; a
  ``--prune`` added here would prejudge it.
* ``TrainStageGuardTest``     -- ``train_output_layer`` calls ``create_snapshot()``
  unconditionally, so a train stage pointed at the default root grows the archive it is
  measuring.
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

import snapshot_classify as sc  # noqa: E402 - path bootstrap must precede the import

MODULE_PATH = REPO_ROOT / "util" / "snapshot_classify.py"


def index_row(**overrides) -> dict:
    """A minimal §6.2 index record, shaped like the ones the real scanner writes."""
    row = {
        "schema_version": 1,
        "path": "/archive/cascor_snapshot_20260401_000000_aaaaaaaa.h5",
        "name": "cascor_snapshot_20260401_000000_aaaaaaaa.h5",
        "tier": "model",
        "size_bytes": 48893,
        "readable": True,
        "groups": ["arch", "config", "meta", "mp", "params", "random"],
        "created": "2026-04-01T00:00:00",
        "uuid": "aaaaaaaa-0000-0000-0000-000000000000",
        "arch": {"input_size": 2, "output_size": 2, "num_hidden_units": 0},
        "provenance": None,
    }
    row.update(overrides)
    return row


class CategoryAssignmentTest(unittest.TestCase):
    """The two-axis rule. ``category`` answers 'must we reconstruct?'; ``health`` answers 'what works?'."""

    def test_hidden_units_without_provenance_is_category_four(self) -> None:
        verdict = sc.classify_index_stage(index_row(arch={"num_hidden_units": 3}))
        self.assertEqual(verdict["category"], sc.LOADS_HIDDEN_NODES)
        self.assertEqual(verdict["health"], sc.HEALTH_HAS_HIDDEN)
        self.assertEqual(verdict["iterations_lower_bound"], 3)

    def test_attributed_zero_node_is_category_five_not_undetermined(self) -> None:
        """The regression that motivated ``assign_category``.

        The archive's ONLY attributed snapshot has zero hidden units. When attribution
        was consulted on the has-hidden path but not the zero-node path, this row fell
        through to ``undetermined`` and the population table reported category 5 as
        empty -- against an index that plainly holds one attributed record.
        """
        verdict = sc.classify_index_stage(index_row(provenance={"run_id": "20260821T2210Z-a1b2"}))
        self.assertEqual(verdict["category"], sc.FULLY_ATTRIBUTED)
        self.assertEqual(verdict["health"], sc.HEALTH_ZERO_NODE, "attribution must not overwrite the health fact")

    def test_fails_to_load_overrides_attribution(self) -> None:
        """A broken file is category 1 however good its metadata is.

        'Fully attributed' means nothing needs reconstructing. A file that will not load
        needs a root cause, so filing it as finished work would lose exactly the
        population §3.4 wants root-caused.
        """
        verdict = sc.classify_index_stage(index_row(provenance={"run_id": "r"}, arch={"num_hidden_units": 5}))
        sc.apply_load_result(verdict, "snapshot_corrupt", "Missing required group: random", "ok")
        self.assertEqual(verdict["category"], sc.FAILS_TO_LOAD)
        self.assertEqual(verdict["health"], sc.HEALTH_FAILS_TO_LOAD)

    def test_zero_node_unattributed_stays_undetermined_until_the_train_stage(self) -> None:
        verdict = sc.classify_index_stage(index_row())
        self.assertEqual(verdict["category"], sc.UNDETERMINED)
        self.assertEqual(verdict["health"], sc.HEALTH_ZERO_NODE)
        self.assertIn("train stage", verdict["reason"])

    def test_missing_arch_never_claims_category_five(self) -> None:
        """Loadability is unresolved, and it is the one thing that outranks attribution."""
        verdict = sc.classify_index_stage(index_row(arch={}, provenance={"run_id": "r"}))
        self.assertEqual(verdict["category"], sc.UNDETERMINED)
        self.assertEqual(verdict["health"], sc.HEALTH_UNDETERMINED)

    def test_both_stages_agree_on_the_same_row(self) -> None:
        """One ``assign_category`` for both stages, so they cannot drift apart."""
        for attributed in (None, {"run_id": "r"}):
            for units in (0, 4):
                row = index_row(arch={"num_hidden_units": units}, provenance=attributed)
                indexed = sc.classify_index_stage(row)
                loaded = sc.apply_load_result(sc.classify_index_stage(row), "ok", "", "ok")
                self.assertEqual(indexed["category"], loaded["category"], f"stage disagreement at units={units} attributed={bool(attributed)}")


class ReadableIsNotLoadableTest(unittest.TestCase):
    """The handoff's §3.1 shortcut, pinned as wrong.

    §3.1 says categories 1/4/5 are 'already derivable without opening a file:
    ``readable``, ``arch.num_hidden_units > 0``, ``provenance != null``'. The index marks
    all 27,908 archive files readable because ``readable`` records only that h5py opened
    the file. A 300-file load probe found 7 refusals (5 arch-mismatch, 2 corrupt).
    """

    def test_readable_row_is_not_classified_as_loading(self) -> None:
        verdict = sc.classify_index_stage(index_row(readable=True, arch={"num_hidden_units": 2}))
        self.assertEqual(verdict["stage"], "index", "an index-stage verdict must not claim load confirmation")
        self.assertIsNone(verdict["load"])

    def test_a_readable_file_can_still_fail_to_load(self) -> None:
        verdict = sc.classify_index_stage(index_row(readable=True, arch={"num_hidden_units": 2}))
        sc.apply_load_result(verdict, "snapshot_arch_mismatch", "output_size disagrees: the snapshot's arch group says 3, the network built from its config is 2", "ok")
        self.assertEqual(verdict["category"], sc.FAILS_TO_LOAD)
        self.assertEqual(verdict["stage"], "load")


class FailureSignatureTest(unittest.TestCase):
    """Root-cause bucketing (§3.4) needs faults grouped by SHAPE, not by file."""

    def test_paths_and_numbers_collapse_so_one_fault_is_one_bucket(self) -> None:
        first = sc.failure_signature("output_size disagrees: the snapshot's arch group says 3, the network built from its config is 2")
        second = sc.failure_signature("output_size disagrees: the snapshot's arch group says 7, the network built from its config is 4")
        self.assertEqual(first, second, "two instances of one fault must share a signature")

    def test_distinct_faults_stay_distinct(self) -> None:
        self.assertNotEqual(sc.failure_signature("Missing required group: random"), sc.failure_signature("Invalid format: None"))

    def test_empty_detail_is_labelled_not_blank(self) -> None:
        self.assertEqual(sc.failure_signature(""), "(no detail)")


class IterationsNotEpochsTest(unittest.TestCase):
    """§2.1 — hidden-unit count, never an epoch counter.

    ``meta.current_epoch`` is 0 across all 27,908 snapshots including all 174 belonging
    to a network that grew to 260 hidden units; ``snapshot_counter`` is 0 and
    ``best_value_loss`` is inf. Reading those as progress says 'nothing here was trained',
    which would have justified deleting 27,005 real models.
    """

    def test_hidden_units_is_the_measure(self) -> None:
        self.assertEqual(sc.hidden_units(index_row(arch={"num_hidden_units": 260})), 260)

    def test_inert_epoch_counter_is_never_consulted(self) -> None:
        verdict = sc.classify_index_stage(index_row(arch={"num_hidden_units": 12}, current_epoch=0))
        self.assertEqual(verdict["iterations_lower_bound"], 12, "an inert current_epoch=0 must not reduce the bound")

    def test_absent_arch_yields_no_bound_rather_than_zero(self) -> None:
        """``None`` and ``0`` mean different things: unknown vs measured-as-none."""
        self.assertIsNone(sc.hidden_units(index_row(arch={})))

    def test_non_numeric_units_degrade_to_unknown(self) -> None:
        self.assertIsNone(sc.hidden_units(index_row(arch={"num_hidden_units": "corrupted"})))

    def test_summary_separates_unknown_from_zero(self) -> None:
        summary = sc.summarise([sc.classify_index_stage(index_row(arch={})), sc.classify_index_stage(index_row(arch={"num_hidden_units": 0})), sc.classify_index_stage(index_row(arch={"num_hidden_units": 5}))])
        self.assertEqual(summary["iterations_lower_bound"]["measured"], 2, "the unknown row must not be counted as measured")
        self.assertEqual(summary["iterations_lower_bound"]["zero"], 1)
        self.assertEqual(summary["iterations_lower_bound"]["at_least_one"], 1)


class SidecarTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_rewrite_replaces_rather_than_appends(self) -> None:
        """A deeper stage revises a verdict; appending would leave two rows for one path."""
        first = [sc.classify_index_stage(index_row())]
        sc.write_sidecar(self.root, first)
        revised = [sc.apply_load_result(sc.classify_index_stage(index_row()), "snapshot_corrupt", "boom", "ok")]
        sidecar = sc.write_sidecar(self.root, revised)
        rows = [json.loads(line) for line in sidecar.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 1, "the sidecar must hold one row per path, not an append log")
        self.assertEqual(rows[0]["category"], sc.FAILS_TO_LOAD)

    def test_no_temp_file_survives_a_successful_write(self) -> None:
        sc.write_sidecar(self.root, [sc.classify_index_stage(index_row())])
        self.assertEqual([p.name for p in self.root.iterdir()], [sc.SIDECAR_NAME])

    def test_round_trips_a_load_stage_verdict(self) -> None:
        """The write/read pair must preserve the one thing only the load stage knows.

        ``fails_to_load`` cannot be re-derived from the index, so if the sidecar did not
        round-trip it the 14-minute pass would have to be repeated for every query.
        """
        written = [sc.apply_load_result(sc.classify_index_stage(index_row()), "snapshot_corrupt", "Missing required group: random", "ok")]
        sc.write_sidecar(self.root, written)
        restored = sc.read_sidecar(self.root)
        self.assertEqual(len(restored), 1)
        self.assertEqual(restored[0]["category"], sc.FAILS_TO_LOAD)
        self.assertEqual(restored[0]["load"]["detail"], "Missing required group: random")

    def test_absent_sidecar_reads_as_empty_not_an_error(self) -> None:
        self.assertEqual(sc.read_sidecar(self.root), [])

    def test_truncated_line_costs_one_record_not_the_file(self) -> None:
        (self.root / sc.SIDECAR_NAME).write_text(json.dumps(sc.classify_index_stage(index_row())) + "\n{ truncated")
        self.assertEqual(len(sc.read_sidecar(self.root)), 1)


class MuffleStdoutTest(unittest.TestCase):
    """The cascor log leak that breaks ``--json``.

    ``logging.disable`` is undone mid-pass by cascor's per-network ``dictConfig``, so the
    suppression must sit below the logging module entirely.
    """

    def test_muffling_swallows_fd_level_writes(self) -> None:
        import os

        with tempfile.TemporaryFile(mode="w+") as sink:
            saved = os.dup(1)
            try:
                os.dup2(sink.fileno(), 1)
                with sc._muffle_stdout(True):
                    os.write(1, b"NOISE\n")
                os.write(1, b"KEPT\n")
            finally:
                os.dup2(saved, 1)
                os.close(saved)
            sink.seek(0)
            captured = sink.read()
        self.assertNotIn("NOISE", captured, "muffled writes must not reach stdout")
        self.assertIn("KEPT", captured, "stdout must be restored after the block")

    def test_disabled_muffling_is_a_passthrough(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer), sc._muffle_stdout(False):
            print("visible")
        self.assertIn("visible", buffer.getvalue())


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _write_index(self, rows) -> None:
        (self.root / sc.INDEX_NAME).write_text("".join(json.dumps(r) + "\n" for r in rows))

    def _run(self, *argv) -> "tuple[int, str]":
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sc.main(["--root", str(self.root), *argv])
        return code, out.getvalue() + err.getvalue()

    def test_missing_index_exits_2_and_names_the_fix(self) -> None:
        code, text = self._run("--stats")
        self.assertEqual(code, 2)
        self.assertIn("--scan", text, "the error must name the command that builds the index")

    def test_missing_root_exits_2(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sc.main(["--root", str(self.root / "absent"), "--stats"])
        self.assertEqual(code, 2)

    def test_stats_counts_the_population(self) -> None:
        self._write_index([index_row(arch={"num_hidden_units": 2}), index_row(arch={"num_hidden_units": 0}), index_row(arch={"num_hidden_units": 0}, provenance={"run_id": "r"})])
        code, text = self._run("--stats")
        self.assertEqual(code, 0)
        summary = json.loads(text)
        self.assertEqual(summary["by_category"][sc.LOADS_HIDDEN_NODES], 1)
        self.assertEqual(summary["by_category"][sc.FULLY_ATTRIBUTED], 1)
        self.assertEqual(summary["by_category"][sc.UNDETERMINED], 1)

    def test_sampled_run_refuses_to_write_a_partial_sidecar(self) -> None:
        """A sampled classification replacing the whole-archive sidecar would silently
        shrink it from 27,908 rows to N, and the sidecar is a replace-not-append file."""
        self._write_index([index_row() for _ in range(5)])
        code, text = self._run("--sample", "2", "--write")
        self.assertEqual(code, 2)
        self.assertIn("sampled", text)
        self.assertFalse((self.root / sc.SIDECAR_NAME).exists())

    def test_sample_is_repeatable_under_a_fixed_seed(self) -> None:
        self._write_index([index_row(name=f"s{i}.h5", path=f"/a/s{i}.h5") for i in range(50)])
        _, first = self._run("--sample", "5", "--json")
        _, second = self._run("--sample", "5", "--json")
        self.assertEqual(first, second)

    def test_category_filter_selects(self) -> None:
        self._write_index([index_row(arch={"num_hidden_units": 2}), index_row(arch={"num_hidden_units": 0})])
        _, text = self._run("--category", sc.LOADS_HIDDEN_NODES, "--json")
        self.assertEqual(len(json.loads(text)), 1)

    def test_from_sidecar_returns_the_stored_load_verdicts(self) -> None:
        """The gap this closed: `--category fails_to_load` reported "no matching
        snapshots" against a sidecar holding 526 of them, because re-deriving from the
        index can never produce that category."""
        self._write_index([index_row()])
        sc.write_sidecar(self.root, [sc.apply_load_result(sc.classify_index_stage(index_row()), "snapshot_corrupt", "boom", "ok")])
        code, text = self._run("--from-sidecar", "--category", sc.FAILS_TO_LOAD, "--json")
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(text)), 1)

    def test_from_sidecar_without_one_exits_2_and_names_the_fix(self) -> None:
        self._write_index([index_row()])
        code, text = self._run("--from-sidecar", "--stats")
        self.assertEqual(code, 2)
        self.assertIn("--stage load --write", text)

    def test_from_sidecar_refuses_to_combine_with_a_stage(self) -> None:
        """Stored verdicts and a fresh classification are different answers; silently
        preferring one would make the output depend on flag order."""
        self._write_index([index_row()])
        sc.write_sidecar(self.root, [sc.classify_index_stage(index_row())])
        code, _ = self._run("--from-sidecar", "--stage", "load")
        self.assertEqual(code, 2)

    def test_from_sidecar_refuses_to_write(self) -> None:
        self._write_index([index_row()])
        sc.write_sidecar(self.root, [sc.classify_index_stage(index_row())])
        code, text = self._run("--from-sidecar", "--write")
        self.assertEqual(code, 2)
        self.assertIn("rewrite the sidecar from itself", text)

    def test_empty_index_exits_2_rather_than_reporting_a_clean_archive(self) -> None:
        """A zero-row summary reads as 'nothing wrong here', which is the vacuous-pass class."""
        (self.root / sc.INDEX_NAME).write_text("")
        code, _ = self._run("--stats")
        self.assertEqual(code, 2)


class TrainStageGuardTest(unittest.TestCase):
    """``train_output_layer`` calls ``create_snapshot()`` unconditionally (trap §5.7)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        (self.root / sc.INDEX_NAME).write_text(json.dumps(index_row()) + "\n")

    def _run_train(self, env_value) -> "tuple[int, str]":
        import os

        previous = os.environ.get(sc.DEFAULT_ROOT_ENV)
        if env_value is None:
            os.environ.pop(sc.DEFAULT_ROOT_ENV, None)
        else:
            os.environ[sc.DEFAULT_ROOT_ENV] = env_value
        try:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = sc.main(["--root", str(self.root), "--stage", "train"])
            return code, out.getvalue() + err.getvalue()
        finally:
            os.environ.pop(sc.DEFAULT_ROOT_ENV, None)
            if previous is not None:
                os.environ[sc.DEFAULT_ROOT_ENV] = previous

    def test_train_without_a_scratch_root_refuses(self) -> None:
        code, text = self._run_train(None)
        self.assertNotEqual(code, 0)
        self.assertIn("create_snapshot", text, "the refusal must name WHY training writes")

    def test_train_pointed_at_the_real_archive_refuses(self) -> None:
        code, text = self._run_train(str(sc.DEFAULT_ROOT_FALLBACK))
        self.assertNotEqual(code, 0)
        self.assertIn("scratch", text)

    def test_train_stage_is_honestly_unimplemented(self) -> None:
        """It must not silently report categories 2 and 3 as zero."""
        code, text = self._run_train(str(self.root / "scratch"))
        self.assertEqual(code, 2)
        self.assertIn("not implemented", text)


class NoDestructivePathTest(unittest.TestCase):
    """Retention is §6.4 and is GATED on this tool's output.

    Anti-resurrection, mirroring the guard on ``snapshot_index.py``: a ``--prune`` added
    to the tool that FORMS the verdict would act on it in the same breath, prejudging the
    owner's decision.
    """

    def test_module_has_no_delete_surface(self) -> None:
        """Inspect the AST, not the prose — the docstring explains why there is no
        ``--prune``, and a substring grep would fire on the explanation, making the
        tempting fix 'delete the documentation of the rule'."""
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
        for forbidden in ("os.remove", "shutil.rmtree", "unlink", "rmdir"):
            self.assertNotIn(forbidden, called, f"snapshot_classify.py must stay read-only; it calls {forbidden}")
        for flag in ("--prune", "--delete", "--yes"):
            self.assertNotIn(flag, cli_flags, f"snapshot_classify.py must expose no destructive flag; found {flag}")

    def test_snapshots_are_never_opened_writable(self) -> None:
        """The only file this tool writes is the derived sidecar, in the snapshot root."""
        source = MODULE_PATH.read_text()
        self.assertNotIn("h5py.File(", source, "the classifier reads the index and the loader; it must not open .h5 files itself")

    def test_the_only_write_target_is_the_sidecar(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text())
        write_modes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "open":
                for arg in list(node.args) + [kw.value for kw in node.keywords if kw.arg == "mode"]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        write_modes.add(arg.value)
        self.assertLessEqual(write_modes - {"r"}, {"w"}, f"unexpected file modes: {write_modes}")


if __name__ == "__main__":
    unittest.main()
