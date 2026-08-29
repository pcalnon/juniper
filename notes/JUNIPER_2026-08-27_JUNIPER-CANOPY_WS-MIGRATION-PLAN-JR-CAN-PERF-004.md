# JR-CAN-PERF-004 — WebSocket migration plan for the canopy dashboard

**Project**: Juniper — juniper-canopy
**Author**: Paul Calnon
**Status**: PLAN (design of record) — no code changes proposed for immediate execution
**Created**: 2026-08-27
**Requirement**: [`JR-CAN-PERF-004`](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md) (PERF, P2, owner `can`)
**Triggered by**: the owner's 2026-08-26 disposition on **F-CANOPY-004** — *accept the freshness
contract now **and** schedule the WS migration* (the scheduled half; the contract half is already
written into the finding).

---

## 1. Why this exists

F-CANOPY-004 is ACCEPTED, not fixed. The owner accepted a measured freshness envelope and scheduled
this workstream to remove the architecture that produces it. That envelope, quoted verbatim from the
finding so this plan and the ledger cannot drift:

| surface class | contract | notes |
|---|---|---|
| clientside callbacks (WS badge, depth-slider reveal, theme) | immediate | no server round-trip |
| interaction-triggered server render (click, select, toggle) | **≤ 16 s**, typically 3–8 s | measured from the interaction, not from page load |
| fresh-session population (first paint of a panel after load) | **≤ 40 s**, typically 20–30 s | a shorter settle reports a working panel as dead |
| during-run steady-state polling surfaces | best-effort; **no freshness guarantee** | **this is the class JR-CAN-PERF-004 exists to fix** |

**The last row is the whole mandate.** The first three are acceptable and documented. The fourth is
not a latency figure at all — it is an admission that during a training run, the only time the
dashboard matters, canopy makes no promise about what it is showing.

### The mechanism, in one paragraph

Every interval-driven server callback does a synchronous self-call
`requests.get(self._api_url(...))` back into the *same* canopy server, so callbacks queue behind
their own server's request backlog. dash-renderer holds a hard-coded **12-slot** concurrency pool
(see `reference_dash_renderer_12_slot_starvation` and the remediation design's §12), so a lane whose
round-trip exceeds its own period permanently occupies slots and starves its siblings. Stages 1–3 of
the callback-starvation remediation (canopy#507 + #509 + #511) cut the envelope from *30 s–minutes*
to the numbers above by **gating and consolidating** the polling. This workstream removes it.

### What this plan is NOT

It is not a re-litigation of Stages 1–3. The remediation design
([`JUNIPER_2026-08-23_JUNIPER-CANOPY_CALLBACK-STARVATION-REMEDIATION-DESIGN.md`](JUNIPER_2026-08-23_JUNIPER-CANOPY_CALLBACK-STARVATION-REMEDIATION-DESIGN.md) §149)
already recorded the correct sequencing and it still holds:

> **Right long-term, wrong now.** … converting 13 panel pollers is a much larger change than Phase 2
> can absorb, and it does not help panels with no WS channel (redis, cassandra, snapshots). Should
> follow this work, not replace it.

Stages 1–3 shipped. This is the "follow" step, and the parenthetical is the central design
constraint: **a WS migration cannot cover every poller, so the plan must say which ones it does not
cover and what happens to them.**

---

## 2. Measured current state

Counted against `juniper-canopy` `9f6fac9` by walking `dm.app._callback_list` — not from
documentation, which has drifted before.

### 2.1 The twelve gated lanes

`_GATED_POLL_INTERVALS` (`src/frontend/dashboard_manager.py:453-470`) is the single source of truth
and is pinned by `tests/unit/frontend/test_poll_gating.py`. Two shared lanes, four dashboard-owned
per-tab lanes, six panel-owned lanes.

### 2.2 What actually rides them

| lane | period | server callbacks | clientside callbacks |
|---|---:|---:|---:|
| `fast-update-interval` | 1000 ms | **3** | 7 (the WS drain pump) |
| `slow-update-interval` | 5000 ms | 2 | 0 |
| `tabpoll-topology` | 5000 ms | 3 | 0 |
| `tabpoll-boundaries` | 5000 ms | 2 | 0 |
| `tabpoll-dataset` / `tabpoll-workers` | 5000 ms | 1 each | 0 |
| `candidate-metrics-panel-update-interval` | tab-gated | 1 | 0 |
| `metrics-panel-stats-update-interval` | 5000 ms | 1 | 0 |
| `cassandra-panel-interval` | tab-gated | 1 | 0 |
| `redis-panel-refresh-interval` | tab-gated | 1 | 0 |
| `hdf5-snapshots-panel-refresh-interval` | tab-gated | 1 | 0 |
| `network-editor-panel-fsm-poll` | 2000 ms | 1 | 0 |

**18 server-side interval-driven callbacks.** (The design doc's "13 panel pollers" predates the
per-tab lane split; use this table.)

**Note the `fast-update-interval` shape, because it is easy to misread**: 7 of its 10 callbacks are
*clientside* drains that pump the WS buffers. They are the migration's delivery mechanism, not its
targets. Only three server callbacks ride the 1 Hz lane: the unified status bar, the metrics-store
poll (already liveness-demoted by N8), and the button-timeout sweep — which is a timeout sweep, not
a data poller, and is not in scope at all.

### 2.3 What the WS bridge already delivers

`src/frontend/assets/ws_dash_bridge.js` registers **7** handlers on the cascor socket:
`metrics` (:217), `initial_metrics` (:255), `state` (:276), `topology` (:286), `cascade_add` (:309),
`event` (:321), `candidate_progress` (:331). These drain into six `dcc.Store` buffers
(`dashboard_manager.py:1892-1911`) plus `ws-liveness-store` and `ws-connection-status`.

The infrastructure is **already built and already load-bearing**. N8 made the metrics store
WS-primary: the REST poll returns `no_update` while `ws-liveness-store.metrics_live` is fresh, and
re-engages within `WS_LIVENESS_WINDOW_MS` when the stream goes quiet. **That is the pattern this
plan generalises — it is not a new idea, it is an existing, tested, live one.**

---

## 3. The classification that drives everything

A poller can be migrated only if cascor already broadcasts the state it polls. Sorting the 18 by
that test is the plan's central act, because it determines both scope and the honest answer to
"what will still be slow afterwards".

### 3.1 Convertible — a WS channel exists

| poller | WS source | current status |
|---|---|---|
| metrics store | `metrics` / `initial_metrics` | **already WS-primary (N8)** — the reference implementation |
| topology store | `topology` + `cascade_add` | WS push already takes priority; REST is the fallback |
| unified status bar | `state` | polls at 1 Hz; `ws-state-buffer` exists with 1 consumer |
| metrics-panel training state | `state` | same source as the status bar |
| network-editor FSM poll | `state` (`fsm_state`) | polls `/api/status` at 2 Hz for one field |
| candidate metrics | `candidate_progress` | drain exists in JS; the store's Dash consumer was removed in N1 |
| dataset-swap events | `ws-dataset-swap-buffer` | already merged with the slow poll, with dedupe |

### 3.2 NOT convertible — no WS channel exists

| poller | why not |
|---|---|
| raw topology (weight-matrix heatmap) | cascor does not broadcast raw weight matrices — only the structural `topology` event. Documented as **GAP-WS-25**; REST is the only source. |
| decision boundary | no channel; the mesh is computed on request at a chosen resolution |
| workers roster / stats | no channel; cascor's registry is REST-only |
| redis panel | infrastructure telemetry, not training state |
| cassandra panel | infrastructure telemetry, not training state |
| HDF5 snapshots | filesystem/asset-store listing, not an event stream |

**Six pollers cannot be migrated without new cascor broadcast channels**, which is a juniper-cascor
workstream, not this one. Three of the six (redis, cassandra, snapshots) arguably should *never* be
WS — they are not real-time surfaces and a 5 s tab-gated poll is the correct design for them.

### 3.3 The honest consequence

**Migrating everything convertible does not empty the polling lanes.** Six pollers remain, and the
"no freshness guarantee" row of the contract continues to apply to them. Any claim that
JR-CAN-PERF-004 "fixes F-CANOPY-004" is therefore wrong as stated, and this plan should be cited
against it. What it can honestly promise:

- every **training-state** surface becomes event-driven and sub-second;
- the 1 Hz lane loses its last two data pollers, so the pool stops being contended at 1 Hz;
- the remaining six are tab-gated, low-rate, and non-real-time by nature, so their staleness stops
  being a *training-visibility* problem and becomes an ordinary refresh delay.

That is a real and sufficient outcome. It is just not "no more polling".

---

## 4. Proposed phasing

Each phase is independently shippable and independently revertible. **No phase deletes a REST
fallback** — see §5.

### Phase 0 — prerequisites (blocking)

1. **F-CANOPY-037 must be merged** (juniper-canopy#531). It removes the topology rebuild from the
   1 Hz metrics store's consumer set. Migrating the status bar onto WS while an 8-output rebuild is
   still chained to a 1 Hz store would just move the starvation.
2. **F-CANOPY-038 must be diagnosed.** The Stage 2 no-op-write suppression is present at
   `dashboard_manager.py:6724-6725` and demonstrably not biting (33 of 34 identical writes went out
   anyway). Until we know why, we cannot predict whether a WS-fed store will suppress correctly
   either — the same equality check guards both paths. **This is the cheapest and highest-value
   next probe**, and #531 merging is itself a discriminator for one of its candidate mechanisms.

### Phase 1 — the `state` fan-out (highest value, lowest risk)

Three separate pollers all read the same `/api/status` payload: the unified status bar (1 Hz), the
metrics-panel training state (5 s), and the network-editor FSM poll (2 Hz for a single field). One
`state` WS event already arrives and already lands in `ws-state-buffer`.

Convert all three to the **N8 posture**, verbatim: WS-primary append, liveness-gated REST demotion,
REST re-engagement the instant the stream goes stale.

Removes **three** server pollers including both remaining 1 Hz data pollers, and the 2 Hz FSM poll
that exists to watch one string.

### Phase 2 — candidate metrics

Re-establish a Dash consumer for the `candidate_progress` drain (N1 removed the store's consumer as
a dead end; the JS ring buffer was deliberately kept for exactly this). Interacts with
**F-CANOPY-036** (pool history never accumulates because the append loses a race with its own
feeder) — Phase 2 should either subsume that finding's fix or be sequenced after it, **not run
concurrently with it**.

### Phase 3 — topology consolidation

The topology store already prefers WS push. Phase 3 retires the REST *poll* (keeping REST as the
on-demand fallback for the documented stub-payload case at
`dashboard_manager.py:3934-3948`) and folds `tabpoll-topology`'s three callbacks down.

### Phase 4 — decide, don't drift, on the remaining six

Not a migration phase. A written decision per poller: keep the tab-gated poll (the expected outcome
for redis / cassandra / snapshots), or file a juniper-cascor requirement for a new broadcast channel
(the candidate for workers, and for raw topology if the heatmap is to be real-time). **Recording
"keep polling, deliberately" is a successful outcome for this phase.**

---

## 5. Invariants — the traps already paid for

Every one of these is a bug this codebase has already shipped and fixed. A WS migration re-enters
exactly the territory where they live.

1. **A WS buffer must never be an `Input` to an interval-driven poller.** Its clientside producer
   returns `no_update` when the socket is quiet, and a chained Input whose producer `no_update`s
   makes Dash **skip** the interval callback for that tick — silently re-creating the starvation the
   poll exists to prevent. `ws-liveness-store` rides as `State`, never `Input`. This is written into
   `dashboard_manager.py:3859-3872` and must survive every phase.
2. **Liveness must be derived from frame-arrival age, never a sticky `received` flag.** The sticky
   `topologyReceived` gate is what starved long-lived tabs in the N1 era. Staleness must flip within
   `WS_LIVENESS_WINDOW_MS` and re-engage the poll on the next tick.
3. **Never delete the REST fallback.** Every phase leaves a demoted, liveness-gated REST path. A WS
   channel that stops delivering must degrade to *late*, never to *absent* — the difference between
   F-CANOPY-004 (accepted) and F-CANOPY-037 (a P0/P1 blocker).
4. **`on()` is a single-slot registry per type unless the fan-out fix is present.** F-CANOPY-002:
   `ws_latency.js` silently *replaced* the bridge's `metrics` handler and killed the fast path for
   every live run. Fixed in canopy#515 (handler lists + dispatch fan-out with the try/catch inside
   the loop). Any new WS consumer must register through that, and
   `tests/unit/test_ws_handler_fanout.py` must keep passing.
5. **A store write with no consumer is dead work, and a consumer with no writer is a dead panel.**
   F-CANOPY-034 (poller with no consumer) and F-CANOPY-027 (filled store, dead render) are the two
   halves. `test_poll_gating.py::TestDeadPollerRemoved` is the existing tripwire; extend it per phase.
6. **A no-op write still fires every consumer.** The Stage 2 suppression is the guard, and
   F-CANOPY-038 says it is currently not working. See Phase 0.
7. **The 12-slot pool is the real budget.** Success is measured in *slots freed*, not pollers
   deleted.

---

## 6. Acceptance criteria

Per phase, measured **live on the isolated E2E trio during an active training run** — not in unit
tests, which cannot see the pool contention that is the entire subject.

| # | criterion | instrument |
|---|---|---|
| A1 | The migrated surface updates within **1 s** of the underlying cascor state change | wire census joined on the request body (`e2e_seg17_topology_driver.py --step wirecensus`) |
| A2 | Killing the WS mid-run degrades the surface to the REST envelope (≤16 s), never to blank | the `ws.close()` induction under a raised reconnect delay |
| A3 | Dash POST volume during a run drops measurably | POST/s census; the pre-remediation baseline is ~12/s |
| A4 | No surface regresses from *late* to *absent* | the F-CANOPY-037 render census — 11 sessions, not 1 |
| A5 | The `_GATED_POLL_INTERVALS` registry and its test still agree | `test_poll_gating.py` |

**A4 is the one that matters most.** F-CANOPY-037 is exactly the failure this workstream could
cause at scale: a correct server render that never gets a slot. A single-session probe cannot see
it — that finding needed **11 sessions** to establish 2-of-11. Any phase's sign-off needs a
multi-session render census, not one screenshot.

---

## 7. Open questions for the owner

1. **Is Phase 4's "keep polling, deliberately" acceptable as a terminal state** for redis /
   cassandra / snapshots? This plan assumes yes.
2. **Does the workers roster warrant a new cascor broadcast channel**, or is a tab-gated poll
   correct? Bears on F-CANOPY-032, whose alert path is verified correct in source but not
   reproducible — it may be a render-starvation instance rather than a data-path one.
3. **Sequencing against F-CANOPY-036** — subsume into Phase 2, or fix first? They touch the same
   store and must not run concurrently.
4. **Does this workstream own F-CANOPY-038**, or is that a Stage 2 defect fixed independently? This
   plan treats it as a Phase 0 blocker either way, because it gates the predictability of every
   later phase.

---

## 8. Status ledger

| phase | state | blocking |
|---|---|---|
| 0 — prerequisites | **not started** | canopy#531 merge; F-CANOPY-038 diagnosis |
| 1 — `state` fan-out | not started | Phase 0 |
| 2 — candidate metrics | not started | Phase 1; F-CANOPY-036 decision |
| 3 — topology consolidation | not started | Phase 1 |
| 4 — decide on the remaining six | not started | — (can be written at any time) |

**No code has been written for this workstream.** This document is the design of record produced by
the scheduled half of the owner's 2026-08-26 F-CANOPY-004 disposition.
