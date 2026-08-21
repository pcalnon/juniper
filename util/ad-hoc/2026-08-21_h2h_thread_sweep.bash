#!/usr/bin/env bash
# Interleaved direct-CLI thread-budget sweep: is `unset` the same as an explicit value?
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-21
# Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
# Retire when: the residual wall-gap evidence note is merged; delete then.
# Related:     2026-08-21_h2h_paired_ratio.py, 2026-08-20_determinism_nrun.py (readers).
#
# THE TWO QUESTIONS, ONE SWEEP
#
# 1. IS `unset` THE SAME AS EXPLICIT 16? juniper-cascor#531's thread probe exported
#    OMP_NUM_THREADS=16 explicitly; the post-#533 shipped CLI leaves the variables UNSET and lets
#    the library choose. Those are *intended* to be the same 16 threads on a 16-core host, but
#    OpenMP and MKL both have defaulting heuristics that an explicit value bypasses, and nothing
#    guarantees they land in the same place. This matters because the cap-16 candidate-phase ratio
#    measured here (1.706x, k=4) sits far outside #531's single-run 1.17x, and "we measured
#    different thread configurations" is one of the two live explanations for that.
#
# 2. DOES THE OMP=2 CAP ACTUALLY COST 1.30x? #531 attributed 1.30x of a 1.52x candidate-phase
#    penalty to `main.py`'s pre-#533 cap, from ONE RUN PER SETTING. Two single-run attributions in
#    this investigation have already failed to survive k=4 -- the 1.17x residual and the claim that
#    #533 would move the cap-64 headline. Re-measuring the cap directly is cheap and settles
#    whether the 1.30x is real.
#
# WHY INTERLEAVED BY CONDITION
# The conditions rotate INSIDE each replicate -- unset, 16, 2, unset, 16, 2, ... -- rather than
# running all of one then all of the next. Host load drifts over hours; a block layout hands the
# drift to whichever condition ran during the busy stretch, which is exactly how the predecessor
# campaign's timing was ruined. Rotating means every condition sees the same slice of the day.
#
# The direct CLI is nondeterministic (divergence rate 0.768), so its candidate WORK varies run to
# run. Read the per-epoch RATE column rather than the span when comparing conditions: at cap 64 the
# rate held a 3.7% cv across a 2x swing in work, so it is the stable channel.
#
# One stack for the whole sweep, DATA_URL captured once and passed explicitly.
#
# Usage: 2026-08-21_h2h_thread_sweep.bash <CASCOR_SRC> <CELL_YAML> <OUT_ROOT> <REPS> <COND> [COND...]
#        COND is an integer thread count or the literal `default` (leave the variables unset).
# Exit: 0 sweep attempted; 2 pre-flight failure.
set -uo pipefail

CASCOR_SRC="${1:?usage: see header}"
CELL="${2:?usage: see header}"
OUT_ROOT="${3:?usage: see header}"
REPS="${4:?usage: see header}"
shift 4
CONDS=("$@")
((${#CONDS[@]} >= 1)) || { echo "sweep: need at least one condition" >&2; exit 2; }

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"
BOUND="${JUNIPER_H2H_BOUND:-15600}"

[[ -d "${CASCOR_SRC}" ]] || { echo "sweep: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -f "${CELL}" ]] || { echo "sweep: cell not found: ${CELL}" >&2; exit 2; }
mkdir -p "${OUT_ROOT}" || exit 2

SHA="$(git -C "${CASCOR_SRC}/.." rev-parse HEAD 2>/dev/null)"
printf '{"cascor_sha":"%s","cell":"%s","reps":%d,"conditions":"%s","started_utc":"%s"}\n' \
    "${SHA}" "${CELL}" "${REPS}" "${CONDS[*]}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    >"${OUT_ROOT}/provenance.json"
echo "sweep: cascor ${SHA} | ${REPS} reps x [${CONDS[*]}] | out=${OUT_ROOT}"

STACK_OUT="$(bash "${REPO_ROOT}/util/ad-hoc/2026-08-14_r5_stack_up.bash" 2>&1 | tee "${OUT_ROOT}/stack_up.log" | tail -3)"
RUN_ID="$(sed -n 's/^RUN_ID=//p' <<<"${STACK_OUT}")"
DATA_URL="$(sed -n 's/^DATA_URL=//p' <<<"${STACK_OUT}")"
RUN_DIR="$(sed -n 's/^RUN_DIR=//p' <<<"${STACK_OUT}")"
[[ -n "${RUN_ID}" && -n "${DATA_URL}" ]] || { echo "sweep: stack bring-up failed" >&2; exit 2; }
grep -q "\"data_url\": \"${DATA_URL}\"" "${RUN_DIR}/ports.json" 2>/dev/null || {
    echo "sweep: REFUSING -- DATA_URL ${DATA_URL} not in ${RUN_DIR}/ports.json" >&2
    bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >/dev/null 2>&1
    exit 2
}
echo "sweep: stack ${RUN_ID} DATA_URL=${DATA_URL} (verified)"

for ((rep = 1; rep <= REPS; rep++)); do
    for cond in "${CONDS[@]}"; do
        dir="${OUT_ROOT}/t${cond}-r$(printf '%02d' "${rep}")"
        load="$(cut -d' ' -f1 /proc/loadavg)"
        echo "sweep: rep ${rep}/${REPS} threads=${cond} (load1=${load})"
        bash "${REPO_ROOT}/util/ad-hoc/2026-08-17_h2h_thread_probe.bash" \
            "${CASCOR_SRC}" "${CELL}" "${dir}" "${DATA_URL}" "${BOUND}" "${cond}" \
            >>"${OUT_ROOT}/sweep.log" 2>&1
        printf '{"rep":%d,"threads":"%s","dir":"%s","load1":%s}\n' \
            "${rep}" "${cond}" "${dir}" "${load}" >>"${OUT_ROOT}/legs.jsonl"
    done
done

bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >>"${OUT_ROOT}/stack_up.log" 2>&1
echo "sweep: stack ${RUN_ID} torn down"
echo "sweep: done -> ${OUT_ROOT}"
