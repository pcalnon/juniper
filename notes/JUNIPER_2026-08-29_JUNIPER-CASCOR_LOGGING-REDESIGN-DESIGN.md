# Logging redesign — design of record

**Project**: Juniper
**Sub-Project**: juniper-cascor (`src/log_config/logger/logger.py`)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-29
**Status**: DESIGN — owner-timed; scope was owner-raised on [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)
**Measured at**: cascor `67d7ea35`, 32 worker profiles per corpus
**Evidence**: `reports/perf-lane-post-fix-2026-08-26/worker_profile_*`

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

- The file sink holds an **open handle** for the process lifetime, flushing per record (or on an
  interval — see Q2), instead of opening per record. Create-on-demand from F-2 moves into sink
  initialisation, preserving the `JUNIPER_CASCOR_LOG_DIR` and fresh-worktree cases.
- The console sink is **independently configurable and independently disableable**, defaulting to
  stderr rather than stdout so a process's stdout stays a clean data channel.
- Colourisation belongs to the console sink only, gated on a TTY check, never applied to the file
  sink (colour escapes in `juniper_cascor.log` would break every existing grep-based analysis and
  every log-parsing tool in `util/ad-hoc/`).

**Forked-worker constraint — this is the part most likely to go wrong.** Candidate workers are
forked from the parent. An inherited open file handle shared across processes gives interleaved and
potentially torn writes. Options: per-process handle opened lazily on first write after fork
(simplest, keeps one file), one file per PID (safest, changes the artifact layout every log-reading
tool depends on), or a queue plus a single writer thread in the parent (cleanest, most machinery,
and the queue must not become a fork-safety hazard of its own — see
`util/ad-hoc/2026-08-26_fork_safety_import_surface.py`). **Q3.**

### D-3 — per-logger levels from config and environment (scope 3)

Precedence, most specific wins: per-logger env var → global env var (`CASCOR_LOG_LEVEL`, already
honoured) → per-logger config entry → global config → default. Resolve names to integers **once**
at configuration time and store the integer on the logger, which retires the per-record
`_is_valid_level_name` cost in F-4 as a side effect rather than as a separate optimisation.

### D-4 — ELK/Kibana export (scope 4) — design the seam, defer the sink

Structured JSON output is the prerequisite and is worth doing regardless: one JSON object per
record with stable field names. Ship that as a sink option; leave the actual shipper (filebeat
sidecar, HTTP appender, or a `juniper-observability` helper) out of the first change. A network sink
on the per-record path in a forked worker is exactly where an unbounded queue or a blocking socket
would cost more than the 18 % this design is trying to recover. `juniper-observability` already owns
structured-JSON logging for the service tier and is the natural home — reuse rather than a second
implementation.

## 5. What this is expected to be worth

Honest accounting, since #563's number is banked and must not be double-counted:

- **F-1 is the large one and it is not yet sized.** 18 % `logger.py` + ~15 % tensor formatting is
  the *ceiling*, not the recovery: some of those records are at levels that are enabled and would
  still be emitted. The recoverable fraction is the share of that work done for records that are
  **discarded**, and nothing measured to date separates the two.
- **F-2 and F-4 are bounded and real** — three syscalls per emitted record, two closures per
  emitted record, and 2.66 % of self time in level-name validation.
- **F-3 is a correctness/ergonomics fix**, not a performance one.

**Measure before building (§7 Q1).** One profiled cap-4 cell with all logging disabled gives the
true ceiling; the same cell at production level gives the enabled-record floor. The gap between them
is what D-1 can actually recover. That is one cell on the harness already used for the tensor probe,
and it should precede the implementation rather than justify it retroactively.

## 6. Constraints and hazards

- **`log_config` is mirrored into `juniper-cascor-model`.** Edits to `src/log_config/...` must be
  mirrored or `test_drift` fails, and pre-commit's black hook covers only `src/`, so it reformats
  one side of a byte-gated pair — re-sync the model copy after running pre-commit.
- **Every log-parsing tool anchors on the current text format.** The `+`-prefix, the
  `[file.py: func:LINE] (timestamp) [LEVEL] message` shape, and the `juniper_cascor.log` filename are
  depended on by the experiment harness, `util/ad-hoc/2026-08-26_g4_post_fix_analysis.py`, the
  census tooling and the snapshot pipeline. **A format change is a breaking change to the evidence
  corpus.** Either hold the human-readable format byte-stable and add JSON as a *second* sink, or
  budget for updating every consumer. Recommended: the former.
- **Do not fold this into a hot-path bugfix.** #573 was deliberately kept out of #563 so neither
  justifies the other; keep that separation.
- **Log rotation already happens** (`juniper_cascor.log.1` exists in service runs) and any analysis
  that reads only `juniper_cascor.log` silently misses records — a rotating file sink must keep that
  behaviour predictable and documented, since it has already caused one truncated analysis.

## 7. Open questions for the owner

1. **Measure the discarded-record share first?** Recommended — without it §5's headline is a
   ceiling, not a benefit.
2. **Flush per record or on an interval?** Per record is what the current code effectively gives
   (open/write/close) and is what makes a crashed run's log complete. An interval is faster and can
   lose the tail — which matters here, because a truncated log is how several analyses in this arc
   went wrong.
3. **Forked-worker file strategy** — per-process handle, per-PID file, or parent writer thread
   (D-2). This is the highest-risk decision in the design.
4. **Console default: stderr, or keep stdout?** Moving to stderr is the fix for the swallowed-pytest
   problem but changes what existing runners capture.
5. **How far does the call-site migration go?** Hot paths only (recommended) or a full sweep.
6. **Does structured JSON go through `juniper-observability`** as a shared sink, or stay local to
   cascor initially?

## 8. References

- [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) — the issue, owner-raised scope
- [cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563) — the `inspect.getmodule` fix; its number is banked, not available to this design
- `reports/perf-lane-post-fix-2026-08-26/worker_profile_inspect_share_pre563_vs_at67d7ea35.txt` — the shares quoted in §1
- `reports/perf-lane-post-fix-2026-08-26/worker_profile_diff_pre563_vs_at67d7ea35.txt` — the 1,813,318 `__format__` calls, identical on both arms
- 2026-08-24 handoff §4.13 — the original framing (per-record `open`, unconditional `print`)
- `notes/JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md` §8 — #563's fix design
