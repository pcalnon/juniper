# HANDOFF 2026-08-24 — defect register: 38 fixed / 58 open; every LIVE service-core row closed, juniper-data down to R/M/E

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix **and** the register go in one PR — there is no second repo to coordinate.

Successor to [`HANDOFF_2026-08-21_defect-register-data-and-service-core-next.md`](HANDOFF_2026-08-21_defect-register-data-and-service-core-next.md).
**This document was validated by three independent agents before archiving; they found 40+ defects in
the first draft, four of them factual errors copied forward from the predecessor.** Do the same before
you trust the next one.

**Disposition of the predecessor** — read this before assuming any of it still holds:

- Its **§3 per-repo table is superseded** (it read 75 open). Use §3 below.
- Its **§3.1 recommendation** (juniper-data's seven `C` rows) is **done** — all seven closed, and the
  whole `Correctness` class with them.
- Its **§3.2 service-core triage by the register's §4.2 preamble is still the right frame**, and is
  now *resolved*: every row live for any production consumer is closed. See §5.
- Its **§3.3** flagged that `juniper-canopy` and `juniper-cascor-worker` have **zero register rows
  because the primer barely visited them, not because they are clean** — still true, still tracked by
  no document. Carried into §3.4 so it does not vanish again.
- Its **§4** (`raise_on_status` improvement) is still unfiled — carried into §7.
- Its **§5 traps mostly hold, with two corrections**: its item 4 says `--no-auto-fallback` is required
  "while D3 is open" — **D3 has been closed since ml#1202** (see §6.3); and its "absent repo prints
  `0`" tell does **not** reproduce (see §1).
- Its **§6 method notes hold except the B042 / `__reduce__` bullet**, which §8 below corrects.

**All dates UTC.** Throughout, a bare `§N` means **this** document; anything in the register is
written "the register's §N".

---

## 1. Verify starting state

**Run these from your own session worktree, not the shared checkout.** A worktree-isolated session
refuses any command that `cd`s to `/home/pcalnon/Development/python/Juniper/juniper-ml`, so the
predecessor's opening `cd` + `git pull` is rejected outright. Each line below is standalone —
`REG=…` does **not** survive between tool calls, so the path is inlined.

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main    # expect 0 0

grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
grep -c 'status=KNOWN_GAP,' tests/test_service_fork_drift.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
gh pr list --repo pcalnon/juniper-ml --state open
```

**Expected, and why each is conditional:**

- **`FIXED` rows: 38.** Do not treat the number as the invariant — read the register's §2 Status
  paragraph, which states counts in words. `96 − 38 = 58` open. **Note the register's own §5.1
  preamble still says "These twenty-one carry their original IDs" while its table holds 38** — stale
  prose, corrected in this PR; the §2 paragraph is the authority either way.
- **`KNOWN_GAP` prints `0` and exits `1`.** That exit code is grep saying "no matches"; it aborts a
  `set -e` wrapper. Note the **trailing comma** — a bare `grep -c status=KNOWN_GAP` prints `1`,
  matching a docstring sentence rather than a guard row.
- **The drift test reports `8 tests, 0 skipped, OK`** with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`, and
  `OK (skipped=3)` without it — exactly three tests call `_require_cross_repo()`. In `ci.yml` the
  `skipped=3` form is correct, not a bug. **`0 skipped` still does not mean eight live assertions**:
  with zero `KNOWN_GAP` rows, `test_known_gaps_are_still_open_or_get_promoted` iterates an empty set
  and passes vacuously.

**Sibling checkouts.** The drift gate reads **only two** — `_FORK_REPOS = ("juniper-data",
"juniper-cascor")` at `tests/test_service_fork_drift.py:59`. The predecessor told you to pull five
"because the drift gate reads their working trees"; that rationale is wrong for the other three,
though pulling them is still useful for cross-repo greps. Issue these as **separate** commands — a
`for` loop is refused by the worktree guard:

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-data pull --ff-only origin main
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor pull --ff-only origin main
```

**Use `git -C <path> grep`, never a plain `grep -rn`, against a sibling** — but not for the reason
the predecessor gave. Measured: a plain grep on a *missing* checkout prints **nothing** to stdout and
exits **2** (distinct from 1 = no match). The advice stands because `git grep` fails loudly and
scopes to tracked files; the "prints `0`" symptom does not reproduce, so do not watch for it.

---

## 2. What this session closed

Seventeen entries, 21 → 38 fixed. All PRs merged; SHAs given so "merged" is checkable without GitHub.

| Entries | Fix PR | Register PR | Merge SHA(s) |
|---|---|---|---|
| `APD-SVCCORE-008`, `APD-OBS-002` (`py.typed`, **six** packages) | ml#1237 | same PR | `27f91e75` |
| — (orphaned sequence-safety waiver, §6.1) | ml#1243 | — | `f65a3101` |
| `APD-OBS-003`, `APD-OBS-004` | ml#1245 | same PR | `5781b954` |
| `APD-DATA-009` | data#280 | ml#1258 | `12d92c7e` / `f650329d` |
| `APD-DATA-013`, `APD-DATA-014` | data#281 | ml#1266 | `f6791d62` / `c3deb4d2` |
| `APD-DATA-007` | data#282 | ml#1276 | `c5b1d37b` / `8df23e22` |
| `APD-DATA-011`, `APD-DATA-012` | data#283 | ml#1283 | `0d27fab6` / `8630a464` |
| `APD-DATA-010` | data#284 | ml#1290 | `294104fc` / `18760ad2` |
| `APD-SVCCORE-006`, `APD-SVCCORE-014` | ml#1297 | same PR | `adcc396b` |
| `APD-SVCCORE-009`, `APD-SVCCORE-017` | ml#1298 | same PR | `01ab44e1` |
| `APD-SVCCORE-004` | ml#1300 | same PR | `4652afe3` |
| `APD-SVCCORE-007` | ml#1303 | same PR | `32fc9639` |

**Post-merge `main` verification: green everywhere EXCEPT ml#1237.** Its run (`27f91e75`) is
`conclusion: failure`, never re-run — it is one of the five reds described in §6.1, caused by a
waiver someone else's PR had dropped, not by ml#1237's content. juniper-data's five post-merge runs
are all green. Do not read this table as "all green"; §6.1 is the explanation.

**Two PRs from other concurrent sessions landed inside this window and matter to you:**

- **ml#1291** (`d4b78b0`-era, merged 07:52Z) — *main-verify's catch-up base must ratchet on SCREENED,
  not GREEN*. This **supersedes the mechanism** the predecessor and my own first draft described. See
  §6.1.
- **ml#1299** (merged 08:09Z) — *pip-audit audited NOTHING in both jobs — install the extras*.

**Three milestones, each verified rather than asserted:**

- **`juniper-observability` is at zero open rows.**
- **`juniper-data` has no open `Security` or `Correctness` row.** Its remaining 21 are `R`/`M`/`E`.
- **`juniper-service-core`'s entire *live* surface is closed** — §5 has the proof script.

---

## 3. What is left — 58 open

**Re-derive this; do not copy it forward.** An ID appears in both the register's §4 table and (once
fixed) its §5.1 table, so **an ID is FIXED if *any* of its rows carries the marker** — scoring rows
independently reports every fixed entry as open.

| Repository | Open | Severity split |
|---|---:|---|
| `juniper-data` | **21** | R5 M7 E9 |
| `juniper-cascor-client` | **10** | C1 R2 M4 E3 |
| Cross-client / ecosystem (`APD-ECO-*`) | 7 | R3 M3 E1 |
| `juniper-service-core` | 7 | R2 M3 E2 — **all latent, see §5** |
| `juniper-data-client` | 6 | C1 R1 M3 E1 |
| `juniper-recurrence-client` | 4 | R1 M3 — **not its own repo, see §3.4** |
| `juniper-cascor` | 2 | M2 |
| `juniper-ml` (meta) | 1 | M1 |
| **Total** | **58** | **2 `C`**, zero `S` |

### 3.1 The two remaining `C` rows

- **`APD-CCLIENT-001`** — retries `POST`/`DELETE`/`PATCH` with no idempotency key. **Blocked on
  `APD-ECO-001`**: no `Idempotency-Key` mechanism exists anywhere in the stack, zero occurrences.
  Narrowing the retry allow-list without a key leaves the gap ecosystem-wide — one decision, not two
  tasks.
- **`APD-DCLIENT-002`** — public `validate_npz_contract` raises a bare `ValueError`, escaping the
  hierarchy `APD-DCLIENT-001` established. **Recommended first pick**: self-contained, single repo,
  and the contract it must join already exists and is documented.

### 3.2 juniper-data is the largest group but not the most actionable

Nine of its 21 (`-026`–`-033`, plus `-008`) are a coherent REST redesign — RFC 9457 problem details,
`Link` headers, `Content-Location`, ETags, retryability signalling. **They need a decision from Paul
before any is actionable**, and the ask is outstanding. `APD-DATA-017` (`R`, no ETag/conditional
requests) and `APD-DATA-022` (`M`, no `responses={}` in OpenAPI) sit against the same surface and are
probably blocked with them — treat juniper-data's genuinely actionable count as **~10, not 21**,
until that is settled.

**When a decision is made, capture it inline in the register the way this arc already does:** the
`(owner decision, 2026-08-23)` markers on `APD-DATA-011` and `APD-DATA-014` are the format.

### 3.3 Partial closes — three, all marked in their status markers

Do not re-open these; do read their markers before touching adjacent work.

| Entry | What was closed | What remains |
|---|---|---|
| `APD-DATA-013` | The 422 contract is now *owned* by an explicit handler | `detail` shape unification — needs the envelope decision in §3.2 |
| `APD-SVCCORE-006` | 4 of 5 exceptions rebased onto the package base | `UnknownTunableError` excluded **by design** (§8) |
| `APD-SVCCORE-007` | **Disclosure only** — the per-process scope is now documented | The constraint itself stands: four replicas still admit 4× the configured budget |

### 3.4 Two scope facts that are easy to get wrong

- **`juniper-recurrence-client` is NOT a repository.** It is a sub-package of the
  `pcalnon/juniper-recurrence` monorepo at `juniper-recurrence/juniper-recurrence-client/`.
  `gh pr list --repo pcalnon/juniper-recurrence-client` 404s. The register's §4.6 anchors are bare
  and read as though it had its own repo. This matters immediately — `APD-RCLIENT-003` is a cheap win
  (§3.5).
- **`juniper-canopy` and `juniper-cascor-worker` have zero register rows because the primer barely
  visited them, not because they are clean** (the register's §6). They are outside the 58 and outside
  the table above. **An actual audit of those two is un-done work that no document tracks** — it was
  flagged one generation ago and is being carried forward again here rather than dropped.

### 3.5 Cheapest genuine wins

- **`APD-CCLIENT-010`** / **`APD-DCLIENT-007`** — redundant `pass` after a docstring in 8 and 6
  exception classes. Deliberately *not* folded into cclient#123/#124 to keep those diffs reviewable.
- **`APD-RCLIENT-003`** — ships `py.typed` and the `Typing :: Typed` classifier with **no mypy
  config**: it advertises a checked surface nothing checks. Directly adjacent to ml#1237; the pattern
  and tests exist to copy. Mind §3.4 — it lives in the recurrence monorepo.
- **`APD-CASCOR-005`** — read the register's §3 assessment first; it is a re-scoped entry.

---

## 4. What a register PR must touch

The most repeated mechanic in this arc, and the easiest to under-do. Closing an entry means **all
four**:

1. The **§4 table row** — prepend `**FIXED (<pr>)** — ` to the finding text. If the close is partial,
   say so *in the marker* (`**FIXED (ml#1303, disclosure — the constraint itself stands by design)**`),
   not only in §5.1, so a reader who never scrolls there still sees it.
2. The **§3 detail entry**, if the entry has one (only `S`/`C` rows do).
3. A **§5.1 row**: ID, one-line finding, PR link, and verification prose — what was reproduced, what
   was mutation-tested, what was deliberately *not* done.
4. The **§2 Status paragraph** — counts in words, the running ID list, and the "remaining N" figure.
   §1's grep and this paragraph must agree; disagreement is the usual symptom of an under-update.

Commit title convention: `chore(register): close APD-…`. **Open the PR first, then write the register
with the number it actually returned** — I predicted PR numbers twice and was wrong both times.

---

## 5. juniper-service-core: the live surface is closed — verify before continuing there

Its seven remaining rows are **all latent**: `.websocket.*` and `workers/` have no production consumer
at all. The register's §4.2 preamble is the authority. Prove it rather than trusting this document —
run from the repo root:

```python
import pathlib, re
fixed = set()
for line in pathlib.Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").read_text().split("\n"):
    m = re.match(r"\| APD-SVCCORE-(\d+)", line)          # note: bare \d+, no letter-suffix support
    if m and "**FIXED" in line:
        fixed.add(m.group(1))
for label, group in {
    "live for recurrence": {"004", "007"},
    "live for EVERY consumer": {"006", "008", "009", "014", "017"},
    "latent (no consumer)": {"001", "003", "005", "010", "011", "012", "013", "015", "016"},
}.items():
    print(f"{label:24} open: {sorted(group - fixed) or 'NONE'}")
```

Expected: `NONE`, `NONE`, and seven latent. (The register does use letter-suffixed IDs elsewhere —
`APD-CASCOR-001a`/`-001b` — so widen the regex if you generalise this.)

**Do not fix the latent seven as though they were live exposure.** That guidance has held for three
generations; the register's §2.2 consolidation loop is why they exist at all. They become live if and
when the wider service-core migration lands.

---

## 6. Traps, in the order they will bite you

### 6.1 main-verify's catch-up base — the mechanism CHANGED mid-session

**Read this before diagnosing any red `main-verify`.** Until 2026-08-24 the G3.1 catch-up base
resolved from run-level `status=success`, so a screen *finding* froze the base: every later merge
re-screened a window still containing the offending commit, and each red guaranteed the next. That is
the model the predecessor describes and it is **superseded**.

**ml#1291 (merged 07:52Z, 2026-08-24) changed the base to ratchet on SCREENED, not GREEN** — it now
resolves from a dedicated *"Assert screens reached a verdict"* step, so a finding advances the base
instead of freezing it. Tier order: screened tip → legacy `status=success` → `github.event.before` →
`HEAD^1`.

**Its live hazard, which you inherit:** the tier-1 resolver keys on an **exact step name**. Rename
that step and tier 1 matches nothing, the resolver falls silently through to tier 2, and the old
defect returns **with every check green** — the vacuous-pass class again.

**The immediate cause of this session's five-red streak was different, and is worth knowing anyway:**
a *correct* waiver was silently discarded by squash-merge. ml#1228's branch carried commit
`38df160a` with a valid `Allow-Symbol-Loss:` trailer; the PR merged **without it**, because **squash
composes the merge message from the PR's *first* commit** and the waiver was pushed on top as a
second one. Diagnose with the *merged* commit, never the branch:

```bash
git log -1 --format='%B' <squashed-sha> | grep -c 'Allow-Symbol-Loss'   # 0 => orphaned; note: exits 1
git branch -a --contains <waiver-sha>                                    # only meaningful in a clone that still has the branch
```

Fixed by ml#1243. **Verify a waiver locally before merging** — `juniper-symbol-loss-check --base
<last-green-tip> --head HEAD` prints `by_verdict={'WAIVED': 1}` and exits 0 when the trailer is really
seen. Do not infer it from the trailer appearing in `git log`.

**Careful with prose:** the parser is `^\s*Allow-Symbol-Loss:\s*(.+?)$` with `MULTILINE` — it anchors
to **line start**, not to trailer position. A line that *begins* with the bare token **is parsed as a
declaration**, even mid-paragraph and even indented. Only backticked or mid-sentence mentions are
safe. (My first draft claimed prose is never parsed; that is wrong.)

### 6.2 A green PR can still be unmergeable

`required_review_thread_resolution` is `true` fleet-wide and an unresolved CodeQL review thread **does
not appear in the check rollup**. Fired twice this session — `mergeState=BLOCKED` at 21/21 and 17/17
green (those are the two repos' required-context counts: juniper-data 21, juniper-ml 17).

```bash
gh api graphql -f query='{repository(owner:"pcalnon",name:"<REPO>"){pullRequest(number:<N>){
  reviewThreads(first:20){nodes{isResolved path comments(first:1){nodes{body}}}}}}}' \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false)'
```

**Fix the code, don't resolve the thread** — the alert going away resolves it and `mergeState` moves
`BLOCKED` → `CLEAN` on its own. Both instances were cheap: `py/overly-permissive-file` on a `0o644`
lock file (→ `0o600`), and `py/import-and-import-from` from mixing `import juniper_service_core` with
`from juniper_service_core…` in one test file (→ `importlib.import_module`; the obvious
`from … import X as x` workaround then trips ruff **N813**).

### 6.3 Waiting and merging

- **Never hand-roll a poll loop.** `python3 util/wait_for_checks.py --pr <n> [--repo <r>]` anchors on
  the ruleset's *required* contexts. Its **exit 2 is not always "wait longer"**: it distinguishes
  still-running from never-reported and prints a **STALLED** verdict when a required check already
  failed and the unreported ones are downstream `needs:` jobs that will never report.
- **Merge with `util/safe_merge.py --execute --no-auto-fallback`.** Direct pushes to `main` are
  blocked on all nine repos. **`--no-auto-fallback` is for the D4 residual, not D3** — the predecessor
  says "while D3 is open" and that is stale: D3 (disarm on refusal) shipped in ml#1202, and
  `disarm_auto_merge()` now wraps every refusal path (`util/safe_merge.py:505`, `:628-660`). D4 is the
  reason to keep the flag: once armed, the net merges whatever head is current.
- safe_merge syncs a `BEHIND` PR and re-waits on the **new** head; it did that on five PRs this
  session. **A GitHub network timeout mid-merge is not a failed merge** — it happened twice; check
  `gh pr view <n> --json state,mergedAt` before retrying.
- **Concurrent sessions merge constantly.** Re-run `gh pr list` immediately before pushing. The
  register and `AGENTS.md` are the hottest files, and this arc's PRs interleaved minute-by-minute with
  other sessions' all day.

### 6.4 The install can silently resolve to the wrong tree

juniper-data's editable install resolves to the **main checkout**, so a worktree fix is **not
exercised** unless you run with `PYTHONPATH=<worktree>`. My first `APD-DATA-007` reproduction ran
against unpatched code because of this. Verify with the **absolute** worktree path — `PYTHONPATH=.`
run from the wrong directory prints the main checkout and exits 0, which is indistinguishable from
success:

```bash
cd <your juniper-data worktree> && PYTHONPATH="$PWD" python -c "import juniper_data; print(juniper_data.__file__)"
```

Same class in service-core, with a twist worth knowing: the tree declares **0.5.1**, pip's metadata
says **0.5.0**, and the installed package's own `__version__` attribute says **0.4.0** — all three
disagree. `test_smoke` asserts the *attribute*, so it fails locally. Pre-existing and environmental;
run with `PYTHONPATH=<worktree>/juniper-service-core`. CI installs fresh and is unaffected.

### 6.5 Per-repo conventions that fail rather than warn

- **juniper-service-core** sets `--strict-markers` with no `markers` registration, so a habitual
  `@pytest.mark.unit` **fails** the run. Its `[Unreleased]` CHANGELOG section already has `### Fixed`
  and `### Added` — a second trips markdownlint **MD024**; add to the existing one.
- **`AGENTS.md`'s UTC date check applies to juniper-ml too**, not just juniper-data — both carry
  `agents-md-touch-up.yml`. Touching `AGENTS.md` requires the `**Last Updated**` bump to today's
  **UTC** date (`date -u +%Y-%m-%d`).
- **juniper-data**: `Slow Tests` is `schedule`/`workflow_dispatch` only — SKIPPED on every PR is
  correct, not a masked gap. Five `Cursor Automation: *` checks report NEUTRAL and make
  `mergeStateStatus` read `UNSTABLE` while nothing is wrong. `delete_branch_on_merge` is **false**
  here (true on juniper-ml), so delete fork branches yourself.
- **Local linter version skew is common — reproduce on pristine `main` before believing a failure is
  yours.** juniper-recurrence pins ruff v0.15.18 (accepts `line-length = 512`); a locally available
  0.15.9 caps it at 320 and refuses to run. Fall back to `ruff check --isolated`.
- **The drift registry has an `ordered` site kind.** `cors-outside-auth` regresses by two
  `add_middleware` calls **swapping places**, so a presence-only check reports SUCCESS on the exact
  defect it guards. `test_enforced_guards_are_present_in_every_fork` re-implements matching inline
  rather than calling `guard_is_present()` — extend both or the gate stays green on a reorder.
- **PR conventions**: `.github/pull_request_template.md` carries a `## Requirements` JR-ID section —
  fill it or delete it, and **do not invent an ID** (there is no `PKG` area; verify against
  `notes/requirements/by-area/`). `required_signatures` is fleet-wide; `util/open_signed_pr.py` exists.

---

## 7. Unfiled / owed work

None of these has a register entry. They will be lost unless carried.

- **`raise_on_status=False` in juniper-data-client and juniper-recurrence-client.** Their `Retry` is
  built without it, so an *exhausted* retry reports `status_code=None` instead of the real status.
  **Not `APD-CCLIENT-002` repeated** — neither has a dead branch, because their generic `else` arm
  handles 5xx. A fidelity improvement, not a defect. **If you act on it**, you must also revisit
  data-client's `test_not_found_and_generic_errors_also_carry_status`, whose docstring documents that
  503 never reaches the response branch and which deliberately uses **409**.
- **juniper-data-client's redundant `__reduce__`.** `exceptions.py:56` carries an override justified
  by a claim that is false (see §8). Harmless — it reproduces what CPython already does — but correct
  the rationale if you touch that file.
- **The canopy / cascor-worker audit** (§3.4). Genuinely un-done, genuinely untracked.
- **The register's §5.1 preamble** said "These twenty-one" against a 38-row table; corrected in this
  PR. Watch for the same drift as the count grows.

---

## 8. Method notes that earned their place

- **Re-derive the entry's scope; the register is a map, not a specification.** Every round found it
  mis-scoped: `APD-SVCCORE-008`/`APD-OBS-002` were filed as two packages and were **six**;
  `APD-DATA-010` named the mid-stream race but the *likelier* path is an id that never existed;
  `APD-DATA-013`/`-014` were one defect wearing two labels.
- **A test can pin a defect by ASSERTING its value as the contract** — three instances (`-009`'s four
  `201`s, the offset-order assertions, `-010`'s two `namelist()` equalities). **The tell is a test
  whose *name* describes the defect**: "returns zip with found only", "skips missing datasets". When
  the name reads like a description of what goes wrong, check whether it documents or endorses.
- **A concurrency test that does not fail against the unfixed code is not a concurrency test.** My
  first `APD-DATA-007` race test passed with the lock disabled: the barrier released workers as each
  subprocess was *spawned*, but `Popen` returns before the child imports anything, so start-up jitter
  serialised them. Barriers must be **two-phase** — announce readiness after setup, release only once
  every participant has announced.
- **When a structural defect will not reproduce by chance, construct the input.** `APD-DATA-012`
  looked non-reproducible and would have been closed as stale. The right question was not "does the
  order vary by luck" but "does the output depend on input order at all".
- **Mutate in both directions.** `APD-DATA-009`'s revert fails 3 arms and its *over*-application fails
  3 **different** ones; `APD-SVCCORE-004`'s `max(1, int(...))` — the obvious partial repair —
  satisfies "never zero" while still under-reporting every other remainder.
- **The correct output can hide a missing mechanism.** `APD-DATA-013`'s handler is deliberately
  byte-identical to FastAPI's default, so every payload assertion passes with it unregistered.
  Ownership had to be asserted directly. A new route into the vacuous-pass class: not broken
  machinery, but a fix whose success is indistinguishable from its absence by observation alone.
- **A partial signal can be worse than no signal.** `APD-DATA-010`'s tempting fix was a response
  header listing pre-check misses — cheap, and silently incomplete for the exact path the entry names.
- **`__reduce__` on an exception is usually redundant** — this **corrects the predecessor's §6**,
  which says B042 should be answered with an override. CPython's `BaseException.__reduce__` returns
  `(cls, args, self.__dict__)` whenever the instance dict is non-empty, so attributes survive
  pickle/copy automatically as long as `args` matches the constructor's positional parameters. I
  shipped a draft with an override; the mutation run exposed it — removing it changed nothing.
- **A deliberate constraint can outweigh uniformity.** `APD-SVCCORE-006` is 4 of 5 *by design*:
  `websocket/tunables.py` is stdlib-only and standalone, pinned by two tests, one of which loads it by
  file path bypassing the package `__init__`. I tried adding the base, watched that test fail, and
  backed out rather than widening its allowlist.
- **Validate the handoff itself with independent agents.** Three found 40+ defects here, including
  four factual errors copied forward from the predecessor (`D3 is open`, the `grep` tell, the
  catch-up-base model, "all post-merge green"). Linting is not validation.

---

## 9. Git status

Written from the harness-created session worktree
`juniper-ml/.claude/worktrees/serialized-puzzling-pike` on branch
`docs/handoff-defect-register-svccore-live-surface`. **Note this is not CLAUDE.md's mandated
centralized location** (`/home/pcalnon/Development/python/Juniper/worktrees/<repo>--<branch>--<ts>--<sha>`)
— it is created by the harness, not by the setup procedure. For your own task worktrees follow
`notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md` and clean up with
`notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` / `util/worktree_cleanup.bash`.

- **Verified at `juniper-ml` `main` = `32fc9639`** (38 fixed / 58 open). juniper-data `main` =
  `294104fc`, carrying all five of this session's fixes.
- **Working tree at the time of writing**: the only change is this document plus the register's §5.1
  preamble correction — `git status --short` shows nothing else.
- **All juniper-data worktrees removed**, local and remote branches deleted, `git worktree prune` run.
  juniper-data does **not** auto-delete merged branches; juniper-ml does.
- **Other PRs are open on juniper-ml from concurrent sessions** (e.g. the lockfile bot). "Everything
  in this session is merged" refers to this arc's PRs only — do not read an open PR list as
  unfinished work of mine.
- Sibling checkouts left on merged `main` with clean trees. **Re-pull before running the drift gate** —
  other sessions move them.
