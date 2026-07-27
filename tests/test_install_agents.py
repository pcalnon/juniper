"""Tests for util/install_agents.bash (custom-agent suite PR 6a).

The mirror symlinks `.claude/{agents,skills}/*` into `~/.claude` so the suite is available
cross-repo (design D-6). These tests drive the script against a SYNTHETIC source repo and a
throwaway target dir (via the `JUNIPER_ML_REPO_ROOT` / `JUNIPER_CLAUDE_HOME` overrides) and
assert it is idempotent, reversible, `--dry-run`-safe, never clobbers or removes a file
it does not own, and retargets stale symlinks (old-worktree repair via ``ln -sfn``).

Location-agnostic: discovers the repo root by walking up for `.github/workflows/`.
"""

from __future__ import annotations

import os
import subprocess
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
_SCRIPT = _REPO_ROOT / "util" / "install_agents.bash"


def _make_source(root: Path) -> None:
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "skills" / "sample-skill").mkdir(parents=True)
    (root / ".claude" / "agents" / "sample-agent.md").write_text("---\nname: sample-agent\n---\nbody\n", encoding="utf-8")
    (root / ".claude" / "skills" / "sample-skill" / "SKILL.md").write_text("---\nname: sample-skill\n---\nbody\n", encoding="utf-8")


class InstallAgentsTest(unittest.TestCase):
    def setUp(self):
        self._src_tmp = tempfile.TemporaryDirectory()
        self._tgt_tmp = tempfile.TemporaryDirectory()
        self.src = Path(self._src_tmp.name)
        self.tgt = Path(self._tgt_tmp.name)
        _make_source(self.src)

    def tearDown(self):
        self._src_tmp.cleanup()
        self._tgt_tmp.cleanup()

    def _run(self, *args):
        env = RedactedEnv(os.environ, JUNIPER_ML_REPO_ROOT=str(self.src), JUNIPER_CLAUDE_HOME=str(self.tgt))
        return subprocess.run(["bash", str(_SCRIPT), *args], capture_output=True, text=True, check=False, timeout=60, env=env)

    def test_script_exists_and_parses(self):
        self.assertTrue(_SCRIPT.exists(), f"missing {_SCRIPT}")
        proc = subprocess.run(["bash", "-n", str(_SCRIPT)], capture_output=True, text=True, check=False, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_install_creates_symlinks(self):
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        agent_link = self.tgt / "agents" / "sample-agent.md"
        skill_link = self.tgt / "skills" / "sample-skill"
        self.assertTrue(agent_link.is_symlink())
        self.assertTrue(skill_link.is_symlink())
        self.assertEqual(os.readlink(agent_link), str(self.src / ".claude" / "agents" / "sample-agent.md"))
        self.assertEqual(os.readlink(skill_link), str(self.src / ".claude" / "skills" / "sample-skill"))

    def test_idempotent(self):
        self.assertEqual(self._run().returncode, 0)
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("already linked", proc.stdout)
        self.assertTrue((self.tgt / "agents" / "sample-agent.md").is_symlink())

    def test_dry_run_touches_nothing(self):
        proc = self._run("--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.tgt / "agents").exists(), "dry-run must not create anything")

    def test_reverse_removes_owned_links(self):
        self._run()
        self.assertTrue((self.tgt / "agents" / "sample-agent.md").is_symlink())
        proc = self._run("--reverse")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.tgt / "agents" / "sample-agent.md").exists())
        self.assertFalse((self.tgt / "skills" / "sample-skill").exists())

    def test_reverse_leaves_foreign_files(self):
        (self.tgt / "agents").mkdir(parents=True)
        foreign = self.tgt / "agents" / "user-own.md"
        foreign.write_text("mine\n", encoding="utf-8")
        self._run()
        self._run("--reverse")
        self.assertTrue(foreign.exists(), "reverse must not remove a file it does not own")

    def test_install_refuses_to_clobber_nonsymlink(self):
        (self.tgt / "agents").mkdir(parents=True)
        clash = self.tgt / "agents" / "sample-agent.md"
        clash.write_text("preexisting\n", encoding="utf-8")
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(clash.is_symlink())
        self.assertEqual(clash.read_text(encoding="utf-8"), "preexisting\n")
        self.assertIn("refusing to clobber", proc.stdout)

    def test_install_relinks_stale_symlink(self):
        """Stale symlink (e.g. old worktree) must be retargeted with ln -sfn.

        After a checkout move, ~/.claude agents/skills often still point at the
        previous path. The relink arm is the repair path — a regression that
        treats any existing symlink as already-ok leaves the suite pointing at
        deleted worktrees.
        """
        (self.tgt / "agents").mkdir(parents=True)
        (self.tgt / "skills").mkdir(parents=True)
        stale_agent_target = self.tgt / "stale-elsewhere" / "sample-agent.md"
        stale_skill_target = self.tgt / "stale-elsewhere" / "sample-skill"
        stale_agent_target.parent.mkdir(parents=True)
        stale_agent_target.write_text("stale\n", encoding="utf-8")
        stale_skill_target.mkdir()
        agent_link = self.tgt / "agents" / "sample-agent.md"
        skill_link = self.tgt / "skills" / "sample-skill"
        agent_link.symlink_to(stale_agent_target)
        skill_link.symlink_to(stale_skill_target)

        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("relink:", proc.stdout)
        self.assertTrue(agent_link.is_symlink())
        self.assertTrue(skill_link.is_symlink())
        expected_agent = str(self.src / ".claude" / "agents" / "sample-agent.md")
        expected_skill = str(self.src / ".claude" / "skills" / "sample-skill")
        self.assertEqual(os.readlink(agent_link), expected_agent)
        self.assertEqual(os.readlink(skill_link), expected_skill)

    def test_dry_run_relink_leaves_stale_symlink(self):
        """``--dry-run`` must log relink intent but not rewrite the stale link."""
        (self.tgt / "agents").mkdir(parents=True)
        stale = self.tgt / "old-worktree" / "sample-agent.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale\n", encoding="utf-8")
        agent_link = self.tgt / "agents" / "sample-agent.md"
        agent_link.symlink_to(stale)

        proc = self._run("--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("relink:", proc.stdout)
        self.assertEqual(os.readlink(agent_link), str(stale))

    def test_reverse_skips_foreign_symlink(self):
        """``--reverse`` must not remove a symlink that does not point into this repo."""
        (self.tgt / "agents").mkdir(parents=True)
        foreign_target = self.tgt / "other-repo" / "foreign-agent.md"
        foreign_target.parent.mkdir(parents=True)
        foreign_target.write_text("foreign\n", encoding="utf-8")
        foreign_link = self.tgt / "agents" / "foreign-agent.md"
        foreign_link.symlink_to(foreign_target)

        self._run()  # also installs owned links
        proc = self._run("--reverse")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("skip (not ours)", proc.stdout)
        self.assertTrue(foreign_link.is_symlink(), "reverse must leave foreign symlinks")
        self.assertEqual(os.readlink(foreign_link), str(foreign_target))
        self.assertFalse((self.tgt / "agents" / "sample-agent.md").exists())


if __name__ == "__main__":
    unittest.main()
