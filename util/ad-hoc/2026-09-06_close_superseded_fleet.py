#!/usr/bin/env python3
"""
Close the cursor PRs a merged carrier superseded -- verifying each class the way it can be verified.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-06
Status: ad-hoc -- migration (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-06_superseded_method_presence.py`, `2026-09-06_docs_residue_audit.py`

Two rules, both bought at a cost:

  1. VERIFY AFTER THE CARRIER MERGES, never against the intent to merge it. ml#1698 was closed in
     a batch whose carriers had merged and whose own presence check had not been re-run; it
     reported 6 of 18 methods present and had to be reopened.
  1b. AND VERIFY AGAINST MAIN'S TREE, not whatever is checked out. The presence checker reads
     `tests/` off the working checkout; run from a carrier branch it finds that carrier's own
     methods and calls them present. Same failure, with the checkout substituted for the
     calendar. This refuses unless `HEAD:tests` and `origin/main:tests` are the same tree.
  2. VERIFY THE CLASS YOU HAVE. A test PR is checkable by METHOD -- the method is what it
     contributes. A docs PR adds no method, so its evidence is the consolidation's own residue
     audit, and the comment says which document holds it rather than asserting completeness.

So this refuses to close a test PR whose methods are not all on the carrier's merged tree, and
requires the carrier to be MERGED before it will act at all.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- fixed argv gh/git invocations, no shell
import sys
from pathlib import Path

REPO = "pcalnon/juniper-ml"
PRESENCE = Path(__file__).with_name("2026-09-06_superseded_method_presence.py")

DOCS_BODY = """Superseded by #{carrier}, which carries this PR's content.

**Verified, not asserted.** #{carrier} merges all 35 remaining `app/cursor` docs PRs by ITEM identity -- a table row keyed on its first cell and its table, a bullet on the path or anchor it names -- and **writes nothing it cannot address**. Every line it declines is printed rather than merged.

That printout is adjudicated in [`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md): across the 35 PRs' 2841 added lines, 26 LANDED from a keyed sibling, 66 are NEAR (the same claim reworded), and **173 (6%) are ABSENT**, listed per PR so the judgement can be re-run rather than taken on trust.

The refusal is the point. A whole-line union cannot tell a new claim from a stale one -- the previous consolidation shipped two superseded security bounds past six green gates -- so this one declines to try and reports instead.

Closing with the work kept."""

METHOD_BODY = """Superseded by #{carrier} -- verified against `origin/main` **after** that carrier merged, not against the intent to merge it.

`util/ad-hoc/2026-09-06_superseded_method_presence.py` reports **{count}**: every test method this branch adds is on `main`.

The check is method-level rather than line-level on purpose. A carrier legitimately rewrites prose -- a wiring comment, a docstring, an `AGENTS.md` entry -- so a line diff over-reports absence; measured on #1629, 16 of 187 lines read as "absent" and every one was comment text while all six test methods were present. The method is what a test PR contributes, so the method is what has to be found.

Closing with the work kept."""


def gh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=180, check=False)


def tests_tree(ref: str) -> str:
    res = subprocess.run(["git", "rev-parse", f"{ref}:tests"], capture_output=True, text=True, timeout=120, check=False)
    return res.stdout.strip()


def checkout_is_main() -> bool:
    """Is this checkout's `tests/` byte-identical to `origin/main`'s?

    The presence checker reads `tests/` off the WORKING CHECKOUT. Run from a carrier branch it
    would find that carrier's own methods and report them "on main" -- ml#1698's failure with
    the checkout substituted for the calendar. The tree hash is the right unit: a commit hash
    would over-refuse on an unrelated docs commit that touched nothing under `tests/`.
    """
    subprocess.run(["git", "fetch", "origin", "main", "--quiet"], capture_output=True, text=True, timeout=300, check=False)
    ours, theirs = tests_tree("HEAD"), tests_tree("origin/main")
    return bool(ours) and ours == theirs


def state(pr: int) -> str:
    res = gh("pr", "view", str(pr), "--repo", REPO, "--json", "state", "--jq", ".state")
    return res.stdout.strip()


def presence(prs: list[int]) -> dict[int, str]:
    """`{pr: "k/m methods present"}` from the presence checker, run against the CURRENT checkout."""
    res = subprocess.run([sys.executable, str(PRESENCE), ".", *[str(p) for p in prs]], capture_output=True, text=True, timeout=1800, check=False)
    out: dict[int, str] = {}
    for line in res.stdout.splitlines():
        if line.startswith(("[OK  ] #", "[MISS] #")):
            head, _, tail = line.partition("#")
            number, _, rest = tail.partition(":")
            out[int(number)] = rest.strip()
            if head.startswith("[MISS"):
                out[int(number)] = "MISS " + out[int(number)]
    return out


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    plan = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    apply = args[1] == "--apply"

    if not checkout_is_main():
        print("REFUSING: this checkout's tests/ differs from origin/main's.")
        print("The presence checker reads tests/ off the working tree, so a carrier branch would")
        print("report its OWN methods as present on main. Check out origin/main and re-run.")
        return 2

    worst = 0
    for carrier_s, group in plan.items():
        carrier = int(carrier_s)
        if state(carrier) != "MERGED":
            print(f"[SKIP ] carrier #{carrier} is {state(carrier)}, not MERGED -- refusing to close its group")
            worst = 1
            continue
        kind, prs = group["kind"], [int(p) for p in group["prs"]]
        measured = presence(prs) if kind == "methods" else {}
        for pr in prs:
            if state(pr) != "OPEN":
                print(f"[skip ] #{pr} already {state(pr)}")
                continue
            if kind == "methods":
                count = measured.get(pr, "")
                if not count or count.startswith("MISS"):
                    print(f"[HOLD ] #{pr}: {count or 'no measurement'} -- NOT closing")
                    worst = 1
                    continue
                body = METHOD_BODY.format(carrier=carrier, count=count)
            else:
                body = DOCS_BODY.format(carrier=carrier)
            if not apply:
                print(f"[dry  ] #{pr} would close (carrier #{carrier}, {kind})")
                continue
            res = gh("pr", "close", str(pr), "--repo", REPO, "--comment", body)
            print(f"[{'closed' if res.returncode == 0 else 'ERROR '}] #{pr}" + ("" if res.returncode == 0 else f" {res.stderr.strip()[:100]}"))
            worst = max(worst, 0 if res.returncode == 0 else 1)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
