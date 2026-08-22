"""Convert the ratified JR-REC-* proposal into a v5 extraction YAML.

Parses `notes/JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md`
rather than transcribing it. Eleven entries hand-copied is eleven chances to typo a brief,
mis-file a category, or silently drop a source -- and the proposal is the ratified text, so
anything this script cannot parse is a defect in the proposal worth seeing, not something to
paper over by editing the YAML afterwards.

Sources in the proposal are prose (`file.md` (OQ-14 bands); `other.py` (`symbol`)) with line
numbers "deliberately omitted where files churn". They are emitted as path-only citations,
which the view renderer already supports -- ``- `path` `` with no ``(lines A-B)`` suffix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-21
Status: ad-hoc -- one-off (v5 refresh ingestion)
Retire when: the v5 refresh has merged and JR-REC-* IDs are official; the YAML it produces is
             the durable artifact, this converter is not.
Related: T7 of HANDOFF_2026-08-18_cli-experimentation-unowned-tasks.md; Q-12 / Wave 7.6
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = REPO_ROOT / "notes" / "JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md"
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
OUT = REPO_ROOT / "notes" / "requirements" / "v5_rec_extraction.yaml"

_HEAD = re.compile(r"^### (?P<id>JR-REC-[A-Z]+-\d+) — (?P<brief>.+)$")
_META = re.compile(r"^\*\*Status\*\*: (?P<status>\S+)\s+\*\*Priority\*\*: (?P<priority>\S+)\s+\*\*Category\*\*: (?P<category>\S+)\s+\*\*Owner\*\*: (?P<owner>\S+)\s*$")
_FIELD = re.compile(r"^\*\*(?P<name>Sources|Detail)\*\*: (?P<value>.+)$")

#: Schema-conformant citations, resolved by ANCHOR rather than by line number.
#:
#: The proposal cites sources as prose ("WS-1 data foundation (juniper-data#168)", "CLI
#: experimentation plan §5.5/§6.3") and states that "line numbers [are] deliberately omitted
#: where files churn". That is fine for a human-readable proposal and NOT fine for the
#: corpus, whose schema calls Sources the "hallucination check anchor" and requires
#: ``path`` + ``line_start``/``line_end``. Ingesting the prose verbatim produced 21
#: BAD_RANGE findings on ``util/requirements_drift_check.py`` -- a quality regression
#: introduced by the very refresh meant to improve traceability.
#:
#: So the proposal keeps its prose and this map carries the machine-checkable form: each
#: citation is a real path plus a text anchor located at conversion time. An anchor that no
#: longer matches raises instead of emitting a citation that merely LOOKS precise -- which
#: is the same guarantee a line number was supposed to give, without the churn.
SOURCES: "dict[str, list[tuple[str, str]]]" = {
    "JR-REC-TRAIN-001": [
        ("juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-DESIGN.md", "≥25% lower RMSE"),
        ("juniper-recurrence/bench/run_benchmark.py", "def evaluate_bands"),
    ],
    "JR-REC-TRAIN-002": [
        ("juniper-ml/notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md", "## 1. Scope and non-goals"),
        ("juniper-recurrence/bench/datasets.py", "delay_product"),
    ],
    "JR-REC-DATA-001": [
        ("juniper-ml/notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md", "# Juniper-Recurse — Irregular-Δt Datasets"),
        ("juniper-data-client/juniper_data_client/contract.py", "def validate_npz_contract"),
    ],
    "JR-REC-API-001": [
        ("juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md", "### 5.5 recurrence experiment YAML"),
        ("juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/training.py", '@router.post("/v1/train"'),
    ],
    "JR-REC-TEST-001": [
        ("juniper-recurrence/bench/run_benchmark.py", "def evaluate_bands"),
        ("juniper-recurrence/bench/datasets.py", "PRIMARY_DATASETS = "),
        ("juniper-recurrence/bench/test_bench_smoke.py", "Smoke tests for the bench harness"),
    ],
    "JR-REC-TEST-002": [
        ("juniper-ml/notes/JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md", "# CLI Experimentation — P3 Acceptance-Criteria Roll-Up"),
    ],
    "JR-REC-TOOL-001": [
        ("juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md", "### 5.2 Implementation mechanism"),
        ("juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py", "class ExperimentYamlSettingsSource"),
    ],
    "JR-REC-TOOL-002": [
        ("juniper-recurrence/juniper-recurrence/juniper_recurrence/main.py", "def _experiment_train_overrides"),
    ],
    "JR-REC-TEST-003": [
        ("juniper-recurrence/bench/run_benchmark.py", "--results-dir DIR"),
    ],
    "JR-REC-OBS-001": [
        ("juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md", "### 6.1 Canonical launch commands"),
        ("juniper-ml/util/experiment_stack.bash", "recurrence 8260-8289"),
    ],
    "JR-REC-DEP-001": [
        ("juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md", "| **Q-10** |"),
    ],
}

#: Lines of context to cite around an anchor. The corpus convention is a RANGE, not a point:
#: a one-line citation re-reads as noise the moment anything above it shifts.
CONTEXT_LINES = 12


def _resolve(entry_id: str) -> "list[dict]":
    """Turn the anchor map into ``path`` + ``line_start``/``line_end`` citations.

    Raises when an anchor no longer matches: a citation that cannot be located is worse than
    no citation, because it survives review looking authoritative.
    """
    out: "list[dict]" = []
    for rel, anchor in SOURCES[entry_id]:
        path = ECOSYSTEM_ROOT / rel
        if not path.is_file():
            raise SystemExit(f"{entry_id}: cited path does not exist: {rel}")
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        hit = next((n for n, line in enumerate(lines, 1) if anchor in line), None)
        if hit is None:
            raise SystemExit(f"{entry_id}: anchor {anchor!r} no longer appears in {rel} -- re-anchor it")
        out.append({"path": str(path), "line_start": hit, "line_end": min(hit + CONTEXT_LINES, len(lines))})
    return out


def main() -> int:
    text = PROPOSAL.read_text(encoding="utf-8")
    entries: "list[dict]" = []
    current: "dict | None" = None

    for line in text.split("\n"):
        head = _HEAD.match(line)
        if head:
            current = {"id": head.group("id"), "brief": head.group("brief").strip()}
            entries.append(current)
            continue
        if current is None:
            continue
        meta = _META.match(line)
        if meta:
            current.update(
                status=meta.group("status"),
                priority=meta.group("priority"),
                category=meta.group("category"),
                owner=meta.group("owner"),
            )
            continue
        field = _FIELD.match(line)
        if field:
            if field.group("name") == "Detail":
                current["detail"] = field.group("value").strip()
            continue
        if line.startswith("## "):
            current = None

    for entry in entries:
        if entry["id"] not in SOURCES:
            raise SystemExit(f"{entry['id']}: no citation anchors defined -- add them to SOURCES")
        entry["sources"] = _resolve(entry["id"])

    required = ("id", "brief", "status", "priority", "category", "owner", "sources", "detail")
    for entry in entries:
        missing = [f for f in required if not entry.get(f)]
        if missing:
            raise SystemExit(f"{entry.get('id', '?')}: proposal is missing {missing} -- fix the PROPOSAL, not this output")

    ordered = [{k: entry[k] for k in ("id", "owner", "category", "status", "priority", "brief", "sources", "detail")} for entry in entries]
    OUT.write_text(
        "# v5 refresh -- juniper-recurrence (rec) starter block.\n"
        "#\n"
        "# GENERATED from notes/JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md\n"
        "# by util/ad-hoc/2026-08-21_v5_rec_extraction.py. Edit the PROPOSAL and re-run; do not\n"
        "# hand-edit this file -- the proposal is the ratified text and must stay the single source.\n"
        "#\n"
        "# IDs are explicit because the proposal reserved them and PR descriptions already cite\n"
        "# them as (proposed); minting fresh numbers would break those references.\n"
        + yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, width=10_000),
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(REPO_ROOT)}: {len(ordered)} entries")
    for entry in ordered:
        print(f"  {entry['id']:22s} {entry['status']:9s} {entry['priority']}  {entry['category']:6s} {len(entry['sources'])} source(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
