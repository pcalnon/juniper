# Juniper-Canopy — X7: Event-Loop Blocking on an Unreachable Backend — Remediation Design

- **Project**: Juniper — juniper-canopy
- **Author**: Paul Calnon
- **Date**: 2026-09-03
- **Status**: **Revision 3** — root cause settled; first plan refuted (§4); §5's mechanical core validated by measurement; its safety layer refuted twice and §§5-10 **rewritten** (§10). Pending re-review.
- **Defect**: X7, first labelled in [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md) §6.1
- **Evidence**: `reports/2026-09-02_canopy-selection-deadlock/` (X7 lanes: `x7_laneA{1,2,3}.md`, `x7_fix_F{1,2,3,4}.md`, `x7_laneB{1,2}.md`)

---

## 1. Scope

Remove X7: juniper-canopy ceases to answer HTTP — `/v1/health` included — whenever juniper-cascor
is unreachable. This document specifies the remediation. It does **not** cover the demo-mode
honesty chain, which is a separate defect discovered during this arc and sequenced as PR 2 (§7).

**This is the third design.** The first was refuted in full (§4). The second had its mechanical core
validated by measurement and its safety layer refuted on ten counts, then nine more; §§5-10 are a
rewrite rather than a third patch layer. §4 is retained because each of the first plan's four steps
is the change a competent engineer reaches for, and three are actively harmful — without that
record, the next reader re-derives all four.

---

## 2. The defect, measured

**Root cause**: synchronous, retrying `requests` I/O executed inside `async def` route handlers, on
a **single-worker** uvicorn. That blocks the event loop, so *every* route stalls — including
pure-async ones. Confirmed by four independent lanes; the reconciler's own hypothesis
(threadpool exhaustion) was **excluded** by a decisive counter-example: four concurrent *threadpool*
blockers ran in parallel (6.0 s each, not 24 s) and left the loop at 2.4 ms.

| condition | `GET /v1/health` | source |
| --- | --- | --- |
| cascor healthy | **5.7 ms** | reconciler, end-to-end |
| cascor **stopped** (ECONNREFUSED) | **3.0 s** | Lane A1 + reconciler |
| cascor **hung** (`SIGSTOP`) | **123.12 s** | reconciler, end-to-end |
| recovery, no canopy restart | **5.1 ms** | reconciler |

The 123 s is `timeout × (retries+1) + Σbackoff` = `30×4 + (0+1+2)`. It was derived by Lane A2,
measured at the client (123.13 s) and confirmed end-to-end (123.12 s) — three routes to the same
number.

**Direct evidence of loop blocking**: one `/v1/health` (3.008 s) stalled the pure-async
`/v1/health/live` for **2.603 s** — its exact remainder; 8 concurrent → 24.05 s serialised. The
loop thread's kernel `wchan` read `hrtimer_nanosleep` throughout the outage and flipped to
`ep_poll` the instant it ended.

### 2.1 Why it becomes a *total* outage rather than latency

Three amplifiers, each verified:

1. **The pollers are self-defeating.** The 5 s lane issues **three sequential** blocking self-calls
   per tick (`dashboard_manager.py:6543/6565/6566`). At 3.0 s each that is ~9 s of blocked loop per
   5 s tick. Canopy generates more blocking work than wall-clock time, from timers, unattended.
2. **Health probes sustain it.** Compose polls `/v1/health` every 15 s
   (`docker-compose.yml`, `x-healthcheck-canopy`), the image every 30 s (`Dockerfile:107-108`).
   Each probe launches a call that can block for 123 s. **The probe that exists to detect the
   outage perpetuates it.**
3. **a2wsgi turns a stall into a deadlock.** `a2wsgi/wsgi.py:215-219` calls `future.result()` with
   no timeout, scheduled onto the blocked loop, so the 10 WSGI worker threads cannot emit a
   response chunk and `/dashboard/*` dies too.

### 2.2 Why it survived seven prior sightings

- **The guardrail is green on the bug.** `.pre-commit-config.yaml:123-131` wires a CI-blocking hook
  named *"Async-route audit (BUG-JD-10 class)"* running `ruff --select ASYNC`. Verified:
  `ruff check --isolated --select ASYNC src/` → **"All checks passed!"** against 35-40 live sites.
  Ruff's `ASYNC2xx` rules match a hardcoded callee list; `backend.get_status()` is an opaque method
  call. **No ruff configuration can see this defect.**
- **The standing deferral was gated on an impossible signal.** The deferred refactor keyed on a
  werkzeug "queue full" log line; werkzeug is not in the serving path and that string does not
  exist in the installed package.
- **SEC-F20 fixed this mechanism once and shipped a comment with no test.** X7 is its recurrence.
- **The system is configured to be immune, in dead config.** `conf/app_config.yaml:400-401`
  declares `workers: 4`; nothing reads it, and `main.py:4419` passes an app *object*, which makes
  `workers>1` impossible without changing the launch form.

---

## 3. Constraints any fix must satisfy

Derived from measurement, not preference. A design that misses any of these is refuted on arrival.

| id | constraint | why |
| --- | --- | --- |
| **C1** | No request handler may perform an unbounded blocking call on the request path | the defect itself |
| **C2** | Upstream call rate must be independent of browser-tab count and poller count | ρ scales with tabs otherwise (§4.2) |
| **C3** | Handler latency must fit the dashboard's own budget: **1.0 s** fast lane, **2.0 s** normal (`canopy_constants.py:373-374`) | otherwise every panel renders an error div even when "fixed" |
| **C4** | Concurrent outbound cascor calls must be **bounded**, and the bound must be < the 20-slot executor (`min(32, cpu+4)`, verified) | unbounded offload measured **3 → 42** upstream requests and peaked 20/20 |
| **C5** | The shared `requests.Session` must not be used concurrently from multiple threads | documented not thread-safe; the loop currently serialises it at concurrency 1 |
| **C6** | An unknown/stale backend status must never be presented as a *fresh negative* fact | the adapter returns `{"is_training": False, "error": …}` rather than raising (§5.1); a cache that stamps that `FRESH` fabricates "not training" |
| **C7** | Health must **surface staleness**, and must **stay 200/degraded** on an upstream outage | ratified: `values.yaml:222-226` — "upstream … outages remain 200/degraded so the dashboard stays useful with cached state" — and guarded by `test_canopy_never_returns_503_on_upstream_down` (`src/tests/unit/test_health.py:300-315`) |
| **C8** | Retries must not be applied to non-idempotent verbs | `POST /v1/training/start` measured reaching the server **4×** |
| **C9** | Any cached value served to a caller must carry `stale` + age when it is not fresh | canopy's own 2026-07-10 remedy (`main.py:1224-1237`); the relay-fed global went **~8 h stale** silently and the fix was explicit `stale: true` marking |
| **C10** | Work abandoned by its caller must not remain queued for upstream | measured: 30 POSTs abandoned at 1.25 s still produced **all 30** upstream calls over 45 s behind `Semaphore(4)` |

---

## 4. The first plan, and why it is refuted

Recorded because each step is the obvious move, and three are harmful.

### 4.1 "Bound the client's timeout and retries" — a no-op as written, and a dead end as intended

`cascor_service_adapter.py:507` constructs `JuniperCascorClient(base_url, api_key)`. The proposal
was to pass explicit values — but **`timeout=30, retries=3` ARE the defaults** (verified). The
first plan proposed applying the settings under which the defect was measured.

Choosing *different* values also fails. Lane B1 computed utilisation and confirmed each row
empirically (λ ≈ 1.47/s per tab; c = 20 offloaded):

| setting | per-call cost | ρ, 1 tab | 2 tabs | 4 tabs |
| --- | --- | --- | --- | --- |
| today `t=30, r=3` | 123.1 s | 9.03 | 17.6 | 34.7 |
| `t=10, r=1` | 20.0 s | **1.47** | 2.87 | 5.67 |
| `t=5, r=1` | 10.0 s | 0.734 | **1.43** | 2.84 |
| `t=2, r=0` | 2.0 s | 0.147 | 0.287 | 0.567 |

Only `t≤5, r≤1` reaches ρ<1, and `t=5/r=1` **saturates at two browser tabs**. Every ρ<1 setting
still costs ≥1.0 s, which **exceeds C3** — so even the "working" settings leave every panel
erroring. **No `(timeout, retries)` pair satisfies C2 and C3 together.**

### 4.2 "Offload the five hot handlers with `asyncio.to_thread`" — not compositional, and unsafe

- **Not a partial fix.** 24 handlers / 35 sites reach blocking I/O; five is not a subset that
  helps. Measured: `/live` sat at 25 ms until a single `POST /api/train/stop` landed, then went to
  hard timeout and **never recovered**. One request to one un-offloaded handler reinstates the full
  outage — and stopping training is precisely what an operator does during an X7 event.
- **Deletes the only back-pressure.** Measured at canopy's real cadence: inline → 3 upstream
  requests; `to_thread` → **42** (14×), executor peak **20/20**, mean occupancy 16.2. `to_thread`
  is **uncancellable**, so a client abandoning at 1-2 s does not free the slot. Violates C4.
- **Introduces a thread-safety bug.** Violates C5: the blocked loop is currently serialising a
  non-thread-safe `Session` at concurrency 1; offloading puts 20 threads on it with
  `pool_maxsize=10`. The defect is accidentally protecting itself.

### 4.3 "Serve health from a TTL cache" — a no-op if lazy, and unsafe if naive

Probe budget is **5 s** at 15 s / 30 s intervals, so any TTL short enough to keep `training_active`
honest is shorter than the probe interval: **every** healthcheck pays the full refresh. And
`is_training_in_progress()` returns `False` on error, so a naive cache serves
`training_active: false` **during a live run** — violating C6.

The repo already contains this exact anti-pattern: the adapter's network cache
(`cascor_service_adapter.py:1012-1031`) stores `None` on failure while its guard requires
`is not None`, so it **re-queries on every call precisely when cascor is down** — zero protection
in the only failure mode that matters.

### 4.4 "A latency-percentile guard test" — vacuous

With the executor saturated, `/v1/health/live` returned **0 samples in 40 s**; in today's blocked
loop, 0 samples in 40 s. A p95 assertion over an empty sample reads 0/0 and **passes**. The
threshold was never the problem — it measures the wrong thing.

---

## 5. The design

> **Revision 3 (2026-09-03).** §§5-10 are rewritten, not patched. Revision 2 accumulated nine
> blocking findings plus internal contradictions (§6 forbidding the stub its own tests required;
> §8.1 filed under "what this does not fix" while claimed in PR 1; a constraint added with no
> design satisfying it). A third patch layer would have compounded that. §§1-4 are unchanged and
> remain the stable part: the defect, the measurements, the constraints, and the record of the
> refuted first plan.

> **D1 — cascor leaves the read path.** A single background task owns all periodic cascor polling.
> Read handlers and health endpoints serve from an in-memory cache and never make an outbound
> cascor call. Mutating routes keep a bounded, deadline-checked outbound call.

D1's mechanical core is **validated by measurement**, not argument: with a hung upstream the
refresher keeps the loop free (80/80 completions, mean 3.0 ms, max 4.7 ms), **cannot overlap**
(`starts=1, returns=0, peak_inflight=1`), leaks no executor slot, and exits on SIGTERM in 0.161 s.
Everything below is the layer that failed twice and has been rebuilt.

### 5.1 The classifier — the load-bearing component

Revision 2's classifier keyed on the presence of an `error` field. Measured against the real
adapter, that is wrong in five directions, so classification is now **positive**: a tick is OK only
if the payload proves it is.

| observed return | class | why |
| --- | --- | --- |
| `None` | `UNREACHABLE` | `_unwrap_response` can return `None`; `"error" in None` raises `TypeError` and would have killed the refresher task |
| not a `dict` (e.g. `[]`) | `UNREACHABLE` | a list is not a status |
| `dict` with **truthy** `error` | `UNREACHABLE` | connect/transport failure |
| `dict`, `error` present but **falsy** (`None`, `""`) | fall through to positive check | a healthy backend must not be classified failed |
| `dict`, no `error`, **no expected status field** (`{}`, `{"state": "IDLE"}` with nothing else) | `UNREACHABLE` | a half-dead cascor returning a shaped-but-empty 200 must not pin the cache `FRESH` — this is precisely the 2026-07-10 failure |
| `dict`, no truthy `error`, **carries the expected field(s)** | `OK` | the only success path |
| `dict` with `error == "circuit open"` from a **shared** breaker | `INDETERMINATE` | see §5.2 — may reflect a *different* method's failures |

**Positive validation is the point.** Absence of an error is not evidence of health; presence of a
recognisable status is.

### 5.2 The refresher

A single `asyncio` task, started in `lifespan` (`main.py:216`) beside the existing `ws-keepalive`
idiom (`:369`) and cancelled in the shutdown block (`:387-392`). Each tick calls the adapter via
`await asyncio.to_thread(...)`, classifies per §5.1, and sleeps. Sequential by construction, so
single-flight, executor bounding and — for *this* caller — session exclusivity are structural
rather than disciplinary.

**It uses a dedicated circuit breaker.** `_cb` is one shared instance across five adapter call
sites (`cascor_service_adapter.py:1970, 1980, 2099, 2117`). Five failing `get_network_data()` calls
— a route inside PR 1's scope — would otherwise trip it for `get_training_status()`, so the cache
would read `circuit open` **against a healthy upstream** and freeze for 60 s. With its own breaker,
circuit-open on the refresher's path is genuine evidence about cascor and is classed `UNREACHABLE`;
`INDETERMINATE` remains only for reads that still traverse the shared breaker.

**It uses `retries=0` and a short timeout (proposed 5 s).** A poller does not need retries — it
retries by definition on the next tick, and urllib3's backoff is pure sleep on a blocked thread.
This also settles the timeout left unspecified in revision 2.

### 5.3 Read paths, and preserving the one indicator that works

Read handlers (`/api/status`, `/api/network/stats`, the health endpoints) serve from the cache. The
cache exposes **two** views, and the distinction is load-bearing:

- **`for_ui()` → the last observed payload, error field intact.** `dashboard_manager.py:6436-6438`
  renders "Unreachable" iff the payload carries `error`, per **PR #340** ("handle the circuit-open
  200 explicitly instead of as Stopped"). That is currently the **only working outage indicator in
  the product**. Revision 2's "a failed refresh leaves `value` untouched" would have starved it and
  made the branch dead code — creating a second dead indicator alongside the `"WS: Demo"` badge this
  arc already found.
- **`for_status()` → the last **OK** value, plus `stale: true` and `age_seconds` when the latest
  class is not `OK`.** This is the non-fabricating read (C6, C9).

Withholding the error was the error. The error is **routed**, not suppressed.

### 5.4 Mutating paths — bounded and deadline-checked

`POST /api/train/*`, snapshot mutations, `patch_weights`, `add/remove_hidden_unit` cannot be served
from cache. They keep an outbound call, offloaded, behind an `asyncio.Semaphore` (proposed **4**),
with each job carrying a **deadline**.

The semaphore alone is insufficient (C10): measured, 30 POSTs abandoned by their caller at 1.25 s
still produced **all 30** upstream calls over 45 s. `asyncio.to_thread` is uncancellable, so the
achievable remedy is **admission control, not cancellation** — the worker checks its deadline
*before* issuing the request and skips if the caller's budget (`API_TIMEOUT_SECONDS = 2`) has
already elapsed. In-flight work still completes; queued work for an absent caller does not start.

### 5.5 The client boundary

Because §8's paths are folded into PR 1, the refresher is **no longer the only caller** — revision
2's "one caller, so the shared `Session` is never used concurrently" is false by construction and is
withdrawn. C5 is met explicitly instead: a `threading.local()` session at the client boundary, so
each worker thread owns its own connection pool.

Retry verbs are bounded here as a **bridge** until §7's PR 4 lands: `JuniperCascorClient.__init__`
exposes only `base_url, timeout, retries, api_key` — not `allowed_methods` — and its
`RETRY_ALLOWED_METHODS` is `['GET','POST','DELETE','PUT','PATCH']`, so a timed-out
`POST /v1/training/start` reaches the server **4×** (measured). Canopy injects a correctly
configured client through the existing seam `CascorServiceAdapter(client=...)`
(`cascor_service_adapter.py:494`). Note this bounds *method* retries only: **connect-level retries
are unaffected** — measured 3.0 s / 4 attempts in both configurations.

### 5.6 Health contract

Unchanged status codes. `values.yaml:222-226` is **binding, not supporting**: *"upstream …
outages remain 200/degraded so the dashboard stays useful with cached state"*, guarded by
`test_canopy_never_returns_503_on_upstream_down` (`src/tests/unit/test_health.py:300-315`).
Revision 2's 503 is withdrawn and stays withdrawn.

| endpoint | change |
| --- | --- |
| `/v1/health/live` | none |
| `/v1/health/ready` | **none.** Revision 2 proposed routing it through the cache; that was wrong — `probe_dependency` (`src/health.py:60-90`) is *already* native-async httpx, does not block the loop, and is the only live signal `make health` reads. Downgrading it to cached would remove a working signal to fix a problem it does not have. |
| `/v1/health`, `/health`, `/api/health` | stop calling `backend.is_training_active()` inline; serve `training_active` from `for_status()`, and add `cascor_reachable`, `cascor_status_age_seconds`, `stale` |

Revision 2 also asserted "503 remains reserved for `ws_manager` unbound". `readiness_probe`
(`main.py:1093-1141`) does not implement that. It is an aspiration in `values.yaml`, not behaviour,
and is **not** claimed here.

### 5.7 Staleness must reach a consumer that exists

Revision 2 claimed probes would "observe staleness continuously". **No probe reads the body** —
Dockerfile `curl --fail --silent`; Compose `urlopen(...)` with the return value discarded
(`docker-compose.yml:732, 814, 869`); k8s `httpGet`; and `make health` parses `/v1/health/ready`,
extracting fields the design puts on `/v1/health`. The promise was unfunded in every channel.

Two channels that **do** exist:

1. **Prometheus.** canopy already mounts `PrometheusMiddleware` (`main.py:458`) and depends on
   `juniper-observability`. Export `juniper_canopy_backend_status_age_seconds` and
   `juniper_canopy_backend_reachable` via `register_or_reuse` (the ecosystem's mandated idiom), plus
   an alert on sustained age. This is the operator-facing channel.
2. **The PR #340 status bar** (§5.3), which is the user-facing channel and already works — provided
   §5.3's `for_ui()` keeps feeding it.

**If neither is implemented, §5.9's claim is void and the design reproduces 2026-07-10.** That is
the acceptance condition, not a nicety.

### 5.8 Interlocks: narrow rule, fixed at source

Fail-closed stays withdrawn (it protects nothing — cascor's FSM already rejects the same operations
at `juniper-cascor/src/api/routes/snapshots.py:279, 330, 379, 435` — and bricks Restart, Start and
model-swap, the actions taken during an outage).

The retained rule is only C6: **do not present unknown as a fresh negative.**

Revision 2 could not satisfy this at its own gate, because `is_training_in_progress()`
(`cascor_service_adapter.py:1089-1100`) bypasses both `_unwrap_response` and the breaker and returns
a **bare `False`** — there is no payload for §5.1 to classify. **So it is fixed at source**: that
method routes through the same breakered, classified path as its sibling
`get_training_status()` (`:1968-1976`) and returns a tri-state, not a bool. Without this, the
classifier cannot see the very call the health endpoints make.

### 5.9 Why this differs from 2026-07-10

Canopy previously served status from a relay-fed global; on **2026-07-10 it went ~8 h silently
stale** when the WS relay died, and the remedy (still in code at `main.py:1224-1237`) inverted to
**live-first**, keeping the cached value only as a fallback "explicitly marked `stale: true` with an
age".

X7 forces the opposite posture — live-first is what blocks the loop. So this design re-introduces
the shape that failed, and is defensible only by carrying the property whose absence caused that
failure:

| 2026-07-10 | this design |
| --- | --- |
| the relay died silently | §5.1 classifies positively, so a dead or half-dead upstream is recorded rather than smoothed |
| the stale value looked fresh | `stale` + `age_seconds` on every non-OK read (§5.3), reusing the idiom `main.py:1224-1237` established |
| nothing alerted | §5.7's gauge + alert — **the acceptance condition** |
| 8 h to notice | age is exported continuously and rendered in the status bar |

Revision 2 would have failed this test outright: its failure detection was unreachable code, so its
cache would have read `FRESH` forever against a dead cascor — reproducing 2026-07-10 with better
latency. That is why the classifier, not the cache, is the load-bearing component.

---

## 6. Test plan

Designed against the four vacuous checks this arc has now measured — the ruff hook, the latency
percentile, the completion count, and the pair that cancelled each other.

**The T1/T7 stub is BOUNDED** (harness constraint: `asyncio.to_thread` exposes no shutdown seam, and
a hung thread blocked `asyncio.run` finalisation past 40 s under pytest). **The assertion is
LATENCY, not completion** — revision 2 required a driver but asserted completion, and measured
20/20 completions on the defect while max control latency was **5.813 s**. The signal was present;
the assertion discarded it.

| id | test | today | after |
| --- | --- | --- | --- |
| **X7-T1** | hold **≥3 concurrent requests** to a cascor-touching route against a **2.0 s bounded** stub; assert **max latency of `/v1/health/live` < 500 ms** | **fails** (5.813 s measured) | passes |
| **X7-T2** | vacuity guards for T1: control sample non-empty, **and** each driver's latency ≥ the stub bound (proving it actually blocked) | — | both must hold or T1 is void |
| **X7-T3** | classifier table (§5.1) row-by-row, including `None`, `[]`, `{}`, `{"data": {}}`, `error: None` | fails | passes |
| **X7-T4** | non-OK read carries `stale` + `age_seconds` and does not report a bare `is_training: false` as current | fails | passes |
| **X7-T5** | `/v1/health/ready` **stays 200** on a cascor outage — asserted alongside the existing `test_canopy_never_returns_503_on_upstream_down`, which must keep passing | passes | passes |
| **X7-T6** | `for_ui()` still surfaces the `error` field, so `dashboard_manager.py:6436-6438` renders "Unreachable" (PR #340 regression guard) | passes | **must not regress** |
| **X7-T7** | outbound concurrency never exceeds the semaphore bound | fails (peak 20/20) | passes |
| **X7-T8** | deadline admission control: jobs whose caller budget elapsed are skipped, not issued | fails (30/30 issued) | passes |
| **X7-T9** | the refresher's dedicated breaker is not tripped by `get_network_data()` failures | fails | passes |
| **X7-T10** | staleness reaches a consumer: the gauge is registered and its value tracks cache age | fails | passes |

**Placement**: the coverage gate reads only `src/tests/unit/` and `src/tests/regression/` with
`-m "not slow"`, so these live there and are not `slow`. The new cache module is a per-file ≥90 %
risk and must be table-driven — X7-T3 largely provides that.

---

## 7. Phasing

| PR | repo | contents |
| --- | --- | --- |
| **1** | juniper-canopy | §5.1-§5.9 **plus the four §8 paths** + X7-T1…T10 |
| **2** | juniper-canopy | demo-mode honesty |
| **3** | juniper-deploy | probe/alert wiring + image-tag bump, after 1 and 2 |
| **4** | juniper-cascor-client | **version bump → Release → floor pin** |

**PR 4 detail** (revision 2 amputated the version bump): `main` already carries `['HEAD','GET']`
since `ff3df6c` (2026-08-28), but `pyproject.toml` still reads **0.7.0** and the latest tag is
**v0.7.0** — a Release now would republish 0.7.0 into an immutable index. The work is **bump to
0.7.1 → cut a GitHub Release → pin canopy's floor to `>=0.7.1`**, which fits canopy's existing
`<0.8.0` cap (`pyproject.toml:162`). §5.5's injected client is the bridge until then.

**Sequencing rule**: do not tighten liveness before demo mode is honest (PR 3 after PR 2). PR 1
before PR 2 is defensible — the demo fallback fires only in `lifespan`, so a mid-flight outage
yields the hang and never the fallback; they are mutually exclusive by timing.

**PR 1 is large** — §8's paths bring the blast radius to roughly **76 of 333** canopy test files. It
is kept whole rather than split because a partial fix that looks complete is precisely how SEC-F20
recurred as X7. If it must be split, the split is by *path* with the invariant tests landing first,
never by "core now, remaining paths later".

---

## 8. Paths included in PR 1 that are not the polled read path

These are **in scope**, not deferred. Each reinstates the full outage on its own.

| path | anchor | why it blocks |
| --- | --- | --- |
| **metrics relay** | `cascor_service_adapter.py:755-763` | on `cascade_add` the relay coroutine calls `extract_network_topology()` synchronously inside `async`. Measured **123 s blocked per 183 s with no user present** — the most serious residue, because it recurs during ordinary training |
| **WS connect** | `main.py:705` | `get_status()` on the accept path, unbounded per browser tab |
| **`_swap_backend`** | `main.py:3718` | `initialize()` inline — measured **6 × 123 s from one click**. Its gate at `:3710` additionally fails open |
| **lifespan discovery** | `main.py:294`, `:322` | runs before the refresher exists |

### 8.1 What this genuinely does not fix

- **`JuniperDataClient` is unbounded** (`demo_mode.py:918`, `:1829`) — same 123 s exposure via
  `/api/dataset/generate` and `/api/dataset/import-file`.
- **~29 handlers remain structurally sync-in-async** outside the polled and mutating sets.
- **The enforcement gap**: ruff cannot see this class (§2.2) and a naive AST rule false-positives on
  the repo's own correct idiom (13 bare-attribute offloads, 8 named closures). This is the mechanism
  by which SEC-F20 became X7, and it remains open.
- **a2wsgi's unbounded `future.result()`** — an amplifier, not the cause.
- **`/v1/health/ready` probes its two dependencies sequentially** (10 s worst case), exceeding
  Helm's `timeoutSeconds: 5` independently of X7.

---

## 9. Open questions

- **OQ-X1** — `REFRESH_INTERVAL` (proposed 1.0 s) and the `STALE`/`UNKNOWN` age thresholds, which
  should be derived from the 15 s/30 s probe intervals rather than chosen.
- **OQ-X2** — should the refresher back off when cascor is unreachable? Fixed 1 Hz costs one
  executor slot continuously; backoff reduces load but delays recovery detection.
- **OQ-X3** — semaphore bound (proposed 4) and deadline source: `API_TIMEOUT_SECONDS` or per-route?
- **OQ-X4** — does §5.7's alert belong in `juniper-deploy`'s `alert_rules.yml` (PR 3) or ship with
  PR 1 as a rule file? Splitting it risks PR 1 claiming a channel that is not yet wired.
- **OQ-X5** — the enforcement gap (§8.1). Deferring it is what turned SEC-F20 into X7; a
  closure-aware AST test is the only mechanical option identified.

---

## 10. Validation record

- **Lane A (3 agents, distinct entry points)** — empirical discrimination with kernel-level
  evidence; static concurrency census; prior art and blast radius. The reconciler's own mechanism
  hypothesis was **excluded** by measurement.
- **Fix design (4 agents, different lenses)** — minimal, systemic, operational, architectural.
- **Lane B (2 agents, opposing briefs)** — refuted the resulting plan **in full** (§4).
- **Design review round 1 (1 agent, measurement-first)** — validated D1's mechanical core; refuted
  its safety layer on ten counts.
- **Design review round 2 (1 agent, briefed on the corrections only)** — **nine blocking findings**,
  including a *restored-and-reclosed* instance: corrections 5 and 6 cancelled, producing a test that
  passes on the defect while its own vacuity guard fails. Also found that the revision would have
  deleted the product's only working outage indicator (PR #340), that the shared breaker poisons the
  cache, that no probe reads the body, and that a constraint was added with no design satisfying it.
- **Reconciler re-derivations**: the 123 s cost (client and end-to-end), executor size (20), client
  defaults and retry-verb list, the dashboard's own 1.0 s/2.0 s budgets, the ruff gate's green
  result, the dead `workers: 4` config, the `:1012-1031` cache anti-pattern, the adapter's
  return-not-raise behaviour, the `values.yaml` negation, the PR #340 indicator, and the shared `_cb`.

**Status of this revision**: §§5-10 are a **rewrite**, not a patch, and have **not** been reviewed.
Four successive plans in this arc were refuted — every one by measurement, none by reasoning. The
next round should be measurement-first and should target §5.1's classifier table, §5.7's channels,
and whether §8's inclusion keeps PR 1 reviewable.
