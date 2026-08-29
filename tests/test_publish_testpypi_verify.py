#!/usr/bin/env python3
"""Structural + hermetic YAML-extraction gate for publish.yml TestPyPI install verification.

The meta-package publish path (``.github/workflows/publish.yml``) must prove the
uploaded wheel installs from TestPyPI AND that the light extras ``[clients]`` and
``[tools]`` still resolve against published metadata. A broken extras declaration
(mistyped name, missing roll-up, dangling self-ref) that only the bare install
would catch would otherwise ship to production PyPI.

**2026-08-08 two-phase amendment (owner-approved).** The verify used to pass
``--index-url <testpypi> --extra-index-url <pypi>`` to a single ``pip install``.
pip has NO index priority: those two flags form ONE merged namespace and pip picks
the HIGHEST version across both. That is a dependency-confusion vector -- a TestPyPI
squatter outranks the real package. It fired for real: TestPyPI ``fastapi 1.0`` (a
broken sdist) beat production ``fastapi 0.141.1`` and killed the v0.7.0 verify
(run 31281873275). The verify is now two phases:

  * **Phase 1 (provenance)** -- ``pip download --no-deps`` from TestPyPI ONLY, at the
    exact ``==${VERSION}``, so the artifact under test provably came from TestPyPI.
  * **Phase 2 (resolution)** -- ``pip install`` the LOCAL wheel (optionally with
    extras) against production PyPI ONLY. No ``--no-deps``, so extras/dependency
    resolution is genuinely exercised; single index, so nothing can be confused.

This unittest:
  1. Structurally pins both phases: the download phase's TestPyPI-only index +
     ``--no-deps`` + exact ``==${VERSION}``, the three install phases' PyPI-only index
     + local-wheel target + extras + absence of ``--no-deps``, the tomllib version read,
     TestPyPI upload ``skip-existing`` (PyPI stays strict), the ``pypi needs: testpypi``
     gate, and the ``v*`` release-tag guard.
  2. Enforces the anti-regression invariant: NO verify command may carry
     ``--extra-index-url``, and no single command may name both index URLs (the merged
     namespace). A synthetic-violation self-test proves that check actually bites.
  3. Extracts the verify shell and runs it hermetically with PATH stubs for
     ``sleep`` / ``mktemp`` / ``pip`` / ``python`` so a rewrite that drops a phase, swaps
     the index URLs, or stops walking extras fails in CI without hitting the network --
     including a negative arm proving the missing-wheel guard aborts before any install.

Assertions target *executable* lines only (comments are stripped), so the workflow may
document the merged-namespace rationale without tripping its own gate.

Neither the workflow YAML nor ``util/`` is pre-commit-lint-gated for these
properties, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_publish_testpypi_verify.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import re
import stat
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "publish.yml"
VERIFY_STEP_NAME = "Verify TestPyPI install"
TESTPYPI_INDEX = "https://test.pypi.org/simple/"
PYPI_INDEX = "https://pypi.org/simple/"

# Rehearsal version + the wheel the download phase is contracted to produce.
REHEARSAL_VERSION = "9.9.9"
WHEEL_TEMPLATE = "juniper_ml-{version}-py3-none-any.whl"

# Light extras exercised at publish time (no torch). Order is part of the contract
# (bare first, then clients, then tools) so a truncated verify cannot silently ship.
EXPECTED_INSTALL_EXTRAS = ("", "[clients]", "[tools]")


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _verify_step_run(doc: dict) -> str:
    steps = (doc.get("jobs") or {}).get("testpypi", {}).get("steps") or []
    step = next((s for s in steps if s.get("name") == VERIFY_STEP_NAME), None)
    if step is None or "run" not in step:
        raise unittest.SkipTest(f"could not locate {VERIFY_STEP_NAME!r} in {WORKFLOW_NAME}")
    return step["run"]


def _command_lines(script: str) -> list[str]:
    """Executable lines of a shell step: comments and blanks stripped.

    The workflow documents the dependency-confusion rationale in comments that
    necessarily name ``--extra-index-url``; the contract is about what actually RUNS.
    """
    return [ln.strip() for ln in script.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def _merges_index_namespaces(line: str) -> bool:
    """True when ONE command names both index URLs -- the merged-namespace form.

    Compares full index URLs, never bare hosts: ``test.pypi.org`` contains ``pypi.org``
    as a substring, so a host-level check would report a false positive on every
    TestPyPI-only command.
    """
    return TESTPYPI_INDEX in line and PYPI_INDEX in line


def _pip_command_lines(script: str, subcommand: str) -> list[str]:
    return [ln for ln in _command_lines(script) if re.match(rf"^pip\s+{subcommand}\b", ln)]


class PublishTestPyPIVerifyStructuralTest(unittest.TestCase):
    """Pin publish.yml verify wiring so a casual edit cannot drop a phase or merge indexes."""

    repo_root: Path
    workflow_path: Path
    raw: str
    doc: dict
    script: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.script = _verify_step_run(cls.doc)

    def test_jobs_present(self) -> None:
        jobs = self.doc.get("jobs") or {}
        for name in ("build", "testpypi", "pypi"):
            with self.subTest(job=name):
                self.assertIn(name, jobs)

    def test_build_tag_guard_rejects_shared_package_releases(self) -> None:
        # Meta publish must NOT fire for juniper-<pkg>-v* shared/sub-package Releases.
        build_if = str(self.doc["jobs"]["build"].get("if") or "")
        self.assertIn("workflow_dispatch", build_if)
        self.assertIn("startsWith(github.event.release.tag_name, 'v')", build_if)

    def test_pypi_needs_testpypi(self) -> None:
        needs = self.doc["jobs"]["pypi"].get("needs")
        needs = [needs] if isinstance(needs, str) else (needs or [])
        self.assertIn("testpypi", needs, "PyPI publish must wait on TestPyPI verify (Gate 1).")

    def test_testpypi_needs_build(self) -> None:
        needs = self.doc["jobs"]["testpypi"].get("needs")
        needs = [needs] if isinstance(needs, str) else (needs or [])
        self.assertIn("build", needs)

    def test_verify_reads_version_from_pyproject_tomllib(self) -> None:
        self.assertIn("tomllib", self.script)
        self.assertIn("pyproject.toml", self.script)
        self.assertIn("['project']['version']", self.script)

    # ── Phase 1: artifact provenance ────────────────────────────────────────────────
    def test_download_phase_is_testpypi_only_at_exact_version(self) -> None:
        downloads = _pip_command_lines(self.script, "download")
        self.assertEqual(len(downloads), 1, f"expected exactly one `pip download` provenance phase, got {downloads}")
        line = downloads[0]
        self.assertIn("--no-deps", line, "provenance phase must be --no-deps (it resolves nothing)")
        self.assertIn(f"--index-url {TESTPYPI_INDEX}", line)
        self.assertNotIn(PYPI_INDEX, line, "the artifact MUST come from TestPyPI only")
        self.assertIn('"juniper-ml==${VERSION}"', line, "provenance phase must pin the exact built version")
        self.assertIn("--dest", line)

    def test_download_phase_precedes_every_install(self) -> None:
        lines = _command_lines(self.script)
        dl = next(i for i, ln in enumerate(lines) if re.match(r"^pip\s+download\b", ln))
        first_install = next(i for i, ln in enumerate(lines) if re.match(r"^pip\s+install\b", ln))
        self.assertLess(dl, first_install, "download the artifact before installing it")

    def test_wheel_path_is_version_pinned_and_guarded(self) -> None:
        # The install target must be the exact expected wheel, and a missing wheel must
        # abort loudly rather than hand a bogus path to pip.
        self.assertIn(WHEEL_TEMPLATE.format(version="${VERSION}"), self.script)
        self.assertIn('if [ ! -f "${WHEEL}" ]', self.script)
        self.assertIn("exit 1", self.script)

    # ── Phase 2: dependency resolution from ONE index ───────────────────────────────
    def test_install_phase_uses_pypi_index_only_and_local_wheel(self) -> None:
        installs = _pip_command_lines(self.script, "install")
        self.assertEqual(len(installs), 3, f"expected exactly 3 install phases (bare/[clients]/[tools]), got {installs}")
        for line in installs:
            with self.subTest(line=line):
                self.assertIn(f"--index-url {PYPI_INDEX}", line, "deps must resolve from production PyPI")
                self.assertNotIn(TESTPYPI_INDEX, line, "install phase must not touch TestPyPI")
                self.assertIn("${WHEEL}", line, "install target must be the locally downloaded TestPyPI wheel")
                self.assertNotIn("--no-deps", line, "extras/dependency resolution must be genuinely exercised")

    def test_install_phases_cover_bare_then_clients_then_tools(self) -> None:
        # Bare -> [clients] -> [tools]. A missing extras step is the exact ship-silent class.
        installs = _pip_command_lines(self.script, "install")
        for line, extra in zip(installs, EXPECTED_INSTALL_EXTRAS):
            with self.subTest(extra=extra or "<bare>"):
                self.assertTrue(
                    line.endswith(f'"${{WHEEL}}{extra}"'),
                    f'expected install spec ending in "${{WHEEL}}{extra}", got: {line}',
                )

    # ── Anti-regression: the merged namespace must never come back ──────────────────
    def test_no_verify_command_uses_extra_index_url(self) -> None:
        offenders = [ln for ln in _command_lines(self.script) if "--extra-index-url" in ln]
        self.assertEqual(
            offenders,
            [],
            "--extra-index-url reintroduces the merged index namespace that let a TestPyPI " "squatter (fastapi 1.0) outrank production fastapi 0.141.1 and kill the v0.7.0 " f"verify (run 31281873275). Offending command(s): {offenders}",
        )

    def test_no_verify_command_merges_both_index_namespaces(self) -> None:
        offenders = [ln for ln in _command_lines(self.script) if _merges_index_namespaces(ln)]
        self.assertEqual(
            offenders,
            [],
            "a single pip command names BOTH TestPyPI and production PyPI. pip has no index " "priority -- it picks the highest version across the merged namespace, so a " f"TestPyPI squatter wins. Split into download-then-install phases. Offenders: {offenders}",
        )

    def test_verify_does_not_install_heavy_extras(self) -> None:
        # [worker]/[servers]/[all]/[recurrence] pull torch / multi-GB; keep publish verify light.
        for heavy in ("[worker]", "[servers]", "[all]", "[recurrence]"):
            with self.subTest(extra=heavy):
                self.assertNotIn(f"${{WHEEL}}{heavy}", self.script)
                self.assertNotIn(f"juniper-ml{heavy}", self.script)

    def test_verify_imports_clients_and_tools_surfaces(self) -> None:
        self.assertIn("import juniper_data_client, juniper_cascor_client", self.script)
        self.assertIn("import juniper_ci_tools, juniper_doc_tools, juniper_observability", self.script)
        self.assertIn("importlib.metadata", self.script)

    def test_testpypi_environment_and_oidc(self) -> None:
        """Environments are declared, and OIDC is scoped to the publish jobs only.

        P4 (juniper-ml#357) moved ``id-token: write`` off the workflow block and
        onto the two publish jobs.  The build job compiles the tree and must not
        be able to mint a PyPI credential; job-level ``permissions`` REPLACE the
        workflow block rather than merging with it, so each publish job restates
        ``contents: read`` for its checkout.
        """
        self.assertEqual(self.doc["jobs"]["testpypi"].get("environment"), "testpypi")
        self.assertEqual(self.doc["jobs"]["pypi"].get("environment"), "pypi")

        self.assertEqual(self.doc.get("permissions"), {"contents": "read"}, "workflow-level permissions must NOT grant id-token; scope it to the publish jobs")

        for job in ("testpypi", "pypi"):
            with self.subTest(job=job):
                self.assertEqual(self.doc["jobs"][job].get("permissions"), {"id-token": "write", "contents": "read"})

        self.assertNotIn("permissions", self.doc["jobs"]["build"], "the build job must not be granted OIDC minting rights")

    def test_build_asserts_release_tag_matches_built_version(self) -> None:
        """P3: the build job proves it is building a tag whose version it actually built."""
        steps = self.doc["jobs"]["build"]["steps"]
        run_bodies = "\n".join(str(s.get("run", "")) for s in steps)
        self.assertIn("util/assert_release_tag.bash", run_bodies)
        self.assertIn("--expect-prefix v", run_bodies)
        # `github.ref` (fully-formed, documented as refs/tags/<tag> for a release
        # event) rather than `github.ref_name` -- the script keys on the
        # `refs/tags/` prefix, so a bare name would be refused.
        self.assertIn("github.ref }}", run_bodies, "the check must be fed the real github.ref, not a hardcoded value")
        self.assertNotIn("github.ref_name", run_bodies)

    def test_testpypi_upload_skips_existing_but_pypi_stays_strict(self) -> None:
        # A re-cut Release republishes a version TestPyPI already holds (immutable upload).
        # TestPyPI tolerates it; production PyPI must NOT silently swallow a duplicate.
        tp_steps = self.doc["jobs"]["testpypi"]["steps"]
        tp_pub = next(s for s in tp_steps if str(s.get("uses", "")).startswith("pypa/gh-action-pypi-publish"))
        self.assertIs(
            (tp_pub.get("with") or {}).get("skip-existing"),
            True,
            "TestPyPI upload must set skip-existing: true so a Release recut is a no-op, not a 400.",
        )
        self.assertEqual((tp_pub.get("with") or {}).get("repository-url"), "https://test.pypi.org/legacy/")

        py_steps = self.doc["jobs"]["pypi"]["steps"]
        py_pub = next(s for s in py_steps if str(s.get("uses", "")).startswith("pypa/gh-action-pypi-publish"))
        self.assertNotIn(
            "skip-existing",
            (py_pub.get("with") or {}),
            "production PyPI upload must stay STRICT -- a duplicate upload is a real error.",
        )


class MergedNamespaceDetectorTest(unittest.TestCase):
    """Synthetic-violation self-test: prove the merged-namespace check actually bites."""

    def test_detects_the_pre_amendment_merged_form(self) -> None:
        regressed = f'pip install --index-url {TESTPYPI_INDEX} --extra-index-url {PYPI_INDEX} "juniper-ml[clients]==${{VERSION}}"'
        self.assertTrue(
            _merges_index_namespaces(regressed),
            "the exact pre-2026-08-08 form that failed run 31281873275 must be detected",
        )

    def test_single_index_forms_are_clean(self) -> None:
        for line in (
            f'pip download --no-deps --index-url {TESTPYPI_INDEX} --dest "${{D}}" "juniper-ml==${{VERSION}}"',
            f'pip install --index-url {PYPI_INDEX} "${{WHEEL}}[tools]"',
        ):
            with self.subTest(line=line):
                self.assertFalse(_merges_index_namespaces(line))

    def test_testpypi_only_line_is_not_a_false_positive(self) -> None:
        # Guards the substring trap: "test.pypi.org" contains "pypi.org".
        self.assertFalse(_merges_index_namespaces(f"pip download --index-url {TESTPYPI_INDEX} juniper-ml"))

    def test_command_lines_strips_comments(self) -> None:
        script = "# pip install --extra-index-url https://pypi.org/simple/ foo\npip install bar\n\n   # trailing note\n"
        self.assertEqual(_command_lines(script), ["pip install bar"])


class PublishTestPyPIVerifyRehearsalTest(unittest.TestCase):
    """Run the extracted verify shell with PATH stubs — prove the ACTUAL two phases fire."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        cls.script = _verify_step_run(yaml.safe_load(wf.read_text(encoding="utf-8")))

    @staticmethod
    def _write_exec(path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def _write_stubs(self, bindir: Path, pip_log: Path, mktemp_dir: Path, *, version: str, create_wheel: bool) -> None:
        self._write_exec(bindir / "sleep", "#!/bin/bash\nexit 0\n")

        # mktemp stub: deterministic dir INSIDE the test tree (keeps the rehearsal hermetic).
        self._write_exec(bindir / "mktemp", "#!/bin/bash\n" f'mkdir -p "{mktemp_dir}"\n' f'printf "%s\\n" "{mktemp_dir}"\n' "exit 0\n")

        # pip stub: logs every invocation; on `download` optionally materializes the wheel
        # the workflow expects, so the download -> install handoff is genuinely exercised.
        wheel_name = WHEEL_TEMPLATE.format(version=version)
        make_wheel = "if [[ \"$1\" == 'download' ]]; then\n" '  dest=""; prev=""\n' '  for a in "$@"; do\n' '    if [[ "$prev" == "--dest" ]]; then dest="$a"; fi\n' '    prev="$a"\n' "  done\n" f'  if [[ -n "$dest" && "{int(create_wheel)}" == "1" ]]; then\n' '    mkdir -p "$dest"\n' f'    : > "$dest/{wheel_name}"\n' "  fi\n" "fi\n"
        self._write_exec(bindir / "pip", "#!/bin/bash\n" f'printf "%s\\n" "$*" >> "{pip_log}"\n' f"{make_wheel}" "exit 0\n")

        # python stub: tomllib version probe prints VERSION; import probes succeed.
        self._write_exec(
            bindir / "python",
            "#!/bin/bash\n" 'args="$*"\n' 'if [[ "$args" == *tomllib* ]]; then\n' f'  echo "{version}"\n' "  exit 0\n" "fi\n" "exit 0\n",
        )

    def _run_verify(self, *, create_wheel: bool = True) -> tuple[int, list[str], str]:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            bindir = tdp / "bin"
            bindir.mkdir()
            pip_log = tdp / "pip.log"
            pip_log.write_text("", encoding="utf-8")
            # Minimal pyproject so a non-stubbed python path still has a file (defensive).
            (tdp / "pyproject.toml").write_text('[project]\nname = "juniper-ml"\nversion = "9.9.9"\n', encoding="utf-8")
            self._write_stubs(bindir, pip_log, tdp / "dl", version=REHEARSAL_VERSION, create_wheel=create_wheel)
            script_path = tdp / "verify.sh"
            script_path.write_text(self.script, encoding="utf-8")
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            # Keep cwd at the temp tree (script opens pyproject.toml relative to CWD).
            proc = subprocess.run(  # nosec B603,B607 - workflow's own shell, fixed argv
                ["bash", str(script_path)],
                cwd=str(tdp),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            lines = [ln for ln in pip_log.read_text(encoding="utf-8").splitlines() if ln.strip()]
            return proc.returncode, lines, proc.stdout + proc.stderr

    def _run_verify_ok(self) -> list[str]:
        rc, lines, out = self._run_verify()
        self.assertEqual(rc, 0, f"verify shell exited {rc}\n{out}")
        return lines

    def test_download_then_three_installs_fire(self) -> None:
        lines = self._run_verify_ok()
        self.assertEqual(len(lines), 4, f"expected 1 download + 3 installs, got {len(lines)}: {lines}")
        self.assertTrue(lines[0].startswith("download "), f"first pip call must be the provenance download: {lines[0]}")
        for line in lines[1:]:
            self.assertTrue(line.startswith("install "), f"expected an install call, got: {line}")

    def test_download_phase_hits_testpypi_only_with_exact_version(self) -> None:
        line = self._run_verify_ok()[0]
        self.assertIn("--no-deps", line)
        self.assertIn(f"--index-url {TESTPYPI_INDEX}", line)
        self.assertIn(f"juniper-ml=={REHEARSAL_VERSION}", line)
        self.assertNotIn(PYPI_INDEX, line)

    def test_install_phases_hit_pypi_only_with_local_wheel_and_extras(self) -> None:
        lines = self._run_verify_ok()[1:]
        wheel_name = WHEEL_TEMPLATE.format(version=REHEARSAL_VERSION)
        for line, extra in zip(lines, EXPECTED_INSTALL_EXTRAS):
            with self.subTest(extra=extra or "<bare>"):
                self.assertIn(f"--index-url {PYPI_INDEX}", line)
                self.assertNotIn(TESTPYPI_INDEX, line)
                self.assertNotIn("--no-deps", line)
                self.assertNotIn("--extra-index-url", line)
                self.assertTrue(line.endswith(f"{wheel_name}{extra}"), f"expected spec ending {wheel_name}{extra}, got: {line}")

    def test_no_rehearsed_command_merges_index_namespaces(self) -> None:
        # The runtime counterpart of the structural anti-regression gate.
        offenders = [ln for ln in self._run_verify_ok() if _merges_index_namespaces(ln)]
        self.assertEqual(offenders, [], f"pip invoked with a merged index namespace: {offenders}")

    def test_clients_install_precedes_tools(self) -> None:
        lines = self._run_verify_ok()
        clients_i = next(i for i, ln in enumerate(lines) if ln.endswith("[clients]"))
        tools_i = next(i for i, ln in enumerate(lines) if ln.endswith("[tools]"))
        self.assertLess(clients_i, tools_i)

    def test_missing_wheel_aborts_before_any_install(self) -> None:
        # Negative arm: if TestPyPI does not serve the expected wheel, the guard must fail
        # the step rather than hand pip a nonexistent path (which would resolve juniper-ml
        # from PyPI and silently verify the WRONG artifact).
        rc, lines, out = self._run_verify(create_wheel=False)
        self.assertNotEqual(rc, 0, "missing TestPyPI wheel must fail the verify step")
        self.assertEqual(len(lines), 1, f"no install may run after a failed download: {lines}")
        self.assertIn("::error::", out)

    def test_sleep_is_invoked_but_stubbed_not_blocking(self) -> None:
        """The index-lag buffer is a BOUNDED POLL, not a fixed sleep (2026-08-24).

        The contract this pins is unchanged in substance -- TestPyPI's index is
        CDN-fronted and lags an upload by ~5-30s, so the first fetch can 404 and the
        verify must absorb that. What changed is the shape. It was an unconditional
        `sleep 30`: 77% of a measured 39s step, paid on EVERY publish even when the
        index was already warm, and still a coin-flip if propagation ran long. A
        retry around the fetch is better in both directions.

        Asserted here: no unconditional long sleep survives, and the buffer is a
        retry loop whose sleep is SHORT (a poll interval, not a fixed wait).
        """
        self.assertIsNone(
            re.search(r"^\s*sleep\s+30\s*$", self.script, re.MULTILINE),
            "the unconditional `sleep 30` should be gone -- it is now a bounded poll",
        )
        sleeps = re.findall(r"^\s*sleep\s+(\d+)\s*$", self.script, re.MULTILINE)
        self.assertTrue(sleeps, "verify shell must retain an index-lag buffer of some form")
        for value in sleeps:
            self.assertLessEqual(
                int(value),
                10,
                msg=f"sleep {value} looks like a fixed wait, not a poll interval; sleeps={sleeps}",
            )
        # The buffer must be a RETRY, i.e. the fetch is reachable more than once.
        # re.MULTILINE is load-bearing: assertRegex uses a bare re.search, so `^`
        # would anchor at the start of the whole script rather than each line.
        self.assertIsNotNone(
            re.search(r"^\s*for\s+attempt\s+in\b", self.script, re.MULTILINE),
            "expected a bounded retry loop around the fetch",
        )
        # A failure to ever fetch must be a real error, never a silent fall-through
        # into the install phases with an empty download dir.
        self.assertIn("never served", self.script)
        # If sleep were not stubbed this would hang; finishing quickly is the proof.
        # Still exactly 4 pip invocations: the stub succeeds on the first attempt, so
        # the retry adds nothing in the happy path.
        self.assertEqual(len(self._run_verify_ok()), 4)


if __name__ == "__main__":
    unittest.main()
