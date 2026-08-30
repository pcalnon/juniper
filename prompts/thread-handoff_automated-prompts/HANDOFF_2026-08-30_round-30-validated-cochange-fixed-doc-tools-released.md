# HANDOFF 2026-08-30 — round 31: round 30 validated (7 claims falsified, 2 of them on main), the co-change gap closed, doc-tools 0.1.2 shipped, and ZERO register rows closed

The standing mandate is unchanged: keep closing entries in the ecosystem defect register
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix and the register go in one PR.

Successor to
`HANDOFF_2026-08-29_defect-register-round-30-service-core-zero-open.md`
— cite this one by its full name. Validate this document with independent agents before trusting it
(memory `feedback_validate_handoff_prompts_independently`). Its own validation status is §8.
All dates UTC. A bare §N means this document; register-anatomy terms ("the §2 Status paragraph",
"§4.2", "a §5.1 row") always name sections of the register.

**Read this first: this session closed NO register rows.** It spent itself on the predecessor's §0
items 1 and 2, on owner-directed release work, and on repairing what validation found. The register
is exactly where round 30 left it — 74 fixed / 22 open.

That is a shortfall against the mandate, not a neutral outcome — **but it is also not "everything
left is owner-gated"**, which is the excuse this lineage is at risk of settling into. Measured:
**14 of the 22 carry explicit register park text; 8 do not** (§0.2 lists both sets). The register's
own §4.1 lesson block records **over-parking three times** — "a bucket label is not a rationale…
a member with no stated reason is unexamined, not deferred" — and records zero instances of an
unsafe close. Route accordingly: the risk here runs toward carrying rows forever, not toward
closing one hastily.

---

## 0. Remaining work

1. **Successor, first — validate this document (§8).** No round has been run on it.
2. **Successor — close register rows. 14 of the 22 are register-parked; the other 8 are NOT.**
   That split is the number this lineage has never written down, and it is the whole routing
   question. Parked, with quotable text: the ten juniper-data REST rows (register:598, "do not
   action any of them unilaterally"), `APD-CASCOR-005` (:679), `APD-ML-001` (:898), and
   `APD-RCLIENT-004` + `APD-ECO-004` (:857, "DEFERRED"). **Unparked: `APD-ECO-001`, `APD-ECO-003`,
   `APD-ECO-007`, `APD-CCLIENT-008`, `APD-RCLIENT-005`, `APD-DATA-016`, `-018`, `-019`.**

   **Two are executable now, by the register's own precedent** — a session may author a disposition;
   `APD-SVCCORE-007` closed as **disclosure only** (:951) and `APD-SVCCORE-013`/`-016` as
   **docstring / WON'T FIX** (:984), both settled by the §6 "triage before actioning" instruction
   with no owner approval recorded:
   - `APD-RCLIENT-005` — close **WON'T FIX**, pinning the rationale. Its complaint is a false
     positive: `juniper-recurrence-client` is a sub-package of the `juniper-recurrence` monorepo, so
     `[project.urls] -> pcalnon/juniper-recurrence` (`pyproject.toml:49-52`) is CORRECT, and
     distribution-vs-import (`juniper-recurrence-client` / `juniper_recurrence_client`) is PEP-mandated,
     not drift. One repo, one PR. (Round 30's validation refuted *changing* the URLs — which is the
     same finding, pointed at the right remedy.)
   - `APD-CCLIENT-008` — read the SERVER before writing anything. juniper-cascor registers handlers
     for `ValueError`, `HTTPException` and `Exception` (`src/api/app.py:719-760`) but **not
     `RequestValidationError`**, so FastAPI's `{"detail": [...]}` is still live for 422 alongside the
     wrapped `{"status":"error","error":{...}}`. Both envelopes are real. The honest finding is an
     **incomplete server-side migration**, not "the client sniffs two shapes" — so either close it as
     disclosure at the client's `_handle_response`, or re-file it against cascor.

   Do NOT force a close on a parked row, and do not invent a park for an unparked one. Re-read the
   source first — see §3's anchor warning.
3. **Successor — `juniper-service-core` has UNRELEASED code and a 0.7.0 would escape the ceilings
   this arc just set.** `detect` reports `UNRELEASED_CHANGES / minor -> 0.7.0` from ml#1332
   (a Cursor-fleet PR, merged `cf072040`): `websocket/worker_stream.py` and `workers/coordinator.py`,
   both substantive.

   **Under the plan this is a PATCH (0.6.1), and 0.6.1 escapes NOTHING. Put the choice to the
   owner; do not assume a minor.** Two validation rounds fought over this and round 2 won on the
   text: plan §6 (`notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md:296-308`)
   derives the bump from exactly two signals, and its only "adds API surface" escalator is scoped to
   **`Security`**, NOT to `Fixed`. service-core files #1332 under `### Fixed`
   (`juniper-service-core/CHANGELOG.md:10`) and the commit is `fix(...)`, so the table's
   `fix only ⇒ PATCH — within ceilings; no propagation` applies.

   It is true that #1332 adds `WorkerCoordinator.release_worker_tasks`
   (`workers/coordinator.py:300`, new at this tag) on a class exported in `__all__`
   (`juniper_service_core/__init__.py:193`, lazy map `:276`) — but "new public surface ⇒ minor" is a
   rule **the plan does not contain**, and all three call sites are inside the package. register:627
   records that `.websocket.*` and `workers/` have **no production consumer at all**. So a minor buys
   no consumer anything while firing the whole cascade below. **0.7.0 is an owner OVERRIDE (which N4
   explicitly permits), not a content-determined bump.**

   Also do not read `detect`'s `minor` as evidence: `propose_semver` computes
   `feature = ... or ("feat" in classes)` (`detect.py:823`) where `classes` comes from a **repo-wide**
   compare (`:377`, fallback keeps remote messages `:384-385`). Six `feat:` commits landed repo-wide
   since the tag and **none touches the package**.

   **The escape set — what a 0.7.0 would cost, and what 0.6.1 avoids entirely:**

   | Site | Pin | Covered? |
   |---|---|---|
   | `juniper-cascor/pyproject.toml:105` | `>=0.5.0,<0.7.0` | follow-on PR |
   | `juniper-data/pyproject.toml:110` | `>=0.5.0,<0.7.0` | follow-on PR |
   | `juniper-recurrence` app | `>=0.6.0,<0.7.0` | follow-on PR |
   | **juniper-ml's OWN** `pyproject.toml:57` | `>=0.2.0,<0.7.0` | yes — + the 4 extras tables |
   | `juniper-canopy/pyproject.toml:119` | `>=0.5.0` — **no ceiling** | nothing needed; auto-adopts |

   **Three live `<0.7.0` strings are neither edited nor gated**: `docs/REFERENCE.md:2909` (the
   `**Meta pin**` field row — outside the `### Available Extras` section that both the editor and
   the gate scope to), `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:140`, and
   `juniper-service-core/README.md:102`. All three are files THIS session set to `<0.7.0` by hand in
   ml#1474; they will go stale again and nothing will say so. Plus the two consumer **lockfiles**
   (`juniper-cascor/requirements.lock:65`, `juniper-data/requirements.lock:83`, both `==0.6.0`),
   green-while-stale under constraint-mode (§6) and needing the manual refresh in §5.3.

   **Deliverable: an owner packet in the register:580-590 three-option shape** — PATCH 0.6.1
   (plan-conformant, zero cascade) vs MINOR 0.7.0 (override; 5-site escape + 3 ungated strings +
   2 lockfiles) — not a settled minor. Building that packet is session work; choosing is Paul's.
4. **Paul — `juniper-observability` is `UNRELEASED_CHANGES / minor` with a warning**:
   "CHANGELOG [Unreleased] has no feature/fix/security bullets (under-documented)". 2 ship /
   5 discounted files. **Its `[Unreleased]` is literally EMPTY** (`CHANGELOG.md:9-10`) — so no
   heading is driving that `minor`; it is entirely the repo-wide `feat:` commit-prefix input
   described in item 3, which is the worse trap. The actionable half is not the version at all:
   write the missing CHANGELOG entries for the changes that are actually there
   (`middleware/request_id.py` +48/-1 ingress validation, ml#1156; `prometheus_helpers.py` +12/-4
   return type, ml#1245; py.typed, ml#1237), then let the documented content pick the bump.
5. **Paul — the parked register decisions, unchanged from round 30**: the ten-row juniper-data REST
   group (§4.1); `APD-ECO-001`; `APD-ECO-007`; `APD-ECO-004` ↔ `APD-RCLIENT-004` (deferred
   2026-08-26); `APD-CASCOR-005`; `APD-RCLIENT-005`; `APD-ML-001`.
6. **Nobody yet — py.typed packaging is unguarded in all three clients** (carried from round 30 §0.6;
   the fact is confirmed — all three ship the marker, declare it as package-data, carry the
   `Typing :: Typed` classifier, have **no** `MANIFEST.in`, and nothing asserts any of it; a
   `py.typed|py_typed` grep over the three test suites returns zero).

   **Do this LAST, and know what it is.** A validation round proposed it as the successor's first
   action; round 2 refuted that on two grounds. (a) **It is off-mandate** — it closes no register
   row. There is no APD row for client py.typed packaging: `APD-RCLIENT-003` is already FIXED
   (register:851), and `APD-SVCCORE-008` / `APD-OBS-002` cover juniper-ml's own sub-packages only.
   (b) **It lands green on all three**, so it is a pure ratchet — worth having, but it pins the
   reference implementations against a regression that has never occurred (register:933:
   "This was a deviation from an existing convention, not an ecosystem gap").

   Two corrections to how round 30 described the model: `tests/test_subpackage_py_typed.py` has
   **five** arms, not one — including a marker-file-on-disk check (`:100-107`) and an anti-vacuous
   guard (`:136-146`) — and its docstring says why both halves are needed. And the
   declaration check is a **proxy** for wheel contents that is sound only because no `MANIFEST.in`
   exists; a build-backend switch would make every `[tool.setuptools.*]` key inert while all arms
   still pass. Only a wheel build closes that, which is how `APD-SVCCORE-008` was verified once —
   as a one-time check, not a gate. Cost is 3 PRs across 3 repos (one a monorepo carrying its own
   coverage and memory-budget gates), not one.
7. Carried unfiled ledger (§5.6).

---

## 1. Verify starting state

Run from your session worktree. Each line standalone — see §5.1.

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main    # 0 N -> git pull --ff-only origin main
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
python3 util/ad-hoc/register_open_set.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
```

Expected, all measured 2026-08-30: FIXED rows **74**; script **`96 rows | 74 fixed | 22 open`**;
drift gate **8 tests, OK**. The §2 Status paragraph in words ("Seventy-four … leaving 22 open") is
the authority; all three must agree.

Zero-waiver check (read values, not text — `grep -c 'status=KNOWN_GAP,'` is a vacuous pass):

```bash
python3 -c "import sys;sys.path.insert(0,'tests');import test_service_fork_drift as m;g=[x.guard_id for x in m.GUARDS if x.status==m.KNOWN_GAP];print(len(m.GUARDS),'guards, KNOWN_GAP:',g);sys.exit(1 if g else 0)"
# -> 6 guards, KNOWN_GAP: []   exit 0
```

Release-train state: `python3 util/release_train/detect.py` — expect `juniper-doc-tools 0.1.2/0.1.2
UP_TO_DATE`, and `juniper-service-core` + `juniper-observability` as `UNRELEASED_CHANGES`.
`detect` runs fine either way (`-m util.release_train.detect` and the script path give byte-identical
output). **`propose` does NOT**: `python3 -m util.release_train.propose` dies with
`ModuleNotFoundError: No module named 'detect'`, because *propose.py* imports `detect` as a
same-directory sibling. Run **propose** as a script path; either form works for detect. Note also
that `detect` exits **1** when anything is not `UP_TO_DATE` — that is its normal signal, not a crash.

Cascor-primary freeze: `python3 util/ad-hoc/cascor_freeze_tell.py`. It was IN FORCE all session
(live uvicorn out of the primary's `src/`, plus two python3.13 children). Do not write to that
checkout; §5.3 has the safe pattern that worked.

---

## 2. What this session did

Six juniper-ml PRs merged plus two sibling PRs. Every SHA below is the **merge commit** and was
verified an ancestor of `main` (`git merge-base --is-ancestor`, and `gh api compare` for siblings) —
round 30 shipped pre-squash branch tips here, so the check is now mandatory.

| PR | What | Merge |
|---|---|---|
| ml#1474 | register: service-core was the **third** grouping to zero, not the first; 3 stale pin/version facts; `Last Updated` | `fe3dfa2d` |
| ml#1476 | `propose.py` cross-repo docstrings — 6 stale sites | `7df7fcd4` |
| ml#1479 | round-30 handoff archived with its §10 validation result | `b3d158e9` |
| ml#1478 | co-change gap CLOSED — whole documented extras surface | `5fbb3d0d` |
| ml#1484 | doc-tools v0.1.2 version bump (Gate 1) | `4f070d17` |
| ml#1486 | doc-tools v0.1.2 release-notes archive (ceremony-opened) | `c6b64ca7` |
| data#300 | lockfile adopts service-core 0.6.0 | `68d73d43` |
| cascor#597 | lockfile adopts 0.6.0 + corrects the header's `-o` path | `6f3b09a7` |

**Round 30's handoff was validated in two rounds** (three REFUTE lenses, then a round 2 against
round 1). Seven claims falsified; the full record is §10 of its archive. Two were **on main**, not
just in the handoff, and are fixed. Round 2 overturned two of round 1's own conclusions — see §9.

**`juniper-doc-tools` 0.1.2 is live on PyPI** (uploaded `2026-08-30T06:27:39Z`; wheel + sdist).
Shipped as a **patch, not the detector's minor** — owner decision. First end-to-end exercise of the
release-train **ceremony** mode in this repo (§6).

---

## 3. What is left — 22 open, and the "cheap one" is contested

| Repository | Open | Assessment |
|---|---:|---|
| `juniper-data` | 13 | the ten-row REST group is owner-routed (§4.1); `-016`/`-018`/`-019` design-shaped |
| `APD-ECO-*` | 4 | `-001`/`-004`/`-007` owner decisions; `-003` see below |
| `juniper-recurrence-client` | 2 | `-004` deferred; `-005` — **see the warning below** |
| `juniper-cascor-client` | 1 | `-008` envelope sniffing — design-shaped; needs a **cascor server** decision (below) |
| `juniper-cascor` | 1 | `-005` owner decision |
| `juniper-ml` | 1 | `-001` — release-train question first |

**`APD-ECO-003` is NOT simply "the cheap one."** Its facts hold (all three anchors dead;
recurrence-client has a per-call timeout on `train`/`crossval` only, 8 public methods without;
data-client has no per-request override; cascor-client hardcodes `timeout=self.timeout`). But
register:960 routes "which of their methods warrant the kwarg" into the row **as a decision**, and
round 30's own paragraph calls it "medium cost, not one kwarg". Two cross-repo PRs plus fake-parity
plus a register PR.

**`APD-RCLIENT-005` — do not FIX it; DO close it.** Round 30's validation proposed changing its
`[project.urls]` and was refuted: `juniper-recurrence-client` is a sub-package of the
`pcalnon/juniper-recurrence` monorepo, so pointing at that repo is **correct** and changing it would
make the metadata wrong. The register carries the monorepo fact three times (:182, :887, :933). But
"the proposed fix is wrong" is not "the row is blocked" — the row is a **false positive**, and this
register closes those (`APD-SVCCORE-016`, WON'T FIX, :984). Round 30 §0.5 listed it under Paul's
parked decisions; the register itself carries no park for it (it appears exactly once, at :853).
Prefer the won't-fix close over another round of carrying it.

**`APD-CCLIENT-008` is design-shaped but the shape is on the SERVER.** juniper-cascor never
registered a `RequestValidationError` handler (`src/api/app.py:719-760` covers `ValueError`,
`HTTPException`, `Exception` only), so 422s still return FastAPI's `{"detail": [...]}` beside the
wrapped envelope. The client is sniffing two shapes because two shapes exist. Read both sides before
writing anything.

**Anchor rot, measured — and the criterion matters more than the number.** Only **17** of the 22
rows carry a file:line anchor at all (the other five name directories or "all route decorators", so
they cannot rot). Of those 17, exactly **2 are ALIVE** — `APD-ML-001` (all five anchors land on the
uncapped first-party pins it describes) and `APD-RCLIENT-005` (`pyproject.toml:49-52` is the
`[project.urls]` block). So **15 carry at least one dead anchor**.

"Wholly dead" is where two validation passes disagreed (13 vs 14), and the disagreement is real:
it turns on whether an anchor that lands *inside the right function but not on the named construct*
counts as dead. Score strictly (must land on the construct) and it is **14**; allow
"inside the right method" and `APD-RCLIENT-004` becomes partial — but then `DATA-008`, `DATA-018`,
`CASCOR-005` and `DATA-026/-027` do too, and the 15 moves as well. **Do not quote a number without
stating the rule.** The actionable fact is unchanged and is the only one worth carrying: at most
2 of 22 rows can be trusted to point at real code. Re-read source before acting on any row.
(Round 30's "≥16 dead" is false under every rule.)

---

## 4. The register-PR protocol

Five touches per close: the §4 table row (`**FIXED (<pr>)**` — prefix, qualification inside the
marker), the §3 detail entry's Status (only some rows have one), a §5.1 verification row, the §2
Status paragraph (counts in words + running ID list + "leaving N open" + "all N are recorded"), and
the header **Last Updated**. Then a whole-file `grep -n 'APD-<ID>'` — and READ each hit, because grep
finds mentions and only reading decides whether a closure falsified one.

**`**FIXED` is the machine-readable token — never invent a second marker.** A won't-fix is still a
close. `register_open_set.py` keys on it, and the three-way count check is what catches a drift.

**A correction-only register PR is legitimate** — ml#1474 and the earlier ml#1449 are both precedent.
The five-touch rule is about closes; it does not forbid fixing a false statement.

`References JR-ML-QA-001` is FABRICATED — no QA area exists. Real areas: API ARCH DATA DEP DOC LOCK
OBS OPS PERF SEC TEST TOOL TRAIN UI WS. Real prefixes include `JR-CCL-*` (not `JR-CCLIENT-*`). When
nothing applies, delete the section and say the work is tracked in the register.

---

## 5. Traps

### 5.1 The sandbox refuses shell STRUCTURE, and the cwd claim is session-dependent

Refused, measured: `for … do … done`, `${PIPESTATUS[0]}`, a heredoc inside an `&&` list, and any
command complex enough that the worktree guard cannot prove it stays in-tree (**a shell function
definition alone tripped this**). A standalone heredoc (`> `/`>> `) runs. `;` and `&&` alone run.

**Correction to round 30 §5.1:** "the Bash cwd PERSISTS between calls" is true only in a main
interactive session. In a **subagent thread the cwd resets every call**, and this session observed
`Shell cwd was reset to …` after `cd` in its own main thread too. Treat cwd as non-persistent: use
absolute paths, or `cd X && cmd` in ONE call.

Also: `echo "exit=$?"` after a **pipe** reports the exit of the last pipeline element, not your
script — and `${PIPESTATUS[0]}` is refused here, so read the script's own output text instead.

### 5.2 The signing hazard is REAL but does not apply to a local commit here

Round 30 §5.2 stands as written for the REST contents API. But this box's `commit.gpgsign=true` and
the YubiKey signing key **were reachable all session**: every local commit came out `G / Good
signature` and merged normally. So the ordinary branch → local signed commit → push → PR flow works
and is preferable to `util/open_signed_pr.py`, whose `--add` sends WHOLE files and can silently
revert concurrent changes. Verify with `git log --format='%G?' -1` **on your own commit, before you
push**.

**Do not run that check on a merged SHA — it will read `E` and mean nothing is wrong.** Two signing
regimes are in play and §2's table names only the second: your local pre-squash commit is signed by
Paul's YubiKey (`%G?` = `G`, committer `Paul Calnon`), while the squash-merge GitHub creates is signed
by **GitHub's own key** (`%G?` = `E`, committer `GitHub`, "Can't check signature: No public key" —
that key is not in the local keyring). Measured: `3d3fd5f6` → `G Paul Calnon`; its merge `fe3dfa2d` →
`E GitHub`, which `gh api …/commits/fe3dfa2d --jq .commit.verification` independently reports as
`verified:true`. Every commit reachable from `main` is `E` for this reason. `E` on main is normal;
`E` on a commit you just authored locally is the problem.

### 5.3 Writing to a repo whose primary checkout is frozen

The pattern that worked, twice: `git clone --depth 1 --branch main <ssh-remote> <scratchpad>/x`,
edit there, commit (signed), push, `gh pr create`. Zero interaction with the frozen checkout. Read
the sibling's remote first — each repo uses its own SSH host alias (`github.com-juniper-cascor`).

**Round 30 §5.3 was FALSE and is fixed (ml#1476).** `propose.py --execute --cross-repo` does NOT
write to sibling checkouts; it has been GitHub-API-only since 2026-08-14. The checkout is a
READ-ONLY input. The real hazard, now recorded at the guard: `create_signed_commit` sends WHOLE file
bodies read from the local checkout onto a branch cut from live `main`, so a **stale** sibling
checkout commits over concurrent work — and `expectedHeadOid` cannot see it, because it guards a
branch that was just created. Fetch siblings before an `--execute --cross-repo` run.

### 5.4 A green CI waiter can go stale under you

`util/wait_for_checks.py` reported `GREEN — 17/17 required contexts, mergeState=CLEAN`, and the PR
then read `BLOCKED` with three required jobs pending. Not a waiter defect: `safe_merge.py` had done
an **update-branch**, producing a new head and a fresh required-check run. Diagnose before acting —
compare the PR's `headRefOid` against the commit you pushed. Its args are `--repo <bare-name>
--owner <owner>`; passing `--repo pcalnon/juniper-ml` yields `pcalnon/pcalnon/juniper-ml`.

With `delete_branch_on_merge: true` on all nine repos (verified), merged branches vanish — so
`git branch -r` showing your branch means a **stale local ref**, not a leftover. `git fetch --prune`
before concluding anything about branch hygiene.

### 5.5 `pre-commit run --files` green means PATH SCOPE, and nothing else

**Corrected here after a validation round falsified the previous wording, and the standing memory
`reference_precommit_files_skips_untracked` with it.** `pre-commit run --files` does **not** consult
git tracked/staged status at all. It matches the literal path you pass against each hook's
`files:` / `exclude:` / `types:` patterns — that is the only mechanism.

Measured both directions:

- An **untracked** file in an in-scope location IS processed. A `?? util/ad-hoc/_zz_probe.md` ran
  8 of 23 hooks; trailing-whitespace **failed and rewrote the file on disk**. So "`git add` first"
  is not a remedy, because there was never an untracked skip to remedy.
- A **tracked** file can still show "no files to check" on every hook — because `prompts/.*` sits in
  the **top-level `exclude:`** block (`.pre-commit-config.yaml:35-...`), which applies to ALL hooks,
  not merely markdownlint's own narrower exclude.

So an all-Skipped run tells you the path is out of scope; it never tells you the file is untracked.
When a `prompts/` document is your deliverable, the real gate is
`tests/test_thread_handoff_archive.py` (its filename-canonicality arm globs the directory), not
pre-commit.

### 5.6 The unfiled-work ledger

- CARRIED: `raise_on_status=False` for data-/recurrence-client (§4.4); the canopy / cascor-worker
  audit (tenth carry) — and juniper-recurrence the service, still zero register rows; the
  cascor-client WS `rstrip("/")`-only base URL; recurrence app/model py.typed; the cascor-client
  fake-vs-server divergence; MEMORY.md compaction; the 08-21 stale cascor-client worktree
  `fix/503-branch-unreachable`.
- NEW: §0 items 3 and 4. Plus a cosmetic one: the release-notes template emits "review and expand it
  before the release ceremony" into notes the ceremony itself already published — stale advice by the
  time anyone reads it.
- NO task worktrees were created; all work was branches cut from `origin/main` in the harness
  worktree, and every branch auto-deleted on merge.

---

## 6. Method notes that earned their place

- **The detector's bump has TWO inputs and neither is a judgement about your package.**
  `propose_semver` (`detect.py:820-828`) ORs a CHANGELOG-heading signal
  (`FEATURE_CATEGORIES = {"added","changed","deprecated"}`) with a commit-prefix signal
  (`"feat" in classes`). The heading half is why doc-tools scored `minor` off a `### Changed` whose
  own last sentence reads "No runtime or behavioral change". **The commit half is worse and was
  missed on the first pass here**: `classes` comes from a **repo-wide** compare (`detect.py:377`,
  fallback keeps remote messages at `:384-385`), so `feat:` commits in *unrelated* parts of
  juniper-ml raise a sub-package's bump. Observability's `minor` is driven purely by that — its
  `[Unreleased]` is empty, so no heading exists to blame. The plan says it outright (N4: "**Not** a
  versioning oracle … *proposals* the owner may override"). Read the diff, and check whether the
  package gained public surface.
- **Choosing patch over minor avoided a live cascade.** 0.2.0 would have escaped doc-tools' `<0.2.0`
  ceiling and fired the co-change path across five extras tables plus two workflow pins — on a real
  release, hours after that code was written. 0.1.2 escaped nothing: "none needed (new version within
  existing ceilings)".
- **Dry-run the automation before its first real use.** Ceremony mode had never executed here. Running
  `ceremony.py --dry-run` locally produced a 4-step plan with `0 HALTED`; the live run then performed
  exactly those four steps. Cheap, and it turns "should work" into "does work".
- **Check the gate topology BEFORE firing, not after.** `testpypi` carries only a branch policy — no
  reviewer, no timer — so TestPyPI publishes unattended; `pypi` carries `required_reviewers:[pcalnon]`
  plus a 5-minute wait. Knowing that in advance is what let the ceremony run without ambiguity about
  what would happen unattended.
- **A gate that passes forever is not the same as a gate that is satisfied.** `Lockfile Freshness` is
  constraint-mode: it compiles with `--constraint requirements.lock` and asks only whether the lock
  still SATISFIES pyproject. `==0.5.1` satisfies `>=0.5.0,<0.7.0`, so both locks sat stale for a day
  with CI green. Adopting a newly published version is a deliberate act nothing prompts.
- **A range auto-adopts; a lockfile does not.** The same 0.1.2 needed no consumer floor bumps
  (`>=0.1.0,<0.2.0` resolves to newest at install) while 0.6.0 needed explicit lockfile refreshes.
  Do not generalise one to the other.
- **Mutation-test the guard, not just the fix.** ml#1478's four mutations each killed a distinct arm.
  The one worth copying is the **positive control**: a test asserting each editor actually MOVES the
  live file, because every other assertion in that suite is satisfied by an editor that does nothing.

---

## 7. Git status

Written from the harness worktree `zippy-meandering-boole`, on branches cut from `origin/main`.
Working tree clean apart from this file; no task worktrees created; no sibling checkout written to
(the two lockfile refreshes used throwaway clones); the cascor primary never touched — it was frozen
throughout. Concurrent sessions were active all session (backup, canopy-E2E, perf-lane, fleet-triage,
cli-exp, agents, plus the Cursor automation fleet) — `git fetch` + `gh pr list` before every push.
Of the ~25 juniper-ml PRs merged in this window, only the six in §2 are this session's; do not
attribute the rest. In particular ml#1498's "register" is the canopy-E2E **finding** register
(`F-ML-002`), not the defect register — a name collision worth not tripping over.

One caveat on the no-worktrees claim, raised by validation and worth stating plainly: it is a
first-person record. A created-then-removed-then-pruned worktree leaves no trace, so a later reader
cannot verify it from state alone — only fail to contradict it.

---

## 8. Validation of this document

**VALIDATED, two rounds, 2026-08-30** — three REFUTE lenses (facts/git, executability/safety,
consequence/routing), then a round 2 over what round 1 changed. Every finding was re-derived in
source by the authoring session before being applied; two lens findings were **rejected** on
re-derivation (a claimed `git show --stat` pathspec quirk that does not reproduce, and a claim that
§0.3 implied canopy carried a ceiling — it never mentioned canopy).

Round 1 survived: all eight merge SHAs; the zero-rows-closed headline; the ml#1332 attribution; the
PyPI publish; every §1 expected value; `delete_branch_on_merge` on all nine repos. Round 1 falsified
and this document now carries corrected: the `-m` invocation claim (it is **propose** that fails,
not detect); the pre-commit untracked-file claim (path scope is the only mechanism — this also
falsifies the standing memory `reference_precommit_files_skips_untracked`); the signing check
(local `G` vs merged `E`); §0.3's omission of juniper-ml's own ceiling and of three ungated
`<0.7.0` strings; §0.4's heading-heuristic misattribution; and §3's unreproducible "13 wholly dead".

**Round 2 again overturned round 1, twice, and both reversals are load-bearing here.** Round 1
concluded that *no* open row is actionable without an owner and that py.typed guards should be the
successor's first act. Round 2 showed only **14 of 22** carry register park text, that
`APD-RCLIENT-005` and `APD-CCLIENT-008` are executable under the register's own
disclosure/won't-fix precedent (:951, :984), and that py.typed is **off-mandate**. It also refuted
the minor-bump justification this document had adopted from round 1 — the plan's "adds API surface"
escalator is scoped to `Security`, not `Fixed`, so service-core is a plan-conformant **PATCH** and
0.7.0 is an owner override. **Two lineage rounds running, round 2 has reversed round 1's routing.
Do not skip it.**

For the successor validating THIS document: attack §0.2's 14/8 split (recount the park text
yourself); §0.3's PATCH-not-MINOR reading of plan:296-308; the claim that `APD-RCLIENT-005` and
`APD-CCLIENT-008` are unparked (each appears exactly once in the register — verify); and §3's
anchor criterion. Measure with `wc -w` before quoting length.

Measured: **4,709 words / 480 lines** — up from round 30's 2,646. Almost all of the growth is §0.2
and §0.3, and it is there because two validation rounds were needed to establish the routing that
neither round 30 nor round 1 got right. If a future round can state the park split and the bump
reading in half the space without losing the citations, it should.

---

## 9. Corrections to the predecessor

Round 30's handoff was validated over two rounds; all seven falsifications are recorded in §10 of its
archive (`HANDOFF_2026-08-29_defect-register-round-30-service-core-zero-open.md`). The four that
change what a successor should DO:

1. **§5.3's cross-repo hazard did not exist.** Fixed at the source in ml#1476 — see §5.3 above.
2. **§2's "first repository with ZERO open rows" was false** and was **on main** at register line 62.
   `juniper-observability` (ml#1245) and `juniper-data-client` (dclient#171) reached zero first;
   service-core was third. Fixed in ml#1474, worded as "third **grouping**" — strictly, neither
   observability nor service-core is a repository at all, so "third repository" would have replaced
   one false claim with another.
3. **§0.2's artifact set was wrong twice.** `docs/REFERENCE.md` needs ONE edit, not two (it has no
   inline table; `_pins_from_inline_extras_table` returns `{}` for it), and the set is per-package,
   not a fixed five — doc-tools and ci-tools each carry workflow pins gated by
   `test_*_drift.py::test_juniper_ml_own_workflows_pin_current_version`, which does NOT skip in
   per-PR mode. Closed in ml#1478 to the corrected spec.
4. **§2's "Seven rows closed" was +8**, and that is the same miscount its own §9.6 corrects the
   predecessor for. Two rounds in a row. If you write a count in §2, derive it from
   `register_open_set.py`, not from reading your own table.

Also corrected: §2's ECO-006 SHAs were pre-squash branch tips (unreachable once the branches
auto-deleted), and §3's "≥16 dead anchors" is false under every reading (§3 above has the real
numbers).
