#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``MEMORY.md`` index gate -- enforcement option A of
``notes/JUNIPER_2026-08-24_JUNIPER-ML_MEMORY-INDEX-RUNWAY-AND-ENFORCEMENT-OPTIONS.md``.

Why this exists
---------------
``MEMORY.md`` is loaded into every session and truncates **silently, newest-first**
at 200 lines / 25,000 bytes. Nothing measured it. Over the first measured window
(2026-08-19 -> 2026-08-24) it grew ~2.6x faster than the plan assumed, and the
projected runway fell from ~32 days to single digits.

No rate is quoted here on purpose. It moved twice while this file was being
written, and a transcribed number in a docstring is exactly the stale figure the
rest of this arc kept tripping over. **The tool computes the current rate from
``history`` and prints it; that output is the number.**

**The flow is the whole problem.** At any observed rate the entire cap is under
40 days, so no eviction, trim or rewrite buys more than that *starting from an
empty file*. Only governing what goes IN moves the date.

The forward-only cap, and why it is on the HOOK
-----------------------------------------------
Owner decision #4 is "120 bytes on NEW entries only; existing rows are not
rewritten". Measured against the real corpus, a **whole-line** 120-byte budget is
unwritable: the link part alone (``- [Title](file.md)``) averages 90 bytes and
reaches 115, and the memory-file slug convention makes it incompressible. The
**hook** -- everything after the link -- has a median of 45 bytes, and only 6 of
137 rows exceed 120. So the cap binds the hook. Same intent; the only reading that
can be satisfied.

How "NEW" is decided without any history
----------------------------------------
``MEMORY.md`` lives outside every repo and has **no git history**, which is why the
growth figures above had to be reconstructed from a plan document rather than
measured. This tool carries its own baseline: ``conf/memory_index_baseline.json``
records the slugs already present, and any row whose slug is absent is NEW and must
satisfy the hook cap. ``--accept`` grandfathers what is there now and appends a
``(date, rows, bytes)`` sample -- so running it also builds the growth series that
did not exist.

Fails CLOSED
------------
A missing memory file is exit 2, not a silent pass: this repo has a documented
class where a check's machinery breaks and it reports SUCCESS. Pass
``--skip-if-absent`` for hosts that legitimately have no memory file (CI cannot
reach it at all), and the skip is announced.

Usage:
    python3 util/memory_index_check.py                     # check
    python3 util/memory_index_check.py --json
    python3 util/memory_index_check.py --advisory          # report, always exit 0
    python3 util/memory_index_check.py --accept            # grandfather + sample

Exit: 0 pass (or advisory/skipped) / 1 violation / 2 misuse or broken machinery.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

# The shipped hard limits. Exceeding EITHER truncates the file silently,
# newest-first -- the newest rows being exactly the ones a session just learned.
HARD_MAX_LINES = 200
HARD_MAX_BYTES = 25000

# Owner decision #4, applied to the HOOK (see the module docstring).
DEFAULT_HOOK_MAX = 120

# Warn before the cliff rather than at it.
WARN_FRACTION = 0.85

DEFAULT_BASELINE = Path("conf/memory_index_baseline.json")

# `- [Title](slug.md) — hook text`
ROW_RE = re.compile(r"^- \[(?P<title>[^\]]*)\]\((?P<slug>[^)]*)\)(?P<hook>.*)$")


class IndexError_(RuntimeError):
    """Machinery failure -- never degrade this to a pass."""


def repo_root(start: Path) -> Path:
    try:
        p = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return start
    return Path(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip() else start


def default_memory_file(root: Path) -> Path:
    """Where Claude Code keeps this project's memory index.

    The directory is the project path with separators replaced by ``-``. A
    worktree must resolve to the MAIN checkout's path, or every worktree would
    look at a different (nonexistent) index.
    """
    main = root
    try:
        p = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        if p.returncode == 0 and p.stdout.strip():
            main = Path(p.stdout.strip()).parent
    except OSError:
        pass
    slug = str(main).replace("/", "-")
    return Path.home() / ".claude" / "projects" / slug / "memory" / "MEMORY.md"


def load_baseline(path: Path) -> dict:
    if not path.is_file():
        return {"slugs": [], "history": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IndexError_(f"baseline unreadable: {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("slugs"), list):
        raise IndexError_(f"baseline malformed (expected an object with a slugs list): {path}")
    data.setdefault("history", [])
    return data


def parse_rows(text: str) -> list[dict]:
    rows = []
    for n, line in enumerate(text.splitlines(), 1):
        m = ROW_RE.match(line)
        if not m:
            continue
        rows.append(
            {
                "line": n,
                "slug": m.group("slug"),
                "title": m.group("title"),
                "hook": m.group("hook"),
                "hook_len": len(m.group("hook")),
                "line_len": len(line),
            }
        )
    return rows


def runway_days(history: list[dict], headroom: int) -> float | None:
    """Bytes/day from the two most recent samples, and the days that leaves.

    Two samples is deliberately the minimum: the file has no history, so a
    long series only exists once this tool has been run repeatedly.
    """
    usable = [h for h in history if isinstance(h.get("bytes"), int) and h.get("date")]
    if len(usable) < 2:
        return None
    a, b = usable[-2], usable[-1]
    try:
        span = (date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days
    except ValueError:
        return None
    if span <= 0:
        return None
    rate = (b["bytes"] - a["bytes"]) / span
    if rate <= 0:
        return float("inf")
    return headroom / rate


def evaluate(memory_text: str, baseline: dict, hook_max: int) -> dict:
    rows = parse_rows(memory_text)
    n_lines = len(memory_text.splitlines())
    n_bytes = len(memory_text.encode("utf-8"))
    known = set(baseline.get("slugs") or [])

    new_rows = [r for r in rows if r["slug"] not in known]
    oversize_new = [r for r in new_rows if r["hook_len"] > hook_max]

    return {
        "lines": n_lines,
        "bytes": n_bytes,
        "rows": len(rows),
        "max_lines": HARD_MAX_LINES,
        "max_bytes": HARD_MAX_BYTES,
        "line_headroom": HARD_MAX_LINES - n_lines,
        "byte_headroom": HARD_MAX_BYTES - n_bytes,
        "over_hard_cap": n_lines > HARD_MAX_LINES or n_bytes > HARD_MAX_BYTES,
        "near_hard_cap": n_bytes > HARD_MAX_BYTES * WARN_FRACTION or n_lines > HARD_MAX_LINES * WARN_FRACTION,
        "new_rows": len(new_rows),
        "oversize_new": oversize_new,
        "hook_max": hook_max,
        "runway_days": runway_days(baseline.get("history") or [], HARD_MAX_BYTES - n_bytes),
    }


def _accept(baseline_path: Path, baseline: dict, rows: list[dict], st: dict) -> None:
    """Grandfather every current slug and append one growth sample."""
    slugs = sorted({*(baseline.get("slugs") or []), *(r["slug"] for r in rows)})
    history = list(baseline.get("history") or [])
    today = date.today().isoformat()
    history = [h for h in history if h.get("date") != today]
    history.append({"date": today, "rows": st["rows"], "lines": st["lines"], "bytes": st["bytes"]})
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps({"slugs": slugs, "history": history}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--memory-file", type=Path, default=None)
    ap.add_argument("--baseline", type=Path, default=None)
    ap.add_argument("--hook-max", type=int, default=DEFAULT_HOOK_MAX)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--advisory", action="store_true", help="report, always exit 0")
    ap.add_argument("--accept", action="store_true", help="grandfather current rows + record a growth sample")
    ap.add_argument("--skip-if-absent", action="store_true", help="exit 0 when there is no memory file (CI cannot reach it)")
    args = ap.parse_args()

    root = (args.repo_root or repo_root(Path.cwd())).resolve()
    memory_file = args.memory_file or default_memory_file(root)
    baseline_path = args.baseline or (root / DEFAULT_BASELINE)

    if not memory_file.is_file():
        # Fails CLOSED by default: a check that cannot find its subject and
        # reports success is the vacuous-pass class this repo keeps re-finding.
        if args.skip_if_absent:
            print(f"SKIPPED: no memory index at {memory_file} (--skip-if-absent)")
            return 0
        print(f"::error::memory index not found: {memory_file}", file=sys.stderr)
        print("        pass --memory-file, or --skip-if-absent on a host that has none", file=sys.stderr)
        return 2

    try:
        text = memory_file.read_text(encoding="utf-8")
        baseline = load_baseline(baseline_path)
    except (OSError, IndexError_) as exc:
        print(f"::error::memory-index machinery failure: {exc}", file=sys.stderr)
        return 2

    st = evaluate(text, baseline, args.hook_max)

    if args.accept:
        _accept(baseline_path, baseline, parse_rows(text), st)
        print(f"accepted {st['rows']} slugs into {baseline_path}; recorded {st['bytes']} bytes at {date.today().isoformat()}")
        return 0

    if args.json:
        printable = dict(st)
        printable["oversize_new"] = [{k: v for k, v in r.items() if k != "hook"} for r in st["oversize_new"]]
        print(json.dumps(printable, indent=2, sort_keys=True))
    else:
        print("=== MEMORY.md index budget ===")
        rw = st["runway_days"]
        rw_s = "n/a (need 2+ samples; run --accept)" if rw is None else ("no growth" if rw == float("inf") else f"{rw:.1f} days")
        print(f"  lines  {st['lines']:>6} / {st['max_lines']}   headroom {st['line_headroom']}")
        print(f"  bytes  {st['bytes']:>6} / {st['max_bytes']}   headroom {st['byte_headroom']}   runway {rw_s}")
        print(f"  rows   {st['rows']:>6}   new since baseline {st['new_rows']}")
        if st["over_hard_cap"]:
            print("::error::OVER THE HARD CAP -- the index is being truncated SILENTLY, newest-first")
        elif st["near_hard_cap"]:
            print(f"::warning::within {int((1 - WARN_FRACTION) * 100)}% of the hard cap; the flow is the lever, not eviction")
        for r in st["oversize_new"]:
            print(f"::error::line {r['line']}: NEW row hook is {r['hook_len']}B > {st['hook_max']}B -- {r['slug']}")
        if st["oversize_new"]:
            print("        the cap is on the HOOK (text after the link), not the whole line.")
            print("        Shorten the hook, or run --accept if this row is deliberately grandfathered.")
        if not st["over_hard_cap"] and not st["oversize_new"]:
            print("OK: within the hard caps, and every new row respects the hook budget.")

    if args.advisory:
        return 0
    return 1 if (st["over_hard_cap"] or st["oversize_new"]) else 0


if __name__ == "__main__":
    sys.exit(main())
