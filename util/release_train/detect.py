#!/usr/bin/env python3
"""Juniper PyPI release-train detection engine (report-only; plan S4.2/S4.3).

Answers, per package, the one question the release train exists to answer:
*does this package have changes that need a PyPI deploy?* -- with machine-readable
evidence and taking no action. It reproduces the companion audit's classification
pipeline (``JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-SURFACE-AUDIT.md`` S7)
against ``registry.yaml`` (the 18-package registry, plan S4.1).

Algorithm per package (plan S4.2, in order):

  1. Released truth  -- PyPI JSON ``info.version`` + latest upload time (authoritative
     for what is actually deployed; immune to local/tag drift).
  2. Declared version -- ``[project].version`` (static) or ``_version.py __version__``
     (dynamic: model-core + the 3 recurrence packages). ``declared > released`` short-
     circuits to BUMPED_NOT_RELEASED; ``declared < released`` to ANOMALY (a human-only
     yanked/rolled-back state).
  3. Diff base       -- the newest tag under ``tag_pattern`` whose stripped version ==
     the released version (S7.3: "prefer the tag that matches the current PyPI version").
  4. Remote-authoritative diff -- ``gh api repos/<owner>/<repo>/compare/<tag>...main``
     (default), path-scoped client-side to the package's ``ship_paths`` minus
     ``exclude_paths``. Local checkouts can be stale (F-6), so the diff is remote by
     default; ``--local-git`` is an offline fallback. The compare API caps ``files`` at
     300; when that cap is hit and no ship evidence is found, the verdict is
     SHIP_UNCERTAIN, never a silent UP_TO_DATE.
  5. SHIP vs NON-SHIP filter -- the correctness crux. A SHIP classification requires a
     SUBSTANTIVE, non-comment hunk in a SHIP-path file. Pure comment/docstring/link
     edits are discounted (this guards the 2026-07-04 notes-rename false-positive class
     that misclassified UP_TO_DATE packages). Patch-unavailable => SHIP_UNCERTAIN.
  6. CHANGELOG [Unreleased] corroboration -- corroborating, NOT authoritative; the
     commit-diff signal wins on conflict, and any conflict is surfaced in the manifest.
  7. SemVer proposal (plan S6, pre-1.0: breaking-or-feature => MINOR, fix => PATCH).
     Advisory only.
  8. Release-hygiene flags (orthogonal to "needs deploy"): TAG_ONLY (no GitHub Release
     for the diff-base tag) and NOTES_MISSING (no central notes/releases/ archive).

Output: a release-manifest JSON (``--json``) + a human table (plan S4.3). Exit codes
follow the house convention:

  0  clean scan (every package UP_TO_DATE).
  1  at least one package needs action (UNRELEASED_CHANGES / BUMPED_NOT_RELEASED /
     NEVER_RELEASED / ANOMALY / SHIP_UNCERTAIN).
  2  invocation / network error (a scan failure is a hard stop, not a silent empty result).

All external data sources (PyPI fetch, ``gh`` api, git, filesystem reads) are injected
through the ``Sources`` object so ``tests/test_release_train_detect.py`` is fully
hermetic (no network, no real gh, no real pip). ``util/`` is not pre-commit-lint-gated,
so that unittest IS the gate (the ``env_floor_drift_check`` precedent).

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-11
Status: permanent utility (Phase 1, report-only)
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess  # nosec B404 - only the git/gh binaries with fixed argv (no shell)
import sys
import tokenize
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

try:
    import tomllib  # Python >= 3.11 (juniper-ml requires >= 3.12)
except ModuleNotFoundError:  # pragma: no cover - regex fallback below
    tomllib = None  # type: ignore[assignment]

try:
    from packaging.version import InvalidVersion, Version  # near-universal (pip depends on it)
except ModuleNotFoundError:  # pragma: no cover - tuple fallback below
    Version = None  # type: ignore[assignment]
    InvalidVersion = Exception  # type: ignore[assignment,misc]

DEFAULT_OWNER = os.environ.get("JUNIPER_RELEASE_TRAIN_OWNER", "pcalnon")
DEFAULT_REGISTRY = Path(__file__).resolve().parent / "registry.yaml"
META_REPO = "juniper-ml"
PYPI_JSON_URL = "https://pypi.org/pypi/{name}/json"

# Classifications (plan S4.3 enum).
UP_TO_DATE = "UP_TO_DATE"
UNRELEASED_CHANGES = "UNRELEASED_CHANGES"
BUMPED_NOT_RELEASED = "BUMPED_NOT_RELEASED"
NEVER_RELEASED = "NEVER_RELEASED"
SHIP_UNCERTAIN = "SHIP_UNCERTAIN"
ANOMALY = "ANOMALY"

# Any of these means "this package needs owner attention" -> process exit 1.
ACTION_CLASSIFICATIONS = frozenset({UNRELEASED_CHANGES, BUMPED_NOT_RELEASED, NEVER_RELEASED, SHIP_UNCERTAIN, ANOMALY})

# NON-SHIP basenames (docs / meta / packaging paperwork; audit S7.5).
NONSHIP_BASENAMES = frozenset({"README.md", "README.rst", "README", "CHANGELOG.md", "CHANGELOG", "AGENTS.md", "CLAUDE.md", "LICENSE", "LICENSE.md", "MANIFEST.in", ".gitignore", ".dockerignore", "py.typed"})

# optional-dependencies extras that are test/tooling-only (NON-SHIP; audit S7.5).
TEST_EXTRAS = frozenset({"test", "tests", "dev", "develop", "lint", "docs", "doc", "typing", "mypy", "coverage", "cov", "ci"})

# Keep-a-Changelog category -> SemVer signal (plan S6, pre-1.0).
FEATURE_CATEGORIES = frozenset({"added", "changed", "deprecated"})
FIX_CATEGORIES = frozenset({"fixed", "security"})
BREAKING_CATEGORIES = frozenset({"removed"})


class SourceError(RuntimeError):
    """An environmental failure (network / gh / transport) => hard stop (exit 2)."""


# ── version helpers (packaging with a numeric-tuple fallback; env_floor precedent) ──


def _vtuple(v: str) -> tuple[int, ...]:
    head = re.split(r"[^0-9.]", v, maxsplit=1)[0]
    parts = [int(p) for p in head.split(".") if p.isdigit()]
    return tuple(parts) or (0,)


def version_cmp(a: str, b: str) -> int:
    """-1 if a<b, 0 if a==b, 1 if a>b (packaging-aware; tuple fallback)."""
    if Version is not None:
        try:
            va, vb = Version(a), Version(b)
            return -1 if va < vb else (1 if va > vb else 0)
        except InvalidVersion:
            pass
    ta, tb = _vtuple(a), _vtuple(b)
    return -1 if ta < tb else (1 if ta > tb else 0)


def bump_version(released: str, bump: str) -> "str | None":
    """Apply a SemVer bump to the leading release triple (pre-1.0 policy, plan S6)."""
    if bump == "none":
        return None
    t = list(_vtuple(released))
    while len(t) < 3:
        t.append(0)
    major, minor, patch = t[0], t[1], t[2]
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return None


# ── registry ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PackageEntry:
    pypi_name: str
    repo: str
    path: str
    version_source: str
    tag_pattern: str
    archive_name: str
    trigger: dict
    verify: dict
    depends_on: list
    ship_paths: list
    exclude_paths: list

    @property
    def pyproject_rel(self) -> str:
        """Repo-relative path of this package's pyproject.toml ("pyproject.toml" for path=".")."""
        return os.path.normpath(os.path.join(self.path, "pyproject.toml")).replace(os.sep, "/")

    @property
    def import_package(self) -> str:
        """Import package name (dist name with '-' -> '_'); used to locate _version.py."""
        return self.pypi_name.replace("-", "_")


def load_registry(path: "Path | None" = None) -> list[PackageEntry]:
    import yaml  # noqa: PLC0415 - PyYAML is already a test/util dependency in this repo

    path = Path(path) if path else DEFAULT_REGISTRY
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries: list[PackageEntry] = []
    for raw in data.get("packages", []) or []:
        entries.append(
            PackageEntry(
                pypi_name=raw["pypi_name"],
                repo=raw["repo"],
                path=raw["path"],
                version_source=raw["version_source"],
                tag_pattern=raw["tag_pattern"],
                archive_name=raw["archive_name"],
                trigger=dict(raw.get("trigger", {})),
                verify=dict(raw.get("verify", {})),
                depends_on=list(raw.get("depends_on", []) or []),
                ship_paths=list(raw.get("ship_paths", []) or []),
                exclude_paths=list(raw.get("exclude_paths", []) or []),
            )
        )
    return entries


# ── data sources (injectable) ────────────────────────────────────────────────


@dataclass
class FileChange:
    filename: str
    status: str
    patch: "str | None"
    cumulative: bool = True  # False = a single-commit patch (line numbers do NOT align with HEAD)
    substantive: "bool | None" = None  # pre-computed verdict (fallback .py, base-vs-head content); overrides patch analysis


@dataclass
class CompareResult:
    files: list  # list[FileChange]
    commits: list  # list[str] first-line commit messages (for SemVer)
    truncated: bool = False
    ok: bool = True
    error: "str | None" = None


@dataclass
class Sources:
    """All external I/O the detector needs, injected for hermetic testing."""

    pypi_json: Callable[[str], "dict | None"]
    list_tags: Callable[[str], list]
    list_releases: Callable[[str], set]
    compare: Callable[["PackageEntry", str, str], CompareResult]
    read_file: Callable[["PackageEntry", str], "str | None"]


def base_dir_for(entry: PackageEntry, repo_root: Path, ecosystem_root: Path) -> Path:
    """Filesystem root of a package's owning repo checkout."""
    return repo_root if entry.repo == META_REPO else (ecosystem_root / entry.repo)


# --- default (live) source implementations -----------------------------------


def _http_get_json(url: str, timeout: int = 20) -> "dict | None":
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # nosec B310 - fixed https PyPI host
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None  # never published
        raise SourceError(f"PyPI HTTP {exc.code} for {url}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SourceError(f"PyPI fetch failed for {url}: {exc}") from exc


def _gh_run(args: list, timeout: int = 90) -> "str | None":
    """Run ``gh api <args>`` with a fixed argv (no shell). Returns stdout, or None on a
    404 (caller decides). Any transport/auth failure raises SourceError (=> exit 2)."""
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603 - fixed argv, no shell
    except FileNotFoundError as exc:
        raise SourceError("gh CLI not found (install/authenticate GitHub CLI, or use --local-git)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"gh api timed out: {' '.join(args)}") from exc
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if "Not Found" in stderr or "HTTP 404" in stderr:
            return None
        raise SourceError(f"gh api failed ({' '.join(args)}): {stderr[:200]}")
    return proc.stdout


def _gh_lines(args: list) -> "list[str] | None":
    """gh api with ``--paginate --jq`` -> newline-joined scalars flattened across pages."""
    out = _gh_run(args)
    if out is None:
        return None
    return [ln for ln in out.splitlines() if ln.strip()]


def _gh_json_single(path: str) -> "Any | None":
    out = _gh_run([path])
    if out is None:
        return None
    try:
        return json.loads(out or "null")
    except ValueError as exc:
        raise SourceError(f"gh api returned non-JSON for {path}") from exc


def _git_text(repo_dir: Path, *args: str, timeout: int = 120) -> "str | None":
    """Run ``git -C <repo_dir> <args>`` (fixed argv, no shell). None on non-zero exit."""
    try:
        proc = subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603,B607 - fixed argv
    except FileNotFoundError as exc:
        raise SourceError("git not found (needed for --local-git and the >300-file compare fallback)") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"git timed out in {repo_dir}: {' '.join(args)}") from exc
    return proc.stdout if proc.returncode == 0 else None


def local_git_compare(entry: PackageEntry, base: str, head: str, repo_dir: Path, fetch: bool = True) -> CompareResult:
    """Path-scoped, cap-free, cumulative diff via local git (plan S4.2 step 4 / ``--local-git``).

    Used both as the ``--local-git`` differ AND as the automatic fallback when the remote
    ``gh compare`` hits the 300-file cap (subdir packages in a large repo). It path-scopes
    at the git level (no cap) and computes each in-scope .py verdict from the base-vs-HEAD
    CODE lines (``substantive_between``), which discounts the docstring/comment notes-rename
    class precisely. Requires a checkout with the base tag present; a fresh ``git fetch``
    keeps ``origin/<head>`` authoritative (staleness-immune, F-6)."""
    if fetch:
        _git_text(repo_dir, "fetch", "--tags", "--quiet", "origin")
    rng = f"{base}..origin/{head}"
    pathspecs = ([sp.rstrip("/") for sp in entry.ship_paths] + [entry.pyproject_rel]) if entry.ship_paths else [entry.pyproject_rel]
    names = _git_text(repo_dir, "diff", "--name-status", rng, "--", *pathspecs)
    if names is None:
        return CompareResult(files=[], commits=[], ok=False, error=f"local diff {rng} failed (missing tag or checkout at {repo_dir})")
    files: list = []
    for line in names.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, fn = parts[0], parts[-1]
        if not in_scope(fn, entry):
            continue
        if fn == entry.pyproject_rel:
            files.append(FileChange(filename=fn, status=status, patch=_git_text(repo_dir, "diff", rng, "--", fn), cumulative=True))
        elif fn.endswith((".py", ".pyi")):
            st = status[:1]
            if st in ("A", "D", "R", "C"):  # add/delete/rename/copy of a module is inherently substantive
                sub: "bool | None" = True
            else:
                sub = substantive_between(_git_text(repo_dir, "show", f"{base}:{fn}"), _git_text(repo_dir, "show", f"origin/{head}:{fn}"))
            files.append(FileChange(filename=fn, status=status, patch=None, cumulative=False, substantive=sub))
        else:
            files.append(FileChange(filename=fn, status=status, patch=None, cumulative=False))
    msgs = (_git_text(repo_dir, "log", "--format=%s", rng, "--", *pathspecs) or "").splitlines()
    return CompareResult(files=files, commits=[m for m in msgs if m.strip()], truncated=False, ok=True)


def make_live_sources(owner: str, repo_root: Path, ecosystem_root: Path) -> Sources:
    tag_cache: dict[str, list] = {}
    rel_cache: dict[str, set] = {}

    def pypi_json(name: str) -> "dict | None":
        return _http_get_json(PYPI_JSON_URL.format(name=name))

    def list_tags(repo: str) -> list:
        if repo not in tag_cache:
            tag_cache[repo] = _gh_lines(["--paginate", f"repos/{owner}/{repo}/tags?per_page=100", "--jq", ".[].name"]) or []
        return tag_cache[repo]

    def list_releases(repo: str) -> set:
        if repo not in rel_cache:
            # ``_gh_lines`` returns None on gh 404 / Not Found. Coercing that to ``set()``
            # via ``or []`` made ``diff_base_tag not in releases`` always True → false
            # TAG_ONLY for every package when the Releases API is unavailable (auth gap,
            # renamed repo, transient Not Found). Raise so classify_package sets
            # tag_only=None ("unavailable"), matching make_local_git_sources (#773).
            lines = _gh_lines(["--paginate", f"repos/{owner}/{repo}/releases?per_page=100", "--jq", ".[].tag_name"])
            if lines is None:
                raise SourceError(f"releases unavailable (gh 404/Not Found) for {repo}; cannot evaluate TAG_ONLY")
            rel_cache[repo] = set(lines)
        return rel_cache[repo]

    def compare(entry: PackageEntry, base: str, head: str) -> CompareResult:
        payload = _gh_json_single(f"repos/{owner}/{entry.repo}/compare/{base}...{head}")
        if payload is None:
            return CompareResult(files=[], commits=[], ok=False, error=f"compare {base}...{head} not found")
        files = [FileChange(filename=f.get("filename", ""), status=f.get("status", ""), patch=f.get("patch")) for f in payload.get("files", []) or []]
        commits = [(c.get("commit", {}) or {}).get("message", "").splitlines()[0] if (c.get("commit", {}) or {}).get("message") else "" for c in payload.get("commits", []) or []]
        if len(files) >= 300:  # GitHub caps the compare files array at 300 -> path-scope precisely via local git (cap-free)
            comp = local_git_compare(entry, base, head, base_dir_for(entry, repo_root, ecosystem_root))
            if comp.ok and commits:  # keep the remote commit messages for the SemVer signal
                comp.commits = commits
            return comp
        return CompareResult(files=files, commits=commits, truncated=False, ok=True)

    def read_file(entry: PackageEntry, filename: str) -> "str | None":
        target = base_dir_for(entry, repo_root, ecosystem_root) / filename
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    return Sources(pypi_json=pypi_json, list_tags=list_tags, list_releases=list_releases, compare=compare, read_file=read_file)


def make_local_git_sources(owner: str, repo_root: Path, ecosystem_root: Path) -> Sources:
    """Offline fallback (--local-git): PyPI still via HTTP, but tags/diff via local git.

    Uses a fresh ``git fetch`` then ``git log/diff <tag>..origin/main`` (plan S4.2 step 4).
    Releases are unknown offline, so TAG_ONLY hygiene is reported as unavailable.
    """

    def _repo_dir(repo: str) -> Path:
        return repo_root if repo == META_REPO else (ecosystem_root / repo)

    def pypi_json(name: str) -> "dict | None":
        return _http_get_json(PYPI_JSON_URL.format(name=name))

    def list_tags(repo: str) -> list:
        _git_text(_repo_dir(repo), "fetch", "--tags", "--quiet", "origin")
        out = _git_text(_repo_dir(repo), "tag", "--list") or ""
        return [t for t in out.splitlines() if t.strip()]

    def list_releases(repo: str) -> set:
        # Must raise (not return set()): an empty set makes
        # ``diff_base_tag not in releases`` always True → false TAG_ONLY for every
        # package under --local-git. classify_package catches SourceError and sets
        # tag_only=None ("unavailable"), matching this docstring.
        raise SourceError(f"releases unknown offline (--local-git); cannot evaluate TAG_ONLY for {repo}")

    def compare(entry: PackageEntry, base: str, head: str) -> CompareResult:
        return local_git_compare(entry, base, head, _repo_dir(entry.repo))

    def read_file(entry: PackageEntry, filename: str) -> "str | None":
        target = base_dir_for(entry, repo_root, ecosystem_root) / filename
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    return Sources(pypi_json=pypi_json, list_tags=list_tags, list_releases=list_releases, compare=compare, read_file=read_file)


# ── declared-version reading (static pyproject / dynamic _version.py) ─────────


def _read_static_version(pyproject: Path) -> "str | None":
    if tomllib is not None:
        try:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
            ver = data.get("project", {}).get("version")
            if isinstance(ver, str):
                return ver
        except (OSError, ValueError):
            return None
        return None
    try:
        for line in pyproject.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r'^\s*version\s*=\s*"([^"]+)"\s*$', line)
            if m:
                return m.group(1)
    except OSError:
        return None
    return None


def _read_dynamic_version(pkg_dir: Path, import_package: str) -> "str | None":
    candidates = [pkg_dir / import_package / "_version.py"]
    candidates.extend(sorted(pkg_dir.glob("*/_version.py")))
    for vp in candidates:
        try:
            text = vp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        if m:
            return m.group(1)
    return None


def read_declared_version(entry: PackageEntry, repo_root: Path, ecosystem_root: Path) -> "str | None":
    base = base_dir_for(entry, repo_root, ecosystem_root)
    pkg_dir = (base / entry.path).resolve() if entry.path != "." else base
    if entry.version_source == "dynamic":
        return _read_dynamic_version(pkg_dir, entry.import_package)
    return _read_static_version(pkg_dir / "pyproject.toml")


# ── diff-base tag resolution ─────────────────────────────────────────────────


def tag_version(tag: str, tag_pattern: str) -> "str | None":
    prefix = tag_pattern[:-1] if tag_pattern.endswith("*") else tag_pattern
    if not tag.startswith(prefix):
        return None
    rest = tag[len(prefix):]
    # A bare release triple (allow pre/post/dev suffixes); reject nested '-vX' of a sibling pkg.
    if re.match(r"^[0-9][0-9A-Za-z.\-+]*$", rest):
        return rest
    return None


def resolve_diff_base_tag(tags: list, tag_pattern: str, released_version: str) -> "str | None":
    matches: list[tuple[str, str]] = []
    for t in tags:
        ver = tag_version(t, tag_pattern)
        if ver is not None:
            matches.append((t, ver))
    if not matches:
        return None
    # Prefer the tag whose stripped version == the released version (plan S7.3).
    for t, ver in matches:
        if ver == released_version:
            return t
    # else the newest by version.
    matches.sort(key=lambda tv: _vtuple(tv[1]))
    return matches[-1][0]


# ── SHIP vs NON-SHIP filter (the correctness crux) ───────────────────────────


def code_line_numbers(text: str) -> "set[int] | None":
    """Line numbers carrying a real (non-comment, non-string) Python token.

    Returns None when the text cannot be tokenized (caller falls back to a
    patch-only heuristic rather than mis-discounting)."""
    skip = {tokenize.COMMENT, tokenize.STRING, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER}
    for name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):  # py>=3.12 f-string container tokens
        if hasattr(tokenize, name):
            skip.add(getattr(tokenize, name))
    code: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in skip:
                continue
            code.add(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return None
    return code


def added_line_numbers(patch: str) -> set[int]:
    """New-side line numbers of added ('+') lines."""
    nums: set[int] = set()
    new_ln = 0
    for line in patch.splitlines():
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_ln = int(m.group(1)) if m else 0
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            nums.add(new_ln)
            new_ln += 1
        elif line.startswith("-"):
            continue
        elif line.startswith(" "):
            new_ln += 1
    return nums


def _changed_lines(patch: str) -> list:
    """(marker, content) for every +/- body line (excluding file headers)."""
    out = []
    for line in patch.splitlines():
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@") or line.startswith("diff "):
            continue
        if line[:1] in ("+", "-"):
            out.append((line[0], line[1:]))
    return out


def _removed_codeish(patch: str) -> bool:
    for marker, content in _changed_lines(patch):
        if marker != "-":
            continue
        s = content.strip()
        if s and not s.startswith("#"):
            return True
    return False


def _patch_only_substantive(patch: str) -> bool:
    """No-file fallback: best-effort docstring/comment discounting over the new side."""
    in_doc = False
    delim = ""
    for line in patch.splitlines():
        if line.startswith("@@"):
            in_doc, delim = False, ""  # reset per hunk (opener may be out of view)
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        marker = line[:1]
        if marker not in ("+", " "):
            continue  # new-side reconstruction: context + additions
        content = line[1:]
        stripped = content.strip()
        substantive = bool(stripped) and not stripped.startswith("#") and not in_doc
        # toggle triple-quote docstring state on this line
        for d in ('"""', "'''"):
            cnt = content.count(d)
            if cnt:
                if in_doc and delim == d:
                    in_doc = (cnt % 2 == 0)
                elif not in_doc:
                    in_doc, delim = (cnt % 2 == 1), d
                break
        if marker == "+" and substantive:
            return True
    return False


def code_lines_text(text: str) -> "list[str] | None":
    """Sorted multiset of source lines that carry a real (non-comment, non-string)
    Python token, with any trailing inline comment stripped (so a notes-rename inside a
    ``# comment`` on a code line is not counted as a code change). None when the text
    cannot be tokenized. Docstrings and standalone comments contribute no code line."""
    skip = {tokenize.COMMENT, tokenize.STRING, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER}
    for name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
        if hasattr(tokenize, name):
            skip.add(getattr(tokenize, name))
    code_lines: set[int] = set()
    comment_col: dict[int, int] = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                ln, col = tok.start
                comment_col[ln] = min(comment_col.get(ln, col), col)
            elif tok.type not in skip:
                code_lines.add(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return None
    lines = text.splitlines()
    out = []
    for ln in code_lines:
        raw = lines[ln - 1] if 1 <= ln <= len(lines) else ""
        if ln in comment_col:
            raw = raw[: comment_col[ln]]
        out.append(raw.strip())
    return sorted(out)


def substantive_between(base_text: "str | None", head_text: "str | None") -> "bool | None":
    """Alignment-free substantive test: True when the set of CODE lines differs between
    two revisions of a file. A docstring / comment / link-only edit (the 2026-07-04
    notes-rename class) leaves the code lines identical => False (discount); a real code
    line change (incl. a default-argument value or a ruff ``strict=`` reformat) => True.
    None when either revision cannot be read/tokenized (=> SHIP_UNCERTAIN). Used by the
    path-scoped fallback where per-commit patch line numbers do not align with HEAD."""
    if base_text is None or head_text is None:
        return None
    base_code = code_lines_text(base_text)
    head_code = code_lines_text(head_text)
    if base_code is None or head_code is None:
        return None
    return base_code != head_code


def has_substantive_hunk(patch: "str | None", file_text: "str | None") -> "bool | None":
    """True = a real code hunk (SHIP); False = comment/docstring/link-only (discount);
    None = patch unavailable (SHIP_UNCERTAIN)."""
    if patch is None:
        return None
    changed = [(m, c) for (m, c) in _changed_lines(patch) if c.strip()]
    if not changed:
        return False  # whitespace-only
    if all(c.strip().startswith("#") for (_m, c) in changed):
        return False  # pure comment edit (the cascor-model / notes-rename comment class)
    if file_text is not None:
        code = code_line_numbers(file_text)
        if code is not None:
            added = added_line_numbers(patch)
            if added:
                # modification/addition: substantive iff any added line lands on real code
                return any(ln in code for ln in added)
            return _removed_codeish(patch)  # pure deletion
    return _patch_only_substantive(patch)


def _is_test_path(fn: str) -> bool:
    parts = fn.split("/")
    if "tests" in parts or "test" in parts:
        return True
    base = parts[-1]
    return base == "conftest.py" or base.startswith("test_") or base.endswith("_test.py")


def classify_pyproject_patch(patch: "str | None") -> tuple:
    """Classify a pyproject.toml change: SHIP for runtime deps/version/non-test extras;
    NON-SHIP for [tool.*] / pytest config / test-or-dev extras (audit S7.5)."""
    if patch is None:
        return ("uncertain", "pyproject patch unavailable")
    section = None
    extra = None
    found_ship = False
    found_nonship = False
    for raw in patch.splitlines():
        if raw.startswith("@@"):
            trailer = raw.split("@@")[-1].strip() if "@@" in raw else ""
            sm = re.match(r"\[([^\]]+)\]", trailer)
            if sm:
                section, extra = sm.group(1), None
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        marker = raw[:1]
        if marker not in ("+", "-", " "):
            continue
        content = raw[1:]
        stripped = content.strip()
        hm = re.match(r"\[([^\]]+)\]\s*$", stripped)
        if hm:
            section, extra = hm.group(1), None
            continue
        if section and section.endswith("optional-dependencies"):
            em = re.match(r"([A-Za-z0-9_.-]+)\s*=\s*\[?", stripped)
            if em:
                extra = em.group(1).lower()
        if marker not in ("+", "-"):
            continue
        if not stripped or stripped.startswith("#"):
            continue
        sec = (section or "").lower()
        if sec.startswith("project"):
            if section.endswith("optional-dependencies") and extra in TEST_EXTRAS:
                found_nonship = True
            else:
                found_ship = True
        elif sec.startswith("build-system"):
            found_ship = True
        else:
            found_nonship = True
    if found_ship:
        return ("ship", "pyproject runtime/deps/version/extras")
    if found_nonship:
        return ("nonship", "pyproject tooling/test-config/test-extra only")
    return ("nonship", "pyproject no decisive change")


def in_scope(fn: str, entry: PackageEntry) -> bool:
    for excl in entry.exclude_paths:
        if fn == excl.rstrip("/") or fn.startswith(excl):
            return False
    if fn == entry.pyproject_rel:
        return True
    for sp in entry.ship_paths:
        if fn == sp.rstrip("/") or fn.startswith(sp):
            return True
    return False


def classify_change(fc: FileChange, entry: PackageEntry, file_text: "str | None") -> tuple:
    """-> (kind, reason) with kind in {'ship','nonship','uncertain'}."""
    fn = fc.filename
    if fn == entry.pyproject_rel:
        return classify_pyproject_patch(fc.patch)
    if _is_test_path(fn):
        return ("nonship", "tests")
    base = fn.split("/")[-1]
    if base in NONSHIP_BASENAMES or fn.endswith(".md"):
        return ("nonship", "docs/meta")
    if "/notes/" in f"/{fn}" or "/docs/" in f"/{fn}":
        return ("nonship", "notes/docs")
    if fn.endswith((".py", ".pyi")):
        if fc.substantive is not None:  # pre-computed base-vs-head verdict (fallback path)
            return ("ship", "substantive code-line change") if fc.substantive else ("nonship", "comment/docstring/link-only (code lines unchanged)")
        sub = has_substantive_hunk(fc.patch, file_text)
        if sub is None:
            return ("uncertain", "patch-unavailable")
        return ("ship", "substantive code hunk") if sub else ("nonship", "comment/docstring/link-only")
    return ("nonship", "non-python file")


# ── CHANGELOG [Unreleased] corroboration ─────────────────────────────────────


def read_changelog_unreleased(entry: PackageEntry, repo_root: Path, ecosystem_root: Path, read_file: Callable) -> list:
    rel = os.path.normpath(os.path.join(entry.path, "CHANGELOG.md")).replace(os.sep, "/")
    text = read_file(entry, rel)
    if not text:
        return []
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s*\[?unreleased\]?", line.strip(), re.IGNORECASE):
            start = i + 1
            break
    if start is None:
        return []
    categories: list[str] = []
    cur = None
    cur_has = False
    for line in lines[start:]:
        if re.match(r"^##\s", line) and not re.match(r"^###", line):
            break  # next version section
        hm = re.match(r"^###\s+([A-Za-z]+)", line.strip())
        if hm:
            if cur and cur_has and cur not in categories:
                categories.append(cur)
            cur, cur_has = hm.group(1).lower(), False
            continue
        if cur and line.strip().startswith(("-", "*")) and line.strip("-* ").strip():
            cur_has = True
    if cur and cur_has and cur not in categories:
        categories.append(cur)
    return categories


def commit_classes(messages: list) -> set:
    classes: set = set()
    for msg in messages:
        m = re.match(r"^([a-z]+)(\([^)]*\))?(!)?:", msg.strip(), re.IGNORECASE)
        if m:
            typ = m.group(1).lower()
            if typ in ("feat", "feature"):
                classes.add("feat")
            elif typ in ("fix", "bugfix"):
                classes.add("fix")
            if m.group(3) == "!":
                classes.add("breaking")
        if "BREAKING CHANGE" in msg:
            classes.add("breaking")
    return classes


def propose_semver(released: str, categories: list, classes: set) -> tuple:
    cats = {c.lower() for c in categories}
    breaking = bool(cats & BREAKING_CATEGORIES) or ("breaking" in classes)
    feature = bool(cats & FEATURE_CATEGORIES) or ("feat" in classes)
    fix = bool(cats & FIX_CATEGORIES) or ("fix" in classes)
    if breaking or feature:  # pre-1.0: breaking OR feature => MINOR (plan S6)
        bump = "minor"
    elif fix:
        bump = "patch"
    else:
        bump = "none"
    return bump, bump_version(released, bump)


def changelog_conflict(classification: str, categories: list) -> "str | None":
    cats = {c.lower() for c in categories}
    release_worthy_cats = cats & (FEATURE_CATEGORIES | FIX_CATEGORIES | BREAKING_CATEGORIES)
    if classification == UP_TO_DATE and release_worthy_cats:
        return f"UP_TO_DATE but CHANGELOG [Unreleased] lists {sorted(release_worthy_cats)} (review)"
    if classification == UNRELEASED_CHANGES and not release_worthy_cats:
        return "UNRELEASED_CHANGES but CHANGELOG [Unreleased] has no feature/fix/security bullets (under-documented)"
    return None


# ── per-package classification ───────────────────────────────────────────────


@dataclass
class PackageRecord:
    entry: PackageEntry
    released_version: "str | None" = None
    released_upload: "str | None" = None
    declared_version: "str | None" = None
    diff_base_tag: "str | None" = None
    classification: str = UP_TO_DATE
    proposed_bump: str = "none"
    proposed_version: "str | None" = None
    ship_evidence: list = field(default_factory=list)
    nonship_discounted: list = field(default_factory=list)
    ship_uncertain: list = field(default_factory=list)
    changelog_categories: list = field(default_factory=list)
    changelog_conflict: "str | None" = None
    hygiene: dict = field(default_factory=lambda: {"tag_only": None, "notes_missing": None})
    propagation_edges: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def to_manifest(self) -> dict:
        return {
            "pypi_name": self.entry.pypi_name,
            "repo": self.entry.repo,
            "released_version": self.released_version,
            "released_upload": self.released_upload,
            "declared_version": self.declared_version,
            "diff_base_tag": self.diff_base_tag,
            "classification": self.classification,
            "proposed_bump": self.proposed_bump,
            "proposed_version": self.proposed_version,
            "ship_evidence": self.ship_evidence,
            "nonship_discounted": self.nonship_discounted,
            "ship_uncertain": self.ship_uncertain,
            "changelog_unreleased_categories": self.changelog_categories,
            "changelog_conflict": self.changelog_conflict,
            "hygiene": self.hygiene,
            "propagation_edges": self.propagation_edges,
            "notes": self.notes,
        }


def _upload_time(pypi: dict) -> "str | None":
    version = pypi.get("info", {}).get("version")
    files = pypi.get("releases", {}).get(version, []) if version else []
    times = [f.get("upload_time_iso_8601") for f in files if f.get("upload_time_iso_8601")]
    return min(times) if times else None


def notes_missing(entry: PackageEntry, released: str, repo_root: Path) -> bool:
    """True when no central juniper-ml/notes/releases/ archive exists for this version."""
    archive = entry.archive_name.format(version=released)
    return not (repo_root / "notes" / "releases" / archive).is_file()


def classify_package(entry: PackageEntry, sources: Sources, repo_root: Path, ecosystem_root: Path) -> PackageRecord:
    rec = PackageRecord(entry=entry)
    rec.declared_version = read_declared_version(entry, repo_root, ecosystem_root)

    pypi = sources.pypi_json(entry.pypi_name)
    if pypi is None or not pypi.get("info", {}).get("version"):
        rec.classification = NEVER_RELEASED
        if rec.declared_version:
            rec.proposed_bump, rec.proposed_version = "minor", rec.declared_version
        rec.notes.append("not present on PyPI (first publish requires a trusted-publisher precheck)")
        return rec
    rec.released_version = pypi["info"]["version"]
    rec.released_upload = _upload_time(pypi)

    if rec.declared_version is None:
        rec.classification = SHIP_UNCERTAIN
        rec.notes.append("could not read declared version from the checkout")
        return rec

    cmp_declared = version_cmp(rec.declared_version, rec.released_version)
    if cmp_declared > 0:
        rec.classification = BUMPED_NOT_RELEASED
        rec.notes.append(f"declared {rec.declared_version} > released {rec.released_version}: ready for the ceremony (no Release cut yet)")
        return rec
    if cmp_declared < 0:
        rec.classification = ANOMALY
        rec.notes.append(f"declared {rec.declared_version} < released {rec.released_version}: yanked/rolled-back anomaly -- HALT for human review")
        return rec

    # declared == released: look for release-worthy commits since the matching tag.
    tags = sources.list_tags(entry.repo)
    rec.diff_base_tag = resolve_diff_base_tag(tags, entry.tag_pattern, rec.released_version)
    if rec.diff_base_tag is None:
        rec.classification = SHIP_UNCERTAIN
        rec.notes.append(f"no tag under '{entry.tag_pattern}' matches released {rec.released_version}")
        return rec

    comp = sources.compare(entry, rec.diff_base_tag, "main")
    if not comp.ok:
        rec.classification = SHIP_UNCERTAIN
        rec.notes.append(comp.error or "compare unavailable")
        return rec

    # A file may appear across multiple commits (path-scoped fallback); resolve each
    # filename to its STRONGEST verdict (ship > uncertain > nonship) so a substantive
    # change in any commit wins over a comment-only one (the meta pyproject case).
    rank = {"ship": 3, "uncertain": 2, "nonship": 1}
    verdicts: dict = {}
    for fc in comp.files:
        if not in_scope(fc.filename, entry):
            continue
        # Only trust the HEAD-tokenize substantive check for CUMULATIVE tag..HEAD patches
        # (their line numbers align with the on-disk HEAD file); per-commit patches use patch-only.
        file_text = sources.read_file(entry, fc.filename) if (fc.filename.endswith((".py", ".pyi")) and fc.cumulative) else None
        kind, reason = classify_change(fc, entry, file_text)
        prev = verdicts.get(fc.filename)
        if prev is None or rank[kind] > rank[prev[0]]:
            verdicts[fc.filename] = (kind, reason)
    for fn, (kind, reason) in verdicts.items():
        item = {"file": fn, "reason": reason}
        if kind == "ship":
            rec.ship_evidence.append(item)
        elif kind == "uncertain":
            rec.ship_uncertain.append(item)
        else:
            rec.nonship_discounted.append(item)

    if rec.ship_evidence:
        rec.classification = UNRELEASED_CHANGES
    elif rec.ship_uncertain or comp.truncated:
        rec.classification = SHIP_UNCERTAIN
        if comp.truncated and not rec.ship_uncertain:
            rec.notes.append("compare diff hit the 300-file cap with no ship evidence in view; page or re-run (--local-git)")
    else:
        rec.classification = UP_TO_DATE

    rec.changelog_categories = read_changelog_unreleased(entry, repo_root, ecosystem_root, sources.read_file)
    rec.changelog_conflict = changelog_conflict(rec.classification, rec.changelog_categories)
    if rec.classification in (UNRELEASED_CHANGES, SHIP_UNCERTAIN):
        rec.proposed_bump, rec.proposed_version = propose_semver(rec.released_version, rec.changelog_categories, commit_classes(comp.commits))

    try:
        rec.hygiene = {
            "tag_only": (rec.diff_base_tag not in sources.list_releases(entry.repo)),
            "notes_missing": notes_missing(entry, rec.released_version, repo_root),
        }
    except SourceError as exc:
        rec.hygiene = {"tag_only": None, "notes_missing": notes_missing(entry, rec.released_version, repo_root)}
        rec.notes.append(f"release-hygiene (tag_only) unavailable: {exc}")
    return rec


# ── reporting ────────────────────────────────────────────────────────────────


def print_table(records: list) -> None:
    print("Juniper PyPI release-train -- report-only detection")
    print()
    print(f"  {'PACKAGE':<27} {'RELEASED':<9} {'DECLARED':<9} {'CLASSIFICATION':<20} {'BUMP':<6} SHIP/UNCERTAIN/DISCOUNTED")
    print(f"  {'-' * 27} {'-' * 9} {'-' * 9} {'-' * 20} {'-' * 6} {'-' * 28}")
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.classification] = counts.get(rec.classification, 0) + 1
        counts_str = f"{len(rec.ship_evidence)}/{len(rec.ship_uncertain)}/{len(rec.nonship_discounted)}"
        print(f"  {rec.entry.pypi_name:<27} {(rec.released_version or '-'):<9} {(rec.declared_version or '-'):<9} {rec.classification:<20} {rec.proposed_bump:<6} {counts_str}")
        if rec.changelog_conflict:
            print(f"      ! changelog: {rec.changelog_conflict}")
        for note in rec.notes:
            print(f"      - {note}")
    print()
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    hyg_tag = sum(1 for r in records if r.hygiene.get("tag_only"))
    hyg_notes = sum(1 for r in records if r.hygiene.get("notes_missing"))
    print(f"  {len(records)} packages: {summary}")
    print(f"  hygiene: TAG_ONLY={hyg_tag}, NOTES_MISSING={hyg_notes}")


def build_manifest(records: list) -> dict:
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.classification] = counts.get(rec.classification, 0) + 1
    return {
        "schema": "juniper-release-train/manifest/v1",
        "generated_by": "util/release_train/detect.py",
        "summary": {"total": len(records), "by_classification": counts},
        "packages": [rec.to_manifest() for rec in records],
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="release_train/detect.py", description="Report-only: classify each Juniper package as needing a PyPI deploy or not (plan S4.2/S4.3).")
    default_repo_root = Path(__file__).resolve().parents[2]
    p.add_argument("--repo-root", default=str(default_repo_root), help="juniper-ml checkout root (in-repo package version reads + central notes/releases/)")
    p.add_argument("--ecosystem-root", default=None, help="parent dir holding sibling repos (default: --repo-root's parent)")
    p.add_argument("--owner", default=DEFAULT_OWNER, help=f"GitHub owner (default: {DEFAULT_OWNER})")
    p.add_argument("--registry", default=None, help="path to registry.yaml (default: alongside detect.py)")
    p.add_argument("--package", action="append", metavar="PYPI_NAME", help="restrict to these pypi_name(s) (repeatable)")
    p.add_argument("--local-git", action="store_true", help="offline fallback: diff via local git instead of the gh compare API")
    p.add_argument("--json", action="store_true", help="emit the release-manifest JSON instead of the human table")
    return p.parse_args(argv)


def main(argv: "list[str] | None" = None, sources: "Sources | None" = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    ecosystem_root = Path(args.ecosystem_root).resolve() if args.ecosystem_root else repo_root.parent

    try:
        entries = load_registry(args.registry)
    except Exception as exc:  # noqa: BLE001 - a missing/broken registry is an invocation error
        print(f"ERROR: cannot load registry: {exc}", file=sys.stderr)
        return 2
    if not entries:
        print("ERROR: registry is empty", file=sys.stderr)
        return 2
    if args.package:
        wanted = set(args.package)
        entries = [e for e in entries if e.pypi_name in wanted]
        if not entries:
            print(f"ERROR: no registry entry matches --package {sorted(wanted)}", file=sys.stderr)
            return 2

    if sources is None:
        sources = make_local_git_sources(args.owner, repo_root, ecosystem_root) if args.local_git else make_live_sources(args.owner, repo_root, ecosystem_root)

    records = []
    hard_error = False
    for entry in entries:
        try:
            records.append(classify_package(entry, sources, repo_root, ecosystem_root))
        except SourceError as exc:
            rec = PackageRecord(entry=entry, classification=SHIP_UNCERTAIN)
            rec.notes.append(f"source error: {exc}")
            records.append(rec)
            hard_error = True

    if args.json:
        print(json.dumps(build_manifest(records), indent=2))
    else:
        print_table(records)

    if hard_error:
        return 2
    if any(rec.classification in ACTION_CLASSIFICATIONS for rec in records):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
