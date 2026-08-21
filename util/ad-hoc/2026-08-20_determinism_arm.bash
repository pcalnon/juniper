#!/usr/bin/env bash
# Run ONE direct-CLI determinism arm: N runs of one cell under one intervention.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-20
# Status:      ad-hoc -- one-off (juniper-cascor#532 seeded-run reproducibility)
# Retire when: #532 is root-caused or accepted and the evidence note is merged; delete then.
# Related:     2026-08-20_determinism_campaign.bash (the baseline arms);
#              2026-08-20_determinism_nrun.py (reads what this produces).
#
# WHY A SEPARATE RUNNER
# The campaign driver establishes the BASELINE (service and direct-CLI, both at the shipped
# thread policy). This runs an INTERVENTION arm against the same materialised cell and the same
# stack, so the only difference from the baseline is the knob under test.
#
# Two interventions are worth testing, and they are not the same fix:
#
#   THREADS=1   Serialise the BLAS pool. Reproducible, but it gives up the throughput that
#               juniper-cascor#531 was opened to recover -- the capped path's candidate phase ran
#               1.52x the uncapped path's. A fix that reintroduces most of that cost is a
#               regression wearing a different hat.
#
#   MKL_CBWR    Intel MKL's Conditional Numerical Reproducibility. torch 2.11 here is built with
#               BLAS_INFO=mkl, and MKL does NOT promise run-to-run reproducible results for
#               threaded reductions unless CNR is enabled; CNR pins the code path so a fixed
#               thread count yields a fixed summation order. If this works it buys reproducibility
#               while KEEPING the threads, which is the outcome worth having.
#
# Both are measured, not assumed -- an intervention that "should" work and is not run at N>=20 is
# exactly the kind of claim this investigation has had to withdraw three times.
#
# Usage: 2026-08-20_determinism_arm.bash <CASCOR_SRC> <CELL_YAML> <OUT_ROOT> <LABEL> <N> <THREADS> [VAR=VAL ...]
#   THREADS   integer, or `default` to leave the BLAS variables unset (the shipped behaviour).
#   VAR=VAL   extra environment exported for every run in this arm (e.g. MKL_CBWR=COMPATIBLE).
#
# The stack is NOT managed here: bring one up first and export DATA_URL, so every arm in a
# comparison talks to the same juniper-data instance and the same content-addressed dataset.
# Exit: 0 arm attempted; 2 pre-flight failure.
set -uo pipefail

CASCOR_SRC="${1:?usage: see header}"
CELL_YAML="${2:?usage: see header}"
OUT_ROOT="${3:?usage: see header}"
LABEL="${4:?usage: see header}"
N="${5:?usage: see header}"
THREADS="${6:?usage: see header}"
shift 6

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
BOUND="${JUNIPER_DET_BOUND:-3600}"
: "${DATA_URL:?DATA_URL must be exported -- bring a stack up first (2026-08-14_r5_stack_up.bash)}"

[[ -d "${CASCOR_SRC}" ]] || { echo "arm: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -f "${CELL_YAML}" ]] || { echo "arm: cell config not found: ${CELL_YAML}" >&2; exit 2; }

for kv in "$@"; do
    [[ "${kv}" == *=* ]] || { echo "arm: extra env must be VAR=VAL, got '${kv}'" >&2; exit 2; }
    export "${kv?}"
done

ARM_DIR="${OUT_ROOT}/${LABEL}"
mkdir -p "${ARM_DIR}" || exit 2
echo "arm: label=${LABEL} threads=${THREADS} N=${N} extra_env=[$*]"
printf '{"label":"%s","threads":"%s","n":%d,"extra_env":"%s","cell":"%s","started_utc":"%s"}\n' \
    "${LABEL}" "${THREADS}" "${N}" "$*" "${CELL_YAML}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    >"${ARM_DIR}/arm.json"

for i in $(seq -w 1 "${N}"); do
    load1="$(cut -d' ' -f1 /proc/loadavg)"
    echo "arm ${LABEL}: run ${i}/${N} (load1=${load1})"
    bash "${REPO_ROOT}/util/ad-hoc/2026-08-17_h2h_thread_probe.bash" \
        "${CASCOR_SRC}" "${CELL_YAML}" "${ARM_DIR}/run-${i}" "${DATA_URL}" "${BOUND}" "${THREADS}" \
        >>"${ARM_DIR}/arm.log" 2>&1
    printf '{"run":"run-%s","load1_before":%s,"load1_after":%s}\n' \
        "${i}" "${load1}" "$(cut -d' ' -f1 /proc/loadavg)" >>"${ARM_DIR}/load.jsonl"
done
echo "arm ${LABEL}: done -> ${ARM_DIR}"
