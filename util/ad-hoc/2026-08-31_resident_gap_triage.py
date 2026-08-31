#!/usr/bin/env python3
"""Rank resident-gap candidates by HAZARD SEVERITY instead of by identifier count.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (plan §P5 — Hazards-block completion, fleet triage)
Author:      Paul Calnon
License:     MIT

Why this is a third tool and not a flag on either of the other two.

``2026-08-28_hazard_triage.py`` scores severity, but only reads ``AGENTS.md`` -- it can rank what
is already resident and nothing else. ``2026-08-28_resident_gap_scan.py`` finds what is
hazard-shaped in SOURCE and resident nowhere, but ranks its output by **identifier count**, which
is a proxy for distinctiveness, not for danger. Run across the fleet on 2026-08-31 it returned
~630 candidates whose top entries were mostly long docstrings that merely happened to name many
symbols.

This joins them: the gap scan's finding, the triage's four severity signals.

SCORE THE BLOCK; use a sentence window only to pick what to PRINT.

The first version of this file scored a 2-sentence sliding window, reasoning that a long docstring
would otherwise accumulate a prohibition from one paragraph and a silence marker from an unrelated
one. That reasoning is sound and the design was still wrong, and a positive control is what caught
it -- the same control discipline ``hazard_triage`` records for itself.

**The control**: cascor's ``cascade_correlation.py:1927`` (the ``max_epochs`` / ``output_epochs``
split) is a known-real hazard -- owner-settled as finding L-2, silent in both directions, and
promoted into cascor's Hazards block by juniper-ml#609 on 2026-08-31. Scored against cascor's
pre-#609 ``AGENTS.md`` it must come out near the top. Under window scoring it scored **2**, below
the default threshold, and the winning window was the BUG-CC-09 tail rather than the directive:
"do not *fix* this by forwarding ``max_epochs``" and "the residual footgun is real" sit four
paragraphs apart, so no small window can ever pair them. The tool would have missed the one hazard
already known to be real.

So the score is the BLOCK score, exactly as ``hazard_triage`` computes it, because that tool is
deliberately "tuned for RECALL, not precision: a missed hazard costs far more than a false
positive". The sentence window survives only to choose the snippet shown to the reviewer, so the
output is readable without 3,000 characters of ``Args:`` boilerplate. False aggregation across a
long docstring is handled where it belongs -- by a human reading the printed line -- not by a
threshold that silently drops real directives.

FALSE POSITIVES ARE DEMOTED, NEVER DROPPED.

The dominant false positive is the word WARNING (or CRITICAL / IMPORTANT) used as a **log level**
rather than as a caution -- ``logger.warning``, ``DeprecationWarning``, a TRACE/DEBUG/INFO/WARNING
level table. Those lose the ``hazard-noun`` signal only, and the demotion is recorded in the
``demoted`` field and counted in the summary. Nothing is silently discarded: a suppressed hit that
still scores >= --min-score is still printed. The rule this obeys is the one from the vacuous-pass
notes -- a filter that hides its own suppressions is how a real hazard gets lost.

Read-only. Imports the two sibling tools by path (their module names start with a digit, so a
plain ``import`` cannot reach them).

Usage:
    python3 util/ad-hoc/2026-08-31_resident_gap_triage.py /path/to/repo [more repos ...]
    python3 util/ad-hoc/2026-08-31_resident_gap_triage.py <repo> --min-score 3 --top 15
    python3 util/ad-hoc/2026-08-31_resident_gap_triage.py <repo> --json out.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(stem: str):
    """Import a sibling ad-hoc module whose name starts with a digit."""
    path = HERE / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem.replace("-", "_"), path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GAP = _load("2026-08-28_resident_gap_scan")
TRI = _load("2026-08-28_hazard_triage")

# A hazard-noun hit is discounted when the window is talking about LOGGING rather than danger.
LOG_CONTEXT = re.compile(
    r"(logger\s*\.\s*\w+|logging\.|log_level|LOG_LEVEL|\blevels?\b|DeprecationWarning|"
    r"\bwarnings?\.warn|structured \w+ line|TRACE|VERBOSE|\bstderr\b|log shipper)", re.I)
# ...and only if the hazard nouns present are the ones that double as level names.
LEVEL_NOUNS = re.compile(r"\b(WARNING|CRITICAL|IMPORTANT)\b", re.I)
OTHER_NOUNS = re.compile(r"\b(HAZARD|CAUTION|DANGER|the one \w+ that|worst|trap|gotcha|footgun|"
                         r"do-not|incident)\b", re.I)

SENT = re.compile(r"(?<=[.!?;])\s+|\s{2,}")


def windows(text: str, size: int = 2) -> list[str]:
    """Consecutive `size`-sentence windows (plus each sentence alone, for short blocks)."""
    parts = [s.strip() for s in SENT.split(text) if s and s.strip()]
    if not parts:
        return []
    out = list(parts)
    for i in range(len(parts) - size + 1):
        out.append(" ".join(parts[i:i + size]))
    return out


def score_window(win: str) -> tuple[int, list[str], list[str]]:
    """(score, signals, demotions) for one window."""
    n, hits = TRI.score(win)
    demoted: list[str] = []
    if "hazard-noun" in hits and LEVEL_NOUNS.search(win) and not OTHER_NOUNS.search(win):
        if LOG_CONTEXT.search(win):
            hits = [h for h in hits if h != "hazard-noun"]
            n -= 1
            demoted.append("hazard-noun: level name in a logging context")
    return n, hits, demoted


def triage_repo(repo: Path, globs: list[str] | None, agents_name: str,
                min_len: int) -> list[dict]:
    agents_path = repo / agents_name
    if not agents_path.is_file():
        return []
    agents_low = agents_path.read_text(encoding="utf-8", errors="replace").lower()

    files: set[Path] = set()
    for g in (globs or ["src/**/*.py", "*/**/*.py"]):
        for p in repo.glob(g):
            if not p.is_file() or "test" in p.name:
                continue
            if GAP.SKIP_DIRS.intersection(p.parts):
                continue
            files.add(p)

    rows: list[dict] = []
    for f in sorted(files):
        for lno, text in GAP.comment_blocks(f):
            if len(text) < min_len or not GAP.MARKER.search(text):
                continue
            idents = GAP.identifiers(text)
            if not idents:
                continue
            # The gap predicate: NONE of its identifiers appears in AGENTS.md.
            if any(i.lower() in agents_low for i in idents):
                continue
            # SCORE: the whole block, recall-first (see module docstring's positive control).
            score, signals, demoted = score_window(text)
            if score == 0:
                continue
            # DISPLAY: the tightest window that carries the most signals, so the reviewer reads
            # the sentence pair that earned the score rather than the whole docstring.
            snippet, snippet_n = text, -1
            for win in windows(text):
                n, _, _ = score_window(win)
                if n > snippet_n or (n == snippet_n and len(win) < len(snippet)):
                    snippet, snippet_n = win, n
            rows.append({
                "repo": repo.name,
                "file": str(f.relative_to(repo)),
                "line": lno,
                "score": score,
                "signals": signals,
                "demoted": demoted,
                "idents": len(idents),
                "block_chars": len(text),
                "window": snippet[:400],
            })
    rows.sort(key=lambda r: (-r["score"], "silent-failure" not in r["signals"], -r["idents"]))
    return rows


def self_check(cascor: Path, agents_name: str) -> int:
    """Positive control: the known-real cascor hazard must rank at the top.

    ``cascade_correlation.py:1927`` is the ``max_epochs`` / ``output_epochs`` split -- owner-settled
    as finding L-2, silent in both directions, and promoted into cascor's Hazards block by ml#609.
    Scored against an ``AGENTS.md`` that does NOT yet contain it, this tool must surface it at
    score >= 3 and inside the top few rows. A window-scoring build put it at 2 and buried it; that
    is the regression this guards.

    Point ``--agents`` at cascor's pre-#609 ``AGENTS.md``:
        git -C juniper-cascor show e1b4988c:AGENTS.md > /tmp/pre609.md
        … --self-check --agents /tmp/pre609.md
    """
    rows = triage_repo(cascor, None, agents_name, 60)
    if not rows:
        print("SELF-CHECK FAIL: no candidates at all -- wrong repo, or AGENTS.md missing?")
        return 1
    target = [(i, r) for i, r in enumerate(rows)
              if r["line"] == 1927 and r["file"].endswith("cascade_correlation.py")]
    if not target:
        print("SELF-CHECK FAIL: the known max_epochs hazard (cascade_correlation.py:1927) "
              "was not returned at all. If cascor's AGENTS.md already carries it, pass "
              "--agents <pre-#609 copy>; otherwise the gap predicate or the globs regressed.")
        return 1
    rank, row = target[0]
    ok = row["score"] >= 3 and rank < 5
    print(f"{'SELF-CHECK PASS' if ok else 'SELF-CHECK FAIL'}: "
          f"cascade_correlation.py:1927 score={row['score']} signals={row['signals']} "
          f"rank={rank + 1} of {len(rows)}")
    if not ok:
        print("  expected score >= 3 and rank within the top 5.")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repos", nargs="+", type=Path)
    ap.add_argument("--glob", action="append", default=None)
    ap.add_argument("--agents", default="AGENTS.md")
    ap.add_argument("--min-len", type=int, default=60)
    ap.add_argument("--min-score", type=int, default=3,
                    help="minimum severity signals to print (default 3 of 4)")
    ap.add_argument("--top", type=int, default=12, help="max rows printed per repo")
    ap.add_argument("--json", type=Path, default=None, help="write ALL scored rows here")
    ap.add_argument("--self-check", action="store_true",
                    help="run the positive control and exit non-zero if the known hazard is missed")
    ns = ap.parse_args(argv)

    if ns.self_check:
        return self_check(ns.repos[0].resolve(), ns.agents)

    everything: list[dict] = []
    for repo_arg in ns.repos:
        repo = repo_arg.resolve()
        rows = triage_repo(repo, ns.glob, ns.agents, ns.min_len)
        everything.extend(rows)
        keep = [r for r in rows if r["score"] >= ns.min_score]
        dem = sum(1 for r in rows if r["demoted"])
        print(f"\n{'=' * 100}\n{repo.name}: {len(rows)} scored candidate(s); "
              f"{len(keep)} at score >= {ns.min_score}; {dem} carried a demotion")
        for r in keep[:ns.top]:
            flags = ",".join(r["signals"])
            print(f"\n  [{r['score']}] {r['file']}:{r['line']}   {flags}")
            if r["demoted"]:
                print(f"      demoted: {'; '.join(r['demoted'])}")
            print(f"      {r['window'][:300]}")
        if len(keep) > ns.top:
            print(f"\n  … {len(keep) - ns.top} more at this threshold (--top)")

    if ns.json:
        ns.json.write_text(json.dumps(everything, indent=2))
        print(f"\nwrote {len(everything)} scored rows -> {ns.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
