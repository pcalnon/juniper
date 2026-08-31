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
    path.write_text("#!/usr/bin/env bash\n" f"MARKERS={marker_dir}\n" 'if [[ "$1" == "--up" ]]; then\n' f"  {'exit 1' if fail_up else ''}\n" '  touch "$MARKERS/up-$$"\n' '  echo "=== Experiment run stub-run-$$ is up ==="\n' "  exit 0\n" "fi\n" 'if [[ "$1" == "--down" ]]; then touch "$MARKERS/down-$2"; exit 0; fi\n' "exit 2\n")
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
        # argv is recorded so tests can assert what the suite actually forwarded to the
        # driver (e.g. --stall-seconds); run_suite only reads 'outcome' from the manifest.
        "(run_dir / 'manifest.json').write_text(json.dumps({'outcome': outcome, 'argv': sys.argv[1:]}))\n"
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

    def _resolve_with_project_dir(self, suite_yaml: "Path", config_rel: str, project_dir: "str | None"):
        """Call _resolve_base_config with JUNIPER_EXP_PROJECT_DIR set, restoring it after."""
        old = os.environ.get("JUNIPER_EXP_PROJECT_DIR")
        if project_dir is None:
            os.environ.pop("JUNIPER_EXP_PROJECT_DIR", None)
        else:
            os.environ["JUNIPER_EXP_PROJECT_DIR"] = project_dir
        try:
            return run_suite._resolve_base_config(suite_yaml, config_rel)
        finally:
            if old is None:
                os.environ.pop("JUNIPER_EXP_PROJECT_DIR", None)
            else:
                os.environ["JUNIPER_EXP_PROJECT_DIR"] = old

    def test_project_dir_override_beats_a_resolving_literal(self) -> None:
        """The override WINS over a literal that exists -- it is an override, not a fallback.

        Launched from the canonical juniper-ml checkout the literal always resolves, so while
        the override was consulted second, a campaign pinning cascor to a worktree took its
        CODE from the worktree and its CONFIG from the primary. Nothing in the manifest showed
        that mixed tree, which is why this is pinned rather than left to review.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "../cascor-checkouts/juniper-cascor/conf/experiments/base.yaml"
            suite_dir = root / "suites"
            suite_dir.mkdir(parents=True)
            suite_yaml = suite_dir / "suite.yaml"
            suite_yaml.write_text("schema_version: 1\n")

            primary = root / "cascor-checkouts" / "juniper-cascor" / "conf" / "experiments"
            primary.mkdir(parents=True)
            (primary / "base.yaml").write_text(BASE_CONFIG)
            # Precondition: the literal walk really does resolve, so the test is not vacuous.
            self.assertTrue((suite_yaml.parent / rel).resolve().is_file())

            pinned = root / "pinned" / "juniper-cascor" / "conf" / "experiments"
            pinned.mkdir(parents=True)
            (pinned / "base.yaml").write_text(BASE_CONFIG)

            self.assertEqual(self._resolve_with_project_dir(suite_yaml, rel, str(root / "pinned")), pinned / "base.yaml")
            # Unset, the literal still wins -- the override changes nothing when absent.
            self.assertEqual(self._resolve_with_project_dir(suite_yaml, rel, None), (primary / "base.yaml").resolve())

    def test_a_nonexistent_override_falls_back_to_the_literal(self) -> None:
        """A stale or mistyped override degrades to the literal rather than failing the suite."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "../cascor-checkouts/juniper-cascor/conf/experiments/base.yaml"
            suite_dir = root / "suites"
            suite_dir.mkdir(parents=True)
            suite_yaml = suite_dir / "suite.yaml"
            suite_yaml.write_text("schema_version: 1\n")
            primary = root / "cascor-checkouts" / "juniper-cascor" / "conf" / "experiments"
            primary.mkdir(parents=True)
            (primary / "base.yaml").write_text(BASE_CONFIG)

            resolved = self._resolve_with_project_dir(suite_yaml, rel, str(root / "does-not-exist"))
            self.assertEqual(resolved, (primary / "base.yaml").resolve())

    def test_project_dir_rebase_for_sibling_base_configs(self) -> None:
        """Wave 7.3: from a worktree, sibling-relative base_config paths rebase onto
        JUNIPER_EXP_PROJECT_DIR from their first juniper-* component; cell ids hash
        the RELATIVE reference so they match the canonical checkout's."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eco = root / "ecosystem" / "juniper-cascor" / "conf" / "experiments"
            eco.mkdir(parents=True)
            (eco / "base.yaml").write_text(BASE_CONFIG)
            suite_dir = root / "elsewhere" / "suites"
            suite_dir.mkdir(parents=True)
            suite_yaml = suite_dir / "suite.yaml"
            suite_yaml.write_text("schema_version: 1\nsuite:\n  name: s\n  app: cascor\n  base_config: [../../../../juniper-cascor/conf/experiments/base.yaml]\nmatrix:\n  training.params.max_hidden_units: [2]\n")
            doc = run_suite.load_suite(suite_yaml)
            old = os.environ.get("JUNIPER_EXP_PROJECT_DIR")
            os.environ["JUNIPER_EXP_PROJECT_DIR"] = str(root / "ecosystem")
            try:
                cells = run_suite.expand_cells(doc, suite_yaml)
            finally:
                if old is None:
                    os.environ.pop("JUNIPER_EXP_PROJECT_DIR", None)
                else:
                    os.environ["JUNIPER_EXP_PROJECT_DIR"] = old
            self.assertEqual(cells[0]["config_path"], str(eco / "base.yaml"))

    def test_validation_rejections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.yaml"
            for body, msg in (
                ("schema_version: 2\nsuite: {name: s, app: cascor, base_config: [b]}\n", "schema_version"),
                ("schema_version: 1\nsuite: {name: s, app: nope, base_config: [b]}\n", "app"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: []}\n", "base_config"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: [b]}\nexecution: {mode: bogus}\n", "sequential.*parallel"),
                # The cascor-parallel case moved to CascorParallelFloorTest: since the Q-6 floor
                # landed its outcome depends on the resolved cascor tree's VERSION, so asserted
                # here it would pass or fail according to whether the host happens to have a
                # juniper-cascor sibling — the environment-dependent-test class.
                ("schema_version: 1\nsuite: {name: s, app: recurrence, base_config: [b]}\nexecution: {mode: parallel, max_parallel: 0}\n", "max_parallel"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: [b]}\nbogus: {}\n", "unknown"),
            ):
                bad.write_text(body)
                with self.assertRaisesRegex(run_suite.SuiteError, msg):
                    run_suite.load_suite(bad)


class CascorParallelFloorTest(unittest.TestCase):
    """Q-6: cascor parallel cells are gated on the LAUNCHED tree's version, and fail closed.

    Every case pins ``JUNIPER_EXP_CASCOR_SRC_DIR`` at a tree this test builds, so the outcome
    never depends on whether the host has a juniper-cascor sibling checkout. Asserting the old
    blanket refusal without that pin is what made the previous placement environment-dependent.
    """

    SUITE = "schema_version: 1\n" "suite: {{name: s, app: cascor, base_config: [b]}}\n" "execution: {{mode: {mode}, max_parallel: {par}}}\n"

    def setUp(self) -> None:
        self._saved = {k: os.environ.get(k) for k in ("JUNIPER_EXP_CASCOR_SRC_DIR", "JUNIPER_EXP_PROJECT_DIR")}

    def tearDown(self) -> None:
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _tree(self, root: Path, version: "str | None") -> Path:
        tree = root / "juniper-cascor"
        (tree / "src").mkdir(parents=True, exist_ok=True)
        if version is not None:
            (tree / "pyproject.toml").write_text(f'[project]\nname = "juniper-cascor"\nversion = "{version}"\n')
        os.environ["JUNIPER_EXP_CASCOR_SRC_DIR"] = str(tree / "src")
        return tree

    def _suite(self, root: Path, mode: str = "parallel", par: int = 4) -> Path:
        path = root / "suite.yaml"
        path.write_text(self.SUITE.format(mode=mode, par=par))
        return path

    def test_at_floor_allows_parallel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, ".".join(str(p) for p in run_suite.CASCOR_PARALLEL_FLOOR))
            self.assertIsInstance(run_suite.load_suite(self._suite(root)), dict)

    def test_below_floor_refuses_and_names_the_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")
            with self.assertRaisesRegex(run_suite.SuiteError, r"0\.9\.0"):
                run_suite.load_suite(self._suite(root))

    def test_unreadable_version_fails_closed(self) -> None:
        """An unknowable version must not resolve the same way as a compliant one."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, None)  # no pyproject.toml -> version unknowable
            with self.assertRaisesRegex(run_suite.SuiteError, "could not be read"):
                run_suite.load_suite(self._suite(root))

    def test_sequential_is_never_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")  # below the floor, and irrelevant in sequential mode
            self.assertIsInstance(run_suite.load_suite(self._suite(root, mode="sequential", par=1)), dict)

    def test_recurrence_parallel_is_never_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")
            path = root / "rec.yaml"
            path.write_text("schema_version: 1\n" "suite: {name: s, app: recurrence, base_config: [b]}\n" "execution: {mode: parallel, max_parallel: 4}\n")
            self.assertIsInstance(run_suite.load_suite(path), dict)


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
    def _setup(self, *, cof: str = "true", fail_marker: "str | None" = None, fail_up: bool = False):
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
        per_cell = {fail_marker: "failed"} if fail_marker else None
        _write_stub_driver(driver, per_cell=per_cell)
        self._env = {"JUNIPER_SUITE_LAUNCHER": str(launcher), "JUNIPER_SUITE_DRIVER": str(driver), "JUNIPER_SUITE_PYTHON": sys.executable}
        self._old_run_root = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root  # type: ignore[attr-defined]
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

    def _driver_argvs(self, run_root: Path) -> "list[list[str]]":
        return [json.loads(m.read_text())["argv"] for m in sorted(run_root.glob("*/manifest.json"))]

    def test_stall_seconds_is_forwarded_to_the_driver(self) -> None:
        """execution.stall_seconds must reach the driver's Q-2 detector.

        The detector watches ``current_epoch``, which does not advance while the CANDIDATE
        pool trains, so a long candidate phase reads as a stall. Without this passthrough a
        suite cannot raise the window and healthy cells are killed at the 120 s default --
        the P4 E-A grid lost every ``candidate_pool_size >= 16`` cell that way.
        """
        root, _suite_dir, _markers, run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 60", "  per_run_timeout_seconds: 60\n  stall_seconds: 900"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertIn("--stall-seconds", argv)
            self.assertEqual(argv[argv.index("--stall-seconds") + 1], "900.0")

    def test_absent_stall_seconds_leaves_the_driver_default_alone(self) -> None:
        """Omitting the key must not pass the flag at all (the driver owns its default)."""
        root, _suite_dir, _markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertNotIn("--stall-seconds", argv)

    def test_max_wall_seconds_is_forwarded_to_the_driver(self) -> None:
        """execution.max_wall_seconds must reach the driver's Q-2 wall-clock budget.

        The ml#1069 class, one field over. A suite could always reach the budget through
        a dotted ``matrix`` / ``include`` override -- ``suites/p4/e-i-cascor-cap-ceiling
        .yaml`` sets ``outputs.max_wall_seconds`` exactly that way -- but an un-overridden
        cell silently inherited ``base_config``'s value (3600 s) with no signal. Measured
        on the E-I run (``20260814T091542Z``): cap 32 -> 1497.4 s, cap 64 -> 2907.1 s,
        cap 128 -> 4243.6 s, so the cap-128 cell would have been truncated by that
        inherited default and cap 64 cleared it by only 693 s.
        """
        root, _suite_dir, _markers, run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 60", "  per_run_timeout_seconds: 60\n  max_wall_seconds: 14400"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertIn("--max-wall-seconds", argv)
            self.assertEqual(argv[argv.index("--max-wall-seconds") + 1], "14400.0")

    def test_absent_max_wall_seconds_leaves_the_driver_default_alone(self) -> None:
        """Omitting the key must not pass the flag at all (the driver owns its default)."""
        root, _suite_dir, _markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertNotIn("--max-wall-seconds", argv)

    def test_both_budget_flags_forward_independently(self) -> None:
        """stall_seconds and max_wall_seconds are orthogonal Q-2 knobs."""
        root, _suite_dir, _markers, run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 60", "  per_run_timeout_seconds: 60\n  stall_seconds: 900\n  max_wall_seconds: 14400"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertEqual(argv[argv.index("--stall-seconds") + 1], "900.0")
            self.assertEqual(argv[argv.index("--max-wall-seconds") + 1], "14400.0")

    def test_max_wall_seconds_typo_still_rejected(self) -> None:
        """The allow-list widens by exactly one -- a near-miss spelling must still fail."""
        root, _suite_dir, _markers, _run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 60", "  per_run_timeout_seconds: 60\n  max_wall_second: 14400"))
        rc, _out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 2)

    def test_dry_run_shows_the_max_wall_flag(self) -> None:
        """The dry-run preview must show the budget an operator is about to spend."""
        root, _suite_dir, _markers, _run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 60", "  per_run_timeout_seconds: 60\n  max_wall_seconds: 14400"))
        rc, out = self._main("--suite", str(suite_yaml), "--dry-run")
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("--max-wall-seconds 14400.0", out)

    def test_unknown_execution_key_still_rejected(self) -> None:
        """The new key widens the allow-list by exactly one — typos must still fail."""
        root, _suite_dir, _markers, _run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 60", "  per_run_timeout_seconds: 60\n  stall_second: 900"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 2, msg=out)
        self.assertIn("unknown execution: keys", out)

    def test_continue_on_failure_runs_all_and_exits_one(self) -> None:
        root, suite_dir, markers, _ = self._setup(fail_marker="max_hidden_units: 2")
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1, msg=out)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(len(registry), 2, "continue_on_failure must run the remaining cells")
        self.assertEqual({r["outcome"] for r in registry}, {"failed", "succeeded"})
        self.assertEqual(len(list(markers.glob("down-*"))), 2)

    def test_stop_on_failure_halts_the_loop(self) -> None:
        root, suite_dir, _, _ = self._setup(cof="false", fail_marker="max_hidden_units: 2")
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


PARALLEL_SUITE_TEMPLATE = """\
schema_version: 1
suite:
  name: p-suite
  description: test
  app: recurrence
  base_config:
    - {base}
execution:
  mode: parallel
  max_parallel: 2
  continue_on_failure: true
  per_run_timeout_seconds: 60
matrix:
  training.params.max_hidden_units: [2, 4]
outputs:
  suite_dir: {suite_dir}
"""


class ParallelModeTest(MainLoopTest):
    """Wave 7.5: bounded-parallel execution (recurrence app; cascor refuses at load)."""

    def test_parallel_happy_path_records_budget_and_both_cells(self) -> None:
        root, suite_dir, markers, run_root = self._setup()
        (root / "suite.yaml").write_text(PARALLEL_SUITE_TEMPLATE.format(base=root / "base.yaml", suite_dir=suite_dir))
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(len(registry), 2)
        self.assertEqual({r["outcome"] for r in registry}, {"succeeded"})
        for r in registry:
            self.assertIsNotNone(r["thread_budget"], "parallel cells must record the H-11 budget env")
            self.assertIn("OMP_NUM_THREADS", r["thread_budget"])
            self.assertNotIn("CASCOR_NUM_PROCESSES", r["thread_budget"], "recurrence budget must not carry the cascor knob")
        self.assertEqual(len(list(markers.glob("down-*"))), 2, "every parallel cell must be torn down")
        index = [json.loads(line) for line in (run_root / "index.jsonl").read_text().splitlines()]
        self.assertEqual(len(index), 2, "index appends must be lock-safe under parallelism")

    def test_sequential_rows_have_no_budget(self) -> None:
        root, suite_dir, _, _ = self._setup()
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertTrue(all(r["thread_budget"] is None for r in registry))

    def test_budget_split_math(self) -> None:
        budget = run_suite.thread_budget_env("cascor", max_parallel=2)
        nproc = os.cpu_count() or 1
        self.assertEqual(budget["CASCOR_NUM_PROCESSES"], str(max(1, nproc // 4)))
        self.assertEqual(budget["OMP_NUM_THREADS"], "2")
        rec = run_suite.thread_budget_env("recurrence", max_parallel=2)
        self.assertEqual(rec["OMP_NUM_THREADS"], str(max(1, nproc // 4)))
        self.assertNotIn("CASCOR_NUM_PROCESSES", rec)


class ProvenanceEnvTest(unittest.TestCase):
    """D-C: the suite is the only layer that knows the cell id and the suite name.

    ``experiment_stack.bash`` forwards both into cascor's process env, so every snapshot a
    cell writes records which cell produced it. Without this the launcher is invoked with
    ``--experiment <cell_id>`` and the SUITE identity is lost -- which is exactly the half of
    "find the model from the E-I cap-128 cell" that the census could not answer.
    """

    def _capture_up_env(self, *, suite_name: "str | None") -> dict:
        import subprocess as _subprocess
        from unittest import mock

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        cell_yaml = Path(tmp.name) / "experiment.yaml"
        cell_yaml.write_text("schema_version: 1\n")
        captured: dict = {}

        def fake_run(argv, **kwargs):
            captured.setdefault("env", kwargs.get("env"))
            return _subprocess.CompletedProcess(argv, 1, stdout="", stderr="stub: no banner")

        cell = {"cell_id": "c007-9f3ab12c", "name": "cap-128", "overrides": {}}
        with mock.patch.object(run_suite.subprocess, "run", side_effect=fake_run):
            run_suite.execute_cell(cell, cell_yaml, "cascor", 5.0, Path("/bin/true"), Path("/bin/true"), sys.executable, None, None, None, suite_name)
        self.assertIsNotNone(captured.get("env"), "execute_cell must pass an explicit env so provenance reaches the launcher")
        return captured["env"]

    def test_cell_id_reaches_the_launcher(self) -> None:
        env = self._capture_up_env(suite_name="e-i-cap-ceiling")
        self.assertEqual(env["JUNIPER_CASCOR_CELL_ID"], "c007-9f3ab12c")

    def test_suite_name_is_the_experiment_not_the_cell_id(self) -> None:
        """The launcher receives ``--experiment <cell_id>``; without this override the
        recorded experiment would duplicate the cell id and the suite would be unrecoverable."""
        env = self._capture_up_env(suite_name="e-i-cap-ceiling")
        self.assertEqual(env["JUNIPER_CASCOR_EXPERIMENT"], "e-i-cap-ceiling")
        self.assertNotEqual(env["JUNIPER_CASCOR_EXPERIMENT"], env["JUNIPER_CASCOR_CELL_ID"])

    def test_absent_suite_name_leaves_the_launcher_default(self) -> None:
        """No suite name -> no override, so ``experiment_stack.bash`` falls back to its own
        ``EXPERIMENT``. Setting an empty string instead would blank the identity."""
        env = self._capture_up_env(suite_name=None)
        self.assertNotIn("JUNIPER_CASCOR_EXPERIMENT", env)
        self.assertEqual(env["JUNIPER_CASCOR_CELL_ID"], "c007-9f3ab12c")
