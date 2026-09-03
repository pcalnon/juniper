# X7 Lane B2 — adversarial review of PR 1 (juniper-canopy event-loop blocking)

Reviewer: Lane B adversarial (B2). Mandate: refute the **implementation**, not the scope.
Repo inspected read-only at `/home/pcalnon/Development/python/Juniper/juniper-canopy` @ `9fbf4b8`.
Measurements run under `conda run -n JuniperCanopy1` (Python 3.13, urllib3 2.7.0, requests 2.34.2,
juniper-cascor-client 0.7.0, juniper-data-client 0.4.1). No repository file was modified. No service
on 8050/8201/8051/8101/8202/8211 was touched — every measurement used ephemeral loopback ports.

Measurement scripts (scratchpad, not repo): `retry_probe.py`, `exec_saturation2.py`,
`exec_saturation3.py`, `swap_race.py`, `scan_handlers.py`.

---

## 0. Blockers (must be resolved before PR 1 ships)

### B1 — Step 1 cannot express a correct retry policy, and every value it can express trades one hazard for another

`juniper-cascor-client` 0.7.0 `client.py:89-95` builds
`Retry(total=retries, backoff_factor=0.5, status_forcelist=RETRYABLE_STATUS_CODES, allowed_methods=RETRY_ALLOWED_METHODS)`
with `constants.py:36-37`:

```
RETRYABLE_STATUS_CODES = [429, 502, 503, 504]
RETRY_ALLOWED_METHODS  = ["GET", "POST", "DELETE", "PUT", "PATCH"]
```

Measured against a stub that counts server-side attempts (`retry_probe.py`, timeout=1, retries=3):

| scenario | GET attempts | POST attempts | wall |
|---|---|---|---|
| upstream hangs (read timeout) | 4 | **4** | 7.01 s |
| upstream 503 | 4 | **4** | 3.05 s |
| upstream 500 | 1 | 1 | 0.00 s |
| hang, `retries=0` | 1 | 1 | 1.00 s |

So a timed-out `POST /v1/training/start` really does reach cascor **four times**. Consequences the
plan does not address:

- **Reducing `retries` 3 → 1 still permits 2 duplicate training starts.** The count is the wrong
  lever; the hazard lives in `allowed_methods`, which `JuniperCascorClient.__init__` does not expose.
- **`retries=0` also disables connect-error retries** — the only genuinely safe class, because the
  request never left the client (`urllib3/util/retry.py` `increment()`: connect errors are governed by
  `connect`, which falls back to `total`; read errors are retried only when `_is_method_retryable`).
- The sibling client already has the right answer: `juniper_data_client.constants.RETRY_ALLOWED_METHODS
  = ['HEAD', 'GET', 'PUT']` — **POST excluded**. `juniper-cascor-client` is the ecosystem outlier.

**Required change to step 1.** Either (a) fix `juniper-cascor-client` to split connect/read/status
retries and drop non-idempotent verbs from `allowed_methods` (aligning it with juniper-data-client),
or (b) have canopy build the `JuniperCascorClient`, mount its own `HTTPAdapter(max_retries=Retry(
connect=2, read=0, status=0, ...))`, and inject it via the already-supported
`CascorServiceAdapter(client=...)` parameter (`cascor_service_adapter.py:494`). Passing a bare
`retries=` at `cascor_service_adapter.py:507` cannot fix both hazards.

**Second half of step 1 — `timeout` — is also under-specified.** `client.py:363` passes
`timeout=self.timeout` on *every* request; there is no per-call override. A short global timeout
therefore also applies to `create_network`, `save_snapshot`, `load_snapshot`, `stage_dataset` and
`update_params`. The PR must state the value and justify it against the slowest legitimate call, not
only against the health path.

**Arithmetic corroboration of the reported outage.** urllib3 backoff is `factor * 2**(n-1)` with the
first retry at 0 → sleeps `0, 1.0, 2.0` = 3.0 s total (measured: attempts at t=0, 1.005, 3.006,
6.011 with timeout=1). With the defaults `timeout=30, retries=3`: `4 × 30 + 3 = 123.0 s`, which matches
the measured **123.12 s** hang to within jitter. The mechanism is confirmed, not merely plausible.

### B2 — Step 2 deletes the system's only back-pressure and amplifies load on the failing upstream ~14×

Replica of canopy's real loading (`exec_saturation3.py`): `/api/status` polled at 1 Hz (fast lane) plus
0.2 Hz (slow lane), client-side give-up at 1 s / 2 s (`DashboardConstants.FAST_API_TIMEOUT_SECONDS = 1.0`,
`API_TIMEOUT_SECONDS = 2`), inbound concurrency capped at 10 (a2wsgi's `ThreadPoolExecutor(max_workers=10)`
default — canopy mounts Dash with `app.mount("/dashboard", WSGIMiddleware(...))` at `main.py:493` and
passes no `workers=`), upstream hung, per-call block 20 s, 40 s run:

| | inline (today) | `to_thread` (PR 1) |
|---|---|---|
| `/ctl` pure-async probes completed | 5, **4 timed out at 10 s** | 158, **0 timed out**, p50 3.8 ms / p95 6.7 ms |
| upstream HTTP requests issued | **3** | **42** |
| executor threads peak-live | 1 | **20 / 20 — fully saturated** |
| occupancy mean | 1.0 | 16.2 |
| accepted-but-never-started backlog | 45 (in the loop) | 6 (in the executor queue) |

Three findings:

1. **The executor does saturate, at a block time well below the current defaults.** Default executor is
   `min(32, cpu_count+4)` — measured **20** on this 16-core box; on a 4-vCPU GitHub runner it is 8.
   Saturation threshold is `block_time > pool_size / arrival_rate` ≈ `20 / 1.2 ≈ 16.7 s` for **one**
   browser tab; ~8 s for two; ~4 s for four. So `timeout=5, retries=3` (23 s) saturates, and
   `timeout=30, retries=0` (30 s) saturates. Only a total budget of roughly **≤5 s** leaves real
   headroom — measured at `timeout=5, retries=0` the peak was 8/20 with p95 6.3 ms.
2. **Yes, it is a regression in one specific respect**: a blocked event loop is an accidental rate
   limiter. Offloading raises upstream request volume from 3 to 42 per 40 s — and with the client's
   default `retries=3` that is 168 HTTP attempts (~4.2/s) hammering a cascor that is already sick.
   Because the client retries POSTs, any control command caught in the storm is duplicated too. The
   adapter's `DEFAULT_POOL_MAXSIZE = 10` is exceeded (42 concurrent sockets observed), so urllib3
   churns and discards connections on top of that.
3. The saturated pool is **shared** with the ~30 `asyncio.to_thread` sites main.py already has —
   `/api/topology`, `/api/topology/raw`, `/api/metrics/history`, `/api/state`, the snapshot family, and
   the entire `/ws/control` command lane. PR 1 adds five more consumers to an unbudgeted pool.

**Required change to step 2.** Ship the offload *with* a concurrency budget: a module-level
`asyncio.Semaphore` (or a dedicated small `ThreadPoolExecutor` reserved for upstream calls) sized from
the poll arithmetic, plus a stated `timeout × (retries+1) + backoff` budget. Without it, PR 1 converts
a canopy-local outage into a cascor-amplification event and merely relocates the failure.

**Does `src/health.py:15-27` invalidate step 2?** No — but its stated arithmetic is wrong in the
*conservative* direction, which strengthens B2. It says the pool is "32 worker threads"; it is 20 here
and 8 on CI. The precedent is about *fan-out of independent probes*, and canopy plainly has not adopted
"never `to_thread`" as policy (~30 live call sites). The correct reading is: **the thread pool is a
shared, small, unbudgeted resource** — which is exactly the objection above, not a veto on the
technique.

### B3 — Step 3's TTL cache is a no-op for the caller it exists to protect, if it is lazily refreshed

Probe cadence and budget, measured from the deploy config:

- `juniper-deploy/docker-compose.yml:58-62` (`x-healthcheck-canopy`): `interval: ${HEALTHCHECK_INTERVAL:-15s}`,
  `timeout: 10s`, `retries: 5`; the canopy services' `test:` (lines 731-732, 813-814) is
  `urllib.request.urlopen('http://localhost:8050/v1/health', timeout=5)` — the **effective per-probe
  budget is 5 s**, not the docker `timeout: 10s`.
- `juniper-canopy/Dockerfile:107-108`: `--interval=30s --timeout=10s --retries=3`, command
  `curl --fail --silent --max-time 5 …/v1/health` — again a **5 s** budget.

A lazily-refreshed TTL cache pays the full upstream cost on the first request after expiry. With
TTL ≤ 10 s (anything larger makes `training_active` dishonest against a 1 Hz UI), TTL < probe interval
(15 s / 30 s) always holds, so **every single container healthcheck pays the refresh**. The cache
removes exactly zero of the worst cases for the probe that decides container liveness. The plan does
not say which discipline it uses; as written this is the likeliest reading and it is a no-op.

Also: even a *bounded* inline refresh must complete inside the 5 s probe budget, which couples step 3
to step 1 — `timeout=3, retries=1` (6 s) already breaches it. The plan states no such coupling.

**Two correct designs, in preference order.**
1. **Serve `training_active` from the relay-fed `training_state` global plus the existing in-memory
   relay liveness** (`CascorServiceAdapter.get_stream_health()`, used by `/api/stream_health` at
   `main.py:1321`, which makes no upstream call). Zero upstream calls, no cold-start penalty. The known
   objection — the relay-fed global went ~8 h stale when the WS relay died silently (recorded at
   `main.py:1225-1232`) — is answerable by emitting the relay's own staleness alongside it, which is
   precisely what `get_stream_health()` already computes.
2. A **background refresher** — but then it needs a lifespan start/stop, cancellation on shutdown, and
   cancellation/rebinding on `_swap_backend` (`main.py:3722`), none of which the plan mentions. Precedent
   exists (`start_metrics_relay` / `stop_metrics_relay`, `_relay_summary_task`).

**Where it must not live:** a module-global cache in `main.py` keyed on nothing survives the backend
swap and would serve cascor's `training_active` after a swap to the recurrence backend.

---

## 1. Attack item 1 — does bounding retries break correctness?

**Verdict: bounding `retries` is net *safer*, but the proposed knob is the wrong one (see B1).**

- **(a) Safer or riskier?** *Safer.* The write hazard is real and measured (4× `POST /training/start`),
  and duplicates are semantically loaded here: cascor 409s a start against an active run and
  `start_fresh` triggers a rebuild, so a duplicate is not idempotent. The read-side loss is small:
  **HTTP 500 is not retried today** (measured: 1 attempt, immediate `JuniperCascorClientError`), so
  only 429/502/503/504 lose protection, and cascor restarts under compose surface as *connect* errors —
  a different retry class that a correct fix keeps.
- **(b) Callers relying on retry to paper over flakiness?** None found that documents such a dependence.
  The paths where a duplicate is strictly worse than a failure are `/api/train/restart`
  (`main.py:3588`, stop → await-stopped → start, with the E-2 pin that a start against an ACTIVE run
  409s) and `/api/v1/snapshots/{id}/restore` (`main.py:2455`, load → apply_params → reset). Both are
  POST chains, both currently retryable.
- **(c) Exact retry semantics** (`urllib3 2.7.0`, read from
  `/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/urllib3/util/retry.py`):
  - connect errors → `connect` counter (unset → falls back to `total`); retried for **every** method;
  - read errors, including read timeouts → retried **only if the method is in `allowed_methods`**
    (`increment()` → `_is_method_retryable`), i.e. POST/PUT/PATCH/DELETE **are** retried here;
  - status responses → retried only for `status_forcelist = [429, 502, 503, 504]` and only for allowed
    methods; `raise_on_status=True`, `respect_retry_after_header=True`, `backoff_jitter=0.0`,
    `backoff_max=120`.

---

## 2. Attack item 2 — executor saturation

**Verdict: the concern is confirmed by measurement and PR 1 as written is insufficient.** See B2 for
the numbers. Summary of the per-item questions:

- **Steady state with cascor hung and bounded timeouts:** occupancy = arrival_rate × block_time, capped
  at 20. `/api/status` alone arrives at **1.2/s per browser tab** (1 Hz fast lane via
  `update_unified_status_bar` → `_update_unified_status_bar_handler` → `dashboard_manager.py:6294`,
  plus 0.2 Hz via `update_system_panels` → `dashboard_manager.py:6543`). Client-side give-up at 1-2 s
  does **not** release the executor slot — `asyncio.to_thread` is uncancellable — so occupancy is set by
  the arrival rate, not the completion rate. That is the saturation mechanism.
- **The 5 s lane really does make three sequential self-calls per tick**: `/api/status`
  (`dashboard_manager.py:6543`), then `_update_network_info_details_handler` → `/api/network/stats`
  (`:6676`), then `_update_stream_health_handler` → `/api/state` (`:7835`). All are loopback self-calls
  into the same uvicorn process, sent with `internal_api_headers()` which is **rate-limit exempt**
  (`src/frontend/internal_api.py:63-79`) — nothing throttles them during an outage.
- **"Quieter failure — is that a regression?"** Partly yes. Liveness stays green while every data route
  stalls *and* upstream load rises 14×. It is a better failure than a dead process, but it is not a
  strictly-dominant one, and it is only acceptable with an explicit concurrency bound.

---

## 3. Attack item 3 — TTL cache correctness

**Verdict: under-specified in the plan, and the likeliest reading is a no-op.** See B3.
Correct TTL from the probe intervals: there is no TTL that both (i) keeps `training_active` honest
against a 1 Hz UI and (ii) spares the 15 s / 30 s container probe — the constraint is unsatisfiable by
a lazy cache, which is why the answer is a background refresher or the relay-fed global.

One further hazard: the failure value. `is_training_in_progress` (`cascor_service_adapter.py:1089-1100`)
swallows every `JuniperCascorClientError` and returns `False`. A cache that stores that value will
serve **`training_active: false` during a real training run** for a full TTL — a silent wrong answer,
not merely a stale one. The cache must distinguish "known false" from "unknown".

---

## 4. Attack item 4 — will the guard test fail today and pass after?

**Verdict: yes, and with a very large margin — but the realistic failure mode is vacuity, not flake.**

- **Separation is ~3 orders of magnitude.** Measured with a 20 s block: inline → 4 of 5 control probes
  time out at 10 s; offload → p95 **6.7 ms**. A 500 ms threshold sits 75× above the passing value and
  ~20× below the failing one. CI-load flake is a weak objection at that separation.
- **Vacuity traps, in order of likelihood.**
  1. Building a throwaway FastAPI app in the test — then main.py's handler is never exercised and the
     test passes forever. It must import `main.app` and monkeypatch `main.backend`.
  2. Stubbing with something that *yields* — `time.sleep` releases the GIL, so a stub that is not a
     genuinely blocking sync call lets a **pre-fix** handler pass too. The stub must block the calling
     thread in a way that would block the loop when called inline.
  3. Choosing a control endpoint that itself touches the backend. `/health` (`main.py:1030`),
     `/v1/health` (`:1057`) and `/v1/health/ready` (`:1094`) all call `backend.is_training_active()`.
     **`/v1/health/live` (`main.py:1088`) is the only pure-async control route** and is the right probe.
- **Better than a wall-clock threshold:** a **ratio** assertion — count how many `/v1/health/live`
  responses complete while one `/api/status` is in flight. Today: 0-1. After: ≥N. CI speed cancels out.
  An event-loop-lag heartbeat (`asyncio.sleep(0)` in a loop, assert max delta) is equally clock-free and
  is the better instrument if the test is to cover more than one route.
- **Real hang risk, not flake risk.** `pyproject.toml [tool.pytest.ini_options]` sets `timeout = 60`
  with `timeout_method = "signal"`; SIGALRM is delivered to the **main** thread only, so an offloaded
  worker still blocked on the stub survives the timeout, and `ThreadPoolExecutor` threads are joined at
  interpreter exit. I hit exactly this: a 123 s-block run would not exit and had to be SIGKILLed. Size
  the stub's block to ~1-2 s and settle it explicitly, or the test can hang the whole session rather
  than fail one case. `filterwarnings = ["error::RuntimeWarning", ...]` also promotes stray runtime
  warnings to failures.
- **Coverage gates.** `.github/workflows/ci.yml:255-261` runs a blocking
  `juniper-coverage-gap-map --enforce` (per-file ≥90%, pooled ≥95% per packaged sub-module) over
  `reports/coverage.json`, which is produced **only** by the unit lane
  (`pytest -m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/`).
  Consequences: the guard test must live under `unit/` or `regression/` and must **not** be marked
  `slow`, or it contributes zero coverage while its production code still needs covering. main.py has
  **1865 statements** (1% = 18.6), so step 2's ~5-10 added statements are noise. The genuine gate risk
  is a **new small module** for step 3: a 40-statement cache file needs ≥36 statements covered, and its
  expiry / lock-contention / task-cancellation arms are exactly the ones tests skip. Prefer putting the
  cache in an already-covered module, or budget tests for every arm.

---

## 5. Attack item 5 — what PR 1 misses

AST scan of `src/main.py` (`scan_handlers.py`): **71 routes, 34 with inline blocking `backend.*` calls.**
PR 1 offloads 5 → **~29 remain.** The outage can still occur through every one of them.

| Path still blocking after PR 1 | Evidence | Can the outage occur through it? |
|---|---|---|
| `/api/train/status` (`main.py:3524`) | `backend.get_status()` inline; polled by `dashboard_manager.py:2287` | **Yes** — same 123 s path as `/api/status` |
| `/api/metrics` (`:1338`) | `backend.get_metrics()` inline | Yes |
| `/api/v1/workers/{stats,list}` (`:3197`, `:3235`) | `backend._adapter._client.*` inline — bypasses the adapter *and* the breaker; polled by `tabpoll-workers` at 5 s | Yes |
| `/api/train/{start,pause,resume,stop,reset}` (`:3408`-`:3503`) | inline control calls | Yes, and these are the POST-duplication paths |
| `/api/model/select` → `_swap_backend` (`:3706`) | `backend.is_training_active()` inline | Yes — and see item 6, the gate **fails open** |
| snapshot restore/replay/resume/retrain (`:2455`-`:2815`) | inline `is_training_active` / `load_snapshot` | Yes |
| `/api/remote/*` (`:4228`-`:4323`) | inline adapter calls | Yes |
| `/api/dataset` (`:1443`), `/api/dataset/generate` (`:1456`), `/api/dataset/import-file` (`:1512`), `/api/decision_boundary` (`:1723`) | inline | Yes |
| `/ws/training` (`main.py:705`) | `backend.get_status()` inline **on every connection accept** | Yes — a new dashboard tab can block the loop |

**Second breaker bypass — and 38 more.** The adapter has **45 direct `self._client.*` call sites and
only 5 `_cb.call(...)` wrappers**. The health path is one of the bypasses:
`is_training_in_progress` (`cascor_service_adapter.py:1089-1100`, reached from `/health`, `/v1/health`,
`/v1/health/ready` via `ServiceBackend.is_training_active` at `service_backend.py:160-161`) calls the
client directly, so no amount of breaker tripping ever protects the health endpoints. The one named in
the brief (`_ServiceTrainingMonitor.is_training`, `:436-447`) is a second copy of the same body with a
*wider* `except Exception`. **Even the breakered path is weak**: `failure_threshold = 5`
(`canopy_constants.py:649`) × 123 s = **615 s** before it opens, and `CircuitBreaker.call`
(`src/backend/circuit_breaker.py`) has **no half-open concurrency token** — it reads `state`, sees
HALF_OPEN, and proceeds, so every concurrent caller is admitted for a full block-time after each 60 s
`recovery_timeout` before one of them records the failure that re-opens it.

**`/ws/control` is already offloaded — and shows the flaw PR 1 would replicate.** `main.py:964-974`
does `asyncio.wait_for(asyncio.to_thread(_execute_command, ...), timeout=_command_timeout(cmd))` with
`ws_control_start_timeout = 10.0`, `ws_control_stop_timeout = 2.0`, `ws_control_set_params_timeout = 1.0`
(`src/settings.py:350-352`). `wait_for` cancels the **await**, never the thread: the browser is told the
stop timed out after 2 s while the command keeps running for another ~121 s, still holding its executor
slot, and — because POST is retryable — possibly landing up to four times. This is a shipped instance of
the anti-pattern, and it is the reason step 2 needs a bound rather than a copy.

**`juniper_data` is NOT bounded.** `JuniperDataClient` is constructed at `src/demo_mode.py:918` and
`:1829` with **no `timeout`/`retries` override** → `timeout=30, retries=3, backoff_factor=0.5`, i.e. the
same 123 s worst case, reached from the inline-blocking `/api/dataset/generate` and
`/api/dataset/import-file`. Its retry list is safer (`['HEAD','GET','PUT']` — POST excluded) but its
`RETRYABLE_STATUS_CODES` includes **500**. **The outage can occur through juniper-data and PR 1 does not
touch it.** Two juniper-data paths are already safe: `/api/dataset/generators` (`main.py:1691`) uses a
native-async `httpx.AsyncClient(timeout=5.0)`, and `juniper_data_available` is a startup-probed module
global, not a live call.

**One more, unrelated to cascor:** `/v1/health/ready` (`main.py:1101-1107`) awaits two
`probe_dependency` calls **sequentially** at 5 s each — up to 10 s even after `training_active` is fixed.
Gather them.

---

## 6. Attack item 6 — hot-swap × offload concurrency

**Transport race: REFUTED by measurement.** `swap_race.py` closes the `JuniperCascorClient` session
1 s into a 4 s in-flight request (modelling `await old_backend.shutdown()` →
`CascorServiceAdapter.shutdown()` at `:2484-2490` → `Session.close()`): the in-flight call **completed
normally** (wall 4.00 s) and a subsequent call on the closed session **also completed**.
`requests.Session.close()` only clears idle pooled connections. So offloading does not introduce a
transport-level crash on swap. State that honestly; it is the plausible objection that does not hold.

**Semantic race: REAL and NEW.** Today `/health`, `/v1/health`, `/api/status` and `/api/network/stats`
contain **no `await` between reading the `backend` global and returning**, and `_swap_backend`
(`main.py:3697-3727`) can only advance at its own awaits — so today a request sees fully-old or
fully-new state, atomically. `await asyncio.to_thread(backend.get_status)` binds the old backend, then
yields; the swap can complete underneath (reassign at `:3722`, `_seed_training_state`,
`set_demo_mode_active`, `await old_backend.shutdown()`), and the handler then reports **old-backend**
state after `/api/model/select` has already returned `swapped: true`. Nothing guards this — no lock, no
generation counter. Offloading genuinely weakens an invariant that blocking-on-the-loop was providing
for free. Mitigation is cheap: capture a generation counter with the backend reference and discard (or
re-run) the result if it changed.

**Independent defect found while checking this.** `_swap_backend`'s gate is
`if backend.is_training_active(): raise HTTPException(409, ...)` (`main.py:3710`). That call is
(i) **inline-blocking** — 123 s on a hung cascor, and it is not on PR 1's list — and (ii)
**fail-open**: `is_training_in_progress` returns `False` on any client error, so during an outage the
"refuse to switch models while training is active" guard silently permits the swap. Also note
`_swap_backend` is not covered by step 2 at all.

---

## 7. Summary of required changes

1. Fix the retry policy where it lives — `juniper-cascor-client`'s `allowed_methods` / split
   connect-read-status counters — or inject a canopy-built client through
   `CascorServiceAdapter(client=...)`. A bare `retries=` at `:507` cannot be correct.
2. State the numeric budget `timeout × (retries+1) + backoff` and justify it against the 5 s container
   probe budget and the 1.2 req/s-per-tab poll arithmetic; it must land at roughly ≤5 s.
3. Add a concurrency bound (semaphore or dedicated executor) to the offload, or step 2 trades an
   event-loop outage for pool exhaustion plus a 14× upstream amplification.
4. Replace the lazy TTL cache with the relay-fed global + `get_stream_health()` staleness, or specify a
   background refresher with lifespan and swap-time cancellation. Do not cache the swallowed `False`.
5. Extend the offload to the polled routes PR 1 misses — at minimum `/api/train/status`,
   `/api/v1/workers/{stats,list}`, `/api/metrics`, `/ws/training`'s accept-time `get_status`, and
   `_swap_backend`'s gate — or state explicitly that the outage remains reachable through them.
6. Bound the `JuniperDataClient` constructions at `demo_mode.py:918` and `:1829`.
7. Make the guard test a ratio/lag assertion against `main.app` with `/v1/health/live` as the control
   probe, in `src/tests/regression/`, unmarked-`slow`, with a ≤2 s stub block.
