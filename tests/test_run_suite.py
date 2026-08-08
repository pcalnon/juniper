"""Tests for ``util/experiments/run_suite.py`` (CLI experimentation plan §13.1/§13.2, Wave 7.1).

``util/`` is not pre-commit-lint-gated, so this unittest is the gate. Everything
is hermetic: the launcher and driver are PATH-less stub scripts injected via the
``JUNIPER_SUITE_LAUNCHER`` / ``JUNIPER_SUITE_DRIVER`` seams, and the run root is
redirected by patching the module's ``DEFAULT_RUN_ROOT`` — no live stack, no
live services, no writes outside tempdirs.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "run_suite.py"

spec = importlib.util.spec_from_file_location("run_suite", MODULE_PATH)
run_suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_suite)


BASE_CONFIG = """\
schema_version: 1
experiment:
  name: fixture
  seed: 7
service:
  log_level: INFO
dataset:
  generator: spiral
  params:
    n_spirals: 2
    n_points_per_spiral: 100
    seed: 7
training:
  params:
    max_hidden_units: 2
outputs:
  plots: []
  max_wall_seconds: 60
"""

SUITE_TEMPLATE = """\
schema_version: 1
suite:
  name: t-suite
  description: test
  app: cascor
  base_config:
    - {base}
  seed_policy: {seed_policy}
execution:
  mode: sequential
  continue_on_failure: {cof}
  per_run_timeout_seconds: 60
matrix:
  training.params.max_hidden_units: [2, 4]
outputs:
  suite_dir: {suite_dir}
"""


def _write_stub_launcher(path: Path, marker_dir: Path, fail_up: bool = False) -> None:
    path.write_text("#!/usr/bin/env bash\n" f"MARKERS={marker_dir}\n" 'if [[ "$1" == "--up" ]]; then\n' f"  {'exit 1' if fail_up else ''}\n" '  n=$(ls "$MARKERS" 2>/dev/null | grep -c up- || true)\n' '  touch "$MARKERS/up-$n"\n' '  echo "=== Experiment run stub-run-$n is up ==="\n' "  exit 0\n" "fi\n" 'if [[ "$1" == "--down" ]]; then touch "$MARKERS/down-$2"; exit 0; fi\n' "exit 2\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _write_stub_driver(path: Path, outcome: str = "succeeded", per_cell: "dict | None" = None) -> None:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys, pathlib\n"
        "args = dict(zip(sys.argv[1::2], sys.argv[2::2]))\n"
        "run_dir = pathlib.Path(args['--run-dir'])\n"
        "run_dir.mkdir(parents=True, exist_ok=True)\n"
        f"per_cell = {per_cell!r}\n"
        f"outcome = {outcome!r}\n"
        "cfg = pathlib.Path(args['--config']).read_text()\n"
        "if per_cell:\n"
        "    for token, oc in per_cell.items():\n"
        "        if token in cfg:\n"
        "            outcome = oc\n"
        "(run_dir / 'manifest.json').write_text(json.dumps({'outcome': outcome}))\n"
        "sys.exit(0 if outcome == 'succeeded' else 1)\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class ExpandTest(unittest.TestCase):
    def _doc(self, extra: str = "") -> "tuple[dict, Path]":
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "base.yaml").write_text(BASE_CONFIG)
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text("schema_version: 1\n" "suite:\n  name: s\n  app: cascor\n  base_config: [base.yaml]\n" "matrix:\n  training.params.max_hidden_units: [4, 8, 16]\n  training.params.candidate_pool_size: [4, 8]\n" + extra)
        return run_suite.load_suite(suite_yaml), suite_yaml

    def test_product_exclude_include_and_determinism(self) -> None:
        doc, path = self._doc("exclude:\n  - {training.params.max_hidden_units: 16, training.params.candidate_pool_size: 8}\ninclude:\n  - name: extra\n    overrides: {training.params.max_hidden_units: 32}\n")
        cells = run_suite.expand_cells(doc, path)
        self.assertEqual(len(cells), 3 * 2 - 1 + 1)
        self.assertEqual(cells[-1]["name"], "extra")
        again = run_suite.expand_cells(doc, path)
        self.assertEqual([c["cell_id"] for c in cells], [c["cell_id"] for c in again])
        self.assertNotIn({"training.params.max_hidden_units": 16, "training.params.candidate_pool_size": 8}, [c["overrides"] for c in cells])

    def test_validation_rejections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.yaml"
            for body, msg in (
                ("schema_version: 2\nsuite: {name: s, app: cascor, base_config: [b]}\n", "schema_version"),
                ("schema_version: 1\nsuite: {name: s, app: nope, base_config: [b]}\n", "app"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: []}\n", "base_config"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: [b]}\nexecution: {mode: parallel}\n", "sequential"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: [b]}\nbogus: {}\n", "unknown"),
            ):
                bad.write_text(body)
                with self.assertRaisesRegex(run_suite.SuiteError, msg):
                    run_suite.load_suite(bad)


class MaterialiseTest(unittest.TestCase):
    def test_overrides_and_per_cell_seed_applied_and_driver_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.yaml"
            base.write_text(BASE_CONFIG)
            cell = {"cell_id": "c003-abcd1234", "index": 3, "name": None, "config_path": str(base), "overrides": {"training.params.max_hidden_units": 8}}
            validate = run_suite._driver_validator()
            self.assertIsNotNone(validate, "the real driver's load_config must be importable")
            out = run_suite.materialise_cell(cell, {"name": "s", "seed_policy": "per_cell"}, root / "suite", validate)
            import yaml

            resolved = yaml.safe_load(out.read_text())
            self.assertEqual(resolved["training"]["params"]["max_hidden_units"], 8)
            self.assertEqual(resolved["experiment"]["seed"], 7 + 3)
            self.assertEqual(resolved["dataset"]["params"]["seed"], 7 + 3)
            self.assertEqual(resolved["experiment"]["name"], "s-c003-abcd1234")

    def test_bad_override_path_is_a_suite_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.yaml"
            base.write_text(BASE_CONFIG)
            cell = {"cell_id": "c000-ffff0000", "index": 0, "name": None, "config_path": str(base), "overrides": {"experiment.name.deep": 1}}
            with self.assertRaisesRegex(run_suite.SuiteError, "non-mapping"):
                run_suite.materialise_cell(cell, {"name": "s"}, root / "suite", None)


class MainLoopTest(unittest.TestCase):
    def _setup(self, *, cof: str = "true", fail_token: "str | None" = None, fail_up: bool = False):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(BASE_CONFIG)
        suite_dir = root / "suite-out"
        (root / "suite.yaml").write_text(SUITE_TEMPLATE.format(base=root / "base.yaml", seed_policy="fixed", cof=cof, suite_dir=suite_dir))
        markers = root / "markers"
        markers.mkdir()
        run_root = root / "runroot"
        run_root.mkdir()
        launcher = root / "stub_launcher.bash"
        _write_stub_launcher(launcher, markers, fail_up=fail_up)
        driver = root / "stub_driver.py"
        per_cell = {fail_token: "failed"} if fail_token else None
        _write_stub_driver(driver, per_cell=per_cell)
        self._env = {"JUNIPER_SUITE_LAUNCHER": str(launcher), "JUNIPER_SUITE_DRIVER": str(driver), "JUNIPER_SUITE_PYTHON": sys.executable}
        self._old_run_root = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root
        self.addCleanup(lambda: setattr(run_suite, "DEFAULT_RUN_ROOT", self._old_run_root))
        return root, suite_dir, markers, run_root

    def _main(self, *argv: str) -> "tuple[int, str]":
        buf = io.StringIO()
        old = {k: os.environ.get(k) for k in self._env}
        os.environ.update(self._env)
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(list(argv))
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        return rc, buf.getvalue()

    def test_happy_path_registry_index_aggregate_and_teardown(self) -> None:
        root, suite_dir, markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual([r["outcome"] for r in registry], ["succeeded", "succeeded"])
        self.assertTrue(all(r["run_id"].startswith("stub-run-") for r in registry))
        self.assertEqual(len(list(markers.glob("down-*"))), 2, "every cell must be torn down")
        index = [json.loads(line) for line in (run_root / "index.jsonl").read_text().splitlines()]
        self.assertEqual(len(index), 2)
        csv_text = (suite_dir / "aggregate.csv").read_text()
        self.assertIn("training.params.max_hidden_units", csv_text)
        self.assertIn("REPORT.md", out)
        manifest = json.loads((suite_dir / "suite_manifest.json").read_text())
        self.assertEqual(manifest["schema"], "juniper-experiment-suite/1")

    def test_continue_on_failure_runs_all_and_exits_one(self) -> None:
        root, suite_dir, markers, _ = self._setup(fail_token="max_hidden_units: 2")
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1, msg=out)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(len(registry), 2, "continue_on_failure must run the remaining cells")
        self.assertEqual({r["outcome"] for r in registry}, {"failed", "succeeded"})
        self.assertEqual(len(list(markers.glob("down-*"))), 2)

    def test_stop_on_failure_halts_the_loop(self) -> None:
        root, suite_dir, _, _ = self._setup(cof="false", fail_token="max_hidden_units: 2")
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(len(registry), 1, "continue_on_failure=false must stop after the first failure")

    def test_resume_skips_succeeded_cells(self) -> None:
        root, suite_dir, markers, _ = self._setup()
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0)
        ups_before = len(list(markers.glob("up-*")))
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--resume", suite_dir.name)
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len(list(markers.glob("up-*"))), ups_before, "resume must not re-run succeeded cells")
        self.assertIn("skipped (resume)", out)

    def test_launcher_up_failure_records_error_and_exits_one(self) -> None:
        root, suite_dir, markers, _ = self._setup(fail_up=True)
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertTrue(all("launcher --up failed" in (r.get("error") or "") for r in registry))
        self.assertEqual(len(list(markers.glob("down-*"))), 0, "no teardown without a run_id")

    def test_dry_run_writes_nothing(self) -> None:
        root, suite_dir, markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("2 cells", out)
        self.assertFalse(suite_dir.exists(), "--dry-run must not create the suite dir")
        self.assertFalse((run_root / "index.jsonl").exists())
        self.assertEqual(len(list(markers.iterdir())), 0)

    def test_only_unknown_cell_id_exits_two(self) -> None:
        root, _, _, _ = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--only", "c999-deadbeef")
        self.assertEqual(rc, 2)
        self.assertIn("not in the expansion", out)


if __name__ == "__main__":
    unittest.main()
