# X7 fix design — F3 lens: operational semantics and failure behaviour

**Author lens**: what the system *should do* when a dependency is unreachable — what health
means, what an orchestrator does with it, what an operator sees, and whether the degraded
state is honest.
**Status**: design only. No repository file was edited.
**Date**: 2026-09-02

---

## 0. Executive position

The blocking-I/O root cause is real and must be fixed, but **a fix that only stops the hang
leaves the worse defect standing.** Canopy's failure mode when cascor is unreachable is not
"unavailable" — it is **"available and lying"**: it falls back to a simulator, serves
fabricated cascade-training data, labels it `live` in the UI, and reports `status: "ok"` on
`/v1/health`. My design therefore treats X7 as **two defects that share a trigger**:

- **X7-A (availability)** — sync retrying `requests` in `async def` blocks the loop. P2.
- **X7-B (integrity)** — unrequested demo fallback fabricates data indistinguishable from
  real. **P1, and not latent.**

And it produces one sequencing rule that I consider the most important output of this
document:

> **Do not tighten the liveness probe before the demo fallback is deleted.**
> Tightening liveness while X7-B stands makes the platform *worse*: it converts a visible,
> self-recovering hang into a fast, silent restart into the simulator.

---

## 1. Anchor verification

Every claim in the brief was re-checked against the repos. Line numbers are from
`/home/pcalnon/Development/python/Juniper/juniper-canopy` and
`/home/pcalnon/Development/python/Juniper/juniper-deploy` as of 2026-09-02.

### 1.1 CONFIRMED as stated

| Claim | Evidence |
|---|---|
| `/v1/health` calls `backend.is_training_active()` inline | `juniper-canopy/src/main.py:1076` |
| `/health` + `/api/health` share it | `main.py:1028-1030`, `:1050` |
| `/v1/health/ready` shares it | `main.py:1133` (inside `details`) |
| That call reaches a blocking `requests` path | `main.py:1076` → `backend/service_backend.py:160` `is_training_active()` → `backend/cascor_service_adapter.py:1089` `is_training_in_progress()` → `self._client.get_training_status()` at `:1091` |
| It **bypasses the circuit breaker** its sibling uses | bypass at `cascor_service_adapter.py:1091` (bare `self._client...`); breaker-protected sibling `get_training_status()` at `:1968-1974` uses `self._cb.call(..., fallback=lambda: {"is_training": False, "error": "circuit open"})` |
| Startup silently falls back to demo | `main.py:322-337`; `system_logger.warning("JuniperCascor unreachable at %s — falling back to demo mode", cascor_url)` at `:328`, then `create_backend(demo_mode=True)` at `:331` |
| `/v1/health` still returns `status: "ok"` | `main.py:1070` — the string is a **literal**, unconditional |
| readiness returns `degraded` at HTTP 200 | `main.py:1093-1141` — the route has no `Response` parameter and never sets `status_code`; `ReadinessResponse` is a body model only |
| no `cascor_available` global exists | only `juniper_data_available` (`main.py:122`) |
| Compose healthcheck targets `/v1/health` | `docker-compose.yml:730-733` (canopy), and two more canopy variants at `:812-815`, `:867-870` |
| Compose interval/timeout/retries = 15s/10s/5 | anchor `x-healthcheck-canopy` at `docker-compose.yml:58-62` (`start_period` 20s) |
| `Dockerfile` uses `curl --max-time 5` | `juniper-canopy/Dockerfile:107-108`, `--interval=30s --timeout=10s --retries=3` (Compose overrides this) |
| Helm liveness → `/v1/health/live`, period 15, failureThreshold 5 | `k8s/helm/juniper/values.yaml:228-233`; wired at `templates/canopy-deployment.yaml:84-91` |
| Helm readiness → `/v1/health/ready` | `values.yaml:234-239`; wired at `canopy-deployment.yaml:92-99` |
| Chart pinned pre-production | `values.yaml:187` — `tag: "0.4.0"` |

### 1.2 CORRECTED

**C-1 — `/v1/health/live` is not itself a dependency-toucher; it is a no-op.**
`main.py:1087-1090` is literally `return {"status": "alive"}`. The brief's chain ("liveness
fails") is right about the *outcome* but not the *mechanism*: liveness fails because the
event loop cannot schedule the handler, not because the handler calls cascor. This matters
because it means **fixing `/v1/health`'s blocking call does not by itself make liveness
trustworthy** — the no-op endpoint still cannot distinguish "loop healthy" from "loop
saturated but under the probe timeout".

**C-2 — the pod kill needs the black-hole case *or* queue saturation, not the 3.0 s case
alone.** Helm `timeoutSeconds: 10` (`values.yaml:232`) exceeds a single 3.0 s block, so
connection-refused does not trip liveness per-call. It trips it by **queueing**: canopy's
dashboard polls at ~1 Hz across many callbacks; with a 3.0 s serialised service time the
loop's utilisation is ρ ≈ 3, the queue grows without bound, and observed latency crosses
10 s within tens of seconds. So the kill is reachable in both cases, but by different
mechanisms — and the fix must therefore address **concurrency**, not only per-call latency.
(Reasoned from the measured 3.0 s and the poll cadence; not separately instrumented.)

**C-3 — the "~75 s" kill time is a floor, not the figure.** `failureThreshold: 5` ×
`periodSeconds: 15` = 60 s of probe failures, plus up to 15 s to the first failing probe
and up to 10 s inside it → **60-85 s**. Immaterial to the argument; stated for accuracy.

**C-4 — X7-B is *not* latent.** The brief files the data-integrity chain as latent because
the chart is pre-production. Only the **pod-restart** step is Helm-gated. The **fabrication**
step needs only *a cold start with cascor unreachable*, which is reachable today via:
(a) any local `python src/main.py` dev run (the documented path, `Dockerfile:110`);
(b) any Docker daemon restart of the canopy container under `restart: unless-stopped`
(`docker-compose.yml`, canopy service) — `depends_on: condition: service_healthy` gates the
initial `compose up` only; the daemon's restart policy does not re-evaluate it;
(c) `compose up` of any profile where cascor becomes unhealthy between its own health gate
and canopy's startup probe.
This is the single most consequential correction in this document.

**C-5 — `values.yaml:222-226` documents a contract canopy does not implement.** The comment
reads:

> *"Canopy's liveness tick verifies the WebSocket-manager singleton; readiness 503s only when
> ws_manager is unbound (upstream juniper-data / juniper-cascor outages remain 200/degraded
> so the dashboard stays useful with cached state)."*

Three of its four assertions are false against `main.py`:
- "liveness tick verifies the WebSocket-manager singleton" — **false**, `main.py:1087-1090`
  verifies nothing;
- "readiness 503s only when ws_manager is unbound" — **false**, readiness never 503s and
  never inspects `websocket_manager`;
- "the dashboard stays useful **with cached state**" — **false, there is no cache** (see
  §1.3 N-3);
- "upstream outages remain 200/degraded" — **true**.

This is a gift to the fix: **the intended semantics were already written down in
juniper-deploy and never implemented in juniper-canopy.** The design below is largely
"implement the contract the chart already claims", not "invent new semantics".

### 1.3 NEW findings (not in the brief)

**N-1 — canopy is the *only* Juniper service without the ecosystem's real liveness
contract.** Both siblings implement a measured in-process tick and 503 on budget overrun:

| | `/v1/health/live` | `/v1/health/ready` codes | `X-Juniper-Readiness` |
|---|---|---|---|
| juniper-cascor | tick + 503 `unresponsive` (`src/api/routes/health.py:91-128`, budget check `:114`) | 200 ready / 200 degraded / **503 not_ready** (`:130-190`, `response.status_code = 503` at `:184`) | set (`:191`) |
| juniper-data | tick + 503 `unresponsive` (`juniper_data/api/routes/health.py:146-183`, budget `:161`) | same, 503 at `:229` | set |
| **juniper-canopy** | **`return {"status": "alive"}`** (`src/main.py:1088-1090`) | **always 200** | **absent** |

`LIVENESS_TICK_BUDGET_MS` (= 250) and `READINESS_HEADER` are **exported from the shared
`juniper_observability` package** (`juniper-cascor/src/api/routes/health.py:31`), which
canopy already depends on (`juniper-canopy/src/health.py:44`). Canopy imports the package
and ignores the constants. juniper-data's comment at `health.py:44-46` names canopy's exact
pattern as the anti-pattern: *"the budget catches event-loop stalls and CPU starvation that
the no-op `return {"status": "alive"}` could not."* The convention exists; canopy is the
outlier.

**N-2 — the codebase already knows `is_training_active()` blocks.** `main.py:3553` and
`:3615` call it as `await asyncio.to_thread(backend.is_training_active)`. The control paths
were offloaded; the **health** paths were not. This is a maintenance-drift defect, not an
oversight of principle — which raises my confidence that a fix will be accepted, and lowers
my confidence that a fix *alone* will stay fixed without a drift guard (see T-1).

**N-3 — `juniper_data_available` is written once at startup and never refreshed.**
`main.py:122` init `False`, `:315` set `True`, read at `:1484` and `:1691`. Nothing else
writes it. So the field canopy already reports on `/v1/health` **cannot go false** once
true: if juniper-data dies after startup, `/v1/health` reports `juniper_data_available: true`
forever, and the `:1484` guard keeps admitting requests. **Any design that "mirrors
`juniper_data_available` for cascor" would replicate a stale-forever flag.** The mirror must
be refreshed, and `juniper_data_available` must be fixed in the same change.

**N-4 — readiness probes its two dependencies *sequentially*.** `main.py:1105` awaits the
data probe, then `:1111` awaits the cascor probe. Each has a 5.0 s httpx timeout
(`src/health.py:60`). Worst case ≈ **10.0 s**, which already exceeds Helm's readiness
`timeoutSeconds: 5` (`values.yaml:238`) and sits at Compose's `timeout: 10s`. **With both
upstreams black-holed, canopy's readiness probe fails on timeout today — independently of
X7.** One `asyncio.gather` fixes it.

**N-5 — a second, unflagged breaker bypass.** `_ServiceTrainingMonitor.is_training`
(`cascor_service_adapter.py:436-447`) calls `self._client.get_training_status()` bare,
identically to `:1091`. Any fix that patches only `is_training_in_progress` leaves this one.

**N-6 — the client's own configuration is the amplifier.**
`cascor_service_adapter.py:507` constructs `JuniperCascorClient(base_url=..., api_key=...)`
with **no timeout and no retries argument**, so it takes the library defaults:
`timeout: int = 30, retries: int = 3`
(`/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/juniper_cascor_client/client.py`).
That is where ~123 s comes from: 4 attempts × 30 s + urllib3 backoff. **A 30 s × 4 budget is
the wrong configuration for a status read that a health endpoint depends on**, independent of
where the call runs.

**N-7 — the breaker cannot save a black-holed canopy.** `failure_threshold=5`,
`recovery_timeout=60.0` (`src/canopy_constants.py:648-650`). Adopting the breaker on the
bypassed call **does not** bound the outage: it takes **5 × 123 s ≈ 615 s** of blocking to
open the circuit, and every 60 s thereafter the HALF_OPEN probe blocks another 123 s. **A
breaker-only fix is not a fix.** The breaker is worth adopting for consistency, but the
load-bearing changes are the timeout budget (N-6) and non-blocking execution.

**N-8 — `asyncio.to_thread` alone converts a loop stall into a threadpool stall.**
Measured in the live env: `anyio` default thread limiter `total_tokens = 40`
(`anyio 4.14.2`, `starlette 1.3.1`, `fastapi 0.137.0`, `uvicorn 0.49.0`). At ~1 Hz arrivals
× 123 s service time, all 40 tokens are consumed in ~40 s; subsequent `to_thread` calls queue
on the limiter, **which is shared with every `def` (sync) route Starlette offloads**. The
loop stays responsive — so liveness passes and the orchestrator sees a healthy pod — while
every route silently stalls forever. **That is a strictly worse operational posture than
today's honest hang**, and it is the obvious "minimal fix" someone will propose. Offload
must be paired with a bounded timeout and a concurrency cap, or replaced by "don't call
upstream from a health endpoint at all" (my choice).

**N-9 — the UI cannot report demo mode. The indicator is dead code.**
- `src/frontend/dashboard_manager.py:1919` seeds the store from
  `"demo" if get_settings().demo_mode else "live"` — the **configured** flag, not
  `backend.backend_type`. In the fallback scenario the configured flag is `False`, so the
  seed already says `"live"`.
- That seed is then **overwritten on the first fast tick** by the clientside peek
  (`dashboard_manager.py:3691-3701`).
- `src/frontend/assets/ws_dash_bridge.js:51` initialises
  `_connectionStatus: {..., mode: "live"}` and `peekConnectionStatus()` at `:138-149`
  returns `mode: status.mode || "live"`.
- `src/frontend/assets/websocket_client.js:372-379` sets `mode: "live"` as a **hardcoded
  literal** on every connection-status change.
- The badge's demo branch (`src/frontend/components/connection_indicator.py:80-83`,
  `"WS: Demo"`) is therefore **unreachable in practice**.

In demo mode the WebSocket *is* connected (DemoMode broadcasts its own simulated frames
through the same manager), so the badge renders **green "WS: Connected"** over fabricated
data. `main.py:333-337` contains a comment that names this exact hazard for the Prometheus
gauge — *"reading `settings.demo_mode` directly would lie about the live state"* — and fixes
it there (`set_demo_mode_active(backend.backend_type == "demo")`). The same reasoning was
never applied to the UI store.

**N-10 — the fabrication reaches persisted artifacts, partially labelled.**
`POST /api/v1/snapshots` in demo mode (`main.py:2282-2322`) returns **HTTP 201** with a
**fabricated `size_bytes`** (`:2283`, `1 MB + timestamp % 512 KB`), a **`path` to a file that
does not exist** (`:2290`), and real-looking `meta_params` / `dataset_name` /
`dataset_version` (`:2286`, `:2299-2302`). The only fabrication marker is
`description or "Demo snapshot (no real HDF5 file)"` (`:2288`) — **an operator-supplied
description erases it.** `_log_snapshot_activity` (`main.py:2215-2248`) then appends a row to
`Path(_snapshots_dir)/"snapshot_history.jsonl"` (`:2229`), and in the Compose full profile
`JUNIPER_CANOPY_SNAPSHOT_DIR=/app/cascor-snapshots` is bind-mounted **read-write** onto the
real cascor snapshot archive. So phantom rows land in the archive of record.
**Honest mitigation**: that jsonl row *does* carry `"mode": "demo"` in `details` (`:2314`),
so the persisted provenance row is self-labelling. The **API response and the UI are not.**

**N-11 — the one telemetry signal that knows the truth is used only to silence another
alert.** `juniper_canopy_demo_mode_active` is set correctly from `backend.backend_type`
(`src/observability.py:326-332`, called at `main.py:337`), and appears in exactly one
Prometheus rule — as a **suppressor**:
`juniper-deploy/prometheus/alert_rules.yml:228`, `... demo_mode_active == 0 and
websocket_connections_active == 0`. **No alert fires when demo mode is active.** The
cheapest possible operator-facing guarantee is unbuilt.

**N-12 (cross-repo, out of scope, report only)** — cascor's readiness route calls the
**synchronous** shared probe inside `async def` without offload:
`juniper-cascor/src/api/routes/health.py:180`, `dependencies["juniper_data"] =
probe_dependency(...)` — and `juniper_observability.probe_dependency` is not a coroutine
(verified: `inspect.iscoroutinefunction(...) is False`). Same defect class as X7, bounded at
5 s. Worth a separate ticket; do not scope-creep this fix into it.

---

## 2. What health SHOULD mean here

Three questions, three endpoints, one rule each.

> **The rule that generates the rest:** *the probe that can restart you must never be able to
> fail because of something a restart cannot fix.* A dependency outage is not fixable by
> restarting canopy; therefore liveness must not observe dependencies. A dependency outage
> *is* a reason to stop sending user traffic to a replica that would answer with nothing (or
> worse, with fiction); therefore readiness may observe them.

### 2.1 `/v1/health/live` — liveness: "is this process able to make progress?"

**Touches upstream: NEVER.** Not via a socket, not via a cached value that a dependency
writes, not transitively.

**But it must stop being a no-op.** A bare `return` cannot distinguish a healthy loop from a
loop at ρ ≈ 3 (C-2, N-8). Adopt the sibling contract exactly, using the constants canopy
already imports:

| Condition | Code | Body |
|---|---|---|
| in-process tick completes within `LIVENESS_TICK_BUDGET_MS` (250) | **200** | `{"status":"alive","tick":"juniper-canopy","duration_ms":N}` |
| tick exceeds the budget | **503** | `{"status":"unresponsive","duration_ms":N,"error":"tick exceeded budget: Nms > 250ms"}` |
| tick raises | **503** | `{"status":"unresponsive","error":"<reason>"}` |

Canopy's tick should be what `values.yaml:224` already claims: **assert the
`websocket_manager` singleton is bound and its event loop is set**. That is pure in-process
work, it is the thing whose absence makes canopy structurally useless, and it makes the
chart comment true.

**Honest limitation, stated up front:** on a *fully* blocked loop the request is never served,
so the 503 never renders and the probe fails by timeout instead. The tick earns its place in
the **partially saturated** regime, and in diagnosis: `kubectl describe pod` showing
`tick exceeded budget: 4200ms` is a different morning from a bare `Get ... context deadline
exceeded`. I am not claiming the tick detects the black-hole case. It detects the shape of
the problem before it becomes total, and it names it when it does.

### 2.2 `/v1/health/ready` — readiness: "should this replica receive traffic?"

**Touches upstream: YES — but only through bounded, retry-free async I/O.** The existing
`probe_dependency` (`src/health.py:60-108`, httpx async, `timeout=5.0`, no retries) is
already correct and is the *only* sanctioned way. Fix N-4: run the two probes under
`asyncio.gather` so the worst case is 5 s, not 10 s.

Adopt the sibling status-code contract (`X-Juniper-Readiness` header included):

| Condition | Code | `status` |
|---|---|---|
| backend is `service`, cascor + data healthy | **200** | `ready` |
| backend is `service`, an upstream unhealthy | **200** | `degraded` |
| backend is `demo` **and demo was explicitly requested** | **200** | `degraded` |
| backend is `demo`/`unavailable` **and demo was NOT requested** | **503** | `not_ready` |
| `websocket_manager` unbound | **503** | `not_ready` |

The fourth row is the load-bearing change and the heart of this design. **Unrequested
simulation is a not-ready condition**, because the traffic this replica would serve is
fiction. It needs no new plumbing — it reuses a status code the siblings already emit and
that the chart comment already promised. And it is the one place in the system where the
orchestrator, not a human, can act on the lie.

Upstream outages deliberately stay at **200/degraded**: canopy with cascor down but a real
backend is still a useful read-only dashboard, and flapping a replica out of the ingress
because a *downstream* service blinked is a self-inflicted outage.

### 2.3 `/v1/health` (and deprecated `/health`, `/api/health`) — aggregate/human view

**Touches upstream: NEVER.** It reports **cached** dependency verdicts and in-process facts
only. Sibling parity is preserved: like cascor and data, it stays **always 200** and is an
informational surface, not a probe. Its `status` field, however, stops being a literal:

```jsonc
{
  "status": "ok" | "degraded",       // "degraded" whenever backend_state != "service"
                                     //   or any dependency verdict is stale/unhealthy
  "service": "juniper-canopy",
  "version": "...", "git_sha": "...", "build_date": "...",   // unchanged
  "timestamp": 1.7e9,
  "active_connections": 3,           // in-process, unchanged

  // ── honest backend identity (replaces the bare `demo_mode` boolean) ──
  "backend_state": "service" | "demo" | "unavailable",
  "demo_mode": true,                 // kept for back-compat; == (backend_state == "demo")
  "demo_mode_requested": false,      // ← the field that makes the lie visible
  "data_provenance": "live" | "simulated" | "cached" | "unavailable",

  // ── cached dependency verdicts, with visible age ──
  "cascor_available": false,
  "cascor_checked_age_seconds": 4.1,
  "juniper_data_available": true,
  "juniper_data_checked_age_seconds": 4.1,

  // ── cached in-process-derived facts, with visible age ──
  "training_active": false,
  "training_active_age_seconds": 4.1
}
```

`demo_mode_requested: false` alongside `demo_mode: true` is the whole point: **the pair is
self-diagnosing.** A single boolean cannot tell an operator whether the simulator is intended.

---

## 3. Degraded-state semantics, and the honesty guarantee

### 3.1 Verdict on the four options in the brief

| Option | Verdict |
|---|---|
| Serve a cached/last-known status | **Adopt** — but only for *in-process-derived* facts on health endpoints, with the age exposed. Never as a substitute for training metrics. |
| Request-time `cascor_available` mirroring `juniper_data_available` | **Adopt the concept, reject the model.** The thing it mirrors is stale-forever (N-3). Both must become refreshed-with-age. |
| Explicit "backend unreachable" UI state | **Adopt, and escalate** — a corner badge is insufficient; see H4. |
| Fail affected routes fast with a clear error | **Adopt** — this *is* the degraded state, and it is what makes the guarantee cheap. |

### 3.2 The guarantee, in one sentence

> **Fabricated data cannot be mistaken for real, because in the unrequested case it is never
> produced.**

Not "labelled". Not "warned about". **Not produced.** Every mechanism below H1 is
defence-in-depth for the case where H1 is later weakened.

### H1 — Delete the implicit runtime demo fallback (structural; the actual fix)

Remove `main.py:322-337`'s fallback to `create_backend(demo_mode=True)`. Demo becomes
reachable **only by explicit request**:
- `settings.demo_mode is True`, or
- no `cascor_service_url` configured at all (`backend/__init__.py:56`, selection rule 5 —
  "I never asked for cascor"), or
- an explicit model selection through the existing `_swap_backend` seam (`main.py:3688`).

When cascor is unreachable at startup **and** demo was not requested, canopy starts in a new
third state: **`unavailable`**.

*Does this cost anything legitimate?* I checked. It does not. The implicit fallback fires in
exactly one configuration — `CASCOR_SERVICE_URL` set **and** `DEMO_MODE=false`, i.e. the
operator explicitly asked for real cascor. The Compose demo profile does not rely on it: the
`juniper-canopy-demo` service points at a **demo cascor service**
(`docker-compose.yml`, `JUNIPER_CANOPY_CASCOR_SERVICE_URL: "http://juniper-cascor-demo:8200"`),
so it runs in *service* mode. A developer wanting the simulator sets `DEMO_MODE=true` or
unsets the URL. **The fallback's entire reachable domain is the configuration in which
fabricating data is wrong.**

### H2 — `UnavailableBackend`: an honest third state

A real `BackendProtocol` implementation, so nothing in `main.py` needs a null check:

- `backend_type == "unavailable"`; `is_training_active() → False` **with zero I/O**;
- every data getter returns empty/`None` — **never a synthesised value**;
- every control route → **503** `{"error":"cascor unreachable","backend_state":"unavailable",
  "last_error":"...","last_attempt_age_seconds":N}`;
- holds the `cascor_available` verdict + last error, refreshed by the §3.3 prober;
- **self-heals**: when the prober sees cascor healthy, promote to `ServiceBackend` through
  the **existing `_swap_backend` machinery** (`main.py:3688-3700`), which already does
  create-then-initialise-then-swap-then-shutdown and already refuses to swap mid-training.
  Reuse it; do not write a second swap path.

This is what makes "fail fast with a clear error" cheap: one class, and every route inherits
the behaviour.

### H3 — Bounded, non-blocking upstream reads (fixes X7-A properly)

1. **Health endpoints call nothing upstream.** `/v1/health`, `/health`, `/api/health` and
   readiness's `details` read the §3.3 cache. This removes `main.py:1050`, `:1076`, `:1133`
   from the blocking path *by construction*, not by making the call faster.
2. **Route the two bypasses through the breaker** — `cascor_service_adapter.py:1089-1099`
   and `:436-447` (N-5) — matching `:1968-1974`. Consistency, not the fix (N-7).
3. **Give status reads their own client budget.** The `timeout=30, retries=3` default (N-6)
   is wrong for anything a probe depends on. Construct with an explicit small budget
   (`timeout=2, retries=0`) for status/health reads, or add a per-call timeout override. This
   is what actually turns 123 s into ~2 s.
4. **Do not "fix" this with a bare `asyncio.to_thread`.** N-8: it converts a diagnosable loop
   stall into an invisible 40-token threadpool stall shared with every sync route. Where an
   offload is genuinely needed, pair it with `asyncio.wait_for` **and** a dedicated
   `anyio.CapacityLimiter` so cascor calls can never consume the shared pool.

### H3.1 — The status cache (the thing `values.yaml:225` already promised)

One background task, started in lifespan, cancelled on shutdown:

- every **5 s** (matching the existing `CASSANDRA_STATUS_CACHE_TTL_SECONDS = 5`,
  `canopy_constants.py:667`), refresh: cascor reachability, juniper-data reachability,
  `training_active`;
- each entry stored as `(value, as_of_monotonic, source)`;
- **all** health endpoints read it non-blockingly and expose `*_age_seconds`;
- an entry older than **3 × TTL** is reported as `stale`, and a stale *dependency* verdict
  reads `unhealthy`, never `healthy` — **a cache must fail closed**;
- **this also fixes `juniper_data_available` (N-3)**, which stops being write-once. Ship that
  in the same change: leaving a stale-forever flag next to a freshly-correct one is worse
  than either alone.

Precedent for the pattern already exists in-repo: `_network_cache` with a 30 s TTL
(`cascor_service_adapter.py:1020`), and juniper-data's readiness probe cache
(`juniper_data/api/routes/health.py`, `_PROBE_CACHE_TTL_SECONDS = 5.0`).

### H4 — Provenance on the wire and on the screen (fixes N-9)

1. **`data_provenance` on every payload that can carry numbers** — `/api/state`,
   `/api/metrics`, `/api/v1/candidates/pool-history`, the snapshot routes, and every WS
   frame: `"live" | "simulated" | "cached" | "unavailable"`. One field, set at the backend
   boundary, so a new route cannot forget it.
2. **The UI's mode must come from the server.** Delete the hardcoded `mode: "live"` at
   `websocket_client.js:377` and the `|| "live"` default at `ws_dash_bridge.js:145`;
   carry `backend_state` on the WS `initial_state` frame and preserve it across
   `_notifyConnectionStatus()`. Fix the seed at `dashboard_manager.py:1919` to read the
   server's `backend_state`, not `get_settings().demo_mode` — the identical correction
   `main.py:333-337` already applied to the metrics gauge.
3. **A page-level banner, not a corner badge**, whenever `backend_state != "service"`:
   persistent, non-dismissable, high-contrast, and **inside the plot area** so it survives a
   screenshot cropped to a chart. The realistic exfiltration path for fabricated data is a
   figure pasted into a report, and a badge in the header does not survive that crop.
4. **Label the fabricated snapshot unconditionally** (N-10): make the demo branch of
   `create_snapshot` (`main.py:2282-2322`) return `"simulated": true` and
   `"path": null` regardless of the caller's description, or — better, and consistent with
   H1 — **refuse** (`503`) to create a snapshot in an unrequested-demo state.

### H5 — Make the orchestrator and the operator able to see it

- **Readiness 503** on unrequested demo (§2.2) — the machine-actionable signal.
- **A new gauge** `juniper_canopy_demo_mode_requested` (from `settings.demo_mode`) beside the
  existing `juniper_canopy_demo_mode_active` (`observability.py:120-122`).
- **A new Prometheus alert** (fixes N-11):

```yaml
- alert: CanopyUnrequestedDemoMode
  expr: >
    juniper_canopy_demo_mode_active{environment!="host-experiment"} == 1
    unless juniper_canopy_demo_mode_requested{environment!="host-experiment"} == 1
  for: 1m
  labels: {severity: critical, service: juniper-canopy}
  annotations:
    summary: "juniper-canopy is serving SIMULATED data without being asked to"
    description: >
      canopy fell back to the demo simulator. Every metric, topology and snapshot
      it is serving is fabricated. Treat all dashboard output since the fallback
      as invalid.
```

- **A startup log line at ERROR, not WARNING.** `main.py:328` currently logs the fallback at
  `warning`. An unannounced switch to fabricated data is not a warning.

---

## 4. Orchestration changes

### 4.1 Should liveness ever depend on an endpoint that can touch a dependency?

**No. Categorically.** Liveness's only remedy is a restart, and a restart cannot reach a
peer's socket. A dependency-observing liveness probe turns a single upstream outage into a
fleet-wide restart storm across every replica that observes it — and here, per §1.2 C-4, into
a **fleet-wide switch to fabricated data**. Canopy's liveness target
(`/v1/health/live`) is already correct; the defect is that the endpoint is a no-op (C-1) and
that the *loop* it runs on is blocked by a different endpoint.

### 4.2 Docker Compose — `juniper-deploy/docker-compose.yml`

Change the target for all **three** canopy services (`:730-733`, `:812-815`, `:867-870`) —
missing one leaves a variant on the old contract:

```yaml
    healthcheck:
      test: ["CMD", "python", "-c",
             "import sys,urllib.request;\
              r=urllib.request.urlopen('http://localhost:8050/v1/health/ready', timeout=4);\
              sys.exit(0 if r.status == 200 else 1)"]
      <<: *healthcheck-canopy
```

Two changes, both deliberate:
- **target `/v1/health/ready`, not `/v1/health`** — after §2, readiness is the only canopy
  endpoint with real status-code semantics. `/v1/health` is always 200 by design (sibling
  parity) and therefore cannot express "unhealthy" at all.
- **explicit status check** — `urlopen` raises on 4xx/5xx, so the check *happens* to work
  today, but an explicit exit code makes the contract legible and survives a future switch to
  a non-raising client.

Anchor `x-healthcheck-canopy` (`docker-compose.yml:58-62`): keep `interval: 15s`,
`retries: 5`, `start_period: 20s`; tighten `timeout: 10s → 6s` **once N-4 is fixed** (probe
worst case drops 10 s → 5 s). Before N-4 is fixed, 6 s would false-fail on a double upstream
outage.

Also update `juniper-canopy/Dockerfile:107-108` to `/v1/health/ready` for parity. Compose
overrides it, but a bare `docker run` uses it, and divergence between the two is exactly the
kind of drift that produces "works in compose, unhealthy in prod".

**Compose still does not restart on `unhealthy`** — confirmed, and I am **not** proposing to
change that (no autoheal sidecar). With H1 in place the correct Compose posture is: honest
`unhealthy` marking, no restart. A restart cannot fix an upstream outage, and after H1 the
non-restarting hang is no longer dangerous — it is a service correctly reporting that it has
nothing true to say.

### 4.3 Helm — `juniper-deploy/k8s/helm/juniper/values.yaml:222-239`

```yaml
  # Canopy's liveness tick asserts the WebSocket-manager singleton is bound and its
  # event loop is set, and 503s ({"status":"unresponsive"}) when the in-process tick
  # exceeds juniper_observability.LIVENESS_TICK_BUDGET_MS. It touches NO dependency:
  # a cascor/juniper-data outage is not repairable by restarting canopy.
  # Readiness DOES probe upstreams (bounded async httpx, 5s, no retries, concurrent):
  #   200 ready | 200 degraded (upstream down, or demo explicitly requested)
  #   503 not_ready (ws_manager unbound, OR the backend fell to demo/unavailable
  #                  without demo being requested — see juniper-canopy H1/H2).
  # There is no cached-metrics mode: when cascor is unreachable canopy serves NOTHING,
  # it does not simulate.
  healthcheck:
    startup:                       # NEW — slow starts stop being liveness's problem
      path: /v1/health/live
      periodSeconds: 2
      timeoutSeconds: 2
      failureThreshold: 30         # up to 60s to become live
    liveness:
      path: /v1/health/live
      initialDelaySeconds: 0       # 20 -> 0; the startupProbe owns cold start
      periodSeconds: 10            # 15 -> 10
      timeoutSeconds: 3            # 10 -> 3   (endpoint does ~0 work; 10s tolerated a
                                   #            10s event-loop stall as "healthy")
      failureThreshold: 3          # 5  -> 3
    readiness:
      path: /v1/health/ready
      initialDelaySeconds: 5       # 15 -> 5   (startupProbe gates traffic anyway)
      periodSeconds: 10            # unchanged
      timeoutSeconds: 5            # unchanged — valid only once N-4 (gather) lands
      failureThreshold: 3          # unchanged
```

Resulting liveness kill time: 3 × 10 s + ≤3 s ≈ **30-33 s**, down from 60-85 s.
`templates/canopy-deployment.yaml:84-99` needs a `startupProbe` block mirroring the liveness
one; no other template change.

**And this retune must not ship before H1.** See §5.

### 4.4 Prometheus — `juniper-deploy/prometheus/alert_rules.yml`

Add `CanopyUnrequestedDemoMode` (§H5) to the `juniper_infrastructure` group (near `:224`).

### 4.5 Same PR or separate?

Separate — different repos force it — but the **ordering is a hard constraint, not a
preference**:

| PR | Repo | Contents | Gate |
|---|---|---|---|
| **A** | juniper-canopy | H1, H2, H3, H3.1; liveness tick; readiness codes + `X-Juniper-Readiness` + `gather` (N-4); breaker on both bypasses (N-5); status-client timeout budget (N-6); fix `juniper_data_available` staleness (N-3); `demo_mode_requested` gauge; fallback log → ERROR | none |
| **B** | juniper-canopy | H4: `data_provenance`, server-sourced UI mode, banner, snapshot labelling/refusal | after A (needs `backend_state` on the wire) |
| **C** | juniper-deploy | Compose target + timeout, Helm retune + startupProbe, `values.yaml` comment correction (C-5), Prometheus alert, `canopy.image.tag` bump | **after A, and the tag bump must be in this same PR** |

**Why C must not lead.** Shipping C's tighter liveness against a canopy image without H1
takes today's 60-85 s window to fabricated data and makes it **30 s**. And C's Compose switch
to `/v1/health/ready` against a pre-A image is worse than useless: that endpoint today never
503s (§1.1) and can take 10 s (N-4), so the healthcheck would be *less* informative and more
prone to timeout-flapping than the one it replaced. **The chart's `image.tag` bump belongs in
PR C**, so the retune cannot be applied to an image that has not got the fix.

---

## 5. Severity and sequencing

**Does the integrity chain justify prioritising this above other work? Yes — and the reason
is C-4, not the Helm chart.**

**Evidence for P1:**
1. **It is silent.** Every surface an operator actually looks at reports healthy: `/v1/health`
   → `status:"ok"` (literal, `main.py:1070`); the UI badge → green `"WS: Connected"` (N-9,
   the demo branch is unreachable); readiness → 200 (`main.py:1093-1141`); Compose →
   `healthy` while cascor is down, because `/v1/health` answers. The only truthful signals are
   a `WARNING` log line at `main.py:328` and a JSON field no human reads.
2. **It is not latent (C-4).** Only the pod-restart step needs Helm. Fabrication needs only a
   cold start with cascor down: a local dev run, or a Docker daemon restart of the canopy
   container under `restart: unless-stopped`.
3. **The fabricated output is durable and semi-labelled (N-10).** Demo snapshot creation
   returns 201 with an invented size and a non-existent path, and writes a row into the
   `snapshot_history.jsonl` that lives in the real cascor snapshot archive. That row *is*
   tagged `mode: "demo"`; the API response and the UI are not. This repo has spent multiple
   sessions on snapshot provenance and classification; a route that injects phantom rows into
   that archive is a direct regression against completed work.
4. **It is the platform's whole purpose.** juniper-ml exists to produce research
   measurements. This repo's own operating memory records `cascor reported metrics are
   SELECTED-ON` and an arc of measurement-integrity work. **A dashboard that silently
   simulates is that same failure class one layer up** — and it is worse, because the
   simulator was *built to look realistic* (`demo_mode.py:519-527`: *"Simulates realistic
   training behavior… realistic loss curves"*).
5. **Nothing detects it (N-11).** The single metric that knows the truth is wired only as an
   alert suppressor.

**Evidence for *not* over-rating X7-A:** it recovers unaided, causes no data loss, and the
worst case is a bounded stall. On its own it is a solid P2.

**Sequencing — the practical output:**

1. **First, and alone if only one thing ships: H1 + H2** (delete the implicit fallback, add
   `unavailable`). This is a small, surgical change to `main.py:322-337` plus one new class.
   It removes the P1 outright and makes every downstream decision safe.
2. **Then H3 + H3.1** — de-block the health endpoints and bound the client budget. Fixes
   X7-A properly.
3. **Then §2's contract** — liveness tick, readiness codes, header. Aligns canopy with cascor
   and data.
4. **Then PR C** — the orchestration retune, with the chart tag bump.
5. **Then H4** — provenance on the wire and the banner. Last because after H1 there is no
   fabricated data left to label in the unrequested case; H4 is defence-in-depth and it makes
   *requested* demo honest.

**The anti-pattern to name explicitly in the PR:** "just make the health endpoint fast" is
step 2 without step 1. It closes the visible symptom, removes the hang that is currently the
*only* loud signal that cascor is down, and leaves the platform silently simulating. It would
look like a complete fix on every dashboard.

---

## 6. Tests and verification

Proving a degraded state is *honest* means proving two things: it does not lie, and the
machinery that would catch it lying is itself working. The last is the harder one — this
repo's `vacuous-pass check class` note exists for exactly this.

**T-1 — Health endpoints make no outbound connections (drift guard).**
Fixture monkeypatches `socket.socket.connect` to raise; assert `/v1/health`, `/health`,
`/api/health`, `/v1/health/live` all return 200. *Ratchet form* (the version that survives a
future refactor): a static check over the three health routes' call graphs failing on any
reference to `requests.*` or a sync `httpx.Client`. Without the static form this test passes
forever while a new blocking call is added behind a mock — the exact drift that produced N-2.

**T-2 — Black-hole test (the X7-A regression pin).**
Bind a listening socket that accepts and never responds; point `CASCOR_SERVICE_URL` at it.
Assert every health endpoint returns in **< 1 s**, and — crucially — that a *concurrent*
stream of `/v1/health/live` requests keeps p99 **< 250 ms** for 60 s while a data route is
stalled. The concurrency assertion is what distinguishes a real fix from the N-8
threadpool-stall pseudo-fix; a serial test passes under both.

**T-3 — The anti-vacuous-pass test: silent demo fallback reporting healthy.**
*This is the check the brief asks for.* Start canopy with `JUNIPER_CANOPY_DEMO_MODE=false`
and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` pointed at a **closed** port. Assert **all** of:
- (a) `backend.backend_type == "unavailable"` — **never `"demo"`**;
- (b) `GET /v1/health/ready` → **503**, body `status == "not_ready"`,
      header `X-Juniper-Readiness: not_ready`;
- (c) `GET /api/state`, `/api/metrics` → **503**, not a payload;
- (d) `GET /v1/health` → 200 with `status:"degraded"`, `backend_state:"unavailable"`,
      `demo_mode:false`, `demo_mode_requested:false`, `cascor_available:false`;
- (e) `POST /api/v1/snapshots` → **503**, and `snapshot_history.jsonl` gains **no** row;
- (f) **over 30 s, zero WebSocket frames carrying a numeric loss/accuracy are broadcast.**

(f) is the assertion that tests the *actual* property. (a)-(e) test flags; (f) tests whether
fiction was emitted. A future refactor could satisfy every flag and still simulate.

**T-4 — The inverse: requested demo must also be honest.**
With `JUNIPER_CANOPY_DEMO_MODE=true`: demo is permitted, but assert `/v1/health/ready` →
**200 `degraded`** (never `ready`), `demo_mode_requested: true`, every metrics payload carries
`data_provenance: "simulated"`, and the UI store's `mode == "demo"`. Catches "we made
unrequested demo honest and left requested demo lying" — which, per N-9, is the status quo.

**T-5 — The UI-provenance test (catches the N-9 class).**
Playwright, against a canopy in requested-demo mode: assert the connection badge renders
**"WS: Demo"** and the page-level banner is present. This is the only check that would have
caught `websocket_client.js:377`'s hardcoded literal — a unit test of
`CONNECTION_INDICATOR_JS` passes today, because the JS is correct; the *input* is what lies.
Per this repo's E2E driver notes: settle before read, and assert on rendered text, not on the
store.

**T-6 — The honesty differential (the generic form).**
Run one scripted scenario — start training, poll for 30 s — twice: once against real cascor,
once against a closed port. Assert the two runs are **distinguishable from the API surface
alone**: the closed-port run yields zero `/api/metrics` rows and 503s on control routes.
Today they are indistinguishable, and *that* is the defect. This is the check I would keep if
I could keep only one, because it does not depend on any flag name surviving a refactor.

**T-7 — Orchestration contract tests, in `juniper-deploy/tests/`.**
`tests/test_helm_chart_probes.py` already asserts probe *paths*
(`test_liveness_probe_path_uses_health_live:102`,
`test_readiness_probe_path_uses_health_ready:121`). Extend it:
- every canopy Compose service's healthcheck URL == `/v1/health/ready` (**all three** — the
  test must enumerate, not sample; that is how one of the three gets left behind);
- liveness `timeoutSeconds` < readiness `timeoutSeconds`;
- liveness kill budget `failureThreshold × periodSeconds` within a declared bound;
- **`canopy.image.tag` >= the release carrying H1** — encodes the PR-C ordering gate (§4.5)
  as a check rather than a paragraph nobody rereads.

**T-8 — Alert rule test.** `promtool test rules` over the new
`CanopyUnrequestedDemoMode`: a series with `demo_mode_active=1, demo_mode_requested=0` fires
within 2 min; `1,1` does not; `0,0` does not.

**T-9 — Manual operator drill (once, recorded in notes).**
Bring up the full Compose stack, `docker stop juniper-cascor`, `docker restart
juniper-canopy`. **Pass criterion: an operator looking only at the dashboard and
`docker ps` can tell within 60 s that the data is not real.** Today they cannot. This is the
only check that tests the thing that actually matters — what a human sees — and no automated
suite substitutes for running it once.

---

## 7. The strongest objection to my own design

**Objection: H1 trades a soft failure for a hard one, and I may be wrong about who that
hurts.**

Today, a developer who runs canopy with a stale `CASCOR_SERVICE_URL` and no cascor gets a
working dashboard. Under H1 they get an empty dashboard and 503s everywhere. I argued in §H1
that the fallback's reachable domain is exactly the configuration where fabrication is wrong
— *"I asked for real cascor"*. **That argument is about configuration, not intent, and the
gap between them is where I could be wrong.** A researcher iterating on the frontend
plausibly leaves `CASCOR_SERVICE_URL` in their shell profile for months and relies on the
fallback as an unwritten convenience. I found no evidence for this — but I also found no
evidence against it, because I inspected code and config, not people. If that user exists,
H1 breaks their loop with a 503 and a message they will read as a bug, and the likely outcome
is that someone quietly restores the fallback in six months with a comment about developer
experience — at which point the P1 returns, and the tests in §6 that would catch it are the
ones most likely to be relaxed alongside it. **The failure mode of my design is that it gets
reverted.**

Three secondary weaknesses I would want challenged:

1. **The liveness tick may be theatre in the case that matters.** I said so plainly in §2.1,
   but I want to be blunt: on a fully blocked loop the tick never runs, so its 503 is
   unreachable and the probe fails by timeout — the same outcome as the no-op it replaces.
   It buys diagnosis and partial-saturation detection. If someone argues that is not worth
   the code, the honest answer is that its main value is **making `values.yaml:224` true**,
   which is a documentation fix wearing a code fix's clothes. Sibling parity carries the rest
   of the weight.

2. **Readiness-503 on unrequested demo can strand a single-replica deployment.**
   `canopy.replicaCount: 1` (`values.yaml:181`). Under H1+H2 a cascor outage takes canopy
   out of the Service endpoints entirely — so an operator who *wants* to open the dashboard
   to see what is wrong gets a connection refused from the ingress, not an "unavailable"
   page. That is arguably a worse operator experience than a page that says "backend
   unreachable". A defensible alternative is 200/`degraded` for the unavailable state, with
   the 503 reserved for `demo`-without-request. I chose the stricter line because
   `unavailable` and unrequested-`demo` should not have different contracts (a future
   refactor that collapses them must fail *safe*), but I hold it loosely, and it is the
   single most reversible decision here.

3. **Everything rests on `demo_mode_requested` being derived correctly.** If it is ever read
   from the wrong place — the way `dashboard_manager.py:1919` reads `get_settings().demo_mode`
   where it needs `backend.backend_type` — the whole honesty guarantee inverts silently: an
   unrequested fallback reports as requested and every alert stays quiet. Note that this is
   the *exact* mistake already present in this codebase, twice (N-9), and that
   `main.py:333-337` contains a comment warning against it. That the same repo made this
   error, documented it, fixed it in one place and left it in two others is the best available
   evidence that my design's central invariant is one refactor away from breaking. T-4 and
   T-5 exist to pin it; whether they survive is the open question.
