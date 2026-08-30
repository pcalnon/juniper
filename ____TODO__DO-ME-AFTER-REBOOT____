#!/usr/bin/env bash


# Print it, store it off-machine, shred -u. (0600, excluded from the archive by filter 36).
cat ${HOME}/.cache/yamaguchi-key-escrow-sheet.txt | lpr

# then securely remove file:
shred -u ${HOME}/.cache/yamaguchi-key-escrow-sheet.txt

# VERIFY the job survived the restart -- this is the §2 trap's blast radius:
python3 ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_census.py --runs 1     # expect '-> AGREE'

# And then this script. pre & post are command line params?
${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_reboot_verify.bash             # pre / post ?
