#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Pointer-follow soak instrument -- section 6 of the shared-session-memory plan
(``notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md``).

Why this exists
---------------
P3 relocated ~124,000 characters out of ``AGENTS.md`` (always loaded) into
``docs/REFERENCE.md`` (read on demand, reachable only through a pointer). The
plan calls the pointer-follow rate "the one load-bearing quantity nobody can
measure in advance" and stakes the whole architecture on it. The soak is the
falsification test: N >= 20 sessions, tracking whether agents actually retrieve
relocated facts when those facts are relevant.

The soak could not start because there was no instrument -- no definition of a
miss, no place to put an observation, no start marker. This is that instrument.
The protocol, the miss definition and the escalation thresholds live in
``notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md``; this file
is the mechanism that makes them measurable.

Why JSONL and not a markdown table
----------------------------------
Plan section 7.7: ~24 concurrent worktrees make any central ledger "a
coordination problem that this plan specifies but does not solve". A markdown
table conflicts on every concurrent append. An append-only JSONL under
``merge=union`` does not -- union merge on a file whose lines are only ever
added is exactly its intended use. Rows carry a ``(session, seq)`` key so the
reader stays correct even if union merge duplicates a line.

The unit of observation is an OCCASION, not a session
-----------------------------------------------------
A session may present zero occasions to retrieve a relocated fact, or several.
Counting one row per session would inflate the denominator with sessions that
never tested anything and make the follow rate look good for free. So: one row
per occasion, and N is the number of DISTINCT SESSIONS that produced at least
one occasion. That preserves the plan's "N >= 20 sessions" while keeping the
rate honest.

Exit codes
----------
``record``  0 written, 2 rejected (validation)
``report``  0 always
``status``  0 in progress or bet holds, 1 an escalation is due, 2 bad input
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# The soak counts only what happened at or after the cut was complete. 500508b
# is #1196, "restore the resident hazard list P3 was required to keep" -- the
# first commit at which AGENTS.md is in its post-P3, hazards-correct shape.
START_MARKER = "500508b"

DEFAULT_LEDGER = Path("reports/soak/pointer_follow_soak.jsonl")

TARGET_SESSIONS = 20
RATE_BET_HOLDS = 0.90
RATE_BET_FAILING = 0.70
AREA_SYSTEMATIC_THRESHOLD = 3

OUTCOMES = ("follow", "miss")

# Recorded miss classes map 1:1 onto the plan's fixed escalation ladder.
# "area-systematic" is deliberately NOT recordable -- it is DERIVED from >=3
# misses sharing an area. Letting a human type it would let the ladder be
# jumped by assertion, which is the rationalisation the plan forbids.
MISS_CLASSES = {
    "discoverability": "agent never knew to look -> ladder 1: add an index row",
    "hazard": "the missed fact was hazard-class -> ladder 2: CI gate or hook",
    "pointer-defect": "pointer wrong/stale -> fix the pointer, not the architecture",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(repo_root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=repo_root, capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def at_or_after_marker(repo_root: Path) -> bool | None:
    """True if HEAD descends from the start marker. None if undecidable."""
    if _git(repo_root, "rev-parse", "--verify", f"{START_MARKER}^{{commit}}") is None:
        return None
    res = subprocess.run(
        ["git", "merge-base", "--is-ancestor", START_MARKER, "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return res.returncode == 0


def load_rows(ledger: Path) -> list[dict]:
    """Read the ledger, tolerating union-merge duplicates and blank lines."""
    if not ledger.exists():
        return []
    rows: list[dict] = []
    seen: set[tuple] = set()
    for lineno, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            print(f"warning: {ledger}:{lineno}: unparseable, skipped", file=sys.stderr)
            continue
        if not isinstance(row, dict):
            continue
        key = (row.get("session"), row.get("seq"))
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    return rows


def next_seq(rows: list[dict], session: str) -> int:
    used = [r.get("seq", 0) for r in rows if r.get("session") == session]
    return (max(used) + 1) if used else 1


def analyse(rows: list[dict]) -> dict:
    """Reduce the ledger to the numbers the ladder is defined over."""
    in_scope = [r for r in rows if r.get("in_scope") is not False]
    out_of_scope = len(rows) - len(in_scope)

    # pointer-defect misses are excluded from the ARCHITECTURAL rate: the agent
    # did try to follow, so discoverability worked and the target was broken.
    # Folding them in would blame the architecture for a typo. They are still
    # reported, and every one is an immediate fix.
    architectural = [r for r in in_scope if r.get("miss_class") != "pointer-defect"]

    follows = [r for r in architectural if r.get("outcome") == "follow"]
    misses = [r for r in architectural if r.get("outcome") == "miss"]
    pointer_defects = [r for r in in_scope if r.get("miss_class") == "pointer-defect"]

    denom = len(follows) + len(misses)
    rate = (len(follows) / denom) if denom else None

    sessions = sorted({r.get("session") for r in in_scope if r.get("session")})

    by_class = Counter(r.get("miss_class") for r in misses if r.get("miss_class"))
    by_area: dict[str, int] = defaultdict(int)
    for r in misses:
        if r.get("area"):
            by_area[r["area"]] += 1
    systematic = sorted(a for a, n in by_area.items() if n >= AREA_SYSTEMATIC_THRESHOLD)

    hazard_misses = [r for r in misses if r.get("miss_class") == "hazard"]

    # Verdict. Hazard and area escalations fire regardless of N: a hazard miss
    # is a live defect, not a statistic to be accumulated.
    if hazard_misses:
        verdict, ladder = "ESCALATE-HAZARD", 2
    elif systematic:
        verdict, ladder = "ESCALATE-AREA", 3
    elif len(sessions) < TARGET_SESSIONS:
        verdict, ladder = "IN-PROGRESS", 0
    elif rate is None:
        verdict, ladder = "IN-PROGRESS", 0
    elif rate >= RATE_BET_HOLDS:
        verdict, ladder = "BET-HOLDS", 0
    elif rate >= RATE_BET_FAILING:
        verdict, ladder = "LADDER-1", 1
    else:
        verdict, ladder = "BET-FAILING", 3

    return {
        "occasions": len(in_scope),
        "out_of_scope": out_of_scope,
        "sessions": len(sessions),
        "target_sessions": TARGET_SESSIONS,
        "follows": len(follows),
        "misses": len(misses),
        "pointer_defects": len(pointer_defects),
        "follow_rate": rate,
        "miss_classes": dict(by_class),
        "misses_by_area": dict(by_area),
        "systematic_areas": systematic,
        "verdict": verdict,
        "ladder_step": ladder,
        "start_marker": START_MARKER,
    }


def cmd_record(args: argparse.Namespace) -> int:
    if args.outcome not in OUTCOMES:
        print(f"error: --outcome must be one of {OUTCOMES}", file=sys.stderr)
        return 2
    if args.outcome == "miss" and not args.miss_class:
        print("error: a miss requires --class", file=sys.stderr)
        return 2
    if args.outcome == "follow" and args.miss_class:
        print("error: --class is only meaningful on a miss", file=sys.stderr)
        return 2
    if args.miss_class and args.miss_class not in MISS_CLASSES:
        print(
            f"error: --class must be one of {sorted(MISS_CLASSES)}; "
            "'area-systematic' is derived from >=3 misses in one area, never recorded",
            file=sys.stderr,
        )
        return 2

    session = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID") or "unknown"
    ledger = args.ledger or (args.repo_root / DEFAULT_LEDGER)
    rows = load_rows(ledger)
    scope = at_or_after_marker(args.repo_root)

    row = {
        "ts": _utcnow(),
        "session": session,
        "seq": next_seq(rows, session),
        "outcome": args.outcome,
        "fact": args.fact,
        "pointer": args.pointer,
        "task": args.task,
        "area": args.area,
        "miss_class": args.miss_class,
        "worktree": args.repo_root.name,
        "commit": _git(args.repo_root, "rev-parse", "--short=8", "HEAD"),
        "in_scope": True if scope is None else scope,
        "note": args.note,
    }

    line = json.dumps(row, sort_keys=True, ensure_ascii=False)
    if args.dry_run:
        print(line)
        return 0

    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(f"recorded {row['outcome']} ({session} seq={row['seq']}) -> {ledger}")
    if row["in_scope"] is False:
        print(
            f"  note: HEAD does not descend from {START_MARKER}; "
            "row is OUT OF SCOPE and will not count toward the rate",
            file=sys.stderr,
        )
    return 0


def _render_markdown(rows: list[dict], stats: dict) -> str:
    lines = [
        "| # | Date | Session | Task | Fact needed | Pointer | Outcome | Class |",
        "|---|------|---------|------|-------------|---------|---------|-------|",
    ]
    for i, r in enumerate(sorted(rows, key=lambda x: (x.get("ts") or "")), 1):
        sess = (r.get("session") or "?")[-8:]
        mark = "follow" if r.get("outcome") == "follow" else "**MISS**"
        cells = [
            str(i),
            (r.get("ts") or "")[:10],
            sess,
            r.get("task") or "",
            r.get("fact") or "",
            f"`{r['pointer']}`" if r.get("pointer") else "",
            mark,
            r.get("miss_class") or "",
        ]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    if len(lines) == 2:
        lines.append("| _no observations recorded yet_ | | | | | | | |")
    rate = stats["follow_rate"]
    lines += [
        "",
        f"**Sessions** {stats['sessions']}/{stats['target_sessions']} &nbsp;&nbsp; "
        f"**Occasions** {stats['occasions']} &nbsp;&nbsp; "
        f"**Follows** {stats['follows']} &nbsp;&nbsp; "
        f"**Misses** {stats['misses']} &nbsp;&nbsp; "
        f"**Pointer defects** {stats['pointer_defects']} &nbsp;&nbsp; "
        f"**Follow rate** {'n/a' if rate is None else format(rate, '.1%')}",
        "",
        f"**Verdict**: `{stats['verdict']}`"
        + (f" (ladder step {stats['ladder_step']})" if stats["ladder_step"] else ""),
    ]
    return "\n".join(lines)


def cmd_report(args: argparse.Namespace) -> int:
    ledger = args.ledger or (args.repo_root / DEFAULT_LEDGER)
    rows = load_rows(ledger)
    in_scope = [r for r in rows if r.get("in_scope") is not False]
    stats = analyse(rows)
    if args.json:
        print(json.dumps(stats, indent=2, sort_keys=True))
    elif args.markdown:
        print(_render_markdown(in_scope, stats))
    else:
        print("=== pointer-follow soak ===")
        print(f"  ledger        {ledger}")
        print(f"  start marker  {START_MARKER}")
        print(f"  sessions      {stats['sessions']} / {stats['target_sessions']}")
        extra = f"  (+{stats['out_of_scope']} out of scope)" if stats["out_of_scope"] else ""
        print(f"  occasions     {stats['occasions']}{extra}")
        print(f"  follows       {stats['follows']}")
        print(f"  misses        {stats['misses']}  {stats['miss_classes'] or ''}")
        print(f"  ptr defects   {stats['pointer_defects']}")
        rate = stats["follow_rate"]
        print(f"  follow rate   {'n/a' if rate is None else format(rate, '.1%')}")
        print(f"  verdict       {stats['verdict']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ledger = args.ledger or (args.repo_root / DEFAULT_LEDGER)
    stats = analyse(load_rows(ledger))
    if args.json:
        print(json.dumps(stats, indent=2, sort_keys=True))
    else:
        rate = stats["follow_rate"]
        print(
            f"{stats['verdict']}  sessions={stats['sessions']}/{stats['target_sessions']} "
            f"rate={'n/a' if rate is None else format(rate, '.1%')} "
            f"misses={stats['misses']} ptr_defects={stats['pointer_defects']}"
        )
        if stats["verdict"] == "ESCALATE-HAZARD":
            print("  -> ladder 2: promote the missed hazard to a CI gate or hook. "
                  "NEVER re-inline.")
        elif stats["verdict"] == "ESCALATE-AREA":
            print(f"  -> ladder 3: path-scoped rule for {stats['systematic_areas']}. "
                  "Caveat (plan 7.6): a path-scoped rule is LOST AT COMPACTION.")
        elif stats["verdict"] == "LADDER-1":
            print("  -> ladder 1: add index rows for the missed facts, then re-soak.")
        elif stats["verdict"] == "BET-FAILING":
            print("  -> the relocation bet is failing; revisit owner decision 7 "
                  "(Proposal A skills probe). NEVER re-inline.")
    return 1 if stats["ladder_step"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Pointer-follow soak ledger.")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--ledger", type=Path, default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="append one observation")
    rec.add_argument("--outcome", required=True, choices=OUTCOMES)
    rec.add_argument("--fact", required=True, help="short slug for the fact needed")
    rec.add_argument("--pointer", required=True, help="destination path (+anchor)")
    rec.add_argument("--task", required=True, help="one line: the work in hand")
    rec.add_argument("--area", default=None, help="area slug (drives ladder step 3)")
    rec.add_argument("--class", dest="miss_class", default=None,
                     choices=sorted(MISS_CLASSES))
    rec.add_argument("--session", default=None)
    rec.add_argument("--note", default=None)
    rec.add_argument("--dry-run", action="store_true")
    rec.set_defaults(func=cmd_record)

    rep = sub.add_parser("report", help="render the ledger and the rates")
    rep.add_argument("--json", action="store_true")
    rep.add_argument("--markdown", action="store_true")
    rep.set_defaults(func=cmd_report)

    st = sub.add_parser("status", help="verdict against the fixed thresholds")
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_status)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
