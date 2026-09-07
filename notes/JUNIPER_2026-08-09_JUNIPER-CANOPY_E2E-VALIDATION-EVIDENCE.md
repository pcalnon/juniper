# Juniper Canopy — E2E Front-End Validation: Evidence Record

**Project**: juniper-canopy end-to-end front-end validation (execution arc)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Fable 5), session "canopy functionality testing"
**Started**: 2026-08-09
**Status**: PHASE 0 COMPLETE — PHASE 1 IN PROGRESS (run `20260810T002233Z`)
**Plan of record**: [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`](JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md) (merged juniper-ml#1036, approved by owner 2026-08-09)
**Execution script**: [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md)

This file accumulates the arc's execution evidence phase by phase (plan §9). Matrix row statuses live in the matrix's own `status` column at Phase-1 close; this file holds transcripts, findings, and the PR ledger.

**Triage this ledger mechanically** — `python3 util/ad-hoc/e2e_finding_triage.py` (see [`docs/REFERENCE.md` § Canopy E2E Finding Triage](../docs/REFERENCE.md#canopy-e2e-finding-triage)). Disposition tokens (`FIXED` / `HEALED` / `ACCEPTED`) must sit in the finding **header**, in its last 170 characters. Body prose is invisible to the counter.

---

## Phase 0 — Prerequisites & stack fixes (2026-08-09) — COMPLETE

### Exit criteria (plan §6.1)

| Criterion | Result |
|---|---|
| `--up` reaches the honest gate (`demo_mode == false`, `juniper_data_available == true`) | **PASS** (rehearsal 4, ~08:40Z) |
| `--down` releases all ports | **PASS** (8051/8101/8202/8211 all free post-teardown) |
| Env preflight | **PASS** (see below) |
| PR-M1 | **MERGED** — juniper-ml#1037 |
| PR-M2 (§4.5 default, owner-ratified) | juniper-ml#1042 (auto-merge armed at time of writing) |

### Env preflight (plan §6.1 step 3)

- Ports 8050/8051/8101/8202/8211: no listeners at preflight.
- `python3.14`: present at `/usr/bin/python3.14` — **stock GIL build** (`Py_GIL_DISABLED = 0`; no `python3.14t` exists) → drove fix (2) below.
- `juniper-cascor-client` in JuniperCanopy1: `0.7.0` — meets the `>=0.7.0` floor (T-3/T-4 preflight).
- `juniper-recurrence` console script: present in JuniperCascor1 (no dedicated recurrence env; experiment_stack parity).
- Canopy `make check-env` equivalent (`juniper-env-drift-check --repo-root juniper-canopy --check-lock`): **RESULT: OK** (5 lock pins OK).

### Bring-up rehearsal ledger

| # | Command | Result | Cause / action |
|---|---|---|---|
| 1 | `--up --with-recurrence` (defaults) | FAIL (data leg) | Session-worktree gotcha: `PROJECT_DIR` derives two-up from the script → resolved to `.claude/worktrees/`; `pip install -e .../worktrees/juniper-data[api]` invalid. Action: use `JUNIPER_E2E_PROJECT_DIR` (documented override); partial-failure teardown behaved correctly. |
| 2 | + `JUNIPER_E2E_PROJECT_DIR=<ecosystem root>` | FAIL (data leg, 60s gate burn) | `PYTHON_GIL=0` fatal on the now-stock host python3.14: `Fatal Python error: config_read_gil: Disabling the GIL is not supported by this build`. Action: fix (2). |
| 3 | + GIL-probe fix | FAIL (cascor leg) | **cascor main broken at HEAD** — see Finding F-E2E-001. Action: restore PR cascor#501; rehearsal re-pointed via symlink e2e-root at the restore worktree. |
| 4 | + restored cascor | **PASS — exit 0** | data healthy 2s → cascor 2s → recurrence 2s → canopy 6s. |

**Honest gate (rehearsal 4)** — `GET http://127.0.0.1:8051/v1/health`: `status: "ok"`, **`demo_mode: false`**, **`juniper_data_available: true`**, `version: 0.4.0`; `GET /v1/health/ready`: `overall: ready`, `juniper_data: healthy`, `juniper_cascor: healthy`; recurrence `GET :8211/v1/health/ready`: HTTP 200. Teardown: all four services stopped by port; `ss` re-check empty. Full transcripts: session scratchpad `rehearsal_up{,2,3,4}.log` (summarized here; scratchpad is transient by design).

### Findings (Phase 0)

**F-E2E-001 — cascor main broken by direct-push over-deletion (CRITICAL, HEALED).**
cascor commit `4081f5b` ("removing old snapshots", 2026-08-09 03:16 CDT, direct push) deleted the stale `src/snapshots/snapshot_*.h5` artifacts **and five live source modules** (`snapshot_cli.py`, `snapshot_common.py`, `snapshot_errors.py`, `snapshot_serializer.py`, `snapshot_utils.py`; 2,635 lines). `api/routes/snapshots.py:11` and `cascade_correlation.py` still import them → `create_app` import-dies; cascor Post-Merge Main Verification and Golden Regression (WS-6 Gate) went RED on main. Landing as a direct push bypassed the per-PR sequence-safety `juniper-symbol-loss-check` screen (which exists for precisely this class). **Heal**: cascor#501 restored the five modules byte-for-byte from `4081f5b^` (`.h5` deletions honored), merged 2026-08-09T08:47:50Z; primary cascor checkout fast-forwarded.

**F-E2E-002 — isolated_stack teardown glob reproduced the same over-deletion class (FIXED in #1042).**
`do_down`'s `snapshots/snapshot_*` glob matched the **source modules** (`src/snapshots/` is a Python package), reproduced live against a fresh cascor worktree. Root-cause rhyme for F-E2E-001's sweep pattern. Glob tightened to `snapshot_*.h5` + a `snapshot_cli.py` survival guard in tests.

**F-E2E-003 — host python3.14 regressed to a stock GIL build (FIXED for isolated_stack in #1042; experiment_stack follow-up PR in flight).**
`PYTHON_GIL=0` is fatal on stock CPython (`config_read_gil`). isolated_stack's data leg now probes `sysconfig Py_GIL_DISABLED` and passes the toggle conditionally. `util/experiment_stack.bash` carries the same latent class (3 sites) — follow-up PR delegated.

**F-E2E-004 — `juniper_plant_all.bash` flat `JUNIPER_CANOPY_PORT` is probe-only (LEDGER; operator path; FIXED by juniper-ml#1385 `aaf7c751` — the canopy launch now exports `JUNIPER_CANOPY_SERVER__PORT`).**
The plant script's `JUNIPER_CANOPY_PORT` (default 8050) moves only its health-probe URL/origin derivation and is never exported into canopy's process — an operator override probes a port canopy never binds. Latent T-1 variant; works at defaults by coincidence. **Disposition (2026-08-26): FIXED by juniper-ml#1385 `aaf7c751`** — the canopy `nohup` line front-loads `JUNIPER_CANOPY_SERVER__PORT="${JUNIPER_CANOPY_PORT}"` (canopy reads `ServerSettings.port` under `env_prefix="JUNIPER_CANOPY_"` with `__` nesting), exactly as the cascor block exports HOST/PORT; pinned by `test_canopy_invocation_exports_the_server_port`.

**F-E2E-005 — `tests/test_experiment_stack_script.py` pre-existing `assertIn(..., env_text)` sites render ambient secrets on failure (LEDGER; test hygiene; FIXED by juniper-ml#1385 `aaf7c751`).**
Found by the #1044 executor while mutation-testing: the live-up stubs capture `env | grep -E '^(...|JUNIPER_)'` into `env_text`, and an assertion failure renders the whole blob — including live `JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI` tokens — the exact class `tests/redacted_env.py` exists to prevent. #1044's new assertions compare filtered line lists; the pre-existing sites remain. Follow-up: sweep that file (and siblings) for the shape. Severity: leaks only on local failure output, but real. **Disposition (2026-08-26): FIXED by juniper-ml#1385 `aaf7c751`** — the three remaining sites (the data / cascor / recurrence env captures) assert against `_env_lines_for_key(env_text, KEY)`, so a failure renders only the lines for the asserted key and never the blob.

**F-E2E-003 scope precision (from the #1044 executor)**: the JuniperData *conda* env python (3.14.2) is still free-threaded (`Py_GIL_DISABLED=1`); only the *system* `/usr/bin/python3.14` (3.14.0) is stock. isolated_stack builds its venv from the system interpreter (live break, fixed in #1042); experiment_stack launches from the conda env (latent, hardened in #1044).

### PR ledger (Phase 0)

| PR | Repo | Content | State |
|---|---|---|---|
| #1036 | juniper-ml | Planning docs (plan + matrix + dual audits) | MERGED (owner) |
| #1037 | juniper-ml | PR-M1: canopy leg nested `JUNIPER_CANOPY_SERVER__PORT`/`__HOST` + checklist §3.3 + 3 test-site inversion + negative guards | MERGED |
| cascor#501 | juniper-cascor | Restore 5 snapshot modules (F-E2E-001 heal) | MERGED |
| #1042 | juniper-ml | PR-M2: `--with-recurrence` leg (8211, occupancy pre-check, canopy URL hand-off) + GIL probe + teardown glob `.h5`-only | auto-merge armed |
| #1044 | juniper-ml | experiment_stack GIL probe (F-E2E-003 tail; latent hardening — conda-env python still free-threaded) | MERGED |

### Notes for Phase 1

- Bring-up: `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper util/isolated_stack.bash --up --with-recurrence` (post-#1042 script; cascor primary is healed so no symlink root needed).
- Gate every live check on the §4.3 body assertions, never HTTP 200.
- Evidence: matrix row statuses + screenshots per plan §9 (`<row-id>__<step>.png`).

---

## Phase 1 — Live click-by-click validation (2026-08-10) — IN PROGRESS

### Run header (plan §9 / §8.5)

| Field | Value |
|---|---|
| Run-id | `20260810T002233Z` — screenshots `reports/e2e/20260810T002233Z/`, running row record `statuses.tsv` there; matrix `status` column filled in bulk at Phase-1 close |
| Stack | data 8101 (v0.11.0) · cascor 8202 (v0.6.0) · recurrence **8212** (8211 held by the operator Docker stack at bring-up; the #1042 occupancy pre-check relocated the leg — canopy env `JUNIPER_E2E_RECURRENCE_PORT=8212` confirms) · canopy 8051 (v0.4.0). **Superseded 2026-08-10 (segment 4): the isolated recurrence leg is DOWN — see §"Stack-topology correction" below. The trio (data/cascor/canopy) is unaffected and still honest.** |
| Honest gate (§4.3) | `GET :8051/v1/health`: `status:"ok"`, **`demo_mode:false`**, **`juniper_data_available:true`**; `GET /v1/health/ready`: `ready`, deps healthy (data 20.5 ms, cascor 15.7 ms), `details.mode:"service"` |
| Canopy env (live process) | `JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS=["http://127.0.0.1:8051","http://localhost:8051"]` present (F-E2E-006 fix live); `DEMO_MODE=0`; nested `SERVER__PORT=8051` |
| Transport | WS-primary confirmed: `/ws/training` + `/ws/control` both OPEN; control handshake observed in console (`CSRF token acquired` → `Sending CSRF auth frame` → `Control WS Status: open`) — plan T-21 posture as shipped |
| Browser | Playwright MCP Chromium, fresh profile (clean localStorage) |

### Findings ledger (Phase 1)

**F-E2E-006 — isolated_stack canopy leg lacked the browser-WS origin allowlist (stack harness; FIXED ml#1049).**
Found at first live browser attach (prior session, 2026-08-09): with `JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS` unset, canopy's browser-facing sockets rejected the dashboard's own origin. Fix: `util/isolated_stack.bash` canopy leg now exports the canopy-origin allowlist pair (`isolated_stack.bash:363-364`); merged as ml#1049. Verified live this run: both sockets OPEN with the allowlist in the process env.

**F-E2E-007 — WITHDRAWN 2026-09-04, the same day it was filed. It was wrong, and the way it was wrong is the durable part (LEDGER; withdrawn).**

It claimed that the `W4-01..17` / `W1-12..14` identifiers in this arc's repeated "Blast radius"
sentence "have never existed", 18 of 20 of them, and that F-CANOPY-037's closure condition was
therefore unsatisfiable. **Both claims are false.**

`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` §4 enumerates
`### W4 — Topology exploration` as **exactly 17 numbered steps** (`:1005-1023`) and
`### W1 — Cold-start cascor training` as 19, whose steps 12/13/14 are the topology-DOM steps
(`:954-956`). Both were added 2026-08-09 in `e835e2b4` (juniper-ml#1036) and **never deleted** —
`git log --all -S` on three distinctive step strings returns that one commit each. The coverage
audit of the same day says it outright: *"W4 is a 17-step script"*
(`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-COVERAGE-AUDIT.md:353`).

**The error**: a search for the id *token* (`W4-09`) over a definition written as an ordinal (`9.`)
under a section heading. Absence of the token was read as absence of the definition.

**Three things make it worse, and they are why this entry stays as a record rather than vanishing.**

1. **The answer was in the file being edited.** `util/ad-hoc/e2e_seg17_topology_driver.py:64-72`
   already said these ids *"live in the MATRIX … NOT in the plan"*. That comment was read during the
   same session and did not register.
2. **The finding manufactured one of the ids it denied.** The literal token `W1-13` had never
   appeared anywhere in this repository's history; it entered for the first time **inside the
   sentence asserting it had never existed**. When a claim of non-existence has to spell the thing
   to deny it, that is the tell.
3. **It was convenient.** It removed the one obstacle to a closure the author was already trying to
   make — an explicit escalator in
   `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §3 that was not
   heeded.

**The replacement root cause was also wrong, and was withdrawn before it shipped.** A second draft
blamed the plan's §9 row-id scheme for having no `W<n>-NN` form, making workflow steps
"structurally untrackable per-step". Refuted three ways: `reports/e2e/20260811T010700Z/statuses.tsv`
carries **71 individually-verdicted W-rows** including `W5-01`…`W5-29` and `W6-01`…`W6-21` with
per-step FAILs, so the tooling tracks them fine; the plan at `:151` explicitly delegates workflow
ids to the matrix (*"its §4 scripts are canonical"*) and §9 is a screenshot-filename convention that
never mentions `statuses.tsv`; and the token form appears in the 2026-08-10 run, sixteen days before
the date the draft blamed. **W4 is not structurally different from W5 — it was driven once instead
of thirty times.**

Caught by the consensus procedure: three Lane A agents on independent entry points (run artifacts,
git history, plan-plus-product) and two Lane B agents on opposing briefs. Lane A found the
enumeration; Lane B2 refuted the replacement; Lane B1 independently found that the closure it
enabled also needed amendment (see F-CANOPY-037). **No round agreed with the author.**

> **A real trap, salvaged from the withdrawn entry because it is independently true.**
> `util/ad-hoc/e2e_finding_triage.py` reads a finding's severity as the **first**
> `P0|P0/P1|P1|P2|CRITICAL|LEDGER` token anywhere in the bolded header, not just the one in the
> parenthetical. This entry's first draft said *"holding the arc's only P0/P1 open"* in its prose and
> was duly triaged **P0/P1**, inventing a top-severity defect out of a bookkeeping note. **Do not
> name another severity in a header's prose**, or the count silently misreports.

**F-CANOPY-001 — dark-mode toggle glyph not synced from the persisted store on mount (P2, OPEN).**
Reproducer: toggle dark (glyph 🌙→☀️, `<html>` gains `dark-mode`) → reload → theme restores dark but the button renders the layout-default 🌙; the next click still behaves correctly (store true→false → light), so only the glyph is stale.
Evidence: `toggle_dark_mode` (`juniper-canopy/src/frontend/dashboard_manager.py:2905-2916`) is the **sole writer** of `dark-mode-toggle.children` and is `prevent_initial_call=True`; the PERF-CN-01 mount-time propagation (`:2921-2928`, `prevent_initial_call=False`) exists only for `theme-state` — the glyph Output is omitted from any mount path. Screenshots: `C2.1-01__dark.png` (correct ☀️ pre-reload), `C2.1-02__reload-glyph-desync.png` (dark theme + 🌙). Matrix rows C2.1-01/02 — both PASS on their stated expectations; this is a ledger finding, not a row FAIL.

**F-CANOPY-002 — `ws_latency.js` beacon CLOBBERS the WS bridge's `metrics` handler: the metrics fast path is dead in every live run and the panel starves (P0, root-caused; FIXED canopy#515 `04f06ff`, verified live — closure block below).**
Mechanism, proven live across two runs: `CascorWebSocket.on(type, handler)` is a **single-slot registry** — `this.handlers[type] = handler` silently replaces (`websocket_client.js:179-180`; dispatch `:258-260`). `ws_dash_bridge.js:217` registers the real `metrics` intake (feeding `_juniperWsDrain._metricsBuffer` → `ws-metrics-buffer` → `append_ws_metrics_store`, `dashboard_manager.py:3703-3712`); `ws_latency.js:75` then registers its latency-sampling `metrics` handler on the same socket — alphabetical asset load order guarantees the beacon loads after the bridge (console: "[WS Bridge] Handlers registered" precedes "[WS Latency] Beacon initialized") — and **replaces the bridge's**. Result: metrics frames arrive on `/ws/training` (run 2 raw-socket instrumentation: 401 `metrics` frames during the output phase) but dispatch ONLY into the latency sampler; the drain's metrics intake never fires (`_metricsReceived: false` / stale, buffer 0) while `state` / `candidate_progress` / `cascade_add` — types the beacon does not touch — flow normally on the same socket, and `initial_metrics` (its own un-clobbered slot) stamps the drain at reconnects. Live-run dispatch snapshot: `handlers['metrics'].toString()` = the beacon's `_recordLatency` body. Panel impact: KPI tiles / status pill / both plots / progress-detail sat frozen through both runs, catching up minutes later via the congested REST poll (M-METRICS-31 — `ws_live` correctly reads false, so the 1 Hz poll runs but lands ~30-90 s late under the F-CANOPY-003 congestion). Matrix: M-METRICS-31 FAIL (during-run), M-METRICS-32 FAIL. Fix direction (Phase 2): per-type handler LIST (registry append + dispatch fan-out), or route the beacon through the bridge. Note `off()` (`websocket_client.js:493-494`) already guards identity — only `on()` clobbers.

**CLOSED (2026-08-24, canopy#515 `04f06ff`; run `20260825T044659Z`).** The ledger's own fix direction, implemented: `on()` appends to a per-type list; dispatch fans out over a copy with the try/catch INSIDE the loop (one handler throwing cannot starve its siblings — the bridge and the beacon now share `metrics`); `off()` keeps its identity guard against the list; zero caller changes. Pinned by `src/tests/unit/test_ws_handler_fanout.py` (the JS-source idiom), including that both real `metrics` registrants remain. **Verified live on merged main mid-run:** `_juniperWsDrain.metricsReceived: true` with `lastMetricsFrameMs` **47 ms** old (the pre-fix state was "no metrics frame has EVER arrived"), `_metricsBuffer` at 24, and the `allow_duplicate` WS append callback executing 13×/45 s with `ws-metrics-buffer.data` in its `changedPropIds` — M-METRICS-31 (the liveness gate now reads fresh, demoting the REST poll as designed) and M-METRICS-32 (the WS append path) re-scored `PASS (re-validated @ 04f06ff)`. Not exercised in the window: the beacon's own `/api/ws_latency` posting cadence (its registration is source-pinned; a latency-display check can ride any future segment).

**F-CANOPY-003 — control-button loading state: success ack never re-enables; the 2 s timeout sweep lands at 30 s–minutes under callback congestion (P1; canopy#523 `9c381604`; C2.5-09 re-drive 2026-08-26 → PASS; VERIFIED LIVE, FIXED).**
Measured: Reset click → WS frame sent + success ack in ~1 s → optimistic ⏳ rendered at +4 s → button re-enabled at **+32 s**. Start's stuck window after its successful ack ran **minutes** (cleared only when the next control action fired the sweep's other Input). Evidence: the Phase-D clientside success path only `console.log`s — no button-states write and no `training-control-action` write on success (`dashboard_manager.py:233-236`); the sweep `handle_button_timeout_and_acks` (`:4246-4257`, handler `:6771-6796`) is the SOLE recovery and compares against `DASHBOARD_TIMEOUT_THRESHOLD = 2.0` s (`canopy_constants.py:384`) — the registration comment "Re-enable buttons after timeout (5s) or on control acknowledgment" is doubly stale (no ack path exists; threshold is 2 s). The 30 s+ real-world latency tracks the same server-side callback congestion that delayed every render during the run (12 Dash POSTs/s observed; `fast-update-interval` fired 26×/6 s). Matrix row C2.5-09 **FAIL**; C2.5-02's optimistic-disable half PASS.

**FIX MERGED (2026-08-26, canopy#523 `9c381604`; C2.5-09 and W2 step 2's pause-pause arm re-drive owed, alongside the F-CANOPY-005 verification on the same congestion run).** Both halves: the Phase-D JS gained `reportSuccess(transport, commandId)`, the sibling of `reportFailure`, called on WS success and on REST 2xx — it writes the ack into `training-control-action` (`success: true`, `command`, `transport`, `command_id`) AND clears that button's loading state directly via `set_props('button-states', …)`, so the ack is the primary release and the sweep only the backstop; and `_handle_button_timeout_and_acks_handler` finally implements its own name — a fresh success ack (`success` + `command` + a `ts` not older than the click) releases the button immediately, while stale acks, failures, no-`ts` actions and the click-time optimistic write leave the timeout semantics untouched. The stale "(5s)" registration docstring is corrected. `src/tests/unit/test_f003_control_button_ack.py` pins the JS contract and the sweep (4 of 12 fail on the parent); F-CANOPY-005's transport-only fallback gate is untouched.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f005`).** Across six control cycles under a live run, every button re-enabled in **0.82–3.59 s** (was 30 s–minutes) — the success ack releases the button directly, the sweep is only the backstop. C2.5-09 → PASS. **FIXED.**

**F-CANOPY-004 — server-side Dash callbacks lag behind reality during a live run; clientside callbacks are instant (P0/P1 systemic; owner ACCEPTED 2026-08-26 under a documented freshness contract, WS migration scheduled as JR-CAN-PERF-004).**

> **OWNER DISPOSITION (2026-08-26) — ACCEPTED under a freshness contract; migration scheduled.**
> After Stage 1–3 of the callback-starvation remediation (canopy#507 + #509 + #511), the measured envelope is
> **3–16 s for an interaction-triggered render** and **20–40 s for fresh-session population** — down from the
> 30 s–minutes recorded below at the finding's discovery. The owner's decision is to **accept and document
> that envelope as canopy's freshness contract** rather than hold the arc open on it, **and** to schedule the
> WebSocket-migration workstream (**JR-CAN-PERF-004**) that removes the polling architecture instead of
> tuning it. F-CANOPY-004 therefore stops gating Phase 3 entry.
>
> **The contract, as it must be stated in user-facing docs and in any row that asserts freshness:**
> | surface class | contract | notes |
> |---|---|---|
> | clientside callbacks (WS badge, depth-slider reveal, theme) | immediate | no server round-trip |
> | interaction-triggered server render (click, select, toggle) | **≤ 16 s**, typically 3–8 s | measure from the interaction, not from page load |
> | fresh-session population (first paint of a panel after load) | **≤ 40 s**, typically 20–30 s | a shorter settle reports a working panel as dead |
> | during-run steady-state polling surfaces | best-effort; **no freshness guarantee** | this is the class JR-CAN-PERF-004 exists to fix |
>
> **Scope limit — read this before citing the contract.** The contract covers surfaces that *do* render,
> late. It does **not** cover a surface that never renders at all: **F-CANOPY-037** (found the same day)
> shows the topology rebuild starved *absent*, not late, in 9 of 11 measured sessions, and no wait budget
> resolves it. Do not use this acceptance to close a row that never painted — that is F-037, and it is open.
>
> **Re-drivers:** every wait budget in the drivers is sized to the two numbers above; a row scored "starved"
> must state which class it belongs to and the budget it actually waited.

*Original finding, as recorded at discovery (pre-Stage-1..3 numbers):*
Measured, run 2 (topology tab, 1 Hz sampling for 60 s): canopy `/api/status` steady at `phase:candidate, hidden_units:1, epoch:1` for the full minute while the top status bar rendered `Output Training / Step 0 / Hidden Units 0/10` and the topology counts rendered `0/0/0/0` THROUGHOUT — yet the **clientside** depth-slider reveal (same underlying store) flipped `display:block` instantly. Same pattern everywhere: optimistic button ⏳ rendered +4 s after a clientside write; the 2 s button sweep landed +32 s (F-CANOPY-003); run-1 tiles caught up minutes post-run. Dash POST volume observed: ~12/s during a run (`fast-update-interval` alone fired 26×/6 s). Architecture note for Phase 2: every interval-driven server callback does a synchronous self-call `requests.get(self._api_url(...))` back into the same canopy server (e.g. `dashboard_manager.py:6376`), so callbacks queue behind their own server's request backlog; the WS drain pump (500 ms) multiplies POSTs during runs. Impact: during training — the only time the dashboard matters — every REST-fed surface is 30 s–minutes stale; only WS-clientside surfaces (badge) and the (currently clobbered, F-CANOPY-002) WS fast path can be truthful in real time. FA-3 rows C2.3-01..07 pass *eventually* but fail any reasonable freshness expectation; recorded here rather than as per-row FAILs since no row states a latency contract.

**F-CANOPY-005 — WS command send-promise races its own 3 s timeout under congestion: the REST fallback double-fires state-changing commands AFTER WS success (P0; root-caused live; canopy#518 `d275ce2`; re-drive 2026-08-26 → 0 double-fires + alert; VERIFIED LIVE, FIXED).**
Captured on a W2 resume: the `{command:"resume"}` frame was acked on the wire **+18 ms** after send (`command_response`, matching `command_id`), yet the send-promise rejected `"Command timeout (no command_response for 81c7f1a1-…)"` and the Phase-D fallback then POSTed `/api/train/resume` — which the (already-resumed) backend refused **409**. Mechanism: `send()` arms a per-command `setTimeout` ceiling — start 11 s, set_params 2 s, **everything else 3 s** (`websocket_client.js:396-403,410-413`) — while ack matching happens in `_handleMessage → _resolvePendingCommand` on the browser main thread (`:210-211`, `:436-447`); during a run the main thread is blocked by the F-CANOPY-004 render queue, so the expired timer task can beat the queued WS `message` task and reject a command whose ack already arrived. Consequences: (a) duplicate **state-changing** POSTs (a lost race on `start` would re-POST start; observed on resume as a 409); (b) the operator sees a failure signal for a command that succeeded — `reportFailure` fed `training-control-action` with `success:false` (console: `[Phase D] REST fallback (resume): WS rejected: Command timeout…` then `…returned 409`), though the danger alert itself ALSO never rendered (its server-side callback starved — same congestion; alert element still empty 6+ min later). Composed with F-CANOPY-003: after this sequence THREE buttons (start/pause/resume) sat stuck ⏳ disabled >8 min — during a run the interval-driven sweep pass effectively never lands (quiet-page clear ≈ +32 s), so a rejected/raced command wedges its button for the rest of the run. W2 step 2's pause-pause rejection arm is **BLOCKED** by exactly this wedge: the second pause click hits a still-disabled button, so no frame is ever sent and C2.5-10's alert is unreachable via that route.

**FIX MERGED (2026-08-25, canopy#518 `d275ce2`; the entry stays OPEN until the live verification lands, after the T6 GPU window).** Both halves are the ledger's own fix directions: (1) the send-promise timeout re-arms ONCE for a 250 ms grace window, so an ack task already queued behind the congested main thread wins the race it used to lose (the captured instance: acked +18 ms, rejected at 3 s, REST re-POST → 409); (2) every WS rejection is classed (`err.transport`) and the Phase-D REST fallback fires ONLY for transport-class failures — a business rejection (segment 10's pause-while-STOPPED, `Training cannot be paused in the current state`) now surfaces through the `training-control-action` danger alert instead of re-issuing an adjudicated state-changing command over HTTP. Pinned by `src/tests/unit/test_f005_ws_command_race.py` plus the updated Phase-D clientside pins (`test_phase_d_button_clientside.py`); full unit suite, `node --check` and sequence-safety green; merged by the owner after a branch update (`8ea00b3b`) at 21:09Z. **Verification owed** (stack on merged main, a training run for congestion): drive the control buttons — expect zero `409` double-fires; then induce a business rejection — expect the danger alert via `training-control-action` and **no** `/api/train/*` POST in the request capture. Then the closure block, the rows in its blast radius (W2 step 2's pause-pause arm; C2.5-10's alert route), and coordination with F-CANOPY-003, which touches the same Phase-D code.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f005`).** Six control cycles on a live run: **zero** `/api/train/*` POSTs from the browser and **zero** 409s (the double-fire is gone). The reachable business rejection (pause-while-paused) surfaced the danger alert *"Pause failed. Training cannot be paused in the current state"* at +7.9 s via `training-control-action` with **no** HTTP re-issue; the pause-while-STOPPED arm is N-A (the pause button is correctly disabled when stopped). C2.5-10 → PASS. **FIXED.**

**F-CANOPY-006 — the topology graph NEVER renders in the live lane: a provably-correct server render is silently never applied client-side (P0; server side exonerated live; FIXED by the F-CANOPY-027 remediation series — closure block below).**
End-to-end isolation, all captured live on run 2's completed 10-unit network: (1) data layer perfect — `GET /api/topology` serves `input_units:2, output_units:2, hidden_units:10`, 14 nodes, 89 weighted connections; (2) the rebuild callback's own request body (intercepted) carries that full topology + `depth-slider.value: 10`; (3) the server's response (intercepted) is **HTTP 200, 39 KB, a 181-trace figure, counts `2/10/2/89`** — the rebuild (`network_visualizer.py:365-…`) computes correctly; (4) the DOM never changes: counts remain the layout-default `"0"`s and the applied Plotly figure stays `data:[]` — across the whole run, post-run quiet queue, a direct store injection, AND a fresh page reload (clean renderer). Zero console errors, zero server-side callback errors. Two compounding shipped facts: the depth slider ships `value=0, max=0` (`network_visualizer.py:180-183`), so every fresh session's rebuild input is a hierarchy filter of **zero** cascade units (label renders `"0 of N"` — the "user-picked" value nobody picked); and the rebuild's 12-Input set includes the 1 s `fast-update-interval` while its own server time measures 1.5–5 s (F-CANOPY-004), keeping the same-output callback perpetually re-queued — the prime Phase-2 suspect for the renderer never painting a response (supersession/serialization), to be confirmed at fix time. Blast radius: M-TOPOLOGY-01..18 and W4 BLOCKED (graph-dependent rows); W1 steps 12–14 blocked at the DOM (cascade growth itself proven server-side and via the Evolution tab's cards). The mandate's flagship visualization is non-functional in the live lane.

**CLOSED (2026-08-24, fixed by the F-CANOPY-027 remediation series — canopy#507+#509+#511; verified live on `5f2e905`-content, run `20260825T041134Z`).** The "prime Phase-2 suspect" was exactly right: the 12-Input rebuild riding the 1 s `fast-update-interval` with 1.5–5 s server time was perpetually re-queued/superseded — the same claimed-Input/starvation family as the rest of F-CANOPY-027. After #509 gated it to `tabpoll-topology` and Stage 2 suppressed its chained metrics-store rewrites, the panel is alive in BOTH lanes: **during an active run** the graph rendered **271 traces** with the counts tracking growth in real time (the DOM read `2/13/2/134` while the status probe still said 12 units — the panel was *ahead* of the probe), renderer executing 5×/30 s; at idle, 209 traces, counts `2/11/2/103`, renderer 4×/30 s. Two 2026-08-20 sub-claims corrected by source + observation: the depth slider's `max` DOES seed from topology (observed `max=11/13`), and `value=0` means **no filter** by design (`_apply_hierarchy_filter` returns unfiltered for `depth <= 0`, `network_visualizer.py:728`) — the feared "hierarchy filter of zero cascade units" never existed. Residual cosmetic (D-ledger, not this P0): the depth label renders `"0 of N"` for the all-filter where `"all"` would be honest. M-TOPOLOGY-01..18 / W4 / W1-12..14's blocker is gone; the rows await their re-drive segment.

**F-CASCOR-001 — CUDA OOM in candidate seeding is classified "Completed — stalled (0 new units)" instead of an error state (P1, cascor repo, OPEN; filed as juniper-cascor#590 on 2026-08-26).**
W1 run 1: every `CandidateUnit` construction raised `torch.AcceleratorError: CUDA error: out of memory` at `candidate_unit.py:333`/`:392` (`torch.rand(1, device="cuda")` seed-roll) via `train_candidate_worker` (`cascade_correlation.py:3270`) — repeated per candidate — and the run transitioned `Started -> Completed` with the stall label. The UI surfaced cascor's classification faithfully (`Status: Completed — stalled (0 new units)` — honest-label plumbing WORKS, plan §7.3), but a hard environmental failure is indistinguishable from a legitimate correlation stall at every surface. Host cause: 7563/8192 MiB VRAM pinned by ~50 orphaned `JuniperCascor1` forkserver workers (the known orphan class). **Filed as [juniper-cascor#590](https://github.com/pcalnon/juniper-cascor/issues/590) on 2026-08-26** with the current anchors (`src/candidate_unit/candidate_unit.py:352` seed-roll; `cascade_correlation.py:3436` `train_candidate_worker`; `manager.py` ~`:2596` `completion_reason`, whose enumeration has no error value) and a proposed `candidate_error` completion reason / FAILED terminal state.

**F-ML-002 — `isolated_stack.bash --down` stops `${RECURRENCE_PORT}` unconditionally where `--up` refuses on collision; the in-source safety argument is unsound, though the blast radius is NARROWER than this arc has been claiming (P2, juniper-ml repo; OPEN; found 2026-08-30 at arc teardown).**

`do_down` (`util/isolated_stack.bash:466-469`) calls `stop_port "${RECURRENCE_PORT}"` — default **8211** —
with no occupancy check, justified in-source by:

> the recurrence stop is unconditional (idempotent when the leg was never started — `stop_port` logs
> "nothing listening"), so `--down` does not need to know whether `--up` ran with `--with-recurrence`.

**That argument is unsound as written.** It assumes two states — our leg running, or nothing listening —
and omits the third: *someone else* listening. `stop_port` (`:398-409`) kills whatever pid holds the
port; it cannot tell whose it is. And `--up` knows this: `recurrence_port_precheck` (`:310-318`) refuses
to start the leg when 8211 is occupied, naming the cause — *"likely the juniper-deploy stack (host 8211
-> recurrence container 8210)"*. **The up path guards the collision the down path ignores.**

**BUT — measured, and this corrects an overstatement this arc has repeated in the ledger, two handoffs
and a peer message.** `port_pid` (`:179-183`) resolves the pid via `ss -tlnpH "sport = :PORT"`, and on
this host that returns **empty** for 8211: the deploy container publishes through a proxy in another
namespace, so `ss` attributes no pid to it for this user. `stop_port` therefore logs "nothing listening"
and **kills nothing**. The claim "`--down` will kill the deploy container" is **not true as configured**.

**The accurate statement:** the missing pre-check is a real asymmetry, and the risk is *conditional on
pid visibility* — it would bite where `ss` does attribute a pid to the collider (running as root, a
runtime that publishes in the host namespace, or a non-container process squatting 8211). It is a latent
correctness defect, not the live container-killer it was described as.

**How the overstatement propagated, which is the more useful half.** It entered as a hazard line in a
handoff, was carried forward verbatim into the next handoff and the ledger, was repeated to a peer
session, and was acted on — this session stopped the trio by pid *specifically to avoid it*. Stopping by
pid was correct and harmless, but the reason given for it was not verified until after the fact. **Nobody
ran the one command that checks it** (`ss -tlnpH "sport = :8211" | grep -oE 'pid=[0-9]+'`) across four
documents and two sessions. Same shape as the arc's other propagated errors: a claim quoted forward
rather than re-derived, with the check costing one command.

**Fix (not applied here):** give `do_down` the same occupancy discrimination `--up` already has — skip
the recurrence stop unless the listener is ours (run-dir pidfile, or cmdline referencing the run root,
matching the two protection keys `reap_pytest_orphans.bash` uses). Until then, prefer stopping legs by
pid.


**F-ML-001 — `util/reap_pytest_orphans.bash` kills nohup-detached isolated-stack services (P1, juniper-ml repo; FIXED by juniper-ml#1133 `b7f7ec20` on 2026-08-17 — verified 2026-08-26, closure below).**
Freeing the VRAM via the repo's own reaper took down the live cascor service leg: isolated-stack services are launched `( cd … && nohup … & )`, so after the subshell exits they are parentless BY DESIGN — exactly the reaper's orphan predicate (candidate gate: JuniperC-env python; orphan: parent gone/init/systemd). Dry-run listed only forkserver/resource-tracker rows, but the live pass cascaded 145 kills including the service (`52 would be reaped` → `145 reaped`; the dry-run/live delta is itself a gap — children of reaped orphans re-classify mid-pass). The data leg survived only because its venv python path escapes the `JuniperC[a-z0-9]+` gate; canopy (JuniperCanopy1 — gate-matching) survived this pass but is equally exposed. Needs a service-pidfile exclusion (read `${RUN_DIR}/juniper-*.pid`) or a listener-port KEEP gate.

**CLOSED (2026-08-26, by verification: juniper-ml#1133 `b7f7ec20`, merged 2026-08-17).** The prescribed service-pidfile exclusion shipped a week before this arc reached it: `util/reap_pytest_orphans.bash` protects two roots — `JUNIPER_EXP_RUN_ROOT` and `JUNIPER_E2E_RUN_DIR` (default `${TMPDIR:-/tmp}/juniper-e2e`) — with two keys, either sufficient: the pid appears in a run-dir `*.pid` (`isolated_stack.bash` writes `${RUN_DIR}/juniper-{data,cascor,recurrence,canopy}.pid` at depth 1, inside the reaper's depth-3 scan), or its cmdline references a run root. Pinned by `tests/test_reap_pytest_orphans.py` — `test_isolated_stack_run_dir_is_also_protected`, `test_pidfiled_experiment_service_is_protected_not_reaped`, `test_real_mode_kills_the_orphan_but_never_the_protected_service`, `test_stale_pidfile_protects_conservatively` — green on 2026-08-26. The segment-5 supervision remedy (`e2e_cascor_leg_supervise.bash`) stays available as belt-and-braces but is no longer required against the reaper class; blanket killers (`kill_all_pythons.bash` and friends) are still not covered, as the segment-5 note states.

**F-CANOPY-017 — a step-invalid numeric param silently applied a hardcoded default (P1; FIXED canopy#489, verified live segment 12).**
Minted in run `20260811T010700Z` (`statuses.tsv:90`) but never entered this ledger until segment 12 — recorded here to close that gap. HTML5 evaluates `step` relative to `min`, so `#nn-learning-rate-input` (`min=0.0001, step=0.001`) admitted only `0.0001+n*0.001`; no plausible learning rate was on that grid, an edit therefore delivered Dash `None`, and `_apply_parameters_handler` substituted `DEFAULT_LEARNING_RATE`. Live instance: `/api/state` 0.0789 → user types 0.0733 → POSTs 0.01. A DOM sweep found 7 of 22 sidebar number inputs whose own seeded value was already `stepMismatch`. **FIXED** by juniper-canopy#489 (`d11bfcd`, 2026-08-14), which cites the finding by name: float params now use `step="any"`, integer params `step=1`, and a `None` numeric State refuses the apply and names the offending fields instead of substituting a default. **Verified live in segment 12** — all 20 sidebar numeric inputs report `validity.valid=true` / `stepMismatch=false`, and the finding's own 0.0733 instance now commits. Consequence: the matrix's `AUTO-API` class for the sidebar numeric rows is stale (see §1.1).

**F-CANOPY-018 — `params-status` has two writers, so the apply toast is always overwritten (P2, OPEN).**
Minted in run `20260811T010700Z` (`statuses.tsv:88`, W3-08) but never entered this ledger until segment 12. `params-status.children` is written both by `apply_parameters` (the toast, via `_compose_apply_toast` `:7057`) and by `track_param_changes` (`:4385-4389`), which takes `applied-params-store` as an Input — so a successful apply re-fires the tracker, which overwrites the toast. **Segment 12 sharpened it:** the toast *is* rendered (`Parameters applied` observed at t=1800 ms) and survives **~900 ms** before being replaced by `⚠️ Unsaved changes`; the earlier "never the success toast" reading was a sampling artifact. Also: after a successful apply the form never returns to clean until a page reload. Matrix row C2.9-05 **FAIL**.

> **CORRECTED + FIX AUTHORED (2026-08-27, `juniper-canopy#533`; CI green, NOT merged — entry stays OPEN).**
> **"Two writers" is not the driver.** The tracker's clean path already returns `no_update` and leaves the
> toast alone. The real cause is that the form never *compares* clean after an apply: **three** keys sit in
> the dirty-comparison set that `_apply_parameters_handler`'s payload deliberately does not carry, so
> `applied.get(key)` is `None` against a real widget value and the dirty check latches True for the rest of
> the session — which is also exactly why "the form never returns to clean until a page reload" was
> observed, since the MOUNT seed *does* carry them.
>
> All three came from the same `#2b` payload trim: `cn_training_complete` (a read-only status flag) and
> `nn_dataset_elements` / `nn_dataset_noise` (canopy-local — they travel on `/api/stage_dataset`, which the
> Apply button never calls). **The finding named only the toast symptom; the two dataset keys were found by
> a new class-level test, not by inspection.** Comparing them was wrong twice over: it latched the form
> dirty *and* lit Apply for an edit Apply cannot make. `nn_spiral_rotations` / `nn_spiral_number` ride both
> payloads and stay compared. The class-level pin — *every key the tracker compares must be a key the apply
> payload writes* — makes the next `#2b`-style trim fail loudly instead of silently latching.

**F-CANOPY-022 — the "Add Top Tier Candidates" option can never be applied (P1; FIXED juniper-canopy#492 `0460240`).**
canopy emits `value: "top_tier"` (`juniper-canopy/src/frontend/dashboard_manager.py:1471`); cascor accepts only `Literal["top","random","mixed"]` (`juniper-cascor/src/api/models/training.py:159`, `:327`). No translation exists — `_toggle_cn_selection_inputs_handler` (`dashboard_manager.py:6815-6821`) uses `top_tier` only for UI gating and the raw value enters the payload, so Apply returns a Pydantic `literal_error` surfaced as HTTP 502. Control: the sibling `random` arm matches cascor's literal and applies cleanly. cascor's `mixed` has no canopy option at all. Fix direction: map at the payload boundary, or change the option value.

**F-CANOPY-023 — a successful apply is reported as a 502 failure (P1; FIXED juniper-canopy#494 `56ce45f`).**
**CORRECTED after source review — this is a canopy-only defect; the original two-repo framing was wrong.** cascor's `epochs_max` behaviour is deliberate, documented and *not* a defect: C2b / Q1 outcome (c) made it a **derived read-only** value (`epochs_max = output_epochs + effective_iterations * (candidate_epochs + output_epochs)`, `juniper-cascor/src/api/lifecycle/manager.py:1618-1640`), and cascor "accepts [it] at the request boundary (so pre-N5 canopy full-form applies keep succeeding) and report[s it] as `skipped(not-updatable)` by the C2a accounting instead of being applied" (`manager.py:3583-3586`). It is therefore **not silent** — cascor names the key in its skipped partition. My original note called this a cascor defect on the strength of a raw `curl` that only inspected the `data` block; that was an error of method, not of observation.

The real defect is entirely canopy-side, and is an **ordering** bug: `apply_params` runs `_verify_apply_roundtrip(mapped)` at `cascor_service_adapter.py:1325` and returns `{"ok": False, "error": "verification_failed"}` on any divergence — *before* `_extract_cascor_partition(result_data)` at `:1339` parses the very partition that explains the divergence. canopy already knows the answer: that method's own docstring states "`epochs_max` is the standing `not-updatable` case post-C2b". So a key cascor explicitly declined is compared as though it should have changed, and one expected mismatch fails an apply in which every operator edit landed. Trigger is unchanged: only when the sidebar's seeded `nn_max_total_epochs` is stale against cascor's derived `epochs_max`, i.e. after a training run has moved the granular limits; a page reload re-seeds and the next apply succeeds. Fix direction: extract the C2a partition *first* and exclude cascor-declined keys from the verify (plus a static derived-read-only set for backends that do not report one).

**F-CANOPY-024 — the shipped default candidate triple is invalid (P2; FIXED juniper-canopy#493 `71b569b`).**
A fresh dashboard ships S=1, T=1, R=1, so T+R=2≠S and the *first* Apply always fails validation. Both validators agree (identical sentence client-side and from cascor). The user cannot fix it in place because T and R both ship `disabled=True` behind `cn-multi-candidate-checkbox`. Related, not itself a defect: cascor's `candidate_selection` is never seeded into `cn-candidate-selection-radio` (which ships `value=None` by design), so a backend-configured selection is lost across a page load.

**F-CANOPY-025 — the Live Dataset Switch is unreachable: its gate callback never emits (P1; FIXED canopy#514 `5f2e905`, allow arm driven live 2026-08-24 — closure block below; segment 13).**
`live-dataset-switch-button` ships `disabled=True` (`dashboard_manager.py:1279-1280`) and the sole writer of that prop is `gate_live_switch_button` (`:4894-4901`), whose handler returns `not (flags_ok and running)` (`:5732-5741`). The callback **is** registered — `GET /dashboard/_dash-dependencies` lists it among 182 callbacks with output `live-dataset-switch-button.disabled` and inputs `['experimental-flags-store', 'training-status-store']` — and **both inputs are provably correct on the wire**: `_dash-update-component` responses repeatedly carry `{"training-status-store": {"data": {"is_running": true, "phase": "candidate"}}}` and `{"experimental-flags-store": {"data": {"experimental_functions": true}}}`. Yet **zero** responses ever carry `live-dataset-switch-button`, across a 120 s watch (24 samples at 5 s), a full page reload with the response hook armed from before load, and a forced experimental OFF→ON transition. Registered, inputs live, never fires. **Root cause not isolated — fix-phase work** (same disposition as F-CANOPY-016). Blast radius: C2.7-10 FAIL, C2.10-02 / C2.10-03 BLOCKED, and workflow **W7's hot-swap cannot be entered from the UI at all**.
**Why it hid for five segments:** the only prior record of this surface is `W7-step1 PASS` (`reports/e2e/20260810T002233Z/statuses.tsv:63`) — the **deny** arm, *"exp toggle OFF + training running → button disabled"*. A gate that never opens satisfies every should-be-disabled assertion, so the deny arm passing is not evidence the gate works; the **allow** arm had never been driven. Distinct from F-CANOPY-004's server-callback lag: the same page demonstrably updated other surfaces throughout (`network-info-panel` moved from 0 to 6 hidden units), and 120 s exceeds the documented lag while both stores were already correct.

**CLOSED (2026-08-24, canopy#514 `5f2e905`; run `20260825T041134Z`). Root cause was TWO defects.** (1) The gate callback could never win promotion: its `training-status-store` Input is an output the unified-status-bar feeder claims while in flight on every fast tick (the §12.6 claimed-Input race), and the gate is only *useful* during a run — exactly when the feeder's in-flight duty cycle saturates. Measured post-Stage-2: the gate fired at idle mount and **zero times across 80 s of training**; "registered, inputs live, never fires" was promotion starvation, not wiring. Fixed by computing the gate INSIDE `update_unified_status_bar` from the same `/api/status` payload (tuple 10 → 11; the flag rides as `State`, landing within one fast tick; suppressed on no-change). (2) **Every page load clobbered the server-side flag**: the mount reconciliation's *unchanged* toggle write fired the toggle handler — an unchanged write fires every consumer — which POSTed the mount-time value back to cascor, reverting operator changes made since that mount (observed live: a fresh page's echo reset `enabled:true` to `false` within seconds). Fixed with unchanged-write suppression in the reconcile plus an echo guard in the handler (`value == store` ⇒ programmatic write, no POST). **Verified live on the merged content** (tree `c2ec3998` == `5f2e905`): flag ON + run live + fresh mount → `disabled:false` at t+12 s (the arc's first-ever allow-arm observation), the button correctly re-disabling when the run completed; the flag now SURVIVES page attaches; and the enabled button's click opened the Live Switch modal (500×1044) with the full dataset summary — C2.7-10 and C2.10-02 re-scored PASS, W7's UI entry unblocked (C2.10-03, the confirm/swap arm, remains for a W7 drive). Operational note: the flag is cascor-process state — a cascor restart resets it to `false`; that is boot behaviour, not the echo defect.

**F-CANOPY-026 — phase duration is inflated by the host's UTC offset: cascor emits naive LOCAL time, canopy stamps it as UTC (P2, OPEN; segment 15).**
`metrics-panel-phase-duration` read **"Phase Duration: 300m 37s"** on a run that had been alive for 37 seconds. Mechanism, both halves proven in source and live: cascor writes `phase_started_at=datetime.now().isoformat()` — **naive, LOCAL** — at `juniper-cascor/src/api/lifecycle/manager.py:1781` (candidate phase) and `:2326` (output phase); canopy's `_update_phase_duration_handler` (`juniper-canopy/src/frontend/components/metrics_panel.py:1375-1376`) does `if started.tzinfo is None: started = started.replace(tzinfo=timezone.utc)` and then subtracts from `datetime.now(timezone.utc)`. Stamping a local timestamp as UTC shifts it by the host offset, so the displayed elapsed time is inflated by exactly that offset. Measured live: `phase_started_at = 2026-08-20T03:11:17.347900` with the box on CDT (`date +%z` → `-0500`); canopy's arithmetic yields 302m29s where the correct value is 2m29s — **delta exactly 18000 s = 5 h**. The counter ticks correctly at 1 s/s (300m37s → 301m18s across 41 s wall), so this is a pure constant offset, not a broken clock. **Invisible in any UTC-0 environment** (CI, most containers), which is why 14 segments on this dashboard never surfaced it. Matrix row M-METRICS-03 **FAIL**. Fix direction: emit tz-aware UTC from cascor (`datetime.now(timezone.utc).isoformat()`), which also makes canopy's naive branch unreachable; treating a naive value as local on the canopy side would be the compatible stopgap.

> **FIX AUTHORED, BOTH HALVES (2026-08-27; CI green on both, NEITHER merged — entry stays OPEN).**
> `juniper-cascor#594` emits `datetime.now(UTC)` at both phase transitions — the correct fix, since an
> unambiguous instant makes canopy's naive branch unreachable. `juniper-canopy#534` reads a naive value as
> **local** via `astimezone()` — the compat half, for a dashboard pointed at an un-upgraded cascor.
>
> **Mirror symptom, worth recording because it presents as a different bug:** east of UTC the same
> misreading puts `started` in the FUTURE, the handler's `total_seconds < 0` guard fires, and the readout is
> **blank** rather than wrong. Split hosts in different zones cannot be repaired from the canopy side at
> all — hence the upstream fix being the real one.
>
> **Same-class audit (cascor, deliberately out of scope of the fix):** five other naive
> `datetime.now().isoformat()` emissions exist — `monitor.py:302` / `:345` and `manager.py:2651`
> (metrics/event `timestamp` fields) and `snapshot_serializer.py:271` / `:288` (**persisted** snapshot attrs
> `created` / `creation_timestamp`). Same defect class, different blast radius; the snapshot pair writes a
> format the in-flight snapshot-integrity work reads, so they are recorded for their own assessment rather
> than swept in.

**F-CANOPY-027 — a panel's data store is written repeatedly with changing data and NOTHING downstream of it ever runs, so three panels stay frozen at mount defaults through a whole live run (P0/P1; FIXED canopy#507+#509+#511, all rows re-driven live 2026-08-24 — closure block at the end of this entry; found segment 15; ROOT-CAUSED 2026-08-23 — callback starvation under dash-renderer's hard-coded 12-slot concurrency pool, reproduced in a clean room with a control. Read the `ROOT CAUSE (2026-08-23)` block at the end of this entry FIRST: it supersedes the "broken wiring" framing of every block above it, and those blocks are retained only as the refutation record for twenty mechanisms. FIXED — closure block at the entry's end).**
Two panels, identical signature: their data store is demonstrably filled on the wire, and the server-side `@app.callback` renderers that take that store as their sole/primary `Input` never emit a single output.
*Candidate Metrics*: `candidate-metrics-panel-training-state-store` received fresh payloads repeatedly (`{"candidate_pool_status":"Training","candidate_pool_size":40,"top_candidate_id":"31","top_candidate_score":0.181,"second_candidate_id":"11"}`), while `/api/state` carried a full pool (`candidate_pool_size 40`, `candidates_trained 40/40`, `candidate_epoch 351/400`, 40 `all_correlations`). The panel rendered `Inactive` / `Idle` / `0` / "No active candidate pool" / "No candidate data available" / "No pool history yet" for the entire run. `update_status_display`, `update_epoch_progress`, `update_pool_info` (`candidate_metrics_panel.py:251-300`) are plain server-side `@app.callback`s on `Input(-training-state-store,"data")`; **zero** `candidate-metrics-panel-status-badge` outputs across 252 responses / 45 s, and zero again across 200 responses / 49 s on a second, independent trigger path (forcing `visualization-tabs.active_tab` to change rather than riding the interval).
*Decision Boundary*: `decision-boundary-boundary-data` filled 12×/61 s and 22×/60 s (the latter including a direct `decision-boundary-refresh-btn` click), while `decision-boundary-plot` and `-status` emitted **0** outputs and the status stayed `"Status: No network loaded"` — even though `GET /api/decision_boundary?resolution=50` returns a full `xx` meshgrid and cascor reported `current_hidden_units: 7`. `update_boundary_plot` (`decision_boundary.py:172-183`) is likewise a server-side `@app.callback`.
**Ruled out, each explicitly:** instrument truncation (the first probes sliced responses to 3000 chars while the largest real response was **675,891** chars — re-measured with full-text matching); buffer overflow (the first counter capped at 250 entries and silently shifted — replaced with uncapped counters); duplicate component ids (all `count == 1`); "the store isn't in the layout" (`dcc.Store`/`dcc.Interval` render no DOM at all — the *working* `metrics-panel-metrics-store` and `fast-update-interval` also return 0 nodes, so DOM absence proves nothing); a server-side exception (canopy log clean — the only ERRORs are pre-run `No network created` lines); clientside callbacks (grep for `clientside_callback` in both panel files returns nothing); and too-short settle windows (49 s, 121 s, and 120 s watches, well past F-CANOPY-004's documented 30 s–minutes).
**Blast radius / why it matters for scoring:** M-CANDIDATES-07 **FAIL**, M-CANDIDATES-09/-10/-11 and M-BOUNDARIES-02/-03 **BLOCKED**, M-BOUNDARIES-04 **FAIL**, M-BOUNDARIES-01 half-failed. It also means **M-CANDIDATES-01/-02/-03/-04/-06 carry `PASS` recorded against the panel's mount DEFAULTS** — the same negative-arm trap that hid F-CANOPY-025 for five segments (`-02`'s and `-03`'s stated expectations literally name the defaults `"Idle"` and `"0"`). Those five rows should be treated as unproven and re-driven once this is fixed.

**THIRD INSTANCE (segment 16) — the Dataset View plotter.** Same signature, now on a third panel:
`dataset-plotter-dataset-store` filled **13 times in 90 s** with real data
(`num_samples 1000, num_features 2, num_classes 2, train 800 / test 200`, plus `inputs` arrays), while the
6-output consumer (`dataset_plotter.py:496-532`, which writes both plots AND all four stat tiles) emitted
**ZERO** outputs across **409** `_dash-update-component` responses. The tiles sat at `0 / 0 / 0 / N/A` and both
plots at `1102x0` with no traces. Full-text response matching, uncapped counters, tab active throughout.
Rows: M-DATASET-13 / -15 / -16 **FAIL**.
**Two more mechanisms tested and REFUTED here** (recorded so nobody re-runs them): (i) *"a callback Input is
missing from the rendered tree, so Dash cannot dispatch it"* — after a 90 s settle all four sequence selectors
among the nine Inputs **are** rendered; (ii) *"the component is absent from the served layout"* — every Input
is present in `/dashboard/_dash-layout`. Also learned the hard way: this panel **rebuilds continuously**, so
`getElementById` against it is racy and a short settle produces false "absent" readings (one nearly became a
filed defect for `dataset-plotter-split-selector`, which renders fine). Root cause still NOT isolated.


**PHASE 2 INVESTIGATION (2026-08-22) — nine more mechanisms refuted, characterisation corrected, root cause STILL NOT isolated.**
The symptom reproduces cleanly and is not a measurement artifact: with the Candidates tab active and a live run, the backend advanced `candidate_epoch` **1 → 101** at a steady `candidate_pool_size 40` while the panel held a **single** DOM state for 180 s (`badge:""`, `phase:"Idle"`, `pool:"0"`).

**The old characterisation was wrong in two ways, and both matter for whoever fixes this:**
1. *"The consumers never fire."* They do. With a fetch hook installed via `add_init_script` — i.e. from the first byte, which every earlier probe was too late to see — `dataset-plotter-scatter-plot` dispatched at ~39.8 s carrying `changedPropIds='dataset-plotter-dataset-store.data,theme-state.data,…'`, and the candidate consumers dispatched once at mount in a run where their tab was inactive. **They are wired and they can fire; they fire at mount and then effectively stop.**
2. *"They hang."* They do not. When they fire they **complete**: 0.6 s for the three candidate consumers, 2.6 s for `dataset-plotter-scatter-plot`, against 0.3–1.8 s for the working metrics consumers. Nothing sits in flight.

**The precise contradiction now on the table.** On the Candidates tab with a live run, in one 90 s window: the writer `candidate-metrics-panel-training-state-store.data` dispatched **32** times, and **every one of its five consumers dispatched 0 times** — including `candidate-metrics-panel-pool-history-store`, whose output is just another store and does no rendering at all. A separate 90 s window measured the store's payloads directly: **29 dispatches, 29 carried a payload, 27 of them differed from the previous value.** So the data genuinely changes and nothing downstream of it ever runs. The structurally identical metrics chain dispatched 8× in the same window.

**Refuted this phase (each with evidence; do not re-run these):**
- *not registered* — all 182 callbacks in `app.callback_map`; the five candidate consumers present with the right inputs.
- *component missing from the layout* — every implicated component reachable from `app.layout`; **zero** callback outputs whose component is absent.
- *invisible to the browser* — the served `/dashboard/_dash-dependencies` has 182 entries (== `callback_map`), and an **exact** `id ==` scan finds all five consumers carrying `candidate-metrics-panel-training-state-store` as an Input.
- *duplicate component ids* — 461 id declarations, 461 distinct, **0** duplicates. (This mattered: both earlier duplicate checks were blind here — segment 15 counted DOM nodes, and a `dcc.Store` renders none; the layout audit first used a `set()`, which discards multiplicity by construction.)
- *mount order / late-mounted panels are never wired* — falsified by its own prediction. The working metrics chain was unmounted and remounted by a tab round-trip and **kept working** (5× before, 2× after, DOM value advancing `Best Corr 0.1490 → 0.1685`).
- *a client-side exception stops propagation* — **0** console errors and **0** `pageerror`s across every window, with full capture (not just error/warning).
- *the callback hangs* — see above; all complete in ≤ 2.6 s.
- *the store's value never actually changes* — 27 of 29 payloads differ.
- *rendering-output callbacks specifically are broken* — the store-output consumer is equally dead, so it is not about figures or expensive renders.
- *writer/consumer id mismatch* — writer output is `'candidate-metrics-panel-training-state-store.data'` and every consumer input id is `'candidate-metrics-panel-training-state-store'`; byte-identical.
- *different registration path* — both panels go through the same `DashboardManager.register_component()` → `component.register_callbacks(self.app)` (`dashboard_manager.py:7434-7444`, called for metrics at `:583` and candidate at `:584`). *(The absence of its `"Registered component: …"` INFO lines from the canopy log is a logger-timing artifact, not evidence of a second path.)*
- *storage_type difference* — both are plain `dcc.Store(id=…, data={})` (`candidate_metrics_panel.py:212`, `metrics_panel.py:539`).

**Where the remaining hypothesis space is.** Everything from the layout through the served dependency graph is provably correct, and the server side is provably reachable, so the break is in the **client's change-propagation for these specific store components**: Dash applies the writer's response and does not mark the store's `data` as changed for its observers. The two concrete next steps are (a) read Dash's client-side redux/`paths` state directly for the store and compare against the working metrics store, and (b) bisect by adding a *temporary* trivial consumer of the same store in canopy source — if a brand-new callback on that store also never fires, the defect is in the component instance rather than in any of the five existing consumers.

**Tooling.** Eleven reusable probes shipped under `util/ad-hoc/e2e_f027_*.py` — callback-registry audit, precise producer/consumer dep graph, layout-presence audit, `_dash-dependencies` comparison, duplicate-id walker, dispatch probe (reads each request's `output` field, which names the callback rather than its inputs), store-value delta, mount-order discriminator, from-first-byte mount-dispatch capture, in-flight/duration tracker, and a DOM watcher.


**CLIENT-STATE INVESTIGATION (2026-08-23) — localised to the prop, still not root-caused.**
Next-step (a) from the previous block was executed: reach Dash's client-side redux store through the React
fiber on `#react-entry-point` and inspect `paths`, `layout` and the callback queues directly.

**The decisive measurement.** The dead store's **client-side `data` prop never leaves its declared default
`{}`** — sampled every 400 ms for 90 s, while **23 wire payloads arrived, all 23 carrying data**
(arrival times 7.9 s, 19.8 s, 25.0 s … 87.5 s). Not one momentary flip. So the failure is neither
"the consumer does not fire" nor "the value does not change": **Dash receives a well-formed response
carrying the store's new `data` and never applies it to the client's copy.** The consumers are then behaving
correctly — from the client's point of view their Input has never changed from `{}`.

That is a materially tighter localisation than "client-side propagation": the break is *between* receiving the
response and writing the prop.

**And the obvious explanations for THAT are also refuted:**
- *stale or wrong `paths` entry* — the entry resolves into the live layout to a node whose `props.id` is
  exactly `candidate-metrics-panel-training-state-store` and whose `type` is `Store`. Verified for all four
  watched components; every one matches. `paths` holds 461 entries.
- *the component is unknown to the client* — it is in `paths`, and redux dispatches **do** name it: 102
  actions in 90 s (56 `Callbacks.Aggregate`, 24 `LOADING`, 22 `LOADED`) against 305 for the working store.
  Dash is actively tracking it; it just never lands the value.
- *the tab-bar rebuild wipes it* — `visualization-tabs.children` (whose sole Input is `model-class-store.data`)
  dispatched **once** in 90 s, not continuously.
- *`RESET_COMPONENT_STATE` wipes it* — it fires a great deal (below) but every sampled payload targets
  `…/children/**12**/…`, i.e. the **Cassandra** tab subtree, while the dead store lives under
  `…/children/**1**/…`. Wrong subtree; not the cause here.

**Where to resume.** The remaining question is narrow and mechanical: why does Dash's client accept a response
naming this component and not dispatch a prop write for it, when it does exactly that for
`metrics-panel-training-state-store` in the same window? The next probe should capture the *full* action
sequence around one specific payload arrival for both stores side by side (the trace tool already timestamps
both) and diff them — the working store's extra ~200 `Callbacks.Aggregate` actions are the obvious place to
look for the branch that is being skipped.


**A/B INJECTION RESULT (2026-08-23) — the defect is the client's runtime OBSERVER wiring, and the previous localisation was one layer off.**

*Correction first.* The previous block concluded "the break is between receiving the response and writing the
prop." That is **wrong**, and the correction matters: writing the prop does not help either.

**The A/B.** Using the component's own Dash-supplied `setProps({data: …})` — reached through the React fiber —
a fresh value was injected directly into each store, with a control confirming in redux that the prop really
changed (`{"candidate_pool_status":"PROBE-INJECTED",…}`). Identical probe, identical mechanism, opposite
outcomes:

| store | prop written? | consumers |
|---|---|---|
| `metrics-panel-training-state-store` (working) | yes, verified in redux | **all three FIRED**, 4 dispatches each |
| `candidate-metrics-panel-training-state-store` (dead) | yes, verified in redux | **all three SILENT**, 0 dispatches across 220 |

**What that establishes.** Dash's client does not treat the dead store as an observable callback Input at
runtime — even though its five consumers are in the served `/dashboard/_dash-dependencies` with the exact
input id, `paths` resolves it to the correct `Store` component, and the prop is writable. The unapplied server
response and the never-firing consumers are therefore **two faces of one defect**, not two defects: the
component is absent from the client's runtime observer graph, so Dash neither routes responses to it nor
reacts when its value changes.

**Also refuted this pass:**
- *Dash takes a different action branch for the two stores* — the redux action-type sequence immediately after
  a data-carrying response is indistinguishable between them
  (`LOADED×N → Callbacks.Aggregate → function → SET_PATHS …` in both).
- *"the prop is written then reverted inside my sampling gap"* — replaced 400 ms polling with a
  `store.subscribe` observer that sees **every** dispatch: across **5974 state changes** the dead prop held
  exactly one value, `{}`. The earlier sampled conclusion was right, and is now proven without sampling.

**Where to resume.** The question is now specific enough to answer by reading Dash's renderer: what makes a
component present in `paths` and in the dependency list nevertheless absent from the runtime observer
registry? The one structural difference the path data actually supports is tab position: the working panel is the
**default/first** tab (its store path has no tab index after the tabs container), while every dead panel sits
at an indexed position under it -- candidate at `children/1`, boundary at `children/4`, dataset at
`children/5`. All four are children of `visualization-tabs`, which is rebuilt by the model-class callback, so
the suspect is the renderer's observer registration for tab content that is *not* the initially-active pane,
and how that interacts with the rebuild and with `SET_PATHS`. Note this is NOT the already-refuted
mount-order hypothesis: the working chain survived an unmount/remount round-trip, so "mounts later" is not
sufficient -- "is never the initially-active pane" is the narrower property still standing. A fix attempt
should re-run
`util/ad-hoc/e2e_f027_setprops_probe.py` — that probe is now the fastest yes/no test of whether wiring is
restored, taking about a minute rather than a full driving pass.


**ROOT CAUSE (2026-08-23) — CALLBACK STARVATION under dash-renderer's hard-coded 12-slot pool. Reproduced in a clean room with a control; the "wiring" framing above is WRONG and is superseded by this block.**

*The tab-position property does not survive either.* "Is never the initially-active pane" was the last
standing hypothesis. It is refuted: in the clean-room reproduction below the **initially-active pane dies
too**, and in canopy the working panel is a winner of a race, not a beneficiary of its position.

**What it actually is.** Nothing is mis-wired. Every consumer is registered, resolvable and *queued* — and
never picked. dash-renderer's prioritized-callback executor
(`dash_renderer.dev.js:2846`, dash 4.2.0 — the unminified bundle ships in the env) promotes work out of
`callbacks.prioritized` under a **hard-coded, non-configurable cap of 12**:

```js
available = Math.max(0, 12 - executing.length - watched.length);
pickedSyncCallbacks = syncCallbacks.slice(0, available);
```

When `executing + watched >= 12`, `available == 0` and **nothing** leaves `prioritized` on that pass.
Separately, `getReadyCallbacks` refuses to promote a `requested` callback while any of its Inputs is an
output claimed by a *still-pending* callback. Put together: **a poller whose completion time exceeds its own
trigger period is never absent from the pending set, so every consumer of its output starves forever.**

**Measured on the live isolated stack** (`e2e_f027_slots.py`, subscribe-not-sample, 5020 state changes over
60 s on the Candidates tab):

| metric | value |
|---|---|
| pool FULL (`available == 0`) | **4195 / 5020 samples = 83.6 %** |
| `available <= 1` | 97.1 % |
| `prioritized` queue length | min 0, **max 36** (3× the pool) |
| callbacks completed, whole dashboard | 224 in 60 s |
| interval-driven server callbacks registered | **26** (14 `fast-update-interval`, 9 `slow-update-interval`, 3 per-panel) |

26 perpetual pollers contend for 12 slots. Arbitration is `sortPriority` → `getPriority`
(`dash_renderer.dev.js:1592`), a base-36 string of the callback's downstream chain depth and breadth sorted
**descending**, so a *terminal* render callback — one whose outputs feed nothing further, which is exactly
what `update_status_display` / `update_pool_info` / `update_boundary_plot` / the dataset stat tiles are —
scores the minimum and loses every arbitration while the pool is contended. Deterministic ordering means the
same losers lose every time, which is why the symptom looks like broken wiring rather than jitter.

**Clean-room reproduction WITH A CONTROL** (`util/ad-hoc/e2e_f027_cleanroom.py`, same dash 4.2.0 / dbc 2.0.4,
`dbc.Tabs` + per-pane `Interval → Store → Div`, plus canopy's one-shot `visualization-tabs.children`
rebuild). Only the writer's completion time was varied:

| writer work | interval | outcome |
|---|---|---|
| 0.0 s | 500 ms | 5 / 5 panes **LIVE** |
| 0.2 s | 500 ms | 5 / 5 panes **LIVE** |
| 1.0 s | 500 ms | **0 / 5 panes live — all frozen at mount defaults, including the initially-active pane** |

The dead arm reproduces the exact F-CANOPY-027 signature: store filled repeatedly on the wire, consumers
never fire, zero console errors, wiring perfect. The threshold is completion-time-vs-trigger-period and
nothing else. The earlier 5-pane / no-delay run is the reason a first clean-room attempt did **not**
reproduce: 10 fast callbacks never contend for the 12 slots.

**Two more mechanisms refuted this pass, both by direct experiment (do not re-run):**
- *the consumers are missing from the client's derived observer index* — `e2e_f027_inputmap.py` reads
  `state.graphs.inputMap` (the client-DERIVED index, **not** the served `_dash-dependencies` that earlier
  probes checked) and dash-renderer's second gate. All three dead stores are in `inputMap` with `props=['data']`,
  and **every** consumer output resolves in `paths` — 0 callbacks dropped. Both gates pass.
- *`visualization-tabs.active_tab` as an Input poisons the writer* — all three dead writers take it as an
  `Input` and `no_update` off-tab, while the one working writer (`metrics_panel.py:608`) deliberately takes
  only its interval, with a comment naming this hazard as "the I-1 starvation". Plausible, and **wrong**:
  moving it to `State` in `candidate_metrics_panel.py`, confirmed applied in the served graph
  (`state: [('visualization-tabs','active_tab')]`), left the panel exactly as dead. Reverted.

**Why this subsumes other findings.** F-CANOPY-004 ("server-side Dash callbacks lag 30 s–minutes behind
reality during a live run") is the same saturation seen from the outside, not an independent defect. The
three F-CANOPY-027 panels are the starvation losers; the metrics panel is a winner.

**Fix direction (design needed — this is architectural, not a one-line fix).** The lever is the *number of
concurrently pending callbacks*, which must sit below 12. The largest single win: canopy's tab-gated pollers
are gated **server-side** — `_update_dataset_store_handler` / `_update_boundary_store_handler` /
`fetch_training_state` all return `dash.no_update` when their tab is inactive, but the callback has already
made a full round-trip and consumed a slot to decide that. Gating on the **client** instead (drive each
`dcc.Interval.disabled` from `visualization-tabs.active_tab` via a clientside callback) stops the off-tab
pollers from firing at all and should return the pool to the uncontended regime the clean-room control
demonstrates. Raising the cap is not an option — it is a literal `12` in the renderer bundle.

**Verification loop.** `e2e_f027_slots.py` is the primary instrument: a fix works iff `available == 0` drops
well below 83.6 % and `prioritized` stops backing up. `e2e_f027_setprops_probe.py` remains the ~1-minute
yes/no on a single panel, but note it answers "did this panel win a slot", not "is the wiring restored".

**STAGE 1 + 3 SHIPPED (2026-08-23) — the three panels are ALIVE; the pool is better but still contended.**
Design of record: [`JUNIPER_2026-08-23_JUNIPER-CANOPY_CALLBACK-STARVATION-REMEDIATION-DESIGN.md`](JUNIPER_2026-08-23_JUNIPER-CANOPY_CALLBACK-STARVATION-REMEDIATION-DESIGN.md).
Shipped as juniper-canopy#507 (gating) and #508 (completion + budget guard).

**Behavioural close, verified on all three panels.** A/B injection through each component's own
Dash-supplied `setProps`, the same probe that measured **0** consumer dispatches across 220 before:

| panel | consumer dispatches | DOM |
|---|---|---|
| Candidate Metrics | 0 → **2** each | `''` → `Inactive` / `No active candidate pool` |
| Dataset View | **3 / 3 / 4** | changed ✓ |
| Decision Boundary | **3 / 3** | `No network loaded` → `Displaying decision boundary` |

The `''` → `Inactive` transition is the tell: the panel had been showing the *static layout default*
because `update_status_display` had never executed once, not even at mount.

**Pool measurements** (`e2e_f027_slots.py`, 60 s, Candidates tab):

| metric | baseline | after #507 | after #508 | design §7.1 target |
|---|---|---|---|---|
| pool full (`available == 0`) | 83.6 % | 63.6 % | **61.4 %** | < 20 % — **NOT met** |
| `prioritized` backlog, max | 36 | 37 | **23** | < 12 — **NOT met** |
| completions / 60 s | 224 | 499 | 449 | > 500 — met at #507 |

Worst-case concurrent perpetual pollers, censused from the built app: **14 → 12** against a cap of 12.

**What shipped.** Four `disabled=True` per-tab `dcc.Interval` lanes outside `visualization-tabs` (so the
A1-iii-b1 children rebuild cannot reset them); the CAN-000 apply clamp and the new tab gate **fused into
one clientside callback** (Dash permits one un-duplicated writer per prop); five panel-owned intervals
gated in place; a dead poller removed (`fetch_network_stats` wrote a store with no consumer anywhere in
`src/` — tracked as F-CANOPY-034); a redundant tab-bar rebuild suppressed (`hydrate_model_class` no longer
rewrites the store with an identical value); and a **poller-budget guard** in canopy's suite that fails if
worst-case concurrency exceeds 12 or if a panel-scoped poller rides an ungateable shared lane.

**A SECOND MECHANISM, found during implementation — this is what Stage 2 must address.** Interval gating
silences interval-driven pollers and nothing else. Panel work chained off a **global store** re-runs on
every tab regardless: `update_snapshots_table` takes `Input("dataset-swap-events-store", "data")`, which
`poll_dataset_swap_events` rewrites every 5 s, so the snapshots panel re-renders on every tab no matter
what its own interval does. Network Editor and Replay show the same shape. The cheap lever is the one
already applied to `hydrate_model_class` — **do not rewrite a store with identical content**, because an
unchanged write still fires every downstream consumer — but applying it across the ~10 remaining global
pollers is Stage 2.

**Also learned: the AST census under-reports.** `canopy_poller_inventory.py` resolves 151 of the app's 182
callbacks (pattern-matching and clientside registrations are invisible to a static pass), and it missed two
real panel-scoped pollers — `network-editor-panel-fsm-poll` (2 s, every tab) and `update_network_graph`
(the 8-output topology renderer, forced at 1 Hz from every tab). Censusing `app._callback_list` on the
**built** app finds them. Use the built-app census for anything load-bearing; the AST pass is for a quick
read only.

**Not closed.** F-CANOPY-027's symptom is closed on all three panels and F-CANOPY-004's lag is materially
improved (2.2× throughput), but neither should be marked `fixed` until Stage 2 brings saturation down and
the matrix rows are re-driven against a live training run.

**CORRECTION (2026-08-24, from the live re-drive): "closed on all three panels" was an attach-time claim,
and it does not hold in steady state for the Decision Boundary panel.** The setProps A/B and the DOM
transitions above were measured on quiet pages / at attach. Under the live steady state the panel's
plot-render callback fires once at mount and is never promoted again — request-capture proof: 80
boundary-data fills at ~1/s against exactly 1 plot render in 115 s, a session-long empty
`"No network loaded"` figure, and zero re-renders for slider / confidence / refresh interactions. Cause:
both of the panel's feeders are fast-lane ~1 s pollers whose round-trips cover their period, so the
downstream render's Inputs are permanently claimed (the F-CANOPY-036 promotion race, generalized). The
candidates and dataset lanes ARE closed live (see the 2026-08-24 re-drive section). Stage 2 gains a third
lever: the boundaries chain specifically.

**CLOSED (2026-08-24, Stage 2 = canopy#511 `60f9737`).** All three levers shipped (global lane 10 → 6
pollers, no-op-write suppression, boundaries tabpoll → SLOW + feeder suppression) and every panel in this
finding's blast radius is verified live on the merged build: candidates + dataset lanes (run
`20260824T080426Z`), and the boundaries lane on `60f9737` (run `20260824T192748Z`) — M-BOUNDARIES-01/-02/
-03/-04 all `PASS (re-validated @ 60f9737)`, -02/-03 by direct `changedPropIds` causation. Saturation
(§7.1 protocol): pool-full 83.6 % → **25.5 % idle / 35.3 % under live training**, completions 224 →
**778/60 s idle**, backlog now DRAINS to 0 (was held at 23+), and the probe's starving-in-`prioritized`
list is **empty**. The rows that remain red in these panels are owned by their own findings —
M-CANDIDATES-07 (F-CANOPY-035), -09/-10/-11 (F-CANOPY-036) — not by this one. F-CANOPY-004 stays OPEN
(residual lag: fresh-session population 20-40 s; render latencies 3-16 s), materially improved.

**F-CANOPY-034 — `metrics-panel-network-stats-store` is now written by nothing and read by nothing (P2, OPEN; found while fixing F-CANOPY-027).**
The store was fed by a `fetch_network_stats` poller that GET `/api/network/stats` every 5 s — and **no callback
anywhere in `src/` took it as an `Input` or a `State`** (verified repo-wide; the only other reference was its own
`dcc.Store` declaration). Under dash-renderer's 12-slot cap that was a permanently-occupied slot bought for
nothing, so juniper-canopy#507 removed the poller. The `dcc.Store` was deliberately RETAINED there: it is inert,
it is pinned by the layout regression snapshot `src/tests/regression/snapshots/metrics_panel.txt`, and dropping
it in the same PR would have mixed a snapshot rewrite into a load fix. Remaining work is small and purely
tidying: delete `dcc.Store(id=f"{self.component_id}-network-stats-store")` (`metrics_panel.py:538`), regenerate
that snapshot, and decide whether `_fetch_network_stats_handler` (`metrics_panel.py:1182`, still covered by five
unit tests in `tests/unit/frontend/test_metrics_panel_handlers.py`) should go with it. A tripwire already exists:
`tests/unit/frontend/test_poll_gating.py::TestDeadPollerRemoved::test_network_stats_store_still_has_no_consumer`
fails if anyone wires a consumer without restoring a writer.

**F-CANOPY-035 — the candidate loss plot reads `epochs`/`losses`/`phases` off the training-state store, keys `/api/state` never provides in any lane, so the plot is structurally empty (P1, OPEN; found during the 2026-08-24 live re-drive; fix MERGED as canopy#524 `f20602cb`, M-CANDIDATES-07 re-drive owed).**

> **WHY IT IS STILL EMPTY AFTER THE MERGED FIX — MEASURED 2026-08-29.** canopy#524 corrected the key
> shape, and the plot is still empty, because the store it reads is empty for a second and independent
> reason. A server-side probe inside `_update_metrics_store_handler` (79 samples, 140 s, BOTH tabs)
> shows the CLIENT's copy of `metrics-panel-metrics-store` pinned at its shipped empty default
> (`cur_type=list cur_len=2`, i.e. `[]`) on **every** sample, while the server offers **155,392 B** on
> every tick. This entry's own earlier observation — "globally empty (`len 0`) on BOTH tabs" — was
> made with the client-side `storeprobe` this arc later ruled inadmissible; it is now established from
> the server side, where the value Dash actually delivers as `State` is visible.
>
> **So the INCONCLUSIVE / F-004-congestion attribution on this entry is superseded.** It was not an
> instrument artefact and not congestion: the store really is empty, always, and the panel is
> rendering exactly what it is given. The remaining question is why the write never lands — see
> F-CANOPY-038's measured block and F-CANOPY-039. **M-CANDIDATES-07 cannot pass until that is fixed**,
> so the owed re-drive is blocked rather than merely outstanding.
`_create_candidate_loss_figure` (`candidate_metrics_panel.py:570-577`) filters `state.epochs`/`state.losses`/`state.phases` for entries whose phase contains `"candidate"`; the store it reads is filled by `_fetch_training_state` → GET `/api/state` (`:414`). But that route (`main.py:1129`) serves `TrainingState.get_state()`, and `TrainingState._STATE_FIELDS` (`training_monitor.py:232-264`) contains **none of those keys** — the demo branch augments only `nn_*`/`cn_*`/convergence params, so no lane ever provides them. Confirmed live mid-candidate-phase 2026-08-24: `/api/state` carried `candidate_pool_size 40`, `candidate_epoch 201/400`, `candidates_trained 40/40`, `all_correlations[40]` — and no `epochs`/`losses`/`phases`. This is **not** starvation: in the same session the same store's other consumers (badge, phase, pool size, progress bar, pool info) all rendered live candidate-phase values post-#507/#509, while the figure's only reachable render is the `create_empty_plot("No candidate data available")` placeholder (`:567`/`:575`/`:605`). The data exists in-system — cascor `/v1/metrics/history` returned 4,106 `phase:"candidate"` per-epoch loss entries (of 4,909 total) for the same run, and canopy already proxies it at `/api/metrics/history` — the panel is simply wired to the wrong producer. Fix is canopy-side: source the candidate-loss figure from the metrics-history data (or merge those keys into the store fetch) and drop the dead three-key read. Matrix row M-CANDIDATES-07 re-scored FAIL with its cause re-attributed from F-CANOPY-027 to this finding. Same consumer-reads-keys-the-producer-never-emits class as F-CANOPY-011/-013.

**FIX MERGED (2026-08-26, canopy#524 `f20602cb`; M-CANDIDATES-07 re-drive owed).** The loss-plot callback takes the dashboard's existing shared `metrics-panel-metrics-store` (fed by the liveness-gated `/api/metrics/history` poll and the WS append path) as a third Input — no new poller, the F-CANOPY-027 rule — and `_candidate_series_from_history` derives the three series from its candidate-phase entries (the nested `{epoch, metrics.loss, phase}` shape both the demo backend and the cascor adapter's `_to_dashboard_metric` produce; flat `loss`/`train_loss` + `cascade_phase` tolerated). The figure builder is untouched and the state-store shape stays a fallback, so every existing figure test holds. `src/tests/unit/frontend/test_f035_candidate_loss_from_history.py` (15 tests) pins the producer contract (`TrainingState._STATE_FIELDS` has none of the three keys; the callback declares the shared store), the series adapter and the rendered `Candidate Training` trace from a real `/api/state`-shaped payload plus history; the module does not import on the parent.

**LIVE RE-DRIVE INCONCLUSIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f035,f035probe,storeprobe`; stays OPEN).** The adapter is provably correct — `/api/metrics/history` held 3216 candidate-phase entries in the exact `{epoch, metrics.loss, phase}` shape, and a direct simulation of `_candidate_series_from_history` kept 99/99 from the last-100 window. But the shared `metrics-panel-metrics-store` was **empty** (`len 0`) on BOTH the Training Metrics and Candidate Metrics tabs post-run, and the **main** metrics loss plot was empty too — the store never populated from the available history (the liveness-gated fast-interval poll starved/demoted throughout the congested run; F-CANOPY-004 territory). So M-CANDIDATES-07's live render cannot be exercised while the upstream store is empty — this is the instrument/F-004 condition, not an F-035 regression. The fix stands on its unit suite + the adapter simulation; the live render is blocked on the same store-population/staleness that F-CANOPY-004 tracks. Row stays as-is pending an F-004 render.

> **THE OWED RE-DRIVE IS DONE (2026-09-05) — M-CANDIDATES-07 is FAIL, and the blocker is now measured
> rather than inferred: the store is WRITTEN and never applied.**
>
> Driven against canopy main **`94220f0`** with
> `util/ad-hoc/2026-09-04_f035_candidate_loss_redrive.py`. This re-drive exists separately from
> `e2e_p1wave_redrive.py --step f035` for one reason: the 2026-08-26 attempt used the client-side
> `storeprobe` this arc later ruled **inadmissible** (it read `None` for every store on the app,
> including one whose heatmap was visibly rendering, and reported that as "empty"). This one uses the
> repaired reader (`state.paths.strs`) and **refuses to score an unreadable store as an empty one**.
>
> | measurement | result |
> |---|---|
> | server, the handler's own endpoint | `{"history": [...]}`, **99 of 100 rows `phase:"candidate"`** |
> | `ws-liveness-store` | `{'metrics_live': False, 'state_live': False}` — the WS demotion gate is **open**, so the REST branch is the one running |
> | **writes to `metrics-panel-metrics-store`, parsed off `/_dash-update-component`** | **17 writes of 500 rows** in 30 s; `omitted=0`, `unparsed=0` *(correct for the window — but the `.json` archived beside it reads 46/`unparsed=7`; see the census-window correction below)* |
> | store read **immediately before** those writes | `ok` via `paths.strs`, `len=0` |
> | store read **immediately after** those writes | `ok` via `paths.strs`, **`len=0`** |
> | `candidate-metrics-panel-loss-plot` | present, **zero traces**, after a 45 s budget |
>
> **The server sends 500 rows seventeen times and the client's copy stays empty.** That is the
> **F-CANOPY-039 signature** — one store id, two different values — on a *different* store, after
> canopy#549 fixed it for the topology store (which is now healthy: M-TOPOLOGY re-drives 16 PASS).
>
> **canopy#524's adapter is correct and unreachable.** The panel renders exactly what it is given. So
> this finding's own fix stands, and its row stays FAIL on an upstream cause.
>
> **Two hypotheses ruled OUT by measurement, not argument.**
>
> - *The WS demotion gate is engaged.* `_update_metrics_store_handler` returns `no_update` only
>   `if ws_live and not full_fetch`, and `ws-liveness-store` reads `metrics_live: False`.
> - *The callback is starved, silent, or writing empty.* It is none of those: every one of the 17
>   captured writes carried 500 rows. An earlier count in this session reported only "13 of 74
>   responses naming the store", which established that the callback was *speaking* and **nothing about
>   whether a value landed** — a `no_update` for an output can still name it in the body. Parsing the
>   bodies is what separated the two.
>
> **A THIRD hypothesis was ruled out by the log, and a fourth was NOT ruled out by it — the difference
> matters.** The handler warns on both its failure paths (`Metrics history API returned <code>` and
> `Failed to fetch metrics from API`). The instance log carries **zero** of either, so the fetch is
> neither erroring nor non-OK. It also carries zero `Fetched N metrics from …` debug lines — but the
> log has **zero DEBUG lines at all**, so that absence says nothing about whether the handler ran. An
> instrument that cannot produce a non-zero answer has not measured anything.
>
> **WHAT IS NOT ESTABLISHED, and the instrument that cannot establish it.** Whether the reader and the
> writer are addressing *the same store instance*. The duplicate-instance hypothesis is exactly what
> F-CANOPY-039's investigation chased, and this arc's own note records the limitation:
> **"`dcc.Store` has no DOM; `paths.strs` hides duplicates"** (`util/ad-hoc/README.md`). The reader used
> here goes through `paths.strs`. **It therefore cannot answer the question its own result raises.** The
> next instruments are the ones the arc already built for this store —
> `util/ad-hoc/e2e_f039_metrics_store_soak.py` and `e2e_f039_duplicate_store_probe.py` — and note that
> the latter's `exit 1` is "could not run", not a verdict.
>
> **A correction to an earlier statement in this session.** The server check was first run at
> `?limit=100`, the code's default `window_size`; the live display-mode store asks for **500**, which is
> what the captured writes carry. The candidate-phase content holds at either limit, so no conclusion
> moves — but the figure to quote is 500.
>
> **Matrix effect: none.** M-CANDIDATES-07 was already FAIL. What changes is the *basis* — from
> "blocked on an upstream store that is empty for reasons attributed to F-CANOPY-038/-039" to a measured
> written-and-not-applied, with the duplicate-instance question named and its instrument identified. The
> row's "re-drive owed" state is closed.
>
> Evidence: `reports/e2e-canopy-2026-09-02/transcripts/2026-09-05_f035_candidate_redrive.{txt,json}`
> (bracketing reads + write census) and `…/2026-09-04_f035_candidate_redrive.{txt,json}` (the first
> pass, kept because its weaker mention-count is the contrast that motivated parsing the bodies).

---

#### 2026-09-05, later — the open question is ANSWERED, the warning is DISCHARGED, and one instrument defect is repaired

The block above closed with a question its own reader could not answer — *are the reader and the
writer addressing the same store instance?* — and the F-039 topoprobe's report closed with a warning
that had to be discharged before its verdict could be read. Both are now settled, and settling them
turned up a defect in the re-drive instrument itself.

**What was SERVING, not merely checked out.** Everything below was measured against a dedicated leg on
`:8052` launched from the probe worktree at canopy **`8a43a33`** and running the topoprobe-instrumented
`dashboard_manager.py`; the shared `:8050` leg was untouched. Naming the serving commit rather than the
checkout is deliberate — a long-running leg serves the code it *imported*, and reading a merged fix into
a process that predates it cost this arc a whole row census once already. Every `file:line` cited below
was re-verified against canopy main **`785fb64`** after teardown and still resolves to the same
statement, so the citations do not depend on which of the two commits the reader has to hand.

**A. THE DUPLICATE-INSTANCE HYPOTHESIS IS REFUTED — from the one vantage point that can see it.**
`state.paths.strs` maps one id to one path, so it cannot *represent* a duplicate; asking it this
question was always going to return a confident non-answer. Dash serves the layout tree as JSON from
the **server**, before dash-renderer indexes anything, so a duplicate id appears there as what it is.
New instrument: `util/ad-hoc/2026-09-05_dash_layout_id_census.py`, against
`/dashboard/_dash-layout` on the instrumented leg.

| | |
|---|---|
| layout served | 165,807 bytes |
| id-bearing nodes | **465** |
| distinct ids | **465** |
| duplicate ids, anywhere in the layout | **0** |
| `metrics-panel-metrics-store` instances | **1**, at `children.11.children.1.children.0.children.0.children.children.11`, default `data=[]` |

Corroborated by source: the id has exactly one declaration site,
`metrics_panel.py:537` (`dcc.Store(id=f"{self.component_id}-metrics-store", data=[])`).
`candidate_metrics_panel.py` declares no such store — its `SHARED_METRICS_STORE_ID` (line 63) is only
ever *read*, as an `Input` at line 349. **There is one store. Reader and writer address it.**

**B. THE TOPOPROBE'S WARNING IS DISCHARGED — the second writer is exonerated twice over.** The report
demands: *"BEFORE concluding: discriminate by WRITER"*, naming `append_ws_metrics_store`
(`allow_duplicate=True`, `dashboard_manager.py:3910`) as an ungated writer whose every write is
"`no_update`-free by construction".

- *Statically*, that characterisation is too strong in the direction that matters here.
  `_append_ws_metrics_store_handler` (`dashboard_manager.py:6732`) opens
  `if not ws_events: return dash.no_update`, and its only other return is
  `current + ws_events` bounded to the window. **It cannot write an empty value at all**, so it
  cannot be the thing holding the store at `[]`.
- *Empirically*, it never ran. The appender fires only on a `ws-metrics-buffer` change; that store is
  written by a **clientside** drain (`dashboard_manager.py:3602`) which returns `no_update` unless it
  actually drained frames, and it bumps `gen` on every real drain. Bracketing the census window, the
  buffer read `{'events': [], 'gen': 0, 'last_drain_ms': 0}` **before and after** — its mount default,
  `gen` **0 → 0**. Consistent with `ws-liveness-store`'s `metrics_live: False`.

The re-drive now records this as `ws_appender_fired: false` rather than leaving it to be inferred.
**The liveness-gated REST poll is the sole writer**, and the topoprobe's verdict may be read.

**C. THE SERVER'S OWN VIEW NEVER ADVANCES EITHER — this is the sharp fact.** The topoprobe logs the
guarded handler's `State`, which is the handler's own Output handed back on the next tick. Over
**130 comparisons** (`--target metrics`), every one is `eq=False` at a **constant `cur_len=2`** — the
serialised `[]` — against `new_len=164570` offered each time.

> If the browser had applied any of those writes, the following tick's `State` would carry 500 rows.
> It carried `[]` one hundred and thirty times.

So the response reaches the browser and **the browser does not apply it**. That is a stronger claim
than the block above could make, and it is made from a server-side vantage point that shares no
machinery with the `paths.strs` reader.

**D. A CENSUS-WINDOW CORRECTION, and the instrument defect behind it.** The block above quotes
"17 writes of 500 rows in 30 s; `omitted=0`, `unparsed=0`". That figure is **correct for the window**
and matches the archived `.txt` exactly. The `.json` archived beside it, from the *same run*, reads
**46 writes / `unparsed=7`**. Both are real: `_wire_census` and `_write_census` attached
`page.on("response", …)` and **never detached**, and returned the very dict the handler keeps
mutating — so the log printed the honest 30 s snapshot at t=91 s and the JSON, dumped at t=139 s
after the script's 45 s wait on the loss plot, reported the whole listening lifetime. A census that
does not stop counting when its window closes is not a census. Fixed in
`util/ad-hoc/2026-09-04_f035_candidate_loss_redrive.py`: both censuses now `remove_listener`, return
a copy, and record `window_s` in the artifact so the window is never again implied.

Re-driven after the fix, artifacts coherent (`…_v2.{txt,json}`, both windows now agreeing):

| measurement | result |
|---|---|
| server history | 100 rows, **93 `candidate`** / 7 `output` *(fixture regrown — see the F-CANOPY-037 notice)* |
| `ws-liveness-store` | `{'metrics_live': False, 'state_live': False}` |
| `ws-metrics-buffer`, bracketing | `gen` **0 → 0**, mount default both reads |
| writes to the store, parsed, **30 s window** | **14 writes of 500 rows**; `omitted=0`, `unparsed=0` |
| store read before / after those writes | `len=0` / **`len=0`** |
| `candidate-metrics-panel-loss-plot` | present, **zero traces**, 45 s budget |

**E. THE LEADING MECHANISM IS MEASURED — and it does NOT close the finding.** The arc already carries
a mechanism with this exact signature: dash-renderer retires an **in-flight** call when the same
callback is **re-requested**, and the retired response is discarded on arrival. `update_metrics_store`
is driven by `fast-update-interval` at `FAST_UPDATE_INTERVAL_MS = 1000` (`canopy_constants.py:370`).
New instrument: `util/ad-hoc/2026-09-05_f035_store_write_latency_probe.py`, 60 s window, timing every
store-writing round trip at the browser.

| | min | median | max |
|---|---|---|---|
| round-trip duration | 0.989 s | **1.827 s** | 4.71 s |
| gap between store-writing requests | 1.128 s | **1.716 s** | 2.848 s |

**29 writes of 500 rows; 20 of them (69%) were still in flight when a successor was issued.** The
median round trip exceeds the median re-request gap, so on average a write is superseded before it
lands — the retirement precondition, holding most of the time.

**But it does not account for the result, and saying so is the point.** Nine of the 29 responses had
no store-writing successor in flight, and the store still read `len=0` at the end of the window —
and the server-side `State` was constant-empty across **130** comparisons, not 69% of them. Overlap
this heavy would degrade freshness; it cannot by itself produce a store that *never* advances. So:

- **Established**: one store instance; one active writer; full payloads on the wire; neither the
  client's copy nor the server's `State` ever advancing; heavy request overlap.
- **NOT established**: that renderer retirement is the cause. It is the leading hypothesis with
  supporting arithmetic and an unexplained residual — nine unopposed responses that also failed to
  land. Reporting it as the cause would be this arc's recurring error, a well-formed measurement of
  an adjacent question returned in confident numbers.

**The discriminating next measurement** is inside dash-renderer, not around it: instrument the store's
`setProps`/reducer path in the browser to record whether the payload arrives at the renderer and is
dropped, or never reaches it. `util/ad-hoc/e2e_f039_metrics_store_soak.py` and
`e2e_f039_duplicate_store_probe.py` remain available; note the latter's `exit 1` means "could not
run", not a verdict — and its question (duplicates) is now answered by **A**, so it is no longer the
one to reach for.

**Matrix effect: none.** M-CANDIDATES-07 stays **FAIL**; canopy#524's adapter stays correct and
unreachable. What moves is the basis and the open-question list: the duplicate-instance question is
**closed by refutation**, the writer discrimination is **done**, and the remaining unknown is narrowed
from "why is the store empty" to "why does an applied-looking response not reach the store's state".

**The instrumented leg is down.** The topoprobe was reverted (`revert` confirmed the checkout clean,
zero `TOPOPROBE` occurrences, empty `git status`), the :8052 leg was stopped **by pid** (2235611) via
`util/ad-hoc/2026-09-04_canopy_verify_instance.bash down 8052`, and the probe worktree
`juniper-canopy--probe--f039-metrics--20260905-1200--probe` was removed and pruned.

Evidence, all under `reports/e2e-canopy-2026-09-02/transcripts/`:
`2026-09-05_f035_candidate_redrive_v2.{txt,json}` (coherent re-drive),
`2026-09-05_f035_layout_id_census.{txt,json}` (the duplicate refutation),
`2026-09-05_f035_store_write_latency.{txt,json}` (the timing),
`2026-09-05_f035_topoprobe_metrics_report.txt` (130 comparisons) and
`2026-09-05_f035_topoprobe_canopy8052.txt` (the leg log it was read from — archived as `.txt`
deliberately: `.gitignore:52` is `*.log`, which would have silently excluded it).

**F-CANOPY-036 — candidate pool history NEVER accumulates in the live lane: the history-append callback loses its race with its own feeder's repoll, so short-lived pool states are never recorded (P2, OPEN; found during the 2026-08-24 live re-drive).**
Across five training runs on one bring-up (~20 candidate phases), `candidate-metrics-panel-history-section` never rendered a card — while in the same sessions the SAME store's sibling consumers provably rendered active-pool values (run 5: an in-page 500 ms observer, healthy all run — 8 sampler gaps > 2 s, worst 2.8 s — recorded the badge rendering `Selecting Best` at t+189 s; runs 1/2 rendered pool 40 / `Training` / progress `351/400`). So this is **not** the fixed F-CANOPY-027 store→consumer starvation. Constructive probe on a CALM post-run page: injecting a fully-shaped `candidate_pool_status:"Training"` payload through the store's own `setProps` (the §12.1 idiom, `ok via memoizedProps.setProps`) produced **no card in 100 s**, and the request capture shows `update_pool_history` (output `…-pool-history-store.data`, `candidate_metrics_panel.py:347-381`) **never executed after the injected write** — while the same capture shows it executing normally on an ordinary poll fill (with `candidate_pool_status=Inactive`, i.e. after the transient state was already overwritten). Mechanism family: dash-renderer executes a queued callback with the store's CURRENT value (or supersedes the queued trigger entirely) when the feeder — `fetch_training_state`, polling at ~1 s on the candidates tab — rewrites the store before the append is promoted; any pool state shorter-lived than the promotion delay is unrecordable. The append's design contract (`:344-392`, one snapshot per `current_epoch` while a pool is active) is therefore probabilistic-to-never under load, and zero-across-five-runs in practice. Matrix effect: M-CANDIDATES-09 FAIL (populated arm unreachable, cause re-attributed from F-CANOPY-027 to this finding); M-CANDIDATES-10/-11 remain BLOCKED (their DEAD-EXPECTED click test needs a rendered card; blocker likewise re-attributed). Candidate fixes (owner decision): append server-side (canopy backend accumulates pool history and serves it, removing the client-side race entirely) or make `update_pool_history` clientside so it runs synchronously in the same commit as the store write.

**F-CANOPY-037 — the topology rebuild is still chained off the 1 Hz `metrics-panel-metrics-store`, which rewrites 141 KB of IDENTICAL data ~0.6/s on a COMPLETED run; the graph therefore renders only when it wins the race — 2 of 11 sessions measured (P0/P1; found during the 2026-08-26 §6.3 topology re-drive; mechanism FIXED canopy#531 2026-08-27, verified 2026-08-28; **CLOSED 2026-09-05** — the `ws-cascade-add-buffer` growth trigger the fix created is now driven on a live cascade, twice).**
Measured live on a fresh isolated trio (data 8101 / cascor 8202 / canopy 8051, service mode; cascor `c6cd2f0`,
canopy `9f6fac9`) against a completed 10-unit network, with `util/ad-hoc/e2e_seg17_topology_driver.py`.

**This is not F-CANOPY-006 and not F-CANOPY-004.** F-006 was "a provably-correct server render is silently
never applied client-side"; it is genuinely fixed — when the rebuild runs here, the DOM *does* apply it. F-004
is a *latency* envelope (3–16 s interaction, 20–40 s fresh session); this is not late, it is **absent**, and it
does not resolve at any budget.

**What renders, when it renders.** In 2 of 11 sessions the rebuild executed and the graph was correct and fast:
the intercepted response was **HTTP 200, 39,319 B, 206 traces**, and the DOM applied it — stats bar
`2 / 10 / 2 / 89` exactly matching `GET /api/topology` (14 nodes, 89 connections), `gd.data` 181 traces,
`sig=31152`, ~22 s after tab entry. A wire census in another live session counted the rebuild output
(`..network-visualizer-graph.figure...-input-count.children...`) **12×/60 s**.

**What happens the other 9 times.** Zero rebuild POSTs, `gd.data` stays `[]` (`sig=2`), stats bar stays at the
layout-default `"0"`s. Ruled out explicitly, each by measurement: *tab not active* (`[role=tab].active` read
`'Network Topology'` every time); *server wrong* (`/api/topology` served 2/10/2/89 throughout); *store empty*
(the depth slider's clientside max bumped `0 → 10`, which only the populated store can do); *callback errored*
(canopy log carries zero callback errors — the only ERRORs are the benign pre-run `No network created` lines);
*my own polling starving it* (a control that opened the tab and waited **90 s with zero `page.evaluate` calls**
was equally empty); *progressive in-process starvation* (a **fresh canopy leg** via
`e2e_canopy_leg_restart.bash` was equally empty); *run-vs-idle posture* (equally empty **during an active run**
and post-run); and *the depth filter* (`_apply_hierarchy_filter` returns unfiltered for `depth <= 0`,
`network_visualizer.py:728`, so `value=0` is "all", not "none"). Driving the callback's **own Inputs** — three
off/on toggles of `show-weights`, which is one of its 12 `Input`s — did not wake it either (112 s, 3 attempts).

**Mechanism, measured directly.** `update_network_graph` takes `Input("metrics-panel-metrics-store", "data")`
(`network_visualizer.py:350-359`), and the source comment already names the hazard: *"this callback is still
chained off `metrics-panel-metrics-store` (a global 1 Hz store), so gating the interval reduces but does not
eliminate its off-tab work — that chained-store class is Stage 2."* A rewrite census on a **COMPLETED** run
recorded **34 writes to that store in 60 s (0.57/s), 33 of them byte-identical to their predecessor**
(141,460 B every time), and **zero `no_update`**. The rebuild's own server time is 1.5–5 s, so its Input is
re-claimed by a pending feeder far more often than the rebuild can complete — the §12.2 / §12.6 claimed-Input
limit case that Stage 2 fixed for the Decision Boundary panel, still live on this path. Stage 2's no-op-write
suppression demonstrably does **not** cover this feeder: 33 of 34 identical rewrites is the proof.

> **Correction (2026-08-27).** "Does not cover this feeder" was read as *the lever was never applied here*.
> It **was** applied: `dashboard_manager.py:6724-6725` returns `no_update` when the fetched history equals
> the store. The lever is present and **not biting** in the live lane — which is a different, separate
> defect, now filed as **F-CANOPY-038**. It does not change this finding's mechanism or its fix.

**Blast radius.** M-TOPOLOGY-01..18, W4-01..17 and W1-12..14 stay **BLOCKED**, with the blocker **re-attributed
from F-CANOPY-006 (closed) to this finding**. The mandate's flagship visualization is non-functional in the
live lane for ~4 sessions in 5. Independently, a 141 KB payload rewritten 0.57/s on a finished run is ~80 KB/s
of pointless traffic and its own regression on Stage 2's intent.

**Candidate fixes (owner decision).** (a) Suppress no-op writes on the `metrics-panel-metrics-store` feeder —
the Stage 2 lever, simply not applied to this producer; (b) drop `metrics-panel-metrics-store` from the
rebuild's Input list (the rebuild does not use metrics data for the node graph — it is a legacy chain);
(c) stop the metrics poll entirely once `fsm_status` is terminal. (a) and (b) are independent and either alone
should be sufficient; (b) is the smaller diff and removes the coupling outright.

> **MECHANISM VERIFIED FIXED LIVE (2026-08-28, run `20260828T132533Z`) — but the rows stay BLOCKED on a
> DIFFERENT failure, now filed as F-CANOPY-039.** Re-driven on a fresh isolated trio against a completed
> 10-unit network whose server truth is byte-identical to this finding's (`2 / 10 / 2 / 89`, 14 nodes).
>
> **The starvation is gone.** `--step wirecensus` counted, in 60 s on the topology tab: the rebuild output
> **10x**, `network-visualizer-topology-store.data` **12x**, `-raw-topology-store.data` **12x** — 12 writes
> in 60 s is exactly the 5 s `tabpoll-topology` cadence, so the tab-gated interval ticks and the rebuild
> now runs on it. This entry's own measurement was **zero rebuild POSTs** in 9 of 11 sessions; the trigger
> is no longer being re-claimed. `--step rebuildprobe` confirms each response is HTTP 200 / 39,319 B /
> ~206 traces / `empty_fig=False` — correct and complete.
>
> **What did not improve: the graph still does not paint.** The multi-session census
> (`util/ad-hoc/e2e_f037_render_census.py`, the instrument this entry's 2-of-11 demands) recorded **0 of 5
> painted**, every session with an identical deterministic signature — `sig=2`, `counts 0/0/0/0`, the full
> 240 s budget burned. It was stopped at 5 of a planned 11 because the signature was identical every time
> and the wire evidence had already re-pointed the investigation; artifact
> `reports/e2e/20260828T132533Z/f037_census.json` records the truncation and its reason. `--step topo`
> likewise reports `wake_topology: woke=False` after 109.5 s of driving the callback's own Inputs.
>
> So the rebuild runs, returns a correct figure, and **the DOM never applies it** — a different defect,
> which an A/B against pre-merge `9f6fac9` proves is **not** a regression from this fix. See
> **F-CANOPY-039** for the evidence and the named next probes. This entry stays OPEN because its rows are
> still BLOCKED, but its own stated mechanism — the claimed-Input starvation — is closed.

**FIX MERGED (2026-08-27, `juniper-canopy#531` → canopy main `a4b8daa`; 21/21 required contexts green.
LIVE RE-DRIVE OWED — this entry stays OPEN until the topology block is re-driven, per the same convention
F-CANOPY-035 follows.)** Fix **(b)**, with one correction to
the candidate's rationale: the rebuild *does* use `metrics_data` — `network_visualizer.py:471-473` reads the
last two entries' `network_topology.hidden_units` to arm the P2-1 new-unit highlight — so the store is
**demoted from `Input` to `State`**, not dropped. The data still arrives on every run; it simply no longer
triggers. Remaining Inputs are only what means "the topology changed": `network-visualizer-topology-store`,
the tab-gated 5 s `tabpoll-topology` (slower than the 1.5-5 s rebuild, so it structurally cannot starve it)
and `ws-cascade-add-buffer`.

**Why (b) and not (a) — the argument that settles the owner choice.** (a) can only fix the idle regime: at
idle the refetch is identical, so suppression applies. **During a run the store changes legitimately at 1 Hz**,
so the claimed-Input starvation would survive exactly when the cascade is growing and the user is watching it
— and this finding measured the graph *equally absent during an active run and post-run*. Only decoupling
fixes both regimes. (a) remains worth doing on its own merits (the ~80 KB/s waste, 4+ consumers re-fired);
that is now **F-CANOPY-038**, not part of this fix.

---

### 2026-09-04 — the owed live re-drive, against merged main (and what it does not reach)

This entry has said since 2026-08-28 that its **own mechanism is closed** and that it stays OPEN only
until the topology block is re-driven. That re-drive is now done for the M-TOPOLOGY rows, **against canopy main `94220f0`** —
which contains both of this arc's latest fixes (canopy#570 F-CANOPY-042, canopy#573 F-CANOPY-046) *and*
another session's canopy#567, which moved every synchronous network call off the event loop and could
plausibly have disturbed rendering.

Driven with `util/ad-hoc/e2e_seg17_topology_driver.py` on the live 2/40/2/944 fixture, via a second
canopy on `:8052` launched from the primary checkout
(`util/ad-hoc/2026-09-04_canopy_verify_instance.bash`) so the arc's `:8051` instance was left untouched:

| step | rows | result |
|---|---|---|
| `topo` | M-TOPOLOGY-01..08, -17 | **9 PASS / 0 FAIL** |
| `topoevents` | -09, -10, -12, -15 | **4 PASS / 0 FAIL** |
| `topostate` | -13, -18 | **2 PASS** (see the ordering note below) |
| `topoexport` | -14 | **1 PASS** (`canopy_network_20260904_173346.png`, 2204×1200 = scale 2.0 from the IHDR) |

**16 PASS / 0 FAIL across every scoreable M-TOPOLOGY row.** The two that remain BLOCKED — **-11**
(select-mode drag emits nothing) and **-16** (cascade-add glow, which a saturated 40/40 fixture cannot
exercise) — are blocked on their own causes, neither of which is this finding.

**One row needed a control, and got one.** In the combined four-step run M-TOPOLOGY-18 scored
**INDETERMINATE** (`empty_in_node_graph=False`) rather than PASS. That is an **ordering artifact, not a
regression**: the row's first half needs the raw-topology store still empty, and `topo` fills it
permanently when M-TOPOLOGY-03 opens the Weight Matrix. Re-driven **alone against the same build minutes
later** it scored **PASS** (`empty_in_node_graph=True`, filled in 6.6 s). The scorer reporting
INDETERMINATE instead of FAIL is the behaviour working as intended; the hazard is now pinned in three
places in the driver so the next reader does not mistake it for a defect.

**WHAT THIS DRIVE DOES NOT ESTABLISH — and why this entry is NOT closed on it.**

An adversarial review of this very closure (Lane B, 2026-09-04) found the gap, and it is the one
that matters: **this finding's fix was an `Input` → `State` demotion, so after it, cascade growth
reaches the rebuild through exactly one Input — `ws-cascade-add-buffer`
(`network_visualizer.py:369-379`). The drive above produced ZERO cascade adds**: the fixture is
`COMPLETED`, 40/40, `early_stopped`. Seven of ten Inputs were driven, all of them user controls, on
a static network where nothing contends. **The trigger the fix created, and the live-growth
contention regime this finding is actually about, are both undriven.**

Two further observations from the same review, each checkable in the transcripts:

- **Both runs needed `wake_topology` to reach a painted graph.** That helper exists *because of this
  defect* — its docstring records "0 rebuild POSTs in 180 s in one session, 12 in 60 s in another".
  The runs report `already: False` and then `woke: True` after **23.2 s** (1 attempt) and **62.0 s**
  (2 attempts — the first burned a full 30 s budget producing no paint). 23.2 s is this finding's own
  lucky-session number. Neither run observed the tab-poll lane painting unaided.
- **The step→row coverage is 9 of 20, not "most".** Uncovered: W4-01 (tab entry asserts a NET call;
  M-17 asserts DOM on *re*-entry), W4-05, W4-10, W4-12 (the re-click gesture is driven nowhere),
  W4-13, W1-12 (its precondition is a cold-start run), W1-13, W1-14. Partial: W4-03, W4-14, W4-17.
  Two driver aliases are also wrong — `M-TOPOLOGY-12 / W4-13` should be W4-12, and
  `M-TOPOLOGY-18 / W4-15` is unsound since W4-15 is the camera export (M-TOPOLOGY-14). And
  `M-TOPOLOGY-08 / W1-14` is **structurally false**: W1-14 compares the *top status bar* to the
  topology counts, and `counts()` never reads the top bar — the two surfaces are *designed* to
  diverge under the depth filter.

**The fixture blocker is a reversible arc decision, not an independent cause.**
`nn_max_hidden_units` is a settable product parameter (`dashboard_manager.py:498`, `main.py:3791`),
this arc gathered F-CANOPY-037's own evidence on a 10-unit fixture on 2026-08-26/28, and the matrix
says plainly that the network *"was deliberately left [saturated] on 2026-09-02 to preserve the
2/40/2/944 baseline"*. So W4-10, W1-13 and M-TOPOLOGY-16 are blocked on a choice this arc made and
can unmake — pending owner sign-off, since the fixture is held by an explicit hold.

**Disposition (2026-09-04): F-CANOPY-037 stays OPEN.** Its stated mechanism (claimed-Input starvation
on a completed run) is credibly closed on merged main and the M-TOPOLOGY rows are re-driven; what
remains undriven is the growth-trigger path the fix itself introduced. Closing on the static branch
alone would be closing the symptom on the easy branch.

---

### CLOSED 2026-09-05 — the growth trigger is driven, on a live cascade, twice

The owner lifted the fixture hold, so the regime this finding is actually about was finally
exercised. `max_hidden_units` was raised by `PATCH /v1/training/params` — **the network was never
destroyed** (`POST /v1/network` was not used; the uuid is unchanged throughout) — and training
restarted, twice, with a browser attached and watching *before* growth began.

**Probe**: `util/ad-hoc/2026-09-05_f037_growth_trigger_probe.py`, against canopy main `94220f0`.
Growth oracle is **cascor's own** `hidden_units`, read off `:8202` — deliberately not through canopy,
because canopy's number is the thing under test and an oracle sharing a path with its subject is not
an oracle.

| | run 1 (40 → 44) | run 2 (44 → 48) |
|---|---|---|
| server grew | t=18.4 s | t=17.6 s |
| **`ws-cascade-add-buffer` `gen`** | *(not polled — see below)* | **0 → 6, `events=1`, t=17.6 s** |
| rebuild wrote `-graph.figure` | t=12.4 s, t=38.3 s | t=65.3 s |
| DOM reached the new count | **t=44.4 s → `44`** | **t=70.8 s → `48`** |
| final DOM vs server | `44` = 44 ✓ | `2 / 48 / 2 / 1324`, hidden 48 ✓ |

**The trigger the fix created fires.** `ws-cascade-add-buffer`'s `gen` moves `0 → 6` carrying an
event at the exact moment cascor grows, and the rebuild follows. **The graph tracks live cascade
growth to the correct final count in both runs.** The lag from server growth to DOM catch-up was
**26 s** and **53 s** — an F-CANOPY-004 latency question, not the absence this finding recorded
(0 rebuild POSTs in 9 of 11 sessions).

**AN INSTRUMENT THAT WOULD HAVE GIVEN THE WRONG ANSWER, and why its number is excluded.** The probe
also counts `/_dash-update-component` responses naming the buffer. That count is **0 in both runs**,
and it means nothing: `ws-cascade-add-buffer` is written by a **`clientside_callback`**
(`dashboard_manager.py:3652`), which executes in the browser and produces no callback response at
all. A zero there is structurally guaranteed — the mirror image of browser-counting a server-side
fetch, the error that produced a confident FAIL on M-TOPOLOGY-18. **Only the store's polled value is
admissible for this trigger**, and it is what the table above reports. The counter is retained in
the probe with that caveat written beside it rather than deleted, so the next reader sees why it is
not evidence.

**RESIDUALS, stated rather than buried.**

- **n = 2 growth events**, one session each. The procedure's own escalator for a sample below ~5
  applies; this closes the *stated* gap, it does not make the path well-characterised.
- Run 1 did **not** poll the buffer — the trigger evidence rests on run 2 alone. Run 1 contributes
  the independent fact that the DOM tracked growth.
- Growth arrived as a **4-unit jump** at the 5 s poll granularity, and run 2's single drained event
  may therefore cover several adds. Per-add behaviour is not resolved.
- The DOM lag (26 s / 53 s) is unmeasured against a budget; it is recorded, not scored.

**THE SHARED FIXTURE HAS CHANGED, and this is the notice.** It was **2/40/2/944** and is now
**2/48/2/1324**, `max_hidden_units` 48, saturated again so it is stable. Every earlier row in this
ledger and matrix quoting `2/40/2/944` was measured against the old fixture and remains valid *for
that build and that fixture* — do not treat a new reading of `48` as a regression.

The pre-change state is recoverable: snapshot **`snapshot_20260905T103912Z`** (815,937 bytes,
`juniper.cascor` format v2, verified on disk — the creation response reports `size_bytes: 0` before
flush, but the listing and the file agree at 815,937).

**To make M-TOPOLOGY-16 (cascade-add glow) drivable again**, raise the cap and restart — the network
is grown, not rebuilt:

```bash
curl -X PATCH -H 'Content-Type: application/json' \
     -d '{"max_hidden_units": 52}' http://127.0.0.1:8202/v1/training/params
curl -X POST  -H 'Content-Type: application/json' -d '{}' \
     http://127.0.0.1:8202/v1/training/start
```

Evidence: `reports/e2e-canopy-2026-09-02/transcripts/2026-09-05_f037_growth_1.txt` (run 1 — log
only; the probe was stopped once growth had been captured, so it never wrote its results file)
and `…_f037_growth_2.{txt,json}` (run 2, complete).

Evidence: `reports/e2e-canopy-2026-09-02/transcripts/2026-09-04_f037_closure_main_94220f0.{txt,json}`
and `…_f037_m18_isolated.{txt,json}` (the control).

Pinned by `src/tests/unit/frontend/test_f037_topology_rebuild_decoupling.py` (6 tests): the store absent from
Inputs / present in State; the real triggers still Inputs (a forward guard against an over-correction that
decouples those too); new-unit detection still arming across the demotion, and arming nothing on a steady
topology; and — class-level — that **no _unconditional_ 1 Hz feeder drives the rebuild**, whichever store it
arrives through, cross-checked against the real `DashboardManager` wiring. That last pin surfaced that
`ws-cascade-add-buffer` also rides `fast-update-interval`; it is an event **drain** that returns `no_update`
on an empty drain, so it writes at the cascade-add rate, and the test **verifies that guard in source** rather
than waiving it. **5 of the 6 fail on the parent `9f6fac9`** (the sixth is the forward guard, which passes
there by construction). The pre-existing `test_invoke_update_network_graph_with_metrics` was mutation-checked
against the old argument order and fails `assert new_highlight is not None`, so the State reordering is pinned
by an existing test too. Full `src/tests/unit/` + `src/tests/regression/` exit 0; pre-commit clean.

**Known trade-off, recorded rather than hidden.** New-unit detection is a *last-pair* check
(`metrics_data[-2]` vs `[-1]`). It previously benefited from the metrics-store write *being* the trigger, so
the straddle was fresh by construction; under the demotion it depends on a rebuild landing while the
transition is still the last pair. This is cosmetic (the P2-1 pulse; the graph, counts and stats bar are
unaffected) and was deliberately not bundled into a P0/P1 fix.
`metrics_panel._hidden_unit_addition_markers` (`metrics_panel.py:1999-2003`) already uses the more robust
whole-window scan — adopting it here, with dedupe so a dismissed pulse cannot re-arm, is the follow-up.

**F-CANOPY-038 — the Stage 2 no-op-write suppression on the metrics-store feeder is present in the source but does not bite in the live lane; its unit test cannot observe the failure because it never round-trips through the browser (P2, OPEN; found 2026-08-27 while fixing F-CANOPY-037).**
The lever exists. `_update_metrics_store_handler` (`dashboard_manager.py:6724-6725`) ends with
`if isinstance(current_metrics, list) and metrics == current_metrics: return dash.no_update`, and
`current_metrics` is wired as `State("metrics-panel-metrics-store", "data")` on the writing callback
(`:3869-3875`). Yet the F-CANOPY-037 census on a **COMPLETED** run recorded **34 writes / 60 s (0.57/s), 33 of
them byte-identical (141,460 B each), and zero `no_update`** — so the branch is present and not taken. At
~80 KB/s on a finished run this re-fires every consumer of that store (the tiles, the model-class styles, the
replay UI, and — until `juniper-canopy#531` — the 8-output topology rebuild).

**Why the suite is green.** `test_stage2_global_lane.py::test_metrics_identical_fetch_is_no_update`
(`:111-116`) builds `history = [{"epoch": 1, "metrics": {"loss": 0.5}}]` and passes `current_metrics=list(history)`
— the *same in-process Python objects* on both sides of the `==`. Live, the two sides are not comparable that
way: `metrics` is fresh from `response.json()`, while `current_metrics` is the client's copy of the store,
having been serialized by Dash, parsed by JS, re-serialized and re-parsed. The test cannot exercise any
round-trip asymmetry, so it passes against a predicate that is dead on the wire. This is the
**vacuous-pass / mock-seam class** in its round-trip flavour.

**Root cause NOT yet determined — do not guess-patch.** Candidates, none confirmed: (i) a JSON round-trip
asymmetry that makes `==` always false (a `NaN` on one side and `null` on the other is the classic — note
`_normalize_metric` carries nullable `val_loss` / `f1` / `precision` / `recall` / `roc_auc`,
`cascor_service_adapter.py:1905-1928`); (ii) **State staleness under congestion** — the client's store value
lags the writes it has not applied yet, so `current_metrics` never catches up and every tick looks like a
change; this one is self-reinforcing and fits "zero `no_update`" exactly, and F-CANOPY-004's congestion is the
enabling condition; (iii) the census attributed to this writer something written by another path. **Single
instrument caveat**: the 33/34 figure comes from one `storestorm` run; per this arc's own rule a probe is not
evidence until a second instrument agrees, so the confirming step is to log the comparison's *outcome* server-side
(and both operands' canonical hashes) for a minute and read which branch is taken and why.
A useful side-signal: `juniper-canopy#531` removes the rebuild from this store's consumer set, which reduces
the congestion hypothesis (ii) depends on — so re-measuring **after** that merges is the cheapest next probe.

> **RE-MEASURED POST-#531 (2026-08-28, run `20260828T132533Z`, `--step storestorm`). Reproduced exactly,
> and it eliminates hypothesis (ii).** On merged canopy `6b55399` against a completed run: **32 writes in
> 60 s (0.53/s), 31 identical-to-previous, ZERO `no_update`, 141,460 B every time** — the same rate and
> the same byte size as the original census, to three significant figures.
>
> That is the discriminator this entry asked for. `#531` removed the 8-output topology rebuild from this
> store's consumer set, so if **(ii) State-staleness-under-congestion** were the mechanism, the suppression
> should have begun to bite with one fewer heavy consumer re-firing on every write. It did not bite at all —
> the `no_update` count is still exactly zero. **(ii) is effectively ruled out**, which leaves **(i) a JSON
> round-trip asymmetry that makes `metrics == current_metrics` permanently false** as the leading candidate and
> (iii) mis-attribution as the remaining alternative.
>
> Next probe, now the cheap one: log the comparison's OUTCOME server-side — both operands' canonical
> hashes and which branch was taken — for one minute. That distinguishes (i) from (iii) directly, and
> unlike every probe so far it cannot be defeated by an unreliable client-side store read.
>
> > **(i) IS PROBABLY WRONG TOO — F-038 / F-039 / F-035 are probably ONE defect (2026-08-29).** Surfaced
> > by an adversarial review of the arc handoff, then DERIVED here rather than measured, so it is flagged
> > as a deduction — but it follows from data already in this document.
> >
> > **The analogy this deduction first used was WRONG (caught the same day).** It said F-CANOPY-039's probe
> > showed topology's client copy "pinned at its empty default on every tick". It does not: that copy is
> > empty for 4 ticks and then CONVERGES, sitting at the correct 7,059 bytes for 11 consecutive samples —
> > see F-CANOPY-039's correction block. **The deduction survives the loss of that analogy, because it
> > never depended on it** — it rests only on this entry's own census. But the two stores now look
> > DIFFERENT rather than identical, and that contrast is itself the signal: topology's client copy
> > converges, and metrics' apparently never does.
> >
> > **AND THE DEDUCTION ITSELF IS UNSOUND — second correction, same day, from a second adversarial pass.**
> > It said zero `no_update` "can only happen if" the client's copy never advances. That is false in
> > source. Zero `no_update` is consistent with at least FOUR things and this census separates none:
> >
> > 1. the client's copy genuinely never advancing;
> > 2. hypothesis (i) — but *deterministic*, which inverts the parsimony argument below: a constant
> >    result is exactly what a deterministic transform PREDICTS (NaN→null on `_normalize_metric`'s
> >    nullable `val_loss`/`f1`/`precision`/`recall`/`roc_auc`, which this entry itself calls "the
> >    classic"). "It would have to corrupt all 32 identically" is not the objection it reads as;
> > 3. **hypothesis (iii), which this correction had silently dropped**: the store has TWO writers. Besides
> >    the guarded poll `update_metrics_store` (`dashboard_manager.py:3877-3899`) there is
> >    `append_ws_metrics_store` (`:3910-3919`, `allow_duplicate=True`), whose handler
> >    `_append_ws_metrics_store_handler` (`:6664-6685`) ends `return merged[-window_size:] …` with **no
> >    identity guard at all**. Every write it contributes is `no_update`-free by construction and says
> >    nothing about the client's copy;
> > 4. the guarded handler's OWN empty-copy branches (`:6740`, `:6795`): `return dash.no_update if
> >    current_metrics else []` **writes `[]` instead of returning `no_update` whenever the client copy is
> >    falsy** — so "zero `no_update`" is partly PREDICTED by the hypothesis's own premise, and cannot
> >    also serve as its evidence.
> >
> > F-CANOPY-035's corroboration is also weaker than stated: its `len 0` came from
> > `e2e_p1wave_redrive.py --step storeprobe`, the client-side store read this arc has ruled unreliable
> > (F-039's entry says outright "do not re-diagnose from `store` reads … its zeros are not evidence"),
> > and this ledger attributed that reading to F-004 congestion / instrument artefact — **not** to a
> > failed write, and not "for want of an explanation".
> >
> > **Net: F-035 / F-038 / F-039 may be one defect or three.** The probe below still decides it, but
> > **discriminate by WRITER** first — a small constant `cur_len` on the guarded handler is consistent
> > with the census having counted the other one.
> >
> > This entry's own census: **32 writes, 31 byte-identical to each other, ZERO `no_update`.** If the fetched payloads are
> > identical to one another, the only way `metrics == current_metrics` is False *every single time* is if
> > `current_metrics` never equals any of them — i.e. **the client's copy of `metrics-panel-metrics-store`
> > never advances either.** A round-trip asymmetry would have to corrupt the comparison identically on
> > all 32 samples while the payloads stayed stable; "the client value is a constant empty default"
> > explains it with no extra machinery.
> >
> > **F-CANOPY-035 already recorded exactly that, independently** (see its entry): the shared
> > `metrics-panel-metrics-store` was **"globally empty (`len 0`) on BOTH the Training Metrics and
> > Candidate Metrics tabs"** post-run, with the main loss plot empty too — and it was filed INCONCLUSIVE
> > for want of an explanation. This is the explanation.
> >
> > So one sentence — *the server writes, the client's copy never advances* — now covers **F-CANOPY-035
> > (open P1), F-CANOPY-038 (P2) and F-CANOPY-039 (P0/P1)** across **two different stores**. That
> > materially changes F-039's blast radius: not 36 blocked topology rows, but those plus the
> > metrics/candidates render block.
> >
> > **Confirming probe** (the tool now supports it directly; `current_metrics` is already a parameter of
> > `_update_metrics_store_handler`, so unlike the topology target this needs no preparatory `State` edit):
> >
> > ```
> > util/ad-hoc/e2e_f039_topoprobe_instrument.py apply  --checkout <canopy> --target metrics
> > # restart that leg, open Training Metrics for ~90 s, then:
> > util/ad-hoc/e2e_f039_topoprobe_instrument.py report --log <log>     --target metrics
> > util/ad-hoc/e2e_f039_topoprobe_instrument.py revert --checkout <canopy>
> > ```
> >
> > **Read it against topology's baseline, which is now known**: `eq=False` for 4 ticks, then `eq=True`
> > for 11 consecutive samples. If metrics shows `eq=False` on EVERY sample at one constant `cur_len`,
> > its client copy genuinely never advances — the round-trip asymmetry hypothesis dies and F-CANOPY-035
> > is explained. If it converges the way topology's does, this entry returns to hypothesis (i).
> > **Do this before treating F-038 and F-039 as separate work.**

> > ---
> >
> > ## MEASURED 2026-08-29 — the probe was run, and it is decisive.
> >
> > Isolated trio, live (data :8101 / cascor :8202 / canopy :8051 out of the primary checkouts,
> > canopy at `c0c873c`, the `2/10/2/89` fixture alive at 1 d 7 h). `--target metrics` applied to
> > `_update_metrics_store_handler`, 140 s browser soak across BOTH the Training Metrics and Candidate
> > Metrics tabs (`util/ad-hoc/e2e_f039_metrics_store_soak.py`, 480 dash updates, so the interval
> > provably ticked). **79 comparisons. Head identical to tail. Zero `eq=True` anywhere.**
> >
> > ```
> > TOPOPROBE[metrics] eq=False cur_type=list cur_len=2 new_len=155392 canon_eq=False    (x79)
> > ```
> >
> > Evidence: `reports/e2e/20260829T202800Z/f039_metrics_probe/metrics_store_comparison.log`
> > (force-added; `.gitignore:52` is `*.log`).
> >
> > **`cur_len=2` is `[]` — the store's shipped empty default. The CLIENT's copy of
> > `metrics-panel-metrics-store` never advances, at all, ever**, while the server offers 155,392 B on
> > every tick.
> >
> > **1. Hypothesis (i) is DEAD.** A deterministic JSON round-trip asymmetry would have to turn a
> > 155 KB payload into a 2-byte `[]`. It does not survive contact with the measurement. The Stage 2
> > suppression at `:6789` can never bite, because `metrics == current_metrics` is `155 KB == []`,
> > false by construction — which is why the census found **zero** `no_update` in 32 writes. That
> > count is now EXPLAINED rather than merely consistent.
> >
> > **2. F-CANOPY-035 is explained, by an admissible instrument.** Its "globally empty (`len 0`) on
> > BOTH tabs" was measured with the client-side `storeprobe` this arc ruled unreliable. The same fact
> > now holds server-side, where the value Dash actually delivers as `State` is visible. Its
> > INCONCLUSIVE disposition should be revisited on this basis.
> >
> > **3. But the two stores behave DIFFERENTLY, so this is not one mechanism.** Topology's client copy
> > CONVERGES after ~22 s and then holds correct (F-039's correction block). Metrics' never advances
> > at all. Any account that explains both with a single sentence is over-fitting.
> >
> > **4. The strongest inference, and it was not predicted by either hypothesis.** Because `eq` is
> > false on every sample, the poll RETURNS the full 155 KB every tick — and one tick later its own
> > `State` read of that same store id comes back `[]`. **A callback's write is not visible to its own
> > next read.** The WS append writer cannot account for it: `_append_ws_metrics_store_handler`
> > returns `no_update` when there are no events and a non-empty `merged` when there are, so it can
> > never produce `[]`. This is the duplicate-instance signature — now evidenced on a SECOND store id,
> > by a different route than F-039's.
> >
> > **Consequence for the next step:** the runtime duplicate-store probe must target **both**
> > `network-visualizer-topology-store` and `metrics-panel-metrics-store`. It is no longer a topology
> > investigation.


**F-CANOPY-042 — the depth-filter LABEL never updates when the user moves the slider, and reads `"0 of 40"` at rest on an unfiltered network (P2; found 2026-09-02, and only visible once the slider could be driven at all; FIXED canopy#570, merged 2026-09-04, squash `28c0fa19`).**
Drag the depth slider to 20 on a 40-unit cascade and the filter works: the figure re-renders
(`de463bff` -> `ab8c6d50`, 1891 -> 551 traces) and the stats bar updates (`hidden` `40` -> `20 of 40`,
`conn` `944` -> `274`). **The depth label beside the slider stays `"0 of 40"`.**

Cause, from the wiring rather than the symptom: the label is an Output of the CLIENTSIDE slider-bounds
sync (`network_visualizer.py:706-738`), whose only Input is `network-visualizer-topology-store`. The
slider's own value rides there as **State**. So the label is recomputed when the TOPOLOGY changes, never
when the user moves the slider — and post-F-CANOPY-039 the topology store is identity-suppressed, so at
idle it never changes at all. The label is therefore frozen at whatever the last topology write produced.

Severity P2: the filter itself is correct and the stats bar tells the truth, so the user is not misled
about the graph — but the one readout attached to the control they are actually manipulating disagrees
with it.

**It was undiscoverable until the harness could drive the slider.** M-TOPOLOGY-06's expectation is
`label == want OR counts["hidden"] == want`, and it now passes on the counts branch, so the row's PASS
does not cover this. Recorded separately for that reason.

---

**A SECOND DEFECT UNDER THE SAME ID, found reading the code to write the fix brief
(`JUNIPER_2026-09-04_JUNIPER-CANOPY_F042-F046-FIX-DECISION-BRIEF.md`), and wrong AT REST.**

`0` meant two different things:

| consumer | rule | at `value=0`, `n_hidden=40` |
|---|---|---|
| filter (`_apply_hierarchy_filter`) | `depth is None or depth <= 0 or depth >= total` → no filter, label `"all"` | shows **all 40** |
| label (clientside) | `(v === nHidden) ? "all" : v + " of " + nHidden` | renders **`"0 of 40"`** |

The slider ships `min=0, max=0, value=0` and the label's static default is `"all"`, so a freshly loaded
40-unit network read **`"0 of 40"` while all 40 units were on screen** — before anyone touched anything.
**Fixing the wiring alone would not have fixed this**; the label would still have said `"0 of 40"` at
rest. Both had to be settled together, which is why the fix went through a decision brief rather than
straight to a patch.

**The obvious repair was structurally unavailable.** Adding `Input(-depth-slider, "value")` to the
bounds-sync callback makes one component-property both an Input and an Output of a single callback,
which Dash rejects at registration as a circular dependency. Hence the split: the label now has its own
clientside callback (Inputs: the slider value *and* the topology store, the second because a
`cascade_add` changes the denominator with no user action), and the bounds-sync callback returns three
elements instead of four.

Routing the label out of `update_network_graph` — which already computes exactly the right string and
**throws it away** — was rejected on measurement, not taste: that callback is the starvation-prone one
(1.5–31 s; F-CANOPY-037 / -039 / -043), so the number under the user's thumb would update seconds after
the drag. The clientside rule is now a condition-for-condition transliteration of the server guard, and
both sides carry a comment saying so.

**FIXED AND VERIFIED LIVE — A/B, same fixture, minutes apart (canopy#570).** A second canopy was
launched on `:8052` from the fix branch beside the arc's `:8051` instance, both pointed at the same
cascor (`:8202`) and juniper-data (`:8101`), so the only thing differing between the two runs is which
code the process imported. The 2/40/2/944 fixture was never touched.
(`util/ad-hoc/2026-09-04_canopy_verify_instance.bash`, written for this and reused for F-CANOPY-046.)

| row | `:8051` parent `ee2ec79` | `:8052` fix branch |
|---|---|---|
| M-TOPOLOGY-07 (at rest, no gesture) | `display='block' label='0 of 40'` → **FAIL** | `display='block' label='all'` → **PASS** |
| M-TOPOLOGY-06 (drag to depth 20) | `label='0 of 40' hidden='20 of 40'` (`label_ok=False counts_ok=True`) → **FAIL** | `label='20 of 40' hidden='20 of 40'` (both `True`) → **PASS** |
| `--step topo` total | 7 PASS / 2 FAIL | **9 PASS / 0 FAIL** |

**BOTH SCORERS WERE TIGHTENED IN THE SAME PASS, and that is why they read FAIL on parent.**

- **M-TOPOLOGY-06** was `label == want **OR** counts["hidden"] == want` and had been passing on the
  counts branch — the stats bar tracked the filter while the label sat at `"0 of 40"`. **An `OR` over
  two independent claims scores the easier one.** That is why this row was green while half of what it
  names was broken, and why F-CANOPY-042 had to be found by eye instead of by its own scorer.
- **M-TOPOLOGY-07** *read* the label and never asserted it: `label` went into the record as decoration
  while the verdict turned on `display` alone. It logged `'0 of 40'` on every run of this arc and scored
  PASS. Defect B was sitting in that scorer's own output the whole time.

**Unit coverage** (`src/tests/unit/frontend/test_f042_depth_filter_label.py`, 11 tests) is layered so
the JavaScript is not merely *described*: wiring is asserted against `app._callback_list` after a real
`register_callbacks`; **the rule is checked by executing the registered clientside function under node**
over a 48-case grid and comparing it case-for-case against `_apply_hierarchy_filter`, with the Python
function as the oracle and the arguments built from the callback's declared Input order; and a
source-level backstop asserts all four arms of the server guard are present clientside so a missing node
cannot leave the zero-semantics uncovered by a skip. **5 of 11 fail against parent** — driven through
its own registered Input list, parent's label writer ignores the depth entirely and returns `"all"` for
all 48 cases, including the 9 where the filter really is filtering.

---

**M-TOPOLOGY RE-DRIVE COMPLETE (2026-09-02) — 9 of 9 PASS, and the two "harness" failures were real
harness defects with a shared root cause.**

Final: M-TOPOLOGY-01, -02, -03, -04, -05, -06, -07, -08, -17 all PASS against a live 2/40/2/944 network
on canopy `30e15b7`. The driver needed four fixes, and each was verified by effect, not by a sleep.

**One root cause behind three symptoms: the driver acted and read INSIDE the rebuild window.** It waited
1200-1500 ms against a rebuild that settles at 2.8-7 s. Consequences, all of which looked like product
defects:

- layouts appeared to render identically (Spring's figure matched Hierarchical's on a fast read and
  DIFFERED once settled), so the distinct count wobbled 3 -> 2 -> 3 across runs of an unchanged topology;
- the next interaction landed mid-render, so the dropdown portal never opened and "Staggered" scored
  `driven=False` on every run;
- the depth label and stats bar were read before the rebuild that would have updated them.

Fixes: `settle_figure()` (polls until the figure hash holds steady, and reports `painted` because **a
stable EMPTY figure is not a ready one** — a first probe run settled on an unpainted graph and concluded
"the widget could not move"); `fig_hash` added beside `sig` in `fig_info` (`sig` is
`JSON.stringify(gd.data).length`, kept unchanged so historical values stay comparable); `set_dropdown`
settles before and after and retries the portal 3x.

**THE DRIVER COULD NOT READ ANY `dcc.Store`, AND REPORTED THAT AS "EMPTY" — 2026-09-03.**

`_store()` returned the store's value directly and `None` when it failed, which makes *"the store is
empty"* and *"I cannot read this store"* the same answer. It was failing for **every store on the app**.

Caught by a contradiction rather than by inspection. M-TOPOLOGY-18's scorer read
`-raw-topology-store` as empty **while its Weight Matrix heatmap was rendering at `plot_area=0.70`** —
which is only possible if that store is populated. Both cannot be true. A dedicated probe
(`util/ad-hoc/2026-09-03_store_read_probe.py`) then put the app in that exact state and read five stores:

| store | element present | `_store()` (before) |
|---|---|---|
| `-raw-topology-store` | no | `None` |
| `-topology-store` | no | `None` |
| `-view-state` | no | `None` |
| `-selected-nodes` | no | `None` |
| `metrics-panel-metrics-store` | no | `None` |

**Five of five**, including one whose contents the arc has argued about at length. Why: a `dcc.Store`
renders no element, so `getElementById(id)` is null and `_dashprivate_layout` never exists; and the
recursive walk over `state.layout` does not reach components through the shapes Dash 3 nests them in.
The supported route is Dash's own id → path index at `state.paths.strs`, which now works — all five read
back as populated dicts.

**Two consequences, and the second is the reason this is written down:**

1. **M-TOPOLOGY-18 produced a confident FAIL against a working gate**, complete with a diagnostic line
   blaming F-CANOPY-040's shape. It is a PASS: the store is empty in Node Graph and populated 8.4 s
   after switching to Weight Matrix, which is the gate working two-sided.
2. **`step_topodiag` has been logging `topology-store (NoneType): None` for the whole arc.** That line
   reads as *"the client's copy of the store is empty"* — one inch from F-CANOPY-039's central and
   most-relitigated claim about that exact store. It was never evidence of anything; the reader could
   not see any store. `_store()` now returns `{"ok", "value", "via"}` and `store_value()` raises rather
   than returning a falsy value, so an unreadable store cannot be scored as an empty one again.

**Third instrument in this session to return a confident wrong number**, after M-TOPOLOGY-18's first
version counted BROWSER requests for `/api/topology/raw` — an endpoint canopy fetches **server-side**,
so it never crosses the browser and the count was structurally always 0. The pattern is the same each
time: the instrument answers a question adjacent to the one asked, and answers it fluently.

---

**AND THE SAME TRAP ONE LEVEL UP — "stable" is not "ready", 2026-09-02 (M-TOPOLOGY-02).**
`settle_figure` answers *"has the figure stopped changing?"*, which is the wrong question immediately
after an action: **a figure whose rebuild has not STARTED yet is perfectly stable.** The hash holds, three
reads agree, and it reports `settled` while showing the *previous* action's render. `painted` does not
catch this either — the stale figure is fully painted, just stale.

Measured (`/tmp/juniper-e2e/seg17_results.json`, 06:30): M-01 ended by selecting Hierarchical and waiting
a **fixed 2000 ms**; M-02 then called `settle_figure`, which settled on **Circular's `26d0f961`** — M-01's
*last* layout — and scored it as `on`. The weights-off toggle then retired that still-pending Hierarchical
rebuild (`getUniqueIdentifier` hashes inputs + outputs + state and **not** the trigger, and both controls
are Inputs of the same rebuild), so `off` read `26d0f961` as well and the row failed on
`on_hash == off_hash` — two reads of a figure that was neither state.

The fix is `settle_changed(page, prev_hash)`: wait for the **transition** away from a known previous hash,
*then* settle, and return whether the transition was actually observed. A transition that never lands now
scores **INDETERMINATE** rather than silently comparing two stale hashes.

**THE WINDOW, MEASURED** (`seg17_postf561_B.json`, `M-TOPOLOGY-02-precondition`). The new instrumentation
reports how long each transition actually took, which turns the mechanism from an inference into a number:

| transition | from → to | landed at |
|---|---|---|
| M-01 tail → Hierarchical (the precondition) | `26d0f961` → `de463bff` | **7.9 s** |
| show-weights OFF | `de463bff` → `d5d1a4e6` | 6.9 s |
| show-weights back ON | `d5d1a4e6` → `de463bff` | 10.5 s |

**The old code waited a fixed 2000 ms for the first of those.** The rebuild landed at 7.9 s, so there was
a **5.9 s window** in which `settle_figure` would settle on Circular and score it as `on` — and the
weights toggle fired inside that window, retiring the pending rebuild. The two later transitions at 6.9 s
and 10.5 s also exceed every fixed wait the old block used. Nothing about this was marginal; the row
passed at all only when unrelated slowness pushed the read past the window.

**TWO CORRECTIONS THIS PRODUCED, both to claims this arc had already written down:**

1. **The row is a RACE, not a stable defect.** The 06:30 run failed it; the very next run passed it
   unchanged, because a dropdown retry earlier in M-01 happened to add ~12 s and the rebuild landed
   before the first read. *A verdict that depends on how long an unrelated retry took is not a
   measurement.* Both post-#561 runs (A, old driver; B, fixed driver) score PASS.
2. **"Done = `on`/`off`/`back` are three distinct `fig_hash`es" is WRONG**, and that criterion would fail
   a correctly-behaving toggle. Turning weights off and on again *returns the graph to its previous
   render*, so `back` **must** equal `on`. Measured identically in both runs:
   `on=de463bff  off=d5d1a4e6  back=de463bff`. The contract is the two **transitions** — `off != on` and
   `back != off` — which is what the driver has always asserted and what it still asserts.

**M-TOPOLOGY-06 was an IDIOM-ORDERING defect, and the ordering made a WORKING control look dead.** The
slider is `updatemode="mouseup"`: Dash is notified only by a mouseup concluding a real drag, so the
synthetic idioms (React native-value-setter, keyboard arrows) cannot deliver the value **by design**.
Worse, running them first moved the DOM to the target, after which the drag computed a destination the
thumb already occupied and degenerated into a no-op gesture. Measured on the same control and target:

| order | figure | stats bar |
|---|---|---|
| drag AFTER synthetic | unchanged | unchanged |
| **drag FIRST** | **`de463bff` -> `ab8c6d50`, 1891 -> 551 traces** | **`40` -> `20 of 40`, `944` -> `274`** |

`set_slider` now takes an optional `effect` predicate; when given, it drags FIRST and treats a
DOM-only move as a FAILURE so the remaining idioms are actually tried. Verifying by re-reading the widget
proves the DOM moved, **not** that Dash received the value, and on this slider those come apart.

**Fixing M-06 broke M-TOPOLOGY-17, which is the most useful thing in this re-drive.** M-06 leaves the
filter applied; the existing reset called `set_slider(..., 0)` **without** an effect, so it moved the DOM
back to 0 while Dash kept 20. That never mattered while M-06 was broken and applied no filter — **every
earlier PASS of M-TOPOLOGY-17 was valid only BECAUSE M-06 was broken.** The moment M-06 worked, M-17 read
`hidden="20 of 40"` / `conn=274` against a server truth of 40 / 944 and failed. The reset now demands the
downstream effect and logs loudly if the filter fails to clear, so a later row cannot silently inherit a
filtered graph and report a defect belonging to an earlier one.

That is the same shape as F-CANOPY-040 masking F-CANOPY-041, one layer up: **a broken thing was masking a
second broken thing, and the mask was load-bearing for a green result.**


---

**F-CANOPY-040 — the raw-topology poll was gated on the 2D/3D toggle, so the Weight Matrix heatmap could never have data (P1; found 2026-09-01 in the post-F-039 M-TOPOLOGY re-drive; FIXED canopy#557).**
`update_raw_topology_store` passed `State("network-visualizer-view-mode", "value")` — the **2D/3D toggle**,
whose only values are `"2d"` and `"3d"` — into a handler gating on:

```python
if active_tab != "topology" or view_mode != "weight_matrix":
    return dash.no_update
```

`"weight_matrix"` is a value of `network-visualizer-display-mode` (Node Graph / Weight Matrix), never of
the 2D/3D toggle. **The comparison was always true**, the poll returned `no_update` on every tick, the
store was never populated, and the heatmap drew nothing — deterministically, for every user.

Measured: `/api/topology/raw` served a full 40-unit weight payload at the same moment the heatmap
reported `heatmap=False types=[]`. Data present, frontend never received it.

**Third instance in this arc of "a guard that exists, reads as correct, and never fires because it names
an identifier that moved"** — after canopy#537's dead short-circuit (F-CANOPY-039) and F-CANOPY-038/018.
The docstring even states the correct intent while the code names the wrong control.

**Why no test caught it, which is the transferable part.** All five handler tests call
`_update_raw_topology_store_handler(..., view_mode="weight_matrix")` **directly**. The handler was always
correct; only the wiring was wrong, and nothing asserted the wiring. **Unit coverage of a correct
function cannot see a caller that never supplies the value.** The new tests pin the CALLBACK's
dependencies, plus a class-level invariant that generalises past these two ids: *whatever control a gate
reads must be able to hold the value the gate tests for.* On the parent it reports that the gate tests
for `weight_matrix` while reading only controls that can never hold it.

---

**F-CANOPY-043 — fixing F-CANOPY-040 made a previously-dead 5 s poll LIVE, and it feeds the rebuild with no identity suppression: the same hazard class as F-CANOPY-037 and -039, re-created by the fix for -040 (P2; found 2026-09-02 by adversarial review; FIXED canopy#562, merged 2026-09-02, squash `9fbf4b8`).**
`network-visualizer-raw-topology-store` is an **Input** of `update_network_graph`
(`network_visualizer.py:349`). Its writer (`dashboard_manager.py:3983-3984`) is driven by
`Input("tabpoll-topology", "n_intervals")` — the same 5 s tick F-CANOPY-039 demoted one layer down — and
`_update_raw_topology_store_handler` has **no identity comparison at all**: it returns the fetched payload
unconditionally.

**Before canopy#557 this was harmless because the poll never wrote.** Its gate read the 2D/3D toggle and
was always true, so it returned `dash.no_update` on every tick — that *was* F-CANOPY-040. Fixing the gate
turned a permanently-dead poll into a live one that rewrites an identical payload every 5 s into an Input
of a 1.5-5 s rebuild. That is precisely the shape of F-CANOPY-037 (a 1 Hz store) and F-CANOPY-039 (a 5 s
tick).

**Scope, stated precisely:** the handler still gates on `active_tab == "topology"` **and**
`display_mode == "weight_matrix"`, so the rewrite only fires while the user is actually on the Weight
Matrix view. It is not always-on, and no live starvation has been measured for it — this is registered on
the wiring, not on an observation.

**The lesson is the registration, not the severity.** The arc's own remediation pattern (identity-suppress
every unconditional feeder, F-CANOPY-027 Stage 2) was not applied to a feeder that this session brought
back to life. A fix that revives dormant code inherits the obligations that code never had to meet.
The suppression to add is the one `update_topology_store` already carries (canopy#542).

---

**F-CANOPY-040b — `network-visualizer-display-mode` rides the raw-topology poll as `State`, so selecting Weight Matrix does not TRIGGER the fetch (P2; found 2026-09-02; FIXED canopy#562, merged 2026-09-02, squash `9fbf4b8`).**
canopy#557 corrected **which** control the poll reads — it had been `-view-mode`, the 2D/3D toggle, whose
values `"2d"`/`"3d"` can never equal the handler's `"weight_matrix"` gate — but left the dependency a
`State` (`dashboard_manager.py:3992`, pre-fix). **A `State` is read when something else fires.** So the
switch to Weight Matrix still did not fetch: the store filled only on the next `tabpoll-topology` tick,
up to 5 s later.

This is the second half of M-TOPOLOGY-03's run-to-run variance. The row produced **41 zero-height traces**
in one drive and **zero traces** in the next, against an unchanged stack. The zero-height half was
F-CANOPY-041b; **the zero-traces half is this** — the driver read inside the up-to-5 s window before the
store filled.

**Reading the right control is not the same as reacting to it**, and the existing regression test could
not see the difference: `test_it_reads_display_mode_and_not_the_2d_3d_toggle` deliberately unions
`state` + `inputs`, because the question it was written to answer is *which control is read*. That union
is exactly why it stayed green across this defect. canopy#562 adds a separate assertion for the second
question — does that control make it run.

Falsified rather than asserted: `util/ad-hoc/2026-09-02_f043_suppression_probe.py` runs the real
`DashboardManager` out of an arbitrary checkout and reports both properties. Parent `b78bbbb` →
`Q1 NO / Q2 NO`, `VERDICT: DEFECTIVE` (exit 1); canopy#562 → `Q1 YES / Q2 YES`, `VERDICT: FIXED` (exit 0).

---

**F-CANOPY-044 — clicking a node selects NOTHING: every click resolves to a co-located EDGE trace, whose points carry no `text`, and the handler's `if text:` guard drops it silently (P1; found 2026-09-02 by pinning the plotly-event idiom for M-TOPOLOGY-10; FIXED canopy#564, merged 2026-09-03, squash `af390836`).**

`handle_node_selection` (`network_visualizer.py:630`) reads `points[0]` out of `clickData` and does:

```python
point = points[0]
text = point.get("text", "")
if text:            # edge traces have no per-point text -> falls through, no output
```

The figure is **1888 edge traces + 3 node traces** (`Input Units` curve 1888, `Hidden Units` 1889,
`Output Units` 1890). Each edge is `go.Scatter(x=[x0, x1, None], …, mode="lines", hoverinfo="text")`
(`network_visualizer.py:1098`) drawn *to a node centre*, so an edge vertex sits at distance **zero** from
the marker a user aims at, and the click resolves to the edge rather than the node.

**The tie-break RULE is not established, and an earlier draft of this entry over-claimed it.** It said
Plotly "resolves the tie to the lower curve number". The measured hits were curves **82, 166, 248, 1468,
1884, 1886** — not monotonically low, so that explanation does not survive its own data. What IS
established is the outcome: **every click resolved to an edge trace and none to a node trace.** Why
Plotly picks the particular edge it picks is unexplained and does not matter for the finding.

**MEASURED, and it is not a fluke of one marker** (`util/ad-hoc/2026-09-02_plotly_event_probe.py`,
`reports/e2e-canopy-2026-09-02/plotly_event_probe.json`). Seven clicks spanning all three node traces,
at the first / middle / last point of each:

| clicked | node trace | Plotly reported | `text` |
|---|---|---|---|
| Input Units[0] | 1888 | curve **82** | `None` |
| Input Units[1] | 1888 | curve **166** | `None` |
| Hidden Units[0] | 1889 | curve **248** | `None` |
| Hidden Units[20] | 1889 | curve **1468** | `None` |
| Hidden Units[39] | 1889 | curve **1886** | `None` |
| Output Units[0] | 1890 | curve **1884** | `None` |
| Output Units[1] | 1890 | curve **1886** | `None` |

**0 of 7 resolved to a node trace.** `-selection-info` stayed `display:none` with empty `innerHTML`
throughout.

**THE IDIOM IS NOT THE PROBLEM, AND THAT IS THE POINT OF THE INSTRUMENT.** The probe split the question
before drawing a conclusion, because "the click did nothing" has two very different causes. Both halves
were measured: `plotly_click` **fired 9 times** on the graph's own emitter, and **9 `_dash-update-component`
posts carried `clickData`**. Plotly emitted, Dash received, the server was told — and the DOM still never
changed. Two independent idioms (axis `l2p` arithmetic, and the marker's own rendered `<path>` bounding
box) agreed on the same pixel to within a fraction of one, so this is a product defect, not a driver gap.

*(A first probe run had the two idioms "disagreeing" by 279 px. That was the probe's own bug — the
axis-math coordinates were captured BEFORE a `scrollIntoView` and used after it. Both return VIEWPORT
coordinates, so a scroll invalidates them. Recorded because it is the same class as everything else
here: a stale reading that looked like a substantive disagreement.)*

**Consequence for the matrix:** M-TOPOLOGY-10 and -12 are blocked by THIS, not by "no scorer exists".

**M-TOPOLOGY-11 (box/lasso) — the prediction was TESTED and is UNRESOLVED, which is not the same as
refuted.** The prediction was that -11 might be reachable anyway, since it rides `selectedData`, which
returns every point inside the region across all traces, and node-trace points **do** carry `text`.
Driven three times, it produced **zero selections** — but the instrument shows the reason is on the
DRIVER side, not the product's:

```
dragmode at drag time : 'select'      (re-checked immediately before the gesture)
plotly_selected emitted: 0
```

**Plotly never fired the selection event at all**, so nothing was ever handed to Dash and the product
code under test never ran. Ruled out along the way: `dragmode` (confirmed `'select'` at drag time, not
merely after the relayout — the rebuild re-applies `-view-state`, which carries dragmode, and it had
already been shown to wipe a runtime `Plotly.restyle`), and drag distance (the box was ~88x106 px,
well over plotly's ~8 px minimum).

**So M-TOPOLOGY-11 stays "no scorer exists", and its box-select idiom is explicitly NOT pinned.**
Recording this as a driver gap rather than a product finding is the whole point of splitting
emit-vs-receive — the same split turned M-10 into F-CANOPY-044 and keeps M-11 out of the findings
register until a gesture actually reaches Plotly.

> **NARROWED 2026-09-03, and the earlier wording here was too broad.** This entry said "the click idiom
> is pinned and works; the drag idiom is not". **Drags work.** M-TOPOLOGY-13's scorer drives a **zoom**
> drag through the identical `mouse.down / move / move / up` sequence and it lands — `plotly_relayout`
> fires twice, the axis range changes, and it survives a forced rebuild. What fails is specifically the
> **select-mode** drag. The open question is therefore *"why does a select drag emit nothing when a zoom
> drag emits normally"*, not *"can Playwright drag at all"* — a much smaller question, and one the next
> session should not re-open from scratch.

**MECHANISM CONFIRMED BY EXPERIMENT, not by argument.** The probe now runs the hypothesis: set
`hoverinfo:'skip'` on all **1888** edge traces at runtime via `Plotly.restyle`, then re-click. The very
first click flipped:

```
[edges skipped] click Input Units -> hit curve 1888  text='Input 0'  display: block
```

Curve **1888 is the `Input Units` node trace** — the click resolved to a node, carried its `text`, and
`-selection-info` rendered. So "the edges are stealing the hit" is sufficient to explain the whole
finding.

**Why only the first click flipped, which is itself informative:** `-selected-nodes` is an `Input` of the
topology rebuild, so a successful selection *triggers a rebuild*, which re-renders the figure from the
server and **wipes the runtime restyle**. Clicks 2 and 3 hit edges again (curves 248, 1884). The restyle
is a probe device with a lifetime of one rebuild — it is not a candidate fix.

**Fix direction is still NOT asserted.** Candidates: make edge traces unhittable (kills the
`"Weight: -0.420"` tooltip, which is a real feature); resolve the node from the click's `x`/`y` against
the node traces (the handler would need the topology as `State` — it currently receives only `clickData`,
`selectedData`, `-selected-nodes` and `theme-state`); or reorder traces so nodes win the tie (costs
z-order unless plotly's `zorder` is used — the env is plotly **6.8.0**, which supports it). Each has a
cost, and this arc's record on predicted fix directions is poor.

---

**F-CANOPY-045 — the `Layer:` label reads "Output" for every node, because it indexes a 5-element table with a curve number that is now ~1889 (P2; found 2026-09-02, masked by F-CANOPY-044 — and then OBSERVED LIVE the moment that mask was lifted experimentally; FIXED canopy#564, merged 2026-09-03, squash `af390836`).**

Same callback, a few lines on (`network_visualizer.py:687`):

```python
curve_number = point.get("curveNumber", 0)
layer_names = ["", "", "Input", "Hidden", "Output"]
layer = layer_names[min(curve_number, 4)] if curve_number >= 2 else "Unknown"
```

This is correct only if the node traces are curves **2, 3, 4** — i.e. if exactly two traces precede them.
They are curves **1888, 1889, 1890**, and `min(1888, 4)`, `min(1889, 4)` and `min(1890, 4)` are all `4`,
so *every* node — input, hidden and output alike — is labelled `Layer: Output`.

**This is the "a broken thing masks the next one" pattern again, and it is worth naming because the
masking is total**: F-CANOPY-044 means the `if text:` guard never passes, so this line never executes and
the wrong label had never been seen by anyone. Fixing -044 will expose -045 immediately, and the symptom
will look like the -044 fix was wrong. It is not. Registered before the fix, so that inference was
already on the record.

**AND THE PREDICTION WAS THEN CONFIRMED, in the same probe run that confirmed -044's mechanism.** With
the 1888 edge traces made unhittable, the first click landed on the `Input Units` node trace and
`-selection-info` rendered:

```
Selected: Input 0
Layer: Output
(Click again or elsewhere to deselect)
```

**`Input 0` is labelled `Layer: Output`.** So this is no longer an inference from the source — it is
observed behaviour, and it appeared within seconds of the mask being lifted, exactly as written above.
The masking prediction and the defect were both confirmed by one experiment.

The trace ordering that breaks it is not exotic — it is one trace per connection, which is how the
rebuild has always drawn edges. The table encodes an assumption about figure composition that the figure
stopped satisfying as soon as edges became per-connection traces.

---

**F-CANOPY-047 — canopy's own CSP blocks plotly's PNG export: the modebar camera button silently produces nothing, for every user in every browser (P2; found 2026-09-03 while building M-TOPOLOGY-14's scorer; FIXED canopy#565, merged 2026-09-03, squash `c72c0712`).**

`canopy_constants.py` `DEFAULT_CSP_POLICY` serves **`img-src 'self' data:`**. plotly's PNG export
rasterises the figure as **SVG → Blob → `<img>` → canvas → `toDataURL`**, and `blob:` is not in that
directive. The browser blocks the image load; plotly's promise rejects with a bare `[object Event]`; no
`<a download>` is ever clicked; the user gets a console error and no file.

The comment above the constant says *"`data:` in img-src is needed for Bootstrap inline SVG data URIs"* —
`data:` was added for Bootstrap and `blob:` was never added for plotly. `test_csp_bootstrap_cdn.py` pins
`data:` in `img-src`; **nothing pins `blob:`**, so nothing failed when the export broke.

**MEASURED** (`util/ad-hoc/2026-09-03_modebar_download_probe.py`):

| test | result |
|---|---|
| topology PNG, scale 2 | FAIL `[object Event]` (4.4 s) |
| topology PNG, scale 1 | FAIL `[object Event]` — not scale-specific |
| topology **SVG** export | **OK**, 1,211,031 bytes — serialisation is fine |
| 10×10 SVG via **`blob:`** | FAIL `img.onerror` |
| 10×10 SVG via **`data:`** | **OK**, len 170 |

and the console says it outright:

```
Loading the image 'blob:http://127.0.0.1:8051/…' violates the following
Content Security Policy directive: "img-src 'self' data:". The action has been blocked.
```

The camera button exists (9 modebar buttons) and its config is correct —
`format: png`, `scale: 2`, `filename: canopy_network_<YYYYmmdd>_<HHMMSS>`. **Everything the product
declares is right; the header silently disables it.**

**I NEARLY FILED THIS AS AN ENVIRONMENT LIMITATION, and the near-miss is the durable part.** The first
control rasterised a hand-made 10×10 SVG through a **`blob:`** URL — *the same scheme under test* — so it
reproduced the failure and "proved" that headless chromium cannot rasterise SVG. That conclusion was
written into the driver's docstring and the row scored BLOCKED. **A control that shares the mechanism
under test is not a control.** Only varying the scheme — `data:` succeeds, `blob:` fails — exposed the
CSP. Same family as the other instruments in this session that answered an adjacent question fluently.

**FIXED AND VERIFIED LIVE (canopy#565, merged 2026-09-03 as `c72c0712`).** `img-src` becomes `'self' data: blob:`. Two consecutive
`--step topoexport` runs against the same 2/40/2/944 fixture:

| | result |
|---|---|
| before | download timed out at 90 s; raster control `blob:`=FAIL, `data:`=OK |
| after | `canopy_network_20260903_143947.png` — **2204x1200 (scale 2.0)** → PASS |
| after | `canopy_network_20260903_144123.png` — **2204x1200 (scale 2.0)** → PASS |

2204x1200 against a 1102x600 graph is scale 2.0 read from the **PNG's own IHDR**, so `scale: 2` is
verified rather than trusted. The download completes in ~5 s where it previously exhausted a 90 s budget,
so the CSP was the entire blocker. **This is also the first time M-TOPOLOGY-14's scorer has exercised its
PASS path** — until now it had only ever been driven against the broken state.

The widening is deliberately minimal: `blob:` URLs are minted by the page's own scripts and are opaque
origins a third party cannot forge, so allowing them **for images only** admits no external content. It is
NOT added to `script-src` or `default-src`, and a new regression test fails if a later edit puts it there.

Regression pin: `src/tests/regression/test_csp_plotly_image_export.py` (canopy), five tests, deliberately
SEPARATE from `test_csp_bootstrap_cdn.py` because the two `img-src` allowances exist for unrelated
consumers. Against the parent it is **2 failed / 3 passed** — the three that pass are the guards
(`data:` preserved, widening minimal, no wildcard), which must hold either way.

*Original note, kept because the reasoning still applies to whoever next touches this directive:* the fix
shape was narrow — adding `blob:` to `img-src` restores the export. That is a security-header change and belongs to whoever owns the CSP posture, and the
Bootstrap-driven history of this directive suggests it should be widened deliberately rather than
casually. A regression test pinning `blob:` alongside the existing `data:` assertion is the cheap half.

---

**F-CANOPY-046 — clicking empty space cannot clear the selection: plotly emits `plotly_click` only for POINT hits, so `clickData` never changes and the clear path is unreachable by that gesture (P2; found 2026-09-02 by the new `topoevents` scorer; FIXED canopy#573, merged 2026-09-04).**

`handle_node_selection` ends with `return [], [], hidden_style` — the "no valid selection, clear" path
the matrix cites for M-TOPOLOGY-12 — and the panel's own text tells the user *"(Click again or elsewhere
to deselect)"*. But the callback's only click Input is `-graph.clickData`, and **plotly emits
`plotly_click` only when a POINT is hit.** A click on genuinely empty canvas produces no event, so
`clickData` does not change, the callback (`prevent_initial_call=True`) never runs, and the selection
stands.

**MEASURED, and the row diagnoses itself** rather than leaving the reader to guess which half failed:

```
M-TOPOLOGY-12 click empty space: cleared=False plotly_click_events=0 -> FAIL
```

Two consecutive runs, identical. `plotly_click_events=0` is the whole finding: this is not "the handler
ran and failed to clear", it is **no event to clear on**. The distinction matters because the two have
different fixes — the handler is fine.

**Clicking the same node again DOES deselect** (pinned by `test_clicking_the_same_node_again_deselects`),
so the feature is reachable; it is the *"or elsewhere"* half of the app's own instruction that is not.

**Not caused by canopy#564, and worth stating because the timing invites the inference.** Before #564 a
click on an EDGE reached the clear path (edge points have no `text`, so the guard fell through to
`return [], [], hidden_style`), and #564 makes such a click select instead. But that path was never
"click empty space" — it was "click an edge", and it only mattered once something could be selected at
all, which before #564 nothing could. The empty-space gesture has produced no event on either build.

**Fix direction NOT asserted.** A `plotly_relayout`/`plotly_deselect` Input, or a container-level click
handler, would each reach it; both add a trigger to a callback family this arc has repeatedly starved
(F-CANOPY-037 / -039 / -043), so the cost needs measuring before choosing.

---

**A SECOND COST UNDER THE SAME ID, found reading the code to write the fix brief
(`JUNIPER_2026-09-04_JUNIPER-CANOPY_F042-F046-FIX-DECISION-BRIEF.md`), and part of no proposed option.**

The clear path wrote `[]` **unconditionally**. `-selected-nodes` is a real Input of
`update_network_graph`, and Dash fires every consumer of a store on *any* write, identical or not — the
property canopy#542 had to suppress for the topology store. So **failing** to clear an already-empty
selection bought a full 1.5–31 s rebuild: the waste class of F-CANOPY-037 / -039 / -043, reached by the
most ordinary gesture there is (a click that lands on nothing).

**FIXED AND VERIFIED LIVE (canopy#573, merged 2026-09-04), and the fix does NOT implement the gesture.**
The decision (D4 = B1 + B2) was to make the panel's text true *and* ship a control:

- a **"Clear selection" button**, wired as an **Input** to the selection callback (the click on it *is*
  the trigger) and revealed by a fourth Output only while something is selected;
- the click branch keeps `"(Click again to deselect)"` — that half was always true, via the toggle
  branch, and dropping it would lose a working gesture. `"or elsewhere"` goes;
- the box branch loses its hint **entirely**: no click gesture clears a box selection, so there is no
  true sentence to write there;
- both clear paths return `dash.no_update` when the selection is already empty.

A clientside listener on the graph container (B3) would literally satisfy the old sentence and was
rejected: it races plotly's own event path, in the callback family this arc keeps starving.

**A/B on the same 2/40/2/944 fixture, minutes apart** — a second canopy on `:8052` from the fix branch
beside the arc's `:8051`, same cascor and juniper-data, so the only difference is which code the process
imported (`util/ad-hoc/2026-09-04_canopy_verify_instance.bash`):

| row | `:8051` parent | `:8052` fix branch |
|---|---|---|
| M-TOPOLOGY-12 | `control={present:False, visible:False}`, `cleared=False` → **BLOCKED** | `control={present:True, visible:True, clicked:True}`, `cleared=True` → **PASS** |
| empty-space click *(recorded, not scored)* | `plotly_click_events=0`, `cleared=False` | `plotly_click_events=0`, `cleared=False` |
| `--step topoevents` total | 3 PASS / 1 BLOCKED | **4 PASS / 0 BLOCKED** |

**The empty-space row is identical on both builds, and that is the point.** The fix withdraws a claim
rather than implementing a gesture. **M-TOPOLOGY-12 was restated in the same pass** — from *"click empty
space, selection clears"* to *"a selection can be cleared"* — because scoring a deliberately withdrawn
promise as a product FAIL forever would be measuring the matrix, not the app. The empty-space click is
**kept and still counted**: it is the evidence for why the contract changed, and a future build that
does wire a container-level listener should show up there as a behaviour change rather than as silence.
A build with no control now scores **BLOCKED**, not FAIL — a product without the affordance cannot be
asked whether its affordance works. Same three-state discipline as the `{ok, value, via}` readers.

**Unit coverage**: `src/tests/unit/frontend/test_f046_clear_selection.py` (canopy), 17 tests, all
reaching the real callback. **16 of 17 fail against parent**, each for its own reason — the harness
builds its argument list from the callback's *actual* signature, deliberately, so the falsification does
not collapse into a single arity error that would prove only that the signature changed. Parent's
failures name the real strings, including
`'Selected: Hidden 0  Layer: Hidden  (Click again or elsewhere to deselect)'`.

**Two assertions were vacuous on the first falsification pass and were tightened.** An Output the build
does not return reads as `None` in that harness, and `None != "none"` is **true** — so
`assert clear_style.get("display") != "none"` passed against a build with no button at all. They now
assert a positive display value. This is the fourth instrument in this arc that was well-formed and
answering an adjacent question.

**Adding an Input changed the callback's arity, and a grep for the symbol name found only ONE of the
three files that invoke it.** `test_network_visualizer_callbacks.py` and
`regression/test_dark_mode_info_panels.py` locate the callback by its **Output key**
(`f"{component_id}-selected-nodes.data"`) and never mention `handle_node_selection`, so they were
invisible to the audit and were caught by the full suite instead — one of them only on the *second*
run. **When a callback's signature changes, grep the Output key as well as the symbol.**

---

**M-TOPOLOGY re-drive, 2026-09-02 post-#561: 9 PASS / 0 FAIL — and the prior 5 PASS / 4 FAIL was measured against code that was never loaded.**

`/tmp/juniper-e2e/seg17_postf561_A.json` (archived under `reports/e2e-canopy-2026-09-02/`), all nine
scored rows PASS: M-TOPOLOGY-01, -02, -03, -04, -05, -06, -07, -08, -17.

**Why the earlier run disagreed, which is the durable part.** The canopy leg serving `:8051` had been
running since **2026-09-01 15:39:34**. canopy#558 merged into the primary checkout at 12:42 that day and
**canopy#561 at 2026-09-02 16:14** — but *Python reads the source at import*. The process kept serving
its 2026-09-01 image for another day. Every measurement taken in between was attributed to the checkout's
HEAD and actually came from code up to 28 hours older.

That accounts for the whole 5-vs-9 gap without any product change: M-03 failed on F-CANOPY-041b (not
resident yet), -04 and -05 cascaded from M-03's empty graph, and M-02 lost its race. Relaunching the leg
from the up-to-date primary and re-driving the same step returned 9 PASS.

**A CHECKOUT IS NOT A DEPLOYMENT.** This is a distinct vacuous-measurement class from the ones already
registered here: nothing was broken, no check was tautological, and the run was honest about what it
saw — it simply measured a *different build* than the one being reasoned about. The two guards now in
`util/ad-hoc/e2e_f039_relaunch_canopy.bash`:

1. it **stops the previous leg by pid** before launching. Without that, the newcomer fails to bind, the
   health probe is answered by the OLD process, and the script prints `canopy healthy` and exits 0 while
   the change under test is not loaded — a vacuous pass that is invisible downstream;
2. after the health probe returns 200 it **confirms the pid it launched is still alive**, so "something
   serves :8051" can never be mistaken for "the thing I started serves :8051".

**Consequence for the arc:** every row verdict carries not only a timestamp but a *build*. When a run's
result is surprising, check the serving process's start time against the merge time of the fix it is
supposed to exercise before re-opening the finding.

---

**F-CANOPY-041 — the Weight Matrix heatmap raised ValueError -> HTTP 500 from 26 hidden units upward (P1; found 2026-09-01 by fixing F-CANOPY-040 first; canopy#558 did NOT fix it — see F-CANOPY-041b below; FIXED canopy#561, merged 2026-09-02T19:22Z, and CONFIRMED LIVE 2026-09-02 — see F-CANOPY-041b).**

> **DISPOSITION CORRECTED 2026-09-02. This entry said FIXED for a day and was wrong.**
> canopy#558 removed the HTTP 500 and replaced it with a **silent blank canvas**, which is worse: the
> 500 was visible. Clamping `vertical_spacing` **to** `1/(n_rows-1)` is clamping to the value at which
> the inter-row gaps consume the entire figure, so every row renders at zero height. Measured on the
> real `_create_weight_heatmap`: `min_row_h=0.000000`, `total_plot_area=0.0000` at 25 / 26 / 40 / 80
> hidden units, and only **4%** plot area at 24 — degradation begins well before the stated boundary.
>
> **Three checks certified the blank, and that taxonomy is the durable part:**
> 1. #558's regression test was a **tautology** — `assert min(desired, limit) <= limit` is true for every
>    input, never called the function, and could not fail for any implementation;
> 2. its sibling asserted only `len(fig.data) > 0`, satisfied by zero-height traces;
> 3. **M-TOPOLOGY-03's driver predicate** was `any(type == "heatmap")`, so the row **PASSED on the
>    blank** — confirmed live afterwards at `plot_area=0, n_yaxes=41`.
>
> Found by an adversarial reviewer under the independent-agent consensus procedure, running the
> production function rather than reading the diff. **Every check that existed at merge time was blind
> to it.**

---

**F-CANOPY-041b — canopy#558's clamp renders every heatmap subplot at ZERO height from 25 hidden units up (P1; found 2026-09-02 by adversarial review of the F-041 fix; FIXED canopy#561, merged 2026-09-02T19:22Z; CONFIRMED LIVE 2026-09-02).**

> **LIVE CONFIRMATION, 2026-09-02** (`/tmp/juniper-e2e/seg17_postf561_A.json`, archived under
> `reports/e2e-canopy-2026-09-02/`). canopy#561's arithmetic had only ever been checked by unit test;
> the handoff recorded "canopy#561 is correct beyond its unit tests — it has not been driven live" as an
> explicit evidence gap. It has now been driven:
>
> ```
> M-TOPOLOGY-03 weight matrix: heatmap=True plot_area=0.7 n_yaxes=41 types=[6x heatmap] conn='—'
> ```
>
> `plot_area = 0.70` at 40 hidden units is exactly the figure canopy#561 predicted, measured through the
> browser against the live 2/40/2/944 fixture rather than by calling the function. **Gap closed.**
`min(desired, 1/(n_rows-1))` returns exactly the limit for every `n_rows >= 26`. canopy#561 reserves plot
area instead (`GAP_BUDGET = 0.30`), giving a **floor** of 70% plot area on tall cascades:

| hidden | #558 min_row_h / plot_area | #561 min_row_h / plot_area |
|---|---|---|
| 24 | 0.001538 / 0.0400 | 0.026923 / 0.7000 |
| 25 | **0.000000 / 0.0000** | 0.025926 / 0.7000 |
| 40 | **0.000000 / 0.0000** | 0.016667 / 0.7000 |
| 80 | **0.000000 / 0.0000** | 0.008537 / 0.7000 |

**Correction to canopy#561's own wording**, caught in review and recorded rather than quietly fixed: the
PR says short cascades keep "exactly their previous appearance" and the handoff said "70% at every
depth". Both are false in detail — at `n_rows = 5` and `9` the budget binds and plot area moves
0.68 -> 0.70, and small depths sit at 92 / 84 / 76 / 80 / 76 / 72%, above the 70% floor. The direction is
benign (more plot area everywhere, no regression at any depth), but the universal claim was wrong.

`M-TOPOLOGY-03`'s predicate now also requires `plot_area >= 0.05` (`fig_info` gained `plot_area` /
`n_yaxes`), so the row can no longer certify a blank. **Residual, unfixed:** that row's `wait_for` is
still the bare `any(type == "heatmap")` and is satisfiable by a blank, and `area_ok` treats a missing
measurement as passing.
`make_subplots` enforces `vertical_spacing <= 1 / (n_rows - 1)`; `_create_weight_heatmap` passed a fixed
`0.08 if n_rows <= 5 else 0.04` with no reference to that constraint. One row per hidden unit plus one
for the output weights puts the boundary at **26 hidden units**:

| hidden | n_rows | spacing | plotly limit | |
|---|---|---|---|---|
| 25 | 26 | 0.040 | 0.0400 | fits, exactly |
| 26 | 27 | 0.040 | 0.0385 | **ValueError -> 500** |
| 40 | 41 | 0.040 | 0.0250 | **ValueError -> 500** |

The view did not degrade on a tall cascade — it **broke**, 500ing on every poll tick, with repeated
"Failed to load resource: 500" in the browser console.

**THE ORDERING IS THE FINDING.** F-CANOPY-040 and F-CANOPY-041 present the *identical* symptom —
M-TOPOLOGY-03 reporting `heatmap=False types=[] conn='—'`. While the store was never populated,
`_create_weight_heatmap` was never reached with real data, so this crash **could not occur**. Fixing the
outer defect is what made the inner one visible. **canopy#557 was necessary but NOT sufficient: M-03
still failed after it, and only passed after canopy#558.** Two stacked causes behind one symptom.

Two reasons it stayed hidden: the service default `max_hidden_units` is 10, well under the boundary; and
F-CANOPY-040 meant nothing rendered regardless. It took a deliberately tall (40-unit) fixture to surface.

---

**M-TOPOLOGY RE-DRIVE (2026-09-01) — 7 of 9 PASS; the 2 failures are HARNESS, not product.**
Driven three times against a live 2/40/2/944 network, canopy `a3dad69` then `30e15b7`. Verdicts were
byte-stable across runs (same baseline 1891 traces / `sig=314447` every time).

| row | verdict | note |
|---|---|---|
| M-TOPOLOGY-02, -04, -05, -07, -08, -17 | **PASS** | unblocked by F-CANOPY-039 |
| M-TOPOLOGY-03 | **PASS** | only after BOTH canopy#557 and canopy#558 |
| M-TOPOLOGY-01 | FAIL — **harness** | see below |
| M-TOPOLOGY-06 | FAIL — **harness** | see below |

**M-TOPOLOGY-06 is not a defect.** `_apply_hierarchy_filter` was exercised directly:
`depth=20 -> hidden_units=20, label='20 of 40', conns=20`. The filter is correct; the driver's
number-input write never reached Dash state (the documented keystrokes-don't-land trap).

**M-TOPOLOGY-01 is not a defect either, and it has TWO harness causes.** All four layouts produce
genuinely distinct coordinates, verified by calling `_calculate_layout` directly for each
(`hierarchical`/`staggered`/`spring`/`circular`, all six pairwise comparisons `identical=False`). So:

- **`sig` is `JSON.stringify(gd.data).length`** (`util/ad-hoc/e2e_f027_redrive.py:161`) — a LENGTH proxy,
  not a content hash. Hierarchical and Spring collided at 314447 despite different layouts, which is why
  `distinct_sigs` wobbled 3 -> 2 -> 3 across runs while `driven` never moved. **Equal sigs do not prove
  an unchanged figure.**
- **`set_dropdown` fails on "Staggered"** (`driven=False` every run).

The verdict requires `len(sigs) == 4`, which **cannot be satisfied while Staggered will not drive** — the
row is unpassable by construction as the driver is written. That is the same shape as canopy#537's
unfireable guard and F-CANOPY-040's gate: **the third "condition that can never be true" this session.**
Both rows stay BLOCKED, attributed to the harness rather than scored FAIL against the product.


---

**F-CANOPY-039 — the topology rebuild's response is provably CORRECT on the wire and the DOM never applies it; this, not starvation, is what blocked the topology block (P0/P1; found 2026-08-28 during the F-CANOPY-037 post-fix re-drive; root-caused in dash-renderer's own source and FIXED 2026-08-31 by canopy#549, censused 0-of-11 -> 11-of-11 at idle scope).**
Operator loop (apply / soak / report / revert; read the whole series): [`docs/REFERENCE.md` § F-039 Store Probe](../docs/REFERENCE.md#f-039-store-probe).
Measured on the isolated trio (data 8101 / cascor 8202 / canopy 8051, service mode; cascor `a709d52`,
canopy `6b55399`) against a **completed 10-unit network whose server truth is byte-identical to the one
F-CANOPY-037 was found on** — `GET /api/topology` = `2 / 10 / 2 / 89`, 14 nodes.

**What the wire shows.** `e2e_seg17_topology_driver.py --step rebuildprobe`: the rebuild fires and every
response is **HTTP 200, 39,319 B, ~206 traces, `empty_fig=False`** — the same byte size F-CANOPY-037
recorded for its two *successful* sessions. **What the DOM shows, at the same moment:** `gd.data` empty,
`sig=2`, `traces=0`, stats bar `0 / 0 / 0 / 0`. The correct figure arrives and is not applied.

**Zero errors anywhere.** The canopy log carries no callback errors and no topology-fetch warnings (the
only ERROR lines are the benign pre-run `No network created` ones at bring-up), and the browser console
emits **no error or warning** — `open_dashboard` wires console capture and nothing fired.

**This is the F-CANOPY-006 signature** — "a provably-correct server render is silently never applied
client-side" — which F-CANOPY-037's entry asserts is "genuinely fixed: when the rebuild runs here, the
DOM *does* apply it". **Stated carefully: the conditions differ from that measurement and the difference
is not yet explained.** F-037 saw the DOM apply in 2 of 11 sessions; this re-drive saw it apply in **0 of
6** across *two different canopy builds*. Something about this environment is not the environment that
produced the 2-of-11, and until that is identified this should not be recorded as "F-006 regressed".

**It is NOT a regression from the 2026-08-27/28 merges — A/B measured, not assumed.** A second canopy leg
was stood up on `:8052` from **pre-merge `9f6fac9`**, pointed at the *same* cascor and the *same* network,
and driven with `JUNIPER_E2E_CANOPY_URL`. It fails **identically**: `painted=False after 241.8 s`,
`sig=2`, `counts 0/0/0/0`. So none of canopy#531/#532/#533/#534/#535 caused it.
(Harness: `util/ad-hoc/e2e_f037_ab_premerge_leg.bash`.)

> **ALL FOUR CANDIDATE EXPLANATIONS RULED OUT (2026-08-28, `util/ad-hoc/e2e_f039_dom_apply_probe.py` and
> `e2e_f039_reset_target.py`). The failure is localised to dash-renderer applying the prop.**
>
> The DOM probe joins "a rebuild response landed" to "did `gd.data` change?" on **one event**, rather than
> two independent polls that can each be wrong, and reports the whole element state at that instant.
> Across **9 responses of 39,319 B each: 0 changed the DOM.** At the same instants:
>
> | candidate | measured | verdict |
> |---|---|---|
> | duplicate / detached graph element | `n_elements_with_graph_id` = **1**, attached | ruled out (static check also 464 ids / 464 distinct) |
> | hidden or unlaid-out pane | `hidden_by` = **None**, rect **1102x600** | ruled out |
> | plotly never initialised | `_fullLayout` present, modebar present | ruled out |
> | `RESET_COMPONENT_STATE` wiping it (F-CANOPY-033) | **0 of 40** resets at-or-above the graph's itempath | ruled out |
>
> So: a single, attached, visible, correctly-sized, fully-initialised plotly instance receives nine correct
> 39 KB figures and holds `gd.data == []` throughout. **What remains is the renderer step between "response
> received" and "prop applied"** — which is precisely where F-CANOPY-006 lived.
>
> **Instrument note, because it nearly became a finding.** The first version of the DOM probe read
> `_fullLayout` off the element carrying the id and reported `plotly_inited: false` — i.e. "plotly never
> rendered this graph at all", a completely different and much more dramatic diagnosis. `dcc.Graph(id=X)`
> renders a **wrapper** div with that id; the plotly instance lives on an inner `.js-plotly-plot`, which is
> how the driver's own `fig_info` resolves it. Corrected, it reads `true`. **Resolve a `dcc.Graph` through
> `.js-plotly-plot` before reporting anything about its plotly state.**
>
> **CONSTRUCTIVE TEST — the component is HEALTHY, so the defect is Dash's response application.**
> `util/ad-hoc/e2e_f039_setprops_graph.py` writes the `figure` prop BY HAND through the component's own
> Dash-supplied `setProps` (`memoizedProps.setProps`, 29,671 fiber hops): `traces 0 -> 1`, `sig 2 -> 87`,
> `names=['F039-PROBE']`. **The graph renders a hand-written figure immediately and correctly.**
>
> So every half of the path is individually proven sound — the server produces a correct 39 KB figure, the
> transport delivers it at HTTP 200, the target component accepts and renders `figure` on demand — and the
> only remaining link is **dash-renderer writing the callback response into that prop**. That is
> F-CANOPY-006's mechanism exactly, now established constructively rather than by elimination.
>
> **A sixth candidate, also ruled out: an unresolvable sibling output.** `update_network_graph` is an
> **8-output** callback, and a renderer that cannot resolve one output's path can fail to apply the whole
> batch — which would present precisely as "correct response, healthy component, nothing changes". All
> seven distinct output ids (`-graph`, the four `-*-count`s, `-topology-hash`, `-new-node-highlight`)
> resolve in `paths.strs`; `rebuild_outputs_missing` is **empty**. Checked with
> `util/ad-hoc/e2e_f039_state_shape.py`.
>
> **RENDERER TRACE — the lifecycle COMPLETES and the value is never dispatched.**
> `util/ad-hoc/e2e_f039_renderer_apply.py` wraps `store.dispatch` and joins it to response arrival. In
> 60 s: **7 rebuild responses carrying the graph, 5,556 redux actions, 126 of them naming
> `network-visualizer-graph`.** The callback's whole lifecycle is present and correctly pathed —
> `Callbacks.AddRequested` → `LOADING` → `Callbacks.RemovePrioritized` / `RemoveExecuting` →
> `Callbacks.RemoveExecuted` → `LOADED` — and both `LOADING` and `LOADED` carry the *exact* itempath from
> `paths.strs`. Dash knows precisely which component and which prop.
>
> **And no dispatched action carries the figure.** Every action naming the graph is ≤23 KB and is
> lifecycle bookkeeping (the callback descriptor is itself large — 12 Inputs, 8 Outputs); the 39,319 B
> payload never enters the store. So the callback is requested, marked loading, executed, marked loaded,
> and **the apply step in between simply does not happen**. That is F-CANOPY-039 stated at its narrowest.
>
> **Hypothesis worth testing next, NOT yet established: supersession.** `Callbacks.RemoveRequested` fires
> for this callback, and a response whose invocation has already been removed from the requested set is
> discarded rather than applied. That is the same *class* as F-CANOPY-037 — an in-flight rebuild
> superseded before it can land — one layer lower: not the Input being re-claimed, but the queued
> invocation being retired. The rebuild's server time is 1.5-5 s and its surviving trigger,
> `tabpoll-topology`, ticks every 5 s, which is uncomfortably close. It would also explain why the
> post-fix rate is *more* deterministic (0 of 6) than the pre-fix 2 of 11: with the 1 Hz store gone, every
> invocation now comes from the one cadence that races it.
>
> **Discriminating test:** raise `tabpoll-topology`'s interval (or lower the rebuild's cost) and re-run the
> census. If the graph paints, supersession is confirmed and the fix is a cadence/`no_update` guard rather
> than anything in the component. Do this before reading dash-renderer's source — it is far cheaper and it
> falsifies the hypothesis outright if wrong.
>
> ---
>
> ## ROOT CAUSE (2026-08-28) — the STORE never lands, and the graph was never the defect
>
> **The supersession hypothesis above is WRONG, and two fixes built on it were tested live and reverted
> rather than shipped.** Recorded in full because the reasoning was plausible at every step and still
> ended in the wrong place.
>
> ## THE CENSUS THAT CONDEMNED THESE FIXES DOES NOT SUPPORT THE CONCLUSION DRAWN FROM IT (2026-08-30)
>
> Re-read under the independent-agent consensus procedure
> (`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`): 3 measurement agents
> with distinct entry points (ledger text / git+PR history / raw evidence tree), 2 adversarial analysis
> agents with opposing briefs, every load-bearing single-sourced claim re-derived by the reconciler.
>
> **1. "0 of 1" is not a census.** It is ONE session
> (`reports/e2e/_recovered/.../single_session_runs/f039_fix_check.json`, 534 B) that never went through
> `util/ad-hoc/e2e_f037_render_census.py` at all. That tool's own header says a fix **"CANNOT be validated
> by one session"**, and `DEFAULT_SESSIONS = 11` carries the comment *"2/11 vs 11/11 is a claim, 2/11 vs
> 1/1 is not."* The suppression was discarded on exactly the sample size the tool exists to forbid.
> **"0 of 2" is n=2.** No artifact for either was ever committed; both survived only as orphaned `/tmp`
> tempfiles, now recovered to `reports/e2e/_recovered/20260828_census_artifacts/`.
>
> **2. Neither census can be tied to a build — PARTIALLY REVERSED, see the teardown recovery below.** The `:8051` leg log shows 16-line session bursts at each
> 0-of-5 census timestamp, and **exactly one line per minute** (heartbeat only) through the 0-of-2 and
> 0-of-1 windows. Those runs drove a second leg whose log a truncating `nohup >` redirect destroyed.
> **Nothing establishes that the code under test contained either fix.**
>
> **2b. RECOVERED AT TEARDOWN (2026-08-30) — the provenance was NOT destroyed, and finding 2 above is
> too strong.** The claim rested on `/tmp/juniper-e2e/juniper-canopy-ab.log` having been truncated by a
> `nohup >` redirect. That file was truncated. But **each arc worktree kept its own `logs/system.log`**,
> ignored by git and therefore invisible to every search the measurement round ran — and about to be
> deleted by `git worktree remove`, which does not respect `--porcelain`'s blindness to ignored files.
>
> `fix/f039-stale-shortcircuit`'s copy (433,745 B) records **7 server starts**, including
> `:8052` at **19:25:05** and again at **19:37:28**, with request bursts at **19:30** and **19:34** (the
> two 0-of-2 census sessions), **19:37** (30 lines) and **19:42** (36 lines). So a second leg *was*
> restarted between the census runs, which is consistent with different builds being loaded and is more
> than the record previously held.
>
> **This does not rescue the census** — the log still does not name a commit, so *which* build each run
> drove remains unestablished, and findings 1, 3, 4 and 5 are untouched. But "no artifact establishes
> it" was wrong; the correct statement is "no artifact NAMES the build, though the leg restarts are now
> visible". All seven worktree logs (2.3 MB) are preserved under
> `reports/e2e/_recovered/20260827-28_arc_worktree_leg_logs/`.
>
> **The methodological point is the durable one.** Three measurement agents, two adversarial agents and
> a reconciler all searched for this evidence and all missed it, because every one of them searched
> tracked files, `/tmp`, and git objects — and this lived in an ignored directory inside a worktree
> queued for deletion. **`git status --porcelain` is blind to ignored files, and `git worktree remove`
> deletes them.** Harvest ignored `logs/` before any sweep; the sweep is where evidence dies.
>
> **3. The stated rationale is false against the artifact it cites.** canopy#537's body justifies the
> revert with *"its comparison can never fire while `current` is always the empty default."* The cited log
> is **11 `eq=True` in 15 samples** — the comparison fired, and returned equal, 73% of the time. This is
> the same head-of-log misreading corrected elsewhere in this entry, except here it was load-bearing for a
> discard decision.
>
> **4. The suppression's source was never staged and is unrecoverable** — no branch, commit, stash,
> worktree, backup, dangling object, or loose object in the window. Reinstating means rewriting from a
> twelve-word description, so its next measurement is not comparable to the 0-of-1.
>
> **5. The configuration the mechanism predicts would work has never been run.** The short-circuit branch
> touches only `network_visualizer.py` and its test — `dashboard_manager.py` is untouched in all four of
> its commits — and the primary checkout sat at `27af847` (no short-circuit) throughout the suppression's
> test window. Short-circuit shipped alone; suppression was tested alone; **the pair has never been
> tested together.**
>
> ### Where the two adversarial briefs each proved weaker than they looked
>
> **Against the revert — "the census was underpowered" is much weaker than it first appears.** P(0 painted
> | no effect) ≈ 82% at n=1 assumes a *stochastic* null at p=2/11. But the current regime is **0 of 6
> across two canopy builds** with identical deterministic signatures (`sig=2`, `counts 0/0/0/0`, full
> 240 s budget), and this ledger already notes the post-fix rate is *more* deterministic than 2/11. Under
> a deterministic failure n=1 carries far more information than that arithmetic implies. **The baseline
> the arithmetic is computed against also has no surviving artifact** — the census tool postdates the
> "2 of 11" claim by two days and cannot have produced it.
>
> **For the revert — "the store write demonstrably works" does not survive inspection.** The brief's
> strongest point is that `depth-slider.max` reads **10** against a layout default of **0** in all ten
> recovered failing sessions, and its only writer takes the topology store as its sole `Input` — so the
> write reaches the client. True, and verified. **But that writer is `app.clientside_callback`
> (`network_visualizer.py:706`) — it runs in the browser with no round trip**, whereas the rebuild is
> `@app.callback` (`:332`), server-side at 1.5-5 s. A fast clientside consumer landing while a slow
> server consumer does not is *what supersession predicts*. The observation is consistent with the
> hypothesis it was offered against.
>
> **Also for the revert, and also overstated** — that the blocked rows test a *growing* cascade, where a
> suppression that "only helps at idle" would be inert. In fact **15 of the 16 blocked M-TOPOLOGY rows are
> static control rows** (layout selector, show-weights, display mode, view mode, depth slider, stats bar,
> graph interactions), testable on a completed network — the idle regime where the lever bites hardest.
> Only M-TOPOLOGY-16 (cascade-add glow) requires growth.
>
> **Against the revert, and also weaker than argued** — that the identical fix is already shipped on the
> sibling store, so the codebase ratified the principle. It shipped
> (`dashboard_manager.py:6783-6790`, whose comment names "the 8-output topology renderer" as a harmed
> consumer) — **but it is INERT**: F-CANOPY-038 measured **zero** `no_update` in 32 writes, and the
> 2026-08-29 metrics probe explains why (`current_metrics` is always `[]`, so the comparison is always
> False). The precedent is a fix that never fires. *Note the asymmetry that makes the topology case
> different, and better:* the topology store's client copy **converges** (11 of 15 `eq=True`), so a
> suppression there **would** fire — the probe log is direct evidence its precondition held on 11
> consecutive ticks.
>
> ### Disposition
>
> **The revert is not supported by its evidence, and the supersession hypothesis is NOT refuted.** It was
> discarded on one session, against an untraceable baseline, on a build that cannot be identified, for a
> stated reason that its own cited artifact contradicts.
>
> **This is not licence to reinstate.** The implementation is gone, so any reinstatement is a rewrite; and
> the newest instrumentation (see the OVERTURNED block) shows the rebuild receiving correct data and its
> response never being applied, which supersession explains but does not uniquely explain — a pure
> dash-renderer apply failure fits equally, and the one runtime manipulation that discriminates them
> (disabling `tabpoll-topology`) is itself n=1.
>
> **The owed experiment is specific:** rewrite the suppression (five edit sites — `dashboard_manager.py`
> `:3924` add the `State`, `:3959`/`:3966` thread it as `current=`, `:6797` extend the signature, `:6829`
> add the guard), run it **together with #537's short-circuit** — the pair never yet tested — at
> **N >= 11**, and record the canopy commit in the census artifact, which no census in this arc has ever
> done.
>
> **Correction of record:** the sentence below says both fixes were "reverted rather than shipped". The
> short-circuit **shipped** — `c0c873c` is an ancestor of canopy `main` (canopy#537, merged 2026-08-29).
> Only the suppression was reverted.
>

> The discriminating test *appeared* to confirm supersession: disabling `tabpoll-topology` at runtime made
> the graph paint immediately (traces 0 -> 181, sig 2 -> **31152**, byte-identical to F-CANOPY-037's two
> painting sessions). But two fixes derived from it both failed a live census — the stale-identifier
> short-circuit (0 of 2) and a no-op-write suppression on the topology store (0 of 1).
>
> **What settled it was logging the comparison's operands server-side** — the probe F-CANOPY-038 has been
> asking for. Every tick, on every sample:
>
> ```
> TOPOPROBE eq=False cur_type=dict cur_len=75 new_len=7059 canon_eq=False
> TOPOPROBE   differs key='input_units'  cur=0  new=2
> TOPOPROBE   differs key='hidden_units' cur=0  new=10
> TOPOPROBE   differs key='connections'  cur=[] new=[{'from': 'input_0', ...}]
> TOPOPROBE   differs key='nodes'        cur=None new=[{'id': 'input_0', ...}]
> ```
>
> **CORRECTION (2026-08-29) — the paragraph below was wrong, and its error made the finding LOOK weaker
> than it is.** It read the head of the probe log and generalised. Re-running the (now re-runnable)
> reporter over the WHOLE 35-line log gives:
>
> ```
> 4 samples  19:43:17 → 19:43:33   eq=False  cur_len=75    new_len=7059
> 11 samples 19:43:39 → 19:44:28   eq=True   cur_len=7059  new_len=7059
> ```
>
> One continuous 71 s window, no restart. **The client's copy is empty for ~22 s, then CONVERGES to the
> correct 7,059-byte topology and stays correct for the remaining 49 s.** It is not "permanently empty" and
> it does not "never advance".
>
> **This strengthens the duplicate-store hypothesis rather than weakening it, and it is now supported from
> BOTH sides**: the probe proves the value the store's WRITER sees is correct and stable for 11
> consecutive ticks, while the rebuild's `input_units == 0` fast path proves the value its READER sees is
> empty over the same window. **Two different values for the same store id, simultaneously.** That is the
> duplicate-instance signature, and it is no longer an inference from absence — it is a direct
> contradiction between two measurements taken at the same time on the same running app.
>
> It also means the "one defect" deduction filed against F-CANOPY-038 must NOT lean on a
> "client copies never advance" analogy: this store's client copy demonstrably does. See that entry's
> correction.
>
> ~~**The CLIENT's copy of `network-visualizer-topology-store` is permanently the 75-byte empty default**,
> while the server returns the correct 7,059-byte topology every 5 s. It never advances — not once, across
> every tick of every session.~~
>
> ## OVERTURNED BY DIRECT MEASUREMENT, 2026-08-30. Read this before the paragraph below.
>
> The paragraph below concluded that the rebuild "is not failing to apply anything" and is "faithfully
> rendering an empty topology, because that is what it is given". **Both halves are false.** It was an
> inference from the store's contents, never a measurement of the callback. The callback has now been
> instrumented directly (`util/ad-hoc/e2e_f039_rebuild_instrument.py`), on the live trio, while the
> failure was reproducing (`traces=0`, counts `0/0/0/0`, 3/3 samples):
>
> ```
> 8 invocations of update_network_graph
>  1 x  td_len=75    input_units=0  takes_empty_path=True    <- MOUNT ONLY
>  7 x  td_len=7059  input_units=2  takes_empty_path=False   <- every subsequent tick
> ```
>
> **The rebuild RUNS, RECEIVES the correct 7,059 B topology, and does NOT take the empty fast path** —
> seven times out of eight — while the DOM keeps showing the mount-time empty render. So the response is
> computed correctly and **never applied**. That is the original F-CANOPY-039 statement, which this entry
> abandoned on the strength of a store reading rather than a callback reading.
>
> **The duplicate-instance hypothesis this entry built up is also refuted** (`util/ad-hoc/
> e2e_f039_duplicate_store_probe.py`): exactly ONE instance of `network-visualizer-topology-store` on all
> three tabs, and one each of `metrics-panel-metrics-store`, `ws-metrics-buffer`,
> `metrics-panel-display-mode-store` and `ws-liveness-store` — the last three carried as controls
> precisely so that an all-duplicated result would read as the probe measuring itself.
>
> **The trigger list is the mechanism, and it is visible in every one of the seven:**
>
> ```
> triggered=['tabpoll-topology.n_intervals',
>            'network-visualizer-topology-store.data',
>            'network-visualizer-depth-slider.value']
> ```
>
> The topology poll rewrites an IDENTICAL 7,059 B payload every 5 s, and Dash fires consumers on any
> write, identical or not. So the store re-triggers the rebuild on every tick; it is never a *bare* tick,
> which is why canopy#537's short-circuit correctly does not fire; and each invocation is superseded
> before its response can land. That is also why disabling `tabpoll-topology` at runtime made the graph
> paint instantly (traces 0 -> 181): it stopped the supersession, not "the empty-store invocations".
>
> **This points back at the no-op-write suppression on the topology store that this arc built and
> REVERTED** for failing a live census. Do not simply reinstate it: the census that condemned it was read
> under the same wrong premise, so *that reading* needs re-examining first. But it is now the leading
> candidate rather than a discarded one.
>
> Evidence: `reports/e2e/20260830T000000Z/f039_dupstore/` (duplicate-store probe JSON, and two
> render-state runs taken with the rebuild instrumented and un-instrumented).
>
> ## THE THIRD TRIGGER HAS A SOURCE, AND IT MAKES canopy#537 STRUCTURALLY DEAD (2026-08-30, from source)
>
> Derived by reading the declarations, no stack required. The trigger list above has three entries and
> this entry has been attributing all three to the store write. **`depth-slider.value` has its own causal
> path**, and naming it settles a question this arc has been treating as statistical.
>
> The slider's clientside bounds-sync (`network_visualizer.py:706-738`) takes
> `network-visualizer-topology-store` as its **only** Input, and its return array re-emits
> `depth-slider.value` **unconditionally** (`:731-736`) — including when the value is unchanged. So the
> store's own write manufactures a second consumer trigger, which arrives back at the rebuild as Input #7
> (`:347`). The full cycle:
>
> ```
> update_topology_store  (dashboard_manager.py:3924/:6797)   identical 7,059 B every 5 s
>    |-> update_network_graph                                 [trigger 2: topology-store.data]
>    \-> clientside slider-sync (network_visualizer.py:706)
>           \-> depth-slider.value := 2 (unchanged, still fires)
>                  \-> update_network_graph                   [trigger 3: depth-slider.value]
> tabpoll-topology.n_intervals                                [trigger 1]
> ```
>
> **canopy#537's guard (`network_visualizer.py:447`) requires `len(ctx.triggered) == 1`. On a poll cycle
> that is always 3.** The guard is structurally dead — not statistically unlucky — and no census size
> would ever have shown otherwise. That in turn *explains* both prior results rather than explaining them
> away, which matters because the consensus re-read left supersession neither refuted nor confirmed:
>
> | trial | measured | why, structurally |
> |---|---|---|
> | canopy#537 alone | 0 of 2 | the guard cannot fire; sample size was never the issue |
> | suppression alone | 0 of 6 | removes triggers 2 and 3, leaving a bare tick — but #537 did not exist in that build (primary at `27af847`), so a full rebuild still ran every 5 s |
> | **the pair** | **never run** | suppression leaves a bare tick, which #537's guard then catches |
>
> So the "underpowered census" argument is no longer load-bearing in either direction. **Neither fix could
> have worked alone, for reasons visible in the source.**
>
> **Shipped as canopy#542** (`fix/f039-topology-noop-suppression`): the store rides as `State` on its own
> writer; `_update_topology_store_handler` gains a canonical identity guard at both success returns;
> `current=None` never suppresses, so all seven existing direct call sites stay valid. The WS `cascade_add`
> path is deliberately left unsuppressed — such a frame is by construction a change. Consumer starvation
> was checked: all three consumers of this store have a second Input, so suppression strands none of them.
> Pinned by `TestF039TopologyIdentitySuppression` (7 tests, 6 of which fail on the parent), including one
> that pins the store as `State` and never as an `Input` of its own writer — because dropping that `State`
> would disable the guard **silently** (`current` would be `None` forever) and no other test would notice.
>
> ## ROOT CAUSE — CONFIRMED IN dash-renderer's SOURCE, AND FIXED (2026-08-31, canopy#549)
>
> **The response was never applied because the renderer RETIRES the in-flight invocation whenever the
> same callback identity is re-requested.** Read from the shipped unminified bundle, not inferred:
>
> - `getUniqueIdentifier` (`dash_renderer.dev.js:1715`) hashes a pending callback's **inputs + outputs +
>   state — NOT what triggered it**. So a rebuild triggered by the topology store and one triggered by a
>   bare tick are the *same identity*.
> - `:3026` computes `eDuplicates = concat(executing, requested)`, grouped by that identity, each group
>   sliced `[0:-1]`, and hands the result to `removeExecutingCallbacks`. `requested` is concatenated
>   **last**, so the newly-requested invocation survives and the **in-flight** one is dropped.
> - Its response then arrives for a callback no longer in `executing`, and is discarded rather than applied.
>
> The rebuild takes 1.5-5 s; `tabpoll-topology` ticked every 5 s. As an **Input**, the tick retired the
> populated rebuild on essentially every cycle. That is F-CANOPY-039, and it retro-explains every
> measurement in this entry — the 7 responses none of which carried the figure, the `RemoveRequested`
> traffic (one set over from `RemoveExecuting`, which is where the response actually dies), and the
> instant paint when the tick was disabled at runtime.
>
> **The fix is an Input -> State demotion** — the same move F-CANOPY-037 made on
> `metrics-panel-metrics-store` one layer up. State does not trigger, so the tick can no longer
> re-request the callback, while `n_intervals` stays readable for the P2-1 pulse.
>
> **CENSUS — one fixture, one variable, provenance recorded in both artifacts**
> (`reports/e2e/20260831T000000Z/f039_pair/`, canopy `4e6faae`, cascor `e1b4988`, a completed 10-unit
> cascade, `scope=idle populated=True`):
>
> | build | painted | signature |
> |---|---|---|
> | merged pair (#537 + #542), tick as Input | **0 of 11** | deterministic, `counts=0/0/0/0`, `traces=0`, `sig=2` |
> | + tick as State (canopy#549) | **11 of 11** | `counts=2/10/2/89`, `traces=181`, `sig=30850` |
>
> Paint 7.1 s min / 17.8 s median / 31.1 s max — inside F-CANOPY-004's ≤16 s interaction bound at the
> median. The counts match server truth exactly, and **`traces=181` is the same figure this entry
> recorded when `tabpoll-topology` was disabled at RUNTIME** — the source fix and the runtime
> manipulation converge from opposite directions on the identical result.
>
> **canopy#537's guard is REMOVED, and it made the defect worse rather than better.** Before it, a bare
> tick ran a full rebuild that at least computed a correct figure (the measured "7 responses carrying the
> graph"). With it, the tick's invocation returned `no_update` for all 8 outputs — so it still displaced
> the in-flight populated rebuild via the dedup above, and then contributed nothing in its place. That is
> what converted an intermittent miss into a deterministic never-paint.
>
> **The durable rule, worth more than the fix: a server-side `no_update` does NOT save a renderer slot
> and does NOT prevent the invocation.** The round trip already happened and the invocation had already
> displaced its predecessor. **Suppress the TRIGGER, not the work.**
>
> **GROWTH SCOPE ALSO CONFIRMED (2026-08-31) — 11 of 11 against the MERGED build, clean.**
> `reports/e2e/20260831T000000Z/f039_pair/census_growth_scope.json`: canopy **`b9ad825`** (the shipped
> #549 merge, `dirty=False`), cascor `e1b4988`, `scope=growth populated=True varied=True`,
> `hidden_units_observed=['25','6']`. Paint 9.5 s min / 25.7 s median / 53.7 s max.
>
> The three arms together, each with provenance in its artifact:
>
> | arm | build | topology | painted |
> |---|---|---|---|
> | idle, tick as **Input** (the merged #537+#542 pair) | `4e6faae` clean | static 10 | **0 of 11** |
> | idle, tick as **State** | `4e6faae` dirty | static 10 | **11 of 11** |
> | **growth, tick as State** | **`b9ad825` clean** | **6 -> 25** | **11 of 11** |
>
> It also renders at scale: the 25-unit topology is `2/25/2/404` — **811 traces**, 4.5x the connections
> of the 10-unit case — and still paints, without falling back to the empty path.
>
> **Read `varied=True` narrowly, and this is a limit of the check I added rather than of the result.**
> It compares the topology each session OBSERVED, so it cannot separate "the cascade grew while a session
> watched" from "consecutive sessions saw different static topologies". Here it was mostly the latter:
> training completed before sessions 1-3 (at 6 units) and again before 4-11 (at 25). The tool's note now
> says so explicitly instead of claiming "the topology changed during the census".
>
> The best single datapoint for painting *during* active growth is from the aborted first attempt:
> one session at `2/10/2/89` with **`traces=196` against that topology's static signature of 181**, and
> `elapsed=117 s` against an idle median of ~18 s — a longer paint carrying extra traces, consistent with
> an active new-unit highlight. Suggestive, n=1, and NOT load-bearing for anything claimed here.
>
> **M-TOPOLOGY-16 — INVESTIGATED AND FIXED 2026-08-31 (canopy#555), and it overturned the "BLOCKED"
> reading recorded here hours earlier.**
>
> The claim above — that this row "depends on `metrics-panel-metrics-store` reaching the client, which is
> a separate open question", and was therefore probably BLOCKED rather than owed — is **refuted by direct
> measurement**. It was an inference from the ledger's older "the client copy never advances" note, and it
> was flagged at the time as needing a measurement rather than a reading. The measurement went the other
> way.
>
> `util/ad-hoc/e2e_m16_glow_instrument.py` logs the detector's OWN ARGUMENTS from inside the callback —
> the same technique that broke F-CANOPY-039 open, and for the same reason: every browser-side probe in
> this arc has been unreliable, and the argument is what the detector actually sees. On the live trio:
>
> ```
> GLOWPROBE metrics_len=4   last_pair=40->40  window_span=(39, 40)  armed=0  newly_added_unit=None
> GLOWPROBE metrics_len=23  last_pair=17->17  window_span=(0, 17)   armed=0  newly_added_unit=None
> ```
>
> - **`metrics_len` is 4 and 23, NOT 0.** The metrics store reaches the callback. The row was never
>   blocked on it.
> - **The second line is the whole defect**: a window carrying **seventeen** unit additions, and the glow
>   armed **zero** times. "Flaky by design" understates it — on this evidence it essentially never fired.
> - The cause is the **last-pair check** (`network_visualizer.py`, `metrics_data[-2]` vs `[-1]`). The
>   rebuild does not run on every metrics sample, so by the time it runs those two are equal and the
>   addition has scrolled into the middle of the window.
>
> After the whole-window scan, an **identical window shape** arms:
>
> ```
> GLOWPROBE metrics_len=4   last_pair=40->40  window_span=(39, 40)  armed=1  newly_added_unit=39
> ```
>
> Same window, same last pair, same topology — the scan is the only variable. Corroborated at the render:
> **1936 traces vs 1891** on the same `2/40/2/944` topology, consistent with highlight traces drawing.
>
> **The fix is THREE coupled edits, because the one-liner ships broken.** `_update_highlight_state`
> resets on any detection, so a whole-window scan alone re-arms the same unit every rebuild and the glow
> never fades. And the obvious dedupe — "is it already the current highlight?" — **does not close the
> loop**: once the glow fades the scan still reports that unit and re-arms it forever. The memory must
> OUTLIVE the highlight, so the fade path now returns `{"node_id": None, "state": "done",
> "shown_unit": N}` and `_calculate_highlight_properties` gained a `node_id` guard so the marker renders
> nothing. Pinned by `TestM16WholeWindowGlowDetection` (6 tests, 5 fail on the parent).
>
> **Row verdict NOT changed.** M-TOPOLOGY-16 is a **MANUAL / VIS** row — its contract is that the glow is
> *visible*, driven through active→fading with pulse scale and opacity. What is proven here is that the
> **detector arms**, plus a suggestive trace delta. Scoring the row still needs a visual drive, and
> `e2e_seg17_topology_driver.py` has no M-TOPOLOGY-16 step.
>
> **F-CANOPY-039's fix UNBLOCKS THE WHOLE M-TOPOLOGY BLOCK.** `FA-1` in the matrix is a feature-area
> label ("Topology display"), not a blocker — M-TOPOLOGY-01..18 were BLOCKED on F-039 itself. With the
> graph now painting 11/11 at idle and 11/11 under growth, those rows are drivable again. The AUTO ones
> (02/04/05/06/07/08/17) are covered by the driver's `topo` step; the rest are MANUAL. **They are owed a
> re-drive, and none of them should be scored from the census alone** — the census measures paint, not
> each row's contract.
>
> **Two cascor fixture traps, both of which silently produced the wrong network** (found while building
> the growth arm; each cost a census run):
>
> - **`POST /v1/training/start {"start_fresh": true}` discards the network's configured
>   `max_hidden_units`** and rebuilds from service defaults. A network created with `max_hidden_units=25`
>   trained to exactly 10 and reported success. Start without `start_fresh` to keep the network you made.
> - **`POST /v1/network` fills unspecified params from the REQUEST schema, not the service config.**
>   Naming only `max_hidden_units` and `candidate_epochs` silently takes `correlation_threshold=0.1` and
>   `patience=5` — far stricter than the service's own `0.01` / `50` — and the cascade early-stopped at 6
>   of 25. Specify every param that governs cascade depth, or PATCH `/v1/training/params` after creating.
>
> ---
>
> ## THE SECTION BELOW IS WRONG AND IS RETAINED AS THE RECORD OF THE ERROR (written 2026-08-30, refuted 2026-08-31)
>
> It claimed an idle census "reads green either way" and would therefore be vacuous. **That is false, and
> the error was a conflation**: the fix suppresses *redundant* rebuilds, not the rebuild that matters.
> Post-suppression the idle sequence contains exactly ONE populated rebuild — the mount-time fetch, where
> the 7,059 B payload differs from the 75 B store default — so whether the graph paints at idle *is*
> precisely whether that one response was applied. The idle census was fully discriminating, and it is
> what produced the 0-of-11 that led to the root cause.
>
> What survives from it: an idle census cannot speak to the **growth-dependent rows**, and the real
> vacuity risk is an **empty** topology (nothing to draw, so a FAIL means "nothing to paint"). The census
> tool now pins that as its `populated` precondition and reports `scope` as invalid / idle / growth.
>
> **This is a predicted vacuous pass, recorded before the census rather than after it.**
>
> The pair works by stopping the rebuild from *running* on no-op cycles. At idle that is sufficient and
> the graph will paint. But a server-side `dash.no_update` **does not save a renderer slot** — the round
> trip already happened, which F-CANOPY-027's own remediation established. So on a cycle where the
> topology *genuinely* changes, the rebuild starts (1.5-5 s) and the next 5 s tick still issues a
> bare-tick invocation against the same 8 outputs, which may still retire it.
>
> If that is what happens, the pair yields **correct at idle, still broken during cascade growth** — which
> is the only time the panel matters, and which an idle census would certify as FIXED. Any census run
> against canopy#542 that does not drive live topology change is therefore **vacuous by construction**,
> regardless of its N.
>
> **Do not re-run the renderer-apply instrument.** `util/ad-hoc/e2e_f039_renderer_apply.py` has already
> been run and its result is recorded above in this same entry (7 responses, 5,556 actions, 126 naming the
> graph, **none carrying the figure**, lifecycle complete with exact itempaths). The 2026-08-30 handoff
> lists it as "never been run" and prefers it as the next step; that is wrong, and following it would buy
> a measurement this ledger already holds.
>
> ---
>
> ~~Superseded — retained so the reasoning error stays visible:~~
>
> **Given that, the rebuild is behaving correctly.** Its own fast path is
> `if not topology_data or topology_data.get("input_units", 0) == 0: return empty_fig, ..., "0","0","0","0"`
> (`network_visualizer.py`). Handed an empty store it returns an empty figure and `"0"` counts — which is
> *exactly* the observed DOM. **The graph is not failing to apply anything. It is faithfully rendering an
> empty topology, because that is what it is given.**
>
> This also re-reads the earlier evidence correctly: the 39,319 B / 206-trace responses are the
> invocations that DID receive a populated store, and they are interleaved with empty-store invocations
> whose `"0"` counts overwrite them. It explains the `RemoveRequested` traffic without supersession, and it
> explains why disabling the tick helped — it stopped the empty-store invocations that were overwriting
> the good ones.
>
> **The open question is now sharp and different: why does a store write that the server issues every 5 s
> never reach the client's copy?** Note the shape — a `dcc.Store` renders **no DOM**, so a duplicated one
> is invisible to both the live DOM count *and* (if created at runtime by the A1-iii-b1 tab rebuild rather
> than declared) the static layout check that came back 464/464 clean. F-CANOPY-027's own investigation
> named this exact trap: *"If a store is declared twice, Dash writes one instance and the consumers read
> the other."* That is the first thing to test, at runtime rather than statically.
>
> **Method note.** Three hypotheses (renderer apply, supersession, no-op writes) each survived several
> negative probes and each was wrong. The one measurement that settled it was the cheapest available and
> was named as F-CANOPY-038's next probe two sessions ago: **log the comparison's operands server-side.**
> When a client-side value is in question, instrument the SERVER's view of it — every browser-side probe
> in this arc has been either unreliable or ambiguous, and this one was neither.
>
> **Instrument note:** a substring match for the component id is not a match for "an action about this
> component". 45 `SET_PATHS` dispatches per minute each carry a **534 KB** payload naming *every* id in
> the app, so a naive count reported 126 "actions naming the graph" and read as "the renderer is applying
> it". Filter by action type before drawing that conclusion.

**Named next probes, in order of expected value.** (1) **Duplicate component ids** — the A1-iii-b1 tab
rebuild reconstructs the tab bar, so a stale detached `network-visualizer-graph` would take the response
while the probe reads the live one; F-CANOPY-027's methodology checked exactly this (`count == 1`) and it
has not been re-checked post-rebuild. (2) A dash-renderer-level trace of the response's application
(`e2e_f027_setprops_probe.py` / `e2e_f027_dom_watch.py`). (3) Whether the graph element is inside a pane
that is `display:none` at apply time. **Do not re-diagnose from `store` reads**: the driver's `_store()`
returned `None` in every session here while the store's own writer fired 12x/60 s, and the same probe
returned `changed=None` / `depth=None`, so that instrument is unreliable in this configuration and its
zeros are not evidence.

**Blast radius.** M-TOPOLOGY-01..18, W4-01..17 and W1-12..14 stay **BLOCKED**, with the blocker
**re-attributed from F-CANOPY-037 (mechanism fixed, see its entry) to this finding**.

**F-CANOPY-033 — `RESET_COMPONENT_STATE` storms one panel at ~13/s (P2, OPEN; found while tracing F-CANOPY-027).**
Redux tracing recorded **1157 `RESET_COMPONENT_STATE` dispatches in 90 s** — roughly 13 per second, out of
6251 total actions — and every sampled payload carries an `itempath` under `…/props/children/12/…`, the
**Cassandra** panel's subtree. `RESET_COMPONENT_STATE` returns components to their layout defaults, so a panel
nobody is looking at is being torn back to defaults ~13 times a second for the whole session. Unrelated to the
F-CANOPY-027 chain (wrong subtree) but a real and continuous waste of client work on a dashboard already
documented as callback-congested (F-CANOPY-004); it also makes any redux trace noisy for future
investigations. Reproduce with `util/ad-hoc/e2e_f027_redux_actions.py`.

> **REPRODUCED AND RE-ATTRIBUTED (2026-08-28, run `20260828T132533Z`). The Cassandra attribution is
> WRONG.** Live on merged canopy `6b55399`: **908 `RESET_COMPONENT_STATE` in 60 s (~15/s)** — the rate
> holds. But this entry named the target by reading an itempath INDEX (`…/props/children/12/…`) and
> calling it "the Cassandra panel's subtree". Resolving the same itempaths against **Dash's own
> `paths.strs` id→itempath map** (`util/ad-hoc/e2e_f039_reset_target.py`), the owners are:
>
> | resets (of 40 sampled) | owning component |
> |---:|---|
> | 20 | `network-info-panel` |
> | 12 | `network-info-details-panel` |
> | 8 | `network-evolution-grid-container` |
>
> **Cassandra does not appear.** The first two are the slow-lane callback's own outputs, so it is
> re-rendering its children; the third is the evolution grid. Anyone acting on this entry would have gone
> looking at the wrong panel. **An itempath index is not an identity** — the tab list is rebuilt
> (A1-iii-b1) and the indices move; resolve through `paths.strs` instead, which is what Dash itself does.
>
> This also settles the obvious question raised by F-CANOPY-039 (a graph stuck at its layout defaults,
> next to a storm of "reset to layout defaults"): **0 of 40 resets target the graph or any ancestor of
> it**, so F-033 is *not* F-039's cause and the two stay separate findings.

**F-CANOPY-028 — pinned params are silently discarded on the first pin after any reload (P2, OPEN; segment 15).**
`pinned-params-store` is `storage_type="local"` and survives reload correctly, but the `{"type":"param-pin"}` checkboxes in the Parameters tables **do not rehydrate from it** — after a reload they all render unchecked while the store and the sidebar card still show the pinned set. Because the single pattern-matched writer (`dashboard_manager.py:3948-3952`) *collects the state of every checkbox*, the next pin action writes a list built from the un-rehydrated DOM, dropping everything pinned before the reload. Reproduced end-to-end: pinned `learning_rate` → `pinned-params-store` `["learning_rate"]`, sidebar card `display:block` showing "Learning Rate" → full page reload → `localStorage["pinned-params-store"]` still `["learning_rate"]`, card still shown, **but the `learning_rate` checkbox reads `checked:false`** → pinning `max_iterations` → store and localStorage both become `["max_iterations"]`, `learning_rate` gone with no warning. Matrix rows M-PARAMETERS-04/-05/-06 still **PASS** on their own stated expectations (the store write, the card reveal, and persistence all work); this is the cross-cutting defect those rows sit on top of.

> **CORRECTED + FIX AUTHORED (2026-08-27, `juniper-canopy#533`; CI green, NOT merged — entry stays OPEN).**
> **"The checkboxes do not rehydrate from it" does not hold in source.** `_build_table`
> (`parameters_panel.py:114-118`) sets `value=key in pinned_set` on every pin checkbox, and
> `update_parameters_tables` takes `pinned-params-store` as an Input with `prevent_initial_call=False` — the
> rehydration path is wired and correct.
>
> What IS wrong is the writer, and it is the half this entry's own last sentence identified: it *collects
> the state of every checkbox* and replaces the store wholesale, so "this checkbox is absent" is
> indistinguishable from "this key is not pinned". Any render that under-reports the pin set — a mount
> before the `storage_type="local"` store hydrates, or tables not in the DOM — then gets persisted on the
> next toggle. `_merge_pinned_params` now writes only what it can observe: an empty component set returns
> `no_update` (an empty render is never evidence that nothing is pinned), rendered checkboxes stay
> authoritative for their own keys so unpinning still works, and pinned keys with no rendered checkbox are
> carried through untouched.
>
> **The precise repro recorded above was not reproduced from source**, so the live re-drive should re-check
> the original symptom rather than assume this closed it.

**F-CANOPY-029 — the Dataset View "Generate Dataset" modal can never open: its callback 500s on every click (P1; FIXED juniper-canopy#504, `041eb69`; found segment 16).**
`toggle_generate_modal` (`dashboard_manager.py:3869-3870`) does `ctx = get_callback_context()` and then reads **`ctx.triggered_id`**. `get_callback_context()` returns canopy's **own** `CallbackContextAdapter` (`frontend/callback_context.py:53`), whose only accessor is **`get_triggered_id()`** (`:78`) — there is no `triggered_id` property. Every click therefore raises `AttributeError: 'CallbackContextAdapter' object has no attribute 'triggered_id'. Did you mean: 'get_triggered_id'?` and Dash returns **HTTP 500**; the browser console shows `Callback error updating dataset-plotter-generate-modal.is_open`, and the canopy log carries the full traceback. Deterministic — reproduced on every attempt. The other three production `.triggered_id` reads (`dashboard_manager.py:2411`, `:2429`, `callback_context.py:92`) are on the genuine `dash.callback_context`, which is why the model-selection modal (C2.6-18) still passes; this one call site mixes the adapter object with the raw-dash attribute name. Fix: `ctx.get_triggered_id()`.
**Why the suite is green:** `test_toggle_generate_modal_open` / `_close` (`src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py:375-388`) patch `get_callback_context` with a bare `MagicMock()` and then set `fake_ctx.triggered_id = ...`. A `MagicMock` fabricates any attribute on demand, so the test asserts against a shape the production object has never had. Hardening: give the mock `spec=CallbackContextAdapter` — that alone would have failed the test. This is the mock-seam / vacuous-pass class in its purest form.
**Blast radius (as found):** M-DATASET-01 **FAIL**; M-DATASET-02 / -03 / -05 / -07 / -09 **BLOCKED** — the tabs, the generate params, the CSV upload contract, the URL input and the cancel button all live inside a modal that never opens.
**Fix (Phase 2, `juniper-canopy#504` → `041eb69`).** `ctx.triggered_id` → `ctx.get_triggered_id()`, plus the test hardening below. **The hardening was verified to bite**: with the production fix temporarily reverted, the updated tests fail with precisely the production error (`AttributeError: Mock object has no attribute 'triggered_id'. Did you mean: 'get_triggered_id'?`) — the same tests passed against that same broken code beforehand. Three adapter fakes are now `MagicMock(spec=CallbackContextAdapter)` and a new `test_toggle_generate_modal_rejects_raw_dash_attribute` pins the adapter's interface directly. Full `tests/unit/frontend/` suite green; canopy CI green on 20/20 required contexts including the Playwright UI sub-suite.
**Re-driven live after the fix** (run `20260822T014138Z`): canopy log carries **zero** callback errors, and all five rows now **PASS** — modal opens `display:flex` 500x1044; the three tabs render (Generate active / Upload File / Fetch URL); the file input carries `accept=".csv,text/csv"` + `multiple:false` with the confirm shipping disabled; the URL input is `type="url"` and fills; Cancel closes to ABSENT with **0** `/api/` requests. Only M-DATASET-03 remains BLOCKED, on its own DEMO-lane precondition rather than on this defect. **Timing note for re-drivers: the fixed modal takes ~39 s to appear** under live-run callback congestion (F-CANOPY-004) — a short settle reports it as still dead, which it briefly did here.

**F-CANOPY-031 — the snapshots panel never renders against the migrated shared corpus (P1; found segment 16; FIXED canopy#517 `9dcbb77a`, verified live — closure block below).**
`hdf5-snapshots-panel-status` is stuck at **"Loading snapshots…"**, `hdf5-snapshots-panel-table-body` has **0 rows**, and `hdf5-snapshots-panel-empty-state` is `display:none` (so the user sees neither data nor an empty state), while `GET /api/v1/snapshots` answers successfully with **27,903 entries — a 10.4 MB payload taking 4.9 s to serve**. The route works; the panel never leaves its loading state. Newly exposed by the S-1 storage-convention migration (`notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-STORAGE-CONVENTION-DESIGN.md`): segment 15 drove this same panel successfully when the corpus held **4** files, and the panel then rendered per-row op buttons. The list endpoint takes no `limit`/pagination, so the panel asks for the entire asset store every refresh. NB the fetch is **not** hammering — 18 logged fetches over ~25 min, tab-gated — so this is a render/scale failure, not a polling storm.
**Blast radius:** M-SNAPSHOTS-19 **BLOCKED** — with no snapshot row rendered there is nothing to right-click. Independently, the two attributes `snapshot_context_menu.js` requires to build its menu, `data-snapshot-row` and `data-snapshot-id` (`:29-30`), appear on **zero** elements in the DOM, so that menu would not open even with rows present — worth checking as a second defect once the panel renders.

> **Both cleared — the owed `f031` driver step, re-driven 2026-08-26 (run `20260826T215010Z`,
> `e2e_seg17_topology_driver.py --step f031`).** The step the arc has owed since its probes were lost to
> `/tmp` now exists in a script. Against the live corpus the panel rendered **200 rows in 2.0 s**, status
> read **`"Showing newest 200 of 28042 snapshot(s)"`** (bounded slice, correct total), and
> `-empty-state` was correctly `display:none`. The `limit`/`offset`/`total` contract holds on the wire:
> `?limit=3&offset=0` and `?limit=3&offset=3` return disjoint, correctly newest-first triples off the same
> `total: 28042`. **The second defect is also gone:** `data-snapshot-row` and `data-snapshot-id` are now
> present on **200 of 200** rendered rows (was zero), so the context menu M-SNAPSHOTS-19 depends on has its
> required attributes — that row's existing `PASS (re-validated @ 9dcbb77)` is corroborated, not changed.

**CLOSED (2026-08-25, canopy#517 `9dcbb77a`; run `20260825T101752Z`). Two stacked mechanisms, both addressed.** (1) The fetch lost the race: the panel's bare 2 s `api_timeout` against the ~4.9 s unbounded scan+serialize of the whole store — every list fetch timed out, so the panel never left its layout-default "Loading snapshots…" (neither data nor the empty state, exactly as observed). (2) The render could never scale: one `html.Tr` — two buttons plus a four-item dropdown, five pattern-matching ids — per snapshot × 27,903, and under the ratified no-deletion retention the corpus only grows. Fix: `GET /api/v1/snapshots` gains `limit`/`offset` (a server-side slice of the already newest-first list; omitting `limit` keeps the legacy full list for existing callers; the demo branch slices identically) and **always** reports the pre-slice `total`; the panel fetches only the newest `SNAPSHOT_TABLE_PAGE_SIZE` (200) with the create-path's `+3` timeout headroom, and its status line reads **"Showing newest N of TOTAL snapshot(s)"** — truncation is never silent. **Verified live against the real corpus** (28,016 files under the symlinked e2e root; canopy leg `:8051`, probes 10:17–10:22Z on the branch working tree committed as `5560cb19` at 10:23Z and squashed as `9dcbb77a` at 10:40Z — the two trees differ only by #516's four memory-budget files, so every file the fix touched is byte-identical in merged main): the table rendered **200 rows in seconds** with status `"Showing newest 200 of 28016 snapshot(s)"` and the empty state correctly hidden; `data-snapshot-id` was present on **all 200 rows** — the entry's secondary observation ("attributes on zero elements") was zero *rows*; the attributes were always in the row builder, so the feared second defect never existed. **The full M-SNAPSHOTS-19 chain works**: right-click on the newest row → the context menu (243×235: Restore / Replay / Resume training / Retrain) → Restore → the **Confirm Snapshot Operation** modal (500×1044) naming that exact snapshot (`cascor_snapshot_20260824_234648_5c7c8004-…`), with the `context-menu-trigger` store write captured on the wire at t+13.4 s. M-SNAPSHOTS-19 → `PASS (re-validated @ 9dcbb77)`; the FA-4 block ("nothing to right-click") is gone. Pinned by `src/tests/unit/test_f031_snapshot_scale.py` (route: newest-head slice + `total`, offset, legacy no-params, demo parity; panel: one-page fetch with headroom timeout, `total` threading, the truncation line and the plain line when not truncated); one existing route test updated for the additive `total`. Instrument note: two intermediate probes matched the welcome modal's container (1600×1100, "Welcome to Juniper Canopy") through a generic modal selector before the confirm modal was targeted by its own element — select modals by their own ids. The probe scripts themselves lived in `/tmp` and are gone (the surviving logs are `/tmp/juniper-e2e/f031_verify*.log`); an `f031` driver step is owed at the next stack window so the row's regression re-drive is reproducible.

**F-CANOPY-032 — the worker panel's "Worker data degraded" alert never renders even though canopy's own API reports the error (P2, OPEN; segment 16).**
`worker_panel.py:226-227` renders a dismissable `dbc.Alert(f"Worker data degraded: {upstream_error}")` when `upstream_error` is set. Driven under **both** upstream failure modes — control-WS-only outage (`stream_health.overall == "degraded"`) and cascor fully down (`overall == "reconnecting"`) — `worker-panel-error-display` stayed present-but-empty (`display:block`, 860x0, text `""`) across 60 s each, with the panel showing `NO WORKERS` and all-zero tiles. Yet with cascor down canopy's own endpoints carry the error explicitly: `GET /api/v1/workers/list` → `{"workers":[],"count":0,"local_reported":false,"error":"Upstream error","error_id":"dd1a84f727da"}` and `/api/v1/workers/stats` → `{...,"error":"Upstream error","error_id":"450850d9f349"}`. So the signal exists end-to-end and the alert branch never fires. Matrix row M-WORKERS-02 **FAIL**. Consistent with the F-CANOPY-027 filled-data / dead-render class, though the store fill itself was not separately instrumented here.

> **NOT FIXED — RE-DIAGNOSED (2026-08-27). The stated mechanism does not reproduce from source, and no
> speculative patch was written.** Traced end to end: `GET /api/v1/workers/list` returns its error dict at
> **HTTP 200** on the upstream-failure branch (`main.py`, the `except` path), so the dashboard's `resp.ok`
> empty-guard does **not** discard it; `_update_workers_store_handler` threads `"error":
> list_data.get("error")` into the store payload; and `_render_from_store` builds the `dbc.Alert` whenever
> that key is truthy. Most likely another instance of the filled-store / dead-render class
> (**F-CANOPY-027**, since FIXED) — which this entry itself allows for. **Needs a live re-drive to confirm
> or re-diagnose.**
>
> Four contract tests were added in `juniper-canopy#533` to stop the path rotting before that happens,
> including one asserting the route's failure branch must **not** become a 5xx — the single change that
> *would* make the empty-guard swallow the signal.
>
> **Correction to this entry's evidence:** of its two test arms, the **control-WS-only outage** arm should
> not have counted as a failure. With cascor's HTTP up, `list_workers()` succeeds and the route returns no
> `error` key at all, so no alert is the correct behaviour there; "NO WORKERS" then simply means no workers
> are registered.

### Observations (non-finding)

- **Badge render lag**: `ws-connection-indicator` trails the client state machine by ~1–2 s in both directions (client `closed/reconnecting` at +0.8 s rendered amber at +2.8 s; client re-`open` rendered green ~2 s later). No latency contract exists in the matrix; recorded as §7.3 context.
- **Load sequence**: badge renders `WS: Offline` (red) during pre-first-connect hydration (observed +0.8 s → ~11 s on a cold reload) before settling `WS: Connected`; the server-rendered initial layout is `WS: --` grey `#6c757d` (verified from `/dashboard/_dash-layout` JSON — C2.4-01's authoritative source).
- **Rejected induction, documented for console-log honesty**: a `context.setOffline(true)` probe does NOT drop established localhost WebSockets (Chromium blocks only new connections) — the badge rightly stayed green while every HTTP poll failed, spraying **187 fetch errors** into the console (`console-2026-08-10T00-27-03-702Z.log`, all within the offline window, cleared by the next reload). Those errors are excluded from CON assertions; the working induction for badge states 6/7 is a client-side `ws.close()` under a temporarily raised `baseReconnectDelay`.
- Reconnect timing: a bare `ws.close()` on localhost recovers in ~121 ms (attempt 1) — too fast for the badge to repaint; the raised-delay induction is what makes states 6/7 renderable.
- **Doc divergences for the truth-up batch (D-ledger additions)**: (i) `stream_health.overall` recovery value is `"healthy"`, not the matrix's claimed `"ok"` (W14 steps 3/9, `main.py:1279` route) **[matrix lines corrected 2026-08-26]**; (ii) the About panel renders **"App Version: 2.2.0"** while `/v1/health` serves `version: 0.4.0` — the About `self.version` source is stale/mis-wired (`about_panel.py:323-345` block) **[RESOLVED 2026-08-26, canopy#526 `27a4bb1d`: the root cause was a second, hardcoded `APP_VERSION = "2.2.0"` literal in `about_panel.py`; the version is now resolved once by `canopy_constants.resolve_app_version()` — installed metadata, `pyproject.toml` fallback — the same source `/v1/health` reports]**; (iii) depth-slider label read `"0 of 3"` while the slider had never been touched — the initial slider `value` seeds 0 rather than max, so the "user-picked value" semantics start from a filter that would draw zero cascade units (matrix M-TOPOLOGY-06/07 context; Phase-2 look).
- W1 run 2 (post-VRAM-heal): output phase streamed ~400 metrics frames on `/ws/training` (raw-socket capture), then candidate phases with steady `candidate_progress` (~35/30 s) and `state` frames; cascade growth 1→6+ units observed server-side; Evolution tab captured a growth card per add via the clientside WS path — confirming every WS type EXCEPT the clobbered `metrics` reaches Dash.
- Console-error ledger for the CON sweeps: zero uncaught errors across all tab walks; the only entries are (a) the deliberately-excluded offline-window fetch spam, (b) F-CANOPY-005's `409` + its two `[Phase D]` warnings.

### Phase-1 methodology notes

- **"NET" verifies for `/api/*` polls are server-side.** Canopy's interval callbacks fetch its own REST routes from INSIDE the Dash callback (`requests.get(self._api_url(...))`), so the browser network log shows only `_dash-update-component` POSTs — the matrix's NET expectations for poll rows are verified via the canopy log / direct endpoint probes, not browser DevTools. Browser-originated NET remains observable for the explicitly clientside paths (`/api/csrf`, `/api/ws_latency`, the Phase-D REST fallback, snapshot/replay panel fetches).
- **During-run DOM reads carry the F-CANOPY-004 lag** (renders land 30 s–minutes late). Rows whose *expected result* is a DOM state were credited only after the state actually rendered; rows starved past the run's end were re-read post-run when the callback queue drains. Direct endpoint probes were used to separate "backend wrong" from "render late" in every ambiguous case.
- **Multi-writer store races**: sub-second synthetic batch gestures (e.g. clicking all 5 accordion headers in one JS task) can race Dash's store round-trips; paced re-probes (600–900 ms gaps) were used before recording any FAIL.

### Row statuses (running)

`reports/e2e/20260810T002233Z/statuses.tsv` is the per-row record as rows execute. Verdicts so far: **C2.1-01..04 PASS** · **C2.4-01 PASS** · **C2.4-03 PASS** · **C2.4-06 PASS** · **C2.4-07 PASS** (C2.4-02 → DEMO lane; C2.4-04/05 → W14 induction).

---

## Phase 1 — segment 4 (2026-08-10): state reconciliation

Segment 4 opened against a stale handoff. Reconciling it against the live host produced three
corrections and one evidence recovery, all recorded here before any new row was driven.

### Stack-topology correction — the isolated recurrence leg is DOWN

The segment-3 handoff (and the run header above) assert a live recurrence leg on **8212**. Re-probed at
segment-4 open: **false**.

| Probe | Result |
|---|---|
| `curl :8212/v1/health/ready` | `Failed to connect … Could not connect to server` — **nothing is serving 8212** |
| `curl :8211/v1/health/ready` | `{"status":"ready"}` — but **not an E2E leg** (below) |
| `ss -tlnpH "sport = :8211"` | listener with no owning host pid visible to this user |
| `pgrep -af juniper-recurrence` | pid 1169615 `/usr/local/bin/python3.13 … serve` — **no `--port` flag**, container-style prefix |
| `/proc/1169615/root/.dockerenv` | **present** |
| `/proc/1169615/cgroup` | `…/docker-106a7b2f….scope` |
| `docker ps` | `juniper-recurrence  127.0.0.1:8211->8210/tcp  Up 30 hours (healthy)` |

**Conclusion**: host 8211 is the operator's **juniper-deploy container** (host 8211 → ctr 8210), exactly the
collider `isolated_stack.bash:26-27,164-165,291-295` warns about; the canonical E2E default is
8211 (`isolated_stack.bash:83`), which is why the earlier session relocated the leg to 8212. That relocated
leg has since exited (canopy, started 2026-08-09 17:46, has survived it). Canopy still points at the dead
port: live process env carries `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL=http://127.0.0.1:8212` and
`JUNIPER_E2E_RECURRENCE_PORT=8212`.

**Consequence (recorded to prevent a false finding)**: **W7 / W8 and every recurrence-dependent row are
BLOCKED until the isolated leg is restored on 8212.** Driven as-is they would fail for a purely
environmental reason while presenting exactly as the pre-registered **T-16** candidate (recurrence silent
no-op swap with Start still enabled). T-16 may only be adjudicated against a live leg. The deploy stack is
the operator's and is **not** to be stopped to free 8211 — the documented `JUNIPER_E2E_RECURRENCE_PORT`
override is the sanctioned path.

The trio is unaffected: data 8101 and cascor 8202 are host processes (`python` pid 1755429, `uvicorn`
pid 3325500 — the latter the documented mid-session cascor restart), and the honest gate re-passed at
segment-4 open (`demo_mode:false`, `juniper_data_available:true`).

### W5 preconditions re-verified live

`GET :8202/v1/training/status` → `state_machine.status STOPPED`, `phase IDLE`,
`monitor.current_hidden_units 10`, `is_training false`; `GET :8202/v1/snapshots` → `data: []`.
The trained 10-unit network and the empty snapshot baseline both survived the 26 h idle — W5 may proceed.

### Evidence recovery — the superseded `-results` run

Phase 1 was driven twice, on two branches, by two sessions:

| Branch | Run-id | Record | Fate |
|---|---|---|---|
| `arc/canopy-e2e-phase1-results` | `20260809T223851Z` | `rowlog.md` (91 lines) | superseded; its F-E2E-006 fix landed as ml#1049 |
| `arc/canopy-e2e-phase1` | `20260810T002233Z` | `statuses.tsv` (92 rows) | carried forward |

The later run re-covered most of the earlier one, but **~22 verdicts exist only in the earlier rowlog**.
It is preserved verbatim at `reports/e2e/20260809T223851Z/rowlog.md` rather than discarded, and its unique
rows are inherited with run-id attribution: **C2.2-02/04/05/06**, **M-WORKERS-06**, **M-REDIS-01/04**,
**M-CASSANDRA-01/04**, **M-TUTORIAL-01/02**, **M-ABOUT-03**, **M-PARAMETERS-01/02/03**, **M-REPLAY-01**,
**M-NETWORK-EDITOR-02/03/05/10**, and the **W13 step ledger 1–16**.

Most consequential: **M-NETWORK-EDITOR-05 already confirms divergence D-0 live** — readout
"No topology loaded.", server-side 404, *no browser-side request* — which the segment-3 handoff still
listed as outstanding work.

### Cross-run verdict reconciliation — C2.4-07

The two runs disagree, and the disagreement is itself evidence: the earlier run recorded **N-A
(annotated)** — "WS: Offline" judged unreachable, because the retry-forever client collapses
`closed`→`reconnecting` in a single status update (GAP-WS-31) and a MutationObserver over a fresh socket
close saw no intermediate state. The later run recorded **PASS**, catching the red `#dc3545` state in the
*pre-connect* window (t≈+806 ms after reload) rather than via socket loss. **PASS stands**; the earlier
note is retained as the methodology reason the state is invisible on the socket-loss path.

### Coverage baseline

`util/ad-hoc/e2e_row_coverage.py` (added this segment) diffs the matrix row inventory against every
accumulated verdict record, expanding the compressed range notation the run records use
(`M-TOPOLOGY-01..06,09..18`). At segment-4 open:

**298 matrix rows · 104 verdicted · 194 remaining.** The mapper only credits a row when its id is the
verdict record's *subject* (first TSV field / first table cell), so rows recorded in the earlier rowlog's
prose bullets (`M-PARAMETERS-02/03`, `M-NETWORK-EDITOR-03/05/10`) read as remaining and will be
re-confirmed live rather than assumed — a deliberately conservative bias.

### Observation candidates promoted from the `-results` sweep

- **OBS-1 → docs-truth-up (Phase 4)**: About panel "App Version: 2.2.0" vs `/v1/health` `version: 0.4.0` —
  two disagreeing version sources (about-panel local `self.version` vs the health handler). Corroborated
  independently by the later run (TSV `M-ABOUT-02`).
- **OBS-2 → UX candidate (Phase 2 triage)**: dark mode flattens all five training-control buttons to a
  uniform blue, losing the light-mode semantics (Start green / Pause yellow / Stop red). Legible, but
  semantics-destroying. Evidence: `W13-13__dark-metrics-top.png` vs the light walkthrough capture.
- **OBS-3 → not a finding**: metrics-tab sidebar header "Network Parameters" vs tutorial-tab "Training
  Controls" is `TAB_HEADER_MAP` behaving as designed (C2.2-04 corroboration).

### Findings opened in segment 4

**F-CANOPY-007 — canopy CREATES snapshots through the cascor backend but LISTS them off a LOCAL
filesystem path; on any split-filesystem deployment the list is silently empty (P1; canopy#525 `141324fa`; W5 step 3 re-drive 2026-08-26 on an empty local dir → cascor-sourced list (28029==28029); VERIFIED LIVE, FIXED).**

Found driving W5 step 3. The create succeeded end-to-end — panel reported
`✅ Snapshot created successfully: snapshot_20260811T010849Z`, both inputs cleared — yet the table stayed
on its empty state and `#hdf5-snapshots-panel-status` still read "No snapshots available". The UI was
faithful; its own API was wrong:

| Probe | Result |
|---|---|
| `GET :8202/v1/snapshots` (cascor) | `{"status":"success","data":[{"id":"snapshot_20260811T010849Z","size_bytes":296701,"path":".../juniper-cascor/src/snapshots/…h5"}]}` |
| `GET :8051/api/v1/snapshots` (canopy) | `{"snapshots": [], "message": "No snapshots available"}` |

Mechanism: `get_snapshots` (`juniper-canopy/src/main.py:1874-1909`) serves `_list_snapshot_files()`
(`:1838`), which reads `_snapshots_dir` — `JUNIPER_CANOPY_SNAPSHOT_DIR`, else the deprecated
`CASCOR_SNAPSHOT_DIR`, else **`"./snapshots"` relative to canopy's CWD** (`:1713-1726`). The detail and
op paths resolve through the same root (`_find_snapshot_file`, `:1764-1806`, used at `:2000`). Creation,
by contrast, is proxied to the cascor backend, which writes under **its own** `src/snapshots`. Live: the
env var was unset, canopy's CWD was `juniper-canopy/src`, and `juniper-canopy/src/snapshots/` held only
`snapshot_history.jsonl` — no `.h5` at all.

Why it has never been seen: the shipped compose topology co-mounts ONE volume
(`juniper-cascor-snapshots:/app/data`, `juniper-deploy/docker-compose.yml:265` and `:434`) into both
services, so the local read resolves to cascor's directory. Two host processes with different CWDs — the
isolated stack, or any split-host deployment — do not share it. The failure is **silent**: no error, no
warning, no degraded-mode signal; `snapshot_history.jsonl` is still written locally, so history and list
actively disagree.

Blast radius: the entire FA-4 surface (list / detail / restore / replay / resume / retrain), i.e. W5
steps 4-7 and 16-27, because every one of them needs a table row that can never appear.

**Confirmed by remediation** — the strongest available proof. After exporting
`JUNIPER_CANOPY_SNAPSHOT_DIR` at cascor's real snapshot dir and bouncing the canopy leg, the same probe
returned the snapshot with its true path, and the panel rendered `1 snapshot(s) found`, empty state
`display:none`, one row (289.7 KB), 1 View button + 4 op buttons.

Fix direction (Phase 2): canopy should resolve snapshots through the backend it created them with rather
than assuming a shared filesystem — or, at minimum, detect that the configured dir is not the backend's
and surface a degraded-mode banner instead of an empty list.

**FIX MERGED (2026-08-26, canopy#525 `141324fa`; W5 step 3 re-drive WITHOUT the harness's `JUNIPER_CANOPY_SNAPSHOT_DIR` workaround owed, plus the FA-4 rows that depended on it).** The first fix direction, taken whole: the adapter gained `list_snapshots()` / `get_snapshot(id)` proxies over cascor's `GET /v1/snapshots` and `GET /v1/snapshots/{id}` (the `{"ok", …}` envelopes of `get_snapshot_dataset_swaps`; a cascor 404 is a definite absence, any other client failure is "cannot answer"); in service mode `GET /api/v1/snapshots` serves cascor's inventory (normalized to the panel shape, newest first, `source: "cascor"`) with the F-CANOPY-031 `limit`/`offset`/`total` contract preserved, and the detail route treats cascor as the authority on existence while a local copy, when also visible, only enriches the record with its HDF5 attributes; the local directory remains the fallback whenever the backend cannot answer, and demo mode is untouched. `src/tests/unit/test_f007_snapshots_resolve_through_backend.py` (14 tests) drives the split-filesystem condition (cascor holds two, canopy's directory holds none) and every fallback arm; on the parent it reproduces the live empty list. The degraded-mode banner is not needed once the backend is the source.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f008,f007`).** With the canopy leg restarted against an **empty** local snapshot dir (0 `.h5`), the Snapshots table listed **"newest 200 of 28028"** from cascor (the split-filesystem silent-empty bug is gone); a create landed (`snapshot_20260826T183019Z`) and `/api/v1/snapshots` reported **28029**, exactly matching cascor's **28029** while the local dir stayed empty. W5 step 3 → PASS. **FIXED.**

**F-CANOPY-008 — the `/ws/control` CSRF gate leaks a per-IP connection slot on every rejection;
five rejections permanently lock the control plane out until canopy restarts (P0/P1; canopy#519 `ce819775`; restart re-drive 2026-08-26 → 5 rejects, 0 per-IP lock, plane recovered; VERIFIED LIVE, FIXED).**

Found immediately after the canopy bounce above. `/ws/training` reconnected normally; `/ws/control`
403-looped, and the audit log named the reason:
`{"event":"ws_csrf_rejected","endpoint":"/ws/control","reason":"invalid_token"}` × 5 — the browser was
still presenting a token minted by the *previous* canopy process. That part is expected. What is **not**
expected is what those five rejections left behind: `Per-IP limit reached for 127.0.0.1 (5/5)`, which then
survived a full page close, `clearCookies()`, `localStorage`/`sessionStorage` clear, and a 20 s idle
window. The counter never came back.

Mechanism, read out of the handler (`juniper-canopy/src/main.py`, `/ws/control`):

| Step | Path | Slot handling |
|---|---|---|
| Origin validation | `close(4003); return` | correct — returns *before* any reservation |
| `check_connection_limits(...)` | reserves a per-IP + per-session slot | its own per-session failure arm decrements (`websocket_manager.py:544`) |
| `connect(...)` | `except: release_connection_limits(); raise` / `if not connected: release_connection_limits()` | **correct on both arms** |
| **CSRF first-frame auth** | `missing_or_invalid_frame`, `invalid_token`, `auth_timeout`, `malformed_auth`, generic `Exception` | **all five do `log…(); close(1008); return` — none calls `release_connection_limits()` or `disconnect()`** |

The reservation taken before `connect()` is therefore never rolled back when the CSRF gate rejects.
`websocket_manager.release_connection_limits` (`:549-559`) exists for precisely this rollback and its
docstring describes the window; the surrounding `connect()` call was written with that discipline and the
CSRF block that follows was not. Since `connect()` had already *succeeded*, the socket is also still
registered in `active_connections` — so the leak plausibly extends to the registration and to
`juniper_canopy_websocket_connections_active{channel="control"}`. (The counter leak is proven live; the
registration/metric leak is a code-reading inference to confirm during Phase 2 triage.)

Why this matters well beyond the test rig, with `max_connections_per_ip: int = 5` (`settings.py:156`):

- It is reachable with **zero malice** — restart canopy, or simply let a token go stale, with a dashboard
  tab open. The client's own auto-reconnect burns all five slots in about ten seconds. That is exactly how
  it was hit here.
- Recovery requires **restarting canopy**. Nothing the operator does in the browser releases the slots.
- The cap is **shared across all clients behind NAT** — the method's own docstring states that inside
  Docker every client presents as the bridge-gateway IP. So five CSRF failures from *one* user lock the
  control plane for *every* user of that deployment.
- Because the training buttons are WS-primary (T-21), the visible symptom is "the training controls stopped
  working", with only a console 403 to go on.

Fix direction (Phase 2): release the reservation on every CSRF reject path — cleanest as a `try/finally`
(or a small context manager) around the post-reservation block so no future gate inserted after
`check_connection_limits` can reintroduce the leak. Regression test: drive N+1 rejected handshakes from
one IP, then assert a *valid* handshake still connects.

Note this is the "audit every call site when extending a shared helper" class: the helper was correct and
correctly used at the call site it shipped with; the later-added gate simply did not adopt it.

**FIX MERGED (2026-08-25, canopy#519 `ce819775`; the entry stays OPEN until the restart scenario is re-driven live).** Every CSRF reject arm now funnels through ONE teardown that logs the reason, closes 1008 and — in a `finally` — calls `websocket_manager.disconnect(websocket)`, the full rollback (per-IP + per-session slot, the `active_connections` entry and the `{channel="control"}` gauge). Reading `connect()` / `disconnect()` confirmed the deferred inference: `connect()` had already succeeded, so the leak covered the registration and the gauge too, and `release_connection_limits()` alone would not have been enough. `src/tests/unit/test_f008_csrf_reject_releases_slots.py` drives the real handler through `main.app`: `max_connections_per_ip + 1` stale-token handshakes all close 1008, the slot/registration/gauge snapshot returns to baseline, and a valid handshake still connects — on the parent the sixth attempt was refused `1013` (`[1008 ×5, 1013]`), the live signature exactly. Owed post-T6: restart canopy with a dashboard tab open and confirm five `ws_csrf_rejected` audit events with no `Per-IP limit reached` and a working control plane afterwards.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f008`).** Restarting the canopy leg with a dashboard tab open produced exactly **5** `ws_csrf_rejected` events (the stale token) and **`Per-IP limit reached` = 0** — five rejections no longer lock the control plane out. After a reload the badge read `WS: Connected` and the reset button re-enabled in 1.28 s with no `/api/train` POST. **FIXED.**

---

## Phase 1 — segment 5 (2026-08-11): W5 steps 4-7

### Stack state on entry — the cascor leg had died

Segment 4 handed off "stack UP and honest: data 8101 / cascor 8202 / canopy 8051". On entry to segment 5
the cascor leg was **DOWN and had been for ~7.6 h**:

| Probe | Result |
|---|---|
| `isolated_stack.bash --status` | data `health=200 pid=1755429` · cascor **`health=000 pid=none`** · canopy `health=200 pid=2375744` |
| `/tmp/juniper-e2e/logs/juniper-cascor.log` | last write `2026-08-10 20:36` local (= `2026-08-11T01:36Z`); ends **mid-poll** on a `GET /v1/training/status 200 OK` |
| uvicorn shutdown lines | none — no `Shutting down`, no traceback, no exit code |
| `syslog` OOM in the window | none (`grep -iE 'oom|killed process'`, `Aug 10 19:00–21:59` → no hits) |

An abrupt end mid-request with no graceful shutdown and no OOM is a **hard external kill**. This is the
second occurrence of the **F-ML-001** class already in this ledger — and the sibling helper
`util/ad-hoc/e2e_cascor_leg_restart.bash` was written during the *first* occurrence, its header recording
"after an orphan-reaper pass took down the nohup-detached cascor service". A concurrent experiment
campaign was active across the window (run dirs `20260811T022342Z` … `20260811T042344Z` under
`~/.local/state/juniper-experiments`), and orphaned `JuniperCascor1` forkserver children from a dead
experiment_stack cascor (port 8230, ~4.8 h old) were still resident. F-ML-001 therefore stands **unfixed
and demonstrably recurrent**: the isolated stack's nohup-detached services remain reapable by any
concurrent session's cleanup pass. The pidfile-exclusion / listener-port KEEP gate proposed in F-ML-001 is
what would have prevented both occurrences.

Recovery: `bash util/ad-hoc/e2e_cascor_leg_restart.bash` → `cascor healthy on 8202`. Canopy was **not**
touched, so the browser CSRF context stayed valid and no F-CANOPY-008 slot was burned.

**Canopy reconnect — an unprompted resilience positive.** Canopy rode the entire 7.6 h outage and healed
itself with no intervention: `Control stream supervisor connected to ws://127.0.0.1:8202` at `04:14:04`
and `Cascor metrics stream connected` at `04:14:19`, with the next relay summary reading
`status=healthy; reconnects=1`. The supervisor's fixed 30 s control-stream backoff and the metrics
stream's escalating backoff both behaved as designed across a multi-hour outage. Relevant to the W14
outage-recovery rows.

### Precondition change — restore now targets an EMPTY cascor

The restarted cascor came back with no in-memory model: `GET :8202/v1/network` → `404 "No network created"`,
FSM `STOPPED/IDLE`, `current_hidden_units: 0`. The trained 10-unit network segment 4 handed forward is
**gone**; the snapshot file survived on disk (`snapshot_20260811T010849Z.h5`, 296 701 bytes).

This *strengthens* W5 steps 4-7 rather than weakening them: the restore is now exercised into a genuinely
empty backend, which is the honest test of the restore path, and its success becomes the precondition for
steps 8+ instead of being masked by a network that was already resident. Recorded here because any later
row that assumes "10 units were already loaded" must read this note first.

### Findings opened in segment 5

**F-CANOPY-009 — the snapshot detail panel is wiped by the table's own 10 s refresh: every selection
self-destructs within one tick (P1; root-caused live; canopy#520 `29a8c41e`; W5 step 4 re-drive 2026-08-26 → detail panel held past two refresh ticks; VERIFIED LIVE, FIXED).**

Found driving W5 step 4. The row's `View Details` button *does* work — the panel fills correctly — and then
the panel clears itself with no user action. Measured live, single click, 500 ms polling of
`#hdf5-snapshots-panel-detail-panel`:

| t (ms from probe start) | Panel content |
|---|---|
| 10 527 | `Select a snapshot from the table above to view its details.` (placeholder) |
| **14 308** | **`ID: snapshot_20260811T010849Z  Name: snapshot_20260811T010849Z.h5  Times…`** (filled) |
| **21 320** | `Select a snapshot from the table above to view its details.` (**wiped**) |

Visible lifetime ≈ **7 s**, bounded above by the panel's 10 s refresh tick. The first three attempts of this
row were recorded as "button does nothing" purely because each post-click read at +7–10 s sampled *after*
the wipe — the defect masquerades as a dead button.

Mechanism, captured from the wire (`_dash-update-component` request/response pairs):

1. `select_snapshot` (`juniper-canopy/src/frontend/components/hdf5_snapshots_panel.py:995`) fires with
   `changedPropIds` naming the row button's `n_clicks` and `state` carrying the correct
   `{"type":"hdf5-snapshots-panel-view-btn","index":"snapshot_20260811T010849Z"}` — and returns
   `{"hdf5-snapshots-panel-selected-id":{"data":null}}`. The serialized `inputs` entry carries **no
   `value` key**, i.e. `n_clicks` arrives falsy.
2. `update_detail_panel` (`:1038`) then fires with `selected-id.data = null` and returns the placeholder
   `P` element — captured verbatim in the same trace.

Why `n_clicks` is falsy on that second firing: `update_snapshots_table` (`:868`) is driven by
`Input(f"{component_id}-refresh-interval", "n_intervals")` (`:862`) on a **10 s** interval
(`DEFAULT_REFRESH_INTERVAL_MS = 10000`, `:53`; wired `:361-364`) and rebuilds **every row from scratch**
each tick. The rebuilt `View Details` button (`:920-927`) is constructed **without `n_clicks=0`** — unlike
all four sibling op-buttons (`:936-954`), which each pass it explicitly. Its counter therefore returns as
`None`, the pattern-matching `Input(..., ALL)` sees the input list change, and `select_snapshot` re-fires
with `n_clicks_list = [None]`. It hits its own guard at `:997-998`:

```python
if not n_clicks_list or not any(n_clicks_list):
    return None
```

`any([None])` is `False`, so the callback **clears** the store rather than leaving it alone — and the
detail panel follows it down.

Two structural notes that matter at fix time:

- All four early-outs in this callback (`:998`, `:1002`, `:1007`, `:1012`) `return None`. Every one of them
  means "nothing meaningful triggered me", yet each **destroys** existing selection state. `dash.no_update`
  is the correct return for all four and `dash` is already imported at `:41` — the fix is a one-token change
  per site, not a refactor.
- The author's own fallback at `:1022-1030` ("find the button with highest `n_clicks`") is **dead code**: it
  sits in the `except json.JSONDecodeError` arm, which is only reachable *after* passing the `:997` guard
  that already rejected this exact state. Someone anticipated this failure mode and the guard above it
  prevents the remedy from ever running.

Blast radius: W5 step 4, and every downstream row that needs a *stable* selection — the detail panel is the
only surface exposing a snapshot's HDF5 attributes (`format_version`, `serializer_version`,
`juniper_version`), so the V1/V2 determination behind W5 step 18 cannot be made from the UI. Any operator
reading a snapshot's provenance has a ≈7 s window per click.

Note the contrast with **F-CANOPY-007**: that one made the list unreachable on a split filesystem; this one
makes the *detail* unreadable even when the list is correct. They are independent defects on the same
panel, and 007's fix is what made 009 observable at all.

Fix direction (Phase 2): return `dash.no_update` from all four early-outs in `select_snapshot`, and
construct the `View Details` button with `n_clicks=0` to match its siblings so the rebuild stops
re-triggering the callback at all. Regression test: select a snapshot, hold past two refresh ticks
(> 20 s), assert the detail panel still renders the selected id.

**FIX MERGED (2026-08-25, canopy#520 `29a8c41e`; W5 step 4 re-drive owed).** Exactly the prescribed one-token change: all four early-outs of `select_snapshot` return `dash.no_update`, and the `View Details` button is built with `n_clicks=0` like its four op-item siblings, so the rebuild stops re-triggering the callback at all. `src/tests/unit/frontend/test_f009_f010_snapshot_rebuild_preserves_state.py` (14 tests, 13 failing on the parent) pins the rebuilt button's `n_clicks == 0`, every rebuild-shaped re-fire leaving the selection alone, and a selection surviving a rebuild; the five `test_hdf5_callbacks.py` tests that had pinned the destructive `None` now assert `no_update`.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f009`).** `View Details` filled at +12.5 s and **stayed filled** through the full 32 s watch (two 10 s refresh ticks) — the table-refresh wipe is gone. W5 step 4 → PASS. **FIXED.**

**F-CANOPY-010 — the snapshot-operation CONFIRMATION MODAL closes itself ~3.6 s after opening; the
operator has under four seconds to read and confirm a state-changing action (P1; root-caused live; canopy#520 `29a8c41e`; re-drive 2026-08-26 → modal survived 65.8 s; VERIFIED LIVE, FIXED).**

Same class as F-CANOPY-009, different callback, worse consequence — recorded separately because it needs
its own fix and its own regression test. Found driving W5 step 5.

The modal opens **correctly**. Body captured live, matching the matrix expectation on both halves:

> `Confirm Restore of snapshot: snapshot_20260811T010849Z` · `Load this snapshot for inspection and
> modification. Training is NOT started — invoke Retrain or Resume to begin a training run.` · `⚠️ Training
> must …`

Then it decays, in two stages, with no user action:

| t (ms from click) | State |
|---|---|
| 2 256 | modal open, body correct |
| 4 765 | modal still open, **body emptied** (`""`) |
| 5 887 | **modal gone** |

≈ **3.6 s** of usable life. Mechanism: `open_snapshot_op_modal`
(`hdf5_snapshots_panel.py:1151`) is fed by `Input({"type": …-snapshot-op-btn, "index": ALL, "op": ALL},
"n_clicks")` (`:1146`). The same 10 s `update_snapshots_table` rebuild that drives F-CANOPY-009 reconstructs
the dropdown items, re-firing this callback with a falsy `n_clicks`; it takes one of its four early-outs
(`:1167`, `:1171`, `:1175`, `:1198`), each of which returns the triple

```python
return False, "", None      # is_open=False, modal_body="", pending_id=None
```

— i.e. it *actively slams the dialog shut, blanks its body, and discards the pending operation id*. The
two-stage decay above is exactly those three Outputs landing across ticks. Note the op-buttons **do** carry
`n_clicks=0` (`:936-954`), so unlike F-CANOPY-009 this is not a missing-default bug — the guard at `:1170`
rejects the rebuilt `0` as falsy just the same. The fix is the same one-token change (`dash.no_update`,
already imported at `:41`) at all four sites.

Severity above F-CANOPY-009: this is the **confirmation gate for restore / replay / resume / retrain** — the
operations that mutate live training state. A confirmation dialog that revokes itself in 3.6 s either
trains the operator to click without reading, or silently drops the action. It also discards
`-restore-pending-id`, so the pending operation is gone even if the button were still reachable.

Reproduction is deterministic and needs no special timing: open any row's op menu, pick any operation,
wait four seconds.

**FIX MERGED (2026-08-25, canopy#520 `29a8c41e`; the ≥ 20 s modal-survival re-drive owed).** All four early-outs of `open_snapshot_op_modal` return `(no_update, no_update, no_update)`; the rebuild-shaped re-fires (`n_clicks` 0 / None, no trigger, empty prop id, unknown op, the context-menu store reset) are pinned to leave an OPEN modal untouched while a real click still opens it with the right pending operation.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f010`).** The restore confirm modal opened and **survived the full 65.8 s watch** with its body intact (was self-closing at ~3.6 s). Cancel-close is a provably-correct one-liner (`return False if n_clicks else no_update`); the harness's open-after-cancel read is a fade-timing artifact, no `/api/v1/snapshots` POST fired. W5 step 5 → PASS. **FIXED.**

### W5 steps 5-7 — results

- **Step 5 PASS.** Modal opens with the correct title and the ⚠️ training-state warning (body quoted above).
  The self-close is filed as F-CANOPY-010, not as a step-5 failure — the step's stated expectation is met.
- **Step 6 PASS**, and proven on the wire rather than by timing. Cancel produced exactly one
  `_dash-update-component` carrying `restore-cancel`, answered
  `{"hdf5-snapshots-panel-restore-modal":{"is_open":false}}` — the dedicated cancel callback (`:1209-1210`)
  — with **zero `/api/` requests** in the window, satisfying "modal closes, no request". Timing confirms the
  close was the click and not the F-CANOPY-010 decay: modal open t=3383 ms, cancel clicked t=3390 ms, closed
  t=6172 ms.
- **Step 7 INCONCLUSIVE — re-run required.** Confirm fired and the panel rendered
  `❌ Failed (restore): Failed to restore snapshot`, but **the cascor leg was already dead when it landed**,
  so this is environmental and *not* a canopy verdict. A direct probe taken while cascor was down returned
  the identical `HTTP 500 {"detail":"Failed to restore snapshot"}` from
  `POST :8051/api/v1/snapshots/{id}/restore` — canopy's message is faithful to an unreachable backend.
  Recorded as INCONCLUSIVE rather than FAIL. One honest-label observation does survive: the surface reports
  failure correctly but carries **no diagnostic** distinguishing "backend unreachable" from "restore
  rejected" — the operator cannot tell these apart from the UI.

### F-ML-001 UPGRADE — three confirmed kills in one session; the trigger is now pinned

F-ML-001 was filed as "the reaper can kill nohup-detached isolated-stack services". This segment escalates
it from a hazard to a **demonstrated, repeating, arc-blocking failure**, and pins both the trigger and the
selectivity.

Three kills of the isolated cascor leg (8202) inside ~1 hour, each within ~2 s of a concurrent
experiment-campaign run directory being created:

| # | cascor log last write | Concurrent run dir created | Δ |
|---|---|---|---|
| 1 | `2026-08-11 01:36` (local 20:36 Aug 10) | campaign active across the window | — |
| 2 | `04:34:01.118` | `20260811T093401Z-3b2b` → 04:34:01 | **~0 s** |
| 3 | `04:36:45.999` | `20260811T093647Z-dae2` → 04:36:47 | **~2 s** |

Every kill is abrupt: last line is a served request, no uvicorn `Shutting down`, no traceback, and no OOM
in `syslog` for any window. Kill #3 landed *mid-gesture*, between the restore-confirm click and its
response — which is what produced the INCONCLUSIVE W5-07 above.

**Why cascor and not the other two legs** — the reaper's predicate explains the selectivity exactly, and
all three legs behave as predicted:

| Leg | cmdline | Matches `JuniperC[a-z0-9]+` gate? | Parentless? | Outcome |
|---|---|---|---|---|
| cascor 8202 | `/opt/miniforge3/envs/**JuniperCascor1**/bin/python3.13 …/uvicorn api.app:create_app` | **yes** | yes (ppid 1/systemd — nohup by design) | **killed, 3×** |
| data 8101 | `/tmp/juniper-e2e/.venv-data/…/python -m juniper_data` | no (venv path) | yes | survived |
| canopy 8051 | `python main.py` (bare argv; env path not in cmdline) | no | yes | survived |

So the leg that dies is precisely the one whose **conda env name appears in its cmdline**. Data and canopy
survive by accident of how they are invoked, not by any protection — F-ML-001's original note that canopy
"is equally exposed" is confirmed as *conditionally* true: it escapes only because `python main.py` hides
`JuniperCanopy1`.

**The trigger is an operator action, not the campaign scripts.** `util/experiments/**` and
`util/experiment_stack.bash` contain no `reap_pytest_orphans` / `kill_all_pythons` / `pkill` / `killall`
invocation (greps clean). The kills therefore come from the concurrent session's *manual pre-run reap* —
the standing practice of clearing orphaned `JuniperCascor1` forkserver children before each campaign run
(the known GPU-leak class). Corroborating: the ~4.8 h-old orphaned forkserver children from a dead
experiment cascor on port 8230 that were resident at segment start were gone after kill #2.

Consequence for this arc: **the isolated cascor leg cannot be kept alive while the campaign runs**, and
189 matrix rows remain, most of which need it. This is a coordination/tooling blocker, not a canopy defect
— escalated to the session owner rather than worked around, because every available workaround either
deviates from the byte-matched launch recipe the E2E evidence depends on, or edits a shared tool another
running session is actively using.

#### Remedy adopted (owner-selected): supervise the leg under a live parent

`util/ad-hoc/e2e_cascor_leg_supervise.bash` (new) launches the cascor leg as a **direct child of a resident
supervisor** instead of via `( … nohup … & )`. It targets the reaper's *orphan* predicate only — the
uvicorn argv, the §6.1 env set, the port, the CWD, and the log destination stay byte-identical to
`cascor_up` / `e2e_cascor_leg_restart.bash`, so nothing the E2E evidence observes about canopy↔cascor
behaviour changes. The supervisor's own argv (`bash util/ad-hoc/e2e_cascor_leg_supervise.bash`) does not
match the `JuniperC[a-z0-9]+` candidate gate, so the supervisor is never itself a reap candidate and the
child can never re-classify to orphan.

**Verified with the reaper itself** — `util/reap_pytest_orphans.bash --dry-run --verbose` against the
running supervised stack:

```text
KEEP       pid=437062 ppid=437053 (live parent) cmd=…/JuniperCascor1/bin/python3.13 …/uvicorn api.app:create_app --
WOULD REAP pid=3695742 ppid=25920 cmd=…/JuniperCascor1/bin/python3.13 -c … multiprocessing.forkserver …
…
Dry-run summary: 5 would be reaped, 4 kept (live parent), 0 skipped.
```

The E2E leg is classified **KEEP (live parent)** by the very tool that killed it three times, while the
stale campaign forkserver orphans are still correctly flagged for reaping. The F-ML-001 dry-run/live delta
caveat (children of reaped orphans re-classify mid-pass) does not reach this leg: its parent is not a
candidate in any pass.

Two limits worth stating plainly:

- This defends against the **orphan reaper only**. A blanket killer (`kill_all_pythons.bash` and friends)
  kills regardless of parentage and would still take the leg down.
- cascor's own multiprocessing **forkserver children** remain orphan-classified candidates. Reaping those
  does not kill the service (its parent is the supervisor) but can disrupt an in-flight training run — so a
  reap during a live W1/W2 run is still not safe.

Auto-restart is deliberately **opt-in** (`--restart`, default off) so a genuine cascor crash stays visible
instead of being silently papered over mid-run; every child exit is timestamped to
`${LOG_DIR}/juniper-cascor-supervisor.log` either way, so a row verdict can always be checked against
whether the backend restarted underneath it.

F-6 note: because uvicorn is a *direct* child here, `$!` genuinely is the server pid, so the pidfile this
script writes is honest — unlike the subshell form, where `$!` is the subshell.

---

## Phase 1 — segment 6 (2026-08-12): W5 steps 7-10

### Stack state on entry — the supervision remedy held

All four legs healthy on arrival; **the cascor leg had been up 10.6 h uninterrupted** under
`util/ad-hoc/e2e_cascor_leg_supervise.bash` (supervisor pid 437053, child pid 437062, started
`2026-08-12 09:44:52-0500`). `${LOG_DIR}/juniper-cascor-supervisor.log` records **zero child exits** across
the whole segment, so every verdict below is a genuine canopy verdict rather than an environmental
artifact — the exact confound that made W5-07 inconclusive in segment 5. `reap_pytest_orphans.bash
--dry-run` still reports `KEEP pid=437062 ppid=437053 (live parent)`. The F-ML-001 remedy is holding.

Restore precondition was as segment 5 left it: cascor network **empty** (`GET :8202/v1/network` →
`"No network created"`), snapshot `snapshot_20260811T010849Z` intact on disk (296701 bytes). Clean
restore-into-empty.

### W5-07 — RE-RUN: PASS (was INCONCLUSIVE)

Driven as one `page.evaluate` gesture per the segment-5 technique (CDP round-trips are far too slow for
F-CANOPY-010's ~3.6 s modal window). Timings from inside the page: restore op-btn clicked `t=9 ms`,
confirm button visible `t=1837 ms`, **restore-confirm clicked `t=1844 ms`** (comfortably inside the decay
window), status settled `t=4282 ms`.

- **UI**: `#hdf5-snapshots-panel-restore-status` → `✅ Restored from snapshot 'snapshot_20260811T010849Z'`.
- **Modal body** (re-confirming W5-05): `Confirm Restore of snapshot: snapshot_20260811T010849Z / Load this
  snapshot for inspection and modification. Training is NOT started — invoke Retrain or Resume to begin a
  training run. / ⚠️ Training must be paused or stopped before any snaps…`
- **Wire** (server-side, per the §methodology note — the browser log carries only
  `_dash-update-component`; a filtered capture of 1978 requests contained **zero** `/api/v1/snapshots`
  entries, confirming the call is canopy→cascor): cascor log shows
  `POST /v1/snapshots/snapshot_20260811T010849Z/restore HTTP/1.1" 200 OK` and
  `api.lifecycle.manager - INFO - Snapshot restored: snapshot_20260811T010849Z (FSM=Investigating)`
  at `2026-08-12 20:24:03,610`.
- **Backend truth** (the half that was missing): `GET :8202/v1/network` → `input_size:2, output_size:2,
  hidden_units:10, max_hidden_units:10, uuid d5827628-4843-4910-a9ba-aec16f0de3ee`;
  `/v1/network/topology` returns all 10 units with the correct CasCor cascade fan-in (unit 0 → 2 weights,
  unit 1 → 3, unit 2 → 4, …). Empty → 10 units, correlated to the click, on a leg proven not to have
  restarted.

The segment-5 honest-label note stands and is now sharper: canopy's failure copy was faithful to a dead
backend, and its success copy is faithful to a live one — but **neither carries a diagnostic
distinguishing the two**, which is precisely why the row needed a supervised leg to adjudicate.

### W5-08 — PASS

`GET :8051/api/status` → `fsm_status = 'INVESTIGATING'`, corroborated at the source by cascor's
`/v1/training/status` → `state_machine.status = "INVESTIGATING"`, `phase = "IDLE"`. Restore did **not**
start training (`training_state.status "Stopped"`, `is_training false`) — matching the modal's own copy.

### W5-09 — FAIL (F-CANOPY-011)

Expected: idle block hides, active block shows, `#network-editor-panel-idle-fsm-badge` reads
`FSM: Investigating`. Observed, **stable across 6 samples spanning 12.5 s** (not a transient):

| element | expected | observed |
|---|---|---|
| `#network-editor-panel-idle-fsm-badge` | `FSM: Investigating` | `FSM: Unknown` |
| `#network-editor-panel-idle` | hidden | `display: block` (visible) |
| `#network-editor-panel-active` | shown | `display: none` (hidden) |

The panel never leaves its idle state, so the entire active editing surface — add-unit, remove-unit,
patch-weights — is unreachable through the UI while the FSM is genuinely `INVESTIGATING`.

### W5-10 — PASS (expected divergence D-0), but the cause is now known to be doubled

`#network-editor-panel-topology-readout` → `No topology loaded.` and `#network-editor-panel-remove-idx`
options `[""]` (empty) — exactly the matrix's "expected today" text, so the row passes as written.

The new information is *why*. There are **two stacked defects**, and the first masks the second:

1. **F-CANOPY-011** short-circuits at `network_editor_panel.py:505` before the topology fetch is ever
   attempted, returning `topology-store = None` → `render_topology` renders the placeholder.
2. **D-0** — the fetch at `:517` targets `/api/network/topology`, which is **404** (verified live); the
   working route is `/api/topology` (**200**, serving `input_units:2, output_units:2, hidden_units:10`,
   14 nodes, 89 connections).

**Operational consequence: fixing D-0's route alone will NOT revive the Network Editor.** Both the FSM key
and the route must be corrected, or the panel stays idle and the readout stays on the placeholder.

### Findings opened in segment 6

**F-CANOPY-011 — the Network Editor reads the FSM from a key shape canopy's `/api/status` never returns,
so the panel is permanently inert (P1; root-caused, deterministic; canopy#522 `ef495cf3` with D-0; re-drive 2026-08-26 → active surface, FSM Investigating, topology 2/9/2; VERIFIED LIVE, FIXED).**
`network_editor_panel.py:400-412` (`_is_investigating`) and the badge line `:501` both read
`status["state_machine"]["status"]`, falling back to a top-level `status["status"]`. Canopy's `/api/status`
returns **neither**: it is a flat dict whose FSM field is `fsm_status`. Verified live against the running
service — `'state_machine' in payload → False`, `'status' in payload → False`,
`payload['fsm_status'] → 'INVESTIGATING'`. `state_machine` is *cascor's* `/v1/training/status` schema, not
canopy's; the panel was written against the upstream shape but points at the canopy proxy. The docstring at
`:403-406` asserts the wrong contract in prose ("nests the FSM summary under `state_machine`"), which is
why it reads as correct on inspection. Consequently `_is_investigating` returns `False` unconditionally,
`:505` always takes the not-investigating branch (`idle: block`, `active: none`), and `:501` renders
`"Unknown".title()` → `FSM: Unknown`. This is a complete feature blackout of a shipped panel, independent
of actual FSM state, and it masks D-0 (`:517` → `/api/network/topology`, 404; the live route is
`/api/topology`). Blast radius: W5-09 FAIL; W5-12/13/14 have **no UI path** and must be driven at the API
to prove the routes; M-NETWORK-EDITOR rows that assert the active surface. Fix is two contract
corrections (read `fsm_status`; fetch `/api/topology`) plus a test that pins the panel against a real
`/api/status` payload rather than a hand-built one.

**FIX MERGED (2026-08-26, canopy#522 `ef495cf3`, together with D-0; W5-09 (was FAIL), W5-10 (was PASS-as-expected-divergence), W5-12/13/14 through the UI, and the M-NETWORK-EDITOR active-surface rows re-drive owed).** Exactly the two contract corrections: `_is_investigating` and the badge read canopy's flat `fsm_status` first (the nested `state_machine.status` and top-level `status` shapes stay tolerated for cascor-shaped or partial payloads, so every existing pin holds; the docstring that asserted the wrong contract is corrected), and the active-state fetch targets `/api/topology`, whose `{input_units, output_units, hidden_units}` shape `render_topology` already consumed. `src/tests/unit/frontend/test_f011_d0_network_editor_contracts.py` (17 tests, 7 failing on the parent) pins the panel to the REAL contracts — the `StatusResult` TypedDict, the real `/api/status` payload through `main.app` with a demo backend installed, the flat-payload poll behaviour, the exact `[/api/status, /api/topology]` fetch sequence, and the real app answering `/api/network/topology` 404. D-0 closes with it.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f011,f011check`).** After a UI restore (FSM → `INVESTIGATING`), the editor's active surface rendered with badge **`FSM: Investigating`** (the flat `fsm_status` read), the topology readout **`Inputs: 2 Outputs: 2 Hidden units: 9`** (the `/api/topology` fetch — was a permanent 404 → *"No topology loaded."*), and the remove dropdown **populated** (10 options; was empty under D-0); a UI **remove** operated live (10 → 9 hidden units; `/api/topology` = 2/9/2). The render lagged ~65 s under F-CANOPY-004 congestion during the restore+ops window (the `f011check` quiescent re-read is clean) — F-004, not an F-011 regression. W5-09/-10 → PASS. **FIXED.**

**F-CASCOR-002 — snapshot restore ALWAYS drops optimizer state: `learning_rate` is written as a string and
read back undecoded, so the Adam constructor raises and the optimizer is silently set to `None` (P1, cascor
repo, OPEN; root-caused and reproduced; FILED 2026-08-30 as
[juniper-cascor#602](https://github.com/pcalnon/juniper-cascor/issues/602)).**

> **Severity synchronised 2026-08-30, not re-judged.** This header read `P2` while the UPGRADE section
> below — written in the same segment — argues `P2 -> P1` and gives the artifact evidence for it. The
> header was simply never updated, so the triage script has been counting this finding one band low ever
> since. Changing the header to `P1` makes it agree with its own body; no new judgement was made here.
Save/load asymmetry in `src/snapshots/snapshot_serializer.py`. `:448` writes
`write_str_attr(opt_group, "learning_rate", network.learning_rate)` — a **string** attribute. `:1037` reads
it back with a raw `opt_group.attrs.get("learning_rate", …)` — **no decode** — while its sibling one line
up (`:1036`, `optimizer_type`, written by the same `write_str_attr`) *is* decoded via `read_str_attr`.
Direct probe of the live artifact confirms the on-disk types: `params/output_layer/optimizer` attrs are
`learning_rate = np.bytes_(b'0.1')`, `optimizer_type = np.bytes_(b'Adam')`. The undecoded value flows to
`:1050` `optim.Adam(output_layer.parameters(), lr=learning_rate)`, where torch's range check
(`0.0 <= lr`) raises — reproduced verbatim in the JuniperCascor1 env:
`TypeError: '<=' not supported between instances of 'float' and 'numpy.bytes_'`. `:1026-1028` catches it,
logs `Could not restore optimizer: …` at **WARNING**, and sets `network.output_optimizer = None`. This is
deterministic, not intermittent: every restore of every snapshot loses optimizer state. Observed live in
this segment's restore. The codebase is internally inconsistent about the same field — `:336` writes
`config_group.attrs["learning_rate"]` as a native float. Severity is P2 because the weights restore
correctly and the network is usable for inspection; the **consequence for resume/retrain (W5-27) is
verified at that row**, since `output_optimizer = None` may either be lazily rebuilt or fault. Surface
honesty gap: canopy reports an unqualified `✅ Restored` while the backend has degraded the restore, and
the warning exists only in the cascor log. **Scope widened later in the segment:** the same warning fires
on the **replay** load path too (cascor log, `20:45:31` and `20:51:19`, both `POST …/replay` starts), so
this is not restore-specific — it is every snapshot load path that reaches
`_load_optimizer_state_from_hdf5_helper`.

### Observations (segment 6, non-finding)

- **`/api/status.hidden_units` is stale after a restore.** For the same restored network, canopy's
  `/api/status` reports `hidden_units: 0` while `/api/topology` reports `10` and cascor's `/v1/network`
  reports `10`. The source is cascor's `/v1/training/status` **`monitor`** block
  (`monitor.current_hidden_units: 0`) — training telemetry, which is legitimately zero because no training
  has run since the restore. Recorded as a finding-*candidate* rather than a finding: no consumer has yet
  been shown to render network size from this field. Any that does would show a restored 10-unit network
  as empty. `input_size`/`output_size` on the same payload are correct (2/2).
- **Topology tab reads 0/0/0 for the restored network** (`#network-visualizer-{input,hidden,output}-count`)
  while `/api/topology` serves 2/10/2. This **corroborates F-CANOPY-006** (counts stay at the layout-default
  `"0"`s and the DOM never updates) rather than being new, and it is *not* attributable to the stale
  `/api/status.hidden_units` above — under F-CANOPY-006 those counts never update from any source.
- **Step-11 inputs resolved.** `I = 2`, `H = 10` taken from `/api/topology` (the topology DOM being dead
  per F-CANOPY-006), confirming the handoff's pre-computed **append weight-vector length of `I + H` = 12
  floats** for W5-13.

### W5 steps 11-15 — the editor works; only its gate is broken

**The load-bearing result of this segment.** Every Network Editor control is `present: true,
disabled: false, visible: false` — enabled, in the DOM, inside the block F-CANOPY-011 keeps hidden.
Driving them by raw JS (which Dash honours regardless of CSS visibility) exercised the full callback →
canopy route → adapter → cascor path **successfully**, including two real mutations that landed in cascor.

**Therefore F-CANOPY-011 is a visibility/gating defect ONLY.** The editor's callbacks, canopy's three
proxy routes, and cascor's validation are all sound. This bounds the fix to the two contract corrections
and is why F-CANOPY-011 is filed P1-unreachable rather than P0-broken.

Control types (relevant because the T-7 numeric wall does *not* obstruct this panel): `patch-values` and
`add-weights` are `<textarea>`; `patch-target`, `add-activation`, `remove-idx` are `<select>`; only
`patch-idx` and `add-bias` are `input[type=number]`, and both ship at usable defaults (`0` / `Tanh`), so
no numeric field had to be driven.

| step | verdict | evidence |
|---|---|---|
| W5-11 | PASS | `I=2`, `H=10` from `/api/topology`; `output_weights` is 12 × 2, cascade fan-in 2,3,4,…,11 |
| W5-12 | PASS (both arms) | shape violation rejected **without mutating**; valid 1-D patch landed |
| W5-13 | PASS (after cap reorder) | cap-refused at H=10; appended after the step-15 delete |
| W5-14 | PASS | count 9 → 10, verified at the API (DOM oracle dead per F-CANOPY-006) |
| W5-15 | PASS | `DELETE …/hidden-units/9` → 200; UI path blocked, twice over |

**W5-12 — negative arm (the matrix's explicit requirement).** Target `output_weights`, 24 flat floats
(`0.01 … 0.24`, row-major for the 12 × 2 shape) →
`Patch failed: patch_weights failed: shape mismatch: output_weights expects (12, 2), got (24,)`.
Re-reading `/v1/network/topology` immediately after shows `output_weights` **byte-identical** to the
pre-state (`[[0.08172,-0.08172],[0.32116,-0.32093],[0.64142,-0.64161]]`) — the matrix's "must be rejected
without mutating state" is satisfied, and the error text is precise and actionable.

**W5-12 — positive arm.** Target `output_bias`, values `0.25, -0.25` → `Patched output.bias (2 values).`;
`/v1/network/topology` then reports `output_bias = [0.25, -0.25]`. The write path is proven end-to-end.

**W5-13 — as specified, then reordered.** With H=10 the append was refused:
`Add failed: add_hidden_unit failed: network is at max_hidden_units cap (10)` — an honest business-rule
refusal (the restored snapshot is a fully-grown network at `max_hidden_units: 10`), not a defect; state
unmutated. The success path therefore required freeing a slot, so **step 15 was executed before step 13**
and the append vector recomputed at the new H: `I + H = 2 + 9 = 11` floats. Result:
`hidden_units 9 → 10`, tail unit id 9 carrying **exactly** the sent ramp
`[0.31,0.32,…,0.41]` (11 weights), `bias 0.0`, `activation Tanh` — the shipped defaults, uncoerced.

**W5-15 — route proven, UI path blocked twice.** `DELETE :8051/api/v1/network/hidden-units/9` (canopy's
proxy, `main.py:2745-2755`) → **HTTP 200**, body `removed_index: 9`, `num_hidden_units: 9`,
`fsm_state: "INVESTIGATING"`; count 10 → 9. The UI path is unreachable for **two independent reasons**:
`#network-editor-panel-remove-idx` has options `[""]` (D-0 — the topology that would populate it never
loads) *and* the whole active block is hidden (F-CANOPY-011).

Final network state left for the replay rows: `input 2 / hidden 10 / output 2`, `output_bias [0.25,-0.25]`,
tail unit = the synthetic ramp. The snapshot `.h5` on disk is **untouched** by all of this, so W5-16/27
still replay and resume from the pristine artifact.

### Findings opened in segment 6 (continued)

**F-CANOPY-012 — `output_weights`, the Network Editor's DEFAULT patch target, is structurally impossible
to patch from the UI: the panel parses a flat 1-D list while the route requires 2-D (P2, OPEN;
root-caused).**
`_parse_float_list` (`network_editor_panel.py:415-431`) returns a **flat** `List[float]`, and
`on_patch_weights` (`:721-760`) forwards it verbatim as `body["values"]` — there is **no reshape anywhere**
in the callback, and none is possible today because the topology needed to infer the shape is exactly what
D-0/F-CANOPY-011 withhold. cascor requires `output_weights` as `(I+H, output_size)` = `(12, 2)`, so any
input a user can type is rejected: `shape mismatch: output_weights expects (12, 2), got (24,)`. Of the
four dropdown options, only this one is 2-D — `output_bias` (1-D), `hidden_unit_weights` (1-D per unit),
and `hidden_unit_bias` (scalar) all round-trip fine, and `output_bias` was proven to land live. The broken
option is the dropdown's **first and default** value, so it is the first thing any operator tries.
Mitigating: the failure is loud, precise, and non-mutating. Fix options are a 2-D-aware parse (accept
nested `[[…],[…]]`) or a reshape using `(I+H, output_size)` once the topology is available — which makes
this dependent on the D-0 route fix.

**F-CANOPY-013 — Network Editor success messages read payload keys off the response ENVELOPE, so a
successful append reports `index None (now None hidden units)` (P2, OPEN; root-caused, one latent second
instance; re-tagged 2026-08-24 from an out-of-vocabulary "P3" — the plan §9 severity scale is P0/P1/P2
only, and the untagged state made `e2e_finding_triage.py` report the finding as priority `?`).**
`_post_json` (`:433-465`) returns `{"success": True, "data": resp.json()}` — i.e. `result["data"]` is the
**entire** cascor envelope `{"status":…, "data": {…}, "meta":…}`, as confirmed live by the DELETE response
body. But `on_add_unit` (`:608-611`) does `data = result["data"]; idx = data.get("unit_index"); total =
data.get("num_hidden_units")`, reading both keys off the envelope root where they do not exist; they live
one level deeper at `result["data"]["data"]`. Both resolve to `None`, producing the observed
`Appended unit at index None (now None hidden units).` on an append that in fact **fully succeeded**. The
key *names* are correct — cascor documents the add payload as carrying `unit_index`, `num_hidden_units`,
`operation` (`juniper-cascor src/api/routes/network.py:135`) — so this is purely a nesting-level error,
fixable in one line. Cosmetic only (no state is harmed, and the operation itself is correct), but it
degrades the one surface an operator has for confirming a blind mutation, and it does so on the *success*
path where nobody is looking for a bug. **Second, latent instance:** `on_remove_unit` (`:705-707`) repeats
the pattern verbatim and would render `Removed unit N (now None hidden units).` — unreachable today only
because the remove dropdown is empty, so it will surface the moment F-CANOPY-011 and D-0 are fixed. Fix
both call sites together.

### W5 steps 16-26 — replay starts perfectly, then cannot be controlled at all

**W5-16 PASS.** Replay op → modal body `Confirm Replay of snapshot: snapshot_20260811T010849Z / Start a
read-only playback session of this snapshot's training history. Use the replay player controls to scrub
through metric and topology evolution. / ⚠️ Training must b…` → confirm → **the active tab auto-switched
to `Replay`** (t=6125 ms) and the panel reported `✅ Snapshot replay started`. Both halves of the
expectation met.

**W5-17 PASS.** `#replay-player-panel-idle` is `display: none` (placeholder gone),
`#replay-player-panel-active` is `display: block`, `#replay-player-panel-snapshot-id` =
`snapshot_20260811T010849Z`, `#replay-player-panel-fsm-badge` = `REPLAYING`. All three halves met.

**W5-18 FAIL (F-CANOPY-015).** `#replay-player-panel-weights-badge` renders **`V1 (metrics only)`** in the
grey style. The snapshot is provably **V2 with weight history**: the artifact's own root attrs are
`format_version = b'2'`, `serializer_version = b'2.0.0'`, and `history/weights/` holds `output_weights`
and `output_bias` (3 samples each) plus `hidden_units` and `sample_indices`; cascor's own replay-start
response reports `session.weights_available = True` with
`weight_sampling {strategy: adaptive, interval: 50, num_samples: 3}`. The badge is reporting the opposite
of the truth, which per the matrix is the row's entire purpose ("Record which").

**W5-19 FAIL / W5-26 FAIL / W5-21, W5-22, W5-23 BLOCKED (all F-CANOPY-014).** Clicking
`#replay-player-panel-play-btn` (visible, enabled) leaves the status block on
`❌ Invalid URL '/api/v1/snapshots/snapshot_20260811T010849Z/replay/control': No scheme supplied. Perhaps
you meant https:///api/v1/…` and `#replay-player-panel-epoch-readout` frozen at `0 / 12` — playback never
advances. `#replay-player-panel-stop-btn` produces the **identical** error, proving the failure is
**action-independent**: every control action funnels through the one malformed URL at
`replay_player_panel.py:356`. The slider rows (seek / speed / range) are therefore recorded BLOCKED rather
than driven — the submit path is provably dead for every action, so dragging them could only re-observe
the same error.
**Backend exonerated on the wire**: a direct `POST :8051/api/v1/snapshots/{id}/replay/control
{"action":"play"}` returns **HTTP 200** with a full result block (`length: 12, time_index: 0, speed: 1.0,
paused: false, range {0,12}, weights_available: true`). canopy's route and cascor are both healthy; only
the panel's URL construction is broken.

**W5-20, W5-24, W5-25 BLOCKED (consequential).** The V2 last-sample drain, the Evolution weight-norms
un-hide, and the Decision-Boundary redraw all require playback to advance, which F-CANOPY-014 prevents.
W5-20 is doubly blocked — the panel also believes the session is V1 (F-CANOPY-015).

### Findings opened in segment 6 (continued)

**F-CANOPY-014 — the replay player builds every control URL with an EMPTY base, so the entire replay
control surface is dead: play / pause / seek / speed / range / stop all fail with `No scheme supplied`
(P1; root-caused, backend exonerated; canopy#521 `07e9a061`; re-drive 2026-08-26 → play/pause/stop POST absolute URLs, no scheme errors; VERIFIED LIVE (buttons), FIXED).**
`replay_player_panel.py:80` initialises `self._api_base_url = config.get("api_base_url", "")` — an
**empty-string** fallback. The runtime config does not supply `api_base_url`, so the base is `""` and
`:356` builds `f"{self._api_base_url}/api/v1/snapshots/{snapshot_id}/replay/control"` =
`"/api/v1/snapshots/…/replay/control"`, a schemeless relative path. `requests` rejects it verbatim:
`Invalid URL …: No scheme supplied.` The panel surfaces this honestly in its status block, but every
control is inert. A three-way comparison across the sibling panels isolates the defect precisely — this is
the **only** one of the three with an empty fallback:

| panel | line | base-URL expression | outcome |
|---|---|---|---|
| `hdf5_snapshots_panel.py` | `:79` | `f"http://127.0.0.1:{_settings.server.port}"` (unconditional) | works — create/restore/replay all landed |
| `network_editor_panel.py` | `:99` | `config.get("api_base_url", f"http://127.0.0.1:{_settings.server.port}")` | works — patch/add/delete all landed |
| `replay_player_panel.py` | `:80` | `config.get("api_base_url", "")` | **broken** |

Blast radius: W5-19/26 FAIL and W5-20/21/22/23/24/25 BLOCKED — the whole M-REPLAY control surface. Fix is
one line (adopt either sibling's fallback); the deeper question of why the config omits `api_base_url` is
worth answering so the two working panels aren't relying on defaults either.

**FIX MERGED (2026-08-26, canopy#521 `07e9a061`; W5-19/26 and W5-20..25 re-drive owed).** The sibling panels' fallback adopted verbatim — `config.get("api_base_url", f"http://127.0.0.1:{get_settings().server.port}")` — so every control POST is absolute by default while an explicit `api_base_url` still wins. `src/tests/unit/frontend/test_f014_replay_api_base_url.py` pins the default base to the configured server port and every control action (`play` / `pause` / `seek` / `speed` / `range` / `stop`) to `…/api/v1/snapshots/snap_1/replay/control` on that base — 7 of its 8 tests fail on the parent, which produced the schemeless `/api/v1/…` path. The deeper question the entry raised (why the runtime config omits `api_base_url` at all) stays open here as a note, not a defect.

**VERIFIED LIVE (2026-08-26, run `20260826T174225Z`, `e2e_p1wave_redrive.py --step f014`).** A replay session started, the tab switched to `Replay`, and the three **button** controls all POSTed to **absolute** URLs with success statuses (play → `✓ Seeked`, pause → `✓ Playing`, stop → `✓ Stopped`) with **zero** `No scheme supplied` errors — the empty-base-URL fix. The three slider controls (speed/seek/range) were instrument-limited (rc-slider drag did not land; `driven=False`, not errored) and share the same `dispatch_control` URL path; the slider rows W5-21..23 need an rc-slider drag idiom to re-drive. W5-19 (play) / W5-26 (stop) → PASS. **FIXED.**

**F-CANOPY-015 — the replay player reads three session fields one nesting level too shallow; the weights
badge therefore reports V1 for a V2 snapshot while two sibling misreads are silently masked by
coincidence (P2, OPEN; root-caused, empirically confirmed).**
cascor's replay-start payload nests the live session summary under a `session` key. Measured directly off
the running service, the `data` block's keys are
`['fsm_state', 'operation', 'session', 'snapshot_id', 'status', 'time_index', 'training_params']` while
`data.session` carries `['length', 'paused', 'range', 'snapshot_id', 'speed', 'time_index',
'weight_sampling', 'weights_available']`. canopy's `confirm_snapshot_op`
(`hdf5_snapshots_panel.py:1281-1287`) stores the **data block** as the session store — correct as far as it
goes — but `replay_player_panel.py:468-471` then reads `range`, `speed`, and `weights_available` off that
block's top level, where **none of the three exist**. The panel is inconsistent with itself: its own
`_session_window` (`:383-397`) and the `fsm_state` read (`:470`) *are* written against the unified
data-block shape and work correctly, which is why the epoch readout and FSM badge are right.
Observed consequences, exactly as the shapes predict:

| read | line | actual value | rendered | masked? |
|---|---|---|---|---|
| `weights_available` | `:471` | `True` (nested) | `V1 (metrics only)` | **no — visibly wrong** |
| `speed` | `:469` | `1.0` (nested) | `1×` via `SPEED_DEFAULT` | yes, by coincidence |
| `range` | `:468` | `{0, 12}` (nested) | `[0, 12]` via `[start, end]` | yes, by coincidence |

The two masked reads are latent: they render correctly **only** while the real session values happen to
equal the fallbacks, so a resumed session at a non-default speed or a user-narrowed range would display
stale defaults with no error. Same defect class as F-CANOPY-013 (a payload key read one level too
shallow), different file and different pair of keys — worth fixing as one sweep with a helper that
unwraps `session.session` once.

### W5 steps 27-29 — the tail rows

**W5-27 PASS — both operations 200 in the LIVE lane.** The row asks for "200 vs 409 vs 501 for each":

| op | code | resulting FSM | notes |
|---|---|---|---|
| `POST …/{id}/resume` | **200** | `RESUME_READY` | prepares a resume point; does **not** start training. `time_index.default = "end"`, window `{0, 12}` |
| `POST …/{id}/retrain` | **200** | `STOPPED` | resets to a fresh-run-ready state, window reset to `{0, 0}` |

Both were driven at the API after the UI modal gesture failed to open twice under page congestion (see the
methodology note below); the surrounding modal machinery is already proven by W5-05 and W5-16. The **409**
arm was not induced — it requires an active training run, which is out of this row's scope and would have
left the stack mid-run against the W5 cleanup contract. The **501** arm belongs to the DEMO-lane row
W5-30, not here. Both ops are recorded by the backend history surface, which is how W5-28 cross-validates.

**W5-28 PASS.** `#hdf5-snapshots-panel-history-toggle` flipped
`#hdf5-snapshots-panel-history-collapse` from `visible:false / .collapse` to `visible:true / .collapsing`,
and `#…-history-content` went from its `Loading history…` placeholder to real entries within 3.2 s:
`• RETRAIN snapshot_20260811T010849Z 2026-08-13 01:57:41 … • RESUME … 01:57:32 … • REPLAY_STOPPED …
01:54:41 …`. A satisfying cross-check: the history faithfully lists exactly the operations this segment
drove, in order. `GET /api/v1/snapshots/history` independently returns 200 with the same records.

**W5-29 PASS (dead-expected, proven statically).** Stronger than the row asks. The two ids
`{"type": "hdf5-snapshots-panel-swap-restore-pre-btn"…}` / `…-post-btn` occur in the entire panel **only**
at their construction sites (`hdf5_snapshots_panel.py:709` and `:720`) — there is **no `Input(...)`
anywhere referencing either**, so no callback can fire and the buttons are inert *by construction*, not
merely inert-on-the-day. Live confirmation: this session renders **zero** such buttons
(`swapBtnCount: 0`) because there are no dataset-swap events to build paired-diff cards from
(`#hdf5-snapshots-panel-dataset-swaps-content` is present but empty). The row's expectation — nothing
happens, no request, no console error — therefore holds vacuously and provably. Not click-driven: there
was nothing to click, and manufacturing a swap event to reach a button already proven callback-less would
add no evidence.

### Methodology notes (segment 6)

- **A click issued within ~10 ms of a tab render is silently lost.** The first W5-16 attempt clicked the
  replay op 7 ms after the Snapshots tab rendered and nothing happened — Dash had not yet wired the
  freshly-rebuilt pattern-matched Input. A **1.5-2 s settle before clicking** made it reliable. This is
  distinct from F-CANOPY-010 (which closes an *already-open* modal) and worth carrying forward: a lost
  click looks exactly like a broken control.
- **The confirm modal's DOM does not exist while closed.** `[id*="modal"]` returns `[]` on a settled
  Snapshots tab; the modal and its confirm button enter the DOM only on open. So "confirm button absent"
  is the normal closed state, not evidence of a defect — poll for the element to *appear*.
- **Page congestion is real and measurable.** Two `page.evaluate` gestures with ~43 s internal budgets
  exceeded 120 s of wall clock while the same operations succeeded instantly at the API. This is
  F-CANOPY-004 territory and it makes long in-page polling loops an unreliable instrument; where a row's
  assertion is about the *backend outcome* rather than the *UI gesture*, driving the API is both faster
  and more trustworthy.
- **Supervisor log clean for the whole segment.** `${LOG_DIR}/juniper-cascor-supervisor.log` still shows
  only the single `09:44:52` start and the `09:44:56` healthy line — **zero child exits** across every row
  above, so no verdict in this segment can be an environmental artifact.

---

## Phase 1 — segment 7 (2026-08-13): the Network Editor tab, 18/18

Branch `arc/canopy-e2e-phase1-seg7`, cut from the pushed seg6 tip `3562bff`; the seg6 worktree
`encapsulated-prancing-sun` is locked by another session, so this segment follows the arc's
one-worktree-per-segment pattern for the third time. Run id unchanged: `20260811T010700Z`.

### Stack state on entry

`data 8101 / cascor 8202 / canopy 8051` all `200`; cascor at **10/10** hidden units; 1 snapshot;
supervisor log still showing only the `09:44:52` start and `09:44:56` healthy lines — **zero child
exits**, now across two segments and ~19 h of uptime. The F-ML-001 supervision remedy continues to hold,
so nothing below is environmental.

### The headline: F-CANOPY-011 is now proven live, not inferred

Segment 6 established the defect by reading the code. This segment put it in front of the panel and
watched it fail, which is a materially stronger claim.

`POST /api/v1/snapshots/snapshot_20260811T010849Z/restore` → `200`, and canopy's **own** `/api/status`
then reported:

```json
{"fsm_status": "INVESTIGATING", "phase": "idle", "state_machine": null, ...}
```

That is the exact state the editor exists to unlock in. After waiting 5 s — more than two of the panel's
own 2 s poll cycles, so staleness is excluded — the panel was **unchanged**:

| element | observed | expected if the gate worked |
|---|---|---|
| `-idle` | `display:block`, `offsetParent` set | hidden |
| `-active` | `display:none`, `offsetParent` null | **visible** |
| `-idle-fsm-badge` | `FSM: Unknown` | `FSM: Investigating` |
| `-topology-readout` | `No topology loaded.` | the live topology |

The mechanism is visible in that JSON: `state_machine` is literally `null` and the field is `fsm_status`,
so `_is_investigating` (`:410-412`) evaluates `("" or "").upper() == "INVESTIGATING"` → `False`
**unconditionally**, and the badge falls all the way to its last-resort `Unknown`.

### The correction: the gate's *intent* is right — cascor enforces the same precondition

This is the segment's most consequential finding, and it revises segment 6's framing. Driving the append
and remove submits while the FSM was `STOPPED` produced, from **cascor**, not canopy:

```text
Add failed:    add_hidden_unit failed:    add_hidden_unit_manual requires INVESTIGATING state (currently STOPPED)
Remove failed: remove_hidden_unit failed: remove_hidden_unit_manual requires INVESTIGATING state (currently STOPPED)
```

So the editor is **not** gated for no reason: manual structural edits have a real backend precondition,
and canopy's gate is a faithful mirror of it that happens to read the wrong key. Segment 6 saw only the
two `PATCH` mutations land — and `PATCH` is genuinely permitted in `STOPPED`, which is why the gate looked
gratuitous from that evidence alone.

The practical consequence for the fix: **do not remove the gate**, correct it
(`state_machine.status` → `fsm_status`). And the corrected gate does work — with the FSM actually at
`INVESTIGATING`, the same two ops succeeded end-to-end (`hidden_units` 10 → 9 → 10, tail unit carrying the
sent 11-weight vector, `bias 0.25`, `activation Sigmoid`, all read back from cascor).

### F-CANOPY-013 is no longer latent — it is observed on successful operations

Both success messages were captured on ops that **fully succeeded** at the backend:

```text
Snapshot taken; Removed unit 9 (now None hidden units).      [alert-success]
Appended unit at index None (now None hidden units).         [alert-success]
```

`_post_json` (`:458`) returns the whole `{status, data, meta}` envelope as `result["data"]`, so `:609-610`
and the remove callback read `unit_index` / `num_hidden_units` off the **envelope root** and get `None`.
The patch path is *spared* — its messages count request-side values via `len(values)` — which usefully
bounds the fix to callbacks that read a response.

### F-CANOPY-012 confirmed and sharpened — a naive reshape would still be wrong

```text
Patch failed: patch_weights failed: shape mismatch: output_weights expects (12, 2), got (24,)
```

The panel sends flat `(24,)`; cascor wants 2-D. But the required shape is
`(n_in + n_hidden, n_out) = (12, 2)` — **not** `(n_out, n_in + n_hidden) = (2, 12)` — while the field's own
placeholder instructs the user to type "CSV **row-major**". A reshape that trusts the placeholder would
produce a transposed weight matrix that *passes* the shape check and silently corrupts the network. The
fix must reshape to `(12, 2)` and the placeholder must be corrected in the same change.

### F-CASCOR-002 UPGRADE — the loss is physical, self-propagating, and reproducible on demand

Segment 6 proved the `TypeError` and the swallowed WARNING. Segment 7 found what that costs on disk.
Re-snapshotting a network that was itself restored from a snapshot yields an artifact with the optimizer
group **entirely absent** — verified with `util/ad-hoc/e2e_snapshot_h5_compare.py` (added this segment):

| snapshot | provenance | nodes | optimizer nodes |
|---|---|---|---|
| `snapshot_20260811T010849Z.h5` (296,701 B) | original training | 191 | **2** — `params/output_layer/optimizer[/state_dict]` |
| `snapshot_20260813T043121Z.h5` (285,187 B) | taken after an earlier restore | 185 | **0 — ABSENT** |
| `snapshot_20260813T043711Z.h5` (295,308 B) | taken after a *fresh* restore | 189 | **0 — ABSENT** |

The third row is a deliberate control: an independent restore→save cycle, run minutes after the second,
reproducing the loss exactly. And the smoking gun sits in the pristine file where the finding said it
would:

```text
params/output_layer/optimizer.attrs['learning_rate'] = np.bytes_(b'0.1')   (python type bytes_)
config.attrs['learning_rate']                        = np.float64(0.1)     (python type float64)
```

— the same attribute written as a **string** in one place and a float in the other, which is precisely the
`np.bytes_` that trips torch's range check at `:1037`.

This warrants a **severity upgrade, P2 → P1**. The original finding describes a load-time warning; what is
actually happening is that one restore→save cycle **permanently destroys the optimizer state in the
artifact lineage**. A consumer of the second-generation snapshot cannot even encounter the bug — there is
nothing left to fail on — so training resumed from it silently restarts the optimizer from scratch, with
no warning at all. The failure is loudest at its least harmful moment and silent thereafter.

### Row-by-row results (all 18)

`M-NETWORK-EDITOR-05` was already recorded in segment 6 (D-0 re-confirmed); the other 17 are new.
Full per-row detail is in `reports/e2e/20260811T010700Z/statuses.tsv` — the summary:

| verdict | rows |
|---|---|
| **PASS** | 01, 02, 05, 06, 07, 08, 10, 12, 14, 15, 16, 18 |
| **PASS**, reachable only by injection | 11 |
| **PASS** on path/effect, **FAIL** on status message (F-CANOPY-013) | 09, 13 |
| **PASS** on 2 of 4 targets, **FAIL** on the default (F-CANOPY-012) | 17 |
| **FAIL** (F-CANOPY-011) | 03, 04 |

Three rows earned more than a bare verdict:

- **M-NETWORK-EDITOR-01** — `dcc.Interval` renders **no DOM node**, and canopy's log is application-level
  with no access lines, so neither the usual DOM nor log oracle applies. Verified instead by instrumenting
  `window.fetch` and timing the Dash callback POSTs carrying the `fsm-poll` input: **6 fires in 11 s,
  median inter-arrival 1957 ms** against the 2000 ms nominal. The 1045–3025 ms spread is congestion, not
  drift — the same window carried **140** other Dash callbacks, which is the hardest number this arc has
  yet put on F-CANOPY-004.
- **M-NETWORK-EDITOR-11** — the validation arm needs no trickery and is the more useful evidence: clicking
  Delete with an empty index returns `Pick a unit to delete.` and correctly does **not** open the modal,
  proving the callback is wired and fires from a `display:none` control. Reaching the modal itself
  required injecting the `<option value="9">` that D-0 prevents from ever existing.
- **M-NETWORK-EDITOR-13** — the `STOPPED` arm proves the *ordering* independently of the outcome: the
  snapshot-first `POST` succeeded (count 1 → 2) and only then was the `DELETE` refused. Had the order been
  reversed or the snapshot skipped, the counts could not look like that.

### Observations (segment 7, non-finding)

- **The snapshot-first pre-step is not transactional.** A refused `DELETE` leaves its safety snapshot
  behind (count 1 → 2 with the network untouched at 10 units). Defensible — a pre-op snapshot is a safety
  artifact and keeping it costs only disk — but undocumented, and repeated failed attempts accumulate
  orphans.
- **The T-7 numeric wall is narrower than recorded.** `-add-bias` and `-patch-idx` are both
  `type="number"`, yet both were driven successfully with a native-setter + `input`/`change` gesture, and
  the values reached cascor (`bias 0.25` on the appended unit; `[0.11, 0.22]` on unit 0). T-7 is a
  Playwright `fill()` limitation, **not** a DOM one — so `AUTO` via raw JS is sufficient where the matrix
  currently prescribes `AUTO-API`.
- **The remove picker has two independent reasons to stay empty**, so fixing either alone is insufficient:
  the gate returns before the topology fetch is ever reached (`:505`), *and* that fetch targets the 404
  route `/api/network/topology` (D-0).

### The Replay tab, 17/17

A replay session was started **through the UI** (Snapshots → `▶️ Replay` → Confirm) on the pristine
`snapshot_20260811T010849Z`. That detail matters: a session started by direct API call does **not** light
the panel up, because `replay-player-session` is written by the *snapshots* panel after its own POST — the
player is store-driven, not backend-polled. The panel went active 4643 ms after Confirm and the tab
**auto-switched to Replay**, corroborating segment 6.

**The whole transport surface is dead, and now provably all of it.** Segment 6 established
action-independence from play + stop. This segment drove all six controls:

| control | driven how | dispatched? | result |
|---|---|---|---|
| `-play-btn` / `-pause-btn` / `-stop-btn` | `.click()` | yes | **byte-identical** `No scheme supplied` |
| `-scrubber` | trusted `ArrowRight` | 2 callbacks | same error; handle 6 → 7 |
| `-speed` | trusted `ArrowRight` | 2 callbacks | same error; handle 5.0 → 5.1 |
| `-range` | trusted `ArrowRight` | 2 callbacks | same error; handles → `[3, 12]` |

The error text carries its own diagnosis — `Perhaps you meant **https:///**/api/v1/…` — three slashes,
the empty base URL concatenated straight onto the path. The sliders' readouts (`0 / 12`, `1×`, `[0, 12]`)
correctly do **not** advance, because they re-render only from a *successful* control response; that is
right behaviour downstream of a dead request, not a second defect.

The backend was exonerated once more en passant: a direct `POST {"action":"stop"}` to the same route
returned `200` with `fsm_state: STOPPED`.

**F-CANOPY-015 measured against the payload.** `POST /replay` returns, nested at `data.session`:

```json
{"length": 12, "time_index": 0, "speed": 1.0, "paused": true,
 "range": {"start": 0, "end": 12}, "weights_available": true,
 "weight_sampling": {"strategy": "adaptive", "num_samples": 3, "sample_epochs": [10000, 10, 11]}}
```

`weights_available` is **true** — this is provably a V2 snapshot — and the badge nonetheless renders
**`V1 (metrics only)`** in grey. The two masked siblings behave exactly as the finding predicted: `speed`
`1.0` equals `SPEED_DEFAULT`, and `range` renders `[0, 12]` because the fallback `[start, end]` from
`_session_window` coincides with the real window.

That second one hides a trap worth stating plainly, because it is the same shape as the F-CANOPY-012
transpose: the backend's `range` is a **dict** `{start, end}`, while the render does
`f"[{range_value[0]}, {range_value[1]}]"`. **Reading one level deeper without converting dict → list turns
a silently-wrong readout into a `KeyError`.** The obvious one-line fix crashes the panel.

One more stale line in the matrix: row 05 says the badge "ships `display:none`", but the callback's
`badge_style` sets `display:inline-block`, so it is *shown* — shown and wrong, which is worse than hidden.

**What still works.** `-status` faithfully rendered the error for all six attempts (it is doing its job —
what it reports is F-CANOPY-014). The weight-drain plumbing is intact: `window._juniperWsDrain` exposes
`_replayWeightBuffer` beside its six sibling channel buffers and `drainReplayWeights()` returns
`array(0)` — idle, not broken, which is precisely the distinction worth drawing when the observable
payoff is blocked upstream. The swap-events graph renders its empty state correctly, and
`GET /api/snapshots/{id}/history/dataset_swaps` returns `200` with `{"events": []}` — a live route, not
another D-0. Graph, count (`0 events`) and backend all agree, so the count is genuinely wired.

| verdict | rows |
|---|---|
| **PASS** | 01, 02, 03, 04, 06, 13, 14, 15, 16, 17 |
| **FAIL** (F-CANOPY-014) | 07, 08, 09, 10, 11, 12 |
| **FAIL** (F-CANOPY-015) | 05 |

### Methodology corrections (segment 7)

Two of my own instrument errors, recorded because each cost real time and each would recur:

- **`offsetParent` is `null` for `position:fixed` elements — so it is not a visibility test for modals.**
  Two replay-start attempts were scored as "modal never opened (20 s)" and provisionally blamed on
  F-CANOPY-004 congestion. Both were wrong: the modal *was* opening and my filter could not see it. Use
  `getComputedStyle` + `getBoundingClientRect().width/height > 0`. This sits directly beside segment 6's
  note that the modal DOM does not exist while closed — together they say: poll for the element to
  appear, then test visibility by geometry.
- **A Dash slider commits only on a TRUSTED event.** Setting the paired `<input type="number">` via the
  React native-setter moves the visual handle but produces **zero** callback dispatches and no readout
  change; so does a full synthetic `pointerdown`/`pointermove`/`pointerup` sequence. A real
  `page.keyboard.press('ArrowRight')` on the focused thumb dispatches immediately. Under
  `updatemode="mouseup"`, a moved handle is **not** evidence that a value committed — the two must be
  checked separately, or a dead control looks driven.
- **Do not blame congestion before excluding the instrument.** Both corrections above initially presented
  as F-CANOPY-004. Congestion is real and measured (140 callbacks / 11 s), which makes it an attractive
  and therefore dangerous default explanation.

### A first-load overlay stands between a fresh page and every gesture

After any reload the **welcome modal** (`welcome-modal`, matrix §2.1) is open over the dashboard and must
be dismissed via `#welcome-modal-close` before driving anything. Sessions that keep one long-lived page
never see it, so it is easy to omit from a recipe and then lose time to it after the first reload.

### W11 — in-metrics replay: first pass (SUPERSEDED below by the training run)

> The verdicts in this subsection were recorded **before** the owner-approved training run. They are kept
> because they document what was and was not distinguishable without history — but the recorded row
> statuses have since been **revised** by "W11 re-driven with real history" below. Nine rows moved from
> BLOCKED to **FAIL**.

W11's stated precondition is "training **stopped** with accumulated history". The second half is not met
in this run: `GET /api/metrics/history?count=100` returns `history: []`, and `monitor.total_metrics` is
`0` — no training has run in this cascor process since the `09:44:52` start. Two rows are still
answerable, and one of the two is a matrix-precision correction worth having.

**W11-01 passes through a branch the row does not describe.** The controls are visible — but
`toggle_replay_visibility` (`metrics_panel.py:946-947`) returns `display:block` *unconditionally* when the
training-state store is falsy, and only then falls through to the
`status ∈ [STOPPED, PAUSED, COMPLETED, FAILED]` test the row names. The store is empty here, so the
status branch was never evaluated. This matters because canopy's `/api/status` currently reports
`fsm_status: REPLAYING`, which is **not** in that set — anyone checking the row against live status would
record a divergence that is not real.

**W11-02 passes in its degenerate form.** The readout is `0 / 0`. The row's `N = history length − 1` holds
for non-empty history; `update_replay_ui` (`:1082`) is `len(metrics_data) - 1 if metrics_data else 0`, so
empty history clamps `N` to `0`, not `−1`.

**D-3 is confirmed at the cited site**, which is W11-05's real payload: `metrics_panel.py:1034` reads
`base_interval = 1000`, and `:1035` divides by speed — so 1x = 1000 ms, 2x = 500 ms, 4x = 250 ms. The
documented divergence (base is 1000 ms, **not** 500 ms) holds exactly, and step 4's expected 250 ms at 4x
follows.

**The remaining nine rows were driven anyway, and the results are artifacts rather than verdicts** — which
is the point of recording them explicitly. With `max_index = 0`, `replay_tick` (`:1053-1060`) computes
`new_index 1 > end_index 0` and sets `mode = "stopped"` on the *first* tick, so:

- the play icon never durably shows ⏸ (there is no empty-history guard on the play branch — `:1010-1011`
  flips `mode` unconditionally — the state is simply overtaken by its own auto-stop);
- both step buttons pin to 0 through their own clamps (`max(0, i-1)` / `min(max_index, i+1)`);
- both jumps are no-ops because `start_index` and `end_index` coincide at 0;
- the slider is explicitly short-circuited (`:1031` computes the index only `if max_index > 0`).

None of that distinguishes a correct control from a dead one, so none of it is reported as a defect.

**Unblocking W11 needs a decision, not just more driving.** It requires a short cascor training run to
accumulate metrics history — that is W1 — which is a live state change: it would overwrite the
deliberately mutated network built by W5-12/13/15 and this segment's editor rows, and the standing
guidance is not to disturb a live cascor training state casually. Flagged for the owner rather than taken
unilaterally.

### W11 re-driven with real history — and the lane is a defect, not a precondition gap

The owner approved the training run. An insurance snapshot of the mutated network was taken first
(`snapshot_20260813T051936Z`), then:

1. `Start` alone → **`409: Training cannot be started: Training data not provided`**.
2. `Apply Dataset` staged canopy's pending config (spirals, 1000 samples, noise 0.25) and raised the §2.9
   pending-dataset banner. The banner's `Stop & Restart with new dataset` did **not** start a run.
3. Staging directly on cascor — `POST /v1/training/dataset` with
   `{"dataset_type":"spirals","params":{…}}` → `staged` — then `Start` → training **ran**
   (`STARTED / OUTPUT`, `is_training: true`, 10 hidden units retained).
4. Stopped after ~35 s with **401 metrics** accumulated.

**W11-11 PASS**, proven properly: with training running the controls went `display:none`. That also
exercises the *status* branch of `toggle_replay_visibility` that the first pass could not reach — so both
arms of that gate are now covered, and W11-01 is upgraded accordingly.

**Everything else in the lane FAILED — and the training run is what made that provable.** With 401 rows
of history:

- `#metrics-panel-replay-position` still reads **`0 / 0`**;
- play, step-forward/back, and both jumps do nothing;
- and the slider never moves.

The first pass could not tell this apart from correct behaviour at `max_index = 0`. With a real window
(`max_index = 400`) the clamps, the coincident start/end, and the short-circuited slider math are all out
of the picture, and the controls are simply dead.

**F-CANOPY-016 (new, P1) — the in-metrics replay control cluster never dispatches.** The evidence is on
the wire, not inferred:

| probe | result |
|---|---|
| store genuinely populated? | **yes** — the sibling loss chart, reading the *same* `metrics-panel-metrics-store` Input, renders a trace of **401 points** |
| `update_replay_ui` requested when that store changed? | **zero** requests in 20 s |
| `metrics-panel-replay-state` requested on a play / step click? | **zero** requests in 15 s |
| instrument working? | **yes** — the same hook caught 3 unrelated `replay-player-panel` dispatches in that window, and 15 `metrics-panel-metrics-store` polls in another |

So the callback is registered (it rendered `0 / 0` at mount under `prevent_initial_call=False`) and then
never fires again, while the button callbacks never fire at all. The readout is frozen at its mount value
forever. **Root cause is not isolated** — registered-but-never-re-triggered is a Dash-graph symptom, not a
diagnosis — and that isolation belongs to the fix phase. What is established is the observable: the entire
W11 surface is inert in the live lane regardless of history.

Two smaller things worth carrying:

- **The metrics store is throttled, not starved.** In `full` mode only **1 poll in 15** returns data — the
  `FULL_HISTORY_POLL_TICK_MODULUS` throttle — the other 14 return `{"multi":true,"response":{}}`
  (`dash.no_update`). A short observation window will look like a dead store when it is merely slow.
- **F-CANOPY-002 confirmed from the client side.** `window._juniperWsDrain` shows
  **`_lastMetricsFrameMs: 0`** — *no metrics frame has ever arrived* — with `_metricsBuffer` empty and
  `_metricsReceived: false`, while `_lastStateFrameMs` carries a real timestamp and
  `_connectionStatus` is `{connected: true, mode: "live"}`. The socket is up and sibling channels deliver;
  the metrics channel specifically is dead. That is exactly the clobbered-handler signature, now visible
  in the client's own state rather than only in the source.

**Do not read the replay slider's `aria-valuemax` as a data signal**: `update_replay_ui` returns a
hardcoded `100` for that output (`metrics_panel.py:1084` — `return slider_value, 100, position_text`),
because the slider is a percentage scale. It reads `100` whether history is 0 rows or 401.

---

## Phase 1 — segment 9 (2026-08-14): the W6 owner gate, driven

Segment 9 opened from `main` (the segment-8 evidence PR #1100 having landed) with the browser MCP
**available for the first time in the arc** — `mcp__playwright__*` tools entered the session index, so the
`util/ad-hoc/` script drivers were not needed. Both legs were version-checked before anything was believed:
canopy was restarted onto `d11bfcd` (it had been running Aug-10 code, i.e. pre-#489), and the cascor leg was
left alone but recorded as pinning `#513` — see the F-CASCOR-003b row for why that matters.

### The headline: W6-16..20 driven, and F-CANOPY-019's open question is settled

The owner gate the last three segments deferred is now driven, and it answered the question it was blocking:
**the STAGED dataset wins at restart, while the modal describes the SIDEBAR.**

The reproduction was built as a single-variable discriminator, because the segment-8 setup (staged *moons*
vs summary *spirals*) varied the generator, sample count and noise at once:

1. Staged `spirals / 200 / 0.1` through `#apply-dataset-button` — canopy logged
   `Dataset staged: {nn_dataset_elements: 200, nn_dataset_noise: 0.1}` and `/api/status.pending_dataset`
   carried `n_samples 200, noise 0.1`.
2. Set the sidebar **back** to `1000 / 0.25` *without* applying. Re-checked `pending_dataset`: still 200/0.1.
   Sidebar and staged now differ in exactly two numbers.
3. Opened the modal. `#restart-confirm-summary` read **`Samples: 1000 | Noise: 0.25`** — the sidebar values.
   The granular fields agreed with the summary (`#restart-ds-samples` `1000`, `#restart-ds-noise` `0.25`), so
   the misdescription is not confined to the summary text.
4. Confirmed. juniper-data then generated `spiral-1.0.0-6514b5ab7f063c31` —
   `n_points_per_spiral 100, noise 0.1` → **`n_samples 200`**, `n_train 160`, `n_test 40` — distinct from the
   pre-restart `spiral-1.0.0-1aacda4c47242992` (`n_points_per_spiral 500, noise 0.25` → `n_samples 1000`).

So the user reads *"Samples: 1000, Noise: 0.25"*, confirms, and gets 200/0.1. That moves F-CANOPY-019 from
"the summary is cosmetically wrong" to **the confirmation dialog misdescribes the action it then performs** —
the one thing a confirm dialog exists to get right.

**A second-order consequence falls out of the code and is worth driving next.** `_execute_restart_handler`
Phase 1 re-stages only when `_restart_dataset_changed(dataset_vals, baseline.dataset)` is true — and *both*
sides of that comparison are seeded from the sidebar. Touching **any** granular dataset field should
therefore flip the outcome: it would re-stage the sidebar values over the staged ones and silently discard
the pending change. The dialog's effect would then depend on whether the user opened the
"Verify / modify what will happen" section at all. Not yet driven; recorded as the next W6 target.

### Two worries the handoff carried, both disproven

- **Confirming would NOT have wiped the network.** `dashboard_manager.py:5453` does hard-code
  `payload = {"start_fresh": bool(start_fresh), "reset": True}` (line `:5453` on `d11bfcd`, not `:5447`), but
  with `start_fresh` OFF the network **survived**: `hidden_units` stayed `1` across the restart and
  `current_epoch` reset `1 → 0`. The hard-coded `reset` resets training counters, not the model. The gate was
  guarding less than it appeared to, and the outcome alert's claim to have "continued the current model" is
  substantively **true**.
- **The outcome alert is truthful — but ungrammatical.** It rendered
  `Restart succeeded. Restart complete. Started continued the current model.` `:5504` appends
  `"a fresh model."` / `"continued the current model."` onto a prefix already ending in `Started`. Cosmetic,
  but this is the surface the plan requires to read truthfully, and *"Started continued"* invites a misread.

### A finding that wasn't: checking the ledger before filing

A live, reproducible observation — a dashboard loaded **while training is already running** shows
`Stopped / Idle / 0 hidden units` with `#latency-display` **empty**, and never recovers — was drafted as a new
P1 and then **withdrawn as a duplicate**. F-CANOPY-006 (P0, OPEN) already establishes that the topology
counters "never update from any source", and segment 4 recorded the same 0/0/0-vs-correct-`/api/topology`
reading as corroboration; F-CANOPY-004 (P0/P1, OPEN) already records a starved server-side callback leaving an
"alert element still empty 6+ min later". The observation is those two findings' blast radius.

What it does add, kept on the `F-CANOPY-020` row: the affected surface is the **top status bar itself** — the
dashboard's primary readout, written as one group by `update_unified_status_bar` (`:3087-3104`) on the same
1 s `fast-update-interval` that F-CANOPY-006 already fingers as the supersession driver; the failure is
**permanent**, not the documented 30 s–minutes lag; `#latency-display` rendering *empty* rather than stale is a
clean discriminator between "never produced a value" and "produced a late one"; and it correlates with **when
the page was loaded** — the only page in the session with a live status bar was loaded *before* training
started and tracked correctly throughout, including candidate progress `400/400`.

Ruled out along the way, so a fixer need not re-run them: interval throttling
(`visibilityState: 'visible'`, `hasFocus: true`), a dead callback loop (**62** `_dash-update-component` POSTs
in a 12 s window, all 200), JS errors (none), server-side errors (none), and init/localStorage state (broken
with the welcomed key both set and cleared, in a fresh tab, and after a full canopy restart).

### Methodology notes (segment 9)

- **Playwright's post-click ack times out on this page, but the click lands.** `locator.click()` — even with
  `force: true` — exceeds the tool's budget after "done scrolling", while the element is provably stable
  (identical rect across 6 samples), topmost at its centre, and `pointerEvents: auto`. `page.mouse.click(x, y)`
  fired without awaiting completion **does** reach the app: the console recorded
  `[Phase D] WS command success: stop <uuid>` and the backend transitioned. **Verify clicks by effect, never
  by the tool's return.** Compute the target's coordinates and dispatch immediately — a layout shift between
  computing and clicking silently misses.
- **Focus via JS, type with real keys.** The working input technique for the numeric wall is
  `element.focus()` through `page.evaluate`, then `Control+A` / `Delete` / `keyboard.type()`. The keystrokes are
  genuinely trusted; only the focusing is scripted. Both `#nn-dataset-elements-input` (`step=1`) and
  `#nn-dataset-noise-input` (`step="any"`) committed typed values cleanly on post-#489 canopy.
- **`performance.getEntriesByType('resource')` caps at 250 entries.** A full buffer reads *exactly* like zero
  traffic and produced an interim "the callback loop is dead" conclusion that was wrong. Call
  `performance.clearResourceTimings()` and `setResourceTimingBufferSize()` before counting anything.
- **Read a panel's counters only with its own tab active.** Panels are hidden, not unmounted, so a
  never-hydrated hidden panel returns `0` and is indistinguishable from a real failure. A first W6-19 reading
  was taken from the Topology panel while Dataset View was active, and was discarded.
- **`#welcome-modal` IS the `.modal-dialog`**, not a wrapper around one. `#welcome-modal .modal-dialog`
  returns null and reads exactly like a closed modal.
- **Scope `[role=option]` by the trigger's `aria-controls`.** A global query returned six options belonging to
  *other* open dropdowns. Radix selects also drive reliably by keyboard (focus → `Enter` → arrows) when an
  option click does not take; note `ArrowDown` + typeahead is not the same as an exact-name click.
- **`window.cascorControlWS` is not the socket handle** — the bridge registers on `window.cascorWS`, so probing
  `cascorControlWS.readyState` reports a false "socket unavailable" and invites the wrong transport conclusion.
- **Settle before judging, again.** The W6-14 summary re-render was read at 2.5 s and looked like a wall; it had
  updated by the next 1.5 s sample. Sample repeatedly and only call a wall when the value is stable across
  several reads.

### Row results (segment 9)

`reports/e2e/20260811T010700Z/statuses.tsv` — **119 rows** (112 → 119).

| row | verdict |
|---|---|
| W6-16 | **PASS** — progress alert ≈1.8 s, orchestration ran, `reset: True` confirmed at `:5453` |
| W6-17 | **PASS(truthful) / FAIL(message composition)** — "Started continued the current model." |
| W6-18 | **PASS** — banner trio unmounts once `pending_dataset` clears |
| W6-19 | **FAIL(display only — F-CANOPY-006)**; the 2-feature width itself is correct at the API |
| W6-20 | **FAIL(display only — F-CANOPY-004 class)**; the staged dataset demonstrably *did* apply |
| C2.1-03 / C2.1-04 / C2.4-03 | **PASS** — re-confirmed on this run (first recorded on run `20260810T002233Z`) |
| C2.2-02 | **PASS** — active tab restored from `layout-state-store` across reload |
| C2.5-TRANSPORT | **PASS** — FE-1 confirmed: clicks travel as `/ws/control` frames, **zero** `/api/train/*` browser POSTs |
| F-CANOPY-019 | **RESOLVED open question** — staged wins, modal describes the sidebar |
| F-CANOPY-020 | **withdrawn as new** — blast radius of F-CANOPY-004 + F-CANOPY-006 |
| F-CASCOR-003b | **OPEN QUESTION** — pool retention observed, but not attributable to current cascor main |

### The cascor worker pool: an observation held back on purpose

Starting training from a cold network spawned a forkserver (pid `1503392`, ppid `2830469` — ancestry walked to
**this arc's** cascor child, not the other session's port-8230 stack) plus **15 children at 116 MiB each**
(~1740 MiB). After a clean UI stop with `fsm_status` confirmed `STOPPED`, all 16 were **still resident** at
+8 s and again at +90 s. That is the F-CASCOR-003 signature.

It is **not** recorded as a defect against current cascor main, because this leg pins older code: the
supervised child booted `2026-08-14 03:52:46`, while cascor **#514 — "thread candidate patience and
convergence to the pool"** merged at `04:57:03` and **#516** at `15:37:23`, both *after*. The leg carries
`#511/#512/#513` only, and #514 touches the candidate-pool path by name. To settle it: restart the cascor leg
onto `fadfe80` and repeat start → stop → observe. This is the same trap the segment-8 handoff flagged after it
nearly cost a duplicate PR — a long-lived supervised leg silently pins its boot-time code, so `ps -o lstart`
against `git log` is a precondition for attributing *any* observed behaviour.

---

## Phase 1 — segment 10 (2026-08-14): the second F-CANOPY-019 arm, and the matrix finally gets filled

Segment 10 opened from `main` with the segment-9 evidence PR (#1106) merged. TSV **120 → 145 rows**, and the
matrix status column went from **completely empty** to **66 rows filled** — the bulk-fill had been deferred
in every segment since 4.

### The headline: F-CANOPY-019 is now fully characterized, and it is worse than a wrong label

Segment 9 proved the modal describes the SIDEBAR while the STAGED dataset is what gets applied. Segment 10
drove the other branch — the one the code predicted but nobody had run.

Setup was identical to segment 9 (staged `spirals/200/0.1`, sidebar set back to `1000/0.25` without applying,
`pending_dataset` re-verified at 200/0.1, modal summary reading "Samples: 1000"). The single difference: before
confirming, **one granular field was edited** — `#restart-ds-rotations` 1.5 → 2.5, an axis unrelated to the
staged difference.

Result: juniper-data generated `spiral-1.0.0-a697da0a6182be0c` with **`n_samples 1000`, `noise 0.25`,
`n_rotations 2.5`** — the sidebar values plus the edit. The staged 200/0.1 was **silently discarded**.

So the same dialog, from the same visible state, produces opposite outcomes:

| user action | modal says | backend applies | staged intent |
|---|---|---|---|
| does not touch the granular section | Samples 1000 | **200** (staged) | preserved; dialog misdescribed it |
| edits **any** granular field | Samples 1000 | **1000** (sidebar + edit) | **silently discarded** |

The mechanism is exactly the code read: `_execute_restart_handler` Phase 1 re-stages when
`_restart_dataset_changed(dataset_vals, baseline.dataset)` differs, and **both sides are seeded from the
sidebar**, so any edit makes the comparison true. The destructive direction — losing a deliberately staged
dataset — is the one triggered by the user being *more* careful and opening "Verify / modify what will happen".

In fairness: arm B is not wholly silent. The outcome alert does say *"Re-staged dataset to spirals (1000
samples)."* But that is post-hoc, after the restart has run, and it auto-dismisses in ~8 s. Nothing before the
click warns that the staged change is about to be dropped. **Upgraded P2 → P1.**

### F-CANOPY-005's trigger is broader than the timeout race

Clicking Pause on a non-running backend produced this console sequence:

```
[WARNING] [Phase D] REST fallback (pause): WS rejected: Training cannot be paused in the current state
[ERROR]   Failed to load resource: 409 (Conflict) @ /api/train/pause
[WARNING] [Phase D] REST /api/train/pause returned 409
```

Read the first line carefully: the WS did **not** time out and did **not** fail at the transport level. It
returned a well-formed rejection carrying a legitimate *business* error from the backend. The client then
treated that considered refusal as grounds to re-issue the identical command over HTTP.

That matches the shipped contract as the matrix states it ("the REST fetch fires only if the WS send is
unavailable/**rejected**"), so it is by design — but it means a rejection the backend has already adjudicated
gets retried on a second transport, and the client cannot distinguish *"the socket failed, retry"* from
*"the server considered this and said no."* Harmless for pause-on-stopped (409 both times); the exposure is any
command whose WS rejection is transient or partially applied. The fix direction is to fire the fallback only on
transport-level failure, never on a received error ack.

**F-CANOPY-003 also reproduced** on `d11bfcd`: after the rejected pause and a rapid reset pair, `#pause-button`
and `#reset-button` were both still `disabled` across 10 samples spanning ~12 s, with no ack and no sweep
clearing them.

### A correction to segment 9's wording

Segment 9 recorded the dead status bar as **permanent**. Segment 10 shows that was over-stated. Loaded while
the backend is **at rest**, the bar does hydrate — it sat at its initial `Stopped`/`Idle`/`0`/`""` values for
~19 s and then came fully good at ~21 s (`Completed — early stopped` / `Output Training` / Step 14 /
`11 / 10` / `Latency: 6ms`, every field matching `/api/status`). Loaded **during** a live run it never
hydrates, which is precisely F-CANOPY-004's documented scope. The corrected statement: **starved when the page
is loaded mid-run, merely slow (~20 s) when loaded at rest.**

### Two documented divergences confirmed, one new observability gap

- **D-1 confirmed** (doc-only): there are THREE writers of `visualization-tabs.active_tab` —
  `dashboard_manager.py:3283`, `:3305`, and `hdf5_snapshots_panel.py:1230` — while `_visible_tabs`' docstring
  at `:2264-2266` states the dashboard "keeps exactly two". Runtime behaviour is fine; the comment is stale.
- **D-5 confirmed** (doc-only): the comment at `:4128-4129` says "When the flag is off (default)…" while
  `settings.py:349` declares `enable_ws_control_buttons: bool = True`. Note the guard reads
  `getattr(..., False)` — that `False` is a missing-attribute fallback, not the product default, and is easy
  to misread as corroborating the comment.
- **NEW — the matrix's own transport oracle is unavailable.** §2.5 instructs "Record the active transport in
  the run header (startup log line at `:4149`)". That line does not exist in the canopy log: **zero**
  occurrences of `Phase D` across the whole 119 MB file, and zero for the else-branch equivalent, while other
  `frontend.dashboard_manager` INFO records are present. It is emitted during app construction, before logging
  is configured. The transport had to be established behaviourally instead — WS frames plus zero
  `/api/train/*` requests.

### An anomaly parked rather than filed

`/api/status` reported **`hidden_units: 11` against `max_hidden_units: 10`** — the network holds eleven units
against a declared cap of ten. It reached 10/10 before the segment-10 restart and 11 after, so the extra unit
arrived across a restart carrying the hard-coded `reset: True` with start-fresh OFF. Recorded as an
observation on C2.3-05, not a finding: cascor's cap semantics are not established here (`max_hidden_units` may
bound grow *iterations* rather than total units). Reproduce deliberately before filing.

### Row results (segment 10)

`reports/e2e/20260811T010700Z/statuses.tsv` — **145 rows**; matrix status column **66 filled**.

| group | result |
|---|---|
| §2.1 header/theme/welcome | **4/4** — C2.1-01/02 driven; F-CANOPY-001 (glyph desync) re-confirmed live on `d11bfcd`, still OPEN |
| §2.2 tab bar | **6/6** — incl. D-1 confirmed; all 15 tabs enumerated |
| §2.3 top status bar | **8/8** — all asserted against the `/api/status` oracle |
| §2.5 training controls | **8/10** — C2.5-04 (resume) and C2.5-07 (non-default REST posture) not driven; C2.5-08 recorded INCONCLUSIVE on purpose |
| W6 | W6-14 upgraded to both halves; new W6-16b (second execution, granular-edit path) |

**C2.5-08 is deliberately INCONCLUSIVE.** Two clicks 120 ms apart produced one command effect — the contract's
outcome — but the mechanism is not separable here: the first click optimistically disables the button, so the
second lands on a disabled control regardless of any debounce, and neither click logged a WS frame. Scoring it
PASS would credit the 500 ms guard for something the disable alone explains.

### Methodology notes (segment 10)

- **`scrollIntoView` does not apply before a `getBoundingClientRect` in the same `page.evaluate`.** A stop
  click was dispatched at `y = -1515` — far off-viewport — because the rect was read in the same call that
  requested the scroll. Scroll, wait, then read the rect in a **separate** evaluate, and reject any box with
  `y < 0` or `height == 0` before clicking.
- **Read the id list from source, never from a DOM prefix.** A `[id^="sidebar-"]` query returns 20 elements;
  `SIDEBAR_SECTION_IDS` (`dashboard_manager.py:267-282`) is exactly 14. Scoring against the superset makes a
  correctly all-hidden tab look like a failure — it nearly produced a false FAIL on C2.2-05.
- **Match tab labels exactly**: an attempt on "Evolution" found nothing because the tab is "Network Evolution",
  which reads as an unclickable control if the selector result is not checked.
- **Hooking `console.log` alone misses the interesting lines.** The Phase-D fallback path logs at `warn` and
  `error`, so a `console.log`-only capture returned empty while the real evidence sat in the console file.
- **The T-22 numeric wall is obsolete for the restart modal's dataset fields.** `#restart-ds-rotations` was
  driven with real keystrokes (JS `focus()` then `Control+A`/`Delete`/`type`/`Tab`); the granular fields now
  carry the post-#489 step pattern (`step="any"` for floats, `step="1"` for ints). The six `#restart-p-*` param
  fields are the same widget class but were not exercised — re-check them before deleting the T-22 note.

---

## Phase 1 — segment 11 (2026-08-15): every recorded verdict consolidated into the matrix

Segment 11 drove **nothing live** — the isolated trio (data 8101 / cascor 8202 / canopy 8051) was down and a
fresh stack would have opened a new run-id for no new evidence. It is a consolidation segment: the arc has been
accumulating verdicts in **three** separate run records since 2026-08-09, and only the newest of them had ever
been mapped back into the matrix.

Matrix status column: **66 → 140 of 298 rows (47%)**. Nothing was re-driven and no verdict was invented; every
cell traces to a record already committed in `reports/e2e/`.

### The three verdict sources, and who wins

| source | run | contributed |
|---|---|---|
| `reports/e2e/20260811T010700Z/statuses.tsv` | segments 9-10 | the 66 already-filled cells (unchanged) |
| `reports/e2e/20260810T002233Z/statuses.tsv` | segments 4-8 | the bulk of the new fills |
| `reports/e2e/20260809T223851Z/rowlog.md`    | the superseded first LIVE run | the §2.1-2.4 chrome baseline |

Precedence is **newest-first**: a later re-drive of a row always beats an earlier record, and `--overwrite` was
not used, so the segment-10 cells are byte-identical to what #1113 merged. Re-running the fill now reports
`filled: 0` — it is idempotent.

### A silent mis-fill in the segment-10 tool, found and repaired

`util/ad-hoc/e2e_matrix_fill.py` split table rows on **every** `|`. Markdown escapes a literal pipe inside a
cell as `\|`, which adds a phantom cell and shifts every index past it by one. Exactly one matrix row contains
such an escape — **C2.2-04** (`display:block\|none`) — and it was in segment 10's fill set, so its `PASS` was
written into the **FA** column while the status cell stayed `—`. The row read as fragile-area-tagged and
unverified; both halves were wrong.

Fixed three ways: the splitter now splits on unescaped pipes only, the row is repaired (FA back to `—`, status
`PASS`), and the tool refuses to write any line whose **cell count** changes — the structural invariant that
makes this class of error impossible to reintroduce silently rather than merely unlikely.

### Three honesty rules the consolidation had to encode

- **`pending` is not a verdict.** The rowlog records in-progress bookkeeping in the same column as outcomes
  (`pending demo lane`, `pending W14`). Four ids — C2.4-02, C2.4-05, M-TUTORIAL-04, M-WORKERS-02 — are
  deliberately **left empty** rather than filled with a non-terminal value a reader would take as an outcome.
  (C2.4-04 shared the `C2.4-04/05 pending` token but carries a real verdict from a later run, which wins once
  the token is expanded — see the slash-enumeration fix below.)
- **A lane arm proves one lane.** `M-DATASET-04-L` / `-06-L` / `-08-L` are LIVE-arm drives of demo-only
  features (each asserting the documented non-demo `400`). They fold onto their base row — the row expectation
  covers that behaviour — but render as `PASS (LIVE arm)`, never a bare `PASS`, because the demo arm was never
  driven.
- **A compressed range addresses real rows.** `M-TOPOLOGY-01..06,09..18 BLOCKED` (graph never renders in the
  live lane — F-CANOPY-006) is one record covering **fourteen** rows; taking the token literally dropped all
  fourteen. This expansion and the lane-suffix fold now match `util/ad-hoc/e2e_row_coverage.py`.

### Two more ways a run record addresses rows — and the last three cells they were hiding

Auditing the filler against the mapper left an unexplained residue, and chasing it found two further forms the
run records use that the tool did not read:

- **A slash enumeration is a range written differently.** `M-PARAMETERS-01/02/03 PASS` names three rows.
  `,` and `..` were expanded; `/` was not, so the token matched no matrix row and was dropped whole. `/` is now
  the same separator as `,`.
- **A rowlog records verdicts as prose bullets, not only table rows.** The filler read `| row | status |`
  tables exclusively. The first LIVE run also wrote free bullets, and three of them carry terminal verdicts.

Together these fill exactly three cells — **M-PARAMETERS-01/02/03 → `PASS`** ("tables render: 9/5/11 rows incl.
headers"). That is precisely the inheritance §"Coverage baseline" promised: those three ids are named in this
note's own list of rowlog-unique rows to inherit with run-id attribution, and they render as a bare `PASS`
exactly like the other inherited cells (C2.2-02, M-ABOUT-03, M-REDIS-01). The segment-4 note that they "read as
remaining and will be re-confirmed live rather than assumed" was describing the *mapper's* conservative
crediting, not a decision to discard the record; a recorded verdict with named evidence is not an assumption.

The bullet parser is deliberately narrow: the bullet must **open** with a row token followed by a terminal
verdict word, and only that leading token is taken. The one bullet that continues with bare `-03 PASS-with-note,
-05 …` continuations is not unpacked — those rows already carry later verdicts, and guessing at an ambiguous
continuation to save three cells is the trade that produced the C2.2-04 mis-fill above. Under-reading is
recoverable; a wrong status cell is not.

**The two tools still disagree by one row, and the filler is the correct one.** The mapper credits only the
*leading* token of a slash enumeration, so it counts M-PARAMETERS-01 verdicted while M-PARAMETERS-02/03 read
remaining. `e2e_row_coverage.py` is a coverage estimator, not the ledger; the matrix is the ledger. Left as-is
and recorded here rather than quietly reconciled by loosening one of them to match the other.

### Where the remaining 158 rows are

| section | filled |
|---|---|
| §2.1 / §2.2 / §2.3 header, tabs, status bar | 4/4, 6/6, 8/8 |
| §2.4 WS badge | 5/7 (C2.4-02 demo arm, C2.4-05 upstream-degraded induction) |
| §2.5 training controls | 9/10 |
| §2.6 NN meta-parameters | 4/19 |
| §2.7 dataset subsection | 0/10 |
| §2.8 candidate-node meta-parameters | 0/14 |
| §2.9 banner trio / Apply / Experimental / Network Info / Pinned | 0/16 |
| §2.10 global modals + floating alerts | 0/17 |
| §3.1 metrics | 10/32 |
| §3.2 candidates | 7/11 |
| §3.3 topology | 18/18 |
| §3.4 evolution | 5/7 |
| §3.5 boundaries | 0/8 |
| §3.6 dataset view | 3/27 |
| §3.7 workers | 5/6 |
| §3.8 parameters | 3/7 |
| §3.9 snapshots | 4/21 |
| §3.10 replay / §3.11 network editor | 17/17, 18/18 |
| §3.12 redis / §3.13 cassandra / §3.14 tutorial / §3.15 about | 4/4, 4/4, 3/4, 3/3 |

The unfilled mass is concentrated in the **sidebar** (§2.6-§2.10, 66 rows) and three tabs (dataset view,
snapshots, metrics — 70 rows). That is the shape of the remaining Phase-1 live work, and it is now visible
from the matrix itself instead of having to be reconstructed from run records.

### Two verdict ids that have no matrix row — on purpose

`C2.5-TRANSPORT` (the FE-1 behavioural transport proof) and `C2.5-D5` (divergence D-5 + the unavailable
transport oracle) were recorded as synthetic ids in segment 9/10 because neither is a matrix row. The filler
reports them rather than dropping them silently; they live in this note, not in a status cell.

### Methodology note (segment 11)

Consolidation is worth a segment of its own. The three-source merge surfaced a mis-filed verdict, three
separate row-addressing forms the tool could not read (`..` ranges, `/` enumerations, prose bullets), and a
non-terminal value one step away from being recorded as an outcome — none of which a live-driving segment
would have looked for.

The generalisable part is the audit method, not any one fix: **two independent tools counting the same thing
and disagreeing is a defect detector.** Every one of the row-addressing gaps above was found by taking a small
unexplained delta between `e2e_matrix_fill.py` and `e2e_row_coverage.py` seriously instead of rounding it off.
The last disagreement is left standing *because* it is now explained — a reconciled number that no longer
carries information is worth less than an explained discrepancy.

---

## Phase 1 — segment 12 (2026-08-16): the sidebar driven live, and the numeric wall is gone

Run id `20260816T124231Z`. Stack: canopy `f90420e` (0.4.0, :8051), cascor `3909d27` (0.9.0, :8202),
juniper-data `4db9544` (0.11.0, :8101), all launched fresh at 07:41 local and health-gated on
`demo_mode:false` + `juniper_data_available:true`. Matrix **140 → 168 of 298**.

Segment 11 consolidated; segment 12 drove. The target was the four sidebar sections (§2.6–§2.9, 55 rows),
which the matrix classes largely as `AUTO-API` — "not drivable through the browser". That classification
turned out to be the segment's headline.

### The headline: `F-CANOPY-017` is fixed, so the `AUTO-API` wall no longer exists

The handoff asked for the class to be re-tested before `AUTO-API` was accepted as "API only". It does not
hold. **juniper-canopy#489 (`d11bfcd`, 2026-08-14) fixed `F-CANOPY-017`** — its commit message cites the
finding by name and describes the same root cause this arc recorded.

A live DOM sweep of **all 20** sidebar numeric inputs on canopy `f90420e` found **every one** reporting
`validity.valid = true` and `stepMismatch = false`. All seven fields the finding named as off-grid are
repaired, to the `float="any"` / `int=1` pattern:

| field | F-CANOPY-017 recorded | now |
|---|---|---|
| `nn-max-iterations-input` | `step=100` | `step=1` |
| `nn-max-total-epochs-input` | `step=1000` | `step=1` |
| `nn-learning-rate-input` | `step=0.001, min=0.0001` | `step="any"` |
| `nn-growth-preset-epochs-input` | `step=10` | `step=1` |
| `nn-dataset-elements-input` | `step=100` | `step=1` |
| `cn-correlation-threshold-input` | `step=0.0001` | `step="any"` |
| `cn-training-convergence-threshold-input` | `step=0.00001` | `step="any"` |

The finding's own live instance was re-run: typing **`0.0733`** into `#nn-learning-rate-input` — the exact
value whose old grid position produced "typed 0.0733 → POSTed 0.01" — now reads valid and commits.

That is not merely a DOM-level result. Typed values were shown to reach **cascor**: `output_epochs=12345`,
`patience=88`, and the whole `S/T/R` triple were read back from `GET /v1/training/params` and survived a full
page reload. `F-CANOPY-017` is therefore recorded **RESOLVED (verified live)**, and the matrix's `AUTO-API`
column is flagged stale for these rows in §1.1.

### Two driving techniques, cross-validated

Real keystrokes (`focus` → `Control+a` → `Delete` → `pressSequentially` → `Tab`) drove `C2.6-02` end to end.
Because a per-keystroke Dash round trip makes that path cost ~6 tool calls per field, the rest of the numeric
rows were driven with the React native-setter (`HTMLInputElement.prototype.value` setter + a real `input`
event). The two were cross-validated: both produce the identical dirty→Apply transition, and the native-setter
path was additionally proven to round-trip to the backend on five separate fields. Neither is the `page.fill()`
that the old doctrine indicted.

Per-field attribution used a **set → revert** probe: set a value, wait for `apply-params-button` to go
`disabled → enabled`, restore the original, wait for `enabled → disabled`. Both transitions belong to that one
field, so no row borrows another row's evidence.

### Three new findings

**`F-CANOPY-022` (P1) — "Add Top Tier Candidates" can never be applied.** canopy and cascor disagree on the
value vocabulary. canopy declares `{"label": "Add Top Tier Candidates", "value": "top_tier"}`
(`juniper-canopy/src/frontend/dashboard_manager.py:1471`); cascor accepts only
`Literal["top","random","mixed"]` (`juniper-cascor/src/api/models/training.py:159`, `:327`). No translation
exists — `_toggle_cn_selection_inputs_handler` (`dashboard_manager.py:6815-6821`) consumes `top_tier` purely
for UI gating and the raw value enters the payload. Selecting it with an otherwise-valid triple
(S=5, T=5, R=0; clientside feedback empty) yields
`literal_error … 'input': 'top_tier' … "Input should be 'top', 'random' or 'mixed'"`. **Control:** the sibling
`random` arm matches cascor's literal exactly and applied cleanly in the same session. One of the two shipped
options is permanently unusable; cascor's third literal `mixed` has no canopy option at all.

**`F-CANOPY-023` (P1) — a successful apply is reported as a 502 failure.** Observed as two halves:

* *cascor* does not store what was sent for `epochs_max`. `PATCH /v1/training/params -d '{"epochs_max":
  115000}'` returns `200 status=success` while the stored value stays `140795`. Control: the same shape with
  `{"patience": 77}` stored 77.
* *canopy* fails the whole apply on any single divergence. `_verify_apply_roundtrip`
  (`juniper-canopy/src/backend/cascor_service_adapter.py:~1316-1334`) compares every mapped key after the
  write and returns `{"ok": False, "error": "verification_failed"}` for the entire operation.

> **CORRECTION (same segment, after source review).** The first bullet is **not** a cascor defect, and calling
> it one was an error of method: I read only the `data` block of a raw `curl` response. `epochs_max` is a
> **derived read-only** value by owner decision (C2b / Q1 outcome (c),
> `juniper-cascor/src/api/lifecycle/manager.py:1618-1640`), and cascor deliberately accepts it at the request
> boundary "so pre-N5 canopy full-form applies keep succeeding" while reporting it as `skipped(not-updatable)`
> in its C2a accounting (`manager.py:3583-3586`) — so it is not silent either. **The defect is canopy-only,
> and it is an ordering bug**: the verify at `:1325` short-circuits *before* `_extract_cascor_partition` at
> `:1339` reads the partition that explains the divergence — and that method's own docstring already says
> "`epochs_max` is the standing `not-updatable` case post-C2b". See the ledger entry for the corrected
> statement.

Live: canopy logged `apply_params verify mismatch: {'epochs_max': {'requested': 115000, 'applied': 140795}}`
and showed `Failed to apply (HTTP 502) … verification_failed` — yet cascor had taken every edit, and they
survived a reload. The trigger is precise: only when the sidebar's seeded `nn_max_total_epochs` has gone stale
against cascor's live `epochs_max`, which happens across a training run. **Why earlier segments missed it:**
`W3-03` drove `/api/set_params` with a body seeded from live `/api/state`, so no key could diverge.

**`F-CANOPY-024` (P2) — the shipped default candidate triple is invalid.** On the first sweep of a fresh
stack, before any edit: S=1, T=1, R=1, so T+R=2≠S. Both validators agree — the clientside feedback and
cascor's rejection are the same sentence — so the *first* Apply on a fresh dashboard always fails. The user
cannot fix it in place, because T and R both ship `disabled=True` behind `cn-multi-candidate-checkbox`.

### `F-CANOPY-018` confirmed and sharpened

Still open on `f90420e`, and the prior characterisation was a sampling artifact. The success toast **is**
rendered: sampling `params-status` at 900 ms intervals caught `Parameters applied` at t=1800 ms, overwritten
by `⚠️ Unsaved changes` at t=2700 ms and never returning. **The toast survives ~900 ms.** Earlier segments
recorded "never the success toast, 3 independent runs" — they sampled too coarsely. All three documented §2.9
shapes were observed this segment, so `_compose_apply_toast` is correct; the row fails only because the second
writer destroys its output. Also not previously recorded: **after a successful apply the form never returns to
clean** — Apply stays enabled and the status stays `⚠️ Unsaved changes` until a page reload.

### `F-CASCOR-003b` — not settled, and the measurement method was the problem

The naive count appeared to reproduce the original observation — `pgrep -f 'JuniperCascor1.*forkserver'`
returned **18** at +43 s and +73 s after a clean stop — then fell to 7, to 3, and **rose back to 11**. A rise
is impossible for a draining pool, which exposed the error: the box is shared, and the pattern was matching a
concurrent session's cascor.

Attributing by parentage instead, my leg (pid `298210`) held exactly two children — `319149` (14 MB) and the
476 MB multiprocessing forkserver `319150` — and **no candidate-pool grandchildren**. The 461 MB × 7 cluster
belonged to a different cascor (pid `348136`), started 130 s earlier by another session. The forkserver
persisting is expected and is not pool residency.

Recorded **INCONCLUSIVE**. The next attempt must record the leg pid at bring-up and count only its
descendants. The original observation was taken with the box-wide method and should be re-taken before being
treated as real.

### Row results (segment 12) — 28 rows

| verdict | rows |
|---|---|
| **PASS** (27) | C2.6-02, C2.6-03, C2.6-04, C2.6-08, C2.6-09, C2.6-13, C2.6-15, C2.6-16, C2.7-01, C2.7-04, C2.7-05, C2.8-01, C2.8-02, C2.8-03, C2.8-04, C2.8-05, C2.8-06, C2.8-07, C2.8-08, C2.8-10, C2.8-11, C2.8-12, C2.8-13, C2.8-14, C2.9-04, C2.9-10, C2.9-12 |
| **FAIL** (1) | C2.9-05 (`F-CANOPY-018`) |

`C2.8-05` deserves note: three of the nine truth-table branches were exercised, each flagging exactly the
offending input(s) and no others, and branch (1)'s message is **byte-identical** to cascor's own server-side
rejection. That proves the clientside mirror matches `_validate_candidate_pool_triple` rather than merely
looking plausible — a stronger result than a DOM-only assertion could give.

### Methodology notes (segment 12)

**Settle times are much longer than the arc has been assuming.** Measured this segment: `C2.8-01` toggled at
**3.5 s**; `C2.9-12` at 3.0 s; the `cn-multi-candidate-checkbox` sub-group took **more than 8 s** to recover
after an uncheck→re-check. At 4 s that last one read as opacity stuck at 0.5 with both count inputs dead — a
convincing defect that I drafted and then withdrew when a longer window showed full recovery. The handoff's
"1.5–2 s" is a floor, not a range; **poll for the expected transition, never sample once.**

**Playwright's click ack is unusable on this page, and worse during a run.** Every `browser_click` timed out at
5 s. On a quiet page the click still *lands* (the log reaches "click action done") and must be verified by
effect — the documented trap. During an active training run the actionability wait never clears at all and the
click genuinely does not land: a `stop-button` click was lost this way, confirmed by the absence of any
`Control command received: stop` line. A JS `.click()` on a `<button>` drives the real callback chain — the
same gesture produced a genuine `/ws/control` `stop` command with a `command_id` — and is the reliable path.
The numeric wall was always about `type="number"` *value* propagation, never about button clicks.

**A count on a shared box is not a measurement.** See `F-CASCOR-003b` above. The same caution applies to any
future GPU- or process-level assertion in this arc: attribute to the leg pid, or do not claim it.

**Two near-miss false findings this segment**, both caught by re-checking rather than by filing: the
"stuck" multi-candidate sub-group (under-settled), and an apparent both-inputs-enabled violation of
`C2.8-12`'s documented "or" (a mid-transition read at 1000 ms; the settled state is exclusive). Both would
have been plausible, specific, and wrong.

### All three segment-12 findings fixed the same day (owner-directed)

| finding | PR | merge | shape of the fix |
|---|---|---|---|
| `F-CANOPY-022` | juniper-canopy#492 | `0460240` | radio ships `top` (cascor's literal); handler accepts `top`/`top_tier`; `_CANOPY_TO_CASCOR_VALUE_MAP` translates the legacy value at the adapter boundary |
| `F-CANOPY-024` | juniper-canopy#493 | `71b569b` | `DEFAULT_RANDOM_CANDIDATES_COUNT` 1→0 (shipped triple S=1,T=1,R=0 is valid) and the two count floors 1→0 to match cascor's `ge=0` |
| `F-CANOPY-023` | juniper-canopy#494 | `56ce45f` | extract the C2a partition **before** the verify; exclude cascor-declined keys; static `_DERIVED_READONLY_CASCOR_PARAMS` backstop |

**Each fix carries a negative control**, and in two cases the control reproduces the *live* symptom
verbatim: disabling the `F-CANOPY-023` exclusion yields
`{'epochs_max': {'applied': 140795, 'requested': 115000}}` — the same two numbers captured on the running
stack — and reverting the `F-CANOPY-024` default yields
`top_candidates+random_candidates must equal S=1 (got 1+1=2)`, the same sentence both validators printed.

**A correction the fixes forced.** `F-CANOPY-023` was published as a two-repo defect. Reading cascor's
source to write the fix showed the cascor half is deliberate, documented, and *announced* — see the
CORRECTION block on the ledger entry. The lesson generalises past this arc: **a raw `curl` that inspects
only the payload you expected can manufacture a defect out of a documented contract.** cascor was reporting
`epochs_max` in its `skipped` partition the whole time; I never looked at that key of the response.

**Method note for fixing, not just finding.** Each fix was developed in a throwaway `git clone` under the
scratchpad rather than in the sibling checkout — the working tree is shared with concurrent sessions, and
`util/open_signed_pr.py` needs no working tree anyway. Because `open_signed_pr.py` uploads *whole files*, two
PRs touching the same file must be **merged sequentially and the second rebased**, or the second silently
reverts the first; `F-CANOPY-023` was held back for exactly that reason while `F-CANOPY-024` (disjoint files)
went in parallel. Local suites need `LD_LIBRARY_PATH=` cleared: invoking the env's python directly bypasses
the conda hooks that strip it, and an ambient `rust_mudgeon` libtorch then breaks *module import* with
`undefined symbol: _PyObject_NextNotImplemented`, which reads like a test failure and is not one.
On this host the unmodified canopy `tests/unit` sweep fails **34** tests (19 redis, 10 cassandra, 5 metrics)
for want of backing services — measured on a pristine clone, and identical set-for-set with the fix applied,
so "34 failures" is the floor to compare against, not a regression.

---

## Phase 1 — segment 13 (2026-08-17): §2.10 closed, and a shipped feature found unreachable

Run id `20260817T093715Z`. Stack: canopy **`56ce45f`** (all three segment-12 fixes present and verified in the
launched tree), cascor `3909d27`, juniper-data `4db9544`; health-gated on `demo_mode:false` +
`juniper_data_available:true`. Matrix **168 → 198 of 298**. 30 rows, plus one new P1.

The browser MCP was unavailable again (present in segments 9 and 12, absent in 8 and here), so driving used
the arc's script fallback — a new `util/ad-hoc/e2e_seg13_modals_driver.py` reusing the segment-8 w3 helpers,
run under `JuniperCanopy1` with `LD_LIBRARY_PATH=` cleared.

### §2.10 is closed — 17 of 17

15 PASS, and the two BLOCKED rows are blocked by the finding below rather than by anything about themselves.

* **C2.10-01 / -04** — both modals open on demand (1500 ms / 1000 ms) with every declared child present.
  `restart-modal-baseline` is the one absentee and is *not* a missing surface: it is a `dcc.Store`
  (`:2045`), which Dash 3.x emits no DOM node for.
* **`keyboard=False` proved behaviourally**, not by reading a prop: Escape left `restart-confirm-modal`
  open, while the same keypress closed the model picker — which is documented *without* that flag.
* **C2.10-05 / -06** — the floating alerts stack exactly where the matrix says, read as computed style:
  `training-control-outcome-alert` 144px = **9rem**, `restart-outcome-alert` 208px = **13rem**,
  `dataset-stage-outcome-alert` 272px = **17rem**.

### The T-22 "MANUAL-only" limitation is retired

The matrix stated the *modify* half of the 11 granular restart fields "is not drivable by any documented
automated method". That rested on the numeric wall canopy#489 removed. Measured: **all 10** numeric fields
now report `valid=true` / `stepMismatch=false` on the `float="any"` / `int=1` pattern — **including the six
`restart-p-*` fields segment 10 explicitly flagged as never re-tested**. All 10 were then driven, each
re-rendering `#restart-confirm-summary` with its delta in 1400–2800 ms, plus `restart-ds-type`
(Spirals→XOR) at 700 ms. The param fields render into their own section:

    Parameter changes to apply before restart:
    Learning rate: 0.01 → 0.0733 · Max hidden units: 1000 → 7 · Patience: 50 → 77

The matrix's LIMITATION block is struck through with the measurement, and the `auto` column flagged stale.

### F-CANOPY-025 (P1) — the Live Dataset Switch cannot be reached

See the ledger entry for the full evidence. The short form: the gate callback is **registered**, both of its
store inputs are **provably true on the wire**, and it **never emits** — zero `_dash-update-component`
responses carry the button across 120 s, a reload, and a forced toggle. The hot-swap surface (C2.7-10,
C2.10-02/03, workflow **W7**) is unreachable from the dashboard.

The instructive part is *why five segments missed it*. The only prior record is `W7-step1 PASS` — the **deny**
arm. A gate that never opens passes every "should be disabled" assertion. **A negative-arm pass is not
evidence a gate works**, and this arc should treat any deny-only row as unproven until its allow arm runs.

### §2.9's tail — 9 of 12

PASS: C2.9-01 (both paths — opened by Apply Dataset at 2500 ms, *and* reconciled from
`/api/status.pending_dataset` at 5000 ms on a cold load with no gesture), -02, -03 (`pending_dataset` →
`null`, banner closed 2100 ms), -07, -08, -09, -11, -13, -16.

`C2.9-16` was scored from both ends: `CONTROL_TOOLTIPS` has exactly **23** entries including
`apply-params-button` — matching the matrix's "22 parameter inputs + apply-params-button" — and hovering
rendered the right text per target.

**Three rows deliberately left unfilled**, because the instrument failed rather than the app:

* **C2.9-14 / -15** (pinned card + list) — the pin checkbox could not be driven. Neither the native-setter
  idiom nor a trusted `page.check()` reached its Dash `value` prop. The wire shows the chain is *correct*:
  `pinned-params-store` received `data: []` and `sidebar-pinned-card` correctly got `display:none` for an
  empty store. Recording this as NOT DRIVEN rather than a defect.
* **C2.9-06** (apply-in-flight interval clamp) — the form never dirtied during a live run, so no apply was
  ever in flight and there was nothing to score.

### Methodology notes (segment 13)

**The JS-click rule needs a caveat.** Segment 12 established that a raw `.click()` drives the real callback
chain where Playwright's ack times out. That holds for `<button>` — it opened both modals, the banner
buttons and the granular toggle. It is **inert on `dbc.Switch` checkboxes**: on
`experimental-functions-toggle` a `.click()` left `.checked` *and* the backend untouched across a 10-sample
fast poll, while the native-`checked`-descriptor + `change` idiom flipped the backend to `enabled: true`.
Switches need the numeric-input technique, not the button technique — and `dbc.Checkbox` (the pin controls)
resisted **both**, so the family is not uniform.

**Closed means absent.** Modals and the pending-dataset banner are not in the DOM at all while closed;
`getElementById` returning null is the normal shipped state, so every check polls for *appearance*. The
floating alerts are the opposite — always present, height 0 — which is why their `top` offsets are readable
at rest.

**Prove a refill with a value that moves.** Sampling `network-info-panel` twice on an idle network shows
identical text and proves nothing; against a live run it moved from "Input Nodes: 0 / Hidden Units: 0" to
"Input Nodes: 2, Hidden Units: 6 / 10, Training Step: 6". Same for the details panel (empty → populated).
One observation logged against **F-CANOPY-006** rather than filed fresh: those details totals read
`Total Nodes 0` while the live network held 6 hidden units — the topology-counts class segment 9 already
withdrew a P1 for.

**Playwright's `page.hover()` fails the same way its `click()` does** (30 s timeout), so tooltip proof came
from dispatching `pointerover`/`mouseover`/`mouseenter` directly.

---

## Phase 1 — segment 14 (2026-08-17): §3.9 Snapshots, and instruments that lie

Run id `20260817T101500Z`. Stack: canopy `56ce45f`, cascor `3909d27`, data `4db9544`; health-gated on
`demo_mode:false` + `juniper_data_available:true`, with the 4-snapshot corpus present (backed up first —
a failed `--up` calls `do_down` internally, which deletes it). Matrix **198 → 212 of 298**.

**§3.9 goes 4/21 → 18/21.** Fourteen rows, all PASS. New driver
`util/ad-hoc/e2e_seg14_snapshots_driver.py`.

### The headline result

**M-SNAPSHOTS-15** is proved three independent ways, which matters because the canopy POST is server-side
and therefore invisible to the browser:

1. UI — `-restore-status` rendered `✅ Restored from snapshot 'snapshot_20260813T051936Z'`
2. Backend FSM — `STOPPED` → `INVESTIGATING`
3. `GET /v1/network` — `hidden_units: 10`, the snapshot's topology genuinely rehydrated from 0

**M-SNAPSHOTS-16** carries the row's distinguishing claim: a confirmed *replay* also moved
`visualization-tabs.active_tab` from `Snapshots` to `Replay` (the third `active_tab` writer, D-1), with
`✅ Snapshot replay started`.

### Three instruments that produced confident, meaningless numbers

This segment's real lesson is not any single row — it is that **the obvious measurement was wrong three
separate times**, and each wrong measurement supported a plausible verdict.

1. **Browser-request counting for the refresh rows.** `M-SNAPSHOTS-04` first read as "zero GETs, never
   refreshes". The list fetch is issued *server-side* from the Dash callback, so zero browser requests is
   the expected state — the arc's own standing rule, re-learned. Re-measured on the canopy log as a rate:
   idle baseline 7 fetches/60 s (2.33 per 20 s), driven 4 clicks in 20 s → **4 fetches**, a clean 1:1
   above noise.
2. **A single timing window.** The first `M-SNAPSHOTS-05` sample gave gaps of 0.33 s to 92 s — all
   self-inflicted, because the driver was clicking throughout. On two *strictly idle* 60 s windows it
   settles to 5 and 7 fetches (median gap 8.77 s), bracketing the source-declared
   `DEFAULT_REFRESH_INTERVAL_MS = 10000` once F-CANOPY-004 jitter is allowed for. Recorded as
   consistent-with-10 s, not as an exact period.
3. **A stale element id.** Every click in this panel races the 10 s table rebuild — the same mechanism
   behind F-CANOPY-009 and F-CANOPY-010. Each step now re-queries its target immediately before clicking
   and retries; `M-SNAPSHOTS-16` needed **3 attempts**, `-17` needed 2.

### A finding I did not file

Restore failed to open twice while its three siblings opened cleanly. Two attempts, consistent, and
op-specific — a convincing defect. On the focused re-run it **inverted**: restore opened at 750 ms and
*resume* failed. The wire gave the real cause — F-CANOPY-010's early-out, returning exactly the documented
`(False, "", None)`:

    {"restore-modal": {"is_open": false}, "restore-modal-body": {"children": ""}, "restore-pending-id": …}

The failure is **racy, not op-specific**. This is the fourth plausible-but-wrong finding this arc has
avoided by re-checking rather than filing (after the multi-candidate "stuck" control, the C2.8-12 "or"
violation, and the F-CANOPY-023 root cause). The rule is now well enough evidenced to state plainly:
**on this dashboard a first-pass anomaly is more often the instrument or a documented race than a new
defect — reproduce it a second way before writing it down.**

F-CANOPY-009 was also observed directly rather than inferred: the wire shows `-selected-id` receiving
`{"data": null}` and *then* the snapshot id, which is why a DOM-only read of the detail panel reported
"never rendered" (it would have been a wrong FAIL for `M-SNAPSHOTS-07`/`-08`).

### Three rows deliberately unfilled

* **M-SNAPSHOTS-19** — `MANUAL (native menu)`, a right-click context menu.
* **M-SNAPSHOTS-20 / -21** — `DEAD-EXPECTED`, and **unreachable**: those buttons render only inside
  dataset-swap cards, and the panel reports "No dataset swaps recorded yet." Scoring them needs a real
  dataset swap (W6/W7) to exist first. A `DEAD-CONFIRMED` verdict requires clicking a control that does
  not currently render, so no verdict is honest here.

The same precondition bounds **M-SNAPSHOTS-18**, recorded as `PASS (empty branch)`: the empty state renders
correctly, the populated paired-diff cards are unproven.

### Other measurements

`M-SNAPSHOTS-13`'s ⚠️ line was initially "missing" because the driver's own `probe()` helper slices
`textContent` to 120 chars. Read untruncated, the body carries all three documented parts (248 chars),
ending `⚠️ Training must be paused or stopped before any snapshot operation.` A reading artifact, not a
product gap — and a reminder that a helper's convenience truncation can manufacture a finding.

`M-SNAPSHOTS-14` is clean: modal open at 750 ms, Cancel, gone 300 ms later, and the POST hook recorded
`posts_seen: []` — no request of any kind, exactly as the row requires.

Also logged as an **F-CANOPY-006 observation, not a new finding**: after the restore, `monitor.
current_hidden_units` read 0 while `/v1/network` read 10 — the same stale-counter class segment 9 already
withdrew a P1 for.

---

## Phase 1 — segment 15 (2026-08-20): the live-run block, three new findings, and the checkbox gesture solved

Run id `20260820T080544Z`. Matrix **212 → 266 of 298** (54 rows). Stack: isolated trio at data 8101 /
cascor 8202 / canopy 8051, health-gated on `demo_mode:false` + `juniper_data_available:true`; leg pids
data 1349777 / cascor 1349995 / canopy 1350263 (recorded at bring-up for per-leg attribution). Sibling
checkouts verified current before driving: canopy `955e8d4` (≥ `56ce45f`, all three fix greps 1/3/1),
cascor `4bec1be`, both clean on `main`. The browser MCP **was** available this segment.

Sections closed outright: **§3.1 metrics 22/22**, **§3.2 candidates 4/4**, **§3.4 evolution 2/2**,
**§3.5 boundaries 8/8**, **§3.8 parameters 4/4**, **§2.6 4/4**, **§2.7 6/6**, **§2.8 1/1**, **§2.9 3/3**.
Not reached: §3.6 dataset (24), §3.7 workers (1), §3.9 snapshots tail (3), §3.14 tutorial (1), and the
four special-posture rows (C2.4-02, C2.4-05, C2.5-07) — 32 rows, all still unfilled.

### Corpus state on arrival — the seg14 backup was never restored

`juniper-cascor/src/snapshots/` held **zero** `.h5` files, not the 4 the handoff described. The four files
were sitting in `backups/e2e-snapshots-seg14/` — segment 14 took its backup and never ran the restore half.
They were restored before bring-up (so the snapshots panel had a corpus) and re-backed-up flat to
`backups/e2e-snapshots-seg15/`. **Successors: verify the corpus itself, not the handoff's count** — the
handoff's "4 `.h5` files currently live in …" was true as of the backup, not as of the handoff.

> **SUPERSEDED 2026-08-21 — do not carry this ceremony forward.** The snapshot root moved to
> `<Juniper>/juniper-cascor/cascor-snapshots/` under the S-1 storage-convention ruling
> ([`notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-STORAGE-CONVENTION-DESIGN.md`](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-STORAGE-CONVENTION-DESIGN.md),
> ml#1197/#1211), and `isolated_stack.bash` now reads it via `CASCOR_SNAPSHOT_ROOT` (`:122`).
> `juniper-cascor/src/snapshots/` is the importable serializer **package** and receives no artifacts, so the
> backup glob above matches nothing. **`--down` no longer sweeps the cascor corpus** — the script carries an
> explicit `-- DO NOT ADD A SWEEP OF ${CASCOR_SNAPSHOT_ROOT} HERE --` guard (`:476`), because that root is a
> protected asset store (**27,896 `.h5` / 1.8 GB**, measured 2026-08-21) that outlives every stack. There is
> nothing to back up and nothing to restore. Note the shared root is large enough that `ls *.h5` overflows
> the shell argument limit and reports **0** — count with `find <root> -maxdepth 1 -name '*.h5' | wc -l`.
> The paragraph's *general* lesson survives intact: verify the corpus and the script yourself rather than
> trusting a path or count quoted in a handoff.

### Two unresolved questions from earlier segments, now settled

**The segment-7 "1-in-15" full-history poll cadence is modulus 5 × a tick that is not 1 Hz.**
Measured in `full` display mode during a live run: 4 `metrics-panel-metrics-store` fills in 61 s, gaps
9.9 / 11.3 / 13.6 s — i.e. ~15.3 s per fill, reproducing segment 7's 1-in-15 against a
`FULL_HISTORY_POLL_TICK_MODULUS` of **5** (`canopy_constants.py:368`, applied at
`dashboard_manager.py:6380` as `n % 5 != 0 → skip`). The missing factor is the tick itself: instrumenting
`fast-update-interval`'s `n_intervals` off the request bodies gave **17 ticks in 42.7 s = a 2.51 s period**
against a declared `FAST_UPDATE_INTERVAL_MS` of 1000 (`canopy_constants.py:350`). 5 × 2.51 s ≈ 12.6 s,
matching the observed 10–14 s gaps. **The constant is correct as written; the effective wall-clock cadence
is modulus × the *actual* tick period, and the tick period is inflated ~2.5× by the same server-callback
congestion F-CANOPY-004 describes.** No new finding — but any future row scored "starved" must measure the
real tick before attributing anything to the modulus.

**The `dbc.Checkbox` gesture that defeated segment 13 is solved.** Recipe:

```js
box._valueTracker.setValue(String(!target));   // tracker must hold the OPPOSITE of the target
Object.getOwnPropertyDescriptor(Object.getPrototypeOf(box), 'checked').set.call(box, target);
box.dispatchEvent(new Event('click', {bubbles: true}));   // React drives checkbox onChange off CLICK
```

Two things were missing before: React's `_valueTracker` must be **desynced** (React's ChangeEventPlugin
ignores a write whose tracked value already equals the new one — my own first attempt set the tracker *to*
the target and produced exactly the segment-13 symptom), and the event must be **`click`**, not `change`.
Proven by the carried value in the response, not the DOM: `pinned-params-store` → `{"data":["learning_rate"]}`.
This unlocked M-PARAMETERS-04/-05/-06, C2.6-10, C2.9-14/-15 — six rows the handoff listed as blocked on it.
`dcc.RadioItems`, by contrast, responds to a plain raw `.click()`; the widget family is still not uniform.

### Findings

Three new, all written into the ledger above rather than left in this section: **F-CANOPY-026** (phase
duration inflated by exactly the host UTC offset — cascor emits naive local, canopy stamps it UTC;
invisible in any UTC-0 container), **F-CANOPY-027** (store-fill → render chains dead in the Candidate
Metrics and Decision Boundary panels; root cause NOT isolated), **F-CANOPY-028** (pinned params silently
discarded on the first pin after any reload).

**F-CANOPY-027 also re-opens five already-`PASS` rows.** M-CANDIDATES-01/-02/-03/-04/-06 were scored
against the panel's mount defaults — and `-02`/`-03`'s stated expectations literally name those defaults
(`"Idle"`, `"0"`). That is the F-CANOPY-025 negative-arm trap repeating in a second section. They are left
`PASS` (this segment did not overwrite prior cells) but should be re-driven once the chain is fixed.

**Three findings were *avoided* by the reproduce-a-second-way rule**, worth recording because each looked
solid on first pass:

1. *"The candidate panel's store isn't in the layout"* — `dcc.Store` and `dcc.Interval` render **no DOM**,
   so a `querySelectorAll('[id=…]').length` of 0 is normal. The control that killed it: the demonstrably
   *working* `metrics-panel-metrics-store` and `fast-update-interval` also return 0.
2. *"NN → CN multi-node checkbox mirror is broken"* — `_sync_multi_node_checkboxes_handler`
   (`dashboard_manager.py:6841-6852`) is deliberately **one-directional**: the
   `cn-multi-candidate-checkbox` branch writes NN, and the NN-triggered branch returns
   `no_update, no_update` by design. The matrix's "mirrored with the CN twin" wording on C2.6-10 is
   imprecise; the twin is `cn-multi-candidate-checkbox`, not a `cn-multi-node-*` id.
3. *"The pinned sidebar card is inconsistent with its store"* — it was simply lagging; it settled to
   `display:block` with the right label a few seconds later.

### Instrument traps hit this segment (all self-inflicted, all documented in the handoff)

- **My own wire buffer capped at 250 entries** and silently shifted — the exact shape of the documented
  `performance.getEntriesByType('resource')` trap. It reported 1 metrics-store fill where uncapped counters
  found 4. Replaced with counters that never evict.
- **My response capture sliced to 3000 chars** while the largest real Dash response this session was
  **675,891** chars. Every `includes()` must run against the full text before slicing — this alone nearly
  manufactured the F-CANOPY-027 write-up in a wrong shape.
- **A loose substring filter** (`'status-badge'`) matched another panel's badge and reported 15 phantom
  outputs; the precise id returned 0.
- **Real keystrokes do not land on this page.** `elementHandle.type()` timed out at 5 s *and* left the
  value untouched with no wire traffic — unlike clicks, which land despite the ack timing out. The
  native-setter idiom remains the only working numeric path.
- Probing a control immediately after a tab switch reports `ABSENT` for elements that exist —
  `nn-init-output-weights-dropdown` "vanished" and reappeared once the sidebar settled.

### Selected evidence

- **§3.1 layout CRUD** round-tripped fully against the API oracle: save → 8→9 layouts with `seg15_layout`
  at head and the name input cleared; load → status `saved`→`loaded`; delete → 9→8 and dropdown cleared.
  Settle times 11.0 s / 4.8 s / 17.2 s — more datapoints for F-CANOPY-004.
- **M-METRICS-20's clamp is effectively dead for typed out-of-range input**: `dbc.Input` reports invalid,
  Dash sends `None`, and `window_size or 100` (`metrics_panel.py:1174`) yields **100**, not the boundary
  1000. In-range 250 round-trips correctly. The store never holds an out-of-range value, so the safety
  property holds; only the mechanism differs from the row's wording.
- **M-BOUNDARIES-01's resolution arm proved by mesh density**, not by the plot: ArrowRight moved the thumb
  100 → 125 (step 25) and the refetched `xx` row spacing tightened from 0.441 (res 50) to 0.219.
- **C2.6-05 confirms DIVERGENCE D-2 twice over**: changing `nn-init-output-weights` alone never enabled
  Apply across a 30 s watch, yet after an unrelated Apply `/api/state` reads
  `nn_init_output_weights = random` — the value travels on the 28-State gather while sitting outside the
  27-input dirty-tracking set, exactly as C2.9-04 documents.
- **C2.7 dataset staging shape differs by generator**: spirals stages **flat**
  (`{dataset_type, n_samples, noise, rotations, n_spirals}`) while circles nests under `params{}`
  (`{dataset_type:"circles", params:{n_samples:777, …}}`). Both accepted by `/api/stage_dataset`.
- **C2.9-06's interval clamp**: `apply-in-flight` was set and released to `false` in the same response that
  carried "Parameters applied" — the `:3209` release path, not the `:3241` watchdog — with 1187 Dash
  responses spanning the window, so the dashboard demonstrably never froze. The two interval `disabled`
  Outputs produce **no** wire traffic because `:3213-3226` is a clientside callback; 0 hits there is
  expected, not a miss.
- **F-CANOPY-006 got two starker live confirmations**: canopy `/api/status` reported `hidden_units: 0`
  while `/api/metrics` reported `network_topology.hidden_units: 1`, and later `0` against cascor's
  `current_hidden_units: 7`. Post-run the tile correctly read `10 / 10`.
- The run **completed on its own** (`fsm_status: COMPLETED`, 10/10 hidden units) partway through the
  replay work — which is *why* the §3.1 replay controls became visible, and it supplied the post-run
  reading for M-METRICS-23 (accuracy `96.00%`).

### Why §3.1's replay block (M-METRICS-11..18) came out BLOCKED

The controls revealed correctly at COMPLETED (`display:block`, h=95) and `metrics-panel-replay-position`
shows its documented ship value `0 / 0` — but the replay **timeline never materialises**: position stays
`0 / 0` and the slider at 0 even though `metrics-panel-metrics-store` is filling 18×/30 s with real data,
and the loss plot carries 3 traces but a single point. With `max_index` 0 every documented index
transition clamps to 0, so none of them has an observable. **M-METRICS-13 is the discriminator to re-drive
first**: its "icon becomes ⏸ while playing" claim is data-independent and it also failed, with zero wire
output across 196 responses. Whether that is a third face of F-CANOPY-027 or its own defect is not
established, and is deliberately not claimed here.

### Tooling added

`util/ad-hoc/e2e_unfilled_rows.py` — lists the still-unfilled rows **straight from the ledger**, grouped by
`###` section with line anchors, reusing `e2e_matrix_fill`'s own pipe-splitting and placeholder set so it
cannot drift from what the filler will write. This exists because segment 15's own handoff draft published
the *estimator's* row list under the ledger's headline and was caught only in validation. Run it, and diff
its table against the filler's dry run, before planning any segment.

---

## Phase 1 — segment 16 (2026-08-21): the last 32 rows — matrix COMPLETE at 298/298

Run id `20260821T212306Z`. Matrix **266 → 298 of 298**. **Phase 1 row coverage is complete**: every row in
the matrix now carries a terminal verdict, including the four that had sat on a non-terminal `pending …`
since earlier segments (`C2.4-02`, `C2.4-05`, `M-WORKERS-02`, `M-TUTORIAL-04`). Sections closed this segment:
**§2.4 6/6**, **§2.5 10/10**, **§3.6 27/27**, **§3.7 8/8**, **§3.9 21/21**, **§3.14 4/4**.

The browser MCP was **absent** this segment (as in 8, 13, 14), so everything was driven through a new script,
`util/ad-hoc/e2e_seg16_dataset_driver.py`, under `LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python`.

Three stack postures were used: the default isolated trio; a second cycle with
`JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` for `C2.5-07`; and a hand-launched DEMO canopy on port 8053
for `C2.4-02`. The corpus needed **no** backup — the S-1 migration moved the root to
`juniper-cascor/cascor-snapshots/` and teardown no longer sweeps it (verified by `--dry-run --down`, and by
counting 27,906 `.h5` intact after the final teardown).

### Findings

Three new, all in the ledger above: **F-CANOPY-029** (the Dataset View generate modal 500s on every click —
root-caused to a single line, with a green-but-vacuous unit test explaining why nobody noticed),
**F-CANOPY-031** (the snapshots panel never renders against the 27,903-entry migrated corpus),
**F-CANOPY-032** (the worker "data degraded" alert never renders although canopy's own API reports the error).
**F-CANOPY-027 gained a third instance** — the Dataset View plotter — and two candidate mechanisms for it
were tested and refuted; see its entry.

**F-CANOPY-029 is the most actionable defect this arc has produced.** It is deterministic, one line, and the
error message names its own fix (`Did you mean: 'get_triggered_id'?`). The reason it survived is worth more
than the bug: the unit tests patch `get_callback_context` with a bare `MagicMock()` and then set
`fake_ctx.triggered_id`, so they assert against a shape the production adapter never had. `spec=` on the mock
would have caught it. That is the same "green tests / dead app" seam class the mock-seam auditor exists for.

### Corrections to the handoff, made from measurement

- **`C2.4-05` and `M-WORKERS-02` do NOT share an induction.** The handoff said they did. `degraded` requires
  the relay **healthy** and the control stream **unhealthy** (`cascor_service_adapter.py:1004-1006`), so
  taking cascor down yields `reconnecting`, not `degraded` — which is exactly why segment 4 got the wrong
  state. The working induction is to restart **cascor only** with
  `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` pointed at a bogus origin, leaving canopy untouched (W14's T-2
  respected — `/v1/health demo_mode` stayed `False` throughout). That produced `overall='degraded'`,
  `relay='healthy'`, `control='reconnecting'` and the badge `WS: Upstream degraded` on `#ffc107`. The worker
  alert then still did not render under either mode — hence F-CANOPY-032.
- **`M-TUTORIAL-04` and `M-SNAPSHOTS-19` are not "native menu" rows.** Both are *custom JS* menus
  (`frontend/assets/context_menus.js`, `snapshot_context_menu.js`), so both are automatable. M-TUTORIAL-04
  was driven end-to-end: dispatching a `contextmenu` MouseEvent with real coordinates on a tooltipped control
  opened `#juniper-context-menu` (360x114) and clicking "View tutorial →" flipped `active_tab` to `Tutorial`.
  (The Playwright *locator* right-click times out, like every other click on this page — the dispatched event
  is what lands.)
- **The DEMO canopy must be launched with `LD_LIBRARY_PATH=` cleared.** The demo backend imports torch
  (`demo_backend.py:45`) where the service backend does not, so the first hand-launch died on
  `undefined symbol: _PyObject_NextNotImplemented` during startup — the documented rust_mudgeon trap, in a
  place the launcher never had to handle.

### Instrument discipline — one wrong finding caught, three probes rebuilt

I stated `dataset-plotter-split-selector` "definitively" never renders, on the strength of a served-layout /
DOM comparison (7 children served, 6 rendered) — and it was **wrong**. The very next step drove all three of
its values cleanly (`All Data` → `Training Only` → `Test Only`, 0 requests). The panel rebuilds continuously,
so a short settle produces false "absent" readings. **M-DATASET-12 is a PASS and there is no defect there.**
That is the arc's "reproduce a second way" rule earning its keep for the second segment running.

Three of my own probes had to be rebuilt mid-segment, each after producing a plausible wrong answer:
an unscoped `[role=option]` sweep that captured *other* open Radix menus and manufactured a 24-entry option
list (scoping by `aria-controls` gives the true 16); a `table tbody tr` count that was reading the Network
Info table and reported 63 snapshot rows that did not exist (the panel's own
`hdf5-snapshots-panel-table-body` has 0); and a theme-flip comparison that reported "changed" only because
the second sample carried an extra key, while the toggle had not fired at all — M-DATASET-14 is recorded
**BLOCKED** on that instrument limit rather than scored.

### Selected evidence

- **§3.6 data is real, not metadata-only.** The matrix's service-mode caveat (metadata tiles with empty
  plots) did not apply: `/api/dataset` returned `loaded:true` with `num_samples 1000`, `train 800 / test 200`
  **and** populated `inputs`/`targets`. The tiles and plots are empty anyway — F-CANOPY-027, not the caveat.
- **M-DATASET-10** options, scoped properly, are exactly the 16 from `GET /api/dataset/generators`, default
  `Spiral`, and selecting `Xor` produced **zero** `/api/dataset*` requests — select-alone-is-inert confirmed.
- **M-DATASET-11's LIVE arm** verified twice: the UI wrote `❌ Dataset generation only available in demo mode`
  into `-load-status`, and a direct `POST /api/dataset/generate` returned **400** with the same message.
- **M-DATASET-27** is a genuine PASS on the 2-D inverse: with spirals loaded, `seq-controls`,
  `seq-group-windows`, `seq-grid-container` and `seq-char-companion` are all `display:none` and every other
  `seq-*` element is 0x0 and empty.
- **The sequence set (M-DATASET-17..26) is BLOCKED for a structural reason**, not a timing one: a sequence
  dataset cannot be loaded in the LIVE lane at all. `POST /api/dataset/generate` is demo-gated (400), and the
  two sequence-capable registry entries — `equities` and `equities_seq` — both report `available:false` from
  `GET /api/dataset/generators`. Reaching these ten rows needs either the DEMO lane or a 3-D model posture.
- **C2.5-07's posture was proven three ways** rather than assumed: the flag in `/proc/<pid>/environ`, the
  *absence* of the clientside branch's log line (`dashboard_manager.py:4158` logs only in the `if` branch, so
  its absence proves the `else` ran), and the command working end-to-end.

### What Phase 1 completion does and does not mean

Every row has a verdict; that is not the same as every row passing. The matrix now carries a substantial
BLOCKED population whose common cause is a small number of open findings — chiefly **F-CANOPY-027** (three
panels), **F-CANOPY-029** (six §3.6 rows behind one dead modal), **F-CANOPY-025** (W7 and the swap cards) and
the LIVE-lane dataset gate (ten sequence rows). Fixing F-CANOPY-029 alone re-opens six rows for real scoring;
fixing F-CANOPY-027 re-opens roughly a dozen and also invalidates the five §3.2 rows currently carrying a
mount-default `PASS`. **Phase 2 should be ordered by that leverage, not by section number.**

---

## Phase 2 — fix 1 (2026-08-22): F-CANOPY-029, and what it says about the test suite

Run id `20260822T014138Z`. First **code** fix of the arc; everything before this was evidence capture.
Shipped as **juniper-canopy#504** (`041eb69`), canopy CI green on 20/20 required contexts including the
Playwright UI sub-suite, canopy main-verify green.

**The fix is one line** — `ctx.triggered_id` → `ctx.get_triggered_id()` in `toggle_generate_modal`. The
object is canopy's own `CallbackContextAdapter`, not `dash.callback_context`; the adapter exposes only
`get_triggered_id()`. The same file's *other* adapter call site
(`dashboard_manager.py:6621`) already used the correct accessor, so this was a single-site slip with a
correct in-file precedent, and the sweep confirmed the three other `.triggered_id` reads are on the genuine
dash context and are fine.

**The interesting part is why it shipped, and that generalises.** The two unit tests covering this callback
patched `get_callback_context` with a bare `MagicMock()` and set `fake_ctx.triggered_id` — an attribute the
adapter has never had. A bare MagicMock fabricates any attribute on demand, so the tests asserted against a
shape production never had and stayed green while every real click returned HTTP 500. Fixed by spec'ing the
fakes (`MagicMock(spec=CallbackContextAdapter)`), which makes the mock reject the wrong name.

**The hardening was checked against the defect rather than assumed.** With the production fix temporarily
reverted, the updated tests fail with exactly the production error; before the hardening they passed against
that same broken code. That before/after is the evidence the new tests are not themselves vacuous — worth
repeating for every mock-seam fix in this phase, because a hardened test that passes both ways buys nothing.

**Leverage confirmed.** Segment 16 predicted that fixing F-CANOPY-029 alone would re-open five rows. Re-driven
live: all five now PASS (M-DATASET-01 / -02 / -05 / -07 / -09). M-DATASET-03 stays BLOCKED on its own
DEMO-lane precondition, not on this defect. Matrix stays at **298 of 298**, with five cells moving
FAIL/BLOCKED → PASS.

**Two process notes for the rest of Phase 2:**

- **A fixed control can still look dead.** The repaired modal takes **~39 s** to appear under live-run
  callback congestion (F-CANOPY-004). My first post-fix probe used a 3 s settle and reported it still broken;
  only a polling re-drive showed the fix working. Every Phase 2 verification needs the same patience the
  Phase 1 driving did — otherwise a good fix gets reverted on a bad measurement.
- **Re-scoring rows needs a scalpel, not `--overwrite`.** `e2e_matrix_fill.py --overwrite` rewrites every
  cell any source covers, which would clobber the hand-authored cells earlier segments left
  (`INCONCLUSIVE`, `DIVERGENCE D-1 CONFIRMED …`). Added `util/ad-hoc/e2e_matrix_rescore.py`, which touches
  exactly the named rows, reuses the filler's pipe splitting, and refuses to write a line whose cell count
  changes.

---

## Phase 2 — investigation 2 (2026-08-22): F-CANOPY-027 narrowed, not fixed

**Outcome up front: F-CANOPY-027 is NOT fixed.** This session eliminated eleven more candidate mechanisms
with evidence, corrected two wrong statements in the finding, and left a much smaller hypothesis space plus
eleven reusable probes. The full technical record lives in the ledger entry; this section is the narrative.

### The symptom is real

Worth stating plainly, because the first job was to check the finding itself rather than inherit it. With the
Candidates tab active and a live run, the backend advanced `candidate_epoch` **1 → 101** at a steady
`candidate_pool_size 40` while the panel held a **single** DOM state for 180 s. No artifact, no timing
excuse.

### Two things the finding asserted that are false

- **"The consumers never fire."** They fire at mount. Every previous probe installed its hook *after*
  `open_dashboard` had navigated, waited ~3 s and dismissed the welcome modal — so all of them were blind to
  the mount burst by construction. Hooking via `add_init_script` (before any page script) caught
  `dataset-plotter-scatter-plot` dispatching with
  `changedPropIds='dataset-plotter-dataset-store.data,…'`. **They are wired and can fire.**
- **"They hang."** They complete — 0.6 s for the candidate consumers, 2.6 s for the dataset figure, against
  0.3–1.8 s for the working metrics consumers. Nothing sits in flight.

Both corrections change what a fix would even look like, which is why they were worth the effort even
without a root cause.

### The contradiction, stated precisely

In one 90 s window on the Candidates tab: the writer dispatched **32** times; **all five** of its consumers
dispatched **0** times — including the one whose output is just another store and renders nothing. A
separate window measured the payloads: **29 dispatches, 29 carried data, 27 differed from the previous
value.** The data genuinely changes; nothing downstream runs. The structurally identical metrics chain
dispatched 8× in the same window.

### What that rules out

Eleven mechanisms, each with evidence, listed in the ledger entry: not registered · component missing from
layout · invisible to the browser's dependency graph · duplicate ids · mount order · client-side exception ·
callback hang · value never changes · rendering-specific · writer/consumer id mismatch · different
registration path or `storage_type`.

Two of those deserve a note because they were *previously believed checked*. The duplicate-id check had a
blind spot precisely where this finding lives: segment 15 counted DOM nodes, and a `dcc.Store` renders none;
my own first layout audit collected ids into a `set()`, which discards multiplicity by construction. Both
would have missed a duplicated store. A dedicated walker now counts declarations — 461 ids, 461 distinct, 0
duplicates.

The mount-order hypothesis is the one I most expected to be right (every dead panel mounts on a tab switch;
the one working panel is the default tab). It was falsified by its own prediction: the working chain was
unmounted and remounted by a tab round-trip and kept working, DOM value advancing.

### Where it stands

Everything from the layout through the served dependency graph is provably correct and the server side is
provably reachable, so the break is in the **client's change-propagation for these specific store
components**. The two concrete next steps are in the ledger entry: read Dash's client-side redux/`paths`
state for the store and diff it against the working metrics store; or bisect by adding a temporary trivial
consumer of the same store in canopy source — if a brand-new callback on that store also never fires, the
defect is in the component instance, not in any of the five existing consumers.

### Method note

Four times this arc I have been misled by substring matching on component ids, and this session added two
more: `candidate-metrics-panel-training-state-store` **contains** `metrics-panel-training-state-store`, which
silently contaminated one control column, and a multi-output callback stores every output under one combined
key, which made a correct registry look like it was missing 253 entries. Exact `==` on ids, and counting
entries rather than trusting a derived index, is not pedantry on this codebase — it is the difference between
a finding and a false finding.

---

## Phase 2 — investigation 3 (2026-08-23): F-CANOPY-027 ROOT-CAUSED

**Outcome up front: F-CANOPY-027 is root-caused and is not a wiring defect at all.** It is *callback
starvation* under a hard-coded 12-slot concurrency cap in dash-renderer. The full technical record — the
renderer source lines, the live saturation numbers, and the clean-room reproduction with its control — is in
the ledger entry's `ROOT CAUSE (2026-08-23)` block. This section is the narrative.

### What broke the deadlock

Twenty mechanisms had been refuted, all of them *in situ*, against the full 461-component dashboard. The move
that worked was going the other way: build the smallest app that has canopy's shape on the same dash 4.2.0 /
dbc 2.0.4, and ask whether the symptom appears at all.

The first clean-room run did **not** reproduce — five panes, all live, even with canopy's
`visualization-tabs.children` rebuild. That negative result was the useful one: it killed "is never the
initially-active pane", the last standing hypothesis, and forced the question "what does canopy have that
five panes do not?" The answer turned out to be *load*, not structure.

### The instrument that had never been pointed at this

Every prior probe measured the served dependency graph, `paths`, the redux `layout`, or action *types*. None
read dash-renderer's own queues — even though `e2e_f027_client_state.py`'s docstring had named them and
observed that "a consumer parked in `blocked` forever is a different defect from one that is never queued at
all". Reading them settled it in one pass: the consumers sit in `requested`/`prioritized` with `blocked`,
`executing` and `executed` all at **0**. Queued, and never picked.

From there the renderer bundle (`dash_renderer.dev.js`, unminified, ships in the env) gives the rule in one
line: `available = Math.max(0, 12 - executing.length - watched.length)`. Canopy runs 26 interval-driven
server callbacks against those 12 slots and holds the pool full 83.6 % of the time.

### The correction that matters most

I filed nothing on the strongest-looking lead. All three dead writers take `visualization-tabs.active_tab`
as an `Input` and `no_update` off-tab; the one working writer deliberately takes only its interval and
carries a comment naming that exact hazard as "the I-1 starvation" — the codebase's own name for a defect
class it had already diagnosed and fixed once. It was a compelling story and it was wrong: moving the
dependency to `State`, verified applied in the served graph, changed nothing. The arc's rule — reproduce a
second way before writing it down — paid for itself again, and the fix-and-verify *was* the second way.

### What this changes downstream

F-CANOPY-004 (callbacks lagging 30 s–minutes during a live run) is the same saturation observed from outside,
not an independent defect. And the fix is architectural rather than local: canopy's tab-gated pollers are
gated **server-side**, so an inactive tab's poller still spends a full round-trip and a renderer slot to
decide to return `no_update`. Moving that gate to the client is the lever. That is a design task, not a
one-line patch, and it should be designed before it is coded.

### Method note

Two instrument lessons worth keeping. First, "present in the served `_dash-dependencies`" and "present in the
client's derived `graphs.inputMap`" are different claims; the arc had checked only the first and treated it as
the second. Second, a negative clean-room result is evidence, not a failed experiment — the five-pane run that
"didn't reproduce" is what identified load as the variable.

---

## Phase 2 — re-drive (2026-08-24): the F-CANOPY-027 rows against live runs — two lanes closed, one still starving

**Outcome up front: 16 rows re-driven under live training on canopy `f9defb4` (#507+#509 merged); the fix
holds on two of the three panels and does NOT hold on the third.** 8 rows PASS re-validated
(M-CANDIDATES-01/-02/-03/-04/-06 — previously PASS against mount defaults only — and M-DATASET-13/-15/-16,
previously FAIL); 5 FAIL with causes re-attributed or sharpened (M-CANDIDATES-07 → new **F-CANOPY-035**,
M-CANDIDATES-09 → new **F-CANOPY-036**, M-BOUNDARIES-02/-04 → F-CANOPY-027 residue,
M-BOUNDARIES-01 `PASS(slider-value)/FAIL(re-render)`); 3 BLOCKED with blockers re-attributed
(M-CANDIDATES-10/-11 → F-CANOPY-036; M-BOUNDARIES-03 unattributable at 1/s ambient polling). Run id
`20260824T080426Z` (16-row `statuses.tsv`); driver `util/ad-hoc/e2e_f027_redrive.py` (new; steps
idle/start/candidates/livecards/cardsprobe/boundaries/bprobe/dstats) plus `e2e_seg16_dataset_driver.py`.
Five training runs on one bring-up (spirals 1000×2, 800/200; isolated trio 8101/8202/8051,
`demo_mode:false`, `juniper_data_available:true`).

### The headline: the Decision Boundary render is still starved in steady state

§12.1's "all three panels alive" was verified by setProps A/B on quiet pages and DOM transitions at attach.
The live steady state disagrees for the boundaries panel, and the request capture states it exactly
(`bprobe`, fresh session, post-run): the `decision-boundary-boundary-data` feeder fired **80 times at ~1/s**
(dataset feeder likewise, 78) while the plot-render callback (`…-plot.figure` + `…-status.children`) fired
**exactly once — at mount, before the first fill applied — and never again in 115 s**. That session's figure
stayed at the empty `"No network loaded"` state its whole life while real mesh data streamed into the store
beside it: F-CANOPY-027's original signature, post-fix. A second session got lucky at attach (render ran at
t+22 s after the fills landed and produced the full contour + two-scatter figure — so the render itself is
correct when it runs); interactions afterwards (slider 100→125 in 3.4 s, confidence toggle with the React
value-tracker following) produced **zero** re-renders in 30-60 s windows.

The mechanism is the F-CANOPY-036 promotion race generalized: **a consumer of a store whose feeder's
in-flight time covers the feeder's period is never promoted again** — dash-renderer will not promote a
callback while any of its Inputs is claimed by a pending callback, and a ~1 Hz feeder with a ≥1 s round-trip
(the boundary mesh fetch) is pending essentially always. The dataset panel proves the converse: its
slow-lane 5 s feeder with fast round-trips leaves promotion gaps, and its tile-render callback fired 6×/118 s
(census in `dstats`), tiles populating 0/0/0/N-A → 800/2/2/Balanced at t+40 s of a fresh session, scatter
900×800 with both class traces, histograms with both feature annotations. This is what the unmet §7.1
saturation targets (pool full 61.4 %, backlog 23 > 12) mean behaviourally, and it adds a third lever to
Stage 2's scope: the boundaries chain specifically (slow its feeders, make them no-op-suppressing, or move
the render clientside) — interval gating alone cannot fix a panel whose gated-open lane self-blocks.

### The candidates panel: five rows proven live, and the panel is honest

With the run live, the panel tracked the server through the full cycle: badge `Inactive`→`Training` (and,
run 5, `Selecting Best`), phase `Idle`→`Training`, pool `0`→`40`, progress section `none`→`block` with
`351/400`, pool-info placeholder→Top-2-candidates table — the exact dispatches that measured **0** across
220 fills before the fix. The UI lags the server 10-20 s under run load in both directions (F-CANOPY-004,
reduced but present): at one sample the server was mid-candidate (`candidate_epoch 151/400`) while the UI
still read Idle; 17 s later the UI read `Training 351/400` after the server had already returned to output.

### Two new findings (ledger entries above)

- **F-CANOPY-035 (P1)**: the candidate loss plot reads `epochs`/`losses`/`phases` — keys `/api/state` never
  provides in any lane (`TrainingState._STATE_FIELDS`); the data exists at `/v1/metrics/history` (4,106
  candidate-phase entries in one run). The panel is wired to the wrong producer; M-CANDIDATES-07 FAIL
  re-attributed.
- **F-CANOPY-036 (P2)**: pool history never accumulates — `update_pool_history` races its own feeder's ~1 s
  repoll and never executes with a short-lived active-pool state (request-capture proof: zero executions in
  100 s after an injected `Training` write on a calm page, while the same capture shows it executing on
  ordinary fills with the already-overwritten `Inactive` value). Zero cards across 5 runs / ~20 candidate
  phases. M-CANDIDATES-09 FAIL, -10/-11 BLOCKED, re-attributed.

### F-CANOPY-005 corroboration (two clean on-demand reproductions)

Runs 2 and 3 both started with: WS `start` command timing out client-side (`WS rejected: Command timeout
(no command_response for <uuid>)`), REST fallback firing, and the fallback hitting **409 Conflict** because
the WS command had actually landed server-side. The run starts anyway; the console carries a spurious 409
each time. This is the send-promise race, reproducible by clicking Start under load.

### Instrument record (what it took to observe this)

Three observation designs stalled identically once training began — DOM sampling at 3 s, 700 ms sampling
with a Redux subscribe, and a single cheap 1 Hz tick — each session's `page.evaluate` starving for minutes
(one renderer: 8m33s CPU over an 8.5-min session, pinned from attach; headless chromium under swiftshader,
so a GPU browser bears the plotly load far more cheaply — but the *server-completion fan-out to hidden
panels* it was rendering is real and is Stage 2's no-op-write lever). What worked: (1) an **in-page
observer** installed while calm (500 ms sampler + self-driving click test, harvested with one patient
evaluate after run end — run 5's sampler stayed healthy: 8 gaps > 2 s, worst 2.8 s); (2) **request-side
censuses** — every dash POST body names its output, so feeder-vs-render activity is countable without
touching the page, and identical-data rewrites are visible where a value-change subscribe is blind (that
blindness cost one wrong inference mid-session: "2 fills in 40 s" was actually ~1/s of identical rewrites);
(3) **short single-purpose sessions**. Also: each service restart resumed the SAME network (units
10→11→12→13 across runs 2-4) with runs shrinking to ~35 s; a cascor-leg restart
(`e2e_cascor_leg_restart.bash`) restored a fresh network and full-length runs. The dead-click test for
-10/-11 is ready in the driver (`cardsprobe`) for the moment F-CANOPY-036 is fixed.

### Status effects

F-CANOPY-027 stays **OPEN** — §12.5's refusal to mark it fixed is now *confirmed* rather than precautionary:
Stage 1+3 closed the candidates and dataset lanes; the boundaries lane needs Stage 2 (with the third lever
above). F-CANOPY-004 stays OPEN (lag observed 10-20 s + 20-40 s fresh-session population latency).
F-CANOPY-013 re-tagged P2 (was out-of-vocabulary "P3", which the triage script surfaced as `?`). Matrix
coverage unchanged at 298/298; verdict deltas this session: M-DATASET-13/-15/-16 FAIL→PASS,
M-CANDIDATES-09 BLOCKED→FAIL, M-BOUNDARIES-02 BLOCKED→FAIL, five candidates rows PASS→PASS(re-validated),
M-BOUNDARIES-01 rider narrowed, M-BOUNDARIES-04 FAIL sharpened, -10/-11/-03 BLOCKED re-attributed.

---

## Phase 2 — Stage 2 shipped (2026-08-24): the global lane consolidated, the boundaries render un-blocked, F-CANOPY-027 CLOSED

**Outcome up front: canopy#511 (`60f9737`, squash of the single waived commit; tree `a8be88ca` — identical
to the pre-merge build every branch measurement ran against) shipped all three §13 levers, and the four
M-BOUNDARIES rows re-drove to `PASS (re-validated @ 60f9737)` under run `20260824T192748Z`. F-CANOPY-027
is FIXED** (closure block in its ledger entry); its residual red rows belong to F-CANOPY-035/-036.

### What shipped

Design §13's per-call-site table, exactly: **lever 1** — `update_unified_status_bar` absorbed
`training-status-store`'s dedicated `/api/status` poller (suppressed on `{is_running, phase}` no-change),
and a new `update_system_panels` replaced four slow-lane callbacks (network-info + details + stream-health
+ pending-banner; one shared `/api/status` fetch — the banner's was the dashboard's FOURTH poller of that
endpoint). Global perpetual pollers 10 → 6; worst-case concurrency 13 → 9 vs the cap of 12. **Lever 2** —
no-op-write suppression on the swap-events poller (whose every 5 s rewrite had re-rendered three panels and
re-fetched the whole snapshot list), the metrics REST poll (identical history at 1 Hz into 4+ consumers
incl. the 8-output topology renderer), and both boundary feeders. **Lever 3** — `tabpoll-boundaries`
FAST → SLOW plus those feeder suppressions; tab activation and ↻ Refresh keep their immediate-fetch Inputs.
12 new pinning tests (`test_stage2_global_lane.py`, all failing on the parent) + the contract tests of the
merged-away callbacks moved to the new shape. One extract-method and one renamed test needed
`Allow-Symbol-Loss` waivers (in the single commit; post-merge main verification green).

### Measurements (§7.1 protocol, `e2e_f027_slots.py`, 60 s on the Candidate Metrics tab)

| state | pool full | backlog max | completions/60 s |
|---|---|---|---|
| baseline (pre-#507) | 83.6 % | 36 (held) | 224 |
| after #507+#509 | 61.4 % | 23 (held) | 449 |
| **Stage 2, idle** | **25.5 %** | 25 → drains to 0 | **778** |
| **Stage 2, during live training** | **35.3 %** | 24 → drains to 0 | 627 |

The starving-in-`prioritized` list (waited, never picked) is **empty** in both windows — the quantity that
WAS this defect. §7.1's <20 % pool-full reads as a near-miss at idle and the <12 backlog as transient-only;
both targets assumed held-backlog semantics that no longer occur.

### The boundaries rows (run `20260824T192748Z`, merged main)

-04: status → `Displaying decision boundary` at t+16 s DURING a run and t+10 s post-run, full
contour+scatter figure. -01: slider 100→125 in 1.3 s, the next feeder POSTs carry `resolution=125`, and
the figure re-rendered to the larger 125-mesh (sig 166696 → 218804) — also answering the prior run's open
question: the slider's Redux commit lands. -02: a plot-render POST with
`decision-boundary-show-confidence.value` in `changedPropIds` ~9 s after one toggle click — direct
causation. -03: a feeder POST with `decision-boundary-refresh-btn.n_clicks` in `changedPropIds`, landing
OFF the 5 s ambient grid — the twice-BLOCKED attribution, closed by the Stage-2 cadence itself.

### Instrument laws (hard-won this session; supersede "sparse evaluates" advice)

1. **On the boundaries tab, only attach-window evaluates are reliable** (≤ ~25 s of page life; 100 %
   service across nine sessions). Rapid polls, sparse 6 s-spaced reads, and even single late harvests all
   starved for minutes-to-forever, run state irrelevant. Structure probes as **one gesture per session**:
   open tab → one click → all analysis python-side from the request capture.
2. **`changedPropIds` is the causal channel** — every dash POST names the props that triggered it — but it
   serializes AFTER the callback's inputs, so the arc's shared 4000-char body slice never contains it for
   big-store callbacks; register a full-body `page.on("request")` handler.
3. **A value-change subscribe is blind to identical rewrites** (it under-read the boundary feeder as
   "2 fills/40 s" when it was ~1/s), and the boundary-data body filter also catches the replay co-writer's
   requests during live runs — count writers by `changedPropIds`, not by output id alone.
4. **Long browser probes must be launched DETACHED** (`nohup setsid`) — the session task lease kills
   backgrounded probes mid-harvest (two were lost to it here; the known ~3600 s bg-worker-lease class).

### Status effects

F-CANOPY-027 **FIXED** (canopy#507+#509+#511) — ledger now 40 findings / 10 fixed / 30 open
(3 P0 · 2 P0/P1 · 11 P1 · 12 P2 · 2 LEDGER). F-CANOPY-004 OPEN with materially better numbers.
Matrix: M-BOUNDARIES-01..04 re-scored; coverage 298/298, 0 unfilled. `CURRENT_RUN_ID` →
`20260824T192748Z`. The driver gained the measurement/attribution steps (`bprobe`/`bfinal*`/`bcausal`/
`btoggle`/`brefresh`) and the earlier session's observer steps; the F-CANOPY-036 dead-click test
(`cardsprobe`) stays ready for that finding's fix.

---

## Phase 2 — two more closures (2026-08-24): F-CANOPY-006 (P0) and F-CANOPY-025 (P1)

**Outcome up front: the topology graph works in the live lane, and the Live Dataset Switch opens — a P0
and a P1 closed in one session, both children of the same promotion-race family §12.6 named.** Ledger:
40 findings / **12 fixed / 28 open** (2 P0 · 2 P0/P1 · 10 P1 · 12 P2 · 2 LEDGER). Run `20260825T041134Z`.

### F-CANOPY-006 — closed by verification, no new code

The Stage 1+2+3 series had already fixed it: post-#511 probes on the merged content showed the topology
panel alive in BOTH lanes — **271 traces during an active run with counts tracking growth in real time**
(the DOM was a step *ahead* of the status probe), 209 traces / live counts at idle, renderer executing
4-5×/30 s. The 2026-08-20 entry's suspect ("the 12-Input rebuild perpetually re-queued behind the 1 s
interval") was the correct mechanism all along. Two sub-claims corrected: the depth slider's `max` does
seed (observed 11/13), and `value=0` is the designed no-filter arm — the "0 of N" label is a residual
cosmetic, not a defect. M-TOPOLOGY-01..18 / W4 / W1-12..14 are unblocked and await their re-drive segment.

### F-CANOPY-025 — canopy#514 (`5f2e905`), and the root cause was TWO defects

(1) The standalone gate lost the promotion race against its own feeder's in-flight claim on
`training-status-store` — fired at idle mount, zero times across 80 s of training; fixed by computing the
gate inside `update_unified_status_bar` (the Stage-2 consolidation pattern, tuple 10 → 11). (2) The mount
reconciliation's unchanged toggle write fired the toggle handler, which POSTed the mount-time flag back to
cascor on **every page load** — reverting operator changes (observed live within seconds); fixed with
unchanged-write suppression + an echo guard. Verified end-to-end on the merged content: the allow arm's
first-ever observation (`disabled:false` at t+12 s mid-run), the deny arm re-engaging at run end, the flag
surviving page attaches, and the enabled button opening the Live Switch modal with its full dataset
summary. Matrix: C2.7-10 and C2.10-02 → `PASS (re-validated @ 5f2e905)`; C2.10-03 (confirm/swap) remains
for W7. Operational note: the flag is cascor-process state and resets on a cascor restart (boot behaviour).

### Instrument additions

`e2e_f027_redrive.py` gained `f025` / `f025idle` / `f006` steps (API-set preconditions, attach-window
reads, request-side gate censuses) — the idle-vs-run gate census is the two-point probe that sealed the
promotion-race mechanism in one stack session.

---

## Phase 2 — F-CANOPY-002 closed (2026-08-24): the WS metrics fast path lives

**canopy#515 (`04f06ff`)** implemented the ledger's own fix direction — a per-type handler LIST with
fan-out dispatch (copy-iteration, error isolation inside the loop, identity `off()`), zero caller changes
— and the live verification (run `20260825T044659Z`) read the exact inverse of the defect's signature:
`_juniperWsDrain.metricsReceived: true` with the last metrics frame **47 ms** old mid-run (pre-fix, "no
metrics frame has EVER arrived"), the drain buffer filling, and the `allow_duplicate` WS append callback
executing 13×/45 s with `ws-metrics-buffer.data` in its `changedPropIds`. M-METRICS-31/-32 →
`PASS (re-validated @ 04f06ff)`. Pinned by `test_ws_handler_fanout.py` (the JS-source idiom). Ledger:
**40 findings / 13 fixed / 27 open — one P0 left** (F-CANOPY-005, the WS send-promise race; F-CANOPY-004
and F-CANOPY-008 hold the P0/P1 bucket). The `f002` driver step records the probe.

## Phase 2 — F-CANOPY-031 closed (2026-08-25): the snapshots panel scales against the no-deletion corpus; the last P0's fix lands

**canopy#517 (`9dcbb77a`)** paged the snapshot list — `limit`/`offset` on `GET /api/v1/snapshots` with an
always-reported pre-slice `total` (legacy full list when `limit` is omitted; demo branch identical), the panel
fetching only the newest 200 with the create-path's `+3` timeout headroom, and an honest
**"Showing newest N of TOTAL snapshot(s)"** status line. The defect was TWO stacked mechanisms: the panel's
bare 2 s timeout lost every fetch to the ~4.9 s unbounded scan+serialize, and 27,903 `html.Tr`s (five
pattern-matching ids each) could never have rendered anyway. Live against the real 28,016-file corpus
(run `20260825T101752Z`, canopy leg `:8051`): **200 rows in seconds**, `"Showing newest 200 of 28016
snapshot(s)"`, `data-snapshot-id` on all 200 (the "attrs on zero elements" sub-claim was zero *rows*), and
the FULL M-SNAPSHOTS-19 chain — right-click → context menu → Restore → the **Confirm Snapshot Operation**
modal for that exact snapshot, `context-menu-trigger` write captured on the wire. Matrix:
M-SNAPSHOTS-19 → `PASS (re-validated @ 9dcbb77)`; coverage 298/298, 0 unfilled. `CURRENT_RUN_ID` →
`20260825T101752Z`. Rider: the probes ran on the branch working tree committed as `5560cb19`; the squash
tree differs from it only by #516's four memory-budget files, so every file the fix touched is identical in
merged main. Two intermediate probes read the welcome modal's container through a generic modal selector
(an instrument miss, corrected by targeting the confirm modal's own element); the probe scripts were left in
`/tmp` and are gone — the logs survive, and an `f031` driver step is owed at the next stack window.

**canopy#518 (`d275ce2`) — the F-CANOPY-005 fix — was merged by the owner at 21:09Z** (after a branch
update; all checks green): a 250 ms one-shot grace re-arm on the send-promise timeout, and a
transport-only (`err.transport`) gate on the Phase-D REST fallback so business rejections surface as the
danger alert instead of a re-issued command. Its **live verification is queued behind the T6 re-baseline
GPU window** (a cross-session hold: no stack bring-ups, training runs or browser probes until that session
announces completion), so the entry stays OPEN with a fix-merged rider. Both fix worktrees and branches are
cleaned up; the primary canopy checkout is at `d275ce2`.

Ledger: **40 findings / 14 fixed / 26 open** (1 P0 · 2 P0/P1 · 9 P1 · 12 P2 · 2 LEDGER). The one P0 is
F-CANOPY-005 with its fix already in main; F-CANOPY-004 and -008 hold the P0/P1 bucket.

## Phase 2 — the P1 fix wave (2026-08-25/26): eight canopy fix PRs merged, two ledger closures by verification, all under the T6 GPU hold

**Posture.** The T6 re-baseline session held the exclusive GPU window for the whole session (successor
session `t6 rebaseline`, handoff ml#1371; zero cells run as of 23:20Z on 08-25; window re-planned to
~05:10–07:45 local on 08-26), so nothing here touched the isolated trio or a browser: every fix is
CPU/CI work — a fix plus a failing-on-parent regression test, canopy's pre-commit hooks, the
sequence-safety symbol-loss screen, a signed PR via `util/open_signed_pr.py`, a REST squash on green
required checks under the plan's merge policy, and main-verify green after each merge. Every fixed
finding therefore stays **OPEN with a fix-merged rider** until the post-T6 live re-drive, the discipline
F-CANOPY-005 set. **Correction (adversarial validation, rulesets API): protection IS strict on both repos**
(`strict_required_status_checks_policy: true`; canopy ruleset `14249530`, ml `13805432`) with an Admin
bypass (`bypass_mode: always`). The REST squash of a green-but-`BEHIND` PR therefore merged on the owner's
bypass — rule-suites recorded `result=bypass` for canopy `29a8c41e`, `9c381604`, `f20602cb`, `141324fa`,
`27a4bb1d`, `ef495cf3` and ml `aaf7c751` (`ce819775`, `07e9a061`, `74c5fce5` were `pass`). No required
check ran on those merged trees; the post-merge `main-verify` run, green for every one of them, is the
evidence they are sound. From here on: update-branch → green on the new head → merge, no bypass.

**Merged (canopy, in merge order):**

- **F-CANOPY-008 → canopy#519 `ce819775`.** Every CSRF reject arm on `/ws/control` funnels through one
  teardown that calls `websocket_manager.disconnect()` — the full rollback, since `connect()` had already
  registered the socket (the deferred registration/gauge-leak inference is confirmed by code). The
  regression test reproduces the live signature on the parent: `[1008 ×5, 1013]`.
- **F-CANOPY-009 + -010 → canopy#520 `29a8c41e`.** `dash.no_update` at all eight early-outs; the
  `View Details` button gets `n_clicks=0` like its siblings. 13 of 14 new tests fail on the parent.
- **F-CANOPY-014 → canopy#521 `07e9a061`.** The replay panel adopts the sibling panels' port-based base-URL
  fallback; every control action posts to an absolute URL (7 of 8 tests fail on the parent).
- **F-CANOPY-003 → canopy#523 `9c381604`.** `reportSuccess` in the Phase-D JS on WS success and REST 2xx
  writes the ack and clears the button directly; the sweep handler honours a fresh success ack
  (`success` + `command` + a `ts` not older than the click). 4 of 12 tests fail on the parent.
- **F-CANOPY-035 → canopy#524 `f20602cb`.** The candidate loss plot consumes the shared
  `metrics-panel-metrics-store` (no new poller — the F-CANOPY-027 rule) through
  `_candidate_series_from_history`; the module does not import on the parent.
- **F-CANOPY-007 → canopy#525 `141324fa`.** Snapshots are listed and resolved through the backend that
  created them (`list_snapshots` / `get_snapshot` adapter proxies; cascor is the authority in service mode,
  the local directory the fallback; the F-031 `limit`/`offset`/`total` contract holds on either source).
  The split-filesystem test reproduces the live empty list on the parent.
- **OBS-1 → canopy#526 `27a4bb1d`.** The About panel's own hardcoded `APP_VERSION = "2.2.0"` literal is
  gone; `canopy_constants.resolve_app_version()` is the one source (installed metadata, `pyproject.toml`
  fallback pinned by test).
- **F-CANOPY-011 + D-0 → canopy#522 `ef495cf3`.** The editor reads canopy's flat `fsm_status` and fetches
  `/api/topology`; 17 contract tests pin the REAL routes through `main.app` with a demo backend installed
  (7 fail on the parent).
- **Phase-4 truth-up → canopy#527 (in CI at the time of writing).** D-2: `nn-init-output-weights-dropdown`
  joins the 27-input Apply dirty set (its handler parameter is appended after `applied`, so positional
  callers are unaffected); D-5: the Phase-D registration comment states the real flag default; `main.py`
  takes `APP_VERSION` from `canopy_constants`.

**Closed by verification, no new code:** **F-ML-001** — juniper-ml#1133 (`b7f7ec20`, 2026-08-17) had
already shipped the prescribed pidfile exclusion (`JUNIPER_E2E_RUN_DIR` protected; the isolated stack's
`${RUN_DIR}/juniper-*.pid` files are its P1 key); its four protection tests are green.
**F-CASCOR-001** is filed upstream as juniper-cascor#590 with re-derived anchors. **F-E2E-004/-005**
(the LEDGER harness pair) are FIXED by juniper-ml#1385 `aaf7c751` (`JUNIPER_CANOPY_SERVER__PORT` exported
into canopy's process; the three `assertIn(..., env_text)` sites compare per-key line lists).

**Docs truth-up (Phase 4) started:** the two W14 matrix lines now name `stream_health.overall`'s real
recovery value `"healthy"`; D-1's stale "exactly two writers" docstring no longer exists in the source
(verified — no change needed); D-3 is already recorded correctly in the matrix (the source-doc fix belongs
to the canopy USER_MANUAL truth-up); the depth-label "0 of N" cosmetic reads as already fixed in code
(`_apply_hierarchy_filter` returns `"all"` for the unfiltered case) — verify live.

**Owner decisions requested (carried in the handoff):** the F-CANOPY-004 latency disposition — accept and
document a freshness contract now (post-Stage-2: 3–16 s interaction renders, 20–40 s fresh-session
population) versus open the JR-CAN-PERF-004 WS-migration workstream; recommendation: the contract now, the
migration as a planned workstream — and the open-P2 set (§6.3).

**Instrument/tooling notes.** The worktree-isolation hook rejects heredocs containing escaped apostrophes
(`\'`), `for` loops and `env -C`; Read+Edit or plain single commands are the reliable path. A bare
`TestClient(app)` never runs the lifespan, so route tests that need a backend must install one
(`monkeypatch.setattr(main, "backend", DemoBackend(DemoMode(update_interval=1.0)))`). A fresh canopy
worktree lacks the gitignored runtime `logs/` dir, which `integration/test_setup.py::test_directories`
requires — create it before a full-suite run. `wait_for_checks.py` returns immediately after an
update-branch if the OLD head's rollup is still the one it sees — re-check the PR after it fires.

Ledger at the end of the session: **40 findings / 17 fixed / 23 open** (1 P0 · 2 P0/P1 · 8 P1 · 12 P2 ·
0 LEDGER). Every P1 in the canopy tail now has its fix in main; the counts move only when the post-T6
re-drive verifies them live. Matrix coverage unchanged (298/298, 0 unfilled); no live rows were driven,
so `CURRENT_RUN_ID` stays `20260825T101752Z`.

## Phase 2 — the post-T6 live re-drive (2026-08-26): the P1 fix wave verified live; F-CANOPY-004 gates the render, not the fix

The T6 GPU hold released at 12:30 local (campaign COMPLETED 03:58, 23/23 cells, cascor pin `67d7ea3`
held; the 8.5 h gap was the T6 session's late wake, nothing ran in it). The isolated trio came up clean
(`e2e_isolated_stack.bash --up`; data 8101 / cascor 8202 / canopy 8051 / recurrence 8212; leg pids
recorded; `/v1/health` `demo_mode:false`, `juniper_data_available:true`). Run id **`20260826T174225Z`**.
The driver is `util/ad-hoc/e2e_p1wave_redrive.py` (+ the `e2e_fcandidate_model_select_probe.py` unit
probe), both archived.

**The headline: every P1 fix driven this session verifies at the mechanism/data-path level; the ones
whose acceptance is a *live render during a run* are gated by the still-open F-CANOPY-004 callback
congestion, which starves the render for tens of seconds before it catches up.** So the re-drive
confirms the fixes are correct and, for the render-latency-sensitive ones, re-confirms F-CANOPY-004 as
the dominant open issue — the freshness-contract owner decision.

### Verified live (PASS)

- **F-CANOPY-003 (C2.5-09) — PASS.** Six control cycles (pause/resume/pause/resume/stop/reset): every
  button re-enabled in **0.82–3.59 s** (was 30 s–minutes). The success ack now releases the button
  directly; the sweep is only the backstop.
- **F-CANOPY-005 (W2 step 2 / C2.5-10) — PASS.** Across all six cycles: **zero** `/api/train/*` POSTs
  from the browser and **zero** 409s — the WS-success-then-REST-double-fire is gone. The reachable
  business rejection (pause-while-paused) surfaced the danger alert *"Pause failed. Training cannot be
  paused in the current state"* at +7.9 s via `training-control-action` with **no** HTTP re-issue
  (console: `[Phase D] WS business rejection (pause)`). The pause-while-STOPPED arm is N-A — the pause
  button is correctly disabled when stopped, so that rejection is unreachable through the UI (correct,
  not the defect).
- **F-CANOPY-009 (W5 step 4) — PASS.** `View Details` filled at +12.5 s and **stayed filled** through
  the full 32 s watch (two 10 s refresh ticks) — the table-refresh wipe is gone.
- **F-CANOPY-010 (W5 step 5) — PASS (core).** The restore confirm modal **opened and survived the full
  65.8 s watch** with its body intact (was self-closing at ~3.6 s). Cancel-close is a secondary W5-step-6
  assertion still to re-confirm (one read showed the dialog lingering after the cancel click — likely a
  fade-timing artifact; no request fired).
- **F-CANOPY-011 + D-0 (W5-07..15) — PASS (via the quiescent re-read).** After a UI restore the FSM went
  `INVESTIGATING`; the Network Editor's active surface rendered with badge **`FSM: Investigating`** (the
  flat `fsm_status` read — F-011), the topology readout **`Inputs: 2 Outputs: 2 Hidden units: 9`** (the
  `/api/topology` fetch — D-0; was a permanent 404 → *"No topology loaded."*), and the remove dropdown
  **populated** (10 options, was empty under D-0). The restore and a UI **remove** both operated live
  (10 → 9 hidden units; `/api/topology` = 2/9/2, 13 nodes, 76 connections). **The render lagged ~65 s
  during the congested restore+ops window** (the editor read stale `FSM: Completed` / *"No topology
  loaded."* / 0-counts until it caught up) — F-CANOPY-004, not an F-011 regression; the quiescent re-read
  (`--step f011check`) is clean.
- **OBS-1 — PASS.** About "App Version" == `/v1/health` `version` (both `0.4.0` on this leg, from the
  same installed-metadata source; the `0.4.0`-vs-pyproject-`0.6.0` gap is the separate nested-egg-info
  shadow already pinned by `test_dockerignore_egg_info.py`, and is exactly what the D-11 code truth-up
  below single-sources).
- **The depth-label "0 of N" cosmetic — PASS.** `#network-visualizer-depth-label` reads **`all`** for
  the unfiltered case (code already returned `"all"`; confirmed live).

### F-CANOPY-035 (M-CANDIDATES-07) — INCONCLUSIVE, and why it is NOT a regression

The candidate loss plot rendered **empty** both during and after the run — but this is the F-004
store-population problem, not an F-035 defect, and the distinction was pinned mechanically:

- `/api/metrics/history` holds **3216 candidate-phase entries** in exactly the `{epoch, metrics.loss,
  phase}` shape `_candidate_series_from_history` consumes; a direct simulation of the adapter kept
  **99/99** entries from the last-100 window. The fix's data path is correct.
- But the shared `metrics-panel-metrics-store` is **globally empty** (`len 0`) on **both** the Training
  Metrics and Candidate Metrics tabs post-run, and the **main** metrics loss plot is *also* empty — the
  store simply never populated from the available history (the liveness-gated fast-interval poll was
  starved/demoted throughout the congested run and stays empty after; F-CANOPY-004 territory).
- So M-CANDIDATES-07's live render can't be exercised while the upstream store is empty. F-CANOPY-035's
  fix stands on its 15-test unit suite + the adapter simulation; the live render is blocked on the same
  store-population/staleness that F-CANOPY-004 tracks. **Verdict: INCONCLUSIVE (live), not FAIL** — the
  arc's "a first-pass anomaly is more often the instrument" rule, applied.

- **F-CANOPY-014 (W5-19/26) — PASS (buttons).** The replay session started, the tab switched to
  `Replay`, and the three **button** controls all POSTed to **absolute** URLs with success statuses —
  play → `✓ Seeked`, pause → `✓ Playing`, stop → `✓ Stopped` — with **zero** `No scheme supplied`
  errors (the empty-base-URL bug that made the entire replay surface dead). The three **slider**
  controls (speed/seek/range) were instrument-limited (the rc-slider handle drag did not land in the
  harness — `driven=False`, not errored) and share the same `dispatch_control` URL-building path, so
  the fix covers them; the slider rows W5-21..23 still need a re-drive. **Correction (2026-08-26): the
  "needs an rc-slider drag idiom" diagnosis carried in the 08-26 handoff is WRONG.** A DOM probe of the live
  app (`e2e_seg17_topology_driver.py --step probe`) shows this canopy is on **Dash 3.x**, whose sliders are
  **Radix** (`.dash-slider-root`, `.dash-slider-track`, a `[role=slider]` thumb) beside an
  `input[type=number]` — **there is no `.rc-slider-handle` in the tree at all**. That is why the arc's
  `drag_handle` reported `driven=False` without erroring: it was querying a selector this Dash version never
  renders, so it returned "no handle" rather than failing a drag. The working idiom is the companion number
  input driven with the React native-value-setter, with keyboard arrows on the Radix thumb as a fallback —
  both implemented and effect-verified in `e2e_seg17_topology_driver.py`'s `set_slider`.
  **Re-driven with the corrected idiom (2026-08-26, run `20260826T215010Z`):** `drag_handle` in
  `e2e_p1wave_redrive.py` was rewritten to be Radix-aware (keyboard-on-focused-thumb first — the only idiom
  that addresses one handle of a two-handle range slider — then the number input, then a real pointer drag,
  each scored by re-reading `aria-valuenow`). **W5-22 (speed) now DRIVES**: `driven=True`, status
  `✓ Speed updated`. **W5-21 (scrubber/seek) and W5-23 (range) still do not — but for a PRECONDITION reason,
  not an idiom one.** The replay session opened on a **V1 (metrics only)** snapshot whose history is empty:
  `epoch-readout` read `0 / 0` and `range-readout` read `[0, 0]` for the whole session, so both sliders have
  `min == max == 0` and there is nowhere to move. The rewritten helper correctly returns `False` rather than
  reporting a phantom drive. **To close W5-21/-23 a re-driver needs a V2 (`V2 ✓ weights`) snapshot with a
  non-empty sample history** — not a different drag idiom.
  *Side observation (no new finding):* the replay status block lags one action behind — `play` read
  `✓ Seeked`, `pause` read `✓ Playing`, `speed` read `✓ Paused` — i.e. each control's own status surfaces
  only after the *next* control is driven. Consistent with the F-CANOPY-004 interaction-render envelope now
  accepted above; recorded so a re-driver does not read the lag as a wrong-status defect.
- **F-CANOPY-008 — PASS.** Restarting the canopy leg with a dashboard tab open produced exactly **5**
  `ws_csrf_rejected` events (the stale token) and **`Per-IP limit reached` = 0** — the CSRF reject
  paths now release the reserved connection slot, so five rejections no longer lock the control plane
  out. After a reload the badge read `WS: Connected` and the reset button re-enabled in 1.28 s with no
  `/api/train` POST — the control plane recovered.
- **F-CANOPY-007 — PASS.** With the canopy leg restarted against an **empty** local snapshot dir (0
  `.h5`), the Snapshots table listed **"newest 200 of 28028"** from cascor (not the empty local dir —
  the split-filesystem silent-empty bug), a create round-trip landed
  (`snapshot_20260826T183019Z`), and `/api/v1/snapshots` then reported **28029**, exactly matching
  cascor's **28029** while the local dir stayed empty (`local_h5=[]`). Snapshots are listed through the
  backend that created them.

### Still owed

The `f031` driver step is still owed at a stack window. F-CANOPY-014's three slider rows (W5-21..23)
need an rc-slider drag idiom. The remaining §6.3 re-drives that never depended on a fix
(M-TOPOLOGY-01..18 + W4 + W1-12..14, C2.10-03, the M-SNAPSHOTS live-swap rows, M-DATASET-14 theme flip)
are unblocked by the F-CANOPY-006/-027 closures and can run on this same bring-up while it is warm.

### Phase-4 truth-up shipped alongside

- **Docs (§11) → canopy#528** (`9b88ba10`, main-verify green): D-1..D-7 repaired, the ten undocumented
  tabs documented, the real `JUNIPER_CANOPY_` configuration surface (with the dead `CASCOR_SERVER_*` /
  `CASCOR_DEBUG` names called out), and the demo-doc `JuniperPython`→`JuniperCanopy1` / "C++ backend"→
  juniper-cascor-service corrections. Four further drifts found while grounding (D-9 dead demo env vars +
  legacy YAML layer; D-10 `demo_update_interval` declared-but-not-applied; D-11 stale manual version;
  D-12 production-mode → service-mode) are repaired there too.
- **Code (§7.5) → canopy#530** (open): **D-8** — `_try_create_recurrence_backend`'s docstring claimed a
  UI gate on an unconfigured recurrence model that does not exist; the probe reproduced
  `POST /api/model/select {"nn_model":"recurrence"}` → `200 {backend:demo, status:live, swapped:false}`
  with no service URL, so the docstring now describes the real (ungated) behaviour and defers the gating
  question to the ledger. **D-11** — both package `__version__` literals (`"0.5.0"` vs pyproject `0.6.0`)
  now resolve from `importlib.metadata`, the OBS-1 single source.

Owner decisions unchanged and now **sharper**: F-CANOPY-004's freshness contract is the gate on a clean
live render for F-035, F-011 and the rest — this re-drive is the strongest evidence yet that the fixes
are correct *and* that F-004 is what stands between them and a snappy live UI.

**Ledger at the end of this session: 40 findings / 25 fixed / 15 open** (0 P0 · 1 P0/P1 [F-CANOPY-004] · 2 P1 [F-CANOPY-035 F-004-gated INCONCLUSIVE, F-CASCOR-001 upstream juniper-cascor#590] · 12 P2 · 0 LEDGER). The eight P0/P1 fixes verified this session (F-CANOPY-003/-005/-007/-008/-009/-010/-011+D-0/-014) all flip to FIXED; F-CANOPY-004 is now the sole open P0/P1 and the gate on every remaining live render. Run id `20260826T174225Z`; `CURRENT_RUN_ID` bumped.

## Phase 2 — the §6.3 topology re-drive (2026-08-26, later session): F-CANOPY-004 ACCEPTED, F-CANOPY-037 found

Owner decisions taken at the top of this session (all four): F-CANOPY-004 → **accept the freshness contract
now AND schedule the WS migration** (JR-CAN-PERF-004); run the **full** fix-independent re-drive block on a
live bring-up; fix **all 11** canopy P2s (F-CASCOR-002 upstream); and **enable a live 3-D posture** for
M-DATASET-17..26 rather than settling for the DEMO lane.

### Stack

Fresh isolated trio, brought up clean and health-gated: data `8101`, cascor `8202`, canopy `8051`
(`JUNIPER_CANOPY_DEMO_MODE=0`, service mode). The deploy containers on 8050/8201/8211 were left untouched —
`--with-recurrence` was deliberately NOT used because 8211 is the deploy stack's recurrence port.
**Pin moved, deliberately and recorded:** cascor primary is no longer the handoff's `67d7ea3` but `c6cd2f0`
— a peer advanced it while the T6 freeze was lifted. The delta is exactly two commits, `3697101` (forkserver
trainer preload, cascor#592) and `c6cd2f0` (a CI-only memory-budget gate); neither touches an API or UI
contract, so the re-drive ran against current main. Canopy `9f6fac9`, juniper-data `e0b738e`.

Two full training runs were driven cold-start through the UI's WS control path: run A grew **0 → 10** hidden
units and COMPLETED; run B resumed the same network to **11** and stopped `early_stopped`.

### The headline: the topology graph is starved ABSENT, and it is a new finding

**F-CANOPY-037** (new, P0/P1, OPEN — full block in the ledger above). The rebuild is chained off
`metrics-panel-metrics-store`, which rewrites **141,460 B of byte-identical data 0.57/s on a COMPLETED run**
(34 writes / 60 s, **33 identical**, 0 `no_update`), so `update_network_graph`'s Input is re-claimed faster
than its own 1.5–5 s server time and the callback is starved out entirely. Measured **2 renders in 11 live
sessions**. When it does render it is correct and fast: HTTP 200, **39,319 B, 206 traces**, stats bar
`2 / 10 / 2 / 89` exactly matching `GET /api/topology`, ~22 s after tab entry.

This was *nearly* mis-filed twice, in both directions, and the record matters more than the result:

- **First read — "F-006 has regressed."** Wrong. F-CANOPY-006 was "a correct server render is never applied
  client-side"; here the DOM *does* apply it whenever the callback runs. F-006 is genuinely fixed.
- **Second read — "the callback never fires."** Also wrong, and it was **my instrument, not the app**: the
  first `rebuildprobe` read `resp.request.post_data` inside the response handler, which silently yielded
  nothing, so it reported 0 rebuilds while a wire census counted **12 in 60 s**. Stashing each POST body on
  the *request* event and joining on the response fixed it. A probe that reports zero is not evidence until
  a second, independent instrument agrees.
- **Third read — "my polling is starving it."** Tested and refuted: a control that opened the tab and waited
  **90 s with zero `page.evaluate` calls** was equally empty.

Ruled out by measurement, each explicitly: tab not active (`[role=tab].active` read `Network Topology` every
time); server wrong (2/10/2/89 throughout); store empty (the depth slider's clientside max bumped 0 → 10,
which only a populated store can do); callback error (canopy log clean — only the benign pre-run
`No network created`); progressive in-process starvation (a **fresh canopy leg** was equally empty);
run-vs-idle posture (equally empty during an active run and post-run); the depth filter
(`_apply_hierarchy_filter` returns unfiltered for `depth <= 0`, so `value=0` is "all"); and driving the
callback's **own Inputs** (three `show-weights` off/on toggles, 112 s — no wake).

### F-CANOPY-004 — ACCEPTED under a documented contract

Per the owner decision, F-004 is now **ACCEPTED**, not open: the post-Stage-2 envelope (**≤ 16 s**
interaction renders, **≤ 40 s** fresh-session population, clientside immediate, during-run steady-state
best-effort) is written into the finding as canopy's freshness contract, and **JR-CAN-PERF-004** is scheduled
as the workstream that removes the polling architecture rather than tuning it. F-004 no longer gates Phase 3.

**The contract has an explicit scope limit, and F-037 is why.** It covers surfaces that render *late*. It
does not cover a surface that never renders at all. A row that never painted is F-037 and stays open — the
acceptance must not be used to close it.

`e2e_finding_triage.py` gained a third disposition (`ACCEPTED`) so the ledger can express "real, unrepaired,
owner-signed-off" without either overstating what shipped or holding an exit criterion red. Header token
`ACCEPTED` in the last 170 chars, same convention as `FIXED`.

### Instrument correction that invalidates a handoff diagnosis

**This canopy is on Dash 3.x**, and three of the arc's widget idioms were written for Dash 2:
`-layout-selector` is a native `<button class="dash-dropdown">` with its value in `#…-layout-selector-value`
(not react-select); `-display-mode` / `-view-mode` are `input[type=radio]`; `-depth-slider` is a **Radix**
slider (`.dash-slider-root` / `[role=slider]`) beside an `input[type=number]`. **There is no
`.rc-slider-handle` anywhere in the tree.** So the 08-26 handoff's "W5-21..23 need the native rc-slider drag
idiom" is wrong at the root: `drag_handle` returned `driven=False` because it queried a selector this Dash
version never renders. The working idiom is the companion number input via the React native-value-setter,
with keyboard arrows on the Radix thumb as fallback — both in `set_slider`, effect-verified.

### Matrix effect

No verdict moved. M-TOPOLOGY-01..18, W4-01..17 and W1-12..14 were already **BLOCKED** and stay so, with the
blocker **re-attributed from the closed F-CANOPY-006 to F-CANOPY-037** and the Dash-3 idioms recorded inline
at §3.3 so the next re-drive does not repeat the widget archaeology. Separately, the stale **D-0** text was
trued up in five places (the divergence block, the divergence table, M-NETWORK-EDITOR-05/-10/-11, and W5
steps 10/11/15 — step 15 still told a re-driver "the dropdown is empty, drive the `DELETE` directly", which
has been false since canopy#522). Coverage unchanged at **298 / 298, 0 unfilled**.

### New tooling

`util/ad-hoc/e2e_seg17_topology_driver.py` — steps `probe` (pins the real widget markup before any row is
scored), `topodiag`, `rebuildprobe` (request-side body capture joined on the response), `wirecensus` (every
dash POST by output), `quietread` (the zero-evaluate control), `storestorm` (the no-op-rewrite census that
proved the mechanism) and `topo` (the control-surface drive, which correctly refuses to score rows when the
graph never paints).

**Ledger at the end of this session: 41 findings / 25 fixed / 1 accepted / 15 open** (0 P0 · 1 P0/P1
[F-CANOPY-037] · 2 P1 [F-CANOPY-035, F-CASCOR-001 upstream juniper-cascor#590] · 12 P2 · 0 LEDGER).
F-CANOPY-004 moves out of the open set as ACCEPTED; F-CANOPY-037 takes its place as the sole open P0/P1 and
is now the gate on the topology row block.

### Still owed

The `f031` driver step; **W5-21 and W5-23 on a V2 snapshot with a non-empty history** (W5-22 now drives via
the corrected Radix idiom; the other two are blocked by an empty `0 / 0` V1 replay session, not by the
idiom); C2.10-03, M-SNAPSHOTS-20/-21 and
M-DATASET-14; the **all-11 P2 fix wave**; the **JR-CAN-PERF-004** plan document; and the **live 3-D posture**
workstream for M-DATASET-17..26 (`POST /api/dataset/generate` is demo-gated 400 and both `equities` /
`equities_seq` report `available:false` in the live lane). The topology block cannot be re-driven until
F-CANOPY-037 is fixed.

---

## Phase 4 — the P2 fix wave (2026-08-27): 8 of 11 addressed, 1 re-diagnosed, 2 deferred

Owner decision 3 ("fix all 11 canopy P2s"), executed as far as source work can take it. No stack was
brought up; every fix is grounded in the Phase 1–3 measurements plus source tracing.

> **STATUS CORRECTION (2026-08-29).** This section was written before the wave merged and said
> "**nothing here is merged**, so every entry above stays OPEN". That is now stale in two ways, and the
> staleness is load-bearing because it is why `e2e_finding_triage.py` still counts these as open P2s.
>
> - **All of the wave merged 2026-08-28**: canopy#532 (F-001/-013/-015/-034), #533 (F-018/-028),
>   #534 + cascor#594 (F-026 both halves), #535 (F-012). The table's F-CANOPY-036 row still reads
>   "deferred — —"; it shipped as **canopy#536** (server-side accumulation) on the owner's decision.
> - **The honest count is 9 of 11 FIXED**, not 8 and not 10: the eight above plus F-036, with
>   **F-CANOPY-032 NOT fixed** (contract pins only — its mechanism does not reproduce) and
>   **F-CANOPY-033 deferred**.
> - **Every one of those entries still needs its live row re-drive** before its header token changes,
>   which is why they remain OPEN in the triage. That is correct, but it is correct for a different
>   reason than this paragraph gave. The owed rows are listed at the end of this section.
>
> **F-CANOPY-036's owner-decision note is also now spent**: it read as an open choice between server-side
> accumulation and a clientside append. The owner chose **server-side**, and canopy#536 shipped it. The
> JR-CAN-PERF-004 plan still carries that as an open question in its §7 and its Phase 2 blocker —
> `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md` — and should be updated
> to record that Phase 2 is no longer gated on it.

### Disposition

| finding | PR | outcome |
|---|---|---|
| F-CANOPY-001 dark-mode glyph | canopy#532 | fixed — glyph derived from the store by the mount-capable callback |
| F-CANOPY-013 envelope nesting | canopy#532 | fixed — both call sites, incl. the latent DELETE instance |
| F-CANOPY-015 replay session nesting | canopy#532 | fixed — `_session_summary`, legacy shape tolerated |
| F-CANOPY-034 dead store | canopy#532 | fixed — store, handler and its 5 tests removed |
| F-CANOPY-018 apply toast | canopy#533 | fixed — **and re-diagnosed: 3 keys, not "two writers"** |
| F-CANOPY-028 pinned params | canopy#533 | fixed — **and re-diagnosed: the writer, not rehydration** |
| F-CANOPY-026 UTC offset | cascor#594 + canopy#534 | fixed both halves |
| F-CANOPY-012 output_weights 2-D | canopy#535 | fixed — unblocked by the D-0 route fix |
| F-CANOPY-032 worker alert | canopy#533 (pins only) | **NOT fixed — mechanism does not reproduce; re-diagnosed** |
| F-CANOPY-033 RESET storm | — | **deferred** — needs live redux tracing; no root cause in source |
| F-CANOPY-036 pool-history race | — | **deferred** — the entry states the fix is an owner design decision |

### What the wave changed about the findings themselves

Four entries carry corrections (annotated in place above). The pattern is worth naming, because it
recurred four times in one session and it is the same pattern F-CANOPY-037 exposed:

> **A finding's *symptom* held every time; its *mechanism* was wrong or incomplete four times.**

- **F-018** — "two writers" was a plausible reading of a real duplicate Output, but the tracker's clean
  path already `no_update`s. The actual driver was a three-key asymmetry between the dirty set and the
  apply payload, and **two of those three keys were found by a test, not by reading the finding.**
- **F-028** — the rehydration wiring the entry called broken is present and correct; the writer is the
  defect, which the entry's own final sentence had actually identified.
- **F-032** — the whole path is correct in source, and one of its two test arms should never have counted
  as a failure.
- **F-026** — correct as written, but the *same-class* audit found five more naive emissions the entry
  did not mention, two of them in a persisted snapshot format.

The operational lesson, consistent with `feedback_validate_handoff_prompts_independently`: **read the
call site before implementing the finding's own recommended fix.** F-CANOPY-012's recommendation ("drop
the Input" for F-037; here, the 2-D parse) and F-CANOPY-037's ("the rebuild does not use metrics data")
were both wrong in ways that would have deleted working behaviour.

### Deferred, with reasons

- **F-CANOPY-033** (`RESET_COMPONENT_STATE` at ~13/s into the Cassandra subtree). No source-level root
  cause was found and the entry's own evidence is a redux trace. This needs the live instrument
  (`e2e_f027_redux_actions.py`) re-run against post-Stage-3 main, not a guess.
- **F-CANOPY-036** (candidate pool history never accumulates). The entry states the fix is an **owner
  design decision** between server-side accumulation and a clientside `update_pool_history`. It also
  overlaps Phase 2 of the JR-CAN-PERF-004 plan, which must not run concurrently with it.

### Still owed (unchanged, plus)

Everything from Phase 3, plus: the **live re-drive of every row these eight fixes touch** once they
merge (C2.9-05, M-PARAMETERS-04/-05/-06, M-METRICS-03, M-WORKERS-02, C2.1-01/02 and the Network Editor
patch rows); **F-CANOPY-033's redux re-trace**; and **F-CANOPY-036's owner decision**.

### Owner decision 4 (the live 3-D posture) — unblocked by source diagnosis, no stack needed

M-DATASET-17..26 were recorded as blocked on two symptoms. Neither is a defect; both are now
explained, which turns this workstream from "blocked" into "has a recipe plus one design question".

**1. `equities` / `equities_seq` report `available:false` — a PROVISIONING gap, not a defect.**
Both generators' `is_available()` returns `EQUITIES_DEPS_AVAILABLE`
(`juniper-data/src/generators/equities/generator.py:59-65`), which is simply whether `pandas` and
`yfinance` import. They are the optional **`[equities]` extra** (`pyproject.toml:48-53`:
`yfinance>=0.2.40`, `pandas>=2.0.0`). The generator even carries the remedy as its own message:
`'The "equities" extra is required. Install with: pip install "juniper-data[equities]"'`. The E2E
lane's data leg is installed without it. **Recipe: install the isolated stack's data leg as
`juniper-data[equities]` and both generators become available.** Nothing in canopy or cascor changes.

**2. `POST /api/dataset/generate` returns 400 in the live lane — BY DESIGN, and permanently.**
`main.py:1423-1427` gates the route on `backend.backend_type != "demo"` and returns
`{"error": "Dataset generation only available in demo mode"}`. The E2E lane runs **service** mode, so
this route is *correctly* 400 there and no amount of provisioning changes that. **Any M-DATASET row
whose live-lane arm depends on `/api/dataset/generate` is asserting against a route that is
deliberately demo-only** — those rows need either a DEMO-lane arm or a different live path
(`/api/stage_dataset`, which is what the cold-swap flow actually uses, or the juniper-data service
directly).

**Open question for the owner:** should the live 3-D arm drive `/api/stage_dataset` (the path the
product actually uses in service mode), or should those rows be re-scoped to the demo lane? That is a
matrix-semantics decision, not an implementation one, and it should be made before the rows are
re-driven rather than discovered mid-drive.

---

## Phase 5 — the post-fix topology re-drive (2026-08-28, run `20260828T132533Z`)

The first live session of this arc since F-CANOPY-037's fix merged. Stack: a fresh isolated trio brought
up with `util/isolated_stack.bash --up`, data on 8101 / cascor 8202 / canopy 8051, service mode, cascor
`a709d52` and canopy `6b55399` (both merged mains). The deploy stack on 8050/8201/8211 was never touched.

A run was trained from the dashboard to completion: **10 hidden units, `fsm_status=COMPLETED`**, and
`GET /api/topology` = **`2 / 10 / 2 / 89`, 14 nodes** — byte-identical to the server truth F-CANOPY-037
was found against, which is what makes the before/after comparable at all.

### Headline: the fix works, and it did not unblock the rows

| | F-CANOPY-037 as found | this re-drive |
|---|---|---|
| rebuild POSTs | **zero** in 9 of 11 sessions | **10x / 60 s**, every session |
| topology-store writes | — | **12x / 60 s** (the 5 s tabpoll cadence) |
| rebuild response | 200 / 39,319 B / 206 traces (when it ran) | 200 / 39,319 B / 206 traces, **always** |
| DOM applied it | yes, in the 2 sessions that ran | **never — 0 of 6, across two canopy builds** |
| graph painted | 2 of 11 | **0 of 5** |

The claimed-Input starvation this arc spent a session diagnosing and fixing **is closed**. What remains is
a different defect — the correct 39 KB figure arrives and the DOM does not apply it — filed as
**F-CANOPY-039**, and it is now the sole blocker on M-TOPOLOGY-01..18 / W4-01..17 / W1-12..14.

### The A/B that mattered

A 0-of-5 census on freshly-merged code is exactly the shape of a self-inflicted regression, so it was
tested rather than argued about. A second canopy leg was stood up on `:8052` from **pre-merge `9f6fac9`**,
against the *same* cascor and the *same* trained network, and driven via `JUNIPER_E2E_CANOPY_URL`. It
fails **identically** — `painted=False after 241.8 s`, `sig=2`, `counts 0/0/0/0`. None of
canopy#531/#532/#533/#534/#535 caused it. Harness: `util/ad-hoc/e2e_f037_ab_premerge_leg.bash`.

**This should have been the first move and was nearly not made.** The census result alone reads as "the
fix failed"; the wire census reads as "the fix worked"; only the A/B distinguishes "we broke it" from "it
was already broken". When a post-merge measurement is worse than the pre-merge one on record, stand up the
pre-merge build before writing either conclusion down.

### Two instrument lessons, both paid for here

- **A `logger.debug` grep returning zero is not evidence when DEBUG is off.** "Zero `Fetched topology from`
  lines" was read as "the store handler never runs" — the canopy log had **zero DEBUG lines at all**. The
  wire census then showed that handler firing 12x/60 s. Check the level before reading a debug-line count.
- **The driver's `_store()` probe is unreliable in this configuration.** It returned `None` in every
  session while that store's writer was provably firing, and returned `changed=None` / `depth=None` from
  the same request-body extraction. Its zeros are instrument artifacts. The DOM reads (`sig`, `traces`,
  `counts`) and the response bytes are the trustworthy signals.

### Owner decision 4 (live 3-D) — the provisioning half is CONFIRMED live

The stack was brought up with `JUNIPER_E2E_DATA_EXTRAS=api,equities`, and `GET /v1/generators` on the data
leg now reports **`equities available=True`** and **`equities_seq available=True`** (they were
`available:false`). This confirms the source diagnosis exactly: it was the absent optional extra, not a
defect. `mnist` remains `available=False` — the same class, its own extra. The other half stands
unchanged: `/api/dataset/generate` is demo-gated by design, so the **both-arms** decision needs new matrix
rows (a demo arm on `generate`, a live arm on `/api/stage_dataset`), not re-scoped ones.

### New tooling

- `util/ad-hoc/e2e_f037_render_census.py` — N independent sessions in N separate processes, reading each
  session's structured verdict from its own results file rather than scraping logs. Defaults to **11**
  sessions because that is the finding's sample size, and it deliberately does **not** judge pass/fail: a
  non-zero exit means the census failed to measure, which is a different thing from a bad render rate.
- `util/ad-hoc/e2e_f037_ab_premerge_leg.bash` — a second canopy leg on `:8052` from any checkout, against
  the live trio's cascor/data, for exactly the A/B above.

### Ledger

**43 findings / 25 fixed / 1 accepted / 17 open** (0 P0 · 2 P0/P1 [F-CANOPY-037 mechanism-closed but
rows-blocked, F-CANOPY-039] · 2 P1 · 13 P2). Matrix unchanged at 298/298, 0 unfilled — **no row was
re-scored**, because the block they belong to still does not paint.

### Still owed

F-CANOPY-039's three named probes (duplicate ids first); then the topology re-drive that F-037 has been
waiting for. F-CANOPY-038's re-measure is now cheap — the stack is up and `--step storestorm` is one
command. F-CANOPY-036's fix (canopy#536) needs a live run with the Candidate Metrics tab open. And the
F-CANOPY-026 live confirmation needs a **mid-run** sample: `phase_started_at` is cleared once a run
completes, so a post-run probe reads `None` and proves nothing.
