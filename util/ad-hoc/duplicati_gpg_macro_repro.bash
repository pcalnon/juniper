#!/usr/bin/env bash
#
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# Version:     0.1.0
# License:     MIT License
#
# End-to-end SCRATCH reproduction of the 2026-08-23 Duplicati GPGFlushError
# failure: a full duplicati-cli backup of the real source with the real job's
# options, against a throwaway destination/database/tempdir/passphrase, with
# three instruments the failing run lacked:
#
#   1. --log-file-log-level=Verbose        (captures Retry lines, invisible at
#                                           the default console Warning level)
#   2. a gpg wrapper that logs every invocation's start/end/rc  (discriminates
#      "gpg exited fine, pump-side frozen" from "gpg itself stalled" on a
#      GPGFlushError event)
#   3. a 5 s sampler: PSI avg10+totals, MemAvailable/SwapFree, duplicati
#      RSS/swap/threads, live gpg count/states, dest/tmp growth
#
# Run it inside a systemd transient unit to match the failing run's context
# (Nice=10, IOSchedulingClass=best-effort, IOSchedulingPriority=7), optionally
# with MemoryMax/MemoryHigh to emulate the collapsed-available-memory enabling
# condition of the 2026-08-23 episode:
#
#   systemd-run --user --unit=gpg-macro-repro --collect \
#       -p Nice=10 -p IOSchedulingClass=best-effort -p IOSchedulingPriority=7 \
#       [-p MemoryMax=6G -p MemoryHigh=5G] \
#       -p RuntimeMaxSec=18000 \
#       /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/mossy-growing-salamander/util/ad-hoc/duplicati_gpg_macro_repro.bash
#
# SAFETY: refuses to run unless the scratch filesystem is mounted with >=100 GB
# free; every write lands under a fresh run directory in _gpg_repro/; the real
# destination, the real databases, and the real credential files are never
# read or written (the passphrase is a fresh random scratch value). The real
# backup job is untouched; a concurrent REAL backup run aborts this script.

set -euo pipefail

RUN_ROOT="/media/pcalnon/temp_backups/_gpg_repro"
REAL_DEST_DIR="/media/pcalnon/temp_backups/Ubuntu"
REAL_DBPATH="/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite"
SOURCE_PATH="/home/pcalnon"
MIN_FREE_GB=100

fail() { echo "FATAL: $*" >&2; exit 1; }

# ---- guards -----------------------------------------------------------------
mountpoint -q /media/pcalnon/temp_backups \
    || fail "/media/pcalnon/temp_backups is not a mountpoint (unmounted dest trap)"

free_gb="$(df -BG --output=avail /media/pcalnon/temp_backups | tail -1 | tr -dc '0-9')"
[[ "${free_gb}" -ge "${MIN_FREE_GB}" ]] \
    || fail "only ${free_gb} GB free on scratch fs, need ${MIN_FREE_GB}"

case "${RUN_ROOT}" in
    "${REAL_DEST_DIR}"*|/mnt/Backups*) fail "RUN_ROOT overlaps a real destination" ;;
esac

# a REAL backup run (against the real dest or real db) must not be in flight
if ps -eo args | grep -E '^duplicati-cli backup' | grep -qE "temp_backups/Ubuntu|$(basename "${REAL_DBPATH}")"; then
    fail "a real duplicati-cli backup appears to be running; refusing to add repro load"
fi

RUN_DIR="${RUN_ROOT}/macro-$(date +%Y%m%d-%H%M%S)"
DEST_DIR="${RUN_DIR}/dest"
TEMP_DIR="${RUN_DIR}/tmp"
LOG_DIR="${RUN_DIR}/logs"
DBPATH="${RUN_DIR}/repro.sqlite"
mkdir -p "${DEST_DIR}" "${TEMP_DIR}" "${LOG_DIR}"

[[ -e "${DBPATH}" ]] && fail "dbpath already exists: ${DBPATH}"

# ---- scratch passphrase (never the real credentials) ------------------------
PASSPHRASE="$(openssl rand -hex 22)"
export PASSPHRASE
umask 077
printf 'PASSPHRASE=%s\n' "${PASSPHRASE}" > "${RUN_DIR}/env"
PP_SHA="$(printf '%s' "${PASSPHRASE}" | sha256sum | cut -c1-16)"

# ---- gpg wrapper: log every invocation --------------------------------------
GPG_WRAPPER="${RUN_DIR}/gpg_logged.bash"
cat > "${GPG_WRAPPER}" <<WRAP
#!/usr/bin/env bash
start=\$(date +%s.%N)
/usr/bin/gpg "\$@" &
child=\$!
trap 'kill -TERM "\$child" 2>/dev/null' TERM INT
wait "\$child"; rc=\$?
end=\$(date +%s.%N)
printf 'pid=%s gpgpid=%s start=%s end=%s rc=%s args=%s\n' \
    "\$\$" "\$child" "\$start" "\$end" "\$rc" "\$*" >> "${LOG_DIR}/gpg_invocations.log"
exit "\$rc"
WRAP
chmod +x "${GPG_WRAPPER}"

# ---- monitor ----------------------------------------------------------------
MON_CSV="${LOG_DIR}/monitor.csv"
echo "epoch,mem_avail_kb,swap_free_kb,psi_cpu_avg10,psi_io_avg10,psi_mem_avg10,psi_cpu_total,psi_io_total,psi_mem_total,dup_rss_kb,dup_swap_kb,dup_threads,gpg_count,gpg_states,dest_files,tmp_kb" > "${MON_CSV}"
monitor() {
    while :; do
        local dup_pid mem_avail swap_free rss swp thr gcount gstates dfiles tkb
        dup_pid="$(pgrep -f "duplicati-cli backup file://${DEST_DIR}" | head -1 || true)"
        mem_avail="$(awk '/MemAvailable/{print $2}' /proc/meminfo)"
        swap_free="$(awk '/SwapFree/{print $2}' /proc/meminfo)"
        read -r c_avg c_tot < <(awk 'NR==1{split($2,a,"=");split($5,b,"=");print a[2],b[2]}' /proc/pressure/cpu)
        read -r i_avg i_tot < <(awk 'NR==1{split($2,a,"=");split($5,b,"=");print a[2],b[2]}' /proc/pressure/io)
        read -r m_avg m_tot < <(awk 'NR==1{split($2,a,"=");split($5,b,"=");print a[2],b[2]}' /proc/pressure/memory)
        if [[ -n "${dup_pid}" ]] && [[ -r "/proc/${dup_pid}/status" ]]; then
            rss="$(awk '/VmRSS/{print $2}' "/proc/${dup_pid}/status")"
            swp="$(awk '/VmSwap/{print $2}' "/proc/${dup_pid}/status")"
            thr="$(awk '/Threads/{print $2}' "/proc/${dup_pid}/status")"
        else
            rss=0; swp=0; thr=0
        fi
        gcount="$(pgrep -xc gpg || true)"
        gstates="$(ps -o state= -C gpg 2>/dev/null | tr -d ' \n' || true)"
        dfiles="$(find "${DEST_DIR}" -maxdepth 1 -type f 2>/dev/null | wc -l)"
        tkb="$(du -sk "${TEMP_DIR}" 2>/dev/null | cut -f1)"
        echo "$(date +%s),${mem_avail},${swap_free},${c_avg},${i_avg},${m_avg},${c_tot},${i_tot},${m_tot},${rss},${swp},${thr},${gcount},${gstates:-none},${dfiles},${tkb}" >> "${MON_CSV}"
        sleep 5
    done
}
monitor &
MON_PID=$!
trap 'kill "${MON_PID}" 2>/dev/null || true' EXIT

# ---- record run parameters --------------------------------------------------
{
    echo "run_dir     : ${RUN_DIR}"
    echo "started     : $(date -Is)"
    echo "passphrase  : scratch, sha256[:16]=${PP_SHA} (env file: ${RUN_DIR}/env)"
    echo "dest        : file://${DEST_DIR}"
    echo "dbpath      : ${DBPATH}"
    echo "tempdir     : ${TEMP_DIR}"
    echo "gpg wrapper : ${GPG_WRAPPER}"
    echo "cgroup      : $(cat /proc/self/cgroup 2>/dev/null)"
    echo "unit memory : MemoryMax=$(cat "/sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup)/memory.max" 2>/dev/null || echo '?')"
    echo "nice(self)  : $(awk '{print $19}' /proc/self/stat 2>/dev/null || nice)"
} | tee "${LOG_DIR}/run_params.txt"

# ---- the backup (options cloned from util/duplicati_scheduled_backup.bash) --
set +e
duplicati-cli backup "file://${DEST_DIR}" "${SOURCE_PATH}" \
    --dbpath="${DBPATH}" \
    --tempdir="${TEMP_DIR}" \
    --encryption-module=gpg \
    --gpg-program-path="${GPG_WRAPPER}" \
    --compression-module=zip \
    --blocksize=1MB \
    --dblock-size=500MB \
    --skip-files-larger-than=2GB \
    --no-auto-compact=true \
    --allow-missing-source=true \
    --log-file="${LOG_DIR}/duplicati.log" \
    --log-file-log-level=Verbose \
    "--exclude=/home/pcalnon/Development/rust/tch-rs/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/juniper/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/juniper/libs/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/tensors/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/min_via/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/adamo/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/mandelbrot/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/advent_of_code/2021/day24/prob1/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/advent_of_code/2021/day19/prob1/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/nerd_snipe/target/" \
    "--exclude=/home/pcalnon/Development/llms/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/jupyter/backups/.ipynb_checkpoints/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/logs/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/resources/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/data/" \
    "--exclude=/home/pcalnon/.sudo_as_admin_successful" \
    "--exclude=/home/pcalnon/.python_history-58693.tmp" \
    "--exclude=/home/pcalnon/.python_history-32739.tmp" \
    "--exclude=/home/pcalnon/.bash_history-51918.tmp" \
    "--exclude=/home/pcalnon/.bash_history-40075.tmp" \
    "--exclude=/home/pcalnon/.bash_history-25805.tmp" \
    "--exclude=/home/pcalnon/.bash_history-21251.tmp" \
    "--exclude=/home/pcalnon/.bash_history-09616.tmp" \
    "--exclude=/home/pcalnon/.bash_history-11775.tmp" \
    "--exclude=/home/pcalnon/SteamMods/" \
    "--exclude=/home/pcalnon/SteamGames/" \
    "--exclude=/home/pcalnon/StarfieldMods/" \
    "--exclude=/home/pcalnon/Dropbox/" \
    "--exclude=/home/pcalnon/FiraxisLive/" \
    "--exclude=/home/pcalnon/Downloads/" \
    "--exclude=/home/pcalnon/Desktop/" \
    "--exclude=/home/pcalnon/.thunderbird/" \
    "--exclude=/home/pcalnon/.dropbox/" \
    "--exclude=/home/pcalnon/.dropbox-dist/" \
    "--exclude=/home/pcalnon/.steam/steam/steamapps/common/Stardew Valley/Mods/zoe_mods/" \
    "--exclude=/home/pcalnon/snap/" \
    "--exclude=/home/pcalnon/.cache/" \
    "--exclude=/home/pcalnon/.local/share/Steam/" \
    "--exclude=/home/pcalnon/snap/steam/" \
    "--exclude=/home/pcalnon/StarfieldData/" \
    "--exclude=/home/pcalnon/VirtualMachines/" \
    "--exclude=/home/pcalnon/.config/Duplicati/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/juniper-data/data/" \
    "--exclude=/home/pcalnon/.config/duplicati-backup/" \
    >> "${LOG_DIR}/console.log" 2>&1
rc=$?
set -e

{
    echo "result=$([[ ${rc} -eq 0 ]] && echo OK || echo FAILED)"
    echo "rc=${rc}"
    echo "when=$(date -Is)"
    echo "gpg_invocations=$(wc -l < "${LOG_DIR}/gpg_invocations.log" 2>/dev/null || echo 0)"
    echo "gpg_nonzero_rc=$(grep -cv 'rc=0 ' "${LOG_DIR}/gpg_invocations.log" 2>/dev/null || echo 0)"
    echo "dest_files=$(find "${DEST_DIR}" -maxdepth 1 -type f | wc -l)"
    echo "flush_errors=$(grep -c "won't flush" "${LOG_DIR}"/*.log 2>/dev/null | awk -F: '{s+=$2} END {print s+0}')"
} | tee "${RUN_DIR}/result.status"

exit "${rc}"
