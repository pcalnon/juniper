# HANDOFF — logging redesign arc: documents merged, no phase started

- **Date**: 2026-09-07
- **Arc**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) — logging redesign
- **Predecessor**: the 2026-09-02 reconciliation + roadmap session, merged as [ml#1573](https://github.com/pcalnon/juniper-ml/pull/1573) (squash `53ec93e9`)
- **This document lives in**: `juniper-ml/.claude/worktrees/bubbly-shimmying-seahorse`, branch `docs/handoff-logging-redesign-arc`
- **Freshness**: re-verified against juniper-ml `origin/main` `ef73443f` and juniper-cascor `origin/main` `1ea2062` on 2026-09-07

**Documents REFERENCED** (short names used throughout, full filenames here once):

| short name | filename, all under `juniper-ml/notes/` |
| --- | --- |
| **ROADMAP** | `JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` |
| **RECON** | `JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md` |
| **DESIGN** | `JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md` |
| **ANALYSIS** | `JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md` |
| **GATED** | `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md` |
| **CONSENSUS** | `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` |

**Documents CHANGED by this handoff**: this file only.

---

## 0. PREFLIGHT

1. **Read ROADMAP end to end**, then **RECON §2, §3, §6, §6.1 and §7**. §7 is titled *"What is unmeasured, and therefore gates the roadmap"* — it defines Phase 0's job.
2. **DESIGN and ANALYSIS are corrected, not retired.** DESIGN carries **8** inline `CORRECTION 2026-09-02` markers (lines 138, 189, 224, 245, 280, 300, 315, 330; a ninth occurrence at line 19 is the legend). ANALYSIS carries **4** (lines 89, 261, 275, 293). **Only those passages are superseded** — the rest, notably DESIGN §7 and §7.1, stands.
3. **Two different decision sets exist and they are both numbered 1–6.** See §2. Getting these confused will send you at the wrong work.
4. **Run the probe with the level vars unset** (§11). Exported `JUNIPER_CASCOR_LOG_LEVEL` produces a **false negative** that looks like "the defect is fixed" — see §11's warning.
5. **The arc is owner-blocked.** Six of seven ROADMAP §13 decisions are unanswered. §3 states them so you can ask in one message rather than reading them out of a document.

---

## 1. Standing constraints

- **Merges require Paul's explicit approval, per PR.** The blanket approval given in the 2026-09-02 session covered *that* arc. Do not self-approve.
- **Deploy / PyPI / environment gates are Paul's.** Never auto-approve one.
- Commit trailers: `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` and the session URL. PR bodies get the Claude Code footer.
- **Scripts go in `util/` or `util/ad-hoc/`. `/tmp/` is prohibited** for script source.
- Never bare `git stash` / `git stash pop` — the stack is shared across worktrees.
- **`gh` here is 2.46.0**: `gh pr checks --json` does not exist, and **all** `gh pr edit` flags are broken. Use `juniper-ml/util/wait_for_checks.py` for waiting and the API for PR-body edits.

---

## 2. Goal statement

Continue the **juniper-cascor logging redesign** ([cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)). Design work is finished and merged; **no implementation phase has started**, and the arc is **blocked on six owner decisions** (§3).

**Completed:**

- **RECON** — created. Verdict on every substantive claim in DESIGN and ANALYSIS; a call-site census with its method caveats; the pre-#598 measured baseline (reproduced in §6 below); nine findings N-1…N-9.
- **ROADMAP** — created. Eight phases P0–P7, 30 numbered steps, 32 named guardrails, five traps, critical path, rollback and release obligations, seven owner decisions.
- **DESIGN** and **ANALYSIS** — correction markers added, narrowing rather than deleting.
- `util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py` — the instrument that found the central defect.
- Consensus: Lane A two entry points, Lane B three lenses, then round 2 on the corrections (24 further defects).

**Remaining:** every phase. P0 through P6 are untouched; P7 is deferred by design. See §9 for what is explicitly **not** remaining work — "all of it" would be wrong.

**Key context — the four things that most change what you do:**

1. **The central finding is a state split, verifiable only by probe.** `Logger.isEnabledFor` reads `_log_level`; `_log_at_level`'s filter reads `_level_logger_config` / `_level_logger_name`; `set_level()` writes only the first, and `_level_logger_name` is assigned once in the class body (`logger.py:164`) and never written again. A correct guard and a broken guard produce the **same log**.
2. **The process model is `forkserver`, never `fork`** — and the actionable half is the mechanism, not the headline: a parent-held handle is *not* inherited; the hazard is that `cascade_correlation` is **preloaded**, so a handle opened at import or forkserver time **is** inherited with a shared offset. A persistent handle invalidates [cascor#569](https://github.com/pcalnon/juniper-cascor/issues/569)'s fork-safety certification. CPython **swallows** a preload `ImportError`.
3. **The compatibility surface is inverted from what DESIGN protects.** Nothing parses `[file.py: func:LINE]`.
   What breaks: the `+` sentinel (2 consumers), the timestamp (6 parsers, **3 intolerant**, failing by *silent
   skip*), anchored **message text** (~17 scripts), the log filename glob (~17 scripts). The prefix exists in
   **three** places — `constants_logging.py:152` (Path A), `conf/logging_config.yaml:47` (Path B),
   `api/observability.py:119` (Path C) — so a guardrail scoped to Path A misses two. **All breakage is
   cross-repo; cascor CI stays green.**
4. **"The suite is green" verifies nothing about emission.** See §7's P0.5 — the fixture stubs **three** seams, and one of them makes the eight guard sites unreachable by any test.

**Claim limits, verbatim from ROADMAP §1** — carry these into any PR body or issue comment:

1. Do **not** re-claim [cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563)'s 9× or [cascor#598](https://github.com/pcalnon/juniper-cascor/pull/598)'s 49 %. **Both are banked.**
2. No number in the revised priority order still describes the build — except `_filter_by_level` at 1.20 s / 2.8 %, **and that is a pre-merge branch measurement** (see §6).
3. A format change is not safe because cascor CI is green.
4. "The existing test suite is green" verifies nothing about emission.

---

## 3. The two decision sets, and the six open questions

**DESIGN §7 decisions 1–6 are SETTLED (2026-08-29) and still binding.** Do not re-open them:

| # | settled decision |
| --- | --- |
| 1 | Measure before building |
| 2 | **Flush per record** — *"a complete log for a crashed run outweighs the throughput; a truncated log is how several analyses in this arc went wrong"* |
| 3 | Per-process file handle, opened lazily — **premise refuted** (it says "after fork"; read "after forkserver start"), never formally re-issued |
| 4 | **Console stays on stdout** (provisional) |
| 5 | Call-site migration scope **deferred, and reserved to the owner** — this is ROADMAP §13 decision 6 |
| 6 | JSON via `juniper-observability` — **already violated deliberately**; `api/observability.py:75-119` is a local fork |

**ROADMAP §13 decisions 1–7 are the OPEN set.** §13.1 is a response slot: `.` means unanswered. Only 7 is answered. **Everywhere below, "decision N" means ROADMAP §13 N.**

| # | the question | what it gates | answer |
| --- | --- | --- | --- |
| 1 | **Does P2 run at all?** Pre-authorise "drop P2 if the logging share is below X %" | all of P2; lets P0 close cleanly | open |
| 2 | **P3.2's default** — console sink on or off? Roadmap recommends **on by default, off in the harness profile**. A *policy* switch, **not** runtime detection | all of P3.2 | open |
| 3 | **P5.1** — upstream / keep / **narrow the fork (recommended)** | P3.1 and P3.3 | open |
| 4 | **P0.6 / mirror** — is `juniper-cascor-model`'s logger backported in Wave 2, or frozen? | every P1 and P4 edit carries an undefined obligation to a second tree **and a published package** until answered | open |
| 5 | **P4.1** — per-instance loggers, or named sub-loggers on the class? Per-instance de-classmethods `isEnabledFor` and breaks **~1,200 call sites** | whether P4 is M or L | open |
| 6 | **Call-site migration scope** (= DESIGN decision 5). ROADMAP **schedules P6 but does not take the decision**; *"it must not become planned work by default"* | P6.2 and P6.4 | open |
| 7 | **§7.1 swallowed-pytest investigation** | nothing — explicitly not a blocker | **ANSWERED: "i concur. let's run the investigation as written."** |

**Ask 1–6 in one message.** The arc is waiting on the owner, not on more analysis.

**On decision 7's investigation**: the symptom is *pytest summary lines vanishing from local runs*, recorded
in
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-24_determinism-zero-and-perf-lane-open-surface.md`
§6. DESIGN §7.1 is **uncorrected** — follow it as written: reproduce the disappearance, then distinguish
pytest capture, a `capsys`/`-s` interaction, the logger's `print`, and stream buffering, **and only then**
propose a fix. Current anchor for the `print`: `src/log_config/logger/logger.py:523` (DESIGN cites `:475`,
which has drifted — anchor on the `print(f"+{_console_message(...)}")` text).

---

## 4. State at handoff

**Stable** (re-verify only if something looks wrong):

| item | state |
| --- | --- |
| Implementation | **none** — zero phases started |
| cascor `src/log_config/`, `src/candidate_unit/`, `src/tests/conftest.py`, `src/api/observability.py` | **untouched** across the 12 commits `70edfc4..origin/main` |
| Documents | all four on ml `main`; only header-format normalisation and the addition of ROADMAP §13.1 since the merge |

**Volatile — re-measure, do not trust:**

| item | value at 2026-09-07 |
| --- | --- |
| juniper-ml `origin/main` | `ef73443f` |
| juniper-cascor `origin/main` | `1ea2062` |
| cascor#573 | OPEN, **0 comments**, `createdAt == updatedAt == 2026-08-24T00:29:11Z` |
| In-flight logging work | none in either repo |

> **The primary checkouts are routinely behind `origin/main`** — at time of writing, juniper-ml by 11 commits and juniper-cascor by 3. Always `git fetch` and compare against `origin/main`, never the local `main` ref.

---

## 5. Anchors, re-verified 2026-09-07 at cascor `1ea2062`

| anchor | location | verified |
| --- | --- | --- |
| `is_valid_level`'s `level == level` typo | `src/log_config/logger/logger.py:341` | yes |
| `_level_logger_name` assigned once, never rewritten | `src/log_config/logger/logger.py:164` | yes |
| `isEnabledFor(level=` sites | `src/candidate_unit/candidate_unit.py:596,597,764,765,766,833,834,1046` — **8** | yes |
| the `_cache_logging_system` fixture | `src/tests/conftest.py:871-935` | yes |
| the `configure_logging` fork | `src/api/observability.py:75-119` | yes |
| Path C's rotator | `src/api/observability.py:110-115`, 10 MiB / 5 backups | yes |

**Anchor on the quoted text, not the number.** DESIGN's `:475` for the `print` has already drifted to `:523`.

---

## 6. The measured baseline — inlined deliberately

RECON §6.1 says these were inlined *"because Phase 0's author may not open the upstream document."* The same reasoning applies one level up, so they are here too. **A re-measurement with no prior cannot show movement.**

Pre-#598, over **84.96 s** of worker self time at `67d7ea35` (32-profile cap-4 corpus, `~/.local/state/juniper-experiments/census-at67d7ea35/prof`):

| component | calls | time | share | paid for |
| --- | --- | --- | --- | --- |
| `Tensor.__format__` chain | 2,262 → 1.81 M | 27.98 s | 33 % | **emitted records only** |
| `_filter_by_level` | 646,016 | 11.19 s | 13.2 % | every call — 91 % discarded |
| `strftime` | 116,798 | 0.99 s | 1.2 % | emitted only |
| `currentframe` (eager) | 646,016 | 0.87 s | 1.0 % | every call |

Logger calls by level, exact and complete (sums to 646,016): **`trace` 264,784 · `debug` 264,223 · `verbose` 58,610 · `info` 58,399**. **91.0 % of calls are discarded** (587,617 of 646,016) at INFO.

Two controls that make the finding checkable: **1,131** emitted `Norm Output:` lines × 2 tensors = **2,262** attributed `__format__` calls (attributed, not inferred); and **zero VERBOSE records** in the log — which shows the *emit* threshold was INFO and says **nothing** about guard state, since the two read separate values.

**Post-#598 and pre-merge — this caveat travels with the numbers.** Worker self time **84.96 s → 43.20 s**, `_filter_by_level` **13.2 % → 2.8 %** (1.20 s / 746,410 calls). But: the corpus did **15 % more** logger calls, so the −49 % is approximate; it was measured on the branch build **twelve minutes before merge**; and `find ~/.local/state/juniper-experiments -name '*.prof' -newermt "2026-08-30 02:11:01"` returns **zero**. **No post-merge corpus exists.**

**A limit on what P0.2 may promise** (GATED §3, restored clause included): f-string *construction* cost for
discarded records is inline in each caller's self time and is **not separately attributable** from this
corpus. *"It is bounded small by the finding that the only expensive interpolation in the hot path — tensor
formatting — is entirely in the emitted INFO line."* So: **promise no number**, but do not treat it as
unknown. And the **disabled-logging A/B was already considered and rejected** — it gives total cost but cannot
separate discarded from emitted. Do not reach for it.

**Volume** (RECON N-1, scope caveat included): under the **juniper-ml launchers only** — not the deployed
service, where systemd inherits `journal` and Docker sets no `logging:` override — every Path-A record is
written to disk twice. Measured: 77,796 records / 13,318,772 B in the file sink against 77,790 / 11,889,782 B
in the stdout capture — **44 % of a run's log bytes**, a **1.89×** Path-A amplification. The 3.3 GB resident
figure is a **third** harness (`juniper_plant_all.bash:126`) and is **historical** (Mar–Jul 2026). The 637 MB
cap-64 figure is **not** established as being in this bucket.

**Still unmeasured, and therefore gating** (RECON §7): the post-merge value itself; bytes per record and per run; **why Path C's rollover fires ~45 % late** and how many Path-B records are lost to a descriptor held across the rename; **whether Path A records can tear** under concurrent forkserver appends.

---

## 7. Where to start

**Head of the critical path — start here.** ROADMAP §2.3: *"Do not schedule P1 as the cheap early win; schedule P0.4 and P5.1."*

- **P0.4 — the envelope + marker harness** (ROADMAP §3.1). No dependencies. It is the **landing gate for every
  P2 item** (P2-G1) and P3/P6 inherit it. Four parts beyond the obvious: (a) **two** reference captures, file
  sink and redirected-stdout sink, because their formats and flush semantics differ; (b) the envelope checker,
  including timestamp **precision**; (c) a **named-marker inventory** — the half that matters most, because an
  envelope check *passes* a message-text change and message text is BREAKING for ~17 scripts; (d) the
  enforcement mechanism — a juniper-ml-sited test **cannot fail a cascor PR** (separate repos, no status-check
  propagation), so prefer a **cascor-side** golden over the formatter strings in all three locations; (e) CI
  wiring in the same PR — juniper-ml's test list is hand-maintained and `tests/test_ci_test_wiring_drift.py`
  fails otherwise.
- **P0.5 — characterise the stubbed emit path.** Pure code read. **The fixture stubs three seams, not one**:
  `src/tests/conftest.py:871-935`, `_cache_logging_system`, autouse + session scope —
  `CascadeCorrelationNetwork._init_logging_system` → `_fast_init_logging_system` (`:892`);
  `CandidateUnit.__init__` **and** `__setstate__` → `self.logger = _noop_logger` (`:898`, `:914`);
  `Logger._log_at_level` → no-op (`:921-927`). **The `CandidateUnit` seam is the one that matters most** — the
  eight guard sites are `self.logger.isEnabledFor(...)`, so with `_noop_logger` in place **no test exercises
  them**. Characterising only the third seam produces a false all-clear. Deliverable: a per-phase table of
  invalidated acceptance criteria — agree with the owner whether it lands as a ROADMAP §3 subsection or its own
  notes document.
- **P5.1 — adjudicate the fork.** This *is* decision 3, so **produce the adjudication and its recommendation; do
  not implement it.** Options: (a) upstream into `juniper_observability.configure_logging` — **note this deletes
  the only rotator**, since the shared library has no file sink; (b) keep the fork, documented, re-using only
  `JuniperJsonFormatter`; (c) **narrow to the delta — recommended**. Any option moves the handler-set state that
  `Logger.__init__:768` tests, which decides whether Path B attaches a second handler to the same file. The
  affected suite is `src/tests/unit/test_api_observability.py:89,:97,:114`, all asserting `len(root.handlers) ==
  2`.
- **Decision 7's investigation** — authorised. See §3.

**Also unblocked, but needing a slot or a decision:**

- **P0.1** (post-merge 32-profile cap-4 corpus) and **P0.3** (volume census) — no dependencies, but
  **live-stack**: they need a GPU slot, a distinct `JUNIPER_CASCOR_LOG_DIR`, and reaper protection (§10 trap 1).
  P0.1(c) must **record the cell identity** — suite path, `max_hidden_units`, dataset seed, experiment seed,
  base config, arm — because a profile *count* is not a cell identity (cap 8 × pool 4 also yields 32). Be
  prepared for the pre-#598 cell to be **unreconstructable**: `logfix-verify/` holds only `prof/`, no config or
  manifest, and `grep -rln 'logfix'` across juniper-ml returns nothing. If so, say so explicitly rather than
  comparing a known cell to an unknown one.
- **P6.1** (delete `src/cascade_correlation/backups/`) — `depends on: —`, and worth **472 sites / ~24 %** of the migration surface at zero behavioural risk. But it is **not free** (§10 trap 2) and it sits under decision 6, so confirm it is separable before starting.
- **P1.1 / P1.2** — `depends on: —`. Unblocked but **deprioritised and serialised**: P1 is L not M, its edits contend with P4.3 across four byte-gated trees, and it delivers no observable change. P1.2's target is specific — `cascor_constants/constants.py:534-541` is **canonical and imported** by `logger.py:92-93`, so **keep it**; re-derive the agreeing duplicate at `logger.py:233-242`; only `profiling/logging_utils.py:250-251` contradicts.

**Genuinely blocked:** P2 (may not *land* without P0.4 green per P2-G1; whether it runs at all is decision 1, sized by P0.2) · P3.1 (P0.4, P2, P5.1) · **P3.3 (P0.3, P3.1, P5.1 — note P0.3, a live-stack step)** · P3.4 (P3.3) · P4.1–P4.3 (**P1.1 only**, and they may run parallel to P3) · P4.4 (P4.2 **and P3.4**) · P6.2–P6.4 (P0.4, P1, P2, and decision 6).

---

## 8. Phase content not to lose

- **P1**: the two-state reconciliation (P1.1a–d, including the `is_valid_level` typo, which makes P4-G4's "fail
  loudly on an unknown level" *unimplementable* until fixed); **P1.4** — disposition
  `src/profiling/logging_utils.py`, which already implements `SampledLogger` / `BatchLogger` /
  `LogFrequencyTracker`, is imported only by its own test, and is the third level table: **decide its fate
  rather than rebuilding it**; **P1.5** — the per-level exercise test, blocked on P1.1 because until one value
  drives both paths there is no runtime way to set the emission level.
- **P2**: **seven** closures per record, not two — six per emitted record plus `_get_log_level`'s lambda, built
  **before** the filter and therefore paid on the 91 % discarded. P2.1(c): **preserve `_frame_info`'s one-hop
  contract** by passing `cls._frm().f_back` from `_log_at_level`; `test_logger_frame_resolution.py` calls
  `_frame_info` **directly** at `:71,:90,:104,:109` and is P2.1's **only** detector — rewriting it to
  accommodate the change leaves the step with none. **P2.4 is deliberately absent; it belongs to P4.2** (round 1
  found the same edit filed twice).
- **P3**: P3.1(b) — **fix the shadowed binding first**: `logger.py:136` sets `_file_name = "file"`, `:155`
  overwrites it with `"filename"`, so a registry keyed on it registers a sink named `"filename"`. P3.2 — an
  **explicit** switch; do **not** condition on "stdout is redirected", because `isatty()` is false for a
  redirect *and* a pipe *and* systemd. P3.4 — **`O_APPEND`** (the one constraint the consensus record shows was
  dropped once and restored), lazy open relative to **forkserver start**, preserve create-on-demand and the
  `FileNotFoundError` retry, and **stat-and-reopen or `copytruncate`** so a held descriptor survives P3.3's
  rollover.
- **P4**: the precedence chain (per-logger env → global env → per-logger config → global config → default); `JUNIPER_CASCOR_LOG_LEVEL` is canonical and `CASCOR_LOG_LEVEL` deprecated under CFG-05 — **do not invent a second convention**; P4.4 must demonstrate **in a forkserver child**.
- **P6**: the three `%`-conversion hazards — a literal `%` raises at emit time inside logging, in a forked
  worker, at a level off in testing and on in production; a dropped format spec **silently changes precision**,
  which is a *downstream parsing change*; a lone tuple argument splats. P6-G1 is **not** discharged by P1.5 — it
  requires exercising every **converted site** at its own level. P6-G4: say which `__format__` population you
  are quoting (1,813,318 for `Tensor.__format__` alone; 3,626,636 for the matched-callee set).
- **Rollback**: P1.3, P3.2, P3.4 and P5.1 change a shared on-disk artifact. A revert after a corpus is generated leaves a **mixed corpus with no marker** — put a version token in the first record.
- **Release**: every byte-gated edit carries a mirror re-extraction **and a `juniper-cascor-model` package release** before `juniper-cascor-worker` sees it.

---

## 9. Not remaining work

Reproduced from ROADMAP §1 and §12 so "remaining work" is not read as "everything":

- **The ELK/Kibana shipper** — deferred (P7). Its latent conflict: lazy message callables (ANALYSIS Option D) and a queued writer are **mutually unsafe** and must not be adopted independently — relevant now, because Option D is a call-site idiom P6 could adopt.
- **Converging Path B into Path A** — explicitly out of scope.
- **A full 879-site f-string sweep** — Option B, **refused** twice.
- **canopy's custom logger and its dead `CASCOR_*_LOG_LEVEL` overrides; `juniper-service-core`'s unread `JUNIPER_SERVICE_LOG_LEVEL`** (150 emit sites); **canopy accepting `CASCOR_*` names for a non-cascor service** — three verified findings that belong in issues, not in this arc.

---

## 10. Traps

1. **Two cascor processes sharing a checkout destroy each other's logs** — stated in-source at
   `juniper-cascor/src/cascor_constants/constants.py:422-427` with a named incident. Every live-stack step needs
   a **distinct `JUNIPER_CASCOR_LOG_DIR`** *and* reaper protection: `juniper-ml/util/reap_pytest_orphans.bash`
   treats reparenting to `systemd --user` as the orphan predicate while the stack launches under `nohup`, so a
   multi-hour cell can be killed mid-run. Protection keys: the pid in a run-dir `*.pid`, or a cmdline referencing
   the run root.
2. **The byte-gate covers four trees, not one file.**
   `juniper-cascor/juniper-cascor-model/tests/test_drift.py:27` — `_EXTRACTED_DIRS = ("candidate_unit", "utils",
   "log_config", "cascor_constants")`, `_NORMALIZED_DIVERGENCE` now empty. **Serialise all work in those four
   trees.** The single exception is `log_config/logger/logger.py`, on `_INTENTIONAL_DIVERGENCE` (`:31`) — it must
   **NOT** be mirrored, and a reverse guard fails if the copies become identical. Also: pre-commit's black covers
   `src/` only, so it reformats one side of a byte-gated pair — **re-sync after the final pre-commit run.**
3. **Deleting `backups/` (P6.1) blocks the PR, not just main.** `Sequence Safety` is a **required status check**
   on cascor `main` (verified against the ruleset — note `sequence-safety.yml`'s own header comment claims it is
   "never a required context", which is **stale**), and `main-verify.yml`'s screen always runs post-merge. The
   waiver is `Allow-Symbol-Loss:` taking a **comma-separated symbol list**; **`*` is explicitly rejected**, and
   `cascade_correlation-ORIG.py` alone has ~76 top-level defs. The checker reads the **concatenated messages of
   the whole base..head range**, not one commit's final paragraph — though writing it as the last paragraph of
   one commit errs safe. Also decide `src/backups/check.py` (~68 sites, **untracked**, invisible to `git grep`,
   survives a tracked-tree deletion).
4. **P3.3 (rotation owner) before P3.4 (persistent handle)** — and ordering alone is not sufficient; P3.4 must implement stat-and-reopen or `copytruncate`. **The defect exists today**: Path C rotates the file Path B holds open, so Path B's records land in `.1` and vanish from the live file. That is why a run's live `juniper_cascor.log` is ~2 KB while `.1` is 15 MB.
5. **The mirror gate is one-directional** — `juniper-cascor/juniper-cascor-model/tests/test_drift.py:78` walks the **package** tree, so a file existing only in `src/` is never compared. P3.1 adds a module; add it to the package tree in the same PR.
6. **Unresolved CodeQL threads block a merge while every check reads green.** ml#1573 hit this at 17/17 required contexts with `mergeStateStatus: BLOCKED`, on one unused-import alert. Fix the finding; do not `noqa` it.
7. **Do not hand-roll a CI poll loop** — use `juniper-ml/util/wait_for_checks.py`. The predecessor session hand-rolled one on `gh pr checks --json`, which this `gh` does not support; the fallback returned an empty array and the loop reported "no pending checks". A probe that cannot observe a failure must exit non-zero, not report success.

---

## 11. Verify the starting state

```bash
# --- juniper-ml ---
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin
git merge-base --is-ancestor ef73443f origin/main && echo "ml OK"
ls notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-*.md      # expect 2 files

# --- juniper-cascor ---
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git fetch origin
git merge-base --is-ancestor 1ea2062 origin/main && echo "cascor OK"
git rev-list --count 70edfc4..origin/main                   # non-zero: proves the range is real
git log --oneline 70edfc4..origin/main -- \
  src/log_config/ src/candidate_unit/ src/tests/conftest.py src/api/observability.py
                                                            # expect EMPTY against a non-zero range
gh issue view 573 --repo pcalnon/juniper-cascor --json state,comments \
  --jq '{state, n: (.comments|length)}'                     # expect OPEN, 0

# --- the central finding, reproduced ---
cd /home/pcalnon/Development/python/Juniper/juniper-ml
env -u CASCOR_LOG_LEVEL -u JUNIPER_CASCOR_LOG_LEVEL \
  python3 util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py
```

**Read exactly one row.** Under the block tagged `--- C: after Logger.set_level('TRACE')`, the row beginning `isEnabledFor( 1)` must read **`True` on the left and `False` on the right**. Any other value there means re-verify before proceeding — do not judge by "the columns agree", which is true of some rows in every state.

> **Why the `env -u` matters.** `_level_logger_name` is seeded from the environment at class-body import (`logger.py:164`). With `JUNIPER_CASCOR_LOG_LEVEL=TRACE` exported, the two disjoint states are seeded with the **same** value and the row reads `True`/`True` — the defect is unchanged, merely masked. Measured 2026-09-07. Without `env -u` this check produces a false "the arc is over".
>
> The probe reads the **primary** cascor checkout by hardcoded path (`CASCOR_SRC` at its line 23), so fetch that checkout before trusting the result. The probe also exits **0 unconditionally** — it is eyeball-only. P1-G4 already calls for extending it into a regression test; doing that as part of P0.5 would close trap 7 against the arc's own instrument.

---

## 12. Git status at handoff

- **juniper-ml**: branch `docs/handoff-logging-redesign-arc`, cut from `origin/main` at `ef73443f`, in worktree `.claude/worktrees/bubbly-shimmying-seahorse`. Only this file added.
- **juniper-cascor**: clean; no branch for this arc.
- Predecessor branch `design/logging-redesign-roadmap` was **squash**-merged as `53ec93e9`, so `git branch -d` will refuse. Confirm with `git merge-base --is-ancestor 53ec93e9 origin/main`, then `git branch -D`.

---

## 13. Consensus validation of this handoff

Per **CONSENSUS** §3, sized **high criticality** (a handoff misdirects a whole successor session) × **medium uncertainty** → 2 Lane A + 2 Lane B. Run as **1 Lane A + 2 Lane B** across three agents with distinct entry points and lenses, each briefed that a finding of soundness is worth nothing.

**Sample**: three agents, ~120 tool calls, no tests run — every claim comes from source, git, the GitHub API, and two live executions of the probe.

| lens | found |
| --- | --- |
| Lane A — re-derive every factual claim from primary sources | 3 wrong, 2 unverifiable, of 12 |
| Lane B — amputation | ~40 dropped items; 5 ranked top |
| Lane B — executability | 35 numbered defects, 4 classed as day-one blockers |

**What the review changed, materially:**

- **The first draft was a pointer document.** It carried RECON §6.1's baseline by reference — in a section whose own opening sentence says the numbers were inlined *because Phase 0's author may not open the upstream document*. §6 now inlines them.
- **Owner decisions 1–6 were declared blocking and never stated**, and the pointer given landed on six empty bullets. §3 now states all six with what each gates.
- **Decision 6 was inverted** — "do not re-litigate the call-site migration" read as *settled* where ROADMAP reserves it explicitly.
- **Two decision sets, both numbered 1–6, were conflated**; one sentence used DESIGN numbering with no marker. §3 disambiguates and PREFLIGHT 3 warns.
- **`O_APPEND` was dropped** — the one constraint the consensus record shows was amputated once and restored. Amputated again; now in §8.
- **P0.4 vanished entirely** from "where to start", despite ROADMAP naming it the critical-path head and the landing gate for P2/P3/P6.
- **The probe's stop-rule was dangerous.** With `JUNIPER_CASCOR_LOG_LEVEL` exported the two paths read identically and a successor would have abandoned a live arc. Reproduced, and §11 now mandates `env -u` and names one row.
- **P0.5's anchor was too narrow** — the fixture stubs three seams, and the `CandidateUnit` → `_noop_logger` seam is the one that makes the eight guard sites unreachable. The original scoping would have produced a false all-clear from the item called "free on day one".
- Four dependency claims were wrong (P4, P6, P3.3's P0.3 gate, P2's gate), the verify commands read stale local refs with no `fetch`, and a "(trap 2)" cross-reference resolved to the wrong trap.

**Where the reviewers disagreed, and how it was settled.** One held that cascor's per-PR symbol-loss screen is advisory; another that it is required. Settled against the **ruleset**, not the workflow: `Sequence Safety` **is** a required context on cascor `main`, and `sequence-safety.yml`'s own header comment asserting otherwise is stale. Trap 3 records both the fact and the stale comment.

**What this evidence cannot support**: the pre-merge `mergeStateStatus: BLOCKED` on ml#1573 is not retained by GitHub and is corroborated only indirectly, by the surviving CodeQL comment. The 17/17 half is directly verified.

**Owed to a third round**: nothing. Round 2's residue was anchor and pointer slips changing no number, disposition or action — CONSENSUS's stopping condition.
