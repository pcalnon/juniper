#!/usr/bin/env bash
# Native-profile ONE direct-CLI leg, matching the service leg's py-spy settings exactly.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-23
# Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
# Retire when: the residual wall-gap evidence note is merged; delete then.
# Related:     2026-08-23_pyspy_conda_shim.bash (the SERVICE-side counterpart).
#
# The CLI side needs no shim: py-spy can spawn `python main.py` itself, so it is already the parent
# and ptrace_scope=1 is satisfied. What it DOES need is to match the service leg's sampling settings
# exactly -- same --rate, same --native, same --subprocesses, same blocking mode -- because the
# output is a RATIO between the two arms and any asymmetry in the instrument goes straight into it.
#
# The environment below is thread_probe.bash's, reproduced rather than reused: that script execs the
# CLI itself, so it cannot be wrapped without py-spy losing the parent relationship. `default`
# thread behaviour means the BLAS variables are UNSET -- verified equivalent to an explicit 16 in
# the 2026-08-22 thread sweep (1.033x, CI includes 1.0).
#
# Usage: 2026-08-23_pyspy_cli_leg.bash <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> [RATE]
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> [RATE]}"
CELL="${2:?usage: see header}"
OUT_DIR="${3:?usage: see header}"
DATA_URL="${4:?usage: see header}"
RATE="${5:-100}"

PYSPY="${JUNIPER_PYSPY:-/opt/miniforge3/envs/JuniperCascor1/bin/py-spy}"
PY="${JUNIPER_H2H_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
[[ -x "${PYSPY}" ]] || { echo "cli-leg: py-spy not found: ${PYSPY}" >&2; exit 2; }
[[ -d "${CASCOR_SRC}" ]] || { echo "cli-leg: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -f "${CELL}" ]] || { echo "cli-leg: cell not found: ${CELL}" >&2; exit 2; }

mkdir -p "${OUT_DIR}/logs" || exit 2
OUT_DIR="$(realpath "${OUT_DIR}")"
CELL="$(realpath "${CELL}")"

export LD_LIBRARY_PATH=""
export JUNIPER_DATA_URL="${DATA_URL}"
export JUNIPER_CASCOR_LOG_DIR="${OUT_DIR}/logs"
unset OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS

cd "${CASCOR_SRC}" || exit 2
echo "cli-leg: py-spy --native --subprocesses --rate ${RATE} -> ${OUT_DIR}/cli.raw"
start=$(date +%s)
"${PYSPY}" record --subprocesses --native --rate "${RATE}" \
    --format raw --output "${OUT_DIR}/cli.raw" \
    -- "${PY}" main.py --config "${CELL}" --no-plots >"${OUT_DIR}/direct_cli.log" 2>&1
rc=$?
echo "cli-leg: exit=${rc} wall=$(( $(date +%s) - start ))s"
exit "${rc}"
