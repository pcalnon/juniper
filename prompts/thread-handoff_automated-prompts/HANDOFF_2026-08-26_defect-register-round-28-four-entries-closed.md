# HANDOFF 2026-08-26 — defect register round 28: 63 fixed / 33 open; four entries closed, and the "nothing is cheap" claim was false

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix **and** the register go in one PR.

Successor to [`HANDOFF_2026-08-26_defect-register-round-27-juniper-data-actionables-exhausted.md`](HANDOFF_2026-08-26_defect-register-round-27-juniper-data-actionables-exhausted.md)
— cite this one by its full name. **Validate this document with independent agents before trusting
it**, and run a second round on whatever the first round changes (memory
`feedback_validate_handoff_prompts_independently`). This draft's own validation status is in §8.

**Disposition of the predecessor.** Its §0 items 1–5 are **consumed** (§2 below). Its round-2
validation, which §8 recorded as never completed, **was run this session and changed the plan** —
see §9. Its §5 traps stand; §5 here adds this round's. All dates UTC.
A bare §N means this document — EXCEPT register-anatomy terms ("the §2 Status paragraph", "§4.1",
"§4.3", "a §5.1 row"), which always name sections of the register.

---

## 0. Remaining work — the complete list, in order

1. **Successor, first — validate this document (§8).** No round has been run on it.
2. **Successor — confirm ml#1420 merged** (`gh pr view 1420 --repo pcalnon/juniper-ml --json
   state,mergeCommit`). It was armed with auto-merge and all checks green at write time; if it
   reads `BEHIND`, apply `gh api repos/pcalnon/juniper-ml/pulls/1420/update-branch -X PUT`.
3. **Paul — an owner decision this session surfaced and did not take**: cascor and service-core
   carry juniper-data's `APD-DATA-024` `EXEMPT_PATHS` trap (§3.3). It is **latent**, recorded as a
   §4.3 register note, and deliberately **not filed as new `APD-` IDs** because the register's 96
   is a fixed identity. *Should it become `APD-CASCOR-007 †` / `APD-SVCCORE-018 †`, or stay a note?*
4. **Paul — the parked decisions, unchanged** (§3.1): the eleven-row juniper-data REST group;
   `APD-ECO-001` → `APD-CCLIENT-001`; `APD-ECO-007` (owns `CCLIENT-012`'s removal date);
   `APD-ECO-004` ↔ `APD-RCLIENT-004` (**deferred 2026-08-26, recorded in §4.6** — a deferral, not a
   rejection); `APD-CASCOR-005` (now owner-routed **in the register**, §4.3); `APD-RCLIENT-005`;
   `APD-ML-001` (release-train question first).
5. **Successor — the remaining actionable work is design-shaped**, and there is no longer a cheap
   unblocked row (§3.2): `APD-DATA-016` (streaming across seven `DatasetStore` backends),
   `-018`/`-019` (async-job + pagination), `APD-CCLIENT-008` (a fleet error-envelope decision that
   belongs beside the REST group's `-031`). **Write the design note before the code.**
6. **Nobody, yet — the seven latent `juniper-service-core` rows** (`.websocket.*` / `workers/`, no
   consumer): re-verified this session, still latent. Do not fix as live.
7. **Carried unfiled ledger (§5.6)**, including the six worktrees this session created — **cleanup
   needs Paul's explicit signal** (memory `feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15`).

---

## 1. Verify starting state

Run from your session worktree. Each line standalone (§5.1).

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main    # 0 N -> git pull --ff-only origin main

grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
grep -c 'status=KNOWN_GAP,' tests/test_service_fork_drift.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
gh pr list --repo pcalnon/juniper-ml --state open
```

**Expected:** FIXED rows **63** (the §2 Status paragraph in words is the authority — sixty-three /
**33 open**); `KNOWN_GAP` prints `0` and exits `1` (grep no-match — the only line that proves the
ledger still waives nothing; the drift run prints `8 tests, OK` at 0 or N gap rows alike); the drift
gate reports `8 tests, OK` (`skipped=3` without the env var is correct). `gh pr list` at write time
showed only the Cursor-fleet DRAFTs plus ml#1420.

**Re-derive the open set with a script, not the tables** — an ID is FIXED if *any* row carries the
marker (fixed IDs appear twice: §4 row + §5.1 row):

```python
import pathlib, re, collections
text = pathlib.Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").read_text()
fixed, seen = set(), set()
for line in text.split("\n"):
    m = re.match(r"\| (APD-[A-Z]+-\d+[ab]?) ", line)
    if not m: continue
    seen.add(m.group(1))
    if "**FIXED" in line: fixed.add(m.group(1))
print(len(seen), "rows |", len(fixed), "fixed |", len(seen - fixed), "open")
```

Expected: `96 rows | 63 fixed | 33 open`.

**The cascor-primary freeze rule still stands** (round 27 §1) — the primary is frozen whenever any
live stack imports it, because the JuniperCascor1 editable finder maps every cascor package to the
primary's `src`. **Executable tell, verified working this session:**

```bash
ss -tlnpH                                     # bare scan; eyeball the ports
python3 - <<'PY'                              # the decisive check: who holds a cwd in the primary
import os, glob
for p in glob.glob("/proc/[0-9]*"):
    try: cwd = os.readlink(os.path.join(p, "cwd"))
    except OSError: continue
    if "juniper-cascor" in cwd and ".claude/worktrees" not in cwd:
        print(p.rsplit("/",1)[1], cwd)
PY
ls /tmp/juniper-e2e/*.pid
```

At write time: listeners on 8201/8211/8050/8181 with **no process column** (root-owned Docker
port-forwards — the compose stack, which uses image copies, not the checkout), no
`/tmp/juniper-e2e/*.pid`, and the `/proc` scan found only **idle `bash` shells**, no Python. **The
freeze was NOT in force.** Note `ss -tlnpH 'sport = :A or sport = :B'` DOES work (round 27's
"multi-port filter returns empty" claim is false — §9), but `sport = :8230-8259` errors; the range
form is `'( sport >= :8230 && sport <= :8259 )'`.
**You do not need to pull the cascor primary anyway** — cut task worktrees from `origin/main`, which
never touches the primary's working tree, and never `pip install -e` from one.

If the harness worktree refuses `git checkout main`, that is normal — cut task branches from
`origin/main` (`git checkout -b <branch> origin/main`).

---

## 2. What this session closed — four entries, nine PRs, all merged

| Entry | Fix PR(s) | Register PR | Merge SHAs |
|---|---|---|---|
| round-27 validator fix-ups (4 register defects) | — | ml#1406 | `2139b7c2` |
| `APD-ECO-002` retry jitter | dclient#175 / cclient#141 / recurrence#133 | ml#1410 | `20742fd6` / `4041604f` / `359b8b7a`; `1db02637` |
| `APD-DATA-005` + `APD-DATA-024` | data#295 | ml#1418 | `d3c806d0` / `e07e3b96` |
| `APD-CASCOR-003` (**partial**) + unfiled `operation_id` sibling | cascor#593 | ml#1420 (armed) | `d68e6541` |

**Owner decisions taken this session** (put as questions, answered): merge approval re-granted for
this arc — **it does NOT carry across sessions, ask every session**; Question A answered **(a) serve
`/openapi.json` behind the key**; Question B (`RCLIENT-004`/`ECO-004` TypedDicts) **deferred, not
rejected**, with the reason now a §4.6 register note.

**`APD-ECO-002` — the finding that mattered more than the fix.** Round 27 stated that nothing in the
open set was both cheap and unblocked. **That was false.** `APD-ECO-002` sat in a blanket "7
decision-shaped `APD-ECO-*` rows" bucket with **no per-row rationale** — unlike `-001`/`-004`/`-007`,
which have real ones. It was one kwarg per client. *A bucket label is not a rationale: when a group
is parked, check each member was individually assessed.*
Fix: `backoff_jitter=DEFAULT_BACKOFF_JITTER` on all three `Retry` sites. urllib3 applies jitter as an
**ABSOLUTE additive term** (`backoff_value += random.random() * backoff_jitter`), not proportional,
so it is matched to `DEFAULT_BACKOFF_FACTOR` (0.5 in all three). **`backoff_jitter` arrived in
urllib3 2.0.0** (upstream #2952) and all three already pinned `urllib3>=2.0.0` — checked against the
upstream `CHANGES.rst`, because a higher floor would have turned a one-line fix into a fleet
dependency decision. Decisive pin is **behavioural**: 200 sampled backoffs must differ (200 distinct
with jitter, exactly 1 without). recurrence-client had no retry-policy suite; one was created.

**`APD-DATA-005` + `-024` — three options, two of them one keystroke apart.** `EXEMPT_PATHS` already
listed `/docs`, `/openapi.json`, `/redoc`, and `_is_exempt()` is a bare membership test evaluated
*regardless of whether a key was supplied*. So re-enabling `openapi_url` **alone** serves the
document to **everyone** while looking exactly like "behind the key". All three paths removed from
the exempt set. Explorers stay **unmounted** under auth (Swagger UI/ReDoc fetch `/openapi.json` by
XHR with no header and could only 401). Scheme declared **per protected router, not app-wide**, so
the exempt health probes are not documented as needing a key. Unit lane 1084 → **1094**.

**`APD-CASCOR-003` — partial, deliberately.** 47 decorators gained `operation_id`; **44 of 46**
gained `response_model=ResponseEnvelope`. Document-level evidence: the generated OpenAPI carries
**47 operationIds and 44 `$ref: ResponseEnvelope` 200-schemas**. `health_check` + `liveness_probe`
are excluded because they serve the cross-service **API-02 `{status, version, service}`** base
shared with juniper-data and juniper-canopy, and declaring a model there **is** a wire change —
measured: an optional field absent from the 200 body reappears as `"error": null`, because
`response_model_exclude_none` defaults to **False**. `src/tests/unit/api` **2203 passed**.

---

## 3. What is left — 33 open; nothing is both cheap and unblocked (this time it is true)

Re-derived by the §1 script.

| Repository | Open | Note |
|---|---:|---|
| `juniper-data` | 14 | the 11-row REST group (`-026`–`-033`, `-008`, `-017`, `-022`) is **owner-routed in the register** (§4.1 note); `-016`, `-018`, `-019` are design-shaped |
| `juniper-service-core` | 7 | **all latent** (`.websocket.*` / `workers/`, no consumer) — re-verified 2026-08-26 |
| `APD-ECO-*` | 6 | decision-shaped; `-004`'s shape proposal **deferred, recorded §4.6** |
| `juniper-recurrence-client` | 2 | `-004` (deferred with `ECO-004`), `-005` (three-name identity, Low conf) |
| `juniper-cascor-client` | 2 | `-001` (blocked on `APD-ECO-001`), `-008` (envelope sniffing — design-shaped) |
| `juniper-ml` | 1 | `-001` — do not action before the release-train question |
| `juniper-cascor` | 1 | `-005` **owner decision**, now routed *in the register* |
| `juniper-data-client`, `juniper-observability` | 0 | swept |

### 3.1 Parked on Paul — all now recorded in the register, not the handoff chain

That was this arc's method lesson and it is done: the juniper-data REST group (§4.1),
`APD-ECO-004` ↔ `APD-RCLIENT-004` incl. the 2026-08-26 deferral (§4.6), `APD-ECO-007` ↔
`APD-CCLIENT-012` (§4.8), and `APD-CASCOR-005` (§4.3, added ml#1406). **Cite the register's notes,
not this document.**

### 3.2 Most actionable next — all design-shaped

1. **`APD-DATA-016`** (R) — `download_artifact` materialises the whole body; true streaming needs a
   chunk-yielding method on the `DatasetStore` ABC across **seven** backends (`local_fs` can stream;
   `memory`/`redis_store`/`postgres_store`/`cached`/`hf_store`/`kaggle_store` would fake it).
   **JuniperData** env; run pytest from the worktree root (`pythonpath = ["."]`).
2. **`APD-DATA-018` / `-019`** (R) — async-job pattern and per-page full-population. Round 2 judged
   the round-27 claim that `-019` "wants the keyset cursor `-011` already shipped" only **PARTLY**
   right: `filter_datasets` still does a full scan → filter → two sorts → `total = len(filtered)`
   **unconditionally, before** the cursor branch. The cursor changes which slice is returned and
   nothing about the cost that *is* `-019`'s defect.
3. **`APD-CCLIENT-008`** (M) — the client sniffs two error envelopes; the fix is a fleet
   error-envelope decision belonging beside the REST group's RFC 9457 row `-031`.

### 3.3 Carried scope facts

- `juniper-recurrence-client` lives in the **`pcalnon/juniper-recurrence` monorepo**.
- **`juniper-canopy` and `juniper-cascor-worker` still have zero register rows because the primer
  barely visited them.** Seventh carry.
- **NEW — the `EXEMPT_PATHS` sibling gap** (§0 item 3). `juniper-cascor/src/api/middleware.py:16`
  and `juniper-service-core/juniper_service_core/middleware.py:30` both list `/docs`,
  `/openapi.json`, `/redoc`; cascor's `app.py:616-618` gates the docs on `not settings.api_keys`.
  **Latent** — inert while the document is unmounted. Both are **local forks** (each service imports
  only `enforce_auth_posture` from service-core), so this is the §2.3 fork-drift theme. Recorded as
  a §4.3 note; **not filed as IDs** — that is Paul's call.

---

## 4. The register-PR protocol (reference — unchanged, plus one clarification)

Four touches per close: the §4 table row (`**FIXED (<pr>)** — ` prefix; **partial closes qualified
*in the marker*** — `APD-CASCOR-003`'s reads `**FIXED — partial (cascor#593)**` and names what is
left), the §3 detail entry if the ID has one, a §5.1 verification row, and the §2 Status paragraph
(counts **in words** + running ID list + "leaving N open" + "all N are recorded"), plus the header
`**Last Updated**` whenever the day changed. **The fifth touch is a whole-file `grep -n 'APD-<ID>'`**
— IDs also live in prose notes. Counts-must-agree: §1 grep, re-derivation script, and the paragraph,
every close.
**A partial close still counts as FIXED** in all three (the re-derivation script keys on the
marker), so the marker text is the only thing carrying the nuance — write it precisely.
Commit title `chore(register): close APD-…`. Retained evidence scripts ride in the register PR under
the `util/ad-hoc/README.md` header convention; the PR body carries `## Requirements` (`References
JR-ML-QA-001`).
**Open the fix PR first, then write the register with the number it returned.** Merge order: fix PR
merged and VERIFIED (`gh pr view --json state,mergeCommit`, never safe_merge's exit code) **and its
post-merge main-verify green**, then arm the register PR (`gh pr merge --squash --auto`) and verify
via `autoMergeRequest` being non-null. **If it reads `BEHIND`, the net will not fire on its own** —
`gh api repos/pcalnon/juniper-ml/pulls/<N>/update-branch -X PUT` (needed on ml#1410, #1418 **and**
#1420 this round — assume it, do not hope).

---

## 5. Traps — this round's, in the order they will bite

Round 27's §5 traps stand, and through it rounds 25–26's.

### 5.1 The sandbox refuses heredocs and loops that NAME a sibling checkout

A `python3 - <<'PY'` heredoc reading `/home/pcalnon/.../juniper-cascor/...` is refused as "too
complex to verify it stays inside the worktree", as is `for r in a b; do ... done` and
`mkdir -p /tmp/... && cat > ...`. A heredoc that touches only the *current* worktree is fine.
**The remedy is the convention anyway**: put multi-step logic in a `util/ad-hoc/` script and run it
with a plain `python3 util/ad-hoc/x.py <sibling-path>`. That is how every transform, census and
mutation check in this round was run.

### 5.2 A CodeQL review thread blocks the merge while every required check reads green

`safe_merge` **REFUSED** dclient#175 with all contexts green: two unresolved
`py/should-use-with` threads on `try/finally` client construction. Cause: matching the surrounding
suite's older style. **Fix all sibling repos at once, not just the one that complained.** The threads
**auto-resolve as *outdated*** once the code changes — no manual `resolveReviewThread` needed.

### 5.3 That fix becomes a second commit, and squash-merge ships only the FIRST

Memory `feedback_squash_merge_first_commit_only`. A "scratch that" follow-up commit would have been
silently dropped, re-blocking the merge. **Collapse to one commit before merging**:
`git reset --soft <base> && git commit -F - && git push --force-with-lease` (or `--amend` if the fix
is still unstaged). Done on all three ECO-002 branches.

### 5.4 FastAPI INFERS `response_model` from the return annotation

Every `-> dict` handler reports a **non-`None`** `route.response_model` whether or not the decorator
says anything. So "is it declared?" can only be answered from the **decorator source (AST)** — an
identity check against `route.response_model` passes regardless and pins nothing. This cost a
failing test and a rewrite.

### 5.5 A mutation harness that matches only `^FAILED` reports a broken run as a SURVIVAL

A mutation that breaks *import* produces a pytest **collection ERROR** with no `FAILED` line, so the
runner read it as a clean survival — the vacuous-pass class, in my own tooling. Match
`^(?:FAILED|ERROR)` **and** fall back to the process exit status. Also: a mutation whose anchor does
not exist silently does nothing — every script here aborts on a non-applying mutation.

### 5.6 Two more that cost real time

- **`pytest -q` on top of `addopts = ["-q", …]` is `-qq` and suppresses the summary line.** Exit
  code is still right. Bit me twice (juniper-data AND cascor). Pass no extra `-q`; and never end a
  captured run with `| tail -3`, which cut the summary out of a background log entirely.
- **CI-event delay is not a trigger gap.** cascor#593 and ml#1420 showed `total_count: 0` workflow
  runs for ~10 minutes while other PRs got CI normally and GitHub status read operational. They were
  **queued**. The `workflow_dispatch` fired as "recovery" was unnecessary. **Wait before diagnosing.**
  Separately, a transient GitHub **504** cloning juniper-data-client during pip install failed
  data#295's Security Scans and cascaded into the Quality Gate; `gh run rerun --failed` cleared it.

### 5.7 The unfiled-work ledger

- **CARRIED**: `raise_on_status=False` for data-/recurrence-client (§4.4 sibling note); the
  **canopy / cascor-worker audit** (§3.3, seventh carry); the cascor-client WS streams'
  `rstrip("/")`-only base URL; the recurrence app + model packages' unchecked `py.typed`; the
  cascor-client fake-vs-server divergence; **MEMORY.md compaction** (still deferred, unblocked); the
  08-21 stale cascor-client worktree `fix/503-branch-unreachable`.
- **NEW — six worktrees this session created, all with merged PRs**, cleanup pending Paul's signal:
  `juniper-data-client--fix--eco-002-retry-jitter--20260826-1622--a3226826`,
  `juniper-cascor-client--fix--eco-002-retry-jitter--20260826-1622--87464c35`,
  `juniper-recurrence--fix--eco-002-retry-jitter--20260826-1622--a80a7dc9`,
  `juniper-data--fix--apd-data-005-024-openapi-behind-key--20260826-1646--e0b738e6`,
  `juniper-cascor--fix--apd-cascor-003-response-model--20260826-1716--c6cd2f09`.
  **`juniper-data` does NOT auto-delete merged branches** (`delete_branch_on_merge` false; juniper-ml
  true) — `git push origin --delete <branch>` before removing that worktree.
  Memory `reference_worktree_remove_deletes_ignored_files`: `status --porcelain` is blind to ignored
  files; check `--ignored=matching` before removing a cascor worktree.
- **DONE**: the predecessor's §0 items 1–5.

---

## 6. Method notes that earned their place

- **A bucket label is not a rationale.** `APD-ECO-002` was parked in a 7-row group with no per-row
  reason and turned out to be one kwarg per client. When a group is parked, check each member was
  individually assessed.
- **A pin can restate the defect in a new form and pass every other arm.** The first cascor pin
  asserted `operation_id == endpoint.__name__` — re-coupling exactly what the explicit id exists to
  decouple. Only the **expected-survival** row exposes that class.
- **Verify a version floor against the upstream changelog, not memory.** `backoff_jitter` landing in
  urllib3 **2.0.0** is what kept a one-line fix from becoming a fleet dependency decision.
- **Prove it at the artifact the consumer reads.** Route objects said 47/44; generating the OpenAPI
  document and counting `operationId` and `$ref: ResponseEnvelope` is the evidence that matters.
- **Two options that differ by one keystroke need the trap named in the artifact of record**, not
  just avoided in the fix. `APD-DATA-024`'s (b) is now tabled as a trap in §4.1.
- **Check the siblings after every close.** The `EXEMPT_PATHS` gap in cascor and service-core was
  found by asking §6's question one more time.

---

## 7. Git status

Written from the harness worktree `juniper-ml/.claude/worktrees/atomic-weaving-corbato`. This
document is archived from a branch cut off `origin/main`. Nine PRs merged this session (§2);
**ml#1420 was OPEN and armed** at write time. Six task worktrees remain (§5.7) — every branch merged,
cleanup pending Paul's signal. Sibling checkouts were fetched but never pulled or `pip install -e`'d;
the cascor primary was never touched beyond read-only git. Concurrent sessions were active
throughout (canopy E2E, P5, backup arcs) — `git fetch` + `gh pr list` before every register push;
the register is the hottest file in juniper-ml.

---

## 8. Validation of this document

**NOT VALIDATED.** No adversarial round has been run against this draft. Run three REFUTE-mode
lenses before trusting it — facts/git, executability/safety, consequence/prioritisation — and a
second round over whatever the first changes, because the correction pass is historically the least
trustworthy part.

Specific things to attack: the §2 merge SHAs and counts; the §3 per-repo split (re-derive, do not
read); §1's freeze tell (the `/proc` scan is new this round — **run it**); the claim that the
service-core rows are still latent; §3.2's judgement that nothing cheap remains — **round 27 made
that claim and was wrong**, so treat it as the primary target; and whether the `EXEMPT_PATHS` gap is
genuinely latent in both repos rather than live in one.

Length ~2,900 words — lineage-consistent (round 26 was 3,259, round 27 ~5,200).

---

## 9. Corrections to the predecessor

Round 27's own §8 recorded its round 2 as never completed. **It was run this session**, with three
REFUTE-mode lenses, and it changed the plan rather than merely polishing it.

1. **Its central claim was false.** "Nothing is both cheap and unblocked" — `APD-ECO-002` was both,
   and closing it is most of this round. Its three named "cheap in isolation" rows (`-033`,
   `SVCCORE-012`, `-013`) were all correctly parked; the miss was a fourth it never considered.
2. **Question A was mis-framed** — two options where there are three, and the "yes" option as
   written silently produces the open variant (§2). Round 1 of the round-27 validation had not
   caught this either.
3. **Its `-019` → `-011` cursor remark is only PARTLY right** (§3.2 item 2).
4. **`ss` multi-port filters DO work** — round 27's "a multi-port filter returns empty with exit 0"
   is false (verified iproute2-6.16.0). Port *ranges* are what need the compound form (§1).
5. **cascor has no `src/tests/__init__.py`.** Round 27 said the sys.path insertion lives there; it is
   in `src/tests/conftest.py:121-122`. The memory file it inherited this from carried the same error
   and **has been corrected**.
6. Its §4.1 anchor list said `app.py:91`/`:97-99`; the register actually read `:91`, `:99`. Both are
   now refreshed to the live `:95`, `:101-103`.
7. Its §5.5 "data#294 in flight" and §7 open-PR snapshot were all resolved before this session began
   — harmless, but do not act on a snapshot.
8. **Everything else it asserted survived attack.** The facts/git lens returned **zero refutations**
   across ~32 checked claims — every SHA, line number, character count, dash count and timestamp
   reproduced exactly. Round 27 is reliable apart from the above.
