#!/usr/bin/env bash
# Narrow the Duplicati web service from *:8300 to loopback (ROOT).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-29
# Status:     ad-hoc — owner decision 2026-08-29 (note §8.19): "narrow bind only"
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§2, §8.19)
#
# Usage:
#   sudo bash util/ad-hoc/yamaguchi_narrow_bind.bash             # edit + verify, NO restart
#   sudo bash util/ad-hoc/yamaguchi_narrow_bind.bash --restart   # also restart the service
#
# ---------------------------------------------------------------------------
# THE TRAP THIS SCRIPT EXISTS TO AVOID
#
# /etc/default/duplicati ships BOTH of these lines:
#
#   DAEMON_OPTS="--webservice-interface=any --webservice-port=8300 --portable-mode"
#   # DAEMON_OPTS="--webservice-interface=loopback --webservice-port=8300"
#
# The commented line OMITS --portable-mode. Swapping the comment markers is the
# most natural way to make this change and it reproduces the note §2 restart
# trap, which cost this arc a full session.
#
# Mechanism, confirmed 2026-08-29: duplicati.service is
#   EnvironmentFile=-/etc/default/duplicati
#   ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS
# and the live server keeps BOTH databases in /usr/lib/duplicati/data/ -- the
# PORTABLE location. Without --portable-mode the server looks in root's profile
# instead, finds no job, and comes up EMPTY: no Yamaguchi backup, no schedule,
# no history. It looks like total loss and is merely a wrong data directory.
#
# So: this script EDITS THE ACTIVE LINE IN PLACE and asserts --portable-mode
# survives. It never activates the commented line, and it refuses to leave a
# DAEMON_OPTS without --portable-mode behind.
#
# The narrowing works because the server DB already stores
# server-listen-interface=loopback (verified 2026-08-29 via
# GET /api/v1/serversettings). The command-line flag is what OVERRIDES it, so
# the fix is to DELETE the flag, not to add =loopback.
#
# This is defence-in-depth, not closing live exposure: ufw is active.
# ---------------------------------------------------------------------------
set -euo pipefail

CONF=/etc/default/duplicati
RESTART=0
[ "${1:-}" = "--restart" ] && RESTART=1

if [ "$(id -u)" -ne 0 ]; then
    echo "REFUSE: must run as root ($CONF is root-owned)" >&2
    exit 2
fi
if [ ! -f "$CONF" ]; then
    echo "REFUSE: $CONF not found" >&2
    exit 2
fi

active=$(grep -E '^\s*DAEMON_OPTS=' "$CONF" || true)
if [ -z "$active" ]; then
    echo "REFUSE: no ACTIVE DAEMON_OPTS= line in $CONF (only commented ones?)" >&2
    exit 2
fi
if [ "$(grep -cE '^\s*DAEMON_OPTS=' "$CONF")" -ne 1 ]; then
    echo "REFUSE: more than one active DAEMON_OPTS= line; resolve by hand" >&2
    exit 2
fi

echo "== before"
echo "   $active"

if ! grep -qE '^\s*DAEMON_OPTS=.*--webservice-interface=any' "$CONF"; then
    echo "== nothing to do: the active line has no --webservice-interface=any"
    echo "   current bind:"
    ss -ltn 2>/dev/null | grep -E '8300' || echo "   (nothing listening on 8300)"
    exit 0
fi

backup="$CONF.bak-$(date +%Y%m%d-%H%M%S)"
cp -a "$CONF" "$backup"
echo "== backup: $backup"

# Edit the ACTIVE line only (anchored to line start, so the commented variant is
# untouched): drop the interface flag and any doubled space it leaves behind.
sed -i -E 's|^(\s*DAEMON_OPTS=.*)--webservice-interface=any\s*|\1|' "$CONF"
sed -i -E 's|^(\s*DAEMON_OPTS=")\s+|\1|' "$CONF"

after=$(grep -E '^\s*DAEMON_OPTS=' "$CONF" || true)
echo "== after"
echo "   $after"

# --- the assertion that makes this safe --------------------------------------
fatal=0
if ! grep -qE '^\s*DAEMON_OPTS=.*--portable-mode' "$CONF"; then
    echo "FATAL: the active DAEMON_OPTS lost --portable-mode. Restarting now would" >&2
    echo "       bring the server up against root's profile with NO job defined." >&2
    fatal=1
fi
if grep -qE '^\s*DAEMON_OPTS=.*--webservice-interface=any' "$CONF"; then
    echo "FATAL: --webservice-interface=any is still present after the edit." >&2
    fatal=1
fi
if [ "$fatal" -ne 0 ]; then
    cp -a "$backup" "$CONF"
    echo "ROLLED BACK from $backup -- $CONF is unchanged." >&2
    exit 3
fi
echo "== assertions passed (--portable-mode intact, interface flag removed)"

if [ "$RESTART" -ne 1 ]; then
    echo
    echo "NOT restarting (pass --restart to apply). The running server keeps its"
    echo "current bind until it is restarted."
    exit 0
fi

# --- restart, but never across a running backup ------------------------------
echo "== checking for an in-flight backup before restarting"
state=$(runuser -u pcalnon -- python3 \
    /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_server_api.py \
    status 2>/dev/null || true)
if [ -n "$state" ]; then
    echo "$state" | head -12
    if ! grep -q '"ActiveTask": null' <<<"$state"; then
        echo "REFUSE: ActiveTask is not null -- a backup is in flight. Restarting now" >&2
        echo "        would interrupt it. Re-run when it is idle." >&2
        exit 4
    fi
else
    echo "WARN: could not read server status; not restarting on an unknown state." >&2
    exit 4
fi

systemctl restart duplicati.service
sleep 3
echo "== service"
systemctl is-active duplicati.service
echo "== bind now"
ss -ltn 2>/dev/null | grep -E '8300' || echo "   (nothing listening on 8300)"
echo
echo "VERIFY the job survived the restart -- this is the §2 trap's blast radius:"
echo "  python3 util/ad-hoc/yamaguchi_census.py --runs 1   # expect '-> AGREE'"
