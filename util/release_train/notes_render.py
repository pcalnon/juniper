#!/usr/bin/env python3
"""Template-driven release-notes generation for the Juniper PyPI release-train (plan S10.1).

Given a package + version + the CHANGELOG ``[Unreleased]`` bullets, render a well-formed
release-notes DRAFT from ``notes/templates/TEMPLATE_RELEASE_NOTES.md`` (or the security
template when the ``[Unreleased]`` block carries a ``Security`` category, plan S10.1 /
Q-SEVERITY). The draft is what the standard-gated proposal PR (``propose.py``, plan S5.4)
shows the owner; it is **not** archived to ``notes/releases/`` here -- archival is the later
exempt ceremony step (plan S7/S10.2). The central archive filename convention is surfaced
(``archive_name`` / ``archive_relpath``) so the proposal body can name the eventual home.

Design conventions mirror ``detect.py`` (the Phase 1.2 engine): stdlib-only rendering with a
lazy template read, small pure functions the tests drive directly, path-invoked with a
``--repo-root`` seam so it runs fully offline, and exit codes 0/1/2. ``util/`` is not
pre-commit-lint-gated, so ``tests/test_release_train_propose.py`` IS the gate (the
``env_floor_drift_check`` precedent) -- it exercises this module alongside ``propose.py``.

The renderer is deliberately conservative: it fills the metadata block, an Overview, a
Release Summary, and the Keep-a-Changelog change groups sourced from the CHANGELOG, then
lists the remaining template sections as a to-complete scaffold. It never invents test
counts, coverage numbers, or issue IDs -- those are owner-authored during review.

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-14
Status: permanent utility (Phase 2, proposal-PR generation)
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

META_PACKAGE = "juniper-ml"
RELEASES_DIR = "notes/releases"

# util/release_train/notes_render.py -> parents[2] == the juniper-ml checkout root.
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_REL = "notes/templates/TEMPLATE_RELEASE_NOTES.md"
SECURITY_TEMPLATE_REL = "notes/templates/TEMPLATE_SECURITY_RELEASE_NOTES.md"

# Keep-a-Changelog category whose presence flips the release to the security template
# (plan S10.1: "the Security CHANGELOG category is the trigger").
SECURITY_CATEGORY = "security"

# bump -> release-type label (plan S6). "none" is defensive; propose.py never renders it.
_RELEASE_TYPE = {"major": "MAJOR", "minor": "MINOR", "patch": "PATCH", "none": "PATCH"}

# Keep-a-Changelog category -> the one-word "primary focus" phrase for the Release Summary.
_FOCUS = {
    "added": "new features",
    "changed": "behavioural changes",
    "deprecated": "deprecations",
    "removed": "removals",
    "fixed": "bug fixes",
    "security": "security hardening",
}

# Section headings this renderer fills, per template. Kept in template order so the draft
# reads top-to-bottom like the template; a subset of the live template's `## ` titles (the
# test asserts the subset relationship, so a template rename is caught as drift).
STANDARD_FILLED_SECTIONS = ("Overview", "Release Summary", "What's New", "Known Issues", "Links")
SECURITY_FILLED_SECTIONS = ("Security Impact", "Changes in v", "References")


# ── naming ───────────────────────────────────────────────────────────────────


def archive_name(pypi_name: str, version: str) -> str:
    """Central ``notes/releases/`` filename for a package+version (procedure S11.3 / plan S10.2).

    Meta-package -> ``RELEASE_NOTES_v<version>.md``; every other package ->
    ``RELEASE_NOTES_<pkg>_v<version>.md`` (the ``_v`` separator convention)."""
    if pypi_name == META_PACKAGE:
        return f"RELEASE_NOTES_v{version}.md"
    return f"RELEASE_NOTES_{pypi_name}_v{version}.md"


def archive_relpath(pypi_name: str, version: str) -> str:
    """Repo-relative path of the eventual central archive (``notes/releases/<archive_name>``)."""
    return f"{RELEASES_DIR}/{archive_name(pypi_name, version)}"


def release_type(bump: str) -> str:
    return _RELEASE_TYPE.get(bump, "PATCH")


def display_name(pypi_name: str) -> str:
    """Human title stem: the meta-package reads 'Juniper ML'; others use the dist name."""
    return "Juniper ML" if pypi_name == META_PACKAGE else pypi_name


# ── CHANGELOG [Unreleased] parsing (category -> bullets) ─────────────────────


def _split_bullets(body_lines: list) -> list:
    """Group a category body's lines into top-level bullets (marker-stripped, continuations
    folded in). A new bullet starts at a line whose stripped text begins with ``-`` or ``*``;
    indented / continuation lines join the current bullet."""
    bullets: list = []
    current: "list[str]" = []
    for raw in body_lines:
        stripped = raw.strip()
        is_marker = stripped.startswith(("- ", "* ")) or stripped in ("-", "*")
        indent = len(raw) - len(raw.lstrip())
        if is_marker and indent == 0:
            if current:
                bullets.append("\n".join(current).rstrip())
            current = [stripped[1:].strip()]
        elif current:
            current.append(raw.rstrip())
        # a non-marker line before any bullet (stray prose) is ignored for the bullet list
    if current:
        bullets.append("\n".join(current).rstrip())
    return [b for b in bullets if b.strip()]


def parse_unreleased(changelog_text: str) -> "OrderedDict[str, list]":
    """Parse the ``## [Unreleased]`` block into ``{Category: [bullets]}`` preserving the
    template's Keep-a-Changelog order and the original category casing (``Added`` / ``Fixed``).

    Categories with no bullets are omitted (matching ``detect.read_changelog_unreleased``)."""
    result: "OrderedDict[str, list]" = OrderedDict()
    if not changelog_text:
        return result
    lines = changelog_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s*\[?unreleased\]?", line.strip(), re.IGNORECASE):
            start = i + 1
            break
    if start is None:
        return result
    current_cat: "str | None" = None
    body: "list[str]" = []
    for line in lines[start:]:
        if re.match(r"^##\s", line) and not re.match(r"^###", line):
            break  # next version section ends [Unreleased]
        hm = re.match(r"^###\s+([A-Za-z]+)", line.strip())
        if hm:
            if current_cat is not None:
                bullets = _split_bullets(body)
                if bullets:
                    result[current_cat] = bullets
            current_cat = hm.group(1)
            body = []
            continue
        if current_cat is not None:
            body.append(line)
    if current_cat is not None:
        bullets = _split_bullets(body)
        if bullets:
            result[current_cat] = bullets
    return result


def is_security_release(sections: "OrderedDict[str, list] | dict | list | None") -> bool:
    """True when a ``Security`` Keep-a-Changelog category is present (plan S10.1 trigger)."""
    if not sections:
        return False
    keys = sections.keys() if hasattr(sections, "keys") else sections
    return any(str(k).lower() == SECURITY_CATEGORY for k in keys)


# ── template access ──────────────────────────────────────────────────────────


def template_path(is_security: bool, repo_root: "Path | None" = None) -> Path:
    root = Path(repo_root) if repo_root else DEFAULT_REPO_ROOT
    return root / (SECURITY_TEMPLATE_REL if is_security else TEMPLATE_REL)


def read_template(is_security: bool, repo_root: "Path | None" = None) -> str:
    return template_path(is_security, repo_root).read_text(encoding="utf-8")


def template_section_titles(template_text: str) -> list:
    """Ordered list of the template's ``## `` section titles (the skeleton), excluding ``###``.

    The tests assert the renderer's filled headings are a subset of these, so a template
    section rename surfaces as a drift failure instead of a silently wrong draft."""
    titles: list = []
    for line in template_text.splitlines():
        m = re.match(r"^##\s+(?!#)(.*\S)\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    return titles


# ── rendering ────────────────────────────────────────────────────────────────


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _render_change_groups(sections: "OrderedDict[str, list]") -> list:
    out: list = []
    for category, bullets in sections.items():
        out.append(f"### {category}")
        out.append("")
        for bullet in bullets:
            first, *rest = bullet.splitlines() or [""]
            out.append(f"- {first}")
            out.extend(rest)  # continuation lines keep their indentation
        out.append("")
    return out


def _is_filled(title: str, filled: tuple) -> bool:
    """A template title counts as filled when one of the filled-section keys is a
    case-insensitive prefix of it (so 'Security Impact' matches 'Security Impact ([SEVERITY])')."""
    low = title.lower()
    return any(low.startswith(key.lower()) for key in filled)


def _remaining_sections_comment(template_text: str, filled: tuple, repo_root: "Path | None") -> list:
    titles = template_section_titles(template_text)
    remaining = [t for t in titles if not _is_filled(t, filled)]
    rel = SECURITY_TEMPLATE_REL if "Security Impact" in filled else TEMPLATE_REL
    lines = [
        "<!-- Auto-generated release-train DRAFT (util/release_train/notes_render.py).",
        f"     Source template: {rel}.",
        "     Complete or delete these template sections before the release ceremony:",
    ]
    for title in remaining:
        lines.append(f"       - {title}")
    lines.append("-->")
    return lines


def _render_standard(pypi_name: str, version: str, bump: str, date: str, sections: "OrderedDict[str, list]", template_text: str, repo_root: "Path | None", changelog_url: "str | None" = None, final: bool = False) -> str:
    rtype = release_type(bump)
    breaking = "YES" if ("removed" in {k.lower() for k in sections}) else "NO"
    focus = ", ".join(dict.fromkeys(_FOCUS.get(k.lower(), k.lower()) for k in sections)) or "maintenance"
    name = display_name(pypi_name)
    lines: list = [
        f"# {name} v{version} Release Notes",
        "",
        f"**Release Date:** {date}",
        f"**Version:** {version}",
        f"**Release Type:** {rtype}",
        "",
        "---",
        "",
        "## Overview",
        "",
        f"`{pypi_name}` v{version} rolls up the release-worthy changes accumulated on `main` since the last "
        f"published release, generated by the Juniper release-train from this package's CHANGELOG.",
        "",
        "---",
        "",
        "## Release Summary",
        "",
        f"- **Release type:** {rtype}",
        f"- **Primary focus:** {focus}",
        f"- **Breaking changes:** {breaking}",
        f"- **Package:** `{pypi_name}` v{version}",
        "",
        "---",
        "",
        "## What's New",
        "",
    ]
    if sections:
        lines.extend(_render_change_groups(sections))
    else:
        lines.append("_No CHANGELOG `[Unreleased]` bullets found; populate before release._")
        lines.append("")
    lines.extend(
        [
            "---",
            "",
            "## Known Issues",
            "",
            "None known at time of release.",
            "",
            "---",
            "",
            "## Links",
            "",
            f"- [Full Changelog]({changelog_url or '../../CHANGELOG.md'})",
            f"- Archive target: `{archive_relpath(pypi_name, version)}`",
            "",
        ]
    )
    if not final:
        lines.extend(_remaining_sections_comment(template_text, STANDARD_FILLED_SECTIONS, repo_root))
    return "\n".join(lines) + "\n"


def _render_security(pypi_name: str, version: str, bump: str, date: str, sections: "OrderedDict[str, list]", template_text: str, repo_root: "Path | None", changelog_url: "str | None" = None, final: bool = False) -> str:
    name = display_name(pypi_name)
    lines: list = [
        f"# {name} v{version} – :lock: SECURITY PATCH RELEASE",
        "",
        f"**Release Date:** {date}",
        "**Release Type:** Security Patch",
        "**Priority:** [PRIORITY_LEVEL]",
        f"**Package Affected:** {pypi_name}",
        "",
        "---",
        "",
        f"This is a security-bearing release of `{pypi_name}` v{version}. It carries a `Security` "
        f"Keep-a-Changelog category and was drafted by the release-train from the security template; "
        f"complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.",
        "",
        "---",
        "",
        "## Security Impact ([SEVERITY])",
        "",
        "| Attribute | Value |",
        "| --------- | ----- |",
        "| **Package** | `" + pypi_name + "` |",
        "| **Fixed in** | " + version + " |",
        "| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |",
        "| **Advisory** | [DEPENDABOT_ALERT_URL] |",
        "",
        "---",
        "",
        f"## Changes in v{version}",
        "",
    ]
    if sections:
        lines.extend(_render_change_groups(sections))
    else:
        lines.append("_No CHANGELOG `[Unreleased]` bullets found; populate before release._")
        lines.append("")
    lines.extend(
        [
            "---",
            "",
            "## References",
            "",
            f"- [CHANGELOG.md]({changelog_url or '../../CHANGELOG.md'})",
            f"- Archive target: `{archive_relpath(pypi_name, version)}`",
            "",
        ]
    )
    if not final:
        lines.extend(_remaining_sections_comment(template_text, SECURITY_FILLED_SECTIONS, repo_root))
    return "\n".join(lines) + "\n"


# ── relative-link rewrite (central-archive correctness) ──────────────────────
#
# CHANGELOG bullets legitimately carry links relative to the OWNING repo's tree
# (e.g. ``[design](notes/FOO.md)`` in juniper-canopy). Archived verbatim into
# juniper-ml's central ``notes/releases/`` those targets 404 (the canopy v0.6.0
# archive shipped two such links). When the caller supplies ``link_base`` —
# ``https://github.com/<owner>/<repo>/blob/<ref>`` — every inline markdown link
# whose target is relative (no URL scheme, not an in-page ``#`` anchor, not
# protocol-relative ``//``) is rewritten onto that base. Absolute http(s)/
# mailto links, bare anchors, and reference-style definitions are untouched.

_REL_LINK_RE = re.compile(
    r"""(\]\(\s*)              # the ](  opener (group 1, kept)
        (?![a-zA-Z][a-zA-Z0-9+.-]*:)   # not scheme: (http:, https:, mailto:, ...)
        (?!\#)                 # not a bare in-page anchor
        (?!//)                 # not protocol-relative
        ([^)\s]+)              # the relative target (group 2)
        (\s+"[^"]*")?          # optional markdown title (group 3)
        (\s*\))                # the closer (group 4, kept)
    """,
    re.VERBOSE,
)


def rewrite_relative_links(text: str, link_base: str) -> str:
    """Rewrite relative inline-link targets in ``text`` onto ``link_base``.

    ``link_base`` should be an absolute URL prefix without a trailing slash
    (``https://github.com/<owner>/<repo>/blob/<ref>``). ``./``-prefixed targets
    are normalized; in-page anchors on the target are preserved."""
    base = link_base.rstrip("/")

    def _sub(m: "re.Match") -> str:
        target = m.group(2)
        while target.startswith("./"):
            target = target[2:]
        title = m.group(3) or ""
        return f"{m.group(1)}{base}/{target}{title}{m.group(4)}"

    return _REL_LINK_RE.sub(_sub, text)


def _rewrite_sections(sections: "OrderedDict[str, list]", link_base: str) -> "OrderedDict[str, list]":
    out: "OrderedDict[str, list]" = OrderedDict()
    for category, bullets in sections.items():
        out[category] = [rewrite_relative_links(b, link_base) for b in bullets]
    return out


def render_notes(
    pypi_name: str,
    version: str,
    *,
    bump: str = "minor",
    release_date: "str | None" = None,
    sections: "OrderedDict[str, list] | None" = None,
    is_security: "bool | None" = None,
    template_text: "str | None" = None,
    repo_root: "Path | None" = None,
    link_base: "str | None" = None,
    changelog_url: "str | None" = None,
    final: bool = False,
) -> str:
    """Render a well-formed release-notes body (markdown string) for one package+version.

    ``sections`` is the ordered ``{Category: [bullets]}`` from :func:`parse_unreleased`; when
    omitted the draft is still well-formed with a placeholder in the changes group. ``is_security``
    defaults to detection from the ``sections`` categories (plan S10.1). ``template_text`` /
    ``repo_root`` let the tests inject a template offline; by default the live template is read.

    ``changelog_url`` is the absolute URL of the package's OWN ``CHANGELOG.md``. The archive lives
    centrally under juniper-ml's ``notes/releases/``, so the historical relative ``../../CHANGELOG.md``
    resolved to juniper-ml's ROOT changelog for every sub-package, and resolved to nothing at all in a
    GitHub Release body (relative links do not work there). Callers should build it as
    ``f"{link_base}/{changelog_rel(entry)}"``; omitted, the old relative link is kept so existing
    callers and the CLI are unchanged.

    ``final=True`` marks a body that is about to be PUBLISHED (the ceremony's archive + Release), and
    suppresses the trailing "complete or delete these template sections" HTML comment. That comment is
    correct guidance for a ``propose`` draft and is stale the moment it ships inside a cut Release."""
    sections = sections if sections is not None else OrderedDict()
    if link_base:
        sections = _rewrite_sections(sections, link_base)
    if is_security is None:
        is_security = is_security_release(sections)
    date = release_date or _today()
    if template_text is None:
        template_text = read_template(is_security, repo_root)
    if is_security:
        return _render_security(pypi_name, version, bump, date, sections, template_text, repo_root, changelog_url, final)
    return _render_standard(pypi_name, version, bump, date, sections, template_text, repo_root, changelog_url, final)


# ── CLI (independently invokable, plan S10.1) ────────────────────────────────


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="release_train/notes_render.py", description="Render a template-driven release-notes DRAFT for one package+version (plan S10.1).")
    p.add_argument("--package", required=True, metavar="PYPI_NAME", help="the package's pypi_name (drives the title + archive-name convention)")
    p.add_argument("--version", required=True, help="the proposed release version (e.g. 0.4.1)")
    p.add_argument("--bump", default="minor", choices=("major", "minor", "patch", "none"), help="SemVer bump class -> Release Type label (plan S6)")
    p.add_argument("--changelog", default=None, help="path to the package CHANGELOG.md to source [Unreleased] bullets (optional)")
    p.add_argument("--release-date", default=None, help="override the release date (default: today UTC; use for deterministic output)")
    p.add_argument("--security", action="store_true", help="force the security template (else auto-detected from a Security category)")
    p.add_argument("--repo-root", default=None, help="juniper-ml checkout root for template lookup (default: three parents up)")
    p.add_argument("--print-archive-name", action="store_true", help="print only the central archive relpath and exit")
    p.add_argument("--link-base", default=None, metavar="URL", help="absolute URL prefix (https://github.com/<owner>/<repo>/blob/<ref>) to rewrite relative CHANGELOG links onto (central-archive correctness; default: no rewrite)")
    p.add_argument("--changelog-url", default=None, metavar="URL", help="absolute URL of the package's OWN CHANGELOG.md for the Links section (default: the legacy relative ../../CHANGELOG.md, which resolves to juniper-ml's ROOT changelog)")
    p.add_argument("--final", action="store_true", help="render a body destined to be PUBLISHED: drop the trailing 'complete or delete these template sections' comment, which is stale once a Release is cut from it")
    return p.parse_args(argv)


def main(argv: "list[str] | None" = None) -> int:
    args = parse_args(argv)
    if args.print_archive_name:
        print(archive_relpath(args.package, args.version))
        return 0
    sections: "OrderedDict[str, list]" = OrderedDict()
    if args.changelog:
        try:
            sections = parse_unreleased(Path(args.changelog).read_text(encoding="utf-8"))
        except OSError as exc:
            print(f"ERROR: cannot read changelog {args.changelog}: {exc}", file=sys.stderr)
            return 2
    is_security = True if args.security else None
    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    try:
        text = render_notes(args.package, args.version, bump=args.bump, release_date=args.release_date, sections=sections, is_security=is_security, repo_root=repo_root, link_base=args.link_base, changelog_url=args.changelog_url, final=args.final)
    except OSError as exc:
        print(f"ERROR: cannot read release-notes template: {exc}", file=sys.stderr)
        return 2
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
