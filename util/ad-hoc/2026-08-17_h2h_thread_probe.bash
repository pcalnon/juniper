#!/usr/bin/env bash
# ROOT-CAUSE PROBE for the ~2x direct-CLI wall-clock penalty (ml#1143) -- BLAS thread asymmetry.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-17
# Status:      ad-hoc -- one-off (2x root-cause investigation)
# Retire when: the root cause is written up and remediated; delete then.
# Related:     util/experiments/suites/p4/e-k-thread-probe-cap16.yaml (the service reference);
#              util/ad-hoc/2026-08-16_h2h_phase_split.py (reads what this produces).
#
# THE HYPOTHESIS
# juniper-cascor/src/main.py:48-50 caps BLAS threads to 2 at the DIRECT-CLI entry point:
#     os.environ.setdefault("OMP_NUM_THREADS", "2")   (+ MKL_, OPENBLAS_)
# labelled "PARALLEL-FIX (RC-1)". The SERVICE enters via `uvicorn api.app:create_app` and never
# runs main.py; src/api/ sets no thread variables at all. Because BLAS reads these ONCE at library
# load, and the candidate workers are FORKED from that parent, every candidate worker inherits the
# entry point's pool size permanently -- torch.set_num_threads(1) in the worker resizes torch's
# intra-op pool but not an already-built OpenMP pool.
#
# main.py uses setdefault, so an exported value WINS. That makes the hypothesis testable by
# changing exactly one thing: run the same cell config, on the same data, from the same checkout,
# varying only the inherited thread budget. If candidate throughput moves with it, RC-1's cap is
# the mechanism.
#
# Deliberately NOT a service-side test: injecting env into the service would need launcher changes,
# whereas the CLI honours the override natively. If the CLI at high thread counts matches the
# service reference, that is the same finding with less machinery.
#
# Usage: util/ad-hoc/2026-08-17_h2h_thread_probe.bash <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND> <THREADS|default>
#   THREADS  an integer exported to OMP_/MKL_/OPENBLAS_NUM_THREADS, or the literal `default`
#            to leave them unset so main.py's RC-1 setdefault applies (the shipped CLI behaviour).
# Exit: the CLI's exit code; 2 on usage/pre-flight failure.
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND> <THREADS|default>}"
CONFIG="${2:?usage: see header}"
OUT_DIR="${3:?usage: see header}"
DATA_URL="${4:?usage: see header}"
BOUND="${5:?usage: see header}"
THREADS="${6:?usage: see header}"

PY="${JUNIPER_H2H_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
[[ -d "${CASCOR_SRC}" ]] || { echo "thread probe: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -f "${CONFIG}" ]] || { echo "thread probe: config not found: ${CONFIG}" >&2; exit 2; }
[[ -x "${PY}" ]] || { echo "thread probe: python not found: ${PY}" >&2; exit 2; }

mkdir -p "${OUT_DIR}/logs" || exit 2
CASCOR_SRC="$(realpath "${CASCOR_SRC}")"
CONFIG="$(realpath "${CONFIG}")"
OUT_DIR="$(realpath "${OUT_DIR}")"

export LD_LIBRARY_PATH=""
export JUNIPER_DATA_URL="${DATA_URL}"
export JUNIPER_CASCOR_LOG_DIR="${OUT_DIR}/logs"

if [[ "${THREADS}" == "default" ]]; then
    # Leave unset so main.py's setdefault wins -- this is the shipped direct-CLI behaviour and the
    # arm that ml#1143 actually measured.
    unset OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS
    LABEL="default(RC-1 -> 2)"
else
    export OMP_NUM_THREADS="${THREADS}" MKL_NUM_THREADS="${THREADS}" OPENBLAS_NUM_THREADS="${THREADS}"
    LABEL="${THREADS}"
fi

echo "thread probe: threads=${LABEL}  config=$(basename "$(dirname "${CONFIG}")")  out=${OUT_DIR}"

cd "${CASCOR_SRC}" || exit 2
: >"${OUT_DIR}/direct_cli.log"
start=$(date +%s)
timeout --foreground --kill-after=30s "${BOUND}" \
    "${PY}" main.py --config "${CONFIG}" --no-plots >>"${OUT_DIR}/direct_cli.log" 2>&1
rc=$?
elapsed=$(( $(date +%s) - start ))
pkill -f "main.py --config ${CONFIG}" 2>/dev/null
sleep 2

# Record what the process ACTUALLY resolved, not what was requested -- the whole point is that the
# effective pool can differ from the nominal setting.
printf '{"arm":"cli","threads_requested":"%s","exit_code":%d,"process_wall_seconds":%d,"omp":"%s"}\n' \
    "${LABEL}" "${rc}" "${elapsed}" "${OMP_NUM_THREADS:-<unset-at-launch>}" >"${OUT_DIR}/thread_probe.json"
echo "thread probe: threads=${LABEL} exit=${rc} process_wall_seconds=${elapsed}"
exit "${rc}"
