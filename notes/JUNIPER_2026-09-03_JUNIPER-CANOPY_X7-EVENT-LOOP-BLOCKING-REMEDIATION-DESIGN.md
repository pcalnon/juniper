# Juniper-Canopy — X7: Event-Loop Blocking on an Unreachable Backend — Remediation Design

- **Project**: Juniper — juniper-canopy
- **Author**: Paul Calnon
- **Date**: 2026-09-03
- **Status**: Revision 2 — validated root cause; first plan refuted (§4); §5 core validated by measurement and its safety layer refuted and rewritten (§10); revision pending re-review
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

> **REVISION (2026-09-03, review finding B1 — this was the design's decisive defect).**
> **Failure must be detected from the PAYLOAD, not from an exception.** `get_training_status`
> (`cascor_service_adapter.py:1968-1976`) **does not raise**. It returns
> `{"is_training": False, "error": "<connect error>"}` on the exception path and
> `{"is_training": False, "error": "circuit open"}` from the breaker's fallback. Measured against a
> dead cascor: **8 consecutive ticks, zero raises.**
>
> So the first draft's `except Exception → record_failure` was **unreachable code**. `record_success()`
> would have run every tick, the state would never have left `FRESH`, and the cache would have
> stamped a failure payload as fresh — fabricating "not training" (violating C6) and silently
> defeating §5.4, §5.5 and tests X7-T3/T4/T5 in one stroke.
>
> **The refresher must classify a tick as failed when the payload carries an `error` key** (and
> specifically `"circuit open"`), independently of whether an exception was raised. Exception
> handling is retained as a backstop, not as the mechanism. This is the single most important
> correction in the revision, because it is what makes staleness observable at all — and silent
> staleness is this architecture's known failure mode (§5.6).

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

> **REVISION (2026-09-03, review findings B2/B3).** The first draft proposed that
> `/v1/health/ready` return **503** when cascor is unreachable, and cited
> `juniper-deploy` `values.yaml:222-226` as documenting that contract. **That citation was wrong —
> the document states the negation**: *"readiness 503s **only when ws_manager is unbound** (upstream
> juniper-data / juniper-cascor outages remain **200/degraded** so the dashboard stays useful with
> cached state)."* The proposal is additionally forbidden by an explicit named regression guard,
> `test_canopy_never_returns_503_on_upstream_down` (`src/tests/unit/test_health.py:300-315`), whose
> docstring states canopy must not 503 on upstream-down because "it would page on every downstream
> incident", and by the ratified probe-graph DoR, which prescribes a test-first amendment procedure
> for any such change.
>
> Operationally the proposal was also harmful: with `replicaCount: 1` behind a single-backend
> Ingress, a readiness 503 removes the dashboard from its own ingress ~50-70 s into a cascor outage
> — exactly when an operator needs it.
>
> **The 503 is withdrawn.** Note the same sentence names **cached state** as the sanctioned
> mechanism, so the cache (§5.1) is endorsed by the very policy that forbids the status-code change.

| endpoint | touches upstream | contract |
| --- | --- | --- |
| `/v1/health/live` | **never** | in-process liveness only; unchanged |
| `/v1/health/ready` | **never inline** — reads cache | **200** `ready` / **200** `degraded` on a cascor outage (unchanged status policy); 503 remains reserved for `ws_manager` unbound |
| `/v1/health`, `/health`, `/api/health` | **never inline** — reads cache | **200**; body carries `cascor_reachable`, `cascor_status_age_seconds`, and `stale: true` when not fresh |

The behavioural change is therefore **not** the status code but the **body and the latency**: these
endpoints stop blocking, and they start telling the truth about staleness (C7, C9).

### 5.5 Safety interlocks: do not fabricate a negative — but do not fail closed either

> **REVISION (2026-09-03, review finding B4).** The first draft had these interlocks **fail closed**
> on `STALE`/`UNKNOWN`. That is withdrawn: it protects nothing and breaks recovery.
>
> - **Protects nothing**: all four snapshot gates are redundant with cascor's own FSM
>   (`juniper-cascor/src/api/routes/snapshots.py:279, 330, 379, 435`), which rejects the same
>   operations server-side; the fifth guards an operation documented as harmless.
> - **Breaks recovery**: failing closed bricks **Restart even after the run is stopped**, bricks
>   Start through an un-enumerated gate (`service_backend.py:106-107`), and bricks model-swap —
>   precisely the actions an operator takes during an X7 event. Stop and reset survive; the ones
>   that matter do not.

The retained requirement is narrower and is C6: **never present an unknown status as a fresh
negative.** `is_training_in_progress()` returning `False` on error is the fabrication to remove; the
correct value for "we do not know" is *unknown*, surfaced as `stale` + age (C9), with the decision
left to cascor's FSM, which owns it.

Separately, `_swap_backend`'s gate (`main.py:3710`) is inline-blocking **and** fails open, so it
permits a model swap during a live run when cascor is hung. That is a genuine defect, but it is a
*different* one; it is recorded in §8 rather than fixed by inverting an interlock here.

### 5.6 Canopy has run this architecture before, and it failed — what is different

**This is the most important section of the revision.** Canopy previously served status from a
relay-fed in-memory global. On **2026-07-10 that global went ~8 hours stale when the WS relay
silently died**, and the remedy — still in the code, at `main.py:1224-1237` — was to invert the
posture to **LIVE-FIRST**:

> *"…served base fields solely from the relay-fed `training_state` global — which went ~8 h stale in
> the 2026-07-10 session when the WS relay silently died. The base fields now ride the same
> live-fetch posture … and the relay-fed global is only the fallback on upstream error, explicitly
> marked `stale: true` with an age."*

**X7 forces the opposite posture.** Live-first is exactly what blocks the loop; §5 is cache-first by
necessity. So this design must be read as *re-introducing the shape that previously failed*, and it
is only defensible if it carries the property whose absence caused that failure.

That property is **not** live-fetching. It is **staleness that is impossible to miss**:

| 2026-07-10 failure | this design's answer |
| --- | --- |
| the relay died **silently** | the refresher classifies failure from the payload (§5.1 revision), so a dead upstream is *recorded*, not smoothed over |
| the stale value looked fresh | `stale: true` + `age_seconds` on the wire for every non-fresh read (C9), reusing the idiom `main.py:1224-1237` already established |
| nothing alerted | `consecutive_failures` and cache age are exported, and staleness beyond a threshold is an alertable condition |
| it took 8 h to notice | `/v1/health`'s body carries the age, so the existing 15 s/30 s probes observe it continuously |

The first draft would have failed this test outright: because its failure detection was unreachable
(§5.1 revision), its cache would have reported `FRESH` forever against a dead cascor — **reproducing
the 2026-07-10 incident exactly, with better latency.** That is why B1 is classified as decisive
rather than as a detail.

---

## 6. Test plan

Specified to fail on today's code, and specified against the two vacuity traps this arc measured.

> **REVISION (2026-09-03, review finding B5).** **X7-T1 as first written PASSES on today's broken
> code** — measured 20/20 completions, max 14 ms. The "0 completions in 40 s" figure in §4.4 came
> from a scenario with a **concurrent blocking driver**, which the test specification omitted. A
> guard test that passes on the defect is the third vacuous check this arc has found (after the ruff
> hook and the latency percentile), so the driver is now part of the specification, not context.

| id | test | must |
| --- | --- | --- |
| **X7-T1** | **completion count** under load: hold **≥3 concurrent in-flight requests to a cascor-touching route** against a hung stub (the driver is mandatory — without it the test passes on the defect), and assert **all N** control requests to `/v1/health/live` complete | fail today, pass after |
| **X7-T2** | vacuity guard for T1: assert the control sample size is non-zero, the driver actually blocked (its requests did **not** complete), and the route census ≥ 70 | a 0/0 sample, or an absent driver, must not read as success |
| **X7-T3** | the refresher classifies a **payload-carried** error as a failure: feed `{"is_training": False, "error": "circuit open"}` and assert `state` degrades and `value` is **not** overwritten | fail today — the draft's `except Exception` never fires (§5.1) |
| **X7-T4** | no fabricated negative: with the cache non-fresh, a status read is marked `stale` with an age and does **not** report a bare `is_training: false` as current | fail today |
| **X7-T5** | `/v1/health/ready` **stays 200** on a cascor outage while its body reports `cascor_reachable: false` + age — asserted *alongside* the existing `test_canopy_never_returns_503_on_upstream_down`, which must continue to pass | guards the withdrawn 503 from returning |
| **X7-T6** | injected client does not retry non-idempotent verbs: a timed-out `POST` reaches a counting stub **once** | fail today (**4×**) |
| **X7-T7** | outbound concurrency never exceeds the semaphore bound under a hung stub | fail today (peak 20/20) |
| **X7-T8** | **abandonment**: requests whose caller has gone away do not reach upstream (C10) | fail today (30 abandoned POSTs → **30** upstream calls) |

**Harness hazards, both hit during this arc**: pytest's `timeout_method="signal"` cannot interrupt a
worker thread, and `ThreadPoolExecutor` joins at interpreter exit — a naive test hangs the session.

> **REVISION**: the first draft's mitigation — "shut the executor down explicitly" — is **not
> achievable** for `asyncio.to_thread`, which uses the loop's default executor and exposes no
> shutdown seam to the caller. Measured: a hung `to_thread` blocked `asyncio.run` finalisation past
> 40 s (bounded only by `THREAD_JOIN_TIMEOUT=300`). **The stubs must therefore be bounded so the
> thread always returns** — never "hung forever" inside the pytest process. Note this is a
> *test-harness* constraint only: in the live server uvicorn's `capture_signals` re-raises from
> inside `serve()`, so `Runner.close()` never runs and SIGTERM exits cleanly in **0.161 s**
> (measured).

**Placement**: the coverage gate reads only the unit lane (`src/tests/unit/`,
`src/tests/regression/`, `-m "not slow"`), so these must live there and must not be marked `slow`.
`status_cache.py` is a new small module and is a genuine ≥90 % per-file coverage risk — it must be
table-driven tested to the gate.

---

## 7. Phasing

| PR | repo | contents |
| --- | --- | --- |
| **1** | juniper-canopy | `status_cache.py` + refresher + read paths + health contract + injected client + interlocks + X7-T1…T7 |
| **2** | juniper-canopy | demo-mode honesty (§9) — **must precede any probe tightening** |
| **3** | juniper-deploy | probe retargeting + image-tag bump, **only after 1 and 2** |
| **4** | juniper-cascor-client | **cut a Release and pin the floor** — see below |

> **REVISION (2026-09-03, review finding B8).** PR 4 as first written is **already done**.
> `juniper-cascor-client` `main` has carried `["HEAD","GET"]` since commit `ff3df6c` (2026-08-28),
> but `git tag --contains ff3df6c` is **empty** and `pyproject.toml` still reads `0.7.0` — the fix
> is **committed, unreleased and unversioned**. The remaining work is therefore a **Release plus a
> version floor pin in canopy**, not a code change. Per the ecosystem release convention that is a
> GitHub Release (never a bare tag push) with archived notes.
>
> Until that floor lands, canopy's injected client (§5.3) is what bounds the verb list — so §5.3 is
> a *bridge*, not a duplicate of PR 4.

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

### 8.1 Four paths that still produce the FULL outage after PR 1 (review findings B6/B7)

PR 1 covers the polled read path. These are not on it, and each reinstates X7 on its own:

| path | anchor | why it still blocks |
| --- | --- | --- |
| **the metrics relay** | `cascor_service_adapter.py:755-763` | on `cascade_add` the relay coroutine calls `extract_network_topology()` **synchronously inside `async`**. Measured **123 s blocked per 183 s — with no user present at all.** This is the most serious residue: it recurs during ordinary training. |
| **WS connect** | `main.py:705` | `get_status()` on the accept path |
| **`_swap_backend`** | `main.py:3718` | `initialize()` inline — measured **6 × 123 s from one click** |
| **lifespan auto-discovery** | `main.py:294`, `:322` | runs before the refresher exists; the demo-fallback probe is skipped on this path |

**Consequence for sequencing**: PR 1 alone does **not** close X7. The relay path in particular must
be included or the defect survives the fix that claims to remove it. It is folded into PR 1 rather
than deferred, precisely because a partial fix that looks complete is how SEC-F20 recurred as X7.
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
- **Adversarial round on §5 (2026-09-03)** — one reviewer, briefed to prefer measurement over
  argument. Outcome: **the mechanical core survived; the safety layer did not.**
  - **Survived, by measurement**: the refresher keeps the loop free under a hung upstream (80/80
    completions, mean 3.0 ms, max 4.7 ms); it **cannot overlap** (`starts=1, returns=0,
    peak_inflight=1`), so "one in-flight call" holds; no executor leak; SIGTERM exits in 0.161 s;
    `Semaphore(4)` caps concurrency as claimed.
  - **Refuted**: failure detection was unreachable code (B1, decisive); the 503 contract was
    forbidden and mis-cited (B2/B3); fail-closed interlocks protect nothing and brick recovery (B4);
    X7-T1 passed on the defect (B5); four outage paths were missed (B6/B7); PR 4 was already written
    upstream (B8); the semaphore leaves an unaged queue (M1); `allowed_methods` does not stop
    connect-level retries (M3); and canopy had already run and removed this architecture (M8).
  - All ten are folded into the revision above, each marked at the section it changes.
- **Residual uncertainty**: the **revision** has not itself been reviewed. Per the consensus
  procedure the fix pass is the least trustworthy part of any document, and this arc has now
  refuted three successive plans — so the next round is briefed on the changed sections only.
- **Known-unfixed by design**: §8.1's four paths are in PR 1's scope but unmeasured as a set;
  `JuniperDataClient` remains unbounded; the enforcement gap (§2.2) is untouched and is the
  mechanism by which SEC-F20 became X7.
