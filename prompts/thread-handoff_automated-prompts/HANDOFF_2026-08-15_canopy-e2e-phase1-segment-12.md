# HANDOFF 2026-08-15 — Canopy E2E Phase 1: segment 12, the 158 unfilled matrix rows

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. Successor to
[`HANDOFF_2026-08-14_canopy-e2e-phase1-segment-10.md`](HANDOFF_2026-08-14_canopy-e2e-phase1-segment-10.md)
(segment 11 produced no handoff of its own — its record is the evidence note, §"Phase 1 — segment 11").
Segments 10 and 11 are merged and **no arc PR is open in either repo**.

Segment 11 was a consolidation segment (no live driving): it mapped every verdict the arc had recorded into
the matrix's `status` column and stopped there. **Segment 12's job is the opposite — drive rows live.**

## Verify your starting state first

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline -3 origin/main            # expect 1b5cbf3 or later
git status --porcelain                                          # expect clean or unrelated stragglers
gh pr list --repo pcalnon/juniper-ml   --state open --limit 10  # expect no arc/canopy-e2e-* PR
gh pr list --repo pcalnon/juniper-canopy --state open --limit 10
git branch --list 'arc/canopy-e2e*'; git worktree list | grep arc/canopy-e2e
python3 util/ad-hoc/e2e_row_coverage.py                         # 298 rows / 141 verdicted / 157 remaining
```

Count the ledger itself with the filler's own splitter, never a naive `|` split (at least one matrix row
contains an escaped `\|`):

```bash
python3 util/ad-hoc/e2e_matrix_fill.py \
  --verdicts reports/e2e/20260811T010700Z/statuses.tsv \
  --verdicts reports/e2e/20260810T002233Z/statuses.tsv \
  --verdicts reports/e2e/20260809T223851Z/rowlog.md
# expect: filled 0 · already filled 140 · no verdict yet 158   (dry run; writes nothing; exits 1 on "nothing to fill")
```

**The two tools disagree, and both numbers are right.** The mapper says 141 verdicted / 157 remaining; the
matrix ledger says 140 / 158. Net +1 from two opposed causes: the mapper **under**-credits M-PARAMETERS-02/03
(it reads only the leading token of the `M-PARAMETERS-01/02/03` slash enumeration in
`reports/e2e/20260809T223851Z/rowlog.md:82`, −2) and **over**-credits three rows whose only record is a
non-terminal `pending …` that the filler deliberately refuses to write — C2.4-02, M-TUTORIAL-04, M-WORKERS-02
(+3). `158 − 3 + 2 = 157`, exactly. The filler prints **four** non-terminal ids, not three: C2.4-05 is in that
list for a different reason — it has **no** record at all in `reports/e2e/`, terminal or otherwise, so the
mapper never credited it and it is not part of the delta. **The matrix is the ledger**; the mapper is an
estimator. Do not "reconcile" them by loosening either.

## What is done (do not redo)

| PR      | Merge     | Item                                                                             |
|---------|-----------|----------------------------------------------------------------------------------|
| ml#1106 | `4afaf5e` | segment 9 — W6 owner gate driven, F-CANOPY-019's open question resolved           |
| ml#1113 | `dccd564` | segment 10 — second F-CANOPY-019 arm, first matrix bulk-fill (66 cells)           |
| ml#1115 | `831c1ec` | segment 11 — three-source consolidation to 137/298, C2.2-04 mis-fill repaired     |
| ml#1117 | `1932479` | segment 11 follow-up — slash enumerations + rowlog bullets, 140/298               |

Closed lanes, from the matrix: §2.1 4/4, §2.2 6/6, §2.3 8/8, §3.3 topology 18/18, §3.10 replay 17/17,
§3.11 network editor 18/18, §3.12 redis 4/4, §3.13 cassandra 4/4, §3.15 about 3/3. W-lane prose steps
W1 / W2 / W3 / W5 (LIVE) / W6-01..20 / W7-step1 / W9-step12 / W11 / W13 / W14 are recorded in the TSVs; they
have no matrix status cell, so they never appear in the fill counts.

## The remaining 158 rows

Every count below is reproducible from the matrix with the splitter above. Section anchors are line numbers in
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`.

| section (line)                                   | unfilled | row ids                                        |
|--------------------------------------------------|---------:|------------------------------------------------|
| §2.4 WS badge (`:215`)                           |        2 | C2.4-02, C2.4-05                               |
| §2.5 training controls (`:238`)                  |        1 | C2.5-07                                        |
| §2.6 NN meta-parameters (`:267`)                 |       15 | C2.6-02,03,04,05,07,08,09,10,13,14,15,16,17,18,19 |
| §2.7 dataset subsection (`:293`)                 |       10 | C2.7-01..10                                    |
| §2.8 candidate-node meta-parameters (`:308`)     |       14 | C2.8-01..14                                    |
| §2.9 banner trio / Apply / Experimental / Info / Pinned (`:327`) | 16 | C2.9-01..16                     |
| §2.10 global modals + floating alerts (`:348`)   |       17 | C2.10-01..17                                   |
| §3.1 metrics (`:390`)                            |       22 | M-METRICS-02..09,11..20,23,25,27,28             |
| §3.2 candidates (`:429`)                         |        4 | M-CANDIDATES-07,09,10,11                       |
| §3.4 evolution (`:474`)                          |        2 | M-EVOLUTION-04,07                              |
| §3.5 boundaries (`:489`)                         |        8 | M-BOUNDARIES-01..08                            |
| §3.6 dataset view (`:504`)                       |       24 | M-DATASET-01,02,03,05,07,09..27                |
| §3.7 workers (`:558`)                            |        1 | M-WORKERS-02                                   |
| §3.8 parameters (`:571`)                         |        4 | M-PARAMETERS-04,05,06,07                       |
| §3.9 snapshots (`:585`)                          |       17 | M-SNAPSHOTS-04,05,07..21                       |
| §3.14 tutorial (`:686`)                          |        1 | M-TUTORIAL-04                                  |

**145 of the 158 are `mode: B`** — in scope for the live lane (five of them are `MANUAL`, so "in scope" is not
"scriptable"; see the classes below). The other 13 break down as:

- **DEMO-lane only (2)**: C2.4-02 (`WS: Demo` badge), M-DATASET-03. The live stack runs `demo_mode:false`, so
  these need the DEMO arm.
- **LIVE-lane only (4)**: C2.4-05 (upstream *degraded*), M-METRICS-27, M-BOUNDARIES-07, M-WORKERS-02.
  C2.4-05 and M-WORKERS-02 are the same induction — segment 4 produced `WS: Upstream reconnecting` by taking
  the cascor leg down; *degraded* is a different `streamHealth.overall` value and has never been induced.
- **Mixed mode (1)**: **M-DATASET-11** (`D (success) / L (400 arm)`) — the same class as M-DATASET-04/06,
  still unfilled, and easy to miss because it falls into none of the buckets above.
- **No mode column (6)**: C2.10-01..06 sit in a table that has **no `mode` column at all**
  (`| row id | id | line | role | status |`). The C2.4 badge table is also non-standard but *does* carry
  `mode` — which is why C2.4-02/05 are classified above. Locate the status column **by header name**, never by
  index — `e2e_matrix_fill.py` does; a hand edit must too.

Cross-cutting classes that change how you drive, not whether:

- **`DEAD-EXPECTED` (4)**: M-CANDIDATES-10, M-CANDIDATES-11, M-SNAPSHOTS-20, M-SNAPSHOTS-21. Their passing
  terminal value is **`DEAD-CONFIRMED`**, not `PASS` (matrix §1.1 legend): the click verifiably did nothing —
  no request, no DOM change, no console error.
- **`MANUAL` (6)**: M-EVOLUTION-07, M-BOUNDARIES-07, M-DATASET-15, M-DATASET-16, and two carrying
  `MANUAL (native menu)` — M-SNAPSHOTS-19 and M-TUTORIAL-04.
- **`AUTO-API (seed-only) / MANUAL (modify)` (10)**: C2.10-08..17 — seed the state through the API, then the
  modify half is a human gesture.
- **`AUTO-API` (21 of the 55 rows in §2.6–§2.9)**: classified as not browser-drivable *because of the numeric
  wall*. **Segment 9** showed post-canopy#489 (evidence note, "Methodology notes (segment 9)") that at least
  two sidebar numeric inputs — `#nn-dataset-elements-input` (`step=1`) and `#nn-dataset-noise-input`
  (`step="any"`) — now commit typed values cleanly through real keystrokes. **Re-test the class before
  accepting `AUTO-API` as "API only"** — if it holds generally, 21 rows get much cheaper.

## Suggested order

1. **§2.6 → §2.7 → §2.8 → §2.9 (55 rows, one bring-up).** All sidebar, all `mode: B`, most reachable without a
   training run. Densest yield in the arc.
2. **§2.10 global modals (17).** Reachable from any tab; the seed-only/modify split above says which half is
   scriptable.
3. **§3.9 snapshots (17).** Needs the snapshot corpus — see the teardown hazard below before you cycle the
   stack. Expect F-CANOPY-009 (detail panel wiped ~7 s later by the panel's own 10 s refresh) and
   F-CANOPY-010 (op-confirm modal self-closes ~3.6 s); both OPEN.
4. **§3.1 metrics (22).** Needs a training run with history. F-CANOPY-002 means the WS metrics fast path is
   dead in every live run, so score against the REST oracle.
5. **§3.6 dataset view (24)** and **§3.5 boundaries (8)** last — boundaries needs a trained network.

Opportunistic small rows: M-PARAMETERS-04..06 (pin checkboxes → `pinned-params-store`, local storage) and
M-PARAMETERS-07 (table refresh after an Apply — a different mechanism, `parameters-panel-params-store` fed
from `applied-params-store`), M-EVOLUTION-04/07, M-CANDIDATES-07/09.

**C2.5-07 is not opportunistic.** It is the non-default REST posture (`enable_ws_control_buttons=false`) and
needs canopy **relaunched** with that setting. Drive it in its own pass and drive nothing else in that
posture — the default is `true`, and any other §2.5 row scored there is scored against the wrong transport.

## Standing up the stack — read this before running anything

The isolated trio is **DOWN** as of this handoff (`curl localhost:{8101,8202,8051}/v1/health` all fail). The
juniper-deploy containers on **8050, 8201 and 8211** are up and are **not** this arc's stack; never validate
against them.

```bash
# from the CANONICAL checkout, not a worktree (see the PROJECT_DIR trap below)
cd /home/pcalnon/Development/python/Juniper/juniper-ml
JUNIPER_E2E_RECURRENCE_PORT=8212 util/isolated_stack.bash --status
JUNIPER_E2E_RECURRENCE_PORT=8212 util/isolated_stack.bash --dry-run --up   # prints recipes, starts nothing
JUNIPER_E2E_RECURRENCE_PORT=8212 util/isolated_stack.bash --up             # data 8101 · cascor 8202 · canopy 8051
```

Three ways this script will hurt you if you run it the obvious way:

1. **`--down` stops the recurrence port unconditionally**, whether or not you passed `--with-recurrence`, and
   `JUNIPER_E2E_RECURRENCE_PORT` **defaults to 8211 — the port the live juniper-deploy container holds**
   (host 8211 → container 8210). `--up` is protected (`recurrence_port_precheck` refuses to start onto an
   occupied 8211) and **teardown is not**. *Today* the teardown is nonetheless a no-op against that container:
   `stop_port` resolves its target through `port_pid`, which parses `pid=` out of `ss -tlnpH`, and `ss` omits
   that field for the root-owned docker-proxy when you are not root — so it logs "nothing listening" and never
   kills. Treat this as **latent, not harmless**: it becomes a real kill the moment the port is held by a
   user-owned process (your own `--with-recurrence` leg) or the script runs as root. Pass
   `JUNIPER_E2E_RECURRENCE_PORT=8212` on **every** call anyway — it costs nothing, and a failed `--up` calls
   `do_down` internally, so the override matters on bring-up too.
2. **`--down` deletes the snapshot corpus** — `rm -f <cascor>/src/snapshots/snapshot_*.h5` and the canopy
   mirror. Four `.h5` files currently live in `juniper-cascor/src/snapshots/` (verify the count yourself);
   they are the precondition for all 17 §3.9 rows. **Do the snapshots block before you cycle the stack**, or
   copy the corpus somewhere safe first.
3. **`PROJECT_DIR` derives from the script's own location** (`util/ -> juniper-ml -> Juniper`). Run it from a
   worktree and it resolves siblings to `worktrees/juniper-data`, `worktrees/juniper-cascor`,
   `worktrees/juniper-canopy` — paths that do not exist. Launch from the canonical checkout, or set
   `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`.

Other defaults, from the script's header: `JUNIPER_E2E_DATA_PORT` 8101, `_CASCOR_PORT` 8202, `_CANOPY_PORT`
8051, `_CASCOR_CONDA` `JuniperCascor1`, `_CANOPY_CONDA` `JuniperCanopy1`, `_HEALTH_TIMEOUT` 60.

Gate every live check on canopy's `/v1/health` reporting `demo_mode:false` **and** `juniper_data_available:true`
— an HTTP 200 alone is not the gate.

**Know which code you are testing.** The last live segment ran canopy `d11bfcd` and a cascor leg pinning
`#513`. Both have moved (canopy `f90420e`, cascor `3857d1e` / `#522` at the time of writing). Record the SHAs
you actually launch, and check `ps -o lstart -p <pid>` against `git log` before attributing any observed
behaviour to a finding — otherwise you are comparing against code the arc never ran.

## Recording verdicts

A fresh bring-up means a **new run id**, formatted `<UTC yyyymmddThhmmssZ>`. Create
`reports/e2e/<NEW_RUN_ID>/statuses.tsv` with the header `row_id<TAB>status<TAB>notes<TAB>screenshots`, update
`reports/e2e/CURRENT_RUN_ID` (it currently reads `20260811T010700Z`), and name screenshots
`reports/e2e/<run-id>/<row-id>__<step>.png`. Append verdicts through the helper — it is dup-guarded, so an
existing `row_id` is skipped unless you pass `--replace`:

```bash
python3 util/ad-hoc/e2e_append_statuses.py reports/e2e/<NEW_RUN_ID>/statuses.tsv rows.json
```

Then fill the matrix, **newest run first** (first source carrying a row wins; `--overwrite` is not used, so
earlier cells are never clobbered):

```bash
python3 util/ad-hoc/e2e_matrix_fill.py \
  --verdicts reports/e2e/<NEW_RUN_ID>/statuses.tsv \
  --verdicts reports/e2e/20260811T010700Z/statuses.tsv \
  --verdicts reports/e2e/20260810T002233Z/statuses.tsv \
  --verdicts reports/e2e/20260809T223851Z/rowlog.md          # dry run
# ... review the "filled rows" list, then re-run with --write
```

Four rules the filler enforces — respect them in any hand edit too:

- **`pending …` is not a verdict.** Only the plan §9 vocabulary reaches a status cell: `PASS` / `FAIL` /
  `BLOCKED` / `N-A` / `DEAD-CONFIRMED`, optionally with a short rider that *narrows* the verdict
  (`PASS (LIVE arm)`, `FAIL(during-run)/PASS(post-run)`).
- **A lane arm proves one lane** — render it as such, never as a bare `PASS`.
- **A compressed token addresses real rows**: `..` ranges, `,` and `/` enumerations, and `-L`/`-D` lane
  suffixes all expand.
- **Never change a row's cell count.** The filler refuses to; a hand edit that adds or drops a `|` silently
  moves every later cell. That is how segment 10 wrote a `PASS` into C2.2-04's **FA** column.

## Tools you already have

| tool                                  | use                                                             |
|---------------------------------------|-----------------------------------------------------------------|
| `util/isolated_stack.bash`            | `--up` / `--down` / `--status` / `--dry-run` / `--with-recurrence` — **always with `JUNIPER_E2E_RECURRENCE_PORT=8212`** |
| `util/ad-hoc/e2e_matrix_fill.py`      | fill the matrix status column from run records (dry-run default) |
| `util/ad-hoc/e2e_row_coverage.py`     | "which rows still need a verdict?" estimator                     |
| `util/ad-hoc/e2e_append_statuses.py`  | dup-guarded TSV verdict append (`--replace` to rewrite in place) |
| `util/ad-hoc/e2e_poll_status.py`      | `--until-units N` / `--until-fsm STOPPED` / `--until-pending-clear` |
| `util/ad-hoc/e2e_w3_params_driver.py` | scripted Playwright driver + shared browser/log helpers          |
| `util/ad-hoc/e2e_w6_dataset_driver.py`| scripted dataset/restart driver (imports the W3 helpers)         |
| `util/ad-hoc/e2e_cascor_leg_supervise.bash` | run the cascor leg under a resident supervisor (F-ML-001)   |
| `util/ad-hoc/e2e_snapshot_h5_compare.py` | compare snapshot `.h5` artifacts                              |

**Try the browser MCP first** (`mcp__playwright__*`). It was available in segment 9 and unavailable in
segment 8; when it is absent, drive the `util/ad-hoc/` scripts under
`/opt/miniforge3/envs/JuniperCanopy1/bin/python` — the only environment with playwright installed.

**Never run `util/reap_pytest_orphans.bash` while the stack is up** (F-ML-001, OPEN): it kills the
nohup-launched cascor leg. Use the supervisor script for long sessions. The GPU box is shared with other
sessions — prove a process descends from *your* leg before killing anything.

## Still open from earlier segments

- **F-CASCOR-003b (open question, never settled).** After a clean stop, the cascor candidate pool was still
  resident (forkserver children at +90 s with `fsm_status` STOPPED). The leg that showed it booted before
  cascor#514. Segment 11 drove nothing, so segment 12 is the first chance to settle it: restart the leg onto
  current main and repeat start → stop → observe. Cheap, and the network is disposable.
- **W7 is NOT blocked** — its matrix preconditions are "LIVE lane; training **running**", with no recurrence
  dependency (`:866`). `W7-step1` is already PASS; steps 2..18 are drivable on the base trio. The segment-9
  and segment-10 handoffs both said "W7/W8 remain BLOCKED"; **that was wrong for W7**, and it is the largest
  drivable prose lane still outstanding.
- **W8 is `N-A`, not BLOCKED, while the recurrence leg is down** — its preconditions require plan §4.5's
  `--with-recurrence` fourth leg, and the matrix's own remedy for the missing leg is
  `N-A (no recurrence service)` (`:889-891`).
- **W6-21** (staging-failure arm) needs the shared juniper-data leg stopped — MANUAL, never attempted;
  recorded in the TSV as `NOT DRIVEN (MANUAL)`.
- **W5-30 + the DEMO lane** — each demo arm must 501 and render `❌ Operation not supported in this mode`.
  Needs its own bring-up posture.

## Traps that have already cost this arc time

- **Verify a click by its EFFECT, not by the tool's return.** Playwright's post-click ack times out on this
  page while the click lands.
- **Settle after any tab render or reload before judging a control.** The measured figure is a **1.5–2 s**
  settle before clicking a freshly rebuilt pattern-matched Input (one status field settled at ~4.3 s); treat
  a few seconds as a heuristic, not a constant. An under-settled page silently drops the callback and reads
  exactly like a broken control.
- **Panels are hidden, not unmounted** — read a panel's counters only with its own tab active, and assert
  *visibility* (`getComputedStyle` + `getBoundingClientRect`), never presence. `offsetParent` is `null` for
  `position:fixed` elements and is not a visibility test.
- **Dismiss `#welcome-modal` after any reload** — and note `#welcome-modal` *is* the `.modal-dialog`.
- **`performance.getEntriesByType('resource')` caps at 250 entries**; a full buffer reads exactly like zero
  traffic. Call `clearResourceTimings()` + `setResourceTimingBufferSize()` first.
- **`scrollIntoView` does not apply before a `getBoundingClientRect` in the same `page.evaluate`.** Scroll,
  wait, then read the rect in a separate call; reject any box with `y < 0` or `height == 0`.
- **Read id lists from source, never from a DOM prefix** (`[id^="sidebar-"]` returned 20; `SIDEBAR_SECTION_IDS`
  is exactly 14).
- **Dropdowns are Dash 3.x Radix selects**, not react-select: a `<button aria-haspopup="listbox">` with options
  portalled to `body` as `[role=option]`. Scope options by the trigger's `aria-controls`, and match labels
  exactly ("Network Evolution", not "Evolution"; "Adam" also matches AdamW/NAdam/RAdam/Adamax).
- **A component id appearing in a `_dash-update-component` body proves nothing.** These callbacks carry many
  Inputs and States, and every fire names all of them; only the carried *value* is evidence.
- **`/api/set_params`, `/api/stage_dataset` and `/api/cancel_pending_dataset` are POSTed server-side** from
  Dash callbacks: **zero browser requests is expected**, never a failure. Prove them on the canopy server log
  (read by byte offset — it is >100 MB) plus the browser's `_dash-update-component`.
- **A Dash slider's commit rule depends on its `updatemode`.** The replay and network-visualizer sliders are
  `updatemode="mouseup"` — a moved handle is not evidence a value committed, and
  `page.keyboard.press('ArrowRight')` on the focused thumb is what dispatches. The metrics-panel slider
  (`metrics_panel.py:369`) is `updatemode="drag"` and does commit continuously. Check before you score.
- **The metrics store is throttled, not starved.** `FULL_HISTORY_POLL_TICK_MODULUS` is **5** — 1 poll in 5
  returns data (~0.2 Hz at the 1 s interval), the rest return `no_update`. Segment 7 recorded an observed
  1-in-15 and attributed it to this constant; the constant reads 5, so **that attribution is unresolved**.
  Measure the real cadence before scoring a metrics row as starved.
- **The T-22 numeric wall is obsolete for the restart modal's dataset fields** post-canopy#489
  (`step="any"` / `step="1"`), and segment 9 drove two *sidebar* numeric inputs cleanly. The six
  `#restart-p-*` param fields were never re-tested.
- **Check the findings ledger before filing.** Segment 9 drafted a P1 that was withdrawn as the blast radius
  of two already-open findings. The ledger in
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` contains F-CANOPY-001..016 and
  019/020, F-CASCOR-001..003, F-E2E-001..006, F-ML-001. **F-CANOPY-017 and F-CANOPY-018 were minted but never
  landed in that ledger** — 017 (P1: a step-invalid numeric param silently applied a hardcoded default; the
  `is not None else DEFAULT` idiom spans ~18 fields, and 7 of 22 sidebar number inputs were already off their
  own step grid) is at `reports/e2e/20260811T010700Z/statuses.tsv:90`, and 018 (P2: `params-status` has two
  writers, so the apply toast is always overwritten by "⚠️ Unsaved changes") at `:88`. Both govern the §2.6 /
  §2.8 / §2.9 rows this segment starts with. **Grep the TSVs as well as the ledger before filing**, and fold
  017/018 into the note when you next touch it.

## Landing the segment

Aim for one PR per segment (the cadence changed at segment 8; segment 11 needed two — a follow-up is fine, a
sprawl is not):

1. Branch from `origin/main` — `git worktree add <WT> -b arc/canopy-e2e-phase1-seg12 origin/main`, in
   `/home/pcalnon/Development/python/Juniper/worktrees/` with the standard
   `<repo>--<branch>--<YYYYMMDD-HHMM>--<short-hash>` name (parent `AGENTS.md`, "Worktree Procedures").
2. **Check `gh pr list` immediately before you push, and re-verify your worktree diff against the pushed
   branch right after opening the PR.** Concurrent sessions are real here — on 2026-08-15 a peer session
   opened a duplicate PR (#1116) on the same branch name as the one already merged (#1115).
3. Commit signed. `python3 util/open_signed_pr.py --repo juniper-ml --branch <b> --add <local>:<repopath> …
   --message … --title … --body-file …` creates a GitHub-signed commit through the API and needs no working
   tree; `main` enforces `required_signatures`.
4. Merge with the REST squash endpoint —
   `gh api -X PUT repos/pcalnon/juniper-ml/pulls/<N>/merge -f merge_method=squash` — which succeeds where
   `gh pr merge` stalls, because the squash commit GitHub creates is itself signed. The plan pre-authorizes
   headless merge for this arc's PRs (`…E2E-FRONTEND-VALIDATION-PLAN.md:689`); recent sessions have still
   confirmed each merge with the owner. **Confirm.**
5. After merging, check `main-verify` is green on the merge SHA
   (`gh run list --workflow=main-verify.yml --limit 1`), then clean up your worktree and branch.

## Git state at handoff

This handoff was cut from `1b5cbf3` (#1118). **`origin/main` moves several times a day** — other sessions land
PRs continuously — so always branch from a freshly fetched `origin/main`, never from the SHA above, and expect
the primary checkout to carry unrelated stragglers (`git status --porcelain` there before assuming otherwise).

**No open arc PR in either repo**, and no `arc/canopy-e2e-phase1-seg12` branch exists anywhere, so step 1 above
is safe. But "no arc worktree" would be wrong: **seven session worktrees under
`juniper-ml/.claude/worktrees/` still hold arc branches** — `arc/canopy-e2e-phase1`,
`arc/canopy-e2e-phase1-results`, and `-seg4`, `-seg5`, `-seg6`, `-seg7`, `-seg10`. `git branch --list
'arc/canopy-e2e*'` marks those seven with `+` (checked out elsewhere); only `-seg9` is free. A checked-out
branch **cannot** be deleted until its worktree goes, so sweeping them means `scripts/cleanup_session_worktrees.py`
first — optional hygiene, not a prerequisite. Remote leftovers: `origin/arc/canopy-e2e-phase1{,-results,-seg4,
-seg5,-seg6,-seg7,-seg11}`. There is no `-seg8` branch, local or remote.

Matrix line anchors in this document are against the matrix as this segment's PR lands it; if one is off by a
line, re-grep the `###` header — the section names are the durable key, not the numbers.

Matrix at **140 of 298** rows verdicted. Verdict records: `reports/e2e/20260810T002233Z/statuses.tsv`
(91 rows), `reports/e2e/20260811T010700Z/statuses.tsv` (145 rows), and the inherited
`reports/e2e/20260809T223851Z/rowlog.md`.
