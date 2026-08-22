#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   snapshots
# File Name:     snapshot_classify.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Read-only classifier for a cascor snapshot archive, implementing the owner's classification
#   scheme (handoff 2026-08-22 §2.4) on top of the §6.2 index. Staged, because the five categories
#   cost between one second and several CPU-days to decide. Writes only a derived sidecar; never
#   touches a .h5, never deletes anything.
#####################################################################################################################################################################################################
"""Classify a cascor snapshot archive into the owner's five categories.

Usage:
    python util/snapshot_classify.py --stats                     # index stage (~1s), population table
    python util/snapshot_classify.py --stage load --sample 300   # cost probe on a random sample
    python util/snapshot_classify.py --stage load --write        # full load pass, persist the sidecar
    python util/snapshot_classify.py --from-sidecar --category fails_to_load   # ~0.5s, stored verdicts
    python util/snapshot_classify.py --category fails_to_load --limit 20       # re-derives; index stage only

THE SCHEME (handoff 2026-08-22 §2.4)
    1. fails_to_load       — the loader refuses it
    2. fails_to_train      — loads with no hidden units, and cannot be trained
    3. formerly_broken     — loads with no hidden units, but CAN be trained
    4. loads_hidden_nodes  — loads carrying hidden units
    5. fully_attributed    — carries D-C provenance, so nothing needs reconstructing

WHY IT IS STAGED
    Only categories 4 and 5 are decidable from the index alone. 1 needs a real load
    (see below). 2 vs 3 needs an actual training run per network -- ~11.7k of them --
    which is item 3 of the handoff and is deliberately NOT implemented here.

    +---------+----------------------------+----------------------------------+
    | stage   | cost                       | resolves                         |
    +---------+----------------------------+----------------------------------+
    | index   | ~1s over the whole archive | 4, 5; narrows the rest           |
    | load    | measured, see --sample     | 1 authoritatively                |
    | train   | NOT IMPLEMENTED (item 3)   | 2 vs 3                           |
    +---------+----------------------------+----------------------------------+

WHY ``readable`` IS NOT CATEGORY 1
    The handoff's §3.1 says categories 1/4/5 are derivable from the index without
    opening a file, reading ``readable`` as "loads". It is not: ``readable`` is set by
    ``snapshot_index.scan_one`` and means only that **h5py opened the file**. The index
    reports all 27,908 as readable, while the forensics design measured ~130 files where
    ``load_network`` returns ``None`` and ~170 more that load with invalid shapes.

    This is the same trap the 2026-08-16 census fell into -- classifying structurally,
    without ever calling the loader -- and it is why "88/89 valid" was never a
    loadability figure. So category 1 here is decided by cascor's OWN loader, through
    ``load_network_result``, and reported in cascor's own taxonomy.

ITERATIONS, NOT EPOCHS (§2.1)
    ``meta.current_epoch`` is INERT: 0 across all 27,908 snapshots, including all 174
    snapshots of a network that grew to 260 hidden units. ``snapshot_counter`` is 0 and
    ``best_value_loss`` is inf. Three fields that look like training progress are dead,
    and reading them literally would say "nothing here was ever trained".

    The live measure is ``arch.num_hidden_units``, and it is a LOWER BOUND on completed
    cascor iterations: each installed hidden unit required one iteration that found a
    candidate clearing the correlation threshold, and an unknown number of iterations may
    have run without finding one. This tool therefore reports
    ``iterations_lower_bound`` and never an epoch count.

WHY THE SIDECAR IS REWRITTEN, NOT APPENDED
    ``snapshots_index.jsonl`` is append-only because it records OBSERVATIONS -- what was
    in the file when it was scanned. Classification is a DERIVED verdict that a deeper
    stage legitimately revises: a row that is ``undetermined`` after the index stage
    becomes ``loads_hidden_nodes`` after the load stage. Appending would leave two
    contradictory rows for one path and make the newest answer a matter of file order.
    So the sidecar is keyed by path and replaced atomically.

    ``--from-sidecar`` reads it back. Without that the tool could WRITE a verdict it could
    not READ: only the load stage can set ``fails_to_load``, so a later
    ``--category fails_to_load`` re-derived from the index and reported "no matching
    snapshots" against a sidecar holding 526 of them. A 14-minute pass whose answers are
    unqueryable afterwards is a pass nobody runs twice. Reading them back costs ~0.5s.

WHY THERE IS NO --prune
    Retention is design §6.4 and is gated on classification, which is what this tool
    produces. Acting on the verdict in the same tool that forms it would prejudge the
    owner's decision. This tool only reads snapshots. (The live hazard next door:
    ``snapshot_cli.py cleanup --keep N`` is count-based and mtime-ordered, and mtime in
    this archive is NOT creation time -- a copy reset them all.)

SAFETY
    Loading never writes a snapshot. Training would: ``train_output_layer`` calls
    ``create_snapshot()`` unconditionally, so any future train stage MUST set
    ``JUNIPER_CASCOR_SNAPSHOTS_DIR`` to a scratch dir or it will grow the archive it is
    measuring. That is enforced for the train stage in ``_require_scratch_root``.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

# Reuse the index's own root resolution and reader rather than a second copy free to
# drift from it -- the failure class this arc kept finding.
sys.path.insert(0, str(REPO_ROOT / "util"))
from snapshot_index import (  # noqa: E402  - path bootstrap must precede the import
    DEFAULT_ROOT_ENV,
    DEFAULT_ROOT_FALLBACK,
    INDEX_NAME,
    default_root,
    read_index,
)

SIDECAR_NAME = "snapshots_classification.jsonl"
SCHEMA_VERSION = 1

#: Cascor source tree, needed only by the load stage.
DEFAULT_CASCOR_SRC_ENV = "JUNIPER_CASCOR_SRC"
DEFAULT_CASCOR_SRC_FALLBACK = Path.home() / "Development" / "python" / "Juniper" / "juniper-cascor" / "src"

FAILS_TO_LOAD = "fails_to_load"
FAILS_TO_TRAIN = "fails_to_train"
FORMERLY_BROKEN = "formerly_broken"
LOADS_HIDDEN_NODES = "loads_hidden_nodes"
FULLY_ATTRIBUTED = "fully_attributed"
UNDETERMINED = "undetermined"

#: Owner's §2.4 categories, in the order a row is tested against them.
#:
#: RESOLVED AMBIGUITY -- read this before trusting the population table.
#:
#: The five categories as stated are not a partition, and the order they are listed in
#: is not a first-match-wins precedence. Taken literally as one, category 5 would be
#: unreachable: every attributed snapshot that loads with hidden units is caught by
#: category 4 first, and every attributed one without them by 2 or 3. Category 5 would
#: always be empty, which is plainly not what "snapshots generated going forward with
#: full metadata" means.
#:
#: So the scheme is TWO AXES, and this tool emits both:
#:
#:   * ``category`` -- do we need to reconstruct this snapshot's metadata? Attribution
#:     decides it, because for an attributed snapshot there is nothing left to infer.
#:   * ``health``   -- what can the artifact actually do? Load, train, grow.
#:
#: ``fails_to_load`` overrides attribution: a file that will not load needs a root cause
#: whatever metadata it carries, and calling it "fully attributed" would file a broken
#: artifact as finished work. Nothing else does.
#:
#: Consequence worth knowing: an attributed snapshot that turns out not to train is
#: reported as category 5 with ``health="zero_node"``. That is deliberate -- its identity
#: is known, its health is not -- and it is why health questions must be asked with
#: ``--health``, never with ``--category``.
CATEGORY_PRECEDENCE = (FAILS_TO_LOAD, FULLY_ATTRIBUTED, FAILS_TO_TRAIN, FORMERLY_BROKEN, LOADS_HIDDEN_NODES)

CATEGORIES = CATEGORY_PRECEDENCE + (UNDETERMINED,)

#: Health axis: what the artifact can do, independent of what metadata it carries.
HEALTH_FAILS_TO_LOAD = "fails_to_load"
HEALTH_ZERO_NODE = "zero_node"
HEALTH_HAS_HIDDEN = "has_hidden"
HEALTH_UNDETERMINED = "undetermined"

STAGES = ("index", "load", "train")


class ClassifierError(Exception):
    """An operator-facing refusal, raised from a helper and rendered once by ``main``.

    Every refusal must leave by the same door: one line on stderr, exit 2. Raising
    ``SystemExit(str)`` from a helper instead would exit 1 with the message printed by the
    interpreter, so the exit code would depend on which check tripped and an in-process
    caller would have to catch two different things.
    """


def default_cascor_src() -> Path:
    override = os.environ.get(DEFAULT_CASCOR_SRC_ENV, "").strip()
    return Path(override).expanduser() if override else DEFAULT_CASCOR_SRC_FALLBACK


def hidden_units(row: dict) -> Optional[int]:
    """The live training-duration signal: ``arch.num_hidden_units``.

    ``None`` when the file carries no ``arch`` group at all, which is itself a finding --
    8 files in the archive are in that state and are prime category-1 candidates.
    """
    value = (row.get("arch") or {}).get("num_hidden_units")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def assign_category(health: str, attributed: bool) -> str:
    """Map the two axes onto the owner's single ``category`` label.

    One place, so the index stage and the load stage cannot drift into disagreeing
    about the same row -- which they did in the first cut of this tool: attribution was
    consulted on the has-hidden path and silently ignored on the zero-node path, so the
    archive's only attributed snapshot (which has zero hidden units) reported as
    ``undetermined`` and category 5 came out empty.
    """
    if health == HEALTH_FAILS_TO_LOAD:
        return FAILS_TO_LOAD
    if health == HEALTH_UNDETERMINED:
        # Loadability is unresolved, and it is the one thing that overrides attribution.
        # Claiming category 5 here could file a broken file as finished work.
        return UNDETERMINED
    if attributed:
        return FULLY_ATTRIBUTED
    if health == HEALTH_HAS_HIDDEN:
        return LOADS_HIDDEN_NODES
    return UNDETERMINED  # zero-node and unattributed: category 2 vs 3 needs the train stage


def classify_index_stage(row: dict) -> Dict[str, Any]:
    """Everything decidable without opening the .h5 again.

    Deliberately conservative: a row with hidden units is only a *candidate* for
    category 4 until the loader confirms it, because the index's ``readable`` flag
    is an h5py fact rather than a load verdict. Rows that cannot be settled here are
    ``undetermined`` rather than being defaulted into a category that looks healthy.
    """
    units = hidden_units(row)
    attributed = bool(row.get("provenance"))
    verdict: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "path": row.get("path"),
        "name": row.get("name"),
        "stage": "index",
        "attributed": attributed,
        "iterations_lower_bound": units,
        "created": row.get("created"),
        "size_bytes": row.get("size_bytes"),
        "load": None,
        "train": None,
    }

    if units is None:
        # No arch group. Structurally incomplete; the loader decides whether it is
        # category 1, and it very likely is.
        verdict["health"] = HEALTH_UNDETERMINED
        verdict["reason"] = "no arch group in the index record; needs the load stage"
    elif units > 0:
        verdict["health"] = HEALTH_HAS_HIDDEN
        verdict["reason"] = f"arch.num_hidden_units={units} (>=1 completed cascor iteration each)"
    else:
        verdict["health"] = HEALTH_ZERO_NODE
        verdict["reason"] = "zero hidden units; category 2 vs 3 needs the train stage"
    verdict["category"] = assign_category(verdict["health"], attributed)
    return verdict


def apply_load_result(verdict: Dict[str, Any], status: str, detail: str, ok_status: str) -> Dict[str, Any]:
    """Fold a loader verdict into a row already classified at the index stage."""
    verdict["stage"] = "load"
    verdict["load"] = {"status": status, "detail": detail}
    units = verdict.get("iterations_lower_bound")

    if status != ok_status:
        verdict["health"] = HEALTH_FAILS_TO_LOAD
        verdict["reason"] = f"loader refused it: {status}"
    elif units is None:
        # Loaded despite the index seeing no arch group -- record the contradiction
        # rather than smoothing it, because it means one of the two readers is wrong.
        verdict["health"] = HEALTH_UNDETERMINED
        verdict["reason"] = "loads, but the index recorded no arch group; re-scan this file"
    elif units > 0:
        verdict["health"] = HEALTH_HAS_HIDDEN
        verdict["reason"] = f"loads with {units} hidden unit(s)"
    else:
        verdict["health"] = HEALTH_ZERO_NODE
        verdict["reason"] = "loads with zero hidden units; category 2 vs 3 needs the train stage"
    verdict["category"] = assign_category(verdict["health"], bool(verdict.get("attributed")))
    return verdict


@contextlib.contextmanager
def _muffle_stdout(enabled: bool):
    """Send everything written to fd 1 to /dev/null for the duration of the block.

    Not cosmetic. cascor logs every load to **stdout**, so a full pass puts ~119k lines
    into the same stream as ``--json`` and the output stops being parseable. Measured on
    a 300-file sample: 1,277 leaked lines.

    Two gentler fixes were tried first and both fail here:

      * ``logging.disable(logging.CRITICAL)`` is UNDONE mid-pass. Every ``load_network``
        constructs a network, whose ``Logger.__init__`` re-runs ``dictConfig``, which
        resets the global disable. It suppresses the first few files and then quietly
        stops working -- the worst failure mode, because it looks like it worked.
      * ``contextlib.redirect_stdout`` rebinds ``sys.stdout``, but a ``StreamHandler``
        built earlier holds the ORIGINAL stream object and keeps writing to it.

    Redirecting the file descriptor is below both of those, so no amount of logging
    reconfiguration can escape it. Progress and timings are written to stderr (fd 2) and
    are deliberately unaffected.
    """
    if not enabled:
        yield
        return
    sys.stdout.flush()
    saved_fd = os.dup(1)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull_fd, 1)
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved_fd, 1)
        os.close(devnull_fd)
        os.close(saved_fd)


def _load_seam(cascor_src: Path):
    """Import cascor's loader, or explain precisely why it could not be reached.

    Lazy and path-bootstrapped so the index stage needs no cascor tree at all, and so
    the load stage runs from any cwd rather than only from ``<juniper-cascor>/src``.
    """
    if not cascor_src.is_dir():
        raise ClassifierError(f"cascor source tree not found: {cascor_src}\n       set ${DEFAULT_CASCOR_SRC_ENV} or pass --cascor-src")
    if str(cascor_src) not in sys.path:
        sys.path.insert(0, str(cascor_src))
    try:
        from snapshots.snapshot_load_status import SNAPSHOT_OK
        from snapshots.snapshot_serializer import CascadeHDF5Serializer
    except ImportError as exc:
        raise ClassifierError(f"cascor not importable from {cascor_src}: {exc}\n       conda activate JuniperCascor1 (the unsuffixed env has broken torch)")
    return CascadeHDF5Serializer(), SNAPSHOT_OK


def run_load_stage(verdicts: List[Dict[str, Any]], cascor_src: Path, *, progress_every: int = 500, verbose: bool = False) -> Dict[str, Any]:
    """Ask cascor's own loader about each row, in cascor's own taxonomy.

    ``restore_multiprocessing=False`` because a classification pass must not stand up
    a worker pool per file; the flag governs restoring the training-time MP state, which
    nothing here uses.
    """
    serializer, ok_status = _load_seam(cascor_src)
    started = time.time()
    with _muffle_stdout(not verbose):
        for position, verdict in enumerate(verdicts, start=1):
            path = verdict.get("path")
            try:
                result = serializer.load_network_result(path, restore_multiprocessing=False)
                status, detail = result.status, (result.detail or "")
            except Exception as exc:  # noqa: BLE001 - a loader crash is a finding, not a reason to abort the pass
                status, detail = "loader_exception", f"{type(exc).__name__}: {exc}"
            apply_load_result(verdict, status, detail, ok_status)
            if progress_every and position % progress_every == 0:
                rate = position / max(time.time() - started, 1e-9)
                print(f"  … {position}/{len(verdicts)}  ({rate:.1f}/s)", file=sys.stderr)
    elapsed = time.time() - started
    return {
        "loaded": len(verdicts),
        "elapsed_s": round(elapsed, 2),
        "per_file_ms": round(elapsed / len(verdicts) * 1000, 2) if verdicts else 0.0,
    }


def _require_scratch_root() -> None:
    """Refuse a train stage that would grow the archive it is measuring.

    ``train_output_layer`` calls ``create_snapshot()`` unconditionally, so training
    against the default root writes new snapshots into the corpus under study. cascor#558
    stopped the test suite doing this; an ad-hoc probe still can.
    """
    configured = os.environ.get(DEFAULT_ROOT_ENV, "").strip()
    if not configured:
        raise ClassifierError(
            f"the train stage writes snapshots (train_output_layer calls create_snapshot\n"
            f"       unconditionally). Set ${DEFAULT_ROOT_ENV} to a scratch directory first, or it\n"
            f"       will grow the archive it is measuring."
        )
    if Path(configured).expanduser().resolve() == DEFAULT_ROOT_FALLBACK.resolve():
        raise ClassifierError(f"${DEFAULT_ROOT_ENV} points at the real archive ({configured}); use a scratch directory")


def failure_signature(detail: str) -> str:
    """Collapse a loader ``detail`` to the shape of the fault, dropping the specifics.

    The details name the offending file and its actual dimensions, so counting them raw
    yields one bucket per file and no signal. Paths and integers are the specifics;
    which check failed is the signature -- and the signature is what a root-cause pass
    (§3.4) needs, because it is what says how many DISTINCT faults are in the archive.
    """
    collapsed = re.sub(r"/\S+", "<path>", detail or "")
    collapsed = re.sub(r"\d+", "N", collapsed)
    return " ".join(collapsed.split())[:160] or "(no detail)"


def summarise(verdicts: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Population table, plus the iteration lower bounds the scheme actually cares about."""
    verdicts = list(verdicts)
    by_category: Dict[str, int] = {name: 0 for name in CATEGORIES}
    by_health: Dict[str, int] = {}
    by_stage: Dict[str, int] = {}
    by_load_status: Dict[str, int] = {}
    by_failure: Dict[str, int] = {}
    bounds: List[int] = []
    total_bytes = 0
    for verdict in verdicts:
        load = verdict.get("load") or {}
        if load:
            by_load_status[load.get("status", "?")] = by_load_status.get(load.get("status", "?"), 0) + 1
            if verdict.get("health") == HEALTH_FAILS_TO_LOAD:
                signature = failure_signature(load.get("detail", ""))
                by_failure[signature] = by_failure.get(signature, 0) + 1
        by_category[verdict.get("category", UNDETERMINED)] = by_category.get(verdict.get("category", UNDETERMINED), 0) + 1
        health = verdict.get("health", HEALTH_UNDETERMINED)
        by_health[health] = by_health.get(health, 0) + 1
        stage = verdict.get("stage", "index")
        by_stage[stage] = by_stage.get(stage, 0) + 1
        units = verdict.get("iterations_lower_bound")
        if isinstance(units, int):
            bounds.append(units)
        total_bytes += verdict.get("size_bytes") or 0
    grew = [b for b in bounds if b > 0]
    return {
        "total": len(verdicts),
        "bytes": total_bytes,
        "by_category": by_category,
        "by_health": dict(sorted(by_health.items())),
        "by_stage": dict(sorted(by_stage.items())),
        "by_load_status": dict(sorted(by_load_status.items(), key=lambda kv: -kv[1])),
        "load_failure_signatures": dict(sorted(by_failure.items(), key=lambda kv: -kv[1])),
        "iterations_lower_bound": {
            "measured": len(bounds),
            "zero": len(bounds) - len(grew),
            "at_least_one": len(grew),
            "max": max(bounds) if bounds else None,
            "sum_over_archive": sum(bounds),
        },
    }


def read_sidecar(root: Path) -> List[Dict[str, Any]]:
    """Load previously-written verdicts, skipping any line that is not a JSON object.

    Same tolerance as ``snapshot_index.read_index``: a run killed mid-write costs that
    one record, not the whole file.
    """
    sidecar = root / SIDECAR_NAME
    if not sidecar.exists():
        return []
    verdicts = []
    for line in sidecar.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            verdict = json.loads(line)
        except ValueError:
            continue
        if isinstance(verdict, dict):
            verdicts.append(verdict)
    return verdicts


def write_sidecar(root: Path, verdicts: List[Dict[str, Any]]) -> Path:
    """Replace the sidecar atomically, keyed by path.

    Whole-file replace rather than append: see the module docstring. The temp file is
    written beside the target so the rename cannot cross a filesystem boundary.
    """
    sidecar = root / SIDECAR_NAME
    staging = sidecar.with_suffix(".jsonl.tmp")
    with staging.open("w", encoding="utf-8") as handle:
        for verdict in verdicts:
            handle.write(json.dumps(verdict, sort_keys=True) + "\n")
    staging.replace(sidecar)
    return sidecar


def _print_rows(verdicts: List[Dict[str, Any]], as_json: bool) -> None:
    if as_json:
        print(json.dumps(verdicts, indent=2, sort_keys=True))
        return
    if not verdicts:
        print("(no matching snapshots)")
        return
    print(f"{'name':<62} {'category':<20} {'health':<16} {'iters>=':<8} {'reason'}")
    for verdict in verdicts:
        units = verdict.get("iterations_lower_bound")
        print(f"{str(verdict.get('name', '')):<62} {str(verdict.get('category', '')):<20} {str(verdict.get('health', '')):<16} {str(units if units is not None else '-'):<8} {verdict.get('reason', '')}")


def _report(verdicts: List[Dict[str, Any]], args: argparse.Namespace) -> int:
    """Filter, then either summarise or list. Shared by the derive path and --from-sidecar
    so a stored verdict and a freshly-computed one are reported identically."""
    selected = verdicts
    if args.category:
        selected = [v for v in selected if v.get("category") == args.category]
    if args.health:
        selected = [v for v in selected if v.get("health") == args.health]

    if args.stats:
        print(json.dumps(summarise(selected), indent=2))
        return 0

    if args.limit is not None:
        selected = selected[: args.limit]
    _print_rows(selected, args.json)
    return 0


def main(argv: "list[str] | None" = None) -> int:
    """Render every operator refusal the same way: one stderr line, exit 2."""
    try:
        return _dispatch(argv)
    except ClassifierError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _dispatch(argv: "list[str] | None" = None) -> int:  # noqa: C901 - a CLI dispatch, flat by design
    parser = argparse.ArgumentParser(description="Classify a cascor snapshot archive into the owner's five categories (handoff §2.4). Read-only.")
    parser.add_argument("--root", type=Path, default=None, help=f"Snapshot root (default: ${DEFAULT_ROOT_ENV}, else {DEFAULT_ROOT_FALLBACK})")
    parser.add_argument("--stage", choices=STAGES, default="index", help="How deep to classify (default: index)")
    parser.add_argument("--cascor-src", type=Path, default=None, help=f"Cascor source tree for the load stage (default: ${DEFAULT_CASCOR_SRC_ENV}, else {DEFAULT_CASCOR_SRC_FALLBACK})")
    parser.add_argument("--from-sidecar", action="store_true", help=f"Query the verdicts already in {SIDECAR_NAME} instead of re-deriving them (instant; keeps the load stage's answers)")
    parser.add_argument("--sample", type=int, default=None, help="Classify a random sample of N rows instead of the whole archive (cost probe)")
    parser.add_argument("--seed", type=int, default=20260822, help="Sample seed, so a probe is repeatable")
    parser.add_argument("--write", action="store_true", help=f"Persist the verdicts to {SIDECAR_NAME} in the snapshot root")
    parser.add_argument("--stats", action="store_true", help="Print the population table instead of listing rows")
    parser.add_argument("--category", choices=CATEGORIES, default=None, help="List only rows in this category")
    parser.add_argument("--health", choices=(HEALTH_FAILS_TO_LOAD, HEALTH_ZERO_NODE, HEALTH_HAS_HIDDEN, HEALTH_UNDETERMINED), default=None, help="List only rows with this health verdict")
    parser.add_argument("--limit", type=int, default=None, help="Cap rows listed")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--verbose", action="store_true", help="Let cascor's own logging through (two stdout lines per file; breaks --json)")
    args = parser.parse_args(argv)

    root = args.root or default_root()
    if not root.is_dir():
        print(f"ERROR: snapshot root not found: {root}", file=sys.stderr)
        return 2

    if args.from_sidecar:
        # Read back what a previous run decided. Without this the tool could WRITE a
        # verdict it could not READ: `--category fails_to_load` re-derived from the index
        # and reported "no matching snapshots" against a sidecar holding 526 of them,
        # because only the load stage can set that category. A 14-minute pass whose
        # answers are unqueryable afterwards is a pass nobody runs twice.
        if args.stage != "index":
            print("ERROR: --from-sidecar reads stored verdicts; it cannot be combined with --stage", file=sys.stderr)
            return 2
        if args.write:
            print("ERROR: --from-sidecar with --write would rewrite the sidecar from itself", file=sys.stderr)
            return 2
        verdicts = read_sidecar(root)
        if not verdicts:
            print(f"ERROR: no verdicts at {root / SIDECAR_NAME} — run '--stage load --write' first", file=sys.stderr)
            return 2
        return _report(verdicts, args)

    index_path = root / INDEX_NAME
    if not index_path.exists():
        print(f"ERROR: no index at {index_path} — run 'python util/snapshot_index.py --scan' first", file=sys.stderr)
        return 2

    rows = read_index(index_path)
    if not rows:
        print(f"ERROR: index at {index_path} holds no usable records", file=sys.stderr)
        return 2

    if args.sample is not None:
        if args.sample < 1:
            print("ERROR: --sample must be >= 1", file=sys.stderr)
            return 2
        # Sample the INDEX, not the classified rows: a sample drawn after classification
        # would report a population fraction of whatever the filter already selected.
        rows = random.Random(args.seed).sample(rows, min(args.sample, len(rows)))

    verdicts = [classify_index_stage(row) for row in rows]

    if args.stage == "train":
        _require_scratch_root()
        print(
            "ERROR: the train stage is not implemented (handoff item 3).\n"
            "       It separates category 2 (fails_to_train) from 3 (formerly_broken) by loading each\n"
            "       zero-node snapshot and running standard training, and it is the expensive step:\n"
            f"       {sum(1 for v in verdicts if v.get('health') == HEALTH_ZERO_NODE)} rows in this selection are zero-node.\n"
            "       Design it against measured per-network cost, not an estimate.",
            file=sys.stderr,
        )
        return 2

    if args.stage == "load":
        timing = run_load_stage(verdicts, args.cascor_src or default_cascor_src(), verbose=args.verbose)
        print(f"load stage: {timing['loaded']} file(s) in {timing['elapsed_s']}s ({timing['per_file_ms']} ms/file)", file=sys.stderr)
        if args.sample is not None:
            projected = timing["per_file_ms"] * len(read_index(index_path)) / 1000 / 60
            print(f"            full-archive projection: {projected:.1f} min", file=sys.stderr)

    if args.write:
        if args.sample is not None:
            print("ERROR: refusing to --write a sampled classification; it would replace the sidecar with a partial one", file=sys.stderr)
            return 2
        sidecar = write_sidecar(root, verdicts)
        print(f"wrote {len(verdicts)} verdict(s) -> {sidecar}", file=sys.stderr)

    return _report(verdicts, args)


if __name__ == "__main__":
    raise SystemExit(main())
