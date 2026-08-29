#!/usr/bin/env bash
# T6 re-baseline: run E-A, E-I and E-C against ONE post-cascor#514 code state.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-23
# Status:     ad-hoc -- one-off (T6 re-baseline campaign)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the re-baselined E-A/E-I/E-C grids are published and the evidence doc's
#              KNOWINGLY STALE marker is lifted.
# Related:    T6 of HANDOFF_2026-08-18_cli-experimentation-unowned-tasks.md; R-5 §5.1
#
# WHY A DRIVER RATHER THAN THREE COMMANDS
#
# The whole point of this campaign is that the three grids become comparable to each other.
# R-5 §5.1 established that spiral figures are NOT comparable across cascor#514, so a
# re-baseline that straddles another cascor change just relocates the problem: E-A on one
# commit and E-C on another is exactly the incomparability being fixed.
#
# The cascor primary checkout is shared, other sessions merge into it, and this run takes
# hours. So the SHA is captured before and after EVERY suite and the run is aborted the
# moment it moves. Detecting it afterwards is not good enough -- by then the GPU hours are
# already spent on a split baseline.
#
# Pinning the checkout instead was considered and rejected: juniper-cascor is installed
# EDITABLE into JuniperCascor1, so pointing the launcher at a pinned worktree would mix a
# pinned cwd with primary-checkout imports and produce a baseline nobody could describe.
#
# JUNIPER_EXP_PROJECT_DIR is mandatory here: experiment_stack.bash derives PROJECT_DIR from
# its own location, which resolves to `.../.claude/worktrees` when this repo is checked out
# as a worktree, and CASCOR_SRC_DIR would then point at a directory that does not exist.

set -euo pipefail

PROJECT_DIR="/home/pcalnon/Development/python/Juniper"
export JUNIPER_EXP_PROJECT_DIR="${PROJECT_DIR}"

ML_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CASCOR_DIR="${PROJECT_DIR}/juniper-cascor"
STATE_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
CAMPAIGN_DIR="${STATE_ROOT}/t6-rebaseline-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${CAMPAIGN_DIR}"
LEDGER="${CAMPAIGN_DIR}/campaign.jsonl"

# E-A first: its cheapest cell (cap 4 / pool 4) ran 215 s, so a broken pipeline surfaces in
# minutes rather than after the first hour-long cell of a wider grid.
SUITES=(
  "p4/e-a-cascor-budget-sweep"
  "p4/e-i-cascor-cap-ceiling"
  "p4/e-c-cascor-noise-robustness"
)

cascor_sha() { git -C "${CASCOR_DIR}" rev-parse HEAD; }
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }

BASELINE_SHA="$(cascor_sha)"
log "campaign dir : ${CAMPAIGN_DIR}"
log "cascor pinned: ${BASELINE_SHA}"
log "project dir  : ${JUNIPER_EXP_PROJECT_DIR}"
printf '{"event":"start","cascor_sha":"%s","suites":%d}\n' "${BASELINE_SHA}" "${#SUITES[@]}" >>"${LEDGER}"

if [[ -n "$(git -C "${CASCOR_DIR}" status --porcelain)" ]]; then
  log "ABORT: ${CASCOR_DIR} has uncommitted changes -- the baseline would not be describable"
  exit 2
fi

rc_total=0
for suite in "${SUITES[@]}"; do
  before="$(cascor_sha)"
  if [[ "${before}" != "${BASELINE_SHA}" ]]; then
    log "ABORT before ${suite}: cascor moved ${BASELINE_SHA} -> ${before}"
    printf '{"event":"abort","suite":"%s","expected":"%s","found":"%s"}\n' "${suite}" "${BASELINE_SHA}" "${before}" >>"${LEDGER}"
    exit 3
  fi

  name="$(basename "${suite}")"
  suite_log="${CAMPAIGN_DIR}/${name}.log"
  log "START ${name}  (log: ${suite_log})"
  printf '{"event":"suite_start","suite":"%s","utc":"%s"}\n' "${name}" "$(date -u +%FT%TZ)" >>"${LEDGER}"

  started=$(date +%s)
  # continue_on_failure is a per-CELL setting inside each suite; a non-zero exit here means
  # some cell failed. Record it and keep going: a half-complete grid is still evidence, and
  # stopping would leave the remaining suites on a different (later) cascor state.
  set +e
  python3 "${ML_DIR}/util/experiments/run_suite.py" --suite "${ML_DIR}/util/experiments/suites/${suite}.yaml" >"${suite_log}" 2>&1
  rc=$?
  set -e
  elapsed=$(( $(date +%s) - started ))

  after="$(cascor_sha)"
  log "END   ${name}  rc=${rc}  elapsed=${elapsed}s"
  printf '{"event":"suite_end","suite":"%s","rc":%d,"elapsed_s":%d,"sha_before":"%s","sha_after":"%s"}\n' \
    "${name}" "${rc}" "${elapsed}" "${before}" "${after}" >>"${LEDGER}"

  if [[ "${after}" != "${BASELINE_SHA}" ]]; then
    log "ABORT after ${name}: cascor moved ${BASELINE_SHA} -> ${after}; later suites would not be comparable"
    printf '{"event":"abort","suite":"%s","expected":"%s","found":"%s"}\n' "${name}" "${BASELINE_SHA}" "${after}" >>"${LEDGER}"
    exit 3
  fi
  [[ ${rc} -ne 0 ]] && rc_total=1
done

log "CAMPAIGN COMPLETE  cascor=${BASELINE_SHA}  worst_rc=${rc_total}"
printf '{"event":"complete","cascor_sha":"%s","rc":%d}\n' "${BASELINE_SHA}" "${rc_total}" >>"${LEDGER}"
exit "${rc_total}"
