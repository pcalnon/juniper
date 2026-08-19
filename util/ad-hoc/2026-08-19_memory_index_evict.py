#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
License:     MIT License

P0 of the shared-session-memory plan: evict CLOSED / RESOLVED / COMPLETE index
rows from the auto-memory ``MEMORY.md``.

Why this exists
---------------
``MEMORY.md`` is the only Juniper memory file with a HARD cap -- 200 lines or
25,000 bytes, whichever binds first -- past which content is dropped SILENTLY
and **newest-first** (the index is append-ordered, and truncation keeps the
head). See notes/JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md
sections 2, 2a and 2b.

Eviction is nearly free: the auto-memory *topic file* survives on disk, so an
evicted row is demoted from resident to on-demand, not deleted.

Why the eviction list is hand-curated and not a regex
-----------------------------------------------------
A marker regex over-matches badly. Measured 2026-08-18, entries matching
CLOSED|RESOLVED|COMPLETE|SHIPPED|REFUTED included rows carrying LIVE state --
an open ``BLOCKER cascor#532``, a "tail WS-5/6", a live symlink gotcha. Evicting
those would destroy exactly the information the index exists to surface. So the
slug list below is explicit and reviewed; each entry is closed with no open tail.

Concurrency
-----------
Other agentic sessions edit this file continuously. The script therefore hashes
the file before and after building the new content and REFUSES to write if it
changed underneath -- re-run rather than clobber a concurrent curation.

Usage:
    python3 util/ad-hoc/2026-08-19_memory_index_evict.py            # dry run
    python3 util/ad-hoc/2026-08-19_memory_index_evict.py --execute
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

DEFAULT_INDEX = Path.home() / (
    ".claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md"
)

# Hard caps read from the shipped 2.1.235 binary (Tte=200 lines, qpe=25000 bytes).
LINE_CAP = 200
BYTE_CAP = 25000

# Explicit, reviewed eviction list -- topic-file slugs whose work is CLOSED with
# no open tail. Matched as a substring of the index row, which is stable across
# reflows in a way line numbers are not.
EVICT_SLUGS = [
    "project_cascor_pytest_ini_drift_2026-05-03.md",
    "project_juniper_cascor_worker_file_indirection_gap_2026-05-27.md",
    "project_juniper_canopy_data_api_key_gap.md",
    "project_poc_observability_remediation_complete_2026-05-29.md",
    "project_canopy_frontend_remediation_complete_2026-05-31.md",
    "project_ws1_irregular_dt_data_foundation.md",
    "project_juniper_model_core_scaffold_2026-06-14.md",
    "project_canopy_csrf_ttl_macos_flake_2026-06-22.md",
    "project_juniper_recurrence_full_audit.md",
    "project_notes_naming_convention_2026-07-04.md",
    "project_ci_tools_consumer_pin_drift_2026-07-06.md",
    "project_redis_cap_drop_all_crash_2026-07-07.md",
    "project_two_flag_attestation_image_skew_2026-07-07.md",
    "project_canopy_ci_red_20260710_coverage_gate_docker_smoke.md",
    "project_code_signing_key_migration_2026-07-16.md",
    "project_sc_050_release_train_pin_gaps_2026-07-17.md",
    "project_f_p1_2_grafana_misdiagnosis_2026-08-16.md",
]

# Rows that MATCH a closure marker but must NOT be evicted -- recorded so the
# judgement is auditable and a future run does not silently widen the list.
DELIBERATELY_KEPT = {
    "project_cascor_recurrence_cli_experimentation_plan.md": "open BLOCKER cascor#532",
    "project_platform_environment_roadmap_2026-06-17.md": "tail WS-5/6 still open",
    "project_canopy_debug_prompt_suite_gaps_2026-06-26.md": "live symlink gotcha",
    "project_custom_agent_suite.md": "fleet-supervisor added 2026-08, still evolving",
    "project_dp3_readout_spectrum_design_2026-06-20.md": "carries a live measurement",
}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    ap.add_argument("--execute", action="store_true", help="write (default: dry run)")
    args = ap.parse_args()

    if not args.index.is_file():
        print(f"ERROR: index not found: {args.index}", file=sys.stderr)
        return 2

    before = args.index.read_text(encoding="utf-8")
    before_hash = digest(before)
    lines = before.splitlines(keepends=True)

    kept, evicted = [], []
    for line in lines:
        if any(slug in line for slug in EVICT_SLUGS):
            evicted.append(line)
        else:
            kept.append(line)

    after = "".join(kept)

    missing = [s for s in EVICT_SLUGS if not any(s in ln for ln in evicted)]

    b_bytes, a_bytes = len(before.encode()), len(after.encode())
    b_lines, a_lines = len(lines), len(kept)

    print(f"index: {args.index}")
    print(f"  before : {b_lines:>4} lines  {b_bytes:>6} bytes"
          f"  ({b_bytes / BYTE_CAP:.0%} of byte cap)")
    print(f"  after  : {a_lines:>4} lines  {a_bytes:>6} bytes"
          f"  ({a_bytes / BYTE_CAP:.0%} of byte cap)")
    print(f"  freed  : {b_lines - a_lines:>4} rows   {b_bytes - a_bytes:>6} bytes")
    print(f"  headroom: {BYTE_CAP - a_bytes} bytes / {LINE_CAP - a_lines} lines")
    print(f"  deliberately kept (closed-marker but live): {len(DELIBERATELY_KEPT)}")

    if missing:
        print("\nWARNING: these slugs matched no row (already evicted, or renamed):")
        for slug in missing:
            print(f"  - {slug}")

    if not args.execute:
        print("\nDRY RUN -- nothing written. Pass --execute to apply.")
        return 0

    # Concurrency guard: refuse if another session wrote while we were working.
    if digest(args.index.read_text(encoding="utf-8")) != before_hash:
        print("\nREFUSING: index changed on disk while this run was building the "
              "result. Re-run; do not clobber a concurrent curation.", file=sys.stderr)
        return 1

    tmp = args.index.with_suffix(".md.tmp")
    tmp.write_text(after, encoding="utf-8")
    os.replace(tmp, args.index)
    print(f"\nWROTE {args.index} ({a_lines} lines, {a_bytes} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
