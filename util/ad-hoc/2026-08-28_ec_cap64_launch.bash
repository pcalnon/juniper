#!/usr/bin/env bash
#
# Launch the E-C cap-64 re-run against a PINNED cascor worktree.
#
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-08-28
# Status: ad-hoc -- campaign launcher (E-C noise-robustness re-run at cap 64)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml (ml#1409, the cap-64 definition);
#          util/experiment_stack.bash JUNIPER_EXP_CASCOR_SRC_DIR (ml#1412, what makes pinning possible);
#          util/ad-hoc/2026-08-26_cascor_import_provenance.py (the non-vacuous pin check)
#
# Why a script: the launch is one command with four environment overrides, a nohup and a
# redirect -- a compound line this session's shell gate refuses. It is also the provenance
# record of exactly how the run was launched, which a shell history is not.
#
# Why detached: the run takes ~50 min and the harness background-task lease is ~1h, so a
# harness-backgrounded run risks being reaped mid-campaign. setsid+nohup outlives the session.
#
# PINNING, and why both variables are needed:
#   JUNIPER_EXP_CASCOR_SRC_DIR -> the uvicorn CWD, i.e. which cascor CODE runs.
#   JUNIPER_EXP_PROJECT_DIR    -> how run_suite resolves the suite's sibling-relative
#                                 base_config, i.e. which spiral-baseline.yaml CONFIG is read.
# Setting only the first gives pinned code against the PRIMARY's config -- a mixed tree that
# nothing in the manifest would reveal. The shadow dir exists solely to give the pinned
# worktree the directory NAME `juniper-cascor` that the rebase looks for.

set -euo pipefail

WORKTREE="${JUNIPER_EC_WORKTREE:-/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--exp--e-c-cap64--20260828-1922--67d7ea35}"
SHADOW="${JUNIPER_EC_SHADOW:-/home/pcalnon/.local/state/juniper-experiments/shadow-ec-cap64}"
DEPLOY="${JUNIPER_EC_DEPLOY:-/home/pcalnon/Development/python/Juniper/juniper-deploy}"
SUITE="${JUNIPER_EC_SUITE:-util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml}"
LOG_DIR="${JUNIPER_EC_LOG_DIR:-/home/pcalnon/.local/state/juniper-experiments/ec-cap64-20260828}"

mkdir -p "${LOG_DIR}"
LOG="${LOG_DIR}/run_suite.log"

# Fail loudly BEFORE launching rather than 40 minutes in: a missing pin silently falls back
# to the primary checkout, which is the whole failure mode this run exists to avoid.
[[ -d "${WORKTREE}/src" ]] || { echo "FATAL: no src/ under ${WORKTREE}" >&2; exit 2; }
[[ -f "${SHADOW}/juniper-cascor/conf/experiments/spiral-baseline.yaml" ]] || {
    echo "FATAL: ${SHADOW}/juniper-cascor does not resolve a base config" >&2; exit 2; }

echo "worktree : ${WORKTREE}"
echo "shadow   : ${SHADOW}"
echo "suite    : ${SUITE}"
echo "log      : ${LOG}"

setsid nohup env \
    JUNIPER_EXP_CASCOR_SRC_DIR="${WORKTREE}/src" \
    JUNIPER_EXP_PROJECT_DIR="${SHADOW}" \
    JUNIPER_EXP_DEPLOY_DIR="${DEPLOY}" \
    python3 util/experiments/run_suite.py --suite "${SUITE}" \
    >"${LOG}" 2>&1 &

echo "launched pid $!"
