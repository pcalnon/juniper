#!/usr/bin/env python3
"""Behavioural tests for util/snapshot_index.py (snapshot-lifecycle design §6.2).

Hermetic: fixtures are built with h5py directly, so nothing here needs the cascor
tree importable and no test touches the real ~27.9k archive.

The arms that carry weight:

- ``ReportingTest`` — ``--limit`` must not report deferred files as "already
  present". The first cut did, which made a completely unindexed archive read as
  27,606-of-27,906 done. A wrong count in a scan summary is believed, not checked.
- ``NoDestructivePathTest`` — retention is design §6.4 and is gated on this index
  existing. A delete path shipped here would prejudge that decision.
- ``QueryTest.test_finds_the_model_from_a_named_cell`` — the concrete question
  the census could not answer, which is the whole point of Phase 2.
"""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("snapshot_index", REPO_ROOT / "util" / "snapshot_index.py")
snapshot_index = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(snapshot_index)


def write_snapshot(root: Path, name: str, *, provenance: "dict | None" = None, arch: "dict | None" = None, groups=("meta", "config", "params", "arch", "random")) -> Path:
    """A structurally plausible snapshot, written the way cascor writes attrs."""
    path = root / name
    with h5py.File(path, "w") as hf:
        hf.attrs["created"] = np.bytes_("2026-08-21T12:00:00.000000")
        hf.attrs["format"] = np.bytes_("juniper.cascor")
        hf.attrs["format_version"] = np.bytes_("2")
        hf.attrs["juniper_version"] = np.bytes_("0.9.0")
        for group in groups:
            hf.create_group(group)
        if "meta" in groups:
            hf["meta"].attrs["uuid"] = np.bytes_("abc-123")
            hf["meta"].attrs["current_epoch"] = np.int64(7)
        if "arch" in groups:
            for key, value in (arch or {"input_size": 2, "output_size": 2, "num_hidden_units": 1}).items():
                hf["arch"].attrs[key] = np.int64(value) if isinstance(value, int) else np.bytes_(str(value))
        if provenance:
            group = hf.create_group("provenance")
            group.attrs["schema_version"] = np.bytes_("1")
            for key, value in provenance.items():
                group.attrs[key] = np.bytes_(value)
    return path


class TempRoot(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def run_cli(self, *argv: str) -> "tuple[int, str]":
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = snapshot_index.main(["--root", str(self.root), *argv])
        return rc, buf.getvalue()


class TierTest(unittest.TestCase):
    def test_classifies_each_writer(self) -> None:
        self.assertEqual(snapshot_index.classify_tier("cascor_snapshot_20260821_120000_uuid.h5"), "model")
        self.assertEqual(snapshot_index.classify_tier("snapshot_2026-08-21T12:00:00Z.h5"), "service")

    def test_unrecognised_name_is_unknown_not_forced(self) -> None:
        """An unfamiliar writer must be recorded honestly, not bucketed into one."""
        self.assertEqual(snapshot_index.classify_tier("something_else.h5"), "unknown")


class ScanRecordTest(TempRoot):
    def test_record_decodes_bytes_attrs(self) -> None:
        """cascor writes attrs as ``np.bytes_``; a raw read serialises to "b'...'"
        and compares unequal to every string a caller filters on."""
        write_snapshot(self.root, "cascor_snapshot_a.h5", provenance={"experiment": "e-i", "cell_id": "c001"})
        record = snapshot_index.scan_one(self.root / "cascor_snapshot_a.h5")

        self.assertTrue(record["readable"])
        self.assertEqual(record["created"], "2026-08-21T12:00:00.000000")
        self.assertEqual(record["uuid"], "abc-123")
        self.assertEqual(record["provenance"], {"experiment": "e-i", "cell_id": "c001"})
        self.assertNotIn("b'", json.dumps(record), "no attribute may survive as a bytes repr")

    def test_records_groups_rather_than_judging_validity(self) -> None:
        """The index records the FACT (which groups exist); cascor owns the verdict.

        Re-implementing the required-group list here would create a second copy
        free to drift from ``_validate_format_detail``.
        """
        write_snapshot(self.root, "cascor_snapshot_b.h5", groups=("meta", "arch"))
        record = snapshot_index.scan_one(self.root / "cascor_snapshot_b.h5")

        self.assertEqual(record["groups"], ["arch", "meta"])
        self.assertNotIn("verdict", record, "no verdict without --verify")

    def test_unreadable_file_is_a_recorded_fact_not_a_crash(self) -> None:
        (self.root / "cascor_snapshot_bad.h5").write_bytes(b"not hdf5")
        record = snapshot_index.scan_one(self.root / "cascor_snapshot_bad.h5")

        self.assertFalse(record["readable"])
        self.assertIn("error", record)

    def test_snapshot_without_provenance_records_none(self) -> None:
        write_snapshot(self.root, "cascor_snapshot_c.h5")
        self.assertIsNone(snapshot_index.scan_one(self.root / "cascor_snapshot_c.h5")["provenance"])


class ReportingTest(TempRoot):
    """``--limit`` must not inflate the already-indexed count."""

    def test_deferred_is_not_reported_as_already_present(self) -> None:
        for i in range(5):
            write_snapshot(self.root, f"cascor_snapshot_{i}.h5")

        written, already, deferred, _ = snapshot_index.scan(self.root, limit=2)

        self.assertEqual((written, already, deferred), (2, 0, 3), "a first scan has nothing 'already present' — the remainder is deferred by --limit")

    def test_second_scan_reports_the_first_batch_as_present(self) -> None:
        for i in range(5):
            write_snapshot(self.root, f"cascor_snapshot_{i}.h5")
        snapshot_index.scan(self.root, limit=2)

        written, already, deferred, _ = snapshot_index.scan(self.root, limit=2)

        self.assertEqual((written, already, deferred), (2, 2, 1))


class AppendOnlyTest(TempRoot):
    def test_rescan_appends_only_new_files(self) -> None:
        write_snapshot(self.root, "cascor_snapshot_1.h5")
        snapshot_index.scan(self.root)
        write_snapshot(self.root, "cascor_snapshot_2.h5")

        written, already, _, index_path = snapshot_index.scan(self.root)

        self.assertEqual((written, already), (1, 1))
        self.assertEqual(len(snapshot_index.read_index(index_path)), 2, "the existing record must not be rewritten")

    def test_rebuild_starts_fresh(self) -> None:
        write_snapshot(self.root, "cascor_snapshot_1.h5")
        snapshot_index.scan(self.root)
        written, _, _, index_path = snapshot_index.scan(self.root, rebuild=True)

        self.assertEqual(written, 1)
        self.assertEqual(len(snapshot_index.read_index(index_path)), 1, "--rebuild must replace, not duplicate")

    def test_truncated_line_costs_one_record_not_the_index(self) -> None:
        write_snapshot(self.root, "cascor_snapshot_1.h5")
        _, _, _, index_path = snapshot_index.scan(self.root)
        with index_path.open("a") as handle:
            handle.write('{"path": "truncated"\n')

        self.assertEqual(len(snapshot_index.read_index(index_path)), 1, "a half-written final line must not poison the whole index")


class QueryTest(TempRoot):
    def setUp(self) -> None:
        super().setUp()
        write_snapshot(self.root, "cascor_snapshot_hit.h5", provenance={"experiment": "e-i-cap-ceiling", "cell_id": "c128-capsweep", "run_id": "r1"})
        write_snapshot(self.root, "cascor_snapshot_other.h5", provenance={"experiment": "e-a-grid", "cell_id": "c003", "run_id": "r2"})
        write_snapshot(self.root, "cascor_snapshot_legacy.h5")
        snapshot_index.scan(self.root)

    def test_finds_the_model_from_a_named_cell(self) -> None:
        """The question the census could not answer."""
        rc, out = self.run_cli("--experiment", "e-i-cap-ceiling", "--cell-id", "c128-capsweep")
        self.assertEqual(rc, 0)
        self.assertIn("cascor_snapshot_hit.h5", out)
        self.assertNotIn("cascor_snapshot_other.h5", out)

    def test_unattributed_selects_the_legacy_archive(self) -> None:
        rc, out = self.run_cli("--unattributed", "--json")
        self.assertEqual(rc, 0)
        rows = json.loads(out)
        self.assertEqual([r["name"] for r in rows], ["cascor_snapshot_legacy.h5"])

    def test_attributed_excludes_it(self) -> None:
        rc, out = self.run_cli("--attributed", "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(len(json.loads(out)), 2)

    def test_stats_counts_attribution(self) -> None:
        rc, out = self.run_cli("--stats", "--json")
        self.assertEqual(rc, 0)
        stats = json.loads(out)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["attributed"], 2)
        self.assertEqual(stats["unattributed"], 1)
        self.assertEqual(stats["by_experiment"]["e-i-cap-ceiling"], 1)

    def test_missing_index_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = snapshot_index.main(["--root", empty, "--stats"])
            self.assertEqual(rc, 2)
            self.assertIn("--scan first", buf.getvalue())

    def test_contradictory_filters_exit_2(self) -> None:
        rc, out = self.run_cli("--attributed", "--unattributed")
        self.assertEqual(rc, 2)
        self.assertIn("mutually exclusive", out)

    def test_missing_root_exits_2(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = snapshot_index.main(["--root", str(self.root / "nope"), "--stats"])
        self.assertEqual(rc, 2)


class NoDestructivePathTest(unittest.TestCase):
    """Retention is design §6.4 and is GATED on this index existing.

    Shipping a delete path in the change that first makes the archive legible
    would prejudge the decision this tool is meant to inform. Anti-resurrection,
    because "add a --prune while you're in there" is the obvious next edit.
    """

    def test_module_has_no_delete_surface(self) -> None:
        """Inspect the AST, not the prose.

        A plain substring grep fires on the docstring section that explains *why*
        there is no ``--prune`` — the documentation of the rule would break the
        test enforcing it, and the tempting fix is to delete the explanation.
        """
        import ast

        tree = ast.parse((REPO_ROOT / "util" / "snapshot_index.py").read_text())

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
            self.assertNotIn(forbidden, called, f"snapshot_index.py must stay read-only; it calls {forbidden} (retention is §6.4 and gated)")
        for flag in ("--prune", "--delete", "--yes"):
            self.assertNotIn(flag, cli_flags, f"snapshot_index.py must expose no destructive flag; found {flag}")

    def test_scan_opens_files_read_only(self) -> None:
        source = (REPO_ROOT / "util" / "snapshot_index.py").read_text()
        self.assertIn('h5py.File(path, "r")', source, "snapshots must never be opened writable by the indexer")


if __name__ == "__main__":
    unittest.main()
