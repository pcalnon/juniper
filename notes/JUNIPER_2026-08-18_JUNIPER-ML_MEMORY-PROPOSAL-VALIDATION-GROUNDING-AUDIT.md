# Memory Proposals — Grounding and Factual-Accuracy Audit (Validator 1 of 3)

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose and standing

This is the **grounding audit** of the four competing shared-session-memory proposals: does
every load-bearing claim survive contact with the repository, the shipped Claude Code
2.1.235 binary, and the two fact-base documents? It is one of three independent validation
passes; it deliberately does **not** assess design merit, only factual accuracy.

Subjects:

- [Proposal A — Skills / progressive disclosure](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md)
- [Proposal B — Path-scoped locality](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md)
- [Proposal C — Deduplication and pruning](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md)
- [Proposal D — Governance and enforcement](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md)

Fact bases:

- [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) (**BASE**)
- [Claude Code memory mechanisms](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) (**MECH**)

All verification was performed in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`
at `main` = `e209b74`, clean tree, 2026-08-18. Binary reads were taken from
`/home/pcalnon/.local/share/claude/versions/2.1.235` (330,946,864 bytes, matching MECH §8b).
Nothing in the repository was modified; this document is the only artifact created.

**Headline: no CRITICAL finding.** No proposal's thesis rests on a false claim. Three MAJOR
findings change a conclusion; two of them are inherited from the fact base rather than
originated by the proposal.

---

## 1. Checklist applied

| # | Criterion | Pass means |
|---|-----------|------------|
| G1 | `file:line` citations resolve and say what is claimed | ≥15 sampled per proposal; misses reported with the actual content |
| G2 | Headline measurements re-derive independently | my figure within stated method tolerance, or the disagreement is adjudicated |
| G3 | Cross-proposal number disputes adjudicated | the correct figure named, the cause of the divergence identified, affected proposals listed |
| G4 | Mechanism claims consistent with MECH | no contradiction; no reliance on a MECH-UNVERIFIED fact without saying so |
| G5 | MECH §4c-bis (post-compaction survival) applied retroactively | no safety-critical content placed in a silently-vanishing mechanism without acknowledgement |
| G6 | Proposal A's three binary readings independently verified | quoted code found verbatim in 2.1.235 |
| G7 | No invented artifacts | every cited path / test / workflow / flag exists, or is explicitly a proposed new artifact |
| G8 | Orchestrator-pre-verified facts stated correctly | the four pre-confirmed items are represented accurately |
| G9 | Internal arithmetic reconciles | tables sum to their stated totals |

Verified claims sampled: **A ≈ 40, B ≈ 35, C ≈ 45, D ≈ 35.**

---

## 2. Adjudications — where two proposals measured the same thing and disagreed

### AD-1 — Mandatory-language line count: 164 (BASE) vs 160 (A) vs 125 (B) vs 124 (D)

**Verdict: every proposal is right about its own predicate. BASE's 164 is the outlier and is
not reproducible from the word list BASE names.**

Measured on `AGENTS.md` at `e209b74`:

| Predicate | Lines | Who reports it |
|-----------|------:|----------------|
| `\b(must\|mandatory\|never\|prohibited)\b` (case-insensitive) | **124** | D §3.3 — exact |
| `must\|mandatory\|never\|prohibited` (no word boundary) | **125** | B §7.4 — exact |
| `\b(must\|mandatory\|never\|prohibited\|always\|required)\b` | **160** | A §1.3 — exact |
| the same six words, no word boundary | 163 | — |
| *any predicate yielding* **164** | not found | BASE §8 |

I tried nine variants (adding `required`, `always`, `shall`, `do not`, `binding`, `only`;
occurrence counts as well as line counts) and could not land on 164. The closest is 166
*occurrences* of the five-word set. BASE §8's figure should be treated as unsourced.

**This does not damage any proposal**, because the load-bearing quantity is the
*distribution*, and three independent measurements agree to within 1 percentage point:

| Proposal | genre-B share of mandatory lines | my re-derivation |
|----------|----------------------------------|------------------|
| A §1.3 | 139 of 160 = 87% | 110 + 21 + 8 = **139 of 160** ✓ exact |
| B §7.4 | 108 of 125 = 86% | 53 + 25 + 10 + 16 + 4 = **108 of 125** ✓ exact |
| D §3.3 | 107 of 124 = 86% | 87 + 16 + 4 = **107 of 124** ✓ exact |

Every per-section row in all three tables reproduced exactly. C §E4's fourth figure (117
lines / 105 = 90%) is the only one I could not reproduce (see C-15).

### AD-2 — `AGENTS.md` size: 170,137 bytes vs 168,317 characters

**Verdict: both correct; all four proposals handle the unit distinction explicitly and
correctly.** `wc -c -m -l AGENTS.md` → `1115 168317 170137`. The 1,820-byte gap is **981
non-ASCII characters** — dominated by box-drawing glyphs in the Repository-Structure tree
(`─` 354, `├` 162, `│` 131, `└` 15) plus `§` 138, `—` 117, `→` 48. D's stated "981
non-ASCII characters" is exact. B's characterization (box-drawing + typographic punctuation)
is more accurate than C's (which names only punctuation), but neither conclusion turns on it.

A works in characters and reconciles to 168,317 exactly. D works in bytes and its 15-section
partition sums to 170,137 exactly under its stated convention. C reproduces BASE's four
per-section figures exactly on a character basis. B is uniformly one character low per row
(see B-9).

### AD-3 — `MEMORY.md` byte cap: 25,000 (shipped) vs 25,600 (A, B, D)

**Verdict: 25,000 is correct.** MECH §2 now states it and MECH §8b sources it to the shipped
constant `qpe=25000`, explicitly "correct[ing] an earlier 25,600 estimate". C §16 uses 25,000
and cites the correction. A §17, B §11 and D §7.1 all use ~25,600.

Effect: headroom is **4,612 bytes, not 5,212** — 600 bytes ≈ 4 entries ≈ 4 days of the
observed 156 B/day rate. See A-MAJOR-1 (A, unflagged) and D-12 / B-4 (flagged or peripheral).

### AD-4 — "This repo has no active `.claude/settings.json`"

**Verdict: the elaboration is false, and it changes C's conclusion.** The literal statement
is true — no project-scope `.claude/settings.json` exists. But MECH §8b's supporting
sentence, "The directory contains only `settings.local-ORIG_{1..5}.json` and
`settings.local-WORKING.json` — none of which are filenames Claude Code reads", is wrong for
the **main checkout**:

```
$ ls -la /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/
-rw-rw-r-- 1 pcalnon pcalnon 1801 Jun  9 12:41 settings.local.json
```

`.claude/settings.local.json` **is** a read filename — it appears **91 times** in the 2.1.235
binary. It is gitignored (`.gitignore:167`), which is why it is absent from the worktree the
fact-finding agent ran in, and absent from this worktree too. See C-11.

---

## 3. Proposal A — Skills / progressive disclosure

### A-CONFIRMED-1 — the accretion-localization measurement is exact

**Claim** (§1.1): 44,567 bytes in nested sub-bullets; 43,842 (98.4%), 154 of 156, inside
`## Key Files`; the remaining two in `## Shared Service-Core Contracts` at `AGENTS.md:175`
"and one sibling".

**Found**: exact.

```
total sub-bullets=156 bytes=44567; in Key Files=154 bytes=43842
NOT in Key Files:
   (175, '## Shared Service-Core Contracts', '  - The `getattr`-based decoupling is deliberate…')
   (176, '## Shared Service-Core Contracts', '  - `resolve()` on an undeclared name raises…')
```

The sibling is `AGENTS.md:176`. BASE §4's 44,350 is the same measurement in characters.

### A-CONFIRMED-2 — the churn attribution reproduces

**Claim** (§1.2): 285 commits since 2026-06-01, 2,011 added lines; `## Key Files` 1,298 lines
/ 225 commits; `## CI/CD Pipelines` 222 / 70; `## Repository Structure` 209 / 114; header
block 103 / 102; `## Build & Package Commands` 69 / 58; the four genre-A sections combined
38 / 10. Of the 225 `## Key Files` commits, **164 (73%) touch exactly one domain**.

**Found**: I reimplemented A's Appendix A procedure independently (reconstruct each commit's
`AGENTS.md`, build a line→H2 map, attribute each `+` line by post-image line number) and got
**every headline figure exactly**: 285 / 2,011 / 1,298-225 / 222-70 / 209-114 / 103-102 /
69-58, and 17+10+5+6 = 38 lines across 10 commits.

Domain shares: release-train 40.2% (120), host-orchestration 25.0% (82), experiments 15.6%
(45), env/install-drift 8.9% (42) — all exact; agent-suite 5.4%/38 vs A's 5.3%/37, fleet
2.3%/8 vs 2.2%/8, other 2.5%/9 vs 2.6%/9 (regex ordering).

Single-domain histogram: mine `{1: 164, 2: 31, 3: 8, 4: 15, 5: 7}` vs A's
`{1: 164, 2: 31, 3: 9, 4: 14, 5: 7}` — one commit moves between the 3- and 4-domain buckets.
**The load-bearing 164 of 225 = 73% is exact.**

### A-CONFIRMED-3 — the genre split is exact

**Claim** (§1.3): 160 mandatory lines distributed 110 / 21 / 8 / 5 / 5 / 4 / 4 / 2 / 1; 139
(87%) in the three relocated sections; 16 genre A.

**Found**: exact, row for row (see AD-1).

### A-CONFIRMED-4 — the three binary readings are correct (independently re-extracted)

This is the mandate's highest-value check: A read three facts fresh from the binary and they
were not independently verified. All three hold.

**§3.1 — skills are model-invocable by default.** Found verbatim:

```js
disableModelInvocation:typeof e.disableModelInvocation==="function"?!0:e.disableModelInvocation??!1,userInvocable:e.userInvocable??!0,
```

Corroborated by the frontmatter reader on a second path — `function fOr(e){return F0e(e)??!1}`,
where `F0e` returns `undefined` for an absent key. **A skill that omits
`disable-model-invocation` is model-invocable.** A's thesis-critical fact is sound.

**§3.3 — the listing budget is exactly 8,000 characters.** Found verbatim:

```js
var B7v=0.01,fgf=4,F7v=200000,U7v=1536
function ecr(e,t=fgf){let r=lee(process.env.SLASH_COMMAND_TOOL_CHAR_BUDGET);if(r)return r;let n=j7v(),o=(e??F7v)*t*n;return Math.max(1,Math.floor(o))}
function j7v(){return qo().skillListingBudgetFraction??B7v}
function Qlr(){return qo().skillListingMaxDescChars??U7v}
```

`200000 × 4 × 0.01 = 8,000` ✓, per-entry cap 1,536 ✓. A's quoted settings description string
("Fraction of the context window (in characters) reserved for the skill listing sent to
Claude (default: 0.01 = 1%)") is verbatim. A's entry-text claim is also verbatim:
`function tcr(e){return e.whenToUse?\`${e.description} - ${e.whenToUse}\`:e.description}` —
so `when_to_use` genuinely shares the description's cap.

**§3.2 — an over-budget skill loses its description entirely.** Found verbatim:

```js
function G7v(e){let t=tcr(e),r=Qlr();return t.length>r?t.slice(0,r-1)+"…":t}
```

and in the solver, exactly A's arithmetic — a funded entry costs `b.name.length+4+S`, an
unfunded one `b.name.length+2`:

```js
m.sort((b,v)=>t(v.cmd)-t(b.cmd));
for(let b of m){let v=b.entryLen-(b.cmd.name.length+2); if(v<=g) g-=v; else y.push(b)}
… budgetMode:"priority", budgetTruncatedSkills:y.map((b)=>b.cmd.name)
```

**All-or-nothing per skill, priority-sorted, start-preserving truncation — confirmed.** A's
§12.5 caveat that the priority metric `t()` is undecompiled is honest and still stands.

**§3.4** also holds: `syncClaudeAiSkills` is described as opt-out with synced skills at
`~/.claude/skills/synced`; and neither `~/.claude/skills/` nor `~/.claude/agents/` exists on
this host (`ls -la /home/pcalnon/.claude/`).

### A-CONFIRMED-5 — citation accuracy is high

Every one of these resolved to exactly the claimed content:

| Cited | Verified content |
|-------|------------------|
| `tests/test_template_agent_skill_lint.py:108-109`, `test_service_smoke_skill_lint.py:157-158`, `test_ui_test_author_skill_lint.py:142-143` | `def test_user_only_invocation` + `assertIs(self.front.get("disable-model-invocation"), True…)` in all three |
| `tests/test_agents_md_tree_drift.py:44-49 / :52-59 / :93-102 / :114-116` | `tree_block()`, `top_level_dir_nodes()`, the 18-dir assertion, the `agent_templates/` assertion — all exact |
| `tests/test_agents_frontmatter.py:27-31` | `_find_repo_root` walking up for `.github/workflows/` |
| `tests/test_release_train_ceremony.py:719` | `class SelectPublishRunTest(unittest.TestCase):` |
| `util/install_agents.bash:99-104` | the quoted `for d in "$SRC_SKILLS"/*/` loop is verbatim (lines 100-103) |
| `util/agent_suite_doctor.py:105` | `skill = root / ".claude" / "skills" / "template-agent" / "SKILL.md"` — hardcoded, as claimed |
| `.github/workflows/agents-md-touch-up.yml:60-64` | `on: / pull_request: / types: / paths: / - "AGENTS.md"` |
| `.github/workflows/ci.yml:804-805` | `sequence-safety:` / `name: Sequence Safety` |
| `.github/workflows/main-verify.yml:196` | `juniper-docs-additions-check --base "$base" --head "$HEAD_SHA"` — no `|| true`, as claimed |
| `docs/REFERENCE.md:493` (4,777 chars) | `## Pytest Orphan Reaper`; section 493-563 measures exactly 4,777 |
| `docs/REFERENCE.md:823 / :829` | the Docs-deletions waiver row; `Allow-Docs-Rewrite: *` **is** accepted — verbatim |
| `docs/REFERENCE.md:1374` | the `[skip ci]` orphan table row inside `## AGENTS.md Date Check` (H2 at :1353) |
| `docs/REFERENCE.md:1719` | "Operator deep-dive …: AGENTS.md CI/CD Pipelines (`main-verify.yml`)" — the circular pointer, verbatim |
| `AGENTS.md:113-114 / :895 / :904-915 / :940 / :1018 / :1034 / :1036 / :1042-1053 / :1110` | all nine Tier-1 directive locations exact |
| `AGENTS.md:431 / :446 / :447 / :453-457 / :681 / :705-709` | all six Tier-3 pin examples exact |
| `.gitignore:176-181` | negates only `.claude/skills/` and `.claude/agents/` |
| `.pre-commit-config.yaml:35-56`, `:226` | the global exclude block (no `.claude/`) and the markdownlint exclude |
| "89 test modules / 65 non-ad-hoc `util/` scripts" | `ls tests/*.py` = 89; `find util -not -path 'util/ad-hoc/*'` = 65 |
| "51 of the 154 sub-bullets name their own pin" | A's own awk reproduces `51 of 154` |
| `e209b74` promoted `Sequence Safety` to REQUIRED on all nine repos | commit body: "`Sequence Safety` is now a REQUIRED status check on all 9 repos" |

Arithmetic also reconciles exactly: §7.2 residual (200 lines / 15,157 chars), §8 crossover
(168,317 − 20,427 = 147,890 = 36,973 tokens; 16.1 invocations), §11.1 (9 × 11 × 350 = 34,650
= 4.3×), §13.1–13.3 (the destination table sums to 168,317 exactly).

### A-MAJOR-1 — §17 uses the superseded `MEMORY.md` cap

**Claim** (§17): "| Bytes | 20,388 | ~25,600 | ~5,212 |" and "The byte axis binds first, at
roughly **35 more entries**."

**Found**: the shipped cap is `qpe=25000` (MECH §8b), so headroom is 4,612 not 5,212. At
MECH §2a's recent-rate 234.8 B/entry that is **~20 entries / ≈19–29 days**, not 35. A's
preamble states "Every mechanism claim below is grounded in doc 2", and doc 2 §2 now says
25,000 — so A contradicts its declared fact base and, unlike D, does not flag the
uncertainty.

**Impact**: understates the `MEMORY.md` horizon by roughly 40%. Blast radius is limited —
§17 exists precisely to say "Proposal A does not help here" — but the number should not
reach the final plan. **Recommended fix**: replace with MECH §2/§2a's 25,000 / 4,612 / ~20
entries / 19–29 days.

### A-MINOR-1 — the "1,561 characters" genre-A figure is not reproducible

**Claim** (§9.2): the 16 genre-A directives "combined … are **1,561 characters** as currently
written (measured across the 13 directive lines themselves)".

**Found**: the 16 genre-A mandatory lines total **1,691 characters** (1,707 with newlines).
Excluding the three heading/restatement lines (`AGENTS.md:904`, `:950`, `:1042`) gives 1,548.
No 13-line subset lands on 1,561. The conclusion ("all 16 fit comfortably inside a 200-line
residual") is unaffected — 1,691 chars is 11% of the 15,157-char budget.

### A-MINOR-2 — binary occurrence counts are understated

**Claim** (§3.1): "The key appears 16 times as `disable-model-invocation` and 33 times as
`disableModelInvocation` in the shipped binary."

**Found**: `20` and `55` respectively (`grep -ao … | wc -l`, cross-checked with `rg -ao`), on
the same 330,946,864-byte file. Decorative, not load-bearing — but wrong.

### A-MINOR-3 — existing skill description lengths are inflated by the YAML key

**Claim** (§6.1): "3 existing procedural skills (`template-agent` 481, `ui-test-author` 414,
`service-smoke` 455, + names) | 1,403".

**Found**: 468 / 401 / 442 — each exactly **13 characters** less, which is `len("description: ")`.
A measured the raw frontmatter line, not the description value. Correct listing cost for the
three: **1,364**, not 1,403.

### A-MINOR-4 — the proposed descriptions are 5.9% longer than tabulated

Measuring A's own §5.1 table text: claimed total 3,535, actual **3,744** (every row 9–30
chars long; `juniper-ml-repo-map` claimed 270 / actual 300). Combined with A-MINOR-3 the
§6.1 listing total becomes **5,440**, not 5,270 — 68% of the 8,000 budget rather than 66%,
still inside A's own proposed 6,400-char gate. No decision impact.

### A-MINOR-5 — §5's source-byte column is approximate, not measured

A presents the column as "UTF-8 **bytes** as measured from the line ranges named". Measuring
those exact ranges:

| Skill | A | measured | Δ |
|-------|--:|---------:|--:|
| 3 experiments, 6 env-drift, 7 agent-suite, 8 fleet-triage | as stated | **identical** | 0 |
| 1 release-train | 23,321 | 22,806 | −515 |
| 2 publish-path | 10,220 | 9,655 | −565 |
| 4 host-orchestration | 6,517 | 5,769 | −748 |
| 5 worktree-ops | 3,900 | 3,460 | −440 |
| 10 shared-packages | 6,607 | 7,086 | +479 |
| 11 repo-map | 22,911 | 23,927 | +1,016 |

Four of nine checkable rows are exact; the total is within 0.5% of A's 145,675. The
deviations look like unstated "less X" adjustments (only skill 9 carries one in the table).

### A-MINOR-6 — "seven sub-bullets" for the reaper entry

`AGENTS.md:407-413` is one top-level bullet plus **six** nested sub-bullets (1,534 chars —
C's figure for the same range is exact). Trivial.

### A-MINOR-7 — D8 places security invariants in a mechanism MECH §4c-bis says vanishes

A's D8 routes the five `juniper-service-core` security invariants to a `paths:`-scoped rule
because "Trigger is a *file read*, not a model decision — so it does not share D3's
false-negative risk". MECH §4c-bis (added after A was commissioned) records that rules with
`paths:` are **lost after compaction until a matching file is read again**. A does not name
that property.

**Mitigating**: A already specifies belt-and-braces — "The service-core invariants remain
**additionally** present in `juniper-ml-shared-packages`, so the rule is a safety net rather
than the sole copy" — and invoked skill bodies *are* re-injected post-compaction. So A's
design survives §4c-bis; only the reasoning is incomplete. A's §9.1 treatment of skill-body
compaction (5,000 tok/skill, 25,000 total, start-preserving) is fully consistent with §4c-bis.

### A-MINOR-8 — the worktree-ancestor migration hazard (MECH §8c) is unaddressed

A's Phases 2–8 are worktree-based PRs that shrink `AGENTS.md`. MECH §8c (added after A was
commissioned) shows the main checkout's `AGENTS.md` is a filesystem ancestor of the worktree
and that the two are currently byte-identical (`md5sum` = `d8f2f655…`, which I reproduced), so
if content-dedup is the reason it is not double-loaded, a trimmed worktree file would make a
session carry **both**. B surfaced this and gives the merge-then-pull sequencing; A does not.
Not A's fault chronologically, but the ordering constraint must be imported into A's Phase 2
if A is chosen.

---

## 4. Proposal B — Path-scoped locality

### B-CONFIRMED-1 — the "97% component lore" headline holds

**Claim** (§3.2): 86,456 of 88,971 chars of `### Utilities` + `### Tests` are component lore;
35 Utilities entries, 57 Tests entries; only 2,515 chars are directory-shaped.

**Found**: independently parsing the top-level bullets in `AGENTS.md:403-596` and `:597-712`
gives **35** and **57** entries exactly, 89,063 chars combined (B: 88,971 — 0.1% apart,
continuation handling), and an unclassified residue of 3,035 chars = **96.6% component lore**
against B's 97.2%. Per-component agreement is close and in three cases near-exact:
experiments mine 26,469 / B 26,460; host-orchestration 6,057 / 6,050; cross-repo-pr 5,892 /
5,889. My unclassified set is exactly the class B describes as fall-through (`util/ad-hoc/`,
the two "moved to a package" pointers, the shared-screen note at `AGENTS.md:463`).

B's §4.2.1 table sums to 104,488 and §4.2.2 to 48,412 exactly.

### B-CONFIRMED-2 — the session-breadth measurement reproduces almost exactly

**Claim** (§3.4): 611 squash-merged commits with files since 2026-06-01; breadth
57/23/9/9/3%; memory-bearing 32/41/18/8/1%; **73% touch at most one memory-bearing directory**;
unit frequency `notes/` 39%, `tests/` 26%, `util/` 22%, root 22%, `prompts/` 20%, `.github/`
18%, `docs/` 8%, `juniper-service-core/` 6%.

**Found**: 626 first-parent no-merge commits, **611 with files** ✓. Breadth
`{1:351, 2:139, 3:51, 4:54, 5+:16}` vs B's `{1:351, 2:139, 3:52, 4:53, 5+:16}` — one commit
between buckets; percentages identical. Memory-bearing `{0:194, 1:251, 2:109, 3:50, 4+:7}` vs
B's `{0:193, 1:252, …}` — one commit between buckets; percentages identical; **73%
cumulative confirmed**. Unit frequencies all match except root (mine 20%, B 22%).

### B-CONFIRMED-3 — the Repository-Structure subtree sizes are exact, nine for nine

B's Tier-1 table depends on splitting the tree by top-level node. Measuring the sub-node
bytes under each node (excluding the node line itself, which is B's convention):

`tests/` 8,765 ✓ · `.github/` 1,126 ✓ · `util/` 4,822 ✓ · `notes/` 933 ✓ · `scripts/` 953 ✓ ·
`.claude/` 902 ✓ · `prompts/` 336 ✓ · `docs/` 332 ✓ · `.serena/` 71 ✓

All nine exact. This is the most precisely-measured table in any of the four proposals.

### B-CONFIRMED-4 — citation accuracy

| Cited | Verified |
|-------|----------|
| `.pre-commit-config.yaml:103,116,136,152,174` | all five are `files: ^(scripts\|tests)/.*\.py$` |
| `.pre-commit-config.yaml:197 / :226 / :263 / :281-285` | ruff sub-package scope; the markdownlint exclude, verbatim; `files: \.md$`; the `no-unencrypted-env` hook |
| `.gitignore:151` and `:176-181` | `.claude/*`; negation of only `skills/` + `agents/` |
| `tests/test_agents_md_tree_drift.py:47` | `if "└── util/" in body or "├── AGENTS.md" in body:` — verbatim |
| `tests/test_agents_md_header_schema.py:26-29` | the self-locating-convention docstring — verbatim |
| `util/install_agents.bash:51-52` | `SRC_AGENTS=` / `SRC_SKILLS=` |
| `.github/workflows/ci.yml:989-990` | the `:fire: touches **AGENTS.md** (a flood hotspot…)` step-summary line |
| `.github/workflows/ci.yml:874-877`, `main-verify.yml:194-196` | the no-`--scope` docs screen, both places |
| `AGENTS.md:538-540` | the F-6 pid rule, verbatim |
| `AGENTS.md:913` | the `/tmp/` scratch-workspace carve-out |
| `AGENTS.md:1018-1020` | worktree-cleanup Phase 7 |
| Parent `Juniper/AGENTS.md` 11,016 B, symlink, section sizes | all eight section figures exact (uniform −1) |
| 23 session worktrees | `ls .claude/worktrees` in the main checkout = 23 |
| `scripts/juniper-all-ctl`, `.yamllint.yaml` | both exist |

Budget arithmetic is exact throughout: 104,488 + 48,412 + 13,836 = 166,736 (−1,581);
182,682 → 28,201 (−84.6% = −154,481); scenario 2 = 28,201 + 13,789 + 13,404 = 55,394
(−69.7%); scenario 5 = 181,101 (−0.9%); §4.3 root table sums to 228 lines / 13,836 chars
exactly.

### B-CONFIRMED-5 — B is the only proposal that got the compaction question right in advance

B §2.2 reported that its brief attributed a compaction fact to MECH that MECH did not then
contain, treated post-compaction persistence of lazy memory as **UNVERIFIED**, and designed
for the worse branch (§7.2, §7.4). MECH §4c-bis now confirms the worse branch is the true
one: `paths:` rules and nested `CLAUDE.md` are lost until re-triggered. **B's guardrails
therefore become load-bearing exactly as B predicted, and nothing safety-critical is placed
lazily by construction.** B's §7.4 residual-17 list (script placement, handoff, worktree
location, never-merge-to-main, `.env`, notes naming, line length / Python floor) is the right
resident set under §4c-bis.

### B-MAJOR-1 — E4's guardrail cannot fire in CI

**Claim** (§6 E4 guardrails): the risk "Parent-file dedup silently breaks" is mitigated by a
new `tests/test_ancestor_dedup.py` that asserts the parent still contains each deleted
directive, "Runs under the same cross-repo gating as the existing drift tests … **It bites
weekly in `docs-full-check.yml`, the only job that clones siblings.**"

**Found**: `docs-full-check.yml:107-110` clones by GitHub repo name —
`git clone --depth 1 "https://github.com/${{ github.repository_owner }}/$repo.git"` — over
`env.ECOSYSTEM_REPOS` (`:79-83`: juniper-data, juniper-cascor, juniper-canopy,
juniper-data-client, …). The parent ecosystem file lives at
`/home/pcalnon/Development/python/Juniper/AGENTS.md`, and **that directory is not a git
repository** (no `.git`; independently confirmed, and stated correctly by D §9.5). There is
no repo to clone and no remote to fetch, so in CI the proposed test can only ever take its
skip path.

**Impact**: E4 is the element that deletes ~6,120 chars from `AGENTS.md` *on the strength of*
the parent carrying them, and B itself names the risk — "No CI in any repo detects a
directive that vanished from a file in a different repository." The named guardrail does not
close that gap. E4's residual risk is unmitigated as designed.

**Recommended fix**: either (a) put `Juniper/` under version control first (D's OD-7), (b)
make the check a local-only `util/` probe invoked from `util/agent_suite_doctor.py`, or (c)
drop the dedup and keep the three-line restatements B already proposes for the two
highest-consequence rules.

### B-MINOR-1 — §3.1's section table does not reconcile to its own total

Every row is one character low (a section-join convention), and `## Thread Handoff` is listed
at 75 lines where the true span `1042-1115` is 74. Summing B's own rows gives **168,302 chars
/ 1,116 lines** against the stated `168,317 / 1,115`. No downstream number depends on it, but
a table that states a total it does not sum to invites a re-derivation.

### B-MINOR-2 — "appears verbatim throughout `AGENTS.md:403-712`"

The phrase "`util/` is not lint-gated, so this unittest is the gate" (and near-variants)
appears **4 times**; "is the gate" appears 8 times. The convention claim is true; "throughout"
overstates its frequency.

### B-MINOR-3 — two citations point at repo-root locators, not header reads

§4.2.2 justifies keeping the header block with "Three CI gates read it
(`test_agents_md_header_schema.py:43`, `test_agents_md_version_drift.py:32`,
`agents-md-touch-up.yml`)". Both cited lines are inside `_repo_root()` helpers
(`if (parent / "AGENTS.md").is_file() and (parent / ".github").is_dir():` and the
`pyproject.toml` analogue) — they locate the file, they do not read the header. The three
gates do read it; the line numbers are wrong.

### B-MINOR-4 — `MEMORY.md` headroom uses the superseded cap

§11 states "~5,200 bytes of headroom" and "≈80% consumed"; MECH §2 gives 4,612 and 82%. See
AD-3. B's section is explicitly "Proposal B does not help. Not partially — not at all", so
the impact is nil.

### B-COULD-NOT-VERIFY-1 — the collision-reduction model

The 28.2% / 48.5% / 53.5% pairwise reductions and the "21 of 285 (7%)" root-contention figure
depend on B's own hunk→destination projection, which I did not reimplement. What I could
check is consistent: 285 commits ✓, `C(285,2) = 40,470` ✓, 18,817 ≈ 46.5% of 40,470 ✓,
header-block commits 102 (B: 104) ✓ within 2, release-train 120 within `## Key Files` (B: 127
including the CI/CD Pipelines subsection) ✓ plausible. The three models' *relative* ordering
— component scoping roughly doubling a directory-only split — follows from the §3.2
measurement I did confirm. Treat the point estimates as model output, not measurement.

---

## 5. Proposal C — Deduplication and pruning

### C-CONFIRMED-1 — all six §2.4 defects are real

This is the strongest evidence base in any of the four proposals. Every defect verified:

| # | Verified |
|---|----------|
| 1 | `util/assert_release_tag.bash:64` parses `--ref`; the flag list is exactly `--ref`, `--dist-dir`, `--expect-prefix`, `-h\|--help`. `:38-41` explains the rejection of the two-flag form verbatim. `tests/test_assert_release_tag.py:42` = `"--ref",`. `AGENTS.md:485` documents `--ref-type` / `--ref-name`. **Documented flags do not exist.** |
| 2 | `AGENTS.md:381` says version `0.6.0`; `pyproject.toml:7` says `0.7.1`; `AGENTS.md:7` says `0.7.1`. |
| 3 | `AGENTS.md:381`'s extras list omits `recurrence`, which the same file carries in the table. |
| 4 | 88 real test files; `### Tests` names **55**; the run block names **54**; 4 appear in `### Tests` only, 3 in the run block only; `test_wait_for_checks.py`, `test_run_suite.py`, `test_juniper_plant_all.py`, `test_publish_testpypi_verify.py` and all four `test_main_verify_*.py` are absent. |
| 5 | The tree omits `codeql.yml`, `agents-md-touch-up.yml`, `pr-budget-alarm.yml`; the `skills/` node lists only `template-agent/SKILL.md` (`AGENTS.md:200-201`), omitting `service-smoke` and `ui-test-author`. |
| 6 | `.github/workflows/ci.yml` names **87 of 88** test files; the sole absentee is `tests/test_assert_release_tag.py`. `AGENTS.md:626` calls it "the gate"; `AGENTS.md:64` puts it in the run block. |

Defect 6 also surfaced independently in my token sweep: `tests/test_assert_release_tag.py` is
one of the 38 backticked tokens that resolve nowhere in the workflow corpus.

### C-CONFIRMED-2 — token recoverability reproduces within 1 point on every row

**Claim** (§2.3): 945 distinct backticked tokens across `### Utilities` + `### Tests` +
`### CI/CD Workflows`; `docs/*.md` 60%, `notes/**/*.md` 82%, code 93%, union **96%**; 36
matched nowhere.

**Found** (independent implementation, 3–60 char backticked tokens over `AGENTS.md:403-742`,
excluding today's memory documents from the notes corpus): 1,006 tokens (6% more than C's,
different filtering) →

| Corpus | mine | C |
|--------|-----:|--:|
| `docs/*.md` | 61% | 60% |
| `notes/**/*.md` | 80% (84% including today's docs) | 82% |
| code | 92% | 93% |
| **union** | **96%** | **96%** |
| unmatched | 38 | 36 |

C's characterization of the residue is borne out: most unmatched tokens are tokenizer
artifacts or globs. C's two named genuine-residue tokens are exactly where C says:
`util/experiments/run_experiment.py:1557` = `"stall_window_inert": stall_inert,` and
`util/experiments/run_suite.py:64` = the `EXECUTION_KEYS` frozenset containing
`per_run_timeout_seconds`.

### C-CONFIRMED-3 — the 15,860-char unique residue is exact, entry by entry

The 71% headline follows definitionally from `1 − 15,860 / 54,510`, so the residue table is
what has to be right. Measuring each `### Utilities` bullet span:

`wait_for_checks.py` 3,632 ✓ · `release_train/ceremony.py` 2,780 ✓ · `open_signed_pr.py`
1,527 ✓ · `assert_release_tag.bash` 1,430 ✓ · `experiments/run_suite.py` 1,048 ✓ ·
`release_train/notes_render.py` 1,026 ✓ · `requirements_drift_check.py` 512 ✓ ·
`scaffold_template.py` 501 ✓ · `template_data_resolver.py` 494 ✓ ·
`template_select_preview.py` 480 ✓ · `generated_prompt_index.py` 465 ✓ ·
`agent_suite_summary.py` 385 ✓ · `get_cascor_*.bash` 325 ✓ · `worktree_cleanup.bash` 802 ✓ ·
sequence-safety screen summary 447 ✓

**Fifteen for fifteen.** Subtotals 11,443 + 4,417 = 15,860 ✓. And none of the six
"needs a new section" subjects has a `docs/REFERENCE.md` heading (73 H2+H3 headings scanned;
28 H2 — D's figure, also exact).

### C-CONFIRMED-4 — the growth and duplication measurements are exact

§9.1: 2026-06-01 = 38,248 ✓, 2026-07-01 = 64,965 ✓, 2026-08-01 = 120,685 ✓, today 170,137 ✓;
derived 891 / 1,797 / **2,909** B/day all exact. §9.2's regrowth milestones (12 / 8 days to
40,000; 42 / 29 to 100,000; 77 / 53 to today's size) all recompute exactly.

§7.2–7.3: `docs/REFERENCE.md` 1,865 lines / 161,487 chars / 162,231 bytes ✓; 16,008 →
59,140 → 162,231 ✓ (August 6,064 B/day ✓); commits since 2026-06-01 — REFERENCE 85 ✓,
cheatsheet 158 ✓, `AGENTS.md` 285 ✓; most recent REFERENCE commit
`604fefc docs(reference): declare the startup port overrides…` ✓ verbatim.

§2.2(a): the reaper entry is 1,534 chars at `AGENTS.md:407-413` ✓, and every one of the seven
`docs/REFERENCE.md` cross-references resolves — `:493` `## Pytest Orphan Reaper`, `:507`
`#### Candidate awk filter (false-positive wall)`, `:517` `#### Live-experiment protection
(checked FIRST)`, `:521` the `e-j-h2h-wide-cap6` incident, `:525-528` the two-row P1/P2 table
with a *Catches* column, `:534` `#### Orphan decision and SKIPPED races`, `:545-551` the
four-row override table. Section headings `:130 ### Service Ports`, `:799 ## Fleet Triage and
Sequence Safety`, `:1226 ## Shared-Package CI Workflows`, `:1843 ## Environment Variables` —
all exact.

§2.2(b): `AGENTS.md:490-499` = 3,632 chars ✓; `util/wait_for_checks.py:20` = "**Trap 1 --
terminal must be defined POSITIVELY.**" ✓; `:28` = "**Trap 2 -- the rollup GROWS…**" ✓;
`grep -rln wait_for_checks --include='*.md'` returns `AGENTS.md` + the one handoff prompt ✓
(plus today's proposals, which post-date the measurement).

§2.2(c): the extras table is 2,050 chars at `AGENTS.md:881-892` ✓; `tests/test_pyproject_extras.py:200`
= `class ExtrasDocsLockstepTest` ✓; `docs/REFERENCE.md:93-94` names the four documented
tables verbatim ✓.

§12 arithmetic reconciles exactly: 152,017/152,018, 16,299, 68,409, 41,544, 157,718,
30,665 / 19,649.

### C-CONFIRMED-5 — C's architecture is unaffected by MECH §4c-bis

C is the only proposal that relies on **no lazy memory mechanism at all**: the ≤200-line root
`AGENTS.md` is re-injected from disk after compaction, and everything else is an ordinary
document reached by a tool call, which compaction treats like any other tool output and which
can simply be re-read. The handoff rule stays resident (§5.3 rule 8), which is the
self-referential requirement §4c-bis cares about. C mentions compaction only twice and never
analyses it, but nothing in the design needs the analysis.

The one place §4c-bis would bite — Phase 5's optional `.claude/rules/` layer — is explicitly
evidence-gated and flagged as "borrowing a different proposal's lever".

### C-MAJOR-1 — the `.claude/settings.json` conclusion is wrong

**Claim** (§8, and §11.2 "Against" (a)): "this repo currently has **no active
`.claude/settings.json`** at all (mechanism fact base §8b), so there is nowhere for a hook to
be configured until one is created"; and "only `settings.local-ORIG_{1..5}.json` and
`settings.local-WORKING.json`, none of which are read filenames".

**Found**: the main checkout carries `.claude/settings.local.json` (1,801 bytes, 2026-06-09),
which Claude Code **does** read — 91 occurrences of the literal `.claude/settings.local.json`
in the 2.1.235 binary. It is gitignored at `.gitignore:167`, which is why it is absent from
worktrees (including this one) and why the fact-finding agent missed it.

**Impact**: the derived conclusion — no home for a `PreToolUse` hook, and creating a settings
file is a prerequisite with "effects beyond this proposal" — is wrong for local scope. A hook
could be configured today in the existing file. The *shareable* argument survives: a
committed, fleet-portable hook still needs a tracked `.claude/settings.json` plus a
`.gitignore` negation. Inherited from MECH §8b, but C builds on it twice.

### C-MINOR-1 through C-MINOR-8 — citation and count slips, none decision-affecting

| ID | Claim | Found |
|----|-------|-------|
| C-MINOR-1 | `recurrence` extras row at `AGENTS.md:887` | it is at `:890`; `:887` is the `servers` row (the `:883-891` table-body citation is exact) |
| C-MINOR-2 | `docs/DOCUMENTATION_OVERVIEW.md:21-61` is a "35-row" table | header at `:25`, data rows `:27-58` = **32** rows |
| C-MINOR-3 | `EXPECTED_EXTRAS` at `tests/test_pyproject_extras.py:141` | the constant is at `:106`; `:141` is `class PyprojectExtrasTest` |
| C-MINOR-4 | "**33** `Operator surface`/`table`/`detail` trailers" | 26 for exactly those three phrases; **32** for BASE §4's broader family (A and D both use 32) |
| C-MINOR-5 | "117 mandatory-language lines … 105 (90%) are component contracts" | predicate unstated and unreproducible (124 / 125 / 160 are the reproducible values). The 86–90% conclusion is corroborated by A, B and D independently. |
| C-MINOR-6 | `### Utilities` (405–596) 54,510 · `### Tests` (599–712) 34,579 | the char figures are the `403-596` / `597-712` spans (heading included); the line labels exclude the heading. Self-inconsistent labelling only. |
| C-MINOR-7 | over-protection rationale at `docs/REFERENCE.md:533` | it is at `:532` (`:533` is blank) |
| C-MINOR-8 | user-global handoff "3,342 (`:8-66`)" | lines 8-66 measure 3,247 chars (whole file 3,349 bytes / 66 lines) |

Two further notes, neither a defect: C's §2.4 defect-4 line label `:39–94` and its elsewhere-used
3,315-char figure bracket the same block — the true span `39-96` is 58 lines / 3,314 chars
(A's `40-93` = 54 lines / 3,119 chars is also exact). And C's Phase 5 `.claude/rules/`
option does not mention the `.gitignore` negation prerequisite that A, B and D all flag —
worth adding if Phase 5 is ever taken.

---

## 6. Proposal D — Governance and enforcement

### D-CONFIRMED-1 — the rate measurements are exact, including the decisive one

**Claim** (§3.2): trailing-30-day net growth from +1,607 (2026-03-31) to **+92,796**
(2026-08-18); 58× in five months; 55% of the file added in 30 days; a cleanup to 34,263 bytes
undone in **44 days**.

**Found**: reproducing D's Appendix A command, **10 of 11 rows land exactly**, including the
headline `+92,796` and every pre-flood reading. The single divergence is 2026-06-23: mine
+2,596 vs D's +2,553 (43 bytes, a `--before` boundary nuance) — it changes neither the
pre-flood median (12,672) nor the maximum (14,580), both of which are exact and both of which
D uses to set the terminal rate budget.

Derived: 92,796/1,607 = 57.7 ≈ 58 ✓; 92,796/170,137 = 54.5% ≈ 55% ✓;
(170,137 − 34,263)/(92,796/30) = **43.9 → 44 days** ✓ exact.

### D-CONFIRMED-2 — the mandatory-language distribution and hook sizing are exact

§3.3's nine-row table, its 124-line total and 144-occurrence count, and 107/124 = 86% all
reproduce exactly (see AD-1). §D6's hook sizing (1,700 + 400 + 200 + 150 = 2,450 B = 1.4% of
the file = 7.5% of the 32,510-byte genre-A residue) is arithmetically exact, and the 32,510
figure matches BASE §8's residue definition under D's own partition
(170,137 − 99,627 − 21,833 − 16,167).

### D-CONFIRMED-3 — the flood-analysis evidence is quoted faithfully

`:36-37` carries the same-file cluster counts verbatim — `AGENTS.md` **54**, cheatsheet **53**,
release-train runbook **34**, `docs/REFERENCE.md` **15**. `:450-451` is quoted verbatim
("Docs … have **only** markdownlint + dangling-anchor check → prose/section deletions have
**no** gate"). `:52` and `:229` carry the #801/#803 wholesale-deletion class and the
**NOT PREVENTED** adjudication. `:502-504` carries the per-class disjoint file scopes.
`:514` carries OQ3 ("whether Cursor reads repo `AGENTS.md` at [generation] is **unverified**").

### D-CONFIRMED-4 — the CI/workflow citations are exact, and unusually well chosen

`ci.yml:720-780` (archive-guard job shape) · `:735-740` (the `merge_group` green notice at
737-740, before the checkout at 742) · `:787-794` (the ADVISORY-not-required rationale) ·
`:791-794` (the "owner + Cursor App always-bypass it … guaranteed value is the visible red at
review" sentence, verbatim) · `:796-803` (the WARN-only label hatch) · `:812-815`
(`fetch-depth: 0`) · `:873-877` (the no-`--scope` docs screen) — **all exact**.

`util/release_train/archive_guard.py:187` = the `Allow-Archive-Edit` `MULTILINE|IGNORECASE`
regex ✓ · `:190-208` = `parse_allow_trailers` ✓ · `:210-215` = `_waives` with the
wildcard/path/basename rule ✓ · `:225` = `change_waived` (D cites `:224-236`) ✓ · `:9-25` =
the four-rule docstring ✓.

`pr-budget-alarm.yml:20-21` (always writes a step-summary table) · `:80-86`
(`PR_BUDGET_WARN:-15` / `PR_BUDGET_ALARM:-30`) · `:149-166` (`continue-on-error: true`,
breach-only Slack) — all exact.

`agents-md-touch-up.yml:21-35` and `:26-33` (the UNSIGNED COMMIT and `[skip ci]` ORPHAN
blocks, cascor#515) — exact. `util/agent_suite_doctor.py:13-14` (exit codes), `:36`
(`OK, WARN, FAIL = …`), `:167-186` (`check_discovery` fail-closed) — exact.
`tests/test_agents_md_tree_drift.py:109-112` is reproduced **verbatim**, comment included.
`tests/test_agents_md_header_schema.py:40-45` = `_repo_root()` — exact. Every "modelled on"
test exists (`test_archive_guard_workflow.py`, `test_ci_sequence_safety_hatch.py`,
`test_agent_suite_path_drift.py`).

`e209b74` is quoted correctly on both counts: it promoted `Sequence Safety` to REQUIRED on all
nine repos in the ruleset, and its pre-flight note contains both "the suffix is part of the
job name and must stay in the context string" and "a required context that never reports is
never satisfied".

### D-CONFIRMED-5 — the `MEMORY.md` measurements and the parent-repo hole

§7.1: 139 lines / 20,388 bytes / 20,049 chars / **146.7 mean bytes per line** / **153 sibling
topic files** / no frontmatter or HTML comments — all exact. §7.2's arithmetic is internally
exact (5,212 ÷ 146.7 = 35.5; binds at ≈174 lines; 61/35 = 74% overstatement) and §7.4's
per-entry-cap saving (139 × 146.7 = 20,391 → 139 × 120 = 16,680, freeing 3,711 B ≈ 31 entries)
recomputes exactly. The longest entry is 791 characters ✓.

§9.5: `/home/pcalnon/Development/python/Juniper/` contains **no `.git`** ✓ — D is the only
proposal to state this, and it is the fact that invalidates B's E4 guardrail (B-MAJOR-1).

§5.3's vacuous-pass trap 1 is also real: `AGENTS.md` and `CLAUDE.md` are byte-identical today
(`md5sum` = `d8f2f6558a4fccfecf4a0fc5f32fa2db` for both), so a gate that measured the symlink
would pass identically and diverge silently later.

### D-MINOR-1 — §3.1 excludes the file-creation commit but presents itself as complete

**Claim**: "First-parent (main-line) accounting of **every merge** that touched `AGENTS.md`" —
Total 200 commits / 172 grew / 14 shrank / **+164,626**.

**Found**: including the commit that created the file, the totals are **201 / 173 / 14 /
+170,137**. February is the only divergent row (D: 1 commit / +3,028; mine: 2 / +8,539), and
170,137 − 164,626 = 5,511 is exactly the creation commit's size. D's derived statistics are
self-consistent with the exclusion (mean growing merge +972 recomputes to 972.8 only when the
creation commit is excluded; max +13,835 is exact either way), so this is a labelling problem,
not a calculation error — but the stated net does not reconcile to the file's actual size, and
"172 of 200" should be "173 of 201".

**Unaffected and exact**: 14 shrinking merges removing **2,628 bytes** total, largest single
reduction **−393** (`34f44864`, 2026-07-01), August **35 merges / 33 grew / 0 shrank**.

### D-MINOR-2 — two flood-analysis slips

The Cursor integration id is at `:34`, not `:33`. And "three of the five always-bypass actors
can click-merge past every non-nuclear stage" over-attributes: the source
(`:447-449`) attaches that parenthetical specifically to `RepositoryRole 5` (admin=owner)
while listing five bypass actors in total. The substantive point — that bypass actors
including the Cursor App can merge past the gate — is correct and is separately stated at
`ci.yml:791-794`.

### D-MINOR-3 — `ci.yml:775` off by one

The trailers-file line `git log --format=%B FETCH_HEAD..HEAD > archive-guard-trailers.txt` is
at `ci.yml:776`.

### D-MINOR-4 — the two August figures are both right and unlabelled

§3.1 reports August at **+50,430** (sum of merges dated in August) while §D1 reports
**+49,452** (the 2026-08-01 → HEAD calendar delta, which I confirmed exactly, along with the
+190 net lines and 260 B/line). Both are correct under their own definition; the document
does not say which is which.

### D-MINOR-5 — the `MEMORY.md` cap, flagged

D uses ~25,600 (see AD-3) but **also gives the 25,000 arithmetic** ("≈30 days"), records it as
OQ-2, lists it in §12.2 as "the single highest-consequence unverified fact in the document",
and proposes a canary entry to settle it empirically. This is the model treatment of an
uncertain constant; the number is nonetheless superseded and should be updated to 25,000 /
4,612, and — per MECH §2a, which was written partly in response to D — to ~20 entries / 19–29
days on the recent-rate basis rather than ~35 / ≈33.

### D-MINOR-6 — the D7 dead-referent scan is not reproducible as stated, but its findings are

**Claim**: "164 distinct path-shaped backtick tokens, **7 unresolved**", all seven false
positives, "100% false-positive rate at this implementation".

**Found**: a naive implementation gives 268 path-shaped tokens and 70 unresolved — D's
extractor is evidently much more selective, and D does not publish it. However **all seven
named tokens verified**: `util/generate_dep_docs.sh` appears exactly **4 times** ✓,
`scripts/generate_dep_docs.sh` ✓, `scripts/check_doc_links.py` ✓,
`util/ad-hoc/2026-08-10_driver_stall_shim.py` ✓, and the two sub-package-relative paths
resolve one directory down exactly as D says
(`juniper-service-core/tests/test_ws_tunables.py`,
`juniper-service-core/juniper_service_core/websocket/tunables.py`) ✓,
`artifacts/results/stats.json` is a runtime path ✓. D's qualitative conclusion — the naive
signal is all false positives here — holds; my broader scan adds `util/sequence_safety/`,
which is also a deliberate anti-resurrection reference.

### D-MINOR-7 — D4 rows 3–4 route content into compaction-fragile mechanisms without saying so

D's routing table gives `.claude/rules/<name>.md` with `paths:` a resident cost of "~0 until
triggered". Under MECH §4c-bis that content is **lost after compaction until a matching file
is read again**. D mentions compaction zero times. Mitigating: D explicitly changes no prose
placement itself (§2 non-goals), its own new artifacts (the inbox) are never loaded at all,
and its CI/hook elements are compaction-immune by construction — so the design is unaffected;
only the routing table's cost column is incomplete. If D's D4 becomes the fleet's routing
policy, row 4 needs a "does not survive compaction" note.

---

## 7. Cross-cutting checks

### The orchestrator's four pre-verified facts are stated correctly

| Fact | A | B | C | D |
|------|---|---|---|---|
| `.claude/rules/` is gitignored; only `skills/` + `agents/` re-included | ✓ `.gitignore:176-181`, and A requires the negation in the same PR | ✓ cites `:151` **and** `:176-181`, calls it a "non-negotiable prerequisite" | not mentioned (Phase 5 only) — see C §13 note | ✓ `.gitignore:172-181`, "a two-line prerequisite that is very easy to miss" |
| `Juniper/` is not a git repository | — | — (and B-MAJOR-1 depends on it) | — | ✓ §9.5, stated explicitly |
| `tests/test_assert_release_tag.py` is in zero workflows | — | — | ✓ defect #6, verified | — |
| `AGENTS.md:485` documents flags the script does not parse | — | — | ✓ defect #1, verified | — |

### Reliance on MECH-UNVERIFIED facts

All four cite MECH §8 item 6 (no published adherence benchmark) when making the
smaller-is-better argument — honest across the board. B §4.4 and C §11.2 both flag MECH §8
item 3 (`Rzr(r.path)` unconfirmed) before relying on `claudeMdExcludes`; C additionally
declares the 11,016 bytes "unbanked" until verified. D §9.5 names `claudeMdExcludes` as a
lever without citing §8 item 3 — a small omission in a section whose point is that no lever
in D reaches the parent. A §12.7 explicitly flags its own sub-file-loading assumption as an
inference and prices what breaks if it is wrong. No proposal upgrades an inference into a
fact.

### Invented artifacts

**None found.** Every path, test module, workflow, console script and CLI flag cited as
existing does exist; every non-existent artifact is explicitly proposed (new skills, new
`.claude/rules/*.md`, new nested `CLAUDE.md`, `conf/memory_budget.toml`,
`util/memory_budget_check.py`, `notes/memory-inbox/`, and the seven proposed `tests/test_*.py`
gates). Both `util/ad-hoc/` scripts cited by the fact base exist. The one flag-level defect in
the corpus — `--ref-type` / `--ref-name` — is a defect **in `AGENTS.md`** that C correctly
identifies, not an invention by any proposal.

### MECH §4c-bis retroactive check — summary

| Proposal | Safety-critical content in a lazy mechanism? | Verdict |
|----------|----------------------------------------------|---------|
| A | Genre-A directives all stay in the re-injected root; skill bodies **are** re-injected (capped); D8's `paths:` rule holds security invariants but is duplicated into a skill body | **Survives.** Reasoning incomplete (A-MINOR-7), design intact |
| B | Explicitly designed for the pessimistic branch before the fact existed; §7.4 keeps the 17 irrecoverable-consequence directives eager | **Survives, and predicted the fact.** Its guardrails are now load-bearing rather than redundant |
| C | Uses no lazy memory mechanism; root file is re-injected; handoff rule resident | **Survives.** Least exposed of the four |
| D | Changes no placement; inbox never loaded; hooks/CI compaction-immune. D4 row 4 recommends `paths:` rules without the caveat | **Survives.** Routing-table cost column incomplete (D-MINOR-7) |

**No proposal puts safety-critical content somewhere that silently vanishes post-compaction
without either acknowledging it or providing a redundant copy.**

---

## 8. Summary

| Severity | A | B | C | D | Total |
|----------|--:|--:|--:|--:|------:|
| CRITICAL | 0 | 0 | 0 | 0 | **0** |
| MAJOR | 1 | 1 | 1 | 0 | **3** |
| MINOR | 8 | 4 | 8 | 7 | **27** |
| CONFIRMED (finding groups) | 5 | 5 | 5 | 5 | **20** |
| Could not verify | 0 | 1 | 0 | 0 | **1** |

Fact-base findings surfaced along the way (not charged to any proposal): BASE §8's 164 is not
reproducible from its stated word list (AD-1); MECH §8b's "none of which are filenames Claude
Code reads" is wrong for the main checkout (AD-4); MECH §8b's "154 auto-memory topic files"
is 154 directory entries = 153 topic files + `MEMORY.md`; MECH §2a's oldest-topic-file date
is 2026-04-08 by mtime, not 2026-04-09 (changes 1.061 → 1.053 entries/day, immaterial).

### Could not verify

- **B's collision model** (28.2% / 48.5% / 53.5%; 21 of 285 root commits). Reproducing it
  requires reimplementing B's hunk→destination projection. All measurable inputs check out
  and the internal arithmetic is consistent; treat the point estimates as model output.
- **A's skill-9 source size** (11,925 bytes) is defined by hand-subtraction ("less
  publish/release rows") and is not mechanically checkable.
- **C's Measure-A subject-coverage judgements** for the 20 entries under 500 characters were
  hand-corrected by C and were not re-adjudicated here; the 15 entries that drive the 15,860
  residue were all verified exactly.

---

## 9. Per-proposal grounding scorecard

### Proposal A — Skills / progressive disclosure

**Sampled**: ~40 claims (12 `file:line`, 3 binary readings re-extracted from
`/home/pcalnon/.local/share/claude/versions/2.1.235`, 6 headline measurements, ~15 arithmetic
reconciliations, 1 fleet-state check).
**Misses**: 1 MAJOR (superseded `MEMORY.md` cap), 8 MINOR (a non-reproducible 1,561; binary
occurrence counts 33/16 → 55/20; existing skill descriptions +13 each; proposed descriptions
+5.9%; 5 of 9 source-byte rows off by up to 1,016; "seven sub-bullets"; D8 compaction
unstated; §8c worktree hazard unaddressed).

**Verdict: sound.** The three binary readings the whole thesis rests on are correct, verbatim,
and confirmed on two independent code paths. The churn and genre measurements reproduce
exactly. The misses are peripheral counts, not load-bearing facts; the one MAJOR is in the
section A itself designates as out of scope. Build on it — but re-measure the §5 source-byte
column before Phase 3 sizes any skill body, and import B's §8c sequencing into Phase 2.

### Proposal B — Path-scoped locality

**Sampled**: ~35 claims (14 `file:line`, 4 headline measurements re-derived, 9 subtree
measurements, ~8 arithmetic reconciliations).
**Misses**: 1 MAJOR (E4's ancestor-dedup gate cannot fire in CI), 4 MINOR (§3.1 table does not
sum to its stated total; "appears verbatim throughout" = 4 occurrences; two locator lines
cited as header reads; superseded `MEMORY.md` headroom). 1 could-not-verify (the collision
model).

**Verdict: sound, with one guardrail to redesign.** The measurement work is the most precise
in the set — nine subtree sizes exact, session breadth exact, component classification
reproduced at 96.6% against a claimed 97%, every budget table summing exactly. B is also the
only proposal that got the compaction question right *before* the fact base recorded it.
The MAJOR is confined to one element's guardrail, and B's own risk narrative already names
the exposure; fix the guardrail, keep the analysis.

### Proposal C — Deduplication and pruning

**Sampled**: ~45 claims (20 `file:line`, all six §2.4 defects re-verified end to end, 4
headline measurements re-derived independently, ~10 arithmetic reconciliations).
**Misses**: 1 MAJOR (the `.claude/settings.json` conclusion, inherited from MECH §8b), 8 MINOR
(all line-number or count slips: `:887`→`:890`; 35 rows→32; `:141`→`:106`; 33→26/32
trailers; the unreproducible 117; heading-inclusive/exclusive range labels; `:533`→`:532`;
3,342→3,247).

**Verdict: sound, and the best-evidenced of the four.** All six claimed defects are real and
independently confirmed — including the one the orchestrator pre-verified and the one my own
token sweep rediscovered by accident. The 15,860-char residue table is exact fifteen times
out of fifteen; the token-recoverability percentages reproduce within a point on every row;
the growth and duplication measurements are exact. The MINOR density is higher than the
others', but every one is a pointer slip around a claim that is itself true. Correct the
settings-file conclusion and the eight citations, and this is the most reliable factual base
in the set.

### Proposal D — Governance and enforcement

**Sampled**: ~35 claims (18 `file:line` across four workflows and three modules, 4 headline
measurements re-derived, the flood-analysis quotations, ~8 arithmetic reconciliations).
**Misses**: 0 MAJOR, 7 MINOR (the creation-commit exclusion presented as a complete
accounting; two flood-analysis slips; `ci.yml:775`→`:776`; two unlabelled August figures; the
superseded but flagged `MEMORY.md` cap; a non-reproducible D7 token count whose findings all
check out; D4 row 4's missing compaction caveat).

**Verdict: sound.** The decisive number — the +92,796 trailing-30-day rate and the 44-day
regrowth it implies — is exact, as is the 86% genre-B concentration that sizes D6 honestly
downward. D's workflow citations are the most precise in the corpus, and D is the only
proposal to identify the ungoverned, unversioned parent file. Its handling of its own
uncertain constant (§12.2 plus a canary test) is the standard the others should be held to.
Fix the §3.1 header row to 173/201/+170,137 and label the two August figures.

---

## 10. Related documents

| Document | Role |
|----------|------|
| [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) | BASE — the measured fact base audited against |
| [Claude Code memory mechanisms](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) | MECH — the mechanism fact base audited against |
| [Proposal A](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md) · [B](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md) · [C](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md) · [D](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md) | the four subjects |
| [`../AGENTS.md`](../AGENTS.md) | the file every measurement is about |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | the 162,231-byte operator reference the duplication claims are measured against |
| [`../util/ad-hoc/2026-08-18_agents_md_growth_curve.bash`](../util/ad-hoc/2026-08-18_agents_md_growth_curve.bash) | the committed growth-curve reproducer |
| [notes/ naming convention](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) | this document's naming rules |
