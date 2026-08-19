#!/usr/bin/env bash
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: ad-hoc forensics
# Author:      Paul Calnon
# License:     MIT License
#
# P1 of the shared-session-memory plan: the WORKTREE ANCESTOR CANARY.
#
# The question (mechanism-facts section 8c): the main checkout's AGENTS.md IS a
# filesystem ancestor of .claude/worktrees/<name>/, so the documented rule
# ("ancestors load eagerly") predicts it loads -- yet it does not appear in a
# worktree session's context. Two hypotheses fit:
#
#   H-a  CONTENT DEDUP        -- identical content is injected once.
#   H-b  WORKTREE ROOT DETECT -- the worktree is the project root; ancestors skipped.
#
# They diverge exactly during migration, and H-a fails badly: once a worktree
# carries a TRIMMED AGENTS.md while the main checkout still carries the fat one,
# the two stop matching and BOTH load -- trimming would make context go UP.
#
# This builds a synthetic tree with DELIBERATELY DIFFERENT canaries at each
# level, so the two hypotheses give different observable answers.
#
#   H-a  -> the worktree probe sees BOTH canaries (files differ, so no dedup)
#   H-b  -> the worktree probe sees ONLY the worktree canary
#
# The marker is PLAIN TEXT, never an HTML comment: block-level HTML comments are
# stripped before injection, so an ABSENT result would conflate "ancestor not
# loaded" with "comment stripped" -- a false H-b in the dangerous direction.
#
# Probe A is a POSITIVE CONTROL from a plain subdirectory, where the ancestor
# MUST be visible. Without it, an ABSENT result in probe B is indistinguishable
# from a session that simply did not answer the question.
#
# Usage: bash util/ad-hoc/2026-08-19_build_ancestor_canary_probe.bash [ROOT]
# Prints the two probe directories; run claude -p from each.

set -euo pipefail

ROOT="${1:-${TMPDIR:-/tmp}/juniper-ancestor-canary}"

rm -rf "$ROOT"
mkdir -p "$ROOT/repo/plain_sub"
mkdir -p "$ROOT/repo/.claude/worktrees/wt"

# --- the "main checkout" (ancestor) ---
cat > "$ROOT/repo/AGENTS.md" <<'EOF'
# Probe Repo — ancestor level

CANARY_ANCESTOR_7Q2X is defined at the repository root level.
EOF
ln -sf AGENTS.md "$ROOT/repo/CLAUDE.md"

# --- the "worktree" (descendant), DELIBERATELY DIFFERENT content ---
cat > "$ROOT/repo/.claude/worktrees/wt/AGENTS.md" <<'EOF'
# Probe Repo — worktree level

CANARY_WORKTREE_7Q2X is defined inside the worktree.
EOF
ln -sf AGENTS.md "$ROOT/repo/.claude/worktrees/wt/CLAUDE.md"

echo "PROBE_A_DIR=$ROOT/repo/plain_sub"
echo "PROBE_B_DIR=$ROOT/repo/.claude/worktrees/wt"
echo
echo "ancestor md5 : $(md5sum "$ROOT/repo/AGENTS.md" | cut -d' ' -f1)"
echo "worktree md5 : $(md5sum "$ROOT/repo/.claude/worktrees/wt/AGENTS.md" | cut -d' ' -f1)"
echo "(they MUST differ for the probe to discriminate)"
