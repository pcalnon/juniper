#!/usr/bin/env python3
"""Structural R7-privilege-boundary guard for .github/workflows/release-train.yml (plan S9.3 / S12 steps 2.2/4.1/4.3).

The release-train's write identity must open PRs / cut Releases ONLY -- it must never touch environments,
deployments, or PyPI (plan S9.3, the R7 hard invariant: "A guard test asserts the workflow contains no
environment-mutating API calls"). This lint pins that boundary against drift by parsing the workflow with
PyYAML and asserting:

  (a) workflow-level permissions are exactly {contents: read} -- the report/detect path is read-only;
  (b) EACH write-scoped job (``propose`` AND -- Phase 4.3 -- ``ceremony``) has permissions exactly
      {contents: write, pull-requests: write} -- nothing broader (no id-token, no deployments, no
      environments scope); the read-only ``detect`` job never elevates;
  (c) each write job's ``if`` gates on the detect job's resolved ``mode`` output, so its write scope is
      UNREACHABLE unless mode == that job's mode (it never runs on the report/off path), with no
      always()/!cancelled() escape hatch;
  (d) no job/step references a ``secrets.`` value other than SLACK_WEBHOOK_URL and (Phase 4.1) the
      GitHub App private key RELEASE_TRAIN_APP_PRIVATE_KEY -- the workflow otherwise uses the built-in
      ``github.token``, so a stray privileged secret cannot slip in behind a write scope;
  (e) **Phase 4.1/4.3 App-identity boundary** -- the cross-repo write identity is fenced: the App
      private-key secret is referenced EXACTLY ONCE PER WRITE JOB (the ``create-github-app-token`` mint
      step's ``private-key`` input) and nowhere else; each mint step + the minted token live ONLY in a
      write job (never the read-only detect job); each mint step is gated on ``vars.RELEASE_TRAIN_APP_ID``
      so an absent App config degrades to the built-in ``GITHUB_TOKEN``; and the action is pinned by a
      full commit SHA (fleet convention);
  (f) **Phase 4.3 off-quiesce** -- ``mode=off`` runs nothing beyond mode resolution: every detect-job step
      other than the mode resolver is gated on the resolved mode (``!= 'off'`` for the work steps, the one
      ``== 'off'`` quiesce step), and both write jobs are unreachable (their ``if`` requires a non-off mode);
  (g) **Cross-repo headless git identity (ml#705)** -- EACH write job configures ``user.name`` /
      ``user.email`` / ``commit.gpgsign`` with ``git config --global`` (NOT bare repo-local ``git config``).
      Cross-repo propose/ceremony commits inside freshly-cloned sibling checkouts; a repo-local identity
      on the juniper-ml checkout alone leaves siblings with ``Author identity unknown`` (first cross-repo
      pilot failure, run 30040138774). The detect job must never configure identity (it never commits).
  (h) **Phase 4.1 mint-scope / clone-list lockstep** -- both write jobs' App-token ``repositories:`` lists
      equal the registry's publishing-repo set (R7 least-privilege; a drift either widens the token or
      silently drops a sibling), the two mint lists are identical, and ``env.ECOSYSTEM_REPOS`` equals
      that set minus ``juniper-ml`` (the checkout itself). Also pins the operator ``packages`` dispatch
      charset reject + the ``APP_TOKEN`` → ``--cross-repo`` capability gate on both write jobs' run scripts
      (a regression that always passes ``--cross-repo`` breaks the no-App degraded path).

Beyond the structural pins, three **YAML-extraction rehearsals** execute the actual workflow snippets
hermetically (the "run the real thing, not a reimplementation" idiom): ``ModeResolutionMatrixTest`` extracts
the ``id: mode`` step's shell and runs it over the whole mode matrix (incl. ``ceremony`` now valid + the
dispatch-input > repo-variable precedence), ``CeremonySummaryRehearsalTest`` extracts the ceremony
step-summary Python and runs it over a synthetic ``ceremony-output.txt`` (proving it renders
ceremonies/resumes/HALTs/PENDING_PYPI_APPROVAL and the degraded-issue line), and
``PackagesInputRehearsalTest`` extracts the write-job ``packages`` / ``--cross-repo`` shell prefix and
*runs* it (charset reject exit 2 + App-token capability gate) -- complementary to the structural
mint/ECOSYSTEM_REPOS / packages string pins.

Companion to ``tests/test_release_train_propose.py`` / ``tests/test_release_train_ceremony.py``. Neither
``util/`` nor the workflow YAML is pre-commit-lint-gated for these properties, so this unittest IS the gate.

Portable: locates the repo root by walking up for ``.github/workflows/`` (mirrors
``test_workflow_script_paths.py``) and skips loudly if ``release-train.yml`` is absent.

Run: python3 -m unittest -v tests/test_release_train_workflow_guard.py

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-16
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell/python hermetically (fixed argv)
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "release-train.yml"

# The two write-scoped lanes (R7 privilege boundary): propose (Phase 2.2) opens PRs; ceremony (Phase 4.3)
# opens the central archive PR AND cuts Releases. The read-only detect job must never join this set.
WRITE_JOBS = ("propose", "ceremony")

# The built-in ``github.token`` is used for GitHub auth on the read path; the ``secrets.*`` the train
# consumes are the non-blocking Slack webhook (plan S9.4, Q-CHANNEL) and -- Phase 4.1 -- the GitHub App
# private key that mints the cross-repo write identity (plan S9.2 / S12 step 4.1). Any OTHER secret
# slipping in behind a write scope is exactly what R7 forbids.
ALLOWED_SECRETS = frozenset({"SLACK_WEBHOOK_URL", "RELEASE_TRAIN_APP_PRIVATE_KEY"})

# Phase 4.1 App-identity anchors (the cross-repo write identity, plan S9.2). These are workflow
# IDENTIFIER names (an action ref + a secret/variable NAME to search for), never credential VALUES --
# nosec B105 silences bandit's hardcoded-password heuristic on the "token"/"KEY"/"SECRET" substrings.
APP_TOKEN_ACTION = "actions/create-github-app-token"  # nosec B105 - action ref, not a credential
APP_PRIVATE_KEY_SECRET = "RELEASE_TRAIN_APP_PRIVATE_KEY"  # nosec B105 - the secret's NAME, not its value
APP_ID_VARIABLE = "RELEASE_TRAIN_APP_ID"


def _find_repo_root(start: Path) -> Path:
    """First ancestor of ``start`` containing a ``.github/workflows/`` directory (the repo root)."""
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


class ReleaseTrainWorkflowGuardTest(unittest.TestCase):
    """Pin the R7 privilege boundary of release-train.yml so a refactor cannot silently widen it."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)

    # (a) --------------------------------------------------------------------------------------
    def test_workflow_level_permissions_are_read_only(self):
        self.assertEqual(
            self.doc.get("permissions"),
            {"contents": "read"},
            "workflow-level permissions must be exactly {contents: read} -- the report/detect path is read-only (R7).",
        )

    def test_detect_job_has_no_write_scope(self):
        perms = self.doc["jobs"]["detect"].get("permissions")
        self.assertIn(
            perms,
            (None, {"contents": "read"}),
            f"the detect job must not elevate above the read-only workflow default (got {perms!r}).",
        )

    # (b) --------------------------------------------------------------------------------------
    def test_write_jobs_defined(self):
        for job in WRITE_JOBS:
            self.assertIsNotNone(self.doc["jobs"].get(job), f"release-train.yml must define the {job} job")

    def test_write_job_permissions_are_exactly_pr_write(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                self.assertEqual(
                    self.doc["jobs"][job].get("permissions"),
                    {"contents": "write", "pull-requests": "write"},
                    f"{job} job permissions must be exactly {{contents: write, pull-requests: write}} -- no id-token/deployments/environments (R7).",
                )

    def test_write_jobs_need_detect(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                needs = self.doc["jobs"][job].get("needs")
                needs = [needs] if isinstance(needs, str) else (needs or [])
                self.assertIn("detect", needs, f"{job} must `needs: detect` (it consumes the detection manifest + the mode gate).")

    # (c) --------------------------------------------------------------------------------------
    def test_write_jobs_if_gate_on_resolved_mode(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                cond = str(self.doc["jobs"][job].get("if", ""))
                self.assertIn("needs.detect.outputs.mode", cond, f"{job} `if` must gate on the detect job's resolved mode output (privilege path unreachable in report mode).")
                self.assertIn(job, cond, f"{job} `if` must require the resolved mode be '{job}'.")
                # no escape hatch that would run the write-scoped job on a failed / other-mode run.
                self.assertNotIn("always()", cond, f"{job} `if` must not use always() -- that would run the write job regardless of mode.")
                self.assertNotIn("cancelled()", cond, f"{job} `if` must not use !cancelled() -- same escape-hatch hazard.")

    def test_write_job_ifs_are_mutually_exclusive_modes(self):
        # propose and ceremony must gate on DISTINCT modes so exactly one write lane can run per run.
        conds = {job: str(self.doc["jobs"][job].get("if", "")) for job in WRITE_JOBS}
        self.assertIn("propose", conds["propose"])
        self.assertIn("ceremony", conds["ceremony"])
        self.assertNotIn("ceremony", conds["propose"], "the propose gate must not also fire on ceremony mode")
        self.assertNotIn("propose", conds["ceremony"], "the ceremony gate must not also fire on propose mode")

    # (d) --------------------------------------------------------------------------------------
    def test_only_allowed_secrets_referenced(self):
        referenced = set(re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)", self.raw))
        extra = referenced - ALLOWED_SECRETS
        self.assertEqual(
            extra,
            set(),
            f"unexpected secrets referenced: {sorted(extra)} -- only {sorted(ALLOWED_SECRETS)} is allowed (use the built-in github.token for GitHub auth, never a broad PAT/deploy secret behind the write scope).",
        )

    # (e) Phase 4.1/4.3: the App cross-repo write identity is fenced to the write jobs' mint steps -------
    def _job_steps(self, job):
        return self.doc["jobs"][job].get("steps") or []

    def _mint_steps(self, job):
        return [s for s in self._job_steps(job) if APP_TOKEN_ACTION in str(s.get("uses", ""))]

    def test_app_token_minted_once_per_write_job_and_nowhere_else(self):
        # exactly one mint step in EACH write job ...
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                self.assertEqual(len(self._mint_steps(job)), 1, f"the {job} job must mint the App token exactly once")
        # ... and no OTHER job mints or references the App token (the read-only detect path must never see it)
        for job_name, job in self.doc["jobs"].items():
            if job_name in WRITE_JOBS:
                continue
            blob = json.dumps(job)
            self.assertNotIn(APP_TOKEN_ACTION, blob, f"job {job_name!r} must not mint the App token (write-jobs only)")
            self.assertNotIn("app-token", blob, f"job {job_name!r} must not reference the minted App token (write-jobs only)")

    def test_app_private_key_secret_only_in_the_mint_steps(self):
        # the raw workflow references the App private-key secret EXACTLY once per write job (2 total) ...
        self.assertEqual(
            self.raw.count(f"secrets.{APP_PRIVATE_KEY_SECRET}"),
            len(WRITE_JOBS),
            f"secrets.{APP_PRIVATE_KEY_SECRET} must be referenced exactly {len(WRITE_JOBS)} times (one mint step per write job).",
        )
        # ... and each reference is a write job's create-github-app-token step's `private-key` input, nowhere else.
        seen_in_write_jobs = 0
        for job in WRITE_JOBS:
            stepwise = [s for s in self._job_steps(job) if APP_PRIVATE_KEY_SECRET in json.dumps(s)]
            with self.subTest(job=job):
                self.assertEqual(len(stepwise), 1, f"the App private-key secret must appear in exactly one {job} step")
                self.assertIn(APP_TOKEN_ACTION, str(stepwise[0].get("uses", "")), f"the App private-key secret must appear ONLY in the {job} mint step")
                self.assertIn("private-key", stepwise[0].get("with", {}) or {}, f"the App private-key secret must be the {job} mint step's private-key input")
            seen_in_write_jobs += 1
        # no non-write job references it at all
        for job_name, job in self.doc["jobs"].items():
            if job_name in WRITE_JOBS:
                continue
            self.assertNotIn(APP_PRIVATE_KEY_SECRET, json.dumps(job), f"job {job_name!r} must not reference the App private-key secret")
        self.assertEqual(seen_in_write_jobs, len(WRITE_JOBS))

    def test_mint_steps_gated_on_variable_for_graceful_degradation(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                cond = str(self._mint_steps(job)[0].get("if", ""))
                self.assertIn(
                    f"vars.{APP_ID_VARIABLE}",
                    cond,
                    f"the {job} mint step must be gated on vars.RELEASE_TRAIN_APP_ID so an absent App config degrades to the built-in GITHUB_TOKEN (in-repo only).",
                )

    def test_app_token_action_pinned_by_full_sha(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                uses = str(self._mint_steps(job)[0].get("uses", ""))
                self.assertIsNotNone(
                    re.match(rf"^{re.escape(APP_TOKEN_ACTION)}@[0-9a-f]{{40}}(\s|$)", uses + " "),
                    f"create-github-app-token must be pinned by a full 40-hex commit SHA (fleet convention); got {uses!r}.",
                )

    # reinforcement: the gate depends on the mode output existing -------------------------------
    def test_detect_job_exposes_mode_output(self):
        outputs = self.doc["jobs"]["detect"].get("outputs") or {}
        self.assertIn("mode", outputs, "the detect job must expose a `mode` output -- the write-job gates read needs.detect.outputs.mode.")

    # (f) Phase 4.3 off-quiesce: mode=off runs nothing beyond mode resolution --------------------
    def _detect_step_by_id(self, step_id):
        for step in self._job_steps("detect"):
            if step.get("id") == step_id:
                return step
        return None

    def test_off_mode_quiesces_all_work(self):
        steps = self._job_steps("detect")
        # the mode resolver ALWAYS runs (no `if`) -- it is the one step that must fire on every mode incl. off.
        resolver = self._detect_step_by_id("mode")
        self.assertIsNotNone(resolver, "the detect job must have the `id: mode` resolver step")
        self.assertIsNone(resolver.get("if"), "the mode resolver step must have no `if` (it must run on every mode, incl. off).")
        # every OTHER detect step must be gated on the resolved mode so `off` does no detection/report work.
        off_gated = 0
        quiesce = 0
        for step in steps:
            if step is resolver:
                continue
            cond = str(step.get("if", ""))
            self.assertIn("steps.mode.outputs.mode", cond, f"detect step {step.get('name')!r} must be gated on the resolved mode (so off does nothing).")
            self.assertIn("off", cond, f"detect step {step.get('name')!r}'s gate must reference 'off'.")
            if "== 'off'" in cond:
                quiesce += 1
            elif "!= 'off'" in cond:
                off_gated += 1
        self.assertEqual(quiesce, 1, "exactly one detect step (the quiesce summary) is gated `== 'off'`.")
        self.assertGreaterEqual(off_gated, 1, "the real detection steps must be gated `!= 'off'`.")
        # and both write jobs are unreachable in off (their `if` requires a non-off mode).
        for job in WRITE_JOBS:
            cond = str(self.doc["jobs"][job].get("if", ""))
            self.assertNotIn("off", cond, f"{job} `if` should gate on its own non-off mode, never run on off.")

    # (h) Phase 4.1: mint repositories / ECOSYSTEM_REPOS lockstep with registry.yaml --------------
    def _registry_publishing_repos(self) -> frozenset[str]:
        """Unique ``repo`` values from ``util/release_train/registry.yaml`` (the S4.1 source of truth)."""
        self.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        registry_path = self.repo_root / "util" / "release_train" / "registry.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        packages = data.get("packages") or []
        repos = {str(pkg["repo"]) for pkg in packages if isinstance(pkg, dict) and pkg.get("repo")}
        self.assertGreaterEqual(len(repos), 2, "registry.yaml must resolve to a non-trivial publishing-repo set")
        return frozenset(repos)

    @staticmethod
    def _multiline_repo_list(block: str) -> frozenset[str]:
        return frozenset(line.strip() for line in (block or "").splitlines() if line.strip())

    def _mint_repositories(self, job: str) -> frozenset[str]:
        mint = self._mint_steps(job)[0]
        repos_block = (mint.get("with") or {}).get("repositories")
        self.assertIsInstance(repos_block, str, f"{job} mint step must declare a multiline repositories: block")
        return self._multiline_repo_list(repos_block)

    def test_mint_repositories_lockstep_with_registry(self):
        """App-token scope must be exactly the registry's publishing repos (R7 least-privilege)."""
        expected = self._registry_publishing_repos()
        propose_repos = self._mint_repositories("propose")
        ceremony_repos = self._mint_repositories("ceremony")
        self.assertEqual(
            propose_repos,
            expected,
            "propose mint repositories: must equal registry.yaml's publishing-repo set " f"(extra={sorted(propose_repos - expected)}, missing={sorted(expected - propose_repos)}).",
        )
        self.assertEqual(
            ceremony_repos,
            expected,
            "ceremony mint repositories: must equal registry.yaml's publishing-repo set " f"(extra={sorted(ceremony_repos - expected)}, missing={sorted(expected - ceremony_repos)}).",
        )
        self.assertEqual(
            propose_repos,
            ceremony_repos,
            "propose and ceremony mint repositories: lists must be identical (one R7 scope, two write jobs).",
        )

    def test_ecosystem_repos_are_registry_siblings(self):
        """``ECOSYSTEM_REPOS`` clones the sibling publishing repos; juniper-ml is the checkout itself."""
        expected_siblings = self._registry_publishing_repos() - {"juniper-ml"}
        ecosystem_block = (self.doc.get("env") or {}).get("ECOSYSTEM_REPOS")
        self.assertIsInstance(ecosystem_block, str, "workflow env.ECOSYSTEM_REPOS must be a multiline string")
        ecosystem = self._multiline_repo_list(ecosystem_block)
        self.assertEqual(
            ecosystem,
            expected_siblings,
            "env.ECOSYSTEM_REPOS must equal registry publishing repos minus juniper-ml " f"(extra={sorted(ecosystem - expected_siblings)}, missing={sorted(expected_siblings - ecosystem)}).",
        )
        self.assertNotIn("juniper-ml", ecosystem, "juniper-ml is the workflow checkout, not an ECOSYSTEM_REPOS clone")
        self.assertNotIn("juniper-deploy", ecosystem, "juniper-deploy hosts no PyPI package and must not be cloned")

    def _write_job_run_scripts(self, job: str) -> str:
        """Concatenate every ``run:`` script body in a write job (for structural pin searches)."""
        return "\n".join(str(step.get("run") or "") for step in self._job_steps(job))

    def test_packages_input_charset_reject_present_on_both_write_jobs(self):
        """Operator ``packages`` dispatch must reject non-pypi-name tokens before shelling them out."""
        # The live gate: ``[[ ! "$tok" =~ ^[a-z0-9][a-z0-9-]*$ ]]`` + ``exit 2`` + ``::error::``.
        charset_needle = r"^[a-z0-9][a-z0-9-]*$"
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                blob = self._write_job_run_scripts(job)
                self.assertIn(
                    charset_needle,
                    blob,
                    f"{job} must validate every packages-input token against the pypi-name charset " "(reject ../x / UPPER / ;rm rather than shelling garbage into propose.py/ceremony.py).",
                )
                self.assertIn("exit 2", blob, f"{job} packages-input reject path must exit 2")
                self.assertIn("::error::", blob, f"{job} packages-input reject path must emit ::error::")
                self.assertIn("PACKAGES_INPUT", blob, f"{job} must read the packages dispatch input")

    def test_cross_repo_flag_gated_on_app_token_on_both_write_jobs(self):
        """``--cross-repo`` must be capability-gated on a minted APP_TOKEN (degraded path stays in-repo)."""
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                blob = self._write_job_run_scripts(job)
                self.assertIn("--cross-repo", blob, f"{job} must know about --cross-repo")
                # The gate: only append --cross-repo when APP_TOKEN is non-empty (minted).
                self.assertRegex(
                    blob,
                    r'if\s+\[\s+-n\s+"\$\{APP_TOKEN:-\}"\s*\]',
                    f"{job} must gate --cross-repo on a non-empty APP_TOKEN " "(unconditional --cross-repo breaks the no-App degraded GITHUB_TOKEN path).",
                )
                # Sanity: the flag is added inside that branch, not as a bare always-on argv.
                # Extract the APP_TOKEN if-block (best-effort; structural, not a shell parser).
                match = re.search(
                    r'if\s+\[\s+-n\s+"\$\{APP_TOKEN:-\}"\s*\]\s*;\s*then(.*?)else',
                    blob,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(match, f"{job} APP_TOKEN if/then/else block not found")
                self.assertIn("--cross-repo", match.group(1), f"{job} must append --cross-repo inside the APP_TOKEN-present branch")

    # (g) Cross-repo headless git identity must be --global (ml#705 / run 30040138774) -------------
    def _identity_steps(self, job):
        """Steps whose name marks the headless git-identity configuration (both write jobs share the name)."""
        return [s for s in self._job_steps(job) if "Configure git identity" in str(s.get("name", ""))]

    def test_write_jobs_configure_git_identity_globally(self):
        """Pin ``git config --global`` for user.name / user.email / commit.gpgsign on EVERY write job.

        A bare ``git config user.*`` (repo-local) is the #705 failure class: it succeeds on the
        juniper-ml checkout and then every sibling clone dies with ``Author identity unknown``.
        """
        # Repo-local forms that would reintroduce the bug (must NOT appear in the identity step).
        local_only = (
            re.compile(r"(?m)^\s*git\s+config\s+user\.name\b"),
            re.compile(r"(?m)^\s*git\s+config\s+user\.email\b"),
            re.compile(r"(?m)^\s*git\s+config\s+commit\.gpgsign\b"),
        )
        required_global = (
            "git config --global user.name",
            "git config --global user.email",
            "git config --global commit.gpgsign",
        )
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                steps = self._identity_steps(job)
                self.assertEqual(
                    len(steps),
                    1,
                    f"the {job} job must have exactly one 'Configure git identity' step " f"(cross-repo sibling commits need a job-scoped global identity).",
                )
                run = str(steps[0].get("run", ""))
                for needle in required_global:
                    self.assertIn(
                        needle,
                        run,
                        f"{job} identity step must use `{needle}` -- repo-local config does not " f"propagate into freshly-cloned sibling checkouts (ml#705).",
                    )
                for pat in local_only:
                    self.assertIsNone(
                        pat.search(run),
                        f"{job} identity step must not use repo-local `{pat.pattern}` " f"(would reintroduce Author-identity-unknown on sibling checkouts).",
                    )

    def test_detect_job_does_not_configure_git_identity(self):
        # detect is read-only and never commits; an identity step there would be dead / misleading.
        self.assertEqual(
            self._identity_steps("detect"),
            [],
            "the detect job must not configure git identity (it never commits; write-jobs only).",
        )

    # (h) Phase 4.1: mint repositories / ECOSYSTEM_REPOS lockstep with registry.yaml --------------
    def _registry_publishing_repos(self) -> frozenset[str]:
        """Unique ``repo`` values from ``util/release_train/registry.yaml`` (the S4.1 source of truth)."""
        self.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        registry_path = self.repo_root / "util" / "release_train" / "registry.yaml"
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        packages = data.get("packages") or []
        repos = {str(pkg["repo"]) for pkg in packages if isinstance(pkg, dict) and pkg.get("repo")}
        self.assertGreaterEqual(len(repos), 2, "registry.yaml must resolve to a non-trivial publishing-repo set")
        return frozenset(repos)

    @staticmethod
    def _multiline_repo_list(block: str) -> frozenset[str]:
        return frozenset(line.strip() for line in (block or "").splitlines() if line.strip())

    def _mint_repositories(self, job: str) -> frozenset[str]:
        mint = self._mint_steps(job)[0]
        repos_block = (mint.get("with") or {}).get("repositories")
        self.assertIsInstance(repos_block, str, f"{job} mint step must declare a multiline repositories: block")
        return self._multiline_repo_list(repos_block)

    def test_mint_repositories_lockstep_with_registry(self):
        """App-token scope must be exactly the registry's publishing repos (R7 least-privilege)."""
        expected = self._registry_publishing_repos()
        propose_repos = self._mint_repositories("propose")
        ceremony_repos = self._mint_repositories("ceremony")
        self.assertEqual(
            propose_repos,
            expected,
            "propose mint repositories: must equal registry.yaml's publishing-repo set " f"(extra={sorted(propose_repos - expected)}, missing={sorted(expected - propose_repos)}).",
        )
        self.assertEqual(
            ceremony_repos,
            expected,
            "ceremony mint repositories: must equal registry.yaml's publishing-repo set " f"(extra={sorted(ceremony_repos - expected)}, missing={sorted(expected - ceremony_repos)}).",
        )
        self.assertEqual(
            propose_repos,
            ceremony_repos,
            "propose and ceremony mint repositories: lists must be identical (one R7 scope, two write jobs).",
        )

    def test_ecosystem_repos_are_registry_siblings(self):
        """``ECOSYSTEM_REPOS`` clones the sibling publishing repos; juniper-ml is the checkout itself."""
        expected_siblings = self._registry_publishing_repos() - {"juniper-ml"}
        ecosystem_block = (self.doc.get("env") or {}).get("ECOSYSTEM_REPOS")
        self.assertIsInstance(ecosystem_block, str, "workflow env.ECOSYSTEM_REPOS must be a multiline string")
        ecosystem = self._multiline_repo_list(ecosystem_block)
        self.assertEqual(
            ecosystem,
            expected_siblings,
            "env.ECOSYSTEM_REPOS must equal registry publishing repos minus juniper-ml " f"(extra={sorted(ecosystem - expected_siblings)}, missing={sorted(expected_siblings - ecosystem)}).",
        )
        self.assertNotIn("juniper-ml", ecosystem, "juniper-ml is the workflow checkout, not an ECOSYSTEM_REPOS clone")
        self.assertNotIn("juniper-deploy", ecosystem, "juniper-deploy hosts no PyPI package and must not be cloned")

    def _write_job_run_scripts(self, job: str) -> str:
        """Concatenate every ``run:`` script body in a write job (for structural pin searches)."""
        return "\n".join(str(step.get("run") or "") for step in self._job_steps(job))

    def test_packages_input_charset_reject_present_on_both_write_jobs(self):
        """Operator ``packages`` dispatch must reject non-pypi-name tokens before shelling them out."""
        # The live gate: ``[[ ! "$tok" =~ ^[a-z0-9][a-z0-9-]*$ ]]`` + ``exit 2`` + ``::error::``.
        charset_needle = r"^[a-z0-9][a-z0-9-]*$"
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                blob = self._write_job_run_scripts(job)
                self.assertIn(
                    charset_needle,
                    blob,
                    f"{job} must validate every packages-input token against the pypi-name charset " "(reject ../x / UPPER / ;rm rather than shelling garbage into propose.py/ceremony.py).",
                )
                self.assertIn("exit 2", blob, f"{job} packages-input reject path must exit 2")
                self.assertIn("::error::", blob, f"{job} packages-input reject path must emit ::error::")
                self.assertIn("PACKAGES_INPUT", blob, f"{job} must read the packages dispatch input")

    def test_cross_repo_flag_gated_on_app_token_on_both_write_jobs(self):
        """``--cross-repo`` must be capability-gated on a minted APP_TOKEN (degraded path stays in-repo)."""
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                blob = self._write_job_run_scripts(job)
                self.assertIn("--cross-repo", blob, f"{job} must know about --cross-repo")
                # The gate: only append --cross-repo when APP_TOKEN is non-empty (minted).
                self.assertRegex(
                    blob,
                    r'if\s+\[\s+-n\s+"\$\{APP_TOKEN:-\}"\s*\]',
                    f"{job} must gate --cross-repo on a non-empty APP_TOKEN " "(unconditional --cross-repo breaks the no-App degraded GITHUB_TOKEN path).",
                )
                # Sanity: the flag is added inside that branch, not as a bare always-on argv.
                # Extract the APP_TOKEN if-block (best-effort; structural, not a shell parser).
                match = re.search(
                    r'if\s+\[\s+-n\s+"\$\{APP_TOKEN:-\}"\s*\]\s*;\s*then(.*?)else',
                    blob,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(match, f"{job} APP_TOKEN if/then/else block not found")
                self.assertIn("--cross-repo", match.group(1), f"{job} must append --cross-repo inside the APP_TOKEN-present branch")

    # (g) Cross-repo headless git identity must be --global (ml#705 / run 30040138774) -------------
    def _identity_steps(self, job):
        """Steps whose name marks the headless git-identity configuration (both write jobs share the name)."""
        return [s for s in self._job_steps(job) if "Configure git identity" in str(s.get("name", ""))]

    def test_write_jobs_configure_git_identity_globally(self):
        """Pin ``git config --global`` for user.name / user.email / commit.gpgsign on EVERY write job.

        A bare ``git config user.*`` (repo-local) is the #705 failure class: it succeeds on the
        juniper-ml checkout and then every sibling clone dies with ``Author identity unknown``.
        """
        # Repo-local forms that would reintroduce the bug (must NOT appear in the identity step).
        local_only = (
            re.compile(r"(?m)^\s*git\s+config\s+user\.name\b"),
            re.compile(r"(?m)^\s*git\s+config\s+user\.email\b"),
            re.compile(r"(?m)^\s*git\s+config\s+commit\.gpgsign\b"),
        )
        required_global = (
            "git config --global user.name",
            "git config --global user.email",
            "git config --global commit.gpgsign",
        )
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                steps = self._identity_steps(job)
                self.assertEqual(
                    len(steps),
                    1,
                    f"the {job} job must have exactly one 'Configure git identity' step " f"(cross-repo sibling commits need a job-scoped global identity).",
                )
                run = str(steps[0].get("run", ""))
                for needle in required_global:
                    self.assertIn(
                        needle,
                        run,
                        f"{job} identity step must use `{needle}` -- repo-local config does not " f"propagate into freshly-cloned sibling checkouts (ml#705).",
                    )
                for pat in local_only:
                    self.assertIsNone(
                        pat.search(run),
                        f"{job} identity step must not use repo-local `{pat.pattern}` " f"(would reintroduce Author-identity-unknown on sibling checkouts).",
                    )

    def test_detect_job_does_not_configure_git_identity(self):
        # detect is read-only and never commits; an identity step there would be dead / misleading.
        self.assertEqual(
            self._identity_steps("detect"),
            [],
            "the detect job must not configure git identity (it never commits; write-jobs only).",
        )


# ── YAML-extraction rehearsal 1: the mode-resolution matrix (the real shell, run hermetically) ──


class ModeResolutionMatrixTest(unittest.TestCase):
    """Extract the workflow's ``id: mode`` shell and run it over the whole mode matrix -- proving the ACTUAL
    resolver (not a reimplementation) accepts all four modes (incl. ``ceremony`` now valid), degrades an
    unknown value to ``report``, and honours dispatch-input > repo-variable > default precedence (plan S9.4)."""

    script: str  # the extracted `id: mode` shell (set in setUpClass)

    @classmethod
    def setUpClass(cls):
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        step = next((s for s in doc["jobs"]["detect"]["steps"] if s.get("id") == "mode"), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest("could not locate the detect job's `id: mode` run step")
        cls.script = step["run"]

    def _resolve(self, mode_input: "str | None", mode_var: "str | None") -> str:
        """Run the extracted resolver shell with the given env; return the ``mode=`` it wrote to GITHUB_OUTPUT."""
        with tempfile.TemporaryDirectory() as td:
            script_path = Path(td) / "resolve.sh"
            script_path.write_text(self.script, encoding="utf-8")
            gh_out = Path(td) / "gh_output"
            gh_out.write_text("", encoding="utf-8")
            env = RedactedEnv(os.environ)
            # Mirror the workflow's env: block (values are always SET, possibly empty).
            env["MODE_INPUT"] = "" if mode_input is None else mode_input
            env["MODE_VAR"] = "" if mode_var is None else mode_var
            env["GITHUB_OUTPUT"] = str(gh_out)
            proc = subprocess.run(["bash", str(script_path)], capture_output=True, text=True, env=env, check=False)  # nosec B603,B607 - the workflow's own shell, fixed argv
            self.assertEqual(proc.returncode, 0, f"resolver shell exited {proc.returncode}: {proc.stderr}")
            written = gh_out.read_text(encoding="utf-8")
            m = re.search(r"^mode=(.*)$", written, re.MULTILINE)
            self.assertIsNotNone(m, f"resolver wrote no mode= line; GITHUB_OUTPUT was:\n{written}")
            return m.group(1).strip()

    def test_mode_matrix(self):
        cases = [
            # (dispatch input, repo variable, expected resolved mode)
            ("", "", "report"),  # default
            ("off", "", "off"),
            ("report", "", "report"),
            ("propose", "", "propose"),
            ("ceremony", "", "ceremony"),  # Phase 4.3: no longer degrades to report
            ("bogus", "", "report"),  # unknown -> warn + report
            ("", "ceremony", "ceremony"),  # repo-variable path
            ("", "off", "off"),
            ("", "propose", "propose"),
            ("propose", "off", "propose"),  # dispatch input WINS over the repo variable
            ("ceremony", "report", "ceremony"),
            ("off", "ceremony", "off"),
        ]
        for mode_input, mode_var, expected in cases:
            with self.subTest(input=mode_input, var=mode_var):
                self.assertEqual(self._resolve(mode_input, mode_var), expected)

    def test_ceremony_is_a_first_class_mode(self):
        # the exact regression this phase fixes: ceremony must resolve to ceremony (not report).
        self.assertEqual(self._resolve("ceremony", ""), "ceremony")

    def test_unknown_warns_on_stderr_or_stdout(self):
        # a bogus value must still resolve to report AND emit the ::warning:: annotation.
        with tempfile.TemporaryDirectory() as td:
            script_path = Path(td) / "resolve.sh"
            script_path.write_text(self.script, encoding="utf-8")
            gh_out = Path(td) / "gh_output"
            gh_out.write_text("", encoding="utf-8")
            env = RedactedEnv(os.environ, MODE_INPUT="wat", MODE_VAR="", GITHUB_OUTPUT=str(gh_out))
            proc = subprocess.run(["bash", str(script_path)], capture_output=True, text=True, env=env, check=False)  # nosec B603,B607
            self.assertIn("::warning::", proc.stdout + proc.stderr)
            self.assertIn("mode=report", gh_out.read_text(encoding="utf-8"))


# ── YAML-extraction rehearsal 2: the ceremony step summary (the real Python, run hermetically) ──


CEREMONY_OUTPUT_FIXTURE = "\n".join(
    [
        "ceremony-run: 6 package(s) processed (execute)",
        "ceremony-result: plan=CEREMONY_PLANNED state=PENDING_PYPI_APPROVAL pkg=juniper-observability version=0.5.0 repo=juniper-ml pr=https://github.com/pcalnon/juniper-ml/pull/1 release=https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.5.0 issue=- issue_failed=0",
        "ceremony-result: plan=RESUME_MONITOR state=PENDING_PYPI_APPROVAL pkg=juniper-ci-tools version=0.8.0 repo=juniper-ml pr=- release=- issue=- issue_failed=0",
        "ceremony-result: plan=CEREMONY_PLANNED state=HALTED pkg=juniper-service-core version=0.6.0 repo=juniper-ml pr=- release=- issue=https://github.com/pcalnon/juniper-ml/issues/5 issue_failed=0",
        "ceremony-result: plan=CEREMONY_PLANNED state=HALTED pkg=juniper-cascor-client version=0.6.0 repo=juniper-cascor-client pr=- release=- issue=- issue_failed=1",
        "ceremony-result: plan=CEREMONY_PLANNED state=IN_PROGRESS pkg=juniper-canopy version=0.6.0 repo=juniper-canopy pr=- release=- issue=- issue_failed=0",
        "ceremony-result: plan=SKIPPED_CROSS_REPO state=SKIPPED_CROSS_REPO pkg=juniper-data version=0.7.0 repo=juniper-data pr=- release=- issue=- issue_failed=0",
        "",
    ]
)


class CeremonySummaryRehearsalTest(unittest.TestCase):
    """Extract the ceremony job's step-summary Python and run it over a synthetic ``ceremony-output.txt``,
    proving the ACTUAL renderer buckets ceremonies/resumes/HALTs/PENDING_PYPI_APPROVAL and surfaces the
    degraded HALT-issue (issue_failed=1) line -- the deliverable-1 + deliverable-2 acceptance evidence."""

    py_body: str  # the extracted ceremony-summary Python heredoc body (set in setUpClass)

    @classmethod
    def setUpClass(cls):
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        step = next((s for s in doc["jobs"]["ceremony"]["steps"] if s.get("name") == "Render ceremony step summary"), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest("could not locate the ceremony job's summary step")
        # the run is `python - <<'PY'\n<body>\nPY\n` -- extract the heredoc body (up to the line that is
        # exactly the `PY` terminator) and run it via sys.executable (avoids depending on a `python` binary).
        run = step["run"]
        if "<<'PY'\n" not in run:
            raise unittest.SkipTest("ceremony summary step is not a `python - <<'PY'` heredoc")
        after = run.split("<<'PY'\n", 1)[1]
        body_lines = []
        for line in after.splitlines():
            if line.strip() == "PY":
                break
            body_lines.append(line)
        cls.py_body = "\n".join(body_lines)

    def _render(self, output_text: str) -> str:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "ceremony-output.txt").write_text(output_text, encoding="utf-8")
            summary = ws / "step_summary.md"
            summary.write_text("", encoding="utf-8")
            env = RedactedEnv(os.environ, GITHUB_WORKSPACE=str(ws), GITHUB_STEP_SUMMARY=str(summary))
            proc = subprocess.run([sys.executable, "-c", self.py_body], capture_output=True, text=True, env=env, check=False)  # nosec B603 - the workflow's own python body
            self.assertEqual(proc.returncode, 0, f"summary renderer failed: {proc.stderr}")
            return summary.read_text(encoding="utf-8")

    def test_renders_all_buckets_and_degraded_issue(self):
        md = self._render(CEREMONY_OUTPUT_FIXTURE)
        self.assertIn("Release train -- ceremony mode", md)
        # counts line: 6 processed = 4 ceremony (plan=CEREMONY_PLANNED) + 1 resume + 1 skipped; 2 pending, 2 halted, 1 building.
        self.assertIn("6 package(s) processed", md)
        self.assertIn("4 ceremony", md)
        self.assertIn("1 resume-monitor", md)
        self.assertIn("2 PENDING_PYPI_APPROVAL", md)
        self.assertIn("2 HALTED", md)
        # PENDING section + the owner Gate-2 framing
        self.assertIn("PENDING_PYPI_APPROVAL -- owner Gate 2", md)
        self.assertIn("juniper-observability", md)
        # HALT section, incl. the DEGRADED (issue_failed=1) line -- deliverable-2 acceptance
        self.assertIn("HALTED -- owner attention", md)
        self.assertIn("juniper-cascor-client", md)
        self.assertIn("could NOT be filed", md)
        # still-building section
        self.assertIn("Still building", md)
        self.assertIn("juniper-canopy", md)

    def test_no_results_is_clean_not_a_failure_banner(self):
        md = self._render("ceremony-run: no BUMPED_NOT_RELEASED packages in the manifest -- nothing to do (execute).\n")
        self.assertIn("0 package(s) processed", md)
        self.assertIn("nothing to do", md)
        self.assertNotIn("produced no output", md)  # non-empty output -> not the crash banner

    def test_truly_empty_output_shows_crash_banner(self):
        md = self._render("")
        self.assertIn("produced no output", md)


# ── YAML-extraction rehearsal 3: the propose step summary (the real Python, run hermetically) ──


PROPOSE_OUTPUT_FIXTURE = "\n".join(
    [
        "opened: juniper-observability (juniper-ml) -- https://github.com/pcalnon/juniper-ml/pull/1",
        "opened: juniper-ci-tools (juniper-ml) -- https://github.com/pcalnon/juniper-ml/pull/2",
        "skip: juniper-cascor (juniper-cascor) -- --cross-repo required for sibling packages (no App token)",
        "skip: juniper-thing (juniper-ml) -- duplicate open proposal PR #99",
        "",
    ]
)


class ProposeSummaryRehearsalTest(unittest.TestCase):
    """Extract the propose job's step-summary Python and run it over a synthetic ``propose-output.txt``,
    proving the ACTUAL renderer buckets ``opened:`` / ``skip:`` lines and surfaces the empty-output
    crash banner -- the operator-facing deliverable of propose mode (plan S12 step 2.2).

    Ceremony already has ``CeremonySummaryRehearsalTest``; without this twin, a propose-summary edit that
    stops parsing ``opened:`` / ``skip:`` (or drops the empty-output banner) is invisible to CI until a
    live propose run misreports how many PRs opened.
    """

    py_body: str  # the extracted propose-summary Python heredoc body (set in setUpClass)

    @classmethod
    def setUpClass(cls):
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        step = next((s for s in doc["jobs"]["propose"]["steps"] if s.get("name") == "Render propose step summary"), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest("could not locate the propose job's summary step")
        run = step["run"]
        if "<<'PY'\n" not in run:
            raise unittest.SkipTest("propose summary step is not a `python - <<'PY'` heredoc")
        after = run.split("<<'PY'\n", 1)[1]
        body_lines = []
        for line in after.splitlines():
            if line.strip() == "PY":
                break
            body_lines.append(line)
        cls.py_body = "\n".join(body_lines)

    def _render(self, output_text: str) -> str:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "propose-output.txt").write_text(output_text, encoding="utf-8")
            summary = ws / "step_summary.md"
            summary.write_text("", encoding="utf-8")
            env = RedactedEnv(os.environ, GITHUB_WORKSPACE=str(ws), GITHUB_STEP_SUMMARY=str(summary))
            proc = subprocess.run([sys.executable, "-c", self.py_body], capture_output=True, text=True, env=env, check=False)  # nosec B603 - the workflow's own python body
            self.assertEqual(proc.returncode, 0, f"summary renderer failed: {proc.stderr}")
            return summary.read_text(encoding="utf-8")

    def test_renders_opened_and_skipped_buckets(self):
        md = self._render(PROPOSE_OUTPUT_FIXTURE)
        self.assertIn("Release train -- propose mode", md)
        self.assertIn("2 proposal PR(s) opened, 2 skipped.", md)
        self.assertIn("### Opened (standard-gated -- owner reviews & merges)", md)
        self.assertIn("juniper-observability", md)
        self.assertIn("juniper-ci-tools", md)
        self.assertIn("### Skipped", md)
        self.assertIn("juniper-cascor", md)
        self.assertIn("duplicate open proposal PR #99", md)
        # Gate-1 framing (App vs degraded no-App path) must stay visible to operators.
        self.assertIn("standard-gated", md)
        self.assertIn("GitHub App", md)

    def test_no_opened_or_skipped_is_clean_zero_counts(self):
        md = self._render("propose-run: no UNRELEASED_CHANGES packages -- nothing to propose.\n")
        self.assertIn("0 proposal PR(s) opened, 0 skipped.", md)
        self.assertNotIn("### Opened", md)
        self.assertNotIn("### Skipped", md)
        self.assertNotIn("produced no output", md)  # non-empty output -> not the crash banner

    def test_truly_empty_output_shows_crash_banner(self):
        md = self._render("")
        self.assertIn("produced no output", md)
        self.assertIn("0 proposal PR(s) opened, 0 skipped.", md)


# Matches `python - <<'PY'` and the Slack redirect form `python - <<'PY' > slack-payload.json`.
_PY_HEREDOC_OPENER = re.compile(r"<<'PY'(?:\s*>\s*\S+)?\n")


_PACKAGES_STEP_NAMES = {
    "propose": "Open release-proposal PRs (propose.py --execute)",
    "ceremony": "Run the ceremony (ceremony.py --execute)",
}


def _extract_packages_prefix(run: str) -> str:
    """Take the write-job run script up to (not including) the ``rc=0`` / python invocation.

    The prefix owns the ``packages`` charset reject and the App-token ``--cross-repo`` gate; the
    remainder shells out to propose.py / ceremony.py and is covered by their hermetic suites.
    Append a deterministic ARGS line so the rehearsal can assert resolved flags without a fake python.
    """
    lines = run.splitlines()
    kept = []
    for line in lines:
        if re.match(r"^\s*rc=0\s*$", line):
            break
        kept.append(line)
    kept.append('echo "ARGS:${pkg_args[*]}|CROSS:${cross_repo_args[*]}"')
    return "\n".join(kept) + "\n"


class PackagesInputRehearsalTest(unittest.TestCase):
    """Extract each write job's ``packages`` / ``--cross-repo`` shell prefix and *run* it.

    Complementary to the structural string pins (charset needle / APP_TOKEN ``if`` present): this
    rehearses the ACTUAL shell so a drifted regex or a reordered gate that still "contains" the
    substrings cannot silently accept garbage or always pass ``--cross-repo``.

    Pins (a) garbage ``packages`` tokens exit 2 with ``::error::`` before any python runs,
    (b) empty input means no ``--package`` filter, (c) commas and whitespace are equivalent,
    (d) ``--cross-repo`` is emitted ONLY when ``APP_TOKEN`` is non-empty (Phase 4.1 capability gate).
    """

    prefixes: dict  # job -> extracted shell prefix

    @classmethod
    def setUpClass(cls):
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf_path = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf_path}")
        doc = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
        cls.prefixes = {}
        for job, step_name in _PACKAGES_STEP_NAMES.items():
            step = next((s for s in (doc["jobs"][job].get("steps") or []) if s.get("name") == step_name), None)
            if step is None or "run" not in step:
                raise unittest.SkipTest(f"could not locate {job} step {step_name!r}")
            run = step["run"]
            if "PACKAGES_INPUT" not in (step.get("env") or {}):
                raise unittest.SkipTest(f"{job} step must bind PACKAGES_INPUT from inputs.packages")
            if "pkg_args" not in run or "cross_repo_args" not in run:
                raise unittest.SkipTest(f"{job} step lacks packages/cross-repo parsing")
            cls.prefixes[job] = _extract_packages_prefix(run)

    def _run(self, job: str, packages_input: str, app_token: str = "") -> "subprocess.CompletedProcess":
        with tempfile.TemporaryDirectory() as td:
            script_path = Path(td) / "packages.sh"
            script_path.write_text(self.prefixes[job], encoding="utf-8")
            env = RedactedEnv(os.environ, PACKAGES_INPUT=packages_input, APP_TOKEN=app_token)
            return subprocess.run(["bash", str(script_path)], capture_output=True, text=True, env=env, check=False)  # nosec B603,B607 - workflow's own shell prefix

    def test_both_write_jobs_share_packages_charset_and_cross_repo_gate(self):
        # structural: the charset regex + APP_TOKEN gate exist in BOTH write-job prefixes (drift of one
        # job alone would let garbage through propose while ceremony rejects, or vice versa).
        for job, prefix in self.prefixes.items():
            with self.subTest(job=job):
                self.assertIn("^[a-z0-9][a-z0-9-]*$", prefix)
                self.assertIn('if [ -n "${APP_TOKEN:-}" ]', prefix)
                self.assertIn("--cross-repo", prefix)

    def test_empty_packages_means_all_eligible(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                proc = self._run(job, "")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("package filter: <all eligible packages>", proc.stdout)
                self.assertIn("ARGS:|CROSS:", proc.stdout)  # no --package, no --cross-repo

    def test_comma_and_whitespace_separated_tokens(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job):
                proc = self._run(job, "juniper-observability, juniper-ci-tools")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("--package juniper-observability", proc.stdout)
                self.assertIn("--package juniper-ci-tools", proc.stdout)
                self.assertRegex(proc.stdout, r"ARGS:--package juniper-observability --package juniper-ci-tools\|CROSS:")

    def test_invalid_token_exits_2_with_error_annotation(self):
        for job in WRITE_JOBS:
            for garbage in ("Juniper-Observability", "../evil", "juniper_observability", "a;rm -rf /"):
                with self.subTest(job=job, tok=garbage):
                    proc = self._run(job, garbage)
                    self.assertEqual(proc.returncode, 2, f"expected exit 2 for {garbage!r}; got {proc.returncode}: {proc.stdout}{proc.stderr}")
                    self.assertIn("::error::invalid package token", proc.stdout + proc.stderr)
                    self.assertNotIn("ARGS:", proc.stdout)  # never reached the stub echo

    def test_cross_repo_only_when_app_token_nonempty(self):
        for job in WRITE_JOBS:
            with self.subTest(job=job, token="present"):
                proc = self._run(job, "juniper-observability", app_token="minted-token")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("cross-repo", proc.stdout.lower())
                self.assertRegex(proc.stdout, r"ARGS:--package juniper-observability\|CROSS:--cross-repo")
            with self.subTest(job=job, token="absent"):
                proc = self._run(job, "juniper-observability", app_token="")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("degraded", proc.stdout.lower())
                self.assertRegex(proc.stdout, r"ARGS:--package juniper-observability\|CROSS:$")


class HeredocBalanceTest(unittest.TestCase):
    """Every ``run:`` script's ``<<'PY'`` heredocs must have exactly one terminator each.

    The first live ceremony run (30051952226) went red on exit 127 AFTER a fully successful
    ceremony: the summary step's heredoc carried a duplicated ``PY`` terminator line, and bash
    executed the second one as a command. The YAML-extraction rehearsals exercise the python
    BETWEEN the markers, so only a raw-script structural check catches this class.
    """

    def test_py_heredocs_are_balanced_in_every_run_script(self):
        workflow_path = _find_repo_root(Path(__file__).resolve().parent) / ".github" / "workflows" / WORKFLOW_NAME
        wf = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        problems = []
        for jname, job in (wf.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                run = step.get("run") or ""
                if "<<'PY'" not in run:
                    continue
                openers = run.count("<<'PY'")
                terminators = sum(1 for ln in run.splitlines() if ln.strip() == "PY" and "<<" not in ln)
                if openers != terminators:
                    problems.append(f"{jname} / {step.get('name')!r}: {openers} <<'PY' opener(s) vs {terminators} PY terminator line(s)")
        self.assertEqual(problems, [], "unbalanced PY heredoc(s) in release-train.yml -- a stray terminator executes as a shell command (exit 127, the run-30051952226 class): " + "; ".join(problems))


class HeredocCompileTest(unittest.TestCase):
    """Every ``<<'PY'`` heredoc body in ``release-train.yml`` must compile as Python.

    Balance alone (#708) does not catch a syntax-broken summary / Slack payload body — bash still
    launches ``python -``, then the step fails mid-run after the real work finished (the same
    late-failure class as run-30051952226, just with ``SyntaxError`` instead of exit 127). The
    YAML-extraction rehearsals only exercise two of the four heredocs; this lint compiles ALL of
    them (incl. the Slack redirect form ``<<'PY' > slack-payload.json``).
    """

    def test_every_py_heredoc_body_compiles(self):
        workflow_path = _find_repo_root(Path(__file__).resolve().parent) / ".github" / "workflows" / WORKFLOW_NAME
        wf = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        compiled = 0
        problems = []
        for jname, job in (wf.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                run = step.get("run") or ""
                if "<<'PY'" not in run:
                    continue
                step_name = step.get("name") or "<unnamed>"
                bodies = list(_iter_py_heredoc_bodies(run))
                if not bodies:
                    problems.append(f"{jname} / {step_name!r}: saw <<'PY' but extracted zero bodies")
                    continue
                for idx, (_match, body) in enumerate(bodies, 1):
                    if not body.strip():
                        problems.append(f"{jname} / {step_name!r} heredoc#{idx}: empty body")
                        continue
                    try:
                        compile(body, f"{WORKFLOW_NAME}:{jname}:{step_name}:heredoc{idx}", "exec")
                    except SyntaxError as exc:
                        problems.append(f"{jname} / {step_name!r} heredoc#{idx}: {exc}")
                    else:
                        compiled += 1
        self.assertEqual(
            problems,
            [],
            "PY heredoc body(ies) in release-train.yml failed to compile -- a SyntaxError would " "fail the step only after the real work finished (late-failure class): " + "; ".join(problems),
        )
        # Pin the known set so a deleted heredoc (or a new uncompiled one that the opener regex
        # misses) cannot silently shrink coverage. Today: detect summary, detect Slack, propose
        # summary, ceremony summary.
        self.assertEqual(
            compiled,
            4,
            f"expected to compile 4 PY heredoc bodies in {WORKFLOW_NAME}; got {compiled} " f"(update this pin when intentionally adding/removing a <<'PY' block).",
        )


if __name__ == "__main__":
    unittest.main()
