#!/usr/bin/env bash
# Validate the juniper-cascor#531 fix end to end: the PATCHED direct CLI, run with NO thread
# environment set, must now behave like the service instead of like the old 2-thread-capped CLI.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-17
# Status:      ad-hoc -- one-off (2x remediation validation)
# Retire when: the fix is merged and the root-cause note is written; delete then.
# Related:     2026-08-17_h2h_thread_probe.bash; e-k-thread-probe-cap16.yaml.
#
# Reuses the E-K cell config, so this run shares dataset AND network initialisation with the
# service reference (961 s) and with the unpatched CLI arms (default 1492 s, OMP=16 1162 s).
# Expectation if the fix is correct: the patched default lands near the unpatched OMP=16 arm,
# because "default" now means "set nothing", which is what the service has always done.
#
# The base SHA moved from 3909d27 to 7fa2e66 between the campaign and the fix, but the only two
# commits in that range touch service-tier auth code (api/middleware.py, api/security.py,
# api/settings.py) and their tests -- nothing in the training path -- so the cross-SHA comparison
# against the earlier CLI arms holds.
#
# Usage: util/ad-hoc/2026-08-17_h2h_fix_verify.bash <PATCHED_CASCOR_SRC> <SUITE_DIR> <OUT_ROOT>
set -uo pipefail
PATCHED="${1:?usage: $0 <PATCHED_CASCOR_SRC> <SUITE_DIR> <OUT_ROOT>}"
SUITE="${2:?usage: see header}"
OUT="${3:?usage: see header}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

CELL="$(find "${SUITE}/cells" -mindepth 1 -maxdepth 1 -type d | sort | head -1)"
[[ -d "${CELL}" ]] || { echo "fix verify: no cell under ${SUITE}/cells" >&2; exit 2; }

UP="$(bash "${REPO_ROOT}/util/ad-hoc/2026-08-14_r5_stack_up.bash" 2>&1)" || { echo "${UP}" >&2; exit 2; }
RUN_ID="$(grep -oP '^RUN_ID=\K.*' <<<"${UP}")"
DATA_URL="$(grep -oP '^DATA_URL=\K.*' <<<"${UP}")"
[[ -n "${RUN_ID}" && -n "${DATA_URL}" ]] || { echo "${UP}" >&2; echo "fix verify: cannot parse stack banner" >&2; exit 2; }
echo "fix verify: stack ${RUN_ID} at ${DATA_URL}  patched src=${PATCHED}"

bash "${REPO_ROOT}/util/ad-hoc/2026-08-17_h2h_thread_probe.bash" \
    "${PATCHED}" "${CELL}/experiment.yaml" "${OUT}/patched-default" "${DATA_URL}" 7200 default
rc=$?

bash "${REPO_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >"${OUT}/teardown.log" 2>&1 \
    && echo "fix verify: stack ${RUN_ID} torn down" \
    || { echo "fix verify: TEARDOWN FAILED (see ${OUT}/teardown.log)" >&2; rc=1; }

echo "############ FIX VERIFY COMPLETE rc=${rc} ############"
exit "${rc}"
