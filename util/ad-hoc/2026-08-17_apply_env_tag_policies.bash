#!/usr/bin/env bash
# Apply release-tag-only deployment ref policies to a publish environment.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-17
# Status:      ad-hoc — migration
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: all publish environments carry the policy set and a drift gate enforces it.
# Related:     notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md §6 Option A / §7 P1
#              Owner decisions D2 (patterns) + D3 (tag-only, main NOT allowed), 2026-08-17.
#
# Applies ONLY tag policies -- deliberately no branch policy, so a workflow_dispatch from a branch
# (including main) is refused at the environment gate before any OIDC credential is minted. That
# refusal IS the control; do not add a `main` branch policy to "make dispatch work".
#
# Idempotent: GitHub returns 303 for an already-present pattern, which this treats as success.
# Dry-run by default; pass --apply to write.
#
# Usage: util/ad-hoc/2026-08-17_apply_env_tag_policies.bash [--apply] <repo> <env> [<repo> <env> ...]
set -uo pipefail

PATTERNS=(
  'v*' 'juniper-*-v*'
  'rc*' 'juniper-*-rc*'
  'hf*' 'juniper-*-hf*'
)

APPLY=0
if [ "${1:-}" = "--apply" ]; then APPLY=1; shift; fi

if [ "$#" -lt 2 ] || [ $(( $# % 2 )) -ne 0 ]; then
  echo "usage: $0 [--apply] <repo> <env> [<repo> <env> ...]" >&2
  exit 2
fi

while [ "$#" -ge 2 ]; do
  repo="$1"; env="$2"; shift 2
  echo "=== ${repo} / ${env} ==="

  if [ "${APPLY}" -eq 0 ]; then
    echo "  DRY-RUN: would set custom_branch_policies=true and add ${#PATTERNS[@]} tag patterns"
    printf '    tag: %s\n' "${PATTERNS[@]}"
    continue
  fi

  # Preserve existing protection rules: PATCH-like PUT carrying only the ref-policy field.
  # (Reviewers / wait timers live in protection_rules and are untouched by this payload.)
  if ! echo '{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}' \
      | gh api -X PUT "repos/pcalnon/${repo}/environments/${env}" --input - --jq '.name' >/dev/null; then
    echo "  ERROR: could not enable custom ref policies" >&2
    continue
  fi

  for p in "${PATTERNS[@]}"; do
    out=$(gh api -X POST "repos/pcalnon/${repo}/environments/${env}/deployment-branch-policies" \
            -f name="${p}" -f type=tag 2>&1)
    if printf '%s' "${out}" | grep -q '"id"'; then
      echo "  added   tag ${p}"
    elif printf '%s' "${out}" | grep -qiE '303|already exists'; then
      echo "  present tag ${p}"
    else
      echo "  FAILED  tag ${p}: $(printf '%s' "${out}" | head -1)" >&2
    fi
  done

  echo "  --- resulting policy set ---"
  gh api "repos/pcalnon/${repo}/environments/${env}/deployment-branch-policies" \
    --jq '.branch_policies[]? | "    \(.type // "branch")\t\(.name)"'
done
