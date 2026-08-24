"""Hardcoded inventories of the Juniper ecosystem layout.

These are split out so future tools (e.g., cross-repo coverage rollups,
ecosystem-wide doc-quality lints) can reuse the same authoritative sets
without grepping the validator. The hardcoding is intentional -- see the
JUNIPER_2026-03-07_JUNIPER-ECOSYSTEM_CROSS-REPO-LINK-RESOLUTION-PROPOSAL.md design note for the security
rationale (auto-discovery from the filesystem would let a maliciously-named
sibling directory be implicitly trusted).
"""

from __future__ import annotations

import re

__all__ = [
    "ECOSYSTEM_REPOS",
    "ECOSYSTEM_ROOT_ITEMS",
    "CROSS_REPO_PATTERN",
    "ECOSYSTEM_ROOT_PATTERN",
    "MAX_TRAVERSAL_DEPTH",
    "CROSS_REPO_MODES",
]

# Juniper ecosystem repository names. Update this set when repos are added
# or removed from the polyrepo.
#
# It drifted, and drift here is SILENT: a repo missing from this set is not
# classified as cross-repo at all, so ``../juniper-recurrence/notes/x.md`` is
# resolved as an ordinary intra-repo path, fails, and is reported as a broken
# link -- pointing at the link rather than at this stale list. Two repos were
# added to the polyrepo and never added here (fixed 2026-08-24):
#
#   * juniper-recurrence -- a PUBLISHING sibling (8th in the release-train
#     registry), shipping 14 workflows and 3 PyPI packages;
#   * juniper-slacker -- a repo but not a package, like juniper-deploy.
#
# The authoritative roster is util/release_train/registry.yaml's publishing
# repos, plus the two non-package repos. tests/test_doc_tools_drift.py pins
# this set against it so the next addition cannot drift in silence.
ECOSYSTEM_REPOS: frozenset[str] = frozenset(
    {
        "juniper-canopy",
        "juniper-cascor",
        "juniper-cascor-client",
        "juniper-cascor-worker",
        "juniper-data",
        "juniper-data-client",
        "juniper-deploy",
        "juniper-ml",
        "juniper-recurrence",
        "juniper-slacker",
    }
)

# Files and directories that live at the Juniper ecosystem root (parent of
# the juniper-X repos). Repo docs may reference them via ``../<item>`` /
# ``../../<item>`` patterns; the validator classifies these the same way as
# cross-repo links and applies the --cross-repo policy to them. Update this
# set when ecosystem-root files/dirs are added or removed.
ECOSYSTEM_ROOT_ITEMS: frozenset[str] = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "Juniper.code-workspace",
        "Juniper1.code-workspace",
        "backups",
        "logs",
        "notes",
        "prompts",
        "resources",
        "worktrees",
        "juniper-legacy",
    }
)

# Pattern to detect cross-repo relative links: zero or more ``../`` segments
# followed by an ecosystem repo name and a trailing slash.
CROSS_REPO_PATTERN: re.Pattern[str] = re.compile(r"^(?:\.\./)*(" + "|".join(re.escape(r) for r in sorted(ECOSYSTEM_REPOS)) + r")/")

# Pattern to detect ecosystem-root relative links: one or more ``../``
# segments followed by a known ecosystem-root item. Classification only
# applies when the link also escapes the current repo (verified by the
# bounds check at the call site); ``../notes/foo.md`` from a repo subdir
# that still resolves inside the repo is handled by normal intra-repo
# validation.
ECOSYSTEM_ROOT_PATTERN: re.Pattern[str] = re.compile(r"^(?:\.\./)+(" + "|".join(re.escape(n) for n in sorted(ECOSYSTEM_ROOT_ITEMS)) + r")(?:/|$)")

# Maximum allowed directory traversal segments (..) in a single link. Higher
# than five is almost certainly a typo or a path-traversal attempt.
MAX_TRAVERSAL_DEPTH: int = 5

# Valid modes for the --cross-repo flag.
CROSS_REPO_MODES: frozenset[str] = frozenset({"skip", "warn", "check"})
