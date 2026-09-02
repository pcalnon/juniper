# Logging redesign — design of record

**Project**: Juniper
**Sub-Project**: juniper-cascor (`src/log_config/logger/logger.py`)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-29
**Status**: DESIGN — **SUPERSEDED IN PART 2026-09-02**; owner-timed; scope owner-raised on [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)
**Measured at**: cascor `67d7ea35`, 32 worker profiles per corpus
**Evidence**: `juniper-ml/reports/perf-lane-post-fix-2026-08-26/worker_profile_*`

> **RECONCILED 2026-09-02.** [cascor#598](https://github.com/pcalnon/juniper-cascor/pull/598) shipped
> the top two items of §5's revised order, and a re-derivation from the code found several claims here
> that were wrong when written. **Read
> [`JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md)
> before acting on any section below**; the plan of record is now
> [`JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md).
> Corrections are marked inline as **CORRECTION 2026-09-02**. The load-bearing ones: D-2 reasons about
> `fork` and the pool is **forkserver**; §6's mirroring constraint is **inverted** for the one file a
> redesign touches; and D-1's premise — that the level filter is a single consistent gate — is false,
> because the guard predicate and the emit filter read **disjoint state**.

---

## 1. Why now

[cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563) removed `inspect.getmodule`'s
`sys.modules` scan from the per-record path — the `inspect` family fell from **52.17 % to 0.88 %**
of candidate-worker self time, and total worker self time from **3,994 s to 85 s**. That fix is
banked and this redesign must not be justified by it.

What the same profile shows about *what is left* is the case for #573:

| file | share of post-#563 worker self time |
| --- | --- |
| `logger/logger.py` | **18.00 %** (15.29 s) |
| `torch/_tensor_str.py` | 10.38 % (8.82 s) |
| `torch/_tensor.py` (essentially all `__format__`) | 5.21 % (4.43 s) |

Roughly **a third of what remains after the big fix is logging** — the logger itself plus tensor
formatting driven by f-strings in log messages. `Tensor.__format__` is called **1,813,318** times
per corpus, and *identically on both arms* (`1813318/1813318` pre- and post-#563), so #563 changed
the `inspect` storm and nothing about the formatting workload.

This is not a micro-optimisation argument. §2 shows the level filter does not work — the cost is
paid for records that are then discarded.

## 2. The findings the design must answer

All line numbers are at `67d7ea35`; anchor on the quoted text, not the number
(`_add_best_candidate` moved five times in one arc — 2026-08-24 handoff §5.5).

### F-1 — the level filter cannot prevent the work, because arguments are evaluated first

Every public method has the shape (`logger.py:506` and its siblings through `:562`):

```python
cls._log_at_level(frame=cls._frm(), tsp=cls._tsp(), level=cls._level_trace, message=message, args=args or None)
```

with `_frm = currentframe` and `_tsp = datetime.datetime.now` (`logger.py:130-131`). Python
evaluates arguments **before** the call, so `currentframe()` and `datetime.now()` run on every
`logger.trace(...)` in a hot loop **even when TRACE is filtered out**. `_log_at_level`'s
`_filter_by_level` guard is downstream of the cost it is supposed to avoid.

The same applies, far more expensively, to the message itself. Call sites are f-strings:

```python
self.logger.verbose(f"CandidateUnit: _initialize_randomness: Random seed set to: {seed}")
```

The f-string — including `Tensor.__format__` on any tensor interpolated into it — is fully
evaluated at the call site. A lazy path exists (`logger.py:472`, *"Lazy formatting: only
interpolate %s args when the message passes the level filter"*, `if args: message = message % args`)
but essentially no call site uses it. **The mechanism is present and unused.** That is the single
highest-value finding here, and it explains the 1.8 M `__format__` calls surviving #563.

### F-2 — the log file is opened per record

```python
with open(cls._logging_file, "a") as f:
    f.write(_line)
```

(`logger.py:478`, and again at `:495` on the `FileNotFoundError` retry.) Open + write + close, three
syscalls per record, on every record that passes the filter. This is the same class of per-record
cost #563 removed from the `inspect` path and it should not survive a redesign — the 2026-08-24
handoff §4.13 says exactly that.

The `FileNotFoundError` retry around it is *correct and load-bearing* (a fresh checkout or
`git worktree add` has no `logs/`, and `JUNIPER_CASCOR_LOG_DIR` makes a missing directory a
first-class case). Any redesign must preserve create-on-demand, not delete it along with the
per-record `open`.

### F-3 — stdout is written unconditionally

```python
print(f"+{_console_message(frame, tsp, level, message)}")
```

(`logger.py:475`.) Once a record passes the level filter it *always* goes to stdout. There is no
console sink to disable independently of the file sink. Two consequences: local pytest summaries
are swallowed (2026-08-24 handoff §6), and any consumer parsing this process's stdout gets log
records interleaved with its data — which is why several ad-hoc runners redirect stdout wholesale
and read the log file instead.

### F-4 — per-record closure construction and repeated level-name validation

`_log_at_level` builds two formatter closures per record:

```python
_console_message = cls._logging_message(cls._formatter_string_console, cls._console_dict)
_file_message    = cls._logging_message(cls._formatter_string_file, cls._file_dict)
```

and the level machinery re-validates level *names* as strings on the hot path —
`_is_valid_level_name` is **2.66 %** of worker self time on its own (`logger.py:329`, called from
`:326`, `:391`, `:401`, `:422`), with `_log_at_level` a further **2.49 %**. Levels are a closed set
known at import; resolving them to integers once and comparing integers is the standard shape.

## 3. Scope as the owner raised it (#573)

1. A clean stream to stdout/stderr.
2. Richer sinks — formatted, colourised file output.
3. **Per-logger** levels, settable via config file *and* environment variable.
4. Possibly streaming to an ELK/Kibana backend.

§2's findings are additive to that scope, not a replacement for it: (1) and (2) are F-3, and (3)
is where F-1's guard naturally lives.

## 4. Design

### D-1 — make the level check precede all cost (answers F-1)

Two layers, both needed:

> **CORRECTION 2026-09-02 — the predicate exists, and it does not agree with the filter.**
> `Logger.isEnabledFor` has existed since PR #116 (`logger.py:1027`) and is already used at 8 sites in
> `candidate_unit.py`. But it reads `_log_level` while `_log_at_level`'s filter reads
> `_level_logger_config`/`_level_logger_name`, and `set_level()` writes only the former — so a guard
> can be **open on records the emitter discards**. Measured, not read:
> `juniper-ml/util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py`. Four of the eight deployed
> guards also pass wrong integers — two live-wrong (`level=5 # TRACE`, where 5 is VERBOSE) and two
> wrong-but-inert (`level=8 # VERBOSE`, 8 being unregistered). **The state split must be fixed
> before this design's guard idiom can be recommended**; symbolic constants alone are not sufficient.
> See the reconciliation's N-3.

**Cheap gate at the call site.** Expose an `is_enabled_for(level)` predicate and use it for hot-path
records that interpolate anything expensive:

```python
if self.logger.is_enabled_for(TRACE):
    self.logger.trace(f"... {tensor} ...")
```

**Lazy arguments as the default idiom.** Migrate hot call sites from f-strings to the existing
`%`-args path so interpolation happens only after the filter passes. The path already exists
(`logger.py:472`); this is a call-site migration, not new machinery.

`frame` and `tsp` must stop being eagerly-evaluated arguments. Capture them **inside**
`_log_at_level`, after the filter — `currentframe()` there can walk one extra frame, and the
timestamp of a record that will be discarded is not needed at all.

*Migration note*: there are many call sites. They do not all need to change. Convert the hot ones —
anything inside candidate training, the per-epoch output loop, or a per-record path — and leave
cold start-up/config logging as f-strings. A sweep that changes every call site is a large diff with
most of its risk in the parts that do not matter. Grep for tensor interpolation first: those are the
1.8 M calls.

### D-2 — persistent, level-routed sinks (answers F-2, F-3, part of scope 1/2)

A sink abstraction with, at minimum, a console sink and a rotating file sink:

- The file sink holds an **open handle** for the process lifetime, **flushing per record**
  (owner decision 2), instead of opening per record. Create-on-demand from F-2 moves into sink
  initialisation, preserving the `JUNIPER_CASCOR_LOG_DIR` and fresh-worktree cases.
- The console sink is **independently configurable and independently disableable**, and **stays on
  stdout** (owner decision 4). It gains a disable switch, which the current unconditional `print()`
  lacks; the swallowed-pytest problem is handled separately (§7.1), not by moving the stream.
- Colourisation belongs to the console sink only, gated on a TTY check, never applied to the file
  sink (colour escapes in `juniper_cascor.log` would break every existing grep-based analysis and
  every log-parsing tool in `util/ad-hoc/`).

**Forked-worker constraint — this is the part most likely to go wrong.** Candidate workers are
forked from the parent. An inherited open file handle shared across processes gives interleaved and
potentially torn writes.

> **CORRECTION 2026-09-02 — the premise is wrong.** The candidate pool uses **`forkserver`**, not
> `fork` (`cascade_correlation.py:1103-1109`; the in-source comment even records the earlier version
> of this same mistake: *"Issue #569: an earlier comment here said the code used the 'fork' context —
> it never did on this path"*). A handle held by the **parent** is therefore not inherited by a
> candidate worker at all. The real hazard is the mirror image: `cascade_correlation` is in the
> forkserver **preload** list, so the forkserver process imports the logging tree, and a handle opened
> at import or forkserver time **is** inherited by every child with a shared offset. Laziness stays
> load-bearing — relative to forkserver start, not to fork. See the reconciliation's N-2.

**Owner decision 3: per-process handle**, opened lazily on first write after fork — the simplest
option, and the only one that keeps a single log file and so keeps every existing log-reading tool
working unchanged. Taken as **provisional**: if it proves untenable, the fallbacks are one file per
PID (safest, but changes the artifact layout that the experiment harness, the census tooling and the
snapshot pipeline all depend on) or a queue plus a single writer thread in the parent (cleanest, most
machinery, and the queue must not become a fork-safety hazard of its own — screen it with
`util/ad-hoc/2026-08-26_fork_safety_import_surface.py`).

Two things must be **verified rather than assumed** before this is considered settled:

1. **A handle inherited across `fork` shares its file offset.** Opening in append mode (`O_APPEND`)
   makes each write seek-to-end atomically, which is what makes concurrent appenders survivable at
   all; a handle opened *before* the fork and written by both parent and child without `O_APPEND`
   will corrupt. "Opened lazily on first write after fork" is what avoids this — the laziness is
   load-bearing, not an optimisation.
2. **Atomicity has a size limit.** Appends larger than the platform's atomic-write guarantee can
   still tear under concurrency. cascor log records embed formatted tensors and can be long. The
   §5 measurement run must be checked for torn or interleaved records in the worker log.

### D-3 — per-logger levels from config and environment (scope 3)

Precedence, most specific wins: per-logger env var → global env var (`CASCOR_LOG_LEVEL`, already
honoured) → per-logger config entry → global config → default. Resolve names to integers **once**
at configuration time and store the integer on the logger, which retires the per-record
`_is_valid_level_name` cost in F-4 as a side effect rather than as a separate optimisation.

> **CORRECTION 2026-09-02 — two things.** (1) The canonical variable is
> **`JUNIPER_CASCOR_LOG_LEVEL`**; `CASCOR_LOG_LEVEL` is deprecated, raises a `DeprecationWarning`, and
> loses to the prefixed form with a split-config stderr warning (CFG-05, `constants.py:638-658`).
> (2) **A prerequisite this section does not name**: there are currently **two** configured-level
> states — `isEnabledFor` reads `_log_level`, `_log_at_level`'s filter reads
> `_level_logger_config`/`_level_logger_name`, and `set_level()` writes only the first — so a
> precedence chain built on top of them would move one gate and not the other. And an unknown level
> name cannot be made to fail loudly while `is_valid_level` returns `True` for every input
> (`logger.py:341`, the `level == level` typo). See the reconciliation's N-3 and N-3a.

### D-4 — ELK/Kibana export (scope 4) — design the seam, defer the sink

Structured JSON output is the prerequisite and is worth doing regardless: one JSON object per
record with stable field names. Ship that as a sink option; leave the actual shipper (filebeat
sidecar, HTTP appender, or a `juniper-observability` helper) out of the first change. A network sink
on the per-record path in a forked worker is exactly where an unbounded queue or a blocking socket
would cost more than the 18 % this design is trying to recover.

**Owner decision 6: the JSON sink goes through `juniper-observability`**, which already owns
structured-JSON logging for the service tier — one implementation, not a cascor-local second one.

> **CORRECTION 2026-09-02 — a second implementation already exists, deliberately.**
> `src/api/observability.py:75-119` is a **local fork** of
> `juniper_observability.configure_logging`, adding a `RotatingFileHandler` and a cascor-aware log
> directory, with its rationale in-source at `:81-83`. cascor already imports `JuniperJsonFormatter`
> (`:36`) and already emits JSON on the API tier (`:102`), so the dependency is present today and the
> "hard dependency in the worker import path" framing below applies only to putting it on **Path A**.
> The decision to take is therefore not "avoid a fork" but **"reconcile the one we have"** — and note
> that upstreaming it would delete the only rotator, since the shared library has no file sink.
Two consequences to plan for: cascor gains a hard dependency on `juniper-observability` in the
*worker* import path, so the addition must be screened for fork-safety
(`util/ad-hoc/2026-08-26_fork_safety_import_surface.py`) and for its effect on the worker module
count — [cascor#570](https://github.com/pcalnon/juniper-cascor/issues/570) has just been closed at
1,166 modules per worker and this design should not silently undo that. And the shared package's
minimum pin moves, which is a fleet-wide change rather than a cascor-local one.

## 5. What this is expected to be worth — **MEASURED 2026-08-29; the priority order below is superseded**

> **Result**: the 1.81 M `Tensor.__format__` calls come from ONE line, at **INFO** — an *enabled*
> level — so guards and lazy args cannot recover them. The largest recoverable item is instead
> `_filter_by_level` at **11.19 s / 13.2 %** of worker self time, paid on all 646,016 calls of which
> **91 % are discarded**. Revised priority: (1) stop formatting whole tensors into the INFO line,
> ~33 %; (2) cheap integer level compare, 13.2 %; (3) move frame/tsp inside, 1.0 %; (4) call-site
> migration, small. **The call-site migration drops from headline to last.** Full decomposition:
> [`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md) §3.

Honest accounting, since #563's number is banked and must not be double-counted:

- **F-1 is the large one and it is not yet sized.** 18 % `logger.py` + ~15 % tensor formatting is
  the *ceiling*, not the recovery: some of those records are at levels that are enabled and would
  still be emitted. The recoverable fraction is the share of that work done for records that are
  **discarded**, and nothing measured to date separates the two.
- **F-2 and F-4 are bounded and real** — three syscalls per emitted record, two closures per
  emitted record, and 2.66 % of self time in level-name validation.
- **F-3 is a correctness/ergonomics fix**, not a performance one.

  > **CORRECTION 2026-09-02 — under the juniper-ml launchers it is a 1.89× write amplification.**
  > `juniper-ml/util/experiment_stack.bash:685`, `util/isolated_stack.bash:297` and
  > `util/juniper_plant_all.bash:126` redirect the service's stdout into the log directory, so the
  > unconditional `print()` puts every record on disk a second time in a second format. Measured in
  > one run: 77,790 duplicate records / 11.89 MB against a 27.07 MB total — **44 % of the run's log
  > bytes**. This does **not** apply to the deployed service (systemd inherits `journal`; the Docker
  > stanza sets no `logging:` override), so the claim holds for the harness, which is where the
  > evidence corpus is produced. See the reconciliation's N-1.

**Measure before building (§7 Q1).** One profiled cap-4 cell with all logging disabled gives the
true ceiling; the same cell at production level gives the enabled-record floor. The gap between them
is what D-1 can actually recover. That is one cell on the harness already used for the tensor probe,
and it should precede the implementation rather than justify it retroactively.

## 6. Constraints and hazards

- **`log_config` is mirrored into `juniper-cascor-model`.** Edits to `src/log_config/...` must be
  mirrored or `test_drift` fails, and pre-commit's black hook covers only `src/`, so it reformats
  one side of a byte-gated pair — re-sync the model copy after running pre-commit.

  > **CORRECTION 2026-09-02 — inverted for the file that matters.** The gate is **file-level**.
  > `log_config/logger/logger.py` is on `_INTENTIONAL_DIVERGENCE`
  > (`juniper-cascor-model/tests/test_drift.py:31`) and must **NOT** be mirrored — a reverse guard,
  > `test_intentional_divergences_actually_differ` (`:104-117`), **fails if the two copies become
  > identical**. #598 hit this and reverted. The other three `log_config` files, and all of
  > `candidate_unit/`, `utils/` and `cascor_constants/`, **are** byte-gated and must be mirrored. The
  > black-hook half of this bullet is entirely correct and survives. See the reconciliation's N-5.

- **Every log-parsing tool anchors on the current text format.** The `+`-prefix, the
  `[file.py: func:LINE] (timestamp) [LEVEL] message` shape, and the `juniper_cascor.log` filename are
  depended on by the experiment harness, `util/ad-hoc/2026-08-26_g4_post_fix_analysis.py`, the
  census tooling and the snapshot pipeline. **A format change is a breaking change to the evidence
  corpus.** Either hold the human-readable format byte-stable and add JSON as a *second* sink, or
  budget for updating every consumer. Recommended: the former.

  > **CORRECTION 2026-09-02 — narrow this, do not delete it.** The conclusion and the recommendation
  > are right; the element list is not. **Nothing parses `[file.py: func:LINE]`** — anchoring on it is
  > a *documented prohibition* ("methodology rule 5") in four juniper-ml scripts after a 2026-08-20
  > incident, and #573's own body states the rule. What **is** load-bearing: the `+` sentinel (2
  > scripts split worker from parent on it), Path A's **absence of milliseconds** (the same 2 scripts
  > use it as the same discriminator — so a "richer sink" adding sub-second precision breaks them
  > silently), the `(YYYY-MM-DD HH:MM:SS)` timestamp (6 scripts, 3 of which cannot read a `,millis`
  > form and fail by **silent skip**), anchored **message text** (~17 scripts), and the
  > `juniper_cascor.log*` filename/rotation scheme. All of this breakage is **cross-repo — cascor's
  > CI stays green**. See the reconciliation's N-4.
- **Do not fold this into a hot-path bugfix.** #573 was deliberately kept out of #563 so neither
  justifies the other; keep that separation.
- **Log rotation already happens** (`juniper_cascor.log.1` exists in service runs) and any analysis
  that reads only `juniper_cascor.log` silently misses records — a rotating file sink must keep that
  behaviour predictable and documented, since it has already caused one truncated analysis.

  > **CORRECTION 2026-09-02 — the mechanism, and it is worse than "predictable".** The rotator is
  > **Path C**: `api/observability.py:110-115` attaches a `RotatingFileHandler` (10 MB, 5 backups) to
  > **the same `juniper_cascor.log`** that Path A appends to per record and Path B holds open. Path A
  > survives a rollover only because it re-opens by name each record; **Path B's held descriptor
  > follows the renamed inode and keeps writing into `.1`**. Rollover fires only when Path C emits —
  > ~21 records per run — so it checks the size of a file being inflated out of band, which is why
  > rotated files run to 15 MB, 41 MB and 129 MB against a 10 MB threshold. See the reconciliation's
  > N-9. **A persistent-handle redesign acquires this defect for Path A**, so rotation must be given a
  > single owner *before* the handle is made persistent.

## 7. Owner decisions — SETTLED 2026-08-29

All six questions answered by the owner. Recorded here as the design's binding constraints.

| # | question | **decision** |
| --- | --- | --- |
| 1 | Measure the discarded-record share first? | **YES — measure before building.** §5's number stays a ceiling until then. This is now a gate on starting implementation, not a nice-to-have. |
| 2 | Flush per record or on an interval? | **Per record.** A complete log for a crashed run outweighs the throughput; a truncated log is how several analyses in this arc went wrong. |
| 3 | Forked-worker file strategy | **Per-process file handle**, opened lazily on first write after fork. Explicitly provisional — re-evaluate if it proves untenable. Per-PID files and the parent writer thread stay on the table as fallbacks. |
| 4 | Console default stderr or stdout? | **Keep stdout.** The swallowed-pytest problem is not to be fixed by relocating the stream — it gets its own rigorous investigation (see F-3a below). Provisional; revisit if it becomes problematic. |
| 5 | Call-site migration scope | **Deferred pending analysis** — written up separately in [`JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md`](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md). Headline: 1,885 call sites, 879 f-strings, but 36 % of sites and essentially all tensor formatting sit in two files, so hot-path-only is a ~150-site diff. Recommends guards + `%`-args on the hot path, explicitly **not** a full sweep. Still owner's call. |
| 6 | Structured JSON via `juniper-observability`? | **Yes — through `juniper-observability`.** No second implementation local to cascor. |

Consequences of (2) + (3) together: per-record flush on a per-process handle means each forked
worker holds its own descriptor to the same file and flushes every record. Interleaving is then at
record granularity rather than byte granularity for writes under `PIPE_BUF`, but **this is an
assumption that must be tested, not assumed** — a write larger than the atomic-append guarantee can
still tear. The §5 measurement run should be used to check for torn or interleaved records in the
worker log before the design is considered settled.

Consequence of (4): stdout stays the log stream, so the existing runner convention of redirecting
stdout wholesale and reading the log file remains correct and must keep working.

### 7.1 Deferred to its own document — the swallowed-pytest problem (F-3a)

Decision 4 keeps stdout *and* declines to treat relocation as the fix, which means the underlying
cause is still unexplained. It is currently attributed to the unconditional `print()` at
`logger.py:475`, but that attribution has never been tested — pytest captures stdout by default and
restores it per test, so "the logger prints to stdout" is a plausible story rather than a
demonstrated mechanism. Worth a bounded investigation of its own: reproduce the disappearance,
identify whether it is pytest's capture, a `capsys`/`-s` interaction, the logger's `print`, or
stream buffering, and only then propose a fix. Explicitly NOT a blocker on the rest of this design.

## 8. References

- [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) — the issue, owner-raised scope
- [cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563) — the `inspect.getmodule` fix; its number is banked, not available to this design
- `reports/perf-lane-post-fix-2026-08-26/worker_profile_inspect_share_pre563_vs_at67d7ea35.txt` — the shares quoted in §1
- `reports/perf-lane-post-fix-2026-08-26/worker_profile_diff_pre563_vs_at67d7ea35.txt` — the 1,813,318 `__format__` calls, identical on both arms
- 2026-08-24 handoff §4.13 — the original framing (per-record `open`, unconditional `print`)
- `notes/JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md` §8 — #563's fix design
