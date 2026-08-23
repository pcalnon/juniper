#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   snapshots
# File Name:     snapshot_attribute.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Read-only dataset attribution for a cascor snapshot archive (handoff 2026-08-22 §3.2).
#   Scores each loadable snapshot against every shape-compatible cascor dataset and reports
#   which one it was plausibly trained on -- gated against an untrained-network null, because
#   "beats chance" is NOT evidence here. Writes only a derived sidecar; never touches a .h5.
#####################################################################################################################################################################################################
"""Infer which dataset a snapshot was trained on, or honestly say we cannot tell.

Usage:
    python util/snapshot_attribute.py --null-only            # show the per-dataset floors
    python util/snapshot_attribute.py --sample 200 --stats   # cost/behaviour probe
    python util/snapshot_attribute.py --write --stats        # full pass, persist the sidecar
    python util/snapshot_attribute.py --from-sidecar --verdict attributed

THE OWNER'S DESIGN, AND THE TWO CORRECTIONS MEASUREMENT FORCED ON IT
    §3.2: "since inference is computationally cheap, network accuracy per dataset can be
    calculated for all cascor, 2-in -> 2-out datasets. getting a better than random accuracy
    for a dataset is a strong--but not definitive--indicator that the network trained on that
    dataset [...] select the dataset associated with the largest increase in accuracy over
    chance."

    The shape of that is right and it is what this implements. Two things had to change, both
    because an experiment said so rather than because they read better:

    1. RAW ACCURACY IS THE WRONG MEASURE. One-hot column order is an arbitrary convention of
       whichever generator run produced the training data, so a network that learned a dataset
       with its columns swapped scores ``1 - p`` -- reading as far BELOW chance, i.e. as "did
       not learn this", which is exactly backwards. Measured: archive snapshots scoring
       **0.010 / 0.030** on gaussian are 0.990 / 0.970 with the labels inverted. Correcting to
       a permutation-invariant score moved decisive picks from 6/14 to 12/14 and changed most
       winners.

    2. "BETTER THAN CHANCE" IS NOT THE RIGHT BAR -- AN UNTRAINED NETWORK ALREADY CLEARS IT.
       A freshly-initialised, never-trained network beats chance on ``gaussian`` by **+0.408
       on average, up to +0.500 (perfect)**, because gaussian blobs are linearly separable and
       a random linear boundary separates them. 11 of 12 untrained networks "pick" gaussian.
       Permutation-correction makes this worse, not better.

       So the bar is not chance, it is **the untrained-network null for that dataset**. This
       module builds that null and refuses to attribute below it.

WHY THIS IS NOT OVER-CAUTION
    Applied to the archive's best-grown snapshots, the null is what separates a real answer
    from a confident wrong one:

        network 295a396f  (18 -> 103 hidden units)  xor 0.945 -> 0.995, floor 0.690  ATTRIBUTED
        network 17de4973  (125 -> 256 hidden)       gaussian 0.970-0.990, floor 1.000  REJECTED
        network 4e96c5b7  (35 -> 38 hidden)         moon 0.830-0.865,     floor 0.885  REJECTED

    The 17de4973 family has up to 256 hidden units and enormous gaussian margins. Without the
    null it would be confidently attributed to gaussian; with it, it is correctly indeterminate.

    ``gaussian`` is effectively unattributable for this reason -- its floor is 1.000, so no
    score can distinguish a trained network from a random one. It is scored and reported, but
    it can never be an ANSWER.

    3. THE FLOOR IS THE NULL'S OBSERVED MAXIMUM, NOT ITS p95. The first full pass used p95 and
       attributed **327 snapshots to checkerboard at a median lift of +0.059 -- with a median
       hidden-unit count of ZERO**. A zero-hidden-unit network is a linear model and cannot
       learn checkerboard; those scores sat between checkerboard's p95 (0.565) and its observed
       untrained max (0.610), i.e. inside the null's uncharacterised tail. Switching the floor
       to the max removed all 327 and left the xor cluster (+0.235 median lift) untouched.

KNOWN LIMITATION -- THE NULL IS NOT CAPACITY-MATCHED
    The null is built from freshly-constructed networks, which have ZERO hidden units. That is
    correctly matched for the archive's zero-node majority, but it is **too lenient for grown
    networks**: a random 58-unit network has more capacity to fit anything by chance than a
    0-unit one, so the true floor for those should be higher than the one used here.

    The xor cluster survives this on independent grounds -- its scores rise monotonically
    (0.945 -> 0.995) as the network grows 18 -> 103 units, and a capacity artifact does not
    produce a learning curve. Thinner results (spiral at +0.062, moon at +0.085) do NOT have
    that corroboration and should be read as provisional. A capacity-matched null is the
    rigorous fix and is not implemented.

VALIDATED BY A POSITIVE CONTROL
    Networks trained here on a known dataset and then attributed: **4/4 correct** (xor,
    gaussian, circles, moon; spiral and checkerboard were excluded because training did not
    take at the control's budget -- 8 hidden units still scored 0.510 on spiral). The method
    works when the network actually learned; it is the archive that is mostly under-trained,
    median 3 hidden units.

WHAT A VERDICT MEANS
    attributed    -- one dataset clears its null floor and is separated from the runner-up.
                     Strong, NOT definitive: it means "this network behaves like one trained
                     on X", which is evidence, not provenance.
    indeterminate -- nothing clears its floor. The expected answer for most of the archive,
                     and an honest one: under-trained networks carry no signature.
    ambiguous     -- something clears its floor but the runner-up is too close to separate.

NO --prune. Retention is design §6.4 and is gated on evidence like this, not performed by it.
"""

from __future__ import annotations

import argparse
import contextlib
import itertools
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))
from snapshot_index import DEFAULT_ROOT_ENV, DEFAULT_ROOT_FALLBACK, default_root  # noqa: E402

SIDECAR_NAME = "snapshots_attribution.jsonl"
CLASSIFICATION_NAME = "snapshots_classification.jsonl"
SCHEMA_VERSION = 1

DEFAULT_CASCOR_SRC_ENV = "JUNIPER_CASCOR_SRC"
DEFAULT_CASCOR_SRC_FALLBACK = Path.home() / "Development" / "python" / "Juniper" / "juniper-cascor" / "src"
DEFAULT_DATA_ROOT_ENV = "JUNIPER_DATA_ROOT"
DEFAULT_DATA_ROOT_FALLBACK = Path.home() / "Development" / "python" / "Juniper" / "juniper-data"

#: The 2-D classification family from juniper-data's GENERATOR_REGISTRY. Deliberately excludes
#: csv_import (arbitrary shape), equities / equities_seq, the four regression synthetics
#: (multi_sine / mackey_glass / ar_p / irregular_sine), mnist (784->10) and arc_agi.
GENERATORS = ("spiral", "xor", "gaussian", "circles", "moon", "checkerboard")

ATTRIBUTED = "attributed"
INDETERMINATE = "indeterminate"
AMBIGUOUS = "ambiguous"
VERDICTS = (ATTRIBUTED, AMBIGUOUS, INDETERMINATE)

#: How far above the null's OBSERVED MAXIMUM a score must sit before it counts (see
#: ``adjudicate._floor`` for why the max rather than p95). Headroom on top of the strictest
#: thing an untrained network actually achieved, so a marginal snapshot is called
#: indeterminate rather than attributed.
DEFAULT_MARGIN = 0.05
#: How far the winner must sit above the runner-up. Without this, a network that behaves like
#: several of these datasets at once gets a confident answer it has not earned.
DEFAULT_GAP = 0.05


@contextlib.contextmanager
def _muffle_stdout(enabled: bool):
    """Send fd 1 to /dev/null for the duration.

    cascor logs every load to **stdout**, and ``logging.disable`` does not hold -- each load
    re-runs ``dictConfig`` and resets it, so it suppresses the first few files and then
    silently stops. Redirecting the file descriptor sits below the logging layer entirely.
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


def default_cascor_src() -> Path:
    override = os.environ.get(DEFAULT_CASCOR_SRC_ENV, "").strip()
    return Path(override).expanduser() if override else DEFAULT_CASCOR_SRC_FALLBACK


def default_data_root() -> Path:
    override = os.environ.get(DEFAULT_DATA_ROOT_ENV, "").strip()
    return Path(override).expanduser() if override else DEFAULT_DATA_ROOT_FALLBACK


def permutation_corrected_accuracy(predicted, labels, n_classes: int) -> float:
    """Best accuracy over any relabelling of the classes.

    Class-index order is a convention of the training run, not a property of the dataset, so a
    network that learned the structure with permuted columns must not be scored as though it
    learned nothing. For two classes this is ``max(p, 1 - p)``; the general form is the max
    over all permutations, which is why ``n_classes`` is capped below.
    """
    best = 0.0
    for permutation in itertools.permutations(range(n_classes)):
        mapped = [permutation[int(value)] for value in predicted]
        matched = sum(1 for a, b in zip(mapped, labels) if a == int(b))
        best = max(best, matched / len(labels))
    return best


def percentile(values: List[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = q / 100.0 * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def load_datasets(data_root: Path, max_classes: int = 4) -> Dict[str, Dict[str, Any]]:
    """Generate one canonical instance of each 2-D classification generator.

    Uses each generator's declared defaults. Attribution therefore lands on a dataset FAMILY,
    not a specific instance -- a network trained on ``spiral(noise=0.1)`` is being compared
    against ``spiral(<defaults>)``. That is a real limitation and it is why a miss is reported
    as ``indeterminate`` rather than as evidence of absence.
    """
    if not data_root.is_dir():
        raise SystemExit(f"ERROR: juniper-data tree not found: {data_root}\n       set ${DEFAULT_DATA_ROOT_ENV} or pass --data-root")
    sys.path.insert(0, str(data_root))
    import numpy as np

    datasets: Dict[str, Dict[str, Any]] = {}
    for name in GENERATORS:
        try:
            module = __import__(f"juniper_data.generators.{name}", fromlist=["x"])
            generator = getattr(module, f"{name.capitalize()}Generator", None) or getattr(module, f"{name.title()}Generator")
            params_cls = getattr(module, f"{name.capitalize()}Params", None) or getattr(module, f"{name.title()}Params")
            produced = generator.generate(params_cls())
        except Exception as exc:  # noqa: BLE001 - a generator that will not build is a recorded gap, not a crash
            print(f"WARNING: generator {name!r} unavailable ({type(exc).__name__}: {exc}); excluded", file=sys.stderr)
            continue
        X, y = produced["X_full"], produced["y_full"]
        n_classes = int(y.shape[1])
        if n_classes > max_classes:
            print(f"WARNING: generator {name!r} has {n_classes} classes; excluded (permutation search would be {n_classes}!)", file=sys.stderr)
            continue
        labels = np.argmax(y, axis=1)
        datasets[name] = {
            "X": X,
            "labels": labels,
            "input_size": int(X.shape[1]),
            "output_size": n_classes,
            "n": int(len(labels)),
        }
    return datasets


def build_null(datasets, shape: Tuple[int, int], size: int, cascor_src: Path, verbose: bool) -> Dict[str, Dict[str, float]]:
    """Score ``size`` freshly-initialised networks of ``shape`` against every dataset.

    THIS IS THE LOAD-BEARING PART OF THE MODULE. Without it, ``gaussian`` wins almost every
    comparison for a reason that has nothing to do with training: it is linearly separable, so
    a random boundary already separates it, and permutation-correction turns that into a
    near-perfect score. Measured: untrained networks average +0.408 over chance on gaussian
    and up to +0.500.

    The null is built per (input_size, output_size) because capacity and output width change
    what a random network scores; a null borrowed from a different shape would be the wrong
    floor.
    """
    sys.path.insert(0, str(cascor_src))
    import torch

    from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig

    input_size, output_size = shape
    samples: Dict[str, List[float]] = {name: [] for name in datasets}
    with _muffle_stdout(not verbose):
        for seed in range(size):
            torch.manual_seed(seed)
            network = CascadeCorrelationNetwork(config=CascadeCorrelationConfig(input_size=input_size, output_size=output_size, random_seed=seed))
            for name, scored in score_network(network, datasets, torch).items():
                samples[name].append(scored)
    # A shape with no compatible dataset yields empty samples -- the archive's (2,1), (2,3),
    # (2,4), (4,2) and (784,10) networks, which no 2-in/2-out generator can score. That is a
    # legitimate outcome rather than an error, and it must not raise: those snapshots are
    # simply unattributable against this dataset roster and are reported as such.
    built: Dict[str, Dict[str, Optional[float]]] = {}
    for name, values in samples.items():
        if values:
            built[name] = {"p50": percentile(values, 50), "p95": percentile(values, 95), "max": max(values), "n": len(values)}
        else:
            built[name] = {"p50": None, "p95": None, "max": None, "n": 0}
    return built


def score_network(network, datasets, torch) -> Dict[str, float]:
    """Permutation-corrected accuracy on every SHAPE-COMPATIBLE dataset.

    A dataset whose width does not match the network is skipped rather than coerced: scoring a
    2-output network against a 3-class problem would compare different questions.
    """
    results: Dict[str, float] = {}
    for name, data in datasets.items():
        if getattr(network, "input_size", None) != data["input_size"] or getattr(network, "output_size", None) != data["output_size"]:
            continue
        try:
            output = network.forward(torch.tensor(data["X"], dtype=torch.float32))
            predicted = output.argmax(dim=1).cpu().numpy()
        except Exception:  # noqa: BLE001 - an un-runnable network is not attributable; that is a finding
            continue
        results[name] = permutation_corrected_accuracy(predicted, data["labels"], data["output_size"])
    return results


def adjudicate(scores: Dict[str, float], null: Dict[str, Dict[str, float]], margin: float, gap: float) -> Dict[str, Any]:
    """Turn a score vector into a verdict, refusing to answer when the evidence is weak."""
    if not scores:
        return {"verdict": INDETERMINATE, "dataset": None, "reason": "no shape-compatible dataset to score against", "lift": None, "gap": None}

    # A dataset with no null -- no untrained sample could be scored for this shape -- has no
    # floor to clear and must not be attributable. Treating a missing floor as 1.0 drives the
    # lift negative and keeps it out of the running, which is the conservative direction.
    def _floor(name: str) -> float:
        """The floor is the null's OBSERVED MAXIMUM, not its 95th percentile.

        p95 is the 5%-false-positive line, and with a 120-sample null the tail beyond it is
        not characterised at all -- so a score sitting between p95 and the observed max is
        indistinguishable from an untrained network that happened to do well.

        Measured cost of getting this wrong: with a p95 floor, **327 snapshots attributed to
        checkerboard at a median lift of +0.059 -- and a median hidden-unit count of ZERO**.
        A zero-hidden-unit network is a linear model and cannot learn checkerboard; those
        scores (~0.624) sat just above checkerboard's untrained max of 0.610, i.e. inside the
        null's tail. The xor cluster, by contrast, cleared its floor by +0.265 and was
        unaffected by the change -- which is exactly the discrimination wanted.

        A missing null means no floor to clear, so it cannot be attributed to.
        """
        entry = null.get(name, {})
        value = entry.get("max")
        if value is None:
            value = entry.get("p95")
        return 1.0 if value is None else float(value)

    lifts = {name: value - _floor(name) for name, value in scores.items()}
    ordered = sorted(lifts.items(), key=lambda kv: -kv[1])
    best, best_lift = ordered[0]
    runner_up_lift = ordered[1][1] if len(ordered) > 1 else float("-inf")
    separation = best_lift - runner_up_lift

    if best_lift < margin:
        return {
            "verdict": INDETERMINATE,
            "dataset": None,
            "reason": f"best candidate {best!r} scores {scores[best]:.3f}, within {margin:.2f} of the untrained floor {_floor(best):.3f}",
            "lift": round(best_lift, 4),
            "gap": round(separation, 4) if separation != float("inf") else None,
        }
    if separation < gap:
        return {
            "verdict": AMBIGUOUS,
            "dataset": None,
            "reason": f"{best!r} leads but {ordered[1][0]!r} is within {gap:.2f}; behaving like several of these datasets is not evidence for one",
            "lift": round(best_lift, 4),
            "gap": round(separation, 4),
        }
    return {
        "verdict": ATTRIBUTED,
        "dataset": best,
        "reason": f"scores {scores[best]:.3f} vs untrained floor {_floor(best):.3f} (+{best_lift:.3f}), clear of the runner-up by {separation:.3f}",
        "lift": round(best_lift, 4),
        "gap": round(separation, 4),
    }


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


def write_sidecar(root: Path, rows: List[dict]) -> Path:
    """Replace, not append -- an attribution is a derived verdict a later run revises."""
    sidecar = root / SIDECAR_NAME
    staging = sidecar.with_suffix(".jsonl.tmp")
    with staging.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    staging.replace(sidecar)
    return sidecar


def summarise(rows: Iterable[dict]) -> Dict[str, Any]:
    rows = list(rows)
    by_verdict: Dict[str, int] = {name: 0 for name in VERDICTS}
    by_dataset: Dict[str, int] = {}
    for row in rows:
        by_verdict[row.get("verdict", INDETERMINATE)] = by_verdict.get(row.get("verdict", INDETERMINATE), 0) + 1
        dataset = row.get("dataset")
        if dataset:
            by_dataset[dataset] = by_dataset.get(dataset, 0) + 1
    return {
        "total": len(rows),
        "by_verdict": by_verdict,
        "attributed_to": dict(sorted(by_dataset.items(), key=lambda kv: -kv[1])),
        "attributed_share": round(by_verdict.get(ATTRIBUTED, 0) / len(rows), 4) if rows else 0.0,
    }


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description="Infer which dataset each snapshot was trained on (handoff §3.2). Read-only.")
    parser.add_argument("--root", type=Path, default=None, help=f"Snapshot root (default: ${DEFAULT_ROOT_ENV}, else {DEFAULT_ROOT_FALLBACK})")
    parser.add_argument("--cascor-src", type=Path, default=None)
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--null-size", type=int, default=120, help="Untrained networks per shape in the null")
    parser.add_argument("--null-only", action="store_true", help="Build and print the per-dataset floors, then stop")
    parser.add_argument("--margin", type=float, default=DEFAULT_MARGIN, help="Required lift above the untrained p95")
    parser.add_argument("--gap", type=float, default=DEFAULT_GAP, help="Required separation from the runner-up")
    parser.add_argument(
        "--min-hidden",
        type=int,
        default=None,
        help="Only attribute snapshots with at least this many hidden units. Attribution is "
        "only meaningful for networks that grew: the archive's median is 3, and 3 units "
        "cannot learn these problems (measured -- 8 units still scored 0.510 on spiral). "
        "Restricting to the grown tail is both faster and more honest than reporting "
        "thousands of foregone-conclusion indeterminates.",
    )
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260823)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--write", action="store_true", help=f"Persist verdicts to {SIDECAR_NAME}")
    parser.add_argument("--from-sidecar", action="store_true", help="Read stored verdicts instead of recomputing")
    parser.add_argument("--verdict", choices=VERDICTS, default=None)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Let cascor's logging through (breaks --json)")
    args = parser.parse_args(argv)

    root = args.root or default_root()
    if not root.is_dir():
        print(f"ERROR: snapshot root not found: {root}", file=sys.stderr)
        return 2

    # Checked BEFORE any dataset build, null build or scoring pass. A partial-write refusal
    # that only fires after a 20-minute run is a refusal the operator discovers at the end,
    # having paid for it.
    if args.write:
        # A sidecar that silently covers a subset is worse than none: the next reader counts
        # its rows and believes them to be the archive. Both filters are refused rather than
        # recorded, because "which filter produced this file" is exactly the context that gets
        # lost between the run and the reading.
        if args.sample is not None:
            print("ERROR: refusing to --write a sampled attribution; it would replace the sidecar with a partial one", file=sys.stderr)
            return 2
        if args.min_hidden is not None:
            print("ERROR: refusing to --write a --min-hidden attribution; the sidecar must cover every loadable snapshot", file=sys.stderr)
            return 2
        if args.from_sidecar:
            print("ERROR: --from-sidecar with --write would rewrite the sidecar from itself", file=sys.stderr)
            return 2

    if args.from_sidecar:
        rows = read_jsonl(root / SIDECAR_NAME)
        if not rows:
            print(f"ERROR: no verdicts at {root / SIDECAR_NAME} — run with --write first", file=sys.stderr)
            return 2
        return _report(rows, args)

    datasets = load_datasets(args.data_root or default_data_root())
    if not datasets:
        print("ERROR: no usable datasets; nothing to attribute against", file=sys.stderr)
        return 2

    cascor_src = args.cascor_src or default_cascor_src()
    if not cascor_src.is_dir():
        print(f"ERROR: cascor source tree not found: {cascor_src}", file=sys.stderr)
        return 2

    if args.null_only:
        null = build_null(datasets, (2, 2), args.null_size, cascor_src, args.verbose)
        print(json.dumps({"shape": "2x2", "null": null}, indent=2, sort_keys=True))
        print("\nA dataset whose p95 is at or near 1.0 is UNATTRIBUTABLE: an untrained network", file=sys.stderr)
        print("already scores there, so no score can distinguish training from randomness.", file=sys.stderr)
        return 0

    classification = read_jsonl(root / CLASSIFICATION_NAME)
    if not classification:
        print(f"ERROR: no classification at {root / CLASSIFICATION_NAME} — run util/snapshot_classify.py --stage load --write first", file=sys.stderr)
        return 2
    loadable = [row for row in classification if (row.get("load") or {}).get("status") == "ok"]
    if args.min_hidden is not None:
        loadable = [row for row in loadable if (row.get("iterations_lower_bound") or 0) >= args.min_hidden]
    if args.sample is not None:
        loadable = random.Random(args.seed).sample(loadable, min(args.sample, len(loadable)))

    sys.path.insert(0, str(cascor_src))
    import torch

    from snapshots.snapshot_serializer import CascadeHDF5Serializer

    serializer = CascadeHDF5Serializer()
    nulls: Dict[Tuple[int, int], Dict[str, Dict[str, float]]] = {}
    rows: List[dict] = []
    with _muffle_stdout(not args.verbose):
        for position, record in enumerate(loadable, start=1):
            network = serializer.load_network(record["path"], restore_multiprocessing=False)
            if network is None:
                continue
            shape = (getattr(network, "input_size", None), getattr(network, "output_size", None))
            if None in shape:
                continue
            if shape not in nulls:
                nulls[shape] = build_null(datasets, shape, args.null_size, cascor_src, False)
            scores = score_network(network, datasets, torch)
            verdict = adjudicate(scores, nulls[shape], args.margin, args.gap)
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "path": record["path"],
                    "name": record.get("name"),
                    "shape": list(shape),
                    "hidden_units": record.get("iterations_lower_bound"),
                    "scores": {name: round(value, 4) for name, value in scores.items()},
                    **verdict,
                }
            )
            if position % 500 == 0:
                print(f"  … {position}/{len(loadable)}", file=sys.stderr)

    if args.write:
        print(f"wrote {len(rows)} verdict(s) -> {write_sidecar(root, rows)}", file=sys.stderr)
    return _report(rows, args)


def _report(rows: List[dict], args: argparse.Namespace) -> int:
    selected = [row for row in rows if not args.verdict or row.get("verdict") == args.verdict]
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
    print(f"{'name':<58} {'hid':>5} {'verdict':<14} {'dataset':<14} {'lift':>7} {'gap':>7}")
    for row in selected:
        print(f"{str(row.get('name', ''))[:58]:<58} {str(row.get('hidden_units', '-')):>5} {row.get('verdict', ''):<14} {str(row.get('dataset') or '-'):<14} {row.get('lift', 0) or 0:>+7.3f} {row.get('gap') or 0:>+7.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
