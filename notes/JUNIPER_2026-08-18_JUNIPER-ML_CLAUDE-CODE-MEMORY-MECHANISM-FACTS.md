# Claude Code Memory Mechanisms — Verified Fact Base

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose

Verified mechanism facts for the 2026-08-18 shared-session-memory design effort,
established by a dedicated research agent against official documentation and the
shipped Claude Code **2.1.235** binary on this host.

**Every proposal must ground its mechanism claims here.** Where a fact is
unverified it is labelled as such — do not upgrade an inference into a fact.

Source tiers: **T1** = official docs (`code.claude.com/docs`); **T1-BIN** = the
installed 2.1.235 binary; **T2** = Anthropic engineering blog; **T3** =
`agents.md` standard; **T4** = `anthropics/claude-code` issues.

---

## 1. There is no hard limit on CLAUDE.md, and nothing is truncated

> "This limit applies only to `MEMORY.md`. CLAUDE.md files are loaded in full
> regardless of length, though shorter files produce better adherence."
> — T1, `/docs/en/memory`

The "character limit" being hit is a **CLI performance warning**, not a limit:

```js
o.push(`Large ${a} will impact performance (${cf(s.content.length)} chars > ${cf(i)})`)
```
— T1-BIN, byte offset 312824648

The threshold is computed, not fixed:

```js
function SUn(e=Gi()){let t=Vk(e,jC()),r=Number.isFinite(t)&&t>0?t:jLr;
  return Math.max(qSv,Math.round(r*WSv*eR(e)))}
// WSv = 0.05, qSv = 40000, eR() -> 4 or 3 chars/token
```
— T1-BIN, byte offsets 301469991 / 301485885

On a 200k-token model this evaluates to exactly **40,000 characters** — which is
why third-party posts all report "40,000". **40,000 is a floor constant inside a
`max()`, not the rule.**

Four consequences that matter here:

1. **The check is PER-FILE, not aggregate** (`r.content.length > t`). Our
   170,137-char `AGENTS.md` trips it alone, at 4.25× the floor. The ~204,890-char
   aggregate is never measured — so *splitting one file into several sub-40K files
   would silence the warning while saving exactly zero tokens.* Any proposal must
   optimise for tokens, not for the warning.
2. **Nothing truncates, drops, or elides.** The warning is pushed onto a status
   array beside "MCP servers" and "Setting sources".
3. It covers types User / Project / Local / Managed — our user-global,
   parent-directory, and repo files each count **separately**.
4. It excludes `AutoMem` — `MEMORY.md` is governed by a different, genuinely hard
   limit (§2).

**Implication.** No content is being lost today. The cost is tokens and
attention, not data. This lowers the urgency but does not remove the problem —
see §6.

---

## 2. `MEMORY.md` DOES have a hard limit — and we are near it

> "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first,
> are loaded at the start of every conversation. **Content beyond that threshold
> is not loaded at session start.**"
> — T1, `/docs/en/memory`

> "If the file is over a limit, the write still succeeds, but Claude Code returns
> an error telling Claude to rewrite the index, because everything past the limit
> is dropped on the next load."

Frontmatter and block-level HTML comments are stripped before measuring
(v2.1.211+).

**Our position as of 2026-08-18:**

| Measure | Value | Limit | Headroom |
|---------|-------|-------|----------|
| Lines | 139 | 200 | 61 lines |
| Bytes | 20,388 | 25,000 | 4,612 bytes |

**82% consumed on the byte axis, and growing.** (The cap is `qpe=25000` bytes in
the shipped code — see §8b, which corrects an earlier 25,600 estimate.)

### 2a. How long until it truncates — and which entries die

**Bytes bind long before lines.** The nominal 61-line headroom is misleading: the
byte cap is reached first, and entries have been getting longer.

Measured 2026-08-18:

| Sample | Bytes | Bytes/entry |
|--------|-------|-------------|
| 20 oldest entries | 2,688 | 134.4 |
| 20 newest entries | 4,695 | **234.8** |

Entries are **75% longer** than they were. Remaining budget is
`25,000 − 20,388 = 4,612` bytes, so:

| Basis | Entries remaining | Binds at line |
|-------|-------------------|---------------|
| Blended average (146.7 B) | ~31 | ~170 |
| **Recent rate (234.8 B)** | **~20** | **~159** |

Against the observed ≈1.06 entries/day, the honest horizon is **≈19–29 days**,
and the recent rate is the better predictor. Proposal D independently derived
~35 entries / ≈33 days using a blended average and explicitly flagged that
calculation as the one most likely to be wrong; checking it moved the answer in
the **dangerous** direction, roughly halving the horizon.

**The loss is newest-first, and silent.** Truncation keeps the *first* 200 lines
/ 25,000 bytes, and the index is append-ordered — so the content dropped is the
**tail**, i.e. the most recently learned facts. The worst possible ordering: the
newest, least-redundant, hardest-won entries are the first to vanish, with no
error surfaced at read time.

### 2b. The remedy is eviction, not a per-entry cap

Identified by synthesis agent 1 and reconciled here against two independent
counts. The index carries a large tail of entries whose work is **finished** —
marked CLOSED / RESOLVED / COMPLETE / SHIPPED / REFUTED (and FIXED / DONE):

| Match | Entries | Bytes | vs 4,612-byte headroom |
|-------|--------:|------:|------------------------|
| Strict, uppercase only | 24 | 4,147 | **90%** |
| Synthesis 1 (case-insensitive, 5 markers) | 35 | 5,471 | **119%** |
| Broad (case-insensitive, + `fixed`/`done`) | 43 | 6,844 | **148%** |

**Every count recovers most or all of the headroom**, and the operation is nearly
free: the auto-memory *topic file* survives on disk (§8b: 154 files / 1,082,901
bytes, of which only the index loads), so evicting an index line demotes a closed
item from resident to on-demand rather than deleting it.

Compare the alternative lever, a per-entry character cap: 120 bytes frees 3,873
but requires rewriting **113 of 139** entries; 150 bytes frees only 1,892 while
touching 20. Eviction is strictly better — more bytes, far less churn, no
rewriting of live entries, and no information destroyed.

**Conclusion: `MEMORY.md` is a nearer-term and harder problem than `AGENTS.md`.**
`AGENTS.md` is oversized but loses nothing. `MEMORY.md` begins silently losing
real content inside a month. Any plan must sequence this first. This is a *separate and harder*
problem than `AGENTS.md`: here overflow is **silent** and causes real memory loss.
It must be addressed in the plan, not folded into the `AGENTS.md` discussion.

---

## 3. `@path` imports are a trap — they save zero tokens

Stated three times in official docs, in language written to pre-empt exactly this
assumption:

> "Imported files are expanded and loaded into context at launch alongside the
> CLAUDE.md that references them."

> "You can also split content into imports for organization, **though imported
> files still load and enter the context window at launch**."

> "Splitting into `@path` imports helps organization but **doesn't reduce context,
> since imported files load at launch**."
> — all T1, `/docs/en/memory`

- Depth: 4 hops, recursive.
- Relative paths resolve against the *containing file*, not the CWD.
- Imports inside code spans / fenced blocks are **not** evaluated (backtick a path
  to mention it without importing).
- A project-level import resolving outside the working directory triggers a
  one-time approval dialog; declining disables those imports permanently and
  silently. User-scope imports load without a dialog.

**Any proposal whose token savings come from `@`-imports is void.** Imports are a
maintainability tool (smaller files, clearer ownership, per-file git history) with
zero context benefit.

---

## 4. The mechanisms that actually defer loading

### 4a. Skills — lazy body, resident description

> "Unlike CLAUDE.md content, a skill's body loads only when it's used, so long
> reference material costs almost nothing until you need it." — T1, `/docs/en/skills`

> "Create a skill when you keep pasting the same instructions, checklist, or
> multi-step procedure into chat, **or when a section of CLAUDE.md has grown into
> a procedure rather than a fact**."

- In context before invocation: **name + description only** (plus `when_to_use`).
- Guidance: keep `SKILL.md` **under 500 lines**; move detail to separate files.
- **Recurring-cost trap:** once invoked, the body "stays there for the rest of the
  session". Post-compaction re-attach is capped at **5,000 tokens per skill /
  25,000 total**, oldest dropped; truncation keeps the *start* of the file, so put
  the highest-value instructions first.
- **Listing-budget trap — load-bearing for a 9-repo ecosystem:** the listing
  always contains every skill name, but descriptions are shortened to fit a budget
  of **1% of the context window**, dropping descriptions for least-invoked skills
  first. Per-entry cap **1,536 chars** (`skillListingMaxDescChars`); budget
  tunable via `skillListingBudgetFraction` / `SLASH_COMMAND_TOOL_CHAR_BUDGET`.
  A proposal that creates many skills can starve its own discovery.

### 4b. `.claude/rules/` with `paths:` frontmatter — lazy, path-scoped

- Rules **without** `paths:` load at launch (no saving).
- Rules **with** `paths:` trigger "when Claude reads files matching the pattern,
  not on every tool use."
- Budget: 1,000 expanded patterns / 4 MiB per rule's `paths` list.

### 4c. Per-subdirectory `CLAUDE.md` — the eager/lazy asymmetry

> "CLAUDE.md and CLAUDE.local.md files in the directory hierarchy **above** the
> working directory are loaded in full at launch. Files in **subdirectories load
> on demand** when Claude reads files in those directories." — T1

**Ancestors are eager; descendants are lazy.** Content pushed *down* the tree
becomes lazy; content sitting *above* the launch directory is always paid for.

### 4c-bis. What survives compaction — the central design tension

*(Added 2026-08-18 after Proposal B correctly reported that this fact was asserted
in its brief but missing from this document. Both research agents reported it from
T1 `/docs/en/context-window`; the omission was in this fact base, not in the
sources. Proposals A, C and D were drafted without it and must be checked against
it during validation.)*

| Mechanism | After compaction |
|-----------|------------------|
| Project-root `CLAUDE.md` and unscoped rules | **Re-injected from disk** |
| Auto memory | **Re-injected from disk** |
| Rules with `paths:` frontmatter | **Lost until a matching file is read again** |
| Nested `CLAUDE.md` in subdirectories | **Lost until a file in that subdirectory is read again** |
| Invoked skill bodies | Re-injected, capped 5,000 tok/skill, 25,000 total; oldest dropped first |

> "If a rule must persist across compaction, drop the `paths:` frontmatter or move
> it to the project-root CLAUDE.md." — T1

**This is the real design axis, and it is sharper than file size.** *The
mechanisms that save context are exactly the ones that do not survive
compaction.* Anything that must hold for the whole of a long session belongs in
the root file; anything episodic belongs in a lazy mechanism.

It bites hardest here because this project's standing policy is **thread handoff
instead of compaction** — but handoff is a *convention the agent must choose to
follow*, and §6 establishes that memory content is advisory with no compliance
guarantee. A session that compacts anyway silently loses every path-scoped rule
and nested file until re-triggered. Any proposal moving safety-critical content
into a lazy mechanism must say what happens in that window.

### 4d. Free wins

- **Block-level HTML comments are stripped before injection** — maintainer notes
  cost nothing.
- **`claudeMdExcludes`** (glob/path, merges across settings layers) suppresses
  specific ancestor files — the documented answer to an over-broad parent file.
- **`/doctor`** ships a purpose-built CLAUDE.md trim proposer, requires v2.1.206+;
  we run **2.1.235**. It "cuts content Claude can derive from the codebase, such
  as directory layouts, dependency lists, and architecture overviews, and keeps
  pitfalls, rationale, and conventions that differ from tool defaults."

---

## 5. Official authoring guidance

> "Keep it concise. For each line, ask: *'Would removing this cause Claude to make
> mistakes?'* If not, cut it. **Bloated CLAUDE.md files cause Claude to ignore your
> actual instructions!**" — T1, `/docs/en/best-practices`

> "**The over-specified CLAUDE.md.** If your CLAUDE.md is too long, Claude ignores
> half of it because important rules get lost in the noise. **Fix**: Ruthlessly
> prune."

> "Keep it to facts Claude should hold in every session: build commands,
> conventions, project layout, 'always do X' rules. If an entry is a multi-step
> procedure or only matters for one part of the codebase, move it to a skill or a
> path-scoped rule instead." — T1, `/docs/en/memory`

Target: **under 200 lines per CLAUDE.md.** Ours is 1,115 lines.

The official EXCLUDE list names several things that make up the bulk of our file:
*detailed API documentation (link instead)*, *information that changes
frequently*, *long explanations*, **file-by-file descriptions of the codebase**,
*anything Claude can figure out by reading code*.

---

## 6. Why this still matters even though nothing truncates

> "LLMs have an 'attention budget'… Every new token introduced depletes this
> budget by some amount."
> "…**context rot**: as the number of tokens in the context window increases, the
> model's ability to accurately recall information from that context decreases."
> — T2, *Effective context engineering for AI agents*

Our ~51k tokens of always-on memory is roughly **28× the illustrative
project-CLAUDE.md figure** in the official context-window doc (1,800 tokens) and
consumes about **25% of a 200k context window before the first prompt**.

**Enforcement caveat that constrains every proposal:**

> "CLAUDE.md content is delivered as a user message after the system prompt, not
> as part of the system prompt itself… there's no guarantee of strict compliance."
> "To block an action regardless of what Claude decides, use a PreToolUse hook
> instead." — T1

So the 164 `MUST` / `MANDATORY` / `NEVER` lines in our `AGENTS.md` are **advisory
context competing for attention, not enforcement.** Rules that must hold
deterministically belong in hooks or CI gates.

---

## 7. `AGENTS.md` standard vs Claude Code — a real conflict

- The standard (T3) specifies **nearest-file-wins**: "the closest one takes
  precedence". It gives **no** size guidance and **no** import convention.
- Claude Code does **not** implement that:

> "All discovered files are **concatenated** into context rather than overriding
> each other." — T1

**Our parent `Juniper/CLAUDE.md` (11,016 chars) is fully additive**, not
superseded by the repo file. Any design assuming override semantics will silently
double-load.

Claude Code reads `CLAUDE.md`, not `AGENTS.md`; our symlink is the officially
documented bridge.

---

## 8. Explicitly UNVERIFIED

Carried forward verbatim so no proposal treats these as settled:

1. **Semantics of `Vk(e,jC())`** in the threshold formula. The arithmetic
   `max(40000, round(r × 0.05 × charsPerToken))` is verified as shipped code; that
   `r` is the context-window size is **inferred** from the constants and the exact
   200,000 × 0.05 × 4 = 40,000 coincidence. Not decompiled. If `r` is something
   else, only the "scales with context window" claim weakens — per-file scope and
   no-truncation are unaffected.
2. `jLr` (non-finite fallback) — unresolved.
3. `Rzr(r.path)` — the path-exclusion predicate; almost certainly
   `claudeMdExcludes`, unconfirmed.
4. Version history of the 40,000 floor — verified only in 2.1.235.
5. **No Anthropic documentation page states 40,000 anywhere.** A proposal citing
   it must cite the binary or a GitHub issue, never the docs.
6. **No published Anthropic benchmark** measures instruction-adherence degradation
   as a function of CLAUDE.md size. The adherence claims are documentation
   assertions; the context-rot evidence concerns long contexts generally.
7. Issue #2766's maintainer replies could not be loaded; **no official
   recommendation may be attributed to that thread.**
8. agents.md nesting behaviour in Claude Code was not runtime-tested.

---

## 8b. ADDENDUM — second independent agent, binary forensics

A second agent independently disassembled the same binary and reached the same
constants, then added findings the first did not. **Nothing here contradicts
§1–§8; it strengthens and extends it.** Recorded separately because it landed
after the four proposals were commissioned.

### The binary is readable, and the full file demonstrably loads

The install is a 330,946,864-byte **Bun v1.4.0 single-file executable** with the
JS bundle embedded as **plaintext, uncompressed** — so these are quotations from
shipped code, not guesses.

**In-situ proof of no truncation.** The agent used its own context as the canary:
`AGENTS.md`'s final line begins at byte **170,061** — 4.25× past the 40,000
"limit" — and was present verbatim in its system prompt. To rule out head+tail
elision it sampled six interior offsets (40,000 / 60,000 / 90,000 / 120,000 /
150,000 / 168,000), all present verbatim. **A 170 KB memory file loads whole.**

The assembler does no slicing, and the loader computes the aggregate for
telemetry only, then ignores it:

```js
r.push(`Contents of ${i.path}${s}:\n${i.content.trim()}`)   // full content
let b=s.reduce((S,A)=>S+A.content.length,0);
Ir("info","memory_files_completed",{...,total_content_length:b});
```

**There is no aggregate memory budget anywhere in the load path.** Only per-file
warnings exist.

### The one genuine hard limit is 4 MiB — and it SKIPS the file entirely

```js
if(n.totalBytes>Nci)return{kind:"skipped",isDirectory:!1};   // Nci = 4194304
E(`[CLAUDE.md] skipping ${e}: not a regular file or exceeds ${Nci} byte limit`)
```

A memory file over 4 MiB is **dropped whole, not truncated**. We are at 4% of
that, so it is not a near-term risk — but it is the actual cliff, and it fails
closed in the most destructive possible way. Worth a guardrail purely because the
failure is total and silent in normal use.

### Truncation exists in exactly one place, and it is auto-memory

```js
if(r==="AutoMem")d=NOr(c).content;      // <- ONLY AutoMem
```
`NOr` caps at `Tte=200` lines / `qpe=25000` bytes. User / Project / Local /
Managed content is passed through untouched. **This confirms §2 from the
implementation side**, and corrects the byte figure: the cap is **25,000 bytes**,
not 25,600.

| Measure | Value | Limit | Consumed |
|---------|-------|-------|----------|
| Lines | 139 | 200 | **70%** |
| Bytes | 20,388 | 25,000 | **82%** |

### Auto-memory is proven LAZY at runtime — the architecture already works here

Measured on this host, 2026-08-18:

| | Value |
|---|---|
| Auto-memory topic files on disk | **154** |
| Total bytes on disk | **1,082,901** |
| Bytes actually loaded (the `MEMORY.md` index) | **20,388** |
| **Reduction** | **≈53 : 1** |

The agent dumped a topic file in full and confirmed its ~1,500-char body is
**absent** from context, which carries only its one-line index entry.

**This is the single most important finding for the design.** The pattern the
proposals are reaching for — *a small always-loaded index pointing at a large
on-demand corpus* — is not speculative. It is already running in this project,
next to the problem file, at 53:1, and it is the mechanism that keeps 1 MB of
accumulated project knowledge available at a cost of 20 KB.

### `.claude/rules/` conditional loading is code-proven

`KSv` parses frontmatter `paths:` into globs. The session-start loader calls
`iir({…conditionalRule:false})`, which keeps only files **without** globs. A
separate path `Bci(filePath, rulesDir, …)` calls `iir({…conditionalRule:true})`
and returns only rules whose globs match the file being touched. Code-proven;
runtime behaviour not observed.

### Imports: eager, confirmed from the recursion itself

```js
async function wke(e,t,r,n,o=0,i,s){
  let a=qT(e); if(r.has(a)||o>=iEv)return[];        // iEv = 5, root at o=0
  let{info:d,includePaths:p}=await GIa(e,t,c,s);    // READ NOW
  let f=[]; f.push(d);
  for(let m of p){ let g=await wke(m,t,r,n,o+1,e);  // RECURSE NOW
                   f.push(...g); }
  return f;}
```

Every import is read and flattened into one array of full-content records at
session start. Cycle-guarded; depth root + 4.

### Two new findings with direct local consequences

1. **`.claude/agents/` has its own budget.** `EXl=15000` drives a separate
   `large-agent-descriptions` warning. This repo ships **six** custom agents —
   a proposal that adds more agents or skills must budget against this too, not
   just against the memory files.
2. **Settings differ between the main checkout and a worktree.**
   *(Corrected 2026-08-18 by the grounding validator; the original claim here —
   "this repo has no active settings" — was measured in the **worktree** and
   wrongly generalised to the repo.)* Verified:

   | Location | File | Read by Claude Code? |
   |----------|------|----------------------|
   | Main checkout | `.claude/settings.local.json` (1,801 B, Jun 9) | **yes** |
   | Worktree | `settings.local-ORIG_{1..5}.json`, `settings.local-WORKING.json` | **no** |
   | Either | `.claude/settings.json` | absent |

   `settings.local.json` **is** a filename Claude Code reads (91 references in the
   2.1.235 binary). It is gitignored at `.gitignore:167`, so it does **not**
   travel into a fresh worktree — meaning **sessions run in worktrees operate
   without the local settings that main-checkout sessions get.** Given that this
   project does nearly all its work in worktrees, that asymmetry is worth
   resolving on its own merits; it also means any settings-based remedy
   (`claudeMdExcludes`, hook configuration) must be placed somewhere that reaches
   worktrees, not in the gitignored local file.

   Proposal C built a conclusion on the original wrong claim ("nowhere for a hook
   to be configured") and must be re-read with this correction.

### Other surfaces

- `/context` renders a **`Memory files`** token row plus a per-file tree; a
  `/doctor` advisory reads *"Memory files using N tokens (X%) — Largest: … Use
  /memory to review and prune stale entries"* and estimates savings at ~30%.
- No CLI subcommand reports context accounting; it is TUI-only.
- `--bare` skips auto-memory and CLAUDE.md discovery entirely.
  `CLAUDE_CODE_DISABLE_CLAUDE_MDS` and
  `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` exist.
- `claudeMdExcludes` is documented as matching **absolute paths via picomatch**,
  and applies only to User / Project / Local types.
- Two distinct warning strings were found by the two agents
  (`Large … will impact performance (N chars > T)` and `… is over the T-char
  limit (N chars) · /memory to free up context`), suggesting two surfaces. Not
  material to any design decision.

### 8c-RESOLVED. Worktree ancestor behaviour — TESTED 2026-08-19: it is content dedup

**The hypothesis below was resolved empirically. H-a (content dedup) is
CONFIRMED; H-b (worktree-aware root detection) is REFUTED.** The original
statement of the question is retained afterwards for provenance.

Probe: `util/ad-hoc/2026-08-19_build_ancestor_canary_probe.bash` builds a
synthetic repo whose root and `.claude/worktrees/wt/` carry **deliberately
different** plain-text canaries (never an HTML comment — those are stripped
before injection, §4d, which would give a false H-b).

| Probe | cwd | Result |
|-------|-----|--------|
| **A — positive control** | `repo/plain_sub/` | `CANARY_ANCESTOR_7Q2X` — ancestor loads, method sound |
| **B — the question** | `repo/.claude/worktrees/wt/` | **`CANARY_ANCESTOR_7Q2X` *and* `CANARY_WORKTREE_7Q2X`** |

Both canaries appear. **When the ancestor and the worktree file differ, BOTH
load.** The complementary branch is evidenced by this very session: the two files
were byte-identical and only three memory files were injected, the ancestor
absent. Identical → deduped; different → both.

#### This is not only a migration hazard. It is happening now.

Measured 2026-08-19 across the 23 live worktrees under
`juniper-ml/.claude/worktrees/`:

| Distinct `AGENTS.md` contents | 11 |
|---|---|
| Worktrees matching the main checkout | **1 of 23** |
| Worktrees that therefore load **both** files | **22 of 23** |

Cost of a session in a divergent worktree (`cached-roaming-hamster`):

| Component | Chars |
|-----------|------:|
| worktree `AGENTS.md` | 139,561 |
| **main-checkout `AGENTS.md` (ancestor, differs → also loads)** | **173,591** |
| `Juniper/CLAUDE.md` | 11,016 |
| `~/.claude/CLAUDE.md` | 3,349 |
| `MEMORY.md` (post-P0) | 16,933 |
| **Total** | **344,450 ≈ 86k tokens ≈ 43% of a 200k window** |

Against ~204,889 chars (~26%) for a session whose files happen to match. **The
measured problem is roughly twice as large as the baseline assumed, for 22 of 23
worktrees**, and the baseline's 204,890 figure describes only the deduped case.

#### Consequences for the plan

1. **P3 ordering is now determined.** A trimmed worktree against an untrimmed
   main checkout is the *worst* configuration: 32K + 173K ≈ 205K, i.e. trimming
   would make context go **up**. The cut must land on `main` and the primary
   checkout must be pulled, before worktrees carry the trimmed file — or the
   trim must be performed such that both converge together.
2. **Worktree hygiene is itself a memory control.** Every stale worktree is a
   permanent second copy of `AGENTS.md` in every session it hosts. Pruning merged
   worktrees, or keeping them rebased, recovers ~170K per session at zero
   authoring cost — plausibly a larger and cheaper win than any content edit.
3. **It compounds with the cut rather than competing.** After the cut, a
   divergent worktree costs 2 × 32K instead of 2 × 173K, so the two remedies
   multiply.

---

### 8c (original statement, retained for provenance). An untested migration hazard

Raised by Proposal B, independently reproduced here. It must be settled **before**
any migration begins, because getting it wrong inverts the result.

The main checkout's `juniper-ml/CLAUDE.md` **is** a filesystem ancestor of
`.claude/worktrees/<name>/`, so §4c predicts it loads eagerly. It does not appear
in this session's injected context, which carries only three memory files:
`~/.claude/CLAUDE.md`, `Juniper/CLAUDE.md`, and the worktree's own `CLAUDE.md`.

Verified here:

```
$ md5sum AGENTS.md /…/juniper-ml/AGENTS.md
d8f2f6558a4fccfecf4a0fc5f32fa2db  AGENTS.md
d8f2f6558a4fccfecf4a0fc5f32fa2db  /…/juniper-ml/AGENTS.md      # byte-identical
$ readlink -f CLAUDE.md
/…/.claude/worktrees/swirling-kindling-octopus/AGENTS.md        # relative symlink,
                                                                # resolves in-worktree
```

Two hypotheses fit the observation:

1. **Content dedup** — identical content is injected once.
2. **Worktree-aware root detection** — the worktree is treated as the project
   root, so intermediate ancestors are skipped.

**They diverge exactly during migration, and hypothesis 1 fails badly.** If dedup
is the mechanism, then the moment a worktree carries a trimmed `AGENTS.md` while
the main checkout still carries the 170K original, the two stop matching and
**both** load — a session would carry the new slim file *and* the old monolith at
once. Trimming the file would make context go **up**.

**Required before Phase 1 of any migration:** make the two files differ by one
marker line and start a session in a worktree to see whether both appear. Cheap,
decisive, and it gates the ordering of every migration plan (merge-to-main first,
or trim-in-worktree first).

### Still not verified

- Runtime confirmation of eager imports and the depth limit. A probe tree builder
  is committed at
  [`util/ad-hoc/2026-08-18_build_memory_import_probe.bash`](../util/ad-hoc/2026-08-18_build_memory_import_probe.bash);
  the headless run was **aborted** on low API credit, per its cost guardrail. It
  predicts `CANARY_D1..D4` load and `D5`/`D6` do not — re-run to confirm.
- Whether conditional rules re-inject per read, per turn, or once.
- Whether prompt caching makes the 42k-token file cheap on later turns.
- Whether `eR()` returns 4 or 3 for the model actually in use.

---

## 8d. The docs-deletion screen does NOT protect a memory migration

Raised by the adversarial validator, **verified here at source** against the same
`juniper-ci-tools` **0.8.0** that CI pins
(`/opt/miniforge3/envs/JuniperCascor1/lib/python3.13/site-packages/juniper_ci_tools/docs_additions_check.py`).
This overturns a design claim made by two proposals and must be settled before any
migration relies on the screen.

### The deletion-run FAIL is a *pure*-run rule — one added line defeats it

```python
if del_headings:                                   # :193-195  heading deleted -> FAIL
    ...
elif added == 0 and deleted >= min_run:            # :196      FAIL  (default N=5)
    ...
else:
    ... "small-deletion", "WARN"                   # :199      WARN never fails
```

`added == 0` is required for the FAIL. Executed by the validator:

```
del=  5 add=0  ->  deletion-run   FAIL
del= 40 add=1  ->  small-deletion WARN      <- 40 lines destroyed, screen green
```

**"Delete a block, leave a pointer, keep the heading" — the shape all four
proposals prescribe — passes with no waiver trailer at any magnitude.** The
module's own docstring concedes this at `:31`, relying on the heading-deletion
rule as backstop; but relocating **nested sub-bullets under a heading that stays**
deletes no heading at all — and those sub-bullets are precisely the 44,350 chars
of accreted lore (baseline §4) that most needs relocating.

Two consequences:

- **Proposal D's "vise" does not hold.** Its §5.4 argues the budget gate and the
  docs screen are opposed so that *relocation is the only legal move*. Compressing
  prose in place also passes. The vise was among the more elegant ideas in the set;
  it is empirically dead.
- **Proposal C's G2 claim is wrong.** The screen will *not* "fire on every phase
  by design".

### The screen's scope excludes most proposed destinations

```python
def in_docs_scope(path: str) -> bool:                          # :62-66
    if path in ("AGENTS.md", "CLAUDE.md"): return True
    if path.endswith(".md") and (path.startswith("docs/")
                              or path.startswith("notes/")): return True
    return False
```

| Destination | Proposal | Screened? |
|-------------|----------|-----------|
| `docs/REFERENCE.md` | C | **yes** |
| `notes/**/*.md` | C, D | **yes** |
| `.claude/skills/**/SKILL.md` | A | **no** |
| `.claude/rules/*.md` | B | **no** |
| `util/CLAUDE.md`, `tests/CLAUDE.md`, `.github/CLAUDE.md` | B | **no** |

Note `util/CLAUDE.md` is *not* the literal string `CLAUDE.md`, so the first clause
misses it.

**A relocates ~101,000 chars and B ~152,900 chars out of a file under a *required*
screen into files under none.** Proposal B presents this as a benefit ("the screens
get quieter"). It is not quiet; it is silent. Whatever protection the content has
today against a careless future deletion, it loses on arrival.

**This is the sharpest discriminator between the four proposals**, and it favours
destinations inside `docs/` and `notes/` — i.e. C's and D's — over `.claude/` ones.
Any proposal keeping a `.claude/` destination must either extend the screen's scope
(`--scope` is repeatable and already used by `ci.yml` for the symbol screen) or
accept the exposure explicitly.

---

## 9. Bottom line for proposal authors

1. **Nothing is truncated.** The cost is tokens and attention. Optimise for
   tokens, never for silencing the per-file warning.
2. **`@`-imports save nothing.** Reject any design resting on them.
3. **Real levers, in descending documented effect:** Skills (lazy body) →
   `.claude/rules/` with `paths:` (lazy) → per-subdirectory `CLAUDE.md` (lazy) →
   ruthless pruning against the official EXCLUDE list → `claudeMdExcludes` for the
   additive parent → HTML comments for maintainer prose → `/doctor` trim proposer.
4. **Budget the skill listing** (1% of context, least-used descriptions dropped
   first) — a 9-repo rollout can starve its own discovery.
5. **Directives that must hold belong in hooks / CI gates,** not in prose.
6. **`MEMORY.md` is a separate, harder problem** at ~80% of a hard silent-loss
   limit (§2).
