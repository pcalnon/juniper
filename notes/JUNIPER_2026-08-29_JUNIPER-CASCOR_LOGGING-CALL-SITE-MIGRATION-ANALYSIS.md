# Logging call-site migration — options analysis

**Project**: Juniper
**Sub-Project**: juniper-cascor (`src/log_config/logger/logger.py` and its 1,885 call sites)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-29
**Status**: ANALYSIS — **RECONCILED 2026-09-02**; answers Q5 of [`JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md), **and owner decision 5 is still open**
**Tracks**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)
**Measured at**: cascor `67d7ea35`

> **RECONCILED 2026-09-02.** G-1's measured hot-site list was produced
> ([`…GATED-MEASUREMENTS-RESULTS.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md) §3)
> and, exactly as §6 predicted it might, **it overturned this document's recommendation**: the
> expensive interpolation was one line at an *enabled* level, which no guard or lazy argument could
> recover. It shipped in [cascor#598](https://github.com/pcalnon/juniper-cascor/pull/598). Full
> verdict on every claim here:
> [`JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md) §5;
> plan of record: [`…LOGGING-REDESIGN-ROADMAP.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md).
> **What survives strongest is §5's hazard list and §7's guardrails** — §5.4 in particular, which has
> since been realised against the *guard* idiom this document recommends rather than the
> `%`-conversion it warned about.

---

## 1. The question

The redesign's finding F-1 is that **the level filter cannot prevent the work it exists to
prevent**. Given:

```python
cls._log_at_level(frame=cls._frm(), tsp=cls._tsp(), level=cls._level_trace, message=message, args=args or None)
```

Python evaluates `cls._frm()`, `cls._tsp()` and — critically — the caller's f-string **before**
`_log_at_level` is entered and can consult the level. A `logger.trace(f"... {tensor} ...")` in a hot
loop therefore pays full tensor formatting at TRACE level even when TRACE is off.

Fixing the logger's *internals* (moving `frame`/`tsp` inside, holding an open handle, integer level
comparison) is a contained change. Fixing the **message** cost is not contained: it lives at the
call sites, and there are a lot of them. Q5 asks how far that migration should go.

## 2. Why this is the expensive half

`Tensor.__format__` is called **1,813,318** times per 32-profile corpus, and *identically* before and
after [cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563) (`1813318/1813318`) — #563
removed the `inspect` storm and did not touch this at all. `torch/_tensor_str.py` (10.38 %) plus
`torch/_tensor.py` (5.21 %, essentially all `__format__`) is ~15.6 % of post-#563 worker self time,
against `logger/logger.py`'s own 18.00 %.

So the logger-internal fixes and the call-site migration are roughly **comparable in size**, and
only the call-site migration can touch the tensor-formatting half.

## 3. The measured surface

Counts over `src/`, excluding `src/tests/`, at `67d7ea35`:

| measure | count |
| --- | --- |
| total `logger.*(...)` call sites | **1,885** |
| of which f-string (`logger.x(f"…")`) | **879** (47 %) |
| `logger.debug` | 707 |
| `logger.info` | 313 |
| `logger.trace` | 281 |
| `logger.verbose` | 267 |
| `logger.warning` / `error` / `fatal` / `critical` | 168 / 141 / 5 / 4 |

**Suppressed-by-default levels — `trace` + `verbose` + `debug` — are 1,255 sites, 67 % of all
calls.** At a production level of INFO, every one of those pays its message cost and discards it.

Concentration in the hot path:

| file | logger calls | f-strings interpolating a tensor-ish name |
| --- | --- | --- |
| `cascade_correlation/cascade_correlation.py` | 501 | 97 |
| `candidate_unit/candidate_unit.py` | 171 | 49 |
| **hot-path subtotal** | **672** (36 % of all) | **146** |

The tensor-ish count greps for interpolations naming `tensor`/`weight`/`output`/`input`/`corr`/
`activation`/`grad`/`x_`/`y_`. It is a **heuristic, not a proof** — it will miss a tensor reached
through a local alias and will over-count a plain int named `output_size`. Treat 146 as an order of
magnitude, not a work order; §7 G-1 says how to get the real list.

The useful conclusion stands regardless of the heuristic's precision: **the expensive sites are
concentrated in two files**, and a hot-path-only migration is a ~150-site diff rather than an
879-site one.

> **CORRECTION 2026-09-02 — the arithmetic is wrong and the conclusion is UNDERSTATED.** The 1,885
> denominator includes **472 sites in `src/cascade_correlation/backups/`** (tracked, imported by
> nothing, dead) and **250 sites in `src/api/`** which are bound to **stdlib** loggers and never reach
> this logger at all. On the live tree the two-file concentration is **46.2 %**, and on live Path-A
> sites it is **55.7 %** — so removing the dead weight makes this section's claim *stronger*, not
> weaker. The real defect is the **file set**: `src/spiral_problem/spiral_problem.py` carries **264**
> sites and 45 tensor-ish interpolations and is omitted here; the three-file set reaches **64.2 % /
> 77.3 %**. Full census, with its method caveats:
> [`…LOGGING-CURRENT-STATE-RECONCILIATION.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md) §3.1.
> (Separately, G-1's measurement showed the 146 heuristic overstated the *expensive* set by two orders
> of magnitude — the answer was one line.)

## 4. Options

### Option A — hot paths only, converted to lazy `%`-args

Convert the ~146 tensor-interpolating f-strings in the two hot files to the logger's existing
`message % args` path (`logger.py:472`).

```python
self.logger.trace("… correlation=%s unit=%s", corr, unit)     # args interpolated only if enabled
```

**Strengths**: smallest diff that captures nearly all the benefit, since the cost is concentrated;
uses machinery that already exists and is already commented for this purpose; reviewable in one
sitting; leaves 90 % of the codebase untouched, so 90 % of the regression risk never arises.

**Weaknesses**: leaves two idioms in the codebase permanently (f-strings in cold paths, `%`-args in
hot ones) with no mechanical rule for which to use — a future author adding a hot-path log will
reach for the f-string. Recovers nothing from the 733 f-strings outside the two files, some of which
are in per-epoch paths not counted here.

**Risks**: `%`-conversion is **not** mechanically semantics-preserving (see §5). A literal `%` in an
existing message becomes a format spec and raises at runtime — and it raises *inside logging*, in a
forked worker, at a level that may be off in testing and on in production.

### Option B — full sweep, all 879 f-strings

**Strengths**: one idiom everywhere; the rule becomes teachable and lintable; no future author has
to know which file they are in.

**Weaknesses**: an 879-site diff in which **the great majority of the changes are worthless** — a
`logger.info(f"Starting {name}")` at start-up costs nothing worth recovering. Review attention is
finite and would be spread across ~730 sites that do not matter, which is exactly where a
`%`-conversion bug slips through.

**Risks**: the same §5 conversion hazards, multiplied by six, across files with far less test
coverage than the two hot ones. High probability of at least one runtime `%` fault in a rarely-hit
error path — the worst place to put a new exception.

### Option C — call-site guards, no message rewriting

Leave messages as f-strings; wrap expensive sites in a cheap predicate.

```python
if self.logger.is_enabled_for(TRACE):
    self.logger.trace(f"… {tensor} …")
```

**Strengths**: zero conversion risk — the message string is untouched, so §5's hazards do not exist.
The guard is obvious in review. Works for *any* expensive argument, not just `%`-convertible ones
(e.g. a `.tolist()` or a comprehension in the message). Can be applied incrementally, site by site,
with no global consistency requirement.

**Weaknesses**: three lines where there was one; visually noisy at density. Easy to forget on new
code, and a missing guard is invisible — it costs performance silently, which is precisely how the
current situation arose. Adds a branch (negligible next to the formatting it avoids).

**Risks**: low. The main one is scope creep — guards migrating into cold paths where they add noise
for no gain.

### Option D — lazy message callables

Extend the logger to accept a zero-arg callable and invoke it only after the level check.

```python
self.logger.trace(lambda: f"… {tensor} …")
```

**Strengths**: keeps f-string ergonomics and readability exactly as they are — the diff is
`("` → `(lambda: "` — while deferring 100 % of the message cost. No `%`-conversion hazards at all.
Mechanically applicable, and much easier to lint for than "did you remember a guard?". Handles
arbitrarily expensive message construction, not just interpolation.

**Weaknesses**: a new idiom the codebase does not currently use, requiring a logger change (accept
`callable(message)` and call it post-filter) plus a decision about what happens if the lambda raises
— a logging call must never take down a training run, so it needs its own try/except, which is a new
swallow-path to get right. Allocates a closure per call even when suppressed: far cheaper than
formatting a tensor, but not free, and it is a *new* per-call cost at the 1,255 suppressed sites.

**Risks**: closures capture by reference, so a lambda evaluated after the fact can render a
**different value** than the one at the call site if the variable is rebound in between. For a
post-filter-but-immediate invocation this is safe; it becomes unsafe the moment anyone defers the
message further (e.g. into a queue for the parent writer thread — a fallback the redesign's D-2
explicitly keeps on the table). **Option D and the parent-writer-thread sink are in latent conflict
and must not be adopted independently without revisiting this.**

### Option E — do nothing at the call sites; ship logger internals only

**Strengths**: no call-site risk whatsoever; still recovers F-2 (per-record `open`), F-4 (closures,
level-name validation) and the `frame`/`tsp` eager evaluation, which are real.

**Weaknesses**: leaves the tensor-formatting half — the larger, more surprising half — entirely on
the table, and leaves F-1's central finding unaddressed. The 1.8 M `__format__` calls remain.

**Risks**: none technically. The risk is organisational: "we did the logging work" becomes true
while the headline finding is untouched, and the measurement in §5 of the design doc then has no
follow-through.

## 5. The conversion hazard, stated precisely

Any option that rewrites message strings (A, B) inherits these. They are the reason this analysis
recommends against a mechanical sweep:

1. **A literal `%` becomes a format spec.** `logger.info(f"progress {pct}%")` → `"progress %s%"`
   raises `ValueError: incomplete format` at emit time. Existing messages containing `%` must be
   escaped to `%%`.
2. **Format specs do not survive.** `f"{x:.4f}"` must become `"%.4f"`; `f"{x!r}"` must become `"%r"`.
   A conversion that drops the spec silently changes log output — and several analysis tools in
   `util/ad-hoc/` parse numeric fields out of log text, so a precision change is a **downstream
   parsing change**, not a cosmetic one.
3. **Single-argument `%` with a tuple-valued variable mis-formats.** `msg % args` where `args` is a
   tuple splats it. The logger's `if args: message = message % args` path passes whatever it is
   given, so a lone tuple argument is a live bug class.
4. **Failures are level-gated and therefore hide.** A broken `%` string at TRACE never raises in a
   test run at INFO. It surfaces in production, in a forked worker, on the first run someone turns
   TRACE on to debug something else.

Hazard 4 is the decisive one: it means **conversion bugs are not discoverable by the ordinary test
suite**, and any migration must carry a guardrail that exercises every converted site at its own
level (§7 G-2).

## 6. Recommendation

**C + D as the standing idiom, A as the immediate work — and explicitly not B.**

Concretely, and in this order:

1. Ship the logger-internal fixes first (Option E's content). They are independent, risk-free
   relative to call sites, and make the level check cheap enough for a guard to be worth using.
2. Take the §5 measurement from the design doc **before** touching call sites, so the recoverable
   share is known rather than assumed.
3. Migrate the hot path only (Option A's scope, ~146 sites in two files), preferring **Option C's
   guard** wherever the message is complex and `%`-conversion would be error-prone, and `%`-args
   where the conversion is trivial and mechanical. The two are complementary, not alternatives.
4. Evaluate Option D as a follow-up once the sink strategy is settled — its conflict with a
   deferred/queued writer must be resolved first.
5. Never do B. The 733 cold-path f-strings are readable as they are and buy nothing.

The recommendation rests on the concentration finding: 36 % of call sites and essentially all of the
tensor formatting live in two files. If §7 G-1's real measurement contradicts that — if expensive
interpolations turn out to be spread across the codebase — then this recommendation changes, and
Option D becomes much more attractive because it is the only mechanically-applicable one.

## 7. Guardrails

Required regardless of which option is chosen:

- **G-1 — get the real hot-site list, do not trust the grep.** §3's 146 is a name-based heuristic.
  The honest instrument is the profile that already exists: attribute `Tensor.__format__` callers
  from the worker `.prof` corpus in `reports/perf-lane-post-fix-2026-08-26/` and rank *actual*
  call sites by cost. Migrating from a measured list is a different activity from migrating from a
  grep, and only the first can claim to have covered the expensive sites.
- **G-2 — exercise every converted site at its own level.** One test run per level
  (`CASCOR_LOG_LEVEL=TRACE`, then VERBOSE, then DEBUG) over the converted modules, asserting no
  exception and no `ValueError: … format …`. Without this, hazard §5.4 ships.
- **G-3 — byte-compare log output before and after on a fixed cell.** Any diff in the human-readable
  text is a **breaking change to the evidence corpus** — the experiment harness,
  `util/ad-hoc/2026-08-26_g4_post_fix_analysis.py`, the census tooling and the snapshot pipeline all
  parse this format. Identical bytes is the acceptance criterion; a deliberate change needs every
  consumer updated in the same PR.

  > **CORRECTION 2026-09-02 — "identical bytes" is already inconsistent with shipped practice, and
  > the criterion needs splitting.** #598 deliberately changed message *content*
  > (`Norm Output: tensor([…])` → `shape=… l2=…`) with review, and was right to. Restate as: the
  > record **envelope** is byte-stable, and **anchored message text** is protected by a named-marker
  > inventory — which is the half of this guardrail nothing has ever built, and the half that matters
  > most, since anchored message text is BREAKING for ~17 juniper-ml scripts while the prefix is
  > breaking for none. The same-PR consumer requirement stands. Carried into the roadmap as P0.4(c).
- **G-4 — re-measure, do not assume the win.** Re-run the 32-profile worker corpus after migration
  and report the actual `__format__` call-count delta. The pre-migration number is 1,813,318; a
  migration that does not move it materially did not work, whatever the diff looks like.
- **G-5 — mirror `log_config` into `juniper-cascor-model`.** Byte-gated by `test_drift`, and
  pre-commit's black hook covers only `src/`, so it reformats one side of the pair. Re-sync after
  every pre-commit run.

  > **CORRECTION 2026-09-02 — clause 1 is wrong for the file a redesign touches; clause 2 is right.**
  > `log_config/logger/logger.py` is on `_INTENTIONAL_DIVERGENCE` (`test_drift.py:31`) and must
  > **NOT** be mirrored — `test_intentional_divergences_actually_differ` (`:104-117`) **fails if the
  > copies become identical**, which is what #598 hit and reverted. The other three `log_config`
  > files **are** byte-gated, as are `candidate_unit/`, `utils/` and `cascor_constants/` — so the
  > mirroring obligation is real for everything *except* the logger. **The black-hook trap in the
  > second sentence is entirely correct and must be retained** — it is carried into the roadmap as
  > P1-G2. See the reconciliation's N-5.
- **G-6 — one PR per file, not one PR for the migration.** `cascade_correlation.py` (501 sites) and
  `candidate_unit.py` (171) are separately reviewable; together they are not.

## 8. Sub-questions this analysis cannot settle

1. **Does G-1's measured list agree with the grep?** Until it is run, §6's recommendation rests on a
   heuristic. This is the one input that could change the recommendation.
2. **Should `is_enabled_for` be public API on the logger?** Option C requires it; the current class
   exposes no such predicate.

   > **CORRECTION 2026-09-02 — half answered, and the other half got worse.** A predicate *does*
   > exist: `Logger.isEnabledFor` (`logger.py:1027`), since PR #116, already used at 8 sites in
   > `candidate_unit.py`. But **it reads different state than the emit filter** — `_log_level` vs
   > `_level_logger_config`/`_level_logger_name`, with `set_level()` writing only the first — so a
   > guard can be open on records that are then discarded. The API question this item raises is
   > therefore still live and now more urgent: an integer-taking predicate reading its own copy of
   > the level is what let three wrong guard integers ship unnoticed. See the reconciliation's N-3.
3. **What is the policy for new code?** A migration without a rule is undone by the next author.
   Options: a lint rule banning f-strings in `logger.trace/verbose/debug` calls within the hot
   modules; a docstring convention; or nothing. A lint rule is the only one that actually holds.
4. **Is `logger.debug` suppressed in production?** 707 sites — the single largest level — and the
   whole cost argument for them depends on the answer. Worth confirming against the deployed config
   rather than assumed.

   > **ANSWERED 2026-09-02 — yes.** With no environment override the level resolves to **INFO**
   > (`constants.py:663-668`), and `_filter_by_level` requires `level_num >= log_level_num`, so
   > DEBUG(10) < INFO(20) is discarded. Count correction: **517** live `logger.debug` sites, and
   > **919** counting `trace` and `verbose` — the 707/1,255 figures include the dead `backups/` tree.
   > Census and method caveats:
   > [`…LOGGING-CURRENT-STATE-RECONCILIATION.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md) §3.1.

## 9. References

- [`JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md) — the parent design; F-1 is the finding this analysis serves
- [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) — the issue
- [cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563) — the `inspect` fix, whose number is banked and unavailable to this work
- `reports/perf-lane-post-fix-2026-08-26/worker_profile_diff_pre563_vs_at67d7ea35.txt` — the 1,813,318 `__format__` calls, identical on both arms
