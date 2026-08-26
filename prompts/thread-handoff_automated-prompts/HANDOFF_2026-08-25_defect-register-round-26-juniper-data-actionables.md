# HANDOFF 2026-08-25 — defect register: 57 fixed / 39 open; juniper-data's cheap actionables are closed, what is left there is design-shaped or coupled

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix **and** the register go in one PR.

Successor to [`HANDOFF_2026-08-25_defect-register-round-25-client-tier-sweep.md`](HANDOFF_2026-08-25_defect-register-round-25-client-tier-sweep.md)
— cite this one by its full name. **Validate this document with independent agents before
trusting it**: this draft's three validators (facts/git, register-consistency, amputation lenses,
all prompted to REFUTE) returned **24 findings (4 major / 20 minor, about six of them the same
defect seen through two lenses)** — every one applied before archiving. The classes: two owner
routings that existed only in this lineage and not in the register (§3.1, §5.3), a stale count
inside the register's own Status block (§4), an unexecutable constraint (the T6 caveat had no
check a fresh thread could run — §1), an amputated environment requirement and two amputated
standing rules from the predecessor (§3.2), local clock times labelled UTC, and a merge SHA
written as "pending" after the merge had already landed.

**Disposition of the predecessor.** Its §1 mechanics still hold (standalone commands, the
two-sibling drift-gate scope, the re-derivation script — reproduced below) with **one new caveat on
the cascor sibling pull (§1)**. Its §3 table is superseded by §3 here (it read 42 open). Its §3.2
most-actionable list is **fully consumed** — items 1–3 closed this session; item 4
(`APD-RCLIENT-004`) is turned into a proposal in §3.2 rather than actioned. Its §5 traps all still
stand; §5 below adds this round's. Its §5.3 unfiled ledger is updated in §5.3 below. All dates UTC;
clock times are local CDT (UTC-5) unless marked.
A bare §N means this document — EXCEPT register-anatomy terms ("the §2 Status paragraph", "§2.2",
"§2.3", "the §3 detail entry", "the §4 table row", "a §5.1 row"), which always name sections of the
register.

---

## 1. Verify starting state

Run from your session worktree. Each line is standalone.

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main    # expect 0 0 (0 N once main moves — git pull --ff-only origin main)

grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
grep -c 'status=KNOWN_GAP,' tests/test_service_fork_drift.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
gh pr list --repo pcalnon/juniper-ml --state open
```

**Expected:** `FIXED` rows **57** (the §2 Status paragraph in words is the authority — fifty-seven /
**39 open**); `KNOWN_GAP` prints `0` and exits `1` (grep no-match — aborts a `set -e` wrapper; the
gate is two-sided, so this grep is the only line that tells you the ledger still waives nothing —
the drift run prints `8 tests, OK` at 0 or N gap rows alike); the drift gate reports `8 tests, OK`
(`skipped=3` without the env var is correct).

Sibling pulls (separate commands, never a loop) — only these two feed the drift gate:
`git -C /home/pcalnon/Development/python/Juniper/juniper-data pull --ff-only origin main` and
`git -C /home/pcalnon/Development/python/Juniper/juniper-cascor pull --ff-only origin main`.
**New caveat on the cascor pull**: the "t6 rebaseline" session runs an 8–12 GPU-hour campaign
pinned to ONE cascor SHA and its driver **aborts (exit 3) if the shared cascor PRIMARY checkout's
HEAD moves between its LAUNCH and COMPLETION announcements** (sent as cross-session messages;
its handoff is ml#1371 — **OPEN at write time, so read it with `gh pr diff 1371`**). A fresh
thread never received those messages, so use the durable marker instead: a launch is in force iff
`ls ~/.local/state/juniper-experiments/t6-campaign-*.out` lists a file whose `LAUNCHED pid=` is
still alive and which does not yet contain `CAMPAIGN COMPLETE` (zero such files existed at write
time). If one is in force, **skip the cascor pull** (the drift gate then runs against the pinned
checkout, which is fine) and do no experiment-range (`:8230+`/`:8110+`) or GPU work. This session pulled cascor once
at 18:12 CDT (23:12 UTC; cascor reflog), before any launch, and told that session so.

If the harness worktree refuses `git checkout main` (`'main' is already used by worktree at
…/juniper-ml`), that is normal — cut task branches from `origin/main`
(`git checkout -b <branch> origin/main`) instead.

**Re-derive the open set with a script, not the tables** — an ID is FIXED if *any* of its rows
carries the marker (fixed IDs appear twice: §4 row + §5.1 row):

```python
import pathlib, re
text = pathlib.Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").read_text()
fixed, seen = set(), set()
for line in text.split("\n"):
    m = re.match(r"\| (APD-[A-Z]+-\d+[ab]?) ", line)
    if not m: continue
    seen.add(m.group(1))
    if "**FIXED" in line: fixed.add(m.group(1))
print(len(seen), "rows |", len(fixed), "fixed |", len(seen - fixed), "open")
```

---

## 2. What this session closed

Three register entries across two close cycles (rounds 26.1–26.2 — one register PR per cycle; the
-020/-021 pair shared one). All fix PRs merged and post-merge main-verify verified green on
juniper-data and juniper-ml; both register PRs merged (ml#1377 via native `--auto`, armed only
after both of its fix PRs read MERGED). Merge SHAs make "merged" checkable offline.

| Entry | Fix PR | Register PR | Merge SHAs (fix / register) |
|---|---|---|---|
| `APD-DATA-015` (route-order guard: four pins over `APIRouter.routes`, test-only) | data#288 | ml#1374 | `a8c40ae8` / `1ac6e767` |
| `APD-DATA-020` (`/v1` spelled once as `API_PREFIX`; eight sites not five; AST call-site pin) | data#289 | ml#1377 | `78bf61c1` / `1291e839` |
| `APD-DATA-021` (`DatasetListFilter` deleted after a measured OpenAPI probe; `/filter` contract pinned; `Allow-Symbol-Loss: class:DatasetListFilter` trailer survived the squash) | data#290 | ml#1377 | `b4db8f61` / `1291e839` |

**Milestones and shape:**

- **juniper-data's cheap actionables are gone.** Its 18 open rows are the 11 this handoff lineage
  routes to the REST-redesign decision plus 7 that are design-shaped or coupled (§3).
- **Every close this round was a *measure-first* close**: -021's remedy flipped from "wire the model"
  to "delete it" because a probe showed wiring drops `tags` from the wire contract; -020's census
  found eight literal sites where the register said five; -015's guard had to be rewritten once
  FastAPI 0.137's route table turned out not to flatten included routers.
- **Every pin is a call-site or structural pin, mutation-checked before the claim was written** —
  six mutations over three passes: -020 and -021 each fail only the targeted pin; -015's hoist
  fails the generic + named pair by design and its delete only the named pin. The -021 evidence scripts are
  retained under `util/ad-hoc/apd_data_021_{openapi_probe,mutation_check}.py` (ad-hoc retention
  policy, owner decision 2026-08-25).

---

## 3. What is left — 39 open, none of it cheap

Re-derived by the §1 script; per-repo splits re-derived the same way.

| Repository | Open | Note |
|---|---:|---|
| `juniper-data` | 18 | 11 routed to the REST-redesign decision by the handoff lineage (`-026`–`-033`, `-008`, `-017`, `-022` — see §3.1 for what the register itself records); remainder: `-005` (securitySchemes) + `-024` (openapi.json deletion) — coupled, see §3.2; `-016` (streaming materialises); `-018`/`-019` (async-job / pagination design); `-023` (operation_id); `-025` (content-type split) |
| Cross-client `APD-ECO-*` | 7 | decision-shaped; `-001` unlocks `CCLIENT-001`; `-004` now also owns the `RCLIENT-004` proposal (§3.2 — handoff routing, not yet recorded in the register); `-007` carries `CCLIENT-012`'s removal-date half (recorded in place) |
| `juniper-service-core` | 7 | **all latent** (`.websocket.*` / `workers/`, no consumer) — still do not fix as live |
| `juniper-cascor-client` | 2 | `-001` (blocked on `APD-ECO-001`), `-008` (envelope sniffing — design-shaped) |
| `juniper-rclient` | 2 | `-004` (proposal in §3.2), `-005` (three-name identity — owner-flavored, Low conf) |
| `juniper-cascor` | 2 | `-003` (response_model on 46 routes — large); `-005` **owner decision** (primer self-contradiction, unchanged) |
| `juniper-ml` | 1 | `-001` — primer-flagged as judgement |
| `juniper-data-client` | 0 | swept |
| `juniper-observability` | 0 | swept (4/4 FIXED) |

### 3.1 Parked on Paul's decisions — unchanged, do not action unilaterally

`APD-CASCOR-005`; the juniper-data REST group — **an owner routing carried by this handoff lineage,
not recorded in the register**: the register ties only `-026`–`-033` together (via `APD-DATA-013`'s
marker), and `-008`/`-017`/`-022` are grouped by lineage alone, so cite the predecessor chain, not
the register, for it (§5.3 carries the fix-up); `APD-ECO-001` → `APD-CCLIENT-001` (one decision, not
two tasks); `APD-ECO-007` (owns `CCLIENT-012`'s removal date — recorded in place). Newly routed INTO
the decision set by this handoff (not yet in the register): `APD-ECO-004` now also owns the
`RCLIENT-004` shape question below.

### 3.2 Most actionable next, in order — and what each one actually is

All anchors re-verified against juniper-data `main` = `b4db8f6` on 2026-08-25; re-verify again.
Items 1–4 are juniper-data work and **need the JuniperData conda env**
(`/opt/miniforge3/envs/JuniperData/bin/python`; run pytest from the worktree root so
`pythonpath = ["."]` imports the worktree, not the editable install).

1. **`APD-DATA-023`** (M) — no `operation_id=` on any of the 21 route decorators (datasets 16,
   generators 2, health 3; `grep -rn operation_id juniper_data/api/routes/` is empty). FastAPI's
   default id is `<handler>_<path>_<method>`, so explicit ids equal to the handler names **change the
   generated ids once** — acceptable because no generated SDK exists in the ecosystem
   (`juniper-data-client` is hand-written), but say so in the PR. Pin shape: AST over every
   `@router.<method>(...)` call requires an `operation_id=` keyword, plus an OpenAPI uniqueness pin.
   Mechanical; one PR.
2. **`APD-DATA-025`** (M) — `application/zip` on batch-export (`datasets.py:743`) vs
   `application/octet-stream` on the artifact download (`:861`). Either direction is a wire change:
   read `juniper-data-client`'s response handling before choosing (NPZ *is* a zip container, so
   `application/zip` on both is defensible; so is octet-stream on both). Propose in the PR, don't
   just pick.
3. **`APD-DATA-005` + `-024` together** (M+M) — `api_key_header` (`api/security.py:29`) is defined
   and referenced nowhere, and `openapi_url` is `None` whenever any API key is configured
   (`api/app.py`, `docs_enabled = not settings.api_keys`), so `securitySchemes` would be invisible
   exactly where it matters. The -024 half is an owner decision (serve `/openapi.json` behind
   auth?); -005 alone is a no-op. Bring them to Paul as one question.
4. **`APD-DATA-016`** (R) — `download_artifact` (`datasets.py:836-863`) calls
   `store.get_artifact_bytes` (whole body) and wraps `io.BytesIO(...)` in a `StreamingResponse`.
   True streaming needs a chunk-yielding method on the `DatasetStore` ABC across all **seven**
   backends (local_fs can stream a file; memory, redis, postgres, cached, hf_store and kaggle_store
   would fake it) — design-shaped, not a quick close.
5. **`APD-RCLIENT-004` — proposal, not a task.** The recurrence client returns `dict[str, Any]`
   while its same-repo server declares pydantic models (`juniper_recurrence/schemas.py`;
   `client.py` `_parse_json` is where the `dict[str, Any]` return type is deliberate — read its
   docstring). The client's only dependency is `requests`: importing the server's schemas would make
   it depend on the `juniper-recurrence` app distribution (fastapi et al.) and on pydantic at
   import time. The shape that fits is client-side `TypedDict`s **held to the server models by a
   keys-equality drift test** (the monorepo makes that test possible). But it is one decision
   across three clients (`APD-ECO-004`, 45+ methods) — put it to Paul as a proposal; a register
   touch on both rows is owed if he accepts. If it is actioned, the predecessor's standing rules
   bind: an AST census over all 7 repos before any signature boundary moves, and every fake mirrors
   its real signature under an `inspect.signature` parity pin.

### 3.3 Carried scope facts

- `juniper-recurrence-client` lives in the **`pcalnon/juniper-recurrence` monorepo**.
- **`juniper-canopy` and `juniper-cascor-worker` still have zero register rows because the primer
  barely visited them.** Carried a fifth time so it does not vanish.

---

## 4. The register-PR protocol (unchanged — reference)

Four touches per close: the §4 table row (`**FIXED (<pr>)** — ` prefix; partial closes qualified
*in the marker*), the §3 detail entry if the ID has one (`grep -n '### APD-<ID>'` — none of this
round's three had one, but do not skip the check), a §5.1 verification row, and the §2 Status
paragraph (counts in words + the running ID list + "leaving N open" — **and the sentence two lines
below it, which still reads "the remaining 58 are `C`/`R`/`M`/`E`", stale since ml#1303; reword it
to "every remaining open row is `C`/`R`/`M`/`E`" in the next register PR**). Counts-must-agree: this
document's §1 grep, the re-derivation script, and the paragraph — all three, every close. Check
whether your ID appears in the register's §2.2/§2.3 tables too (a fifth touch). Commit title
`chore(register): close APD-…`.
**Open the fix PR first, then write the register with the number it actually returned.** Merge
order: fix PR merged and VERIFIED (`gh pr view --json state,mergeCommit`, never safe_merge's exit
code), then arm the register PR (`gh pr merge --squash --auto --subject … --body …`, verify
`state=OPEN armed=true`). The register is the hottest file in juniper-ml — `git fetch` +
`gh pr list` immediately before pushing, and rebase onto `origin/main` right before the push.

---

## 5. Traps — this round's additions, in the order they will bite

### 5.1 A local mutation check lies three ways — stale `.pyc`, `git checkout --`, piped exit codes

Restoring a mutated file with `cp`/`sed -i`/`mv` inside the same second leaves a `.pyc` compiled
from the MUTATED source that still validates (mtime seconds + size unchanged): the file read `v1`
while the import yielded `'v2'`, and the full suite failed 121 tests for no visible reason. Run
mutation passes with `PYTHONDONTWRITEBYTECODE=1` (or `rm __pycache__/<mod>*.pyc && touch`).
`git checkout -- <file>` is not "undo the mutation" — on a file carrying uncommitted real edits it
wipes them (lost and re-applied the -020 edits). And `pytest … | grep …` exits with grep's status:
the background harness reported that 121-failure run as "exit code 0". Read the summary line. The
retained `util/ad-hoc/apd_data_021_mutation_check.py` is the safe shape (copy-restore in
`finally`, subprocess pytest, bytecode off). Memory: `reference_mutation_check_stale_pyc_and_piped_exit`.

### 5.2 FastAPI 0.137 no longer flattens included routers into `app.routes`

`app.routes` holds opaque `_IncludedRouter` nodes (`path=None`, `methods=None`); a route walk over
it sees only the four docs routes and passes vacuously. Note the version split: the local
JuniperData env has 0.137.0 while juniper-data's `requirements.lock` pins 0.141.1, so local and CI
can run different FastAPI releases — one more reason the guards read only public, version-stable
surfaces. Read the public, version-stable
`APIRouter.routes` — that list is exactly what `_IncludedRouter._match` iterates — and compile
patterns with Starlette's public `compile_path`, not the route's private `path_regex`. The -015
guard's mount pin (`app.openapi()["paths"]`) is how it proves the routers under test are the ones
the app serves.

### 5.3 The unfiled-work ledger (predecessor §5.3, updated)

- **CARRIED**: `raise_on_status=False` for data-client / recurrence-client (see the register's §4.4
  sibling note); the canopy / cascor-worker audit (§3.3, fifth carry); the cascor-client WS stream
  classes' `rstrip("/")`-only base-URL treatment (recorded in `APD-CCLIENT-005`'s §5.1 row); the
  recurrence app + model packages' unchecked `py.typed` (recorded in `APD-RCLIENT-003`'s §5.1 row);
  the cascor-client **fake-vs-server validation divergence** (`FakeCascorClient.create_network`
  stricter than production; recorded with `CCLIENT-011`); **MEMORY.md compaction** — still
  deferred, but no longer blocked on the runway arc: ml#1329 (memory-index linter) and ml#1322
  (`docs/memory-index-runway-analysis`) both MERGED on 2026-08-25 (20:39Z / 21:02Z).
- **CARRIED — the 08-21 stale cascor-client worktree** (`fix/503-branch-unreachable`, PR#124 MERGED)
  is still present; cleanup needs Paul's signal.
- **NEW — other sessions' worktrees seen today, do not touch**: cascor-client
  `feat/memory-budget-gate` (18:26) and juniper-data `feat/memory-budget-gate` (18:52) — the
  memory-budget-gate rollout, not this arc.
- **NEW — the T6 constraint** (§1): between the "t6 rebaseline" session's LAUNCH and COMPLETION
  announcements, no cascor-primary pull/commit/dirty tree and no experiment-range/GPU work. Its
  window may open the evening of 08-25 or ~05:10–07:45 on 08-26; pin candidate `d2d1069`.
- **NEW — -020's census note**: the register said five `/v1` sites; the live count was eight (the
  three `EXEMPT_PATHS` health entries post-date the primer). Recorded in the §5.1 row; the AST pin
  now owns all of them.
- **NEW — two register fix-ups for the next register PR** (found by this handoff's validators):
  the §2 Status block's "the remaining 58 are `C`/`R`/`M`/`E`" sentence is stale (see §4); and the
  two owner routings this lineage relies on — the juniper-data REST group (`-026`–`-033`, `-008`,
  `-017`, `-022`) and `APD-ECO-004` ↔ `APD-RCLIENT-004` — exist only in handoffs. Record them in the
  register (a §4.1 / §4.6 note in the style of the `APD-DATA-005` cross-reference note) so they
  survive the handoff chain not being read.

### 5.4 Native auto-merge does not self-update a BEHIND branch on juniper-ml — use the update-branch API

ml#1374 sat green-but-`BEHIND` after `main` moved; the armed net did nothing. `gh api
repos/pcalnon/juniper-ml/pulls/<N>/update-branch -X PUT` re-ran CI on the fresh head and the net
fired minutes later. Never force-push to fix this (the CI-skip/force-push traps in the resident
hazards still apply).

### 5.5 The waiter's `mergeState=UNSTABLE` was transient, and `safe_merge` was right to proceed

data#290 read `GREEN 21/21 required … mergeState=UNSTABLE` because a non-required context (a Cursor
automation) had not reported yet. `safe_merge --execute` merged it and printed the `MERGED #290 at
…` line; the post-merge `gh pr view` confirmed. Trust only the explicit `MERGED #N at <sha>` line
plus `gh pr view --json state,mergeCommit`; `UNSTABLE` caused by a non-required context is not a
reason to refuse.

### 5.6 The sandbox refuses compound commands aimed at sibling worktrees — write a retained script instead

Heredocs to sibling paths, `for` loops over `gh`, `$(...)` substitutions and `${PIPESTATUS[0]}`
were all refused as "too complex to verify it stays inside the worktree". Plain single `git -C …`
/ `sed -i` / `python -c` calls work; anything richer belongs in `util/ad-hoc/` (retained
provenance, header convention in `util/ad-hoc/README.md`) and is run with one command.

---

## 6. Method notes that earned their place this session

- **Measure before choosing the remedy.** The -021 row asked whether wiring the model changes
  OpenAPI; a 40-line probe answered it decisively (`tags` vanishes; descriptions lost) and flipped
  the close from DRY-by-wiring to delete-and-pin. A register row's *question* is often the whole
  task.
- **Call-site pins are the standard shape for "implicit literal" defects.** A value assertion equal
  to the library default or the constant passes the mutation that deletes the guard (predecessor
  §5.2, twice more this round). AST over the package (`-020`: any string literal starting with
  `/v1`) or over the one call (`-021`: `Query(default=Name, pattern=Name)`) is what actually sees
  the regression; pair it with the runtime check, never replace it.
- **Anti-resurrection + parameter-set pins make a deletion honest**: a dead symbol that comes back
  unwired, or a "helpful" `Depends(model)` that reshapes the wire, both fail loudly.
- **The server route, not the client docstring or a sibling model, is the contract of record** —
  same lesson as `CCLIENT-011`, applied inside the server this time.
- **Retain the evidence scripts.** Ad-hoc policy is now RETAINED-as-provenance; the -021 probe and
  mutation runner shipped in the register PR, so the §5.1 row's claims are re-runnable.

---

## 7. Git status

Written from the harness session worktree `juniper-ml/.claude/worktrees/spicy-frolicking-heron`.
This document is archived from branch `docs/handoff-defect-register-round-26`, cut from
`origin/main` = `1291e839` (ml#1377's merge) after the register branch was deleted; it is the only
working-tree change on that branch. Every task
worktree this session created (juniper-data ×3) has been removed, its local and remote branches
deleted, and `git worktree prune` run; the juniper-data editable install resolves to the primary
checkout (verified after cleanup — the per-cycle rule stands: if it ever resolves elsewhere, run
`pip install -e . --force-reinstall --no-deps` from the primary checkout). Sibling checkouts left on merged, clean `main`: juniper-data `b4db8f6`, juniper-cascor
`d2d1069` (pulled once at ~18:15, before any T6 launch — see §1 caveat; equals that session's pin
candidate). juniper-recurrence, juniper-data-client and
juniper-cascor-client were not touched by this session. Open juniper-ml PRs at last check: the
Cursor-fleet DRAFTs plus five non-draft PRs from concurrent sessions (#1371 T6 handoff, #1373,
#1376, #1379, #1380 — P5 and handoff archives), none of them this session's — re-run `gh pr list`. Concurrent
sessions merged all day — `git fetch` + `gh pr list` before every register push.
