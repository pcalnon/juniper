#!/usr/bin/env python3
"""Split an open-PR set into the cohorts the flood disposition acts on.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc analysis (Cursor-fleet flood disposition)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- analysis
Retire when: the fleet stops producing floods, or the census tool grows this view.
Related:     util/ad-hoc/2026-09-04_fleet_flood2_census.py (contention histogram),
             util/ad-hoc/2026-09-05_fleet_docs_consolidate.py (acts on DOCS-ONLY),
             util/ad-hoc/2026-09-05_fleet_provably_clean.py (acts on CODE).

WHY A SEPARATE VIEW

The census reports counts per category; the disposition needs the actual PR
NUMBERS per cohort, because the three cohorts get three different treatments:

  DOCS-ONLY  -> consolidate into one branch (they collide only on version
                headers, which carry nothing that survives consolidation)
  CODE       -> screen individually with predict_merge / provably_clean; a code
                PR is never folded into a docs consolidation
  OTHER      -> notes-only or unclassified; read by hand

"Contended" is the five files the census measures as touched by many PRs. A PR
that edits ONLY those, and no code, is consolidatable by construction.

Usage
-----
    gh pr list --repo pcalnon/juniper-ml --limit 300 \
        --json number,title,headRefName,isDraft,files > ml_files.json
    python3 util/ad-hoc/2026-09-05_fleet_cohort_split.py --dump ml_files.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONTENDED = {
    "docs/REFERENCE.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/QUICK_START.md",
    "util/ad-hoc/README.md",
}
CODE_SUFFIX = (".py", ".bash", ".sh", ".yml", ".yaml", ".toml", ".cfg", ".ini")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    prs = json.loads(args.dump.read_text())
    docs_only, code, other = [], [], []
    for p in prs:
        paths = [f["path"] for f in p.get("files", [])]
        has_code = any(x.endswith(CODE_SUFFIX) for x in paths)
        touches_contended = any(x in CONTENDED for x in paths)
        if has_code:
            code.append(p)
        elif touches_contended:
            docs_only.append(p)
        else:
            other.append(p)

    if args.json:
        json.dump(
            {
                "docs_only": [p["number"] for p in docs_only],
                "code": [p["number"] for p in code],
                "other": [p["number"] for p in other],
            },
            sys.stdout,
            indent=1,
        )
        print()
        return 0

    for label, group in (("DOCS-ONLY (consolidate)", docs_only), ("CODE (screen individually)", code), ("OTHER (read by hand)", other)):
        print(f"\n=== {label}: {len(group)} ===")
        for p in sorted(group, key=lambda x: x["number"]):
            flag = "draft" if p.get("isDraft") else "READY"
            print(f"  #{p['number']} {flag}  {p['title'][:74]}")
    print(f"\ntotal {len(prs)}  docs-only {len(docs_only)}  code {len(code)}  other {len(other)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
