#!/usr/bin/env bash
# Project     : Juniper
# Sub-Project : juniper-ml
# Application : ad-hoc utility
# Author      : Paul Calnon
# Version     : 1.0.0
# License     : MIT License
#
# Yamaguchi destination-durability check.
#
# Answers one question: will the backup DESTINATION filesystem be mounted after a
# reboot, without a desktop login?  A Duplicati job whose `file://` target is on a
# filesystem that nothing mounts at boot can fire against a bare directory on the
# root filesystem and see an empty destination against a populated local job DB.
#
# The tell is systemd's view of the mount unit:
#   FragmentPath=/run/systemd/generator/<unit>.mount + SourcePath=/etc/fstab
#       -> generated FROM fstab; mounts at boot.  DURABLE.
#   FragmentPath=<empty>          + SourcePath=/proc/self/mountinfo
#       -> systemd merely OBSERVED an existing mount and synthesised a passive
#          unit to track it.  Nothing remounts it at boot.  NOT DURABLE.
#
# Read-only.  Exits 0 always; the verdict is on stdout (this is a reporting
# probe, not a gate -- a nonzero exit would make it unusable inside `&&` chains
# during an incident).
#
# Usage: bash util/ad-hoc/yamaguchi_destination_durability_check.bash [MOUNTPOINT ...]
#        Defaults to the current Yamaguchi destination fs and the sda1 archive fs.

set -uo pipefail

TARGETS=("$@")
if [[ ${#TARGETS[@]} -eq 0 ]]; then
    TARGETS=(/media/pcalnon/temp_backups /mnt/Backups/Ubuntu)
fi

echo "== Yamaguchi destination-durability check at $(date -Is)"
echo "== host uptime since: $(uptime -s)  ($(uptime -p))"
echo

for mp in "${TARGETS[@]}"; do
    echo "---- $mp"
    if ! mountpoint -q "$mp"; then
        echo "  MOUNTED   : NO -- not a mountpoint right now"
        echo "  VERDICT   : ABSENT"
        echo
        continue
    fi

    src=$(findmnt -no SOURCE --target "$mp")
    opts=$(findmnt -no OPTIONS --target "$mp")
    unit=$(systemd-escape --path --suffix=mount "$mp")
    frag=$(systemctl show "$unit" -p FragmentPath --value 2>/dev/null)
    spath=$(systemctl show "$unit" -p SourcePath --value 2>/dev/null)
    infstab=NO
    if findmnt -no SOURCE --fstab --target "$mp" >/dev/null 2>&1; then
        infstab=YES
    fi

    echo "  MOUNTED   : YES  source=$src"
    echo "  OPTIONS   : $opts"
    echo "  UNIT      : $unit"
    echo "  Fragment  : ${frag:-<empty>}"
    echo "  SourcePath: ${spath:-<empty>}"
    echo "  in fstab  : $infstab"

    if [[ "$infstab" == "YES" && -n "$frag" ]]; then
        echo "  VERDICT   : DURABLE -- fstab-generated, mounts at boot"
    else
        echo "  VERDICT   : NOT DURABLE -- no boot-time mount configuration;"
        echo "              systemd only observed an existing mount."
        echo "              A root-owned system unit firing before/without this"
        echo "              mount sees a BARE PATH, not the destination."
    fi
    echo
done

echo "== free space on the root filesystem (the fallback a bare path would fill)"
df -h / | tail -1
