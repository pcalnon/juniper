#!/usr/bin/env python3
"""Drift detection for juniper editable installs across the conda environments.

A juniper package installed with ``pip install -e <path>`` records its source
path in ``<pkg>.dist-info/direct_url.json`` (PEP 610). When that path is a git
worktree that is later removed, the editable install ORPHANS: ``importlib`` /
``importlib.metadata`` still report the package, but ``import <pkg>`` fails
because the editable finder points at a directory that no longer exists. This
is the recurring failure mode behind on-host environment bit-rot (orphaned
editable installs after worktree cleanup).

This checker reads the ``direct_url.json`` files directly from each
environment's site-packages — it does NOT invoke the environment's interpreter,
so it still works when that interpreter is itself broken (which is exactly when
the drift bites). Each juniper editable install is classified:

  FRESH            target directory exists and is not inside a git worktree
  WORKTREE_PINNED  target exists but lives under a ``worktrees`` path — it will
                   orphan when that worktree is removed (soft warning)
  ORPHANED         target directory is missing — ``import`` is broken (drift)

A second, ORTHOGONAL axis compares the version the install RECORDED at
``pip install -e`` time against the version its source tree declares NOW:

  MATCH            recorded version == the target's declared version
  STALE            they disagree — the metadata is frozen at install time
  UNKNOWN          not comparable (ORPHANED target, or no resolvable version)

Editable installs do NOT re-derive their version when the source moves on: an
editable finder makes ``import`` follow the live tree, but ``*.dist-info/METADATA``
keeps whatever version was declared when pip last ran. So a long-lived env
silently reports a stale version through :mod:`importlib.metadata` while the code
it imports is current. That breaks anything reading the installed version rather
than the source: a repo's own ``version == pyproject`` self-check, and the
build-info/provenance metric a host-launched service exports.

This is a distinct question from ``juniper-env-drift-check`` (juniper-ci-tools),
which asks whether an installed version satisfies a consumer's declared *floor*.
A stale editable can sit comfortably above every floor — 7 of 8 installs on this
host did — and still be wrong. Only an editable install can drift this way, which
is why the check lives here.

With ``--fix`` the tool re-points ORPHANED installs (and, with
``--fix-worktree-pinned``, WORKTREE_PINNED ones) to the canonical source repo
discovered under the ecosystem root — the non-worktree checkout whose
``pyproject.toml`` ``[project].name`` matches — via
``<env>/bin/python -m pip install -e <repo> --no-deps --force-reinstall``.
``--fix-stale`` additionally refreshes STALE installs in place (same pip command,
against the path they already point at, which is what re-stamps the metadata).
``--dry-run`` prints the plan without running pip.

Exit codes
----------
0   No ORPHANED installs (clean, or only soft WORKTREE_PINNED / STALE warnings).
1   At least one ORPHANED install (or, with --strict, any WORKTREE_PINNED; with
    --strict-version, any STALE).
2   Invocation error (no environments found).

Project: juniper-ml
Sub-Project: on-host environment hygiene tooling
Author: Paul Calnon
Created: 2026-06-16
Status: permanent utility (graduates immediately to ``util/``)
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    import tomllib  # Python >= 3.11 (juniper-ml requires >= 3.12)
except ModuleNotFoundError:  # pragma: no cover - regex fallback below
    tomllib = None  # type: ignore[assignment]

DEFAULT_CONDA_DIR = os.environ.get("JUNIPER_CONDA_DIR", "/opt/miniforge3")
DEFAULT_ECOSYSTEM_ROOT = os.environ.get(
    "JUNIPER_ECOSYSTEM_ROOT", "/home/pcalnon/Development/python/Juniper"
)
DEFAULT_ENV_GLOB = "Juniper*"
JUNIPER_PREFIX = "juniper"

STATUS_FRESH = "FRESH"
STATUS_WORKTREE = "WORKTREE_PINNED"
STATUS_ORPHANED = "ORPHANED"

# Version axis — orthogonal to the path axis above (a WORKTREE_PINNED install can
# also be STALE; an ORPHANED one is never comparable).
VERSION_MATCH = "MATCH"
VERSION_STALE = "STALE"
VERSION_UNKNOWN = "UNKNOWN"

# ``__version__ = "1.2.3"`` in a dynamic-version module.
_VERSION_ATTR_RE = re.compile(r"""__version__\s*=\s*["']([^"']+)["']""")

# Directory names never descended into when discovering a package's canonical
# source. ``worktrees`` (centralized) and ``.claude`` (session worktrees live in
# ``.claude/worktrees/``) are excluded so a worktree copy is never treated as
# canonical; the rest are noise that only slows the walk.
_SKIP_DIRS = {
    "worktrees", ".claude", ".git", "backups", "juniper-legacy",
    "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".mypy_cache", ".pytest_cache", "site-packages",
}


@dataclass(frozen=True)
class EditableFinding:
    """Classification of a single juniper editable install in one environment."""

    env: str
    package: str
    target: str
    status: str  # FRESH | WORKTREE_PINNED | ORPHANED
    detail: str
    # Version axis. Defaulted so an external caller constructing the pre-version
    # 5-field form still works.
    installed_version: str | None = None
    source_version: str | None = None
    version_status: str = VERSION_UNKNOWN  # MATCH | STALE | UNKNOWN
    version_detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "env": self.env,
            "package": self.package,
            "target": self.target,
            "status": self.status,
            "detail": self.detail,
            "installed_version": self.installed_version,
            "source_version": self.source_version,
            "version_status": self.version_status,
            "version_detail": self.version_detail,
        }


def normalize(name: str) -> str:
    """PEP 503-ish normalization (enough to compare juniper dist names)."""
    return name.strip().lower().replace("_", "-")


# ── discovery ───────────────────────────────────────────────────────────────


def discover_envs(conda_dir: Path, env_filter: list[str] | None,
                  include_deprecated: bool = False) -> list[Path]:
    envs_root = conda_dir / "envs"
    if not envs_root.is_dir():
        return []
    if env_filter:  # an explicit --env wins, deprecated names included
        wanted = set(env_filter)
        return sorted(d for d in envs_root.iterdir() if d.is_dir() and d.name in wanted)

    def keep(name: str) -> bool:
        if not fnmatch.fnmatch(name, DEFAULT_ENV_GLOB):
            return False
        # *-DEPRECATED envs are intentionally dead; their drift is expected noise.
        return include_deprecated or "DEPRECATED" not in name.upper()

    return sorted(d for d in envs_root.iterdir() if d.is_dir() and keep(d.name))


def site_packages_dirs(env_dir: Path) -> list[Path]:
    # Covers cpython (python3.13) and free-threaded (python3.14t) layouts.
    return sorted(env_dir.glob("lib/python*/site-packages"))


def _read_dist_name(dist_info: Path) -> str | None:
    meta = dist_info / "METADATA"
    if meta.is_file():
        for line in meta.read_text(errors="replace").splitlines():
            if line.startswith("Name:"):
                return line.split(":", 1)[1].strip()
            if line == "":  # end of the RFC-822 header block
                break
    stem = dist_info.name
    if stem.endswith(".dist-info"):
        stem = stem[: -len(".dist-info")]
    return stem.rsplit("-", 1)[0] if "-" in stem else None


def _read_dist_version(dist_info: Path) -> str | None:
    """The version this install RECORDED at pip time (METADATA, dirname fallback)."""
    meta = dist_info / "METADATA"
    if meta.is_file():
        for line in meta.read_text(errors="replace").splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
            if line == "":  # end of the RFC-822 header block
                break
    stem = dist_info.name
    if stem.endswith(".dist-info"):
        stem = stem[: -len(".dist-info")]
    return stem.rsplit("-", 1)[1] if "-" in stem else None


def editable_installs(site_pkgs: Path) -> Iterator[tuple[str, str, str | None]]:
    """Yield (dist_name, target_path, recorded_version) for each editable install."""
    for direct_url in site_pkgs.glob("*.dist-info/direct_url.json"):
        try:
            data = json.loads(direct_url.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or not data.get("dir_info", {}).get("editable"):
            continue
        url = data.get("url", "")
        if not url.startswith("file://"):
            continue
        name = _read_dist_name(direct_url.parent)
        if name:
            yield name, url[len("file://"):], _read_dist_version(direct_url.parent)


def classify(target: str) -> tuple[str, str]:
    path = Path(target)
    inside_worktree = "worktrees" in path.parts
    exists = path.is_dir()
    if inside_worktree:
        if exists:
            return STATUS_WORKTREE, "target exists but is inside a git worktree (re-orphans when removed)"
        return STATUS_ORPHANED, "target worktree no longer exists"
    if not exists:
        return STATUS_ORPHANED, "target directory does not exist"
    return STATUS_FRESH, "stable (non-worktree) checkout"


def _load_pyproject(pyproject: Path) -> dict[str, Any] | None:
    if tomllib is None:  # pragma: no cover - juniper-ml requires >= 3.12
        return None
    try:
        with pyproject.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, ValueError):  # ValueError covers TOMLDecodeError
        return None


def _dynamic_version_file(target: Path, data: dict[str, Any]) -> Path | None:
    """Resolve the module file a dynamic ``version`` declaration points at.

    Only follows an EXPLICIT declaration (setuptools ``attr`` / hatch ``path``);
    it never guesses at a ``_version.py``, so an unrecognized backend reports
    UNKNOWN rather than a version from the wrong file.
    """
    tool = data.get("tool", {})
    attr = tool.get("setuptools", {}).get("dynamic", {}).get("version", {})
    if isinstance(attr, dict) and isinstance(attr.get("attr"), str):
        # "juniper_recurrence._version.__version__" -> juniper_recurrence/_version.py
        dotted = attr["attr"].rsplit(".", 1)[0]
        rel = Path(*dotted.split(".")).with_suffix(".py")
        for base in (target, target / "src"):  # flat and src/ layouts
            if (cand := base / rel).is_file():
                return cand
    path = tool.get("hatch", {}).get("version", {}).get("path")
    if isinstance(path, str) and (cand := target / path).is_file():
        return cand
    return None


def source_version(target: str) -> tuple[str | None, str]:
    """Return (version, detail) that the source tree at ``target`` declares now."""
    root = Path(target)
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None, "no pyproject.toml at target"
    data = _load_pyproject(pyproject)
    if data is None:
        return None, "pyproject.toml unreadable"
    project = data.get("project", {})
    version = project.get("version")
    if isinstance(version, str):
        return version, "static [project].version"
    if "version" in (project.get("dynamic") or []):
        vfile = _dynamic_version_file(root, data)
        if vfile is None:
            return None, "dynamic version declaration not resolvable"
        try:
            match = _VERSION_ATTR_RE.search(vfile.read_text(errors="replace"))
        except OSError:
            return None, f"dynamic version file unreadable ({vfile.name})"
        if match:
            return match.group(1), f"dynamic {vfile.name}"
        return None, f"no __version__ in {vfile.name}"
    return None, "no version declared in pyproject.toml"


def classify_version(installed: str | None, target: str,
                     status: str) -> tuple[str, str | None, str]:
    """Compare an editable install's recorded version to its source tree.

    Returns (version_status, source_version, detail). An ORPHANED target has no
    source to read, so it is UNKNOWN rather than a guess.
    """
    if status == STATUS_ORPHANED:
        return VERSION_UNKNOWN, None, "target missing — not comparable"
    declared, detail = source_version(target)
    if declared is None:
        return VERSION_UNKNOWN, None, detail
    if installed is None:
        return VERSION_UNKNOWN, declared, "recorded version unreadable"
    if installed == declared:
        return VERSION_MATCH, declared, detail
    return VERSION_STALE, declared, f"recorded {installed}, source declares {declared}"


def collect(conda_dir: Path, env_filter: list[str] | None,
            include_deprecated: bool = False) -> list[EditableFinding]:
    findings: list[EditableFinding] = []
    for env_dir in discover_envs(conda_dir, env_filter, include_deprecated):
        seen: set[str] = set()
        for site_pkgs in site_packages_dirs(env_dir):
            for name, target, installed in editable_installs(site_pkgs):
                norm = normalize(name)
                if not norm.startswith(JUNIPER_PREFIX) or norm in seen:
                    continue
                seen.add(norm)
                status, detail = classify(target)
                vstatus, declared, vdetail = classify_version(installed, target, status)
                findings.append(EditableFinding(
                    env_dir.name, norm, target, status, detail,
                    installed_version=installed, source_version=declared,
                    version_status=vstatus, version_detail=vdetail,
                ))
    findings.sort(key=lambda f: (f.env, f.package))
    return findings


# ── canonical-source discovery (for --fix) ──────────────────────────────────


def _pyproject_name(pyproject: Path) -> str | None:
    try:
        if tomllib is not None:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
            name = data.get("project", {}).get("name")
            if isinstance(name, str):
                return name
        for line in pyproject.read_text(errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("name") and "=" in stripped:
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def _walk_pyprojects(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        if "pyproject.toml" in filenames:
            yield Path(dirpath) / "pyproject.toml"


def discover_canonical(pkg_name: str, ecosystem_root: Path) -> tuple[Path | None, list[Path]]:
    """Return (unique_canonical_dir_or_None, all_candidate_dirs) for pkg_name."""
    want = normalize(pkg_name)
    candidates = sorted({
        py.parent for py in _walk_pyprojects(ecosystem_root)
        if (n := _pyproject_name(py)) and normalize(n) == want
    })
    return (candidates[0] if len(candidates) == 1 else None), candidates


def env_python(conda_dir: Path, env_name: str) -> Path:
    return conda_dir / "envs" / env_name / "bin" / "python"


def build_fix_plan(findings, ecosystem_root, include_worktree, include_stale=False):
    targets = {STATUS_ORPHANED} | ({STATUS_WORKTREE} if include_worktree else set())
    plan = []
    for finding in findings:
        stale = include_stale and finding.version_status == VERSION_STALE
        if finding.status not in targets and not stale:
            continue
        if finding.status in targets:
            # Path drift: the recorded target is wrong, so resolve the canonical repo.
            canonical, candidates = discover_canonical(finding.package, ecosystem_root)
            reason = "path"
        else:
            # Version-only drift: the path is already right. Reinstalling from the
            # SAME path is exactly what re-stamps the frozen metadata, so resolving
            # a canonical here would risk re-pointing a deliberate checkout.
            canonical, candidates, reason = Path(finding.target), [], "stale-metadata"
        plan.append({
            "env": finding.env,
            "package": finding.package,
            "from": finding.target,
            "canonical": str(canonical) if canonical else None,
            "candidates": [str(c) for c in candidates],
            "resolvable": canonical is not None,
            "drift": reason,
        })
    return plan


def run_fix(plan, conda_dir: Path, dry_run: bool):
    results = []
    for item in plan:
        if not item["resolvable"]:
            reason = ("no canonical source found" if not item["candidates"]
                      else f"ambiguous: {len(item['candidates'])} candidates")
            results.append({**item, "action": "SKIP", "reason": reason})
            continue
        cmd = [str(env_python(conda_dir, item["env"])), "-m", "pip", "install",
               "-e", item["canonical"], "--no-deps", "--force-reinstall", "-q"]
        if dry_run:
            results.append({**item, "action": "DRY_RUN", "cmd": cmd})
            continue
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            results.append({**item, "action": "FIXED", "cmd": cmd})
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            results.append({**item, "action": "ERROR", "cmd": cmd, "error": detail.strip()[:500]})
    return results


# ── reporting ───────────────────────────────────────────────────────────────


def summary(findings) -> dict[str, int]:
    counts = {STATUS_FRESH: 0, STATUS_WORKTREE: 0, STATUS_ORPHANED: 0,
              VERSION_MATCH: 0, VERSION_STALE: 0, VERSION_UNKNOWN: 0}
    for finding in findings:
        counts[finding.status] = counts.get(finding.status, 0) + 1
        counts[finding.version_status] = counts.get(finding.version_status, 0) + 1
    counts["total"] = len(findings)
    return counts


def print_report(findings, fix_results) -> None:
    print("Juniper editable-install drift report")
    print()
    if not findings:
        print("  (no juniper editable installs found)")
    else:
        print(f"  {'ENV':<16} {'PACKAGE':<26} {'STATUS':<16} {'VERSION':<22} TARGET")
        print(f"  {'─' * 16} {'─' * 26} {'─' * 16} {'─' * 22} {'─' * 40}")
        for f in findings:
            if f.version_status == VERSION_STALE:
                version = f"STALE {f.installed_version}->{f.source_version}"
            elif f.version_status == VERSION_MATCH:
                version = f"MATCH {f.installed_version}"
            else:
                version = VERSION_UNKNOWN
            print(f"  {f.env:<16} {f.package:<26} {f.status:<16} {version:<22} {f.target}")
    counts = summary(findings)
    print()
    print(f"  {counts['total']} editable install(s): "
          f"{counts[STATUS_FRESH]} FRESH, {counts[STATUS_WORKTREE]} WORKTREE_PINNED, "
          f"{counts[STATUS_ORPHANED]} ORPHANED")
    print(f"  {'':<19}versions: {counts[VERSION_MATCH]} MATCH, "
          f"{counts[VERSION_STALE]} STALE, {counts[VERSION_UNKNOWN]} UNKNOWN")
    if counts[VERSION_STALE]:
        print("    STALE = metadata frozen at pip time; importlib.metadata reports the "
              "old version. Refresh with --fix --fix-stale.")
    if fix_results:
        print()
        print("  --fix:")
        for r in fix_results:
            line = f"    [{r['action']:<7}] {r['env']}/{r['package']}"
            if r.get("canonical"):
                line += f" -> {r['canonical']}"
            if r.get("reason"):
                line += f"  ({r['reason']})"
            print(line)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    conda_dir = Path(args.conda_dir)
    ecosystem_root = Path(args.ecosystem_root)

    if not discover_envs(conda_dir, args.env, args.include_deprecated):
        print(f"ERROR: no environments found under {conda_dir}/envs "
              f"(filter={args.env or DEFAULT_ENV_GLOB!r})", file=sys.stderr)
        return 2

    findings = collect(conda_dir, args.env, args.include_deprecated)

    fix_results = None
    if args.fix:
        plan = build_fix_plan(findings, ecosystem_root, args.fix_worktree_pinned,
                              args.fix_stale)
        fix_results = run_fix(plan, conda_dir, args.dry_run)
        if not args.dry_run:
            findings = collect(conda_dir, args.env, args.include_deprecated)  # re-scan

    if args.json:
        out: dict[str, Any] = {"findings": [f.as_dict() for f in findings],
                               "summary": summary(findings)}
        if fix_results is not None:
            out["fix"] = fix_results
        print(json.dumps(out, indent=2))
    else:
        print_report(findings, fix_results)

    counts = summary(findings)
    if counts[STATUS_ORPHANED] > 0:
        return 1
    if args.strict and counts[STATUS_WORKTREE] > 0:
        return 1
    if args.strict_version and counts[VERSION_STALE] > 0:
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="editable_install_drift_check.py",
        description=("Detect (and optionally repair) drifted juniper editable installs "
                     "across the Juniper conda environments."),
    )
    p.add_argument("--conda-dir", default=DEFAULT_CONDA_DIR,
                   help=f"conda/miniforge install dir (default: {DEFAULT_CONDA_DIR})")
    p.add_argument("--env", action="append", metavar="NAME",
                   help=f"restrict to this environment (repeatable); default: all "
                        f"matching {DEFAULT_ENV_GLOB!r}")
    p.add_argument("--ecosystem-root", default=DEFAULT_ECOSYSTEM_ROOT,
                   help=f"root for --fix canonical-source discovery "
                        f"(default: {DEFAULT_ECOSYSTEM_ROOT})")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p.add_argument("--include-deprecated", action="store_true",
                   help="also scan *-DEPRECATED environments (skipped by default)")
    p.add_argument("--strict", action="store_true",
                   help="also fail (exit 1) on WORKTREE_PINNED installs")
    p.add_argument("--strict-version", action="store_true",
                   help="also fail (exit 1) on STALE (frozen-metadata) installs")
    p.add_argument("--fix", action="store_true",
                   help="re-point ORPHANED installs to their canonical source repo")
    p.add_argument("--fix-worktree-pinned", action="store_true",
                   help="with --fix, also re-point WORKTREE_PINNED installs")
    p.add_argument("--fix-stale", action="store_true",
                   help="with --fix, also refresh STALE installs in place "
                        "(reinstall from the path they already point at)")
    p.add_argument("--dry-run", action="store_true",
                   help="with --fix, print the pip commands without running them")
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
