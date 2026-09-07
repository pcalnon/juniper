# Requirements Snapshot — Next Steps

**Author**: Paul Calnon
**Created**: 2026-05-16
**Last updated**: 2026-05-16
**Status**: Living document — forward-looking work for after the v4 snapshot
**Owner**: Paul Calnon
**Cross-refs**:

- Plan doc: [`JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md`](JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md) — §10 future-work, §11 ship history, §12 known issues
- Snapshot index: [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md)
- Schema reference: [`requirements/README.md`](requirements/README.md)
- Operator surface: [`docs/REFERENCE.md` § Requirements Snapshot Consolidation](../docs/REFERENCE.md#requirements-snapshot-consolidation) — `by-area` is the corpus of record; the ledger has no `detail`

---

## 1. Purpose

The v1–v4 effort produced a stable 1,803-entry requirements snapshot. The corpus is at coverage ceiling (~98% density-weighted). This document is the action-oriented forward plan for **using** the snapshot rather than extracting more from it.

Each section below is a separate, independently-shippable initiative. None of them block the others. They are listed in suggested adoption order — start with the cheap immediate-value items, then layer infrastructure as actual usage signals appear.

**Decision rule**: don't build any of these speculatively. Wait for the corresponding usage signal (someone reaches for a feature that isn't there) before investing. The snapshot itself is the deliverable; everything here is opt-in tooling around it.

---

## 2. Topics

| # | Topic                                                                                    | Cost        | Value     | Depends on        | Status (2026-05-18)                  |
|---|------------------------------------------------------------------------------------------|-------------|-----------|-------------------|--------------------------------------|
| 1 | [Snapshot consumption recipes](#3-snapshot-consumption-recipes)                          | Trivial     | Immediate | —                 | ✅ Shipped (PR #264)                  |
| 2 | [JR-ID references in PRs](#4-jr-id-references-in-prs)                                    | Low         | High      | —                 | ✅ Shipped (PR #264)                  |
| 3 | [Author-side JR-ID tagging in notes/](#5-author-side-jr-id-tagging-in-notes-source-docs) | Low         | Medium    | §6                | Wait for §6                          |
| 4 | [CI lint validating JR-ID references](#6-ci-lint-validating-jr-id-references)            | Medium      | Medium    | §4 organic uptake | Wait for ~10 PRs using §4            |
| 5 | [Stale / drift detection](#7-stale--drift-detection)                                     | Medium      | Medium    | —                 | ✅ `--mode quick` shipped (this PR); `--mode full`/`--mode rewrite` deferred |
| 6 | [Periodic refresh procedure](#8-periodic-refresh-procedure)                              | Medium      | Medium    | §7 full, consolidate-script rebuild | Wait for refresh trigger             |
| 7 | [§12 carry-over triage](#9-12-carry-over-triage)                                         | Low (admin) | Low       | —                 | ✅ Shipped (PR #264)                  |

---

## 3. Snapshot consumption recipes

**Status**: Ready to use immediately. Zero infrastructure needed.

**Why**: 1,803 entries is too many to browse linearly. People will use the snapshot only if they have a clear path from a question to the answer.

### Common queries

All examples assume `cd juniper-ml`.

#### "What P0/P1 SEC requirements are still open?"

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('notes/requirements/id_assignments.yaml'))
hits = [e for e in d if e['category'] == 'SEC'
        and e['priority'] in ('P0','P1')
        and e['status'] in ('proposed','designed','in-progress','deferred')]
for e in sorted(hits, key=lambda x: (x['priority'], x['id'])):
    print(f\"{e['id']}  {e['priority']}  {e['status']:11s}  {e['brief'][:90]}\")
"
```

#### "What requirements cite file X?"

```bash
python3 -c "
import yaml, sys
target = sys.argv[1]  # path substring
d = yaml.safe_load(open('notes/requirements/id_assignments.yaml'))
for e in d:
    for s in e.get('sources', []):
        if target in s.get('path',''):
            print(f\"{e['id']}  L{s['line_start']}-{s['line_end']}  {e['brief'][:90]}\")
            break
" '<path-substring>'
```

#### "Show me the OBS area, by status"

Open [`requirements/by-area/OBS.md`](requirements/by-area/OBS.md). It's already sorted by status precedence + priority.

#### "What's shipped vs. proposed in cascor?"

Open [`requirements/by-repo/cas.md`](requirements/by-repo/cas.md). Header shows status breakdown.

#### "Find the entry for the WebSocket replay-buffer requirement"

```bash
grep -i 'replay.*buffer' notes/requirements/by-area/WS.md | head
```

### What NOT to do

- **Don't `grep` `id_assignments.yaml` for content.** Briefs there are truncated/normalized; the markdown files have full detail blocks.
- **Don't manually edit `id_assignments.yaml`** — it's regenerated by the consolidation script. Edits will be clobbered on next refresh.
- **Don't link to line numbers within `by-area/*.md`** — they shift on every regen. Link to the JR-* ID anchor instead (e.g., `requirements/by-area/SEC.md#jr-ml-sec-014`).

---

## 4. JR-ID references in PRs

**Status**: Convention proposal. Adopt by writing JR-* IDs in PR descriptions; no tooling required to start.

**Why**: A PR that closes (partially or fully) a requirement should say so. Without a stable cross-reference, the snapshot becomes stale-by-default — readers can't tell which requirements have been worked on since the snapshot was taken.

### Proposed convention

In every PR description, add a `Requirements` section listing JR-* IDs touched:

```markdown
## Requirements

- Closes JR-CAS-WS-014 — WebSocket replay buffer occupancy gauge.
- Partially closes JR-ML-SEC-002 — adds Origin allowlist; rate limiting deferred.
- References JR-CAN-UI-007 — uses the per-tab sidebar-width convention.
```

Verb conventions:

- `Closes JR-*` — this PR fully satisfies the requirement; after merge it should be marked `shipped` in the snapshot.
- `Partially closes JR-*` — this PR satisfies some of the requirement; description should specify which parts.
- `References JR-*` — this PR is informed by but doesn't change the requirement's status.
- `Supersedes JR-*` — this PR's design replaces an earlier requirement; the old entry should be marked `superseded` in the next refresh.

### How this scales

Initially: voluntary, no enforcement. Authors who care about traceability use it; those who don't, don't.

After ~10 PRs have used the convention naturally, add the [CI lint](#6-ci-lint-validating-jr-id-references) to keep references resolving. Then add a refresh-time pass that updates statuses based on `Closes JR-*` lines in merged PRs (this is the bridge between point-in-time snapshot and living document).

### Open decisions

- **Do PRs in non-Juniper repos (e.g., upstream libraries) get JR-* references too?** Likely no — the snapshot is internal.
- **Do we add JR-* references in commit messages, or only PR descriptions?** PR descriptions only, to keep the surface area small. Commit messages are too noisy.

---

## 5. Author-side JR-ID tagging in `notes/` source docs

**Status**: Convention proposal. Becomes load-bearing only after CI lint (§6) is in place.

**Why**: Right now, the snapshot's mapping from JR-* ID back to source content is one-way: the entry cites the source path + line range. The reverse mapping (find the JR-* ID for a paragraph in a notes doc) requires running a search. If notes docs include explicit JR-* markers, the mapping is bidirectional and self-validating.

### Proposed marker

In a notes doc, wrap a requirement paragraph with an HTML comment:

```markdown
<!-- requirement: JR-CAS-WS-014 -->
The cascor WebSocket server must expose `cascor_ws_replay_buffer_occupancy`
and `cascor_ws_replay_buffer_capacity` as Prometheus gauges, updated at every
replay-buffer mutation.
<!-- /requirement -->
```

The marker is HTML, so it renders invisibly in markdown viewers and doesn't disrupt prose.

### Convention rules

- A paragraph can have multiple markers if it satisfies multiple JR-* IDs.
- A JR-* ID can have multiple marker locations (cross-file restatements stay valid; the consolidator handles dedup).
- Don't tag historical narrative (only forward-looking content gets tagged — same rule as Phase-3 extraction).
- When superseding: leave the old marker, add `<!-- superseded: JR-X-Y-Z by JR-A-B-C -->` next to it.

### How this enables refresh

When the next refresh runs, the [drift-detection script](#7-stale--drift-detection) can:

1. Find all `<!-- requirement: JR-* -->` markers across notes/
2. Cross-reference each with `id_assignments.yaml`
3. Flag mismatches:
   - Marker references a JR-* ID that doesn't exist → broken reference
   - JR-* entry's cited line range doesn't contain a marker → cite drift
   - Marker present but the prose body changed substantially → content drift

Without these markers, drift detection has to fall back to keyword matching (what we have now). With them, drift detection becomes precise.

### Open decisions

- **Adoption ramp**: tag opportunistically (when editing a notes doc anyway) rather than backfill all 1,803 entries at once. Backfill would be a multi-day effort.
- **Marker format**: HTML comment is least disruptive. Alternatives considered: YAML frontmatter (rejected — only works on file level), code-fence directive (rejected — visible in rendered docs).

---

## 6. CI lint validating JR-ID references

**Status**: Pre-design. Implement after enough PRs use §4 convention to make it worth automating.

**Why**: PR descriptions that reference JR-* IDs are only useful if the references resolve. A typo (`JR-CAS-WS-104` instead of `JR-CAS-WS-014`) silently loses the cross-reference. CI lint catches typos at PR-open time.

### Proposed scope (v1 lint — minimum viable)

A GitHub Actions workflow that runs on PR open / update:

1. Extract all `JR-[A-Z]+-[A-Z]+-\d{3}` references from the PR description.
2. Cross-reference each against the current `id_assignments.yaml` on `main`.
3. Fail if any reference doesn't resolve.
4. Soft-warn (don't fail) if a reference resolves but is in `superseded` or `rejected` status.

### v2 lint (later, optional)

Additional checks:

- If PR description says `Closes JR-*`, verify the JR entry's status was `proposed`/`designed`/`in-progress`/`deferred` (not already `shipped`/`rejected`).
- If PR touches files cited by a JR-* entry but the description doesn't reference that entry, post an info comment suggesting the cross-reference.

### Implementation sketch

```yaml
# .github/workflows/requirements-lint.yml
name: Requirements lint
on:
  pull_request:
    types: [opened, edited, synchronize]
jobs:
  jr-id-references:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/validate_jr_id_refs.py --pr-body "${{ github.event.pull_request.body }}"
```

The `scripts/validate_jr_id_refs.py` (to be written) reads the PR body from stdin or arg, parses `id_assignments.yaml`, and exits non-zero on unresolved references.

### Cost

- Script: ~50 lines of Python.
- Workflow: ~20 lines of YAML.
- Maintenance: trivial unless the ID format changes (it won't — locked per plan §6).

### Open decisions

- **Where does the lint live?** Probably in juniper-ml since that's where the snapshot lives. Other repos would need to either reach across with `actions/checkout@v4` for juniper-ml or wait for a published validation action.
- **Do we want this on every repo, or only juniper-ml?** Start with juniper-ml. Extend to other repos when JR-* references appear in their PRs.

---

## 7. Stale / drift detection

**Status**: `--mode quick` shipped 2026-05-18 at [`util/requirements_drift_check.py`](../util/requirements_drift_check.py), with regression tests at [`tests/test_requirements_drift_check.py`](../tests/test_requirements_drift_check.py). Baseline run against v4 snapshot: **1,914 / 1,915 citations OK (99.95%), 1 BAD_PATH** (`JR-CAS-TOOL-002` cites a renamed/removed cascor history file). Drift is far below the >5% refresh trigger.

`--mode full` and `--mode rewrite` are stubbed but unimplemented; they exit with code 2 and a "not yet implemented" message. They remain useful additions but should wait for a refresh trigger that actually exercises them.

**Why**: Notes docs change over time. The cited line ranges in `id_assignments.yaml` are snapshots from extraction date; the content at those lines today may have shifted, been deleted, or been replaced by unrelated content. Without drift detection, a refresh can't tell what changed.

### Categories of drift

| Drift type                                                                                             | Detection signal                                            | Likely action                                                 |
|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|---------------------------------------------------------------|
| **Line shift** — content moved within the same file (e.g., section added above pushed everything down) | Brief keywords no longer in cited range but still in file   | Re-cite to new line range                                     |
| **Content deletion** — cited content removed                                                           | Brief keywords no longer in file at all                     | Mark requirement as `superseded` or `rejected` pending review |
| **File deletion** — source file no longer exists                                                       | `path` does not resolve                                     | Same — supersede or rejection                                 |
| **File renamed** — source moved (e.g., `notes/foo.md` → `notes/legacy/foo.md`)                         | Path doesn't resolve but a same-basename file exists nearby | Re-cite to new path                                           |
| **Content drift** — line range still contains relevant content, but specifics changed (numbers, names) | Brief partially matches; surrounding content has changed    | Flag for manual review; possibly update brief                 |
| **No drift**                                                                                           | Brief keywords still in cited range                         | No action                                                     |

### Existing tooling

**Status (2026-05-18): irrecoverable.** The v4-QA script `v2_citation_validate.py` was authored in `/tmp/` and is no longer on disk — the session sandbox where it lived has been reaped. It cannot be promoted because there is nothing to promote. This loss is the motivating incident for the new ecosystem-wide [Script placement rule](../AGENTS.md#script-placement-mandatory): utility scripts MUST live in `util/`, never in `/tmp/`.

The successor must therefore be **built from scratch** at `util/requirements_drift_check.py`. The five detection categories that the lost script implemented are still spec'd in the table above; the file-rename heuristic (6th category) is the only addition relative to the lost behaviour. The cost is small (~150–200 lines of Python) and the spec is unambiguous, so the rebuild is tractable when triggered.

### Proposed permanent location

```text
util/requirements_drift_check.py   # main script
util/requirements_drift_check_README.md   # usage doc
```

Run modes:

- `--mode quick` — just path + line-range validity (fast, no file reads). Output: count by drift category.
- `--mode full` — full content match using brief-keyword grep. Output: per-entry drift report.
- `--mode rewrite` — full check + attempt automatic fixes (line shift, file rename). Output: patch file against `id_assignments.yaml`.

### Open decisions

- **How often to run**: Suggest `--mode quick` weekly via cron; `--mode full` before each refresh; `--mode rewrite` only ad-hoc with human review.
- **What to do with `superseded`-candidates**: Don't auto-promote. The script flags; humans decide.

---

## 8. Periodic refresh procedure

**Status**: Pre-design. Depends on drift-detection (§7). Run on demand for now; consider quarterly cadence once tooling exists.

**Why**: The snapshot is a point-in-time artifact. Without refresh, it diverges from reality. A controlled refresh procedure prevents drift from accumulating to the point where the snapshot is no longer useful.

### Proposed refresh procedure

Each refresh is a numbered iteration (vN+1) following the same pattern as v1-v4:

1. **Audit** — run drift-detection (`util/requirements_drift_check.py --mode full`). Generate the drift report.
2. **Decide scope** — review the drift report. If <5% drift, do a minimal refresh (re-cite only). If 5-20%, do a partial re-extraction on changed files. If >20%, consider a full re-extraction.
3. **Refresh** — run [`util/requirements_consolidate.py`](../util/requirements_consolidate.py) (`--check-roundtrip`, `--check-views`, then `--merge PATH.yaml --apply`). **History (2026-05-18): the v1–v4 consolidator (`phase4_consolidate.py`) was authored in `/tmp/` and is irrecoverable** — the session sandbox that held it has been reaped. That loss is the motivating incident for the ecosystem-wide [Script placement rule](../AGENTS.md#script-placement-mandatory). The v5 rebuild is in-tree; it is **not** a reimplementation of the `/tmp` script (the Phase-3 extraction YAMLs are gone too). Operator contract: [`docs/REFERENCE.md` § Requirements Snapshot Consolidation](../docs/REFERENCE.md#requirements-snapshot-consolidation).
4. **Validate** — re-run citation validator. Confirm precision ≥ 95% EXACT.
5. **Update plan doc §11** — add a new vN+1 row in the phase tracker. Update §12 with any new issues.
6. **Ship** — commit, push, open PR. Same close-out pattern as v1-v4.

### Triggers

A refresh becomes worthwhile when one or more of:

- Drift report shows >5% citation drift.
- A major refactor lands that touches many cited source files.
- A new major repo joins the ecosystem (current 8 active repos).
- More than 6 months since last refresh.

### Cost per refresh

- v2 (the biggest pass): ~1 day of focused work + agent runtime.
- v3, v4 (quality passes): ~half-day each.
- Future minimal refresh (re-cite only): ~2 hours.

### Open decisions

- **Cadence**: do nothing scheduled; refresh when drift triggers it. Avoid calendar-driven refreshes if nothing has drifted.
- **Where does the consolidation script live permanently?** **RESOLVED 2026-08-21** — it exists at [`util/requirements_consolidate.py`](../util/requirements_consolidate.py), rebuilt as the v5-1 task. The hard prerequisite is discharged; future refreshes are no longer blocked. Note it is deliberately **not** a reimplementation of `phase4_consolidate.py`: that script consumed the Phase-3 extraction YAMLs, which were also `/tmp`-resident and are gone, so the corpus is now parsed from the shipped views. See plan-doc §11 rows v5-1/v5-2 for the two findings that forced the redesign (the ledger carries no `detail`; the three view families disagree with each other).

---

## 9. §12 carry-over triage

**Status**: Active. The following plan-doc §12 issues have explicit dispositions:

| §   | Issue                                        | Disposition                                                                                                         | Rationale                                              |
|-----|----------------------------------------------|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| #8  | Phase-3c agents truncated on elephant files  | **DEFER permanently** — agent-brief improvement; only helps future extraction passes. No extraction passes planned. | Resolution from v4-#18: corpus is at coverage ceiling. |
| #9  | 3c-3b-2 invented invalid category codes      | **DEFER permanently** — same reason as #8.                                                                          | Same.                                                  |
| #11 | Score 1-9 long-tail (~245 files) unprocessed | **REJECT permanently** — cost > benefit, boilerplate content.                                                       | v1 decision, reaffirmed at v4.                         |
| #12 | ARCH re-bucket rules first-match heuristic   | **ACCEPT as-is** — v3 spot-check showed no obvious misclassifications.                                              | No usage signal that finer ARCH bucketing matters.     |
| #17 | 2 thin-brief entries still flagged after v4  | **ACCEPT as-is** — trivial residual.                                                                                | Not worth a v5 just for 2 entries.                     |
| #18 | Coverage ceiling reached                     | **FRAMING DECISION (not a defect)** — informs §10 update.                                                           | Future work shifts to *use* per this doc.              |

Update plan doc §12 to reflect these dispositions in a future small PR (or alongside the next substantive change).

**2026-05-18**: Done. Plan doc §12 now has a "Final dispositions (consolidated 2026-05-18)" subsection mirroring this table. Future refreshes can treat these as closed.

---

## 10. Anti-patterns — things NOT to do next

| Anti-pattern                                              | Why not                                                                                            |
|-----------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Build all of §3-§9 speculatively                          | Most won't pay off. Wait for usage signals (someone reaches for the feature).                      |
| Re-extract score 1-9 long-tail files                      | §12-#11; rejected at v1 and v4. Cost > benefit.                                                    |
| Add new area codes without a corpus-level review          | The 15-code enum is locked. New codes are a v5 prerequisite, not a v4.x option.                    |
| Manually edit `id_assignments.yaml` to fix small things   | Regenerator will clobber. Edit the source extraction YAMLs instead, or accept the small thing.     |
| Build a custom UI on top of the snapshot                  | The markdown tree IS the UI. Don't add layers; add queries (§3).                                   |
| Treat the snapshot as ground truth without checking drift | Snapshot is point-in-time. Always run drift detection (§7) before relying on it for big decisions. |

---

## 11. Decision log

| Date       | Decision                                      | Rationale                                                                                                                                  | Owner       |
|------------|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| 2026-05-16 | Document created with 7 next-step topics      | Captures forward plan after v4 corpus shipped (PR #261). Format mirrors plan doc structure: numbered sections, cross-refs, open decisions. | Paul Calnon |
| 2026-05-16 | All 7 topics are opt-in / wait-for-signal     | Avoid speculative infra. The snapshot itself is the deliverable.                                                                           | Paul Calnon |
| 2026-05-16 | §3 and §4 recommended as first adoption steps | Lowest cost, immediate value, no infrastructure required.                                                                                  | Paul Calnon |
