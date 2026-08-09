# juniper stack fails to start training

the juniper stack fails to successfully start the training process.

## background

### the default case

a successful launch of the juniper stack does not automatically, begin the training process.

- although this behavior was previously present, moving to a user activated training approach is a reasonable design decision.

### the trivial case

clicking on the "Start Training" button in the left menu of the juniper-canopy web frontend, appears to fail silently.

- this behavior pre-supposes a default selection for model and dataset.
- it seems reasonable to expect this to work, although we should probably present the user with the specifics of the defaults and require confirmation before training actually starts.

### the fully determined case

explicitly specifying the model and dataset before clicking on the "Start Training" button, appears to hang indefinitely.

- the "Start Training" button stays in the "active" state indefinitely.
- the logs appear to indicate that there could be an infinite authentication loop.
- of the three scenarios, this should absolutely be working properly at this point.
  - extensive auditing and debugging has been carried out on the stack in general and on juniper-canopy in particular, and this represents the most critical, core functionality, behind the most common, generic use-case.

## juniper stack launch

### containerized startup

containerized startup of the juniper stack, using docker compose, appears to be successful.

```bash
(JuniperCascor1) pcalnon@yamaguchi:~/Development/python/Juniper/juniper-deploy$ make doctor
Juniper Platform — Build-Provenance Doctor
  running image revision (OCI label) vs source repo HEAD
  services derived from: docker compose --profile full --profile demo --profile dev --profile test --profile observability config

  SERVICE                IMAGE SHA    SOURCE HEAD  STATUS
  ────────────────────── ────────── ────────── ──────
  juniper-canopy         96fa3d1      96fa3d1      FRESH
  juniper-canopy-demo    96fa3d1      96fa3d1      FRESH
  juniper-canopy-dev     96fa3d1      96fa3d1      FRESH
  juniper-cascor         d14f32f      d14f32f      FRESH
  juniper-cascor-demo    d14f32f      d14f32f      FRESH
  juniper-cascor-worker  7d59d67      7d59d67      FRESH
  juniper-data           fdbe0de      fdbe0de      FRESH
  juniper-recurrence     606715f      606715f      FRESH

  No stale or dirty images detected.
(JuniperCascor1) pcalnon@yamaguchi:~/Development/python/Juniper/juniper-deploy$ make status
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
(JuniperCascor1) pcalnon@yamaguchi:~/Development/python/Juniper/juniper-deploy$ make up
prepare-secrets: populated=7 placeholder/empty=0 from /home/pcalnon/Development/python/Juniper/juniper-deploy/.env.secrets.enc
Juniper Platform — Bind-Posture Preflight
  verify every *_LOOPBACK_PUBLISH_ATTESTED service publishes loopback-only
  source: docker compose --profile full config

  [OK]   juniper-canopy  JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED=true  host binds: 127.0.0.1:8050
  [OK]   juniper-cascor  JUNIPER_CASCOR_LOOPBACK_PUBLISH_ATTESTED=true  host binds: 127.0.0.1:8201

  PASS — 2 attested service(s) publish loopback-only; bind posture verified.
Juniper Platform — Image-Provenance Preflight
  verify the built images about to run match the code on disk (org.opencontainers.image.revision)
  source: docker compose --profile full config

  [MATCH     ] juniper-canopy:latest        revision 96fa3d1 == juniper-canopy HEAD 96fa3d1
  [MATCH     ] juniper-cascor-worker:latest revision 7d59d67 == juniper-cascor-worker HEAD 7d59d67
  [MATCH     ] juniper-cascor:latest        revision d14f32f == juniper-cascor HEAD d14f32f
  [MATCH     ] juniper-data:latest          revision fdbe0de == juniper-data HEAD fdbe0de
  [MATCH     ] juniper-recurrence:latest    revision 606715f == juniper-recurrence HEAD 606715f

  PASS — 5 image(s) match their checkouts; provenance verified.
[+] up 10/10
 ✔ Network juniper-deploy_frontend                    Created   0.0s
 ✔ Network juniper-deploy_backend                     Created   0.0s
 ✔ Network juniper-deploy_data                        Created   0.0s
 ✔ Container juniper-data                             Healthy   7.0s
 ✔ Container juniper-redis                            Healthy   7.0s
 ✔ Container juniper-cascor                           Healthy  12.0s
 ✔ Container juniper-recurrence                       Started   6.4s
 ✔ Container juniper-canopy                           Started  12.3s
 ✔ Container juniper-deploy-juniper-cascor-worker-2   Started  12.2s
 ✔ Container juniper-deploy-juniper-cascor-worker-1   Started  12.5s
Services starting. Run 'make logs' to follow output.
```

### on-host startup

on-host startup of the juniper stack, using the util/juniper_plant_all.bash script, appears to be successful.

```bash
(JuniperCascor1) pcalnon@yamaguchi:~/Development/python/Juniper/juniper-ml$ ./util/juniper_plant_all.bash
[juniper_plant_all.bash:45] Beginning script run
[juniper_plant_all.bash:50] Script Name:      juniper_plant_all.bash
[juniper_plant_all.bash:51] Script Path:      /home/pcalnon/Development/python/Juniper/juniper-ml/util/juniper_plant_all.bash
[juniper_plant_all.bash:52] Script Dir:       /home/pcalnon/Development/python/Juniper/juniper-ml/util
[juniper_plant_all.bash:82] JUNIPER_PROJECT_PID_FILE="/home/pcalnon/Development/python/Juniper/juniper-ml/JuniperProject.pid"
[juniper_plant_all.bash:320] === Pre-flight Checks ===
[juniper_plant_all.bash:205] Conda environment 'JuniperData' validated at /opt/miniforge3/envs/JuniperData
[juniper_plant_all.bash:205] Conda environment 'JuniperCascor1' validated at /opt/miniforge3/envs/JuniperCascor1
[juniper_plant_all.bash:205] Conda environment 'JuniperCanopy1' validated at /opt/miniforge3/envs/JuniperCanopy1
[juniper_plant_all.bash:205] Conda environment 'JuniperCascor1' validated at /opt/miniforge3/envs/JuniperCascor1
[juniper_plant_all.bash:188] Port 8100 is available for juniper-data
[juniper_plant_all.bash:188] Port 8201 is available for juniper-cascor
[juniper_plant_all.bash:188] Port 8050 is available for juniper-canopy
[juniper_plant_all.bash:188] Port 8210 is available for juniper-cascor-worker (health listener)
[juniper_plant_all.bash:374] === Pre-flight Checks Passed ===
[juniper_plant_all.bash:380] source "/opt/miniforge3/etc/profile.d/conda.sh"

[juniper_plant_all.bash:400] === Starting juniper-data ===
[juniper_plant_all.bash:401] cd "/home/pcalnon/Development/python/Juniper/juniper-data"
[juniper_plant_all.bash:403] conda activate "JuniperData"
[juniper_plant_all.bash:405] PYTHON_GIL=0 nohup uvicorn juniper_data.api.app:get_app --factory --host "127.0.0.1" --port "8100" >"/home/pcalnon/Development/python/Juniper/juniper-data/logs/juniper-data_2026-07-09_1856.log" 2>&1 &
[juniper_plant_all.bash:409] JUNIPER_DATA_PID=1019953
[juniper_plant_all.bash:410] Log: /home/pcalnon/Development/python/Juniper/juniper-data/logs/juniper-data_2026-07-09_1856.log
[juniper_plant_all.bash:226] Waiting for juniper-data health at http://localhost:8100/v1/health (timeout: 60s)
[juniper_plant_all.bash:230] juniper-data is healthy (took 4s)

[juniper_plant_all.bash:418] === Starting juniper-cascor ===
[juniper_plant_all.bash:419] cd "/home/pcalnon/Development/python/Juniper/juniper-cascor/src"
[juniper_plant_all.bash:421] conda activate "JuniperCascor1"
[juniper_plant_all.bash:423] JUNIPER_CASCOR_HOST="localhost" JUNIPER_CASCOR_PORT="8201" nohup "/opt/miniforge3/envs/JuniperCascor1/bin/python" "server.py" >"/home/pcalnon/Development/python/Juniper/juniper-cascor/logs/juniper-cascor_2026-07-09_1856.log" 2>&1 &
[juniper_plant_all.bash:431] JUNIPER_CASCOR_PID="1020122"
[juniper_plant_all.bash:432] Log: /home/pcalnon/Development/python/Juniper/juniper-cascor/logs/juniper-cascor_2026-07-09_1856.log
[juniper_plant_all.bash:226] Waiting for juniper-cascor health at http://localhost:8201/v1/health (timeout: 60s)
[juniper_plant_all.bash:230] juniper-cascor is healthy (took 4s)

[juniper_plant_all.bash:440] === Starting juniper-canopy ===
[juniper_plant_all.bash:441] cd "/home/pcalnon/Development/python/Juniper/juniper-canopy/src"
[juniper_plant_all.bash:443] conda activate "JuniperCanopy1"
[juniper_plant_all.bash:446] JUNIPER_CANOPY_CASCOR_SERVICE_URL="http://localhost:8201" JUNIPER_CANOPY_JUNIPER_DATA_URL="http://localhost:8100" nohup "/opt/miniforge3/envs/JuniperCanopy1/bin/python" "main.py" >"/home/pcalnon/Development/python/Juniper/juniper-canopy/logs/juniper-canopy_2026-07-09_1856.log" 2>&1 &
[juniper_plant_all.bash:452] JUNIPER_CANOPY_PID=1020306
[juniper_plant_all.bash:453] Log: /home/pcalnon/Development/python/Juniper/juniper-canopy/logs/juniper-canopy_2026-07-09_1856.log
[juniper_plant_all.bash:226] Waiting for juniper-canopy health at http://localhost:8050/v1/health (timeout: 60s)
[juniper_plant_all.bash:230] juniper-canopy is healthy (took 4s)

[juniper_plant_all.bash:461] === Starting juniper-cascor-worker ===
[juniper_plant_all.bash:463] conda activate "JuniperCascor1"
[juniper_plant_all.bash:465] CASCOR_SERVER_URL="ws://localhost:8201/ws/v1/workers" CASCOR_WORKER_HEALTH_PORT="8210" CASCOR_WORKER_HEALTH_BIND="127.0.0.1" nohup "/opt/miniforge3/envs/JuniperCascor1/bin/juniper-cascor-worker" >"/home/pcalnon/Development/python/Juniper/juniper-cascor-worker/logs/juniper-cascor-worker_2026-07-09_1856.log" 2>&1 &
[juniper_plant_all.bash:473] JUNIPER_WORKER_PID=1020478
[juniper_plant_all.bash:474] Log: /home/pcalnon/Development/python/Juniper/juniper-cascor-worker/logs/juniper-cascor-worker_2026-07-09_1856.log
[juniper_plant_all.bash:226] Waiting for juniper-cascor-worker health at http://127.0.0.1:8210/v1/health/ready (timeout: 60s)
[juniper_plant_all.bash:230] juniper-cascor-worker is healthy (took 2s)

[juniper_plant_all.bash:486] === Writing PID File ===
[juniper_plant_all.bash:487] conda deactivate
[juniper_plant_all.bash:505] PID file written to /home/pcalnon/Development/python/Juniper/juniper-ml/JuniperProject.pid:
juniper-data=1019953
juniper-cascor=1020122
juniper-canopy=1020306
juniper-cascor-worker=1020478

[juniper_plant_all.bash:509] === All Juniper services started successfully ===
[juniper_plant_all.bash:510]   juniper-data          : PID 1019953   @ http://localhost:8100
[juniper_plant_all.bash:511]   juniper-cascor        : PID 1020122 @ http://localhost:8201
[juniper_plant_all.bash:512]   juniper-canopy        : PID 1020306 @ http://localhost:8050
[juniper_plant_all.bash:513]   juniper-cascor-worker : PID 1020478 @ http://127.0.0.1:8210/v1/health/ready
```

## workflow screenshots

### naive training start after clean launch

The following attached screenshots illustrate the silent failure mode that happens when training start is attempted immediately after a successful launch of the on-host or containerized stack.

- Image #1: prior to Start Training button click
- Image #2: after clicking Start Training button--the button is in the active state
- Image #3: button returns to idle state after failing silently to start training

### start training after specifying a dataset

The following attached screenshots illustrate the juniper canopy application stuck in training startup mode after a clean launch and a dataset being selected.

- Image #21: The "Dataset View" tab is selected from the canopy top tab menu.
- Image #22: The "Spiral" dataset is selected from the Dataset Parameters module of the left menu, Current Dataset section, Dataset subsection, Type dropdown.
- Image #23: Updating the noise parameter for the selected Spiral dataset, set to 0.125.
- Image #24: Clicking the "Apply Parameters" button results in the following error conditions: the parameter value error, "Please select a valid value. The two nearest valid values are 0.1 and 0.15", and the parameter update error, "Failed to apply (502)".
- Image #25: Selecting a "valid" noise parameter value, 0.1, and clicking the "Apply Parameters" button still results in the parameter update error, "Failed to apply (502)".
- Image #26: After the dataset type and parameters have been updated, and prior to clicking the "Apply Dataset" button.
- Image #27: After clicking the "Apply Dataset" button, the "Dataset change pending" dialog box is opened.
- Image #28: After clicking the "Stop & Restart with new dataset" button and before clicking the "Start" training button--the button is in the "highlighted" (i.e., mouse hover) state.
- Image #29: After clicking the "Start" training button, the button is in the "active" state; the juniper-canopy application continues in this state indefinitely.

## logs

the logs generated by the on-host stack seem to indicate that canopy is stuck in a repeated, authentication issue loop.

```bash
2026-07-09 19:19:46,820 [WARNING] juniper_canopy.backend.cascor_service_adapter: Control stream supervisor disconnected (Failed to connect to ws://localhost:8201/ws/control: server rejected WebSocket connection: HTTP 403), reconnecting in 30s
2026-07-09 19:19:50,414 [WARNING] juniper_canopy.backend.cascor_service_adapter: Failed to fetch canopy params: No network created
2026-07-09 19:19:50,420 [ERROR] juniper_canopy.backend.cascor_service_adapter: Failed to get network data: No network created
2026-07-09 19:19:51,527 [INFO] frontend.base_component.HDF5SnapshotsPanel: Fetching snapshots from API
2026-07-09 19:19:55,448 [WARNING] juniper_canopy.backend.cascor_service_adapter: Failed to fetch canopy params: No network created
2026-07-09 19:19:55,454 [ERROR] juniper_canopy.backend.cascor_service_adapter: Failed to get network data: No network created
2026-07-09 19:20:00,449 [WARNING] juniper_canopy.backend.cascor_service_adapter: Failed to fetch canopy params: No network created
2026-07-09 19:20:00,453 [ERROR] juniper_canopy.backend.cascor_service_adapter: Failed to get network data: No network created
2026-07-09 19:20:01,630 [INFO] frontend.base_component.HDF5SnapshotsPanel: Fetching snapshots from API
2026-07-09 19:20:03,690 [WARNING] juniper_cascor_client.observability: juniper_cascor_client_unrecognized_ws_frame
2026-07-09 19:20:03,690 [WARNING] juniper_canopy.observability: juniper_canopy_unrecognized_ws_frame
2026-07-09 19:20:05,484 [WARNING] juniper_canopy.backend.cascor_service_adapter: Failed to fetch canopy params: No network created
2026-07-09 19:20:05,500 [ERROR] juniper_canopy.backend.cascor_service_adapter: Failed to get network data: No network created
2026-07-09 19:20:10,536 [WARNING] juniper_canopy.backend.cascor_service_adapter: Failed to fetch canopy params: No network created
2026-07-09 19:20:10,555 [ERROR] juniper_canopy.backend.cascor_service_adapter: Failed to get network data: No network created
2026-07-09 19:20:11,758 [INFO] frontend.base_component.HDF5SnapshotsPanel: Fetching snapshots from API
2026-07-09 19:20:15,570 [WARNING] juniper_canopy.backend.cascor_service_adapter: Failed to fetch canopy params: No network created
2026-07-09 19:20:15,589 [ERROR] juniper_canopy.backend.cascor_service_adapter: Failed to get network data: No network created
```

---

[Image #1] [Image #2] [Image #3] [Image #21] [Image #22] [Image #23] [Image #24] [Image #25] [Image #26] [Image #27] [Image #28] [Image #29]

---

| Image Label | Image File                                                                              |
|-------------|-----------------------------------------------------------------------------------------|
| [Image #1]  | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-50-59.png |
| [Image #1]  | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-50-59.png |
| [Image #2]  | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-51-09.png |
| [Image #3]  | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-53-39.png |
| [Image #21] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-53-49.png |
| [Image #22] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-54-15.png |
| [Image #23] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-54-27.png |
| [Image #24] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-54-46.png |
| [Image #25] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-55-10.png |
| [Image #26] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-55-19.png |
| [Image #27] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-56-04.png |
| [Image #28] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2019-56-12.png |
| [Image #29] | file:///home/pcalnon/Pictures/Screenshots/Screenshot%20From%202026-07-09%2018-54-47.png |

---
