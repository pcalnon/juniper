#!/usr/bin/env bash
# Run the cascor DIRECT CLI (src/main.py) under an experiment YAML — R-5 arm C.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-14
# Status:      ad-hoc -- one-off (R-5 arm C runner)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: R-5 is written up and merged; delete then.
# Related:     P4 §7 R-5; premise check util/ad-hoc/2026-08-13_spiral_service_vs_cli_compare.py
#
# Exists because the direct CLI must run with cwd == juniper-cascor/src: main.py relies on
# sys.path[0] for its `spiral_problem` / `cascade_correlation` imports AND writes
# logs/juniper_cascor.log relative to cwd. Invoking it from anywhere else scatters logs into
# the caller's tree.
#
# Runs against the cascor PRIMARY CHECKOUT on main, deliberately: the 0.735 service anchor
# (c010) was measured on that code, and cascor#514 (the #505 candidate-patience fix) would
# change the candidate operating point mid-comparison.
#
# The CLI is NOT self-contained: SpiralProblem.generate_n_spiral_dataset delegates to
# SpiralDataProvider against juniper-data (the local generators are deprecated), so a data
# URL is required and the dataset both paths train on comes from the same service.
#
# Usage: util/ad-hoc/2026-08-14_r5_run_direct_cli.bash <CONFIG_YAML> <OUT_DIR> <DATA_URL>
# Exit:  the CLI's own exit code.
set -uo pipefail

CONFIG="${1:?usage: $0 <CONFIG_YAML> <OUT_DIR> <DATA_URL>}"
OUT_DIR="${2:?usage: $0 <CONFIG_YAML> <OUT_DIR> <DATA_URL>}"
DATA_URL="${3:?usage: $0 <CONFIG_YAML> <OUT_DIR> <DATA_URL>}"
CASCOR_SRC="${JUNIPER_R5_CASCOR_SRC:-/home/pcalnon/Development/python/Juniper/juniper-cascor/src}"
PY="${JUNIPER_R5_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"

[[ -f "${CONFIG}" ]] || { echo "R-5: config not found: ${CONFIG}" >&2; exit 2; }
[[ -d "${CASCOR_SRC}" ]] || { echo "R-5: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -x "${PY}" ]] || { echo "R-5: python not found: ${PY}" >&2; exit 2; }

mkdir -p "${OUT_DIR}" || exit 2
CONFIG="$(realpath "${CONFIG}")"
OUT_DIR="$(realpath "${OUT_DIR}")"

# The direct CLI has no juniper-data dependency (it generates its own spiral), so nothing
# here points at a data service. Keep torch off the ambient LD_LIBRARY_PATH the same way the
# isolated/experiment stacks do.
#
# Deliberately NO `PYTHON_GIL=0`: the experiment stack sets it for juniper-data's
# free-threaded python3.14t, but JuniperCascor1 is a normal GIL build and aborts at
# interpreter preinit with `config_read_gil: Disabling the GIL is not supported by this
# build`.
export LD_LIBRARY_PATH=""
export JUNIPER_DATA_URL="${DATA_URL}"

echo "R-5 arm C: config=${CONFIG}"
echo "R-5 arm C: cwd=${CASCOR_SRC}  python=${PY}"
echo "R-5 arm C: data=${JUNIPER_DATA_URL}"
echo "R-5 arm C: out=${OUT_DIR}"

cd "${CASCOR_SRC}" || exit 2
start=$(date +%s)
"${PY}" main.py --config "${CONFIG}" 2>&1 | tee "${OUT_DIR}/direct_cli.log"
rc=${PIPESTATUS[0]}
end=$(date +%s)

echo "R-5 arm C: exit=${rc} wall_seconds=$((end - start))" | tee -a "${OUT_DIR}/direct_cli.log"
exit "${rc}"
