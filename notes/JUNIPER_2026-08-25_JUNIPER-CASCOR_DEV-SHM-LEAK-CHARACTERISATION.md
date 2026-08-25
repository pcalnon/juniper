# `/dev/shm` leak — characterisation

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-25

**Status**: FINDINGS — measured, read-only. Nothing was unlinked or killed in producing this.

**Headline: the OPT-5 SharedMemory design is not defective, and the leak is ~371 KB.** It fires
when the service is **stopped while training is in progress** — a *graceful* shutdown that then
escalates to SIGKILL because nothing waits for training to unwind (§6). `/dev/shm` is therefore
an accidental **ledger of that event**: ten occurrences in eight days.

**And it is the same root cause that produced cohort B** — the 273 truncated snapshot writes,
the archive's only irrecoverable loss (§6.3). juniper-cascor#561 made those writes atomic, which
is why cohort B stopped growing; the kill that caused them did not stop, and now shows up here
instead.

---

## 1. What is actually there

| | count | size |
|---|---:|---:|
| `juniper_train_*` segments | **10** | **368 KB** |
| `sem.mp-*` semaphores | **90** | ~2.9 KB |
| **total attributable to Juniper** | | **~371 KB** |

Against a 47 GB tmpfs. **Every one is orphaned** — a scan of `/proc/*/fd` finds **zero** open
descriptors on any of them.

Growth measured over 24 h (2026-08-24 → 08-25): segments 8 → 10, semaphores 72 → 90. So
roughly **+1 leak event per day**.

### 1.1 ⚠ `df` says 32 MB; that is NOT this leak

`df` reports ~32 MB used while `du` reports 732 KB. The ~31 MB difference is **unlinked-but-still-open**
objects, which `ls` and `du` cannot see. Enumerated via `/proc/*/fd`, they are:

- **Chromium** (`.org.chromium.Chromium.*`) — unrelated to Juniper.
- **`torch_<pid>_*`** held by the **live** cascor service (pid 789015, uvicorn on 127.0.0.1:8202).

Both are *correct* behaviour: unlink-then-keep-open is the standard pattern, and the pages are
freed when the holder exits. **No torch-side leak exists** — there are no visible `torch_*` files
at all, meaning every one was properly unlinked.

This is the same trap that produced the earlier "32 MB" misreport. `df` on `/dev/shm` is not a
measure of leaked Juniper memory; **`du -ch /dev/shm/juniper_train_*` is**.

---

## 2. The leak has exact structure: 10 events, each 9 semaphores + 1 segment

Grouping every object by mtime:

```
when            shm  sem          when            shm  sem
08-17 04:33       0    9          08-23 17:08       0    9
08-17 05:04       1    0          08-23 17:09       1    0
08-21 16:47       0    9          08-23 17:10       0    9
08-21 16:51       1    0          08-23 18:10       1    0
08-22 16:44       0    9          08-23 18:12       0    9
08-22 17:13       1    0          08-23 18:15       1    0
08-23 06:28       0    9          08-24 22:59       0    9
08-23 06:41       1    0          08-24 23:01       1    0
08-23 14:31       0    9          08-24 23:46       1    9
08-23 14:38       1    0          TOTAL            10   90
```

Ten pairs, no exceptions: **9 semaphores at pool startup, then exactly 1 segment** between one
minute and one hour later (the gap from pool creation to the first candidate-task generation).

---

## 3. Why exactly one segment per event — the design is correct

`SharedTrainingMemory` uses a **deferred unlink**, deliberately
(`cascade_correlation.py`, `_execute_parallel_training` / `_cleanup_pending_shared_memory`):

1. Round *N* creates a block → `_active_shm_blocks`.
2. End of round *N*: `close()` **only, not unlink** — "persistent worker processes may still hold
   references for in-flight tasks" — and the block moves to `_pending_shm_unlinks`.
3. Start of round *N+1*: the pending blocks are unlinked, after results are drained.

So at any instant **exactly one round's block** sits closed-but-unlinked. A process killed inside
that window leaks precisely one segment — which is what the table shows. The nine semaphores are
the `multiprocessing` pool's, leaked because Python's `resource_tracker` never got to run.

**`atexit` is registered** (`atexit.register(self._cleanup_shared_memory)`), so a *normal* exit
cleans up completely. Every object here therefore comes from a process that died **without
running `atexit`** — SIGKILL, `os._exit`, or a crash. The leak is not a missing cleanup path; it
is the residue of a process that never reached exit — §6 identifies exactly when and why that happens.

---

## 4. ⚠ The obvious sweep predicate is unsafe — verified, not reasoned

The tempting rule is "no open fd ⇒ orphaned ⇒ unlink it". **That is wrong**, and a probe shows
why:

```
LIVE (attached)   fds: 6
AFTER close()     fds: 0   (file still exists: True)
AFTER unlink()    exists: False
```

`close()` leaves **zero fds with the file still present** — and that is precisely the *normal*
state of a block sitting in `_pending_shm_unlinks` during a **live** training round. A sweeper
keyed on fd-count alone cannot tell a leaked block from a live one, and would unlink a block a
queued worker has not attached to yet, failing that task.

**An age threshold is the load-bearing safety mechanism, not the fd check.** A round lasts
minutes, so a segment older than a couple of hours cannot belong to an in-flight round. This
matters concretely today: a cascor service *is* live on 127.0.0.1:8202 while these ten segments
sit orphaned.

Any sweeper therefore needs **all** of: zero open fds, **and** an age threshold, **and**
`--dry-run` by default with `--yes` required, **and** a refusal to touch anything not matching
`juniper_train_*`.

---

## 5. What this is actually worth

**Not the disk.** 371 KB against 47 GB will never matter, and the growth rate (~1 event/day,
~46 KB/day) reaches ~17 MB a year.

**The signal.** Each leaked pair is a receipt for a training process that did not exit cleanly:
**ten in eight days, ~1.25/day.** `/dev/shm` has been keeping this ledger by accident, and it is
the only place the event is written down at all — the kill itself is logged nowhere.

The actionable question is therefore **not** "how do we reclaim 371 KB" but **"why is roughly one
cascor run a day dying without a clean shutdown?"** — which §6 answers, and the answer is a real
defect rather than an environmental accident.

### 5.1 Options, in order of value

1. **Treat it as telemetry.** Read the pair-count when investigating hard kills; it is a free,
   retroactive record with timestamps.
2. **A guarded sweeper** (`util/`, dry-run default, §4's four conditions). Low value on its own —
   it reclaims nothing that matters and erases the ledger — but useful before a long campaign
   that wants a clean baseline.
3. **A startup sweep inside cascor.** Tempting and the most dangerous: it would run while other
   cascor processes are live, so it needs §4's age threshold or it will unlink a peer's pending
   block. Not recommended without that.

---

## 6. ⚠ What is actually killing the runs — and it is NOT a hard kill

§3 assumed the residue came from processes that were simply SIGKILLed. Chasing it produced a
more specific and more useful answer: **the leak fires when the cascor service is stopped while
training is in progress**, and the shutdown that produced it was *graceful*.

### 6.1 The evidence, with a control

`logs/juniper_cascor.log.1` ends mid-training and the rotated log opens on the shutdown sequence:

```
23:46:59  manager.py: disconnect         WebSocket disconnected (0 active, 0 pending)
23:47:00  train_output_layer             Output Layer Training - Epoch 7960     <- log.1 ends here
23:47:00,080  coordinator.py: stop_monitor    Health monitor thread stopped     <- new log opens
23:47:00,083  coordinator.py: cancel_round    Current round cancelled
23:47:00,083  coordinator.py: shutdown        WorkerCoordinator shut down
23:47:00,084  manager.py: close_all           All WebSocket connections closed
23:47:00,084  manager.py: shutdown            TrainingLifecycleManager shut down
23:47:00,084  app.py: lifespan                JuniperCascor API shutting down
```

That is the **complete FastAPI lifespan shutdown**, in ~4 ms. Not a crash, not a signal death.

**The control is what makes this conclusive.** The *next* service session (2026-08-25
05:16→05:22) ran the byte-identical shutdown sequence — and produced **no leak**, because it had
no training in progress (its log contains only WebSocket pings). Same shutdown path, training
absent, no residue. Training present, residue.

Two other hypotheses are eliminated outright:

- **OOM: no.** The only journal hits since 08-17 are GNOME system-monitor icon-load errors that
  merely contain the string `oom_reaper`. Zero real kills.
- **Missing cleanup path: no.** `atexit.register(self._cleanup_shared_memory)` is registered, and
  §3 shows the deferred-unlink logic is correct.

### 6.2 The mechanism

1. `util/juniper_chop_all.bash` sends **SIGTERM**, waits `SIGTERM_TIMEOUT` (**default 15 s**),
   then escalates to **SIGKILL** (its lines 184-214).
2. uvicorn runs the lifespan shutdown — the block above — and it completes in milliseconds.
3. `TrainingLifecycleManager.shutdown()` does set the stop flag, but **does not wait for training
   to unwind**:

   ```python
   self._stop_event.set()
   ...
   self._executor.shutdown(wait=False, cancel_futures=True)
   self.logger.info("TrainingLifecycleManager shut down")
   ```

   `wait=False` returns immediately, and `cancel_futures=True` cancels only *queued* futures —
   never the one already running. So the reassuring "shut down" line is emitted while training
   may still be live.
4. Training therefore has to notice `_stop_event` on its own. The mechanism for that exists —
   `TrainingInterrupted` is raised from the training-loop callback (`manager.py:209`) — but
   `train_output_layer`'s loop is a bare `for epoch in range(epochs):` with **no stop check**,
   and `cascade_correlation.py` contains **zero** references to `_stop_event`. The only hook is
   the throttled `on_epoch_callback`, fired every 25 epochs.
5. Whatever keeps the interpreter alive past the lifespan — the candidate worker pool and its
   forkserver children are the documented suspect (`_release_candidate_worker_pool` already warns
   "forkserver children may survive this run") — outlasts the 15 s window.
6. **SIGKILL.** `atexit` never runs, so the block in `_pending_shm_unlinks` and the pool's nine
   semaphores survive.

**How we know it was SIGKILLed rather than exiting cleanly:** the residue itself. A normal exit
after that lifespan would have run `atexit` and unlinked everything. It did not, so the
interpreter never reached exit. That is a deduction from the evidence, not a directly observed
signal — the signal itself is not logged anywhere.

### 6.3 ⚠ The same root cause produced cohort B

This is the part worth carrying. **Cohort B — the 273 truncated snapshot writes, the archive's
only irrecoverable loss — is what a SIGKILL during active training looks like on the write path.**
`train_output_layer` calls `create_snapshot()` unconditionally, so a service killed mid-training
is killed mid-write.

juniper-cascor#561 made the writes atomic, which is why cohort B has stopped growing and sits at
exactly 273 across every rebuild. But **#561 fixed the symptom, not the cause**: the kill that
truncated those files still happens, roughly once a day, and `/dev/shm` is where it now shows up
instead.

### 6.4 What to fix, in order

1. **`shutdown()` should wait, bounded.** `wait=False` is the defect: it makes the shutdown log
   line a lie and guarantees the 15 s escalation whenever training is live. A bounded join
   (a few seconds, well inside `SIGTERM_TIMEOUT`) would let the existing `TrainingInterrupted`
   path do its job.
2. **Give `train_output_layer` a stop check.** One `if` at the top of the epoch loop, against a
   flag the lifecycle already sets, removes the dependency on a callback that fires only every
   25 epochs and whose return value is discarded.
3. **Only then consider raising `SIGTERM_TIMEOUT`** — raising it first would merely lengthen every
   stop without fixing anything.

None of this is implemented here; this document is the diagnosis.

---

## 7. Reproducing

```bash
# The visible Juniper leak — du, never df (see 1.1)
ls -1 /dev/shm | grep -c '^juniper_train_'
du -ch /dev/shm/juniper_train_* | tail -1
ls -1 /dev/shm | grep -c '^sem.mp-'

# Orphan check: expect 0 for the leaked segments
find /proc -maxdepth 3 -path '*/fd/*' -lname '/dev/shm/juniper_train_*' 2>/dev/null | wc -l

# Where the 31 MB df/du gap actually lives (Chromium + live-service torch), NOT Juniper
find /proc -maxdepth 3 -path '*/fd/*' -lname '/dev/shm/*' -printf '%l\n' 2>/dev/null \
  | sed 's/ (deleted)//' | sort | uniq -c | sort -rn | head
```

The event table of §2 is reproduced by grouping `/dev/shm` entries on mtime-to-the-minute and
counting the two prefixes separately.
