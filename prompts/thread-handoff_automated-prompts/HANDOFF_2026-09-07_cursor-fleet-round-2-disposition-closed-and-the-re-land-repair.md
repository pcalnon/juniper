# HANDOFF — Cursor fleet round 2: disposition CLOSED, and the re-land repair

**Date**: 2026-09-07
**Session**: `b8961afb-ff80-4711-ad14-f0b84fc764cf` (`https://claude.ai/code/session_01XKkhhaqpFhYJ89JFtYU6Q5`)
**Worktree**: `juniper-ml/.claude/worktrees/zippy-dreaming-kay`
**Validation**: five independent agents — results in **§7**. **Nine of my claims were wrong; they are corrected below and the corrections are the most useful thing in this document.**

---

## 1. Goal statement for the next thread

```text
Continue the cursor-fleet round-2 disposition arc for juniper-ml. The BACKLOG IS CLOSED --
0 open `app/cursor` PRs across ALL 17 non-archived repos in the pcalnon org. What remains is
tail work plus TWO UNMERGED PRs of mine (#1814, #1815).

Completed so far:
- 100 cursor PRs closed UNMERGED on juniper-ml since 2026-09-05; two more (#1655, #1627) were
  MERGED rather than closed. Every closure states a reason; 73 of the 100 also name the carrier
  PR by number. The three a tool could not adjudicate (#1664, #1734, #1735) were read by hand
  against main's own stated reasons and closed with them quoted.
- Live defects fixed in juniper-ml and juniper-data, each found by RUNNING a harvested test
  rather than reading its diff. The evidence is in the merged PR bodies; I have not enumerated
  them, so do not quote a count.
- Contract reverts caught by READING, in juniper-data #324/#325, #327, #328 and juniper-ml
  #1735. See "Key context" -- my earlier claim that all would have merged green is FALSE.
- `util/markdown_structure_delta.py` shipped in #1801 and wired into ci.yml's required `docs`
  job, gating the DELTA per touched file.

Remaining work, in priority order:
0. LAND MY TWO OPEN PRs. They are ordered and they collide:
     #1815 fix/gate-vacuity-holes   -- two vacuity holes in the #1801 gate + census roster
     #1814 fix/dedupe-1799-reland   -- removes #1799's duplication (REFERENCE.md +1/-329)
     #1807, #1808, #1810 already MERGED -- do not treat them as open
   #1814 touches docs/REFERENCE.md heavily. Of the OTHER sessions' open PRs, **#1811 edits the
   same file** (measured, not assumed: it is the only other open PR that does). Land #1814
   BEFORE it merges, or rebase onto it -- this is the same collision class that made #1787/#1799
   land duplicate content over #1797. RE-MEASURE that set; it moved twice while I wrote this:
     gh pr list --repo pcalnon/juniper-ml --state open --limit 50 --json number,files \
       --jq '.[] | select(.files[].path == "docs/REFERENCE.md") | .number'
1. Decide whether to reduce main's 102 markdown structure problems across 21 files, or ratify
   them. The gate stops growth only. By directory: 11 files / 62 problems in `notes/`, 6 / 20 in
   `notes/legacy/`, 3 / 19 in `prompts/`, 1 / 1 in `notes/code-review/`, ZERO in `docs/`.
   OWNER DECISION, not a defect to fix unasked.
2. That 102/21 is a count over 1012 of 1022 tracked `.md` paths. `2026-09-05_markdown_structure_
   check.py:125` has `if not p.is_file(): continue`, and `is_file()` FOLLOWS SYMLINKS -- ten
   dangling links (nine in `notes/legacy/` pointing at a `regressions/` dir absent from main,
   one under `notes/development/`) read as "not a file" and score clean. #1815 fixes the same
   class in the sibling `markdown_structure_delta.py`; PORT IT rather than re-deriving it.
3. Resolve the `0.6.27` version collision in `docs/REFERENCE.md`'s version history -- two
   different changes claim it. Left as #1799 shipped rather than invented over.
4. Finish the `or {}` type-guard sweep if wanted. THREE production files remain, not one:
   `util/snapshot_index.py` (4 unguarded chains), `util/experiments/run_experiment.py` (1),
   `util/snapshot_classify.py` (1). Re-measure:
   `python3 util/ad-hoc/2026-09-06_untyped_json_read_census.py util tests`

Key context:
- A DUPLICATED SECTION IS INVISIBLE TO THE GATE I SHIPPED. #1801's gate checks fences, swallowed
  headings and separator-less tables -- a document's SHAPE. #1799 duplicated five whole sections
  and `docs/REFERENCE.md` scored 0 structural problems throughout. That is a limitation of my
  gate, not a law of nature. `2026-09-07_duplicate_section_census.py` (on #1814 only) is the
  instrument for the other question.
- "ALL FOUR CONTRACT REVERTS WOULD HAVE GONE GREEN" IS FALSE -- I said it repeatedly and it does
  not survive measurement. Only juniper-data #327 was fully green. #324, #325 and juniper-ml
  #1735 each failed the REQUIRED `Guard PR base branch`; #328 failed `Sequence Safety`. What IS
  true, and is the real finding: the revert was invisible to every check that RAN, and on a
  stacked PR almost nothing runs -- #1735's entire check set was ONE context, the base-branch
  guard. A stacked PR is governed by no ruleset (both are `~DEFAULT_BRANCH`-scoped), so its
  test suite never executes. Reading was the only thing that could have caught these.
- VERIFY A REPAIR AS A LOSS CHECK, NOT A STEP CHECK. Two removals that were each correct combined
  to lose a version-history row; only "what does the BRANCH have that the RESULT lacks" found it.
- The dup-guard for concurrent sessions must key on the SET OF PR NUMBERS an open PR body claims.
  Branch name and subject line both differ between two sessions consolidating the same cohort --
  that is how #1787 and #1799 collided with #1797 twice in one day.
```

---

## 2. State at handoff

| | |
| --- | --- |
| open `app/cursor` PRs, all 17 org repos | **0** |
| my PRs still open | **#1814, #1815** — both armed, both BEHIND/BLOCKED at write time |
| cursor PRs closed UNMERGED since 2026-09-05 | 100 (+2 merged: #1655, #1627) |
| PRs merged in juniper-ml since 2026-09-05 | **81 and rising** — a live repo with concurrent sessions; run the query, do not quote this |
| this handoff | committed on branch `docs/handoff-fleet-round-2` |

**Other sessions' open PRs at 15:00Z — #1809, #1811, #1812, #1813, #1816, #1817.** Do not take
them over. **#1811 is the only one that edits `docs/REFERENCE.md`**, so it is the only one that
collides with #1814.

**That set is the most perishable thing in this document, and it moved twice while I wrote it.**
An early draft listed #1807 and #1810 as open; both had merged. A later draft named #1808 as a
REFERENCE.md collision; it merged at 14:39Z, and #1816/#1817 opened. Every number in this
section is a timestamp, not a fact — **run the query in §1 item 0 before acting on it.**

### Verification commands

Run from `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/zippy-dreaming-kay`.
**No `| tail -N`** — a pipe discards the exit code, and these are gates whose exit code is the answer.

```bash
git fetch origin main && git log origin/main --oneline -3
gh pr list --repo pcalnon/juniper-ml --state open --json number,title,mergeStateStatus

# Backlog. Lives on branch fix/gate-vacuity-holes (#1815) -- NOT on main until that lands.
python3 util/ad-hoc/2026-09-07_fleet_backlog_census.py; echo "exit=$?"
#   exit 0 = every repo answered and the total is zero
#   exit 2 = a repo was UNREADABLE. That is not a zero.

# main's structure debt (the item 1 decision)
find . -name '*.md' -not -path './.git/*' -print0 \
  | xargs -0 python3 util/ad-hoc/2026-09-05_markdown_structure_check.py; echo "exit=$?"

# The duplication question the structure gate cannot answer.
# Lives on branch fix/dedupe-1799-reland (#1814) ONLY.
python3 util/ad-hoc/2026-09-07_duplicate_section_census.py docs/REFERENCE.md; echo "exit=$?"
```

---

## 3. Tools this arc built

**Read the tool's docstring before using it** — each records the defect that motivated it.
`main?` says whether it is on `origin/main` yet — **4 of these 15 are not, so a command copied
from here fails from `main` until #1814 and #1815 land.** **`writes?` says whether it MUTATES
FILES OR GITHUB STATE** — **6 of the 15 are not queries**, and one of those closes PRs.

| tool (under `util/ad-hoc/` unless marked) | main? | writes? | question |
| --- | --- | --- | --- |
| `2026-09-06_superseded_method_presence.py` | yes | no | is every test METHOD this PR adds present on main? |
| `2026-09-06_harvest_methods.py` | yes | **yes** — rewrites the target test file | take named methods, class- and dependency-aware |
| `2026-09-06_mutation_check_harvest.py` | yes | no (temp copies) | break each guard; does the harvested test notice? |
| `2026-09-06_docs_pr_cluster_map.py` | yes | no | who touches what, from how many distinct bases? |
| `2026-09-06_docs_merge_probe.py` | yes | no (aborts each merge) | how much of a docs fleet merges clean? (0 of 35) |
| `2026-09-06_docs_conflict_resolve.py` | yes | **yes** — resolves in place | resolve a docs conflict by ITEM identity |
| `2026-09-06_docs_consolidate.py` | yes | **yes** — merges and commits | drive the per-PR merge, resumable, gated per step |
| `2026-09-06_docs_residue_audit.py` | yes | no | of the lines held back, which LANDED / NEAR / ABSENT? |
| `2026-09-06_close_superseded_fleet.py` | yes | **yes — CLOSES PRs.** Dry-run unless `argv[1] == "--apply"`, parsed POSITIONALLY, no argparse | close a carrier's group, refusing what it cannot verify |
| `2026-09-06_untyped_json_read_census.py` | yes | no | `.get` chains over JSON another process wrote |
| `2026-09-07_duplicate_section_census.py` | **#1814 only** | no | which headings/rows appear more than once? |
| `2026-09-07_dedupe_relanded_sections.py` | **#1814 only** | **yes** — `--apply` | remove a re-landed duplicate `##` section |
| `2026-09-07_dedupe_relanded_rows.py` | **#1814 only** | **yes** — `--apply` | remove rows duplicated vs a BASELINE ref |
| `2026-09-07_fleet_backlog_census.py` | **#1815 only** | no | open cursor PRs, org-enumerated, ERROR ≠ zero |
| **`util/markdown_structure_delta.py`** | yes (#1815 fixes it) | no | **the CI gate: did this PR make structure worse?** |

---

## 4. Traps this arc paid for

1. **Keying a merge by identity is half the fix; PLACEMENT is the other half.** Appending a new
   row after ours' whole block drops it past the end of its table and starts a separator-less
   one. `origin/main` scored 0 structural problems; my first identity-keyed consolidation scored
   28. A new item must splice beside ours' last item of the SAME KIND, where a row's kind
   includes its table's header signature.
2. **A fence pair removed entirely is invisible to a balance check.** Balance stays intact; the
   commands become prose. My structure screen cannot see it — only a content comparison can.
3. **FENCE-BLINDNESS, five times, mostly in MY OWN tools.** A `# comment` inside a ```bash block
   reads as an H1 to anything scanning for a leading `#`; a `| ... |` line inside indented code
   reads as a table row. Every markdown scan must track fences FIRST.
4. **A presence MISS is usually main's CORRECTED name.** #1734, #1664 and #1735 each had an
   "absent" method that main carries inverted or renamed on evidence, with the reason in the
   test's own docstring. A tool may HOLD on a MISS; it must never CLOSE on one.
5. **`or {}` guards FALSY, not TYPE.** A truthy non-dict sails through to the next `.get`.
6. **A count is not a regression; a DELTA is.** Applied three times, and I still shipped a gate
   that demanded a delta while its own vacuity guard demanded a total (see 7).
7. **My own repair tooling had four defects**, and independent review found two of them after I
   had declared the work done: the census total was accumulated inside a display-capped loop
   (reported 149 where the truth was 397); `0 -> 1` was treated as an excess, which I fixed in
   one tool and then RE-INTRODUCED in its sibling by writing the predicate from memory; the gate
   skipped an unreadable file without counting it, so its fail-closed fired only when EVERY file
   was unreadable; and `base == head` passed vacuously. #1815 fixes the last two.
8. **`update-branch` creates a merge commit on the REMOTE.** A later local push is then
   non-fast-forward, and `--force-with-lease` would "succeed" with a stale lease. Merge it.
9. **BLOCKED with zero failing and zero pending checks = an unresolved CodeQL thread.** Twice.
10. **pre-commit fixes land in the WORKING TREE, not the index.** Re-`git add` after any hook
    that modifies files.
11. **Do not switch branches in a worktree while a subagent is measuring in it.** I did; the
    agent detected the switch via reflog and re-ran from refs with `git archive`. Its numbers
    survived because it noticed — not because I was careful.
12. **A gate piped into `tail` reports success no matter what it found** — the pipeline's exit
    code is `tail`'s. I wrote this warning into §2 of this very document and then, three commits
    later, ran `python3 util/wait_for_checks.py --pr 1819 ... | tail -5`. The tool hit a refused
    connection and correctly returned **3**; the shell reported **0**, and the only reason I did
    not read that as "checks are green" is that the error text happened to be inside the five
    lines `tail` kept. **Knowing a trap does not protect you from it — the invocation has to
    change.** Applies to every gate here: the structure checker, the census, `wait_for_checks`.

---

## 5. Decisions made — do not re-litigate

- **`## Perf-Lane Split Comparator` stays in `docs/REFERENCE.md`**, corrected rather than deleted.
  **Corrected count**: three other documents carry four links to `#perf-lane-split-comparator`
  (`QUICK_START.md` ×1, `DOCUMENTATION_OVERVIEW.md` ×1, `DEVELOPER_CHEATSHEET` ×2);
  `REFERENCE.md` self-links five more times. My earlier "eight documents" was occurrences
  relabelled as documents. **This decision is recorded ONLY here** — #1797's body argues a
  different reason — so a successor may reasonably reopen it. Note `origin/main` still carries
  the section TWICE until #1814 lands.
- **The structure gate gates the DELTA, not the count.** A zero-demanding gate could not ship
  against main's 102 inherited problems. Recorded durably in #1801's merged body.
- **Of the 2841 lines the 35 docs PRs added, 173 are ABSENT from the merged tree.** That is a
  MEASURED OUTCOME, not a decision — and
  `notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md` §2 says the
  count "errs toward over-reporting loss". Its §3 adjudicates the four largest contributors,
  which is about half; the remaining ~86 lines were listed, not adjudicated.
- **#1799's `0.6.27` version collision is left as shipped.** Recorded in #1814's body.

---

## 6. Documents this handoff references or changes

**References**: `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`,
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`,
`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md`.

**Changed**: this file only —
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_cursor-fleet-round-2-disposition-closed-and-the-re-land-repair.md`.

---

## 7. Independent validation — what it changed

Run per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
Sized at the top cell: document of record, containing universal quantifiers, and **convenient** —
it reports that its author's arc succeeded. **3 Lane A** (PR history / repo tree / re-run the
instruments) **+ 2 Lane B** (omission; false authority).

### Lane A — measurement re-creation

| my claim | measured | why I was wrong |
| --- | --- | --- |
| 102 cursor PRs closed | **100 closed + 2 merged** | `gh pr list --state closed` INCLUDES merged PRs |
| "every closure carries its evidence" | **73 of 100** name a carrier | 27 give a reason without a number |
| 0 across **eight** repos | **0 across all 17 org repos** | my eight came from a table omitting `juniper-recurrence` |
| main: 102 problems / 21 files | true, but **over 1012 of 1022 paths** | `is_file()` follows symlinks; 10 dangling links score clean |

Lane A also read the #1801 gate's code and found **two vacuity holes** the eleven existing tests
pass with open. Both fixed in #1815, with mutation-checked tests.

### Lane B — adversarial review

| finding | disposition |
| --- | --- |
| **"All four contract reverts would have gone green" is FALSE** | **ACCEPTED.** Only #327 was green; #324/#325/#1735 failed the required base-branch guard, #328 failed Sequence Safety. Corrected in §1. |
| "Eight documents link the anchor" is a 2.7× inflation | **ACCEPTED.** 4 external links / 3 documents. Corrected in §5. |
| "Twelve live defects" is unverifiable — the number appears nowhere but this file | **ACCEPTED.** Count removed. |
| `fix/gate-vacuity-holes` pushed with NO PR and absent from the handoff | **ACCEPTED.** Now #1815, listed as item 0. |
| Verification commands fail from main; three tools exist only on #1814 | **ACCEPTED.** §2 and §3 now say which branch each lives on. |
| `\| tail -N` discards the exit code | **ACCEPTED.** Removed; `echo "exit=$?"` added. |
| #1807/#1810 were MERGED, not open; #1808/#1811 collide with #1814 | **ACCEPTED**, and it kept moving — #1808 merged during the revision, #1816/#1817 opened. §2 now carries a re-measure query instead of a list to trust. |
| "only production file left" — there are three | **ACCEPTED.** Corrected in §1 item 4. |
| "79 PRs merged since 2026-09-05" | **ACCEPTED.** **81** — 78 pcalnon + 2 cursor + 1 app/github-actions. §2 now says "and rising" and tells you to run the query. |
| §3 did not mark which tools MUTATE state | **ACCEPTED.** `writes?` column added. |
| 173 lines framed as "deliberately not merged" | **ACCEPTED.** Reframed as a measured outcome with the over-report caveat. |
| Failures softened; the gate's limitation written as a law of nature | **ACCEPTED.** §1 and §4 now attribute them to me. |
| the draft promised a §8 that did not exist | **ACCEPTED.** §7 (this section) is it. The header's pointer to "§8" outlived the fix by two commits — a dangling cross-reference survives every edit that does not happen to read that line. |

**Nine distinct claims of mine were wrong** — and because this document's whole argument is that
asserted counts should be auditable, here is that one: **four** in Lane A's table above, plus
**five** in Lane B's (the contract reverts, the anchor count, the twelve defects, the
production-file count, the merged count). The #1807/#1810 row is perishable state that went
stale, not a claim I got wrong, so it is counted separately — see §2.

The most serious is the contract-revert one, because I repeated it to the operator several times
before it was measured. Both Lane B agents were prompted to refute rather than to check; had they
been asked to verify, the sizing table's own warning is that they would have agreed.
