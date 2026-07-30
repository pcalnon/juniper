# CLI Experimentation Program — Wave 0 / P0 Preflight Evidence

**Project**: Juniper — CasCor Neural Network Research Platform
**Author**: Paul Calnon
**Date executed**: 2026-07-30
**Status**: Complete — all P0 steps executed; **Wave 1.1 gate: OPEN**
**Plan of record**: [`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) — §10.1 (P0), §14 Wave 0 (items 0.2 / 0.2b)

This document is the evidence filing required by Wave 0 items 0.2 and 0.2b. The owner ratified the plan and every open-question recommendation (Q-1…Q-12) on 2026-07-30 before execution. All commands ran on the development host; env binaries were invoked directly (`/opt/miniforge3/envs/<env>/bin/…`), which is equivalent to `conda activate <env>` for these steps.

---

## 1. Verdict summary

| Step | Verdict | One-line result |
|---|---|---|
| P0.1 | PASS | `JuniperCascor1` + `JuniperData` present; `-DEPRECATED` envs exist but unused |
| P0.2 | PASS | All five imports OK in `JuniperCascor1` (py 3.13.13, torch 2.11.0+cu130, matplotlib 3.10.9, pyyaml 6.0.3); `juniper_recurrence` **0.3.0** (F-7) |
| P0.3 | PASS | All six imports OK in `JuniperData` (py **3.14.2 free-threaded**, uvicorn 0.40.0, numpy 2.4.1, requests 2.32.5) — settles the §6.3 driver-dependency claim |
| P0.4 | PASS (command erratum F-4) | Editables: 9/9 `FRESH`, 0 `ORPHANED`; floors: 15/15 `OK`, 0 `BELOW_FLOOR` (run with `--env JuniperCascor1 --env JuniperData`) |
| P0.5 | PASS | data up on 8110 in 4 s; generators: **15/16 available, only `mnist` unavailable** — exactly the predicted G-16 state |
| P0.6 | PASS (finding F-1) | cascor 8230 healthy in 4 s; `/metrics` **307-redirects** to `/metrics/`; exposition non-empty; `juniper_cascor_build_info{version="0.6.0"}` present |
| P0.7 | PASS | With `JUNIPER_CASCOR_METRICS_ENABLED` unset, `/metrics` and `/metrics/` both **404** — G-3 confirmed live, not folklore |
| P0.8 | PASS (note F-8) | recurrence 8260 ready in **1.1 s** (warm start; cold-start 10-15 s remains the design point); `juniper_recurrence_build_info{version="0.3.0"}` |
| P0.9 | PASS | `make obs` from cold: all five baseline jobs `up` (`prometheus`, data, cascor, recurrence, canopy), `environment="docker"` |
| **P0.10** | **PASS — Q-4 ANSWERED** | Control arm: `connection refused` (never a 403). Relay arm: both host targets **`up == 1`** with run-scoped labels; see §5 |
| P0.11 | PASS (finding F-2) | monitoring gateway **172.31.0.1** (subnet 172.31.0.0/16); backend 172.28.0.1; default bridge **172.17.0.1**; `socat` at `/usr/bin/socat` |
| P0.12 | PASS (wording erratum F-5) | All three experiment sub-ranges empty (8110-8139 / 8230-8259 / 8260-8289); ambient non-experiment listeners recorded |

Host state was fully restored after evidence capture (§6).

## 2. Environment probes (P0.1–P0.4)

```text
$ ls /opt/miniforge3/envs/
AgentControlPanel  CloseBuildWithUs  JuniperCanopy-DEPRECATED  JuniperCanopy1  JuniperCascor-DEPRECATED
JuniperCascor1  JuniperCassandra  JuniperData  JuniperPython-DEPRECATED  TrustMe  kvm_k8s
```

```text
JuniperCascor1: python 3.13.13 | juniper_cascor 0.6.0 | juniper_recurrence 0.3.0 | torch 2.11.0+cu130 | matplotlib 3.10.9 | pyyaml 6.0.3
JuniperData:    python 3.14.2 (free-threaded) | juniper_data 0.6.0 | uvicorn 0.40.0 | matplotlib 3.10.8 | pyyaml 6.0.3 | numpy 2.4.1 | requests 2.32.5
```

Drift checkers (from the juniper-ml checkout):

```text
$ python3 util/editable_install_drift_check.py
  9 editable install(s): 9 FRESH, 0 WORKTREE_PINNED, 0 ORPHANED          (exit 0)

$ python3 util/env_floor_drift_check.py --env JuniperCascor1 --env JuniperData
  15 floor(s): 15 OK, 0 BELOW_FLOOR, 0 MISSING                           (exit 0)
```

Note: the floor table reads `juniper-recurrence 0.2.0` from dist-info METADATA while the editable's live `_version.py` is 0.3.0 — the known editable-metadata lag, not a floor violation (F-7).

## 3. Host service launches (P0.5–P0.8)

Launched per plan §6.1 (data → cascor → recurrence), `RUN_DIR` under the session scratchpad:

```text
data(8110):   pid ready in 4 s; /v1/generators → total=16 available=15; unavailable: mnist
cascor(8230, METRICS_ENABLED=true): healthy in 4 s
  /metrics  → HTTP 307   (ASGI-mount redirect; see F-1)
  /metrics/ → HTTP 200; juniper_cascor_build_info{python_version="3.13.13",version="0.6.0"} 1.0
cascor(8231, METRICS_ENABLED unset): /metrics → 404, /metrics/ → 404, body {"detail":"Not Found"}   (stopped after probe)
recurrence(8260): first successful /v1/health/ready after 1.1 s (warm start)
  juniper_recurrence_build_info{python_version="3.13.13",version="0.3.0"} 1.0
```

## 4. Docker observability baseline (P0.9, P0.11)

Docker was fully down before Wave 0 (0 containers). `make obs` (= `monitor`: `--env-file .env.observability --profile full --profile observability up -d`) brought the stack up cleanly.

```text
$ curl -s localhost:9090/api/v1/targets   (baseline, stock config)
job=juniper-canopy      instance=juniper-canopy:8050       health=up  env=docker
job=juniper-cascor      instance=juniper-cascor:8200       health=up  env=docker
job=juniper-data        instance=juniper-data:8100         health=up  env=docker
job=juniper-recurrence  instance=juniper-recurrence:8210   health=up  env=docker
job=prometheus          instance=localhost:9090            health=up  env=docker
total active targets: 5
```

```text
network=juniper-deploy_backend     subnet=172.28.0.0/16  gateway=172.28.0.1
network=juniper-deploy_monitoring  subnet=172.31.0.0/16  gateway=172.31.0.1
default bridge gateway: 172.17.0.1
socat: /usr/bin/socat
```

## 5. P0.10 — the relay probe (step 0.2b; answers Q-4)

**Overlay (hand-applied, uncommitted, fully reverted after capture):** (a) `extra_hosts: ["host.docker.internal:172.31.0.1"]` on the prometheus service — the monitoring-network gateway **explicitly** (see F-2); (b) a `juniper-host-experiments` scrape job with `file_sd_configs` reading `/etc/prometheus/targets/*.json` (`refresh_interval: 15s`, `honor_labels: false`);
(c) a target file naming `host.docker.internal:8230` (cascor) + `:8110` (data) with labels `environment="host-experiment"`, `run_id="wave0-p010-probe"`, `experiment="p0-preflight"`.
No new volume mount was needed — the existing `./prometheus:/etc/prometheus:ro` mount already exposes `targets/` (F-3). Container recreated via the same compose invocation `make obs` uses.

**Control arm — overlay live, NO relay** (the §7.1 kernel-refusal prediction, verbatim):

```text
instance=host.docker.internal:8230  service=juniper-cascor  run_id=wave0-p010-probe env=host-experiment
  health=down lastError=Get "http://host.docker.internal:8230/metrics": dial tcp 172.31.0.1:8230: connect: connection refused
instance=host.docker.internal:8110  service=juniper-data    run_id=wave0-p010-probe env=host-experiment
  health=down lastError=Get "http://host.docker.internal:8110/metrics": dial tcp 172.31.0.1:8110: connect: connection refused
```

Connection **refused** — not a 403 — exactly the failure signature the redesigned §7.3 predicts. A gateway-addressed scrape can never land on a loopback bind; no allowlist change could have fixed this.

**Relay arm** — two launcher-style relays (`socat "TCP-LISTEN:<port>,bind=172.31.0.1,fork,reuseaddr" "TCP:127.0.0.1:<port>"`, pids recorded, apps untouched and loopback-bound):

```text
instance=host.docker.internal:8110  service=juniper-data    run_id=wave0-p010-probe health=up lastError=(none)
instance=host.docker.internal:8230  service=juniper-cascor  run_id=wave0-p010-probe health=up lastError=(none)
up targets: 2/2

PromQL up{environment='host-experiment'}:
  up{service=juniper-data,run_id=wave0-p010-probe} = 1
  up{service=juniper-cascor,run_id=wave0-p010-probe} = 1
PromQL juniper_cascor_build_info{environment='host-experiment'}:
  {version=0.6.0,run_id=wave0-p010-probe} = 1
```

The full chain is proven end-to-end: host-run loopback-bound service → launcher-owned gateway relay → dockerized Prometheus, with R1.1-compliant **scrape-side** run identity (`run_id` as a target label; the apps never learned it, and `MetricsAuthMiddleware` needed **zero** configuration because the relay presents a loopback source address). **Q-4 is answered; Wave 1.1 is evidence-gated open.**

## 6. State restoration attestation

Executed in order after capture: relays killed (0 listeners left on 172.31.0.1); overlay reverted (`git checkout -- prometheus/prometheus.yml docker-compose.yml`, `targets/` removed; `juniper-deploy` porcelain clean); prometheus recreated stock (5 baseline targets, 0 `juniper-host-experiments` references); full stack brought back **down** (0 containers — the pre-Wave-0 state); the three host services stopped by verified listener pid (§7 F-6); final sweep:

```text
data 8110-8139: 0 listeners | cascor 8230-8259: 0 | recurrence 8260-8289: 0
operator cascor 8200: untouched throughout (2 listeners, v4+v6)
orphaned launch processes: 0
```

## 7. Findings and errata (feed forward into Waves 1-2)

| # | Finding | Consequence |
|---|---|---|
| F-1 | cascor `/metrics` (no slash) answers **307** to `/metrics/` (ASGI sub-app mount semantics); `curl -sf` without `-L` silently yields empty output. Prometheus is unaffected (scrape `follow_redirects` defaults true — the existing dockerized scrape of the same mount already works). | Plan §6.1 verification lines corrected to `curl -sfL` (this PR). Wave 2.2's driver must use redirect-following GETs for its `/metrics` sampling. |
| F-2 | The compose `host-gateway` **keyword** resolves to the default-bridge gateway (172.17.0.1), while the §7.3 relay binds the **monitoring**-network gateway (172.31.0.1). The coherent form is an **explicit-IP** `extra_hosts` mapping, which is what this probe used successfully. | Wave 1.1 must ship the explicit-IP form (explicit-IP preferred over relaying on the default-bridge gateway — shortest path, no cross-bridge iptables exposure). Plan §7.3 wording updated (this PR). |
| F-3 | No new volume mount is needed for target files: `./prometheus:/etc/prometheus:ro` already exposes `prometheus/targets/`. | Wave 1.1 shrinks to: `extra_hosts` + scrape job + `targets/.gitkeep` (+ its structural test). |
| F-4 | P0.4's bare `env_floor_drift_check.py` exits 2 from juniper-ml (no env maps to `juniper-ml` in `ecosystem.yaml`) — the tool's documented unresolved-env arm. | Correct invocation is `--env JuniperCascor1 --env JuniperData`; plan §10.1 P0.4 row corrected (this PR). |
| F-5 | P0.12's naive `ss` span 8110-8289 includes **non-experiment** ports: an unidentified listener on `0.0.0.0:8181` (owner not resolvable without root) and the operator's on-host cascor on `127.0.0.1:8200` — both outside every experiment sub-range. | Acceptance is per-sub-range emptiness (8110-8139 / 8230-8259 / 8260-8289); plan §10.1 P0.12 row corrected (this PR). |
| F-6 | Wrapper-PID class (known ecosystem gotcha, reconfirmed): `$!` after `cd … && nohup <server> … &` is the **backgrounded subshell**, not the server — all three "recorded" pids died on signal while the servers lived on. | Wave 2.1's launcher must resolve the authoritative pid from the **listener** (`ss -tlnpH "sport = :<port>"`) after the health gate, write THAT to the pidfile, keeping kill-by-port as fallback. Teardown here verified each pid's cmdline + owner before killing. |
| F-7 | Version drift vs the plan's drafting snapshot: live `juniper_recurrence` is **0.3.0** (plan §2/§3 recorded 0.2.0 at SHA `f23f3ba`); the dist-info floor table still reads 0.2.0 (editable-metadata lag). | No action for Wave 0; re-pin provenance when Wave 3 touches the recurrence repo. |
| F-8 | Recurrence bound in **1.1 s** warm (imports page-cached from P0.2 minutes earlier); the 10-15 s figure is the cold-start design point. | Keep the launcher's health-gate timeout sized for cold start (≥ 60 s); do not tune down based on warm numbers. |

## 8. Gate decision

- **0.2 (P0.1-P0.9 + P0.11-P0.12): complete, all PASS** (two command-form errata folded into the plan in this same change).
- **0.2b (P0.10): complete — Q-4 answered empirically in favor of the launcher-owned relay.** The without-relay control shows kernel connection-refusal; the with-relay arm shows both targets `up == 1` with run-scoped labels flowing into PromQL.
- **Wave 1.1 (juniper-deploy: explicit-IP `extra_hosts` + `juniper-host-experiments` file_sd job + `prometheus/targets/.gitkeep` + structural test) is UNBLOCKED**, with F-2/F-3 as binding implementation guidance.
