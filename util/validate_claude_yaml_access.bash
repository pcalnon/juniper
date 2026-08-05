#!/usr/bin/env bash
###########################################################################################################################################################################################################
# validate_claude_yaml_access.bash — Audit .github/workflows/claude.yml for safe public-repo deployment
#
# Verifies the three structural safeguards documented in
# notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md:
#
#   L2  Trigger-surface audit:    no `pull_request_target:` / `workflow_run:`
#   L3a If-guard presence:        the `claude:` job declares an `if:`
#   L3b If-guard contains '@claude' literal
#
# Usage:
#   validate_claude_yaml_access.bash [<file-or-dir> ...]
#
# Behavior with no arguments:
#   - If JUNIPER_ROOT is set and contains the canonical 8 Juniper sibling
#     repos, validate each repo's .github/workflows/claude.yml that exists.
#   - Otherwise, validate the current git repo's
#     .github/workflows/claude.yml relative to the script location.
#
# Behavior with arguments:
#   - For each argument, resolve to a claude.yml path:
#     - file: validate it directly.
#     - dir:  validate <dir>/.github/workflows/claude.yml if present.
#
# Exit codes:
#   0 — every claude.yml validated cleanly (or none found, with a warning)
#   1 — at least one finding
#   2 — usage / I/O error
#
# Environment overrides:
#   JUNIPER_ROOT  — root that contains all juniper-* sibling checkouts (optional)
#   VERBOSE       — set to 1 for per-check trace output
#
# License:  MIT License
# Copyright: Copyright (c) 2024-2026 Paul Calnon
###########################################################################################################################################################################################################

set -euo pipefail

VERBOSE="${VERBOSE:-0}"

DEFAULT_REPOS=(
  juniper-cascor
  juniper-data
  juniper-data-client
  juniper-cascor-client
  juniper-cascor-worker
  juniper-ml
  juniper-canopy
  juniper-deploy
)

print_header() {
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║       claude.yml Public-Repo Access Validation             ║"
  echo "╚════════════════════════════════════════════════════════════╝"
}

# Resolve a positional argument into a claude.yml path. Echoes the path
# (or empty string if no claude.yml lives at the resolved location).
# Exits 2 on a non-existent input.
resolve_target() {
  local arg="$1"
  if [ ! -e "$arg" ]; then
    echo "::error::input does not exist: $arg" >&2
    exit 2
  fi
  if [ -d "$arg" ]; then
    local candidate="$arg/.github/workflows/claude.yml"
    if [ -f "$candidate" ]; then
      echo "$candidate"
    else
      echo ""
    fi
  else
    echo "$arg"
  fi
}

# Collect default targets when no positional args given.
default_targets() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local repo_root
  repo_root="$(cd "$script_dir/.." && pwd)"

  if [ -n "${JUNIPER_ROOT:-}" ] && [ -d "$JUNIPER_ROOT" ]; then
    local found=0
    for repo in "${DEFAULT_REPOS[@]}"; do
      local f="$JUNIPER_ROOT/$repo/.github/workflows/claude.yml"
      if [ -f "$f" ]; then
        echo "$f"
        found=1
      fi
    done
    if [ "$found" -eq 0 ]; then
      echo "::warning::JUNIPER_ROOT=$JUNIPER_ROOT contains no claude.yml under the canonical Juniper repos" >&2
    fi
    return
  fi

  local local_yml="$repo_root/.github/workflows/claude.yml"
  if [ -f "$local_yml" ]; then
    echo "$local_yml"
  fi
}

# Returns 0 if file passes all checks, 1 otherwise. Emits ::error:: lines on findings.
audit_one() {
  local f="$1"
  local label="$2"
  local exit_code=0

  if [ "$VERBOSE" = "1" ]; then echo "→ $label  ($f)"; fi

  # L2: dangerous triggers
  if grep -qE '^[[:space:]]*(pull_request_target|workflow_run):' "$f"; then
    echo "::error file=$f::L2 dangerous trigger present (pull_request_target or workflow_run); fork PRs would inherit secrets"
    grep -nE '^[[:space:]]*(pull_request_target|workflow_run):' "$f" | sed 's/^/    /' >&2
    exit_code=1
  fi

  # L3a: claude job declares an if-guard.
  # Walk from the `claude:` job marker until `runs-on:` (start of the steps),
  # tracking whether an `if:` clause appeared at the job level.
  local has_if
  has_if=$(awk '
    /^[[:space:]]*claude:[[:space:]]*$/ {flag=1; next}
    flag && /^[[:space:]]*runs-on:/ {exit}
    flag && /^[[:space:]]*if:/ {found=1}
    END {print found?"yes":"no"}
  ' "$f")
  if [ "$has_if" != "yes" ]; then
    echo "::error file=$f::L3a claude job has no if-guard; every event would trigger the action"
    exit_code=1
  fi

  # L3b: if-guard contains the literal '@claude'
  if ! grep -qE "contains\([^)]*'@claude'\)" "$f"; then
    echo "::error file=$f::L3b if-guard does not reference '@claude' literal; drive-by events could trigger the action"
    exit_code=1
  fi

  if [ "$exit_code" -eq 0 ]; then
    printf 'OK     %s\n' "$label"
  else
    printf 'FAIL   %s\n' "$label"
  fi
  return "$exit_code"
}

main() {
  print_header

  local targets=()
  if [ "$#" -gt 0 ]; then
    for arg in "$@"; do
      local t
      t="$(resolve_target "$arg")"
      if [ -z "$t" ]; then
        echo "::warning::no claude.yml under $arg — skipping" >&2
        continue
      fi
      targets+=("$t")
    done
  else
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      targets+=("$line")
    done < <(default_targets)
  fi

  if [ "${#targets[@]}" -eq 0 ]; then
    echo "::warning::no claude.yml files to validate (nothing to do)"
    exit 0
  fi

  local total_failures=0
  for f in "${targets[@]}"; do
    # Render a friendly label: <repo-or-name>/.github/workflows/claude.yml
    local label
    label="$(realpath --relative-to="$(pwd)" "$f" 2>/dev/null || echo "$f")"
    if ! audit_one "$f" "$label"; then
      total_failures=$((total_failures + 1))
    fi
  done

  echo ""
  if [ "$total_failures" -gt 0 ]; then
    echo "::error::$total_failures claude.yml file(s) failed validation"
    exit 1
  fi
  echo "::notice::all claude.yml files passed L2/L3 validation"
}

main "$@"
