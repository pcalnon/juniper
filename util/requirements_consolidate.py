#!/usr/bin/env python3
"""Consolidate the Juniper requirements snapshot: parse the corpus, merge, regenerate.

Project:     Juniper
Sub-Project: juniper-ml
Application: requirements snapshot consolidation (v5+)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      permanent utility

Why this exists
---------------
The v1-v4 consolidation script (``phase4_consolidate.py``) was authored in ``/tmp/`` and is
irrecoverable -- the incident that produced the ecosystem-wide Script-placement rule. The
requirements next-steps doc §8 calls rebuilding it **"a hard v5 prerequisite"**: without it no
refresh can run, so the snapshot is frozen and a new repo joining the ecosystem cannot be
given IDs.

WHAT CHANGED SINCE v1-v4, AND WHY THIS IS NOT A REIMPLEMENTATION
---------------------------------------------------------------
The original consumed the Phase-3 extraction YAMLs (``/tmp/req_extract_*.yaml``). **Those are
gone too.** So the corpus has to come from the shipped artifacts, and they are not
interchangeable:

  * ``notes/requirements/id_assignments.yaml`` -- the ID ledger. 1,803 entries carrying
    id / owner / category / status / priority / brief / sources / notes / merged_count.
    It has **no ``detail`` field at all.**
  * ``notes/requirements/by-area/*.md`` -- the rendered views. The same 1,803 entries, of
    which **910 carry a ``**Detail**:`` section that exists nowhere else.**

Regenerating the views *from the ledger* -- the obvious reading of "regenerate" -- would
silently delete every one of those 910 Detail sections. The by-area views are therefore the
**corpus of record** here, and the ledger is a derived subset.

That inverts the original data flow, so the load-bearing property is round-trip fidelity:

    render(parse(corpus)) == corpus, byte for byte

``--check-roundtrip`` asserts exactly that against the live tree and is the first thing to run
after any change to the parser or the renderer. A round-trip that loses one space in one entry
is a corpus-wide diff that no reviewer can read, which is how content gets lost quietly.

WHAT THIS DOES *NOT* DO
-----------------------
The v2-v4 quality passes -- ARCH re-bucket (v2-4), fuzzy cross-repo dedup (v3-1), cross-round
dedup (v3-2), thin-brief repair (v3-3 / v4-3) -- were one-time corrections **already applied to
the shipped corpus**. Re-running them over already-corrected entries would churn 1,803 entries
to no benefit and risk re-repairing a human-repaired brief. They are implemented here as
``--merge``-time passes over INCOMING entries only, which is where they still earn their keep.

Usage
-----
    # safety first: prove the parser and renderer agree with the shipped tree
    python3 util/requirements_consolidate.py --check-roundtrip

    # what would a merge change? (writes nothing)
    python3 util/requirements_consolidate.py --merge notes/requirements/v5_rec_extraction.yaml --dry-run

    # do it
    python3 util/requirements_consolidate.py --merge notes/requirements/v5_rec_extraction.yaml --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REQ_ROOT = REPO_ROOT / "notes" / "requirements"
def _find_ecosystem_root(start: Path) -> Path:
    """The directory that holds the sibling repos.

    NOT ``REPO_ROOT.parent``: this repo is routinely checked out as a worktree under
    ``<repo>/.claude/worktrees/<name>``, where that yields ``.../.claude/worktrees`` and every
    absolute path written to the ledger comes out corrupted. The views survive it (parse and
    render share the constant, so the error cancels) which is exactly what makes it dangerous
    -- the round-trip check cannot see it. Anchor on the sibling repos instead.
    """
    for candidate in [start, *start.parents]:
        if (candidate / "juniper-ml").is_dir() and (candidate / "juniper-cascor").is_dir():
            return candidate
    return start.parent


ECOSYSTEM_ROOT = _find_ecosystem_root(REPO_ROOT)

#: The 15 locked area codes, in the README's documented order, with their scope blurbs.
#: Locked at the 2026-05-12 schema freeze; a new code is a schema change, not a refresh.
AREA_SCOPES: "dict[str, str]" = {
    "OBS": "observability — metrics, logging, tracing, dashboards, alerting",
    "SEC": "security — authn, authz, secrets, CVEs, hardening",
    "API": "API contracts — schemas, versioning, compatibility, migrations",
    "DEP": "deployment-config — Docker, Compose, K8s, Helm, image build",
    "UI": "ui-frontend — Canopy/Dash, UX, visualizations",
    "DATA": "data-pipeline — dataset generation, NPZ contracts, ingestion",
    "TRAIN": "training — cascor algorithm, candidates, convergence, model state",
    "WS": "websocket / messaging — Canopy↔Cascor streaming, replay, control plane",
    "TEST": "testing-and-ci — pytest, fixtures, CI workflows, regression analysis",
    "LOCK": "lockfile-and-deps — uv lockfiles, pyproject pins, dep updates, env rebuilds",
    "ARCH": "architecture / cross-cutting design — microservices, polyrepo, interface proposals",
    "PERF": "performance / scalability — throughput, latency, parallelization, CUDA",
    "TOOL": "dev tooling / scripts / workflow — worktree procs, claude-code launchers",
    "DOC": "documentation / process — link validation, conventions, file headers",
    "OPS": "operations / runbooks / on-call — runbook documents, incident response",
}

#: Owner shortcode -> repo directory. ``rec`` is the v5 addition (juniper-recurrence
#: postdates the 2026-05-12 snapshot; its absence is the trigger that opened v5).
OWNER_REPOS: "dict[str, str]" = {
    "ml": "juniper-ml",
    "cas": "juniper-cascor",
    "can": "juniper-canopy",
    "dat": "juniper-data",
    "dep": "juniper-deploy",
    "cwk": "juniper-cascor-worker",
    "ccl": "juniper-cascor-client",
    "dcl": "juniper-data-client",
    "rec": "juniper-recurrence",
}

STATUSES = ["proposed", "designed", "in-progress", "shipped", "deferred", "rejected", "superseded"]
PRIORITIES = ["P0", "P1", "P2", "P3"]

_ENTRY_RE = re.compile(r"^### (?P<id>JR-[A-Z]+-[A-Z]+-\d+) — (?P<brief>.*)$")
_META_RE = re.compile(r"^\*\*Status\*\*: (?P<status>\S+)  \*\*Priority\*\*: (?P<priority>\S+)  \*\*Category\*\*: (?P<category>\S+)  \*\*Owner\*\*: (?P<owner>\S+)$")
_SOURCE_RE = re.compile(r"^- `(?P<path>[^`]+)`(?: \(lines (?P<start>\d+)-(?P<end>\d+)\))?$")


class Entry:
    """One requirement. Field order here is the ledger's field order, deliberately."""

    __slots__ = ("id", "owner", "category", "status", "priority", "brief", "merged_count", "notes", "sources", "detail", "body")

    def __init__(self, id: str, owner: str, category: str, status: str, priority: str, brief: str, merged_count: int = 1, notes: Optional[str] = None, sources: Optional[list] = None, detail: Optional[str] = None, body: Optional[str] = None) -> None:
        self.id = id
        self.owner = owner
        self.category = category
        self.status = status
        self.priority = priority
        self.brief = brief
        self.merged_count = merged_count
        self.notes = notes
        self.sources = sources or []
        self.detail = detail
        #: The entry body EXACTLY as it appeared in the view, re-emitted unchanged.
        #:
        #: Modelling every optional section was tried and is the wrong shape: the corpus
        #: carries a ``**Design**:`` section (36 entries), a
        #: ``*Merged from N extraction candidates (slices: X).*`` provenance line whose
        #: ``slices`` value exists in NO other artifact, and at least one stray
        #: file-level heading. Each was a field the first renderer silently dropped, and
        #: each was caught only by the round-trip check. Keeping the body verbatim makes
        #: that whole class impossible rather than repeatedly rediscovered.
        #:
        #: None for a NEW entry, whose body is synthesised from the fields above.
        self.body = body

    @property
    def number(self) -> int:
        return int(self.id.rsplit("-", 1)[1])

    def ledger_dict(self) -> dict:
        """The ledger projection -- note it deliberately drops ``detail``.

        That asymmetry is not a bug to fix here: it is the shipped ledger's schema, and
        changing it would rewrite all 1,803 ledger entries in a refresh whose scope is one
        new repo. The views keep the detail; see the module docstring.
        """
        return {
            "id": self.id,
            "owner": self.owner,
            "category": self.category,
            "status": self.status,
            "priority": self.priority,
            "brief": self.brief,
            "merged_count": self.merged_count,
            "notes": self.notes,
            "sources": [dict(s) for s in self.sources],
        }


# --------------------------------------------------------------------------- parse


def _split_blocks(text: str) -> "list[str]":
    """Entry blocks from a rendered view, in file order."""
    parts = text.split("\n### ")
    return ["### " + p for p in parts[1:]]


def _preamble(text: str) -> str:
    """Whatever sits between the ``---`` rule and the first entry.

    Normally empty. ``by-area/DATA.md`` carries a stray ``## Requirements from Area: Data,
    List`` heading there -- an artifact of the original run. It is preserved rather than
    tidied away: this script's job in a refresh is to not lose content, and silently
    dropping a line nobody has reviewed is exactly the failure being guarded against.
    """
    marker = "\n---\n"
    idx = text.find(marker)
    if idx == -1:
        return ""
    start = idx + len(marker)
    match = re.search(r"^### ", text[start:], re.M)
    return text[start:start + match.start()] if match else text[start:]


def parse_entry(block: str) -> Entry:
    """One ``### JR-...`` block back into an Entry.

    Sections are optional and order-fixed: Status line, Sources, Detail, Notes. A brief may
    itself contain markdown, em-dashes and backticks, so only the FIRST ' — ' after the id
    separates id from brief.
    """
    lines = block.split("\n")
    head = _ENTRY_RE.match(lines[0])
    if head is None:  # pragma: no cover - malformed corpus
        raise ValueError(f"unparseable entry header: {lines[0][:120]!r}")

    meta = None
    for line in lines:
        m = _META_RE.match(line)
        if m:
            meta = m
            break
    if meta is None:  # pragma: no cover - malformed corpus
        raise ValueError(f"{head.group('id')}: no Status/Priority/Category/Owner line")

    sections = _sections(lines)
    sources = []
    for line in sections.get("Sources", []):
        sm = _SOURCE_RE.match(line)
        if sm is None:
            continue
        src = {"path": str(ECOSYSTEM_ROOT / sm.group("path"))}
        if sm.group("start"):
            src["line_start"] = int(sm.group("start"))
            src["line_end"] = int(sm.group("end"))
        sources.append(src)

    detail = "\n".join(sections.get("Detail", [])).strip("\n") or None
    notes = "\n".join(sections.get("Notes", [])).strip("\n") or None

    return Entry(
        id=head.group("id"),
        owner=meta.group("owner"),
        category=meta.group("category"),
        status=meta.group("status"),
        priority=meta.group("priority"),
        brief=head.group("brief"),
        notes=notes,
        sources=sources,
        detail=detail,
        body="\n".join(lines[1:]),
    )


def _sections(lines: "list[str]") -> "dict[str, list[str]]":
    """Split an entry block into its ``**Name**:`` sections, preserving inner blank lines."""
    out: "dict[str, list[str]]" = {}
    current: Optional[str] = None
    for line in lines[1:]:
        m = re.match(r"^\*\*(Sources|Detail|Notes)\*\*:\s*$", line)
        if m:
            current = m.group(1)
            out[current] = []
            continue
        if _META_RE.match(line):
            current = None
            continue
        if current is not None:
            out[current].append(line)
    for key in out:
        while out[key] and not out[key][0].strip():
            out[key].pop(0)
        while out[key] and not out[key][-1].strip():
            out[key].pop()
    return out


def parse_corpus(req_root: Path = REQ_ROOT) -> "list[Entry]":
    """The corpus of record: every entry in ``by-area/*.md``, in file then document order."""
    entries: "list[Entry]" = []
    seen: "set[str]" = set()
    for path in sorted((req_root / "by-area").glob("*.md")):
        for block in _split_blocks(path.read_text(encoding="utf-8")):
            entry = parse_entry(block)
            if entry.id in seen:  # pragma: no cover - would be a corpus defect
                raise ValueError(f"duplicate id in corpus: {entry.id}")
            seen.add(entry.id)
            entries.append(entry)
    return entries


def _apply_ledger(entries: "list[Entry]", req_root: Path = REQ_ROOT) -> None:
    """Fold ledger-only fields (``merged_count``) onto parsed entries.

    ``merged_count`` records how many extraction candidates collapsed into an entry. It is
    not rendered in any view, so a parse-only corpus would reset every one of them to 1 and
    quietly destroy the dedup history.
    """
    ledger_path = req_root / "id_assignments.yaml"
    if not ledger_path.is_file():
        return
    ledger = {e["id"]: e for e in yaml.safe_load(ledger_path.read_text(encoding="utf-8")) or []}
    for entry in entries:
        row = ledger.get(entry.id)
        if row is not None:
            entry.merged_count = row.get("merged_count", 1)


def load_corpus(req_root: Path = REQ_ROOT) -> "list[Entry]":
    """The corpus in CANONICAL ORDER.

    Every view is the same global sequence filtered -- by-area by category, by-repo by
    owner, by-status by status -- and that sequence survives only in ``id_assignments.yaml``.
    Parsing by-area alone recovers the entries but concatenates them area by area, which
    reproduces by-area exactly and reorders by-repo and by-status wholesale. Re-imposing the
    ledger order is what keeps a refresh's diff limited to what actually changed.
    """
    entries = parse_corpus(req_root)
    _apply_ledger(entries, req_root)
    ledger_path = req_root / "id_assignments.yaml"
    if ledger_path.is_file():
        order = {row["id"]: n for n, row in enumerate(yaml.safe_load(ledger_path.read_text(encoding="utf-8")) or [])}
        # Unknown ids sort last, keeping their relative order: a view entry absent from the
        # ledger is a corpus defect, not a reason to drop it.
        entries.sort(key=lambda e: order.get(e.id, len(order)))
    return entries


# -------------------------------------------------------------------------- render


def _rel_source(path: str) -> str:
    """Views cite repo-relative paths; the ledger stores absolute ones."""
    try:
        return str(Path(path).relative_to(ECOSYSTEM_ROOT))
    except ValueError:
        return path


def render_entry(entry: Entry) -> str:
    """Render one entry.

    An entry parsed from the corpus re-emits its body byte-for-byte; only a NEW entry has
    its body synthesised. See ``Entry.body`` for why.
    """
    if entry.body is not None:
        return f"### {entry.id} — {entry.brief}\n{entry.body}"
    out = [f"### {entry.id} — {entry.brief}", ""]
    out.append(f"**Status**: {entry.status}  **Priority**: {entry.priority}  **Category**: {entry.category}  **Owner**: {entry.owner}")
    out.append("")
    out.append("**Sources**:")
    for src in entry.sources:
        rel = _rel_source(src["path"])
        if src.get("line_start") is not None:
            out.append(f"- `{rel}` (lines {src['line_start']}-{src['line_end']})")
        else:
            out.append(f"- `{rel}`")
    out.append("")
    if entry.detail:
        out.append("**Detail**:")
        out.append("")
        out.append(entry.detail)
        out.append("")
    if entry.notes:
        out.append("**Notes**:")
        out.append("")
        out.append(entry.notes)
        out.append("")
    return "\n".join(out)


def _counts(entries: Iterable[Entry], attr: str, order: Optional["list[str]"] = None) -> str:
    counter = Counter(getattr(e, attr) for e in entries)
    keys = [k for k in (order or []) if k in counter] if order else []
    keys += [k for k, _ in counter.most_common() if k not in keys]
    return " | ".join(f"{k}={counter[k]}" for k in keys)


def _render_view(title: str, subtitle: Optional[str], entries: "list[Entry]", stat_lines: "list[str]", preamble: str = "\n") -> str:
    out = [f"# {title}", ""]
    if subtitle:
        out.append(subtitle)
        out.append("")
    out.append(f"**Total entries**: {len(entries)}")
    out.append("")
    for line in stat_lines:
        out.append(line)
        out.append("")
    out.append("---")
    # The rule's own newline, then the preamble region verbatim, then the entries
    # concatenated with no separator: each parsed body already ends with the blank line
    # that separated it from its successor, so re-joining reproduces the original spacing.
    body = "\n".join(out) + "\n" + preamble + "\n".join(render_entry(e) for e in entries)
    return body.rstrip("\n") + "\n"


def render_area(code: str, entries: "list[Entry]", preamble: str = "\n") -> str:
    return _render_view(
        f"Requirements — {code}",
        f"**Area**: {AREA_SCOPES[code]}",
        entries,
        [
            f"**By status**: {_counts(entries, 'status', STATUSES)}",
            f"**By priority**: {_counts(entries, 'priority', PRIORITIES)}",
            f"**By owner**: {_counts(entries, 'owner')}",
        ],
        preamble,
    )


def render_repo(owner: str, entries: "list[Entry]", preamble: str = "\n") -> str:
    return _render_view(
        f"Requirements — {OWNER_REPOS[owner]} ({owner})",
        None,
        entries,
        [
            f"**By status**: {_counts(entries, 'status', STATUSES)}",
            f"**By priority**: {_counts(entries, 'priority', PRIORITIES)}",
            f"**By category**: {_counts(entries, 'category')}",
        ],
        preamble,
    )


def render_status(status: str, entries: "list[Entry]", preamble: str = "\n") -> str:
    return _render_view(
        f"Requirements — status: {status}",
        None,
        entries,
        [
            f"**By priority**: {_counts(entries, 'priority', PRIORITIES)}",
            f"**By category**: {_counts(entries, 'category')}",
            f"**By owner**: {_counts(entries, 'owner')}",
        ],
        preamble,
    )


#: The family ``write_all`` owns. Deliberately just the canonical one -- ``by-repo`` and
#: ``by-status`` are written by ``regenerate_views`` instead, so exactly one writer owns each
#: file. Two independent writers is what produced the drift this factoring removes.
FAMILIES_WRITTEN_BY_WRITE_ALL = (("by-area", "category", render_area),)


def write_all(new_entries: "list[Entry]", req_root: Path = REQ_ROOT) -> "list[Path]":
    """Add ``new_entries`` to the views and the ledger, touching nothing else.

    APPEND-ONLY for ``by-area``, which is canonical: each file is re-rendered from its OWN
    parsed entries plus whatever is new, and every shipped file round-trips byte-for-byte.
    The ledger is likewise appended rather than re-dumped -- ``id_assignments.yaml`` briefs are
    truncated by design (AGENTS.md says never to read content from it), so rewriting it from
    full view text would churn ~1,100 rows and bury the real change.

    ``by-repo`` and ``by-status`` are NOT written here. They are derived -- see
    ``render_derived`` / ``regenerate_views`` -- and the caller projects them from ``by-area``
    after this returns, so an addition cannot land in one family and miss another.

    This function previously appended to all three independently, justified by a measured claim
    that regenerating one family from another "would PROPAGATE a defect across ~150 entries".
    That claim was **wrong** (ml#1415): the families differ by ZERO ids and ZERO metadata fields;
    the 52 / 149 counts are trailing punctuation and whitespace on otherwise identical entries,
    reducing to four markdown artifacts. Independent maintenance was the thing producing the
    drift, not the protection against it.
    """
    written: "list[Path]" = []
    families = FAMILIES_WRITTEN_BY_WRITE_ALL
    for sub, attr, renderer in families:
        additions: "dict[str, list[Entry]]" = {}
        for entry in new_entries:
            additions.setdefault(getattr(entry, attr), []).append(entry)

        for path in sorted((req_root / sub).glob("*.md")):
            key = path.stem
            text = path.read_text(encoding="utf-8")
            if key not in additions:
                continue  # untouched: not even rewritten, so it cannot drift
            own = [parse_entry(b) for b in _split_blocks(text)]
            path.write_text(renderer(key, own + additions.pop(key), _preamble(text)), encoding="utf-8")
            written.append(path)

        # Keys with no existing file -- by-repo/rec.md on the v5 refresh.
        for key, group in additions.items():
            path = req_root / sub / f"{key}.md"
            path.write_text(renderer(key, group, "\n"), encoding="utf-8")
            written.append(path)

    # Ledger: append raw YAML rather than re-dumping. A safe_dump of the whole ledger
    # re-quotes and re-wraps all 1,803 existing rows, burying the real change.
    ledger = req_root / "id_assignments.yaml"
    if new_entries:
        chunk = yaml.safe_dump([e.ledger_dict() for e in new_entries], sort_keys=False, allow_unicode=True, width=10_000)
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(chunk)
        written.append(ledger)
    return written


# --------------------------------------------------------------------------- merge


def _normalize(brief: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", brief.lower()).strip()


def _tokens(brief: str) -> "set[str]":
    return {t for t in _normalize(brief).split() if len(t) > 2}


def _overlap(a: "set[str]", b: "set[str]") -> float:
    """Overlap coefficient -- the v3-1 similarity, threshold 0.65."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def next_id(entries: "list[Entry]", owner: str, category: str) -> str:
    prefix = f"JR-{owner.upper()}-{category}-"
    used = [e.number for e in entries if e.id.startswith(prefix)]
    return f"{prefix}{(max(used) + 1) if used else 1:03d}"


def merge(corpus: "list[Entry]", incoming: "list[Entry]") -> "tuple[list[Entry], list[str]]":
    """Merge incoming entries into the corpus, minting IDs. Returns (corpus, report lines).

    Dedup is applied to INCOMING entries only (see the module docstring): exact
    normalized-brief match within an (owner, category) bucket, then the v3-1 fuzzy pass at
    overlap >= 0.65. An incoming entry that matches an existing one is dropped with its
    ``merged_count`` folded into the survivor rather than minting a second ID for one
    requirement -- IDs are permanent and never reused, so a wrong mint is not retractable.
    """
    report: "list[str]" = []
    out = list(corpus)
    by_bucket: "dict[tuple[str, str], list[Entry]]" = {}
    for entry in out:
        by_bucket.setdefault((entry.owner, entry.category), []).append(entry)

    for entry in incoming:
        bucket = by_bucket.setdefault((entry.owner, entry.category), [])
        exact = next((e for e in bucket if _normalize(e.brief) == _normalize(entry.brief)), None)
        if exact is not None:
            exact.merged_count += 1
            report.append(f"  DEDUP exact  {entry.brief[:60]!r} -> {exact.id}")
            continue
        tokens = _tokens(entry.brief)
        fuzzy = next((e for e in bucket if _overlap(_tokens(e.brief), tokens) >= 0.65), None)
        if fuzzy is not None:
            fuzzy.merged_count += 1
            report.append(f"  DEDUP fuzzy  {entry.brief[:60]!r} -> {fuzzy.id}")
            continue
        entry.id = entry.id or next_id(out, entry.owner, entry.category)
        if any(e.id == entry.id for e in out):
            raise ValueError(f"id collision: {entry.id} already exists; IDs are never reused")
        out.append(entry)
        bucket.append(entry)
        report.append(f"  MINT  {entry.id}  {entry.brief[:60]}")
    return out, report


def load_incoming(path: Path) -> "list[Entry]":
    """Read an extraction YAML into Entries.

    Entries MAY carry an explicit ``id`` (the JR-REC block reserved its IDs in a proposal
    that PR descriptions already cite, so honouring them keeps those references resolving);
    otherwise one is minted.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    out = []
    for row in raw:
        for field in ("owner", "category", "status", "priority", "brief"):
            if not row.get(field):
                raise ValueError(f"{path}: entry missing required field {field!r}: {row.get('id') or row.get('brief')!r}")
        if row["category"] not in AREA_SCOPES:
            raise ValueError(f"{path}: unknown category {row['category']!r} (the 15 codes are locked)")
        if row["owner"] not in OWNER_REPOS:
            raise ValueError(f"{path}: unknown owner {row['owner']!r}")
        if row["status"] not in STATUSES:
            raise ValueError(f"{path}: unknown status {row['status']!r}")
        if row["priority"] not in PRIORITIES:
            raise ValueError(f"{path}: unknown priority {row['priority']!r}")
        out.append(
            Entry(
                id=row.get("id", ""),
                owner=row["owner"],
                category=row["category"],
                status=row["status"],
                priority=row["priority"],
                brief=row["brief"],
                merged_count=row.get("merged_count", 1),
                notes=row.get("notes"),
                sources=row.get("sources") or [],
                detail=row.get("detail"),
            )
        )
    return out


# ---------------------------------------------------------------------------- cli


def check_roundtrip(req_root: Path = REQ_ROOT) -> int:
    """Prove render(parse(corpus)) == corpus for every shipped view. The safety gate."""
    entries = load_corpus(req_root)
    by_area: "dict[str, list[Entry]]" = {}
    for entry in entries:
        by_area.setdefault(entry.category, []).append(entry)

    bad = 0
    for code, group in sorted(by_area.items()):
        path = req_root / "by-area" / f"{code}.md"
        want = path.read_text(encoding="utf-8")
        got = render_area(code, group, _preamble(want))
        if got != want:
            bad += 1
            for i, (a, b) in enumerate(zip(want.split("\n"), got.split("\n"))):
                if a != b:
                    print(f"  {path.name}: first diff at line {i + 1}\n    shipped: {a[:150]!r}\n    render : {b[:150]!r}")
                    break
            else:
                print(f"  {path.name}: differs in length ({len(want.splitlines())} vs {len(got.splitlines())} lines)")
    print(f"round-trip: {len(entries)} entries, {len(by_area)} area files, {bad} mismatching")
    return 1 if bad else 0


#: The DERIVED view families. ``by-area`` is canonical and is never regenerated from anything;
#: these two are a projection of it, grouped by a different key. The plan
#: (JUNIPER_2026-05-11_..._REQUIREMENTS-IDENTIFICATION-PLAN.md §97) always described them as
#: derived -- "thin indexes that link into by-area -- not duplicates ... avoids the maintenance
#: trap of three copies of every requirement going stale independently" -- but what shipped was
#: three independently-maintained full copies, and they had begun to drift.
DERIVED_FAMILIES = (("by-repo", "owner", render_repo), ("by-status", "status", render_status))


def render_derived(req_root: Path = REQ_ROOT, entries: "Optional[list[Entry]]" = None) -> "dict[Path, str]":
    """Every derived view file's intended content, projected from the canonical corpus.

    Order is the corpus order (``load_corpus`` re-imposes the ledger's), which is what every
    shipped view already follows: measured 2026-08-29, ``by-repo/ml.md``, ``by-status/proposed.md``
    and ``by-area/OBS.md`` are each exactly the ledger sequence filtered. Regenerating in any other
    order would reorder thousands of entries and bury the real diff.

    Each file's PREAMBLE is preserved from disk rather than synthesised: two shipped files carry a
    heading between the rule and the first entry (``## Requirements with Status: Designed, List``),
    which is content, not formatting, and a regeneration that dropped it would be a silent loss.
    """
    if entries is None:
        entries = load_corpus(req_root)
    out: "dict[Path, str]" = {}
    for sub, attr, renderer in DERIVED_FAMILIES:
        groups: "dict[str, list[Entry]]" = {}
        for entry in entries:
            groups.setdefault(getattr(entry, attr), []).append(entry)
        for key, group in sorted(groups.items()):
            path = req_root / sub / f"{key}.md"
            preamble = _preamble(path.read_text(encoding="utf-8")) if path.is_file() else "\n"
            out[path] = renderer(key, group, preamble)
    return out


def check_views(req_root: Path = REQ_ROOT) -> int:
    """Assert the derived families are exactly the projection of ``by-area``. The drift gate.

    ``--check-roundtrip`` proves ``render(parse(x)) == x`` for the 15 ``by-area`` files and never
    reads ``by-repo`` or ``by-status`` at all, so for as long as the three families were maintained
    independently nothing compared them. They diverged: 52 entries between by-area and by-repo, 149
    between by-area and by-status (measured 2026-08-29, ml#1415 -- zero id differences, zero
    metadata differences, entirely trailing punctuation and whitespace). This is the check that
    could have caught that, and that stops it recurring.
    """
    entries = load_corpus(req_root)
    intended = render_derived(req_root, entries)

    bad = 0
    for path in sorted(intended):
        want = path.read_text(encoding="utf-8") if path.is_file() else None
        got = intended[path]
        if want is None:
            bad += 1
            print(f"  {path.parent.name}/{path.name}: MISSING on disk (the corpus projects it)")
            continue
        if got != want:
            bad += 1
            for i, (a, b) in enumerate(zip(want.split("\n"), got.split("\n"))):
                if a != b:
                    print(f"  {path.parent.name}/{path.name}: first diff at line {i + 1}\n    shipped  : {a[:150]!r}\n    projected: {b[:150]!r}")
                    break
            else:
                print(f"  {path.parent.name}/{path.name}: differs in length ({len(want.splitlines())} vs {len(got.splitlines())} lines)")

    # A file the corpus no longer projects is REPORTED, never deleted: an owner or status with no
    # remaining entries is a corpus-level event that wants a human, not a side effect of a check.
    orphans = [p for sub, _, _ in DERIVED_FAMILIES for p in sorted((req_root / sub).glob("*.md")) if p not in intended]
    for path in orphans:
        bad += 1
        print(f"  {path.parent.name}/{path.name}: ORPHAN — on disk but no entry projects into it (not deleted; decide deliberately)")

    print(f"views: {len(entries)} entries, {len(intended)} derived files, {bad} mismatching")
    return 1 if bad else 0


def regenerate_views(req_root: Path = REQ_ROOT, apply: bool = False) -> "list[Path]":
    """Write the derived families from the canonical corpus. Returns the paths that CHANGED."""
    intended = render_derived(req_root, None)
    changed = [p for p, text in intended.items() if not p.is_file() or p.read_text(encoding="utf-8") != text]
    if apply:
        for path in changed:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(intended[path], encoding="utf-8")
    return changed


def main(argv: "Optional[list[str]]" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check-roundtrip", action="store_true", help="assert render(parse(corpus)) == corpus and exit")
    parser.add_argument("--check-views", action="store_true", help="assert by-repo/by-status are exactly the projection of by-area and exit")
    parser.add_argument("--regenerate-views", action="store_true", help="rewrite by-repo/by-status from by-area (needs --apply to write)")
    parser.add_argument("--merge", type=Path, default=None, help="extraction YAML to merge into the corpus")
    parser.add_argument("--apply", action="store_true", help="write the regenerated views (default is a dry run)")
    parser.add_argument("--dry-run", action="store_true", help="explicit no-write (the default; accepted for symmetry)")
    parser.add_argument("--req-root", type=Path, default=REQ_ROOT, help="requirements tree (default: notes/requirements)")
    args = parser.parse_args(argv)

    if args.check_roundtrip:
        return check_roundtrip(args.req_root)

    if args.check_views:
        return check_views(args.req_root)

    if args.regenerate_views:
        # by-area is canonical, so a broken round-trip means the SOURCE is unparseable and any
        # projection of it would be wrong. Refuse rather than write a confidently bad corpus.
        if check_roundtrip(args.req_root) != 0:
            print("refusing to regenerate: by-area does not round-trip, so the corpus cannot be trusted as the source")
            return 1
        changed = regenerate_views(args.req_root, apply=args.apply)
        for path in changed:
            print(f"  {'wrote' if args.apply else 'would write'} {path.parent.name}/{path.name}")
        print(f"regenerate-views: {len(changed)} file(s) {'written' if args.apply else 'would change'}")
        if not args.apply:
            print("dry run -- nothing written (pass --apply to write)")
        return 0

    corpus = load_corpus(args.req_root)
    print(f"corpus: {len(corpus)} entries")

    added: "list[Entry]" = []
    if args.merge is not None:
        incoming = load_incoming(args.merge)
        print(f"incoming: {len(incoming)} entries from {args.merge}")
        before = {e.id for e in corpus}
        corpus, report = merge(corpus, incoming)
        for line in report:
            print(line)
        added = [e for e in corpus if e.id not in before]
        print(f"corpus after merge: {len(corpus)} entries ({len(added)} new)")

    if not args.apply:
        print("dry run -- nothing written (pass --apply to write)")
        return 0
    if not added:
        print("nothing to add -- not rewriting any file")
        return 0

    # write_all is append-only, so only the by-area files an addition lands in are touched.
    written = write_all(added, args.req_root)
    # Refuse to leave a tree the parser cannot read back: a view whose new entry did not
    # survive its own round-trip is a view that has started losing content.
    if check_roundtrip(args.req_root) != 0:
        print("ERROR: post-write round-trip FAILED -- the tree is inconsistent", file=sys.stderr)
        return 2
    # by-repo / by-status are a projection of the canonical family, regenerated AFTER by-area is
    # written and verified. Doing it here rather than inside write_all keeps the ordering explicit:
    # the source must be parseable before anything is derived from it.
    written += regenerate_views(args.req_root, apply=True)
    if check_views(args.req_root) != 0:
        print("ERROR: derived views do not match the corpus after regeneration", file=sys.stderr)
        return 2
    print(f"wrote {len(written)} files")
    for path in written:
        print(f"  {path.relative_to(args.req_root.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
