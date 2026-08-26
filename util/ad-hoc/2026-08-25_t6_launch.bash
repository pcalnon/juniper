#!/usr/bin/env bash
# T6 re-baseline: atomic precondition re-check + DETACHED campaign launch.
# Any gate failure aborts WITHOUT launching; on success the campaign runs under
# setsid/nohup so it survives the launching session (a harness background task
# would die with a [bg] worker lease -- safe-merge-kill-forensics SS3.4).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-25
# Status:     ad-hoc -- one-off (T6 re-baseline launch coordination)
# Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline)
# Related:    HANDOFF_2026-08-25_t6-rebaseline-window-held-not-launched.md;
#             util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash
#
# The campaign script itself re-verifies cascor cleanliness and pins/ledgers
# the SHA around every suite; these gates only decide whether NOW is a sane
# moment to start. Gate values mirror the watch script's quiet-host bar
# (2026-08-25_t6_watch_host_drained.bash), slightly looser so the launcher's
# own probes and the watch's decay window cannot cause a spurious abort.
#
# set -e deliberately omitted: every failure path is an explicit gated abort
# with a printed reason, which -e would preempt silently.
set -uo pipefail

ML_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

for p in 8230 8110 8202 8101 8051; do
  n=$(ss -tlnH "sport = :${p}" 2>/dev/null | wc -l)
  if [ "${n}" -gt 0 ]; then echo "ABORT: port ${p} occupied"; exit 1; fi
done

gpu=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
case "${gpu}" in ''|*[!0-9]*) echo "ABORT: gpu query failed: ${gpu}"; exit 1 ;; esac
if [ "${gpu}" -ge 1200 ]; then echo "ABORT: gpu ${gpu} MiB >= 1200"; exit 1; fi

load1=$(cut -d' ' -f1 /proc/loadavg)
load15=$(cut -d' ' -f3 /proc/loadavg)
lok=$(awk -v a="${load1}" -v b="${load15}" 'BEGIN{print (a<6.0 && b<5.0)?1:0}')
if [ "${lok}" -ne 1 ]; then echo "ABORT: load1=${load1} load15=${load15} (need <6 / <5)"; exit 1; fi
# Instantaneous CPU (second snapshot of a 1 s wide-column `top` sample) -- NOT `ps pcpu`,
# which is a lifetime average and read 45% for an idle duplicati-server on 2026-08-25.
# Mirrors the watch script's gate; see the comment there.
hot=$(top -b -n 2 -d 1 -w 512 2>/dev/null | awk '/^top -/{n++} n==2 && $NF ~ /clamscan|clamdscan|duplicati|aescrypt/ && $9+0 > 20 {c++} END{print c+0}')
if [ "${hot}" -ne 0 ]; then echo "ABORT: ${hot} hot maintenance process(es) (clamscan/duplicati >20% CPU)"; exit 1; fi

# shellcheck disable=SC1091  # conda's hook is outside the repo by design
source /opt/miniforge3/etc/profile.d/conda.sh
conda activate JuniperCascor1
pyv=$(python3 --version 2>&1)
case "${pyv}" in
  *3.13.13*) : ;;
  *) echo "ABORT: wrong interpreter for driver provenance: ${pyv} (want JuniperCascor1 3.13.13)"; exit 1 ;;
esac

cd "${ML_DIR}" || { echo "ABORT: cd ${ML_DIR} failed"; exit 1; }
OUT="${HOME}/.local/state/juniper-experiments/t6-campaign-$(date -u +%Y%m%dT%H%M%SZ).out"
setsid nohup bash "${ML_DIR}/util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash" > "${OUT}" 2>&1 < /dev/null &
cpid=$!
echo "LAUNCHED pid=${cpid} out=${OUT} ml_dir=${ML_DIR} load1=${load1} load15=${load15} gpu=${gpu}MiB py=${pyv}"
