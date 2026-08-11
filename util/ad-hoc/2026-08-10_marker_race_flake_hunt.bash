#!/usr/bin/env bash
# Repeat-run a unittest module to surface an intermittent (flaky) failure and name it.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-10
# Status:     ad-hoc -- investigation
# Retire when: a general flake-hunt harness graduates to util/ proper. Kept (not deleted
#              with its originating fix) because it is module-agnostic: the next
#              intermittent failure in any unittest module is hunted with the same tool.
# Related:    ml#1045 flake; the isolated-stack marker-atomicity fix. Reproducing the
#             marker race needed CPU contention -- two concurrent hunts, not one; a
#             40-run solo hunt was clean while a contended 25-run hunt failed on run 2.
#
# Usage: util/ad-hoc/2026-08-10_marker_race_flake_hunt.bash [ITERATIONS] [MODULE]
# Exit:  0 = every iteration passed; 1 = at least one iteration failed.
set -euo pipefail

ITERATIONS="${1:-40}"
MODULE="${2:-tests.test_isolated_stack_script}"
LOG_DIR="$(mktemp -d -t juniper-flake-hunt-XXXXXX)"

pass=0
fail=0
declare -a failed_tests=()

for ((i = 1; i <= ITERATIONS; i++)); do
    log="${LOG_DIR}/run_${i}.log"
    if python3 -m unittest "${MODULE}" -v >"${log}" 2>&1; then
        pass=$((pass + 1))
        rm -f "${log}"
    else
        fail=$((fail + 1))
        echo "=== FAILURE on iteration ${i} (log: ${log}) ==="
        # Name every failing/erroring test so the flake is identified, not just counted.
        while IFS= read -r line; do
            echo "    ${line}"
            failed_tests+=("${line}")
        done < <(grep -E '^(FAIL|ERROR): ' "${log}" || true)
        # The assertion text is what distinguishes a marker race from a real defect.
        grep -E '^(AssertionError|[A-Za-z_.]*Error):' "${log}" | head -5 | sed 's/^/    | /' || true
    fi
done

echo ""
echo "HUNT DONE: ${pass} passed, ${fail} failed, of ${ITERATIONS} runs of ${MODULE}"
if ((fail > 0)); then
    echo "Distinct failing tests:"
    printf '%s\n' "${failed_tests[@]}" | sort -u | sed 's/^/  /'
    echo "Failure logs retained under: ${LOG_DIR}"
    exit 1
fi

rmdir "${LOG_DIR}" 2>/dev/null || true
exit 0
