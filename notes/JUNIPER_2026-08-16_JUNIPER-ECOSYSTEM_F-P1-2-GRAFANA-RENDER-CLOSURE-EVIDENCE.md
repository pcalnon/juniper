# CLI Experimentation — F-P1-2: the Grafana block never existed, and the dashboard renders

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-ml / juniper-deploy
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-16

**F-P1-2** — "a native Grafana v13 squats `:3000`, so the containerized dashboard surface cannot
bind" — is **CLOSED**, and it was a **misdiagnosis from the start**. The juniper-deploy Grafana has
not mapped host `:3000` since **2026-05-27**, two months before the program plan was written. The
premise the finding rested on was already false when it was raised on 2026-08-07.

The blocked arms are now positively evidenced, not merely unblocked: **P1.6 interactive dashboard
render**, and the Grafana sub-arms of **P3 criteria 6 (Observability) and 8 (Isolation)**. The
`Juniper Experiments` dashboard was driven end-to-end against a live experiment run and rendered all
13 panels with real data.

Two genuine host defects surfaced while probing, neither of them Juniper's — both recorded in §5.

---

## 1. The correction

The [P3 acceptance rollup §3](JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md)
context package states three facts. All three are wrong.

| P3 rollup §3 claim | Probed 2026-08-16 |
|---|---|
| "The listener on `:3000` is a **system-level `grafana-server.service`**" | **False.** It is the **Domotz Pro agent**, a snap (`snap.domotzpro-agent-publicstore.domotzpro-agent-deamon.service`, active/running). The served HTML is an AngularJS app declaring `ng-app="agent"` and loading `domotz-angular-widgets`. `grafana-server` *wants* `:3000` and cannot have it. |
| "`/api/health` returns 200 with `database: ok`" | **False for `:3000`.** `GET :3000/api/health` → **404**; `GET :3000/login` → **404**; `GET :3000/` → 200 serving the Domotz agent UI. The 200/`database: ok` belongs to the **deploy** Grafana on `:3001`. |
| "Credentials are non-default (anonymous 401; `admin:admin` rejected)" | **A phantom.** That was the Domotz agent refusing, not Grafana. There is no Grafana credential mystery on `:3000` because there is no Grafana on `:3000`. |

And the consequence the finding drew from those facts:

> "the juniper-deploy compose Grafana maps host `:3000`, so the containerized dashboard surface
> (including the Wave-1.4 experiments dashboard) cannot bind while the native service runs."

**It has not mapped `:3000` since 2026-05-27.** `juniper-deploy` commit `c36e52b` —
*"fix(grafana): default host port to 3001 (avoid system-installed grafana on 3000)"*
(juniper-deploy#90) — changed it, and the current mapping is explicit about why:

```yaml
# docker-compose.yml:921-931
# Grafana — Metrics Dashboard (host port 3001 → container 3000)
# Host port is 3001 by default because port 3000 is commonly held by a
# ...
- "127.0.0.1:${GRAFANA_HOST_PORT:-3001}:3000"
```

That predates the 2026-07-29 program plan by two months and the F-P1-2 finding by ten weeks. **No
host change was required to close this finding, and none was made.**

**Method note.** Every fact in the original context package was recorded as "probed read-only
2026-08-08", and the probes were real — but they were probes of the *wrong process*, interpreted
against an assumption about the compose file that was never checked against the compose file. A
port probe tells you something is listening; it does not tell you what. This is the same class as
this program's earlier retraction and the E-I "different spirals" error: **a claim about a
component must be read from that component, not inferred from its neighbourhood.**

---

## 2. What was verified

Run `20260817T011726Z-6d05`, experiment tag `f-p1-2-render`, brought up with
`util/experiment_stack.bash --up --cascor --grafana-bridge`, data `:8111`, cascor `:8231`.

### 2.1 Scrape lane (launcher → relay → Prometheus)

Both socat relays bound the discovered monitoring gateway `172.31.0.1`; the `file_sd` target file
was written to `juniper-deploy/prometheus/targets/20260817T011726Z-6d05.json` and picked up:

```text
host-experiment series: 2
  juniper-cascor  run_id=20260817T011726Z-6d05  experiment=f-p1-2-render  up=1
  juniper-data    run_id=20260817T011726Z-6d05  experiment=f-p1-2-render  up=1
```

### 2.2 Training run

`run_experiment.py --config juniper-cascor/conf/experiments/spiral-smoke.yaml` →
**`outcome: succeeded`, exit 0**, 133.4 s total (drive 130.5 s, 27 polls, `sampling_errors=0`),
`dataset_id=spiral-1.0.0-f98fd84bccbfe1dd`, 3 plots rendered.

### 2.3 Data path *through Grafana* (not just Prometheus)

Queried via Grafana's datasource proxy, so this exercises Grafana's own datasource wiring and the
dashboard's template-variable mechanism — the layer P2/P3 had only ever evidenced at the Prometheus
level:

| check | result |
|---|---|
| `run_id` template variable (`label_values(up{environment="host-experiment"}, run_id)`) | `['20260817T011726Z-6d05']` |
| Host-Experiment Scrape Targets | 2 series, value 1 |
| Targets Up | 2 |
| `juniper_cascor_build_info` / `juniper_data_build_info` | 1 series each |
| `juniper_cascor_training_loss` | 2 series, 0.20409207046031952 |
| `juniper_cascor_hidden_units_total` | 2 |

### 2.4 Interactive render — the arm that was actually blocked

Driven in a real browser against `/d/juniper-experiments/juniper-experiments` with
`var-run_id=20260817T011726Z-6d05`. **All 13 panels rendered with data**, across all three rows:

- **Run Inventory** — About This Dashboard; Host-Experiment Scrape Targets (both rows present,
  `experiment=f-p1-2-render`, instances `host.docker.internal:8231` / `:8111`); Targets Up = **2**.
- **Run Provenance** — Build Info: `juniper-cascor 0.9.0` (python 3.13.13),
  `juniper-data 0.11.0` (python 3.14.2), both carrying `run_id` and `experiment`.
- **Cascor Training** — Training Loss (train 0.204 / validation 0.263), Training Accuracy
  (output 57.5% / validation 35%), Hidden Units (2), Candidate Correlation (≈0.19), Epoch Rate
  (≈0.008 ops/s), Training Step Duration p50 **25.5 ms** / p95 **48.4 ms**.

Screenshot preserved with the run's own artifacts:
`<RUN_DIR>/artifacts/plots/f-p1-2-experiments-dashboard.png`.

**Credential handling.** The real admin secret was never placed in a browser automation step. A
throwaway Grafana viewer account was created via the admin API, used for the render, and **deleted**
immediately afterwards (`/api/users` back to `['admin']`).

### 2.5 Teardown attestation

Pidfile-first teardown of both services and both relays; ports `8111`/`8231` released and confirmed
clear; this run's two port lockdirs removed; the Prometheus target file removed (`targets/` back to
its dotfiles); `artifacts/` preserved. The juniper-deploy stack was untouched throughout (10
containers before and after).

---

## 3. Concurrency observation — Q-6 paying off in the field, same day

A **concurrent session's campaign was running throughout** this verification:
`20260817T011416Z-b01d`, `exp=r5-service-vs-cli`, holding data `:8110` / cascor `:8230` with live
port lockdirs. This run allocated `8111`/`8231` and never contended — the §9.3 lockdir + probe
mechanism behaving exactly as designed under genuine concurrent load, which no prior evidence had
observed live.

More pointedly: **both runs used the same `juniper-cascor` checkout at the same time.** Before
[Q-6](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md)
that is precisely the configuration that destroyed the F-P1-3 arm A/B evidence — the shared
`logs/juniper_cascor.log` is the only place cascor's parent logger writes, so a co-tenant rotates it
away. With `JUNIPER_CASCOR_LOG_DIR` exported per run (cascor#523 + ml#1120), each run's app log
landed in its own `RUN_DIR/logs/`. The hazard H-7 described did not occur.

---

## 4. Disposition

| arm | before | now |
|---|---|---|
| **F-P1-2** | Owner decision, parked since 2026-08-07 | **CLOSED — premise false; no action taken or needed** |
| **P1.6** interactive render | the only non-PASS arm of P1 smoke | **PASS** (§2.4) |
| **P3 criterion 6** Grafana sub-arm | "pending the F-P1-2 decision" | **PASS** (§2.3, §2.4) |
| **P3 criterion 8** "both visible in Grafana" | "shares the F-P1-2 shadow" | **PASS** — both services visible, run-scoped (§2.4) |

P1 smoke and P3 acceptance now have **no** arms outstanding.

---

## 5. Defects found while probing (neither is Juniper's)

**D-1 — `grafana-server.service` is in a hard restart loop.** `NRestarts` was **12,538** at
20:11 CDT and **12,763** by 20:29 — roughly 225 restarts in 18 minutes, continuously. It can never
succeed: it is configured for `:3000`, which the Domotz snap owns. It burns CPU and floods the
journal indefinitely. It is unrelated to Juniper — no Juniper component uses it, and the deploy
stack's Grafana on `:3001` is unaffected.

*Owner-directed remedy: repoint it to a free port* (`:3002` verified free). The reversible form is a
systemd drop-in rather than editing the apt-managed `/etc/grafana/grafana.ini`, which a package
upgrade may overwrite:

```bash
sudo mkdir -p /etc/systemd/system/grafana-server.service.d
printf '[Service]\nEnvironment=GF_SERVER_HTTP_PORT=3002\n' \
  | sudo tee /etc/systemd/system/grafana-server.service.d/override.conf
sudo systemctl daemon-reload && sudo systemctl restart grafana-server
# verify: systemctl show grafana-server -p NRestarts --value   # must stop climbing
#         curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3002/api/health   # expect 200
# revert: sudo rm -rf /etc/systemd/system/grafana-server.service.d && sudo systemctl daemon-reload
```

Requires sudo, so it is left for the operator; nothing in this program depends on it.

> **Update (2026-08-17) — the port IS configurable at start time, proven three ways; and the drop-in
> above is NOT the best form.** The owner asked (correctly) whether the port could be set at server
> start via command line, environment variable, or config file, rather than settling for a
> hard-coded root-level fix. **All three are natively supported**, and two were demonstrated on this
> host **without root**, by running the packaged binary as an unprivileged user against scratch dirs:
>
> | mechanism | form | probe result |
> |---|---|---|
> | **command line** | `grafana server cfg:server.http_port=3002` (the `--configOverrides` / `cfg:` syntax) | **bound `:3002`**, `/api/health` → 200, `database: ok` |
> | **environment variable** | `GF_SERVER_HTTP_PORT=3002` (the standard `GF_<SECTION>_<KEY>` form) | **bound `:3002`**, `/api/health` → 200 |
> | **config file** | `[server] http_port` in an ini passed via `--config` | supported; not separately probed — `/etc/grafana/grafana.ini` is `root:grafana 0640` and unreadable here |
>
> No residual listener after the probe. **The port is hard-coded nowhere** — `grafana.ini`'s default
> is simply what applies when nothing overrides it.
>
> **Better remedy than the drop-in above.** The packaged unit already declares
> `EnvironmentFile=/etc/default/grafana-server`, and its `ExecStart` already uses the `cfg:`
> mechanism for the four path settings. So the designed extension point is a **single line** in that
> file — no new systemd unit fragment, and no edit to the 94 KB packaged `grafana.ini` conffile:
>
> ```bash
> echo 'GF_SERVER_HTTP_PORT=3002' | sudo tee -a /etc/default/grafana-server
> sudo systemctl restart grafana-server
> # verify: systemctl show grafana-server -p NRestarts --value   # must stop climbing
> #         curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3002/api/health   # expect 200
> # revert: sudo sed -i '/^GF_SERVER_HTTP_PORT=/d' /etc/default/grafana-server && sudo systemctl restart grafana-server
> ```
>
> The drop-in recommendation above was written before the unit was read; it works, but it adds a file
> where the packaging already provides one. Prefer the line above.
>
> **What is genuinely not solvable without root, and why it is not a Juniper concern.** The blocker
> was never the mechanism — it is **file ownership**. `grafana-server` is a *system* service
> (`User=grafana`, unit under `/usr/lib/systemd/system`, `grafana.ini` `root:grafana 0640`,
> `/etc/default/grafana-server` `root:root 0644`). Reconfiguring a system service means writing a
> root-owned file, by design; `systemctl edit` is likewise root. That is a property of system
> services, not a Grafana limitation, and **nothing in juniper-ml can or should route around it** —
> this Grafana is an apt package with no Juniper dependency, and putting host system configuration
> inside an application repo would cross a boundary the ecosystem otherwise keeps clean.
>
> **The Juniper-scoped Grafana already has exactly the configurability being asked for.** The deploy
> stack's Grafana takes `GRAFANA_HOST_PORT` (compose `:931`, default `3001`) — an environment
> variable, settable per deployment, no root. That surface needs nothing added.
>
> **Question worth answering before spending root on this at all:** does the native `grafana-server`
> need to run? Nothing in Juniper uses it — the ecosystem's dashboards are the container on `:3001` —
> and it has never successfully bound since Domotz took `:3000`. If it is not wanted,
> `sudo systemctl disable --now grafana-server` ends the restart loop outright and leaves
> `/var/lib/grafana` intact; if it is wanted, the one-line env var above gives it a working port.
> Either way the loop stops. Probe script:
> [`util/ad-hoc/2026-08-17_grafana_port_probe.sh`](../util/ad-hoc/2026-08-17_grafana_port_probe.sh).

**D-2 — the deploy Grafana's mounted admin secret does not match its live password.** The running
container mounts **`secrets.example/grafana_admin_password.txt`** (the repo-committed 28-char
placeholder) at `/run/secrets/grafana_admin_password`, because juniper-deploy has no `.env` setting
`GRAFANA_ADMIN_PASSWORD_FILE` and the compose default is the example path. The password Grafana
actually accepts is the 32-char value in **`secrets/grafana_admin_password.txt`** — the volume was
initialised from it.

This is latent, not currently exploitable: Grafana reads `GF_SECURITY_ADMIN_PASSWORD` **at volume
init only** (the known read-once class), so today the mismatch is invisible. The hazard is that
**any volume re-initialisation silently sets the admin password to a value committed in a public
repository.** The fix is a one-line `.env` entry pointing `GRAFANA_ADMIN_PASSWORD_FILE` at
`./secrets/grafana_admin_password.txt`, so the declared secret and the live secret agree. Filed for
juniper-deploy; not changed here, since it is outside this program's scope and touches a running
stack.

---

## 6. Reproduction

```bash
# Facts
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/api/health   # 404 — not Grafana
curl -s http://localhost:3000/ | grep -o domotz-angular-widgets             # the actual squatter
systemctl show grafana-server -p NRestarts --value                          # climbing
curl -s http://127.0.0.1:3001/api/health                                    # deploy Grafana: database ok
git -C ../juniper-deploy log -1 --format='%h %ad %s' --date=short -L 921,932:docker-compose.yml

# The verification (from the juniper-ml repo root; note the worktree override)
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  util/experiment_stack.bash --up --cascor --grafana-bridge --experiment f-p1-2-render
python util/experiments/run_experiment.py \
  --config ../juniper-cascor/conf/experiments/spiral-smoke.yaml --run-dir <RUN_DIR>
curl -s 'http://127.0.0.1:9090/api/v1/query?query=up%7Benvironment%3D%22host-experiment%22%7D'
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  util/experiment_stack.bash --down <RUN_ID>
```

**Worktree gotcha.** `experiment_stack.bash` derives sibling repos from the juniper-ml root
(`PROJECT_DIR="$(dirname "${JUNIPER_ML_DIR}")"`, `:91`). Run from a **worktree**, that resolves to
`<worktree>/../juniper-cascor`, which does not exist — cascor and the Prometheus targets dir both
point into nowhere. Set `JUNIPER_EXP_PROJECT_DIR` to the real ecosystem root, or run from the
primary checkout. `--dry-run` prints the resolved paths, which is the cheapest way to catch it.
