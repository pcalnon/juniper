# HANDOFF 2026-08-25 — Canopy E2E Phase 2: the P0 sweep — five findings closed, two PRs in flight, F-CANOPY-005 awaiting its post-T6 live verification

Continue the juniper-canopy E2E validation arc, **Phase 2** (plan §6.3). Successor to
[`HANDOFF_2026-08-23_canopy-e2e-phase2-defect-triage.md`](HANDOFF_2026-08-23_canopy-e2e-phase2-defect-triage.md);
that handoff's **Traps** and **Landing work** sections remain fully valid and are not repeated here — read them,
plus the four **instrument laws** in the evidence note's *Stage 2 shipped* section (one-gesture sessions;
`changedPropIds` causal attribution + its 4000-char truncation trap; value-change subscribes are blind to
identical rewrites; `nohup setsid` for any probe longer than ~5 min — the task lease killed two mid-harvest).

**The headline: this arc has closed F-CANOPY-027 (Stage 2 = canopy#511), -006 (by verification — the
#507+#509+#511 series had already fixed it, no new code), -025 (canopy#514), -002 (canopy#515), and -031
(canopy#517 `9dcbb77a`) since the last handoff. One P0 remains open in the whole
ledger — F-CANOPY-005 — and its FIX is already written and in CI (canopy#518); only its live verification
is owed, queued behind the T6 GPU window.**

## Documents

Same four as always: matrix `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`,
evidence note `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (all closure blocks live
inside the finding entries; per-session sections at the end), plan (merge policy `:689` — headless merges
pre-authorized for arc PRs, green CI incl. ui-tests, REST squash endpoint), design note
`…CALLBACK-STARVATION-REMEDIATION-DESIGN.md` (§13/§13.1 = Stage 2 plan+outcome; §12.6 = the promotion-race
limit case that kept resolving findings: **a consumer of a store is unrunnable while its feeder's in-flight
time covers the feeder's period**).

## Verify your starting state

```bash
cd <fresh worktree of juniper-ml main>   # fetch first; main moves several times a day
python3 util/ad-hoc/e2e_finding_triage.py --open-only   # expect 40 findings / 13 fixed / 27 open (1 P0 · 2 P0/P1 · 10 P1)
python3 util/ad-hoc/e2e_unfilled_rows.py                # expect 298 verdicted / 0 UNFILLED
gh pr view 518 -R pcalnon/juniper-canopy --json state   # f005 fix — merge if green (REST squash)
# canopy#517 (f031) MERGED at handoff time: squash sha 9dcbb77a — that is the M-SNAPSHOTS-19 rider sha
```

`CURRENT_RUN_ID` = `20260825T044659Z`. Canopy worktrees `juniper-canopy--fix--f031-*` and `--f005-*` under
`/home/pcalnon/Development/python/Juniper/worktrees/` await post-merge cleanup (remove + branch -D + prune).

## THE T6 HOLD (cross-session, active)

The T6 re-baseline session (`uds:/run/user/1000/cc-socks/1606678.sock`) holds an exclusive GPU window of
**~7–9.5 h from ~2026-08-25T05:15Z**. I tore the isolated trio down and agreed to hold ALL GPU-touching E2E
steps (stack bring-ups, training runs, browser probes) until it **announces completion by cross-session
message**. CPU/CI/docs work is unrestricted. Do not bring the stack up before that announcement; if urgency
demands it, escalate the ordering to Paul rather than deciding unilaterally.

## Remaining work, in priority order

1. **Land canopy#518** (merge policy above; branch-update dance if BEHIND; delete its branch; clean BOTH
   canopy worktrees — #517 merged at handoff time as `9dcbb77a`, its worktree/branch still need cleanup;
   primary canopy checkout ff after each).
2. **f031 records** (ml PR; rider sha = `9dcbb77a`): ledger F-CANOPY-031 → FIXED
   (canopy#517 `9dcbb77a`) — closure facts: verified live against the real corpus, **"Showing newest 200 of 28016
   snapshot(s)"**, 200 rows in seconds, `data-snapshot-id` on all 200 (the "attrs on zero elements"
   sub-claim was zero ROWS — attrs were always in the row builder), and the FULL M-SNAPSHOTS-19 chain:
   right-click → context menu → Restore → **Confirm Snapshot Operation modal** for that exact snapshot,
   `context-menu-trigger` write captured. Matrix: M-SNAPSHOTS-19 → `PASS (re-validated @ <517-sha>)`
   (`e2e_matrix_rescore.py`; never `--overwrite`). New run id + tsv (protocol as always), CURRENT_RUN_ID
   bump, evidence-note section, arc-memory update. Mechanism for the note: TWO stacked causes — the
   panel's bare 2 s timeout lost to the ~4.9 s unbounded scan+serialize, AND 27,903 `html.Tr`s can never
   render; fix = route `limit`/`offset`+`total` (legacy full list when limit omitted) + newest-200 page +
   honest truncation line + `+3` timeout headroom.
3. **F-CANOPY-005 live verification** (AFTER the T6 announcement; #518 merged first): stack up on merged
   main, training run for congestion, drive control buttons — expect zero 409 double-fires (the grace
   window absorbs the timer-vs-ack race); then induce a business rejection (pause while STOPPED) — expect
   the danger alert via `training-control-action` and **NO** `/api/train/*` POST in the request capture
   (that's the new gate: fallback only on `err.transport`). Then: ledger closure, matrix rows in its blast
   radius (W2-step-2 arm, C2.5-10's alert — check the entry), records. **The entry stays OPEN until this.**
4. **The P1 tail**, cheapest-first from the root-caused set: **-010** (modal self-close → `dash.no_update`
   in `open_snapshot_op_modal`'s early-outs, `no_update` already imported), **-009** (detail wiped by the
   10 s rebuild → give `View Details` `n_clicks=0` like its four siblings + guard returns `no_update`),
   **-011** (Network Editor reads `state_machine.status`; canopy serves `fsm_status` — **fix the key, NOT
   the gate**: cascor genuinely enforces INVESTIGATING; also unmasks D-0's 404 route which must be fixed
   WITH it), **-014** (replay `_api_base_url` defaults `""` → build a real base like its two sibling
   panels), **-007** (canopy lists snapshots off a LOCAL path while creating via cascor — split-filesystem
   silent-empty; harness works around it via `JUNIPER_CANOPY_SNAPSHOT_DIR`), **-003** (ack path never
   re-enables buttons; sweep threshold 2 s vs comment's 5 s — touches the same Phase-D code #518 just
   changed, coordinate), **-035** (P1: loss plot reads `epochs/losses/phases` that `/api/state` never
   serves in any lane — repoint at `/api/metrics/history`, which has 4,106 candidate-phase rows/run).
   Then F-CASCOR-001 (file as a cascor issue) and F-ML-001 (reaper pidfile/port exclusion, juniper-ml).
   **Also in this tier, DO NOT DROP: F-CANOPY-008 (P0/P1)** — the `/ws/control` CSRF first-frame gate
   leaks a per-IP connection slot on ALL FIVE reject arms (`close(1008); return` without
   `release_connection_limits()`; five stale-token rejections permanently lock the control plane until a
   canopy restart, reachable with zero malice — proven live, entry `:647-680`); fix = release on every
   reject arm, and confirm the entry's deferred registration/metric-leak inference while there. **And
   F-CANOPY-004 (P0/P1) needs a FINDING-level disposition, not just row re-drives**: post-Stage-2 the
   numbers are materially better (interaction renders 3–16 s; fresh-session population 20–40 s) — take an
   owner decision: accept-and-document a latency contract (close with the numbers) or open the
   WS-migration workstream (JR-CAN-PERF-004); its rows re-drive after that call.
5. **P2 dispositions are the OWNER's call (§6.3)** — present Paul the open-P2 set (-001, -012, -015,
   -018, -026, -028, -032, -033, -034, -036, -013, F-CASCOR-002) for fixed-vs-deferred sign-off;
   execution order after approval is yours. Ready-made pieces: -034 (delete the inert store + regen
   `metrics_panel.txt`), -036 (the dead-click test is READY at `e2e_f027_redrive.py --step cardsprobe`),
   -013 (two one-line envelope fixes). The LEDGER pair F-E2E-004/-005 (harness-class) folds naturally
   into the F-ML-001 PR or closes as documented — give it an explicit disposition either way.
6. **Row re-drives owed** (each needs the stack, so post-T6): M-TOPOLOGY-01..18 + W4 + W1-12..14 (F-006's
   blocker gone), C2.10-03 (W7 confirm/swap), **M-SNAPSHOTS-20/-21 — NEWLY REACHABLE**: they need a real
   dataset-swap event, whose UI entry F-CANOPY-025 killed and canopy#514 restored (drive the Live Switch
   end-to-end and these two come with it), M-DATASET-14 (theme-flip re-drive owed regardless of fixes),
   and the F-CANOPY-004 latency-class rows (after item 4's disposition). **M-DATASET-17..26 (10 BLOCKED
   rows) still await the owner's DEMO-lane / 3-D-posture scoping decision** — surface it; do not drive
   around it.
7. **Phase 3** (plan §6.4, the `ui_live` suite) — entry condition is "every P0/P1 closed or
   owner-deferred": 13 P0/P1-tier findings remain open (1 P0 · 2 P0/P1 · 10 P1), so it is NOT near —
   items 3–4 are the path there. Do not start early.
8. **Phase 4 (plan §6.5) — still owed, do not lose it again**: the docs-truth-up batch per §11 — the
   D-ledger divergences (D-1 three-writers, D-2, D-3 replay-interval base, D-5 flag-default comment; D-0
   rides the -011 fix), the observation batch (OBS-1 About-vs-health version — About renders "App
   Version: 2.2.0" vs `/v1/health` `0.4.0`; `stream_health` recovery value `"healthy"` not `"ok"`; the
   depth-label "0 of N" cosmetic), and the closeout note against §13's acceptance criteria once Phase 3
   lands.

## Key context (hard-won this session; supplements the standing traps)

- **The worktree-isolation hook** rejects compound commands mentioning other repos' paths — run single
  commands, or `git -C <path>` one at a time. The ml session-worktree can't `cd` out; canopy work happens
  in centralized worktrees via `git -C`.
- **The PRIMARY juniper-ml checkout (`/home/pcalnon/Development/python/Juniper/juniper-ml`) is STALE**
  behind `origin/main` — this session's isolation could not ff it. Its notes/matrix/driver copies predate
  every closure since ~#1350; never read arc state from it. Sync it (`git checkout main && git pull
  --ff-only origin main`, only if its tree is clean — the F-6 guard) or work exclusively from a fresh
  worktree.
- **ml worktree sync after your own squash-merge**: git refuses the ff over your identical uncommitted
  copies — verify byte-equality vs origin/main (`git diff origin/main -- <files>` empty), then
  `git checkout HEAD -- <files>`, delete untracked news, ff. Never blind-restore.
- **Tree-equality riders**: pre-merge branch measurements bind to the merged content when
  `git rev-parse <branch>^{tree}` == `<squash>^{tree}` — record it in the rider note.
- **canopy CI traps hit this arc**: Sequence Safety WEAKENED on extract-method + LOST on renamed tests
  (waiver trailers in the ONE commit; prove locally with `juniper-symbol-loss-check --scope 'src/**/*.py'`);
  CodeQL `py/empty-except` blocks merge at green checks via an unresolved thread (comment inside the except
  body; fix commits to the same branch via `createCommitOnBranch` — helper archived at
  `util/ad-hoc/2026-08-24_commit_driver_fix_to_pr_branch.py`); the JS-source test idiom greps the WHOLE
  file — keep banned literals out of comments.
- **Driver**: `util/ad-hoc/e2e_f027_redrive.py` carries all verification steps (`f025`, `f025idle`,
  `f006`, `f002`, `bprobe`, `bcausal`, `btoggle`, `brefresh`, `dstats`, `cardsprobe`, observer-based
  `livecards`). The f031 probes live in scratch (`/tmp` — volatile; key numbers are in this handoff and
  PR #517's body). Evidence logs under `/tmp/juniper-e2e/` do not survive reboots.
- **The experimental-functions flag is cascor-process state** — a cascor restart resets it to false (boot
  behaviour, not the fixed echo bug). Runs on a trained network shrink to ~15–35 s; restart the cascor leg
  (`e2e_cascor_leg_restart.bash`, with `JUNIPER_E2E_PROJECT_DIR`) for full-length runs.
- Matrix deltas this session beyond the closures: C2.7-10 + C2.10-02 → `PASS (re-validated @ 5f2e905)`,
  M-METRICS-31/-32 → `PASS (re-validated @ 04f06ff)`.

## Git state at handoff

Shas below were main during this session; several sessions land PRs continuously, so take truth ONLY from
a fresh fetch. juniper-ml: my ml records through F-CANOPY-002 merged at `84d4712` (other sessions have
appended commits since — none touching the E2E ledger/matrix). juniper-canopy: **#517/f031 merged as
`9dcbb77a`**; Paul's #516 (memory-budget ratchet port) merged independently this morning. **Open canopy
PR: #518 (f005 fix, CI in flight)** — mine, squash-merge candidate under the arc policy; #512/#513 are
cursor drafts (not mine). Isolated stack DOWN, all ports free, 8211 = the live deploy container (never
touch). No uncommitted arc work outstanding.
**`origin/main` moves several times a day — always branch from a freshly fetched `origin/main`, and
re-derive every line anchor before relying on it.**
