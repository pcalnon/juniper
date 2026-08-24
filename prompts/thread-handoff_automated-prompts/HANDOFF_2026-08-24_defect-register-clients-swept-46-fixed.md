# HANDOFF 2026-08-24 (second of the day) — defect register: 46 fixed / 50 open; the three clients swept, the base-URL drift rows closed, and what is left is mostly decisions

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix **and** the register go in one PR.

Successor to [`HANDOFF_2026-08-24_defect-register-svccore-live-surface-closed.md`](HANDOFF_2026-08-24_defect-register-svccore-live-surface-closed.md)
(ml#1307), written the same day — cite this one by its full name. **Validate this document with
independent agents before trusting it**; its predecessor's three validators found 40+ defects
including four factual errors copied forward, and this draft's three validators returned **27
findings (17 distinct)** — every one applied before archiving, including two of exactly that
copied-forward class.

**Disposition of the predecessor** — all of its §1 mechanics still hold (the worktree-guard command
shapes, the standalone-command rule, the two-sibling drift-gate scope). Its §3 table is superseded by
§3 below (it read 58 open). Its §3.1 recommendation (`APD-DCLIENT-002`) is **done**, as are the
cheap wins its §3.5 listed — *except* `APD-CASCOR-005`, its third bullet, now parked as an owner
decision (§3.1) — plus the register's §2.3 base-URL drift pair. Its §6.1–§6.5 traps all still stand;
§5 below adds five new ones plus the updated unfiled ledger (§5.3). Its §7 had four items: one
closed here (the data-client `__reduce__`), three carried into §5.3 (`raise_on_status`, the
canopy/worker audit, and its item 4 — the register-§5.1-preamble drift-watch, whose correction stuck
and whose watch instruction is now the §4 counts-must-agree discipline), and four items added.

**All dates UTC. A bare §N means this document — EXCEPT the register-anatomy terms** ("the §2 Status
paragraph", "§2.3", "the §3 detail entry", "the §4 table row", "a §5.1 row"), **which always name
sections of the register**, whose structure every close touches.

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

**Expected:** `FIXED` rows **46** (the §2 Status paragraph in words is the authority — it says
forty-six / **50 open**); `KNOWN_GAP` prints `0` and exits `1` (grep no-match — aborts a `set -e`
wrapper); the drift gate reports `8 tests, OK` (`skipped=3` without the env var is correct, not a
bug). Sibling pulls (separate commands, never a loop):
`git -C /home/pcalnon/Development/python/Juniper/juniper-data pull --ff-only origin main` and
`git -C /home/pcalnon/Development/python/Juniper/juniper-cascor pull --ff-only origin main` — only
those two feed the drift gate.

**Re-derive the open set with a script, not the tables** — an ID is FIXED if *any* of its rows
carries the marker. This one-liner is what produced §3 and it agrees with the §2 paragraph:

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

Eight register entries plus two ecosystem sweeps, across six close cycles (rounds 19–24 in the
register-arc numbering — one round per register PR). All PRs merged; merge SHAs given so "merged" is
checkable offline.

| Entries | Fix PR(s) | Register PR | Merge SHA(s) |
|---|---|---|---|
| `APD-DCLIENT-002` (bare `ValueError` escaping the hierarchy — **9 raise sites**, row anchored 1) | data-client#161 | ml#1315 | `d120603f` / `019ed661` |
| `APD-DCLIENT-007` + the redundant `__reduce__` (unrecorded; ordered by `APD-SVCCORE-014`'s row) | data-client#162 | ml#1317 | `595a4b3a` / `77b4112a` |
| `APD-CCLIENT-010` + the ported `__reduce__` (7 `pass` remained of the filed 8) | cascor-client#126 | ml#1321 | `29072bd2` / `581ada0c` |
| `APD-RCLIENT-003` (mypy gate + `_parse_json` Any-laundering) and the third `__reduce__` copy | recurrence#127 + #128 | ml#1327 | `b1ef4201` + `edd5673a` / `1df567c6` |
| `APD-DCLIENT-005` (**9** headers in **4** values, register knew 6/3) / `APD-DCLIENT-006` (`ContractKind` Literal) | data-client#164 | ml#1328 | `7a8ee5af` / `7b15ff7c` |
| `APD-DCLIENT-004` / `APD-CCLIENT-005` (base-URL drift pair) + the case/hostname hardening sweep | data-client#165 + #166, cascor-client#129, recurrence#129 | ml#1331 | `1acd7380` + `1af5be13`, `619012b6`, `f61036d0` / `96ed7307` |

**Milestones:**

- **The `__reduce__` false-rationale is corrected in all four carriers** (service-core, data-client,
  cascor-client, recurrence-client). Every removal proven by deletion-under-test; every deletion
  waived with `Allow-Symbol-Loss: method:<Base>.__reduce__` in the branch's **single** commit, proven
  `WAIVED` locally before push, and verified surviving the squash into main.
- **Both §2.3 base-URL drift rows are closed and struck through in place.** All three clients now
  normalise **and** validate, including two hardenings from a **confirmed Cursor Automation review
  finding** (§5.1). The only sibling-drift row left is idempotency, blocked on `APD-ECO-001`.
- **Post-merge main-verify verified green on all three client repos through the final merges** —
  data-client at `1acd7380` and `1af5be13`, cascor-client at `619012b6`, recurrence at `edd5673a`
  and beyond (validation re-checked the late runs). Re-verify before relying:
  `gh run list --repo pcalnon/<repo> --workflow main-verify.yml --limit 2`.

---

## 3. What is left — 50 open, and most of the cheap ones are gone

Re-derived by the §1 script; severity split by the same method.

| Repository | Open | Split | Note |
|---|---:|---|---|
| `juniper-data` | 21 | R5 M7 E9 | ~9–11 blocked on the REST-redesign decision (`-026`–`-033`, `-008`, probably `-017`/`-022`) |
| `juniper-cascor-client` | 8 | C1 R1 M3 E3 | the `C` is `-001`, blocked on `APD-ECO-001` |
| Cross-client `APD-ECO-*` | 7 | R3 M3 E1 | decision-shaped; `-001` unlocks `CCLIENT-001` |
| `juniper-service-core` | 7 | R2 M3 E2 | **all latent** (`.websocket.*` / `workers/`, no consumer) — still do not fix as live |
| `juniper-rclient` (in the recurrence monorepo) | 3 | R1 M2 | `-002` per-call timeout is the most actionable single item left |
| `juniper-cascor` | 2 | M2 | `-003` (response_model on 46 routes — large); `-005` is an **owner decision** (§3.1) |
| `juniper-data-client` | 1 | E1 | `-008` — kw-only migration, verify call sites first |
| `juniper-ml` | 1 | M1 | `-001`, primer-flagged as judgement |

### 3.1 Parked on Paul's decisions — do not action unilaterally

- **`APD-CASCOR-005`** — the register's §3 assessment shows the *primer contradicts itself* (body
  endorses the `any()` short-circuit at line 1029; appendix Q26 at 9463 demands the full loop).
  Closing it means deciding which behaviour is intended and unifying three copies. The row is `M`,
  Low-confidence, and the register's §6 confidence note lists it among "should be triaged before
  being actioned".
- **The juniper-data REST group** (`-026`–`-033`, `-008`, `-017`, `-022`) — outstanding since the
  08-21 handoff. When decided, record it inline as `(owner decision, YYYY-MM-DD)` per the `-011`/`-014`
  precedent.
- **`APD-ECO-001` → `APD-CCLIENT-001`** — the idempotency mechanism; one decision, not two tasks.

### 3.2 Most actionable next, in order

1. **`APD-RCLIENT-002`** (R) — 30 s scalar timeout with no per-call override on synchronous
   `train`/`crossval`. **The register row's `client.py:217/:311/:405` anchors are DEAD — this
   session's own merges moved the file**; current: `def train` `:383`, `def crossval` `:473`,
   timeout plumbing `:181`/`:201`/`:262`, `DEFAULT_TIMEOUT` `constants.py:47`. Update the row's
   Source cell with the fix. Additive kwarg, clean.
2. **`APD-CCLIENT-006`** (R) — listener fault isolation present at `_dispatch_disconnect` (`:459`,
   per-listener try/except), absent at `_dispatch` (`:453`, one raising listener tears down the
   stream; §2.3 same-file table). Small port, mutation-testable.
3. **`APD-DCLIENT-008`** (E) — 9 positional-or-keyword params on `create_dataset`. Grep every
   consumer call site first; kw-only enforcement is breaking only if someone calls positionally.
4. **The `constants.__all__` completion** (unfiled, §5.3) — one pass + a drift test.

### 3.3 Carried scope facts

- `juniper-recurrence-client` lives in the **`pcalnon/juniper-recurrence` monorepo**. `gh pr list
  --repo pcalnon/juniper-recurrence-client` 404s.
- **`juniper-canopy` and `juniper-cascor-worker` still have zero register rows because the primer
  barely visited them.** Un-done, untracked; carried a third time so it does not vanish.

---

## 4. The register-PR protocol (unchanged — reference)

Four touches per close: the §4 table row (`**FIXED (<pr>)** — ` prefix; partial closes qualified *in
the marker*), the §3 detail entry if the ID has one (**not every ID does, and it is NOT only S/C
rows** — open R and M rows with §3 entries include `APD-SVCCORE-001`, `APD-ECO-001` and
`APD-CASCOR-005`; `grep -n '### APD-<ID>'` the register to check), a §5.1 verification row, and
the §2 Status paragraph (counts in words + the running ID list + "leaving N open"). The §1 grep and
the paragraph must agree. Commit title `chore(register): close APD-…`. **Open the fix PR first, then
write the register with the number it actually returned.** Merge order: fix PR, then register PR.
The register is the hottest file in juniper-ml — `git fetch` + `gh pr list` immediately before
pushing, and rebase onto `origin/main` right before the push.

---

## 5. Traps — six new ones, in the order they will bite

### 5.1 A Cursor Automation review thread blocks a green PR — and it may be RIGHT

cascor-client#129 sat at 19/19 green, `mergeState=BLOCKED`, with an unresolved review thread from the
Cursor fleet. Unlike a CodeQL thread it does **not** auto-resolve when code changes. The flow that
works: read the full comment body via the GraphQL `reviewThreads` query; **evaluate it as a real
review, not noise** — this one was a confirmed finding (below); fix; push; reply with
`addPullRequestReviewThreadReply` (the payload field is `comment` — asking for `thread` errors);
then `resolveReviewThread`.

**The finding itself is a class to check in any URL normaliser:** a case-sensitive
`startswith(("http://", "https://"))` re-prefixes `HTTPS://host` into `http://HTTPS://host` —
`scheme='http'`, `netloc='HTTPS:'` — a silent TLS downgrade that sends `X-API-Key` over HTTP to
hostname `https`. And a `netloc`-truthiness guard passes userinfo-only authorities
(`http://user:secret@`) that `parsed.hostname` (None) rejects. The flaw originated in the
**reference implementation** (recurrence-client) and was being copied outward with every port — the
§2.3 drift class operating in reverse. Fixed in all three clients (`url.lower().startswith`, guard
on `hostname`); `urlparse` canonicalises the scheme on rebuild.

### 5.2 safe_merge exits 0 without merging — RECURRED TWICE MORE; also non-FF after its resyncs

Both ml#1315's and cascor-client#129's first `safe_merge` runs did BEHIND-resyncs (concurrent merges
kept moving main) and then exited 0 with the PR still OPEN. The standing discipline held both times:
**verify `gh pr view --json state,mergeCommit`, never the exit code**, then re-run. Corollary this
session added: after safe_merge's server-side `update-branch` resyncs, **a plain push of a new local
commit is non-fast-forward** — `git pull --rebase origin <branch>` replays just your commit onto the
update-branch merge commits; squash still composes from the *first* commit, so waiver trailers are
safe. Prefer short **foreground** `wait_for_checks --timeout 540` polls over long background waiters
— background tasks get lease-killed (~2 killed this session) and a killed waiter looks like silence.

### 5.3 The unfiled-work ledger (§7 of the predecessor, updated)

- **CLOSED**: the data-client `__reduce__` correction (predecessor item 2).
- **CARRIED**: `raise_on_status=False` for data-client / recurrence-client (fidelity improvement, not
  a defect — see predecessor §7 for the test that must move with it); the canopy / cascor-worker
  audit (§3.3); and predecessor item 4's drift-watch — the corrected register-§5.1 preamble stuck,
  and the watch itself is now §4's counts-must-agree discipline.
- **NEW — `juniper_data_client/constants.py`'s `__all__` covered 27 of ~141 public module constants
  pre-#164; 30 after its exports — ~111 remain unexported.** (The register row's "28 of ~142 /
  ~114" figures are off by a few; re-measure with `ast` before acting.) Complete it in one pass with
  a drift test asserting every public module assignment is exported; CodeQL blocks piecemeal (§5.5).
- **NEW — the cascor-client WS stream classes** (`CascorTrainingStream` / `CascorControlStream`,
  `ws_client.py:251`, `:509`) keep `rstrip("/")`-only base-URL treatment; the `ws://` scheme family
  needs its own defaulting rules. Recorded in `APD-CCLIENT-005`'s §5.1 row.
- **NEW — recurrence app + model packages ship `py.typed` with nothing checking them** (0 and 2
  hook-flag findings). Recorded in `APD-RCLIENT-003`'s §5.1 row.
- **NEW (operational) — MEMORY.md compaction is due and deferred.** The post-edit hook reported
  19.9KB against its 24.4KB limit (asking for <17.1KB) at this session's edit; the file moves as
  other sessions write it. Deferred deliberately: `docs/memory-index-runway-analysis` (PR #1322,
  OPEN at last check) was being updated all session by another session working exactly that surface
  — check whether it landed before compacting.

### 5.4 A mutation can refute the fix's OWN documentation — run it before writing the claim

The pickle-pin docstring drafted for #162 claimed the test catches dropping the message from
`super().__init__`. Measured: that mutation empties `args` on **both** sides of the round-trip, every
equality arm holds, the test PASSES. What it actually catches is B042's own remedy — extras forwarded
into `args` make the rebuild's `cls(*args)` raise `TypeError`. The false-rationale class nearly
re-entered the file during its own removal; the mutation run is what caught it.

### 5.5 A module WITH `__all__` turns CodeQL's `py/unused-global-variable` into a merge-blocker for whatever lines you touch

data-client#164 sat green-but-BLOCKED on two threads because the constants it re-typed were not in
the module's `__all__` (the other ~111 public constants in that module still are not — CodeQL
anchors alerts to changed lines, so only the touched names fire). Fix by **exporting** the touched
names; the threads auto-resolve. Never hand-resolve a CodeQL thread.

### 5.6 Mutation-restore via `git checkout --` WIPES uncommitted work — commit first

An uncommitted fix plus a sed mutation plus `git checkout -- <file>` restored the *branch* state and
silently deleted the fix under test (#165's first mutation cycle; the edits had to be re-applied).
The order that works: **commit the fix, then mutate, then `git checkout --`** restores the committed
state exactly. Related: a sed *restore* can hit prose occurrences of the mutated string inside
comments — anchor the pattern with `$`, or rely on commit-first restore instead.

---

## 6. Method notes that earned their place this session

- **Dual inheritance is how a typed error joins a hierarchy without breaking a documented
  `Raises: ValueError`** — and check what consumers actually catch before choosing: recurrence's
  routers catch `(JuniperDataClientError, ValueError)` and `_common.py` dispatches on `ValueError`,
  which made single inheritance the breaking option (`-002`).
- **Scope re-derivation out-ran the register three times**: 1 anchored raise site → 9 (`-002`); six
  drifted headers → nine in four values, below the register's own corrected floor (`-005`); "no mypy
  config" → no config *and* no execution, monorepo-wide, three packages (`RCLIENT-003`).
- **All nine strict-mypy findings funnelled through one `-> Any` function** (`_parse_json`); typing
  the source (a validated JSON-object parse with a typed error) beat nine casts and improved runtime
  behaviour (`AttributeError` → typed error on non-object bodies).
- **Vacuous-pass discipline for a NEW lint gate has two arms**: a planted error must fail the exact
  invocation, and the hook's `files:` regex must be proven to match the intended files and nothing
  else — a mis-scoped hook succeeds silently forever.
- **The `pass`-after-docstring counts differed per port** (5, 7, 0 of the filed 6, 8, —): the
  recurrence port was written clean. Re-derive per repo; the register counts predate the base-class
  fixes.
- **A sibling-alignment convention faithfully propagates its reference implementation's flaws** — the
  `__reduce__` false rationale rode cclient#123's port; the case-sensitive scheme check rode every
  port of the recurrence normaliser. When fixing the reference, sweep the ports; when fixing a port,
  sweep the reference.
- **Fleet/bot review threads deserve adversarial evaluation, not dismissal** — the Cursor finding was
  real, severity-relevant (TLS downgrade), and arrived from outside the port-review loop that had
  missed it three times.

---

## 7. Git status

Written from the harness session worktree `juniper-ml/.claude/worktrees/parsed-plotting-bunny`, on
branch `docs/handoff-defect-register-round-23` cut from `origin/main` = `96ed7307` (ml#1331's merge).
This document is the only working-tree change. For task worktrees follow the centralized-worktree
procedure; every task worktree this session created has been removed, its local and remote branches
deleted, and `git worktree prune` run in all four repos (data-client, cascor-client, recurrence,
plus juniper-ml's own branches). Sibling checkouts left on merged, clean `main`:
juniper-data-client `1af5be13`, juniper-cascor-client `619012b6`, juniper-recurrence `f61036d0`,
juniper-data `294104fc`-era plus later pulls, juniper-cascor `4a92082` (moved by another session).
Open juniper-ml PRs at last check (#1304 lockfiles, #1313, #1322, plus whatever concurrent sessions
have opened since — re-run `gh pr list`) are **not** this session's work. Concurrent sessions merged
all day — re-run `gh pr list` and `git fetch` before every register push.
