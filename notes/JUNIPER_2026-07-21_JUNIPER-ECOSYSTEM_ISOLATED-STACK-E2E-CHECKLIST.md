# Isolated-Stack E2E Verification Checklist — Juniper Training-Runtime

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Scope**: juniper-data, juniper-cascor, juniper-canopy (+ juniper-cascor-client)
**Author**: Paul Calnon (checklist by Claude Code)
**License**: MIT License
**Version**: 1.0
**Last Updated**: 2026-07-21

---

This is the **durable, repeatable** isolated-stack end-to-end (E2E) verification checklist for the canopy
training-runtime remediation. It encodes what the live verification sessions of 2026-07-16 → 2026-07-19 actually
did and learned, distilled from the fix plan's **§9 Verification Plan** and the **§13** living-tracker addenda
(2026-07-16 / 2026-07-17 / 2026-07-18) in
[`JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md`](JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md)
(roadmap unit **E1**, closes *verification*).

The bring-up recipe below is also encoded (as executable + `--dry-run`-previewable steps) in the helper script
[`util/isolated_stack.bash`](../util/isolated_stack.bash).

## 1. Why an isolated stack (and never the operator's)

Every check here runs against a **fresh, throwaway trio** on non-default ports — juniper-data on **8101**,
juniper-cascor on **8202**, juniper-canopy on **8051** — with cascor pointed at the isolated juniper-data. This
is the §9 pattern: *"never against the operator's stack."* The operator's on-host stack (data 8100 / cascor 8201 /
canopy 8050) and the deploy Docker stack must be left untouched — several of these checks (start / stop-restart /
metrics-clear) mutate training state, and the whole point of the 2026-07-10 incident investigation was to observe
without perturbing production state.

Use this checklist when:

- verifying any training-runtime roadmap unit (D*/C*/N*) end-to-end after its per-repo suite is green;
- reproducing the OPEN experiments E-1 / E-2 / E-3;
- re-checking the full wave after a Docker rebuild (`make up`) under the deploy build-freshness / provenance guards.

## 2. Prerequisites

| Service | Port | Runtime | Notes |
|---------|------|---------|-------|
| juniper-data   | 8101 | **dedicated `python3.14 -m venv`** | Do NOT reuse the `JuniperData` conda env — keep it pristine. |
| juniper-cascor | 8202 | `JuniperCascor1` conda env | Py 3.13 + torch 2.11.0 (the known-good env; see `util/juniper_plant_all.bash`). |
| juniper-canopy | 8051 | `JuniperCanopy1` conda env | Has the LIBTORCH-strip activate hook. Service mode (`JUNIPER_CANOPY_DEMO_MODE=0`). |

Repo checkouts are assumed under `/home/pcalnon/Development/python/Juniper/` (the ecosystem root). Adjust paths
if your layout differs; the helper script derives them from its own location and accepts overrides (§8).

## 3. Stack bring-up recipe

Bring the services up in dependency order **data → cascor → canopy**, health-checking each before the next.

### 3.1 juniper-data on 8101 (dedicated venv)

The base install has **no server** (uvicorn is not a base dependency) and the app imports the shared metrics
helpers at startup. Install the `[api]` extra for uvicorn, and add `prometheus_client` + `juniper-observability`
explicitly — belt-and-suspenders across extra drift (the `[api]` extra's membership has changed between sessions;
the 2026-07-18 session installed both explicitly because that session's `[api]` did not pull them, and
`prometheus-client` lives in the separate `[observability]` extra to this day).

```bash
# CWD determines where the generator's ./data/ artifacts land — run from a scratch dir.
mkdir -p /tmp/juniper-e2e && cd /tmp/juniper-e2e
python3.14 -m venv .venv-data
source .venv-data/bin/activate
pip install -e '/home/pcalnon/Development/python/Juniper/juniper-data[api]' prometheus_client juniper-observability
# For the MNIST checks (D2 / I-5) add the [mnist] extra (pulls Hugging Face datasets[vision]):
#   pip install -e '/home/pcalnon/Development/python/Juniper/juniper-data[api,mnist]'
# PYTHON_GIL=0 matches util/isolated_stack.bash data_up — but ONLY on a free-threaded
# CPython (Py_GIL_DISABLED build): on a stock build it is FATAL at startup
# (config_read_gil). The script probes the venv interpreter and passes the toggle
# conditionally since 2026-08-09 (the host python3.14 reverted to a stock build).
PYTHON_GIL=0 python -m juniper_data --host 127.0.0.1 --port 8101   # (background it / separate shell)
```

Health gate: `curl -sf http://127.0.0.1:8101/v1/health` returns 200.

When using [`util/isolated_stack.bash`](../util/isolated_stack.bash) instead of the hand recipe: `data_up`
requires `python3.14` on `PATH` (aborts before side effects if missing), creates
`${JUNIPER_E2E_RUN_DIR:-/tmp/juniper-e2e}/.venv-data` only when absent, always re-runs the pip install above
(extras from `JUNIPER_E2E_DATA_EXTRAS`, default `api`), launches with `PYTHON_GIL=0`, writes `juniper-data.pid`,
then health-gates. Prefer `--up` / `--dry-run --up` over hand-rolling when the helper is available — see
[`docs/REFERENCE.md` Isolated Stack — `data_up`](../docs/REFERENCE.md#dedicated-data-venv-bring-up-data_up).

### 3.2 juniper-cascor on 8202 (JuniperCascor1)

```bash
conda activate JuniperCascor1
cd /home/pcalnon/Development/python/Juniper/juniper-cascor/src
LD_LIBRARY_PATH= \
  JUNIPER_DATA_URL=http://127.0.0.1:8101 \
  JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://127.0.0.1:8051 \
  uvicorn api.app:create_app --factory --host 127.0.0.1 --port 8202
```

- `LD_LIBRARY_PATH=` (emptied) neutralizes the rust_mudgeon libtorch bleed-through that otherwise shadows the
  env's torch (the same collision the JuniperCascor1/JuniperCanopy1 activate hooks strip).
- `JUNIPER_DATA_URL` points cascor's dataset fetch at the **isolated** juniper-data, not 8100.
- `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` — see §4 (the control-WS origin/allowlist pair).

Health gate: `curl -sf http://127.0.0.1:8202/v1/health` returns 200. The `create_app` factory lives at
`juniper-cascor/src/api/app.py:590`.

### 3.3 juniper-canopy on 8051 (JuniperCanopy1, service mode)

```bash
conda activate JuniperCanopy1
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
JUNIPER_CANOPY_DEMO_MODE=0 \
  JUNIPER_CANOPY_SERVER__HOST=127.0.0.1 \
  JUNIPER_CANOPY_SERVER__PORT=8051 \
  JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://127.0.0.1:8202 \
  JUNIPER_CANOPY_JUNIPER_DATA_URL=http://127.0.0.1:8101 \
  JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://127.0.0.1:8051 \
  JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS='["http://127.0.0.1:8051","http://localhost:8051"]' \
  python main.py
```

- `JUNIPER_CANOPY_CASCOR_SERVICE_URL` is the **canonical** env var (canopy `src/settings.py:497`). The bare
  `CASCOR_SERVICE_URL` still works but is the **deprecated** legacy alias (`settings.py:499-502`) — prefer the
  prefixed form, matching `util/juniper_plant_all.bash`.
- `JUNIPER_CANOPY_JUNIPER_DATA_URL` lets canopy read `/v1/generators` from the isolated juniper-data (I-5 / N7).
- `JUNIPER_CANOPY_CASCOR_WS_ORIGIN` — see §4.
- `JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS` — canopy's **own** browser-WS origin gate
  (`websocket.allowed_origins`, canopy `src/settings.py:142-147`): the default admits only
  port-**8050** origins, so off `:8050` the dashboard's own `/ws/training` + `/ws/control`
  handshakes are rejected 403 in a reconnect loop (E2E arc finding F-E2E-006). Must name the
  real canopy origin(s) as a JSON list.

Health gate: `curl -sf http://127.0.0.1:8051/v1/health` returns 200.

## 4. The control-WS origin / allowlist pair (the "403 mystery", resolved as config)

Canopy's backend opens a control WebSocket to cascor's `/ws/control`, presenting an **Origin** header. cascor
enforces an **Origin allowlist** on that endpoint. Off the default `:8050`, the two ends must be aligned or every
control-stream connect is rejected **403** and canopy's supervisor churns on a 30 s reconnect loop (hot
`set_params` then silently falls back to REST). This was wave-1's "403 mystery" — a configuration gap, not a bug.

Set **both** halves to canopy's own origin (here `http://127.0.0.1:8051`):

| End | Env var | Value | Anchor |
|-----|---------|-------|--------|
| cascor  | `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` | `http://127.0.0.1:8051` | `juniper-cascor/src/api/settings.py:496` |
| canopy  | `JUNIPER_CANOPY_CASCOR_WS_ORIGIN`           | `http://127.0.0.1:8051` | `juniper-canopy/src/settings.py:58-86` |

Why canopy needs the explicit override: its derived default is `http://{socket.gethostname()}:8050` (the
`_default_cascor_ws_origin` docstring, canopy `src/settings.py:58-86`) — correct inside docker compose
(service-name hostnames, which juniper-deploy pre-aligns), wrong for a split-host isolated stack bound off `:8050`.
Match the host token on **both** sides exactly (`127.0.0.1` vs `localhost` are distinct strings to cascor's
allowlist).

Evidence that the pair matters (and that the REST fallback is resilient without it): the 2026-07-18 addendum
recorded *"control-WS to cascor returns 403 in the split-host topology (apply's REST fallback engaged cleanly —
C3/N2 resilience visible)."* With the pair set, the WS leg connects and E-1's live census sees pings answered
(§5, C3).

## 5. Per-issue scripted checks

Each check below is a compact, copy-pasteable probe with its **expected** result and the **§13 evidence** that a
live session already confirmed it. Ports are the isolated trio (data 8101, cascor 8202, canopy 8051). Probes hit
the service that owns the surface; the full-stack rows drive canopy and observe the cascade downstream.

### D1 — generator availability map + `501`/hint + control-generator `201` (juniper-data)

```bash
# 1) Availability map — every generator carries an `available` bool.
curl -s http://127.0.0.1:8101/v1/generators | python -m json.tool
# 2) Unavailable generator (mnist WITHOUT the [mnist] extra) -> 501 + install hint, never a masked 500.
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8101/v1/datasets \
  -H 'content-type: application/json' -d '{"generator":"mnist","params":{"n_samples":16}}'
# 3) Control generator (spiral) is available -> 201.
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8101/v1/datasets \
  -H 'content-type: application/json' -d '{"generator":"spiral","params":{"n_samples":64}}'
```

**Expect**: (1) each entry `"available": true|false`; (2) `501` with detail `Generator 'mnist' is not available in
this deployment: …` (routes/datasets.py:71,167-173); (3) `201`.
**§13 evidence**: D1 → `verified` (juniper-data#220): *"availability map correct; mnist→501+install hint; spiral
control 201."*

### D2 — `[mnist]` flag-flip + real generation, 784 features (juniper-data)

Bring juniper-data up with `[api,mnist]` (§3.1), then:

```bash
# mnist now advertises available:true
curl -s http://127.0.0.1:8101/v1/generators | python -c \
  "import sys,json;[print(g['name'],g['available']) for g in json.load(sys.stdin)]"
# real HF generation -> 201; artifact carries 784 features (flattened 28x28)
curl -s -X POST http://127.0.0.1:8101/v1/datasets \
  -H 'content-type: application/json' -d '{"generator":"mnist","params":{"n_samples":512}}' | python -m json.tool
```

**Expect**: `mnist True`; a `201` create with a dataset whose feature dimension is **784** (one-hot label width 10).
**§13 evidence**: D2 → `verified` (juniper-data#221): *"[mnist] extra flips available:true; real HF generation
(784 features, 512 samples)."*

### I-5 — full-stack MNIST: stage → start → 784×10 auto-net (canopy → cascor → data)

```bash
# Stage the canopy-dialect mnist dataset onto cascor, then start training through canopy.
curl -s -X POST http://127.0.0.1:8051/api/train/start \
  -H 'content-type: application/json' -d '{"dataset":{"type":"mnist","n_samples":512}}'
# Observe cascor auto-create the 784x10 network and begin training.
curl -s http://127.0.0.1:8202/v1/network | python -m json.tool          # inputs 784, outputs 10
curl -s http://127.0.0.1:8202/v1/training/status | python -m json.tool  # status advances to running
```

**Expect**: cascor fetches the dataset from the isolated juniper-data (8101), auto-creates a **784×10** network,
and training runs to completion. Requires D2's `[mnist]` extra installed in the data venv.
**§13 evidence**: I-5 end-to-end (2026-07-18 addendum): *"canopy-dialect mnist staged on cascor → fetched from
isolated juniper-data → 784×10 network auto-created → training ran"*; D2 note: *"cascor auto-built 784×10 net and
trained."*

### C1 — null / blank / filled snapshot descriptions during a live run (cascor)

With a training run active, POST snapshot creates directly to cascor with each description shape:

```bash
curl -s -o /dev/null -w 'omitted=%{http_code}\n' -X POST http://127.0.0.1:8202/v1/snapshots \
  -H 'content-type: application/json' -d '{}'
curl -s -o /dev/null -w 'null=%{http_code}\n'    -X POST http://127.0.0.1:8202/v1/snapshots \
  -H 'content-type: application/json' -d '{"description":null}'
curl -s -o /dev/null -w 'blank=%{http_code}\n'   -X POST http://127.0.0.1:8202/v1/snapshots \
  -H 'content-type: application/json' -d '{"description":""}'
curl -s -o /dev/null -w 'filled=%{http_code}\n'  -X POST http://127.0.0.1:8202/v1/snapshots \
  -H 'content-type: application/json' -d '{"description":"e2e checkpoint"}'
```

**Expect**: all four `200` (post-C1 cascor tolerates explicit-null `description`; pre-C1 the null case 422'd).
**§13 evidence**: C1 → `verified` (juniper-cascor#397): *"null/blank/filled snapshot descriptions → 200 during a
live run."*

### C2a — applied / skipped partition + atomic `422` (cascor)

```bash
# A valid PATCH partitions into applied/skipped(reason) additively.
curl -s -X PATCH http://127.0.0.1:8202/v1/training/params \
  -H 'content-type: application/json' -d '{"learning_rate":0.05}' | python -m json.tool
# A bound violation is still atomically rejected 422 (nothing applied).
curl -s -o /dev/null -w '%{http_code}\n' -X PATCH http://127.0.0.1:8202/v1/training/params \
  -H 'content-type: application/json' -d '{"epochs_max":100000000000}'
```

**Expect**: the valid PATCH returns an `applied`/`skipped` partition on the wire (killing the old silent
`hasattr` drop); the out-of-range `epochs_max` returns `422` atomically.
**§13 evidence**: C2a → `verified` (juniper-cascor#398): *"applied/skipped partition live on the wire; atomic 422
intact."*

### C2b — bound + surface coherence (cascor)

```bash
# The two parameter surfaces must agree, and epochs_max must sit under its own PATCH ceiling.
curl -s http://127.0.0.1:8202/v1/network          | python -c "import sys,json;d=json.load(sys.stdin);print('network',{k:d.get(k) for k in ('learning_rate','max_hidden_units')})"
curl -s http://127.0.0.1:8202/v1/training/status  | python -c "import sys,json;d=json.load(sys.stdin);print('status ',{k:d.get(k) for k in ('learning_rate','max_hidden_units','epochs_max')})"
```

**Expect**: `learning_rate` / `max_hidden_units` agree across `/v1/network` and `/v1/training/status` (the
reconciled single source of truth), and `epochs_max` is a derived cap (e.g. `114000`), no longer the incoherent
`1e11` that exceeded the `le=1_000_000` PATCH ceiling.
**§13 evidence**: C2b → `merged` (juniper-cascor#400, Q1 outcome (c) — epochs_max deprecated for derived limits);
I-4 end-to-end (2026-07-18 addendum): *"C2b's derived cap epochs_max=114000 seeds /api/state with stale:false;
full-form apply with the seeded values succeeds through canopy — the evening-502 wholesale-422 class is gone."*

### C3 — idle-heartbeat `1011`-with-reason close + origin-gate `403` (cascor / cascor-client)

Non-scripted (WS-level) — use the raw-frame census from E-1 (below) or the transport counters:

```bash
# Emission summary + transport counters corroborate the heartbeat contract.
curl -s http://127.0.0.1:8202/v1/metrics | grep -iE 'ws_|control|ping|frame' | head
```

**Expect**: with the §4 origin pair MISSING, the control WS is closed with an RFC-legal `1011` **carrying a
reason** and canopy sees `403` on reconnect (config gate, not a crash); with the pair SET, pings are answered and
transport counters advance. C3 adds any-frame tolerance + a disable hatch.
**§13 evidence**: C3 → `merged` (juniper-cascor#401): *"heartbeat contract (any-frame tolerance, RFC-legal 1011
close, disable hatch) + emission summary + transport counters"*; E-1: *"pings answered per C3."*

### C4 — access-log survival + rejected-start `WARNING` (cascor)

```bash
# Start training, then confirm subsequent API calls STILL appear in the uvicorn access log.
curl -s -X POST 'http://127.0.0.1:8202/v1/training/start?reset=true' -o /dev/null
curl -s http://127.0.0.1:8202/v1/training/status -o /dev/null
# In the cascor server log: access records for the /status GET must appear AFTER training start,
# and a rejected start (e.g. start against an active run) must log at WARNING (not DEBUG).
```

**Expect**: uvicorn access records survive past `training/start` (the `disable_existing_loggers` clobber is
fixed), and a rejected start emits a `WARNING`.
**§13 evidence**: C4 → `merged` (juniper-cascor#407): *"access-log `disable_existing_loggers` fix + root-clobber
guard + WARNING on rejected starts + `test_access_log_survival.py`."*

### C5 — retain / clear / undo / `409`-finalize / start_fresh-preserves-snapshots (cascor)

```bash
# Retention-by-default: history survives across runs.
curl -s 'http://127.0.0.1:8202/v1/metrics/history?count=2' | python -m json.tool
# Explicit clear + undo (undo valid until the NEXT start).
curl -s -X POST http://127.0.0.1:8202/v1/training/metrics/clear      -o /dev/null -w 'clear=%{http_code}\n'
curl -s http://127.0.0.1:8202/v1/training/status | python -c "import sys,json;print('undo_available=',json.load(sys.stdin).get('metrics_clear_undo_available'))"
curl -s -X POST http://127.0.0.1:8202/v1/training/metrics/clear/undo -o /dev/null -w 'undo=%{http_code}\n'
# start_fresh discards the model + retained data but PRESERVES permanent artifacts (snapshots).
curl -s -X POST http://127.0.0.1:8202/v1/training/start \
  -H 'content-type: application/json' -d '{"reset":true,"start_fresh":true}' -o /dev/null -w 'fresh=%{http_code}\n'
curl -s http://127.0.0.1:8202/v1/snapshots | python -c "import sys,json;print('snapshots_after_fresh=',len(json.load(sys.stdin)))"
```

**Expect**: history retained by default; `metrics_clear_undo_available` flips true after a clear and false after
the next start; `start_fresh` resets model/metrics but the snapshot list is non-empty afterward.
**§13 evidence**: C5 → `merged` (juniper-cascor#408): *"full Q4 contract (retain-by-default, clear+undo,
snapshot-preserving start_fresh)"*; addendum: *"POST /v1/training/metrics/clear + /clear/undo (undo valid until
the next start), metrics_clear_undo_available on status, retention-by-default for GET /v1/metrics/history."*

### N2 — `/api/stream_health` healthy ×3 + `/api/state` live-first (canopy)

```bash
# Stream health should read healthy across three consecutive polls (no half-open flap).
for i in 1 2 3; do curl -s http://127.0.0.1:8051/api/stream_health | python -c "import sys,json;print(json.load(sys.stdin).get('status'))"; sleep 1; done
# /api/state base fields are live-first (derived from the per-GET cascor fetch), with an honest stale fallback.
curl -s http://127.0.0.1:8051/api/state | python -c "import sys,json;d=json.load(sys.stdin);print({k:d.get(k) for k in ('status','current_epoch','stale')})"
```

**Expect**: three healthy reads; `/api/state` reports `stale: false` with a live `status`/`current_epoch` during
a run (the relay-fed global is retained only as the demo/WS-push fallback).
**§13 evidence**: N2 → `merged`; 2026-07-14 addendum: *"StreamHealth + GET /api/stream_health + the badge's
upstream degraded-mode dimension, /api/state live-first base fields with an honest stale fallback."*

### N4 — snapshot create `201` with cascor metadata (canopy route seam)

```bash
# Blank description must NOT mint a JSON null at the route seam; create returns 201 + cascor metadata.
curl -s -X POST http://127.0.0.1:8051/api/v1/snapshots \
  -H 'content-type: application/json' -d '{}' | python -m json.tool
curl -s -X POST http://127.0.0.1:8051/api/v1/snapshots \
  -H 'content-type: application/json' -d '{"description":"named e2e snapshot"}' | python -m json.tool
```

**Expect**: `201` with the snapshot's cascor-side metadata surfaced (the route now sends `""` — never `null` —
to cascor, and forwards upstream detail verbatim on any error). **Caveat**: the 2026-07-18 pass surfaced a
service-mode `POST /api/v1/snapshots` `500` (canopy `stat()`ed a local path the adapter deliberately ignores) —
fixed in **canopy#451**; re-verify a live `201` once that is merged.
**§13 evidence**: N4 → `verified` (juniper-canopy#442): *"seam holds (cascor receives ""); detail passthrough
works; surfaced the service-mode local-stat 500 → fix canopy#451."*

### Full-stack apply (I-4) and the OPEN experiments E-1 / E-2 / E-3

- **I-4 full-form apply** (canopy `POST /api/set_params`): with C2b's derived cap seeding `/api/state`
  (`stale:false`), a full-form apply carrying the backend-seeded values succeeds through canopy — the evening-502
  wholesale-422 class is gone (2026-07-18 addendum, I-4 end-to-end).
- **E-1** (verified): raw WS client on cascor `/ws/training` during an isolated run — 245 `metrics` frames in
  100 s (every 25th epoch during output phases), `candidate_progress` in candidate phases, pings answered per C3;
  transport counters corroborate exactly. cascor **already** emits per-epoch metrics, so C6's add-emission premise
  is void and N8 can consume the existing stream.
- **E-2** (verified, cascor half): `POST /v1/training/start?reset=true` against an **active** run returns an
  immediate `409` (54 ms, no executor queueing); the staged dataset config **survives** the refusal → pins N3's
  active-run design as stop → await → start(staged).
- **E-3** (merged with N2): the pre-refresh total-freeze root cause resolved by N2's always-release of the
  apply-in-flight clamp + a client-side watchdog.

## 6. Known divergences & gotchas

- **CI-vs-local dataset numerics (the canopy#449 saga's root).** CI has **no juniper-data**, so canopy/cascor CI
  runs fall back to locally-generated datasets. Different data → different candidate correlations → runs converge
  differently than on the isolated stack. Two concrete consequences already bit: (a) CI demo runs converge to FSM
  `COMPLETED`, and START from `COMPLETED` is refused (`/api/train/start` defaults `reset=False`) — the UI harness
  needs a Reset → Start precondition; (b) the topology store handler's lazy `CascorServiceAdapter` import pulls
  `juniper_cascor_client`, absent by design in client-less installs → `ModuleNotFoundError` → silent `no_update`
  → a permanently empty Network Topology panel in demo-only installs. Do not expect CI numerics to match the
  isolated stack; the isolated stack (with real juniper-data) is the authoritative E2E surface.
- **The CI-lane extras class (CL2 / canopy#459 lessons).** Both the unit AND integration CI lanes need
  `pip install -e ".[juniper-cascor]"` — install the client-bearing extra or client-dependent tests
  `importorskip` away and run *nowhere* (e.g. canopy's 510-line `test_stream_liveness.py` was silently skipped in
  the unit job, which installs bare `-e .`). When a suite reports suspiciously few tests, check for skipped
  client-gated modules before trusting green.
- **Stale plan pointers.** The plan's old *"second `None`-description seam at `main.py:2718`"* pointer is stale —
  that region is now the layouts API. Treat as resolved-or-moved (2026-07-18 addendum).
- **0.6.0-era installed client noise.** An installed `juniper-cascor-client` below the 0.7.0 floor still emits
  `unrecognized_ws_frame` warnings; these retire with CL2's floor bump — benign on the isolated stack.

## 7. Teardown hygiene

Leave no residue and free the ports for the next run:

```bash
# 1) Kill the trio by port (no root needed) — targets ONLY the isolated ports.
for p in 8101 8202 8051; do
  pid=$(ss -tlnpH "sport = :$p" 2>/dev/null | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)
  [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
done
# (fallback) pgrep -af 'juniper_data|api.app:create_app|canopy/src/main.py'
# 2) Clean run artifacts: the data venv's ./data/ dir, logs, pidfiles under the scratch dir.
rm -rf /tmp/juniper-e2e/data /tmp/juniper-e2e/.venv-data
# 3) Clean snapshot artifacts written during the run (gitignored, but tidy up):
rm -f /home/pcalnon/Development/python/Juniper/juniper-cascor/src/snapshots/snapshot_* 2>/dev/null || true
rm -f /home/pcalnon/Development/python/Juniper/juniper-canopy/src/snapshots/snapshot_* 2>/dev/null || true
```

Confirm the ports are free: `ss -tlnH 'sport = :8101 or sport = :8202 or sport = :8051'` prints nothing.

## 8. The helper script

[`util/isolated_stack.bash`](../util/isolated_stack.bash) encodes this recipe. It is deliberately simple; the
checklist above is the primary deliverable. Surface:

```text
util/isolated_stack.bash --up        # bring the trio up (data venv + cascor + canopy) with the §3/§4 env
util/isolated_stack.bash --status    # probe the three /v1/health endpoints; list listening ports
util/isolated_stack.bash --down      # stop the trio by port and clean run + snapshot artifacts (§7)
util/isolated_stack.bash --dry-run --up   # PRINT every command without executing (safe when the ports are in use)
util/isolated_stack.bash --help
```

`--status` probes `http://127.0.0.1:<port>/v1/health` for all three services (not a separate canopy `/api/health`).
Live `cascor_up` / `canopy_up` compose (emptied `LD_LIBRARY_PATH`, Origin/allowlist pair, `DEMO_MODE=0`, pid
writes, missing-`conda.sh` abort) is pinned in
[`docs/REFERENCE.md` — Isolated Stack E2E](../docs/REFERENCE.md#isolated-stack-e2e-utilities) and covered by
`tests/test_isolated_stack_script.py` (`TestCascorUp` / `TestCanopyUp`).

Ports default to 8101 / 8202 / 8051 and are overridable via `JUNIPER_E2E_DATA_PORT` / `JUNIPER_E2E_CASCOR_PORT` /
`JUNIPER_E2E_CANOPY_PORT` (plus `JUNIPER_E2E_DATA_EXTRAS=api,mnist` for the MNIST checks and `JUNIPER_E2E_*_DIR` /
`JUNIPER_E2E_*_CONDA` path/env overrides — see the script header). Prefer `--dry-run` to preview the exact
commands before a live bring-up, and never run `--up` against ports the operator's stack already owns.

Operator contract (`data_up` dedicated venv / `PYTHON_GIL=0` / pidfile, nounset restore after conda activate,
kill-by-port `--down`, hard-coded 2s health poll / `JUNIPER_E2E_HEALTH_TIMEOUT`):
[`docs/REFERENCE.md` Isolated Stack E2E Utilities](../docs/REFERENCE.md#isolated-stack-e2e-utilities).
`--status` probes `http://127.0.0.1:<port>/v1/health` for all three services (not a separate canopy `/api/health`).

If an isolated canopy is live but Candidate Metrics / Decision Boundary / Topology stay at mount defaults, that is **F-CANOPY-027** (12-slot dash-renderer starvation, **FIXED** canopy#507/#509/#511) — not missing wiring. Do not add a new Interval. Operator probes: [`docs/REFERENCE.md` F-CANOPY-027 Poller Starvation Probes](../docs/REFERENCE.md#f-canopy-027-poller-starvation-probes).

---

*Derived from [`JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md`](JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md)
§9 (Verification Plan) and §13 addenda (2026-07-16 / 2026-07-17 / 2026-07-18); command anchors re-probed against
juniper-data, juniper-cascor, and juniper-canopy at the E1 authoring HEAD. The §13 tracker is owned by the
orchestrating session and is not modified by this checklist.*
