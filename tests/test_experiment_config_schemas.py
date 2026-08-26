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

ECOSYSTEM_ROOT = REPO_ROOT.parent
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
