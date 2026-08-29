#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   snapshots
# File Name:     snapshot_backfill.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Consolidate everything recovered about each snapshot into one record (handoff §3.4,
#   "backfill"), with EVERY field labelled by how it was obtained. Writes a derived sidecar
#   beside the index; never writes into a .h5, because snapshots are read-only project assets.
#####################################################################################################################################################################################################
"""Assemble the recovered metadata, and make its provenance impossible to miss.

Usage:
    python util/snapshot_backfill.py --stats
    python util/snapshot_backfill.py --write
    python util/snapshot_backfill.py --explain cascor_snapshot_20260707_183654_295a396f-….h5
    python util/snapshot_backfill.py --from-sidecar --derivation inferred --limit 20

THE OWNER'S INSTRUCTION (§3.4)
    "backfilling metadata would tend to increase the research value of snapshots. caveating
    backfilled snapshots with a clear and visible label capturing the approximate, inferred,
    or recreated nature of their metadata would be a potentially important caution against
    naive reasoning. [...] using the index rather than write into the snapshots also seems
    like an option worth investigating."

    Both halves are implemented literally: the record goes beside the index, never into the
    file, and no recovered value is expressible without its label.

WHY A FOUR-LEVEL TAXONOMY AND NOT A CONFIDENCE SCORE
    A single number invites averaging things that must not be averaged. These four differ in
    KIND, not degree:

      observed    Read straight out of the .h5. ``arch.num_hidden_units``, ``created``,
                  ``uuid``. If the file says it, this says it.
      measured    Obtained by RUNNING the artifact through cascor -- load status, per-dataset
                  accuracy. Reproducible, and specific to this snapshot.
      inferred    A judgement made FROM measurements. Dataset attribution: "behaves like a
                  network trained on X". Strong, never definitive.
      population  A claim about the COHORT that was never verified for THIS snapshot.

    The last level is the one that matters, and it is why a score would have been wrong.
    Item 3 established that the zero-node cohort trains -- from **380 samples out of 15,927**.
    Writing ``formerly_broken`` onto every one of them as though it were a fact would fabricate
    a per-snapshot result for 15,547 files nobody ever trained. That is precisely the "naive
    reasoning" the caveat exists to prevent, and a 0.99-confidence field would have licensed it.

    So a population claim is stored in its own bucket, carrying the sample size and an explicit
    statement that it was not verified here.

WHAT IS AND IS NOT RECOVERABLE
    Recovered:      architecture, creation time, uuid, loadability + failure reason, root cause
                    for every failing file, hidden-unit count (a LOWER BOUND on completed
                    cascor iterations, never an epoch count -- ``meta.current_epoch`` is inert
                    at 0 across all 27,908), per-dataset accuracy, and dataset attribution
                    where the evidence clears an untrained-network null.
    NOT recovered:  run identity. There are ZERO surviving experiment run dirs before
                    2026-07-30 and the cohort is March-April, so ``run_id`` / ``experiment`` /
                    ``cell_id`` are gone. This tool never invents them; absence stays absence.

NO --prune, and nothing is written into any .h5. Retention is design §6.4; this produces the
evidence that decision needs and performs none of it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))
from snapshot_index import DEFAULT_ROOT_ENV, DEFAULT_ROOT_FALLBACK, INDEX_NAME, default_root, read_index  # noqa: E402

CLASSIFICATION_NAME = "snapshots_classification.jsonl"
ATTRIBUTION_NAME = "snapshots_attribution.jsonl"
SIDECAR_NAME = "snapshots_backfill.jsonl"
SCHEMA_VERSION = 1

OBSERVED = "observed"
MEASURED = "measured"
INFERRED = "inferred"
POPULATION = "population"
DERIVATIONS = (OBSERVED, MEASURED, INFERRED, POPULATION)

#: Item 3's sampled result. Stored as a POPULATION claim, never as a per-snapshot fact.
#: 380 of 15,927 zero-node snapshots were trained; all 380 trained successfully. By the rule
#: of three, 0/380 puts the 95% upper bound on the dysfunctional rate at ~0.8%.
TRAINABILITY_SAMPLE = {"tested": 380, "succeeded": 380, "cohort": 15927, "upper_bound_95": 0.008}

#: Load-failure signature -> root cause, from the four-root-cause decomposition
#: (JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_SNAPSHOT-CLASSIFICATION-STAGE-1-FINDINGS.md).
#: A and C were FIXED (juniper-cascor#560 / #559) and no longer appear; only B's truncated
#: writes still fail, and their loss is irrecoverable.
ROOT_CAUSES = (
    ("Missing required group: random", "B", "truncated write -- died inside _save_hidden_units; hidden-unit tensors are lost and unrecoverable"),
    ("Missing required group: params", "B", "truncated write -- died after the config group"),
    # These two are the SAME condition under two spellings. juniper-cascor#575 split an ABSENT
    # ``format`` attribute out of the present-but-wrong branch, because rendering the absence
    # produced "Invalid format: None" -- a message naming a format that does not exist. The
    # loader's wording is an undeclared contract with this table: when it changed, these six
    # files silently stopped matching and lost their root cause (backfill coverage fell 273 ->
    # 267) while every other count stayed right. Both spellings are kept so a pre-#575 sidecar
    # still classifies.
    ("Missing required attribute: format", "B", "truncated write -- died before the root attributes; the file is an empty HDF5 container"),
    ("Invalid format", "B", "truncated write -- died before the root attributes; the file is an empty HDF5 container (pre-juniper-cascor#575 spelling)"),
    ("output_size disagrees", "A", "stale config_json after a live dataset resize (FIXED in juniper-cascor#560; recoverable)"),
    ("could not be deserialized", "C", "config schema drift -- carries a field this version removed (FIXED in juniper-cascor#559; recoverable)"),
)


def classify_root_cause(detail: str) -> Optional[Dict[str, str]]:
    """Name WHY a snapshot fails to load, in the arc's own four-cause vocabulary."""
    for signature, cohort, explanation in ROOT_CAUSES:
        if signature in (detail or ""):
            return {"cohort": cohort, "explanation": explanation}
    return None


def read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
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


def build_record(index_row: dict, classification: Optional[dict], attribution: Optional[dict]) -> dict:
    """Merge one snapshot's evidence, tagging every field with how it was obtained."""
    arch = index_row.get("arch") or {}
    record: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "path": index_row.get("path"),
        "name": index_row.get("name"),
        OBSERVED: {},
        MEASURED: {},
        INFERRED: {},
        POPULATION: {},
    }

    # --- observed: straight out of the file -------------------------------------------------
    for field in ("created", "uuid", "juniper_version", "format_version", "size_bytes", "tier"):
        if index_row.get(field) is not None:
            record[OBSERVED][field] = index_row[field]
    if arch:
        record[OBSERVED]["arch"] = arch
    if index_row.get("groups"):
        record[OBSERVED]["groups"] = index_row["groups"]
    # D-C provenance is the ONLY authoritative identity, and it exists for exactly one
    # snapshot. Absence is recorded as absence -- never reconstructed, because there are no
    # surviving run dirs before 2026-07-30 to reconstruct it from.
    record[OBSERVED]["provenance"] = index_row.get("provenance")

    # --- measured: obtained by running the artifact ------------------------------------------
    if classification:
        load = classification.get("load") or {}
        if load:
            record[MEASURED]["load_status"] = load.get("status")
            if load.get("status") != "ok" and load.get("detail"):
                record[MEASURED]["load_failure"] = load["detail"]
                cause = classify_root_cause(load["detail"])
                if cause:
                    record[MEASURED]["root_cause"] = cause
        if classification.get("health"):
            record[MEASURED]["health"] = classification["health"]
        if classification.get("category"):
            record[MEASURED]["category"] = classification["category"]
        units = classification.get("iterations_lower_bound")
        if units is not None:
            # Named for what it is. Hidden-unit count is a LOWER BOUND on completed cascor
            # iterations -- each installed unit required one iteration that cleared the
            # correlation threshold, and an unknown number of iterations found nothing.
            # meta.current_epoch is inert (0 across all 27,908) and is never used.
            record[MEASURED]["iterations_lower_bound"] = units
    if attribution and attribution.get("scores"):
        record[MEASURED]["dataset_accuracy"] = attribution["scores"]

    # --- inferred: a judgement made from the measurements ------------------------------------
    if attribution and attribution.get("verdict") == "attributed" and attribution.get("dataset"):
        record[INFERRED]["dataset"] = {
            "value": attribution["dataset"],
            "confidence": "strong, not definitive",
            "meaning": "this network BEHAVES like one trained on that dataset; it is evidence, not provenance",
            "evidence": attribution.get("reason"),
            "lift_over_untrained_floor": attribution.get("lift"),
            "separation_from_runner_up": attribution.get("gap"),
            "caveat": "attribution is to a dataset FAMILY at generator defaults, not to a specific instance or parameterisation",
        }

    # --- population: true of the cohort, NOT verified for this snapshot ----------------------
    if classification and classification.get("health") == "zero_node":
        record[POPULATION]["trainability"] = {
            "value": "formerly_broken",
            "meaning": "loads with no hidden units but CAN be trained (handoff category 3)",
            "basis": f"{TRAINABILITY_SAMPLE['succeeded']}/{TRAINABILITY_SAMPLE['tested']} of a random sample trained successfully; 0 failures",
            "not_verified_here": True,
            "cohort_size": TRAINABILITY_SAMPLE["cohort"],
            "upper_bound_95_dysfunctional_rate": TRAINABILITY_SAMPLE["upper_bound_95"],
            "caveat": "a POPULATION claim. This snapshot was almost certainly never trained; do not cite it as a per-snapshot result",
        }

    record["derivation_summary"] = {level: sorted(record[level].keys()) for level in DERIVATIONS}
    return record


def summarise(records: Iterable[dict]) -> Dict[str, Any]:
    records = list(records)
    coverage: Dict[str, Dict[str, int]] = {level: {} for level in DERIVATIONS}
    for record in records:
        for level in DERIVATIONS:
            for field in record.get(level, {}):
                if record[level][field] is None:
                    continue
                coverage[level][field] = coverage[level].get(field, 0) + 1
    root_causes: Dict[str, int] = {}
    for record in records:
        cause = (record.get(MEASURED, {}).get("root_cause") or {}).get("cohort")
        if cause:
            root_causes[cause] = root_causes.get(cause, 0) + 1
    return {
        "total": len(records),
        "field_coverage": {level: dict(sorted(fields.items(), key=lambda kv: -kv[1])) for level, fields in coverage.items()},
        "root_causes": dict(sorted(root_causes.items())),
        "identity_recovered": sum(1 for r in records if r.get(OBSERVED, {}).get("provenance")),
        "identity_unrecoverable": sum(1 for r in records if not r.get(OBSERVED, {}).get("provenance")),
    }


def write_sidecar(root: Path, records: List[dict]) -> Path:
    sidecar = root / SIDECAR_NAME
    staging = sidecar.with_suffix(".jsonl.tmp")
    with staging.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    staging.replace(sidecar)
    return sidecar


def explain(record: dict) -> str:
    """Human-readable provenance for one snapshot -- the caveat made unmissable."""
    lines = [f"{record.get('name')}", "=" * len(str(record.get("name"))), ""]
    labels = {
        OBSERVED: "OBSERVED — read directly from the file",
        MEASURED: "MEASURED — obtained by running this snapshot through cascor",
        INFERRED: "INFERRED — a judgement from those measurements; evidence, not provenance",
        POPULATION: "POPULATION — true of the cohort, NOT verified for this snapshot",
    }
    for level in DERIVATIONS:
        fields = record.get(level) or {}
        present = {k: v for k, v in fields.items() if v is not None}
        lines.append(labels[level])
        if not present:
            lines.append("    (nothing at this level)")
        for key, value in sorted(present.items()):
            lines.append(f"    {key}: {json.dumps(value, sort_keys=True)}")
        lines.append("")
    if not (record.get(OBSERVED) or {}).get("provenance"):
        lines.append("IDENTITY: UNRECOVERABLE. No D-C provenance, and no experiment run dir survives")
        lines.append("          from before 2026-07-30 to reconstruct it from. Absence is absence.")
    return "\n".join(lines)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description="Consolidate recovered snapshot metadata, labelled by derivation (handoff §3.4). Read-only.")
    parser.add_argument("--root", type=Path, default=None, help=f"Snapshot root (default: ${DEFAULT_ROOT_ENV}, else {DEFAULT_ROOT_FALLBACK})")
    parser.add_argument("--write", action="store_true", help=f"Persist the consolidated record to {SIDECAR_NAME}")
    parser.add_argument("--from-sidecar", action="store_true", help="Read the stored record instead of rebuilding")
    parser.add_argument("--explain", default=None, metavar="NAME", help="Print one snapshot's full provenance and stop")
    parser.add_argument("--derivation", choices=DERIVATIONS, default=None, help="List only snapshots carrying a field at this level")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = args.root or default_root()
    if not root.is_dir():
        print(f"ERROR: snapshot root not found: {root}", file=sys.stderr)
        return 2

    if args.from_sidecar:
        records = read_jsonl(root / SIDECAR_NAME)
        if not records:
            print(f"ERROR: no record at {root / SIDECAR_NAME} — run with --write first", file=sys.stderr)
            return 2
    else:
        index_rows = read_index(root / INDEX_NAME)
        if not index_rows:
            print(f"ERROR: no index at {root / INDEX_NAME} — run util/snapshot_index.py --scan first", file=sys.stderr)
            return 2
        classification = {row.get("path"): row for row in read_jsonl(root / CLASSIFICATION_NAME)}
        attribution = {row.get("path"): row for row in read_jsonl(root / ATTRIBUTION_NAME)}
        if not classification:
            print(f"WARNING: no classification at {root / CLASSIFICATION_NAME}; measured fields will be absent", file=sys.stderr)
        if not attribution:
            print(f"WARNING: no attribution at {root / ATTRIBUTION_NAME}; inferred fields will be absent", file=sys.stderr)
        records = [build_record(row, classification.get(row.get("path")), attribution.get(row.get("path"))) for row in index_rows]

    if args.explain:
        matches = [r for r in records if args.explain in str(r.get("name", "")) or args.explain == r.get("path")]
        if not matches:
            print(f"ERROR: no snapshot matching {args.explain!r}", file=sys.stderr)
            return 2
        print(explain(matches[0]))
        return 0

    if args.write:
        print(f"wrote {len(records)} record(s) -> {write_sidecar(root, records)}", file=sys.stderr)

    selected = records
    if args.derivation:
        selected = [r for r in selected if any(v is not None for v in (r.get(args.derivation) or {}).values())]

    if args.stats:
        print(json.dumps(summarise(selected), indent=2))
        return 0
    if args.limit is not None:
        selected = selected[: args.limit]
    if args.json:
        print(json.dumps(selected, indent=2, sort_keys=True))
        return 0
    if not selected:
        print("(no matching snapshots)")
        return 0
    print(f"{'name':<58} {'obs':>4} {'meas':>5} {'infer':>6} {'pop':>4}  dataset")
    for record in selected:
        counts = [sum(1 for v in (record.get(level) or {}).values() if v is not None) for level in DERIVATIONS]
        dataset = (record.get(INFERRED, {}).get("dataset") or {}).get("value") or "-"
        print(f"{str(record.get('name', ''))[:58]:<58} {counts[0]:>4} {counts[1]:>5} {counts[2]:>6} {counts[3]:>4}  {dataset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
