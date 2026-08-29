# HANDOFF 2026-08-25 — snapshot arc closed; the cascor stop-during-training defect is the live work

> **Continue the juniper-cascor / juniper-ml snapshot-lifecycle arc.** Every item the 2026-08-23
> handoff carried is CLOSED. What remains is **one partly-diagnosed defect** (§2) plus a tail (§3).

**FIRST ACTION: land `ml#1357`** (all required contexts green — 17 required of 26 reported; `BEHIND`) — see §5, a plain merge will not work.
⚠ Its title reads *"…not a defect"*, which refers to the **SharedMemory design** being sound. The
**shutdown behaviour** in §2 *is* a defect. Both are true; do not let the title mislead you.

**THEN §2** — but read §2.3 first. **The diagnosis is incomplete in a specific, named way**, and
the obvious fix is probably the wrong one.

"§N" means a section of THIS document. Other documents are given a path.

> ⚠ **Every number in §3/§4 was re-derived from the LIVE sidecar on 2026-08-25.** An earlier draft
> of this handoff carried pre-regeneration figures and was wrong in six places. If you quote a
> count, re-probe it — the archive grows when other sessions train.

## Documents

| what | path |
|---|---|
| **the §2 diagnosis** | `notes/JUNIPER_2026-08-25_JUNIPER-CASCOR_DEV-SHM-LEAK-CHARACTERISATION.md` §6 |
| attribution null models + the seed defect | `notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md` |
| the five unstable networks | `notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-INSTABILITY-FINDINGS.md` |
| §6.4 retention, RATIFIED | `notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md` §6.4 |
| predecessor handoff | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-23_snapshot-retention-and-arc-closeout.md` |

⚠ **The §2 diagnosis document is UNTRACKED and uncommitted**, and its only other copy is inside
the OPEN `ml#1357`. If that PR is closed and this worktree cleaned, §2 loses its entire evidence
base. Land it or commit it before anything else.

---

## 1. Shipped — do NOT redo

**Merged: 1 cascor + 6 juniper-ml.** `ml#1357` is open. ⚠ Other sessions also have PRs open (e.g. #1356, #1359 at handoff time) — they are NOT this arc's; check ownership before assuming.

| PR | what |
|---|---|
| cascor#575 | an ABSENT `format` attr said `Invalid format: None`, naming nothing → `Missing required attribute: format` |
| ml#1296 | **§6.4 retention RATIFIED: no file in the archive has a deletion path** |
| ml#1301 | attribution null-model findings (three nulls) |
| ml#1306 | **the two-floor gate** — clear the untrained floor AND a cross-dataset floor |
| ml#1314 | the five unstable networks: 3 artifacts, 1 real multi-dataset run, 1 marginal |
| ml#1333 | **the dataset instance is pinned** — attribution was not reproducible |
| ml#1347 | backfill root cause: cascor#575's new wording lost 6 files (273→267) |

**Sidecar chain regenerated twice** (index → classify → attribute → backfill, ~41 min;
`util/ad-hoc/2026-08-24_regenerate_sidecar_chain.bash`). Final, seeded, reproducible:

- index / classification / backfill **27,962**; attribution **27,689** (= 27,962 − 273)
- all rows **schema v2**; both floors on all **26,252** scored rows
- **108 attributed** — xor 94, circles 7, spiral 4, moon 3 — plus **8 ambiguous**
- cohort B exactly **273**; root-cause coverage **273/273**

⚠ **108 is the TOOL's output; the DEFENSIBLE set is ~100.** spiral's four are withdrawn by §4.5 on
independent grounds — they clear the floor but sit at **8, 10, 12, 13** hidden units, and the
tool's own positive control records 8 units scoring 0.510 (chance) on spiral. That is knowledge
about the *problem*, not the score vector; a floor cannot encode it. **Do not quote "spiral 4" as a
property of the archive.** `--min-hidden` is the honest filter, but `--write` **refuses** it by
design (a sidecar must never silently cover a subset), so those rows are always in the file.

**Backups (durable, NOT `/tmp`)**: `Juniper/backups/snapshot-sidecars-2026-08-24/` (v1, 129
attributed) and `…-2026-08-24-v2-preseed/` (v2 pre-seed-fix, 109). Keep the pre-seed set — it is
the physical evidence that attribution was non-reproducible.

---

## 2. THE REMAINING WORK — stop-during-training escalates to SIGKILL

**A juniper-cascor change.** Full diagnosis in the §6 document; nothing implemented.

### 2.0 ⚠ CHECK THESE IN-FLIGHT PRs FIRST — both collide

| PR | touches | collides with |
|---|---|---|
| **cascor#584** (DRAFT) | `src/api/lifecycle/manager.py` + 4 lifecycle test files | **§2 edits that exact file** |
| **ml#1340** (OPEN) | `util/snapshot_attribute.py`, `tests/test_snapshot_attribute.py`, `docs/REFERENCE.md`, the null-model doc, `util/ad-hoc/2026-08-24_regenerate_sidecar_chain.bash` | **§3 item 1 lands in exactly this surface** |

**Why this is dangerous:** `util/open_signed_pr.py` sends **WHOLE files**, and the §8 staleness
guard (`git diff --stat origin/main -- <path>`) **cannot see an in-flight PR by construction** — it
compares against `main`, where that work has not landed. The guard that caught a `REFERENCE.md`
clobber this session will NOT catch these. Check with
`gh pr view <N> --repo <repo> --json files,state`; both may have merged or closed since.

### 2.1 What is established

Stopping the service **while training is in progress** leaves a leak; stopping it with no training
does not. Both observed, same shutdown path (§2.5). The shutdown itself is **graceful** — the full
FastAPI lifespan sequence completes in ~4 ms.

⚠ **Paths below are repo-qualified deliberately — §2 spans BOTH repos.** One real defect is
confirmed in **`juniper-cascor/src/api/lifecycle/manager.py`**, `TrainingLifecycleManager.shutdown()`
(re-derive by symbol; the three lines are **not contiguous** — they sit at roughly :5023, :5034 and
:5036 with other work between):

```python
self._stop_event.set()
...
self._executor.shutdown(wait=False, cancel_futures=True)   # does NOT wait
self.logger.info("TrainingLifecycleManager shut down")     # logged regardless
```

`cancel_futures=True` cancels only *queued* futures, never the running one, and `wait=False` returns
immediately — so the reassuring log line is emitted while training may still be live.

**`juniper-ml/util/juniper_chop_all.bash`** (~:184-214 — note: juniper-**ml**, not cascor) then sends SIGTERM, waits `SIGTERM_TIMEOUT` (**default
15 s**), and escalates to **SIGKILL**.

**That the process was SIGKILLed is a DEDUCTION, not an observed signal** — the signal is logged
nowhere. The evidence is the residue itself: `atexit.register(self._cleanup_shared_memory)` is
registered, so a normal exit would have cleaned up. It didn't, so the interpreter never reached exit.

### 2.2 ⚠ Why it matters far more than the 371 KB

**Same TRIGGER as cohort B** — the 273 truncated snapshot writes, the archive's only irrecoverable
loss. `train_output_layer` calls `create_snapshot()` unconditionally, so a service killed
mid-training was also killed mid-write.

⚠ **Be precise about what #561 did, because an earlier draft overstated it.** These are two
independent resource paths that share only "the process got SIGKILLed": shm segments cleaned by
`atexit`, versus partial HDF5 files. `_atomic_hdf5_write` genuinely closed the archive path — post-#561
a killed write leaves an **unrenamed temp file**, so it cannot land in the archive at all, and
`snapshot_serializer.py:134` calls the non-atomic write *"the sole root cause of every
structurally-incomplete file in the live archive."* So **do not say "#561 fixed the symptom, not the
cause."** The accurate claim is narrower and still worth acting on: **the trigger that used to
truncate archive writes is still firing ~1/day, and now shows up only in `/dev/shm`.**

### 2.3 ⚠⚠ THE DIAGNOSIS IS INCOMPLETE — do not build a stop check first

**A cooperative-interrupt mechanism ALREADY EXISTS and is live.** An earlier draft of this handoff
said training had no escape; that was wrong and would have sent you to build a second one. The real
path, traced end to end:

```
cascade_correlation.py  train_output_layer   ->  _cb(epoch=…, epochs=…, loss=…)   [every 25 epochs]
api/models/cascor_model.py  _on_epoch        ->  emit("epoch_end", …) -> on_event(...)   [no try/except]
api/lifecycle/manager.py    _handle_event    ->  if etype == "epoch_end": self._check_for_interrupt()
api/lifecycle/manager.py    _check_for_interrupt -> if self._stop_event.is_set(): raise TrainingInterrupted
```

The escape works by **exception**, not by return value — `_check_for_interrupt`'s own docstring says
*"raising here propagates straight out of `fit` — this is how stop/pause rides CCN's native hooks
(WS-6 PR-B3.3)"*.

**So the open question is not "how do we interrupt training" — it is "why did the existing
interrupt not fire?"** It should trigger within ≤25 epochs, which is well under a second. Candidates,
none yet tested:

1. That training was **not** driven through `CascorModel.fit(on_event=…)`, so no sink was wired.
2. `shutdown()`'s `_stop_event` is not the object `_check_for_interrupt` reads (there are **two**
   `_stop_event` assignments in `manager.py`, ~:896 and ~:1130 — confirm they are the same class).
3. The interrupt *did* fire and something else held the interpreter open — the **candidate worker
   pool / forkserver children** are the documented suspect (`_release_candidate_worker_pool` already
   warns *"forkserver children may survive this run"*). This is step 5 of the §6.2 mechanism.

**Start by determining which.** A one-line instrumented repro (stop mid-training, log whether
`_check_for_interrupt` is reached) settles it and costs minutes.

### 2.4 Fix order — conditional on §2.3, not before it

1. **`shutdown()` must wait, bounded.** ⚠ **Do NOT "fix" this by flipping `wait=False` to
   `wait=True`** — `concurrent.futures.Executor.shutdown(self, wait=True, *, cancel_futures=False)`
   has **no timeout**, so `wait=True` blocks until training ends naturally (minutes) and guarantees
   the 15 s SIGKILL. That is strictly worse than today, and without even the log line.

   **The bounded pattern already exists in the same file** — the `swap_dataset_live` path at
   `manager.py` ~:2927-2939 sets `_stop_event`, sets `_pause_event` (so the pause wait-loop wakes to
   observe the stop), then joins `self._training_future` with `future.result(timeout=10)`. Reuse it.

   Two constraints this step must respect, both verified:
   - `lifecycle.shutdown()` is called at `juniper-cascor/src/api/app.py:463` inside an **`async def
     lifespan`** — a synchronous multi-second wait **blocks the event loop**.
   - `worker_coordinator.shutdown()` (`app.py:451`) and `ws_manager.close_all()` (`app.py:458`) run
     **before** it, so you are waiting on training whose workers are already gone.

2. **Then whatever §2.3 identifies.** If it is cause 3, the pool is the target and no stop check is
   needed. If the callback path is genuinely unreachable, note **`_stop_event` is NOT in scope in
   `cascade_correlation.py`** (zero references; the network holds no manager reference), so it must
   be plumbed the way `_output_epoch_callback` already is. Not a one-line change.

   ⚠ **If you do add a check, `raise` — never `break`.** `create_snapshot()` sits at
   `cascade_correlation.py` ~:2181, **AFTER** the epoch loop (~:2147). A `break` falls straight
   through into it and **writes a snapshot during shutdown**, reproducing the very failure mode §2.2
   describes. Only raising (the existing `TrainingInterrupted`) skips it.

3. **Only then** consider raising `SIGTERM_TIMEOUT`. ⚠ That knob lives in
   **`juniper-ml/util/juniper_chop_all.bash`** (~:70), **a different repo from steps 1-2** — it needs
   its own PR. Raising it first lengthens every stop and fixes nothing.

⚠ **Line numbers drift** — six merges moved them during the predecessor arc. Re-derive by symbol.

### 2.5 The control, and how to reproduce SAFELY

2026-08-24 23:47 ran the complete graceful lifespan **and leaked**, with training live at epoch
7960. 2026-08-25 05:22 ran the byte-identical sequence with **no training** and leaked nothing.

⚠ **Do NOT reproduce by "stopping the service".** At handoff time this host had **two live cascor
stacks on :8202** (pids ~789014/789015 and ~880900/880901), `juniper-cascor-worker` processes, and
another session's campaign watcher. `util/juniper_chop_all.bash` is the only stop tool named in
this document and it **SIGKILLs** — running it would kill other people's live experiments, which is
a resident AGENTS.md hazard.

Reproduce on an **isolated stack you own**:

1. `util/isolated_stack.bash --up` (own ports/run-dir), and confirm the pid you will stop.
2. Capture a **before** snapshot: `ls -la --time-style=+%s /dev/shm/juniper_train_* > before.txt`
   (there were already **10** segments and **90** `sem.mp-*` at handoff — the signature is *one new
   pair*, not an absolute count).
3. Start training on that stack; wait until epochs are logging.
4. Stop **only your** pid, then diff against `before.txt`. A new segment plus ~9 new `sem.mp-*`
   means it still escalates.

---

## 3. The tail, highest value first

1. **The displacement guard** (designed, not shipped) — ⚠ **and its premise needs restating.** An
   unattributable dataset can never win, so attribution falls through to a **lower-scoring
   runner-up** instead of refusing. Live figures: **6 of 108** survivors are displaced —
   **spiral 4 AND xor 2** (the xor pair at 18u/19u, both beaten by gaussian at 0.94). An earlier
   draft claimed "5 of 104, all spiral, xor zero" — wrong on every count.
   ⚠ **Do not frame the guard on "floor ≥1.000".** Post-regeneration, moon's cross floor is **0.86**
   and moon has **3 attributions** — it is no longer structurally unattributable. Frame it on the
   observed condition: *the dataset with the best RAW score is not the one that won.* Needs its own
   PR, a regression test, and a decision on ties.
2. **`846587fb` — restate before acting.** Live: its xor score at 1 hidden unit is **0.79** (not the
   0.855 an earlier draft claimed), and it is **attributed to circles at a perfect 1.000 at 2, 3 and
   4 units** — three consecutive confident attributions the earlier draft omitted entirely. The open
   question is only whether the single 1-unit xor row is real; the circles run is not in doubt.
3. **Decide whether to persist training history** — ⚠ **the flag is `include_training_state`, NOT
   `save_history`.** `save_history` exists nowhere in juniper-cascor; an earlier draft invented it.
   The real lever is `snapshot_serializer.py:180` (`include_training_state: bool = False`) gated at
   `:217`, and `create_snapshot` (`cascade_correlation.py` ~:5078) **never passes it** — which is
   why the group is absent.
   ⚠ **And four snapshots already carry it**: a full-archive census finds **4 of ~27,956** with a
   `history` group (2026-08-11 and 08-13), readable now via `read_dataset_swap_events`. The
   "UNANSWERABLE, not no" framing holds for the archive at large — a 500-sample of the
   2025-10→2026-07 window found zero — but **read those four first**; they may settle the
   multi-dataset question with no new flag at all.
4. **The restore drill this arc's ratification created.** §6.4.2 q3 was answered *"Not until a
   restore drill passes"*, and §6.4.3 records it as **owed to the backup arc regardless** and a hard
   precondition if retention is revisited. `util/juniper-backup.bash` line 173 says it cannot prove
   the tar inside is intact; **no drill has ever run.** Still gated on it: **S-4** (cold-archive
   location), plus unanswered **S-1** (move snapshots out of the checkout) and **S-3**
   (`snapshot_history.jsonl` vs the §6.2 index). ⚠ Do not let a later session satisfy q3 by pointing
   at an archive nobody has restored — that is the ml#1263 failure class exactly.
5. **`snapshot_counter` is LIVE and unused, and a shipped docstring still denies it.** 28 distinct
   values over an 800-snapshot sample, one network running **0 → 109**: a per-run ordering signal
   independent of filename mtime (corrected in ml#1282). `util/snapshot_classify.py` (~:60) still
   asserts the retracted *"`snapshot_counter` is 0"* — fix it, then consider whether the signal
   settles item 2 or orders `2537e0f0`'s two sessions without mtime.
6. **A guarded `/dev/shm` sweeper** — optional, low value (371 KB, and it erases the ledger). Needs
   **all** of: zero open fds, **an age threshold**, `--dry-run` default with `--yes`, and a refusal
   to touch anything not matching `juniper_train_*`. ⚠ A **startup sweep inside cascor** is the most
   dangerous variant — it runs while peer cascor processes are live and will unlink a peer's pending
   block without the age threshold.
7. **moon is undecidable, not settled.** 3 survive with `5af596ef` excluded from its reference class,
   0 with it included — and that snapshot is itself the unstable network. Do not report it resolved
   in either direction.
8. **Read the `/dev/shm` ledger as telemetry after §2 ships.** The pair-count (1 segment + 9
   `sem.mp-*` per event, ~1.25/day) is the **only production verification** that the fix worked — the
   kill is logged nowhere else. Baseline: **10 events, 08-17 → 08-24**.

---

## 4. Findings that constrain the work

### 4.1 ⚠ Attribution was NOT reproducible; every pre-2026-08-24 count is run-specific

Five of the six 2-D generators declare `seed: int | None = Field(default=None)`, so `load_datasets`
redrew the data **on every call**. **`spiral` alone is seeded** (`SPIRAL_DEFAULT_SEED = 42`) — and
spiral was the only column steady across every rebuild. That tell was visible for days.

A 0.005 jitter moved moon's score 1.000 → 0.995 → flipped one snapshot's first-pass winner → removed
it from moon's own reference class → dropped moon's cross floor → changed six verdicts. **Any
statistic defined as a max over a reference class is this brittle.**

Fixed in ml#1333: `seeded_params()` supplies `DATASET_SEED = 20260824` **only where a generator
declares none**. Verify reproducibility as a property, both directions.

### 4.2 ⚠ A snapshot must not help set the bar it is judged against

`cross_floor_excluding()` exists because `5af596ef` scored moon 1.000, setting moon's floor to 1.000,
which drove its **own** moon lift to zero and removed moon as a runner-up.

⚠ **A residual circularity remains and self-exclusion does not fix it.** Floor B's reference class is
built **from attributions**, so a wrong attribution contaminates the floor. **The two-floor verdict is
not an oracle.** Capacity-banding the class (±20 units) shrinks it to ~4 networks for high-capacity
targets and costs xor 17 survivors — that is small-sample noise, **not a finding**. Written down so
nobody rediscovers it and reports it as one.

### 4.3 The capacity confound is real but INERT — and points the other way

0 of 129 attributions had zero hidden units, yet a capacity-matched null withdrew only **3**. At high
capacity the matched floor is often **lower**: ~100 random cascade units inject noise columns and push
the score toward chance. **Do not rebuild a capacity-matched null expecting it to tighten anything.**

### 4.4 ⚠ Only TWO metadata fields are inert, not three

| field | reality |
|---|---|
| `current_epoch` | **INERT** — 0 in all 800 sampled; never assigned |
| `patience_counter` / `best_value_loss` | inert *before* cascor#565; **assigned now** |
| **`snapshot_counter`** | **LIVE — 28 distinct values** |

Use `arch.num_hidden_units` as the iteration **lower bound**, never an epoch count.

### 4.5 spiral is withdrawn; xor holds — but check the live margins

spiral: 20 → 19 → 9 → 4 across three nulls; capacity flat-to-falling; the tool's own `--min-hidden`
text records 8 units scoring 0.510 (chance) on spiral, yet 11 of the 20 sat at ≤10 units; and its
survivors score **higher on moon than on spiral**.

xor's separation is real but **thinner than an earlier draft claimed**. Live: floors
`untrained 0.72 / cross_dataset 0.70`; cohort minimum **0.785**, with two rows below 0.81. The
conclusion survives (0.785 > 0.72) but the margin is **0.010**, not 0.035. Corroborated independently
by a monotone learning curve, which no floor choice affects.

---

## 5. ⚠ Merging is contended — read before trying

`util/safe_merge.py` **refused **ml#1333 and ml#1347** with *"went BEHIND 3 times without a stable
green head; main is moving faster than CI completes"*. That is the tool working. Measured: main's
median merge gap **~12 min**, required CI **~10-15 min**.

**Do not re-run `update-branch` the moment a PR goes BEHIND** — it *restarts* CI and guarantees
another loss. Four such nudges produced four wasted runs and zero progress.

Working pattern (merge queues are settled-unavailable). ⚠ **Check the two preconditions first** —
the safety guarantee below is conditional, and `util/safe_merge.py` (~:56, :388-398) documents why:
where `allow_auto_merge` is false, `--auto` **does not arm at all — it silently falls back to an
immediate merge**, which with the owner's `always` ruleset bypass can land a PR whose checks never
finished.

```bash
gh api repos/pcalnon/juniper-ml --jq .allow_auto_merge     # MUST be true, else do NOT use --auto
# and the ruleset must have strict_required_status_checks_policy = true (it did at handoff)
```

1. Arm auto-merge — `gh pr merge <N> --repo pcalnon/juniper-ml --auto --squash`. **Given those two
   preconditions** it is checks-gated and cannot land an untested head.
2. Update the branch **only** once main has been quiet ~4 min, then leave that attempt a full ~17 min
   CI window. Gaps of 18-27 min occur; one is enough. Bound your retries — do not loop indefinitely.

```bash
# is it behind?  ⚠ `baseRefOid` is NOT a `gh pr --json` field on gh 2.46 — use the REST API:
gh api repos/pcalnon/juniper-ml/pulls/<N> --jq .base.sha
gh api repos/pcalnon/juniper-ml/commits/main --jq .sha        # differ => behind
# how long has main been quiet?
gh api repos/pcalnon/juniper-ml/commits/main --jq .commit.committer.date
# update it
gh api --method PUT repos/pcalnon/juniper-ml/pulls/<N>/update-branch
# confirm it actually landed (waiters get killed — §6.10)
gh pr view <N> --repo pcalnon/juniper-ml --json state,mergedAt
```

**Compare `.base.sha` to main's sha, NEVER `mergeStateStatus == "BEHIND"`.** GitHub returns
`UNKNOWN` while recomputing, and a genuinely-behind PR sits there long enough to be skipped
**silently and forever**.

---

## 6. Traps this session paid for

1. **You need BOTH lint invocations — neither subsumes the other.**
   - `pre-commit run --files <each changed file>` catches what bare `flake8` cannot (the hook loads
     bugbear/comprehensions/simplify). ml#1333 passed `flake8 exit=0` and every test, then failed
     required **Pre-commit (Python 3.13)** on **B903**. Fix with real code (`__slots__`), never `noqa`.
   - `python -m flake8 --select=F401,F811,F841 --max-line-length=512 util/<files>` catches what
     **pre-commit cannot**: its flake8 hook `--extend-ignore`s **F401,F811** and scopes to
     `^(scripts|tests)/.*\.py$` — **`util/` is unlinted for unused imports**, and that is where §3
     item 1 lands. An unused import there reaches `main` and trips CodeQL on someone else's PR.
2. **`mergeStateStatus=BLOCKED` at 17/17 green means an unresolved review thread**, not a check
   failure. CodeQL blocked three PRs this way in the predecessor arc. `gh pr checks` does not show it;
   use the `reviewThreads` GraphQL query. The thread self-resolves once the line changes.
3. **A new suite must be verified to FAIL against unfixed code, asserting the SPECIFIC status** —
   `assert status != OK` once passed against a broken design. And **juniper-ml's CI test list is
   hand-maintained**: a new `tests/test_*.py` needs three edits (ci.yml run block, ci.yml install
   block, AGENTS.md), enforced by `tests/test_ci_test_wiring_drift.py`.
4. **`JUNIPER_CASCOR_SNAPSHOTS_DIR` has two OPPOSITE traps.** Export it to a scratch dir **before any
   cascor import** when probing (`constants_hdf5.py` reads it at import time; `train_output_layer`
   calls `create_snapshot()` unconditionally — otherwise your probe grows the archive it measures).
   But **never** set it for the sidecar chain: it is *also* `snapshot_index.default_root()`, so
   redirecting points all four stages at an empty scratch root. Pass `--root` explicitly.
5. **A message string can be an undeclared cross-repo contract.** cascor#575 changed a rejection
   message; `snapshot_backfill.py` matched the old literal; 6 files silently lost their root cause
   (273→267) while every other count stayed right and both repos passed their own tests.
6. **`tail -1` can hide a command's failure.** A `git merge --ff-only` refused because untracked files
   would be overwritten; `tail -1` showed only "Updating …". After merging a PR whose files you hold
   locally, `rm` the untracked copies first.
7. **`df` on `/dev/shm` is not a leak measurement.** It read 32 MB against `du`'s 732 KB; the gap was
   Chromium plus `torch_*` held by the **live** service — all correct. Use
   `du -ch /dev/shm/juniper_train_*`. This already caused one misreport.
8. **Zero open fds does NOT mean orphaned.** Verified: `close()` leaves 0 fds with the file still
   present — the normal state of a live round's pending block. An age threshold is the load-bearing
   check, not the fd count.
9. **Worktree isolation blocks `git -C` into sibling repos**, blocks `source`, and refuses commands it
   deems too complex. Use `gh api` for sibling-repo facts; split compound commands.
10. **A background wait can be killed by the ~3600 s worker lease.** Re-check state directly rather
    than trusting a waiter completed.
11. **Three stale `*.pid` files persist under `~/.local/state/juniper-experiments/`**, all pointing at
    dead processes, **two at the directory root rather than in run dirs**. Not cosmetic: a run-dir
    `*.pid` is one of only **two** orphan-reaper protection keys (AGENTS.md resident hazard), so a
    root-level stale pidfile protects nothing while sparing a recycled PID.

---

## 7. Verification commands

⚠ **Run these from the WORKTREE, not the primary checkout.** The primary
`/home/pcalnon/Development/python/Juniper/juniper-ml` is behind `main`, and the documented test
counts reproduce **only** in the worktree.

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper
WT="$JUNIPER/juniper-ml/.claude/worktrees/merry-puzzling-quasar"   # or your own
ROOT="$JUNIPER/juniper-cascor/cascor-snapshots"
PY=/opt/miniforge3/envs/JuniperCascor1/bin/python   # envs are JuniperCascor1 / JuniperCascor-DEPRECATED;
                                                    # there is NO bare "JuniperCascor". `conda activate`
                                                    # needs the shell hook in a non-interactive shell.

gh pr list --repo pcalnon/juniper-ml --state open      # dup-guard AND §2.0 collision check
gh pr list --repo pcalnon/juniper-cascor --state open

cd "$WT"
python3 -m unittest tests/test_snapshot_attribute.py tests/test_snapshot_backfill.py   # 49 + 33 = 82

# the four sidecars (gitignored, beside the archive)
$PY util/snapshot_index.py      --root "$ROOT" --stats
$PY util/snapshot_classify.py   --root "$ROOT" --from-sidecar --stats
$PY util/snapshot_attribute.py  --root "$ROOT" --from-sidecar --stats
$PY util/snapshot_backfill.py   --root "$ROOT" --from-sidecar --stats

# reproducibility as a PROPERTY — must diff empty
T=$(mktemp -d)   # NOT the repo root: untracked files there block a later --ff-only merge (§6.6)
$PY util/snapshot_attribute.py --root "$ROOT" --sample 300 --seed 4242 --json > "$T/A.json"
$PY util/snapshot_attribute.py --root "$ROOT" --sample 300 --seed 4242 --json > "$T/B.json"
diff "$T/A.json" "$T/B.json"   # MUST be empty; if not, you are on a checkout without ml#1333

# the §2 leak, measured correctly
ls -1 /dev/shm | grep -c '^juniper_train_' ; du -ch /dev/shm/juniper_train_* | tail -1
```

⚠ **The cascor gates below are MANDATORY for §2**, not optional: it edits the training path the
golden trajectory exists to pin. Without them a trajectory shift is found post-push, or not at all.

```bash
cd "$JUNIPER/juniper-cascor/src"
$PY -m pytest tests/unit -q --slow
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CASCOR_NUM_PROCESSES=1 \
  $PY -m pytest -m golden --golden --slow --integration tests/integration/test_golden_trajectory.py
```

**Expected**: index/classification/backfill **27,962**; attribution **27,689**, **108** attributed
(xor 94 / circles 7 / spiral 4 / moon 3) + 8 ambiguous; classification `fails_to_load` **273** with
`Missing required group: random` 265 / `Missing required attribute: format` 6 /
`Missing required group: params` 2; backfill `{"B": 273}`. The archive grows when other sessions
train, so the raw `.h5` count drifts while sidecar totals do not — **re-run the chain rather than
reconciling by hand** — that is `util/ad-hoc/2026-08-24_regenerate_sidecar_chain.bash`, a **~41 min**
operation that **refuses to start without `--backup DIR`** (pointing at a directory already holding
all four sidecars) and whose `REPO` default is hard-coded to *this* worktree — pass `--repo` if you
are elsewhere, because the standing cleanup procedure removes it.

---

## 8. Git state and procedure

- **juniper-ml `origin/main`: re-probe** (it moved ~15 times this session; it was `7464695` when this
  was drafted and had already moved by validation). **juniper-cascor `origin/main`: `c4bbe81502`.**
- ⚠ **The juniper-cascor checkout is NOT stale** — local `main` == `origin/main` == `c4bbe81502`. An
  earlier draft said it needed a fast-forward; that was wrong. **The juniper-ml primary checkout IS
  behind.** Verify before assuming either.
- Work was done in `juniper-ml/.claude/worktrees/merry-puzzling-quasar`, branch
  `worktree-merry-puzzling-quasar`.
- **Uncommitted: TWO files** — this handoff, and
  `notes/JUNIPER_2026-08-25_JUNIPER-CASCOR_DEV-SHM-LEAK-CHARACTERISATION.md` (the sole source for §2,
  otherwise only inside the open `ml#1357`).
- **`required_signatures` is live fleet-wide** — a headless local commit cannot land. Use
  `util/open_signed_pr.py`; it refuses an existing branch by design, so amend in-flight PRs with
  `util/ad-hoc/2026-08-22_amend_signed_pr.py`.
- ⚠ **`open_signed_pr.py` sends WHOLE files.** Confirm your copy is current
  (`git diff --stat origin/main -- <path>` should show only your change) — and remember it **cannot
  see in-flight PRs** (§2.0).
- **Worktrees are the standing default**, centralized in `Juniper/worktrees/`.
- ⚠ **`pre-commit` on anything under `prompts/` is a VACUOUS PASS** — the config excludes
  `prompts/.*`, so every hook reports "no files to check", **including doc-link validation**.
  Handoffs are never machine-validated. Validate the next one the way this one was (§9).

---

## 9. Validation record

Reviewed by independent agents under three distinct lenses, each prompted to **refute** rather than
confirm, per the project's multi-agent adversarial SOP:

| lens | found |
|---|---|
| **factual re-probe** | **17 findings.** Six live counts in an earlier draft were stale (displacement 5→**6**, "xor zero"→**xor 2**, 104→**108**, moon's floor 1.000→**0.86**, xor cohort min 0.810→**0.785**, `846587fb` xor 0.855→**0.79**), and one **amputation of its own**: the draft deleted the clause saying the interrupt mechanism already exists, which would have sent a successor to build a second one. Also caught a false "cascor checkout is stale" and a wrong conda rationale. |
| **amputation** | **13 findings.** Missing cascor regression gates; the forkserver step dropped from a six-step mechanism; **two in-flight PRs colliding with the remaining work**; the restore-drill obligation the ratification created; 108-vs-100 unreconciled; Floor B's residual circularity; `snapshot_counter` LIVE with a stale docstring still denying it. |
| **cold successor** | **5 blockers, 11 major, 8 minor** — the harshest of the three. It *executed* the document. §7 as first written pointed at the primary checkout, where the reproducibility test emits an **8,428-line diff** and the unittest prints `OK` while running 75 of 82 — a vacuous pass of exactly the class this project tracks. It also caught that `wait=True` is **unbounded** (no `timeout` on `Executor.shutdown`) so the obvious fix is strictly worse; that `create_snapshot()` sits **after** the epoch loop, making `break` vs `raise` decisive; that `save_history` **does not exist** (`include_training_state` does); that `baseRefOid` is not a `gh pr --json` field; that the §2.5 repro would have killed other sessions' live stacks; and that "#561 fixed the symptom not the cause" contradicts the code's own record. |

**Every blocker and major is incorporated.** Three lessons worth keeping:

1. **Two of the three lenses caught errors the others missed entirely**, and the overlap was small.
   A single reviewer — however careful — would have shipped most of this.
2. **The most dangerous findings were not false statements but true ones with a load-bearing clause
   removed.** The draft's "training has no escape" was literally accurate about
   `cascade_correlation.py` and would still have sent a successor to rebuild a live mechanism.
3. **Re-probing beats re-reading.** Six counts were stale because they were written before the
   sidecar was regenerated — the same trap §4.1 warns about, committed inside the document that
   warns about it. Only an agent that *ran the queries* caught it.
