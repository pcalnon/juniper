#!/usr/bin/env bash
# ROOT-CAUSE PROBE campaign: sweep the direct CLI's inherited BLAS thread budget.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-17
# Status:      ad-hoc -- one-off (2x root-cause investigation)
# Retire when: the root cause is written up and remediated; delete then.
# Related:     2026-08-17_h2h_thread_probe.bash (one arm); e-k-thread-probe-cap16.yaml (service ref).
#
# Runs the SAME suite-generated cell config through the direct CLI three times, varying only the
# inherited OMP/MKL/OPENBLAS thread budget:
#
#   default  -- main.py's RC-1 setdefault applies (2). This is shipped direct-CLI behaviour and
#               the arm the wide-budget head-to-head actually measured.
#   8        -- torch's own default on this host when nothing is set.
#   16       -- one per core; the upper end of what an unset OpenMP runtime may choose.
#
# The service reference never executes main.py, so it loads BLAS with NOTHING set. If the CLI's
# candidate throughput moves with this knob and lands near the service reference at the high end,
# RC-1's cap is the mechanism behind the ~2x.
#
# Strictly sequential and single-stack: the arms are being timed, so they must not share cores,
# and one juniper-data instance means all three resolve the SAME content-addressed dataset.
#
# Usage: util/ad-hoc/2026-08-17_h2h_thread_campaign.bash <SUITE_DIR> <OUT_ROOT> <CASCOR_SRC> [BOUND]
set -uo pipefail

SUITE_DIR="${1:?usage: $0 <SUITE_DIR> <OUT_ROOT> <CASCOR_SRC> [BOUND]}"
OUT_ROOT="${2:?usage: see header}"
CASCOR_SRC="${3:?usage: see header}"
BOUND="${4:-7200}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

CELL_DIR="$(find "${SUITE_DIR}/cells" -mindepth 1 -maxdepth 1 -type d | sort | head -1)"
[[ -d "${CELL_DIR}" ]] || { echo "thread campaign: no cell under ${SUITE_DIR}/cells" >&2; exit 2; }
CELL_ID="$(basename "${CELL_DIR}")"
echo "thread campaign: cell=${CELL_ID}  bound=${BOUND}s"

UP_OUT="$(bash "${REPO_ROOT}/util/ad-hoc/2026-08-14_r5_stack_up.bash" 2>&1)" || { echo "${UP_OUT}" >&2; exit 2; }
RUN_ID="$(grep -oP '^RUN_ID=\K.*' <<<"${UP_OUT}")"
DATA_URL="$(grep -oP '^DATA_URL=\K.*' <<<"${UP_OUT}")"
[[ -n "${RUN_ID}" && -n "${DATA_URL}" ]] || { echo "${UP_OUT}" >&2; echo "thread campaign: cannot parse stack banner" >&2; exit 2; }
echo "thread campaign: stack ${RUN_ID} up at ${DATA_URL}"

fail=0
for threads in default 8 16; do
    echo ""
    echo "############ $(date '+%H:%M:%S') CLI arm, threads=${threads} ############"
    bash "${REPO_ROOT}/util/ad-hoc/2026-08-17_h2h_thread_probe.bash" \
        "${CASCOR_SRC}" "${CELL_DIR}/experiment.yaml" "${OUT_ROOT}/threads-${threads}" \
        "${DATA_URL}" "${BOUND}" "${threads}" || fail=1
done

bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >"${OUT_ROOT}/teardown.log" 2>&1 \
    && echo "thread campaign: stack ${RUN_ID} torn down" \
    || { echo "thread campaign: TEARDOWN FAILED (see ${OUT_ROOT}/teardown.log)" >&2; fail=1; }

echo "############ $(date '+%H:%M:%S') THREAD CAMPAIGN COMPLETE (fail=${fail}) ############"
exit "${fail}"
