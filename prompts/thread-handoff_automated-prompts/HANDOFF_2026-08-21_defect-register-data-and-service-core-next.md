# HANDOFF 2026-08-21 — defect register: 21 fixed / 75 open, every *grouped* defect closed; juniper-data and juniper-service-core are next

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per fork-pair, plus a juniper-ml PR recording it.

Successor to [`HANDOFF_2026-08-18_defect-register-round-3-and-ci-waiter.md`](HANDOFF_2026-08-18_defect-register-round-3-and-ci-waiter.md).

**Disposition of that document** — read this before assuming any of it still holds:

- Its **§2 per-repo table is superseded** (it read 84 open). Use §3 below.
- Its **§1 (`util/wait_for_checks.py`)** is fully live and was used on every PR this session. Its two
  traps are real; a third — **stall detection** — earned its keep and is described in §5 item 2.
- Its **§3 fork-consolidation** discussion still holds and is untouched.
- Its **§4 (closing a `KNOWN_GAP` row)** is still the procedure, and was exercised once more; the
  registry gained an `ordered` marker kind, see §5 item 6.
- Its **§5 traps are all still live.** Item 1 (UTC date) and item 3 (invisible CodeQL thread) both
  fired again this session.

**All dates UTC.** Local and UTC agreed for most of this session; do not rely on that.

Throughout: a bare `§N` means **this** document. References to the register are written "the
register's §N".

---

## 1. Verify starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git pull --ff-only origin main
git rev-list --left-right --count HEAD...origin/main          # expect 0 0
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
grep -c 'status=KNOWN_GAP,' tests/test_service_fork_drift.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest -v tests/test_service_fork_drift.py
gh pr list --repo pcalnon/juniper-ml --state open
```

**Expected, and why each is conditional:**

- **`FIXED` rows: 21.** Do not treat any number as the invariant — read the register's §2 Status
  paragraph, which states the counts in words. `96 − 21 = 75` open.
- **`KNOWN_GAP`: prints `0` and exits `1`.** That exit code is grep saying "no matches", not a
  failure; it aborts a `set -e` wrapper. Note the **trailing comma** — a bare
  `grep -c status=KNOWN_GAP` prints `1`, matching a docstring sentence, not a guard row.
- **The drift test must report `8 tests, 0 skipped, OK`** (was 6 before the `ordered` marker landed).
  Sibling checkouts must be at their merged `main` or the gate reads a stale tree. In `ci.yml` the
  same file legitimately reports **`skipped=3`** — no siblings on disk. That is not a bug.
- **`0 skipped` still does not mean eight live assertions.** With zero `KNOWN_GAP` rows,
  `test_known_gaps_are_still_open_or_get_promoted` iterates an empty set and passes **vacuously**.

**Sibling checkouts to pull** (the drift gate reads their working trees):

```bash
for r in juniper-data juniper-cascor juniper-data-client juniper-cascor-client juniper-recurrence; do
  git -C /home/pcalnon/Development/python/Juniper/$r pull --ff-only origin main
done
```

**Use `git -C <path> grep`, never plain `grep -rn` against a sibling.** A plain grep on a *missing*
checkout writes to stderr and prints `0` to stdout, making "absent repo" and "verified absent"
indistinguishable. `git grep` fails loudly.

---

## 2. What closed, and what it means for what is left

| Round | Entries | PRs | Class retired |
|-------|---------|-----|---------------|
| 4 | `APD-CASCOR-001a`, `-001b`, `APD-DATA-035` † | data#273, cascor#540, ml#1201 | §2.3 copy-drift — closed **and** encoded |
| 5 | `APD-DATA-004` | data#275, ml#1209 | **`Security` — all 7** |
| 6 | `APD-DCLIENT-001`, `-003` | dclient#158, ml#1217 | sibling-drift reference impl |
| 7 | `APD-CCLIENT-004`, `APD-RCLIENT-001` | cclient#123, recurrence#124, ml#1224 | **sibling-package drift** |
| 8 | `APD-CCLIENT-002` | cclient#124, ml#1227 | — |

**The structural work is done, and that changes the economics.** Every round above got leverage from
a *pattern*: one fix ported to a sibling, one gate covering a family. All three of the register's
§2.3 drift groups and the whole `Security` class are now closed. **The remaining 75 have no shared
theme** — each is its own item, so expect roughly linear cost per entry from here and do not spend
time hunting for another family.

---

## 3. What is left — 75 open, and where to start

Per-repo, computed from the register's §4 `FIXED` markers and verified by arithmetic (`96 − 21 = 75`):

| Repository | Open | Register |
|---|---:|---|
| **`juniper-data`** | **28** | §4.1 — largest group, and the recommended start |
| **`juniper-service-core`** | **14** | §4.2 — **read its preamble before triaging anything** |
| `juniper-cascor-client` | 10 | §4.4 |
| Cross-client / ecosystem / meta | 8 | §4.8 |
| `juniper-data-client` | 6 | §4.5 |
| `juniper-recurrence-client` | 4 | §4.6 |
| `juniper-observability` | 3 | §4.7 |
| `juniper-cascor` | 2 | §4.3 |
| **Total** | **75** | zero `S`; 9 open `C` |

### 3.1 `juniper-data` — 28 open (start here)

Severity split: **7 `C`, 5 `R`, 7 `M`, 9 `E`.**

The seven Correctness rows are the highest-value cluster left in the register:

| ID | Finding | Anchor (stale — verify) |
|---|---|---|
| `APD-DATA-007` | Tag update is read-modify-write with **no CAS / version check** | `api/routes/datasets.py:785-794` |
| `APD-DATA-009` | Batch-create returns **201 even when every item failed** | `api/routes/datasets.py:377` |
| `APD-DATA-010` | Batch export **silently skips** datasets deleted mid-stream | `api/routes/datasets.py:570-572` |
| `APD-DATA-011` | Offset pagination **skips and duplicates** under concurrent writes | `storage/local_fs.py:253-255` |
| `APD-DATA-012` | `/filter` tie order non-deterministic (unsorted glob feeds a stable sort) | `storage/base.py:376` |
| `APD-DATA-013` | Two incompatible `detail` shapes — **no `RequestValidationError` handler** | `api/app.py:152-166` |
| `APD-DATA-014` | 400 vs 422 split falls out of **exception-subclass MRO, not design** | `api/routes/datasets.py:106-112` |

**Two of these are plausibly one PR.** `-013` and `-014` are both about the 400/422 error surface in
the same two files, and `-013`'s missing handler is *why* `-014`'s split is accidental. Verify that
before committing to it — this session's repeated lesson is that the register's grouping is a
hypothesis, not a specification (§6).

**`APD-DATA-009` is the cheapest real win**: a batch where every item failed still returns 201.

**Do not start with the nine `E` rows.** `-026` through `-033` are a coherent REST-semantics critique
(RFC 9457 problem details, `Link` headers, `Content-Location`, ETags) that reads as a redesign, not a
defect queue. They need a design decision from Paul before any of them is actionable.

### 3.2 `juniper-service-core` — 14 open (read the preamble first)

Severity split: **5 `R`, 5 `M`, 4 `E`.** No `C`, no `S`.

**The register's §4.2 preamble is the whole triage, and it is not optional.** The package is only
*partially* adopted, and which module an entry lives in decides whether it is live or latent:

| Reachability | Count | IDs |
|---|---:|---|
| **Live in production for `juniper-recurrence`** (its only `.middleware` / `.security` consumer) | 2 | `-004`, `-007` |
| **Latent library defects — `.websocket.*` / `workers/` have _no_ production consumer at all** | 7 | `-001`, `-005`, `-011`, `-012`, `-013`, `-015`, `-016` |
| **Live for every consumer** (package-root + boot checks: `enforce_auth_posture`, `enforce_dependency_floors`, `SettingsBase`, `get_secret`, `TrainingLifecycle`) | 5 | `-006`, `-008`, `-009`, `-014`, `-017` |

Practical reading: **the five package-root rows are the ones with real users today.** `-008`
(no `py.typed`, so every annotation is discarded by consumers' type checkers) is the highest
value-per-effort item in the whole register right now — it is a packaging one-liner plus a test, and
it silently degrades four downstream repos.

`-004` (`Retry-After` truncates toward zero → `Retry-After: 0`, a tight retry loop) is the only
live-in-production `R` row and is small.

**The seven latent ones can wait** — and the register's §2.2 consolidation loop is the reason they
exist. Do not "fix" them as though they were live exposure.

### 3.3 Everything else

- **`juniper-cascor-client` (10)** — `APD-CCLIENT-001` is the only `C` left there (retries
  `POST`/`DELETE`/`PATCH` with no idempotency key — blocked on `APD-ECO-001`, below); the rest are
  `M`/`E`. `APD-CCLIENT-010` (redundant `pass` in 8 exception classes) is trivial and was deliberately
  *not* folded into #123/#124 to keep those diffs reviewable.
- **Cross-client / ecosystem (8)** — `APD-ECO-001` is still the sharpest: **no `Idempotency-Key`
  mechanism exists anywhere in the stack, zero occurrences.** It is the enabling condition for
  `APD-CCLIENT-001` (retries `POST`/`DELETE`/`PATCH` with no idempotency key); fixing the retry
  allow-list without a key leaves the gap ecosystem-wide.
- **`juniper-observability` (3)** — `-002`/`-003`/`-004` are all `M` (`py.typed`, a return
  annotation, two `__all__` lists) and would bundle naturally into one PR, taking that repo to zero.
- **`juniper-canopy` and `juniper-cascor-worker` have no rows because the primer barely visited
  them, not because they are clean** (the register's §6). An actual audit of those two is **un-done
  work no document tracks.**

---

## 4. One unfiled improvement, deliberately not a defect

`juniper-data-client` and `juniper-recurrence-client` construct their `Retry` without
`raise_on_status=False`, so an **exhausted** retry reports `status_code=None` instead of the real
status. This is **not** `APD-CCLIENT-002` repeated: neither has a *dead* branch, because their
generic `else` arm handles 5xx. It is a fidelity improvement, not a defect, and no `†` entry was
filed.

**If you act on it**, you must also revisit `juniper-data-client`'s
`test_not_found_and_generic_errors_also_carry_status`, whose docstring documents that 503 never
reaches the response branch and which deliberately uses **409** instead.

---

## 5. Traps, in the order they will bite you

1. **`AGENTS.md`'s date check runs on UTC** (`date -u +%Y-%m-%d`). It passes if the header equals
   today's UTC date **or** the line changed in this PR. Set it from `date -u`. Not every repo has the
   workflow — `juniper-recurrence` does not.
2. **`util/wait_for_checks.py` exit 2 is not always "wait longer".** It distinguishes *still-running*
   from *never-reported* contexts and prints a **STALLED** verdict when a required check has already
   failed and the unreported ones are downstream (`needs:`) jobs that will never report. That fired on
   dclient#158 with 8 never-reported contexts; without it, "11/19 finished" reads as "still running"
   and you wait out the full timeout.
3. **A green PR can still be unmergeable.** `required_review_thread_resolution` is `true` fleet-wide,
   and an unresolved CodeQL review thread **does not appear in the check rollup**. data#275 sat at
   20/20 green, `mergeable=MERGEABLE`, and `mergeState=BLOCKED`. Find them with:
   ```bash
   gh api graphql -f query='{repository(owner:"pcalnon",name:"REPO"){pullRequest(number:N){
     reviewThreads(first:20){nodes{isResolved path comments(first:1){nodes{body}}}}}}}' \
     --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false)'
   ```
   **Fix the code, don't resolve the thread** — the alert going away resolves it.
4. **Merge with `util/safe_merge.py --execute --no-auto-fallback`.** Direct pushes to `main` are
   blocked on all nine repos. `--no-auto-fallback` is required while **D3 is open** (the auto-merge
   net is never disarmed, so a refusal can still become a merge later —
   `HANDOFF_2026-08-19_safe-merge-defects-and-kill-forensics.md` §2.2). safe_merge syncs a `BEHIND`
   PR and re-waits on the **new** head; it did that on five PRs this session, and on data#275 the head
   moved because another PR landed between push and merge.
5. **Local linter version skew is common — reproduce on pristine `main` before believing a failure is
   yours.** `juniper-recurrence` pins ruff **v0.15.18** (accepts `line-length = 512`); the locally
   available **0.15.9** caps it at 320 and refuses to run at all. Same shape for black (repos pin
   25.1.0; local is 26.1.0). Fall back to `ruff check --isolated`. **Also check the hook's own
   `files:` / `exclude:` scope** — cascor-client's source flake8 excludes `testing/`, so an `F401`
   there is not in CI's scope at all.
6. **The drift registry now has an `ordered` site kind** (`tests/test_service_fork_drift.py`).
   Markers must appear in the declared *sequence*, not merely be present. `cors-outside-auth` needs it
   because that guard regresses by two `add_middleware` calls **swapping places** — every marker stays
   present, so a presence-only check reports SUCCESS on the exact defect it guards. **Order-awareness
   had to be added in two places**: `test_enforced_guards_are_present_in_every_fork` re-implements
   matching inline rather than calling `guard_is_present()`.
7. **`juniper-recurrence-client` is not a repository.** It is a sub-package of the
   `pcalnon/juniper-recurrence` monorepo at `juniper-recurrence-client/juniper_recurrence_client/`.
   `gh pr list --repo pcalnon/juniper-recurrence-client` 404s. The register's §4.6 anchors are bare
   and read as though it had its own repo.
8. **Concurrent sessions merge constantly.** Re-run `gh pr list` right before pushing. The register
   and `AGENTS.md` are the two hottest files.

---

## 6. Method notes that earned their place this session

- **The register is a good map and a poor specification.** In *every* round, the entry was
  mis-scoped, and checking that is what produced the right fix rather than a plausible wrong one:
  - `APD-CASCOR-001b` missed a second symptom (auth-rejected cross-origin requests also carried no
    CORS headers) **and** an unrecorded juniper-data sibling of `-001a`.
  - `APD-DATA-004` was wrong in **both** directions at once — too narrow (single-create leaked
    identically; it is not batch-specific) and too wide (the curated install hints never leaked).
  - `APD-DCLIENT-001` looked like one repo's bug and was three.
  - Both siblings in round 7 carried `APD-DCLIENT-003`, filed only against data-client.
  **Reproduce the defect before fixing it, and audit the whole surface** — for `APD-DATA-004`,
  auditing every `detail=` in the module is what showed only two interpolate exception text and that
  one of them was legitimate client-facing validation feedback.
- **Mutation-test in BOTH directions.** A leak-only suite passes a fix that silently destroys a
  deliberate feature. `APD-DATA-004` needed three tests, not two: reverting the fix fails the two leak
  arms, and forcing redact-everything fails the hint arm. Where an arm passes both ways, say why in
  its docstring — several here are deliberate invariant guards.
- **A test fixture can hide a defect the same way broken machinery can** (new this session,
  `APD-CCLIENT-002`). Every pre-existing test of the dead 503 branch mounted
  `HTTPAdapter(max_retries=0)` first, so the branch **had passing coverage that exercised it under a
  configuration production never uses.** Generalise: when a defect is described as unreachable in
  production, check whether its tests reach it by removing the very mechanism that makes it
  unreachable.
- **Compare a tool's error SET against baseline, not its count.** A shared `**kwargs` dict for typed
  keyword-only args infers `dict[str, object]` and silently abandons `mypy --strict` checking on
  exactly the arguments being added — while leaving the error count unchanged.
- **Update a public test double in the same PR as the contract it doubles**, and verify its status
  codes against the **real service**. cascor validates `input_size` with a pydantic `Field(ge=1)` and
  `resolution` with `Query(ge=, le=)`; FastAPI answers those **422, not 400**. Guessing 400 would have
  baked a wrong contract into a public double.
- **`B042` is right about the concern and wrong about the remedy.** An exception whose `__init__`
  does not forward to `super()` loses its attributes across `pickle`/`copy`, because
  `BaseException.__reduce__` rebuilds from `args`. Fix with a `__reduce__` override; its own advice
  ("take no kwargs") *is* the defect being closed, and forwarding the extras to `super()` makes
  `str(exc)` a tuple repr.
- **A prose comment beginning with `# nosec` is parsed as a directive** and the following words are
  read as bandit test IDs. Keep the marker as a trailing inline comment only.
- **Assume this document has errors.** That is the documented density in this lineage — three
  independent validators found 13 defects in an earlier generation (ml#1126). Verify before relying.

---

## 7. Git status

Written from the session worktree
`juniper-ml/.claude/worktrees/binary-whistling-hopper`, archived from branch
`docs/handoff-defect-register-data-and-svccore`.

- **Everything in this session is merged.** `juniper-ml` `main` is at `9ba8298`
  (`chore(register): close APD-CCLIENT-002`), carrying **21 fixed / 75 open**. The only thing that may
  still be open is the PR archiving *this document*, which changes no code.
- Session PRs, all **merged**, post-merge `main` verification green in every affected repo:
  data#273 `aaf5abc`, data#275 `17d51cc`, cascor#540 `e266d4e`, dclient#158 `225078f`,
  cclient#123 `8a34b3a`, cclient#124 `53aeb72`, recurrence#124 `b28b2891`,
  ml#1201 `b9629de`, ml#1209 `897a110`, ml#1217 `47cafe9`, ml#1224 `7372bc5`.
- **All session worktrees removed**, local and remote branches deleted, `git worktree prune` run in
  each repo. Note: the fork repos do **not** auto-delete merged branches; juniper-ml does.
- Sibling checkouts were left on merged `main` with clean trees. Re-pull before running the drift
  gate — other sessions move them.
