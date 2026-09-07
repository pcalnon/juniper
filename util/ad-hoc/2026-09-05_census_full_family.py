#!/usr/bin/env python3
"""Census the ``*_full`` family across the ecosystem before removing it.

Project:     Juniper
Sub-Project: juniper-ecosystem
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     partition arc decision 11; design JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md 9.5

Decision 11 drops ``X_full`` / ``y_full`` and their per-key siblings from the NPZ
contract. The design's own §9.5.1 list of affected sites was known to be incomplete
before this arc started -- it named none of ``juniper_data_client/contract.py``'s
tabular-vs-sequence dispatch, ``testing/generators.py``, or ``testing/fake_client.py``,
all of which produce or consume the family.

So the removal starts from a measured census rather than that list. Counts are split by
ROLE, because the three have different removal costs:

* PRODUCE -- a generator or fake writes the key. Deleting the write is the change.
* CONSUME -- something reads it. Each read needs a replacement or a reason.
* ASSERT  -- a test pins it. These fall out once the other two are done.

Output is a table, not a verdict: the point is to make the size of the job visible
before any of it is done.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
from collections import defaultdict

ROOT = pathlib.Path("/home/pcalnon/Development/python/Juniper")
REPOS = ("juniper-data", "juniper-data-client", "juniper-cascor", "juniper-canopy", "juniper-ml")
SKIP = re.compile(r"/(\.git|node_modules|htmlcov|\.venv|__pycache__|backups?|juniper-legacy)/")

#: Any key ending in ``_full``, plus the bare names.
PATTERN = re.compile(r"\b\w*_full\b|\bfull\b(?=[\"'])")


def _classify(line: str, path: str) -> str:
    if "/tests/" in path or "/test_" in path or path.split("/")[-1].startswith("test_"):
        return "ASSERT"
    if re.search(r"""\[\s*["']\w*_full["']\s*\]\s*=|["']\w*_full["']\s*:""", line):
        return "PRODUCE"
    return "CONSUME"


def main() -> int:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    files: dict[str, set[str]] = defaultdict(set)

    for repo in REPOS:
        base = ROOT / repo
        if not base.is_dir():
            print(f"missing repo: {repo}", file=sys.stderr)
            continue
        try:
            out = subprocess.run(
                ["grep", "-rn", "--include=*.py", "--include=*.md", "-E", r"_full\b", "."],
                cwd=base,
                capture_output=True,
                text=True,
                check=False,
            ).stdout
        except OSError as exc:  # pragma: no cover - environment problem, not a finding
            print(f"{repo}: {exc}", file=sys.stderr)
            continue
        for line in out.splitlines():
            path, _, rest = line.partition(":")
            if SKIP.search("/" + path):
                continue
            if not PATTERN.search(rest):
                continue
            role = _classify(rest, path)
            counts[repo][role] += 1
            files[f"{repo}/{role}"].add(path)

    print(f"{'repo':22s} {'PRODUCE':>8s} {'CONSUME':>8s} {'ASSERT':>8s} {'files':>7s}")
    for repo in REPOS:
        row = counts[repo]
        n_files = len({p for role in ("PRODUCE", "CONSUME", "ASSERT") for p in files[f"{repo}/{role}"]})
        print(f"{repo:22s} {row['PRODUCE']:8d} {row['CONSUME']:8d} {row['ASSERT']:8d} {n_files:7d}")

    print("\nCONSUME sites (each needs a replacement or a reason):")
    for repo in REPOS:
        for path in sorted(files[f"{repo}/CONSUME"]):
            print(f"  {repo}/{path.lstrip('./')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
