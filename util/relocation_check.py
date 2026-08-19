#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Relocation completeness check -- gate **G3** of the shared-session-memory plan
(``notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md``).

Why this has to exist before the cut
------------------------------------
P3 relocates ~136,000 characters out of ``AGENTS.md``. The repo's only mechanical
content-loss alarm cannot see that shape of edit:

* ``juniper-docs-additions-check`` FAILs only when ``added == 0``. "Delete a
  block, leave a pointer, keep the heading" -- exactly what a relocation looks
  like -- is a WARN at any magnitude (mechanism-facts section 8d, verified at
  source).
* A token-level check does not help either: a relocation that carries the
  identifiers but drops the surrounding reasoning scores as complete, because the
  identifiers survive in the destination while the prose that explained them does
  not. That is the loss this repo actually suffers.

So the migration would otherwise proceed with **no** content-loss control. This is
that control, and it is deliberately prose-level rather than token-level.

What it asserts
---------------
Every substantive line REMOVED from the source between BASE and HEAD must have a
sufficiently similar line PRESENT in the destination at HEAD. Similarity is
computed on normalised prose (markdown emphasis, link syntax, list markers and
backticks stripped; whitespace collapsed; lowercased), so a faithfully reworded
relocation passes while a dropped explanation does not.

Not a plagiarism check. The threshold is deliberately below 1.0 because relocation
legitimately rewrites lead-ins ("-- Drift checker for X" becomes "### X\\n\\nDrift
checker for ..."). It is high enough that dropping a sentence fails.

Deliberately ignored (never "substantive"): blank lines, pure markup, headings,
fence delimiters, and lines below ``--min-chars`` -- a bare ``| --- |`` table rule
carries no knowledge and would only add noise.

Known limitation: it is LINE-granular
-------------------------------------
A removed line whose content is **redistributed** across several destination lines
scores low and is reported, even though no knowledge was lost. That is a real
false-positive class, and it is left in deliberately rather than tuned away:

* the gate is advisory, and "this line's prose is no longer findable as a unit --
  check it" is a useful thing to say;
* the fix for it would be union/coverage matching, where an arbitrary scatter of
  tokens can cover any needle -- which is how this gate would become the
  token-level check it exists to replace.

For the P3 migration the distinction matters little, because P3 *relocates* prose
largely intact rather than rewriting it. Compression-and-redistribution is a
different operation and should be verified by a human when flagged.

Vacuous-pass resistance
-----------------------
A gate that cannot fail is not a gate, and this repo has a documented class where
the machinery breaks and reports SUCCESS. Hard exit 2, never a pass, when: the
source or destination path does not exist at HEAD; a git invocation fails; or the
diff yields no removed lines while the caller asserted a relocation via
``--expect-removals``. ``tests/test_relocation_check.py`` carries the negative
controls, including the identifier-carried / prose-dropped case that a token-level
check would wave through.

Usage:
    python util/relocation_check.py --base origin/main --head HEAD \\
        --source AGENTS.md --dest docs/REFERENCE.md [--threshold 0.72]
        [--min-chars 40] [--expect-removals] [--json] [--advisory]

Exit: 0 complete (or advisory) / 1 content lost / 2 misuse or broken machinery.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_THRESHOLD = 0.72
DEFAULT_MIN_CHARS = 40

_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^\s*#{1,6}\s")
_TABLE_RULE = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MARKUP = re.compile(r"[*_`>#|]+")
_LIST = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
_WS = re.compile(r"\s+")


class RelocationError(RuntimeError):
    """Machinery failure -- never degrade this to a pass."""


def git(repo: Path, *args: str) -> str:
    try:
        res = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, check=False
        )
    except OSError as exc:
        raise RelocationError(f"git invocation failed: {exc}") from exc
    if res.returncode != 0:
        raise RelocationError(
            f"git {' '.join(args)} failed: {res.stderr.decode(errors='replace').strip()}"
        )
    return res.stdout.decode("utf-8", errors="replace")


def normalise(line: str) -> str:
    """Reduce a markdown line to comparable prose."""
    text = _LIST.sub("", line)
    text = _LINK.sub(r"\1", text)          # keep link TEXT, drop the target
    text = _MARKUP.sub(" ", text)
    return _WS.sub(" ", text).strip().lower()


def is_substantive(line: str, min_chars: int) -> bool:
    stripped = line.strip()
    if not stripped or _FENCE.match(stripped) or _HEADING.match(stripped):
        return False
    if _TABLE_RULE.match(stripped):
        return False
    return len(normalise(stripped)) >= min_chars


def removed_lines(repo: Path, base: str, head: str, source: str) -> list[str]:
    diff = git(repo, "diff", "--unified=0", f"{base}...{head}", "--", source)
    out = []
    for raw in diff.splitlines():
        if raw.startswith("---"):
            continue
        if raw.startswith("-"):
            out.append(raw[1:])
    return out


def dest_lines(repo: Path, head: str, dest: str) -> list[str]:
    return git(repo, "show", f"{head}:{dest}").splitlines()


def best_match(needle: str, haystack: list[str]) -> float:
    """Highest similarity of `needle` against any destination line.

    Containment is asymmetric on purpose, and getting this backwards is how the
    gate becomes tautological:

    * ``needle in candidate`` -> **1.0**. The destination line contains the whole
      removed line; relocation routinely merges two source bullets into one
      destination sentence, and that is not a loss.
    * ``candidate in needle`` -> **NOT a match**. The destination holds only a
      FRAGMENT of what was removed -- e.g. the source sentence explained why
      ``--fix`` never picks ``candidates[0]``, and the destination kept only the
      bare identifier. That is exactly the identifier-carried / prose-dropped
      loss this gate exists to catch, so it must fall through to the ratio and
      score low. Pinned by ``test_identifiers_carried_but_prose_dropped_fails``.
    """
    best = 0.0
    for candidate in haystack:
        if not candidate:
            continue
        if needle in candidate:
            return 1.0
        ratio = difflib.SequenceMatcher(None, needle, candidate).ratio()
        if ratio > best:
            best = ratio
    return best


def check(
    repo: Path, base: str, head: str, source: str, dest: str,
    threshold: float, min_chars: int, expect_removals: bool,
) -> dict:
    for rel in (source, dest):
        try:
            git(repo, "cat-file", "-e", f"{head}:{rel}")
        except RelocationError as exc:
            raise RelocationError(f"{rel} not present at {head}: {exc}") from exc

    removed = [ln for ln in removed_lines(repo, base, head, source)
               if is_substantive(ln, min_chars)]

    if expect_removals and not removed:
        raise RelocationError(
            "--expect-removals was set but the diff removed no substantive lines "
            "from the source; the check would have passed vacuously"
        )

    # The haystack is the destination AND the source as it stands at HEAD.
    #
    # "Lost" means gone from BOTH, not merely moved out of one diff hunk. An
    # in-place rewrite -- reword a bullet, keep it in AGENTS.md -- shows up in the
    # diff as a removal exactly like a relocation does, and searching only the
    # destination would report it as content loss. Found by running this gate on
    # its own PR, which is the whole argument for dogfooding a control before
    # trusting it with a 136,000-character migration.
    haystack = [
        normalise(ln)
        for ln in dest_lines(repo, head, dest) + dest_lines(repo, head, source)
    ]
    haystack = [h for h in haystack if h]

    findings = []
    for line in removed:
        needle = normalise(line)
        score = best_match(needle, haystack)
        if score < threshold:
            findings.append({"line": line.strip()[:200], "best_score": round(score, 3)})

    return {
        "source": source, "dest": dest, "base": base, "head": head,
        "threshold": threshold, "removed_substantive": len(removed),
        "unmatched": len(findings), "findings": findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--source", default="AGENTS.md")
    ap.add_argument("--dest", default="docs/REFERENCE.md")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS)
    ap.add_argument("--expect-removals", action="store_true",
                    help="fail if the diff removed nothing (anti-vacuous-pass)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--advisory", action="store_true", help="report, always exit 0")
    args = ap.parse_args()

    try:
        result = check(
            args.repo_root.resolve(), args.base, args.head, args.source, args.dest,
            args.threshold, args.min_chars, args.expect_removals,
        )
    except RelocationError as exc:
        print(f"::error::relocation-check machinery failure: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=== relocation completeness (G3) ===")
        print(f"{result['source']} -> {result['dest']}  "
              f"base={result['base']} head={result['head']} "
              f"threshold={result['threshold']}")
        print(f"removed_substantive={result['removed_substantive']} "
              f"unmatched={result['unmatched']}")
        for f in result["findings"]:
            print(f"\n  [LOST] (best={f['best_score']}) {f['line']}")
        if result["findings"]:
            print(f"\n::error::{result['unmatched']} substantive line(s) were removed "
                  f"from {result['source']} without a matching line appearing in "
                  f"{result['dest']}. Relocation must MOVE knowledge, not drop it — "
                  f"carrying the identifiers while losing the prose that explains "
                  f"them is the exact failure this gate exists to catch.")
        elif result["removed_substantive"]:
            print("\nOK: every removed substantive line has a match in the destination.")
        else:
            print("\nOK: no substantive removals in this range.")

    if args.advisory and result["findings"]:
        print("\nADVISORY MODE — reporting only, not failing the build.")
        return 0
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
