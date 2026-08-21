#!/usr/bin/env bash
# Produce the whole determinism evidence set from a finished campaign, in one call.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-20
# Status:      ad-hoc -- one-off (juniper-cascor#532 seeded-run reproducibility)
# Retire when: #532 is root-caused or accepted and the evidence note is merged; delete then.
# Related:     2026-08-20_determinism_campaign.bash (produces what this reads).
#
# The rate, the localisation and the contention record are three separate tools, and a written-up
# result that quotes them has to quote the SAME run set to all three. Doing that by hand across
# forty run directories is where a quietly-dropped arm comes from. This runs all three over one
# resolved run set and writes every output next to the campaign, so the note cites files rather
# than remembered terminal output.
#
# Usage: util/ad-hoc/2026-08-20_determinism_report.bash <SUITE_REGISTRY_JSONL> [OUT_ROOT]
set -uo pipefail

REGISTRY="${1:?usage: $0 <SUITE_REGISTRY_JSONL> [OUT_ROOT]}"
OUT_ROOT="${2:-${HOME}/.local/state/juniper-experiments/determinism-n20}"
REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
REPORT_DIR="${OUT_ROOT}/report"

[[ -f "${REGISTRY}" ]] || { echo "report: registry not found: ${REGISTRY}" >&2; exit 2; }
mkdir -p "${REPORT_DIR}" || exit 2

mapfile -t CLI_DIRS < <(find "${OUT_ROOT}" -maxdepth 1 -type d -name 'cli-*' | sort)
if ((${#CLI_DIRS[@]} == 0)); then
    echo "report: no cli-* run dirs under ${OUT_ROOT}; reporting the service arm only" >&2
fi

echo "report: service registry = ${REGISTRY}"
echo "report: CLI runs found    = ${#CLI_DIRS[@]}"

# 1. the RATE, both arms, both fingerprints
if ((${#CLI_DIRS[@]} > 0)); then
    python3 "${REPO_ROOT}/util/ad-hoc/2026-08-20_determinism_nrun.py" \
        --suite-arm service "${REGISTRY}" \
        --arm cli "${CLI_DIRS[@]}" \
        --json "${REPORT_DIR}/rate.json" | tee "${REPORT_DIR}/rate.txt"
else
    python3 "${REPO_ROOT}/util/ad-hoc/2026-08-20_determinism_nrun.py" \
        --suite-arm service "${REGISTRY}" \
        --json "${REPORT_DIR}/rate.json" | tee "${REPORT_DIR}/rate.txt"
fi

# 2. WHERE it diverges. Run per arm: a cross-arm pair is a different comparison (the two entry
#    points need not agree with each other even when each is internally deterministic), and
#    pooling them would report cross-arm differences as if they were reproducibility failures.
mapfile -t SVC_DIRS < <(python3 -c "
import json, sys
for line in open(sys.argv[1]):
    row = json.loads(line)
    if row.get('run_dir'):
        print(row['run_dir'])
" "${REGISTRY}")

python3 "${REPO_ROOT}/util/ad-hoc/2026-08-20_determinism_localize.py" "${SVC_DIRS[@]}" \
    >"${REPORT_DIR}/localize_service.txt" 2>&1
echo "report: wrote ${REPORT_DIR}/localize_service.txt"
if ((${#CLI_DIRS[@]} > 1)); then
    python3 "${REPO_ROOT}/util/ad-hoc/2026-08-20_determinism_localize.py" "${CLI_DIRS[@]}" \
        >"${REPORT_DIR}/localize_cli.txt" 2>&1
    echo "report: wrote ${REPORT_DIR}/localize_cli.txt"
fi

# 3. the contention record -- the reason the timing columns above are not a noise floor
if [[ -f "${OUT_ROOT}/load.jsonl" ]]; then
    python3 -c "
import json, statistics, sys
vals = [json.loads(l)['load1'] for l in open(sys.argv[1]) if l.strip()]
if vals:
    print(f'host load1 over the campaign: n={len(vals)} min={min(vals):.2f} '
          f'median={statistics.median(vals):.2f} mean={statistics.mean(vals):.2f} max={max(vals):.2f}')
" "${OUT_ROOT}/load.jsonl" | tee "${REPORT_DIR}/load_summary.txt"
fi

echo "report: done -> ${REPORT_DIR}"
