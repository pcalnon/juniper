#!/usr/bin/env python3
"""Census the ``*_full`` family across the ecosystem -- corrected instrument.

Project:     Juniper
Sub-Project: juniper-ecosystem
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data#369; supersedes 2026-09-05_census_full_family.py

Why a v2 exists
---------------
``2026-09-05_census_full_family.py`` is the instrument that was actually run during
this arc, and the round-2 consensus pass established that it under-reported. It is
kept unmodified as the record of what was run; this file is what should have been
run. Two independent defects, either sufficient to hide a real site:

1. **``REPOS`` listed five repositories.** juniper-recurrence, juniper-cascor-client,
   juniper-cascor-worker, juniper-deploy and juniper-slacker were never scanned. The
   design's §9.5.5 claims a census over "the eight active repos"; the instrument saw
   five. ``juniper-recurrence/bench/datasets.py`` -- 24 hard ``*_full`` reads, and a
   crossval route that hardcodes ``split="full"`` -- sat in that blind spot.

2. **``--include`` covered only ``*.py`` and ``*.md``.** Every YAML, JSON and TOML
   declaration of the contract was invisible. That is not hypothetical either:
   ``juniper-ml/prompts/agent_templates/data/ecosystem.yaml:32`` still publishes the
   pre-arc two-way key list and no run of v1 could ever have reported it.

3. **Ecosystem-root files were out of scope entirely.** ``Juniper/AGENTS.md`` is not
   inside any repository, so a per-repo loop cannot see it -- yet it is the
   always-loaded parent agent file, read by every session in every repo, and it
   publishes both the key list and the ``len(...) == len(X_full)`` identity.

The failure class is the one the ecosystem already has a note for: a CORRECT predicate
over an INCOMPLETE site enumeration. The predicate here was never in doubt. Reviewing a
gate's enumeration is a separate act from reviewing its predicate, and only the second
one was done.

A fourth defect, found by running this file
-------------------------------------------
v1 walks the filesystem with ``grep -r``. Widening the include list to YAML/JSON/TOML
made that walk reach into untracked build output and vendored trees, and the run did
not finish in eight minutes. Enumerating with ``git ls-files`` instead is both faster
and *more correct* for a contract census: it sees tracked files only, which is exactly
the set a contract can be declared in. The ``SKIP`` filter that v1 needed becomes
mostly redundant.

What the correction was actually worth
--------------------------------------
Measured 2026-09-05, so the cost of the defect is on record rather than asserted:

- The five-repo scope hid **juniper-recurrence** and nothing else. The other four
  never-scanned repositories -- cascor-client, cascor-worker, deploy, slacker -- have
  **zero** ``*_full`` sites. But juniper-recurrence had three, one of them a route
  that dies outright.
- The py/md-only file scope hid exactly **one** site,
  ``juniper-ml/prompts/agent_templates/data/ecosystem.yaml:32``.
- The per-repo loop hid **two** statements, both in ``Juniper/AGENTS.md`` (`:122` the
  key list, `:130` the length identity) -- the always-loaded parent agent file.

A narrow instrument is not wrong in proportion to how much it misses. It missed six
sites out of a few hundred, and one of them was a permanently-broken API route.

Known false positives -- stated, not silently narrowed
------------------------------------------------------
``PATTERN``'s second alternative, a bare quoted ``full``, exists to catch split-name
allow-lists (``RECURRENCE_SPLITS``, ``delay_product/generator.py``'s emission loop).
It cannot tell those from any other list that happens to contain the word. Measured
false positives in this run:

- ``juniper-deploy/docker-compose.yml`` -- six hits, all ``profiles: ["full", ...]``,
  Docker Compose profiles with no relation to the NPZ contract. A round-1 reviewer
  independently reported juniper-deploy as having **zero** ``_full`` sites; that
  reviewer was right and this instrument is wrong. Reconciling the two is what
  surfaced the class.
- ``juniper-ml/util/requirements_drift_check.py`` -- ``choices=("quick","full","rewrite")``.

The pattern is left as-is deliberately. Tightening it to exclude these would risk
excluding the allow-list sites it exists to find, and a census whose caveats are
written down is more useful than one quietly narrowed until it looks clean.

What this does NOT do
---------------------
It does not distinguish a live read from a retained ad-hoc script or an archived
backup, beyond the ``PROVENANCE`` bucket below. A ``CONSUME`` count is a starting list
for a human, not a work queue.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
from collections import defaultdict

ROOT = pathlib.Path("/home/pcalnon/Development/python/Juniper")

#: All ten repositories, not five. Ordered so the producer tier reads first.
REPOS = (
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-canopy",
    "juniper-recurrence",
    "juniper-deploy",
    "juniper-ml",
    "juniper-slacker",
)

#: Files that belong to the ecosystem rather than to any repository. A per-repo loop
#: cannot reach these, and `AGENTS.md` is the highest-leverage doc site in the arc.
ROOT_FILES = ("AGENTS.md", "CLAUDE.md")

SKIP = re.compile(r"/(\.git|node_modules|htmlcov|\.venv|__pycache__|backups?|juniper-legacy|\.mypy_cache|\.pytest_cache)/")

#: Retained provenance -- real hits, but they are the record of a migration rather
#: than code anyone will run again. Counted separately so they cannot inflate the
#: number that matters.
PROVENANCE = re.compile(r"/util/ad-hoc/|/reports/|/notes/|/prompts/thread-handoff")

#: Any key ending in ``_full``, plus a bare quoted ``full`` (a split-name allow-list).
PATTERN = re.compile(r"\b\w*_full\b|\bfull\b(?=[\"'])")

INCLUDES = ("*.py", "*.md", "*.yaml", "*.yml", "*.json", "*.toml", "*.cfg", "*.txt")

ROLES = ("PRODUCE", "CONSUME", "ASSERT", "PROVENANCE")


def _classify(line: str, path: str) -> str:
    if PROVENANCE.search("/" + path.lstrip("./")):
        return "PROVENANCE"
    name = path.split("/")[-1]
    if "/tests/" in path or "/test_" in path or name.startswith("test_"):
        return "ASSERT"
    if re.search(r"""\[\s*["']\w*_full["']\s*\]\s*=|["']\w*_full["']\s*:""", line):
        return "PRODUCE"
    return "CONSUME"


def _tracked(base: pathlib.Path) -> list[str]:
    """Tracked files of interest. ``git ls-files`` rather than a filesystem walk.

    v1's ``grep -r`` reached into untracked build output and vendored trees; with the
    widened include list it did not finish in eight minutes. A contract can only be
    declared in a tracked file, so this is the correct population as well as the fast
    one.
    """
    proc = subprocess.run(["git", "-C", str(base), "ls-files", "-z"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return []
    suffixes = tuple(pat.lstrip("*") for pat in INCLUDES)
    return [p for p in proc.stdout.split("\0") if p.endswith(suffixes) and not SKIP.search("/" + p)]


def _grep(base: pathlib.Path, targets: list[str]) -> str:
    if not targets:
        return ""
    out = []
    # Chunked so a repo with thousands of tracked files cannot overflow ARG_MAX.
    for i in range(0, len(targets), 400):
        proc = subprocess.run(
            ["grep", "-n", "-E", r"_full\b|[\"']full[\"']", "--", *targets[i : i + 400]],
            cwd=base,
            capture_output=True,
            text=True,
            check=False,
        )
        out.append(proc.stdout)
    return "".join(out)


def main() -> int:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    files: dict[str, set[str]] = defaultdict(set)
    scanned: list[str] = []

    for repo in REPOS:
        base = ROOT / repo
        if not base.is_dir():
            print(f"MISSING repo (not scanned): {repo}", file=sys.stderr)
            continue
        scanned.append(repo)
        for line in _grep(base, _tracked(base)).splitlines():
            path, _, rest = line.partition(":")
            if SKIP.search("/" + path):
                continue
            if not PATTERN.search(rest):
                continue
            role = _classify(rest, path)
            counts[repo][role] += 1
            files[f"{repo}/{role}"].add(path)

    # The ecosystem-root files, which live in no repository.
    present = [f for f in ROOT_FILES if (ROOT / f).is_file()]
    if present:
        scanned.append("<ecosystem root>")
        for line in _grep(ROOT, present).splitlines():
            path, _, rest = line.partition(":")
            if not PATTERN.search(rest):
                continue
            role = _classify(rest, path)
            counts["<ecosystem root>"][role] += 1
            files[f"<ecosystem root>/{role}"].add(path)

    header = f"{'repo':24s} {'PRODUCE':>8s} {'CONSUME':>8s} {'ASSERT':>8s} {'PROV':>6s} {'files':>7s}"
    print(header)
    print("-" * len(header))
    for repo in scanned:
        row = counts[repo]
        n_files = len({p for role in ROLES for p in files[f"{repo}/{role}"]})
        print(f"{repo:24s} {row['PRODUCE']:8d} {row['CONSUME']:8d} {row['ASSERT']:8d} {row['PROVENANCE']:6d} {n_files:7d}")

    print("\nCONSUME sites -- each needs a replacement or a stated reason:")
    for repo in scanned:
        paths = sorted(files[f"{repo}/CONSUME"])
        if not paths:
            print(f"  {repo}: none")
            continue
        for path in paths:
            print(f"  {repo}/{path.lstrip('./')}")

    print(f"\nscanned {len(scanned)} scopes: {', '.join(scanned)}")
    print(f"file types: {' '.join(INCLUDES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
