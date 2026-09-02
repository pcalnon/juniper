# Logging — current state, reconciled against the deferred redesign

**Project**: Juniper
**Sub-Project**: juniper-cascor (`src/log_config/`), with an ecosystem inventory
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-09-02
**Status**: RECONCILIATION — supersedes the stale parts of the two 2026-08-29 logging documents
**Measured at**: cascor `70edfc4` (HEAD, 2026-09-02); prior evidence at `67d7ea35` and `64ff9ab8`
**Tracks**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)

> **Anchoring rule, inherited from the design and restated because this document is line-number
> dense.** All line numbers are at the revisions named above. **Anchor on the quoted text, not the
> number** — `_add_best_candidate` moved five times in one arc (2026-08-24 handoff §5.5), and N-4
> below is itself the record of a line-anchored parser that silently parsed nothing after a refactor.

---

## 1. Why this document exists

Two documents of record were written on 2026-08-29 and then overtaken:

- [`JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md) — the design of record.
- [`JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md`](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md) — Q5's options analysis.

Between them and today, three things happened. First, the measurement they gated on was taken and
**inverted their priority order** ([`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md) §3).
Second, [cascor#598](https://github.com/pcalnon/juniper-cascor/pull/598) shipped the top two items
from that revised order. Third, the redesign was deferred, and nothing has been written down since.

This document establishes what is true at `70edfc4`, issues a verdict on every substantive claim in
the two documents, and records the findings neither of them carries. It is the evidence base for
[`JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md).

**The headline is not "the docs are stale."** Roughly half of what changed is staleness. The other
half is that the design reasons about a **process model the repo does not use** (§4 D-2), inverts
the **format-compatibility surface** it is trying to protect (§4 §6-a), and recommends a **call-site
idiom that is already deployed and already wrong** (§6 N-3).

---

## 2. What shipped, and what it banks

[cascor#598](https://github.com/pcalnon/juniper-cascor/pull/598) (`64ff9ab8`, merged 2026-08-30) is
the "critical remediation". It took exactly the top two items of the revised priority order:

| revised-order item | measured value | status at `70edfc4` |
| --- | --- | --- |
| 1 — stop formatting whole tensors into the INFO line | ~28 s / 33 % | **SHIPPED**. `CandidateUnit._tensor_brief` (`candidate_unit.py:701`) renders shape + scalar L2. Matched-callee `__format__` calls 3,626,636 → 2,912 (see the note below on which figure is which). |
| 2 — make `_filter_by_level` cheap | 11.19 s / 13.2 % | **SHIPPED**, by memoisation rather than by resolve-once-at-config-time. `_resolve_level_number` + `_invalidate_level_cache` (`logger.py:474`, `:463`). 17.3 µs → 1.6 µs per call. |
| 3 — move `frame`/`tsp` inside `_log_at_level` | 0.87 s / 1.0 % | **NOT DONE**. All eight public methods still evaluate `frame=cls._frm(), tsp=cls._tsp()` as arguments (`logger.py:554-610`). |
| 4 — call-site migration | small | **NOT DONE**, and correctly last. |

Headline: worker self time **84.96 s → 43.20 s** across a 32-profile cap-4 corpus. #598's own PR body
carries the honest caveat that the corpus did **15 % more** logger calls (646,016 → 746,410), "so the
headline −49 % is approximate."

**Two `__format__` figures are in circulation and they are not the same population.** The design and
the analysis quote **1,813,318**; #598's commit-message table quotes **3,626,636**; #598's own prose
quotes 1,813,318. Both are correct and neither supersedes the other:

- **1,813,318** = calls to `Tensor.__format__` alone.
- **3,626,636** = the whole *matched-callee set* the attribution tool targeted —
  `Tensor.__format__`, `float.__format__`, **and** `_tensor.py:1144(__format__)`, which appears in
  the corpus as its own caller with 1,813,210 calls (the delegation edge). 1,813,318 + 1,813,210 =
  3,626,528, with the 108-call residue in `float.__format__`
  (`reports/measurements-2026-08-29/format_caller_attribution.txt`, header + caller table).

The **2,262** figure is a third population again: the calls attributed to
`candidate_unit.py:702(_display_training_progress)` specifically — arithmetically confirmed in
GATED §3 as 1,131 emitted `Norm Output:` lines × 2 tensors. The post-fix **2,912** is a matched-set
total, so it is not comparable to 2,262 and does not represent a regression.

**Anchor for G-4**: the migration analysis's guardrail names 1,813,318 as the number a migration must
move. That anchor remains valid **against the `Tensor.__format__`-only count**, and any re-measurement
must report which population it is quoting.

**Three qualifications on that number, all load-bearing for the roadmap.**

1. **It was measured on the pre-merge branch build, not on merged `main`.** The `logfix-verify`
   corpus (`~/.local/state/juniper-experiments/logfix-verify/prof`, 32 profiles) was last written
   **2026-08-30 01:59:05**, twelve minutes *before* the `64ff9ab8` merge at 02:11:01. `find ~/.local/state/juniper-experiments -name '*.prof' -newermt "2026-08-30 02:11:01"` returns **zero**. The
   post-merge equivalent of [cascor#579](https://github.com/pcalnon/juniper-cascor/issues/579)'s
   verification has not been run.
2. **Two components of the remaining 43.20 s are decomposed; the balance is not.** #598's PR body
   reports `_filter_by_level` at **1.20 s / 746,410 calls / 2.8 %** of worker self time post-fix
   (from 11.19 s / 13.2 %), and `__format__` at 1,245× fewer calls. What is *not* decomposed is
   everything else — the per-record `open()`, the `print()`, the closures, `strftime`, and the
   non-logging remainder. The pre-#598 attribution
   (`reports/measurements-2026-08-29/format_caller_attribution.txt`) is a corpus at `67d7ea35` and
   cannot speak to those.

   **Consequence for the roadmap**: the single largest previously-measured logger component is
   already at 2.8 %, which materially lowers the expected value of further logger-internal work
   before Phase 0 even runs.
3. **Nothing was recorded on the issue.** [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)
   has `createdAt == updatedAt == 2026-08-24T00:29:11Z` and **zero comments**. Neither #598, nor the
   measurement that justified it, nor the deferral is recorded there. #598 says "Partially addresses
   #573" in its own body only.

---

## 3. The architecture as it actually is

The design documents describe **one** logging path. There are **three**, and they share a file.

### Path A — the custom classmethod logger (the one the docs describe)

`Logger(logging.getLoggerClass())`, `src/log_config/logger/logger.py:114`. It bypasses stdlib
handlers entirely:

```python
print(f"+{_console_message(frame, tsp, level, message)}")          # logger.py:523
_line = f"+{_file_message(frame, tsp, level, message)}\n"
with open(cls._logging_file, "a") as f:                            # logger.py:525-526
    f.write(_line)
```

Records carry a `+` sentinel and a **second-resolution** timestamp `(2026-09-01 05:35:59)`.
Note `self.logger = Logger` binds the **class**, not an instance (`candidate_unit.py:187`, `:296`), so
the innermost candidate-training loop is on this path.

### Path B — stdlib `logging` via `dictConfig`

`conf/logging_config.yaml`, applied at `logger.py:772`. A `StreamHandler` at **ERROR** on stdout and a
plain `logging.FileHandler` at **DEBUG** writing **the same file**. `Fix C1` (`logger.py:745-753`)
rewrites the YAML's relative `filename:` to an absolute path so the destination is not CWD-dependent.
Records carry **no** `+` and a **millisecond** timestamp `(2026-09-01 05:35:56,045)`.

### Path C — the API tier's JSON logging

`src/api/observability.py:75` — a **local fork** of `juniper_observability.configure_logging`, adding a
`RotatingFileHandler` (`:113-118`) and selecting `JuniperJsonFormatter` (`:102`) from
`juniper-observability`. The fork is deliberate and its rationale is in-source at `:81-83`: the shared
function's console handler "would race the file handler" and "the lib has no notion of cascor's log
directory layout". Every other consumer in the ecosystem — data (`app.py:45`), canopy
(`main.py:220`), recurrence (`logging_config.py:41`) — calls the shared function unmodified.

### What that combination produces on disk

One experiment run, `~/.local/state/juniper-experiments/20260901T103548Z-befc/logs/`:

| file | size | content |
| --- | --- | --- |
| `juniper_cascor.log.1` | 15,161,801 B | **77,796** Path-A `+` records **and** 10,375 non-`+` records, interleaved, two timestamp formats |
| `juniper-cascor.log` (hyphen) | 11,901,133 B | **77,790** Path-A `+` records again (the harness redirects the service's stdout: `juniper-ml/util/experiment_stack.bash:685`), plus 97 uvicorn lines and 21 lines in a third format |
| `juniper_cascor.log` | 2,122 B | the post-rotation tail — 21 records, all non-`+` |

**Path B and Path C are not distinguishable on disk.** Path C's file formatter
(`api/observability.py:119`) is byte-identical to Path B's `formatter_file`
(`conf/logging_config.yaml:47`), so the 10,375 non-`+` records above are Path B ∪ Path C. Any
per-path byte census must either instrument the writers or report `A` vs `{B ∪ C}`.

**Every Path-A record is written to disk twice** — once by `open()`/`write()`, once by `print()` into
a redirected stdout — in two *different* formats (the console formatter omits the function name:
`constants_logging.py:152-158`). ~27 MB for one short run; 4.8 MB/run is typical across the
2026-09-01 cells; the cascor repo's own `logs/` is **3.3 GB**. #573 records a **637 MB** trainer log
from a single cap-64 CLI leg.

### 3.1 Call-site census — one regex, one rev, three populations

Every call-site number in this document and the roadmap comes from this census, so that no two
figures use different denominators. Method:
`git grep -o -E '\b[Ll]ogger\.(trace|verbose|debug|info|warning|error|critical|fatal)\(' HEAD -- src`
at `70edfc4`. Single-quoted f-strings were checked for separately and are **zero**, so the
double-quote-only f-string pattern misses nothing.

**Two method caveats that explain most disagreement with other counts.** (1) `git grep` walks the
**tracked** tree; `src/backups/check.py` carries a further ~68 sites and is **untracked**, so a
working-tree grep counts it and this census does not. (2) The regex accepts `logger.`/`Logger.`
prefixes only; a broader alternation (`self._logger`, `cls.logger`, `exception`, `warn`) returns
higher totals. Any figure quoted downstream must say which.

| population | all calls | f-strings | trace+verbose | debug |
| --- | --- | --- | --- | --- |
| all of `src/` (tracked) | 1,953 | 907 | 550 | 737 |
| less `src/tests/` | 1,943 | 905 | 548 | 734 |
| less `cascade_correlation/backups/` — dead (N-6) | 1,471 | 870 | 402 | 517 |
| **less `src/api/` — stdlib-bound, not Path A** | **1,221** | — | — | — |

**`src/api/` is not on Path A.** It carries **250** of the counted sites and has **zero** `Logger.`
references; its 25 modules bind `logging.getLogger(...)`. So a call-site count is not a Path-A count,
and the migration surface is smaller than the raw total suggests. A full per-file binding audit
across the rest of `src/` has **not** been done, so 1,221 is a bound, not a settled figure.

Concentration, on both defensible denominators:

| file set | calls | of 1,471 (live) | of 1,221 (live, Path A) |
| --- | --- | --- | --- |
| `cascade_correlation.py` (508) + `candidate_unit.py` (172) | 680 | 46.2 % | **55.7 %** |
| …plus `spiral_problem.py` (264) | 944 | 64.2 % | **77.3 %** |

**Reconciliation with the 2026-08-29 figures.** The migration analysis reported 1,885 sites / 879
f-strings / 707 `debug` at `67d7ea35` under a regex that has not been recovered. Per-file counts at
`67d7ea35` and at HEAD differ by **+2 calls** under *this* regex (`api/app.py` +1,
`api/lifecycle/manager.py` +1) — so **the surface has not moved; the differences are method, not
drift.** Where the two disagree, this census is the one used, and the older figure is not mixed with
it.

### Ecosystem inventory

Independently surveyed from the code tree across all repos. The relevant conclusion for scope:

- **No repo outside cascor imports cascor's `Logger`.** `grep -rl 'from log_config'` across canopy,
  data, recurrence, cascor-worker, cascor-client and data-client returns nothing. The custom logger's
  blast radius is cascor plus its `juniper-cascor-model/` mirror (which `juniper-cascor-worker`
  depends on: `pyproject.toml:68`).
- **`juniper-canopy` has a second, unrelated custom logger** (`src/logger/logger.py:165`,
  `CascorLogger` + four subclasses) with its own TRACE/VERBOSE, a `RotatingFileHandler` and a JSON
  formatter. Its `CASCOR_CONSOLE_LOG_LEVEL` / `CASCOR_FILE_LOG_LEVEL` overrides are **dead code** —
  `logger.py:536` gates on a top-level `logging:` key that its dictConfig-shaped YAML does not have.
- **`juniper-service-core` has no logging configuration at all** — 22 `getLogger` sites, 150 emit
  sites, zero handlers, and a `JUNIPER_SERVICE_LOG_LEVEL` (`settings.py:31,36`) that nothing reads.
- **`juniper-observability`'s logging API is small**: `JuniperJsonFormatter`, `configure_logging`,
  `DEFAULT_LOG_FORMAT_PLAIN`, `LOG_FORMAT_JSON` (`juniper_observability/logging.py`, 83 lines). It
  installs a single `StreamHandler()` — **stderr**, not stdout — after **removing all existing root
  handlers** (`logging.py:72-73`). No file sink, no rotation, no custom levels, six fixed JSON keys.
- `.format()` inside a log call: **zero occurrences ecosystem-wide.**

---

## 4. Verdict on the design document

Claim-by-claim. **CONFIRMED** = still true and still load-bearing. **BANKED** = fixed, remove from
scope. **STALE** = was true, overtaken. **WRONG** = not true at the time of writing either.

| # | claim | verdict | evidence |
| --- | --- | --- | --- |
| F-1a | `frame`/`tsp` eagerly evaluated before the level check | **CONFIRMED** | `logger.py:554-610`, all eight methods |
| F-1b | the lazy `%`-args path exists and "essentially no call site uses it" | **STALE** | the path exists (`logger.py:520-521`); **97** call sites now use it, including in the hot files (`candidate_unit.py:855`) |
| F-1c | the f-string cost is "the single highest-value finding" | **SUPERSEDED** | measured: the cost was one line at an *enabled* level; banked by #598 |
| F-2 | the log file is opened per record | **CONFIRMED** | `logger.py:525-526`, retry at `:543` |
| F-2b | the `FileNotFoundError` retry is correct and load-bearing | **CONFIRMED** | `logger.py:527-543`; keep it |
| F-3 | stdout is written unconditionally; no independently disableable console sink | **CONFIRMED, and under-stated** | `logger.py:523`. See N-1: it is a 2× write amplification, not only an ergonomics issue |
| F-4a | two formatter closures built per record | **CONFIRMED** | `logger.py:521-522` |
| F-4b | `_is_valid_level_name` is 2.66 % of worker self time | **BANKED** | #598's `_resolve_level_number` memoisation |
| §4 D-1 | expose an `is_enabled_for(level)` predicate | **REFINED, not refuted** (a proposal has no truth value) | A predicate exists — `Logger.isEnabledFor`, since PR #116 (`logger.py:1027`) — already used at 8 sites in `candidate_unit.py`, so the *machinery* half is met. Unmet: it takes an **integer** where D-1 proposed a **symbolic** argument, and — decisively — it reads different state than the emit filter (N-3) |
| §4 D-2 | "Candidate workers are **forked** from the parent"; strategy hinges on "opened lazily on first write **after fork**" | **WRONG** | the pool is **forkserver** by default (`cascade_correlation.py:1103-1109`). The in-source comment even records the correction: *"(Issue #569: an earlier comment here said the code used the 'fork' context — it never did on this path.)"* See N-2 |
| §4 D-3 | precedence "…global env var (`CASCOR_LOG_LEVEL`, already honoured)…" | **STALE** | canonical is **`JUNIPER_CASCOR_LOG_LEVEL`**; `CASCOR_LOG_LEVEL` is deprecated with a `DeprecationWarning` and a split-config stderr warning (CFG-05, `constants.py:638-658`) |
| §4 D-4 | structured JSON is "the prerequisite… ship that as a sink option"; cascor "gains a hard dependency on `juniper-observability`" | **STALE** | cascor **already** imports `JuniperJsonFormatter` and already emits JSON on the API tier (`api/observability.py:36`, `:102`). The dependency exists today |
| §7 dec. 6 | "through `juniper-observability`… no second implementation local to cascor" | **ALREADY VIOLATED, deliberately** | `api/observability.py:75-119` *is* a local fork of `configure_logging`, with a documented rationale at `:81-83`. The decision needs restating as "reconcile the existing fork", not "do not create one" |
| §5 | payoff table and priority order | **SUPERSEDED** (already marked in-doc) | GATED-MEASUREMENTS §3 |
| §6-a | "the `+`-prefix, the `[file.py: func:LINE] (timestamp) [LEVEL] message` shape, and the filename are depended on… A format change is a breaking change" | **PARTIALLY WRONG — right about the surface, wrong about one element** | Right that format is a compatibility surface, and that the `+`-prefix, timestamp and filename are depended on (N-4 rates all three BREAKING); its remedy is roadmap P5-G2. **Wrong only about `[file.py: func:LINE]`** — nothing parses it. **Narrow, do not delete** |
| §6-b | "`log_config` is mirrored into `juniper-cascor-model`… edits must be mirrored or `test_drift` fails" | **WRONG for the file that matters** | it is **file-level**. `log_config/logger/logger.py` is on `_INTENTIONAL_DIVERGENCE` (`juniper-cascor-model/tests/test_drift.py:31`) and is **not** byte-gated; a reverse guard, `test_intentional_divergences_actually_differ` (`:104-117`), **fails if you do mirror it**. The other three `log_config` files *are* byte-gated. See N-5 |
| §6-c | "Log rotation already happens… a rotating file sink must keep that behaviour predictable" | **CONFIRMED and EXPLAINED** | the rotator is **Path C**: `api/observability.py:110` names `log_dir / "juniper_cascor.log"` and `:111-115` wraps it in a `RotatingFileHandler` at 10 MB / 5 backups (`constants_logging.py:276-277`) — the same file Paths A and B write. `logs/` holding exactly `.1`…`.5` matches `backupCount=5`. See N-9 |
| §7 dec. 2 | flush per record — *"a complete log for a crashed run outweighs the throughput; a truncated log is how several analyses in this arc went wrong"* | **CONFIRMED as a decision, rationale intact** | Path A already achieves it by closing the file every record. The rationale must travel with the decision: per-record flush is the obvious thing to trade away once an I/O cost is measured |
| §7 dec. 3 | per-process file handle, opened lazily **on first write after fork**; provisional | **PREMISE REFUTED, DECISION SALVAGEABLE** | the premise is `fork`; the pool is `forkserver` (N-2). The decision's *shape* survives, but "after fork" must be re-read as "after forkserver start", and the `O_APPEND` requirement from the same section is what makes it safe at all. **Never formally re-issued against the corrected process model** |
| §7 dec. 5 | call-site migration scope — *"Still owner's call"* | **STILL OPEN, STILL THE OWNER'S** | the analysis it was deferred pending has been delivered and its recommendation overturned by measurement, so the decision is now *ripe* — but it has not been taken. It is **not** discharged by this roadmap; carried to roadmap §12 |
| §7 dec. 4 | keep console on stdout | **CONFIRMED as a decision** | but `juniper_observability.configure_logging` uses **stderr** (`logging.py:75`), so "keep stdout" is a divergence from the shared library, not alignment with it |
| §7.1 | the swallowed-pytest problem is unexplained | **CONFIRMED, still unexplained** | untouched since |

---

## 5. Verdict on the call-site migration analysis

| # | claim | verdict | evidence |
| --- | --- | --- | --- |
| §3 | 1,885 call sites, 879 f-strings | **CONFIRMED to method** | at `70edfc4` a broader regex gives 1,943 / 870 excluding tests. Per-file counts at `67d7ea35` vs HEAD differ by **+2 records total** — the surface has not moved |
| §3 | "36 % of call sites… in two files"; "the expensive sites are concentrated in two files" | **ARITHMETIC WRONG, CONCLUSION STRENGTHENED** | the denominator includes **472 dead** sites (N-6) and **250 stdlib-bound** sites in `src/api/`. Excluding them **raises** the two-file concentration to **46.2 %**, or **55.7 %** of live Path-A sites (§3.1) — the correction *confirms* the claim. The real defect is the **file set**: `spiral_problem.py`'s 264 sites are omitted; three files reach **64.2 % / 77.3 %** |
| §3 | 146 tensor-ish interpolations (heuristic) | **CONFIRMED as a heuristic, and refuted as a proxy** | reproduces today at 127 in the two files (+45 in the omitted third). The measured answer was **one line**. The heuristic overstated by ~two orders of magnitude — exactly what its own G-1 warned |
| §4 A/B | `%`-conversion hazards §5.1–5.4 | **CONFIRMED** and still the right reason to refuse Option B | |
| §5.4 | "conversion bugs are not discoverable by the ordinary test suite" — level-gated failures hide | **CONFIRMED, and it has already happened — to the guards, not the conversions** | N-3 |
| §6 | recommendation "C + D as the standing idiom, A as the immediate work" | **PARTIALLY OVERTAKEN** | step 1 (logger internals) and step 2 (measure first) both happened; step 3's premise — that the expensive sites are in that ~146 — is refuted |
| §8 Q2 | "Should `is_enabled_for` be public API? …the current class exposes no such predicate" | **HALF ANSWERED** — the existence half only | A predicate exists (`isEnabledFor`, `logger.py:1027`), so the second clause is wrong. **The question itself — should there be a documented, supported predicate that call sites are directed to use — is still open**, and N-3 re-raises its substance: an integer-taking `isEnabledFor` is what let the wrong integers ship. Carried to roadmap P1.1 |
| §8 Q4 | "Is `logger.debug` suppressed in production?" | **ANSWERED: yes** | default resolves to INFO (`constants.py:663-668`); `_filter_by_level` requires `level_num >= log_level_num`, so DEBUG(10) < INFO(20) is discarded. **517 live `logger.debug` sites** (§3.1) are suppressed by default; **919** counting `trace` and `verbose`. The analysis's 707/1,255 include the dead `backups/` tree |
| §7 G-1 | get the real hot-site list from the profile | **DISCHARGED**, and it changed the recommendation | GATED-MEASUREMENTS §3 |
| §7 G-3 | "Identical bytes is the acceptance criterion" | **CONTRADICTED BY SHIPPED PRACTICE** | #598 deliberately changed message *content* (`Norm Output: tensor([…])` → `shape=… l2=…`). The criterion must be restated as record-*envelope* stability plus a named-marker inventory — N-4 |
| §7 G-5 clause (i) | "mirror `log_config` into `juniper-cascor-model`… byte-gated by `test_drift`" | **WRONG for `logger.py`, RIGHT for the other three** | mirroring `logger.py` **fails** `test_intentional_divergences_actually_differ`; #598 hit this and reverted. But `log_config/__init__.py`, `log_config/log_config.py` and `log_config/logger/__init__.py` **are** byte-gated and must be mirrored. N-5 |
| §7 G-5 clause (ii) | "pre-commit's black hook covers only `src/`, so it reformats one side of the pair — re-sync after every pre-commit run" | **FULLY CORRECT — retain** | independently confirmed by #598's PR body. Carried unchanged as roadmap P1-G2. **Deleting G-5 wholesale would lose this trap**, which is why clause (i)'s narrowing is stated separately |
| §7 G-6 | one PR per file | **CONFIRMED** | `cascade_correlation.py` (504 sites) and `candidate_unit.py` (172) are separately reviewable; together they are not |

---

## 6. Findings neither document carries

**N-1 — under the juniper-ml launchers, F-3 is a 1.89× write amplification, not an ergonomics issue.**
The design classes F-3 as "a correctness/ergonomics fix, not a performance one."

**Scope, stated precisely — this applies to the harness, not to the deployed service.** The
juniper-ml launchers redirect the service's stdout into the log directory
(`juniper-ml/util/experiment_stack.bash:685`, `util/isolated_stack.bash:297`, and
`util/juniper_plant_all.bash:126`), so the unconditional `print()` writes every record to disk a
second time in a second format. The **deployed** paths do not: the systemd unit
(`scripts/juniper-cascor.service`) sets no `StandardOutput=` and inherits `journal`; the Docker
stanza in `juniper-deploy/docker-compose.yml` sets no `logging:` override, so stdout goes to the
daemon's json-file log outside the log dir; a terminal CLI run writes nothing extra.

**Magnitude, measured** (`~/.local/state/juniper-experiments/20260901T103548Z-befc/logs/`):

| sink | records | bytes |
| --- | --- | --- |
| `juniper_cascor.log.1` — file sink | 77,796 | 13,318,772 |
| `juniper-cascor.log` — stdout capture | 77,790 | 11,889,782 |

Record counts reproduce exactly; bytes differ because the console formatter drops the function name
(`constants_logging.py:157`). Removing the `print()` recovers **11.89 MB of the run's 27.07 MB — 44 %**,
i.e. **1.89×**, not 2×.

**The 3.3 GB resident figure is real but historical, and mostly a third harness.** Splitting
`juniper-cascor/logs/` by writer: the file sink's `juniper_cascor.log*` is 249 MB (the real log, not
recoverable); `juniper-cascor_*.log` — written by `juniper-ml/util/juniper_plant_all.bash:126` — is
3.23 GB, of which 2.10 GB is duplicated `+` records. Every one of those files is dated
**March–July 2026**, so this is accumulated stock, not a current accrual rate.

**The 637 MB is not established as being in this bucket.** #573 attributes it to a cap-64 **CLI** leg,
whose stdout reaches disk only if a launcher redirects it; that has not been checked.

Net: F-3 moves from ergonomics into the volume and I/O budget **for harness runs**, which is where
the experiment corpus is produced — but the claim must not be made about production.

**N-2 — the process model is forkserver, and the design reasons about fork.** Default context is
`forkserver` (`cascade_correlation.py:1103-1109`), with `set_forkserver_preload([... "logging",
"datetime", "cascade_correlation.cascade_correlation"])` (`:1114-1132`). Consequences the design
misses:

- A handle held by the **parent** is not inherited by a candidate worker at all; the child forks from
  the **forkserver**, not from the parent. D-2's "opened lazily on first write after fork" defends
  against a mechanism that does not apply.
- The real hazard is the mirror image: `cascade_correlation` is **preloaded**, so the forkserver
  process imports the logging tree. A handle opened at *import* or *forkserver* time **is** inherited
  by every child, with a shared file offset. Laziness is still load-bearing — but relative to
  forkserver start, not to fork.
- [cascor#569](https://github.com/pcalnon/juniper-cascor/issues/569)'s fork-safety audit certified the
  preload closure as creating "no import-time resource that a forked child would share". A persistent
  log handle would **invalidate that audited invariant**, so re-running
  `util/ad-hoc/2026-08-26_fork_safety_import_surface.py` is a landing gate, not a nicety.
- CPython **swallows a preload `ImportError`**, so a mistake here is a silent no-op verified only by
  the module census.

**N-3 — the guard predicate and the emit filter read DIFFERENT configured-level state, and
`set_level()` moves only the guard.** This is the sharpest finding in the document and it is
**measured, not read** — `util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py` imports the real
`Logger` at `70edfc4` and prints both paths side by side:

```text
--- after Logger.set_level('TRACE')
    _log_level          = 'TRACE'      get_level() = 'TRACE'
    _level_logger_name  = 'INFO'       EMIT-PATH effective level = 20
    isEnabledFor( 1) = True    _filter_by_level(TRACE) = False
    isEnabledFor(10) = True    _filter_by_level(DEBUG) = False
```

Two independent state variables:

- `set_level()` writes **only** `cls._log_level` (`logger.py:438-442`); `get_level()` reads it
  (`:448`); `isEnabledFor` reads `get_level()` (`:1042`). **The guard path.**
- `_log_at_level` resolves its threshold from `_level_logger_config` / `_level_logger_name`
  (`:516`), and **`_level_logger_name` is assigned once in the class body at import (`:164`) and is
  never written again anywhere in the repo**. **The emit path.**

So **`Logger.set_level(...)` — which `candidate_unit.py:188` and `:297` call on construction — is a
no-op for emission.** The only thing that moves the emission threshold is the environment variable
read at import (`constants.py:638-668`). Turning the level down opens every guard while the records
behind them are still discarded: the guards pay their branch and produce nothing.

**It is a performance defect, not an output defect.** Both `if _log_trace:` blocks
(`candidate_unit.py:604`, `:767`) contain only `.trace()` calls, so nothing an operator sees changes
— the process simply does the guarded work (argument evaluation, `.shape` calls, `_frm()`/`_tsp()`)
for records the emit filter then throws away. **No user-visible behaviour change needs announcing**,
which is the opposite of what a naive reading of "the guards are wrong" implies.

**This supersedes the simpler story.** The mis-numbered integers are real —
`isEnabledFor(level=5) # TRACE` (5 is VERBOSE), `isEnabledFor(level=8) # VERBOSE`, at
`candidate_unit.py:596-597`, `:764-766`, `:833-834`, `:1046` — **8 call sites**, not the 15
`if _log_*:` *use* sites they feed. Two qualifications:

- **`level=8` is wrong but behaviourally inert.** `8 >= L` and `5 >= L` differ only for
  `L ∈ {6,7,8}`, and `_level_numbers` contains none of those. It can never return a wrong answer;
  it is a readability defect.
- **`cascade_correlation.py`'s 7 hoists are already correct** — they pass `logging.DEBUG` /
  `logging.INFO`, symbolic and numerically right — and need no conversion.

So only `level=5 # TRACE` is live-wrong, and only at one configured level. The integers are the
second-order defect; the first-order one is that the predicate cannot agree with the filter,
whatever integer it is passed.

This is the migration analysis's own hazard §5.4 (level-gated failures hide) realised against the
idiom it recommends, one layer deeper than the analysis imagined.

**Consequence for the roadmap: a guard idiom cannot be recommended until the two level states are
reconciled.** Symbolic constants are necessary and *not sufficient* — a correct constant passed to
`isEnabledFor` still asks a different question than the emit filter answers.

**N-3a — `Logger.is_valid_level` returns `True` for every input.**

```python
return cls._is_valid_level_name(level=level) or cls._is_valid_level_number(level == level)
```

(`logger.py:341`.) `level == level` is `True`; `isinstance(True, int)` is `True`; and
`True in _level_numbers.values()` is `True` because `True == 1` and TRACE is 1. Verified:
`is_valid_level("BANANA") → True`, `is_valid_level(None) → True`. It is currently harmless only
because `_resolve_level_number` re-validates through `getLevelNumber`, which returns `None` for an
unknown name. **Any design that asks for loud failure on an unknown level name is unimplementable
until this is fixed** — the repo's only validity predicate cannot say no.

**N-3b — the level tables: two agree, one contradicts.** The earlier framing of "three contradictory
definitions" was wrong. `cascor_constants/constants.py:534-541` is the **canonical** numeric table
(`TRACE=1 … FATAL=60`) and `logger.py:92-93` **imports** `_LOGGER_LOG_LEVEL_NUMBERS_DICT` from it —
so it must not be deleted. `logger.py:233-242` hardcodes a **duplicate that agrees** with it; that is
the one to re-derive. Only `src/profiling/logging_utils.py:250-251` (`TRACE = 5`, `VERBOSE = 15`,
commented "match custom levels from log_config") actually contradicts.

**N-4 — the compatibility surface is the inverse of what the design protects.** Re-derived from the
consumers:

| surface | breaking? | consumers |
| --- | --- | --- |
| `[file.py: func:LINE]` prefix | **NOT breaking** | none — anchoring on it is a *documented prohibition* ("methodology rule 5") stated in four scripts after the 2026-08-20 incident. Searched for regex, `split`, `awk -F']'`, `cut -d']'` and `funcName` consumers; found none |
| **the `+` sentinel** | **BREAKING** | **2 scripts** — `juniper-ml/util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash:309` and `util/ad-hoc/2026-08-26_t6_stop_evidence_scan.py:103` both do `line.startswith("+")` to split **worker from parent** lines. It carries the orphaned-worker signal; remove or relocate it and `last_worker_ts` goes null **silently** |
| **Path A's absence of milliseconds** | **BREAKING** | the same 2 scripts use "no `,millis`" as the same parent/worker discriminator. **A "richer sink" that adds sub-second precision to Path A breaks them identically and silently** |
| `(YYYY-MM-DD HH:MM:SS)` timestamp | **BREAKING** | **6** scripts compile a regex and `strptime` it: 3 tolerate an optional `,millis`, **3 do not** — and the intolerant failure mode is a **silent skip** (`re.search` misses, the line is dropped), not an exception |
| anchored **message text** | **BREAKING** | ~17 juniper-ml scripts; #573's body states this as the rule, naming the **phase-split and determinism tooling** as the victims |
| `logs/juniper_cascor.log*` filename + rotation scheme | **BREAKING** | ~17 scripts glob it |

**All of this breakage is cross-repo — cascor's own CI stays green.** No test in `src/tests/` asserts
the record layout. That is the hazard: the guardrail must live in juniper-ml, not in cascor.

**The prefix exists in three places, not one**: `constants_logging.py:152` (Path A file),
`conf/logging_config.yaml:47` (Path B), and a **hardcoded third copy** at `api/observability.py:119`
(Path C). Any "hold the format stable" guardrail that scopes only Path A misses two of them.

Note also that Path A and Path B/C emit **different timestamp formats into the same file**, and 3 of
the 6 parsers cannot read the millisecond form.

**N-5 — mirroring `logger.py` breaks CI; not mirroring the rest breaks CI.** `_EXTRACTED_DIRS`
includes `log_config` (`test_drift.py:27`), so `log_config/__init__.py`, `log_config/log_config.py`
and `log_config/logger/__init__.py` are byte-gated and **must** be mirrored. But
`_INTENTIONAL_DIVERGENCE = frozenset({Path("log_config/logger/logger.py")})` (`:31`) exempts the
logger *and* `test_intentional_divergences_actually_differ` (`:104-117`) **asserts the two copies
differ**. Verified: `diff -q` reports they differ today. G-5 as written would fail the build.

**N-6 — 472 of the call sites are in dead files.** `src/cascade_correlation/backups/` is tracked and
imported by nothing: `cascade_correlation-ORIG.py` (430 logger calls) and `cascade_correlation_fix.py`
(42). Deleting the directory removes ~24 % of the migration surface at zero behavioural risk, and it
corrects the "36 % in two files" arithmetic.

**N-7 — `src/profiling/logging_utils.py` already implements the hot-path idioms, and is dead.** It
provides `SampledLogger`, `BatchLogger` and `LogFrequencyTracker`, headed *"P4-NEW-004: Reduce Debug
Logging in Hot Paths"*, and its module docstring demonstrates the `isEnabledFor` guard. Its only
importer is `src/tests/unit/test_profiling_module.py`. Any proposal for sampling or batching must
start by deciding this module's fate rather than rebuilding it.

**N-9 — three writers share one filename, and exactly one of them rotates it.** This answers the
design's §6-c ("log rotation already happens", mechanism unexplained). The rotator is **Path C**:

```python
log_file = log_dir / "juniper_cascor.log"                 # api/observability.py:109
file_handler = RotatingFileHandler(str(log_file),
    maxBytes=_LOGGER_LOG_FILE_MAX_BYTES,                  # 10 MB
    backupCount=_LOGGER_LOG_FILE_BACKUP_COUNT)            # 5
```

(`constants_logging.py:276-277`.) That is the **same path** Path A appends to per record and Path B's
`FileHandler` holds open. Consequences:

- Path A opens by name every record, so it survives a rollover by re-creating the file.
- **Path B holds a descriptor.** After Path C renames the file, Path B keeps writing to the renamed
  inode — its records continue landing in `juniper_cascor.log.1` and disappear from the live file.
- Path C renames a file two other writers are actively appending to.

The code already knows: `_resolve_log_dir`'s docstring (`api/observability.py:55-57`) justifies the
`JUNIPER_CASCOR_LOG_DIR` override as avoiding *"the checkout-shared `<repo>/logs` that concurrent
cascor processes interleave and **rotate away**."* The design's own §6 notes that "any analysis that
reads only `juniper_cascor.log` silently misses records — it has already caused one truncated
analysis." This is the mechanism behind that.

**Why the rollover fires late, and why the live file is nearly empty.** `RotatingFileHandler` checks
size **only when it emits**. Path C emits ~21 records per run while Path A writes ~78,000 outside its
accounting, so the check is consulted ~21 times against a file being inflated out of band. That
explains both observations in §3 at once: the rotated `.1` is **15,161,801 B against a 10 MB
threshold** (and `logs/` holds files at 41 MB and 129 MB), and the live `juniper_cascor.log` is
**2,122 B of 21 non-`+` records** — Path C rolled over and then wrote only its own handful of records
into the new file. Two independent reviewers reached this mechanism from the same artifacts.

**N-8 — the test net exists but the emit path is stubbed out for the whole suite.** There are
~1,441 lines of logger tests — `test_logger_coverage.py` (723), `test_logger_extended.py` (569),
`test_logger_frame_resolution.py` (149) — plus `test_log_config_coverage.py`,
`test_logging_utils_extended.py` and `test_cfg_05_log_level_resolution.py`. **But**:

```python
@pytest.fixture(autouse=True, scope="session")        # src/tests/conftest.py:870
def _cache_logging_system():
    ...
    @classmethod
    def _noop_log_at_level(cls, **kwargs):
        pass
    Logger._log_at_level = _noop_log_at_level          # conftest.py:924-926
```

**`Logger._log_at_level` is replaced by a no-op for the entire pytest session**, autouse, session
scope, no opt-out. Every filter decision, every `print()`, every `open()`/`write()` — the whole emit
path — is unreachable from the suite. None of these tests assert the on-disk record format either
(N-4).

This is the vacuous-pass class: **any acceptance criterion of the form "the existing suite is green"
says nothing about the emit path**, and the roadmap must not use one. It is also a live candidate
mechanism for the design's §7.1 swallowed-pytest problem, which has never been investigated.

---

## 6.1 The pre-#598 baseline, carried forward verbatim

Phase 0 re-measures against these. A re-measurement with no prior cannot show movement, so the
numbers are restated here rather than left in a document Phase 0's author may not open.

From GATED §3, over 84.96 s of worker self time at `67d7ea35`:

| component | calls | time | share | paid for |
| --- | --- | --- | --- | --- |
| `Tensor.__format__` chain | 2,262 → 1.81 M | 27.98 s cum | 33 % | **emitted records only** |
| `_filter_by_level` | 646,016 | 11.19 s | 13.2 % | every call — 91 % discarded |
| `strftime` | 116,798 | 0.99 s | 1.2 % | emitted only |
| `currentframe` (eager) | 646,016 | 0.87 s | 1.0 % | every call |

Logger calls by level, exact and complete (sums to 646,016):
**`trace` 264,784 · `debug` 264,223 · `verbose` 58,610 · `info` 58,399.**

**91.0 % of logger calls are discarded** (587,617 of 646,016) at INFO.

Two controls that make the §3 finding checkable, and that support N-3:

- **Arithmetic confirmation**: the run log contains **1,131** emitted `Norm Output:` lines × 2 tensors
  = **2,262** attributed `__format__` calls — exactly the attributed count, not an inference.
- **The log contains zero VERBOSE records**, so the neighbouring unguarded `logger.verbose` line
  contributed nothing. This is also the direct evidence that N-3's mis-numbered guards are **latent
  at the production level** rather than actively mis-emitting.

### The residual uncertainty, restated because Phase 0 depends on it

GATED §3 states a limit on its own instrument, and it constrains what Phase 0 can promise:

> f-string *construction* cost for the 587,617 discarded records is inline in each calling function's
> own self time and is therefore **not separately attributable** from this corpus… A true bound would
> need a build with the log calls removed outright, which is not cheaply obtainable; raising
> `CASCOR_LOG_LEVEL` does **not** measure it, because arguments are evaluated at the call site
> regardless of level.

**Two consequences.** (1) Caller attribution can give the *emitted* share and the discard *count*, but
**not** the construction cost of discarded records — so no phase may set that as an acceptance
criterion. (2) The disabled-logging A/B was **already considered and rejected**: it gives total
logging cost but "cannot separate discarded from emitted records, which is precisely the split that
was being asked for." The design's §5 still proposes it un-retracted at the sentence level; it should
not be reached for.

## 7. What is unmeasured, and therefore gates the roadmap

1. **The composition of the remaining 43.20 s of worker self time.** No post-#598 corpus exists.
2. **The post-merge value itself.** #598's number is a pre-merge branch measurement.
3. **Volume, per record and per run.** 4.8 MB/run typical, 27 MB observed, 637 MB at cap 64, 3.3 GB
   resident — but bytes-per-record and the duplication factor are not characterised.
4. ~~**Which mechanism rotates `juniper_cascor.log`.**~~ **ANSWERED — N-9.** Path C's
   `RotatingFileHandler`, 10 MB / 5 backups, on the file all three paths share. What remains
   unmeasured is *why the rollover fires 52 % late*, and how many Path-B records are lost to a
   held descriptor after a rename.
5. **Whether Path A records can tear** under concurrent forkserver-child appends.
6. **The swallowed-pytest mechanism** (design §7.1), untouched.

---

## 8. Consensus record

Per [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).
Sizing: **high criticality** (documents of record; overturns standing conclusions) × **medium
uncertainty** (direct code reads, but conclusions that invert prior ones) → 2 Lane A + Lane B.

**Lane A — two agents, deliberately different entry points**, neither reading the two documents under
review: (a) the **code tree** across all repos, for the ecosystem inventory; (b) **git/GitHub/disk
history**, for the redesign's provenance and consumer surface.

**Re-derivation, not acceptance.** Every finding an agent returned that changes a verdict was
re-derived first-hand before being written here: the `_INTENTIONAL_DIVERGENCE` allowlist and its
reverse guard (§6 N-5), the absence of any `[file.py: func:LINE]` parser (N-4), #573's state and body
text, the level-number contradiction (N-3), and the forkserver default (N-2). The double-write (N-1)
and the dead `backups/` tree (N-6) were found first-hand and not by either agent.

**Universal quantifiers used here, and how each was tested**: "nothing parses `[file.py: func:LINE]`"
— `grep -rn 'func:'` over `util/` returns only Sphinx `:func:` docstring cross-references.
"No repo outside cascor imports the Logger" — `grep -rl 'from log_config'` over six repos, empty.
"Zero `.format()` in a log call ecosystem-wide" — from the inventory sweep; a single-line regex, so it
would miss a call split across lines.

**Lane B — three reviewers, three lenses** (factual over-generalisation; amputation; executability),
each briefed that "a finding that this is sound is worth nothing." Round 1 changed this document
materially and the changes are recorded in place, not appended:

| what round 1 overturned | how this document changed |
| --- | --- |
| N-3's mechanism | **rewritten.** Two reviewers independently found that `isEnabledFor` and `_filter_by_level` read **disjoint state**, and that `set_level()` is a no-op for emission — a larger defect than the wrong integers, found by *running* the logger rather than reading it |
| N-3's manifestation | **reversed.** "Emits TRACE-guarded blocks at VERBOSE" is false; the guarded blocks contain only `.trace()` calls. It is a performance defect with no output change |
| N-1's scope | **narrowed.** The deployed service does not redirect stdout into the log dir; only the juniper-ml launchers do. Magnitude corrected 2× → **1.89×**; the 3.3 GB attributed to a third harness and marked historical |
| N-4's `+`-sentinel row | **reversed.** Two scripts *do* consume it, and also consume Path A's *absence* of milliseconds — so a "richer sink" adding sub-second precision breaks them silently. Timestamp parsers recounted 5→**6** |
| N-8 | **reversed.** A session-scoped autouse fixture stubs `Logger._log_at_level` to a no-op, so "the suite is green" is vacuous for the emit path |
| §3's Path-A reach | **corrected.** `src/api/`'s 250 sites are stdlib-bound, so a call-site count is not a Path-A count |
| §4 §6-a, §5 "36 %", §5 Q2, §5 G-5, §4 D-1 | **verdicts softened.** Each was over-harsh: the original was right about more than the verdict allowed, and in the "36 %" case the correction *strengthens* the claim it was attached to |
| §2 "nothing decomposes it" | **withdrawn.** #598's PR body decomposes `_filter_by_level` post-fix at 1.20 s / 2.8 % |
| dropped inheritance | **restored** as §6.1 — the pre-#598 baseline table, per-level histogram, 91 % discard rate, the arithmetic control, and GATED's residual-uncertainty limit |

**Round 2** is briefed on these corrections specifically, per the procedure's rule that the fix pass
is the least trustworthy part of any document.

---

## 10. References

- [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) — the issue; owner scope, the message-text anchoring rule, the 637 MB leg. **OPEN, zero comments, untouched since 2026-08-24**
- [cascor#598](https://github.com/pcalnon/juniper-cascor/pull/598) (`64ff9ab8`) — the shipped remediation and its post-fix numbers
- [cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563) — the `inspect` fix; banked, unavailable to this work
- [cascor#579](https://github.com/pcalnon/juniper-cascor/issues/579) — where the "~30 % is logging-related" brief actually lives
- [cascor#569](https://github.com/pcalnon/juniper-cascor/issues/569) / [#570](https://github.com/pcalnon/juniper-cascor/issues/570) — the forkserver fork-safety audit and module census
- `juniper-ml/reports/measurements-2026-08-29/format_caller_attribution.txt` — the caller attribution behind §6.1
- `juniper-ml/reports/perf-lane-post-fix-2026-08-26/worker_profile_*` — the post-#563 corpus
- `~/.local/state/juniper-experiments/census-at67d7ea35/prof` (32 profiles, 2026-08-26) — pre-#598 corpus
- `~/.local/state/juniper-experiments/logfix-verify/prof` (32 profiles, **2026-08-30 01:59**, twelve minutes pre-merge) — the #598 headline's corpus
- `juniper-ml/util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py` — the N-3 probe
- 2026-08-24 handoff §4.13 (per-record `open`, unconditional `print`) and §6 (swallowed pytest)
- [`JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md`](JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md) §8 — #563's fix design
