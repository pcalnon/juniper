#!/usr/bin/env bash
# Tally per-rule ruleset evaluation results across a repo's retained rule-suite window.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-17
# Status:      ad-hoc — investigation
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the question "which ruleset rule actually blocks merges here?" stops recurring.
# Related:     notes/JUNIPER_2026-08-17_JUNIPER-ML_HELD-PLANNING-ITEMS-REGISTER.md §1.2
#
# Read-only: issues GET requests only.
#
# Why it exists: a rule can be *configured* and still never bite. The 2026-08-15 ruleset register
# asserted the tool-less `code_quality` rule was deadlocking non-bypass auto-merges; this tally
# showed code_quality passing 13/13 while required_status_checks / code_scanning / pull_request
# were the rules actually failing. Configuration is not behaviour -- measure before attributing.
#
# Usage: util/ad-hoc/2026-08-17_rule_suite_tally.bash [repo] [pages] [sample]
set -uo pipefail

REPO="${1:-juniper-ml}"
PAGES="${2:-1}"
SAMPLE="${3:-40}"

tmp=$(mktemp)
trap 'rm -f "${tmp}"' EXIT

for p in $(seq 1 "${PAGES}"); do
  gh api "repos/pcalnon/${REPO}/rulesets/rule-suites?per_page=100&page=${p}" \
    --jq '.[] | "\(.id)\t\(.result)\t\(.actor_name)"' 2>/dev/null >>"${tmp}"
done

total=$(wc -l <"${tmp}" | tr -d ' ')
echo "repo=${REPO}  suites=${total}"

if [ "${total}" -eq 0 ]; then
  echo "(no rule suites retained -- nothing to tally)"
  exit 0
fi

echo "--- overall suite result ---"
cut -f2 "${tmp}" | sort | uniq -c | sort -rn

echo "--- per-rule result (sampling up to ${SAMPLE} suites) ---"
head -"${SAMPLE}" "${tmp}" | cut -f1 | while read -r id; do
  gh api "repos/pcalnon/${REPO}/rulesets/rule-suites/${id}" \
    --jq '.rule_evaluations[]? | "\(.rule_type)\t\(.result)"' 2>/dev/null
done | sort | uniq -c | sort -k2,2 -k3,3
