"""Docs deletion-magnitude screen -- BASE vs HEAD markdown (sequence-safety gate G2 / G3).

Library implementation behind the ``juniper-docs-additions-check`` console script
(the thin argparse wrapper is :mod:`juniper_ci_tools.cli_docs_additions_check`).
Productionized (deletion-magnitude only, not the full LOST-IN-MERGE reconstruction)
from the 2026-07-28 Cursor-fleet docs census (Proposal P2 S2; juniper-ml
``notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md``) and
migrated into ``juniper-ci-tools`` as the single, PyPI-distributed source of truth
(sequence-safety rollout plan
``notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`` Wave 0).

The flood's docs class (a *net section deletion*) was one no existing check could see:
the doc-links validator only catches dangling anchors, and markdownlint excludes
``notes/`` + ``docs/``. So a merge that dropped a whole runbook section stayed green.

A bare "any ``-`` hunk fails" rule is too blunt -- the UPDATE-target docs
(``REFERENCE.md``, the runbooks, the cheatsheet) take legitimate line *replacements* on
nearly every edit, so it would paint honest docs PRs red or train a reflex
``docs-rewrite`` waiver. Instead a **magnitude-gated** rule:

  * FAIL on a deleted Markdown **heading** line (a ``-`` hunk whose content matches
    ``^\\s{0,3}#{1,6}\\s``) UNLESS the same hunk also adds a heading (a retitle -> WARN).
  * FAIL on a run of **>= N consecutive deleted lines with no adjacent addition**
    (``added == 0 and deleted >= min_run``; default N = 5) -- the net-section-removal
    signature.
  * WARN (annotate, not fail) on smaller deletions and small in-place swaps (a few
    deleted lines bracketed by additions -- a normal edit).

Blind spot (stated honestly, mirrors the symbol screen's WEAKENED note). A *lopsided
swap* that deletes a large block but adds a line or two in the same hunk evades the
pure-run rule (added > 0). The heading-deletion rule usually still catches it (sections
carry headings), but a section-body gut that removes no heading and adds one filler line
can slip to WARN. That residue is for human review, not this magnitude screen.

Escape hatch. A ``Allow-Docs-Rewrite: <path>[, ...]`` trailer in any commit of the
BASE..HEAD range waives the enumerated files (``*`` waives all docs in the diff); it
travels in git history so it works for both the per-PR and the post-merge gate.

Scope. By default (no ``scope``) the universal docs cluster is used: ``AGENTS.md`` (and
its ``CLAUDE.md`` symlink), ``docs/**/*.md``, and ``notes/**/*.md``. A caller may pass
``scope`` globs (from the CLI ``--scope`` flag) to screen a different markdown surface;
a path is then in scope iff it matches any glob AND ends ``.md``. An explicit ``files``
list bypasses the scope filter (any ``.md`` path).

Exit codes (surfaced by the CLI): 0 = clean (no unwaived FAIL), 1 = >= 1 unwaived FAIL,
2 = usage / invocation error. WARN / WAIVED never fail.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_MIN_RUN = 5  # >= this many consecutive deleted lines (no adjacent add) -> FAIL

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_HUNK_RE = re.compile(r"^@@ ")


def in_docs_scope(path: str) -> bool:
    """AGENTS.md (+ its CLAUDE.md symlink), docs/**/*.md, notes/**/*.md."""
    if path in ("AGENTS.md", "CLAUDE.md"):
        return True
    if path.endswith(".md") and (path.startswith("docs/") or path.startswith("notes/")):
        return True
    return False


# ---- scope globs (--scope override; POSIX path globs, 3.11-floor safe) ------


def _glob_to_regex(glob: str) -> str:
    """Translate a POSIX path glob into a regex source (used with ``re.fullmatch``).

    Explicit ``**`` recursion, so it does not depend on ``PurePath.full_match`` (3.13+,
    unavailable on the ci-tools 3.11 floor):

      * ``**/`` matches zero or more whole path segments, so ``docs/**/*.md`` matches BOTH
        ``docs/a.md`` and ``docs/sub/a.md``. A trailing / embedded ``**`` matches anything.
      * ``*`` matches within a single segment (any run of non-``/`` characters).
      * ``?`` matches a single non-``/`` character. Every other char is literal.
    """
    i, n = 0, len(glob)
    out: list[str] = []
    while i < n:
        c = glob[i]
        if c == "*":
            if i + 1 < n and glob[i + 1] == "*":
                i += 2
                if i < n and glob[i] == "/":
                    out.append("(?:[^/]+/)*")  # **/ -> zero or more whole segments
                    i += 1
                else:
                    out.append(".*")  # trailing / embedded ** -> anything
            else:
                out.append("[^/]*")  # * -> within a single segment
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


def _match_scope(path: str, globs: list[str]) -> bool:
    """True iff ``path`` matches any glob in ``globs`` (POSIX path-glob semantics)."""
    return any(re.fullmatch(_glob_to_regex(g), path) is not None for g in globs)


# ---- git helpers (standalone so the module needs no cross-import) ----------


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def resolve_ref(root: str, ref: str) -> Optional[str]:
    cp = _git(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")
    out = cp.stdout.strip()
    return out if cp.returncode == 0 and out else None


def changed_files(root: str, base: str, head: str) -> list[str]:
    cp = _git(root, "diff", "--name-only", f"{base}...{head}")
    return [ln for ln in cp.stdout.splitlines() if ln]


def file_diff(root: str, base: str, head: str, path: str) -> str:
    """Unified=0 base->head diff for one file (minimal, tight hunks)."""
    return _git(root, "diff", "--unified=0", "--no-color", base, head, "--", path).stdout


def range_messages(root: str, base: str, head: str) -> str:
    return _git(root, "log", "--format=%B", f"{base}..{head}").stdout


# ---- hunk parsing ----------------------------------------------------------


@dataclass
class Hunk:
    deleted: list[str] = field(default_factory=list)  # content of '-' lines
    added: list[str] = field(default_factory=list)  # content of '+' lines


def parse_hunks(diff_text: str) -> list[Hunk]:
    """Split a unified diff into hunks, collecting deleted / added line contents.

    With ``--unified=0`` each hunk's deleted lines are contiguous in the old file, so a
    hunk with ``added == 0`` is a run of that many consecutive deletions with no
    adjacent addition -- exactly the P2 S2 magnitude signal.
    """
    hunks: list[Hunk] = []
    cur: Optional[Hunk] = None
    for line in diff_text.splitlines():
        if _HUNK_RE.match(line):
            cur = Hunk()
            hunks.append(cur)
            continue
        if cur is None:
            continue  # pre-hunk file header (diff --git / index / --- / +++)
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("-"):
            cur.deleted.append(line[1:])
        elif line.startswith("+"):
            cur.added.append(line[1:])
    return hunks


# ---- classification --------------------------------------------------------


@dataclass
class Finding:
    path: str
    reason: str  # heading-deletion | deletion-run | small-deletion
    severity: str  # FAIL | WARN | WAIVED
    detail: dict = field(default_factory=dict)


def classify_file(path: str, hunks: list[Hunk], min_run: int) -> list[Finding]:
    findings: list[Finding] = []
    for h in hunks:
        deleted, added = len(h.deleted), len(h.added)
        if deleted == 0:
            continue  # pure addition -- the additions-only happy path
        del_headings = [ln for ln in h.deleted if _HEADING_RE.match(ln)]
        add_headings = [ln for ln in h.added if _HEADING_RE.match(ln)]
        if del_headings and not add_headings:
            findings.append(Finding(path, "heading-deletion", "FAIL", {"headings": [ln.strip()[:120] for ln in del_headings], "deleted": deleted, "added": added}))
        elif added == 0 and deleted >= min_run:
            findings.append(Finding(path, "deletion-run", "FAIL", {"deleted": deleted, "min_run": min_run}))
        else:
            findings.append(Finding(path, "small-deletion", "WARN", {"deleted": deleted, "added": added}))
    return findings


# ---- escape-hatch trailer parsing ------------------------------------------

_ALLOW_RE = re.compile(r"^\s*Allow-Docs-Rewrite:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def parse_allow_trailers(messages: str) -> tuple[set[str], bool]:
    """Return (enumerated file tokens, wildcard_seen). A ``*`` waives all docs files."""
    allowed: set[str] = set()
    wildcard = False
    for m in _ALLOW_RE.finditer(messages or ""):
        for tok in re.split(r"[,\s]+", m.group(1).strip()):
            tok = tok.strip()
            if not tok:
                continue
            if tok == "*":
                wildcard = True
                continue
            allowed.add(tok)
    return allowed, wildcard


def _waives(path: str, allowed: set[str], wildcard: bool) -> bool:
    if wildcard:
        return True
    return path in allowed or path.rsplit("/", 1)[-1] in allowed


def apply_waivers(findings: list[Finding], allowed: set[str], wildcard: bool) -> None:
    for f in findings:
        if f.severity == "FAIL" and _waives(f.path, allowed, wildcard):
            f.severity = "WAIVED"
            f.detail = {**f.detail, "waived_by": "Allow-Docs-Rewrite trailer"}


# ---- driver ----------------------------------------------------------------


def run(root: str, base: str, head: str, files: Optional[list[str]], min_run: int, scope: Optional[list[str]] = None) -> tuple[int, dict]:
    """Return (exit_code, report). exit_code: 0 clean, 1 findings, 2 invocation error.

    ``scope`` (from the CLI ``--scope`` flag) is an optional list of POSIX path globs.
    When None/empty the universal :func:`in_docs_scope` predicate is used verbatim;
    otherwise a discovered path is in scope iff it matches any glob AND ends ``.md``.
    An explicit ``files`` list bypasses scope entirely.
    """
    base_sha = resolve_ref(root, base)
    head_sha = resolve_ref(root, head)
    if base_sha is None or head_sha is None:
        bad = base if base_sha is None else head
        return 2, {"error": f"could not resolve ref: {bad!r}"}

    if files:
        scoped = [p for p in files if p.endswith(".md")]
        skipped = [p for p in files if p not in scoped]
    else:
        discovered = changed_files(root, base, head)
        if scope:
            # A discovered path is in scope iff it matches any --scope glob AND ends .md.
            scoped = [p for p in discovered if p.endswith(".md") and _match_scope(p, scope)]
        else:
            # No --scope: reproduce the universal in_docs_scope() predicate verbatim.
            scoped = [p for p in discovered if in_docs_scope(p)]
        skipped = [p for p in discovered if p not in scoped]

    findings: list[Finding] = []
    for path in sorted(set(scoped)):
        hunks = parse_hunks(file_diff(root, base_sha, head_sha, path))
        findings.extend(classify_file(path, hunks, min_run))

    allowed, wildcard = parse_allow_trailers(range_messages(root, base_sha, head_sha))
    apply_waivers(findings, allowed, wildcard)

    fails = [f for f in findings if f.severity == "FAIL"]
    by_reason: dict[str, int] = {}
    for f in findings:
        by_reason[f.reason] = by_reason.get(f.reason, 0) + 1

    report = {
        "base": base_sha,
        "head": head_sha,
        "min_run": min_run,
        "stats": {
            "files_screened": len(scoped),
            "skipped_out_of_scope": sorted(set(skipped)),
            "findings_total": len(findings),
            "fail_count": len(fails),
            "by_reason": by_reason,
            "waived_files": sorted(allowed),
            "wildcard_waiver": wildcard,
        },
        "findings": [{"path": f.path, "reason": f.reason, "severity": f.severity, "detail": f.detail} for f in sorted(findings, key=lambda x: (x.path, x.reason))],
    }
    return (1 if fails else 0), report
