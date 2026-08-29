#!/usr/bin/env bash
# Watch for Claude Fable 5 service restoration and signal when it is servable again.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-06-14
# Status:     ad-hoc — one-off (personal availability monitor)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: Claude Fable 5 access is restored, or the monitor is no longer wanted.
# Related:    Fable 5 + Mythos 5 disabled for all users 2026-06-12 (US export-control
#             directive) — https://www.anthropic.com/news/fable-mythos-access
#
# How it works
# ------------
# The pay-as-you-go ANTHROPIC_API_KEY in this environment is unfunded (every
# POST /v1/messages returns HTTP 400 "credit balance too low"), and GET /v1/models
# still lists claude-fable-5 even while it is disabled — so neither REST probe can
# tell "Fable up" from "Fable down". The faithful probe is the local `claude` CLI,
# which uses the same OAuth credential + routing as an interactive session. While
# Fable 5 is disabled the CLI returns, for $0 / 0 tokens / ~0.2s:
#
#   {"is_error":true, "result":"Claude Fable 5 is currently unavailable. ...", ...}
#
# When service is restored the same probe returns is_error:false with result "ok".
# We classify AVAILABLE only on is_error:false (never on a transient/odd error), so
# the watcher cannot cry wolf — at worst it waits a little longer.
#
# Usage
# -----
#   watch_fable5_availability.bash --once                 # single probe, print status, exit
#   watch_fable5_availability.bash [--interval S] [--max-iters N]   # loop until available
#
# Exit codes
#   0   AVAILABLE              (loop: Fable 5 servable; --once: servable)
#   10  UNAVAILABLE            (--once only: the "currently unavailable" gate)
#   20  INCONCLUSIVE           (--once only: probe error/timeout/odd output)
#   3   MONITOR_EXPIRED        (loop only: hit --max-iters without availability)
set -uo pipefail

MODEL="${MODEL_FABLE_NAME:-claude-fable-5}"
MODE="loop"
INTERVAL="${FABLE_WATCH_INTERVAL:-300}"   # seconds between probes (default 5 min)
MAX_ITERS="${FABLE_WATCH_MAX_ITERS:-4032}" # safety cap (4032 * 300s ~= 14 days)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --once)       MODE="once"; shift ;;
    --interval)   INTERVAL="$2"; shift 2 ;;
    --max-iters)  MAX_ITERS="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 64 ;;
  esac
done

# Single probe. Prints "<STATUS>: <detail>" and returns 0/10/20.
probe_once() {
  local workdir out err ec
  workdir="$(mktemp -d "${TMPDIR:-/tmp}/fableprobe.XXXXXX")" || { echo "INCONCLUSIVE: mktemp failed"; return 20; }
  # shellcheck disable=SC2064
  trap "rm -rf '$workdir'" RETURN
  printf '{"mcpServers":{}}' > "$workdir/empty_mcp.json"
  out="$workdir/out.json"; err="$workdir/err.txt"

  # Run from a neutral dir so the repo CLAUDE.md / .mcp.json are not auto-loaded.
  ( cd "$workdir" && timeout 90 claude -p "Reply with exactly: ok" \
      --model "$MODEL" \
      --output-format json \
      --strict-mcp-config --mcp-config "$workdir/empty_mcp.json" \
      --disable-slash-commands ) > "$out" 2>"$err"
  ec=$?

  if [[ $ec -eq 124 ]]; then echo "INCONCLUSIVE: probe timed out after 90s"; return 20; fi
  if [[ ! -s "$out" ]]; then echo "INCONCLUSIVE: empty output (exit $ec): $(head -c 160 "$err" 2>/dev/null)"; return 20; fi

  python3 - "$out" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print(f"INCONCLUSIVE: json parse failed: {e}"); sys.exit(20)

is_err = d.get("is_error", None)
result = (d.get("result") or "")
mu = d.get("modelUsage") or {}
low = result.lower()

# Hard "down" signals first.
if is_err is True or "unavailable" in low:
    print(f"UNAVAILABLE: {result[:160]}"); sys.exit(10)

# Success path — but guard against a silent fallback to another model.
if is_err is False:
    served = ",".join(mu.keys())
    if mu and not any("fable" in k.lower() for k in mu):
        print(f"INCONCLUSIVE: served by other model(s): {served}"); sys.exit(20)
    print(f"AVAILABLE: result={result[:80]!r} served={served or 'n/a'}"); sys.exit(0)

print(f"INCONCLUSIVE: unclear status is_error={is_err!r} result={result[:120]!r}"); sys.exit(20)
PY
  return $?
}

if [[ "$MODE" == "once" ]]; then
  status="$(probe_once)"; rc=$?
  echo "$status"
  exit $rc
fi

# Loop mode.
echo "[$(date -u +%FT%TZ)] watch_fable5: armed (model=$MODEL interval=${INTERVAL}s max_iters=$MAX_ITERS)"
i=0
while (( i < MAX_ITERS )); do
  status="$(probe_once)"; rc=$?
  ts="$(date -u +%FT%TZ)"
  if [[ $rc -eq 0 ]]; then
    echo "[$ts] FABLE5_AVAILABLE :: $status"
    exit 0
  fi
  echo "[$ts] still down (iter $((i+1))/$MAX_ITERS) :: $status"
  i=$((i+1))
  (( i < MAX_ITERS )) && sleep "$INTERVAL"
done
echo "[$(date -u +%FT%TZ)] FABLE5_MONITOR_EXPIRED after $MAX_ITERS iterations without availability"
exit 3
