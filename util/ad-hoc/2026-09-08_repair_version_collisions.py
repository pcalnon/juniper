#!/usr/bin/env python3
"""2026-09-08_repair_version_collisions.py -- disambiguate doubly-claimed version rows.

Project: juniper-ml
Sub-Project: docs/REFERENCE.md integrity
Application: ad-hoc repair (documentation integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`docs/REFERENCE.md`'s Version History has FOUR doubly-claimed version numbers -- 0.6.19,
0.6.27, 0.6.40 and 0.6.59, eight rows -- an artifact of concurrent PR authorship during
the Cursor-fleet consolidation, where several sessions appended a row without seeing each
other's.

THE OBVIOUS RULE CANNOT BE APPLIED. "Mark the later-DATED row of each pair" fails because
both rows of all four pairs carry the SAME date. Document order is no better: the table is
not sorted (0.6.60 and 0.6.61 precede 0.6.22). Recency had to come from the only record
that holds it -- git. `util/ad-hoc/2026-09-08_version_collision_recency.py` runs
`git log -S` per row; its findings drive the table below.

That measurement also showed the four pairs are not one situation:

  0.6.27  two genuinely different changes; the second landed LATER (#1799, 2026-09-07)
          than the first (#1797, 2026-09-05).  -> suffix the later one
  0.6.59  two genuinely different changes; #1760 (08:56) is later than #1758 (08:14).
          -> suffix the later one
  0.6.19  two genuinely different changes that landed in the SAME commit (#1787). No
          recency exists to recover, so the suffix marks the second-in-document and the
          note says the order is documentary, not chronological.
  0.6.40  NOT two changes. Both rows are "Suite driver operator surface / run_suite.py",
          added by the SAME commit (#1797) -- one change described twice. Suffixing would
          assert a difference that is not there, so the two rows are MERGED into one
          carrying the union of both descriptions.

WHY `+1` AND NOT `.1` OR `-1`

Nothing machine-reads this table (`Version History` appears nowhere in tests/, util/,
.github/ or docs/ outside REFERENCE.md itself), so the format is unconstrained and the
choice is about what a READER infers:

  `0.6.59.1`  a fourth numeric component is not valid SemVer at all.
  `0.6.59-1`  valid SemVer, but a hyphen introduces a PRE-RELEASE, and SemVer orders
              pre-release BEFORE the release: 0.6.59-1 < 0.6.59. A marker meant to say
              "newer" would formally say "older" -- the one genuinely wrong option.
  `0.6.59+1`  valid SemVer BUILD METADATA, explicitly ignored for precedence. Its defined
              meaning is "same version, different build", which is exactly the situation:
              two entries that legitimately share a version number. It asserts no false
              ordering; the Date column and the note carry the rest.

Usage:
    python3 util/ad-hoc/2026-09-08_repair_version_collisions.py [--apply]
"""

from __future__ import annotations

import sys
from pathlib import Path

DOC = Path("docs") / "REFERENCE.md"

NOTE = """> **Four version numbers below are claimed twice** — `0.6.19`, `0.6.27`, `0.6.40` and
> `0.6.59` — because several sessions appended rows concurrently during the 2026-09
> docs-fleet consolidation and none could see the others. The rows are kept as shipped;
> the later of each pair carries a `+N` **SemVer build-metadata** suffix (`0.6.59+1`),
> which is ignored for version precedence and means "same version, different build". It
> deliberately is **not** `-1`, which SemVer reads as a *pre-release* and would order the
> newer row *before* the older one.
>
> Recency came from `git log`, not from this table: **both rows of every pair carry the
> same date.** For `0.6.19` the two rows landed in the *same commit* (#1787), so no
> recency exists — there the suffix marks document order and nothing more. `0.6.40` was
> not a collision at all but one change described twice by one commit (#1797); those two
> rows have been merged. Instrument:
> [`util/ad-hoc/2026-09-08_version_collision_recency.py`](../util/ad-hoc/2026-09-08_version_collision_recency.py).
"""

#: (lineno, old version token, new token, why) -- the LATER row of each genuine pair.
SUFFIXES = [
    (7148, "| 0.6.59  |", "| 0.6.59+1 |", "landed in #1760 (08:56), after #1758 (08:14)"),
    (7156, "| 0.6.27  |", "| 0.6.27+1 |", "landed in #1799 (2026-09-07), after #1797 (2026-09-05)"),
    (7170, "| 0.6.19  |", "| 0.6.19+1 |", "same commit as its pair (#1787) -- document order only"),
]

#: The 0.6.40 duplicate: keep :7165, drop :7179, and widen :7165 to the union.
MERGE_KEEP = 7165
MERGE_DROP = 7179
MERGED_ROW = (
    "| 0.6.40  | 2026-09-04 | Suite driver operator surface (`util/experiments/run_suite.py`): "
    "expansion / resume / `--only` exit, cascor parallel floor, `JUNIPER_EXP_PROJECT_DIR` rebase, "
    "Grafana env toggle, Q-2 flag forwarding. Distinct from gate-input docs #1649 |"
)


def main(argv: "list[str] | None" = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    apply = "--apply" in argv

    lines = DOC.read_text(encoding="utf-8").splitlines()

    def at(n: int) -> str:
        return lines[n - 1]

    # Verify every target before changing anything -- a stale line number must abort.
    for lineno, old, _new, _why in SUFFIXES:
        if not at(lineno).startswith(old):
            print(f"REFUSING {DOC}:{lineno} does not start {old!r}: {at(lineno)[:70]!r}", file=sys.stderr)
            return 2
    for lineno in (MERGE_KEEP, MERGE_DROP):
        if not at(lineno).startswith("| 0.6.40  |"):
            print(f"REFUSING {DOC}:{lineno} is not a 0.6.40 row: {at(lineno)[:70]!r}", file=sys.stderr)
            return 2
    if at(7128) != "## Version History":
        print(f"REFUSING {DOC}:7128 is not the Version History heading: {at(7128)[:70]!r}", file=sys.stderr)
        return 2

    out = list(lines)
    # Descending line order so an earlier edit cannot shift a later target.
    del out[MERGE_DROP - 1]
    print(f"  MERGED     :{MERGE_DROP} into :{MERGE_KEEP}  (one change described twice by #1797)")
    for lineno, old, new, why in sorted(SUFFIXES, key=lambda s: -s[0]):
        out[lineno - 1] = out[lineno - 1].replace(old, new, 1)
        print(f"  SUFFIXED   :{lineno}  {old.strip()} -> {new.strip()}  {why}")
    out[MERGE_KEEP - 1] = MERGED_ROW
    out[7129:7129] = [NOTE.rstrip("\n"), ""]
    print(f"  NOTE       :7130  added under '## Version History'")

    if apply:
        DOC.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\n{'applied' if apply else 'would apply'} 5 change(s)"
          + ("" if apply else "  (dry run -- pass --apply)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
