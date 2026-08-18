"""Drift gate: every publish environment must stay ref-gated to release tags.

Companion to ``notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md``
(§6 Option A, §12 implementation record, §12.5 "no drift gate" gap).

On 2026-08-17 every ``pypi`` / ``testpypi`` environment across the 8 publishing
repos was given a **tag-only** deployment ref policy, so a ``workflow_dispatch``
from a branch is refused at the environment gate before any OIDC credential is
minted.  That control lives in **GitHub settings, not in the repository**: no
test covers it, no reviewer sees a diff when one is deleted, and the failure is
silent -- the publish path simply becomes permissive again.  This gate is the
only thing standing between that and a regression.

Two invariants matter more than the rest:

1. **No branch-type policy may exist.**  Adding a ``main`` branch policy is the
   single edit that re-opens the arbitrary-ref hole while leaving every tag
   pattern intact and the environment still looking configured.  Owner decision
   D3 was explicitly tag-only.
2. **The ``pypi`` reviewer gate must survive.**  ``PUT``ing an environment is a
   create-or-update, so a careless payload can clear ``required_reviewers``
   while successfully setting a ref policy -- the environment then looks *more*
   configured while actually being weaker.

Modes (mirroring ``tests/test_ci_tools_drift.py`` and
``tests/test_docs_full_check_ecosystem.py``):

* **Structural checks always run** -- the registry resolves a publishing-repo
  set, the expected pattern set is coherent, and the detector provably bites on
  synthetic violations (the negative control).  These need no network.
* **Live API assertions are gated** behind ``GITHUB_ACTIONS=true`` or
  ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``, and additionally require ``gh`` on PATH
  with working auth.  A missing / unauthenticated ``gh`` skips loudly rather
  than failing, so the suite stays runnable offline.

Read-only: the live half issues ``gh api`` GETs only and never mutates an
environment.  Repair is
``util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> <env>``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

import yaml

OWNER = "pcalnon"
REGISTRY_REL = Path("util") / "release_train" / "registry.yaml"

# The two environments every publishing repo exposes to the PyPA publish action.
PUBLISH_ENVS = ("pypi", "testpypi")

# Repos that must NOT carry a publish environment at all.  juniper-deploy's
# vestigial pair was deleted 2026-08-17 (owner decision D4); an environment
# named `pypi` on a repo that ships no package is a latent foothold, so this
# doubles as an anti-resurrection guard.
NON_PUBLISHING_REPOS = ("juniper-deploy",)

# Owner decision D2.  `v*` / `juniper-*-v*` are the live conventions; the `rc` /
# `hf` pairs were registered ahead of any release-candidate or hotfix use.
EXPECTED_TAG_PATTERNS = frozenset(
    {
        "v*",
        "juniper-*-v*",
        "rc*",
        "juniper-*-rc*",
        "hf*",
        "juniper-*-hf*",
    }
)

# Environments whose human approval gate must also survive.  testpypi is
# deliberately reviewer-free -- gating it would break hands-free release-train
# operation, which is exactly what the ref policy exists to avoid needing.
ENVS_REQUIRING_REVIEWERS = ("pypi",)


def _repo_root() -> Path:
    """Locate the juniper-ml checkout root from this file."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / REGISTRY_REL).is_file():
            return candidate
    return here.parents[1]


def _registry_repos() -> frozenset[str]:
    """Unique publishing repos from the release-train registry (S4.1 source of truth)."""
    registry_path = _repo_root() / REGISTRY_REL
    if not registry_path.is_file():
        raise unittest.SkipTest(f"{REGISTRY_REL} not found")
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    packages = data.get("packages") or []
    return frozenset(str(pkg["repo"]) for pkg in packages if isinstance(pkg, dict) and pkg.get("repo"))


def check_environment(env_payload: dict, policies: list, *, env_name: str) -> list:
    """Return a list of human-readable violations for one environment.

    Pure: takes already-fetched API payloads so the negative control can drive
    it with synthetic data and no network.  An empty list means compliant.
    """
    violations: list = []

    policy_cfg = env_payload.get("deployment_branch_policy")
    if policy_cfg is None:
        # Everything below reads fields of that object; without it there is
        # nothing further to say and this single finding is the actionable one.
        return ["deployment_branch_policy is null -- environment accepts ANY ref"]

    if policy_cfg.get("protected_branches"):
        violations.append("protected_branches is true -- protected branches may deploy; expected custom policies only")
    if not policy_cfg.get("custom_branch_policies"):
        violations.append("custom_branch_policies is not true -- no custom ref policy is in force")

    # Invariant 1: a branch policy of any kind re-opens the arbitrary-ref path.
    branch_policies = [p for p in policies if (p.get("type") or "branch") != "tag"]
    if branch_policies:
        names = ", ".join(sorted(str(p.get("name")) for p in branch_policies))
        violations.append(f"branch-type deployment policy present ({names}) -- D3 requires tag-only; this re-opens branch dispatch")

    found_tags = {str(p.get("name")) for p in policies if (p.get("type") or "branch") == "tag"}
    missing = EXPECTED_TAG_PATTERNS - found_tags
    if missing:
        violations.append(f"missing tag pattern(s): {', '.join(sorted(missing))}")
    unexpected = found_tags - EXPECTED_TAG_PATTERNS
    if unexpected:
        violations.append(f"unexpected tag pattern(s): {', '.join(sorted(unexpected))} -- widen EXPECTED_TAG_PATTERNS deliberately or remove them")

    # Invariant 2: the reviewer gate must not have been cleared by a PUT.
    if env_name in ENVS_REQUIRING_REVIEWERS:
        rule_types = {str(r.get("type")) for r in env_payload.get("protection_rules") or []}
        if "required_reviewers" not in rule_types:
            violations.append("required_reviewers protection rule is absent -- the human approval gate was cleared")

    return violations


def _gh_json(path: str):
    """GET a gh API path and parse JSON. Raises RuntimeError on failure."""
    proc = subprocess.run(
        ["gh", "api", path],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


class RegistryResolutionTest(unittest.TestCase):
    """Always-on: the publishing-repo set resolves from the registry."""

    def test_registry_resolves_publishing_repos(self) -> None:
        repos = _registry_repos()
        self.assertGreaterEqual(len(repos), 2, "registry.yaml did not resolve a non-trivial publishing-repo set")
        self.assertIn("juniper-ml", repos)

    def test_non_publishing_repos_are_not_registry_publishers(self) -> None:
        repos = _registry_repos()
        for repo in NON_PUBLISHING_REPOS:
            self.assertNotIn(repo, repos, f"{repo} is a registry publisher; it must not be listed in NON_PUBLISHING_REPOS")


class ExpectedPatternContractTest(unittest.TestCase):
    """Always-on: the expected pattern set is coherent and covers the conventions."""

    def test_pattern_set_is_non_trivial(self) -> None:
        self.assertGreaterEqual(len(EXPECTED_TAG_PATTERNS), 2)

    def test_live_release_conventions_are_covered(self) -> None:
        """The two shapes real releases actually use must be present."""
        self.assertIn("v*", EXPECTED_TAG_PATTERNS, "meta / app releases tag as v<semver>")
        self.assertIn("juniper-*-v*", EXPECTED_TAG_PATTERNS, "sub-package releases tag as juniper-<pkg>-v<semver>")

    def test_no_branch_shaped_pattern_smuggled_in(self) -> None:
        """A bare branch name in the tag set would be a category error."""
        for pattern in EXPECTED_TAG_PATTERNS:
            self.assertNotIn(pattern, {"main", "develop"}, "branch names must never appear as deployment tag patterns")

    def test_no_catch_all_pattern(self) -> None:
        """A bare `*` would admit every tag and silently defeat the gate."""
        self.assertNotIn("*", EXPECTED_TAG_PATTERNS)


class DetectorNegativeControlTest(unittest.TestCase):
    """Always-on: prove the detector bites. A gate that cannot fail is not a gate."""

    COMPLIANT_ENV = {
        "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
        "protection_rules": [{"type": "required_reviewers"}, {"type": "wait_timer"}, {"type": "branch_policy"}],
    }
    COMPLIANT_POLICIES = [{"name": p, "type": "tag"} for p in sorted(EXPECTED_TAG_PATTERNS)]

    def test_compliant_environment_passes(self) -> None:
        self.assertEqual(check_environment(self.COMPLIANT_ENV, self.COMPLIANT_POLICIES, env_name="pypi"), [])

    def test_null_policy_is_flagged(self) -> None:
        violations = check_environment({"deployment_branch_policy": None, "protection_rules": []}, [], env_name="testpypi")
        self.assertTrue(any("ANY ref" in v for v in violations), violations)

    def test_branch_policy_is_flagged(self) -> None:
        """The critical case: every tag pattern present, but `main` added alongside."""
        policies = [*self.COMPLIANT_POLICIES, {"name": "main", "type": "branch"}]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("branch-type deployment policy present" in v for v in violations), violations)

    def test_untyped_policy_counts_as_branch(self) -> None:
        """The API omits `type` for legacy branch policies; absence must not read as `tag`."""
        policies = [*self.COMPLIANT_POLICIES, {"name": "main"}]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("branch-type deployment policy present" in v for v in violations), violations)

    def test_missing_tag_pattern_is_flagged(self) -> None:
        policies = [p for p in self.COMPLIANT_POLICIES if p["name"] != "v*"]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("missing tag pattern" in v and "v*" in v for v in violations), violations)

    def test_unexpected_tag_pattern_is_flagged(self) -> None:
        policies = [*self.COMPLIANT_POLICIES, {"name": "*", "type": "tag"}]
        violations = check_environment(self.COMPLIANT_ENV, policies, env_name="pypi")
        self.assertTrue(any("unexpected tag pattern" in v for v in violations), violations)

    def test_cleared_reviewer_gate_is_flagged_on_pypi(self) -> None:
        env = {**self.COMPLIANT_ENV, "protection_rules": [{"type": "branch_policy"}]}
        violations = check_environment(env, self.COMPLIANT_POLICIES, env_name="pypi")
        self.assertTrue(any("required_reviewers" in v for v in violations), violations)

    def test_testpypi_does_not_require_reviewers(self) -> None:
        """testpypi is deliberately reviewer-free so the release train stays hands-free."""
        env = {**self.COMPLIANT_ENV, "protection_rules": [{"type": "branch_policy"}]}
        self.assertEqual(check_environment(env, self.COMPLIANT_POLICIES, env_name="testpypi"), [])

    def test_protected_branches_mode_is_flagged(self) -> None:
        env = {**self.COMPLIANT_ENV, "deployment_branch_policy": {"protected_branches": True, "custom_branch_policies": False}}
        violations = check_environment(env, [], env_name="testpypi")
        self.assertTrue(any("protected_branches" in v for v in violations), violations)


class LivePublishEnvironmentPolicyTest(unittest.TestCase):
    """Gated: assert the real environments still carry the tag-only policy."""

    # Registry repos partitioned by what the ambient token can actually read.
    readable: list = []
    unreadable: list = []

    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            raise unittest.SkipTest("skipping live environment lint (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override)")
        if shutil.which("gh") is None:
            raise unittest.SkipTest("gh not on PATH")

        # Partition the registry repos by what this token can actually read.
        #
        # In juniper-ml's own CI the built-in GITHUB_TOKEN is scoped to
        # juniper-ml alone, so every sibling probe fails on PERMISSION, not on
        # drift.  Treating that as a violation would make ci.yml permanently
        # red; treating it as success would silently shrink coverage to one
        # repo while the test name still claims "every publish environment".
        # So: verify what is readable, NAME what is not, and refuse to pass at
        # all if nothing was readable.
        cls.readable = []
        cls.unreadable = []
        for repo in sorted(_registry_repos()):
            try:
                _gh_json(f"repos/{OWNER}/{repo}/environments")
            except Exception:
                cls.unreadable.append(repo)
            else:
                cls.readable.append(repo)

        if not cls.readable:
            raise unittest.SkipTest(f"gh api could not read environments for ANY registry repo (unauthenticated, or token lacks access): {', '.join(cls.unreadable)}")

    def test_every_publish_environment_is_tag_gated(self) -> None:
        failures: list = []
        for repo in self.readable:
            for env_name in PUBLISH_ENVS:
                try:
                    env_payload = _gh_json(f"repos/{OWNER}/{repo}/environments/{env_name}")
                    policy_doc = _gh_json(f"repos/{OWNER}/{repo}/environments/{env_name}/deployment-branch-policies")
                except RuntimeError as exc:
                    # The repo IS readable, so a failure here is a real finding
                    # -- most likely the environment was deleted outright.
                    failures.append(f"{repo}/{env_name}: could not read environment ({exc})")
                    continue
                policies = (policy_doc or {}).get("branch_policies") or []
                for violation in check_environment(env_payload, policies, env_name=env_name):
                    failures.append(f"{repo}/{env_name}: {violation}")

        # Never let bounded coverage read as full coverage (no silent caps).
        if self.unreadable:
            print(f"\n[publish-env drift] verified {len(self.readable)} repo(s): {', '.join(self.readable)}")
            print(f"[publish-env drift] NOT verified (token lacks access): {', '.join(self.unreadable)}")

        self.assertEqual(
            failures,
            [],
            "publish environment ref-policy drift detected:\n  " + "\n  ".join(failures) + "\nRepair: util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> <env>",
        )

    def test_non_publishing_repos_have_no_publish_environment(self) -> None:
        """Anti-resurrection: juniper-deploy's vestigial pypi/testpypi stay deleted."""
        failures: list = []
        for repo in NON_PUBLISHING_REPOS:
            try:
                doc = _gh_json(f"repos/{OWNER}/{repo}/environments")
            except RuntimeError as exc:
                raise unittest.SkipTest(f"could not enumerate {repo} environments: {exc}")
            names = {str(e.get("name")) for e in (doc or {}).get("environments") or []}
            for env_name in PUBLISH_ENVS:
                if env_name in names:
                    failures.append(f"{repo}: environment '{env_name}' exists but {repo} publishes no package (owner decision D4 deleted it)")
        self.assertEqual(failures, [], "\n  ".join(failures))


if __name__ == "__main__":
    unittest.main(verbosity=2)
