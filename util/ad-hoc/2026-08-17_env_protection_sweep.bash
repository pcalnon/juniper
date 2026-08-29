#!/usr/bin/env bash
# Sweep GitHub deployment environments + protection rules + ref policies across the Juniper fleet.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-17
# Status:      ad-hoc — investigation
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: environment ref policies are applied fleet-wide and a permanent drift gate covers them
#              (see the publish-path design doc §7 P1 / §8), or the check moves into juniper-ci-tools.
# Related:     notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md §2.1 / §8
#
# Read-only: issues GET requests only. Never edits an environment, policy, or ruleset.
#
# Usage: util/ad-hoc/2026-08-17_env_protection_sweep.bash [repo ...]
#   refs=ANY-REF marks an environment with deployment_branch_policy: null -- any branch or tag may
#   deploy to it. That is the finding this script exists to surface.
set -uo pipefail

REPOS=("$@")
if [ "${#REPOS[@]}" -eq 0 ]; then
  REPOS=(
    juniper-ml juniper-cascor juniper-data juniper-data-client
    juniper-cascor-client juniper-cascor-worker juniper-canopy
    juniper-recurrence juniper-deploy
  )
fi

for r in "${REPOS[@]}"; do
  envs=$(gh api "repos/pcalnon/${r}/environments" --jq '.environments[].name' 2>/dev/null)
  if [ -z "${envs}" ]; then
    printf '%-24s (no environments)\n' "${r}"
    continue
  fi
  for e in ${envs}; do
    json=$(gh api "repos/pcalnon/${r}/environments/${e}" 2>/dev/null) || continue
    rules=$(printf '%s' "${json}" | jq -r '
      [.protection_rules[]?
        | if   .type == "required_reviewers" then "reviewers(\([.reviewers[]?.reviewer.login] | join(",")))"
          elif .type == "wait_timer"         then "wait(\(.wait_timer)m)"
          else .type end
      ] | join("+")')
    pol=$(printf '%s' "${json}" | jq -r '
      if .deployment_branch_policy == null then "ANY-REF"
      else "protected=\(.deployment_branch_policy.protected_branches) custom=\(.deployment_branch_policy.custom_branch_policies)"
      end')
    printf '%-24s %-12s rules=%-34s refs=%s\n' "${r}" "${e}" "${rules:--}" "${pol}"

    if printf '%s' "${json}" | jq -e '.deployment_branch_policy.custom_branch_policies == true' >/dev/null 2>&1; then
      gh api "repos/pcalnon/${r}/environments/${e}/deployment-branch-policies" \
        --jq '.branch_policies[]? | "        policy: \(.type // "branch") \(.name)"' 2>/dev/null
    fi
  done
done
