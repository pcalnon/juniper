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
library-versus-copy.

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
        status=KNOWN_GAP,
        canonical="juniper-service-core/juniper_service_core/security.py",
        sites=(
            ForkSite("juniper-data", _DATA_SECURITY, (".strip()",)),
            ForkSite("juniper-cascor", _CASCOR_SECURITY, (".strip()",)),
        ),
    ),
    Guard(
        guard_id="pre-auth-throttle",
        summary=("juniper-ml#1082 added FailedAuthThrottle to the shared package so the 401 path consumes budget; neither fork imports it. This is the natural experiment above -- the fix reached recurrence automatically and neither fork at all."),
        register_ids=("APD-DATA-001", "APD-CASCOR-004"),
        status=KNOWN_GAP,
        canonical="juniper-service-core/juniper_service_core/security.py",
        sites=(
            ForkSite("juniper-data", _DATA_MIDDLEWARE, ("FailedAuthThrottle",)),
            ForkSite("juniper-cascor", _CASCOR_MIDDLEWARE, ("FailedAuthThrottle",)),
        ),
    ),
)

# Register §2.3 also lists an "OPTIONS bypass in the exempt check" row. It is
# deliberately NOT encoded here: it landed in *no* copy, so there is no reference
# implementation to derive a marker from, and a marker invented here would assert
# a shape nobody has agreed to. It stays tracked in the register
# (APD-CASCOR-001b / APD-DATA-035) until one copy establishes the pattern.


def guard_is_present(source: str, site: ForkSite) -> bool:
    """Return True when every marker for ``site`` appears in ``source``.

    All markers must be present: a guard that needs two cooperating pieces (the
    stream read *and* the method gate) is not implemented by either alone.
    """
    return all(marker in source for marker in site.markers)


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
