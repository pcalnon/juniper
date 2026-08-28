#!/usr/bin/env bash
#########################################################################################################################################################################################################################################
# Project: Juniper
# Repository: juniper-ml
# Script: project_stats.bash
#
# Author: Paul Calnon <overtoad.research@gmail.com>
# Date: 2026-08-28
# Version: 1.0.0
#
# Description:
#   Display the statistics of the Juniper project and all active repositories.
#########################################################################################################################################################################################################################################
#
# Usage:
#   ./util/project_stats.bash
#
# Output:
#   Displays the statistics of the Juniper project and all active repositories.
#
#########################################################################################################################################################################################################################################
# Notes:
#
#########################################################################################################################################################################################################################################

#########################################################################################################################################################################################################################################
# Define the Script variables and environment constants.
#########################################################################################################################################################################################################################################
TRUE=0
FALSE=1


#########################################################################################################################################################################################################################################
# Define the project and repository names.
PROJECT_NAME="Juniper"
REPO_PREFIX="juniper"

JUNIPER_PROJECT="${HOME}/Development/python/${PROJECT_NAME}"


#########################################################################################################################################################################################################################################
# Define the display constants.
PROJECT_DISPLAY="2"
REPO_DISPLAY="1"
FILE_DISPLAY="0"

# DISPLAY_LEVEL=${PROJECT_DISPLAY}
DISPLAY_LEVEL=${REPO_DISPLAY}
# DISPLAY_LEVEL=${FILE_DISPLAY}

# DETAILED_OUTPUT="${TRUE}"
DETAILED_OUTPUT="${FALSE}"


#########################################################################################################################################################################################################################################
# INCLUDE_LEGACY="${TRUE}"
INCLUDE_LEGACY="${FALSE}"

LEGACY_NAME="juniper-legacy"


#########################################################################################################################################################################################################################################
# Define the total statistics variables.
TOTAL_FILES=0
TOTAL_LINES=0
TOTAL_REPOS=0
TOTAL_SIZE=0
TOTAL_SOURCE=0


#########################################################################################################################################################################################################################################
# Display the script variables.
# echo "JUNIPER_PROJECT: ${JUNIPER_PROJECT}"
# echo "REPO_PREFIX: ${REPO_PREFIX}"
# echo "LEGACY_NAME: ${LEGACY_NAME}"
# echo "INCLUDE_LEGACY: ${INCLUDE_LEGACY}"
# echo "DETAILED_OUTPUT: ${DETAILED_OUTPUT}"
# echo "DISPLAY_LEVEL: ${DISPLAY_LEVEL}"
# echo "TOTAL_FILES: ${TOTAL_FILES}"
# echo "TOTAL_LINES: ${TOTAL_LINES}"
# echo "TOTAL_REPOS: ${TOTAL_REPOS}"
# echo "TOTAL_SIZE: ${TOTAL_SIZE}"
# echo "TOTAL_SOURCE: ${TOTAL_SOURCE}"


#########################################################################################################################################################################################################################################
# Display the statistics of the Juniper project and all active repositories.
# for i in $(ls "${JUNIPER_PROJECT}" | grep -e "^${REPO_PREFIX}-" ); do
# for i in "${JUNIPER_PROJECT}"/*; do

for i in "${JUNIPER_PROJECT}"/*; do
    # echo "i: ${i}"
    # Set the repository path.
    REPO_PATH="${i}"
    # echo "REPO_PATH: ${REPO_PATH}"
    # Get the repository name.
    REPO_NAME="$(basename "${REPO_PATH}")"
    # echo "REPO_NAME: ${REPO_NAME}"
    # Bail if not a repository Directory.
    # if [[ "${REPO_NAME}" != "${REPO_PREFIX}-*" ]]; then
    if [[ "$(echo "${REPO_NAME}" | grep -e "^${REPO_PREFIX}-.*$")" == "" ]]; then
        # echo "Not a repository directory."
        continue
    # Bail if repository is Legacy code and not flagged for inclusion.
    elif [[ "${REPO_NAME}" == "${LEGACY_NAME}" ]] && [[ "${INCLUDE_LEGACY}" != "${TRUE}" ]]; then
        # echo "Legacy repository and not flagged for inclusion."
        continue;
    fi

    # Display the repository statistics.
    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]]; then
        # echo "Displaying detailed output."
        if (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
            printf "%-6s%-20s\t%-6s%-s\n" "Name:" "${REPO_NAME}" "Path:" "${REPO_PATH}"
        fi
        if (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
            printf "\n"
        fi
    fi

    # Get the repository size.
    REPO_SIZE="$(du -s --exclude="juniper-data/data/*" "${REPO_PATH}" | awk -F " " '{print $1;}')"
    # echo "REPO_SIZE: ${REPO_SIZE}"

    # Display the repository statistics.
    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]]; then
        if (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
            printf "%-6s%7s\t%-6s%-20s\t%-6s%-s\n" "Size:" "$(numfmt --format %6.1f --to=iec "${REPO_SIZE}")" "Name:" "${CURRENT_REPO_NAME}" "Path:" "${REPO_PATH}"
        fi
        if (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
            printf "\n"
        fi
    fi

    # Initialize the repository statistics.
    REPO_LINES=0
    REPO_FILES=0
    SOURCE_SIZE=0

    # Loop through the repository files.
    while IFS= read -r -d '' file; do
        # Get the file name.
        FILE_NAME="$(basename "${file}")"
        # Get the file lines.
        FILE_LINES="$(wc  -l "${file}" | awk -F " " '{print $1;}')"
        # Get the file size.
        FILE_SIZE="$(du -s "${file}" | awk -F " " '{print $1;}')"
        # Update the repository statistics.
        SOURCE_SIZE=$(( SOURCE_SIZE + FILE_SIZE ))
        REPO_LINES=$(( REPO_LINES + FILE_LINES ))
        REPO_FILES=$(( REPO_FILES + 1 ));
        # Display the file statistics.
        if (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
            printf "%-s%'8d\t%-s%8s\t%-s%'10d\t%-s%10s\t%-s%8s\t%-9s%-55s\t%-9s%-s\n" "File Lines:" "${FILE_LINES}" "File Size:" "$(numfmt --format %6.1f --to=iec "${FILE_SIZE}")" "Repo Lines:" "${REPO_LINES}" "Repo Source Size:" "$(numfmt --format %6.1f --to=iec "${SOURCE_SIZE}")" "Repo Size:" "$(numfmt --format %6.1f --to=iec "${REPO_SIZE}")" "Name:" "${FILE_NAME}" "Path:" "${file}";
        fi;
    done <   <(find "${REPO_PATH}" -name '.claude' -prune -o -name '*.py' -print0);

    # for j in $(find "${REPO_PATH}" -name '.claude' -prune -o -name '*.py' -print); do
    #     FILE_NAME="$(basename "${j}")"
    #     # FILE_LINES=$(cat "${j}" | wc -l)
    #     FILE_LINES="$(wc  -l "${j}" | awk -F " " '{print $1;}')"
    #     FILE_SIZE="$(du -s "${j}" | awk -F " " '{print $1;}')"
    #     SOURCE_SIZE=$(( SOURCE_SIZE + FILE_SIZE ))
    #     REPO_LINES=$(( REPO_LINES + FILE_LINES ))
    #     REPO_FILES=$(( REPO_FILES + 1 ))
    #     if (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
    #         printf "%-s%'8d\t%-s%8s\t%-s%'10d\t%-s%10s\t%-s%8s\t%-9s%-55s\t%-9s%-s\n" "File Lines:" "${FILE_LINES}" "File Size:" "$(numfmt --format %6.1f --to=iec "${FILE_SIZE}")" "Repo Lines:" "${REPO_LINES}" "Repo Source Size:" "$(numfmt --format %6.1f --to=iec "${SOURCE_SIZE}")" "Repo Size:" "$(numfmt --format %6.1f --to=iec "${REPO_SIZE}")" "Name:" "${FILE_NAME}" "Path:" "${j}"
    #     fi
    # done

    # Display the repository statistics.
    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]] && (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
        printf "\n"
    fi
    if (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
        printf "%-14s%s\t%-s%10s\t%-s%'10d\t%-s%'10d\t%-9s%-20s\t%-9s%-s\n" "Repo Size:" "$(numfmt --format %6.1f --to=iec "${REPO_SIZE}")" "Source Size:" "$(numfmt --format %6.1f --to=iec "${SOURCE_SIZE}")" "Files:" "${REPO_FILES}" "Lines:" "${REPO_LINES}" "Name:" "${REPO_NAME}" "Path:" "${REPO_PATH}"
    fi
    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]] && (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
        printf "\n"
    fi

    # Update the total statistics.
    TOTAL_FILES=$((  TOTAL_FILES  + REPO_FILES  ))
    TOTAL_SIZE=$((   TOTAL_SIZE   + REPO_SIZE   ))
    TOTAL_SOURCE=$(( TOTAL_SOURCE + SOURCE_SIZE ))
    TOTAL_LINES=$((  TOTAL_LINES  + REPO_LINES  ))
    TOTAL_REPOS=$((  TOTAL_REPOS  + 1           ))
done

if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]] && (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
    printf "\n"
fi
if (( DISPLAY_LEVEL <= PROJECT_DISPLAY )); then
    printf "\nProject Totals:\n%-6s%'10d\t%-7s%'d\t%-6s%5s\t%-8s%s\t%-7s%'10d\n\n" "Repos:" "${TOTAL_REPOS}" "Files:" "${TOTAL_FILES}" "Size:" "$(numfmt --format %6.1f --to=iec "${TOTAL_SIZE}")" "Source:" "$(numfmt --format %6.1f --to=iec "${TOTAL_SOURCE}")" "Lines:" "${TOTAL_LINES}"
fi
