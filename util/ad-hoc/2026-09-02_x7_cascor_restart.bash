#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       X7 Lane-A1 helper: restart ONLY the cascor leg of the /tmp/juniper-x7-a1 isolated
#                stack, reproducing the exact launch line isolated_stack.bash used, and rewrite the
#                run-dir pid file (reaper protection key).
#
# Author:        Paul Calnon
# License:       MIT License
#####################################################################################################################################################################################################
set -u

RUN_DIR=/tmp/juniper-x7-a1
CASCOR_SRC=/home/pcalnon/Development/python/Juniper/juniper-cascor/src
UVICORN=/opt/miniforge3/envs/JuniperCascor1/bin/uvicorn

cd "${CASCOR_SRC}" || exit 1

LD_LIBRARY_PATH= \
JUNIPER_DATA_URL=http://127.0.0.1:8105 \
JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://127.0.0.1:8055 \
nohup "${UVICORN}" api.app:create_app --factory --host 127.0.0.1 --port 8206 \
    >> "${RUN_DIR}/logs/juniper-cascor.log" 2>&1 &

echo $! > "${RUN_DIR}/juniper-cascor.pid"
echo "cascor relaunched pid=$(cat "${RUN_DIR}/juniper-cascor.pid")"
