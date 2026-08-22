#!/usr/bin/env python3
"""Clean up Claude Code session worktrees in ``juniper-ml/.claude/worktrees/``.

Claude Code creates a fresh git worktree per session under
``.claude/worktrees/<session-name>/`` (each tied to a ``worktree-<name>``
branch). After the work is merged, those worktrees and branches accumulate
indefinitely if nothing prunes them. This script applies the V2 cleanup
procedure to every session worktree at once.

A worktree is removed iff:

1. It is **not locked**. Claude Code locks a live session's worktree, naming
   the session and pid in the lock reason, so git's lock flag is this fleet's
   liveness signal.
2. Its working tree is clean (no uncommitted or untracked changes).
3. Its branch tip is reachable from ``origin/main`` (the work was merged),
   OR a MERGED pull request exists for the branch on GitHub.

Worktrees that fail any gate are left alone and reported. The current
process's CWD is also always skipped — git refuses to remove the active
worktree of a running process.

Gate 1 was missing until 2026-08-21: this script read merge state and
cleanliness but never the lock. ``git worktree remove`` with a single
``--force`` does refuse a locked tree, so a live run could never actually
delete a session — the damage was to the PLAN. ``--dry-run`` printed
"WOULD REMOVE" for worktrees a real run would refuse, and an operator
reconciling that contradiction reaches for ``-f -f`` or unlocks by hand,
either of which *does* destroy live work. The removal call no longer passes
``--force`` at all: dirty and locked are both refused above it, so force
could only mask a surprise git is right to raise.

When a worktree is removed, the script also deletes the corresponding
local branch (force) and the matching branch on ``origin`` (best-effort —
GitHub's auto-delete-on-merge often beats the explicit push, in which case
the failure is silently treated as already-clean).

Usage::

    python scripts/cleanup_session_worktrees.py [--dry-run] [--root <path>]
                                                [--repo <path>] [--gh-repo <slug>]
                                                [--allow-cwd]

Project: Juniper
Sub-Project: juniper-ml
Application: JuniperMLToolingScripts
Author: Paul Calnon
Version: 0.1.0
License: MIT License
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

DEFAULT_REPO = Path("/home/pcalnon/Development/python/Juniper/juniper-ml")
DEFAULT_ROOT = DEFAULT_REPO / ".claude" / "worktrees"
DEFAULT_GH_REPO = "pcalnon/juniper-ml"


# ─── Result accounting ───────────────────────────────────────────────────────


@dataclass
class CleanupReport:
    removed: list[str] = field(default_factory=list)
    kept_dirty: list[str] = field(default_factory=list)
    kept_unmerged: list[str] = field(default_factory=list)
    kept_locked: list[str] = field(default_factory=list)
    skipped_self: list[str] = field(default_factory=list)
    skipped_remove_failed: list[str] = field(default_factory=list)

    def total(self) -> int:
        return sum(
            len(x)
            for x in (
                self.removed,
                self.kept_dirty,
                self.kept_unmerged,
                self.kept_locked,
                self.skipped_self,
                self.skipped_remove_failed,
            )
        )

    def summary_line(self) -> str:
        return f"Summary: removed={len(self.removed)} kept_dirty={len(self.kept_dirty)} " f"kept_unmerged={len(self.kept_unmerged)} kept_locked={len(self.kept_locked)} " f"skipped_self={len(self.skipped_self)} " f"failed={len(self.skipped_remove_failed)} (total={self.total()})"


# ─── Git helpers ─────────────────────────────────────────────────────────────


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def _branch_of(wt: Path) -> str:
    return _run(["git", "-C", str(wt), "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()


def _head_of(wt: Path) -> str:
    return _run(["git", "-C", str(wt), "rev-parse", "HEAD"]).stdout.strip()


def _is_dirty(wt: Path) -> bool:
    return bool(_run(["git", "-C", str(wt), "status", "--porcelain"]).stdout.strip())


def _is_ancestor(wt: Path, tip: str, ref: str) -> bool:
    return _run(["git", "-C", str(wt), "merge-base", "--is-ancestor", tip, ref]).returncode == 0


def _has_merged_pr(gh_repo: str, branch: str) -> bool:
    """Return True if at least one PR for ``branch`` is in the MERGED state.

    Requires the ``gh`` CLI to be authenticated. Failures are treated as
    "no merged PR" so the worktree is kept rather than wrongly removed.
    """
    out = _run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            gh_repo,
            "--head",
            branch,
            "--state",
            "all",
            "--json",
            "state,number",
            "--limit",
            "5",
        ]
    )
    if out.returncode != 0:
        return False
    try:
        prs = json.loads(out.stdout) if out.stdout.strip() else []
    except json.JSONDecodeError:
        return False
    return any(p.get("state") == "MERGED" for p in prs)


# ─── Cleanup ─────────────────────────────────────────────────────────────────


def _locked_worktrees(repo: Path) -> dict[Path, str]:
    """Map every LOCKED worktree path to its lock reason.

    Claude Code marks a live session's worktree by locking it, with the reason
    naming the session and pid -- so git's lock flag is the fleet's liveness
    signal, and this script previously never read it. ``git worktree remove``
    with a single ``--force`` does refuse a locked tree, so a live run could not
    actually delete one; the damage was to the PLAN. ``--dry-run`` reported
    "WOULD REMOVE" for trees a real run would refuse, which is how an operator
    ends up reaching for ``-f -f`` or unlocking by hand to make the tool agree
    with itself.

    Porcelain emits a bare ``locked`` line, or ``locked <reason>``.
    """
    out = _run(["git", "-C", str(repo), "worktree", "list", "--porcelain"]).stdout
    locked: dict[Path, str] = {}
    current: Path | None = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            current = Path(line[len("worktree ") :].strip())
        elif line.startswith("locked") and current is not None:
            reason = line[len("locked") :].strip()
            locked[current.resolve()] = reason or "(no reason given)"
    return locked


def _is_self_cwd(wt: Path) -> bool:
    """Return True iff ``wt`` is (or contains) the current working directory.

    Removing the active worktree of the running process leaves git in a
    confused state. ``Path.resolve`` on the cwd handles symlinks under
    ``.claude`` correctly.
    """
    cwd = Path.cwd().resolve()
    try:
        cwd.relative_to(wt.resolve())
        return True
    except ValueError:
        return False


def _remove_worktree(repo: Path, wt: Path, branch: str, dry_run: bool) -> tuple[bool, str]:
    """Remove a worktree and its associated local + remote branches.

    Returns ``(success, message)``. ``success`` is False only when the
    ``git worktree remove`` call itself fails — branch deletions are
    best-effort and surfaced in the message text.
    """
    if dry_run:
        return True, "DRY-RUN: would remove worktree + branches"

    # No --force. The caller has already refused dirty and locked worktrees, so
    # force can only mask a surprise git is right to raise -- and normalising it
    # here is the step before someone reaches for `-f -f`, which DOES delete a
    # live session's tree.
    r = _run(["git", "-C", str(repo), "worktree", "remove", str(wt)])
    if r.returncode != 0:
        return False, f"worktree remove failed: {r.stderr.strip()}"

    notes: list[str] = []
    rb = _run(["git", "-C", str(repo), "branch", "-D", branch])
    if rb.returncode == 0:
        notes.append("local-branch:deleted")
    else:
        notes.append(f"local-branch:{rb.stderr.strip().splitlines()[-1] if rb.stderr.strip() else 'no-op'}")

    rp = _run(["git", "-C", str(repo), "push", "origin", "--delete", branch])
    if rp.returncode == 0:
        notes.append("remote-branch:deleted")
    else:
        # GitHub's auto-delete-on-merge often beats us to the punch.
        last = rp.stderr.strip().splitlines()[-1] if rp.stderr.strip() else ""
        if "remote ref does not exist" in rp.stderr or "remote ref does not exist" in last:
            notes.append("remote-branch:already-gone")
        else:
            notes.append(f"remote-branch-failed: {last}")

    return True, ", ".join(notes)


def cleanup_session_worktrees(
    *,
    repo: Path,
    root: Path,
    gh_repo: str,
    dry_run: bool,
    allow_cwd: bool,
) -> CleanupReport:
    """Walk ``root`` and apply the cleanup policy to every session worktree."""
    if not root.is_dir():
        raise SystemExit(f"worktree root does not exist: {root}")

    report = CleanupReport()

    # Refresh remote tracking + prune so ``origin/main`` is current.
    _run(["git", "-C", str(repo), "fetch", "origin", "--prune", "--quiet"])
    main_tip = _run(["git", "-C", str(repo), "rev-parse", "origin/main"]).stdout.strip()
    if not main_tip:
        raise SystemExit(f"could not resolve origin/main in {repo}")

    # Read the lock table once, before any decision. A locked worktree is a
    # LIVE SESSION and is a hard stop -- ahead of dirty/merged, because merge
    # state says nothing about whether someone is working in there right now.
    locked = _locked_worktrees(repo)

    for wt in sorted(root.iterdir()):
        if not wt.is_dir() or not (wt / ".git").exists():
            continue
        if not allow_cwd and _is_self_cwd(wt):
            print(f"SKIP {wt.name}: current session cwd")
            report.skipped_self.append(wt.name)
            continue
        lock_reason = locked.get(wt.resolve())
        if lock_reason is not None:
            print(f"KEEP {wt.name}: LOCKED — {lock_reason}")
            report.kept_locked.append(wt.name)
            continue

        branch = _branch_of(wt)
        if not branch or branch in {"HEAD"}:
            # detached HEAD — treat as kept so a human can investigate
            print(f"KEEP {wt.name}: detached HEAD")
            report.kept_unmerged.append(wt.name)
            continue

        tip = _head_of(wt)
        dirty = _is_dirty(wt)
        in_main = bool(tip) and _is_ancestor(wt, tip, main_tip)
        merged_pr = False if in_main else _has_merged_pr(gh_repo, branch)

        if dirty:
            print(f"KEEP {wt.name} ({branch}): DIRTY")
            report.kept_dirty.append(wt.name)
            continue
        if not (in_main or merged_pr):
            print(f"KEEP {wt.name} ({branch}): unmerged, no merged PR")
            report.kept_unmerged.append(wt.name)
            continue

        ok, message = _remove_worktree(repo, wt, branch, dry_run=dry_run)
        if ok:
            verb = "WOULD REMOVE" if dry_run else "REMOVED"
            print(f"{verb} {wt.name} ({branch}): {message}")
            report.removed.append(wt.name)
        else:
            print(f"FAILED to remove {wt.name} ({branch}): {message}")
            report.skipped_remove_failed.append(wt.name)

    if not dry_run:
        _run(["git", "-C", str(repo), "worktree", "prune"])

    return report


# ─── CLI entry point ─────────────────────────────────────────────────────────


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="Path to the juniper-ml git repository")
    p.add_argument("--root", type=Path, default=None, help="Worktree root (default: <repo>/.claude/worktrees)")
    p.add_argument("--gh-repo", default=DEFAULT_GH_REPO, help="GitHub repo slug owner/name (default: pcalnon/juniper-ml)")
    p.add_argument("--dry-run", action="store_true", help="Audit only — do not remove worktrees or delete branches")
    p.add_argument(
        "--allow-cwd",
        action="store_true",
        help="DANGEROUS: allow removing the current process's worktree (will fail at git level)",
    )
    return p


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_argparser().parse_args(list(argv) if argv is not None else None)
    root = args.root or (args.repo / ".claude" / "worktrees")

    report = cleanup_session_worktrees(
        repo=args.repo,
        root=root,
        gh_repo=args.gh_repo,
        dry_run=args.dry_run,
        allow_cwd=args.allow_cwd,
    )

    print()
    print(report.summary_line())
    return 0 if not report.skipped_remove_failed else 1


if __name__ == "__main__":
    sys.exit(main())
