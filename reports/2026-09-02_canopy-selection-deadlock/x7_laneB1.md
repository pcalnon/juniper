# Lane B1 — adversarial review of the X7 fix scope (juniper-canopy)

**Role**: Lane B adversarial reviewer B1. Brief: refute the plan.
**Date**: 2026-09-02
**Repos read (read-only, nothing edited)**: `juniper-canopy` @ `9fbf4b8`, `juniper-deploy`, `juniper-cascor-client`, `juniper-ml`
**Measurement harnesses** (throwaway, scratchpad only — I was forbidden to write into the repos):
`scratchpad/x7b1/{budget,repro2,repro3,census,census2,census3}.py`

---

## VERDICT

**The plan does not survive.** Three findings block it, two of which are decisive on their own:

| # | Finding | Status |
|---|---|---|
| **B-1** | **PR 1(a) is a literal no-op.** `timeout=30, retries=3` are already the `JuniperCascorClient` defaults. The 123.12 s measurement the plan cites *as the defect* is that budget being consumed in full. I reproduced 123.124 s with the plan's proposed setting. | **BLOCKS** |
| **B-2** | **The `asyncio.to_thread` offload is not compositional.** One request to any of the **19 handlers PR 1(b) leaves on the loop** reinstates the complete outage for every endpoint, `/live` and the health probes included. Demonstrated: `/live` went from 25 ms to hard-timeout the instant a single `POST /api/train/stop` landed, and never recovered. The un-offloaded set is exactly the operator's emergency levers. | **BLOCKS** |
| **B-3** | **No proposed setting gives ρ<1, and where ρ<1 is reachable the outage still is not removed.** Arithmetic + empirical below. The dashboard's own client timeouts (1.0 s / 2.0 s) are a hard ceiling that every ρ<1 setting exceeds. | **BLOCKS** |
| B-4 | The guard test is vacuous, and I proved it two independent ways. | Must be redesigned |
| B-5 | The TTL cache lands on a **safety interlock**, not a display field, and has no single-flight. | Must be re-scoped |
| B-6 | The offload removes the event loop's accidental serialisation of a **non-thread-safe shared `requests.Session`**. | New defect introduced |
| B-7 | The deferral the plan proposes has a **written un-defer trigger that X7 satisfies verbatim**. | Deferral indefensible |

Brief-by-brief: **#1 survives (strengthened)**, **#3 survives (decisively)**, **#4 survives (proven)**, **#5 survives (worse than posed)**. **#2 does not survive** as posed — I found the counter-evidence against it and report it honestly in §6.

---

## 1. B-1 — PR 1(a) changes nothing

`juniper-cascor-client/juniper_cascor_client/constants.py:33-35`

```
DEFAULT_REQUEST_TIMEOUT: int = 30
DEFAULT_RETRY_COUNT: int = 3
DEFAULT_BACKOFF_FACTOR: float = 0.5
DEFAULT_BACKOFF_JITTER: float = 0.5   # line 41
```

`juniper_cascor_client/client.py:126-128` — the constructor's own defaults are `timeout=DEFAULT_REQUEST_TIMEOUT, retries=DEFAULT_RETRY_COUNT`. The call site the plan targets,
`juniper-canopy/src/backend/cascor_service_adapter.py:507`:

```python
self._client = client or JuniperCascorClient(base_url=service_url, api_key=api_key)
```

**already runs with `timeout=30, retries=3`.** Writing them explicitly is a comment.

Measured (`budget.py`, real client, in-process blackhole listener = SIGSTOP'd upstream; closed port = refused):

```
setting                   HUNG wall                        REFUSED wall
DEFAULTS (today)           123.097s JuniperCascorConnectionError   3.004s
plan 1a: t=30 r=3          123.124s JuniperCascorConnectionError   3.004s   <-- identical
t=10 r=1                    20.023s                                0.002s
t=5  r=1                    10.011s                                0.001s
t=2  r=0                     2.003s                                0.002s
t=1  r=0                     1.003s                                0.003s
```

Both reported measurements fall straight out of the existing budget:

- **hung** = `30 × 4` + urllib3 backoff `0 + (0.5·2¹) + (0.5·2²)` = `120 + 3.0` ≈ **123.1 s** — reported 123.12 s.
- **refused** = `4 × ~0` + the same 3.0 s of backoff = **3.0 s** — reported 3.0 s.

Closed form: `S = timeout × (retries + 1) + Σbackoff`, with `Σbackoff = 0` for `retries ≤ 1` (urllib3 returns 0 while `consecutive_errors_len ≤ 1`) and ≈3.0-4.0 s for `retries = 3`.

**Two readings of the plan's text, both fatal.** If "→ timeout=30, retries=3" is the *proposed* value, PR 1(a) is a no-op that will be reported as a fix. If it is a description of the *current effective* value, then the plan has not specified any bound at all, and §3 shows the choice is the whole ballgame.

---

## 2. B-3 — the ρ arithmetic (the brief's central question)

### Demand λ — measured from the code, per browser tab

| lane | cadence | file:line | upstream cascor calls |
|---|---|---|---|
| fast | `FAST_UPDATE_INTERVAL_MS = 1000` (`canopy_constants.py:370`) | `dashboard_manager.py:6294` → `/api/status`, client timeout `FAST_API_TIMEOUT_SECONDS = 1.0` | 1 per tick → **1.00/s** |
| slow | `SLOW_UPDATE_INTERVAL_MS = 5000` (`canopy_constants.py:371`) | `_update_system_panels_handler`, three *sequential* self-calls: `/api/status` (6544), `/api/network/stats` (6677), `/api/stream_health` (7820) | third is pure in-memory → 2 per tick → **0.40/s** |
| probe | `HEALTHCHECK_INTERVAL = 15s` (`juniper-deploy/docker-compose.yml:47`), `urlopen(.../v1/health, timeout=5)` (line 732) | `main.py:1076` `backend.is_training_active()` | **0.067/s** |

> Correction to the brief: the slow lane makes **three self-calls but only two upstream calls**; `/api/stream_health` is in-memory (`main.py:1321`, adapter method verified `_client`-free). I use the corrected figure — it is *conservative against my own case*.

**λ(n tabs) = 1.40·n + 0.067**  — and it is **open-loop**: `dcc.Interval` fires on a wall-clock timer, and a browser-side XHR abort does not stop the server-side handler. Arrivals do not throttle when service slows. That is the condition under which ρ ≥ 1 diverges without bound.

### Servers c

- **c = 1** — the single event loop (today; `WSGIMiddleware` mount at `main.py:493` runs Dash in *its own* pool, but every route handler body runs on the loop).
- **c = 20** — `asyncio.to_thread` → default executor, `min(32, cpu_count + 4)`, `cpu_count = 16`. **Verified 20.**

### ρ = λ·S/c

**Case A — handlers on the loop (today, and after PR 1(a) alone), 1 tab, λ = 1.467/s**

| setting | S | **ρ** | |
|---|---|---|---|
| today = plan 1a (t=30, r=3) | 123.1 s | **180.6** | diverges |
| t=10, r=1 | 20.02 s | **29.4** | diverges |
| t=5, r=1 | 10.01 s | **14.7** | diverges |
| t=2, r=0 | 2.003 s | **2.94** | diverges |
| t=1, r=0 | 1.003 s | **1.47** | diverges |

Stability needs `S < 1/λ = 0.68 s`. **Without the offload, no usable timeout gives ρ<1.** PR 1(a) alone cannot work at any setting.

**Case B — the 5 handlers offloaded to the 20-slot executor**

| setting | S | ρ @1 tab | ρ @2 tabs | ρ @4 tabs | ρ @8 tabs |
|---|---|---|---|---|---|
| **plan 1a (t=30, r=3)** | 123.1 s | **9.03** | **17.6** | **34.7** | **69.3** |
| t=10, r=1 | 20.02 s | **1.47** | **2.87** | **5.67** | **11.3** |
| t=5, r=1 | 10.01 s | 0.734 | **1.43** | **2.84** | **5.64** |
| t=2, r=0 | 2.003 s | 0.147 | 0.287 | 0.567 | **1.13** |
| t=1, r=0 | 1.003 s | 0.074 | 0.144 | 0.284 | 0.565 |

Max stable service time at c=20: `S < 20/λ` → **13.6 s** (1 tab), **6.98 s** (2), **3.53 s** (4), **1.77 s** (8).

### Empirical validation (`repro2.py` — real client, real uvicorn, real blackhole, open-loop pollers)

| run | observed | matches prediction |
|---|---|---|
| thread, t=30 r=3, 1 tab, 60 s | inflight **pinned 20/20 by t=15 s**, `started=20 finished=0` | ρ = 9.03 ≫ 1 ✓ |
| thread, t=5 r=1, 1 tab, 60 s | inflight 13-16, `finished=74` (1.23/s ≈ λ) | ρ = 0.734 ✓ |
| thread, t=5 r=1, **2 tabs**, 60 s | inflight **pinned 20/20 from t=10 s** | ρ = 1.43 ✓ |
| thread, t=2 r=0, 4 tabs, 45 s | inflight steady 8, `finished=247` (5.5/s ≈ λ) | ρ = 0.567 ✓ |

### Answer

> **Does any proposed setting give ρ<1?**

**The plan's own setting does not** — ρ = 180.6 unoffloaded, 9.03 offloaded, at one browser tab. **Without the offload nothing does.** With the offload, only `t ≤ 5, r ≤ 1`, and `t=5/r=1` **fails at two open browser tabs**. Only `t=2, r=0` holds to four tabs, and it fails at eight.

### And ρ<1 still does not remove the outage

`canopy_constants.py:374-375` — `API_TIMEOUT_SECONDS = 2`, `FAST_API_TIMEOUT_SECONDS = 1.0`. These are the *dashboard's* client timeouts on its own self-calls. Every setting above with ρ<1 has `S ≥ 1.0 s ≥` those timeouts, so **every dashboard panel still times out and renders an error div** (`_network_info_error_div`, `dashboard_manager.py:6559/6681`). For a panel to actually render you need `S < 1.0 s` — i.e. `timeout < 1 s, retries = 0` — which then fails against a merely-slow-but-alive cascor.

**There is no `(timeout, retries)` pair that both keeps ρ<1 and lets the dashboard render during a cascor hang.** Bounding the client is a *dead end as a fix*; it is only a prerequisite for something else. The something else is: stop calling upstream synchronously in the request path — serve from state a background task maintains. The WS metrics relay (`_relay_task`, `start_metrics_relay`) is already that machinery. The plan defers exactly this.

---

## 3. B-2 — the offload is not compositional (`repro3.py`)

Topology: `/api/status` offloaded (stands for the 5 PR 1(b) fixes), `POST /api/train/stop` left on the loop (stands for the 19 it does not), `/live` pure-async. `t=30, r=3`. A single operator POST at t=20 s:

```
        window  /live worst ms  /live timeouts
    0-5                   59.1               0
    5-10                  28.8               0
   10-15                  25.4               0
  [t=20s] operator POSTs /api/train/stop (an un-offloaded handler)
   15-20                  39.5               0
   20-25                3021.1               1   <-- STALLED
   25-30                   0.0               0        (zero samples completed)
   30-35                3022.9               1   <-- STALLED
   ...
   55-60                3020.8               1   <-- STALLED
```

`/live` never recovers. **One request to one un-offloaded handler restores the full original outage for the entire service.**

Exact census (`census3.py` — AST, transitive closure over `CascorServiceAdapter` → `service_backend` → `main.py` route handlers, counting only un-awaited calls that provably reach `self._client`):

- 45 of the adapter's public methods perform synchronous `requests` I/O; 25 `service_backend` methods delegate to them.
- **24 route handlers / 35 call sites** in `main.py` reach that I/O un-awaited.
- **PR 1(b) covers 5 handlers / 5 sites. 19 handlers / 30 sites remain.** (Conservative — this join ignores `backend._adapter._client.list_workers()` at `main.py:3254` and direct `requests.*`.)

The 19 are not a long tail. They are the control surface:

```
api_train_start/pause/resume/stop/reset/status/restart   (3408, 3440, 3461, 3482, 3503, 3524, 3588)
create/restore/replay/resume/retrain_snapshot            (2252, 2455, 2728, 2791, 2815)
patch_weights, add_hidden_unit, remove_hidden_unit       (2860, 2890, 2907)
get_state, get_dataset, get_decision_boundary, replay_control
```

**During an X7 event the operator cannot stop training — and the attempt re-jams the service for another 123 s.** PR 1 makes the *probe* fast and leaves the *emergency stop* jammed.

---

## 4. B-4 — the guard test is vacuous, proven two ways

### Precedent: the repo already ships this exact check, and it is green

`.pre-commit-config.yaml:117-131`, a **CI-blocking** hook named `Async-route audit (BUG-JD-10 class)`, running `ruff --select ASYNC` over `^src/.*\.py$`. I ran it:

```
$ ruff check --select ASYNC src/
All checks passed!
```

against 24 handlers / 35 live sites. `ASYNC210` pattern-matches the *callee name* (`requests.get`, `httpx.get`, `urllib.request.urlopen`); `backend.get_status()` is an ordinary method call that reaches `requests` three frames down and is structurally invisible to it. The hook's header even claims "The repo reached zero visible violations" — *visible* is doing all the work.

### Mechanism 1 — the offload makes the control endpoint fast **by construction**

From `repro2.py`, thread mode, plan settings, executor **100% saturated at 20/20 with zero completions**:

```
/live samples over the plan's 500 ms guard threshold: 0/60
NEVER breached 500 ms
peak concurrent upstream calls = 20 (cap = 20)
started=20 finished=0 -> backlog=20
```

**The guard test passes with a green tick while the dashboard is completely dead.** A pure-async endpoint needs no thread, so once *anything* is offloaded it cannot breach the threshold — the test measures the *presence of an offload*, not the *absence of an outage*, and cannot see executor exhaustion, the 19 un-offloaded handlers, or the dashboard's actual state.

### Mechanism 2 — the fully-broken case yields an **empty sample set**

`repro2.py` in `loop` mode (today's behaviour): `/live` returned **0 samples in 40 s** — every probe was still outstanding. A test that asserts on a latency statistic over collected samples reads `0/0` and passes. This is the vacuous-pass class exactly: the machinery breaks, the report reads green.

### What would make it non-vacuous

1. Assert on a **completed request against a wall-clock deadline**, failing closed on timeout/no-response — never on a percentile over collected samples.
2. Probe **`/api/status` and one snapshot/train-control route**, not a pure-async control endpoint. The invariant that matters is "an endpoint that *needs* upstream data answers (with a degraded payload) within its budget", not "an endpoint that needs nothing is fast".
3. Assert **executor headroom** (`len(executor._threads)` / queue depth) and **`started == finished + small`**, so saturation fails the test.
4. Drive it at the **real open-loop λ** with ≥2 simulated tabs for ≥60 s. A single-shot probe passes at t=0 in every configuration I measured; saturation took 10-15 s to appear.
5. Assert the **compositional** property: after issuing one request to a *randomly chosen* route handler, `/live` still answers. That is the only form that would have caught B-2.

The 500 ms threshold is not the problem — `/live` sat at 20-35 ms under total saturation. **A tighter threshold would not help.** The threshold is measuring the wrong thing.

---

## 5. B-5 — the TTL cache lands on a safety interlock, and B-6

### `training_active` is not a display field

`backend.is_training_active()` is the **mutation interlock** for five destructive routes:

| main.py | guard |
|---|---|
| 2480 | `restore_snapshot` — "Cannot restore while training is running" (409) |
| 2740 | `replay_snapshot_route` — "Cannot start replay while training is running" |
| 2801 / 2822 | `resume_snapshot_route` / `retrain_snapshot_route` |
| 3710 | model select — "Cannot switch models while training is active" |

If the TTL cache is implemented at the adapter/`is_training_active` level — the natural place, and where the repo's existing cache already lives (`cascor_service_adapter.py:1012-1031`, `network`, 30 s TTL) — then **a stale `False` opens all five interlocks and a restore clobbers a live run.** The plan's wording ("serve `training_active` in the health endpoints from a short TTL cache") reads endpoint-scoped, but the in-repo precedent pulls the other way. This needs an explicit prohibition, not an assumption.

### The existing TTL cache is the proof that the pattern fails here

`cascor_service_adapter.py:1012-1031`:

```python
if self._network_cache is not None and now - self._network_cache_time < 30:
    return self._network_cache
try:
    result = self._client.get_network()
    ...
except Exception as e:
    logger.debug(...)
self._network_cache = None          # negative result
self._network_cache_time = now
```

The guard is `is not None`, so a **negative result is never served from cache**. During an outage every call re-probes and pays the full 123 s. **The repo's existing TTL cache provides exactly zero protection against the failure mode PR 1(c) is aimed at.** Copy it and you inherit that.

### No single-flight

There is **one** `threading.Lock` in the entire adapter, and it is not around the cache. Without in-flight de-duplication, the 1 Hz fast lane generates ~123 concurrent upstream calls before the first one returns to populate the cache. **Single-flight, not TTL, is the load-bearing part** — and the plan does not mention it.

### The structural dilemma

- TTL short enough to be truthful → nearly every request is a miss during an outage → still pays S. No protection.
- TTL long enough to protect (≥ S) → health reports a value up to 123 s stale, presented as fresh.
- Serve-stale-on-error → health reports the pre-outage value indefinitely.

### The cache removes the only automated outage signal

Today the docker healthcheck (`urlopen('.../v1/health', timeout=5)`, 15 s interval, 5 retries) fails **only as a side effect of the loop stall** — `/v1/health` returns `"status": "ok"` unconditionally, so it has never been a health *assessment*. `/v1/health/live` (`main.py:1088`) returns `{"status":"alive"}` unconditionally. `/v1/health/ready` returns `status="degraded"` **with HTTP 200** (no `status_code` override at `main.py:1123`).

**After PR 1(b)+(c) there is no probe in the stack that goes red on a cascor outage.** PR 3 "retargets probes" — to endpoints that are all unconditionally-200. This is a **net loss** of observability, and it is compounded by:

- the Prometheus SLO alerts keying on `juniper_canopy_http_requests_total{status=~"5.."}` and a latency histogram (`juniper-deploy/prometheus/alert_rules.yml:102`) — a stalled request emits **neither**;
- `juniper_canopy_demo_mode_active == 0 and ...` (line 228) using the demo gauge purely as an **alert suppressor**.

Mitigating, and I report it: after the offload `/api/status` *completes* (after S) and therefore *does* emit a >0.5 s histogram sample, so the latency SLO would start firing. That is a real improvement — but it fires on the endpoint the plan leaves slow, not on the probe the plan makes fast.

### B-6 — the offload introduces a genuine new defect

`requests.Session` is documented **not thread-safe**. `cascor_service_adapter.py:507` builds one `JuniperCascorClient`, hence one `self.session`, shared by every call site. Today the event loop **serialises every one of the 5 hot handlers** — I measured `peak concurrent upstream calls = 1` in loop mode over 40 s. **The event loop is currently acting as a giant lock over a non-thread-safe object.** `asyncio.to_thread` removes that lock and puts up to **20 threads** on the shared Session (measured: `peak concurrent = 20`), with `pool_maxsize=10` so half of them churn connections outside the pool. The plan must add a per-thread client, a lock, or a documented thread-safety argument.

Related: `asyncio.to_thread` futures are **uncancellable once running**, and `ThreadPoolExecutor` threads are non-daemon with an `atexit` join. My first harness run **hung on interpreter exit** for exactly this reason — the pool had to drain 123 s jobs. That is a live graceful-shutdown hazard (compare the known `uvicorn SIGTERM re-raise skips atexit` behaviour).

---

## 6. Brief-by-brief adjudication

### Brief #1 — "PR 1 is too narrow and entrenches the defect" — **SURVIVES, strengthened**

The strongest form is not rhetorical, it is documentary. `juniper-ml/notes/JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_FOLLOWUP-ASYNC-ROUTE-AUDIT.md:82` states the un-defer trigger for the systemic AST checker (`util/check_async_routes.py`) verbatim:

> 1. A new BUG-JD-10-class incident occurs in production where a sync call inside an `async def` route handler stalls the event loop, **and** the call site would not have been caught by ruff's `--select ASYNC` (i.e. it's a project-internal helper, not a stdlib primitive).

X7 satisfies **both conjuncts exactly**: a 123.12 s event-loop stall from `backend.is_training_active()` / `backend.get_status()` — project-internal helpers — and I verified `ruff --select ASYNC src/` reports "All checks passed!". Trigger #2 in the same list ("a code review surfaces a sync call inside an `async def` that uses a project-internal helper") also fired, in this very review.

The 2026-05-19 status doc (`JUNIPER_2026-05-19_JUNIPER-ECOSYSTEM_STATUS-FOLLOWUP-ASYNC-ROUTE-AUDIT.md`) chose "**Continue to defer**" on the reasoning "ruff coverage still appears sufficient". **That premise is now measurably false.** Deferring again requires overturning the project's own written criterion, on evidence that contradicts the stated reason.

**The self-attack the brief asked for — and its outcome.** The counter is that a stalled multi-PR arc leaves a ratchet plus a bilingual `main.py`. **That harm is already realised**: `main.py:3553` and `main.py:3615` *already* use `asyncio.to_thread(backend.is_training_active)`, with a comment citing "plan §8 stop→start race". An earlier session offloaded 2 of 35 sites for one specific race and the class survived — the eighth-deferral pattern in miniature, already on disk. So "a narrow fix risks leaving main.py bilingual" cannot defend PR 1(b): it *is* bilingual, PR 1(b) makes it more so, and B-2 proves that partial offloading is not merely untidy but **non-compositional** — a mixed `main.py` is not a slower path to the fix, it is a service that still fails completely.

The systemic reframing the brief proposes ("collapse the checker to: is the parent an `ast.Await`?") is sound in shape but I must flag: it is **not sufficient as stated**. `probe_dependency` (`health.py:60`) is correctly `async`/httpx and awaited; `get_stream_health` is sync but pure in-memory and correctly *not* awaited. A bare await-parent rule flags the latter as a false positive. The rule needs the reachability set — which is cheap: `census3.py` computes it in one AST pass (45 network-reaching adapter methods, 25 backend delegates).

### Brief #2 — "demo honesty must come first" — **DOES NOT SURVIVE as posed**

Every factual claim checks out:

- `main.py:320-333` — silent demo fallback on a cold start with cascor unreachable; a `WARNING` log is the only signal.
- `websocket_client.js:377` hardcodes `mode: "live"`; `connection_indicator.py:80-83`'s `if (wsStatus.mode === "demo") return ["WS: Demo", ...]` is **unreachable dead code** — I found no other writer of `.mode`. The same file documents the identical prior incident at lines 55-57: *"in the 2026-07-10 incident the badge showed a green 'WS: Connected' for 12+ hours while the canopy→cascor relay behind it was dead."*
- `main.py:2284-2296` — `size_bytes = 1024*1024 + int(now.timestamp()) % (512*1024)` and `"path": f"{_snapshots_dir}/{snapshot_name}"`, returned with **201**, carrying real `dataset_name`/`dataset_version` provenance.
- `alert_rules.yml:228` — the demo gauge used only as an alert suppressor.

**But the ordering argument fails on mechanism.** The demo fallback fires **only at startup** (`lifespan`, `main.py:320`); nothing re-checks at runtime. So a mid-flight cascor outage produces the **hang**, never the demo fallback — the two are mutually exclusive by timing and the hang is not "the symptom preventing fabrication". I also checked the escalation path that would have rescued the argument: canopy is `restart: unless-stopped` with **no autoheal container**, and Docker's restart policy does not act on healthcheck state — so "hang → unhealthy → restart → cold start into demo mode" **does not exist** in this stack.

Worse for the brief: PR 1(c) *prevents* the healthcheck from failing, which if anything makes a restart-into-demo *less* likely. **Fixing the hang first is not actively harmful.**

What survives is narrower and still worth saying: during an X7 event `_update_stream_health_handler` (`dashboard_manager.py:7811-7826`) returns `dash.no_update` on failure, so the badge **retains its last value — green "WS: Connected" — over a frozen dashboard**, reproducing the 2026-07-10 incident. PR 1(b) would actually *restore* that signal by letting `/api/stream_health` answer. So PR 1 before PR 2 is defensible; **PR 3 before PR 2 is not**, because PR 3 retargets probes to unconditionally-200 endpoints while the fabrication paths are still live.

### Brief #3 — "the fix does not remove the outage" — **SURVIVES DECISIVELY.** §2 above.

### Brief #4 — "the guard test is vacuous" — **SURVIVES, proven.** §4 above.

### Brief #5 — "the TTL cache is a new defect" — **SURVIVES, and is worse than posed.** §5 above: it is not a staleness question, it is a safety-interlock question plus a missing single-flight, plus the removal of the only automated outage signal.

---

## 7. What would actually have to be true

1. **Delete PR 1(a) or replace it with a real bound.** `t=2, r=0` is the only setting that holds past two browser tabs — and see (3), it is still not sufficient.
2. **Offload is all-or-nothing.** Either all 24 handlers or none; a mixed `main.py` fails completely on the first request to an un-offloaded route (B-2). The 19 un-offloaded handlers are the operator's control surface.
3. **Bounding + offloading cannot remove the outage.** No `(timeout, retries)` pair satisfies both ρ<1 and `S < 1.0 s`. The dashboard needs a **background refresher + cache with single-flight** (the WS relay already exists) — i.e. the work the plan defers.
4. **Add single-flight before any TTL cache**, and forbid caching at the `is_training_active`/adapter level (five interlocks).
5. **Redesign the guard test** per §4, and settle the `requests.Session` thread-safety question (B-6) before any offload ships.
6. **Do not retarget probes (PR 3) until something can go red.** All three health endpoints are unconditionally-200 today.
