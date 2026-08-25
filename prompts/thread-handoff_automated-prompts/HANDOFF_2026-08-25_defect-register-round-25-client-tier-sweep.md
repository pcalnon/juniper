# HANDOFF 2026-08-25 — defect register: 54 fixed / 42 open; the client tier is nearly swept, and the cheap generic closes are now genuinely gone

**The standing mandate is unchanged: keep closing entries in the ecosystem defect register**
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it. For entries inside a juniper-ml
sub-package the fix **and** the register go in one PR.

Successor to [`HANDOFF_2026-08-24_defect-register-clients-swept-46-fixed.md`](HANDOFF_2026-08-24_defect-register-clients-swept-46-fixed.md)
— cite this one by its full name. **Validate this document with independent agents before
trusting it**; this draft's three validators (facts/git, register-consistency, amputation lenses,
all prompted to REFUTE) returned **6 findings (5 distinct)** — every one applied before archiving,
including one arithmetic error of the copied-forward class (a per-repo open count one short of the
register) and three amputations (the §1 `KNOWN_GAP` grep, two §4 protocol elements, two §5.3
ledger items) — the exact classes this lineage warns about.

**Disposition of the predecessor.** Its §1 mechanics all still hold (standalone commands, the
two-sibling drift-gate scope, the re-derivation script — reproduced below). Its §3 table is
superseded by §3 here (it read 50 open). Its §3.2 most-actionable list is **fully consumed** —
items 1–4 all closed this session. Its §5 traps all still stand; §5 below adds this round's. Its
§5.3 unfiled ledger is updated in §5.3 below. All dates UTC. A bare §N means this document —
EXCEPT register-anatomy terms ("the §2 Status paragraph", "§2.3", "the §3 detail entry", "the §4
table row", "a §5.1 row"), which always name sections of the register.

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

**Expected:** `FIXED` rows **54** (the §2 Status paragraph in words is the authority — fifty-four /
**42 open**); `KNOWN_GAP` prints `0` and exits `1` (grep no-match — aborts a `set -e` wrapper; the
gate is two-sided, so this grep is the only line that tells you the ledger still waives nothing —
the drift run prints `8 tests, OK` at 0 or N gap rows alike); the drift gate reports `8 tests, OK`
(`skipped=3` without the env var is correct).
Sibling pulls (separate commands, never a loop):
`git -C /home/pcalnon/Development/python/Juniper/juniper-data pull --ff-only origin main` and
`git -C /home/pcalnon/Development/python/Juniper/juniper-cascor pull --ff-only origin main` — only
those two feed the drift gate.

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

Eight register entries plus one unfiled completion, across six close cycles (rounds 25.1–25.6 —
one register PR per cycle; the trio shared one). All PRs merged; merge SHAs make "merged" checkable
offline. Post-merge main-verify verified green on every fix repo.

| Entries | Fix PR(s) | Register PR | Merge SHA(s) (fix / register) |
|---|---|---|---|
| `APD-RCLIENT-002` (per-call `timeout` on synchronous `train`/`crossval`; effective-timeout error message) | recurrence#130 | ml#1358 | `d968852` / `7464695` |
| `APD-CCLIENT-006` (listener fault isolation ported into `_dispatch`) | cascor-client#135 | ml#1360 | `628f2d8` / `fae1680` |
| `APD-DCLIENT-008` (`create_dataset` persist-onward keyword-only, fake mirrored) | data-client#171 | ml#1362 | `f108c74` / `878d576` |
| the unfiled `constants.__all__` completion (141/141 + drift gate) | data-client#172 | annotated in ml#1365 | `4a32a34` / — |
| `APD-CCLIENT-007` / `-009` / `-013` (mypy 3.12 floor-pinned; both pool knobs; constructor `backoff_factor`) | cascor-client#136 | ml#1365 | `a45fdeb` / `e6645d2` |
| `APD-CCLIENT-012` (`auto_pong` keyword-only ×3 constructors; removal-date half routed to `APD-ECO-001`-style decision row `APD-ECO-007`) | cascor-client#137 | ml#1366 | `b4fbff6` / `8b1cad0` |
| `APD-CCLIENT-011` (`create_network` typed to the server's 14 fields; `**extra` kept but LOUD) | cascor-client#138 | ml#1367 | `f5a9030` / `252f14e` |

**Milestones:**

- **The register crossed its halfway point** (48/48 at close two) and ends the session at 54/42.
- **juniper-cascor-client's generic (non-decision) rows are fully swept** — its only open rows are
  `APD-CCLIENT-001` (blocked on `APD-ECO-001`) and `APD-CCLIENT-008` (envelope sniffing,
  design-shaped). `juniper-data-client` is at **zero open rows**.
- **Both rows of the register's §2.3 same-file inconsistency table are now closed** (the
  `_dispatch` strikethrough landed with ml#1360).
- **Three kw-only boundary closes used the same census discipline** (`create_dataset`, `auto_pong`,
  `create_network`): AST census over all 7 repos for positional/keyword usage BEFORE choosing the
  boundary; each found zero breakers, and each fake mirrors its real signature under a parity pin.

---

## 3. What is left — 42 open, and almost all of it is decisions or larger design work

Re-derived by the §1 script; per-repo splits re-derived the same way.

| Repository | Open | Note |
|---|---:|---|
| `juniper-data` | 21 | 11 blocked on the REST-redesign decision (`-026`–`-033`, `-008`, `-017`, `-022`); actionable remainder: `-005` (securitySchemes), `-015` (route-order guard), `-016` (streaming materialises), `-018`/`-019` (async-job / pagination design), `-020` (`/v1` constant), `-021` (unused filter model), `-023` (operation_id), `-024` (openapi.json deletion), `-025` (content-type split) |
| Cross-client `APD-ECO-*` | 7 | decision-shaped; `-001` unlocks `CCLIENT-001`; `-007` now also carries `CCLIENT-012`'s removal-date half |
| `juniper-service-core` | 7 | **all latent** (`.websocket.*` / `workers/`, no consumer) — still do not fix as live |
| `juniper-cascor-client` | 2 | `-001` (blocked on `APD-ECO-001`), `-008` (envelope sniffing — design-shaped) |
| `juniper-rclient` | 2 | `-004` (dict vs same-repo server models — ECO-004-adjacent), `-005` (three-name identity — owner-flavored, Low conf) |
| `juniper-cascor` | 2 | `-003` (response_model on 46 routes — large); `-005` **owner decision** (primer self-contradiction, unchanged) |
| `juniper-ml` | 1 | `-001` — primer-flagged as judgement |
| `juniper-data-client` | 0 | swept |

### 3.1 Parked on Paul's decisions — unchanged from the predecessor, do not action unilaterally

`APD-CASCOR-005` (primer contradicts itself); the juniper-data REST group; `APD-ECO-001` →
`APD-CCLIENT-001` (one decision, not two tasks). Newly routed INTO the decision set:
`APD-ECO-007` now also owns the `auto_pong=False` removal-date question (`CCLIENT-012`'s §4
marker and §5.1 row say so).

### 3.2 Most actionable next, in order

1. **`APD-DATA-015`** (R) — route ordering is load-bearing and unguarded (`/{dataset_id}`
   catch-all; row anchors `api/routes/datasets.py:276`, `:338`, `:604`, `:628`, `:651` —
   re-verify before acting). A test-only pin in juniper-data; the vacuous-pass lesson from
   `CCLIENT-009` applies — pin declaration ORDER (source/AST or route-table order), not just
   that requests resolve today. Needs the JuniperData conda env
   (`/opt/miniforge3/envs/JuniperData/bin/python`).
2. **`APD-DATA-020`** (M) — `/v1` literal in five places → one constant. Small and mechanical;
   verify the five sites still exist first (anchors predate 08-25 merges).
3. **`APD-DATA-021`** (M) — `DatasetListFilter` declared, never used; route re-declares 12
   params. Check whether wiring the model in changes OpenAPI before choosing remedy.
4. **`APD-RCLIENT-004`** (M) — client `dict[str, Any]` vs same-repo server models. Monorepo, but
   the client package is deliberately dependency-light: importing the app's pydantic models would
   drag fastapi into the client — TypedDicts duplicated client-side are the likely shape; that
   overlaps `APD-ECO-004`'s decision, so consider proposing rather than unilaterally picking.

### 3.3 Carried scope facts

- `juniper-recurrence-client` lives in the **`pcalnon/juniper-recurrence` monorepo**.
- **`juniper-canopy` and `juniper-cascor-worker` still have zero register rows because the primer
  barely visited them.** Carried a fourth time so it does not vanish.

---

## 4. The register-PR protocol (unchanged — reference)

Four touches per close: the §4 table row (`**FIXED (<pr>)** — ` prefix; partial closes qualified
*in the marker*), the §3 detail entry if the ID has one (`grep -n '### APD-<ID>'` — none of this
round's eight had one, but do not skip the check), a §5.1 verification row, and the §2 Status
paragraph (counts in words + the running ID list + "leaving N open"). Counts-must-agree: the §1
grep, the re-derivation script, and the paragraph — all three, every close. Some closes carry a
fifth touch: `CCLIENT-006` struck through its §2.3 same-file table cell; check whether your ID
appears in §2.2/§2.3 tables too. Commit title `chore(register): close APD-…` (all six of this round's register merges use it
verbatim). **Open the fix PR first, then write the register with the number it actually
returned.** Merge order: fix PR merged and VERIFIED, then the register PR (see §5.1). The
register is the hottest file in juniper-ml — `git fetch` + `gh pr list` immediately before
pushing, and rebase onto `origin/main` right before the push.

---

## 5. Traps — this round's additions, in the order they will bite

### 5.1 safe_merge's silent non-merge inverted a merge order — never arm the register PR's auto-merge until the fix PR is VERIFIED MERGED

cclient#138's `safe_merge --execute` printed "all required checks green — merging … (squash)" and
exited 0 with the PR still **OPEN** (the standing class, again). Because ml#1367's auto-merge had
already been armed, the REGISTER PR merged first — the register claimed FIXED for an unmerged fix
for about a minute until a direct `gh pr merge` closed the gap. Two rules compose: verify
`gh pr view --json state,mergeCommit` after every safe_merge (never the exit code), and do not
arm the ml register PR's `--auto` until the fix PR's state reads MERGED.

### 5.2 A runtime guard equal to the library default is vacuous — pin the call site

`CCLIENT-009`'s first-draft test asserted `adapter._pool_connections == 10` — and the mutation
(delete the explicit kwarg) PASSED it, because requests' own default is also 10. When the defect
is "implicit dependence on a library default", a value assertion cannot see the omission; the
shipped gate pins the **call site** (AST: every `HTTPAdapter(...)` passes both knobs by keyword).
Same lesson as §5.4 of the predecessor, new shape: run the mutation BEFORE writing the claim.

### 5.3 The unfiled-work ledger (predecessor §5.3, updated)

- **CLOSED**: the data-client `constants.__all__` completion (data-client#172; 141/141 + drift
  gate; the `APD-DCLIENT-006` §5.1 row carries the completion note).
- **CARRIED**: `raise_on_status=False` for data-client / recurrence-client (fidelity improvement —
  see the register's §4.4 sibling note for the test that must move with it); the canopy /
  cascor-worker audit (§3.3, fourth carry); **the cascor-client WS stream classes**
  (`CascorTrainingStream` / `CascorControlStream`) still keep `rstrip("/")`-only base-URL
  treatment — the `ws://` scheme family needs its own defaulting rules, **no register row names
  them** (recorded in `APD-CCLIENT-005`'s §5.1 row; `CCLIENT-012` changed only their `auto_pong`
  boundary); **recurrence app + model packages still ship `py.typed` with nothing checking them**
  (0 and 2 hook-flag findings; recorded in `APD-RCLIENT-003`'s §5.1 row); **MEMORY.md
  compaction** — still deferred, still owned by the `docs/memory-index-runway-analysis` arc
  (ml#1322 OPEN at last check, plus ml#1329 memory-linter OPEN); check both before compacting.
- **NEW — fake-vs-server validation divergence in cascor-client**: `FakeCascorClient.create_network`
  *requires* `input_size`/`output_size`/`learning_rate` (422 outside `SCENARIO_EMPTY`) while the
  real server defaults every field, and its default config still carries the retired `epochs_max`.
  Observed and recorded with the `CCLIENT-011` close, deliberately unchanged. A fake stricter than
  production fails consumer tests production would pass — file it or fix it consciously.
- **NEW — a stale cascor-client worktree from 2026-08-21**
  (`worktrees/juniper-cascor-client--fix--503-branch-unreachable--20260821-1619--8a34b3a1`, branch
  `fix/503-branch-unreachable`, PR#124 **MERGED** 08-21). Another session's leftover; cleanup
  needs Paul's signal per the worktree-cleanup policy — flagged, not touched.

### 5.4 CodeQL on new TEST files is a three-round trap; the arity check even folds literal-tuple splats

This round's green-but-BLOCKED PRs were all CodeQL threads on freshly added tests: use `with` on a
context-manager client (try/finally is flagged even though the adjacent pre-existing test uses it —
alerts anchor to changed lines); never `import x` AND `from x import` the same module; relaxed
test-flake8 misses an unused import that CodeQL then blocks on (the `noqa`-class memory, test-file
edition). Worst: a deliberately-illegal positional instantiation inside `pytest.raises(TypeError)`
is flagged by `py/call/wrong-number-class-arguments`, and **splatting a literal tuple does not
evade it** — CodeQL folds the tuple. Do not write that arm at all for class constructors: the
KEYWORD_ONLY kind pin implies the TypeError by Python semantics and survives mutation on its own.
(Method calls — data-client#171's `create_dataset` arm — do not trip this query.)

### 5.5 The `**kwargs` pass-through + pydantic's silent-ignore is a live defect class, and the escape hatch must be LOUD

The server's `NetworkCreateRequest` ignores unknown keys, so a typo'd hyperparameter through
`create_network(**kwargs)` vanished without a trace — `epochs_max` demonstrates it in production
(retired server-side; senders keep "working"). The `CCLIENT-011` shape to reuse: type the server's
actual fields (contract of record — read the server model, not the client docstring: three of its
claims were false), keep `**extra` for dict-splat consumers and forward-compat, and `logger.warning`
naming the extra keys. Strictness would have crashed canopy: its adapter splats an arbitrary config
dict and catches only `JuniperCascorClientError` — an uncaught TypeError path.

### 5.6 A push that silently failed leaves `gh pr create` with "Head sha can't be blank"

Transient SSH refusals happened twice; `git push … | tail -1` swallowed one, and the subsequent
PR creation failed with that opaque GraphQL error. Read push output, or re-run the push before
diagnosing anything else.

---

## 6. Method notes that earned their place this session

- **The server model is the contract of record for a client surface** — the `CCLIENT-011` close
  started by reading `NetworkCreateRequest` and refuted three client-docstring claims before
  writing any code. Client docstrings drift; server pydantic does not lie about itself.
- **Census before boundary, every time**: three kw-only closes, three AST censuses over all 7
  repos (223 / 72 / 49+32+35 calls), three zero-breaker results — and one census initially ran
  against the WRONG class name (`FakeCascorWsClient` vs the real `FakeCascorTrainingStream`) and
  returned an empty histogram; an empty census result is a claim about your query, not the world.
  Re-derive the class name from the source before trusting zero.
- **`str`-not-Literal for registry-backed fields in a separately-released client** — duplicating
  the server's `optimizer_type`/`activation` Literals would make a newer server's legal values
  mypy-illegal in older clients; the server already 422s bad values. Typed ≠ maximally narrow.
- **Sibling/fake parity is a per-close checklist item**: every signature change this round was
  mirrored into the corresponding fake under an `inspect.signature` equality pin — and the one
  divergence that could not be safely mirrored (the fake's validation posture) was recorded, not
  redefined.
- **Registry hygiene compounds**: the round's eight closes all passed the counts-must-agree
  check on the first run because the §1 script, not the tables, is the source of truth.

---

## 7. Git status

Written from the harness session worktree
`juniper-ml/.claude/worktrees/sunny-conjuring-sedgewick`, branch
`docs/handoff-defect-register-round-25` cut from `origin/main` = `252f14e` (ml#1367's merge).
This document is the only working-tree change. Every task worktree this session created has been
removed, its local and remote branches deleted, and `git worktree prune` run (juniper-recurrence,
juniper-data-client ×2, juniper-cascor-client ×4). Editable installs restored to the primary
checkouts after every cycle (`pip install -e . --force-reinstall --no-deps`). Sibling checkouts
left on merged, clean `main`: juniper-recurrence `d968852`, juniper-data-client `4a32a34`,
juniper-cascor-client `f5a9030`, juniper-data `9ebc37f`, juniper-cascor `c4bbe81`. The 08-21
stale cascor-client worktree (§5.3) is the one deliberate leftover. Open juniper-ml PRs at last
check (#1313, #1320, #1322, #1329, #1349, #1356, #1357, #1359, plus the Cursor-fleet DRAFTs and
whatever concurrent sessions opened since — re-run `gh pr list`) are **not** this session's work.
Concurrent sessions merged all day — `git fetch` + `gh pr list` before every register push.
