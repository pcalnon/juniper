"""Drift gate: security guards that must not silently diverge across the forks.

``juniper-data`` and ``juniper-cascor`` each maintain their own copy of the
service-tier middleware and security code that ``juniper-service-core`` also
ships. That is the single most productive defect shape in the 2026-08-14
ecosystem defect register: **a guard adopted in one copy of near-identical code
and not in its siblings** (register §2.3, "Copy drift"). Five register findings
are exactly this, and nothing in CI noticed any of them.

The natural experiment that proves the shape: ``juniper-ml#1082`` added
``FailedAuthThrottle`` to the shared package and it reached ``juniper-recurrence``
**automatically**, because recurrence imports the shared middleware. It never
reached ``juniper-data`` or ``juniper-cascor``, because both import their own
forks. Same fix, same ecosystem, three services; the only differentiator is
library-versus-copy. Closing that gap took two hand-written PRs against the two
forks (``juniper-data#266``, ``juniper-cascor#524``) -- the per-fork cost this
gate exists to make visible up front, rather than at the next audit.

Why a targeted invariant registry and not a file diff
-----------------------------------------------------
The forks diverge *legitimately* and constantly -- different constants, different
imports, different middleware inventories -- and some divergence is deliberate:
``juniper-data`` holds API keys in a ``list`` specifically so ``compare_digest``
runs per key without a set-membership timing side-channel, where service-core
uses a ``set``. A whole-file diff would drown a real signal in that noise. So
this gate asserts **named guards**, each a small source marker that is present
if and only if the guard is implemented.

The KNOWN_GAP ledger is self-maintaining
----------------------------------------
Guards the forks have *not* adopted are recorded with ``status=KNOWN_GAP`` and
asserted to be **still absent**. That is deliberate: when someone closes one of
those gaps, this test fails and tells them to promote the row to ``ENFORCED``.
A ledger that only ever asserted the good news would rot silently into a list of
things that used to be true -- which is the exact failure mode this file exists
to prevent.

Scope, cross-repo gating, and cadence mirror ``test_ci_tools_drift.py`` /
``test_doc_tools_drift.py``: the sibling-walking assertions run under
``GITHUB_ACTIONS=true`` (the weekly ``docs-full-check`` job clones the siblings)
or locally with ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``. The registry's own
structural checks and the matcher's negative control always run.
"""

from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from pathlib import Path

ENFORCED = "ENFORCED"
KNOWN_GAP = "KNOWN_GAP"
_VALID_STATUSES = frozenset({ENFORCED, KNOWN_GAP})

# Sibling repos this gate reads. Kept small on purpose: these are the two
# services that fork the service-core code. ``juniper-recurrence`` consumes the
# shared package directly and so cannot drift this way.
_FORK_REPOS = ("juniper-data", "juniper-cascor")


@dataclass(frozen=True)
class ForkSite:
    """One fork's copy of a guarded code path."""

    repo: str
    path: str
    markers: tuple[str, ...]
    #: When True, the markers must also appear in this ORDER in the source.
    #:
    #: Some guards are an ordering, not a token. Middleware registration is the
    #: case in hand: Starlette's ``add_middleware`` prepends, so the layer
    #: registered LAST executes OUTERMOST. "CORS runs outside auth" is therefore
    #: a statement about where two ``add_middleware`` calls sit relative to each
    #: other, and substring presence cannot express it -- both calls are present
    #: either way. First-occurrence order can.
    ordered: bool = False


@dataclass(frozen=True)
class Guard:
    """A security guard that should hold identically in every fork."""

    guard_id: str
    summary: str
    register_ids: tuple[str, ...]
    status: str
    canonical: str
    sites: tuple[ForkSite, ...]


_DATA_MIDDLEWARE = "juniper_data/api/middleware.py"
_CASCOR_MIDDLEWARE = "src/api/middleware.py"
_DATA_SECURITY = "juniper_data/api/security.py"
_CASCOR_SECURITY = "src/api/security.py"
_DATA_APP = "juniper_data/api/app.py"
_CASCOR_APP = "src/api/app.py"


GUARDS: tuple[Guard, ...] = (
    Guard(
        guard_id="streaming-body-cap",
        summary=("CR-024: POST/PUT/PATCH bodies are always stream-read against a cumulative cap. Content-Length is an early-reject hint only, so an omitted or under-declared header cannot buy passage."),
        register_ids=("APD-DATA-002",),
        status=ENFORCED,
        canonical="juniper-service-core/juniper_service_core/middleware.py",
        sites=(
            ForkSite("juniper-data", _DATA_MIDDLEWARE, ("request.stream()", '("POST", "PUT", "PATCH")')),
            ForkSite("juniper-cascor", _CASCOR_MIDDLEWARE, ("request.stream()", '("POST", "PUT", "PATCH")')),
        ),
    ),
    Guard(
        guard_id="content-length-parse-guard",
        summary=("A malformed Content-Length is a 400, not an uncaught ValueError. BaseHTTPMiddleware.dispatch runs outside ExceptionMiddleware, so an unguarded int() escapes the app's own ValueError handler and surfaces as a 500."),
        register_ids=("APD-DATA-036",),
        status=ENFORCED,
        canonical="juniper-service-core/juniper_service_core/middleware.py",
        sites=(
            ForkSite("juniper-data", _DATA_MIDDLEWARE, ("Invalid Content-Length header",)),
            ForkSite("juniper-cascor", _CASCOR_MIDDLEWARE, ("Invalid Content-Length header",)),
        ),
    ),
    Guard(
        guard_id="narrow-serialization-error",
        summary=("PydanticSerializationError subclasses ValueError but is a SERVER fault. The blanket ValueError->400 handler must special-case it, or the app's own serialisation failures are reported as client errors and never reach 5xx alerting."),
        register_ids=("APD-CASCOR-002", "APD-DATA-034"),
        status=ENFORCED,
        canonical="(no shared implementation -- both services fixed independently)",
        sites=(
            ForkSite("juniper-data", _DATA_APP, ("PydanticSerializationError",)),
            ForkSite("juniper-cascor", _CASCOR_APP, ("PydanticSerializationError",)),
        ),
    ),
    Guard(
        guard_id="blank-api-key-filter",
        summary=("Blank / whitespace-only API keys must be filtered before auth is enabled, or an empty secret file enables auth that then accepts an empty X-API-Key -- strictly worse than auth being off, because the deployment believes it is protected."),
        register_ids=("APD-DATA-003", "APD-CASCOR-006"),
        status=ENFORCED,
        canonical="juniper-service-core/juniper_service_core/security.py",
        sites=(
            # Two markers, mirroring the canonical filter
            # ``{k for k in (api_keys or []) if isinstance(k, str) and k.strip()}``.
            # The previous bare ``.strip()`` marker was sufficient to DETECT this
            # fix -- neither fork's security.py contained a strip beforehand -- but
            # it is not specific to it: any unrelated strip later added to that
            # module (normalising a header, trimming a secret-file read) would flip
            # the guard green while the blank-key filter stayed absent. Pairing it
            # with ``isinstance(k, str)`` ties the marker to the guard's actual
            # shape instead of to an incidental call.
            ForkSite("juniper-data", _DATA_SECURITY, ("isinstance(k, str)", "k.strip()")),
            ForkSite("juniper-cascor", _CASCOR_SECURITY, ("isinstance(k, str)", "k.strip()")),
        ),
    ),
    Guard(
        guard_id="pre-auth-throttle",
        summary=("juniper-ml#1082 added FailedAuthThrottle to the shared package so the 401 path consumes budget. This was the natural experiment above -- the fix reached recurrence automatically and neither fork at all -- until it was ported into both (juniper-data#266, juniper-cascor#524)."),
        register_ids=("APD-DATA-001", "APD-CASCOR-004"),
        status=ENFORCED,
        canonical="juniper-service-core/juniper_service_core/security.py",
        sites=(
            # Two markers, not one. The class name alone would go green on a bare
            # ``import``, and the half-port that matters -- wiring the pre-auth
            # ``check()`` but omitting ``record_failure`` -- is a throttle that never
            # accumulates, i.e. a silent no-op that still satisfies a name-only marker.
            # Behavioural coverage lives in each fork's own suite; this pair is the
            # cheapest structural proxy for "both halves are present".
            ForkSite("juniper-data", _DATA_MIDDLEWARE, ("FailedAuthThrottle", "record_failure")),
            ForkSite("juniper-cascor", _CASCOR_MIDDLEWARE, ("FailedAuthThrottle", "record_failure")),
        ),
    ),
    Guard(
        guard_id="cors-outside-auth",
        summary=("CORS must execute OUTSIDE SecurityMiddleware. add_middleware prepends, so the LAST registration runs outermost -- registering CORS first put auth in front of it and every browser preflight to a non-exempt path was answered 401. A preflight carries no X-API-Key by construction, so no browser client on a configured origin could reach a protected endpoint at all."),
        register_ids=("APD-CASCOR-001b", "APD-DATA-035"),
        status=ENFORCED,
        canonical="(no shared implementation -- both services fixed independently)",
        sites=(
            # An ORDERED pair, and it has to be: both markers are present whether
            # or not the guard holds, because the bug was never a missing call --
            # it was the same two calls in the wrong sequence. Requiring
            # ``RequestIdMiddleware`` to be registered BEFORE ``CORSMiddleware``
            # is exactly the invariant "CORS is registered last, so it runs
            # outermost". A plain presence marker here would be vacuous.
            #
            # ``CORSMiddleware,`` (with the comma) matches the add_middleware
            # argument and not the import line, which has no trailing comma.
            ForkSite("juniper-data", _DATA_APP, ("app.add_middleware(RequestIdMiddleware)", "CORSMiddleware,"), ordered=True),
            ForkSite("juniper-cascor", _CASCOR_APP, ("app.add_middleware(RequestIdMiddleware)", "CORSMiddleware,"), ordered=True),
        ),
    ),
)

# Register §2.3's "OPTIONS bypass in the exempt check" row is the guard above.
# It was tracked unencoded while it had landed in *no* copy -- there was no
# reference implementation to derive a marker from. juniper-data#273 and
# juniper-cascor#540 fixed both copies (by reordering the middleware rather than
# adding an OPTIONS bypass, which would have exempted every OPTIONS request from
# auth), which is what made the pattern encodable.


def markers_out_of_order(source: str, site: ForkSite) -> list[str]:
    """Return the markers that break ``site``'s declared order, else ``[]``.

    Only meaningful for ``ordered`` sites. Absence is *not* reported here: a
    missing marker is a different failure with a different message, and folding
    the two together would blame a reorder for a deletion.
    """
    if not site.ordered:
        return []
    positions = [source.find(marker) for marker in site.markers]
    if any(position < 0 for position in positions):
        return []
    return [site.markers[i] for i in range(1, len(positions)) if positions[i] < positions[i - 1]]


def guard_is_present(source: str, site: ForkSite) -> bool:
    """Return True when every marker for ``site`` appears in ``source``.

    All markers must be present: a guard that needs two cooperating pieces (the
    stream read *and* the method gate) is not implemented by either alone. For
    an ``ordered`` site they must additionally appear in the declared order.
    """
    if not all(marker in source for marker in site.markers):
        return False
    return not markers_out_of_order(source, site)


def _find_ecosystem_root(juniper_ml_root: Path) -> Path | None:
    """Walk up looking for a directory holding the fork repos.

    Walks further than the two levels ``test_ci_tools_drift`` checks so the gate
    still resolves when juniper-ml is checked out as a nested session worktree
    (``juniper-ml/.claude/worktrees/<name>``), which is otherwise four levels
    below the ecosystem root.
    """
    candidate = juniper_ml_root
    for _ in range(6):
        candidate = candidate.parent
        if candidate == candidate.parent:
            break
        try:
            if all((candidate / repo).is_dir() for repo in _FORK_REPOS):
                return candidate
        except OSError:
            continue
    return None


class GuardRegistryStructureTest(unittest.TestCase):
    """Always-on checks on the registry itself. No sibling repos required."""

    def test_every_guard_is_well_formed(self):
        seen_ids: set[str] = set()
        for guard in GUARDS:
            with self.subTest(guard=guard.guard_id):
                self.assertNotIn(guard.guard_id, seen_ids, "duplicate guard_id")
                seen_ids.add(guard.guard_id)
                self.assertIn(guard.status, _VALID_STATUSES)
                self.assertTrue(guard.summary.strip(), "a guard must say what it protects")
                self.assertTrue(guard.register_ids, "a guard must cite at least one register ID")
                self.assertTrue(guard.sites, "a guard with no fork sites checks nothing")
                for site in guard.sites:
                    self.assertIn(site.repo, _FORK_REPOS)
                    self.assertTrue(site.markers, "a site with no markers always passes")
                    for marker in site.markers:
                        self.assertTrue(marker.strip(), "an empty marker matches everything")
                    if site.ordered:
                        self.assertGreaterEqual(len(site.markers), 2, "an ordered site needs two markers; one can never be out of order, so the flag would be decorative")

    def test_register_ids_look_like_register_ids(self):
        for guard in GUARDS:
            for register_id in guard.register_ids:
                with self.subTest(guard=guard.guard_id, register_id=register_id):
                    self.assertTrue(register_id.startswith("APD-"), "register IDs are APD-<AREA>-<NNN>")

    def test_matcher_requires_every_marker(self):
        """Negative control: the matcher must not pass on a partial match."""
        site = ForkSite("juniper-data", "x.py", ("alpha", "beta"))
        self.assertTrue(guard_is_present("alpha and beta", site))
        self.assertFalse(guard_is_present("alpha only", site))
        self.assertFalse(guard_is_present("", site))

    def test_ordered_matcher_requires_the_declared_order(self):
        """Negative control: for an ordered site, presence alone must not pass.

        This is the whole point of the flag. ``cors-outside-auth`` regresses by
        the markers SWAPPING, never by one going missing, so a matcher that only
        counted presence would report SUCCESS on the defect it exists to catch.
        """
        ordered = ForkSite("juniper-data", "x.py", ("alpha", "beta"), ordered=True)
        self.assertTrue(guard_is_present("alpha then beta", ordered))
        self.assertFalse(guard_is_present("beta then alpha", ordered))
        self.assertFalse(guard_is_present("alpha only", ordered))

        # The flag is opt-in: an unordered site keeps matching either sequence.
        unordered = ForkSite("juniper-data", "x.py", ("alpha", "beta"))
        self.assertTrue(guard_is_present("beta then alpha", unordered))

    def test_out_of_order_report_does_not_double_report_absence(self):
        """A missing marker is a deletion, not a reorder; the messages differ."""
        ordered = ForkSite("juniper-data", "x.py", ("alpha", "beta"), ordered=True)
        self.assertEqual(markers_out_of_order("alpha only", ordered), [])
        self.assertEqual(markers_out_of_order("beta then alpha", ordered), ["beta"])


class ServiceForkDriftTest(unittest.TestCase):
    """Assert each guard's real state in each fork's working tree."""

    juniper_ml_root: Path
    ecosystem_root: Path | None

    @classmethod
    def setUpClass(cls):
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.ecosystem_root = _find_ecosystem_root(cls.juniper_ml_root)

    def _read_site(self, site: ForkSite) -> str | None:
        """Return the site's source, or None when it cannot be read."""
        if self.ecosystem_root is None:
            return None
        path = self.ecosystem_root / site.repo / site.path
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None

    def _require_cross_repo(self):
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            self.skipTest("skipping local cross-repo lint (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override; siblings must be `git pull`ed to origin/main first)")
        if self.ecosystem_root is None:
            self.skipTest(f"ecosystem root not found -- need sibling checkouts of {', '.join(_FORK_REPOS)}")

    def test_enforced_guards_are_present_in_every_fork(self):
        """An ENFORCED guard missing from a fork is a silent regression."""
        self._require_cross_repo()
        for guard in (g for g in GUARDS if g.status == ENFORCED):
            for site in guard.sites:
                with self.subTest(guard=guard.guard_id, repo=site.repo):
                    source = self._read_site(site)
                    if source is None:
                        self.skipTest(f"{site.repo}/{site.path} not readable")
                    missing = [m for m in site.markers if m not in source]
                    self.assertFalse(
                        missing,
                        f"Guard '{guard.guard_id}' is missing from {site.repo}/{site.path} " f"(absent markers: {missing}). This guard is ENFORCED because it was " f"already fixed there; its disappearance is a regression of " f"{', '.join(guard.register_ids)}. Canonical implementation: {guard.canonical}. " f"What it protects: {guard.summary}",
                    )
                    disordered = markers_out_of_order(source, site)
                    self.assertFalse(
                        disordered,
                        f"Guard '{guard.guard_id}' has all its markers in {site.repo}/{site.path} " f"but in the WRONG ORDER (first out of place: {disordered}). For an ordered " f"site the sequence IS the guard -- every marker being present proves nothing. " f"This is a regression of {', '.join(guard.register_ids)}. " f"What it protects: {guard.summary}",
                    )

    def test_known_gaps_are_still_open_or_get_promoted(self):
        """A closed gap must be promoted to ENFORCED, not left mislabelled.

        This is the self-maintaining half of the ledger. Failing here is GOOD
        news -- someone fixed the fork -- but the row must move so the fix is
        then protected against regression like every other ENFORCED guard.
        """
        self._require_cross_repo()
        for guard in (g for g in GUARDS if g.status == KNOWN_GAP):
            for site in guard.sites:
                with self.subTest(guard=guard.guard_id, repo=site.repo):
                    source = self._read_site(site)
                    if source is None:
                        self.skipTest(f"{site.repo}/{site.path} not readable")
                    self.assertFalse(
                        guard_is_present(source, site),
                        f"Guard '{guard.guard_id}' now appears IMPLEMENTED in " f"{site.repo}/{site.path}, but the registry still lists it as a " f"KNOWN_GAP. If you just fixed it: change that row's status to " f"ENFORCED in this file so the fix is protected against future " f"regression, and close {', '.join(guard.register_ids)} in the " f"defect register.",
                    )

    def test_fork_files_named_by_the_registry_exist(self):
        """A renamed or deleted fork file would make every guard vacuously pass."""
        self._require_cross_repo()
        for guard in GUARDS:
            for site in guard.sites:
                with self.subTest(guard=guard.guard_id, repo=site.repo):
                    path = self.ecosystem_root / site.repo / site.path
                    self.assertTrue(
                        path.is_file(),
                        f"{site.repo}/{site.path} does not exist. The registry is stale: " f"until the path is corrected, guard '{guard.guard_id}' is checking nothing.",
                    )


if __name__ == "__main__":
    unittest.main()
