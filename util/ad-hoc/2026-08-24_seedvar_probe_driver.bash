#!/usr/bin/env bash
# Sequential bisection probes for the CLI determinism closure: #563, then #562.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-24
# Status:      ad-hoc -- one-off (juniper-cascor#532 attribution bisect)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: #532's attribution is written up in the evidence note and merged; delete then.
# Related:     util/ad-hoc/2026-08-20_determinism_arm.bash (runs one arm);
#              util/ad-hoc/2026-08-24_seedvar_analysis.py (reads what this produces);
#              util/ad-hoc/2026-08-21_cascor_seeds_and_balance_diag.patch (the instrument).
#
# WHY THIS EXISTS
# The N=20 instrumented arm at e4e5b990 (#565, direct parent of #566) read 0/190 with
# byte-identical candidate-seed lists -- the direct CLI was ALREADY deterministic before
# #566, so the closure of the pre-arc 0.768 lies in (#539, #565]. These two probes decide
# the leading hypothesis (#563, the 9x logger fix -- the only commit in the window that
# materially changes the training hot path's runtime): if #562 (its parent) diverges while
# #563 does not, the attribution is exact, with no inertness argument needed for #564/#565.
#
# STRICTLY SEQUENTIAL: both arms use the same materialised cell, and the thread probe's
# per-run teardown pkills by that cell path -- overlapping arms would kill each other
# (the §3.3 two-campaigns trap). The #562 arm runs pre-#563 logging, ~280 s/run: budget
# ~95 min for it and ~10 min for the #563 arm.
#
# Usage: DATA_URL=http://127.0.0.1:<port> util/ad-hoc/2026-08-24_seedvar_probe_driver.bash
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
WT_ROOT="/home/pcalnon/Development/python/Juniper/worktrees"
CELL="${HOME}/.local/state/juniper-experiments/suites/e-l-determinism-cap4-20260824T003754Z/cells/c000-7749f335/experiment.yaml"
STATE="${HOME}/.local/state/juniper-experiments"
: "${DATA_URL:?export DATA_URL first (stack must be up)}"

probe() {
    local tag="$1" wt="$2" sha="$3"
    local out="${STATE}/seedvar-n20-${tag}"
    mkdir -p "${out}"
    printf '{"purpose":"cascor#532 attribution bisect: run-to-run determinism of the DIRECT CLI at %s","base_sha":"%s","diag_patch":"util/ad-hoc/2026-08-21_cascor_seeds_and_balance_diag.patch","cascor_src":"%s/src","cell":"%s","data_url":"%s","n":20,"threads":"default","started_utc":"%s","host_nproc":%d,"load1_at_start":%s}\n' \
        "${tag}" "${sha}" "${wt}" "${CELL}" "${DATA_URL}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(nproc)" "$(cut -d' ' -f1 /proc/loadavg)" \
        >"${out}/provenance.json"
    echo "driver: === arm ${tag} (${sha}) start $(date -u +%H:%M:%SZ) ==="
    bash "${REPO_ROOT}/util/ad-hoc/2026-08-20_determinism_arm.bash" \
        "${wt}/src" "${CELL}" "${out}" "${tag}" 20 default
    echo "driver: === arm ${tag} done $(date -u +%H:%M:%SZ) ==="
}

probe at563 "${WT_ROOT}/juniper-cascor--diag--seed-instability-at-563--20260824-0540--6a3d1a87" "6a3d1a87 (#563)"
probe at562 "${WT_ROOT}/juniper-cascor--diag--seed-instability-at-562--20260824-0540--acf953b3" "acf953b3 (#562)"
echo "driver: ALL PROBES DONE"
