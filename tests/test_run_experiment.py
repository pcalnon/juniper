"""Hermetic tests for ``util/experiments/run_experiment.py`` (Wave 2.2 cascor + Wave 2.3 recurrence paths).

The SS10.6 gate for the experiment driver -- ``util/`` is not pre-commit-lint-gated
(flake8/black scope to ``scripts``+``tests``), so this unittest is the gate. No live
services and no network beyond a loopback stub: a scripted ``http.server`` stands in
for BOTH the run's juniper-data and cascor (their endpoint sets are disjoint). Covers:

* SS5.6 YAML validation: unknown top-level block / unknown keys per block, missing or
  non-integer ``experiment.seed``, missing / out-of-range ``schema_version``, the rule-6
  infra-key rejection (``service.port`` etc.), app-kind resolution (``training:`` vs
  ``train:``; both / neither -> error), and the seed-derivation + default-tags rules;
* the cascor drive loop against the stub: completion, ``FAILED``, the Q-2 stall detector
  and wall-clock budget (CLI ``--max-wall-seconds`` beating YAML ``outputs.max_wall_seconds``),
  and the F-1 arm -- the bare ``/metrics`` sampling GET follows the 307 to ``/metrics/``;
* metrics_series.csv sampling (allowlisted families, labeled + bare exposition lines,
  degraded-but-alive when ``/metrics`` 404s -- the G-3 metrics-disabled trap);
* the G-6 staging path for non-spiral generators (``POST /v1/training/dataset`` with the
  aliased ``dataset_type``, no inline ``dataset`` on start, and the post-run shape assert
  in both its pass and mismatch arms; un-stageable generators name W-3);
* the SS13.4 manifest schema (also written for failed / stalled / timed-out runs) and the
  full SS6.3 exit-code matrix (0/1/2/3/4), including one subprocess arm pinning the real
  ``sys.exit`` wiring (``RedactedEnv`` builds the subprocess env mapping);
* the Wave-2.3 recurrence path: SS5.5 block validation (dataset.split, train/crossval/predict
  keys, crossval n_folds), the synchronous ``POST /v1/train`` drive (200 / 409->4 / 422->2 /
  socket-timeout->``timed_out``), predict + crossval phases (dataset_id refs, hyperparams copied
  into crossval, record-and-continue on failure — including the crossval-fail-continue arm),
  and the G-18 ``outputs.save_model`` re-run (PATH-stubbed ``juniper-recurrence`` CLI:
  --dataset/--split/--out + JUNIPER_DATA_URL env; missing CLI -> acceptance failure);
* cascor essential-collect failure after COMPLETED (exit 1) and mid-drive consecutive poll
  unreachability (exit 3, ``torn_down_early``).
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402  (path-invoked util import)

SCRIPT_PATH = REPO_ROOT / "util" / "experiments" / "run_experiment.py"

try:
    import numpy  # noqa: F401

    HAVE_NUMPY = True
except ImportError:  # pragma: no cover - CI installs numpy; local envs all carry it
    HAVE_NUMPY = False

try:
    import matplotlib  # noqa: F401

    HAVE_MPL = True
except ImportError:  # pragma: no cover - CI installs matplotlib; local envs all carry it
    HAVE_MPL = False

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

FAST_FLAGS = ["--poll-interval", "0.05", "--stall-seconds", "5", "--health-timeout", "2"]


# --------------------------------------------------------------------------- #
# scripted stub server (juniper-data + cascor roles on one loopback listener)
# --------------------------------------------------------------------------- #


class _ScriptedState:
    """Mutable per-test script driving the stub's responses."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str, dict | None]] = []
        self.status_sequence: list[tuple[str, int, int]] = [("STARTED", 1, 0), ("STARTED", 2, 1), ("COMPLETED", 3, 2)]
        self.status_index = 0
        self.increment_epochs = False
        self.auto_epoch = 0
        self.metrics_enabled = True
        self.redirect_hits = 0
        self.n_features = 2
        self.network_input_size = 2
        self.start_status = 200
        self.completion_reason = "max_iterations"
        self.train_status = 200
        self.train_delay = 0.0
        self.predict_status = 200
        self.crossval_status = 200
        self.metrics_final_status = 200
        self.metrics_history_status = 200
        # After this many /v1/training/status responses, drop the listening socket so
        # subsequent polls fail immediately with Connection refused (mid-drive tear-down).
        self.status_die_after: int | None = None
        self.eval_metrics_present = True
        self.artifact_kind = "tabular"
        self.lock = threading.Lock()


_ARTIFACT_CACHE: dict = {}


def _artifact_npz_bytes(kind: str = "tabular") -> bytes:
    """Deterministic NPZ /artifact bodies: 2-feature classification ('tabular') or 3-D Delta-t sequence ('sequence')."""
    if kind not in _ARTIFACT_CACHE:
        import io

        import numpy as np

        rng = np.random.default_rng(0)
        buf = io.BytesIO()
        if kind == "tabular":
            x = rng.normal(size=(40, 2)).astype("float32")
            labels = (x[:, 0] > 0).astype("float32")
            one_hot = np.stack([1 - labels, labels], axis=1)
            np.savez(buf, X_train=x[:32], y_train=one_hot[:32], X_test=x[32:], y_test=one_hot[32:], X_full=x, y_full=one_hot)
        else:  # the _sequence.py contract: {X,y,dt,target_dt}_{split}; leading per-window dt is 0.0
            x = rng.normal(size=(12, 16, 3)).astype("float32")
            y = x[:, -1, 0].astype("float32")
            dt = np.abs(rng.normal(1.0, 0.3, size=(12, 16))).astype("float32")
            dt[:, 0] = 0.0
            target_dt = np.abs(rng.normal(1.0, 0.2, size=12)).astype("float32")
            np.savez(
                buf,
                X_train=x[:8],
                y_train=y[:8],
                dt_train=dt[:8],
                target_dt_train=target_dt[:8],
                X_test=x[8:],
                y_test=y[8:],
                dt_test=dt[8:],
                target_dt_test=target_dt[8:],
                X_full=x,
                y_full=y,
                dt_full=dt,
                target_dt_full=target_dt,
            )
        _ARTIFACT_CACHE[kind] = buf.getvalue()
    return _ARTIFACT_CACHE[kind]


def _envelope(data) -> bytes:
    return json.dumps({"status": "success", "data": data, "meta": {"timestamp": 0.0, "version": "0.6.0"}}).encode("utf-8")


_EXPOSITION = b"""# HELP juniper_cascor_training_loss Current training loss
# TYPE juniper_cascor_training_loss gauge
juniper_cascor_training_loss 0.123
juniper_cascor_training_accuracy_ratio 0.9
juniper_cascor_hidden_units_total 2
juniper_cascor_candidate_correlation{best="true"} 0.87
juniper_cascor_training_step_duration_seconds_sum 1.5
juniper_cascor_training_step_duration_seconds_count 3
juniper_cascor_unrelated_family 99
"""


class _StubHandler(BaseHTTPRequestHandler):
    server: "_StubServer"

    def log_message(self, *args) -> None:  # noqa: D102 - silence the stub
        pass

    def _state(self) -> _ScriptedState:
        return self.server.state

    def _send(self, code: int, body: bytes = b"", content_type: str = "application/json", extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _read_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            return None

    def _record(self, method: str, body: dict | None = None) -> None:
        state = self._state()
        with state.lock:
            state.requests.append((method, self.path.split("?", 1)[0], body))

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        state = self._state()
        path = self.path.split("?", 1)[0]
        self._record("GET")
        if path == "/v1/health":
            self._send(200, json.dumps({"status": "ok"}).encode("utf-8"))
        elif path == "/v1/health/ready":
            self._send(200, json.dumps({"status": "ready"}).encode("utf-8"))
        elif path == "/v1/generators":
            self._send(
                200,
                json.dumps(
                    [
                        {"name": "spiral", "version": "1.2.0", "description": "", "available": True, "schema": {}},
                        {"name": "xor", "version": "1.0.0", "description": "", "available": True, "schema": {}},
                        {"name": "moon", "version": "1.0.0", "description": "", "available": True, "schema": {}},
                        {"name": "gaussian", "version": "1.0.0", "description": "", "available": True, "schema": {}},
                        {"name": "irregular_sine", "version": "1.0.0", "description": "", "available": True, "schema": {}},
                        {"name": "mnist", "version": "1.0.0", "description": "", "available": False, "schema": {}},
                    ]
                ).encode("utf-8"),
            )
        elif path == "/v1/training/status":
            with state.lock:
                if state.status_die_after is not None and state.status_index >= state.status_die_after:
                    state.status_index += 1
                    die = True
                else:
                    die = False
                    if state.increment_epochs:
                        state.auto_epoch += 1
                        fsm, epoch, hidden = "STARTED", state.auto_epoch, 0
                    else:
                        idx = min(state.status_index, len(state.status_sequence) - 1)
                        fsm, epoch, hidden = state.status_sequence[idx]
                        state.status_index += 1
            if die:
                # Close the listening socket so the next poll fails immediately
                # (Connection refused), not after DEFAULT_HTTP_TIMEOUT.
                try:
                    self.server.socket.close()
                except OSError:
                    pass
                self.close_connection = True
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                return
            self._send(
                200,
                _envelope(
                    {
                        "state_machine": {"status": fsm, "phase": "OUTPUT", "paused_phase": None, "has_candidate_state": False},
                        "monitor": {"is_training": fsm == "STARTED", "current_epoch": epoch, "current_hidden_units": hidden, "current_phase": "output", "total_metrics": epoch},
                        "training_state": {"input_size": state.network_input_size, "output_size": 1},
                        "network_loaded": True,
                        "training_active": fsm == "STARTED",
                        "pending_dataset": None,
                        "completion_reason": state.completion_reason if fsm == "COMPLETED" else None,
                    }
                ),
            )
        elif path == "/metrics":
            if not state.metrics_enabled:
                self._send(404, b'{"detail": "metrics disabled"}')
                return
            with state.lock:
                state.redirect_hits += 1
            self._send(307, b"", extra={"Location": "/metrics/"})
        elif path == "/metrics/":
            if not state.metrics_enabled:
                self._send(404, b'{"detail": "metrics disabled"}')
                return
            self._send(200, _EXPOSITION, content_type="text/plain; version=0.0.4")
        elif path == "/v1/metrics":
            if state.metrics_final_status != 200:
                self._send(state.metrics_final_status, json.dumps({"detail": "metrics final stub error"}).encode("utf-8"))
                return
            payload = {"epoch": 3, "train_loss": 0.1, "train_accuracy": 0.95, "hidden_units": 2}
            if state.eval_metrics_present:
                payload.update({"f1": 0.9, "precision": 0.88, "recall": 0.91, "roc_auc": 0.97})
            self._send(200, _envelope(payload))
        elif path == "/v1/metrics/history":
            if state.metrics_history_status != 200:
                self._send(state.metrics_history_status, json.dumps({"detail": "metrics history stub error"}).encode("utf-8"))
                return
            self._send(
                200,
                _envelope(
                    [
                        {"epoch": 1, "kind": "training_step", "loss": 0.5, "accuracy": 0.6, "hidden_units": 0},
                        {"epoch": 2, "kind": "training_step", "loss": 0.3, "accuracy": 0.8, "hidden_units": 1},
                        {"epoch": 3, "kind": "training_step", "loss": 0.1, "accuracy": 0.95, "hidden_units": 2},
                    ]
                ),
            )
        elif path == "/v1/network":
            self._send(200, _envelope({"input_size": state.network_input_size, "output_size": 1, "hidden_units": 2, "max_hidden_units": 8, "learning_rate": 0.05, "uuid": "stub"}))
        elif path == "/v1/network/topology":
            self._send(200, _envelope({"nodes": [{"id": 0}], "connections": []}))
        elif path == "/v1/decision-boundary":
            # The real payload contract (manager.get_decision_boundary, manager.py:4284-4291).
            self._send(200, _envelope({"x_range": [-1.0, 1.0], "y_range": [-1.0, 1.0], "resolution": 2, "grid_x": [[-1.0, 1.0], [-1.0, 1.0]], "grid_y": [[-1.0, -1.0], [1.0, 1.0]], "predictions": [[0, 1], [1, 0]]}))
        elif path.startswith("/v1/datasets/") and path.endswith("/artifact"):
            if HAVE_NUMPY:
                self._send(200, _artifact_npz_bytes(state.artifact_kind), content_type="application/octet-stream")
            else:  # pragma: no cover - numpy present in CI + dev envs
                self._send(404, b'{"detail": "numpy unavailable in stub"}')
        else:
            self._send(404, b'{"detail": "not found"}')

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        state = self._state()
        path = self.path.split("?", 1)[0]
        body = self._read_body()
        self._record("POST", body)
        if path == "/v1/datasets":
            generator = (body or {}).get("generator", "spiral")
            meta = {
                "dataset_id": "ds-stub123",
                "generator": generator,
                "generator_version": "1.2.0",
                "params": (body or {}).get("params", {}),
                "n_samples": 1000,
                "n_features": state.n_features,
                "task_type": "classification",
                "n_classes": 2,
                "n_train": 800,
                "n_test": 200,
            }
            self._send(201, json.dumps({"dataset_id": "ds-stub123", "generator": generator, "meta": meta, "artifact_url": "/v1/datasets/ds-stub123/artifact"}).encode("utf-8"))
        elif path == "/v1/training/dataset":
            self._send(200, _envelope({"staged": body}))
        elif path == "/v1/training/start":
            if state.start_status == 422:
                self._send(422, b'{"detail": "TrainingParams rejected: extra field"}')
            else:
                self._send(200, _envelope({"started": True}))
        elif path == "/v1/snapshots":
            self._send(200, _envelope({"snapshot_id": "snap-stub-1"}))
        elif path == "/v1/train":
            if state.train_delay:
                time.sleep(state.train_delay)
            if state.train_status != 200:
                self._send(state.train_status, json.dumps({"detail": f"train stub {state.train_status}"}).encode("utf-8"))
            else:
                descriptor = {"dataset_id": "ds-stub123", "name": None, "split": ((body or {}).get("dataset") or {}).get("split", "train"), "n_windows": 100, "lookback": 64, "n_features": 3, "output_dim": 1, "has_target_dt": True, "has_seq_lengths": False}
                self._send(200, json.dumps({"final_metrics": {"r2": 0.91, "mse": 0.01}, "n_epochs": 1, "stopped_reason": "converged", "dataset": descriptor}).encode("utf-8"))
        elif path == "/v1/predict":
            if state.predict_status != 200:
                self._send(state.predict_status, json.dumps({"detail": "predict stub error"}).encode("utf-8"))
            else:
                # 4 predictions = the sequence artifact's test-split window count (forecast plots align).
                self._send(200, json.dumps({"predictions": [[0.1], [0.2], [0.3], [0.4]], "shape": [4, 1]}).encode("utf-8"))
        elif path == "/v1/crossval":
            if state.crossval_status != 200:
                self._send(state.crossval_status, json.dumps({"detail": "crossval stub error"}).encode("utf-8"))
            else:
                descriptor = {"dataset_id": "ds-stub123", "name": None, "split": "full", "n_windows": 100, "lookback": 64, "n_features": 3, "output_dim": 1, "has_target_dt": True, "has_seq_lengths": False}
                self._send(
                    200,
                    json.dumps(
                        {
                            "task_type": "regression",
                            "n_folds": (body or {}).get("n_folds", 2),
                            "folds": [{"fold": 0, "train_metrics": {"r2": 0.9}, "eval_metrics": {"r2": 0.8}, "n_epochs": 1}],
                            "eval_aggregate": {"r2": 0.8},
                            "eval_std": {"r2": 0.0},
                            "dataset": descriptor,
                        }
                    ).encode("utf-8"),
                )
        else:
            self._send(404, b'{"detail": "not found"}')


class _StubServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address) -> None:  # noqa: D102 - quiet broken pipes from the timeout arm
        pass

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _StubHandler)
        self.state = _ScriptedState()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #


def _base_config() -> dict:
    return {
        "schema_version": 1,
        "experiment": {"name": "stub-exp", "description": "hermetic stub run", "seed": 4242},
        "dataset": {"generator": "spiral", "params": {"n_spirals": 2}},
        "training": {"params": {"max_iterations": 2}},
        "outputs": {"max_wall_seconds": 30},
    }


def _recurrence_config() -> dict:
    return {
        "schema_version": 1,
        "experiment": {"name": "rec-exp", "description": "hermetic recurrence stub run", "seed": 777},
        "dataset": {"generator": "irregular_sine", "split": "train", "params": {"n_steps": 500, "lookback": 64}},
        "train": {"d": 8, "ridge": 1.0, "readout": "linear"},
        "crossval": {"enabled": True, "n_folds": 2, "scheme": "expanding", "embargo": 2},
        "predict": {"enabled": True, "from_dataset_split": "test"},
        "outputs": {"max_wall_seconds": 30},
    }


def _write_config(directory: Path, cfg: dict, name: str = "experiment-in.yaml") -> Path:
    path = directory / name
    path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return path


def _make_run_dir(directory: Path, base_url: str, run_id: str = "20260730T000000Z-beef", grafana_bridge: bool = False) -> Path:
    run_dir = directory / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    port = urlparse(base_url).port
    (run_dir / "ports.json").write_text(
        json.dumps({"run_id": run_id, "data": port, "cascor": port, "recurrence": port, "data_url": base_url, "experiment": "stub-exp", "grafana_bridge": grafana_bridge}),
        encoding="utf-8",
    )
    return run_dir


def _invoke(config: Path, run_dir: Path, *extra: str) -> tuple[int, str]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = rx.main(["--config", str(config), "--run-dir", str(run_dir), *FAST_FLAGS, *extra])
    return code, stdout.getvalue()


def _manifest(run_dir: Path) -> dict:
    return json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))


class _StubTestCase(unittest.TestCase):
    """Shared stub-server + tempdir scaffolding."""

    def setUp(self) -> None:
        self.server = _StubServer()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.tmp = Path(tempfile.mkdtemp(prefix="run-experiment-test-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.run_dir = _make_run_dir(self.tmp, self.server.base_url)

    @property
    def state(self) -> _ScriptedState:
        return self.server.state

    def _posts(self, path: str) -> list[dict | None]:
        return [body for method, req_path, body in self.state.requests if method == "POST" and req_path == path]


# --------------------------------------------------------------------------- #
# SS5.6 config validation (rule 1/2/3/6 + kind resolution)
# --------------------------------------------------------------------------- #


class ConfigValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="run-experiment-cfg-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def _load(self, cfg: dict):
        return rx.load_config(_write_config(self.tmp, cfg))

    def _assert_rejects(self, cfg: dict, fragment: str) -> None:
        with self.assertRaises(rx.ConfigError) as ctx:
            self._load(cfg)
        self.assertIn(fragment, str(ctx.exception))

    def test_valid_config_loads(self) -> None:
        config = self._load(_base_config())
        self.assertEqual(config["kind"], "cascor")
        self.assertEqual(config["experiment"]["name"], "stub-exp")
        self.assertEqual(config["experiment"]["seed"], 4242)

    def test_unknown_top_level_block_rejected(self) -> None:
        cfg = _base_config()
        cfg["surprise"] = {}
        self._assert_rejects(cfg, "unknown top-level block")

    def test_unknown_experiment_key_rejected(self) -> None:
        cfg = _base_config()
        cfg["experiment"]["operator"] = "paul"
        self._assert_rejects(cfg, "unknown key(s) in experiment")

    def test_unknown_dataset_key_rejected(self) -> None:
        cfg = _base_config()
        cfg["dataset"]["split"] = "train"
        self._assert_rejects(cfg, "unknown key(s) in dataset")

    def test_unknown_training_key_rejected(self) -> None:
        cfg = _base_config()
        cfg["training"]["turbo"] = True
        self._assert_rejects(cfg, "unknown key(s) in training")

    def test_unknown_outputs_key_rejected(self) -> None:
        cfg = _base_config()
        cfg["outputs"]["frobnicate"] = 1
        self._assert_rejects(cfg, "unknown key(s) in outputs")

    def test_unknown_runtime_key_rejected(self) -> None:
        cfg = _base_config()
        cfg["runtime"] = {"gpu": True}
        self._assert_rejects(cfg, "unknown key(s) in runtime")

    def test_missing_schema_version_rejected(self) -> None:
        cfg = _base_config()
        del cfg["schema_version"]
        self._assert_rejects(cfg, "schema_version")

    def test_future_schema_version_rejected(self) -> None:
        cfg = _base_config()
        cfg["schema_version"] = rx.SCHEMA_VERSION_MAX + 1
        self._assert_rejects(cfg, "schema_version")

    def test_string_schema_version_rejected(self) -> None:
        cfg = _base_config()
        cfg["schema_version"] = "1"
        self._assert_rejects(cfg, "schema_version")

    def test_missing_seed_rejected(self) -> None:
        cfg = _base_config()
        del cfg["experiment"]["seed"]
        self._assert_rejects(cfg, "experiment.seed is REQUIRED")

    def test_bool_seed_rejected(self) -> None:
        cfg = _base_config()
        cfg["experiment"]["seed"] = True
        self._assert_rejects(cfg, "experiment.seed")

    def test_service_infra_keys_rejected(self) -> None:
        for key in sorted(rx.SERVICE_FORBIDDEN_KEYS):
            cfg = _base_config()
            cfg["service"] = {key: "anything"}
            with self.subTest(key=key):
                self._assert_rejects(cfg, "rule 6")

    def test_service_science_keys_pass(self) -> None:
        cfg = _base_config()
        cfg["service"] = {"log_level": "INFO", "metrics_enabled": True}
        self.assertEqual(self._load(cfg)["kind"], "cascor")

    def test_both_app_blocks_rejected(self) -> None:
        cfg = _base_config()
        cfg["train"] = {"d": 8}
        self._assert_rejects(cfg, "both")

    def test_neither_app_block_rejected(self) -> None:
        cfg = _base_config()
        del cfg["training"]
        self._assert_rejects(cfg, "neither")

    def test_missing_dataset_block_rejected(self) -> None:
        cfg = _base_config()
        del cfg["dataset"]
        self._assert_rejects(cfg, "dataset")

    def test_recurrence_full_config_loads(self) -> None:
        config = self._load(_recurrence_config())
        self.assertEqual(config["kind"], "recurrence")
        self.assertEqual(config["dataset"]["split"], "train")
        self.assertEqual(config["dataset"]["params"]["seed"], 777)
        self.assertEqual(config["dataset"]["tags"], ["experiment", "rec-exp"])
        self.assertTrue(config["crossval"]["enabled"])
        self.assertEqual(config["crossval"]["n_folds"], 2)
        self.assertTrue(config["predict"]["enabled"])
        self.assertEqual(config["predict"]["from_dataset_split"], "test")
        self.assertEqual(config["train"], {"d": 8, "ridge": 1.0, "readout": "linear"})
        self.assertFalse(config["outputs"]["save_model"])

    def test_recurrence_absent_blocks_disabled(self) -> None:
        cfg = _recurrence_config()
        del cfg["crossval"]
        del cfg["predict"]
        config = self._load(cfg)
        self.assertFalse(config["crossval"]["enabled"])
        self.assertFalse(config["predict"]["enabled"])

    def test_recurrence_unknown_train_key_rejected(self) -> None:
        cfg = _recurrence_config()
        cfg["train"]["turbo"] = True
        self._assert_rejects(cfg, "unknown key(s) in train")

    def test_recurrence_unknown_crossval_key_rejected(self) -> None:
        cfg = _recurrence_config()
        cfg["crossval"]["folds"] = 3
        self._assert_rejects(cfg, "unknown key(s) in crossval")

    def test_recurrence_unknown_predict_key_rejected(self) -> None:
        cfg = _recurrence_config()
        cfg["predict"]["split"] = "test"
        self._assert_rejects(cfg, "unknown key(s) in predict")

    def test_recurrence_bad_dataset_split_rejected(self) -> None:
        cfg = _recurrence_config()
        cfg["dataset"]["split"] = "validation"
        self._assert_rejects(cfg, "dataset.split")

    def test_recurrence_bad_predict_split_rejected(self) -> None:
        cfg = _recurrence_config()
        cfg["predict"]["from_dataset_split"] = "validation"
        self._assert_rejects(cfg, "predict.from_dataset_split")

    def test_recurrence_crossval_needs_n_folds(self) -> None:
        cfg = _recurrence_config()
        cfg["crossval"] = {"enabled": True}
        self._assert_rejects(cfg, "n_folds")

    def test_recurrence_missing_dataset_rejected(self) -> None:
        cfg = _recurrence_config()
        del cfg["dataset"]
        self._assert_rejects(cfg, "recurrence path")

    def test_cascor_unknown_plot_name_rejected(self) -> None:
        cfg = _base_config()
        cfg["outputs"]["plots"] = ["dataset", "dt_histogram"]
        self._assert_rejects(cfg, "unknown plot name(s) for the cascor path")

    def test_recurrence_plot_names_validated_per_kind(self) -> None:
        cfg = _recurrence_config()
        cfg["outputs"]["plots"] = ["dt_histogram", "crossval_folds"]
        self.assertEqual(self._load(cfg)["outputs"]["plots"], ["dt_histogram", "crossval_folds"])
        cfg["outputs"]["plots"] = ["dataset"]
        self._assert_rejects(cfg, "unknown plot name(s) for the recurrence path")

    def test_seed_derivation_rule(self) -> None:
        config = self._load(_base_config())
        self.assertEqual(config["dataset"]["params"]["seed"], 4242)

    def test_explicit_dataset_seed_preserved(self) -> None:
        cfg = _base_config()
        cfg["dataset"]["params"]["seed"] = 7
        config = self._load(cfg)
        self.assertEqual(config["dataset"]["params"]["seed"], 7)

    def test_default_tags_are_run_scoped(self) -> None:
        config = self._load(_base_config())
        self.assertEqual(config["dataset"]["tags"], ["experiment", "stub-exp"])

    def test_bad_max_wall_seconds_rejected(self) -> None:
        cfg = _base_config()
        cfg["outputs"]["max_wall_seconds"] = -5
        self._assert_rejects(cfg, "max_wall_seconds")


class MetricParsingTest(unittest.TestCase):
    def test_allowlisted_families_parsed(self) -> None:
        samples = rx.parse_metric_samples(_EXPOSITION.decode("utf-8"))
        self.assertEqual(samples["juniper_cascor_training_loss"], 0.123)
        self.assertEqual(samples["juniper_cascor_candidate_correlation"], 0.87)
        self.assertEqual(samples["juniper_cascor_training_step_duration_seconds_count"], 3.0)

    def test_non_allowlisted_family_ignored(self) -> None:
        samples = rx.parse_metric_samples("juniper_cascor_unrelated_family 99\n")
        self.assertEqual(samples, {})

    def test_last_sample_wins(self) -> None:
        text = "juniper_cascor_training_loss 1.0\njuniper_cascor_training_loss 2.0\n"
        self.assertEqual(rx.parse_metric_samples(text)["juniper_cascor_training_loss"], 2.0)

    def test_malformed_lines_skipped(self) -> None:
        text = "juniper_cascor_training_loss notafloat\njuniper_cascor_training_loss\n# comment\n"
        self.assertEqual(rx.parse_metric_samples(text), {})


class EndpointResolutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="run-experiment-ep-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def test_ports_json_resolution(self) -> None:
        run_dir = _make_run_dir(self.tmp, "http://127.0.0.1:8110")
        data_url, cascor_url, ports = rx.resolve_endpoints(run_dir, None, None)
        self.assertEqual(data_url, "http://127.0.0.1:8110")
        self.assertEqual(cascor_url, "http://127.0.0.1:8110")
        self.assertEqual(ports["run_id"], "20260730T000000Z-beef")

    def test_cli_overrides_win(self) -> None:
        run_dir = _make_run_dir(self.tmp, "http://127.0.0.1:8110")
        data_url, cascor_url, _ = rx.resolve_endpoints(run_dir, "http://127.0.0.1:1/", "http://127.0.0.1:2/")
        self.assertEqual(data_url, "http://127.0.0.1:1")
        self.assertEqual(cascor_url, "http://127.0.0.1:2")

    def test_missing_everything_rejected(self) -> None:
        run_dir = self.tmp / "empty-run"
        run_dir.mkdir()
        with self.assertRaises(rx.ConfigError):
            rx.resolve_endpoints(run_dir, None, None)


# --------------------------------------------------------------------------- #
# drive-loop arms (completion / FAILED / stall / timeout / F-1 / G-3 degrade)
# --------------------------------------------------------------------------- #


class HappyPathTest(_StubTestCase):
    def test_spiral_run_end_to_end(self) -> None:
        config = _write_config(self.tmp, _base_config())
        code, stdout = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS, stdout)

        start_bodies = self._posts("/v1/training/start")
        self.assertEqual(len(start_bodies), 1)
        start = start_bodies[0]
        self.assertTrue(start["start_fresh"])
        self.assertEqual(start["params"], {"max_iterations": 2})
        self.assertEqual(start["dataset"]["source"], "juniper-data")
        self.assertEqual(start["dataset"]["url"], self.server.base_url)
        self.assertEqual(start["dataset"]["generator"], "spiral")
        self.assertEqual(start["dataset"]["params"]["seed"], 4242)
        self.assertEqual(self._posts("/v1/training/dataset"), [])

        dataset_bodies = self._posts("/v1/datasets")
        self.assertEqual(len(dataset_bodies), 1)
        self.assertEqual(dataset_bodies[0]["params"]["seed"], 4242)
        self.assertEqual(dataset_bodies[0]["tags"], ["experiment", "stub-exp"])

        # F-1: the bare /metrics GET must follow the 307 to /metrics/.
        self.assertGreaterEqual(self.state.redirect_hits, 1)

        series = (self.run_dir / "artifacts" / "results" / "metrics_series.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(series[0], ",".join(rx.SERIES_CSV_COLUMNS))
        self.assertGreaterEqual(len(series), 3)
        correlation_col = rx.SERIES_CSV_COLUMNS.index("juniper_cascor_candidate_correlation")
        self.assertEqual(series[1].split(",")[correlation_col], "0.87")

        results = self.run_dir / "artifacts" / "results"
        for artifact in ("metrics_final.json", "metrics_history.json", "topology.json"):
            self.assertTrue((results / artifact).is_file(), artifact)
        self.assertTrue((self.run_dir / "config" / "experiment.yaml").is_file())
        self.assertTrue((self.run_dir / "logs" / "run_experiment.log").is_file())

        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["schema"], rx.MANIFEST_SCHEMA)
        self.assertEqual(manifest["run_id"], "20260730T000000Z-beef")
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertTrue(manifest["acceptance"]["ok"])
        self.assertEqual(manifest["config_sha256"], hashlib.sha256(config.read_bytes()).hexdigest())
        self.assertEqual(manifest["dataset"]["dataset_id"], "ds-stub123")
        self.assertEqual(manifest["dataset"]["version"], "1.2.0")
        self.assertEqual(manifest["seeds"], {"experiment": 4242, "dataset": 4242})
        self.assertEqual(manifest["completion_reason"], "max_iterations")
        self.assertIsNone(manifest["g6_shape_check"])
        self.assertFalse(manifest["metrics_scraped"]["grafana_bridge"])
        self.assertIn("artifacts/results/metrics_series.csv", manifest["artifacts"])
        self.assertIn("config/experiment.yaml", manifest["artifacts"])
        self.assertEqual(manifest["driver"]["wave"], rx.DRIVER_WAVE)

        # SS8.3 (Wave 2.6): stats.json + summary.md written and folded into the manifest.
        self.assertIsNone(manifest["stats_error"])
        self.assertIn("artifacts/results/stats.json", manifest["artifacts"])
        self.assertIn("artifacts/results/summary.md", manifest["artifacts"])
        stats = json.loads((results / "stats.json").read_text(encoding="utf-8"))
        self.assertEqual(stats["schema"], "juniper-experiment-stats/1")
        self.assertEqual(stats["identity"]["run_id"], "20260730T000000Z-beef")
        self.assertEqual(stats["dataset"]["shapes"], {"kind": "tabular", "n_train": 800, "n_test": 200, "n_features": 2, "n_classes": 2})
        correlation = stats["cascor"]["candidate_correlation"]
        self.assertEqual(correlation["max"], 0.87)
        self.assertGreaterEqual(len(correlation["per_round"]), 1)
        duration = stats["cascor"]["training_step_duration"]
        self.assertEqual(duration["total_steps"], 3)
        self.assertIn("per-poll mean", duration["basis"])
        summary_text = (results / "summary.md").read_text(encoding="utf-8")
        self.assertIn("20260730T000000Z-beef", summary_text)
        self.assertIn("## cascor", summary_text)

        self.assertIn("run_experiment summary", stdout)
        self.assertIn("20260730T000000Z-beef", stdout)

    @unittest.skipUnless(HAVE_NUMPY, "numpy required for the .npz decision-boundary artifact")
    def test_decision_boundary_npz_roundtrip(self) -> None:
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        npz_path = self.run_dir / "artifacts" / "results" / "decision_boundary.npz"
        self.assertTrue(npz_path.is_file())
        import numpy as np

        with np.load(npz_path, allow_pickle=False) as bundle:
            self.assertIn("predictions", bundle.files)
            self.assertEqual(bundle["predictions"].shape, (2, 2))

    def test_snapshot_at_end(self) -> None:
        cfg = _base_config()
        cfg["outputs"]["snapshot_at_end"] = True
        config = _write_config(self.tmp, cfg)
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        self.assertEqual(len(self._posts("/v1/snapshots")), 1)
        self.assertEqual(_manifest(self.run_dir)["snapshot"], {"snapshot_id": "snap-stub-1"})

    def test_metrics_disabled_degrades_but_completes(self) -> None:
        # The G-3 trap: /metrics 404s when JUNIPER_CASCOR_METRICS_ENABLED is unset.
        self.state.metrics_enabled = False
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        manifest = _manifest(self.run_dir)
        self.assertGreaterEqual(manifest["drive_loop"]["metrics_sampling_errors"], 1)
        series = (self.run_dir / "artifacts" / "results" / "metrics_series.csv").read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(series), 2)
        correlation_col = rx.SERIES_CSV_COLUMNS.index("juniper_cascor_candidate_correlation")
        self.assertEqual(series[1].split(",")[correlation_col], "")


class FailureArmsTest(_StubTestCase):
    def test_failed_run_exits_4(self) -> None:
        self.state.status_sequence = [("STARTED", 1, 0), ("FAILED", 1, 0)]
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_RUN_FAILED)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "failed")
        self.assertFalse(manifest["acceptance"]["ok"])

    def test_stall_exits_1(self) -> None:
        self.state.status_sequence = [("STARTED", 1, 0)]
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.run_dir, "--stall-seconds", "0.2")
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(_manifest(self.run_dir)["outcome"], "stalled")
        # SS8.3: stats render for every outcome, not just success.
        self.assertTrue((self.run_dir / "artifacts" / "results" / "stats.json").is_file())

    def test_cli_budget_beats_yaml(self) -> None:
        self.state.increment_epochs = True
        cfg = _base_config()
        cfg["outputs"]["max_wall_seconds"] = 9999
        config = _write_config(self.tmp, cfg)
        code, _ = _invoke(config, self.run_dir, "--max-wall-seconds", "0.3")
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "timed_out")
        self.assertEqual(manifest["driver"]["max_wall_seconds"], 0.3)

    def test_essential_collect_failure_exits_1(self) -> None:
        # Training COMPLETED but an essential artifact is missing -> acceptance, not green.
        self.state.metrics_final_status = 500
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertTrue(
            any("essential artifact 'metrics_final'" in reason for reason in manifest["acceptance"]["reasons"]),
            msg=manifest["acceptance"]["reasons"],
        )
        self.assertFalse((self.run_dir / "artifacts" / "results" / "metrics_final.json").exists())

    def test_mid_drive_unreachable_exits_3(self) -> None:
        # After the first status poll, kill the stub listener so CONSECUTIVE_POLL_ERRORS_MAX
        # trips -> torn_down_early + EXIT_UNREACHABLE (not a silent green).
        self.state.status_sequence = [("STARTED", 1, 0), ("STARTED", 2, 0), ("COMPLETED", 3, 1)]
        self.state.status_die_after = 1
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.run_dir, "--poll-interval", "0.05")
        self.assertEqual(code, rx.EXIT_UNREACHABLE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "torn_down_early")
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertTrue(
            any("unreachable mid-run" in reason for reason in manifest["acceptance"]["reasons"]),
            msg=manifest["acceptance"]["reasons"],
        )

    def test_yaml_budget_honored_without_cli(self) -> None:
        self.state.increment_epochs = True
        cfg = _base_config()
        cfg["outputs"]["max_wall_seconds"] = 0.3
        config = _write_config(self.tmp, cfg)
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(_manifest(self.run_dir)["outcome"], "timed_out")

    def test_start_422_exits_2(self) -> None:
        self.state.start_status = 422
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_MISUSE)

    def test_unavailable_generator_exits_2(self) -> None:
        cfg = _base_config()
        cfg["dataset"]["generator"] = "mnist"
        config = _write_config(self.tmp, cfg)
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_MISUSE)

    def test_unknown_generator_exits_2(self) -> None:
        cfg = _base_config()
        cfg["dataset"]["generator"] = "nonexistent"
        config = _write_config(self.tmp, cfg)
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_MISUSE)


class StagingPathTest(_StubTestCase):
    def _xor_config(self) -> Path:
        cfg = _base_config()
        cfg["dataset"] = {"generator": "xor", "params": {"n_points_per_quadrant": 250}}
        return _write_config(self.tmp, cfg)

    def test_non_spiral_stages_then_starts(self) -> None:
        code, _ = _invoke(self._xor_config(), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        staged = self._posts("/v1/training/dataset")
        self.assertEqual(len(staged), 1)
        self.assertEqual(staged[0]["dataset_type"], "xor")
        self.assertEqual(staged[0]["params"]["seed"], 4242)
        start = self._posts("/v1/training/start")[0]
        self.assertNotIn("dataset", start)
        g6 = _manifest(self.run_dir)["g6_shape_check"]
        self.assertTrue(g6["ok"])
        self.assertEqual(g6["expected_input_size"], 2)

    def test_moon_maps_to_moons_alias(self) -> None:
        cfg = _base_config()
        cfg["dataset"] = {"generator": "moon", "params": {"n_samples": 100}}
        code, _ = _invoke(_write_config(self.tmp, cfg), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        self.assertEqual(self._posts("/v1/training/dataset")[0]["dataset_type"], "moons")

    def test_g6_shape_mismatch_fails_acceptance(self) -> None:
        self.state.network_input_size = 784  # the stale-data class: network never took the new dataset
        code, _ = _invoke(self._xor_config(), self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertFalse(manifest["g6_shape_check"]["ok"])
        self.assertTrue(any("G-6" in reason for reason in manifest["acceptance"]["reasons"]))

    def test_unstageable_generator_exits_2_naming_w3(self) -> None:
        cfg = _base_config()
        cfg["dataset"] = {"generator": "gaussian", "params": {"n_classes": 3}}
        with self.assertLogs(rx.log, level="ERROR") as logs:
            code, _ = _invoke(_write_config(self.tmp, cfg), self.run_dir)
        self.assertEqual(code, rx.EXIT_MISUSE)
        self.assertTrue(any("W-3" in line for line in logs.output))
        self.assertEqual(self._posts("/v1/training/start"), [])


class CliArmsTest(_StubTestCase):
    def test_recurrence_missing_dataset_exits_2(self) -> None:
        cfg = {"schema_version": 1, "experiment": {"name": "rec", "seed": 1}, "train": {"d": 8}}
        config = _write_config(self.tmp, cfg)
        with self.assertLogs(rx.log, level="ERROR") as logs:
            code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_MISUSE)
        self.assertTrue(any("recurrence path" in line for line in logs.output))

    def test_missing_run_dir_exits_2(self) -> None:
        config = _write_config(self.tmp, _base_config())
        code, _ = _invoke(config, self.tmp / "no-such-run")
        self.assertEqual(code, rx.EXIT_MISUSE)

    def test_unreachable_service_exits_3(self) -> None:
        config = _write_config(self.tmp, _base_config())
        dead_run = _make_run_dir(self.tmp, "http://127.0.0.1:9", run_id="20260730T000000Z-dead")
        code, _ = _invoke(config, dead_run, "--health-timeout", "0.3")
        self.assertEqual(code, rx.EXIT_UNREACHABLE)

    def test_corrupt_ports_json_exits_2(self) -> None:
        config = _write_config(self.tmp, _base_config())
        (self.run_dir / "ports.json").write_text("{not json", encoding="utf-8")
        code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_MISUSE)


class RecurrencePathTest(_StubTestCase):
    """Wave 2.3: the recurrence drive path (synchronous train -> optional predict/crossval)."""

    def _config(self, **mutate) -> Path:
        cfg = _recurrence_config()
        for key, value in mutate.items():
            if value is None:
                cfg.pop(key, None)
            else:
                cfg[key] = value
        return _write_config(self.tmp, cfg)

    def test_recurrence_run_end_to_end(self) -> None:
        code, stdout = _invoke(self._config(), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS, stdout)

        train_bodies = self._posts("/v1/train")
        self.assertEqual(len(train_bodies), 1)
        self.assertEqual(train_bodies[0]["dataset"], {"dataset_id": "ds-stub123", "split": "train"})
        self.assertEqual(train_bodies[0]["d"], 8)
        self.assertEqual(train_bodies[0]["ridge"], 1.0)
        self.assertEqual(train_bodies[0]["readout"], "linear")
        self.assertNotIn("theta", train_bodies[0])

        predict_bodies = self._posts("/v1/predict")
        self.assertEqual(len(predict_bodies), 1)
        self.assertEqual(predict_bodies[0]["dataset"], {"dataset_id": "ds-stub123", "split": "test"})

        crossval_bodies = self._posts("/v1/crossval")
        self.assertEqual(len(crossval_bodies), 1)
        self.assertEqual(crossval_bodies[0]["dataset"], {"dataset_id": "ds-stub123"})
        self.assertEqual(crossval_bodies[0]["n_folds"], 2)
        self.assertEqual(crossval_bodies[0]["scheme"], "expanding")
        self.assertEqual(crossval_bodies[0]["embargo"], 2)
        self.assertEqual(crossval_bodies[0]["d"], 8)

        dataset_bodies = self._posts("/v1/datasets")
        self.assertEqual(len(dataset_bodies), 1)
        self.assertEqual(dataset_bodies[0]["params"]["seed"], 777)
        self.assertEqual(dataset_bodies[0]["tags"], ["experiment", "rec-exp"])

        results = self.run_dir / "artifacts" / "results"
        for artifact in ("train_response.json", "predict_response.json", "crossval_response.json"):
            self.assertTrue((results / artifact).is_file(), artifact)

        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertTrue(manifest["acceptance"]["ok"])
        self.assertEqual(manifest["train"]["final_metrics"]["r2"], 0.91)
        self.assertEqual(manifest["train"]["stopped_reason"], "converged")
        self.assertEqual(manifest["predict"], {"shape": [4, 1]})
        self.assertEqual(manifest["crossval"]["eval_aggregate"], {"r2": 0.8})
        self.assertIsNone(manifest["g6_shape_check"])
        self.assertIsNone(manifest["save_model_rerun"])
        self.assertEqual(manifest["service_urls"]["recurrence"], self.server.base_url)
        self.assertEqual(manifest["dataset"]["split"], "train")
        self.assertEqual(manifest["driver"]["wave"], rx.DRIVER_WAVE)

        # SS8.3 (Wave 2.6): the recurrence stats block + summary.
        self.assertIsNone(manifest["stats_error"])
        stats = json.loads((results / "stats.json").read_text(encoding="utf-8"))
        self.assertEqual(stats["recurrence"]["final_metrics"]["r2"], 0.91)
        self.assertEqual(stats["recurrence"]["theta"]["note"], "data-driven (resolved from per-window elapsed time)")
        self.assertEqual(stats["recurrence"]["readout"]["rung"], "linear")
        self.assertEqual(stats["recurrence"]["crossval"]["eval_aggregate"], {"r2": 0.8})
        self.assertIn("## recurrence", (results / "summary.md").read_text(encoding="utf-8"))

        self.assertIn("(recurrence)", stdout)

    def test_disabled_blocks_skip_phases(self) -> None:
        code, _ = _invoke(self._config(crossval=None, predict=None), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        self.assertEqual(self._posts("/v1/predict"), [])
        self.assertEqual(self._posts("/v1/crossval"), [])
        manifest = _manifest(self.run_dir)
        self.assertIsNone(manifest["predict"])
        self.assertIsNone(manifest["crossval"])

    def test_train_409_exits_4(self) -> None:
        self.state.train_status = 409
        code, _ = _invoke(self._config(), self.run_dir)
        self.assertEqual(code, rx.EXIT_RUN_FAILED)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "failed")
        self.assertFalse(manifest["acceptance"]["ok"])

    def test_train_422_exits_2(self) -> None:
        self.state.train_status = 422
        code, _ = _invoke(self._config(), self.run_dir)
        self.assertEqual(code, rx.EXIT_MISUSE)

    def test_train_budget_timeout_exits_1(self) -> None:
        # Q-2 for the synchronous train: the wall budget is the request's socket timeout.
        self.state.train_delay = 0.6
        code, _ = _invoke(self._config(), self.run_dir, "--max-wall-seconds", "0.2")
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "timed_out")
        self.assertEqual(self._posts("/v1/predict"), [])
        self.assertEqual(self._posts("/v1/crossval"), [])

    def test_predict_failure_continues_to_crossval(self) -> None:
        self.state.predict_status = 500
        code, _ = _invoke(self._config(), self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(len(self._posts("/v1/crossval")), 1)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertTrue(any("predict" in reason for reason in manifest["acceptance"]["reasons"]))
        self.assertTrue((self.run_dir / "artifacts" / "results" / "crossval_response.json").is_file())

    def test_crossval_failure_keeps_predict_and_fails_acceptance(self) -> None:
        # Asymmetric sibling of predict-failure-continues: crossval 500 must not drop predict
        # evidence, and the run must still land as acceptance failure with a written manifest.
        self.state.crossval_status = 500
        code, _ = _invoke(self._config(), self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(len(self._posts("/v1/predict")), 1)
        self.assertEqual(len(self._posts("/v1/crossval")), 1)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertTrue(any("crossval" in reason for reason in manifest["acceptance"]["reasons"]))
        self.assertEqual(manifest["predict"], {"shape": [4, 1]})
        self.assertIsNone(manifest["crossval"])
        self.assertTrue((self.run_dir / "artifacts" / "results" / "predict_response.json").is_file())
        self.assertFalse((self.run_dir / "artifacts" / "results" / "crossval_response.json").exists())

    def test_save_model_rerun_invokes_cli(self) -> None:
        bindir = self.tmp / "bin"
        bindir.mkdir()
        capture = self.tmp / "capture"
        capture.mkdir()
        stub = bindir / "juniper-recurrence"
        stub.write_text(
            "#!/bin/bash\n" f"printf '%s\\n' \"$*\" > '{capture}/cmd.txt'\n" f"printf '%s\\n' \"$JUNIPER_DATA_URL\" > '{capture}/env.txt'\n" "prev=''\nout=''\n" 'for a in "$@"; do [ "$prev" = "--out" ] && out="$a"; prev="$a"; done\n' '[ -n "$out" ] && : > "$out"\n' "exit 0\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        cfg = _recurrence_config()
        cfg["outputs"]["save_model"] = True
        config = _write_config(self.tmp, cfg)
        with mock.patch.dict(os.environ, {"PATH": f"{bindir}:{os.environ['PATH']}"}):
            code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        cmd = (capture / "cmd.txt").read_text(encoding="utf-8")
        self.assertIn("--dataset ds-stub123", cmd)
        self.assertIn("--split train", cmd)
        self.assertIn("--d 8", cmd)
        self.assertIn("--out", cmd)
        self.assertEqual((capture / "env.txt").read_text(encoding="utf-8").strip(), self.server.base_url)
        manifest = _manifest(self.run_dir)
        self.assertTrue(manifest["save_model_rerun"]["ok"])
        self.assertTrue((self.run_dir / "artifacts" / "results" / "model.npz").is_file())
        self.assertIn("artifacts/results/model.npz", manifest["artifacts"])

    def test_save_model_missing_cli_fails_acceptance(self) -> None:
        cfg = _recurrence_config()
        cfg["outputs"]["save_model"] = True
        config = _write_config(self.tmp, cfg)
        empty_bin = self.tmp / "empty-bin"
        empty_bin.mkdir()
        with mock.patch.dict(os.environ, {"PATH": str(empty_bin)}):
            code, _ = _invoke(config, self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertFalse(manifest["save_model_rerun"]["ok"])
        self.assertTrue(any("save_model" in reason for reason in manifest["acceptance"]["reasons"]))


@unittest.skipUnless(HAVE_NUMPY and HAVE_MPL, "numpy + matplotlib required for the SS8.1 plot set")
class CascorPlotsTest(_StubTestCase):
    """Wave 2.4: the SS8.1 cascor plot set rendered client-side from collected payloads."""

    ALL_PLOTS = ["dataset", "decision_boundary", "training_history", "candidate_correlation", "eval_metrics"]

    def _config_with_plots(self, plots: list) -> Path:
        cfg = _base_config()
        cfg["outputs"]["plots"] = plots
        return _write_config(self.tmp, cfg)

    def test_all_five_plots_rendered(self) -> None:
        code, _ = _invoke(self._config_with_plots(self.ALL_PLOTS), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        plots_dir = self.run_dir / "artifacts" / "plots"
        for name in ("dataset.png", "decision_boundary.png", "training_history.png", "candidate_correlation.png", "eval_metrics.png"):
            path = plots_dir / name
            self.assertTrue(path.is_file(), name)
            raw = path.read_bytes()
            self.assertTrue(raw.startswith(PNG_MAGIC), f"{name} is not a PNG")
            self.assertGreater(len(raw), 1500, f"{name} suspiciously small ({len(raw)} bytes)")
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["driver"]["plots"]["rendered"], self.ALL_PLOTS)
        self.assertEqual(manifest["driver"]["plots"]["skipped"], [])
        self.assertIn("plots", manifest["timings"])
        for name in ("dataset.png", "decision_boundary.png"):
            self.assertIn(f"artifacts/plots/{name}", manifest["artifacts"])

    def test_eval_metrics_disabled_is_a_skip_not_a_failure(self) -> None:
        self.state.eval_metrics_present = False
        code, _ = _invoke(self._config_with_plots(["eval_metrics"]), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["driver"]["plots"]["rendered"], [])
        self.assertEqual(len(manifest["driver"]["plots"]["skipped"]), 1)
        self.assertIn("eval metrics", manifest["driver"]["plots"]["skipped"][0]["reason"])
        self.assertFalse((self.run_dir / "artifacts" / "plots" / "eval_metrics.png").exists())

    def test_degraded_sampling_skips_correlation_plot(self) -> None:
        self.state.metrics_enabled = False  # the G-3 trap: series csv has no correlation samples
        code, _ = _invoke(self._config_with_plots(["candidate_correlation"]), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["driver"]["plots"]["rendered"], [])
        self.assertIn("candidate_correlation", manifest["driver"]["plots"]["skipped"][0]["reason"])

    def test_matplotlib_unavailable_fails_acceptance(self) -> None:
        with mock.patch.object(rx, "_load_plots_module", side_effect=ImportError("matplotlib stub-missing")):
            code, _ = _invoke(self._config_with_plots(["dataset"]), self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertTrue(any("matplotlib" in reason for reason in manifest["acceptance"]["reasons"]))
        self.assertEqual(manifest["driver"]["plots"]["skipped"][0]["reason"], "matplotlib unavailable")

    def test_no_plots_requested_renders_nothing(self) -> None:
        code, _ = _invoke(_write_config(self.tmp, _base_config()), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["driver"]["plots"], {"requested": [], "rendered": [], "skipped": []})
        self.assertEqual(list((self.run_dir / "artifacts" / "plots").iterdir()), [])


@unittest.skipUnless(HAVE_NUMPY and HAVE_MPL, "numpy + matplotlib required for the SS8.1 plot set")
class PlotRendererUnitTest(unittest.TestCase):
    """Unit arms for plots_cascor.py: synthetic payloads in, non-degenerate PNGs (or ValueError) out."""

    def setUp(self) -> None:
        self.plots = rx._load_plots_module()
        self.tmp = Path(tempfile.mkdtemp(prefix="run-experiment-plots-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def test_render_training_history_writes_png(self) -> None:
        rows = [{"loss": 0.5, "accuracy": 0.6, "hidden_units": 0}, {"loss": 0.2, "accuracy": 0.9, "hidden_units": 1}]
        out = self.plots.render_training_history(rows, "t", self.tmp / "history.png")
        self.assertTrue(out.read_bytes().startswith(PNG_MAGIC))

    def test_render_training_history_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            self.plots.render_training_history([], "t", self.tmp / "history.png")

    def test_render_eval_metrics_rejects_all_null(self) -> None:
        with self.assertRaises(ValueError):
            self.plots.render_eval_metrics({"f1": None, "precision": None}, "t", self.tmp / "eval.png")

    def test_render_candidate_correlation_rejects_empty_cells(self) -> None:
        rows = [{"ts_unix": "1.0", "juniper_cascor_candidate_correlation": "", "current_hidden_units": "0"}]
        with self.assertRaises(ValueError):
            self.plots.render_candidate_correlation(rows, "t", self.tmp / "corr.png")

    def test_render_dataset_rejects_non_2d(self) -> None:
        import numpy as np

        npz = {"X_train": np.zeros((4, 3)), "y_train": np.zeros(4), "X_test": np.zeros((2, 3)), "y_test": np.zeros(2)}
        with self.assertRaises(ValueError):
            self.plots.render_dataset(npz, "t", self.tmp / "dataset.png")


@unittest.skipUnless(HAVE_NUMPY and HAVE_MPL, "numpy + matplotlib required for the SS8.2 plot set")
class RecurrencePlotsTest(_StubTestCase):
    """Wave 2.5: the SS8.2 recurrence plot set (closes G-5)."""

    ALL_PLOTS = ["dataset_overview", "dt_histogram", "forecast_vs_truth", "residuals", "crossval_folds", "metrics_table"]

    def setUp(self) -> None:
        super().setUp()
        self.state.artifact_kind = "sequence"

    def _config_with_plots(self, plots: list, **mutate) -> Path:
        cfg = _recurrence_config()
        cfg["outputs"]["plots"] = plots
        for key, value in mutate.items():
            if value is None:
                cfg.pop(key, None)
            else:
                cfg[key] = value
        return _write_config(self.tmp, cfg)

    def test_all_six_plots_rendered(self) -> None:
        code, _ = _invoke(self._config_with_plots(self.ALL_PLOTS), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        plots_dir = self.run_dir / "artifacts" / "plots"
        for name in ("dataset_overview.png", "dt_histogram.png", "forecast_vs_truth.png", "residuals.png", "crossval_folds.png", "metrics_table.png"):
            path = plots_dir / name
            self.assertTrue(path.is_file(), name)
            raw = path.read_bytes()
            self.assertTrue(raw.startswith(PNG_MAGIC), f"{name} is not a PNG")
            self.assertGreater(len(raw), 1500, f"{name} suspiciously small ({len(raw)} bytes)")
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["driver"]["plots"]["rendered"], self.ALL_PLOTS)
        self.assertEqual(manifest["driver"]["plots"]["skipped"], [])
        self.assertIn("plots", manifest["timings"])
        self.assertIn("artifacts/plots/dt_histogram.png", manifest["artifacts"])

    def test_disabled_phases_skip_their_plots(self) -> None:
        code, _ = _invoke(self._config_with_plots(["forecast_vs_truth", "crossval_folds", "metrics_table"], crossval=None, predict=None), self.run_dir)
        self.assertEqual(code, rx.EXIT_SUCCESS)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["driver"]["plots"]["rendered"], ["metrics_table"])
        skipped = {entry["name"]: entry["reason"] for entry in manifest["driver"]["plots"]["skipped"]}
        self.assertIn("predict phase disabled or failed", skipped["forecast_vs_truth"])
        self.assertIn("crossval phase disabled or failed", skipped["crossval_folds"])

    def test_matplotlib_unavailable_fails_acceptance(self) -> None:
        with mock.patch.object(rx, "_load_plots_module", side_effect=ImportError("matplotlib stub-missing")):
            code, _ = _invoke(self._config_with_plots(["dt_histogram"]), self.run_dir)
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        manifest = _manifest(self.run_dir)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertTrue(any("matplotlib" in reason for reason in manifest["acceptance"]["reasons"]))


@unittest.skipUnless(HAVE_NUMPY and HAVE_MPL, "numpy + matplotlib required for the SS8.2 plot set")
class RecurrencePlotRendererUnitTest(unittest.TestCase):
    """Unit arms for plots_recurrence.py: key resolution + the ValueError no-data contracts."""

    def setUp(self) -> None:
        self.plots = rx._load_plots_module("plots_recurrence.py")
        self.tmp = Path(tempfile.mkdtemp(prefix="run-experiment-rec-plots-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def test_resolve_target_key_prefers_y_reg(self) -> None:
        self.assertEqual(self.plots.resolve_target_key({"y_reg_test": 1, "y_test": 1}, "test"), "y_reg_test")
        self.assertEqual(self.plots.resolve_target_key({"y_test": 1}, "test"), "y_test")
        with self.assertRaises(ValueError):
            self.plots.resolve_target_key({"X_test": 1}, "test")

    def test_dt_histogram_rejects_non_dt_dataset(self) -> None:
        with self.assertRaises(ValueError):
            self.plots.render_dt_histogram({"X_train": [1]}, "train", "t", self.tmp / "dt.png")

    def test_crossval_folds_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            self.plots.render_crossval_folds({"folds": []}, "t", self.tmp / "cv.png")

    def test_forecast_rejects_length_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            self.plots.render_forecast_vs_truth([[0.1], [0.2]], [0.1, 0.2, 0.3], "t", self.tmp / "f.png")

    def test_metrics_table_renders_train_and_cv_rows(self) -> None:
        crossval = {"eval_aggregate": {"r2": 0.8}, "eval_std": {"r2": 0.05}}
        out = self.plots.render_metrics_table({"r2": 0.91, "mse": 0.01}, crossval, "t", self.tmp / "table.png")
        self.assertTrue(out.read_bytes().startswith(PNG_MAGIC))


class StatsSummaryUnitTest(unittest.TestCase):
    """Unit arms for stats_summary.py (SS8.3, stdlib-only): percentiles, series-derived stats, block assembly."""

    def setUp(self) -> None:
        self.stats = rx._load_sibling("stats_summary.py")

    def test_percentile(self) -> None:
        self.assertIsNone(self.stats.percentile([], 50))
        self.assertEqual(self.stats.percentile([3.0], 95), 3.0)
        self.assertEqual(self.stats.percentile([1.0, 2.0, 3.0, 4.0], 50), 2.5)
        self.assertEqual(self.stats.percentile([1.0, 2.0], 100), 2.0)

    def test_step_duration_stats_from_deltas(self) -> None:
        rows = [
            {"juniper_cascor_training_step_duration_seconds_sum": "1.0", "juniper_cascor_training_step_duration_seconds_count": "2"},
            {"juniper_cascor_training_step_duration_seconds_sum": "2.0", "juniper_cascor_training_step_duration_seconds_count": "4"},
            {"juniper_cascor_training_step_duration_seconds_sum": "5.0", "juniper_cascor_training_step_duration_seconds_count": "5"},
        ]
        result = self.stats.step_duration_stats(rows)
        self.assertEqual(result["total_steps"], 5)
        self.assertEqual(result["poll_samples"], 2)  # per-poll means: (1.0/2)=0.5 and (3.0/1)=3.0
        self.assertEqual(result["p50_seconds"], 1.75)
        self.assertEqual(result["overall_mean_seconds"], 1.0)

    def test_step_duration_stats_constant_series(self) -> None:
        rows = [{"juniper_cascor_training_step_duration_seconds_sum": "1.5", "juniper_cascor_training_step_duration_seconds_count": "3"}] * 3
        result = self.stats.step_duration_stats(rows)
        self.assertEqual(result["total_steps"], 3)
        self.assertIsNone(result["p50_seconds"])
        self.assertIn("per-poll mean", result["basis"])

    def test_correlation_per_round(self) -> None:
        rows = [
            {"juniper_cascor_candidate_correlation": "0.5", "current_hidden_units": "0"},
            {"juniper_cascor_candidate_correlation": "0.7", "current_hidden_units": "0"},
            {"juniper_cascor_candidate_correlation": "0.6", "current_hidden_units": "1"},
            {"juniper_cascor_candidate_correlation": "", "current_hidden_units": "1"},
        ]
        result = self.stats.correlation_per_round(rows)
        self.assertEqual(result["per_round"], [{"hidden_units": 0, "best_correlation": 0.7}, {"hidden_units": 1, "best_correlation": 0.6}])
        self.assertEqual(result["max"], 0.7)
        self.assertEqual(result["samples"], 3)

    def test_build_stats_sequence_shapes_and_summary(self) -> None:
        manifest = {
            "run_id": "r-unit",
            "experiment": {"name": "e", "description": None},
            "config_sha256": "x",
            "seeds": {"experiment": 1, "dataset": 1},
            "git": {"juniper-ml": {"head_sha": "a" * 40, "dirty": False}},
            "packages": {"juniper-data": {"version": "0.6.0"}},
            "timings": {"total": 1.0},
            "outcome": "succeeded",
            "acceptance": {"ok": True, "reasons": []},
            "metrics_scraped": {"grafana_bridge": False, "present": False},
            "collect_errors": [],
            "drive_loop": {},
            "driver": {"plots": {"skipped": []}},
            "g6_shape_check": None,
            "dataset": {
                "dataset_id": "d",
                "generator": "irregular_sine",
                "version": "1",
                "split": "train",
                "params": {},
                "meta": {"sequence": True, "n_samples": 12, "lookback": 16, "n_features": 3, "n_train": 8, "n_test": 4, "task_type": "regression"},
            },
        }
        stats = self.stats.build_stats(manifest, kind="recurrence", train_summary={"final_metrics": {"r2": 0.9}}, train_config={"theta": None, "d": 8})
        self.assertEqual(stats["dataset"]["shapes"]["kind"], "sequence")
        self.assertEqual(stats["dataset"]["shapes"]["n_windows"], 12)
        self.assertEqual(stats["dataset"]["shapes"]["lookback"], 16)
        self.assertIn("data-driven", stats["recurrence"]["theta"]["note"])
        self.assertEqual(stats["identity"]["packages"], {"juniper-data": "0.6.0"})
        rendered = self.stats.render_summary_md(stats)
        self.assertIn("r-unit", rendered)
        self.assertIn("## recurrence", rendered)
        self.assertIn("n_windows=12", rendered)

    def test_degraded_notes_surface(self) -> None:
        manifest = {
            "run_id": "r",
            "experiment": {"name": "e"},
            "timings": {},
            "outcome": "succeeded",
            "acceptance": {"ok": False, "reasons": []},
            "drive_loop": {"metrics_sampling_errors": 2},
            "collect_errors": [{"artifact": "topology", "essential": "false", "error": "HTTP 500"}],
            "driver": {"plots": {"skipped": [{"name": "eval_metrics", "reason": "disabled"}]}},
            "g6_shape_check": {"ok": False},
            "dataset": {"meta": {}},
            "metrics_scraped": {},
        }
        stats = self.stats.build_stats(manifest, kind="cascor", series_rows=[], metrics_final={"eval_metrics": {"enabled": False}})
        notes = stats["provenance"]["degraded_notes"]
        self.assertTrue(any("G-3" in note for note in notes))
        self.assertTrue(any("topology" in note for note in notes))
        self.assertTrue(any("eval_metrics" in note for note in notes))
        self.assertTrue(any("G-6" in note for note in notes))
        self.assertTrue(any("eval metrics disabled" in note for note in notes))


class SubprocessSmokeTest(unittest.TestCase):
    """One arm through the real CLI so the ``sys.exit`` wiring stays pinned."""

    def test_validation_error_exits_2(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="run-experiment-sub-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        config = _write_config(tmp, {"experiment": {"name": "x", "seed": 1}, "training": {}, "dataset": {"generator": "spiral"}})
        run_dir = tmp / "run"
        run_dir.mkdir()
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--config", str(config), "--run-dir", str(run_dir)],
            capture_output=True,
            text=True,
            timeout=60,
            env=RedactedEnv(os.environ),
            check=False,
        )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("schema_version", proc.stderr)

    def test_usage_error_exits_2(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=60,
            env=RedactedEnv(os.environ),
            check=False,
        )
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
