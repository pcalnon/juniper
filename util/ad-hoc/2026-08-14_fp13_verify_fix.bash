#!/usr/bin/env bash
# F-P1-3 VERIFY — run the cascor direct CLI from an arbitrary checkout with arbitrary flags,
# under a hard bound, and report whether it terminated.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-14
# Status:      ad-hoc -- one-off (F-P1-3 fix verification)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: F-P1-3 is written up and the cascor fix is merged; delete then.
# Related:     control arm 2026-08-14_fp13_control_tkagg.bash; P1 finding F-P1-3 / F-P1-3b
#
# Differs from the control arm in two ways: the cascor checkout is a parameter (so the FIXED
# worktree can be exercised against the same dataset service), and trailing arguments are
# forwarded to main.py (so `--no-plots` can be exercised).
#
# The matplotlib backend is deliberately INHERITED — on this host DISPLAY=:0 makes it tkagg,
# which is precisely the condition under which the unfixed CLI hangs. Do not set MPLBACKEND
# here: that would mask the very thing being verified.
#
# Usage: util/ad-hoc/2026-08-14_fp13_verify_fix.bash <CASCOR_SRC> <CONFIG_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS> [-- <main.py args...>]
# Exit:  the CLI's exit code (0 = terminated cleanly); nonzero/bound = still hanging.
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> <CONFIG_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS> [-- args...]}"
CONFIG="${2:?usage: $0 <CASCOR_SRC> <CONFIG_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS> [-- args...]}"
OUT_DIR="${3:?usage: $0 <CASCOR_SRC> <CONFIG_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS> [-- args...]}"
DATA_URL="${4:?usage: $0 <CASCOR_SRC> <CONFIG_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS> [-- args...]}"
BOUND="${5:?usage: $0 <CASCOR_SRC> <CONFIG_YAML> <OUT_DIR> <DATA_URL> <BOUND_SECONDS> [-- args...]}"
shift 5
[[ "${1:-}" == "--" ]] && shift
EXTRA_ARGS=("$@")

PY="${JUNIPER_R5_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"

[[ -d "${CASCOR_SRC}" ]] || { echo "F-P1-3 verify: cascor src not found: ${CASCOR_SRC}" >&2; exit 2; }
[[ -f "${CONFIG}" ]] || { echo "F-P1-3 verify: config not found: ${CONFIG}" >&2; exit 2; }
[[ -x "${PY}" ]] || { echo "F-P1-3 verify: python not found: ${PY}" >&2; exit 2; }

mkdir -p "${OUT_DIR}" || exit 2
CASCOR_SRC="$(realpath "${CASCOR_SRC}")"
CONFIG="$(realpath "${CONFIG}")"
OUT_DIR="$(realpath "${OUT_DIR}")"

# The log dir is derived from the checkout root (constants.py: _PROJECT_DIR =
# _PROJECT_SOURCE_DIR.parent), and logger init raises FileNotFoundError when it is absent —
# a fresh worktree has no logs/. Create it rather than have the run die before it starts.
mkdir -p "${CASCOR_SRC}/../logs" || exit 2

export LD_LIBRARY_PATH=""
export JUNIPER_DATA_URL="${DATA_URL}"
unset MPLBACKEND

echo "F-P1-3 verify: src=${CASCOR_SRC}"
echo "F-P1-3 verify: backend=INHERITED (MPLBACKEND unset)  bound=${BOUND}s"
echo "F-P1-3 verify: extra args=${EXTRA_ARGS[*]:-<none>}"

cd "${CASCOR_SRC}" || exit 2

# The parent's own logger writes to <checkout>/logs/juniper_cascor.log, NOT to stdout — stdout
# carries only the candidate workers, so the completion marker that decides this run's verdict is
# not in the stdout capture at all. Record the pre-run length and slice the run's own portion out
# afterwards. Reliable only when CASCOR_SRC is a DEDICATED checkout/worktree: a shared one gets
# rotated out from under you by any other cascor writing to it (a live service rotates ~15 MB
# files in minutes, which is exactly how the 2026-08-14 arm evidence was lost).
PARENT_LOG="${CASCOR_SRC}/../logs/juniper_cascor.log"
parent_log_before=0
[[ -f "${PARENT_LOG}" ]] && parent_log_before=$(wc -l <"${PARENT_LOG}")

start=$(date +%s)
# `>>` (O_APPEND), never `>`: a truncating redirect gives every forked child a shared, non-append
# file offset, so an orphaned worker flushing after the kill overwrites whatever the shell appended
# in the meantime. That destroyed the sibling runner's verdict line on the 2026-08-14 run.
: >"${OUT_DIR}/direct_cli_verify.log"
timeout --foreground --kill-after=10s "${BOUND}" \
    "${PY}" main.py --config "${CONFIG}" "${EXTRA_ARGS[@]}" >>"${OUT_DIR}/direct_cli_verify.log" 2>&1
rc=$?
end=$(date +%s)
elapsed=$((end - start))

pkill -f "main.py --config ${CONFIG}" 2>/dev/null
sleep 2   # let any reaped children finish flushing before the parent log is sliced

if [[ -f "${PARENT_LOG}" ]]; then
    parent_log_after=$(wc -l <"${PARENT_LOG}")
    if ((parent_log_after >= parent_log_before)); then
        tail -n +$((parent_log_before + 1)) "${PARENT_LOG}" >"${OUT_DIR}/parent_juniper_cascor.log"
        echo "F-P1-3 verify: parent log slice -> ${OUT_DIR}/parent_juniper_cascor.log ($((parent_log_after - parent_log_before)) lines)"
    else
        echo "F-P1-3 verify: WARNING parent log shrank (rotated mid-run) — slice not preserved; re-run from a DEDICATED worktree"
    fi
else
    echo "F-P1-3 verify: WARNING no parent log at ${PARENT_LOG} — the completion marker is not preserved"
fi

echo "F-P1-3 verify: exit=${rc} wall_seconds=${elapsed}" | tee -a "${OUT_DIR}/direct_cli_verify.log"
if ((elapsed >= BOUND)); then
    echo "F-P1-3 verify: STILL HANGING at the ${BOUND}s bound (exit ${rc}) — fix did NOT take"
elif ((rc == 0)); then
    echo "F-P1-3 verify: TERMINATED cleanly in ${elapsed}s (exit 0) — fix verified"
else
    echo "F-P1-3 verify: terminated in ${elapsed}s with exit ${rc} — not a hang, but inspect the log"
fi
exit "${rc}"
