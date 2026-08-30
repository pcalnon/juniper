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
# CORRECTION 2026-08-30 (ml#1412 + the import-provenance probe). This block used to say:
#
#     "Pinning the checkout instead was considered and rejected: juniper-cascor is installed
#      EDITABLE into JuniperCascor1, so pointing the launcher at a pinned worktree would mix
#      a pinned cwd with primary-checkout imports and produce a baseline nobody could
#      describe."
#
# That theory is REFUTED and pinning is now the better option. The editable finder registers
# itself with `sys.meta_path.append(_EditableFinder)` -- AFTER the default PathFinder -- so
# the launcher's CWD wins and the finder is only a fallback. Measured, not assumed:
#   /opt/miniforge3/envs/JuniperCascor1/bin/python3.13 \
#       util/ad-hoc/2026-08-26_cascor_import_provenance.py <worktree>/src
# (exit 1 on a mixed tree). ml#1412 then added JUNIPER_EXP_CASCOR_SRC_DIR to
# experiment_stack.bash (:112), which is what makes a pinned launch expressible at all.
#
# So this driver now supports BOTH modes -- see PINNED MODE below. The freeze/abort logic is
# kept in both: against the shared primary it is load-bearing, and against a detached pin it
# is a cheap no-op that costs one `rev-parse` per suite.
#
# PINNED MODE -- set all THREE, or you get a silently mixed tree:
#   JUNIPER_EXP_CASCOR_SRC_DIR=<worktree>/src   which cascor CODE runs (uvicorn's CWD)
#   JUNIPER_EXP_PROJECT_DIR=<shadow dir>        which CONFIG run_suite reads for the suite's
#                                               sibling-relative base_config
#   JUNIPER_EXP_DEPLOY_DIR=<real juniper-deploy> the shadow has no juniper-deploy
# `_resolve_base_config` falls back SILENTLY when the override does not resolve, so a wrong
# or dangling PROJECT_DIR reads the PRIMARY's spiral-baseline.yaml -- pinned code, primary
# config, and nothing in the manifest reveals it. The preflight below fails loudly instead.
# Reference launcher: util/ad-hoc/2026-08-28_ec_cap64_launch.bash.
#
# UNPINNED MODE (the default, and what the original T6 campaign ran): JUNIPER_EXP_PROJECT_DIR
# defaults to the ecosystem root and cascor resolves to the shared primary checkout.
# JUNIPER_EXP_PROJECT_DIR is mandatory either way: experiment_stack.bash derives PROJECT_DIR
# from its own location, which resolves to `.../.claude/worktrees` when this repo is checked
# out as a worktree, and CASCOR_SRC_DIR would then point at a directory that does not exist.

set -euo pipefail

PROJECT_DIR="/home/pcalnon/Development/python/Juniper"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-${PROJECT_DIR}}"

ML_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Which cascor tree is this campaign about? A pin names it directly; otherwise it is whatever
# JUNIPER_EXP_PROJECT_DIR resolves to -- NOT a hard-coded primary, so that the freeze below
# watches the tree that actually runs rather than a different one that happens to share a name.
if [[ -n "${JUNIPER_EXP_CASCOR_SRC_DIR:-}" ]]; then
  # Validate BEFORE resolving: a bare `cd` on a bad pin dies with a raw shell error and
  # exit 1 under `set -e`, which reads like a script bug rather than the operator error it is.
  [[ -d "${JUNIPER_EXP_CASCOR_SRC_DIR}" ]] || {
    echo "FATAL: JUNIPER_EXP_CASCOR_SRC_DIR does not exist: ${JUNIPER_EXP_CASCOR_SRC_DIR}" >&2; exit 2; }
  CASCOR_DIR="$(cd "${JUNIPER_EXP_CASCOR_SRC_DIR}/.." && pwd)"
  PINNED=1
else
  CASCOR_DIR="${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor"
  PINNED=0
fi

# Preflight the pin BEFORE spending GPU hours. _resolve_base_config falls back silently, so a
# wrong PROJECT_DIR would otherwise surface only as an inexplicable grid hours later.
#
# The check that matters is TREE IDENTITY, not file existence. An "is there a base config
# there?" test is VACUOUS for the failure this guards: the ecosystem root has a perfectly good
# spiral-baseline.yaml -- the PRIMARY's -- so pinned-code/primary-config passes it every time.
# Compare the resolved trees instead, which is the only form that can actually fail.
if (( PINNED )); then
  [[ -n "${JUNIPER_EXP_DEPLOY_DIR:-}" ]] || {
    echo "FATAL: pinned mode also needs JUNIPER_EXP_DEPLOY_DIR -- the shadow has no juniper-deploy." >&2; exit 2; }

  CODE_TREE="$(realpath "${JUNIPER_EXP_CASCOR_SRC_DIR}/.." 2>/dev/null || true)"
  CONF_TREE="$(realpath "${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor" 2>/dev/null || true)"
  if [[ -z "${CONF_TREE}" ]]; then
    echo "FATAL: JUNIPER_EXP_PROJECT_DIR=${JUNIPER_EXP_PROJECT_DIR} has no juniper-cascor entry." >&2
    echo "       Pinned mode needs the SHADOW dir here, whose juniper-cascor symlinks to the pin." >&2
    exit 2
  fi
  if [[ "${CODE_TREE}" != "${CONF_TREE}" ]]; then
    echo "FATAL: pinned CODE and CONFIG resolve to DIFFERENT cascor trees --" >&2
    echo "         code   <- ${CODE_TREE}" >&2
    echo "         config <- ${CONF_TREE}" >&2
    echo "       That is the silent mixed tree this preflight exists to prevent. Set" >&2
    echo "       JUNIPER_EXP_PROJECT_DIR to the SHADOW dir whose juniper-cascor symlinks to" >&2
    echo "       ${CODE_TREE}, not to the ecosystem root. See PINNED MODE in this file's header." >&2
    exit 2
  fi
  log_pin_note="code and config both resolve to ${CODE_TREE}"
fi

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
if (( PINNED )); then MODE_LABEL="pinned"; else MODE_LABEL="primary"; fi
log "campaign dir : ${CAMPAIGN_DIR}"
log "mode         : ${MODE_LABEL}"
if [[ -n "${log_pin_note:-}" ]]; then log "pin check    : ${log_pin_note}"; fi
log "cascor tree  : ${CASCOR_DIR}"
log "cascor sha   : ${BASELINE_SHA}"
log "project dir  : ${JUNIPER_EXP_PROJECT_DIR}"
# The per-run manifest CANNOT record the pin -- it carries git={} and an editable_source that
# points at the PRIMARY regardless of what ran -- so the campaign ledger is where the pin is
# recorded. It is still a LABEL, not proof; the import probe named in the header is the proof.
printf '{"event":"start","cascor_sha":"%s","suites":%d,"mode":"%s","cascor_dir":"%s","project_dir":"%s"}\n' \
  "${BASELINE_SHA}" "${#SUITES[@]}" "${MODE_LABEL}" "${CASCOR_DIR}" "${JUNIPER_EXP_PROJECT_DIR}" >>"${LEDGER}"

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
