# Juniper Canopy — E2E Validation Plan + Test Matrix: Coverage & Consistency Audit

**Project**: Juniper — juniper-canopy end-to-end front-end validation
**Repository under audit**: pcalnon/juniper-canopy (READ-ONLY) · documents filed in pcalnon/juniper-ml
**Document Type**: Findings Report / Independent Coverage Audit
**Status**: **COMPLETE**
**Date**: 2026-08-08
**Auditor**: independent coverage auditor (Claude Code, read-only; no repository was modified)

**Documents audited**

1. `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` (the plan, 704 lines)
2. `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` (the matrix, 1015 lines)

**Method.** The derivation in the Appendix was produced **before** either document was opened, directly from
`juniper-canopy` at `main` / `e8309ec` (clean tree): an AST sweep of `src/frontend/**` for every `id=`-bearing
Dash component (471 total, 181 interactive constructions → **186 distinct interactive id families**), an AST
sweep of every `requests.*` / `session.*` call site (72), and the `@app.<verb>` route inventory of `src/main.py`.
The documents were then diffed against that derivation mechanically. Sibling repos (`juniper-recurrence`,
`juniper-ml`) were consulted only where the plan makes claims about them.

**Lens.** Completeness, internal consistency, feasibility, and invented claims. A parallel grounding auditor
owns `file:line` re-probing; line numbers below are cited only where they carry a finding.

**Scope note.** This audit deliberately does **not** re-verify every `file:line` in the audited documents. It
verifies (a) that nothing in the derived control/endpoint/tab universe is missing from the documents,
(b) that the documents agree with each other and with themselves, (c) that each step is executable as written
against the lane it declares, and (d) that nothing the documents assert is absent from source.

---

## 1. Executive verdict

### **MAJOR-GAPS** — 3 blocker findings, 13 major, 22 minor (38 total)

The two documents are **unusually well grounded**. The mechanical hallucination sweep found **zero**
unresolvable identifiers: 300 distinct kebab-case control-id tokens in the matrix and 76 backticked symbol
tokens all resolve to real `juniper-canopy` source, and every tab in the derived roster and (with the
exceptions listed in §2) every interactive control id appears in the matrix. Tab coverage is a genuine 15/15.
The matrix's 287 control rows and 13 workflows / 195 steps are the most complete UI inventory that exists for
this application.

The verdict is nevertheless MAJOR-GAPS because three findings would, if the documents were approved as-is,
either invalidate the evidence Phase 1 produces or break a lane the plan promises to leave untouched:

| ID | Finding | Why blocker |
|---|---|---|
| **FE-1** | `enable_ws_control_buttons` **defaults `True`** — the five training-control buttons ship as a *clientside* callback that sends over the `/ws/control` WebSocket, with REST only as a fallback. Every matrix row and workflow step asserting `POST /api/train/*` on a button click is written against the non-default transport. | The single most-exercised surface in the arc (FA-3, W1, W2) would produce false FAILs — or worse, an operator "fixing" the app to match the doc. |
| **FE-2** | `make test-ui` is `pytest src/tests/ui --override-ini=addopts=` with **no `-m` filter**. Adding `src/tests/ui/live/` under it pulls the live suite into the demo runner. The plan changes only `ci.yml:402`. | Directly contradicts plan §6.4 exit and A-6 ("`make test-ui` ... unchanged"). |
| **CN-1** | The plan (§3.3, §6.2, §8.4, A-3) and the matrix (§4, §6.4) use **two incompatible `W-n` namespaces**. Plan W-3 = training control; matrix W3 = parameter apply. Plan W-5 = params; matrix W5 = snapshot lifecycle. Plan W-10 = topology; matrix W10 = metrics layouts. Plan W-12 = dataset import; matrix W12 = evolution/boundaries. The plan has 12 workflows, the matrix 13. | The plan's execution order, suite composition and acceptance criteria reference workflow ids that name different workflows in the document that is actually executed. |

Counts by audit dimension:

| Dimension | blocker | major | minor | total |
|---|---:|---:|---:|---:|
| **A** — Coverage gaps (§2) | 0 | 5 | 4 | 9 |
| **B** — Owner-mandate coverage (§3) | — | — | — | 5 verdicts: 2 COVERED, 3 COVERED-WITH-GAPS, 0 UNCOVERED |
| **C** — Internal consistency (§4) | 1 | 3 | 9 | 13 |
| **D** — Feasibility (§5) | 2 | 4 | 4 | 10 |
| **E** — Suspected inventions (§6) | 0 | 1 | 5 | 6 |
| **Total** | **3** | **13** | **22** | **38** |

**Every blocker is mechanically fixable before approval** — none requires re-authoring either document.
§7 lists the corrections in applicable form.

---

## 2. Coverage-gap findings

Verified pass first, so the gaps are read in proportion:

- **Tabs — VERIFIED PASS.** All 15 `tab_id`s from `_all_visualization_tabs` (`dashboard_manager.py:2176-2252`)
  appear in matrix §3.1-§3.15 with a per-control section, in §6.1's cross-check, and each maps to ≥1 workflow
  that genuinely visits it (spot-checked all 15 against workflow bodies). The plan's §3.2 table matches the
  derived roster exactly, including the 5 `_CASCADE_ONLY_TAB_IDS` (`:387` — `candidates`, `topology`,
  `evolution`, `boundaries`, `workers`).
- **Control ids — VERIFIED PASS with 4 exceptions (CG-4, CG-6 below).** Of the 186 derived interactive id
  families, 185 appear in the matrix (many in shorthand `-suffix` form, which is legitimate). The one literal
  miss, `metrics-panel-speed-2x`, is covered by the consolidated row `metrics-panel-speed-1x/2x/4x` at matrix
  §3.1 — a stated consolidation, not a gap.

---

### CG-1 — `GET /api/snapshots/{id}/history/dataset_swaps` is frontend-called and absent from both documents  — **major**

**Location**: `juniper-canopy/src/frontend/dashboard_manager.py:5686` (caller); `src/main.py` route
`@app.get("/api/snapshots/{snapshot_id}/history/dataset_swaps")`.

**Problem**: this is the endpoint that fills `dataset-swap-events-store`, which in turn drives *two* documented
surfaces: `replay-player-panel-swap-events-graph` / `-swap-events-count` (matrix §3.10) and
`hdf5-snapshots-panel-dataset-swaps-content` (matrix §3.9). Neither document names it. The matrix §1.6 route
inventory lists only the *global* `/api/history/dataset_swaps :4006`; the plan §3.4 likewise. W7 step 13
exercises the global route; nothing exercises the per-snapshot route. A row rendering from an empty store is
indistinguishable from a 404 on this endpoint.

**Evidence**:

```
$ grep -n 'history/dataset_swaps' juniper-canopy/src/frontend/dashboard_manager.py
5686:                self._api_url(f"/api/snapshots/{snapshot_id}/history/dataset_swaps"),

$ grep -n 'history/dataset_swaps' notes/JUNIPER_2026-08-08_..._TEST-MATRIX.md
110:`/api/live_dataset_swap` (POST/DELETE) :3937/:3968 · `/api/history/dataset_swaps` :4006 · `/api/csrf` :535.
786:13. `GET /api/history/dataset_swaps` returns the new event. → **API** → `main.py:4006`
```

(The per-snapshot form appears nowhere in either document; the plan file returns no match at all.)

**Fix**: add the route to matrix §1.6 and add a W7 step, after step 15, asserting the per-snapshot fetch fires
when a replay session with a swap in its window is loaded.

---

### CG-2 — `POST /api/ws_latency` (browser-originated, every 60 s) is absent from both documents — **minor**

**Location**: `juniper-canopy/src/frontend/assets/ws_latency.js:47-50`; route `@app.post("/api/ws_latency")`.

**Problem**: the matrix asserts `latency-display` (§2.3) is fed by `GET /api/status`, which is correct for the
*displayed* string, but the shipped asset independently POSTs aggregated latency samples from the browser on a
60 s cadence. This is one of only three browser-originated (non-internal-token) HTTP calls in the app — the
exact class the plan's T-8 rate-limiter reasoning turns on — and no row, workflow step, or console/network
expectation mentions it. A W13 "console clean / no unexpected requests" assertion could flag it as noise.

**Evidence**:

```
$ grep -rn 'ws_latency' juniper-canopy/src/frontend/assets/ws_latency.js
5: * in WS frames, and POSTs aggregated samples to /api/ws_latency every 60s.
50:            xhr.open("POST", "/api/ws_latency", true);
$ grep -n 'ws_latency' notes/JUNIPER_2026-08-08_..._TEST-MATRIX.md notes/JUNIPER_2026-08-08_..._VALIDATION-PLAN.md
(no matches)
```

---

### CG-3 — The WebSocket endpoints the browser actually uses are never named or exercised — **major**

**Location**: `juniper-canopy/src/main.py:634` (`@app.websocket("/ws/training")`), `:777`
(`@app.websocket("/ws/control")`), `:3147` (`@app.websocket("/ws")`).

**Problem**: canopy exposes three WS endpoints. The matrix mentions none. The plan mentions `/ws/training`
once, in T-17 (idle-timeout precision), and `/ws/control` nowhere. Yet:

- `/ws/control` is the **default** transport for the five training-control buttons (see FE-1) —
  `websocket_client.js:517` opens `window.cascorControlWS = new CascorWebSocket(controlWSUrl, {csrf: true})`;
- the WS badge (matrix §2.4, 7 states) is a *derived* view of that socket plus `/api/stream_health`;
- matrix §5.2 A-1 instructs the operator to "Record which transport the run exercised" but supplies no way to
  observe it beyond a server startup log line.

Consequence: the matrix's `verify` vocabulary includes **WS** ("WebSocket frame observation") but no row
states *which socket*, *which frame shape*, or *what a passing frame looks like*. WS is therefore an
unexecutable verification method as documented.

**Evidence**:

```
$ grep -n '@app.websocket' juniper-canopy/src/main.py
634:@app.websocket("/ws/training")
777:@app.websocket("/ws/control")
3147:@app.websocket("/ws")
$ grep -n 'ws/control' notes/JUNIPER_2026-08-08_..._TEST-MATRIX.md notes/JUNIPER_2026-08-08_..._VALIDATION-PLAN.md
(no matches)
```

**Fix**: add a §1.6-style WS inventory to the matrix (3 endpoints, which one each surface uses), and define
what a **WS** verify means concretely (CDP `Network.webSocketFrameSent/Received` in Playwright).

---

### CG-4 — The 11 restart-modal granular fields have no rows and no stated consolidation — **major**

**Location**: `dashboard_manager.py:5148-5175` (`_build_restart_dataset_fields`) and `:5176-5204`
(`_build_restart_param_fields`).

**Problem**: the N3b "granular MODIFY" section of the restart-confirm modal contains 11 interactive controls:
`restart-ds-type` (Dropdown) plus `restart-ds-samples`, `restart-ds-noise`, `restart-ds-rotations`,
`restart-ds-spirals`, `restart-p-nn-learning-rate`, `restart-p-nn-max-hidden-units`, `restart-p-nn-patience`,
`restart-p-cn-pool-size`, `restart-p-cn-selected`, `restart-p-cn-corr-thresh` (all
`dbc.Input(type="number")`). Matrix §2.10 enumerates the restart modal's children — `restart-confirm-summary`,
`restart-start-fresh-toggle`, `restart-granular-toggle`, `restart-granular-collapse`,
`restart-granular-context`, `restart-modal-baseline`, `restart-cancel-button`, `restart-confirm-button` — and
**omits all 11 fields**. They appear only as the glob `every restart-ds-* / restart-p-* field is seeded`
(W6 step 10) and via one named instance (`#restart-ds-type`, W6 step 14).

This is the surface the source itself calls out as the difference between N3 (read-only VERIFY) and N3b
(in-place MODIFY) — i.e. the *editing* half of cold migration, an owner-named fragile area. Ten of the eleven
are numeric and therefore not browser-drivable at all (see FE-5).

**Evidence**:

```
$ grep -o -- 'restart-ds-[a-z]*\|restart-p-[a-z-]*' notes/JUNIPER_2026-08-08_..._TEST-MATRIX.md | sort | uniq -c
      1 restart-ds-
      1 restart-ds-type
      1 restart-p-
$ grep -o -- 'restart-ds-[a-z]*\|restart-p-[a-z-]*' notes/JUNIPER_2026-08-08_..._VALIDATION-PLAN.md
(no matches)
```

Source (`dashboard_manager.py:5169-5174`):

```python
_num("Samples", "restart-ds-samples", 100, 1),
_num("Noise", "restart-ds-noise", 0.05, 0),
_num("Spiral rotations", "restart-ds-rotations", 0.5, 0),
_num("Spirals", "restart-ds-spirals", 1, 1),
```

---

### CG-5 — Matrix §6.3's cross-check maps 7 surfaces to workflows that do not exercise them — **major**

**Location**: matrix §6.3 "Cross-cutting global chrome" (lines 971-993).

**Problem**: §6.3 is the table that substantiates the matrix's completeness claim. Seven of its 19 rows name a
workflow that contains no step touching the surface. Tested by extracting each workflow body and searching for
the surface's id / label:

| §6.3 row | Claimed workflow | Result |
|---|---|---|
| WS badge (7 states incl. initial) | W1, **W13** | W1 **HIT** (step 4); W13 **ABSENT** — no badge step |
| Tooltips (24) | **W13** | **ABSENT** — no workflow hovers a tooltip anywhere |
| Network Information (2 collapse levels) | **W1** | **ABSENT** — `network-info*` appears in no W1 step |
| Pinned Parameters mirror | **W3** | **ABSENT** — W3's only "pinned" is *"body shape pinned by test_param_roundtrip_visible.py"* |
| CN meta-parameter block **+ triple validator** | **W3** | validator **ABSENT** — `cn-pool-triple-feedback` / "triple" appear in no W3 step |
| Tab bar + persistence + **sidebar visibility/width** | **W13** | persistence HIT (step 11); visibility/width **ABSENT** |
| Dataset-stage outcome alert | **W6** | **ABSENT** — W6 has no staging-failure arm |

**Evidence** (extraction script output; workflow bodies delimited by `^### W\d+ —`):

```
WS badge                 in W13 : ABSENT
Tooltips                 in W13 : ABSENT
Network Information      in W1  : ABSENT
Pinned Parameters        in W3  : HIT  pinned        <- false positive, see below
dataset-stage-outcome    in W6  : ABSENT
CN triple validator      in W3  : ABSENT
sidebar width            in W13 : ABSENT
sidebar visibility       in W13 : ABSENT
model-selection modal    in W8  : HIT  model-selection-modal
welcome modal            in W13 : HIT  welcome
dark mode                in W13 : HIT  dark-mode-toggle
restart-outcome-alert    in W6  : HIT  restart-outcome-alert

W3 [pinned] ... body shape pinned by `src/tests/ui/test_param_roundtrip_visible.py:37-6...
```

The `cn-pool-triple-feedback` case is the costliest: it is a **nine-branch clientside truth table** mirroring
cascor's `_validate_candidate_pool_triple` (matrix §2.8 documents all nine branches) and no workflow drives a
single one of them.

**Note**: §6.1 (tabs) and §6.2 (fragile areas) survive the same test — every mapping there is real. The defect
is confined to §6.3.

---

### CG-6 — No workflow exercises the `{"type":"param-pin"}` pin/unpin cycle — **minor**

**Location**: `parameters_panel.py:117-118`; matrix §3.8 rows (3 of them) and §2.9 `sidebar-pinned-card` /
`sidebar-pinned-list`.

**Problem**: the pin control is the only pattern-matched control on the Parameters tab and drives a
`storage_type="local"` store that survives reload. §3.8 documents it in three rows (check → store; check →
sidebar mirror; uncheck-all + reload → persistence) but no numbered workflow performs the gesture. Combined
with CG-5 this means the Parameters-tab pin feature has *no* executable click path.

**Evidence**: `grep -c 'param-pin' <matrix>` → matches only inside §3.8/§2.9 tables; no `^\d+\.` workflow step
in W1-W13 contains `param-pin` or a pin gesture.

---

### CG-7 — No workflow induces the degraded / outage conditions the plan names as fragile — **major**

**Location**: plan §7.3 ("a **degraded probe**: stop cascor mid-run…"), plan §7.1 (iv) ("repeat with
`juniper-cascor-client` deliberately absent in a throwaway env"), plan T-18; matrix §2.4 states 3/4.

**Problem**: the matrix itself concedes the gap and does not close it —

> §2.4: "states 3/4 need an induced upstream fault — **MANUAL** in Phase 1."

There is no step anywhere in W1-W13 that stops cascor, kills the relay, or removes the client package. Grep of
the matrix for `stop cascor|kill|outage|unreachable|absent` returns only *passive descriptions* of degraded
renders (`worker-panel-error-display`, `redis-panel-error-display`, `cassandra-panel-error-area`,
`dataset-plotter-dataset-selector` fallback list) — never an induction procedure.

This matters disproportionately: T-18 records that "a green badge once masked a dead relay for 12+ hours", and
T-5 records that every topology/metrics failure path returns `dash.no_update` (last-known-good) so a broken
panel reads as *stale*, not *failed*. The plan's own risk table says "Every fragile-area assertion requires an
**observed change**" — but the two assertions that would catch masking (badge downgrade, classified outage
label) have no execution path and two of the plan's named regressions
(`test_status_bar_classifies_backend_outage`, `test_ws_badge_downgrades_on_stream_health`) have no click
script to be derived from.

---

### CG-8 — Plan §3.4 claims `/api/remote/*` is "exercised through the UI"; nothing calls it — **minor**

**Location**: plan §3.4, line 148.

**Problem**: the plan's §3.4 heading is "Key API surface **exercised through the UI**" and its list includes
`/api/remote/*`. An AST sweep of every `requests.*` call in `src/frontend/**` (72 call sites) and a text grep
of `src/frontend/**` including the JS assets find **zero** callers of any `/api/remote/` route. The section's
closing sentence is honest about the method ("All enumerated from the `@app.<verb>("/api/...")` decorators in
`src/main.py`") — i.e. it enumerated *registered routes*, not *UI-reachable* ones — but the heading makes a
coverage claim the matrix does not and cannot honour (no §2/§3 row, no workflow step).

**Evidence**:

```
$ grep -rn 'api/remote' juniper-canopy/src/frontend/
(no matches)
```

Five registered routes are affected: `/api/remote/{status,connect,disconnect,start_workers,stop_workers}`.

---

### CG-9 — Acceptance criterion A-2 has no enumerated claim set anywhere in either document — **minor**

**Location**: plan §13 A-2.

**Problem**: A-2 reads "Every behavioural claim in `docs/USER_MANUAL.md` + `docs/REFERENCE.md` that maps to a
UI control has a matrix row with a terminal status". The matrix is **code-derived** (its §0: "Every component
id, callback, endpoint and `file:line` in this document was read out of the repository"), never doc-derived,
and neither document contains an enumeration of USER_MANUAL / REFERENCE behavioural claims. The plan's §11
drift table lists 8 known divergences but is explicitly a *findings* list, not a claim inventory. As written
A-2 is unmeasurable: there is no denominator.

This is sharpened by the plan's own D-4: "Only ~5 of 15 tabs documented … 10 tabs are undocumented." — so the
mapping from documented claims to matrix rows is both small and unstated.

---

## 3. Owner-mandate coverage verdicts

The owner named five frequently-broken areas. For each: does the **plan** give concrete validation steps AND a
planned automated regression, and does the **matrix** give executable click paths (workflow + rows)?

### Area 1 — Network topology graph **displays** → **COVERED-WITH-GAPS**

| Requirement | Verdict |
|---|---|
| Plan: concrete validation steps | **PASS** — §7.1 gives 4 numbered approaches incl. the anti-masking rule ("assert **node count increases**", defeating T-5). |
| Plan: planned automated regression | **PASS** — `test_live_topology_renders_and_grows`, `test_topology_weight_matrix_populates`, plus a conditional unit pin. |
| Matrix: executable click paths | **PASS** — §3.3 store-refresh + raw-store rows, §3.4 evolution rows; W1 steps 12-14, W4 steps 1/6/7, W12 steps 1-4. |
| **Gap** | §7.1 approach (iv) — "repeat with `juniper-cascor-client` deliberately absent in a throwaway env to prove the import path fails *loudly*" — has **no matrix step and no phase owner**. This is the exact defect class T-3/T-4 describe (`dashboard_manager.py:6462` and `:3742` still `from backend.cascor_service_adapter import CascorServiceAdapter`, and the surrounding `except Exception → dash.no_update` at `:6467-6469` still swallows it). The plan's own history section calls it "the 2026-07-12…14 UI-leg red". Verified live in source: the graph-format passthrough guard is `if isinstance(topology, dict) and "input_units" in topology:` at `:6456-6458`, and the adapter import is unconditional on the fall-through path. |

### Area 2 — Network topology graph **interactions** → **COVERED**

| Requirement | Verdict |
|---|---|
| Plan | **PASS** — §7.2 enumerates every control with its source range, states the figure-level assertion doctrine ("trace count, axis type `scene` for 3-D, `heatmap` type"), correctly identifies the **no-`hoverData`-callback** fact, and names 4 regressions. |
| Matrix | **PASS** — §3.3 has 18 rows including all 6 interactive controls and 6 distinct `network-visualizer-graph` gestures (click / box-lasso / click-empty / zoom-pan / modebar camera / hover-as-DEAD-EXPECTED); W4 is a 17-step script that drives every one. |
| **Independent confirmation** | My derivation independently confirms the rebuild callback takes exactly **12 Inputs** (`network_visualizer.py:344-356`) and that the only graph Inputs are `relayoutData` (`:294`), `clickData` (`:552`), `selectedData` (`:553`) — no `hoverData`, no `restyleData`, anywhere in `src/frontend/`. This is the best-covered of the five areas and the only one with no gap. |

### Area 3 — Front-page training status indicators → **COVERED-WITH-GAPS**

| Requirement | Verdict |
|---|---|
| Plan | **PASS on inventory** — §7.3 maps all 7 status-bar elements to source and to `_counter_displays`; names 3 regressions + a unit pin. |
| Matrix | **PASS on inventory** — §2.3 has one row per element (8 rows), §2.4 covers all 7 badge states, §2.5 covers the 5 buttons + the outcome alert. |
| **Gap 1 (blocker-linked)** | Every §2.5 button row declares `backend effect: POST /api/train/<cmd>` and `verify: DOM, API, NET`, but the shipped default routes those clicks over `/ws/control` (see **FE-1**). The primary status-driving workflow (W1 step 5, W2 steps 1/4/5/6/10) therefore asserts a request that will not be made. |
| **Gap 2** | The degraded probe has no click path (**CG-7**); badge states 3/4 are declared MANUAL with no induction procedure. Given T-18's 12-hour masking incident, this is the *most* important assertion in the area and the least executable. |
| **Gap 3** | The plan names `_status_bar_display_fields` as the unit-pin target; **no such symbol exists** (**IV-1**). |

### Area 4 — Snapshots saving / loading / **replaying** → **COVERED**

| Requirement | Verdict |
|---|---|
| Plan | **PASS** — §7.4 traces create → list → detail → the pattern-matched 4-op menu → replay transport → weight drain → V2/V1 badge, records the 501 demo trap (T-10), the fabricated demo list, and the two dead buttons (T-12); names 4 `ui_live` + 1 demo regression. |
| Matrix | **PASS** — §3.9 (21 rows) + §3.10 (16 rows) + W5, at 29 steps the longest workflow in the arc, covering create, view, all four ops through the shared modal, cancel, the FSM→Network-Editor unlock, every transport control, history, the DEAD-EXPECTED probe, and an explicit DEMO-lane 501 arm (step 29). |
| **Minor gaps** | (a) the per-snapshot swap-history endpoint (**CG-1**); (b) the right-click context menu is `MANUAL (native menu)` in §3.9 with no fallback if the native menu is undrivable — Playwright cannot dismiss/interact with an OS context menu, though this app's menu is JS-rendered so it is likely drivable; the doc does not say which. Neither undermines the verdict. |

### Area 5 — Dataset loading, hot and cold new-dataset migration → **COVERED-WITH-GAPS**

| Requirement | Verdict |
|---|---|
| Plan | **PASS** — §7.5 separates cold (stage → banner → restart-confirm → restart) from hot (experimental gate → two-step modal → swap → history) and Dataset-View import (demo-only), names 5 regressions, and surfaces F-CANDIDATE (recurrence selection succeeds while the backend stays cascor). |
| Matrix | **PASS on the happy paths** — §2.7 (10 rows), §2.9 (16 rows), §3.6 (29 rows), §3.9/§3.10 swap surfaces; W6 (20 steps, incl. the cancel path and the G-6-analogue input-width oracle) + W7 (17 steps, incl. the deny arm, the fallback arm and the cancel arm) + W9 (13 steps, demo lane + a live 400-mirror step). This is a strong pair. |
| **Gap 1** | The **granular MODIFY** half of cold migration is un-rowed (**CG-4**) and, for its 10 numeric fields, un-drivable (**FE-5**). W6 step 14 exercises exactly one field — a dropdown — and the doc never states that the other ten cannot be exercised. |
| **Gap 2** | `dataset-stage-outcome-alert` — the surface that exists specifically so a staging failure is not silent (`dashboard_manager.py:4663-4685`) — has no failure-arm step in W6 (**CG-5**). |
| **Gap 3** | W6 step 19 ("input-width sanity, G-6 analogue") asserts `#network-visualizer-input-count` — a **cascade-only tab**. Correct for cascor; silently unavailable if the arc ever runs W6 after a one-shot model swap. Not a defect today, worth a precondition line. |

---

## 4. Consistency findings

### CN-1 — Two incompatible `W-n` workflow namespaces across the two documents — **blocker**

**Location**: plan §3.3 / §6.2 / §8.4 / §13 A-3; matrix §4 / §6.4.

| n | Plan §3.3 | Matrix §4 | Collision? |
|---|---|---|---|
| 1 | First visit → welcome modal | Cold-start cascor training | yes |
| 2 | Tab tour (all 15) | Pause/Resume/Stop/Reset | yes |
| 3 | Start → Pause → Resume → Stop | Parameter apply round-trip | yes |
| 4 | Reset → Start | Topology exploration | yes |
| 5 | Parameter apply round-trip | Snapshot lifecycle | yes |
| 6 | Cold dataset migration | Dataset COLD migration | **no** (coincides) |
| 7 | Hot dataset migration | Dataset HOT migration | **no** (coincides) |
| 8 | Snapshot create → restore | Model switch | yes |
| 9 | Snapshot replay | DEMO-lane generate/upload/URL | yes |
| 10 | Topology render + interactions | Metrics layout save/load/delete | yes |
| 11 | Model swap | In-metrics replay controls | yes |
| 12 | Dataset View import | Evolution + Boundaries | yes |
| 13 | — (plan has 12) | Ancillary tabs + chrome smoke | plan has no W-13 |

**Consequence**: plan §6.2 prescribes the Phase-1 order "W-1 → W-2 → W-3/W-4 → W-5 → W-10 → W-8/W-9 → W-6 →
W-7 → W-11 → W-12" — read against the matrix (the document actually executed) that order runs topology
exploration under "W-4", metrics layouts under "W-10", and never runs W13 at all. Plan §8.4's suite composition
("W-3/W-4 control loop, W-5 params, W-8/W-9 snapshots+replay, W-11 model swap") is wrong in every term against
the matrix. Acceptance criterion A-3 ("W-1 … W-12 each end `PASS`") under-counts by one workflow and names the
wrong ones.

**Fix**: adopt the matrix's W1-W13 as canonical (it is the executable document) and rewrite plan §3.3, §6.2,
§8.4 and A-3 against it. Alternatively prefix the plan's as `PW-n`; either is mechanical.

---

### CN-2 — The two documents declare different row-status vocabularies while claiming they are identical — **major**

**Location**: plan §9 ("**Row statuses** … used identically by this plan and the companion matrix"); matrix §7.

| Status | Plan §9 | Matrix §7 / §1.3 |
|---|---|---|
| `PASS` / `FAIL` / `BLOCKED` | yes | yes |
| `N-A` | **yes** (a row status) | absent (matrix's `mode` column uses `L`/`D`/`B`) |
| `DEAD-EXPECTED` | **yes** (a row status) | present but as an **automation class** (§1.3), not a status |
| `DIVERGENCE` | **absent** | **yes** ("A `DIVERGENCE` is not a Phase-1 failure") |
| `UNTESTED` | used in plan §6.2 exit criterion, absent from plan §9's own table | absent |

An evidence file written under one vocabulary cannot be scored under the other, and the plan's claim of
identity is false.

---

### CN-3 — The matrix has no row IDs and no status column, but the plan's evidence protocol and A-5 require both — **major**

**Location**: plan §9 ("**Screenshots.** `reports/e2e/<run-id>/<matrix-row-id>__<step>.png`") and §13 A-5
("100 % of the companion matrix's control rows carry a terminal status"); matrix §1.1 column legend.

**Problem**: the matrix's §2/§3 tables have exactly 8 columns — control id, interaction, expected result,
backend effect, verify, auto, mode, FA. There is **no ID column and no status column**. There are **287 data
rows** across §2.1-§3.15, several of which share a control id across multiple interaction rows
(`network-visualizer-graph` appears 6 times, `visualization-tabs` 3 times, `dark-mode-toggle` 2 times,
`experimental-functions-toggle` 2 times), so "control id" cannot serve as the row key either.

**Consequence**: `<matrix-row-id>` in the screenshot convention does not exist; A-5 is unscorable as written;
and the plan's §6.2 exit ("every matrix row carries a terminal status") has no place to record one.

**Evidence** (row count by section, derived from the matrix's own markdown tables):

```
§2.1 4 · §2.2 6 · §2.3 8 · §2.4 7 · §2.5 9 · §2.6 19 · §2.7 10 · §2.8 14 · §2.9 16 · §2.10 6
§3.1 32 · §3.2 11 · §3.3 18 · §3.4 7 · §3.5 8 · §3.6 29 · §3.7 6 · §3.8 7 · §3.9 21
§3.10 16 · §3.11 18 · §3.12 4 · §3.13 4 · §3.14 4 · §3.15 3        TOTAL 287
```

**Fix**: add a leading `#` column with stable ids (`M-2.5-04`, `M-3.9-12`, …) and a trailing `status` column
before approval. Retro-fitting ids after execution loses the evidence linkage.

---

### CN-4 — "27 fields" for the Apply `POST /api/set_params` payload; the shipped payload has 25 — **major**

**Location**: matrix §2.9 `apply-params-button` row ("`POST /api/set_params` with all 27 fields") and W3 step 3
("the full 27-field body").

**Problem**: three different numbers exist in the ecosystem and the documents adopt the wrong one.

- The **dashboard's actual POST body** (`dashboard_manager.py:6971-7003`) has **25** keys. Source comments
  explicitly drop three: `nn_dataset_elements` / `nn_dataset_noise` ("canopy-local and travel on
  `/api/stage_dataset`", `:6980-6982`) and `cn_training_complete` ("a read-only status flag … dropped from the
  set_params payload", `:6988-6989`), and add `nn_init_output_weights` (`:7002`).
- **27** is the length of the *dirty-tracking* `comparisons` list (`:6883-6909`) — a different set.
- The shipped UI test's payload has **27** keys and its own comment says **28**
  (`src/tests/ui/test_param_roundtrip_visible.py:34-35`: "the dashboard sends all 28 fields on Apply").

**Evidence**:

```
$ python3 - <<'PY'   # extract the params dict at dashboard_manager.py:6971
payload keys: 25
['nn_max_iterations','nn_max_total_epochs','nn_learning_rate','nn_max_hidden_units',
 'nn_multi_node_layers','nn_growth_trigger','nn_growth_preset_epochs',
 'nn_growth_convergence_threshold','nn_patience','nn_spiral_rotations','nn_spiral_number',
 'cn_pool_size','cn_correlation_threshold','cn_selected_candidates','cn_training_iterations',
 'cn_training_convergence_threshold','cn_patience','cn_multi_candidate','cn_candidate_selection',
 'cn_top_candidates','cn_random_candidates','nn_output_epochs','nn_optimizer_type',
 'nn_activation_function_name','nn_init_output_weights']
PY
```

W3 step 3 remains **executable** (it says to mirror the shipped test's body, which is a passing test), but the
matrix's description of what the Apply button does is wrong — and the discrepancy is exactly the kind that
turns into a "fix" PR against working code.

---

### CN-5 — Tooltip count is 23, not 24; "23 parameter inputs" is 22 — **minor**

**Location**: matrix §2.9 ("24 `dbc.Tooltip`s built at `:1819` from `CONTROL_TOOLTIPS` … — 23 parameter inputs
+ `apply-params-button`").

**Evidence**: `CONTROL_TOOLTIPS` has **23** entries total, one of which *is* `apply-params-button`, so 22 are
parameter controls. The builder is a comprehension over `CONTROL_TOOLTIPS.items()`
(`dashboard_manager.py:1819`), so exactly 23 `dbc.Tooltip`s are emitted.

```
$ python3 -c "...ast.literal_eval(CONTROL_TOOLTIPS)..."
entries: 23
has apply-params-button: True
```

---

### CN-6 — `dataset-plotter-import-url-input` is `type="url"`, described as text — **minor**

**Location**: matrix §3.6 ("`type` is text — normal fill works"); source `dataset_plotter.py:248-249`:

```python
dbc.Input(
    id=f"{self.component_id}-import-url-input",
    type="url",
```

The *conclusion* (normal fill works — the wall is specific to `type="number"`) is correct; the stated attribute
is not. Worth correcting because §1.3's wall doctrine is enumerated by `type`.

---

### CN-7 — "the twelve tests named in §7" — §7 names 18 `ui_live` tests (19 including the demo one) — **minor**

**Location**: plan §8.4 ("Fragile-area regressions | `live/test_fragile_*.py` | **the twelve tests named in
§7** | live").

Counting §7's "Planned regression tests" lines: §7.1 → 2, §7.2 → 4, §7.3 → 3, §7.4 → 4 (+1 demo-lane), §7.5 →
5 = **18 `ui_live`** (+1 demo). Acceptance criterion A-4 ("≥12 new `ui_live` tests") is satisfied either way,
but §8.4's count is wrong and under-scopes the PR-C-F budget by a third.

---

### CN-8 — The recurrence settings path differs between plan §4.2 and plan §15 — **minor**

§4.2 cites `juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py:128,:152`; §15 cites
`juniper-recurrence/juniper_recurrence/settings.py:128,:152` (one directory short). The first is correct:

```
$ find juniper-recurrence -name settings.py -path '*juniper_recurrence*'
juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py
```

---

### CN-9 — Recurrence port: §15 says 8210, §4.5 picks 8211 — and 8211 is the deploy **host** port — **minor**

**Location**: plan §4.5 / §6.1 PR-M2 / §10 PR-M2 (all "8211"); plan §15 ("port 8210").

**Problem**: `juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py:152` reads:

```python
port: int = 8210  # container port; deploy maps host 8211 -> ctr 8210 (design §6.8)
```

So **8211 is the documented operator/deploy host port for recurrence**, and plan §4.1 opens with the isolated
stack's defining property: "brings up a trio that never touches operator ports". Choosing 8211 for the
optional fourth leg contradicts that doctrine and would collide with a running deploy stack. The §15 "port
8210" note is not wrong, but the two sections read as if they disagree.

**Fix**: pick a port outside both the operator set and the experiment ranges (`experiment_stack.bash` reserves
recurrence 8260-8289) — e.g. 8203, adjacent to the isolated cascor 8202 — and state the reasoning.

---

### CN-10 — Header field and cross-reference asymmetry — **minor**

The plan uses `**Date**: 2026-08-08`; the matrix uses `**Last Updated**: 2026-08-08`. The plan names both
audit reports ("Grounding audits to be produced against this plan": `…E2E-PLAN-GROUNDING-AUDIT.md`,
`…E2E-PLAN-COVERAGE-AUDIT.md`); the matrix §7 only says "an independent cross-validation pass … is
recommended" without naming them, so a reader arriving at the matrix first cannot find the audits.

All cross-references that *are* present resolve: the matrix's companion filename matches the plan's actual
filename byte-for-byte, and vice versa (verified by `ls notes/`).

---

### CN-11 — The matrix never states its dependency on the Phase-0 port fix — **minor**

The matrix's target surface is `http://127.0.0.1:8051/dashboard/` (§0). Plan T-1 establishes that canopy
**cannot bind 8051 today** — `util/isolated_stack.bash:252` exports `JUNIPER_CANOPY_PORT`, which does not exist
in canopy. Independently confirmed:

```
$ grep -rn 'JUNIPER_CANOPY_PORT' juniper-canopy/ --include='*.py' --include='*.md' --include='*.yaml' \
      --include='*.yml' --include='*.toml' --include='*.env*'
(no matches)
```

`ServerSettings.port` defaults to `8050` (`src/settings.py:118-122`) under
`env_prefix="JUNIPER_CANOPY_"` + `env_nested_delimiter="__"` + `extra="ignore"` (`:188-195`), so the correct
name is `JUNIPER_CANOPY_SERVER__PORT`. **Corroborating evidence the plan does not cite**: canopy's own UI
conftest already uses the nested form —

```python
# juniper-canopy/src/tests/ui/conftest.py:37-39
"JUNIPER_CANOPY_DEMO_MODE": "1",
"JUNIPER_CANOPY_SERVER__HOST": "127.0.0.1",
"JUNIPER_CANOPY_SERVER__PORT": str(port),
```

T-1 is a **verified-true blocker** and the plan's Phase-0 fix is correct. The matrix should carry a one-line
"prerequisite: plan Phase 0 (T-1)" so it is never executed against a canopy on 8050.

---

### CN-12 — Plan §8.2 says "the two demo pins"; there are three sites — **minor**

Plan §8.2 item 1 scopes the escape hatch to "Both conftests". The pins are at:

- `juniper-canopy/conftest.py:12` — `os.environ["JUNIPER_CANOPY_DEMO_MODE"] = "1"`
- `juniper-canopy/src/tests/conftest.py:23` — same (plus `JUNIPER_DATA_URL=http://localhost:8100`, the
  **operator** data port, and `JUNIPER_CANOPY_RATE_LIMIT_ENABLED=false`)
- `juniper-canopy/src/tests/ui/conftest.py:38` — `"JUNIPER_CANOPY_DEMO_MODE": "1"` inside the `canopy_url`
  subprocess env

The third is bypassed on the live path only because §8.2 item 2 Popens nothing — an implicit dependency worth
stating. The `JUNIPER_DATA_URL` pin at the operator port is a second unlisted pin in the same file.

---

### CN-13 — The `params-status` 429 arm is documented as reachable; per plan T-8 it is not — **minor**

Matrix §2.9 lists `429 with retries exhausted → "Rate limited — please try again in a few seconds"` as one of
the `params-status` outcomes. Plan T-8 establishes `rate_limit_enabled: bool = False`
(`src/settings.py:317`) and that server-side self-calls carry the internal-request token regardless. The Apply
path is a **server-side** Dash callback (`dashboard_manager.py:4505` → `_apply_parameters_handler` →
`_apply_params_via_backend` → `requests.post(self._api_url("/api/set_params"), …, headers=internal_api_headers())`
at `:7034`), so the 429 branch is unreachable in both lanes as configured. The row should be marked
`N-A (limiter off; self-call exempt)` rather than presented as an observable outcome.

---

## 5. Feasibility findings

### FE-1 — The five training-control buttons default to the `/ws/control` transport, not `POST /api/train/*` — **blocker**

**Location**: `src/settings.py:349`; `src/frontend/dashboard_manager.py:4125`; matrix §2.5 (9 rows), W1 step 5,
W2 steps 1/4/5/6/10; plan §7.3.

**Problem**: the shipped default is WebSocket-first.

```python
# juniper-canopy/src/settings.py:348-349
# Phase D: control buttons over WebSocket (D-49, §S10)
enable_ws_control_buttons: bool = True  # D-49: P12b flag-flip — production soak passed, browser buttons via /ws/control
```

```python
# juniper-canopy/src/frontend/dashboard_manager.py:4122-4125
# automatic REST fallback if the send() promise rejects. When the flag
# is off (default), the pre-Phase-D server-side handler is registered   <-- STALE COMMENT
# instead and keeps the existing behavior plus test fixtures untouched.
if getattr(self._settings, "enable_ws_control_buttons", False):
```

The clientside JS routes as follows (`dashboard_manager.py:212-213`, `:184`):

```javascript
var ws = window.cascorControlWS;
var wsReady = !!(ws && ws.connected && ws.ws && ws.ws.readyState === 1 /* OPEN */);
...   // only on WS-unavailable / send() rejection:
fetch('/api/train/' + command, fetchOpts)
```

`window.cascorControlWS` is opened unconditionally by `assets/websocket_client.js:517`.

**Consequences for the documents**:

1. Matrix §2.5 rows 2-6 declare `backend effect: POST /api/train/<cmd>` and `verify: DOM, API, **NET**`. Under
   the default, no such HTTP request is made — a NET assertion fails on a working app.
2. W1 step 5 cites `dashboard_manager.py:4158` as the handler; `:4158` is inside the **`else`** (server-side)
   branch, i.e. the non-default path.
3. Matrix §2.5's debounce row cites `:6615-6621` (server-side handler); the clientside JS has its own 500 ms
   guard at `:130-160`.
4. The matrix's auth note (lines 120-124) reasons about `/api/train/*` `Origin` + `X-CSRF-Token`; under the
   default the CSRF is carried by the WS handshake (`{csrf: true}`, `websocket_client.js:517`) instead.
5. Matrix §5.2 A-1 *does* describe the two-transport branch and says "Record which transport the run
   exercised" — but never states which is the default, and leaves every row REST-only.

**Fix**: state the default explicitly; give each of the 6 button rows a WS-primary / REST-fallback pair of
expectations; add a Phase-0 evidence-header field `enable_ws_control_buttons`; and either (a) define a **WS**
verify concretely, or (b) have Phase 1 run with `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` for the REST
rows *and* a second pass at the default for the WS rows, stating which rows belong to which pass.

---

### FE-2 — Adding `src/tests/ui/live/` breaks `make test-ui`, which the plan promises to leave unchanged — **blocker**

**Location**: `juniper-canopy/Makefile:23-24`; plan §8.2 item 3-4, §6.4 exit, §13 A-6.

```make
test-ui:
	$(PYTEST) src/tests/ui --override-ini=addopts=
```

There is **no `-m` filter**. The plan places live tests at `src/tests/ui/live/` "so the existing `--ignore`
keeps it out of the default run" — true for bare `pytest`, but `make test-ui` targets `src/tests/ui`
explicitly *and* clears `addopts`, so it will collect and run every `ui_live` test with no live stack. The plan
changes only the CI marker expression (`ci.yml:402` → `-m "ui and not slow and not ui_live"`) and leaves the
Makefile untouched.

Plan §6.4 exit says "`make test-ui` (demo) and the new live runner both green; default `pytest` unchanged" and
A-6 says "`make test-ui` and default `pytest` unchanged". Neither can hold.

**Fix (one line)**: `test-ui: $(PYTEST) src/tests/ui -m "not ui_live" --override-ini=addopts=` — and add it to
PR-C-H's scope in §10.

---

### FE-3 — Matrix W8 declares a precondition the declared lane cannot satisfy, with no fallback — **major**

**Location**: matrix W8 ("**Preconditions**: LIVE lane with a reachable recurrence service."), matrix §6.4
(lists W8 under LIVE unconditionally); plan §4.5.

The plan establishes that `util/isolated_stack.bash` starts **data, cascor, canopy only** (independently
verified: no `recurrence` token in the script) and makes the fourth leg a §4.5 *decision the owner may
override*. The matrix carries neither the dependency nor an `N-A` fallback, and §6.4's lane table asserts W8
runs on LIVE. If the owner declines PR-M2, W8's 15 steps are unexecutable and §6.4 is wrong.

Note also that steps 6-10 of W8 (cascade-tab suppression, `status-iteration-segment` hidden,
`metrics-panel-oneshot-result` shown, dataset re-gating, `oneshot-start-params-store` non-`None`) depend on
`model-class-store == "one_shot"`, which is only written by the modal Select's response — and that response's
`execution` value comes from a backend that, without a configured URL, never becomes a recurrence backend
(`_selection_targets_recurrence`, `main.py:3498-3509`).

---

### FE-4 — The plan's §4.5 fallback would build a real recurrence adapter against canopy itself — **major**

**Location**: plan §4.5 Fallback ("pointing `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` at the stack's own canopy
port so the routing predicate is satisfied without a real fit").

**Problem**: satisfying the predicate is not cosmetic — it changes the process-global backend.

```python
# juniper-canopy/src/backend/__init__.py:130-134
adapter = RecurrenceServiceAdapter(settings.recurrence_service_url, settings.recurrence_api_key)
logger.info("Recurrence mode: model %r -> RecurrenceServiceAdapter at %s", nn_model, settings.recurrence_service_url)
return RecurrenceBackend(adapter)
```

`POST /api/model/select` re-creates the backend, so pointing the URL at canopy's own port yields a
`RecurrenceBackend` whose every upstream call targets a service that does not implement the recurrence API.
There is no validator that would reject a self-URL (`_check_recurrence_service_url`, `settings.py:509-525`,
only resolves a shared unprefixed alias). The dashboard's status/metrics/topology polling all read through
`backend`, so the likely outcome is a broadly broken dashboard, not "selection / gating / suppression UI only".

**Fix**: replace the fallback with either (a) a stub recurrence service (a 40-line FastAPI shim answering
`/v1/health/ready` + `/v1/train` + `/v1/predict`) in `util/ad-hoc/`, or (b) an honest `N-A (no recurrence
service)` for all of W8, which the plan's own §9 vocabulary already supports.

---

### FE-5 — The restart modal's "granular MODIFY" capability is not drivable by any documented method — **major**

**Location**: `dashboard_manager.py:5157-5162` and `:5185-5190` (the shared `_num` builder emits
`dbc.Input(..., type="number", ...)`); matrix W6 steps 13-14; plan T-7 / §8.3.

**Problem**: 10 of the 11 granular fields are `dbc.Input(type="number")` and therefore hit the wall pinned by
two **strict** xfails (verified: `test_apply_button_flow.py:61-62` `@pytest.mark.xfail(strict=True, …)`;
`test_l3_native_setter_poc.py:45-47` same). The plan's escape hatch — the `set_params` doctrine (§8.3) — drives
the *effect* through `POST /api/set_params` and asserts the DOM reflects it. That works for the sidebar
parameters, which are hydrated from `/api/state`. It does **not** work here: the granular fields are *seeded on
modal open* from staged/current values, and the thing under test is the **edit**, whose only consumer is the
Confirm handler's diff-against-baseline (`dashboard_manager.py:5058-5079`). There is no route that writes those
Dash `State`s. So:

- the seeding half is testable (set backend params → open modal → assert seeded values);
- the **modify** half — the entire point of N3b — is untestable by any method either document names.

W6 step 14 quietly sidesteps this by choosing the one dropdown ("Edit one granular field (**a dropdown**, e.g.
`#restart-ds-type`)") without saying why. The documents should say so explicitly and record the modify half as
a known coverage limit (or adopt the `dash_duo` path — see FE-9).

---

### FE-6 — W5 steps 11-12 require a shape the workflow's own preceding steps never establish — **major**

**Location**: matrix W5 steps 10-12.

Step 10 records that `#network-editor-panel-topology-readout` reads **"No topology loaded."** and the
remove-unit dropdown is empty (DIVERGENCE D-0 — independently confirmed: `network_editor_panel.py:516` fetches
`/api/network/topology`, which is not among main.py's routes; the registered neighbours are
`/api/network/stats`, `/api/topology`, `/api/topology/raw`).

Step 11 then says to "fill `#network-editor-panel-patch-values` with a correctly shaped row-major list", and
step 12 to fill `#network-editor-panel-add-weights` with "`input_size + n_hidden` floats". Neither the shape
nor the two counts are obtainable from any preceding step — the readout that would have supplied them is the
dead one. The values *are* available, on a different tab (`network-visualizer-input-count` /
`-hidden-count`, §3.3), and W5 never goes there before step 11.

**Fix**: insert a step between 10 and 11: "Topology tab → read `#network-visualizer-input-count` (I) and
`#network-visualizer-hidden-count` (H); the append vector length is I + H."

---

### FE-7 — W3 step 9's clamp arm has no DOM precondition — **minor**

Step 9: "`POST /api/set_params` with a value outside `CascorPatchBounds`, then Apply from the UI on the same
field → the toast carries ` (clamped to bounds: key→value)`."

The UI Apply reads the **sidebar input's current DOM/Dash value**, which after an out-of-band POST still holds
the pre-POST value until the `params-init-interval` seeding tick on a fresh load (the mechanism W3 step 5 itself
relies on). Without a reload between the POST and the Apply, the clamp cannot be provoked. Add "reload the
dashboard and wait for the init tick" between steps 8 and 9.

(Additionally uncertain, flagged rather than asserted: whether `/api/set_params` will even persist an
out-of-range value, since the clamp lives client-side in `_apply_params_via_backend` and cascor validates
independently. The step should record the observed behaviour either way.)

---

### FE-8 — Degraded-state rows are declared MANUAL with no induction procedure — **minor**

See **CG-7**. Matrix §2.4 states badge states 3/4 "need an induced upstream fault — **MANUAL** in Phase 1"
without saying how to induce one; plan §7.1 (iv) and §7.3 name two induction procedures that appear in no
workflow. Both are cheap to write (`util/isolated_stack.bash` already owns cascor's pidfile and `stop_port`),
so this is a documentation gap, not a capability gap.

---

### FE-9 — Both documents treat the numeric wall as permanent; the shipped xfails name an un-xfail path — **minor**

Plan §2.2 lists numeric entry as a **non-goal** ("Structurally blocked") and T-7 / matrix §1.3 build the whole
AUTO-API doctrine on it. Both shipped xfail reasons, however, name a concrete route out:

```python
# test_apply_button_flow.py (xfail reason)
"Un-xfail via dash[testing]/dash_duo (Selenium send_keys), which needs
 selenium+multiprocess+chromedriver added to the env (deferred follow-up)."
# test_l3_native_setter_poc.py (xfail reason)
"Un-xfail path is dash_duo (Selenium send_keys); see the audit doc §5.3."
```

Given that Phase 3 builds a whole new local-only suite, and that ~40 of the matrix's 287 rows are AUTO-API
because of this wall (plus the entirety of FE-5), the plan should at least *evaluate and reject* the
`dash_duo` option rather than declare the constraint structural.

---

### FE-10 — W12 step 3 embeds a workflow that violates W12's own precondition — **minor**

W12's precondition is "LIVE lane, training **running** with cascade growth". Step 3 says "Trigger a
dataset/network reset (W6)" — but W6 is the cold-migration workflow, whose restart path is stop → await
stopped → start (`main.py:3426`, `reset` default True). Running W6 inside W12 terminates the run W12 depends
on, and steps 4-10 then execute against a fresh network. Either reorder (make step 3 the last step) or state
the expected post-reset state.

---

## 6. Suspected inventions

**Headline negative result (verified pass).** A mechanical reverse sweep found **no invented identifiers**:

```
### E2E-CLICK-BY-CLICK-TEST-MATRIX.md: 300 distinct kebab tokens; 0 NOT found in canopy src
### E2E-FRONTEND-VALIDATION-PLAN.md:    25 distinct kebab tokens; 0 NOT found in canopy src
### E2E-CLICK-BY-CLICK-TEST-MATRIX.md:  76 distinct symbol tokens; 2 NOT found  (add_api_route, include_router
                                                                                — both used as evidence of ABSENCE)
```

The plan's 24 unresolved symbol tokens are, with one exception, *proposed future artifacts* (18 `test_*` names,
the `ui_live` marker, `JUNIPER_E2E_CANOPY_URL`, `JUNIPER_RECURRENCE_PORT`, Playwright's `to_be_visible`) —
legitimately absent from today's source. The exception is IV-1.

---

### IV-3 — "27 fields" attributed to the Apply POST — **major**

Covered in full as **CN-4**. Restated here because it is a claim about behaviour, not a citation slip: the
matrix asserts the Apply button POSTs 27 fields; the shipped code posts 25 and its comments name the three
deliberate exclusions. Listed as an invention because 27 is the count of a *different* list
(`comparisons`, `dashboard_manager.py:6883-6909`) and does not describe the surface it is attached to.

### IV-1 — `_status_bar_display_fields` does not exist — **minor**

**Location**: plan §7.3 ("plus a pure-unit pin on `_status_bar_display_fields` mapping if Phase 2 touches it").

```
$ grep -rn '_status_bar_display_fields' juniper-canopy/src/
(no matches — exit 1)
$ grep -rn 'def _counter_displays' juniper-canopy/src/frontend/dashboard_manager.py
5996:    def _counter_displays(status):
```

The real helper is `_counter_displays` (which the matrix cites correctly at §2.3 and `:6032-6042`). The plan
names a symbol that has never existed in this repository.

### IV-2 — `/api/remote/*` described as UI-exercised — **minor**

Covered as **CG-8**. Zero frontend callers; five registered routes.

### IV-4 — "24 `dbc.Tooltip`s … 23 parameter inputs" — **minor**

Covered as **CN-5**. Actual: 23 tooltips, 22 parameter controls.

### IV-5 — `dataset-plotter-import-url-input` "`type` is text" — **minor**

Covered as **CN-6**. Actual: `type="url"` (`dataset_plotter.py:249`).

### IV-6 — "the twelve tests named in §7" — **minor**

Covered as **CN-7**. Actual: 18 `ui_live` + 1 demo.

---

### Explicitly verified as NOT inventions (spot-checked because they are load-bearing)

| Claim | Verdict |
|---|---|
| T-1: `JUNIPER_CANOPY_PORT` is ignored; canopy binds 8050 | **VERIFIED TRUE** — zero repo-wide matches; `ServerSettings.port = 8050` (`settings.py:118-122`) under `env_nested_delimiter="__"`, `extra="ignore"` (`:188-195`). Canopy's own UI conftest already uses `JUNIPER_CANOPY_SERVER__PORT`. |
| T-2: cascor-unreachable → silent demo fallback, `/v1/health` still `"ok"` | **VERIFIED TRUE** — `main.py:330-336` (`create_backend(demo_mode=True)`); health body returns `"status": "ok"` with `"demo_mode": backend.backend_type == "demo"` and `"juniper_data_available"` (`:1059-1069`). The honest gate is correctly specified. |
| T-3/T-5: adapter import on the weight-oriented branch; failure → `dash.no_update` | **VERIFIED TRUE** — `dashboard_manager.py:6456-6469`: graph-format passthrough guarded by `"input_units" in topology`, then unconditional `from backend.cascor_service_adapter import CascorServiceAdapter`, wrapped in `except Exception: … return dash.no_update`. |
| T-6: `POST /api/train/start` defaults `reset=False` and carries browser-control auth | **VERIFIED TRUE** — `main.py:3246-3247`. |
| T-7: both numeric proofs are **strict** xfails | **VERIFIED TRUE** — `strict=True` in both. |
| T-9: `/api/set_params` is not in the auth-gated set | **VERIFIED TRUE** — `@app.post("/api/set_params")` at `main.py:3640` has no `dependencies=`. |
| T-16 / D-8: recurrence hardcoded `status="live"`; `model_is_trainable` gates on status only | **VERIFIED TRUE** — `model_registry.py:188` and `:232-247`; the contradicting docstring is `backend/__init__.py:116-118`. |
| T-20: UI tests `--ignore`d from the default run; `ui` marker registered | **VERIFIED TRUE** — `pyproject.toml:352` (`--ignore=src/tests/ui`), marker at `:368`. |
| D-0: `/api/network/topology` is not a registered route | **VERIFIED TRUE** — absent from the `@app.<verb>` inventory; fetched at `network_editor_panel.py:516`. |
| D-2: `nn-init-output-weights-dropdown` absent from the dirty-tracking Inputs but sent on Apply | **VERIFIED TRUE** — Input list `dashboard_manager.py:4390-4423` (13 NN + 10 CN + 3, no init-output-weights); payload key at `:7002`. |
| D-3: in-metrics replay base tick is 1000 ms | **VERIFIED TRUE** — `metrics_panel.py:566` (`interval=1000`) and `:1034-1035` (`interval = 1000 / speed`). |
| §3.3: the topology rebuild callback takes 12 Inputs | **VERIFIED TRUE** — `network_visualizer.py:344-356`. |
| §5.2 A-4: `TAB_SIDEBAR_CONFIG` covers 12 of 15 tabs; `TAB_SIDEBAR_WIDTH` covers 15 | **VERIFIED TRUE** — 12 keys (missing `evolution`, `replay`, `network-editor`); `ui_standards.py:37-56` lists all 15. `SIDEBAR_SECTION_IDS` = 14. |
| §3.9/§3.12/§3.13 refresh intervals 10 000 / 5 000 / 10 000 ms | **VERIFIED TRUE** — `hdf5_snapshots_panel.py:53`, `redis_panel.py:50`, `cassandra_panel.py:55`. |
| §3.14: 5 accordion items, `always_open=True`, `start_collapsed=True` | **VERIFIED TRUE** — `tutorial_panel.py:46-77`. |
| Plan §8.1: "11 files / 21 test functions" under `src/tests/ui/` | **VERIFIED TRUE** — 11 `test_*.py`, 21 `def test_` functions. |
| Plan §4.3: `juniper-cascor-client>=0.7.0` floor and installed version | **VERIFIED TRUE** — `pyproject.toml:162`; `/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/juniper_cascor_client-0.7.0.dist-info` present. |
| Plan §11 D-3: `hidden_units` min 0 / max 10000 / default 1000 | **VERIFIED TRUE** — `settings.py:113`. |

---

## 7. Recommended corrections (mechanically applicable)

Ordered so the three blockers land first. Each is a self-contained edit; none requires re-deriving either
document.

**Blockers — must land before owner approval**

1. **CN-1** — Adopt the matrix's `W1`-`W13` as the canonical workflow namespace. Rewrite plan §3.3 (the
   workflow roster), §6.2 (execution order), §8.4 (suite composition, "Workflows" row) and §13 A-3
   (`W-1 … W-12` → `W1 … W13`) against it. Alternatively rename the plan's to `PW-1 … PW-12` and add a
   mapping table; the first option is cheaper.
2. **FE-1** — In matrix §2.5: state `enable_ws_control_buttons` **defaults `True`** (`settings.py:349`); split
   each of the 6 button rows into a WS-primary expectation (frame on `/ws/control`) and a REST-fallback
   expectation; correct the handler citations for the default path (the clientside JS at
   `dashboard_manager.py:110-260`, not `:6594-6659`); add `enable_ws_control_buttons` to the plan §8.5 run
   header; and add a Phase-1 note on how to force each transport.
3. **FE-2** — Add `-m "not ui_live"` to `Makefile:24` (`test-ui`) and put that edit in PR-C-H's scope (plan
   §10); or place the live suite outside `src/tests/ui/` entirely and adjust the `--ignore` instead.

**Major**

4. **CN-3** — Add a leading `#` column (stable ids, e.g. `M-3.9-12`) and a trailing `status` column to every
   §2/§3 table (287 rows), then fix plan §9's screenshot convention and A-5 to reference them.
5. **CN-2** — Publish one status vocabulary. Recommended union: `PASS` / `FAIL` / `BLOCKED` / `N-A` /
   `DEAD-EXPECTED` / `DIVERGENCE`, with `DEAD-EXPECTED` kept as *both* an automation class and a terminal
   status (the matrix's §1.3 semantics already define the pass condition). Remove `UNTESTED` from plan §6.2 or
   add it to §9.
6. **CN-4 / IV-3** — Change "27 fields" → "25 fields" in matrix §2.9 and W3 step 3, and add a parenthetical
   that the shipped test body carries 27 (a superset with the three canopy-local keys) so the executor is not
   surprised. Consider a follow-up canopy issue for the stale comment at
   `src/tests/ui/test_param_roundtrip_visible.py:34-35` ("all 28 fields").
7. **CG-1** — Add `/api/snapshots/{id}/history/dataset_swaps` to matrix §1.6 and plan §3.4; add a W7 step
   after 15 asserting the per-snapshot fetch.
8. **CG-3** — Add a WS endpoint inventory to matrix §1.6 (`/ws/training` :634, `/ws/control` :777, `/ws`
   :3147, with which surface uses which) and define the **WS** verify method concretely
   (`Network.webSocketFrameSent/Received` via CDP).
9. **CG-4 / FE-5** — Add a §2.10 sub-table with one row per restart-modal granular field (11 rows), mark the
   10 numeric ones `AUTO-API (seed-only)` with an explicit note that the *modify* half is not drivable, and
   add a W6 sub-step exercising the seeding assertion.
10. **CG-5** — Correct matrix §6.3's seven unsupported mappings: either add the missing workflow steps (WS
    badge → W13; a tooltip hover → W13; network-info collapse → W1; pin/unpin → W3 or W13; the CN triple
    validator → W3; sidebar visibility/width → W13; a staging-failure arm → W6) or change the mapping cell to
    `— (rows only)`. **Adding the steps is preferred** — six of the seven are 1-2 lines.
11. **CG-7 / FE-8** — Add a W14 "Degraded / outage probes" workflow: (a) stop cascor mid-run → assert the
    classified status label and the badge downgrade; (b) induce `stream_health.overall == "degraded"` → badge
    state 4; (c) run with `juniper-cascor-client` uninstalled → assert the topology panel fails loudly, not
    stale. Reference it from plan §7.1 (iv) and §7.3 and from matrix §6.2 FA-1/FA-3.
12. **FE-3** — Add to matrix W8 a Preconditions line: "requires plan §4.5's `--with-recurrence` leg; without
    it every step is `N-A (no recurrence service)`", and add the same conditional to §6.4's lane table.
13. **FE-4** — Replace plan §4.5's self-URL fallback with a stub recurrence service under `util/ad-hoc/`, or
    with a plain `N-A` for W8. State that pointing the URL at canopy re-creates the process-global backend
    (`backend/__init__.py:130-134`).
14. **FE-6** — Insert a W5 step between 10 and 11 reading `#network-visualizer-input-count` and
    `#network-visualizer-hidden-count` and stating that the append vector length is their sum.

**Minor**

15. **CG-2** — Add `POST /api/ws_latency` (`assets/ws_latency.js:47-50`) to matrix §1.6 with an "expected
    background traffic" note so W13's console/network sweep does not flag it.
16. **CG-6** — Add a pin/unpin gesture to W3 (or W13) so the Parameters-tab pin feature has a click path.
17. **CG-8 / IV-2** — Change plan §3.4's heading to "Canopy `/api/*` route surface (registered)" and mark
    `/api/remote/*` as "registered; no frontend caller — out of scope".
18. **CG-9** — Either enumerate the USER_MANUAL / REFERENCE behavioural claims (a numbered list in plan §11) or
    restate A-2 as "every claim in the §11 drift table plus any found in Phase 1".
19. **CN-5 / IV-4** — "24 tooltips … 23 parameter inputs" → "23 tooltips … 22 parameter controls +
    `apply-params-button`".
20. **CN-6 / IV-5** — "`type` is text" → "`type=\"url\"` — text-like; the wall is specific to `type=\"number\"`".
21. **CN-7 / IV-6** — "the twelve tests named in §7" → "the eighteen `ui_live` tests named in §7 (plus one
    demo-lane test)". Re-check the PR-C-F budget.
22. **CN-8** — Fix the plan §15 recurrence settings path to
    `juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py`.
23. **CN-9** — Change the optional recurrence leg from 8211 to a non-operator port (8203 suggested) and note
    that 8211 is recurrence's deploy **host** port per `settings.py:152`; reconcile §15's "port 8210".
24. **CN-10** — Align the two headers (`**Date**` vs `**Last Updated**`) and have matrix §7 name both audit
    reports by filename.
25. **CN-11** — Add "Prerequisite: plan Phase 0 / T-1 (canopy must actually bind 8051)" to matrix §0. Consider
    citing `src/tests/ui/conftest.py:37-39` in plan T-1 — canopy's own conftest already uses the nested form,
    which is the strongest in-repo evidence the fix is right.
26. **CN-12** — Change plan §8.2 item 1 "Both conftests" → "all three demo pins" and enumerate
    `conftest.py:12`, `src/tests/conftest.py:23`, `src/tests/ui/conftest.py:38`; note that
    `src/tests/conftest.py` also pins `JUNIPER_DATA_URL` to the **operator** port 8100.
27. **CN-13** — Mark matrix §2.9's 429 arm `N-A (limiter off by default; server-side self-calls carry the
    internal token)`.
28. **FE-7** — Insert "reload the dashboard and wait for the `params-init-interval` tick" between W3 steps 8
    and 9.
29. **FE-9** — Add a line to plan §2.2 / T-7 evaluating (and, if rejected, rejecting on the record) the
    `dash[testing]` / `dash_duo` Selenium `send_keys` un-xfail path both shipped xfails name.
30. **FE-10** — Reorder W12 so the reset step is last, or state the expected post-reset state for steps 4-10.

---

## 8. Items that could not be checked

| Item | Why |
|---|---|
| Whether the matrix's 287 rows are *behaviourally* correct (i.e. whether each "expected result" matches runtime) | Requires a running isolated stack, which plan T-1 establishes cannot start today. This audit verified structure, existence, consistency and drivability only. |
| Whether `POST /api/set_params` accepts the dashboard's 25-key body (i.e. whether `SetParamsRequest` has required fields the body omits) | Would require running canopy; the field is `body: SetParamsRequest` (`main.py:3641`) and the model was not fully expanded. Recorded as uncertain, not asserted. Relevant only to CN-4's severity, not its truth. |
| Whether the JS snapshot context menu (matrix §3.9 "right-click … **MANUAL** (native menu)") is Playwright-drivable | Static reading of `assets/snapshot_context_menu.js` suggests it is a JS-rendered menu (therefore drivable), but confirming needs a browser. The matrix's MANUAL classification is conservative and safe. |
| Line-number accuracy of the ~700 `file:line` citations | Explicitly out of scope — owned by the parallel grounding audit. Spot-checks in §6's verification table were all correct. |
| Whether the plan's Phase-2 PR budget (3-10 canopy fixes) is realistic | Depends on Phase-1 outcomes that do not exist yet. The plan itself scopes it as budget-ranged. |
| juniper-canopy CI behaviour of the proposed `ui_live` marker exclusion | Requires a CI run; the workflow text was read (`ci.yml:402`) and the change is coherent, but FE-2 shows the Makefile half was missed, so a dry run before PR-C-H merges is advisable. |

---

## Appendix — Independent derivation (produced before the audited documents were opened)

**Source of truth**: `/home/pcalnon/Development/python/Juniper/juniper-canopy` at `main` / `e8309ec`, working
tree clean (`git status --porcelain` empty). Derivation scripts: an AST walker over `src/frontend/**/*.py`
extracting every `Call` node carrying an `id=` keyword (471 hits), a second walker extracting every
`requests.* / session.* / httpx.*` call with its first argument's source segment (72 hits), and a regex
inventory of `@app.<verb>("…")` in `src/main.py`.

### A.1 Tab roster (15) — `dashboard_manager.py:2176-2252`

| # | `tab_id` | `label=` | Renderer (component instance) | Cascade-only |
|---|---|---|---|---|
| 1 | `metrics` | Training Metrics | `MetricsPanel` (`metrics-panel`) | no |
| 2 | `candidates` | Candidate Metrics | `CandidateMetricsPanel` (`candidate-metrics-panel`) | **yes** |
| 3 | `topology` | Network Topology | `NetworkVisualizer` (`network-visualizer`) | **yes** |
| 4 | `evolution` | Network Evolution | `NetworkEvolution` (`network-evolution`) | **yes** |
| 5 | `boundaries` | Decision Boundary | `DecisionBoundary` (`decision-boundary`) | **yes** |
| 6 | `dataset` | Dataset View | `DatasetPlotter` (`dataset-plotter`) | no |
| 7 | `workers` | Workers | `WorkerPanel` (`worker-panel`) | **yes** |
| 8 | `parameters` | Parameters | `ParametersPanel` (`parameters-panel`) | no |
| 9 | `snapshots` | Snapshots | `HDF5SnapshotsPanel` (`hdf5-snapshots-panel`) | no |
| 10 | `replay` | Replay | `ReplayPlayerPanel` (`replay-player-panel`) | no |
| 11 | `network-editor` | Network Editor | `NetworkEditorPanel` (`network-editor-panel`) | no |
| 12 | `redis` | Redis | `RedisPanel` (`redis-panel`) | no |
| 13 | `cassandra` | Cassandra | `CassandraPanel` (`cassandra-panel`) | no |
| 14 | `tutorial` | Tutorial | `TutorialPanel` (`tutorial-panel`) | no |
| 15 | `about` | About | `AboutPanel` (`about-panel`) | no |

`_CASCADE_ONLY_TAB_IDS = frozenset({"candidates", "topology", "evolution", "boundaries", "workers"})`
(`dashboard_manager.py:387`); filtered by `_visible_tabs` (`:2254-2268`) when `model_class == "one_shot"`;
`component_id` values confirmed at the instantiation site `dashboard_manager.py:529-575`.

### A.2 Interactive-control checklist — 181 constructions → **186 distinct id families**

Component-type census of all 471 `id=`-bearing constructions in `src/frontend/**`:

```
120 html.Div   64 dcc.Store    57 dbc.Button   48 html.Span   36 dbc.Input
 15 dbc.Collapse  14 dcc.Dropdown  13 dcc.Interval  13 dcc.Graph   9 html.H6
  7 dbc.Modal    6 dbc.RadioItems  6 dbc.Badge   5 html.H2   5 dcc.Slider
  5 dbc.Alert    4 dcc.Checklist   4 dbc.DropdownMenuItem  3 dbc.Select  3 dbc.Progress
  3 dbc.Checklist  2 html.Hr  2 html.H5  2 dcc.RadioItems  2 dbc.Textarea  2 dbc.Tabs
  2 dbc.Switch   2 dbc.ListGroup  2 dbc.Col  2 dbc.Checkbox  2 dbc.CardHeader
  1 each: html.Ul, html.Tbody, html.Table, html.Code, html.Button, dcc.Upload,
          dcc.RangeSlider, dbc.ModalBody, dbc.CardBody, dbc.Card, dbc.Accordion
```

Filtering to interactive types (Button / Input / Dropdown / Select / Slider / RangeSlider / RadioItems /
Checklist / Checkbox / Switch / Upload / Graph / Modal / Textarea / Tabs / Collapse / DropdownMenuItem /
Accordion / html.Button) gives **181 constructions**. Two of those (`dashboard_manager.py:5161`, `:5189`) are
the shared `_num` helper and expand to **10** concrete restart-granular ids; four (`:2616`, `:2618`, `:2627`,
`:2629`) are the `field_id` generator-schema widgets and collapse to **one** pattern family. Net:
**181 − 2 + 10 − 4 + 1 = 186** distinct interactive id families.

Per component (resolved `component_id` prefixes):

**`dashboard_manager.py` (74 constructions → 82 ids)**
`dark-mode-toggle`, `start-button`, `pause-button`, `resume-button`, `stop-button`, `reset-button`,
`nn-subsection-collapse`, `nn-max-iterations-input`, `nn-max-total-epochs-input`, `nn-output-epochs-input`,
`nn-init-output-weights-dropdown`, `nn-optimizer-type-dropdown`, `nn-activation-function-dropdown`,
`nn-learning-rate-input`, `nn-max-hidden-units-input`, `ctx-multi-node-collapse`,
`nn-multi-node-layers-checkbox`, `ctx-growth-triggers-collapse`, `nn-growth-trigger-radio`,
`nn-growth-preset-epochs-input`, `nn-growth-convergence-threshold-input`, `nn-patience-input`,
`nn-model-change-button`, `ctx-spiral-dataset-collapse`, `nn-spiral-rotations-input`, `nn-spiral-number-input`,
`nn-dataset-elements-input`, `nn-dataset-noise-input`, `nn-dataset-type-dropdown`, `apply-dataset-button`,
`live-dataset-switch-button`, `cn-subsection-collapse`, `cn-pool-size-input`, `cn-correlation-threshold-input`,
`cn-selected-candidates-input`, `ctx-pool-training-collapse`, `cn-training-complete-radio`,
`cn-training-iterations-input`, `cn-training-convergence-threshold-input`, `cn-patience-input`,
`cn-multi-candidate-checkbox`, `cn-candidate-selection-radio`, `cn-top-candidates-input`,
`cn-random-candidates-input`, `restart-with-new-dataset-button`, `cancel-pending-dataset-button`,
`apply-params-button`, `network-info-collapse`, `network-info-details-collapse`,
`experimental-functions-toggle`, `visualization-tabs`, `welcome-modal`, `welcome-modal-close`,
`live-switch-modal`, `live-switch-fallback-button`, `live-switch-accept-button`, `live-switch-cancel-button`,
`restart-confirm-modal`, `restart-start-fresh-toggle`, `restart-granular-toggle`, `restart-granular-collapse`,
`restart-cancel-button`, `restart-confirm-button`, `model-selection-modal`, `model-search-input`,
`model-selection-modal-close`, `{"type":"model-select-btn","index":<key>}`,
`{"type":"nn-gen-param","name":<field>}` (Checkbox / Dropdown / numeric Input / text Input variants),
`restart-ds-type`, **`restart-ds-samples`**, **`restart-ds-noise`**, **`restart-ds-rotations`**,
**`restart-ds-spirals`**, **`restart-p-nn-learning-rate`**, **`restart-p-nn-max-hidden-units`**,
**`restart-p-nn-patience`**, **`restart-p-cn-pool-size`**, **`restart-p-cn-selected`**,
**`restart-p-cn-corr-thresh`**  *(bold = the 10 fields with no matrix row, CG-4)*

**`dataset_plotter.py` (31)** — `-generate-btn`, `-dataset-selector`, `-load-selected-btn`, `-split-selector`,
`-generate-modal`, `-modal-tabs`, `-gen-samples`, `-gen-spirals`, `-gen-rotations`, `-gen-noise`,
`-gen-confirm`, `-import-file-upload`, `-import-file-confirm`, `-import-url-input`, `-import-url-confirm`,
`-gen-cancel`, `-seq-mode`, `-seq-window-single`, `-seq-signal-select`, `-seq-signal-single`,
`-seq-window-multi`, `-seq-arrange`, `-seq-target-toggle`, `-seq-grid-toggle`, `-scatter-plot`,
`-distribution-plot`, `-seq-target-plot`, `-seq-char-collapse`, `-seq-char-dt-hist`, `-seq-char-target-dist`,
`-seq-grid-plot`

**`metrics_panel.py` (18)** — `-layout-name-input`, `-save-layout-btn`, `-layout-dropdown`, `-load-layout-btn`,
`-delete-layout-btn`, `-replay-start`, `-replay-step-back`, `-replay-play`, `-replay-step-forward`,
`-replay-end`, `-speed-1x`, `-speed-2x`, `-speed-4x`, `-replay-slider`, `-display-mode`, `-window-size`,
`-loss-plot`, `-accuracy-plot`

**`hdf5_snapshots_panel.py` (16)** — `-create-name`, `-create-description`, `-create-button`,
`-refresh-button`, `-restore-modal`, `-restore-cancel`, `-restore-confirm`, `-history-toggle`,
`-history-collapse`, `{"type":"…-swap-restore-pre-btn","index":i}`,
`{"type":"…-swap-restore-post-btn","index":i}`, `{"type":"…-view-btn","index":<id>}`,
`{"type":"…-snapshot-op-btn","index":<id>,"op":"restore"|"replay"|"resume"|"retrain"}` (4)

**`network_editor_panel.py` (14)** — `-remove-modal`, `-remove-snapshot-first`, `-remove-cancel`,
`-remove-confirm`, `-add-weights`, `-add-bias`, `-add-activation`, `-add-submit`, `-remove-idx`,
`-remove-submit`, `-patch-target`, `-patch-idx`, `-patch-values`, `-patch-submit`

**`replay_player_panel.py` (7)** — `-play-btn`, `-pause-btn`, `-stop-btn`, `-scrubber`, `-speed`, `-range`,
`-swap-events-graph`

**`network_visualizer.py` (6)** — `-layout-selector`, `-show-weights`, `-display-mode`, `-view-mode`,
`-depth-slider`, `-graph`

**`decision_boundary.py` (4)** — `-resolution-slider`, `-show-confidence`, `-refresh-btn`, `-plot`

**`candidate_metrics_panel.py` (4)** — `-pool-collapse`, `-loss-plot`, `-history-collapse`,
`{"type":"…-history-pool-collapse","index":<epoch>}`

**`tutorial_panel.py` (2)** — `walkthrough-launch-btn`, `tutorial-panel-accordion`
**`network_evolution.py` (2)** — `-clear-btn`, `-weight-norms`
**`about_panel.py` (2)** — `-system-info-toggle`, `-system-info-collapse`
**`parameters_panel.py` (1)** — `{"type":"param-pin","key":<param>}`

**Read-only panels with no interactive control** (badges / tiles / intervals only): `worker_panel.py`,
`redis_panel.py`, `cassandra_panel.py`, `connection_indicator.py`.

**Graph-event surfaces (Dash Inputs only — no `hoverData` anywhere):**

```
network_visualizer.py:294   Input(f"{cid}-graph", "relayoutData")
network_visualizer.py:552   Input(f"{cid}-graph", "clickData")
network_visualizer.py:553   Input(f"{cid}-graph", "selectedData")
metrics_panel.py:685        Input(f"{cid}-loss-plot", "relayoutData")
metrics_panel.py:686        Input(f"{cid}-accuracy-plot", "relayoutData")
```

**Pattern-matched id families (6):** `nn-gen-param` (`dashboard_manager.py:2613`), `model-select-btn`
(`:2866`), `param-pin` (`parameters_panel.py:118`), `hdf5-snapshots-panel-{view-btn, snapshot-op-btn,
swap-restore-pre-btn, swap-restore-post-btn}` (`:922/:937-952/:709/:720`),
`candidate-metrics-panel-history-pool-{header, collapse}` (`:679/:694`).

**Status-bar element inventory (`dashboard_manager.py:711-842`):** `status-indicator` (:716),
`top-status-display` (:731), `top-phase-display` (:750), `top-epoch-display` (:773) — labelled **"Step: "**
(:769), `top-hidden-units-display` (:799) inside `status-iteration-segment` (:808) — labelled
**"Hidden Units: "** (:795), `latency-display` (:813), `ws-connection-indicator`
(`connection_indicator.py:34`), `connection-status` (:842, `display:none` sink), `train-gate-notice` (:857).

**`dcc.Interval` census (13):** `fast-update-interval` (:1757), `slow-update-interval` (:1758),
`params-init-interval` (:1760, `max_intervals=1`), `apply-watchdog-interval` (:1769),
`metrics-panel-update-interval` (:551), `metrics-panel-stats-update-interval` (:552, 5000 ms),
`metrics-panel-replay-interval` (:564, 1000 ms), `hdf5-snapshots-panel-refresh-interval` (:360, 10000 ms),
`candidate-metrics-panel-*` (:214), `cassandra-panel-interval` (:190, 10000 ms),
`redis-panel-refresh-interval` (:317, 5000 ms), `replay-player-panel-weight-drain` (:129, 500 ms),
`network-editor-panel-fsm-poll` (:135, 2000 ms).

### A.3 Frontend-called endpoint list (derived from 72 AST-extracted call sites)

Every path below is invoked from `src/frontend/**`. `file:line` is the call site.

| Method | Path | Call site |
|---|---|---|
| GET | `/api/state` | `candidate_metrics_panel.py:414`, `metrics_panel.py:1273`, `dashboard_manager.py:5262/:7038/:7249` |
| GET | `/api/status` | `network_editor_panel.py:492`, `dashboard_manager.py:4734/:5707/:5958/:6190` |
| GET | `/api/stream_health` | `dashboard_manager.py:7234` (`url` @ `:7233`) |
| GET | `/api/metrics/history?limit=` | `dashboard_manager.py:6376` (`url` @ `:6375`) |
| GET | `/api/network/stats` | `metrics_panel.py:1194`; `dashboard_manager.py:6286` (`url` @ `:6285`) |
| GET | `/api/topology` | `dashboard_manager.py:6440` (`url` @ `:6439`) |
| GET | `/api/topology/raw` | `dashboard_manager.py:6478` (`url` @ `:6477`) |
| GET | **`/api/network/topology`** | `network_editor_panel.py:516` — **not a registered route (D-0)** |
| GET | `/api/dataset` | `dashboard_manager.py:6545/:6585` (`url` @ `:6544/:6584`) |
| GET | `/api/decision_boundary[?resolution=]` | `dashboard_manager.py:6566` (`url` @ `:6563-6565`) |
| POST | `/api/dataset/generate` | `dashboard_manager.py:4021` (`url` @ `:4014`), `:4040` |
| POST | `/api/dataset/import-file` | `dashboard_manager.py:4080` (`url` @ `:4078`) |
| POST | `/api/dataset/import-url` | `dashboard_manager.py:4104` (`url` @ `:4103`) |
| GET | `/api/dataset/generators` | `dashboard_manager.py:2547`; `dataset_plotter.py` (via `{origin}/api/dataset/generators`) |
| POST | `/api/stage_dataset` | `dashboard_manager.py:2680`, `:5383` |
| DELETE | `/api/cancel_pending_dataset` | `dashboard_manager.py:4697` |
| POST/DELETE | `/api/live_dataset_swap` | `dashboard_manager.py:5793` / `:5845` |
| GET | `/api/history/dataset_swaps` | `dashboard_manager.py:5577` |
| GET | **`/api/snapshots/{id}/history/dataset_swaps`** | `dashboard_manager.py:5686` — **absent from both docs (CG-1)** |
| GET/POST | `/api/admin/experimental_functions` | `dashboard_manager.py:4783` / `:4818` |
| POST | `/api/model/select` | `dashboard_manager.py:2705` |
| GET | `/api/train/status` | `dashboard_manager.py:2341` |
| POST | `/api/train/{start,pause,stop,resume,reset}` | `dashboard_manager.py:6647` (`url` @ `:6640`, `button_map` @ `:6622-6628`) — **but see FE-1** |
| POST | `/api/train/restart` | `dashboard_manager.py:5450` |
| POST | `/api/set_params` | `dashboard_manager.py:7034` |
| GET/POST | `/api/v1/snapshots` | `hdf5_snapshots_panel.py:462` / `:406`; `network_editor_panel.py:695` |
| GET | `/api/v1/snapshots/{id}` | `hdf5_snapshots_panel.py:489` |
| GET | `/api/v1/snapshots/history` | `hdf5_snapshots_panel.py:605` |
| POST | `/api/v1/snapshots/{id}/{restore,replay,resume,retrain}` | `hdf5_snapshots_panel.py:555` |
| POST | `/api/v1/snapshots/{id}/replay/control` | `replay_player_panel.py:355` |
| POST/DELETE | `/api/v1/network/hidden-units[/{idx}]` | `network_editor_panel.py:603` / `:703` (via `_post_json` @ `:433-446`) |
| PATCH | `/api/v1/network/weights` | `network_editor_panel.py:758` |
| GET/POST | `/api/v1/metrics/layouts` | `metrics_panel.py:1521` / `:1552` |
| GET/DELETE | `/api/v1/metrics/layouts/{name}` | `metrics_panel.py:1597` / `:1641` |
| GET | `/api/v1/workers/{list,stats}` | `dashboard_manager.py:6503` / `:6527` |
| GET | `/api/v1/redis/{status,metrics}` | `redis_panel.py:374` / `:427` |
| GET | `/api/v1/cassandra/{status,metrics}` | `cassandra_panel.py:394` / `:453` |

**Browser-originated (JS assets, not Dash callbacks):**

| Method | Path | Call site |
|---|---|---|
| GET | `/api/csrf` | `assets/websocket_client.js:524` |
| POST | **`/api/ws_latency`** | `assets/ws_latency.js:50` — **absent from both docs (CG-2)** |
| WS | `/ws/control` | `assets/websocket_client.js:517` (`window.cascorControlWS`) — **CG-3 / FE-1** |

**Registered routes with no frontend caller** (therefore correctly out of a UI-coverage matrix, but listed by
the plan §3.4 as "exercised through the UI" — CG-8): `/api/remote/{status,connect,disconnect,start_workers,
stop_workers}`, `/api/statistics`, `/api/metrics`, `/api/health`, `/api/ws_browser_errors`.

**Canopy WebSocket routes** (`src/main.py`): `/ws/training` :634, `/ws/control` :777, `/ws` :3147.

### A.4 Primary user workflows implied by the wiring (derived independently)

1. **Training control** — `start|pause|resume|stop|reset-button` → (default) `/ws/control` frame, else
   `POST /api/train/<cmd>`; outcome surfaced only on failure via `training-control-outcome-alert`.
2. **Parameter apply** — 26 tracked controls → dirty gate (`:4385-4423`) → `apply-params-button` → blur-commit
   → `CascorPatchBounds` clamp → `POST /api/set_params` (25 keys) → verify against `/api/state` → toast.
3. **Dataset stage → cold restart** — `nn-dataset-*` + `{nn-gen-param}` → `apply-dataset-button` →
   `POST /api/stage_dataset` → `pending-dataset-banner` → `restart-with-new-dataset-button` →
   `restart-confirm-modal` (+ 11 granular fields) → `POST /api/train/restart`; cancel via
   `DELETE /api/cancel_pending_dataset`.
4. **Live (hot) swap** — `experimental-functions-toggle` (server-authoritative) **and** a running run gate
   `live-dataset-switch-button` → `live-switch-modal` → `POST /api/live_dataset_swap`; in-flight cancel via
   `DELETE`; history via `/api/history/dataset_swaps`.
5. **Snapshot ops** — create/list/detail; the 4-op pattern menu → shared confirm modal →
   `POST /api/v1/snapshots/{id}/{op}`; a successful `replay` also writes `replay-player-session` and switches
   `active_tab` to `replay`.
6. **Replay transport** — play/pause/stop/scrubber/speed/range → `POST …/replay/control`; weights drain into
   `replay-weight-buffer` on a 500 ms Interval, feeding the evolution weight-norms panel and the
   decision-boundary recompute.
7. **Model selection** — `nn-model-change-button` → `model-selection-modal` (+ `model-search-input`) →
   `{model-select-btn}` → `POST /api/model/select` → `model-class-store` → cascade-tab suppression.
8. **Network editing** — unlocked only when the cascor FSM reads `Investigating` (2 s poll of `/api/status`);
   append (`POST /api/v1/network/hidden-units`), remove (confirm modal → optional snapshot →
   `DELETE …/hidden-units/{idx}`), patch (`PATCH /api/v1/network/weights`).
9. **Metrics layouts** — save/load/delete against `/api/v1/metrics/layouts[/{name}]`, keyed on
   `metrics-panel-view-state`.
10. **Topology exploration** — layout / show-weights / node-graph⇄weight-matrix / 2-D⇄3-D / depth filter /
    click-select / box-lasso / relayout capture, over two stores fed by `/api/topology` and `/api/topology/raw`
    plus a WS `cascade_add` fast path.
11. **In-metrics replay** — a separate, purely client-side history scrubber (start/step/play/end/speed 1x-4x/
    slider) visible only when training is not running.
12. **Parameter pinning** — `{param-pin}` checkboxes on the Parameters tab → `pinned-params-store` (local) →
    `sidebar-pinned-card` / `-list` mirror.

---

*End of audit. Status: COMPLETE. No file in either audited document, and no file in `juniper-canopy`, was
modified by this audit; the only artifact written is this report.*
