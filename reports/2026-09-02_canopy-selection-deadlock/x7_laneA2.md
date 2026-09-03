# X7 — Lane A2 (MEASUREMENT by static analysis)

**Defect**: juniper-canopy stops answering HTTP entirely — `GET /v1/health` included —
while juniper-cascor is unreachable. No crash; recovers unaided when cascor returns.

**Lane**: static analysis of code + installed library source. The service was **not** run.
The only dynamic work is a standalone `requests`/`urllib3` timing probe against a closed
loopback port and a black-holed TEST-NET address (§5.4) — that exercises the HTTP client
library only and contacts no Juniper service.

**Commit analysed**: `9fbf4b8cdb9f0aee788369bc669568029b698129`
(canopy#562, 2026-09-02 19:43:33 -0500, "fix(F-CANOPY-040 residual, F-CANOPY-043)…").
Primary checkout HEAD was **not** changed; the historical comparison in §8 uses
`git diff b78bbbb 9fbf4b8`.

**Installed versions** (`JuniperCanopy1`, Python 3.13):
uvicorn **0.49.0** · a2wsgi **1.10.10** · starlette **1.3.1** · anyio **4.14.2** ·
fastapi **0.137.0** · dash **4.2.0** · requests **2.34.2** · urllib3 **2.7.0** ·
flask 3.1.3 · h11 0.16.0 · juniper-cascor-client **0.7.0** · gunicorn **not installed**.

---

## Verdict up front

The hang is **not** threadpool exhaustion. It is **event-loop blocking**.

Every one of canopy's 72 HTTP/WS route handlers is `async def`, and **41 of them call
`backend.*` synchronously without an `asyncio.to_thread` hop** — including
`/v1/health` itself. With `workers=1` and one event loop, a single such call blocks
the entire process for the duration of one cascor HTTP round trip, which is
**3.0 s** when cascor refuses connections and **123 s** when its SYNs are dropped.

`/v1/health` is `async def`, but at `src/main.py:1076` it evaluates
`backend.is_training_active()` — a blocking HTTP call to cascor that is **not**
protected by the circuit breaker its sibling `get_training_status()` uses.

---

## 1. The server stack

### 1.1 Entry point

`src/main.py:4419`:

```python
uvicorn.run(app, host=host, port=port, log_level="info" if debug else "warning")
```

Host/port come from `settings.server` (`src/settings.py:121-122`: `host="127.0.0.1"`,
`port=8050`). **No other uvicorn parameter is passed**, so every concurrency-relevant
setting is the library default.

### 1.2 Effective uvicorn settings (uvicorn 0.49.0, `uvicorn/config.py`)

| Setting | Value | Evidence | Consequence |
|---|---|---|---|
| `workers` | **1** | `config.py:255` `self.workers = workers or 1` | One process, one event loop. No parallelism across requests. |
| `limit_concurrency` | **None** | `config.py:260`; enforcement at `protocols/http/httptools_impl.py:266-272` is guarded by `if self.limit_concurrency is not None` | **No 503 load-shedding.** Requests are never rejected for concurrency; they queue forever. |
| `backlog` | **2048** | `config.py:215` | The kernel accept queue absorbs 2048 pending connections before refusing. Clients see a hang, not a refusal. |
| `timeout_keep_alive` | **5** | `config.py:216` | Idle keep-alive only. Does **not** bound request processing. |
| `timeout_graceful_shutdown` | **None** | `config.py:218` | — |
| `limit_max_requests` | **None** | `config.py:261` | No worker recycling. |

`uvicorn.run` is passed an **app instance**, not an import string, so even a
`workers>1` request would be ignored — but none is made.

**There is no request-processing timeout anywhere in uvicorn.** A blocked handler
blocks indefinitely, and the process recovers only when the blocking call itself
returns. That is exactly the observed "recovers unaided when cascor returns".

### 1.3 Middleware stack (`src/main.py:411-467`, Starlette LIFO — last added is outermost)

`RequestIdMiddleware` (outermost) → `PrometheusMiddleware` → `SessionMiddleware` →
`SecurityMiddleware` → `SecurityHeadersMiddleware` → `RequestBodyLimitMiddleware` →
`CORSMiddleware` (only if `settings.cors_origins`) → router.

`SecurityMiddleware` is a `BaseHTTPMiddleware` (`src/middleware.py:75`) with an
`async def dispatch` (`:99`). It performs no blocking I/O.

---

## 2. How Dash is mounted — a2wsgi has its **own** executor

`src/main.py:57`: `from a2wsgi import WSGIMiddleware`
`src/main.py:493`: `app.mount("/dashboard", WSGIMiddleware(dashboard_manager.app.server))`

**No `workers=` argument is supplied**, so the default applies.

### 2.1 What a2wsgi actually does (installed source, a2wsgi 1.10.10)

`site-packages/a2wsgi/wsgi.py`:

```python
153  def __init__(self, app: WSGIApp, workers: int = 10, send_queue_size: int = 10) -> None:
158      self.executor = ThreadPoolExecutor(thread_name_prefix="WSGI", max_workers=workers)
```

```python
200      await self.loop.run_in_executor(self.executor, func, environ, self.start_response)
```

**Answer to the brief's question**: a2wsgi does **not** use `anyio.to_thread.run_sync`
and does **not** use starlette's threadpool. It creates its **own private
`concurrent.futures.ThreadPoolExecutor`** and dispatches via
`loop.run_in_executor(self.executor, …)`.

- **Concurrency limit: 10 threads.** (`wsgi.py:154`, default `workers=10`.)
- **Is it configurable?** Yes — `WSGIMiddleware(app, workers=N)`. Canopy does not set it
  (`main.py:493`), so **10** is in force.
- Overflow does **not** block the event loop: `run_in_executor` returns a future that the
  coroutine awaits; excess work queues in the executor's unbounded work queue.
- The executor is created **per `WSGIMiddleware` instance** (one here), not per request.
  `WSGIResponder` is per request but shares the executor (`wsgi.py:164`).

### 2.2 The reverse coupling — WSGI threads block on the event loop

This is load-bearing for §9. `wsgi.py:215-219`:

```python
def send(self, message):
    future = asyncio.run_coroutine_threadsafe(self.send_queue.put(message), loop=self.loop)
    future.result()                 # <-- no timeout
```

`start_response` (`:244`) and every body chunk (`:259`, `:263`) go through `send()`.
`Body._receive_more_data` (`:29-30`) does the same for request bodies.

`future.result()` has **no timeout**. So when the event loop is blocked, **every WSGI
thread that finishes its work parks indefinitely trying to hand the response back**.
All 10 threads eventually park, and `/dashboard/*` — including static assets — stops
responding too. The `requests` timeouts inside the Dash callbacks (1–5 s) do **not**
rescue this: they bound the *outbound* socket, not the response hand-off.

---

## 3. The threadpool census

### 3.1 Route handler sync/async census — `src/main.py`

AST census over every `@app.<verb>(...)`-decorated function:

```
TOTAL decorated app.* handlers            : 73  (72 HTTP/WS routes + 1 exception handler)
counts by kind (ALL app.* decorated)      : {'async': 73}
counts by kind (HTTP/WS routes only)      : {'async': 72}   [n=72]
SYNC HTTP/WS routes                       : (none)
```

**Count: 72 `async def`, 0 `def`.** There is not one sync route handler in the file.

### 3.2 The anyio 40-token threadpool is **unused**

- Starlette routes sync handlers through `run_in_threadpool` → `anyio.to_thread.run_sync`
  → the default `CapacityLimiter(40)`
  (`anyio/_backends/_asyncio.py:3093-3099` — confirmed default is **40**).
- With **zero** sync routes, nothing reaches it from the router.
- All 7 `Depends(...)` sites (`main.py:3407,3439,3460,3481,3502,3523,3587`) name
  `require_browser_control_auth`, which is `async def` (`src/security.py:314`) — so
  FastAPI does not offload it either.
- `grep -rn "anyio\|run_in_threadpool" src/*.py src/backend/*.py src/frontend/*.py`
  returns **nothing**.

**Load-bearing negative result: the 40-token anyio limiter plays no part in X7.**
Any hypothesis built on "40 threadpool tokens" is measuring a pool this app never touches.

### 3.3 The three pools that *do* exist

| Pool | Size | Who uses it | Evidence |
|---|---|---|---|
| **Event loop** | **1** | All 72 async route handlers, all middleware | `config.py:255` `workers=1` |
| **asyncio default executor** | **20** = `min(32, cpu_count+4)`, cpu_count=16 | The 30 `asyncio.to_thread(...)` sites in `main.py` | CPython `loop.run_in_executor(None, …)` |
| **a2wsgi "WSGI" executor** | **10** | Every Dash callback + every `/dashboard/*` asset | `a2wsgi/wsgi.py:154` |
| anyio limiter | 40 | **nobody** | §3.2 |

`asyncio.to_thread` uses the loop's *default* executor, **not** anyio's limiter — so the
30 guarded sites and the 0 sync routes draw on different pools entirely.

---

## 4. The self-call graph

`DashboardManager._api_url` (`src/frontend/dashboard_manager.py:2260-2273`) resolves
against `self._api_base_url = f"http://127.0.0.1:{self._settings.server.port}"`
(`:528`, `:531`) — i.e. **canopy calls its own FastAPI over loopback HTTP**.

37 `_api_url(` occurrences = 1 definition + **36 call sites**, resolving to **26 distinct
target routes**. All 36 outbound calls carry `headers=internal_api_headers()`
(36 `requests.*` sites, 36 `internal_api_headers()` — 100 % coverage), which matters
for §6.

### 4.1 The `dcc.Interval` drivers

| Interval id | Period | Enabled by default | Evidence |
|---|---|---|---|
| `fast-update-interval` | **1000 ms** | yes | `dashboard_manager.py:1850`, `canopy_constants.py:370` |
| `slow-update-interval` | **5000 ms** | yes | `:1851`, `canopy_constants.py:371` |
| `tabpoll-topology` | 5000 ms | **`disabled=True`** until the tab is active | `:1859` |
| `tabpoll-dataset` | 5000 ms | **`disabled=True`** | `:1860` |
| `tabpoll-workers` | 5000 ms | **`disabled=True`** | `:1861` |
| `tabpoll-boundaries` | 5000 ms | **`disabled=True`** | `:1869` |
| `params-init-interval` | 1000 ms, **`max_intervals=1`** | one-shot on mount — **not periodic** | `:1871` |
| `apply-watchdog-interval` | 5000 ms | yes, but makes **no** self-call | `:1880` |

### 4.2 The table

Columns: **(a)** periodic or user-triggered · **(b)** FastAPI handler sync/async ·
**(c)** does the handler reach cascor, and is it circuit-breaker protected.
`LOOP` in column (b) means the cascor call runs **on the event loop** (no `to_thread`).

| # | Target route | Callback (`dashboard_manager.py`) | (a) Driver | (b) FastAPI handler | (c) Cascor call |
|---|---|---|---|---|---|
| 1 | `/api/status` | `_update_unified_status_bar_handler` :6294 | **PERIODIC 1 Hz** (`fast-update-interval`) | `main.py:1311` async, **`:1317` LOOP** | `get_training_status` — **CB** |
| 2 | `/api/metrics/history` | `_update_metrics_store_handler` :6766 | **PERIODIC 1 Hz** (full fetch every 5th tick, `FULL_HISTORY_POLL_TICK_MODULUS=5`) | `main.py:1348` async, `:1360` **`to_thread` ✅** | monitor history |
| 3 | `/api/status` | `_update_system_panels_handler` :6543 | **PERIODIC 0.2 Hz** (`slow-update-interval`) | `main.py:1311` async, **LOOP** | **CB** |
| 4 | `/api/network/stats` | `_update_network_info_details_handler` :6676 (called from #3) | **PERIODIC 0.2 Hz** | `main.py:1364` async, **`:1401` LOOP** | `get_network_data` — **CB** |
| 5 | `/api/stream_health` | `_update_stream_health_handler` :7819 (called from #3) | **PERIODIC 0.2 Hz** | `main.py:1321` async, **`:1333` LOOP** | **none** — in-memory snapshot (`cascor_service_adapter.py:977-995`). Harmless. |
| 6 | `/api/history/dataset_swaps` | `_poll_dataset_swap_events_handler` :5854 | **PERIODIC 0.2 Hz** | `main.py:4168` async, `:4180` **`to_thread` ✅** | — |
| 7 | `/api/topology` | `_update_topology_store_handler` :6882 | **PERIODIC 0.2 Hz**, topology tab only | `main.py:1415` async, `:1423` **`to_thread` ✅** | CB |
| 8 | `/api/topology/raw` | `_update_raw_topology_store_handler` :6944 | **PERIODIC 0.2 Hz**, topology tab **+ weight_matrix** only | `main.py:1430` async, `:1436` **`to_thread` ✅** | CB |
| 9 | `/api/v1/workers/list` | `_update_workers_store_handler` :6983 | **PERIODIC 0.2 Hz**, workers tab only | `main.py:3235` async, **`:3254` LOOP** | `_client.list_workers()` — **NO CB** |
| 10 | `/api/v1/workers/stats` | `_update_workers_store_handler` :7007 | **PERIODIC 0.2 Hz**, workers tab only | `main.py:3197` async, **`:3206` LOOP** | `_client.get_worker_stats()` — **NO CB** |
| 11 | `/api/dataset` | `_update_dataset_store_handler` :7024 | **PERIODIC 0.2 Hz**, dataset tab only | `main.py:1443` async, **`:1449` LOOP** | `get_dataset_info` — **CB** |
| 12 | `/api/decision_boundary` | `_update_boundary_store_handler` :7050 | **PERIODIC 0.2 Hz**, boundaries tab only | `main.py:1723` async, **`:1732` LOOP** | `get_decision_boundary` — **NO CB** (`cascor_service_adapter.py:2202`) |
| 13 | `/api/dataset` | `_update_boundary_dataset_store_handler` :7078 | **PERIODIC 0.2 Hz**, boundaries tab only | as #11 | **CB** |
| 14 | `/api/train/status` | `_resolve_model_class` :2287 | one-shot on mount (`params-init-interval`) | `main.py:3524` async, **`:3530` LOOP** | `get_status` — CB |
| 15 | `/api/dataset/generators` | `_fetch_generators` :2727 | one-shot on mount + dropdown change | `main.py:1682` async | — |
| 16 | `/api/admin/experimental_functions` | `load_reconcile_experimental_functions` :5039 | one-shot on mount | `main.py:4042` async, `:4051` **`to_thread` ✅** | — |
| 17 | `/api/state` | `_init_params_from_backend_handler` :7835 | one-shot on mount | `main.py:1171` async, `:1237` **`to_thread` ✅** | CB |
| 18 | `/api/state` | `_read_restart_param_seed` :5530 | user (restart button) | as #17 | — |
| 19 | `/api/state` | `_apply_params_via_backend` :7624 | user (apply) | as #17 | — |
| 20 | `/api/stage_dataset` | :2861, :5651 | user | `main.py:3986` async, `:3995` `to_thread` ✅ | — |
| 21 | `/api/model/select` | `_select_model_handler` :2886 | user | `main.py:3732` async | — |
| 22 | `/api/dataset/generate` | :4264, :4291 | user | `main.py:1456` async, **`:1489`/`:1497` LOOP** | — |
| 23 | `/api/dataset/import-file` | :4328 | user | `main.py:1512` async, **`:1536` LOOP** | — |
| 24 | `/api/dataset/import-url` | :4353 | user | `main.py:1599` async, **`:1671` LOOP** | — |
| 25 | `/api/cancel_pending_dataset` | :4961 | user | `main.py:4009` async, `to_thread` ✅ | — |
| 26 | `/api/admin/experimental_functions` (POST) | :5086 | user | `main.py:4064` async, `to_thread` ✅ | — |
| 27 | `/api/history/…/dataset_swaps` | :5965 | user (snapshot load) | `main.py:4194` async, `to_thread` ✅ | — |
| 28 | `/api/live_dataset_swap` | :6072, :6124 | user | `main.py:4099`/`4130` async, `to_thread` ✅ | — |
| 29 | `/api/train/restart` | `_execute_restart_handler` :5718 | user | `main.py:3588` async, **`:3617`/`:3638` LOOP** | start/stop — no CB |
| 30 | `/api/train/{command}` | `_handle_training_buttons_handler` :7137 | user | `main.py:3408-3503` async, **`:3428`… LOOP** | no CB |
| 31 | `/api/set_params` | `_apply_params_via_backend` :7620 | user | `main.py:3802` async, `:3899` `to_thread` ✅ | — |

**Two dead entries, correctly excluded.** `_update_training_status_store_handler`
(`:5977`) and `_update_network_info_handler` (`:6569`) contain `_api_url` calls but are
wired to **no** callback — both were merged into the unified/system-panel callbacks and
survive only as "directly invocable unit-test surface" (`:5145-5147`, `:6572-6575`).
They contribute **zero** live traffic. That is why 36 sites collapse to 34 live ones.

### 4.3 The periodic set — what runs with no user interaction

**Always on, any tab (2 pollers, 4 requests / 5 s):**

| Route | Rate | Blocks the loop on a cascor call? |
|---|---|---|
| `/api/status` | **1.0 /s** | **YES** — CB-protected |
| `/api/metrics/history` | 1.0 /s | no (`to_thread`) |
| `/api/status` | 0.2 /s | **YES** — CB-protected |
| `/api/network/stats` | 0.2 /s | **YES** — CB-protected |
| `/api/stream_health` | 0.2 /s | no cascor call |
| `/api/history/dataset_swaps` | 0.2 /s | no (`to_thread`) |

**Tab-gated additions (only while that tab is selected):**

| Tab | Routes | Blocks the loop? |
|---|---|---|
| topology | `/api/topology`, `/api/topology/raw` | no — both `to_thread` |
| dataset | `/api/dataset` | **YES** — CB |
| **workers** | `/api/v1/workers/list` **+** `/api/v1/workers/stats` | **YES × 2 — NEITHER has a circuit breaker** |
| boundaries | `/api/decision_boundary`, `/api/dataset` | **YES** — boundary has **no** CB |

Each additional open browser tab multiplies every rate above.

---

## 5. The retry / timeout budget

### 5.1 Client construction

`src/backend/cascor_service_adapter.py:507`:

```python
self._client = client or JuniperCascorClient(base_url=service_url, api_key=api_key)
```

**No `timeout=` and no `retries=` are passed** — both are library defaults.

`site-packages/juniper_cascor_client/client.py:74-97`:

```python
timeout: int = DEFAULT_REQUEST_TIMEOUT,
retries: int = DEFAULT_RETRY_COUNT,
...
retry_strategy = Retry(
    total=retries,
    backoff_factor=DEFAULT_BACKOFF_FACTOR,
    status_forcelist=RETRYABLE_STATUS_CODES,
    allowed_methods=RETRY_ALLOWED_METHODS,
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=DEFAULT_POOL_MAXSIZE)
```

`juniper_cascor_client/constants.py:28-38`:

| Constant | Value |
|---|---|
| `DEFAULT_REQUEST_TIMEOUT` | **30** (a scalar, so `requests` applies it to **both** connect and read) |
| `DEFAULT_RETRY_COUNT` | **3** |
| `DEFAULT_BACKOFF_FACTOR` | **0.5** |
| `RETRYABLE_STATUS_CODES` | `[429, 502, 503, 504]` |
| `RETRY_ALLOWED_METHODS` | `[GET, POST, DELETE, PUT, PATCH]` |
| `DEFAULT_POOL_MAXSIZE` | 10 |

**Discrepancy with the brief.** The brief states "The log showed `Retry(total=2)`".
The installed code is **`total=3`** (`constants.py:29`, client 0.7.0). Either the log
predates a bump, or it came from a different client. **All arithmetic below uses
`total=3` = 4 attempts**, which is the code on disk. At `total=2` the refused-case
figure would be 1.0 s and the black-hole case 93 s.

The per-request timeout is applied at `client.py:363` (`timeout=self.timeout`).

### 5.2 urllib3 backoff formula (urllib3 2.7.0, `util/retry.py:309-326`)

```python
if consecutive_errors_len <= 1: return 0
backoff_value = self.backoff_factor * (2 ** (consecutive_errors_len - 1))
return float(max(0, min(self.backoff_max, backoff_value)))
```

`DEFAULT_BACKOFF_MAX = 120` (`retry.py:210`), never reached here.

### 5.3 Worst-case wall time for one cascor call

| After failure # | Sleep |
|---|---|
| 1 | 0.00 s (first retry is not delayed) |
| 2 | 0.5 × 2¹ = **1.00 s** |
| 3 | 0.5 × 2² = **2.00 s** |
| | **Σ backoff = 3.00 s**, over **4 attempts** (1 initial + 3 retries) |

**Case (a) — cascor process down, host stack replies RST ("connection refused"):**
each connect fails immediately, so the 30 s timeout is *not* consumed.
**Total = 0 + 3.00 s backoff = 3.00 s.**

**Case (b) — cascor host unreachable / SYNs dropped (firewall, dead container host,
paused container):** each attempt burns the full connect timeout.
**Total = 4 × 30 s + 3.00 s = 123.0 s.**

### 5.4 Measured confirmation (library-only probe)

Script: `scratchpad/retry_budget.py`, run in `JuniperCanopy1`, importing the real
constants from `juniper_cascor_client.constants`:

```
config: total=3 backoff_factor=0.5 timeout=30 pool_maxsize=10
urllib3 backoff schedule (backoff_max=120):
   after failure #1 -> sleep 0.00s
   after failure #2 -> sleep 1.00s
   after failure #3 -> sleep 2.00s
   TOTAL backoff sleep = 3.00s   (attempts = 1 initial + 3 retries = 4)

(a) CONNECTION REFUSED (loopback, closed port 53739)
    elapsed = 3.004 s   exc = ConnectionError

(b) SYN BLACK-HOLE (192.0.2.1, per-attempt timeout artificially 2s)
    elapsed = 11.009 s   exc = ConnectTimeout      # = 4x2 + 3, formula confirmed
    -> extrapolated at the real timeout of 30s:
       4 attempts x 30s + 3.0s backoff = 123.0 s
```

Prediction and measurement agree to 4 ms in case (a); case (b) confirms the
`n_attempts × timeout + backoff` shape exactly (11.009 s vs 11.0 s predicted).

### 5.5 How `DASHBOARD_GET_TIMEOUT` relates

`src/canopy_constants.py:432`: `DASHBOARD_GET_TIMEOUT: Final[int] = 5`.
Sibling values: `FAST_API_TIMEOUT_SECONDS = 1.0` (`:375`), `API_TIMEOUT_SECONDS = 2`
(`:374`), `DASHBOARD_POST_TIMEOUT = 2` (`:421`), `DASHBOARD_LONG_POST_TIMEOUT = 10`
(`:426`), `DASHBOARD_RESTART_POST_TIMEOUT = 30` (`:430`).

**These are the *inner* leg only.** They bound `dashboard_manager` → **canopy's own**
FastAPI (loopback). They do **not** bound canopy → cascor, which is governed by the
30 s / 4-attempt budget above.

The relationship is a **~25× mismatch**:

```
dashboard --(1.0-5.0 s budget)--> canopy FastAPI --(3.0 s .. 123.0 s budget)--> cascor
```

The inner timeout is 3–123× shorter than the work it is waiting on. Consequences:

1. Every periodic Dash poll that lands on a blocked route **times out and returns
   `dash.no_update`** — the UI degrades quietly rather than erroring. The dashboard
   *looks* merely stale.
2. The Dash callback's timeout frees its WSGI thread only for the *outbound socket*.
   The response hand-off (§2.2) is **not** covered, so the thread can still park.
3. The abandoned canopy→cascor call **keeps running on the event loop** after the
   dashboard has given up. Client-side abandonment provides no back-pressure at all.

Docker's health probe has the same mismatch: `Dockerfile:107-108`
`HEALTHCHECK --interval=30s --timeout=10s --retries=3` running
`curl --max-time 5 http://localhost:8050/v1/health`. Compose overrides it to
`interval: 15s / timeout: 10s / retries: 5`
(`juniper-deploy/docker-compose.yml:58-63`, applied at `:733`).
**5 s curl budget vs a 3.0 s (refused) or 123 s (black-hole) handler.** In the
black-hole case the probe fails every time and the container is marked unhealthy.

---

## 6. The rate limiter — ruled out as a hang mechanism

`src/main.py:427-428`:

```python
rate_limiter = get_rate_limiter()
app.add_middleware(SecurityMiddleware, api_key_auth=api_key_auth, rate_limiter=rate_limiter)
```

`src/security.py:271-282` → `RateLimiter(requests_per_minute=settings.rate_limit_requests_per_minute, enabled=settings.rate_limit_enabled)`.

| Question | Answer | Evidence |
|---|---|---|
| **Algorithm** | In-memory **fixed-window counter** (not token bucket, not sliding window) | `security.py:108-133`, `check()` at `:175-209` |
| **Budget** | `rate_limit_requests_per_minute` = **60** per 60 s window | `settings.py:318`, `security.py:117-118` |
| **Enabled?** | **`rate_limit_enabled: bool = False` — OFF BY DEFAULT** | `settings.py:317` |
| **Keyed on** | `key:<api_key>` when authenticated, else **`ip:<client.host>`** | `security.py:151-166` |
| **On exceed** | `raise HTTPException(429)` → caught at `middleware.py:131-136` → **`JSONResponse(429)` returned immediately** | `security.py:239-249` |
| **Sleeps or blocks?** | **NO.** No `sleep`, no `await`, no wait anywhere in the exceed path. Pure fast-fail with `Retry-After`. | `security.py:239-249` |
| **`/v1/health` exempt?** | **YES** — `_is_exempt` short-circuits **before both** the key gate and the limiter | `middleware.py:115-116`, `:159-161`; `canopy_constants.py:557-573` lists `/`, `/health`, `/api/health`, `/v1/health`, `/v1/health/live`, `/v1/health/ready` |
| **Loopback exempt?** | Not by IP — but **every** canopy self-call carries `INTERNAL_REQUEST_HEADER`, compared with `hmac.compare_digest`, and returns before `check()` | `security.py:229-231`; `frontend/internal_api.py:75`; 36/36 call-site coverage |
| **`/dashboard/*`** | Prefix-exempt | `canopy_constants.py:555` |

**Verdict: the rate limiter cannot produce a hang.**

1. It is **disabled by default**.
2. Even enabled, the exceed path returns 429 in microseconds — it never sleeps.
3. `/v1/health` never reaches it at all (`EXEMPT_PATHS`).
4. The dashboard's own polling is token-exempt, so it cannot drain the bucket.

The only shared state is a `threading.Lock` (`security.py:132`) held for a dict
read/write — microseconds, and not reachable from the self-call path.

**Mechanism (3) of the brief is refuted.** If X7 were rate-limiting, the symptom would
be fast HTTP 429s with a `Retry-After` header, not a hang — and `/v1/health` would be
unaffected in any case.

---

## 7. Arithmetic — how long to exhaust, and of what

### 7.1 The binding resource is the event loop, not a pool

The brief's framing ("how long to exhaust the pool") does not fit the code, and saying
so is itself a finding:

- The **anyio 40-token pool is never touched** (§3.2) — it cannot be exhausted.
- The **a2wsgi 10-thread pool** is downstream: it fills only *because* the loop is
  already blocked (§2.2), so it is an amplifier, not the trigger.
- The **event loop has capacity 1**. It is not "exhausted" — it is **occupied**. The
  right metric is **duty cycle**: Σ(rate × blocking-duration). Duty cycle ≥ 1.0 means
  permanent unresponsiveness.

### 7.2 Circuit-breaker coverage is the multiplier

`CircuitBreaker` (`src/backend/circuit_breaker.py:35-103`), configured
`failure_threshold=5`, `recovery_timeout=60.0` (`canopy_constants.py:648-650`).
OPEN returns the fallback instantly; after 60 s it half-opens and lets **one** probe
through.

**Coverage is 5 `_cb.call` sites against 45 `self._client.` call sites in
`cascor_service_adapter.py` — ~11 %.** Protected: `get_training_status` (`:1968`),
`get_network_data` (`:1978`), `extract_network_topology` (`:2097`), `get_raw_topology`
(`:2114`), `get_dataset_info` (`:2128`). Everything else is bare.

So there are two steady-state costs per call while cascor is down:

| Path class | Steady-state cost per call |
|---|---|
| **CB-protected** | 5 × D to open, then ~0 for 60 s, then 1 × D per 60 s |
| **NOT CB-protected** | **D on every single call, forever** |

with D = **3.0 s** (refused) or **123.0 s** (black-holed).

### 7.3 Duty-cycle calculation, refused case (D = 3.0 s)

**Transient (first ~15 s).** `/api/status` at 1 Hz drives the shared breaker:
5 failures × 3.0 s = **15.0 s of ~100 % loop occupancy** before it opens.
(The breaker is one instance on the adapter, so `/api/network/stats` shares the
benefit — and the cost.)

**Steady state, default tab, dashboard open:**

| Source | Rate | D | Loop-seconds / s |
|---|---|---|---|
| CB half-open probe (`/api/status` + `/api/network/stats`) | 2 / 60 s | 3.0 s | 0.10 |
| `/v1/health` docker probe (compose: 15 s) | 1 / 15 s | 3.0 s | 0.20 |
| **Total duty cycle** | | | **≈ 0.30** |

**≈ 30 % occupied — degraded and jittery, but NOT a permanent hang.** With the default
tab alone, the refused case does not reproduce the symptom. **That is a finding**: the
observed total unresponsiveness needs either a heavier tab or the black-hole case.

**Steady state, Workers tab active:**

`_update_workers_store_handler` issues **two** sequential unprotected calls per tick
(`:6983` `/api/v1/workers/list`, `:7007` `/api/v1/workers/stats`), neither CB-protected:

```
2 calls x 3.0 s = 6.0 s of loop blocking, emitted every 5.0 s
duty cycle = 6.0 / 5.0 = 1.20   ->  120 %
```

**Over 100 %. The loop never catches up. Permanent, self-sustaining hang** — and it
persists indefinitely, because no circuit breaker ever short-circuits these two.
Add the 0.30 baseline: **≈ 1.50**.

**Steady state, Boundaries tab active:**
`/api/decision_boundary` is unprotected: 3.0 s per 5 s tick = 0.60, plus baseline
0.30 → **≈ 0.90**. Right at the edge; any second browser tab pushes it over 1.0.

**Time to saturation from t₀ (cascor goes away), Workers tab open:**

```
t=0 s      first /api/status blocks 3.0 s
t=0-15 s   5 consecutive failures -> breaker OPEN; loop ~100% blocked throughout
t=5 s      first workers tick: 6.0 s of blocking, still running at t=11 s
t=10 s     second workers tick queues behind it
...
```

**The loop is saturated within one `slow-update-interval` tick — under 5 seconds —
and never recovers while the tab stays open.**

### 7.4 Black-hole case (D = 123.0 s) — saturation is immediate and total

Duty cycle is irrelevant here: **a single unguarded call blackouts the process for
123 s.** One docker health probe at t=0 → 123 s of total unresponsiveness, during which
the 15 s probe fires 8 more times (each queueing behind), the 1 Hz `/api/status` poll
queues, and every `/dashboard/*` request parks. The breaker needs 5 × 123 s = **615 s
(> 10 minutes)** merely to open.

This matches the reported symptom exactly and unconditionally — **no tab selection
required.**

### 7.5 The a2wsgi pool, as an amplifier

Dash callbacks time out against canopy in 1.0–5.0 s and free their socket, so the
10-thread pool is **not** the trigger. But once the loop is blocked, `send()`
(`a2wsgi/wsgi.py:215-219`, no timeout) parks each thread that has finished its work.
With ≥ 4 always-on periodic callbacks plus asset requests, all 10 threads park within
a few seconds and **`/dashboard/*` goes dark too** — consistent with "stops answering
HTTP entirely" rather than "only the API is slow".

### 7.6 Verdict on the brief's hypothesis

**The numbers do not support pool exhaustion, and they do support loop occupancy.**
Any fix sized against "40 anyio tokens" or "10 WSGI workers" would be sized against a
pool that is either unused or merely a downstream symptom.

---

## 8. Version dependence: `b78bbbb` vs `9fbf4b8` (canopy#562)

`git diff b78bbbb 9fbf4b8 -- src/frontend/dashboard_manager.py` — 47 insertions,
5 deletions, all inside `update_raw_topology_store` / `_update_raw_topology_store_handler`.

**Three changes:**

1. `State("network-visualizer-display-mode","value")` → **`Input(...)`** (`:3992`).
2. Added `State("network-visualizer-raw-topology-store","data")` as `current`.
3. Added identity suppression **after** the fetch (`:6949-6959`):
   `json.dumps(current, sort_keys=True) == json.dumps(fetched, sort_keys=True)` →
   `dash.no_update`.

**Effect on the periodic self-call rate: NONE.**

The gate that decides whether the HTTP call happens at all is unchanged on both sides:

```python
if active_tab != "topology" or display_mode != "weight_matrix":
    return dash.no_update
```

and the suppression in (3) runs **after** `requests.get(self._api_url("/api/topology/raw"))`
has already completed. `/api/topology/raw` is therefore fetched at the same 0.2 Hz on
both commits. Change (1) adds one **user-triggered** fetch when the display mode is
switched — not periodic.

**Table flag (per the coordinator's request):** row **#8** (`/api/topology/raw`) is the
only entry `9fbf4b8` touched. It **neither removed, throttled, nor short-circuited** the
periodic self-call. No other row changed.

**Consequence for §7: the arithmetic is identical for both commits.** Giving it twice
would produce the same numbers, so it is stated once and holds for `b78bbbb` and
`9fbf4b8` alike. `/api/topology/raw` is `to_thread`-guarded (`main.py:1436`) in both, so
it never contributed to loop occupancy in the first place.

**One real difference, in a different pool.** Before `9fbf4b8`, the unchanged payload
was rewritten to `-raw-topology-store` every 5 s, re-triggering the topology rebuild —
a callback the #562 commit message measures at **1.5–31 s** per run. That rebuild
occupies an **a2wsgi WSGI thread** (1 of 10). So `9fbf4b8` **did** materially reduce
WSGI-executor occupancy on the topology tab, which makes §7.5's amplifier somewhat
slower to bite on that tab. It changed **nothing** about the event-loop occupancy that
drives X7.

**Bottom line: X7's severity is NOT version-dependent between `b78bbbb` and `9fbf4b8`.**
A fix sized against today's numbers is sized correctly for the code X7 was observed on.

---

## 9. THE CRITICAL QUESTION

> `GET /v1/health` is `async def` (`main.py:1056-1057`), so it should run on the event
> loop and survive threadpool exhaustion. How can an async endpoint nonetheless fail to
> respond?

**It does not survive, because the premise is inverted.** Running on the event loop is
what makes it *vulnerable*, not what protects it. Threadpool exhaustion is not the
mechanism; the event loop being the only executor is.

Ranked by strength of evidence:

### M1 — `/v1/health` makes a blocking cascor HTTP call **on the event loop**, itself. *(direct code path; strongest)*

```
src/main.py:1057   async def health_check():
src/main.py:1076       "training_active": backend.is_training_active(),   # <-- no await, no to_thread
  -> src/backend/service_backend.py:160   def is_training_active(self): return self._adapter.is_training_in_progress()
  -> src/backend/cascor_service_adapter.py:1089-1091
         def is_training_in_progress(self) -> bool:
             try:
                 status = self._client.get_training_status()      # BLOCKING requests.Session HTTP
  -> juniper_cascor_client/client.py:357-363   session.request(..., timeout=30)  with Retry(total=3)
```

`backend` is a `ServiceBackend` whenever `settings.cascor_service_url` is set
(`src/backend/__init__.py:88-104`). So on every `/v1/health`, the event loop performs a
synchronous 4-attempt HTTP conversation with cascor: **3.0 s** refused, **123.0 s**
black-holed.

**The decisive detail — this path deliberately bypasses the circuit breaker.** Its
sibling one screen away *is* protected:

```python
# cascor_service_adapter.py:1089   is_training_in_progress  -> self._client.get_training_status()   NO breaker
# cascor_service_adapter.py:1968   get_training_status      -> self._cb.call(...)                   breaker
```

So `/api/status` degrades gracefully after 5 failures, while **`/v1/health` pays the
full retry budget on every single probe, forever**, and never even records a failure
into the breaker.

**All three health endpoints are affected**, not just one:
`/health` + `/api/health` (`:1050`), `/v1/health` (`:1076`),
`/v1/health/ready` (`:1133`). Only `/v1/health/live` (`:1088`) is clean — it returns
`{"status": "alive"}` with no backend touch. Its `probe_dependency` sibling is
correctly `httpx.AsyncClient`-based (`src/health.py:60-82`), which makes the contrast
sharper: the *async* probe was done properly, and the *sync* `is_training_active()`
sitting beside it in the same response dict was not.

### M2 — Even a genuinely clean async endpoint cannot be served while the single loop is blocked by another handler. *(structural; equally strong)*

`workers=1` (`uvicorn/config.py:255`) means one event loop for the whole process. A
blocking call inside **any** `async def` handler stops **every** other request,
including ones with no backend dependency at all.

AST scan (`scratchpad/loop_block_scan.py`): **41 unguarded `backend.*` calls inside
async route handlers.** The periodic offenders are `/api/status` (`:1317`, 1 Hz),
`/api/network/stats` (`:1401`), `/api/v1/workers/list` (`:3254`),
`/api/v1/workers/stats` (`:3206`), `/api/dataset` (`:1449`),
`/api/decision_boundary` (`:1732`).

This is why **`/v1/health/live` also fails**, despite being flawless in isolation — and
it is the reason the symptom is described as canopy stopping HTTP *entirely* rather
than a single endpoint misbehaving.

**The guard exists and was applied inconsistently.** The codebase clearly knows the
hazard — `main.py:1236-1237` even says *"Both fetches are synchronous HTTP calls — keep
them off the event loop so a slow cascor cannot stall every other canopy route"*, and
`:1421` and `:1435` carry an explicit *"N1 event-loop guard"* comment. Thirty
`asyncio.to_thread` hops were added. **The 1 Hz `/api/status` poller and all three
health endpoints were missed.**

### M3 — The a2wsgi WSGI pool then parks too, taking `/dashboard/*` down with it. *(amplifier; direct code evidence)*

`a2wsgi/wsgi.py:215-219`, `send()` → `future.result()` with **no timeout**. Every WSGI
thread that finishes its callback blocks handing the response back through the stalled
loop. All 10 (`wsgi.py:154`, default, not overridden at `main.py:493`) park. Static
assets under `/dashboard/` go through the same executor.

### M4 — asyncio default executor saturation. *(secondary; contributes latency, not the hang)*

The 30 `asyncio.to_thread` sites share the loop's default `ThreadPoolExecutor`,
`min(32, 16+4) = 20` threads. With each cascor call taking 3–123 s, those 20 fill.
But `await`ing a full executor does not block the loop — it yields. So this degrades the
*guarded* routes without explaining a total hang.

### M5 — RULED OUT: the rate limiter. *(negative result)*

Disabled by default (`settings.py:317`); fast-429 with no sleep when enabled
(`security.py:239-249`); `/v1/health` is in `EXEMPT_PATHS` and short-circuits before the
limiter (`middleware.py:115-116`, `canopy_constants.py:562`); self-calls are
token-exempt (`security.py:229-231`, 36/36 sites). **Cannot produce a hang.**

### M6 — RULED OUT: anyio threadpool exhaustion. *(negative result)*

0 sync routes of 72; 0 `anyio.to_thread` / `run_in_threadpool` uses in `src/`; all
`Depends` are `async def`. **The 40-token limiter is never acquired by this
application.**

### M7 — Considered and rejected: uvicorn connection shedding.

`limit_concurrency=None` (`config.py:260`) means the 503 path at
`httptools_impl.py:266-272` is dead code here. `backlog=2048` (`config.py:215`) means
the kernel absorbs 2048 pending connections before refusing — so clients see a **hang**,
not a connection error. This does not *cause* X7, but it explains why the symptom
presents as "stops answering" rather than "refuses connections".

### Why it recovers unaided

There is no request timeout anywhere in uvicorn (§1.2). The loop is released only when
the blocking `requests` call itself returns — which happens the moment cascor starts
answering. No supervision, restart, or breaker transition is needed. **"Recovers unaided
when cascor returns" is the exact signature of a synchronous call on the event loop**,
and it is inconsistent with pool exhaustion (which would leave a backlog to drain) or
with rate limiting (which would recover on a window boundary, not on cascor's return).

---

## 10. Artifact ledger

| Claim | Artifact |
|---|---|
| uvicorn settings | `uvicorn/config.py:215,216,218,255,260,261,263`; `httptools_impl.py:266-272` |
| a2wsgi own executor, 10 threads | `a2wsgi/wsgi.py:153-160,164,200` |
| a2wsgi `send()` has no timeout | `a2wsgi/wsgi.py:215-219,244,251,259,263`; `Body._receive_more_data` `:26-32` |
| Mount without `workers=` | `src/main.py:57,493` |
| 72 async / 0 sync routes | AST census, `scratchpad/route_census.py` |
| anyio limiter = 40, unused | `anyio/_backends/_asyncio.py:3093-3099`; empty grep for `anyio\|run_in_threadpool` in `src/` |
| 41 unguarded backend calls | AST scan, `scratchpad/loop_block_scan.py` |
| `/v1/health` blocking call | `src/main.py:1076` → `service_backend.py:160` → `cascor_service_adapter.py:1089-1091` |
| No CB on the health path | `cascor_service_adapter.py:1089` (bare) vs `:1968` (`_cb.call`) |
| CB coverage 5 of 45 | `grep -c "_cb\.call"` = 5; `grep -c "self\._client\."` = 45 |
| CB config | `circuit_breaker.py:35-103`; `canopy_constants.py:648-650` |
| Retry config | `cascor_service_adapter.py:507`; `client.py:74-97,363`; `constants.py:28-38` |
| Backoff formula | `urllib3/util/retry.py:309-326`, `:210` |
| 3.004 s / 123 s | `scratchpad/retry_budget.py` measured output |
| `DASHBOARD_GET_TIMEOUT` | `src/canopy_constants.py:432`; siblings `:370,371,374,375,388,421,426,430` |
| Rate limiter | `src/security.py:108-133,151-166,175-209,211-249,271-282`; `settings.py:317-318`; `middleware.py:75,99,115-116,131-136,159-161`; `canopy_constants.py:555-573,586-587` |
| Self-call base URL | `dashboard_manager.py:528,531,2260-2273` |
| Intervals | `dashboard_manager.py:1850,1851,1859,1860,1861,1869,1871,1880`; `canopy_constants.py:370,371,388,468` |
| Dead handlers | `dashboard_manager.py:5145-5147,5977,6569,6572-6575` |
| #562 scope | `git diff b78bbbb 9fbf4b8 -- src/frontend/dashboard_manager.py` |
| Healthchecks | `Dockerfile:107-108`; `juniper-deploy/docker-compose.yml:58-63,733` |

**NO ARTIFACT** — stated as such, not asserted:

- Whether the running canopy actually had `rate_limit_enabled=True`. The default is
  `False`; the deployed `.env` was not read. Immaterial — §6 rules the limiter out either way.
- Which cascor failure mode X7 was observed under (RST vs dropped SYN). The two differ by
  **41×** in blocking cost (3.0 s vs 123.0 s). §7 gives both.
- Which dashboard tab was selected during the observation. This decides whether the
  refused case saturates (Workers: 120 %) or merely degrades (default: 30 %).
- How many browser tabs were open — a linear multiplier on every periodic rate.
- The brief's `Retry(total=2)` log line. The installed client is `total=3`
  (`constants.py:29`); the source of the `total=2` observation was not located.
