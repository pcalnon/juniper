#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Census every component id in a live Dash layout, and name the duplicates.

WHY THIS EXISTS -- it lifts a recorded limitation of this arc.

``util/ad-hoc/README.md`` records that a ``dcc.Store`` renders no DOM, so the arc's
store reader resolves ids through dash-renderer's own index at ``state.paths.strs``.
That index maps one id to one path: **it cannot represent a duplicate**, so every
"is the reader looking at the same instance the writer wrote?" question -- the one
F-CANOPY-039's investigation chased and F-CANOPY-035's re-drive left open -- is
structurally unanswerable through it. An instrument that cannot produce a non-zero
answer has not measured anything, so the question needed a different vantage point.

``/<prefix>_dash-layout`` is that vantage point. Dash serves the layout tree as JSON
from the SERVER, before dash-renderer indexes anything, so duplicate ids appear as
what they are: two nodes carrying the same id. Walking it counts every id-bearing
node and reports the multiset, which settles the question either way -- a clean
census is a refutation, not an absence of evidence.

READING THE OUTPUT. ``nodes == distinct`` means no id repeats anywhere in the
layout. For a specific store, the per-instance paths and each instance's declared
default ``data`` are printed, because two instances with different defaults is the
shape that makes a reader and a writer disagree while both are "correct".

CAVEAT, stated because it bounds the claim. This reads the layout as SERVED -- the
initial tree. A component added later by a callback that returns ``children`` would
not appear here. For stores declared in a panel's static layout (which is how every
canopy panel builds them) that distinction does not arise, but a duplicate created
dynamically at runtime would need a different instrument.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-05_dash_layout_id_census.py \\
            --url http://127.0.0.1:8052 --focus metrics-panel-metrics-store
"""

import argparse
import collections
import json
import sys
import urllib.request


def walk(node, path, ids, paths, focus, focus_defaults):
    if isinstance(node, dict):
        props = node.get("props") or {}
        nid = props.get("id")
        if isinstance(nid, str):
            ids[nid] += 1
            paths[nid].append(".".join(path))
            if focus and nid == focus:
                focus_defaults.append(props.get("data"))
        for k, v in props.items():
            walk(v, path + [k], ids, paths, focus, focus_defaults)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + [str(i)], ids, paths, focus, focus_defaults)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://127.0.0.1:8052", help="canopy base URL")
    ap.add_argument("--prefix", default="/dashboard/", help="Dash requests_pathname_prefix")
    ap.add_argument("--focus", default=None, help="report every instance of this id in detail")
    ap.add_argument("--json", default=None, help="write the census here")
    args = ap.parse_args()

    url = f"{args.url.rstrip('/')}{args.prefix}_dash-layout"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:  # noqa: S310
            raw = r.read().decode()
    except Exception as exc:  # noqa: BLE001
        # Report the failure rather than an empty census: "unreadable" is not "clean".
        print(f"UNREADABLE {url}: {exc!r}", file=sys.stderr)
        return 2

    ids: collections.Counter = collections.Counter()
    paths: dict = collections.defaultdict(list)
    focus_defaults: list = []
    walk(json.loads(raw), [], ids, paths, args.focus, focus_defaults)

    dupes = {k: v for k, v in ids.items() if v > 1}
    out = {
        "url": url,
        "bytes": len(raw),
        "id_bearing_nodes": sum(ids.values()),
        "distinct_ids": len(ids),
        "duplicate_ids": {k: {"count": v, "paths": paths[k]} for k, v in sorted(dupes.items())},
    }
    print(f"{url}\n  {len(raw)} bytes, {sum(ids.values())} id-bearing nodes, {len(ids)} distinct")
    print(f"  DUPLICATE ids: {len(dupes)}")
    for k, v in sorted(dupes.items()):
        print(f"    {k} x{v}")
        for p in paths[k]:
            print(f"       {p}")

    if args.focus:
        out["focus"] = {
            "id": args.focus,
            "instances": ids.get(args.focus, 0),
            "paths": paths.get(args.focus, []),
            "defaults": focus_defaults,
        }
        print(f"  focus {args.focus!r}: {ids.get(args.focus, 0)} instance(s)")
        for p, d in zip(paths.get(args.focus, []), focus_defaults):
            print(f"     path={p}\n       default data={d!r}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, default=str)
        print(f"  census -> {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
