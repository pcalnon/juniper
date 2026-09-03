# X7 — Lane A3 (PRIOR ART and BLAST RADIUS)

**Verifier**: Lane A3. **Date**: 2026-09-02. **Scope**: prior art, E2E cost, pattern uniqueness,
provenance, existing mitigations, deployment exposure. **No fixes proposed.**

Artifact discipline: every claim below is anchored to code, config, or a dated document with
`file:line`. Where the record is silent I say so.

---

## 0. Headline

**PRIOR-ART VERDICT: NOT NOVEL. Documented five times over ~5 months, root-caused live twice, filed
as a security finding once, tracked as two requirements — and deliberately deferred every time.**

The symptom class ("canopy's own self-calls starve its single worker; `/v1/health` latency degrades")
was **measured live on 2026-07-02** and filed as UX finding **F-D** and **F-F** plus security finding
**SEC-F20**. The architectural remedy was designed on **2026-05-10** and explicitly deferred with a
trigger list. The first warning is **2026-04-04** ("can make the dashboard unresponsive").

X7 as stated — *total* unresponsiveness gated on **cascor being unreachable** — is the untreated tail
of that class with a new amplifier the prior art never modelled: an unreachable upstream turns a
bounded self-contention cost into a ~123 s-per-request event-loop stall.

**Note**: the identifier `X7` appears **nowhere** in `juniper-canopy/`, `juniper-ml/notes/`, or
`juniper-ml/reports/`. It is this consensus round's local label, not a tracked defect id.

---

## 1. Task 1 — Prior art

### 1.1 The five artifacts, oldest first

| # | Date | Artifact | What it says |
|---|---|---|---|
| A1 | 2026-04-02 | `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-REMEDIATION-PLAN-01.md:308-318` and `…REGRESSION-DEVELOPMENT-ROADMAP-01.md:292` | Names the **"HTTP self-call antipattern"** for the Cassandra panel. **"Recommendation: Option B — eliminates the HTTP self-call antipattern."** |
| A2 | 2026-04-04 | `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` **HIGH-005** | Severity **High**, Likelihood **High**: *"Multiple callbacks on `fast-update-interval` (1s) make synchronous `requests.get()` calls… **These block Flask worker threads and can make the dashboard unresponsive.**"* Four remediations proposed. Same doc's **HIGH-006** flags `_api_url()`'s Flask-request-context misuse. |
| A3 | 2026-05-10 | `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md` | The **deferred design of record**. §4.2: *"every Option-B self-call occupies **two** worker slots simultaneously… **Effective concurrency is halved.**"* §6.1 trigger: *"Concurrent-user dashboard **exhausts the Flask threadpool**."* §7 out-of-scope: *"Threadpool tuning (raising Flask's worker count). A short-term mitigation if §6.1 triggers but Option C isn't ready."* Status line: **"Deferred."** Still deferred today. |
| A4 | 2026-07-02 | `juniper-ml/notes/JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-INTERACTIVE-UX-AUDIT-PLAN.md` §11 table + §11.1 | **F-D**: *"Single-worker canopy **`/v1/health` latency reached ~10 s** under the tool's polling + WS reconnect storm (39 TCP conns), recovering to ~2 ms once quiesced."* **F-F**: Redis tab shows DISABLED though healthy; *"canopy logged 'Redis metrics/status API request timed out' **37×**"*; root cause **"single-worker self-call starvation, not redis"**. §11.1 **"Architectural theme (D4)"**: *"F-C, F-D, and F-F share one root: **canopy runs a single uvicorn worker** … while several Dash callbacks make **synchronous authenticated HTTP calls back to that same worker**."* |
| A5 | 2026-07-02 | `juniper-ml/notes/JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-SECURITY-AUDIT-PLAN.md:249-251`, table row `:272` | **SEC-F20 (Medium, class DOS)** — *"single-worker self-call starvation is an availability weakness… a slow/last self-call starves the sole worker. **Verify worker count + async the self-calls.**"* |
| A6 | 2026-08-27 | `juniper-ml/notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md:33` | *"**Every interval-driven server callback does a synchronous self-call** `requests.get(self._api_url(...))` back into the **same** canopy server, so callbacks queue behind their own server's request backlog."* |

**F-D is the closest prior observation to X7's stated symptom** — same endpoint (`/v1/health`), same
direction (5000× latency degradation), same recovery-without-restart, and no crash. It was produced
by *client load* rather than by *upstream unreachability*; X7 is the same failure driven from the
other side.

### 1.2 A shipped fix for the same mechanism, on one path only

`juniper-canopy/src/health.py:16-26` (METRICS-MON R4.2 / seed-10) is an **already-remediated instance
of exactly this class**, in this repo, in a docstring:

> *"`probe_dependency` is now native async (`httpx.AsyncClient`) rather than a thread-pool offload…
> The previous `asyncio.to_thread` path was correct (it didn't block the event loop) but **consumed
> one of the default 32 worker threads per concurrent probe** — under N>32 simultaneous readiness
> checks (Kubernetes orchestrator hitting all canopy replicas during a rolling restart, dashboard
> auto-refresh fan-out to many upstream peers) **the pool would exhaust.**"*

The fix was applied to the health-probe path **only**. The 32 `backend.*` route calls and the 60
frontend `requests.*` calls were not touched.

### 1.3 Two tracked requirements, both still `proposed`

- **`JR-CAN-PERF-003`** — *"API timeout must be reduced for fast-interval callbacks."*
  `juniper-ml/notes/requirements/by-status/proposed.md:8424-8436`. Status **proposed**, P2, owner `can`.
  This is literally HIGH-005's remediation #1 from A2, formalised and never shipped.
- **`JR-CAN-PERF-004`** — *"Dashboard HTTP polling ignores WebSocket relay."*
  `…/proposed.md:10019-10028`. Status **proposed**, P2. A plan exists (A6); no code.
- Adjacent: **`JR-CAN-OBS-011`** — *"Dashboard must not hardcode localhost:8050 URLs"* (`…/proposed.md:10030`).

**SEC-F20 has no follow-up of any kind.** `grep -rn "SEC-F20"` across `juniper-ml/notes/` and
`juniper-canopy/notes/` returns **exactly two hits, both inside its own filing document**. It was
never given a JR-ID, never scheduled, never closed.

### 1.4 What is genuinely NO ARTIFACT

- **No record of canopy ceasing to answer HTTP entirely.** The record has degradation (F-D, ~10 s),
  starved panels (F-F), and starved callbacks (F-CANOPY-004/027/037/039) — never total refusal.
- **No record of the cascor-down trigger producing it.** The opposite is on record: the E2E arc drove
  cascor-fully-down deliberately (W14) and asserted canopy stayed up (§2 below).
- **No incident/postmortem document.** `juniper-canopy` has only **7 issues total** (`gh issue list
  --state all`), none related. No PR title in 400 mentions hang/deadlock/starvation of this kind.
- **No load or soak test** exercising canopy with a black-holed cascor.

---

## 2. Task 2 — The W8 connection and the E2E cost

### 2.1 W8: the cited line does not exist, and the stated cause HOLDS

`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` is now **4951 lines**; line 1756 is
inside an unrelated F-CANOPY-031 closure block. The live W7/W8 record is at **`:1823`**:

> *"**Consequence (recorded to prevent a false finding)**: **W7 / W8 and every recurrence-dependent
> row are BLOCKED until the isolated leg is restored on 8212.**"*

The surrounding block (`:1802-1830`) is a **probe table**, not a claim: `curl :8212/v1/health/ready`
refused; `:8211` answered but `/proc/<pid>/.dockerenv` present and `/proc/<pid>/cgroup` shows
`docker-106a7b2f….scope`; `docker ps` shows `juniper-recurrence 127.0.0.1:8211->8210/tcp Up 30 hours
(healthy)`. Canopy's live process env still carried `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=
http://127.0.0.1:8212`.

**Verdict: W8's stated cause is correct and is NOT a masked X7.** It is a port collision with the
operator's own Docker stack plus an exited relocated leg. Canopy was demonstrably answering
throughout — the same session ran the honest gate (`demo_mode:false`, `juniper_data_available:true`)
and drove W5 preconditions against `:8202`.

### 2.2 Matrix census (parsed from the trailing status column, all 298 rows)

| status | rows |
|---|---|
| PASS | 249 |
| BLOCKED | 35 |
| FAIL | 12 |
| INCONCLUSIVE | 1 |
| DIVERGENCE (doc-only) | 1 |
| **N-A** | **0** |

Source: `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`. No row currently
carries `N-A`; the W8 `N-A` was conditional on the `--with-recurrence` leg (`:948`, `:1183`) and the
rows were re-scored BLOCKED instead.

### 2.3 Attribution of the 35 BLOCKED rows

| cluster | rows | stated cause (with anchor) | X7-plausible? |
|---|---|---|---|
| `M-DATASET-17..26` | **10** | **Provisioning, explicitly "not a defect"**: `equities`/`equities_seq` report `available:false` because the optional `juniper-data[equities]` extra was absent. Evidence `:4009-4011`, `:4846-4856`: *"Install `juniper-data[equities]` and both generators become available. **Nothing in canopy or cascor changes.**"* | **NO** |
| `M-TOPOLOGY-09..16, -18` | **9** | Re-attributed twice: F-CANOPY-006 → F-CANOPY-037 (callback starvation) → **F-CANOPY-039** (duplicate store instance). Matrix `:473-490`. | **PARTIAL** — congestion family, but the *client-side* 12-slot variant, not the cascor-down variant |
| `M-METRICS-11..16, -18, -27` | **8** | Replay timeline never materialises; `max_index` stays 0 so every index transition clamps. Evidence `:3908-3916`: *"**Whether that is a third face of F-CANOPY-027 or its own defect is not established**, and is deliberately not claimed here."* | **CANDIDATE — unresolved** |
| `M-CANDIDATES-10/11`, `M-SNAPSHOTS-20/21` | **4** | `DEAD-EXPECTED` — **no callback exists anywhere in the repo** (static proof; matrix §5.1 register). | **NO** |
| `M-EVOLUTION-07`, `M-BOUNDARIES-07`, `M-DATASET-03`, `C2.10-03`, `C2.5-08` | **4 + 1 INCONCLUSIVE** | Mixed: F-CANOPY-025, MANUAL replay-driven, AUTO-API demo gate, debounce arm. | **UNRESOLVED** |

### 2.4 The honest cost estimate

**Rows demonstrably lost to canopy-not-answering-in-time: 9 confirmed + 8 candidate = up to 17 of the
48 non-PASS rows (~5.7% of the 298-row matrix).** The *cascor-unreachable* variant specifically:
**0 rows** — no matrix row is attributed to it.

**But the row count materially understates the cost, and this is the more important answer.** The
arc absorbed the congestion as a *methodology constraint* rather than as blocked rows. From the
matrix's own Phase-1 methodology notes:

> *"**During-run DOM reads carry the F-CANOPY-004 lag** (renders land 30 s–minutes late). Rows whose
> expected result is a DOM state were credited only after the state actually rendered; rows starved
> past the run's end were re-read post-run when the callback queue drains."*

and F-CANOPY-004 was **owner-ACCEPTED** (evidence `:117-133`) with a written freshness contract whose
fourth row reads *"during-run steady-state polling surfaces — best-effort; **no freshness
guarantee**"*. A6 §1 calls that row *"the whole mandate… an admission that during a training run, the
only time the dashboard matters, canopy makes no promise about what it is showing."*

So the cost is: **every one of the 249 PASS rows that reads a during-run DOM state was scored under a
settle-and-retry protocol built to work around this defect class**, plus three defect entries
(F-CANOPY-027, -037, -039) that consumed roughly a dozen arc segments and refuted ~20 candidate
mechanisms before the real one was found. The self-call is named as the feeder of that congestion in
A6:33. That is the cost, and it is far larger than 17 rows.

### 2.5 The one place the arc pre-registered X7's exact scenario — and it PASSED

`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md:1049-1078` defines **W14 —
Upstream-degradation induction (stop/restart cascor)**. Step 7:

> *"Confirm `/v1/health` still returns HTTP 200 with `status: "ok"` and `demo_mode: false` while
> degraded — the canopy process did not fall back to demo."*

And it was driven. Evidence `:3964-3970`, correcting an earlier handoff:

> *"The working induction is to restart **cascor only** with `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS`
> pointed at a bogus origin, leaving canopy untouched (**W14's T-2 respected — `/v1/health demo_mode`
> stayed `False` throughout**)."*

And F-CANOPY-032 (`:1754`) was driven *"under **both** upstream failure modes — control-WS-only outage
and **cascor fully down**"*, with canopy answering its own routes correctly:
`GET /api/v1/workers/list → {"workers":[],"count":0,"local_reported":false,"error":"Upstream
error","error_id":"dd1a84f727da"}`.

**This is real counter-evidence and must be reconciled.** Taking cascor *down* on localhost produces
a fast `ECONNREFUSED`; a *black-holed* cascor (paused container, DROP rule, hung process, network
partition) produces a full connect/read timeout. §5.3 below shows the two differ by ~123 s per call.
Any X7 reproduction that kills the process rather than black-holing the socket will likely **not**
reproduce, and the arc's W14 PASS is therefore not a refutation of X7 — it is a refutation of the
process-kill variant only.

---

## 3. Task 3 — Is the self-call pattern unique to canopy? **YES.**

### 3.1 Measured

`grep -rn --include=*.py -E "^\s*import requests|requests\.(get|post|put|delete|patch)\(" <repo>/src`,
excluding tests:

| repo | blocking `requests` in non-test source | verdict |
|---|---|---|
| **juniper-canopy** | **60 call sites across `src/frontend/`** | **the only offender** |
| juniper-cascor | 0 | clean |
| juniper-data | 0 | clean |
| juniper-recurrence | 0 | clean |

Canopy is also the **only** repo that mounts a WSGI sub-app: `app.mount("/dashboard",
WSGIMiddleware(dashboard_manager.app.server))` — `juniper-canopy/src/main.py:493`. `app.mount(` /
`WSGIMiddleware` / `a2wsgi` return **zero** hits in cascor, data and recurrence.

### 3.2 The one look-alike in cascor — different shape, not the same hazard

`juniper-cascor/src/cascor_constants/constants_api/constants_api_defaults.py:116`
`_PROJECT_API_SELF_HEALTH_CHECK_URL_TEMPLATE: str = "http://localhost:{port}/v1/health"`,
consumed at `juniper-cascor/src/api/app.py:564` inside `_auto_start_canopy`.

It differs on every axis that matters:
- it is a **startup background asyncio task**, not a request handler;
- it is gated on the `auto_start_canopy` setting (`src/api/settings.py:544`);
- it polls with `await asyncio.sleep(interval)` between attempts (`src/api/service_launcher.py:105-123`).

**One latent sibling worth recording, not the same defect**: `wait_for_health` uses
`urllib.request.urlopen(req, timeout=…)` — a **blocking** call — inside an `async def` on cascor's
event loop (`service_launcher.py:116-118`), polling cascor's own health endpoint, which that same
loop must serve. It is bounded, startup-only, and opt-in, so it does not carry X7's blast radius —
but it is the same anti-pattern one layer down.

### 3.3 Consequence for fix ownership

**A fix belongs in canopy, not in `juniper-service-core`.** No other service has the pattern, so
there is nothing to share and no other consumer to regress. This also means the shared-tier
regression risk of a canopy-local fix is nil.

---

## 4. Task 4 — Provenance: **inherited, then accreted. Never a decision.**

### 4.1 It arrived with the repo's first commit

```
b64f6df  2025-12-04  "cleaning up Juniper Canopy prototype for initial deployment to github…"
```
`git show b64f6df:src/frontend/dashboard_manager.py | grep -c "_api_url"` → **14**.

`_api_url` is present in the **very first commit** of `juniper-canopy`, already at 14 sites. There is
**no design note, no ADR, and no PR body** anywhere in `juniper-canopy/notes/`, `juniper-ml/notes/`,
or the 400 PR titles that argues *for* the pattern. It is a prototype inheritance.

### 4.2 Growth by accretion (count of `_api_url` in `dashboard_manager.py`)

| commit | date | sites | subject |
|---|---|---|---|
| `b64f6df` | 2025-12-04 | **14** | initial prototype import |
| `9439b1d` | 2026-04-06 | 15 | Phase 3 code quality (18 tasks) |
| `4162a49` | 2026-05-17 | 26 | P2-7 Replay timeline + History paired-diff (Issue #3) |
| `c611afb` | 2026-07-11 | 32 | stream-health: live-first `/api/state` |
| `fa5f32a` | 2026-07-22 | **37** | workers list API + dashboard integration |
| `9fbf4b8` | 2026-09-02 | **37** | HEAD |

**+23 sites in ~8 months, every one added by a feature PR, none by a design decision.** The steepest
climb (15→26) is 2026-05-17, i.e. **one week after A3 was written and the refactor deferred** —
the deferral was immediately followed by an 11-site expansion of the thing deferred.

Repo-wide today (`grep -c "_api_url"`, non-test):
`dashboard_manager.py` **37** · `candidate_metrics_panel.py` 3 · `cassandra_panel.py` 3 ·
`redis_panel.py` 3 · `internal_api.py` 1 (docstring) = **46 named sites**, plus siblings that build
the URL from `origin` / hardcoded `localhost:8050` (`dataset_plotter.py:578`,
`network_editor_panel.py:537-639`, `hdf5_snapshots_panel.py:413-622`, `replay_player_panel.py:363`,
`metrics_panel.py:1255`) — **60 blocking `requests.*` invocations in `src/frontend/` total.**

A3 §5.1 counted "~44" in 2026-05-10. The growth since is real, not a counting difference.

### 4.3 PR numbers touching the pattern

Structural additions: **#366** (deferred orphan controls), **#368/#388/#393** (model selection),
**#459** (N3 restart orchestration). Treatments of the pattern, none removing it:
- **#265** (2026-05-10) — `fix(security): inject X-API-Key into dashboard self-calls (Bug 4)`; the
  Option-B stepping stone. Bug 4 write-up: `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_IMAGE-BUILD-BUGS.md:207-239`.
- **#345** — `fix(security): exempt canopy's own self-calls from rate limiting (#2a)`.
- **#350** — `fix(tests): align metrics-panel self-call assertions with internal_api_headers()`.
- **#341** — `fix(dashboard): render circuit-open /api/status as "Unreachable" not "Stopped"`.
- **#443** — `fix(dashboard): N1 — un-gate metrics/topology polls with empty-guard + to_thread + bounded full-mode fetch`.
- **#507 / #509 / #511** — callback-starvation remediation Stages 1–3 (gating and consolidating polls).

Every one of these makes the self-call *work better*. None removes it. **Option C has never been
scheduled.**

---

## 5. Task 5 — Existing mitigations, and what they do NOT cover

### 5.1 Inventory

| # | Mitigation | Where | Covers the cascor path? |
|---|---|---|---|
| M1 | **Circuit breaker**, `failure_threshold=5`, `recovery_timeout=60.0`, name `"cascor"` | `src/backend/circuit_breaker.py`; constants `src/canopy_constants.py:648-650`; wired `cascor_service_adapter.py:518, 2089-2095` | **Yes but weakly** — see §5.2 |
| M2 | Breaker-open surfaced in the UI as "Unreachable" not "Stopped" | canopy#341 | display only |
| M3 | **Startup** cascor probe with **silent demo fallback** | `src/main.py:322-337` | startup only; see §6.3 |
| M4 | `juniper_data_available` global | `src/main.py:122, 312-322, 1484, 1691` | **juniper-data only. There is NO `cascor_available` equivalent.** |
| M5 | Native-async `probe_dependency` (`httpx.AsyncClient`) | `src/health.py:63-108` | **health probes only** — the fix for this class, applied to one path |
| M6 | `asyncio.to_thread` on ~20 route paths | `src/main.py:967, 1239, 1360, 1423, 1436, 2027, 2081, 2147, 3553, 3574, …` | partial — **32 sibling calls have no hop**; see §5.3 |
| M7 | Short dashboard timeouts: `DASHBOARD_POST_TIMEOUT=2`, `DASHBOARD_GET_TIMEOUT=5` | `src/canopy_constants.py:421, 432` | bounds the **Dash→canopy** leg only |
| M8 | Poll gating/consolidation (tab-gating, liveness gate, empty-guard) | canopy#443, #507, #509, #511 | reduces **frequency**, not per-call cost |
| M9 | Self-calls exempt from the rate limiter | canopy#345 | avoids self-429, not self-starvation |

### 5.2 What the circuit breaker does not do

`CircuitBreaker.call()` is **not a timeout**. It counts failures *after* they complete. With
`failure_threshold=5`, five full-duration failures must elapse before it opens. On
`recovery_timeout=60.0` it half-opens and lets **one probe** through — which pays the full cost
again. So it converts a permanent stall into a **sawtooth**, and it protects nothing during the
first five calls or during each 60 s probe.

It is also **not on every path**. Only 6 adapter methods route through `_cb`
(`cascor_service_adapter.py:1970, 1980, 2099, 2117, 2130` and `get_dataset_info`). The five
`/api/train/*` control calls (`main.py:3428, 3450, 3471, 3492, 3513`) are **not** breaker-protected.

### 5.3 The gap the mitigations leave — measured, cross-lane

`GET /api/status` is `async def` and calls `backend.get_status()` **directly on the event loop with
no `to_thread` hop** (`src/main.py:1310-1317`):

```
main.py:1317        return backend.get_status()                       # on the event loop
service_backend.py:165-166   raw = self._adapter.get_training_status()
cascor_service_adapter.py:1968-1976   self._cb.call(lambda: … self._client.get_training_status())
juniper_cascor_client/client.py:11-13  requests + urllib3.util.retry.Retry   # BLOCKING, WITH RETRIES
```

The client is constructed with **no timeout and no retries override** —
`cascor_service_adapter.py:507`: `JuniperCascorClient(base_url=service_url, api_key=api_key)` — so
the library defaults apply (`juniper_cascor_client/constants.py:28-30`):
`DEFAULT_REQUEST_TIMEOUT = 30`, `DEFAULT_RETRY_COUNT = 3`, `DEFAULT_BACKOFF_FACTOR = 0.5`.

**Worst case per `/api/status` request against a black-holed cascor: 4 × 30 s + (0+1+2) s backoff
≈ 123 s of blocked event loop.** Canopy runs **one** uvicorn worker and one loop — `Dockerfile:110`
`CMD ["python", "src/main.py"]` → `src/main.py:4419` `uvicorn.run(app, host=host, port=port,
log_level=…)` with **no `workers=`**. While the loop is blocked, *every* endpoint is unanswerable,
including the `async def` `/v1/health` (`main.py:1056`) and `/v1/health/live` (`main.py:1087`).

**32 route-handler `backend.*` calls in `src/main.py` take this on-loop path** (`:184, :202, :208,
:705, :895-907, :1237, :1317, :1344, :1449, :1489, :1497, :1536, :1671, :1732, :2211, :2298, :2419,
:2529, :2543, :2626, :3428, :3450, :3471, :3492, :3513`).

Two additional hard numbers for the other lanes:
- **a2wsgi's WSGI pool is 10 threads.** `WSGIMiddleware.__init__(self, app, workers: int = 10,
  send_queue_size: int = 10)` — `a2wsgi/wsgi.py:153-160` (v1.10.10, `notes/reqs.txt:19`). Canopy
  passes no override (`main.py:493`), so the entire Dash dashboard has **10** concurrent slots.
- **`asyncio.to_thread` uses the loop's default executor**, `min(32, cpu_count+4)` — the exact pool
  `src/health.py:16-26` documents exhausting.

**Nothing runs at request time that is equivalent to the `main.py:311-330` startup probe.** There is
no request-time availability flag for cascor, no cached-status store, no stale-while-revalidate, and
no demo-mode fallback outside startup.

---

## 6. Task 6 — Deployment exposure: **YES on Kubernetes, NO on Compose.**

### 6.1 Docker Compose — unhealthy, but no restart loop

`juniper-deploy/docker-compose.yml:730-733`:
```yaml
healthcheck:
  test: ["CMD", "python", "-c",
         "import urllib.request; urllib.request.urlopen('http://localhost:8050/v1/health', timeout=5)"]
  <<: *healthcheck-canopy
```
with `x-healthcheck-canopy` (`:58-62`): `interval 15s`, `timeout 10s`, `retries 5`,
`start_period 20s`; and `restart: unless-stopped` (`:740`).

**The probe target is exactly the endpoint X7 blocks.** Five consecutive failures at 15 s → container
`(unhealthy)` in ~75–95 s.

**But plain Docker Compose does not restart on healthcheck failure** — `restart:` policies fire on
container *exit*, and nothing here exits. So the Compose outcome is: **canopy marked `(unhealthy)`
and left running, silently, for as long as cascor is unreachable.** No autoheal sidecar exists
(`grep -rn "autoheal|restart_policy"` → 0 hits). `depends_on: condition: service_healthy` (`:723-729`)
only gates startup ordering.

The image also carries its own `HEALTHCHECK` (`juniper-canopy/Dockerfile:108`):
`curl --fail --silent --max-time 5 http://localhost:8050/v1/health || exit 1` — same target, tighter
5 s budget.

### 6.2 Kubernetes / Helm — **this is the restart loop, and it is real**

`juniper-deploy/k8s/helm/juniper/values.yaml`, canopy block:
```yaml
  healthcheck:
    liveness:
      path: /v1/health/live      # async def, served by the blocked loop
      initialDelaySeconds: 20
      periodSeconds: 15
      timeoutSeconds: 10
      failureThreshold: 5
    readiness:
      path: /v1/health/ready
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
```
wired at `k8s/helm/juniper/templates/canopy-deployment.yaml:84-99`.

**A failing `livenessProbe` makes the kubelet kill and restart the container.** Threshold: 5 × 15 s
≈ **75 s**. If X7 blocks the event loop, `/v1/health/live` cannot answer, and canopy is restarted.

**And the restart is worse than the hang.** `src/main.py:322-337` — on startup with cascor
unreachable, canopy **silently falls back to demo mode**:

```python
cascor_probe = await probe_dependency("JuniperCascor", f"{cascor_url…}/v1/health/live")
if cascor_probe.status == "healthy": …
else:
    system_logger.warning("JuniperCascor unreachable at %s — falling back to demo mode", cascor_url)
    backend = create_backend(demo_mode=True)
```

The E2E matrix already names this hazard, at `:1059-1063`:

> *"**Hard rule — do NOT restart canopy during this workflow**: restarting canopy while cascor is down
> triggers the **T-2 silent demo fallback** (`main.py:322-337` — canopy re-creates a demo backend and
> **`/v1/health` still reads `status: "ok"`, only `demo_mode: true` betrays it**)."*

So on Kubernetes the full chain is:

> **cascor unreachable → canopy's loop blocks → livenessProbe fails 5× (~75 s) → kubelet restarts the
> pod → canopy restarts into DEMO MODE → the probe now passes and the pod goes Ready → operators see
> a green, healthy dashboard rendering FABRICATED training data.**

That is not a restart loop; it is worse than one. A crash-loop is visible. This terminates in a
**green pod serving simulated data**, and the only signal is the `demo_mode: true` field inside a
`200 {"status":"ok"}` body that no probe inspects. `readinessProbe` on `/v1/health/ready` does not
catch it either: the values.yaml comment states the design intent explicitly —

> *"readiness 503s only when ws_manager is unbound (**upstream juniper-data / juniper-cascor outages
> remain 200/degraded** so the dashboard stays useful with cached state)"*

— and `readiness_probe()` (`main.py:1093-1140`) returns `status="degraded"` at **HTTP 200** for an
unhealthy dependency. It never 503s on a cascor outage, by design.

### 6.3 Severity verdict

| lane | outcome | severity effect |
|---|---|---|
| Docker Compose (`juniper-deploy` default) | `(unhealthy)`, never restarted, hang persists | **no restart loop** — severity unchanged, but the hang is silent and indefinite |
| Kubernetes / Helm | pod killed at ~75 s, restarts into **silent demo mode**, then reports Ready | **materially raises severity** — availability failure converts into a **data-integrity failure** |

The Compose lane is the one in daily use; the Helm chart is `tag: "0.4.0"` and pre-production. The
k8s exposure is therefore **latent but load-bearing the moment the chart is deployed**.

---

## 7. Loose ends and honest gaps

- **The W14 counter-evidence (§2.5) is unreconciled.** Someone must drive cascor-black-holed
  (`docker pause`, or `iptables -j DROP`), not cascor-killed, before X7's trigger condition is
  settled. `ECONNREFUSED` returns in microseconds; the 123 s figure needs a dropped SYN.
- **`/v1/health` blocking implies the EVENT LOOP is blocked, not just a threadpool.** Threadpool
  exhaustion (a2wsgi's 10, or the default 32) would starve `/dashboard/*` and the `to_thread` routes
  while leaving pure-`async` routes responsive. The §5.3 on-loop chain is the only mechanism I found
  in the artifacts that explains total refusal. This is the concurrency lane's call, not mine.
- **8 rows (`M-METRICS-11..16, -18, -27`) have an explicitly unresolved attribution**
  (evidence `:3914-3916`). They may or may not belong to this family.
- **`juniper-canopy` has no `logs/` runtime evidence** examined here; a live log with 37×-style
  "request timed out" lines (as F-F produced) would be the cheapest confirmation available.

---

## 8. Anchor index

- `juniper-canopy/src/main.py` — `:122, :311-337, :493, :1056-1150, :1310-1317, :3548-3557, :4419`
- `juniper-canopy/src/backend/cascor_service_adapter.py` — `:507, :518, :1968-1976, :2089-2140`
- `juniper-canopy/src/backend/circuit_breaker.py`; `juniper-canopy/src/canopy_constants.py:421,432,648-650`
- `juniper-canopy/src/backend/service_backend.py:165-166`; `juniper-canopy/src/health.py:16-26, 63-108`
- `juniper-canopy/Dockerfile:108, :110`; `juniper-canopy/notes/reqs.txt:19`
- `juniper-canopy/notes/history/CODE_REVIEW_ANALYSIS_2026-04-04.md` HIGH-005 / HIGH-006
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-CANOPY_DASHBOARD-SELF-CALL-REFACTOR.md` §4.2, §5.1, §6.1, §7
- `juniper-ml/notes/observability/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_IMAGE-BUILD-BUGS.md:207-239`
- `juniper-ml/notes/JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-INTERACTIVE-UX-AUDIT-PLAN.md` F-D / F-F / §11.1
- `juniper-ml/notes/JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-SECURITY-AUDIT-PLAN.md:249-251, :272` (SEC-F20)
- `juniper-ml/notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md:20-45`
- `juniper-ml/notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md:948, :1049-1078, :1183`
- `juniper-ml/notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:117-133, :1754, :1802-1830, :3908-3916, :3964-3970, :4009-4011, :4846-4856`
- `juniper-ml/notes/requirements/by-status/proposed.md:8424-8436` (JR-CAN-PERF-003), `:10019-10030` (JR-CAN-PERF-004, JR-CAN-OBS-011)
- `juniper-ml/notes/regressions/JUNIPER_2026-04-02_JUNIPER-ECOSYSTEM_REGRESSION-REMEDIATION-PLAN-01.md:308-318`
- `juniper-deploy/docker-compose.yml:46-62, :718-740`; `juniper-deploy/k8s/helm/juniper/values.yaml` canopy healthcheck; `…/templates/canopy-deployment.yaml:84-99`
- `juniper-cascor/src/api/app.py:550-595`; `juniper-cascor/src/api/service_launcher.py:105-123`; `juniper-cascor/src/cascor_constants/constants_api/constants_api_defaults.py:116, :120`
- `/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/a2wsgi/wsgi.py:153-160`
- `/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/juniper_cascor_client/constants.py:28-30`
