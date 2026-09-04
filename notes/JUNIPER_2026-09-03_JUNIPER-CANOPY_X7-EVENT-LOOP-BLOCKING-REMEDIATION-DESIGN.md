# Juniper-Canopy — X7: Event-Loop Blocking on an Unreachable Backend — Remediation Design

- **Project**: Juniper — juniper-canopy
- **Author**: Paul Calnon
- **Date**: 2026-09-03 (revised 2026-09-04)
- **Status**: **Revision 4** — root cause settled; §§5-8 restructured onto **four exhaustive mechanism slices**, of which **1a closes X7 alone**. Ready to implement 1b then 1a; 1c/1d follow.
- **Defect**: X7, first labelled in [`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md) §6.1
- **Evidence**: `reports/2026-09-02_canopy-selection-deadlock/` (X7 lanes: `x7_laneA{1,2,3}.md`, `x7_fix_F{1,2,3,4}.md`, `x7_laneB{1,2}.md`)
- **Operator surface**: [`docs/REFERENCE.md` § X7 Off-Loop Census](../docs/REFERENCE.md#x7-off-loop-census). The canopy slice-1a gate (after juniper-canopy#567) is authority for `main.py`. This document's §5.2 count of **36** is superseded — the shipped count is **58** (52 direct + 2 `HELPER` + 4 outside `main.py`). Do not stop at 36 or at the `d33ab0a` figure of 52. Body history lands with juniper-ml#1661.

---

## 1. Scope

Remove X7: juniper-canopy ceases to answer HTTP — `/v1/health` included — whenever juniper-cascor
is unreachable. This document specifies the remediation. It does **not** cover the demo-mode
honesty chain, which is a separate defect discovered during this arc and sequenced as PR 2 (§7).

**This is the fourth design.** Three predecessors were refuted, every one by **measurement** and none
by reasoning: the first in full (§4), the second on ten counts, the third on nine — the last being
that its single PR was *the partial fix it forbids*. §§5-8 are now organised by **mechanism**, which
is what finally makes the work both small and complete. §4 is retained because each of the first
plan's four steps is the change a competent engineer reaches for, and three are actively harmful —
without that record, the next reader re-derives all four.

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

## 5. The design — four mechanisms, each exhaustive

> **Revision 4 (2026-09-04).** §§5-8 are restructured around **mechanism slices** rather than
> components. Revision 3 was refuted on nine counts, the decisive one being that its single PR was
> **the partial fix it forbids** — 5 of 36 blocking sites left behind, including the very function it
> rerouted. Measured surface: **144 of 333 test files (50 % of test functions)** and a 350-750 line
> production diff against canopy's own p90 of 285. Not reviewable, not revertible.
>
> The constraint that forbade splitting was "never *core now, remaining paths later*", because that
> is how SEC-F20 recurred as X7. **Splitting by mechanism satisfies it**: each slice is exhaustive
> over its own mechanism, so none can leave a residue. §§1-4 are unchanged.

| slice | mechanism | acceptance | closes X7? |
| --- | --- | --- | --- |
| **1b** | client plumbing — bound cost per call | measured cost per refused tick | no (reduces) |
| **1a** | **off-loop discipline — all 36 sites** | **AST scan returns 0** | **yes, alone** |
| **1c** | status cache + classifier | classifier census | no (removes load) |
| **1d** | admission control | abandonment test | no (removes waste) |

**1b precedes 1a**: bare offload without bounded cost is the measured 3 → 42 upstream amplification
with the executor at 20/20. **1a alone closes X7** — everything after it is load reduction and
honesty, not outage removal. That ordering is the single most useful result of this arc.

### 5.1 Slice 1b — client plumbing

`cascor_service_adapter.py:507` constructs `JuniperCascorClient(base_url, api_key)`, taking the
defaults `timeout=30, retries=3` — the settings under which X7 was measured (§4.1).

- **`retries=0` for every canopy-originated call.** Measured: **3.005 s → 0.002 s** per
  ECONNREFUSED tick. urllib3's backoff is pure `sleep` on a blocked thread, and canopy re-polls
  anyway; a poller retries by definition on its next tick.
- **A bounded timeout**, below the *caller's* budget rather than a single global. §5.5 records the
  seven real caller budgets; a single constant drops the operator's Restart click.
- **Verb list** — a bridge only. `JuniperCascorClient.__init__` exposes `base_url, timeout,
  retries, api_key`, **not** `allowed_methods`, and its `RETRY_ALLOWED_METHODS` is
  `['GET','POST','DELETE','PUT','PATCH']`, so a timed-out `POST /v1/training/start` reaches the
  server **4×**. Canopy injects a configured client through the existing seam
  `CascorServiceAdapter(client=...)` (`:494`) until §7's PR 4 lands. **Caveat**: this bounds
  *method* retries only — **connect-level retries are unaffected**, measured 3.0 s / 4 attempts in
  both configurations, which is why `retries=0` above is the load-bearing half.

### 5.2 Slice 1a — off-loop discipline (this is the fix)

**All 36 confirmed-blocking sites** in `async def` handlers move off the loop. Not 5, not 31 — the
count is the acceptance criterion, and the scan is the test.

The guard already exists and is applied correctly at `/api/state` (`main.py:1239`) under the comment
*"keep them off the event loop so a slow cascor cannot stall every other canopy route"*; `main.py`
uses `asyncio.to_thread` 30 times. This slice makes that convention **total**.

- **Acceptance is mechanical**: a closure-aware AST scan reports **0** un-offloaded blocking calls in
  async route handlers. It must be closure-aware — a naive lexical rule reports 50 unguarded / 0
  guarded, because the repo's correct idiom includes **13 bare-attribute offloads**
  (`to_thread(backend.f)` — never a `Call` node) and **8 named closures**, so it would emit 8 false
  positives on the exemplar code while missing 13 correct offloads.
- **Session safety (C5)**: multiple worker threads now touch the client, so a `threading.local()`
  session at the client boundary is part of this slice, not a follow-up. The pre-fix serialisation
  was accidental — the blocked loop held concurrency at 1.
- **Sites the previous plan omitted** are explicitly in scope, including
  `main.py:3530 GET /api/train/status`, the WS accept path (`:705`), `_swap_backend`'s `initialize()`
  (`:3718`), lifespan discovery (`:294`, `:322`), and the metrics relay's inline
  `extract_network_topology()` (`cascor_service_adapter.py:755-763`) — the last measured at
  **123 s blocked per 183 s with no user present**.

### 5.3 Slice 1c — the status cache and its classifier

A single background task polls cascor on a timer and read handlers serve from its cache. Sequential
by construction, so single-flight and one-in-flight are structural. Measured on this shape: the loop
stays free under a hung upstream (80/80 completions, mean 3.0 ms), the tick **cannot overlap**
(`starts=1, returns=0, peak_inflight=1`), no executor leak, SIGTERM in 0.161 s.

**The classifier reuses canopy's own predicate.** Revision 3 invented one and never named its
"expected status field"; the most inferrable choice (`is_training`) appears **only on the failure
path**, misclassifying **7 of 20 shapes, all healthy → UNREACHABLE**. Canopy already ships
`CascorServiceAdapter.is_cascor_nested` (`:542`), which does *positive* detection of nested structure
for exactly the stated reason — *"rather than checking for flat keys, which could misfire"* — and is
used in production at `service_backend.py:167`. Measured 4/4 clean separation.

```text
OK            iff isinstance(raw, dict) and is_cascor_nested(raw) and not raw.get("error")
UNREACHABLE   if  raw is None, not a dict, carries a truthy error, or fails is_cascor_nested
INDETERMINATE if  the error is the SHARED breaker's "circuit open" (see below)
```

`raw is None` and non-dict rows are not defensive padding: `"error" in None` raises `TypeError` and
would kill the refresher task.

**A dedicated breaker.** `_cb` is one shared instance across five adapter call sites (`:1970`,
`:1980`, `:2099`, `:2117`). Five failing `get_network_data()` calls would otherwise trip it for
`get_training_status()`, freezing the cache 60 s **against a healthy upstream**. The refresher gets
its own, so circuit-open on its path is genuine evidence.

**Route the class, not the payload.** Revision 3 gave the UI the raw payload so that
`dashboard_manager.py:6436-6438` — the PR #340 "Unreachable" branch, the **only working outage
indicator in the product** — kept working. Measured, that re-creates the very defect PR #340 fixed:
on a half-dead 200 the payload carries no `error`, so the status bar renders **"Stopped"** while the
cache knows the backend is unreachable. The cache therefore publishes its **class**, and the UI
renders from the class. `for_status()` continues to serve last-OK plus `stale` and `age_seconds`.

### 5.4 Slice 1d — admission control

`asyncio.to_thread` is uncancellable, so abandonment cannot be implemented by cancelling. Measured:
30 POSTs abandoned by their caller at 1.25 s still produced **all 30** upstream calls over 45 s
behind `Semaphore(4)`. The achievable remedy is **admission control**: each offloaded job carries a
deadline derived from **its own caller's budget** (§5.5), and the worker checks it *before* issuing
the request. In-flight work completes; queued work for a departed caller never starts.

`Request.is_disconnected` is `async` and unreachable from inside `to_thread`, so the deadline must be
computed in the handler and passed as a value.

### 5.5 What deliberately does NOT change

Revision 3 broke things here, so the non-changes are now explicit.

- **`is_training_active()` keeps its `bool` contract.** Revision 3 widened it to a tri-state; measured,
  that escapes onto the wire through `service_backend.py:160` to 10 call sites, where `None`
  **opens all five 409 gates** and races a second run, and an `Enum` refuses a known-idle backend.
  It also reaches `/health`, `/v1/health` and `/v1/health/ready` before a reviewer sees a failing
  test — the one irreversible change in the previous plan. The health endpoints instead stop calling
  it *inline* and read the cache; the interlocks are left exactly as they are.
- **The 409 interlocks are not hardened.** Fail-closed protects nothing — cascor's FSM already
  rejects the same operations (`juniper-cascor/src/api/routes/snapshots.py:279, 330, 379, 435`) —
  and bricks Restart, Start and model-swap, the actions taken during an outage.
- **`/v1/health/ready` is left alone.** `probe_dependency` (`src/health.py:60-90`) is already
  native-async httpx, does not block the loop, and is the only live signal `make health` reads.
- **Status codes are unchanged.** `values.yaml:222-226` is binding, not supporting — *"upstream …
  outages remain 200/degraded"* — and `test_canopy_never_returns_503_on_upstream_down`
  (`src/tests/unit/test_health.py:300-315`) guards it.
- **No single global timeout.** Seven real caller budgets span **1.0 s to 30 s**; one constant
  breaks the long ones.

### 5.6 Staleness must reach a consumer that is switched on

Revision 3 named two channels and **both are dark**:

- **Prometheus is default-off.** `main.py:453` is `if settings.metrics_enabled:`, wrapping both the
  middleware and the `/metrics` mount; `settings.py:283` defaults it **`False`**. `prometheus.yml:116`
  does define a `juniper-canopy` job at a 15 s interval, and `/metrics` sits behind
  `MetricsAuthMiddleware(..., metrics_trusted_ips)` — so the channel is real but requires **both** an
  enable flag and an allowlist entry.
- **The status bar is silent on the shape that matters** — half-dead 200s render "Stopped" (§5.3),
  which is the defect, not the signal.

Therefore:

| channel | fixed by | needs config? |
| --- | --- | --- |
| **PR #340 status bar** (primary) | **1c**, by routing the class | **no** — works out of the box |
| **Prometheus gauge** (operator) | 1c registers it via `register_or_reuse`; PR 3 enables `metrics_enabled` + allowlist | **yes** |

**The acceptance condition binds to the status bar**, because it needs no configuration to be true.
The gauge is registered in 1c but only becomes observable when PR 3 turns metrics on — and the design
says so rather than assuming it.

### 5.7 Why this differs from 2026-07-10

Canopy previously served status from a relay-fed global; on **2026-07-10 it went ~8 h silently
stale** when the relay died, and the remedy (`main.py:1224-1237`) inverted to **live-first**, keeping
the cached value only as a fallback "explicitly marked `stale: true` with an age".

X7 forces the opposite posture, so 1c re-introduces the shape that failed. It is defensible only by
carrying the property whose absence caused that failure — and note **1a closes X7 without 1c at
all**, so if the staleness guarantees cannot be met, the cache can be dropped without reopening the
defect. That is a property the previous single-PR plan did not have.

| 2026-07-10 | this design |
| --- | --- |
| relay died silently | positive classification via `is_cascor_nested` (§5.3) |
| stale value looked fresh | `stale` + `age_seconds` on every non-OK read |
| nothing alerted | status bar renders the class; gauge once PR 3 enables metrics |
| 8 h to notice | age is continuous and user-visible |

---

## 6. Test plan

Designed against the **five** vacuous checks this arc has measured: the ruff hook, the latency
percentile, the completion count, the pair that cancelled, and a route choice that voided its own
guard.

**Per slice**, so each is independently acceptable:

| slice | id | test | today | after |
| --- | --- | --- | --- | --- |
| 1b | **T-B1** | per-call cost against a closed port | 3.005 s | **0.002 s** |
| 1b | **T-B2** | timed-out `POST` reaches a counting stub once | 4× | 1× |
| **1a** | **T-A1** | **closure-aware AST scan: 0 un-offloaded blocking calls in async handlers** | fails (36) | **0** |
| **1a** | **T-A2** | with **≥3 concurrent drivers** against a **2.0 s bounded** stub, **max latency of `/v1/health/live` < 500 ms** | fails (5.813 s) | passes |
| **1a** | **T-A3** | vacuity guards for T-A2: control sample non-empty, **and** each driver's latency ≥ the stub bound, **and** the driver route is one T-A2 actually blocks on | — | all must hold |
| 1a | **T-A4** | per-thread session: no `Session` shared across worker threads | fails | passes |
| 1c | **T-C1** | classifier census over the §5.3 table, incl. `None`, `[]`, `{}`, half-dead 200, `error: None` | fails | passes |
| 1c | **T-C2** | half-dead 200 renders **"Unreachable"**, not "Stopped" — PR #340 regression guard | **fails** | passes |
| 1c | **T-C3** | refresher's dedicated breaker unaffected by `get_network_data()` failures | fails | passes |
| 1c | **T-C4** | non-OK read carries `stale` + `age_seconds` | fails | passes |
| 1d | **T-D1** | jobs whose caller budget elapsed are skipped, not issued | fails (30/30) | passes |

**T-A3 exists because of a measured failure**: revision 3's driver route was one the control could
outrun, so T-A2 passed while its own guard was violated. The guard must pin the *route*, not just the
counts.

**Harness constraint**: `asyncio.to_thread` exposes no shutdown seam, and a hung thread blocked
`asyncio.run` finalisation past 40 s under pytest. Stubs are **bounded**; the discriminating quantity
is **latency**, which is why T-A2 asserts a deadline rather than completion.

**Placement**: the coverage gate reads only `src/tests/unit/` and `src/tests/regression/` with
`-m "not slow"`. Any new module is a per-file ≥90 % risk; T-C1 is table-driven for that reason.

---

## 7. Phasing

| PR | repo | slice | why here |
| --- | --- | --- | --- |
| **1b** | canopy | client plumbing | precedes 1a; bare offload without it is the 3 → 42 amplification |
| **1a** | canopy | **off-loop discipline** | **closes X7**; acceptance is an AST scan, not a judgement |
| **1c** | canopy | cache + classifier + status-bar class | load reduction and honesty; **droppable without reopening X7** |
| **1d** | canopy | admission control | removes wasted upstream work |
| **2** | canopy | demo-mode honesty | must precede any probe tightening |
| **3** | juniper-deploy | probes, `metrics_enabled`, allowlist, alert, image tag | after 1 and 2 |
| **4** | juniper-cascor-client | **bump 0.7.0 → 0.7.1, cut a Release, pin canopy's floor** | `main` carries `['HEAD','GET']` since `ff3df6c` but `pyproject.toml` still reads 0.7.0 against tag `v0.7.0`, so a Release now republishes an immutable version. The floor fits canopy's existing `<0.8.0` cap |

**Sequencing rule**: do not tighten liveness before demo mode is honest (PR 3 after PR 2). PR 1b/1a
before PR 2 is defensible — the demo fallback fires only in `lifespan`, so a mid-flight outage yields
the hang and never the fallback; they are mutually exclusive by timing.

---

## 8. Residual — what remains after all four slices

- **`JuniperDataClient` is unbounded** (`demo_mode.py:918`, `:1829`) — the same 123 s exposure via
  `/api/dataset/generate` and `/api/dataset/import-file`. 1b bounds the *cascor* client only.
- **The enforcement gap.** Ruff cannot see this class — the CI-blocking hook named "Async-route audit
  (BUG-JD-10 class)" reports "All checks passed!" against 35-40 live sites — and T-A1 is a
  canopy-local test, not an ecosystem gate. This is the mechanism by which SEC-F20 became X7, and it
  survives this design.
- **a2wsgi's unbounded `future.result()`** (`a2wsgi/wsgi.py:215-219`) — an amplifier, not the cause.
- **`/v1/health/ready` probes its two dependencies sequentially** (10 s worst case), exceeding Helm's
  `timeoutSeconds: 5` independently of X7.
- **The demo-mode data-integrity chain** — PR 2, and the reason PR 3 must not precede it.

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
