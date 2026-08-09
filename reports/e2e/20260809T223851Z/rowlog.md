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

## W13 step ledger

1 PASS · 2 PASS (LIVE arm) · 3 PASS (poll stops) · 4 PASS · 5 PASS · 6 PASS · 7 PASS · 8 PASS · 10 PASS · 11 PASS · 12 PASS — 9/13/14/15/16 pending.

## Observations / finding candidates (not yet ledgered)

- OBS-1: About panel "App Version: 2.2.0" vs /v1/health "version": "0.4.0" — two version sources disagree (about_panel local self.version vs health handler). Candidate F-CANOPY finding (truth/docs class) for Phase 2 triage.
