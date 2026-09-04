# HANDOFF 2026-09-04 — X7 slice 1a: off-loop discipline

**Session**: canopy model/dataset catch-22 → X7 (event-loop blocking) → slice 1a
**Predecessor**: <https://claude.ai/code/session_01UxSBtM3k8X27dEPX54KEgK>
**Validation**: independently reviewed; 2 blocking + 5 must-fix findings folded in (see §Validation)

---

## Handoff goal (paste everything between the rules as the new thread's first prompt)

---

Continue **X7 slice 1a — move every synchronous network call out of juniper-canopy's async
route handlers**, until the committed gate test turns green **and** the two items it cannot see
are done.

### Completed so far

- **X7 root-caused and measured.** Canopy stops answering HTTP — `/v1/health` included — while
  juniper-cascor is unreachable: synchronous retrying `requests` I/O inside `async def` route
  handlers on a **single-worker** uvicorn blocks the whole event loop. End-to-end: **5.7 ms**
  healthy, **3.0 s** cascor stopped, **123.12 s** cascor hung (`SIGSTOP`), **5.1 ms** recovery
  with no restart.
- **Design of record on juniper-ml `main`, revision 4**:
  `notes/JUNIPER_2026-09-03_JUNIPER-CANOPY_X7-EVENT-LOOP-BLOCKING-REMEDIATION-DESIGN.md`
  (ml#1596 + ml#1610). **Read §§3, 5.2, 6, 7 before writing code.**
- **Slice 1b MERGED** (canopy#566): cascor client budget explicit, `retries=0`. Measured
  **3.005 s → 0.001 s** per refused tick; a counting stub showed a timed-out POST go from
  **4 attempts to 1**. (The design quotes 0.002 s from an independent run; both are correct —
  same order, different host.)
- **Slice 1a gate committed RED**, canopy branch `fix/x7-1a-off-loop-discipline` @ `d33ab0a`:
  `src/tests/regression/test_x7_off_loop_discipline.py`, failing at **52**, `UNRESOLVED 0`.

### Remaining work

1. **Offload the 52 sites the gate lists**, in `juniper-canopy/src/main.py`. Pattern:
   `X.method(a, b=c)` → `await asyncio.to_thread(X.method, a, b=c)`. `asyncio` is imported and
   the idiom is used correctly ~30 times; `main.py:1239` is the exemplar. Re-run the gate after
   each batch — the count must fall monotonically to **0**.
2. **The relay — the gate CANNOT see this one.** `extract_network_topology()` at
   `backend/cascor_service_adapter.py:771`, called synchronously inside `async def _relay_loop()`.
   Measured **123 s blocked per 183 s with no user present** — it recurs during ordinary training.
   Design §5.2 puts it in slice 1a. It is a `self`-method with internal I/O, so a receiver-based
   scan cannot detect it; verify by inspection.
3. **Per-thread sessions.** The `requests.Session` is at
   `juniper_cascor_client/client.py:142` — **a different repo**; canopy holds no `Session` of its
   own. Options: inject a session-per-thread client through the existing seam
   `CascorServiceAdapter(client=...)` (`cascor_service_adapter.py:494`), or fix upstream. Decide
   and record which. Rationale: the blocked loop currently serialises a non-thread-safe `Session`
   at concurrency 1, and offloading removes that accidental protection (design §5.2, C5).
4. **Write the three missing design tests** (§6): **T-A2** (≥3 concurrent drivers against a
   **2.0 s bounded** stub; assert `/v1/health/live` max latency **< 500 ms**), **T-A3** (T-A2's
   vacuity guards — sample non-empty, each driver's latency ≥ the stub bound, and the driver route
   is one T-A2 actually blocks on), **T-A4** (per-thread session). T-A3 exists *because* an
   earlier draft's driver route was outrunnable, so T-A2 passed while its own guard failed.
5. **Run the full suites**: `cd src && conda run -n JuniperCanopy1 python -m pytest tests/unit/ tests/regression/ -q`.
   Expect churn — the measured surface is **144 of 333 test files**.
6. Open the PR against `main` (**never stacked** — the base-branch guard fails any non-default base).
7. Then slices **1c** (status cache + classifier) and **1d** (admission control), per design §7.

### Key context — settled; do not re-litigate

- **Four plans were refuted before this one, every one by MEASUREMENT.** §4 of the design records
  the first in full. **Do not** "just bound the timeout" — `timeout=30, retries=3` *are* the
  library defaults, so passing them is a literal no-op, and no `(timeout, retries)` pair satisfies
  both ρ<1 and the dashboard's own **1.0 s** fast-lane budget (`canopy_constants.py:373-374`).
  **Do not** offload only the hot handlers — measured, one request to one un-offloaded handler
  reinstates the full outage permanently and never recovers. **Do not** route health through the
  circuit breaker — it runs `func()` inline (`circuit_breaker.py:96`); 5 × 123 s to open.
  **Do not** raise `workers` — a no-op as launched (`main.py:4419` passes an app object), and it
  silently breaks WS fan-out and the hot-swapped backend.
- **Constraint C4 is DEFERRED, not satisfied.** Design §4.2 refutes *bare* `to_thread` partly on a
  measured **3 → 42** upstream amplification with the executor at 20/20. Slice 1a intentionally
  ships bare offload because 1b already bounds per-call cost; **bounded concurrency is 1d**. Say so
  in the PR body rather than implying 1a satisfies C4.
- **The slices are split by MECHANISM, each exhaustive over its own.** Never "core now, remaining
  paths later" — that split is how SEC-F20 recurred as X7.
- **1a alone closes X7.** 1c and 1d are load reduction and honesty; if 1c's staleness guarantees
  can't be met it can be dropped without reopening the defect.
- **The count is 52, and the design's "36"/"37" are superseded.** It moved 40 → 39 → 37 → **52**.
  The first three moves each removed a false positive; the last **added 15 real sites** after the
  gate's own unsoundness was found (below). Update the design's §5.2 count when you touch it.
- **`UNRESOLVED` fails the gate on purpose.** Adjudicate new receivers into the tables at the top
  of the test file; never widen a blanket rule. Excluded on verified grounds: an awaited
  `httpx.AsyncClient` (`main.py:1646`); `DataAdapter` (no network I/O); and two `backend._demo`
  accessors — excluded **by exact expression, not prefix**, because demo mode *does* reach
  juniper-data via `JuniperDataClient`, which wraps `requests` internally and is invisible to a
  grep for `requests.`.
- **Redis and cassandra sites are IN scope** (4 of the 52). Same mechanism, different upstream;
  `redis_client.get_status` is `def` at `:276`, called in an async handler.

### The gate was unsound — understand this before trusting it

Its exemption was **expression-based and module-global**: any call whose expression appeared
offloaded *anywhere* was skipped *everywhere*. Because `:3574` offloads `backend.get_status`,
every other `backend.get_status()` was invisible — including `health_check()`,
`health_check_deprecated()` and `readiness_probe()`, the three endpoints X7 is *defined* by.
It also degraded as work progressed: offloading `:3129` drove the count 37 → 35 because the
cassandra twin at `:3171` shares the expression and vanished un-fixed. **31 edits would have
driven it to 0 with ~21 sites still blocking.** Fixed in `d33ab0a` — exemption is now site-local
only. If you touch the gate, do not reintroduce cross-site matching.

### Traps that cost the predecessor session time

- **`gh` 2.46.0 breaks all `gh pr edit`** — use `gh api -X PATCH repos/.../pulls/N -F body=@file`.
- **Backticks in `git commit -m "…"` are shell-interpolated** — always `commit -F <file>`.
- **`gh run list --branch` can read EMPTY while the REST API shows runs in flight.**
- **Canopy never reaches DOM stability** (`document.title` sits at "Updating…"), so Playwright's
  default click and chrome-devtools' click both time out; use `locator.click({force: true})`.
- **`util/isolated_stack.bash` derives its root from its own location** — from a worktree it
  resolves to a nonexistent path. Always set `JUNIPER_E2E_PROJECT_DIR` **and** a distinct
  `JUNIPER_E2E_RUN_DIR`, or you clobber another session's pid files.
- **Do not disturb ports 8050/8201** (operator) or **8051/8101/8202/8211** (another session).
  Black-hole listener for the hung-upstream case:
  `juniper-ml/util/ad-hoc/2026-09-03_blackhole_listener.py`.
- **Test-harness constraint** (design §6): `asyncio.to_thread` exposes no shutdown seam and a hung
  thread blocked `asyncio.run` finalisation past 40 s under pytest. **Bound your stubs.** New tests
  must live in `src/tests/unit/` or `src/tests/regression/` and must not be marked `slow`, or the
  coverage gate will not see them.

### Verification commands

```bash
# The gate -- currently 52, must reach 0 (run from the 1a worktree's src/)
cd /home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--x7-1a-off-loop--20260904-0130--c72c071/src
conda run -n JuniperCanopy1 python -m pytest tests/regression/test_x7_off_loop_discipline.py -q

# Full suites (expect churn: 144 of 333 files touch this surface)
conda run -n JuniperCanopy1 python -m pytest tests/unit/ tests/regression/ -q
```

The standalone census (`juniper-ml/util/ad-hoc/2026-09-04_x7_offload_census_v2.py`) is **not on
`main`** — it is on branch `design/x7-census-instruments`, which has no worktree, and it carries
the same unsoundness the gate just had. **Prefer the gate.**

### Git state

| repo | branch / worktree | state |
| --- | --- | --- |
| juniper-canopy | `main` | slice 1b merged (`ee2ec79`, canopy#566) |
| juniper-canopy | `fix/x7-1a-off-loop-discipline` @ `d33ab0a` | **gate committed RED at 52**, pushed, **no PR yet**. Worktree: `worktrees/juniper-canopy--fix--x7-1a-off-loop--20260904-0130--c72c071` |
| juniper-canopy | `fix/x7-1b-client-plumbing` | merged; worktree `worktrees/juniper-canopy--fix--x7-1b-client-plumbing--20260904-0100--c72c071` is **safe to remove** (16 ignored entries, all caches/logs) |
| juniper-ml | `main` | design at revision 4 (ml#1596, ml#1610 merged) |
| juniper-ml | `design/x7-census-instruments` | pushed, **no PR yet** — census instruments |
| juniper-ml | `design/canopy-x7-remediation` (session worktree `.claude/worktrees/wondrous-spinning-piglet`) | merged; this handoff file is committed here |

All code and documents are committed and pushed.

---

## Deferred, with pointers — NOT part of slice 1a

Recorded in `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` and the
design; carried here so they are not lost:

- **The demo-mode data-integrity chain.** Canopy falls back to demo mode silently on a cold start
  with cascor unreachable; the `"WS: Demo"` badge is **unreachable dead code**
  (`websocket_client.js:377` hardcodes `mode: "live"`), so the UI shows green "WS: Connected" over
  simulated data; `POST /api/v1/snapshots` returns **201** with an invented plausible `size_bytes`
  into a bind-mounted real archive; and the demo Prometheus gauge is used only as an alert
  **suppressor**. **Sequencing rule: do not tighten liveness before this is honest** — it converts
  a loud, self-recovering hang into a fast, silent restart into the simulator.
- **The original catch-22** — `(recurrence, equities_seq)` compatible but unreachable. Design:
  `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`; PRs 1–3 unstarted.
- **canopy seeds 6 of juniper-data's 16 generators**, hiding five rank-3 regression datasets.
- **`JuniperDataClient` is unbounded** (`demo_mode.py:918`, `:1829`) — same 123 s exposure.
- **PR 4**: `juniper-cascor-client` has `['HEAD','GET']` on `main` since `ff3df6c`, but
  `pyproject.toml` reads **0.7.0** against tag `v0.7.0` — needs **version bump → Release → floor
  pin**, not a code change.
- **The enforcement gap** — ruff cannot see this class (its hook reports "All checks passed!"
  against these sites), and the new gate is canopy-local, not ecosystem-wide. This is the mechanism
  by which SEC-F20 became X7.

---

## Validation record

Independently validated before archiving, per the consensus procedure
(`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).

**Blocking findings, both fixed:**

1. **The gate was unsound** — module-global expression exemption hid 15 sites and would have read
   0 with ~21 still blocking. Fixed in `d33ab0a`; count corrected 37 → **52**, matching the
   validator's independent measurement.
2. **Slice 1a's scope exceeded the gate** — design §5.2's relay site is not in `main.py`. Now a
   named work item (Remaining §2) and a documented scope limit in the gate's docstring.

**Must-fix, all folded in**: the 36/37/52 reconciliation; the unactionable per-thread-session step
(the `Session` is in another repo); the three missing design tests; a verification command that
could not run; and constraint C4's deferral being silent.

**Confirmed accurate by the validator**: the whole git-state table, all four end-to-end
measurements, and every code anchor (`main.py:1239`, `:1646`, `redis_client.py:276`,
`websocket_client.js:377`, `ff3df6c`, `demo_mode.py:918`/`:1829`), `to_thread` count 30,
`UNRESOLVED 0`.
