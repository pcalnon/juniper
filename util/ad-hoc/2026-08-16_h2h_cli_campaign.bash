#!/usr/bin/env bash
# WIDE-BUDGET HEAD-TO-HEAD -- run the direct-CLI arm for every cell of one service suite.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-16
# Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the wide-budget head-to-head evidence note is merged; delete then.
# Related:     util/ad-hoc/2026-08-16_h2h_cli_arm.bash (one arm); the e-j-h2h-wide-cap* suites.
#
# The suite (run_suite) is the SERVICE-arm driver: it brings a stack up and down PER CELL and
# writes a fully-resolved cells/<cell_id>/experiment.yaml for each. This runs the other arm over
# exactly those generated files, so both arms of a replicate read byte-identical configuration.
# Handing the CLI the hand-written base config instead is the campaign's silent failure mode
# (one seed on one arm, three on the other); the arm runner refuses anything not on a cells/ path.
#
# ONE stack for the whole suite, not one per cell: juniper-data dataset ids are content-addressed,
# so the three replicates of a cap resolve to three ids on a single service and the listing this
# prints before teardown IS the equalisation evidence. Run the caps as separate invocations --
# both should print the SAME three ids, which is what demonstrates that each cap-64 replicate is
# paired with a cap-128 replicate on identical data.
#
# Sequential by construction: an experiment wall-clock comparison is meaningless if two arms
# share the GPU. Nothing here is backgrounded.
#
# Usage: util/ad-hoc/2026-08-16_h2h_cli_campaign.bash <SUITE_DIR> <CLI_ROOT> <CASCOR_SRC> [BOUND]
# Exit:  0 every arm completed; 1 an arm failed (the rest still ran); 2 usage / bring-up failure.
set -uo pipefail

SUITE_DIR="${1:?usage: $0 <SUITE_DIR> <CLI_ROOT> <CASCOR_SRC> [BOUND]}"
CLI_ROOT="${2:?usage: $0 <SUITE_DIR> <CLI_ROOT> <CASCOR_SRC> [BOUND]}"
CASCOR_SRC="${3:?usage: $0 <SUITE_DIR> <CLI_ROOT> <CASCOR_SRC> [BOUND]}"
BOUND="${4:-14400}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

[[ -d "${SUITE_DIR}/cells" ]] || { echo "h2h campaign: no cells/ under ${SUITE_DIR}" >&2; exit 2; }
SUITE_NAME="$(basename "${SUITE_DIR}")"
mapfile -t CELLS < <(find "${SUITE_DIR}/cells" -mindepth 1 -maxdepth 1 -type d | sort)
((${#CELLS[@]} > 0)) || { echo "h2h campaign: ${SUITE_DIR}/cells is empty" >&2; exit 2; }

echo "h2h campaign: suite=${SUITE_NAME}  cells=${#CELLS[@]}  bound=${BOUND}s"

UP_OUT="$(bash "${REPO_ROOT}/util/ad-hoc/2026-08-14_r5_stack_up.bash" 2>&1)"
rc=$?
if ((rc != 0)); then
    echo "${UP_OUT}" >&2
    echo "h2h campaign: stack bring-up failed (exit ${rc})" >&2
    exit 2
fi
RUN_ID="$(grep -oP '^RUN_ID=\K.*' <<<"${UP_OUT}")"
DATA_URL="$(grep -oP '^DATA_URL=\K.*' <<<"${UP_OUT}")"
[[ -n "${RUN_ID}" && -n "${DATA_URL}" ]] || { echo "${UP_OUT}" >&2; echo "h2h campaign: could not parse RUN_ID/DATA_URL" >&2; exit 2; }
echo "h2h campaign: stack ${RUN_ID} up, data at ${DATA_URL}"

fail=0
for cell_dir in "${CELLS[@]}"; do
    cell_id="$(basename "${cell_dir}")"
    out_dir="${CLI_ROOT}/${SUITE_NAME}/${cell_id}"
    echo ""
    echo "=== h2h campaign: CLI arm ${SUITE_NAME}/${cell_id} ==="
    bash "${REPO_ROOT}/util/ad-hoc/2026-08-16_h2h_cli_arm.bash" \
        "${CASCOR_SRC}" "${cell_dir}/experiment.yaml" "${out_dir}" "${DATA_URL}" "${BOUND}"
    arm_rc=$?
    ((arm_rc == 0)) || { fail=1; echo "h2h campaign: ${cell_id} arm exited ${arm_rc} -- continuing"; }
done

# The equalisation evidence, captured BEFORE teardown takes the service away. Expect exactly one
# id per distinct derived seed (three for a 3-replicate suite) -- and the same three for the
# other cap's invocation.
echo ""
echo "=== h2h campaign: datasets held by ${RUN_ID} (expect 3, shared with the other cap) ==="
mkdir -p "${CLI_ROOT}/${SUITE_NAME}"
curl -s --max-time 20 "${DATA_URL}/v1/datasets?limit=50" | tee "${CLI_ROOT}/${SUITE_NAME}/datasets.json" | head -c 2000
echo ""

bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >"${CLI_ROOT}/${SUITE_NAME}/teardown.log" 2>&1
down_rc=$?
((down_rc == 0)) && echo "h2h campaign: stack ${RUN_ID} torn down" || { echo "h2h campaign: TEARDOWN FAILED for ${RUN_ID} (exit ${down_rc}) -- see ${CLI_ROOT}/${SUITE_NAME}/teardown.log" >&2; fail=1; }

exit "${fail}"
