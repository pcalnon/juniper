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

    3. THE FLOOR IS THE NULL'S OBSERVED MAXIMUM, NOT ITS p95. A zero-hidden-unit network is a
       linear model and cannot learn a non-linearly-separable problem, yet such networks scored
       ~0.624 on checkerboard -- above its untrained p95 (0.565) but below its observed max
       (0.610), i.e. inside the null's uncharacterised tail. Under a p95 floor they attribute;
       under a max floor they do not, while the xor cluster (+0.235 median lift) is untouched.
       (An earlier revision of this passage put a specific count on that cohort. It is not
       reproducible from the current sidecar -- checkerboard now has ZERO attributions -- and
       it contradicted itself on where the scores sat. The mechanism is what the tests pin.)

    4. THE UNTRAINED NULL ANSWERS THE WRONG QUESTION, SO THERE IS A SECOND FLOOR. See
       ``build_cross_dataset_floor``. The untrained null can only ask "did this network learn
       ANYTHING?"; attribution needs "did it learn THIS rather than something else?". A
       snapshot attributed to spiral (7 hidden units) scored gaussian 0.890, moon 0.835 and
       spiral 0.624 -- attributed to spiral while scoring worse on spiral than on three other
       datasets, purely because spiral's untrained floor was the lowest available. A candidate
       must now clear BOTH floors. ``--no-cross-dataset-floor`` restores the older behaviour.

WHAT MEASUREMENT SAID ABOUT CAPACITY -- AND WHY A CAPACITY-MATCHED NULL IS NOT THE FIX
    This module used to carry a KNOWN LIMITATION saying the null is built from ZERO-hidden-unit
    networks and is therefore "too lenient for grown networks", with a capacity-matched null
    named as the rigorous fix. That was measured, and **it does not hold**.

    Of the 129 attributions, **none** had zero hidden units (they run 1..103), so the concern
    applied to all of them -- yet rebuilding the null at matched capacity withdrew only 3. At
    high capacity the capacity-matched floor is frequently LOWER than the zero-unit one: a
    zero-unit network is a linear model and a good linear split already scores well after
    permutation correction, whereas ~100 cascade units with RANDOM weights inject noise columns
    into the readout and push the score toward chance. A high score at high capacity is
    therefore HARDER to reach by accident, not easier.

    What the archive actually needed was not a capacity-matched null but a differently-TRAINED
    one -- item 4 above. Full measurement, including the weight-permutation null and the
    per-dataset outcome (xor holds with zero distributional overlap; spiral withdrawn; moon
    undecidable on one contested snapshot), is in
    ``notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md``.

VALIDATED BY A POSITIVE CONTROL
    Networks trained here on a known dataset and then attributed: **4/4 correct** (xor,
    gaussian, circles, moon; spiral and checkerboard were excluded because training did not
    take at the control's budget -- 8 hidden units still scored 0.510 on spiral). The method
    works when the network actually learned; it is the archive that is mostly under-trained,
    median 3 hidden units.

    5. THE DATASET INSTANCE HAS TO BE PINNED, OR NOTHING HERE IS REPRODUCIBLE. Five of the six
       generators declare ``seed: int | None = Field(default=None)``, so building them from
       their bare defaults draws DIFFERENT data on every call -- measured: two ``load_datasets``
       calls in ONE process returned different arrays for checkerboard, circles, gaussian, moon
       and xor. ``spiral`` alone declares a real default seed, and it was the only generator
       whose counts held steady across a rebuild.

       The cost was not theoretical. Regenerating the archive sidecar moved moon's attributed
       count from 0 to 6: moon's own score shifted 1.000 -> 0.995, which flipped one snapshot's
       first-pass winner, which removed it from moon's reference class, which dropped moon's
       cross floor 1.000 -> 0.850. ``seeded_params`` now supplies ``DATASET_SEED`` to any
       generator declaring none, and leaves a declared seed alone so spiral keeps the exact
       instance every prior analysis used.

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
#: 2 adds the ``floors`` object (``untrained`` and, when the second floor applies,
#: ``cross_dataset``) and changes what a verdict MEANS: a v2 attribution cleared both floors,
#: a v1 attribution only ever cleared the untrained one. A v1 sidecar is still readable, but
#: its verdicts are not comparable with v2's and must be regenerated rather than merged.
#:
#: ``displaced`` (and its companions ``raw_best`` / ``raw_best_score``) deliberately do NOT bump
#: this. The version encodes what a verdict MEANS, and displacement changes no verdict -- it is a
#: purely additive diagnostic over the same decision. Bumping would declare every existing v2 row
#: incomparable and force a full regeneration of a 28k-row sidecar to gain nothing. Consequence to
#: be aware of when reading an older sidecar: absence of ``displaced`` means "not computed", not
#: "not displaced". ``row.get("displaced")`` is therefore the correct test, and a census of
#: displacement must be taken from rows written after this change.
SCHEMA_VERSION = 2

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
#: Seed handed to any generator that declares none, so the dataset instance a snapshot is
#: scored against is FIXED across runs. Without it five of the six generators redraw on every
#: call and attribution is not reproducible -- see :func:`seeded_params`. Changing this value
#: redefines the canonical instance and invalidates comparisons with existing sidecars, so it
#: is a constant rather than a default that drifts.
DATASET_SEED = 20260824
#: Sentinel distinguishing "declares no ``seed`` field" from "declares ``seed=None``". They are
#: different answers: the first must be left alone (passing a seed would raise), the second is
#: the defect this module pins.
_NO_SEED_FIELD = object()


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


def seeded_params(params_cls, seed: int):
    """Build a generator's params, supplying ``seed`` ONLY where it declares none.

    Five of the six 2-D generators declare ``seed: int | None = Field(default=None)``, which
    means ``params_cls()`` draws a DIFFERENT dataset on every call -- measured: two calls to
    ``load_datasets`` in one process return different data for checkerboard, circles, gaussian,
    moon and xor. Attribution scored against that is not reproducible: a rebuild moved the
    archive's moon count from 0 to 6, because moon's own score shifted 1.000 -> 0.995, which
    flipped one snapshot's first-pass winner, which removed it from moon's reference class,
    which dropped moon's cross floor 1.000 -> 0.850.

    ``spiral`` is the exception -- it declares a real default seed -- and it is the only
    generator whose counts held steady across rebuilds. So the rule here is to RESPECT a
    generator's declared canonical instance and supply one only where the generator declines
    to: spiral keeps the exact instance every prior analysis used, and the other five become
    reproducible without silently redefining the one that already was.
    """
    params = params_cls()
    declared = getattr(params, "seed", _NO_SEED_FIELD)
    if declared is _NO_SEED_FIELD:
        # A generator with no ``seed`` field at all is not merely unseeded -- passing one would
        # raise. Absence and None are different answers and must not be collapsed.
        return params
    if declared is not None:
        return params
    return params_cls(seed=seed)


def _whole_dataset(produced: Dict[str, Any], np) -> Tuple[Any, Any]:
    """The whole dataset as ``(X, y)``, from whichever shape the generator emitted.

    Attribution wants "every row this generator produces", not a partition. That used to be
    ``produced["X_full"]``; decision 11 (juniper-data#369) retires the ``*_full`` family, so
    the key is gone from any freshly-generated artifact and a bare subscript raises.

    The concatenation is not an approximation. ``juniper_data/core/split.py`` built
    ``X_full`` as ``np.vstack([X_train, X_val, X_test])`` over contiguous slices, so
    stacking the partitions in that order reproduces it row for row for these six 2-D
    generators. A legacy artifact that still carries the family is used as-is, which keeps
    an old snapshot's attribution byte-identical to what it scored before.

    Ordering matters even though attribution itself is order-insensitive: ``labels`` is
    derived from ``y`` positionally, so ``X`` and ``y`` must be stacked the same way.
    """
    if "X_full" in produced and "y_full" in produced:
        return produced["X_full"], produced["y_full"]
    partitions = [p for p in ("train", "val", "test") if f"X_{p}" in produced]
    if not partitions:
        raise KeyError(f"no partitions to build the whole dataset from; have {sorted(produced)}")
    return (
        np.vstack([produced[f"X_{p}"] for p in partitions]),
        np.vstack([produced[f"y_{p}"] for p in partitions]),
    )


def load_datasets(data_root: Path, max_classes: int = 4, seed: int = DATASET_SEED) -> Dict[str, Dict[str, Any]]:
    """Generate one canonical instance of each 2-D classification generator.

    Uses each generator's declared defaults, except that a generator declaring no seed is given
    ``seed`` so the instance is FIXED across runs (see :func:`seeded_params`; without it,
    attribution is not reproducible run to run).

    Attribution therefore lands on a dataset FAMILY, not a specific instance -- a network
    trained on ``spiral(noise=0.1)`` is being compared against ``spiral(<defaults>)``. That is a
    real limitation and it is why a miss is reported as ``indeterminate`` rather than as
    evidence of absence.
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
            produced = generator.generate(seeded_params(params_cls, seed))
            X, y = _whole_dataset(produced, np)
        except Exception as exc:  # noqa: BLE001 - a generator that will not build is a recorded gap, not a crash
            print(f"WARNING: generator {name!r} unavailable ({type(exc).__name__}: {exc}); excluded", file=sys.stderr)
            continue
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


def build_cross_dataset_floor(rows: Iterable[dict]) -> Dict[str, Dict[str, Any]]:
    """The SECOND floor: what a network trained on something ELSE scores on each dataset.

    THIS IS THE OTHER LOAD-BEARING PART OF THE MODULE, and it exists because the untrained
    null answers the wrong question. That null asks "did this network learn anything?".
    Attribution needs "did it learn THIS rather than something else?", and the two diverge
    whenever a network trained on A also scores well on B -- which is common, because these
    six generators are not orthogonal.

    Measured instance: a snapshot attributed to ``spiral`` (7 hidden units) scored
    ``gaussian`` 0.890, ``moon`` 0.835 and ``spiral`` 0.624. It was attributed to spiral while
    scoring WORSE on spiral than on three other datasets, purely because spiral's untrained
    floor (0.572) was the lowest one available. That is floor arithmetic, not evidence.

    The reference class for dataset ``D`` is every snapshot ATTRIBUTED TO SOMETHING OTHER THAN
    D by the first pass: real networks, at real capacities, carrying real trained weights, that
    we have positive evidence were trained on something that is not D. No simulation is needed
    and none is done -- the scores already exist.

    Both the maximum and the runner-up are kept so that a snapshot can be excluded from the
    floor it is itself judged against (see ``cross_floor_excluding``). A snapshot that helps
    set its own bar is not being tested against anything.

    Returns ``{dataset: {"max", "runner_up", "n", "setter"}}``. A dataset with no reference
    class is absent, which makes it fall back to the untrained floor alone.
    """
    best: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if row.get("verdict") != ATTRIBUTED:
            continue
        attributed_to = row.get("dataset")
        if not attributed_to:
            continue
        for name, value in (row.get("scores") or {}).items():
            if name == attributed_to:
                continue
            entry = best.setdefault(name, {"max": None, "runner_up": None, "n": 0, "setter": None})
            entry["n"] += 1
            score = float(value)
            if entry["max"] is None or score > entry["max"]:
                entry["runner_up"] = entry["max"]
                entry["max"] = score
                entry["setter"] = row.get("name")
            elif entry["runner_up"] is None or score > entry["runner_up"]:
                entry["runner_up"] = score
    return best


def cross_floor_excluding(cross: Dict[str, Dict[str, Any]], row_name: Optional[str]) -> Dict[str, float]:
    """Flatten ``cross`` into ``{dataset: floor}`` with ``row_name`` removed from its own bar.

    Only matters when the excluded snapshot IS the maximum; then the runner-up governs. A
    dataset whose entire reference class was that one snapshot drops out and falls back to the
    untrained floor, rather than silently keeping a floor of its own making.
    """
    floors: Dict[str, float] = {}
    for name, entry in cross.items():
        value = entry["runner_up"] if entry.get("setter") == row_name else entry["max"]
        if value is not None:
            floors[name] = float(value)
    return floors


def adjudicate(
    scores: Dict[str, float],
    null: Dict[str, Dict[str, float]],
    margin: float,
    gap: float,
    cross_floor: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Turn a score vector into a verdict, refusing to answer when the evidence is weak.

    ``cross_floor`` is the optional SECOND floor (§ ``build_cross_dataset_floor``). When
    supplied, a candidate must clear both floors -- equivalently, the higher of the two.
    Omitting it reproduces the single-floor behaviour exactly.
    """
    if not scores:
        return {"verdict": INDETERMINATE, "dataset": None, "reason": "no shape-compatible dataset to score against", "lift": None, "gap": None}

    # A dataset with no null -- no untrained sample could be scored for this shape -- has no
    # floor to clear and must not be attributable. Treating a missing floor as 1.0 drives the
    # lift negative and keeps it out of the running, which is the conservative direction.
    def _untrained_floor(name: str) -> float:
        """The floor is the null's OBSERVED MAXIMUM, not its 95th percentile.

        p95 is the 5%-false-positive line, and with a 120-sample null the tail beyond it is
        not characterised at all -- so a score sitting between p95 and the observed max is
        indistinguishable from an untrained network that happened to do well.

        The failure this rules out: a zero-hidden-unit network is a linear model and cannot
        learn a non-linearly-separable problem, yet such networks scored ~0.624 on
        checkerboard -- above its untrained p95 of 0.565 but below its observed max of 0.610,
        i.e. inside the tail a 120-sample null cannot characterise. Under a p95 floor they
        attribute; under a max floor they do not. The xor cluster clears its floor by +0.265
        and is unaffected either way, which is exactly the discrimination wanted.

        (An earlier revision of this docstring put a specific count on that cohort. It is not
        reproducible from the current sidecar -- checkerboard now has ZERO attributions -- and
        the passage contradicted itself on whether the scores sat between p95 and max or above
        max. The mechanism above is what the regression tests pin; the count is not quoted.)

        A missing null means no floor to clear, so it cannot be attributed to.
        """
        entry = null.get(name, {})
        value = entry.get("max")
        if value is None:
            value = entry.get("p95")
        return 1.0 if value is None else float(value)

    def _floor(name: str) -> float:
        """The effective floor: the stricter of the untrained and cross-dataset floors.

        The two ask different questions and a candidate has to answer both -- "did this network
        learn anything?" (untrained) and "did it learn THIS rather than something else?"
        (cross-dataset). Requiring both is the same as clearing the higher one.
        """
        floor = _untrained_floor(name)
        if cross_floor:
            other = cross_floor.get(name)
            if other is not None:
                floor = max(floor, float(other))
        return floor

    lifts = {name: value - _floor(name) for name, value in scores.items()}
    ordered = sorted(lifts.items(), key=lambda kv: -kv[1])
    best, best_lift = ordered[0]
    runner_up_lift = ordered[1][1] if len(ordered) > 1 else float("-inf")
    separation = best_lift - runner_up_lift

    def _floors_for(name: str) -> Dict[str, Optional[float]]:
        """Both floors for ``name``, so a verdict can be re-derived without re-running."""
        entry: Dict[str, Optional[float]] = {"untrained": round(_untrained_floor(name), 4)}
        if cross_floor and cross_floor.get(name) is not None:
            entry["cross_dataset"] = round(float(cross_floor[name]), 4)
        return entry

    def _which(name: str) -> str:
        """Name the floor that actually bound, so the reason says WHY it was refused."""
        if cross_floor and cross_floor.get(name) is not None and float(cross_floor[name]) > _untrained_floor(name):
            return "cross-dataset floor"
        return "untrained floor"

    if best_lift < margin:
        return {
            "verdict": INDETERMINATE,
            "dataset": None,
            "reason": f"best candidate {best!r} scores {scores[best]:.3f}, within {margin:.2f} of the {_which(best)} {_floor(best):.3f}",
            "lift": round(best_lift, 4),
            "gap": round(separation, 4) if separation != float("inf") else None,
            "floors": _floors_for(best),
        }
    if separation < gap:
        return {
            "verdict": AMBIGUOUS,
            "dataset": None,
            "reason": f"{best!r} leads but {ordered[1][0]!r} is within {gap:.2f}; behaving like several of these datasets is not evidence for one",
            "lift": round(best_lift, 4),
            "gap": round(separation, 4),
            "floors": _floors_for(best),
        }
    # DISPLACEMENT. The winner is chosen by LIFT (score - floor), not by raw score, and those can
    # disagree: a candidate with a low floor can win while scoring worse than several datasets it
    # was not attributed to. §3.2 of the null-model findings has the clearest case -- a snapshot
    # attributed to spiral at 0.624 while scoring gaussian 0.890 and moon 0.835, winning only
    # because spiral's floor (0.572) was the lowest available. That is floor arithmetic, and it is
    # exactly the reasoning that made spiral's attributions withdrawable.
    #
    # Lift remains the right criterion -- raw score cannot distinguish "learned this" from "this
    # dataset is easy" -- so this does NOT change any verdict. It only marks the rows where the two
    # criteria disagree, because those are the ones whose evidence is arithmetic rather than
    # separation, and a reader has no way to see it from `lift` alone.
    #
    # Framed on "best raw score != winner", deliberately NOT on "floor >= 1.000": a saturated floor
    # is the gaussian-unattributable case, a different diagnostic that this flag would obscure.
    raw_best = max(scores, key=lambda name: scores[name])
    displaced = raw_best != best

    verdict: Dict[str, Any] = {
        "verdict": ATTRIBUTED,
        "dataset": best,
        "reason": f"scores {scores[best]:.3f} vs {_which(best)} {_floor(best):.3f} (+{best_lift:.3f}), clear of the runner-up by {separation:.3f}",
        "lift": round(best_lift, 4),
        "gap": round(separation, 4),
        "floors": _floors_for(best),
        "displaced": displaced,
    }
    if displaced:
        verdict["raw_best"] = raw_best
        verdict["raw_best_score"] = round(float(scores[raw_best]), 4)
        verdict["reason"] += (
            f"; DISPLACED -- {raw_best!r} scores higher ({scores[raw_best]:.3f} vs {scores[best]:.3f}) "
            f"but lifts less over its own floor"
        )
    return verdict


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
    parser.add_argument(
        "--dataset-seed",
        type=int,
        default=DATASET_SEED,
        help="Seed for generators that declare none, so the dataset instance is fixed across "
        "runs (5 of the 6 redraw otherwise, which makes attribution non-reproducible). "
        "spiral declares its own and keeps it. Changing this redefines the canonical instance "
        "and invalidates comparisons with an existing sidecar.",
    )
    parser.add_argument(
        "--no-cross-dataset-floor",
        dest="cross_dataset_floor",
        action="store_false",
        help="Judge against the untrained null ALONE, as this tool did before the second floor "
        "existed. The untrained null answers 'did this learn anything?'; attribution needs "
        "'did it learn THIS rather than something else?'. Disabling restores the weaker, "
        "single-question behaviour -- available for comparison, not recommended.",
    )
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

    datasets = load_datasets(args.data_root or default_data_root(), seed=args.dataset_seed)
    print(f"dataset seed: {args.dataset_seed} (applied only to generators declaring none; spiral keeps its own)", file=sys.stderr)
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

    # SECOND PASS. The first pass judged every snapshot against the untrained null alone, which
    # can only answer "did this learn anything?". Its attributions are now the reference class
    # for the cross-dataset floor, which answers "did it learn THIS rather than something else?"
    # -- so this pass cannot run until the first one has finished.
    if args.cross_dataset_floor:
        cross = build_cross_dataset_floor(rows)
        if not cross:
            print("note: no first-pass attributions, so no cross-dataset floor could be built", file=sys.stderr)
        else:
            withdrawn = 0
            for row in rows:
                revised = adjudicate(
                    row["scores"],
                    nulls[tuple(row["shape"])],
                    args.margin,
                    args.gap,
                    cross_floor=cross_floor_excluding(cross, row.get("name")),
                )
                if row.get("verdict") == ATTRIBUTED and revised.get("verdict") != ATTRIBUTED:
                    withdrawn += 1
                row.update(revised)
            print(
                f"cross-dataset floor applied over {len(cross)} dataset(s); {withdrawn} first-pass attribution(s) withdrawn",
                file=sys.stderr,
            )

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
    print(f"{'name':<58} {'hid':>5} {'verdict':<14} {'dataset':<14} {'lift':>7} {'gap':>7}  {'raw'}")
    displaced_count = 0
    for row in selected:
        # A displaced row is flagged inline rather than filtered out: it IS attributed, and hiding
        # it would misrepresent the count. The marker names the dataset that outscored the winner.
        marker = ""
        if row.get("displaced"):
            displaced_count += 1
            marker = f"  !{row.get('raw_best', '?')} {row.get('raw_best_score', 0) or 0:.3f}"
        print(f"{str(row.get('name', ''))[:58]:<58} {str(row.get('hidden_units', '-')):>5} {row.get('verdict', ''):<14} {str(row.get('dataset') or '-'):<14} {row.get('lift', 0) or 0:>+7.3f} {row.get('gap') or 0:>+7.3f}{marker}")
    if displaced_count:
        print(
            f"\n{displaced_count} DISPLACED: the winner is not the highest raw scorer -- it won on lift"
            f" over a lower floor. Marked '!<dataset> <score>'. See § DISPLACEMENT in adjudicate().",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
