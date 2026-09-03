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
   already in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.1: `total =
   len(filtered)` at `storage/base.py:504` materialises the whole filtered set then slices, **and
   does so on the cursor path too** (`:515`) — so `APD-DATA-011`'s keyset work fixed pagination's
   *correctness* half and left this *performance* half untouched.
4. **The other 16 open rows are owner-parked.** Per the recount recorded in this lineage, `ECO-001`
   (register:959) and `ECO-003` (:960) carry park text; the ten-row juniper-data REST group is
   owner-routed at register:598; `CASCOR-005` (:674/:679), `ML-001` (:898), `RCLIENT-004`/`ECO-004`
   (:857) are parked. **There are no unparked rows left.**
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

Fourteen PRs merged across five repos. All content verified on the relevant `main` after merge.

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

**A precedent correction worth carrying:** §6 of
`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` scopes triage to `Low`-confidence
rows, and `APD-CASCOR-005` is `Low`, on that list, **and** says "owner decision, not a task … do not
action unilaterally". So §6 membership is *eligibility to triage*, never a licence to dispose.
That register's own line 984 misstates this.

---

## 4. `arc_agi`, and the lesson that outranks the rest

Measuring Class B generators for `APD-DATA-018` found `arc_agi` **returning an empty dataset**: its
Hub source `fchollet/arc-agi` no longer exists, the fallback `multimodal-reasoning-lab/ARC-AGI` is a
reasoning-trace dataset with no `train`/`test` columns, and `item.get("train", [])` swallowed the
mismatch. `X_full` came back `(0, 900)` after ~9 minutes of decoding ~92 000 images that were then
discarded. Nothing downstream rejects a zero-sample dataset, so it would have been persisted,
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

**NOT YET VALIDATED.** No round has been run. §8 of the predecessor
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
- [ ] PR opened for this document
- [ ] Consensus validation begun
- [ ] Consensus findings applied

**If context ends before a box is ticked, the unticked ones are the successor's first work**, in
that order, before §0.2.
