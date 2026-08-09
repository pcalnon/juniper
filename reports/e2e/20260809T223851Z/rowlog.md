# Phase 1 row log — run 20260809T223851Z (LIVE lane)

Append-only running record; consolidated into the matrix `status` column at Phase-1 close.
Statuses: PASS / FAIL / BLOCKED / N-A / DEAD-CONFIRMED (plan §9).

## Session facts

- Stack: data 8101 / cascor 8202 / recurrence 8212 (override; deploy holds 8211) / canopy 8051, script @ c9bd54e (F-E2E-006 fix live, PR #1049).
- Honest gate re-passed post-bounce: demo_mode:false, juniper_data_available:true.
- Auth posture: no CANOPY_API_KEY (browser-control auth off); rate limiter off; WS-primary transport (T-21).
- Browser: Playwright MCP Chromium 1600×900. Console clean at load (0 errors after F-E2E-006 fix; 4 errors before it — the 403 WS loop).
- Playwright note: on this DOM (15 eager tabs) the post-action snapshot can exceed the 5s tool timeout — a timed-out click MAY still have landed; verify state, never blind-retry toggles.

## Chrome rows

| row | status | evidence |
|---|---|---|
| C2.1-01 | PASS | dark-mode-store flips, glyph 🌙→☀️, html.dark-mode added; C2.1-01__dark-mode-about.png |
| C2.1-02 | PASS | dark persisted across reload (storage_type=local) |
| C2.1-03 | PASS | modal auto-opened with key absent, off params-init tick; C2.1-03__welcome-open.png |
| C2.1-04 | PASS | Get Started sets key=1 + closes; did not reopen on later reload |
| C2.2-01 | PASS (partial sweep) | tabs clicked so far switch panels: workers/redis/cassandra/tutorial/about; full 15-tab walk in W13-13 |
| C2.2-02 | PASS | non-default tab (About) restored exactly once on reload |
| C2.2-03 | pending | D-1 divergence row; third writer (snapshot replay) observed in W5 |
| C2.3-01 | PASS | status dot renders; C2.3-01__chrome-baseline.png |
| C2.3-02 | PASS | "Stopped" default |
| C2.3-03 | PASS | "Idle" default |
| C2.3-04 | PASS | "Step: 0" label+value |
| C2.3-05 | PASS | "Hidden Units: 0" bare-count form (no cap at idle) |
| C2.3-06 | PASS (cascade arm) | iteration segment display:block under cascade model; one_shot-hide arm in W8 |
| C2.3-07 | PASS | "Latency: 12ms" |
| C2.3-08 | PASS | connection-status display:none, callback-target-only |
| C2.4-01 | pending | initial "WS: --" too transient to catch post-hoc; capture in W13-14 offline reload |
| C2.4-03 | PASS | "WS: Connected" bg rgb(40,167,69) on healthy stack |

## Tab rows (W13 ancillary)

| row | status | evidence |
|---|---|---|
| M-WORKERS-01 | PASS | badge LOADING→NO WORKERS (warning) on isolated cascor; M-WORKERS-01__panel.png |
| M-WORKERS-02 | pending | upstream-degraded arm → W14 |
| M-WORKERS-03 | PASS | six tiles: 0/0/0/0, "0 / 0 fail", "0.0%" |
| M-WORKERS-04 | PASS | "No workers connected" info alert |
| M-WORKERS-05 | PASS (L arm) | local-note present (service mode forces local_reported=false) |
| M-WORKERS-06 | PASS | tab-gated poll: cascor log workers-lines 47→59 while on-tab, frozen at 59 after leaving (8s+ dwell) |
| M-REDIS-01 | PASS (behavioral) | poll resolves badges from LOADING; interval server-side, no browser-side observable by design |
| M-REDIS-02 | PASS | status/mode badges "DISABLED"; M-REDIS-02__disabled-state.png |
| M-REDIS-03 | PASS | unavailable state renders clean, dashboard unaffected, no crash |
| M-REDIS-04 | PASS | 8 tiles placeholder "--" / "0 keys" |
| M-CASSANDRA-01 | PASS (behavioral) | as REDIS-01 |
| M-CASSANDRA-02 | PASS | badges "DISABLED"; M-CASSANDRA-02__disabled-state.png |
| M-CASSANDRA-03 | PASS | clean unavailable render |
| M-CASSANDRA-04 | PASS | "N/A" fields, "No hosts available", counts 0, "No data available" |
| M-TUTORIAL-01 | PASS | walkthrough overlay live, "Step 1 of 8"; M-TUTORIAL-01__walkthrough-overlay.png |
| M-TUTORIAL-02 | PASS (Skip arm) | Next→Step 2 of 8, Skip hides overlay (container stays mounted — hide() semantics) |
| M-TUTORIAL-03 | PASS | 5/5 accordion items open simultaneously (always_open) |
| M-TUTORIAL-04 | pending | native-ish context menu; drive in tooltip section or record MANUAL |
| M-ABOUT-01 | PASS | toggle opens/closes collapse |
| M-ABOUT-02 | PASS | 4 li's (Py 3.13.13 / Linux 6.17.0-40-generic / x86_64 / App 2.2.0), zero about-ish network requests; M-ABOUT-02__system-info-open.png |
| M-ABOUT-03 | PASS | static content renders (screenshots) |

## W13 step ledger — COMPLETE (except W14-deferred arms)

1 PASS · 2 PASS (LIVE arm) · 3 PASS (poll stops, cascor-log observable 47→59→frozen) · 4 PASS · 5 PASS · 6 PASS · 7 PASS · 8 PASS · 9 PASS (15 dark screenshots `W13-13__dark-*.png`; spot-judged metrics-top/about/sidebar — legible; OBS-2 noted) · 10 PASS · 11 PASS · 12 PASS · 13 PASS (15-tab walk, 0 console errors/warnings) · 14 PASS (states 0/2/5 + recovery; state 6 N-A — see C2.4-07) · 15 PASS (2 tooltips + Apply-disabled note) · 16 PASS (3/9 ⇄ 2/10, sum 12; evolution hides all 14 config-managed sections).

## W13-14 / badge-state addenda

| row | status | evidence |
|---|---|---|
| C2.4-01 | PASS | caught in-script post-reload: first paint "WS: --" bg rgb(108,117,125) before Connected |
| C2.4-06 | PASS | socket close under setOffline → "WS: Reconnecting" amber rgb(255,193,7) |
| C2.4-07 | N-A (annotated) | "WS: Offline" unreachable via socket loss: GAP-WS-31 retry-forever client collapses closed→reconnecting in one status update; MutationObserver over a fresh close saw zero intermediate states. Renderer branch is defensive-only. Matrix-annotation candidate. |
| C2.4-04/05 | pending W14 | upstream reconnecting/degraded induction |
| C2.4-02 | pending demo lane | WS: Demo grey |
| C2.2-04 | PASS | per-tab section swaps observed (metrics NN-only, candidates CN, evolution none, dataset config) |
| C2.2-05 | PASS (annotated) | evolution: all 14 SIDEBAR_SECTION_IDS hidden ✓; row text "only Training Controls remains" imprecise — always-on Experimental Functions card also remains (not config-managed; verified dashboard_manager.py:267-282) |
| C2.2-06 | PASS | col-3/col-9 ⇄ col-2/col-10, always sums 12 |
| C2.2-01 | PASS | all 15 tabs switch panels (full walk) |

## Sweep extras recorded

- M-PARAMETERS-01/02/03 PASS (tables render: 9/5/11 rows incl. headers).
- M-REPLAY-01 PASS ("▶ No active replay session" visible, active block hidden).
- M-NETWORK-EDITOR-02 PASS (idle block + Investigating explanation), -03 PASS-with-note (badge "FSM: Unknown" at cold idle — fallback chain; recheck during W1), -05 PASS-as-documented (**D-0 confirmed live**: readout "No topology loaded."; server-side 404 — no browser-side request), -10 PASS (options empty per D-0).
- Playwright method notes: `setOffline` does NOT kill established WebSockets (badge honestly stays Connected; only pollers fail) — socket-state tests must close `window.cascorWS.ws` / `window.cascorControlWS.ws` directly. Disabled bootstrap buttons are pointer-transparent — tooltip hover on disabled Apply can't fire (retest enabled in W3; possible UX note).

## Observations / finding candidates (not yet ledgered)

- OBS-1: About panel "App Version: 2.2.0" vs /v1/health "version": "0.4.0" — two version sources disagree (about_panel local self.version vs health handler). Candidate F-CANOPY finding (truth/docs class) for Phase 2 triage.
- OBS-2: Dark mode renders all five training-control buttons uniform blue — the light-mode semantic colors (Start green / Pause yellow / Stop red) are lost. Legible but semantics-flattening; UX-class candidate for Phase 2 triage. Evidence: W13-13__dark-metrics-top.png vs M-TUTORIAL-01__walkthrough-overlay.png (light).
- OBS-3: Metrics-tab sidebar header reads "Network Parameters" while the tutorial-tab shows "Training Controls" card only — header text swaps per TAB_HEADER_MAP as designed (C2.2-04 corroboration, not a finding).
