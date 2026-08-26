#!/usr/bin/env bash
# Run the post-#588 worker census (cascor#570) and the post-#563 worker profile (cascor#579) on one cap-4 cell.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-26
# Status:      ad-hoc -- one-off (handoff 2026-08-25 section 3.1 steps 2-3)
# Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline). Previously: cascor#570 and
#              #579 carry the census + profile results; delete then.
# Related:     util/ad-hoc/2026-08-17_h2h_thread_probe.bash (the probe this drives twice);
#              util/ad-hoc/2026-08-14_r5_stack_up.bash (one persistent data stack for both legs);
#              util/ad-hoc/2026-08-23_h2h_worker_profile_diff.py (reads the .prof this produces);
#              the auditor lives on the cascor branch diag/census-at67d7ea35-0339 (NOT for merge).
#
# WHY A SCRIPT
# Two legs share one data stack and one cell, but must NEVER share an output dir: re-using cli-01
# appends to its logs/juniper_cascor.log and doubles every count (handoff 2026-08-24 section 3.2's
# reuse class). Leg 1 arms the import auditor (JUNIPER_DIAG_IMPORT_LOG) -- the module reads the
# variable at import inside the forkserver, so it must be in the environment of the parent that
# starts the forkserver. Leg 2 leaves it unset (the auditor is then a defined-but-inert module) and
# sets JUNIPER_CASCOR_WORKER_PROFILE instead (cascor#567). The stack is torn down by RUN_ID from this
# script's own record, never with --all-mine.
#
# The controls are PRINTED, not judged: every zero must be checked for vacuity by the reader
# (a missing audit-logs dir = zero ledgers = a hollow zero; the auditor's _write() swallows errors).
#
# Usage: 2026-08-26_census_post588_run.bash <CASCOR_SRC> <CELL_YAML> <OUT_ROOT> [BOUND_SECONDS]
# Terminal markers: `census: done ->` on completion; `census: FAIL` on any pre-flight failure.
# Exit: 0 both legs attempted and stack torn down; 2 pre-flight failure.
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_ROOT> [BOUND_SECONDS]}"
CELL="${2:?usage: see header}"
OUT_ROOT="${3:?usage: see header}"
BOUND="${4:-360}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ML_ROOT="$(cd "${HERE}/../.." && pwd)"

[[ -d "${CASCOR_SRC}" ]] || { echo "census: FAIL cascor src not found: ${CASCOR_SRC}"; exit 2; }
[[ -f "${CELL}" ]] || { echo "census: FAIL cell not found: ${CELL}"; exit 2; }
if [[ -z "${JUNIPER_CASCOR_SENTRY_DSN:-${SENTRY_SDK_DSN:-}}" ]]; then
    echo "census: FAIL no Sentry DSN in the environment (by value) -- the Sentry negative would be meaningless"
    exit 2
fi
if ! grep -q '"sentry_sdk"' "${CASCOR_SRC}/cascade_correlation/cascade_correlation.py"; then
    echo "census: FAIL _diag_hot in ${CASCOR_SRC} does not name sentry_sdk -- edit the census worktree first"
    exit 2
fi
if ! grep -q '"sentry_sdk"' "${CASCOR_SRC}/cascor_diag_import_audit.py"; then
    echo "census: FAIL _WATCH in ${CASCOR_SRC}/cascor_diag_import_audit.py does not name sentry_sdk"
    exit 2
fi
if [[ -e "${OUT_ROOT}/cli-01" || -e "${OUT_ROOT}/cli-02" ]]; then
    echo "census: FAIL ${OUT_ROOT}/cli-0{1,2} already exists -- a NEW OUT_ROOT every time"
    exit 2
fi
mkdir -p "${OUT_ROOT}/audit-logs" "${OUT_ROOT}/prof" || { echo "census: FAIL cannot create ${OUT_ROOT}"; exit 2; }

echo "census: cascor $(git -C "${CASCOR_SRC}" rev-parse HEAD) branch $(git -C "${CASCOR_SRC}" rev-parse --abbrev-ref HEAD) | cell ${CELL} | out=${OUT_ROOT}"
cat >"${OUT_ROOT}/provenance.json" <<EOF
{"cascor_sha": "$(git -C "${CASCOR_SRC}" rev-parse HEAD)", "cascor_branch": "$(git -C "${CASCOR_SRC}" rev-parse --abbrev-ref HEAD)", "cascor_src": "${CASCOR_SRC}", "cell": "${CELL}", "bound": ${BOUND}, "started_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF

# --- one persistent data stack for both legs ---------------------------------------------------
stack_out="$(bash "${HERE}/2026-08-14_r5_stack_up.bash" 2>"${OUT_ROOT}/stack_up.log")" || {
    echo "census: FAIL stack bring-up failed; see ${OUT_ROOT}/stack_up.log"
    exit 2
}
RUN_ID="$(sed -n 's/^RUN_ID=//p' <<<"${stack_out}")"
DATA_URL="$(sed -n 's/^DATA_URL=//p' <<<"${stack_out}")"
[[ -n "${RUN_ID}" && -n "${DATA_URL}" ]] || { echo "census: FAIL could not parse RUN_ID/DATA_URL from: ${stack_out}"; exit 2; }
echo "${RUN_ID}" >"${OUT_ROOT}/stack_run_id"
echo "census: stack ${RUN_ID} DATA_URL=${DATA_URL}"

# --- leg 1: import-audit census (cascor#570) ---------------------------------------------------
echo "census: leg 1 (auditor armed) -> ${OUT_ROOT}/cli-01  load1=$(cut -d' ' -f1 /proc/loadavg)"
JUNIPER_DIAG_IMPORT_LOG="${OUT_ROOT}/audit-logs" \
    bash "${HERE}/2026-08-17_h2h_thread_probe.bash" "${CASCOR_SRC}" "${CELL}" "${OUT_ROOT}/cli-01" "${DATA_URL}" "${BOUND}" default
rc1=$?
echo "census: leg 1 rc=${rc1}"

# --- leg 2: worker cProfile (cascor#579), auditor inert -----------------------------------------
echo "census: leg 2 (worker profile) -> ${OUT_ROOT}/cli-02  load1=$(cut -d' ' -f1 /proc/loadavg)"
env -u JUNIPER_DIAG_IMPORT_LOG JUNIPER_CASCOR_WORKER_PROFILE="${OUT_ROOT}/prof" \
    bash "${HERE}/2026-08-17_h2h_thread_probe.bash" "${CASCOR_SRC}" "${CELL}" "${OUT_ROOT}/cli-02" "${DATA_URL}" "${BOUND}" default
rc2=$?
echo "census: leg 2 rc=${rc2}"

# --- teardown by our own RUN_ID ------------------------------------------------------------------
bash "${ML_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >"${OUT_ROOT}/stack_down.log" 2>&1
echo "census: stack ${RUN_ID} down rc=$?"

# --- controls (printed, not judged) --------------------------------------------------------------
echo "census: control 1 (parent resolved a DSN; legacy-name DeprecationWarning lines in cli-01/direct_cli.log): $(grep -c 'SENTRY_SDK_DSN is deprecated' "${OUT_ROOT}/cli-01/direct_cli.log" 2>/dev/null || echo 0)"
ledgers=$(find "${OUT_ROOT}/audit-logs" -name 'import_audit_*.log' | wc -l)
armed=$(grep -l 'auditor ARMED' "${OUT_ROOT}"/audit-logs/*.log 2>/dev/null | wc -l)
final=$(grep -l 'FINAL modules=' "${OUT_ROOT}"/audit-logs/*.log 2>/dev/null | wc -l)
firsts=$(grep -l 'FIRST-IMPORT' "${OUT_ROOT}"/audit-logs/*.log 2>/dev/null | wc -l)
echo "census: control 2 (ledgers): total=${ledgers} armed=${armed} final=${final} with_FIRST_IMPORT=${firsts}  (expect exactly one ARMED+FINAL = the forkserver; child ledgers expected ZERO on the fixed build)"
grep -h 'FINAL modules=' "${OUT_ROOT}"/audit-logs/*.log 2>/dev/null | sed 's/^/census:   /'
grep -h 'FIRST-IMPORT' "${OUT_ROOT}"/audit-logs/*.log 2>/dev/null | sed 's/^/census:   /'
diag_lines=$(cat "${OUT_ROOT}"/cli-01/logs/juniper_cascor.log* 2>/dev/null | grep -c '_worker_loop: DIAG-ENV')
echo "census: control 3 (DIAG-ENV census lines in cli-01 trainer log): ${diag_lines}  (expect 7-8)"
cat "${OUT_ROOT}"/cli-01/logs/juniper_cascor.log* 2>/dev/null | grep '_worker_loop: DIAG-ENV' | sed -E 's/.*(pid=[0-9]+ start_method=[a-z]+ parent=[0-9]+ sys_modules=[0-9]+ present=\[[^]]*\]).*/census:   \1/'
echo "census: profile: $(find "${OUT_ROOT}/prof" -name '*.prof' | wc -l) .prof files in ${OUT_ROOT}/prof"
echo "census: done -> ${OUT_ROOT}"
