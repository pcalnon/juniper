#!/usr/bin/env python3
"""Tests for util/ruleset_scope_guard.py -- the `~ALL`-scope guard.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

The guard exists because removing the dependabot (29110) / Copilot (1143301) bypass rows on
2026-08-23 was safe **only while every ruleset stays `~DEFAULT_BRANCH`-scoped**. Under `~ALL`
the `creation` rule is evaluated on every branch and those rows become load-bearing again --
so a re-scope silently re-arms a dependency on rows that no longer exist, and the symptom is
dependency PRs stopping fleet-wide with nothing naming the cause.

Hermetic by construction: every test injects a fake getter or patches the module's `_get`.
No network, no `gh`, no repo is ever touched -- matching the rest of this suite.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import unittest

import yaml

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_MOD_PATH = _ROOT / "util" / "ruleset_scope_guard.py"
_spec = importlib.util.spec_from_file_location("ruleset_scope_guard", _MOD_PATH)
assert _spec and _spec.loader
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


def _ruleset(rid: int, name: str, include: list[str]) -> dict:
    return {"id": rid, "name": name, "conditions": {"ref_name": {"exclude": [], "include": include}}}


def _fake_getter(per_repo: dict[str, list[dict]]):
    """Serve the list endpoint then each detail endpoint from a canned mapping."""

    def getter(path: str):
        parts = path.strip("/").split("/")
        repo = parts[2]
        rulesets = per_repo[repo]
        if parts[-1] == "rulesets":
            return [{"id": r["id"], "name": r["name"]} for r in rulesets]
        rid = int(parts[-1])
        return next(r for r in rulesets if r["id"] == rid)

    return getter


class _PatchBase(unittest.TestCase):
    """setattr/getattr rather than attribute syntax, mirroring `SafeMergeTestBase.monkey`.

    `guard` is loaded through importlib, so mypy sees a bare `ModuleType` and rejects
    assignment to an attribute it cannot verify (`Module has no attribute "_get"`). Going
    through `setattr` keeps the patch invisible to mypy and restores in LIFO order.
    """

    def setUp(self):
        self._restore: list[tuple[object, str, object]] = []

    def tearDown(self):
        for obj, name, val in reversed(self._restore):
            setattr(obj, name, val)

    def monkey(self, obj, name, val):
        self._restore.append((obj, name, getattr(obj, name)))
        setattr(obj, name, val)


class FleetListDriftTest(unittest.TestCase):
    """The third hard-coded fleet list in this repo -- pinned so it cannot drift alone.

    CLAUDE.md already warns that `DEFAULT_REPOS` and `ECOSYSTEM_REPOS` must move together
    when a publishing sibling is added, and one of them has silently dropped a sibling
    before. The guard keeps a stdlib-only list (so it needs no YAML at runtime); this test
    is what keeps it honest.
    """

    def test_fleet_equals_registry_publishers_plus_deploy(self):
        registry = yaml.safe_load((_ROOT / "util" / "release_train" / "registry.yaml").read_text())
        publishers = {p["repo"] for p in registry["packages"] if p.get("repo")}
        self.assertEqual(
            set(guard.FLEET),
            publishers | {"juniper-deploy"},
            "FLEET must equal the release-train registry's publishing repos plus " "juniper-deploy (which ships no package but carries the same rulesets). " "Adding a sibling repo means updating this list too.",
        )

    def test_self_repo_is_in_the_fleet(self):
        self.assertIn(guard.SELF_REPO, guard.FLEET)


class ScopeVerdictTest(_PatchBase):
    """Narrow passes, wide fails. The core assertion."""

    def _run(self, per_repo: dict[str, list[dict]], argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        self.monkey(guard, "_get", _fake_getter(per_repo))
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = guard.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_narrow_scope_passes(self):
        code, out, _ = self._run({"juniper-ml": [_ruleset(1, "rules", ["~DEFAULT_BRANCH"])]}, ["--repo", "juniper-ml"])
        self.assertEqual(code, 0)
        self.assertIn("none scoped ~ALL", out)

    def test_wide_scope_fails_with_exit_one(self):
        code, _, err = self._run({"juniper-ml": [_ruleset(1, "rules", ["~ALL"])]}, ["--repo", "juniper-ml"])
        self.assertEqual(code, 1, "a ~ALL ruleset must FAIL, not warn")
        self.assertIn("~ALL", err)

    def test_the_failure_names_the_offending_ruleset_and_the_consequence(self):
        code, _, err = self._run({"juniper-data": [_ruleset(77, "data-rules", ["~ALL"])]}, ["--repo", "juniper-data"])
        self.assertEqual(code, 1)
        self.assertIn("juniper-data", err)
        self.assertIn("77", err)
        self.assertIn("29110", err, "the message must name the rows it re-arms")
        self.assertIn("dependency PRs stop", err)

    def test_one_wide_among_many_narrow_still_fails(self):
        code, _, _ = self._run(
            {
                "juniper-ml": [
                    _ruleset(1, "a", ["~DEFAULT_BRANCH"]),
                    _ruleset(2, "b", ["~ALL"]),
                    _ruleset(3, "c", ["~DEFAULT_BRANCH"]),
                ]
            },
            ["--repo", "juniper-ml"],
        )
        self.assertEqual(code, 1)

    def test_an_empty_ruleset_list_is_NOT_a_pass(self):
        """No rulesets means unprotected or a degraded probe -- never 'clean'."""
        code, _, err = self._run({"juniper-ml": []}, ["--repo", "juniper-ml"])
        self.assertEqual(code, 2)
        self.assertIn("no rulesets found", err.lower())


class ProbeFailureTest(_PatchBase):
    """A failed probe must never read as a clean result -- the recurring local failure mode."""

    def test_probe_failure_exits_two_not_zero(self):
        def boom(path):
            raise guard.ProbeError("GET failed after 3 attempts -- simulated outage")

        self.monkey(guard, "_get", boom)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = guard.main(["--repo", "juniper-ml"])
        # .getvalue(), NOT the StringIO: `x in StringIO` ITERATES the stream, which is at EOF
        # after writing, so it always yields False -- an assertNotIn against one passes
        # vacuously. Caught here only because the paired assertIn failed loudly.
        stdout_text, stderr_text = out.getvalue(), err.getvalue()
        self.assertEqual(code, 2, "an unverifiable result must not exit 0")
        self.assertIn("COULD NOT VERIFY", stderr_text)
        self.assertNotIn("OK:", stdout_text)

    def test_get_raises_rather_than_returning_empty(self):
        calls = {"n": 0}

        def always_fail(req, timeout=0):
            calls["n"] += 1
            raise OSError("connection refused")

        self.monkey(guard.urllib.request, "urlopen", always_fail)
        with self.assertRaises(guard.ProbeError):
            guard._get("/repos/x/y/rulesets", sleeper=lambda _s: None)
        self.assertEqual(calls["n"], guard._RETRIES, "must retry before giving up")

    def test_get_recovers_on_a_later_attempt(self):
        state = {"n": 0}

        class _Resp:
            def read(self):
                return b'[{"id": 1}]'

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def flaky(req, timeout=0):
            state["n"] += 1
            if state["n"] < 2:
                raise OSError("transient")
            return _Resp()

        self.monkey(guard.urllib.request, "urlopen", flaky)
        self.assertEqual(guard._get("/x", sleeper=lambda _s: None), [{"id": 1}])


class ScopeContractTest(unittest.TestCase):
    """Pins that must not be 'simplified' away."""

    def test_guard_does_not_claim_to_check_bypass_rows(self):
        """`bypass_actors` is REDACTED unauthenticated, so a token-free row check would
        report a redacted field as an empty one -- verifying nothing while looking green."""
        src = _MOD_PATH.read_text()
        self.assertNotIn(
            'get("bypass_actors")',
            src,
            "the token-free guard must not read bypass_actors -- it is redacted " "unauthenticated. Row checking belongs in the authenticated verifier.",
        )
        self.assertIn("bypass rows are NOT checked", src)

    def test_forbidden_scope_is_exactly_tilde_all(self):
        self.assertEqual(guard.FORBIDDEN_SCOPE, "~ALL")

    def test_scope_of_tolerates_a_missing_conditions_block(self):
        self.assertEqual(guard.scope_of({}), [])
        self.assertEqual(guard.scope_of({"conditions": None}), [])


if __name__ == "__main__":
    unittest.main()
