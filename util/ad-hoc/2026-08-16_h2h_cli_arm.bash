#!/usr/bin/env bash
# WIDE-BUDGET HEAD-TO-HEAD -- the direct-CLI arm of one replicate.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-16
# Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the wide-budget head-to-head evidence note is merged; delete then.
# Related:     supersedes util/ad-hoc/2026-08-14_fp13_verify_fix.bash for THIS campaign;
#              util/experiments/suites/p4/e-j-h2h-wide-cap{64,128}.yaml (the service arm);
#              util/ad-hoc/2026-08-16_h2h_collect.py (reads what this writes).
#
# WHAT IT DOES DIFFERENTLY FROM THE fp13 RUNNER
#
# 1. PER-RUN PARENT LOG. juniper-cascor#523 (in the checkout as of 3909d27) made the direct CLI
#    honour JUNIPER_CASCOR_LOG_DIR, so this exports it at <OUT_DIR>/logs and gets a COMPLETE,
#    unrotatable parent log instead of a line-count slice of the checkout-shared file. That
#    removes the rotation hazard that destroyed the 2026-08-14 arm evidence outright rather than
#    merely warning about it. (A dedicated checkout is still used -- belt and braces, and it
#    makes "which checkout ran which arm" unambiguous in the write-up.)
#    The constant resolves at IMPORT time, so the export must precede the process, not the fit.
#
# 2. A SHARED WALL-CLOCK DENOMINATOR. The smoke run could not report a ratio because the service
#    figure was the driver's poll-based drive loop and the CLI figure was whole-process wall
#    including interpreter start and dataset fetch -- no common span. Both paths run the same
#    CascadeCorrelationNetwork.fit and emit the same bracketing pair,
#      cascade_correlation.py:1918  "fit: Starting main training loop with max_epochs: ..."
#      cascade_correlation.py:1936  "fit: Training completed."
#    at second resolution. With #523 the SERVICE arm now writes that pair into its own run dir
#    too (verified live 2026-08-16), so the training span between them is measurable on both
#    paths and is the denominator this campaign reports. Whole-process wall is still recorded,
#    but as a separate, explicitly non-comparable column.
#
# The matplotlib backend is deliberately INHERITED (MPLBACKEND left alone), matching the smoke
# run's conditions; --no-plots plus the juniper-cascor#517 backend guard is what prevents the
# post-training hang.
#
# Usage: util/ad-hoc/2026-08-16_h2h_cli_arm.bash <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS>
#   CASCOR_SRC  the DEDICATED cascor checkout's src/ dir
#   CELL_YAML   the suite-generated cells/<cell_id>/experiment.yaml -- NOT the base config
#   OUT_DIR     where this arm's evidence is written
# Exit: 0 clean; 2 usage/pre-flight; otherwise the CLI's own exit code.
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS>}"
CONFIG="${2:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS>}"
OUT_DIR="${3:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS>}"
DATA_URL="${4:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS>}"
BOUND="${5:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS>}"

PY="${JUNIPER_H2H_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"

[[ -d "${CASCOR_SRC}" ]] || { echo "h2h cli arm: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -f "${CONFIG}" ]] || { echo "h2h cli arm: config not found: ${CONFIG}" >&2; exit 2; }
[[ -x "${PY}" ]] || { echo "h2h cli arm: python not found: ${PY}" >&2; exit 2; }

mkdir -p "${OUT_DIR}/logs" || exit 2
CASCOR_SRC="$(realpath "${CASCOR_SRC}")"
CONFIG="$(realpath "${CONFIG}")"
OUT_DIR="$(realpath "${OUT_DIR}")"

# Refuse the base config outright. Handing this arm the hand-written base instead of the
# suite-generated cell file is THE silent failure of this campaign: every CLI replicate would
# train on one seed while the service arm varied, and the resulting "agreement" would be an
# artifact. The equalisation check catches it afterwards; catching it here is free.
case "${CONFIG}" in
    */cells/*/experiment.yaml) ;;
    *) echo "h2h cli arm: REFUSING ${CONFIG} -- expected a suite-generated cells/<cell_id>/experiment.yaml, not the base config" >&2; exit 2 ;;
esac

export LD_LIBRARY_PATH=""
export JUNIPER_DATA_URL="${DATA_URL}"
# cascor#523: resolved at cascor_constants IMPORT time, so it must be exported before the exec.
export JUNIPER_CASCOR_LOG_DIR="${OUT_DIR}/logs"
PARENT_LOG="${OUT_DIR}/logs/juniper_cascor.log"

echo "h2h cli arm: src=${CASCOR_SRC}"
echo "h2h cli arm: config=${CONFIG}"
echo "h2h cli arm: parent log=${PARENT_LOG} (per-run, via JUNIPER_CASCOR_LOG_DIR)"
echo "h2h cli arm: data=${DATA_URL}  bound=${BOUND}s  backend=INHERITED"

cd "${CASCOR_SRC}" || exit 2

start=$(date +%s)
# `>>` (O_APPEND), never `>`: a truncating redirect gives every forked child a shared, non-append
# file offset, so an orphaned worker flushing after the kill overwrites whatever the shell
# appended in the meantime. That destroyed a runner's verdict line on the 2026-08-14 run.
: >"${OUT_DIR}/direct_cli.log"
timeout --foreground --kill-after=30s "${BOUND}" \
    "${PY}" main.py --config "${CONFIG}" --no-plots >>"${OUT_DIR}/direct_cli.log" 2>&1
rc=$?
end=$(date +%s)
elapsed=$((end - start))

pkill -f "main.py --config ${CONFIG}" 2>/dev/null
sleep 2   # let any reaped children flush before the parent log is read

if [[ -f "${PARENT_LOG}" ]]; then
    echo "h2h cli arm: parent log $(wc -l <"${PARENT_LOG}") lines -> ${PARENT_LOG}"
else
    echo "h2h cli arm: WARNING no parent log at ${PARENT_LOG} -- the training-span markers are not preserved"
fi

printf '{"arm":"cli","config":"%s","cascor_src":"%s","exit_code":%d,"process_wall_seconds":%d,"bound_seconds":%s,"parent_log":"%s"}\n' \
    "${CONFIG}" "${CASCOR_SRC}" "${rc}" "${elapsed}" "${BOUND}" "${PARENT_LOG}" >"${OUT_DIR}/cli_arm.json"

echo "h2h cli arm: exit=${rc} process_wall_seconds=${elapsed}" | tee -a "${OUT_DIR}/direct_cli.log"
if ((elapsed >= BOUND)); then
    echo "h2h cli arm: HIT THE ${BOUND}s BOUND (exit ${rc}) -- this arm is NOT a completed run"
elif ((rc == 0)); then
    echo "h2h cli arm: completed cleanly in ${elapsed}s"
else
    echo "h2h cli arm: terminated in ${elapsed}s with exit ${rc} -- inspect ${OUT_DIR}/direct_cli.log"
fi
exit "${rc}"
