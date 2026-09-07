# HANDOFF — canopy E2E arc: F-CANOPY-035 narrowed (not solved), and the 27 blocked rows

**Date**: 2026-09-07 · **Session**: <https://claude.ai/code/session_0128NYXuYk5LcwUyWwpydK45>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/functional-crafting-metcalfe`
**Branch**: `docs/f035-supersession-mechanism` (juniper-ml#1812, armed, awaiting checks at time of writing)

**Documents REFERENCED** (the ecosystem convention in
`/home/pcalnon/Development/python/Juniper/AGENTS.md` § Cross-Project Conventions requires the filename
on every citation, because more than one document is cited):

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` — the finding ledger, the arc's document of record
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` — the row matrix; its §4 scripts are canonical for step detail
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — §11's instrument
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` — this document's template
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` — defines the W-series, the FA-1..FA-5 fault areas, and the `DEAD-EXPECTED`/`DEAD-CONFIRMED` vocabulary this arc scores in
- `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md` — its Phase 2 must **not** run concurrently with F-CANOPY-036's verification (§7)
- `util/ad-hoc/README.md` — the ad-hoc header convention and the arc's instrument traps

Two session memories are cited by name in §1 rather than by allusion:
`feedback_e2e_finding_mechanisms_are_unreliable.md` and `reference_dash_renderer_12_slot_starvation.md`.

**Documents CHANGED by the session this hands off from**: `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,
`util/ad-hoc/README.md`, and this file. **Added**: `util/ad-hoc/2026-09-05_dash_layout_id_census.py`,
`util/ad-hoc/2026-09-05_f035_store_write_latency_probe.py`,
`util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py`,
`util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py`, and **22** evidence files under
`reports/e2e-canopy-2026-09-02/transcripts/` — 8 landed by juniper-ml#1790, 8 by **#1810**, 6 on the
#1812 branch. One **pre-existing** instrument was also modified, behaviourally:
`util/ad-hoc/2026-09-04_f035_candidate_loss_redrive.py` (+33/−2, detaches its response listener so a
census stops counting when its window closes). The lifecycle probe is **new in #1812** — it gained
`--store`, the list inventory and the shape census in a later commit *within the same PR*, which is
invisible to any `--name-status` check, so it appears only in the Added list (§3.3, §9).

---

## 0. PREFLIGHT — five things before you read further

Each one cost this arc real work.

1. **Confirm juniper-ml#1812 merged.** `gh api repos/pcalnon/juniper-ml/pulls/1812 --jq '{merged,merged_at}'`.
   **Exit 0 is not a merge** — read the `merged` field or safe_merge's `MERGED` line. If it is still
   open, only what §2 attributes to #1812 is on the branch; **#1790, #1794 and #1810 are already on
   main.** In particular `util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py` and 8 transcripts
   landed via **#1810**, not #1812. (They are *also* present on the #1812 branch, which has merged main
   three times — so finding the file proves nothing about which PR carried it. Use
   `git log -1 -- <path>` to see the merge commit that actually landed it.)
2. **Fetch both repos**, juniper-ml *and* juniper-canopy — and know that **the serving commit of the
   :8052 leg is not recoverable.** The ledger cites `f56f46c` for the lifecycle runs and `de253e9` for
   the topology read, from the same probe on the same leg in the same session; `de253e9` is today's
   `origin/main` and looks like a *checkout* HEAD, not what the leg imported. **No F-035 artifact
   records a SHA at all** (grep confirms zero hits), so nothing can adjudicate it. Treat every canopy
   `file:line` in §1/§3 as needing re-verification against whatever `origin/main` is when you read
   this — §10 step 7 does that. This is the same class of error the arc already paid for in #1794, and
   writing the serving commit into the artifacts is outstanding work (§7.1).
3. **Nothing in §3 is shipped product code.** F-CANOPY-035's cause is *identified*, the fix is **not
   built**. Do not read the ledger's "mechanism named" as "defect fixed".
4. **The fixture is grown, not rebuilt, and must stay that way.** `POST /v1/network` **destroys** it.
   Grow with `PATCH /v1/training/params`. See §6.
5. **Environment.** canopy python is
   `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python` — the bare
   `JuniperCanopy` env is deprecated, and the conda hooks that strip `LIBTORCH` do **not** run when
   you invoke the binary directly.

---

## 1. Goal statement

Continue the juniper-canopy E2E validation arc. Its ledger is
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and its row matrix is
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`.

The arc is at **55 findings — 37 fixed, 1 accepted, 1 withdrawn, 16 open (3 P1, 13 P2), zero open
P0** — and the matrix is at **296 of 298 rows verdicted**. Both figures are tool-produced and
reproducible; see §10.

The session handing off closed the long-running investigation into **F-CANOPY-035**, the top open P1.
Its symptom is that `metrics-panel-metrics-store` is written and never applied, so the candidate loss
plot renders empty while the server serves candidate history. Over 2026-09-05 and 2026-09-07 that was
narrowed by measurement. **An earlier draft of this handoff said the mechanism was named —
renderer-level supersession. A Lane B review took that apart and it is withdrawn to a hypothesis.**
What stands:

> The store-writing callback (`update_metrics_store`) is scheduled ~24 times per 90 s and its
> lifecycle **never completes** — it reaches a terminal list zero times while the store's value never
> advances. **Why** it never completes is NOT established.

Four explanations were eliminated by measurement — a duplicate store instance, the `allow_duplicate`
WS appender clobbering it, a stale server-side view, and a reducer that drops a value it was handed.
**A fifth is uneliminated and correlates better than supersession**: `Callback failed: the server did
not respond` appeared in 2 of the 4 failing runs and none of the successful one (§3.4). One run in
eight went `0 → 500` and stayed — enough to make "dead path" unlikely, not enough to say "the wiring
works": that run came from a pre-fix instrument and did not reproduce in a 2×2 over its own cell. §3
has the chain and the four numbers that fit supersession badly.

**The single highest-value next action is NOT to build a fix — it is to run the test that already
exists.** `util/ad-hoc/e2e_f039_supersession_test.py` (2026-09-02) was written for exactly this
hypothesis on F-CANOPY-039: it disables the competing cadence **at runtime via `setProps` — no code
change, no restart** — on the reasoning that if supersession is right, removing the competing cadence
should make it paint. Point it at `metrics-panel-metrics-store`. One drive discriminates supersession
from the failed-response candidate, before a line of canopy code is written.

**When a fix is built** it is a **juniper-canopy** change. Where: `update_metrics_store` at
`juniper-canopy/src/frontend/dashboard_manager.py:4082-4103`; the CRITICAL note referenced below is
`:4074-4081`; the handler is `_update_metrics_store_handler` at `:7004`.

Three cautions, all load-bearing:

1. **The poll's Input shape is deliberate.** The CRITICAL note explains why `ws-metrics-buffer` is
   **not** an Input to `update_metrics_store` — a chained Input whose producer `no_update`s makes Dash
   skip the interval-only callback, silently re-creating the I-1 starvation. Trigger-gating must not
   re-introduce that.
2. **Do NOT raise `FAST_UPDATE_INTERVAL_MS`** (`juniper-canopy/src/canopy_constants.py:370`) to
   lengthen the poll. It is the shared fast lane: `src/tests/unit/frontend/test_stage2_global_lane.py`
   pins its exact membership, `src/tests/unit/test_constants.py` pins the value at 1000, and
   `network_visualizer.py:1881,1923` derives the **cascade-add glow timing — M-TOPOLOGY-16, a row this
   arc still owes** — from it. Give `update_metrics_store` its own Interval, or gate it clientside.
3. **A faster handler is not obviously futile.** Against the *measured* re-request gap (median
   1.716 s) rather than the 1.0 s constant, the margin is **~0.11 s (~6%)**. "Suppress the TRIGGER, not
   the work" is this arc's standing prior from `reference_dash_renderer_12_slot_starvation.md` — it is
   **not** a result of this measurement, and the measurement fits it poorly (§3.4). Every candidate is
   untested.

And the standing warning from `feedback_e2e_finding_mechanisms_are_unreliable.md`: on this arc,
**symptoms hold; mechanisms and fix directions often do not.** This finding is now a live instance of
exactly that.

Beyond that, the outstanding work is much larger than an earlier draft of this document claimed:
**27 BLOCKED matrix rows** (§5 and §5.1 — not two, and two whole blocks are drivable today with one
command each), the 16 open findings (§7), the ledger's own still-owed list (§7.1), and the
F-CANOPY-038 relationship F-035's result reframes (§3.4). **There are no unverdicted rows** — §4
explains why the coverage tool says otherwise. None of these are blocked on each other. The fixture is
live and saturated at 48 hidden units; §6 says how to drive growth without destroying it.

This session wrote **no product code in any repo**. Everything it added is documentation and ad-hoc
instrumentation, and none of its instruments patch a running service — so there is nothing staged,
nothing to revert, and no half-applied state to inherit.

---

## 2. State at handoff

*Every number below is a 2026-09-07 snapshot. §10 re-derives the findings and fixture rows; the
M-TOPOLOGY counts, the PR table and the service map have no tool — recount them before relying on them.*

| | |
|---|---|
| Findings ledger | 55 total / 37 fixed / 1 accepted / 1 withdrawn / **16 open** (3 P1, 13 P2), **zero P0** |
| Matrix rows | 298 total, **296 verdicted**, 2 remaining (`M-PARAMETERS-02`, `M-PARAMETERS-03`) |
| M-TOPOLOGY section | **16 PASS / 0 FAIL / 2 BLOCKED** (`-11` select-drag, `-16` cascade-add glow) |
| cascor fixture | `2 / 48 / 2 / 1324`, `max_hidden_units` 48, saturated, `COMPLETED`, uuid `1cd15120-8f71-4319-ab7d-a384bfd692a9` |
| Services | `:8050` shared canopy (up) · **`:8051` the arc's isolated-stack canopy (up)** · **`:8101` juniper-data (up — the verify script's default backend; a leg without it is half-dead)** · `:8202` cascor (up) · `:8201`/`:8211` deploy stack (up — **do not touch**) · `:8052` verify leg (**down** — every instrument in §9 defaults to it; bring it up per §8) |
| juniper-ml PRs this session | **#1790** (merged 09-05T20:38Z), **#1794** (09-05T20:49Z), **#1810** (merged 09-07T13:31Z, `fea75cde`, 11 files — the dispatch probe, 8 transcripts, the ledger and `util/ad-hoc/README.md`); **#1812** open, 6 commits, auto-merge armed |
| Product code changed | **none**, in any repo |

---

## 3. F-CANOPY-035 — the evidence chain, so you can attack it

All of this is in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` under the
F-CANOPY-035 entry; this is the short form with the numbers that matter.

### 3.1 The symptom, reproduced on demand

`util/ad-hoc/2026-09-04_f035_candidate_loss_redrive.py` drives the Candidate Metrics tab and parses
store writes off `/_dash-update-component`. **The write count is run- and window-specific, not a
constant of the instrument** — quote the run, never the instrument:

| run | artifact | writes × 500 rows | `omitted` / `unparsed` | store before → after |
|---|---|---|---|---|
| 2026-09-05 #1 | `…_redrive.txt` (30 s) / `.json` (lifetime) | **17** in 30 s — the `.json` says 46 | 0 / 0 in 30 s; **7** unparsed over the lifetime | 0 → 0 |
| 2026-09-05 #2 | `…_redrive_v2.json` | 14 (30 s window) | 0 / 0 | 0 → 0 |
| 2026-09-07 | `…_redrive_v3.json` | 18 (30 s window) | 0 / 0 | 0 → 0 |

The invariant across all three is the last column: **the store reads `len=0` before and after, every
time.** **The comparable 30 s figure for run 1 is 17, not 46** — its censuses had not yet been fixed to
detach their listeners, so its `.json` reports the whole ~78 s listening lifetime while its `.txt`
reports the 30 s window. The ledger treats 17 as canonical. Quote 17; that pair is retained
deliberately, with the diagnosis, in
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`. **Do not cite that pair's `.json`
and `.txt` as one run's numbers.**

The 2026-09-07 run was driven on the same leg and commit as the renderer-probe runs, which is what
shows the difference is not the build — but note that **no F-035 artifact records a commit SHA**; that
linkage is recorded in the ledger prose, not in the evidence files, and the ledger's two SHAs for
this leg contradict each other (§0 item 2). Writing the serving commit into the artifacts is
outstanding work — item 7 of §7.1.

### 3.2 Four explanations eliminated by measurement

- **A second store instance** — refuted by `util/ad-hoc/2026-09-05_dash_layout_id_census.py` against
  `/dashboard/_dash-layout`: **465 id-bearing nodes, 465 distinct, zero duplicate ids anywhere**, the
  store exactly once with `data=[]`. This is a vantage point `state.paths.strs` structurally cannot
  provide, because it maps one id to one path and cannot *represent* a duplicate. **Bound:** the census
  reads the **server-declared** layout, so a duplicate created at runtime by a callback returning
  `children` is outside its field of view — as it is outside `paths.strs`'s. Two instruments each blind
  to one half of the space are not jointly exhaustive.
- **The ungated `allow_duplicate` appender** (`append_ws_metrics_store`) — refuted twice: statically,
  `_append_ws_metrics_store_handler` opens `if not ws_events: return dash.no_update`, so it cannot
  write an empty value at all; empirically, `ws-metrics-buffer` held its mount default with `gen`
  **0 → 0**, so it never fired.
- **A stale server-side view** — refuted by the F-039 topoprobe: **130 comparisons**, every one
  `eq=False` at a constant `cur_len=2` (the serialised `[]`) against `new_len=164570`.
- **A reducer that drops a value it was handed** — refuted by
  `util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py`: across **four of its five runs**
  (5,230 / 9,794 / 10,425 / 10,616 dispatches) **zero** dispatched actions carried a value for the
  store. **The fifth run is the one where the store succeeded** — 3 `Callbacks.Aggregate` actions
  carrying 500 rows, store `0 → 500`, independent read 500 (§3.4).
  **But it was NOT the same matcher.** That fifth run used the *pre-fix* matcher (its `dispatches`
  array still holds the 577 bogus `SET_PATHS` hits). The fixed matcher has run four times and produced
  **four zeros and no positive instance ever** — so the dispatch probe's zero is uncontrolled in
  exactly the sense §3.3 addresses for the lifecycle probe. **Building that control is outstanding
  work**; until then, treat "the payload never reaches the reducer" as supported by the store reads and
  the pre-fix positive, not by a controlled instrument.

### 3.3 The mechanism, and the number that carries it

`util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py` reads dash-renderer's own pending-callback
bookkeeping out of the same Redux store (`state.callbacks`: `requested` / `prioritized` / `blocked` /
`executing` / `watched` / `executed` / `stored`). Two 90 s replicates, ~3,000 Redux notifies each,
counting only callbacks with the store **as an output**:

| | run 2 | run 3 |
|---|---|---|
| present in `watched` | 2,344 | 2,731 |
| present in `executed` / `stored` | **0** | **0** |
| **distinct entries into `watched`** | **23** | **26** |
| store length throughout | `0` | `0` |

**The entry count is the load-bearing number.** "Present for 2,344 notifies" is satisfied by two
mechanisms needing *opposite* fixes — a series of calls each superseded, or one call whose promise
never resolves. Only counting absent→present transitions separates them. 23 and 26 separate entries:
supersession.

It fits the independent timing: `FAST_UPDATE_INTERVAL_MS = 1000`
(`juniper-canopy/src/canopy_constants.py:370`) against a **median round trip of 1.827 s** measured by
`util/ad-hoc/2026-09-05_f035_store_write_latency_probe.py`.

**THE ZERO IS BETTER SUPPORTED, AND STILL NOT PROVEN TO BE A MEASUREMENT.** Consensus round 1
objected — correctly — that this instrument had never produced a non-empty terminal bucket, making
`terminal=[]` an *uncontrolled* zero. Two things were then done, and a Lane B review showed neither
fully closes it:

- **A control on `theme-state`** reports `terminal=['stored']` across 1,987 notifies — but its
  `entries: {stored: 1}` and `maxRun: 1987` mean **one entry, resident for the whole window**, already
  there when the watcher armed. It shows the matcher can *read a resident entry*; it does **not** show
  the sampler can catch a **transit**, which is the actual blind spot (§13 trap 5). It also ran 45 s on
  a one-shot page-load callback, not 90 s on a 1 Hz poll, and its own committed verdict block reads
  `EXECUTED-NOT-APPLIED … the retirement hypothesis should be dropped` — a false read from the `len()`
  test on a string-valued store. **Do not cite that artifact's verdict.**
- **A shape census** confirms `stored` holds **32–34** entries (32 in the topology run, 33 in the
  control, 34 in the inventory) of which **all** expose `callback.outputs`,
  so the matcher's shape assumption holds for the list the verdict rests on.

**A SECOND CONTROL RETURNED THE SAME VERDICT ON A DIFFERENT STORE.**
`network-visualizer-topology-store` — chosen because M-TOPOLOGY is 16 PASS — also returned
`RETIRED-BEFORE-EXECUTION`, 9 entries into `watched`, `terminal=[]`. It was set aside because a direct
read showed it at `hidden_units: 0`, i.e. empty too. **That dismissal is circular**: §7 flags the very
same reading as a single unreplicated observation nothing may be concluded from. Either it is evidence
(and the control is invalid) or it is not (and the control stands, and the verdict does not
discriminate a broken store from a working one). **Until re-driven, treat the lifecycle verdict as
non-discriminating.** Artifacts: `2026-09-07_f035_lifecycle_POSITIVE-CONTROL_theme-state.json`,
`2026-09-07_f035_lifecycle_control_topology-store.json`, `2026-09-07_f035_callbacks_list_inventory.txt`.

### 3.4 What this reframes, and what it does not settle

- **F-CANOPY-035 and F-CANOPY-039 die at different points.** F-039's lifecycle *completes* and its
  result is dropped on the way to being applied; F-035's lifecycle *never completes*. Same family, not
  the same defect. An earlier ledger note that this "supports F-035/-038/-039 being one defect" should
  be read with that distinction.
- **F-CANOPY-038 (OPEN, P2)** — the Stage-2 no-op-write suppression present in one place and not
  another — sits in the same family and has not been re-examined against this result. Worth doing
  before anyone assumes it is a separate defect.
- **FOUR NUMBERS THAT FIT SUPERSESSION BADLY**, all from this arc's own artifacts: the measured
  re-request gap is **1.716 s** against a 1.827 s round trip — a **0.11 s** margin, not the 0.8 s the
  1.0 s constant implies; **9 of 29** in-flight calls were **not** overlapped and the store still read
  0; the writer enters `watched` **once per ~3.7 s**, three and a half times *slower* than the 1 Hz
  trigger (supersession predicts ~90 entries per 90 s, not 23–26); and **two concurrent entries were
  never observed once** (`everSeen: {watched: 1}` in both replicates) — supersession's direct
  observable never appeared.
- **AN UNELIMINATED FIFTH MECHANISM, better correlated than supersession**: `Callback failed: the
  server did not respond` appeared in the console of **2 of the 4** failing probe runs and **none** of
  the successful one. A response the renderer treats as failed or aborted produces the identical
  signature and needs a *different* fix from trigger-gating.
- **AN UNEXPLAINED INSTRUMENT RESULT that cuts against the verdict**: `stored` never showed an entry
  even *touching* `metrics-panel-metrics-store` in any lifecycle run, though that store is an `Input`
  to the plots, tiles and candidate panel and `stored` holds 30+ entries. The `theme-state` control by
  contrast shows `stored: 3` in `touchHigh`. This is live evidence for the structural-blindness reading.
- **THE THREE INSTRUMENTS ARE NOT INDEPENDENT.** The redrive, dispatch and lifecycle probes share a
  Playwright driver (`e2e_seg17_topology_driver.py`), a browser, a leg and the `state.paths.strs`
  reader; the lifecycle probe's docstring takes the dispatch probe's result as its *premise*. That is a
  chain, not a triangulation, and two of the three have already mislabelled their own most important run.
- **NOT settled**: *which* rule performs the supersession — and note the four numbers above make
  supersession itself uncertain, so this is now "which mechanism, of at least two candidates".
- **NOT settled**: why the store succeeded in exactly one run of eight. A 2×2 over {fresh server,
  loaded server} × {reload, no reload} showed it **does not reproduce in its own cell**. It is recorded
  as an unexplained anomaly whose *existence* is the finding.
- **Sample sizes are small, and two of the runs are PRE-FIX artifacts.** n=2 for the entry counts
  (only lifecycle runs 2 and 3 carry `entries`); n=3 for "never terminal" — but lifecycle run 1 was
  produced by a pre-fix build of the probe whose verdict the committed rule would not reproduce, so
  treat that n as 2 + 1. The dispatch probe's `run1_applied` is likewise a pre-fix artifact (its
  `dispatches` array still contains the 577 bogus `SET_PATHS` hits) whose `result` block was
  **relabelled from its saved data**, annotated in-file with a `relabelled` key. Its *observation* —
  store `0 → 500`, independent read 500 — is unaffected by either.
- **"1 run in 8" pools two instruments.** The denominator is 5 dispatch-probe runs + 3 lifecycle runs,
  each of which records an independent store read; 7 read `0` and one read `500`. It is a real count
  but **not a controlled rate** — different instruments, 60 s vs 90 s windows, and three different
  arming strategies. Do not treat it as a probability.

---

## 4. There are NO unverdicted rows — the coverage tool's "2 remaining" is a known artifact

`util/ad-hoc/e2e_row_coverage.py` reports `M-PARAMETERS-02`/`-03` as remaining. **They are not.** Both
carry `PASS` in the matrix, and the ledger adjudicates the disagreement explicitly
(`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, the M-PARAMETERS-01/02/03
entry): the bullet parser deliberately credits only the **leading** token of a slash enumeration
(`M-PARAMETERS-01/02/03 → PASS`), and *"`e2e_row_coverage.py` is a coverage estimator, not the ledger;
the matrix is the ledger… Left as-is and recorded here rather than quietly reconciled."*

**Do not re-drive these two rows.** Where the estimator and the matrix disagree, **the matrix wins** —
which is the exact inverse of what an earlier draft of §10 told you to do. `util/ad-hoc/e2e_unfilled_rows.py`
exists because a previous handoff published the estimator's row list under the ledger's headline; this
one nearly repeated it.

### 4.1 How a verdict actually lands

`e2e_append_statuses.py` appends to a **run's TSV**, not to the matrix — an earlier draft named it as
the matrix filler, which it is not. The real pipeline:

1. Drive the row from the matrix's own §4 scripts (canonical for step detail).
2. `python util/ad-hoc/e2e_append_statuses.py reports/e2e/<RUN>/statuses.tsv rows.json`
   — `rows.json` is a list of `{row_id, status, notes, screenshots?}`.
3. `python3 util/ad-hoc/e2e_matrix_fill.py --verdicts reports/e2e/<RUN>/statuses.tsv --write`
   (dry-run by default; `--overwrite` only to revise an existing verdict).
4. Re-run `e2e_row_coverage.py` **and** `e2e_unfilled_rows.py` and diff them.

`reports/e2e/CURRENT_RUN_ID` currently reads `20260826T215010Z` while run dirs exist through
`20260831T000000Z`; open a new run dir and bump it.

---

## 5. The two BLOCKED M-TOPOLOGY rows

Neither is blocked on F-CANOPY-037 or -039 any more — both of those are closed and the rebuild paints.
The reasons differ and conflating them would mis-attribute a product defect to missing tooling.

- **M-TOPOLOGY-11** — box / lasso select on `network-visualizer-graph`.
- **M-TOPOLOGY-16** — cascade-add glow, a purely visual time-based highlight driven off the metrics
  delta. **This one is drivable right now**: it needs a live cascade-add event, and §6 says how to
  produce one without destroying the fixture. `util/ad-hoc/2026-09-05_f037_growth_trigger_probe.py`
  already drives and instruments a growth event and can be reused nearly as-is.

---

### 5.1 The other 25 BLOCKED rows — two blocks are one command from done

The matrix carries **27 BLOCKED cells**, not two. An earlier draft of this document named only
`M-TOPOLOGY-11` and `-16`, which would have left a successor believing the frontier was two rows wide.
Per the matrix's own §7 contract, `BLOCKED` is an input to the remediation backlog — **not** a done
state.

| block | rows | real state, per the ledger |
|---|---|---|
| `M-METRICS-11..16, -18` | 7 | Replay transport. Controls *do* reveal at `COMPLETED`, but `metrics-panel-replay-position` stays `0 / 0` so `max_index=0` clamps every transition. **`M-METRICS-13` is the discriminator to re-drive first** — data-independent, and it failed with zero wire output across 196 responses. Whether this is a third face of F-CANOPY-027 or its own defect is **not established and no finding is filed**. Drivable today on the `COMPLETED` fixture. |
| `M-DATASET-17..26` | 10 | Sequence (3-D) controls. **Not a defect** (owner decision 4): `equities`/`equities_seq` read `available:false` because the data leg lacked the optional extra. Recipe: bring the stack up with `JUNIPER_E2E_DATA_EXTRAS=api,equities`. The remaining half is an **unanswered owner question** — should the live 3-D arm drive `/api/stage_dataset`, or be re-scoped to the demo lane? The both-arms answer **needs new matrix rows**, so the 298 denominator is expected to grow. |
| `M-CANDIDATES-10/-11` | 2 | Dead-click `DEAD-EXPECTED`. The test is **ready in the driver** (`util/ad-hoc/e2e_f027_redrive.py --step cardsprobe`) and was waiting on F-CANOPY-036's fix — **which shipped as canopy#536**. One command; also unblocks the `M-CANDIDATES-09` FAIL. |
| `M-SNAPSHOTS-20/-21`, `C2.10-03`, `M-DATASET-03`, `M-METRICS-27`, `M-EVOLUTION-07`, `M-BOUNDARIES-07` | 6 | Assorted; `C2.10-03` and `M-SNAPSHOTS-20/-21` are named in the ledger's "still owed". `M-SNAPSHOTS-20/-21` are `DEAD-EXPECTED` rows scored `BLOCKED`, meaning the terminal `DEAD-CONFIRMED` was never earned. |

---

## 6. Fixture control — read before touching cascor

The fixture is **grown, never rebuilt**; the uuid has been stable throughout the arc and is the check
that it was never recreated.

```bash
# Grow (raises the cap, then restarts training; the network survives)
curl -X PATCH -H 'Content-Type: application/json' \
     -d '{"max_hidden_units": 52}' http://127.0.0.1:8202/v1/training/params
curl -X POST  -H 'Content-Type: application/json' -d '{}' \
     http://127.0.0.1:8202/v1/training/start
```

**`POST /v1/network` DESTROYS the fixture.** Do not use it. The pre-growth state (40 units) is
recoverable from snapshot **`snapshot_20260905T103912Z`** (815,937 bytes, `juniper.cascor` format v2;
the creation response reports `size_bytes: 0` before flush — that is a pre-flush artifact, not a
defect, and it was checked before being dismissed).

Every ledger and matrix row quoting the older `2/40/2/944` fixture was measured against it and remains
valid *for that build and that fixture*. **Do not read a new `48` as a regression.**

---

## 7. The 16 open findings

Reproduce with `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_finding_triage.py`.

**P1 (3)** — `F-CANOPY-035` (cause found, fix not built — §1, §3); `F-CASCOR-001` (CUDA OOM in
candidate seeding misclassified as "Completed — stalled"); `F-CASCOR-002` (snapshot restore always
drops optimizer state).

**P2 (13)** — `F-CANOPY-001`, `-012`, `-013`, `-015`, `-018`, `-026`, `-028`, `-032`, `-033`, `-034`,
`-036`, `-038`, and `F-ML-002`. Three findings worth flagging, plus one thing that is deliberately
**not** a finding:

- **`F-CANOPY-036`** — candidate pool history never accumulates in the live lane. **Its fix already
  shipped** as **canopy#536** (server-side accumulation, on the owner's decision). The entry is OPEN
  only because the **live verification is owed: a run with the Candidate Metrics tab open.** That same
  run discharges `M-CANDIDATES-09/-10/-11` via `util/ad-hoc/e2e_f027_redrive.py --step cardsprobe`.
  **Do not run it concurrently with Phase 2 of
  `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md`** — the ledger records
  that conflict. (An earlier draft of this document described F-036 as an undiagnosed race and sent the
  successor to open a mechanism investigation into a defect whose fix had merged.)
- **`F-CANOPY-038`** — see §3.4.
- **AN OBSERVATION TO RE-DRIVE, deliberately not filed.** While building the positive control on
  2026-09-07, a direct read showed `network-visualizer-topology-store` holding **`hidden_units: 0`**
  against a 48-unit fixture, on canopy `de253e9`. That is not what M-TOPOLOGY's 16 PASS would predict.
  It is **one unreplicated read, taken for another purpose, on a tab open ~12 s**, and this arc has a
  standing rule against filing from a single session. Re-drive it before concluding anything; if it
  holds, it is a regression and a new finding, and if it does not, nothing was lost.
  Artifact: `reports/e2e-canopy-2026-09-02/transcripts/2026-09-07_f035_lifecycle_control_topology-store.json`.
  Command: `util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py --store network-visualizer-topology-store`.
  **This reading is also load-bearing for §3.3** — it is the sole ground on which that control was set
  aside, so re-driving it settles two things at once.
- **`F-CANOPY-033`** — `RESET_COMPONENT_STATE` storms one panel at ~13/s. The renderer probe's action
  census recorded, across **five** 60 s runs: **996 / 2,653 / 4,488 / 4,872 / 5,543** — i.e.
  **~17–92/s**, a range spanning roughly 1.1× to 6× and highly run-dependent, *not* a stable multiple.
  (An earlier draft quoted only the top three and called it "6×".) It was the single most frequent
  action type in **3 of 5** runs. Note also that the finding's `~13/s` is the superseded figure: the
  ledger already carries a **2026-08-28 re-measure at ~15/s with a re-attribution** away from Cassandra
  to `network-info-panel` / `network-info-details-panel` / `network-evolution-grid-container`. The owed
  action on that row is a **live redux re-trace**, which the ledger records as deferred for want of one.

---

### 7.1 Carried forward from the ledger's own "still owed" list

These are recorded in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and were
absent from an earlier draft of this handoff:

1. **F-CANOPY-026's live confirmation needs a MID-RUN sample.** `phase_started_at` is cleared once a
   run completes, so a post-run probe reads `None` and proves nothing. **The fixture is `COMPLETED`, so
   this item is unreachable until you grow it (§6) and sample during training.**
2. **F-CANOPY-033 needs a live redux re-trace** — deferred for want of one; no root cause in source.
3. **F-CANOPY-038's re-measure is one command**: `util/ad-hoc/e2e_seg17_topology_driver.py --step storestorm`.
4. **The topology re-drive F-CANOPY-037 was waiting for.**
5. **A live re-drive of every row the eight recent fixes touch** — `C2.9-05`, `M-PARAMETERS-04/-05/-06`,
   `M-METRICS-03`, `M-WORKERS-02`, `C2.1-01/-02`, plus the Network Editor patch rows. Their verdicts
   predate the fixes that touched them.
6. **`W5-21` / `W5-23` on a V2 snapshot with non-empty history**, and the `f031` driver step.
7. **Record the serving commit in every driver's result artifact.** No F-035 artifact contains a SHA,
   which is why §0 item 2's contradiction cannot be adjudicated. One line in each driver
   (`git -C <canopy> rev-parse --short HEAD` at launch, written into the result dict) closes a class of
   error this arc has now hit twice — #1794's `785fb64` and the `f56f46c`/`de253e9` split.

---

## 8. Standing up a leg to drive rows

Never drive the shared `:8050` leg for row work — it is someone else's, and its serving commit is
unknown. Stand up a dedicated one from a worktree at a **known commit**, and say which commit in
anything you write, because *a checkout is not a deployment*: a long-running leg serves the code it
imported.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git worktree add /home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--probe--<task>--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main) --detach origin/main
bash util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <that-worktree>/src 8052
# ... drive ...
bash util/ad-hoc/2026-09-04_canopy_verify_instance.bash down 8052   # BY PID, never by port
```

The `up` argument is the directory **containing `main.py`**, i.e. `<worktree>/src`, not the worktree
root. Teardown is by pid from the run-dir pid file — which is also one of the orphan reaper's two
protection keys, so leave the pid file alone while the leg is up.

---

## 9. The instrument inventory — check it before building anything

This session built a `store.dispatch` wrapper before noticing that
`util/ad-hoc/e2e_f039_renderer_apply.py` (2026-09-02) already was one — and then, in the first draft of
this very section, **omitted `e2e_f039_supersession_test.py`, the instrument written to test this
finding's own hypothesis.** That is the failure this section exists to prevent, committed twice in one
session. **Read this list first, and grep `util/ad-hoc/` before writing anything.**

**Every browser-side instrument below defaults to `http://127.0.0.1:8052`, which is DOWN.** Run §8
first, or pass `--url` / `JUNIPER_E2E_CANOPY_URL`.

| instrument | what it answers | revert needed? |
|---|---|---|
| `util/ad-hoc/e2e_finding_triage.py` | finding counts and dispositions | no |
| `util/ad-hoc/e2e_row_coverage.py` | which matrix rows lack a verdict | no |
| `util/ad-hoc/e2e_append_statuses.py` | append verdicts to the matrix | no |
| `util/ad-hoc/2026-09-04_f035_candidate_loss_redrive.py` | drives M-CANDIDATES-07; parses store writes off the wire | no |
| `util/ad-hoc/2026-09-05_dash_layout_id_census.py` | duplicate component ids, server-side | no |
| `util/ad-hoc/2026-09-05_f035_store_write_latency_probe.py` | round trip vs re-request interval | no |
| `util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py` | did the payload reach the reducer | no |
| `util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py` | callback lifecycle via `state.callbacks`. `--discover` prints a per-list output-shape census; `--store <id>` re-points it at another store (that is how a control is *built* — it is not a control by itself, see §3.3). It writes the list inventory into **every** artifact, and returns **BLOCKED** rather than a verdict if no list matches the terminal hints — which is what stops a future dash-renderer rename silently reproducing "retired". | no |
| `util/ad-hoc/e2e_f039_renderer_apply.py` | pre-existing dispatch wrapper (F-039) | no |
| `util/ad-hoc/e2e_f039_topoprobe_instrument.py` | server-side State comparison | **YES — `revert` before committing** |
| `util/ad-hoc/2026-09-05_f037_growth_trigger_probe.py` | drives + instruments a cascade-add | no |
| `util/ad-hoc/2026-09-04_canopy_verify_instance.bash` | stand up / tear down a leg by pid | no |
| **`util/ad-hoc/e2e_f039_supersession_test.py`** | **disables the competing cadence at RUNTIME via `setProps` — no code change, no restart. The discriminating test for §1's hypothesis.** | no |
| `util/ad-hoc/e2e_seg17_topology_driver.py` | the shared Playwright driver; `--step storestorm` is F-CANOPY-038's one-command re-measure | no |
| `util/ad-hoc/e2e_f027_redrive.py` | `--step cardsprobe` discharges `M-CANDIDATES-09/-10/-11` | no |
| `util/ad-hoc/e2e_matrix_fill.py` | **the actual matrix filler** (§4.1) | no |
| `util/ad-hoc/e2e_unfilled_rows.py` | the check that stops an estimator artifact being published as the frontier (§4) | no |
| `util/ad-hoc/e2e_f039_metrics_store_soak.py` | drives samples for the topoprobe against the metrics store | no |

---

## 10. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/functional-crafting-metcalfe
git fetch origin main && git log --oneline -1 origin/main

# 1. Is #1812 in? (read the field, not the exit code)
gh api repos/pcalnon/juniper-ml/pulls/1812 --jq '{merged,merged_at}'

# 2. Findings — expect 55 / 37 / 1 / 1 / 16, zero P0
LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_finding_triage.py | tail -8

# 3. Matrix — expect 298 rows, 296 verdicted, "remaining: 2". Those 2 are the KNOWN
#    slash-enumeration artifact (§4), NOT work. Cross-check with the unfilled-rows tool.
LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_row_coverage.py | head -5
LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_unfilled_rows.py | head -5

# 4. Fixture — expect hidden_units 48, uuid 1cd15120-...
curl -s http://127.0.0.1:8202/v1/network

# 5. Services — expect 8050, 8051, 8101, 8201, 8202, 8211 listening; 8052 absent until §8
ss -ltn | grep -E ':(8050|8051|8052|8101|8201|8202|8211)'

# 6. M-TOPOLOGY's 16/0/2 has NO tool — recount the verdict column by hand
grep -cE '^\| M-TOPOLOGY-[0-9]+ .*\| PASS \|' notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md

# 7. canopy origin/main — §3's file:line are pinned to f56f46c
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy fetch -q origin main
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy rev-parse --short origin/main
#    If this is not f56f46c, re-verify every file:line in §1 and §3 before quoting it.
#    The local checkout is often several commits behind origin/main — check both.

# 8. Fixture FSM status (load-bearing for §5.1's replay block and §7.1 item 1)
curl -s http://127.0.0.1:8202/v1/training/status
```

If **(2)** disagrees with §2, trust the tool and correct this document — the finding counts are
tool-produced and the arc moves daily. **If (3) disagrees, trust the MATRIX, not the tool** (§4): the
coverage script is an estimator and its "2 remaining" is a known, deliberately-preserved artifact.

---

## 11. Consensus validation — two rounds, and what they cost

Run under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`. Sized
to the top-right cell of its §3: a document of record that gates a successor's work, aggregating a
multi-day arc, written by the session that produced the findings (the **convenient-finding**
escalator), containing universal quantifiers, with a fix hanging on it. That cell requires **3+ Lane A
at distinct entry points, 2+ Lane B on opposing briefs, and at least 2 iterations.**

**Lane A — measurement re-creation, three reviewers, three entry points.** (1) live tooling and
services; (2) git and PR history; (3) the raw evidence tree and instrument source. Convergent findings:

- Reviewers 1 and 2 **independently made the same finding their #1**: juniper-ml **#1810** was missing
  from the document, and the "eleven evidence files" figure was exactly what you get by dropping it.
  True count 22.
- The §7 `RESET_COMPONENT_STATE` census was attributed to ~90 s windows; every run is 60 s.
- #1812's commit count, the "clean tree" claim, and "nothing stashed" were all wrong as written.
- The §3.1 write count was one run's figure presented as three runs'.
- Reviewer 3 found the **decisive** objection: the lifecycle probe **had never produced a non-empty
  terminal bucket on any run**, so `RETIRED-BEFORE-EXECUTION` was an *uncontrolled zero*.

**Action taken mid-review**: #1812's auto-merge was **disarmed** rather than allowed to land the claim,
and a positive control was built (`--store`). It resolved *in favour* of the instrument — which is why
the control, not an argument, is what settled it.

**Lane B — adversarial, two opposing briefs on the reconciled measurement**, plus a round-2 pass briefed
**only on the corrections** (§4 of the procedure: *"the fix pass is the least trustworthy part of any
document"*). Both Lane B reviewers returned **DO NOT SHIP**, on unrelated grounds:

- **Over-claiming lens**: the mechanism claim does not survive its own arithmetic — a 0.11 s measured
  margin (not 0.8 s), 9 of 29 calls unopposed, a scheduling rate 3.5× *slower* than the trigger, and
  two concurrent entries never once observed. The dispatch probe's zero is **also** uncontrolled (its
  only positive came from the pre-fix matcher). The `theme-state` control shows a *resident* entry, not
  a transit. A **fifth mechanism** (a response the renderer treats as failed) is uneliminated and
  better correlated. The three instruments are **not independent** — shared driver, browser, leg and
  store reader.
- **Omission lens**: §4's "two unverdicted rows" was a **known, deliberately-preserved coverage-tool
  artifact** — both rows already carry `PASS`, and §10 told the successor to trust the tool over the
  matrix, the exact inverse of the recorded decision. The real frontier is **27 BLOCKED rows**, two
  blocks of which are one command from done. F-CANOPY-036 was described as an undiagnosed race when its
  fix had **already shipped** (canopy#536) and only a verification run is owed. And §9 — the section
  whose entire purpose is "do not rebuild an instrument that exists" — **omitted
  `e2e_f039_supersession_test.py`, the instrument written to test this finding's own hypothesis.**
- **Round 2 on the corrections** found that the fix pass **introduced six new errors**: a commit
  decomposition summing to 5, a cherry-picked 3-of-5 range, a lifetime count seated beside two windowed
  counts, one file listed as both added and pre-existing, a false "not on the branch", and a dead `§11`
  pointer.

**What changed as a result.** The headline was demoted from *"the mechanism is named"* to *"the
lifecycle never completes; why is not established"*, in this document **and in the ledger**; §4 was
replaced wholesale; §5.1, §7.1 and six instrument rows were added; and every number above was
re-derived. **#1812 remains disarmed** — see §12.

**Outstanding after two rounds, and the reason this is honest rather than finished:**

1. Build a **positive control for the dispatch probe** (its fixed matcher has never produced one).
2. Re-drive the `network-visualizer-topology-store` reading — it is load-bearing in two directions at
   once (§3.3's control validity and §7's observation).
3. Run `e2e_f039_supersession_test.py` against the metrics store to discriminate supersession from the
   failed-response candidate.

A third round was not run. Per §4's termination rule, stop when a round produces no finding that
changes a number, a disposition or an action — round 2 produced six, so **the honest state is
"validated, with three named gaps", not "validated".**

---

## 12. Git status at handoff

- **Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/functional-crafting-metcalfe`
- **Branch**: `docs/f035-supersession-mechanism`, pushed. Working tree carries **only this handoff
  document** until it is committed; nothing else is modified or staged.
- **PR**: juniper-ml#1812 — **6 commits: 3 content + 3 main-merges** (`d895d049`, `ec6be8d2`,
  `89bae418`; merges `fe034f55`, `a795ffa9`, `21fe197e`). An earlier draft said "2 content + 2 merges",
  which sums to 5 and undercounts the merges. It was **disarmed
  twice**: once while consensus round 1's control objection was open, and again when Lane B refuted the
  mechanism claim. **It is disarmed at the time of writing and must not be re-armed until §11's
  outstanding items are closed.** Confirm with `gh pr view 1812 --json autoMergeRequest`.
- **10 stashes exist in juniper-ml and 4 in juniper-canopy; none are from this session** and none
  should be popped. (The earlier draft said "nothing stashed", which was true of this session and false
  of the repo.)
- **No product code touched in any repo** — verified against the full `--name-status` of every PR, not
  against prose: every file is under `notes/`, `reports/`, `util/ad-hoc/` or `prompts/`.
- **No instrument left applied.** The topoprobe was reverted 2026-09-05; `grep -r TOPOPROBE` over
  juniper-canopy and its worktrees returns zero, and no canopy commit ever contained the string. Note
  the probe worktree was also deleted, which erases residue either way — the absence is *consistent*
  with the revert rather than proof of it. Every instrument added since is browser-side only.
- Probe worktrees created this session were removed and pruned.

---

## 13. Traps

Each of these cost this arc real work. The first three are the expensive ones.

1. **A key match is not a value match.** Searching a structure for an id and taking whatever sits
   there counts the wrong thing with total confidence. The dispatch probe matched dash-renderer's
   *paths index* and reported **577 bogus hits at `len=18`** — a path length dressed as a row count —
   against 3 real ones, a 192× over-count. Require the matched position to have the *shape* of what
   you want.
2. **A pre-registered rule does not protect a branch that encodes the expected answer.** The same
   probe's reading rule was fixed before the run, and still mislabelled its single most important
   observation, because the `carrying and reached` branch *asserted* "something reverts it afterwards"
   without testing for a revert. Write each branch's test, not its expected story. Relabel from saved
   data rather than re-running.
3. **Do not attribute a difference to a procedural detail on n=1.** One run populated the store where
   every other read empty, differing by a `page.reload()`. "Reload fixes it" survived until a 2×2 drove
   the anomalous cell again — where it did not reproduce.
4. **A presence count cannot distinguish supersession from a stuck request**, and they need opposite
   fixes. Count absent→present transitions.
5. **Sampling on Redux notifies can miss a fast transit.** "Never reached a terminal list" is not
   self-supporting; it is closed here by two *other* instruments. Say which instrument closes another's
   blind spot rather than asserting a negative.
6. **`.gitignore:52` is `*.log`.** An archived run log with a `.log` extension is silently excluded and
   your summary will claim it was committed. Archive as `.txt` and prove it with `git check-ignore -v`.
7. **safe_merge's auto-merge net arms pinned to a head SHA and does not re-pin.** A commit pushed after
   arming is silently left behind while the PR merges — that is why #1794 exists. In a contended lane
   prefer `gh pr merge --squash --auto`, which tracks the PR and survives `update-branch` (verified
   again this session on #1812); it does not auto-sync a `behind` branch, so that step stays manual.
   **Treat arming as a freeze: land everything first, arm last.**
8. **W-series ids are not matrix row ids.** `e2e_row_coverage.py` reports ~129 "unmatched verdict
   tokens", nearly all `W<n>-NN`. That is expected — the W-series are workflow steps whose detail lives
   in the matrix's §4 scripts, not rows in the matrix table. A 2026-09-04 finding (F-E2E-007) was filed
   and **withdrawn** for exactly this confusion; do not re-derive it.
9. **canopy never reaches DOM stability** (title stuck at "Updating..."), so default clicks fail and
   the widgets are Radix. Use `locator.click({force:true})`; coordinate clicks go stale.
10. **A control must be shown POSITIVE before its negative result means anything.** The first attempt
    to control the lifecycle probe used a store believed healthy; it returned the same empty terminal
    bucket, which looked like proof the instrument was blind — until a direct read showed that store was
    empty too, so the run distinguished nothing. The mirror of the 2026-09-03 `blob:`/`data:` near-miss,
    where a control shared the mechanism under test. Both directions cost a wrong conclusion.
11. **The orphan reaper can kill a live leg.** The run-dir pid file is one of its two protection keys.
    Leave it in place while the leg runs, and tear down by pid, never by port.
