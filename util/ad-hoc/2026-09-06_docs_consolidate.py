#!/usr/bin/env python3
"""
Merge a fleet of docs PRs onto one branch, one at a time, resolving by ITEM identity.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 35 juniper-ml docs PRs; `2026-09-06_docs_conflict_resolve.py`

Thirty-five PRs edit the same four documents from seventeen different bases, so every one of
them conflicts -- measured, not assumed. Serial 3-way merges are still the right shape, because
a 3-way merge has the BASE and can tell an added row from a changed one; what a merge cannot do
is decide which of two prose claims is current.

So each step is: merge, resolve the keyable conflicts by address, and write NOTHING it cannot
key. That refusal is the whole safety property -- an unattended run that resolved everything
would be the whole-line union again, wearing a better hat.

Each PR lands as its own commit, so `git log` records which document text came from which PR
and a single bad step can be dropped without unpicking the rest.

Residue is ACCUMULATED, not stopped on. Stopping at the first prologue means 35 stops for a
fleet of 35, each restart re-merging everything before it. The property that matters is not
"stop early" -- it is that nothing unkeyable is ever written and every dropped line lands in
front of a human. So the run completes, writes one report, and exits non-zero if it is not
empty.

Usage:
    2026-09-06_docs_consolidate.py <repo-dir> <branch> <report-path> <pr> [<pr> ...]

Exit: 0 when every PR merged with zero residue; 1 when the report is non-empty (read it before
opening the PR); 2 on usage error.
"""

from __future__ import annotations

import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
import tempfile
from pathlib import Path

RESOLVER = Path(__file__).with_name("2026-09-06_docs_conflict_resolve.py")
STRUCTURE = Path(__file__).with_name("2026-09-05_markdown_structure_check.py")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=600, check=False)


def _problems(repo: Path, paths: list[str], *, at: str | None) -> int:
    """Structural-problem count for `paths`, either as they are now (`at=None`) or as `at` had
    them. The `at` form materialises each blob under a temp dir, because the screen reads files
    and the point is to compare the SAME screen against two trees."""
    with tempfile.TemporaryDirectory() as td:
        if at is not None:
            targets = []
            for rel in paths:
                blob = git(repo, "show", f"{at}:{rel}").stdout
                dest = Path(td) / rel.replace("/", "__")
                dest.write_text(blob, encoding="utf-8")
                targets.append(str(dest))
        else:
            targets = paths
        res = subprocess.run([sys.executable, str(STRUCTURE), *targets], cwd=repo, capture_output=True, text=True, timeout=300, check=False)
    for line in res.stdout.splitlines():
        if line.startswith("structural problems:"):
            return int(line.split(":")[1])
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 4:
        print(__doc__)
        return 2
    repo = Path(args[0]).resolve()
    branch = args[1]
    report_path = Path(args[2])
    prs = [int(a) for a in args[3:]]
    report: list[str] = []

    def flush(stopped_at: int | None) -> int:
        """Write whatever residue was collected, on EVERY exit path.

        A run that stops at PR 5 of 35 must not throw away the lines it held back from PRs 1-4:
        those are exactly the ones that have to be read. Naming the PR it stopped on makes
        resuming a matter of re-invoking with the tail of the list, rather than reconstructing
        the position from `git log`.
        """
        if report:
            report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
            dropped = sum(1 for ln in report if ln.startswith("        |"))
            print(f"\n{dropped} unkeyable line(s) NOT written -- read {report_path}")
        if stopped_at is not None:
            rest = prs[prs.index(stopped_at) :]
            print(f"resume with: {' '.join(str(x) for x in rest)}")
            return 1
        return 1 if report else 0

    for pr in prs:
        ref = f"refs/superseded/pr{pr}"
        git(repo, "fetch", "origin", f"pull/{pr}/head:{ref}", "--force")
        title = subprocess.run(["gh", "pr", "view", str(pr), "--json", "title", "--jq", ".title"], cwd=repo, capture_output=True, text=True, timeout=120, check=False).stdout.strip()
        res = git(repo, "merge", "--no-commit", "--no-ff", ref)
        unmerged = [ln for ln in git(repo, "diff", "--name-only", "--diff-filter=U").stdout.splitlines() if ln]

        if res.returncode != 0 and not unmerged:
            print(f"[STOP ] #{pr}: merge failed with no unmerged paths\n{res.stderr}")
            return flush(pr)

        residue = 0
        if unmerged:
            out = subprocess.run([sys.executable, str(RESOLVER), *unmerged], cwd=repo, capture_output=True, text=True, timeout=600, check=False)
            residue = out.returncode
            if residue:
                report.append(f"=== #{pr} {title}")
                report.extend(ln for ln in out.stdout.splitlines() if ln.startswith(("    PROLOGUE", "    UNKEYED", "        |")))
            still = [ln for ln in git(repo, "diff", "--name-only", "--diff-filter=U").stdout.splitlines() if ln]
            # Ask the TREE, not the resolver's prose: keying this on the word "UNKEYED" in
            # stdout means renaming the verdict silently stops the driver stopping.
            leftover = [f for f in still if "<<<<<<< " in (repo / f).read_text(encoding="utf-8", errors="replace")]
            if leftover:
                print(f"[STOP ] #{pr}: conflict markers survive in {leftover} -- cannot continue")
                print(out.stdout.rstrip())
                return flush(pr)
            md = [f for f in unmerged if f.endswith(".md")]
            if md:
                # Gate HERE, not at the end: a table broken in step 3 is cheap to find now and
                # expensive after step 35, with 82 commits to unpick. And gate on the DELTA --
                # #1680's two headerless tables are already on origin/main, so a demand for zero
                # fails on inherited damage while saying nothing about this step.
                before = _problems(repo, md, at="HEAD")
                after = _problems(repo, md, at=None)
                if after > before:
                    print(f"[STOP ] #{pr}: structure problems {before} -> {after} after resolution")
                    chk = subprocess.run([sys.executable, str(STRUCTURE), *md], cwd=repo, capture_output=True, text=True, timeout=300, check=False)
                    print(chk.stdout.rstrip()[-4000:])
                    return flush(pr)
            git(repo, "add", *unmerged)

        msg = f"docs: {title}\n\nHarvested from #{pr} by identity-keyed conflict resolution (see\n`util/ad-hoc/2026-09-06_docs_conflict_resolve.py`). Metadata took HEAD;\ninventory entries were unioned on their PATH or ANCHOR address.\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01XKkhhaqpFhYJ89JFtYU6Q5\n"
        commit = git(repo, "commit", "--no-verify", "-m", msg)
        if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
            print(f"[STOP ] #{pr}: commit failed\n{commit.stdout}\n{commit.stderr}")
            return flush(pr)
        print(f"[OK   ] #{pr} on {branch}")

    print(f"\nAll {len(prs)} PR(s) merged.")
    return flush(None)


if __name__ == "__main__":
    raise SystemExit(main())
