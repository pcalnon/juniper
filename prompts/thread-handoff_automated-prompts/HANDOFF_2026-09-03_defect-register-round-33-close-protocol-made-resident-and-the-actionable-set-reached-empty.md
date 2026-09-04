# HANDOFF 2026-09-03 — round 33: the close protocol had no residency, "parked" had three definitions, and the actionable-without-the-owner set reached empty

The standing mandate is unchanged: keep closing entries in the ecosystem defect register
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix and the register go in one PR.

Successor to
`HANDOFF_2026-09-03_defect-register-round-32-four-rows-closed-and-a-measurement-that-reversed-itself.md`
— cite this one by its full name. **Validate this document with independent agents before trusting
it** (memory `feedback_validate_handoff_prompts_independently`); its own validation status is §7.
All dates UTC.

**A bare "§N" in this document means a section OF this document.** Every reference to a section of
any other file names that file.

**The register did not move: 78 fixed / 18 open, before and after.** This round closed no row *on
purpose* — round 2 of the predecessor's validation found that its two nominated "cheap next rows"
were both mis-scoped, and that the protocol governing the whole mandate had stopped existing.

---

## 0. Remaining work

1. **Successor, first — validate this document (§7).** Then read §1.
2. **Every remaining decision is the owner's. There is no code a session may write unasked.** This
   is the round's headline and it is a *finding*, not a blocker: 78 of 96 rows are closed, and what
   is left is 16 parked rows plus 2 unparked ones that still need a decision before any code. The
   four asks are in §3, already put to the owner in-session. **Do not "make progress" by picking
   one.** The register records this at its § *"Parked" has three shapes*.
3. **If the owner answers `APD-DATA-018`** (rows-vs-bytes **and** rejection-vs-truncation for the
   `csv_import` cap): note the equities sub-case is **not** one constant.
   `juniper-data/juniper_data/generators/equities/generator.py:264` is a bare slice that silently
   truncates, so a finite `EQUITIES_DEFAULT_MAX_SYMBOLS` needs a reject-or-report path beside it. A
   *rejecting* cap adds a status code, which entangles parked `APD-DATA-022`.
4. **If the owner answers `APD-ECO-003`**: the row has **two halves**, and only the second was ever
   worked. `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md:378`
   prescribes *"Set a timeout, and split it"* (connect / read / write / pool) — untouched in **all
   three** clients, the "already shipped" recurrence arm included. And `juniper-cascor-client` has
   **no `**kwargs` anywhere in its chain** (`_get`/`_post`/`_delete`/`_patch`/`_request`,
   `juniper_cascor_client/client.py:517-535`): five signatures to thread before any public method
   can take the kwarg. `juniper-data-client` is already the recurrence shape (`client.py:302`).
5. **Carried, all verified live 2026-09-03, none actioned** — `juniper-observability` is at `0.4.0`
   with four `### Fixed` bullets unreleased (content-determined bump: **PATCH 0.4.1**; a release is
   an owner approval); `juniper-data#317` is an **open duplicate** of the `arc_agi` finding, filed
   ~54 min before data#318 was created, and #318 does not reference it; the worktree
   `worktrees/juniper-cascor-client--fix--503-branch-unreachable--20260821-1619--8a34b3a1` is 13
   days stale with local **and** origin branches extant (PR#124 merged) — untouched because
   `git worktree remove` deletes ignored files porcelain cannot see, and there is no owner signal.
6. **Carried from the predecessor's §5.6, with corrections**: two of its carries are themselves
   stale — `recurrence app/model py.typed` has been **fixed since 2026-06-25** (markers on disk
   *and* declared in `[tool.setuptools.package-data]`), carried as missing for ~10 weeks; and the
   MEMORY.md compaction carry omits that ml#1532 ran one on 2026-08-31. Its NEW item is partly
   false: **`juniper-data` has no `cascor-protocol` dependency at all.** Still live: cascor-client's
   fake-vs-server divergence (`testing/fake_client.py:376-378`), the stale worktree above,
   `raise_on_status=False` for data-/recurrence-client, cascor-client WS `rstrip("/")`-only base
   URL, py.typed packaging unguarded in all three clients.

---

## 1. Verify starting state

Run from your session worktree; each line standalone (§5.1).

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
python3 util/ad-hoc/register_open_set.py
python3 util/ad-hoc/register_status_crosscheck.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
```

Expected, measured 2026-09-03: FIXED rows **78**; open-set **`96 rows | 78 fixed | 18 open`**;
cross-check **78 / 78 / 78, AGREE**; drift gate **8 tests, OK**.

`register_status_crosscheck.py` is **new this round** and is the point: the first two commands read
the *same* §4 tables, so they are one measurement reported twice and can agree while both are
wrong. The cross-check reads §4's `**FIXED` set, §2's prose list and §5.1's verification rows
independently and requires the same 78 ids.

---

## 2. What this session did

| # | PR | Result |
|---|---|---|
| 1 | **data#321** | `arc_agi` incident record — three error classes across four sites. MERGED, verified an ancestor of `main` (`ddc67248`). |
| 2 | **ml#1604** | Register: close protocol made resident, park taxonomy defined, four dead anchors refreshed, fork-drift observation recorded, handoff §9. MERGED (`2c7834cc`). |
| 3 | *(this document)* | Round-33 handoff + the intra-document citation rule ml#1604 itself violated. |

Round-2 validation ran three REFUTE lenses — deliberately **not** round 1's — and its results are
recorded as **§9 of the predecessor**, not only here.

---

## 3. The four findings, and the ask

- **The five-touch close protocol had no residency anywhere.** It was written down *only in the
  handoff chain*; round 32 dropped the section, and it then existed in no `notes/` doc, no `docs/`
  page, no `AGENTS.md`, and no agent memory — while the register still **cited it by name**. The
  session complied in practice, so nothing failed loudly. **Now resident** in the register, marked
  do-not-relocate. *A rule that lives only in the document that hands off the work stops existing
  the first time one successor omits it.*
- **"Parked" had three definitions and nobody had noticed.** The split was counted 14/8, then 16/6,
  then 14/4, each round concluding its predecessor miscounted. Park text is written **row-level**,
  **group-level** (`APD-DATA-028`'s *only* protection) and **foreign-cell** (park language for row X
  inside row Y's §5.1 cell — how `APD-ECO-001` and `APD-ECO-003` are parked). One shape → 4 parked;
  two → 14; three → 16. All three numbers were right. The register now adopts all three, because
  that reading can only ever *prevent* unilateral action: **16 parked / 2 unparked**.
- **The ID-keyed sweep is blind to claims that name no ID.** The register read "the third grouping …
  three prefixes read zero" for three days after `APD-CCLIENT-008` made it four — with a *complete*
  four-touch close and a *clean* whole-file grep, because the sentence names no ID. Counts and
  rankings need re-reading after a close; grep will never route you to them.
- **Both nominated "cheap" rows were mis-scoped** (§0.3, §0.4 above).

**The four owner asks, put in-session:** `APD-DATA-018` (rows-vs-bytes **and**
rejection-vs-truncation); `APD-DATA-019` (`total` estimated, cached or absent — the last is a
response-shape change for existing clients); `APD-ECO-003` (is the split-the-timeout half in scope,
and which of cascor-client's 30 / data-client's 20 public methods warrant the kwarg);
`APD-ECO-001` (largest — primer says server-first: 3 services, then 3 clients).

---

## 4. Traps

### 4.1 Sandbox refuses shell STRUCTURE
`for … do … done`, `${PIPESTATUS[0]}` and heredocs inside `&&` lists are refused. A **standalone**
heredoc runs — `python3 - <<'PYEOF' … PYEOF` worked this round for a multi-site edit. `;` and `&&`
alone run. **cwd does not persist** — use `cd X && cmd` in one call.

### 4.2 `safe_merge.py` WORKS — the predecessor's §5.2 advice is reversed
Round 32 said it livelocks and to use GitHub auto-merge instead. **The opposite held this round.**
`main` has `strict_required_status_checks_policy: true`, so auto-merge armed alone can *never* fire
while `main` takes a merge every ~5-12 min: the PR goes BEHIND during its own 17-context cycle, and
auto-merge does not re-sync. Two hand-driven `update-branch` + wait rounds both lost the race.
`python3 util/safe_merge.py --pr N --execute` won on the first attempt — it **re-syncs itself** on
BEHIND ("went BEHIND while waiting — re-syncing"), arms a checks-gated auto-merge net pinned to the
head, then merges locally when green. Note it can print `could not arm auto-merge net … expected
head oid` and still succeed — that is the net failing, not the merge.
**Exit 0 is still not evidence of a merge**: look for the literal `MERGED #N at <sha>` line, then
confirm ancestry with `git merge-base --is-ancestor <merge-sha> origin/main`.

### 4.3 Measuring a line number and then editing ABOVE it invalidates it
Self-inflicted this round, inside the PR that added the anchor-staleness warning: three citations
were measured, a note was then inserted ~450 lines earlier, and all three shipped ~19 lines short.
The register now says: **cite by section name or distinctive phrase, never by its own `:NNN`.**

### 4.4 juniper-data runs two mypy hooks; juniper-ml does not lint `util/`
juniper-data lints production *and* tests. juniper-ml's Black/isort/flake8/mypy/bandit are scoped
`^(scripts|tests)/.*\.py$`, so a new `util/ad-hoc/` script reports "no files to check" — that is
**by design, not a silent skip**; lint it by hand.

---

## 5. Git status

Written from harness worktree `cozy-wibbling-nebula`. Branches cut from `origin/main`, auto-deleted
on merge. **Zero open PRs** at handoff other than this document's. Sibling primaries
`juniper-data`, `juniper-cascor-client`, `juniper-recurrence` all restored to `main` at `0 0` and
clean; `juniper-cascor` was read-only throughout (frozen). Concurrent sessions were active
continuously — `main` took ~6 unrelated merges during this session.

---

## 6. Validation of this document

**NOT YET VALIDATED.** The predecessor needed two rounds and its round 2 falsified six claims,
including both of its forward-routing recommendations. Assume the same here.

Attack in this order:
1. **§3's "no residency anywhere" claim** — the strongest in this document. Re-run the residency
   search yourself over `notes/`, `docs/`, `AGENTS.md` and the agent memory directory *at the
   commit before ml#1604*, not at HEAD.
2. **§3's park taxonomy and the 16/2 split** — recount park text for all 18 open ids independently.
   This lineage has now produced four different answers; a fifth is more likely than not.
3. **§4.2's reversal of the predecessor's merge advice** — one success is not a rule. Check whether
   `strict_required_status_checks_policy` was actually the operative constraint.
4. **§0.5's carried items** — each was verified once, today. Re-verify before acting.
5. **§2's PR table** — verify both merge SHAs are ancestors of the right `main`.

---

## 7. Session-close checklist

- [x] Round-2 validation of the predecessor — three lenses; results in **its §9**
- [x] Predecessor's three unticked boxes — all closed (two under-scoped; corrected)
- [x] data#321 merged and ancestry-verified
- [x] ml#1604 merged and ancestry-verified
- [x] Handoff document generated (this file)
- [ ] PR opened for this document
- [ ] **Consensus validation of THIS document** (§6) — the successor's first work
- [ ] **Owner answers pending on four rows** — `APD-DATA-018`, `APD-DATA-019`, `APD-ECO-003`,
      `APD-ECO-001`. Until one lands, there is no register work a session may do unasked.
