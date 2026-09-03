# HANDOFF 2026-09-03 — round 32: four register rows closed, `arc_agi` found producing nothing, and a recommendation reversed twice by measurement

The standing mandate is unchanged: keep closing entries in the ecosystem defect register
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix and the register go in one PR.

Successor to `HANDOFF_2026-08-30_round-30-validated-cochange-fixed-doc-tools-released.md` — cite this
one by its full name. **Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`); its own validation status is §8. All dates UTC.

**A bare "§N" in this document means a section OF this document.** Every reference to a section of
any other file names that file, per the convention adopted 2026-09-01 and widened 2026-09-02
(`Juniper/AGENTS.md` § Cross-Project Conventions — the governing ancestor; the juniper-ml mirror was
still an open PR at the time of writing).

**Register moved 74 → 78 fixed, 22 → 18 open.** Four rows closed. `APD-CCLIENT` reached zero open,
the fourth grouping to do so.

---

## 0. Remaining work

1. **Successor, first — validate this document (§8).**
2. **`APD-DATA-018` is now a clean owner decision, not a research task.** All four generator timings
   are measured and recorded in §1.6 of
   `notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md`. The
   recommendation (§4 of that file) is Option 6 — bound the inputs — and it has **two sub-cases**:
   `equities` needs a *default* changed (`EQUITIES_DEFAULT_MAX_SYMBOLS = None` → finite, one
   constant, ~34 min → seconds); `csv_import` needs a cap **added**, since none exists. Do not
   present these as equally cheap. The unresolved sub-question, deliberately not guessed, is
   recorded in §6 of that file: **rows or bytes** for the `csv_import` cap.
3. **`APD-DATA-019` (pagination) has no analysis yet** and is the natural next one. Verified facts
   already in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.1 — **but its
   anchors are dead and must be re-read first.** `total = len(filtered)` is `storage/base.py:537`
   (not `:504`) and the cursor path `:545-548` (not `:515`); data#313 shifted them **ten minutes
   after** ml#1539 recorded them as "re-verified". The substance holds: the whole filtered set is
   materialised then sliced, **on the cursor path too** — so `APD-DATA-011`'s keyset work fixed
   pagination's *correctness* half and left this *performance* half untouched. register:558 and
   :627-628 carry the same dead anchors and need correcting.
4. **CORRECTED BY VALIDATION — the split is 14 parked / 4 UNPARKED, and this draft had it wrong.**
   The claim "no unparked rows left" was false and is withdrawn. Parked (14): the ten-row
   juniper-data REST group (register:598, "do not action any of them unilaterally"), `CASCOR-005`
   (:689/:694), `RCLIENT-004` + `ECO-004` (:872), `ML-001` (:913). **Unparked (4): `APD-DATA-018`,
   `APD-DATA-019`, `APD-ECO-001`, `APD-ECO-003`.**
5. **`APD-ECO-003` is the cheapest open row in the register, and this draft mis-parked it.** It has
   **no** park text: it appears twice (register:889 bare table row; :975 inside *another* row's
   verification cell). Its remedy is a per-call `timeout` kwarg on two clients, and the pattern is
   already shipped — `APD-RCLIENT-002` (recurrence#130) did the recurrence arm. Remaining:
   `juniper-data-client/juniper_data_client/client.py:302` and
   `juniper-cascor-client/juniper_cascor_client/client.py:544`. §4 of
   `notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md` **schedules it as
   step 2** of its own recommendation, which is irreconcilable with parking it. This is the
   `APD-ECO-002` shape the register records twice as a mis-park (register:611-617, :906): *a bucket
   label is not a rationale*.
6. **`APD-ECO-001` needs an owner ASK, not an inherited park.** Its only "owner decision" phrase sits
   inside `APD-CCLIENT-005`'s verification row (register:974) and refers to `APD-CCLIENT-001` — which
   is FIXED, and whose dependency direction register:525-528 explicitly corrects as having been
   *backwards* in the round-27/28 lineage.
5. Carried unfiled ledger (§6).

---

## 1. Verify starting state

Run from your session worktree; each line standalone (§5.1).

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
python3 util/ad-hoc/register_open_set.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
```

Expected, measured 2026-09-03: FIXED rows **78**; script **`96 rows | 78 fixed | 18 open`**; drift
gate **8 tests, OK**. The §2 Status paragraph of
`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` reads "Seventy-eight … leaving 18
open"; all three must agree.

---

## 2. What this session did — every step, completed

**CORRECTED BY VALIDATION.** The table has 15 numbered rows, but rows hold multiple PRs: the true
total is **28 PRs across six repos** (ml 13, data 5, cascor 3, recurrence 3, cascor-client 2,
canopy 2). The first draft said "fourteen PRs across five repos" — a *row* count read as a PR count,
and five only if juniper-ml is excluded, which holds 13 of them. All 28 verified MERGED with their
squash commits reachable from the relevant `main`; the round-30 pre-squash-tip failure did not
recur.

| # | PR | Result |
|---|---|---|
| 1 | recurrence#143 | `APD-RCLIENT-005` doc fix — the monorepo/name disclosure |
| 2 | ml#1507 | register close `APD-RCLIENT-005` → 75/21 |
| 3 | ml#1512 | `juniper-service-core` **0.7.0** (re-filed under `### Added`) + 4 ungated pin strings |
| 4 | ml#1513 | observability CHANGELOG backfill (4 entries) |
| 5 | data#304, recurrence#144, cascor#604 | service-core ceilings → `<0.8.0` |
| 6 | **Release** `juniper-service-core-v0.7.0` | live on PyPI; verified by clean-venv install |
| 7 | data#306, cascor#606, canopy#546 | lockfiles adopt 0.7.0 |
| 8 | ml#1514, ml#1516 | release-notes renderer: wrong CHANGELOG section claim; wrong link target + DRAFT block |
| 9 | canopy#547 | five first-party pins gain ceilings |
| 10 | cascor#610 + cclient#148 | `APD-CCLIENT-008` — API-09 422 envelope completed |
| 11 | ml#1526 | register close `APD-CCLIENT-008` → 76/20 |
| 12 | cclient#151 + ml#1535 | `APD-ECO-007` — `auto_pong` dated (removal 0.9.0) + policy documented → 77/19 |
| 13 | data#313 + ml#1539 | `APD-DATA-016` — artifact streaming → 78/18 |
| 14 | ml#1558, ml#1565, ml#1580, ml#1584 | `APD-DATA-018` analysis, measurements, two revisions |
| 15 | **data#318** | `arc_agi` empty-dataset fix (536 s → 1.30 s, `(0,900)` → `(1717,900)`) |
| 16 | **ml#1515** | release-notes archive for 0.7.0 — **omitted from the first draft**; it is the gate-exempt archive half of row 6's Release, so a successor auditing the publish ceremony would have found it apparently missing |

Also merged: data#307, recurrence#147 (a shell-escaping artifact **I shipped** in the ceiling PRs).

---

## 3. The four closes, and why each disposition was chosen

Each row's **primer anchor is the authority**, not the one-line register row. That single habit
overturned a proposed disposition three times.

- **`APD-RCLIENT-005`** — two prior rounds proposed repointing `[project.urls]` or closing WON'T
  FIX. Anchor 8188-8195 of
  `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md` calls it "a
  documentation problem, and why `[project.urls]` … pointing at the right repository **matters**".
  Both proposals were backwards. Closed by fixing the README.
- **`APD-CCLIENT-008`** — filed against the client; the defect was on the **server**. cascor never
  registered a `RequestValidationError` handler, so 422s bypassed the API-09 envelope. Both the
  filed anchor and the filed premise were wrong.
- **`APD-ECO-007`** — bundles a policy claim with a concrete debt. The policy half is **documented,
  not built**: nothing in either shared package is currently deprecated, so machinery would ship
  with zero call sites. The concrete half (`auto_pong`) was dated after a census found **zero**
  production users.
- **`APD-DATA-016`** — the media-type sub-finding was **already fixed** before this session, and the
  ETag half belongs to parked `APD-DATA-017`. Only one of the passage's three findings was live.

**A precedent correction worth carrying, re-anchored after validation.** §6 of
`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (at :1034) scopes triage to
`Low`-confidence rows, and `APD-CASCOR-005` is `Low` and on that list — yet its own row says "owner
decision, not a task" (:689) and "Do not unify the three copies unilaterally" (:694). **The
discriminator is the row-level park, not §6**: `APD-SVCCORE-013`/`-016` carried no row-level park;
`CASCOR-005` does. State it that way rather than as "§6 does not license disposal".

**WARNING — every register line number this lineage inherited is stale by 15.** ml#1539 (this
session's own register PR) inserted a net +15 lines at register:617, so citations after that point
shifted. The predecessor's `:674` / `:679` / `:857` / `:898` / `:959` / `:960` / `:984` are now
`:689` / `:694` / `:872` / `:913` / `:974` / `:975` / `:999`; `:598` is unaffected. Verified by
reading each. This is register:579's own warning — *refresh anchors after the fix lands, not
before* — landing on the lineage that wrote it.

---

## 4. `arc_agi`, and the lesson that outranks the rest

Measuring Class B generators for `APD-DATA-018` found `arc_agi` **returning an empty dataset**: its
Hub source `fchollet/arc-agi` does **not** exist — and, on the evidence, never did for this code:
it was hardcoded at the generator's introduction and every test mocks the Hub, so no test ever
exercised it live (say "does not exist and was never verified", not "no longer exists"). The
fallback `multimodal-reasoning-lab/ARC-AGI` is a
reasoning-trace dataset with no `train`/`test` columns, and `item.get("train", [])` swallowed the
mismatch. `X_full` came back `(0, 900)`.

**Two numbers in this paragraph were wrong, and validation caught them.** (a) The image count was
first written as "~92 000" — that is 2000 rows × 46 image columns, *arithmetic presented as a
count of work done*. Only **17,232** cells (18.7%) are populated; null cells decode to `None` at no
cost. (b) The "~9 minutes" (536.42 s) was a **warm** run; the **> 600 s** that actually drove the
Option 4 promotion was the cold one and included a 143 s download of a 1.09 GB parquet. `(0, 900)`
was observed in the later investigation, **not** in the run that timed out. This is the section's
own lesson recurring inside the section: a real number, measuring something other than it appeared
to. Nothing downstream rejects a zero-sample dataset, so it would have been persisted,
content-addressed and served to a trainer as real.

Fixed in data#318: new source, dead fallback removed, schema guard **and** non-empty backstop.
**1.30 s, `(1717, 900)`.**

**Then it forced a retraction.** §4 of
`notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md` had promoted the
async-job option on the strength of `arc_agi` being an unboundable residue. That residue was an
artifact. The promotion is withdrawn; that document now states plainly that its recommendation was
**revised twice by measurement, in opposite directions**.

> A timing measurement taken at face value would have justified building an async job pattern to
> accommodate a generator that was producing nothing at all. The number was real; what it measured
> was not what it appeared to measure.

Four other things this session reported success over unexamined ground: a green `Lockfile Freshness`
on a two-release-stale pin; a CHANGELOG link returning 200 to the **wrong file**; a `detect` bump
driven by unrelated repo-wide commits; and a PR **BLOCKED with all 20 required contexts SUCCESS**
(unresolved CodeQL threads). A green rollup is not evidence a PR can land.

---

## 5. Traps

### 5.1 Sandbox refuses shell STRUCTURE
`for … do … done`, `${PIPESTATUS[0]}`, heredocs inside `&&` lists, and any command the worktree
guard cannot prove stays in-tree are refused — **including a heredoc whose body merely looks
complex**. A standalone heredoc (`> `) runs; `;` and `&&` alone run. Fall back to the Edit tool when
Bash is refused. **cwd does not persist** — use absolute paths or `cd X && cmd` in one call.

### 5.2 `safe_merge.py` livelocks under a fast-moving main
Two runs returned **exit 0 without merging** ("went BEHIND while waiting" ×2, then "auto-merge net
disarmed"). juniper-ml `main` takes merges every ~5-10 min; a 17-context check cycle loses the race.
**Use GitHub auto-merge instead**: `gh pr merge N --auto --squash` (prints **nothing** on gh 2.46.0
— verify `autoMergeRequest.enabledAt` via the API), then drive `update-branch` yourself when the PR
goes BEHIND. Every PR in §2 landed this way.

### 5.3 Verify the checkout is current before editing a sibling
`juniper-cascor-client` was **3 commits behind** and `juniper-data` **4**, both caught only by a
suite count changing (497 vs 502). `git fetch && git rev-list --left-right --count HEAD...origin/main`
before touching any sibling.

### 5.4 juniper-data runs **two** mypy hooks
Production *and* tests. `ruff check` passing locally is not enough — `data#313` failed CI on
`str(tmp_path)` where a `Path` was typed. Run `pre-commit run --files <changed set>` before pushing.

### 5.5 Sequence Safety fires on intended test removals
Removing/renaming test symbols FAILs the screen. Waive with `Allow-Symbol-Loss: method:Class.name`
commit trailers — they work in **any commit** of base..HEAD (no force-push needed), accept the full
key or the stripped form, and reject a `*` wildcard. Enumerate each with its reason.

### 5.6 Unfiled ledger
CARRIED: `raise_on_status=False` for data-/recurrence-client; the canopy / cascor-worker audit
(eleventh carry); juniper-recurrence the service still has zero register rows; cascor-client WS
`rstrip("/")`-only base URL; recurrence app/model py.typed; MEMORY.md compaction; py.typed packaging
unguarded in all three clients (off-mandate — closes no row).
NEW: `observability`, `data-client`, `cascor-protocol` are unbounded in **cascor and data** too
(canopy fixed in canopy#547); the release-notes renderer's `Full Changelog` link and DRAFT block
were fixed, but no test pins either.

---

## 6. Git status

Written from harness worktree `curried-brewing-ocean`, branches cut from `origin/main`, all
auto-deleted on merge. **Zero open PRs authored by this session.** No task worktrees created; no
sibling primary checkout left dirty (cascor was frozen throughout — its writes used throwaway
clones; `juniper-data` and `juniper-cascor-client` were restored to `main` at 0/0). Concurrent
sessions were active continuously; `git fetch` + `gh pr list` before every push.

---

## 7. Validation of this document

**VALIDATED, one round, 2026-09-03** — three REFUTE lenses (PRs/counts; the `arc_agi` claim and the analysis; routing/parks). Every finding below was re-derived in source before being applied, and the two lenses that disagreed on register line numbers were adjudicated: `:887`/`:889` are the §4 table rows, `:974`/`:975` the §5.1 rows carrying the only park-ish mentions — both were right about different lines.

**Falsified and corrected in this document:** the "~92 000 images" figure (really **17,232** populated of 92,000 cells — arithmetic presented as a count, the section's own lesson recurring inside it); "fourteen PRs across five repos" (really **28 across six**); the omission of **ml#1515**; "no unparked rows left" (really **14 parked / 4 unparked**, with `APD-ECO-003` the cheapest open row); every register line citation except `:598` (stale by ~15 after this session's own ml#1539); and `APD-DATA-019`'s anchors (`:537`/`:545-548`, not `:504`/`:515` — invalidated by this session's own data#313 ten minutes later).

**Survived every attack:** the 74→78 / 22→18 move and all four intermediate counts; all 28 merge SHAs on main; the four-groupings claim and its ordering; §1's expected values; the 0.7.0 release; the `(0, 900)` mechanism, reproduced end-to-end from the pre-fix module; the post-fix `1717 = 1301 + 416`; and the retraction being genuinely recorded in both directions.

**A second round is still owed** — the predecessor needed two, and its round 2 reversed round 1's routing twice. §8 of the predecessor
(`HANDOFF_2026-08-30_round-30-validated-cochange-fixed-doc-tools-released.md`) records that two
rounds were needed there and that **round 2 reversed round 1's routing twice** — so a single round
is not sufficient evidence.

For the successor validating this document, attack in this order:
1. **§2's fourteen-PR table** — verify each merge SHA is an ancestor of the right `main`, and that
   the attributed PR number matches. Round 30 shipped pre-squash branch tips here.
2. **§1's expected values** — re-derive all three independently; they must agree with each other.
3. **§4's `arc_agi` claim** — the strongest claim in the document. Verify `(0, 900)` was real (the
   pre-fix behaviour is reconstructable from data#318's diff) and that 1.30 s is reproducible.
4. **§3's precedent correction** — read register:674, :679, :984 and §6 of
   `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` yourself.
5. **§0.4's "no unparked rows left"** — recount the park text for all 18 open ids. This lineage has
   got that count wrong twice (14/8 was really 16/6).

---

## 8. Session-close checklist (state at handoff)

- [x] Handoff document generated (this file)
- [x] PR opened for this document — **ml#1590**, auto-merge armed
- [x] Consensus validation begun — three REFUTE lenses launched 2026-09-03
- [x] Consensus findings applied — three lenses, corrections in this document
- [ ] **Round 2 validation** (the predecessor needed one; round 2 reversed round 1 twice)
- [ ] **Fix "~92 000" in three places outside this file**: §1.6 of `notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md`, `juniper-data/CHANGELOG.md:17`, and `juniper-data/juniper_data/generators/arc_agi/generator.py:151` — the code comment will outlive the rest
- [ ] **Correct register:558 and :627-628** — they carry the dead `APD-DATA-019` anchors

**If context ends before a box is ticked, the unticked ones are the successor's first work**, in
that order, before §0.2.
