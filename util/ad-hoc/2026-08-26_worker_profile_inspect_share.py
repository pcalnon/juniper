#!/usr/bin/env python3
"""Share of candidate-worker self time by source file, for a cProfile corpus (cascor#579).

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-26
Status:      ad-hoc -- one-off (cascor#579: is the post-#563 worker still dominated by `inspect`?)
Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline). Previously: cascor#579 is
             closed with the share posted; delete then.
Related:     util/ad-hoc/2026-08-23_h2h_worker_profile_diff.py (per-function A/B diff of two corpora);
             JUNIPER_CASCOR_WORKER_PROFILE (cascor#567) writes the .prof files this reads.

WHY THIS EXISTS
cascor#579's acceptance is a SHARE: "inspect.getmodule / getsourcefile frames < 5 % of worker self
time". The per-function diff shows call-count collapses but not a share, and pstats' default sort
mixes the inspect machinery across a dozen callees (inspect.py, linecache.py, posixpath.py,
posix.stat, hasattr storms). This aggregates tottime per source FILE across every .prof in a
directory and reports the inspect family (inspect.py + linecache.py + posixpath.py + genericpath.py
+ tokenize.py) as one share, alongside the top files, so pre- and post-#563 corpora can be compared
like for like. cProfile is for attribution, never timing (handoff 2026-08-24 section 1.6).

Usage: 2026-08-26_worker_profile_inspect_share.py <LABEL> <PROF_DIR> [<LABEL> <PROF_DIR> ...] [--top N]
Exit:  0 report printed; 2 usage error / no .prof files.
"""

from __future__ import annotations

import pstats
import sys
from collections import defaultdict
from pathlib import Path

INSPECT_FAMILY = ("inspect.py", "linecache.py", "posixpath.py", "genericpath.py", "tokenize.py", "<frozen posixpath>", "<frozen genericpath>")


def file_key(path: str) -> str:
    if path.startswith("~") or path.startswith("<"):
        return path  # built-ins: '~' ; frozen modules: '<frozen …>'
    p = Path(path)
    parts = p.parts
    # keep the last two components for readability (pkg/module.py)
    return "/".join(parts[-2:]) if len(parts) >= 2 else p.name


def corpus_share(prof_dir: Path) -> tuple[float, dict[str, float], dict[str, float], int]:
    files = sorted(prof_dir.glob("*.prof"))
    if not files:
        return 0.0, {}, {}, 0
    per_file: dict[str, float] = defaultdict(float)
    per_func: dict[str, float] = defaultdict(float)
    total = 0.0
    for f in files:
        st = pstats.Stats(str(f))
        for (filename, lineno, funcname), (_cc, _nc, tottime, _ct, _callers) in st.stats.items():
            total += tottime
            per_file[file_key(filename)] += tottime
            per_func[f"{file_key(filename)}:{lineno}({funcname})"] += tottime
    return total, dict(per_file), dict(per_func), len(files)


def main(argv: list[str]) -> int:
    top = 12
    if "--top" in argv:
        i = argv.index("--top")
        top = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 2 or len(argv) % 2:
        print(__doc__.split("Usage:")[1].split("\n")[0].strip(), file=sys.stderr)
        return 2
    pairs = [(argv[i], Path(argv[i + 1]).expanduser()) for i in range(0, len(argv), 2)]
    for label, prof_dir in pairs:
        total, per_file, per_func, n = corpus_share(prof_dir)
        if not n:
            print(f"{label}: no .prof files under {prof_dir}", file=sys.stderr)
            return 2
        inspect_t = sum(t for k, t in per_file.items() if any(k.endswith(fam) or k == fam for fam in INSPECT_FAMILY))
        builtin_t = per_file.get("~", 0.0)
        print(f"== {label}: {n} profiles under {prof_dir}")
        print(f"   total self time {total:10.2f} s")
        print(f"   inspect family  {inspect_t:10.2f} s  = {100.0 * inspect_t / total:6.2f} %   ({', '.join(INSPECT_FAMILY[:5])})")
        print(f"   built-ins ('~') {builtin_t:10.2f} s  = {100.0 * builtin_t / total:6.2f} %   (hasattr/isinstance/dict.get storms live here when inspect dominates)")
        print(f"   top {top} files by self time:")
        for k, t in sorted(per_file.items(), key=lambda kv: -kv[1])[:top]:
            print(f"     {100.0 * t / total:6.2f} %  {t:9.2f} s  {k}")
        print(f"   top {top} functions by self time:")
        for k, t in sorted(per_func.items(), key=lambda kv: -kv[1])[:top]:
            print(f"     {100.0 * t / total:6.2f} %  {t:9.2f} s  {k}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
