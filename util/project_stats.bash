#!/usr/bin/env bash
#########################################################################################################################################################################################################################################
#
#########################################################################################################################################################################################################################################

TRUE=0
FALSE=1



#########################################################################################################################################################################################################################################
#

PROJECT_NAME="Juniper"
REPO_PREFIX="juniper"

JUNIPER_PROJECT="${HOME}/Development/python/${PROJECT_NAME}"



#########################################################################################################################################################################################################################################
#

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
#

TOTAL_SIZE=0
TOTAL_LINES=0
TOTAL_FILES=0
TOTAL_REPOS=0
TOTAL_SOURCE=0



#########################################################################################################################################################################################################################################
#

for i in $(ls ${JUNIPER_PROJECT} | grep -e "^${REPO_PREFIX}-" ); do

    # Exclude Legacy code if flagged
    if [[ ( "${LEGACY_NAME}" == "${i}" ) && ( "${INCLUDE_LEGACY}" != "${TRUE}" ) ]]; then
        continue
    fi

    REPO_PATH="${JUNIPER_PROJECT}/${i}"

    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]]; then
        if (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
            printf "%-6s%-20s\t%-6s%-s\n" "Name:" ${i} "Path:" ${REPO_PATH}
        fi
        if (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
            printf "\n"
        fi
    fi

    REPO_SIZE="$(du -s --exclude="juniper-data/data/*" ${REPO_PATH} | awk -F " " '{print $1;}')"

    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]]; then
        if (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
            printf "%-6s%7s\t%-6s%-20s\t%-6s%-s\n" "Size:" $(numfmt --format %6.1f --to=iec ${REPO_SIZE}) "Name:" ${i} "Path:" ${REPO_PATH}
        fi
        if (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
            printf "\n"
        fi
    fi

    REPO_LINES=0
    REPO_FILES=0
    SOURCE_SIZE=0

    for j in $(find ${REPO_PATH} -name '.claude' -prune -o -name '*.py' -print); do

        FILE_NAME="$(basename ${j})"

        FILE_LINES=$(cat ${j} | wc -l)
        FILE_SIZE=$(du -s ${j} | awk -F " " '{print $1;}')

        SOURCE_SIZE=$(( SOURCE_SIZE + FILE_SIZE ))
        REPO_LINES=$(( REPO_LINES + FILE_LINES ))

        REPO_FILES=$(( REPO_FILES + 1 ))

        if (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
            printf "%-s%'8d\t%-s%8s\t%-s%'10d\t%-s%10s\t%-s%8s\t%-9s%-55s\t%-9s%-s\n" "File Lines:" ${FILE_LINES} "File Size:" $(numfmt --format %6.1f --to=iec ${FILE_SIZE}) "Repo Lines:" ${REPO_LINES} "Repo Source Size:" $(numfmt --format %6.1f --to=iec ${SOURCE_SIZE}) "Repo Size:" $(numfmt --format %6.1f --to=iec ${REPO_SIZE}) "Name:" ${FILE_NAME} "Path:" ${j}
        fi

    done

    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]] && (( DISPLAY_LEVEL <= FILE_DISPLAY )); then
        printf "\n"
    fi
    if (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
        printf "%-14s%s\t%-s%10s\t%-s%'10d\t%-s%'10d\t%-9s%-20s\t%-9s%-s\n" "Repo Size:" $(numfmt --format %6.1f --to=iec ${REPO_SIZE}) "Source Size:" $(numfmt --format %6.1f --to=iec ${SOURCE_SIZE}) "Files:" ${REPO_FILES} "Lines:" ${REPO_LINES} "Name:" ${i} "Path:" ${REPO_PATH}
    fi
    if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]] && (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
        printf "\n"
    fi

    TOTAL_FILES=$(( TOTAL_FILES + REPO_FILES ))
    TOTAL_SIZE=$(( TOTAL_SIZE + REPO_SIZE ))
    TOTAL_SOURCE=$(( TOTAL_SOURCE + SOURCE_SIZE ))
    TOTAL_LINES=$(( TOTAL_LINES + REPO_LINES ))

    TOTAL_REPOS=$(( TOTAL_REPOS + 1 ))

done

if [[ "${DETAILED_OUTPUT}" == "${TRUE}" ]] && (( DISPLAY_LEVEL <= REPO_DISPLAY )); then
    printf "\n"
fi
if (( DISPLAY_LEVEL <= PROJECT_DISPLAY )); then
    printf "\nProject Totals:\n%-6s%'10d\t%-7s%'d\t%-6s%5s\t%-8s%s\t%-7s%'10d\n\n" "Repos:" ${TOTAL_REPOS} "Files:" ${TOTAL_FILES} "Size:" $(numfmt --format %6.1f --to=iec ${TOTAL_SIZE}) "Source:" $(numfmt --format %6.1f --to=iec ${TOTAL_SOURCE}) "Lines:" ${TOTAL_LINES}
fi
