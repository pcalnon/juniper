# HANDOFF 2026-08-28 — defect register round 29: 66 fixed / 30 open; a "latent" row was live, and "nothing is cheap" was false for the third round

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix **and** the register go in one PR.

Successor to [`HANDOFF_2026-08-26_defect-register-round-28-four-entries-closed.md`](HANDOFF_2026-08-26_defect-register-round-28-four-entries-closed.md)
— cite this one by its full name. **Validate this document with independent agents before trusting
it** (memory `feedback_validate_handoff_prompts_independently`). This draft's own validation status
is in §8. All dates UTC. A bare §N means this document, except register-anatomy terms ("the §2
Status paragraph", "§4.1", "§4.3", "a §5.1 row"), which always name sections of the register.

**Disposition of the predecessor.** Its §0 items 1–5 are consumed. Its round-1 validation was run
this session with three REFUTE lenses and **changed the plan** — see §9. Its §5 traps are corrected
here, two of them as **hazards**.

---

## 0. Remaining work

1. **Successor, first — validate this document (§8).** No round has been run on it.
2. **Paul — the recurrence consumer PR is blocked on a service-core release.** ml#1434 fixed
   service-core, but `juniper-recurrence` resolves it from PyPI
   (`juniper-service-core>=0.5.0,<0.6.0`), so **the exposure persists in recurrence until a release
   ships** — mitigated only by its default loopback bind. Once published: pass
   `explorers_enabled=not settings.api_keys` at `juniper_recurrence/app.py:86-91`, and invert
   `tests/test_app_smoke.py::test_docs_reachable_and_exempt`, which currently asserts the defect as
   correct. One small PR. **Publishing is an owner gate** (memory
   `feedback_deploy_approvals_paul_manages`).
3. **Paul — `delete_branch_on_merge` is `false` in seven repos.** juniper-data was set 2026-08-28;
   **juniper-ml is the only other `true`**. Still false: cascor (≥100 branches), canopy,
   data-client, cascor-client, cascor-worker, recurrence, deploy. One
   `gh api repos/pcalnon/<repo> -X PATCH -f delete_branch_on_merge=true` each.
4. **Paul — the parked decisions, unchanged**: the now **ten**-row juniper-data REST group (§4.1);
   `APD-ECO-001`; `APD-ECO-007` (owns `APD-CCLIENT-012`'s removal date); `APD-ECO-004` ↔
   `APD-RCLIENT-004` (deferred 2026-08-26, recorded §4.6); `APD-CASCOR-005` (§4.3);
   `APD-RCLIENT-005`; `APD-ML-001` (release-train question first). Plus the open **§4.3** question:
   should cascor's latent `EXEMPT_PATHS` copy become a filed ID, or stay a note?
5. **Successor — 30 open rows, and I have NOT individually assessed all of them.** §3 says what is
   known and what is not. **Do not repeat the lineage's signature error by asserting nothing cheap
   remains** — read §3 before believing any such claim, including mine.
6. **Nobody yet — the seven latent `juniper-service-core` rows** (`.websocket.*` / `workers/`).
   Re-verified 2026-08-26. **But see §5.1**: "latent" was wrong once this arc, by exactly the rule
   these seven are filed under. Re-derive the consumer graph before trusting it a third time.
7. **Carried unfiled ledger (§5.7).**

---

## 1. Verify starting state

Run from your session worktree. **Each line standalone** — see §5.2.

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main    # 0 N -> git pull --ff-only origin main
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
gh pr list --repo pcalnon/juniper-ml --state open
```

**Expected:** FIXED rows **66** (the §2 Status paragraph in words is the authority — sixty-six /
**30 open**); drift gate `8 tests, OK` (`skipped=3` without the env var is correct).

**The zero-waiver check — use this, NOT the old grep.** Round 28's §1 used
`grep -c 'status=KNOWN_GAP,'` and called it "the only line that proves the ledger still waives
nothing". It proves nothing: five waiver spellings evade it, and **two of those survive every
pre-commit hook** (an aliased constant, and positional `Guard("id", …, KNOWN_GAP, …)`). Read the
*values*:

```bash
python3 -c "import sys;sys.path.insert(0,'tests');import test_service_fork_drift as m;g=[x.guard_id for x in m.GUARDS if x.status==m.KNOWN_GAP];print(len(m.GUARDS),'guards, KNOWN_GAP:',g);sys.exit(1 if g else 0)"
# -> 6 guards, KNOWN_GAP: []   exit 0
```

**Re-derive the open set with the script, not the tables** — `util/ad-hoc/register_open_set.py`
(shipped ml#1434). Expected `96 rows | 66 fixed | 30 open`. It excludes three §5.2 pre-primer rows
(`APD-CCLIENT-F01`, `APD-SVCCORE-F01`, `APD-SVCCORE-F02`) by regex shape rather than by section, so
99 row-ids exist; the 96 is correct but the exclusion is accidental. The §1 grep *would* match an
`F`-row marked FIXED while the script would not, so "counts agree" compares two populations. Low
risk today; fix the regex if an F-row ever gains a marker.

**Cascor-primary freeze.** The tell in round 28's §1 is **unsound in both directions** — see §5.1.
Use `python3 util/ad-hoc/cascor_freeze_tell.py` (exit 1 = freeze in force). It found a live
`uvicorn` on 8202 out of the primary's `src` that the old tell reported as absent. Root-owned
importers are invisible to any unprivileged tell; read a clean result as "no user-owned importer".
**You do not need to touch the cascor primary anyway** — cut task worktrees from `origin/main`.

If the harness worktree refuses `git checkout main`, that is normal. **Success is the dangerous
outcome**: local `main` is often checked out nowhere, so a checkout here takes the ref hostage from
the primary. Always `git checkout -b <branch> origin/main`.

---

## 2. What this session closed — seven PRs, all merged and verified

| Entry | Fix PR | Merge SHA |
|---|---|---|
| service-core auth bypass (§4.3 note, no ID) | ml#1434 | `80cefb44` |
| `APD-CCLIENT-001` | cclient#143 | `ff3df6cc` |
| `APD-DATA-033` | data#297 | `ff55735d` |
| `APD-ECO-005` | dclient#177 / cclient#144 | `fff37078` / `cfc7e076` |
| register 63 → 66 | ml#1436 | `c5a63dfb` |

Also: five round-28 worktrees removed with local **and remote** branches deleted in all five repos;
`delete_branch_on_merge` enabled on juniper-data.

**The live finding.** `juniper-service-core`'s `create_app` passed no `docs_url`/`redoc_url`/
`openapi_url` — zero occurrences package-wide — so FastAPI mounted all three unconditionally, and
`_is_exempt` is a bare membership test. `juniper-recurrence`, the sole production consumer, served
its **complete OpenAPI surface to unauthenticated callers** with `REQUIRE_AUTH` defaulting to true.
The register had filed this **latent**, applying the §4.2 no-consumer rule to `middleware.py`, which
that rule does not cover. Fixed per data#295 option (a): three paths out of `EXEMPT_PATHS`,
`explorers_enabled` (default `True`) added to `create_app`. cascor's copy really is latent.

---

## 3. What is left — 30 open, and what is actually known about them

| Repository | Open | Assessment status |
|---|---:|---|
| `juniper-data` | 13 | the **ten**-row REST group is owner-routed (§4.1); `-016`/`-018`/`-019` are design-shaped and were re-read this arc |
| `juniper-service-core` | 7 | filed latent — **by the rule that failed this arc**; re-derive before trusting |
| `APD-ECO-*` | 5 | `-001`/`-004`/`-007` have real per-row rationale; **`-003` and `-006` do not** |
| `juniper-recurrence-client` | 2 | `-004` deferred (§4.6), `-005` three-name identity, Low conf |
| `juniper-cascor-client` | 1 | `-008` envelope sniffing — design-shaped, belongs beside `-031` |
| `juniper-cascor` | 1 | `-005` owner decision |
| `juniper-ml` | 1 | `-001` — release-train question first |

**What I did not do: individually re-read all 30.** Three were closed because an adversarial lens
walked them; I have not repeated that walk over the remainder. **Two rows are the same shape as this
arc's misses and deserve first look:**

- **`APD-ECO-003`** — a lens found all three of its register anchors dead, and its claim "in all
  three clients" already false: `APD-RCLIENT-002` shipped a per-call timeout override in
  recurrence-client, data-client's `**kwargs` path threads it and only mis-reports the effective
  value, cascor-client hardcodes `timeout=self.timeout`. That is **sibling drift with a shipped
  reference implementation**, not a decision. Medium cost — not one kwarg. *(Reported by an agent;
  I did not independently verify the anchors. Check before acting.)*
- **`APD-ECO-006`** — grouped as "decision-shaped" with no per-row rationale, exactly like
  `APD-ECO-002` was before it turned out to be one kwarg per client.

**Do not read the table above as "the rest is parked."** Read it as "the rest is unaudited."

---

## 4. The register-PR protocol (corrected)

Five touches per close: the §4 table row (`**FIXED (<pr>)** — ` prefix; partial closes qualified *in
the marker*), the §3 detail entry's `Status`, a §5.1 verification row, the §2 Status paragraph
(counts **in words** + running ID list + "leaving N open" + "all N are recorded"), and the header
`**Last Updated**` when the day changed. **The fifth touch is a whole-file `grep -n 'APD-<ID>'`** —
and it is not cosmetic: this round it caught three prose claims the closures made **false**,
including `APD-ECO-001`'s "Every non-idempotent POST in the stack duplicates on replay". Counts must
agree three ways: §1 grep, re-derivation script, paragraph.

**`References JR-ML-QA-001` is a FABRICATED id — stop citing it.** There is no `QA` area at all.
ml#1418 carries it; so did the protocol text. Real areas: `API ARCH DATA DEP DOC LOCK OBS OPS PERF
SEC TEST TOOL TRAIN UI WS`. Real prefixes include `JR-ML-* JR-CAN-* JR-CAS-* JR-DAT-* JR-CCL-*`
(**not** `JR-CCLIENT-*`). `JR-ML-SEC-097` fits any exempt-list auth bypass. When nothing applies,
`AGENTS.md` says delete the section — do that, and say the work is tracked in the register instead.

Open the fix PR first, then write the register with the number it returned. Merge order: fix PR
merged and **verified via `mergeCommit`**, never safe_merge's exit code, then the register PR.
`BEHIND` needs `gh api repos/pcalnon/juniper-ml/pulls/<N>/update-branch -X PUT` — assume it.

---

## 5. Traps — this round's, in the order they will bite

### 5.1 "Latent" is a claim about the CONSUMER GRAPH, not about the code in front of you

The arc's most expensive error. Two copies of a defect read identically at the source; what
separates latent from live is *does any consumer reach this?* A module-level rule is a **proxy** for
that question and answered it wrong for the one module with a consumer. Worse, **a checked-in test
asserted the defect as correct** (`test_docs_reachable_and_exempt`), so every source re-read
confirmed it. Before writing "latent": name the consumers, check each one's **construction** path
(a shared package can lack the gate its forks have), and grep the consumers' tests for one asserting
the current behaviour.

### 5.2 The sandbox refuses shell STRUCTURE, not sibling paths

Round 28's §5.1 blamed sibling paths. Wrong — a heredoc reading a sibling checkout runs fine. What
is refused: `for … do … done`; `mkdir … && cat > … <<EOF` **with a following command**; `cat >> file
<<EOF`; and **`git -C` pointed at *this repo's* shared checkout** (siblings are fine). Remedy: plain
single commands, or a `util/ad-hoc/` script. Fall back to Write/Edit when a heredoc is refused.

### 5.3 HAZARD — round 28's §5.3 rescue recipe destroys work. Both halves.

- **`git commit --amend` commits the INDEX.** With the fix unstaged it produces a one-commit branch
  **without the fix**, then force-pushes it — the exact failure the recipe exists to prevent. Stage
  first, or `git commit -a --amend`.
- **Bare `--force-with-lease` loses its protection after a `git fetch`** — and §7 mandates a fetch
  before every push. A probe destroyed a peer commit this way. Use
  `--force-with-lease=<branch>:<sha>` with the SHA you actually expect.

### 5.4 A green rollup with `mergeStateStatus: BLOCKED` is an unresolved review thread

17/17 required contexts GREEN and still unmergeable: two CodeQL threads on ad-hoc scripts (an
unclosed `open()`, a bare `except: pass`). **Fix the code, never suppress** — the threads
auto-resolve as *outdated*. Query them:
`gh api graphql -f query='{repository(owner:"pcalnon",name:"juniper-ml"){pullRequest(number:N){mergeStateStatus reviewThreads(first:10){nodes{isResolved path}}}}}'`

### 5.5 `gh pr edit --body-file` fails SILENTLY behind a deprecation warning

It printed a Projects-classic GraphQL notice and **did not update the body** — verified by re-reading
it. Use `gh api repos/OWNER/REPO/pulls/N -X PATCH --input <json>` instead, and verify by re-reading.

### 5.6 Round 28's §5.4 claim is FALSE — an identity check on `response_model` DOES discriminate

Measured on fastapi 0.137.0: a `-> dict` handler reports `response_model` = `<class 'dict'>`, not
the declared model, so `route.response_model is ResponseEnvelope` is a **sound** check. Only a
non-None/truthiness check is vacuous. The residual gap is narrow: a `-> ResponseEnvelope`
*annotation* is indistinguishable from a decorator declaration.

### 5.7 The unfiled-work ledger

- **CARRIED**: `raise_on_status=False` for data-/recurrence-client (§4.4); the **canopy /
  cascor-worker audit** (eighth carry) — **and add `juniper-recurrence` the service to that list**,
  which also has zero register rows and is the sole production consumer of service-core's middleware;
  the cascor-client WS `rstrip("/")`-only base URL; recurrence app/model `py.typed`; the
  cascor-client fake-vs-server divergence; MEMORY.md compaction; the 08-21 stale cascor-client
  worktree `fix/503-branch-unreachable`.
- **NEW — four worktrees this session created**, all PRs merged, cleanup pending Paul's signal:
  `juniper-cascor-client--fix--apd-cclient-001-idempotent-retry--20260828-0830--4041604f`,
  `juniper-data--fix--apd-data-033-rate-limit-window--20260828-0845--d3c806d0`,
  `juniper-data-client--test--apd-eco-005-version-lockstep--20260828-0900--20742fd6`,
  `juniper-cascor-client--test--apd-eco-005-version-lockstep--20260828-0900--ff3df6cc`.
  **Every repo except juniper-ml and juniper-data still needs `git push origin --delete` first.**
- **DONE**: the predecessor's §0 items 1–5, 7 (worktrees), and item 2 (ml#1420, `31e8b754`).

---

## 6. Method notes that earned their place

- **A group boundary drawn by ID range is a label, not an assessment.** `APD-DATA-033` sat in the
  eleven-row REST group by ID adjacency; the note gave per-row reasons for `-008`/`-017`/`-022` and
  none for `-033`. This is the *same* lesson round 28 wrote down about `APD-ECO-002` and then
  repeated. It is now recorded in §4.1 where the next reader of the group will meet it.
- **The structural arm is never the proof.** Every fix this round has a pin that passes **unchanged
  against the broken code** — a `Settings` field nobody reads, a constant that never reaches
  urllib3, a `path not in EXEMPT_PATHS` that survives a rename. Always add the arm that reads the
  value back off the thing the app actually built, and mutation-check that it is the one that fails.
- **A mutation that kills only one arm is evidence, not a gap.** `APD-DATA-033`'s mutation failed 1
  of 3 — precisely the arm designed to be decisive.
- **Verify every JR id before citing it.** A fabricated one propagated through an entire arc.
- **Check the siblings after every close** — and then check the *consumers*, which is the step this
  arc added and which is what found the live exposure.

---

## 7. Git status

Written from the harness worktree `juniper-ml/.claude/worktrees/soft-chasing-shannon`, archived from
a branch cut off `origin/main`. Seven PRs merged (§2); working tree clean at `c5a63dfb`. Four task
worktrees remain (§5.7). Sibling checkouts were fetched, never pulled or `pip install -e`'d; the
cascor primary was never written. **The cascor freeze WAS in force during this session** (a
concurrent stack's uvicorn on 8202) — irrelevant to this work, which was juniper-ml only, but do not
assume it is clear. Concurrent sessions were active throughout (canopy E2E, P5, backup); `git fetch`
+ `gh pr list` before every register push.

---

## 8. Validation of this document

**NOT VALIDATED.** Run three REFUTE-mode lenses — facts/git, executability/safety, consequence —
then a second round over whatever the first changes.

Attack first: §2's SHAs; §3's per-repo split (**re-derive, do not read**); the §3 claim that
`APD-ECO-003`/`-006` are the likeliest cheap rows — that came from an agent I did not fully verify;
§5.3's two hazards (reproduce them); §5.6's fastapi claim; and §1's freeze tell. **The single
highest-value target is §3's honesty**: three consecutive rounds asserted "nothing cheap remains"
and all three were wrong, so verify that this document's refusal to make that claim is matched by
its table actually being unaudited rather than quietly implying otherwise.

**2,807 words** (`wc -w`, the same measure round 28's lineage figures used) — shorter than round 28's
3,398, whose length correlated with its errors. Stated as a measured number rather than an estimate:
round 28 claimed "~2,900" against an actual 3,398, and I first wrote "~2,150" here against an actual
2,737 before measuring. **Run `wc -w` before quoting your own length** — the estimate is wrong by
20-30% in both recorded attempts, and a dated, specific-looking number is exactly what a successor
will not re-check.

---

## 9. Corrections to the predecessor

Round 28's own §8 recorded it as never validated. It was validated this session, and the result
changed the plan.

1. **Its central claim was false.** "Nothing is both cheap and unblocked (this time it is true)" —
   three rows were both, and closing them is most of this round. Third consecutive round to make
   this error.
2. **`APD-CCLIENT-001` was never blocked on `APD-ECO-001`.** The dependency runs one way:
   restricting an unsafe retry needs no idempotency key; only *enabling a safe one* does. Corrected
   in the register.
3. **Its §3.3 "latent in both" was wrong for service-core** (§2, §5.1).
4. **Its §5.1 refusal cause was wrong** — shell structure, not sibling paths (§5.2).
5. **Its §5.3 recipe is actively destructive**, both halves (§5.3).
6. **Its §5.4 `response_model` claim is false** (§5.6).
7. **Its §1 `KNOWN_GAP` grep is a vacuous-pass** (§1).
8. **Its §5.7 said "six worktrees" and listed five**; and `delete_branch_on_merge` was false in
   **all five** repos, not just juniper-data — following it as written would have left four stale
   remote branches.
9. **§8's own length was understated** — "~2,900 words" against an actual 3,398. Its lineage figures
   were right.
10. **Everything else survived.** The facts lens returned **zero refutations across 41 checks** —
    every SHA, count, line number and version floor reproduced. Round 28 is reliable on facts; it
    failed on judgement and on recipes.
