# HANDOFF 2026-08-18 — Canopy E2E Phase 1: segment 15, the 86 unfilled matrix rows

Continue Phase 1 live click-by-click validation of the juniper-canopy E2E arc. Successor to
[`HANDOFF_2026-08-15_canopy-e2e-phase1-segment-12.md`](HANDOFF_2026-08-15_canopy-e2e-phase1-segment-12.md);
segments 13 and 14 produced no handoff of their own — their record is the evidence note, §"Phase 1 —
segment 13" and §"Phase 1 — segment 14".

Segments 12–14 drove **72 rows** (140 → 212) and closed **one** whole section (§2.10); segment 14 also took
§3.9 to 18/21. Segment 15 continues into the two largest remaining blocks, both of which need a **live
training run** — a precondition none of the last three segments required, so §"Getting a live run" below is
mandatory reading.

**Read order ≠ page order.** The sections are arranged narratively; execute them in this order:
**(1)** Verify your starting state → **(2)** *Standing up the stack* (it carries the corpus backup, three
destructive traps, and the C2.5-07 / DEMO postures you must choose *before* `--up`) → **(3)** Getting a live
run → **(4)** Suggested order → **(5)** Recording verdicts → **(6)** Landing the segment. Read Traps once up
front; it is reference, not a step.

## Documents

| what | path |
|---|---|
| matrix (the ledger) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| evidence note (findings + per-segment record) | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` |
| plan (§9 verdict vocabulary, §4.5 recurrence leg, merge policy `:689-690`) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` |

## Verify your starting state first

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline -3 origin/main       # expect 604fefc or later
git status --porcelain                                     # expect clean or unrelated stragglers
gh pr list --repo pcalnon/juniper-ml     --state open --limit 10   # expect no arc/canopy-e2e-* PR
gh pr list --repo pcalnon/juniper-canopy --state open --limit 10   # expect no arc PR (dependabot PRs are normal)
python3 util/ad-hoc/e2e_row_coverage.py                    # 298 rows / 213 verdicted / 85 remaining
```

Count the ledger itself with the filler, never a naive `|` split (at least one row carries an escaped `\|`):

```bash
python3 util/ad-hoc/e2e_matrix_fill.py \
  --verdicts reports/e2e/20260817T101500Z/statuses.tsv \
  --verdicts reports/e2e/20260817T093715Z/statuses.tsv \
  --verdicts reports/e2e/20260816T124231Z/statuses.tsv \
  --verdicts reports/e2e/20260811T010700Z/statuses.tsv \
  --verdicts reports/e2e/20260810T002233Z/statuses.tsv \
  --verdicts reports/e2e/20260809T223851Z/rowlog.md
# expect: filled 0 · already filled 212 · no verdict yet 86   (dry run; writes nothing)
```

**The two tools disagree by one, and both numbers are right.** The mapper says 213/85, the ledger 212/86.
The delta is unchanged since segment 11 and is *explained*: the mapper reads only the leading token of the
`M-PARAMETERS-01/02/03` slash enumeration in `reports/e2e/20260809T223851Z/rowlog.md:82` (−2, so it thinks
`M-PARAMETERS-02`/`-03` are open when the ledger has them `PASS`), and it over-credits three rows whose only
record is a non-terminal `pending …` that the filler deliberately refuses to write (+3: `C2.4-02`,
`M-WORKERS-02`, `M-TUTORIAL-04`). **The matrix is the ledger; the mapper is an estimator.** Do not
"reconcile" them — and **plan your work from the table below, which is ledger-derived**, not from
`e2e_row_coverage.py`'s section listing. *(Segment 15's own handoff draft published the mapper's list under
the ledger's headline and was caught in validation; do not repeat it.)*

## What is done (do not redo)

| PR | Merge | Item |
|---|---|---|
| ml#1131 | `0966f94` | segment 12 — sidebar §2.6–§2.9 driven, matrix 140→168, **AUTO-API numeric wall retired** |
| canopy#492 | `0460240` | **F-CANOPY-022 FIXED** — `candidate_selection` ships cascor's `top` literal |
| canopy#493 | `71b569b` | **F-CANOPY-024 FIXED** — valid default triple, count floors match cascor `ge=0` |
| canopy#494 | `56ce45f` | **F-CANOPY-023 FIXED** — verify skips cascor-declined keys |
| ml#1132 | `5239dfd` | fix record + **F-CANOPY-023 root cause corrected** (it is canopy-only) |
| ml#1146 | `7bf5b3d` | segment 13 — **§2.10 CLOSED 17/17**, §2.9 tail, matrix 168→198, **new F-CANOPY-025** |
| ml#1153 | `6ddfa21` | segment 14 — **§3.9 Snapshots 4/21→18/21**, matrix 198→212 |

Closed lanes (10): §2.1 4/4, §2.2 6/6, §2.3 8/8, §2.10 17/17, §3.3 topology 18/18, §3.10 replay 17/17,
§3.11 network editor 18/18, §3.12 redis 4/4, §3.13 cassandra 4/4, §3.15 about 3/3.

## The remaining 86 rows — ledger-derived, sums to 86

Anchors are line numbers in the matrix. Re-grep the `###` header if one is off — the section *names* are the
durable key.

| section (line) | unfilled | row ids |
|---|---:|---|
| §2.4 WS badge (`:223`) | 2 | C2.4-02, C2.4-05 |
| §2.5 training controls (`:246`) | 1 | C2.5-07 |
| §2.6 NN meta-parameters (`:275`) | 4 | C2.6-05, 07, 10, 14 |
| §2.7 dataset subsection (`:301`) | 6 | C2.7-02, 03, 06, 07, 08, 09 |
| §2.8 candidate-node meta-parameters (`:316`) | 1 | C2.8-09 |
| §2.9 banner trio / Apply / Experimental (`:335`) | 3 | C2.9-06, 14, 15 |
| §3.1 metrics (`:405`) | 22 | M-METRICS-02..09, 11..20, 23, 25, 27, 28 |
| §3.2 candidates (`:444`) | 4 | M-CANDIDATES-07, 09, 10, 11 |
| §3.4 evolution (`:489`) | 2 | M-EVOLUTION-04, 07 |
| §3.5 boundaries (`:504`) | 8 | M-BOUNDARIES-01..08 |
| §3.6 dataset view (`:519`) | 24 | M-DATASET-01, 02, 03, 05, 07, 09..27 |
| §3.7 workers (`:573`) | 1 | M-WORKERS-02 |
| §3.8 parameters (`:586`) | 4 | M-PARAMETERS-04, 05, 06, 07 |
| §3.9 snapshots (`:600`) | 3 | M-SNAPSHOTS-19, 20, 21 |
| §3.14 tutorial (`:701`) | 1 | M-TUTORIAL-04 |

**Four of these carry a stale non-terminal `pending …` record** — `C2.4-02`, `C2.4-05`
(`rowlog.md:73`, `| C2.4-04/05 | pending W14 |`), `M-WORKERS-02` and `M-TUTORIAL-04`. They need a *terminal*
verdict, not a first one, and the filler's dry-run names all four. (Only the first, third and fourth are the
mapper's `+3` over-credit; `C2.4-05` is unfilled in both tools.) **§3.7 and §3.14 are one row from closing**:
the cheapest wins in the set.

### Classes that change how you drive, not whether

- **`DEAD-EXPECTED` (4)** — M-CANDIDATES-10, -11, M-SNAPSHOTS-20, -21. Their passing terminal value is
  **`DEAD-CONFIRMED`**, not `PASS` (matrix `:70` legend): the click verifiably did nothing — no request, no
  DOM change, no console error.
- **M-SNAPSHOTS-20/-21 are currently UNREACHABLE.** Those buttons render only inside dataset-swap cards, and
  the panel reports "No dataset swaps recorded yet." A `DEAD-CONFIRMED` verdict means clicking a control and
  proving nothing happened — a control that does not render cannot be scored. They need a real dataset-swap
  **event**, and **a W6 cold restart cannot make one**: `record_dataset_swap_event` has a single caller,
  inside `swap_dataset_live` (`juniper-cascor/src/api/lifecycle/manager.py:3079`, def `:2801`), reachable
  only from `POST /v1/training/dataset/swap`. Canopy's restart is stop → await → start and never touches
  that path. F-CANOPY-025 kills the *button*, but the server-side route
  (`juniper-canopy/src/main.py:3937 /api/live_dataset_swap`) is still there — that API induction is the only
  candidate. **Do not burn a destructive W6 restart on this.** If no swap card exists by end of segment,
  record `BLOCKED` with the reason — not `N-A`, not blank.
- **`MANUAL` (6)** — M-EVOLUTION-07, M-BOUNDARIES-07, M-DATASET-15, M-DATASET-16, M-SNAPSHOTS-19
  (`MANUAL (native menu)`), **M-TUTORIAL-04** (`MANUAL (native menu)`).
- **DEMO-lane only (2)** — **C2.4-02** (`WS: Demo` badge) and M-DATASET-03. See the DEMO posture warning
  below: `isolated_stack.bash` **cannot** produce this lane.
- **LIVE-lane only (4)** — C2.4-05 (upstream *degraded*), **M-WORKERS-02** (`worker-panel-error-display`,
  upstream degraded), M-METRICS-27, M-BOUNDARIES-07. **C2.4-05 and M-WORKERS-02 share the same induction**
  (upstream degraded) and should be driven in one pass. Neither has been induced: segment 4 produced
  `WS: Upstream reconnecting` by taking the cascor leg down, but *degraded* is a different
  `streamHealth.overall` value.
- **Mixed mode (1)** — **M-DATASET-11** (`D (success) / L (400 arm)`), easy to miss because it falls into
  none of the buckets above.

## Getting a live run — the precondition for ~60 of these rows

§3.1 (22), §3.6 (24), §3.5 (8), §3.2 (4) and §3.4 (2) all need a live/trained network.

**The scripted path already exists**: `util/ad-hoc/e2e_seg13_modals_driver.py --step live_switch` clicks
`#start-button` (`:634`) and then polls `/api/status` for `is_running` (`:637-642`) — i.e. it automates
matrix §W1 (`:731`) steps 5–6. It *also* goes on to open the live-switch modal (its original purpose), so
either reuse it and ignore the tail, or drive the same two steps by hand:

```bash
# stack already up and health-gated (below); then in the browser session:
#   1. dismiss the welcome modal: click #welcome-modal-close
#   2. click #start-button       -> {command:"start", command_id} on /ws/control
#   3. confirm it took:
curl -s http://127.0.0.1:8051/api/status | python3 -m json.tool | grep is_running   # expect true
#   4. accumulate history before scoring §3.1:
python3 util/ad-hoc/e2e_poll_status.py --until-units 2
```

Dataset rows (§3.6) stage through `util/ad-hoc/e2e_w6_dataset_driver.py` (note: `--steps`, plural — see the
tools table).

**Order matters.** §3.6 routes through a **W6 cold restart, which wipes the run history §3.1 depends on**.
Finish §3.1 / §3.2 / §3.4 / §3.5 on one run *before* restarting for the dataset work.

## Suggested order for segment 15

1. **§3.1 metrics (22).** **F-CANOPY-002 means the WS metrics fast path is dead in every live run** — score
   against the **REST oracle** (`/api/metrics`, `/api/metrics/history`), not the WS store. The metrics store
   is **throttled, not starved**: `FULL_HISTORY_POLL_TICK_MODULUS` reads **5**
   (`juniper-canopy/src/canopy_constants.py:368`), while segment 7 observed 1-in-15 and attributed it to that
   constant — **that attribution is still unresolved, so measure the real cadence before scoring any row as
   starved**.
2. **§3.2 candidates (4) + §3.4 evolution (2)** — small, live during the same run.
3. **§3.5 boundaries (8).** Needs a **trained** network (the boundary needs weights). Its slider
   (`decision_boundary.py:100`) declares **no** `updatemode`, so it is Dash-default `mouseup`.
4. **The 11 sidebar leftovers, while the run is still alive** — C2.6-05, 07, 10, 14; C2.7-02, 03, 06, 07, 08,
   09; C2.8-09; and **C2.9-06**, which is the apply-in-flight interval clamp and can *only* be scored during
   a live run (segment 13 lost it because the form never dirtied — dirty a tracked field first, then Apply).
   These get one table line and no other guidance, so schedule them deliberately.
5. **§3.7 workers (1) + §2.4-05 + §3.14 tutorial (1)** — drive `M-WORKERS-02` and `C2.4-05` together (one
   degraded induction); `M-TUTORIAL-04` is `MANUAL (native menu)` but closes §3.14 outright, so attempt it by
   hand while you are in the browser. **Do this LAST among the live-run items** — see the W14 hard rule below;
   the induction ends the run.

   > **W14 HARD RULE, and the handoff before this one omitted it (matrix `:1017-1020`): do NOT restart canopy
   > during the degraded induction.** Restarting canopy while cascor is down triggers the **T-2 silent demo
   > fallback** — canopy re-creates a demo backend (`juniper-canopy/src/main.py:322-337`) and `/v1/health`
   > still reads `status: "ok"`; only `demo_mode: true` betrays it. Every verdict scored after that is
   > against the demo backend. W14 also records that in-memory training state is expected lost (`:1029`), so
   > this induction **destroys the run** — finish items 1–4 first.
6. **§3.8 parameters (4)** — do these BEFORE the dataset block; they need only a loaded dataset, not a fresh run.
   M-PARAMETERS-04..06 are the pin checkboxes feeding `pinned-params-store`;
   M-PARAMETERS-07 is a different mechanism (table refresh after Apply).
   **Warning, measured in segment 13:** the pin checkboxes could not be driven by any available technique —
   neither the native-setter idiom nor a trusted `page.check()` reached their Dash `value` prop. The wire
   showed the chain is *correct* (`pinned-params-store` received `data: []`, `sidebar-pinned-card` correctly
   got `display:none`). **C2.9-14/-15 are blocked on the same gesture.** Solve it and you unlock five rows;
   if you cannot, record NOT DRIVEN rather than filing a defect.
7. **§3.6 dataset view (24)** — last of the main blocks, because the W6 route restarts training. **Note the
   driver stops short:** `e2e_w6_dataset_driver.py` deliberately refuses matrix step 16
   (`#restart-confirm-button`) — its own header calls that "an owner call, not a driver's" — and its step
   registry has no `16`. Staging is automated; the confirm is yours.
8. **Leftovers needing their own posture, if time remains** — `C2.5-07` (relaunch with
   `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false`, drive nothing else), the DEMO lane (`C2.4-02`,
   `M-DATASET-03`, `W5-30` — hand-launched canopy), `M-SNAPSHOTS-19` (MANUAL native menu), and
   `M-SNAPSHOTS-20/-21` (see the unreachable note above — do not spend a restart on them).

**Coverage check:** items 1–8 account for all 86 rows. If your plan does not, you have dropped something.

## Standing up the stack — read this before running anything

The isolated trio is **DOWN** as of this handoff. The juniper-deploy containers on **8050, 8201, 8211** (and
a listener on **8200**) are up and are **not** this arc's stack — run `ss -tlnp` and treat anything already
bound as not-ours.

```bash
# 1. BACK UP THE SNAPSHOT CORPUS FIRST — a failed --up calls do_down internally, which deletes it.
#    Flat copy, not `cp -a <dir>`: this segment needs 2-3 bring-up cycles (C2.5-07 posture, DEMO lane),
#    each teardown wipes the corpus, and re-running `cp -a` would nest it and break the restore glob.
mkdir -p /home/pcalnon/Development/python/Juniper/backups/e2e-snapshots-seg15
cp /home/pcalnon/Development/python/Juniper/juniper-cascor/src/snapshots/snapshot_*.h5 \
   /home/pcalnon/Development/python/Juniper/backups/e2e-snapshots-seg15/

# 2. bring up
cd /home/pcalnon/Development/python/Juniper/juniper-ml
JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_E2E_RECURRENCE_PORT=8212 util/isolated_stack.bash --up   # data 8101 · cascor 8202 · canopy 8051

# 3. tear down (SAME overrides — this is the destructive call)
JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_E2E_RECURRENCE_PORT=8212 util/isolated_stack.bash --down
# 4. then restore the corpus
cp /home/pcalnon/Development/python/Juniper/backups/e2e-snapshots-seg15/snapshot_*.h5 \
   /home/pcalnon/Development/python/Juniper/juniper-cascor/src/snapshots/
```

Three ways this script will hurt you:

1. **`--down` stops the recurrence port unconditionally**, and `JUNIPER_E2E_RECURRENCE_PORT` **defaults to
   8211 — the port the live juniper-deploy container holds** (`isolated_stack.bash:83`, stop at `:457`).
   `--up` is protected by a pre-check; teardown is not. Today it is a no-op against that container (`ss`
   hides the root-owned docker-proxy pid from a non-root caller) — **latent, not harmless**.
2. **`--down` deletes the snapshot corpus** (`:470-471`). **4 `.h5` files** currently live in
   `juniper-cascor/src/snapshots/` (verify yourself).
3. **`PROJECT_DIR` derives from the script's own location** (`:62`). Run it from a worktree and it resolves
   siblings to `worktrees/juniper-{data,cascor,canopy}` — paths that do not exist.

Gate every live check on canopy's `/v1/health` reporting `demo_mode:false` **and**
`juniper_data_available:true` — HTTP 200 alone is not the gate.

### The DEMO lane cannot be produced by this launcher

`util/isolated_stack.bash:369` hard-codes `JUNIPER_CANOPY_DEMO_MODE=0` inside the `nohup env` list, so it
overrides any ambient value. To drive `C2.4-02` / `M-DATASET-03` / `W5-30`, launch canopy by hand from
`juniper-canopy/src` with the same env block minus that line. **Do not waste time on env overrides.**

### C2.5-07's non-default transport posture

`export JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` **before** `--up` — the launcher uses `nohup env`
without `-i` (`:368`), so ambient exports propagate (unlike `DEMO_MODE`, which is explicitly overridden).
Default is `True` (`juniper-canopy/src/settings.py:349`). Drive **nothing else** in that posture, then tear
down and relaunch clean.

### Know which code you are testing

**The sibling checkout can lag `origin/main`.** Segment 12 ran against canopy `f90420e` (evidence note
`:1744`) — the tree *before* the three fixes it went on to produce — and segment 13 found the checkout still
there and had to ff-pull before driving; scoring §2.9 on the pre-fix tree would have been meaningless.
**These paths are ecosystem-root-relative:**

```bash
cd /home/pcalnon/Development/python/Juniper
git -C juniper-canopy log --oneline -1        # expect 56ce45f or later; ff-pull if behind
grep -c '"value": "top"'                    juniper-canopy/src/frontend/dashboard_manager.py        # 1
grep -c '_DERIVED_READONLY_CASCOR_PARAMS'   juniper-canopy/src/backend/cascor_service_adapter.py   # 3
grep -c 'DEFAULT_RANDOM_CANDIDATES_COUNT: Final\[int\] = 0' juniper-canopy/src/canopy_constants.py # 1
```

## Recording verdicts

A fresh bring-up means a **new run id**, formatted `<UTC yyyymmddThhmmssZ>`. Create
`reports/e2e/<NEW_RUN_ID>/statuses.tsv` with header `row_id<TAB>status<TAB>notes<TAB>screenshots`, and update
`reports/e2e/CURRENT_RUN_ID` (currently `20260817T101500Z`) — *purely a human pointer; no tool reads it*.

**Screenshots are local evidence only — do NOT commit them.** `*.png` is LFS-tracked
(`.gitattributes`), but `util/open_signed_pr.py` base64s raw bytes through the API and bypasses the LFS clean
filter, so a committed screenshot silently violates the LFS contract. Only run `20260810T002233Z` ever
committed images; do not resume the practice. Reference filenames in the TSV `screenshots` column instead.

Append with the dup-guarded helper. `rows.json` is a JSON **array** of objects with `row_id`, `status`,
`notes`, optional `screenshots` (defaults to an em dash); duplicate `row_id` is skipped unless `--replace`.
Keep it out of the repo (a scratch path is fine — it is not committed):

```json
[
 {"row_id":"M-METRICS-02","status":"PASS","notes":"…evidence…","screenshots":"—"},
 {"row_id":"M-CANDIDATES-10","status":"DEAD-CONFIRMED","notes":"no request, no DOM change, no console error","screenshots":"—"}
]
```

```bash
python3 util/ad-hoc/e2e_append_statuses.py reports/e2e/<NEW_RUN_ID>/statuses.tsv /path/to/rows.json
```

Then fill the matrix, **newest run first** (first source carrying a row wins; `--overwrite` is not used).
**Run `ls reports/e2e/` first** and confirm your `--verdicts` list names every run dir — a peer session may
have added one.

> **Mind your cwd and your checkout.** Both counting tools resolve the matrix relative to the current
> directory (`e2e_row_coverage.py --repo-root` defaults to `.`; `e2e_matrix_fill.py` defaults to
> `Path.cwd()`). Several blocks above deliberately `cd` to the ecosystem root
> (`/home/pcalnon/Development/python/Juniper`) for the sibling greps — **`cd` back into your working
> checkout before any `--write`**, or you will fill the matrix in whichever tree you happen to be standing
> in rather than the branch you are about to PR.

```bash
python3 util/ad-hoc/e2e_matrix_fill.py \
  --verdicts reports/e2e/<NEW_RUN_ID>/statuses.tsv \
  --verdicts reports/e2e/20260817T101500Z/statuses.tsv \
  --verdicts reports/e2e/20260817T093715Z/statuses.tsv \
  --verdicts reports/e2e/20260816T124231Z/statuses.tsv \
  --verdicts reports/e2e/20260811T010700Z/statuses.tsv \
  --verdicts reports/e2e/20260810T002233Z/statuses.tsv \
  --verdicts reports/e2e/20260809T223851Z/rowlog.md          # dry run
# ... review the "filled rows" list, then re-run with --write
```

Four rules for the status column. The filler *mechanically enforces* only the first and the last (it refuses
a `pending …` prefix, and it refuses to write a line whose cell count changes); rules 2 and 3 describe what
it parses and what the arc treats as honest. Respect all four in any hand edit — the matrix already carries
a few non-§9 strings (`INCONCLUSIVE`, `DIVERGENCE D-1 CONFIRMED …`) from earlier segments, so the vocabulary
is a convention the tool will not police for you:

- **`pending …` is not a verdict.** Only the plan §9 vocabulary reaches a status cell: `PASS` / `FAIL` /
  `BLOCKED` / `N-A` / `DEAD-CONFIRMED`, optionally with a rider that *narrows* the verdict
  (`PASS (LIVE arm)`, `PASS (empty branch)`, `FAIL(during-run)/PASS(post-run)`).
- **A lane arm proves one lane** — render it as such, never a bare `PASS`.
- **A compressed token addresses real rows** — `..` ranges, `,` and `/` enumerations, `-L`/`-D` lane suffixes.
- **Never change a row's cell count.** A hand edit that adds or drops a `|` silently moves every later cell —
  that is how segment 10 wrote a `PASS` into C2.2-04's **FA** column. Verify after every fill with
  `git diff -U0 <matrix> | grep -E '^[-+]\|'`, confirming equal in/out counts and zero cell-count mismatches.

## Tools you already have

| tool | use |
|---|---|
| `util/isolated_stack.bash` | `--up` / `--down` / `--status` / `--dry-run` — **always with both env overrides** |
| `util/ad-hoc/e2e_matrix_fill.py` | fill the status column from run records (dry-run default) |
| `util/ad-hoc/e2e_row_coverage.py` | coverage **estimator** — do not plan the work from its section list |
| `util/ad-hoc/e2e_append_statuses.py` | dup-guarded TSV verdict append (`--replace` to rewrite) |
| `util/ad-hoc/e2e_poll_status.py` | `--until-units N` / `--until-fsm STOPPED` / `--until-pending-clear` |
| `util/ad-hoc/e2e_w3_params_driver.py` | shared browser/log helpers — **`--steps`** (comma/range, e.g. `1-9`) |
| `util/ad-hoc/e2e_w6_dataset_driver.py` | dataset staging driver — **`--steps`** (plural, **comma-only — no ranges**, despite its docstring); **stops before the W6 restart confirm by design** |
| `util/ad-hoc/e2e_seg13_modals_driver.py` | §2.10 + §2.9 tail, **and `--step live_switch` starts a training run** — **`--step`** (single name); `probe`, `_click`, `_set_number`, `_set_checkbox`, `_wait_present` |
| `util/ad-hoc/e2e_seg14_snapshots_driver.py` | §3.9 — **`--step`**; re-query-before-click + retry, `full_text`, wire capture |
| `util/ad-hoc/e2e_cascor_leg_supervise.bash` | run the cascor leg under a resident supervisor (F-ML-001) |
| `util/ad-hoc/e2e_snapshot_h5_compare.py` | compare snapshot `.h5` artifacts |

**Try the browser MCP first** (`mcp__playwright__*`). It was available in segments 9 and 12, **absent in 8, 13
and 14**. When absent, drive the scripts under `/opt/miniforge3/envs/JuniperCanopy1/bin/python` — the only
environment with playwright — and **clear `LD_LIBRARY_PATH`**:

```bash
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/<driver>.py --step <name>
```

Invoking that python directly bypasses the conda hooks that strip `LD_LIBRARY_PATH`, and an ambient
`rust_mudgeon` libtorch then breaks **module import** with `undefined symbol: _PyObject_NextNotImplemented`
— which reads exactly like a test failure and is not one.

**Never run `util/reap_pytest_orphans.bash` while the stack is up** (F-ML-001): it kills the nohup-launched
cascor leg. The GPU box is shared — prove a process descends from *your* leg before killing or **counting**.

## Traps that have already cost this arc time

### Driving

- **Verify a click by its EFFECT, not the tool's return.** Playwright's post-click ack times out on this page
  while the click lands. `page.hover()` fails the same way (30 s) — dispatch `pointerover` / `mouseover` /
  `mouseenter` instead.
- **A raw JS `.click()` drives `<button>` correctly** but is **INERT on `dbc.Switch`** — on
  `experimental-functions-toggle` it left `.checked` *and* the backend untouched, while the
  native-`checked`-descriptor + `change` idiom flipped the backend. **`dbc.Checkbox` (the param-pin controls)
  resisted BOTH.** The family is not uniform; pick the gesture per widget class and prove it landed.
- **Numeric inputs take the native-setter idiom** (`value` property descriptor + `input` / `change`),
  cross-validated against real keystrokes and round-tripped to the backend. The `AUTO-API` numeric wall is
  **retired** (canopy#489).
- **Re-query an element id immediately before clicking, and retry.** Panels that rebuild on an interval
  (snapshots table: 10 s) detach nodes between query and click; that presents as "the control never
  responded". Segment 14's `M-SNAPSHOTS-16` needed 3 attempts, `-17` needed 2.

### Reading

- **Settle times are far longer than 1.5–2 s.** Measured: 3.5 s (`C2.8-01`), 3.0 s (`C2.9-12`), **>8 s** for
  the multi-candidate sub-group. Poll for the expected transition; never sample once.
- **Closed means ABSENT** for modals and the pending-dataset banner — `getElementById` returning null is the
  normal shipped state, so poll for *appearance*. Floating alerts are the opposite: always present at
  height 0, which is why their `top` offsets are readable at rest.
- **Panels are hidden, not unmounted** — read counters only with the panel's own tab active, and assert
  *visibility* (`getComputedStyle` + `getBoundingClientRect`), never presence. `offsetParent` is `null` for
  `position:fixed` and is not a visibility test.
- **Prove a refill with a value that MOVES.** Sampling an idle panel twice proves nothing.
- **A component id in a `_dash-update-component` REQUEST proves nothing** — every fire of a many-Input
  callback names them all. Only the carried **value**, in the **response**, is evidence.
- **`/api/set_params`, `/api/stage_dataset`, `/api/cancel_pending_dataset` and the snapshot list/op routes are
  POSTed/GETed SERVER-side**: **zero browser requests is expected**, never a failure. Prove them on the canopy
  server log (read by byte offset — it grows past 100 MB). Segment 14 measured the snapshot refresh as a
  **rate against an idle baseline** for exactly this reason.
- **A helper's convenience truncation can manufacture a finding** — segment 14's `probe()` sliced
  `textContent` to 120 chars and made `M-SNAPSHOTS-13`'s ⚠️ line look missing.
- **`performance.getEntriesByType('resource')` caps at 250 entries**; a full buffer reads exactly like zero
  traffic. Call `clearResourceTimings()` + `setResourceTimingBufferSize()` first.
- **`scrollIntoView` does not apply before a `getBoundingClientRect` in the same `page.evaluate`.**
- **Read id lists from source, never a DOM prefix** (`[id^="sidebar-"]` returned 20; `SIDEBAR_SECTION_IDS` is
  exactly 14).
- **Dropdowns are Dash 3.x Radix selects** — `<button aria-haspopup="listbox">` with options portalled to
  `body` as `[role=option]`. Scope by the trigger's `aria-controls`; match labels exactly ("Network
  Evolution", not "Evolution"; "Adam" also matches AdamW/NAdam/RAdam/Adamax).
- **Slider commit rules differ by `updatemode`.** In-metrics replay slider (`metrics_panel.py:369`) is
  **`drag`** (commits continuously). Replay-tab (`replay_player_panel.py:245,266,291`) and network-visualizer
  (`network_visualizer.py:187`) are **`mouseup`** — a moved handle is not evidence a value committed;
  `page.keyboard.press('ArrowRight')` on the focused thumb is what dispatches. The boundaries slider
  (`decision_boundary.py:100`) declares **none**, so it is Dash-default `mouseup`. Check before you score.
- **Dismiss `#welcome-modal` after any reload** — and note `#welcome-modal` *is* the `.modal-dialog`.

### Judgement

- **A first-pass anomaly on this dashboard is more often the instrument or a documented race than a new
  defect.** Four plausible findings have dissolved on re-check: the "stuck" multi-candidate sub-group
  (under-settled), a C2.8-12 "or" violation (mid-transition read), F-CANOPY-023's root cause (a `curl` whose
  `skipped` partition was never read), and a restore-specific modal defect (F-CANOPY-010's race, which
  **inverted** on re-run). **Reproduce a second way before writing it down.**
- **A negative-arm pass is not evidence a gate works.** `W7-step1 PASS` recorded the *deny* arm and hid
  **F-CANOPY-025** for five segments. Treat any deny-only row as unproven until its allow arm runs.
- **A count on a shared box is not a measurement.** Attribute processes to the leg pid recorded at bring-up,
  never a box-wide pattern — a naive count "reproduced" F-CASCOR-003b and was another session's cascor.
- **Check the findings ledger AND grep the TSVs before filing.** F-CANOPY-017/018 were minted in a TSV and
  sat outside the ledger for four segments.

## Open findings that bound this segment

Ledger: evidence note §"Findings ledger (Phase 1)" (`:96`) — **but several findings live in the per-segment
sections instead**: F-CANOPY-009 at `:403`, F-CANOPY-010 at `:471`, F-CASCOR-003b at `:1847`. Grep the whole
file, not just the ledger section.

| finding | bearing on segment 15 |
|---|---|
| **F-CANOPY-002** (P0) | WS metrics fast path dead in every live run — **score §3.1 against the REST oracle** |
| **F-CANOPY-003** (P1) | control buttons never re-enable after a successful ack; the 2 s sweep lands at 30 s–minutes, so **a raced command wedges start/pause/resume disabled until the next control action fires the sweep** (observed >8 min) |
| **F-CANOPY-004** (P0/P1) | server callbacks lag 30 s–minutes during a run; budget settle windows accordingly |
| **F-CANOPY-005** (P0) | the WS send-promise races its 3 s timeout, so the REST fallback **double-fires state-changing commands** — an apparently-failed command may already have succeeded |
| **F-CANOPY-006** (P0) | topology counts never update; stale counters (e.g. `monitor.current_hidden_units` reading 0 against a live 10-unit network) belong here, **not** a new finding |
| **F-CANOPY-009 / -010** (P1) | snapshot detail panel wiped ~7 s later; op-confirm modal self-closes ~3.6 s, early-out returns `(False, "", None)` |
| **F-CANOPY-025** (P1) | Live Dataset Switch gate never emits → **W7 hot swap unreachable from the UI**; W6 cold restart is the only route to a dataset-swap event |
| **F-ML-001** (P1) | never run the orphan reaper while the stack is up |
| **F-CASCOR-003b** | unsettled, and its original observation used the discredited box-wide counting method — **re-take with per-leg attribution** |

Fixed this arc, **do not re-file**: F-CANOPY-017 (canopy#489), -022 (#492), -023 (#494), -024 (#493).

## Still open from earlier segments

- **W7 is not blocked by its own preconditions** — "LIVE lane; training **running**", no recurrence
  dependency (`:881`). But **F-CANOPY-025 means the UI entry point is dead**, so W7 is blocked by that
  finding. Record it that way; do not re-file it as a precondition problem.
- **W8 is `N-A`, not BLOCKED**, while the recurrence leg is down (`:904-906`).
- **W6-21** (staging-failure arm) needs the shared juniper-data leg stopped — MANUAL, never attempted.
- **W5-30 + the DEMO lane** — each demo arm must 501 and render `❌ Operation not supported in this mode`.
  Needs the hand-launched DEMO posture above.
- **C2.9-06 / -14 / -15** — not driven in segment 13 for stated reasons (the form never dirtied during a live
  run; the pin gesture is unsolved). Instrument limits, not defects.

## Landing the segment

Aim for one PR per segment. **Deliverables** (segment 14 = ml#1153 for shape):

- **(a)** a new `## Phase 1 — segment 15 (YYYY-MM-DD): <title>` section appended to the evidence note — every
  segment except 8 has written one (segments 4–7, 9–14; segment 8's record is its own handoff plus the TSV
  rows landed by ml#1100). This is the primary narrative record, not optional;
- **(b)** `reports/e2e/<RUN_ID>/statuses.tsv`;
- **(c)** `reports/e2e/CURRENT_RUN_ID`;
- **(d)** matrix status cells **and** the `As of segment N: **X of 298**` counter line (`:77`);
- **(e)** any new `util/ad-hoc/` driver.

Then:

1. Branch from a freshly fetched `origin/main`.
2. **Check `gh pr list` immediately before you push, and re-verify your worktree diff against the pushed
   branch right after opening the PR.** On 2026-08-15 a peer opened a duplicate PR (#1116) on a branch name
   already merged.
3. Commit signed with `util/open_signed_pr.py` (`--repo` / `--branch` / `--add local:repopath` / `--message`
   / `--title` / `--body-file`); `main` enforces `required_signatures`. It uploads **whole files**, so two
   PRs touching the same file must be **merged sequentially with the second rebased**, or the second
   silently reverts the first. `--body-file` bypasses `.github/pull_request_template.md`, so include the
   repo's standing `## Requirements` section yourself (`conventions.yaml` sets `pr.requires_jr_id: true`);
   ml#1153 used *"No tracked JR-ID applies — evidence capture for the canopy E2E validation arc."*
4. Merge with the REST squash endpoint —
   `gh api -X PUT repos/pcalnon/juniper-ml/pulls/<N>/merge -f merge_method=squash` — which succeeds where
   `gh pr merge` stalls. Headless merge is pre-authorized for this arc by the plan (`:689-690`), *"each still
   requires green CI including `ui-tests`, and no PR in this arc touches release/publish machinery or a
   deploy gate"*. (The owner additionally granted blanket approval for this arc's PRs verbally on 2026-08-16,
   in the segment-13/14 session; the plan is the durable source.)
5. **Wait for CI correctly.** A loop keyed on "zero pending" completes **spuriously** — segment 14's watcher
   announced a settled PR while three required Regression Tests were still pending. A docs-only ml PR reports
   **23–24 contexts, of which 17 are SUCCESS** and the rest NEUTRAL/SKIPPED, so guard on
   **`SUCCESS >= 17 AND pending == 0`** — *not* on `total >= 17`, which is satisfied six checks early. Better:
   wait on a **named** required check.
6. After merging: `gh run list --workflow=main-verify.yml -c "$(gh pr view <N> --json mergeCommit -q .mergeCommit.oid)" --json conclusion,url` (**`-c` matches only FULL 40-char SHAs** — a 7-char SHA silently returns `[]`, which reads like "no run yet") (**`-c`**, not
   `--limit 1`, which returns the newest run repo-wide and routinely reports another session's). **main-verify
   goes red periodically** from an inherited docs-deletion finding carried forward by the G3.1 catch-up base
   — it was failing on `604fefc` when this handoff was cut, and green again a few merges later, so check the
   state yourself rather than assuming either. Confirm the failing paths are not yours before acting. If your own diff trips `juniper-docs-additions-check`, add an `Allow-Docs-Rewrite: <path>` commit
   trailer **and carry it into the squash commit message**. A paired status-cell swap does not trip it.
7. Clean up your worktree and branch.

**Before you emit the segment-16 handoff, validate it independently** — this arc's handoffs inherit errors
across generations. This document was rewritten after three independent agents (rubric validator, adversarial
fact-checker, procedure auditor) returned FAIL/NOT READY on the first draft, whose work table was the
*estimator's* list published under the ledger's headline: it would have sent segment 15 to re-drive two
already-`PASS` rows while silently dropping three unfilled ones. Re-run both counting tools and diff your
per-section table against the filler's output before opening the PR.

## Git state at handoff

Cut from `604fefc`. **`origin/main` moves several times a day** — always branch from a freshly fetched
`origin/main`, never from the SHA above.

**No open arc PR in either repo** (juniper-canopy has routine dependabot PRs). Local `arc/canopy-e2e*`
branches from earlier segments remain checked out in session worktrees under
`juniper-ml/.claude/worktrees/`; a checked-out branch cannot be deleted until its worktree goes, so sweeping
them means `scripts/cleanup_session_worktrees.py` first — optional hygiene, not a prerequisite.

Matrix at **212 of 298**. Verdict records: `reports/e2e/20260809T223851Z/rowlog.md`,
`20260810T002233Z/statuses.tsv`, `20260811T010700Z/statuses.tsv`, `20260816T124231Z/statuses.tsv`,
`20260817T093715Z/statuses.tsv`, `20260817T101500Z/statuses.tsv`.
