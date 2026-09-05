#!/usr/bin/env python3
"""2026-09-05_fleet_docs_consolidate.py -- consolidate N fleet docs PRs into one branch.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License

WHY

Under `strict_required_status_checks_policy: true` with `allow_update_branch: false`,
N docs PRs that all edit `docs/REFERENCE.md` are a strictly serial train, AND each landed
merge advances the file's `**Version:**` line, which is precisely the line every sibling
PR also rewrites. Measured on 2026-09-05: PRs based on doc-version 0.6.15 were 34/34
CONFLICTING while those based on 0.6.22 were 0/12 -- a single merge bumped seven versions
and converted the whole clean cohort at once. So merging them one at a time is not just
~17 check-batteries per PR, it degrades as it runs: #1707 went DIRTY mid-train.

Consolidating them into ONE branch costs one check battery and one merge.

THE SAFETY PROPERTY, AND WHY THE RESOLVER IS FAIL-CLOSED

The bot pre-allocates a UNIQUE doc-version per PR (REFERENCE.md 0.6.16 -> 0.6.58), so
every pair of docs PRs conflicts on the version/date/footer lines and on the
Version-History row insertion point. Those lines carry no information that survives
consolidation -- the consolidated PR gets ONE coherent header.

But "the conflicts are only version lines" is a MEASUREMENT, not a guarantee: an
independent adversarial pass found that 22 of 43 conflicting PRs had at least one
conflicted file with no version header at all (e.g. `util/ad-hoc/README.md`, a pure
section-append collision). So this script NEVER assumes. It auto-resolves a conflict
hunk only when every line inside it matches `NEUTRAL_LINE_RE`; any other conflicted
hunk aborts the whole run with the file and the hunk printed. A wrong auto-resolution
here would silently drop a section, which is exactly the 2026-07-26 damage class.

VERIFICATION

`--verify` re-derives, per source PR, every line that PR ADDS to a docs file, and asserts
it is present in the consolidated tree -- excluding only lines matching NEUTRAL_LINE_RE
(the deliberately-dropped header churn), which are reported as a separate count so the
drop is visible rather than assumed. A missing line is a hard failure: a false close
loses real work.

Usage:
    python util/ad-hoc/2026-09-05_fleet_docs_consolidate.py \\
        --worktree /path/to/consolidation --base origin/main \\
        --pr 1707=cursor/engineering-documentation-updates-7a33 [...] [--verify]
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from pathlib import Path

# Lines whose only content is the bot's pre-allocated header churn. A conflict confined to
# these is auto-resolvable; a Version-History table row is NOT here -- it carries the
# changelog text and is treated as real content.
NEUTRAL_LINE_RE = re.compile(
    r"^\s*(?:\*\*Version:?\*\*|\*\*Last Updated:?\*\*|\*\*Date:?\*\*|_Version:|_Last Updated:)",
    re.IGNORECASE,
)

# Lines that are DELIBERATELY superseded by a single hand-written union, and so will never
# match any one branch's text. `docs/DOCUMENTATION_OVERVIEW.md` carries one summary row per
# document, and every docs PR appends its own topic to the SAME row; there is no string that
# contains all ten variants, so the consolidated branch rewrites the row once to carry every
# topic. Keeping these in the MISSING count would bury the genuine losses under a known one.
#
# The trade is explicit: these rows are verified BY TOPIC (does the union mention what each
# variant mentioned?) and not by string presence. That is a human check, recorded here so it
# is visible rather than implied -- and it is also how main ended up with a DUPLICATED
# `**REFERENCE.md**` row (DOCUMENTATION_OVERVIEW.md:87 and :89 before this branch): an earlier
# merge kept both variants instead of unioning them. This branch collapses that back to one.
WAIVED_LINE_RE = re.compile(
    r"^\|\s*\*\*(?:REFERENCE\.md|DEVELOPER_CHEATSHEET_JUNIPER-ML\.md)\*\*\s*\|\s*(?:Reference|Cheatsheet)\s*\|"
)

# Shared navigation files. Every docs PR appends to these, so they are an N-way semantic
# contention point.
#
# They are deliberately EMPTY by default. Blanket-resolving a whole index file to `ours`
# discards that branch's ENTIRE contribution to it, not just the one contended summary row
# -- measured: doing so dropped 135 lines across these three files, 88 of them append-only
# content blocks in the cheatsheet that merge perfectly well. The per-hunk rules
# (add/add union, per-line 3-way) handle the appends; only the genuinely two-sided summary
# rows need deferring, and `--defer-prose` already covers exactly those.
#
# Populate this only to quarantine a file whose every hunk is contended.
INDEX_FILES: set = set()

CONFLICT_START = re.compile(r"^<{7} ")
CONFLICT_BASE = re.compile(r"^\|{7}")
CONFLICT_MID = re.compile(r"^={7}$")
CONFLICT_END = re.compile(r"^>{7} ")


def git(wt: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    cp = subprocess.run(["git", "-C", str(wt), *args], capture_output=True, text=True)  # nosec B603
    if check and cp.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {cp.stderr.strip()[:400]}")
    return cp


def _threeway_pairwise(ours: list, base: list, theirs: list):
    """Per-line 3-way merge of one conflict hunk. Returns lines, or None to abort.

    Git conflicts a whole hunk when two changed lines merely ABUT, even though each line
    was changed by only ONE side. That is the dominant shape here: `docs/REFERENCE.md`
    carries a repo-tree listing where main annotated `test_experiment_stack_script.py`
    while a fleet branch annotated the adjacent `test_run_suite.py`. Both edits must
    survive; taking either side wholesale silently reverts the other -- the 2026-07-26
    damage class.

    Rule, applied per line position and only when all three sides have equal line counts:
        base == ours   -> only THEIRS changed it  -> take theirs
        base == theirs -> only OURS changed it    -> take ours
        ours == theirs -> both made the same edit -> take ours
        otherwise      -> a genuine two-sided edit of ONE line -> abort, do not guess
    """
    if not base or len(ours) != len(base) or len(base) != len(theirs):
        return None
    resolved = []
    for o, b, t in zip(ours, base, theirs):
        so, sb, st = o.strip(), b.strip(), t.strip()
        if sb == so:
            resolved.append(t)
        elif sb == st:
            resolved.append(o)
        elif so == st:
            resolved.append(o)
        else:
            return None
    return resolved


def _superset_pairwise(ours: list, theirs: list):
    """Union two conflict sides when they are the same lines, one side's text containing the other's.

    Returns the resolved line list, or None when the rule does not apply. Requires the two
    sides to have EQUAL line counts and, for every position, one line's stripped text to be
    a substring of the other's -- i.e. the sides differ only by one having added detail to
    the same sentence. Anything else (a different count, or two genuinely divergent texts)
    returns None so the caller aborts.
    """
    if not ours or len(ours) != len(theirs):
        return None
    resolved = []
    for a, b in zip(ours, theirs):
        sa, sb = a.strip(), b.strip()
        if sa == sb:
            resolved.append(a)
        elif sa and sa in sb:
            resolved.append(b)
        elif sb and sb in sa:
            resolved.append(a)
        else:
            return None
    return resolved


def conflicted_files(wt: Path) -> list:
    cp = git(wt, "diff", "--name-only", "--diff-filter=U")
    return [ln for ln in cp.stdout.splitlines() if ln.strip()]


def resolve_file(path: Path, *, defer: bool = False, deferrals: list | None = None) -> tuple:
    """Resolve conflict hunks that are ENTIRELY header churn by taking 'ours'.

    Returns (resolved: bool, offending_hunk: str|None). Fail-closed: the first hunk with
    any non-neutral line aborts, with that hunk returned verbatim for the operator.
    """
    deferrals = deferrals if deferrals is not None else []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    out: list = []
    i = 0
    while i < len(lines):
        if not CONFLICT_START.match(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        ours: list = []
        base: list = []
        theirs: list = []
        raw = [lines[i]]
        i += 1
        while i < len(lines) and not CONFLICT_BASE.match(lines[i]) and not CONFLICT_MID.match(lines[i]):
            ours.append(lines[i])
            raw.append(lines[i])
            i += 1
        if i < len(lines) and CONFLICT_BASE.match(lines[i]):  # diff3 style: the base section
            raw.append(lines[i])
            i += 1
            while i < len(lines) and not CONFLICT_MID.match(lines[i]):
                base.append(lines[i])
                raw.append(lines[i])
                i += 1
        raw.append(lines[i] if i < len(lines) else "")
        i += 1
        while i < len(lines) and not CONFLICT_END.match(lines[i]):
            theirs.append(lines[i])
            raw.append(lines[i])
            i += 1
        raw.append(lines[i] if i < len(lines) else "")
        i += 1

        body = [ln for ln in ours + theirs if ln.strip()]
        if body and all(NEUTRAL_LINE_RE.match(ln) for ln in body):
            out.extend(ours)  # one coherent header; the batch sets it explicitly afterwards
        elif not [ln for ln in base if ln.strip()] and ours and theirs:
            # ADD/ADD at the same position: the base had nothing here and both sides
            # inserted. The usual site is a TOC / index list where each PR adds its own
            # entry -- both belong, and taking either side alone silently drops a real
            # navigation line. Union, in a stable order, de-duplicated.
            seen = set()
            for ln in ours + theirs:
                if ln.strip() and ln.strip() in seen:
                    continue
                seen.add(ln.strip())
                out.append(ln)
        elif _threeway_pairwise(ours, base, theirs) is not None:
            out.extend(_threeway_pairwise(ours, base, theirs))
        elif _superset_pairwise(ours, theirs) is not None:
            # Both sides rewrote the SAME descriptive lines (the repo-tree listing in
            # REFERENCE.md is the usual site) and, line for line, one side's text CONTAINS
            # the other's. Taking the containing side is a true union: nothing either side
            # wrote is dropped. Anything not of this exact shape still aborts, and the
            # two-direction verification below re-checks the result regardless.
            out.extend(_superset_pairwise(ours, theirs))
        elif defer:
            # DEFERRED, not resolved. Two sides appended different prose to the SAME
            # descriptive line (REFERENCE.md's tree/test index is the site). Merging two
            # sentences is a judgement, not a rule, and inventing a rule per shape is how a
            # clause gets silently dropped. Keep OURS so the merge proceeds, and rely on the
            # two-direction verification to surface every line this drops: that report is
            # the exact TODO list for one manual pass at the end. Nothing is trusted here --
            # a line that never gets re-added shows up as MISSING and fails the run.
            out.extend(ours)
            deferrals.append("".join(raw)[:900])
        else:
            return (False, "".join(raw)[:1200])
    path.write_text("".join(out), encoding="utf-8")
    return (True, None)


def added_doc_lines(wt: Path, base: str, branch: str) -> dict:
    """{file: [added lines]} for .md files, from the branch's diff against the MERGE BASE.

    Merge-base, not the base tip: a line the branch did not touch but that main later
    changed is not this PR's work and must not be demanded of the consolidation.
    """
    mb = git(wt, "merge-base", base, branch).stdout.strip()
    cp = git(wt, "diff", "--unified=0", f"{mb}..{branch}", "--", "*.md")
    out: dict = {}
    current = None
    for ln in cp.stdout.splitlines():
        if ln.startswith("+++ b/"):
            current = ln[6:]
            out.setdefault(current, [])
        elif ln.startswith("+") and not ln.startswith("+++") and current:
            out[current].append(ln[1:])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--pr", action="append", required=True, metavar="N=branch")
    ap.add_argument("--verify", action="store_true", help="only re-verify content presence; merge nothing")
    ap.add_argument(
        "--defer-prose",
        action="store_true",
        help="on a two-sided prose conflict keep OURS and record it, instead of aborting; the "
             "verification report then lists exactly what must be re-added by hand",
    )
    args = ap.parse_args(argv)

    wt = Path(args.worktree).resolve()
    pairs = []
    for spec in args.pr:
        num, _, br = spec.partition("=")
        if not br:
            print(f"bad --pr {spec!r}; want N=branch", file=sys.stderr)
            return 2
        pairs.append((int(num), f"origin/{br}" if not br.startswith("origin/") else br))

    deferred: dict = {}
    prose_deferrals: list = []
    if not args.verify:
        for num, branch in pairs:
            # diff3 keeps the BASE section in the conflict markers, which is what makes the
            # per-line 3-way resolution above possible; the default 'merge' style discards it.
            cp = git(wt, "-c", "merge.conflictStyle=diff3", "merge", "--no-ff", "--no-commit", branch)
            if cp.returncode != 0:
                bad = conflicted_files(wt)
                if not bad:
                    print(f"#{num}: merge failed with no conflicted files:\n{cp.stderr[:400]}", file=sys.stderr)
                    return 1
                for rel in bad:
                    if rel in INDEX_FILES:
                        # Shared NAVIGATION files: a one-row-per-document summary table and
                        # two index lists that EVERY docs PR appends to, so they are an N-way
                        # semantic contention point rather than a merge. Growing an
                        # auto-resolver per conflict shape here is how a section gets silently
                        # dropped -- and main ALREADY carries a duplicated `**REFERENCE.md**`
                        # row (DOCUMENTATION_OVERVIEW.md:77 and :79) from exactly that mistake
                        # in an earlier merge. So: keep ours, record what each branch wanted,
                        # and REWRITE these files once, by hand, at the end of the batch.
                        git(wt, "checkout", "--ours", "--", rel)
                        git(wt, "add", rel)
                        deferred.setdefault(rel, []).append(num)
                        continue
                    ok, hunk = resolve_file(wt / rel, defer=args.defer_prose, deferrals=prose_deferrals)
                    if not ok:
                        print(f"\nABORT at #{num}: {rel} has a NON-HEADER conflict.\n{hunk}", file=sys.stderr)
                        print("Resolve by hand; this script refuses to guess.", file=sys.stderr)
                        return 1
                    git(wt, "add", rel)
            git(wt, "commit", "--no-edit", "-m", f"consolidate: docs from juniper-ml#{num} ({branch})", check=False)
            print(f"  merged #{num}", flush=True)
        if deferred:
            print("\n=== DEFERRED index files (kept OURS; rewrite these by hand) ===")
            for rel, nums in deferred.items():
                print(f"  {rel}: contended by {nums}")

    if prose_deferrals:
        print(f"\n=== {len(prose_deferrals)} DEFERRED prose conflict(s) -- kept OURS, must be re-checked ===")
        for h in prose_deferrals[:4]:
            print(h[:400])
            print("    ---")
    print("\n=== content verification (every added .md line must survive) ===")
    total_missing = 0
    for num, branch in pairs:
        added = added_doc_lines(wt, args.base, branch)
        missing: list = []
        dropped = 0
        for rel, lines in added.items():
            target = wt / rel
            text = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
            for ln in lines:
                if not ln.strip():
                    continue
                if NEUTRAL_LINE_RE.match(ln) or WAIVED_LINE_RE.match(ln):
                    dropped += 1
                    continue
                if ln.strip() not in text:
                    missing.append(f"{rel}: {ln.strip()[:110]}")
        total_missing += len(missing)
        status = "OK" if not missing else f"MISSING {len(missing)}"
        print(f"  #{num}: {status}  (header lines deliberately dropped: {dropped})")
        for m in missing[:6]:
            print(f"      - {m}")
    print(f"\nTOTAL MISSING (branch additions absent from result): {total_missing}")

    # The SYMMETRIC half. The check above only asks whether each branch's ADDITIONS
    # survived; it is blind to content that was on `main` and got dropped when a conflict
    # was resolved toward a branch. That is the 2026-07-26 damage class (a merge took the
    # branch side and deleted sections merged hours earlier), so it must be checked
    # explicitly rather than inferred.
    print("\n=== reverse check: no line on the base may be lost from a .md ===")
    cp = git(wt, "diff", "--unified=0", args.base, "--", "*.md")
    removed: dict = {}
    current = None
    for ln in cp.stdout.splitlines():
        if ln.startswith("--- a/"):
            current = ln[6:]
        elif ln.startswith("-") and not ln.startswith("---") and current:
            body = ln[1:]
            if body.strip() and not NEUTRAL_LINE_RE.match(body):
                removed.setdefault(current, []).append(body.strip())
    n_removed = sum(len(v) for v in removed.values())
    if not n_removed:
        print("  none -- the consolidation is additions-only against the base")
    else:
        for rel, lines in removed.items():
            print(f"  {rel}: {len(lines)} base line(s) removed")
            for ln in lines[:8]:
                print(f"      - {ln[:110]}")
    print(f"\nTOTAL BASE LINES REMOVED: {n_removed}")
    print("  (a removal is not automatically wrong -- an in-place edit shows as one --")
    print("   but every one must be explained before this branch merges.)")
    return 1 if total_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
