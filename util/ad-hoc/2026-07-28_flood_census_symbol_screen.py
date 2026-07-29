"""
AST per-symbol loss-screen for the 2026-07-25..28 Cursor-fleet PR flood.

Builds a symbol inventory for every in-scope test/util file at each touching
merge's main-side parent (<M>^1) and at the current main (+ two heal
waypoints), then classifies every symbol LOST / WEAKENED / DUPLICATED / OK so
a human can adjudicate the candidates against `git log -m -S`.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: agent C1 (flood remediation census)
Created: 2026-07-28
Status: ad-hoc - investigation
Retire when: the Cursor-fleet flood census is closed and its findings healed
Related: 2026-07-26 Cursor Automation fleet incident (memory topic file); PRs #838/#842/#843
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

# ---- config ----------------------------------------------------------------

HEAD = "3915d1e6a7aa7330e5c16f72efefd40ebdf242a9"
WAYPOINT_DF = "df326402395d603e73f5f145886a840cede64a32"  # #843 heal merge (post-heal ref)
WAYPOINT_BD = "bd25e316d1ba15baf6b2b3fde862cf16a06d7b04"  # post-#842 heal
WEAKEN_RATIO = 0.6   # flag when current_lines <= ratio * max_prior_lines
WEAKEN_MIN_DELTA = 4  # ...and the absolute line delta is at least this


def in_scope(path: str) -> bool:
    """tests/*.py (top-level only), util/**/*.py, util/**/*.bash."""
    if path.endswith(".py") and path.startswith("tests/") and "/" not in path[len("tests/"):]:
        return True
    if path.startswith("util/") and (path.endswith(".py") or path.endswith(".bash")):
        return True
    return False


# ---- git helpers -----------------------------------------------------------

def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def blob_sha(ref: str, path: str) -> Optional[str]:
    """Resolve <ref>:<path> to a blob sha, or None if the path is absent there."""
    cp = git("rev-parse", "--verify", "-q", f"{ref}:{path}")
    out = cp.stdout.strip()
    return out if cp.returncode == 0 and out else None


def blob_text(sha: str) -> str:
    cp = git("cat-file", "-p", sha)
    return cp.stdout


# ---- symbol extraction -----------------------------------------------------

@dataclass
class Sym:
    lines: int
    chars: int
    count: int = 1  # occurrences of this id within a single blob (dup detect)


def _seg_len(src: str, node: ast.AST) -> tuple[int, int]:
    try:
        seg = ast.get_source_segment(src, node)
    except Exception:
        seg = None
    if seg is not None:
        return seg.count("\n") + 1, len(seg)
    lo = getattr(node, "lineno", None)
    hi = getattr(node, "end_lineno", None)
    if lo and hi:
        return hi - lo + 1, 0
    return 0, 0


def _add(d: dict[str, Sym], key: str, lines: int, chars: int) -> None:
    if key in d:
        d[key].count += 1
        # keep the larger segment for a duplicated id
        if lines > d[key].lines:
            d[key].lines, d[key].chars = lines, chars
    else:
        d[key] = Sym(lines, chars)


def _walk_class(src: str, cls: ast.ClassDef, prefix: str, out: dict[str, Sym]) -> None:
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ln, ch = _seg_len(src, n)
            _add(out, f"method:{prefix}.{n.name}", ln, ch)
        elif isinstance(n, ast.ClassDef):
            ln, ch = _seg_len(src, n)
            _add(out, f"class:{prefix}.{n.name}", ln, ch)
            _walk_class(src, n, f"{prefix}.{n.name}", out)


def py_symbols(src: str) -> Optional[dict[str, Sym]]:
    """Return None if the blob does not parse (record UNPARSEABLE upstream)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    out: dict[str, Sym] = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ln, ch = _seg_len(src, n)
            _add(out, f"func:{n.name}", ln, ch)
        elif isinstance(n, ast.ClassDef):
            ln, ch = _seg_len(src, n)
            _add(out, f"class:{n.name}", ln, ch)
            _walk_class(src, n, n.name, out)
        elif isinstance(n, ast.Import):
            for a in n.names:
                _add(out, f"import:{a.asname or a.name}", 1, 0)
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                _add(out, f"import:{a.asname or a.name}", 1, 0)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for name in _target_names(t):
                    _add(out, f"const:{name}", 1, 0)
        elif isinstance(n, ast.AnnAssign):
            for name in _target_names(n.target):
                _add(out, f"const:{name}", 1, 0)
    return out


def _target_names(t: ast.AST) -> list[str]:
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, (ast.Tuple, ast.List)):
        names: list[str] = []
        for e in t.elts:
            names.extend(_target_names(e))
        return names
    return []


import re

_BASH_FN = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_-]*)\s*\(\s*\)\s*\{", re.M)
_BASH_FN2 = re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_-]*)\s*(?:\(\s*\))?\s*\{?", re.M)


def bash_symbols(src: str) -> dict[str, Sym]:
    out: dict[str, Sym] = {}
    lines = src.splitlines()
    seen_line: dict[str, int] = {}
    for m in _BASH_FN.finditer(src):
        name = m.group(1)
        _add(out, f"fn:{name}", 1, 0)
        seen_line.setdefault(name, src[: m.start()].count("\n"))
    for m in _BASH_FN2.finditer(src):
        name = m.group(1)
        key = f"fn:{name}"
        if key not in out:
            _add(out, key, 1, 0)
            seen_line.setdefault(name, src[: m.start()].count("\n"))
    # crude body length: distance to next function or EOF (for WEAKENED signal)
    starts = sorted(seen_line.items(), key=lambda kv: kv[1])
    for i, (name, ln) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(lines)
        out[f"fn:{name}"].lines = max(1, end - ln)
    return out


def symbols_for(path: str, sha: str) -> tuple[Optional[dict[str, Sym]], bool]:
    """(symbols, parseable). symbols is None + parseable False for a py SyntaxError."""
    src = blob_text(sha)
    if path.endswith(".bash"):
        return bash_symbols(src), True
    syms = py_symbols(src)
    if syms is None:
        return None, False
    return syms, True


# ---- main analysis ---------------------------------------------------------

@dataclass
class FileReport:
    path: str
    prior_refs: list[str] = field(default_factory=list)  # merge shas whose ^1 we sampled
    blob_by_ref: dict[str, Optional[str]] = field(default_factory=dict)  # ref-label -> blob sha or None
    unparseable_refs: list[str] = field(default_factory=list)
    candidates: list[dict] = field(default_factory=list)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--out", required=True, help="JSON output path")
    args = ap.parse_args()

    with open(args.census) as census_file:
        census = json.load(census_file)
    merges = census["merges"]
    idx_by_sha = {m["sha"]: i for i, m in enumerate(merges)}  # lower i == more recent
    files_by_sha = {m["sha"]: m.get("files", []) for m in merges}

    union = set(census["buckets"]["tests_touching"]) | set(census["buckets"]["util_touching"])

    # file -> set of touching merge shas (restricted to the union set)
    file_merges: dict[str, set[str]] = {}
    excluded_files: set[str] = set()
    for msha in union:
        for f in files_by_sha.get(msha, []):
            if in_scope(f):
                file_merges.setdefault(f, set()).add(msha)
            elif f.startswith("tests/") and f.endswith(".py"):
                excluded_files.add(f)  # tests/ subdir py (out of the tests/*.py glob)

    # dedupe symbol extraction by blob sha
    sym_cache: dict[tuple[str, str], tuple[Optional[dict[str, Sym]], bool]] = {}

    def get_syms(path: str, sha: str):
        key = (path, sha)
        if key not in sym_cache:
            sym_cache[key] = symbols_for(path, sha)
        return sym_cache[key]

    reports: list[FileReport] = []
    stat_blobs: set[str] = set()
    stat_symbol_compares = 0

    for path in sorted(file_merges):
        fr = FileReport(path=path)
        # ordered list of prior refs (most-recent-first)
        prior = sorted(file_merges[path], key=lambda s: idx_by_sha.get(s, 9999))
        fr.prior_refs = prior

        # label -> blob sha (or None)
        ref_labels: list[tuple[str, str]] = []
        for msha in prior:
            ref_labels.append((f"{msha[:9]}^1", f"{msha}^1"))
        ref_labels.append(("df32640", WAYPOINT_DF))
        ref_labels.append(("bd25e31", WAYPOINT_BD))
        ref_labels.append(("HEAD", HEAD))

        # resolve blobs, gather symbol tables
        syms_by_label: dict[str, Optional[dict[str, Sym]]] = {}
        for label, gitref in ref_labels:
            bsha = blob_sha(gitref, path)
            fr.blob_by_ref[label] = bsha
            if bsha is None:
                syms_by_label[label] = None
                continue
            stat_blobs.add(bsha)
            syms, ok = get_syms(path, bsha)
            if not ok:
                fr.unparseable_refs.append(label)
            syms_by_label[label] = syms

        # symbol universe across all refs
        all_ids: set[str] = set()
        for s in syms_by_label.values():
            if s:
                all_ids.update(s.keys())

        cur = syms_by_label.get("HEAD") or {}
        df = syms_by_label.get("df32640") or {}
        prior_labels = [f"{m[:9]}^1" for m in prior]

        for sid in sorted(all_ids):
            stat_symbol_compares += 1
            # max prior segment + which prior ref held the largest / the most-recent-present
            max_prior_lines = 0
            max_prior_label = None
            recent_present_label = None  # most recent prior ref (list is recent-first)
            for lbl in prior_labels:
                s = syms_by_label.get(lbl)
                if s and sid in s:
                    if recent_present_label is None:
                        recent_present_label = lbl
                    if s[sid].lines > max_prior_lines:
                        max_prior_lines = s[sid].lines
                        max_prior_label = lbl
            present_in_any_prior = recent_present_label is not None
            cur_present = sid in cur
            df_present = sid in df

            verdict = None
            detail = {}
            if cur_present and cur[sid].count >= 2:
                verdict = "DUPLICATED"
                detail["cur_count"] = cur[sid].count
            elif present_in_any_prior and not cur_present:
                verdict = "LOST"
                if df_present:
                    verdict = "POST-HEAL-REGRESSION"
            elif cur_present and max_prior_lines and max_prior_label:
                cl = cur[sid].lines
                if cl <= WEAKEN_RATIO * max_prior_lines and (max_prior_lines - cl) >= WEAKEN_MIN_DELTA:
                    verdict = "WEAKENED"
                    detail["cur_lines"] = cl
                    detail["max_prior_lines"] = max_prior_lines
                    detail["ratio"] = round(cl / max_prior_lines, 2)

            if verdict:
                # last-good ref: for LOST use most-recent prior that had it;
                # for WEAKENED use the label with the largest segment.
                if verdict in ("LOST", "POST-HEAL-REGRESSION", "DUPLICATED"):
                    lastgood = recent_present_label
                else:
                    lastgood = max_prior_label
                lastgood_sha = None
                if lastgood:
                    lastgood_sha = lastgood.replace("^1", "")
                fr.candidates.append({
                    "symbol": sid,
                    "verdict": verdict,
                    "last_good_ref": (f"{lastgood_sha}^1:{path}" if lastgood_sha else None),
                    "df_present": df_present,
                    "detail": detail,
                })
        reports.append(fr)

    # ---- emit -------------------------------------------------------------
    out = {
        "head": HEAD,
        "stats": {
            "merges_in_union": len(union),
            "files_screened": len(file_merges),
            "distinct_blobs": len(stat_blobs),
            "symbol_compares": stat_symbol_compares,
            "excluded_tests_subdir_files": sorted(excluded_files),
        },
        "files": [
            {
                "path": fr.path,
                "prior_refs": fr.prior_refs,
                "blob_by_ref": fr.blob_by_ref,
                "unparseable_refs": fr.unparseable_refs,
                "candidates": fr.candidates,
            }
            for fr in reports
        ],
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    json.dump(out, open(args.out, "w"), indent=1)

    # human summary
    total_c = sum(len(fr.candidates) for fr in reports)
    by_verdict: dict[str, int] = {}
    for fr in reports:
        for c in fr.candidates:
            by_verdict[c["verdict"]] = by_verdict.get(c["verdict"], 0) + 1
    print("=== flood census symbol screen ===")
    print(f"merges(union)={len(union)} files={len(file_merges)} "
          f"blobs={len(stat_blobs)} symbol_compares={stat_symbol_compares}")
    print(f"candidates total={total_c} by_verdict={by_verdict}")
    if out["stats"]["excluded_tests_subdir_files"]:
        print("excluded tests/ subdir py:", out["stats"]["excluded_tests_subdir_files"])
    print()
    for fr in reports:
        if fr.candidates or fr.unparseable_refs:
            print(f"--- {fr.path}  (priors={len(fr.prior_refs)}, unparseable={fr.unparseable_refs})")
            for c in fr.candidates:
                print(f"    [{c['verdict']}] {c['symbol']}  last_good={c['last_good_ref']}  {c['detail']}")
    print(f"\nJSON -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
