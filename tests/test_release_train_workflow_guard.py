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
      ``== 'off'`` quiesce step), and both write jobs are unreachable (their ``if`` requires a non-off mode).

Beyond the structural pins, two **YAML-extraction rehearsals** execute the actual workflow snippets
hermetically (the "run the real thing, not a reimplementation" idiom): ``ModeResolutionMatrixTest`` extracts
the ``id: mode`` step's shell and runs it over the whole mode matrix (incl. ``ceremony`` now valid + the
dispatch-input > repo-variable precedence), and ``CeremonySummaryRehearsalTest`` extracts the ceremony
step-summary Python and runs it over a synthetic ``ceremony-output.txt`` (proving it renders
ceremonies/resumes/HALTs/PENDING_PYPI_APPROVAL and the degraded-issue line). ``HeredocBalanceTest`` +
``HeredocCompileTest`` pin every ``<<'PY'`` opener/terminator pair and that each heredoc body compiles
(catching the late-failure class #708's balance lint alone cannot see).

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


# Matches `python - <<'PY'` and the Slack redirect form `python - <<'PY' > slack-payload.json`.
_PY_HEREDOC_OPENER = re.compile(r"<<'PY'(?:\s*>\s*\S+)?\n")


def _iter_py_heredoc_bodies(run: str):
    """Yield ``(opener_match, body)`` for every ``<<'PY'…`` heredoc in a workflow ``run:`` script."""
    for match in _PY_HEREDOC_OPENER.finditer(run):
        after = run[match.end() :]
        body_lines = []
        for line in after.splitlines():
            if line.strip() == "PY" and "<<" not in line:
                break
            body_lines.append(line)
        yield match, "\n".join(body_lines) + ("\n" if body_lines else "")


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
