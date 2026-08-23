#!/usr/bin/env bash
########################################################################################################################################################################################################################
# Script:    average_iso_size.bash
# Project:   Juniper
# Author:    Paul Calnon
# Date:      2026-08-23
# Version:   v0.1
#
# Copyright (c) 2026 Paul Calnon
########################################################################################################################################################################################################################
#
# Description:
#   This script calculates the average size of ISO files in the current directory.
#
########################################################################################################################################################################################################################
#
# Usage:
#   average_iso_size.bash
#
# Example:
#   average_iso_size.bash
#
# Output:
#   Iso Count: 10, Total Size: 100, Mean Size: 10
#
########################################################################################################################################################################################################################
#
# Notes:
#   This script uses the ls -Flah command to list the ISO files and the awk command to extract the size.
#   The tr command is used to remove the "G." from the size.
#   The bc command is used to calculate the mean size.
#
#   for i in $(l -h *.iso | awk -F " " '{print $5;}' | tr -d "G."); do
#   SIZE=$(ls -Flah "${i}" | awk -F " " '{print $5;}' | tr -d "G.")
#   COUNT_ADJ=$( 10#${COUNT} * 10#10 | )
#   MEAN=$(( 10#${TOTAL} / 10#${COUNT} ))
#
########################################################################################################################################################################################################################

COUNT=0
TOTAL=0

# SEARCH_DIR="${PWD}"
SEARCH_DIR="${HOME}/Downloads"

for i in "${SEARCH_DIR}"/*.iso ; do
    SIZE=$(du -sh "${i}" | awk -F " " '{print $1;}' | tr -d "G.")
    TOTAL=$(echo "scale=2; ${TOTAL} + ${SIZE}" | bc)
    COUNT=$(( 10#${COUNT} + 1 ))

    echo "Count: ${COUNT}, Value: ${SIZE}, Total: ${TOTAL}"
done

COUNT_ADJ=$( echo "scale=2; ${COUNT} * 10" | bc )
TOTAL_ADJ=$( echo "scale=2; ${TOTAL} / 10" | bc )

MEAN=$(echo "scale=2; ${TOTAL} / ${COUNT_ADJ}" | bc)

echo "Iso Count: ${COUNT}, Total Size: ${TOTAL_ADJ}, Mean Size: ${MEAN}"

exit 0
