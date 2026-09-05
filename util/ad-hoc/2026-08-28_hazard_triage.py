#!/usr/bin/env python3
"""Find candidate HAZARDS in an AGENTS.md — directives that must stay resident through a cut.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (plan §P5 step e — cut prerequisite)
Author:      Paul Calnon
License:     MIT

Why this runs BEFORE a cut, not after.

juniper-ml's own `AGENTS.md` carries a `## Hazards (resident -- do not relocate)` block whose
rationale is that these are directives whose NON-APPLICATION destroys work, and that "a pointer only
helps an agent that already knows to look". A size-driven cut has no way to tell a lookup-reference
from a must-not-look-up warning, so relocating blind can demote a hazard into a footnote.

The failure is real and silent. The canopy session recorded three instances in three days of a guard
that existed, read as correct, and never fired because it named something that had moved
(F-CANOPY-039 still naming `fast-update-interval` after F-027 replaced it; F-038's Stage 2
suppression never biting; F-033 attributing a reset storm from a stale itempath index). A relocation
is the same move as a rename: it turns a resident fact into a reference someone must follow.

This does NOT decide anything. It surfaces candidates for a human to triage, ranked, with the
section each lives in -- so the promote-to-Hazards decision is made on a list rather than on memory.

Signals, strongest first:
  * an imperative prohibition -- NEVER / MUST NOT / DO NOT / never / must not
  * a silence marker -- "silently", "no error", "reads as", "looks like", "passes vacuously"
  * an irreversibility marker -- "unrecoverable", "irrecoverable", "destroys", "deletes", "lost"
  * a hazard-shaped noun -- HAZARD / WARNING / CAUTION / "the one ... that"

Usage:
    python3 util/ad-hoc/2026-08-28_hazard_triage.py juniper-canopy [juniper-cascor ...]
    python3 util/ad-hoc/2026-08-28_hazard_triage.py juniper-canopy --min-score 2
"""
from __future__ import annotations

import argparse
import base64
import re
import subprocess  # nosec B404 -- fixed-argv `gh api` calls only; nothing is shell-interpolated
import sys

# Tuned for RECALL, not precision: this is a triage list a human reads, and a missed hazard costs
# far more than a false positive. The thresholds were set by a positive control against
# juniper-ml's own Hazards block -- the first version scored 0 of its 4, the second 1 of 4. A
# hazard-finder that finds no hazards in a file with a Hazards section is the vacuous-pass class.
PROHIBITION = re.compile(r"\b(NEVER|MUST NOT|DO NOT|never|must not|do not|don't|cannot|may not|"
                         r"must (?:be|set|use|run|carry|have|stay|match|go)|is not optional|"
                         r"refuse|prohibited|forbidden|only \w+ (?:can|may|does))\b", re.I)
SILENCE = re.compile(r"\b(silent|silently|quietly|no error|without warning|reads? as|reads green|"
                     r"looks? like|vacuous|passes anyway|still green|no way to tell|"
                     r"indistinguishable|invisible|unnoticed|appears? to|seems? to)\b", re.I)
IRREVERSIBLE = re.compile(r"\b(unrecoverab\w*|irrecoverab\w*|destroy\w*|delete[sd]?|deleting|"
                          r"permanently|lost|loses|losing|clobber\w*|overwrit\w*|corrupt\w*|"
                          r"unmergeable|cannot be undone|kill[sed]*|killing|wipe[sd]?|reap\w*|"
                          r"irreversib\w*|breaks?\b|broken)\b", re.I)
HAZARD_NOUN = re.compile(r"\b(HAZARD|WARNING|CAUTION|DANGER|CRITICAL|IMPORTANT|the one \w+ that|"
                         r"worst|trap|gotcha|footgun|do-not|incident)\b", re.I)


def blob(repo: str, path: str) -> str:
    p = subprocess.run(  # nosec B603 B607 -- fixed argv, gh on PATH by policy
        ["gh", "api", f"repos/pcalnon/{repo}/contents/{path}?ref=main", "--jq", ".content"],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        err = (p.stderr or p.stdout).strip()
        if "HTTP 404" in err or '"status":"404"' in err:
            return ""
        raise RuntimeError(f"gh api {repo}/{path}: {err[:300]}")
    return base64.b64decode(p.stdout.strip()).decode("utf-8", "replace")


def fence_mask(lines: list[str]) -> list[bool]:
    """CommonMark-correct: a fence closes only on >= the opening run, with no info string."""
    mask = [False] * len(lines)
    char, count = None, 0
    for i, raw in enumerate(lines):
        s = raw.lstrip()
        m = re.match(r"^(`{3,}|~{3,})(.*)$", s) if (len(raw) - len(s)) <= 3 else None
        if m is None:
            mask[i] = char is not None
            continue
        run, info = m.group(1), m.group(2).strip()
        if char is None:
            char, count = run[0], len(run)
        elif run[0] == char and len(run) >= count and not info:
            char, count = None, 0
        else:
            mask[i] = True
    return mask


def score(line: str) -> tuple[int, list[str]]:
    hits = []
    if PROHIBITION.search(line):
        hits.append("prohibition")
    if SILENCE.search(line):
        hits.append("silent-failure")
    if IRREVERSIBLE.search(line):
        hits.append("irreversible")
    if HAZARD_NOUN.search(line):
        hits.append("hazard-noun")
    return len(hits), hits


def has_hazards_section(text: str) -> bool:
    return any(re.match(r"^##+\s+Hazards\b", ln) for ln in text.splitlines())


def collect_blocks(lines: list[str], inside: list[bool] | None = None) -> list[tuple[int, str, list[str]]]:
    """Split markdown into scoreable blocks. A fence ends the current block and is never scored.

    A block is a bullet item or a paragraph: it starts at a list marker or after a blank line,
    and continues through continuation lines. Headings (`#...`) also start a new block so the
    section label can change. 1-indexed start lines match the CLI's `L<n>` output.
    """
    if inside is None:
        inside = fence_mask(lines)
    section = "(preamble)"
    blocks: list[tuple[int, str, list[str]]] = []
    cur: list[str] = []
    cur_start, cur_sec = 0, section
    for i, ln in enumerate(lines):
        # A fence ENDS the current block and its contents are never scored. Letting fenced
        # lines join the preceding block produced a false positive on canopy: a `try/except`
        # code sample scored `silent-failure,hazard-noun` off its own comments. A hazards list
        # a human reads must not spend their judgement on code examples.
        if inside[i] or re.match(r"^\s{0,3}(`{3,}|~{3,})", ln):
            if cur:
                blocks.append((cur_start, cur_sec, cur))
                cur = []
            continue
        if ln.startswith("## "):
            section = ln[3:].strip()
        starts = bool(re.match(r"^\s*([-*+]|\d+\.)\s", ln)) or ln.startswith("#")
        if not ln.strip() or starts:
            if cur:
                blocks.append((cur_start, cur_sec, cur))
            cur, cur_start, cur_sec = ([ln] if starts else []), i + 1, section
            continue
        if not cur:
            cur_start, cur_sec = i + 1, section
        cur.append(ln)
    if cur:
        blocks.append((cur_start, cur_sec, cur))
    return blocks


def collect_candidates(text: str, min_score: int = 2) -> list[tuple[int, int, str, str, list[str]]]:
    """Score BLOCKS, not lines. Return `(score, start_line, section, text, hits)` descending.

    A first version scored per line and found ZERO candidates in juniper-ml's own AGENTS.md
    -- which has a Hazards section with four bullets. The positive control is what caught it:
    these directives are wrapped prose, so "Do not set it" and "silently diverges" sit on
    different lines and no single line ever reaches two signals.
    """
    lines = text.splitlines()
    found: list[tuple[int, int, str, str, list[str]]] = []
    for start, sec, blines in collect_blocks(lines):
        text_block = " ".join(b.strip() for b in blines).strip()
        if len(text_block) < 40:
            continue
        s, hits = score(text_block)
        if s >= min_score:
            found.append((s, start, sec, text_block, hits))
    found.sort(key=lambda r: (-r[0], r[1]))
    return found


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--min-score", type=int, default=2, help="signals a line must carry (default 2)")
    ap.add_argument("--path", default="AGENTS.md")
    ns = ap.parse_args(argv)

    for repo in ns.repos:
        text = blob(repo, ns.path)
        if not text:
            print(f"\n### {repo}: no {ns.path}")
            continue
        has_block = has_hazards_section(text)
        print(f"\n### {repo}  {ns.path} {len(text):,} chars   "
              f"existing Hazards section: {'YES' if has_block else '** NONE **'}")
        found = collect_candidates(text, ns.min_score)
        print(f"    {len(found)} candidate line(s) at >= {ns.min_score} signals\n")
        for s, lno, sec, ln, hits in found:
            print(f"  [{s}] L{lno:<5} {sec[:38]:<38} {','.join(hits)}")
            print(f"        {ln[:150]}")
        by_sec: dict[str, int] = {}
        for _s, _l, sec, _ln, _h in found:
            by_sec[sec] = by_sec.get(sec, 0) + 1
        if by_sec:
            print("\n    candidates per section (a section with many is a RELOCATION RISK):")
            for sec, n in sorted(by_sec.items(), key=lambda kv: -kv[1]):
                print(f"      {n:>3}  {sec}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
