# HANDOFF 2026-09-07 — pointer-follow soak arc, outstanding work

**Validated by three independent agents before archiving** (lenses: falsification,
fresh-session executability, omission/prioritisation; procedure
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).
They returned ~29 findings against the first draft, including **four criticals about fix
directions the draft recommended**. §12 records what they changed and what this document
still cannot support.

State re-derived on 2026-09-07. `origin/main` moves several times a day; **treat every SHA
here as advisory and re-run §11** rather than trusting a pin.

## 0. The arc's position

The bet failed: `main` is **`BET-FAILING seeded=43/35 rate=60.5% ci=[0.456, 0.736]`**
(ml#1644 landed 2026-09-07T12:46Z), so `util/soak_run_probe.py` refuses every real run
without `--force`.

Three qualifications belong with that headline and are easy to lose — the first draft lost
all three. From `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`:

- **§4.5 — the verdict is one observation deep.** Margin to the boundary is **0.0137**. P15
  scored the other way (27/43) or dropped (26/42) is *not* terminal. The PR's own channel fix
  is what reclassified P15.
- **§4.6 — neither corpus is a clean read.** §15.4 of
  `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` forbids pooling across
  the intervention boundary, *and* says "the four probes are the only ones this intervention
  touches" — but **4 of the 8 post-intervention runs are on probes rung 1 never touched**
  (P02, P06, P15, P19 are treated; P14, P21×2, P23 mix). The post-only corpus is not the
  clean alternative it looks like.
- **§4.7 — 95.3% retention is a one-way artefact.** `RESCORE_OUTCOMES = ("source-recovered",)`
  can only move rows in the retention-raising direction; the corpus was **74.4%** as
  originally recorded. 95.3% is the number that turns a failed bet into "relocation is safe".
  **Do not quote it without this.**

**Do not `--force` past the verdict to resume per-probe characterisation.** §4.1 of the same
document shows the n≈8–10 campaign cannot resolve its targets: P21 needs **n≥16**, P23
**n≥31**, and inside 8–10 the Wilson resolving threshold never leaves `k≤1`, so runs 9 and 10
*lower* the chance of an answer (power at p=0.25: 0.3671 → 0.3003 → 0.2440, rising to 0.4552
only at n=11). Whether that campaign runs at all is owner decision §7.6.

## 1. What to do first

**Nothing here is time-critical.** The first draft said item A was "costing something on
every timer firing"; three validators independently refuted that — the systemd units are
**not installed on this host** (`systemctl --user is-enabled juniper-soak-probe.timer` →
`not-found`; no unit files; `logs/soak_probe_failures.log` does not exist). Item A is
dormant.

The arc is blocked on **owner decisions (§7)**, not on engineering. If work proceeds before
those are settled, this order is defensible and costs no sessions:

1. **Item E's evidence recovery** — the only thing that can move the headline rate (§3.E).
2. **§8's three untested predictors** — the design doc of record calls this *"the actual
   blocker to decision support"*, not a fallback.
3. **Item C's era parameter**, built but *not wired* (§3.C — wiring it is owner decision §7.3
   and re-arms spend).
4. **Item J** (`docs/REFERENCE.md` is actively wrong, §3.J) — cheap, operator-facing.
5. **Item A**, when the unattended path is next enabled.

## 2. State, verified 2026-09-07

| fact | value |
|---|---|
| ledger | 64 records → **49 observations / 43 valid** (6 invalidate, 9 rescore) |
| verdict (pooled) | `BET-FAILING`, exit **1** |
| verdict (post-intervention only) | `IN-PROGRESS seeded=8/35 rate=25.0%`, exit **0** — but see §3.B, this is an n-gate |
| newest observation | `2026-09-04T09:55:27Z` (P21) — **no probe has run since** |
| post-intervention coverage | 8 runs over **7 of 15** probes; **8 probes have zero**: P07, P08, P16, P18, P20, P22, **P24**, P25 |
| open PRs touching soak | none |
| soak test suites | **12**, all wired into `.github/workflows/ci.yml`; 272 tests green |
| `MEMORY.md` | **169 rows / 170 lines**, 21,024 B; headroom **3,976 B**, runway **5.4 days** (`util/memory_index_check.py`). It moved 20,852 → 21,024 B *during the writing of this handoff* — quote the tool, never this row |

## 3. Open work

All items below are open on `origin/main`. Since 09-04 the arc gained **coverage, not fixes**:
five items are now pinned by characterisation tests (A, B, C, E via
`tests/test_soak_run_probe_stopping_rule.py`, `tests/test_soak_analyse_date_pool.py`,
`tests/test_soak_handoff_consensus_checks.py`), so production behaviour is byte-identical but
a silent change would break a test. **A pin is not a fix.**

### A. The stopping rule fails open — dormant on this host

`util/soak_run_probe.py:398-400` never reads `st.returncode`, and `verdict_is_terminal`
(`:112-119`) tests only `("BET-FAILING", "HOLDS-AT-")`, so `NO-DATA`, `DEGRADED`,
`NO-SEEDED-DATA` and `""` all pass the spend control.

**Both obvious fixes are wrong. This is the trap.**

- **`if st.returncode == 2: return 2` does not cover the stated hazard.** A real crash in
  `soak_ledger.py status` exits **1**, not 2 (measured: `--ledger <a directory>` →
  `IsADirectoryError`, rc 1). Only argparse misuse gives rc 2. And rc 1 also means
  *escalations open at any verdict*, so keying on truthiness refuses every escalated soak
  (`util/soak_ledger.py:808-810`; pinned at `tests/test_soak_run_probe_stopping_rule.py:163`).
- **A token set that omits `""` does not fix it either** — a crashed tool yields empty stdout.

**The fix that works**: refuse on the token set **including `""`** —
`{"", "NO-DATA", "DEGRADED", "NO-SEEDED-DATA"}` — **and preserve the `--dry-run` exemption**
that `refuses_terminal_verdict` already carries (`:155-156`). Omitting the exemption makes
`--dry-run` exit 2 with empty stdout, which is *exactly* the regression ml#1690 removed.

**The test suite cannot tell the correct fix from the bug — measured.** Run against both
variants, all 12 soak suites produce the *identical* failure set (11 failures, the same 4
methods), because `tests/test_soak_run_probe_terminal.py` and the stopping-rule suite stub
`ledger_rc=0` (`tests/test_soak_run_probe_stopping_rule.py:108`). `test_soak_run_probe_terminal.py`
passes **OK, 15 tests** under the bug. So the suite gives you no signal before *or* after you
invert the pins.

**The one control that discriminates** — use a **readable but EMPTY** ledger (verdict
`NO-DATA`), not an unreadable one:

| ledger | correct fix | ml#1690 bug |
|---|---|---|
| readable, empty (`NO-DATA`) | `--dry-run` rc **0** | rc **2, empty stdout** |
| unreadable (e.g. a directory) | rc 1 | rc 2 |

An earlier draft of this handoff said to use the *unreadable* case and assert rc 0. **That is
wrong**: the correct fix returns 1 there, because the guard exempts the dry run and then
`util/soak_next_probe.py` dies on the same unreadable ledger (`dispatch failed rc=1`). A
reader following it would have judged a correct fix broken. §11's phrasing — *"rc 2 with empty
stdout means the exemption was reverted"* — is the sound discriminator.

This is the negative-control discipline
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md`
records as *"a blocking gate that cannot fail is worse than none"* — and here the gate that
cannot fail is the test suite itself.

**Expect exactly 4 methods to go red, and invert them deliberately.** Three are in the
stopping-rule suite: `:187` `test_degraded_fails_open_on_a_real_run`, `:201`
`test_a_ledger_tool_crash_fails_open`, and `test_ledger_non_answers_are_not_terminal`
(`:93-97`, in class `VerdictIsTerminalPrefixOnly` at `:71`, covering five verdicts including
`INCONCLUSIVE`). **The fourth is in a suite this item does not otherwise name**:
`tests/test_soak_run_probe.py::TerminalVerdictDoesNotGateADryRun::test_a_non_terminal_verdict_never_refuses`.
Its class name reads as though your fix broke the dry-run exemption. It did not — that class
covers the predicate generally. Do not revert on seeing it.

**Bundled, same cause**: `util/systemd/juniper-soak-probe.service` is `Type=oneshot` with no
`SuccessExitStatus=`, and the guard exits 2 — so once installed, every firing writes a strike
to `logs/soak_probe_failures.log`. `SuccessExitStatus=2` is **not** free: argparse also exits
2, so a typo in `ExecStart=` would then read as success forever. Preferring "guard exits 0
when it refuses by design" costs six `assertEqual(rc, 2)` sites. No test parses that unit
file; nothing on this host can exercise it until the units are installed.

### B. The picker and the stopper read different corpora — and C is its root cause

`util/soak_next_probe.py` filters to post-intervention rows (`:52`, `:61`, `:72`); the stopper
reads the **pooled** verdict. Today: post-only `IN-PROGRESS` rc 0, pooled `BET-FAILING` rc 1.

**Read that `IN-PROGRESS` correctly.** It is purely the `runs < TARGET_PROBE_RUNS` n-gate
(`util/soak_ledger.py:82`, `:376`) firing before any CI test — the same slice's Wilson upper
is **0.591**, already below the 0.75 boundary, and
`util/ad-hoc/2026-09-04_soak_handoff_consensus_checks.py` labels that slice
`terminal(BET-FAILING)=True`. It is **not** evidence that the campaign should continue.

**DANGER — the natural fix silently re-arms spend.** Wiring the stopper to the post-only
corpus makes `refuses_terminal_verdict("IN-PROGRESS", …)` return False: **the spend control
stops refusing, with no `--force`, for ~27 further billed runs** (35 − 8) on a campaign §0
says cannot resolve anything. §15.4's "do not pool" makes that corpus look like the *correct*
choice, which is what makes this dangerous. Choosing the corpus **is** owner decision §7.3.

### C. `analyse()` has no era filter

`util/soak_ledger.py:219` — `def analyse(rows, bad_lines)`. It structurally cannot honour
§15.4. `tests/test_soak_analyse_date_pool.py:122-130` pins the signature as exactly
`["rows","bad_lines"]` **and enumerates `since|until|after|split|cutoff|ts` as forbidden
names**, so any era parameter requires rewriting that pin.

**Building it is safe; wiring it is the owner's call.** A parameter with a default is inert
until a caller passes it, and `cmd_status` (`:758-762`) is the only path the stopper reads —
so "fix C" either ships nothing or *is* §7.3. Say which you did.

### D. The instrument cannot see half of what the protocol calls a follow

`parse_events` captures only `tool_use` (`util/soak_run_probe.py:321`); `grep -rn tool_result`
across the three soak scripts → **0**. But §4 of the soak ledger defines FOLLOW as *"opened
the destination, **grepped it**, or otherwise read it"* and §7 scores from *"the session's
tool log"* — inputs **and** results. A directory-scoped grep that returns the pointer
document's content without naming it is protocol-conformant retrieval scored as a non-follow.
The capability exists in the unwired screen
(`util/ad-hoc/2026-08-21_soak_probe_evidence.py:111`).

### E. Two retrieval standards, and the evidence to settle it EXISTS

8 follows were scored on tool **output**, 18 on tool **input**. As scored: **60.5%**.

**41.9% is a floor produced by an amputated instrument, not "the standard applied
uniformly"** — that phrasing was refuted in round 2 of the 09-04 review and the first draft of
this handoff reinstated it. Under the protocol's own standard (inputs ∪ results, item D) the
rate stays **60.5%**. The live range is **41.9%–60.5%**, depending on a standard nobody has
ratified.

**The transcripts survive.** All 8 output-scored rows are dated 2026-08-22 (P02×3, P18×2, P21,
P22, P24) and were never re-audited — ml#1644's re-audit covered only the automated
2026-09-03/04 runs. 128 transcript files exist under
`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/bf50124e-6fde-4314-bdca-0ca7876b8efb/subagents/`,
47 of them referencing `docs/REFERENCE.md`. Two obstacles, both smaller than they look:
41 of 49 ledger rows carry hand-written labels (`soak-A-P02`) rather than session UUIDs, and
the label→file mapping is recorded nowhere; and `SUBAGENT_DIRS`
(`util/ad-hoc/2026-08-21_soak_probe_evidence.py:39-45`) has only its **project-dir component**
stale — the UUID directory lives under the primary project dir. That is a one-component path
fix, not a dead end.

### F. The contamination screen is unwired

`conf/soak_probes.json`'s `_README` says scoring **MUST** run
`util/ad-hoc/2026-08-21_soak_probe_evidence.py` (8 runs were once discarded for registry
leakage). Zero references to it in `util/soak_run_probe.py`, `util/soak_ledger.py` or
`util/soak_next_probe.py`. `tests/test_soak_probe_evidence.py` tests the **screen**, never the
wiring.

Never re-homed with it, and needed if §7.1 changes the registry — the authoring rule from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md`:
*"store identifier-shaped facts in a form the subject's own grep cannot hit. Holding files
aside failed when a probe agent ran `git checkout`."*

### G. Instrument validity, unchanged

All **15** probes point at `docs/REFERENCE.md`, differing only by `#anchor`, stripped at
`util/soak_run_probe.py:345`; `hit = doc in blob` (`:358`) is a substring test over
`json.dumps` of tool inputs. The target is a per-probe constant. Bounded by: the channel only
`suggests`; a human supplies `--outcome`.

### H. P06's discriminator under-specifies

Unchanged since ml#1206; §9.6 of
`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`. Also never
re-homed: that handoff's three-ways-invalid taxonomy — *the fact never left the source; the
discriminator is satisfiable without engaging the fact (P17); the discriminator is stricter
than the source rule (P15)* — of which item H covers only one instance.

### I. BET-FAILING's prescribed action has never been carried out — and the tool says so on every run

`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md:189`: **"Revisit owner
decision #7. Never re-inline."** Decision #7 is at
`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md:654`, deferred *"revisit
only if the P3 soak shows a real pointer-follow problem."* **That trigger has fired.** Neither
document has been touched; ml#1644 records the verdict without citing decision #7.

Unlike item A this is live: every `soak_ledger.py status` prints
`-> the relocation bet is failing; revisit owner decision 7. NEVER re-inline.`

### J. `docs/REFERENCE.md` on main is actively wrong about the soak — NEW

Not in the 09-04 review. The operator-facing reference carries stale soak content, including
a defect documented as live **after it was fixed**:

1. `:955` "makes even a dry run exit 2 unless `--force`" — false since ml#1690 (measured rc 0).
2. `:955` "On current `main` the ledger is `INCONCLUSIVE` … so the default invocation does
   run" — false; main is BET-FAILING and refuses.
3. `:963` "`blob = tool_inputs + answer`. Reciting the path in the answer scores as a pointer
   hit" — **the exact defect ml#1644 fixed**; code is tool-inputs-only (`:357`).
4. `:988` "INCONCLUSIVE, seeded 40/35, rate 65.0%, CI [0.495, 0.779], retention 95.0%" —
   stale on every figure.
5. `:985` recommends driving probes to **n≈8–10**. This one is a **stale recommendation, not a
   false statement** — and the file **already contradicts it**: `:1250` says *"Do not drive
   the ambiguous probes to n≈8–10"* and derives the same n=31 figure this handoff carries.

**So the remedy is deletion, not authorship — and the site list must be enumerated, not
assumed.** The stale content repeats at different offsets: the channel sentence at `:963` and
`:1272`; "seeded 40/35" at `:988` and `:1266` (that second copy adds a further false claim,
`status` exit 0 — measured **1**); the `n≈8` string occurs at **seven** sites (`:985`, `:1111`,
`:1250`, `:1304`, `:1388`, `:7468`, `:7469`), a mix of stale recommendations and the
correction. `grep -n` each string and classify every hit before editing; patching the first
occurrence leaves live copies behind, and deleting a correction by mistake is worse than
leaving a stale line.

ml#1644 touched no docs.

**The soak section is duplicated in more than one place, so enumerate before editing.**
Verified on `origin/main`: the channel-defect sentence (*"Reciting the path in the answer
scores as a pointer hit"*) appears at `:963` **and `:1272`**; *"seeded 40/35"* at `:988` **and
`:1266`**; `:975`/`:1101`, `:985`/`:1111` and `:999`/`:1123` are further identical pairs. The
copies are not a single contiguous duplicate block and the offsets differ, so **`grep -n` for
each string and fix every hit** rather than assuming two copies at a fixed delta — a fixer who
patches the first hit leaves a live one behind. (The dry-run claim at `:955` appears once.)

## 4. `MEMORY.md`: the intervention under test was pruned on 2026-09-05

Recovered from Claude Code session transcripts (the memory directory is not
version-controlled, so this is the only history that exists):

| when | rows | bytes | hookless |
|---|---|---|---|
| 2026-09-04T21:45Z | 149 | 24,622 | 0 |
| **2026-09-05T08:48Z** | **151** | **25,306** | 0 |
| 2026-09-05T18:26Z | 163 | 17,454 | **48** |
| now | 170 | 20,852 | 48 |

**The file crossed the 25,000-byte cap before the prune.** The prune was a *recovery*, not a
gratuitous trade — the first draft got this backwards. It happened in a nine-minute window on
09-05 (between 18:17:59Z and 18:26:40Z), not over three days.

It cost hook text on **48 of 170 rows**, and rewrote some row titles (several absorbing their
hook's content). Three of the four rung-1 rows — the facts this soak measures — lost hook
text, two entirely:

| row | before (09-05T18:17Z) | after (18:26Z) |
|---|---|---|
| Port check fail-opens | `— missing \`ss\` reads "free"; clean ≠ proof` | `— missing \`ss\` reads "free"` |
| Reaper over-protects | `— false reap = the campaign` | *(none)* |
| Diverging worktree | `— converge; 4 gates + probe` | *(none)* |

The fourth is **Per-run timeout ordering**, whose hook survived. Rung-1 row *titles* are
unchanged, so the "the intervention is weaker now" reading holds for these four specifically.

**Consequence, stated conservatively**: any probe run from here is measuring a different index
state from the 8 post-intervention runs already recorded. Treat pre-/post-prune as a further
era when interpreting, and record which side a run falls on.

**What decides the side is the PARENT session's start time, not the run's.** §17 of
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` establishes that memory
context is a snapshot taken when the parent session starts. A long-running session that began
before 2026-09-05T18:26Z is still served the *pre*-prune index today — this handoff's own
authoring session is one, which is why its `before` column could be quoted at all. So a probe
dispatched from an old session measures the old index while `MEMORY.md` on disk is the new
one. **Record the parent session's start time alongside the run**, not just the run
timestamp; the ledger has no field for this today.

**Do NOT "restore the hooks".** Three reasons the first draft missed: the prior text for 45 of
the 48 rows exists nowhere; §17 of
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` establishes that a
session's memory context is a snapshot from *parent session start*, so restore-then-run cannot
measure its own restoration; and `util/systemd/juniper-soak-probe.path:29` watches this exact
file with `PathChanged=` — **on a host with the units installed, editing it fires a probe
run.** (It is not watched on *this* host, because nothing is installed. The first draft
asserted both "nothing watches this file" and "every `.path` trigger fires"; the second was
wrong.)

`util/memory_index_check.py` is the tool for this: headroom, runway, and hook-size errors.

## 5. Traps

- **`--outcome miss` needs `--class`** (`discoverability | hazard | pointer-defect`); without
  it `probe-run` exits 2. Note `pointer-defect` has never been used, so the reducer's
  `pointer_defects = 0` has never had an input that could make it non-zero.
- **Probe ids are full slugs.** `--probe-id P19` → `no such probe: P19`.
- **There is no per-probe f/n tool.** `soak_next_probe.py --status` gives post-intervention
  *coverage counts*; `soak_ledger.py report` gives pooled aggregates;
  `2026-09-04_soak_handoff_consensus_checks.py` gives the reducer/standards/era splits and
  **prints no probe ids at all**. The only f/n table is hand-maintained prose at
  `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` §10.5.
- **Never pipe an exit-code-significant command through `tail`/`head`.** `soak_ledger.py
  status` exits 1; `status | tail -20` exits **0**. §11 depends on this.
- **`--probes` is a PARENT-parser flag, and its position changes the failure mode.** Before
  the subcommand (`soak_ledger.py --probes /nonexistent.json status`) it is silently ignored
  and the verdict still prints, rc 1. *After* it (`… status --probes /nonexistent.json`) it is
  an argparse error — **rc 2, no verdict at all**, which is the same code the spend guard
  uses and so reads like a degraded ledger.
- **Mutation records name their target in `invalidates` / `rescores`, not their own
  `obs_id`.** A reducer keyed on `obs_id` silently no-ops: 49 valid / 67.3% retention instead
  of 43 / 95.3%, with a clean-looking report either way.
- **`python3 <file>` skips test classes below `unittest.main()`.** Use `-m unittest`.
- **A checkout is not a deployment.** `juniper-soak-probe.service` sets
  `WorkingDirectory=` to the **primary** checkout, which is typically behind `main`. Merging a
  fix does not change what a timer would execute until someone pulls it.
- `util/wait_for_checks.py` has no `--auto` (that is `gh pr merge`, via `util/safe_merge.py`).
- **`safe_merge --execute` exits 0 without merging** on an unresolved review thread; it prints
  `auto-merge net disarmed` and names the thread. Look for the `MERGED` line.
- **`gh pr edit` is broken on gh 2.46.0** — use `gh api -X PATCH .../pulls/N -F body=@file`.
- Five stale remote branches and one stale worktree
  (`worktrees/juniper-ml--test--soak-harvest--20260905-1500--soak`) hold nothing main lacks.
- `AGENTS.md` lists 9 of the 12 soak suites; `test_soak_ledger.py`, `test_soak_next_probe.py`
  and `test_soak_run_probe.py` are in `ci.yml` but missing from the operator list.

## 6. What this evidence CANNOT support

Carried from §7 of `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`,
because a successor who does not read it will re-derive false confidence:

- **The organic arm has never run.** `arm` is `"seeded"` in all 49 rows; `organic: runs 0` is
  an unfed instrument, not a measurement. Every claim here is single-arm.
- **One rater.** `scored_by` is `claude-opus-5` in all 49; there is no inter-rater
  reliability, and items D/E turn entirely on scoring judgement.
- **`pointer_defects = 0`** has never had an input that could make it non-zero.
- **There is no `rung` field** in the ledger or `conf/soak_probes.json`, no index-recovery
  detector, and no such outcome. "1 of 4 rung-1 probes" is transcript prose. §4's "rung-1
  rows" is an attribution from the plan, not something the instrument can make.
- **`p = 0.0017` is a parametric bootstrap, not the permutation test it is labelled** in
  `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` §9.3. A true
  label-shuffle gives p ≈ 0.0002–0.0006. The conclusion survives; the label is wrong and
  uncorrected in the surviving document.

## 7. Owner decisions — DO NOT DECIDE THESE

1. Whether **index-recovery** becomes a scored outcome (registry + ledger change; see item F's
   authoring rule first).
2. Whether **BET-FAILING** feeds back into relocation policy — "safe, but not for the reason
   assumed". The word *safe* rests on the 95.3% whose provenance is §0.
3. Whether the stopping rule keys on the **pooled** or the **post-intervention** verdict. This
   is item B/C's second half and it re-arms ~27 billed runs.
4. **P06's discriminator** (item H).
5. Whether to **`--force`** past a terminal verdict at all — §10.5 of the design conversation
   records this as owner-facing and open. The 09-04 handoff decided it unilaterally; that was
   a finding.
6. **Whether the per-probe campaign runs at all**, given §0. Upstream of 1–5.

Also unadjudicated: §15.3 of
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` pre-registered that rung 1
would **not** move the follow rate on the four treated probes, and said that if it did *"that
prediction is wrong and the §14 conclusion needs revisiting"*. P23's only post-intervention
run is a follow. The design conversation re-reads this as small-sample noise; nobody has
adjudicated it against the pre-registration.

## 8. The actual blocker to decision support

§8.2 of `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`:

> the arc has established, at real cost, that **two sharply separated strata exist** — and has
> not established what puts a fact in one rather than the other. **That is the actual blocker
> to decision support**, and no number of additional runs at the pooled level removes it.

It names three candidate predictors, *"none tested yet"*: grep-findability from the task's own
vocabulary; completable-without-the-fact; contradicts-a-plausible-default. They need no owner
decision and spend no sessions — they run over the 15-probe registry and its tasks (**not**
over the 43 ledger rows; the first draft said otherwise). Any such analysis inherits whichever
retrieval standard item E settles on.

## 9. Documents

- `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md` — verdict and
  corrections. **§4.1** campaign arithmetic, **§4.5** one-observation margin, **§4.6** both
  §15.4 breaches, **§4.7** retention provenance, **§4.8** the two standards, **§6** dissent
  and the reconciler's own errors, **§7** what the evidence cannot support, **§8** owner
  decisions.
- `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` — protocol of record.
  §4 FOLLOW definition, §6 rule table, §7 scoring + priming rule, §15.3 pre-registration,
  §15.4 pooling prohibition, §17 the snapshot limit, §19/§20 instrument limits.
- `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` — §8.2 the actual
  blocker, §8.3 the stopping-rule signal, §9.x strata, §9.6 P06, §10 the bet failing, §10.5
  the per-probe table.
- `notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md` — automation
  boundaries.
- `notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` — owner decision #7 at
  `:654`.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md`
  — still the only home for the registry-leak authoring rule, the three-ways-invalid taxonomy,
  and the negative-control discipline.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-04_soak-per-probe-characterisation.md`
  — **superseded**; archived UNVERIFIED and its central instructions are refuted. History only.

## 10. Corrections to the predecessor

`HANDOFF_2026-09-04_soak-per-probe-characterisation.md` is superseded: its blocker cause (all
three guesses refuted), `mergeState` BLOCKED not BEHIND, two unlisted failing checks,
`--force` not sanctioned by §8.3, bare probe ids, the missing `--class`, `--auto` on the wrong
tool, and "every probe's CI spans 50%" (false for P15 and P19 at 0/4 → `[0.000, 0.490]`).

Stale figures it is easy to inherit: `MEMORY.md` headroom was **378 bytes** in the 09-04
consensus document and is **4,148** now — re-measure, never quote. And ml#1699, ml#1700,
ml#1725 and ml#1728 are **CLOSED, never merged**; their tests reached main via ml#1771 and
ml#1793, so a reader chasing those numbers finds closed PRs and may conclude the work was
abandoned.

## 11. Verify first

```bash
git fetch origin && git log origin/main --oneline -1          # advisory; main moves hourly
git show origin/main:reports/soak/pointer_follow_soak.jsonl > "${TMPDIR:-/tmp}/soak-$$.jsonl"
wc -l "${TMPDIR:-/tmp}/soak-$$.jsonl"                          # expect 64
python3 util/soak_ledger.py --ledger "${TMPDIR:-/tmp}/soak-$$.jsonl" status; echo "rc=$?"
                                                               # expect BET-FAILING, rc 1 -- do NOT pipe this
python3 util/soak_next_probe.py --status                       # 8 runs, 7 covered, 8 at zero
python3 util/soak_run_probe.py --dry-run; echo "rc=$?"         # expect rc 0 + terminal NOTE on stderr
python3 util/memory_index_check.py                             # headroom/runway; flags hookless rows
grep -nE 'Port check fail-opens|Per-run timeout ordering|Reaper over-protects|Diverging worktree' \
  ~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md
                                                               # 4 rung-1 rows; 2 currently have NO hook
systemctl --user is-enabled juniper-soak-probe.timer            # expect not-found -- item A is dormant
python3 -m unittest tests.test_soak_run_probe tests.test_soak_ledger tests.test_soak_next_probe
gh pr list --repo pcalnon/juniper-ml --state open --search soak # expect none
```

`--dry-run` returning **2 with empty stdout** means ml#1690's exemption has been reverted.

## 12. What validation changed, and what this document still cannot support

Three validators returned ~29 findings against the first draft. The four that mattered:

- **Its prioritisation was false.** It called item A urgent on the strength of timer firings
  that do not happen — the units are not installed. All three validators found this
  independently.
- **Its fix direction for item A would have reintroduced ml#1690's bug**, and the named test
  suites would have passed anyway. §3.A now carries the working predicate and the warning.
- **Its "plumbing fix" for B/C silently re-armed ~27 billed runs** with no `--force`. §3.B now
  says so.
- **It told the reader to edit `MEMORY.md`**, which is the `.path` trigger, while forbidding
  probe runs — and to restore text that does not exist. Removed.

It also dropped §4.5, §4.6's second breach, §4.7 and all of §7 from the source review, and
reinstated a phrase round 2 of that review had refuted. Those are restored in §0 and §6.

A **round 2** then attacked those corrections, and found three errors the rewrite itself
introduced — the pattern the procedure predicts. All are fixed above: §3.A's replacement
acceptance check named the *unreadable*-ledger case, on which a correct fix returns 1 (a
reader would have judged it broken); §3.J under-enumerated the stale sites and missed that
`docs/REFERENCE.md` already contains its own correction; §5's `--probes` trap was stated for
the wrong argument position.

**One round-2 finding was rejected.** It argued §4's consequence is undercut because this
session is served the *pre*-prune index though "this session started 2026-09-07". This session
started **2026-09-04**; the date rolled over mid-session. Being served the 09-04 index is what
§17 predicts, so the finding corroborates the snapshot rule rather than refuting the
inference. The useful part is kept, as the parent-session-start note in §4.

**Residual uncertainty.** The `MEMORY.md` series in §4 is recovered from session transcripts;
line counts are exact, byte counts are measured on a transcript-rendered block that truncates
27 long hooks, so treat bytes as ±. The claim that rung-1 rows lost hooks is verbatim-verified
for the three shown. Item E's transcript directory was located but **the label→file mapping
was not solved** — the re-audit is scoped, not done. Item A's fix direction is reasoned and
its discriminating control is measured, but **no fix has been written or landed**. No probe
was run and the ledger was not modified in producing this document.
