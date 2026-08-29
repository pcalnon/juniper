# juniper-service-core v0.6.0 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-08-29
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-service-core

---

This is a security-bearing release of `juniper-service-core` v0.6.0. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-service-core` |
| **Fixed in** | 0.6.0 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.6.0

### Added

- **A guard on the three parallel declarations of the public surface** (`APD-SVCCORE-009`).
  `__all__`, the `_LAZY_EXPORTS` name→module map, and the `TYPE_CHECKING` import block are
  maintained by hand and nothing checked that they agree. They did agree, which is exactly when
  the guard is worth adding: the failure mode is a name exported but unresolvable
  (`AttributeError` for a consumer) or resolvable but invisible to type checkers, and neither
  surfaces until someone hits it. The lists are read from source with `ast`, because
  `TYPE_CHECKING` is `False` at run time and its block is one of the three things under test.
  A behavioural arm additionally resolves every exported name, which is what catches a typo'd
  module path in the lazy map — that passes every list comparison.
- **`JuniperServiceCoreError`** — a package base exception, exported eagerly from the package
  root (defect register `APD-SVCCORE-006`). Before it, the exceptions this package raises had
  nothing in common: three subclassed `RuntimeError` and two `KeyError`, so catching "anything
  juniper-service-core raises" meant naming them all, and the nearest category — `except
  RuntimeError` — also swallowed unrelated runtime failures that should propagate.
  **Additive**: each exception now derives from the base *in addition to* its original base, never
  instead of it, so an existing `except RuntimeError` / `except KeyError` handler is unaffected.
  `SnapshotNotFoundError` in particular is raised where a mapping lookup would be, and callers
  legitimately treat it as a `KeyError`.
  Exported eagerly alongside `__version__` because a consumer must be able to write `except
  JuniperServiceCoreError` without the lazy PEP 562 machinery importing fastapi /
  pydantic-settings to resolve the name; `exceptions.py` is dependency-free, and the blocked-import
  smoke test now covers that.
  **One deliberate exclusion**: `UnknownTunableError` keeps `KeyError` alone. `websocket/tunables.py`
  is pinned stdlib-only and standalone by two tests, one of which loads it *by file path bypassing
  the package `__init__`* — importing the package base there would erase that property, to add a
  base to the one exception in the package with no production consumer. The exclusion is asserted,
  so it stays a decision rather than an oversight.
- **`DependencyFloorError.violations`** — the structured `tuple[FloorViolation, ...]` behind the
  message (`APD-SVCCORE-014`). `check_dependency_floors` computes distribution / floor / installed
  per row and `enforce_dependency_floors` used to render that into prose and discard it, leaving a
  caller to parse the text back apart to learn which distribution to upgrade. The message is
  byte-identical; the structure is simply also available, and single-argument construction still
  works.
- **`FailedAuthThrottle` + `build_failed_auth_throttle(...)`** — an IP-keyed, fixed-window throttle
  for *failed* authentication attempts, checked before authentication and consuming budget only on
  a 401. `SecurityMiddleware` gains an optional `failed_auth_throttle=` argument and **enables one
  by default** (10 failures per 60 s per source IP), returning 429 with `Retry-After` past the
  budget.
  Defaulting to enabled is safe because budget is spent only on failure: a caller presenting a
  valid key is never counted, so well-behaved traffic sees no behaviour change whatsoever. A 429
  from the quota limiter is deliberately *not* counted either — it is a quota outcome, not a
  credential guess, and counting it would let an authenticated caller throttle itself out of the
  auth path by exceeding its own quota. Opt out with
  `build_failed_auth_throttle(enabled=False)`.
  Both names are exported through the lazy PEP 562 surface, so the dependency-free top-level
  import is unchanged.
  Note the throttle is in-memory and per-process: behind multiple replicas the effective budget
  multiplies by the replica count, and exact fleet-wide enforcement needs a shared store.
- **`JsonTaskProtocol`** — the package default `WorkerTaskProtocol`, a JSON-only worker with no
  binary frames (`APD-SVCCORE-015`). The `LifecycleCommandExecutor` analogue for the worker seam:
  publishing the Protocol *and* a working default means a consumer implements the three methods
  only when it actually carries a model-specific wire schema. Structural, not inherited — a
  consumer may use it, wrap it, or ignore it.
  **Derived, not invented**: the envelope is the one this package's own tests already wrote from
  scratch three times, and `PendingTask`'s docstring already named the shape ("a JSON-only worker
  packs a plain dict").
  It declares **no** attachments deliberately, so it never enters the binary-receive loop at all.
  Exported through the lazy PEP 562 surface, so the dependency-free top-level import is unchanged.

### Changed

- **`WorkerTaskProtocol`'s members are now `@abstractmethod` and raise `NotImplementedError`**
  (`APD-SVCCORE-011`). They previously had `pass` bodies, so a partial implementation returned
  `None` into `WorkerCoordinator.get_next_assignment`'s dispatch path. The package's other Protocol
  (`CommandExecutor`) already used the abstract convention; the primer's instruction was to pick one
  per package, and this is that convention applied. Because `Protocol`'s metaclass derives from
  `ABCMeta`, an incomplete implementation now fails at **construction** rather than silently at
  dispatch.
  **Potentially breaking** for a consumer that subclassed `WorkerTaskProtocol` without implementing
  all three members — no such consumer exists in the ecosystem, and no service imports this module.
- **The two shipped defaults refuse subclassing** (`APD-SVCCORE-012`). `LifecycleCommandExecutor`
  and `JsonTaskProtocol` are `@final` **and** raise `TypeError` from `__init_subclass__`. Publishing
  a concrete default beside a Protocol invites the inheritance the composition-only design exists to
  avoid, and neither docstring said whether it was supported — so the answer was whatever the first
  consumer assumed. It is now stated and enforced, and each docstring names the supported variation
  points instead: injection (the `start` callback), implementing the Protocol directly, or wrapping
  an instance.
  `@final` alone would not have held — nothing type-checks this package — so the runtime guard is
  the enforcement and the decorator is documentation for a later checker adoption.
  **Potentially breaking** for a consumer that subclassed either class; verified zero such consumers
  across cascor, data, canopy, recurrence and cascor-worker.
- **An over-limit `/ws/control` frame now closes the connection (1009) instead of continuing**
  (`APD-SVCCORE-005`). The size check necessarily runs after `receive_text()` has materialised the
  frame — that is a transport property, and the real ceiling is uvicorn's `ws_max_size` (16 MiB by
  default) — but the `continue` returned before `_handle_command_message`, the only place a
  rate-limit token is spent, so every oversize frame was free and one connection could repeat the
  allocation indefinitely. Charging the bucket instead would be accounting, not protection: by then
  the allocation has already happened. Closing is also what this loop already does for the adjacent
  protocol violations (malformed JSON, non-object JSON both close 1003), and reconnection is
  governed by the handshake cooldown. 1009 is RFC 6455's "Message Too Big".
  A `pong` frame still costs no token, deliberately and now pinned: the bucket is the *command*
  budget, and charging keepalive would let a command burst rate-limit the client's pong, which the
  heartbeat loop reads as a dead peer and closes 1011.

### Fixed

- **`LeakyBucket`'s docstring no longer misdescribes its own algorithm** (`APD-SVCCORE-013`).
  The class is a **token bucket** — it accumulates up to `capacity` tokens at `refill_rate` per
  second and decrements one per admission, so an idle connection banks a burst and may spend it at
  once. The docstring asserted "leaky-bucket" (a traffic shaper draining at exactly `R`) with no
  correction anywhere, so a reader had nothing to weigh the class name against.
  **The name is deliberately unchanged**: it is exported from `juniper_service_core.websocket`, and
  renaming it would break a published surface to settle an ambiguity the reference material calls
  conventional ("in practice the two are implemented identically and named interchangeably — read
  the code, not the class name"). The docstring now states which algorithm this is, why the name
  stays, and the consequence a caller must not get wrong: **sizing `capacity` as though output were
  smoothed to `refill_rate` will admit `capacity` commands in one instant.** Documentation only: no
  behaviour change, and the burst is now pinned by a test.
- **The `/ws/control` handshake gates are documented as deliberately pre-accept, and the ordering is
  pinned** (`APD-SVCCORE-016`). The four distinct close codes (`1013`, `4029`, `4003`, `4001`) do
  not reach the client — uvicorn converts a pre-accept close into a plain HTTP 403 and discards both
  code and reason. That is **conformant**, not defective: a handshake failure is still HTTP, and
  RFC 6455 §10.2 recommends `403` for an unacceptable Origin. Making the codes observable would
  require accepting the socket *first* and then closing it, completing a handshake for a caller the
  kill switch, the cooldown or the Origin allowlist has already refused — a weaker posture.
  Recorded at `_check_handshake_gates` so the ordering is not "fixed" into that regression, and a
  new test asserts every rejection path leaves the socket un-accepted. Documentation and test only:
  no behaviour change.
- **The worker attachment list is now bounded by count and by total bytes** (`APD-SVCCORE-001`).
  `_handle_task_result` received one binary frame per declared attachment and checked only
  `len(raw_bytes) > _MAX_BINARY_SIZE` per frame, so one submission permitted
  `len(attachment_names) × _MAX_BINARY_SIZE` — a bound on each item is not a bound on the sum, and
  every accepted frame is retained in memory until the submission completes.
  Two independent bounds: `_MAX_ATTACHMENTS = 32` (cardinality, checked **before the first
  `receive()`** so an over-long declaration cannot hold the handler in a receive loop) — ported from
  juniper-cascor's `_MAX_TENSOR_MANIFEST_ENTRIES`, whose own comment names this failure mode — and
  `_MAX_TOTAL_BINARY_SIZE` (aggregate per submission), set equal to the per-frame cap by a stated
  principle rather than an invented magnitude: one submission may not deliver more bytes than a
  single frame was already permitted to carry. The two stay independent policies that merely
  coincide today.
- **The rate limiter's per-process scope is now stated where it is used** (`APD-SVCCORE-007`).
  The constraint itself is deliberate and unchanged — fixed-window counters live in memory, so
  behind multiple replicas each process keeps its own and the effective budget multiplies by the
  replica count. What was missing was disclosure: `RateLimiter` said only "suitable for
  single-process deployments" without the consequence, and `build_rate_limiter` — the function a
  consuming service actually calls — said nothing at all, so a caller choosing
  `requests_per_minute` had no way to learn that four replicas admit four times the configured
  budget. `FailedAuthThrottle`, the sibling control in the same module, already documented this
  properly; the two now agree, and a test pins that they keep agreeing. Documentation only: no
  behaviour change.
- **`Retry-After` no longer tells a rate-limited caller to retry immediately**
  (`APD-SVCCORE-004`). `reset_in` was `int(window - elapsed)`, which truncates toward zero, so any
  sub-second remainder became `0`. A client obeying the header retried at once into a limiter
  guaranteed to reject it again, and kept doing so for the tail of every window. Measured on a
  1-second window before the fix: `Retry-After: 0` at 0.30s, 0.60s, 0.90s and 0.99s in — every
  rejection, not an edge case. Now rounded **up** with a floor of 1: waiting a fraction too long
  costs the caller nothing, waking a fraction early reproduces the defect. Applied to the allowed
  path too, which feeds `X-RateLimit-Reset` — the two headers describe the same instant and were
  free to disagree by a second.
- **`dir(juniper_service_core)` no longer hides the module's own attributes**
  (`APD-SVCCORE-017`). Defining `__dir__` *replaces* the default rather than extending it, so
  returning `sorted(__all__)` made `dir()` a strictly smaller view than the module: `__name__`,
  `__file__`, `__doc__`, `__path__` and every eagerly bound name disappeared. A `__dir__` on a
  PEP 562 module exists to *add* the lazily resolvable names that `globals()` cannot know about,
  not to hide the ones already there. REPL completion and `inspect`-style tooling both read it.
- **WebSocket heartbeat timeouts no longer close with the reserved code 1006.** Both
  `websocket/control_stream.py` and `websocket/training_stream.py` closed a pong-timeout
  connection with `code=1006`. [RFC 6455 §7.4.1](https://www.rfc-editor.org/rfc/rfc6455.html)
  reserves that value and forbids an endpoint from setting it as a Close-frame status — it
  exists for a *receiver* to report a closure that carried no Close frame at all. The
  `websockets` server used under uvicorn enforces this and raises on serialization, so the
  close frame never reached the peer: the client was left holding a silent half-open socket
  with no code and no reason string. Both sites now close **1011** with reason
  `"Heartbeat timeout: no pong or traffic within <N>s"`, matching the fix `juniper-cascor`
  already applied to its own copies after the 2026-07-10 control-WS incident. The timeout and
  ping interval are also now included in the timeout log line. Guarded by an AST-based
  anti-resurrection test so a new handler cannot reintroduce 1006.

### Security

- **The 401 path is no longer unthrottled.** `SecurityMiddleware` runs authentication before the
  identity-keyed `RateLimiter`, which is correct — a rejected request must not spend a legitimate
  caller's quota, and the limiter's bucket key depends on the auth result (`key:{api_key}`, else
  `ip:{client_ip}`), so limiting first would collapse every authenticated caller behind one NAT
  into a single bucket. But because an auth failure raises before the limiter is ever reached,
  **failed authentication consumed no budget at all**: credential guessing and garbage-credential
  floods were rate limited by nothing.
  The fix is not to reorder — that trades a real protection for a worse one — but to add a second,
  coarse limiter ahead of authentication. See `FailedAuthThrottle` above.
- **The OpenAPI document is no longer served to unauthenticated callers.** `/docs`,
  `/openapi.json` and `/redoc` were in `EXEMPT_PATHS`, and `_is_exempt` is a bare membership test
  evaluated *regardless of whether any API key is configured*. Listing a doc path there therefore
  did not "enable" the document — it **published** it. Because `create_app` also passed no
  `docs_url` / `redoc_url` / `openapi_url`, FastAPI's defaults mounted all three unconditionally,
  so every consumer that used the factory served its complete API surface — every route, schema
  and parameter — to callers with no credentials, even with auth configured and required.
  This is the sibling of `APD-DATA-024` (juniper-data#295) and, unlike the cascor copy, it was
  **live**: `juniper-recurrence` is the sole production consumer of this middleware, it mounts the
  document, and it publishes a host port with `REQUIRE_AUTH` defaulting to true.
  The fix follows the posture already chosen for juniper-data: the three paths are removed from
  `EXEMPT_PATHS` so `SecurityMiddleware` authenticates `/openapi.json` like any other route, and
  `create_app` gains **`explorers_enabled`** (default `True`) to unmount `/docs` and `/redoc` when
  auth is on. The explorers are browser pages that fetch the document by XHR with no `X-API-Key`
  header, so mounting them behind the key would serve a page that can only 401 — while leaving
  them exempt looks like "behind the key" and is in fact "open to everyone". A secured deployment
  stays self-describing to *authenticated* callers instead of silently schema-less.
  **Consumer action required**: pass `explorers_enabled=not settings.api_keys` to `create_app`.
  The default preserves the previous behaviour for deployments that run without auth.
  Pinned by `tests/test_security_middleware_exempt_paths.py`, which asserts the paths' **absence**
  — the regression is additive, so presence-only tests cannot catch it.

---

## References

- [CHANGELOG.md](../../CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-service-core_v0.6.0.md`

<!-- Auto-generated release-train DRAFT (util/release_train/notes_render.py).
     Source template: notes/templates/TEMPLATE_SECURITY_RELEASE_NOTES.md.
     Complete or delete these template sections before the release ceremony:
       - Affected Versions
       - Remediation / Upgrade Instructions
       - Testing & Quality
       - Upgrade Recommendation
-->
