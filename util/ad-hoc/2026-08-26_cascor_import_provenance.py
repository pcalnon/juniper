#!/usr/bin/env python3
"""
Which juniper-cascor tree does a process ACTUALLY import from?

Given a cascor ``src/`` directory, reproduces the import environment the experiment stack
launches uvicorn in (that directory as CWD, so ``''`` leads ``sys.path``) and reports, per
top-level cascor module, the file that resolution really picks -- then classifies each as
resolving inside the requested tree or somewhere else.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation (T6 tail: make experiment_stack.bash worktree-safe)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-26_t6-rebaseline-complete.md;
         util/experiment_stack.bash:112 (``CASCOR_SRC_DIR``, overridable via
         ``JUNIPER_EXP_CASCOR_SRC_DIR`` since ml#1412 -- which THIS probe's result unblocked);
         util/ad-hoc/2026-08-28_ec_cap64_launch.bash (the pin-aware reference launcher)

Why this exists -- and what it FOUND
------------------------------------
Originally: ``experiment_stack.bash`` pinned ``CASCOR_SRC_DIR`` to the PRIMARY checkout, so a
campaign froze that checkout for its whole life and any session running a stack out of it
blocked every campaign. The obvious fix -- run the campaign from a pinned worktree -- was
talked out of on the theory that ``JuniperCascor1``'s editable install would drag imports back
to the primary. That theory was testable, and this was the test.

**The theory was REFUTED, and the header above is written in the past tense for that reason.**
The editable finder registers itself with ``sys.meta_path.append(_EditableFinder)`` -- see
``__editable___juniper_cascor_0_9_0_finder.py:74-76``, where ``append`` is the operative word:
it lands AFTER the default ``PathFinder``, so the launcher's CWD wins and the finder only ever
acts as a fallback. A pinned worktree therefore yields a PURE tree, not a mixed one. ml#1412
then added the ``JUNIPER_EXP_CASCOR_SRC_DIR`` override that makes a pinned launch expressible.

**Run it anyway rather than trusting that result.** The refutation is a fact about one env's
install layout, and a rebuilt env, a different interpreter, or a stray ``PYTHONPATH`` can each
change the answer without announcing it.

What this does NOT retire: the campaign drivers' own freeze logic against the SHARED primary,
and peer GPU/CPU contention holds -- a module-resolution fact says nothing about contention
(a concurrent ``clamscan`` was measured at +6.8% on one cell).

It matters which way it falls, because the failure is SILENT: a stack that reads its git sha
from ``git -C ${CASCOR_SRC_DIR} rev-parse`` reports the worktree's sha in every manifest while
importing whatever resolution actually chose. That is a vacuous check -- it cannot fail. This
probe asks the import system instead of asking the label. For the same reason the run record
cannot stand in for it: a pinned run's ``manifest.json`` carries ``git = {}`` and an
``editable_source`` pointing at the PRIMARY regardless of what actually ran.

Usage
-----
    # MUST be the JuniperCascor1 interpreter -- that is the env cascor experiments run in,
    # and the whole question is what THAT env's import system resolves. Bare ``python3``
    # probes a different env and answers a different question.
    /opt/miniforge3/envs/JuniperCascor1/bin/python3.13 \
        util/ad-hoc/2026-08-26_cascor_import_provenance.py <cascor-src-dir> [--json]

Exit 0 = every probed module resolved inside the requested tree; 1 = at least one did not
(a MIXED tree, which is worse than either pure one); 2 = the directory is unusable.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

#: Top-level names the cascor service imports that the editable finder also maps. `api` is the
#: uvicorn factory's own package; the rest are the ones a training run pulls in underneath it.
PROBE_MODULES = (
    "api",
    "cascor_constants",
    "log_config",
    "utils",
    "candidate_unit",
    "cascade_correlation",
)


def probe(src_dir: Path) -> "list[dict]":
    """Import each probe module with ``src_dir`` leading sys.path; report where each landed."""
    os.chdir(src_dir)
    # uvicorn is launched with src/ as CWD, and CPython puts CWD at sys.path[0] for a script
    # or -c. Reproduce that exactly rather than approximating it with an absolute insert.
    sys.path.insert(0, "")

    rows: "list[dict]" = []
    for name in PROBE_MODULES:
        row: "dict" = {"module": name}
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - any import failure is a finding, not a crash
            row.update({"file": None, "inside": False, "error": f"{type(exc).__name__}: {exc}"})
            rows.append(row)
            continue
        origin = getattr(module, "__file__", None)
        resolved = Path(origin).resolve() if origin else None
        row.update(
            {
                "file": str(resolved) if resolved else None,
                # A namespace package has no __file__; that is not evidence of the wrong tree,
                # so it is reported as such rather than silently counted either way.
                "inside": bool(resolved and resolved.is_relative_to(src_dir)),
                "namespace": origin is None,
                "error": None,
            }
        )
        rows.append(row)
    return rows


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("src_dir", help="a juniper-cascor checkout's src/ directory")
    parser.add_argument("--json", action="store_true", help="emit the rows as JSON")
    args = parser.parse_args(argv)

    src_dir = Path(args.src_dir).expanduser().resolve()
    if not (src_dir / "api").is_dir():
        print(f"ERROR: {src_dir} does not look like a cascor src/ (no api/ under it)", file=sys.stderr)
        return 2

    rows = probe(src_dir)
    if args.json:
        print(json.dumps({"src_dir": str(src_dir), "modules": rows}, indent=2))
    else:
        print(f"requested tree: {src_dir}")
        for row in rows:
            if row["error"]:
                verdict, detail = "ERROR  ", row["error"]
            elif row.get("namespace"):
                verdict, detail = "NAMESPC", "(namespace package -- no __file__)"
            else:
                verdict, detail = ("INSIDE " if row["inside"] else "ELSEWHERE"), row["file"]
            print(f"  {verdict}  {row['module']:20s} {detail}")
        strayed = [r["module"] for r in rows if not r["inside"] and not r.get("namespace") and not r["error"]]
        if strayed:
            print(f"\nMIXED TREE: {', '.join(strayed)} resolved outside the requested tree.")
        else:
            print("\nAll probed modules resolved inside the requested tree.")
    return 0 if all(r["inside"] or r.get("namespace") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
