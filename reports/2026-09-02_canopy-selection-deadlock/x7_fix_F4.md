# X7 fix design — F4, architecture lens

**Author**: fix-design author F4 (architecture lens)
**Date**: 2026-09-02
**Defect**: X7 — synchronous retrying `requests` I/O inside `async def` route handlers on a
single-worker uvicorn blocks the whole event loop.
**Status**: design only. No repository file was edited.

---

## 0. The one-paragraph answer

**X7 is not an architecture defect. It is convention drift inside an architecture that already
made the right call and wrote it down.** Canopy has 30 `asyncio.to_thread` offload sites in
`src/main.py`, two of which carry comments explaining *this exact failure mode* in *these exact
words* — "so a slow cascor cannot stall the single uvicorn worker" (`src/main.py:3548`) and
"runs off the event loop so the single uvicorn worker never stalls (SEC-F20)"
(`src/main.py:1629`). Canopy also owns a configured `CircuitBreaker`
(`src/backend/circuit_breaker.py`, wired at `src/backend/cascor_service_adapter.py:518`) whose
whole job is bounding a dead-cascor blast radius.

**Both mechanisms exist, are adopted, are tested — and X7 lives in the fraction of the egress
surface neither one covers.** Measured: of 72 route handlers in `main.py` (**all** `async def`;
FastAPI's `def`-threadpool escape hatch is used **nowhere**), 51 reach cascor, **14 are offloaded
and 37 are not**. The breaker covers **5 of 45** cascor client invocations. And the prior fix for
this very mechanism — SEC-F20 — shipped as a *code comment with no test*: grepping the whole
repository for `SEC-F20` returns exactly one hit, that comment (§1.3).

So the fix is *coverage plus a guard that makes the convention enforceable*, and it is small. The
self-call architecture is a real and separate problem that this defect merely stood next to. I
recommend shipping the small fix now and explicitly **not** attaching the architecture to it —
and §6 is me naming which of my own instincts to reject.

---

## 1. Anchor verification

Everything I was handed, re-derived independently. Two corrections and several additions.

### 1.1 Self-call counts — CONFIRMED, with a refinement

| Claim | Verdict | Evidence |
|---|---|---|
| `dashboard_manager.py` makes ~37 self-calls | **CONFIRMED** | `grep -c '_api_url' src/frontend/dashboard_manager.py` → **37** |
| 60 blocking `requests.*` sites in `src/frontend/` | **CONFIRMED (grep); 58 real** | grep of `requests.{get,post,...}(` → 60 lines: `dashboard_manager.py` 36, `network_editor_panel.py` 5, `metrics_panel.py` 5, `hdf5_snapshots_panel.py` 5, `redis_panel.py` 2, `cassandra_panel.py` 2, `candidate_metrics_panel.py` 2, `internal_api.py` 1, `replay_player_panel.py` 1, `dataset_plotter.py` 1. An AST walk counts **58** real `ast.Call` nodes; the delta is docstring/comment prose (e.g. `internal_api.py:21`). Use **58** for anything load-bearing. |
| First commit `b64f6df` had 14 | **CONFIRMED** | `git show b64f6df:src/frontend/dashboard_manager.py \| grep -c _api_url` → **14** |
| No design note argues *for* the pattern | **CONFIRMED** | The only prose that discusses it (`src/frontend/internal_api.py:39-46`) argues *against* it and points at the deferred Option C. |

### 1.2 Self-call timeout coverage — a claim I tried to make and had to withdraw

An AST audit initially flagged `dashboard_manager.py:7144` as the one self-call lacking
`timeout=`. **That was a false positive of my own tooling.** The call passes timeout through a
`**post_kwargs` unpack (`src/frontend/dashboard_manager.py:7141`), which an AST keyword scan
cannot see. **All 58 self-calls are timeout-bounded.**

I am recording the miss rather than deleting it, because it is the *vacuous-check* class in
miniature: an audit that reads "1 defect found" when the truth is "my check has a blind spot."
Any lint I propose in §7 must be written against a `**kwargs`-aware check or it will ship the
same false confidence.

The consequence matters for the mechanism: because every self-call *is* bounded (2 s POST /
5 s GET / 10 s long-POST / 30 s restart — `src/canopy_constants.py:421-432`), a2wsgi's WSGI
threads do eventually unpark. They then immediately re-park, because the pollers fire again.
So the pool stays saturated *for the duration of the loop block* and drains once the loop
recovers. That is exactly the observed "recovers unaided."

### 1.3 The remedy is already the house style — the most important finding

`src/main.py` contains **30 `asyncio.to_thread` offload sites**, and they are concentrated on
precisely the backend/cascor calls:

```
main.py:1239  live_status, canopy_params = await asyncio.to_thread(_fetch_live_status_and_params)
main.py:1360  return {"history": await asyncio.to_thread(backend.get_metrics_history, count)}
main.py:1423  topology = await asyncio.to_thread(backend.get_network_topology)
main.py:3553  if not await asyncio.to_thread(backend.is_training_active):
main.py:3899  result = await asyncio.to_thread(backend.apply_params, **backend_updates)
main.py:4117  result = await asyncio.to_thread(backend.swap_dataset_live, **params)
   … ~22 more
```

and two of them are annotated with the X7 mechanism verbatim:

- `src/main.py:3548` — *"Status reads run off the event loop (`asyncio.to_thread`) so a slow
  cascor cannot stall the single uvicorn worker…"*
- `src/main.py:1629` — *"Blocking DNS runs off the event loop so the single uvicorn worker never
  stalls (SEC-F20)."*

**A prior defect (SEC-F20) already litigated this exact mechanism and established the exact
remedy, in this exact file.** X7 is the same defect recurring at sites the SEC-F20 sweep did not
reach. That reframes the whole engagement: this is not "canopy chose a bad architecture," it is
"canopy chose the right one and has no guard that keeps it chosen."

**The coverage hole is now measured.** An independent AST census (provenance-aware, resolving
`backend.*`, `backend._adapter.*` and locals bound from `_require_service_adapter()`) gives:

| | count |
|---|---:|
| route decorators in `src/main.py` | **72** |
| …of which are `async def` | **72 — all of them; zero plain `def`** |
| handlers that reach cascor | **51** |
| …fully offloaded via `asyncio.to_thread` | **14** |
| …with ≥1 **bare synchronous cascor call on the event loop** | **37** |

**That "72 of 72" line is itself a finding.** FastAPI's built-in escape hatch — declaring a
handler `def` instead of `async def`, which makes Starlette run it in a threadpool — is used
**nowhere** in this file. The single cheapest mitigation for this entire defect class is
unexercised, and 37 handlers are one keyword away from safety.

The offload was applied opportunistically, and it shows: essentially everything after `main.py`
line ~3800 is offloaded, and almost nothing before line ~1450 is. `/api/state`
(`main.py:1236-1239`) is the model implementation — both sync calls wrapped in a nested
`_fetch_live_status_and_params()` handed to `await asyncio.to_thread(...)`, with a comment at
`main.py:1235` naming the hazard.

**And here is the proof of that last clause.** Grepping the entire repository — every `.py` and
every `.md` — for `SEC-F20` returns **exactly one hit**: the code comment at `src/main.py:1628`.
No regression test. No note. No requirement entry. The prior fix for X7's mechanism shipped as a
*comment*, and a comment cannot fail a build. X7 is what a convention with no enforcement looks
like four months later. This is the strongest single argument in this document for Phase 1 item 4
(§7): without the guard, Phase 0 is just the SEC-F20 sweep run a second time, and there will be a
third.

Canopy is also already partly async-native on egress: the juniper-data path uses
`httpx.AsyncClient` correctly (`src/main.py:1695`, `src/main.py:1635`). It is the *cascor* egress
specifically that is sync.

### 1.4 `src/api/` does not exist — the deferred design's import example targets a phantom

Option C §2 illustrates the refactor as `from api.status import get_status`. **There is no
`src/api/` directory.** All route handlers live in `src/main.py`, a ~4,400-line module. This is
not pedantry; it changes Option C's cost class (§4.3, §6).

### 1.5 The circuit breaker is real, configured, and covers 11% of the surface

`src/backend/cascor_service_adapter.py` makes **45** `self._client.*` cascor invocations. Exactly
**5** are wrapped in `self._cb.call(...)` (lines 1970, 1980, 2099, 2117, 2130). The breaker is
configured at `src/canopy_constants.py:648-650` — `failure_threshold=5`,
`recovery_timeout=60.0`.

So canopy owns the mechanism that would convert "cascor is down → every call pays full retry
budget" into "cascor is down → calls fail fast for 60 s," and applies it to **1 call in 9**.
This is the second already-adopted mechanism with a coverage hole, and it is the one that most
directly attacks X7's *magnitude* (the ~123 s figure).

Resolving the `service_backend.py` delegation layer, the **Dash-reachable** split is:

- **Guarded**: `/api/status`, `/api/train/status` (→ `service_backend.py:166` → adapter `:1970`),
  `/api/network/stats` (→ adapter `:1980`), `/api/dataset` (→ `service_backend.py:271` → adapter
  `:2130`).
- **Unguarded**: `/api/stream_health` (`main.py:1333`), `/api/decision_boundary`
  (→ `service_backend.py:297` → adapter `:2184`), `/api/v1/workers/{list,stats}`
  (`main.py:3254`, `:3206` — these reach `backend._adapter._client` **directly**, bypassing the
  adapter wrapper *and* the breaker), all five `/api/train/*` verbs, `/api/train/restart`, and the
  three dataset mutators.

Two qualifications that matter for §7 and §8:

1. **"Guarded" is not "free."** The breaker opens only after `failure_threshold=5` consecutive
   failures, so the first five ticks each pay the full 3.0 s (≈15 s), and `recovery_timeout=60.0`
   means one probe pays full cost every 60 s thereafter. **This is the mechanism behind "recovers
   unaided."**
2. **The health endpoints bypass the breaker on a path that is otherwise guarded.** `/v1/health`,
   `/health`, `/api/health` and `/v1/health/ready` all call `backend.is_training_active()` →
   `service_backend.py:161` → `cascor_service_adapter.py:1089-1091`, which calls
   `self._client.get_training_status()` **directly at line 1091** — the same underlying client
   method the breaker protects at adapter `:1970`, reached by a route that skips it. See §3.4.

### 1.6 `workers=1` is not written anywhere — it is a consequence of the entrypoint

`src/main.py:4419`:

```python
uvicorn.run(app, host=host, port=port, log_level="info" if debug else "warning")
```

No `workers=` kwarg. And the first argument is the **app object**, not an import string.
uvicorn 0.49.0, `uvicorn/main.py:606`:

> `"You must pass the application as an import string to enable 'reload' or 'workers'."`

It **warns and continues with one worker**. Consequences in §5.

**And the repo already contains a stale assertion to the contrary.**
`conf/app_config.yaml:400-401` declares `workers: 4` with a `UvicornWorker` class — **dead
config, not consumed by the `Dockerfile:110` → `main.py:4419` launch path.** So a reader who
checks configuration before code will conclude canopy runs four workers. It runs one. The
vacuous-fix hazard in §5.1 is therefore not hypothetical: half of it has already happened, and
the artifact that would confirm the wrong answer is sitting in `conf/`.

### 1.7 Process-local state inventory (input to §5)

| State | Location | Rebound at runtime? |
|---|---|---|
| `loop_holder = {"loop": None}` | `main.py:119` | yes, at startup |
| `training_state = TrainingState()` | `main.py:123` | yes (`global`, `main.py:286`) |
| `backend = None` | `main.py:480` | **yes — hot-swapped** (`global backend`, `main.py:3703`; `backend = new_backend`, `main.py:3722`) |
| `current_nn_model`, `_resolved_service_url` | `main.py:485-486` | yes |
| `dashboard_manager = DashboardManager({})` | `main.py:489` | no |
| `_demo_snapshots: deque` | `main.py:2203` | append-only, in-memory |
| `websocket_manager = WebSocketManager()` | `communication/websocket_manager.py:1194` | no, but `self.active_connections: Set[WebSocket]` (`:217`) mutates constantly |

### 1.8 The import cycle nobody has paid down

`src/frontend/dashboard_manager.py`'s imports (lines 36-75) include **no** `main` and **no**
`backend`. They cannot: `main.py:489` constructs `DashboardManager` at module scope, so
`main → dashboard_manager` is an existing edge. Any direct in-process call from a Dash callback
into a handler or the backend singleton closes a **circular import**.

**This is why the self-call pattern accreted.** It is not an architectural preference. It is the
path of least resistance around a dependency cycle that was never broken, and it does real work
today: the loopback HTTP call is a *late-binding* indirection that re-resolves `main.backend` at
call time and therefore **survives the model hot-swap at `main.py:3722`**. A naive Option C
(`from main import backend`) would capture a stale reference and silently keep serving the old
model after a `POST /api/model/select`.

That is a trap sitting directly in the path of the "obvious" refactor, and the deferred design
does not mention it.

---

## 2. Position on the self-call architecture

**Recommendation: (b), a direct in-process call into a shared service layer — as the end state,
scheduled, and explicitly not as the fix for X7.**

The reasoning, option by option:

- **(a) HTTP to its own API — status quo.** Wrong in principle: a process serializing to JSON,
  opening a loopback TCP socket, re-entering its own middleware stack, and deserializing, to
  reach a function in its own address space. It also couples two independent concurrency pools
  (§3.2) and pollutes the HTTP metric stream with synthetic traffic (deferred design §4.3). But
  it is *load-bearing today* for the hot-swap reason in §1.8, and it is the only shape that
  survives a future process split (deferred design §6.6). It should not be defended, but it must
  not be removed casually either.
- **(b) Direct call into a shared service layer.** Correct destination. Note the wording: **not**
  "call the route handler," which is what Option C §2 says. Call a *service layer* that both the
  route handler and the Dash callback depend on — deferred design §5.3's "option 1," which that
  document correctly identifies as "the right pattern" and then does not build its plan around.
  This simultaneously breaks the §1.8 cycle (the service layer imports neither `main` nor
  `dashboard_manager`) and removes the need for any async/sync bridge, because the service layer
  can expose a sync surface that `async def` handlers reach via the `asyncio.to_thread` hop they
  already use.
- **(c) WebSocket/push.** Right for a *subset*, already planned as `JR-CAN-PERF-004`, and by its
  own §3.2 it cannot cover raw topology (`GAP-WS-25`), decision boundary, redis, cassandra, or
  snapshots. It reduces the *trigger population* (§3.3); it does not remove the mechanism.
  Complementary, not alternative.
- **(d) Client-side fetching from the browser.** Correctly ruled out of scope by the deferred
  design §7 — it trades the problem for a CORS/API-key-in-browser surface. I concur; do not
  reopen.

### 2.1 What changes, under (b)

1. A `src/services/` package holding plain, sync, dependency-free functions (`get_status()`,
   `get_metrics_history(n)`, …) that take a backend handle and return dicts.
2. A `get_backend()` accessor — the single fix that makes late binding explicit instead of
   accidental, and the prerequisite for *any* direct-call migration surviving `main.py:3722`.
3. Route handlers in `main.py` become thin: validate, `await asyncio.to_thread(service_fn, …)`,
   serialize.
4. `src/frontend/internal_api.py` grows `internal_call(path, …)` (deferred design §5.7 — the one
   piece of that document I would keep unchanged), dispatching `path → service_fn`. Call sites
   migrate mechanically; the dispatch table migrates one entry at a time behind it.

### 2.2 What it costs

Larger than the deferred design's "3–4× Option B" estimate, because §1.4 and §1.8 are additive
prerequisites it did not scope: extracting a service layer out of a 4,400-line `main.py`,
breaking a module cycle, introducing a backend accessor, and migrating ~50 `patch("requests.get")`
test sites (deferred design §5.6). Call it a multi-PR workstream measured in weeks, not a fix.

---

## 3. Are the self-calls and X7 the same defect?

**Related — and neither "the same" nor "independent." Specifically: the self-calls are the
dominant *trigger population* and the *outage amplifier*, but they are not the *mechanism*, and
removing them does not fix X7.**

This is the question I was asked to get right, so I will be explicit about each direction.

### 3.1 Removing the self-calls does NOT fix X7

The mechanism is sync I/O executing on the event loop, which is a property of **the handler**,
not of **the caller**. An `async def` handler that calls cascor synchronously blocks the loop
identically whether it was invoked by a Dash self-call, by a browser, by Prometheus scraping, or
by the deploy stack's health check at `Dockerfile:108`. Convert all 58 self-calls to direct
in-process calls today and X7 survives untouched, reachable by any external client.

**Corollary: if the proposed fix for X7 is "remove the self-calls," the fix is wrong.** That is
the failure mode I was warned I am most prone to, and it is a real one here, because the two
problems share a symptom (dashboard dies) and a document.

### 3.2 They are not independent either — two concrete couplings

**Coupling 1 — the self-calls are the trigger population, and it is measurably self-defeating.**
Of the distinct `_api_url(...)` target paths, **17 land on `async def` handlers with bare sync
cascor calls**. The timer bindings are the finding:

- **Fast lane, 1000 ms** (`FAST_UPDATE_INTERVAL_MS`, `canopy_constants.py:370`,
  `prevent_initial_call=False`): `dashboard_manager.py:3296-3316` binds
  `Input("fast-update-interval","n_intervals")` → `_update_unified_status_bar_handler` (`:6266`)
  → `GET /api/status` (`:6294`) → `main.py:1311 async def get_status()` → `main.py:1317` bare
  `backend.get_status()`. **A one-second timer drives a synchronous cascor call on the event loop
  with no user present.**
- **Slow lane, 5000 ms** (`canopy_constants.py:371`): `dashboard_manager.py:3340-3355` →
  `_update_system_panels_handler` (`:6530`) issues **three sequential blocking self-calls per
  tick** — `/api/status` (`:6543`), `/api/network/stats` (`:6565` → `:6676`), `/api/stream_health`
  (`:6566` → `:7819`).

That second one is the number that settles the argument: on the refused path, three calls × 3.0 s
is **~9 s of blocked loop per 5 s tick**. **The loop cannot keep up with its own poller.** The
system is not merely vulnerable to a slow cascor; while cascor is refusing, canopy generates more
blocking work than wall-clock time in which to do it, from timers alone, with nobody at the
keyboard. That is why X7 presents as a sustained outage rather than a transient hiccup.

(Tab-gated lanes — `disabled=True` until their tab is active, `dashboard_manager.py:1859-1869` —
add `/api/dataset`, `/api/v1/workers/{list,stats}` and `/api/decision_boundary` on top when a user
is actually looking.)

**Coupling 2 — the self-calls couple two independent pools, turning a stall into a deadlock.**
a2wsgi 1.10.10 runs the Dash WSGI app on `ThreadPoolExecutor(max_workers=10)`
(`a2wsgi/wsgi.py:152-160`; canopy passes no override at `main.py:493`, so **10**). The mechanism
is worse than "waiting for a response," and the detail matters — `a2wsgi/wsgi.py:215-219`:

```python
def send(self, message):
    future = asyncio.run_coroutine_threadsafe(self.send_queue.put(message), loop=self.loop)
    future.result()          # <-- no timeout
```

**That future is scheduled onto the very loop that is blocked** (`loop=self.loop`, captured at
`wsgi.py:186`). So a WSGI worker thread cannot even *emit a response chunk* while the loop is
stalled — it blocks indefinitely in `future.result()`, and unlike the self-call's `requests`
timeout (§1.2) **there is nothing to bound it**. With the 1 s and 5 s pollers both re-firing
during the stall, the 10-thread pool fills and the dashboard stops rendering entirely — not just
the one slow panel. `/dashboard` and `/api/*` deadlock against each other through a single shared
loop.

This corrects a weaker version of this claim I held earlier: the WSGI threads are not merely
parked on *inbound* self-call timeouts, they are parked on the *outbound* send path, which has no
timeout at all.

So: **the self-call pattern does not cause X7, but it sets X7's frequency and its blast radius.**
Fixing X7 without touching self-calls fully resolves X7. Fixing self-calls without touching X7
resolves nothing, but does make a future X7-class regression quieter and rarer.

### 3.3 The direction of the interaction, if you do Option C — and a trap

This is the highest-value thing in this document, so I will state it as a warning.

Option C §5.2 offers three async/sync bridges for calling an `async def` handler from a sync Dash
callback, and ranks them "in increasing complexity," presenting the middle one as the perf-optimal
choice:

> - `asyncio.run(handler(...))` — clean but creates a new event loop per call, expensive.
> - **A canopy-owned background event loop + `asyncio.run_coroutine_threadsafe`. Better perf**,
>   requires a small `loop_bridge.py` helper.
> - Migrate the Dash callback to async-aware.

**The recommended middle option makes X7 strictly worse.** If that "canopy-owned background
event loop" is the serving loop — which is what `schedule_broadcast` (`main.py:499-511`) already
does via `loop_holder["loop"]`, so it is the established in-repo idiom and the obvious thing an
implementer would reach for — then every Dash poller now runs its blocking coroutine **directly
on the serving loop**, with the HTTP boundary's `timeout=` (the only thing bounding each self-call
today, §1.2) **removed**. Eighteen interval-driven pollers gain unbounded loop-blocking access.

The bridge choice therefore determines the sign of Option C's effect on X7:

| bridge | where the blocking lands | effect on X7 |
|---|---|---|
| sync service fn called directly from the WSGI thread | WSGI thread | **improves** — removes 18 loop-blocking entry points |
| `asyncio.run(...)` — fresh loop on the WSGI thread | WSGI thread | improves |
| `run_coroutine_threadsafe` onto the **serving** loop | **serving loop, unbounded** | **strictly worse than today** |

This is why §2 recommends a *sync service layer* rather than *calling the async handlers*: it is
the only shape where the bridge question does not arise, and therefore the only shape where the
refactor cannot silently invert its own benefit.

---

### 3.4 X7 crosses the platform's own liveness threshold — an operational consequence not yet on the record

`/v1/health` is not merely *collateral* to a blocked loop — **it is itself on the blocking path**.
`main.py:1057 async def health_check()` reaches `main.py:1076`
`"training_active": backend.is_training_active()` → `service_backend.py:161` →
`cascor_service_adapter.py:1089-1091`, a bare synchronous `self._client.get_training_status()`
that **bypasses the circuit breaker** protecting the identical client method at adapter `:1970`
(§1.5). The liveness probe is one of the 37 unoffloaded handlers.

A 3.0 s refusal still fits inside `curl --max-time 5`. A 123 s hang does not, and the numbers are
not close:

| probe | config | time to unhealthy | vs. observed ~123 s block |
|---|---|---|---|
| `Dockerfile:107-108` | `--interval=30s --retries=3` | ~90 s | **exceeded** |
| `juniper-deploy/docker-compose.yml:58-62` | `interval=15s retries=5` | ~75 s | **exceeded** |

So X7 is not merely a UI stall — **it marks the canopy container unhealthy**, in both the image's
own and the deploy stack's configuration.

Two honest qualifications, because the consequence is easy to overstate:

- Under plain compose this does **not** auto-restart canopy: `restart: unless-stopped`
  (`docker-compose.yml:740`, `:822`) acts on process *exit*, not on health. The container goes
  unhealthy and recovers when the loop does.
- Under **any** orchestrator that restarts on a failed liveness probe (Swarm, k8s), it *would*
  restart — and a restart destroys every item in §1.7: live WebSocket connections,
  `training_state`, `_demo_snapshots`, and the hot-swapped `backend`. In that topology X7 would
  present as an unexplained crash-and-lose-training-state, not as a stall, which is a materially
  worse and much harder-to-diagnose signature.

This does not change the fix. It raises the priority, and it argues for the event-loop-lag metric
in Phase 1 item 5: today the only signal this class produces is a health-check flap, which reads
identically to a dozen unrelated causes.

---

## 4. Verdict on the deferred design of record

`juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md`

**Verdict: AMEND. Do not supersede, do not implement as written.**

Its destination is right and its §5.3 already contains the correct pattern. Four things are wrong
and one is dangerous.

### 4.1 §6.1's trigger condition is unobservable — I agree the stated mechanism is wrong

§6.1 reads:

> **Concurrent-user dashboard exhausts the Flask threadpool.** Symptom: `werkzeug` logs
> `[WARNING] WSGI request queue full` or panels stall waiting for callbacks.

That trigger cannot fire, for **two independent reasons**, both verified:

1. **Werkzeug is not in the serving path.** Dash's Flask app is mounted via `a2wsgi.WSGIMiddleware`
   (`src/main.py:57`, `:493`), which takes the Flask *WSGI object* and runs it on its own
   `ThreadPoolExecutor`. Werkzeug's server is never started. `grep -rn werkzeug src/ --include=*.py`
   over non-test code returns **nothing**. (`dashboard_manager.py:8000` does hold a
   `self.app.run_server(...)` — but that is the standalone/dev entry point, not the mounted
   production path.)
2. **The log line does not exist.** `grep -rn 'queue full'` across the installed `werkzeug`
   package returns **nothing**. The symptom §6.1 instructs the reader to watch for is not a real
   werkzeug message in any configuration.

So the trigger's stated detection criterion cannot fire — not "has not fired," *cannot*, and not
merely because the component is absent but because the signal was never real. Meanwhile the
condition it describes **in substance** (the WSGI pool exhausting) is exactly what X7 does.

**So the trigger has been met for months while remaining un-fired by its own definition.** That
is a design-of-record failure worth naming independently of X7: a deferral gated on a signal that
no component in the serving path can emit is an unconditional deferral wearing a condition's
clothes.

It also mis-attributes causation. §6.1 assumes exhaustion arrives via *concurrent users*. It
arrives via *a blocked event loop plus the dashboard's own pollers*, at a single user, at zero
external load.

### 4.2 §4.2's "effective concurrency is halved" is the wrong model

> every Option-B self-call occupies *two* worker slots simultaneously: the Dash callback thread
> blocking on `requests.get`, plus the FastAPI worker handling its own request. Effective
> concurrency is halved relative to Option C.

FastAPI `async def` handlers do not occupy a "worker slot" — they run on the event loop. So for
the async-handler majority the cost is not a 2× tax on a single pool; it is a **coupling between
two structurally independent pools** (a bounded 10-thread WSGI executor and a single event loop).
A tax degrades gracefully. A coupling fails catastrophically, which is what §3.2 describes and
what X7 demonstrates. The document understates the risk by describing it as a throughput cost,
and that understatement is plausibly *why* the deferral looked cheap.

### 4.3 §5.1 / §5.2's premise is stale

§5.1 says the handlers are "scattered across `src/api/`." **`src/api/` does not exist** (§1.4);
they are all in a 4,400-line `main.py`. And §1.8's import cycle means the illustrated
`from api.status import get_status` is not merely a wrong path — it is a shape that cannot
compile. The prerequisite service-layer extraction is unscoped, which is the main reason the
"3–4× Option B" estimate is low.

### 4.4 §5.2's preferred bridge is an X7 amplifier — the dangerous item

See §3.3. This is the amendment that most urgently needs to land, because the document is the
design of record and an implementer following it would reach for
`run_coroutine_threadsafe(coro, loop_holder["loop"])` by analogy with `main.py:499`, and ship a
regression that looks like a performance improvement.

### 4.5 What to keep

§5.3's "push the business logic down a layer (call it `core/<feature>.py`), keep the FastAPI layer
thin" is correct and should be promoted from an aside to the plan's spine. §5.7's `internal_call`
shim is correct and is the right migration vehicle. §6.6 (a process split makes Option C
impossible and Option B correct) is a real constraint worth preserving. §7's exclusions are right.

### 4.6 Amendment list

1. Rewrite §6.1: replace the unobservable werkzeug signal with a real one (a2wsgi executor
   saturation gauge, or event-loop-lag histogram — see §7 Phase 1), and record that the substance
   of the trigger was met by X7 on 2026-09-02.
2. Rewrite §4.2 as a coupling, not a halving.
3. **Strike the `run_coroutine_threadsafe`-onto-the-serving-loop bridge**; state the sign-inversion
   from §3.3 explicitly.
4. Correct §5.1/§5.2 for `src/api/` not existing; add the import cycle (§1.8) and the
   `main.py:3722` hot-swap trap as first-class prerequisites; re-baseline the cost estimate.
5. Promote §5.3 option 1 to the plan's spine; target a **sync** service layer.
6. Add a non-goal: **Option C is not a fix for X7** (§3.1).

---

## 5. Is `workers=1` the real architectural defect?

**No. And raising it is currently a no-op that would read as a fix.**

### 5.1 It is not a decision, and "fixing" it would be vacuous

`workers=1` appears nowhere. `src/main.py:4419` passes the **app object** to `uvicorn.run` with no
`workers=` kwarg. Per `uvicorn/main.py:606`, adding `workers=4` there **logs a warning and runs
one worker anyway**. An engineer mitigating X7 that way would ship a change, observe no crash,
and record the mitigation as applied — while nothing changed. That is the vacuous-pass class, and
it is a live trap on this specific line.

Making it real requires converting the entrypoint to an import string, which is where §5.2 bites.

### 5.2 What actually breaks at `workers > 1`

Every item in §1.7 is per-process, and the failures are **silent**:

- **WebSocket fan-out dies.** `websocket_manager` (`websocket_manager.py:1194`) holds
  `self.active_connections: Set[WebSocket]` (`:217`) in process memory. A browser's socket lands
  on worker A; the training event arrives on worker B; `broadcast()` iterates an empty set and
  returns successfully. No error, no metric, no log. The dashboard shows a connected WS badge and
  no data. Given the WS bridge is now load-bearing (`ws_dash_bridge.js` drains 7 channels; N8 made
  the metrics store WS-primary), this is a total real-time regression.
- **`schedule_broadcast` targets the wrong loop.** `main.py:499-511` dispatches via
  `loop_holder["loop"]` — per-process. Same silent failure, from the training side.
- **Training status becomes non-deterministic.** `training_state` (`main.py:123`) is per-process;
  `/api/train/status` answers differently depending on which worker the OS accept-balances to.
  The UI would flicker between states with no cause visible in any single worker's logs.
- **The backend singleton splits its brain.** `backend` (`main.py:480`) is hot-swapped under
  `global backend` on model select (`main.py:3703`, `:3722`). `POST /api/model/select` swaps it in
  **one** worker. The other N−1 keep serving the previous model, and report success.
- **In-memory snapshots fragment.** `_demo_snapshots` (`main.py:2203`) is a per-process deque.
- **N independent Dash servers.** `dashboard_manager` (`main.py:489`) is constructed per process.

None of these are hard to fix in principle (external WS broker, shared state store, a real backend
registry) — but that is an infrastructure workstream, not a defect fix.

### 5.3 It would mask the bug, not fix it

Even with all of that solved: a blocked loop in worker 1 still black-holes every request balanced
to worker 1. You would trade a **total, reproducible, loud** outage for an **intermittent 1-in-N**
stall. That is strictly worse for diagnosis — it converts a defect you can reproduce on demand
into a flake, and it does nothing whatsoever for the blocked request itself. The blocking call is
still blocking; you have only bought neighbours who are not blocked yet.

### 5.4 Verdict

`workers=1` is not the defect. **It is the condition that made the defect legible, and that
legibility is an asset.** The defect is sync I/O in `async def`. Raising workers is (i) currently
a no-op, (ii) gated on externalizing WS fan-out and the backend singleton, and (iii) must never be
described as an X7 mitigation. If capacity is ever the actual motivation, it is its own
workstream with its own justification.

---

## 6. Over-scoping — the proposals of mine that are too big

I am the author most likely to inflate this defect into a re-architecture, so here is the list of
things I could argue for and am **rejecting as the fix for X7**.

| Proposal | Verdict as the X7 fix | Why |
|---|---|---|
| **Full Option C** — migrate all 58 self-calls | **TOO BIG, and it does not fix X7** (§3.1) | Requires extracting a service layer from a 4,400-line `main.py`, breaking the `main → dashboard_manager` cycle (§1.8), a backend accessor to survive `main.py:3722`, and ~50 test-mock migrations. Weeks. Attaching it to X7 would hold a one-day fix hostage. |
| **The `src/services/` extraction** (my own §2 recommendation) | **TOO BIG for this defect** | It is the right end state. Its justification is testability and cycle-breaking, not X7. Schedule it on its own merits. |
| **Full WS migration (`JR-CAN-PERF-004`)** | **TOO BIG, and incomplete** | By its own §3.2 it cannot cover raw topology (`GAP-WS-25`), decision boundary, redis, cassandra, or snapshots. It shrinks the trigger population; the mechanism survives on every non-convertible poller. |
| **Raising `workers`** | **REJECT** | No-op today (§5.1); masks rather than fixes (§5.3). |
| **Moving anything into `juniper-service-core`** | **REJECT on evidence** | Independently reproduced: `juniper-cascor`, `juniper-data` and `juniper-recurrence` each have **0** `a2wsgi`/`WSGIMiddleware` mounts and **0** loopback `requests.*` calls in non-test code. A shared abstraction with exactly one consumer is not a shared abstraction. Fix belongs in canopy. |
| **Replacing Dash / client-side fetching** | **REJECT** | Out of scope per the deferred design §7; I concur. |
| **Giving `juniper-cascor-client` an async REST surface** | **TOO BIG now — but it is the real end state for egress** | `juniper_cascor_client` 0.7.0 ships **no** async REST client: `pyproject.toml:28-31` declares only `requests` and `websockets`. So this is *building a new surface* in another repo with its own release train, not flipping a switch. It is nonetheless the destination, and §8's `health.py:15-23` precedent — canopy deliberately moved *off* `to_thread` to `httpx` elsewhere to avoid exactly the executor-saturation risk my Phase 0 accepts — is the argument for scheduling it rather than filing it. |

**The fix is: close the `asyncio.to_thread` coverage hole, close the circuit-breaker coverage hole,
and add a guard so neither reopens.** Everything above is the end state the defect revealed.

---

## 7. Phasing

### Phase 0 — the fix (ships now; hours, not days)

1. **Close the offload hole — scope is now exact: 37 handlers** (§1.3). Add the
   `await asyncio.to_thread(...)` hop, using `/api/state` (`main.py:1236-1239`) as the reference
   implementation. Order by poller reachability: `/api/status` (1 Hz), `/api/network/stats` and
   `/api/stream_health` (5 s lane) first — those three alone are the ~9 s-per-5 s-tick pathology
   in §3.2. This is the existing house pattern applied to the sites the SEC-F20 sweep missed:
   additive, mechanical, revertible per site.
   *Cheaper variant worth pricing first*: for handlers that do nothing else async, **changing
   `async def` to `def`** hands them to Starlette's threadpool with a one-word diff. All 72
   handlers are currently `async def` and none use this (§1.3). It is not universally applicable
   — a handler that `await`s anything else cannot take it — but where it applies it is the
   smallest possible change.
2. **Close the breaker hole on the hot paths.** The breaker covers 5 of 45 cascor invocations,
   and §1.5 enumerates exactly which Dash-reachable routes are unguarded. Prioritise
   `/api/stream_health`, `/api/v1/workers/{list,stats}` (which bypass the adapter wrapper
   entirely via `backend._adapter._client`), and the four health routes (§3.4). With
   `failure_threshold=5` / `recovery_timeout=60.0` already configured, this is what collapses the
   ~123 s worst case.
3. **Bound the retry budget.** The arithmetic is now exact. `juniper_cascor_client` 0.7.0
   (`client.py:87-97`, `constants.py:28-38`) mounts an `HTTPAdapter` with
   `Retry(total=3, backoff_factor=0.5, status_forcelist=[429,502,503,504])` and a **scalar**
   `timeout=30` applied as both connect and read (`client.py:363`). Canopy overrides none of it
   (`cascor_service_adapter.py:507`).
   - **refused** → 4 attempts, backoff `0 + 1.0 + 2.0` = **3.0 s** (measured: 3.006 s)
   - **hung** → `4 × 30 s + 3.0 s` = **123.0 s**

   Both observed figures are fully explained. Set an explicit `timeout=` and a lower `total=` at
   the canopy construction site so the worst case sits inside the callers' budgets
   (`DASHBOARD_GET_TIMEOUT=5`, `DASHBOARD_POST_TIMEOUT=2` — `canopy_constants.py:421-432`). This
   is a one-line change in canopy that needs no upstream release, and it closes
   `JR-CAN-PERF-003` (`proposed`) as a by-product.
4. **File the non-idempotent-retry defect separately** (do not fix it here). Installed 0.7.0 sets
   `allowed_methods=['GET','POST','DELETE','PUT','PATCH']` — **every verb** — so a timed-out
   `POST /api/train/start` is retried up to 4×. `juniper-cascor-client`'s repo has already drifted
   ahead and narrows this to `["HEAD","GET"]` (`constants.py:77`), so the fix exists upstream and
   is unreleased. This is a latent duplicate-training-command hazard that X7's investigation
   surfaced; it is a *different* defect and belongs in its own ticket.

**Reversible**: yes, entirely. Each item is additive and independently revertible.

### Phase 1 — the guard (ships with, or immediately after, Phase 0)

4. **A regression test that fails on sync cascor I/O inside `async def`.** This is the item that
   makes Phase 0 durable rather than another sweep to be redone in four months — and §1.3 shows
   that is not hypothetical: SEC-F20 fixed this mechanism once, shipped a comment instead of a
   test, and X7 is the recurrence. Write it `**kwargs`-aware (§1.2) or it will ship false
   confidence. **If only one item from this entire document ships, it should be this one** — it is
   the only item that changes the defect's recurrence rate rather than its current instance.
5. **An event-loop-lag metric** (and/or an a2wsgi executor saturation gauge). Canopy already has
   the observability tier for this. It is also the honest replacement for the deferred design's
   unobservable §6.1 trigger (§4.6 item 1).

**Reversible**: yes — test and metric only, no behavior change.

### Phase 2 — amend the design of record (scheduled, no code)

6. Apply the six amendments in §4.6 to
   `JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md`. **Item 3 (strike the
   `run_coroutine_threadsafe` bridge) should not wait for the rest** — it is the one line of that
   document that could cause a regression if followed today.

### Phase 3 — the end state (scheduled, independent justification)

7. `get_backend()` accessor — small, valuable on its own, unblocks everything else.
8. `src/services/` extraction, cycle break, `internal_call` dispatch, incremental self-call
   migration. Justified by testability and the §1.8 cycle, **not** by X7.
9. WS migration per `JR-CAN-PERF-004`, for the convertible subset only.
10. **An async REST surface in `juniper-cascor-client`** — the true fix for the egress axis, and
    the only thing that retires §8's objection rather than mitigating it. Cross-repo, own release
    train. Sequence it after the upstream `allowed_methods` narrowing (Phase 0 item 4) ships, so
    both land in one client bump.

**Reversible**: Phase 3 is the only genuinely hard-to-reverse work, which is exactly why it must
not ride along with a defect fix.

---

## 8. The strongest objection to my own recommendation

**`asyncio.to_thread` moves the blocking onto a shared, bounded, process-wide executor — so my fix
can convert "the loop is blocked" into "the default executor is saturated," which is quieter and
harder to see than what it replaces.**

**This objection is not hypothetical, and canopy has already ruled against me once.**
`src/health.py:15-23` carries a comment explaining that the dependency probe was moved *off*
`asyncio.to_thread` **precisely to avoid thread-pool exhaustion**, and `health.py:60` now uses
`httpx` natively instead. So the repository contains a documented, deliberate decision that the
remedy I am recommending is the wrong one — for a path with the same shape as the one I want to
apply it to. Any reviewer of this design should weigh that precedent heavily, and I would be
misrepresenting the evidence if I buried it.

Why I still recommend `to_thread` for the cascor path despite that precedent: **the alternative
health.py chose does not exist here.** `juniper_cascor_client` 0.7.0 ships **no async REST
surface** — `pyproject.toml:28-31` declares only `requests>=2.28.0` and `websockets>=11.0`; there
is no `httpx.AsyncClient` and no `aiohttp` anywhere in the package. Its only async surface is the
WebSocket client (`ws_client.py`), which canopy already uses. health.py could switch to `httpx`
because it speaks raw HTTP to arbitrary dependencies; the cascor path cannot, because it speaks
through a sync-only client library. **So the honest framing is: `to_thread` is the best remedy
available inside canopy, and the precedent at `health.py:15-23` is the argument for why the
cross-repo async-client work in §6 is the real end state for egress rather than a nice-to-have.**

CPython's default `ThreadPoolExecutor` for `to_thread` is `min(32, cpu_count + 4)` threads, and
canopy never calls `set_default_executor` — verified: there is no `set_default_executor` or
`ThreadPoolExecutor` construction anywhere in non-test `src/`. On this 16-core host that is
**20 threads**, shared by **every** `to_thread` site in the process — all 30 in `main.py` (§1.3),
including snapshot filesystem reads and SSRF DNS resolution that have nothing to do with cascor.

**The margin is thin: 18 interval-driven pollers (§3.2) against 20 shared threads.** If cascor is
refusing connections and those pollers fan into `to_thread` at 1–2 Hz with a multi-second retry
budget each, they can occupy nearly the entire executor on their own, before a single user action
or snapshot read competes for it. Subsequent `to_thread` calls then
**queue**, and the coroutine awaiting them is suspended — so the loop keeps spinning, health checks
keep passing, and unrelated endpoints degrade with no blocked-loop signature to find. That is the
same "a broken thing masks the next one" class this fix is supposed to end, relocated one layer
down.

**Three reasons I still recommend it, and the mitigation that makes the objection tractable:**

1. It is strictly better than the status quo. Today the loop itself stops, which kills WS
   heartbeats, health checks, and every pure-async route simultaneously. Executor saturation
   degrades a subset and keeps the loop alive.
2. **Phase 0 item 2 is the actual answer to this objection**, which is why I ordered it inside the
   same phase rather than deferring it. The circuit breaker bounds executor *occupancy*, not just
   latency: once open, cascor calls return immediately without consuming a thread at all. With
   `failure_threshold=5` and a dead cascor, the pollers stop entering the executor within seconds.
   The offload without the breaker is the version this objection defeats; the two together are not.
3. The residual risk is directly addressable by giving the cascor egress path **its own bounded
   executor** rather than the default one, so cascor failures cannot consume the budget that
   snapshot reads and DNS resolution depend on. I would take that as a Phase 1 item if the
   event-loop-lag metric from item 5 shows executor queueing under a fault-injected dead cascor.

**Where this objection would actually win**: if the breaker cannot be extended to the
poller-reachable invocations cheaply — if those 40 unprotected `self._client.*` sites need
per-call semantics the breaker's uniform `call()` wrapper cannot express — then Phase 0 ships the
offload without its bound, and I would be trading a loud failure for a quiet one. **That is the
single assumption in this design most worth testing before writing code**, and §1.5 now makes it
cheap to test: the Dash-reachable unguarded set is enumerated (`/api/stream_health`,
`/api/decision_boundary`, `/api/v1/workers/{list,stats}`, the five `/api/train/*` verbs,
`/api/train/restart`, the three dataset mutators, and the four health routes). That is a
morning's reading, not a survey.

**A second, narrower way it wins**: even a *fully* guarded path pays `failure_threshold=5` ×
3.0 s ≈ 15 s of executor occupancy before the breaker opens (§1.5). With 20 shared threads and 18
pollers, that opening window is exactly when saturation would occur. Lowering
`failure_threshold` on the poller-reachable paths — or giving the cascor egress its own bounded
executor — is the cheap insurance, and I would take it in Phase 1 rather than argue about it.

---

## 9. Summary

| Question | Answer |
|---|---|
| Self-call architecture | Move to a **sync service layer** (b) — scheduled, not now. Not HTTP-to-self; not "call the async handler." |
| Same defect as X7? | **No — related.** Self-calls are the trigger population and the outage amplifier; they are not the mechanism. Removing them does not fix X7. |
| Deferred design | **Amend, don't supersede.** §6.1's mechanism is wrong *and unobservable*; §4.2 mis-models it; §5.1's `src/api/` doesn't exist; **§5.2's preferred bridge would make X7 worse** — strike that first. |
| `workers=1` | Not the defect. Not even a written decision. Raising it is a **no-op today** (`uvicorn/main.py:606`) and would mask, not fix. |
| Too big | Full Option C; the service extraction; the WS migration; async client migration; anything in `juniper-service-core`; raising workers. |
| The fix | Offload the **37** unoffloaded cascor-reaching handlers (`asyncio.to_thread`, or `def` where it applies) + extend the `CircuitBreaker` (5 of 45) to the poller-reachable and health routes + pin `timeout`/`total` at the client construction site + a guard test. Every mechanism already exists in-repo and is already the house style. |
| Load-bearing numbers | 72 route handlers, **all `async def`**; 51 reach cascor; **14 offloaded, 37 not**. Retry math exact: refused = **3.0 s**, hung = **123.0 s**. a2wsgi pool = **10**, `future.result()` unbounded and scheduled *onto the blocked loop*. Shared `to_thread` executor = **20** threads vs **18** pollers. |
