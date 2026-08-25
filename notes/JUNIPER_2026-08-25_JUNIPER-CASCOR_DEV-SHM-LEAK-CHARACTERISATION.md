# `/dev/shm` leak — characterisation

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-25

**Status**: FINDINGS — measured, read-only. Nothing was unlinked or killed in producing this.

**Headline: the OPT-5 SharedMemory design is not defective, and the leak is ~371 KB.** What
`/dev/shm` is actually recording is something more useful than a resource problem — an
unintentional **ledger of hard-killed cascor training runs**, ten of them in eight days.

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
is the unavoidable residue of a hard kill.

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

**The signal.** Each leaked pair is a receipt for a cascor training process that was hard-killed:
**ten in eight days, ~1.25/day.** `/dev/shm` has been keeping this ledger by accident, and it is
the only place it is written down. Candidate killers already documented in this repo — the orphan
reaper (`util/reap_pytest_orphans.bash`, whose predicate catches healthy services), `KILL_WORKERS=1`,
and experiment timeouts — are exactly the sort of thing that produces this residue.

The actionable question is therefore **not** "how do we reclaim 371 KB" but **"why is roughly one
cascor run a day dying without a clean shutdown?"**

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

## 6. Reproducing

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
