#!/usr/bin/env python3
"""run_experiment.py -- single-run experiment driver (Wave 2.2: the cascor service path).

Project: juniper-ml
Sub-Project: cascor + recurrence CLI test/validation/experimentation program
Application: experiment driver (util/experiments/)
Author: Paul Calnon
License: MIT License

Plan of record: ``notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md``
(SS6.3 driver responsibilities, SS6.4 RUN_DIR layout, SS13.4 run manifest, SS10.6 test contract) plus the Wave-0
preflight evidence doc (finding F-1 binds the ``/metrics`` sampling to redirect-following GETs).

WHAT IT DOES (SS6.3, in order):

  1. loads + validates the experiment YAML (SS5.6 driver-enforced subset: unknown blocks/keys,
     ``schema_version``, the mandatory ``experiment.seed``, and the rule-6 infra-key rejection);
     resolves the app kind from the config shape (``training:`` => cascor, ``train:`` => recurrence);
  2. health-waits on the run's juniper-data and cascor services (bounded);
  3. pre-flights the dataset: ``GET /v1/generators`` must list ``dataset.generator`` with ``available: true``;
  4. drives the run: ``POST /v1/datasets`` on juniper-data (recording the content-addressed ``dataset_id``),
     then -- spiral -- ``POST /v1/training/start`` with the inline ``dataset`` source, or -- any other
     generator (G-6) -- stages via ``POST /v1/training/dataset`` first and asserts the loaded shape
     afterwards; polls ``GET /v1/training/status`` to ``COMPLETED`` / ``FAILED`` under the Q-2 wall-clock
     budget (``outputs.max_wall_seconds``, default 3600) and stall detector (no ``current_epoch`` change for
     ``--stall-seconds``, default 120 -> ``outcome: "stalled"``, never a silent hang); on every poll samples
     the app's own loopback ``/metrics`` exposition (redirect-following, F-1) and appends the allowlisted
     family subset to ``artifacts/results/metrics_series.csv`` -- ``juniper_cascor_candidate_correlation``
     exists ONLY there (``/v1/metrics/history`` rows carry no correlation field);
  5. collects results into ``artifacts/results/``: ``metrics_final.json``, ``metrics_history.json``,
     ``topology.json``, ``decision_boundary.npz`` (2-D input only), and optionally ``POST /v1/snapshots``;
  6. writes the SS13.4 ``manifest.json`` (always -- also for stalled / timed-out / failed runs, so every
     run leaves evidence) and prints a one-screen summary.

Exit codes (SS6.3 item 8):
  0  success (run COMPLETED and the acceptance checks passed)
  1  run did not meet acceptance criteria (stalled, timed_out, interrupted, G-6 shape mismatch,
     or an essential artifact could not be collected)
  2  misuse / validation error (bad CLI, bad YAML, unknown/unavailable generator, 422 from the API)
  3  service unreachable (health-wait timeout or repeated connection failures)
  4  run reached FAILED / a 5xx from a service

Wave boundaries (SS14): the recurrence path is Wave 2.3 (a recurrence-shaped config exits 2 with a
pointer); plot rendering is Wave 2.4 (``outputs.plots`` is validated and recorded, not yet rendered);
``stats.json`` + ``summary.md`` renderers are Wave 2.6.

Dependencies: stdlib + PyYAML; numpy is imported lazily only to write ``decision_boundary.npz`` (with a
JSON fallback when absent). HTTP is stdlib ``urllib`` rather than ``requests`` -- lighter than the SS6.3
allowance and redirect-following by default, which is exactly what F-1 requires.

``util/`` is not pre-commit-lint-gated; ``tests/test_run_experiment.py`` is the gate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError as _exc:  # pragma: no cover - PyYAML is a declared driver dependency (SS6.3)
    raise SystemExit(f"run_experiment.py requires PyYAML: {_exc}")

# --------------------------------------------------------------------------- #
# constants / contract surface (imported by tests/test_run_experiment.py)
# --------------------------------------------------------------------------- #

SCHEMA_VERSION_MAX = 1

DEFAULT_POLL_INTERVAL = 5.0
DEFAULT_STALL_SECONDS = 120.0  # Q-2 ratified default
DEFAULT_MAX_WALL_SECONDS = 3600.0  # Q-2 ratified default (outputs.max_wall_seconds)
DEFAULT_HEALTH_TIMEOUT = 90.0  # matches the launcher's JUNIPER_EXP_HEALTH_TIMEOUT default (F-8)
DEFAULT_HTTP_TIMEOUT = 10.0
DEFAULT_METRICS_HISTORY_COUNT = 1000
CONSECUTIVE_POLL_ERRORS_MAX = 3

# SS6.3: the allowlisted /metrics families sampled into metrics_series.csv each poll.
# The histogram contributes its _sum/_count exposition lines explicitly.
METRIC_FAMILIES: Tuple[str, ...] = (
    "juniper_cascor_candidate_correlation",
    "juniper_cascor_hidden_units_total",
    "juniper_cascor_training_loss",
    "juniper_cascor_training_accuracy_ratio",
    "juniper_cascor_training_step_duration_seconds_sum",
    "juniper_cascor_training_step_duration_seconds_count",
)

SERIES_CSV_COLUMNS: Tuple[str, ...] = ("ts_unix", "fsm_status", "current_epoch", "current_hidden_units", *METRIC_FAMILIES)

# SS5.6 driver-enforced YAML surface. ``train``/``crossval``/``predict`` are recognised
# (recurrence-shaped, Wave 2.3) so kind resolution can name them; the cascor path never
# consumes them.
TOP_LEVEL_BLOCKS = frozenset({"schema_version", "experiment", "service", "dataset", "training", "train", "crossval", "predict", "runtime", "outputs"})
EXPERIMENT_KEYS = frozenset({"name", "description", "seed"})
DATASET_KEYS_CASCOR = frozenset({"generator", "params", "persist", "tags", "ttl_seconds"})
TRAINING_KEYS = frozenset({"start_fresh", "epochs", "params"})
RUNTIME_KEYS = frozenset({"num_processes", "blas_threads", "eval_metrics_enabled"})
OUTPUTS_KEYS = frozenset({"decision_boundary_resolution", "metrics_history_count", "plots", "snapshot_at_end", "max_wall_seconds", "grafana_bridge", "save_model"})
# SS5.6 rule 6: infrastructure is launcher-owned; ``eval_metrics_enabled`` is process-env
# territory (``runtime:``), not a Settings field.
SERVICE_FORBIDDEN_KEYS = frozenset({"host", "port", "juniper_data_url", "eval_metrics_enabled"})

# G-6 staging aliases: juniper-data generator name -> cascor StageDatasetRequest.dataset_type
# Literal member (src/api/models/training.py StageDatasetRequest; manager.py:3251 maps the
# plurals back). gaussian/checkerboard are absent from the staged Literal until W-3 lands.
STAGEABLE_GENERATOR_ALIASES: Dict[str, str] = {
    "spiral": "spirals",
    "xor": "xor",
    "circles": "circles",
    "moon": "moons",
    "mnist": "mnist",
    "equities": "equities",
}

FSM_TERMINAL_OK = "COMPLETED"
FSM_TERMINAL_FAIL = "FAILED"

EXIT_SUCCESS = 0
EXIT_ACCEPTANCE = 1
EXIT_MISUSE = 2
EXIT_UNREACHABLE = 3
EXIT_RUN_FAILED = 4

MANIFEST_SCHEMA = "juniper-experiment-manifest/1"

# SS13.4 git-provenance repos, probed relative to the ecosystem root (best-effort).
MANIFEST_GIT_REPOS: Tuple[str, ...] = ("juniper-cascor", "juniper-recurrence", "juniper-data", "juniper-data-client", "juniper-deploy", "juniper-ml")
THREAD_ENV_VARS: Tuple[str, ...] = ("CASCOR_NUM_PROCESSES", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")

LOGGER_NAME = "run_experiment"
log = logging.getLogger(LOGGER_NAME)


class ConfigError(Exception):
    """Invalid CLI usage or experiment YAML -> exit 2."""


class ServiceUnreachable(Exception):
    """A required service could not be reached -> exit 3."""


class RunFailed(Exception):
    """The run reached FAILED or a service answered 5xx -> exit 4."""


# --------------------------------------------------------------------------- #
# HTTP helpers (stdlib urllib; redirect-following GETs per F-1)
# --------------------------------------------------------------------------- #


def _http_json(method: str, url: str, body: Optional[dict] = None, timeout: float = DEFAULT_HTTP_TIMEOUT) -> Tuple[int, Any]:
    """JSON request returning ``(status_code, parsed_body)``.

    Non-2xx responses are returned (not raised) so callers can branch on the
    code; connection-level failures raise :class:`ServiceUnreachable`.
    """
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - loopback experiment services
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            parsed: Any = json.loads(raw)
        except ValueError:
            parsed = {"detail": raw[:500]}
        return exc.code, parsed
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        raise ServiceUnreachable(f"{method} {url}: {exc}") from exc


def _http_text(url: str, timeout: float = DEFAULT_HTTP_TIMEOUT) -> str:
    """GET a text body (the Prometheus exposition). urllib follows the F-1 307 redirect by default."""
    req = urllib.request.Request(url, headers={"Accept": "text/plain"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - loopback experiment services
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise RunFailed(f"GET {url} -> HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        raise ServiceUnreachable(f"GET {url}: {exc}") from exc


def _unwrap(payload: Any) -> Any:
    """Unwrap the cascor ``{"status", "data", "meta"}`` response envelope; pass raw bodies through."""
    if isinstance(payload, dict) and payload.get("status") in {"success", "error"} and "data" in payload:
        return payload["data"]
    return payload


def _detail(payload: Any) -> str:
    """Best-effort human detail from an error body (FastAPI ``detail`` or the envelope)."""
    if isinstance(payload, dict):
        for key in ("detail", "message", "error"):
            if payload.get(key):
                return str(payload[key])[:500]
    return str(payload)[:500]


# --------------------------------------------------------------------------- #
# Prometheus exposition parsing (the SS6.3 allowlist)
# --------------------------------------------------------------------------- #


def parse_metric_samples(text: str, families: Tuple[str, ...] = METRIC_FAMILIES) -> Dict[str, float]:
    """Extract the latest sample value per allowlisted family from a Prometheus text exposition.

    Handles both bare (``name value``) and labeled (``name{l="v"} value``) sample lines;
    comment/type lines are skipped. When a family exposes multiple series the last one wins
    (the cascor families in the allowlist are singleton gauges/counters in practice).
    """
    wanted = set(families)
    out: Dict[str, float] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        brace = line.find("{")
        space = line.find(" ")
        if brace != -1 and (space == -1 or brace < space):
            name = line[:brace]
            close = line.rfind("}")
            if close == -1:
                continue
            rest = line[close + 1:].split()
        else:
            parts = line.split()
            if len(parts) < 2:
                continue
            name, rest = parts[0], parts[1:]
        if name not in wanted or not rest:
            continue
        try:
            out[name] = float(rest[0])
        except ValueError:
            continue
    return out


# --------------------------------------------------------------------------- #
# experiment YAML load + validation (SS5.6 driver-enforced subset)
# --------------------------------------------------------------------------- #


def _require_mapping(value: Any, where: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _reject_unknown_keys(block: Dict[str, Any], allowed: frozenset, where: str) -> None:
    unknown = sorted(set(block) - allowed)
    if unknown:
        raise ConfigError(f"unknown key(s) in {where}: {', '.join(unknown)} (allowed: {', '.join(sorted(allowed))})")


def load_config(path: Path) -> Dict[str, Any]:
    """Load and validate the experiment YAML; return the normalised config dict.

    Enforces the SS5.6 rules the driver owns: unknown top-level blocks / unknown keys in
    driver-consumed blocks (rule 1), ``schema_version`` (rule 2), the mandatory
    ``experiment.seed`` (rule 3), and the rule-6 infra-key rejection. Value-range
    validation stays with the live pydantic models (rule 5) -- a 422 from the API
    surfaces as exit 2 with the server's detail.
    """
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config {path}: {exc}") from exc
    try:
        cfg = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"config {path} is not valid YAML: {exc}") from exc
    cfg = _require_mapping(cfg, f"config {path}")

    unknown_blocks = sorted(set(cfg) - TOP_LEVEL_BLOCKS)
    if unknown_blocks:
        raise ConfigError(f"unknown top-level block(s): {', '.join(unknown_blocks)} (allowed: {', '.join(sorted(TOP_LEVEL_BLOCKS))})")

    version = cfg.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or not (1 <= version <= SCHEMA_VERSION_MAX):
        raise ConfigError(f"schema_version must be an integer in 1..{SCHEMA_VERSION_MAX}, got {version!r}")

    experiment = _require_mapping(cfg.get("experiment"), "experiment block") if "experiment" in cfg else None
    if experiment is None:
        raise ConfigError("missing required block: experiment")
    _reject_unknown_keys(experiment, EXPERIMENT_KEYS, "experiment")
    name = experiment.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ConfigError("experiment.name must be a non-empty string")
    seed = experiment.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ConfigError("experiment.seed is REQUIRED and must be an integer (SS5.6 rule 3: a seedless experiment is not reproducible by construction)")

    has_cascor = "training" in cfg
    has_recurrence = "train" in cfg
    if has_cascor and has_recurrence:
        raise ConfigError("config contains both 'training:' (cascor) and 'train:' (recurrence) -- exactly one app block is required")
    if not has_cascor and not has_recurrence:
        raise ConfigError("config contains neither 'training:' (cascor) nor 'train:' (recurrence) -- exactly one app block is required")
    kind = "cascor" if has_cascor else "recurrence"

    if "service" in cfg:
        service = _require_mapping(cfg["service"], "service block")
        forbidden = sorted(set(service) & SERVICE_FORBIDDEN_KEYS)
        if forbidden:
            raise ConfigError(
                f"service.{'/'.join(forbidden)} rejected (SS5.6 rule 6): host/port/juniper_data_url are launcher-owned; "
                "eval_metrics_enabled belongs in runtime: (process env), not service:"
            )

    if "runtime" in cfg:
        runtime = _require_mapping(cfg["runtime"], "runtime block")
        _reject_unknown_keys(runtime, RUNTIME_KEYS, "runtime")

    outputs_raw = _require_mapping(cfg.get("outputs", {}) or {}, "outputs block")
    _reject_unknown_keys(outputs_raw, OUTPUTS_KEYS, "outputs")
    max_wall = outputs_raw.get("max_wall_seconds", DEFAULT_MAX_WALL_SECONDS)
    if not isinstance(max_wall, (int, float)) or isinstance(max_wall, bool) or max_wall <= 0:
        raise ConfigError(f"outputs.max_wall_seconds must be a positive number, got {max_wall!r}")
    history_count = outputs_raw.get("metrics_history_count", DEFAULT_METRICS_HISTORY_COUNT)
    if not isinstance(history_count, int) or isinstance(history_count, bool) or history_count < 1:
        raise ConfigError(f"outputs.metrics_history_count must be a positive integer, got {history_count!r}")
    plots = outputs_raw.get("plots", [])
    if not isinstance(plots, list):
        raise ConfigError(f"outputs.plots must be a list, got {type(plots).__name__}")
    outputs = {
        "decision_boundary_resolution": outputs_raw.get("decision_boundary_resolution"),
        "metrics_history_count": history_count,
        "plots": plots,
        "snapshot_at_end": bool(outputs_raw.get("snapshot_at_end", False)),
        "max_wall_seconds": float(max_wall),
        "grafana_bridge": bool(outputs_raw.get("grafana_bridge", False)),
    }

    config: Dict[str, Any] = {
        "kind": kind,
        "experiment": {"name": name.strip(), "description": experiment.get("description"), "seed": seed},
        "outputs": outputs,
        "raw": cfg,
    }
    if kind == "recurrence":
        # Wave 2.3 lands the recurrence drive path; kind resolution + the shared
        # validation above already accept the shape so 2.3 is additive.
        return config

    dataset = _require_mapping(cfg.get("dataset"), "dataset block") if "dataset" in cfg else None
    if dataset is None:
        raise ConfigError("missing required block for the cascor path: dataset")
    _reject_unknown_keys(dataset, DATASET_KEYS_CASCOR, "dataset")
    generator = dataset.get("generator")
    if not isinstance(generator, str) or not generator.strip():
        raise ConfigError("dataset.generator must be a non-empty string")
    params = _require_mapping(dataset.get("params", {}) or {}, "dataset.params")
    params = dict(params)
    # SS13.4 seed derivation rule: dataset.params.seed defaults to experiment.seed
    # (generate_dataset_id is deterministic only when params['seed'] is set).
    params.setdefault("seed", seed)
    tags = dataset.get("tags")
    if tags is None:
        tags = ["experiment", name.strip()]  # H-8: run-scoped tags by default
    if not isinstance(tags, list):
        raise ConfigError(f"dataset.tags must be a list, got {type(tags).__name__}")
    config["dataset"] = {
        "generator": generator.strip(),
        "params": params,
        "persist": bool(dataset.get("persist", True)),
        "tags": tags,
        "ttl_seconds": dataset.get("ttl_seconds"),
    }

    training = _require_mapping(cfg.get("training", {}) or {}, "training block")
    _reject_unknown_keys(training, TRAINING_KEYS, "training")
    training_params = _require_mapping(training.get("params", {}) or {}, "training.params")
    config["training"] = {
        # Experiment runs default to a clean-launch start (SS6.3 drives start with
        # start_fresh: true); YAML may opt out for continual-training experiments.
        "start_fresh": bool(training.get("start_fresh", True)),
        "epochs": training.get("epochs"),
        "params": dict(training_params),
    }
    return config


# --------------------------------------------------------------------------- #
# endpoint resolution (RUN_DIR/ports.json is the launcher's contract, SS6.4)
# --------------------------------------------------------------------------- #


def resolve_endpoints(run_dir: Path, data_url_arg: Optional[str], cascor_url_arg: Optional[str]) -> Tuple[str, str, Dict[str, Any]]:
    """Resolve the juniper-data and cascor base URLs (CLI override > ports.json)."""
    ports: Dict[str, Any] = {}
    ports_file = run_dir / "ports.json"
    if ports_file.is_file():
        try:
            ports = json.loads(ports_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigError(f"cannot parse {ports_file}: {exc}") from exc
        if not isinstance(ports, dict):
            raise ConfigError(f"{ports_file} must contain a JSON object")

    data_url = data_url_arg or ports.get("data_url") or (f"http://127.0.0.1:{ports['data']}" if ports.get("data") else None)
    cascor_url = cascor_url_arg or (f"http://127.0.0.1:{ports['cascor']}" if ports.get("cascor") else None)
    if not data_url:
        raise ConfigError(f"cannot resolve the juniper-data URL: pass --data-url or provide {ports_file} with a 'data'/'data_url' entry")
    if not cascor_url:
        raise ConfigError(f"cannot resolve the cascor URL: pass --cascor-url or provide {ports_file} with a 'cascor' entry")
    return str(data_url).rstrip("/"), str(cascor_url).rstrip("/"), ports


# --------------------------------------------------------------------------- #
# service interaction phases
# --------------------------------------------------------------------------- #


def wait_for_health(base_url: str, path: str, timeout: float, interval: float = 2.0) -> float:
    """Poll ``base_url``+``path`` until 200 or ``timeout``; return the wait in seconds."""
    started = time.monotonic()
    deadline = started + max(timeout, 0.0)
    last_err = "no attempt made"
    while True:
        try:
            code, _ = _http_json("GET", f"{base_url}{path}", timeout=min(DEFAULT_HTTP_TIMEOUT, max(timeout, 0.1)))
            if code == 200:
                return time.monotonic() - started
            last_err = f"HTTP {code}"
        except ServiceUnreachable as exc:
            last_err = str(exc)
        if time.monotonic() >= deadline:
            raise ServiceUnreachable(f"{base_url}{path} not healthy after {timeout:.1f}s (last: {last_err})")
        time.sleep(min(interval, 0.25 if timeout < 5 else interval))


def preflight_generator(data_url: str, generator: str) -> Dict[str, Any]:
    """SS5.6 rule 4: the generator must exist AND report ``available: true`` before the run starts."""
    code, payload = _http_json("GET", f"{data_url}/v1/generators")
    if code != 200:
        raise RunFailed(f"GET /v1/generators -> HTTP {code}: {_detail(payload)}")
    entries = payload if isinstance(payload, list) else []
    by_name = {entry.get("name"): entry for entry in entries if isinstance(entry, dict)}
    entry = by_name.get(generator)
    if entry is None:
        known = ", ".join(sorted(k for k in by_name if isinstance(k, str)))
        raise ConfigError(f"dataset.generator '{generator}' is not registered on the run's juniper-data (known: {known})")
    if not entry.get("available", False):
        raise ConfigError(f"dataset.generator '{generator}' is registered but unavailable on this host (missing optional dependency; see GET /v1/generators for the install hint)")
    return entry


def create_dataset(data_url: str, dataset_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """``POST /v1/datasets`` on the run's juniper-data; returns the CreateDatasetResponse body."""
    body: Dict[str, Any] = {
        "generator": dataset_cfg["generator"],
        "params": dataset_cfg["params"],
        "persist": dataset_cfg["persist"],
        "tags": dataset_cfg["tags"],
    }
    if dataset_cfg.get("ttl_seconds") is not None:
        body["ttl_seconds"] = dataset_cfg["ttl_seconds"]
    code, payload = _http_json("POST", f"{data_url}/v1/datasets", body=body, timeout=120.0)
    if code in (200, 201) and isinstance(payload, dict) and payload.get("dataset_id"):
        return payload
    if code in (400, 422, 501):
        raise ConfigError(f"POST /v1/datasets rejected ({code}): {_detail(payload)}")
    raise RunFailed(f"POST /v1/datasets -> HTTP {code}: {_detail(payload)}")


def stage_dataset(cascor_url: str, dataset_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """G-6: stage a non-spiral dataset via ``POST /v1/training/dataset`` (applied at the next start)."""
    generator = dataset_cfg["generator"]
    alias = STAGEABLE_GENERATOR_ALIASES.get(generator)
    if alias is None:
        raise ConfigError(
            f"generator '{generator}' is not in cascor's staged dataset_type Literal "
            f"(stageable: {', '.join(sorted(STAGEABLE_GENERATOR_ALIASES))}); gaussian/checkerboard need work item W-3 (plan SS11)"
        )
    body = {"dataset_type": alias, "params": dataset_cfg["params"]}
    code, payload = _http_json("POST", f"{cascor_url}/v1/training/dataset", body=body)
    if code == 422:
        raise ConfigError(f"POST /v1/training/dataset rejected (422): {_detail(payload)}")
    if code != 200:
        raise RunFailed(f"POST /v1/training/dataset -> HTTP {code}: {_detail(payload)}")
    return _unwrap(payload) or {}


def start_training(cascor_url: str, config: Dict[str, Any], data_url: str, staged: bool) -> Dict[str, Any]:
    """``POST /v1/training/start``. Spiral runs pass the juniper-data DatasetSource inline; staged runs rely on the pending config."""
    training = config["training"]
    body: Dict[str, Any] = {"start_fresh": training["start_fresh"]}
    if training.get("epochs") is not None:
        body["epochs"] = training["epochs"]
    if training.get("params"):
        body["params"] = training["params"]
    if not staged:
        dataset_cfg = config["dataset"]
        body["dataset"] = {
            "source": "juniper-data",
            "url": data_url,
            "generator": dataset_cfg["generator"],
            "params": dataset_cfg["params"],
        }
    code, payload = _http_json("POST", f"{cascor_url}/v1/training/start", body=body, timeout=60.0)
    if code == 422:
        raise ConfigError(f"POST /v1/training/start rejected (422 -- TrainingParams is extra='forbid'): {_detail(payload)}")
    if code != 200:
        raise RunFailed(f"POST /v1/training/start -> HTTP {code}: {_detail(payload)}")
    return _unwrap(payload) or {}


# --------------------------------------------------------------------------- #
# the drive loop (Q-2: wall-clock budget + stall detector; F-1 metrics sampling)
# --------------------------------------------------------------------------- #


def drive_training(
    cascor_url: str,
    series_path: Path,
    poll_interval: float,
    stall_seconds: float,
    max_wall_seconds: float,
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Poll ``/v1/training/status`` to a terminal state; sample ``/metrics`` each poll.

    Returns ``(outcome, last_status_data, loop_stats)`` with outcome one of
    ``succeeded`` / ``failed`` / ``stalled`` / ``timed_out``.
    """
    started = time.monotonic()
    deadline = started + max_wall_seconds
    last_epoch: Optional[int] = None
    last_progress = started
    consecutive_errors = 0
    polls = 0
    sampling_errors = 0
    sampling_error_logged = False
    last_data: Dict[str, Any] = {}

    series_path.parent.mkdir(parents=True, exist_ok=True)
    with series_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(SERIES_CSV_COLUMNS)
        while True:
            try:
                code, payload = _http_json("GET", f"{cascor_url}/v1/training/status")
                consecutive_errors = 0
            except ServiceUnreachable:
                consecutive_errors += 1
                if consecutive_errors >= CONSECUTIVE_POLL_ERRORS_MAX:
                    raise
                time.sleep(poll_interval)
                continue
            if code >= 500:
                raise RunFailed(f"GET /v1/training/status -> HTTP {code}: {_detail(payload)}")
            data = _unwrap(payload)
            if isinstance(data, dict):
                last_data = data
            polls += 1

            fsm = str(((last_data.get("state_machine") or {}).get("status")) or "").upper()
            monitor = last_data.get("monitor") or {}
            epoch = monitor.get("current_epoch")
            hidden = monitor.get("current_hidden_units")

            samples: Dict[str, float] = {}
            try:
                samples = parse_metric_samples(_http_text(f"{cascor_url}/metrics"))
            except (ServiceUnreachable, RunFailed) as exc:
                sampling_errors += 1
                if not sampling_error_logged:
                    log.warning("metrics sampling degraded (%s) -- continuing; is JUNIPER_CASCOR_METRICS_ENABLED=true? (G-3)", exc)
                    sampling_error_logged = True
            writer.writerow([f"{time.time():.3f}", fsm, epoch, hidden, *[samples.get(fam, "") for fam in METRIC_FAMILIES]])
            handle.flush()

            if fsm == FSM_TERMINAL_OK:
                outcome = "succeeded"
                break
            if fsm == FSM_TERMINAL_FAIL:
                outcome = "failed"
                break
            now = time.monotonic()
            if isinstance(epoch, int) and epoch != last_epoch:
                last_epoch = epoch
                last_progress = now
            elif now - last_progress > stall_seconds:
                log.error("no current_epoch progress for %.1fs (stall threshold %.1fs) -- outcome: stalled (Q-2)", now - last_progress, stall_seconds)
                outcome = "stalled"
                break
            if now >= deadline:
                log.error("wall-clock budget %.1fs exhausted -- outcome: timed_out (Q-2)", max_wall_seconds)
                outcome = "timed_out"
                break
            time.sleep(poll_interval)

    stats = {
        "polls": polls,
        "metrics_sampling_errors": sampling_errors,
        "final_epoch": last_epoch,
        "wall_seconds": round(time.monotonic() - started, 3),
    }
    return outcome, last_data, stats


# --------------------------------------------------------------------------- #
# result collection (SS6.3 step 5 -> artifacts/results/)
# --------------------------------------------------------------------------- #


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_boundary(path_base: Path, boundary: Dict[str, Any]) -> Path:
    """Persist the decision-boundary payload as ``.npz`` (numpy lazily imported; JSON fallback)."""
    try:
        import numpy as np  # noqa: PLC0415 - lazy: the only numpy-touching artifact (SS6.3 deps note)
    except ImportError:
        json_path = path_base.with_suffix(".json")
        _write_json(json_path, boundary)
        log.warning("numpy unavailable -- wrote %s instead of .npz", json_path.name)
        return json_path
    arrays: Dict[str, Any] = {}
    scalars: Dict[str, Any] = {}
    for key, value in boundary.items():
        if isinstance(value, (list, tuple)):
            try:
                arrays[key] = np.asarray(value)
                continue
            except (ValueError, TypeError):
                pass
        scalars[key] = value
    npz_path = path_base.with_suffix(".npz")
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    if scalars:
        arrays["_scalars_json"] = np.frombuffer(json.dumps(scalars, default=str).encode("utf-8"), dtype=np.uint8)
    with npz_path.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    return npz_path


def collect_results(cascor_url: str, config: Dict[str, Any], results_dir: Path, run_label: str) -> Tuple[List[Path], List[Dict[str, str]], Dict[str, Any]]:
    """Fetch the SS6.3 step-5 result payloads. Essential failures are flagged; the rest degrade."""
    outputs = config["outputs"]
    artifacts: List[Path] = []
    errors: List[Dict[str, str]] = []
    extras: Dict[str, Any] = {}

    def _fetch(label: str, url: str, essential: bool) -> Optional[Any]:
        try:
            code, payload = _http_json("GET", url, timeout=60.0)
        except ServiceUnreachable as exc:
            errors.append({"artifact": label, "essential": str(essential).lower(), "error": str(exc)})
            return None
        if code != 200:
            errors.append({"artifact": label, "essential": str(essential).lower(), "error": f"HTTP {code}: {_detail(payload)}"})
            return None
        return _unwrap(payload)

    metrics_final = _fetch("metrics_final", f"{cascor_url}/v1/metrics", essential=True)
    if metrics_final is not None:
        path = results_dir / "metrics_final.json"
        _write_json(path, metrics_final)
        artifacts.append(path)
        extras["metrics_final"] = metrics_final

    history = _fetch("metrics_history", f"{cascor_url}/v1/metrics/history?count={outputs['metrics_history_count']}", essential=True)
    if history is not None:
        path = results_dir / "metrics_history.json"
        _write_json(path, history)
        artifacts.append(path)

    topology = _fetch("topology", f"{cascor_url}/v1/network/topology", essential=False)
    if topology is not None:
        path = results_dir / "topology.json"
        _write_json(path, topology)
        artifacts.append(path)

    network_info = _fetch("network_info", f"{cascor_url}/v1/network", essential=False)
    if isinstance(network_info, dict):
        extras["network_info"] = network_info
        if network_info.get("input_size") == 2:
            resolution = outputs.get("decision_boundary_resolution")
            query = f"?resolution={resolution}" if resolution else ""
            boundary = _fetch("decision_boundary", f"{cascor_url}/v1/decision-boundary{query}", essential=False)
            if isinstance(boundary, dict):
                artifacts.append(_write_boundary(results_dir / "decision_boundary", boundary))

    if outputs.get("snapshot_at_end"):
        try:
            code, payload = _http_json("POST", f"{cascor_url}/v1/snapshots", body={"description": f"experiment {run_label}"}, timeout=120.0)
            if code == 200:
                extras["snapshot"] = _unwrap(payload)
            else:
                errors.append({"artifact": "snapshot", "essential": "false", "error": f"HTTP {code}: {_detail(payload)}"})
        except ServiceUnreachable as exc:
            errors.append({"artifact": "snapshot", "essential": "false", "error": str(exc)})

    return artifacts, errors, extras


def check_g6_shape(dataset_meta: Dict[str, Any], network_info: Optional[Dict[str, Any]], status_data: Dict[str, Any]) -> Dict[str, Any]:
    """G-6 anti-silence assert for staged (non-spiral) runs: the loaded input width must match the generated dataset."""
    expected = dataset_meta.get("n_features")
    actual = None
    if isinstance(network_info, dict):
        actual = network_info.get("input_size")
    if actual is None:
        actual = (status_data.get("training_state") or {}).get("input_size")
    ok = expected is not None and actual is not None and int(expected) == int(actual)
    return {
        "expected_input_size": expected,
        "actual_input_size": actual,
        "ok": bool(ok),
        "note": None if ok else "loaded network input width does not match the requested dataset -- the routes/training.py:75 stale-data class (G-6)",
    }


# --------------------------------------------------------------------------- #
# manifest (SS13.4)
# --------------------------------------------------------------------------- #


def _git_probe(repo_dir: Path) -> Dict[str, Any]:
    def _run(*args: str) -> Optional[str]:
        try:
            proc = subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return proc.stdout.strip() if proc.returncode == 0 else None

    head = _run("rev-parse", "HEAD")
    if head is None:
        return {"path": str(repo_dir), "error": "not a readable git checkout"}
    porcelain = _run("status", "--porcelain")
    return {"path": str(repo_dir), "head_sha": head, "dirty": bool(porcelain)}


def probe_git_repos(ecosystem_root: Path) -> Dict[str, Any]:
    """Best-effort SS13.4 git provenance for every participating repo found on disk."""
    out: Dict[str, Any] = {}
    for repo in MANIFEST_GIT_REPOS:
        repo_dir = ecosystem_root / repo
        if repo_dir.is_dir():
            out[repo] = _git_probe(repo_dir)
    return out


def probe_packages() -> Dict[str, Any]:
    """SS13.4 package provenance: every importable ``juniper-*`` distribution (+ editable source path)."""
    packages: Dict[str, Any] = {}
    try:
        from importlib import metadata
    except ImportError:  # pragma: no cover - importlib.metadata is stdlib on >=3.8
        return packages
    try:
        distributions = list(metadata.distributions())
    except Exception:  # noqa: BLE001 - a broken dist-info must not kill the manifest
        return packages
    for dist in distributions:
        dist_name = (dist.metadata.get("Name") or "").strip()
        if not dist_name.lower().startswith("juniper"):
            continue
        entry: Dict[str, Any] = {"version": dist.version}
        try:
            direct = dist.read_text("direct_url.json")
            if direct:
                parsed = json.loads(direct)
                url = parsed.get("url", "")
                if parsed.get("dir_info", {}).get("editable") and url.startswith("file://"):
                    entry["editable_source"] = url[len("file://"):]
        except Exception:  # noqa: BLE001 - provenance is best-effort
            pass
        packages[dist_name] = entry
    return packages


def _environment_probe() -> Dict[str, Any]:
    nproc = None
    if hasattr(os, "sched_getaffinity"):
        try:
            nproc = len(os.sched_getaffinity(0))
        except OSError:
            nproc = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "nproc": nproc if nproc is not None else os.cpu_count(),
        "thread_env": {var: os.environ.get(var) for var in THREAD_ENV_VARS},
    }


# --------------------------------------------------------------------------- #
# run orchestration
# --------------------------------------------------------------------------- #


def _setup_logging(run_dir: Optional[Path], verbose: bool) -> List[logging.Handler]:
    log.setLevel(logging.DEBUG)
    handlers: List[logging.Handler] = []
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(logging.DEBUG if verbose else logging.INFO)
    stream.setFormatter(fmt)
    handlers.append(stream)
    if run_dir is not None:
        logs_dir = run_dir / "logs"
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(logs_dir / "run_experiment.log", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(fmt)
            handlers.append(file_handler)
        except OSError as exc:
            stream.handle(logging.LogRecord(LOGGER_NAME, logging.WARNING, __file__, 0, f"cannot open run log: {exc}", None, None))
    for handler in handlers:
        log.addHandler(handler)
    return handlers


def _teardown_logging(handlers: List[logging.Handler]) -> None:
    for handler in handlers:
        log.removeHandler(handler)
        try:
            handler.close()
        except OSError:
            pass


def _relative_artifacts(run_dir: Path, paths: List[Path]) -> List[str]:
    rel: List[str] = []
    for path in paths:
        try:
            rel.append(str(path.relative_to(run_dir)))
        except ValueError:
            rel.append(str(path))
    return sorted(rel)


def run(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser()
    run_dir = Path(args.run_dir).expanduser()
    config = load_config(config_path)

    if config["kind"] == "recurrence":
        raise ConfigError("this config is recurrence-shaped ('train:' block); the recurrence drive path lands in Wave 2.3 -- only the cascor path ('training:' block) is implemented")

    if not run_dir.is_dir():
        raise ConfigError(f"--run-dir {run_dir} does not exist (create the run with util/experiment_stack.bash --up first)")

    data_url, cascor_url, ports = resolve_endpoints(run_dir, args.data_url, args.cascor_url)
    max_wall = float(args.max_wall_seconds) if args.max_wall_seconds is not None else config["outputs"]["max_wall_seconds"]

    results_dir = run_dir / "artifacts" / "results"
    plots_dir = run_dir / "artifacts" / "plots"
    config_dir = run_dir / "config"
    for directory in (results_dir, plots_dir, config_dir):
        directory.mkdir(parents=True, exist_ok=True)

    config_copy = config_dir / "experiment.yaml"
    if config_path.resolve() != config_copy.resolve():
        shutil.copyfile(config_path, config_copy)
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()

    run_id = ports.get("run_id") or run_dir.name
    experiment_name = config["experiment"]["name"]
    generator = config["dataset"]["generator"]
    staged_path = generator != "spiral"
    log.info("run %s: experiment '%s' (cascor, generator=%s%s) data=%s cascor=%s", run_id, experiment_name, generator, ", staged G-6 path" if staged_path else "", data_url, cascor_url)

    timings: Dict[str, float] = {}
    outcome = "torn_down_early"
    acceptance_reasons: List[str] = []
    artifacts: List[Path] = [config_copy]
    collect_errors: List[Dict[str, str]] = []
    dataset_response: Dict[str, Any] = {}
    generator_entry: Dict[str, Any] = {}
    status_data: Dict[str, Any] = {}
    loop_stats: Dict[str, Any] = {}
    extras: Dict[str, Any] = {}
    g6: Optional[Dict[str, Any]] = None
    exit_code = EXIT_ACCEPTANCE
    series_path = results_dir / "metrics_series.csv"

    def _phase(name: str, t0: float) -> None:
        timings[name] = round(time.monotonic() - t0, 3)

    total_t0 = time.monotonic()
    try:
        t0 = time.monotonic()
        wait_for_health(data_url, "/v1/health", args.health_timeout)
        wait_for_health(cascor_url, "/v1/health", args.health_timeout)
        _phase("health_wait", t0)

        t0 = time.monotonic()
        generator_entry = preflight_generator(data_url, generator)
        dataset_response = create_dataset(data_url, config["dataset"])
        _phase("dataset_create", t0)
        log.info("dataset ready: dataset_id=%s (generator %s v%s)", dataset_response.get("dataset_id"), generator, generator_entry.get("version"))

        if staged_path:
            t0 = time.monotonic()
            stage_dataset(cascor_url, config["dataset"])
            _phase("stage", t0)

        t0 = time.monotonic()
        start_training(cascor_url, config, data_url, staged=staged_path)
        _phase("start", t0)

        t0 = time.monotonic()
        outcome, status_data, loop_stats = drive_training(
            cascor_url,
            series_path,
            poll_interval=args.poll_interval,
            stall_seconds=args.stall_seconds,
            max_wall_seconds=max_wall,
        )
        _phase("drive", t0)
        if series_path.is_file():
            artifacts.append(series_path)

        t0 = time.monotonic()
        collected, collect_errors, extras = collect_results(cascor_url, config, results_dir, f"{experiment_name} {run_id}")
        artifacts.extend(collected)
        _phase("collect", t0)

        if staged_path:
            meta = dataset_response.get("meta") if isinstance(dataset_response.get("meta"), dict) else {}
            g6 = check_g6_shape(meta, extras.get("network_info"), status_data)
            if not g6["ok"]:
                acceptance_reasons.append("G-6 shape check failed: " + str(g6["note"]))

        if outcome == "succeeded":
            essential_failures = [err for err in collect_errors if err.get("essential") == "true"]
            for err in essential_failures:
                acceptance_reasons.append(f"essential artifact '{err['artifact']}' not collected: {err['error']}")
            if not acceptance_reasons:
                exit_code = EXIT_SUCCESS
            else:
                exit_code = EXIT_ACCEPTANCE
        elif outcome == "failed":
            acceptance_reasons.append("training reached FAILED")
            exit_code = EXIT_RUN_FAILED
        else:  # stalled / timed_out
            acceptance_reasons.append(f"outcome: {outcome}")
            exit_code = EXIT_ACCEPTANCE
    except KeyboardInterrupt:
        outcome = "torn_down_early"
        acceptance_reasons.append("interrupted")
        exit_code = EXIT_ACCEPTANCE
        log.error("interrupted -- writing manifest with outcome torn_down_early")
    except ServiceUnreachable as exc:
        if timings.get("start") is not None and "drive" not in timings:
            # The service vanished mid-drive: record the evidence rather than dying bare.
            outcome = "torn_down_early"
            acceptance_reasons.append(f"service became unreachable mid-run: {exc}")
            exit_code = EXIT_UNREACHABLE
            log.error("%s", exc)
        else:
            acceptance_reasons.append(f"service unreachable during bring-up: {exc}")
            raise
    finally:
        if series_path.is_file() and series_path not in artifacts:
            artifacts.append(series_path)
        timings["total"] = round(time.monotonic() - total_t0, 3)
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "run_id": run_id,
            "suite_id": None,
            "cell_id": None,
            "experiment": {"name": experiment_name, "description": config["experiment"]["description"]},
            "config_sha256": config_sha,
            "config_path": str(config_path),
            "config_copy_path": str(config_copy),
            "dataset": {
                "dataset_id": dataset_response.get("dataset_id"),
                "generator": generator,
                "version": generator_entry.get("version") or (dataset_response.get("meta") or {}).get("generator_version"),
                "params": config["dataset"]["params"],
                "meta": dataset_response.get("meta"),
            },
            "git": probe_git_repos(Path(args.ecosystem_root).expanduser() if args.ecosystem_root else Path(__file__).resolve().parents[2].parent),
            "packages": probe_packages(),
            "environment": _environment_probe(),
            "seeds": {"experiment": config["experiment"]["seed"], "dataset": config["dataset"]["params"].get("seed")},
            "ports": ports,
            "service_urls": {"data": data_url, "cascor": cascor_url},
            "timings": timings,
            "outcome": outcome,
            "acceptance": {"ok": exit_code == EXIT_SUCCESS, "reasons": acceptance_reasons},
            "completion_reason": status_data.get("completion_reason"),
            "drive_loop": loop_stats,
            "metrics_scraped": {
                "grafana_bridge": bool(ports.get("grafana_bridge", False)),
                "target_file": str(run_dir / "artifacts" / "prometheus_target.json"),
                "present": (run_dir / "artifacts" / "prometheus_target.json").is_file(),
            },
            "g6_shape_check": g6,
            "collect_errors": collect_errors,
            "snapshot": extras.get("snapshot"),
            "artifacts": _relative_artifacts(run_dir, artifacts),
            "driver": {
                "wave": "2.2",
                "poll_interval": args.poll_interval,
                "stall_seconds": args.stall_seconds,
                "max_wall_seconds": max_wall,
                "metric_families": list(METRIC_FAMILIES),
                "plots_requested": config["outputs"]["plots"],
                "plots_note": "plot rendering lands in Wave 2.4",
            },
        }
        manifest_path = run_dir / "manifest.json"
        try:
            _write_json(manifest_path, manifest)
        except OSError as exc:
            log.error("cannot write %s: %s", manifest_path, exc)

    _print_summary(run_id, experiment_name, generator, dataset_response, outcome, exit_code, acceptance_reasons, timings, loop_stats, run_dir)
    return exit_code


def _print_summary(
    run_id: str,
    experiment_name: str,
    generator: str,
    dataset_response: Dict[str, Any],
    outcome: str,
    exit_code: int,
    reasons: List[str],
    timings: Dict[str, float],
    loop_stats: Dict[str, Any],
    run_dir: Path,
) -> None:
    print("=" * 68)
    print(f"run_experiment summary -- {run_id}")
    print("=" * 68)
    print(f"experiment : {experiment_name} (cascor)")
    print(f"dataset    : {generator} dataset_id={dataset_response.get('dataset_id')}")
    print(f"outcome    : {outcome}   exit={exit_code}")
    if reasons:
        print(f"reasons    : {'; '.join(reasons)}")
    if loop_stats:
        print(f"drive      : polls={loop_stats.get('polls')} final_epoch={loop_stats.get('final_epoch')} wall={loop_stats.get('wall_seconds')}s sampling_errors={loop_stats.get('metrics_sampling_errors')}")
    print(f"timings    : {json.dumps(timings, sort_keys=True)}")
    print(f"manifest   : {run_dir / 'manifest.json'}")
    print(f"artifacts  : {run_dir / 'artifacts'}")
    print("=" * 68)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_experiment.py",
        description="Drive a single experiment run against a per-run stack from util/experiment_stack.bash (Wave 2.2: cascor service path).",
    )
    parser.add_argument("--config", required=True, help="experiment YAML (SS5.4 schema)")
    parser.add_argument("--run-dir", required=True, help="the launcher's RUN_DIR (SS6.4; must exist)")
    parser.add_argument("--data-url", default=None, help="juniper-data base URL (default: RUN_DIR/ports.json)")
    parser.add_argument("--cascor-url", default=None, help="cascor base URL (default: RUN_DIR/ports.json)")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help=f"status/metrics poll interval seconds (default {DEFAULT_POLL_INTERVAL})")
    parser.add_argument("--stall-seconds", type=float, default=DEFAULT_STALL_SECONDS, help=f"Q-2 stall threshold: no current_epoch progress for this long -> outcome stalled (default {DEFAULT_STALL_SECONDS})")
    parser.add_argument("--max-wall-seconds", type=float, default=None, help=f"Q-2 wall-clock budget override (CLI > YAML outputs.max_wall_seconds > {DEFAULT_MAX_WALL_SECONDS})")
    parser.add_argument("--health-timeout", type=float, default=DEFAULT_HEALTH_TIMEOUT, help=f"health-wait bound per service in seconds (default {DEFAULT_HEALTH_TIMEOUT})")
    parser.add_argument("--ecosystem-root", default=None, help="override the ecosystem root for SS13.4 git provenance probing")
    parser.add_argument("--verbose", action="store_true", help="debug logging on stderr")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on usage errors already
        return int(exc.code or 0)
    run_dir = Path(args.run_dir).expanduser()
    handlers = _setup_logging(run_dir if run_dir.is_dir() else None, args.verbose)
    try:
        return run(args)
    except ConfigError as exc:
        log.error("%s", exc)
        return EXIT_MISUSE
    except ServiceUnreachable as exc:
        log.error("%s", exc)
        return EXIT_UNREACHABLE
    except RunFailed as exc:
        log.error("%s", exc)
        return EXIT_RUN_FAILED
    finally:
        _teardown_logging(handlers)


if __name__ == "__main__":
    sys.exit(main())
