"""Juniper sequence-safety gates -- compositional-loss screens for the PR flood.

Productionization of the 2026-07-28 Cursor-fleet flood census (Proposal P2, the
flood-remediation analysis
``notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`` S3 /
S4 item 8). The flood damage was *compositional*: every PR was individually green,
but serial same-file merges into main fused or silently deleted sibling content, and
a deleted test cannot fail -- so flake8 / mypy / pre-commit all stayed green while
whole test classes and doc sections disappeared.

Two ref-diff screens answer the one question the per-PR checks could not:

  * ``symbol_loss_check.py``    -- AST symbol inventory of BASE vs HEAD for the
    in-scope Python / bash surface (top-level ``tests/*.py`` + ``util/**``); FAIL on
    a silently deleted (LOST) def/class/method, a shrunk-past-threshold (WEAKENED)
    body, or a duplicated (DUPLICATED) member, with a qualified-name / body-similarity
    relocation downgrade and a ``Allow-Symbol-Loss:`` commit-trailer escape hatch.
  * ``docs_additions_check.py`` -- markdown deletion-magnitude screen of BASE vs HEAD
    for ``AGENTS.md`` + ``docs/**`` + ``notes/**``; FAIL on a deleted heading or a run
    of >= N consecutive deleted lines, WARN on small in-place swaps, with a
    ``Allow-Docs-Rewrite:`` commit-trailer escape hatch.

Both are pure git + stdlib (no network, no gh, no pip), path-invoked, and gated by a
``tests/test_*.py`` because pre-commit scopes flake8 / black to ``^(scripts|tests)/``
(so ``util/`` has no lint gate of its own). The post-merge ``main-verify.yml`` workflow
runs both against ``<merge>^1 .. <merge>`` so the compositional-loss net fires no matter
who merged or what they bypassed -- the only gate the always-bypass actors cannot skip.

Project: juniper-ml
Sub-Project: flood-remediation sequence-safety gates
Author: Paul Calnon
Created: 2026-07-28
Status: permanent utility
"""
