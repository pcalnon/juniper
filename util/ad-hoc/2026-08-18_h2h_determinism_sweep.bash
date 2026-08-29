#!/usr/bin/env bash
# Map the direct CLI's reproducibility defect against the BLAS thread budget.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-18
# Status:      ad-hoc -- one-off (CLI reproducibility investigation)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the reproducibility defect is root-caused and written up; delete then.
# Related:     util/experiments/suites/p4/e-l-determinism-cap4.yaml (the service control);
#              util/ad-hoc/2026-08-17_h2h_thread_probe.bash (one arm).
#
# WHAT IS BEING TESTED
# Two direct-CLI runs of one cap-16 cell -- same data, same network seed, same thread setting --
# were bit-identical through iteration 1, diverged at iteration 2, and finished 10 pp apart in
# validation accuracy. Two SERVICE runs of the same cell were bit-identical throughout. So the CLI
# has a reproducibility defect -- whether the SERVICE shares it is UNKNOWN, since two agreeing
# service runs is far too small a sample against an effect that diverged in 3 of 5 pairs (an
# earlier claim that the service was deterministic has been withdrawn) -- and an attribution of the accuracy
# spread to thread count had to be withdrawn: single runs cannot separate a thread effect from
# run-to-run variance.
#
# This runs each thread budget TWICE. A pair that agrees is deterministic at that budget; a pair
# that disagrees is not. Only with pairs can a thread effect and a variance effect be told apart --
# which is exactly what the first attempt lacked.
#
# Cap 4 because divergence appears by iteration 2, so ~4 minutes per run buys the same signal a
# 25-minute cap-16 run does, and repetition is what this question actually needs.
#
# Usage: util/ad-hoc/2026-08-18_h2h_determinism_sweep.bash <SUITE_DIR> <OUT_ROOT> <CASCOR_SRC> [BOUND]
set -uo pipefail

SUITE_DIR="${1:?usage: $0 <SUITE_DIR> <OUT_ROOT> <CASCOR_SRC> [BOUND]}"
OUT_ROOT="${2:?usage: see header}"
CASCOR_SRC="${3:?usage: see header}"
BOUND="${4:-3600}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

CELL="$(find "${SUITE_DIR}/cells" -mindepth 1 -maxdepth 1 -type d | sort | head -1)"
[[ -d "${CELL}" ]] || { echo "determinism sweep: no cell under ${SUITE_DIR}/cells" >&2; exit 2; }

UP="$(bash "${REPO_ROOT}/util/ad-hoc/2026-08-14_r5_stack_up.bash" 2>&1)" || { echo "${UP}" >&2; exit 2; }
RUN_ID="$(grep -oP '^RUN_ID=\K.*' <<<"${UP}")"
DATA_URL="$(grep -oP '^DATA_URL=\K.*' <<<"${UP}")"
[[ -n "${RUN_ID}" && -n "${DATA_URL}" ]] || { echo "${UP}" >&2; echo "determinism sweep: cannot parse stack banner" >&2; exit 2; }
echo "determinism sweep: stack ${RUN_ID} at ${DATA_URL}  cell=$(basename "${CELL}")"

fail=0
# 1 is the decisive arm: fully single-threaded BLAS removes reduction-order nondeterminism as a
# candidate cause. If pairs still disagree at 1, threading is not the source and the defect is
# elsewhere entirely.
for threads in 1 2 default; do
    for rep in a b; do
        echo ""
        echo "############ $(date '+%H:%M:%S') threads=${threads} rep=${rep} ############"
        bash "${REPO_ROOT}/util/ad-hoc/2026-08-17_h2h_thread_probe.bash" \
            "${CASCOR_SRC}" "${CELL}/experiment.yaml" "${OUT_ROOT}/t${threads}-${rep}" \
            "${DATA_URL}" "${BOUND}" "${threads}" || fail=1
    done
done

bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >"${OUT_ROOT}/teardown.log" 2>&1 \
    && echo "determinism sweep: stack ${RUN_ID} torn down" \
    || { echo "determinism sweep: TEARDOWN FAILED (see ${OUT_ROOT}/teardown.log)" >&2; fail=1; }

echo "############ $(date '+%H:%M:%S') DETERMINISM SWEEP COMPLETE (fail=${fail}) ############"
exit "${fail}"
