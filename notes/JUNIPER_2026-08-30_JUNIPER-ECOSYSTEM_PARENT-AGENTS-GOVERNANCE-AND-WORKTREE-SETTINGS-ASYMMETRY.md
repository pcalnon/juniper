# Parent `AGENTS.md` governance, and the worktree settings asymmetry

**Project**: Juniper (ecosystem)
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**Status**: Analysis — owner decisions required, nothing implemented
**Created**: 2026-08-30
**Arc**: shared-session-memory ([plan](JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md) §5 rows 8 and 9; tracker [ml#1326](https://github.com/pcalnon/juniper-ml/issues/1326))

---

## 0. Why this document exists

Plan §5 rows 8 and 9 both read **"Yes, separately"**, and neither had a recorded owner
decision. On 2026-08-29/30 the owner decided **both** should be addressed. This note
establishes what each actually is, measured rather than recalled, and states the decisions
that must be made before either can be implemented.

**Nothing here has been implemented.** Both changes are security- or policy-relevant in ways
that make silent execution the wrong call.

---

## 1. Item 8 — the parent `Juniper/AGENTS.md`

### 1.1 What was measured

| Property | Value | How |
|---|---|---|
| Path | `/home/pcalnon/Development/python/Juniper/AGENTS.md` | — |
| Size | **11,016 bytes / 220 lines** | `wc -c -l` |
| Last modified | **2026-05-18 19:50** | `ls -la` |
| `CLAUDE.md` | symlink → `AGENTS.md` | `ls -la` |
| Under version control | **No** | see §1.2 |
| Governed by a ceiling | **No** | absent from every `conf/memory_budget.json` |
| CI-gated | **No** | no repo, therefore no workflow |

The 11,016-byte figure **independently reproduces** the plan's own §5 row 8 figure
("11,016 additive bytes × 9 repos"), measured 12 days apart. The file has not changed since
May 18, which is consistent, and is itself a finding: the ecosystem's most broadly-loaded
context file has been untouched for over three months while the fleet churned constantly.

### 1.2 Instrument adequacy — could this have said otherwise?

Required by the [consensus procedure](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) §2.
"Not a git repo" is a negative claim, and a naive `ls -d .git` would miss three real cases.
All three were checked:

- **a git *worktree*** — its `.git` is a *file*, not a directory. `ls -a | grep '^\.git'`
  returned **no `.git*` entry of any kind**, so not this.
- **an enclosing repo higher up** — `/home/pcalnon/Development/python/.git`,
  `/home/pcalnon/Development/.git` and `/home/pcalnon/.git` all absent.
- **a non-standard `GIT_DIR`** — would still leave the directory inside no working tree.

The instrument could have produced a different answer and did not. The file is genuinely
unversioned.

### 1.3 The consequence, stated at the right scale

**This subsection previously overstated the case in three ways. All three were caught by
adversarial review and are corrected here; the original framing is recorded so the correction
is auditable.**

This file is loaded into **every session in every Juniper repo** — it is an ancestor of every
repo's working directory, so the harness collects it on the way up. That makes it
**additive**: its chars are charged against no repo's budget and are present in all of them.
**A session pays this cost once, flat.**

Corrections:

- **Chars, not bytes.** §1.1 measures 11,016 *bytes*. The governance mechanism this note is
  about measures **characters** (`util/memory_budget_check.py` docstring: "Characters, not
  bytes"). The file is **10,818 chars** — 198 fewer, from 100 non-ASCII characters. The
  earlier text reused the byte numeral under a "chars" label. The plan's §5 row 8 figure of
  "11,016 additive bytes" is correct *as bytes*; what this note reproduced was that byte
  figure, then mislabelled it.
- **The ×9 multiplier is a ledger sum, not a cost anyone pays.** An earlier draft multiplied
  the file by the repo count to get "~99,144 chars of aggregate resident exposure" and
  compared that against the ~74,018 chars the P5 cut removed. That comparison is rhetorical:
  the multiplied figure rises when a repo is *added*, with no change to the file, and no
  session ever pays it. It also borrows P5's weight — five documents, two days of work —
  for what would be a single edit. **Struck.**
- **The repo count contradicts the artifact.** The parent file's own text says "all **8**
  active repositories" (`AGENTS.md:121`) and its overview table lists 8. It mentions
  `recurrence` **zero times**, though recurrence is a real repo that inherits the file as an
  ancestor. Nine is probably the right count for *inheritance*; eight is what the file claims
  for itself. The discrepancy is unreconciled and is itself a currency finding.

What survives all three corrections: **10,818 chars, resident in every session across the
ecosystem, charged to no budget, and unreviewed since 2026-05-18.** That is the real
observation and it does not need inflating.

### 1.4 The blocker, and the trap that looks like a fix

**A CI-enforced ceiling on this file is not achievable as things stand**, because CI runs on a
GitHub runner where `/home/pcalnon/Development/python/Juniper/AGENTS.md` does not exist. It is
not in the repo being checked out; it is not in any repo at all.

#### The trap this note originally claimed — and why that claim was wrong

An earlier version of this subsection asserted that adding the parent file to
`conf/memory_budget.json` would make the `Memory Budget` check "report OK for a file it never
read, on every PR, forever" — the vacuous-pass class. **That is false, and adversarial review
caught it by opening the code this note had merely named.**

`util/memory_budget_check.py:213-216`:

```python
target = repo_root / rel
if not target.is_file():
    # A governed file that vanished is the loudest possible signal, not a skip.
    raise BudgetError(f"governed file missing: {rel}")
```

`BudgetError` is caught in `main()` at `:296-298` and returns 2, **before** `--advisory` is
consulted — so it cannot be softened. There is a negative control proving it:
`tests/test_memory_budget_check.py:183-188`, `test_missing_governed_file_is_a_hard_failure`.
The module docstring names this exact scenario under a "Vacuous-pass resistance" heading.

**The actual consequence** of adding the parent path is the opposite of a silent pass: the
required `Memory Budget` check would hard-fail with `::error::` on **every PR to juniper-ml,
forever**, because the path cannot resolve on a hosted runner. That is loud and
self-correcting — it would be reverted on the first PR that hit it.

It remains a bad idea, but for a different and weaker reason than originally given: the
danger is not the gate, it is **the patch someone writes to silence the gate**. Wrapping that
call in advisory mode or a `try/except` to get merges flowing is where a real vacuous pass
would enter — introduced by the repair, not by the configuration.

**Recording this as a finding about this note, not just a correction:** the false claim was
written *while describing the vacuous-pass class*, about the one tool in the repo explicitly
hardened against it, by reasoning from a generic mental model of "a checker" instead of
opening the named file. That is the "confident wrongness" failure mode in
[the consensus procedure](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) §6,
and it is the reason that procedure requires artifact over prose.

### 1.5 The redundancy measurement, done

An earlier version of this note recommended options while §3 simultaneously said "no option
should be costed without" a redundancy measurement. That was a contradiction inside one
document, and review caught it. **The measurement has now been run**, so the options can be
costed honestly.

Method: every substantive line (>15 chars, stripped) of the parent file, matched **verbatim**
against each repo's own `AGENTS.md`.

| Repo | shared lines | shared chars |
|---|---|---|
| juniper-data-client | 9 | 565 |
| juniper-deploy | 9 | 550 |
| juniper-data / cascor-client / cascor-worker | 8 each | 533 each |
| juniper-ml | 7 | 482 |
| juniper-cascor | 4 | 88 |
| juniper-canopy | 3 | 92 |
| juniper-recurrence | 2 | 47 |
| **UNION (appears in ≥1 repo)** | **12** | **651** |

**651 chars — 6.0% of the file.** The reviewer who prompted this measurement predicted from a
one-repo, one-section sample that true redundancy was "very likely a multiple" of it. It is
not: the *same* dozen worktree-rule lines recur across repos, so the union barely exceeds the
single-repo figure. A lone finding is a lead, not a fact — this one did not survive
re-derivation.

**651 chars is a lower bound** (verbatim matching cannot see paraphrase or a substituted
path). But the direction is clear: **the parent file is ~94% content that exists nowhere
else.** It is not redundant bloat. That weakens the case for cutting it and strengthens the
case that it is genuinely load-bearing shared context.

### 1.6 Options (owner decision)

| | Option | Cost | Real remote gate? |
|---|---|---|---|
| **A** | Put the parent directory under version control (new repo) | New repo, CI, rulesets | **Yes** |
| **B** | Move the file into an existing repo and symlink it out | Inverts the hierarchy; the symlink is itself unversioned | Partly — gates the copy, not what sessions load |
| **C** | Local recurring check (systemd timer or `always_run` hook), loud output | Small | No |
| **D** | Leave ungoverned; re-measure by hand periodically | Smallest | No |
| **E** | Scheduled workflow on a **self-hosted runner** reading the file off local disk | Runner setup + attack surface | **Yes** |

Option E was absent from the first draft and falsifies the earlier categorical claim that a
remote gate "is not achievable". It is achievable; it costs a self-hosted runner.

**No recommendation is offered on size governance, and that is the finding.** Review asked the
question this note could not answer: **who would a CI gate protect against?** There is no PR
path to this file, no second contributor, and no commit history — the repo-level accretion
story (`AGENTS.md` grew ~20x under four gates) *cannot* occur here, because that mechanism
requires many small merges and this file receives none. It has not changed in 3.5 months. The
problem is **nobody looked**, not **somebody attacked**, and branch protection does not solve
nobody-looked.

**What does have a clear answer: the file is unversioned, and that is a durability problem
rather than a governance one.** There is no history, no diff, no blame, and no recovery if it
is corrupted or deleted — for a file that shapes every session in the ecosystem, and which
this session confirmed is 94% unique content. That argument for version control stands on its
own and does not depend on any size figure. It is also the one the backup arc would recognise.

**Independent of all of the above:** the file is 3.5 months stale, has never been reviewed for
currency, and its own text says "all 8 active repositories" while nine repos inherit it. A
currency pass is worthwhile under every option.

---

## 2. Item 9 — the worktree settings asymmetry

### 2.1 What was measured

Primary checkout `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/`:

```
settings.local-ORIG_1.json … ORIG_5.json    (tracked)
settings.local-WORKING.json                 (tracked)
settings.local.json          1801 bytes     (NOT tracked)  <-- the live one
```

This worktree's `.claude/`: **every file above except `settings.local.json`.**

### 2.2 Mechanism

`.gitignore:177` is `.claude/*`. The `agents/`, `skills/`, `settings.local-ORIG_*` and
`settings.local-WORKING.json` entries were force-added at some point and remain tracked, so
they ride into every new worktree. `settings.local.json` never was, so it does not.

Confirmed directly:

```
$ git check-ignore -v .claude/settings.local.json
.gitignore:177:.claude/*        .claude/settings.local.json
```

Five `-ORIG_*` snapshots and a `-WORKING` copy of those settings *are* version-controlled and
do reach every worktree — but nothing reads a file named `settings.local-ORIG_1.json`. An
independent check of the installed Claude Code binary (2.1.251) found **87 occurrences of
`settings.local.json` and zero of `ORIG_` or `WORKING.json`**. The workaround that was reached
for does not work, and its presence makes the directory *look* provisioned — this analysis
initially read it that way.

#### RETRACTED: the consequence originally inferred from that absence

An earlier version of this subsection concluded: *"every worktree session runs without the
permission set that main-checkout sessions get."* **That inference is refuted for the kind of
worktree this repo actually uses.** The file's absence is real and correctly measured; what it
*means* was assumed rather than tested.

Adversarial review ran the test. The Claude Code binary carries an explicit code path for this
exact case:

```
Skipping settings.local.json copy into <dest>: it resolves localSettings to the
canonical repo root, so a copy would become a stale, revocation-resurrecting
legacy overlay
```

The copy is **deliberately skipped** because the worktree already resolves settings to the
canonical repo root. A controlled experiment confirmed the behaviour: in a Claude-Code-native
worktree with no local `settings.local.json`, a mutating command allowed only by the
*primary's* rules **succeeded**; with that rule removed from the primary, the same command in
the same worktree was **denied**. Flipping only the ancestor's rule flipped the outcome.

This worktree is Claude-Code-native, not `git worktree add`: `.git/worktrees/nifty-tinkering-wave/`
carries a `CLAUDE_BASE` file and a `locked` file reading `claude session nifty-tinkering-wave`,
neither of which plain git creates.

**What survives:** the file is absent (measured). **What does not:** that sessions therefore
run unprovisioned (assumed, and false here). This is precisely the failure the
[consensus procedure](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) §1
names — *a correct local reading generalised past the evidence actually examined*.

**Caveat, unresolved:** worktrees created by the *older* documented procedure
(`git worktree add`, per the worktree-setup note) are **not** Claude-Code-native and would
plausibly behave as originally described. The plan's §5 row 9 may therefore have been accurate
when written, for the worktree style then in use. Not tested.

### 2.3 What is actually in the live file

Inspected structurally, without dumping values:

- `permissions.allow` — **41 rules**
- `enableAllProjectMcpServers` — bool
- `enabledMcpjsonServers` — 5 entries

**CORRECTED.** An earlier version of this subsection stated that *"zero of the 41 rules
contain an absolute path, a home directory, or the username — the content is fully portable."*
That is **false**. **9 of the 41 are machine-specific:**

```
/opt/miniforge3/envs/JuniperCanopy/bin/pip
/opt/miniforge3/envs/JuniperPython/bin/{python,ruff,pytest}
~/.cache/pre-commit/repou8f_qfs3/py_env-python3/bin/bandit
~/.cache/pre-commit/repop0hxonq5/py_env-python3/bin/{bandit,python}
Bash(/usr/local/bin/sops:*)
Bash(SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt /usr/local/bin/sops:*)
```

The `~/.cache/pre-commit/repo<hash>/` entries embed pre-commit's content-addressed cache
hashes — they will not match on another machine, or on this one after a cache clear. The
`/opt/miniforge3/envs/` entries hardcode this machine's conda layout.

**Why the original check missed them, stated because the error is instructive:** the filter
tested only for `'pcalnon'` and `'/home/'`. It could not see `~/`, `/opt/`, or `/usr/` — the
three most common machine-specific forms. An instrument for "is this portable?" that cannot
detect the ordinary shapes of non-portability returns a clean result on a dirty input, and the
clean result was believed. Same class as everything else this note catalogues.

### 2.4 The decision this actually is

`permissions.allow` includes a bare **`Bash`** rule — unrestricted, no pattern. Promoting this
file to a tracked `.claude/settings.json` grants that allow-list to **every checkout of the
repo, including CI**.

**The "including CI" clause was challenged as scaremongering and survived**: `.github/workflows/claude.yml:35`
runs `anthropics/claude-code-action@dcb5774…` (v1.0.199) for real, triggered by `@claude`
mentions in issues, PR comments and reviews, with `contents: write`, `pull-requests: write`,
`issues: write`. Anthropic's own action documentation treats the checked-out
`.claude/settings.json` as a live, honored, explicitly risk-flagged surface — and restores
`.claude/`, `.mcp.json` and `CLAUDE.md` from the base branch precisely to stop a PR branch
smuggling in a modified settings file. So a tracked bare `Bash` grant would reach a real,
token-scoped automation, not a hypothetical one.

That is a security-relevant change to who may run what, and it is not the kind of thing to
land quietly inside a memory-budget arc.

### 2.5 The bigger asymmetry, which is not about permissions

§3 of the first draft admitted only `.claude/` settings had been compared. Review checked the
rest, and found two gaps that matter more than the one this section was built around:

| File | Primary | This worktree | Why it matters |
|---|---|---|---|
| `.mcp.json` | 1,154 B | **absent** | `.gitignore:169` comments it *"contains API tokens"*. `settings.local.json`'s `enabledMcpjsonServers` names 5 servers **defined in this file** — so those servers are undefined here regardless of how the settings question is resolved |
| `.env` | 1,024 B | **absent** | Can change script and test behaviour silently, rather than merely prompting |

Both verified by direct `ls`. Two things were checked and **ruled out**, which is worth
recording so nobody re-checks them: the live settings file has **no `hooks` key** (a lost hook
would be strictly worse — silent wrong behaviour rather than a prompt), and `core.hooksPath`
resolves identically in both trees.

The `.mcp.json` gap is the more consequential finding: it is a capability gap involving API
tokens, not a permissions-prompt annoyance.

### 2.6 Options (owner decision)

| | Option | Effect |
|---|---|---|
| **A** | Track a shared `.claude/settings.json` | Grants the allow-list repo-wide **including the live `claude.yml` automation** (§2.4) |
| **B** | Copy from the primary during worktree setup | Local-only; drifts when the primary changes |
| **C** | Symlink to the primary's copy | Always in step; breaks when the primary moves |
| **D** | Split: track only the safe rules | **More work than first described** — ~22% of rules (9 of 41) need filtering on portability alone, before any `Bash`/MCP carve-out |
| **E** | **`.worktreeinclude`** — a shipped Claude Code mechanism listing gitignored paths to copy into every new native worktree | Confirmed present in the 2.1.251 binary (12 references); **no such file exists in this repo**. Could address `.mcp.json` and `.env` in one line each, with no custom scripting |

**No recommendation on the permissions question**, because §2.2's refutation removed its
premise: for native worktrees the permissions already resolve to the canonical root, so
options A–D solve a problem that may not exist here. **The live question is now E**, aimed at
`.mcp.json` and `.env` — files that genuinely are missing and are not resolved upward.

**Before anything is decided**, the cheap confirmation named by review: re-run the canary
against the *real* primary/worktree pair (add a throwaway rule to the primary, test in the
worktree, remove it). One test settles whether §2.2's retraction generalises.

**Regardless of choice:** delete or relocate the five `-ORIG_*` files and `-WORKING`. They are
tracked, they reach every worktree, **the binary contains zero references to them**, and their
presence is actively misleading — this analysis initially read the directory as provisioned
because of them.

---

## 3. What this note does not establish

- **Whether §2.2's retraction generalises.** The refutation was demonstrated on a synthetic
  repo whose worktrees carry byte-identical `CLAUDE_BASE` / `locked` markers to this one, not
  on the real primary/worktree pair — deliberately, since mutating the production
  `settings.local.json` for a causal test would be reckless. One canary run settles it.
- **Whether `git worktree add` worktrees behave the same.** The refutation covers
  Claude-Code-native worktrees. The older documented procedure produces plain git worktrees,
  which a plain-directory control suggests would behave as originally described — so plan §5
  row 9 may have been correct for the worktree style in use when it was written.
- **How much of the parent file is *paraphrased* elsewhere.** §1.5 measures verbatim overlap
  (651 chars, 6.0%) — a lower bound. Near-duplicates with a substituted path are invisible to
  it.
- **Whether any session was ever actually harmed** by any of this. Every impact in this note
  is inferred from structure. No outcome data was found linking either asymmetry to a failed
  session.

## 4. Method, and what review changed

Direct measurement in one session (`nifty-tinkering-wave`, 2026-08-30) using `ls`, `wc`,
`git check-ignore`, `git ls-files`, `strings` on the installed Claude Code binary, and
structural JSON reads. Sample size is 1 per observation — single-valued facts about specific
files, not estimates.

Reviewed under the
[consensus procedure](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md):
**two Lane B agents, one per section, briefed to refute.** One round. It changed the note
substantially, which is the point — a round that changes nothing means the prompt asked for
confirmation.

**What review overturned (all re-derived by the author before acceptance, per §5.2):**

| Original claim | Outcome |
|---|---|
| Adding the parent path to the budget config yields a silent vacuous pass | **FALSE** — the checker hard-errors by design, with a negative-control test |
| Parent file is 11,016 **chars** | **Wrong unit** — 10,818 chars / 11,016 bytes |
| ×9 aggregate exposure justifies the concern | **Struck as rhetorical** — no session pays it |
| Overlap with repo files is unmeasured, so cost it later | **Measured**: 651 chars, 6.0% — and it refuted the *reviewer's* counter-prediction that overlap was large |
| Worktree sessions run without the primary's permissions | **REFUTED by experiment** for native worktrees |
| Zero of the 41 permission rules are machine-specific | **FALSE** — 9 of 41 |
| "Including CI" overstates the risk | **Upheld** — `claude.yml:35` runs the action for real |

**Unresolved dissent, recorded rather than dropped:** one reviewer extrapolated from a
single-repo sample that parent-file redundancy was "very likely a multiple" of it. Direct
measurement across all nine repos contradicts this (the union barely exceeds the single-repo
figure). The reviewer's *instinct* — that the note should have measured before recommending —
was correct; its *estimate* was not.

**The pattern across every overturned row is one thing:** a correct measurement, reused under
a wrong label, or extended to a consequence that was never tested.
