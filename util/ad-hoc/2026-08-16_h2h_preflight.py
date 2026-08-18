#!/usr/bin/env python3
"""WIDE-BUDGET HEAD-TO-HEAD -- prove the equalisation invariants BEFORE burning the GPU-hours.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-16
Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
Retire when: the wide-budget head-to-head evidence note is merged; delete then.
Related:     util/experiments/suites/p4/e-j-h2h-wide-cap{64,128}.yaml (the suites under test);
             util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml (the shared base config);
             util/ad-hoc/2026-08-16_h2h_collect.py (the after-the-fact evidence collector).

The campaign's whole value rests on the two arms being equalised. Most of the ways that can fail
are silent -- they produce a clean-looking run whose numbers mean nothing:

  * the CLI arm fed the hand-written base config instead of a suite-generated cell, so every CLI
    replicate trains on one seed while the service arm varies;
  * `max_epochs` set without `output_epochs`, so the service runs every per-round output pass at
    the 10000-epoch module default while the CLI runs 2000 (cascade_correlation.py:716/1882);
  * a key the direct CLI cannot receive (candidate_patience, algorithm, radius) left in the
    config, so it moves the service arm only;
  * `max_iterations` below the cap, so growth stops before the cap binds -- the R-3 defect in a
    new costume;
  * both suites deriving DIFFERENT seeds, so the cap-64 and cap-128 replicates share no datasets.

This materialises every cell of both suites into a throwaway directory -- exactly as run_suite
would, through run_suite's own code -- and asserts each of those. It runs no services and writes
nothing outside the temp dir.

Usage: python util/ad-hoc/2026-08-16_h2h_preflight.py [--repo-root P]
Exit:  0 all invariants hold; 1 an invariant failed; 2 could not run the check.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

# The direct-CLI key maps (juniper-cascor/src/main.py:228-249) as of cascor 3909d27. Anything a
# config sets that is NOT in these maps binds the SERVICE arm only, and is therefore either an
# EQUALISE key (deliberate -- it makes the service match a CLI default) or a bug.
CLI_DATASET_KEYS = {"n_points_per_spiral", "n_spirals", "n_rotations", "noise", "train_ratio", "test_ratio", "seed"}
CLI_TRAINING_KEYS = {"learning_rate", "correlation_threshold", "max_hidden_units", "patience", "candidate_epochs", "candidate_pool_size", "output_epochs", "max_epochs"}
# Unmapped keys this campaign sets ON PURPOSE, because the value makes the service behave the way
# the CLI already does by default (see the base config's EQUALISATION DOCTRINE).
ALLOWED_UNMAPPED_TRAINING = {"max_iterations", "early_stopping"}

# Replicate counts are NOT equal across the caps, on purpose. Cap-128 was reduced to two after the
# cap-64 measurements showed a direct-CLI arm costs ~1.8x its service counterpart, which put the
# full 3x2x3 design near 23 h; the hours went to the init-control cell instead. What must still
# hold is that cap-128's seeds are a PREFIX of cap-64's -- that is what keeps each cap-128
# replicate paired with a cap-64 replicate on identical content-addressed data.
SUITES = {"e-j-h2h-wide-cap64.yaml": 3, "e-j-h2h-wide-cap128.yaml": 2}
EXPECTED_SEEDS = [20260729, 20260730, 20260731]
# The init control is checked separately: it is the one cell that must NOT derive a seed at all.
INIT_CONTROL = "e-j-h2h-wide-cap64-init42.yaml"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = ap.parse_args()

    root: Path = args.repo_root.resolve()
    try:
        run_suite = _load(root / "util/experiments/run_suite.py", "h2h_run_suite")
        driver = _load(root / "util/experiments/run_experiment.py", "h2h_driver")
    except Exception as exc:  # noqa: BLE001 - a load failure is a hard stop, not a finding
        print(f"preflight: cannot import the suite/driver modules: {exc}", file=sys.stderr)
        return 2

    failures: list[str] = []
    notes: list[str] = []
    per_suite_seeds: dict[str, list[int]] = {}

    with tempfile.TemporaryDirectory(prefix="h2h-preflight-") as tmp:
        for suite_file, want_cells in list(SUITES.items()) + [(INIT_CONTROL, 1)]:
            suite_path = root / "util/experiments/suites/p4" / suite_file
            try:
                doc = run_suite.load_suite(suite_path)
                cells = run_suite.expand_cells(doc, suite_path)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{suite_file}: does not load/expand: {exc}")
                continue

            if len(cells) != want_cells:
                failures.append(f"{suite_file}: expands to {len(cells)} cells, expected {want_cells}")

            seeds: list[int] = []
            for cell in cells:
                suite_dir = Path(tmp) / suite_file.replace(".yaml", "")
                try:
                    # validate=driver.load_config is exactly what run_suite passes: the resolved
                    # config is rejected here if the driver would reject it at run time.
                    out = run_suite.materialise_cell(cell, doc["suite"], suite_dir, driver.load_config)
                except Exception as exc:  # noqa: BLE001
                    failures.append(f"{suite_file}/{cell['cell_id']}: resolved config rejected: {exc}")
                    continue

                import yaml  # local: only needed once the cell exists

                cfg = yaml.safe_load(out.read_text())
                tag = f"{suite_file}/{cell['cell_id']}"
                exp = cfg.get("experiment", {})
                dparams = (cfg.get("dataset") or {}).get("params") or {}
                tparams = (cfg.get("training") or {}).get("params") or {}

                # --- seeds: derived, and written into BOTH places ---
                seeds.append(int(dparams.get("seed", -1)))
                if exp.get("seed") != dparams.get("seed"):
                    failures.append(f"{tag}: experiment.seed {exp.get('seed')} != dataset.params.seed {dparams.get('seed')} (per_cell rewrite did not reach both)")

                # --- the trap that has no other guard ---
                if tparams.get("max_epochs") != tparams.get("output_epochs"):
                    failures.append(f"{tag}: max_epochs {tparams.get('max_epochs')} != output_epochs {tparams.get('output_epochs')} -- the service would run per-round passes at a different budget than the CLI")

                # --- no unmapped key moves one arm only ---
                for key in sorted(set(tparams) - CLI_TRAINING_KEYS - ALLOWED_UNMAPPED_TRAINING):
                    failures.append(f"{tag}: training.params.{key} is not in _W11_TRAINING_KEY_MAP -- it binds the SERVICE arm only")
                for key in sorted(set(dparams) - CLI_DATASET_KEYS):
                    failures.append(f"{tag}: dataset.params.{key} is not in _W11_DATASET_KEY_MAP -- the CLI cannot send it")

                # --- the cap must actually be able to bind (R-3 in a new costume) ---
                cap = tparams.get("max_hidden_units")
                iters = tparams.get("max_iterations")
                if not isinstance(cap, int) or not isinstance(iters, int) or iters < cap:
                    failures.append(f"{tag}: max_iterations {iters} does not clear max_hidden_units {cap} -- growth stops before the cap binds")

                # --- the knobs the campaign is defined by ---
                if dparams.get("n_rotations") != 3.0:
                    failures.append(f"{tag}: n_rotations {dparams.get('n_rotations')!r}, expected an explicit 3.0 (the hard spiral)")
                if tparams.get("candidate_pool_size") != 8:
                    failures.append(f"{tag}: candidate_pool_size {tparams.get('candidate_pool_size')!r}, expected 8")
                if (cfg.get("outputs") or {}).get("plots") != []:
                    failures.append(f"{tag}: outputs.plots must be [] -- service-side rendering biases the wall comparison")
                if (cfg.get("outputs") or {}).get("max_wall_seconds") is None:
                    failures.append(f"{tag}: outputs.max_wall_seconds unset -- silently inherits the driver's 3600 s (the E-I budget trap)")

                notes.append(f"{tag}: cap={cap} pool={tparams.get('candidate_pool_size')} seed={dparams.get('seed')} epochs={tparams.get('max_epochs')}/{tparams.get('output_epochs')} patience={tparams.get('patience')} cand_epochs={tparams.get('candidate_epochs')}")

            per_suite_seeds[suite_file] = seeds
            if suite_file == INIT_CONTROL:
                # The whole point of this cell is that BOTH arms initialise at 42: the service
                # network is unconditionally _PROJECT_RANDOM_SEED, and the CLI derives its init
                # from the dataset seed. A per_cell derivation here would silently destroy it.
                if doc["suite"].get("seed_policy", "fixed") != "fixed":
                    failures.append(f"{INIT_CONTROL}: seed_policy must be 'fixed' -- per_cell would rewrite the 42 that equalises the two arms' initialisation")
                if seeds != [42]:
                    failures.append(f"{INIT_CONTROL}: dataset seed {seeds}, expected [42] (== _PROJECT_RANDOM_SEED, the service's unconditional network seed)")
            elif seeds and seeds != EXPECTED_SEEDS[:len(seeds)]:
                failures.append(f"{suite_file}: derived seeds {seeds}, expected the prefix {EXPECTED_SEEDS[:len(seeds)]}")

            # stall_seconds must be present and above the driver default -- CI cannot check this
            # at pool 8 (the R-6 gate keys on pool >= 16 and skips).
            stall = (doc.get("execution") or {}).get("stall_seconds")
            if stall is None or float(stall) <= float(driver.DEFAULT_STALL_SECONDS):
                failures.append(f"{suite_file}: execution.stall_seconds {stall!r} must exceed the driver default {driver.DEFAULT_STALL_SECONDS} -- a healthy wide cell would be recorded `stalled`")

    # The pairing that lets each cap-128 replicate sit on the same data as a cap-64 replicate.
    big, small = per_suite_seeds.get("e-j-h2h-wide-cap64.yaml"), per_suite_seeds.get("e-j-h2h-wide-cap128.yaml")
    if big and small and small != big[:len(small)]:
        failures.append(f"cap-128 seeds {small} are not a prefix of cap-64's {big} -- the caps would share no datasets and the cross-cap pairing is lost")

    for line in notes:
        print(f"  {line}")
    print()
    if failures:
        print(f"PREFLIGHT FAILED -- {len(failures)} invariant(s) violated:")
        for f in failures:
            print(f"  FAIL  {f}")
        return 1
    distinct = sorted({s for seeds in per_suite_seeds.values() for s in seeds})
    print(f"PREFLIGHT OK -- {len(notes)} cells across {len(per_suite_seeds)} suites; "
          f"cap-64 {SUITES['e-j-h2h-wide-cap64.yaml']} replicates, cap-128 {SUITES['e-j-h2h-wide-cap128.yaml']} (reduced -- see that suite's header), init control 1.")
    print(f"                 {len(distinct)} distinct dataset seeds {distinct} -> expect {len(distinct)} dataset ids, NOT one per cell: "
          "the caps deliberately share data so each cap-128 replicate is paired with a cap-64 one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
