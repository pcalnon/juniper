# HANDOFF 2026-08-20 — Canopy E2E Phase 1: segment 16, the 32 unfilled matrix rows

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. Successor to
[`HANDOFF_2026-08-18_canopy-e2e-phase1-segment-15.md`](HANDOFF_2026-08-18_canopy-e2e-phase1-segment-15.md).

Segment 15 drove **54 rows** (212 → 266) and closed **nine** sections. What is left is lopsided: **24 of the
32 remaining rows are §3.6 Dataset View**, and the other 8 are singletons that each need their own posture.
This is the first segment where one block dominates, so plan around §3.6 rather than sequencing by section
number.

**Read order ≠ page order.** Execute: **(1)** Verify starting state → **(2)** Standing up the stack →
**(3)** §3.6 and its cold restart → **(4)** the 8 singletons → **(5)** Recording verdicts → **(6)** Landing.
Read *Traps* once up front; it is reference, not a step.

## Documents

| what                                                                       | path                                                                        |
|----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| matrix (the ledger)                                                        | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| evidence note (findings + per-segment record)                              | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`        |
| plan (§9 verdict vocabulary, §4.5 recurrence leg, merge policy `:689-690`) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`   |

## Verify your starting state first

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline -3 origin/main      # expect ml#1203 merged or later
git status --porcelain                                    # expect clean
gh pr list --repo pcalnon/juniper-ml     --state open --limit 10   # expect no arc/canopy-e2e-* PR
gh pr list --repo pcalnon/juniper-canopy --state open --limit 10
python3 util/ad-hoc/e2e_unfilled_rows.py                  # AUTHORITATIVE: 266 verdicted / 32 UNFILLED
python3 util/ad-hoc/e2e_row_coverage.py                   # estimator: 267 / 31 — the delta is EXPECTED
```

**The two tools disagree by one, and both numbers are right.** Unchanged since segment 11 and fully
explained: the estimator reads only the leading token of the `M-PARAMETERS-01/02/03` slash enumeration in
`reports/e2e/20260809T223851Z/rowlog.md:82` (−2, so it thinks `M-PARAMETERS-02`/`-03` are open when the
ledger has them `PASS`), and it over-credits three rows whose only record is a non-terminal `pending …`
(+3: `C2.4-02`, `M-WORKERS-02`, `M-TUTORIAL-04`). **The matrix is the ledger; the estimator is an
estimator.** Do not reconcile them, and **plan from `e2e_unfilled_rows.py`** — new in segment 15 precisely
because segment 15's own draft handoff published the estimator's list under the ledger's headline.

## The remaining 32 rows — ledger-derived, sums to 32

| section (line)                | unfilled | row ids                                            |
|-------------------------------|---------:|----------------------------------------------------|
| §2.4 WS badge (`:223`)        |        2 | C2.4-02, C2.4-05                                   |
| §2.5 training controls (`:246`)|       1 | C2.5-07                                            |
| §3.6 dataset view (`:519`)    |       24 | M-DATASET-01, 02, 03, 05, 07, 09..27                |
| §3.7 workers (`:573`)         |        1 | M-WORKERS-02                                       |
| §3.9 snapshots (`:600`)       |        3 | M-SNAPSHOTS-19, 20, 21                             |
| §3.14 tutorial (`:701`)       |        1 | M-TUTORIAL-04                                      |

Four carry a stale non-terminal `pending …` and need a *terminal* verdict, not a first one: `C2.4-02`,
`C2.4-05`, `M-WORKERS-02`, `M-TUTORIAL-04` — the filler's dry run names all four. **§3.7 and §3.14 are one
row from closing.**

### Classes that change how you drive

- **MANUAL (native menu)** — `M-SNAPSHOTS-19`, `M-TUTORIAL-04`. Attempt by hand while in the browser;
  `M-TUTORIAL-04` closes §3.14 outright.
- **M-SNAPSHOTS-20/-21 remain UNREACHABLE.** `DEAD-EXPECTED`, but the buttons render only inside
  dataset-swap cards and none exist. `record_dataset_swap_event` has one caller, inside `swap_dataset_live`
  (`juniper-cascor/src/api/lifecycle/manager.py:3081`, def `:2803`), reachable only from
  `POST /v1/training/dataset/swap`; canopy's cold restart is stop → await → start and never touches it.
  F-CANOPY-025 kills the *button*, but the server route
  (`juniper-canopy/src/main.py:3937 /api/live_dataset_swap`) still exists — that API induction is the only
  candidate. **Do not burn a destructive restart on them.** If no swap card exists, record `BLOCKED` with
  the reason — not `N-A`, not blank. *(Segment 15 did not attempt them.)*
- **DEMO-lane only (2)** — `C2.4-02` and `M-DATASET-03`. `isolated_stack.bash:379` hard-codes
  `JUNIPER_CANOPY_DEMO_MODE=0` inside its `nohup env` list, so it **cannot** produce this lane; launch
  canopy by hand from `juniper-canopy/src` with the same env block minus that line. Segment 15 re-confirmed
  `extra_env` only ever carries the recurrence URL, so no override reaches it.
- **LIVE-lane, upstream degraded (2)** — `C2.4-05` and `M-WORKERS-02` share one induction; drive them
  together. Still never induced (segment 4 produced `WS: Upstream reconnecting`, a different
  `streamHealth.overall` value).
- **Mixed mode (1)** — `M-DATASET-11` (`D (success) / L (400 arm)`); easy to miss.

## §3.6 — the block that decides the segment

24 rows, and the route runs through **`util/ad-hoc/e2e_w6_dataset_driver.py`** (note `--steps`, plural,
**comma-only — no ranges**, despite its docstring). The driver **deliberately stops short of matrix step 16**
(`#restart-confirm-button`) — its header calls that "an owner call, not a driver's", and its step registry
has no `16`. Staging is automated; **the confirm is yours**.

The W6 cold restart wipes in-memory training state. That no longer costs you anything §3.1 depends on —
§3.1 is closed — so §3.6 can go first this segment. Segment 15 already exercised the staging half from the
sidebar (`C2.7-09`): Apply Dataset opens `pending-dataset-banner` and the config lands in
`GET /api/status.pending_dataset`. Two useful facts from that work:

- **Staged payload shape differs by generator**: spirals stages **flat**
  (`{dataset_type, n_samples, noise, rotations, n_spirals}`), circles nests under `params{}`. Don't assert
  one shape for both.
- `M-DATASET-15`/`-16` are **MANUAL**; `M-DATASET-03` is DEMO-only; `W6-21` (staging-failure arm) needs the
  shared juniper-data leg stopped — MANUAL, never attempted.

## Standing up the stack

**The isolated trio is DOWN** as of this handoff.

> ### The snapshot root MOVED — the old backup ceremony is obsolete AND harmful
>
> **Corrected 2026-08-21**, after concurrent sessions landed the S-1 storage-convention ruling
> (`notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-STORAGE-CONVENTION-DESIGN.md`, ml#1211/#1197).
> Segment 15's original text told you to back up `juniper-cascor/src/snapshots/snapshot_*.h5` before every
> `--up`. **Do not do that.** All three premises are now false:
>
> 1. **The root is `<Juniper>/juniper-cascor/cascor-snapshots/`** — the ONE root shared by the direct CLI,
>    the service and the container (`isolated_stack.bash:122`, `CASCOR_SNAPSHOT_ROOT`). `src/snapshots/` is
>    now the importable serializer **PACKAGE** and receives no artifacts; the old glob matches **nothing**.
> 2. **`--down` no longer touches the cascor corpus.** Teardown removes only canopy-local `.h5`; the script
>    carries an explicit `-- DO NOT ADD A SWEEP OF ${CASCOR_SNAPSHOT_ROOT} HERE --` guard at `:476`
>    explaining that the root is a protected project **asset store** that outlives every stack. **Backing it
>    up is unnecessary.**
> 3. **Copying it would be actively bad.** The root holds **27,896 `.h5` files / 1.8 GB** (measured
>    2026-08-21). A `cp .../*.h5` against it dies with *Argument list too long* — `ls *.h5 | wc -l` silently
>    reports **0** for the same reason, so do not read a zero as "empty"; count with
>    `find <root> -maxdepth 1 -name '*.h5' | wc -l`.
>
> The script's own comment names the trap: *"the obvious 'fix' of repointing this glob at the new root is
> precisely the mistake this comment exists to prevent."* If a run ever needs disposable snapshots, give it
> its **own** root via `JUNIPER_CASCOR_SNAPSHOTS_DIR` (as `experiment_stack.bash` does) and sweep that.
>
> Segment 15's four `.h5` files were **not** migrated into the new root (different name pattern); they
> survive at `backups/e2e-snapshots-seg15/`. You almost certainly do not need them — the shared root already
> gives the snapshots panel a corpus — but that is where they are.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_E2E_RECURRENCE_PORT=8212 util/isolated_stack.bash --up     # data 8101 · cascor 8202 · canopy 8051
# teardown uses the SAME overrides. No corpus backup, no restore.
```

Two ways the script still hurts you: `--down` stops the recurrence port **unconditionally** and defaults to
**8211, the port the live juniper-deploy container holds** (`isolated_stack.bash:83`, stop at `:467`) —
`--up` is pre-checked, teardown is not, so **always pass `JUNIPER_E2E_RECURRENCE_PORT=8212`**; and
`PROJECT_DIR` derives from the script's own location (`:62`), so running from a worktree resolves siblings
to non-existent paths unless `JUNIPER_E2E_PROJECT_DIR` is set. Segment 15's teardown was verified clean: it
stopped exactly the three recorded leg pids and reported "nothing listening" on 8212.

**The general lesson from segment 15 still stands, even though its specifics expired: verify the corpus and
the script yourself; do not trust a path or a count quoted in a handoff.** Segment 15 arrived to find zero
`.h5` where its own handoff claimed four — and then wrote the paragraph this box had to correct.

Gate every live check on canopy `/v1/health` reporting `demo_mode:false` **and**
`juniper_data_available:true` — HTTP 200 alone is not the gate. Record the leg pids at bring-up; a count on
this shared box is not a measurement.

`C2.5-07` needs `export JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` **before** `--up` (the launcher uses
`nohup env` without `-i`, so ambient exports propagate). Drive nothing else in that posture.

### Know which code you are testing

Segment 15 ran against canopy `955e8d4` / cascor `4bec1be`, both clean on `main`. Re-check — the sibling
checkouts can lag:

```bash
cd /home/pcalnon/Development/python/Juniper
git -C juniper-canopy log --oneline -1        # ff-pull if behind
git -C juniper-cascor log --oneline -1
```

**`cd` back into your working checkout before any `--write`** — both counting tools resolve the matrix
relative to cwd.

## What segment 15 changed that you must know

- **The `dbc.Checkbox` gesture is SOLVED.** Segment 13's blocker is gone:

  ```js
  box._valueTracker.setValue(String(!target));   // tracker must hold the OPPOSITE of the target
  Object.getOwnPropertyDescriptor(Object.getPrototypeOf(box), 'checked').set.call(box, target);
  box.dispatchEvent(new Event('click', {bubbles: true}));   // React drives checkbox onChange off CLICK
  ```

  Segment 13 dispatched `change` and never desynced the tracker. Setting the tracker *to* the target
  reproduces the old symptom exactly — get the direction right. `dcc.RadioItems` responds to a plain raw
  `.click()`; the widget family is still not uniform, so prove each gesture landed.
- **Three new findings** — **F-CANOPY-026** (phase duration inflated by exactly the host UTC offset; cascor
  emits naive local, canopy stamps UTC; invisible in UTC-0 containers), **F-CANOPY-027** (store-fill →
  render chains dead in the Candidate Metrics and Decision Boundary panels; **root cause NOT isolated**),
  **F-CANOPY-028** (pinned params silently discarded on the first pin after any reload). All three are in
  the evidence note's ledger.
- **F-CANOPY-027 re-opens five already-`PASS` rows.** `M-CANDIDATES-01/-02/-03/-04/-06` were scored against
  the panel's mount defaults — `-02`/`-03`'s expectations literally name `"Idle"` and `"0"`. Same
  negative-arm trap that hid F-CANOPY-025 for five segments. Cells left as-is; re-drive them if the chain
  gets fixed. **M-METRICS-13 is the cheapest discriminator** for whether the replay group shares the cause:
  its "icon becomes ⏸" claim is data-independent and it also failed.
- **The segment-7 "1-in-15" question is settled.** `FULL_HISTORY_POLL_TICK_MODULUS` is 5 and correct;
  `fast-update-interval` measured a **2.51 s** period against a declared 1000 ms under F-CANOPY-004
  congestion, and 5 × 2.51 ≈ 12.6 s explains the observed gaps. **Never score a row "starved" without
  measuring the real tick first.**

## Recording verdicts

New bring-up ⇒ new run id `<UTC yyyymmddThhmmssZ>`. Create
`reports/e2e/<NEW_RUN_ID>/statuses.tsv` with header `row_id<TAB>status<TAB>notes<TAB>screenshots`, and update
`reports/e2e/CURRENT_RUN_ID` (currently `20260820T080544Z`) — a human pointer only; no tool reads it.

**Screenshots are local evidence only — do NOT commit them.** `*.png` is LFS-tracked but
`util/open_signed_pr.py` base64s raw bytes through the API and bypasses the LFS clean filter. Reference
filenames in the TSV column instead. *(Segment 15 committed none.)*

```bash
python3 util/ad-hoc/e2e_append_statuses.py reports/e2e/<NEW_RUN_ID>/statuses.tsv /path/to/rows.json
ls reports/e2e/                                  # confirm your --verdicts list names EVERY run dir
python3 util/ad-hoc/e2e_matrix_fill.py \
  --verdicts reports/e2e/<NEW_RUN_ID>/statuses.tsv \
  --verdicts reports/e2e/20260820T080544Z/statuses.tsv \
  --verdicts reports/e2e/20260817T101500Z/statuses.tsv \
  --verdicts reports/e2e/20260817T093715Z/statuses.tsv \
  --verdicts reports/e2e/20260816T124231Z/statuses.tsv \
  --verdicts reports/e2e/20260811T010700Z/statuses.tsv \
  --verdicts reports/e2e/20260810T002233Z/statuses.tsv \
  --verdicts reports/e2e/20260809T223851Z/rowlog.md      # dry run; add --write after reviewing
```

Four rules for the status column (the filler mechanically enforces only the first and last):

- **`pending …` is not a verdict.** Only plan §9 vocabulary reaches a status cell: `PASS` / `FAIL` /
  `BLOCKED` / `N-A` / `DEAD-CONFIRMED`, optionally with a rider that *narrows* it (`PASS (LIVE arm)`,
  `PASS(resolution)/FAIL(re-render)`).
- **A lane arm proves one lane** — render it as such, never a bare `PASS`.
- **A compressed token addresses real rows** — `..` ranges, `,`/`/` enumerations, `-L`/`-D` suffixes.
- **Never change a row's cell count.** Verify after every fill:
  `git diff -U0 <matrix> | grep -E '^[-+]\|'`, equal in/out counts, zero cell-count mismatches.
  *(Segment 15: 54 in / 54 out / 0 mismatches.)*

## Traps that have already cost this arc time

### Instrument traps — segment 15 hit four of these in its own probes

- **Never `includes()` against a sliced response.** The largest real Dash response measured this arc is
  **675,891 chars**; a 3000-char slice reported zero hits for outputs that were present.
- **Never let a capture buffer evict.** A 250-entry ring silently dropped entries and under-reported fills
  4× — the same shape as the documented `performance.getEntriesByType('resource')` 250 cap.
- **Scope substring filters to the full component id.** `'status-badge'` matched another panel's badge and
  reported 15 phantom outputs; the precise id returned 0.
- **Real keystrokes do not land on this page.** `elementHandle.type()` timed out at 5 s *and* left the value
  untouched with no wire traffic. Clicks land despite the ack timing out; typing does not. The native-setter
  idiom is the only working numeric path.
- **Probe after the panel settles.** Controls report `ABSENT` immediately after a tab switch and appear
  seconds later.

### Driving

- **Verify a click by its EFFECT, not the tool's return.** Playwright's post-click ack times out while the
  click lands. `page.hover()` fails the same way — dispatch `pointerover`/`mouseover`/`mouseenter`.
- **A raw JS `.click()` drives `<button>`, `[role=tab]`, `[role=option]` and `dcc.RadioItems`** but is
  **INERT on `dbc.Switch`**; `dbc.Checkbox` needs the tracker idiom above.
- **Re-query an element id immediately before clicking, and retry** — panels that rebuild on an interval
  detach nodes between query and click.
- **Radix selects**: `<button aria-haspopup="listbox">` with options portalled to `body` as `[role=option]`.
  Scope by the trigger's `aria-controls`; **match labels exactly** — the activation list contains both
  `Sigmoid` and `sigmoid`.

### Reading

- **Settle times are long.** Measured this arc: 3.0–3.5 s, and **11.0 s / 13.1 s / 17.2 s** for sidebar and
  layout-CRUD round trips. Poll for the expected transition; never sample once.
- **Closed means ABSENT** for modals and the pending-dataset banner. Floating alerts are the opposite.
- **Panels are hidden, not unmounted** — assert *visibility* (`getComputedStyle` + `getBoundingClientRect`),
  never presence. `dcc.Store`/`dcc.Interval` render **no DOM at all**, so a zero node count for a store
  proves nothing — the working stores also return 0.
- **Poll for a CHANGE when the target already holds text.** `params-status` sits at `⚠️ Unsaved changes` and
  a presence-poll returns instantly with the wrong answer.
- **`/api/set_params`, `/api/stage_dataset`, `/api/cancel_pending_dataset` and the snapshot routes are
  POSTed/GETed SERVER-side** — zero browser requests is expected. Prove them on the canopy log or the API.
- **Clientside callbacks emit no `_dash-update-component` traffic** — 0 wire hits for the interval-disable
  Outputs (`:3213-3226`) is expected, not a miss.

### Judgement

- **A first-pass anomaly is more often the instrument or a documented race than a new defect.** Segment 15
  avoided filing **three** wrong findings by re-checking: a "missing store" (stores render no DOM), a "broken
  NN→CN checkbox mirror" (`_sync_multi_node_checkboxes_handler`, `dashboard_manager.py:6841-6852`, is
  deliberately one-directional CN→NN), and an "inconsistent pinned card" (merely lagging). **Reproduce a
  second way, and read the handler, before writing it down.**
- **A negative-arm pass is not evidence a gate works.** This has now bitten the arc twice (F-CANOPY-025;
  F-CANOPY-027's five §3.2 rows).
- **A count on a shared box is not a measurement** — attribute to the leg pid recorded at bring-up.
- **Check the findings ledger AND grep the TSVs before filing.**

## Open findings that bound this segment

Ledger: evidence note §"Findings ledger (Phase 1)" (`:96`) — **but several findings live in per-segment
sections instead** (F-CANOPY-009 `:403`, F-CANOPY-010 `:471`, F-CASCOR-003b `:1847`). Grep the whole file.

| finding                  | bearing on segment 16                                                                                            |
|--------------------------|------------------------------------------------------------------------------------------------------------------|
| **F-CANOPY-002** (P0)    | WS metrics fast path dead — score against the REST oracle                                                        |
| **F-CANOPY-003** (P1)    | control buttons never re-enable after a successful ack; a raced command can wedge start/pause/resume             |
| **F-CANOPY-004** (P0/P1) | server callbacks lag 30 s–minutes; budget settle windows accordingly                                             |
| **F-CANOPY-005** (P0)    | REST fallback **double-fires** state-changing commands — an apparently-failed command may already have succeeded |
| **F-CANOPY-006** (P0)    | topology counts never update; segment 15 saw `/api/status` report 0 against cascor's 7 — belongs here            |
| **F-CANOPY-025** (P1)    | Live Dataset Switch gate never emits → W7 unreachable from the UI; W6 cold restart is the only swap route        |
| **F-CANOPY-027** (P0/P1) | **NEW** — Candidate Metrics + Decision Boundary render chains dead; taints five §3.2 `PASS` rows                 |
| **F-ML-001** (P1)        | never run `util/reap_pytest_orphans.bash` while the stack is up — it kills the nohup cascor leg                  |
| **F-CASCOR-003b**        | unsettled; original observation used the discredited box-wide counting method — re-take per-leg                  |

Fixed this arc, **do not re-file**: F-CANOPY-017 (canopy#489), -022 (#492), -023 (#494), -024 (#493).

Still open from earlier segments: **W7** is blocked by F-CANOPY-025, not by its own preconditions; **W8** is
`N-A` while the recurrence leg is down (`:904-906`); **W6-21** needs the shared juniper-data leg stopped;
**W5-30 + the DEMO lane** need the hand-launched DEMO posture (each demo arm must 501 and render
`❌ Operation not supported in this mode`).

## Landing the segment

One PR. Deliverables (segment 15 = **ml#1203** for shape):

- **(a)** a `## Phase 1 — segment 16 (YYYY-MM-DD): <title>` section appended to the evidence note;
- **(b)** `reports/e2e/<RUN_ID>/statuses.tsv`;
- **(c)** `reports/e2e/CURRENT_RUN_ID`;
- **(d)** matrix cells **and** the `As of segment N: **X of 298**` counter (`:77`);
- **(e)** any new `util/ad-hoc/` driver.

1. Branch from a freshly fetched `origin/main`.
2. **Check `gh pr list` immediately before you push**, and re-verify your worktree diff against the pushed
   branch right after opening the PR.
3. Commit signed with `util/open_signed_pr.py` (`--repo` / `--branch` / `--add local:repopath` / `--message`
   / `--title` / `--body-file`); `main` enforces `required_signatures`. It uploads **whole files**, so two
   PRs touching the same file must be merged sequentially with the second rebased. `--body-file` bypasses the
   PR template, so include the `## Requirements` section yourself — ml#1203 used *"No tracked JR-ID applies —
   evidence capture for the canopy E2E validation arc."*
4. Merge with the REST squash endpoint —
   `gh api -X PUT repos/pcalnon/juniper-ml/pulls/<N>/merge -f merge_method=squash` — which succeeds where
   `gh pr merge` stalls. Headless merge is pre-authorized for this arc by the plan (`:689-690`).
5. **Wait for CI with `util/wait_for_checks.py --pr <N> --anchor required`** — never hand-roll a poll loop; a
   loop keyed on "zero pending" completes spuriously. A docs-only ml PR reports 23–24 contexts of which 17
   are SUCCESS; guard on `SUCCESS >= 17 AND pending == 0`, not `total >= 17`.
6. After merging:
   `gh run list --workflow=main-verify.yml -c "$(gh pr view <N> --json mergeCommit -q .mergeCommit.oid)" --json conclusion,url`
   (**`-c` matches only FULL 40-char SHAs**; a 7-char SHA returns `[]`, which reads like "no run yet").
   main-verify goes red periodically from an inherited docs-deletion finding carried by the G3.1 catch-up
   base — check the state yourself and confirm the failing paths are not yours. A **paired status-cell swap
   does not trip `juniper-docs-additions-check`** (segment 15's 54-row fill passed Sequence Safety clean); if
   your own diff does trip it, add an `Allow-Docs-Rewrite: <path>` trailer **and carry it into the squash
   message**.
7. Clean up your worktree and branch.

**Before you emit the segment-17 handoff, validate it independently** — this arc's handoffs inherit errors
across generations. Re-run **both** counting tools and diff your per-section table against
`e2e_unfilled_rows.py` before opening the PR. Segment 15's input handoff was itself a rewrite after three
validators returned FAIL on a draft whose work table came from the estimator.

## Git state at handoff

Segment 15 shipped as **ml#1203** (`24aee3d`) and this handoff as **ml#1204** (`847e84e`); both merged,
both main-verify green. This document was then **corrected in place on 2026-08-21** (see the snapshot-root
box above) once concurrent sessions landed the S-1 storage-convention ruling — at that point `origin/main`
was `d52c626`. **`origin/main` moves several times a day** — always branch from a freshly fetched
`origin/main`, never from any SHA quoted here, and **re-derive every line anchor in this document before
relying on it**: the 2026-08-21 pass alone had to move `isolated_stack.bash:369→:379` and `:457→:467`, and
`manager.py:3079→:3081` / `:2801→:2803`, purely from other sessions' edits.

Verified still correct on `d52c626`: matrix `:77` (the counter), `:223` / `:246` / `:519` / `:573` / `:600` /
`:701`; evidence note `:96`; plan `:689`; `isolated_stack.bash:62` / `:83` / `:122`;
`dashboard_manager.py:6841`; `juniper-canopy/src/main.py:3937`.

Matrix at **266 of 298**. Verdict records: `reports/e2e/20260809T223851Z/rowlog.md`,
`20260810T002233Z/`, `20260811T010700Z/`, `20260816T124231Z/`, `20260817T093715Z/`, `20260817T101500Z/`,
`20260820T080544Z/` (all `statuses.tsv` except the first).
