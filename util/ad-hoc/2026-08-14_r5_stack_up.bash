#!/usr/bin/env bash
# Bring up a per-run experiment stack for the R-5 direct-CLI arms and print its data URL.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-14
# Status:      ad-hoc -- one-off (R-5 helper)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: R-5 is written up and merged; delete then.
#
# The direct CLI needs juniper-data (SpiralDataProvider), and experiment_stack.bash --up
# requires an app arm, so --cascor is used purely to get a data service; the cascor process
# it starts is left idle and unused by these arms.
#
# JUNIPER_EXP_PROJECT_DIR is load-bearing when running from a worktree: without it the
# launcher's base_config derivation lands in .claude/worktrees/juniper-cascor/... and every
# leg fails to materialise.
#
# Usage: util/ad-hoc/2026-08-14_r5_stack_up.bash
# Exit:  0 with "RUN_ID=<id>" and "DATA_URL=<url>" on stdout; nonzero on bring-up failure.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"

# Capture the launcher's own output: it prints its RUN_ID on the teardown line, and that is the
# ONLY authoritative record of which stack this invocation created.
#
# HAZARD THIS FIXES (observed 2026-08-29). The previous implementation resolved the run dir as
# "newest run dir carrying a ports.json" under a run-root shared by every session on the host.
# A concurrent service leg -- run_suite brings a stack up and tears it down per cell -- creates a
# newer ports.json mid-flight, so the CLI arm silently pointed at ANOTHER run's data service.
# Nothing failed: the wrong service answers healthily and returns a dataset, so the comparison is
# quietly invalid. The paired-campaign script's own header warns about exactly this class
# ("a service leg coming up mid-campaign would otherwise silently re-point the CLI arm at the
# wrong data service") and passes DATA_URL explicitly to avoid it; this script did not.
LAUNCH_LOG="$(mktemp -t r5-stack-up-XXXXXX.log)"
trap 'rm -f "${LAUNCH_LOG}"' EXIT
bash "${REPO_ROOT}/util/experiment_stack.bash" --up --cascor --experiment r5-service-vs-cli 2>&1 | tee "${LAUNCH_LOG}"
rc="${PIPESTATUS[0]}"
if ((rc != 0)); then
    echo "R-5: stack bring-up failed (exit ${rc})" >&2
    exit "${rc}"
fi

# `experiment_stack.bash` prints:  teardown   : experiment_stack.bash --down <RUN_ID>
RUN_ID="$(sed -n 's/.*--down \([0-9]\{8\}T[0-9]\{6\}Z-[0-9a-f]\{4\}\).*/\1/p' "${LAUNCH_LOG}" | head -1)"
if [[ -z "${RUN_ID}" ]]; then
    # Refuse rather than fall back to the newest-ports.json heuristic. A wrong DATA_URL does not
    # fail loudly -- it produces a run against someone else's dataset -- so guessing is worse
    # than stopping.
    echo "R-5: could not parse RUN_ID from the launcher output; refusing to guess the run dir" >&2
    echo "R-5: (a silently-wrong DATA_URL yields a valid-looking run against the wrong data)" >&2
    exit 1
fi
RUN_DIR="${RUN_ROOT}/${RUN_ID}"
[[ -f "${RUN_DIR}/ports.json" ]] || { echo "R-5: ${RUN_DIR}/ports.json missing for parsed RUN_ID ${RUN_ID}" >&2; exit 1; }

DATA_PORT="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['data'])" "${RUN_DIR}/ports.json")"
[[ -n "${DATA_PORT}" ]] || { echo "R-5: no data port in ${RUN_DIR}/ports.json" >&2; exit 1; }

echo "RUN_DIR=${RUN_DIR}"
echo "RUN_ID=$(basename "${RUN_DIR}")"
echo "DATA_URL=http://127.0.0.1:${DATA_PORT}"
