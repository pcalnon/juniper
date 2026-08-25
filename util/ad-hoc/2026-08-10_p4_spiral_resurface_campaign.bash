#!/usr/bin/env bash
# Re-run the P4 spiral surface against the F-P4-1-fixed stack (ml#1055 + cascor#504).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-10
# Status:     ad-hoc -- one-off (campaign driver)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the re-surfaced E-A/E-B/E-C evidence is written up and merged; delete then.
# Related:    F-P4-1 (notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md),
#             ml#1055 (driver stages spiral), cascor#504 (fallback honors SpiralParams),
#             P4 evidence notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md
#
# E-A's 12 cells and the spiral rows of E-B / E-C were measurements OF F-P4-1 (every E-A cell
# recruited 0 hidden units), so they are re-run now that spiral stages like every other
# generator. E-B / E-C are re-run WHOLE, not just their spiral rows: the non-spiral rows are
# cheap at smoke budget and a single self-consistent aggregate.csv per suite beats splicing
# new spiral rows into an old table.
#
# STRICTLY SEQUENTIAL: every suite here is a cascor suite, and cascor is one-per-checkout
# (H-7 -- shared logs/juniper_cascor.log). run_suite refuses cascor with parallel>1; this
# script must likewise never background two suites at once.
#
# Usage: util/ad-hoc/2026-08-10_p4_spiral_resurface_campaign.bash [SUITE_YAML ...]
#        (default: e-c, e-b, e-a -- cheap suites first, the long E-A grid last)
# Exit:  0 = every suite reported success; 1 = at least one suite had failed cells.
set -uo pipefail

# util/ad-hoc/ -> util/ -> repo root (TWO levels, not one).
REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
SUITE_DIR="${REPO_ROOT}/util/experiments/suites/p4"

# Campaign settings ratified during P4 (evidence doc): the 90 s default health gate produced
# false cold-start failures under concurrent groups, and the ecosystem root must be explicit
# because this runs from a git worktree (the launcher's derivation would land in worktrees/).
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

declare -a SUITES
if (($# > 0)); then
    SUITES=("$@")
else
    SUITES=(
        "${SUITE_DIR}/e-c-cascor-noise-robustness.yaml"
        "${SUITE_DIR}/e-b-cascor-dataset-difficulty.yaml"
        "${SUITE_DIR}/e-a-cascor-budget-sweep.yaml"
    )
fi

overall=0
for suite in "${SUITES[@]}"; do
    name="$(basename "${suite}" .yaml)"
    printf '\n===== [%s] START %s =====\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${name}"
    python3 "${REPO_ROOT}/util/experiments/run_suite.py" --suite "${suite}"
    rc=$?
    printf '===== [%s] END %s (exit %d) =====\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${name}" "${rc}"
    # exit 1 = suite ran but some cells failed; 2 = misuse/validation. Keep going either way so
    # one bad suite cannot strand the rest, but remember it for the campaign exit code.
    ((rc != 0)) && overall=1
done

printf '\n===== CAMPAIGN DONE (overall exit %d) =====\n' "${overall}"
exit "${overall}"
