#!/usr/bin/env bash
# Project     : Juniper
# Sub-Project : juniper-ml
# Application : Yamaguchi backup -- reboot survival check (plan criterion 5)
#
# Does the backup lane come back WITHOUT a graphical login?
#
# Usage:
#   bash util/ad-hoc/yamaguchi_reboot_verify.bash pre     # before rebooting
#   bash util/ad-hoc/yamaguchi_reboot_verify.bash post    # after, WITHOUT logging in graphically
#
# ---------------------------------------------------------------------------
# THE TWO CHECKS THAT CANNOT FAIL, AND SO PROVE NOTHING
#
# The predecessor chain proposed three post-reboot checks. Two of them are
# incapable of failing because of a reboot, and reporting them as evidence is a
# vacuous pass:
#
#   systemctl --user is-enabled yamaguchi-watchdog.timer
#       reads a SYMLINK in timers.target.wants/. It is a fact about the
#       filesystem. It said "enabled" before the reboot and will say "enabled"
#       after, whether or not the user manager ever started.
#
#   loginctl show-user pcalnon -p Linger
#       reads /var/lib/systemd/linger/pcalnon. Same story -- persisted state.
#
# Both test CONFIGURATION, not SURVIVAL. The question this criterion actually
# asks is whether the USER MANAGER comes up with no graphical session, and the
# evidence for that is that `systemctl --user` CONNECTS AT ALL. That is why the
# post lane below runs a command that must talk to the user bus.
#
# THE FALSE NEGATIVE
#
# Do NOT use "server-watchdog.status LAST is after the boot time" as the
# criterion. The watchdog timer is OnCalendar=*-*-* 12:00:00 with
# Persistent=true: it catches up only if a 12:00 elapse point was crossed while
# the machine was down. Reboot at any other hour and LAST legitimately stays
# pre-boot for up to ~23 h -- a HEALTHY reboot scored as a failure. Waiting for
# the 09:00 backup does not help either; it is three hours BEFORE the 12:00
# watchdog. Hence the explicit `start` below: the unit is Type=oneshot, safe to
# trigger on demand, and it refreshes the artifact immediately.
#
# ALSO
#   * server-watchdog.status has NO freshness component -- it would read "OK"
#     forever if the watchdog died. Check the TIMESTAMP, never just the word.
#   * startup-delay=30m is set on the server. For the first half hour after boot
#     job 2's ProposedSchedule can read empty or shifted. That is NOT a failed
#     reboot -- wait out the delay before concluding anything from the schedule.
#   * sdc4 (/media/pcalnon/temp_backups) is NOT in fstab and will not remount.
#     The job no longer touches it, so this is expected, not a fault. But
#     yamaguchi_retire_tier3.py then refuses at gate 0 ("not a mountpoint",
#     exit 3) and the durability check prints "VERDICT : ABSENT" for sdc4 rather
#     than "NOT DURABLE". Remount it (or skip both) before re-running those.
#   * Under linger with no session, notify-send has nowhere to go, so the alert
#     degrades to file-only. That is how an earlier outage went unnoticed.
# ---------------------------------------------------------------------------

set -uo pipefail

REPO=/home/pcalnon/Development/python/Juniper/juniper-ml
STATUS=~/.local/state/duplicati/server-watchdog.status
MODE=${1:-}

hr() { printf '%s\n' "-------------------------------------------------------------"; }

case "$MODE" in
pre)
    echo "== PRE-REBOOT checks  $(date -Is)"
    hr
    echo "boot time  : $(uptime -s)"
    echo
    echo "1. NEVER reboot mid-run. Require ActiveTask: null and an empty queue."
    python3 "$REPO/util/ad-hoc/yamaguchi_server_api.py" status 2>&1 | head -20
    hr
    echo "2. ProposedSchedule above is the next run -- do not reboot across it."
    hr
    echo "3. Record the pre-reboot watchdog artifact for comparison:"
    if [[ -f "$STATUS" ]]; then
        echo "   $(cat "$STATUS")"
    else
        echo "   MISSING: $STATUS"
    fi
    hr
    echo "If ActiveTask is null, you are clear to reboot."
    ;;

post)
    echo "== POST-REBOOT checks  $(date -Is)"
    echo "== Run this WITHOUT logging in graphically -- that is the whole point."
    hr
    BOOT_EPOCH=$(date -d "$(uptime -s)" +%s)
    echo "boot time  : $(uptime -s)"
    rc=0

    echo
    echo "[1/4] system service is back"
    if systemctl is-active --quiet duplicati.service; then
        echo "  PASS  duplicati.service = active"
    else
        echo "  FAIL  duplicati.service = $(systemctl is-active duplicati.service 2>&1)"
        rc=1
    fi

    echo
    echo "[2/4] USER MANAGER came up without a graphical login"
    echo "      (that this command connects at all IS the evidence)"
    if timers=$(systemctl --user list-timers yamaguchi-watchdog.timer --no-pager 2>&1); then
        echo "$timers" | sed 's/^/      /'
        if grep -qE '^\s*NEXT|yamaguchi-watchdog' <<<"$timers"; then
            echo "  PASS  user bus reachable and the timer is known"
        else
            echo "  WARN  user bus reachable but the timer was not listed"
            rc=1
        fi
    else
        echo "$timers" | sed 's/^/      /'
        echo "  FAIL  could not reach the user manager -- lingering did not bring it up"
        rc=1
    fi

    echo
    echo "[3/4] force a watchdog run now (Type=oneshot, safe on demand)"
    echo "      NOT waiting for 12:00 -- see the false-negative note in this file."
    if systemctl --user start yamaguchi-watchdog.service 2>&1 | sed 's/^/      /'; then
        echo "  ran   yamaguchi-watchdog.service"
    else
        echo "  note  non-zero exit is the watchdog's ALERT channel, not a runner fault"
    fi

    echo
    echo "[4/4] the artifact refreshed AFTER boot"
    echo "      (check the TIMESTAMP -- the word OK has no freshness component)"
    if [[ -f "$STATUS" ]]; then
        line=$(cat "$STATUS")
        echo "      $line"
        ts=$(awk '{print $1}' <<<"$line")
        if st_epoch=$(date -d "$ts" +%s 2>/dev/null); then
            if (( st_epoch > BOOT_EPOCH )); then
                echo "  PASS  status timestamp is post-boot"
            else
                echo "  FAIL  status timestamp predates boot -- the forced run did not write"
                rc=1
            fi
        else
            echo "  WARN  could not parse the timestamp: $ts"
            rc=1
        fi
    else
        echo "  FAIL  $STATUS missing"
        rc=1
    fi

    hr
    if (( rc == 0 )); then
        echo "RESULT: PASS -- the lane survives reboot without a graphical login."
        echo "Now let one full SCHEDULED run complete (14:00Z daily) before closing"
        echo "criterion 5. Remember startup-delay=30m: for the first 30 minutes"
        echo "after boot the ProposedSchedule may read empty or shifted, and that"
        echo "is not a fault."
    else
        echo "RESULT: FAIL -- see the failing check above."
    fi
    exit "$rc"
    ;;

*)
    echo "usage: $0 pre|post" >&2
    exit 64
    ;;
esac
