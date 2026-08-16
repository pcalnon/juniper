# HANDOFF 2026-08-15 — defect register: 91 open, the throttle port is next, consolidation is gated

Successor to [`HANDOFF_2026-08-14_api-primer-and-defect-register.md`](HANDOFF_2026-08-14_api-primer-and-defect-register.md).
All four of that handoff's "highest-value next steps" have shipped. The register's own §2.2 ranking had four
items; **its items 1-3 are fixed and its item 4 is what section 1 below picks up** — two different fours, do not
conflate them.

Independent of the concurrent CLI-experimentation and canopy E2E arcs; touches none of their files.

**Nothing of this arc is in flight.** At the time of writing, one unrelated PR is open — `juniper-ml#1119`,
a concurrent session's release-train handoff archive. (`juniper-cascor#523` was open when this paragraph was
first drafted and merged 54 seconds later; it touched `src/api/observability.py` and `service_launcher.py`, not
`middleware.py`.) **Concurrent sessions are active on this repo — re-run `gh pr list` yourself before editing
`juniper-cascor/src/api/` or `juniper-data/juniper_data/api/`; section 1 lands in both trees.**

## Closed since the predecessor handoff (do not redo)

| Item | Shipped by |
| --- | --- |
| `APD-DATA-002` + `APD-DATA-036` — body-cap bypass and the unguarded `int(content_length)` | [juniper-data#261](https://github.com/pcalnon/juniper-data/pull/261) — one patch, as the register predicted |
| `APD-CASCOR-002` — blanket `ValueError` handler | [juniper-cascor#516](https://github.com/pcalnon/juniper-cascor/pull/516) |
| `APD-DATA-034` † — the same handler in juniper-data, which had no `coerce_native_scalars` to hide behind | [juniper-data#262](https://github.com/pcalnon/juniper-data/pull/262) |
| `APD-DATA-006` — `record_access` lock asymmetry | [juniper-data#263](https://github.com/pcalnon/juniper-data/pull/263) |
| The §2.3 drift-check recommendation → `tests/test_service_fork_drift.py` | [juniper-ml#1103](https://github.com/pcalnon/juniper-ml/pull/1103) |
| Register updated to record all five in place | [juniper-ml#1104](https://github.com/pcalnon/juniper-ml/pull/1104) |

**96 findings, 5 fixed, 91 open.** Fixed entries keep their original IDs and are marked `FIXED` at their §4
table row (and at the §3 detail entry where one exists) — an existing reference still lands on the right entry.

## Verify starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git rev-list --left-right --count HEAD...origin/main   # expect 0 0
wc -l notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md        # expect 665
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest -v tests/test_service_fork_drift.py
git -C ../juniper-data grep -c FailedAuthThrottle; git -C ../juniper-cascor grep -c FailedAuthThrottle
```

Use the `git -C … grep` form, not `grep -rn … | wc -l`. A plain `grep` against a **missing** sibling checkout
sends its error to stderr and prints `0` to stdout — the absent-repo case and the verified-absent case are then
indistinguishable, which is the same false-green this document warns about below. `git grep` fails loudly instead.
(It also avoids walking `.git` packfiles, which can take minutes under GNU `grep -rn`.)

The local `FORCE_LOCAL` run must report **6 tests, 0 skipped**. Two different conditions skip the cross-repo arms:
the `GITHUB_ACTIONS`/`FORCE_LOCAL` gate (`tests/test_service_fork_drift.py:239-242`) and missing sibling checkouts
(`:244-245`). A skipped arm asserts nothing. **In CI this is different by design**: `ci.yml` runs the same file
with no siblings on disk, so **3 of the 6 legitimately skip** there — `test_enforced_guards_are_present_in_every_fork`,
`test_known_gaps_are_still_open_or_get_promoted` and `test_fork_files_named_by_the_registry_exist`, the three that
call `_require_cross_repo`. Only `docs-full-check.yml` clones the siblings. Do not read `skipped=3` in `ci.yml` as a bug.

## 1. The next item — and the co-change it forces

**`APD-DATA-001` † / `APD-CASCOR-004` † — the 401 path is unthrottled in both running services.**
[juniper-ml#1082](https://github.com/pcalnon/juniper-ml/pull/1082) (the register's `APD-SVCCORE-F02`) added
`FailedAuthThrottle` to `juniper-service-core`; neither fork imports it. Verified 2026-08-15: `FailedAuthThrottle`
has **0 occurrences anywhere** in `juniper-data` and `juniper-cascor`, and **25 in `juniper-ml/juniper-service-core`**
(23 of them in `*.py`; the other 2 are `CHANGELOG.md`).

The register ranked this fourth deliberately, and that reasoning still holds: the credentials are high-entropy
keys from Docker secrets, so online guessing is not the threat. What the throttle buys is CPU and log-flood
control. Note that "fourth of four" now just means "last one standing" — it is not an argument for doing it
before section 5's `blank-api-key-filter`, which has identical gate mechanics and is **live** where
`APD-SVCCORE-003` is latent. Either is a defensible next move.

**Where the canonical implementation lives** (the register does not collect these; `gh pr diff 1082 --repo pcalnon/juniper-ml`
is the fastest orientation):

| Piece | Location |
| --- | --- |
| `class FailedAuthThrottle` | `juniper-service-core/juniper_service_core/security.py:290` |
| `build_failed_auth_throttle(max_failures=10, window_seconds=60, enabled=True)` | `…/security.py:423` |
| Pre-auth `check()` block | `…/middleware.py:205-213` |
| `record_failure()` on a 401 | `…/middleware.py:226-227` |
| Test corpus to mirror | `juniper-service-core/tests/test_middleware.py` (11 `FailedAuthThrottle` references — `_auth_app(throttle=…)` harness plus integration and unit arms) |
| Fork targets | `juniper-data/juniper_data/api/middleware.py`, `juniper-cascor/src/api/middleware.py` |

**The fix is two-part, and half of it is easy to miss.** The throttle is not a drop-in class: `check()` runs
*before* authentication, and `record_failure(client_ip)` is gated on the response being a 401
(`middleware.py:226-227`). **Port only the `check()` half and you ship a throttle that never accumulates —
a silent no-op.** The register states this shape at §5.2's `APD-SVCCORE-F02` row; read that row before starting.

**Open design decision the register does not settle:** both forks' `SecurityMiddleware.__init__` is
`(app, api_key_auth, rate_limiter)` with no throttle parameter. Service-core added a fourth optional parameter.
Mirror that (and update each `app.py`'s `add_middleware` call) or construct internally — decide deliberately.
There is **no settings field** for the throttle in service-core or in recurrence, so the ecosystem precedent is
"library defaults, no env knob"; adding `JUNIPER_DATA_*` settings would diverge the forks further.

**The trap.** The drift gate is deliberately two-sided. `pre-auth-throttle` is a `KNOWN_GAP` row
(`tests/test_service_fork_drift.py:134-144`), asserted to be **still absent**. Landing the fix will **fail**
`test_known_gaps_are_still_open_or_get_promoted` (`:259`, assertion at `:273-276`) until that row's `status`
becomes `ENFORCED`. The test's own message says to promote the row and close the register entries.

**But do not expect CI to catch you, and do not try to do it in one change.** Three repos are involved and the
gate lives in only one of them:

1. The gate is a **juniper-ml** test. Neither fork repo's CI runs it — the only references are
   `juniper-ml/.github/workflows/ci.yml:472` and `docs-full-check.yml:259`.
2. juniper-ml's own `ci.yml` **skips** the cross-repo arms (no siblings on disk). So the failure fires only under
   a local `FORCE_LOCAL` run, or up to a week later on the Monday `docs-full-check.yml`.
3. Both gate assertions are **per-site**. In the window where exactly one fork has landed, *neither* status value
   is green: `KNOWN_GAP` fails on the landed fork, `ENFORCED` fails on the untouched one.

**Correct order: (a) juniper-data fork PR, (b) juniper-cascor fork PR, (c) juniper-ml PR promoting the row to
`ENFORCED` plus the register edits.** Verify each step locally with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`, because
nothing in the fork repos' CI will.

**The gate verifies a name, not a behaviour.** Its marker is the bare string `("FailedAuthThrottle",)` per fork
(`:141-142`) — an `import` alone flips it green. A green `ENFORCED` gate does **not** mean the port is correct;
the `record_failure` omission above would sail straight through it.

**"Close the register entries" means four edits**, not one: the §4 table row, the §3 detail entry, the §2.3
copy-drift table row, and the §2.2 item-4 row (currently "still open") — plus a new §5.1 row with the PR and its
verification, following the pattern the five already-fixed entries set.

## 2. `APD-SVCCORE-003` — the precondition for section 3

The register does not rank this as the second-most-valuable work item; it makes it a **precondition of
consolidation**. Sequencing it here is that precondition, not a claim that it outranks everything in section 5.

`_setting` is `getattr(settings, name, default)` guarded by `getattr(websocket.app.state, "settings", None)` —
both defaulted, so **a misspelled field is indistinguishable from an unconfigured one**. Verified byte-identical
(sha256 match) between `juniper-service-core/juniper_service_core/websocket/control_stream.py:66-69` and
`websocket/training_stream.py:44-47`; that duplication is `APD-SVCCORE-010`, and one PR plausibly closes both
(an inference — the register only records the duplication). 13 call sites: 9 in `control_stream.py`, 4 in
`training_stream.py`, reading 11 distinct tunables.

Six of those eleven are **security controls**: `ws_control_allowed_origins` (`:114`),
`disable_ws_control_endpoint` (`:99`), `ws_control_rate_limit_per_sec` (`:246`), and the three
handshake-cooldown parameters (`:89-91`). Writing `..._per_second` where the library reads `..._per_sec` reverts
the control WebSocket to library defaults — silently, with no log line and no test able to see it.

**Honest tension:** this entry is one of the nine that are latent today (nothing imports
`juniper_service_core.websocket`). It is sequenced early because section 3 is what makes it live, not because it
is exploitable now.

## 3. Fork consolidation — the project, and why it is gated

The tempting fix for section 1's divergence is "adopt the shared middleware everywhere". Read the register's
§2.2 closing paragraph first: **on one axis consolidation would be a regression.**

**Scope that axis precisely** — the draft-stage version of this handoff over-claimed it, and the corrected form is:
cascor reads the **six security controls** as hard attributes
(`juniper-cascor/src/api/websocket/control_stream.py:116-118`, `:144`, `:159-160`, `:424-425`), so a typo there
raises `AttributeError` against a real `Settings` (`src/api/settings.py:207`). The shared `_setting` swallows it.
**But cascor is not uniformly stricter**: its heartbeat, idle and resume tunables use the same defaulted-getattr
pattern via its own `_numeric_setting` helper (`control_stream.py:130-139`, used at `:432-433`, `:439`; inline at
`training_stream.py:246-247`) — deliberately, to stop non-`Settings` test doubles leaking stub objects into
`asyncio.sleep`. So the stricter-fork argument covers **the security subset only**, which is exactly the subset
that matters here.

Three facts that size the project (register §4.2 preamble, re-verified by grepping every service's production tree):

- **`.middleware` / `.security` have exactly one production consumer** — `juniper-recurrence`, via the lazy root
  re-export at `juniper_recurrence/app.py:26-34` (PEP 562 `__getattr__`, `juniper_service_core/__init__.py:275-287`
  over `_LAZY_EXPORTS`). `APD-SVCCORE-004` and `-007` are therefore **live in production for recurrence** — though
  `-007` is a `Low`-confidence row whose own text calls it "a documented constraint, not an oversight", so read
  "live" as reachable, not as an incident.
- **`.websocket.*` and `workers/` have no production consumer at all.** The nine entries rooted there
  (`-001`, `-003`, `-005`, `-010`, `-011`, `-012`, `-013`, `-015`, `-016`) are **latent library defects, not live
  exposure** — and consolidation is precisely what makes them live. `create_app` does not rescue this either way:
  `juniper_service_core/app.py` imports only `fastapi` and `.health`, never `.websocket` / `.workers`.
- **Package-root and boot-check entries are live for every consumer** — `-006`, `-008`, `-009`, `-014`, `-017` —
  because `enforce_auth_posture`, `enforce_dependency_floors`, `SettingsBase`, `get_secret` and
  `TrainingLifecycle` are imported by juniper-data, juniper-cascor, juniper-canopy and juniper-recurrence.

**Do not take away "only recurrence uses service-core".** juniper-data, juniper-cascor and juniper-canopy *are*
production consumers (`juniper-data/juniper_data/api/app.py:12`, `juniper-cascor/src/api/app.py:16`,
`juniper-canopy/src/main.py:234`, `:248`) — of `.auth_posture` / `.dependency_floors`, not of `.middleware` /
`.security`. That distinction is the whole content of the consumer split.

The natural experiment worth keeping in mind — the drift gate's `pre-auth-throttle` guard summary puts it as
"the fix reached recurrence automatically and neither fork at all": ml#1082's fix propagated because recurrence
imports the shared middleware, and both forks missed it entirely. Same fix, same ecosystem, three services — the
only differentiator is library-versus-copy.

## 4. Where the other 91 actually sit

The sections above and below name a few dozen IDs. **They are not the whole surface.** Per-repo open counts, derived from
the register's §2 table minus the five fixed (the register states the 96 totals; the open column is arithmetic):

| Repository | Open | Register §4 |
| --- | ---: | --- |
| `juniper-data` | 32 | §4.1 — the largest group by far |
| `juniper-service-core` | 16 | §4.2 — read its preamble before triaging any of them |
| `juniper-cascor-client` | 12 | §4.4 |
| `juniper-data-client` | 8 | §4.5 |
| `juniper-cascor` | 6 | §4.3 |
| Cross-client / ecosystem | 7 | §4.8 |
| `juniper-recurrence-client` | 5 | §4.6 |
| `juniper-observability` | 4 | §4.7 |
| `juniper-ml` (meta) | 1 | §4.8 |

**Three groups get no coverage at all in section 5** and are easy to lose: `APD-OBS-001`…`-004`,
`APD-RCLIENT-001`…`-005`, and `APD-ECO-001`…`-007`. The sharpest of these is **`APD-ECO-001` — no
`Idempotency-Key` mechanism exists anywhere in the stack, zero occurrences.** The register makes it the *enabling
condition* for `APD-CCLIENT-001` below: without a key, retrying a mutation cannot be made safe. Fixing the retry
allow-list without knowing that leaves the underlying gap ecosystem-wide.

## 5. The pattern, and what actually fixes each group

The register's §2.3 names **fifteen entries sharing one shape: a guard adopted in one copy of near-identical code
and not in its siblings.** Three mechanisms, and only the first is catchable by tooling:

**Copy drift — the register calls it "six of the fifteen"** (six *guard rows*, covering ten entry IDs; do not try
to make 6+3+2 reach 15 — that slip is upstream in the register, not here). A service maintains its own copy of
shared code and misses a fix. This is the actionable group and the entire argument for the drift gate. Three rows
remain open:

- `pre-auth-throttle` (`APD-DATA-001` †, `APD-CASCOR-004` †) — section 1.
- `blank-api-key-filter` (`APD-DATA-003`, `APD-CASCOR-006` †) — same promote-on-fix mechanics. Reachability
  caveat: the boot-time `enforce_auth_posture` check filters blanks, so triggering it needs auth-posture
  enforcement disabled — and in juniper-data *also* the JSON list form `'[""]'`, because the comma-separated-string
  branch filters (`settings.py:159`) while the list branch returns `v` untouched (`:160`).
- `OPTIONS` bypass (`APD-CASCOR-001b`, `APD-DATA-035` †) — deliberately **not encoded** in the gate: it landed in
  no copy, so there is no reference implementation to derive a marker from. `APD-CASCOR-001a` is the paired
  one-line comment fix and is disjoint from it.

**Sibling-package drift** (`APD-CCLIENT-001`, `APD-CCLIENT-005`, `APD-DCLIENT-004`) — three independently
released clients that solved the same problem differently. **No shared code, so no drift check applies.** Needs a
written cross-client convention, not tooling.

**Same-file inconsistency** (`APD-CCLIENT-006`, `APD-DATA-004`) — one author, one file, one hardened path and one
not. Nothing structural would have caught these; they are ordinary review misses.

Outside the pattern, two standing instructions:

- **Do not action `APD-ML-001` without deciding the release-train question first.** Those pin strings are
  byte-for-byte asserted by a passing lint (`tests/test_pyproject_extras.py:106-138`), so "fixing" them means
  editing the contract test in the same PR; and capping first-party pins on a meta-package fed by a daily release
  train makes `juniper-ml` a permanent release bottleneck.
- **Triage every `Low`-confidence entry before actioning it.** There are **fifteen** `Conf | Low` rows across
  §4.1-4.8 — `APD-DATA-028`/`-029`/`-030`/`-031`/`-032`/`-033`, `APD-SVCCORE-007`/`-013`/`-016`/`-017`,
  `APD-CASCOR-005`, `APD-RCLIENT-005`, `APD-ECO-006`/`-007`, `APD-ML-001`. The six the register names in §6 are
  an *illustrative* subset ("several are"), not the list; read the `Conf` column, not that sentence.

## Read before triaging anything

- **§2.1 (reachability) and the §4.2 preamble (consumer split).** `juniper-data` publishes no host port in the
  reference stack; `juniper-cascor` is loopback-only with attestation. **But the entries that survive that filter
  as genuinely reachable are those in the bare/dev profile, where the services bind directly** — that is where
  they bite. A `Security` label means neither "exploitable from the internet today" nor "safe".
- **Severity is not a risk assessment.** The register's §6 is explicit: it "reflects the primer's framing plus
  verification, not a risk assessment against deployment reality. An operator may reasonably re-rank."
- **Entries marked `†` are register-original** — verified against source but *not* asserted by the primer. Both of
  section 1's entries are `†`.
- **Retired and split IDs.** `APD-CCLIENT-003` was merged into `APD-CCLIENT-004`; its number is **retired and must
  not be reused.** `APD-CASCOR-001` was split into `001a` / `001b`.
- **Coverage is uneven by construction.** The primer visited code where it made a good example, so
  `juniper-canopy`, `juniper-cascor-worker` and most of `juniper-cascor` are nearly absent. **Their absence is not
  evidence of health** — an actual audit of those three is un-done work this register does not cover.
- **`file:line` anchors drift with every commit**; primer line anchors are stable. Where the two disagree, the
  source is authoritative and the register is stale. Statuses were verified 2026-08-14.

## Method notes worth reusing

These come from the primer arc, not from the register's own §6 method section.

- **Primary sources on disk beat recall.** 31 specifications were downloaded and grepped rather than remembered
  (`util/ad-hoc/2026-08-13_fetch_api_specs.bash`; 31 fetched, two of them deliberately-uncited obsolete RFCs kept
  so the obsoletion relationship can be *checked* rather than asserted). That caught errors that would otherwise
  have shipped — including that the `RateLimit` header fields are still an Internet-Draft, and the RFC
  7386/7396 pair: **7386 is titled "JSON Merge Patch" and 7396 obsoletes it**, which is why citing either number
  alone is ambiguous. This handoff's own draft got that backwards until a validator caught it.
- **A test can be written against a fixture that cannot express the bug.** `APD-DATA-006`'s lost write is
  **inexpressible** against `InMemoryDatasetStore` — `memory.py:38` stores the `DatasetMeta` by reference and
  `:53` returns that same instance, so both writers mutate one object and nothing is ever lost. The test had to
  use `LocalFSDatasetStore`. Check what a fixture's semantics *erase* before trusting a concurrency test.
- **A validator can be wrong, and so can the author.** Six independent validation passes reviewed this handoff
  before it was committed. Between them they caught, in the author's own text: a false RFC identity claim
  ("7396, not 7386, *is* JSON Merge Patch"), an over-widened "the fork is stricter" claim that source refuted for
  5 of 11 tunables, an off-by-one in the verify block, two wrong line anchors, a skip count that was 3 and not 2,
  an occurrence count measured two different ways inside one sentence, and a Low-confidence list presented as
  complete when it held 6 of 15. **Three of those were introduced by the round of edits that fixed the previous
  round.** Assume the same error density remains in what you are reading; the list above is what was found, not
  what exists. Verify a correction before applying it, exactly as you verify a finding.

## Git status

Branch `main`, synced with `origin/main`. Every PR in the table above is merged; for open PRs see the top of this
document, and re-check `gh pr list` yourself — concurrent sessions are active.

One stale session worktree from the predecessor arc survives at
`.claude/worktrees/dynamic-orbiting-seal` on branch `docs/handoff-api-primer-defect-register` (tip `f3af7f2`, not
an ancestor of `main`). Its content reached `main` via ml#1095, so nothing is lost — but it is not "no arc
worktrees", and a worktree sweep will surface it.

The arc's four ad-hoc harnesses are `util/ad-hoc/2026-08-13_{fetch_api_specs.bash,assemble_api_primer.py,gen_primer_examples.py,run_primer_examples.py}`
— note the `2026-08-13_*` glob also matches two files from unrelated arcs. The primer's worked examples re-run via
`python util/ad-hoc/2026-08-13_run_primer_examples.py` (expect `62 passed`).
