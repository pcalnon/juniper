#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   snapshots
# File Name:     snapshot_index.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Read-only scanner + query CLI for a cascor snapshot root (snapshot-lifecycle design §6.2,
#   "Phase 2 — Index and query", delivers R2). Builds an append-only snapshots_index.jsonl of one
#   record per snapshot, then answers questions over it without opening a single .h5 again.
#   Safety discipline mirrors util/experiments/list_runs.py: read-only by default, --json for
#   machine use. This tool has NO destructive path at all — see "Why there is no --prune" below.
#####################################################################################################################################################################################################
"""Index and query a cascor snapshot archive.

Usage:
    python util/snapshot_index.py --scan [--root DIR] [--verify]
    python util/snapshot_index.py --experiment e-i-cap-ceiling --json
    python util/snapshot_index.py --cell-id c007-9f3ab12c
    python util/snapshot_index.py --unattributed --limit 20
    python util/snapshot_index.py --stats

The archive is ~27.9k files. Opening each one to answer a question is why
"find the model from the E-I cap-128 cell" was unanswerable in practice even
once D-C made the answer *present* in the files: identity you cannot query is
not much better than identity you do not have. The index is what closes that,
and per the design it is worth building **even if no file is ever deleted**.

WHAT A RECORD HOLDS
    path, size_bytes, tier, created, uuid, arch summary, the groups actually
    present, the D-C provenance block, and (only under ``--verify``) cascor's
    own verification verdict.

WHY THE SCAN DOES NOT JUDGE VALIDITY BY DEFAULT
    Deciding which groups a valid snapshot must have is cascor's policy, and it
    lives in ``_validate_format_detail``. Re-implementing that list here would
    create a second copy free to drift from the first -- the exact failure class
    this arc kept finding. So the scan records the FACT (which groups exist) and
    leaves the VERDICT to cascor: ``--verify`` imports the real verifier and
    records what it says. Slower, authoritative, opt-in.

WHY THERE IS NO --prune
    Retention is design §6.4 and is explicitly gated on this index existing --
    the whole point of ordering identity before retention is that a deletion
    rule over anonymous artifacts is guesswork. Shipping a delete path in the
    same change that first makes the archive legible would prejudge that
    decision. This tool only reads.

    (There is also a live hazard next door: ``snapshot_cli.py cleanup --keep N``
    is count-based, and pointed at a shared root would select by mtime -- which
    in this archive is NOT creation time, because a copy reset them all. cascor
    guards that with a shared-root refusal; do not add a second, unguarded path
    to the same place.)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    import h5py
except ImportError:  # pragma: no cover - environment guard
    print("ERROR: h5py is required (conda activate JuniperCascor1)", file=sys.stderr)
    raise

INDEX_NAME = "snapshots_index.jsonl"
SCHEMA_VERSION = 1

#: Snapshot roots, in resolution order. Mirrors the ecosystem convention so the
#: tool finds the archive without being told where it is.
DEFAULT_ROOT_ENV = "JUNIPER_CASCOR_SNAPSHOTS_DIR"
DEFAULT_ROOT_FALLBACK = Path.home() / "Development" / "python" / "Juniper" / "juniper-cascor" / "cascor-snapshots"

#: D-C provenance fields, in the order a human wants to read them.
PROVENANCE_FIELDS = ("run_id", "experiment", "cell_id", "dataset_id", "git_sha")

ARCH_FIELDS = ("input_size", "output_size", "num_hidden_units", "activation_function_name")

#: Experiment run root, holding <run_id>/manifest.json. Mirrors the drivers' own default.
DEFAULT_RUN_ROOT_ENV = "JUNIPER_EXP_RUN_ROOT"
DEFAULT_RUN_ROOT_FALLBACK = Path.home() / ".local" / "state" / "juniper-experiments"


def default_run_root() -> Path:
    override = os.environ.get(DEFAULT_RUN_ROOT_ENV, "").strip()
    return Path(override).expanduser() if override else DEFAULT_RUN_ROOT_FALLBACK


def resolve_dataset(run_id: Optional[str], run_root: Path, cache: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Recover a snapshot's dataset identity by joining on ``run_id``.

    ``dataset_id`` is DERIVED, not stored in the snapshot, and that is deliberate.
    It is content-addressed by ``generate_dataset_id(generator, version, params)``,
    and the generator *version* comes from a live query against juniper-data --
    which happens only after ``run_experiment`` starts driving, long after cascor's
    process env was fixed at exec. So no amount of launch-env plumbing can put it
    in the file; it is simply not knowable at bring-up.

    It does not need to be. ``run_experiment`` already writes it to the run's
    ``manifest.json``, and D-C records ``run_id`` in the snapshot, so the join
    recovers it exactly -- and works for snapshots written before this tool
    existed, provided they carry a run_id.

    Resolving at QUERY time rather than baking it into the index also avoids a
    stale miss: a snapshot is written during training, while the manifest is
    written when the run ends, so a scan mid-run would record "no dataset"
    permanently.

    Returns the dataset block, or None when there is no run_id or no manifest.
    """
    if not run_id:
        return None
    if run_id in cache:
        return cache[run_id]
    manifest_path = run_root / run_id / "manifest.json"
    resolved: Optional[Dict[str, Any]] = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, ValueError):
            manifest = {}
        dataset = manifest.get("dataset") if isinstance(manifest, dict) else None
        if isinstance(dataset, dict):
            resolved = {key: dataset.get(key) for key in ("dataset_id", "generator", "version") if dataset.get(key) is not None} or None
    cache[run_id] = resolved
    return resolved


def default_root() -> Path:
    override = os.environ.get(DEFAULT_ROOT_ENV, "").strip()
    return Path(override).expanduser() if override else DEFAULT_ROOT_FALLBACK


def mapping(value: Any) -> Dict[str, Any]:
    """The sub-object at ``value`` when it really is a mapping, else an empty dict.

    ``x.get(k) or {}`` guards ABSENCE, not TYPE. A truthy non-dict -- a list, a string, a
    number -- sails straight through it into the next ``.get`` and raises
    ``AttributeError``, which kills the whole read rather than the one malformed row.
    ``x.get(k, {})`` is weaker still: it substitutes the default only when the key is
    MISSING, so an explicit ``null`` reaches the next ``.get`` as ``None``.

    These rows are parsed from ``snapshots_index.jsonl`` / ``manifest.json``, written by a
    different process at a different time, so the shape is an assumption rather than a
    guarantee -- a partially written or hand-edited record is exactly the case where the
    index most needs to stay readable.
    """
    return value if isinstance(value, dict) else {}


def _attr(group: Any, key: str) -> Optional[Any]:
    """Read one HDF5 attribute, decoding the bytes form the writer uses.

    ``write_str_attr`` stores ``np.bytes_``; a bare read hands back bytes that
    serialise to ``"b'...'"`` in JSON and compare unequal to every string a
    caller will filter on.
    """
    if key not in group.attrs:
        return None
    value = group.attrs[key]
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def classify_tier(name: str) -> str:
    """Which writer produced this file, by filename convention.

    ``cascor_snapshot_<date>_<time>_<uuid>.h5`` is the model tier's auto-snapshot;
    ``snapshot_<iso>Z.h5`` is the service tier's. Anything else is honestly
    ``unknown`` rather than forced into one of them.
    """
    if name.startswith("cascor_snapshot_"):
        return "model"
    if name.startswith("snapshot_"):
        return "service"
    return "unknown"


def scan_one(path: Path, *, verify: bool = False) -> Dict[str, Any]:
    """Build one index record. Read-only; never writes to the snapshot."""
    record: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "path": str(path),
        "name": path.name,
        "tier": classify_tier(path.name),
        "size_bytes": path.stat().st_size,
        "readable": False,
        "groups": [],
        "created": None,
        "uuid": None,
        "juniper_version": None,
        "arch": {},
        "provenance": None,
    }
    try:
        with h5py.File(path, "r") as hf:
            record["readable"] = True
            record["groups"] = sorted(hf.keys())
            record["created"] = _attr(hf, "created")
            record["juniper_version"] = _attr(hf, "juniper_version")
            record["format_version"] = _attr(hf, "format_version")
            if "meta" in hf:
                record["uuid"] = _attr(hf["meta"], "uuid")
                record["current_epoch"] = _attr(hf["meta"], "current_epoch")
            if "arch" in hf:
                record["arch"] = {field: _attr(hf["arch"], field) for field in ARCH_FIELDS if field in hf["arch"].attrs}
            if "provenance" in hf:
                group = hf["provenance"]
                found = {field: _attr(group, field) for field in PROVENANCE_FIELDS if field in group.attrs}
                record["provenance"] = found or None
    except Exception as exc:  # noqa: BLE001 - an unreadable file is a fact to record, not a crash
        record["error"] = f"{type(exc).__name__}: {exc}"

    if verify:
        record["verdict"] = _cascor_verdict(path)
    return record


def _cascor_verdict(path: Path) -> Dict[str, Any]:
    """Ask cascor's OWN verifier, rather than reimplementing its policy here.

    Imported lazily so the default scan needs no cascor tree on ``sys.path`` --
    and so an unavailable cascor degrades to a recorded reason instead of
    failing the whole scan.
    """
    try:
        from snapshots.snapshot_serializer import CascadeHDF5Serializer
    except ImportError as exc:
        return {"available": False, "reason": f"cascor not importable ({exc}); run from <juniper-cascor>/src"}
    try:
        result = CascadeHDF5Serializer().verify_saved_network(str(path))
    except Exception as exc:  # noqa: BLE001 - report, never abort the scan
        return {"available": True, "valid": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"available": True, "valid": bool(result.get("valid")), "error": result.get("error")}


def read_index(index_path: Path) -> "list[dict]":
    """Load the index, skipping any line that is not a JSON object.

    A truncated final line (a scan killed mid-write) must cost that one record,
    not the whole index.
    """
    if not index_path.exists():
        return []
    rows = []
    for line in index_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def scan(root: Path, *, verify: bool = False, rebuild: bool = False, limit: Optional[int] = None) -> "tuple[int, int, int, Path]":
    """Index every snapshot under ``root`` that is not already indexed.

    Append-only by design (§6.2): a re-run adds records for new files and leaves
    existing ones alone, so the index can be built incrementally over a very
    large archive and re-run over the legacy corpus safely. ``--rebuild`` starts
    a fresh index instead.

    Returns (indexed_now, already_present, deferred_by_limit, index_path).

    ``already_present`` and ``deferred_by_limit`` are counted separately on
    purpose: folding the ``--limit`` remainder into "already present" reports a
    fresh archive as almost entirely indexed, which is the kind of number a
    reader trusts without re-deriving.
    """
    index_path = root / INDEX_NAME
    known = set()
    if not rebuild:
        known = {row.get("path") for row in read_index(index_path)}

    # ``iterdir`` rather than a glob: at ~28k entries a shell-style glob is both
    # slower and, in shell callers, silently truncated by ARG_MAX.
    files = sorted(p for p in root.iterdir() if p.suffix == ".h5" and p.is_file())
    pending = [p for p in files if str(p) not in known]
    already_present = len(files) - len(pending)
    todo = pending[:limit] if limit is not None else pending
    deferred = len(pending) - len(todo)

    mode = "w" if rebuild else "a"
    written = 0
    with index_path.open(mode, encoding="utf-8") as handle:
        for path in todo:
            handle.write(json.dumps(scan_one(path, verify=verify), sort_keys=True) + "\n")
            written += 1
            if written % 2000 == 0:
                print(f"  … {written}/{len(todo)}", file=sys.stderr)
    return written, already_present, deferred, index_path


def matches(row: dict, args: argparse.Namespace) -> bool:
    provenance = mapping(row.get("provenance"))
    if args.unattributed and provenance:
        return False
    if args.attributed and not provenance:
        return False
    for field in PROVENANCE_FIELDS:
        wanted = getattr(args, field, None)
        if not wanted:
            continue
        found = provenance.get(field)
        # ``dataset_id`` is normally DERIVED via the run_id join rather than stored
        # in the snapshot, so accept either source. The env pass-through remains a
        # manual escape hatch; the join is the path that actually populates it.
        if field == "dataset_id" and found is None:
            found = mapping(row.get("dataset")).get("dataset_id")
        if found != wanted:
            return False
    if args.tier and row.get("tier") != args.tier:
        return False
    if args.unreadable and row.get("readable"):
        return False
    return True


def summarise(rows: Iterable[dict]) -> Dict[str, Any]:
    rows = list(rows)
    attributed = [r for r in rows if r.get("provenance")]
    tiers: Dict[str, int] = {}
    experiments: Dict[str, int] = {}
    for row in rows:
        tiers[row.get("tier", "unknown")] = tiers.get(row.get("tier", "unknown"), 0) + 1
        experiment = mapping(row.get("provenance")).get("experiment")
        if experiment:
            experiments[experiment] = experiments.get(experiment, 0) + 1
    return {
        "total": len(rows),
        "readable": sum(1 for r in rows if r.get("readable")),
        "unreadable": sum(1 for r in rows if not r.get("readable")),
        "attributed": len(attributed),
        "unattributed": len(rows) - len(attributed),
        "bytes": sum(r.get("size_bytes", 0) for r in rows),
        "by_tier": dict(sorted(tiers.items())),
        "by_experiment": dict(sorted(experiments.items(), key=lambda kv: -kv[1])),
    }


def _print_rows(rows: "list[dict]", as_json: bool) -> None:
    if as_json:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return
    if not rows:
        print("(no matching snapshots)")
        return
    # Only widen the table when the join actually ran, so the default listing stays
    # narrow rather than carrying a column of dashes.
    show_dataset = any("dataset" in row for row in rows)
    header = f"{'name':<62} {'tier':<8} {'experiment':<24} {'cell_id':<18}"
    print(f"{header} {'dataset_id':<34} {'created':<26}" if show_dataset else f"{header} {'created':<26}")
    for row in rows:
        provenance = mapping(row.get("provenance"))
        line = f"{row.get('name', ''):<62} {row.get('tier', ''):<8} {str(provenance.get('experiment') or '-'):<24} {str(provenance.get('cell_id') or '-'):<18}"
        if show_dataset:
            dataset_id = mapping(row.get("dataset")).get("dataset_id") or provenance.get("dataset_id") or "-"
            line += f" {str(dataset_id):<34}"
        print(f"{line} {str(row.get('created') or '-'):<26}")


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description="Index and query a cascor snapshot archive (design §6.2). Read-only.")
    parser.add_argument("--root", type=Path, default=None, help=f"Snapshot root (default: ${DEFAULT_ROOT_ENV}, else {DEFAULT_ROOT_FALLBACK})")
    parser.add_argument("--scan", action="store_true", help="Index snapshots not already in the index (append-only)")
    parser.add_argument("--rebuild", action="store_true", help="With --scan: start a fresh index instead of appending")
    parser.add_argument("--verify", action="store_true", help="With --scan: also record cascor's own verification verdict (slower; needs the cascor tree importable)")
    parser.add_argument("--limit", type=int, default=None, help="Cap rows scanned or listed")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--stats", action="store_true", help="Summarise the index instead of listing rows")
    parser.add_argument("--tier", choices=("model", "service", "unknown"), default=None, help="Filter by writing tier")
    parser.add_argument("--attributed", action="store_true", help="Only snapshots carrying D-C provenance")
    parser.add_argument("--unattributed", action="store_true", help="Only snapshots with no provenance (the pre-D-C archive)")
    parser.add_argument("--unreadable", action="store_true", help="Only snapshots that could not be opened")
    parser.add_argument("--resolve-datasets", action="store_true", help="Join each snapshot's run_id to the run manifest to recover dataset_id (implied by --dataset-id)")
    parser.add_argument("--run-root", type=Path, default=None, help=f"Experiment run root for the dataset join (default: ${DEFAULT_RUN_ROOT_ENV}, else {DEFAULT_RUN_ROOT_FALLBACK})")
    for field in PROVENANCE_FIELDS:
        parser.add_argument(f"--{field.replace('_', '-')}", dest=field, default=None, help=f"Filter by provenance {field}")
    args = parser.parse_args(argv)

    if args.attributed and args.unattributed:
        print("ERROR: --attributed and --unattributed are mutually exclusive", file=sys.stderr)
        return 2
    root = args.root or default_root()
    if not root.is_dir():
        print(f"ERROR: snapshot root not found: {root}", file=sys.stderr)
        return 2

    if args.scan:
        written, already, deferred, index_path = scan(root, verify=args.verify, rebuild=args.rebuild, limit=args.limit)
        note = f"; {deferred} deferred by --limit" if deferred else ""
        print(f"indexed {written} new snapshot(s); {already} already present{note} -> {index_path}")
        return 0

    index_path = root / INDEX_NAME
    if not index_path.exists():
        print(f"ERROR: no index at {index_path} — run --scan first", file=sys.stderr)
        return 2
    rows = read_index(index_path)
    # Enrich BEFORE filtering, so --dataset-id can match a derived value.
    if args.resolve_datasets or args.dataset_id:
        run_root = args.run_root or default_run_root()
        cache: Dict[str, Any] = {}
        for row in rows:
            row["dataset"] = resolve_dataset(mapping(row.get("provenance")).get("run_id"), run_root, cache)
    rows = [row for row in rows if matches(row, args)]
    if args.stats:
        summary = summarise(rows)
        print(json.dumps(summary, indent=2) if args.json else "\n".join(f"{k:>16}: {v}" for k, v in summary.items()))
        return 0
    if args.limit is not None:
        rows = rows[: args.limit]
    _print_rows(rows, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
