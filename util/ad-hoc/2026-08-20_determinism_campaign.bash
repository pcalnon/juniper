#!/usr/bin/env bash
# N=20 determinism campaign driver -- both arms, one cascor SHA, strictly sequential.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-20
# Status:      ad-hoc -- one-off (juniper-cascor#532 seeded-run reproducibility)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: #532 is root-caused or accepted and the evidence note is merged; delete then.
# Related:     util/experiments/suites/p4/e-l-determinism-cap4.yaml (the SERVICE arm, 20 cells);
#              util/ad-hoc/2026-08-17_h2h_thread_probe.bash (one direct-CLI run);
#              util/ad-hoc/2026-08-20_determinism_nrun.py (reads what this produces).
#
# WHY A DRIVER AND NOT A LOOP TYPED AT THE PROMPT
# The two arms must not overlap. The workload is CPU-bound -- roughly 8 forked candidate workers
# at ~90% CPU each -- so arms running concurrently would contend and void every wall-clock
# figure, and the timing noise floor this campaign exists to establish is the input that sizes
# the next measurement. `2026-08-14_r5_stack_up.bash` also resolves "the newest run dir carrying
# a ports.json", so a second stack coming up mid-campaign would silently re-point the CLI arm.
# Sequencing this in a script rather than by hand is what makes those two things guaranteed
# rather than remembered.
#
# ONE SHA, BOTH ARMS. The service arm runs from ${PROJECT_DIR}/juniper-cascor/src (where
# experiment_stack.bash looks); the CLI arm runs from CASCOR_SRC. Both SHAs are recorded to
# provenance.json and the script REFUSES to start if they differ -- a cross-arm comparison at two
# checkouts is the failure that silently re-inserted a BLAS cap into an earlier CLI arm.
#
# Usage: util/ad-hoc/2026-08-20_determinism_campaign.bash <CASCOR_SRC> [N] [OUT_ROOT]
#   CASCOR_SRC  src/ of a DEDICATED cascor checkout (not the shared one -- a shared checkout's
#               parent log rotates out from under the run; that is how an earlier arm's evidence
#               was lost). Must be the same commit as the service checkout.
#   N           runs per arm (default 20).
# Exit: 0 both arms attempted; 2 pre-flight failure (nothing run).
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> [N] [OUT_ROOT]}"
N="${2:-20}"
OUT_ROOT="${3:-${HOME}/.local/state/juniper-experiments/determinism-n20}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"
PY="${JUNIPER_H2H_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
SUITE="${REPO_ROOT}/util/experiments/suites/p4/e-l-determinism-cap4.yaml"
BOUND="${JUNIPER_DET_BOUND:-3600}"

# --- pre-flight -----------------------------------------------------------------------------
[[ -d "${CASCOR_SRC}" ]] || { echo "campaign: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -x "${PY}" ]] || { echo "campaign: python not found: ${PY}" >&2; exit 2; }
[[ -f "${SUITE}" ]] || { echo "campaign: suite not found: ${SUITE}" >&2; exit 2; }
CASCOR_SRC="$(realpath "${CASCOR_SRC}")"
CLI_SHA="$(git -C "${CASCOR_SRC}/.." rev-parse HEAD 2>/dev/null)"
SVC_SHA="$(git -C "${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor" rev-parse HEAD 2>/dev/null)"
[[ -n "${CLI_SHA}" && -n "${SVC_SHA}" ]] || { echo "campaign: could not resolve both cascor SHAs" >&2; exit 2; }
if [[ "${CLI_SHA}" != "${SVC_SHA}" ]]; then
    echo "campaign: REFUSING -- arms are at different cascor commits." >&2
    echo "  CLI arm (${CASCOR_SRC}/..): ${CLI_SHA}" >&2
    echo "  service arm (${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor): ${SVC_SHA}" >&2
    exit 2
fi

mkdir -p "${OUT_ROOT}" || exit 2
printf '{"cascor_sha":"%s","cascor_src":"%s","n_per_arm":%d,"suite":"%s","started_utc":"%s","host_nproc":%d}\n' \
    "${CLI_SHA}" "${CASCOR_SRC}" "${N}" "${SUITE}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(nproc)" \
    >"${OUT_ROOT}/provenance.json"
echo "campaign: cascor ${CLI_SHA} | N=${N} per arm | out=${OUT_ROOT}"

# --- ARM 1: service (run_suite materialises the shared cell as a side effect) ----------------
echo "campaign: [1/2] service arm -- ${N} cells via run_suite"
"${PY}" "${REPO_ROOT}/util/experiments/run_suite.py" --suite "${SUITE}" \
    >"${OUT_ROOT}/service_arm.log" 2>&1
echo "campaign: service arm exit=$?"

SUITE_DIR="$(find "${HOME}/.local/state/juniper-experiments/suites" -maxdepth 1 -type d -name 'e-l-determinism-cap4-*' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
[[ -n "${SUITE_DIR}" ]] || { echo "campaign: no suite dir produced; stopping before the CLI arm" >&2; exit 2; }
CELL="$(find "${SUITE_DIR}/cells" -mindepth 1 -maxdepth 1 -type d | sort | head -1)"
[[ -f "${CELL}/experiment.yaml" ]] || { echo "campaign: no materialised cell in ${SUITE_DIR}" >&2; exit 2; }
echo "SUITE_DIR=${SUITE_DIR}" >>"${OUT_ROOT}/provenance.json"
echo "CELL=${CELL}" >>"${OUT_ROOT}/provenance.json"
echo "campaign: shared cell = ${CELL}"

# --- ARM 2: direct CLI, N runs against ONE stack ---------------------------------------------
echo "campaign: [2/2] CLI arm -- bringing up one stack for all ${N} runs"
STACK_OUT="$(bash "${REPO_ROOT}/util/ad-hoc/2026-08-14_r5_stack_up.bash" 2>&1 | tee "${OUT_ROOT}/stack_up.log" | tail -3)"
RUN_ID="$(sed -n 's/^RUN_ID=//p' <<<"${STACK_OUT}")"
DATA_URL="$(sed -n 's/^DATA_URL=//p' <<<"${STACK_OUT}")"
if [[ -z "${RUN_ID}" || -z "${DATA_URL}" ]]; then
    echo "campaign: stack bring-up failed; see ${OUT_ROOT}/stack_up.log" >&2
    exit 2
fi
echo "campaign: stack RUN_ID=${RUN_ID} DATA_URL=${DATA_URL}"
echo "STACK_RUN_ID=${RUN_ID}" >>"${OUT_ROOT}/provenance.json"

for i in $(seq -w 1 "${N}"); do
    dir="${OUT_ROOT}/cli-${i}"
    # Record contention alongside the run: the timing noise floor is only interpretable if a
    # busy host is visible rather than folded into the sd.
    load_before="$(cut -d' ' -f1 /proc/loadavg)"
    echo "campaign: cli-${i}/${N} (load1=${load_before})"
    bash "${REPO_ROOT}/util/ad-hoc/2026-08-17_h2h_thread_probe.bash" \
        "${CASCOR_SRC}" "${CELL}/experiment.yaml" "${dir}" "${DATA_URL}" "${BOUND}" default \
        >>"${OUT_ROOT}/cli_arm.log" 2>&1
    printf '{"run":"cli-%s","load1_before":%s,"load1_after":%s}\n' \
        "${i}" "${load_before}" "$(cut -d' ' -f1 /proc/loadavg)" >>"${OUT_ROOT}/cli_load.jsonl"
done

bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >>"${OUT_ROOT}/stack_up.log" 2>&1
echo "campaign: stack ${RUN_ID} torn down"
echo "campaign: done -- analyse with util/ad-hoc/2026-08-20_determinism_nrun.py"
