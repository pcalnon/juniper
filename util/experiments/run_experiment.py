#!/usr/bin/env python3
"""run_experiment.py -- single-run experiment driver (Wave 2.2 cascor + Wave 2.3 recurrence service paths).

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
     then stages EVERY generator via ``POST /v1/training/dataset`` (G-6) and asserts the loaded shape
     afterwards -- spiral included since F-P4-1: the inline ``dataset`` source materialized cascor's
     in-process fallback (unit-radius, params ignored) instead of the configured juniper-data dataset,
     so every service spiral run terminated below_threshold with zero hidden units at chance accuracy;
     polls ``GET /v1/training/status`` to ``COMPLETED`` / ``FAILED`` under the Q-2 wall-clock
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

The recurrence path (Wave 2.3, SS6.3 step 4 *recurrence* + SS5.5): ``POST /v1/train`` is
**synchronous** -- the response IS completion (``routers/training.py:37``), so there is no poll loop;
the Q-2 wall-clock budget is enforced as the request's socket timeout (a timeout -> ``timed_out``,
exit 1, distinct from connection failure). Health gate is ``/v1/health/ready``. The driver creates the
dataset on the run's juniper-data first (content-addressed ``dataset_id`` for the SS13.4 manifest) and
drives every phase by ``dataset_id`` ref (H-8: never a bare name). Optional ``POST /v1/predict``
(re-refs the dataset with ``predict.from_dataset_split``, default ``test``) and ``POST /v1/crossval``
(same LMU hyperparameters as the train block, so bench comparability holds -- SS10.4) follow; a
predict/crossval failure is recorded and the run continues to the manifest (acceptance failure,
exit 1) rather than dying mid-evidence. ``outputs.save_model: true`` (G-18: service mode leaves no
model artifact) re-runs the ``juniper-recurrence train`` CLI with ``--dataset <dataset_id>`` + the
identical hyperparameter flags + ``--out .../model.npz`` as an explicit, manifest-recorded extra step
-- the CLI has no ``--params`` flag (``main.py``), so the ``dataset_id`` ref is the only faithful form.

Plots (Wave 2.4, SS8.1): when ``outputs.plots`` requests them, the cascor path renders the SS8.1 set
client-side from the collected payloads via ``plots_cascor.py`` (lazily loaded -- the driver stays
importable without matplotlib): ``dataset`` (the fetched NPZ artifact; 2-feature generators only),
``decision_boundary`` (the collected grid + sample overlay), ``training_history`` (history rows with
hidden-unit-insertion markers), ``candidate_correlation`` (from the driver's own metrics_series.csv --
the sole source), and ``eval_metrics`` (scalar bars). Structurally-unavailable data is a recorded
per-plot SKIP (exit 0); a render error / failed fetch / missing matplotlib on a requested plot is an
acceptance failure (exit 1). The recurrence set (SS8.2, Wave 2.5 -- closes G-5) renders the same way
via ``plots_recurrence.py``: ``dataset_overview`` / ``dt_histogram`` from the fetched 3-D NPZ
(``{X,y,dt,target_dt}_{split}``; ``y_reg_{split}`` preferred when present -- the equities regression
target), ``forecast_vs_truth`` / ``residuals`` from the predict response vs the predict split's
target, ``crossval_folds`` from the CrossValResponse folds, and ``metrics_table``; a disabled or
failed predict/crossval phase is a per-plot SKIP. There is deliberately no recurrence
training-history plot (TrainResponse carries no per-epoch series -- SS8.2 note).

Stats (Wave 2.6, SS8.3): every run also writes ``artifacts/results/stats.json`` + a human-readable
``summary.md`` via ``stats_summary.py`` (stdlib-only) -- identity / dataset-shape / outcome-timing
blocks from the manifest, the cascor candidate-correlation-per-round and step-duration p50/p95 stats
from the driver's own ``metrics_series.csv`` (the sole source; the duration quantiles are honestly
labeled per-poll means -- true per-step quantiles are not recoverable from a sum/count exposition),
the recurrence train/CV/theta/readout block, and the degraded-mode notes. Written for every outcome;
a stats failure is recorded on the manifest (``stats_error``), never fatal.

Wave boundaries (SS14): the ``docs/REFERENCE.md`` operator section is Wave 2.7.

Dependencies: stdlib + PyYAML; numpy is imported lazily only to write ``decision_boundary.npz`` (with a
JSON fallback when absent). HTTP is stdlib ``urllib`` rather than ``requests`` -- lighter than the SS6.3
allowance and redirect-following by default, which is exactly what F-1 requires.

``util/`` is not pre-commit-lint-gated; ``tests/test_run_experiment.py`` is the gate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import logging
import math
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote
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

# SS5.6 driver-enforced YAML surface. ``training:`` selects the cascor path; ``train:`` (with
# optional ``crossval:``/``predict:``) selects the recurrence path (SS5.5).
TOP_LEVEL_BLOCKS = frozenset({"schema_version", "experiment", "service", "dataset", "training", "train", "crossval", "predict", "runtime", "outputs"})
EXPERIMENT_KEYS = frozenset({"name", "description", "seed"})
DATASET_KEYS_CASCOR = frozenset({"generator", "params", "persist", "tags", "ttl_seconds"})
DATASET_KEYS_RECURRENCE = frozenset({"generator", "split", "params", "persist", "tags", "ttl_seconds"})
RECURRENCE_SPLITS = frozenset({"train", "test", "full"})
TRAINING_KEYS = frozenset({"start_fresh", "epochs", "params"})
# SS5.5 train block: the LMU hyperparameters, forwarded verbatim to TrainRequest (rule 5 --
# ranges + the readout-conditional constraints are validated by the live pydantic model; a 422
# surfaces as exit 2 with the server's detail).
TRAIN_KEYS_RECURRENCE = frozenset({"d", "theta", "ridge", "readout", "rff_features", "rff_gamma", "mlp_hidden", "mlp_weight_decay", "mlp_lr", "mlp_max_epochs", "mlp_patience"})
CROSSVAL_KEYS = frozenset({"enabled", "n_folds", "scheme", "embargo", "min_train"})
PREDICT_KEYS = frozenset({"enabled", "from_dataset_split"})
# SS8.1 / SS8.2 plot names. The cascor set renders in Wave 2.4 (plots_cascor.py); the
# recurrence names are validated now and render in Wave 2.5.
CASCOR_PLOT_NAMES = frozenset({"dataset", "decision_boundary", "training_history", "candidate_correlation", "eval_metrics"})
RECURRENCE_PLOT_NAMES = frozenset({"dataset_overview", "dt_histogram", "forecast_vs_truth", "residuals", "crossval_folds", "metrics_table"})
RUNTIME_KEYS = frozenset({"num_processes", "blas_threads", "eval_metrics_enabled"})
OUTPUTS_KEYS = frozenset({"decision_boundary_resolution", "metrics_history_count", "plots", "snapshot_at_end", "max_wall_seconds", "grafana_bridge", "save_model"})
# SS5.6 rule 6: infrastructure is launcher-owned; ``eval_metrics_enabled`` is process-env
# territory (``runtime:``), not a Settings field.
SERVICE_FORBIDDEN_KEYS = frozenset({"host", "port", "juniper_data_url", "eval_metrics_enabled"})

# G-6 staging aliases: juniper-data generator name -> cascor StageDatasetRequest.dataset_type
# Literal member (src/api/models/training.py StageDatasetRequest; the manager maps the
# plurals back and translates gaussian's n_samples to n_samples_per_class -- W-3,
# juniper-cascor#490). Generators outside this map (arc_agi, csv_import, the 3-D
# sequence family) are not cascade-correlation staging targets (plan SS10.3).
STAGEABLE_GENERATOR_ALIASES: Dict[str, str] = {
    "spiral": "spirals",
    "xor": "xor",
    "circles": "circles",
    "moon": "moons",
    "mnist": "mnist",
    "equities": "equities",
    "gaussian": "gaussian",
    "checkerboard": "checkerboard",
}

FSM_TERMINAL_OK = "COMPLETED"
FSM_TERMINAL_FAIL = "FAILED"
# Lifecycle states holding an ACTIVE training run, i.e. the ones a `stop` can clear.
# Deliberately NOT the whole "start is rejected" set: REPLAYING rejects every training
# command (exit is /replay/control) and INVESTIGATING needs /retrain or /resume, so a
# stop there fails and buries the real reason (juniper-cascor state_machine.py:21-52).
FSM_ACTIVE = frozenset({"STARTED", "PAUSED"})
PREEMPT_TIMEOUT_SECONDS = 120.0
PREEMPT_POLL_SECONDS = 2.0

# Drive outcomes that leave the service STILL TRAINING: the driver gave up on the run,
# the run did not give up on itself. `succeeded` / `failed` are already terminal service-side.
TERMINAL_UNSETTLED = frozenset({"stalled", "timed_out"})
#: Budget for the teardown-path stop, deliberately shorter than PREEMPT_TIMEOUT_SECONDS.
#: That one gates a run that has not started yet and can afford to wait; this one runs
#: AFTER the wall budget is already spent, and every second it takes is taken from the
#: margin the manifest write needs before run_suite's `per_run_timeout_seconds` kills the
#: subprocess -- and a kill there records `timed_out` with exit_code null and NO manifest
#: (the failure mode p4/e-c-cascor-noise-robustness.yaml:22-26 raised its timeout to avoid).
TEARDOWN_PREEMPT_TIMEOUT_SECONDS = 30.0

EXIT_SUCCESS = 0
EXIT_ACCEPTANCE = 1
EXIT_MISUSE = 2
EXIT_UNREACHABLE = 3
EXIT_RUN_FAILED = 4

MANIFEST_SCHEMA = "juniper-experiment-manifest/1"
DRIVER_WAVE = "2.6"

# SS13.4 git-provenance repos, probed relative to the ecosystem root (best-effort).
MANIFEST_GIT_REPOS: Tuple[str, ...] = ("juniper-cascor", "juniper-recurrence", "juniper-data", "juniper-data-client", "juniper-deploy", "juniper-ml")
THREAD_ENV_VARS: Tuple[str, ...] = ("CASCOR_NUM_PROCESSES", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")

LOGGER_NAME = "run_experiment"
log = logging.getLogger(LOGGER_NAME)


def _warn_epoch_budget_split(training_params: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Flag ``max_epochs`` set without ``output_epochs`` -- they are NOT the same budget.

    The two keys mean different things on the two paths, and the difference is silent:

    * SERVICE -- ``TrainingParams.max_epochs`` is forwarded to ``fit()`` as the **initial**
      output-training pass budget only. Every later per-round pass reads
      ``self.output_epochs`` (``cascade_correlation.py:4591`` / ``:4768`` / ``:4820``), which falls
      back to ``_PROJECT_MODEL_OUTPUT_EPOCHS = 10000`` when the config leaves it unset
      (``:716``). The network source states it outright at ``:1876-1882``: *"The two therefore
      agree only while a caller leaves max_epochs unset"*.
    * DIRECT CLI -- ``_W11_TRAINING_KEY_MAP`` aliases ``max_epochs -> output_epochs``
      (``main.py:238-249``), so it bounds **every** output pass; an explicit ``output_epochs``
      wins over the alias (``main.py:291-292``).

    So a config carrying only ``max_epochs: N`` runs the CLI at N epochs per output pass and the
    service at N for the first pass and 10000 for every pass after it. On a run that grows 64-128
    units that is a several-fold per-pass asymmetry, and it makes the service arm both slower and
    better-trained than the config appears to ask for. It cost the wide-budget head-to-head
    campaign a rerun to notice (juniper-ml#1143 SS2.2); at a 1-2 unit cap there is only the initial
    pass, so smoke-scale runs cannot surface it.

    This WARNS rather than raises: a service-only run may legitimately want the split, and the
    canonical ``spiral-baseline.yaml`` ships that way. The warning is also recorded on the config
    so the manifest carries it into the run's evidence rather than living only in a log nobody
    re-reads.
    """
    if "max_epochs" in training_params and "output_epochs" not in training_params:
        note = (
            f"training.params.max_epochs={training_params['max_epochs']!r} is set without output_epochs: "
            "on the SERVICE this bounds only the INITIAL output pass (later passes fall back to the "
            "output_epochs default 10000), while the direct CLI aliases max_epochs onto EVERY output "
            "pass. Set BOTH to the same value for a like-for-like budget, or set output_epochs "
            "explicitly to confirm the split is intended (juniper-ml#1143 SS2.2)."
        )
        config.setdefault("validation_warnings", []).append(note)
        log.warning("config: %s", note)


class ConfigError(Exception):
    """Invalid CLI usage or experiment YAML -> exit 2."""


class ServiceUnreachable(Exception):
    """A required service could not be reached -> exit 3."""


class RequestTimeout(ServiceUnreachable):
    """An HTTP request hit its socket timeout.

    Subclass of :class:`ServiceUnreachable` so generic handlers keep working; the
    recurrence train call catches it FIRST -- there a timeout means the Q-2 wall-clock
    budget expired on the synchronous ``POST /v1/train`` (-> ``timed_out``, exit 1),
    not that the service is down.
    """


class RunFailed(Exception):
    """The run reached FAILED or a service answered 5xx -> exit 4."""


# --------------------------------------------------------------------------- #
# HTTP helpers (stdlib urllib; redirect-following GETs per F-1)
# --------------------------------------------------------------------------- #


#: Where to ask whether a run's metrics actually reached Prometheus. Overridable because the
#: experiment host and the compose stack do not always agree on the address.
PROMETHEUS_URL = os.environ.get("JUNIPER_EXP_PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")


def _metrics_scraped(run_dir: Path, run_id: str, bridge: bool) -> Dict[str, Any]:
    """Did this run's metrics actually reach Prometheus? Ask Prometheus, not the filesystem.

    The field this replaces was ``present: prometheus_target.json.is_file()`` — it asserted that a
    JSON file existed, under a key named ``metrics_scraped``. That could not fail: writing the
    target file is the same act that set the flag. It read as "metrics were scraped" and meant
    "we wrote a file", and on 2026-09-01 five bridged PF-1 runs all reported ``present: true``
    while Prometheus held **zero** series for any of them — the target was never discovered inside
    the ~20 s the service lived (file_sd refresh 15 s + scrape 15 s).

    So the two facts are now reported separately and named for what they are:

    ``target_file_written`` — the local act, still useful for debugging a bridge that did nothing.
    ``scrape_confirmed``    — a query against Prometheus for at least one sample carrying this
                              ``run_id``. Falsifiable: it is false exactly when no sample exists.

    Never raises, and never lets an unreachable Prometheus masquerade as a negative result:
    ``scrape_confirmed`` is ``None`` (not ``False``) when the question could not be asked, with the
    reason recorded. "We could not check" and "nothing was scraped" are different findings and must
    not collapse into the same value — that collapse is the defect this function exists to end.
    """
    target = run_dir / "artifacts" / "prometheus_target.json"
    out: Dict[str, Any] = {
        "grafana_bridge": bridge,
        "target_file": str(target),
        "target_file_written": target.is_file(),
        "scrape_confirmed": None,
        "series_found": None,
        "reason": None,
        "prometheus_url": PROMETHEUS_URL,
    }
    if not bridge:
        out["reason"] = "grafana bridge was OFF for this run; nothing was published to scrape"
        out["scrape_confirmed"] = False
        return out
    query = f'count({{__name__=~"juniper_.+", run_id="{run_id}"}})'
    try:
        code, payload = _http_json("GET", f"{PROMETHEUS_URL}/api/v1/query?query={quote(query)}", timeout=10.0)
    except Exception as exc:  # noqa: BLE001 - provenance must never break a run
        out["reason"] = f"could not reach Prometheus at {PROMETHEUS_URL}: {exc}"
        return out
    if code != 200 or not isinstance(payload, dict) or payload.get("status") != "success":
        out["reason"] = f"Prometheus query returned HTTP {code} / status {payload.get('status') if isinstance(payload, dict) else '?'}"
        return out
    result = (payload.get("data") or {}).get("result") or []
    found = int(float(result[0]["value"][1])) if result else 0
    out["series_found"] = found
    out["scrape_confirmed"] = found > 0
    if found == 0:
        out["reason"] = "target file written but Prometheus holds no series for this run_id — discovery/scrape did not complete within the run's lifetime"
    return out


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
        if isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError):
            raise RequestTimeout(f"{method} {url}: timed out: {exc}") from exc
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


def _http_bytes(url: str, timeout: float = 60.0) -> bytes:
    """GET a binary body (the juniper-data NPZ artifact for the dataset plot)."""
    req = urllib.request.Request(url, headers={"Accept": "application/octet-stream"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - loopback experiment services
            return resp.read()
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
            value = float(rest[0])
        except ValueError:
            continue
        # Prometheus can emit NaN / ±Inf for empty gauges; accepting them poisons
        # correlation_per_round / step-duration stats and plot rendering. Skip non-finite.
        if not math.isfinite(value):
            continue
        out[name] = value
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
    allowed_plots = CASCOR_PLOT_NAMES if kind == "cascor" else RECURRENCE_PLOT_NAMES
    bad_plots = [str(name) for name in plots if name not in allowed_plots]
    if bad_plots:
        raise ConfigError(f"unknown plot name(s) for the {kind} path: {', '.join(bad_plots)} (allowed: {', '.join(sorted(allowed_plots))})")
    outputs = {
        "decision_boundary_resolution": outputs_raw.get("decision_boundary_resolution"),
        "metrics_history_count": history_count,
        "plots": plots,
        "snapshot_at_end": bool(outputs_raw.get("snapshot_at_end", False)),
        "max_wall_seconds": float(max_wall),
        "grafana_bridge": bool(outputs_raw.get("grafana_bridge", False)),
        "save_model": bool(outputs_raw.get("save_model", False)),
    }

    config: Dict[str, Any] = {
        "kind": kind,
        "experiment": {"name": name.strip(), "description": experiment.get("description"), "seed": seed},
        "outputs": outputs,
        "raw": cfg,
    }
    if kind == "recurrence":
        dataset = _require_mapping(cfg.get("dataset"), "dataset block") if "dataset" in cfg else None
        if dataset is None:
            raise ConfigError("missing required block for the recurrence path: dataset")
        _reject_unknown_keys(dataset, DATASET_KEYS_RECURRENCE, "dataset")
        generator = dataset.get("generator")
        if not isinstance(generator, str) or not generator.strip():
            raise ConfigError("dataset.generator must be a non-empty string")
        params = dict(_require_mapping(dataset.get("params", {}) or {}, "dataset.params"))
        params.setdefault("seed", seed)
        split = dataset.get("split", "train")
        if split not in RECURRENCE_SPLITS:
            raise ConfigError(f"dataset.split must be one of {sorted(RECURRENCE_SPLITS)}, got {split!r}")
        tags = dataset.get("tags")
        if tags is None:
            tags = ["experiment", name.strip()]
        if not isinstance(tags, list):
            raise ConfigError(f"dataset.tags must be a list, got {type(tags).__name__}")
        config["dataset"] = {
            "generator": generator.strip(),
            "params": params,
            "persist": bool(dataset.get("persist", True)),
            "tags": tags,
            "ttl_seconds": dataset.get("ttl_seconds"),
            "split": split,
        }

        train_block = _require_mapping(cfg.get("train", {}) or {}, "train block")
        _reject_unknown_keys(train_block, TRAIN_KEYS_RECURRENCE, "train")
        config["train"] = dict(train_block)

        crossval_raw = _require_mapping(cfg.get("crossval", {}) or {}, "crossval block")
        _reject_unknown_keys(crossval_raw, CROSSVAL_KEYS, "crossval")
        crossval_enabled = bool(crossval_raw.get("enabled", True)) if "crossval" in cfg else False
        if crossval_enabled:
            n_folds = crossval_raw.get("n_folds")
            if not isinstance(n_folds, int) or isinstance(n_folds, bool) or n_folds < 2:
                raise ConfigError(f"crossval.n_folds must be an integer >= 2 when crossval is enabled, got {n_folds!r}")
        config["crossval"] = {
            "enabled": crossval_enabled,
            "n_folds": crossval_raw.get("n_folds"),
            "scheme": crossval_raw.get("scheme", "expanding"),
            "embargo": crossval_raw.get("embargo", 0),
            "min_train": crossval_raw.get("min_train"),
        }

        predict_raw = _require_mapping(cfg.get("predict", {}) or {}, "predict block")
        _reject_unknown_keys(predict_raw, PREDICT_KEYS, "predict")
        predict_split = predict_raw.get("from_dataset_split", "test")
        if predict_split not in RECURRENCE_SPLITS:
            raise ConfigError(f"predict.from_dataset_split must be one of {sorted(RECURRENCE_SPLITS)}, got {predict_split!r}")
        config["predict"] = {
            "enabled": bool(predict_raw.get("enabled", True)) if "predict" in cfg else False,
            "from_dataset_split": predict_split,
        }
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
    _warn_epoch_budget_split(training_params, config)
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


def resolve_endpoints(run_dir: Path, data_url_arg: Optional[str], app_url_arg: Optional[str], kind: str = "cascor") -> Tuple[str, str, Dict[str, Any]]:
    """Resolve the juniper-data and target-app base URLs (CLI override > ports.json).

    ``kind`` selects which ports.json entry names the app: ``cascor`` or ``recurrence``.
    """
    ports: Dict[str, Any] = {}
    ports_file = run_dir / "ports.json"
    if ports_file.is_file():
        try:
            ports = json.loads(ports_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigError(f"cannot parse {ports_file}: {exc}") from exc
        if not isinstance(ports, dict):
            raise ConfigError(f"{ports_file} must contain a JSON object")

    app_key = "cascor" if kind == "cascor" else "recurrence"
    data_url = data_url_arg or ports.get("data_url") or (f"http://127.0.0.1:{ports['data']}" if ports.get("data") else None)
    app_url = app_url_arg or (f"http://127.0.0.1:{ports[app_key]}" if ports.get(app_key) else None)
    if not data_url:
        raise ConfigError(f"cannot resolve the juniper-data URL: pass --data-url or provide {ports_file} with a 'data'/'data_url' entry")
    if not app_url:
        raise ConfigError(f"cannot resolve the {app_key} URL: pass --{app_key}-url or provide {ports_file} with a '{app_key}' entry")
    return str(data_url).rstrip("/"), str(app_url).rstrip("/"), ports


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
        # Consume the hint rather than pointing at the response we are already holding. W-4 put
        # `install_hint` on GeneratorInfo precisely so a caller could say what to install; the
        # driver was still telling an operator to go and make the same call by hand.
        #
        # Absent is normal, not an error: juniper-data returns None for the thirteen numpy-only
        # synthetics (they declare no hook), and a juniper-data older than the field returns no
        # key at all — as of 2026-08-26 the newest RELEASE (v0.11.0) predates it, so on a
        # released deployment this always falls back. The pointer stays as that fallback.
        hint = entry.get("install_hint")
        remedy = hint.strip() if isinstance(hint, str) and hint.strip() else "see GET /v1/generators for the install hint"
        raise ConfigError(f"dataset.generator '{generator}' is registered but unavailable on this host (missing optional dependency): {remedy}")
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
    """G-6: stage the dataset via ``POST /v1/training/dataset`` (applied at the next start; spiral included since F-P4-1)."""
    generator = dataset_cfg["generator"]
    alias = STAGEABLE_GENERATOR_ALIASES.get(generator)
    if alias is None:
        raise ConfigError(
            f"generator '{generator}' is not in cascor's staged dataset_type Literal "
            f"(stageable: {', '.join(sorted(STAGEABLE_GENERATOR_ALIASES))}); arc_agi/csv_import and the 3-D sequence generators are not cascade-correlation staging targets (plan SS10.3)"
        )
    body = {"dataset_type": alias, "params": dataset_cfg["params"]}
    code, payload = _http_json("POST", f"{cascor_url}/v1/training/dataset", body=body)
    if code == 422:
        raise ConfigError(f"POST /v1/training/dataset rejected (422): {_detail(payload)}")
    if code != 200:
        raise RunFailed(f"POST /v1/training/dataset -> HTTP {code}: {_detail(payload)}")
    return _unwrap(payload) or {}


def _training_fsm(cascor_url: str) -> str:
    """Current lifecycle status name, uppercased; ``""`` when unreadable."""
    try:
        _code, payload = _http_json("GET", f"{cascor_url}/v1/training/status")
    except (ServiceUnreachable, RunFailed):
        return ""
    data = _unwrap(payload)
    if not isinstance(data, dict):
        return ""
    return str(((data.get("state_machine") or {}).get("status")) or "").upper()


def preempt_training(cascor_url: str, timeout: float = PREEMPT_TIMEOUT_SECONDS, label: str = "retrying start") -> bool:
    """``POST /v1/training/stop`` an active run, then wait for it to leave that state.

    Returns True when the lifecycle is startable again, False otherwise. Never raises:
    a failed preemption falls back to surfacing the original 409.

    ``label`` names what the caller does next, because the two callers do different things
    and the log line is read as evidence: the 409-on-start path retries the start, the
    teardown path settles the service so collect reads a final network.
    """
    code, payload = _http_json("POST", f"{cascor_url}/v1/training/stop", body={}, timeout=60.0)
    if code != 200:
        log.error("POST /v1/training/stop -> HTTP %s: %s", code, _detail(payload))
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        fsm = _training_fsm(cascor_url)
        if fsm and fsm not in FSM_ACTIVE:
            log.info("preempted the in-flight session -- lifecycle is %s, %s", fsm, label)
            return True
        time.sleep(PREEMPT_POLL_SECONDS)
    log.error("in-flight session did not leave %s within %.0fs of the stop", "/".join(sorted(FSM_ACTIVE)), timeout)
    return False


def start_training(cascor_url: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """``POST /v1/training/start`` against the staged (pending) dataset config.

    F-P4-1: every generator — spiral included — is staged via ``stage_dataset``
    before this call. The old spiral-only inline ``dataset`` source made cascor
    materialize its in-process fallback spiral (unit-radius, params silently
    ignored) instead of the configured juniper-data dataset, which pinned
    candidate correlation at ~2.7e-4 and terminated every service spiral run
    below_threshold with zero hidden units.

    A 409 gets ONE preemption attempt, and only from an active state.
    ``start_fresh: true`` does not stop a live run — the lifecycle lock is held, so
    the 409 is raised before ``start_fresh`` is ever consulted. After a driver-side
    stall/budget abort the service keeps training, and the naive re-run then dies on
    ``HTTP 409: Training already in progress`` (observed across the R-5 campaign,
    worked around with an ad-hoc attach-poller).

    The discrimination matters: ``routes/training.py:117`` wraps EVERY start failure
    as 409, including "Training data not provided". Preempting on that would paper
    over a real staging bug, so the decision is made on the lifecycle state, not the
    message text. Only ``STARTED`` / ``PAUSED`` are stoppable: ``REPLAYING`` rejects
    every training command (exit is ``/replay/control``) and ``INVESTIGATING`` needs
    ``/retrain`` or ``/resume`` — issuing a stop in either would fail and then mask
    the real reason.
    """
    training = config["training"]
    body: Dict[str, Any] = {"start_fresh": training["start_fresh"]}
    if training.get("epochs") is not None:
        body["epochs"] = training["epochs"]
    if training.get("params"):
        body["params"] = training["params"]
    code, payload = _http_json("POST", f"{cascor_url}/v1/training/start", body=body, timeout=60.0)
    if code == 409:
        fsm = _training_fsm(cascor_url)
        if fsm in FSM_ACTIVE:
            log.warning("POST /v1/training/start -> 409 with lifecycle %s: %s -- preempting", fsm, _detail(payload))
            if preempt_training(cascor_url):
                code, payload = _http_json("POST", f"{cascor_url}/v1/training/start", body=body, timeout=60.0)
        else:
            log.error("POST /v1/training/start -> 409 with lifecycle %r -- not an active run, not preempting", fsm)
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
        extras["metrics_history"] = history

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
                extras["decision_boundary"] = boundary

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


def _load_sibling(filename: str):
    """Load a sibling helper module by file path -- deterministic under both the package
    import (tests: ``util/`` on sys.path) and path-invocation (``python util/experiments/run_experiment.py``)."""
    spec = importlib.util.spec_from_file_location(f"juniper_experiments_{Path(filename).stem}", Path(__file__).with_name(filename))
    if spec is None or spec.loader is None:  # pragma: no cover - the modules ship beside this file
        raise ImportError(f"cannot locate {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_plots_module(filename: str = "plots_cascor.py"):
    """Plot-module loader -- kept as its OWN seam (not folded into ``_load_sibling`` call
    sites) so tests can stub matplotlib-absence here without affecting the stdlib-only
    SS8.3 stats loader; an ImportError unambiguously means matplotlib (or numpy) is
    unavailable."""
    return _load_sibling(filename)


def _read_series_rows(series_path: Path) -> List[Dict[str, str]]:
    """Parse the driver's own metrics_series.csv into DictReader rows (missing/unreadable -> [])."""
    try:
        with series_path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def _emit_stats(manifest: Dict[str, Any], results_dir: Path, run_dir: Path, artifacts: List[Path], kind: str, **stats_inputs: Any) -> None:
    """SS8.3 (Wave 2.6): build + write ``stats.json`` / ``summary.md`` beside the results and
    fold them into the manifest's artifact list. Stats are stdlib-only and deterministic, so
    a failure here is a code bug -- it is recorded on the manifest (``stats_error``) and
    logged loudly, but never costs the manifest write itself."""
    try:
        stats_mod = _load_sibling("stats_summary.py")
        stats = stats_mod.build_stats(manifest, kind=kind, **stats_inputs)
        stats_path = results_dir / "stats.json"
        _write_json(stats_path, stats)
        artifacts.append(stats_path)
        summary_path = results_dir / "summary.md"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(stats_mod.render_summary_md(stats), encoding="utf-8")
        artifacts.append(summary_path)
        manifest["stats_error"] = None
    except Exception as exc:  # noqa: BLE001 - stats must never cost the manifest
        log.error("stats/summary rendering failed: %s", exc)
        manifest["stats_error"] = str(exc)
    manifest["artifacts"] = _relative_artifacts(run_dir, artifacts)


def _render_cascor_plots(
    config: Dict[str, Any],
    plots_dir: Path,
    series_path: Path,
    extras: Dict[str, Any],
    dataset_response: Dict[str, Any],
    data_url: str,
    title: str,
) -> Tuple[Dict[str, Any], List[str], List[Path]]:
    """Render the requested SS8.1 plots client-side from already-collected payloads.

    Returns ``(record, acceptance_errors, written_paths)``. A plot whose data is
    structurally unavailable (non-2-D input, eval metrics disabled, degraded sampling)
    is a recorded SKIP, not a failure; a render exception, a failed payload fetch, or
    missing matplotlib on a REQUESTED plot is an acceptance error.
    """
    requested = [str(name) for name in config["outputs"]["plots"]]
    record: Dict[str, Any] = {"requested": requested, "rendered": [], "skipped": []}
    errors: List[str] = []
    written: List[Path] = []
    if not requested:
        return record, errors, written
    try:
        plots = _load_plots_module()
    except ImportError as exc:
        record["skipped"] = [{"name": name, "reason": "matplotlib unavailable"} for name in requested]
        errors.append(f"plots requested but matplotlib is unavailable: {exc}")
        return record, errors, written

    meta = dataset_response.get("meta") if isinstance(dataset_response.get("meta"), dict) else {}
    npz_data: Optional[Dict[str, Any]] = None

    def _skip(name: str, reason: str) -> None:
        record["skipped"].append({"name": name, "reason": reason})
        log.warning("plot %s skipped: %s", name, reason)

    def _done(name: str, path: Path) -> None:
        record["rendered"].append(name)
        written.append(path)
        log.info("plot rendered: %s", path.name)

    def _fetch_npz() -> Optional[Dict[str, Any]]:
        raw = _http_bytes(f"{data_url}/v1/datasets/{dataset_response.get('dataset_id')}/artifact")
        return plots.load_npz_bytes(raw)

    for name in requested:
        try:
            if name == "dataset":
                if meta.get("n_features") != 2:
                    _skip(name, f"not applicable: n_features={meta.get('n_features')} (2-feature generators only)")
                    continue
                if npz_data is None:
                    npz_data = _fetch_npz()
                _done(name, plots.render_dataset(npz_data, title, plots_dir / "dataset.png"))
            elif name == "decision_boundary":
                boundary = extras.get("decision_boundary")
                if not isinstance(boundary, dict):
                    _skip(name, "decision-boundary payload unavailable (non-2-D input, or collection failed)")
                    continue
                if npz_data is None and meta.get("n_features") == 2:
                    try:
                        npz_data = _fetch_npz()
                    except (ServiceUnreachable, RunFailed) as exc:
                        log.warning("boundary overlay dataset fetch failed (%s) -- plotting the grid only", exc)
                _done(name, plots.render_decision_boundary(boundary, npz_data, title, plots_dir / "decision_boundary.png"))
            elif name == "training_history":
                rows = extras.get("metrics_history")
                if not isinstance(rows, list) or not rows:
                    _skip(name, "metrics history unavailable or empty")
                    continue
                _done(name, plots.render_training_history(rows, title, plots_dir / "training_history.png"))
            elif name == "candidate_correlation":
                if not series_path.is_file():
                    _skip(name, "metrics_series.csv missing")
                    continue
                with series_path.open("r", encoding="utf-8", newline="") as handle:
                    series_rows = list(csv.DictReader(handle))
                _done(name, plots.render_candidate_correlation(series_rows, title, plots_dir / "candidate_correlation.png"))
            elif name == "eval_metrics":
                metrics_final = extras.get("metrics_final")
                if not isinstance(metrics_final, dict):
                    _skip(name, "metrics_final unavailable")
                    continue
                _done(name, plots.render_eval_metrics(metrics_final, title, plots_dir / "eval_metrics.png"))
            else:  # pragma: no cover - load_config validates plot-name membership
                _skip(name, "unknown plot name")
        except ValueError as exc:
            # The renderer's no-renderable-data contract: an applicability skip, never a run failure.
            _skip(name, str(exc))
        except (ServiceUnreachable, RunFailed) as exc:
            _skip(name, f"payload fetch failed: {exc}")
            errors.append(f"plot {name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - a render bug must not kill the run's evidence
            _skip(name, f"render error: {exc}")
            errors.append(f"plot {name} render error: {exc}")
    return record, errors, written


def _render_recurrence_plots(
    config: Dict[str, Any],
    plots_dir: Path,
    dataset_response: Dict[str, Any],
    data_url: str,
    train_summary: Optional[Dict[str, Any]],
    predict_payload: Optional[Dict[str, Any]],
    crossval_payload: Optional[Dict[str, Any]],
    title: str,
) -> Tuple[Dict[str, Any], List[str], List[Path]]:
    """Render the requested SS8.2 recurrence plots (Wave 2.5, closes G-5).

    Same contract as :func:`_render_cascor_plots`: structurally-unavailable data (a
    disabled/failed predict or crossval phase, a non-Delta-t artifact) is a recorded
    SKIP; a render exception, failed artifact fetch, or missing matplotlib on a
    REQUESTED plot is an acceptance error.
    """
    requested = [str(name) for name in config["outputs"]["plots"]]
    record: Dict[str, Any] = {"requested": requested, "rendered": [], "skipped": []}
    errors: List[str] = []
    written: List[Path] = []
    if not requested:
        return record, errors, written
    try:
        plots = _load_plots_module("plots_recurrence.py")
    except ImportError as exc:
        record["skipped"] = [{"name": name, "reason": "matplotlib unavailable"} for name in requested]
        errors.append(f"plots requested but matplotlib is unavailable: {exc}")
        return record, errors, written

    dataset_split = config["dataset"]["split"]
    predict_split = config["predict"]["from_dataset_split"]
    npz_data: Optional[Dict[str, Any]] = None

    def _skip(name: str, reason: str) -> None:
        record["skipped"].append({"name": name, "reason": reason})
        log.warning("plot %s skipped: %s", name, reason)

    def _done(name: str, path: Path) -> None:
        record["rendered"].append(name)
        written.append(path)
        log.info("plot rendered: %s", path.name)

    def _npz() -> Dict[str, Any]:
        nonlocal npz_data
        if npz_data is None:
            raw = _http_bytes(f"{data_url}/v1/datasets/{dataset_response.get('dataset_id')}/artifact")
            npz_data = plots.load_npz_bytes(raw)
        return npz_data

    for name in requested:
        try:
            if name == "dataset_overview":
                _done(name, plots.render_dataset_overview(_npz(), dataset_split, title, plots_dir / "dataset_overview.png"))
            elif name == "dt_histogram":
                _done(name, plots.render_dt_histogram(_npz(), dataset_split, title, plots_dir / "dt_histogram.png"))
            elif name == "forecast_vs_truth":
                if not isinstance(predict_payload, dict):
                    _skip(name, "predict phase disabled or failed -- no predictions to plot")
                    continue
                bundle = _npz()
                y_true = bundle[plots.resolve_target_key(bundle, predict_split)]
                _done(name, plots.render_forecast_vs_truth(predict_payload.get("predictions"), y_true, title, plots_dir / "forecast_vs_truth.png"))
            elif name == "residuals":
                if not isinstance(predict_payload, dict):
                    _skip(name, "predict phase disabled or failed -- no predictions to plot")
                    continue
                bundle = _npz()
                y_true = bundle[plots.resolve_target_key(bundle, predict_split)]
                target_dt = bundle.get(f"target_dt_{predict_split}")
                _done(name, plots.render_residuals(predict_payload.get("predictions"), y_true, target_dt, title, plots_dir / "residuals.png"))
            elif name == "crossval_folds":
                if not isinstance(crossval_payload, dict):
                    _skip(name, "crossval phase disabled or failed -- no folds to plot")
                    continue
                _done(name, plots.render_crossval_folds(crossval_payload, title, plots_dir / "crossval_folds.png"))
            elif name == "metrics_table":
                if not isinstance(train_summary, dict) or not isinstance(train_summary.get("final_metrics"), dict):
                    _skip(name, "train final_metrics unavailable")
                    continue
                _done(name, plots.render_metrics_table(train_summary["final_metrics"], crossval_payload, title, plots_dir / "metrics_table.png"))
            else:  # pragma: no cover - load_config validates plot-name membership
                _skip(name, "unknown plot name")
        except ValueError as exc:
            _skip(name, str(exc))
        except (ServiceUnreachable, RunFailed) as exc:
            _skip(name, f"payload fetch failed: {exc}")
            errors.append(f"plot {name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - a render bug must not kill the run's evidence
            _skip(name, f"render error: {exc}")
            errors.append(f"plot {name} render error: {exc}")
    return record, errors, written


def check_g6_shape(dataset_meta: Dict[str, Any], network_info: Optional[Dict[str, Any]], status_data: Dict[str, Any]) -> Dict[str, Any]:
    """G-6 anti-silence assert for staged runs (every cascor generator since F-P4-1): the loaded input width must match the generated dataset."""
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

    if not run_dir.is_dir():
        raise ConfigError(f"--run-dir {run_dir} does not exist (create the run with util/experiment_stack.bash --up first)")

    if config["kind"] == "recurrence":
        return _run_recurrence(args, config, config_path, run_dir)
    return _run_cascor(args, config, config_path, run_dir)


def _stall_window_is_inert(stall_seconds: float, max_wall_seconds: float) -> bool:
    """True when the wall budget ends the run before the stall window can elapse.

    Both Q-2 knobs are resolved here and nowhere else, which makes this the only place
    their INTERACTION is visible: a suite sets `stall_seconds`, the budget arrives from
    `outputs.max_wall_seconds` (possibly inherited from a base config), and neither
    layer can see the other. `pf3-cascor-pool-scaling` shipped `stall_seconds: 1200`
    against a 600 s inherited budget for exactly that reason — its stall guard could
    never fire, and a healthy long candidate phase was labelled `timed_out` instead of
    `stalled`: a different wrong label, not protection.

    Reported, never fatal. The run is still valid — only its stall guard is weaker than
    declared — and refusing to start would destroy a legitimate experiment over a
    configuration smell. The manifest carries the finding so the evidence says so too.
    """
    return stall_seconds >= max_wall_seconds


def _run_cascor(args: argparse.Namespace, config: Dict[str, Any], config_path: Path, run_dir: Path) -> int:
    data_url, cascor_url, ports = resolve_endpoints(run_dir, args.data_url, args.cascor_url, kind="cascor")
    max_wall = float(args.max_wall_seconds) if args.max_wall_seconds is not None else config["outputs"]["max_wall_seconds"]
    stall_inert = _stall_window_is_inert(float(args.stall_seconds), float(max_wall))
    if stall_inert:
        log.warning(
            "stall window %.0fs >= wall budget %.0fs -- the Q-2 stall detector can NEVER fire; a healthy long candidate phase will be recorded 'timed_out' rather than 'stalled'. Raise outputs.max_wall_seconds (or execution.max_wall_seconds in a suite) above the stall window.",
            float(args.stall_seconds),
            float(max_wall),
        )

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
    # F-P4-1: spiral joins the staged G-6 path — the inline dataset source made
    # cascor substitute its degenerate in-process fallback for the configured
    # juniper-data dataset. Every cascor-path generator now stages.
    log.info("run %s: experiment '%s' (cascor, generator=%s, staged G-6 path) data=%s cascor=%s", run_id, experiment_name, generator, data_url, cascor_url)

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
    teardown_preempt: Dict[str, Any] = {"attempted": False, "settled": None}
    plots_record: Dict[str, Any] = {"requested": list(config["outputs"]["plots"]), "rendered": [], "skipped": []}
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

        t0 = time.monotonic()
        stage_dataset(cascor_url, config["dataset"])
        _phase("stage", t0)

        t0 = time.monotonic()
        start_training(cascor_url, config)
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

        # A `stalled` / `timed_out` cell leaves the service TRAINING -- the driver gave up on
        # the run, the run did not give up on itself. Two costs follow, and both are the
        # driver's to pay. `collect_results` below samples /v1/metrics, /v1/network and
        # /v1/network/topology off a network that is still recruiting units, so the "final"
        # evidence is a smear across an unknown interval rather than a final state; and the
        # only stop left is experiment_stack.bash's teardown SIGTERM on a 10s grace, which
        # cascor#589 made safe but which no campaign has exercised (T6's 23 inter-cell stops
        # all landed 2-7s AFTER `Training ended`, so only the idle path was proven -- see
        # reports/stop-during-training-2026-08-25/). A graceful stop first settles both.
        #
        # Best-effort by construction: `preempt_training` never raises, and a refused or slow
        # stop degrades to exactly the behaviour that shipped before this block. Only the
        # cascor path gets this -- the recurrence path's `POST /v1/train` is synchronous
        # against a service with no /v1/training/stop lifecycle to call.
        if outcome in TERMINAL_UNSETTLED:
            t0 = time.monotonic()
            settled = preempt_training(cascor_url, timeout=TEARDOWN_PREEMPT_TIMEOUT_SECONDS, label="settling before collect")
            _phase("teardown_preempt", t0)
            teardown_preempt = {"attempted": True, "settled": settled}
            if not settled:
                log.warning(
                    "outcome %s: the service did not settle within %.0fs -- collect samples a live network and teardown falls back to SIGTERM",
                    outcome,
                    TEARDOWN_PREEMPT_TIMEOUT_SECONDS,
                )

        t0 = time.monotonic()
        collected, collect_errors, extras = collect_results(cascor_url, config, results_dir, f"{experiment_name} {run_id}")
        artifacts.extend(collected)
        _phase("collect", t0)

        meta = dataset_response.get("meta") if isinstance(dataset_response.get("meta"), dict) else {}
        g6 = check_g6_shape(meta, extras.get("network_info"), status_data)
        if not g6["ok"]:
            acceptance_reasons.append("G-6 shape check failed: " + str(g6["note"]))

        if config["outputs"]["plots"]:
            t0 = time.monotonic()
            plots_record, plot_errors, plot_paths = _render_cascor_plots(config, plots_dir, series_path, extras, dataset_response, data_url, f"{experiment_name} {run_id}")
            artifacts.extend(plot_paths)
            _phase("plots", t0)
            acceptance_reasons.extend(plot_errors)

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
            # Non-fatal config findings (e.g. the max_epochs/output_epochs budget split) travel
            # with the run's evidence rather than living only in a log nobody re-reads.
            "validation_warnings": config.get("validation_warnings", []),
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
            # Whether the driver stopped a still-training service before collecting. `attempted`
            # false means the outcome was already terminal service-side; `settled` false means
            # collect below sampled a live network -- read the run's numbers accordingly.
            "teardown_preempt": teardown_preempt,
            "metrics_scraped": _metrics_scraped(run_dir, run_id, bool(ports.get("grafana_bridge", False))),
            "g6_shape_check": g6,
            "collect_errors": collect_errors,
            "snapshot": extras.get("snapshot"),
            "artifacts": _relative_artifacts(run_dir, artifacts),
            "driver": {
                "wave": DRIVER_WAVE,
                "poll_interval": args.poll_interval,
                "stall_seconds": args.stall_seconds,
                "max_wall_seconds": max_wall,
                "stall_window_inert": stall_inert,
                "metric_families": list(METRIC_FAMILIES),
                "plots": plots_record,
            },
        }
        _emit_stats(manifest, results_dir, run_dir, artifacts, "cascor", series_rows=_read_series_rows(series_path) if series_path.is_file() else [], metrics_final=extras.get("metrics_final"))
        # Q-1: the resolved-config artifact, written unconditionally alongside the manifest.
        resolved_path = write_resolved_config(config_dir, config, run_id, "cascor", cascor_url)
        if resolved_path is not None:
            manifest["config_resolved_path"] = str(resolved_path)
        manifest_path = run_dir / "manifest.json"
        try:
            _write_json(manifest_path, manifest)
        except OSError as exc:
            log.error("cannot write %s: %s", manifest_path, exc)

    _print_summary(run_id, experiment_name, generator, dataset_response, outcome, exit_code, acceptance_reasons, timings, loop_stats, run_dir, kind="cascor")
    return exit_code


RESOLVED_CONFIG_SCHEMA = "juniper-experiment-resolved/v1"

#: What Q-1 asked for, what this file actually is, and why those differ. Carried IN the
#: artifact rather than only in the plan, because the gap is the thing a reader must not
#: mistake: an ``experiment.resolved.yaml`` that silently omitted the app's own Settings
#: would look authoritative while being partial, which is the hand-reconstruction error
#: class Q-1 was written to kill.
RESOLVED_CONFIG_SCOPE = """Q-1 asked for a fully-resolved config 'dumped from the live Settings object'.
The driver is an HTTP client and never constructs the app's Settings: cascor exposes no
settings endpoint (GET /v1/training/params covers TrainingParams only) and the recurrence
service exposes no equivalent at all. This file therefore records only what can be
VERIFIED, each half tagged with its source, rather than reconstructing anything:

  driver_resolved         - the input YAML after run_experiment's own defaulting. True by
                            construction; this is what the driver acted on.
  service_training_params - the service's own echo of its training parameters, where such
                            an endpoint exists. Authoritative for those fields.

NOT COVERED: app-level Settings (environment, .env, process defaults) are not represented
here. Reading this file as a complete picture of the run's configuration would be wrong."""


def _service_training_params(app_url: Optional[str], app: str) -> Dict[str, Any]:
    """The service's own training-parameter echo, or a stated reason there is none.

    Never raises: this is provenance, and a run must not fail because an optional echo was
    unavailable. A failure is RECORDED, because "we could not read it" and "it was empty"
    must not look the same to a reader.
    """
    if app != "cascor":
        return {"available": False, "reason": f"the {app} service exposes no training-parameters endpoint", "source": None, "params": None}
    if not app_url:
        return {"available": False, "reason": "no service URL was resolved for this run", "source": None, "params": None}
    source = f"{app_url}/v1/training/params"
    try:
        code, payload = _http_json("GET", source, timeout=15.0)
    except Exception as exc:  # noqa: BLE001 - provenance must not break a run
        return {"available": False, "reason": f"GET failed: {exc}", "source": source, "params": None}
    if code == 404:
        # The documented 404: the endpoint requires a live network. A run that failed
        # before network creation legitimately has nothing to report here.
        return {"available": False, "reason": "HTTP 404 - no network existed when the echo was requested", "source": source, "params": None}
    if code != 200 or not isinstance(payload, dict):
        return {"available": False, "reason": f"HTTP {code}", "source": source, "params": None}
    # success_response() wraps the payload in {"data": ...}; keep the inner object when present.
    params = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return {"available": True, "reason": None, "source": source, "params": params}


def write_resolved_config(config_dir: Path, config: Dict[str, Any], run_id: str, app: str, app_url: Optional[str]) -> Optional[Path]:
    """Write ``config/experiment.resolved.yaml`` beside the verbatim copy (Q-1).

    Written from the same ``finally`` that writes the manifest, so every run has one --
    succeeded, failed, stalled or timed_out -- for the same reason the manifest is
    unconditional: a run's provenance is most valuable exactly when the run went wrong.

    Returns the path, or None when it could not be written (logged, never fatal).
    """
    resolved = {
        "_meta": {
            "schema": RESOLVED_CONFIG_SCHEMA,
            "generated_by": "util/experiments/run_experiment.py",
            "run_id": run_id,
            "app": app,
            "scope": RESOLVED_CONFIG_SCOPE,
        },
        "driver_resolved": config,
        "service_training_params": _service_training_params(app_url, app),
    }
    out = config_dir / "experiment.resolved.yaml"
    try:
        out.write_text(yaml.safe_dump(resolved, sort_keys=False), encoding="utf-8")
    except (OSError, yaml.YAMLError) as exc:
        log.error("cannot write %s: %s", out, exc)
        return None
    return out


def _lmu_hyperparams(train_block: Dict[str, Any]) -> Dict[str, Any]:
    """The LMU hyperparameters actually set in the YAML ``train:`` block (unset/None omitted)."""
    return {key: value for key, value in train_block.items() if value is not None}


_SAVE_MODEL_FLAG_MAP = {
    "d": "--d",
    "theta": "--theta",
    "ridge": "--ridge",
    "readout": "--readout",
    "rff_features": "--rff-features",
    "rff_gamma": "--rff-gamma",
    "mlp_hidden": "--mlp-hidden",
    "mlp_weight_decay": "--mlp-weight-decay",
    "mlp_lr": "--mlp-lr",
    "mlp_max_epochs": "--mlp-max-epochs",
    "mlp_patience": "--mlp-patience",
}


def _save_model_rerun(train_block: Dict[str, Any], dataset_id: str, split: str, data_url: str, out_path: Path) -> Dict[str, Any]:
    """G-18: service mode leaves no model artifact, so ``outputs.save_model: true`` re-runs the
    ``juniper-recurrence train`` CLI with ``--dataset <dataset_id>`` (the exact content-addressed
    artifact -- the CLI has no ``--params`` flag, so a generator re-ref would silently use default
    params), the identical hyperparameter flags, and ``--out`` into the run's results dir."""
    cli = shutil.which("juniper-recurrence")
    if cli is None:
        return {"ok": False, "error": "juniper-recurrence CLI not found on PATH (outputs.save_model needs the app env active)"}
    cmd = [cli, "train", "--dataset", str(dataset_id), "--split", str(split), "--out", str(out_path)]
    for key, value in _lmu_hyperparams(train_block).items():
        cmd.extend([_SAVE_MODEL_FLAG_MAP[key], str(value)])
    env = dict(os.environ)
    env["JUNIPER_DATA_URL"] = data_url  # the run's data instance holds the artifact
    env["LD_LIBRARY_PATH"] = ""  # same hygiene the launcher applies to service launches
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env, check=False)  # nosec B603 - cmd built from validated config
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "cmd": cmd, "error": str(exc)}
    result: Dict[str, Any] = {"ok": proc.returncode == 0, "cmd": cmd, "returncode": proc.returncode}
    if proc.returncode != 0:
        result["stderr_tail"] = proc.stderr[-500:]
    return result


def _run_recurrence(args: argparse.Namespace, config: Dict[str, Any], config_path: Path, run_dir: Path) -> int:
    data_url, app_url, ports = resolve_endpoints(run_dir, args.data_url, args.recurrence_url, kind="recurrence")
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
    dataset_cfg = config["dataset"]
    generator = dataset_cfg["generator"]
    log.info("run %s: experiment '%s' (recurrence, generator=%s split=%s) data=%s recurrence=%s", run_id, experiment_name, generator, dataset_cfg["split"], data_url, app_url)

    timings: Dict[str, float] = {}
    outcome = "torn_down_early"
    acceptance_reasons: List[str] = []
    artifacts: List[Path] = [config_copy]
    collect_errors: List[Dict[str, str]] = []
    dataset_response: Dict[str, Any] = {}
    generator_entry: Dict[str, Any] = {}
    train_summary: Optional[Dict[str, Any]] = None
    predict_shape: Optional[List[int]] = None
    predict_full: Optional[Dict[str, Any]] = None
    crossval_summary: Optional[Dict[str, Any]] = None
    crossval_full: Optional[Dict[str, Any]] = None
    save_model_rerun: Optional[Dict[str, Any]] = None
    plots_record: Dict[str, Any] = {"requested": list(config["outputs"]["plots"]), "rendered": [], "skipped": []}
    exit_code = EXIT_ACCEPTANCE

    def _phase(name: str, t0: float) -> None:
        timings[name] = round(time.monotonic() - t0, 3)

    def _aux_phase(label: str, method_url: Tuple[str, str], body: Dict[str, Any], out_name: Optional[str]) -> Optional[Any]:
        """Drive an optional post-train phase; failures are recorded, never fatal (the train
        evidence already exists -- dying here would lose the manifest, the G-18 class)."""
        t0 = time.monotonic()
        try:
            code, payload = _http_json(method_url[0], method_url[1], body=body, timeout=max_wall)
        except ServiceUnreachable as exc:
            _phase(label, t0)
            collect_errors.append({"artifact": label, "essential": "true", "error": str(exc)})
            acceptance_reasons.append(f"{label} failed: {exc}")
            return None
        _phase(label, t0)
        if code != 200:
            detail = f"HTTP {code}: {_detail(payload)}"
            collect_errors.append({"artifact": label, "essential": "true", "error": detail})
            acceptance_reasons.append(f"{label} failed: {detail}")
            return None
        if out_name is not None:
            path = results_dir / out_name
            _write_json(path, payload)
            artifacts.append(path)
        return payload

    total_t0 = time.monotonic()
    try:
        t0 = time.monotonic()
        wait_for_health(data_url, "/v1/health", args.health_timeout)
        wait_for_health(app_url, "/v1/health/ready", args.health_timeout)
        _phase("health_wait", t0)

        t0 = time.monotonic()
        generator_entry = preflight_generator(data_url, generator)
        dataset_response = create_dataset(data_url, dataset_cfg)
        _phase("dataset_create", t0)
        dataset_id = dataset_response.get("dataset_id")
        log.info("dataset ready: dataset_id=%s (generator %s v%s)", dataset_id, generator, generator_entry.get("version"))

        hyper = _lmu_hyperparams(config["train"])
        train_ok = False
        t0 = time.monotonic()
        try:
            code, payload = _http_json("POST", f"{app_url}/v1/train", body={"dataset": {"dataset_id": dataset_id, "split": dataset_cfg["split"]}, **hyper}, timeout=max_wall)
        except RequestTimeout as exc:
            _phase("train", t0)
            log.error("synchronous POST /v1/train exceeded the wall-clock budget %.1fs -- outcome: timed_out (Q-2): %s", max_wall, exc)
            outcome = "timed_out"
            acceptance_reasons.append("outcome: timed_out")
        else:
            _phase("train", t0)
            if code == 422:
                raise ConfigError(f"POST /v1/train rejected (422): {_detail(payload)}")
            if code != 200:
                raise RunFailed(f"POST /v1/train -> HTTP {code}: {_detail(payload)}")
            train_summary = payload if isinstance(payload, dict) else {}
            path = results_dir / "train_response.json"
            _write_json(path, payload)
            artifacts.append(path)
            train_ok = True
            log.info("train complete: n_epochs=%s stopped_reason=%s", train_summary.get("n_epochs"), train_summary.get("stopped_reason"))

        if train_ok:
            outcome = "succeeded"
            if config["predict"]["enabled"]:
                predict_payload = _aux_phase("predict", ("POST", f"{app_url}/v1/predict"), {"dataset": {"dataset_id": dataset_id, "split": config["predict"]["from_dataset_split"]}}, "predict_response.json")
                if isinstance(predict_payload, dict):
                    predict_shape = predict_payload.get("shape")
                    predict_full = predict_payload
            if config["crossval"]["enabled"]:
                crossval_body: Dict[str, Any] = {
                    "dataset": {"dataset_id": dataset_id},
                    "n_folds": config["crossval"]["n_folds"],
                    "scheme": config["crossval"]["scheme"],
                    "embargo": config["crossval"]["embargo"],
                    **hyper,
                }
                if config["crossval"]["min_train"] is not None:
                    crossval_body["min_train"] = config["crossval"]["min_train"]
                crossval_payload = _aux_phase("crossval", ("POST", f"{app_url}/v1/crossval"), crossval_body, "crossval_response.json")
                if isinstance(crossval_payload, dict):
                    crossval_summary = {key: crossval_payload.get(key) for key in ("task_type", "n_folds", "eval_aggregate", "eval_std")}
                    crossval_full = crossval_payload
            if config["outputs"]["save_model"]:
                t0 = time.monotonic()
                model_path = results_dir / "model.npz"
                save_model_rerun = _save_model_rerun(config["train"], str(dataset_id), dataset_cfg["split"], data_url, model_path)
                _phase("save_model", t0)
                if save_model_rerun.get("ok"):
                    if model_path.is_file():
                        artifacts.append(model_path)
                else:
                    acceptance_reasons.append(f"save_model re-run failed: {save_model_rerun.get('error') or save_model_rerun.get('stderr_tail') or save_model_rerun.get('returncode')}")
        if config["outputs"]["plots"]:
            t0 = time.monotonic()
            plots_record, plot_errors, plot_paths = _render_recurrence_plots(config, plots_dir, dataset_response, data_url, train_summary, predict_full, crossval_full, f"{experiment_name} {run_id}")
            artifacts.extend(plot_paths)
            _phase("plots", t0)
            acceptance_reasons.extend(plot_errors)
        if train_ok:
            exit_code = EXIT_SUCCESS if not acceptance_reasons else EXIT_ACCEPTANCE
        else:
            exit_code = EXIT_ACCEPTANCE
    except KeyboardInterrupt:
        outcome = "torn_down_early"
        acceptance_reasons.append("interrupted")
        exit_code = EXIT_ACCEPTANCE
        log.error("interrupted -- writing manifest with outcome torn_down_early")
    except RunFailed as exc:
        outcome = "failed"
        acceptance_reasons.append(str(exc))
        exit_code = EXIT_RUN_FAILED
        log.error("%s", exc)
    except ServiceUnreachable as exc:
        if "dataset_create" in timings:
            outcome = "torn_down_early"
            acceptance_reasons.append(f"service became unreachable mid-run: {exc}")
            exit_code = EXIT_UNREACHABLE
            log.error("%s", exc)
        else:
            acceptance_reasons.append(f"service unreachable during bring-up: {exc}")
            raise
    finally:
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
            # Non-fatal config findings (e.g. the max_epochs/output_epochs budget split) travel
            # with the run's evidence rather than living only in a log nobody re-reads.
            "validation_warnings": config.get("validation_warnings", []),
            "dataset": {
                "dataset_id": dataset_response.get("dataset_id"),
                "generator": generator,
                "version": generator_entry.get("version") or (dataset_response.get("meta") or {}).get("generator_version"),
                "params": config["dataset"]["params"],
                "split": dataset_cfg["split"],
                "meta": dataset_response.get("meta"),
            },
            "git": probe_git_repos(Path(args.ecosystem_root).expanduser() if args.ecosystem_root else Path(__file__).resolve().parents[2].parent),
            "packages": probe_packages(),
            "environment": _environment_probe(),
            "seeds": {"experiment": config["experiment"]["seed"], "dataset": config["dataset"]["params"].get("seed")},
            "ports": ports,
            "service_urls": {"data": data_url, "recurrence": app_url},
            "timings": timings,
            "outcome": outcome,
            "acceptance": {"ok": exit_code == EXIT_SUCCESS, "reasons": acceptance_reasons},
            "completion_reason": None,
            "drive_loop": {},
            "metrics_scraped": _metrics_scraped(run_dir, run_id, bool(ports.get("grafana_bridge", False))),
            "g6_shape_check": None,
            "collect_errors": collect_errors,
            "snapshot": None,
            "train": None if train_summary is None else {key: train_summary.get(key) for key in ("final_metrics", "n_epochs", "stopped_reason", "dataset")},
            "predict": None if predict_shape is None else {"shape": predict_shape},
            "crossval": crossval_summary,
            "save_model_rerun": save_model_rerun,
            "artifacts": _relative_artifacts(run_dir, artifacts),
            "driver": {
                "wave": DRIVER_WAVE,
                "poll_interval": args.poll_interval,
                "stall_seconds": args.stall_seconds,
                "max_wall_seconds": max_wall,
                "metric_families": list(METRIC_FAMILIES),
                "plots": plots_record,
            },
        }
        _emit_stats(manifest, results_dir, run_dir, artifacts, "recurrence", train_summary=train_summary, crossval=crossval_full, train_config=config["train"])
        # Q-1: same artifact on this path. The service half is recorded as unavailable with
        # a reason rather than omitted -- recurrence exposes no training-parameters
        # endpoint, and "there is nothing to read" must be legible as a fact, not a gap.
        resolved_path = write_resolved_config(config_dir, config, run_id, "recurrence", app_url)
        if resolved_path is not None:
            manifest["config_resolved_path"] = str(resolved_path)
        manifest_path = run_dir / "manifest.json"
        try:
            _write_json(manifest_path, manifest)
        except OSError as exc:
            log.error("cannot write %s: %s", manifest_path, exc)

    _print_summary(run_id, experiment_name, generator, dataset_response, outcome, exit_code, acceptance_reasons, timings, {}, run_dir, kind="recurrence")
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
    kind: str = "cascor",
) -> None:
    print("=" * 68)
    print(f"run_experiment summary -- {run_id}")
    print("=" * 68)
    print(f"experiment : {experiment_name} ({kind})")
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
        description="Drive a single experiment run against a per-run stack from util/experiment_stack.bash (cascor + recurrence service paths).",
    )
    parser.add_argument("--config", required=True, help="experiment YAML (SS5.4 cascor / SS5.5 recurrence schema)")
    parser.add_argument("--run-dir", required=True, help="the launcher's RUN_DIR (SS6.4; must exist)")
    parser.add_argument("--data-url", default=None, help="juniper-data base URL (default: RUN_DIR/ports.json)")
    parser.add_argument("--cascor-url", default=None, help="cascor base URL (default: RUN_DIR/ports.json)")
    parser.add_argument("--recurrence-url", default=None, help="recurrence base URL (default: RUN_DIR/ports.json)")
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
