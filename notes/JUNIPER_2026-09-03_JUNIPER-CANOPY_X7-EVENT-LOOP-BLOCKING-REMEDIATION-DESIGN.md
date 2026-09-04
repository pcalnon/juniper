# Juniper-Canopy — X7: Event-Loop Blocking on an Unreachable Backend — Remediation Design

- **Project**: Juniper — juniper-canopy
- **Author**: Paul Calnon
- **Date**: 2026-09-03
- **Status**: Draft design — validated root cause, refuted first plan, revised design pending one review round
- **Defect**: X7, first labelled in [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md) §6.1
- **Evidence**: `reports/2026-09-02_canopy-selection-deadlock/` (X7 lanes: `x7_laneA{1,2,3}.md`, `x7_fix_F{1,2,3,4}.md`, `x7_laneB{1,2}.md`)

---

## 1. Scope

Remove X7: juniper-canopy ceases to answer HTTP — `/v1/health` included — whenever juniper-cascor
is unreachable. This document specifies the remediation. It does **not** cover the demo-mode
honesty chain (§9), which is a separate defect discovered during this arc and sequenced after.

**This is the second design.** The first was refuted in full by adversarial review; §4 records why,
because every one of its four steps is the change a reasonable engineer would reach for, and three
of them are actively harmful.

---

## 2. The defect, measured

**Root cause**: synchronous, retrying `requests` I/O executed inside `async def` route handlers, on
a **single-worker** uvicorn. That blocks the event loop, so *every* route stalls — including
pure-async ones. Confirmed by four independent lanes; the reconciler's own hypothesis
(threadpool exhaustion) was **excluded** by a decisive counter-example: four concurrent *threadpool*
blockers ran in parallel (6.0 s each, not 24 s) and left the loop at 2.4 ms.

| condition                         | `GET /v1/health` | source                 |
|-----------------------------------|------------------|------------------------|
| cascor healthy                    | **5.7 ms**       | reconciler, end-to-end |
| cascor **stopped** (ECONNREFUSED) | **3.0 s**        | Lane A1 + reconciler   |
| cascor **hung** (`SIGSTOP`)       | **123.12 s**     | reconciler, end-to-end |
| recovery, no canopy restart       | **5.1 ms**       | reconciler             |

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

| id     | constraint                                                                                                                      | why                                                                                                           |
|--------|---------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **C1** | No request handler may perform an unbounded blocking call on the request path                                                   | the defect itself                                                                                             |
| **C2** | Upstream call rate must be independent of browser-tab count and poller count                                                    | ρ scales with tabs otherwise (§4.2)                                                                           |
| **C3** | Handler latency must fit the dashboard's own budget: **1.0 s** fast lane, **2.0 s** normal (`canopy_constants.py:373-374`)      | otherwise every panel renders an error div even when "fixed"                                                  |
| **C4** | Concurrent outbound cascor calls must be **bounded**, and the bound must be < the 20-slot executor (`min(32, cpu+4)`, verified) | unbounded offload measured **3 → 42** upstream requests and peaked 20/20                                      |
| **C5** | The shared `requests.Session` must not be used concurrently from multiple threads                                               | documented not thread-safe; the loop currently serialises it at concurrency 1                                 |
| **C6** | An unknown/stale backend status must never be presented as a *negative* fact                                                    | `is_training_active()` gates 409 interlocks on `restore_snapshot`, `replay`, `resume`/`retrain`, model-select |
| **C7** | At least one health endpoint must be able to report **not-ready**                                                               | today all three return unconditional 200                                                                      |
| **C8** | Retries must not be applied to non-idempotent verbs                                                                             | `POST /v1/training/start` measured reaching the server **4×**                                                 |

---

## 4. The first plan, and why it is refuted

Recorded because each step is the obvious move, and three are harmful.

### 4.1 "Bound the client's timeout and retries" — a no-op as written, and a dead end as intended

`cascor_service_adapter.py:507` constructs `JuniperCascorClient(base_url, api_key)`. The proposal
was to pass explicit values — but **`timeout=30, retries=3` ARE the defaults** (verified). The
first plan proposed applying the settings under which the defect was measured.

Choosing *different* values also fails. Lane B1 computed utilisation and confirmed each row
empirically (λ ≈ 1.47/s per tab; c = 20 offloaded):

| setting           | per-call cost | ρ, 1 tab | 2 tabs   | 4 tabs |
|-------------------|---------------|----------|----------|--------|
| today `t=30, r=3` | 123.1 s       | 9.03     | 17.6     | 34.7   |
| `t=10, r=1`       | 20.0 s        | **1.47** | 2.87     | 5.67   |
| `t=5, r=1`        | 10.0 s        | 0.734    | **1.43** | 2.84   |
| `t=2, r=0`        | 2.0 s         | 0.147    | 0.287    | 0.567  |

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

> **D1 — cascor leaves the request path.** A single background task owns all periodic cascor
> polling. Request handlers and health endpoints read an in-memory snapshot and never make an
> outbound cascor call to serve a read.

This is the only shape that satisfies C2 and C3 simultaneously: upstream rate becomes
`1 / refresh_interval` — constant, independent of tabs and pollers — and handler latency becomes a
memory read.

It also dissolves three other constraints **by construction** rather than by discipline:

- **C4** — one refresher task, one in-flight call: executor occupancy 1, never 20.
- **C5** — one caller, so the shared `Session` is never used concurrently.
- single-flight — a sequential loop cannot stampede; no lock or in-flight registry is needed.

### 5.1 Components

**`src/backend/status_cache.py` (new).** A small, dependency-free holder:

- `value`: last successful status payload, or `None` if never fetched.
- `fetched_at`: monotonic timestamp of the last **success**.
- `state`: `FRESH` | `STALE` | `UNKNOWN` — derived, never stored as a bare boolean.
- `consecutive_failures`, `last_error`.
- `age_seconds` property.

**It never stores a failure as a value.** A failed refresh advances `consecutive_failures` and
leaves `value`/`fetched_at` untouched; the state degrades `FRESH → STALE → UNKNOWN` by age. This is
the direct inverse of the `:1012-1031` anti-pattern.

**The refresher.** An `asyncio` task started in `lifespan` (`main.py:216`), following the existing
`ws-keepalive` idiom (`main.py:369`) and cancelled in the shutdown block (`:387-392`). Each tick:

```text
while not cancelled:
    try:
        payload = await asyncio.to_thread(adapter.get_training_status)   # ONE in-flight call
        cache.record_success(payload)
    except Exception as exc:
        cache.record_failure(exc)
    await asyncio.sleep(REFRESH_INTERVAL)
```

`REFRESH_INTERVAL` ≈ 1.0 s, matching the fast lane's cadence so the UI is no less current than
today. The blocking call still costs up to its bounded budget, but it occupies **one** executor
slot and **zero** request handlers.

**Read paths.** `/api/status`, `/api/network/stats` and the three health endpoints read the cache.
They become genuinely non-blocking, satisfying C1 and C3.

### 5.2 Mutating paths keep their upstream call — bounded

`POST /api/train/*`, the snapshot mutations, `patch_weights`, `add/remove_hidden_unit` cannot be
served from cache. They keep an outbound call, but:

- offloaded via `asyncio.to_thread`, **behind an `asyncio.Semaphore`** whose bound is a named
  constant well under the 20-slot executor (proposed: **4**);
- with a **bounded timeout** appropriate to a user action;
- their arrival rate is user-driven, not timer-driven, so C2 is not at risk.

Because the refresher and the mutating path can now both touch the client, C5 requires either a
`threading.local()` session or a lock at the client boundary. **Proposed: per-thread sessions**, as
a lock would serialise mutations behind a refresh.

### 5.3 Retry policy (C8)

`JuniperCascorClient.__init__` exposes only `base_url, timeout, retries, api_key` — **not
`allowed_methods`** — and its `RETRY_ALLOWED_METHODS` is `['GET','POST','DELETE','PUT','PATCH']`.
The sibling `juniper-data-client` already ships the correct `['HEAD','GET','PUT']`, so cascor-client
is the outlier.

Canopy therefore **injects a correctly-configured client** through the existing seam
`CascorServiceAdapter(client=...)` (`cascor_service_adapter.py:494`) rather than tuning `retries=`.
A separate upstream fix to `juniper-cascor-client` is filed (§9) — that is the real home for it.

### 5.4 Health contract (C6, C7)

| endpoint                               | touches upstream               | contract                                                                        |
|----------------------------------------|--------------------------------|---------------------------------------------------------------------------------|
| `/v1/health/live`                      | **never**                      | in-process liveness only; 200 alive / 503 unresponsive                          |
| `/v1/health/ready`                     | **never inline** — reads cache | 200 `ready`; **503 `not_ready`** when the cache is `UNKNOWN` beyond a threshold |
| `/v1/health`, `/health`, `/api/health` | **never inline** — reads cache | 200 with a degraded body; reports `cascor_reachable` and `*_age_seconds`        |

`/v1/health/ready` gains the ability to go red, which C7 requires and which
`juniper-deploy`'s `values.yaml:222-226` **already documents as canopy's contract** — a contract
canopy never implemented.

### 5.5 Safety interlocks fail closed (C6)

`is_training_active()` gates 409s on `restore_snapshot`, `replay`, `resume`/`retrain` and
model-select. Those call sites must consult the cache **state**, not a coerced boolean:

- `FRESH` → use the value.
- `STALE` / `UNKNOWN` → **refuse the mutating operation** with an explicit "backend status unknown"
  error. Never fall through to `False`.

This is the opposite of today, where `is_training_in_progress()` returns `False` on error and
`_swap_backend`'s gate (`main.py:3710`) **fails open** — permitting a model swap during a live run
when cascor is hung.

---

## 6. Test plan

Specified to fail on today's code, and specified against the two vacuity traps this arc measured.

| id        | test                                                                                                                                                    | must                                                   |
|-----------|---------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| **X7-T1** | **completion count**, not latency: with a stub cascor that never responds, issue N requests to `/v1/health/live` over T s and assert **all N complete** | fail today (**0 completions in 40 s**), pass after     |
| **X7-T2** | vacuity guard for T1: assert the sample size is non-zero **and** the route census ≥ 70                                                                  | a 0/0 sample must not read as success                  |
| **X7-T3** | cache never serves a failure as a value: after N failed refreshes, `state` is `UNKNOWN` and `value` is unchanged                                        | fail today (`is_training_in_progress` returns `False`) |
| **X7-T4** | interlock fails closed: with cache `UNKNOWN`, a mutating call returns an explicit error, not a 200                                                      | fail today                                             |
| **X7-T5** | `/v1/health/ready` returns **503** when the cache is `UNKNOWN`                                                                                          | fail today (unconditional 200)                         |
| **X7-T6** | injected client rejects retry on non-idempotent verbs: a timed-out `POST` reaches a counting stub **once**                                              | fail today (**4×**)                                    |
| **X7-T7** | executor bound: under a hung stub, concurrent outbound calls never exceed the semaphore bound                                                           | fail today (peak 20/20)                                |

**Harness hazards, both hit during this arc**: pytest's `timeout_method="signal"` cannot interrupt a
worker thread, and `ThreadPoolExecutor` joins at interpreter exit — a naive test hangs the session.
Tests must bound their stubs and shut the executor down explicitly.

**Placement**: the coverage gate reads only the unit lane (`src/tests/unit/`,
`src/tests/regression/`, `-m "not slow"`), so these must live there and must not be marked `slow`.
`status_cache.py` is a new small module and is a genuine ≥90 % per-file coverage risk — it must be
table-driven tested to the gate.

---

## 7. Phasing

| PR    | repo                  | contents                                                                                               |
|-------|-----------------------|--------------------------------------------------------------------------------------------------------|
| **1** | juniper-canopy        | `status_cache.py` + refresher + read paths + health contract + injected client + interlocks + X7-T1…T7 |
| **2** | juniper-canopy        | demo-mode honesty (§9) — **must precede any probe tightening**                                         |
| **3** | juniper-deploy        | probe retargeting + image-tag bump, **only after 1 and 2**                                             |
| **4** | juniper-cascor-client | restrict `RETRY_ALLOWED_METHODS` to idempotent verbs; expose `allowed_methods`                         |

**Sequencing rule (non-negotiable)**: *do not tighten liveness before demo mode is honest.* Doing so
converts a visible, self-recovering hang into a fast, silent restart into the simulator.

Lane B1 refined this: the demo fallback fires **only in `lifespan`**, so a mid-flight outage yields
the hang and never the fallback — the two are mutually exclusive by timing. Therefore **PR 1 before
PR 2 is defensible; PR 3 before PR 2 is not.**

---

## 8. What this does not fix

- **`JuniperDataClient` is unbounded** (`demo_mode.py:918`, `:1829`), reachable via
  `/api/dataset/generate` and `/api/dataset/import-file` — the same 123 s exposure, same class,
  outside this design.
- **~29 handlers remain structurally sync-in-async** after PR 1; they are bounded and off the
  polled path, but the convention is still wrong. The enforcement problem (§2.2) is not solved by
  this design — ruff cannot see it, and a naive AST rule emits false positives on the repo's own
  correct idiom (13 bare-attribute offloads, 8 named closures).
- **The a2wsgi unbounded `future.result()`** remains; it is an amplifier, not the cause.
- **`/v1/health/ready` probes its two dependencies sequentially** (10 s worst case), exceeding
  Helm's `timeoutSeconds: 5` independently of X7.

---

## 9. Open questions

- **OQ-X1** — `REFRESH_INTERVAL` and the `STALE`/`UNKNOWN` thresholds. Proposed 1.0 s / 5 s / 30 s;
  they should be derived from the probe intervals rather than chosen.
- **OQ-X2** — per-thread sessions vs a client-boundary lock (§5.2).
- **OQ-X3** — should the refresher back off when cascor is unreachable? A fixed 1 Hz against a hung
  backend costs one blocked executor slot continuously. Backoff reduces load but delays recovery
  detection.
- **OQ-X4** — does PR 1 warrant a canopy `cascor_available` global mirroring `juniper_data_available`?
  Note that flag is **write-once** (`main.py:122/315`) and never refreshed, so mirroring it naively
  would clone a stale-forever bug.
- **OQ-X5** — the enforcement gap (§8). A closure-aware AST test is the only mechanical option
  identified; it is deferred here deliberately, and deferring it is what produced X7 from SEC-F20.

---

## 10. Validation record

- **Lane A (3 agents, distinct entry points)** — empirical discrimination with kernel-level
  evidence; static concurrency census; prior art and blast radius. The reconciler's own mechanism
  hypothesis was **excluded**.
- **Fix design (4 agents, different lenses)** — minimal, systemic, operational, architectural.
- **Lane B (2 agents, opposing briefs)** — **refuted the resulting plan in full** (§4), with
  measurements.
- **Reconciler re-derivations** — the 123 s cost (client and end-to-end), the executor size (20),
  the client defaults, the retry-verb list, the dashboard's own timeouts, the ruff gate's green
  result, the dead `workers: 4` config, and the `:1012-1031` cache anti-pattern.
- **Residual uncertainty**: the design in §5 has **not** been through an adversarial round. It is a
  draft, and §4 is evidence that plausible designs in this area fail on measurement rather than on
  review.
