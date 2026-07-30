"""fleet_triage -- Stage-0 fleet-supervisor deterministic script layer.

Project: juniper-ml
Sub-Project: custom-agent suite / Cursor-fleet PR-flood remediation
Application: fleet triage (Stage-0 supervisor, script layer)
Author: Paul Calnon
License: MIT License

The package productionizes the flood-census symbol screen into a per-PR merge
simulator: given a PR branch ref it builds a detached scratch clone, merges
``origin/main`` into the branch tip WITHOUT pushing, and runs the repo-pinned
fast gates plus two screens CI cannot see (an AST symbol-loss screen and a docs
additions-only screen) on the RESULT, emitting a per-PR JSON verdict and the
TRUE changed-file delta. ``--batch`` mode adds a same-file cluster map and a
stale-branch-minimizing merge order.

The read-only ``fleet-supervisor`` agent (``.claude/agents/fleet-supervisor.md``)
invokes this script once per triage batch and adjudicates dup/supersession,
cluster, and order from its JSON. Design of record: P3 §1 in
``notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md``.
"""

from __future__ import annotations

from .predict_merge import (  # noqa: F401
    PredictMergeError,
    SCRIPT_VERDICTS,
    build_clusters,
    simulate_merge,
    suggest_order,
    triage_batch,
    triage_pr,
)

__all__ = [
    "PredictMergeError",
    "SCRIPT_VERDICTS",
    "build_clusters",
    "simulate_merge",
    "suggest_order",
    "triage_batch",
    "triage_pr",
]
