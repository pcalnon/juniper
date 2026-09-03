# X7 — Lane A verifier A1 (MEASUREMENT / MECHANISM DISCRIMINATION)

**Defect**: juniper-canopy stops answering HTTP entirely while its juniper-cascor backend is
unreachable; does not crash; recovers on its own when cascor returns, with no canopy restart.

**Lane**: A (measurement). Mechanism discrimination only — no fixes proposed.
**Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (juniper-ml).
**Date**: 2026-09-02, 22:50–23:03 local.

---

## 0. Version provenance (the coordinator's confound)

| Item | Value |
| --- | --- |
| juniper-canopy commit under test | **`9fbf4b8cdb9f0aee788369bc669568029b698129`** (`9fbf4b8`, canopy#562) |
| Working tree | clean (`git status --porcelain` empty) |
| Relationship to original X7 measurement | **NEWER** — X7 was measured on `b78bbbb` (canopy#561) or earlier |

**X7 REPRODUCES ON `9fbf4b8`. The defect survives canopy#562 and the confound is moot.**

I additionally checked whether #562 changed the amplifier. It did not:

- #562's `dash.no_update` identity-suppression returns **after** `response.json()`
  (`src/frontend/dashboard_manager.py`, `_update_raw_topology_store_handler`), so the self-call to
  `/api/topology` is still issued on every tick. No self-call was removed or throttled.
- #562 also changed `network-visualizer-display-mode` from `State` to `Input`, which can only
  **increase** how often that callback fires.

Classification per the coordinator's taxonomy: **(c) unrelated** — #562 neither fixes X7 nor
materially changes its trigger difficulty.

Severity is nonetheless version-dependent in one respect not tested here — see §7 residual
uncertainty on the "cascor hung" (as opposed to "cascor stopped") case.

---

## 1. Stack under test

Own isolated stack, no interference with the operator's 8050/8201 or the concurrent sessions'
8051/8053/8101/8202/8211.

```
JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_E2E_DATA_PORT=8105 JUNIPER_E2E_CASCOR_PORT=8206 JUNIPER_E2E_CANOPY_PORT=8055 \
JUNIPER_E2E_RECURRENCE_PORT=8215 JUNIPER_E2E_RUN_DIR=/tmp/juniper-x7-a1 \
JUNIPER_E2E_DATA_EXTRAS=api,equities bash util/isolated_stack.bash --up
```

Ports verified free before start; `--dry-run` run first. canopy pid 191839, cascor pid 191700
(later 209216 / 212006 / 217455 across restarts), data pid 190763. Torn down with `--down` and the
same overrides; 8055/8105/8206/8215 verified clear afterwards, all other stacks verified still
listening.

Canopy launched in **service mode** by the script (`JUNIPER_CANOPY_DEMO_MODE=0`,
`JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://127.0.0.1:8206`) — required, since demo mode would not
touch cascor at all.

---

## 2. Instrument adequacy (required)

The probe must be able to report "responsive", so that a timeout is a measurement and not a harness
artifact. With cascor **up**, every endpoint returns 200:

```
/v1/health/live    connect=0.000187 firstbyte=0.001773 code=200
/v1/health         connect=0.000201 firstbyte=0.005961 code=200
/api/health        connect=0.000195 firstbyte=0.005446 code=200
/api/status        connect=0.000173 firstbyte=0.005704 code=200
/api/state         connect=0.000193 firstbyte=0.010377 code=200
/openapi.json      connect=0.000176 firstbyte=0.081453 code=200
/docs              connect=0.000502 firstbyte=0.002259 code=200
/metrics           connect=0.000200 firstbyte=0.001722 code=404   (metrics disabled — expected)
/dashboard/        connect=0.000194 firstbyte=0.017967 code=200
/v1/health/ready   connect=0.000174 firstbyte=0.028679 code=200
```

`/v1/health` at **6.0 ms** matches the prior single measurement's 8 ms. The harness reports
`time_connect` separately from `time_starttransfer`, so a TCP-accept failure is distinguishable
from a first-byte stall.

A second adequacy control is in §5.3: a *deliberately slow but correctly offloaded* endpoint
(`/api/state`, 6 s) must NOT trip the "server is blocked" reading. It does not.

---

## 3. Reproduction

Reproduction triple, matching the prior measurement point for point:

| Phase | Prior measurement | This measurement (`9fbf4b8`) |
| --- | --- | --- |
| cascor up | `/v1/health` 200 in 8 ms | 200 in **6.06 ms** |
| cascor stopped | `curl --max-time 8` — **no response at all** | **`curl` rc=28, no response**, at concurrency N≥3 |
| cascor restarted | 200 in 6 ms, no canopy restart | 200 in **6.07 ms**, canopy never restarted |

Minimum-concurrency sweep, cascor down (each `curl --max-time 8`, the original probe's budget):

```
N=2:  req1 6.018s 200 | req2 6.018s 200 | control /v1/health/live 5.627s 200
N=3:  req1 rc=28 NO RESPONSE | req2 rc=28 | req3 rc=28
      control /v1/health/live rc=28 NO RESPONSE   <-- whole server unresponsive
N=4:  all four rc=28; control rc=28
```

The threshold is exactly **N ≥ 3**, matching the arithmetic in §5.1 (N × 3.0 s > 8 s).

---

## 4. Endpoint matrix, cascor stopped (port closed, ECONNREFUSED), NO client attached

```
/v1/health/live    connect=0.000205 firstbyte=0.001575 code=200    FAST
/v1/health         connect=0.000165 firstbyte=3.007665 code=200    3.0 s
/api/health        connect=0.000187 firstbyte=3.005499 code=200    3.0 s
/api/status        connect=0.000178 firstbyte=3.146933 code=200    3.0 s
/api/state         connect=0.000239 firstbyte=6.012765 code=200    6.0 s
/openapi.json      connect=0.000276 firstbyte=0.002261 code=200    FAST
/docs              connect=0.000190 firstbyte=0.001424 code=200    FAST
/metrics           connect=0.000169 firstbyte=0.001444 code=404    FAST
/dashboard/        connect=0.000165 firstbyte=0.004006 code=200    FAST  (a2wsgi/Dash, threadpool)
/v1/health/ready   connect=0.000186 firstbyte=3.047655 code=200    3.0 s
```

Two facts to carry forward:

1. **`connect` is 0.0002 s in every single row, in every single run of every experiment.** The TCP
   handshake always completes immediately. Every failure in this defect is a **first-byte stall**,
   never a connection-level failure.
2. Endpoints split cleanly into "touches the cascor backend" (3.0 s) and "does not" (< 5 ms) — when
   probed **one at a time**. The total-unresponsiveness symptom only appears under concurrency (§5).

---

## 5. Discrimination experiments

### 5.1 The blocking cost is urllib3 retry backoff, and it is deterministic

`juniper-cascor-client` builds its session with
`Retry(total=DEFAULT_RETRY_COUNT, backoff_factor=DEFAULT_BACKOFF_FACTOR, ...)`
(`juniper-cascor-client/juniper_cascor_client/client.py:144-176`), with
`DEFAULT_RETRY_COUNT = 3`, `DEFAULT_BACKOFF_FACTOR = 0.5`, `DEFAULT_REQUEST_TIMEOUT = 30`
(`juniper_cascor_client/constants.py:33-42`).

Against a **refused** connection each attempt fails instantly, so the entire cost is backoff sleep:
`0 + (0.5 × 2¹) + (0.5 × 2²) = 3.0 s`. Measured: 3.005–3.008 s, reproducibly, across dozens of
calls. The 30 s per-request timeout is never reached in this scenario (see §7).

### 5.2 The event loop is blocked — the decisive experiment

Hold one `/v1/health` in flight; 0.4 s later time `/v1/health/live`, which is `async def` and does
**zero** backend I/O.

```
PRE   /v1/health/live   firstbyte=0.001390 code=200
blocker1 /v1/health     firstbyte=3.008404 code=200
MID   /v1/health/live   firstbyte=2.602747 code=200     <-- 2.60 s == the blocker's remaining 2.6 s
POST  /v1/health/live   firstbyte=0.001863 code=200
```

A **single** in-flight request stalls a completely independent pure-async endpoint for exactly the
remainder of its synchronous cascor call. Scaling confirms perfect serialization:

```
8 concurrent /v1/health:
  all 8 blockers   firstbyte=24.05 s     (8 × 3.0 s — SERIALIZED, not parallel)
  MID /v1/health/live   firstbyte=23.645 s
  POST /v1/health/live  firstbyte=0.002330 s
```

### 5.3 Control — a slow but correctly-offloaded endpoint does NOT block

`/api/state` makes the *same* synchronous cascor calls but wraps them in
`await asyncio.to_thread(...)` (`src/main.py:1239`), under an explicit comment: *"Both fetches are
synchronous HTTP calls — keep them off the event loop so a slow cascor cannot stall every other
canopy route."*

```
4 concurrent /api/state:
  all 4 blockers    firstbyte=6.01 s      (2 × 3.0 s each, run in PARALLEL)
  MID /v1/health/live   firstbyte=0.002434 code=200    <-- loop stays FREE
```

This is the control that makes the whole measurement sound: same upstream, same 3 s retry cost,
same concurrency — but offloaded, so the blockers run in parallel and the event loop is untouched.
The harness therefore measures **event-loop blockage**, not "endpoint is slow".

### 5.4 Kernel-level confirmation of *where* the block is

`py-spy` was unavailable (`/proc/sys/kernel/yama/ptrace_scope = 1`; `py-spy dump` → "Permission
Denied"). I did not escalate to sudo. Instead I read the main thread's kernel wait channel directly
from `/proc` (owner-readable, no ptrace needed). The main thread (tid == pid) is the asyncio event
loop thread.

```
Under /v1/health load, cascor down — 24 consecutive samples, all:
  wchan = hrtimer_nanosleep         (a time.sleep() — urllib3's retry backoff)

At the instant the load stops:
  22:54:23.27  hrtimer_nanosleep
  22:54:23.80  ep_poll              <-- flips to the asyncio selector
  ...          ep_poll (idle)
```

An idle asyncio loop blocks in `epoll_wait` (`ep_poll`). Here the loop thread is instead sitting in
a timed sleep for the entire outage load, and returns to `ep_poll` the moment the load stops. That
is direct kernel evidence that the *event loop thread itself* is executing the blocking retry
backoff.

### 5.5 Code path

```
GET /v1/health                       src/main.py:1076   async def health_check()
  -> backend.is_training_active()                       ← called INLINE on the event loop
  -> ServiceBackend.is_training_active()                src/backend/service_backend.py:160
  -> CascorServiceAdapter.is_training_in_progress()     src/backend/cascor_service_adapter.py:1089
  -> self._client.get_training_status()                 line 1091 — SYNCHRONOUS requests call
  -> urllib3 Retry: 3 retries, 3.0 s of backoff sleep on the event loop thread
```

The same inline `backend.is_training_active()` appears in `/api/health` (`src/main.py:1050`) and in
`/v1/health/ready`'s `details` block (`src/main.py:1133`) — which is why `/v1/health/ready` costs
3.0 s even though its own dependency probes use non-blocking `httpx.AsyncClient`. **All three
health endpoints block the loop.** Its 3.0 s is not the httpx probes; it is this one call.

Other inline (loop-blocking) call sites found by census: `src/main.py:1317` (`/api/status`),
`1344` (`/api/metrics`), `1449` (`/api/dataset`), `1732` (decision boundary), `705`, `2211`, `2298`,
`2419`, `3530`. Correctly offloaded: `1239` (`/api/state`), `1360` (`/api/metrics/history`),
`1423` (`/api/topology`), `3553`, `3574`, `3615`, `4180`. **The offload was applied route-by-route
and the health routes were missed.**

### 5.6 Secondary finding — the health path bypasses the circuit breaker

`is_training_in_progress()` (line 1091) calls `self._client.get_training_status()` **directly**.
`get_training_status()` (line 1969) calls the same client method **through** `self._cb.call(...)`
with a fail-fast fallback. Prediction and result, 10 sequential requests, cascor down:

```
/api/status  (breaker-protected):  3.006  3.007  3.008  0.0024  0.0026  0.0026  0.0014  0.0027  0.0024  0.0014
/v1/health   (NOT protected):      3.008  3.005  3.005  3.008  3.005  3.007  3.007  3.008  3.007  3.006
```

`/api/status` fails fast once the breaker opens. **`/v1/health` blocks 3.0 s on 10 of 10 calls and
never fails fast** — it pays full retry cost on every request for the entire outage. Confirmed in
the canopy log:

```
22:55:39 Circuit 'cascor' opened after 5 consecutive failures
...
23:00:50 Circuit 'cascor' recovered — HALF_OPEN → CLOSED
```

(`CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5`, `RECOVERY_TIMEOUT = 60.0`, `src/canopy_constants.py:649-650`.)

So the endpoint most often polled by health-checkers and monitoring is the one endpoint with no
protection at all.

### 5.7 Browser open vs no client attached — the hard discriminator

Run both ways:

- **No client attached**: a single `curl` to `/v1/health` blocks the loop for 3.0 s. The block
  **does not require a browser.**
- **Dashboard tab open** (my own tab on 8055; the concurrent session's 8053 tab untouched and
  later verified still open), cascor killed while live — loop wait-channel sampled 40× at 0.25 s:

```
hrtimer_nanosleep ×27  (~6.75 s of CONTINUOUS loop blockage, dashboard polls alone)
then ep_poll ×13       (breaker opened; dashboard-driven paths now fail fast)
```

The dashboard polls **no** health endpoint (`dcc.Interval` at
`FAST_UPDATE_INTERVAL_MS = 1000` / `SLOW_UPDATE_INTERVAL_MS = 5000`; grep for a health path in
`dashboard_manager.py` finds only docstrings). It drives `/api/status`, `/api/metrics`,
`/api/dataset` etc. So the browser is a **transient amplifier**: it holds the loop ~100% blocked
for the first ~7 s of an outage, until the circuit breaker opens and rescues the breaker-protected
routes. The health endpoints keep blocking 3.0 s per call indefinitely regardless.

With the dashboard open, single `/v1/health` calls measured 3.0–6.0 s (one queued behind another
loop-blocking request at 6.035 s).

---

## 6. Discrimination table

| # | Candidate mechanism | Verdict | Discriminating observation |
| --- | --- | --- | --- |
| 1 | **anyio threadpool exhaustion** | **EXCLUDED** | The stalled control (`/v1/health/live`) is `async def` and never enters the threadpool, yet it stalls. A **single** in-flight request reproduces the stall (§5.2) — 1 of 40 slots. Thread count moved only 38 → 41 under load. The decisive counter-example is §5.3: 4 concurrent *threadpool* blockers on `/api/state` ran in **parallel** and left the loop at 2.4 ms — the threadpool absorbs concurrency exactly as designed. |
| 2 | **Event-loop blocking** | **CONFIRMED** | One `/v1/health` stalls an unrelated pure-async endpoint for its exact remaining duration (3.008 s blocker → 2.603 s control). N blockers serialize to N × 3.0 s (8 → 24.05 s), which is the signature of loop execution, not concurrent I/O. Kernel `wchan` on the loop thread reads `hrtimer_nanosleep` for the whole outage load and flips to `ep_poll` the instant it ends (§5.4). Code path pinned to `main.py:1076 → cascor_service_adapter.py:1091` (§5.5), and the 3.0 s cost equals the urllib3 backoff schedule exactly (§5.1). |
| 3 | **Rate limiting** | **EXCLUDED** | Zero 429s observed in any experiment — every response in every run was 200 (or the expected 404 on disabled `/metrics`). 40 rapid requests from 127.0.0.1 returned 40 × 200. Health paths are `_is_exempt` in `SecurityMiddleware` (`src/middleware.py:115`) and skip the limiter entirely. A rate limit would also produce a fast 429, not a first-byte stall. |
| 4 | **Connection / socket exhaustion** | **EXCLUDED** | `time_connect` = 0.0002 s in **every** probe of every experiment, including the ones that timed out at 8 s — the TCP handshake always completes instantly. Listen backlog 2048 with `Recv-Q 0`. During a stall: exactly **1** ESTAB connection on 8055. **Zero** sockets to the dead cascor port (refused connections retain none) — no CLOSE_WAIT/TIME_WAIT accumulation. uvicorn `limit_concurrency` unset. |
| 5 | **Something else** | **NOT NEEDED** | Mechanism 2 accounts for every observation quantitatively: the 3.0 s quantum, the N × 3.0 s serialization, the N ≥ 3 threshold for exceeding an 8 s budget, the endpoint split, the self-recovery without restart, and the kernel wait-channel flip. No residual unexplained behaviour. |

---

## 7. Supported mechanism, and what I could not determine

**Supported: mechanism 2 — event-loop blocking.**

Canopy's health endpoints are `async def` but call the **synchronous** `juniper-cascor-client`
inline on the event loop. While cascor is unreachable, each such call costs 3.0 s of urllib3 retry
backoff **executed on the loop thread**, during which canopy cannot serve *any* request — including
endpoints that touch nothing. Because the calls run on the loop they serialize, so N concurrent
health requests cost N × 3.0 s, and N ≥ 3 exceeds an 8 s probe budget, producing "no response at
all". Nothing is leaked or corrupted, so service resumes the moment cascor answers again — hence
recovery with no restart.

The earlier threadpool-exhaustion hypothesis is **refuted**, and for a sharper reason than "the
health endpoint is async": the threadpool is demonstrably *healthy* under the same load (§5.3).

### Residual uncertainty (explicitly not determined)

1. **The "cascor hung" case was not measured — and it is probably much worse.** Every measurement
   here used a *stopped* cascor (port closed → ECONNREFUSED → instant per-attempt failure → 3.0 s
   total). If cascor were instead **hung** (port open but not replying — SIGSTOP, a wedged worker,
   a firewall DROP, a dead remote host), each attempt would run to
   `DEFAULT_REQUEST_TIMEOUT = 30 s`, giving up to **~120 s of event-loop blockage per request**
   instead of 3.0 s. I did not test this. Severity in that regime is untested and plausibly
   catastrophic. **This is the single biggest gap in my measurement.**
2. **No Python-level stack trace.** `ptrace_scope = 1` blocked `py-spy`; I did not escalate to
   sudo. The `wchan` evidence pins the blocking to the loop *thread* at kernel level but does not
   name the Python frame. The frame attribution rests on the code path (§5.5) plus the exact
   3.0 s == urllib3-backoff arithmetic (§5.1) plus the `/api/state` control (§5.3). I consider this
   jointly conclusive but it is inferential, not a captured stack.
3. **The original X7 run's exact concurrency is unknown.** I demonstrated N ≥ 3 is sufficient, and
   that an open dashboard alone produces ~6.75 s of continuous blockage; I cannot say which applied
   in the original observation.
4. **The WS relay's contribution was not isolated.** `cascor_service_adapter.py` runs an async
   auto-reconnect relay (`_connect_loop`, `_relay_loop`). It appeared not to block the loop — the
   loop reads `ep_poll` when no HTTP request is in flight even with cascor down — but I did not
   measure it directly.
5. **Only loopback/refused was exercised.** DNS-resolution stalls and non-loopback connect timeouts
   (the Docker/`juniper-deploy` topology) were not tested; both would land in the §7.1 regime.

---

## 8. Artifacts

Probe harnesses (repo convention: ad-hoc scripts live under `util/ad-hoc/`) — written to the
session worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/wondrous-spinning-piglet/util/ad-hoc/`:

- `2026-09-02_x7_probe_matrix.bash` — endpoint matrix with connect / first-byte / status split
- `2026-09-02_x7_concurrency_discriminator.bash` — N blockers + pure-async control
- `2026-09-02_x7_blocker_path_control.bash` — same, blocker path parameterised (the §5.3 control)
- `2026-09-02_x7_breaker_asymmetry.bash` — protected vs unprotected path
- `2026-09-02_x7_minimum_concurrency.bash` — N ≥ 3 threshold at an 8 s budget
- `2026-09-02_x7_cascor_restart.bash` — restart only the cascor leg

Raw measurement output was under `/tmp/juniper-x7-a1/` (`probe_baseline.txt`,
`probe_down_nobrowser_1.txt`, `disc_n1.txt`, `disc_n8.txt`, `control_api_state.txt`,
`breaker_asymmetry.txt`, `min_concurrency.txt`, `probe_recovery_final.txt`); all values are
transcribed inline above, as the run dir is transient.
