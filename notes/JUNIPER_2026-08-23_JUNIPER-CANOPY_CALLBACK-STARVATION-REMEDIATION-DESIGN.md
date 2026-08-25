# Canopy callback-starvation remediation — design of record

**Project**: Juniper — juniper-canopy
**Author**: Paul Calnon
**Date**: 2026-08-23
**Status**: Stages 1 + 3 **SHIPPED** 2026-08-23 (juniper-canopy#507, #508) — see §12 for the measured
outcome and the corrections implementation forced on this document. Stage 2 remains proposed, with a
widened scope. Owner decision on §9.1 was: Stage 1 + Stage 3 in Phase 2, Stage 2 as a follow-on.
**Closes**: F-CANOPY-027 (P0/P1), F-CANOPY-004 (P0/P1)
**Evidence**: [`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md)
§ F-CANOPY-027 → `ROOT CAUSE (2026-08-23)`, and § `Phase 2 — investigation 3`

---

## 1. Decision

Canopy asks dash-renderer to start callbacks about **three times faster than it can finish them**, against a
**hard-coded 12-slot** concurrency pool. The queue never drains, and the deterministic priority order means
the same low-priority callbacks lose every arbitration forever — which is what F-CANOPY-027 looks like from
the UI.

**The fix is to reduce the arrival rate, not to repair any callback.** The chosen design silences
panel-scoped pollers while their tab is inactive, **on the client**, so an inactive tab costs zero slots.
It is staged into three PRs so the highest-value change lands first and is measurable on its own.

This is a load problem with a load fix. No callback in the three "dead" panels is defective.

---

## 2. The mechanism, in one paragraph

dash-renderer 4.2.0 promotes work out of `callbacks.prioritized` under a cap that is a literal in the
bundle (`dash_renderer.dev.js:2846`):

```js
available = Math.max(0, 12 - executing.length - watched.length);
pickedSyncCallbacks = syncCallbacks.slice(0, available);
```

Separately `getReadyCallbacks` will not promote a `requested` callback while any of its Inputs is an output
claimed by a still-pending callback. Together: **a poller whose completion time exceeds its own trigger
period is never absent from the pending set, so every consumer of its output starves indefinitely.**
Arbitration is `sortPriority` → `getPriority` (`:1592`), a base-36 string of downstream chain depth and
breadth sorted descending, so *terminal* render callbacks — every stat tile, badge and figure in the three
dead panels — score the minimum and lose every time. Full derivation, clean-room reproduction and the
twenty refuted mechanisms are in the evidence note; they are not repeated here.

**The cap is not configurable.** There is no Dash setting, no env var, no `app.run` argument. Patching the
vendored bundle is rejected in §5.

---

## 3. The measured overload

### 3.1 Census

`util/ad-hoc/canopy_poller_inventory.py` (juniper-ml) walks `juniper-canopy/src/frontend/**` by AST and
resolves `f"{self.component_id}-…"` ids against each class's `component_id` default.

| | count |
|---|---|
| callbacks statically resolved | 151 |
| **interval-driven pollers** | **29** |
| of those, one-shot (`params-init-interval`, `max_intervals=1`) | 6 |
| **steady-state perpetual pollers** | **22** |
| renderer concurrency slots | **12** |

> *Census caveat, stated so it is not over-read*: the live app registers **182** callbacks; the static pass
> resolves 151. The gap is pattern-matching (`dash.ALL`) and clientside registrations a static pass cannot
> resolve. Every poller it *does* report is exact, so 22 is a **lower bound** on the steady-state count.

### 3.2 Arrival rate vs service rate

| trigger | period | pollers | starts/s |
|---|---|---|---|
| `fast-update-interval` | 1000 ms | 7 | 7.00 |
| `candidate-metrics-panel-update-interval` | 1000 ms | 1 | 1.00 |
| `slow-update-interval` | 5000 ms | 9 | 1.80 |
| `metrics-panel-stats-update-interval` | 5000 ms | 2 | 0.40 |
| `cassandra` / `redis` / `hdf5-snapshots` refresh | configurable (≈5000 ms) | 3 | ≈0.60 |
| | | **22** | **≈10.8 starts/s** |

Measured throughput on the isolated stack: **224 completions in 60 s = 3.7/s** (`e2e_f027_slots.py`).

**Demand exceeds service by ≈2.9×.** That is the whole defect. Consequences measured over 5020 renderer
state changes:

| metric | value |
|---|---|
| pool full (`available == 0`) | **83.6 %** of samples |
| `available <= 1` | 97.1 % |
| `prioritized` backlog | max **36** (3× the pool) |

### 3.3 What is already tab-scoped, and what is not

Only **7** pollers currently reference `visualization-tabs.active_tab` at all — and all 7 gate
**server-side**, returning `dash.no_update` *after* a full round-trip that has already consumed a slot.

| tab-gated poller | file:line | interval | tab |
|---|---|---|---|
| `fetch_training_state` | `candidate_metrics_panel.py:243` | candidate panel | candidates |
| `update_topology_store` | `dashboard_manager.py:3734` | slow | topology |
| `update_raw_topology_store` | `dashboard_manager.py:3782` | slow | topology |
| `update_dataset_store` | `dashboard_manager.py:3805` | slow | dataset |
| `update_workers_store` | `dashboard_manager.py:3821` | slow | workers |
| `update_boundary_store` | `dashboard_manager.py:3836` | fast | boundaries |
| `update_boundary_dataset_store` | `dashboard_manager.py:3849` | fast | boundaries |

A further **6** are panel-scoped in fact but carry no gate at all — they poll on every tab:

| un-gated but panel-scoped | file:line | belongs to tab |
|---|---|---|
| `update_network_graph` | `network_visualizer.py:364` (**fast**) | topology |
| `update_cassandra_panel` | `cassandra_panel.py:368` | cassandra |
| `update_redis_panel` | `redis_panel.py:357` | redis |
| `update_snapshots_table` | `hdf5_snapshots_panel.py:868` | snapshots |
| `fetch_network_stats` | `metrics_panel.py:590` | metrics |
| `fetch_training_state` | `metrics_panel.py:617` | metrics |

**13 of 22 steady-state pollers are panel-scoped.** On any given tab at most one panel's pollers are
needed. That is the headroom.

---

## 4. Design constraints

1. **The cap is 12 and cannot be raised.** Any design must fit under it.
2. **The shared intervals cannot simply be disabled.** `fast-update-interval` (7 callbacks) and
   `slow-update-interval` (9) each carry a *mix* of global and panel-scoped consumers. Disabling either
   would silence the status bar. This is the reason the fix is not a one-liner.
3. **Tab activation must still repaint promptly.** Today the `active_tab` Input gives an immediate fetch on
   tab switch. A design that only re-enables an interval would make the user wait up to one period (5 s on
   the slow lane) staring at stale content.
4. **`prevent_initial_call=False` on mount is load-bearing.** Multiple call sites carry `PERF-CN-01`
   comments explaining that the panel must populate on mount rather than after the first tick.
5. **No new always-on poller may be added** by the fix.
6. **The idiom already exists in-tree.** `metrics-panel-replay-interval` ships `disabled=True`
   (`metrics_panel.py:565-568`) and is enabled only while replaying. The design generalises an established
   pattern rather than introducing one.

---

## 5. Options considered

| # | option | verdict |
|---|---|---|
| 1 | **Patch the vendored renderer bundle** to raise `12` | **Rejected.** Edits a site-packages artifact; erased by every `pip install`; unshippable to any other environment; makes canopy's correctness depend on a patched dependency. |
| 2 | **Lengthen every interval** until completion < period | **Rejected as the primary fix.** Cheap, but it trades liveness for correctness across the whole dashboard and leaves the 2.9× oversubscription intact — the pool would still saturate under any latency spike. Retained as a *fallback knob*, §8.3. |
| 3 | **Move real-time updates to the existing WebSocket relay** (JR-CAN-PERF-004) | **Right long-term, wrong now.** The WS bridge already exists and the N8 posture uses it for metrics, but converting 13 panel pollers is a much larger change than Phase 2 can absorb, and it does not help panels with no WS channel (redis, cassandra, snapshots). Should follow this work, not replace it. |
| 4 | **Client-side gating: an inactive tab's pollers do not fire** | **Chosen.** Removes the request *and* the slot; matches the existing `disabled=` idiom; scoped to the 13 panel-scoped pollers; measurable in isolation. |
| 5 | **Consolidate the global pollers** (several small fast-lane polls → one) | **Chosen as a follow-on** (Stage 2). Independent of option 4 and additive. |

---

## 6. Chosen design

### 6.1 Stage 1 — per-tab interval gating (the load fix)

**Introduce one gated `dcc.Interval` per panel-scoped polling group**, and move the panel-scoped callbacks
off the shared `fast`/`slow` intervals onto it. The shared intervals keep only the genuinely global
consumers.

```python
# dashboard_manager.get_layout() — one per panel that polls
dcc.Interval(id="tabpoll-topology",   interval=SLOW_UPDATE_INTERVAL_MS, disabled=True),
dcc.Interval(id="tabpoll-dataset",    interval=SLOW_UPDATE_INTERVAL_MS, disabled=True),
dcc.Interval(id="tabpoll-workers",    interval=SLOW_UPDATE_INTERVAL_MS, disabled=True),
dcc.Interval(id="tabpoll-boundaries", interval=FAST_UPDATE_INTERVAL_MS, disabled=True),
dcc.Interval(id="tabpoll-candidates", interval=FAST_UPDATE_INTERVAL_MS, disabled=True),
...
```

A **single clientside callback** owns every `disabled` flag. Clientside is essential: it must not itself
consume a server slot, and it must react instantly on tab switch.

```python
self.app.clientside_callback(
    """
    function(activeTab) {
        // one return position per tabpoll interval, in TABPOLL_ORDER
        return TABPOLL_ORDER.map(function (t) { return t !== activeTab; });
    }
    """,
    [Output(f"tabpoll-{t}", "disabled") for t in TABPOLL_ORDER],
    Input("visualization-tabs", "active_tab"),
)
```

**Preserving prompt repaint (constraint 3).** Each panel-scoped fetcher keeps `active_tab` as an **Input**
alongside its new gated interval. That is what fires the immediate fetch on activation; the interval then
carries the steady state. This is safe: moving `active_tab` from `Input` to `State` was tested during the
root-cause work and is *not* the defect (evidence note, refuted mechanism no. 20), so there is no reason to
disturb it.

```python
@self.app.callback(
    Output("dataset-plotter-dataset-store", "data"),
    Input("tabpoll-dataset", "n_intervals"),        # was: slow-update-interval
    Input("visualization-tabs", "active_tab"),      # unchanged — the immediate-repaint trigger
    prevent_initial_call=False,
)
```

The server-side `if active_tab != "dataset": return dash.no_update` guard **stays** as a belt-and-braces
check. It is now genuinely cheap, because it will almost never be reached.

**Expected effect.** On any tab, at most one panel group polls. Steady-state pollers drop from 22 to
**9 global + 1–2 for the active panel ≈ 10–11**, and arrival rate from ≈10.8/s to **≈4–5/s** — below the
measured 3.7/s service rate once the freed slots raise that rate too. The pool should leave permanent
saturation.

### 6.2 Stage 2 — consolidate the global fast lane

Seven callbacks ride `fast-update-interval` at 1 Hz, several hitting adjacent canopy endpoints
(`update_unified_status_bar`, `update_training_status_store`, `handle_button_timeout_and_acks`,
`update_metrics_store`). Merging the pure-status ones into a single poller that writes one store, with
cheap fan-out callbacks downstream, converts N slots into 1. Sequenced after Stage 1 so its effect is
measurable separately.

### 6.3 Stage 3 — a guard so this cannot regress

Promote `canopy_poller_inventory.py` from `util/ad-hoc/` to a real check and wire it into canopy CI:

- **fail** if steady-state perpetual pollers exceed a pinned budget (proposed: **12**, matching the cap)
- **fail** if a new poller rides a shared interval while referencing `active_tab` (i.e. is panel-scoped but
  not gated) — the exact shape that produced this defect

This is the durable part. Without it, the next panel added to the dashboard silently re-creates F-CANOPY-027.

---

## 7. Verification

### 7.1 Primary instrument

`util/ad-hoc/e2e_f027_slots.py` (juniper-ml), 60 s on the Candidates tab, live isolated stack.

| metric | before (measured) | Stage 1 target |
|---|---|---|
| pool full (`available == 0`) | 83.6 % | **< 20 %** |
| `prioritized` backlog, max | 36 | **< 12** |
| completions / 60 s | 224 | **> 500** |

### 7.2 Behavioural proof

Re-drive the rows F-CANOPY-027 owns and re-score per plan §6.3:
`M-CANDIDATES-07/-09/-10/-11`, `M-BOUNDARIES-01/-02/-03/-04`, `M-DATASET-13/-15/-16`,
plus the five rows currently carrying `PASS` against **mount defaults** —
`M-CANDIDATES-01/-02/-03/-04/-06` — which must be treated as unproven until re-driven.

### 7.3 Regression test that fails on the parent commit

Plan §6.3 requires it, and the F-CANOPY-029 precedent is explicit that a test passing both ways buys
nothing. Two layers:

1. **Unit (deterministic, runs in canopy CI).** Assert the wiring contract: every panel-scoped poller's
   Input interval is a `tabpoll-*` component, and every `tabpoll-*` interval is declared `disabled=True`
   with exactly one clientside writer of its `disabled` prop. **Fails on parent** — today they ride
   `slow-update-interval` / `fast-update-interval`.
2. **`ui_live` (Phase 3 harness).** Drive to Candidates on a live run, poll for
   `candidate-metrics-panel-pool-size` to leave `"0"`. **Fails on parent** — that is the F-CANOPY-027
   symptom itself. If Phase 3's harness is not yet in place when Stage 1 lands, the clean-room
   `e2e_f027_cleanroom.py --delay` dose-response stands in as the mechanism test, and this row moves to
   Phase 3's fragile-area suite.

### 7.4 Watch for

Confirm Stage 1 did not merely *move* the starvation: after the change, re-run `e2e_f027_ready.py` and
check that no callback sits in `requested` with a permanent blocker. A pool that is merely less saturated
would still starve the lowest-priority terminal callbacks.

---

## 8. Risks

| risk | mitigation |
|---|---|
| A panel goes stale because its gate never re-enables | The clientside callback is the single writer of every `disabled` flag; Stage 3's guard asserts exactly one writer. `dcc.Store`-driven tab restore already sets `active_tab` on load, so the initial tab arms correctly. |
| Tab switch feels slower | `active_tab` stays an Input on each fetcher (§6.1), so activation fetches immediately — same as today. |
| A background panel genuinely needs to keep polling while hidden | None identified: all 13 are pure display surfaces. **Owner question §9.3.** |
| Stage 1 helps but does not clear the cap | Fallback knob §8.3 below; and Stage 2 is additive. |
| Clientside callback ordering vs. the `visualization-tabs.children` rebuild | The rebuild fires once, from `model-class-store` hydration. The `disabled` outputs target `tabpoll-*` intervals that live **outside** the tabs container, so the rebuild cannot detach them. Verify with `e2e_f027_slots.py` across a rebuild. |

**§8.3 Fallback knob.** If Stage 1 leaves the pool contended, raise `FAST_UPDATE_INTERVAL_MS`
(`canopy_constants.py:350`) from 1000 ms to 2000 ms. This halves the dominant 7.0 starts/s term at a
liveness cost that should be invisible next to the 30 s–minutes lag F-CANOPY-004 documents today. Cheap,
reversible, one constant.

---

## 9. Open questions for the owner

1. **Stage scope for Phase 2.** Stage 1 alone closes F-CANOPY-027 and F-CANOPY-004 if the §7.1 targets are
   met. Should Stages 2–3 land inside Phase 2, or be tracked as follow-ons so Phase 2 can close?
   *Recommendation: Stage 1 + Stage 3 in Phase 2 (the guard is what stops recurrence); Stage 2 as a
   follow-on.*
2. **Poller budget for the Stage 3 guard.** Pin at 12 (the cap), or lower with headroom (e.g. 9)?
   *Recommendation: 12, with the check reporting the current count so drift is visible before it bites.*
3. **Any panel that must keep polling while hidden?** The design assumes none. A "keep warm" exception
   would need an explicit allow-list in the guard.
4. **Does Stage 1 change the WS migration plan (JR-CAN-PERF-004)?** It reduces the urgency but not the
   value. *Recommendation: keep JR-CAN-PERF-004 open; note this design as a prerequisite that makes the
   migration measurable.*

---

## 10. PR sequencing

| PR | repo | contents | gate |
|---|---|---|---|
| **PR-C1** | juniper-canopy | Stage 1: `tabpoll-*` intervals, clientside gate, 13 pollers re-pointed, unit test from §7.3(1) | §7.1 targets met on a live re-measure |
| **PR-M1** | juniper-ml | evidence-note update, re-drive `statuses.tsv`, `CURRENT_RUN_ID` bump, re-scored matrix rows from §7.2 | follows PR-C1 |
| **PR-C2** | juniper-canopy | Stage 3 guard promoted into canopy CI | after PR-C1 |
| **PR-C3** | juniper-canopy | Stage 2 global-lane consolidation | follow-on; optional for Phase 2 |

Per the arc's merge policy, each canopy PR is a `PR-C*` in the plan's own sequence. `open_signed_pr.py`
uploads whole files, so PR-C1 and PR-C2 both touching `dashboard_manager.py` must merge sequentially with
the second rebased.

---

## 11. What this does not fix

F-CANOPY-002, -005, -006, -008, -003, -007, -009, -010, -011, -014, -025, -031, F-CASCOR-001 and F-ML-001
are independent of the pool and are unaffected by this design. F-CANOPY-033 (`RESET_COMPONENT_STATE` storm
at ~13/s) is *adjacent* — it is wasted client work on a contended dashboard — but it targets the Cassandra
subtree and was measured not to be a cause here; it stays P2 and separate.

---

## 12. Outcome (2026-08-23) — what shipped, and what this document got wrong

Stages 1 and 3 shipped as **juniper-canopy#507** (gating) and **#508** (completion + budget guard).
Stage 2 has not started, and its scope is **wider** than §6.2 assumed. Recorded here so the next reader
works from what implementation actually found rather than from what was predicted.

### 12.1 Result

**The behavioural goal is met.** All three panels F-CANOPY-027 froze are alive, verified by A/B injection
through each component's own `setProps` — the same probe that measured **0** consumer dispatches across
220 before the change:

| panel | consumer dispatches | DOM |
|---|---|---|
| Candidate Metrics | 0 → **2** each | `''` → `Inactive` / `No active candidate pool` |
| Dataset View | **3 / 3 / 4** | changed ✓ |
| Decision Boundary | **3 / 3** | `No network loaded` → `Displaying decision boundary` |

**The §7.1 saturation targets are not met.**

| metric | baseline | after #507 | after #508 | §7.1 target |
|---|---|---|---|---|
| pool full (`available == 0`) | 83.6 % | 63.6 % | **61.4 %** | < 20 % ❌ |
| `prioritized` backlog, max | 36 | 37 | **23** | < 12 ❌ |
| completions / 60 s | 224 | 499 | 449 | > 500 ✓ (at #507) |

Worst-case concurrent perpetual pollers: **14 → 12**, against a cap of 12. The backlog collapse
(36 → 23) is the structurally meaningful figure; throughput roughly doubled.

### 12.2 The correction that matters: interval gating is only half the problem

§6.1 assumed the load was interval-driven. It is not, entirely. **Panel work chained off a global store
re-runs on every tab no matter what its own interval does.** `update_snapshots_table` takes
`Input("dataset-swap-events-store", "data")`, which `poll_dataset_swap_events` rewrites every 5 s — so the
snapshots panel re-renders on every tab, gated interval or not. Network Editor and Replay have the same
shape. This is why saturation floors at ~61 % rather than reaching the §7.1 target.

**Stage 2's scope is therefore two levers, not one:**

1. **Consolidate the global lane** (as originally written) — ~10 perpetual global pollers remain.
2. **NEW — stop no-op store writes.** An unchanged write still fires every downstream consumer. The fix
   is already demonstrated in-tree: `hydrate_model_class` now returns `no_update` when the resolved value
   matches the store, which removed an entire redundant 15-tab rebuild. Applying the same rule to
   `poll_dataset_swap_events`, `stream-health-store`, `training-status-store` and the rest of the global
   lane should cut the chained re-runs directly. Each needs checking individually: in some designs a
   store write doubles as a heartbeat, and suppressing it would break a consumer that keys off the write
   rather than the value.

### 12.3 The census in §3.1 under-reported, exactly as its caveat warned

The AST pass resolves 151 of 182 callbacks. It missed two real panel-scoped pollers that #508 had to add:
`network-editor-panel-fsm-poll` (2 s, running on every tab) and `update_network_graph` (the 8-output
topology renderer, forced at 1 Hz from every tab by `fast-update-interval`). **Use the built-app census
(`app._callback_list`) for anything load-bearing**; the AST pass is for a quick read only. The Stage 3
guard uses the built-app census for this reason.

### 12.4 Two hypotheses this document should not have carried forward

- §6.1's plan to keep `active_tab` as an `Input` for prompt repaint was correct, but for a different
  reason than stated: moving it to `State` was separately tested during root-causing and is **not** the
  defect. It is retained because it fires the immediate fetch, not because moving it would break anything.
- The "known limitation" in `_setup_poll_gating`'s docstring — the children rebuild resetting panel-owned
  interval gates — is now largely moot, because `hydrate_model_class` no longer performs the redundant
  rebuild on the common "live" path. The fail-safe (`disabled=False` default) is retained anyway.

### 12.5 What is still open

- **Stage 2**, with the widened scope above.
- **The matrix re-drive.** §7.2's rows have *not* been re-scored: that needs a live training run, and the
  mechanism-level verification above is not a substitute. `M-CANDIDATES-01/-02/-03/-04/-06` in particular
  still carry `PASS` recorded against mount defaults and remain unproven.
- **F-CANOPY-034** (new, P2): `metrics-panel-network-stats-store` is now written by nothing and read by
  nothing. #507 removed its poller and retained the inert `dcc.Store` to keep the diff reviewable; the
  store itself should be deleted, which requires updating the layout regression snapshot.
- **F-CANOPY-027 and F-CANOPY-004 should not be marked `fixed`** until Stage 2 lands and the rows are
  re-driven.

### 12.6 Re-drive correction (2026-08-24): §12.1's behavioural claim was attach-scoped

The live matrix re-drive (evidence note, *Phase 2 — re-drive (2026-08-24)*; run `20260824T080426Z`)
re-validated the Candidate Metrics and Dataset View lanes end-to-end under live training, and **refuted
§12.1's "all three panels alive" for the Decision Boundary panel in steady state**: its plot-render callback
fires once at mount and is never promoted again (80 store fills at ~1/s vs exactly 1 render in 115 s;
zero re-renders for slider / confidence / refresh). Mechanism: both of its feeders are fast-lane ~1 s
pollers whose round-trip covers their period, so the render's Inputs are permanently claimed by a pending
feeder — the §12.2 correction taken to its limit case. Two new ledger findings came out of the same drive:
F-CANOPY-035 (loss plot reads history keys `/api/state` never serves — wrong producer) and F-CANOPY-036
(pool history append races its feeder's repoll and never lands).

**Stage 2 therefore carries three levers, not two:** (1) consolidate the global lane (§6.2); (2) suppress
no-op store writes (§12.2); (3) **un-block the boundaries chain** — slow its feeders below their round-trip
time, make them no-op-suppressing (post-run they rewrite an identical mesh ~1/s), or move the render
clientside. §7.2's boundaries rows stay red until then; the candidates/dataset rows are re-scored and no
longer gate on this document.

## 13. Stage 2 implementation plan (2026-08-24) — per-call-site decisions

Grounded in the built-app census (10 global perpetual pollers) and a read of every call site + every
consumer of every touched store (heartbeat check: **all consumers are value-driven; none key off the
write itself** — including the three dataset-swap consumers, the four metrics-store consumers, and the
clientside stream-health badge). `update_snapshots_table` in particular carries its own refresh interval,
so suppressing swap-events no-op writes cannot stall it — it only stops the *chained* full snapshot-list
refetch it performs on every 5 s rewrite today.

| # | call site (lane) | decision | why |
|---|---|---|---|
| 1 | `update_unified_status_bar` (fast) + `update_training_status_store` (fast) | **MERGE** into one callback: bar outputs + `training-status-store` (suppressed on `{is_running, phase}` no-change) | both fetch `/api/status` every fast tick; −1 slot, −1 Hz HTTP |
| 2 | `update_network_info` (slow) + `update_network_info_details` (slow) + `update_stream_health` (slow) + `reconcile_pending_dataset_banner` (slow) | **MERGE** into one slow-lane system callback (4 outputs; banner via `prevent_initial_call='initial_duplicate'`) | network-info and the banner both fetch `/api/status` (a 4th `/api/status` poller!); details fetches `/api/network/stats`; stream-health is an in-memory snapshot; −3 slots, −2 slow-lane HTTP |
| 3 | `poll_dataset_swap_events` (slow) | **SUPPRESS**: add `State` on own store, `no_update` on identical `events` | rewrites `{"events":[...]}` unconditionally today; 3 chained panel re-renders per write on every tab |
| 4 | `_update_metrics_store_handler` REST path (fast) | **SUPPRESS**: `no_update` when normalized fetch equals `current_metrics` (State already present) | post-run it rewrites an identical history list at 1 Hz into 4+ consumers incl. the 8-output topology renderer — the measured client-saturation driver |
| 5 | `update_boundary_store` + `update_boundary_dataset_store` (tabpoll-boundaries) | **LEVER 3**: cadence FAST→SLOW (5 s) + suppress both on payload equality; keep `active_tab` / refresh / slider Inputs (immediate repaint + forced refetch unchanged) | both feeders' in-flight time covers their 1 s period, so the render's Inputs are permanently claimed (§12.6); the dataset panel proves slow-cadence feeders leave promotion gaps; suppression alone cannot fix pendingness, cadence alone leaves identical-rewrite fan-out |
| 6 | `handle_button_timeout_and_acks` (fast) | **KEEP** | already returns `no_update` when nothing changed; local-only (no HTTP); F-CANOPY-003-adjacent — do not disturb |
| 7 | `metrics-panel-replay-interval` | **KEEP** | ships `disabled=True`, armed only while replaying (dormant) |
| 8 | `ws-liveness-store` writer (fast) | **KEEP** | clientside — consumes no renderer slot |

Expected effect: global server-side perpetual pollers **10 → 6**; worst-case concurrent (topology tab)
**13 → 9** vs the cap of 12; fast-lane `/api/status` fetches 2/s → 1/s; slow-lane HTTP 4 → 2 per tick;
and at idle/post-run steady state the global stores stop firing their consumer fan-outs entirely.

Volatility notes for the equality checks: `training-status-store` is `{is_running, phase}` (no volatile
fields); swap-events is `{"events": [...]}`; metrics history rows carry timestamps but identical fetches
return identical rows (equality holds when nothing new landed); the boundary mesh/dataset payloads are
pure data. `stream-health-store` is NOT suppressed (its snapshot may carry ages; its one consumer is a
cheap clientside badge — the win there is the merged slot, not the write).

Verification: unit tests per suppressed handler (identical payload → `no_update`; changed payload →
write), callback-shape tests (merged callbacks exist, old ones gone), a cadence pin
(`tabpoll-boundaries` interval == `SLOW_UPDATE_INTERVAL_MS`, failing on the parent commit), the Stage-3
budget guard re-run (expected headroom), then §7.1 slots measurement + the `bprobe` render-aliveness
probe on a live stack running the branch (symlink e2e-root), and finally the M-BOUNDARIES row re-drive.

Open question carried to the re-drive: whether the resolution slider's Redux value commit lands under
load post-#507 (run `20260824T080426Z` saw aria move to 125 while no 125-mesh fetch followed; the
starved render made the client side unobservable — re-test once the render is alive).

### 13.1 Stage 2 outcome (2026-08-24)

Shipped as **juniper-canopy#511** (`60f9737`), exactly per the §13 table. Measured on the merged content
(§7.1 protocol): pool-full 61.4 % → **25.5 % idle / 35.3 % under live training**, completions 449 →
**778/60 s**, backlog now drains to 0 (was held), starving-set **empty**; the Decision Boundary render
executes on every real change including interaction-triggered ones (7 renders/115 s live vs 1 at the
parent), and M-BOUNDARIES-01..04 re-drove to `PASS (re-validated @ 60f9737)` — -02/-03 by direct
`changedPropIds` causation. **F-CANOPY-027 is CLOSED**; §12.5's other opens (F-CANOPY-034 tidy-up, the
F-CANOPY-035/-036 findings the re-drive surfaced) are tracked in the ledger. Full record: evidence note,
*Phase 2 — Stage 2 shipped (2026-08-24)*.
