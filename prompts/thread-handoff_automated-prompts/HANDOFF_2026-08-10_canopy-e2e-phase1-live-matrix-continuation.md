# HANDOFF 2026-08-10 — Canopy E2E Phase 1: live-matrix continuation (segment 3)

Continue **Phase 1 live click-by-click validation** of the juniper-canopy E2E arc (session "canopy validation"). Segments 1–2 are COMMITTED on branch `arc/canopy-e2e-phase1` (worktree hashed-splashing-narwhal; commits `87e9f79` + `6fe85f9`, pushed). Run-id `20260810T002233Z`.

## Completed so far (this session)

- **W1 end-to-end** (cold-start→growth→completion, 0→10 hidden units; DOM rows blocked by F-CANOPY-006 are marked), **W2 complete** (incl. the T-6 verbatim: Start-on-COMPLETED **accepted**, network retained), **W13 complete**, **W14 complete via a REAL outage** (badge states 3/6/7 + recovery), C2.1, C2.3, C2.4 all-states, C2.5 frame-level (WS-primary T-21 **confirmed**: frames+acks captured, zero `/api/train/*` HTTP), live-lane dataset 400-arms, Evolution during-run, post-run metrics harvest.
- **8 findings root-caused live** (all in the evidence doc `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` Phase-1 section, each with file:line):
  - **F-CANOPY-002 (P0)**: `ws_latency.js:75` **clobbers** the bridge's `metrics` handler (`websocket_client.js:179-180` single-slot `on()`) → metrics fast path dead every live run.
  - **F-CANOPY-003 (P1)**: success ack never re-enables control buttons (JS success path only logs); 2 s sweep lands +32 s quiet / never during runs → buttons wedge ⏳.
  - **F-CANOPY-004 (P0/P1)**: server Dash callbacks lag 30 s–minutes during runs (Dash POST p50 1.5 s / p90 3.7 s vs REST tier 6-36 ms); clientside instant.
  - **F-CANOPY-005 (P0)**: 3 s send-promise timeout races main-thread ack dispatch → REST fallback **double-fires state-changing commands after WS success** (409 captured).
  - **F-CANOPY-006 (P0)**: topology graph **never renders in live lane** — server response intercepted PERFECT (200, 181-trace figure, counts 2/10/2/89) but never applied client-side; depth slider ships `value=0/max=0` (`network_visualizer.py:180-183`); fresh-reload systemic.
  - F-CANOPY-001 (P2 glyph), F-CASCOR-001 (CUDA-OOM→"stalled" masking), F-ML-001 (orphan reaper kills nohup stack services).
  - D-divergences: stream_health `"healthy"` vs doc `"ok"`; About "App Version 2.2.0" vs health 0.4.0; T-6 inversion.
- Row record: `reports/e2e/20260810T002233Z/statuses.tsv` (~80 rows verdicted) + 21 screenshots.

## Remaining Phase-1 work (priority order)

1. **W5 snapshot lifecycle** — preconditions ALREADY MET (trained 10-unit network, training stopped, snapshots list empty). Then Network-Editor rows via FSM `Investigating` (confirm **D-0** 404 → `M-NETWORK-EDITOR-05`), Replay-tab rows, W11 (probe why `replay-position` reads 0/0 with a filled store).
2. **W3 param round-trip** (27-key body per `test_param_roundtrip_visible.py:37-65`; T-7 doctrine) + C2.9-04/05 toast arms + re-probe CN collapse/growth-radio/case-suspicion on Apply-enable (see TSV C2.6-06 note).
3. **W6 cold migration** (stage→cancel→re-stage→restart modal C2.10 rows→G-6 width check via `/api/topology` since the topo DOM is dead) + W12-10.
4. **W7 hot swap** (needs exp toggle ON + a NEW run) and **W8 model switch** (recurrence lives on **8212**, canopy env `JUNIPER_E2E_RECURRENCE_PORT=8212`).
5. Remaining chrome: C2.2-02/03, C2.9-07..16, C2.10 seed rows, tooltips; Parameters tab (pin/unpin M-PARAMETERS-04..06); Dataset-tab live rows (M-DATASET-10..16; seq rows N-A tabular).
6. **DEMO lane** (restart canopy `JUNIPER_CANOPY_DEMO_MODE=1`): W9 demo arms, all D-mode rows, `WS: Demo` badge, demo workers pair, M-NETWORK-EDITOR 501 arms, W5-30.
7. Fill the matrix `status` column from the TSV + finish evidence doc → Phase-1 close per plan §6.2 exit.

## Key context / gotchas

- **Stack UP** (data 8101 / cascor 8202 / recurrence 8212 / canopy 8051). cascor was restarted mid-session by `util/ad-hoc/e2e_cascor_leg_restart.bash` (byte-matches cascor_up; use it again if needed). Honest gate: `/v1/health` BODY `demo_mode:false` + `juniper_data_available:true`.
- **cascor holds a trained 10-unit network, stopped.** Snapshot baseline: empty list. Layout baseline: 4+ pre-existing layouts (don't touch `default_metrics_layout` etc.; use `e2e-probe`).
- **NEVER `reap_pytest_orphans.bash` while the stack runs** (F-ML-001 — it kills the nohup services). GPU freed earlier (~4 GB); if CUDA OOM recurs (F-CASCOR-001 symptom: instant "stalled (0 new units)"), check `nvidia-smi`.
- **Button wedge workflow** (F-CANOPY-003): after ANY control-button click, the button stays ⏳ ~30 s (quiet) / indefinitely (during runs). Don't interpret as broken; don't double-click; the wedge blocks W2-02/10-style arms.
- **During-run DOM lags 30 s–min** (F-CANOPY-004): assert API first, DOM patiently; post-run everything catches up EXCEPT topology (F-CANOPY-006 — verify topology via `/api/topology`, not the graph).
- Playwright MCP notes: default 5 s tool timeouts trip on this busy page — use `browser_run_code_unsafe` with `page.screenshot({timeout:30000})` and generous `waitForTimeout`s; `dcc.Dropdown`/slider via `dash_clientside.set_props`; `#visualization-tabs .nav-link` text-match for tabs; sandbox rejects `$( )` and `-C` redirects — plain commands from the worktree only.
- Matrix `status` column untouched so far — verdicts accumulate in the TSV first (bulk-fill at close).
- Landing protocol: this branch lands as ONE evidence PR at Phase-1 close (plan §6.2 says PR count 0 for Phase 1; the wip commits are crash-safety). Arm `--auto`; `--admin` if BLOCKED/BEHIND per arc authorization.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hashed-splashing-narwhal
git log --oneline -3   # expect 6fe85f9, 87e9f79 atop 9813bab
git status --short     # expect clean (playwright-mcp ignored)
for p in 8101 8202 8212 8051; do curl -sS -m 3 "http://127.0.0.1:$p/v1/health" | head -c 80; echo; done
curl -sS http://127.0.0.1:8051/v1/health | grep -o 'demo_mode":[a-z]*'   # expect false
curl -sS http://127.0.0.1:8202/v1/network | grep -o 'hidden_units":[0-9]*'  # expect 10
cat reports/e2e/CURRENT_RUN_ID   # 20260810T002233Z
```

Git: branch `arc/canopy-e2e-phase1` (pushed to origin), clean tree. Session tasks: #1 in_progress (this), #2-4 gated Phase 2-4.
