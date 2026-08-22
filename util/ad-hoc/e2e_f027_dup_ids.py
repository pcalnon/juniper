#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Canopy E2E arc -- F-CANOPY-027 root-cause investigation (duplicate ids)
Author      : Paul Calnon
Version     : 0.1.0
License     : MIT License

Are any component ids DECLARED MORE THAN ONCE in canopy's layout?

Both previous duplicate checks had the same blind spot for exactly the component
type this finding implicates:

  * segment 15 counted DOM nodes with ``querySelectorAll('[id="..."]')`` -- but a
    ``dcc.Store`` renders NO DOM at all, so a duplicated store is invisible to it;
  * ``e2e_f027_layout_audit.py`` collected layout ids into a ``set()``, which
    discards multiplicity by construction.

If a store is declared twice, Dash writes one instance and the consumers read the
other -- which reproduces the F-CANOPY-027 signature exactly: the store "fills"
on the wire, its value changes, and no consumer ever runs.

    cd juniper-canopy/src
    LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        <juniper-ml>/util/ad-hoc/e2e_f027_dup_ids.py

See ``util/ad-hoc/README.md`` for the ad-hoc script convention.
"""

from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.getcwd())


def walk(node, counter, types, depth=0, path="root"):
    if node is None or depth > 300:
        return
    if isinstance(node, (list, tuple)):
        for k, n in enumerate(node):
            walk(n, counter, types, depth + 1, f"{path}[{k}]")
        return
    cid = getattr(node, "id", None)
    if isinstance(cid, str):
        counter[cid] += 1
        types.setdefault(cid, []).append(f"{type(node).__name__}@{path}")
    children = getattr(node, "children", None)
    if children is not None:
        walk(children, counter, types, depth + 1, path + ".children")
    for attr in ("tab_children", "content"):
        sub = getattr(node, attr, None)
        if sub is not None:
            walk(sub, counter, types, depth + 1, f"{path}.{attr}")


def main() -> int:
    import frontend.dashboard_manager as dmmod

    dm = dmmod.DashboardManager({})
    layout = dm.app.layout
    if callable(layout):
        layout = layout()

    counter: Counter = Counter()
    types: dict[str, list[str]] = {}
    walk(layout, counter, types)

    print(f"total id declarations walked: {sum(counter.values())}")
    print(f"distinct ids               : {len(counter)}")
    dups = {k: v for k, v in counter.items() if v > 1}
    print(f"DUPLICATED ids             : {len(dups)}")
    print()
    if not dups:
        print("  (none)")
        return 0
    for cid, n in sorted(dups.items(), key=lambda kv: -kv[1]):
        print(f"  {cid:<52} declared {n}x")
        for where in types[cid][:4]:
            print(f"      {where[:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
