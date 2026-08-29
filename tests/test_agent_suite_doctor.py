"""Tests for util/agent_suite_doctor.py -- the custom-agent suite health check (dogfood utility).

Exercises the read-only doctor against the real suite (must be healthy: no FAIL) and against
synthetic trees missing a component (must FAIL the matching check + exit 1), plus the CLI
contract (--json shape, --no-discovery skip, --strict WARN promotion, bad-root exit 2).

util/ is not a package; the module is importlib-loaded. Location-agnostic.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_DOCTOR = _REPO_ROOT / "util" / "agent_suite_doctor.py"


def _load():
    spec = importlib.util.spec_from_file_location("agent_suite_doctor", _DOCTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _marker(root: Path) -> None:
    (root / ".github" / "workflows").mkdir(parents=True)


def _agent(root: Path, name: str, model: str = "opus", effort: str = "max") -> None:
    agents = root / ".claude" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    body = "description that is sufficiently long to be substantive " * 2
    (agents / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: {body}\ntools: Read, Bash\nmodel: {model}\neffort: {effort}\n---\n\n# {name}\n\nNon-trivial body content for the agent definition.\n",
        encoding="utf-8",
    )


class DoctorUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def _by_name(self, results):
        return {name: (status, reason) for name, status, reason in results}

    def test_real_suite_has_no_fail(self):
        results = self.mod.run_checks(_REPO_ROOT, no_discovery=True)
        names = {n for n, _, _ in results}
        self.assertLessEqual({"agents", "skill", "templates", "rubric", "data_layer", "mirror"}, names)
        fails = [(n, r) for n, s, r in results if s == self.mod.FAIL]
        self.assertEqual(fails, [], f"the real suite should have zero FAIL checks: {fails}")

    def test_no_discovery_skips_discovery(self):
        names = {n for n, _, _ in self.mod.run_checks(_REPO_ROOT, no_discovery=True)}
        self.assertNotIn("discovery", names)

    def test_missing_core_agent_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            _agent(root, "planner")  # only planner -> the load-bearing prompt-validator is missing
            agents = self._by_name(self.mod.run_checks(root, no_discovery=True))["agents"]
            self.assertEqual(agents[0], self.mod.FAIL)

    def test_bad_model_agent_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            _agent(root, "prompt-validator", model="sonnet")  # model drift
            agents = self._by_name(self.mod.run_checks(root, no_discovery=True))["agents"]
            self.assertEqual(agents[0], self.mod.FAIL)
            self.assertIn("opus", agents[1])

    def test_missing_skill_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            _agent(root, "prompt-validator")  # agents ok, but no skill
            skill = self._by_name(self.mod.run_checks(root, no_discovery=True))["skill"]
            self.assertEqual(skill[0], self.mod.FAIL)


def _write_fake_discovery_cli(root: Path, body: str) -> Path:
    """Install a hermetic ``util/prompt_discovery/cli.py`` under *root*."""
    cli = root / "util" / "prompt_discovery" / "cli.py"
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text(body, encoding="utf-8")
    return cli


class DoctorDiscoveryCheckTest(unittest.TestCase):
    """Pin ``check_discovery`` fail-closed arms (existing suite tests skip via ``no_discovery``)."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_missing_cli_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            name, status, reason = self.mod.check_discovery(root)
            self.assertEqual(name, "discovery")
            self.assertEqual(status, self.mod.FAIL)
            self.assertIn("missing", reason)

    def test_nonzero_exit_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            _write_fake_discovery_cli(
                root,
                "import sys\n" "print('boom-stderr', file=sys.stderr)\n" "sys.exit(3)\n",
            )
            name, status, reason = self.mod.check_discovery(root)
            self.assertEqual(name, "discovery")
            self.assertEqual(status, self.mod.FAIL)
            self.assertIn("exited 3", reason)
            self.assertIn("boom-stderr", reason)

    def test_invalid_json_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            _write_fake_discovery_cli(root, "print('not-json')\n")
            name, status, reason = self.mod.check_discovery(root)
            self.assertEqual(name, "discovery")
            self.assertEqual(status, self.mod.FAIL)
            self.assertIn("not valid JSON", reason)

    def test_missing_schema_or_provenance_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            # schema_version present but provenance.head_sha absent -> fail-closed
            _write_fake_discovery_cli(
                root,
                "import json\n" "print(json.dumps({'schema_version': 1, 'provenance': {}}))\n",
            )
            name, status, reason = self.mod.check_discovery(root)
            self.assertEqual(name, "discovery")
            self.assertEqual(status, self.mod.FAIL)
            self.assertIn("schema_version", reason)
            self.assertIn("provenance.head_sha", reason)

    def test_well_formed_bundle_ok(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _marker(root)
            _write_fake_discovery_cli(
                root,
                "import json\n" "print(json.dumps({\n" "  'schema_version': 1,\n" "  'provenance': {'head_sha': 'abc123'},\n" "}))\n",
            )
            name, status, reason = self.mod.check_discovery(root)
            self.assertEqual(name, "discovery")
            self.assertEqual(status, self.mod.OK)
            self.assertIn("well-formed", reason)


class DoctorCliTest(unittest.TestCase):
    def _run(self, *args, env_extra=None):
        env = RedactedEnv(os.environ)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(_DOCTOR), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            env=env,
        )

    def test_real_repo_exit_0(self):
        proc = self._run("--repo-root", str(_REPO_ROOT), "--no-discovery")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_json_shape(self):
        proc = self._run("--repo-root", str(_REPO_ROOT), "--no-discovery", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data), {"repo_root", "checks", "summary"})
        self.assertTrue(all({"name", "status", "reason"} <= set(c) for c in data["checks"]))
        self.assertEqual(set(data["summary"]), {"OK", "WARN", "FAIL"})

    def test_bad_repo_root_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self._run("--repo-root", d)  # no .github/workflows/ marker
            self.assertEqual(proc.returncode, 2)

    def test_missing_components_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".github" / "workflows").mkdir(parents=True)  # marker only; suite absent
            proc = self._run("--repo-root", d, "--no-discovery")
            self.assertEqual(proc.returncode, 1)

    def test_strict_promotes_warn(self):
        # Force the (optional) mirror check to WARN via an empty JUNIPER_CLAUDE_HOME; the real
        # suite is otherwise healthy, so --strict must flip exit 0 -> 1.
        with tempfile.TemporaryDirectory() as d:
            env = {"JUNIPER_CLAUDE_HOME": d}
            base = self._run("--repo-root", str(_REPO_ROOT), "--no-discovery", env_extra=env)
            strict = self._run("--repo-root", str(_REPO_ROOT), "--no-discovery", "--strict", env_extra=env)
            self.assertEqual(base.returncode, 0, base.stderr)
            self.assertEqual(strict.returncode, 1, strict.stdout)


if __name__ == "__main__":
    unittest.main()
