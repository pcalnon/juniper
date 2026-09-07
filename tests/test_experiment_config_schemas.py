"""Wave 3.5 drift gate: every shipped ``conf/experiments/*.yaml`` maps to real app surface.

The SS10.6 row-3 gate for the CLI experimentation program: walks the sibling checkouts'
reference experiment YAMLs (cascor Wave 3.2, recurrence Wave 3.4) and asserts, per file,

* the juniper-ml driver's ``load_config`` accepts it (the SS5.6 validator -- unknown
  blocks/keys, ``schema_version``, mandatory seed, per-kind plot names, infra keys), and
* every ``service:`` key names a REAL field of the target app's ``Settings`` model --
  extracted STATICALLY via AST from the sibling's ``settings.py`` (cascor ``Settings``;
  recurrence ``Settings`` + the in-repo juniper-service-core ``SettingsBase`` it
  subclasses), so the gate bites when an app renames a setting without touching the
  shipped YAMLs. No app import is needed (cascor's ``Settings`` module imports torch).

Skip semantics mirror ``test_doc_tools_drift.py``: the cross-repo walk runs under
``GITHUB_ACTIONS=true`` (the weekly full-check clones siblings) or with
``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``; it also skips loudly when a sibling checkout or
its ``conf/experiments/`` is absent. The AST-extractor self-check always runs (in-repo
``SettingsBase``), so the module is never a silent no-op.
"""

from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402  (path-invoked util import)


def _find_ecosystem_root(start: Path) -> Path:
    """Locate the directory holding the sibling repos, tolerating an in-repo worktree.

    ``REPO_ROOT.parent`` is right for a normal checkout (``Juniper/juniper-ml``) and for CI, but
    juniper-ml keeps session worktrees INSIDE itself at ``.claude/worktrees/<name>``. From one of
    those, ``REPO_ROOT.parent`` is ``.claude/worktrees`` and every sibling lookup misses -- so the
    whole cross-repo walk skipped with a plausible "sibling conf dir not on disk" message while
    checking nothing. A vacuous skip is harder to notice than a failure, because the run still
    reads OK.

    Walk up for the first ancestor that actually contains a sibling; fall back to the old
    behaviour so nothing changes where it was already correct.
    """
    for candidate in start.parents:
        if (candidate / "juniper-cascor").is_dir():
            return candidate
    return start.parent


ECOSYSTEM_ROOT = _find_ecosystem_root(REPO_ROOT)
CASCOR_SETTINGS = ECOSYSTEM_ROOT / "juniper-cascor" / "src" / "api" / "settings.py"
CASCOR_CONF = ECOSYSTEM_ROOT / "juniper-cascor" / "conf" / "experiments"
RECURRENCE_SETTINGS = ECOSYSTEM_ROOT / "juniper-recurrence" / "juniper-recurrence" / "juniper_recurrence" / "settings.py"
RECURRENCE_CONF = ECOSYSTEM_ROOT / "juniper-recurrence" / "conf" / "experiments"
SERVICE_CORE_SETTINGS = REPO_ROOT / "juniper-service-core" / "juniper_service_core" / "settings.py"


def _cross_repo_enabled() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL") == "1"


def _class_field_names(path: Path, class_names: set[str]) -> set[str]:
    """AST-extract the annotated class-level field names of the named Settings classes."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fields: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in class_names:
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    name = stmt.target.id
                    if not name.startswith("_") and name != "model_config":
                        fields.add(name)
    return fields


class ExperimentConfigSchemaDriftTest(unittest.TestCase):
    """SS10.6: shipped reference YAMLs must keep mapping to real app fields."""

    def _gate(self, conf_dir: Path, settings_paths: list[Path]) -> None:
        if not _cross_repo_enabled():
            self.skipTest("cross-repo drift walk gated (CI clones siblings; locally set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1)")
        if not conf_dir.is_dir():
            self.skipTest(f"sibling conf dir not on disk: {conf_dir}")
        for path in settings_paths:
            if not path.is_file():
                self.skipTest(f"sibling settings module not on disk: {path}")

    def _check_dir(self, conf_dir: Path, expected_kind: str, sources: list[tuple[Path, set[str]]]) -> None:
        fields: set[str] = set()
        for path, class_names in sources:
            fields |= _class_field_names(path, class_names)
        self.assertTrue(fields, "AST field extraction found nothing -- did the settings module layout change?")

        yaml_files = sorted(conf_dir.glob("*.yaml"))
        self.assertTrue(yaml_files, f"no reference YAMLs found in {conf_dir}")
        for yaml_file in yaml_files:
            with self.subTest(yaml=yaml_file.name):
                config = rx.load_config(yaml_file)  # SS5.6 driver-side validation (raises on drift)
                self.assertEqual(config["kind"], expected_kind, f"{yaml_file.name}: unexpected app kind")
                raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
                service = raw.get("service") or {}
                unknown = sorted(key for key in service if key not in fields)
                self.assertEqual(unknown, [], f"{yaml_file.name}: service keys not in the app's Settings fields: {unknown}")

    def test_cascor_reference_yamls(self) -> None:
        self._gate(CASCOR_CONF, [CASCOR_SETTINGS])
        self._check_dir(CASCOR_CONF, "cascor", [(CASCOR_SETTINGS, {"Settings"})])

    def test_recurrence_reference_yamls(self) -> None:
        self._gate(RECURRENCE_CONF, [RECURRENCE_SETTINGS, SERVICE_CORE_SETTINGS])
        self._check_dir(RECURRENCE_CONF, "recurrence", [(RECURRENCE_SETTINGS, {"Settings"}), (SERVICE_CORE_SETTINGS, {"SettingsBase"})])


def epoch_budget_split(params: dict) -> bool:
    """True when ``max_epochs`` is set without ``output_epochs`` -- the silent-divergence shape.

    On the SERVICE path ``max_epochs`` bounds only the INITIAL output pass; every later pass reads
    ``output_epochs``, which falls back to ``_PROJECT_MODEL_OUTPUT_EPOCHS = 10000``. The direct CLI
    instead ALIASES ``max_epochs -> output_epochs``, so the two paths silently disagree.
    """
    return "max_epochs" in params and "output_epochs" not in params


# Configs allowed to carry the split, each with the reason it is legitimate. An entry here is a
# CLAIM that the divergence is intended, not a way to quiet the gate.
DELIBERATE_EPOCH_SPLITS = {
    "spiral-baseline.yaml": "service-only reference budget; the split is documented in run_experiment.py's _warn_epoch_budget_split docstring",
}

# Configs whose intent has NOT been decided. Separated from the blessed set deliberately: folding an
# undecided case into DELIBERATE_EPOCH_SPLITS would launder "nobody has looked at this" into "this is
# on purpose", which is precisely how the original defect survived in spiral-smoke.yaml for a month.
# EMPTY as of 2026-09-07, and that is the intended resting state -- an entry here is a config nobody
# has ruled on yet, not a permanent category. xor-staged.yaml was the only occupant; the owner ruled
# on P2 item 0.5 and juniper-cascor#629 set output_epochs: 200, so the split is gone and the
# exemption with it. test_exempt_entries_are_not_stale forces exactly this: it asserts every exempt
# config STILL carries the split, so a fixed config cannot quietly keep its waiver.
PENDING_EPOCH_SPLIT_DECISIONS: dict[str, str] = {}


class EpochBudgetSplitDriftTest(unittest.TestCase):
    """P2 item 0.6: no cascor experiment config may set ``max_epochs`` without ``output_epochs``.

    Why a test and not the existing warning: the driver already flags this at load time, and the
    warning is recorded in every run's manifest. It was flagged on EVERY PF-1 run for a month and
    the campaign ran anyway -- the measurement that eventually caught it showed the service doing
    ~125x the configured work (cascor#618). A warning that lands in an artifact nobody re-reads is
    not a control.
    """

    def _cascor_params(self):
        for yaml_file in sorted(CASCOR_CONF.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
            yield yaml_file, ((raw.get("training") or {}).get("params") or {})

    def test_no_unexempted_epoch_split(self) -> None:
        self._gate_conf()
        offenders = []
        for yaml_file, params in self._cascor_params():
            if not epoch_budget_split(params):
                continue
            if yaml_file.name in DELIBERATE_EPOCH_SPLITS or yaml_file.name in PENDING_EPOCH_SPLIT_DECISIONS:
                continue
            offenders.append(f"{yaml_file.name} (max_epochs={params.get('max_epochs')!r}, no output_epochs)")
        self.assertEqual(
            offenders,
            [],
            "cascor experiment configs set max_epochs without output_epochs -- the service will run " "every non-initial output pass at the 10000 default while the CLI runs it at max_epochs. " f"Set both to the same value, or add an entry with a reason: {offenders}",
        )

    def test_exempt_entries_are_not_stale(self) -> None:
        """An exemption whose file no longer splits is dead weight and must be removed.

        Without this, the allowlist outlives the condition it excuses and the next reader cannot
        tell which entries still mean anything.
        """
        self._gate_conf()
        by_name = {path.name: params for path, params in self._cascor_params()}
        for name in sorted({**DELIBERATE_EPOCH_SPLITS, **PENDING_EPOCH_SPLIT_DECISIONS}):
            with self.subTest(config=name):
                self.assertIn(name, by_name, f"{name} is exempted but no longer exists in {CASCOR_CONF}")
                self.assertTrue(
                    epoch_budget_split(by_name[name]),
                    f"{name} no longer sets max_epochs without output_epochs -- remove its exemption",
                )

    def _gate_conf(self) -> None:
        if not _cross_repo_enabled():
            self.skipTest("cross-repo drift walk gated (CI clones siblings; locally set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1)")
        if not CASCOR_CONF.is_dir():
            self.skipTest(f"sibling conf dir not on disk: {CASCOR_CONF}")


class EpochBudgetSplitPredicateSelfCheckTest(unittest.TestCase):
    """Always-on: the predicate must bite, whether or not the sibling walk runs.

    The cross-repo walk above skips in the normal CI job (siblings are not cloned), so without
    these the module would contribute nothing there -- a gate that only runs where nobody looks.
    """

    def test_split_is_detected(self) -> None:
        self.assertTrue(epoch_budget_split({"max_epochs": 50}))

    def test_matched_pair_is_clean(self) -> None:
        self.assertFalse(epoch_budget_split({"max_epochs": 50, "output_epochs": 50}))

    def test_mismatched_pair_is_still_clean(self) -> None:
        # An explicit, DIFFERENT output_epochs is a stated intent, not the silent shape.
        self.assertFalse(epoch_budget_split({"max_epochs": 50, "output_epochs": 10000}))

    def test_neither_key_is_clean(self) -> None:
        self.assertFalse(epoch_budget_split({"max_iterations": 2}))

    def test_output_epochs_alone_is_clean(self) -> None:
        self.assertFalse(epoch_budget_split({"output_epochs": 500}))

    def test_spiral_smoke_is_fixed(self) -> None:
        """cascor#618 regression pin, run only when the sibling is on disk."""
        smoke = CASCOR_CONF / "spiral-smoke.yaml"
        if not smoke.is_file():
            self.skipTest(f"sibling config not on disk: {smoke}")
        params = (yaml.safe_load(smoke.read_text(encoding="utf-8")).get("training") or {}).get("params") or {}
        self.assertFalse(epoch_budget_split(params), "spiral-smoke.yaml regressed to max_epochs without output_epochs")
        self.assertEqual(params.get("max_epochs"), params.get("output_epochs"), "spiral-smoke.yaml's epoch keys must MATCH, not merely both exist")


class AstExtractorSelfCheckTest(unittest.TestCase):
    """Always-on in-repo self-check so the module is never a silent no-op."""

    def test_settings_base_fields_extracted(self) -> None:
        fields = _class_field_names(SERVICE_CORE_SETTINGS, {"SettingsBase"})
        self.assertIn("log_level", fields)
        self.assertIn("host", fields)
        self.assertIn("port", fields)

    def test_extractor_ignores_private_and_model_config(self) -> None:
        fields = _class_field_names(SERVICE_CORE_SETTINGS, {"SettingsBase"})
        self.assertNotIn("model_config", fields)
        self.assertFalse(any(name.startswith("_") for name in fields))
