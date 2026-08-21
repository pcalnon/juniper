# Juniper Defect Register — Extracted from the API Primer

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml (register spans the whole ecosystem)
**Author**: Paul Calnon
**License**: MIT License
**Status**: Living register — verified against working copies on 2026-08-14
**Last Updated**: 2026-08-20
**Source**: [`JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`](JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md)

---

## 1. What this is

The API primer uses the Juniper codebase as its worked-example corpus. In doing so it asserts, in passing, a large number of concrete problems in that code — because a defect is the most instructive example of a principle. Those assertions were scattered across 9,863 lines of teaching prose, where they are unusable as work items.

This register extracts every such claim, re-verifies it against current source, and records it with both anchors: the primer passage that makes the claim, and the `file:line` where the code lives.

**Provenance marker.** Entries marked **`†`** are **register-original**: verified against source today, but *not* asserted by the primer. They were discovered during re-verification, most often by asking "does this sibling repo have the same gap?" — a question the primer never asked. Everything unmarked was asserted in the primer and re-verified here.
Where an otherwise-primer-sourced entry carries a sub-claim the primer never made, that sub-claim is labelled **(register-derived)** in place. With those markers applied, the claim "this register contains no new *findings*" is precisely true for every unmarked entry, and honestly false for the marked ones.

It does contain some new *analysis*, and it is worth being precise about where. Three passages go beyond the primer: [§2.3](#23-the-pattern-worth-naming) groups fifteen entries into a single failure mode and recommends a drift check that does not exist; [§2.2](#22-the-four-highest-value-items) ranks by consequence, which the primer never did;
and [`APD-CASCOR-005`](#apd-cascor-005--api-key-comparison-short-circuits-on-match-in-two-of-three-copies) records an internal contradiction between two primer passages.

### Identifier namespace

Entries are `APD-<REPO>-<NNN>` — **A**PI-**P**rimer **D**efect. This is deliberately *not* the existing `F-<REPO>-NNN` namespace used by the canopy E2E arc (`F-CANOPY-001`, `F-CASCOR-002`); the two are unrelated and must not be cross-referenced by number.

Retired IDs are never reused. `APD-CCLIENT-003` was merged into `APD-CCLIENT-004` and its number is retired; `APD-CASCOR-001` was split into `APD-CASCOR-001a` and `APD-CASCOR-001b`.

### Inclusion criterion

A finding is included when it is a **concrete, actionable problem a maintainer could ticket**: a bug, a security gap, a specification violation, a bypass, drift between copies of shared code, a missing guard, a stale comment that misleads, dead code, or an ergonomics defect with a real cost.

Deliberately excluded: general API teaching that merely mentions Juniper; neutral descriptions of how something works; design choices the primer explicitly endorses (the seedless-nonce `dataset_id` escape hatch, the 501-not-503 capability signal, the `ZIP_STORED` streaming trade-off, cascor's verb-shaped training routes); and anything about third-party code (Starlette's 307 `redirect_slashes` default, `requests`, mypy).

Where a claim was arguable, it is included with **Confidence: low** and a note, rather than silently dropped. Over-inclusion is recoverable; a missed defect is not.

### Status is verified, not inherited

Every `OPEN` in this document was confirmed by reading the file **today**. Line numbers are current and may differ from the primer's, which are preserved separately so both anchors resolve. Four extraction passes ran independently over disjoint ranges of the primer; overlapping findings were merged, and each merged entry carries the union of its evidence. A fifth pass audited every primer line anchor for faithfulness, which is what produced the `†` markers above.

---

## 2. Summary

| Repository                  | Security | Correctness | Robustness | Maintainability | Ergonomics |  Total |
|-----------------------------|---------:|------------:|-----------:|----------------:|-----------:|-------:|
| `juniper-data`              |        4 |          10 |          6 |               7 |          9 | **36** |
| `juniper-service-core`      |        1 |           0 |          5 |               6 |          4 | **16** |
| `juniper-cascor-client`     |        0 |           3 |          2 |               4 |          3 | **12** |
| `juniper-data-client`       |        0 |           3 |          1 |               3 |          1 |  **8** |
| `juniper-cascor`            |        2 |           2 |          0 |               3 |          0 |  **7** |
| `juniper-observability`     |        0 |           0 |          0 |               4 |          0 |  **4** |
| `juniper-recurrence-client` |        0 |           1 |          1 |               3 |          0 |  **5** |
| Cross-client / ecosystem    |        0 |           0 |          3 |               3 |          1 |  **7** |
| `juniper-ml` (meta)         |        0 |           0 |          0 |               1 |          0 |  **1** |
| **Total**                   |    **7** |      **19** |     **18** |          **34** |     **18** | **96** |

**Status:** the 96 entries above were all confirmed present in current source on 2026-08-14.
**Sixteen have since been fixed** — `APD-DATA-002`, `APD-DATA-006`, `APD-DATA-034`, `APD-DATA-036`, `APD-CASCOR-002`, (2026-08-16) `APD-DATA-001` † / `APD-CASCOR-004` †, (2026-08-17) `APD-DATA-003` / `APD-CASCOR-006` † plus `APD-SVCCORE-003` / `APD-SVCCORE-010` / `APD-OBS-001`, and (2026-08-20) `APD-DATA-035` † / `APD-CASCOR-001b` plus `APD-CASCOR-001a`, then `APD-DATA-004` — leaving **80 open**; each is marked at its detail entry and in its §4 table row, and all sixteen are recorded in [§5](#5-fixed-findings-before-and-since-the-primer) with their PR and verification.
**Every `Security` entry in this register is now `FIXED`.** All seven — `APD-DATA-001`–`-004`, `APD-CASCOR-004`, `APD-CASCOR-006`, `APD-SVCCORE-003` — are closed; the remaining 80 are `C` / `R` / `M` / `E`. That is a statement about this register's contents, not about the services: coverage is uneven by construction (§6), and `juniper-canopy` / `juniper-cascor-worker` were barely visited by the primer at all.
That closes every item in §2.2's ranked list **and every copy-drift row in §2.3** — the `OPTIONS`/CORS row was the last one open, and fixing it in both forks is what finally made it encodable as a drift gate.
Three further findings were already fixed before this register was written and are likewise listed in §5 rather than counted in the 96: two between the primer's publication and this register, and one earlier still.
No extracted claim failed to reproduce, but one claim reproduced with its provenance inverted — see `APD-SVCCORE-016`.

### 2.1 Reachability — read this before triaging any Security entry

Severity here classifies the *defect*. It does not account for deployment topology, and topology removes the external attacker from most of the `Security` entries:

- **`juniper-data` publishes no host port** in the reference stack. It sits only on the `backend` and `data` networks, both `internal: true` (`juniper-deploy/docker-compose.yml:136-143`, which notes a `ports:` mapping there "would be silently ineffective"). Its reachable attacker is a sibling container that already holds a valid API key.
- **`juniper-cascor` publishes loopback-only**, attested by `JUNIPER_CASCOR_LOOPBACK_PUBLISH_ATTESTED` and enforced by `make preflight` plus `tests/test_compose_bind_posture_attestation.py`.
- **`juniper-service-core` is only partially adopted.** Its HTTP middleware and security modules have exactly one production consumer (`juniper-recurrence`); its WebSocket modules have none. Which module an entry lives in decides whether it is live or latent — see the §4.2 preamble, which classifies all sixteen.

The entries that survive this filter as genuinely reachable are those in the bare/dev profile, where the services bind directly. Triage accordingly; do not read a `Security` label as "exploitable from the internet today".

### 2.2 The four highest-value items

Ranked by consequence divided by cost, not by count.

> **Worked through 2026-08-14 to 2026-08-16. All four items are FIXED.** The ranking held up in
> practice: item 1's fix was indeed a port of already-tested lines from two siblings, and item 2 did
> turn out to need two PRs because the handler is byte-identical in both services. Item 4's warning
> below — that consolidating the forks would activate `APD-SVCCORE-003` — is unchanged, and the fix
> chosen for item 4 deliberately **did not** consolidate: it ported the throttle into each copy,
> leaving that warning still governing any future consolidation.
>
> | Item                                | Fixed by                                                                 | Notes                    |
> |-------------------------------------|--------------------------------------------------------------------------|--------------------------|
> | 1 — `APD-DATA-002` + `APD-DATA-036` | [juniper-data#261](https://github.com/pcalnon/juniper-data/pull/261)     | One patch, as predicted  |
> | 2 — `APD-CASCOR-002`                | [juniper-cascor#516](https://github.com/pcalnon/juniper-cascor/pull/516) |                          |
> | 2 — `APD-DATA-034`                  | [juniper-data#262](https://github.com/pcalnon/juniper-data/pull/262)     |                          |
> | 3 — `APD-DATA-006`                  | [juniper-data#263](https://github.com/pcalnon/juniper-data/pull/263)     |                          |
> | 4 — `APD-DATA-001`                  | [juniper-data#266](https://github.com/pcalnon/juniper-data/pull/266)     | Ported, not consolidated |
> | 4 — `APD-CASCOR-004`                | [juniper-cascor#524](https://github.com/pcalnon/juniper-cascor/pull/524) | Ported, not consolidated |
>
> The §2.3 drift-check recommendation was also built: [juniper-ml#1103](https://github.com/pcalnon/juniper-ml/pull/1103).
> Its `pre-auth-throttle` row was promoted `KNOWN_GAP` → `ENFORCED` when item 4 landed, which is the
> self-maintaining half of that ledger working exactly as designed.

1. **`APD-DATA-002` — the request body limit is bypassable.** A chunked request with no `Content-Length` streams past the 10 MiB cap entirely. The only unauthenticated memory-exhaustion vector in the register when the service runs in the open bare/dev profile — and the fix is twelve already-written, already-tested lines sitting in **two** sibling repos
   (`juniper-cascor/src/api/middleware.py:100-110`, `juniper-service-core/juniper_service_core/middleware.py:113-131`). Highest consequence over lowest cost. `APD-DATA-036` is a second defect on the same line and ships with the same patch.
2. **`APD-CASCOR-002` + `APD-DATA-034` † — a blanket `ValueError` handler reports server faults as `400`.** Present in **both** running services. `PydanticSerializationError` subclasses `ValueError`, so a server-side serialisation fault is returned to the caller as a client error and never appears in 5xx alerting.
   It has already bitten once — cascor's `coerce_native_scalars` exists solely to dodge it, and `juniper-data` has no such workaround, so it is *less* protected. An observability blind spot across the whole HTTP surface of two services.
3. **`APD-DATA-006` — a `GET` can silently undo a write.** `record_access` rewrites the whole metadata document under a lock the tag-update path does not take. The race is likelier than it first appears: on the download path `record_access` is scheduled with `call_soon`
   (`routes/datasets.py:698`), so it runs on the loop thread and can land squarely between the tag update's two `asyncio.to_thread` hops. Silent write loss triggered by a *safe* method is the class nobody suspects.
4. **`APD-DATA-001` † / `APD-CASCOR-004` † — the 401 path is unthrottled in both running services.** — **FIXED** ([juniper-data#266](https://github.com/pcalnon/juniper-data/pull/266), [juniper-cascor#524](https://github.com/pcalnon/juniper-cascor/pull/524)). `juniper-ml#1082` added `FailedAuthThrottle` to `juniper-service-core`, but **neither service imported that middleware** — both carry their own copies. Real, but ranked fourth deliberately:
   the credentials are high-entropy keys from Docker secrets, so online guessing is not the threat; what the throttle actually buys is CPU and log-flood control. The shippable fix is porting `FailedAuthThrottle` into the two copies — *not* "retire the copies", which is a migration project, not an equal-cost alternative.
   **Both entries are `†`.** The primer describes the mechanism and states the shared-package fix landed (1058, 1344); it never mentions a juniper-data or juniper-cascor copy of `SecurityMiddleware`, and `FailedAuthThrottle` appears zero times in its 9,863 lines. The copy divergence is this register's finding, not the primer's.
   **What the fix took, for the next port of this shape.** Both PRs mirror service-core's optional fourth constructor parameter (`failed_auth_throttle: FailedAuthThrottle | None = None`, defaulting to an *enabled* throttle), so neither `app.py` call site changed and no settings field was added — the shared package and juniper-recurrence expose no env knob either, and inventing one per fork would have widened the divergence this entry is about.
   The port is two-part and the second half is the easy one to lose: `check()` runs before authentication, but `record_failure()` is gated on the response being a 401, so a `check()`-only port is a throttle that never accumulates.
   Each fork's suite therefore carries an arm that fails if `record_failure` is dropped (verified by mutation in both).
   One pre-existing cascor test, `test_failed_auth_does_not_increment_rate_limit`, fires exactly the default budget of 10 failed attempts and then asserts a valid key still passes; it now builds a generous throttle so it keeps measuring the *identity-keyed limiter's* counters rather than tripping the new gate.

**A loop worth noticing before acting on #4.** The tempting fix for the divergence — adopt the shared middleware everywhere — is precisely what would make `APD-SVCCORE-003` live. That entry (a `getattr`-with-default settings lookup that silently skips the WebSocket Origin allowlist when the field is absent or misspelled) is the
highest *potential* consequence in the register, and it is inert today only because nothing imports `juniper_service_core.websocket`. cascor's copy reads those settings as hard attributes, so a typo is an `AttributeError` there. **On this axis the local copy is the stricter one, and consolidation would be a regression unless `_setting` is hardened first.**

### 2.3 The pattern worth naming

Fifteen entries share one shape: **a guard adopted in one copy of near-identical code and not in its siblings.** They are not all the same mechanism, and the distinction matters for what fixes them:

**Copy drift** — a service maintains its own copy of shared code and misses a fix. A drift check against `juniper-service-core` would catch these. **All of this group is now closed, and every row is encoded**: each has been ported (or, for the two rows with no shared implementation, fixed independently in both forks) and promoted to `ENFORCED`. The `OPTIONS`/CORS row was the last one open — it had landed in *no* copy, so there was nothing to derive a marker from until both forks were fixed.

> **That drift check now exists**: `juniper-ml/tests/test_service_fork_drift.py`
> ([juniper-ml#1103](https://github.com/pcalnon/juniper-ml/pull/1103)). It encodes this table as a
> registry of named guards — deliberately *not* a file diff, because these forks diverge
> legitimately and sometimes intentionally (juniper-data holds API keys in a `list` so
> `compare_digest` runs per key without a set-membership timing side-channel, where service-core uses
> a `set`; a diff would bury the signal). It is **two-sided**: rows already fixed are `ENFORCED` and
> must stay present, and rows still open are `KNOWN_GAP` and asserted to be still *absent*, so
> closing one fails the gate and prompts promotion rather than letting the ledger rot. **No
> `KNOWN_GAP` rows remain**; all six guards are `ENFORCED`. The last one promoted,
> `cors-outside-auth`, needed a mechanism the others did not: its regression shape is two
> `add_middleware` calls swapping places, so every marker is present either way and a presence-only
> check would pass on the very defect it guards. That row is an **ordered** site — the markers must
> appear in a declared sequence — with its own negative controls in the always-on structural class.
> The gate runs against sibling checkouts in `docs-full-check.yml`.

| Guard                                       | Landed in                                     | Missing from                                                                                                     | Gate                                |
|---------------------------------------------|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| Streaming body cap (CR-024)                 | `juniper-cascor`, then `juniper-service-core` | ~~`juniper-data`~~ — **fixed** (`APD-DATA-002`, data#261)                                                        | `ENFORCED`                          |
| `Content-Length` parse guard (400, not 500) | `juniper-cascor`, `juniper-service-core`      | ~~`juniper-data`~~ — **fixed** (`APD-DATA-036`, data#261)                                                        | `ENFORCED`                          |
| Blank-API-key filter                        | `juniper-service-core`                        | ~~`juniper-data`, `juniper-cascor`~~ — **both fixed** (`APD-DATA-003` data#267, `APD-CASCOR-006` † cascor#527)   | `ENFORCED`                          |
| Pre-auth throttle (`juniper-ml#1082`) †     | `juniper-service-core`                        | ~~`juniper-data`, `juniper-cascor`~~ — **both fixed** (`APD-DATA-001` † data#266, `APD-CASCOR-004` † cascor#524) | `ENFORCED`                          |
| CORS outside auth (was: `OPTIONS` bypass)   | *(nowhere)*                                   | ~~`juniper-cascor`, `juniper-data`~~ — **both fixed** (`APD-CASCOR-001b` cascor#540, `APD-DATA-035` † data#273)   | `ENFORCED`                          |
| Narrow serialisation-error handling         | *(nowhere)*                                   | ~~`juniper-cascor`, `juniper-data`~~ — **both fixed** (`APD-CASCOR-002` cascor#516, `APD-DATA-034` † data#262)   | `ENFORCED`                          |

The pre-auth-throttle row is `†`: the pairing of the shared fix against the two unpatched copies is register-original, not a primer claim.

> **A marker caveat learned promoting that row.** The gate checks source markers, so it verifies a
> *name*, not a behaviour — the original single marker `("FailedAuthThrottle",)` would have gone
> green on a bare `import`, and the half-port that actually matters (pre-auth `check()` wired,
> `record_failure` omitted → a throttle that never accumulates) would have sailed through it. The
> promoted row therefore asserts **two** markers per fork, `FailedAuthThrottle` *and*
> `record_failure`. That is still only a structural proxy: real behavioural coverage lives in each
> fork's own suite, and a green `ENFORCED` gate is evidence the pieces are present, never that the
> port is correct. Worth applying the same scepticism to the remaining rows.

**Sibling-package drift** — three independently released client packages that solved the same problem differently. No shared code, so no drift check applies; this needs a written cross-client convention.

| Guard                            | Landed in                                          | Missing from                                                                           |
|----------------------------------|----------------------------------------------------|----------------------------------------------------------------------------------------|
| Idempotent-only retry (XREPO-11) | `juniper-data-client`, `juniper-recurrence-client` | `juniper-cascor-client` (`APD-CCLIENT-001`)                                            |
| Base-URL normalisation           | `juniper-data-client`, `juniper-recurrence-client` | `juniper-cascor-client` (`APD-CCLIENT-005`)                                            |
| Base-URL `netloc` validation     | `juniper-recurrence-client`                        | `juniper-data-client` (`APD-DCLIENT-004`), `juniper-cascor-client` (`APD-CCLIENT-005`) |

**Same-file inconsistency** — one author, one file, one hardened path and one not. Nothing structural would have caught these; they are ordinary review misses.

| Guard                           | Present at                    | Absent at                                                   |
|---------------------------------|-------------------------------|-------------------------------------------------------------|
| Listener fault isolation        | `_dispatch_disconnect`        | `_dispatch` (`APD-CCLIENT-006`)                             |
| Redaction of raw exception text | the `except Exception` branch | ~~the adjacent `except HTTPException` branch~~ — **fixed** at the source (`APD-DATA-004`, data#275) |

The first group is the actionable one, and it is the argument for a drift check: six of the fifteen are copies of `juniper-service-core` code that diverged silently. The other two groups need conventions and review attention respectively, not tooling.

---

## 3. Critical and security findings — detail

Entries below carry full detail. Everything else is tabulated in §4 with the same anchors.

### APD-DATA-001 † — The 401 path consumes no rate-limit budget

|                |                                                                                                                                                                                                                                                                |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Severity**   | Security                                                                                                                                                                                                                                                       |
| **Status**     | **FIXED** — [juniper-data#266](https://github.com/pcalnon/juniper-data/pull/266); the juniper-cascor sibling `APD-CASCOR-004` † in [juniper-cascor#524](https://github.com/pcalnon/juniper-cascor/pull/524)                                                    |
| **Source**     | `juniper-data/juniper_data/api/middleware.py:110-150`                                                                                                                                                                                                          |
| **Primer**     | I.5 — line 1058 (mechanism only)                                                                                                                                                                                                                               |
| **Provenance** | **Register-original.** The primer describes the shared-package mechanism and says the gap "is now fixed (juniper-ml#1082)" (1058, 1344). It never mentions a juniper-data copy of `SecurityMiddleware`; `FailedAuthThrottle` appears zero times in the primer. |
| **Confidence** | High                                                                                                                                                                                                                                                           |

**Problem.** `SecurityMiddleware` calls `APIKeyAuth`, which *raises* on failure, before it ever reaches the rate limiter. A failed authentication therefore consumes no budget at all.

**Impact.** Credential guessing and garbage-credential floods are bounded only by how fast the process can reject them. The limiter protects the authenticated surface and leaves the authentication surface itself open.

**Why this is still open after `juniper-ml#1082`.** The fix landed in `juniper-service-core`. Both services import their **own copies**:

```text
juniper-cascor/src/api/app.py:20        from api.middleware import ... SecurityMiddleware
juniper-data/juniper_data/api/app.py:18 from .middleware import ... SecurityMiddleware
```

`grep -rn FailedAuthThrottle` across both repos returned **zero** hits (re-verified 2026-08-15, still zero). The shared fix was unreachable from either running service.

**Fix.** Port `FailedAuthThrottle` into both copies. Retiring the copies in favour of the shared middleware is the better end state but a much larger project — and read §2.2's closing paragraph first.

**Fixed as described** — ported, not consolidated, so §2.2's loop warning still governs any future consolidation.
Both PRs mirror service-core's optional fourth constructor parameter defaulting to an *enabled* throttle, so no `app.py` call site changed; no settings field was added, matching the shared package and juniper-recurrence.
Both halves are wired (`check()` before auth, `record_failure()` gated on a 401) — a `check()`-only port would be a throttle that never accumulates, and each fork carries an arm that fails if `record_failure` is dropped.
The `pre-auth-throttle` drift row moved `KNOWN_GAP` → `ENFORCED` in the same arc, with a second marker added because the original name-only marker would have gone green on a bare `import`.

---

### APD-DATA-002 — Request body limit is bypassable by a chunked request

|                |                                                                                                                    |
|----------------|--------------------------------------------------------------------------------------------------------------------|
| **Severity**   | Security                                                                                                           |
| **Status**     | **FIXED** — [juniper-data#261](https://github.com/pcalnon/juniper-data/pull/261) (with `APD-DATA-036`, same patch) |
| **Source**     | `juniper-data/juniper_data/api/middleware.py:79-83`                                                                |
| **Primer**     | I.2 / I.4 — lines 757-759                                                                                          |
| **Confidence** | High                                                                                                               |

**Problem.** The entire check is `if content_length is not None and int(content_length) > self._max_bytes`. A chunked request that sends no `Content-Length` makes the first conjunct false, so the comparison never runs and nothing stream-caps the body.

**Impact.** The 10 MiB limit is advisory. Verified empirically in the primer: an 11 MiB chunked body was read in full and surfaced as a 422 JSON-decode error, never a 413.

**Evidence.** The shared implementation at `juniper-service-core/juniper_service_core/middleware.py:113-131` always stream-reads `POST`/`PUT`/`PATCH` against a cumulative cap, and its comment names this exact bypass as "the classic bypass". The fix never propagated. `APD-DATA-036` is a second, distinct defect on the same line.

---

### APD-DATA-003 — A blank API key enables authentication that accepts an empty key

|                |                                                                                                                                                                                                             |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Severity**   | Security                                                                                                                                                                                                    |
| **Status**     | **FIXED** — [juniper-data#267](https://github.com/pcalnon/juniper-data/pull/267); the juniper-cascor sibling `APD-CASCOR-006` † in [juniper-cascor#527](https://github.com/pcalnon/juniper-cascor/pull/527) |
| **Source**     | `juniper-data/juniper_data/api/security.py:54`; `juniper_data/api/settings.py:155-160`                                                                                                                      |
| **Primer**     | I.5 — lines 1041-1042                                                                                                                                                                                       |
| **Confidence** | High                                                                                                                                                                                                        |

**Problem.** `self._api_keys = list(dict.fromkeys(api_keys)) if api_keys else []` de-duplicates but does not filter blanks, and the settings validator is inconsistent: the comma-separated-string branch filters (`:159`), the list branch returns `v` untouched (`:160`).

**Impact.** `JUNIPER_DATA_API_KEYS='[""]'` parses to `['']`, sets `_enabled = True`, and validates an empty `X-API-Key`. This is strictly worse than authentication being off, because the deployment believes it is protected — the exact failure mode the ecosystem's boot-time `enforce_auth_posture` check exists to prevent, defeated after boot.

**Evidence.** `juniper-service-core/juniper_service_core/security.py:44` carries the filter with a comment naming this failure. Not propagated.

**Reachability caveat (register-derived).** The reference deployment defaults `JUNIPER_DATA_REQUIRE_AUTH` to `"true"` (`juniper-deploy/docker-compose.yml:163`). With that set, boot runs `enforce_auth_posture`, which resolves keys through `real_keys` (`juniper_service_core/auth_posture.py:59-69`, called at `:112`) — the same blank filter — so a blank key is a **boot failure**, not a silent open service.
Triggering this defect therefore needs *both* the JSON list form `'[""]'` (the string branch filters) *and* `require_auth=false`. Real, and narrower than it first reads.

**Fixed at the point of use, not by relying on the boot check** (which can be turned off).
Both forks now filter blanks / whitespace-only / non-string entries in `APIKeyAuth.__init__` before deriving `_enabled`, and both settings validators filter the list branch as well — closing the string-vs-list inconsistency that made the JSON form the reachable shape.
juniper-data keeps its `list` container (`hmac.compare_digest` per key, SEC-01/JD-SEC-02) rather than adopting service-core's `set`; cascor already used a set, so its line is byte-identical to the canonical one.
One ordering subtlety surfaced during the fix and is worth keeping: `dict.fromkeys` hashes every element, so the filter must run **before** the de-duplication or a malformed env value containing an unhashable entry raises `TypeError` — the first draft had it backwards and a new test caught it.
The `blank-api-key-filter` drift row moved `KNOWN_GAP` → `ENFORCED` with a two-marker predicate.
The prior bare `.strip()` marker was sufficient to *detect* this fix — neither fork's `security.py` contained a strip beforehand — but it was not specific to it: any unrelated strip later added to that module would have flipped the guard green with the filter still absent.
Pairing it with `isinstance(k, str)` ties the marker to the guard's shape rather than to an incidental call.

---

### APD-DATA-006 — A `GET` can silently undo a concurrent tag edit

|                |                                                                                                    |
|----------------|----------------------------------------------------------------------------------------------------|
| **Severity**   | Correctness                                                                                        |
| **Status**     | **FIXED** — [juniper-data#263](https://github.com/pcalnon/juniper-data/pull/263)                   |
| **Source**     | `juniper-data/juniper_data/storage/base.py:217-222`; `juniper_data/api/routes/datasets.py:785-794` |
| **Primer**     | II.6 — lines 4197-4200, 4275-4279                                                                  |
| **Confidence** | High                                                                                               |

**Problem.** Two writers of the same `DatasetMeta` document use asymmetric locking. `record_access` — fired on every metadata read and every artifact download — does read-modify-write of the whole document under `self._version_lock`. `update_dataset_tags` does its own read-modify-write across two `asyncio.to_thread` hops and takes **no lock at all**, so the lock protects nothing against it.

**Impact.** A plain `GET` can overwrite a concurrent tag edit with a pre-edit snapshot. Silent data loss triggered by a *safe* method, which is why it would never be suspected.

**Note on the existing rationale.** The docstring at `base.py:214-216` reasons about a race — but only for the access *counter*, calling it "informational so this is an acceptable trade-off". The code rewrites the entire document, so the trade-off analysis does not cover what it actually does.

---

### APD-SVCCORE-003 — Unvalidated settings lookup silently defaults security controls

|                |                                                                                                                                                                                                       |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Severity**   | Security                                                                                                                                                                                              |
| **Status**     | **FIXED** — ml#1154 (closes `APD-SVCCORE-010` in the same change)                                                                                                                                     |
| **Source**     | `juniper-service-core/juniper_service_core/websocket/control_stream.py:66-69` — 13 call sites across both `_setting` copies (9 in `control_stream.py`, 4 in `training_stream.py:193-194`, `:210-211`) |
| **Primer**     | III.7 — lines 7950-7951, 7962, 7964-7968                                                                                                                                                              |
| **Confidence** | High                                                                                                                                                                                                  |

**Problem.** `_setting` is `getattr(settings, name, default)` guarded by `getattr(app.state, "settings", None)` — both defaulted. A misspelled or absent settings field is indistinguishable from an unconfigured one. `SettingsBase` declares only four fields; eleven distinct tunables are read this way, entirely unvalidated.

**The primer frames this as a deliberate trade, and that framing belongs here.** At 7950-7951 it calls it "the most interesting trade here", one that "deliberately gives up validation", and at 7964-7965 it names the benefit plainly: "genuine decoupling: the shared package never imports a consuming service's settings class, and each service declares only the tunables it uses." That benefit is real. This entry argues the trade is mispriced for the subset below, not that the design is thoughtless.

**Impact (register-derived).** Several of those tunables are **security controls**: `ws_control_allowed_origins` (the fail-closed Origin allowlist, `control_stream.py:114`), `disable_ws_control_endpoint` (`:99`), `ws_control_rate_limit_per_sec` (`:246`), and the three handshake-cooldown parameters (`:89-91`). Writing `ws_control_rate_limit_per_second` where the library reads `..._per_sec` reverts the control WebSocket to library defaults — silently, forever, with no log line and no test able to see it.

The primer names only that one rate-limit typo pair (7967-7968) and gives an aggregate count without a list; enumerating *which* of the eleven are security controls is this register's analysis. It is what turns a maintainability trade into a security entry.

**Fix (ml#1154) — the trade is kept, the cost is removed.**
`juniper_service_core/websocket/tunables.py` declares all eleven tunables with their defaults and a `security` flag, and both handlers now resolve through it.
Nothing imports a consuming service's settings class, so the decoupling the primer praises is intact.
Two things change: the default lives in the registry rather than at each of the 13 call sites (so the set is *declared* and therefore auditable at all), and a miss that looks like a misspelling is logged at WARNING naming both spellings — the `..._per_second` / `..._per_sec` case the primer names now produces a log line instead of silence.
`audit(settings)` is the boot-time counterpart, reporting which security controls are running on library defaults and which look like typos.
A `resolve()` call for an undeclared name raises rather than defaulting, so a library-side typo cannot reach production either.
This also closes `APD-SVCCORE-010`: the byte-identical `_setting` bodies are replaced by one shared resolver, with the two thin module-local wrappers delegating to it.

**Still latent, and the consolidation warning is now weaker but not void.**
`juniper_service_core.websocket` still has no production consumer, so this remains a latent library defect (§4.2 preamble).
What changed is §2.2's loop: adopting the shared middleware no longer silently reverts a misspelled security control, because the misspelling is now loud.
cascor's hard-attribute reads are still *stricter* for the six security controls (an `AttributeError` beats a WARNING), so consolidation still trades strictness for reach — it is now a judgement call rather than a straight regression.

---

### APD-SVCCORE-001 — Worker binary-frame cap has no cumulative limit across an attachment list

|                |                                                                                                                |
|----------------|----------------------------------------------------------------------------------------------------------------|
| **Severity**   | Robustness                                                                                                     |
| **Status**     | OPEN                                                                                                           |
| **Source**     | `juniper-service-core/juniper_service_core/websocket/worker_stream.py:323` (receive), `:329` (per-frame check) |
| **Primer**     | I.4 — lines 754-755                                                                                            |
| **Confidence** | High                                                                                                           |

**Problem.** `len(raw_bytes) > _MAX_BINARY_SIZE` (100 MB) is evaluated *after* `await websocket.receive()` has fully materialised the frame. More importantly, the cap is **per-frame with no cumulative accumulator**: `_handle_task_result` loops over `attachment_names` and receives one frame each (`:322-333`), so a single result submission permits `len(attachment_names) × cap`.

**Impact.** An authenticated worker can force repeated large allocations across one logical submission. Requires an already-registered, already-authenticated worker — the `/ws/workers` handshake is fail-closed (4001 on a bad key, 4008 on a shape-invalid registration), so this is not an unauthenticated vector.

**Severity caveat — the 100 MB constant is effectively unreachable.** uvicorn's `ws_max_size` defaults to **16 MiB** (`uvicorn.config.Config`, verified 0.46.0) and nothing in `juniper-service-core`, `juniper-cascor` or `juniper-data` overrides it. A frame larger than 16 MiB is rejected by the protocol layer before `receive()` returns, so `_MAX_BINARY_SIZE` can never fire and the maximum forced allocation per frame is 16 MiB, not 100 MB.
That is what moves this from Security to Robustness: the real defect is the missing cumulative cap, plus a dead constant that reads as protection it does not provide.

---

### APD-OBS-001 — `X-Request-ID` is propagated unvalidated

|                |                                                                                                  |
|----------------|--------------------------------------------------------------------------------------------------|
| **Severity**   | Maintainability                                                                                  |
| **Status**     | **FIXED** — ml#1156                                                                              |
| **Source**     | `juniper-observability/juniper_observability/middleware/request_id.py:36` (ingest), `:40` (echo) |
| **Primer**     | I.10 — lines 1109, 2101-2103                                                                     |
| **Confidence** | Medium                                                                                           |

**Problem.** The inbound header is accepted verbatim — no length cap, no character allowlist, no shape validation — stored in a process-wide `ContextVar`, embedded in every log record, and echoed back on the response.

**Severity caveat — both "unmitigated" items are in fact contained.** The register's earlier Security rating rested on two claims that do not survive verification:

- **Length.** h11's `max_incomplete_event_size` defaults to **16384** bytes and caps the *entire* request head, and uvicorn leaves `h11_max_incomplete_event_size` at `None` (verified h11 0.16.0 / uvicorn 0.46.0). A multi-megabyte header value is rejected at the protocol layer and never reaches ASGI, so the "amplified into every log record" scenario cannot occur through HTTP.
- **Injection.** h11 rejects CR/LF in header values outright — `h11.Connection.send` with a value containing `\r\n` raises `LocalProtocolError: Illegal header value`. The response echo at `:40` is therefore not a header-injection vector either.

**What remains, and why it is still worth fixing.** An unvalidated external value flows into a `ContextVar` that any consumer may write to a line-oriented sink, and the containment above is entirely incidental — it depends on the h11 defaults and the JSON formatter's `json.dumps` escaping, neither of which this package controls or asserts.
Restate the work item as: **apply a length cap and a character allowlist on ingress, before that containment is assumed.** The house helper for exactly this class already exists — `_sanitize_for_log` in `juniper-service-core/juniper_service_core/websocket/control_security.py:29` — and is simply not applied here.

**Fixed (ml#1156) — as restated, on ingress.**
`is_valid_request_id` applies a 128-character cap and an allowlist (`[A-Za-z0-9._:-]`, anchored at both ends), and an inbound value that fails either is **replaced with a fresh UUID4** rather than sanitized: stripping characters would propagate an ID the client never sent, correlating to nothing on either side, whereas a fresh UUID is at least honestly this server's own.
Rejection is deliberately **silent** — logging every rejected header would hand an attacker the log-flood lever this guard exists to bound.
The allowlist was chosen to keep real correlation IDs working (UUID, ULID, W3C `traceparent`, `service:id`), all pinned by tests.
Verified by mutation: making the validator return `True` fails 7 arms.
The containment the caveat above describes is now asserted locally instead of borrowed from h11's defaults.

**Provenance (register-derived).** Two claims in the earlier text were not the primer's: that `juniper-data-client` propagates the value outbound across service hops (the primer's client-side references read `X-Request-ID` *off responses*, the opposite direction), and that `_sanitize_for_log` exists and is unapplied (`_sanitize_for_log` appears zero times in the primer). Both are verified against source; neither is an extraction.

---

### APD-CASCOR-001a — Middleware ordering comment is wrong

|                |                                                                                           |
|----------------|-------------------------------------------------------------------------------------------|
| **Severity**   | Maintainability                                                                           |
| **Status**     | **FIXED** — [juniper-cascor#540](https://github.com/pcalnon/juniper-cascor/pull/540)      |
| **Source**     | `juniper-cascor/src/api/app.py:644-646` (the comment); `:621` (CORS), `:630` (body limit) |
| **Primer**     | Appendix A Q57 — lines 9592-9594                                                          |
| **Confidence** | High                                                                                      |

**Problem.** The in-code comment states the execution order as `RequestId → Prometheus → Security → SecurityHeaders → CORS`, omitting `RequestBodyLimitMiddleware` (`:630`), which under Starlette's LIFO `add_middleware` actually runs between `SecurityHeaders` and CORS.

**Impact.** A wrong ordering comment sitting beside security-critical middleware is worse than none — it is the artefact the next maintainer will trust when reordering.

**Fix.** A one-line comment edit. Split from `APD-CASCOR-001b` precisely because the fixes are disjoint: this one is a comment, that one changes request handling and needs tests.

**Fixed together after all.** The split was sound as analysis but not as sequencing: `001b`'s fix *is* a reorder, and a reorder cannot land beside an ordering comment that the reorder has just made doubly wrong. Rewriting the comment was forced by the code change, so both closed in cascor#540. The same wrong comment existed verbatim in `juniper-data` — a sibling the register never recorded, because `APD-CASCOR-001a` was filed as cascor-only — and was corrected in data#273.

---

### APD-CASCOR-001b — CORS sits behind auth, so preflights are answered 401

|                |                                                                                                                                                        |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Severity**   | Correctness                                                                                                                                            |
| **Status**     | **FIXED** — [juniper-cascor#540](https://github.com/pcalnon/juniper-cascor/pull/540); the juniper-data sibling `APD-DATA-035` † in [juniper-data#273](https://github.com/pcalnon/juniper-data/pull/273) |
| **Source**     | `juniper-cascor/src/api/app.py:621` (CORS registered first → innermost), `:641` (`SecurityMiddleware`); `src/api/middleware.py:189-198` (`_is_exempt`) |
| **Primer**     | Appendix A Q57 — lines 9592-9594                                                                                                                       |
| **Confidence** | High                                                                                                                                                   |

**Problem.** Because CORS is registered first it executes *innermost*, so `SecurityMiddleware` sees cross-origin preflights before CORS does — and `_is_exempt` keys on path only (`return path in EXEMPT_PATHS`, `middleware.py:198`), with no `OPTIONS` bypass.

**Impact.** A preflight to any non-exempt `/v1/*` path is answered 401 rather than with CORS headers, so browser clients on a configured origin cannot preflight authenticated endpoints — preflights carry no `X-API-Key` by specification.

**Fix.** Either an `OPTIONS` bypass in `_is_exempt` or a middleware reorder. Both change request handling and need tests, which is why this is tracked separately from the comment fix. `APD-DATA-035` † is the same defect in `juniper-data`.

**Fixed by the reorder, deliberately.** The two options are not equivalent. An `OPTIONS` bypass in `_is_exempt` exempts *every* `OPTIONS` request from auth **and** rate limiting; `CORSMiddleware` short-circuits only a genuine preflight — one carrying `Access-Control-Request-Method` — so a plain `OPTIONS` request still authenticates. Both forks now pin that distinction as a test in its own right, so the narrower surface cannot regress silently.

**A second symptom, not recorded in the original entry:** with CORS innermost, an ordinary cross-origin request rejected by auth also returned **no** CORS headers, so a browser reported an opaque CORS failure instead of surfacing the 401. Running CORS outermost fixes both, which is likely why this was hard to diagnose from the client side. Verified before and after against the real app factories; mutation-tested (4 of 5 new arms fail against the unfixed ordering in each fork).

---

### APD-CASCOR-002 — `ValueError` handler reclassifies server faults as client errors

|                |                                                                                                                                                                                                       |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Severity**   | Correctness                                                                                                                                                                                           |
| **Status**     | **FIXED** — [juniper-cascor#516](https://github.com/pcalnon/juniper-cascor/pull/516); the juniper-data sibling `APD-DATA-034` in [juniper-data#262](https://github.com/pcalnon/juniper-data/pull/262) |
| **Source**     | `juniper-cascor/src/api/app.py:678-684`; mechanism recorded at `src/api/models/common.py:83-94`                                                                                                       |
| **Primer**     | Appendix A Q58 — lines 9596-9598                                                                                                                                                                      |
| **Confidence** | High                                                                                                                                                                                                  |

**Problem.** A blanket `@app.exception_handler(ValueError)` returns `400 VALIDATION_ERROR`. `pydantic_core.PydanticSerializationError` subclasses `ValueError`, so a *server-side serialisation fault* is returned to the client as a 400 with a stripped detail.

**Impact.** Server defects are invisible to 5xx alerting and misattributed to the caller, and the generic `"Invalid request parameters"` destroys the diagnostic. The narrow workaround (`coerce_native_scalars`) is applied only inside `success_response`, so any other `ValueError`-subclass server fault is still misclassified. The failure mode is survivable only because a helper was written specifically to dodge it. `APD-DATA-034` † is the same handler in `juniper-data`, which has no equivalent workaround.

---

### APD-CCLIENT-001 — Non-idempotent methods are auto-retried with no idempotency key

|                |                                                                                             |
|----------------|---------------------------------------------------------------------------------------------|
| **Severity**   | Correctness                                                                                 |
| **Status**     | OPEN                                                                                        |
| **Source**     | `juniper-cascor-client/juniper_cascor_client/constants.py:37`; applied at `client.py:89-95` |
| **Primer**     | I.7 — lines 296, 355, 1574-1590                                                             |
| **Confidence** | High                                                                                        |

**Problem.** `RETRY_ALLOWED_METHODS = ["GET", "POST", "DELETE", "PUT", "PATCH"]` is handed to urllib3's `Retry`, so it transparently replays non-idempotent mutations on any of `[429, 502, 503, 504]`. There is no idempotency key anywhere in the stack (`APD-ECO-001`).

**Impact.** The contract violation is unambiguous: the client replays methods RFC 9110 §9.2.2 defines as non-idempotent, inside the HTTP adapter, where the caller never learns it happened. What that costs varies per call site, and the earlier framing of this entry overstated it:

- **The genuinely duplicating call site is `save_snapshot` (`client.py:295`).** A transient 502 on `POST /v1/snapshots` produces a **duplicate snapshot row** — a real, silent, unreported side effect with no server-side guard.
- **The lifecycle mutations are accidentally protected.** A replayed `POST /v1/training/start` does **not** start a second training run: cascor 409s when the FSM is not startable (`juniper-cascor/src/api/routes/training.py:117`), and `POST /v1/network` 409s likewise (`routes/network.py:31`). 409 is **not** in `RETRYABLE_STATUS_CODES`, so the replay surfaces to the caller as `JuniperCascorConflictError` — confusing, but not duplicating.

**That mitigation is accidental, not designed.** It is a property of cascor's lifecycle FSM rejecting a second start, not of any idempotency contract. It covers exactly the endpoints whose server happens to hold conflicting state, and covers `save_snapshot` not at all. Any new mutating endpoint without an FSM guard inherits the unmitigated behaviour.

**Evidence.** Both siblings carry the fix — `juniper-data-client` is `["HEAD","GET","PUT"]` with RFC 9110 §9.2.2 cited in-comment (`constants.py:59-67`), `juniper-recurrence-client` is `["HEAD","GET"]` (`constants.py:54`). cascor-client received neither. Its own `tests/test_retry_policy.py` pins the *status* forcelist and asserts nothing about the method allow-list.

---

### APD-DATA-004 — Batch-create leaks raw exception detail beside a branch that redacts it

|                |                                                                          |
|----------------|--------------------------------------------------------------------------|
| **Severity**   | Security                                                                 |
| **Status**     | **FIXED** — [juniper-data#275](https://github.com/pcalnon/juniper-data/pull/275) |
| **Source**     | `juniper-data/juniper_data/api/routes/datasets.py:423-431` vs `:433-447` |
| **Primer**     | II.8 — lines 4749-4758                                                   |
| **Confidence** | High                                                                     |

**Problem.** Two `except` blocks apply opposite disclosure policies. The `HTTPException` branch at `:423` copies `e.detail` into the per-item `error` field verbatim; the sibling `except Exception` branch **ten lines below it, at `:433`**, mints a 12-hex correlation id and returns only that, with an ERR-08 comment (`:434-437`) explaining why raw strings "can leak filesystem paths or internal type details".

**Impact.** The 501 detail at `:165-168` interpolates a raw `ImportError` message — which routinely carries a module or filesystem path — into an `HTTPException`. Batch-create's `HTTPException` branch then copies that verbatim into an API response body, defeating the ERR-08 control that sits ten lines below it in the same function.

**Correction, established while fixing it (register-original).** This entry names the amplifier, not the source, and its scope is too narrow in one respect and too wide in another.

- **Too narrow: the leak was never batch-specific.** `create_dataset` raises the `HTTPException`, so single-create returns the same detail to the caller *directly*. Reproduced on both paths. Batch-create doubles the exposure; it does not create it.
- **Too wide: the curated raises never leaked.** All four optional-dependency generators raise a hand-written message carrying an install hint (`pip install datasets`, `pip install "juniper-data[equities]"`). Those are exactly what D1 (I-5) added the 501 to surface. What leaks is an `ImportError` raised *beneath* the availability guard — a broken native extension, a partial install, a failed lazy import inside the third-party package — and those are the path-carrying ones.

**Fixed at the source, not at the amplifier.** Auditing every `detail=` in the module, exactly two interpolate exception text: the 400 `"Invalid parameters: {e}"` (a pydantic error describing the caller's own input — legitimate and unchanged) and this 501. With the 501 curated, batch-create copying `e.detail` is sound, so the `except HTTPException` branch is deliberately left alone; redacting there would have destroyed genuinely client-facing details and made batch-create diverge from single-create. The 501 now echoes the exception only when the generator's `is_available()` reports the dependency missing; otherwise it logs server-side and returns a correlation id.

---

### APD-CASCOR-005 — API-key comparison short-circuits on match in two of three copies

|                |                                                                                                                                                                 |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Severity**   | Maintainability                                                                                                                                                 |
| **Status**     | OPEN                                                                                                                                                            |
| **Confidence** | **Low — see the assessment**                                                                                                                                    |
| **Source**     | `juniper-cascor/src/api/security.py:53`; `juniper-service-core/juniper_service_core/security.py:65`; contrast `juniper-data/juniper_data/api/security.py:80-84` |
| **Primer**     | I.5 — lines 1027-1029 (the analysis); Appendix A Q26 — line 9463 (the contradicting verdict)                                                                    |

**Problem.** `juniper-data` iterates the full key list without breaking, with a comment explaining why. cascor and service-core use `any(hmac.compare_digest(api_key, k) for k in self._api_keys)`, which short-circuits.

**Assessment — this is recorded, not escalated, and it is not a Security entry.** The short-circuit occurs only on a **successful** match. Every non-matching guess still costs all N comparisons, so there is no timing gradient for an attacker to climb; what leaks is the matched key's *index* in the server's list, to a caller who already holds that key. That is weak information disclosure, not a credential leak, and `compare_digest` keeps each individual comparison constant-time.

**The primer reaches the same conclusion and says so explicitly.** At line 1029: "So service-core's form is defensible and juniper-data's is belt-and-braces… A reviewer who flags `any()` here without that analysis is pattern-matching." Under §1's inclusion criterion, a design choice the primer explicitly endorses is out of scope as a security finding — which is why the severity is `M`, not `S`.

**What is actionable is the divergence, plus a contradiction inside the primer itself.** One repo carries a documented invariant that two copies silently dropped; unify the three and decide deliberately which behaviour is intended.
Separately, the primer's own appendix contradicts its body: Q26 at 9463 states that "iterating a list of keys and short-circuiting on the first match reintroduces the leak across the *set*, so the loop must not break early", and credits "the Juniper code" with getting this right — a description true of `juniper-data` and false of the other two.
Both passages cannot stand; that is a defect in the primer, noted here so a reader citing either one knows the other exists.

---

### APD-ECO-001 — No idempotency-key mechanism exists anywhere in the stack

|                |                                   |
|----------------|-----------------------------------|
| **Severity**   | Robustness                        |
| **Status**     | OPEN                              |
| **Source**     | Ecosystem-wide; no implementation |
| **Primer**     | I.7 — lines 1592, 1660            |
| **Confidence** | High                              |

**Problem.** `grep -rn "Idempotency-Key"` across all three clients, `juniper-data`, and `juniper-service-core` returns **zero** hits. Not one occurrence anywhere — no header constant, no handler, no test, no comment naming the header.
The only acknowledgements that the concept exists at all are two prose references in `juniper-data-client`: the explanatory comment at `juniper_data_client/constants.py:65` ("their own idempotency layer") and the module docstring at `juniper-data-client/tests/test_retry_policy.py:7` ("mutations must layer their own idempotency on top").

That is a stronger finding than a single stray hit would have been: the one package that *reasoned* about idempotency concluded the caller must supply it, and no caller does.

**Impact.** Every non-idempotent `POST` in the stack duplicates on replay. `juniper-data` gets idempotent dataset creation only incidentally, via content-addressed IDs. This is the enabling condition for `APD-CCLIENT-001`: without a key, retrying a mutation cannot be made safe.

---

## 4. Full register

`Sev` — **S**ecurity, **C**orrectness, **R**obustness, **M**aintainability, **E**rgonomics. `Conf` — confidence. All statuses OPEN unless stated. `Primer` gives the line in the primer asserting the claim; `Source` gives the current `file:line`. A `†` after an ID marks a **register-original** entry (see §1).

### 4.1 `juniper-data`

| ID             | Finding                                                                                                                                | Sev | Source                                                                   | Primer                | Conf |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------|-----|--------------------------------------------------------------------------|-----------------------|------|
| APD-DATA-001 † | **FIXED (#266)** — 401 path unthrottled — the `#1082` fix never reached this copy                                                      | S   | `api/middleware.py:110-150`                                              | 1058 (mechanism)      | High |
| APD-DATA-002   | **FIXED (#261)** — Body limit bypassable by chunked request with no `Content-Length`                                                   | S   | `api/middleware.py:79-83`                                                | 757                   | High |
| APD-DATA-003   | **FIXED (#267)** — Blank API key enables auth that accepts an empty key                                                                | S   | `api/security.py:54`, `api/settings.py:155-160`                          | 1041                  | High |
| APD-DATA-004   | **FIXED (#275)** — Batch-create echoes raw `e.detail` beside a redacting branch                                                        | S   | `api/routes/datasets.py:423-431` vs `:433-447`                           | 4749                  | High |
| APD-DATA-005   | `APIKeyHeader` declared but never wired — no `securitySchemes` in OpenAPI                                                              | M   | `api/security.py:26`                                                     | 1062, 5199            | High |
| APD-DATA-006   | **FIXED (#263)** — `record_access` lock asymmetry — a `GET` can undo a tag edit                                                        | C   | `storage/base.py:217-222`                                                | 4197                  | High |
| APD-DATA-007   | Tag update is read-modify-write with no CAS or version check                                                                           | C   | `api/routes/datasets.py:785-794`, `storage/local_fs.py:262-298`          | 4171                  | High |
| APD-DATA-008   | Cache hit returns 201 — status line cannot signal "already existed"                                                                    | E   | `api/routes/datasets.py:71`, `:120-139`                                  | 3836                  | High |
| APD-DATA-009   | Batch-create returns 201 even when every item failed                                                                                   | C   | `api/routes/datasets.py:377`                                             | 4785                  | High |
| APD-DATA-010   | Batch export silently skips datasets deleted mid-stream                                                                                | C   | `api/routes/datasets.py:570-572`                                         | 4087                  | High |
| APD-DATA-011   | Offset pagination drifts — skips and duplicates under concurrent writes                                                                | C   | `storage/local_fs.py:253-255`, `storage/base.py:376-378`                 | 4412                  | High |
| APD-DATA-012   | `/filter` tie order is non-deterministic (unsorted glob feeds a stable sort)                                                           | C   | `storage/base.py:376`, `storage/local_fs.py:300-312`                     | 4470                  | High |
| APD-DATA-013   | Two incompatible `detail` shapes — no `RequestValidationError` handler                                                                 | C   | `api/app.py:152-166`                                                     | 4728                  | High |
| APD-DATA-014   | 400 vs 422 split falls out of exception-subclass MRO, not design                                                                       | C   | `api/routes/datasets.py:106-112`                                         | 3910, 4742-4747       | High |
| APD-DATA-015   | Route ordering is load-bearing and unguarded (`/{dataset_id}` catch-all)                                                               | R   | `api/routes/datasets.py:276`, `:338`, `:604`, `:628`, `:651`             | 3455                  | High |
| APD-DATA-016   | `download_artifact` is named streaming but fully materialises the body                                                                 | R   | `api/routes/datasets.py:693-704`                                         | 3999                  | High |
| APD-DATA-017   | No `ETag`/`Cache-Control`/conditional requests despite a stored SHA-256                                                                | R   | `api/routes/datasets.py:700-704`; validator at `core/artifacts.py:50-63` | 3647                  | High |
| APD-DATA-018   | No async job pattern — generation runs inside the request                                                                              | R   | `api/routes/datasets.py:150`                                             | 3853                  | High |
| APD-DATA-019   | Every page does full-population work; exact `total` recomputed per page                                                                | R   | `storage/base.py:348-378`                                                | 4390                  | High |
| APD-DATA-020   | `/v1` is a repeated literal in five places; no `API_VERSION` constant                                                                  | M   | `api/app.py:140-142`, `api/routes/datasets.py:138`, `:253`               | 3278                  | High |
| APD-DATA-021   | `DatasetListFilter` declared and never used; route re-declares 12 params                                                               | M   | `core/models.py:132-144` vs `api/routes/datasets.py:278-289`             | 4538                  | High |
| APD-DATA-022   | No `responses={}` anywhere — entire error surface absent from OpenAPI                                                                  | M   | all route decorators                                                     | 5189                  | High |
| APD-DATA-023   | No `operation_id=` — a handler rename renames every generated SDK method                                                               | M   | all route decorators                                                     | 5157                  | High |
| APD-DATA-024   | Securing the service deletes `/openapi.json`, not just the explorers                                                                   | M   | `api/app.py:91`, `:97-99`                                                | 1065, 5207            | High |
| APD-DATA-025   | `application/octet-stream` on one binary route, `application/zip` on the other                                                         | M   | `api/routes/datasets.py:702` vs `:584`                                   | 4017                  | Med  |
| APD-DATA-026   | Two list endpoints, same params, incompatible shapes                                                                                   | E   | `api/routes/datasets.py:257-273` vs `:276-335`                           | 4535                  | High |
| APD-DATA-027   | No `Link` header or pagination links anywhere                                                                                          | E   | `api/routes/datasets.py:276-335`                                         | 5002                  | High |
| APD-DATA-028   | `/versions` and `/latest` smuggle identity into a mandatory query param                                                                | E   | `api/routes/datasets.py:606`, `:630`                                     | 3408                  | Low  |
| APD-DATA-029   | Two URIs return the same representation with no `Content-Location`                                                                     | E   | `api/routes/datasets.py:628`, `:651`                                     | 3399                  | Low  |
| APD-DATA-030   | Error bodies carry no retryability signal                                                                                              | E   | `api/app.py:152-166`                                                     | 3316                  | Low  |
| APD-DATA-031   | No RFC 9457 problem details; three independent error sources                                                                           | E   | `api/app.py`, `api/middleware.py`, routes                                | 4718                  | Low  |
| APD-DATA-032   | Access counters live in the representation, blocking a strong metadata `ETag`                                                          | E   | `core/models.py:84-85`, `api/routes/datasets.py:672`                     | 4247                  | Low  |
| APD-DATA-033   | Rate-limit window is the one knob of three an operator cannot set                                                                      | E   | `api/app.py:123-126`, `api/settings.py:164-165`                          | 1380                  | Low  |
| APD-DATA-034 † | **FIXED (#262)** — Blanket `ValueError` handler reports server faults as `400` — and no `coerce_native_scalars` equivalent exists here | C   | `api/app.py:152-158`                                                     | 9596 (cascor sibling) | High |
| APD-DATA-035 † | **FIXED (#273)** — CORS registered innermost → `SecurityMiddleware` 401s preflights; path-only `_is_exempt`                            | C   | `api/app.py:104-138`, `api/middleware.py:152-160`                        | 9592 (cascor sibling) | High |
| APD-DATA-036   | **FIXED (#261)** — Unguarded `int(content_length)` — `Content-Length: abc` is a 500, not a 400                                         | R   | `api/middleware.py:81`                                                   | 758                   | High |

**`APD-DATA-005` cross-reference.** `APD-DATA-024` nullifies it further: because `openapi_url` is `None` whenever any API key is configured (`api/app.py:91`, `:99`), a secured deployment serves **no OpenAPI document at all** — so the missing `securitySchemes` block is unobservable exactly where it would matter. The severity is `M`, not `S`: there is no attacker and no gain, only an absent schema stanza. `api_key_header` is instantiated at `api/security.py:26` and referenced nowhere else in the repository.

**`APD-DATA-033` restated.** `DEFAULT_RATE_LIMIT_WINDOW_SECONDS` is **not** an unwired constant — it is load-bearing at `api/security.py:128` (constructor default), `:139` (`self._window`), `:147` (cache TTL) and `:163-165` (the `window` property).
The defect is narrower and real: `RateLimiter` is constructed at `api/app.py:123-126` passing only `requests_per_minute` and `enabled`, and `Settings` declares only `rate_limit_enabled` / `rate_limit_requests_per_minute` (`api/settings.py:164-165`). The window is the one knob of three with no operator-facing setting.

**`APD-DATA-036` mechanism.** `RequestBodyLimitMiddleware` is a `BaseHTTPMiddleware`, so a `ValueError` raised in its `dispatch` propagates *outside* `ExceptionMiddleware` and never reaches the app's `@app.exception_handler(ValueError)` at `api/app.py:152`; it lands on the `Exception` handler at `:160-166`, a 500. Both siblings return an explicit 400 instead — `juniper-cascor/src/api/middleware.py:96-97`, `juniper-service-core/juniper_service_core/middleware.py:107-110`.

### 4.2 `juniper-service-core`

**Consumer reality — read this before triaging anything below.** The shared package is *partially* adopted, and which module an entry lives in decides whether it is live or latent. Verified by grepping every service's production tree for `juniper_service_core`:

- **`.middleware` and `.security` have exactly one production consumer: `juniper-recurrence`.** `juniper_recurrence/app.py:26-34` imports `RequestBodyLimitMiddleware`, `SecurityHeadersMiddleware`, `SecurityMiddleware`, `build_api_key_auth`, `build_rate_limiter` and `create_app`; the lazy map at `__init__.py:211-217` resolves those to `juniper_service_core.middleware` / `.security`.
  `APD-SVCCORE-004` and `-007` are therefore **live in production for recurrence**, and latent for everyone else. juniper-data, juniper-cascor and juniper-canopy each carry their own middleware and import none of it.
- **`.websocket.*` and `workers/` have no production consumer at all.** No service imports `control_stream`, `worker_stream`, `training_stream`, `control_security`, `commands` or `coordinator`. The nine entries rooted there — `-001`, `-003`, `-005`, `-010`, `-011`, `-012`, `-013`, `-015`, `-016` — are **latent library defects, not live exposure.** They become live if and when the wider service-core migration lands, which is exactly the loop §2.2 closes on.
- **Package-root and boot-check entries are live for every consumer** — `-006`, `-008`, `-009`, `-014`, `-017` — because `enforce_auth_posture`, `enforce_dependency_floors`, `SettingsBase`, `get_secret` and `TrainingLifecycle` are imported by juniper-data, juniper-cascor, juniper-canopy and juniper-recurrence respectively.

| ID              | Finding                                                                                    | Sev | Source                                                                                       | Primer     | Conf |
|-----------------|--------------------------------------------------------------------------------------------|-----|----------------------------------------------------------------------------------------------|------------|------|
| APD-SVCCORE-001 | No cumulative cap across a worker-declared attachment list (`N ×` per-frame cap)           | R   | `websocket/worker_stream.py:323`, `:329`                                                     | 754        | High |
| APD-SVCCORE-003 | **FIXED (ml#1154)** — `_setting` silently defaults on a typo — including security controls | S   | `websocket/control_stream.py:66-69` (13 across both copies)                                  | 7950, 7964 | High |
| APD-SVCCORE-004 | `Retry-After` truncates toward zero → `Retry-After: 0` tight retry loop                    | R   | `security.py:205`                                                                            | 1409       | High |
| APD-SVCCORE-005 | Control-WS 64 KB cap checked after the frame is materialised                               | R   | `websocket/control_stream.py:191-199`                                                        | 822        | High |
| APD-SVCCORE-006 | No package base exception; 3 of 6 derive from `RuntimeError`                               | R   | `auth_posture.py:51`, `dependency_floors.py:57`, `workers/registry.py:31`, +3                | 6918       | High |
| APD-SVCCORE-007 | Rate limiter is per-process — a documented constraint, not an oversight                    | R   | `security.py:99-104`, `:125-127`                                                             | 1275, 9448 | Low  |
| APD-SVCCORE-008 | No `py.typed` — all annotations and the 75-line `TYPE_CHECKING` block discarded            | M   | package root; `pyproject.toml`; `__init__.py:38-112`                                         | 7598, 7615 | High |
| APD-SVCCORE-009 | Three parallel name lists (`__all__`, `_LAZY_EXPORTS`, `TYPE_CHECKING`), no guard          | M   | `__init__.py:38-112`, `:114-192`, `:197-272`                                                 | 6398       | High |
| APD-SVCCORE-010 | **FIXED (ml#1154)** — `_setting` duplicated byte-identically in two modules                | M   | `websocket/control_stream.py:66-69`, `websocket/training_stream.py:44-47`                    | 7968       | High |
| APD-SVCCORE-011 | Two Protocols use incompatible member conventions                                          | M   | `workers/coordinator.py:93-120` vs `websocket/commands.py:38-57`                             | 7944       | Med  |
| APD-SVCCORE-012 | `LifecycleCommandExecutor` subclassing neither supported nor forbidden                     | M   | `websocket/commands.py:60-68`                                                                | 8089       | Med  |
| APD-SVCCORE-013 | `LeakyBucket` is a token bucket — name and docstring both wrong                            | M   | `websocket/control_security.py:53-79`                                                        | 1247       | Low  |
| APD-SVCCORE-014 | `DependencyFloorError` discards the structured `FloorViolation` list                       | E   | `dependency_floors.py:213-217`                                                               | 7005       | High |
| APD-SVCCORE-015 | `WorkerTaskProtocol` ships no default implementation                                       | E   | `workers/coordinator.py:93-120`                                                              | 8058       | Med  |
| APD-SVCCORE-016 | Pre-accept close codes are discarded — every rejected handshake looks like an opaque 403   | E   | `websocket/control_stream.py:100`, `:107`, `:118`, `:234`, `:241`; `websocket/manager.py:73` | 849        | Low  |
| APD-SVCCORE-017 | `__dir__` returns exactly `__all__`, hiding module dunders                                 | E   | `__init__.py:290-291`                                                                        | 6400       | Low  |

**`APD-SVCCORE-016` restated — the previous wording was a false positive.** The entry formerly claimed the handshake gates "close after accepting rather than refusing the upgrade". The opposite is true: `control_stream_handler` calls `_check_handshake_gates` at `:234` and returns on failure at `:235`, six lines *before* `await websocket.accept()` at `:241`. All four rejection paths are correctly pre-accept.

The real defect at those lines is that the distinct close codes never reach the client. uvicorn converts a pre-accept close into a plain **HTTP 403** and discards both the code and the reason, so `1013` ("Control endpoint disabled", `:100`), `4029` ("Too many rejected handshakes", `:107`), `4003` ("Origin not allowed", `:118`) and `4001` ("Authentication required", `websocket/manager.py:73`) are all indistinguishable to the caller.
Four carefully chosen, individually meaningful codes collapse into one opaque status — a client cannot tell a kill switch from a cooldown from an Origin rejection from a bad key, and cannot decide whether to retry.

**`APD-SVCCORE-008` counts.** The register earlier cited a "62-name `TYPE_CHECKING` block". Against source today the block spans `__init__.py:38-112` — **75 lines, 62 imported names** — with a 62-entry `_LAZY_EXPORTS` (`:197-272`) and a 63-name `__all__`. The primer's figures ("73-line", 7615; "60 lazy names", 6343) describe an earlier revision; the source numbers above are the current ones.

### 4.3 `juniper-cascor`

| ID               | Finding                                                                                        | Sev | Source                                                        | Primer              | Conf |
|------------------|------------------------------------------------------------------------------------------------|-----|---------------------------------------------------------------|---------------------|------|
| APD-CASCOR-004 † | **FIXED (#524)** — 401 path unthrottled — the `#1082` fix never reached this copy              | S   | `src/api/middleware.py:147-186`                               | 1058 (mechanism)    | High |
| APD-CASCOR-006 † | **FIXED (#527)** — Blank API key enables auth that accepts an empty key — no `.strip()` filter | S   | `src/api/security.py:32-33`                                   | 1041 (data sibling) | High |
| APD-CASCOR-001a  | **FIXED (#540)** — Middleware order comment is wrong (omits `RequestBodyLimitMiddleware`)      | M   | `src/api/app.py:644-646`, `:630`                              | 9592                | High |
| APD-CASCOR-001b  | **FIXED (#540)** — CORS innermost → `SecurityMiddleware` answers preflights 401                | C   | `src/api/app.py:621`, `:641`; `src/api/middleware.py:189-198` | 9592                | High |
| APD-CASCOR-002   | **FIXED (#516)** — `ValueError` handler reclassifies serialisation faults as `400`             | C   | `src/api/app.py:678-684`                                      | 9596                | High |
| APD-CASCOR-003   | 46 of 47 routes declare no `response_model`                                                    | M   | `src/api/routes/` (only `health.py:130`)                      | 7761                | High |
| APD-CASCOR-005   | Key comparison short-circuits on match in 2 of 3 copies (see §3 assessment)                    | M   | `src/api/security.py:53`                                      | 1027-1029, 9463     | Low  |

**`APD-CASCOR-006` detail.** `self._api_keys: set[str] = set(api_keys) if api_keys else set()` (`:32`) followed by `self._enabled = len(self._api_keys) > 0` (`:33`). A configured `[""]` therefore enables authentication and `validate("")` succeeds via `hmac.compare_digest("", "")`. `juniper-service-core/juniper_service_core/security.py:44` carries the blank filter with a comment naming exactly this failure; neither cascor nor juniper-data received it.
Same reachability caveat as `APD-DATA-003`: the boot-time `enforce_auth_posture` check filters blanks, so triggering this needs auth-posture enforcement disabled. **FIXED** in [juniper-cascor#527](https://github.com/pcalnon/juniper-cascor/pull/527) — the `security.py` line is now byte-identical to the canonical service-core filter, and `_parse_api_keys`'s list branch filters too.

### 4.4 `juniper-cascor-client`

| ID              | Finding                                                                                       | Sev | Source                                                                                             | Primer     | Conf |
|-----------------|-----------------------------------------------------------------------------------------------|-----|----------------------------------------------------------------------------------------------------|------------|------|
| APD-CCLIENT-001 | Retries `POST`/`DELETE`/`PATCH` with no idempotency key                                       | C   | `constants.py:37`, `client.py:89-95`                                                               | 296        | High |
| APD-CCLIENT-002 | `JuniperCascorServiceUnavailableError` is unreachable dead code                               | C   | `exceptions.py:40-43`, `client.py:411-412` (dead branch), `:371` (interception), `constants.py:36` | 7041       | High |
| APD-CCLIENT-004 | Exceptions carry no `status_code` / `response` / `detail` — so 400 and 422 are byte-identical | C   | `exceptions.py:4-49`; `client.py:404-414`                                                          | 6961, 6979 | High |
| APD-CCLIENT-005 | No base-URL normalisation or validation at all                                                | R   | `client.py:82-83`                                                                                  | 6691       | High |
| APD-CCLIENT-006 | `_dispatch` unguarded — one raising listener tears down the stream                            | R   | `ws_client.py:453-457` vs `:459-471`                                                               | 7141       | High |
| APD-CCLIENT-007 | mypy targets 3.11 while the package requires ≥3.12                                            | M   | `pyproject.toml:90` vs `:12`                                                                       | 7625       | High |
| APD-CCLIENT-008 | Sniffs two error envelopes, encoding fleet drift rather than surfacing it                     | M   | `client.py:393-402`                                                                                | 4773       | High |
| APD-CCLIENT-009 | `pool_connections` omitted where both siblings set it                                         | M   | `client.py:95`                                                                                     | 269        | High |
| APD-CCLIENT-010 | Redundant `pass` after a docstring in all 8 exception classes                                 | M   | `exceptions.py`                                                                                    | 6888       | Med  |
| APD-CCLIENT-011 | `create_network(**kwargs: Any)` — 11 real parameters, none typed                              | E   | `client.py:138-154`                                                                                | 6565       | High |
| APD-CCLIENT-012 | `auto_pong` is a positional boolean trap with no removal date                                 | E   | `ws_client.py:244-250`                                                                             | 7407       | High |
| APD-CCLIENT-013 | `backoff_factor` hardcoded, not constructor-configurable                                      | E   | `client.py:91`                                                                                     | 1577       | High |

**Retired ID.** `APD-CCLIENT-003` ("status dropped on 4 of 5 branches — 400 and 422 are byte-identical") was **merged into `APD-CCLIENT-004`**. They are one defect in `_handle_response` (`client.py:404-414`) with one fix: 400 and 422 both raise `JuniperCascorValidationError(error_msg)` and are indistinguishable *because* the exception type carries no `status_code`. Give the exception hierarchy a `status_code` and both halves close together. **The number `APD-CCLIENT-003` is retired and must not be reused.**

**`APD-CCLIENT-002` detail.** `RETRYABLE_STATUS_CODES` includes 503 (`constants.py:36`), so urllib3's `Retry` exhausts and raises through `requests`, which surfaces as a `requests.RequestException` and is caught at `client.py:371` — converting it to `JuniperCascorClientError` before `_handle_response` is ever reached. The 503 branch at `client.py:411-412`, and therefore `JuniperCascorServiceUnavailableError` itself, is unreachable.

**`APD-CCLIENT-005` restated.** The earlier wording claimed "a documented base URL yields `/v1/v1/...`"; no documented cascor base URL carries a `/v1` suffix, so that clause is dropped.
What reproduces is broader: `self.base_url = base_url.rstrip("/")` (`:82`) is the *entire* treatment. `grep -rn "urlparse\|urlsplit\|netloc"` across `juniper-cascor-client/` returns **zero** hits — no scheme defaulting, no path normalisation, no `/v1` suffix strip, and no `netloc` validation.
`juniper-data-client` normalises via `urlparse` (`client.py:180-201`) but never checks `netloc`; `juniper-recurrence-client` normalises *and* validates (`client.py:182-185`). cascor-client therefore also carries the hostless-URL gap that §2.3's sibling-drift table pairs it with — it is the only client with neither guard.

### 4.5 `juniper-data-client`

| ID              | Finding                                                                         | Sev | Source                                                                                                                                            | Primer | Conf |
|-----------------|---------------------------------------------------------------------------------|-----|---------------------------------------------------------------------------------------------------------------------------------------------------|--------|------|
| APD-DCLIENT-001 | Exceptions carry no `status_code` / `response` / `detail`                       | C   | `exceptions.py:4-37`, `client.py:312-320`                                                                                                         | 6961   | High |
| APD-DCLIENT-002 | Public `validate_npz_contract` raises bare `ValueError`, escaping the hierarchy | C   | `contract.py:66`, exported `__init__.py:8`, `:15`                                                                                                 | 6931   | High |
| APD-DCLIENT-003 | A 422 `detail` list is f-string-interpolated into an unparseable repr           | C   | `client.py:306`, `:313-319`                                                                                                                       | 4771   | High |
| APD-DCLIENT-004 | `_normalize_url` never validates `netloc` — hostless URL fails opaquely         | R   | `client.py:180-201`                                                                                                                               | 6689   | Med  |
| APD-DCLIENT-005 | Version literal drifted across six file headers (0.4.0 / 0.4.1 / 0.3.2)         | M   | `constants.py:12`, `contract.py:21`, `testing/__init__.py:7`, `testing/generators.py:7`, `testing/fake_client.py:7`, `tests/test_versioning.py:7` | 7332   | High |
| APD-DCLIENT-006 | `validate_npz_contract -> str` where a `Literal` is available                   | M   | `contract.py:41`                                                                                                                                  | 6625   | High |
| APD-DCLIENT-007 | Redundant `pass` after a docstring in all 6 exception classes                   | M   | `exceptions.py`                                                                                                                                   | 6888   | Med  |
| APD-DCLIENT-008 | `create_dataset` — 9 positional-or-keyword params, 3rd a bare boolean           | E   | `client.py:412-423`                                                                                                                               | 6592   | High |

**`APD-DCLIENT-005` count corrected.** The primer names **six** drifted file headers at 7332-7337, not four: the earlier entry omitted `testing/generators.py:7` and `testing/fake_client.py:7`. All six verified against source — `contract.py:21` reads `0.4.1`, `tests/test_versioning.py:7` reads `0.3.2`, and the remaining four read `0.4.0`, while `pyproject.toml` and `__init__.py` agree on the real version. Three distinct values across six decorative copies.

### 4.6 `juniper-recurrence-client`

| ID              | Finding                                                                          | Sev | Source                                                       | Primer | Conf |
|-----------------|----------------------------------------------------------------------------------|-----|--------------------------------------------------------------|--------|------|
| APD-RCLIENT-001 | Exceptions carry no `status_code` / `response` / `detail`                        | C   | `client.py:260-271`, `exceptions.py:10-36`                   | 6961   | High |
| APD-RCLIENT-002 | 30 s scalar timeout governs synchronous `train`/`crossval`; no per-call override | R   | `client.py:217`, `:311`, `:405`                              | 1635   | High |
| APD-RCLIENT-003 | Ships `py.typed` and the `Typing :: Typed` classifier with no mypy config        | M   | `pyproject.toml:61-62`, `:25`                                | 7620   | High |
| APD-RCLIENT-004 | Client returns `dict[str, Any]` while the same-repo server declares models       | M   | `client.py:310`, `:404` vs `juniper_recurrence/routers/*.py` | 7768   | Med  |
| APD-RCLIENT-005 | Repository, distribution and import names are three different strings            | M   | `pyproject.toml:49-52`                                       | 8188   | Low  |

### 4.7 `juniper-observability`

| ID          | Finding                                                                                           | Sev | Source                                              | Primer     | Conf |
|-------------|---------------------------------------------------------------------------------------------------|-----|-----------------------------------------------------|------------|------|
| APD-OBS-001 | **FIXED (ml#1156)** — `X-Request-ID` accepted unvalidated — contained by h11, not by this package | M   | `middleware/request_id.py:36`, `:40`                | 1109, 2101 | Med  |
| APD-OBS-002 | No `py.typed` — every consumer sees `[import-untyped]`                                            | M   | package root; `pyproject.toml`                      | 7598       | High |
| APD-OBS-003 | `register_info_or_update -> Any` beside three siblings returning `T`                              | M   | `prometheus_helpers.py:214-218`                     | 7669       | Med  |
| APD-OBS-004 | Two `__all__` lists must agree; nothing checks it                                                 | M   | `middleware/__init__.py:13-22`, `__init__.py:52-90` | 6250       | Med  |

### 4.8 Cross-client, ecosystem and meta

| ID          | Finding                                                                        | Sev | Source                                                                                                                                       | Primer    | Conf |
|-------------|--------------------------------------------------------------------------------|-----|----------------------------------------------------------------------------------------------------------------------------------------------|-----------|------|
| APD-ECO-001 | No `Idempotency-Key` mechanism anywhere in the stack — zero occurrences        | R   | ecosystem-wide                                                                                                                               | 1592      | High |
| APD-ECO-002 | No retry jitter in any of the three clients — synchronised retry storms        | R   | all three `client.py` `Retry(...)` sites                                                                                                     | 346       | High |
| APD-ECO-003 | One flat 30 s scalar timeout in all three clients; no per-call override        | R   | data `client.py:248`, cascor `:363`, recurrence `:217`                                                                                       | 378       | High |
| APD-ECO-004 | 45+ public methods return `Dict[str, Any]`; zero `TypedDict`, zero `@overload` | M   | all three `client.py`                                                                                                                        | 6709      | High |
| APD-ECO-005 | No version-lockstep test in any client repo                                    | M   | all three `tests/`                                                                                                                           | 7339      | High |
| APD-ECO-006 | No client type-checks a consumer-shaped probe                                  | M   | `juniper-data-client/.pre-commit-config.yaml:167`, `juniper-cascor-client/.pre-commit-config.yaml:167`; recurrence-client has no mypy config | 7676      | Low  |
| APD-ECO-007 | Neither shared package has any deprecation machinery                           | E   | `juniper_service_core/`, `juniper_observability/`                                                                                            | 7421      | Low  |
| APD-ML-001  | First-party pins inconsistently capped; the pattern is coherent but unstated   | M   | `juniper-ml/pyproject.toml:30-31`, `:34`, `:47-49`, `:52`, `:56`                                                                             | 7445-7446 | Low  |

**`APD-ECO-006` restated.** The earlier wording ("no `strict = true` in all three `pyproject.toml`") contradicted itself and is false: **two of three do** configure it — `juniper-data-client/pyproject.toml:88-93` and `juniper-cascor-client/pyproject.toml:89-94` both declare `[tool.mypy]` with `strict = true`.
The real gap is what those checkers are pointed at. Both pre-commit hooks scope mypy to `^juniper_<pkg>_client/(?!testing/).*\.py$` — library-internal source only, never a file that *imports* the package the way a consumer would. `juniper-recurrence-client` configures no mypy at all and has no `.pre-commit-config.yaml`.
So no client verifies that its own published type surface is usable from outside, which is the failure `APD-OBS-002` and `APD-SVCCORE-008` would have caught.

**`APD-ML-001` restated, and downgraded.** The earlier wording — "8 first-party pins uncapped, contradicting the file's own stated policy" — overstated the primer twice. The primer says at 7445-7446 that "the pattern is coherent even if **never stated as policy**": there is no stated policy to contradict. And it states no count of 8; its table has three uncapped rows across six packages. The count of 8 is this register's re-verification (register-derived), not an extraction.

Two further reasons this is Low confidence and probably not actionable: those exact eight pin strings are **byte-for-byte asserted by a passing lint** (`tests/test_pyproject_extras.py:106-125`), so "fixing" them means editing the contract test in the same PR;
and capping first-party pins on a meta-package fed by a **daily release train** would make `juniper-ml` a permanent release bottleneck — every sibling `0.y` bump would need a meta PR before it could be installed together. Record it; do not action it without deciding the release-train question first.

---

## 5. Fixed findings (before and since the primer)

Recorded so the register is not read as a list of live problems that includes resolved ones.

### 5.1 Fixed since this register was published (2026-08-14)

These sixteen carry their **original IDs** — they were counted in the 96, and are marked `FIXED` in place at their §4 table row and detail entry rather than renumbered or removed, so a reader following an existing reference still lands on the right entry and sees why it is closed. Working the §2.2 list is what produced the first of them, and it is now worked through: all four of its items are closed. The §2.3 copy-drift list is now worked through too.

| ID | Finding | Fixed by | Verification |
| --- | --- | --- | --- |
| APD-DATA-003 | Blank API key enabled auth that then accepted an empty `X-API-Key` | [juniper-data#267](https://github.com/pcalnon/juniper-data/pull/267) | `APIKeyAuth.__init__` filters blanks / whitespace-only / non-string entries before deriving `_enabled`; `_parse_api_keys`'s list branch filters too, closing the string-vs-list inconsistency that made the JSON form the reachable shape. Keeps the `list` container deliberately (`hmac.compare_digest` per key, SEC-01/JD-SEC-02) rather than adopting service-core's `set`. 13 arms added; one of them caught a real ordering bug in the first draft -- `dict.fromkeys` hashes every element, so filtering after it raises `TypeError` on an unhashable entry. Fixed at the point of use rather than relying on the boot-time `enforce_auth_posture` check, which can be disabled. |
| APD-DATA-001 † | 401 path unthrottled — the `#1082` fix never reached this copy; the register's #4 item | [juniper-data#266](https://github.com/pcalnon/juniper-data/pull/266) | `FailedAuthThrottle` ported into `api/security.py`; `check()` runs before authentication and `record_failure()` is gated on a 401. **Ported, not consolidated** — §2.2's loop warning about `APD-SVCCORE-003` still governs. Mirrors service-core's optional fourth constructor parameter defaulting to an *enabled* throttle, so `app.py` was unchanged and no settings field was added. 13 arms added; the half-port that matters is caught by mutation — deleting the single `record_failure` line fails 3 of them. Full suite 1173 passed. |
| APD-DATA-002 | Body cap bypassable by a chunked request with no `Content-Length` — the register's #1 item | [juniper-data#261](https://github.com/pcalnon/juniper-data/pull/261) | `POST`/`PUT`/`PATCH` always stream-read against a cumulative cap, aborting 413 mid-stream; `Content-Length` demoted to an early-reject hint. Seven tests added where there had been **no** body-limit coverage at all; the two bypass shapes are driven at the ASGI layer because httpx recomputes `Content-Length` and cannot express them. Ports the implementation already shipping in cascor and service-core. |
| APD-CASCOR-002 | Blanket `ValueError` handler reported serialisation faults as `400` | [juniper-cascor#516](https://github.com/pcalnon/juniper-cascor/pull/516) | `PydanticSerializationError` is classified 500 and logged at exception level; a plain `ValueError` still returns 400, so the existing `test_value_error_handler` passes unchanged — the handler was narrowed, not redefined. `coerce_native_scalars` remains as the cheap pre-emption for the numpy-scalar path. |
| APD-SVCCORE-003 | `_setting` silently defaulted a misspelled settings field — six of the eleven tunables are security controls | ml#1154 | `websocket/tunables.py` declares all eleven with defaults + a `security` flag; both handlers resolve through it. The decoupling is kept (no import of a service settings class); what changes is that the default is declared rather than repeated at 13 call sites, and a near-miss on the settings object is logged at WARNING naming both spellings — |
| | | | the `..._per_second` case now produces a log line instead of silence. `audit(settings)` reports defaulted security controls and suspected typos at boot; an undeclared name raises. Verified by mutation: deleting the near-match lookup fails the warning arm. |
| APD-OBS-001 | `X-Request-ID` accepted unvalidated into a process-wide ContextVar and echoed back | ml#1156 | 128-char cap + anchored allowlist `[A-Za-z0-9._:-]` on ingress; a failing value is **replaced** with a fresh UUID4, not sanitized — a stripped value would correlate to nothing on either side. Rejection is silent on purpose (logging it is the log-flood lever the guard bounds). UUID / ULID / W3C `traceparent` / `service:id` all still pass, pinned by tests. |
| | | | Moves the containment from h11's incidental defaults into this package. Mutation: a always-true validator fails 7 arms. |
| APD-SVCCORE-010 | `_setting` duplicated byte-identically in two modules | ml#1154 | Closed by the same change — one shared resolver, two thin delegating wrappers. A source-scan test asserts neither handler re-implements the `getattr(settings, name, default)` body, so the duplication cannot grow back. |
| APD-DATA-006 | `record_access` could write a pre-edit snapshot over a committed tag edit | [juniper-data#263](https://github.com/pcalnon/juniper-data/pull/263) | New `DatasetStore.update_tags` performs the whole read-modify-write inside the same `_version_lock`, in one thread hop. The test uses `LocalFSDatasetStore` deliberately — `InMemoryDatasetStore.get_meta` returns the very object it stores, so both writers mutate one instance and the lost write **cannot be expressed**; a test written against the convenient store would have passed on the broken code. |
| APD-DATA-036 | Unguarded `int(content_length)` surfaced a malformed client header as a 500 | [juniper-data#261](https://github.com/pcalnon/juniper-data/pull/261) — same patch, as this register predicted | Returns an explicit 400. Reproduced before fixing: the raw `ValueError` escapes to starlette's `ServerErrorMiddleware`, confirming it never reaches the app's own `ValueError` handler. |
| APD-CASCOR-006 † | The same gap in juniper-cascor's copy | [juniper-cascor#527](https://github.com/pcalnon/juniper-cascor/pull/527) | Same fix; this fork already used a `set`, so the `security.py` line is byte-identical to the canonical service-core filter. 11 arms added, complementing the request-side coverage this fork already had (`test_validate_empty_string_key_is_invalid`) with the configuration side -- a blank key must never become a valid credential in the first place. The settings half was caught here by its own new test after a first pass updated only the docstring. |
| APD-DATA-034 † | The same handler in juniper-data, which had **no** `coerce_native_scalars` equivalent | [juniper-data#262](https://github.com/pcalnon/juniper-data/pull/262) | Same narrowing. This was the worse of the two: with no helper standing in the way, every serialisation fault here was reported as a client error. Both fixes confirmed to bite by reverting them (`assert 400 == 500`). |
| APD-CASCOR-004 † | The same gap in juniper-cascor's copy | [juniper-cascor#524](https://github.com/pcalnon/juniper-cascor/pull/524) | Same port, same shape, same mutation check. One pre-existing test needed isolating rather than weakening: `test_failed_auth_does_not_increment_rate_limit` fires **exactly** the default budget of 10 failed attempts and then asserts a valid key passes, so it now builds a generous throttle and keeps measuring the *identity-keyed limiter's* counters. That interaction is correct behaviour, not a regression — once an IP burns its failed-attempt budget it is throttled at the door regardless of the next credential, because `check()` necessarily precedes knowing the key is good. |
| APD-DATA-035 † | CORS registered innermost, so `SecurityMiddleware` answered every browser preflight 401 | [juniper-data#273](https://github.com/pcalnon/juniper-data/pull/273) | Fixed by **reordering** the middleware — CORS registered last, so it executes outermost — not by an `OPTIONS` bypass in `_is_exempt`, which would have exempted every `OPTIONS` request from auth *and* rate limiting. CORS short-circuits only a genuine preflight (one carrying `Access-Control-Request-Method`), so a plain `OPTIONS` still authenticates; that distinction is pinned as its own test. Reproduced first: `OPTIONS /v1/generators` with a valid `Origin` returned 401 and no `Access-Control-Allow-Origin`. Negative control confirms the reorder did **not** widen the origin allowlist — a preflight from a disallowed origin still gets 400 with no ACAO. 5 arms added; mutation-tested, 4 of the 5 fail against the unfixed ordering (the fifth guards the OPTIONS-bypass alternative and holds either way, by design). |
| APD-CASCOR-001b | The same defect in juniper-cascor's copy | [juniper-cascor#540](https://github.com/pcalnon/juniper-cascor/pull/540) | Same reorder, same five arms, same 4-of-5 mutation result, verified on the real non-exempt route `/v1/network/stats`. Both forks also gained a **second** fix the original entries did not name: with CORS innermost an ordinary cross-origin request rejected by auth carried no CORS headers either, so a browser saw an opaque CORS failure rather than the real 401. |
| APD-CASCOR-001a | Middleware ordering comment omitted `RequestBodyLimitMiddleware` | [juniper-cascor#540](https://github.com/pcalnon/juniper-cascor/pull/540) | Folded into `001b` rather than shipped separately as the register anticipated: a reorder cannot land beside an ordering comment it has just made doubly wrong. The identical comment existed in `juniper-data` — an unrecorded sibling, since this ID was filed as cascor-only — and was corrected in data#273. Both repos' `AGENTS.md` middleware tables documented the old order and were corrected too. |
| APD-DATA-004 | 501 detail echoed a raw `ImportError`, which batch-create then copied verbatim | [juniper-data#275](https://github.com/pcalnon/juniper-data/pull/275) | **The last open `Security` row in the register.** Fixed at the source — the 501 construction — rather than at the batch-create branch the entry names: single-create returns the same detail directly, so the leak was never batch-specific, and the curated install hints D1 exists to surface never leaked at all. The interpolation is now gated on `is_available()`: a declared capability gap keeps its hint, anything else is logged server-side and answered with a correlation id. Mutation-tested in **both** directions, which is why there are three tests — reverting the fix fails the two leak arms, and forcing redact-everything fails the new batch hint arm *and* the pre-existing single-path hint test. A leak-only suite would have passed a fix that silently destroyed D1. |

The §2.3 copy-drift recommendation was built alongside them: `tests/test_service_fork_drift.py` ([juniper-ml#1103](https://github.com/pcalnon/juniper-ml/pull/1103)) now holds **all six** copy-drift guards as `ENFORCED` so they cannot silently regress — every row in §2.3's table.
No `KNOWN_GAP` rows remain -- the ledger's self-maintaining half fired twice (throttle, then blank-key filter) and both times did exactly what it was built to do: fail on the fix and demand promotion.
Promoting the `pre-auth-throttle` row exercised that mechanism end to end and exposed a limit worth carrying forward: a single name marker would have gone green on a bare `import`, so the promoted row asserts two markers — see the caveat under §2.3.
The final row, `cors-outside-auth`, could not be expressed as markers at all. Its regression shape is two `add_middleware` calls **swapping places**, so both markers are present either way and any presence-only check would report SUCCESS on the exact defect it exists to catch — the vacuous-pass class. It is encoded instead as an **ordered** site: `RequestIdMiddleware` must be registered before `CORSMiddleware`, which is precisely "CORS is registered last, so it runs outermost". The ordering matcher carries its own negative controls, and both of them are killed by disabling the order check — deliberately placed in the always-on structural class, so they still run in `ci.yml` where the cross-repo arms skip.

### 5.2 Fixed before this register

Two were fixed between the primer's publication on 2026-08-13 and this register; the third was fixed earlier, before the primer was written, and appears here only because the primer discusses it.

| ID | Finding | Fixed by | Verification |
| --- | --- | --- | --- |
| APD-SVCCORE-F01 | WebSocket heartbeat closed with the reserved code `1006`, which RFC 6455 §7.4.1 forbids an endpoint from sending — so the `websockets` server refused to serialise it and no close frame reached the peer | [juniper-ml#1081](https://github.com/pcalnon/juniper-ml/pull/1081) — after the primer | Both sites now close `1011` with the timeout in the reason: `websocket/control_stream.py:180`, `websocket/training_stream.py:118`. An AST anti-resurrection guard prevents recurrence. |
| APD-SVCCORE-F02 | The 401 path consumed no rate-limit budget | [juniper-ml#1082](https://github.com/pcalnon/juniper-ml/pull/1082) — after the primer | `FailedAuthThrottle` is checked **before** authentication (`middleware.py:205-213`) and `record_failure` is gated on a 401 (`:226-227`); `:222-225` is the `except HTTPException` line and its explanatory comment. Fixed in the shared package first and, on 2026-08-16, ported into both forks — see `APD-DATA-001` † and `APD-CASCOR-004` †. |
| APD-CCLIENT-F01 | `__version__` left at `0.4.0` while the package shipped `0.5.x`/`0.6.x` | **Before** the primer — the exact commit is unidentified | All three literals now read `0.7.0`; a tombstone comment records the incident at `__init__.py:11-13`. Attempts to attribute this to a specific PR did not resolve, so no provenance is claimed rather than an unverifiable one being recorded. The *guard* is still absent — see `APD-ECO-005`. |

---

## 6. Method, and its limits

**How this was produced.** Four independent extraction passes ran over disjoint ranges of the primer (front matter + overview, Part I, Part II, Part III + appendices). Each was required to re-read the cited source before assigning a status, and explicitly forbidden from marking anything `OPEN` without having done so. Their outputs were then merged, deduplicated, and re-verified.
A fifth pass audited every primer line anchor against the primer text itself, which produced the `†` provenance markers, three restatements, and the removal of one entry the primer never asserted about Juniper code.

**What this register is not.** It is not an audit of the Juniper codebase. It is an extraction of what one document happened to assert while teaching something else. The primer visited the code where it made a good example, so coverage is uneven by construction:

- `juniper-data`, `juniper-service-core`, and the client libraries are heavily represented because they were the primer's running examples. juniper-data leads; `juniper-service-core` is second, and carries sixteen entries here.
- `juniper-canopy`, `juniper-cascor-worker`, and most of `juniper-cascor` were barely visited at all. **Their absence here is not evidence of health.**
- Severity reflects the primer's framing plus verification, not a risk assessment against deployment reality. An operator may reasonably re-rank.

**Confidence.** `Low` entries are included deliberately under the over-inclusion rule and should be triaged before being actioned — several are matters of judgement the primer itself flags as defensible (`APD-DATA-028`, `APD-DATA-033`, `APD-SVCCORE-007`, `APD-SVCCORE-013`, `APD-CASCOR-005`, `APD-ML-001`).

**Freshness.** Statuses were verified on 2026-08-14. `file:line` anchors drift with every commit; the primer line anchors are stable because that document is not being edited. Where the two disagree, the source is authoritative and this register is stale.
