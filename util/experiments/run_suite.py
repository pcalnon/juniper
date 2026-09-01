#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   experiments
# File Name:     run_suite.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Sequential multi-run experiment suite driver (CLI experimentation plan §13.1/§13.2, Wave 7.1).
#   Expands a suite YAML (base configs × a dotted-path override matrix + include/exclude) into an
#   ordered cell list, materialises each cell as a standalone driver-validated experiment YAML,
#   executes cells sequentially (per-cell experiment_stack --up → run_experiment → --down), records
#   each outcome in the append-only SUITE_DIR/registry.jsonl + the global RUN_ROOT/index.jsonl, and
#   aggregates into aggregate.csv + REPORT.md + suite_manifest.json. Wave 7.5 adds bounded
#   parallelism (execution.mode: parallel + max_parallel; H-11 thread-budget split recorded per
#   cell; cascor parallel>1 still refused from one checkout — Q-6's override landed (cascor#523) but
#   run_suite cannot verify the installed cascor honours it (H-7) — recurrence is free).
#####################################################################################################################################################################################################
"""Run an experiment suite (sequential, or bounded-parallel for recurrence).

Usage:
    python util/experiments/run_suite.py --suite SUITE.yaml [--dry-run] [--resume SUITE_ID]
                                         [--only CELL_ID ...]

Exit codes: 0 = every executed cell succeeded; 1 = suite completed with failed
cells (or aggregation found none succeeded); 2 = misuse / suite-validation error.

Test seams: ``JUNIPER_SUITE_LAUNCHER`` / ``JUNIPER_SUITE_DRIVER`` override the
launcher script and driver script paths; ``JUNIPER_SUITE_PYTHON`` overrides the
interpreter used for the driver (defaults to this interpreter).

``JUNIPER_SUITE_GRAFANA_BRIDGE=1`` adds ``--grafana-bridge`` to every ``--up``, so the
run's metrics are scraped into Prometheus (socat relay + file_sd target). Off by default:
without it a run is UNSCRAPED and ``metrics_scraped.present`` is ``false`` in its manifest.
It is an env toggle rather than a suite key on purpose — see ``execute_cell``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LAUNCHER = REPO_ROOT / "util" / "experiment_stack.bash"
DEFAULT_DRIVER = Path(__file__).resolve().parent / "run_experiment.py"
DEFAULT_RUN_ROOT = Path(os.environ.get("JUNIPER_EXP_RUN_ROOT", str(Path.home() / ".local" / "state" / "juniper-experiments")))

RUN_ID_BANNER = re.compile(r"Experiment run (\S+) is up")

SUITE_KEYS = frozenset({"schema_version", "suite", "execution", "matrix", "include", "exclude", "outputs"})
SUITE_SUITE_KEYS = frozenset({"name", "description", "app", "base_config", "seed_policy"})
EXECUTION_KEYS = frozenset({"mode", "max_parallel", "continue_on_failure", "per_run_timeout_seconds", "stall_seconds", "max_wall_seconds"})
TERMINAL_OUTCOMES = frozenset({"succeeded", "failed", "stalled", "timed_out"})


class SuiteError(Exception):
    """Suite-validation misuse — exits 2."""


def _sha8(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()[:8]


def load_suite(path: Path) -> dict:
    try:
        doc = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise SuiteError(f"cannot read suite YAML {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise SuiteError("suite YAML must be a mapping")
    unknown = set(doc) - SUITE_KEYS
    if unknown:
        raise SuiteError(f"unknown top-level suite keys: {sorted(unknown)}")
    if doc.get("schema_version") != 1:
        raise SuiteError("schema_version must be 1")
    suite = doc.get("suite") or {}
    unknown = set(suite) - SUITE_SUITE_KEYS
    if unknown:
        raise SuiteError(f"unknown suite: keys: {sorted(unknown)}")
    if suite.get("app") not in ("cascor", "recurrence"):
        raise SuiteError("suite.app must be 'cascor' or 'recurrence'")
    if not suite.get("name"):
        raise SuiteError("suite.name is required")
    base = suite.get("base_config") or []
    if not isinstance(base, list) or not base:
        raise SuiteError("suite.base_config must be a non-empty list")
    seed_policy = suite.get("seed_policy", "fixed")
    if seed_policy not in ("fixed", "per_cell"):
        raise SuiteError("suite.seed_policy must be 'fixed' or 'per_cell'")
    execution = doc.get("execution") or {}
    unknown = set(execution) - EXECUTION_KEYS
    if unknown:
        raise SuiteError(f"unknown execution: keys: {sorted(unknown)}")
    mode = execution.get("mode", "sequential")
    if mode not in ("sequential", "parallel"):
        raise SuiteError("execution.mode must be 'sequential' or 'parallel'")
    max_parallel = int(execution.get("max_parallel", 1))
    if max_parallel < 1:
        raise SuiteError("execution.max_parallel must be >= 1")
    if mode == "parallel" and max_parallel > 1 and suite.get("app") == "cascor":
        # Wave 7.5 / Q-6: cascor's file logger targets the shared checkout logs/juniper_cascor.log
        # (H-7); N parallel cascor instances from ONE checkout race it, and because that file is the
        # ONLY place the parent logger writes, the race destroys run evidence rather than merely
        # interleaving it. Recurrence suites parallelise freely.
        #
        # The blanket refusal is LIFTED as of cascor 0.10.0 (2026-08-30), the first release
        # carrying the JUNIPER_CASCOR_LOG_DIR override (cascor#523) that experiment_stack.bash
        # exports per run. What replaces it is the version floor the old comment demanded — read
        # from the tree that will actually be LAUNCHED, not from the driver's own environment.
        #
        # FAILS CLOSED. An undeterminable version refuses, because "we could not read it" and
        # "it is new enough" must not resolve the same way: the failure this guards is silent, so
        # a guard that defaults to permissive would restore the exact race it exists to prevent.
        version, how = _cascor_tree_version()
        if version is None:
            raise SuiteError(
                f"app: cascor with max_parallel > 1 needs a verifiable cascor >= "
                f"{'.'.join(map(str, CASCOR_PARALLEL_FLOOR))} (JUNIPER_CASCOR_LOG_DIR, cascor#523), "
                f"and the version could not be read: {how}. Refusing rather than assuming — the "
                f"shared-log race (Q-6 / H-7) destroys run evidence silently. Use mode: sequential."
            )
        if version < CASCOR_PARALLEL_FLOOR:
            raise SuiteError(
                f"app: cascor with max_parallel > 1 needs cascor >= "
                f"{'.'.join(map(str, CASCOR_PARALLEL_FLOOR))}; the tree that will run is "
                f"{'.'.join(map(str, version))} ({how}). Below that floor "
                f"JUNIPER_CASCOR_LOG_DIR is silently ignored and parallel cells race the shared "
                f"logs/juniper_cascor.log (Q-6 / H-7). Use mode: sequential, or point "
                f"JUNIPER_EXP_CASCOR_SRC_DIR at a tree >= the floor."
            )
    return doc


#: Q-6: the first cascor release carrying JUNIPER_CASCOR_LOG_DIR (cascor#523, published
#: 2026-08-30). Below this the export is silently ignored and parallel cells race the shared
#: logs/juniper_cascor.log — the H-7 evidence-destroying race, with no signal that it happened.
CASCOR_PARALLEL_FLOOR = (0, 10, 0)


def _cascor_tree_version() -> "tuple[tuple | None, str]":
    """Version of the cascor tree the stack will LAUNCH, and how it was resolved.

    Returns ``(version_tuple_or_None, description)``.

    **Not** ``importlib.metadata.version("juniper-cascor")``. That reads the DRIVER's
    environment, which is not necessarily what runs: ``experiment_stack.bash`` launches uvicorn
    with the cascor tree as CWD, and ``JuniperCascor1``'s editable finder registers itself with
    ``sys.meta_path.append`` — *after* the default ``PathFinder`` — so CWD wins and the installed
    distribution is only a fallback (measured, ml#1488). A metadata read would therefore be a
    vacuous check: it can report a compliant version while a pinned worktree runs an older tree.

    Resolution mirrors ``experiment_stack.bash:112`` exactly, so the version reported here is the
    version of the code that will actually serve the run.
    """
    src = os.environ.get("JUNIPER_EXP_CASCOR_SRC_DIR", "").strip()
    project = os.environ.get("JUNIPER_EXP_PROJECT_DIR", "").strip()
    if src:
        tree, how = Path(src).parent, "JUNIPER_EXP_CASCOR_SRC_DIR"
    elif project:
        tree, how = Path(project) / "juniper-cascor", "JUNIPER_EXP_PROJECT_DIR"
    else:
        # No fixed parent depth. From the canonical checkout the ecosystem root is parents[3],
        # but from a session worktree the same index lands on `.../.claude/worktrees` — the trap
        # experiment_stack.bash calls out at its own PROJECT_DIR resolution, and which the first
        # version of this function walked straight into. Probe upward for the ancestor that
        # actually contains a juniper-cascor sibling instead of asserting a layout.
        tree, how = None, "ancestor probe (no JUNIPER_EXP_* override set)"
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "juniper-cascor"
            if (candidate / "pyproject.toml").is_file():
                tree, how = candidate, "ancestor probe"
                break
        if tree is None:
            return None, f"{how}: no juniper-cascor sibling found above {Path(__file__).resolve()}"
    pyproject = tree / "pyproject.toml"
    if not pyproject.is_file():
        return None, f"{how} -> {tree} (no pyproject.toml)"
    m = re.search(r'(?m)^version\s*=\s*"([0-9]+(?:\.[0-9]+)*)"', pyproject.read_text(encoding="utf-8"))
    if not m:
        return None, f"{how} -> {tree} (no static version in pyproject.toml)"
    return tuple(int(p) for p in m.group(1).split(".")), f"{how} -> {tree} @ {m.group(1)}"


def _resolve_base_config(suite_path: Path, config_rel: str) -> Path:
    """Resolve a base_config entry relative to the suite file.

    Sibling-repo references (``../../../../juniper-cascor/...``) assume the
    canonical ecosystem layout; from a session worktree the relative walk lands
    outside the ecosystem. When ``JUNIPER_EXP_PROJECT_DIR`` is set (the launcher's
    own worktree override), the path is rebased onto it from its first
    ``juniper-*`` component.

    The override WINS over a literal walk that happens to resolve. It used to be
    consulted only when the literal missed, which made it an override in name and a
    fallback in fact: launched from the canonical juniper-ml checkout the literal
    always resolves, so a campaign that pinned cascor to a worktree would silently
    take its CODE from the worktree and its CONFIG from the primary. That mixed tree
    is worse than either pure one, and nothing in the manifest would have shown it.
    An override that does not exist on disk still falls back, so a stale or
    mistyped ``JUNIPER_EXP_PROJECT_DIR`` degrades rather than hard-failing the suite.
    """
    literal = (suite_path.parent / config_rel).resolve()
    project_dir = os.environ.get("JUNIPER_EXP_PROJECT_DIR", "").strip()
    if project_dir:
        parts = Path(config_rel).parts
        for i, part in enumerate(parts):
            if part.startswith("juniper-"):
                rebased = (Path(project_dir) / Path(*parts[i:])).resolve()
                if rebased.exists():
                    return rebased
                break
    return literal


def _set_dotted(config: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    node = config
    for part in parts[:-1]:
        nxt = node.get(part)
        if nxt is None:
            nxt = {}
            node[part] = nxt
        if not isinstance(nxt, dict):
            raise SuiteError(f"override path {dotted!r} crosses non-mapping node {part!r}")
        node = nxt
    node[parts[-1]] = value


def expand_cells(doc: dict, suite_path: Path) -> "list[dict]":
    """Ordered cell list: configs × matrix product, minus exclude, plus include."""
    suite = doc["suite"]
    matrix = doc.get("matrix") or {}
    include = doc.get("include") or []
    exclude = doc.get("exclude") or []
    for row in exclude:
        if not isinstance(row, dict) or not row:
            raise SuiteError("exclude entries must be non-empty mappings of dotted path -> value")

    combos: "list[dict]" = [{}]
    if matrix:
        keys = list(matrix)
        for key, values in matrix.items():
            if not isinstance(values, list) or not values:
                raise SuiteError(f"matrix.{key} must be a non-empty list")
        combos = [dict(zip(keys, values)) for values in itertools.product(*(matrix[k] for k in keys))]

    def excluded(overrides: dict) -> bool:
        return any(all(overrides.get(k) == v for k, v in row.items()) for row in exclude)

    cells: "list[dict]" = []
    index = 0
    for config_rel in suite["base_config"]:
        config_path = _resolve_base_config(suite_path, config_rel)
        for overrides in combos:
            if excluded(overrides):
                continue
            # Hash the RELATIVE reference, not the resolved path — cell ids stay
            # identical between the canonical checkout and a worktree (JUNIPER_EXP_PROJECT_DIR rebase).
            cell_id = f"c{index:03d}-{_sha8(config_rel + json.dumps(overrides, sort_keys=True))}"
            cells.append({"cell_id": cell_id, "index": index, "name": None, "config_path": str(config_path), "overrides": dict(overrides)})
            index += 1
    for item in include:
        if not isinstance(item, dict) or "overrides" not in item:
            raise SuiteError("include entries must be mappings with an 'overrides' key")
        config_rel = item.get("config", suite["base_config"][0])
        config_path = _resolve_base_config(suite_path, config_rel)
        overrides = dict(item["overrides"])
        cell_id = f"c{index:03d}-{_sha8(config_rel + json.dumps(overrides, sort_keys=True))}"
        cells.append({"cell_id": cell_id, "index": index, "name": item.get("name"), "config_path": str(config_path), "overrides": overrides})
        index += 1
    if not cells:
        raise SuiteError("suite expands to zero cells")
    return cells


def materialise_cell(cell: dict, suite: dict, suite_dir: Path, validate) -> Path:
    """Write the fully-resolved standalone experiment YAML for one cell."""
    config_path = Path(cell["config_path"])
    try:
        config = yaml.safe_load(config_path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise SuiteError(f"{cell['cell_id']}: cannot read base config {config_path}: {exc}") from exc
    for dotted, value in cell["overrides"].items():
        _set_dotted(config, dotted, value)
    if suite.get("seed_policy", "fixed") == "per_cell":
        base_seed = int(config.get("experiment", {}).get("seed", 0))
        derived = base_seed + cell["index"]
        config.setdefault("experiment", {})["seed"] = derived
        params = config.get("dataset", {}).get("params")
        if isinstance(params, dict) and "seed" in params:
            params["seed"] = derived
    exp = config.setdefault("experiment", {})
    exp["name"] = f"{suite['name']}-{cell['cell_id']}"
    cell_dir = suite_dir / "cells" / cell["cell_id"]
    cell_dir.mkdir(parents=True, exist_ok=True)
    out = cell_dir / "experiment.yaml"
    out.write_text(yaml.safe_dump(config, sort_keys=False))
    if validate is not None:
        try:
            validate(out)
        except Exception as exc:
            raise SuiteError(f"{cell['cell_id']}: resolved config rejected by the driver: {exc}") from exc
    return out


def _driver_validator():
    """The real driver's load_config, imported by path — None if unavailable."""
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("run_experiment_for_suite", DEFAULT_DRIVER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return lambda path: mod.load_config(path)
    except Exception:
        return None


_JSONL_LOCK = threading.Lock()


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _JSONL_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def thread_budget_env(app: str, max_parallel: int) -> "dict[str, str]":
    """H-11 budget split for parallel cells: CASCOR_NUM_PROCESSES (or the BLAS vars for
    recurrence) = max(1, floor(nproc / (2 * max_parallel))); cascor BLAS pinned at 2."""
    nproc = os.cpu_count() or 1
    split = max(1, nproc // (2 * max_parallel))
    if app == "cascor":
        return {"OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2", "CASCOR_NUM_PROCESSES": str(split)}
    return {"OMP_NUM_THREADS": str(split), "MKL_NUM_THREADS": str(split), "OPENBLAS_NUM_THREADS": str(split)}


def _read_registry(suite_dir: Path) -> "dict[str, dict]":
    registry = suite_dir / "registry.jsonl"
    rows: "dict[str, dict]" = {}
    if registry.exists():
        for line in registry.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["cell_id"]] = row
    return rows


def _headline_metrics(run_dir: Path) -> dict:
    stats_file = run_dir / "artifacts" / "results" / "stats.json"
    out: dict = {}
    if not stats_file.exists():
        return out
    try:
        stats = json.loads(stats_file.read_text())
    except (OSError, ValueError):
        return out
    for key in ("cascor", "recurrence"):
        block = stats.get(key)
        if isinstance(block, dict):
            for metric in ("final_accuracy", "test_accuracy", "val_accuracy", "train_r2", "cv_r2", "r2"):
                if isinstance(block.get(metric), (int, float)):
                    out[metric] = block[metric]
    return out


def execute_cell(cell: dict, cell_yaml: Path, app: str, timeout: float, launcher: Path, driver: Path, python_bin: str, extra_env: "dict[str, str] | None" = None, stall_seconds: "float | None" = None, max_wall_seconds: "float | None" = None, suite_name: "str | None" = None) -> dict:
    """--up → driver → --down for one cell; never raises for a cell-level failure.

    ``stall_seconds`` forwards ``execution.stall_seconds`` to the driver's Q-2 stall
    detector. It matters because the detector watches ``current_epoch``, which only
    advances during OUTPUT-layer training — no progress is reported while the CANDIDATE
    pool trains. A cell whose candidate phase runs longer than the driver default (120 s)
    is therefore marked ``stalled`` while perfectly healthy, and the suite has no way to
    say otherwise. Observed on the P4 E-A grid: every ``candidate_pool_size >= 16`` cell
    stalled at ~130 s, then completed normally in 513–1258 s once the window was raised.

    ``max_wall_seconds`` forwards ``execution.max_wall_seconds`` to the driver's Q-2
    wall-clock budget, and is the same class of defect one field over. A suite could
    always reach the budget through a dotted ``matrix`` / ``include`` override — the
    widest suite in the repo does exactly that
    (``suites/p4/e-i-cascor-cap-ceiling.yaml`` sets ``outputs.max_wall_seconds``) — but
    an un-overridden cell silently inherited ``base_config``'s value (3600 s for
    ``spiral-baseline``) with no signal at all. Measured on the E-I run
    (``20260814T091542Z``), its cap-128 cell took 4243.6 s and would have been truncated by
    that inherited default, while cap 64 cleared it by only 693 s. Note this is NOT
    ``per_run_timeout_seconds``, which kills the driver from the OUTSIDE and records
    ``timed_out`` where the driver would otherwise write an honest ``timed_out``
    manifest of its own.
    """
    started = time.time()
    # D-C: the suite is the only layer that knows the cell id, and the launcher passes
    # it through to cascor's process env so every snapshot this cell writes records
    # which cell produced it. Note the launcher is invoked with ``--experiment
    # cell_id`` below, so without this the cell id would be the ONLY identity recorded
    # and the suite it belongs to would be lost.
    provenance_env = {"JUNIPER_CASCOR_CELL_ID": cell["cell_id"]}
    if suite_name:
        provenance_env["JUNIPER_CASCOR_EXPERIMENT"] = suite_name
    env = {**os.environ, **provenance_env, **(extra_env or {})}

    # Grafana bridge: OPT-IN via environment, deliberately NOT a suite key.
    #
    # Two reasons, and the first is the load-bearing one. (1) A suite key would change the suite
    # file, and therefore every cell's `config_sha256`, between a bridged and an unbridged run of
    # the SAME scenario — destroying the comparability that repeat-measurement scenarios like PF-1
    # exist to provide. An env toggle leaves the YAML byte-identical. (2) The bridge is a
    # host-capability concern (it needs docker and the monitoring network) rather than a property
    # of the experiment; a suite that hard-declared it would simply fail on a host without them,
    # and `bridge_up` failing tears the whole run down.
    bridge = os.environ.get("JUNIPER_SUITE_GRAFANA_BRIDGE", "").strip().lower() in ("1", "true", "yes", "on")
    up_args = ["/bin/bash", str(launcher), "--up", f"--{app}", "--config", str(cell_yaml), "--experiment", cell["cell_id"]]
    if bridge:
        up_args.append("--grafana-bridge")

    row = {"cell_id": cell["cell_id"], "name": cell["name"], "overrides": cell["overrides"], "config_sha256": hashlib.sha256(cell_yaml.read_bytes()).hexdigest(), "run_id": None, "outcome": "failed", "exit_code": None, "error": None, "thread_budget": dict(extra_env) if extra_env else None, "grafana_bridge": bridge}
    up = subprocess.run(up_args, capture_output=True, text=True, timeout=max(timeout, 300), env=env)
    match = RUN_ID_BANNER.search(up.stdout + up.stderr)
    if up.returncode != 0 or not match:
        row["error"] = f"launcher --up failed (exit {up.returncode}): {(up.stderr or up.stdout)[-500:]}"
        row["wall_seconds"] = round(time.time() - started, 3)
        return row
    run_id = match.group(1)
    row["run_id"] = run_id
    run_dir = DEFAULT_RUN_ROOT / run_id
    try:
        try:
            drv_argv = [python_bin, str(driver), "--config", str(cell_yaml), "--run-dir", str(run_dir)]
            if stall_seconds is not None:
                drv_argv += ["--stall-seconds", str(stall_seconds)]
            if max_wall_seconds is not None:
                drv_argv += ["--max-wall-seconds", str(max_wall_seconds)]
            drv = subprocess.run(drv_argv, capture_output=True, text=True, timeout=timeout, env=env)
            row["exit_code"] = drv.returncode
        except subprocess.TimeoutExpired:
            row["exit_code"] = None
            row["outcome"] = "timed_out"
            row["error"] = f"driver exceeded per_run_timeout_seconds={timeout}"
            return row
        manifest_file = run_dir / "manifest.json"
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text())
                row["outcome"] = manifest.get("outcome", "failed")
            except (OSError, ValueError):
                row["outcome"] = "failed"
                row["error"] = "unreadable manifest.json"
        else:
            row["outcome"] = "failed"
            row["error"] = f"driver exit {drv.returncode} with no manifest: {(drv.stderr or drv.stdout)[-300:]}"
        row["metrics"] = _headline_metrics(run_dir)
        row["run_dir"] = str(run_dir)
    finally:
        down = subprocess.run(["/bin/bash", str(launcher), "--down", run_id], capture_output=True, text=True, timeout=300, env=env)
        row["teardown_ok"] = down.returncode == 0
        row["wall_seconds"] = round(time.time() - started, 3)
    return row


def aggregate(suite_dir: Path, suite: dict, cells: "list[dict]") -> int:
    registry = _read_registry(suite_dir)
    metric_keys = sorted({k for row in registry.values() for k in (row.get("metrics") or {})})
    override_keys = sorted({k for cell in cells for k in cell["overrides"]})
    csv_path = suite_dir / "aggregate.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["cell_id", "name", "run_id", "outcome", "exit_code", "wall_seconds", *override_keys, *metric_keys])
        for cell in cells:
            row = registry.get(cell["cell_id"], {})
            writer.writerow(
                [cell["cell_id"], cell["name"] or "", row.get("run_id") or "", row.get("outcome") or "not-run", row.get("exit_code"), row.get("wall_seconds"), *[cell["overrides"].get(k, "") for k in override_keys], *[(row.get("metrics") or {}).get(k, "") for k in metric_keys]]
            )
    succeeded = [c for c in cells if registry.get(c["cell_id"], {}).get("outcome") == "succeeded"]
    failed = [c for c in cells if registry.get(c["cell_id"], {}).get("outcome") not in (None, "succeeded")]
    lines = [
        f"# Suite report — {suite['name']}",
        "",
        f"{suite.get('description', '')}".strip(),
        "",
        f"Cells: {len(cells)} total, {len(succeeded)} succeeded, {len(failed)} failed/other, {len(cells) - len(succeeded) - len(failed)} not run.",
        "",
        "| cell | outcome | wall (s) | " + " | ".join(override_keys + metric_keys) + " |",
        "|---|---|---|" + "---|" * (len(override_keys) + len(metric_keys)),
    ]
    for cell in cells:
        row = registry.get(cell["cell_id"], {})
        values = [str(cell["overrides"].get(k, "")) for k in override_keys] + [str((row.get("metrics") or {}).get(k, "")) for k in metric_keys]
        lines.append(f"| {cell['cell_id']} | {row.get('outcome') or 'not-run'} | {row.get('wall_seconds') or ''} | " + " | ".join(values) + " |")
    (suite_dir / "REPORT.md").write_text("\n".join(lines) + "\n")
    return 0 if len(succeeded) == len(cells) else 1


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Print the expanded cell list and every command; write nothing")
    parser.add_argument("--resume", metavar="SUITE_ID", default=None, help="Resume an existing suite dir, skipping cells already terminal in registry.jsonl")
    parser.add_argument("--only", nargs="*", default=None, metavar="CELL_ID", help="Execute only these cell ids")
    args = parser.parse_args(argv)

    try:
        doc = load_suite(args.suite)
        cells = expand_cells(doc, args.suite)
    except SuiteError as exc:
        print(f"suite error: {exc}", file=sys.stderr)
        return 2

    suite = doc["suite"]
    execution = doc.get("execution") or {}
    outputs = doc.get("outputs") or {}
    timeout = float(execution.get("per_run_timeout_seconds", 3600))
    # None => omit the flag entirely, so the driver keeps owning its own default.
    stall_seconds = float(execution["stall_seconds"]) if execution.get("stall_seconds") is not None else None
    max_wall_seconds = float(execution["max_wall_seconds"]) if execution.get("max_wall_seconds") is not None else None
    continue_on_failure = bool(execution.get("continue_on_failure", True))
    launcher = Path(os.environ.get("JUNIPER_SUITE_LAUNCHER", str(DEFAULT_LAUNCHER)))
    driver = Path(os.environ.get("JUNIPER_SUITE_DRIVER", str(DEFAULT_DRIVER)))
    python_bin = os.environ.get("JUNIPER_SUITE_PYTHON", sys.executable)

    if args.resume:
        suite_id = args.resume
    else:
        suite_id = f"{suite['name']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    suite_dir = Path(outputs.get("suite_dir") or (DEFAULT_RUN_ROOT / "suites" / suite_id))

    if args.dry_run:
        print(f"suite {suite['name']} ({suite['app']}): {len(cells)} cells -> {suite_dir}")
        for cell in cells:
            print(f"  {cell['cell_id']}  config={Path(cell['config_path']).name}  overrides={json.dumps(cell['overrides'], sort_keys=True)}" + (f"  name={cell['name']}" if cell["name"] else ""))
            print(f"    $ {launcher} --up --{suite['app']} --config {suite_dir}/cells/{cell['cell_id']}/experiment.yaml --experiment {cell['cell_id']}")
            stall_flag = f" --stall-seconds {stall_seconds}" if stall_seconds is not None else ""
            wall_flag = f" --max-wall-seconds {max_wall_seconds}" if max_wall_seconds is not None else ""
            print(f"    $ {python_bin} {driver} --config …/experiment.yaml --run-dir <RUN_DIR>{stall_flag}{wall_flag} && {launcher} --down <RUN_ID>")
        return 0

    if args.resume and not suite_dir.is_dir():
        print(f"suite error: --resume {suite_id}: no such suite dir {suite_dir}", file=sys.stderr)
        return 2

    suite_dir.mkdir(parents=True, exist_ok=True)
    validate = _driver_validator()
    registry_rows = _read_registry(suite_dir) if args.resume else {}
    selected = [c for c in cells if args.only is None or c["cell_id"] in args.only]
    if args.only is not None and len(selected) != len(args.only):
        missing = set(args.only) - {c["cell_id"] for c in selected}
        print(f"suite error: --only ids not in the expansion: {sorted(missing)}", file=sys.stderr)
        return 2

    (suite_dir / "suite_manifest.json").write_text(
        json.dumps({"schema": "juniper-experiment-suite/1", "suite_id": suite_id, "suite": suite, "execution": execution, "cells": [{k: c[k] for k in ("cell_id", "index", "name", "config_path", "overrides")} for c in cells], "suite_yaml_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest()}, indent=2, sort_keys=True)
        + "\n"
    )

    mode = execution.get("mode", "sequential")
    max_parallel = int(execution.get("max_parallel", 1)) if mode == "parallel" else 1
    budget = thread_budget_env(suite["app"], max_parallel) if mode == "parallel" else None

    runnable = []
    for cell in selected:
        prior = registry_rows.get(cell["cell_id"])
        if prior and prior.get("outcome") == "succeeded":
            print(f"[suite] {cell['cell_id']}: already succeeded — skipped (resume)")
            continue
        runnable.append(cell)
    try:
        materialised = {cell["cell_id"]: materialise_cell(cell, suite, suite_dir, validate) for cell in runnable}
    except SuiteError as exc:
        print(f"suite error: {exc}", file=sys.stderr)
        return 2

    def _record(cell: dict, row: dict) -> None:
        row["suite_id"] = suite_id
        _append_jsonl(suite_dir / "registry.jsonl", row)
        _append_jsonl(DEFAULT_RUN_ROOT / "index.jsonl", {"suite_id": suite_id, "cell_id": cell["cell_id"], "run_id": row.get("run_id"), "outcome": row.get("outcome"), "run_dir": row.get("run_dir")})
        print(f"[suite] {cell['cell_id']}: {row['outcome']}" + (f" ({row.get('error')})" if row.get("error") else ""), flush=True)

    any_failed = False
    if mode == "parallel" and max_parallel > 1:
        # Wave 7.5: bounded worker pool. Port lockdirs serialise allocation; W-6 gives each
        # run its own snapshots dir; the H-11 budget env keeps N cells from thrashing the host.
        # Stop-on-failure = stop SUBMITTING after the first failure; running cells drain.
        stop = threading.Event()
        with ThreadPoolExecutor(max_workers=max_parallel) as pool:
            futures = {}
            for cell in runnable:
                if stop.is_set():
                    break
                print(f"[suite] {cell['cell_id']}: submitted ({json.dumps(cell['overrides'], sort_keys=True)})", flush=True)
                futures[pool.submit(execute_cell, cell, materialised[cell["cell_id"]], suite["app"], timeout, launcher, driver, python_bin, budget, stall_seconds, max_wall_seconds, suite["name"])] = cell
            for future in as_completed(futures):
                cell = futures[future]
                row = future.result()
                _record(cell, row)
                if row["outcome"] != "succeeded":
                    any_failed = True
                    if not continue_on_failure:
                        stop.set()
    else:
        for cell in runnable:
            print(f"[suite] {cell['cell_id']}: running ({json.dumps(cell['overrides'], sort_keys=True)})", flush=True)
            row = execute_cell(cell, materialised[cell["cell_id"]], suite["app"], timeout, launcher, driver, python_bin, budget, stall_seconds, max_wall_seconds, suite["name"])
            _record(cell, row)
            if row["outcome"] != "succeeded":
                any_failed = True
                if not continue_on_failure:
                    break

    rc = aggregate(suite_dir, suite, cells)
    print(f"[suite] wrote {suite_dir}/aggregate.csv + REPORT.md")
    return 1 if (any_failed or rc) else 0


if __name__ == "__main__":
    sys.exit(main())
