#!/usr/bin/env bash
# WIDE-BUDGET HEAD-TO-HEAD -- run the init-control cell on both arms.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-16
# Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the wide-budget head-to-head evidence note is merged; delete then.
# Related:     util/experiments/suites/p4/e-j-h2h-wide-cap64-init42.yaml (the cell, and the full
#              rationale); 2026-08-16_h2h_orchestrate.bash (the main campaign this follows).
#
# The main campaign equalises everything except the network initialisation, which cannot be
# equalised through configuration: the service network always seeds from _PROJECT_RANDOM_SEED = 42
# and TrainingParams carries no seed field, while the direct CLI threads the DATASET seed into the
# network. Setting the dataset seed to 42 is the one configuration that lands BOTH arms on init 42,
# so this cell is the only place in the campaign where a path difference is a measurable quantity
# rather than a confounded one.
#
# Same two steps as any other replicate -- service arm via run_suite, CLI arm over the generated
# cell file -- kept as its own script so the control can be re-run, or run alone, without dragging
# the whole campaign along.
#
# Usage: util/ad-hoc/2026-08-16_h2h_init_control.bash <CLI_ROOT> <CASCOR_SRC>
# Exit:  0 both arms ran; 1 an arm reported failure; 2 a hard failure stopped it.
set -uo pipefail

CLI_ROOT="${1:?usage: $0 <CLI_ROOT> <CASCOR_SRC>}"
CASCOR_SRC="${2:?usage: $0 <CLI_ROOT> <CASCOR_SRC>}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
PY="${JUNIPER_H2H_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

soft=0
echo "############ $(date '+%H:%M:%S') INIT CONTROL 1/2 -- service arm ############"
"${PY}" "${REPO_ROOT}/util/experiments/run_suite.py" --suite "${REPO_ROOT}/util/experiments/suites/p4/e-j-h2h-wide-cap64-init42.yaml"
rc=$?
((rc == 2)) && { echo "init control: suite validation failure -- stopping" >&2; exit 2; }
((rc == 0)) || soft=1

SUITE_DIR="$(find "${RUN_ROOT}/suites" -maxdepth 1 -name 'e-j-h2h-wide-cap64-init42-*' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
[[ -d "${SUITE_DIR}/cells" ]] || { echo "init control: cannot locate the suite dir" >&2; exit 2; }

echo "############ $(date '+%H:%M:%S') INIT CONTROL 2/2 -- direct-CLI arm ############"
bash "${REPO_ROOT}/util/ad-hoc/2026-08-16_h2h_cli_campaign.bash" "${SUITE_DIR}" "${CLI_ROOT}" "${CASCOR_SRC}"
rc=$?
((rc == 2)) && { echo "init control: CLI arm hard failure" >&2; exit 2; }
((rc == 0)) || soft=1

echo "############ $(date '+%H:%M:%S') INIT CONTROL COMPLETE (soft=${soft}) ############"
echo "init control: suite dir = ${SUITE_DIR}"
exit "${soft}"
