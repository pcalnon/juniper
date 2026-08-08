#!/usr/bin/env python3
"""Structural archive-guard for the release-train's exempt notes-archive PR (plan S7.2 / S12 step 3.1).

The release-train's ONE gate-exempt PR is the one that *archives the generated release notes and
contains no other change* (plan R5 / S7.1). This module is the required-CI-job CHECK that proves a
PR's diff is exactly that -- so the exempt PR can (later) auto-merge behind a required status check
without ever leaking a code/config change past the owner gate.

It computes a PR's changed-file set (``git diff --name-status <base>...<head>`` -- injected /
path-invokable so the tests are hermetic) and passes ONLY if **all four** structural rules hold
(plan S7.2):

  1. **Add-only**     -- every change is status ``A`` (added). Any ``M`` / ``D`` / ``R`` / ``C`` fails.
  2. **Path-confined**-- every added path matches ``^notes/releases/RELEASE_NOTES_.*\\.md$``.
  3. **Name-valid**   -- each added filename matches the central-archive convention (procedure S11.3):
     ``RELEASE_NOTES_v<semver>.md`` (meta ``juniper-ml``) or ``RELEASE_NOTES_<pkg>_v<semver>.md``
     (every other package), with ``<pkg>`` a registry ``pypi_name`` and ``<semver>`` semver-shaped.
  4. **Single-purpose**-- no other path in the diff, at all.

Layering (plan S7.2 "pass trivially for non-archive PRs"): a PR whose diff does **not** touch
``notes/releases/`` is **SKIP** -- the exempt path does not apply, the standard owner gate governs,
and this check passes (exit 0). Only a PR that *touches* ``notes/releases/`` is held to the four
rules; if it violates any, the check **fails** (exit 1) and the PR simply falls back to the standard
owner gate (plan S7.2: "the PR is untouched and falls back to the standard owner gate -- it never
auto-merges"). The guard has **no side effect** beyond its own pass/fail -- it opens nothing, merges
nothing, and mutates no environment (R7).

Escape hatch (the #1003 link-repair class). Once this guard is a REQUIRED status check, a PR that
*corrects* an already-archived note (a dead-link repair, a typo fix) is unmergeable-by-default, since
rule 1 is add-only. An ``Allow-Archive-Edit: <path>[, <path>...]`` commit trailer anywhere in the
BASE..HEAD commit bodies **waives** rules 1/4 for the named archive files, exactly mirroring the house
``Allow-Docs-Rewrite`` / ``Allow-Symbol-Loss`` idiom (``juniper_ci_tools.docs_additions_check``):
full path, bare basename, or ``*`` for all. The waiver is **narrow by construction** -- it applies only
to a change whose every path is a FLAT ``notes/releases/RELEASE_NOTES_*.md`` file; a waived path that
also drags an out-of-archive path (a rename OUT, a mixed diff) still FAILs. A waived-and-otherwise-clean
diff reports the distinct verdict **WAIVED** (exit 0, the waived paths named), never a silent ``OK``.
The trailer text is *injected* (``--trailers-file``), so the classifier stays pure and the tests stay
hermetic; ``ci.yml`` produces the file with ``git log --format=%B <BASE>..HEAD``. Trailers travel in git
history, so a squash merge MUST carry the trailer into the squash commit message (house gotcha).

Design mirrors ``detect.py`` / ``propose.py``: stdlib-only pure classification the tests drive
directly, a thin injected seam for the one external effect (the git diff + the registry read), a
``--repo-dir`` / ``--name-status-file`` / stdin seam so it runs fully offline, and the house exit
codes ``0`` pass (SKIP or OK) / ``1`` fail (a rule violated) / ``2`` invocation error. ``util/`` is
not pre-commit-lint-gated, so ``tests/test_release_train_archive_guard.py`` IS the gate (the
``env_floor_drift_check`` precedent, shared with the sibling detectors).

Run (CI guard lane): ``python3 util/release_train/archive_guard.py --base origin/main --head HEAD
                     --trailers-file trailers.txt``
Offline / test:      ``python3 util/release_train/archive_guard.py --name-status-file diff.txt``

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-17
Status: permanent utility (Phase 3, exempt-archive structural guard)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - only the git binary with a fixed argv (no shell)
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Same-directory sibling; resolvable both when run as a script (script dir on sys.path[0]) and under
# the tests' ``sys.path.insert(UTIL_DIR)`` idiom (mirrors test_release_train_detect / _propose).
import detect  # noqa: E402

META_PACKAGE = "juniper-ml"
RELEASES_PREFIX = "notes/releases/"

# plan S7.2 rule 2 -- the exact path shape an added archive file must have.
ARCHIVE_PATH_RE = re.compile(r"^notes/releases/RELEASE_NOTES_.*\.md$")

# plan S7.2 rule 3 / procedure S11.3 -- the two filename conventions. A pypi_name is hyphenated
# (never underscored), so the ``_v`` separator between <pkg> and <version> is unambiguous: the pkg
# charset below excludes ``_`` on purpose so ``RELEASE_NOTES_<pkg>_v<ver>.md`` splits cleanly.
_SEMVER = r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+.][0-9A-Za-z.\-+]+)?"
_META_NAME_RE = re.compile(rf"^RELEASE_NOTES_v(?P<ver>{_SEMVER})\.md$")
_PKG_NAME_RE = re.compile(rf"^RELEASE_NOTES_(?P<pkg>[A-Za-z0-9][A-Za-z0-9.\-]*)_v(?P<ver>{_SEMVER})\.md$")


class GuardError(RuntimeError):
    """An invocation / environmental failure (no diff source, git failure) => hard stop (exit 2)."""


# ── data model ───────────────────────────────────────────────────────────────


@dataclass
class Change:
    """One entry from ``git diff --name-status``: a status letter + its path(s)."""

    status: str  # single letter: A/M/D/R/C/T/U (rename/copy carry a numeric score in the raw field)
    paths: list  # 1 path (A/M/D/T) or 2 (R/C: [old, new])

    @property
    def path(self) -> str:
        """The effective (destination) path -- last field, as git name-status reports it."""
        return self.paths[-1] if self.paths else ""

    def display(self) -> str:
        return f"{self.status} {' -> '.join(self.paths)}"


@dataclass
class GuardResult:
    """The guard verdict for one PR diff. ``passed`` is the CI pass/fail (SKIP/OK/WAIVED all pass)."""

    verdict: str  # "SKIP" (not an archive PR) | "OK" | "WAIVED" (trailer-waived edits) | "FAIL"
    is_archive_pr: bool
    added: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    changes: list = field(default_factory=list)
    waived: list = field(default_factory=list)  # display strings of trailer-waived non-add changes

    @property
    def passed(self) -> bool:
        return self.verdict in ("SKIP", "OK", "WAIVED")

    def to_dict(self) -> dict:
        return {
            "schema": "juniper-release-train/archive-guard/v1",
            "verdict": self.verdict,
            "is_archive_pr": self.is_archive_pr,
            "passed": self.passed,
            "added": list(self.added),
            "violations": list(self.violations),
            "waived": list(self.waived),
            "change_count": len(self.changes),
        }


# ── name-status parsing ──────────────────────────────────────────────────────


def parse_name_status(text: str) -> list:
    """Parse ``git diff --name-status`` output into ``Change`` records.

    Each line is TAB-separated: ``<status>\\t<path>`` or (rename/copy) ``<status>\\t<old>\\t<new>``.
    The status may carry a similarity score (``R100`` / ``C075``); only the leading letter is kept."""
    changes: list = []
    for raw in (text or "").splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0].strip()[:1].upper()
        paths = [p for p in parts[1:] if p.strip()]
        if not paths:
            continue
        changes.append(Change(status=status, paths=paths))
    return changes


# ── filename convention (rule 3) ─────────────────────────────────────────────


def filename_valid(basename: str, known_pypi_names: set) -> bool:
    """True when ``basename`` is a convention-valid central-archive filename (plan S7.2 rule 3).

    ``RELEASE_NOTES_v<semver>.md`` is valid only for the meta-package (``juniper-ml``);
    ``RELEASE_NOTES_<pkg>_v<semver>.md`` requires ``<pkg>`` to be a registered ``pypi_name`` other
    than the meta (the meta uses the bare ``_v`` form, so a ``RELEASE_NOTES_juniper-ml_v*.md`` is a
    deliberate reject)."""
    m = _META_NAME_RE.match(basename)
    if m:
        return META_PACKAGE in known_pypi_names
    m = _PKG_NAME_RE.match(basename)
    if m:
        pkg = m.group("pkg")
        return pkg in known_pypi_names and pkg != META_PACKAGE
    return False


# ── escape-hatch trailer parsing (Allow-Archive-Edit) ────────────────────────

# Whole-body scan (MULTILINE, not just the last trailer block): the house convention is that an
# ``Allow-*`` marker anywhere in ANY commit message of the BASE..HEAD range counts -- identical to
# ``juniper_ci_tools.docs_additions_check._ALLOW_RE`` so the two escapes behave the same way.
_ALLOW_ARCHIVE_EDIT_RE = re.compile(r"^\s*Allow-Archive-Edit:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def parse_allow_trailers(messages: str) -> tuple:
    """Return ``(enumerated tokens, wildcard_seen)`` from concatenated commit messages.

    ``Allow-Archive-Edit: notes/releases/RELEASE_NOTES_juniper-canopy_v0.6.0.md, OTHER.md`` yields the
    two tokens; a ``*`` token sets the wildcard (waives every archive-confined edit in the diff).
    Copied verbatim from the docs screen's ``parse_allow_trailers`` (comma- or whitespace-separated
    tokens, case-insensitive trailer key) so the two escapes are keystroke-compatible."""
    allowed: set = set()
    wildcard = False
    for m in _ALLOW_ARCHIVE_EDIT_RE.finditer(messages or ""):
        for tok in re.split(r"[,\s]+", m.group(1).strip()):
            tok = tok.strip()
            if not tok:
                continue
            if tok == "*":
                wildcard = True
                continue
            allowed.add(tok)
    return allowed, wildcard


def _waives(path: str, allowed: set, wildcard: bool) -> bool:
    """Wildcard, exact repo-relative path, or bare basename -- the docs-screen matcher semantics."""
    if wildcard:
        return True
    return path in allowed or path.rsplit("/", 1)[-1] in allowed


def _is_flat_archive_path(path: str) -> bool:
    """True for a FLAT ``notes/releases/RELEASE_NOTES_*.md`` path (the waiver's confinement test)."""
    if not ARCHIVE_PATH_RE.match(path):
        return False
    return "/" not in path[len(RELEASES_PREFIX):]


def change_waived(change: Change, allowed: set, wildcard: bool) -> bool:
    """True when a non-add change is fully confined to flat archive files AND every path is waived.

    Both conditions are deliberately conjunctive over **every** path of the change: a rename whose
    other side leaves ``notes/releases/`` (or lands in a nested subdirectory) is never waivable, so the
    escape can only ever relax an in-place archive correction -- never smuggle an out-of-archive edit
    onto the exempt auto-merge lane."""
    if not change.paths:
        return False
    return all(_is_flat_archive_path(p) and _waives(p, allowed, wildcard) for p in change.paths)


# ── the guard (pure) ─────────────────────────────────────────────────────────


def touches_releases(changes: list) -> bool:
    """True when any changed path (either side of a rename) is under ``notes/releases/``."""
    return any(p.startswith(RELEASES_PREFIX) for c in changes for p in c.paths)


def classify_diff(changes: list, known_pypi_names: set, allowed: "set | None" = None, wildcard: bool = False) -> GuardResult:
    """Apply the four structural rules (plan S7.2) to a parsed diff.

    Returns SKIP (pass) when the diff does not touch ``notes/releases/`` (not an archive PR); else
    OK (pass) when all four rules hold, WAIVED (pass) when the only would-be violations are
    ``Allow-Archive-Edit``-waived in-place archive edits, or FAIL with the specific rule violation(s).

    ``allowed`` / ``wildcard`` come from :func:`parse_allow_trailers` over the BASE..HEAD commit
    bodies; the default (no trailer) reproduces the pre-escape behaviour byte-for-byte."""
    changes = list(changes)
    if not touches_releases(changes):
        return GuardResult(verdict="SKIP", is_archive_pr=False, changes=changes)

    allowed = set(allowed or ())
    violations: list = []
    added: list = []
    waived: list = []

    # Which non-add changes the trailer waives (rules 1 + 4 skip them; every other rule is unchanged).
    waived_changes = [c for c in changes if c.status != "A" and change_waived(c, allowed, wildcard)]
    waived_ids = {id(c) for c in waived_changes}
    waived = [c.display() for c in waived_changes]
    waived_paths = {p for c in waived_changes for p in c.paths}

    # Rule 1 -- add-only (waived in-place archive edits excepted).
    for c in changes:
        if c.status != "A" and id(c) not in waived_ids:
            violations.append(f"rule1 (add-only): non-add change '{c.display()}' -- the exempt archive PR must add files only, never modify/delete/rename (waive an intended in-place archive edit with an 'Allow-Archive-Edit: <path>' commit trailer)")

    # Rule 2 + Rule 3 -- every ADDED path is a well-formed, convention-valid archive file.
    for c in changes:
        if c.status != "A":
            continue
        path = c.path
        added.append(path)
        if not ARCHIVE_PATH_RE.match(path):
            violations.append(f"rule2 (path-confined): added path '{path}' is not a notes/releases/RELEASE_NOTES_*.md file")
            continue
        basename = path[len(RELEASES_PREFIX):]
        if "/" in basename:
            violations.append(f"rule2 (path-confined): added path '{path}' is nested under notes/releases/ (archive files are flat)")
            continue
        if not filename_valid(basename, known_pypi_names):
            violations.append(f"rule3 (name-valid): added filename '{basename}' fails the RELEASE_NOTES_v<semver> / RELEASE_NOTES_<pkg>_v<semver> convention or names an unregistered package")

    # Rule 4 -- single-purpose: no path anywhere in the diff outside the archive shape. A waived
    # path is flat-archive-confined by construction (change_waived), so this loop could never flag
    # it; the explicit skip states the contract rather than relying on that implication.
    for c in changes:
        for p in c.paths:
            if p in waived_paths:
                continue
            if not ARCHIVE_PATH_RE.match(p):
                violations.append(f"rule4 (single-purpose): out-of-scope path '{p}' ({c.status}) -- the exempt PR must contain nothing but notes/releases/RELEASE_NOTES_*.md file(s)")

    # Dedup while preserving order (rule 2 and rule 4 legitimately both flag an out-of-path add).
    seen: set = set()
    deduped = [v for v in violations if not (v in seen or seen.add(v))]
    if deduped:
        verdict = "FAIL"
    elif waived:
        verdict = "WAIVED"  # clean ONLY because the trailer waived an in-place archive edit
    else:
        verdict = "OK"
    return GuardResult(verdict=verdict, is_archive_pr=True, added=added, violations=deduped, changes=changes, waived=waived)


# ── injected seam (the one external effect: the diff + the registry) ──────────


def git_name_status(base: str, head: str, repo_dir: Path) -> str:
    """``git -C <repo_dir> diff --name-status <base>...<head>`` (fixed argv, no shell).

    The three-dot range is the PR's net change set (merge-base(base, head)..head), matching what
    ``gh pr diff`` reports."""
    try:
        proc = subprocess.run(  # nosec B603,B607 - fixed argv, no shell
            ["git", "-C", str(repo_dir), "diff", "--name-status", f"{base}...{head}"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GuardError("git not found (needed to compute the PR diff)") from exc
    except subprocess.TimeoutExpired as exc:
        raise GuardError(f"git diff timed out: {base}...{head}") from exc
    if proc.returncode != 0:
        raise GuardError(f"git diff --name-status {base}...{head} failed: {(proc.stderr or '').strip()[:200]}")
    return proc.stdout


def load_known_pypi_names(registry_path: "Path | None") -> set:
    """Registered ``pypi_name`` set from the registry (via ``detect.load_registry``)."""
    try:
        entries = detect.load_registry(registry_path)
    except Exception as exc:  # noqa: BLE001 - a missing/broken registry is an invocation error
        raise GuardError(f"cannot load registry.yaml: {exc}") from exc
    names = {e.pypi_name for e in entries}
    if not names:
        raise GuardError("registry.yaml resolved to zero packages")
    return names


# ── reporting ────────────────────────────────────────────────────────────────


def render_report(result: GuardResult) -> str:
    lines = ["Juniper release-train -- exempt notes-archive structural guard (plan S7.2)", ""]
    if result.verdict == "SKIP":
        lines.append("  verdict: SKIP -- the diff does not touch notes/releases/; not an archive PR.")
        lines.append("  The standard owner gate governs this PR; the exempt path does not apply.")
        return "\n".join(lines)
    if result.verdict == "OK":
        lines.append(f"  verdict: OK -- add-only, path-confined, name-valid, single-purpose ({len(result.added)} archive file(s)).")
        for a in result.added:
            lines.append(f"    + {a}")
        return "\n".join(lines)
    if result.verdict == "WAIVED":
        lines.append(f"  verdict: WAIVED -- path-confined and single-purpose; {len(result.waived)} in-place archive edit(s) waived by an 'Allow-Archive-Edit:' commit trailer.")
        for a in result.added:
            lines.append(f"    + {a}")
        for w in result.waived:
            lines.append(f"    ~ waived (Allow-Archive-Edit): {w}")
        lines.append("  Carry the trailer into the SQUASH commit message when merging -- trailers travel in git history and the post-merge screens re-read them.")
        return "\n".join(lines)
    lines.append(f"  verdict: FAIL -- {len(result.violations)} rule violation(s); the PR falls back to the standard owner gate (it never auto-merges).")
    for v in result.violations:
        lines.append(f"    - {v}")
    if result.waived:
        for w in result.waived:
            lines.append(f"    ~ waived (Allow-Archive-Edit): {w}")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────


def _read_diff_text(args: argparse.Namespace) -> str:
    if args.name_status_file is not None:
        if args.name_status_file == "-":
            return sys.stdin.read()
        try:
            return Path(args.name_status_file).read_text(encoding="utf-8")
        except OSError as exc:
            raise GuardError(f"cannot read --name-status-file {args.name_status_file}: {exc}") from exc
    if args.base and args.head:
        return git_name_status(args.base, args.head, Path(args.repo_dir).resolve())
    raise GuardError("no diff source: pass --name-status-file PATH (or '-'), or --base REF --head REF")


def _validate_seams(args: argparse.Namespace) -> None:
    """Reject seam combinations that cannot both be satisfied -- BEFORE either read drains stdin."""
    if args.name_status_file == "-" and args.trailers_file == "-":
        raise GuardError("--name-status-file and --trailers-file cannot both read stdin ('-')")


def _read_trailers_text(args: argparse.Namespace) -> str:
    """The BASE..HEAD commit bodies for the ``Allow-Archive-Edit`` escape (injected, never shelled).

    Absent ``--trailers-file`` the escape is simply inactive (fail-closed: no trailers => no waivers),
    which is exactly the pre-escape behaviour. ``ci.yml`` produces the file with
    ``git log --format=%B <BASE>..HEAD``; the tests write it directly."""
    if args.trailers_file is None:
        return ""
    if args.trailers_file == "-":
        return sys.stdin.read()
    try:
        return Path(args.trailers_file).read_text(encoding="utf-8")
    except OSError as exc:
        raise GuardError(f"cannot read --trailers-file {args.trailers_file}: {exc}") from exc


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="release_train/archive_guard.py", description="Structural guard for the release-train's exempt notes-archive PR (plan S7.2). Exit 0 pass (SKIP/OK/WAIVED), 1 fail, 2 invocation error.")
    p.add_argument("--base", default=None, help="base ref for the diff (e.g. origin/main)")
    p.add_argument("--head", default=None, help="head ref for the diff (e.g. HEAD)")
    p.add_argument("--repo-dir", default=".", help="git checkout to diff in (default: cwd)")
    p.add_argument("--name-status-file", default=None, metavar="PATH", help="read `git diff --name-status` output from a file ('-' for stdin) instead of running git (hermetic/offline)")
    p.add_argument("--trailers-file", default=None, metavar="PATH", help="read the BASE..HEAD commit bodies (`git log --format=%%B <BASE>..HEAD`) from a file ('-' for stdin) so an 'Allow-Archive-Edit: <path>' trailer can waive an in-place archive edit; omitted => the escape is inactive")
    p.add_argument("--registry", default=None, help="path to registry.yaml (default: alongside detect.py)")
    p.add_argument("--json", action="store_true", help="emit the verdict as JSON instead of the human report")
    return p.parse_args(argv)


def main(argv: "list[str] | None" = None) -> int:
    args = parse_args(argv)
    try:
        _validate_seams(args)
        registry_path = Path(args.registry) if args.registry else None
        known = load_known_pypi_names(registry_path)
        diff_text = _read_diff_text(args)
        trailers_text = _read_trailers_text(args)
    except GuardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    allowed, wildcard = parse_allow_trailers(trailers_text)
    result = classify_diff(parse_name_status(diff_text), known, allowed, wildcard)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(render_report(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
