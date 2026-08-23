#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
License:     MIT License

Extract RETRIEVAL EVIDENCE from a subagent transcript for the pointer-follow soak
(``notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`` §7).

Why this exists
---------------
The protocol scores a probe run on whether the session *demonstrably retrieved*
the fact before acting -- "a correct answer reached without consulting the fact
is still a miss". The evidence for that is the session's tool log, not its final
prose: an agent can state a fact confidently from parametric memory, and that is
a MISS, not a follow.

Reading a transcript into a scoring agent's context would both overflow it and
contaminate the scorer. This prints COUNTS AND PATHS ONLY -- never message text
-- so the scorer sees which files were opened and nothing else.

Usage:
    python3 util/ad-hoc/2026-08-21_soak_probe_evidence.py <agent-id> [<agent-id> ...]
    python3 util/ad-hoc/2026-08-21_soak_probe_evidence.py --path <transcript.jsonl>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

SUBAGENT_DIRS = [
    Path.home() / ".claude/projects"
    / "-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-giggly-marinating-backus"
    / "bf50124e-6fde-4314-bdca-0ca7876b8efb" / "subagents",
]

# The relocation destination. Opening this is the retrieval event under test.
DEST = "docs/REFERENCE.md"

# THE ANSWER KEY. conf/soak_probes.json carries each probe's `fact` and
# `discriminator` verbatim, and it lives inside the repo the subject is
# searching -- so a keyword grep for the probe's own subject matter (e.g.
# "per_run_timeout_seconds") surfaces the answer sheet. Any run that touched it
# is CONTAMINATED and must not be scored as a clean observation. Discovered on
# run 2 of the pilot, by this scorer.
ANSWER_KEY = "conf/soak_probes.json"
# The protocol document also names every fact and the whole measurement design.
PROTOCOL_DOC = "POINTER-FOLLOW-SOAK-LEDGER"

PATH_RE = re.compile(r"[\w./-]+\.(?:md|py|bash|sh|yml|yaml|json|toml|cfg|ini)")


def find_transcript(agent_id: str) -> Path | None:
    for d in SUBAGENT_DIRS:
        p = d / f"agent-{agent_id}.jsonl"
        if p.exists():
            return p
        if d.exists():
            for cand in d.glob(f"*{agent_id}*.jsonl"):
                return cand
    return None


def scan(path: Path) -> dict:
    """Walk the transcript, collecting only tool names and file paths."""
    tools: Counter = Counter()
    files: Counter = Counter()
    dest_hits = 0
    records = 0
    contaminated = [0]
    via_output = [0]

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        records += 1
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Walk the record for tool_use blocks without materialising message text.
        stack = [rec]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if node.get("type") == "tool_use":
                    name = node.get("name") or "?"
                    tools[name] += 1
                    blob = json.dumps(node.get("input") or {})
                    for m in PATH_RE.findall(blob):
                        m = m.lstrip("./")
                        if m.startswith("docs/") or m.startswith("util/") \
                           or m.startswith("tests/") or m.startswith("conf/") \
                           or m.startswith(".github/") or m.endswith("AGENTS.md") \
                           or m.endswith("CLAUDE.md"):
                            files[m] += 1
                    if DEST in blob:
                        dest_hits += 1
                    if ANSWER_KEY in blob or PROTOCOL_DOC in blob:
                        contaminated[0] += 1
                elif node.get("type") == "tool_result":
                    # Scanning only tool INPUTS was a false negative: a
                    # directory-wide `grep -rn <term> docs/` retrieves
                    # REFERENCE.md content without the literal path ever
                    # appearing in the command. Found 2026-08-21 when two runs
                    # cited REFERENCE.md line numbers while the scorer reported
                    # zero refs. tool_result is still tool-layer evidence, NOT
                    # model prose -- an agent merely *mentioning* the file in its
                    # answer must never count as having retrieved it.
                    blob = json.dumps(node.get("content") or "")
                    if DEST in blob:
                        via_output[0] += 1
                    if ANSWER_KEY in blob:
                        contaminated[0] += 1
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

    return {
        "records": records,
        "tool_calls": sum(tools.values()),
        "tools": dict(tools),
        "dest_hits": dest_hits,
        "dest_via_output": via_output[0],
        "retrieved": (dest_hits + via_output[0]) > 0,
        "contaminated": contaminated[0] > 0,
        "contamination_hits": contaminated[0],
        "files": files.most_common(12),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("agent_ids", nargs="*")
    ap.add_argument("--path", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    targets: list[tuple[str, Path]] = []
    if args.path:
        targets.append((args.path.stem, args.path))
    for aid in args.agent_ids:
        p = find_transcript(aid)
        if p is None:
            print(f"{aid}: TRANSCRIPT NOT FOUND", file=sys.stderr)
            continue
        targets.append((aid, p))

    out = {}
    for label, p in targets:
        r = scan(p)
        out[label] = r
        if args.json:
            continue
        verdict = "RETRIEVED docs/REFERENCE.md" if r["retrieved"] else "did NOT open docs/REFERENCE.md"
        flag = "  *** CONTAMINATED: touched the answer key ***" if r["contaminated"] else ""
        print(f"=== {label[:12]} ==={flag}")
        print(f"  records {r['records']}  tool_calls {r['tool_calls']}  -> {verdict} "
              f"(opened={r['dest_hits']} via-search-output={r['dest_via_output']})")
        print(f"  tools {r['tools']}")
        for f, n in r["files"]:
            print(f"    {n:>3}x {f}")
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
