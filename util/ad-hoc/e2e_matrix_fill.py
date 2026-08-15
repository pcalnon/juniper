#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-1 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Bulk-fill the ``status`` column of the canopy E2E click-by-click test
#          matrix from a run's ``statuses.tsv``. Written during the 2026-08-14
#          Phase-1 segment-10 session; the bulk-fill had been deferred every
#          segment since segment 4 and was never scripted.
#
# Why a script and not sed
# ------------------------
# The matrix is NOT one uniform table. Different sections carry different column
# sets -- the C2.4 WS-badge table is ``| row id | # | Badge text | Trigger |
# Colour | mode | status |`` while the M-* tables are ``| row id | control |
# interaction | expected | backend | verify | auto | mode | FA | status |``. So
# the status column has to be located **by header name per table**, never by a
# fixed index. Guessing an index silently writes verdicts into the wrong column.
#
# Scope note: only the ``C2.*`` / ``M-*`` namespaces are table rows with a status
# column. The W-lane verdicts (W3-*, W5-*, W6-*, W11-*) are numbered PROSE steps
# in the matrix and have no status cell to fill; they are reported as
# ``no-matrix-row`` rather than treated as an error.
#
# Usage:
#   python3 util/ad-hoc/e2e_matrix_fill.py --verdicts reports/e2e/<RUN>/statuses.tsv
#   python3 util/ad-hoc/e2e_matrix_fill.py --verdicts <tsv> --write
#   python3 util/ad-hoc/e2e_matrix_fill.py --verdicts <tsv> --write --overwrite
#
# ``--verdicts`` is repeatable and accepts BOTH a run's ``statuses.tsv`` and the
# markdown ``rowlog.md`` an earlier run recorded (``| row | status | evidence |``).
# Sources are consulted in the order given and the FIRST one carrying a verdict
# for a row wins, so pass the newest run first -- an older run must never
# overwrite a later re-drive of the same row.
#
# Default is a DRY RUN (writes nothing). Without --overwrite an already-filled
# status cell is left alone, so a re-run cannot clobber a hand-edited verdict.
#
# Exit codes: 0 ok, 1 nothing matched, 2 misuse / unreadable input.

import argparse
import csv
import re
import sys
from pathlib import Path

DEFAULT_MATRIX = "notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
PLACEHOLDERS = {"", "—", "-", "--", "TBD", "n/a"}
MATRIX_NAMESPACES = ("C2.", "M-")
# A rowlog carries in-progress bookkeeping alongside real verdicts. These are
# NOT terminal values (plan §9) and must never reach a status cell -- a matrix
# reader would take "pending" as a recorded outcome. Matched as a PREFIX, because
# the bookkeeping is usually qualified: "pending demo lane", "pending W14".
NON_VERDICT_PREFIXES = ("pending", "todo", "in progress", "in-progress", "deferred", "not run")

# Run records address rows the way a human writes them: a compressed range
# ("M-TOPOLOGY-01..06,09..18" for one BLOCKED verdict covering fourteen rows)
# and lane-arm suffixes ("M-DATASET-04-L" = the LIVE arm of M-DATASET-04). Both
# forms name real matrix rows; taking the token literally silently drops them.
# Same normalisation the row-coverage mapper (util/ad-hoc/e2e_row_coverage.py)
# already applies, so the two tools agree on what "has a verdict" means.
RANGE_TOKEN_RE = re.compile(r"^([A-Z][A-Za-z0-9.]*(?:-[A-Z0-9]+)*)-(\d+(?:\.\.\d+)?(?:,\d+(?:\.\.\d+)?)*)$")
LANE_SUFFIX_RE = re.compile(r"-(?:L|D)$")


def expand_row_ids(token: str) -> list[str]:
    """Normalise one recorded row token into the matrix row ids it addresses."""
    token = LANE_SUFFIX_RE.sub("", token.strip())
    m = RANGE_TOKEN_RE.match(token)
    if not m:
        return [token] if token else []
    prefix, spec = m.group(1), m.group(2)
    width = len(spec.split("..")[0].split(",")[0])
    out: list[str] = []
    for part in spec.split(","):
        if ".." in part:
            lo_s, hi_s = part.split("..", 1)
            pad = max(width, len(lo_s), len(hi_s))
            out.extend(f"{prefix}-{n:0{pad}d}" for n in range(int(lo_s), int(hi_s) + 1))
        else:
            out.append(f"{prefix}-{int(part):0{max(width, len(part))}d}")
    return out


def is_non_terminal(status: str) -> bool:
    lowered = status.strip().lower()
    return not lowered or lowered.startswith(NON_VERDICT_PREFIXES)


# Markdown escapes a literal pipe inside a cell as ``\|``. Splitting on every
# ``|`` turns one such row into an extra phantom cell, which shifts every index
# past it -- the status verdict then lands in the PREVIOUS column and the status
# cell stays empty. That is exactly what happened to C2.2-04
# ("display:block\|none") in the segment-10 bulk fill.
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")


def split_row(line: str) -> list[str]:
    """Split a markdown table line into its cells (keeping the outer empties).

    Splits on UNESCAPED pipes only; ``\\|`` stays inside its cell.
    """
    return CELL_SPLIT_RE.split(line)


def is_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    body = stripped.strip("|")
    return bool(body) and all(set(c.strip()) <= {"-", ":"} and c.strip() for c in body.split("|"))


def _balanced(text: str) -> str:
    """Trim back to the last point where parentheses are balanced.

    A blind character truncation cuts mid-parenthetical and silently drops the
    trailing finding id -- e.g. 'PASS(request path) / FAIL(status message --
    F-CANOPY-013)' loses the one token a matrix reader most needs. Cutting at the
    last balanced point keeps the cell honest about what it is not showing.
    """
    depth = 0
    last_balanced = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
            if depth == 0:
                last_balanced = i + 1
    if depth == 0:
        return text
    return text[:last_balanced].rstrip(" /-–—") if last_balanced else text


def shorten(status: str, max_len: int) -> str:
    """Keep the matrix cell readable: drop a trailing parenthetical/em-dash rider.

    Never emit a cell whose parentheses are unbalanced -- that is how a finding
    id gets silently amputated.
    """
    status = " ".join(status.split())
    if len(status) <= max_len:
        return status
    # prefer dropping a whole trailing rider over any character truncation
    for sep in (" — ", " -- ", " ("):
        head = status.split(sep, 1)[0].strip()
        if head and len(head) <= max_len and _balanced(head) == head:
            return head
    cut = _balanced(status[:max_len])
    if cut and len(cut) <= max_len:
        return cut + ("…" if len(cut) < len(status) else "")
    return status[: max_len - 1].rstrip() + "…"


def load_tsv_verdicts(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if not reader.fieldnames or "row_id" not in reader.fieldnames:
            raise ValueError(f"{path} has no row_id column")
        return {r["row_id"].strip(): (r.get("status") or "").strip() for r in reader if r.get("row_id")}


def load_rowlog_verdicts(path: Path) -> dict[str, str]:
    """Read an earlier run's markdown rowlog (``| row | status | evidence |``)."""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|") or is_separator(line):
            continue
        # split_row keeps the outer empties: ['', row, status, evidence, '']
        cells = [c.strip() for c in split_row(line)]
        if len(cells) < 4:
            continue
        row_id, status = cells[1], cells[2]
        if not row_id or row_id.lower() in {"row", "row id", "row_id"}:
            continue
        if row_id.startswith(MATRIX_NAMESPACES) and status:
            out.setdefault(row_id, status)
    if not out:
        raise ValueError(f"{path} carried no '| row | status |' verdict rows")
    return out


def load_verdicts(paths: list[Path]) -> tuple[dict[str, str], list[str]]:
    """Merge verdict sources, FIRST source wins, dropping non-terminal values.

    Returns the merged map plus the ids that were seen only as a non-verdict
    (so a caller can say what it deliberately did not fill).
    """
    merged: dict[str, str] = {}
    non_terminal: set[str] = set()
    for path in paths:
        raw = load_rowlog_verdicts(path) if path.suffix.lower() == ".md" else load_tsv_verdicts(path)
        for token, status in raw.items():
            # A lane-arm verdict proves one lane only. Say so in the cell rather
            # than folding "PASS" onto a row whose other arm was never driven.
            lane = LANE_SUFFIX_RE.search(token.strip())
            if lane and not is_non_terminal(status) and "arm" not in status.lower():
                status = f"{status} ({'LIVE' if lane.group(0) == '-L' else 'DEMO'} arm)"
            for row_id in expand_row_ids(token):
                if is_non_terminal(status):
                    non_terminal.add(row_id)
                    continue
                merged.setdefault(row_id, status)
    return merged, sorted(non_terminal - set(merged))


def main() -> int:
    ap = argparse.ArgumentParser(description="Fill the E2E matrix status column from a run's statuses.tsv.")
    ap.add_argument(
        "--verdicts",
        required=True,
        action="append",
        type=Path,
        metavar="TSV_OR_ROWLOG",
        help="verdict source (repeatable; newest run FIRST -- first source carrying a row wins)",
    )
    ap.add_argument("--matrix", type=Path, default=None)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--max-len", type=int, default=44, help="cap on the rendered status cell")
    ap.add_argument("--write", action="store_true", help="apply changes (default is a dry run)")
    ap.add_argument("--overwrite", action="store_true", help="replace an already-filled status cell too")
    args = ap.parse_args()

    matrix = args.matrix or (args.repo_root / DEFAULT_MATRIX)
    try:
        verdicts, non_terminal = load_verdicts(args.verdicts)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    try:
        lines = matrix.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    status_idx: int | None = None
    header_cells: list[str] = []
    filled, skipped_filled, unmatched_rows = [], [], []
    seen_ids: set[str] = set()

    for lineno, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            status_idx = None
            continue
        if is_separator(line):
            # the previous non-separator table line was the header
            for cand in (header_cells,):
                lowered = [c.strip().lower() for c in cand]
                status_idx = lowered.index("status") if "status" in lowered else None
            continue

        cells = split_row(line.rstrip("\n"))
        header_cells = cells
        if status_idx is None or status_idx >= len(cells):
            continue

        row_id = cells[1].strip() if len(cells) > 1 else ""
        if not row_id.startswith(MATRIX_NAMESPACES):
            continue
        seen_ids.add(row_id)
        verdict = verdicts.get(row_id)
        if not verdict:
            unmatched_rows.append(row_id)
            continue

        current = cells[status_idx].strip()
        if current not in PLACEHOLDERS and not args.overwrite:
            skipped_filled.append((row_id, current))
            continue

        new_text = shorten(verdict, args.max_len)
        cells[status_idx] = f" {new_text} "
        new_line = "|".join(cells) + "\n"
        # Structural self-check: a fill may only change ONE cell's text, never
        # the shape of the row. Anything else means the split/join disagreed
        # with the source (the escaped-pipe class) and the verdict is about to
        # land in the wrong column.
        if len(split_row(new_line.rstrip("\n"))) != len(split_row(line.rstrip("\n"))):
            print(f"ERROR: {row_id} would change the row's cell count — refusing", file=sys.stderr)
            return 2
        lines[lineno] = new_line
        filled.append((row_id, new_text))

    print(f"matrix          : {matrix}")
    print(f"verdict sources : {', '.join(str(p) for p in args.verdicts)}")
    print(f"verdict rows    : {len(verdicts)}")
    print(f"matrix table ids: {len(seen_ids)}")
    print(f"filled          : {len(filled)}")
    print(f"already filled  : {len(skipped_filled)} (left alone; use --overwrite to replace)")
    print(f"no verdict yet  : {len(unmatched_rows)}")

    no_matrix_row = sorted(
        rid for rid in verdicts if rid.startswith(MATRIX_NAMESPACES) and rid not in seen_ids
    )
    if no_matrix_row:
        print(f"verdicts with NO matrix row ({len(no_matrix_row)}): {', '.join(no_matrix_row)}")
    w_lane = sorted(rid for rid in verdicts if not rid.startswith(MATRIX_NAMESPACES))
    if w_lane:
        print(f"W-lane / finding verdicts (prose steps, no status cell): {len(w_lane)}")
    if non_terminal:
        print(f"non-terminal, deliberately NOT filled ({len(non_terminal)}): {', '.join(non_terminal)}")

    if filled:
        print("\nfilled rows:")
        for rid, text in filled:
            print(f"  {rid:24s} -> {text}")

    if not filled:
        print("\nnothing to fill")
        return 1

    if args.write:
        matrix.write_text("".join(lines), encoding="utf-8")
        print(f"\nWROTE {matrix}")
    else:
        print("\nDRY RUN — nothing written (pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
