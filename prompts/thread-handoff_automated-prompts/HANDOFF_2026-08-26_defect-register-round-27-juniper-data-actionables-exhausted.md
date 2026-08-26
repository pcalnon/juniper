# HANDOFF 2026-08-26 — defect register: 59 fixed / 37 open; juniper-data's actionables are exhausted — what is left is owner questions, design work, and one large-but-mechanical cascor row

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix **and** the register go in one PR.

Successor to [`HANDOFF_2026-08-25_defect-register-round-26-juniper-data-actionables.md`](HANDOFF_2026-08-25_defect-register-round-26-juniper-data-actionables.md)
— cite this one by its full name. **Validate this document with independent agents before
trusting it**, and run a second round on whatever the first round changes (the correction pass is the
least trustworthy part — memory `feedback_validate_handoff_prompts_independently`). This draft's own
validation results are in §8.

**Disposition of the predecessor.** Its §1 mechanics hold with one deletion and one correction (§1
below): the T6 constraint is **cleared** — the campaign it guarded completed 08:57:44Z on 2026-08-26
(23/23 cells, rc=0, cascor pin `67d7ea3` held) and its session announced completion by name — and the
liveness check it prescribed could never have fired (§9). Its §3.2 items 1–2 are **consumed** (closed
this session); items 3–5 are turned into the owner questions in §3.2 here, word for word, so they can
be put to Paul without re-deriving them. Its §5.3 "two register fix-ups" are **done** (ml#1392) and a
third the validators found (the header date) went with them. Its §5 traps stand; §5 below adds this
round's. All dates UTC; clock times UTC unless marked CDT (UTC-5).
A bare §N means this document — EXCEPT register-anatomy terms ("the §2 Status paragraph", "§2.2",
"§2.3", "the §3 detail entry", "the §4 table row", "a §5.1 row"), which always name sections of the
register.

---

## 0. Remaining work — the complete list, in order

Everything the arc still owes, so nothing has to be re-derived from the sections below (which carry the
detail). "Successor" = the next thread; "Paul" = an owner decision.

1. **Successor, first — validate this document's correction pass (§8).** Round 2 never reported.
2. **Successor — one small register fix-up PR** (`chore(register): wording fix-ups from the round-27
   validators`): (a) the §4.8 note calls `APD-CCLIENT-012` "retired" — it is **FIXED (cclient#137)**;
   only `APD-CCLIENT-003` is retired under the namespace rule; say "…the removal-date half of
   `APD-CCLIENT-012`, whose `auto_pong` deprecation still lacks a removal date"; (b) add a §4.3 note
   recording that `APD-CASCOR-005` is parked as an owner decision (today that routing exists only in
   this handoff lineage — §3.1); (c) optional: the -005/-024/-016 rows' stale anchors (`security.py:26`,
   `app.py:91`/`:97-99`, `datasets.py:693-704` → live `:29`, `:95`/`:103`, `:836-864`) — the arc's
   convention is leave-and-note, and §3.2 carries the live lines, so this is cosmetic.
3. **Paul — three items, verbatim in §3.2 item 3**: Question A (`-005`+`-024`: serve `/openapi.json`
   behind the API key?), Question B (`RCLIENT-004` via `ECO-004`: client-side `TypedDict`s held by a
   drift test?), and for the record the `-025` direction taken. Whichever way A/B go, a register note
   is owed.
4. **Successor — `APD-CASCOR-003` + cascor's unfiled `operation_id` sibling in one pass** (§3.2 item
   1): measure first whether `response_model=` on envelope routes changes the wire; work in a cascor
   task worktree under §1's freeze rule; JuniperCascor1 env; expect round-25 §5.4's CodeQL traps.
5. **Successor — design notes before code**: `APD-DATA-016` (§3.2 item 2), `APD-DATA-018`/`-019`
   (item 4), `APD-CCLIENT-008` (item 5 — a fleet envelope decision, beside the REST group's `-031`).
6. **Paul — the parked decisions (§3.1)**: the eleven-row juniper-data REST group; `APD-ECO-001` →
   `APD-CCLIENT-001`; `APD-ECO-007` (owns `CCLIENT-012`'s removal date); `APD-ECO-004` ↔ `RCLIENT-004`
   (= Question B); `APD-CASCOR-005`; `APD-RCLIENT-005` (three-name identity, Low conf); `APD-ML-001`
   (release-train question first).
7. **Nobody, yet — the seven latent `juniper-service-core` rows** (`.websocket.*` / `workers/`, no
   consumer): do not fix as live.
8. **Carried unfiled ledger (§5.7)**: `raise_on_status=False` for data-/recurrence-client; the
   canopy / cascor-worker audit (sixth carry — those two repos have zero register rows because the
   primer barely visited them); cascor-client WS streams' `rstrip("/")`-only base URL; the recurrence
   app + model packages' unchecked `py.typed`; the cascor-client fake-vs-server divergence; MEMORY.md
   compaction (unblocked); the 08-21 stale cascor-client worktree `fix/503-branch-unreachable`
   (cleanup needs Paul's signal).
9. **Successor — confirm juniper-ml's post-merge main-verify went green on `eef710b7`** (ml#1396; in
   progress at write time — `gh run list --repo pcalnon/juniper-ml --branch main --limit 3`) and that
   the handoff-archive PR for this document merged.
10. **Memory hygiene — done this session, nothing owed**: `project_juniper_defect_register_2026-08-14`
    (round 27 paragraph + description), `feedback_validate_handoff_prompts_independently` (the
    unexecutable-liveness-check class), new `reference_cascor_primary_frozen_while_any_stack_imports_it`,
    and their MEMORY.md index lines.

---

## 1. Verify starting state

Run from your session worktree. Each line is standalone (the sandbox refuses `$(...)`, `${PIPESTATUS}`,
`$'…'` quoting, and heredocs or loops that name a sibling checkout — §5.2; a heredoc that stays inside
the worktree, like the script below, is accepted).

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main    # expect 0 0 (0 N once main moves — git pull --ff-only origin main)

grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
grep -c 'status=KNOWN_GAP,' tests/test_service_fork_drift.py
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
gh pr list --repo pcalnon/juniper-ml --state open
```

**Expected:** `FIXED` rows **59** (the §2 Status paragraph in words is the authority — fifty-nine /
**37 open**); `KNOWN_GAP` prints `0` and exits `1` (grep no-match — aborts a `set -e` wrapper; the
gate is two-sided, so this grep is the only line that tells you the ledger still waives nothing — the
drift run prints `8 tests, OK` at 0 or N gap rows alike); the drift gate reports `8 tests, OK`
(`skipped=3` without the env var is correct). `gh pr list` is a snapshot: at archive time it showed the
Cursor-fleet DRAFTs (`cursor/*` heads, thirteen of #1332–#1346) plus four concurrent-session PRs
(#1393 T6 completion, #1394 backup decisions, #1397 shm live-verify, #1398 P5 measure-growth; #1395
had merged) and this arc's handoff-archive PR; anything non-draft that is not this arc's is a
concurrent session — read it before touching the register.

Sibling pulls (separate commands, never a loop) — only these two feed the drift gate:
`git -C /home/pcalnon/Development/python/Juniper/juniper-data pull --ff-only origin main` and
`git -C /home/pcalnon/Development/python/Juniper/juniper-cascor pull --ff-only origin main`.
**The cascor primary is frozen whenever any live stack imports it — not only during T6.** The T6
campaign completed (08:57:44Z; its session released its hold at 12:30 CDT), but at write time the canopy
E2E P1-wave re-drive stack was live — `uvicorn` on `127.0.0.1:8202` whose `/proc/<pid>/cwd` is
`…/juniper-cascor/src` (the PRIMARY), juniper-data on `:8101`, canopy on `:8051`,
`/tmp/juniper-e2e/*.pid` present — and a second session's census stacks were cycling `:8231`/`:8111`.
The JuniperCascor1 editable finder maps every cascor package to the primary's `src`, so a pull that
changes files, a checkout, a dirty edit, or a `pip install -e` from a cascor task worktree changes what
the live stack's next forkserver child imports. **Executable tell — run before any cascor-primary
pull:** `ss -tlnpH` and look for listeners on `8202`, `8101`, `8051`, `8230`–`8259`, `8110`–`8139`
(if you filter, one port per call — a multi-port filter returns empty with exit 0); for each cascor
pid, `readlink /proc/<pid>/cwd`; `ls /tmp/juniper-e2e/*.pid`. Any hit → skip the cascor pull (the drift
gate runs fine against the current checkout) and do every cascor edit in a task worktree, without
`pip install -e`. This session ran the pull once (~17:52Z) without that check; it was a no-op
("Already up to date"), so nothing changed under the live stack — but the check comes first.
The T6-specific tell for a future campaign: `pgrep -f '2026-08-23_t6_rebaseline_campaign[.]bash'`
(bracket form — the plain pattern matches the harness's own shell wrapper and never returns a true
negative) plus the newest `~/.local/state/juniper-experiments/t6-campaign-*.out` (its first line,
after the `[HH:MM:SSZ]` prefix, names the campaign dir) whose `campaign.jsonl` has no
`complete`/`abort` event.

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

Expected: `96 rows | 59 fixed | 37 open`.

---

## 2. What this session closed

Two register entries, two close cycles (rounds 27.1–27.2, one register PR each). The owner granted
merge approval for every PR in this session's arc at the start ("merge approval granted for all PRs
in this session and work arc"), so each PR was self-merged once its required contexts read green — fix
PR via `util/safe_merge.py --execute` and verified with `gh pr view --json state,mergeCommit`, register
PR via native `gh pr merge --squash --auto` armed only after the fix PR's state read MERGED **and**
juniper-data's post-merge main-verify had come back green (both times). Merge SHAs make "merged"
checkable offline.

| Entry | Fix PR | Register PR | Merge SHAs (fix / register) |
|---|---|---|---|
| `APD-DATA-023` (explicit `operation_id` on all 21 routes; three pin kinds; the handler rename must *survive* the mutation run) | data#292 | ml#1392 | `68f7b5e4` / `326e19f4` |
| `APD-DATA-025` (`application/zip` on both binary routes, spelled once as `BINARY_MEDIA_TYPE`; the wire pin checks the bytes really are a zip) | data#293 | ml#1396 | `ea72870a` / `eef710b7` |

**Milestones and shape:**

- **juniper-data's actionables are exhausted.** Its 16 open rows are the 11 the register itself now
  routes to the REST-redesign decision (§4.1 note, ml#1392), `-005`+`-024` (one owner question, §3.2),
  and `-016`/`-018`/`-019` (design-shaped).
- **ml#1392 also carried the register fix-ups the round-26 validators found**: the §2 Status block's
  "remaining 58 are `C`/`R`/`M`/`E`" sentence is now **count-free** ("every remaining open row is …" —
  a count there went stale on every close); the header `Last Updated` was refreshed (it had read
  2026-08-20 through the thirty register-touching commits after ml#1201 set it, up to ml#1377 —
  23 of them `chore(register)` closes); and the two owner routings that had lived only in the
  handoff chain are recorded in the register — the juniper-data REST group as a §4.1 note, `APD-ECO-004`
  ↔ `APD-RCLIENT-004` as §4.6 + §4.8 notes (with the `ECO-007` ↔ `CCLIENT-012` reciprocal pointer).
- **Every close was measure-first**: -023's "changes the ids once" claim rests on a grep of every
  client repo for generator tooling (none); -025's direction rests on reading the data-client's
  response handling (`response.content`, header never read) and grepping canopy/cascor/worker for
  consumers of the header (none). The -025 fix PR **is the proposal** the predecessor asked for — it
  tables the two alternatives and the one-constant reversal cost.
- **Every pin is a call-site or structural pin, mutation-checked before the claim was written** — seven
  mutations across the two closes, and -023's matrix carries an **expected-survival row** (the handler
  rename fails nothing; that survival is the evidence the decoupling works). Evidence scripts retained
  under `util/ad-hoc/apd_data_023_{add_operation_ids,mutation_check}.py` and
  `util/ad-hoc/apd_data_025_mutation_check.py`.
- CI's juniper-data unit lane is now **1084** tests (1035 at -021 → 1080 after data#291's memory-budget
  tests and -023's five → 1084 after -025's four); write the lane count from CI's own summary line.

---

## 3. What is left — 37 open; nothing is both cheap and unblocked

(Three rows *are* cheap in isolation — `APD-DATA-033`, one missing `Settings` knob; `APD-SVCCORE-012`
and `-013`, docstring/naming — but the first sits inside the owner-routed `-026`–`-033` range and the
other two are latent-module rows the §4.2 preamble says not to treat as live.)

Re-derived by the §1 script; per-repo splits re-derived the same way.

| Repository | Open | Note |
|---|---:|---|
| `juniper-data` | 16 | 11 in the REST-redesign group **now recorded in the register's §4.1 note** (`-026`–`-033`, `-008`, `-017`, `-022`); `-005` + `-024` coupled (§3.2 question A); `-016` (streaming materialises — seven `DatasetStore` backends), `-018`/`-019` (async-job / pagination design) |
| Cross-client `APD-ECO-*` | 7 | decision-shaped; `-001` unlocks `CCLIENT-001`; `-004` owns the `RCLIENT-004` proposal (§3.2 question B — now in the register); `-007` owns `CCLIENT-012`'s removal date (reciprocal pointer now in §4.8) |
| `juniper-service-core` | 7 | **all latent** (`.websocket.*` / `workers/`, no consumer) — still do not fix as live |
| `juniper-cascor` | 2 | `-003` (`response_model` on 46 of 47 routes — large but mechanical, §3.2 item 1); `-005` **owner decision** (primer self-contradiction, unchanged) |
| `juniper-cascor-client` | 2 | `-001` (blocked on `APD-ECO-001`), `-008` (envelope sniffing — design-shaped) |
| `juniper-recurrence-client` | 2 | `-004` (proposal, §3.2 question B), `-005` (three-name identity — owner-flavored, Low conf) |
| `juniper-ml` | 1 | `-001` — primer-flagged as judgement; the register's own note says do not action before the release-train question |
| `juniper-data-client` | 0 | swept |
| `juniper-observability` | 0 | swept (4/4 FIXED) |

### 3.1 Parked on Paul's decisions — unchanged; four of five now recorded in the register

The juniper-data REST group (eleven rows — the §4.1 note says "Treat the eleven as one owner decision;
do not action any of them unilaterally"); `APD-ECO-001` → `APD-CCLIENT-001` (one decision, not two
tasks — `CCLIENT-001`'s §5.1 row says "blocked on `APD-ECO-001`'s owner decision"); `APD-ECO-007`
(owns `CCLIENT-012`'s removal date — §4.4 marker + §4.8 note); `APD-ECO-004` ↔ `APD-RCLIENT-004`
(question B below — §4.6 + §4.8 notes). Cite the register's notes for those four, not the handoff
chain. **`APD-CASCOR-005` is parked by this handoff lineage only** — the register's §3 entry says
"unify the three and decide deliberately" and §6 lists it as a judgement call, but nothing there routes
it to the owner; keep carrying it here (or add a §4.3 note in the next register PR).

### 3.2 Most actionable next, in order — and the owner questions, verbatim

1. **`APD-CASCOR-003`** (M, High) — 46 of 47 cascor routes declare no `response_model` (only
   `health.py:130`); same mechanical shape as -023 but larger, and cascor wraps responses in a
   `{"status","data","meta"}` envelope (`models/common.py` `ResponseEnvelope`, `success_response()`,
   used in ten route files), so a per-route model means generic envelope models, not one-liners.
   Re-verify the anchor first
   (`grep -rn response_model /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/routes/`);
   AST-census the decorators; decide envelope-typing before touching a route; needs the
   **JuniperCascor1** env (`/opt/miniforge3/envs/JuniperCascor1/bin/python`). **Work in a cascor task
   worktree, never the primary (§1's freeze rule), and never `pip install -e` from it** — cascor's
   tests resolve the worktree package over the editable because its `tests/__init__.py` inserts the
   rootdir parent on `sys.path` (recorded in memory `project_cascor_recurrence_cli_experimentation_plan`,
   Waves 3.1/3.3), so run them from the worktree and confirm with a `print(module.__file__)` probe
   before trusting any result. **Do -023's sibling in the same pass**: the census run for this
   handoff found the same `operation_id` absence on all 47 cascor decorators
   (`grep -rn operation_id /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/routes/`
   is empty; census 2+2+1+3+1+3+8+9+15+3 across admin/dataset/decision_boundary/health/history/
   metrics/network/snapshots/training/workers). Unfiled; recorded in `APD-DATA-023`'s §5.1 row
   (ml#1396). The rewrite script `util/ad-hoc/apd_data_023_add_operation_ids.py` names the routes
   directory in one line (`routes_dir = worktree / "juniper_data" / "api" / "routes"`) — adapt it.
   Round 25's §5.4 CodeQL-on-new-test-files traps will bite the new test module: `with` on
   context-manager clients, never `import x` + `from x import`, and an unused import that test-flake8
   misses but CodeQL blocks on.
2. **`APD-DATA-016`** (R) — `download_artifact` (`datasets.py:836-864` on `main` = data#293
   `ea72870a`: decorator 836, body 837-864; the register row's `:693-704` is stale) reads the whole
   body via `store.get_artifact_bytes` and wraps `io.BytesIO(...)` in a `StreamingResponse`. True
   streaming needs a chunk-yielding method on the `DatasetStore` ABC across all **seven** backends
   (`local_fs` can stream a file; `memory`, `redis_store`, `postgres_store`, `cached`, `hf_store`,
   `kaggle_store` would fake it). Design-shaped; write the design note before the code. Items 2 and 4
   and Question A are juniper-data work and need the **JuniperData** env
   (`/opt/miniforge3/envs/JuniperData/bin/python`; run pytest from the worktree root so
   `pythonpath = ["."]` imports the worktree, not the editable install — §5.6).
3. **Owner questions — put these to Paul as written; do not action either unilaterally.** Whichever
   way he answers, a register touch on the rows is owed (a §4.1 / §4.6 note in the style of the
   routing notes — the register has no owner-decision marker, only prose notes).
   - **Question A (`APD-DATA-005` + `-024`, one decision):** `api_key_header` (`api/security.py:29`)
     is defined and referenced nowhere, so the OpenAPI document has no `securitySchemes`; but
     `openapi_url` is `None` whenever any API key is configured (`api/app.py:95`, `:103`), so a
     secured deployment serves **no OpenAPI document at all** and the missing scheme is unobservable
     exactly where it would matter. *Should `/openapi.json` (and the explorers) be served behind the
     API key rather than deleted when keys are configured?* If yes, both rows close in one PR (serve
     the document behind auth; wire `APIKeyHeader` so `securitySchemes` and a `security` requirement
     appear). If no, `-005` alone is a no-op and both rows get a §4.1 note recording the decision.
     (The register's own anchors for these rows — `security.py:26`, `app.py:91`, `:97-99` — predate
     the 08-25 merges; the live lines are the ones quoted here.)
   - **Question B (`APD-RCLIENT-004` via `APD-ECO-004`):** the recurrence client returns
     `dict[str, Any]` while its same-repo server declares pydantic models
     (`juniper-recurrence/juniper-recurrence/juniper_recurrence/schemas.py` — the monorepo nests the
     app under a same-named subdirectory). Its runtime dependencies are `requests` and `urllib3` only, so
     importing the server models would make it depend on the app distribution and on pydantic at
     import time. *Proposal: client-side `TypedDict`s held to the server models by a keys-equality
     drift test (possible because both live in the `pcalnon/juniper-recurrence` monorepo).* It is one
     decision across three clients and 45+ methods. If accepted: an AST census over all seven repos
     before any signature boundary moves, and every fake mirrors its real signature under an
     `inspect.signature` parity pin.
   - **For the record (not a question):** `-025` took the primer's own direction (`application/zip`
     on both binary routes); the fix PR tables the alternatives and the reversal is one constant plus
     the pinned value.
4. **`APD-DATA-018` / `-019`** (R) — async-job pattern and per-page full-population work; design
   notes first, and `-019` likely wants the keyset cursor that `-011` already shipped as its base.
5. **`APD-CCLIENT-008`** (M) — the client sniffs two error envelopes; the fix is a fleet error-envelope
   decision (it belongs beside the REST group's RFC 9457 row `-031`), not a client patch.

### 3.3 Carried scope facts

- `juniper-recurrence-client` lives in the **`pcalnon/juniper-recurrence` monorepo**.
- **`juniper-canopy` and `juniper-cascor-worker` still have zero register rows because the primer
  barely visited them.** Carried a sixth time so it does not vanish.

---

## 4. The register-PR protocol (reference — two refinements this round)

Four touches per close: the §4 table row (`**FIXED (<pr>)** — ` prefix; partial closes qualified
*in the marker*; trim the cell's trailing padding by the marker's width so the row keeps the column's
nominal width — 136 characters in §4.1; seven older closes, `-007`/`-009`–`-014`, never did, so the
column is not perfectly aligned today), the §3 detail entry if the ID has one, a §5.1 verification row
(single-space cells, carrying the lane count — usually last, but a recorded sibling gap may follow it,
as -023's does), and the §2 Status paragraph (counts in words + the running ID list + "leaving N open"
+ "all N are recorded"), plus the header `**Last Updated**`
line whenever the day has changed (it sat at 2026-08-20 through thirty closes because no protocol
named it). **The fifth touch is a whole-file `grep -n 'APD-<ID>'`**, not just the §2.2/§2.3 tables —
IDs also live in prose notes (the §4.1 cross-reference and routing notes, the -026–-033 group at the
-013 §4 marker and the -009/-013 §5.1 rows). Counts-must-agree: this document's §1 grep, the
re-derivation script, and the paragraph — all three, every close. Commit title
`chore(register): close APD-…`. Retained evidence scripts ride in the register PR under the
`util/ad-hoc/README.md` header convention; the PR body carries a `## Requirements` section
(`References JR-ML-QA-001`).
**Open the fix PR first, then write the register with the number it actually returned.** Merge
order: fix PR merged and VERIFIED (`gh pr view --json state,mergeCommit`, never safe_merge's exit
code) **and its post-merge main-verify green** (`gh run list --repo pcalnon/<repo> --branch main
--limit 3`), then arm the register PR (`gh pr merge --squash --auto --subject … --body-file <file>` —
a file under the session scratchpad is accepted by the sandbox) and verify with
`gh pr view <N> --json state,autoMergeRequest` — armed ⇔ `autoMergeRequest` is non-null (nothing
prints `armed=`). **If the armed PR reads `mergeStateStatus=BEHIND`, the net will not fire on its
own**: `gh api repos/pcalnon/juniper-ml/pulls/<N>/update-branch -X PUT` refreshes the head server-side,
CI re-runs, the net fires (ml#1374 last round, ml#1396 this round — behind by ml#1395 within minutes
of arming). The register is the hottest file in juniper-ml — `git fetch` + `gh pr list` immediately
before pushing, and rebase onto `origin/main` right before the push.

---

## 5. Traps — this round's additions, in the order they will bite

Round 26's §5 traps stand, and through it round 25's — the two a successor will meet first: round
25 §5.4 (CodeQL on new test files — `with` on context-manager clients; never `import x` + `from x
import`; an unused import that the relaxed test-flake8 misses; never write the positional-TypeError
arm for a class constructor) and round 25 §5.6 (a silently failed push leaves `gh pr create` saying
"Head sha can't be blank" — read the push output, never `git push … | tail -1`).

### 5.1 `pytest -q` on top of juniper-data's `addopts = ["-q", …]` is `-qq` and suppresses the summary line

The run exits 0 and prints dots, then the warnings block, then nothing — no `N passed` line, so a
`grep 'passed'` reads as "no tests ran". Pass no extra `-q`; read the count from CI's own log if you
need a number (`gh api repos/pcalnon/juniper-data/actions/jobs/<job-id>/logs | grep passed` —
`gh run view --job <id> --log` returned nothing for a passing job).

### 5.2 The sandbox refuses more than sibling loops: `$'…'` quoting and `${PIPESTATUS[0]}` inside the worktree too

`gh pr merge … --body $'line\n\nTrailer'` and `cmd | tail; echo ${PIPESTATUS[0]}` were both refused as
"too complex to verify it stays inside the worktree" even though nothing left it. Use `--body-file`,
run each screen as its own plain command and let the tool's exit status speak, and keep multi-step
logic in a retained `util/ad-hoc/` script.

### 5.3 `_IncludedRouter` nodes have NO `path` / `methods` attribute — a bare read raises

FastAPI 0.137's `app.routes` holds `_IncludedRouter` dataclasses; `route.path` on one is an
`AttributeError`, and only `getattr(route, "path", None)` reads `None` (the predecessor's "`path=None`"
wording). Read `APIRouter.routes` — the pins in `test_route_order_guard.py` / `test_operation_ids.py`
show the shape. Local FastAPI is still 0.137.0 while juniper-data's lock pins 0.141.1.

### 5.4 juniper-data does NOT auto-delete merged branches; juniper-ml does

`gh api repos/pcalnon/juniper-data --jq .delete_branch_on_merge` → `false` (juniper-ml → `true`).
After a data merge, `git -C <worktree> push origin --delete <branch>` before removing the worktree, or
the remote branch outlives the arc.

### 5.5 juniper-data's `AGENTS.md` sits AT its P5 memory-budget ceiling

data#291 measured the ceiling at 43,493 characters and the file is exactly there (`wc -m`). A
route-convention bullet would grow it; the ratchet was advisory in juniper-data at write time, but the
whole point of P5 is that a cut without a ceiling is undone. Put conventions in the test module's
docstring and the CHANGELOG entry. **In flight**: juniper-data#294 (`feat/memory-budget-blocking`, a
concurrent session, OPEN at write time) drops `--advisory` and raises the ceiling to 45,493 (+2,000
slack) — once it lands the gate BLOCKS and a small addition fits; the advice above still holds.

### 5.6 A worktree's `pytest` imports the worktree only because of `pythonpath = ["."]`

The JuniperData editable install resolves to the **primary** checkout
(`/opt/miniforge3/envs/JuniperData/bin/python -c 'import juniper_data; print(juniper_data.__file__)'`
→ `…/juniper-data/juniper_data/__init__.py`, verified after each cleanup). Run pytest from the
worktree root; a `python -c` probe from elsewhere imports the primary. If it ever resolves elsewhere,
run `pip install -e . --force-reinstall --no-deps` from the primary checkout.

### 5.7 The unfiled-work ledger (predecessor §5.3, updated)

- **CARRIED**: `raise_on_status=False` for data-client / recurrence-client (register §4.4 sibling
  note); the canopy / cascor-worker audit (§3.3, sixth carry); the cascor-client WS stream classes'
  `rstrip("/")`-only base-URL treatment (`APD-CCLIENT-005`'s §5.1 row); the recurrence app + model
  packages' unchecked `py.typed` (`APD-RCLIENT-003`'s §5.1 row); the cascor-client fake-vs-server
  validation divergence (`CCLIENT-011`'s row); **MEMORY.md compaction** — still deferred, unblocked
  (ml#1329 + ml#1322 merged 2026-08-25).
- **CARRIED — the 08-21 stale cascor-client worktree** (`fix/503-branch-unreachable`, PR#124 MERGED)
  is still present at `worktrees/juniper-cascor-client--fix--503-branch-unreachable--20260821-1619--8a34b3a1`;
  cleanup needs Paul's signal.
- **DONE this round**: the predecessor's two register fix-ups plus the header date (ml#1392); the
  `ECO-007` ↔ `CCLIENT-012` reciprocal pointer (§4.8 note).
- **Predecessor items resolved by other sessions**: the `feat/memory-budget-gate` worktrees are gone
  (cascor-client#139, data#291 merged); ml#1371 (T6 handoff) merged `56d68a58`; T6 itself is complete
  (ml#1393 — OPEN at write time — carries its results and closing handoff).
- **Other sessions' worktrees seen at write time — do not touch (standing rule)**:
  `feat/memory-budget-blocking` in eight repos (12:36–12:39 CDT; juniper-data's is data#294 — the P5
  BLOCKING promotion, not this arc), and three cascor ones — `fix/569-forkserver-preload-trainer`
  (12:52 CDT), `diag/census-at67d7ea35`, `exp/g4-at67d7ea35` (the census stacks named in §1).
  Re-derive with `git -C <repo> worktree list` before assuming any path exists.
- **NEW — unfiled sibling gap**: cascor's 47 route decorators lack `operation_id` (recorded in
  `APD-DATA-023`'s §5.1 row by ml#1396; §3.2 item 1 folds it into the `APD-CASCOR-003` pass).

---

## 6. Method notes that earned their place this session

- **Measure the blast radius before a wire change, then let the PR be the proposal.** -025's
  direction was defensible only once the client's `response.content` path and the empty consumer greps
  were on the table; the PR then presents alternatives and reversal cost instead of asking a question
  the reader cannot answer.
- **A mutation matrix needs an expected-survival row.** The property -023 exists for is that a handler
  rename changes nothing; a runner that only counts failures cannot show it. Carry an `expect_fail`
  flag per mutation.
- **A declared type has to be true of the payload.** The -025 wire pin opens the bytes
  (`zipfile.is_zipfile`, `np.load`, `.npz` members) — otherwise the fix is a different wrong header.
- **Count-free sentences in living documents.** "The remaining N are …" went stale within a day of
  being written; "every remaining open row is …" cannot.
- **Record owner routings in the artifact of record, not the handoff chain.** Two routings survived
  four handoffs only by being re-typed each time; they are now §4 notes and the handoff cites them.
- **Validate the marker's format, not the check's prose** (§9).

---

## 7. Git status

Written from the harness session worktree `juniper-ml/.claude/worktrees/serene-wiggling-hickey`.
This document is archived from branch `docs/handoff-defect-register-round-27`, cut from
`origin/main` = `eef710b7` (ml#1396's merge); it is the only working-tree change on that branch.
Every task worktree this session created (juniper-data ×2) has been removed, its local and remote
branches deleted, and `git worktree prune` run; the juniper-data editable install resolves to the
primary checkout (verified after each cleanup). Sibling checkouts left on merged, clean `main`:
juniper-data `ea72870a` (data#293), juniper-cascor `67d7ea3` (= `origin/main`; the T6 pin, pulled
after the freeze lifted — up to date). juniper-recurrence, juniper-data-client and juniper-cascor-client
were read but not modified. Open juniper-ml PRs at last check: the Cursor-fleet DRAFTs only — re-run
`gh pr list`. Concurrent sessions were active all day (backup arc ml#1390/#1391 and P5 docs ml#1395
merged; ml#1393, ml#1394, ml#1397, ml#1398 and juniper-data#294 OPEN at archive time) — `git fetch` +
`gh pr list` before every register push. juniper-ml's post-merge main-verify for `eef710b7` was still
in progress at archive time (§0 item 9).

---

## 8. Validation of this document

**Round 1 — three REFUTE-mode lenses on the first draft, every finding applied.** Facts/git: 30
confirmed, 3 refuted (ml#1393 "published" → OPEN; the open-PR snapshot; "twelve" → thirty commits), 3
shifted (data#294 flipping the memory budget to BLOCKING; in-flight cleanup state; seven untrimmed
§4.1 rows), 3 unverifiable (chat-only facts). Register-consistency: 29 confirmed, 5 refuted, all
minor ("none of it cheap"; CASCOR-005 not owner-routed in the register; the §5.1-row "ends with the lane
count" wording; the commit count; the PR snapshot) — plus one wording defect in the register itself
(§0 item 2a). Amputation/executability: **1 critical** (§1 had said the cascor primary was "no longer
frozen" while a canopy E2E stack was live on it — rewritten into the standing rule + tells now in
§1), 2 major (the `pgrep -f` tell matched its own wrapper — bracket form now; the protocol omitted the
header-date touch — §4 now names it), ~14 minor (the JuniperData env requirement, the BEHIND remedy,
round-25's traps, the editable-install remedy, the other-session-worktree rule, a wrong §-pointer,
unrooted grep paths, Question A/B refinements — all applied).

**Round 2 — NOT COMPLETED.** Three fresh agents (facts, executability/safety, consequence/
prioritisation) were launched against the corrected draft with the brief "the fix pass is the least
trustworthy part"; **all three terminated on an API usage-credit error before reporting.** The
corrections in §1 (freeze rule and tells), §3.1, §3.2 items 1–3, §4 (header date, main-verify gate,
BEHIND remedy, body-file), §5 intro, §5.5–§5.7 and §7 are therefore **unvalidated**. The round-2
briefs also asked questions no one has answered: does `response_model=` on cascor's envelope routes
change the wire (measure before choosing — §3.2 item 1); is Question A's "serve `/openapi.json` behind
the key" the only sensible option given that `EXEMPT_PATHS` already lists `/openapi.json` and `/docs`
while `openapi_url` is `None` (the exemption is moot today); is the `-019` → `-011` cursor remark in
§3.2 item 4 right; does the 37-row accounting in §0/§3 miss any row. **Run round 2 first.**

Length: ~5,200 words against the procedure's "~500" (§0's complete list is a fifth of it); lineage-consistent (round 26 was 3,259) and every
predecessor in this arc was archived at this length after validation.

---

## 9. Corrections to the predecessor

Found by three REFUTE-mode validators run over the round-26 handoff before it was trusted (facts/git:
21 confirmed, 3 refuted, 4 shifted; register-consistency: 13 confirmed, 2 refuted; amputation/
executability: 1 critical, 2 major, ~10 minor). Every one below was verified against primary sources
before being acted on; the archived predecessor is otherwise reliable.

1. **CRITICAL — its T6 liveness check was unexecutable, and failed in the unsafe direction.** The
   `t6-campaign-*.out` file never carries `LAUNCHED pid=` (the launcher echoes that to its own stdout
   and redirects only the driver into the file), so a literal reader concluded "no launch in force"
   while a campaign was live (launched 07:51:12Z, pinned `67d7ea3`) — and would have run the cascor
   pull the driver aborts on (exit 3). The campaign has since completed; the durable form of the check
   is in §1 for any successor campaign.
2. **Its T6 exclusion zone was understated**: the peer's own text also held CPU-heavy suites and the
   launching juniper-ml worktree (`dazzling-swimming-stroustrup`) until completion. Moot now; the
   lesson (cross-check a peer constraint against the peer's document) is in the memory file.
3. **Stale pin**: "pin candidate `d2d1069`" / "juniper-cascor `d2d1069`" — the campaign pinned
   `67d7ea3` (cascor#589 landed before launch).
4. "`gh pr diff 1371`" — ml#1371 merged 07:00Z on 2026-08-26 (`56d68a58`); read the archived file.
5. "verify `state=OPEN armed=true`" — nothing prints `armed=`; the executable form is in §4.
6. "The client's only dependency is `requests`" — `requests` **and** `urllib3` (precision only; the
   argument stands).
7. "`_IncludedRouter` nodes (`path=None`, `methods=None`)" — the attributes do not exist (§5.3).
8. The "fifth touch" rule was incomplete (§4), and the fix-up list missed the header date (done).
9. Its §7 snapshot (five non-draft PRs open; two `feat/memory-budget-gate` worktrees) had all been
   resolved by other sessions before this one started — harmless, but do not act on it.
