#!/usr/bin/env bash
# F-P1-3 CONTROL arm — run the cascor direct CLI with the INHERITED matplotlib backend.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-14
# Status:      ad-hoc -- one-off (F-P1-3 root-cause control)
# Retire when: F-P1-3 is written up and merged; delete then.
# Related:     P1 finding F-P1-3 / F-P1-3b; R-5 §2.1; runner 2026-08-14_r5_run_direct_cli.bash
#
# The TREATMENT arm (same runner, MPLBACKEND=Agg) completed in 39 s, exit 0. This arm changes
# exactly one variable back — the matplotlib backend — to show the hang is the terminal
# plt.show()/plotter.join() pair and NOT the training budget or cascor#514.
#
# Bounded on purpose: the whole point is that it does not terminate. After the bound expires
# the process tree is torn down, because a blocked parent keeps a forkserver (and its GPU
# children) alive.
#
# Usage: util/ad-hoc/2026-08-14_fp13_control_tkagg.bash <CONFIG_YAML> <OUT_DIR> <DATA_URL> [BOUND_SECONDS]
# Exit:  0 if the CLI completed within the bound (diagnosis WRONG); 124 if it hung (diagnosis CONFIRMED).
set -uo pipefail

CONFIG="${1:?usage: $0 <CONFIG_YAML> <OUT_DIR> <DATA_URL> [BOUND_SECONDS]}"
OUT_DIR="${2:?usage: $0 <CONFIG_YAML> <OUT_DIR> <DATA_URL> [BOUND_SECONDS]}"
DATA_URL="${3:?usage: $0 <CONFIG_YAML> <OUT_DIR> <DATA_URL> [BOUND_SECONDS]}"
BOUND="${4:-240}"
CASCOR_SRC="${JUNIPER_R5_CASCOR_SRC:-/home/pcalnon/Development/python/Juniper/juniper-cascor/src}"
PY="${JUNIPER_R5_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"

[[ -f "${CONFIG}" ]] || { echo "F-P1-3: config not found: ${CONFIG}" >&2; exit 2; }
[[ -d "${CASCOR_SRC}" ]] || { echo "F-P1-3: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -x "${PY}" ]] || { echo "F-P1-3: python not found: ${PY}" >&2; exit 2; }

mkdir -p "${OUT_DIR}" || exit 2
CONFIG="$(realpath "${CONFIG}")"
OUT_DIR="$(realpath "${OUT_DIR}")"

# Same environment as the treatment arm except MPLBACKEND, which is deliberately NOT set so
# matplotlib resolves its own default (tkagg under DISPLAY=:0 on this host).
export LD_LIBRARY_PATH=""
export JUNIPER_DATA_URL="${DATA_URL}"
unset MPLBACKEND

echo "F-P1-3 control: config=${CONFIG}"
echo "F-P1-3 control: backend=INHERITED (MPLBACKEND unset)  bound=${BOUND}s"
echo "F-P1-3 control: data=${JUNIPER_DATA_URL}"

cd "${CASCOR_SRC}" || exit 2
start=$(date +%s)
# --foreground so the bound applies to the python process itself, and KILL after a short
# grace because a Tk mainloop does not always honour TERM promptly.
timeout --foreground --kill-after=10s "${BOUND}" \
    "${PY}" main.py --config "${CONFIG}" >"${OUT_DIR}/direct_cli_control.log" 2>&1
rc=$?
end=$(date +%s)

# A hung parent keeps its forkserver (and any GPU-holding children) alive; reap this run's
# tree explicitly rather than leaving it for the next campaign to trip over.
pkill -f "${CASCOR_SRC}/main.py --config ${CONFIG}" 2>/dev/null
pkill -f "main.py --config ${CONFIG}" 2>/dev/null

elapsed=$((end - start))
echo "F-P1-3 control: exit=${rc} wall_seconds=${elapsed}" | tee -a "${OUT_DIR}/direct_cli_control.log"

# Verdict keys on REACHING THE BOUND, not on a specific rc: `timeout` reports 124 on TERM and
# 137 on SIGKILL, but the --kill-after path was observed returning 125 here. rc alone is
# therefore not a reliable hang signal — elapsed >= bound is.
if ((elapsed >= BOUND)); then
    echo "F-P1-3 control: HUNG at the ${BOUND}s bound (exit ${rc}) — diagnosis CONFIRMED"
    echo "F-P1-3 control: cross-check — the run must have NO 'Completed solving SpiralProblem instance' line:"
    echo "F-P1-3 control:   grep -c 'Completed solving SpiralProblem instance' <cascor repo>/logs/juniper_cascor.log"
else
    echo "F-P1-3 control: completed in ${elapsed}s (exit ${rc}) — diagnosis NOT confirmed; re-examine"
fi
exit "${rc}"
