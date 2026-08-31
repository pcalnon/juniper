#!/usr/bin/env python3
"""Juniper PyPI release-train proposal-PR generator (plan S5.4/S6/S10.1/S13; Phase 2.1 engine, wired in 2.2; dependency ordering + follow-on PRs in 4.2).

Consumes the release-manifest JSON emitted by ``detect.py`` (Phase 1.2) and, for every
package the detector classified ``UNRELEASED_CHANGES``, builds the **complete content** of a
single **standard-gated release-proposal PR** (plan S5.4):

  * the version bump edit -- ``[project].version`` for a static package, ``_version.py``
    ``__version__`` for a dynamic one (model-core + the 3 recurrence packages, audit S2). A static
    package that ALSO ships a ``_version.py`` dunder (all five in-repo static packages) gets the
    dunder bumped in lockstep as a co-change edit, auto-detected by file presence -- the ci-tools
    0.7.0 / service-core 0.5.0 stale-dunder incident class (ml#701; gate:
    ``tests/test_release_train_registry.py`` ``VersionDunderLockstepTest``);
  * the CHANGELOG ``[Unreleased]`` -> ``[<version>] - <date>`` move, leaving a fresh empty
    ``[Unreleased]`` behind (Keep-a-Changelog, plan S5.4);
  * a drafted release-notes body from ``notes_render.py`` (the template, plan S10.1) -- shown
    in the PR body, **not** archived to ``notes/releases/`` (archival is the later exempt step);
  * the meta-package's ``AGENTS.md`` ``**Version**`` co-change (plan S5.4; kept in lockstep by
    ``tests/test_agents_md_version_drift.py``) and the S5.4 co-change checklist (lockfile regen,
    version+pin+lint atomicity). A repo whose ``AGENTS.md`` ALSO carries a per-package version TABLE
    gets the released package's row bumped in the same edit (ml#851): juniper-recurrence pins those
    rows against ``_version.py`` with a repo-local ``version-drift`` hook, so a header-only proposal
    shipped red there (recurrence#92 / #93). The table is per-PACKAGE where the header is per-REPO, so
    a sub-package bumps its own row without ever touching the host repo's primary-tracking header;
  * for an **in-repo** package (the meta-package or one of its six co-located sub-packages), the
    meta-package's own **consumer-pin co-changes** (plan S5.4): a pre-1.0 MINOR bump that escapes a
    ``[project.optional-dependencies]`` ``<next-minor`` ceiling moves that pin AND its FIVE lockstep
    artifacts -- the exact-string membership contract in ``tests/test_pyproject_extras.py``, plus the
    four documented extras tables that ``ExtrasDocsLockstepTest`` asserts against ``pyproject.toml``
    (``AGENTS.md``, ``README.md``, ``docs/QUICK_START.md`` inline; ``docs/REFERENCE.md``
    split-column) -- IN THE SAME PR. This is the ml#657 RK-11 failure class (a
    service-core 0.5.0 proposal that bumped the sub-package but not the ``<0.5.0`` meta ceiling, so
    ``tests/test_service_core_drift.py`` failed and the proposal shipped red);

    **The gap that made this three artifacts short was CLOSED here** (found 2026-08-29 on the
    service-core 0.6.0 cut, ml#1458, which failed 3 arms on all three Python versions and had to be
    repaired by hand). ``ExtrasDocsLockstepTest`` asserts ``README.md`` and ``docs/QUICK_START.md``
    with the same inline parser it uses on ``AGENTS.md``, and ``docs/REFERENCE.md`` with a separate
    one; its failure message says "co-update the documented table in the same PR as the pin change".
    All four now move with the pin: the inline three through
    :func:`apply_pin_edits_agents_table` re-anchored per file (``_INLINE_EXTRAS_TABLES``), and
    REFERENCE through :func:`apply_pin_edits_reference_table`.

    Two corrections to how that gap was first written up, both material to anyone extending this:
    ``docs/REFERENCE.md`` needs **ONE** edit, not two -- it has no inline table at all
    (``_pins_from_inline_extras_table`` returns ``{}`` for it, and ``_DOCS_INLINE_TABLES`` omits it),
    only the split-column one where the distribution and its specifier sit in DIFFERENT columns, so a
    substitution on the combined ``name>=x,<y`` string silently misses it -- which is how the first
    hand-repair looked complete and still failed an arm. And the co-change set is **per-package, not
    fixed**: a package pinned by a drift lint carries more. ``juniper-doc-tools`` and
    ``juniper-ci-tools`` are each additionally pinned in ``.github/workflows/`` by
    ``tests/test_doc_tools_drift.py`` / ``test_ci_tools_drift.py``
    (``test_juniper_ml_own_workflows_pin_current_version``, which does NOT skip in per-PR mode), and
    ``.pre-commit-config.yaml`` carries a doc-tools pin no gate reads at all. Those workflow pins are
    NOT edited here -- a bump that escapes their ceiling still needs them by hand, and the co-change
    checklist's version+pin+lint atomicity line is what says so;
  * the ``propagation_edges`` -- a pre-1.0 MINOR bump escapes a consumer's ``<next-minor``
    ceiling pin (plan S6/S13), so each reverse-dependency consumer gets an edge annotated with a
    ``consumer_pin_state`` (``within_range`` / ``floor_only`` / ``escaped -> follow-on`` /
    ``escaped -> skipped(<reason>)``) read from that consumer's REAL pyproject on disk (Phase 4.2);
  * for each escaped CROSS-REPO (non-meta) consumer, a **standard-gated ceiling-bump follow-on PR**
    in that consumer's repo (Phase 4.2, plan S13/D6): the pin edit (ceiling raised to the upstream's
    next-minor, floors preserved), branch ``deps/<upstream>-ceiling-<new-ceiling>``, and a body citing
    S13 + the triggering proposal -- **never** folded into the upstream proposal or the exempt
    notes-archive path (the 2026-07-06 ci-tools incident class; rec#85 is the hand-made model). The
    meta (juniper-ml) is the sole exception -- its pin rides #661's folded co-change when the upstream
    is in-repo and stays MANUAL (Q-META) otherwise; it never gets a follow-on PR;
  * the branch name, commit message, and PR title/body.

When multiple packages are eligible in one run they are processed in **dependency (upstream-first)
order** (Phase 4.2, plan S13/D6): a deterministic topological sort of the registry ``depends_on`` DAG
(shared libs -> sub-libs -> apps -> meta) with a lexicographic ``pypi_name`` tie-break -- derived from
the registry, NOT hardcoded tiers. A cyclic ``depends_on`` graph is a hard error (exit 2) naming the
cycle.

The proposal PR is **dup-guarded**: before proposing, the train runs ``gh pr list`` for an
existing open release PR for the package (concurrent Claude sessions are a real hazard) and
refuses to duplicate it. A ``changelog_conflict`` flagged by the detector is a **refusal**:
the train will not auto-author notes / move a CHANGELOG the detector found inconsistent.

``--dry-run`` is the DEFAULT: it prints the complete, well-formed proposal (unified diffs +
drafted notes + PR body) and **writes nothing** to the repo and opens nothing. ``--execute``
(opt-in, and overridden by ``--dry-run`` for safety) applies the edits, commits them through the
GitHub API, and opens the PR -- wired into ``release-train.yml``'s write-scoped ``propose`` job.
Cross-repo is
**capability-gated** (Phase 4.1, plan S9.2 / S12 step 4.1): with ``--cross-repo`` (the workflow
passes it ONLY when it minted the GitHub App installation token) AND the sibling repo checked out on
disk under ``--ecosystem-root``, a sibling package's proposal branches from that repo's ``main``,
commits through the GitHub API under the App identity, and opens the PR in that repo (the
dup-guard runs per-repo). **The sibling checkout is a read-only INPUT, never a write target** --
it is where ``read_file`` reads the current file bodies the edits are computed against; the branch,
the commit and the PR are all created through ``gh api`` (see ``ProposeSources``). Nothing on disk
is modified, in this repo or any sibling. WITHOUT the capability -- the degraded single-repo ``GITHUB_TOKEN`` path --
a non-juniper-ml package is SKIPPED with the same clear reason as before. The in-repo meta
consumer-pin co-changes (the #657 RK-11 lockstep) apply ONLY to juniper-ml packages; a sibling
proposal never edits the meta from a sibling checkout -- it emits the S13 propagation edge instead.

Every external effect -- ``gh pr list`` (dup-guard), file reads, and (execute-only) file
writes / git / ``gh pr create`` -- is injected through a ``ProposeSources`` seam so
``tests/test_release_train_propose.py`` is fully hermetic (no network, no real gh, no real
pip). ``util/`` is not pre-commit-lint-gated, so that unittest IS the gate (the
``env_floor_drift_check`` precedent, shared with ``detect.py``).

Exit codes: 0 clean run (dry-run preview or execute completed); 2 invocation error (bad
manifest / empty registry / unknown ``--package``). A dry-run is always report-only.

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-14
Status: permanent utility (Phase 2, proposal-PR generation)
"""

from __future__ import annotations

import argparse
import base64
import difflib
import heapq
import json
import os
import re
import tempfile
import subprocess  # nosec B404 - only the gh/git binaries with fixed argv (no shell)
import sys
import tomllib  # Python >= 3.11 (juniper-ml requires >= 3.12); parses the meta extras for pin co-changes
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# Same-directory siblings; resolvable both when run as a script (script dir on sys.path[0])
# and under the tests' ``sys.path.insert(UTIL_DIR)`` idiom (mirrors test_release_train_detect).
import detect  # noqa: E402
import notes_render  # noqa: E402

SourceError = detect.SourceError  # reuse the detector's environmental-failure type

DEFAULT_OWNER = os.environ.get("JUNIPER_RELEASE_TRAIN_OWNER", "pcalnon")

# Only this classification gets a standard-gated proposal PR (plan S5.4 / S5.1).
PROPOSABLE = "UNRELEASED_CHANGES"

# Keep-a-Changelog categories that make a pre-1.0 bump MINOR (escapes the consumer ceiling).
_MINOR_BUMPS = frozenset({"minor", "major"})

# The repo an ``--execute`` run may ALWAYS write, even on the degraded single-repo ``GITHUB_TOKEN``
# path: juniper-ml itself -- the meta-package and its six co-located sub-packages. The Phase-2/3 pilot
# ran the release-train workflow inside the juniper-ml checkout under a juniper-ml-scoped
# ``GITHUB_TOKEN`` (plan S9.2), which can push a branch + open a PR only in juniper-ml. Cross-repo
# writes are now unlocked by CAPABILITY, not hardcoding: with ``--cross-repo`` (the workflow passes it
# only when it minted the GitHub App installation token, Phase 4.1) AND the sibling checked out on disk
# under ``--ecosystem-root``, a sibling package's branch + commit + PR are created in its OWN repo
# through the GitHub API (``make_live_sources`` is repo-aware -- ``_repo_dir(repo)``); the checkout is
# only READ, to source the file bodies the edits apply to. WITHOUT the
# capability a sibling is SKIPPED with the same clear reason as before (``cross_repo_skip_reason``).
# ``--dry-run`` is unaffected -- it previews every repo's proposal and writes nothing.
# Overridable for tests / a future multi-repo identity.
WRITABLE_REPO = os.environ.get("JUNIPER_RELEASE_TRAIN_WRITABLE_REPO", detect.META_REPO)


# ── data model ───────────────────────────────────────────────────────────────


@dataclass
class FileEdit:
    """One file's before/after content in the proposal (rendered as a unified diff)."""

    path: str
    old_text: str
    new_text: str
    is_new: bool = False

    def unified_diff(self) -> str:
        from_lines = self.old_text.splitlines(keepends=True)
        to_lines = self.new_text.splitlines(keepends=True)
        label = "(new file)" if self.is_new else ""
        diff = difflib.unified_diff(from_lines, to_lines, fromfile=f"a/{self.path}", tofile=f"b/{self.path} {label}".rstrip())
        return "".join(diff)


@dataclass
class Proposal:
    """The full content of one release-proposal PR (or a skipped/refused stub)."""

    pypi_name: str
    repo: str
    from_version: "str | None"
    to_version: "str | None"
    bump: str
    branch: "str | None" = None
    commit_message: "str | None" = None
    pr_title: "str | None" = None
    pr_body: "str | None" = None
    edits: list = field(default_factory=list)
    notes_relpath: "str | None" = None
    notes_draft: "str | None" = None
    propagation_edges: list = field(default_factory=list)
    follow_on_prs: list = field(default_factory=list)
    co_change_checklist: list = field(default_factory=list)
    consumer_pin_cochanges: list = field(default_factory=list)
    ship_evidence: list = field(default_factory=list)
    existing_pr: "dict | None" = None
    skipped_reason: "str | None" = None

    @property
    def skipped(self) -> bool:
        return self.skipped_reason is not None

    def to_dict(self) -> dict:
        return {
            "pypi_name": self.pypi_name,
            "repo": self.repo,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "bump": self.bump,
            "branch": self.branch,
            "commit_message": self.commit_message,
            "pr_title": self.pr_title,
            "pr_body": self.pr_body,
            "edits": [{"path": e.path, "is_new": e.is_new, "diff": e.unified_diff()} for e in self.edits],
            "notes_relpath": self.notes_relpath,
            "notes_draft": self.notes_draft,
            "propagation_edges": self.propagation_edges,
            "follow_on_prs": [f.to_dict() for f in self.follow_on_prs],
            "co_change_checklist": self.co_change_checklist,
            "consumer_pin_cochanges": [cc.to_dict() for cc in self.consumer_pin_cochanges],
            "ship_evidence": self.ship_evidence,
            "existing_pr": self.existing_pr,
            "skipped_reason": self.skipped_reason,
        }


# ── injectable I/O seam (all external effects) ───────────────────────────────


@dataclass
class ProposeSources:
    """External effects the generator needs, injected for hermetic testing.

    ``read_file`` / ``list_open_prs`` are the only members the dry-run path uses; the four write
    members are execute-only and may be ``None``. All are **repo-aware** (Phase 4.1): each takes the
    target ``repo`` -- juniper-ml for an in-repo package, the sibling for a cross-repo one -- so a
    sibling proposal never writes into the juniper-ml checkout.

    The write path is **entirely GitHub-API based**, and deliberately so. It previously wrote files
    into a local checkout and made a local ``git commit`` pinned to ``-c commit.gpgsign=false`` (the
    runner has no GPG key and the owner's YubiKey-resident key cannot reach a headless commit). Once
    the 2026-08-12 branch-protection normalization added ``required_signatures`` to all 9 repos, that
    unsigned commit made every proposal PR unmergeable -- an unsigned commit anywhere on the branch
    blocks the merge and squash does not rescue it (cascor#515; the pre-normalization cascor#497
    merged with the identical unsigned commits). A commit authored through GitHub's API under the App
    / ``GITHUB_TOKEN`` identity is **GitHub-signed / Verified**, which is the same fix ``ceremony.py``
    already applies to the exempt-archive commit (ml#707). Building the commit through the API also
    means the write path needs no working tree at all -- checkouts remain read-only inputs.

    - ``resolve_ref_sha(repo, ref)`` -> the tip sha of ``ref`` (the branch point + the optimistic
      ``expectedHeadOid``).
    - ``create_branch(repo, branch, sha)`` -> create ``refs/heads/<branch>`` at ``sha``.
    - ``create_signed_commit(repo, branch, message, additions, expected_head_oid)`` -> one signed
      commit carrying EVERY edit, where ``additions`` is ``[(path, base64_contents), ...]``.
    - ``open_pr(repo, base, head, title, body)`` opens the PR in ``repo``."""

    read_file: Callable[["detect.PackageEntry", str], "str | None"]
    list_open_prs: Callable[[str], list]
    resolve_ref_sha: "Callable[[str, str], str] | None" = None
    create_branch: "Callable[[str, str, str], None] | None" = None
    create_signed_commit: "Callable[[str, str, str, list, str], str] | None" = None
    open_pr: "Callable[..., str] | None" = None


def _gh(args: list, timeout: int = 60) -> "str | None":
    """Run ``gh <args>`` with a fixed argv (no shell). None on a 404-ish 'no result'."""
    try:
        proc = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv, no shell
    except FileNotFoundError as exc:
        raise SourceError("gh CLI not found (install/authenticate GitHub CLI)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"gh timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if "no pull requests" in stderr.lower() or "not found" in stderr.lower():
            return None
        raise SourceError(f"gh failed ({' '.join(args)}): {stderr[:200]}")
    return proc.stdout


# NOTE: there is deliberately no local-``git`` helper here any more. The write path is API-only so a
# proposal commit is always GitHub-signed; a ``git commit`` helper sitting in this module is exactly
# the affordance that would let the unsigned path grow back (see ``ProposeSources``).


def make_live_sources(owner: str, repo_root: Path, ecosystem_root: Path) -> ProposeSources:
    def read_file(entry: "detect.PackageEntry", filename: str) -> "str | None":
        target = detect.base_dir_for(entry, repo_root, ecosystem_root) / filename
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def list_open_prs(repo: str) -> list:
        out = _gh(["pr", "list", "--repo", f"{owner}/{repo}", "--state", "open", "--json", "number,title,headRefName", "--limit", "100"])
        if not out:
            return []
        try:
            return json.loads(out) or []
        except ValueError as exc:
            raise SourceError(f"gh pr list returned non-JSON for {repo}") from exc

    def resolve_ref_sha(repo: str, ref: str) -> str:
        out = _gh(["api", f"repos/{owner}/{repo}/git/ref/heads/{ref}", "--jq", ".object.sha"])
        sha = (out or "").strip()
        if not sha:
            raise SourceError(f"cannot resolve {ref} in {owner}/{repo} (empty sha)")
        return sha

    def create_branch(repo: str, branch: str, sha: str) -> None:
        _gh(["api", f"repos/{owner}/{repo}/git/refs", "-X", "POST", "-f", f"ref=refs/heads/{branch}", "-f", f"sha={sha}"])

    def create_signed_commit(repo: str, branch: str, message: str, additions: list, expected_head_oid: str) -> str:
        # ``gh api graphql -f k=v`` can only pass scalars, and ``fileChanges.additions`` is a LIST --
        # a proposal commits several files at once (pyproject + CHANGELOG + AGENTS.md, sometimes the
        # extras test and the dunder). So the whole CreateCommitOnBranchInput goes through as one
        # ``$input`` object via a JSON request body (``gh api graphql --input <file>``), which keeps
        # every value JSON-escaped rather than interpolated into the document.
        body = {
            "query": _CREATE_COMMIT_ON_BRANCH_MUTATION,
            "variables": {
                "input": {
                    "branch": {"repositoryNameWithOwner": f"{owner}/{repo}", "branchName": branch},
                    "message": {"headline": message},
                    "expectedHeadOid": expected_head_oid,
                    "fileChanges": {"additions": [{"path": path, "contents": contents} for path, contents in additions]},
                }
            },
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
            json.dump(body, fh)
            body_path = fh.name
        try:
            out = _gh(["api", "graphql", "--input", body_path])
        finally:
            try:
                os.unlink(body_path)
            except OSError:
                # Best-effort cleanup of our own tempfile. Deliberately swallowed: the commit either
                # already landed or already failed, and a leftover temp file on an ephemeral runner
                # must never mask that outcome (nor turn a successful release proposal into an error).
                pass
        try:
            data = json.loads(out) if out else {}
        except ValueError as exc:
            raise SourceError(f"createCommitOnBranch returned non-JSON for {repo}") from exc
        if data.get("errors"):
            raise SourceError(f"createCommitOnBranch failed for {repo}: {data['errors']}")
        return (((data.get("data") or {}).get("createCommitOnBranch") or {}).get("commit") or {}).get("oid") or ""

    def open_pr(repo: str, base: str, head: str, title: str, body: str) -> str:
        out = _gh(["pr", "create", "--repo", f"{owner}/{repo}", "--base", base, "--head", head, "--title", title, "--body", body])
        return (out or "").strip()

    return ProposeSources(
        read_file=read_file,
        list_open_prs=list_open_prs,
        resolve_ref_sha=resolve_ref_sha,
        create_branch=create_branch,
        create_signed_commit=create_signed_commit,
        open_pr=open_pr,
    )


# The GraphQL mutation that makes the proposal commit GitHub-signed. Unlike ceremony.py's single-file
# archive variant, this takes the whole input as one ``$input`` object so a proposal can carry every
# file it edits in ONE commit (see ``create_signed_commit`` for why the scalar ``-f`` form cannot).
_CREATE_COMMIT_ON_BRANCH_MUTATION = "mutation($input: CreateCommitOnBranchInput!) { createCommitOnBranch(input: $input) { commit { oid url } } }"


def _execute_signed_pr(repo: str, branch: str, edits: list, commit_message: str, base_branch: str, sources: "ProposeSources") -> None:
    """Branch from ``base_branch`` and land ``edits`` as ONE GitHub-signed commit on ``branch``.

    Shared by both write lanes (the release proposal and the cross-repo consumer-pin follow-on) so
    neither can drift back to an unsigned local commit -- the whole point of the API path."""
    base_sha = sources.resolve_ref_sha(repo, base_branch)
    sources.create_branch(repo, branch, base_sha)
    additions = [(edit.path, base64.b64encode(edit.new_text.encode("utf-8")).decode("ascii")) for edit in edits]
    # expectedHeadOid pins optimistic concurrency to the tip we just branched from: if anything else
    # advanced the branch in between, the mutation fails loudly rather than silently rebasing.
    sources.create_signed_commit(repo, branch, commit_message, additions, base_sha)


# ── version-file editing (static pyproject / dynamic _version.py / AGENTS.md) ─


def dunder_file_rel(entry: "detect.PackageEntry") -> str:
    """Repo-relative path of the package's ``_version.py`` dunder file (whether or not it exists)."""
    return os.path.normpath(os.path.join(entry.path, entry.import_package, "_version.py")).replace(os.sep, "/")


def version_file_rel(entry: "detect.PackageEntry") -> str:
    """Repo-relative path of the file carrying the version to bump."""
    if entry.version_source == "dynamic":
        return dunder_file_rel(entry)
    return entry.pyproject_rel


def set_pyproject_version(text: str, new_version: str) -> tuple:
    """Replace the ``version = "..."`` line inside the ``[project]`` table. -> (new_text, old|None)."""
    lines = text.splitlines(keepends=True)
    section = None
    for i, line in enumerate(lines):
        hm = re.match(r"^\[([^\]]+)\]\s*$", line.strip())
        if hm:
            section = hm.group(1)
            continue
        if section == "project":
            m = re.match(r'^(\s*version\s*=\s*["\'])([^"\']+)(["\'].*)$', line.rstrip("\n"))
            if m:
                old = m.group(2)
                rebuilt = f"{m.group(1)}{new_version}{m.group(3)}" + ("\n" if line.endswith("\n") else "")
                lines[i] = rebuilt
                return "".join(lines), old
    return text, None


def set_dynamic_version(text: str, new_version: str) -> tuple:
    """Replace ``__version__ = "..."`` (first occurrence). -> (new_text, old|None)."""
    m = re.search(r'^(\s*__version__\s*=\s*["\'])([^"\']+)(["\'])', text, re.MULTILINE)
    if not m:
        return text, None
    old = m.group(2)
    new_text = text[: m.start()] + f"{m.group(1)}{new_version}{m.group(3)}" + text[m.end():]
    return new_text, old


def set_agents_version(text: str, new_version: str) -> tuple:
    """Replace the ``**Version**:`` header value in AGENTS.md. -> (new_text, old|None)."""
    m = re.search(r"^(\*\*Version\*\*:\s*)(\S+)(.*)$", text, re.MULTILINE)
    if not m:
        return text, None
    old = m.group(2)
    new_text = text[: m.start()] + f"{m.group(1)}{new_version}{m.group(3)}" + text[m.end():]
    return new_text, old


def set_agents_last_updated(text: str, date: str) -> tuple:
    """Replace the ``**Last Updated**:`` header value in AGENTS.md. -> (new_text, old|None).

    Satisfies the ``agents-md-touch-up.yml`` date check, which fires on any PR touching AGENTS.md and
    requires ``**Last Updated**`` to be a valid non-future date that either equals today or changed in
    the PR. Setting it here means the proposal passes as authored.

    Historically that lane MUTATED instead of verifying: it pushed its own ``[skip ci]`` commit when the
    date was stale. That commit became the PR head, and because it carried ``[skip ci]`` **no required
    context ever reported on it** -- leaving the proposal permanently BLOCKED (the cascor#515 class:
    every required check stuck at "expected"). It also raced the lockfile workflow, whose push was then
    rejected, and its local commit was UNSIGNED (juniper-ml#1099). The lane now verifies, but setting the
    date here remains correct and is what keeps the proposal green. Purely additive: an AGENTS.md with no
    ``**Last Updated**`` line is returned untouched with ``old=None`` (no invented header) -- the same
    honesty contract as ``set_agents_version``."""
    m = re.search(r"^(\*\*Last Updated\*\*:\s*)(\S+)(.*)$", text, re.MULTILINE)
    if not m:
        return text, None
    old = m.group(2)
    if old == date:
        return text, old  # already current -- silent success, no phantom edit
    new_text = text[: m.start()] + f"{m.group(1)}{date}{m.group(3)}" + text[m.end():]
    return new_text, old


# A markdown-table cell that is a STANDALONE version (optionally backtick-wrapped) and nothing else --
# ``0.3.0`` / ``` `0.2.0` ``` / ``0.4.0rc1``. Deliberately NOT a substring match: an extras-reference
# cell (``` `juniper-doc-tools>=0.1.0,<0.2.0` ```) or a prose cell that merely mentions a version is not
# a version cell, so this anchor is what keeps the heuristic off every other table in an AGENTS.md.
_TABLE_VERSION_CELL = re.compile(r"^`?(\d+\.\d+\.\d+[0-9A-Za-z.\-+]*)`?$")


def _row_names_package(row: str, pypi_name: str) -> bool:
    """True when a markdown-table row names ``pypi_name`` as a backtick-delimited token.

    Byte-identical name anchoring to the consumer gate this co-change exists to satisfy
    (juniper-recurrence ``scripts/check_version_drift.py`` ``_agents_table_version``): the needle is
    ``` `<name>` ``` with BOTH backticks, so the ``juniper-recurrence`` row never matches the
    ``juniper-recurrence-model`` row, and a directory cell (``` `juniper-recurrence/` ```) is not a
    package mention."""
    return "`" + pypi_name + "`" in row


def _rewrite_row_version_cell(line: str, old_version: str, new_version: str) -> str:
    """Replace the standalone version token in a table row's version cell, preserving the row's pipe
    count, padding, and any backticks (only the cell whose whole trimmed content IS ``old_version``)."""
    body = line.rstrip("\r\n")
    trailing = line[len(body):]
    parts = body.split("|")
    for idx, part in enumerate(parts):
        m = _TABLE_VERSION_CELL.match(part.strip())
        if m is not None and m.group(1) == old_version:
            parts[idx] = part.replace(old_version, new_version, 1)
    return "|".join(parts) + trailing


def set_agents_table_version(text: str, pypi_name: str, from_version: "str | None", to_version: str) -> tuple:
    """Bump the per-package version cell of every AGENTS.md markdown-table row naming ``pypi_name``
    (ml#851). -> ``(new_text, status)`` with status in ``absent`` / ``current`` / ``edited`` / ``unexpected``.

    The generic form of the ml#706 / worker#140 header precedent: some repos ALSO carry a per-package
    version TABLE (juniper-recurrence's ``AGENTS.md:22-24`` sub-package table) that a repo-local
    ``version-drift`` hook pins against ``_version.py``, so a proposal that moves only the header ships
    red in that repo (the recurrence#92 / #93 failures). Unlike the header -- which tracks the repo's
    PRIMARY package -- the table has one row PER package, so a sub-package hosted in a sibling repo
    (``juniper-recurrence-model``) must bump its own row while never touching the host header.

    Structured like ``apply_pin_edits_agents_table`` rather than a text sweep: a candidate is a
    ``|``-row that names the package in backticks AND carries exactly one standalone version cell.
    Honesty rules mirror step 5a -- a row already at ``to_version`` is silent success (``current``);
    no candidate row at all is NOT an edit and NOT a checklist item (``absent`` -- most repos have no
    such table); and anything unexpected (a cell that is neither the from- nor the to-version, or an
    ambiguous row with two version cells) is left byte-untouched and surfaced ``unexpected`` for the
    operator, never guessed at. A mixed set across rows is likewise ``unexpected`` (no partial edit)."""
    lines = text.splitlines(keepends=True)
    candidates: list = []  # (line index, version cell value)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|") or not _row_names_package(stripped, pypi_name):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        found = [_TABLE_VERSION_CELL.match(c) for c in cells]
        versions = [m.group(1) for m in found if m is not None]
        if not versions:
            continue  # a descriptive row carrying no version cell -- not a version table
        if len(versions) > 1:
            return text, "unexpected"  # ambiguous: which cell is THE version? never guess
        candidates.append((i, versions[0]))
    if not candidates:
        return text, "absent"
    values = {v for _, v in candidates}
    if values == {to_version}:
        return text, "current"
    if from_version is None or values != {from_version}:
        return text, "unexpected"
    for i, value in candidates:
        lines[i] = _rewrite_row_version_cell(lines[i], value, to_version)
    return "".join(lines), "edited"


# ── in-repo meta-package consumer-pin co-changes (plan S5.4; closes the #657 RK-11 gap) ─
#
# When the train proposes a version bump for an IN-REPO package (the meta-package or one of its six
# co-located sub-packages), the meta-package's own root ``pyproject.toml`` may pin that package behind
# a ``<next-minor`` ceiling in one or more ``[project.optional-dependencies]`` extras. A pre-1.0 MINOR
# bump that escapes such a ceiling must move the pin -- AND the two artifacts kept in lockstep with it:
# the exact-string membership contract in ``tests/test_pyproject_extras.py`` and the ``AGENTS.md``
# "Dependency extras reference" table row -- IN THE SAME proposal PR, or the RK-11 lockstep gate
# (``tests/test_service_core_drift.py`` and its per-package siblings) fails and the proposal ships red
# (the ml#657 incident, fixed in-branch by commit 1860dbb). This is the IN-REPO case only; a
# cross-repo consumer's pin is a separate standard-gated follow-on PR (``propagation_edges``, D6)
# because it cannot ride a PR in a different repo. The ``juniper-ml[extra,...]`` recursive self-ref in
# ``[all]`` names extras, not a versioned package, so it is never a pin co-change target.

_VERSION_OPERATORS = "<>=!~"
_EXTRAS_MARKER_RE = re.compile(r"^\[[^\]]*\]")


@dataclass
class ConsumerPinCoChange:
    """One meta-extras ceiling raise: ``[extra]`` pinned ``old_req``, now needs ``new_req``."""

    extra: str
    old_req: str
    new_req: str

    def to_dict(self) -> dict:
        return {"extra": self.extra, "old_req": self.old_req, "new_req": self.new_req}


def requirement_names_package(req: str, pypi_name: str) -> bool:
    """True when requirement string ``req`` is a *versioned* pin of ``pypi_name`` -- the name, an
    OPTIONAL PEP 508 ``[extras]`` marker, then a version operator. So both ``juniper-service-core>=0.2.0,<0.5.0``
    (the meta-extras form) and ``juniper-model-core[crossval]>=0.2.0,<0.4.0`` (a consumer's
    extras-carrying runtime dep, Phase 4.2) match. The ``juniper-ml[...]`` recursive extras ref (``[``
    then NO operator) and a longer package name (``juniper-cascor-worker`` probed for ``juniper-cascor``)
    both return False."""
    req = req.strip()
    if not req.startswith(pypi_name):
        return False
    rest = req[len(pypi_name):]
    marker = _EXTRAS_MARKER_RE.match(rest)
    if marker:
        rest = rest[marker.end():]
    rest = rest.lstrip()
    return bool(rest) and rest[0] in _VERSION_OPERATORS


def next_minor_ceiling(version: str) -> str:
    """The pre-1.0 next-minor ceiling for a newly released ``version`` (plan S6): ``<{major}.{minor+1}.0``.
    ``0.5.0`` -> ``<0.6.0``; ``0.5.3`` -> ``<0.6.0`` (the whole fleet is 0.x, so major stays 0; the
    formula generalizes to post-1.0 should a package ever cross 1.0)."""
    head = re.split(r"[^0-9.]", version, maxsplit=1)[0]
    parts = [int(p) for p in head.split(".") if p.isdigit()]
    while len(parts) < 2:
        parts.append(0)
    return f"<{parts[0]}.{parts[1] + 1}.0"


def raise_requirement_ceiling(req: str, new_version: str) -> "str | None":
    """If ``new_version`` escapes ``req``'s upper bound, return ``req`` with ONLY the ceiling raised to
    the next-minor of ``new_version`` (the floor and every other specifier preserved byte-for-byte);
    else ``None`` (within range, or no upper bound at all -> no pin change). Floors are never touched."""
    m = re.search(r"(<=?)\s*([0-9][0-9A-Za-z.\-+]*)", req)
    if not m:
        return None  # no upper bound: a higher version still satisfies '>=floor'
    op, ceiling = m.group(1), m.group(2)
    cmp = detect.version_cmp(new_version, ceiling)
    escapes = cmp >= 0 if op == "<" else cmp > 0
    if not escapes:
        return None
    return req[: m.start()] + next_minor_ceiling(new_version) + req[m.end():]


def compute_consumer_pin_cochanges(pyproject_text: str, pypi_name: str, new_version: str) -> list:
    """Every meta-extras requirement that names ``pypi_name`` and whose ceiling ``new_version`` escapes,
    as a list of ``ConsumerPinCoChange`` (one per (extra, requirement) -- a package listed in two extras,
    e.g. ``juniper-doc-tools`` in ``[doc-tools]`` and ``[tools]``, yields one entry each). An empty list
    means the new version is within every existing ceiling (no pin change needed)."""
    try:
        data = tomllib.loads(pyproject_text)
    except (tomllib.TOMLDecodeError, ValueError):
        return []
    extras = (data.get("project") or {}).get("optional-dependencies") or {}
    cochanges: list = []
    for extra_name, reqs in extras.items():
        for req in reqs or []:
            if not isinstance(req, str) or not requirement_names_package(req, pypi_name):
                continue
            new_req = raise_requirement_ceiling(req, new_version)
            if new_req is not None and new_req != req:
                cochanges.append(ConsumerPinCoChange(extra=extra_name, old_req=req, new_req=new_req))
    return cochanges


def apply_pin_pairs_exact(text: str, pairs: list) -> str:
    """Byte-surgical exact-string replacement of each ``(old_req, new_req)`` pair (order-preserving
    de-dup), so only the pinned requirement moves and nothing else in the file does. Shared by the
    meta consumer-pin co-change (``apply_pin_edits_exact``) and the Phase-4.2 D6 follow-on pin edit --
    both edit requirement strings that are the authoritative source the change was parsed from, so
    ``old_req`` matches exactly."""
    seen: set = set()
    for old_req, new_req in pairs:
        key = (old_req, new_req)
        if key in seen:
            continue
        seen.add(key)
        text = text.replace(old_req, new_req)
    return text


def apply_pin_edits_exact(text: str, cochanges: list) -> str:
    """(meta path) exact-string ceiling raise for each ``ConsumerPinCoChange`` -- for the root
    ``pyproject.toml`` and the ``tests/test_pyproject_extras.py`` membership sets. Delegates to
    ``apply_pin_pairs_exact``."""
    return apply_pin_pairs_exact(text, [(cc.old_req, cc.new_req) for cc in cochanges])


_AGENTS_EXTRAS_HEADING = re.compile(r"^#{2,4}\s+Dependency extras reference\s*$", re.IGNORECASE)

# The four documentation surfaces ``tests/test_pyproject_extras.py`` asserts against ``pyproject.toml``.
# THREE share the inline row shape -- one cell holding a comma-joined list of backticked
# ``name>=x,<y`` requirements -- and differ only in their heading anchor, which is why they take the
# same editor re-anchored. ``docs/REFERENCE.md`` is the odd one out and needs its own (see
# :func:`apply_pin_edits_reference_table`). Each heading was verified unique in its file: README's
# ``### Extras`` does not also match REFERENCE's ``## Extras Reference``, and vice versa.
_INLINE_EXTRAS_TABLES = (
    ("AGENTS.md", _AGENTS_EXTRAS_HEADING),
    ("README.md", re.compile(r"^#{2,4}\s+Extras\s*$", re.IGNORECASE)),
    ("docs/QUICK_START.md", re.compile(r"^#{2,4}\s+What Each Extra Installs\s*$", re.IGNORECASE)),
)
_REFERENCE_EXTRAS_REL = "docs/REFERENCE.md"
_REFERENCE_EXTRAS_HEADING = re.compile(r"^#{2,4}\s+Available Extras\s*$", re.IGNORECASE)
# A ``| ... | `pkg` | `>=x,<y` |`` version cell: backticked and OPERATOR-led, which is what separates
# it from the package-name cell beside it and from the ``all`` row's bare ``--``.
_REFERENCE_SPEC_CELL = re.compile(r"^`[<>=!~][^`]*`$")


def apply_pin_edits_reference_table(text: str, pypi_name: str, new_req: str) -> str:
    """True up ``docs/REFERENCE.md``'s "Available Extras" table, whose shape defeats the inline editor.

    That table is SPLIT-COLUMN: the distribution sits in one cell (``\\`juniper-doc-tools\\```, bare)
    and its specifier in another (``\\`>=0.1.0,<0.2.0\\```). A substitution on the combined
    ``name>=x,<y`` string therefore matches nothing here and reports success -- which is exactly how
    the first hand-repair of the service-core 0.6.0 cut looked complete and still failed one arm.

    Rows are matched on the backtick-DELIMITED package name, so ``\\`juniper-recurrence\\``` does not
    also claim the ``\\`juniper-recurrence-model\\``` row beside it, and the extra-name column
    (``\\`tools\\```, ``\\`doc-tools\\```) can never match a distribution. Every row naming the package
    is updated -- ``juniper-doc-tools`` appears under both ``[tools]`` and ``[doc-tools]``. The cell's
    original width is preserved where the new specifier fits, so the table stays aligned and the diff
    stays one cell wide."""
    if not new_req.startswith(pypi_name):
        return text
    spec = new_req[len(pypi_name) :]
    if not spec:
        return text
    name_re = re.compile("`" + re.escape(pypi_name) + "`")
    out: list = []
    in_section = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if _REFERENCE_EXTRAS_HEADING.match(stripped):
            in_section = True
            out.append(line)
            continue
        if in_section and stripped.startswith("#"):
            in_section = False  # the next heading closes the table's section
        if in_section and stripped.startswith("|") and name_re.search(line):
            line = _replace_reference_spec_cell(line, spec)
        out.append(line)
    return "".join(out)


def _replace_reference_spec_cell(line: str, spec: str) -> str:
    """Swap the operator-led backticked cell in one split-column row, preserving the column width."""
    newline = "\n" if line.endswith("\n") else ""
    cells = line[: len(line) - len(newline)].split("|")
    for idx, cell in enumerate(cells):
        if not _REFERENCE_SPEC_CELL.match(cell.strip()):
            continue
        replacement = " `" + spec + "`"
        cells[idx] = replacement.ljust(len(cell)) if len(replacement) <= len(cell) else replacement + " "
        break
    return "|".join(cells) + newline


def apply_pin_edits_agents_table(text: str, pypi_name: str, new_req: str, heading: "re.Pattern" = _AGENTS_EXTRAS_HEADING) -> str:
    """True up ONE inline extras table: within THAT table only, replace
    the affected package's backtick-wrapped, digit-led versioned requirement (whatever ceiling it
    currently shows, in every row it appears -- ``juniper-doc-tools`` sits in both ``[tools]`` and
    ``[doc-tools]``) with the authoritative ``new_req``.

    Scoped to the table because a bare ``\\`juniper-doc-tools\\``` prose mention, a
    ``\\`juniper-observability>=0.2.0\\``` minimum-pin note, and a ``\\`juniper-ci-tools>=0.1.0,<0.2.0\\``
    CI-pin description all live ELSEWHERE in AGENTS.md and must not move. Name-anchored (not
    exact-old-string) so a table row that has drifted from ``pyproject.toml`` -- the ml#657 case where
    the service-core row was stale at ``<0.4.0`` -- is corrected to the new pin too (1860dbb fixed
    exactly this by hand). The operator+digit anchor also skips a bare name or a ``>=X,<Y`` placeholder.

    ``heading`` re-anchors the same editor onto the other two inline surfaces (see
    ``_INLINE_EXTRAS_TABLES``): README's ``### Extras`` and QUICK_START's ``### What Each Extra
    Installs`` carry the identical row shape under different titles. It keeps the AGENTS.md default
    because every existing caller and test passes three arguments. ``docs/REFERENCE.md`` is NOT in
    this set -- it has no inline table at all, only the split-column one
    :func:`apply_pin_edits_reference_table` handles."""
    pin_re = re.compile("`" + re.escape(pypi_name) + r"[<>=!~]+[0-9][^`]*`")
    replacement = "`" + new_req + "`"
    out: list = []
    in_section = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if heading.match(stripped):
            in_section = True
            out.append(line)
            continue
        if in_section and stripped.startswith("#"):
            in_section = False  # the next heading closes the extras-reference section
        if in_section and stripped.startswith("|"):
            line = pin_re.sub(replacement, line)
        out.append(line)
    return "".join(out)


# ── CHANGELOG [Unreleased] -> [version] move ─────────────────────────────────


def _strip_blank_edges(lines: list) -> list:
    out = list(lines)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def move_unreleased(changelog_text: str, version: str, date: str) -> tuple:
    """Move ``[Unreleased]`` bullets into a new ``[<version>] - <date>`` section, leaving a
    fresh empty ``[Unreleased]`` (Keep-a-Changelog, plan S5.4). -> (new_text, reason|None);
    a non-None reason means REFUSE (no move): no Unreleased heading, or an empty section."""
    if not changelog_text:
        return None, "CHANGELOG is empty or unreadable"
    lines = changelog_text.splitlines()
    unrel = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s*\[?unreleased\]?", line.strip(), re.IGNORECASE):
            unrel = i
            break
    if unrel is None:
        return None, "no '## [Unreleased]' heading in CHANGELOG"
    end = len(lines)
    for j in range(unrel + 1, len(lines)):
        if re.match(r"^##\s", lines[j]) and not re.match(r"^###", lines[j]):
            end = j
            break
    body = _strip_blank_edges(lines[unrel + 1:end])
    if not body:
        return None, "[Unreleased] section has no content to move"
    rebuilt: list = []
    rebuilt.extend(lines[: unrel + 1])  # up to and including '## [Unreleased]'
    rebuilt.append("")  # fresh empty Unreleased
    rebuilt.append(f"## [{version}] - {date}")
    rebuilt.append("")
    rebuilt.extend(body)
    if end < len(lines):
        rebuilt.append("")
        rebuilt.extend(lines[end:])
    new_text = "\n".join(rebuilt)
    if changelog_text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, None


# ── dependency-aware ordering (D6, plan S13) ─────────────────────────────────
#
# Within one train run, packages are processed UPSTREAM-FIRST so a consumer's proposal never bumps a
# floor to a version the upstream has not at least released, and a consumer's ceiling-bump follow-on is
# listed AFTER the upstream release proposal that triggers it (plan S13). The order is a deterministic
# topological sort of the registry ``depends_on`` DAG with a lexicographic (``pypi_name``) tie-break,
# so it is a single stable permutation independent of the registry's file order -- the S13 "shared libs
# -> sub-libs -> apps -> meta" tier listing is documentation; the registry ``depends_on`` is the truth.


class CycleError(Exception):
    """Raised when the registry ``depends_on`` graph is not a DAG (plan S13 requires a topological
    order). The message names one concrete cycle as an ``a -> b -> ... -> a`` chain."""


def topological_order(entries: list) -> list:
    """Deterministic **upstream-first** order of the registry ``depends_on`` DAG (plan S13/D6): every
    package appears AFTER every registry package it depends on. Kahn's algorithm with a min-heap on
    ``pypi_name`` as the tie-break among the ready set, so the result is stable and independent of the
    registry's file order (NO hardcoded tiers). Only edges to REGISTERED packages constrain the order
    (a ``depends_on`` naming a non-registry package is ignored). Raises :class:`CycleError` (naming the
    cycle) when the graph is not acyclic."""
    names = [e.pypi_name for e in entries]
    nameset = set(names)
    deps = {e.pypi_name: [d for d in dict.fromkeys(e.depends_on or []) if d in nameset] for e in entries}
    indeg = dict.fromkeys(names, 0)
    dependents: dict = {n: [] for n in names}  # NOT dict.fromkeys: that would share ONE list across all keys
    for n in names:
        for d in deps[n]:
            indeg[n] += 1
            dependents[d].append(n)
    ready = [n for n in names if indeg[n] == 0]
    heapq.heapify(ready)
    order: list = []
    while ready:
        n = heapq.heappop(ready)
        order.append(n)
        for m in sorted(dependents[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                heapq.heappush(ready, m)
    if len(order) != len(names):
        stuck = sorted(n for n in names if indeg[n] > 0)
        raise CycleError(f"registry depends_on is not acyclic (plan S13 requires a DAG): {' -> '.join(_one_cycle(deps, stuck))}")
    return order


def _one_cycle(deps: dict, stuck: list) -> list:
    """One concrete cycle (closed ``a -> ... -> a``) among the ``stuck`` nodes, for the error message."""
    stuck_set = set(stuck)
    onpath: list = []
    onset: set = set()
    seen: set = set()

    def walk(u: str) -> "list | None":
        onpath.append(u)
        onset.add(u)
        for v in deps.get(u, []):
            if v not in stuck_set:
                continue
            if v in onset:
                return onpath[onpath.index(v):] + [v]
            if v not in seen:
                got = walk(v)
                if got:
                    return got
        onpath.pop()
        onset.discard(u)
        seen.add(u)
        return None

    for s in stuck:
        if s not in seen:
            got = walk(s)
            if got:
                return got
    return list(stuck)


# ── dup-guard + propagation ──────────────────────────────────────────────────


def release_branch(pypi_name: str, version: str) -> str:
    return f"release/{pypi_name}-v{version}"


def find_existing_release_pr(open_prs: list, pypi_name: str) -> "dict | None":
    """An open PR whose head branch is this package's release branch (any version) -> dup.

    The ``-v`` delimiter keeps ``juniper-cascor`` from matching ``juniper-cascor-model``."""
    prefix = f"release/{pypi_name}-v"
    for pr in open_prs or []:
        head = (pr or {}).get("headRefName", "")
        if head.startswith(prefix):
            return pr
    return None


def reverse_dependents(entries: list, pypi_name: str) -> list:
    """Registered packages that declare ``pypi_name`` in their ``depends_on`` (consumers)."""
    return sorted(e.pypi_name for e in entries if pypi_name in (e.depends_on or []))


def propagation_edges(entries: list, entry: "detect.PackageEntry", bump: str) -> list:
    """For a pre-1.0 MINOR (or MAJOR) bump, each CROSS-REPO consumer needs a ceiling-bump follow-on PR
    (plan S6/S13). PATCH stays within ``<next-minor`` ceilings -> no propagation.

    When the bumped package is IN-REPO, the meta-package's own consumer pin is co-changed in the SAME
    proposal PR (see ``compute_consumer_pin_cochanges``; closes the ml#657 RK-11 gap), so the meta is
    NOT also listed here as a separate follow-on edge -- that would contradict the folded-in edit. A
    sibling-repo bump still lists the meta as a follow-on (its pin cannot ride a cross-repo PR)."""
    if bump not in _MINOR_BUMPS:
        return []
    by_name = {e.pypi_name: e for e in entries}
    edges: list = []
    fold_meta = entry.repo == detect.META_REPO
    for consumer in reverse_dependents(entries, entry.pypi_name):
        if fold_meta and consumer == notes_render.META_PACKAGE:
            continue  # co-changed in this PR, not a separate follow-on edge
        cons_entry = by_name.get(consumer)
        edges.append(
            {
                "consumer": consumer,
                "repo": cons_entry.repo if cons_entry else None,
                "reason": f"pre-1.0 {bump.upper()} bump of {entry.pypi_name} escapes its '<next-minor' ceiling pin",
                "action": "standard-gated ceiling-bump follow-on PR (D6); never folded into this PR or the exempt path",
            }
        )
    return edges


# ── consumer ceiling-bump follow-on PRs (Phase 4.2, D6, plan S13) ────────────
#
# When a proposed upstream bump is a pre-1.0 MINOR (or MAJOR), each consumer that pins the upstream
# behind a ``<next-minor`` ceiling the NEW version escapes needs a SEPARATE, standard-gated
# ceiling-bump follow-on PR IN THAT CONSUMER'S REPO (plan S13/D6) -- NEVER folded into the upstream
# proposal or the exempt notes-archive path (the 2026-07-06 ci-tools incident class; rec#85 is the
# hand-made shape). The pin state is read from the consumer's REAL pyproject on disk (both floor-only
# and ``<ceiling`` forms; only an escaped ceiling needs action). The meta (juniper-ml) is the sole
# exception: its pin rides #661's folded co-change when the upstream is in-repo and stays MANUAL
# (Q-META) otherwise -- it never gets a follow-on PR. Cross-repo capability (Phase 4.1) gates the
# open: an escaped sibling consumer is a follow-on when this run is ``--cross-repo`` with the sibling
# checked out, and an ``escaped -> skipped(<reason>)`` edge otherwise (the degraded single-repo path).

# consumer_pin_state values (the per-run propagation picture surfaced in the step summary, plan S13):
PIN_WITHIN_RANGE = "within_range"
PIN_FLOOR_ONLY = "floor_only (no ceiling)"
PIN_ESCAPED_FOLLOWON = "escaped -> follow-on"
PIN_NO_VERSIONED = "no_versioned_pin (registry depends_on, but no versioned requirement in the consumer pyproject)"


@dataclass
class FollowOnPR:
    """One standard-gated ceiling-bump follow-on PR in a CONSUMER repo (plan S13/D6). Content is built
    whenever the pin escapes and the consumer pyproject is readable; ``consumer_pin_state`` /
    ``skipped_reason`` record whether THIS run would open it (in-repo or cross-repo-capable) or skip it
    (degraded cross-repo / dup-guard)."""

    consumer: str
    repo: str
    upstream: str
    upstream_version: str
    pin_file: str
    pin_changes: list  # list[(location, old_req, new_req)] -- location is "dependencies" or "[extra]"
    branch: str
    consumer_pin_state: str
    edits: list = field(default_factory=list)
    commit_message: "str | None" = None
    pr_title: "str | None" = None
    pr_body: "str | None" = None
    existing_pr: "dict | None" = None
    skipped_reason: "str | None" = None

    @property
    def skipped(self) -> bool:
        return self.skipped_reason is not None

    def to_dict(self) -> dict:
        return {
            "consumer": self.consumer,
            "repo": self.repo,
            "upstream": self.upstream,
            "upstream_version": self.upstream_version,
            "pin_file": self.pin_file,
            "pin_changes": [{"location": loc, "old_req": old, "new_req": new} for loc, old, new in self.pin_changes],
            "branch": self.branch,
            "consumer_pin_state": self.consumer_pin_state,
            "edits": [{"path": e.path, "is_new": e.is_new, "diff": e.unified_diff()} for e in self.edits],
            "commit_message": self.commit_message,
            "pr_title": self.pr_title,
            "pr_body": self.pr_body,
            "existing_pr": self.existing_pr,
            "skipped_reason": self.skipped_reason,
        }


def consumer_pin_requirements(pyproject_text: str, upstream: str) -> list:
    """Every ``(location, req)`` in a consumer pyproject that versions ``upstream`` -- across
    ``[project.dependencies]`` (location ``"dependencies"``) and each ``[project.optional-dependencies]``
    extra (location ``"[extra]"``). Tolerates the PEP 508 ``[extras]`` marker via
    ``requirement_names_package`` (real consumer deps use e.g. ``juniper-model-core[crossval]>=...``)."""
    try:
        data = tomllib.loads(pyproject_text)
    except (tomllib.TOMLDecodeError, ValueError):
        return []
    project = data.get("project") or {}
    out: list = []
    for req in project.get("dependencies") or []:
        if isinstance(req, str) and requirement_names_package(req, upstream):
            out.append(("dependencies", req))
    for extra, reqs in (project.get("optional-dependencies") or {}).items():
        for req in reqs or []:
            if isinstance(req, str) and requirement_names_package(req, upstream):
                out.append((f"[{extra}]", req))
    return out


def escaped_pin_edits(pin_reqs: list, new_version: str) -> list:
    """The subset of ``[(location, req)]`` whose ceiling ``new_version`` escapes, as
    ``[(location, old_req, new_req)]`` with ONLY the ceiling raised to the next-minor (floors and every
    other specifier preserved byte-for-byte)."""
    edits: list = []
    for location, req in pin_reqs:
        new_req = raise_requirement_ceiling(req, new_version)
        if new_req is not None and new_req != req:
            edits.append((location, req, new_req))
    return edits


def _pin_reqs_have_ceiling(pin_reqs: list) -> bool:
    return any(re.search(r"<=?\s*[0-9]", req) for _loc, req in pin_reqs)


def follow_on_branch(upstream: str, new_version: str) -> str:
    """``deps/<upstream>-ceiling-<new-ceiling>`` where ``<new-ceiling>`` is the raised ceiling version
    (e.g. ``juniper-model-core`` at ``0.4.0`` -> ``deps/juniper-model-core-ceiling-0.5.0``)."""
    return f"deps/{upstream}-ceiling-{next_minor_ceiling(new_version).lstrip('<')}"


def find_existing_follow_on_pr(open_prs: list, upstream: str) -> "dict | None":
    """An open PR whose head branch is this upstream's ceiling-bump follow-on branch (any ceiling) -> a
    dup. The ``-ceiling-`` delimiter keeps ``juniper-cascor`` from matching ``juniper-cascor-model``."""
    prefix = f"deps/{upstream}-ceiling-"
    for pr in open_prs or []:
        if (pr or {}).get("headRefName", "").startswith(prefix):
            return pr
    return None


def _follow_on_body(fo: "FollowOnPR", date: str, trigger_branch: "str | None", trigger_title: "str | None") -> str:
    lines: list = []
    lines.append(f"## Consumer ceiling bump: `{fo.consumer}` for `{fo.upstream}` v{fo.upstream_version}")
    lines.append("")
    lines.append("Generated by the Juniper release-train (`util/release_train/propose.py`) as a **D6 propagation follow-on** (plan `notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md` S13).")
    lines.append("")
    lines.append(f"The upstream **`{fo.upstream}`** is being released at **v{fo.upstream_version}** (a pre-1.0 MINOR bump). Under the fleet's `>=floor,<next-minor` pinning policy (plan S6) each `0.x` is a compatibility boundary, so this new version **escapes** `{fo.consumer}`'s current `<next-minor` ceiling. This PR raises ONLY that ceiling; the floor and every other specifier are preserved byte-for-byte.")
    lines.append("")
    if trigger_branch:
        lines.append(f"Triggering release proposal: `{trigger_title or trigger_branch}` (branch `{trigger_branch}`).")
        lines.append("")
    lines.append("### Pin change(s)")
    for loc, old, new in fo.pin_changes:
        lines.append(f"- `{loc}`: `{old}` -> `{new}`")
    lines.append("")
    lines.append("### Why this is a SEPARATE, standard-gated PR (plan S13/D6)")
    lines.append("- Upstream-first ordering is **soft** for the deploy but **hard** for propagation: the ceiling bump can only land once the upstream is actually released.")
    lines.append("- It is **standard-gated** -- the owner reviews and merges it. It is **never** auto-merged and **never** folded into the exempt notes-archive path (that path is add-only notes files; a pin edit there would break the R5/R7 exemption).")
    lines.append("- This is the exact failure class of the **2026-07-06 ci-tools incident** (six consumer pins `<0.5.0`->`<0.7.0` lagged a 0.6.0 release); rec#85 is the hand-made model of this PR shape.")
    lines.append("")
    lines.append("### Files changed")
    for e in fo.edits:
        lines.append(f"- `{e.path}`")
    lines.append("")
    return "\n".join(lines)


def build_follow_on(cons_entry: "detect.PackageEntry", upstream_entry: "detect.PackageEntry", to_version: str, escaped_edits: list, pyproject_text: str, date: str, trigger_branch: "str | None", trigger_title: "str | None") -> "FollowOnPR":
    """Assemble the full follow-on PR content (pin edit + branch + title/commit/body) for one escaped
    (consumer, upstream) pair. Disposition (open vs skip) is decided by the caller."""
    pairs = [(old, new) for _loc, old, new in escaped_edits]
    new_pyproject = apply_pin_pairs_exact(pyproject_text, pairs)
    new_ceiling = next_minor_ceiling(to_version).lstrip("<")
    fo = FollowOnPR(
        consumer=cons_entry.pypi_name,
        repo=cons_entry.repo,
        upstream=upstream_entry.pypi_name,
        upstream_version=to_version,
        pin_file=cons_entry.pyproject_rel,
        pin_changes=list(escaped_edits),
        branch=follow_on_branch(upstream_entry.pypi_name, to_version),
        consumer_pin_state=PIN_ESCAPED_FOLLOWON,
    )
    if new_pyproject != pyproject_text:
        fo.edits.append(FileEdit(path=cons_entry.pyproject_rel, old_text=pyproject_text, new_text=new_pyproject))
    fo.commit_message = f"chore(deps): raise {upstream_entry.pypi_name} ceiling to <{new_ceiling} for its v{to_version} release"
    fo.pr_title = f"deps: raise {upstream_entry.pypi_name} ceiling to <{new_ceiling} ({cons_entry.pypi_name})"
    fo.pr_body = _follow_on_body(fo, date, trigger_branch, trigger_title)
    return fo


def enrich_edges_with_pin_state(edges: list, upstream_entry: "detect.PackageEntry", to_version: str, entries: list, sources: ProposeSources, *, cross_repo: bool, ecosystem_root: Path, trigger_branch: "str | None", trigger_title: "str | None", date: str) -> list:
    """Annotate each propagation edge with a ``consumer_pin_state`` read from the consumer's REAL
    pyproject (plan S13 propagation picture) and, for an escaped CROSS-REPO (non-meta) consumer, build
    the standard-gated ceiling-bump ``FollowOnPR``. Mutates ``edges`` in place (adds ``consumer_pin_state``
    + ``follow_on_branch``); returns the list of built ``FollowOnPR`` objects. The meta never gets a
    follow-on (Q-META). Content is computed regardless of disposition so a dry-run preview always shows
    the edit; ``cross_repo`` + on-disk checkout decide open (``escaped -> follow-on``) vs skip
    (``escaped -> skipped(<reason>)``)."""
    by_name = {e.pypi_name: e for e in entries}
    follow_ons: list = []
    for edge in edges:
        consumer = edge["consumer"]
        edge["follow_on_branch"] = None
        cons_entry = by_name.get(consumer)
        if cons_entry is None:
            edge["consumer_pin_state"] = "unknown (consumer not in registry)"
            continue
        text = sources.read_file(cons_entry, cons_entry.pyproject_rel)
        if text is None:
            edge["consumer_pin_state"] = f"unknown (consumer pyproject unreadable at {cons_entry.pyproject_rel})"
            continue
        pin_reqs = consumer_pin_requirements(text, upstream_entry.pypi_name)
        if not pin_reqs:
            edge["consumer_pin_state"] = PIN_NO_VERSIONED
            continue
        escaped = escaped_pin_edits(pin_reqs, to_version)
        if not escaped:
            edge["consumer_pin_state"] = PIN_WITHIN_RANGE if _pin_reqs_have_ceiling(pin_reqs) else PIN_FLOOR_ONLY
            continue
        if consumer == notes_render.META_PACKAGE:
            # Escaped, but the meta never gets a follow-on: for an in-repo upstream it is folded (#661)
            # and not even in this edge list; reaching here means a SIBLING upstream, so the meta pin is
            # a manual Q-META item (bumped when the meta is next released).
            edge["consumer_pin_state"] = "escaped -> deferred (juniper-ml meta stays manual per Q-META; no follow-on PR)"
            continue
        fo = build_follow_on(cons_entry, upstream_entry, to_version, escaped, text, date, trigger_branch, trigger_title)
        reason = cross_repo_skip_reason(cons_entry.repo, cross_repo_capable=cross_repo, ecosystem_root=ecosystem_root)
        if reason is not None:
            fo.skipped_reason = reason
            fo.consumer_pin_state = f"escaped -> skipped({reason})"
        else:
            existing = find_existing_follow_on_pr(sources.list_open_prs(cons_entry.repo), upstream_entry.pypi_name)
            if existing is not None:
                fo.existing_pr = existing
                fo.skipped_reason = f"dup-guard: open ceiling-bump PR already exists (#{existing.get('number')} {existing.get('headRefName')})"
                fo.consumer_pin_state = f"escaped -> skipped({fo.skipped_reason})"
            else:
                fo.consumer_pin_state = PIN_ESCAPED_FOLLOWON
        edge["consumer_pin_state"] = fo.consumer_pin_state
        edge["follow_on_branch"] = fo.branch
        follow_ons.append(fo)
    return follow_ons


def execute_follow_on(fo: "FollowOnPR", sources: ProposeSources, base_branch: str = "main", *, cross_repo: bool = False, ecosystem_root: "Path | None" = None) -> str:
    """Apply one follow-on to its consumer repo's checkout and open the PR there (Phase 4.2 execute).
    Mirrors ``execute_proposal``: in-repo and sibling alike branch from ``base_branch``, resolved
    through the API against the target repo's own ref -- there is no in-repo/sibling ``origin/main``
    split any more (that was the removed local-git path).
    The capability guard is belt-and-suspenders (the caller already skips a skipped/degraded follow-on)."""
    if sources.resolve_ref_sha is None or sources.create_branch is None or sources.create_signed_commit is None or sources.open_pr is None:
        raise SourceError("execute mode needs resolve_ref_sha/create_branch/create_signed_commit/open_pr seam members")
    if fo.skipped or not fo.branch or not fo.edits:
        return ""
    if cross_repo_skip_reason(fo.repo, cross_repo_capable=cross_repo, ecosystem_root=ecosystem_root) is not None:
        return ""
    _execute_signed_pr(fo.repo, fo.branch, fo.edits, fo.commit_message or f"deps: raise {fo.upstream} ceiling", base_branch, sources)
    return sources.open_pr(fo.repo, base_branch, fo.branch, fo.pr_title or "", fo.pr_body or "")


# ── proposal construction ────────────────────────────────────────────────────


def _changelog_rel(entry: "detect.PackageEntry") -> str:
    return os.path.normpath(os.path.join(entry.path, "CHANGELOG.md")).replace(os.sep, "/")


def _co_change_checklist(entry: "detect.PackageEntry", bump: str, edges: list, agents_edited: bool, cochanges: list, dunder_rel: "str | None" = None, dunder_edited: bool = False, *, agents_surface: bool = True, agents_table_status: str = "absent") -> list:
    items: list = []
    if dunder_rel is not None:
        state = "included in this PR" if dunder_edited else "REQUIRED (``__version__`` assignment not found -- edit manually)"
        items.append(f"`{dunder_rel}` `__version__` lockstep bump ({state}); a static-version package's dunder must move with `pyproject.toml` or the shipped wheel's `__version__` lies (the ci-tools 0.7.0 / service-core 0.5.0 stale-dunder class, ml#701); guarded by tests/test_release_train_registry.py (VersionDunderLockstepTest).")
    # agents_surface=False: header already at to_version (partial heal / re-entry) — silent success;
    # do NOT false-flag REQUIRED for an AGENTS.md that already satisfies the portable drift lint.
    if agents_surface and entry.pypi_name == notes_render.META_PACKAGE:
        state = "included in this PR" if agents_edited else "REQUIRED (edit could not be computed -- do it manually)"
        items.append(f"AGENTS.md **Version** header bump ({state}); guarded by tests/test_agents_md_version_drift.py.")
    elif agents_surface and entry.pypi_name == entry.repo:
        state = "included in this PR" if agents_edited else "REQUIRED (header absent or not at the expected from-version -- verify and edit manually)"
        items.append(f"Sibling AGENTS.md **Version** header bump ({state}); the target repo's CI runs the portable version-drift lint against its primary package version (the worker#140 pilot failure class).")
    # ml#851: the table variant of the same class. ``absent`` (no such table -- most repos) and
    # ``current`` (row already at to_version) are silent successes, exactly like the header rules above.
    if agents_table_status == "edited":
        items.append(f"AGENTS.md per-package version-table row bump for `{entry.pypi_name}` (included in this PR); a repo-local version-drift hook pins that row against the package version, so a header-only proposal ships red there (ml#851; the juniper-recurrence#92 / #93 class).")
    elif agents_table_status == "unexpected":
        items.append(f"AGENTS.md per-package version-table row bump for `{entry.pypi_name}` (REQUIRED -- a row names the package but its version cell is not at the expected from-version, or the row is ambiguous; verify and edit manually, the train never guesses at a cell); a repo-local version-drift hook pins that row against the package version (ml#851).")
    if cochanges:
        extras_touched = ", ".join(sorted({f"[{cc.extra}]" for cc in cochanges}))
        items.append(f"In-repo meta consumer pin (included in this PR): raised the {extras_touched} ceiling for {entry.pypi_name} to {cochanges[0].new_req} -- root pyproject.toml + tests/test_pyproject_extras.py membership + all four documented extras tables (AGENTS.md, README.md, docs/QUICK_START.md, docs/REFERENCE.md), moved together in THIS PR (closes the ml#657 RK-11 gap and the ml#1458 docs-lockstep gap; guarded by tests/test_pyproject_extras.py + the per-package RK-11 drift gate).")
        items.append(f"If `{entry.pypi_name}` is ALSO pinned in `.github/workflows/` by a drift lint (juniper-doc-tools / juniper-ci-tools carry one via test_*_drift.py::test_juniper_ml_own_workflows_pin_current_version, which does NOT skip in per-PR mode) or in `.pre-commit-config.yaml`, those pins are NOT edited by the train -- move them by hand in THIS PR or the bump ships red.")
    items.append("If this bump raises a runtime dependency floor, regenerate the lockfile (requirements.lock) in this PR (memory: 'regen on floor bump or gate fails').")
    items.append("Version+pin+lint atomicity: if a consumer pins this package behind a drift-lint contract (tests/test_*_drift.py), move the pin + the lint bound in the same change set (model-core precedent).")
    if edges:
        items.append(f"Consumer ceiling propagation: {len(edges)} follow-on ceiling-bump PR(s) needed (see propagation edges) -- standard-gated, opened separately, NEVER folded into this PR or the exempt notes-archive path (2026-07-06 ci-tools incident class).")
    return items


def _pr_body(prop: Proposal, date: str) -> str:
    lines: list = []
    lines.append(f"## Release proposal: `{prop.pypi_name}` v{prop.from_version} -> v{prop.to_version}")
    lines.append("")
    lines.append("Generated by the Juniper release-train (`util/release_train/propose.py`) from the release manifest.")
    lines.append(f"Classification `UNRELEASED_CHANGES`; proposed bump **{prop.bump}** (plan S6). This PR is **standard-gated**: the owner reviews and merges it (plan S7). It is never auto-merged and touches neither TestPyPI nor PyPI.")
    lines.append("")
    lines.append("### Version bump")
    lines.append(f"- `{version_change_summary(prop)}` (via `{version_file_rel_for(prop)}`)")
    dunder_rel = dunder_cochange_rel(prop)
    if dunder_rel is not None:
        lines.append(f"- Lockstep `__version__` dunder co-change: `{dunder_rel}` (the static-with-dunder stale-dunder class, ml#701)")
    lines.append("")
    lines.append("### CHANGELOG")
    lines.append(f"- Move `[Unreleased]` -> `[{prop.to_version}] - {date}`, leaving a fresh empty `[Unreleased]` (Keep-a-Changelog).")
    lines.append("")
    lines.append("### Drafted release notes (NOT archived here)")
    lines.append(f"Archival to the central `{prop.notes_relpath}` is the later **exempt** ceremony step (plan S10.2); this PR only drafts the notes for review.")
    lines.append("")
    lines.append("<details><summary>Drafted release notes</summary>")
    lines.append("")
    lines.append("```markdown")
    lines.append((prop.notes_draft or "").rstrip("\n"))
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")
    if prop.ship_evidence:
        lines.append("### Ship evidence (from the detector)")
        for item in prop.ship_evidence:
            lines.append(f"- `{item.get('file', '?')}` -- {item.get('reason', '')}")
        lines.append("")
    if prop.repo == detect.META_REPO:
        lines.append("### Consumer-pin co-changes (in-repo meta extras, plan S5.4)")
        if prop.consumer_pin_cochanges:
            lines.append("This escaping bump exceeds the meta-package's own `[project.optional-dependencies]` ceiling, so the pin + its two lockstep artifacts (`tests/test_pyproject_extras.py` membership and the `AGENTS.md` extras table) are moved IN THIS PR (closes the ml#657 RK-11 gap):")
            lines.append("")
            lines.append("> **Reviewer action required -- this generator has a known gap.** `tests/test_pyproject_extras.py` also asserts the extras tables in `README.md`, `docs/QUICK_START.md` and `docs/REFERENCE.md` against `pyproject.toml`, and none of the three is in the edit set above, so this PR will fail 3 arms until they are co-updated by hand. `docs/REFERENCE.md` needs **two** edits -- the inline table, and the separate \"Extras Reference\" table whose distribution and specifier sit in different columns, which a combined-string substitution misses. Found on the service-core 0.6.0 cut (ml#1458).")
            for cc in prop.consumer_pin_cochanges:
                lines.append(f"- `[{cc.extra}]`: `{cc.old_req}` -> `{cc.new_req}`")
        else:
            lines.append("- none needed -- new version within existing ceilings.")
        lines.append("")
    lines.append("### Propagation edges (D6)")
    if prop.propagation_edges:
        for edge in prop.propagation_edges:
            lines.append(f"- `{edge['consumer']}` ({edge.get('repo')}): **{edge.get('consumer_pin_state', '?')}** -- {edge['action']}")
    else:
        lines.append("- None -- PATCH within consumer `<next-minor` ceilings (no propagation).")
    lines.append("")
    if prop.follow_on_prs:
        lines.append("### Ceiling-bump follow-on PRs (D6, separate & standard-gated)")
        lines.append("Each is a **separate** owner-reviewed PR in the consumer's repo -- never folded into this proposal or the exempt notes-archive path.")
        for fo in prop.follow_on_prs:
            disp = f"SKIP -- {fo.skipped_reason}" if fo.skipped else "will open"
            lines.append(f"- `{fo.consumer}` ({fo.repo}) branch `{fo.branch}` [{disp}]")
            for loc, old, new in fo.pin_changes:
                lines.append(f"  - `{loc}`: `{old}` -> `{new}`")
        lines.append("")
    lines.append("### Co-change checklist (plan S5.4)")
    for item in prop.co_change_checklist:
        lines.append(f"- [ ] {item}")
    lines.append("")
    lines.append("### Files changed in this proposal")
    for edit in prop.edits:
        lines.append(f"- `{edit.path}`{' (new file)' if edit.is_new else ''}")
    lines.append("")
    return "\n".join(lines)


def version_change_summary(prop: Proposal) -> str:
    return f"{prop.pypi_name}: {prop.from_version} -> {prop.to_version}"


def version_file_rel_for(prop: Proposal) -> str:
    """The version file path from the proposal's first edit (always the version bump)."""
    return prop.edits[0].path if prop.edits else "(version file)"


def dunder_cochange_rel(prop: Proposal) -> "str | None":
    """The static-with-dunder ``_version.py`` lockstep co-change path (ml#701), or None.

    The version bump is always ``edits[0]``; for a static package any LATER ``_version.py`` edit is
    the dunder co-change (a dynamic package's ``_version.py`` IS ``edits[0]``, never later)."""
    for edit in prop.edits[1:]:
        if edit.path.endswith("/_version.py"):
            return edit.path
    return None


def build_proposal(entry: "detect.PackageEntry", pkg: dict, sources: ProposeSources, repo_root: Path, ecosystem_root: Path, entries: list, date: str, *, cross_repo: bool = False) -> Proposal:
    """Build the full proposal for one UNRELEASED_CHANGES manifest package (or a refusal stub).

    ``cross_repo`` (Phase 4.2) records whether THIS run can open cross-repo follow-on PRs, so an escaped
    sibling consumer's edge is labelled ``escaped -> follow-on`` (capable) vs ``escaped -> skipped``
    (degraded); the follow-on CONTENT is built either way for the dry-run preview."""
    from_version = pkg.get("released_version") or pkg.get("declared_version")
    bump = pkg.get("proposed_bump") or "none"
    to_version = pkg.get("proposed_version") or detect.bump_version(from_version or "0.0.0", bump)
    prop = Proposal(pypi_name=entry.pypi_name, repo=entry.repo, from_version=from_version, to_version=to_version, bump=bump, ship_evidence=list(pkg.get("ship_evidence") or []))

    # 1. dup-guard (cheapest; concurrent-session hazard, plan S8/S5.4).
    existing = find_existing_release_pr(sources.list_open_prs(entry.repo), entry.pypi_name)
    if existing is not None:
        prop.existing_pr = existing
        prop.skipped_reason = f"dup-guard: open release PR already exists (#{existing.get('number')} {existing.get('headRefName')})"
        return prop

    # 2. changelog-conflict refusal (the detector flagged an inconsistency, plan S4.2 step 6).
    conflict = pkg.get("changelog_conflict")
    if conflict:
        prop.skipped_reason = f"changelog conflict -- refuse to auto-author: {conflict}"
        return prop

    if not to_version or bump == "none":
        prop.skipped_reason = f"no proposable version (bump={bump}, proposed_version={pkg.get('proposed_version')!r})"
        return prop

    # 3. version bump edit.
    vfile = version_file_rel(entry)
    vtext = sources.read_file(entry, vfile)
    if vtext is None:
        prop.skipped_reason = f"could not read the version file {vfile}"
        return prop
    if entry.version_source == "dynamic":
        new_vtext, old = set_dynamic_version(vtext, to_version)
    else:
        new_vtext, old = set_pyproject_version(vtext, to_version)
    if old is None:
        prop.skipped_reason = f"could not locate the version assignment in {vfile}"
        return prop
    prop.edits.append(FileEdit(path=vfile, old_text=vtext, new_text=new_vtext))

    # 3a. static-with-dunder ``_version.py`` lockstep co-change (ml#701). All five in-repo static
    # packages ALSO carry a ``_version.py`` ``__version__`` dunder that the pyproject-only bump used
    # to silently falsify -- the ci-tools 0.7.0 / service-core 0.5.0 stale-dunder incidents (the
    # shipped wheel's metadata is right while its ``__version__`` lies). Auto-detected by file
    # presence (no registry field that could itself drift); a present-but-unparseable dunder is left
    # alone and surfaced REQUIRED-manual via the co-change checklist (the AGENTS.md header precedent).
    dunder_rel = None
    dunder_edited = False
    if entry.version_source != "dynamic":
        candidate = dunder_file_rel(entry)
        dtext = sources.read_file(entry, candidate)
        if dtext is not None:
            new_dtext, dold = set_dynamic_version(dtext, to_version)
            if dold is None:
                # present-but-unparseable → REQUIRED-manual (never guess at the assignment)
                dunder_rel = candidate
            elif new_dtext != dtext:
                dunder_rel = candidate
                prop.edits.append(FileEdit(path=dunder_rel, old_text=dtext, new_text=new_dtext))
                dunder_edited = True
            # else: already at to_version (partial heal / re-entry) — silent success; do NOT flag
            # REQUIRED-manual for a dunder that is already correct.

    # 4. CHANGELOG move (+ source the notes bullets from the same text).
    clog_rel = _changelog_rel(entry)
    clog_text = sources.read_file(entry, clog_rel)
    sections = notes_render.parse_unreleased(clog_text or "")
    if clog_text is not None:
        moved, reason = move_unreleased(clog_text, to_version, date)
        if reason is not None:
            # Drop any version/dunder edits staged above so a refusal stub matches the
            # dup-guard / bump=none shape (edits=[], skipped_reason set). execute_proposal
            # already guards on ``skipped``, but a half-staged pyproject bump here trained
            # operators to treat leftover edits as harmless — clear them.
            prop.edits.clear()
            prop.skipped_reason = f"CHANGELOG move refused: {reason}"
            return prop
        prop.edits.append(FileEdit(path=clog_rel, old_text=clog_text, new_text=moved))
    else:
        prop.edits.clear()
        prop.skipped_reason = f"could not read {clog_rel}"
        return prop

    # 5. AGENTS.md co-changes. AGENTS.md is read ONCE here and EVERY transformation below (the
    # **Version** header, the ml#851 per-package version table, and the step-5b extras-pin table)
    # composes onto the same text, so a proposal carries at most ONE AGENTS.md FileEdit: the executor
    # writes each edit's full ``new_text`` in order, so two edits on one path would silently drop the
    # first. The single append lives after step 5b (below), once every composer has run.
    #
    # 5. (header) meta-package AGENTS.md **Version** co-change (plan S5.4).
    agents_edited = False
    agents_surface = False  # True => checklist item (included or REQUIRED); False => already-at-target silent
    agents_table_status = "absent"
    atext = sources.read_file(entry, "AGENTS.md")
    agents_new = atext
    if entry.pypi_name == notes_render.META_PACKAGE:
        if atext is None:
            agents_surface = True  # absent → REQUIRED-manual
        else:
            candidate, aold = set_agents_version(agents_new, to_version)
            if aold is None:
                agents_surface = True  # no **Version** line → REQUIRED-manual
            elif candidate != agents_new:
                agents_new = candidate
                agents_edited = True
                agents_surface = True
            # else: already at to_version (partial heal / re-entry) — silent success
    # 5a. sibling-repo AGENTS.md **Version** co-change. Every sibling repo's AGENTS.md header tracks
    # that repo's PRIMARY package version, and the portable version-drift lint runs in their CI --
    # the worker#140 pilot failure class: the proposal bumped pyproject.toml and the lint correctly
    # failed the PR on the stale header. Primary = pypi_name == repo name (registry-derived), so a
    # sub-package hosted in a sibling repo (e.g. juniper-cascor-model in juniper-cascor) never touches
    # the host repo's header. Only a header whose current value equals the from-version is rewritten;
    # anything unexpected is left alone and surfaced via the co-change checklist (agents_edited=False).
    # Already-at-to_version is silent success (same class as the ml#701 dunder re-entry fix).
    elif entry.pypi_name == entry.repo:
        if atext is None:
            agents_surface = True  # absent → REQUIRED-manual
        else:
            candidate, aold = set_agents_version(agents_new, to_version)
            if aold == from_version and candidate != agents_new:
                agents_new = candidate
                agents_edited = True
                agents_surface = True
            elif aold == to_version:
                pass  # already correct — silent success; do NOT false-REQUIRED
            else:
                agents_surface = True  # unexpected / missing header → REQUIRED-manual

    # 5a. per-package AGENTS.md version-TABLE row co-change (ml#851 -- the worker#140 class, table
    # variant). Some repos carry a per-package version table pinned by a repo-local ``version-drift``
    # hook (juniper-recurrence's AGENTS.md:22-24 vs scripts/check_version_drift.py), so a proposal that
    # moved only the header shipped red there (recurrence#92 / #93, healed by hand). Unlike the header,
    # the table has a row PER package -- so this runs for EVERY package, including a sub-package hosted
    # in a sibling repo, which still must not touch that repo's primary-tracking header. Repos without
    # such a table are ``absent``: no edit, no checklist noise.
    if atext is not None:
        candidate, agents_table_status = set_agents_table_version(agents_new, entry.pypi_name, from_version, to_version)
        if agents_table_status == "edited":
            agents_new = candidate

    # 5b. in-repo meta-package consumer-pin co-changes (plan S5.4; closes the ml#657 RK-11 gap).
    # For an in-repo bump whose new version escapes a meta ``[extras]`` ``<next-minor`` ceiling, move
    # the pin AND its two lockstep artifacts (the test_pyproject_extras membership + the AGENTS.md
    # extras table) in THIS PR. Empty co-change list => the new version is within every ceiling (the
    # proposal body then states "none needed"). Cross-repo consumers stay as propagation edges (D6).
    if entry.repo == detect.META_REPO:
        root_pyproject = sources.read_file(entry, "pyproject.toml")
        if root_pyproject is not None:
            cochanges = compute_consumer_pin_cochanges(root_pyproject, entry.pypi_name, to_version)
            prop.consumer_pin_cochanges = cochanges
            if cochanges:
                new_root = apply_pin_edits_exact(root_pyproject, cochanges)
                if new_root != root_pyproject:
                    prop.edits.append(FileEdit(path="pyproject.toml", old_text=root_pyproject, new_text=new_root))
                test_rel = "tests/test_pyproject_extras.py"
                test_text = sources.read_file(entry, test_rel)
                if test_text is not None:
                    new_test = apply_pin_edits_exact(test_text, cochanges)
                    if new_test != test_text:
                        prop.edits.append(FileEdit(path=test_rel, old_text=test_text, new_text=new_test))
                if atext is not None:
                    # composes onto the step-5/5a text (see the step-5 note): one AGENTS.md FileEdit only.
                    agents_new = apply_pin_edits_agents_table(agents_new, entry.pypi_name, cochanges[0].new_req)
                # 5b-ii. The REST of the documented extras surface. ``ExtrasDocsLockstepTest`` asserts
                # README.md and docs/QUICK_START.md with the SAME inline parser it uses on AGENTS.md,
                # and docs/REFERENCE.md with a separate split-column one -- so all three fail the
                # moment the pin escapes and only AGENTS.md moves (the ml#1458 service-core 0.6.0
                # class: 3 arms red on all three Python versions, repaired by hand). AGENTS.md is
                # excluded here because step 5b already composed it into the single 5d FileEdit.
                for doc_rel, doc_heading in _INLINE_EXTRAS_TABLES:
                    if doc_rel == "AGENTS.md":
                        continue
                    doc_text = sources.read_file(entry, doc_rel)
                    if doc_text is None:
                        continue
                    doc_new = apply_pin_edits_agents_table(doc_text, entry.pypi_name, cochanges[0].new_req, doc_heading)
                    if doc_new != doc_text:
                        prop.edits.append(FileEdit(path=doc_rel, old_text=doc_text, new_text=doc_new))
                ref_text = sources.read_file(entry, _REFERENCE_EXTRAS_REL)
                if ref_text is not None:
                    ref_new = apply_pin_edits_reference_table(ref_text, entry.pypi_name, cochanges[0].new_req)
                    if ref_new != ref_text:
                        prop.edits.append(FileEdit(path=_REFERENCE_EXTRAS_REL, old_text=ref_text, new_text=ref_new))

    # 5c. **Last Updated** true-up. Runs ONLY when a previous composer actually changed AGENTS.md --
    # the date-check workflow is path-filtered to AGENTS.md, so a proposal that does not touch the file
    # cannot trigger it and must not gratuitously bump its date. Composes onto the same text as
    # 5/5a/5b (see the step-5 note), so it never adds a second FileEdit.
    if atext is not None and agents_new != atext:
        agents_new, _ = set_agents_last_updated(agents_new, date)

    # 5d. the SINGLE AGENTS.md edit, carrying whichever of the four composers actually changed text.
    if atext is not None and agents_new != atext:
        prop.edits.append(FileEdit(path="AGENTS.md", old_text=atext, new_text=agents_new))

    # 6. drafted release notes (template-driven; NOT archived here, plan S10.1/S10.2).
    prop.notes_relpath = notes_render.archive_relpath(entry.pypi_name, to_version)
    _nb = f"https://github.com/{DEFAULT_OWNER}/{entry.repo}/blob/main"
    prop.notes_draft = notes_render.render_notes(entry.pypi_name, to_version, bump=bump, release_date=date, sections=sections, repo_root=repo_root, link_base=_nb, changelog_url=f"{_nb}/{_changelog_rel(entry)}")

    # 7. propagation edges (annotated with the consumer pin state) + follow-on PRs + co-change checklist.
    prop.propagation_edges = propagation_edges(entries, entry, bump)
    prop.follow_on_prs = enrich_edges_with_pin_state(
        prop.propagation_edges,
        entry,
        to_version,
        entries,
        sources,
        cross_repo=cross_repo,
        ecosystem_root=ecosystem_root,
        trigger_branch=release_branch(entry.pypi_name, to_version),
        trigger_title=f"release: {entry.pypi_name} v{to_version} (proposal)",
        date=date,
    )
    prop.co_change_checklist = _co_change_checklist(entry, bump, prop.propagation_edges, agents_edited, prop.consumer_pin_cochanges, dunder_rel=dunder_rel, dunder_edited=dunder_edited, agents_surface=agents_surface, agents_table_status=agents_table_status)

    # 8. branch / commit / PR metadata.
    prop.branch = release_branch(entry.pypi_name, to_version)
    prop.commit_message = f"chore(release): {entry.pypi_name} v{to_version} -- version bump + CHANGELOG move"
    prop.pr_title = f"release: {entry.pypi_name} v{to_version} (proposal)"
    prop.pr_body = _pr_body(prop, date)
    return prop


# ── output ───────────────────────────────────────────────────────────────────


def _print_proposal(prop: Proposal) -> None:
    print("=" * 78)
    if prop.skipped:
        print(f"SKIP  {prop.pypi_name}  ({prop.repo})")
        print(f"      reason: {prop.skipped_reason}")
        print()
        return
    print(f"PROPOSE  {prop.pypi_name}  {prop.from_version} -> {prop.to_version}  [{prop.bump}]  ({prop.repo})")
    print()
    print(f"  branch:  {prop.branch}")
    print(f"  commit:  {prop.commit_message}")
    print(f"  PR title: {prop.pr_title}")
    print()
    for edit in prop.edits:
        print(f"  --- file edit: {edit.path}{' (new file)' if edit.is_new else ''} ---")
        diff = edit.unified_diff()
        for line in diff.splitlines():
            print(f"  {line}")
        print()
    print("  --- drafted release notes (NOT archived; eventual home:", prop.notes_relpath, ") ---")
    for line in (prop.notes_draft or "").splitlines():
        print(f"  {line}")
    print()
    if prop.repo == detect.META_REPO:
        print("  --- consumer-pin co-changes (in-repo meta extras; folded into THIS PR) ---")
        if prop.consumer_pin_cochanges:
            for cc in prop.consumer_pin_cochanges:
                print(f"  - [{cc.extra}] {cc.old_req} -> {cc.new_req}")
        else:
            print("  - none needed (new version within existing ceilings)")
        print()
    if prop.propagation_edges:
        print("  --- propagation edges (D6): consumer pin state per reverse-dependency ---")
        for edge in prop.propagation_edges:
            print(f"  - {edge['consumer']} ({edge.get('repo')}): {edge.get('consumer_pin_state', '?')}")
        print()
    if prop.follow_on_prs:
        print("  --- ceiling-bump follow-on PRs (D6, separate standard-gated PRs in the consumer repos) ---")
        for fo in prop.follow_on_prs:
            disp = f"SKIP ({fo.skipped_reason})" if fo.skipped else "will open"
            print(f"  - {fo.consumer} ({fo.repo})  branch: {fo.branch}  [{disp}]")
            for loc, old, new in fo.pin_changes:
                print(f"      {loc}: {old} -> {new}")
            for edit in fo.edits:
                for line in edit.unified_diff().splitlines():
                    print(f"      {line}")
        print()
    print("  --- PR body ---")
    for line in (prop.pr_body or "").splitlines():
        print(f"  {line}")
    print()


def print_proposals(proposals: list, dry_run: bool) -> None:
    mode = "DRY-RUN (report-only; writes nothing, opens nothing)" if dry_run else "EXECUTE"
    print(f"Juniper PyPI release-train -- proposal generation [{mode}]")
    print()
    if not proposals:
        print("  no UNRELEASED_CHANGES packages in the manifest -- nothing to propose.")
        return
    for prop in proposals:
        _print_proposal(prop)
    proposed = sum(1 for p in proposals if not p.skipped)
    skipped = sum(1 for p in proposals if p.skipped)
    print("=" * 78)
    print(f"  {len(proposals)} package(s): {proposed} proposal(s), {skipped} skipped/refused.")


def build_output(proposals: list, dry_run: bool) -> dict:
    return {
        "schema": "juniper-release-train/proposals/v1",
        "generated_by": "util/release_train/propose.py",
        "dry_run": dry_run,
        "summary": {"total": len(proposals), "proposed": sum(1 for p in proposals if not p.skipped), "skipped": sum(1 for p in proposals if p.skipped)},
        "proposals": [p.to_dict() for p in proposals],
    }


# ── execute path (Phase 2.2; wired into release-train.yml's write-scoped propose job) ─


def cross_repo_skip_reason(repo: str, *, cross_repo_capable: bool = False, ecosystem_root: "Path | None" = None, writable_repo: str = WRITABLE_REPO) -> "str | None":
    """Reason to skip a proposal under ``--execute``, or ``None`` when the run may open the PR (Phase 4.1).

    Capability-based, not hardcoded:
      * ``repo == writable_repo`` (juniper-ml) -> ``None``: the in-repo package is always writable, even
        on the degraded single-repo ``GITHUB_TOKEN`` path.
      * a sibling repo AND NOT ``cross_repo_capable`` -> the SAME clear reason as before (the degraded
        path has no cross-repo write identity; the single-repo ``GITHUB_TOKEN`` cannot open a PR there).
      * a sibling repo, ``cross_repo_capable``, but its checkout is absent under ``ecosystem_root`` ->
        a distinct reason. The checkout is required as a READ source -- ``read_file`` sources the
        current file bodies from it -- not as a write target; nothing is written to it.
      * a sibling repo, capable, checkout present -> ``None``: the GitHub App identity (plan S9.2) may
        branch from that repo's ``main``, commit through the API and open the PR there (S12 step 4.1).

    **Staleness is the live hazard here, not writes.** ``create_signed_commit`` sends WHOLE file
    bodies, and those bodies come from the local checkout while the branch point comes from the
    repo's live ``main``. A sibling checkout behind its remote therefore commits stale content over
    whatever landed in between -- silently, because ``expectedHeadOid`` guards the freshly created
    branch (which cannot have moved) and says nothing about the checkout's age. Fetch siblings before
    an ``--execute --cross-repo`` run."""
    if repo == writable_repo:
        return None
    if not cross_repo_capable:
        return f"cross-repo: package lives in '{repo}', not the writable repo '{writable_repo}' -- the release-train workflow's single-repo GITHUB_TOKEN cannot open a PR there (Phase 2/3 in-repo pilot; Phase 4's GitHub App identity lifts this, plan S9.2 / S12 step 4.1)"
    checkout = (ecosystem_root / repo) if ecosystem_root is not None else None
    if checkout is None or not checkout.is_dir():
        return f"cross-repo: '{repo}' is release-worthy and this run is cross-repo-capable, but its checkout is not present at {checkout} -- clone it (full history + tags) under --ecosystem-root so propose.py can READ the current file bodies from it; the branch, commit and PR are created through the GitHub API, not in the checkout (plan S12 step 4.1)"
    return None


def execute_proposal(prop: Proposal, sources: ProposeSources, base_branch: str = "main", *, cross_repo: bool = False, ecosystem_root: "Path | None" = None) -> str:
    """Land one proposal as a GitHub-signed commit in its OWN repo and open the PR there.

    Guarded so it can only run under an explicit ``--execute`` (never the default), and only for a
    package the capability check clears (in-repo always; a sibling only when ``cross_repo`` AND its
    checkout is on disk). Both the branch point and the PR ``--base`` are ``base_branch`` (``main``),
    resolved through the API -- so unlike the old local-git path there is no in-repo/sibling
    ``origin/main`` split, and no working tree is touched at all (see ``ProposeSources``)."""
    if sources.resolve_ref_sha is None or sources.create_branch is None or sources.create_signed_commit is None or sources.open_pr is None:
        raise SourceError("execute mode needs resolve_ref_sha/create_branch/create_signed_commit/open_pr seam members")
    if prop.skipped or not prop.branch or not prop.edits:
        return ""
    # Cross-repo guard (belt-and-suspenders -- main() already skips before calling): never write a
    # sibling's edits into the wrong repo / open a doomed PR without the capability (plan S9.2).
    if cross_repo_skip_reason(prop.repo, cross_repo_capable=cross_repo, ecosystem_root=ecosystem_root) is not None:
        return ""
    _execute_signed_pr(prop.repo, prop.branch, prop.edits, prop.commit_message or f"release: {prop.pypi_name}", base_branch, sources)
    return sources.open_pr(prop.repo, base_branch, prop.branch, prop.pr_title or "", prop.pr_body or "")


# ── CLI ──────────────────────────────────────────────────────────────────────


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="release_train/propose.py", description="Generate standard-gated release-proposal PR content from the release manifest (plan S5.4). Dry-run by default.")
    default_repo_root = Path(__file__).resolve().parents[2]
    p.add_argument("--manifest", required=True, help="path to the release-manifest JSON emitted by detect.py (--json)")
    p.add_argument("--package", action="append", metavar="PYPI_NAME", help="restrict to these pypi_name(s) (repeatable)")
    p.add_argument("--repo-root", default=str(default_repo_root), help="juniper-ml checkout root (version-file reads + notes template)")
    p.add_argument("--ecosystem-root", default=None, help="parent dir holding sibling repos (default: --repo-root's parent)")
    p.add_argument("--owner", default=DEFAULT_OWNER, help=f"GitHub owner for the dup-guard (default: {DEFAULT_OWNER})")
    p.add_argument("--registry", default=None, help="path to registry.yaml (default: alongside detect.py)")
    p.add_argument("--release-date", default=None, help="release date for the CHANGELOG/notes (default: today UTC; use for deterministic output)")
    p.add_argument("--dry-run", action="store_true", help="(default behaviour) print the proposal; write nothing, open nothing. Overrides --execute.")
    p.add_argument("--execute", action="store_true", help="opt-in: apply edits + open PRs. --dry-run overrides it.")
    p.add_argument("--cross-repo", action="store_true", help="Phase 4.1: this run has a cross-repo write identity (the GitHub App installation token). With it AND a sibling checkout under --ecosystem-root, a sibling package's PR is opened in ITS repo; without it, sibling packages are skipped (the degraded single-repo GITHUB_TOKEN path). No effect in --dry-run.")
    p.add_argument("--json", action="store_true", help="emit the proposals as JSON instead of the human report")
    return p.parse_args(argv)


def main(argv: "list[str] | None" = None, sources: "ProposeSources | None" = None) -> int:
    args = parse_args(argv)
    dry_run = args.dry_run or not args.execute  # dry-run is the default and always wins for safety
    repo_root = Path(args.repo_root).resolve()
    ecosystem_root = Path(args.ecosystem_root).resolve() if args.ecosystem_root else repo_root.parent
    date = args.release_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

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
    by_name = {e.pypi_name: e for e in entries}

    wanted = set(args.package) if args.package else None
    if wanted:
        unknown = wanted - set(by_name)
        if unknown:
            print(f"ERROR: unknown --package {sorted(unknown)}", file=sys.stderr)
            return 2

    # Dependency-aware ordering (Phase 4.2, plan S13/D6): a deterministic upstream-first topological sort
    # of the registry depends_on DAG (a cyclic graph is a hard invocation error naming the cycle). The
    # eligible packages are processed in this order, so a consumer is never proposed ahead of its upstream
    # and a ceiling-bump follow-on trails the proposal that triggers it.
    try:
        topo = topological_order(entries)
    except CycleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    topo_index = {name: i for i, name in enumerate(topo)}

    if sources is None:
        sources = make_live_sources(args.owner, repo_root, ecosystem_root)

    proposable = [pkg for pkg in manifest_pkgs if pkg.get("classification") == PROPOSABLE and (not wanted or pkg.get("pypi_name") in wanted)]
    proposable.sort(key=lambda p: (topo_index.get(p.get("pypi_name"), len(topo)), p.get("pypi_name") or ""))

    proposals: list = []
    try:
        for pkg in proposable:
            name = pkg.get("pypi_name")
            entry = by_name.get(name)
            if entry is None:
                proposals.append(Proposal(pypi_name=name or "?", repo=pkg.get("repo") or "?", from_version=pkg.get("released_version"), to_version=None, bump=pkg.get("proposed_bump") or "none", skipped_reason="package not in registry.yaml"))
                continue
            proposals.append(build_proposal(entry, pkg, sources, repo_root, ecosystem_root, entries, date, cross_repo=args.cross_repo))
    except SourceError as exc:
        print(f"ERROR: source failure during proposal generation: {exc}", file=sys.stderr)
        return 2

    if not dry_run:
        opened: list = []
        skipped: list = []
        try:
            for prop in proposals:
                # Cross-repo capability takes precedence over any build-time skip so the reported reason
                # is the authoritative one (a sibling-repo package can also fail its file reads when the
                # siblings are not checked out; the cross-repo reason is the real cause). Phase 4.1: a
                # sibling is writable only when this run is --cross-repo AND its checkout is on disk.
                reason = cross_repo_skip_reason(prop.repo, cross_repo_capable=args.cross_repo, ecosystem_root=ecosystem_root)
                if reason is not None:
                    skipped.append(prop)
                    print(f"skip: {prop.pypi_name} ({prop.repo}) -- {reason}")
                    continue
                if prop.skipped:
                    skipped.append(prop)
                    print(f"skip: {prop.pypi_name} ({prop.repo}) -- {prop.skipped_reason}")
                    continue
                url = execute_proposal(prop, sources, "main", cross_repo=args.cross_repo, ecosystem_root=ecosystem_root)
                if url:
                    opened.append(prop)
                    print(f"opened: {prop.pypi_name} ({prop.repo}) -- {url}")
                else:
                    skipped.append(prop)
                    print(f"skip: {prop.pypi_name} ({prop.repo}) -- execute opened no PR (empty URL)")
            # D6 ceiling-bump follow-ons trail their upstream proposals (upstream-first, plan S13). Each
            # was already dispositioned at build time with THIS run's capability; open the openable ones
            # (execute_follow_on re-checks the capability belt-and-suspenders). Skipped/degraded ones are
            # reported, never opened.
            fo_opened: list = []
            fo_skipped: list = []
            for prop in proposals:
                for fo in prop.follow_on_prs:
                    if fo.skipped:
                        fo_skipped.append(fo)
                        print(f"skip follow-on: {fo.consumer} ({fo.repo}) -- {fo.skipped_reason}")
                        continue
                    url = execute_follow_on(fo, sources, "main", cross_repo=args.cross_repo, ecosystem_root=ecosystem_root)
                    if url:
                        fo_opened.append(fo)
                        print(f"opened follow-on: {fo.consumer} ({fo.repo}) -- {url}")
                    else:
                        fo_skipped.append(fo)
                        print(f"skip follow-on: {fo.consumer} ({fo.repo}) -- execute opened no PR (empty URL)")
        except SourceError as exc:
            print(f"ERROR: execute failed: {exc}", file=sys.stderr)
            return 2
        print(f"execute summary: {len(opened)} proposal PR(s) opened, {len(skipped)} skipped; {len(fo_opened)} follow-on PR(s) opened, {len(fo_skipped)} skipped.")
        return 0

    if args.json:
        print(json.dumps(build_output(proposals, dry_run), indent=2))
    else:
        print_proposals(proposals, dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
