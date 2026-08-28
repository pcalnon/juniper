#!/usr/bin/env bash
# Census of remote branches per Juniper repo, and how many are already merged
# into the default branch (i.e. deletable debt that delete_branch_on_merge
# would have prevented).
#
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: defect-register round-28 / delete_branch_on_merge evaluation
# Author:      Paul Calnon
# License:     MIT License
set -uo pipefail

for repo in juniper-ml juniper-data juniper-cascor juniper-canopy \
            juniper-data-client juniper-cascor-client juniper-cascor-worker \
            juniper-recurrence juniper-deploy; do
    total=$(gh api "repos/pcalnon/${repo}/branches?per_page=100" --jq 'length' 2>/dev/null)
    dbom=$(gh api "repos/pcalnon/${repo}" --jq '.delete_branch_on_merge' 2>/dev/null)
    printf '%-22s branches=%-4s delete_on_merge=%s\n' "$repo" "${total:-ERR}" "${dbom:-ERR}"
done
