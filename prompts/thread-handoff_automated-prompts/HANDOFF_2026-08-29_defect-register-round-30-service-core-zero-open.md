# HANDOFF 2026-08-29 — round 30: service-core reaches ZERO open rows, 0.6.0 is live on PyPI, and the release train shipped red twice

The standing mandate is unchanged: keep closing entries in the ecosystem defect register
(notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix and the register go in one PR.

Successor to
`HANDOFF_2026-08-28_defect-register-round-29-live-exposure-closed.md`
— cite this one by its full name. Validate this document with independent agents before trusting
it (memory feedback_validate_handoff_prompts_independently). Its own validation status is §8.
All dates UTC. A bare §N means this document; register-anatomy terms ("the §2 Status paragraph",
"§4.2", "a §5.1 row") always name sections of the register.

Disposition of the predecessor. Its §0 items 1–4 and 6 are consumed. Its round-1 validation was
run and changed the plan; a round 2 then refuted round 1 — see §9. This is the first round in
the lineage where the validation's own output needed validating.

---

## 0. Remaining work

Ordered so the successor-actionable items come first. The predecessor buried three owner-gated items
at the top and its own §17 said to fix that; this does.

1. Successor, first — validate this document (§8). No round has been run on it.
2. Successor — propose.py still has a live co-change gap that ships the NEXT release red.
   Documented at the site and in the generated PR body (ml#1460) but not fixed. Its S5.4 logic
   claims the escaping meta pin has "two lockstep artifacts"; there are five —
   tests/test_pyproject_extras.py, AGENTS.md, plus README.md, docs/QUICK_START.md,
   docs/REFERENCE.md. docs/REFERENCE.md needs two edits: the inline table, and a separate
   "Extras Reference" table whose distribution and specifier sit in different columns, which a
   combined-string substitution silently misses. Generalise apply_pin_edits_agents_table to
   README/QUICK_START, add a split-column editor for REFERENCE, and pin it in
   tests/test_release_train_propose.py.
3. Successor — 22 open rows; the cheap ones are named in §3, and this time they were audited.
4. Paul — cascor and juniper-data need a requirements.lock refresh to actually adopt 0.6.0.
   The ceiling bumps merged, but both locks still pin juniper-service-core==0.5.1 and could not do
   otherwise until 0.6.0 existed on PyPI. It exists now. juniper-recurrence has no lockfile and
   picks it up directly; juniper-canopy pins a floor only.
5. Paul — the parked decisions, unchanged: the ten-row juniper-data REST group (§4.1);
   APD-ECO-001; APD-ECO-007; APD-ECO-004 ↔ APD-RCLIENT-004 (deferred 2026-08-26);
   APD-CASCOR-005; APD-RCLIENT-005; APD-ML-001. The §4.3 "should the latent cascor copies
   become filed IDs" question was ANSWERED 2026-08-29: keep as prose notes, do not file — the 96
   stays a fixed identity.
6. Nobody yet — py.typed packaging is unguarded in all three clients. APD-ECO-006's probes
   deliberately do not cover it (§2). All three ship py.typed; nothing asserts it is packaged, so
   a wheel that dropped it would hand every consumer an untyped package with every check green. This
   is the APD-SVCCORE-008 / APD-OBS-002 class and needs a check against the built artifact.
   juniper-ml/tests/test_subpackage_py_typed.py is the model.
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

Expected: FIXED rows 74; script `96 rows | 74 fixed | 22 open`; drift gate 8 tests, OK.
The §2 Status paragraph in words ("Seventy-four … leaving 22 open") is the authority; all three must
agree.

The zero-waiver check (round 28's `grep -c 'status=KNOWN_GAP,'` is a vacuous-pass — read values,
not text):

```bash
python3 -c "import sys;sys.path.insert(0,'tests');import test_service_fork_drift as m;g=[x.guard_id for x in m.GUARDS if x.status==m.KNOWN_GAP];print(len(m.GUARDS),'guards, KNOWN_GAP:',g);sys.exit(1 if g else 0)"
# -> 6 guards, KNOWN_GAP: []   exit 0
```

Cascor-primary freeze: `python3 util/ad-hoc/cascor_freeze_tell.py` (exit 1 = frozen). It WAS in
force all session (a live uvicorn on :8202 out of the primary's src). Read a clean result as "no
user-owned importer" — root-owned importers are invisible to it, and 2 of its 5 hits are
over-reports (an idle shell; a canopy process matched on a data-path env var). You never need the
cascor primary — cut task branches from origin/main, and see §5.2 for why this mattered.

Release-train state: `python3 -m util.release_train.detect --package juniper-service-core`
should now report RELEASED / no unreleased changes. `curl -s https://pypi.org/pypi/juniper-service-core/0.6.0/json`
resolves (use the version-specific endpoint; the index lags 5–30s after a publish).

---

## 2. What this session did

Fourteen juniper-ml PRs merged (1441, 1443, 1446, 1447, 1449, 1452, 1453, 1454, 1457, 1458,
1459, 1460, 1464, 1468) plus six sibling PRs. Other numbers in that range belong to concurrent
sessions (backup, perf-lane, requirements) — do not attribute them here.

Register 66 → 74 fixed, 30 → 22 open. Seven rows closed:

| Entry | PR | Merge |
|---|---|---|
| `APD-SVCCORE-011` + `-015` | ml#1441 | `655c5909` |
| `APD-SVCCORE-012` | ml#1443 | `c8b80080` |
| `APD-SVCCORE-001` | ml#1446 | `188117e3` |
| `APD-SVCCORE-005` | ml#1447 | `ca44c287` |
| `APD-SVCCORE-013` + `-016` | ml#1454 | `c667c1b5` |
| `APD-ECO-006` | dclient#178 / cclient#145 / rec#138 | `b6cbb323` / `7f39b890` / `9791adb9` |

juniper-service-core is the first repository in the register with ZERO open rows. Three of its
sixteen closed as decisions, not code: -007 (disclosure), -016 (won't-fix — the behaviour is
RFC-conformant and the obvious "fix" is a regression), -013 (docstring, name deliberately
unchanged). Closed, not waived; each records its reasoning at the code.

juniper-service-core 0.6.0 is live on PyPI — Release cut, TestPyPI verified, PyPI published,
notes archived (ml#1464). Consumer ceilings raised to <0.7.0 in cascor#596, data#299, rec#137.

---

## 3. What is left — 22 open, audited this time

| Repository | Open | Assessment |
|---|---:|---|
| `juniper-data` | 13 | the **ten**-row REST group is owner-routed (§4.1); `-016`/`-018`/`-019` design-shaped |
| `APD-ECO-*` | 4 | `-001`/`-004`/`-007` owner decisions; **`-003` is the cheap one** |
| `juniper-recurrence-client` | 2 | `-004` deferred, `-005` Low conf |
| `juniper-cascor-client` | 1 | `-008` envelope sniffing — design-shaped, belongs beside `-031` |
| `juniper-cascor` | 1 | `-005` owner decision |
| `juniper-ml` | 1 | `-001` — release-train question first |

APD-ECO-003 is the best remaining candidate and its facts are verified (two independent agents,
2026-08-29). All three of its register anchors are dead (data `client.py:248` → URL
normalisation; cascor `:363` → a docstring; recurrence `:217` → a docstring). Real state:
APD-RCLIENT-002 shipped a per-call timeout override on recurrence-client but only on `train` and
`crossval` — `predict` and ~8 other public methods have none; juniper-data-client's `_request` is
private and no public method accepts `timeout` or `**kwargs`, so a consumer cannot set one at
all; cascor-client hardcodes `timeout=self.timeout` (`client.py:541`). This is sibling drift with a
shipped partial reference implementation, not a decision — but it is medium cost, not one
kwarg, and the register's own claim "in all three clients" is already false.

≥16 of the open rows carry a DEAD file:line anchor (verified 2026-08-29). Re-read the source
before acting on any row; the register's §3 anchor-note discipline covers only api/app.py.

---

## 4. The register-PR protocol (corrected)

Five touches per close: the §4 table row (`**FIXED (<pr>)**` — prefix, qualification inside the
marker), the §3 detail entry's Status (only some rows have one), a §5.1 verification row, the §2
Status paragraph (counts in words + running ID list + "leaving N open" + "all N are recorded"),
and the header **Last Updated**. Then a whole-file `grep -n 'APD-<ID>'`.

**FIXED is the machine-readable token — never invent a second marker.** A won't-fix is still a
close. Marking APD-SVCCORE-016 as `**CLOSED (…)**` desynchronised the counts instantly (grep 73 vs
script 72) because `register_open_set.py` keys on `**FIXED`. The precedent already existed:
APD-SVCCORE-007 reads `**FIXED (ml#1303, disclosure — the constraint itself stands by design)**`.
The three-way count check is what caught it.

The fifth touch is necessary but not sufficient. It found three falsified prose claims this
round — including one in a §5.1 row written hours earlier the same day ("APD-SVCCORE-001, still
open") and two live docstrings in the package. It also missed one in round 29, because that
sentence named the IDs inside a parenthetical about a different row's grouping. Grep finds mentions;
only reading each one decides whether a closure falsified it.

`References JR-ML-QA-001` is FABRICATED — no QA area exists. Real areas: API ARCH DATA DEP DOC
LOCK OBS OPS PERF SEC TEST TOOL TRAIN UI WS. Real prefixes include `JR-CCL-*` (not
`JR-CCLIENT-*`). When nothing applies, delete the section and say the work is tracked in the register.

---

## 5. Traps

### 5.1 The sandbox refuses shell STRUCTURE — measured, not inferred

Every shape below was executed. A heredoc inside an `&&` list is refused; a standalone heredoc
(`>` or `>>`) runs — so writing a PR body or script that way needs no detour. Also refused:
`for … do … done`, `${PIPESTATUS[0]}`, and `git -C <THIS repo's shared checkout>` (siblings are
fine). `;` alone and `&&` alone run. This applies to the Monitor tool too, not just Bash.
The Bash tool's cwd PERSISTS between calls — a `cd` in one call silently changes later ones; use
absolute paths.

### 5.2 HAZARD — the REST contents API produces UNSIGNED commits, and the symptom is not about signing

All nine repos carry `required_signatures`. Three PRs opened via
`gh api repos/…/contents/… -X PUT` went GREEN on every required context (24/24, 22/22, 10/10),
with zero unresolved review threads and `mergeable=MERGEABLE`, and still reported
`mergeStateStatus=BLOCKED`. `safe_merge.py` refused correctly: "required checks are green but GitHub
will not merge". Nothing in the rollup names the cause — only
`gh api repos/<r>/rules/branches/main` cross-referenced with the commit's own `verification` field
shows `verified=false reason=unsigned`. An unsigned commit anywhere in a branch's history blocks
the merge; squashing does not rescue it — the branches had to be closed and deleted, not repaired.
Use `util/open_signed_pr.py` (GraphQL `createCommitOnBranch`, GitHub-signs server-side); it exists
for exactly this after the ml#1099 fan-out. Its `--add` sends whole files, so build the payload
from the branch tip read via the API, never from a local checkout.

### 5.3 propose.py --execute --cross-repo writes to sibling LOCAL CHECKOUTS

It branches, edits and pushes them. With the cascor primary frozen under a live service that is
unsafe. Run it without `--cross-repo` (it skips the follow-ons with an explicit reason) and open
them through the API instead — `util/ad-hoc/2026-08-29_open_ceiling_bump_prs.py` does this and is
committed.

### 5.4 A green rollup with mergeStateStatus: BLOCKED — three distinct causes seen this round

Unresolved CodeQL review threads (fix the code, never suppress — they auto-resolve as outdated);
an unsigned commit (§5.2); or checks simply still running. Distinguish before acting:
`gh api graphql … reviewThreads` for the first, the branch rules + commit verification for the
second.

### 5.5 CodeQL is right about `class X(Base): pass` inside `pytest.raises`

It binds a name that can never be read, because the definition is what raises.
`type("X", (Base,), {})` is exactly what the class statement compiles to, triggers
`__init_subclass__` identically, and binds nothing. Note it at the site — the class form is the
more natural thing to write and re-trips the alert.

### 5.6 The unfiled-work ledger

- CARRIED: `raise_on_status=False` for data-/recurrence-client (§4.4); the canopy /
  cascor-worker audit (ninth carry) — and juniper-recurrence the service, which still has zero
  register rows; the cascor-client WS `rstrip("/")`-only base URL; recurrence app/model py.typed;
  the cascor-client fake-vs-server divergence; MEMORY.md compaction; the 08-21 stale cascor-client
  worktree `fix/503-branch-unreachable`.
- NEW: §0 items 2, 4 and 6.
- NO task worktrees were created this session — all work was done on branches cut from
  origin/main in the harness worktree, and every branch auto-deleted on merge
  (`delete_branch_on_merge` is now true on all nine repos, set this session).

---

## 6. Method notes that earned their place

- A mutation that survives is not evidence until you have checked it changes behaviour. Moving
  APD-SVCCORE-001's cardinality check to the top of the loop body survived — correctly, because
  that position still runs before the first `receive()`. Moving it after the receive killed the arm
  precisely on the un-consumed-queue assertion while the error frame still fired. Recorded as an
  expected-survival row, not quietly dropped.
- The existing tests are usually not the decisive arm. -016's four gate tests assert the return
  value and the close code; none asserts `accept()` was not reached, so all four survive an
  accept-then-close rewrite — the exact regression the row would provoke.
- A marker that nothing enforces is not protection. `@final` alone would have been vacuous for
  -012: nothing type-checks this package (mypy is scoped `^(scripts|tests)/`; the sub-packages are
  Ruff-only, and Ruff's selected rules do not enforce `@final`).
- Read the PRIMER, not the register's restatement. It changed the disposition of both -013 and
  -016. And the primer is itself wrong about Juniper on -016 (it says accept-then-close; the
  gates are pre-accept) — so verify it too.
- "Repo X has no Y" usually means "Y was somewhere the sweep did not look." Three instances this
  arc, most recently APD-ECO-006, where recurrence-client's config lives at a monorepo root two
  levels up. Correcting it made the row larger.

---

## 7. Git status

Written from the harness worktree `mutable-moseying-gem`, on branches cut from origin/main.
Working tree clean; no task worktrees created, no sibling checkout written to, the cascor primary
never touched (it was frozen throughout). Concurrent sessions were active all session (backup,
perf-lane, requirements, canopy-E2E) — `git fetch` + `gh pr list` before every push.

---

## 8. Validation of this document

NOT VALIDATED. Run three REFUTE-mode lenses — facts/git, executability/safety, consequence — then
a second round over whatever the first changes. This round proved the second round is not
optional: round 1's consequence lens produced a confident, wrong recommendation (§9) that a round-2
lens refuted on evidence.

Attack first: §2's SHAs and the claim that service-core has zero open rows; §3's APD-ECO-003
facts (re-verify against source, do not trust the summary); §0 item 2's five-artifact claim (count
them); §5.2's signing hazard (reproduce the `verified=false` read); the assertion that no other
session's PRs are attributed here. Measure this document with `wc -w` before quoting its length —
the lineage's estimates have been wrong by 20–30% every recorded time.

---

## 9. Corrections to the predecessor

1. Its §3 refusal to claim "nothing cheap remains" was honest in wording but its ROUTING was not.
   It filed the seven juniper-service-core rows under "Nobody yet — latent". All seven are now
   closed, and they were the cheapest rows in the register — juniper-ml's own repo, one PR each, no
   owner gate, no release. Latency is a claim about exposure, not about cost.
2. But round 1's proposed correction was ALSO wrong. Its consequence lens said cascor's forks make
   those rows live and the latent filing is mis-scoped. A round-2 lens refuted it: §4.2's rule is
   explicitly about importers of the shared package and re-derives as true; the register already
   tracks forks via †-marked sibling rows; and the premise "identical code" was false in 2 of 4
   cases, in both directions — cascor is the stricter copy on -001, and the two carry different
   remediations of the same path on -013. §4.2 was qualified, not overturned.
3. Its §5.5 was wrong twice. `gh pr edit` is not silent (exit 1, stderr) and not
   `--body-file`-specific — gh 2.46.0 requests the retired `projectCards` field, so every
   `gh pr edit` on this box fails. Fix the binary. `gh release edit --notes-file` works.
4. Its §1 freeze-tell claim was wrong — the old tell did find the uvicorn, via its cwd arm.
   Round 28's miss was a reading error, not a soundness gap.
5. Its §1 "local main is checked out nowhere" was false — it is checked out in the primary.
6. Its §2/§7 said "seven PRs"; the table listed six.
7. Everything else survived, including both §5.3 git hazards and the §5.6 fastapi measurement,
   which reproduced exactly.

---

## 10. Validation result (appended by the successor, 2026-08-29)

§8 said NOT VALIDATED and named the attack surface. Two rounds were run: three REFUTE lenses
(facts/git, executability/safety, consequence/routing), then a round 2 over what round 1 changed.
Every finding below was re-derived in source by the receiving session before being acted on —
a lens's report is prose about the system; the system is the evidence.

**Round 2 was again not optional.** It overturned two of round 1's own conclusions, exactly as §8
predicted from the previous round.

### Falsified

1. **§5.3 is stale, and the hazard it warns of does not exist.** `propose.py --execute --cross-repo`
   has been **API-only since 2026-08-14** (`7acc4a9f` / `b3fb8335`) — `createCommitOnBranch`, zero
   local `git push`/`clone` in the module. The sibling checkout is a **read-only input**
   (`read_file` sources file bodies from it). The doc quoted the file's stale top docstring without
   cross-checking the `ProposeSources` docstring 150 lines below, which says the opposite. Cost:
   round 30 hand-rolled `2026-08-29_open_ceiling_bump_prs.py` to dodge nothing. FIXED in ml#1476,
   which also records the hazard that IS real — whole-file bodies from a **stale** checkout commit
   over concurrent work, and `expectedHeadOid` cannot see it.
2. **§2 "the first repository to reach zero open rows" is false.** `juniper-observability` (ml#1245)
   and `juniper-data-client` (dclient#171) got there first; service-core was **third**. The register
   refutes itself — the `APD-OBS-004` row reads "Takes `juniper-observability` to zero open rows".
   The false claim was **on main at register line 62**, not just here. FIXED in ml#1474, worded as
   "third **grouping**": strictly, neither observability nor service-core is a repository at all.
3. **§2's ECO-006 SHA row names pre-squash branch tips**, not merge commits. Real:
   `211fcdcb` / `96ca4b91` / `f7c64451`. With `delete_branch_on_merge` true on all nine repos
   (verified), the cited SHAs are unreachable and will be GC'd.
4. **§2 "Seven rows closed" is wrong — the delta is +8.** Round 29's own title says "66 fixed /
   30 open" and ml#1468 says "73 -> 74". The table holds 8 IDs across 6 markdown rows; seven is
   none of {6, 8, 8}. **This is the exact error §9 item 6 corrects the predecessor for.**
5. **§0 item 2's artifact set is wrong twice.** `docs/REFERENCE.md` needs **ONE** edit, not two —
   it has no inline table at all (`_pins_from_inline_extras_table` returns `{}`; `_DOCS_INLINE_TABLES`
   omits it). And the set is **per-package, not a fixed five**: doc-tools and ci-tools each carry
   workflow pins gated by `test_*_drift.py::test_juniper_ml_own_workflows_pin_current_version`,
   which does NOT skip in per-PR mode. FIXED in ml#1478.
6. **§3 ">=16 open rows carry a dead anchor" is false under every reading.** Only 17 of 22 rows carry
   an anchor at all; `APD-ML-001` and `APD-RCLIENT-005` are alive. True figure: **15** carry at least
   one dead anchor, **13** are wholly dead. The directional advice (re-read source first) stands.
7. **§3 "APD-ECO-003 is the cheap one" is unsupported and self-contradicting** — the same paragraph
   calls it medium cost, and register:960 routes its method-scoping into the row as an owner decision.

### Round 1's own errors, refuted by round 2

- Round 1 said the propose.py fix was urgent because doc-tools' `0.2.0` is imminent. **False.**
  doc-tools' `[Unreleased]` is a `Fixed` plus a `Changed` whose last sentence is *"No runtime or
  behavioral change"* — a patch (`0.1.2`) that does not escape `<0.2.0`. `minor` is the detector's
  changelog-heading heuristic, and the release-train plan states bumps are *"proposals the owner may
  override"*. The gap is real; the urgency was not.
- Round 1 said `APD-RCLIENT-005` was the cheapest remaining register work. **False and hazardous.**
  `juniper-recurrence-client` is a sub-package of the `juniper-recurrence` monorepo, so
  `[project.urls] -> pcalnon/juniper-recurrence` is **correct**; changing it would make the metadata
  wrong. The register already carries that note three times (lines 182, 887, 933), the row has no §3
  detail entry, and §0 item 5 parks it with the owner. Acting on it would have taken an owner
  decision unilaterally on a row that may not be a defect.

### Survived

Every §1 command and its exact numbers (74 / `96 rows | 74 fixed | 22 open` / 8 drift tests / zero
KNOWN_GAP); §5.2's signing hazard, reproduced end to end; §5.1 claims 1-4 (claim 5, cwd persistence,
holds for a main session but is **false in subagent threads**, where cwd resets every call); §5.5's
`type()` equivalence, proven by execution; §5.6's `delete_branch_on_merge`; all 14 PRs merged with no
cross-arc misattribution; the ceiling bumps; 0.6.0 on PyPI; the sibling lock/floor state; §3's
10+3=13 routing; and §9 item 2's §4.2 defence, with the consumer graph independently re-derived.

Measured length: **2,646 words**, 295 lines.
