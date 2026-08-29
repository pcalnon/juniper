#!/usr/bin/env bash
#
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# Version:     0.2.0
# License:     MIT License
#
# End-to-end SCRATCH reproduction of the 2026-08-23 Duplicati GPGFlushError
# failure: a full duplicati-cli backup of the real source with the real job's
# options, against a throwaway destination/database/tempdir/passphrase, with
# three instruments the failing run lacked:
#
#   1. --log-file-log-level=Verbose        (captures Retry lines, invisible at
#                                           the default console Warning level)
#   2. a gpg wrapper that logs START at spawn and END after a correct re-wait
#      (discriminates "gpg exited fine, pump-side frozen" from "gpg itself
#      stalled" on a GPGFlushError event; an END-less START line at crash time
#      is positive evidence of an in-flight gpg)
#   3. a 5 s sampler: system PSI avg10+totals, cgroup-local PSI totals,
#      MemAvailable/SwapFree, duplicati RSS/swap/threads, cgroup-scoped gpg
#      pid:state:wchan tuples, dest/tmp growth, free-space watchdog
#
# Run it inside a systemd transient unit to match the failing run's context
# (Nice=10, IOSchedulingClass=best-effort, IOSchedulingPriority=7), optionally
# with MemoryHigh/MemoryMax to emulate the collapsed-available-memory enabling
# condition of the 2026-08-23 episode (prefer MemoryHigh throttling; keep
# MemoryMax well above the process's anonymous needs so the cgroup OOM killer
# stays out of the experiment):
#
#   systemd-run --user --unit=gpg-macro-repro --collect \
#       -p Nice=10 -p IOSchedulingClass=best-effort -p IOSchedulingPriority=7 \
#       [-p MemoryHigh=6G -p MemoryMax=10G] \
#       -p RuntimeMaxSec=18000 \
#       /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/mossy-growing-salamander/util/ad-hoc/duplicati_gpg_macro_repro.bash
#
# SAFETY: refuses to run unless the scratch filesystem is mounted with >=100 GB
# free; every write lands under a fresh run directory in _gpg_repro/; the real
# destination, the real databases, and the real credential files are never
# read or written (the passphrase is a fresh random scratch value). The
# expected footprint is ~55 GB of volumes plus up to ~5 GB of Verbose log; a
# runtime watchdog TERMs the repro's own duplicati-cli if scratch free space
# falls below 60 GB, protecting the real destination's staging headroom on the
# shared drive. A concurrent writer to either real destination or the fresh
# job's database aborts the launch (write-mode /proc fd scan -- name-anchored
# process greps are fail-open, see util/duplicati_scheduled_backup.bash guard
# 5); read-only holders such as the archive Recreate are expected ambient and
# do not block. Adversarially validated 2026-08-24; material findings F1, F2,
# F9, F10, F11, F15, F16, F18, F21, F23 fixed in this revision.

set -euo pipefail

RUN_ROOT="/media/pcalnon/temp_backups/_gpg_repro"
REAL_DEST_DIR="/media/pcalnon/temp_backups/Ubuntu"
OLD_ARCHIVE_DIR="/mnt/Backups/Ubuntu"
REAL_DBPATH="/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite"
SOURCE_PATH="/home/pcalnon"
MIN_FREE_GB=100
MIN_FREE_RUNTIME_GB=60

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

# Anything holding the fresh job's database open (any mode), or holding a
# WRITE handle under either real destination, means a real backup operation is
# in flight. Read-only holders (the Recreate fetching a dblock) pass.
scan_real_holders() {
    local fd tgt flags
    for fd in /proc/[0-9]*/fd/*; do
        [[ -e "${fd}" ]] || continue
        tgt="$(readlink "${fd}" 2>/dev/null)" || continue
        case "${tgt}" in
            "${REAL_DBPATH}")
                echo "${fd} -> ${tgt}"
                ;;
            "${REAL_DEST_DIR}/"*|"${OLD_ARCHIVE_DIR}/"*)
                flags="$(awk '/^flags:/{print $2}' "${fd%/fd/*}/fdinfo/${fd##*/}" 2>/dev/null || true)"
                if [[ -n "${flags}" ]] && (( (8#${flags} & 3) != 0 )); then
                    echo "${fd} -> ${tgt} (write-mode)"
                fi
                ;;
        esac
    done
}
HOLDERS="$(scan_real_holders | head -5 || true)"
[[ -z "${HOLDERS}" ]] || fail "real backup artifacts are held open: ${HOLDERS}"

# a concurrent micro-harness would pollute gpg sampling and double the load
if pgrep -f gpg_tail_latency.py >/dev/null 2>&1; then
    fail "gpg_tail_latency.py is running; finish the micro trials first"
fi

RUN_DIR="${RUN_ROOT}/macro-$(date +%Y%m%d-%H%M%S)"
DEST_DIR="${RUN_DIR}/dest"
TEMP_DIR="${RUN_DIR}/tmp"
LOG_DIR="${RUN_DIR}/logs"
DBPATH="${RUN_DIR}/repro.sqlite"
mkdir -p "${DEST_DIR}" "${TEMP_DIR}" "${LOG_DIR}"

[[ -e "${DBPATH}" ]] && fail "dbpath already exists: ${DBPATH}"

CGREL="$(cut -d: -f3 /proc/self/cgroup)"
CGDIR="/sys/fs/cgroup${CGREL}"

# ---- scratch passphrase (never the real credentials) ------------------------
PASSPHRASE="$(openssl rand -hex 22)"
export PASSPHRASE
umask 077
printf 'PASSPHRASE=%s\n' "${PASSPHRASE}" > "${RUN_DIR}/env"
PP_SHA="$(printf '%s' "${PASSPHRASE}" | sha256sum | cut -c1-16)"

# ---- gpg wrapper: START line at spawn, END line after a correct re-wait -----
# <&0 is load-bearing: a background job in non-interactive bash otherwise gets
# stdin from /dev/null and the passphrase/plaintext never reach gpg.  fds 1/2
# are closed the moment gpg's exit status is settled, BEFORE any bookkeeping:
# the pump's EOF (and so Duplicati's 5 s Join window) waits on the wrapper's
# inherited stdout write-end, and the instrument must not sit inside the
# window it measures.  $EPOCHREALTIME avoids date(1) forks entirely.
GPG_WRAPPER="${RUN_DIR}/gpg_logged.bash"
cat > "${GPG_WRAPPER}" <<WRAP
#!/usr/bin/env bash
exec 9>>"${LOG_DIR}/gpg_invocations.log"
start=\${EPOCHREALTIME}
/usr/bin/gpg "\$@" <&0 &
child=\$!
printf 'START pid=%s gpgpid=%s start=%s args=%s\n' "\$\$" "\$child" "\$start" "\$*" >&9
trap 'kill -TERM "\$child" 2>/dev/null' TERM INT
wait "\$child"; rc=\$?
if [ "\$rc" -gt 128 ]; then wait "\$child"; rc=\$?; fi
exec 1>&- 2>&-
end=\${EPOCHREALTIME}
printf 'END pid=%s gpgpid=%s start=%s end=%s rc=%s\n' "\$\$" "\$child" "\$start" "\$end" "\$rc" >&9
exit "\$rc"
WRAP
chmod +x "${GPG_WRAPPER}"

# ---- monitor ----------------------------------------------------------------
MON_CSV="${LOG_DIR}/monitor.csv"
echo "epoch,mem_avail_kb,swap_free_kb,psi_cpu_avg10,psi_io_avg10,psi_mem_avg10,psi_cpu_total,psi_io_total,psi_mem_total,cg_mem_some_total,cg_mem_full_total,cg_io_some_total,cg_io_full_total,dup_rss_kb,dup_swap_kb,dup_threads,gpg_tuples,dest_files,tmp_kb,free_gb" > "${MON_CSV}"

psi_line() {  # $1=file $2=line-index(1=some,2=full) -> "avg10 total"
    awk -v n="$2" 'NR==n{split($2,a,"=");split($5,b,"=");print a[2],b[2]}' "$1" 2>/dev/null || echo "0 0"
}

monitor() {
    set +e
    local dup_pid mem_avail swap_free rss swp thr dfiles tkb fgb tuples p st wc
    while :; do
        dup_pid="$(pgrep -f "duplicati-cli backup file://${DEST_DIR}" 2>/dev/null | head -1)"
        mem_avail="$(awk '/MemAvailable/{print $2}' /proc/meminfo)"
        swap_free="$(awk '/SwapFree/{print $2}' /proc/meminfo)"
        read -r c_avg c_tot < <(psi_line /proc/pressure/cpu 1)
        read -r i_avg i_tot < <(psi_line /proc/pressure/io 1)
        read -r m_avg m_tot < <(psi_line /proc/pressure/memory 1)
        read -r _ cgms < <(psi_line "${CGDIR}/memory.pressure" 1)
        read -r _ cgmf < <(psi_line "${CGDIR}/memory.pressure" 2)
        read -r _ cgis < <(psi_line "${CGDIR}/io.pressure" 1)
        read -r _ cgif < <(psi_line "${CGDIR}/io.pressure" 2)
        if [[ -n "${dup_pid}" ]] && [[ -r "/proc/${dup_pid}/status" ]]; then
            rss="$(awk '/VmRSS/{print $2}' "/proc/${dup_pid}/status" 2>/dev/null)"
            swp="$(awk '/VmSwap/{print $2}' "/proc/${dup_pid}/status" 2>/dev/null)"
            thr="$(awk '/Threads/{print $2}' "/proc/${dup_pid}/status" 2>/dev/null)"
        else
            rss=0; swp=0; thr=0
        fi
        # cgroup-scoped gpg sampling: pid:state:wchan tuples (';'-joined).
        # System-wide pgrep would count unrelated gpg work (F15).
        tuples=""
        for p in $(pgrep -x gpg 2>/dev/null); do
            grep -qF "${CGREL}" "/proc/${p}/cgroup" 2>/dev/null || continue
            st="$(awk '{print $3}' "/proc/${p}/stat" 2>/dev/null)"
            wc="$(cat "/proc/${p}/wchan" 2>/dev/null)"
            tuples="${tuples}${p}:${st:-?}:${wc:-?};"
        done
        dfiles="$(find "${DEST_DIR}" -maxdepth 1 -type f 2>/dev/null | wc -l)"
        tkb="$(du -sk "${TEMP_DIR}" 2>/dev/null | cut -f1)"
        fgb="$(df -BG --output=avail /media/pcalnon/temp_backups 2>/dev/null | tail -1 | tr -dc '0-9')"
        echo "$(date +%s),${mem_avail},${swap_free},${c_avg},${i_avg},${m_avg},${c_tot},${i_tot},${m_tot},${cgms},${cgmf},${cgis},${cgif},${rss:-0},${swp:-0},${thr:-0},${tuples:-none},${dfiles},${tkb:-0},${fgb:-0}" >> "${MON_CSV}" || true
        if [[ -n "${fgb}" ]] && [[ "${fgb}" -lt "${MIN_FREE_RUNTIME_GB}" ]] && [[ -n "${dup_pid}" ]]; then
            echo "$(date -Is) WATCHDOG: free space ${fgb} GB < ${MIN_FREE_RUNTIME_GB} GB floor, TERM ${dup_pid}" >> "${LOG_DIR}/watchdog.log"
            kill "${dup_pid}" 2>/dev/null || true
        fi
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
    echo "epoch       : $(date +%s)"
    echo "passphrase  : scratch, sha256[:16]=${PP_SHA} (env file: ${RUN_DIR}/env)"
    echo "dest        : file://${DEST_DIR}"
    echo "dbpath      : ${DBPATH}"
    echo "tempdir     : ${TEMP_DIR}"
    echo "gpg wrapper : ${GPG_WRAPPER}"
    echo "cgroup      : ${CGREL}"
    echo "unit memory : MemoryHigh=$(cat "${CGDIR}/memory.high" 2>/dev/null || echo '?') MemoryMax=$(cat "${CGDIR}/memory.max" 2>/dev/null || echo '?')"
    echo "nice(self)  : $(awk '{print $19}' /proc/self/stat 2>/dev/null)"
} | tee "${LOG_DIR}/run_params.txt"

# ---- the backup (options cloned from util/duplicati_scheduled_backup.bash) --
# DELIBERATE DIVERGENCE (2026-08-24): the runner has since gained the
# GPGFlushError mitigations (--gpg-encryption-switches=--compress-algo none,
# --asynchronous-upload-limit=1). This harness reproduces the FAILING
# 2026-08-23 configuration and must NOT inherit them -- the whole point is the
# old regime. To test the mitigated lane instead, add both options here.
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
    echo "gpg_started=$(grep -c '^START ' "${LOG_DIR}/gpg_invocations.log" 2>/dev/null || true)"
    echo "gpg_ended=$(grep -c '^END ' "${LOG_DIR}/gpg_invocations.log" 2>/dev/null || true)"
    echo "gpg_nonzero_rc=$(awk '/^END /{if ($NF != "rc=0") n++} END{print n+0}' "${LOG_DIR}/gpg_invocations.log" 2>/dev/null)"
    echo "dest_files=$(find "${DEST_DIR}" -maxdepth 1 -type f | wc -l)"
    echo "flush_errors=$(grep -c "won't flush" "${LOG_DIR}/duplicati.log" 2>/dev/null || true)"
} | tee "${RUN_DIR}/result.status"

exit "${rc}"
