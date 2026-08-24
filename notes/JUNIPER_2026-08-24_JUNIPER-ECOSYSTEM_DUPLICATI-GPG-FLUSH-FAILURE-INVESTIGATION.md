# Duplicati GPGFlushError — Mechanism Investigation

**Project**: Juniper — Backup Infrastructure
**Author**: Paul Calnon (investigation executed by Claude Code session "backup sys work")
**Date**: 2026-08-24
**Status**: Mechanism pinned (source + forensics + controlled experiments); in-vivo macro reproduction IN FLIGHT (§7)
**Prior context**: [`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md) · handoff `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-24_duplicati-gpg-failure-and-scheduled-lane.md`

---

## 1. Executive summary

The 2026-08-23 fresh-backup run 2 (`rc=100`, `CryptographicException: Failure while
invoking GnuPG, program won't flush output`) died because Duplicati's GPG encryption
pipeline gives a pump thread a **hardcoded 5000 ms** to finish draining gpg's output
into the ciphertext file — *including that file's close-flush* — after gpg's stdin
closes. That tail normally takes **milliseconds**; under **collapsed effective
memory** (the failing day's swap storm), page-cache writeback throttling stretches it
toward and past 5 s. Measured on this machine under a bounded emulation of that
condition, the tail reaches **4.82 s (96.4% of the bound)**, with regime maxima
ordered monotonically across five load regimes. When the stall bites, it is **device/host
global**, so *many* concurrently-encrypting volumes miss the bound together — log
forensics show **at least six independent misses** in the one failing episode. A miss
is **unretryable by construction** (Duplicati retries by re-awaiting a cached,
permanently-faulted task — gpg is never re-invoked), and the backend queue is then
deliberately killed: one multi-second I/O stall fails the entire backup.

**gpg itself is innocent.** In the experiments, the near-miss tails occur *after* gpg
has already exited successfully (gpg gone in 0.2–0.7 s; the pump's final `write()`/
`close()` into the throttled page cache consumes the rest). The name "GPG failure" is
a misattribution baked into Duplicati's error string.

Nothing was changed: per the standing directive, this investigation reproduced and
pinned the mechanism only. Fix candidates and their tradeoffs are catalogued in §9
for a decision; none has been applied.

## 2. The failing event, re-read (run 2, 2026-08-23 22:51:26 → 23:48:24)

Log: `~/.local/state/duplicati/backup-20260823-225125.log`. Corrections to the
handoff's §1a reading, established by adversarial log forensics and verified in
source:

- **It was a correlated multi-pipeline episode, not one victim.** The five
  `UnobservedTaskException` blocks are **five separately-finalized tasks** (one
  UnobservedTaskException event each; distinctness of the underlying exception
  objects follows from .NET finalizer semantics): four are the pre-started
  encryption tasks of queued volumes that were never awaited (their stacks never
  gained `ExecuteAsync` frames), one is the terminated active upload of log line
  517 (frames through `ExecuteWithRetry`, not through `ReclaimCompletedTasks`), and
  the stack of the exception that killed the queue (line 511, with
  `ReclaimCompletedTasks`) matches **none** of them. Total independent
  `Join(5000)` misses evidenced: **≥ 6**.
- **The run died mid-flight**, with ~50 GiB / ~352,000 files still to examine at the
  first error — not in a quiet tail.
- **Retries happened and were invisible** — a derivation, not an observation: the
  `ExecuteWithRetry` frames in the fatal stack prove the retry path ran; source
  defaults (`number-of-retries=5`, `retry-delay=10s`, neither overridden by the
  job) give 6 attempts over ~50 s; retry lines are emitted at level `Retry`, below
  the default console level `Warning`, hence absent from this log.
- **"27.3G memory peak" is cgroup accounting** (page cache included), not a managed
  heap measurement.
- Run 2 ran **with the ext4 tempdir fix in place** (`/media/pcalnon/temp_backups/_duplicati_tmp`)
  — tmpfs staging is definitively not required for the failure. But temp staging, the
  destination, and the `/home` source all share **one rotational disk (sdc)**, and the
  same-day swap storm's residue was still present (14.4 GB swap in use a day later).

## 3. Source anatomy (Duplicati 2.3.0.4, tag `v2.3.0.4_stable_2026-07-09`)

Fetched sources verified byte-identical to the installed version's tag.

**The bound** — `Duplicati/Library/Encryption/GPGStreamWrapper.cs:48-58`:

```csharp
m_basestream.Close();          // closes gpg STDIN -> EOF
if (!m_t.Join(5000))           // pump thread: gpg stdout -> ciphertext FileStream
    throw ... GPGFlushError    //   "program won't flush output"   <- run 2's error
if (!m_p.WaitForExit(5000))
    throw ... GPGTerminateError
```

The throw site is unique in the codebase; the string maps uniquely
(`Strings.cs:60`). The pump thread's last act is `Close()` on the ciphertext
`FileStream` (`GPGEncryption.cs:253-259`), so the 5 s budget **includes the
final file writes and close-flush** — the disk-facing half. Backpressure
(64 KiB pipes, 64 KiB copy buffer — verified `SystemContextSettings.Buffersize`
default — 4 KiB FileStream buffer) bounds in-flight data to ~a few hundred KiB:
bulk throughput structurally cannot explain a miss; only a stall can.

**The invocation** — `gpg --batch --passphrase-fd 0 --symmetric`, passphrase as the
first stdin line, a hardcoded `Thread.Sleep(1000)` per spawn, stderr undrained until
exit (`GPGEncryption.cs:194-247`). No compression override — and because Duplicati
passes no `--no-options`, **the user's `~/.gnupg/gpg.conf` governs**: on this host it
sets `compress-algo ZLIB` + `cipher-algo AES256`, so gpg deflates already-zip-compressed
volume data. Measured cost per 500 MiB volume: **~17 s of gpg CPU (17.4 s wall) vs
~1.6 s CPU (1.4 s wall) with `-z 0`** — a 10–12× tax. (The predecessor probe's
403 MiB/s figure came from passing `--compress-algo none --cipher-algo AES256` —
options the real pipeline does not use.)

**Unbounded encryption concurrency** — `BackendManager.cs:316`:
`op.StartEncryptionAndHashing()` runs **before** `QueueTask(op)`. Encryption
pre-starts for every queued volume; concurrent gpg count is bounded by queue depth,
not by `asynchronous-upload-limit` (default 4). This is how ≥ 6 pipelines could miss
simultaneously.

**Vacuous retry** — `BackendManager.PutOperation.cs:125-129, 205-209`: the encryption
task is one-shot (`"Encryption already started"`) and cached; the retry path's own
comment says *"On retry attempts, we get the same value, without recalculating"*. A
faulted task stays faulted; **gpg is never re-invoked**. After 6 instant rethrows,
`Handler.cs:480-486` deliberately kills the whole backend queue
(`"Error in handler"` → `"Terminating 3 active uploads"`), and every later `PutAsync`
rethrows — surfacing as rc=100 at 23:48:24.

**Upstream status**: `GPGStreamWrapper.cs` last substantively changed **2019**;
unchanged on master as of 2026-04. Upgrading Duplicati does not remove the bound.

## 4. Hypothesis campaign (micro harness)

Harness: [`util/ad-hoc/gpg_tail_latency.py`](../util/ad-hoc/gpg_tail_latency.py) —
replicates the pipeline shape exactly (passphrase line → 1 s sleep → dedicated pump
thread → 64 KiB chunks → stdin close → measured tails), adversarially validated
(three metric defects and two hang-path bugs found and fixed; the shape itself held).
`TAIL_JOIN` = stdin-close → pump-drain-and-close-complete = the `Join(5000)` analog.

Pre-registered protocol: 3 pipelines × 12 trials = 36 tails per regime; only
`TAIL_JOIN > 5 s` counts as the failure analog; a clean sweep means "not easily
reproducible under this regime" (95% upper bound ≈ 8%/tail, rule-of-three; the three
tails per trial share ambient load, so full independence is an approximation), never
disconfirmation.

| regime | conditions | max TAIL_JOIN | verdict |
|---|---|---|---|
| T0 | idle, nice 0 † | **0.005 s** | tail work is ms-scale when schedulable |
| T1 | nice-10 pipeline vs 16 nice-0 CPU burners (feeds stretched 9×) † | 0.110 s | **pure CPU starvation ruled out** |
| T2 | + writeback pressure + ionice BE-7 † | 0.727 s | direction confirmed (gpg observed D-state), magnitude insufficient |
| T3 | memory-capped cgroup `MemoryMax=2G/High=1.5G`, sustained-dirty writer, unit-level nice 10, live Recreate ambient | **4.367 s** | 0/36 over, but the right tail reaches 87% of the bound |
| T4 | same, cap tightened to `1G/768M` | **4.820 s** | 0/36 over; **96.4% of the bound** |

† T0–T2 ran foreground in-session; their values are transcript-only (no archived
log). **Provenance for T3/T4**: the caps, nice-10, and IO class were applied at the
**systemd unit level** and are therefore *not visible* in the logs' own regime lines
(which correctly read `nice=0` — the harness flag was deliberately unset to avoid
double-nicing). The exact `systemd-run` invocations and the observed cap enforcement
are archived at `/media/pcalnon/temp_backups/_gpg_repro/micro/LAUNCH_COMMANDS.txt`.
The T3→T4 maxima are ordered but overlap in their right tails (T4's second-highest
4.338 s vs T3's 4.168 s); the dose–response weight is carried by the T2→T3 jump.

**The decisive discrimination** (T3 trial 7 pipe 0, trial 3 pipe 2): `TAIL_JOIN`
4.367 s / 4.168 s while gpg exited **0.202 s / 0.362 s** after stdin-close. The stall
is entirely the **pump's final writes + close-flush** under memory-pressure writeback
throttling, *after gpg finished successfully*. In Duplicati, this exact profile
crossing 5 s throws GPGFlushError over a dead, successful gpg.

**Why the cap regime**: dirty-writeback throttling thresholds scale with *available*
memory (10%/20% on this host ⇒ engagement only above ~15–20 GB dirty when healthy).
The failing day's swap storm collapsed availability host-wide; a memory-capped cgroup
reproduces the same collapsed-thresholds/reclaim-writeback condition, bounded and
safe. The real day was *harsher* than T4 in this dimension (host-global vs 1 GB
cgroup, plus 350k-file scan churn and the .NET runtime's own memory behavior on top).

**What the micro cannot test** (scope limits, per adversarial review): .NET-side
stalls (GC stop-the-world, thread-pool starvation) — possible *amplifiers*, no longer
*required* to explain the failure; and the exact post-storm host state, deliberately
not recreated on a live machine carrying the 59+ h archive Recreate.

## 5. Conclusion on mechanism

> Duplicati bounds the encrypt-side pump (gpg stdout → ciphertext file, including
> close-flush) with a hardcoded 5 s thread-join. On this machine that tail is
> milliseconds idle, degrades continuously under combined memory pressure +
> writeback contention on the shared spindle, and was measured to within 3.6% of
> the bound under a bounded emulation of the 2026-08-23 conditions — under which
> the stall is device/host-global, so many pre-started encryption pipelines
> (concurrency unbounded by design) miss together. The miss converts to a whole-run
> failure through a structurally vacuous retry path and a deliberate queue kill.
> gpg exits successfully underneath; the error string blames the wrong component.

Confidence: the bound, wiring, retry vacuity, queue kill, and ≥6-miss episode are
**certain** (source + log, independently verified). The writeback-under-memory-collapse
trigger is **strongly supported** (monotone dose–response to 96.4% of the bound with
the exact pump-side signature) and is the parsimonious explanation; crossing was not
observed in 72 synthetic tails, consistent with the real trigger state being harsher
than the bounded emulation.

## 6. Run 1 (the 17:15 hang) — related, still unpinned

The write path of the same pipeline has **no timeout at all** (the 5 s bound exists
only in `Dispose`); a writer-side stall hangs forever, idle, in pipe waits — matching
run 1's presentation (`anon_pipe_read`/`wait_for_partner`, fully idle from ~21:22).
Run 1 also ran under the *tmpfs* staging regime with 8.4 GB resident and swap at
17/20 GB — the harshest memory state of the day. "Same fragility, unbounded side" is
consistent with all evidence but remains a working hypothesis; it was not the
investigation's target and no stack dump exists (`yama.ptrace_scope` blocked
`eu-stack` without sudo).

## 7. In-vivo macro reproduction — IN FLIGHT

Harness: [`util/ad-hoc/duplicati_gpg_macro_repro.bash`](../util/ad-hoc/duplicati_gpg_macro_repro.bash)
— a full scratch backup (real source + options; throwaway destination/db/tempdir/
passphrase) with Verbose logging, a per-invocation gpg START/END logger (an END-less
START at crash time is positive evidence of an in-flight gpg), a 5 s system sampler,
and a free-space watchdog. Adversarially validated; seven material defects fixed
pre-launch (the worst: the wrapper's background job inherited stdin from `/dev/null`
— the run would have failed on volume 1 with the wrong error class; and the wrapper's
exit bookkeeping originally sat *inside* the 5 s window it instruments).

Launched 2026-08-24 04:37 as transient unit `gpg-macro-repro.service` with
`Nice=10 IOSchedulingClass=best-effort IOSchedulingPriority=7 MemoryHigh=6G
MemoryMax=10G RuntimeMaxSec=18000`; cap verified enforced from the host cgroup view.
Run dir: `/media/pcalnon/temp_backups/_gpg_repro/macro-20260824-043743/`.

**RESULT: to be appended when the run completes.**

Known instrument degradations for this run (found at launch, tolerable): the unit
runs in a cgroup namespace, so the in-script cgroup-relative PSI columns read zero
and the gpg cgroup filter degenerates to system-wide (no competing gpg workload
exists during the run; the micro harness had finished and the launcher guards
against concurrency).

## 8. Evidence inventory

| artifact | where |
|---|---|
| failing run 2 log | `~/.local/state/duplicati/backup-20260823-225125.log` (lines 5, 511-593, 797-840) |
| pinned sources at tag | scratchpad `duplicati-src/` — GPGStreamWrapper.cs, GPGEncryption.cs, BackendManager.cs, BackendManager.PutOperation.cs (+ Handler.cs, Options.cs, Strings.cs, EncryptionBase.cs via validators) |
| micro harness + logs | `util/ad-hoc/gpg_tail_latency.py`; `/media/pcalnon/temp_backups/_gpg_repro/micro/t3-run.log`, `t4-run.log` (T0-T2 ran foreground in-session, transcript-only) |
| T3/T4 launch provenance | `/media/pcalnon/temp_backups/_gpg_repro/micro/LAUNCH_COMMANDS.txt` — exact `systemd-run` invocations (unit-level caps/nice, invisible in the harness logs) + observed cap enforcement |
| macro harness + run | `util/ad-hoc/duplicati_gpg_macro_repro.bash`; `/media/pcalnon/temp_backups/_gpg_repro/macro-20260824-043743/` |
| validation | four adversarial validator reports (mechanism, harness fidelity, regime match, macro safety) — summarized in the session transcript; all material findings incorporated |

## 9. Fix candidates — FOR DECISION, none applied

Per the standing directive, nothing was changed. The candidates, with what the
mechanism analysis says about each:

1. **Switch the job to Duplicati's built-in AES module** (`--encryption-module=aes`).
   Bypasses `GPGStreamWrapper` — the 5 s bound, the 1 s per-spawn sleep, the external
   process, and the gpg.conf coupling all disappear. Strongest structural fix; changes
   the archive's encryption format (old volumes stay gpg — both passphrases already
   retained; a fresh set makes this clean).
2. **`--gpg-encryption-switches="--compress-algo none"`** (or `-z 0`). Removes the
   10–12× compression tax and shrinks every tail's work; does *not* remove the 5 s
   bound or the stall exposure of the final file writes. Cheap, compatible, partial.
3. **Reduce exposure width**: `--asynchronous-upload-limit=1` (or 2) shrinks the
   number of concurrently pre-started encryptions and thus the blast radius of one
   global stall — at some throughput cost. Note the pre-start-at-queue design means
   `--concurrency-max-threads` does not govern this.
4. **Upstream issue**: the 5 s hardcoded `Join`, the vacuous retry (cached faulted
   task), and the queue-wide kill are three separable upstream defects; the evidence
   package here (source cites + reproduction data) is filing-ready. Wrapper code
   unchanged since 2019, so no version upgrade helps meanwhile.
5. **Operational**: don't start backup runs in a memory-collapsed state. The tempdir
   fix already removed the biggest self-inflicted source (tmpfs staging); the runner
   could additionally check `MemAvailable`/swap before starting — a guard, not a fix.

These are not mutually exclusive; (1) or (2)+(3) both pair naturally with (4).

## 10. Method lessons (this arc's recurring failure shape)

- The predecessor's gpg probe was out of regime **twice** (idle, and
  `--compress-algo none` vs the real conf-driven ZLIB). Replicate the *invocation*,
  not the tool.
- An idle benchmark cannot close a load-dependent hypothesis; a **distribution's
  right tail** is the object of interest, not its mean.
- `strings` cannot find an integer literal: the "unknown bound" was `Join(5000)` all
  along — read the source at the installed tag.
- The instrument must not sit inside the window it measures (wrapper fd-close order;
  `t_eof` after `close()`).
- A background job in non-interactive bash gets stdin from `/dev/null` — a
  passphrase-fd pipeline dies instantly and looks like a different bug.
- Name-anchored process greps are fail-open (again — same class as the runner's
  guard-5 fix); scan `/proc/*/fd` write-handles instead.
- systemd user units may run in a **cgroup namespace**: `/proc/self/cgroup` reads
  `/`, and in-unit "cgroup-local" instruments silently read the wrong scope. Verify
  caps from the host view.
