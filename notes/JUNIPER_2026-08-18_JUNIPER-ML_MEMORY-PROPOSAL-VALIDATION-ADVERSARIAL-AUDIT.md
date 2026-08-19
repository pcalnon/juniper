# Memory Proposals A–D — Adversarial Validation (Validator 3 of 3)

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose and standing

This is the **third of three independent validation passes** over the four competing
shared-session-memory proposals. Validator 1 checks citations; validator 2 checks
arithmetic. **This pass attacks the designs**: it looks for the failure that makes a
proposal unsafe or unworkable in practice, and for what each proposal quietly omitted.

It is a findings report, not a plan. Nothing here was changed in the repository; this
document is the only file written.

Subjects:

- [Proposal A — Progressive Disclosure via Skills](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md)
- [Proposal B — Path-Scoped Locality](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md)
- [Proposal C — Deduplication and Pruning](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md)
- [Proposal D — Govern the Write Path](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md)

Fact bases (not re-derived, not contradicted):

- [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) — **BASE**
- [Claude Code memory mechanisms](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) — **MECH**

All repo evidence taken 2026-08-18 in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`,
`main` = `e209b74`, clean tree, against the installed `juniper-ci-tools` **0.8.0** — the same
package version `ci.yml` and `main-verify.yml` pin (`>=0.8.0,<0.9.0`).

### Severity vocabulary

| Severity | Meaning |
|----------|---------|
| **FATAL** | The proposal cannot work as designed; the flaw is in the thesis, not the details. |
| **SERIOUS** | Real, will bite, and needs a specific named fix before adoption. |
| **MANAGEABLE** | Real, but bounded and already mitigated by a guardrail the proposal states. |
| **SURVIVES** | Attacked deliberately and held. Recorded so the proposal gets credit. |

---

## The checklist applied

Seven attack surfaces, each worked against all four proposals. "Pass" is stated per item.

| # | Surface | Pass means |
|---|---------|------------|
| 1 | **Compaction** (MECH §4c-bis) | No safety-critical content silently disappears mid-session when a compaction happens despite the handoff policy. |
| 2 | **Discovery failure** | Every directive whose miss costs irreversible work is either resident or mechanically enforced by a gate that actually runs. |
| 3 | **Concurrency** | New lore has a destination; three same-day sessions do not collide; the destination cannot become the next 170K file. |
| 4 | **Gate interactions** | The migration survives its own CI; the target file passes the four existing `AGENTS.md` gates; nothing silently depends on a gitignored path. |
| 5 | **Vacuous pass** | Every proposed gate has a stated negative control and fails closed on an empty input list, a renamed file, or a moved measurement target. |
| 6 | **Waiver / incentive** | The escape hatch cannot be paid with someone else's money, and the cheapest green path at 02:00 is the correct one. |
| 7 | **Omissions** | The stated weaknesses are complete; nothing material is glossed; the cross-cutting holes are named. |

---

## Surface 1 — Compaction

MECH §4c-bis is the governing fact and it was recorded **after** A, C and D were drafted:
path-scoped rules and nested `CLAUDE.md` are *lost after compaction until re-triggered*; skill
bodies re-attach capped at 5,000 tok/skill and **25,000 total, oldest dropped**, truncated
keeping the file's start; the project-root file and auto-memory are **re-injected**.

### AV-C1 — Proposal B: 92% of the corpus sits in the two mechanisms that die at compaction — SERIOUS

**Location**: Proposal B §2.2, §5.2, §7.2.

**Problem.** B's own budget table puts **104,488 chars in `.claude/rules/*.md` and 48,412 chars
in nested `CLAUDE.md`** — 152,900 of 166,736 (92%) — and MECH §4c-bis places *both* mechanisms
in the "Lost until a matching file is read again" row. B wrote its §2.2 correction believing the
fact was unverified and designed for "the worse branch". The worse branch is now the **verified**
branch. That is not a flaw in B's reasoning; it is a change in the odds B was betting against.

The flaw is in B's mitigation. B §7.2 argues the exposure is bounded because *"it edits
`experiment_stack.bash` again — this time via `Edit`, which requires a prior `Read`, so the rule
re-fires"*. That reasoning depends on an unverified property of the harness: whether the
"this file has been read" bookkeeping that `Edit` enforces is **conversation context** (destroyed
by compaction, so a fresh `Read` is forced and the rule re-fires) or **harness state** (survives
compaction, so `Edit` proceeds with no `Read` and the rule never re-fires).

**Scenario.** A six-hour session opens `util/experiments/run_experiment.py` at minute 20 and
absorbs `experiments.md`, including the `max_epochs`/`output_epochs` divergence
(`AGENTS.md:576-578`). At hour four it compacts. At hour four-thirty it edits the driver's
config-validation branch. If read-tracking is harness state, no `Read` occurs, the rule does not
re-fire, and the session "simplifies" the `validation_warnings` emission away. The next campaign
runs the service at 10,000 output epochs per pass against a config that says `max_epochs: 200`.
The gate is `ConfigValidationTest.test_max_epochs_without_output_epochs_warns` — a **warning**
test for a **warning**, so removing the warning fails CI, but removing the *guidance* the warning
points at does not. Cost: a multi-hour GPU campaign whose CLI-vs-service comparison is invalid,
which is a failure this project has already paid for (`AGENTS.md:576-578`, ml#1143 §2.2).

**Evidence.**

```text
MECH §4c-bis: | Rules with `paths:` frontmatter | Lost until a matching file is read again |
              | Nested CLAUDE.md in subdirectories | Lost until a file in that subdirectory is read again |
Proposal B §5.2: 11 .claude/rules/*.md  104,488  lazy, per matched path
                 14 nested CLAUDE.md     48,412  lazy, per directory read
```

**Fix.** (1) Settle the read-tracking question before Phase 2 — it is a two-minute probe of the
same class as B's §13.5/§13.6. (2) Independently of the answer, promote the small set of
component hazards whose miss is *irreversible* (not merely a re-read) into the root file as
one-liners, exactly as Proposal C §5.3 does. B's §7.4 residency test — "does violating this cost
something irrecoverable, **before any file has been read**" — is the wrong test under
§4c-bis; the right test is "before any file has been read **or after a compaction**".

### AV-C2 — Proposal A: the re-attach cap drops the *earliest-invoked* skill, and A under-counts by ~3× — MANAGEABLE

**Location**: Proposal A §9.1(c).

**Problem.** A computes 25,000 tokens = 100,000 chars against an 11-body corpus of 101,000 and
concludes a fully-loaded session "would re-attach ten and drop the oldest". The corpus A actually
ships is larger: 101,000 (11 reference bodies) + 11,000 (`reference/` sub-files) + **29,650
measured chars of existing procedural skill bodies** = 141,650 chars ≈ 35,412 tokens against a
25,000-token cap. That is 1.42× over, so roughly **three to four** bodies drop, not one — and
MECH §4a says the drop order is *oldest first*, i.e. the skill invoked **earliest**, which is
typically the one that framed the task.

**Evidence.**

```console
$ wc -c .claude/skills/*/SKILL.md
13998 .claude/skills/service-smoke/SKILL.md
 6177 .claude/skills/template-agent/SKILL.md
 9475 .claude/skills/ui-test-author/SKILL.md
29650 total
```

**Why this is only MANAGEABLE.** A priced the mechanism correctly even if it mis-sized the
consequence, and its two mitigations are real and cheap: every body opens with `## Invariants`
(start-preserving truncation keeps them) and bodies are idempotent, so a dropped body is
re-invocable. Crucially, **A keeps all 16 genre-A directives in the root file**, which MECH
§4c-bis says is *re-injected*. Structurally, A is the better-behaved of the two lazy proposals
under compaction.

**Fix.** State the corpus against the 25,000-token cap including procedural bodies and sub-files,
and make the corpus cap the *token* budget rather than the char budget it currently is.

### AV-C3 — Proposal C: SURVIVES

Nothing C relies on is in MECH §4c-bis's "lost" row. The resident core — including
`## Where To Look` and the 14-item hazard list — is in the project-root file, which is
re-injected. A post-compaction session that has forgotten the content of `docs/REFERENCE.md`
still holds the pointer to it, so the cost of a compaction is exactly one tool call. C is the
most compaction-robust of the four, and it is robust *by construction* rather than by
mitigation. Recorded as a genuine differentiator.

The one caveat: C's Phase 5 optional `.claude/rules/` layer imports AV-C1 wholesale. C flags it
as "borrowing a different proposal's lever" (§7.6) — correct, and it should also be flagged as
borrowing that lever's compaction exposure.

### AV-C4 — Proposal D: SURVIVES

D changes no prose, its inbox files are never loaded, and CI gates are compaction-immune by
construction. Its routing procedure is resident and therefore re-injected. D's only compaction
exposure is inherited: D4 rows 3 and 4 recommend skills and `paths:` rules, so D inherits A's and
B's exposure exactly to the extent a hybrid adopts them.

### AV-C5 — All four: post-compaction re-accretion has no detector — SERIOUS (unnamed by all four)

**Problem.** Immediately after a compaction, the only memory a session can see is the root file.
Lore that lives in a skill body or a rule is gone. A session that then re-derives a fact and
"helpfully" records it writes it **into the root file**, because that is the only surface it can
still see — producing a duplicate of content that already exists in a lazy artifact it cannot
see. This is the exact circular-authority pathology A §1.4 diagnoses (`[skip ci]` lore existing
in four places at once), except now with a *mechanism that regenerates it on every compaction*.

All four cap the root file's size (A: 260 lines/22,000 chars; B: 250/16,000; C: 200/18,000;
D: a rate + level budget), so the **volume** is bounded. **None of them detects the duplication.**
The root file therefore converges on a dense, budget-compliant, partly-redundant restatement of
the lazy corpus, and the corpus cap forces the *lazy* side to be trimmed to make room — deleting
the authoritative copy while keeping the compaction-generated summary.

**Fix.** A duplication lint in the family C already proposes as `tests/test_agents_md_shape.py`:
for each content line in the root file, flag a normalized near-match in the lazy corpus
(`.claude/**/*.md`, `docs/REFERENCE.md`). Report-only is enough — the point is that the condition
becomes visible. This belongs in whatever hybrid wins.

---

## Surface 2 — Discovery failure

Every proposal except D makes some content conditional on the model choosing to load it.

### AV-D1 — "the gate is the memory" is false for at least one live directive, and A, B and D all rely on it — SERIOUS

**Location**: A §9.2 Tier 3; B §7.4 ("108 of 125 are component contracts … safe to make
path-conditional"); D §4 D4 rows 1–2; C §5.1 Q2 (which *caught* this).

**Problem.** Three of the four proposals justify making component lore lazy on the grounds that
the prose was never the enforcement — a wired CI gate is. That premise is false for at least one
directive today, and the directive in question is the repo's own canonical **vacuous-pass**
lesson:

> `tr -d -- '-_'` needs the `--`: some `tr` builds (the Rust coreutils rewrite) parse a
> leading-dash SET as an option, and without it BOTH sides normalize to empty, making the
> mismatch check pass **vacuously**. — `AGENTS.md:483`

Its pin is `tests/test_assert_release_tag.py`. **That test runs in no workflow.**

**Evidence.**

```console
$ grep -rn "assert_release_tag" .github/workflows/ | grep -c "test_assert_release_tag"
0
$ grep -rln "assert_release_tag" .github/workflows/
.github/workflows/publish.yml          # (7 publishers, all invoking the bash script, not the test)
.github/workflows/publish-observability.yml
... (5 more)
```

Independently reproduced across the whole suite — it is the **only** one of 88 test modules
absent from `ci.yml`:

```console
$ python3 - <<'PY'
... tests = sorted(p.name for p in (root/"tests").glob("test_*.py"))
... print([t for t in tests if t not in ci_yml_text])
PY
total tests: 88
absent from ci.yml: ['test_assert_release_tag.py']
```

**Scenario.** Under A this lore lands in `juniper-ml-publish-path` (lazy); under B in
`.claude/rules/publish-path.md` (lazy, read-triggered); under D it routes by D4 row 2 to
`docs/REFERENCE.md` (lazy). A session tidying `util/assert_release_tag.bash` restores the more
idiomatic `tr -d '-_'`. The publish guard's central assertion — tag version equals built wheel
version — passes **vacuously** on every publish thereafter. Nothing goes red, because the test
that would catch it is not wired. The tag-only environment policies remain the real control, so
this is not a catastrophe; it is the silent removal of a defense-in-depth layer, which is exactly
the class the lore exists to prevent.

**Credit.** Proposal C §2.4 #6 found this independently and made its Q2 relocation for that
directive *conditional on wiring the test into CI*, and proposes the mirror lint (G12) that would
have caught it. C is the only proposal whose residency rule survives its own counterexample.

**Fix (binding on any hybrid).** Ship C's **G12 mirror lint** — every `tests/*.py` must be
referenced by at least one workflow — **before** any Q2 / Tier-3 / D4-row-2 relocation. It is
one assertion, it has exactly one violation today, and without it every "the gate holds it"
justification in A, B and D is unverified.

### AV-D2 — Proposal B: `paths:` rules cannot fire on a Bash invocation, and the destructive utilities are invoked, not read — SERIOUS

**Location**: B §7.4 ("Creating a file with `Write` does not [trigger]"), B OQ-3.

**Problem.** B correctly identifies the `Write`-without-`Read` hole. It does not identify the
larger one: MECH §4b says rules with `paths:` trigger *"when Claude reads files matching the
pattern"*. **Running a script is not reading it.** The utilities whose misuse destroys work are
overwhelmingly *invoked*, not edited:

| Utility | How a session touches it | Does B's rule fire? |
|---------|--------------------------|---------------------|
| `util/juniper_chop_all.bash` with `KILL_WORKERS=1` | `Bash` | **No** |
| `util/reap_pytest_orphans.bash` | `Bash` | **No** |
| `util/kill_all_pythons.bash` | `Bash` | **No** |
| `util/experiment_stack.bash --down --all-mine` | `Bash` | **No** |

**Scenario.** A session is asked to "clean up leftover processes before the next run". It has not
opened `util/`; it runs `KILL_WORKERS=1 util/juniper_chop_all.bash`. `host-orchestration.md`
never fires, so the session never learns that `KILL_WORKERS` is opt-in *because* it reaches
outside the pidfile set. A distributed cascor campaign's workers die mid-run. The strict cmdline
filter bounds the blast radius to worker processes — which is precisely the processes the campaign
needs.

**Fix.** For every utility that terminates a process, keep a **one-line hazard in the root file**
(C §5.3's shape), not only a `paths:` rule. Optionally add a `PreToolUse` `Bash` matcher, but that
is D6 territory and contingent on MECH §12.1.

### AV-D3 — All four: `KILL_WORKERS` becomes conditional under every design — SERIOUS

C's resident hazard list (§5.3) is fourteen items and **does not include `KILL_WORKERS`**;
A files it in `juniper-ml-host-orchestration`; B in `host-orchestration.md`; D leaves the prose
where it is but D4 row 2 would eventually route it to `docs/REFERENCE.md`. So the one directive
in this set whose misuse kills live compute is lazy in all four designs.

`docs/REFERENCE.md:497` already carries the disambiguation and is richer than the `AGENTS.md`
copy — which supports relocating the *explanation*. The **one-line hazard** ("`KILL_WORKERS=1`
reaches outside the pidfile set — never set it while a campaign is running") is what should stay
resident, and no proposal keeps it.

### AV-D4 — Proposal A: the `[skip ci]` trap splits across two skills — MANAGEABLE

A's own D2 weakness ("some content is genuinely cross-domain") lands on a dangerous item: the
`[skip ci]` orphaned-checks class is CI (`juniper-ml-ci-workflows`) *and* fleet triage
(`juniper-ml-fleet-triage`). A session that invokes one gets half. Cost is hours, not destroyed
work — the failure is a permanently BLOCKED PR whose rollup can read SUCCESS (cascor#515).
A's `## See also` footer mitigation is adequate.

**Credit to C**: §5.3 item 3 promotes this from three narrative retellings to a stated rule, and
notes the file "narrates this incident three times and states the rule zero times". That is a
genuine improvement produced *by* pruning, and it is the best single argument in C's favour.

### AV-D5 — The 33-pointer observation: evidence about authors, and it is still decisive — verdict

C §7.3 reports that all 33 `Operator surface` pointers in `AGENTS.md` coexist with a full
restatement, and asks whether that is fatal to pointer designs.

**Judgement: not fatal, but it correctly predicts the failure mode, and it makes C's shape gate
load-bearing rather than cosmetic.** Three reasons:

1. It is evidence about *authors*, and the authors here were largely agents operating under the
   same discovery uncertainty the proposals are trying to resolve. "The author did not trust the
   pointer" and "the reader cannot follow the pointer" are different claims; only the first is
   evidenced.
2. The counter-evidence is strong and local: MECH §8b measures the auto-memory index at
   **53 : 1** (1,082,901 bytes on disk, 20,388 loaded) in this very project. An index over a
   deferred corpus demonstrably works here.
3. But the observation does predict what happens next: the *next* session will restate rather
   than trust. That is why C's `tests/test_agents_md_shape.py` forbidding `Operator surface:`
   trailers in the core is not a style rule — it is the mechanism that stops the observed
   behaviour from re-running. Any hybrid that adopts pointers **must** adopt that assertion.

---

## Surface 3 — Concurrency

Measured for this audit: **23 session worktrees** under `.claude/worktrees/`, **285** commits and
**163** first-parent merges touching `AGENTS.md` since 2026-06-01, `docs/REFERENCE.md` 85,
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` 158.

```console
$ ls -1 .claude/worktrees/ | wc -l
23
$ git log --since=2026-06-01 --format=%H -- AGENTS.md | wc -l
285
$ git log --since=2026-06-01 --format=%H -- docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md | wc -l
158
$ git log --since=2026-06-01 --format=%H -- docs/REFERENCE.md | wc -l
85
```

### AV-N1 — Proposal B: the coverage ledger creates a new shared-edit surface its Herfindahl model does not count — SERIOUS

**Location**: B §3.3 (53.5% contention reduction), B §8.1 `tests/test_rules_paths_resolve.py`
clause (d), B §8.1 `tests/test_nested_memory_drift.py`.

**Problem.** B's headline concurrency number models where `AGENTS.md`'s *content* lands. It does
not model where B's own **gates** force edits. Two of them are shared-edit surfaces:

- Clause (d) of `test_rules_paths_resolve.py`: *"every tracked path under `util/`, `tests/`,
  `.github/workflows/` must be matched by at least one rule glob or be explicitly listed in an
  `UNCOVERED` allowlist"*. That is ~65 `util/` scripts + 88 tests + ~25 workflows. **Every PR
  that adds a file in those trees must edit a rule's `paths:` list or the allowlist**, or CI
  fails. B measured `tests/` at 26% and `util/` at 22% of PRs.
- `tests/test_nested_memory_drift.py` is bidirectional against the **root** routing table, so
  every new nested `CLAUDE.md` requires a root-file edit — the collision B claims to eliminate.

**Scenario.** Three sessions on the same day each add a new `util/` script with its gate test.
Under today's monolith all three edit `## Key Files` — visible, conflicting, resolvable. Under B
all three must add their new paths to `.claude/rules/*.md`, and two of them will pick the same
rule file (`experiments.md` and `drift-checks.md` are the two busiest). B has moved the collision
from a section of a 1,115-line file to a 20,000-char file with no CI gate on its content, no
reviewer habit, and no size signal — B's own §7.5 words.

**Fix.** Make clause (d) advisory, or scope it to a curated set of "must be covered" paths rather
than the whole tree. And count the ledger surface in the Herfindahl model before quoting 53.5%.

### AV-N2 — A and B: splitting removes the only duplicate detector the repo has — SERIOUS

**Problem.** The brief asks whether splitting reduces *semantic* conflicts or only textual ones.
It reduces textual ones, and in doing so it **destroys** a mechanism the repo currently relies on
without naming it: a merge conflict in `## Key Files` is the only signal two sessions get that
they have independently discovered the same failure class. Under A (11 skills) and B (26 files)
two sessions writing the same lore into two different destinations never meet.

Semantic conflicts are unchanged by either design: two sessions can still record contradictory
invariants about the same component. Under the monolith they at least contend for adjacent lines.

**Credit to C**: one destination (`docs/REFERENCE.md`) preserves the collision-as-detector
property. Credit to D: its inbox has *distinct filenames by construction*, so it also eliminates
the detector — but D's weekly curation pass is an explicit, scheduled human/agent read of the
whole inbox, which is a *better* detector than a merge conflict. D is the only proposal that
replaces the mechanism it removes.

### AV-N3 — Proposal D: a rolling-window required gate under `strict` branch policy can block a PR through no fault of its author — SERIOUS

**Location**: D D1 ("net bytes added … over a rolling 30 days, measured on `main`"), D3 (the
loan), D2 rule 3 (ratchet interlock).

**Problem.** Three verified facts interact badly:

```console
$ gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
    --jq '.rules[] | select(.type=="required_status_checks") | .parameters.strict_required_status_checks_policy'
true
```

1. `strict_required_status_checks_policy: true` — a branch **must** be up to date before merging.
2. D's rate axis is a function of the last 30 days on `main`, not of the PR's own delta.
3. D3's overrun waiver is a **loan** that "blocks the next author until repaid".

So: to merge, you must update your branch; updating pulls in other people's merges; those merges
enter the rolling window; the required `memory-budget` context re-runs against the new window and
can now fail. **The act required to merge is the act that breaks the check**, and the author has
no repair available — repaying means deleting content they did not add.

**Scenario, with the loan.** A legitimate 3 KB post-mortem lands with `Allow-Budget-Overrun`. The
window is now over budget. There are 23 session worktrees; call it five in-flight PRs touching
`AGENTS.md`. All five fail on their next mandatory update-branch. None created the debt; none can
repay it. Each adds `Allow-Budget-Overrun` because it is the only green path. That is **five
waivers in the window** — and D2 rule 3 requires `<= 1` waiver for the rate step-down. The ratchet,
which is D's entire claim to permanence, is now frozen by the mechanism intended to make overruns
expensive. The loan does not have a "next author"; in a concurrent fleet it has *all* authors, at
once.

**Fix.** Either (a) evaluate the rate against a **window snapshot pinned at the PR's merge base**,
so a PR's verdict is a function of its own delta and does not move under it; or (b) keep the rate
axis **advisory forever** and make only the level axis blocking — the level axis is deterministic
per-commit and has none of this behaviour. D's own §6.2 already soaks the rate axis advisory at
the terminal value; (b) is a small step from there.

### AV-N4 — Proposal D: the weekly curation PR trips the required docs screen every week and trains the wildcard waiver — SERIOUS

**Problem.** D5's inbox lives at `notes/memory-inbox/`. `notes/**/*.md` **is** inside the docs
screen's scope (verified below), and curation *deletes* inbox files. A whole-file deletion is a
deleted heading plus a pure deletion run — both FAIL conditions.

```console
$ python3 -c "from juniper_ci_tools import docs_additions_check as d; print(d.in_docs_scope('notes/memory-inbox/x.md'))"
True
```

So **every weekly curation PR fails the required `Sequence Safety` context** and needs an
`Allow-Docs-Rewrite:` trailer. The cheapest form is the wildcard, and the wildcard is accepted:

```console
$ python3 -c "from juniper_ci_tools import docs_additions_check as d; print(d.parse_allow_trailers('Allow-Docs-Rewrite: *'))"
(set(), True)
```

A blanket `*` waives **every** deleted `.md` in the screened range — and post-merge the G3.1
catch-up base sweeps a *window* of merges, so a `*` in that window silently waives other people's
deletions too. D5 therefore manufactures a weekly habit of writing the exact reflexive waiver
D §5.2 identifies as the failure mode ("a waiver used three times correctly trains everyone to
use it the fourth time without looking").

**Fix.** The curation tool must emit an **enumerated** trailer naming each deleted inbox file,
never `*`. Trivial to generate, since the tool already knows the file list.

---

## Surface 4 — Gate interactions

### AV-G1 — Proposals A and B relocate the corpus **out of the docs-deletion screen's scope entirely** — SERIOUS, bordering FATAL for B

**Location**: A §5 (11 skill bodies under `.claude/skills/`), B §4.2.1 + §4.2.2 (11 rules under
`.claude/rules/`, 14 nested `CLAUDE.md`), B §7.5 ("Sequence-safety screens get quieter").

**Problem.** `Sequence Safety` is a **required** status check on all nine repos as of `e209b74`
(ml#1166). Its docs half runs with **no `--scope`**, i.e. the package default. That default is:

```python
def in_docs_scope(path: str) -> bool:
    """AGENTS.md (+ its CLAUDE.md symlink), docs/**/*.md, notes/**/*.md."""
    if path in ("AGENTS.md", "CLAUDE.md"):
        return True
    if path.endswith(".md") and (path.startswith("docs/") or path.startswith("notes/")):
        return True
    return False
```

Executed against every destination the four proposals name:

```console
$ python3 -c "from juniper_ci_tools import docs_additions_check as d; [print(f'{d.in_docs_scope(p)!s:>5}  {p}') for p in [...]]"
 True  AGENTS.md
 True  docs/REFERENCE.md
 True  notes/x.md
 True  notes/memory-inbox/x.md
False  .claude/rules/experiments.md
False  .claude/skills/juniper-ml-release-train/SKILL.md
False  util/CLAUDE.md
False  tests/CLAUDE.md
False  .github/CLAUDE.md
False  juniper-service-core/CLAUDE.md
```

**A moves 101,000 chars and B moves 152,900 chars from a file under a required deletion screen
into files under no deletion screen at all.** The screen exists precisely because of the
#801/#803 class — a merge that took the branch side and deleted sibling sections merged hours
earlier — and that class returns in full for the relocated corpus, permanently, for a
23-worktree fleet.

**B additionally states the opposite as a benefit** (§7.5): *"Sequence-safety screens get
quieter… After the split, a rewrite of one 400-line rule file is a smaller, better-localised
diff."* The rule file is not screened at all. "Quieter" is "silent".

**Confirmed also**: `Documentation Links` (a required context) *does* cover `.claude/**/*.md`
(the validator's `files: \.md$` and the CI invocation's exclude list do not mention `.claude/`),
and markdownlint covers it too. So the relocated corpus keeps link validation and line-length
linting — but loses the only content-loss alarm.

**Fix (must land in the same PR as the first relocation).** Pass explicit `--scope` globs to the
docs screen in **both** `.github/workflows/ci.yml` and `.github/workflows/main-verify.yml`, since
`--scope` **replaces** the default (verified in the module docstring: *"a caller may pass `scope`
globs … a path is then in scope iff it matches any glob AND ends `.md`"*):

```text
--scope 'AGENTS.md' --scope 'docs/**/*.md' --scope 'notes/**/*.md' \
--scope '.claude/**/*.md' --scope '**/CLAUDE.md'
```

And note the coordination cost nobody costed: the required context name is shared fleet-wide
(ml publishes `Sequence Safety`, the other eight publish `Sequence Safety (Advisory)` — from the
`e209b74` commit body), so a scope change is a nine-repo change if the pattern is rolled out.

### AV-G2 — The docs screen is WARN-only for any deletion hunk containing one added line, at any magnitude — SERIOUS for all four; this is the headline finding

**Location**: C G2 ("It will fire on every phase of this migration — by design"); D §5.4 ("the
budget and the deletion screen form a vise … Compress prose in place → **FAILS** on a ≥5-line
deletion run → blocked"); A §12.10; B Phase 1.

**Problem.** The magnitude rule is a **pure**-run rule. One added line anywhere in the hunk
defeats it, regardless of how much was deleted. Measured directly against the pinned
`juniper-ci-tools` 0.8.0:

```console
del=  5 add=0: [('deletion-run', 'FAIL')]
del=  5 add=1: [('small-deletion', 'WARN')]
del=  8 add=1: [('small-deletion', 'WARN')]
del= 12 add=1: [('small-deletion', 'WARN')]
del= 20 add=1: [('small-deletion', 'WARN')]
del= 40 add=1: [('small-deletion', 'WARN')]
```

`WARN` never fails (the module docstring: *"WARN / WAIVED never fail"*), so the required
`Sequence Safety` context is **green**.

Now apply the shape every proposal prescribes — delete a block, leave a pointer — to the actual
reaper lore, keeping the heading:

```console
$ # two hunks, each deleting 4 sub-bullets and adding "  - see docs/REFERENCE.md"
8 content lines destroyed, no heading:
  [('small-deletion', 'WARN', {'deleted': 4, 'added': 1}),
   ('small-deletion', 'WARN', {'deleted': 4, 'added': 1})]
```

Eight lines of the live-experiment protection lore destroyed; screen green; no trailer needed;
nothing to review.

**Consequences, per proposal:**

- **C's G2 is wrong as stated.** The screen will *not* fire on every phase; it fires on phases
  that remove headings. C's §12.1 row-by-row deletion table can be authored as pointer-substitutions
  that never remove a heading, and then C's stated "existing content-loss alarm" is silent for the
  whole migration.
- **D's §5.4 vise does not close.** D's own table claims "Compress prose in place (delete lines,
  keep headings) → FAILS → blocked". Measured: WARN → green. So the cheapest way to satisfy D's
  byte budget is precisely the move D's design says is mechanically hardest, and it is the
  destructive one.
- **A and B survive better only by accident**: their migrations delete whole `##` sections, so
  the heading rule fires and they need the trailer. Their *subsequent* edits, and any later
  trimming of the residual file, sit in the WARN band.

**Why this matters more than it looks.** The repo's most recent standing lesson (`40230d2`,
ml#1165) is that a net **−4 line** reformat destroyed three owner-decision blockquotes and was
nearly waived as a reflow. The measurement above shows the screen's classification of that shape
is `small-deletion / WARN`. So the discipline "token-diff before waiving; restore, don't waive"
is not a supplement to the screen — for the migration's own edit shape, **it is the only
control**, and no proposal makes it mechanical.

**Fix.** Do not rely on the magnitude screen for migration safety. Make the token/block diff a
**required PR artifact** with a checker: for each migration PR, every removed heading and every
removed content block must be shown present at a named destination path at HEAD. That is C's G1
upgraded from token granularity (see AV-V4) to block granularity, and it should gate all four.
Optionally also file an upstream `juniper-ci-tools` issue: a `--max-net-deletion` rule that
counts per-file net removed lines independently of the pure-run predicate.

### AV-G3 — Proposal A: the mandatory `## Invariants`-first body layout fails an existing required check — MANAGEABLE (cheap fix, but it would have broken Phase 1)

**Location**: A §9.1(b), A §15 (`tests/test_skills_frontmatter.py` asserts "a body opening with
`## Invariants`").

`.claude/` is not in `.pre-commit-config.yaml`'s top-level exclude and the markdownlint hook's
own exclude covers only `CHANGELOG.md|notes/|docs/|prompts/|scripts/test_prompt-.*\.md`, so
skill bodies are markdownlint-checked inside the required `Pre-commit (Python 3.1x)` contexts.
Executed with the pinned hook version:

```console
$ npx markdownlint-cli@0.42.0 --config .markdownlint.yaml probe/SKILL.md
probe/SKILL.md:6 MD041/first-line-heading/first-line-h1 First line in a file should be a
  top-level heading [Context: "## Invariants"]
```

**Fix.** `# <skill name>` H1, then `## Invariants` as the first H2 — ~30 chars, and start-preserving
truncation still keeps the invariants. A's own lint must assert that shape, not the `##`-first
shape.

### AV-G4 — A, B and C wire shared-budget gates into a required, push-triggered context; D alone does not — SERIOUS

**Problem.** All three cutting proposals wire their new gates into the `tests` job
(A: "beside `ci.yml:611-636`"; B: "wire the four new tests into `ci.yml`"; C: "beside `:633-636`").
That job is `Regression Tests (Python 3.12/3.13/3.14)` — three of the fifteen **required**
contexts — and `ci.yml` triggers on `push: main` as well as `pull_request`.

Two consequences:

1. **A breached shared budget blocks every PR in the repo.** If the skill corpus (A) or the
   200-line ceiling (C) is one unit over, a one-line typo fix in `juniper-observability/` cannot
   merge.
2. **Main can go red for a state each PR was individually green on.** A named this precisely
   (D6 risk: two concurrent PRs each under the per-PR budget, corpus crosses on the second merge)
   and proposed PR-scoping — but then specified the corpus check as "a new `ci.yml` step",
   which inside the `tests` job is neither PR-scoped nor separable. **C does not name it at all**,
   and C is the most exposed: a 200-line / 18,000-char ceiling with C's own stated ~1,700 chars of
   headroom is crossed by four PRs at +400 chars each, at 1.3 merges/day.

**Credit to D.** D D1 specifies a standalone `memory-budget` job, `pull_request` + `merge_group`,
`merge_group` short-circuiting green before checkout, **absent from the Quality Gate `needs:`**,
promoted only in the branch ruleset — and cites the exact precedent
(`ci.yml:787-794`, `release-train-archive-guard`). D is the only proposal that gets the CI
topology right, and it should be the template for all of them.

**Fix.** Every shared-budget gate goes in a standalone job on the archive-guard shape. Per-file
deterministic gates (header schema, tree drift) may stay in `tests`.

### AV-G5 — All four: `main-verify.yml`'s battery sync convention already fails 20% of the time — MANAGEABLE

`main-verify.yml` carries a documented obligation: *"SYNC NOTE: the battery list below MUST stay
in sync with `ci.yml`'s `tests` job enumeration … any test added to / removed from `ci.yml` must
be mirrored here in the same PR."* Measured:

```console
total tests: 88
absent from main-verify.yml: 18
```

So the convention every proposal relies on ("wire it into CI") has an observed ~20% miss rate on
its second half. New gates should be assumed **not** to run post-merge unless someone checks.

### AV-G6 — `.claude/rules/` is gitignored — SERIOUS, and correctly named by B, A and D

```console
$ git check-ignore -v .claude/rules/example.md
.gitignore:177:.claude/*	.claude/rules/example.md
$ git check-ignore -v .claude/skills/example/SKILL.md
.gitignore:179:!.claude/skills/**	.claude/skills/example/SKILL.md
```

The negation block re-includes only `!.claude/skills/` and `!.claude/agents/`. Without a matching
pair for `rules/`, every rule file is invisible to git, to CI, and to every other session — and
it **works locally**, so the author sees nothing wrong.

Credit: B §E2 calls this a "non-negotiable prerequisite" and proposes a `git check-ignore`
assertion; A §12.8 requires the negation "in the same PR"; D D4 row 4 names it as "a two-line
prerequisite that is very easy to miss". C mentions it only inside optional Phase 5.

Also verified for D6/Phase 5: `.claude/settings.json` and `.claude/hooks/**` are gitignored by the
same line, and **no active repo settings file exists** — only `settings.local-ORIG_{1..5}.json`
and `settings.local-WORKING.json`, none of which Claude Code reads (MECH §8b, reproduced).

### AV-G7 — The four existing `AGENTS.md` gates: all four target files pass — SURVIVES

Verified against the real gate source:

- `tests/test_agents_md_tree_drift.py:44-49` anchors the fence on `└── util/` **or**
  `├── AGENTS.md`; `:52-59` counts only top-level nodes ending in `/`; `:93-102` requires all
  tracked non-hidden top-level dirs — **18** today
  (`git ls-tree -d --name-only HEAD | grep -v '^\.' | wc -l` → 18); `:114-116` additionally
  requires the literal `agent_templates/` somewhere in the block. A's §7.3 reading is accurate
  and its 23-line minimum is right; B's 42-line and C's 18-node trees also conform.
- `test_agents_md_header_schema.py` (six fields, relative order, ISO date) and
  `test_agents_md_version_drift.py` are unaffected by any proposed trim.
- `agents-md-touch-up.yml` passes when the date is today **or** changed in the PR, and is **not**
  a required context (verified against the ruleset's 15 contexts), so B's claim that skill-only
  PRs escape it carries no orphaned-context risk.

One caveat worth carrying: `_tracked_top_level_dirs` returns `None` when git is unavailable and
the test **skips**. Any proposal that leans on the tree gate as the reason a minimal tree is safe
is leaning on a gate that can skip itself. Pre-existing, not caused by any proposal.

### AV-G8 — Multi-phase migrations and the date check — MANAGEABLE

A ships 9 phases, B 6, C 6, D 6. `agents-md-touch-up.yml` passes a stacked child PR only if the
date value is *already today* (the base carried the bump) or changed in the child's own diff. A
stacked pair that sits overnight fails, and the documented remedy is re-bumping the base. At 1.3
merges/day across 23 worktrees, expect this once or twice per migration. Named in `AGENTS.md`
already; no proposal repeats it.

---

## Surface 5 — The vacuous-pass class

### AV-V1 — Proposal D: SURVIVES, and sets the standard

D §5.3 is the only complete treatment in the four documents. It enumerates four repo-specific
ways its own gate could go vacuous — including the genuinely nasty **`CLAUDE.md` symlink** trap
(the gate would measure identical bytes today and diverge silently later) — and specifies six
negative controls, of which `test_measured_size_matches_ground_truth` ("a checker must be tested
against ground truth it did not compute") is the correct general antidote. It also specifies the
never-vacuous property: the daily alarm always writes current sizes, so a checker measuring
nothing is visible the day it happens.

Minor residual: `test_governed_target_is_agents_md_not_the_symlink` asserts that `CLAUDE.md`
*currently does* share `AGENTS.md`'s bytes, which will go red on the legitimate day someone
replaces the symlink. Make that half a warning.

### AV-V2 — Proposal A: no negative controls, and every gate is empty-list-vacuous — SERIOUS

**Location**: A §15 guardrail inventory.

A's gates iterate `.claude/skills/*/SKILL.md`. With zero matches — a renamed directory, a
`.gitignore` regression, a nesting change to `.claude/skills/juniper-ml/<domain>/` — every
assertion passes: frontmatter is valid for all zero skills, no body exceeds 16,000 chars, the
corpus sums to 0 of 110,000, and the index-drift check is bidirectionally satisfied by two empty
sets. A cites `tests/test_agents_md_tree_drift.py` as its model but does **not** carry over that
model's defining feature — `test_checker_flags_a_missing_dir` at `:109-112`, the synthetic
negative that proves the guard bites. A's §15 has no negative-control row at all.

**Fix.** `self.assertGreaterEqual(len(skills), EXPECTED_MIN)`; a synthetic over-ceiling fixture
that must FAIL; and a corpus-sum assertion against `os.stat` ground truth, per D's discipline.

### AV-V3 — Proposal B: `tests/test_ancestor_dedup.py` can never execute anywhere — SERIOUS

**Location**: B §E4 guardrails, B §8.1.

B's Phase 1 deletes ~6,120 chars from `AGENTS.md` **on the strength of the parent
`Juniper/AGENTS.md` still carrying them** — worktree naming, the script-placement incident, the
handoff policy. Its guardrail is `tests/test_ancestor_dedup.py`, gated like the other cross-repo
drift tests and, in B's words, biting *"weekly in `docs-full-check.yml`, the only job that clones
siblings"*.

It cannot bite there. `docs-full-check.yml` clones **repos** into `$GITHUB_WORKSPACE`:

```yaml
      - name: Clone ecosystem sibling repos (shallow, read-only)
        run: |
          cd "$GITHUB_WORKSPACE"
          echo "$ECOSYSTEM_REPOS" | while IFS= read -r repo; do
            git clone --depth 1 ".../$repo.git" "$repo" || echo "WARNING: Failed to clone $repo"
```

The parent file is not in any repo:

```console
$ ls -d /home/pcalnon/Development/python/Juniper/.git
ls: cannot access '.../Juniper/.git': No such file or directory
$ wc -c /home/pcalnon/Development/python/Juniper/AGENTS.md
11016
```

So the workspace root has no `AGENTS.md`, the test takes its "sibling absent → skip loudly"
branch on every CI run forever, and B's guardrail for its **riskiest deletion** is a gate that
cannot fail. This is the exact class the repo has documented three instances of in one day.

**Fix.** Either (a) do not delete on the strength of the parent, or (b) vendor a hashed snapshot
of the parent into juniper-ml (`conf/ecosystem/parent-agents.snapshot.md`) and drift-check the
live file against it under `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` plus a session-start check — which
is a partial answer to AV-O1 as well.

### AV-V4 — Proposal C: G1, the anti-content-loss gate, passes on the loss it exists to prevent — SERIOUS

**Location**: C §1.2 (Measure B is "a lower bound on loss, not a proof of no loss … it measures
whether the *nouns* survive, not whether the *reasoning* does"), versus C E3 guardrail G8 ("G1
enforces it mechanically: if the destination text is not in the tree, the tokens do not resolve
and the prune PR fails").

Those two statements are incompatible. G1 asks whether each removed backticked token occurs
*somewhere* in the repo. A relocation that copies every identifier into a `docs/REFERENCE.md`
stub and drops every sentence of reasoning passes G1 at 100%. C's own worked example proves the
point: `util/wait_for_checks.py` scores 86% on Measure B *because the identifiers are in the
module docstring* — but the insight C itself flags as unrecoverable ("`stalled` means further
polling cannot change the answer") is paraphrase, and paraphrase is invisible to a token match.

C is honest about this in §1.2 and then relies on the gate anyway in E3. The scenario is C's own
E1 risk, unmitigated: the `predict_merge` nested detail — a pure-deletion PR can be gate-clean and
still `DAMAGED-FIX-FIRST` — is deleted, every token in it resolves elsewhere, G1 is green.

**Fix.** Demote G1 to advisory triage, and promote **G3 (the token diff in the PR body)** from a
convention to a required, machine-produced artifact operating at heading/paragraph granularity —
the same fix AV-G2 needs. One control, two findings.

### AV-V5 — Proposal B: `tests/test_nested_memory_drift.py` has no negative control — MANAGEABLE

B specifies clause (e) "a synthetic negative proves the checker bites" for
`test_rules_paths_resolve.py` — genuinely good, and clause (d)'s two-sided ledger is the best
single anti-vacuous design among the three cutting proposals, because with zero rules every
tracked path is uncovered and the gate fails loudly. It specifies no such control for
`test_nested_memory_drift.py`, whose bidirectional check is satisfied by two empty sets if the
routing-table heading is ever renamed.

---

## Surface 6 — Waiver and incentive design

### AV-W1 — D's `Allow-Budget-Overrun:` loan has no identifiable next author — SERIOUS

Fully argued under AV-N3. Summarised: with 23 session worktrees and `strict` up-to-date branch
policy, an overrun bills every in-flight PR simultaneously; none of them created it; none can
repay it; each clears with another waiver; and >1 waiver freezes the ratchet. The loan's
economics assume a serial write path the repo does not have.

D names two thirds of this itself — *"the loan penalises the wrong person … That is intentional
… and it is also unjust, and both are true at once"* — which is honest, but it stops one step
short of the interaction with the ratchet interlock that makes it self-defeating.

**Fix.** Scope the loan to *the same author or the same file's next author within the PR's own
merge base*, not the global window; or make the rate axis permanently advisory (AV-N3 fix (b)).

### AV-W2 — D's "vise" can be paid with destroyed content — SERIOUS

D §5.4 argues the size budget and the deletion screen are opposed, so relocation is the only
clean path. Measured (AV-G2), the third option — delete a 4-line block, add a pointer line, keep
the heading — is **WARN, green, no trailer**. That is the cheapest possible way to pay a byte
budget, it is exactly the ml#1165 shape, and it is the natural granularity of an `AGENTS.md`
sub-bullet block (the file's 156 nested sub-bullets average well under 5 lines each).

**Fix.** Measure the rate on **additions only**. A net-of-deletions budget actively rewards
destructive offsets; an additions-only budget cannot be paid by deleting someone else's lore.

### AV-W3 — What a session actually does at 02:00, across all four — SERIOUS as a class

The honest answer is: **the cheapest green path**, and each proposal should be judged on what
that path is.

| Proposal | Gate refuses the append. Cheapest green path is… | Where the bytes end up |
|----------|--------------------------------------------------|------------------------|
| A | append to `docs/REFERENCE.md` (162,231 chars, uncapped) or a skill body under its 16,000 ceiling | uncapped reference, or trading inside a capped corpus (requires judgement) |
| B | append to the rule file (20,000 cap, no reviewer habit, no size signal — B's own words) | a capped file with no cultural gate |
| C | append to `docs/REFERENCE.md` — C's E6 weakness (i) concedes "a hard ceiling cannot make the destination attractive" | uncapped reference |
| D | paste `Allow-Budget-Overrun: <file> — <reason>` (one line, **printed in the failure message**) | nowhere; the debt moves |

D's inbox (D4 row 7) is the right answer and the reason D's failure message can never end in
"you have nowhere to put this" — genuine credit. But the inbox costs a *decision* ("is this
really genre B?") while the waiver costs a *paste*, and the failure message advertises the
waiver on its last line. All four also share the displacement target nobody governs:
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, 158 commits since 2026-06-01, the fleet's
second-hottest file, with no size or shape gate. D at least *reports* it (D1 guardrails).

**Fix.** Make the waiver's mandatory reason **contain an inbox path**, so the cheapest green path
routes *through* the capture mechanism instead of around it. That is a three-line change to D's
checker and it converts a hole into a funnel.

---

## Surface 7 — Omissions

### AV-O1 — The parent `Juniper/AGENTS.md`: 11,016 additive bytes, nine repos, no version control, no gate — SERIOUS, and only D names it

```console
$ wc -c /home/pcalnon/Development/python/Juniper/AGENTS.md
11016
$ ls -d /home/pcalnon/Development/python/Juniper/.git
ls: cannot access '.../Juniper/.git': No such file or directory
$ ls -la /home/pcalnon/Development/python/Juniper/CLAUDE.md
lrwxrwxrwx ... CLAUDE.md -> AGENTS.md
```

MECH §7: all discovered files are **concatenated**, not overridden, so those 11,016 bytes are
paid by every session in all nine repos. There is no `.git`: no history, no diff, no review, no
revert, no CI, no gate, and no way for any repo's tooling to see a change.

What each proposal does with it:

| Proposal | Position | Assessment |
|----------|----------|------------|
| A | §16.3 declines to touch it, and D9 **adds ~150 chars to it** for a cross-repo pointer | A writes to the one ungoverned file and does not list that as a risk |
| B | §4.4 **deletes ~6,120 chars from juniper-ml on the strength of it**, guarded by a test that cannot run (AV-V3) | the most exposed position of the four |
| C | §11.2 recommends `claudeMdExcludes` after inlining, treats the saving as unbanked | cautious and honest, but leaves the governance hole |
| D | §9.5 and OD-7 name it explicitly: *"11,016 ungoverned additive bytes with no `.git` at all"* | the only proposal that states the hole as a hole |

**Scenario.** Any session working from `~/Development/python/Juniper/` edits the parent to add an
ecosystem note. There is no PR, no reviewer, no `Sequence Safety` screen, no docs-link check. Six
weeks later every session in nine repos is carrying a stale or wrong ecosystem fact and nobody can
bisect it because there is no history. Under B, the *deleted* juniper-ml content it silently
replaced is gone too.

**Fix, and it should precede all four proposals.** Put the parent under version control before
anything writes to it or deletes on the strength of it — either its own small repo with the same
four `AGENTS.md` gates, or a vendored snapshot in juniper-ml with a drift test (which also
resolves AV-V3). This is a prerequisite, not a phase.

### AV-O2 — Understated or mis-stated weaknesses, by proposal

| ID | Proposal | What was glossed |
|----|----------|------------------|
| AV-O2a | **B** | §7.5 presents the post-split loss of docs-screen coverage as a *benefit* ("screens get quieter"). It is a total loss of coverage on 92% of the corpus (AV-G1). This is the one place a proposal's stated weakness list is not merely incomplete but inverted. |
| AV-O2b | **C** | Does not name the concurrent-merge red-main class for its own ceiling. With 200 lines / 18,000 chars and C's stated ~1,700 chars of headroom, four PRs at +400 chars each — all individually green — turn main red. A named this class for its corpus cap; C's ceiling is tighter and its file is hotter. |
| AV-O2c | **A** | §16 lists seven things A does not solve and omits that A itself writes to the ungoverned parent (AV-O1), and that its gates have no negative controls (AV-V2). |
| AV-O2d | **D** | Phase 5 requires a repo-tracked `.claude/settings.json` (verified gitignored; verified none exists). That file also carries **permissions**. Having agents author the permission surface is in tension with the suite's own standing rule that no agent may change permission settings; it must be an owner-authored artifact, and D should say so. |
| AV-O2e | **All four** | None costs the fleet-wide coordination of changing the shared `Sequence Safety` required context (AV-G1's fix touches nine repos), nor the ~20% observed miss rate on the `main-verify.yml` battery sync (AV-G5). |
| AV-O2f | **All four** | None governs `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (158 commits, 64,267 chars), the demonstrated displacement target. It costs no tokens, so gating it would be wrong — but its *rate* should be reported, and only D does that. |

### AV-O3 — One factual correction to the record

Proposal C §2.4 defect #6 — `tests/test_assert_release_tag.py` runs in no workflow — is
**independently confirmed** here (AV-D1). It is the only one of 88 test modules absent from
`ci.yml`. C files it as out of scope; this audit rates it a **prerequisite** for any hybrid,
because three of the four proposals route content on the assumption it is false.

---

## Summary

30 classified findings.

| Severity | Count | IDs |
|----------|-------|-----|
| **FATAL** | 0 | — |
| **SERIOUS** | 20 | AV-C1, AV-C5, AV-D1, AV-D2, AV-D3, AV-N1, AV-N2, AV-N3, AV-N4, AV-G1, AV-G2, AV-G4, AV-G6, AV-V2, AV-V3, AV-V4, AV-W1, AV-W2, AV-W3, AV-O1 |
| **MANAGEABLE** | 6 | AV-C2, AV-D4, AV-G3, AV-G5, AV-G8, AV-V5 |
| **SURVIVES** | 4 | AV-C3 (C, compaction), AV-C4 (D, compaction), AV-G7 (all four, the existing `AGENTS.md` gates), AV-V1 (D, vacuous-pass) |

Two entries are judgements rather than defects and are not counted: **AV-D5** (the 33-pointer
question) and **AV-O3** (independent confirmation of C's defect #6). **AV-O2a–f** are per-proposal
omission sub-items under AV-O1's surface and are likewise not separately counted.

**Five SERIOUS findings hit all four proposals** and are therefore properties of the problem, not
of any design: AV-C5 (post-compaction re-accretion), AV-D3 (`KILL_WORKERS` becomes conditional),
AV-G2 (the pure-run WARN band), AV-W3 (the 02:00 cheapest-green-path), AV-O1 (the ungoverned
parent). Any hybrid inherits all five.

Excluding those five, SERIOUS findings that name a specific proposal:

| | A | B | C | D |
|---|---|---|---|---|
| Shared by all four | 5 | 5 | 5 | 5 |
| Specific to this proposal (alone or in a subset) | 5 | **9** | **2** | 5 |
| **Total SERIOUS naming this proposal** | 10 | 14 | 7 | 10 |

Read that as a shape, not a score. **C's two** are the lowest because C introduces the fewest new
mechanisms — it borrows no lazy loader and no new destination — but C also delivers the least
protection against re-growth. **B's nine** cluster in one place: its two lazy destinations and the
guardrails meant to hold them. **D's five** are almost entirely in mechanisms the other three do
not have at all, which is what a governance proposal should look like.

**No proposal is FATAL.** Each has at least one SERIOUS defect with a named fix, and each has at
least one property the others lack.

---

## Cross-proposal risk matrix

Worst severity per cell. `—` = the surface does not apply to that proposal's mechanism.

| Attack surface | A (Skills) | B (Path-scoped) | C (Prune) | D (Governance) |
|----------------|-----------|-----------------|-----------|----------------|
| 1. Compaction | MANAGEABLE (AV-C2) + SERIOUS (AV-C5) | **SERIOUS** (AV-C1) | **SURVIVES** + SERIOUS (AV-C5) | **SURVIVES** + SERIOUS (AV-C5) |
| 2. Discovery | **SERIOUS** (AV-D1, AV-D3, AV-D4) | **SERIOUS** (AV-D1, AV-D2, AV-D3) | MANAGEABLE (AV-D3 only; caught AV-D1) | **SERIOUS** (AV-D1, AV-D3) |
| 3. Concurrency | SERIOUS (AV-N2) | **SERIOUS** (AV-N1, AV-N2) | MANAGEABLE | **SERIOUS** (AV-N3, AV-N4) |
| 4. Gate interactions | **SERIOUS** (AV-G1, AV-G4) + MANAGEABLE (AV-G3) | **SERIOUS** (AV-G1, AV-G4, AV-G6) | **SERIOUS** (AV-G2, AV-G4) | MANAGEABLE (AV-G6) — **SURVIVES** on CI topology |
| 5. Vacuous pass | **SERIOUS** (AV-V2) | **SERIOUS** (AV-V3) + MANAGEABLE (AV-V5) | **SERIOUS** (AV-V4) | **SURVIVES** (AV-V1) |
| 6. Waiver / incentive | SERIOUS (AV-W3) | SERIOUS (AV-W3) | SERIOUS (AV-W3) | **SERIOUS** (AV-W1, AV-W2, AV-W3) |
| 7. Omissions | SERIOUS (AV-O1, AV-O2c) | SERIOUS (AV-O1, AV-O2a) | SERIOUS (AV-O1, AV-O2b) | SERIOUS (AV-O1 — named) + AV-O2d |

Read across the rows: **C and D are strong where A and B are weak (compaction, vacuous-pass, CI
topology), and A and B deliver the reduction C only partly and D not at all.** That is the shape
of the hybrid.

---

## The single most dangerous unaddressed risk

**The repo's only mechanical content-loss alarm is structurally blind to the exact edit shape a
memory migration makes — and, under A and B, blind by path to the destination as well.**

The argument:

1. Every proposal names `juniper-docs-additions-check` as the control that will force its
   migration to prove *relocation* rather than *destruction*. C: "It will fire on every phase of
   this migration — by design." D: "the budget and the deletion screen form a vise." A and B both
   require the `Allow-Docs-Rewrite:` trailer and cite the screen as the reason.
2. Measured on the pinned 0.8.0 package, a hunk deleting **40 lines** with **one** added line is
   `small-deletion / WARN`, and WARN never fails. Keeping the heading and replacing a block with a
   pointer line — the shape all four prescribe — is green with no trailer and nothing to review.
3. Under A and B, the content then lands in `.claude/skills/**` or `.claude/rules/**` or a nested
   `CLAUDE.md`, all of which `in_docs_scope` returns **False** for. From that moment there is not
   even a WARN: the #801/#803 wholesale-section-deletion class returns permanently for 92–100% of
   the corpus, in a repo with 23 concurrent session worktrees.
4. This is not hypothetical. This repo has already shipped a **net −4 line** reformat
   (`76e4513`) that destroyed three substantive owner-decision blockquotes and was nearly waived
   as cosmetic; the restoration is `40230d2` (ml#1165), and the standing lesson recorded from it
   is *"token-diff before waiving — restore, don't waive."* The measurement above shows the screen
   classifies that shape as WARN. So the lesson is not a supplement to the screen; for this edit
   shape it is the **entire** control, and it is a convention, not a mechanism.
5. Scaled to a 100,000–153,000-character relocation executed across six to nine PRs by concurrent
   sessions under time pressure, the expected number of silently dropped blocks is not zero, and
   there is no mechanism that would ever surface it. The knowledge would be lost in exactly the
   way the fact base says `AGENTS.md` currently *cannot* lose it (MECH §1: "Nothing is truncated…
   No content is being lost today"). **The migration is the event that introduces the data-loss
   risk the current pathology does not have.**

**The mitigation that must be in the plan before Phase 1 of anything:**

1. A **block-level relocation proof** as a required, machine-generated PR artifact: every removed
   heading and every removed content block shown present at a named destination path at HEAD.
   (This is C's G1 upgraded from token to block granularity, and it fixes AV-V4 at the same time.)
2. Extend the docs screen's `--scope` in **both** `ci.yml` and `main-verify.yml` to cover
   `.claude/**/*.md` and `**/CLAUDE.md` **in the same PR as the first relocation** — noting that
   `--scope` replaces the default, so all five globs must be listed, and that the required context
   is shared across nine repos.
3. Ship C's **G12 mirror lint** first, so "a gate holds this" stops being an unverified claim
   (AV-D1).

---

## Complementary versus compounding

The final plan will likely be a hybrid, so this is the load-bearing judgement.

### Complementary — combine these

- **C + D is the strongest pair, and it is strong for a non-obvious reason.** C cuts the level;
  D holds it. But more importantly, *neither introduces a lazy mechanism that dies at compaction*
  (AV-C3, AV-C4), and *both keep the corpus inside the docs screen's scope* — C's destination is
  `docs/REFERENCE.md`, D's inbox is `notes/**`, both `in_docs_scope == True`. The pair is the only
  combination that does not create the #1 risk above. Their gates also cover each other's worst
  weakness: C owns the G12 mirror lint that fixes D's D4-row-1/2 premise; D owns the negative-control
  discipline (AV-V1) that C's G1 lacks (AV-V4).
- **D's CI topology should be lifted into whichever cutting proposal wins.** The standalone job,
  `pull_request` + `merge_group`, `merge_group` short-circuit, absent from the Quality Gate
  `needs:`, promoted only in the ruleset — that pattern is the fix for AV-G4 in A, B and C alike.
- **B's two-sided ledger (clause (d) of `test_rules_paths_resolve.py`) is the best anti-vacuous
  design among the cutting proposals** and should be lifted into any hybrid, applied to the
  *destination inventory* rather than to `paths:` globs — every relocated subject must have a
  named destination or an explicit `UNCOVERED` entry with a reason. Modelled on
  `tests/test_service_fork_drift.py`, exactly as B says.
- **C's residency rule (§5, Q1/Q2/Q3) and A's Tier-1/2/3 triage are the same idea**, and C's is
  strictly better because Q2 demands a *wired* gate. Adopt C's rule and A's tier vocabulary.
- **A's Phase 0 is worth running regardless of which proposal wins**, as A itself argues: whether
  model-invocable skills auto-invoke here is a fact any design touching skills needs.

### Compounding — do not combine these without a specific fix

- **A + B is the worst combination available.** Both move the corpus into `.claude/**`, so both
  exit the docs screen (AV-G1) and the exposure is additive, not shared. Both add a *resident
  index* to the root file that must be kept bidirectionally in sync (A's `## Skill Index`, B's
  routing table) — two drift gates on the same file, re-creating the root contention both claim to
  remove. And the discovery budgets do not net: A's skill listing (1% of context, least-invoked
  descriptions dropped first) and B's rule count compete for model attention with no shared
  accounting.
- **B + D cancel each other.** D's rate axis governs an explicit list of *resident* targets. B
  moves 92% of the bytes into `.claude/**`, which are lazily loaded — so governing them would be
  "enforcing the wrong thing", exactly as D says about `docs/**`. Under B, D's rate gate polices a
  file that no longer contains the growth, and D's central claim (the ratchet makes the cut
  permanent) becomes vacuous in the strict sense: the number it guards stops being the number that
  matters.
- **A + C compound the authority problem.** A directs new lore to skill bodies; C directs it to
  `docs/REFERENCE.md`. Adopting both without settling authority reproduces the circular-pointer
  pathology A §1.4 diagnoses — `AGENTS.md` → `REFERENCE.md` → `AGENTS.md` — now three-way, with
  the skill body as a third claimant. If both are adopted, one sentence must be written and gated:
  *operator surface lives in `docs/REFERENCE.md`; agent invariants live in the skill; the root file
  points and never restates.*
- **Any cutting proposal + D's rate axis, at required severity, is a deadlock risk** under
  `strict_required_status_checks_policy: true` (AV-N3). The cutting migration is precisely the
  period of maximum byte churn on the governed file. If both ship, the rate axis must be advisory
  for the duration of the migration and promoted afterwards.

---

## Items that could not be verified

Stated so none is mistaken for a verified pass.

| # | Item | Why not, and what it decides |
|---|------|------------------------------|
| 1 | Whether the harness's "`Edit` requires a prior `Read`" bookkeeping survives compaction | No probe available from a read-only audit. Decides whether B's principal compaction mitigation (AV-C1) holds. |
| 2 | Whether `paths:` globs fire on `Glob` / `Grep` results as well as `Read` (B's OQ-3) | Not runtime-tested. The `Bash` case (AV-D2) is settled by T1's wording — running a script is not reading it — but the `Grep` case is genuinely open and would materially improve B. |
| 3 | Whether model-invocable skills auto-invoke in this environment (A §3.1) | No model-invocable skill has ever shipped here (all three set `disable-model-invocation: true`, all three lint-asserted). A's Phase 0 is the right test; A's whole thesis rests on it. |
| 4 | The skill-listing budget constants (8,000 chars, 1,536/entry, the priority ordering) | Binary forensics is validator 1's lane; not re-extracted here. A's §12.5 already flags the priority metric as un-decompiled. |
| 5 | The worktree-ancestor question (MECH §8c, B's U2) | Requires starting a session with a canary; out of scope for a read-only pass. It gates migration ordering for every proposal, not just B. |
| 6 | Whether `MEMORY.md`'s cap is 25,000 or 25,600 bytes | Arithmetic validator's lane. MECH §8b gives `qpe=25000` from shipped code; D §7.1 uses ~25,600 in its headroom table. The difference is ~4 entries / ~4 days. |
| 7 | Whether `/doctor`'s trim proposer behaves as C §10 assumes | TUI-only; not exercised. C already treats it as an accelerant with a hand-reviewed diff, which is the right posture. |
| 8 | Real-world pointer-follow rate (C §7.1) | Nobody can measure it today; C says so. C's §14.2 soak (N ≥ 20, transcript-observable) is the correct design and should be a gate on any pointer-based hybrid. |

---

## Appendix — reproducing every measurement in this document

All commands run from the worktree root at `main` = `e209b74`.

```bash
# --- Surface 4: the docs screen's scope (AV-G1) --------------------------------
python3 -c "
from juniper_ci_tools import docs_additions_check as d
for p in ['AGENTS.md','docs/REFERENCE.md','notes/x.md','notes/memory-inbox/x.md',
          '.claude/rules/experiments.md','.claude/skills/x/SKILL.md',
          'util/CLAUDE.md','tests/CLAUDE.md','.github/CLAUDE.md']:
    print(f'{d.in_docs_scope(p)!s:>5}  {p}')"

# --- Surface 4: the pure-run WARN band (AV-G2) ---------------------------------
python3 - <<'PY'
from juniper_ci_tools import docs_additions_check as d
for ndel, nadd in [(5,0),(5,1),(8,1),(12,1),(20,1),(40,1)]:
    diff  = "@@ -1,%d +1,%d @@\n" % (ndel, nadd)
    diff += "".join(f"-line {i}\n" for i in range(ndel))
    diff += "".join(f"+new {i}\n"  for i in range(nadd))
    fs = d.classify_file("AGENTS.md", d.parse_hunks(diff), d.DEFAULT_MIN_RUN)
    print(f"del={ndel:3d} add={nadd}: {[(f.reason,f.severity) for f in fs] or 'CLEAN'}")
PY

# --- Surface 4: heading deletion FAILs; the correct trailer waives; wrong path does not
python3 - <<'PY'
from juniper_ci_tools import docs_additions_check as d
diff = "@@ -1,4 +1,1 @@\n-## Key Files\n-\n-- `util/x.py` -- lore\n-  - more lore\n+See elsewhere.\n"
h = d.parse_hunks(diff)
print("no trailer  :", [(f.reason,f.severity) for f in d.classify_file("AGENTS.md",h,5)])
fs = d.classify_file("AGENTS.md",h,5); a,w = d.parse_allow_trailers("Allow-Docs-Rewrite: AGENTS.md")
d.apply_waivers(fs,a,w); print("correct     :", [(f.reason,f.severity) for f in fs])
fs = d.classify_file("AGENTS.md",h,5); a,w = d.parse_allow_trailers("Allow-Docs-Rewrite: docs/REFERENCE.md")
d.apply_waivers(fs,a,w); print("wrong path  :", [(f.reason,f.severity) for f in fs])
print("wildcard    :", d.parse_allow_trailers("Allow-Docs-Rewrite: *"))
PY

# --- Surface 2: the unwired gate (AV-D1) ---------------------------------------
grep -rln "assert_release_tag" .github/workflows/          # 7 publishers, script only
grep -rn  "test_assert_release_tag" .github/workflows/     # (no output)
python3 - <<'PY'
import pathlib
root = pathlib.Path(".")
ci = (root/".github/workflows/ci.yml").read_text()
mv = (root/".github/workflows/main-verify.yml").read_text()
tests = sorted(p.name for p in (root/"tests").glob("test_*.py"))
print("total:", len(tests))
print("absent from ci.yml:", [t for t in tests if t not in ci])
print("absent from main-verify.yml:", len([t for t in tests if t not in mv]))
PY

# --- Surface 4: .claude/rules is gitignored (AV-G6) ----------------------------
git check-ignore -v .claude/rules/example.md
git check-ignore -v .claude/skills/example/SKILL.md
git check-ignore -v .claude/settings.json

# --- Surface 4: MD041 vs an Invariants-first skill body (AV-G3) ----------------
D=$(mktemp -d); printf -- '---\nname: probe\ndescription: x\n---\n\n## Invariants\n\n- a\n' > "$D/SKILL.md"
npx --yes markdownlint-cli@0.42.0 --config .markdownlint.yaml "$D/SKILL.md"

# --- Surface 3 / 6: required contexts and strict policy (AV-N3) ----------------
gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
  --jq '.rules[] | select(.type=="required_status_checks")
        | {strict: .parameters.strict_required_status_checks_policy,
           contexts: [.parameters.required_status_checks[].context]}'

# --- Surface 3: concurrency baseline -------------------------------------------
ls -1 .claude/worktrees/ | wc -l                                           # 23
git log --since=2026-06-01 --format=%H -- AGENTS.md | wc -l                # 285
git log --since=2026-06-01 --format=%H -- docs/REFERENCE.md | wc -l        #  85
git log --since=2026-06-01 --format=%H -- docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md | wc -l  # 158

# --- Surface 1: existing skill body sizes (AV-C2) ------------------------------
wc -c .claude/skills/*/SKILL.md                                            # 29,650 total

# --- Surface 4: the tree gate's real surface (AV-G7) ---------------------------
git ls-tree -d --name-only HEAD | grep -v '^\.' | wc -l                    # 18

# --- Surface 7: the ungoverned parent (AV-O1) ----------------------------------
wc -c /home/pcalnon/Development/python/Juniper/AGENTS.md                   # 11,016
ls -d  /home/pcalnon/Development/python/Juniper/.git                       # absent
```

---

## Related documents

| Document | Role |
|----------|------|
| [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) | BASE — sizes, growth, existing gates |
| [Memory mechanism facts](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) | MECH — §4c-bis is the governing fact for Surface 1 |
| [Proposal A](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md) · [B](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md) · [C](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md) · [D](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md) | the four subjects |
| [`../AGENTS.md`](../AGENTS.md) | the file under discussion |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | C's and D's destination; verified richer than the `AGENTS.md` reaper summary |
| [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) · [`../.github/workflows/main-verify.yml`](../.github/workflows/main-verify.yml) | the two places the docs screen runs; both need the AV-G1 `--scope` fix |
| [`../.github/workflows/agents-md-touch-up.yml`](../.github/workflows/agents-md-touch-up.yml) · [`../.github/workflows/docs-full-check.yml`](../.github/workflows/docs-full-check.yml) | the date check (not required) and the sibling-clone job (does not clone the parent) |
| [`../tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) | the tree gate whose real surface is 18 dirs + `agent_templates/` |
| [`../tests/test_assert_release_tag.py`](../tests/test_assert_release_tag.py) · [`../util/assert_release_tag.bash`](../util/assert_release_tag.bash) | AV-D1 — the pin that runs in no workflow |
| [`../util/install_agents.bash`](../util/install_agents.bash) | mirrors every skill dir unconditionally (A §11.1 confirmed) |
| [`../.pre-commit-config.yaml`](../.pre-commit-config.yaml) · [`../.markdownlint.yaml`](../.markdownlint.yaml) | `.claude/**` is markdownlint- and doc-link-covered, but not deletion-screened |
| [Cursor PR flood remediation analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) | the #801/#803 prose-deletion class the docs screen exists for |
| [Thread handoff procedure](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md) | the policy every proposal's compaction answer leans on |
| [notes/ naming convention](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) | this document's filename rules |
