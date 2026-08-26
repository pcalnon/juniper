#!/usr/bin/env bash
# Paired CLI-vs-service wall-clock campaign — arms INTERLEAVED, one cascor SHA.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-21
# Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the residual wall-gap evidence note is merged; delete then.
# Related:     util/ad-hoc/2026-08-20_determinism_nrun.py (reads the runs this produces);
#              util/ad-hoc/2026-08-16_h2h_phase_split.py (candidate/output split).
#
# WHY INTERLEAVED, AND WHY THAT IS THE POINT
# The predecessor campaign ran all 20 service cells and then all 20 CLI runs. Over the eight hours
# that took, host load fell from ~38 to ~6 -- so the service arm absorbed nearly all the
# contention and the CLI arm nearly none. Within each arm the divergence RATE survived that
# (a fingerprint does not care how long a run took), but the wall-clock columns did not: the
# service arm did byte-identical work twenty times, 11,360 candidate epochs with sd 0, and still
# spanned 825 s to 190 s. Those numbers were correctly declared unpublishable.
#
# Block ordering is what did the damage, not the presence of contention. A load that is merely
# CONSTANT cancels in a ratio; a load that DRIFTS across the boundary between two blocks does not,
# and it biases whichever arm ran during the busy half. So this alternates service, CLI, service,
# CLI ... and a pair's two legs are adjacent in time. Residual drift then hits both arms of a pair
# roughly equally instead of accumulating against one of them.
#
# It is still SEQUENTIAL -- never concurrent. The workload is ~8 forked candidate workers at ~90%
# CPU each, so two arms running at once would contend with each other and void the comparison
# outright.
#
# WHAT SHARES WHAT
#   * The SERVICE leg is one `run_suite` invocation of a single-cell suite; run_suite owns its
#     stack and tears it down per cell, which is the isolation this comparison wants.
#   * The CLI leg needs juniper-data only, so ONE persistent stack is brought up for the whole
#     campaign and its DATA_URL is captured once and passed explicitly. It is never re-resolved:
#     `2026-08-14_r5_stack_up.bash` picks "the newest run dir carrying a ports.json", so a service
#     leg coming up mid-campaign would otherwise silently re-point the CLI arm at the wrong data
#     service. The idle cascor in that stack costs ~0 CPU.
#   * Every service leg re-materialises its own cell. Those cells must be byte-identical to the
#     one the CLI arm was handed, so the script asserts a single `config_sha256` across all legs
#     and stops if it ever differs -- an equalisation failure that would otherwise be invisible.
#
# Usage: 2026-08-21_h2h_paired_campaign.bash <CASCOR_SRC> <SUITE_YAML> <K> [OUT_ROOT]
# Exit: 0 campaign attempted; 2 pre-flight or equalisation failure.
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> <SUITE_YAML> <K> [OUT_ROOT]}"
SUITE="${2:?usage: see header}"
K="${3:?usage: see header}"
OUT_ROOT="${4:-${HOME}/.local/state/juniper-experiments/h2h-paired-$(basename "${SUITE}" .yaml)}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"
PY="${JUNIPER_H2H_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
BOUND="${JUNIPER_H2H_BOUND:-15600}"
SUITE_ROOT="${HOME}/.local/state/juniper-experiments/suites"
SUITE_NAME="$(sed -n 's/^  name: *//p' "${SUITE}" | head -1)"

# --- pre-flight: one SHA, both arms ----------------------------------------------------------
[[ -d "${CASCOR_SRC}" ]] || { echo "paired: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -f "${SUITE}" ]] || { echo "paired: suite not found: ${SUITE}" >&2; exit 2; }
[[ -x "${PY}" ]] || { echo "paired: python not found: ${PY}" >&2; exit 2; }
[[ -n "${SUITE_NAME}" ]] || { echo "paired: could not read suite.name from ${SUITE}" >&2; exit 2; }
CASCOR_SRC="$(realpath "${CASCOR_SRC}")"
CLI_SHA="$(git -C "${CASCOR_SRC}/.." rev-parse HEAD 2>/dev/null)"
SVC_SHA="$(git -C "${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor" rev-parse HEAD 2>/dev/null)"
if [[ -z "${CLI_SHA}" || "${CLI_SHA}" != "${SVC_SHA}" ]]; then
    echo "paired: REFUSING -- arms are at different cascor commits (${CLI_SHA:-?} vs ${SVC_SHA:-?})" >&2
    exit 2
fi

mkdir -p "${OUT_ROOT}" || exit 2
printf '{"cascor_sha":"%s","suite":"%s","k":%d,"started_utc":"%s","host_nproc":%d}\n' \
    "${CLI_SHA}" "${SUITE}" "${K}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(nproc)" \
    >"${OUT_ROOT}/provenance.json"
echo "paired: cascor ${CLI_SHA} | K=${K} pairs | suite ${SUITE_NAME} | out=${OUT_ROOT}"

newest_suite_dir() {
    find "${SUITE_ROOT}" -maxdepth 1 -type d -name "${SUITE_NAME}-*" -printf '%T@ %p\n' 2>/dev/null \
        | sort -rn | head -1 | cut -d' ' -f2-
}
cell_sha() { sed -n 's/.*"config_sha256": *"\([0-9a-f]*\)".*/\1/p' "$1/registry.jsonl" | head -1; }

run_service_leg() {   # $1 = index
    local i="$1" load sd
    load="$(cut -d' ' -f1 /proc/loadavg)"
    # stderr: stdout is captured by the caller for the suite dir, so progress must not go there.
    echo "paired: pair ${i}/${K} SERVICE leg (load1=${load})" >&2
    "${PY}" "${REPO_ROOT}/util/experiments/run_suite.py" --suite "${SUITE}" \
        >>"${OUT_ROOT}/service_arm.log" 2>&1
    sd="$(newest_suite_dir)"
    [[ -n "${sd}" ]] || { echo "paired: service leg ${i} produced no suite dir" >&2; return 1; }
    printf '{"pair":%d,"arm":"service","suite_dir":"%s","config_sha256":"%s","load1":%s}\n' \
        "${i}" "${sd}" "$(cell_sha "${sd}")" "${load}" >>"${OUT_ROOT}/legs.jsonl"
    echo "${sd}"
}

# --- pair 1's service leg also materialises the shared cell -----------------------------------
FIRST_SD="$(run_service_leg 1 | tail -1)"
[[ -n "${FIRST_SD}" ]] || exit 2
CELL="$(find "${FIRST_SD}/cells" -mindepth 1 -maxdepth 1 -type d | sort | head -1)/experiment.yaml"
[[ -f "${CELL}" ]] || { echo "paired: no materialised cell under ${FIRST_SD}" >&2; exit 2; }
BASE_SHA="$(cell_sha "${FIRST_SD}")"
echo "CELL=${CELL}" >>"${OUT_ROOT}/provenance.json"
echo "CONFIG_SHA256=${BASE_SHA}" >>"${OUT_ROOT}/provenance.json"
echo "paired: shared cell ${CELL} (config_sha256 ${BASE_SHA:0:12})"

# --- one persistent stack for every CLI leg ---------------------------------------------------
STACK_OUT="$(bash "${REPO_ROOT}/util/ad-hoc/2026-08-14_r5_stack_up.bash" 2>&1 | tee "${OUT_ROOT}/stack_up.log" | tail -3)"
STACK_RUN_ID="$(sed -n 's/^RUN_ID=//p' <<<"${STACK_OUT}")"
DATA_URL="$(sed -n 's/^DATA_URL=//p' <<<"${STACK_OUT}")"
STACK_RUN_DIR="$(sed -n 's/^RUN_DIR=//p' <<<"${STACK_OUT}")"
if [[ -z "${STACK_RUN_ID}" || -z "${DATA_URL}" ]]; then
    echo "paired: CLI stack bring-up failed; see ${OUT_ROOT}/stack_up.log" >&2
    exit 2
fi
# Verify the resolved URL really belongs to the stack we just launched, rather than to a run dir
# some other session created in the same second.
if ! grep -q "\"data_url\": \"${DATA_URL}\"" "${STACK_RUN_DIR}/ports.json" 2>/dev/null; then
    echo "paired: REFUSING -- DATA_URL ${DATA_URL} is not in ${STACK_RUN_DIR}/ports.json" >&2
    bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${STACK_RUN_ID}" >/dev/null 2>&1
    exit 2
fi
echo "STACK_RUN_ID=${STACK_RUN_ID}" >>"${OUT_ROOT}/provenance.json"
echo "paired: CLI stack ${STACK_RUN_ID} DATA_URL=${DATA_URL} (verified)"

run_cli_leg() {       # $1 = index
    local i="$1" load
    load="$(cut -d' ' -f1 /proc/loadavg)"
    echo "paired: pair ${i}/${K} CLI leg (load1=${load})"
    bash "${REPO_ROOT}/util/ad-hoc/2026-08-17_h2h_thread_probe.bash" \
        "${CASCOR_SRC}" "${CELL}" "${OUT_ROOT}/cli-$(printf '%02d' "${i}")" "${DATA_URL}" "${BOUND}" default \
        >>"${OUT_ROOT}/cli_arm.log" 2>&1
    printf '{"pair":%d,"arm":"cli","load1":%s}\n' "${i}" "${load}" >>"${OUT_ROOT}/legs.jsonl"
}

run_cli_leg 1
for ((i = 2; i <= K; i++)); do
    sd="$(run_service_leg "${i}" | tail -1)"
    [[ -n "${sd}" ]] || break
    got="$(cell_sha "${sd}")"
    if [[ "${got}" != "${BASE_SHA}" ]]; then
        # Equalisation failure: the arms would be running different experiments. Stop rather than
        # produce a table that looks like a wall-clock comparison and is not one.
        echo "paired: REFUSING -- pair ${i} service cell config_sha256 ${got} != ${BASE_SHA}" >&2
        break
    fi
    run_cli_leg "${i}"
done

bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${STACK_RUN_ID}" >>"${OUT_ROOT}/stack_up.log" 2>&1
echo "paired: stack ${STACK_RUN_ID} torn down"
echo "paired: done -> ${OUT_ROOT}"
