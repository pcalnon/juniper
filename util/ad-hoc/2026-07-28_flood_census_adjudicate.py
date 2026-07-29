"""
Adjudicator for the flood-census symbol candidates.

For every LOST/WEAKENED/DUPLICATED candidate emitted by
2026-07-28_flood_census_symbol_screen.py, walk main's FIRST-PARENT lineage
(git log --first-parent -S<leaf>, which -- unlike plain -S -- catches a
deletion that happened inside a merge resolution of main-side content) to find
the exact commit that removed the symbol, classify it MERGE vs non-merge, and
detect an in-place rename (an equivalent same-kind symbol added in the same
commit). Verdict:

  INTENTIONAL       removal in a non-merge commit (a PR's own work), OR a merge
                    that simultaneously added same-kind replacement symbols
                    (rewrite / rename).
  LOST-IN-MERGE     symbol present on the main-side (first) parent, absent in a
                    merge commit, with no same-kind replacement -> real finding.
  NO-MAIN-TRANSITION  never left main's first-parent lineage via a clean drop.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: agent C1 (flood remediation census)
Created: 2026-07-28
Status: ad-hoc - investigation
Retire when: the Cursor-fleet flood census is closed
Related: 2026-07-26 Cursor Automation fleet incident; PRs #838/#842/#843
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HEAD = "3915d1e6a7aa7330e5c16f72efefd40ebdf242a9"

# import the screen module for its AST extraction
_screen_path = Path(__file__).with_name("2026-07-28_flood_census_symbol_screen.py")
_spec = importlib.util.spec_from_file_location("flood_screen", _screen_path)
screen = importlib.util.module_from_spec(_spec)
sys.modules["flood_screen"] = screen  # dataclass resolution needs it registered
_spec.loader.exec_module(screen)


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True)


_parse_cache: dict[tuple[str, str], dict] = {}


def symbols_at(rev: str, path: str) -> dict:
    bsha = screen.blob_sha(rev, path)
    if bsha is None:
        return {}
    key = (path, bsha)
    if key not in _parse_cache:
        syms, ok = screen.symbols_for(path, bsha)
        _parse_cache[key] = syms if (ok and syms) else {}
    return _parse_cache[key]


def leaf_of(symbol: str) -> str:
    _, qual = symbol.split(":", 1)
    return qual.split(".")[-1]


def kind_of(symbol: str) -> str:
    return symbol.split(":", 1)[0]


def parents(sha: str) -> list[str]:
    out = git("rev-list", "--parents", "-n1", sha).stdout.split()
    return out[1:] if len(out) > 1 else []


def census_pr_map():
    sp = ("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/"
          "a75ce638-5880-486b-b2e8-88f88fc42771/scratchpad/flood_census_universe.json")
    with open(sp) as f:
        d = json.load(f)
    return {m["sha"]: m["pr"] for m in d["merges"]}


def adjudicate(path: str, symbol: str) -> dict:
    leaf = leaf_of(symbol)
    kind = kind_of(symbol)
    cp = git("log", "--first-parent", "--format=%H", f"-S{leaf}", HEAD, "--", path)
    commits = [c for c in cp.stdout.split() if c]
    res = {"symbol": symbol, "path": path, "transition": None, "is_merge": None,
           "had_main_side": None, "rename_targets": [], "verdict": "NO-MAIN-TRANSITION",
           "subject": None}
    for c in commits:  # newest -> oldest
        pres_c = symbol in symbols_at(c, path)
        ps = parents(c)
        if not ps:
            continue
        main_parent = ps[0]
        pres_mp = symbol in symbols_at(main_parent, path)
        if (not pres_c) and pres_mp:
            res["transition"] = c
            res["is_merge"] = len(ps) >= 2
            res["had_main_side"] = True
            res["subject"] = git("log", "-1", "--format=%s", c).stdout.strip()
            sc = symbols_at(c, path)
            smp = symbols_at(main_parent, path)
            if kind in ("class", "func", "method"):
                res["rename_targets"] = sorted(
                    s for s in sc if s not in smp and kind_of(s) == kind)
            if not res["is_merge"]:
                res["verdict"] = "INTENTIONAL"
            else:
                res["verdict"] = ("INTENTIONAL" if res["rename_targets"]
                                  else "LOST-IN-MERGE")
            return res
    return res


def main() -> int:
    screen_json = sys.argv[1]
    with open(screen_json) as f:
        data = json.load(f)
    data = json.load(open(screen_json))
    pr_map = census_pr_map()
    results = []
    for fr in data["files"]:
        path = fr["path"]
        for c in fr["candidates"]:
            r = adjudicate(path, c["symbol"])
            r["screen_verdict"] = c["verdict"]
            r["last_good_ref"] = c["last_good_ref"]
            if r["transition"]:
                r["transition_pr"] = pr_map.get(r["transition"])
            results.append(r)
    by_v = {}
    for r in results:
    with open(out_json, "w") as f:
        json.dump({"results": results, "summary": by_v}, f, indent=1)
    json.dump({"results": results, "summary": by_v}, open(out_json, "w"), indent=1)
    print("=== adjudication summary ===")
    print("by verdict:", by_v)
    print()
    interesting = [r for r in results if r["verdict"] != "INTENTIONAL"]
    print(f"--- {len(interesting)} candidates NOT cleanly INTENTIONAL ---")
    for r in interesting:
        pr = r.get("transition_pr")
        tr = (r["transition"][:9] if r["transition"] else None)
        print(f"[{r['verdict']}] {r['path']}::{r['symbol']}")
        print(f"      transition={tr} pr=#{pr} is_merge={r['is_merge']} "
              f"subject={r['subject']!r}")
        if r["rename_targets"]:
            print(f"      rename_targets={r['rename_targets']}")
    print("\n--- sample INTENTIONAL (rename/rewrite) proofs ---")
    shown = 0
    for r in results:
        if r["verdict"] == "INTENTIONAL" and r["rename_targets"] and shown < 10:
            print(f"[INTENTIONAL] {r['path']}::{r['symbol']} -> merge={r['is_merge']} "
                  f"pr=#{r.get('transition_pr')} added={r['rename_targets'][:3]}")
            shown += 1
    print(f"\nJSON -> {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
