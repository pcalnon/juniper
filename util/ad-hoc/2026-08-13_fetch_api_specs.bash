#!/usr/bin/env bash
# Fetch the primary specification texts cited by the API primer into a local cache.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-13
# Status:     ad-hoc -- investigation (citation verification for the API primer)
# Retire when: notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md
#              is merged and its citations are no longer being re-verified.
# Related:    notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md
#
# Why this exists: the primer cites RFC section numbers and normative wording throughout.
# Reciting those from memory is exactly the hallucination class the primer's own validation
# stage is meant to catch, so every cited document is pulled to disk and grepped instead.
# The cache directory is a scratch workspace (intermediate artifacts only); this script --
# the reproducible part -- lives in the repo per the AGENTS.md script-placement rule.
#
# Usage:
#   util/ad-hoc/2026-08-13_fetch_api_specs.bash [CACHE_DIR]
#
# Default CACHE_DIR: ${TMPDIR:-/tmp}/juniper-api-primer-specs
set -euo pipefail

CACHE_DIR="${1:-${TMPDIR:-/tmp}/juniper-api-primer-specs}"
mkdir -p "$CACHE_DIR"

# RFC number -> short slug used for the cached filename. The slug is only a human aid;
# the RFC number is the identity.
RFCS=(
  "9110:http-semantics"
  "9111:http-caching"
  "9112:http1.1"
  "9113:http2"
  "9114:http3"
  "9457:problem-details"
  "6455:websocket"
  "5789:patch"
  "6585:additional-status-codes"
  "8288:web-linking"
  "8594:sunset-header"
  "9745:deprecation-header"
  "6749:oauth2"
  "6750:oauth2-bearer"
  "7519:jwt"
  "9068:jwt-access-tokens"
  "7636:pkce"
  "8414:oauth-metadata"
  "9700:oauth-security-bcp"
  "9421:http-message-signatures"
  "8259:json"
  "9205:building-protocols-with-http"
  "8615:well-known-uris"
  "7807:problem-details-obsolete"
  "9651:structured-field-values"
  # Added after drafting: the patch-format and caching-extension documents the primer cites.
  # RFC 7396 obsoletes RFC 7386, which is the number most often cited by mistake -- both are
  # fetched so the relationship can be checked rather than asserted.
  "6902:json-patch"
  "7396:json-merge-patch"
  "7386:json-merge-patch-obsolete"
  "5861:stale-content-cache-control"
  "6266:content-disposition"
  "6839:media-type-suffixes"
)

fetch_one() {
  local num="$1" slug="$2" dest="$3"
  # rfc-editor.org serves the canonical plain-text rendering; --fail turns a 404 into a
  # nonzero exit so a wrong RFC number is loud rather than a silently empty cache file.
  if curl -sS --fail --max-time 30 -o "$dest" "https://www.rfc-editor.org/rfc/rfc${num}.txt"; then
    printf 'OK      rfc%-5s %-32s %s bytes\n' "$num" "$slug" "$(wc -c <"$dest" | tr -d ' ')"
  else
    printf 'FAILED  rfc%-5s %-32s (removed)\n' "$num" "$slug"
    rm -f "$dest"
    return 1
  fi
}

failures=0
for entry in "${RFCS[@]}"; do
  num="${entry%%:*}"
  slug="${entry##*:}"
  dest="${CACHE_DIR}/rfc${num}-${slug}.txt"
  if [[ -s "$dest" ]]; then
    printf 'CACHED  rfc%-5s %-32s %s bytes\n' "$num" "$slug" "$(wc -c <"$dest" | tr -d ' ')"
    continue
  fi
  fetch_one "$num" "$slug" "$dest" || failures=$((failures + 1))
done

printf '\nCache: %s\n' "$CACHE_DIR"
if ((failures > 0)); then
  printf 'WARNING: %d document(s) could not be fetched -- do not cite them from memory.\n' "$failures"
  exit 1
fi
printf 'All %d documents present.\n' "${#RFCS[@]}"
