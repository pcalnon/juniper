#!/usr/bin/env python3
"""Juniper PyPI release-train ceremony engine (plan S5.3/S7/S8/S9.3/S10; Phase 3 step 3.2).

Consumes the release-manifest JSON emitted by ``detect.py`` and, for every package the detector
classified ``BUMPED_NOT_RELEASED`` (``declared > released``; no Release cut yet -- plan S5.1), runs the
**automated ceremony**: the middle arc R6 automates without ever touching a gate (plan S5.3). The
version bump that *made* the package ``BUMPED_NOT_RELEASED`` already rode the owner-approved proposal PR
(Gate 1), and the PyPI deploy at the very end still waits at the ``pypi`` environment gate (Gate 2). The
ceremony only automates the middle: notes authoring + central archival, the exempt archive PR, the
Release cut, and TestPyPI verification -- **never** a version bump without approval and **never** a PyPI
deploy without approval.

Per BUMPED_NOT_RELEASED package -- in-repo (juniper-ml) always, and a **cross-repo** sibling when the
run is ``--cross-repo``-capable (the GitHub App installation token, Phase 4.1) AND the sibling is
checked out on disk under ``--ecosystem-root`` (plan S9.2 / S12 step 4.1). The cross-repo ceremony
splits its two GitHub effects by repo (plan S10.2): the **exempt notes-archive PR is ALWAYS opened in
juniper-ml** (the central, canonical ``notes/releases/`` archive -- ``plan.archive_repo`` is always
``juniper-ml``), while the **Release is cut on the OWNING repo** (``gh release create --repo
pcalnon/<repo>``) whose publish workflow is then monitored. For an in-repo package the two repos
coincide, so the split is a no-op and behaviour is byte-identical to Phase 3:

  1. **Preconditions (plan S8)** -- any failure HALTs *that* package with a clear reason and a
     deduplicated GitHub-issue payload (title keyed on ``pypi_name`` + reason); a halt never blocks the
     other packages. Checked: target ``main`` CI green; the ``declared >= released`` re-check against
     live PyPI truth; a non-empty ``CHANGELOG [<version>]`` section to source the notes; (during the
     monitor) TestPyPI install-verify success before Gate 2. If the ``gh issue`` API itself fails when
     filing that dedup issue -- most plausibly the cross-repo GitHub App token lacking the **Issues**
     permission (the owner may grant it later; plan S11 failure-issues) -- the upsert **degrades
     gracefully**: a loud operator log line + a step-summary-visible ``halt_issue_failed`` flag, NEVER a
     crash. The package stays HALTED and the run's step summary + Slack still surface it; the R7 ``gh``
     surface is unchanged (the degrade wraps the same ``upsert_halt_issue`` seam member).
  2. **Final central notes** -- build the archive file (``notes_render``, from the released
     sub-package's ``CHANGELOG [<version>]`` section; ``archive_name`` from ``registry.yaml``).
  3. **Exempt archive PR** -- open the add-only, single-file PR (the thing the S7.2 archive-guard proves).
     The archive branch and its single file are created **through the GitHub API** (a ``git/refs`` POST +
     a ``createCommitOnBranch`` GraphQL mutation), so the commit is **GitHub-signed / Verified** and the
     exempt PR satisfies the juniper-ml ruleset's ``required_signatures`` rule -- which is what makes the
     auto-merge (step 4) truly hands-free. A plain runner-side ``git commit`` is unsigned and left the
     armed auto-merge BLOCKED behind that rule despite all checks green (2026-07-23 ml#707, owner
     admin-bypass one-click); the API commit removes that block with zero security-posture change.
  4. **Auto-merge** -- enable ``gh pr merge --auto --squash`` on it; if the repo has ``allow_auto_merge``
     off (step 3.3 has not landed yet) enabling **degrades gracefully** to the owner one-click merge,
     it is NOT a halt.
  5. **Cut the Release** -- ``gh release create <tag> --latest=false --notes-file <archive>``. The
     Release **creates** the tag for a sub-package (procedure S11.4), so there is deliberately **no**
     ``--verify-tag`` (there is no pre-existing tag to verify).
  6. **Monitor** -- watch the triggered publish run; the run legitimately parks at the ``pypi``
     environment gate: that terminal state ``PENDING_PYPI_APPROVAL`` **is success for the train** (plan
     S5.1 terminal-healthy). A TestPyPI-verify failure before Gate 2 is a HALT.

**R7 hard invariant (plan S9.3), enforced in code AND asserted by the tests:** the ``gh`` surface the
ceremony's write identity may touch is exactly {``pr create``, ``pr merge --auto``, ``release create``,
``issue create/edit``, and -- for the archive lane -- an **archive-branch ``git/refs`` POST** + an
**archive ``createCommitOnBranch`` signed commit**} plus the read guards it needs -- and **nothing** that
mutates a deployment environment or a reviewer. Every live ``gh`` call is routed through
``_assert_gh_allowed``, which raises ``SeamViolation`` for any subcommand outside ``GH_ALLOWED_SURFACE``
or carrying a forbidden token (``environment`` / ``deployment`` / ``review`` / ``--admin`` / ...), a bare
``pr merge`` without ``--auto``, or a ``release create --verify-tag``. ``api`` **stays forbidden for the
general surface**; the ONLY carve-out is the archive lane's two calls, which are bounded by the sibling
assertion ``_assert_api_allowed`` to (a) a ``repos/<owner>/<repo>/git/refs`` POST creating a
``refs/heads/*`` ref and (b) an ``api graphql`` body containing ``createCommitOnBranch`` with
``repoWithOwner`` bound -- each pinned to one of the 8 publishing repos; every other ``gh api`` (a
different path, a different mutation, a non-POST ref write, or an out-of-allowlist repo) is a
``SeamViolation``. Phase 4.1 adds a **``--repo`` value bound**:
when a call carries ``--repo <slug>`` and the live seam was built with the registry-derived allowlist,
the slug MUST name one of the 8 publishing repos (``owner/<repo>``); a ``--repo`` pointing anywhere else
is a ``SeamViolation``. This is how cross-repo ``--repo pcalnon/<owning>`` is expressed WITHOUT widening
the verb allowlist -- the surface (verb pairs + forbidden tokens) is unchanged; only the repo target set
opens, and only to the exact 8.

**Idempotent re-entry (plan S8 last row):** a re-run re-computes state from PyPI/Release truth -- if PyPI
already serves the target version the run is a no-op; if the Release tag already exists it resumes at the
monitor (never re-cutting, never duplicating the archive PR); an already-open archive PR / an already-on-
``main`` archive file is reused, not duplicated.

Every external effect is injected through a ``CeremonySources`` seam so ``tests/test_release_train_
ceremony.py`` is fully hermetic (no network / gh / git / repo writes). ``--dry-run`` is the DEFAULT: it
prints the complete ceremony *script of actions* and writes nothing / opens nothing / cuts nothing.
``--execute`` (opt-in, overridden by ``--dry-run`` for safety) performs the actions -- it is wired for a
later workflow step and is **never** run against the real repo in this change. ``util/`` is not
pre-commit-lint-gated, so that unittest IS the gate (the ``env_floor_drift_check`` precedent, shared with
``detect.py`` / ``propose.py``).

Exit codes: 0 clean run (no halts), 1 at least one package HALTED (owner attention -- an issue was
filed/updated), 2 invocation error (bad manifest / empty registry / unknown ``--package``).

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-17
Status: permanent utility (Phase 3, exempt-archive ceremony engine)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess  # nosec B404 - only the gh/git binaries with fixed argv (no shell)
import sys
import tempfile
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# Same-directory siblings; resolvable both when run as a script (script dir on sys.path[0]) and under
# the tests' ``sys.path.insert(UTIL_DIR)`` idiom (mirrors test_release_train_detect / _propose).
import detect  # noqa: E402
import notes_render  # noqa: E402

SourceError = detect.SourceError  # reuse the detector's environmental-failure type

DEFAULT_OWNER = os.environ.get("JUNIPER_RELEASE_TRAIN_OWNER", "pcalnon")

# Only this classification enters the ceremony (plan S5.1/S5.3).
CEREMONIAL = "BUMPED_NOT_RELEASED"

# The repo a ``--execute`` ceremony ALWAYS may write, even on the degraded single-repo ``GITHUB_TOKEN``
# path: juniper-ml -- the meta-package and its six co-located sub-packages, AND the central exempt
# notes-archive PR for EVERY package (plan S10.2). A sibling's Release is cut on its OWNING repo, which
# is unlocked by CAPABILITY (``--cross-repo`` + the GitHub App token, Phase 4.1), not by widening this
# constant. WITHOUT the capability a sibling is SKIPPED with a clear reason (``writable_repo_skip_reason``).
# Overridable for tests / a future multi-repo identity.
WRITABLE_REPO = os.environ.get("JUNIPER_RELEASE_TRAIN_WRITABLE_REPO", detect.META_REPO)

# Monitor bounds (plan S8 TestPyPI gate -> the ``pypi`` env-gate; §12 step 3.2). The publish workflow
# builds + verifies on TestPyPI before its ``pypi``-environment deploy job parks at the owner-gated
# approval, at which point the run's top-level GitHub status becomes ``waiting`` (verified: ``waiting`` is
# a documented workflow-run status and ``gh run view --json status`` is a raw passthrough of that REST
# field). The monitor polls for a BOUNDED wall clock at a short fixed interval so it actually observes
# that ``waiting`` state (-> PENDING_PYPI_APPROVAL) instead of giving up early and reporting IN_PROGRESS.
DEFAULT_MONITOR_TIMEOUT_SECONDS = 900  # ~15 min: headroom for build + TestPyPI publish + install-verify + reaching the gate
MONITOR_POLL_SECONDS = 15  # short fixed poll interval (keeps gh read volume bounded)


# ── R7 gh write-identity surface (plan S9.3) ─────────────────────────────────


class SeamViolation(RuntimeError):
    """A ``gh`` call outside the R7-permitted surface -- a *code* bug, never a runtime condition."""


# The EXACT mutating ``gh`` surface the ceremony's write identity may use (plan S9.3 / R7). Nothing here
# mutates a deployment environment or a reviewer; the PyPI deploy stays owner-gated at the ``pypi`` env.
GH_MUTATING_SURFACE = frozenset(
    {
        ("pr", "create"),  # open the exempt archive PR
        ("pr", "merge"),  # enable --auto --squash (NEVER a bare immediate merge; --auto required)
        ("release", "create"),  # cut the Release (CREATES the tag for a sub-package; no --verify-tag)
        ("issue", "create"),  # open a dedup HALT issue
        ("issue", "edit"),  # update an existing dedup HALT issue
    }
)
# The read-only guards the ceremony needs (dup-guard, idempotency, monitoring). All inherently benign.
GH_READONLY_SURFACE = frozenset(
    {
        ("pr", "list"),  # dup-guard + archive-PR idempotency
        ("release", "view"),  # idempotency: has the Release already been cut?
        ("run", "list"),  # target main-CI status + find the triggered publish run
        ("run", "view"),  # monitor the publish run's jobs/conclusion
        ("issue", "list"),  # dedup a HALT issue
    }
)
GH_ALLOWED_SURFACE = GH_MUTATING_SURFACE | GH_READONLY_SURFACE

# Tokens that must NEVER appear in a general ``gh`` argv the ceremony builds -- the R7 red lines. ``api``
# is forbidden so no raw REST call can reach an environment/deployment endpoint -- with the SOLE, tightly
# bounded exception of the archive lane's two calls (a ``git/refs`` POST + a ``createCommitOnBranch``
# GraphQL signed commit), which are dispatched to ``_assert_api_allowed`` before this general check runs;
# ``review`` / ``approve`` would touch a reviewer; ``--admin`` would bypass required checks;
# env/deploy/secret/variable/ruleset are environment- or policy-mutating.
GH_FORBIDDEN_TOKENS = frozenset(
    {
        "api",
        "review",
        "approve",
        "environment",
        "environments",
        "deployment",
        "deployments",
        "secret",
        "secrets",
        "variable",
        "variables",
        "ruleset",
        "rulesets",
        "--admin",
    }
)


def _assert_gh_allowed(args: list, allowed_repos: "frozenset[str] | None" = None) -> None:
    """Raise ``SeamViolation`` unless ``gh <args>`` is within the R7-permitted surface (plan S9.3).

    Enforces: the leading ``(subcommand, verb)`` pair is in ``GH_ALLOWED_SURFACE``; no argv token is in
    ``GH_FORBIDDEN_TOKENS``; ``pr merge`` always carries ``--auto`` (never a bare immediate merge);
    ``release create`` never carries ``--verify-tag`` (the Release CREATES the tag for a sub-package);
    and -- when ``allowed_repos`` is supplied (the registry-derived ``owner/<repo>`` set, Phase 4.1) --
    any ``--repo <slug>`` names one of the 8 publishing repos and nothing else. ``allowed_repos=None``
    leaves the ``--repo`` VALUE unchecked (the surface + token guards still apply); the live seam always
    supplies it, so a real run is always bounded to the 8.

    A leading ``api`` subcommand is dispatched to ``_assert_api_allowed`` (the ONLY sanctioned raw-REST /
    GraphQL calls are the archive lane's branch-ref create + signed commit); every other ``api`` usage
    raises there. ``api`` therefore never reaches the general ``GH_ALLOWED_SURFACE`` / forbidden-token
    checks below (where it would always be rejected)."""
    if len(args) < 2:
        raise SeamViolation(f"gh call too short to validate: {args!r}")
    if args[0] == "api":
        _assert_api_allowed(args, allowed_repos)
        return
    pair = (args[0], args[1])
    forbidden = [tok for tok in args if tok in GH_FORBIDDEN_TOKENS]
    if forbidden:
        raise SeamViolation(f"forbidden gh token(s) {forbidden} in {args!r} -- R7 permits no environment/deployment/reviewer mutation")
    if pair not in GH_ALLOWED_SURFACE:
        raise SeamViolation(f"gh surface {pair} not in the R7 allowlist {sorted(GH_ALLOWED_SURFACE)}")
    if pair == ("pr", "merge") and "--auto" not in args:
        raise SeamViolation("gh pr merge must carry --auto (the ceremony never immediately merges; it enables auto-merge behind the guard)")
    if pair == ("release", "create") and "--verify-tag" in args:
        raise SeamViolation("gh release create must NOT carry --verify-tag (the Release CREATES the sub-package tag; there is no pre-existing tag to verify)")
    if allowed_repos is not None and "--repo" in args:
        idx = args.index("--repo")
        slug = args[idx + 1] if idx + 1 < len(args) else None
        if slug not in allowed_repos:
            raise SeamViolation(f"gh --repo {slug!r} is not one of the {len(allowed_repos)} publishing repos {sorted(allowed_repos)} -- R7 bounds the cross-repo write identity to exactly those repos (plan S9.3 / S12 step 4.1)")


def publishing_repo_slugs(entries: list, owner: str) -> "frozenset[str]":
    """The ``owner/<repo>`` allowlist for ``_assert_gh_allowed``, derived from the registry's repo set
    (data-driven, so it can never drift from the 8 publishing repos -- plan S4.1 / the registry lint)."""
    return frozenset(f"{owner}/{e.repo}" for e in entries)


# ── the archive lane's two sanctioned ``gh api`` calls (GitHub-signed commit) ─
#
# The exempt notes-archive PR is created through GitHub's API so its commit is GitHub-signed / Verified
# (satisfying the juniper-ml ruleset's ``required_signatures`` rule -> hands-free auto-merge). ``api``
# stays forbidden for everything else; these two shapes are the deliberate, narrowly-bounded carve-out.

# The ONLY sanctioned non-graphql ``gh api`` REST path: a POST creating ``refs/heads/<archive-branch>``
# on one of the 8 publishing repos (group 1 == ``<owner>/<repo>``).
_API_REFS_PATH_RE = re.compile(r"^repos/([^/]+/[^/]+)/git/refs$")

# The ONLY sanctioned ``gh api graphql`` mutation. ``createCommitOnBranch`` adds the single archive file
# as a commit authored by the API -> GitHub-signed. All six variables are string-serialised scalars
# (``Base64String`` / ``GitObjectID`` serialise from JSON strings), so ``gh api graphql -f name=value``
# passes them verbatim; the document is one whitespace-insensitive line (no embedded newlines needed).
_CREATE_COMMIT_ON_BRANCH_MUTATION = (
    "mutation($repoWithOwner: String!, $branch: String!, $headline: String!, "
    "$path: String!, $contents: Base64String!, $expectedHeadOid: GitObjectID!) { "
    "createCommitOnBranch(input: {"
    "branch: {repositoryNameWithOwner: $repoWithOwner, branchName: $branch}, "
    "message: {headline: $headline}, "
    "expectedHeadOid: $expectedHeadOid, "
    "fileChanges: {additions: [{path: $path, contents: $contents}]}"
    "}) { commit { oid url } } }"
)


def _api_field(args: list, key: str) -> "str | None":
    """The value of the first ``-f/-F <key>=<value>`` (or bare ``<key>=<value>``) token, else None.

    ``gh api`` splits a field token on the FIRST ``=`` only, so a base64 value carrying ``=`` padding
    round-trips intact -- this mirrors that split (everything after the first ``=`` is the value)."""
    prefix = f"{key}="
    for tok in args:
        if tok.startswith(prefix):
            return tok[len(prefix):]
    return None


def _api_is_post(args: list) -> bool:
    """True iff the argv carries an explicit POST method (``-X POST`` / ``--method POST``)."""
    return any(tok in ("-X", "--method") and args[i + 1].upper() == "POST" for i, tok in enumerate(args[:-1]))


def _assert_api_allowed(args: list, allowed_repos: "frozenset[str] | None") -> None:
    """Validate the ONLY two sanctioned ``gh api`` calls (the archive lane) -- reject everything else.

    ``api`` stays in ``GH_FORBIDDEN_TOKENS`` for the general surface; this sibling assertion is the
    deliberate carve-out, each call pinned to one of the 8 publishing repos:

      (a) ``api repos/<owner>/<repo>/git/refs`` with method POST and a ``ref=refs/heads/*`` field, or
      (b) ``api graphql`` whose body is the ``createCommitOnBranch`` mutation with ``repoWithOwner`` bound.

    A different path, a different mutation, a non-POST ref write, or a repo outside ``allowed_repos`` (when
    supplied) is a ``SeamViolation``. ``allowed_repos=None`` leaves the repo VALUE unchecked (the path-shape
    + mutation-name guards still bite); the live seam always supplies the registry-derived set, so a real
    run is always bounded to the 8. A genuinely env/deploy/reviewer-mutating token can never ride a
    sanctioned call (the defence-in-depth token check below)."""
    bad = [tok for tok in args if tok != "api" and tok in GH_FORBIDDEN_TOKENS]
    if bad:
        raise SeamViolation(f"forbidden gh token(s) {bad} in an otherwise-sanctioned api call {args!r}")
    sub = args[1]
    if sub == "graphql":
        if not any("createCommitOnBranch" in tok for tok in args):
            raise SeamViolation(f"gh api graphql is sanctioned ONLY for the createCommitOnBranch archive commit; got {args!r}")
        slug = _api_field(args, "repoWithOwner")
        if slug is None:
            raise SeamViolation(f"gh api graphql createCommitOnBranch must bind repoWithOwner=<owner>/<repo>; got {args!r}")
        if allowed_repos is not None and slug not in allowed_repos:
            raise SeamViolation(f"gh api graphql createCommitOnBranch bound to {slug!r}, not one of the {len(allowed_repos)} publishing repos {sorted(allowed_repos)} -- R7 archive-lane repo bound")
        return
    m = _API_REFS_PATH_RE.match(sub)
    if not m:
        raise SeamViolation(f"gh api is forbidden except the archive-branch `repos/<owner>/<repo>/git/refs` POST and the createCommitOnBranch graphql mutation; got {args!r}")
    slug = m.group(1)
    if allowed_repos is not None and slug not in allowed_repos:
        raise SeamViolation(f"gh api git/refs bound to {slug!r}, not one of the {len(allowed_repos)} publishing repos {sorted(allowed_repos)} -- R7 archive-lane repo bound")
    if not _api_is_post(args):
        raise SeamViolation(f"gh api {sub} must be a POST (the archive-branch ref create); got {args!r}")
    ref = _api_field(args, "ref")
    if ref is not None and not ref.startswith("refs/heads/"):
        raise SeamViolation(f"archive-branch ref create must target refs/heads/*, got ref={ref!r}")


# ── low-level gh / git runners (fixed argv, no shell) ────────────────────────


def _gh(args: list, timeout: int = 90) -> "str | None":
    """Run ``gh <args>``. None on a 404-ish 'no result'; SourceError on any transport/auth failure."""
    try:
        proc = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv, no shell
    except FileNotFoundError as exc:
        raise SourceError("gh CLI not found (install/authenticate GitHub CLI)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"gh timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        low = stderr.lower()
        if "not found" in low or "no pull requests" in low or "release not found" in low or "no releases" in low:
            return None
        raise SourceError(f"gh failed ({' '.join(args[:3])}): {stderr[:200]}")
    return proc.stdout


def _git(repo_dir: Path, args: list, timeout: int = 120, check: bool = True) -> "str | None":
    """Run ``git -C <repo_dir> <args>`` (fixed argv, no shell). None on non-zero when ``check`` is False."""
    try:
        proc = subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv
    except FileNotFoundError as exc:
        raise SourceError("git not found (needed for --execute)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"git timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        if check:
            raise SourceError(f"git failed ({' '.join(args[:3])}): {(proc.stderr or '').strip()[:200]}")
        return None
    return proc.stdout


# ── operator warning (best-effort stderr; used by the graceful-degrade paths) ─
#
# NB: the archive lane now creates its branch + commit through the GitHub API (signed commit), so it
# never switches the operator's checkout -- the former ``_capture_git_ref`` / ``_restore_git_ref``
# branch-restore machinery (the 07-19 rough-edge fix) is removed as moot. The archive lane was the last
# local-git WRITE; git is now used only for READS (``archive_on_main`` + the base-sha / branch-reuse
# reads in ``open_archive_pr``), so nothing switches HEAD and there is nothing to restore.


def _warn(msg: str) -> None:
    """Best-effort operator warning to stderr (never raises; used by the HALT-issue graceful degrade)."""
    print(f"WARNING: {msg}", file=sys.stderr)


# ── small pure helpers ───────────────────────────────────────────────────────


def release_tag(entry: "detect.PackageEntry", version: str) -> str:
    """The git tag the Release CREATES, from the registry ``tag_pattern`` (procedure S11.4).

    ``v*`` -> ``v0.5.0`` (meta); ``juniper-service-core-v*`` -> ``juniper-service-core-v0.5.0`` (else)."""
    pat = entry.tag_pattern
    return (pat[:-1] + version) if pat.endswith("*") else f"{pat}{version}"


def archive_branch(pypi_name: str, version: str) -> str:
    """Head branch for the exempt add-only archive PR (distinct from propose.py's ``release/`` branch)."""
    return f"release-notes/{pypi_name}-v{version}"


def changelog_rel(entry: "detect.PackageEntry") -> str:
    return os.path.normpath(os.path.join(entry.path, "CHANGELOG.md")).replace(os.sep, "/")


def archive_relpath(entry: "detect.PackageEntry", version: str) -> str:
    """Central archive path from the registry ``archive_name`` template (procedure S11.3 / plan S10.2)."""
    return f"notes/releases/{entry.archive_name.format(version=version)}"


def infer_bump(old_version: "str | None", new_version: str) -> str:
    """Derive the SemVer bump label from the released -> declared delta (for the notes Release-Type)."""

    def triple(v: "str | None") -> tuple:
        m = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)", v or "0.0.0")
        return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)

    old, new = triple(old_version), triple(new_version)
    if new[0] != old[0]:
        return "major"
    if new[1] != old[1]:
        return "minor"
    if new[2] != old[2]:
        return "patch"
    return "minor"


def changelog_version_section(changelog_text: str, version: str) -> "OrderedDict[str, list]":
    """Parse the ``## [<version>]`` block into ``{Category: [bullets]}`` (Keep-a-Changelog).

    This is the section the proposal PR created when it moved ``[Unreleased] -> [<version>]`` (plan
    S5.4); the ceremony sources the FINAL notes from it. Mirrors ``notes_render.parse_unreleased`` but
    anchored on the concrete version heading, and reuses its bullet grouping."""
    result: "OrderedDict[str, list]" = OrderedDict()
    if not changelog_text:
        return result
    lines = changelog_text.splitlines()
    vpat = re.compile(r"^##\s*\[?" + re.escape(version) + r"\]?", re.IGNORECASE)
    start = None
    for i, line in enumerate(lines):
        if vpat.match(line.strip()):
            start = i + 1
            break
    if start is None:
        return result
    current_cat: "str | None" = None
    body: list = []
    for line in lines[start:]:
        if re.match(r"^##\s", line) and not re.match(r"^###", line):
            break  # next version section
        hm = re.match(r"^###\s+([A-Za-z]+)", line.strip())
        if hm:
            if current_cat is not None:
                bullets = notes_render._split_bullets(body)
                if bullets:
                    result[current_cat] = bullets
            current_cat = hm.group(1)
            body = []
            continue
        if current_cat is not None:
            body.append(line)
    if current_cat is not None:
        bullets = notes_render._split_bullets(body)
        if bullets:
            result[current_cat] = bullets
    return result


def writable_repo_skip_reason(repo: str, *, cross_repo_capable: bool = False, ecosystem_root: "Path | None" = None, writable_repo: str = WRITABLE_REPO) -> "str | None":
    """Reason to SKIP a package, or ``None`` when the ceremony may run it (capability-based, Phase 4.1).

      * ``repo == writable_repo`` (juniper-ml) -> ``None``: in-repo is always ceremoniable.
      * a sibling AND NOT ``cross_repo_capable`` -> the SAME clear reason as before (the degraded
        single-repo ``GITHUB_TOKEN`` cannot cut a Release on the owning repo).
      * a sibling, capable, but its checkout is absent under ``ecosystem_root`` -> a distinct reason
        (the ceremony reads the owning repo's ``CHANGELOG [<version>]`` to source the notes).
      * a sibling, capable, checkout present -> ``None``: the GitHub App identity cuts the Release on the
        owning repo while the exempt archive PR still lands centrally in juniper-ml (plan S9.2 / S10.2)."""
    if repo == writable_repo:
        return None
    if not cross_repo_capable:
        return f"cross-repo: package lives in '{repo}', not the writable repo '{writable_repo}' -- the Phase-3 pilot's single-repo GITHUB_TOKEN cannot open a PR / cut a Release there (Phase 4's GitHub App identity lifts this, plan S9.2 / S12 step 4.1)"
    checkout = (ecosystem_root / repo) if ecosystem_root is not None else None
    if checkout is None or not checkout.is_dir():
        return f"cross-repo: '{repo}' is BUMPED_NOT_RELEASED and this run is cross-repo-capable, but its checkout is not present at {checkout} -- clone it (full history + tags) under --ecosystem-root so the ceremony can read its CHANGELOG (plan S12 step 4.1)"
    return None


def find_open_archive_pr(open_prs: list, branch: str) -> "dict | None":
    """An open PR whose head is this package's archive branch -> reuse it (idempotency, no duplicate)."""
    for pr in open_prs or []:
        if (pr or {}).get("headRefName") == branch:
            return pr
    return None


def halt_issue_payload(pypi_name: str, version: "str | None", reason_key: str, detail: str, when: str) -> dict:
    """The deduplicated HALT-issue payload (plan S8/S11). Title keyed on ``pypi_name`` + ``reason_key``."""
    vtag = f" v{version}" if version else ""
    title = f"[release-train] HALT: {pypi_name} -- {reason_key}"
    body = (
        f"The Juniper release-train ceremony HALTED **{pypi_name}**{vtag} and took no further action on this package.\n\n"
        f"- **Reason ({reason_key}):** {detail}\n"
        f"- **Detected:** {when}\n"
        f"- **Policy:** release-train plan S8 -- a precondition failed, so this package HALTs, this dedup issue is opened/updated, and the ceremony never proceeds on it. A halt on one package does not block the others.\n\n"
        f"Resolve the condition and re-run the ceremony: it re-computes state from PyPI/Release truth and resumes (it never duplicates an archive PR)."
    )
    return {"title": title, "body": body, "reason_key": reason_key}


def classify_publish_run(run: "dict | None") -> str:
    """Map a publish run's status to a ceremony terminal signal (plan S8 TestPyPI gate / S5.1).

    Returns: ``PENDING_PYPI_APPROVAL`` (TestPyPI verify passed; the pypi deploy job is parked at the env
    gate -- SUCCESS for the train), ``HALT_TESTPYPI`` (TestPyPI verify failed before Gate 2),
    ``HALT_PUBLISH`` (the run failed otherwise), ``RELEASED`` (both gates done -- owner already
    approved), ``IN_PROGRESS`` (still running -> keep polling), ``NOT_FOUND`` (no run yet)."""
    if not run:
        return "NOT_FOUND"
    jobs = run.get("jobs") or []

    def named(sub: str) -> list:
        return [j for j in jobs if sub in (j.get("name") or "").lower()]

    testpypi_jobs = named("testpypi")
    pypi_jobs = [j for j in jobs if "pypi" in (j.get("name") or "").lower() and "testpypi" not in (j.get("name") or "").lower()]

    if any((j.get("conclusion") or "").lower() == "failure" for j in testpypi_jobs):
        return "HALT_TESTPYPI"

    run_status = (run.get("status") or "").lower()
    run_conclusion = (run.get("conclusion") or "").lower()
    if run_status == "completed":
        if run_conclusion == "success":
            return "RELEASED"
        if run_conclusion in ("failure", "cancelled", "timed_out"):
            return "HALT_PUBLISH"

    testpypi_ok = bool(testpypi_jobs) and all((j.get("conclusion") or "").lower() == "success" for j in testpypi_jobs)
    pypi_parked = bool(pypi_jobs) and all((j.get("status") or "").lower() in ("waiting", "queued", "pending", "") for j in pypi_jobs)
    # The run's top-level status is 'waiting' while parked at the owner-gated `pypi` deployment env
    # (verified: a documented workflow-run status that `gh run view --json status` passes through). The
    # job-level (testpypi succeeded + pypi job parked) check is the belt-and-suspenders fallback.
    if run_status == "waiting" or (testpypi_ok and pypi_parked):
        return "PENDING_PYPI_APPROVAL"
    return "IN_PROGRESS"


# ── data model ───────────────────────────────────────────────────────────────


@dataclass
class CeremonyAction:
    """One planned ceremony step. ``kind`` is the machine label the tests assert the sequence of."""

    kind: str  # open_archive_pr | enable_auto_merge | cut_release | monitor_publish | halt_issue
    summary: str
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "summary": self.summary, "detail": self.detail}


@dataclass
class CeremonyPlan:
    """The full ceremony plan for one BUMPED_NOT_RELEASED package (or a halt / skip / no-op)."""

    pypi_name: str
    repo: str  # the OWNING repo -- where the Release is cut + the publish run monitored (plan S10.2)
    released_version: "str | None"
    target_version: "str | None"
    tag: "str | None" = None
    archive_repo: str = detect.META_REPO  # the exempt notes-archive PR is ALWAYS central in juniper-ml (plan S10.2)
    state: str = "CEREMONY_PLANNED"  # CEREMONY_PLANNED | RESUME_MONITOR | ALREADY_RELEASED | HALTED | SKIPPED_CROSS_REPO
    halted: bool = False
    halt_reason: "str | None" = None
    skipped_reason: "str | None" = None
    actions: list = field(default_factory=list)
    archive_relpath: "str | None" = None
    archive_content: "str | None" = None
    archive_branch: "str | None" = None
    issue: "dict | None" = None
    notes: list = field(default_factory=list)

    @property
    def action_kinds(self) -> list:
        return [a.kind for a in self.actions]

    def to_dict(self) -> dict:
        return {
            "pypi_name": self.pypi_name,
            "repo": self.repo,
            "archive_repo": self.archive_repo,
            "released_version": self.released_version,
            "target_version": self.target_version,
            "tag": self.tag,
            "state": self.state,
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            "skipped_reason": self.skipped_reason,
            "archive_relpath": self.archive_relpath,
            "archive_branch": self.archive_branch,
            "issue": self.issue,
            "actions": [a.to_dict() for a in self.actions],
            "notes": self.notes,
        }


# ── injectable seam (all external effects) ───────────────────────────────────


@dataclass
class CeremonySources:
    """External effects the ceremony needs, injected for hermetic testing.

    The read/query members are used by the planner (safe in ``--dry-run``); the write members
    (``open_archive_pr`` / ``enable_automerge`` / ``create_release`` / ``upsert_halt_issue``) are
    execute-only and may be ``None`` in a read-only seam. ``create_branch`` / ``create_signed_commit`` are
    the archive lane's two API helpers (the GitHub-signed-commit path) that ``open_archive_pr`` composes;
    the live seam exposes them so the seam-surface tests can drive each directly."""

    pypi_json: Callable[[str], "dict | None"]
    read_file: Callable[["detect.PackageEntry", str], "str | None"]
    main_ci_conclusion: Callable[[str], "str | None"]
    list_open_prs: Callable[[str], list]
    release_exists: Callable[[str, str], bool]
    archive_on_main: Callable[[str], bool]
    publish_run_status: Callable[[str, str], "dict | None"]
    open_archive_pr: "Callable[..., str] | None" = None
    enable_automerge: "Callable[..., bool] | None" = None
    create_release: "Callable[..., str] | None" = None
    upsert_halt_issue: "Callable[..., str] | None" = None
    create_branch: "Callable[..., tuple] | None" = None
    create_signed_commit: "Callable[..., str] | None" = None


def make_live_sources(owner: str, repo_root: Path, ecosystem_root: Path, *, allowed_repos: "frozenset[str] | None" = None, gh: "Callable | None" = None, git: "Callable | None" = None) -> CeremonySources:
    """The live seam. Every ``gh`` call is routed through ``_assert_gh_allowed`` (the R7 code gate).

    ``allowed_repos`` (Phase 4.1) is the registry-derived ``owner/<repo>`` allowlist bounding every
    ``--repo`` argument to the 8 publishing repos; ``main`` always supplies it (via
    ``publishing_repo_slugs``). ``gh`` / ``git`` are injectable so the seam-surface test can drive the
    real argv construction with a recording fake -- proving the live surface is exactly the R7-permitted
    set, hermetically."""
    gh = gh or _gh
    git = git or _git

    def _cgh(args: list, timeout: int = 90) -> "str | None":
        _assert_gh_allowed(args, allowed_repos)  # CODE half of the R7 invariant: a forbidden call (or an out-of-allowlist --repo) raises before gh runs
        return gh(args, timeout)

    def _repo_dir(repo: str) -> Path:
        return repo_root if repo == detect.META_REPO else (ecosystem_root / repo)

    def pypi_json(name: str) -> "dict | None":
        return detect._http_get_json(detect.PYPI_JSON_URL.format(name=name))

    def read_file(entry: "detect.PackageEntry", filename: str) -> "str | None":
        target = detect.base_dir_for(entry, repo_root, ecosystem_root) / filename
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def main_ci_conclusion(repo: str) -> "str | None":
        out = _cgh(["run", "list", "--repo", f"{owner}/{repo}", "--branch", "main", "--limit", "1", "--json", "conclusion,status", "--jq", ".[0].conclusion"])
        return (out or "").strip() or None

    def list_open_prs(repo: str) -> list:
        out = _cgh(["pr", "list", "--repo", f"{owner}/{repo}", "--state", "open", "--json", "number,title,headRefName", "--limit", "100"])
        if not out:
            return []
        try:
            return json.loads(out) or []
        except ValueError as exc:
            raise SourceError(f"gh pr list returned non-JSON for {repo}") from exc

    def release_exists(repo: str, tag: str) -> bool:
        out = _cgh(["release", "view", tag, "--repo", f"{owner}/{repo}", "--json", "tagName", "--jq", ".tagName"])
        return bool((out or "").strip())

    def archive_on_main(relpath: str) -> bool:
        # Remote-authoritative git read (no local-branch truth, plan S8 remote-freshness): is the file
        # present on origin/main? A best-effort fetch keeps origin/main current.
        git(_repo_dir(detect.META_REPO), ["fetch", "--quiet", "origin", "main"], 120, False)
        return git(_repo_dir(detect.META_REPO), ["cat-file", "-e", f"origin/main:{relpath}"], 60, False) is not None

    def publish_run_status(repo: str, tag: str) -> "dict | None":
        out = _cgh(["run", "list", "--repo", f"{owner}/{repo}", "--event", "release", "--json", "databaseId,headBranch,displayTitle,status,conclusion", "--limit", "20"])
        runs = json.loads(out) if out else []
        match = next((r for r in runs if tag in (r.get("displayTitle") or "") or tag == (r.get("headBranch") or "")), None)
        if match is None:
            return None
        out2 = _cgh(["run", "view", str(match["databaseId"]), "--repo", f"{owner}/{repo}", "--json", "status,conclusion,jobs"])
        data = json.loads(out2) if out2 else {}
        return {
            "status": data.get("status"),
            "conclusion": data.get("conclusion"),
            "jobs": [{"name": j.get("name"), "status": j.get("status"), "conclusion": j.get("conclusion")} for j in (data.get("jobs") or [])],
        }

    def create_branch(repo: str, branch: str, from_sha: str) -> "tuple[str, bool]":
        # Create refs/heads/<branch> at <from_sha> via REST (POST /repos/<owner>/<repo>/git/refs).
        # Returns (effective_head_oid, already_committed): the head oid the subsequent signed commit must
        # thread as expectedHeadOid, and whether the branch ALREADY carries our archive commit (so the
        # caller must NOT re-commit). Idempotent re-entry (the branch survives a prior partial run):
        #   * branch does not exist            -> create it at main; (from_sha, False).
        #   * exists, tip == from_sha (at main)-> reuse; commit onto it; (from_sha, False).
        #   * exists, tip is ONE commit atop main (tip^ == from_sha == our single-file archive commit)
        #                                       -> reuse as-is, no re-commit; (tip, True).
        #   * exists, diverged / multi-commit  -> SourceError (a human must resolve; the existing HALT
        #                                          semantics -- the planner's PR-open / on-main dup-guards
        #                                          normally prevent ever reaching here).
        try:
            _cgh(["api", f"repos/{owner}/{repo}/git/refs", "-X", "POST", "-f", f"ref=refs/heads/{branch}", "-f", f"sha={from_sha}"])
            return (from_sha, False)
        except SourceError as exc:
            if "already exists" not in str(exc).lower() and "422" not in str(exc):
                raise  # a genuine transport/auth failure, not the idempotent branch-exists case
        rdir = _repo_dir(repo)
        git(rdir, ["fetch", "--quiet", "origin", branch], 120, False)
        tip = (git(rdir, ["rev-parse", "FETCH_HEAD"], 30, False) or "").strip()
        if not tip:
            raise SourceError(f"archive branch {branch} exists on origin but its tip could not be resolved -- resolve by hand")
        if tip == from_sha:
            return (from_sha, False)
        parent = (git(rdir, ["rev-parse", f"{tip}^"], 30, False) or "").strip()
        if parent == from_sha:
            return (tip, True)
        raise SourceError(f"archive branch {branch} exists but diverged from base {from_sha[:8]} (tip {tip[:8]}, parent {parent[:8]}) -- a human must resolve (idempotent re-entry expects the branch at base or carrying only the single archive commit)")

    def create_signed_commit(repo: str, branch: str, message: str, path: str, content_b64: str, expected_head_oid: str) -> str:
        # Add the single archive file via the GraphQL createCommitOnBranch mutation. A commit authored
        # through GitHub's API under the App / GITHUB_TOKEN identity is GitHub-signed / Verified, so the
        # exempt archive PR satisfies the ruleset's required_signatures rule (hands-free auto-merge).
        # expectedHeadOid pins optimistic concurrency to the branch tip create_branch just resolved.
        out = _cgh(
            [
                "api",
                "graphql",
                "-f",
                f"query={_CREATE_COMMIT_ON_BRANCH_MUTATION}",
                "-f",
                f"repoWithOwner={owner}/{repo}",
                "-f",
                f"branch={branch}",
                "-f",
                f"headline={message}",
                "-f",
                f"path={path}",
                "-f",
                f"contents={content_b64}",
                "-f",
                f"expectedHeadOid={expected_head_oid}",
            ]
        )
        try:  # best-effort: return the created commit oid (callers use the PR URL from gh pr create)
            data = json.loads(out) if out else {}
            return (((data.get("data") or {}).get("createCommitOnBranch") or {}).get("commit") or {}).get("oid") or ""
        except ValueError:
            return ""

    def open_archive_pr(repo: str, base: str, branch: str, relpath: str, content: str, title: str, body: str) -> str:
        # The archive branch AND its single-file commit are created through the GitHub API so the commit
        # is GitHub-signed / Verified (2026-07-23 ml#707: a plain unsigned runner commit left the armed
        # auto-merge BLOCKED behind the ruleset's required_signatures rule). No local checkout switch, no
        # local commit, no push -- git is used only for READS here (freshen origin/<base>, resolve the
        # base sha), so nothing to capture/restore. The archive PR is ALWAYS in juniper-ml (plan S10.2),
        # where both token modes hold contents:write, so this API path is unconditional (no git fallback).
        rdir = _repo_dir(repo)
        git(rdir, ["fetch", "--quiet", "origin", base], 120, False)
        base_sha = (git(rdir, ["rev-parse", f"origin/{base}"], 30, False) or "").strip()
        if not base_sha:
            raise SourceError(f"could not resolve origin/{base} in {rdir} to base the archive branch on")
        head_oid, already_committed = create_branch(repo, branch, base_sha)
        if not already_committed:
            content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
            create_signed_commit(repo, branch, title, relpath, content_b64, head_oid)
        return (_cgh(["pr", "create", "--repo", f"{owner}/{repo}", "--base", base, "--head", branch, "--title", title, "--body", body]) or "").strip()

    def enable_automerge(repo: str, pr: str) -> bool:
        # Graceful degrade (plan S12 step 3.3 not yet landed -> allow_auto_merge may be off): a failure
        # to ENABLE --auto is the owner one-click fallback, NOT a halt. SeamViolation still propagates.
        try:
            _cgh(["pr", "merge", str(pr), "--repo", f"{owner}/{repo}", "--auto", "--squash"])
            return True
        except SourceError:
            return False

    def create_release(repo: str, tag: str, title: str, notes_relpath: str, content: str) -> str:
        # Render the notes body to a SCRATCH temp file (never into any checkout). The archived copy
        # already rode the exempt archive PR into juniper-ml's central notes/releases/ (``notes_relpath``,
        # kept for the record/log); writing it into the OWNING checkout here left a stray untracked file
        # that dirtied the tree (07-19 live run). --notes-file takes the temp path. --latest=false: a
        # sub-package Release never steals the meta-package's "latest" badge (procedure S11.4). NO
        # --verify-tag: the Release CREATES the tag. The cross-repo Release is cut on the owning repo via
        # --repo owner/<repo>; gh does not need a local checkout of it (the temp notes file suffices).
        fd, tmp_path = tempfile.mkstemp(prefix="release-notes-", suffix=".md")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            return (_cgh(["release", "create", tag, "--repo", f"{owner}/{repo}", "--title", title, "--notes-file", tmp_path, "--latest=false"]) or "").strip()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def upsert_halt_issue(repo: str, title: str, body: str) -> str:
        existing = _cgh(["issue", "list", "--repo", f"{owner}/{repo}", "--state", "open", "--search", f"in:title {title}", "--json", "number", "--jq", ".[0].number"])
        num = (existing or "").strip()
        if num:
            return (_cgh(["issue", "edit", num, "--repo", f"{owner}/{repo}", "--body", body]) or "").strip()
        return (_cgh(["issue", "create", "--repo", f"{owner}/{repo}", "--title", title, "--body", body]) or "").strip()

    return CeremonySources(
        pypi_json=pypi_json,
        read_file=read_file,
        main_ci_conclusion=main_ci_conclusion,
        list_open_prs=list_open_prs,
        release_exists=release_exists,
        archive_on_main=archive_on_main,
        publish_run_status=publish_run_status,
        open_archive_pr=open_archive_pr,
        enable_automerge=enable_automerge,
        create_release=create_release,
        upsert_halt_issue=upsert_halt_issue,
        create_branch=create_branch,
        create_signed_commit=create_signed_commit,
    )


# ── planner (pure decisions; reads only) ─────────────────────────────────────


def _halt(plan: CeremonyPlan, reason_key: str, detail: str, when: str) -> CeremonyPlan:
    plan.state = "HALTED"
    plan.halted = True
    plan.halt_reason = detail
    plan.issue = halt_issue_payload(plan.pypi_name, plan.target_version, reason_key, detail, when)
    plan.actions = [CeremonyAction("halt_issue", f"open/update the dedup HALT issue: {plan.issue['title']}", {"issue": plan.issue})]
    return plan


def _monitor_action(tag: str) -> CeremonyAction:
    return CeremonyAction(
        "monitor_publish",
        f"monitor the publish run triggered by Release {tag}; report PENDING_PYPI_APPROVAL when it parks at the pypi env gate (SUCCESS for the train); a TestPyPI-verify failure before Gate 2 HALTs",
        {"tag": tag},
    )


def plan_ceremony(entry: "detect.PackageEntry", pkg: dict, sources: CeremonySources, repo_root: Path, ecosystem_root: Path, when: str, *, cross_repo: bool = False) -> CeremonyPlan:
    """Compute the ceremony plan for one BUMPED_NOT_RELEASED manifest package (reads only; no writes).

    ``plan.repo`` is the OWNING repo (Release + monitor); ``plan.archive_repo`` stays juniper-ml (the
    central exempt archive PR, plan S10.2). ``cross_repo`` unlocks a sibling when its checkout is present."""
    target = pkg.get("declared_version")
    plan = CeremonyPlan(pypi_name=entry.pypi_name, repo=entry.repo, released_version=pkg.get("released_version"), target_version=target)

    # 0. capability guard (Phase 4.1): in-repo always; a sibling only when --cross-repo-capable AND its
    # checkout is on disk. The exempt archive PR is ALWAYS central (plan.archive_repo == juniper-ml).
    reason = writable_repo_skip_reason(entry.repo, cross_repo_capable=cross_repo, ecosystem_root=ecosystem_root)
    if reason is not None:
        plan.state, plan.skipped_reason = "SKIPPED_CROSS_REPO", reason
        return plan

    if not target:
        return _halt(plan, "missing-declared-version", "manifest has no declared_version for a BUMPED_NOT_RELEASED package", when)

    # 1. idempotency + the S8 declared>=released re-check against LIVE PyPI truth (remote-authoritative).
    pypi = sources.pypi_json(entry.pypi_name)
    released_now = (pypi or {}).get("info", {}).get("version") if pypi else None
    plan.released_version = released_now or plan.released_version
    if released_now:
        cmpv = detect.version_cmp(target, released_now)
        if cmpv == 0:
            plan.state = "ALREADY_RELEASED"
            plan.notes.append(f"PyPI already serves {target}: the deploy completed; nothing to do (idempotent no-op).")
            return plan
        if cmpv < 0:
            return _halt(plan, "declared-lt-released-anomaly", f"declared {target} < released {released_now}: a yanked/rolled-back anomaly a human must resolve", when)
    elif plan.released_version:
        return _halt(plan, "pypi-truth-missing", f"manifest said released {plan.released_version} but PyPI now returns no version -- a first-publish/yank a human must resolve (trusted-publisher precheck, plan S8)", when)

    plan.tag = release_tag(entry, target)
    plan.archive_relpath = archive_relpath(entry, target)
    plan.archive_branch = archive_branch(entry.pypi_name, target)

    # 2. S8: target main CI must be green.
    conclusion = sources.main_ci_conclusion(entry.repo)
    if conclusion != "success":
        return _halt(plan, "main-ci-not-green", f"target main CI latest conclusion is {conclusion!r}, not 'success' -- do not cut a Release onto a red main", when)

    # 3. build the FINAL central notes file from the released CHANGELOG [<version>] section.
    clog = sources.read_file(entry, changelog_rel(entry))
    sections = changelog_version_section(clog or "", target)
    if not sections:
        return _halt(plan, "changelog-section-missing", f"no non-empty CHANGELOG [{target}] section to source the release notes from (the proposal PR should have created it)", when)
    bump = infer_bump(plan.released_version, target)
    try:
        plan.archive_content = notes_render.render_notes(entry.pypi_name, target, bump=bump, release_date=when, sections=sections, repo_root=repo_root)
    except OSError as exc:
        return _halt(plan, "notes-render-failed", f"could not render the release notes template: {exc}", when)

    # 4. idempotent re-entry from Release/PR truth (plan S8 last row; dup-guard).
    if sources.release_exists(entry.repo, plan.tag):
        plan.state = "RESUME_MONITOR"
        plan.notes.append(f"Release {plan.tag} already exists: resume monitoring only (no re-cut, no duplicate archive PR).")
        plan.actions = [_monitor_action(plan.tag)]
        return plan

    # The exempt archive PR lives in the CENTRAL archive repo (juniper-ml), so its dup-guard + the
    # on-main idempotency check both reason about juniper-ml -- NOT the owning repo (plan S10.2). For an
    # in-repo package archive_repo == repo, so this is unchanged from Phase 3.
    open_pr = find_open_archive_pr(sources.list_open_prs(plan.archive_repo), plan.archive_branch)
    on_main = sources.archive_on_main(plan.archive_relpath)

    actions: list = []
    if open_pr is not None:
        plan.notes.append(f"archive PR already open (#{open_pr.get('number')} {open_pr.get('headRefName')}): reuse it (no duplicate).")
    elif on_main:
        plan.notes.append(f"archive file already on main ({plan.archive_relpath}): skip the archive PR; cut the Release.")
    else:
        actions.append(CeremonyAction("open_archive_pr", f"open the exempt add-only archive PR ({plan.archive_relpath}) on branch {plan.archive_branch} -- the single-file diff the S7.2 guard proves", {"relpath": plan.archive_relpath, "branch": plan.archive_branch, "title": f"release-notes: {entry.pypi_name} v{target}"}))

    if not on_main:
        actions.append(CeremonyAction("enable_auto_merge", "enable `gh pr merge --auto --squash` on the archive PR (degrades to the owner one-click merge if allow_auto_merge is off -- step 3.3 not yet landed)", {"branch": plan.archive_branch}))

    actions.append(CeremonyAction("cut_release", f"`gh release create {plan.tag} --latest=false --notes-file {plan.archive_relpath}` -- the Release CREATES the tag (no --verify-tag)", {"tag": plan.tag, "notes_relpath": plan.archive_relpath, "latest": False}))
    actions.append(_monitor_action(plan.tag))
    plan.state = "CEREMONY_PLANNED"
    plan.actions = actions
    return plan


# ── execute (Phase-3 wiring; NEVER run against the real repo in this change) ──


def monitor_publish_run(sources: CeremonySources, repo: str, tag: str, *, timeout_seconds: int = DEFAULT_MONITOR_TIMEOUT_SECONDS, poll_seconds: int = MONITOR_POLL_SECONDS, sleep: "Callable[[float], None]" = time.sleep, monotonic: "Callable[[], float]" = time.monotonic) -> str:
    """Poll the triggered publish run until a terminal ceremony signal or a bounded timeout (plan S8 / §12-3.2).

    Polls ``publish_run_status`` at ``poll_seconds`` for up to ``timeout_seconds`` (a bounded wall clock).
    Returns as soon as ``classify_publish_run`` reaches a terminal signal: ``PENDING_PYPI_APPROVAL`` (the
    run parked at the owner-gated ``pypi`` env -- its GitHub status is ``waiting`` -- which is SUCCESS for
    the train), ``RELEASED``, or a HALT. If the timeout elapses while the run is still building it returns
    ``IN_PROGRESS`` -- now an honest 'still building' rather than a premature give-up; the ceremony is
    idempotent, so a re-run resumes at the monitor. ``monotonic`` is injected for hermetic timeout tests."""
    deadline = monotonic() + max(0, timeout_seconds)
    while True:
        verdict = classify_publish_run(sources.publish_run_status(repo, tag))
        if verdict in ("PENDING_PYPI_APPROVAL", "HALT_TESTPYPI", "HALT_PUBLISH", "RELEASED"):
            return verdict
        if monotonic() >= deadline:
            return "IN_PROGRESS"
        sleep(poll_seconds)


def _file_halt_issue(sources: CeremonySources, repo: str, issue: dict, result: dict, *, warn: "Callable[[str], None]" = _warn) -> dict:
    """Upsert the dedup HALT issue, degrading GRACEFULLY if the ``gh issue`` API fails (plan S8/S11).

    A failed ``gh issue create``/``edit`` -- most plausibly the cross-repo GitHub App token lacking the
    **Issues** permission (owner-grantable later; plan S11 failure-issues) -- must NOT crash the ceremony
    run: the package is STILL HALTED, so this emits a LOUD operator log line and records a step-summary-
    visible flag (``halt_issue_failed``) + note, then continues -- the other packages still run and the
    run's step summary + Slack still surface the HALT. Only ``SourceError`` (a runtime gh/transport/auth
    failure) is degraded; ``SeamViolation`` (an R7 *code* bug -- a sibling ``RuntimeError``, NOT a
    ``SourceError`` subclass) is deliberately NOT caught and still propagates. A missing seam member is a
    developer wiring error, not a runtime condition, so it raises OUTSIDE the try (unchanged behaviour).
    The R7 ``gh`` surface is unchanged: this wraps the SAME ``upsert_halt_issue`` seam member."""
    if sources.upsert_halt_issue is None:
        raise SourceError("execute needs the upsert_halt_issue seam member")
    try:
        result["issue_url"] = sources.upsert_halt_issue(repo, issue["title"], issue["body"])
    except SourceError as exc:
        result["issue_url"] = None
        result["halt_issue_failed"] = True
        result["halt_issue_error"] = str(exc)
        msg = (
            f"release-train ceremony: could NOT file the HALT issue for {result.get('pypi_name')} in {repo} ({exc}). "
            f"The package is STILL HALTED -- file the issue manually. The cross-repo GitHub App token may lack the "
            f"Issues permission (plan S8/S11); the run's step summary + Slack still surface this HALT."
        )
        warn(msg)
        result["notes"].append(msg)
    return result


def execute_ceremony(plan: CeremonyPlan, sources: CeremonySources, base_branch: str = "main", *, monitor_kwargs: "dict | None" = None) -> dict:
    """Perform a plan's actions in order via the seam. Opt-in (``--execute``); never the dry-run default.

    Returns a result dict (final state + any PR/Release URLs). A halt files/updates the dedup issue and
    stops. Auto-merge failure degrades to the owner one-click fallback (a note, not a halt)."""
    # plan_state (the classification) is kept alongside the mutable state (the final verdict) so the
    # workflow's ceremony step summary can bucket ceremonies vs resumes vs halts; target_version feeds
    # the same machine-parseable summary line (main's --execute output).
    result: dict = {"pypi_name": plan.pypi_name, "repo": plan.repo, "plan_state": plan.state, "target_version": plan.target_version, "state": plan.state, "pr_url": None, "release_url": None, "notes": list(plan.notes)}

    if plan.state == "SKIPPED_CROSS_REPO":
        result["skipped_reason"] = plan.skipped_reason
        return result

    pr_ref: "str | None" = None
    for action in plan.actions:
        if action.kind == "halt_issue":
            # Graceful degradation: a gh-issue-API failure (e.g. the App token lacks Issues) does NOT
            # crash the run -- the package stays HALTED, loudly logged + step-summary-flagged (plan S11).
            _file_halt_issue(sources, plan.repo, plan.issue, result)
            result["state"] = "HALTED"
            return result
        if action.kind == "open_archive_pr":
            if sources.open_archive_pr is None:
                raise SourceError("execute needs the open_archive_pr seam member")
            # The exempt archive PR is ALWAYS opened in the central archive repo (juniper-ml), even for a
            # cross-repo package whose Release is cut elsewhere (plan S10.2).
            pr_ref = sources.open_archive_pr(plan.archive_repo, base_branch, plan.archive_branch, plan.archive_relpath, plan.archive_content, action.detail.get("title") or plan.archive_branch, _archive_pr_body(plan))
            result["pr_url"] = pr_ref
        elif action.kind == "enable_auto_merge":
            if sources.enable_automerge is None:
                raise SourceError("execute needs the enable_automerge seam member")
            # Auto-merge the central archive PR (juniper-ml), where it lives.
            enabled = sources.enable_automerge(plan.archive_repo, pr_ref or plan.archive_branch)
            if not enabled:
                result["notes"].append("auto-merge could not be enabled (allow_auto_merge off? -- step 3.3); owner one-click merge fallback (NOT a halt).")
            result["auto_merge_enabled"] = enabled
        elif action.kind == "cut_release":
            if sources.create_release is None:
                raise SourceError("execute needs the create_release seam member")
            result["release_url"] = sources.create_release(plan.repo, plan.tag, f"{plan.pypi_name} v{plan.target_version}", plan.archive_relpath, plan.archive_content)
        elif action.kind == "monitor_publish":
            verdict = monitor_publish_run(sources, plan.repo, plan.tag, **(monitor_kwargs or {}))
            if verdict == "HALT_TESTPYPI":
                if sources.upsert_halt_issue is not None:
                    issue = halt_issue_payload(plan.pypi_name, plan.target_version, "testpypi-verify-failed", "the publish workflow's TestPyPI install-verify step failed before Gate 2 -- the run is not healthy", _today())
                    # Same graceful degradation as the precondition HALT: a gh-issue-API failure never crashes the run.
                    _file_halt_issue(sources, plan.repo, issue, result)
                result["state"] = "HALTED"
                return result
            if verdict == "HALT_PUBLISH":
                result["state"] = "HALTED"
                result["notes"].append("the publish run failed before the pypi gate.")
                return result
            result["state"] = verdict  # PENDING_PYPI_APPROVAL (success) / RELEASED / IN_PROGRESS
    return result


def _archive_pr_body(plan: CeremonyPlan) -> str:
    return (
        f"## Release-notes archive: `{plan.pypi_name}` v{plan.target_version}\n\n"
        f"Auto-generated by the Juniper release-train ceremony (`util/release_train/ceremony.py`).\n\n"
        f"This PR **adds a single file** -- `{plan.archive_relpath}` -- and nothing else. It is the "
        f"gate-exempt notes-archive PR (plan §7 / R5); the `release-train-archive-guard` check proves the "
        f"diff is add-only, path-confined, name-valid, and single-purpose, which is why it may auto-merge "
        f"behind that required check. It deploys nothing: the PyPI deploy is the subsequent Release cut, "
        f"whose publish workflow waits at the owner-gated `pypi` environment (R7).\n"
    )


# ── output ───────────────────────────────────────────────────────────────────


def _print_plan(plan: CeremonyPlan) -> None:
    print("=" * 78)
    if plan.state == "SKIPPED_CROSS_REPO":
        print(f"SKIP  {plan.pypi_name}  ({plan.repo})")
        print(f"      {plan.skipped_reason}")
        print()
        return
    if plan.halted:
        print(f"HALT  {plan.pypi_name}  v{plan.target_version}  ({plan.repo})")
        print(f"      reason: {plan.halt_reason}")
        print(f"      issue:  {plan.issue['title'] if plan.issue else '-'}")
        print()
        return
    header = {"ALREADY_RELEASED": "DONE", "RESUME_MONITOR": "RESUME", "CEREMONY_PLANNED": "CEREMONY"}.get(plan.state, plan.state)
    print(f"{header}  {plan.pypi_name}  {plan.released_version} -> {plan.target_version}  ({plan.repo})")
    if plan.tag:
        print(f"  tag:     {plan.tag}")
    if plan.archive_repo != plan.repo:
        print(f"  cross-repo: Release cut on {plan.repo}; exempt archive PR in {plan.archive_repo} (central, plan S10.2)")
    if plan.archive_relpath:
        print(f"  archive: {plan.archive_relpath}")
    for note in plan.notes:
        print(f"  - {note}")
    if plan.actions:
        print("  planned ceremony script (in order):")
        for i, action in enumerate(plan.actions, 1):
            print(f"    {i}. [{action.kind}] {action.summary}")
    else:
        print("  (no actions -- nothing to do)")
    print()


def print_plans(plans: list, dry_run: bool) -> None:
    mode = "DRY-RUN (report-only; writes nothing, opens nothing, cuts nothing)" if dry_run else "EXECUTE"
    print(f"Juniper PyPI release-train -- ceremony [{mode}]")
    print()
    if not plans:
        print("  no BUMPED_NOT_RELEASED packages in the manifest -- nothing to do.")
        return
    for plan in plans:
        _print_plan(plan)
    ceremonies = sum(1 for p in plans if p.state == "CEREMONY_PLANNED")
    resumes = sum(1 for p in plans if p.state == "RESUME_MONITOR")
    halted = sum(1 for p in plans if p.halted)
    skipped = sum(1 for p in plans if p.state == "SKIPPED_CROSS_REPO")
    done = sum(1 for p in plans if p.state == "ALREADY_RELEASED")
    print("=" * 78)
    print(f"  {len(plans)} package(s): {ceremonies} ceremony, {resumes} resume-monitor, {done} already-released, {skipped} skipped, {halted} HALTED.")


def build_output(plans: list, dry_run: bool) -> dict:
    return {
        "schema": "juniper-release-train/ceremony/v1",
        "generated_by": "util/release_train/ceremony.py",
        "dry_run": dry_run,
        "summary": {
            "total": len(plans),
            "ceremony": sum(1 for p in plans if p.state == "CEREMONY_PLANNED"),
            "resume_monitor": sum(1 for p in plans if p.state == "RESUME_MONITOR"),
            "already_released": sum(1 for p in plans if p.state == "ALREADY_RELEASED"),
            "skipped": sum(1 for p in plans if p.state == "SKIPPED_CROSS_REPO"),
            "halted": sum(1 for p in plans if p.halted),
        },
        "plans": [p.to_dict() for p in plans],
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="release_train/ceremony.py", description="Run the exempt-archive + Release ceremony for BUMPED_NOT_RELEASED packages (plan S7/S8/S10). Dry-run by default.")
    default_repo_root = Path(__file__).resolve().parents[2]
    p.add_argument("--manifest", required=True, help="path to the release-manifest JSON emitted by detect.py (--json)")
    p.add_argument("--package", action="append", metavar="PYPI_NAME", help="restrict to these pypi_name(s) (repeatable)")
    p.add_argument("--repo-root", default=str(default_repo_root), help="juniper-ml checkout root (CHANGELOG/notes reads + central notes/releases/)")
    p.add_argument("--ecosystem-root", default=None, help="parent dir holding sibling repos (default: --repo-root's parent)")
    p.add_argument("--owner", default=DEFAULT_OWNER, help=f"GitHub owner (default: {DEFAULT_OWNER})")
    p.add_argument("--registry", default=None, help="path to registry.yaml (default: alongside detect.py)")
    p.add_argument("--release-date", default=None, help="release date for the notes (default: today UTC; use for deterministic output)")
    p.add_argument("--dry-run", action="store_true", help="(default) print the full ceremony script of actions; write nothing, open nothing, cut nothing. Overrides --execute.")
    p.add_argument("--execute", action="store_true", help="opt-in: perform the ceremony (archive PR + auto-merge + Release + monitor). --dry-run overrides it.")
    p.add_argument("--cross-repo", action="store_true", help="Phase 4.1: this run has a cross-repo write identity (the GitHub App installation token). With it AND a sibling checkout under --ecosystem-root, a sibling's Release is cut on ITS repo (--repo owner/<repo>) while the exempt archive PR still lands centrally in juniper-ml; without it, sibling packages are skipped. No effect in --dry-run.")
    p.add_argument("--json", action="store_true", help="emit the ceremony plans as JSON instead of the human report")
    p.add_argument("--monitor-timeout", type=int, default=DEFAULT_MONITOR_TIMEOUT_SECONDS, metavar="SECONDS", help=f"max seconds the (--execute) monitor polls the publish run for the pypi-env-gate 'waiting' state before reporting a still-building IN_PROGRESS (default: {DEFAULT_MONITOR_TIMEOUT_SECONDS} = ~15 min)")
    return p.parse_args(argv)


def _plans_for(manifest_pkgs: list, entries: list, wanted: "set | None", sources: CeremonySources, repo_root: Path, ecosystem_root: Path, when: str, *, cross_repo: bool = False) -> list:
    by_name = {e.pypi_name: e for e in entries}
    plans: list = []
    for pkg in manifest_pkgs:
        name = pkg.get("pypi_name")
        if pkg.get("classification") != CEREMONIAL:
            continue
        if wanted and name not in wanted:
            continue
        entry = by_name.get(name)
        if entry is None:
            plan = CeremonyPlan(pypi_name=name or "?", repo=pkg.get("repo") or "?", released_version=pkg.get("released_version"), target_version=pkg.get("declared_version"))
            _halt(plan, "not-in-registry", "package is BUMPED_NOT_RELEASED in the manifest but absent from registry.yaml", when)
            plans.append(plan)
            continue
        plans.append(plan_ceremony(entry, pkg, sources, repo_root, ecosystem_root, when, cross_repo=cross_repo))
    return plans


def main(argv: "list[str] | None" = None, sources: "CeremonySources | None" = None) -> int:
    args = parse_args(argv)
    dry_run = args.dry_run or not args.execute  # dry-run is the default and always wins for safety
    repo_root = Path(args.repo_root).resolve()
    ecosystem_root = Path(args.ecosystem_root).resolve() if args.ecosystem_root else repo_root.parent
    when = args.release_date or _today()

    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read manifest {args.manifest}: {exc}", file=sys.stderr)
        return 2
    manifest_pkgs = manifest.get("packages") if isinstance(manifest, dict) else None
    if not isinstance(manifest_pkgs, list):
        print("ERROR: manifest has no 'packages' list (expected detect.py --json output)", file=sys.stderr)
        return 2

    try:
        entries = detect.load_registry(args.registry)
    except Exception as exc:  # noqa: BLE001 - a missing/broken registry is an invocation error
        print(f"ERROR: cannot load registry: {exc}", file=sys.stderr)
        return 2
    if not entries:
        print("ERROR: registry is empty", file=sys.stderr)
        return 2

    wanted = set(args.package) if args.package else None
    if wanted:
        unknown = wanted - {e.pypi_name for e in entries}
        if unknown:
            print(f"ERROR: unknown --package {sorted(unknown)}", file=sys.stderr)
            return 2

    if sources is None:
        # Bound every --repo argument to the registry's 8 publishing repos (R7 --repo value guard, Phase 4.1).
        sources = make_live_sources(args.owner, repo_root, ecosystem_root, allowed_repos=publishing_repo_slugs(entries, args.owner))

    try:
        plans = _plans_for(manifest_pkgs, entries, wanted, sources, repo_root, ecosystem_root, when, cross_repo=args.cross_repo)
    except SourceError as exc:
        print(f"ERROR: source failure during ceremony planning: {exc}", file=sys.stderr)
        return 2

    if not dry_run:
        results = []
        try:
            for plan in plans:
                results.append(execute_ceremony(plan, sources, monitor_kwargs={"timeout_seconds": args.monitor_timeout}))
        except SourceError as exc:
            print(f"ERROR: execute failed: {exc}", file=sys.stderr)
            return 2
        if not results:
            print("ceremony-run: no BUMPED_NOT_RELEASED packages in the manifest -- nothing to do (execute).")
        # Stable machine-parseable line per result (mirrors propose.py's grep-prefix convention so the
        # release-train.yml ceremony step summary can bucket ceremonies/resumes/HALTs/PENDING_PYPI_APPROVAL
        # deterministically). Values are space-free (pypi_name/version/repo/URLs), so key=value split is safe.
        for r in results:
            print(
                "ceremony-result:"
                f" plan={r.get('plan_state') or '?'}"
                f" state={r.get('state') or '?'}"
                f" pkg={r.get('pypi_name') or '?'}"
                f" version={r.get('target_version') or '-'}"
                f" repo={r.get('repo') or '-'}"
                f" pr={r.get('pr_url') or '-'}"
                f" release={r.get('release_url') or '-'}"
                f" issue={r.get('issue_url') or '-'}"
                f" issue_failed={'1' if r.get('halt_issue_failed') else '0'}"
            )
        return 1 if any(r["state"] == "HALTED" for r in results) else 0

    if args.json:
        print(json.dumps(build_output(plans, dry_run), indent=2))
    else:
        print_plans(plans, dry_run)
    return 1 if any(p.halted for p in plans) else 0


if __name__ == "__main__":
    sys.exit(main())
