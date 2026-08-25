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

bash "${REPO_ROOT}/util/experiment_stack.bash" --up --cascor --experiment r5-service-vs-cli
rc=$?
if ((rc != 0)); then
    echo "R-5: stack bring-up failed (exit ${rc})" >&2
    exit "${rc}"
fi

RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
# Newest run dir carrying a ports.json is the one just launched.
RUN_DIR="$(find "${RUN_ROOT}" -maxdepth 2 -name ports.json -printf '%T@ %h\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
[[ -n "${RUN_DIR}" ]] || { echo "R-5: could not locate the new run dir under ${RUN_ROOT}" >&2; exit 1; }

DATA_PORT="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['data'])" "${RUN_DIR}/ports.json")"
[[ -n "${DATA_PORT}" ]] || { echo "R-5: no data port in ${RUN_DIR}/ports.json" >&2; exit 1; }

echo "RUN_DIR=${RUN_DIR}"
echo "RUN_ID=$(basename "${RUN_DIR}")"
echo "DATA_URL=http://127.0.0.1:${DATA_PORT}"
