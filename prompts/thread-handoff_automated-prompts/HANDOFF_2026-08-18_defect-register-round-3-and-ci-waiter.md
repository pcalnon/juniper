# HANDOFF 2026-08-18 — defect register: ~84 open, every *encodable* copy-drift row closed, and a shared CI waiter

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per fork-pair. This round closed **seven register entries** across four defect groups (five fixed at the start of the
round, twelve at the end) and built one shared tool. Nothing about
the arc is winding down.

Successor to [`HANDOFF_2026-08-15_api-primer-defect-register-outstanding-work.md`](HANDOFF_2026-08-15_api-primer-defect-register-outstanding-work.md).

**Disposition of that document** — read this before assuming any of it still holds:

- Its **§1** (pre-auth throttle) and the `blank-api-key-filter` it paired with — it called them *"either
  is a defensible next move"*, it did **not** rank them — are both **closed and merged**.
- Its **§4 per-repo table is superseded.** Those numbers were totals-minus-five-fixed; twelve are fixed
  now. Use §2 below.
- Its **§5 taxonomy** (three drift mechanisms) still holds, but its copy-drift row *list* does not —
  two of the three closed this round.
- Its unnumbered **"Read before triaging anything" block is still fully live** (reachability,
  severity-is-not-risk, the `†` marker, retired/split IDs, uneven coverage, anchor drift). The
  load-bearing parts are restated in §2 below; read the original anyway.

**All dates here are UTC.** Local was 2026-08-17 while UTC had rolled to 2026-08-18. That distinction
blocked three PRs — see §5 item 1. A second, unrelated blocker hit the same three PRs; see §5 item 3,
which is the one most likely to cost you an hour.

Throughout: a bare `§N` means **this** document. References to the register are written "the
register's §N".

---

## Verify starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git pull --ff-only origin main     # the primary checkout drifts behind
git rev-list --left-right --count HEAD...origin/main   # expect 0 0
wc -l notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
grep -c 'status=KNOWN_GAP,' tests/test_service_fork_drift.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest -v tests/test_service_fork_drift.py
gh pr list --repo pcalnon/juniper-ml --state open
git -C ../juniper-data log --oneline -1 && git -C ../juniper-cascor log --oneline -1
```

**Expected values, and why they are conditional:**

- `wc -l` on the register: **693** on `main` as this is archived (687 before ml#1154); **696** once
  ml#1156 lands. Do not treat any single number as the invariant — read the
  register's §2 Status paragraph instead, which states the counts in words.
- `grep -c 'status=KNOWN_GAP,'` — expect it to **print `0`** and **exit 1**. That exit code is grep
  signalling "no matches", not a failure; it will abort a `set -e` wrapper. Note the **trailing
  comma**: a bare `grep -c status=KNOWN_GAP` prints `1`, matching a docstring sentence describing the
  mechanism, not a guard row.
- The `FORCE_LOCAL` unittest must report **6 tests, 0 skipped**. Two different conditions skip the
  cross-repo arms — the `GITHUB_ACTIONS`/`FORCE_LOCAL` gate and missing sibling checkouts — and a
  skipped arm asserts nothing. **The siblings must be at their merged `main`** or the gate reads a
  stale tree; that is what the last line checks. In CI this is different by design: `ci.yml` runs the
  same file with no siblings on disk, so **3 of the 6 legitimately skip**. Do not read `skipped=3` in
  `ci.yml` as a bug.
- **`0 skipped` no longer means six live assertions.** With zero `KNOWN_GAP` rows,
  `test_known_gaps_are_still_open_or_get_promoted` iterates an empty set and passes **vacuously**. Five
  arms are live; one is empty until a new gap row exists.

**Use `git -C <path> grep`, never `grep -rn … | wc -l`, against a sibling.** A plain `grep` on a
*missing* checkout writes its error to stderr and prints `0` to stdout, making "absent repo" and
"verified absent" indistinguishable. `git grep` fails loudly.

---

## What closed — and what is about to

| Entry | Fork PRs | juniper-ml PR |
| --- | --- | --- |
| `APD-DATA-001` † / `APD-CASCOR-004` † — unthrottled 401 path | [data#266](https://github.com/pcalnon/juniper-data/pull/266) `cdff3fb`, [cascor#524](https://github.com/pcalnon/juniper-cascor/pull/524) `8295987` | [ml#1130](https://github.com/pcalnon/juniper-ml/pull/1130) `53751fa` |
| `APD-DATA-003` / `APD-CASCOR-006` † — blank API key enables auth | [data#267](https://github.com/pcalnon/juniper-data/pull/267) `8fd002b`, [cascor#527](https://github.com/pcalnon/juniper-cascor/pull/527) `7fa2e66` | [ml#1145](https://github.com/pcalnon/juniper-ml/pull/1145) `132832f` |
| `APD-SVCCORE-003` / `APD-SVCCORE-010` — unvalidated settings lookup + its duplicate | — | [ml#1154](https://github.com/pcalnon/juniper-ml/pull/1154) **pending** |
| `APD-OBS-001` — unvalidated `X-Request-ID` | — | [ml#1156](https://github.com/pcalnon/juniper-ml/pull/1156) **pending** |

`†` = **register-original**: verified against source, not asserted by the primer (the register's §1).
**Retired and split IDs**: `APD-CCLIENT-003` was merged into `-004` and **its number must never be
reused**; `APD-CASCOR-001` was split into `001a` / `001b`.

**The count moved in three steps:** 9 fixed / 87 open → **11 / 85** when ml#1154 landed → **12 / 84**
when ml#1156 does. `main` reads 11/85 as this is archived. Check `main` before quoting a number.

Fixed entries keep their original IDs and are marked `FIXED` in place at the register's §4 table row
and at its §3 detail entry *where one exists*, so an existing reference still lands correctly.

**The encodable copy-drift rows are done.** Every copy-drift row in the register's §2.3 that had a
reference implementation to port is now `ENFORCED`, and **zero `KNOWN_GAP` guard rows remain** in
`tests/test_service_fork_drift.py`. Two scoping caveats that matter:

- **One copy-drift row is still open**: the `OPTIONS` bypass, `APD-CASCOR-001b` / `APD-DATA-035` †.
  Both are **open `C` (Correctness)** entries affecting both running services and **should be fixed** —
  CORS sits behind auth so preflights are answered 401. What must *not* happen is inventing a drift-gate
  marker for it: it landed in **no** copy, so there is no reference implementation to derive one from.
  Fix the defect; leave the gate row unencoded. (`APD-CASCOR-001a` is the paired one-line comment fix
  and is disjoint.)
- **Only the copy-drift sub-group is exhausted.** The register's §2.3 names three mechanisms. The other
  two are untouched and are **not gateable**: **sibling-package drift** (`APD-CCLIENT-001`, `-005`,
  `APD-DCLIENT-004` — three separately released clients, no shared code, so no drift check can apply;
  needs a written cross-client convention) and **same-file inconsistency** (`APD-CCLIENT-006`,
  `APD-DATA-004` — ordinary review misses). Do not reach for `test_service_fork_drift.py` on either.

---

## In flight — check all four before starting

| PR | What | State when written |
| --- | --- | --- |
| [ml#1141](https://github.com/pcalnon/juniper-ml/pull/1141) | `util/wait_for_checks.py` + tests + `ci.yml` wiring — see §1 | **MERGED** `f219594` |
| [ml#1154](https://github.com/pcalnon/juniper-ml/pull/1154) | service-core WS tunable registry | **MERGED** `63af765` |
| [ml#1156](https://github.com/pcalnon/juniper-ml/pull/1156) | observability `X-Request-ID` validation | open, auto-merge armed |
| [ml#1155](https://github.com/pcalnon/juniper-ml/pull/1155) | publish-env policy drift guard — **a concurrent session's** | merged during validation |

**Zero approvals are required** — `required_approving_review_count` is **0** on all nine repos. But
`required_review_thread_resolution` is **`true`** fleet-wide, so a single unresolved review thread
blocks a fully green PR (see §5 item 3). Each `update-branch` restarts CI, and `main` moves often, so they
cycle `BEHIND` → re-run → green. Do not conclude they need an approval.

**ml#1155 collides with ml#1141** — both edit `ci.yml`. All four touch `AGENTS.md`, which is why the
freshness loop below was needed at all.

**ml#1156's stacking (resolved, but read this if it recurs).** ml#1154 has landed and ml#1156's
register conflict was resolved by hand, exactly as predicted below. Its PR base is **`main`**, not ml#1154's branch; only
its *commit ancestry* is stacked, so its diff is a **strict superset** of ml#1154's. Both auto-merge
with **squash**, which creates a new commit that is not an ancestor of ml#1156's branch — so **ml#1154
landing will NOT shrink ml#1156's diff.** After ml#1154 merges, rebase ml#1156 onto `main` and expect a
conflict in the register, which both touch. If ml#1156 wins the race it ships ml#1154's content too; in
that case `APD-SVCCORE-003` / `-010` are closed and ml#1154 should be **closed as superseded, not
re-worked** — confirm by checking whether `juniper_service_core/websocket/tunables.py` exists on `main`.

**Two background loops may still be running.** Find them with `pgrep -af keep_fresh`; stop with
`pkill -f keep_fresh`. Each re-issues `update-branch` when a PR goes `BEHIND`, bounded at 40 rounds ×
60 s; the only write is that branch update. The script lives in **this session's scratchpad**, which is
reaped when the session ends — copy it to `util/ad-hoc/` if you want it to survive, per the
script-placement rule. Do not leave it in `/tmp`.

---

## 1. `util/wait_for_checks.py` — use it, don't hand-roll another CI wait

Three throwaway waiters in one session each failed silently: two reported success on suites that had
not finished, one looped to timeout on a swallowed error. The shared replacement is
`util/wait_for_checks.py` (ml#1141) — read-only, safe to run concurrently.

```bash
python util/wait_for_checks.py --pr 1154
python util/wait_for_checks.py --pr 527 --repo juniper-cascor --fail-fast
python util/wait_for_checks.py --pr 267 --repo juniper-data --json
```

Exit **0** all required green · **1** a required check failed (named) · **2** timeout, with
still-running vs never-reported contexts named separately · **3** hard error.

**The two traps it exists to prevent**, both silent, both real bugs before it existed:

1. **Terminal must be defined POSITIVELY.** An in-flight check run carries `conclusion: null` and no
   `state`, so "not in my list of pending states" reads it as finished. The pending set is
   open-ended; the finished set is closed.
2. **The rollup GROWS as jobs start**, so "everything I can see is terminal" is not "the suite is
   done" — a lull between waves is indistinguishable from completion. Anchor on the branch ruleset's
   **required** contexts. `--anchor observed` reproduces the bug and is opt-in; the suite pins both
   anchors side by side so the difference is executable.

**Gotchas that cost real time:**

- **It does not exist on `main` or on any branch cut before ml#1141.** Retrieve it with
  `git show origin/feat/wait-for-checks-utility:util/wait_for_checks.py > util/ad-hoc/wait_for_checks.py`
  on your working branch — **not** `/tmp`, which the script-placement rule prohibits and which gets
  reaped. Do not hand-roll a fourth waiter.
- **`gh pr checks` has no `--json` on this host** (gh 2.46.0) — only `gh pr view --json statusCheckRollup`
  does. A `|| echo '[]'` fallback around the former makes failure indistinguishable from "no results
  yet"; that is how one hand-rolled waiter looped silently to timeout.
- Probes retry 3× with backoff because transient `TLS handshake timeout` / `unexpected EOF` failures
  hit repeatedly during the arc (ml#1141's AGENTS.md records the figure as of writing; more followed).
  The retry is delay-only and never classifies errors, so a genuinely broken probe still fails every
  attempt — exit 3 keeps meaning what it says.

---

## 2. What is actually left — 84 open (of 96 register totals)

**Read the register's §2.1 before triaging any `Security` entry, and its §4.2 preamble before any
service-core entry.** Topology removes the external attacker from most `Security` rows in the reference
stack — juniper-data publishes no host port, juniper-cascor is loopback-only with attestation — and what
survives is the **bare/dev profile**, where the services bind directly. A `Security` label means neither
"exploitable from the internet today" nor "safe".

**Severity is not a risk assessment.** The register's §6 is explicit that it "reflects the primer's
framing plus verification, not a risk assessment against deployment reality. An operator may reasonably
re-rank." That matters more now, not less — see the ranking gap below.

**`file:line` anchors drift with every commit**; primer line anchors are stable. Where the two disagree
the source is authoritative and the register is stale. Statuses were verified 2026-08-14; twelve fixes
and unrelated commits have landed since, so anchors are staler than that date suggests.

### Open counts (computed from the register's §4 `FIXED` markers; sums to 84)

| Repository | Open | Original | Register |
| --- | ---: | ---: | --- |
| `juniper-data` | **30** | 36 | §4.1 — still the largest group |
| `juniper-service-core` | **14** | 16 | §4.2 — read its preamble first |
| `juniper-cascor-client` | 12 | 12 | §4.4 |
| `juniper-data-client` | 8 | 8 | §4.5 |
| Cross-client / ecosystem / meta | 8 | 8 | §4.8 |
| `juniper-recurrence-client` | 5 | 5 | §4.6 |
| `juniper-cascor` | **4** | 7 | §4.3 |
| `juniper-observability` | **3** | 4 | §4.7 |
| **Total** | **84** | 96 | |

**`juniper-canopy` and `juniper-cascor-worker` have no rows because the primer barely visited them, not
because they are clean** (the register's §6). Most of `juniper-cascor` is in the same position. An
actual audit of those three is **un-done work no document tracks**.

### There is no ranking left — pick deliberately

The register's §2.2 "four highest-value items" was the arc's only ranking mechanism and it is **fully
exhausted**. No successor ranking exists. Two orientations the register supports directly:

- **16 open `C` (Correctness) rows**: `APD-DATA-007/-009/-010/-011/-012/-013/-014/-035`,
  `APD-CASCOR-001b`, `APD-CCLIENT-001/-002/-004`, `APD-DCLIENT-001/-002/-003`, `APD-RCLIENT-001`.
- **`APD-DATA-004` is the last open `S` (Security) row in the register.** Every other `S` is `FIXED`.

Groups this document gives no coverage — a documentation gap, **not** a priority claim:

- **`APD-ECO-001`…`-007`** — untouched. The sharpest is **`-001`: no `Idempotency-Key` mechanism exists
  anywhere in the stack, zero occurrences.** The register makes it the *enabling condition* for
  `APD-CCLIENT-001`; fixing the retry allow-list without a key leaves the gap ecosystem-wide.
- **`APD-RCLIENT-001`…`-005`** — untouched (`-001` is `C`).
- **`APD-OBS-002`…`-004`** — untouched, and all three are `M` (Maintainability): `py.typed`, a return
  annotation, two `__all__` lists.

**Do not action `APD-ML-001` without deciding the release-train question first.** Those pin strings are
byte-for-byte asserted by a passing lint (`tests/test_pyproject_extras.py`, `EXPECTED_EXTRAS` from line
106), so "fixing" them means editing the contract test in the same PR — and capping first-party pins on
a meta-package fed by a daily release train makes `juniper-ml` a permanent release bottleneck.

**Triage every `Low`-confidence entry before actioning it.** Fifteen `Conf | Low` rows span the
register's §4.1–§4.8. Read the `Conf` column, not the register's §6 illustrative subset of six.

---

## 3. Fork consolidation — the precondition moved, but it did not clear

The register's §4.2 preamble creates the circularity: adopting the shared middleware everywhere is
exactly what would make `APD-SVCCORE-003` live, while its §2.2 makes hardening `_setting` a
precondition of consolidating. **ml#1154 changes that calculus without settling it.**

What ml#1154 did: `juniper_service_core/websocket/tunables.py` declares all eleven WebSocket tunables
with defaults and a `security` flag (six are security controls), both handlers resolve through one
shared resolver, and a miss that looks like a **misspelling** logs a WARNING naming both spellings.
`audit(settings)` is the boot-time counterpart. The decoupling the primer praises is untouched — nothing
imports a consuming service's settings class.

**`-003` is booked `FIXED` on the strength of the registry plus the near-miss WARNING. A miss that does
*not* look like a misspelling is still silent.** If you judge that leaves the entry open, re-open it
deliberately rather than letting the count drift.

What is still true after it:

- `juniper_service_core.websocket` still has **no production consumer**, so these remain *latent*
  library defects, not live exposure. `create_app` does not rescue this: `app.py` imports only
  `fastapi`, `.health`, and a `TYPE_CHECKING`-only `starlette` symbol — never `.websocket` / `.workers`.
- **cascor's copy is still stricter for the six security controls** — it reads them as hard attributes
  (`control_stream.py:116-118`, `:144`, `:159-160`, `:424-425`), so a typo raises `AttributeError`,
  which beats a WARNING. Consolidation now trades strictness for reach: a **judgement call**, no longer
  a straight regression. **Scope that precisely — cascor is not uniformly stricter.** Its heartbeat and
  idle tunables use its own defaulted-getattr helper `_numeric_setting`, and its **resume** tunable uses
  a bare inline `getattr` (`training_stream.py:246`), deliberately, to stop non-`Settings` test doubles
  leaking stubs into `asyncio.sleep`. The stricter-fork argument covers the **security subset only**.
- `.middleware` / `.security` still have exactly **one** production consumer, `juniper-recurrence`, via
  the lazy PEP 562 root re-export. juniper-data, juniper-cascor and juniper-canopy *are* production
  consumers of the package root and boot checks — `enforce_auth_posture`, `enforce_dependency_floors`,
  `SettingsBase`, `get_secret`, `TrainingLifecycle` (register entries `-006`, `-008`, `-009`, `-014`,
  `-017`, live for all of them) — but **not** of `.middleware` / `.security`. That distinction is the
  whole content of the consumer split; do not collapse it into "only recurrence uses service-core".

---

## 4. Closing a `KNOWN_GAP` row — the procedure, now that none remain

Kept because the next copy-drift row that acquires a reference implementation will need it, and because
nothing in CI enforces the ordering.

**Order: (a) juniper-data fork PR → (b) juniper-cascor fork PR → (c) juniper-ml promotion + register
edits.** Both drift-gate assertions are **per-site**, so in the window where exactly one fork has
landed, *neither* status value is green.

**(c) is six edits, not one**, all in the register: its §4 table row, its §3 detail entry *where one
exists*, its §2.3 copy-drift row, its §2.2 ranking row (where applicable), a new §5.1 row recording the
PR and its verification, and its §2 Status paragraph's running count — the number this document quotes.

**No CI will catch a wrong order.** The gate is a juniper-ml test (`ci.yml:472`,
`docs-full-check.yml:259`); neither fork repo's CI runs it, and juniper-ml's own `ci.yml` skips the
cross-repo arms. A promotion merged early is green on every PR and red on the **weekly**
`docs-full-check`, up to a week later.

**Verify the promotion in both directions** — it must pass against patched forks *and* fail against
unpatched ones; only the second run proves the constraint is real. Direction one needs no trick once
the forks have merged: your real siblings *are* the patched state. **For direction two**, build a
synthetic ecosystem root (`eco/{juniper-ml,juniper-data,juniper-cascor}`) with the siblings symlinked to
**pre-patch** clones; `_find_ecosystem_root` walks up 6 levels from the juniper-ml root, so it resolves
there with no env override. (A synthetic root exists at this session's `scratchpad/eco/`; it dies
with the session, so rebuild rather than depend on it.)

**Markers verify the presence of a source string, not a behaviour.** Both promotions this round
strengthened their marker to a pair, for **different** reasons:

- `pre-auth-throttle` — the second marker (`record_failure`) pins the half that is easy to omit; a
  `check()`-only port is a throttle that never accumulates.
- `blank-api-key-filter` — the prior bare `.strip()` marker was **sufficient to detect** the fix
  (neither fork's `security.py` contained a strip beforehand) but **not specific to it**: any unrelated
  strip later added to that module would flip the guard green with the filter still absent.

A green `ENFORCED` is a structural proxy; behavioural coverage lives in each fork's own suite.

---

## 5. Traps this session hit, in the order they will bite you

1. **The `AGENTS.md` date check runs on UTC.** `Verify AGENTS.md Last Updated` compares against
   `date -u +%Y-%m-%d`. Local was 2026-08-17 while the runner had rolled to 2026-08-18, so a header
   reading `2026-08-17` was neither "today" nor "bumped in this PR" — it **blocked three PRs at once**
   (ml#1141, ml#1154, ml#1155). Set the header from `date -u`. A second PR on the same UTC day is fine:
   the workflow passes a header already equal to today's UTC date. The failure is specifically a header
   at *yesterday's* UTC date that the PR did not touch.
2. **`strict_required_status_checks_policy: true` on all nine repos** means a PR goes `BEHIND` every
   time `main` moves, and concurrent sessions move it often. Fix with
   `gh api repos/<owner>/<repo>/pulls/<n>/update-branch -X PUT` — server-side, so GitHub signs the merge
   commit and there is no local commit to leave unsigned. This is a **different setting** from the
   removed `update` rule ("Restrict updates", absent on all nine); conflating them wastes a cycle.
3. **A green PR can still be unmergeable: `required_review_thread_resolution` is `true` on all nine
   repos, and an unresolved CodeQL review thread does not appear in the check rollup.** All three of
   this round's PRs sat at `mergeStateStatus=BLOCKED` with **14/14 required checks green**,
   `mergeable=MERGEABLE`, zero required approvals, and zero code-scanning alerts on the PR ref;
   `gh pr merge` refused with *"the base branch policy prohibits the merge"*. The cause was one
   `github-advanced-security` review thread each — an unused-global on a new module, and `unittest`
   imported both `import` and `import from`. Find them with:
   ```bash
   gh api graphql -f query='{repository(owner:"pcalnon",name:"juniper-ml"){pullRequest(number:N){
     reviewThreads(first:20){nodes{isResolved path comments(first:1){nodes{body}}}}}}}' \
     --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false)'
   ```
   Both findings were legitimate, so fix the code rather than resolving the thread — the alert going
   away resolves it. Budget for this: it is invisible to `gh pr checks` and to the waiter in §1, which
   report only status contexts.
4. **Local headless signing does work** (ed25519, no prompt, GitHub reports `verified=true`), so commit
   and push normally on juniper-ml. `util/open_signed_pr.py` is only needed where you have **no
   checkout** — sibling repos from a confined worktree. Item 2's advice is about avoiding a local *merge*
   commit, not about signing being unavailable.
5. **`open_signed_pr.py` uploads WHOLE FILES.** `expectedHeadOid` protects against a concurrent push at
   push time, but if your local copy was read from an older `main` you silently revert anything that
   landed in between. Re-fetch and confirm your clone is at `origin/main` immediately before uploading.
6. **Concurrent sessions merge constantly.** Re-run `gh pr list` right before pushing. `AGENTS.md` and
   the defect register are the two hottest files, and every PR in this round touched at least one.

---

## 6. Method notes that earned their place

- **Mutation-test every guard you add** — it is the only proof a structural gate cannot give you.
  Results this round: the tunable registry's near-match lookup fails **1** named arm
  (`test_probable_typo_is_warned_naming_both_spellings`); an always-true `is_valid_request_id` fails
  **7**. (The throttle's 3-arm figure belongs to the *previous* round; the blank-key filter was verified
  by negative control, not a mutation count.)
- **Your own tests will catch your own bugs — let them.** `dict.fromkeys` hashes *before* filtering, so
  a malformed env value containing an unhashable entry raised `TypeError`.
- **A tuple is not an assertion.** `uuid.UUID(x), "msg"` still *executes* and still raises on a
  malformed value, so it is not inert — but it asserts nothing about the result, and the `assert` form
  it was meant to be was tautological anyway (a `UUID` is always truthy). The real check had to compare
  against an expected value.
- **Scope a claim to what you proved.** "Stdlib-only, so it's importable without fastapi" was false: the
  module's *own* imports are stdlib, but `websocket/__init__.py` imports fastapi eagerly (the lazy PEP
  562 re-export is at the **package root**, a different module). A test asserting the broad claim failed;
  both claim and test were narrowed.
- **Assertions need scoping too.** `assert caplog.records == []` failed on asyncio's own DEBUG record.
  The assertion was right; its scope was not.
- **Verify a correction before applying it.** A marker-strength justification written into a code comment
  was wrong — it blamed a `.strip()` in `settings.py` for a marker scoped to `security.py`. Running the
  negative control, not re-reading the sentence, is what caught it.
- **Assume this document has errors too.** Three independent validators reviewed it before it was
  archived and found real defects, including **two inherited from the predecessor without checking** (a
  worktree that no longer exists; an over-generalised claim about cascor's `_numeric_setting`) and
  several self-introduced. That is the documented density in this lineage. Verify before you rely.

---

## Git status

**This document was written in the session worktree `.claude/worktrees/vast-singing-lecun`** on branch
`fix/obs-request-id-validation` and archived from there. If you are reading it on `main`, it landed.

The **primary checkout** `/home/pcalnon/Development/python/Juniper/juniper-ml` drifts behind
`origin/main` while session worktrees merge — `git pull --ff-only origin main` before the verify block.

Sibling checkouts `juniper-data` (`8fd002b`) and `juniper-cascor` (`7fa2e66`) were at their merged
`main`s with clean trees, which the drift gate needs. Re-pull if time has passed.

**No stale arc worktree remains** — `docs/handoff-api-primer-defect-register` (ml#1095) has already been
cleaned up locally and on the remote. There are ~21 other session worktrees, several locked and owned by
concurrent sessions; **do not sweep blind**.

The primer arc's harnesses are committed and permanent:
`util/ad-hoc/2026-08-13_{fetch_api_specs.bash,assemble_api_primer.py,gen_primer_examples.py,run_primer_examples.py}`
— note the `2026-08-13_*` glob also matches two files from unrelated arcs. Re-run the worked examples
with `python util/ad-hoc/2026-08-13_run_primer_examples.py` (expect `62 passed`) after any API change.
