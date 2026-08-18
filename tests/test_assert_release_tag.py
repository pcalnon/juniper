"""Behavioural tests for ``util/assert_release_tag.bash``.

The script is the in-workflow half of the publish-path hardening (design §6
Option B, juniper-ml#357 / #358): it asserts a publish run is building a **tag**,
that the tag carries this package's prefix, and that the tag's version matches
the version of the wheel that was actually built.

Reading the built version from the **wheel filename** rather than from
``pyproject.toml`` is the load-bearing design choice -- it is the version that
will really be uploaded, and it behaves identically for static and dynamic
version backends.  The tests below pin that, plus the PEP 440 normalization that
lets a ``1.0.0-rc1`` tag agree with a ``1.0.0rc1`` wheel.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the
gate for the script.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "util" / "assert_release_tag.bash").is_file():
            return candidate
    return here.parents[1]


SCRIPT = _repo_root() / "util" / "assert_release_tag.bash"


def run_assert(*, ref: str, dist_dir: str, expect_prefix: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--ref",
            ref,
            "--dist-dir",
            dist_dir,
            "--expect-prefix",
            expect_prefix,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


class AssertReleaseTagTest(unittest.TestCase):
    """Drive the script against synthetic dist directories."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dist = Path(self._tmp.name) / "dist"
        self.dist.mkdir()
        self.addCleanup(self._tmp.cleanup)

    def _wheel(self, name: str) -> None:
        (self.dist / name).write_text("", encoding="utf-8")

    # ── happy paths ──────────────────────────────────────────────────────────

    def test_meta_tag_matches_built_version(self) -> None:
        self._wheel("juniper_ml-0.7.1-py3-none-any.whl")
        proc = run_assert(ref="refs/tags/v0.7.1", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Release tag check passed", proc.stdout)

    def test_subpackage_tag_matches_built_version(self) -> None:
        self._wheel("juniper_ci_tools-0.8.0-py3-none-any.whl")
        proc = run_assert(ref="refs/tags/juniper-ci-tools-v0.8.0", dist_dir=str(self.dist), expect_prefix="juniper-ci-tools-v")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_prerelease_separator_is_normalized(self) -> None:
        """A `1.0.0-rc1` tag must agree with the PEP 440 `1.0.0rc1` wheel."""
        self._wheel("juniper_ml-1.0.0rc1-py3-none-any.whl")
        proc = run_assert(ref="refs/tags/v1.0.0-rc1", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_alpha_version_matches(self) -> None:
        self._wheel("juniper_observability-0.1.0a2-py3-none-any.whl")
        proc = run_assert(ref="refs/tags/juniper-observability-v0.1.0a2", dist_dir=str(self.dist), expect_prefix="juniper-observability-v")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    # ── the assertions that matter ───────────────────────────────────────────

    def test_branch_ref_is_refused(self) -> None:
        """The #357 case: a publish dispatched from a branch."""
        self._wheel("juniper_ml-0.7.1-py3-none-any.whl")
        proc = run_assert(ref="refs/heads/main", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("must run from a tag", proc.stderr)

    def test_bare_tag_name_without_refs_prefix_is_refused(self) -> None:
        """Fail closed on a short ref.

        The script keys on the fully-formed ``refs/tags/`` prefix precisely so a
        bare name cannot be mistaken for a verified tag. If a caller ever passes
        ``github.ref_name`` instead of ``github.ref``, this must refuse rather
        than silently accept an unverified string.
        """
        self._wheel("juniper_ml-0.7.1-py3-none-any.whl")
        proc = run_assert(ref="v0.7.1", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("must run from a tag", proc.stderr)

    def test_refs_heads_lookalike_is_refused(self) -> None:
        """A branch literally named like a tag must still be refused."""
        self._wheel("juniper_ml-0.7.1-py3-none-any.whl")
        proc = run_assert(ref="refs/heads/v0.7.1", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("must run from a tag", proc.stderr)

    def test_version_mismatch_is_refused(self) -> None:
        """The other #357 ask: tag says 0.7.2, tree still builds 0.7.1."""
        self._wheel("juniper_ml-0.7.1-py3-none-any.whl")
        proc = run_assert(ref="refs/tags/v0.7.2", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("tag/version mismatch", proc.stderr)
        self.assertIn("0.7.2", proc.stderr)
        self.assertIn("0.7.1", proc.stderr)

    def test_wrong_package_prefix_is_refused(self) -> None:
        """A sibling package's release tag must not publish this package."""
        self._wheel("juniper_ci_tools-0.8.0-py3-none-any.whl")
        proc = run_assert(ref="refs/tags/juniper-doc-tools-v0.8.0", dist_dir=str(self.dist), expect_prefix="juniper-ci-tools-v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("expected prefix", proc.stderr)

    def test_missing_dist_dir_is_refused(self) -> None:
        proc = run_assert(ref="refs/tags/v0.7.1", dist_dir=str(self.dist / "nope"), expect_prefix="v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not exist", proc.stderr)

    def test_no_wheel_is_refused(self) -> None:
        """An sdist-only dist dir cannot prove the built version."""
        (self.dist / "juniper_ml-0.7.1.tar.gz").write_text("", encoding="utf-8")
        proc = run_assert(ref="refs/tags/v0.7.1", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no wheel found", proc.stderr)

    def test_tag_with_no_version_is_refused(self) -> None:
        self._wheel("juniper_ml-0.7.1-py3-none-any.whl")
        proc = run_assert(ref="refs/tags/v", dist_dir=str(self.dist), expect_prefix="v")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no version", proc.stderr)

    def test_misuse_exits_two(self) -> None:
        proc = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(proc.returncode, 2)


class WorkflowWiringTest(unittest.TestCase):
    """Every publisher must actually call the script, or it protects nothing."""

    EXPECTED_PREFIXES = {
        "publish.yml": "v",
        "publish-ci-tools.yml": "juniper-ci-tools-v",
        "publish-config-tools.yml": "juniper-config-tools-v",
        "publish-doc-tools.yml": "juniper-doc-tools-v",
        "publish-model-core.yml": "juniper-model-core-v",
        "publish-observability.yml": "juniper-observability-v",
        "publish-service-core.yml": "juniper-service-core-v",
    }

    def test_every_publisher_invokes_the_check(self) -> None:
        workflows = _repo_root() / ".github" / "workflows"
        missing = []
        for name, prefix in self.EXPECTED_PREFIXES.items():
            path = workflows / name
            if not path.is_file():
                missing.append(f"{name}: workflow file not found")
                continue
            text = path.read_text(encoding="utf-8")
            if "util/assert_release_tag.bash" not in text:
                missing.append(f"{name}: does not invoke util/assert_release_tag.bash")
            elif f"--expect-prefix {prefix}" not in text and f"--expect-prefix '{prefix}'" not in text:
                missing.append(f"{name}: does not pass --expect-prefix {prefix}")
        self.assertEqual(missing, [], "\n  ".join(missing))

    def test_id_token_is_not_workflow_level(self) -> None:
        """P4: OIDC minting must be scoped to the publish jobs, not the whole workflow."""
        workflows = _repo_root() / ".github" / "workflows"
        offenders = []
        for name in self.EXPECTED_PREFIXES:
            path = workflows / name
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                # A workflow-level permissions key sits at exactly two spaces of
                # indentation; a job-level one is nested deeper.
                if line.startswith("  id-token:"):
                    offenders.append(f"{name}: workflow-level 'id-token' -- scope it to the publish jobs")
                    break
        self.assertEqual(offenders, [], "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main(verbosity=2)
