#!/usr/bin/env bash
# WIDE-BUDGET HEAD-TO-HEAD -- run the remaining campaign phases back to back.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-16
# Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
# Retire when: the wide-budget head-to-head evidence note is merged; delete then.
# Related:     the e-j-h2h-wide-cap{64,128} suites; 2026-08-16_h2h_cli_campaign.bash.
#
# The campaign is four sequential phases -- cap-64 service, cap-64 CLI, cap-128 service, cap-128
# CLI -- and they MUST stay sequential. Two arms sharing 16 cores would inflate both walls, and a
# wall-clock comparison is the whole point of this campaign (the workload is CPU-bound: ~8
# candidate workers at ~80% each, GPU utilisation ~1%).
#
# ORDER IS DELIBERATE: each cap is finished on BOTH arms before the next cap starts. If the
# campaign has to be cut short, that leaves a complete, quotable cap-64 result rather than a
# cap-128 service column with no CLI counterpart. (Cap-128 is the expensive half -- E-I measured
# 4244 s vs 2907 s for comparable service cells.)
#
# Phase 1 is normally already running when this is invoked; pass its suite dir as PHASE1_SUITE_DIR
# and this picks up at phase 2. A hard failure (bring-up, misuse) stops the chain; individual cell
# failures do not -- a partial cap is still evidence, and the collector reports what is missing.
#
# Usage: util/ad-hoc/2026-08-16_h2h_orchestrate.bash <PHASE1_SUITE_DIR> <CLI_ROOT> <CASCOR_SRC>
# Exit:  0 all phases ran; 1 a phase reported failures; 2 a hard failure stopped the chain.
set -uo pipefail

PHASE1_SUITE_DIR="${1:?usage: $0 <PHASE1_SUITE_DIR> <CLI_ROOT> <CASCOR_SRC>}"
CLI_ROOT="${2:?usage: $0 <PHASE1_SUITE_DIR> <CLI_ROOT> <CASCOR_SRC>}"
CASCOR_SRC="${3:?usage: $0 <PHASE1_SUITE_DIR> <CLI_ROOT> <CASCOR_SRC>}"

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
PY="${JUNIPER_H2H_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
export JUNIPER_EXP_HEALTH_TIMEOUT="${JUNIPER_EXP_HEALTH_TIMEOUT:-180}"

soft_fail=0
say() { echo ""; echo "############ $(date '+%H:%M:%S') $* ############"; }

say "PHASE 2/4 -- cap-64 direct-CLI arms"
bash "${REPO_ROOT}/util/ad-hoc/2026-08-16_h2h_cli_campaign.bash" "${PHASE1_SUITE_DIR}" "${CLI_ROOT}" "${CASCOR_SRC}"
rc=$?
((rc == 2)) && { echo "orchestrate: phase 2 hard failure -- stopping" >&2; exit 2; }
((rc == 0)) || soft_fail=1

say "PHASE 3/4 -- cap-128 service suite"
"${PY}" "${REPO_ROOT}/util/experiments/run_suite.py" --suite "${REPO_ROOT}/util/experiments/suites/p4/e-j-h2h-wide-cap128.yaml"
rc=$?
((rc == 2)) && { echo "orchestrate: phase 3 suite validation failure -- stopping" >&2; exit 2; }
((rc == 0)) || soft_fail=1

# run_suite names its dir <suite name>-<UTC stamp>; the newest match is the run just finished.
PHASE3_SUITE_DIR="$(find "${RUN_ROOT}/suites" -maxdepth 1 -name 'e-j-h2h-wide-cap128-*' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
[[ -d "${PHASE3_SUITE_DIR}/cells" ]] || { echo "orchestrate: cannot locate the cap-128 suite dir -- stopping before phase 4" >&2; exit 2; }
echo "orchestrate: cap-128 suite dir = ${PHASE3_SUITE_DIR}"

say "PHASE 4/4 -- cap-128 direct-CLI arms"
bash "${REPO_ROOT}/util/ad-hoc/2026-08-16_h2h_cli_campaign.bash" "${PHASE3_SUITE_DIR}" "${CLI_ROOT}" "${CASCOR_SRC}"
rc=$?
((rc == 2)) && { echo "orchestrate: phase 4 hard failure" >&2; exit 2; }
((rc == 0)) || soft_fail=1

say "CAMPAIGN COMPLETE (soft_fail=${soft_fail})"
echo "orchestrate: collect with --suite-dir ${PHASE1_SUITE_DIR} --suite-dir ${PHASE3_SUITE_DIR} --cli-root ${CLI_ROOT}"
exit "${soft_fail}"
