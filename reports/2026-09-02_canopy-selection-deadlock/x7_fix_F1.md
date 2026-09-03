# X7 fix design — author F1 (lens: minimal, surgical, shippable this week)

**Defect**: juniper-canopy stops answering all HTTP, `/v1/health` included, while juniper-cascor
is unreachable. Cause: synchronous retrying `requests` I/O inside `async def` handlers on a
single-event-loop uvicorn.

**Repo state at time of writing**: `juniper-canopy` @ `9fbf4b8`, branch `main`, clean tree.
Env `JuniperCanopy1`, Python 3.13.13, `juniper-cascor-client` 0.7.0, cpu_count 16.

Everything below was re-derived against the tree; measurements are my own, this session.

---

## 1. Anchor verification

| # | Anchor as given | Verdict | Correction / detail |
|---|---|---|---|
| 1 | `uvicorn.run(...)` at `src/main.py:4419` — workers=1, `limit_concurrency=None`, no request timeout | **CORRECT in effect, imprecise in letter** | The call is `uvicorn.run(app, host=host, port=port, log_level=...)`. No `workers=`, no `limit_concurrency=`, no `timeout_*` are passed at all — single process / single loop by *default*, not by explicit kwarg. Two other launch paths exist and are also single-worker: `util/launch_canopy.bash:12` (`uvicorn main:app --port 8050`) and `Dockerfile:110` (`CMD ["python", "src/main.py"]` → `main()` → line 4419). |
| 2 | 72 routes, all `async def`, zero sync; zero `run_in_threadpool` in `src/` | **CORRECT** | My AST scan: **71 async route functions carrying 72 route decorators** (`/health` and `/api/health` share one function). Zero sync route handlers. |
| 3 | Real pools: loop = 1, asyncio default executor = 20, a2wsgi = 10 | **CORRECT** | `min(32, 16+4) = 20` verified in-env. a2wsgi `WSGIMiddleware.__init__(..., workers: int = 10)` at `a2wsgi/wsgi.py:153-160` — confirmed, and `src/main.py:57` imports it with no `workers` override. |
| 4 | `/v1/health` blocks itself at `main.py:1076` via `backend.is_training_active()` | **CORRECT** | Confirmed. The chain is `main.py:1076` → `service_backend.py:161 is_training_active` → `cascor_service_adapter.py:1089-1091 is_training_in_progress` → `self._client.get_training_status()`, **no breaker**. |
| 5 | Sibling `get_training_status()` at adapter `:1968-1971` IS breaker-protected | **CORRECT** | `adapter.py:1968` uses `self._cb.call(..., fallback=lambda: {"is_training": False, "error": "circuit open"})`. |
| 6 | `/health`, `/api/health`, `/v1/health/ready` details share the defect | **CORRECT** | `main.py:1050` (shared by `/health` + `/api/health`), `main.py:1133` (`ready` → `details.training_active`). |
| 7 | `/api/state` (`main.py:1239`) correctly uses `to_thread`; `main.py` uses it 30 times | **CORRECT** | 30 occurrences. `/api/state` wraps a nested `_fetch_live_status_and_params` at `main.py:1237-1239` — a naive AST scan false-positives here; the anchor is right. |
| 8 | **41** unguarded `backend.*` calls in async route handlers | **CORRECT ±1 — I count 42** | Nested-`to_thread` aware AST scan: **42 unguarded** across **32 route functions**, vs 21 guarded. The delta from 41 is a counting-convention detail (I include `backend._demo.*` and `backend._adapter._client.*`), not a disagreement. Direction and magnitude confirmed. |
| 9 | Breaker coverage 5 of 45 `self._client.` sites | **CORRECT** (spot-checked) | `self._cb.call` appears at adapter `:1970, :1980, :2099, :2117, :2130` — five sites. |
| 10 | `adapter:507` constructs the client with no overrides → `timeout=30, retries=3`, `backoff_factor=0.5` | **CORRECT** | `self._client = client or JuniperCascorClient(base_url=service_url, api_key=api_key)`. Client signature verified: `timeout: int = 30, retries: int = 3`; `Retry(total=retries, backoff_factor=0.5, ...)`. Live construction site: `src/backend/__init__.py:104` (the only non-test one). |
| 11 | Refused = 3.0 s; black-holed ≈ 123 s ("unmeasured, arithmetically derived") | **CORRECT, and I have now MEASURED the model** | See §2. Refused measured **3.003 s**. The black-hole model `timeout*(retries+1) + Σbackoff` was validated at three points to ±12 ms, so 123.0 s is now a validated projection, not a guess. |
| 12 | a2wsgi `send()` calls `future.result()` with no timeout → all 10 WSGI threads park | **CORRECT** | `a2wsgi/wsgi.py:215-219`, verbatim `future.result()`, no timeout arg. |
| 13 | Of the always-on pollers, `/api/status` (`:1317`) and `/api/network/stats` (`:1401`) are unguarded | **CORRECT** | Also confirmed: `/api/stream_health` (`:1333` → `adapter.get_stream_health`) is **not** a hazard — `adapter.py:992-1002` is a pure in-memory snapshot, no upstream call. |

### New findings the brief did not carry

**N1 — The circuit breaker does not move work off the loop.** `src/backend/circuit_breaker.py:96`
executes `result = func(*args, **kwargs)` **inline on the calling thread**. The breaker only *skips*
the call once OPEN. This makes one of the three candidate fixes unsound; see §4/U1.

**N2 — The repo already has an ENFORCED async-blocking lint gate, and it reads GREEN on this defect.**
`.pre-commit-config.yaml:117-131` runs `ruff --select ASYNC` over `^src/.*\.py$`, hard-failing on any
new `ASYNC*` violation ("Phase 4 — enforced", zero visible violations since PR #247). I ran it:

```
$ ruff check --select ASYNC src/main.py src/backend/cascor_service_adapter.py
All checks passed!
```

Ruff's `ASYNC` rules flag *known* blocking primitives (`requests.get`, `open`, `subprocess`). They
cannot see that `backend.is_training_active()` — an ordinary method call — transitively reaches
`requests`. That is exactly why the Phase-0 audit found "4 ASYNC230/240 sites for snapshot-history
file I/O" and **missed all 42 `backend.*` sites**. A vacuous pass. Consequence for §6: the durable
regression gate must be behavioural or a bespoke AST check — *not* a ruff rule.

**N3 — Every caller already gives up long before 30 s.** canopy's own dashboard client timeouts
(`src/canopy_constants.py:373-435`, used in `src/frontend/dashboard_manager.py`):
`FAST_API_TIMEOUT_SECONDS = 1.0` (1 Hz polls), `API_TIMEOUT_SECONDS = 2`,
`DASHBOARD_GET_TIMEOUT = 5`, control POSTs `API_TIMEOUT_SECONDS + 5 = 7`, file import `+10 = 12`,
URL import `+15 = 17`, and `DASHBOARD_RESTART_POST_TIMEOUT = 30` for `/api/train/restart` alone —
whose budget is dominated by canopy's *own* `RESTART_STOP_WAIT_TIMEOUT_SECONDS = 15.0` await loop,
not by a single upstream HTTP call. So the upstream 30 s budget is dead weight: past ~7 s, canopy is
doing work nobody is waiting for. **This is the evidence that lowering the client timeout costs
nothing user-visible.**

**N4 — The container healthcheck amplifier is real and cross-repo.** `Dockerfile:107-108` probes
`/v1/health` with `--max-time 5`, `--retries 3`, `--interval=30s`. `juniper-deploy/docker-compose.yml:732`
and `:814` probe the same endpoint with `timeout=5`. A black-holed cascor (123 s) fails all three
attempts → container reads **unhealthy**. Precision matters: compose's `restart: unless-stopped`
(`docker-compose.yml:740`) keys off process *exit*, not health, so plain Compose will **not**
restart-loop canopy — but the health signal lies, and any Swarm/k8s deployment *would* kill it.

**N5 — `backend` is a module global that is REASSIGNED at runtime** (`main.py:480` `backend = None`;
`main.py:3722` `backend = new_backend` on model swap). Any fix must resolve it at call time. See R2.

**N6 — There is no per-call timeout escape hatch.** `JuniperCascorClient._get(path, params)` and
`._post(path, json)` take no `timeout` argument. The client-level `timeout` is global to all 45 call
sites. This constrains §3-A to a single value and rules out "just lower it for health".

---

## 2. Measured cost model (my measurements, this session)

Script: `scratchpad/measure_client.py` (throwaway; if kept it belongs in `util/ad-hoc/` per the
repo's script-placement rule). A real `JuniperCascorClient` against (a) a closed loopback port and
(b) a loopback socket that accepts and never replies.

```
=== A. CONNECTION REFUSED (closed port) ===
  retries=0  ->  0.003 s
  retries=1  ->  0.002 s     <-- first urllib3 retry has ZERO backoff
  retries=2  ->  1.002 s
  retries=3  ->  3.003 s     <-- TODAY. matches the reported 3.008 s

=== B. BLACK HOLE (accepts, never replies) ===
  timeout=2 retries=0 -> 2.004 s   (predicted 2.0)
  timeout=2 retries=1 -> 4.007 s   (predicted 4.0)
  timeout=2 retries=3 -> 11.012 s  (predicted 11.0)
  timeout=5 retries=0 -> 5.006 s   (predicted 5.0)
```

Model, validated to **±12 ms at three points**:

```
cost = timeout * (retries + 1) + Σ backoff_n ,   backoff_1 = 0, backoff_n = 0.5 * 2^(n-1)
```

**The refused-case 3.0 s is 100% urllib3 retry backoff sleep** (0 + 1.0 + 2.0). Connection-refused
itself is ~2 ms. Today's black hole: `30*4 + 3.0` = **123.0 s** — now a validated projection.

Cost table for candidate settings:

| `timeout` | `retries` | refused | black-hole | note |
|---|---|---|---|---|
| 30 | 3 | **3.003 s** | **123.0 s** | TODAY |
| 30 | 1 | **0.002 s** | 60.0 s | one-keyword fix |
| 30 | 0 | 0.003 s | 30.0 s | loses all 5xx retry |
| **10** | **1** | **0.002 s** | **20.0 s** | **recommended** |
| 10 | 0 | 0.003 s | 10.0 s | loses all 5xx retry |

Note `retries=1` and `retries=0` are **indistinguishable on the refused path** (0.002 vs 0.003 s)
because urllib3's first retry sleeps zero. `retries=1` is therefore strictly better: same outage
removal, and one retained retry for transient 5xx / a cascor restart blip.

---

## 3. The changes, ranked by (correctness × smallness)

### A — Bound the client at construction. `src/backend/cascor_service_adapter.py:507` (RANK 1)

```python
# BEFORE
self._client = client or JuniperCascorClient(base_url=service_url, api_key=api_key)

# AFTER
self._client = client or JuniperCascorClient(
    base_url=service_url,
    api_key=api_key,
    # X7: an unbounded upstream budget turns one slow cascor call into a
    # whole-service outage (all 42 sync-in-async sites share this client).
    # No canopy caller waits longer than 7 s (canopy_constants.py:373-435),
    # so a 10 s ceiling is already more generous than any consumer.
    timeout=BackendConstants.CASCOR_CLIENT_TIMEOUT_SECONDS,
    retries=BackendConstants.CASCOR_CLIENT_RETRIES,
)
```

plus two constants in `src/canopy_constants.py` (`BackendConstants`, next to the existing
`CIRCUIT_BREAKER_*` block at `:648-650`):

```python
CASCOR_CLIENT_TIMEOUT_SECONDS: Final[int] = 10
CASCOR_CLIENT_RETRIES: Final[int] = 1
```

**Size**: 1 production call site, ~8 lines with comment, 2 constants. **Files touched: 2.**

**Does it remove the outage on its own?**
- **Connection-refused: YES.** 3.003 s → 0.002 s per call, a **1500x** reduction. Eight concurrent
  `/v1/health` go from 24.05 s to ~16 ms. The measured serialization symptom disappears entirely.
- **Black-holed: NO.** 123 s → 20 s. Better by 6.15x, still an outage.

**Why rank 1 despite not covering the black hole**: it is the *only* single-point change that covers
**all 42 unguarded route sites and all 45 client sites at once**, and — uniquely — it **cannot be
forgotten at a new call site.** Every other option is a per-site edit that the 43rd handler will skip.

### B — `to_thread` the probe + always-on paths. `src/main.py` (RANK 2)

Five call sites, each a one-line edit to the already-blessed in-repo idiom (`main.py:3553` and
`:3615` already do exactly `await asyncio.to_thread(backend.is_training_active)`):

| Line | Route | Edit |
|---|---|---|
| 1050 | `/health`, `/api/health` | `"training_active": await asyncio.to_thread(backend.is_training_active),` |
| 1076 | `/v1/health` | same |
| 1133 | `/v1/health/ready` (`details`) | same |
| 1317 | `/api/status` (1 Hz + 0.2 Hz) | `return await asyncio.to_thread(backend.get_status)` |
| 1401 | `/api/network/stats` (0.2 Hz) | `network_data = await asyncio.to_thread(backend._adapter.get_network_data)` |

**Size**: 5 lines, 1 file.

**Does it remove the outage on its own?** **Partially, and only for one meaning of "outage".**
It achieves **G1 — the event loop stays responsive**: `/v1/health/live` and every pure-async route
keep answering, and the a2wsgi `/dashboard/*` amplifier is defused for these paths. It does **not**
achieve **G2 — `/v1/health` answering promptly**: the handler still awaits the thread for the full
123 s, so the Docker/compose healthcheck still fails. And the other 37 unguarded sites still block:
a user pressing Start Training freezes the whole app for 123 s.

Note the values returned are **unchanged**, so no existing assertion moves. This matters — see R8.

### C — Retire the container healthcheck's upstream dependency (RANK 3)

`Dockerfile:108`: `.../v1/health` → `.../v1/health/live`. `/v1/health/live` (`main.py:1087-1090`)
returns `{"status": "alive"}` with zero dependencies. A container *liveness* probe should test
liveness; upstream readiness is `/v1/health/ready`'s job and it already probes cascor correctly via
async `httpx` (`src/health.py:60-100`).

**Size**: 1 line in canopy. **But it is cross-repo**: `juniper-deploy/docker-compose.yml:732` and
`:814` must move too, or the compose stack keeps reporting canopy unhealthy. Scope: 1 line here + 2
lines in juniper-deploy.

**Does it remove the outage on its own?** No — it removes the *misreporting* and the
orchestrator-kill amplifier (N4). Worth landing because it is the only cheap route to G2 that does
not touch the response schema.

### D — The remaining 37 unguarded sites (RANK 4 — follow-up, not this PR)

Mechanical `to_thread` wrapping of the other 37 sites: the 6 WS control calls (`main.py:895-907`),
the 5 train-control routes, snapshot create/restore, `/api/metrics`, `/api/dataset`,
`/api/decision_boundary`, the 5 remote-worker routes. ~37 lines, high review cost, **and it is the
change that makes the executor a bottleneck if A has not landed** (see R6). Necessary for structural
correctness; not necessary to stop the outage. Deliberately deferred.

---

## 4. The sharpest question: is there a ≤ 5-line fix that provably removes the outage?

### Yes — for the connection-refused case, in ONE line.

```python
self._client = client or JuniperCascorClient(base_url=service_url, api_key=api_key, retries=1)
```

**Cost**: one keyword argument, one file, one line. Refused-case per-call cost goes from a measured
3.003 s to a measured 0.002 s. The mechanism is understood and verified, not empirical luck:
urllib3's first retry has zero backoff, so the entire 3.0 s was sleep. Eight concurrent health
checks: 24.05 s → ~16 ms. The outage, as reproduced, is gone.

Regression surface is essentially nil: the 30 s per-attempt budget is untouched, so no
slow-but-working cascor call changes behaviour; one retry is retained, so transient 5xx and
restart blips still recover. This is the highest correctness-per-line change available.

### No — for the black-holed case. And no ≤ 5-line fix exists for it.

`retries=1` alone leaves the black hole at 60.0 s. My recommended 5-line form
(`timeout=10, retries=1` + 2 constants) gets it to 20.0 s. Still an outage.

The reason no small fix closes it: with 42 sync sites remaining on the loop and five always-on
pollers (up to 1 Hz) multiplied by every open browser tab, you would need the per-call cost driven
below roughly 50 ms to keep the loop free. Reaching that requires a timeout so aggressive
(≤ 0.05 s) that it breaks every legitimate cascor call. **You cannot buy black-hole immunity with a
timeout value; you have to get the calls off the loop.** That is change B (for the probe paths) and
change D (for the rest) — not a 5-liner.

### UNSOUND small fixes — stated loudly

**U1 — "Just route the health endpoints through the breaker-protected `get_training_status()`
sibling." THIS IS THE DANGEROUS ONE.** It reads like a clean two-line fix that reuses existing,
tested machinery. It does not work. `circuit_breaker.py:96` runs `func(*args, **kwargs)` **inline on
the calling thread**; the breaker only *skips* the call once OPEN. With
`CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5` and `CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60.0`
(`canopy_constants.py:649-650`), a black-holed cascor blocks the loop for **5 × 123 = 615 s** before
the breaker opens, then re-blocks a full 123 s on every half-open probe (`circuit_breaker.py:51-56`
flips OPEN→HALF_OPEN on a mere state *read* after 60 s) — a steady-state **~67% loop-block duty
cycle**. Refused case: 15 s up front, then 3.0 s every ~63 s forever. **The breaker changes the
steady-state cost; it never changes the blocking property.** A reviewer who sees "now it's behind
the circuit breaker, same as its sibling" will approve this, the symptom will partly improve in a
refused-cascor test, and the black-hole hole stays wide open. Reject it explicitly in review.

**U2 — "Set `workers=N` on uvicorn."** Unsound twice over. (a) canopy holds per-process state: the
`training_state` global, `websocket_manager`, the WS relay `asyncio.Task`, the `DashboardManager` /
a2wsgi mount, and the `backend` global that is reassigned at `main.py:3722`. N workers fragment all
of it — WS clients would land on processes that do not host the relay. (b) uvicorn requires an
import string for `workers > 1`; `uvicorn.run(app_object, workers=2)` at `main.py:4419` does not do
what it looks like it does.

**U3 — "`to_thread` everything and we're done."** Incomplete *and* it introduces a new failure mode.
`asyncio.to_thread` uses the loop's default executor: **20 slots** here (verified
`min(32, 16+4)`), shared with the 30 `to_thread` sites `main.py` already has (including snapshot
file I/O). At 123 s per call with five always-on pollers times N tabs, all 20 slots fill and
`to_thread` itself queues. **Without A, `to_thread` converts a total outage into a
resource-exhaustion outage** — slower to appear, harder to diagnose, and it now also starves the
unrelated snapshot file-I/O paths that legitimately use the same pool. This is the strongest reason
A must land before D.

**U4 — "`asyncio.wait_for(asyncio.to_thread(...), timeout=T)` bounds it."** Partially unsound.
`wait_for` cancels the *await*; it cannot cancel the *thread*. The worker keeps its executor slot
until the socket actually times out (123 s), while the next 1 Hz tick starts another one.
`wait_for` bounds latency and **accelerates** slot exhaustion. Only safe once A caps the socket.

---

## 5. Ordering — what lands first, and is the system better or merely different?

**Land A first, alone, as its own PR.**

**Better, not merely different — and I can state the ledger precisely.**

*Strictly better:*
- Refused-cascor outage removed: 3.003 s → 0.002 s per call (measured); 8-concurrent 24.05 s → ~16 ms.
- Black-hole blast radius per call 123 s → 20 s, at **every one of the 42 unguarded sites and 45
  client sites simultaneously**, including the 37 that B does not touch.
- Bounds the a2wsgi thread-parking window (N4/anchor 12) by the same factor, for free.
- Makes B and D *safe*: it caps how long any thread can hold one of the 20 executor slots, which is
  the precondition for U3 not biting.
- Zero new code paths, zero new modules, zero schema change, zero behavioural change while cascor
  is healthy.

*Regressions introduced (the honest side):*
- A cascor call that legitimately takes 10-30 s now fails instead of succeeding. Per N3, **no such
  caller exists**: canopy's own client budgets top out at 7 s for control/snapshot POSTs, 12 s for
  file import, 17 s for URL import; only `/api/train/restart` allows 30 s and that budget is
  consumed by canopy's own 15 s `RESTART_STOP_WAIT_TIMEOUT_SECONDS` await loop, not one HTTP call.
  I checked the two plausibly-slow upstream ops: `save_snapshot`/`load_snapshot`
  (`adapter.py:2239, :2264`) are reached from `/api/v1/snapshots` whose browser budget is 7 s.
  `import_dataset` is **not** on the adapter at all (no cascor call).
- Retries drop 3 → 1, so a cascor that returns two consecutive retryable 5xx now surfaces an error
  toast where it previously recovered silently. I judge this an acceptable, visible trade against a
  whole-service outage, and `retries=1` (not 0) is chosen precisely to keep the first, free retry.

**Then B** (5 lines, keeps the loop alive for the probe and always-on paths), **then C** (1 line +
2 in juniper-deploy, stops health lying), **then D** as a tracked follow-up.

If only one thing can ship this week, ship A. If two, ship A + B.

---

## 6. What this does NOT fix — explicitly

1. **The black-holed cascor case is NOT fixed.** A takes it from 123 s to 20 s per call. With five
   always-on pollers the loop is still saturated and canopy is still effectively down. A+B keeps
   `/v1/health/live` and the pure-async routes answering, but the 37 sites in D still freeze the app
   for up to 20 s whenever a user or a poller touches them. **Fully closing the black-hole case
   requires D. I am not claiming otherwise.**
2. **A cascor that is up but genuinely slow** (say 8 s/call) is untouched by A — 8 s is inside the
   new budget — and 37 sites still block on it.
3. **The 42 sites remain structurally sync-in-async.** The next slow upstream re-opens this defect.
   A is a blast-radius cap, not a structural fix.
4. **The WS control endpoint** (`main.py:895-907`, six unguarded control calls) is not touched by
   A+B; a stalled control call still blocks the loop for up to 20 s.
5. **The a2wsgi `future.result()` no-timeout amplifier** (`a2wsgi/wsgi.py:215-219`) is third-party
   code and is not fixed — only its window is shortened.
6. **The ruff `ASYNC` gate stays blind** (N2). Nothing here teaches it to catch site 43. Only test
   T4 does.
7. **Multi-worker / horizontal scale** is not addressed and should not be (U2).

---

## 7. Tests

Layout: `src/tests/regression/` (33 files) and `src/tests/unit/` (132). `asyncio_mode = "auto"`
(`pyproject.toml:370`), so `async def` tests need no decorator. A module-scoped `client()` TestClient
fixture exists at `src/tests/conftest.py:529-540`. Precedent for a timing-based concurrency
assertion: `src/tests/unit/test_health.py:114 test_probe_runs_concurrently_not_serially_under_fanout`
— model the new test on it, including its "sanity-floor" assertion.

### T1 — event loop stays responsive (MUST FAIL today; the test that would have caught X7)

`src/tests/regression/test_event_loop_not_blocked_by_slow_cascor.py`

- Monkeypatch the module-global `main.backend` with a stub whose `is_training_active` does a real
  `time.sleep(2.0)` (blocking, **not** `asyncio.sleep`) and whose `backend_type` is `"service"`.
- Drive the app with `httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app))` — **not**
  starlette `TestClient`, which is synchronous and cannot express the race.
- `asyncio.gather()` a `GET /v1/health` and a `GET /v1/health/live`, timing the *live* leg
  independently with `time.monotonic()` inside its own coroutine.
- **Assert `/v1/health/live` completes in < 0.5 s** while `/v1/health` is in flight.
- Sanity floor (per the `test_health.py` precedent): assert the `/v1/health` leg took ≥ 1.5 s, so a
  stub that silently stopped sleeping cannot vacuously pass the test.
- **Today**: the live leg waits behind the blocked loop, ≈ 2.0 s → **FAIL**. After change B → PASS.

### T2 — the client is constructed with a bounded budget (MUST FAIL today)

`src/tests/unit/backend/test_cascor_client_bounds.py`

- Construct `CascorServiceAdapter(service_url="http://127.0.0.1:1")` with **no** injected client.
- Assert `adapter._client.timeout <= 15`.
- Assert `adapter._client.session.get_adapter("http://x").max_retries.total <= 1`.
- **Today**: `timeout == 30`, `total == 3` → **FAIL**. After change A → PASS.
- Cheap, hermetic, no sockets. This is the test that pins A against a future well-meaning revert.

### T3 — measured worst-case cost against an unreachable upstream (MUST FAIL today)

`src/tests/regression/test_cascor_call_cost_bounded.py`, `@pytest.mark.regression`

- Helper: bind a loopback socket to port 0, read the port, close it → a guaranteed-closed port.
- Build a real adapter at that URL; time one `get_training_status()`.
- **Assert wall clock < 0.5 s.**
- **Today**: 3.003 s → **FAIL**. After A: 0.002 s → PASS.
- Optional second case (black hole): a thread that `accept()`s and never replies; assert
  `< CASCOR_CLIENT_TIMEOUT_SECONDS * 2 + 1`. Guard it with a generous `pytest.mark.timeout` and
  close all held sockets in a `finally` — a leaked accept-loop thread will hang CI.

### T4 — structural guard against site 43 (the durable gate ruff cannot provide)

`src/tests/regression/test_no_sync_backend_calls_in_hot_routes.py`

- `ast.parse("src/main.py")`; find async functions whose decorators name a route in a pinned
  hot-path allowlist: `/health`, `/api/health`, `/v1/health`, `/v1/health/ready`, `/api/status`,
  `/api/network/stats`.
- Assert **zero** `backend.*` / `backend._adapter.*` / `backend._demo.*` calls in those bodies that
  are not the first positional argument of an `asyncio.to_thread(...)` call.
- **Must be nested-function aware** — `/api/state` (`main.py:1237-1239`) puts its backend calls in a
  local `_fetch_live_status_and_params` that is then `to_thread`-ed. A naive walker false-positives
  there; I hit exactly this while verifying anchor 8 (my first scan reported 50, the correct figure
  is 42). Treat calls inside a nested `def` that is handed to `to_thread` as guarded.
- Scoped to the hot-path set on purpose: a repo-wide version would fail on all 42 sites and get
  waived. Widen the allowlist as D lands.
- **Today**: fails on 5 sites. After B → passes.

### T5 (optional) — `/dashboard/*` survives a stalled backend

Assert the a2wsgi-mounted dashboard still serves while a backend call is blocked. Higher cost and
more fragile; note as a follow-up, not a gate.

### Coverage-gate guardrails (`.github/workflows/ci.yml:244-261`)

The blocking per-file gate is **≥ 90% statement coverage per source file and ≥ 95% pooled per
packaged sub-module**, enforced by `juniper-coverage-gap-map --enforce`. Therefore:

- **Do not add a new module under `src/` for this fix.** A small new helper module with two
  uncovered branches fails the 90% gate on its own. Keep T4's AST logic inside the *test* file.
- New constants in `src/canopy_constants.py` are module-level assignments executed on import — no
  coverage risk.
- Change A adds no branches. Change B adds none (it rewrites expressions in place). This fix is
  coverage-neutral by construction, which is a deliberate property of choosing it.
- `src/main.py` is already in the measured tree; the 5 edited lines are on existing covered paths.

---

## 8. Risks and guardrails — what a careless implementer gets wrong

| # | Trap | Why it bites | Guardrail |
|---|---|---|---|
| **R1** | Writing `asyncio.to_thread(backend.is_training_active())` — **with parens** | Calls the blocking function on the loop, then hands `to_thread` a `bool`. Re-blocks exactly as before, and every existing test still passes because the *value* is right. Completely silent. | Must be `to_thread(backend.is_training_active)`, no parens. T1 catches it; nothing else does. |
| **R2** | `from main import backend` or binding it in a default arg / closure at import | `backend` is `None` at `main.py:480` and **reassigned at `main.py:3722`** on model swap (N5). A captured reference goes stale after any swap. | Reference the module global inside the handler at call time, as the existing `main.py:3553` site does. |
| **R3** | Choosing an aggressive `timeout` (2-5 s) "to be safe" | Breaks `save_snapshot` / `load_snapshot` on a large network — a **new** failure mode, in the class this lens exists to prevent. | Keep ≥ 10 s. N3 shows 10 s already exceeds every caller's patience except restart's aggregate. |
| **R4** | `retries=0` instead of `retries=1` | Identical refused-case cost (0.003 vs 0.002 s — the first retry's backoff is zero), but throws away all transient-5xx and cascor-restart resilience for nothing. | `retries=1`. Pin it in T2 as `<= 1`, and say why in the constant's comment. |
| **R5** | "The circuit breaker already handles this" | U1. Reviewer-plausible, and it leaves the hole. | Reject in review; cite `circuit_breaker.py:96`. Worth a comment at adapter `:1089` noting the sibling's breaker does **not** make it non-blocking. |
| **R6** | Landing D (37 `to_thread` sites) **before** A | U3: 20 executor slots, 123 s holds, plus the 30 pre-existing `to_thread` sites (snapshot file I/O) competing for the same pool. Converts the outage into a slower, harder-to-diagnose one and starves unrelated paths. | **A must land first.** Once the socket is capped at 10 s, worst-case slot occupancy drops 6x. If D ever lands broadly, size the executor explicitly via `loop.set_default_executor(...)` in the lifespan rather than relying on the 20-slot default. |
| **R7** | Breaking the `client=` injection seam at adapter `:507` | Tests inject fakes through that parameter; rewriting it to always construct a real client breaks a large swathe of the unit suite. | Preserve `client or JuniperCascorClient(...)` exactly; only add kwargs to the constructed branch. |
| **R8** | "Simplify" `/v1/health` by reading the `training_state` global instead of the backend | Tempting (1 line, no thread) but it **changes the value**. `src/tests/integration/test_main_coverage.py:1070 test_health_training_active_after_start` starts training in demo mode and asserts `data["training_active"] is True`; demo's `is_training_active` reads `self._demo.get_current_state()` in-memory, which the relay-fed global need not match. Also a silent API contract change for anything scraping `/v1/health`. | Keep `backend.is_training_active`, just move it off the loop. Change B is value-preserving by design — that is why it breaks zero tests. |
| **R9** | Repointing the Dockerfile healthcheck (C) without juniper-deploy | `juniper-deploy/docker-compose.yml:732` and `:814` still probe `/v1/health` with `timeout=5`; the compose stack keeps reporting canopy unhealthy and the fix looks like it did nothing. | Land C as a two-repo change, canopy first, or not at all. |
| **R10** | Trusting `ruff --select ASYNC` to have caught / to catch this | It is enforced in pre-commit and **passes green on the defect** (N2). A pre-commit run proves nothing here. | T4 is the gate. Say so in the PR body so the next author does not assume lint covers it. |

### Is `to_thread`'s 20-slot executor a new bottleneck?

**Yes — but only if B/D land without A, and A is what removes it.**

Verified: `min(32, cpu_count + 4)` = **20** on this host, and it is *shared* with the 30 `to_thread`
call sites `main.py` already has (snapshot file I/O, path resolution, dataset staging). Arithmetic
with today's unbounded client: five always-on pollers at up to 1 Hz, each holding a slot for 123 s,
exhaust 20 slots within ~4 s of a black-hole event — and then starve the *snapshot* paths that share
the pool. With A at `timeout=10, retries=1`, a slot is held at most 20 s, so steady-state occupancy
for the five pollers is bounded and the pool has headroom. Cross-check: a2wsgi's separate 10-thread
pool (`a2wsgi/wsgi.py:153-160`) is unaffected by A directly but its `future.result()` parking window
shrinks with the loop-stall window.

If D is ever landed in full, set the executor size explicitly at startup rather than inheriting 20.
Not needed for A+B.

---

## 9. Strongest objection to my own top pick

**Objection**: *A is a timeout tweak dressed up as a fix. It leaves 42 sync-in-async call sites
untouched, so the defect class is fully intact — you have narrowed the window, not closed the hole.
Worse, it makes the remaining defect harder to find: a 20 s freeze reads as "canopy feels sluggish"
and gets triaged as a perf niggle, whereas today's 123 s total blackout is unmissable and would have
forced the structural fix. You are trading a loud bug for a quiet one, and quiet bugs live for
years.*

I think this objection is **correct about the mechanism and wrong about the decision**, for three
reasons I can defend:

1. **A is the only change with no per-site escape.** Every alternative is an enumeration that the
   43rd handler will miss — and this repo has already demonstrated that failure mode twice: the
   `to_thread` guard was applied at 21 sites and skipped 42, and the enforced ruff `ASYNC` gate
   reads green on the defect (N2). A binds at the single seam all 45 client calls funnel through.
2. **The objection's own remedy depends on A.** Landing the structural fix (D) without a socket cap
   trades a loop-blocking outage for an executor-exhaustion outage (U3) that *also* starves the
   unrelated snapshot paths — strictly harder to diagnose than what we have. A is the precondition,
   not the alternative.
3. **The "quiet bug" risk is real and is what T4 is for.** I accept the objection's core worry
   enough to make T4 a required gate rather than a nice-to-have: it fails the build the moment a
   hot-path route grows a new unguarded `backend.*` call, which is the specific way this would
   silently regrow.

Where I concede: **the black-holed case is not fixed by anything I have ranked 1-3, and I have not
proposed a small fix that closes it.** If the operating environment makes black-holing likely — a
hung cascor process, a dropping firewall, a container paused rather than stopped — then A+B is
insufficient and D is not optional, and I would want that stated in the PR body rather than
discovered later. My lens produces the best available *this week*; it does not produce a complete
fix, and I would rather say so than ship A and call X7 closed.
