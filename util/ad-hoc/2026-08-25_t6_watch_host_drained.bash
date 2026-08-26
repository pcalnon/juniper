#!/usr/bin/env bash
# T6 re-baseline: sustained host-drain watch. Emits ONE line and exits when the
# host is TRULY quiet, so a Monitor wrapping it wakes the session exactly once.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-25
# Status:     ad-hoc -- one-off (T6 re-baseline launch coordination)
# Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline)
# Related:    HANDOFF_2026-08-25_t6-rebaseline-window-held-not-launched.md;
#             HANDOFF_2026-08-24_t6-rebaseline-campaign.md SS2.1
#
# v3 lesson (2026-08-25): v2 gated on load1 alone and fired during a 2-minute
# lull while clamscan and a duplicati backup both ran at 80%+ CPU -- the exact
# attempt-1 trap (judging the 1-minute number). Conditions here:
#   - experiment + E2E-trio ports all clear (ONE port per ss call -- a
#     multi-port ss filter returns empty with exit 0)
#   - load1 < 4 AND load15 < 4.5 (load15 forces ~15 min of genuine quiet;
#     observed daytime floor on this host is ~5, so this bar is effectively
#     an overnight / early-morning window)
#   - no clamscan / clamdscan / duplicati-family / aescrypt process above 20%
#     CPU (aescrypt: the backup's encryption helper can run hot while its
#     parent duplicati-serve idles below the gate)
#   - GPU < 1200 MiB (~950 MiB of display memory is the idle floor with zero
#     compute apps; the bar's intent is "no compute residue")
#   - 2 consecutive 60 s passes
#
# set -e deliberately omitted: `[ cond ] && x=1` AND-lists are load-bearing
# and -e would abort on their intended false branches.
set -uo pipefail
streak=0
while true; do
  ok=1
  for p in 8230 8110 8202 8101 8051; do
    n=$(ss -tlnH "sport = :${p}" 2>/dev/null | wc -l)
    [ "${n}" -gt 0 ] && ok=0
  done
  load1=$(cut -d' ' -f1 /proc/loadavg)
  load15=$(cut -d' ' -f3 /proc/loadavg)
  lok=$(awk -v a="${load1}" -v b="${load15}" 'BEGIN{print (a<4.0 && b<4.5)?1:0}')
  [ "${lok}" -eq 1 ] || ok=0
  # Instantaneous CPU: the SECOND snapshot of a 1 s `top` sample, wide columns so the
  # COMMAND field carries the full comm name ("duplicati-serve", not "duplica+", which
  # the regex would miss). `ps pcpu` is a LIFETIME average: on 2026-08-25 an idle
  # duplicati-server that had run a backup for hours still read 45% (live 0.0%) and
  # held this gate shut for the rest of the day.
  hot=$(top -b -n 2 -d 1 -w 512 2>/dev/null | awk '/^top -/{n++} n==2 && $NF ~ /clamscan|clamdscan|duplicati|aescrypt/ && $9+0 > 20 {c++} END{print c+0}')
  [ "${hot}" -eq 0 ] || ok=0
  gpu=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
  case "${gpu}" in
    ''|*[!0-9]*) ok=0 ;;
    *) [ "${gpu}" -lt 1200 ] || ok=0 ;;
  esac
  if [ "${ok}" -eq 1 ]; then
    streak=$((streak+1))
  else
    streak=0
  fi
  if [ "${streak}" -ge 2 ]; then
    echo "HOST TRULY DRAINED (2x60s): load1=${load1} load15=${load15} gpu=${gpu}MiB no-hot-maintenance -- rerun T6 pre-flight and claim the window"
    exit 0
  fi
  sleep 60
done
