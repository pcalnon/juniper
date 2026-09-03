# X7 fix design — author F2

**Lens**: fix the class, not the instance; make recurrence mechanically impossible.
**Repo inspected read-only**: `/home/pcalnon/Development/python/Juniper/juniper-canopy` @ `9fbf4b8` (main, clean).
**Env**: `JuniperCanopy1` (py3.13.13), `juniper-cascor-client` 0.7.0, ruff 0.15.13, mypy 1.20.0.
**Status**: design only. No repository file was modified.

---

## 0. The finding that reframes this entire defect

Before any design: **the enforcement already exists, is blocking in CI, is green, and is
structurally incapable of seeing X7.**

- `.pre-commit-config.yaml:123-131` wires the ruff hook `ruff-async-audit`
  ("Async-route audit (BUG-JD-10 class)") with `args: [--select, ASYNC]`,
  `files: ^src/.*\.py$`, `stages: [pre-commit, manual]`.
- `.github/workflows/ci.yml:106` runs `pre-commit run --all-files --show-diff-on-failure`,
  and ci.yml:965/986 makes the `pre-commit` job a hard gate on the Quality Gate rollup.
  So the hook is **blocking on every PR**.
- Verified by direct execution:

  ```
  $ ruff 0.15.13 check --isolated --select ASYNC --no-cache src/
  All checks passed!
  ```

  `--isolated` deliberately discards `pyproject.toml`'s `[tool.ruff.lint.per-file-ignores]`,
  so this is not a suppression artifact. The ruleset finds **zero** violations while **40
  unguarded blocking call sites** sit in async route handlers.

**Why it is blind, and why adding rules will not help.** Ruff's `ASYNC2xx` family matches a
*hardcoded list of known-blocking callees* — `requests.*`, `httpx.Client.*`, `open()`,
`time.sleep`, `subprocess.*`, `os.path.*`. `backend.get_status()` is an opaque bound-method
call on a module global. No general static rule can know it performs HTTP. This is not a ruff
bug; it is the rule family's design boundary. **Ruff will never catch this class.**

This is precisely the failure mode the brief warns about — *an enforcement with a large blind
spot is worse than none, because it licenses complacency.* It has already happened here. The
hook exists, the plan `ASYNC_ROUTE_AUDIT_HOOK_MIGRATION_PLAN.md` is cited in
`pyproject.toml:450`, the Phase-0 enumeration is cited at `pyproject.toml:470`, and Phases 2-4
were never completed. X7 is the sixth recorded sighting of a defect that has a *stalled
enforcement rollout already pointed at it*.

Everything below is designed around one consequence: **the enforcement must not be a
name-matching lint. It must be a rule the code's own shape makes decidable.**

---

## 1. Anchor verification

| # | Anchor as briefed | Verdict | Evidence |
|---|---|---|---|
| 1 | `src/main.py:4419` — uvicorn **workers=1** | **CORRECTED** | Line 4419 is `uvicorn.run(app, host=host, port=port, log_level="info" if debug else "warning")`. There is **no `workers` kwarg at all**. Effect is the same (one process), mechanism is not — see §1.1. |
| 2 | no request timeout | **CONFIRMED** | No `timeout_keep_alive`/`timeout_graceful_shutdown` beyond defaults; no per-request deadline anywhere. |
| 3 | 72 routes, **all** `async def` | **CONFIRMED** | AST sweep of all non-test `src/**/*.py`: `async=72, sync=0`, all in `src/main.py`. |
| 4 | Zero `run_in_threadpool` in `src/` | **CONFIRMED** | `grep -rc` → no non-zero file. |
| 5 | asyncio executor = 20 | **CONFIRMED, with caveat** | `min(32, (os.process_cpu_count() or 1) + 4)`; `process_cpu_count()==16` here → 20. **Host-dependent**, and *not* shrunk by the compose CPU quota (`cpus: 1.0`-`4.0` is a quota, not affinity). See §7.1. |
| 6 | `main.py` uses `asyncio.to_thread` **30 times**, correctly | **CONFIRMED** | 30 total; 24 inside route handlers. The `/api/state` exemplar and its comment are at `src/main.py:1234-1239`. |
| 7 | **41** unguarded `backend.*` calls in async routes | **REFINED — the true figure is 40** | See §1.2. The naive count of 41 mis-scores the 2 correctly-guarded `/api/state` calls as unguarded, and omits the 1 unguarded websocket site. |
| 8 | Circuit-breaker coverage **5 of 45** | **CONFIRMED exactly** | 45 `self._client.` sites; `_cb.call` at `cascor_service_adapter.py:1970, 1980, 2099, 2117, 2130`. |
| 9 | `is_training_in_progress()` bare vs `get_training_status()` breakered | **CONFIRMED** | Bare at `cascor_service_adapter.py:1089-1091`; breakered sibling at `:1968-1977` with `fallback=lambda: {"is_training": False, "error": "circuit open"}`. |
| 10 | `/health`, `/v1/health`, `/v1/health/ready` use the unprotected one | **CONFIRMED, chain traced** | `src/main.py:1050 / 1076 / 1133` → `backend.is_training_active()` → `src/backend/service_backend.py:160-161` → `self._adapter.is_training_in_progress()` → bare `self._client.get_training_status()`. |
| 11 | `cascor_service_adapter.py:507` builds client with no overrides → `timeout=30, retries=3`, backoff 0.5 | **CONFIRMED** | Line 507 exactly; `JuniperCascorClient.__init__` defaults inspected live: `timeout=30, retries=3`; `DEFAULT_BACKOFF_FACTOR=0.5`. |
| 12 | Black-holed socket ⇒ **~123 s per call** | **CONFIRMED arithmetically** | 4 attempts × 30 s + backoff (0.5+1+2) = **123.5 s**. |

### 1.1 Correction: `workers=1` is not what the code says, and the difference matters

`src/main.py:4419` passes **an app object**, not an import string. uvicorn cannot fork workers
from a live object — `workers>1` requires `uvicorn.run("main:app", …)`. So "just raise the
worker count" is not a one-line mitigation; it is a launch-form change that also has to survive
the Dash/`WSGIMiddleware` mount at `src/main.py:493` (each worker would get its own Dash server
and its own in-process `training_state`, which is a correctness change, not a scaling knob).

**Additional latent defect found while verifying this.** `conf/app_config.yaml:400-401`
declares:

```yaml
  production:
    workers: 4
    worker_class: uvicorn.workers.UvicornWorker
```

Nothing reads it. A grep for any `workers` key consumer across `src/config/` and `src/*.py`
returns only unrelated cascor-worker endpoints. **An operator reading the config believes canopy
runs 4 workers; it runs 1.** This is not X7, but it is why X7 survived five reviews: the
config asserts the very redundancy whose absence is the root cause. Worth its own one-line issue.

### 1.2 Correction: the count is 40, and the way it is counted is the crux of the whole design

I ran three successively more faithful AST passes over `src/main.py`. The disagreement between
them is the single most important input to the enforcement design.

**Pass 1 — naive (count `backend.*(...)` Call nodes in async routes):**
50 sites. Classified: **41 HTTP-route**, 7 websocket-route, 2 `backend._demo.*` (in-process, non-blocking).
The briefed 41 reproduces exactly under this definition.

**Pass 2 — lexical offload scoping (a call is guarded iff it sits inside a `to_thread(...)` node):**
`guarded=0, unguarded=50`. **Zero.** Despite 24 `to_thread` calls in routes.

**Pass 3 — closure-aware (resolve `to_thread(name)` to the nested `def name` and treat its body
as offloaded; also resolve lambdas):**
`guarded=8, unguarded=40` — 39 HTTP + 1 websocket (`websocket_training_endpoint`,
`src/main.py:705`). The 8 guarded are the 6 in `websocket_control_endpoint` (`:895-907`) and the
2 in `get_state` (`:1237`).

**Why Pass 2 returns zero, and why that is the finding.** The repo's *correct* idiom never
produces a `Call` node inside the `to_thread(...)` node. Inventory of the 24 in-route offload
arguments:

- **13 bare-attribute references** — `await asyncio.to_thread(backend.get_metrics_history, …)`.
  The backend access is an `ast.Attribute`, not an `ast.Call`. **A call-site checker never sees
  it at all** — it neither flags nor credits these.
- **8 named closures** — `_fetch_live_status_and_params`, `_backend_snapshot_inventory`,
  `_load_snapshot_history`, `_backend_snapshot_detail`, `_find_snapshot_file` (×2),
  `_execute_command`, `_classify_import_url_target`. The call lives in a nested `def`; the
  `to_thread` references it by name.
- **3 non-backend** — `Path(_snapshots_dir).resolve`, `Path(_snapshots_dir).mkdir`,
  `snapshot_path.resolve`.

So the true accounting is roughly **61 backend touchpoints in routes: ~21 guarded (8 via closure
+ 13 via bare attribute), 40 unguarded.**

**The consequence for enforcement.** A naive AST rule of the form *"a `backend.*()` call must be
lexically inside a `to_thread(...)` argument"* would emit **50 findings, 8 of them false
positives on code that is already correct**, and would be **silently blind to 13 correct
offloads**. That checker is unshippable: 16% false-positive rate on the exemplar the codebase
holds up as the right pattern. Any design that reaches for that rule has to be rejected. This is
the load-bearing reason my design changes the *shape* of the code before it writes the checker
— see §4.

### 1.3 New anchors found during verification (not in the brief, all load-bearing)

**(a) `src/main.py:480` is `backend = None`.** The single object through which all 40 blocking
calls flow is an untyped module global. mypy run on `src/main.py` with `attr-defined` enabled
produces **57 errors, all of the form `"None" has no attribute X`**. So the type system carries
*zero* information about `backend`.

**(b) mypy cannot help as configured.** `.pre-commit-config.yaml:192-197` disables
`attr-defined`, `return-value`, `arg-type`, `assignment`, `misc`. Those are exactly the five
codes that would fire on "coroutine used where a dict was expected". **Any design claiming
"mypy will catch the un-awaited calls" is wrong twice over** — the codes are off, and the type
is `None` so mypy would say "None has no attribute" long before it reasoned about coroutines.
I held this belief while drafting and had to discard it; recording it because it is the most
attractive wrong answer available here.

**(c) The client retries mutating verbs.** `juniper_cascor_client/constants.py:37` —
`RETRY_ALLOWED_METHODS = ["GET", "POST", "DELETE", "PUT", "PATCH"]`. A `start_training` POST can
be delivered **up to 4 times** on 429/502/503/504. Lowering `retries` is therefore a
*correctness* change, not only a latency one.

**(d) The client's connection pool is 10.** `DEFAULT_POOL_MAXSIZE = 10`, one `requests.Session`,
default `pool_block=False`. The 11th concurrent call through the offload path creates a
throwaway connection and emits urllib3's "Connection pool is full" warning. Not a deadlock, but
connection churn under exactly the fan-out this fix enables. Bounds the semaphore choice in §3.2.

**(e) `src/health.py` already made this migration, and documented the reasoning.** Lines 15-27:
`probe_dependency` was converted **away** from `asyncio.to_thread` to native `httpx.AsyncClient`,
because the offload "was correct (it didn't block the event loop) but consumed one of the
default 32 worker threads per concurrent probe" and would exhaust under fan-out. The repo has
already ruled that **thread-offload is a bounded mitigation and native async is the endgame.**
(Its "32" is slightly off — the real default is `min(32, cpu+4)` = 20 here — but the reasoning
stands.) My phasing in §6 is consistent with this precedent rather than contradicting it.

**(f) `BackendProtocol` exists and is already bypassed.** `src/backend/protocol.py` defines a
20-method `typing.Protocol` whose stated purpose is "main.py to hold a single
`backend: BackendProtocol` reference". Of the 48 non-demo backend calls in routes, **36 use the
protocol surface, 10 reach through `backend._adapter.*`, and 2 reach through
`backend._adapter._client.*`**. The single choke point *was designed*; it is being circumvented
at 12 sites. This is the asset the class fix should restore, not a new abstraction to invent.

---

## 2. What the class actually is

Stated precisely enough to be enforceable — the defect is **not** "someone forgot `to_thread`":

> In `src/main.py`, an `async def` route handler invokes a **synchronous method whose
> implementation performs unbounded network I/O**, on a process with exactly one event loop
> thread and no request deadline.

Four independent properties combine, and the fix should break more than one:

1. **Unbounded duration** — `timeout=30 × retries=3` ⇒ 123 s (`cascor_service_adapter.py:507`).
2. **No isolation** — the call runs on the loop thread (40 sites).
3. **No redundancy** — one process, one loop (`src/main.py:4419`).
4. **No failure memory** — the breaker guards 5 of 45 client calls, and the health path uses one
   of the 40 unguarded ones.

And a fifth that makes it self-amplifying: `src/frontend/` makes **47 loopback HTTP self-calls**
(`grep -c _api_url`) from Dash callbacks running on the a2wsgi thread pool. A blocked event loop
parks every in-flight self-call at once. See §8.

---

## 3. The class fix

Four layers. Layers 0 and C are small and independently valuable. Layer A is the one that makes
the enforcement in §4 decidable. Layer B closes the breaker gap by construction.

### 3.0 Layer 0 — bound the blast radius once, at construction

**File**: `src/backend/cascor_service_adapter.py:507`; constants in `src/backend/constants.py`
(`BackendConstants`).

```python
self._client = client or JuniperCascorClient(
    base_url=service_url,
    api_key=api_key,
    timeout=BackendConstants.CASCOR_CLIENT_TIMEOUT_SECONDS,   # 5.0
    retries=BackendConstants.CASCOR_CLIENT_RETRIES,           # 1
)
```

Worst case falls from **123.5 s → 10.5 s** (2 attempts × 5 s + 0.5 s backoff). Six lines
including the constants. It fixes nothing structurally — it multiplies the harm by 0.085.

Two notes that make this more than a knob-twiddle:

- Per §1.3(c), dropping `retries` 3 → 1 halves the worst-case duplicate delivery of
  `start_training` / `stop_training` POSTs from 4 to 2. That deserves its own regression test
  asserting the retry count reaches the client, because it is a behavioural change that a future
  "let's be more resilient" PR will silently revert.
- A **second, faster client** for liveness use (`timeout=2.0, retries=0`) is worth having, wired
  only into the health path of §3.3. Probes and operations should not share a deadline.

### 3.1 Layer A — the choke point: make the boundary async so a handler *cannot* block

The lens rejects "a helper everyone must remember to call". A helper is a convention; a
convention decays. The mechanism has to be that **the old way stops working.**

`BackendProtocol` is already the declared door (§1.3(f)). Make it an **async** door.

**New file `src/backend/offload.py`** (~60 lines with canopy's banner header):

```python
_CASCOR_SEMAPHORE = asyncio.Semaphore(BackendConstants.CASCOR_OFFLOAD_CONCURRENCY)

async def offload(fn: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Run a blocking backend call off the event loop, bounded."""
    async with _CASCOR_SEMAPHORE:
        return await asyncio.to_thread(fn, *args, **kwargs)
```

**New file `src/backend/async_backend.py`** (~200 lines): `AsyncBackend`, a thin façade holding
a `BackendProtocol` and exposing every method as `async def`:

```python
class AsyncBackend:
    def __init__(self, sync: BackendProtocol) -> None:
        self.sync = sync            # escape hatch for non-loop contexts (lifespan, tests)

    async def get_status(self) -> StatusResult:
        return await offload(self.sync.get_status)
    ...
```

**`src/main.py:480`** becomes `backend: AsyncBackend` (assigned in lifespan), and the 40 sites
become `await backend.get_status()`.

**`src/backend/protocol.py`**: promote the 12 reach-through targets
(`get_canopy_params`, `get_network_data`, `get_stream_health`, `save_snapshot`, `load_snapshot`,
`get_remote_worker_status`, `connect_remote_workers`, `start_remote_workers`,
`stop_remote_workers`, `disconnect_remote_workers`, `get_worker_stats`, `list_workers`) onto
`BackendProtocol` and implement them on `ServiceBackend` / `DemoBackend`. This is what turns the
enforcement rule *"no `_adapter` / `_client` attribute access in `src/main.py`"* into a
zero-false-positive check: there is nothing legitimate left to reach through for.

**Why a façade rather than making `CascorServiceAdapter` itself async**: the adapter has 60
public methods and is also called from non-loop contexts (`_ServiceTrainingMonitor`, the relay
supervisor, lifespan). Making it async forces those onto a loop too, and the mock-seam
consequences across `src/tests/unit/backend/` (7 adapter test modules) are far larger. The
façade confines the async boundary to exactly where routes touch it.

**What this buys the enforcement.** After Layer A, `backend.get_status()` without `await` yields
a coroutine. The static rule collapses from *"is this call transitively offloaded, accounting for
closures and bare-attribute references?"* — undecidable in practice, 16% FP in measurement — to
**"is the parent node an `ast.Await`?"** One token, syntactically local, no resolution, no
false positives. **This is the point of Layer A.** It is not refactoring for elegance; it is
refactoring to make a sound checker exist.

Do **not** implement the façade as a `__getattr__` proxy. It is fewer lines and trivially
coverage-complete, but it erases the method names, and the names are what the checker and the
reader use. Pay the explicit-methods cost; see §5 for how to cover them in one table-driven test.

### 3.2 Layer B — the breaker belongs at the client, not at 5 of 45 call sites

**New file `src/backend/breaking_client.py`** (~90 lines): a wrapper installed at
`cascor_service_adapter.py:507` that proxies attribute access and routes every callable through
the existing `CircuitBreaker`:

```python
class CircuitBreakingClient:
    def __init__(self, inner, breaker): ...
    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr
        @functools.wraps(attr)
        def guarded(*a, **kw):
            return self._breaker.call(lambda: attr(*a, **kw), fallback=_RAISE)
        return guarded
```

Coverage goes **5/45 → 45/45 by construction**, and — crucially — it cannot be un-done by a
future author adding call site 46. `CircuitBreaker` already uses a `threading.Lock`
(`src/backend/circuit_breaker.py:45`), so it stays correct once calls execute on executor
threads.

The 5 existing `_cb.call` sites carry **per-method fallbacks** (`{"is_training": False, "error":
"circuit open"}`, `{}`) that a generic proxy cannot know. Keep those five as they are — they now
double-guard, which is harmless because `CircuitBreaker.call` on an open circuit is a
short-circuit, not a state mutation — or move their fallbacks into a small
`FALLBACKS: dict[str, Callable]` consulted by the proxy. Either is fine; the second is cleaner
and is what I would ship. On an open circuit with no registered fallback the proxy must raise
`JuniperCascorClientError`, because all 60 adapter methods already catch that type; raising
anything else converts a handled degradation into a 500.

### 3.3 Layer C — health endpoints must not depend on a remote service being fast

`/health` (`:1050`), `/v1/health` (`:1076`) and `/v1/health/ready` (`:1133`) each call
`backend.is_training_active()`, which reaches cascor over the network on the *unbreakered* path.
An orchestrator's liveness view of canopy is therefore a function of cascor's latency. Under the
verified numbers, cascor black-holed makes canopy's own `/v1/health` take ~123 s, well past any
sane probe timeout — so **cascor being slow gets canopy restarted.**

Fix: serve `training_active` in the health payload from a TTL-cached value (2 s) refreshed by
the existing training relay, never by a synchronous call inside the probe. ~30 lines. This is the
highest value-per-line change in the whole design and depends on nothing else.

---

## 4. Enforcement

Given §0, the design constraint is: **no name-matching lint, no rule with a blind spot large
enough to license complacency, and every blind spot written down where the next author will read
it.**

### D1 — primary static gate: `src/tests/regression/test_async_route_blocking_guard.py`

An AST test over `src/main.py`. The repo already has AST-driven tests to model on
(`src/tests/regression/test_numeric_input_step_grid.py`,
`src/tests/unit/backend/test_cascor_service_adapter_v1_prefix_regression.py`,
`src/tests/unit/frontend/test_meta_parameters_handlers.py`).

Three predicates, all syntactically local, all decidable:

- **R1 — no reach-through.** No async route function may contain an attribute access on
  `backend` whose dotted path includes `_adapter` or `_client`.
  *Currently 12 violations; zero after Layer A's protocol promotion.*
- **R2 — every backend call is awaited.** Any `ast.Call` whose receiver root is `backend` must
  have an `ast.Await` parent.
  *Currently 40 violations; zero after Layer A's migration.*
- **R3 — no sync HTTP in the API layer.** No module under `src/` outside an explicit allowlist
  (`src/frontend/**`, while Option B stands) may import `requests`.

**Vacuous-pass guard — mandatory, not optional.** The test must assert
`len(routes) >= 70 and len(backend_calls) >= 30` before evaluating R1-R3. Without it, renaming
the `app` global, moving routes out of `main.py`, or changing the decorator form makes the
checker scan zero functions and report success. That is the single most likely way this
enforcement decays into theatre, and it is a known local failure class
(`reference_vacuous_pass_check_class`). R1-R3 must also **fail loudly** if a route is found
outside `src/main.py` rather than silently skipping it.

**What D1 detects**: a new `backend.*` call in an async route that isn't awaited; any new
`_adapter`/`_client` reach-through; a new `requests` import in the API layer. That is the exact
edit shape of all 40 current sites and of the next one.

**What D1 CANNOT detect** — this list belongs verbatim in the test's module docstring, because
an unstated blind spot is what turned the ruff hook into a complacency license:

1. **Blocking reached through any name other than `backend`.** `src/backend/redis_client.py`
   (553 lines), `cassandra_client.py` (504), `data_adapter.py` (552) are all synchronous and all
   importable. A new `redis_client.get(...)` in a route is invisible to R1-R3.
2. **Blocking inside an `async def` adapter method.** Layer A guarantees the *route* cannot
   block; it does not stop someone writing `async def foo(self): return self._client.get()` in
   the adapter. D1 is silent there.
3. **Dash callbacks in `src/frontend/`.** They run on a2wsgi threads, a different pool.
   Deliberately out of scope — and note R3 must *allowlist* `src/frontend/` precisely because
   Option B's self-calls live there.
4. **CPU-bound work on the loop.** A large numpy transform in a route is indistinguishable from
   fast code by AST.
5. **Dynamic dispatch.** `getattr(backend, name)()`, a handler dict, `functools.partial`.
6. **Anything outside `src/main.py`.** Sound today (72/72 routes are there) but silently
   scope-limited tomorrow — which the vacuous-pass guard converts into a loud failure.

Blind spots 1, 2, 4 and 5 are real and are **not** covered by ruff either. They are the reason
D1 alone is insufficient and D2 is not optional.

### D2 — runtime backstop for the class D1 cannot see

**(a) Loop-lag monitor.** In `lifespan`, gated on `settings.debug or
CANOPY_LOOP_LAG_MONITOR=1`: a task that sleeps 250 ms in a loop and records
`actual - expected` into `juniper_canopy_event_loop_lag_seconds`, registered via
`register_or_reuse` from `juniper-observability` per the ecosystem contract; WARNING above
threshold. Plus `loop.set_debug(True)` in dev so asyncio's own `slow_callback_duration` logging
names the offending callback. ~50 lines.

- **Detects**: *any* loop stall regardless of mechanism — the entire blind-spot list above.
- **Cannot**: fail CI by itself; attribute a stall to a call site (the monitor sees the stall,
  not the culprit — asyncio debug mode names it, at a perf cost, hence dev-only); fire at all if
  the offending path is never exercised.

**(b) The one check that tests the actual property.** An integration test that starts the app
against a stub cascor that sleeps 3 s, fires `/v1/health` and a pure-async control route
concurrently, and asserts **the control returns in < 500 ms**. ~90 lines.

This is the only gate in the design that asserts *"the event loop does not stall"* rather than a
syntactic proxy for it. It would have caught X7 with no knowledge of `backend`, `to_thread`, or
any naming convention — and it is the check that will still be true after someone introduces
`redis_client` into a route. **If only one enforcement can be built, build this one.**
D1 is still worth more in aggregate because it fails at the *edit* rather than the *behaviour*,
and scales to 40 sites and to authors who never run the integration lane locally.

### D3 — wiring

Add D1 as a `local` pre-commit hook (so it fails before CI, alongside the existing ruff hook)
**and** confirm it is collected by ci.yml's unit lane. Do not assume collection: the ecosystem
has a live trap where CI test lists are hand-maintained and new suites do not self-register
(`reference_juniper_ml_ci_test_list_is_hand_maintained`). Verify by reading ci.yml's pytest
invocation, not by reasoning that it lives under `src/tests/`.

Also: **update `pyproject.toml:445-451`'s ruff comment block** to record that the ASYNC ruleset
is structurally blind to this class, and that D1 is the check that covers it. Leaving the block
saying "BUG-JD-10 class prevention" unqualified is how the next reviewer concludes the class is
already handled.

---

## 5. Sizing

| Layer | Files | Prod lines | Notes |
|---|---|---|---|
| 0 — bounded client | 2 modified | ~+8 | `cascor_service_adapter.py:507` + `BackendConstants` |
| A — offload helper | 1 new | ~+60 | canopy's banner header is ~25 lines of that |
| A — async façade | 1 new | ~+200 | 32 explicit `async def` methods |
| A — protocol promotion | 3 modified | ~+90 | `protocol.py` +12 stubs, `service_backend.py`, `demo_backend.py` |
| A — route migration | 1 modified | ~-25 net | 40 `await` insertions; 8 guarded sites lose their closures/`to_thread` |
| B — breakering client | 1 new, 1 modified | ~+90 / -20 | |
| C — health TTL cache | 1 modified | ~+30 | |
| D1 — AST guard | 1 new | ~+180 | incl. the six documented blind spots + vacuous-pass asserts |
| D2a — lag monitor | 1 modified | ~+50 | |
| D2b — integration test | 1 new | ~+90 | |
| D3 — wiring | 3 modified | ~+15 | pre-commit, ci.yml, pyproject comment |

**≈ 6 new files, 9 modified, ~+810 / -45 lines.**

**Test churn — the dominant and least certain cost.** 332 test files exist; **97 touch
`TestClient` or route paths**. Layer A changes the return type of every backend method, so any
test stubbing `backend` with `MagicMock` and asserting a route's JSON breaks unless the stub
returns awaitables. Mitigation: ship `src/tests/support/async_backend_stub.py` (an `AsyncMock`
double) plus a conftest fixture, so most sites change by swapping
`MagicMock()` → `make_async_backend()`. **Estimate 40-70 test files touched, mostly
mechanically.** I cannot tighten this without running the suite, which this design pass
deliberately does not do; treat the upper bound as the planning figure. This is the single
largest threat to the estimate and the main input to §9.

**Coverage gates — harder than briefed.** `ci.yml:255-262` runs
`juniper-coverage-gap-map --coverage-json reports/coverage.json --enforce`, which fails if
**any source file** is under **90% statements** *or* **any packaged sub-module pooled** is under
**95%**. This is not `src/frontend/`-specific; it applies to every new file. Consequences:

- `offload.py`, `breaking_client.py`, `async_backend.py` each need ≥90% **on their own**.
- For `async_backend.py`'s 32 near-identical methods that means **every method must execute**.
  This is the real argument for a `__getattr__` proxy (≈15 statements, trivially 100%) — and I
  am rejecting it anyway, because erasing the method names erases what the checker and the
  reader rely on. Resolve it instead with **one table-driven test** that iterates
  `BackendProtocol.__annotations__` / a declared method tuple, calls each façade method against
  an `AsyncMock` sync backend, and asserts delegation. One test, full coverage, and it doubles
  as a drift guard: adding a protocol method without a façade method fails it.

**Sequence-safety.** `.github/workflows/sequence-safety.yml` runs the AST symbol-loss screen.
Removing the 8 nested closures from `main.py` and relocating adapter surface will register as
symbol loss and need an `Allow-*` trailer — which must be **the last paragraph** of the commit
message or it registers as nothing (`reference_git_trailer_must_be_last_paragraph`). Verify with
`git log -1 --format='%(trailers:key=...)'`.

---

## 6. Phasing — and yes, enforcement lands first

**PR 1 — enforcement as a red ratchet (lands before any fix).**
D1 ships in **baseline mode**: the test compares the current violation set against a checked-in
`tests/data/async_route_blocking_baseline.json` listing exactly the 40 known sites, and asserts
`current ⊆ baseline AND len(current) <= len(baseline)`. It **passes today** (documenting the
debt) and **fails the moment anyone adds a 41st**. Ship D2a (lag monitor) and D2b (integration
test) in the same PR; D2b fails today, so it lands `@pytest.mark.xfail(strict=True)` and flips
in PR 6.

This answers the brief's question directly: **a baseline-ratchet enforcement can and should land
before the fixes; a clean-rule enforcement cannot, because §1.2 showed the clean rule has a 16%
false-positive rate against the pre-fix code shape.** The ratchet's own hazard is that a baseline
file is itself a complacency license if it is allowed to grow — hence the monotonic assertion,
and hence PR 6 deletes it.

**PR 2 — Layer 0 + Layer C.** Bounded timeouts, health de-cascored. ~45 lines, near-zero test
churn, no dependency on anything else. Worst case 123 s → 10.5 s, and canopy stops being
restarted for cascor's outages. Highest value per line in the design; ship it even if everything
below stalls.

**PR 3 — Layer B.** Breakering client at construction. 45/45 by construction. Independently
shippable; touches `src/tests/unit/backend/test_circuit_breaker*.py`.

**PRs 4-6 — Layer A, split three ways.**
4: `offload.py` + `async_backend.py` + protocol promotion, with the sync surface still reachable
(both calling conventions valid; nothing breaks).
5: migrate the 40 routes in ~3 batches of ~13, shrinking the baseline each batch.
6: remove the sync surface from `main.py`'s reach, **flip D1 from baseline mode to clean-rule
mode, delete the baseline file, flip D2b's xfail.**

**Never worse mid-way.** Every PR is independently green. The façade coexists with the sync path
through PR 5, so a half-migrated `main.py` is valid — the honest cost of that is two calling
conventions live simultaneously, which is the objection in §9. The only hard ordering constraint
is that D1's mode flip must be last.

---

## 7. Risks

### 7.1 `to_thread` relocates the bottleneck; it does not remove it

The executor is `min(32, process_cpu_count()+4)` — **20 here, host-dependent**, and *not*
shrunk by the compose CPU quota (verified: `os.process_cpu_count()` reflects affinity, not
cgroup quota; `deploy.resources.limits.cpus` is a quota). 41 concurrent offloads → 20 run, 21
queue.

But this is **strictly better than the status quo, and the difference is categorical**: the loop
stays responsive, so pure-async routes, `/metrics`, and WebSocket pings keep serving while
cascor-dependent routes queue. The failure mode degrades from *"the whole dashboard is dead"* to
*"the cascor-backed panels are slow"*. That is the actual product of this fix; the latency
numbers are secondary.

Per §1.3(e), the repo has already decided this ceiling is real, and that native async is the
endgame. The terminal state is an async transport in `juniper-cascor-client` (cross-repo, slow).
This design must not *require* it — but the façade in §3.1 is exactly the seam that would let it
land later as an implementation swap behind an unchanged interface.

### 7.2 `asyncio.wait_for` around `to_thread` does **not** cancel the thread

An obvious-looking addition — `await asyncio.wait_for(asyncio.to_thread(fn), timeout=…)` — frees
the *caller* but leaves the worker occupying its executor slot for the full socket timeout. A
deadline built that way **looks like protection and is not** — the same failure as the green ruff
hook, one layer down. Therefore: pool occupancy is bounded by **Layer 0's client timeout × the
semaphore**, and by nothing else. I deliberately do not put `wait_for` in `offload()`; adding it
would create false confidence for zero real bound.

### 7.3 The semaphore's size is a guess and should not be shipped as one

A semaphore of 8 bounds cascor's share and leaves ~12 slots for the filesystem offloads that
already use `to_thread` (snapshot I/O, `Path.resolve`). Without it, cascor can starve the
snapshot routes. Too small and it serializes the dashboard's own fan-out. **8 is not measured.**
It should be set by a PF-1-style measurement (`project_perf_lane_p1_and_pf1_2026-08-31`), not by
this document. Constraint from §1.3(d): keep it **≤ 10** to stay inside the client's
`pool_maxsize`, or the fan-out this fix enables produces connection churn and urllib3 warnings.

### 7.4 What the choke point breaks

- **Sync callers.** `lifespan`, `_ServiceTrainingMonitor` and the relay supervisor call the
  backend outside a loop context. Hence `AsyncBackend.sync` is retained as an explicit escape
  hatch — and R1/R2 must permit `backend.sync.*` while banning `backend._adapter.*`, which is
  why the escape hatch gets a public name rather than a private one.
- **Exception identity** — safe. `asyncio.to_thread` re-raises in the caller with the thread's
  traceback intact, so `except JuniperCascorClientError` in all 60 adapter methods still works.
- **ContextVars** — safe, and worth stating because it is the obvious fear.
  `asyncio.to_thread` propagates context via `contextvars.copy_context()`, so the
  `RequestIdMiddleware` `request_id` survives into the worker thread and log correlation is
  preserved.
- **Ordering.** Calls that were implicitly serialized by running on one thread now interleave.
  The two multi-call routes to check are `restore_snapshot` (`:2480-2626`, five backend calls
  including `reset_training` then `apply_params`) and `api_train_restart` (`:3617/3638`,
  `stop_training` then `start_training`). Sequential `await`s preserve their order; the risk is
  only if someone "optimizes" them into a `gather`. Worth an explicit comment at both sites.

### 7.5 Enforcement decay

The baseline file is the weak point (§6). Mitigations: the monotonic assertion; deletion in
PR 6; and the vacuous-pass guard in §4. If PR 6 never lands, the ratchet freezes the debt rather
than reducing it — see §9.

---

## 8. Engagement with the deferred design

Read: `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md`
(180 lines, Status: Deferred).

**Verdict: orthogonal in mechanism — my design neither supersedes nor implements it — but X7
satisfies its §6.1 trigger by a path the document does not model, and that section needs
correcting regardless of whether Option C ever ships.**

**Why orthogonal.** Option C removes the **Dash callback → loopback HTTP → route handler** hop.
X7 lives *inside* the route handler, in the **handler → cascor** hop. Option C does not touch it.
Worse, under that document's §5.2 bridge for "async handler from sync Dash callback"
(`asyncio.run(handler(...))` or a background-loop bridge), a blocking `backend.*` call still
blocks whatever loop the bridge runs on. **Option C inherits X7 unless X7 is fixed first.** My
fix is upstream of it, not a substitute for it.

**Where the document is wrong.** §6.1 names the trigger as *"concurrent-user dashboard exhausts
the Flask threadpool"* and dismisses it because *"today the dashboard is essentially
single-user."* That reasoning models exhaustion as a function of **user count**. It is a
function of **hold time × arrival rate**. The a2wsgi pool is 10; `src/frontend/` has **47
`_api_url` self-call sites**. When the event loop blocks, every in-flight self-call parks
simultaneously — so **one user on a 10-panel dashboard with cascor black-holed holds all 10
a2wsgi slots for the full 123 s.** §6.1 is reachable *today, with a single user*, by a mechanism
the document did not consider. That is a correction to the deferred design, not a fix to it.

**Is Option C now required?** **No — still deferrable, and more deferrable after this fix,** because
Layers 0 and A remove the unbounded hold time that makes §6.1 reachable. §6.2 (SLO contamination),
§6.3 (sub-500 ms refresh) and §6.5 (an incident hidden behind `requests.RequestException`) remain
untriggered.

**§6.4 is the one that has moved and should be re-measured.** The document estimated
*"~50 callsites of `patch("requests.get")`"* in §5.6. Measured today:
**354 `patch("requests.*")` sites in `src/tests/`** — roughly a **7× growth** since 2026-05-10.
§6.4's stated threshold is a *share of new tests*, which I have not measured, so this is not yet
a trigger — but it is the metric closest to firing, and the absolute number is now large enough
that Option C's migration cost has grown substantially while its benefit has not.

**Recommended edits to that document** (not made — design only): correct §6.1's mechanism to
hold-time-driven and note it is single-user-reachable; update §5.6's ~50 to the measured 354;
and add an explicit note that Option C is **downstream of X7's fix** and must not be attempted
first.

---

## 9. The strongest objection to my own design

**Layer A is a large, invasive, cross-cutting refactor whose enforcement value is delivered
almost entirely by its smallest part — and this defect's history is five consecutive
non-completions of exactly this kind of work.**

Concretely: Layer 0 (~8 lines) plus Layer C (~30 lines) removes the great majority of the
operational harm — 123 s → 10.5 s, and canopy's health stops depending on cascor's latency — for
about 4% of the diff and near-zero test churn. Everything beyond that buys **the enforceability
of the `await` rule**, and it buys it at the cost of a **40-70 file test migration** whose upper
bound I could not tighten.

The failure mode I am most worried about is not that Layer A is wrong. It is that it **stalls at
PR 5**. In that state the repo has: a baseline ratchet that freezes the debt rather than
reducing it, and a `main.py` with two live calling conventions where the next author has to know
which surface they are on — which is *worse than today*, because today the convention is at
least uniformly wrong. The evidence that this is a live risk is the defect's own history: an
HTTP self-call antipattern note (2026-04-02), HIGH-005 in canopy
`notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md`, the deferred Option C design
(`JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md`), a 2026-07-02 latency
audit, SEC-F20 with no JR-ID, and `JR-CAN-PERF-003`/`JR-CAN-PERF-004` still `proposed`. Six
sightings, six deferrals — plus a **seventh**: the ruff async-audit rollout itself, wired at
Phase 1 and never advanced past it, whose own `pyproject.toml:465` comment says *"Phase 4 may
flip this"*.

**I cannot fully answer this objection.** The honest mitigation is to structure the work so that
stalling is survivable rather than to argue it won't happen:

- PRs 1 and 2 are non-negotiable, independently valuable, and carry ~zero test churn. If nothing
  else lands, the class is **bounded** (10.5 s) and **detected** (D2b's integration test + the
  lag monitor + the ratchet), even though it is not **impossible**.
- Layer A should be treated as genuinely optional, and PR 4 should not begin unless there is
  committed capacity for PRs 5 and 6.
- The tell that the design is failing is the baseline file not shrinking across two consecutive
  batches in PR 5. If that happens, the correct move is to **stop and revert PR 4**, leaving
  PRs 1-3 in place, rather than to leave the codebase bilingual.

A secondary objection worth recording: D1 is a **proxy** check — it asserts a syntactic property
(`await` is present) that stands in for the real property (the loop does not stall). §4's blind
spots 1, 2, 4 and 5 are the gap between them, and a sufficiently determined author routes around
all four without ever tripping it. Only D2b tests the real property. If forced to choose one, the
right choice is the integration test — the AST gate earns its place by scaling across 40 sites
and by failing at edit time, not by being the more trustworthy check.
